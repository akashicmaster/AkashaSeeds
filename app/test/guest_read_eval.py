#!/usr/bin/env python3
"""
F3 (M7) — public GUEST read access to the Concept Laboratory, with the Radu exclusion server-side.

Maintainer decision (2026-09-11): everything under `archives` is public and guests read it read-only,
EXCEPT Radu's unpublished research. This eval drives the contract on BOTH cell shapes as a real GUEST
session (session.guest.create → gbk token, dispatched over the NETWORK transport):

  • a guest READS the public bench: bench.ls lists it, bench.info / learning.runs / vlab.item /
    vlab.item.versions / source.trace / lens.compare all answer;
  • the Radu-scoped bench is ABSENT from a guest's bench.ls and REFUSED (-32001) on bench.info /
    learning.runs;
  • the answer key never leaves the admitted circle: a guest's lens.compare returns rows with
    truth=null and truth_known=0, and no aggregate atom is stored (writes stay denied);
  • an admin is unaffected (sees the Radu bench, gets truth).

Run:  python app/test/guest_read_eval.py     (exit 0 = all pass)
"""
import hashlib
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []
_CLASSES = ["OAK", "MAPLE", "BIRCH", "PINE", "ELM", "ASH"]


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _run(series, shape):
    print(f"\n  ── {shape} ({series}) ──")
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series=series, base_dir=tempfile.mkdtemp(prefix="akasha_guestread_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def a(method, data):                          # admin (local trust)
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
        return r if "error" in r else (r.get("result") or {})

    # a GUEST session over the NETWORK transport (the real public path)
    gr = k.dispatch({"jsonrpc": "2.0", "method": "session.guest.create",
                     "params": {"data": {}}, "id": "gg"}, "network")
    gtok = (gr.get("result") or {}).get("binding_key")

    def g(method, data):                          # guest (network trust)
        return k.dispatch({"jsonrpc": "2.0", "method": method,
                           "params": {"session_token": gtok, "data": data}, "id": "gq"}, "network")

    a("world.genesis", {})
    # ── a PUBLIC bench (nucleus, guest-readable) + a RADU-scoped bench (world=radu → excluded) ──
    a("bench.new", {"name": "plants_vision", "kind": "learning"})     # public (no group)
    a("grp.new", {"group_id": "radu-lab", "admin_id": "admin"})
    a("bench.new", {"name": "radulab", "kind": "learning", "group": "radu-lab"})   # not for the public: in its group

    a("source.register", {"provider": "mock", "name": "leafsrc", "rights": "CC0"})
    recs = [{"id": f"img_{i}", "image": f"mock://leaf/{i}.jpg", "species_symbol": _CLASSES[i % 6]}
            for i in range(24)]
    a("source.pool.create", {"name": "leafimg", "version": "v1", "source": "source:src:leafsrc",
                             "rule": "mock", "label_field": "species_symbol"})
    a("source.acquire", {"source": "source:src:leafsrc", "rule": "mock", "records": recs,
                         "pool": "source:pool:leafimg:v1", "id_field": "id",
                         "label_field": "species_symbol"})
    a("source.pool.freeze", {"pool": "source:pool:leafimg:v1"})
    tg = a("source.pool.sample", {"pool": "source:pool:leafimg:v1", "name": "target", "n": "12",
                                  "seed": "s1", "strata": "species_symbol"})
    s_target = tg.get("sample")
    a("learning.dataset.bind", {"name": "plants_vision", "pool": s_target, "role": "target"})
    # two readings of the target → two run Sets to compare
    a("learning.observe", {"name": "plants_vision", "pool": "role:target", "observers": "mock",
                        "run": "o0", "branch": "plants_t2"})
    a("learning.observe", {"name": "plants_vision", "pool": "role:target", "observers": "color",
                        "run": "o1", "branch": "plants_t6"})
    run_a, run_b = "set:vlab:run:o0:observations", "set:vlab:run:o1:observations"
    # admin stores the diff so learning.runs.diffs has a row
    a("lens.compare", {"a": run_a, "b": run_b, "key": "vis:observes", "truth": "species_symbol",
                       "result": "wb:plants_vision:diff:o0:o1"})
    for _s in ("set:vlab:compares", "set:wb:plants_vision:diffs"):      # the observe.diff macro's filing, by hand
        a("set.add", {"name": _s, "id": "wb:plants_vision:diff:o0:o1"})

    # ── the guest reads the PUBLIC bench ──
    bls = g("bench.ls", {}).get("result") or {}
    _names = {r.get("bench") for r in (bls.get("benches") or [])}
    check(f"[{shape}] guest bench.ls lists the public bench", "wb:plants_vision" in _names, str(_names))
    check(f"[{shape}] guest bench.ls EXCLUDES the Radu-scoped bench", "wb:radulab" not in _names, str(_names))

    bi = g("bench.info", {"name": "plants_vision"})
    check(f"[{shape}] guest bench.info answers for the public bench",
          isinstance(bi, dict) and (bi.get("result") or {}).get("bench") == "wb:plants_vision", str(bi)[:140])
    bir = g("bench.info", {"name": "radulab"})
    check(f"[{shape}] guest bench.info on the Radu bench is REFUSED — the bench is in its group, and the scope gate answers a non-member as if it did not exist",
          isinstance(bir, dict) and "error" in bir and "radulab" not in str(bir.get("result") or ""), str(bir)[:140])
    brr = g("learning.runs", {"name": "radulab"})
    check(f"[{shape}] guest learning.runs on the Radu bench is REFUSED (a bench in its group is unknown to a non-member)",
          isinstance(brr, dict) and "error" in brr, str(brr)[:140])

    brun = g("learning.runs", {"name": "plants_vision"}).get("result") or {}
    check(f"[{shape}] guest learning.runs answers for the public bench (o0 + o1)",
          {r.get("run") for r in (brun.get("runs") or [])} >= {"o0", "o1"},
          str({r.get("run") for r in (brun.get("runs") or [])}))
    _gdiffs = brun.get("diffs") or []
    check(f"[{shape}] guest learning.runs.diffs withhold truth_known (=0) — the answer key stays private",
          _gdiffs and all((dd.get("summary") or {}).get("truth_known") == 0 for dd in _gdiffs),
          str(_gdiffs)[:160])
    # R5 — agree_a/agree_b are COUNTS (public evidence of learning), shown to guests
    check(f"[{shape}] R5 guest learning.runs.diffs SHOW the agree counts (public learning evidence)",
          _gdiffs and all((dd.get("summary") or {}).get("agree_a") is not None
                          and (dd.get("summary") or {}).get("agree_b") is not None for dd in _gdiffs),
          str([dd.get("summary") for dd in _gdiffs])[:160])

    # ── the guest lens.compare returns rows with truth=null, truth_known=0, and stores nothing ──
    gc = g("lens.compare", {"a": run_a, "b": run_b, "key": "vis:observes", "truth": "species_symbol",
                            "result": "wb:plants_vision:diff:guest_attempt"}).get("result") or {}
    check(f"[{shape}] guest lens.compare returns the rows (a public read)",
          (gc.get("summary") or {}).get("items", 0) > 0, str(gc.get("summary")))
    check(f"[{shape}] guest lens.compare hides the answer key (truth_known=0, rows truth=null)",
          (gc.get("summary") or {}).get("truth_known") == 0
          and all(r.get("truth") is None for r in (gc.get("rows") or [])), str(gc.get("summary")))
    check(f"[{shape}] guest lens.compare stores NO aggregate atom (writes denied)",
          gc.get("stored") is None
          and not k.manager.shared_nucleus.core.get_key_by_alias("wb:plants_vision:diff:guest_attempt"),
          str(gc.get("stored")))

    # ── the guest reads the item-level surfaces ──
    tm = sorted(k.manager.shared_nucleus.core.get_collection_members(f"{s_target}:members") or [])
    ti = k.manager.shared_nucleus.core.get_aliases_by_key(tm[0]) if tm else []
    ti = ti[0] if ti else (tm[0] if tm else "")
    it = g("vlab.item", {"source": ti}).get("result") or {}
    check(f"[{shape}] guest vlab.item answers for a public target item",
          len(it.get("observations") or []) >= 2, str(it.get("count_total")))
    tr = g("source.trace", {"id": ti}).get("result") or {}
    check(f"[{shape}] guest source.trace answers for a public target item",
          len(tr.get("observations") or []) >= 2, str(len(tr.get("observations") or [])))

    # ── an ADMIN is unaffected: sees the Radu bench, gets the answer key ──
    _als = a("bench.ls", {})
    check(f"[{shape}] admin bench.ls DOES include the Radu bench",
          "wb:radulab" in {r.get("bench") for r in (_als.get("benches") or [])}, "")
    _ac = a("lens.compare", {"a": run_a, "b": run_b, "key": "vis:observes", "truth": "species_symbol"})
    check(f"[{shape}] admin lens.compare KEEPS the answer key (truth_known>0)",
          (_ac.get("summary") or {}).get("truth_known", 0) > 0, str(_ac.get("summary")))


def main():
    _run("thesaurus", "nucleus cell")
    _run("seeds", "single-store cell")
    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("\nRESULT: PASS — a guest reads the public Concept Laboratory (bench.ls/info/runs, vlab.item, "
          "source.trace, lens.compare) read-only; the Radu-scoped bench is absent from listings and "
          "refused on direct read (-32001); the answer key never leaves the admitted circle (guest "
          "truth=null, truth_known=0, no atom stored); the admin is unaffected — both cell shapes.")
    sys.exit(0)


if __name__ == "__main__":
    main()
