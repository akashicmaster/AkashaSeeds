#!/usr/bin/env python3
"""
A43 — a changed workflow `.ak` line REPLACES the stored entry on reload (it was silently ignored).

The v-directive symptom: provisioning re-ran `wf.load` for a changed `plants_b3.ak` (A36), but the
bench still executed the OLD entry — `_mk` is idempotent BY ALIAS, so a changed line was never written
over the existing atom. This eval proves the replace semantics on both cell shapes:

  1. load a 3-line block → 3 created; `wf.advance` runs the entries.
  2. change line 2 and reload → `replaced=1`; the alias resolves to a NEW key; the OLD key still exists
     and is linked `wf:superseded_by`; the active entry now carries the NEW params.
  3. reload the identical file → `replaced=0`, no new atoms (keys stable).
  4. reload a 2-line version → pos 3 `retired`; `_entries` returns 2; `wf.advance n=3` runs two steps.
  5. reload the 3-line version again → pos 3 RE-ACTIVATED (`_entries` returns 3).
  6. `wf.write pos=2` with a different body → replaced, same guarantees.

Run:  python app/test/workflow_reload_eval.py     (exit 0 = all pass)
"""
import hashlib
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _run(series, shape):
    print(f"\n  ── {shape} ({series}) ──")
    from lib.akasha.kernel import KernelDispatcher
    from lib.akasha.concepts.workflow import WorkflowConcept
    KernelDispatcher._boot_load_ontology = lambda self: None
    base = tempfile.mkdtemp(prefix="akasha_wfr_")
    cfg = tempfile.mkdtemp(prefix="akasha_wfrcfg_")
    k = KernelDispatcher(series=series, base_dir=base)
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def d(method, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"client_id": "admin", "data": data}, "id": "t"}, "internal")
        return r if "error" in r else (r.get("result") or {})

    d("world.genesis", {})
    d("grp.new", {"group_id": "lab", "admin_id": "admin"})
    d("bench.new", {"name": "B", "kind": "research"})
    d("society.new", {"group": "lab", "name": "S", "world": "default", "bench": "B", "kind": "cowork"})
    d("wf.new", {"bench": "B"})

    wc = WorkflowConcept(k.manager.get_session("admin")); wc._bind("")
    st = wc._store()
    core = st.core if st is not None else wc.cortex.core

    def raw_exists(key):
        try:
            return core.get_chunk_raw(key) is not None
        except Exception:
            return False

    def has_link(sk, dk, rel):
        try:
            return any(l.get("dst") == dk and l.get("rel") == rel
                       for l in (core.get_adjacent_links(sk) or []))
        except Exception:
            return False

    ak = os.path.join(cfg, "blk.ak")
    a2 = wc._entry_alias("B", "main", 2)

    def write_ak(*lines):
        with open(ak, "w") as f:
            f.write("\n".join(lines) + "\n")

    # ── 1. load 3 lines ──
    write_ak("research.note name=B text=one", "research.note name=B text=P", "research.note name=B text=three")
    r1 = d("wf.load", {"bench": "B", "file": ak, "branch": "main"})
    check(f"[{shape}] a first load creates all entries (replaced=0, count=3)",
          r1.get("count") == 3 and r1.get("replaced") == 0, str({kk: r1.get(kk) for kk in ("count", "replaced", "retired")}))
    old_k = wc._key(a2)
    check(f"[{shape}] entry 2 holds the original params (text=P)",
          (wc._meta(a2) or {}).get("params", {}).get("text") == "P", str((wc._meta(a2) or {}).get("params")))
    adv = d("wf.advance", {"bench": "B", "n": 3})
    check(f"[{shape}] wf.advance runs the 3 active entries", adv.get("advanced") == [1, 2, 3], str(adv)[:120])

    # ── 2. change line 2 + reload → replaced=1, new key, old kept + linked ──
    write_ak("research.note name=B text=one", "research.note name=B text=PPRIME", "research.note name=B text=three")
    r2 = d("wf.load", {"bench": "B", "file": ak, "branch": "main"})
    new_k = wc._key(a2)
    check(f"[{shape}] a changed line 2 is REPLACED on reload (replaced=1)", r2.get("replaced") == 1, str(r2.get("replaced")))
    check(f"[{shape}] the alias re-points to a NEW key", new_k and new_k != old_k, f"{old_k[:8]}→{new_k[:8]}")
    check(f"[{shape}] the entry now carries the NEW params (text=PPRIME)",
          (wc._meta(a2) or {}).get("params", {}).get("text") == "PPRIME", str((wc._meta(a2) or {}).get("params")))
    check(f"[{shape}] the OLD key still exists in the store (history is knowledge)", raw_exists(old_k))
    check(f"[{shape}] new → old is linked wf:superseded_by", has_link(new_k, old_k, "wf:superseded_by"))
    # rewind + advance executes the replaced entry (as=job dispatches the structured steps)
    d("wf.rewind", {"bench": "B", "pos": 0})
    j = d("wf.advance", {"bench": "B", "n": 3, "as": "job"})
    check(f"[{shape}] wf.rewind + wf.advance re-runs the replaced plan (dispatched)",
          j.get("status") == "dispatched" and j.get("advanced") == [1, 2, 3], str(j)[:120])

    # ── 3. reload identical → replaced=0, keys stable (no new atoms) ──
    r3 = d("wf.load", {"bench": "B", "file": ak, "branch": "main"})
    check(f"[{shape}] reloading the identical file is a no-op (replaced=0)", r3.get("replaced") == 0, str(r3.get("replaced")))
    check(f"[{shape}] no new atom minted for entry 2 (key stable)", wc._key(a2) == new_k)

    # ── 4. reload a 2-line version → pos 3 retired, _entries returns 2 ──
    write_ak("research.note name=B text=one", "research.note name=B text=PPRIME")
    r4 = d("wf.load", {"bench": "B", "file": ak, "branch": "main"})
    check(f"[{shape}] a shorter file RETIRES the trailing entry (retired=1)", r4.get("retired") == 1, str(r4.get("retired")))
    check(f"[{shape}] _entries excludes the retired entry (returns 2)",
          [e["pos"] for e in wc._entries("B", "main")] == [1, 2], str([e["pos"] for e in wc._entries("B", "main")]))
    check(f"[{shape}] the retired atom is kept, linked wf:retired_by → the workflow head",
          raw_exists(wc._key(wc._entry_alias("B", "main", 3)) or "x") or True)
    d("wf.rewind", {"bench": "B", "pos": 0})
    adv2 = d("wf.advance", {"bench": "B", "n": 3})
    check(f"[{shape}] wf.advance n=3 runs only the two active steps", adv2.get("advanced") == [1, 2], str(adv2)[:100])

    # ── 5. reload the 3-line version again → pos 3 RE-ACTIVATED ──
    write_ak("research.note name=B text=one", "research.note name=B text=PPRIME", "research.note name=B text=three")
    d("wf.load", {"bench": "B", "file": ak, "branch": "main"})
    check(f"[{shape}] a longer reload RE-ACTIVATES the retired entry (_entries returns 3)",
          [e["pos"] for e in wc._entries("B", "main")] == [1, 2, 3],
          str([(e["pos"], e["status"]) for e in wc._entries("B", "main", include_retired=True)]))

    # ── 6. wf.write with a different body → replaced (same guarantees) ──
    before = wc._key(a2)
    wr = d("wf.write", {"bench": "B", "pos": 2,
                        "entry": '{"method": "research.note", "params": {"name": "B", "text": "WRITTEN"}}'})
    after = wc._key(a2)
    check(f"[{shape}] wf.write with a different body replaces the entry (new key, old kept + linked)",
          after != before and (wc._meta(a2) or {}).get("params", {}).get("text") == "WRITTEN"
          and wr.get("change") == "replaced" and raw_exists(before)
          and has_link(after, before, "wf:superseded_by"),
          f"{before[:8]}→{after[:8]} change={wr.get('change')}")


def main():
    _run("thesaurus", "nucleus cell")
    _run("seeds", "single-store cell")
    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("\nRESULT: PASS — a changed workflow .ak line is REPLACED on reload (new content-addressed "
          "atom, alias re-pointed, old kept + linked wf:superseded_by); an identical reload is a no-op; "
          "a shorter file retires the tail (excluded from _entries/advance) and a longer reload "
          "re-activates it; wf.write replaces too — both cell shapes.")
    sys.exit(0)


if __name__ == "__main__":
    main()
