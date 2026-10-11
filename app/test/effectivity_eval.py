#!/usr/bin/env python3
"""
B3 §A8 — effectivity: what is IN EFFECT at a chronon coordinate under conditions, and validity expiry.

`effective.at` is a pure Set intersection — the records located at a chronon coordinate (or the union
over a range), narrowed by each `cond:` facet Set (and, when given, a role's visible Set). It stores
nothing. Separately, an atom that expires joins `set:valid:until:<clock>:<pos>` at write time
(`cronon.valid_until`); the nightly retention phase evicts it from the horizon once the clock passes
`<pos>`, and the STORE is never touched (the atom stays readable).

This eval drives both on BOTH cell shapes:
  • two atoms at two chronon coordinates with different `cond:` memberships; `effective.at` returns the
    right one for each (chronon, cond) pair, the union for a range, and the intersection for a range+cond;
  • an atom marked `valid_until` is evicted from the horizon by the sweep once the clock passes its pos
    (`moved>=1`), and is still readable from the store afterwards.

Run:  python test/effectivity_eval.py     (exit 0 = all pass)
"""
import hashlib
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from lib.akasha.concepts import schedules
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []
BENCH = "plants-vision"
BSLUG = "plants_vision"


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _run(series, shape):
    print(f"\n  ── {shape} ({series}) ──")
    from lib.akasha.kernel import KernelDispatcher
    from lib.akasha.concepts.cronon import CrononConcept
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series=series, base_dir=tempfile.mkdtemp(prefix="akasha_eff_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def a(method, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
        return r if "error" in r else (r.get("result") or {})

    a("world.genesis", {})
    a("bench.new", {"name": BENCH, "kind": "learning"})

    cc = CrononConcept(k.manager.get_session("admin"))
    clock = "wb:%s" % BSLUG

    def atom(alias, txt):
        return cc._mk(alias, "[%s] %s" % (alias, txt), {"concept": "eff_test", "label": txt})

    # two atoms, each located at its own bench coordinate + a distinct cond facet
    ka = atom("eff:a", "the mlp row")
    kb = atom("eff:b", "the logreg row")
    c1 = a("cronon.mint", {"clock": clock, "label": "c1"}).get("cronon")     # cronon:wb:...:c1
    c2 = a("cronon.mint", {"clock": clock, "label": "c2"}).get("cronon")     # cronon:wb:...:c2
    cc._add_to_set(c1, ka)
    cc._add_to_set("set:wb:%s:cond:head:mlp" % BSLUG, ka)
    cc._add_to_set(c2, kb)
    cc._add_to_set("set:wb:%s:cond:head:logreg" % BSLUG, kb)
    p1 = int(c1.rsplit(":c", 1)[1]); p2 = int(c2.rsplit(":c", 1)[1])

    # ── effective.at at one coordinate under its cond → exactly that atom ──
    e1 = a("cronon.effective_at", {"bench": BENCH, "chronon": str(p1), "cond": "head=mlp"})
    _al1 = [m.get("alias") for m in (e1.get("members") or [])]
    check(f"[{shape}] effective.at(chronon=c1, head=mlp) returns just the mlp atom",
          _al1 == ["eff:a"], f"members={_al1} count={e1.get('count')}")
    e2 = a("cronon.effective_at", {"bench": BENCH, "chronon": str(p2), "cond": "head=logreg"})
    check(f"[{shape}] effective.at(chronon=c2, head=logreg) returns just the logreg atom",
          [m.get("alias") for m in (e2.get("members") or [])] == ["eff:b"], str(e2.get("members")))
    # a cond that excludes the coordinate's atom → empty
    e3 = a("cronon.effective_at", {"bench": BENCH, "chronon": str(p1), "cond": "head=logreg"})
    check(f"[{shape}] effective.at(chronon=c1, head=logreg) is empty (the cond excludes it)",
          e3.get("count") == 0, str(e3.get("members")))
    # ── a range unions the coordinates; a range + cond intersects ──
    er = a("cronon.effective_at", {"bench": BENCH, "chronon": "%d..%d" % (p1, p2)})
    check(f"[{shape}] effective.at over the range c1..c2 unions both atoms",
          sorted(m.get("alias") for m in (er.get("members") or [])) == ["eff:a", "eff:b"],
          str(er.get("members")))
    erc = a("cronon.effective_at", {"bench": BENCH, "chronon": "%d..%d" % (p1, p2), "cond": "head=mlp"})
    check(f"[{shape}] effective.at over the range narrowed by head=mlp returns just the mlp atom",
          [m.get("alias") for m in (erc.get("members") or [])] == ["eff:a"], str(erc.get("members")))

    # ── the macro forwards to the op ──
    em = a("macro.run", {"name": "effective.at", "bench": BENCH, "chronon": str(p1),
                         "cond": "head=mlp", "as": "inline"})
    _res = (em.get("results") or [{}])[-1]
    _emm = ((_res.get("result") or _res).get("members")) or []
    check(f"[{shape}] macro.run name=effective.at forwards to the op (same one atom)",
          [m.get("alias") for m in _emm] == ["eff:a"], str(em)[:200])

    # ── validity: an atom marked valid_until is evicted from the horizon once the clock passes pos ──
    kv = atom("eff:v", "expires at pos 3 on clock t")
    a("cronon.valid_until", {"id": "eff:v", "clock": "t", "pos": "3"})
    for _i in range(5):                                  # advance clock t past pos 3
        a("cronon.mint", {"clock": "t"})
    res = schedules.retention_expire_validity(k)
    check(f"[{shape}] the retention phase evicts the expired atom (moved>=1)",
          res.get("moved", 0) >= 1 and res.get("membranes", 0) >= 1, str(res))
    # the store is never touched — the atom is still readable
    rd = a("read", {"id": "eff:v"})
    check(f"[{shape}] the expired atom is still readable from the store (horizon-only eviction)",
          not rd.get("error") and bool(rd.get("content") or rd.get("meta") or rd.get("id")), str(rd)[:120])
    # a membrane not yet past its clock does not move
    a("cronon.valid_until", {"id": "eff:a", "clock": "future", "pos": "9999"})
    a("cronon.mint", {"clock": "future"})
    res2 = schedules.retention_expire_validity(k)
    check(f"[{shape}] a not-yet-expired membrane is left alone (only past-due members move)",
          res2.get("moved", 0) == 0, str(res2))


def main():
    print("=" * 78)
    print("B3 §A8 — effectivity (effective.at) + validity expiry")
    print("=" * 78)
    _run("thesaurus", "nucleus cell")
    _run("seeds", "single-store cell")
    print()
    if _fails:
        print("RESULT: FAIL — %d check(s) failed:" % len(_fails))
        for f in _fails:
            print("   - " + f)
        sys.exit(1)
    print("RESULT: PASS — effective.at intersects the chronon coordinate (or range) with the cond facets "
          "(storing nothing), and the nightly validity phase evicts an expired atom from the horizon "
          "while leaving it readable in the store — both cell shapes.")


if __name__ == "__main__":
    main()
