#!/usr/bin/env python3
"""
G4 — chronons are Sets: time as coordinates, reading as intersection.

A coordinate `cronon:<clock>:c<n>` is ALSO the name of a Set; anything located there is a member.
Three clocks: the WORLD's (shared events), each WORKBENCH's (executions + thought acts, mode-marked),
and each workflow BRANCH's (the plan only, rewindable, never synced). This eval drives the model on
BOTH cell shapes:

  • a coordinate is a Set (its members are the located atoms); a plan position holds only the entry +
    its revisions; a bench coordinate carries its mode.
  • executing the same plan step three times (advance, rewind, advance, fork, advance) yields three
    bench coordinates that `cronon:executes` a plan position — and NOTHING on the branch clock changes.
  • wf.advance mode=thought walks the plan WITHOUT running any operator (the entries stay pending, the
    cursor moves), minting bench coordinates mode=thought that `cronon:rehearses` the position; a
    rewind and a branch each add one thought record.
  • the ordered bench timeline shows thought and execution rows distinguishably (mode column); a plan
    (branch) coordinate prints `—` for `when`.
  • wf.dispatch and world.sync each make a `cronon:sync` link world ↔ bench, and none on the branch.

Run:  python app/test/chronon_set_eval.py     (exit 0 = all pass)
"""
import hashlib
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from lib.akasha.workbench import autorun
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _run(series, shape):
    print(f"\n  ── {shape} ({series}) ──")
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series=series, base_dir=tempfile.mkdtemp(prefix="akasha_cron_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def d(method, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
        return r if "error" in r else (r.get("result") or {})

    nuc = k.manager.shared_nucleus.core

    def mem(s):
        try:
            return list(nuc.get_collection_members(s) or [])
        except Exception:
            return []

    d("world.genesis", {})
    d("grp.new", {"group_id": "lab", "admin_id": "admin"})
    d("bench.new", {"name": "sandbox", "kind": "research", "group": "lab"})
    d("society.new", {"group": "lab", "name": "sem", "world": "default", "bench": "sandbox",
                      "kind": "cowork"})
    d("wf.new", {"bench": "sandbox"})
    d("wf.write", {"bench": "sandbox", "pos": 1, "entry": "read the sample"})
    d("wf.write", {"bench": "sandbox", "pos": 2, "entry": "state a hypothesis"})

    # ── a plan position holds ONLY the entry (and its revisions) ──
    p1 = mem("cronon:wf:sandbox:main:p1")
    check(f"[{shape}] a plan position is a Set holding its entry", len(p1) == 1, f"n={len(p1)}")
    d("wf.write", {"bench": "sandbox", "pos": 1, "entry": "read the sample carefully"})   # a revision
    p1r = mem("cronon:wf:sandbox:main:p1")
    check(f"[{shape}] a revised plan position holds the entry AND its revision (history kept)",
          len(p1r) == 2, f"n={len(p1r)}")

    # ── execute the same step three times: advance, rewind, advance, fork, advance ──
    d("wf.advance", {"bench": "sandbox", "n": 1})                       # execution #1 (main p1)
    d("wf.rewind", {"bench": "sandbox", "pos": 0})                      # thought (rewind)
    d("wf.advance", {"bench": "sandbox", "n": 1})                       # execution #2 (main p1)
    d("wf.branch", {"bench": "sandbox", "from": 1, "name": "alt"})      # thought (branch) + fork link
    d("wf.rewind", {"bench": "sandbox", "pos": 0, "branch": "alt"})     # alt cursor → 0 so p1 is ahead
    d("wf.advance", {"bench": "sandbox", "branch": "alt", "n": 1})      # execution #3 (alt p1)
    ex_main = d("cronon.executions", {"bench": "sandbox", "branch": "main", "pos": 1,
                                      "mode": "execution"})
    check(f"[{shape}] main p1 was carried out TWICE (two bench coordinates cronon:executes it)",
          ex_main.get("count") == 2, str(ex_main.get("count")))
    ex_alt = d("cronon.executions", {"bench": "sandbox", "branch": "alt", "pos": 1,
                                     "mode": "execution"})
    check(f"[{shape}] the forked branch's p1 was carried out ONCE", ex_alt.get("count") == 1,
          str(ex_alt.get("count")))
    check(f"[{shape}] NOTHING on the branch clock changed (main p1 still just entry+revision)",
          len(mem("cronon:wf:sandbox:main:p1")) == 2, str(len(mem("cronon:wf:sandbox:main:p1"))))
    # the fork link is on the branch clock (alt p1 → main p1), never a sync
    fork = [dst for dst, rel in
            [(x, "cronon:forked_from") for x in mem("cronon:wf:sandbox:alt:p1")]] or []
    check(f"[{shape}] wf.branch left a cronon:forked_from link on the branch clocks",
          bool([a for a, r in _links(nuc, "cronon:wf:sandbox:alt:p1") if r == "cronon:forked_from"]),
          "no fork link")

    # ── wf.advance mode=thought — walk the plan, run NO operator, cursor moves ──
    d("wf.new", {"bench": "sandbox"})                                  # (idempotent)
    d("wf.rewind", {"bench": "sandbox", "pos": 0})
    _cur0 = d("wf.cursor", {"bench": "sandbox", "branch": "main"}).get("cursor")
    th = d("wf.advance", {"bench": "sandbox", "n": 2, "mode": "thought"})
    _cur1 = d("wf.cursor", {"bench": "sandbox", "branch": "main"}).get("cursor")
    reh = d("cronon.executions", {"bench": "sandbox", "branch": "main", "mode": "thought"})
    check(f"[{shape}] wf.advance mode=thought moved the cursor without running an operator",
          th.get("status") == "rehearsed" and _cur1 == 2 and _cur0 == 0, f"{_cur0}→{_cur1}")
    # the plan entries were NOT annotated done by a thought walk (no operator, no result)
    _ls = d("wf.ls", {"bench": "sandbox", "branch": "main"})
    _statuses = {e["pos"]: e.get("status") for e in _ls.get("entries", [])}
    check(f"[{shape}] a thought walk annotates NOTHING (the plan entries stay pending)",
          _statuses.get(2) != "done", str(_statuses))
    check(f"[{shape}] the thought walk minted rehearsal records (cronon:rehearses)",
          reh.get("count", 0) >= 2, str(reh.get("count")))

    # ── E2-1 (F4) — a DRIVER rewind (the society driver's mechanical reset-before-rerun) is part of the
    #    execution, NOT a thought experiment: it adds ZERO thought records; an AGENT rewind adds one. ──
    def _thought_n():
        return d("cronon.executions", {"bench": "sandbox", "branch": "main",
                                       "mode": "thought"}).get("count", 0)
    _thb = _thought_n()
    _rd = d("wf.rewind", {"bench": "sandbox", "pos": 0, "by": "driver"})       # driver rerun
    check(f"[{shape}] F4 a driver rewind is recorded as execution (mode=execution, by=driver)",
          _rd.get("mode") == "execution" and _rd.get("by") == "driver", str(_rd))
    check(f"[{shape}] F4 a driver rewind adds ZERO thought records", _thought_n() == _thb,
          f"{_thb}→{_thought_n()}")
    _ra = d("wf.rewind", {"bench": "sandbox", "pos": 0})                       # agent rewind (default)
    check(f"[{shape}] F4 an agent rewind stays a thought record (adds one)",
          _ra.get("mode") == "thought" and _thought_n() == _thb + 1,
          f"{_thb}→{_thought_n()} mode={_ra.get('mode')}")

    # ── R4 — the per-run [cronon] summary SEES the coordinates a run minted, and normalises a
    #    hyphenated bench alias (the info.get('bench')='wb:plants-vision' vs cronon:wb:plants_vision bug
    #    that made the VPS line report minted=0 for a run that DID advance the clock). ──
    _cs = autorun.bench_cronon_summary(k, "wb:sandbox", 0)
    check(f"[{shape}] R4 _bench_cronon_summary reports the minted bench coordinates (the clock moved)",
          _cs.get("minted", 0) >= 3, str(_cs))
    check(f"[{shape}] R4 the hyphen→uslug normalization matches _bench_alias (the info.get('bench') bug)",
          autorun.bench_balias_norm("wb:plants-vision") == "wb:plants_vision", autorun.bench_balias_norm("wb:plants-vision"))
    check(f"[{shape}] R4 a mangled (case) bench alias resolves to the same coordinate set",
          autorun.bench_cronon_count(k, "wb:SANDBOX") == autorun.bench_cronon_count(k, "wb:sandbox")
          and autorun.bench_cronon_count(k, "wb:sandbox") > 0,
          f"upper={autorun.bench_cronon_count(k, 'wb:SANDBOX')} lower={autorun.bench_cronon_count(k, 'wb:sandbox')}")

    # ── the ordered bench timeline distinguishes thought from execution (mode column) ──
    tl = d("cronon.timeline", {"clock": "wb:sandbox"})
    modes = {r.get("mode") for r in (tl.get("timeline") or [])}
    check(f"[{shape}] the bench timeline is ordered by position and carries both modes",
          "execution" in modes and "thought" in modes
          and [r["pos"] for r in tl["timeline"]] == sorted(r["pos"] for r in tl["timeline"]),
          str(sorted(modes)))
    # a plan (branch) coordinate has no wall time → `—`
    ptl = d("cronon.timeline", {"clock": "wf:sandbox:main"})
    check(f"[{shape}] a plan (branch) coordinate prints — for when (a plan has no wall time)",
          all(r.get("when") == "—" for r in (ptl.get("timeline") or [])) and ptl.get("count", 0) >= 1,
          str([(r["pos"], r["when"]) for r in ptl.get("timeline", [])]))

    # ── sync = a link world ↔ bench only (wf.dispatch + world.sync); none on the branch ──
    d("wf.dispatch", {"bench": "sandbox", "branch": "main", "from": 1, "to": 2})
    sb = d("cronon.sync.between", {"world": "default", "bench": "sandbox"})
    check(f"[{shape}] wf.dispatch made a cronon:sync link world ↔ bench", sb.get("count", 0) >= 1,
          str(sb.get("count")))
    d("world.sync", {"bench": "sandbox", "at": "cronon:wb:sandbox:c1"})
    sb2 = d("cronon.sync.between", {"world": "default", "bench": "sandbox"})
    check(f"[{shape}] world.sync adds another world ↔ bench sync (a moderator marking a bench moment)",
          sb2.get("count", 0) == sb.get("count", 0) + 1,
          f"{sb.get('count')}→{sb2.get('count')}")
    # a branch coordinate is NEVER a sync endpoint
    _branch_synced = any("wf:sandbox" in str(p.get("bench")) for p in (sb2.get("pairs") or []))
    check(f"[{shape}] no branch coordinate is ever a sync endpoint (world ↔ bench only)",
          not _branch_synced)


def _links(core, alias):
    """Outgoing (dst_alias, rel) for an alias, resolved. The raw core returns list-of-dicts."""
    try:
        k = core.get_key_by_alias(alias) or alias
        out = []
        for row in core.get_adjacent_links(k):
            dst, rel = row["dst"], row["rel"]
            da = core.get_aliases_by_key(dst)
            out.append((da[0] if da else dst, rel))
        return out
    except Exception:
        return []


def main():
    _run("thesaurus", "nucleus cell")
    _run("seeds", "single-store cell")
    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("\nRESULT: PASS — a coordinate is a Set; a plan position holds only its entry + revisions; a "
          "plan step executed three times yields three bench coordinates that cronon:executes it with "
          "nothing changed on the branch clock; wf.advance mode=thought rehearses without running an "
          "operator (cursor moves, entries stay pending); the ordered bench timeline distinguishes "
          "thought from execution; and sync is a link world ↔ bench only — both cell shapes.")
    sys.exit(0)


if __name__ == "__main__":
    main()
