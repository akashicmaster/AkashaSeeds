#!/usr/bin/env python3
"""
FormulaConcept._pairings eval — the shared traversal behind each domain's `X.pairs` operator.

_pairings follows typed pairing edges (out + incoming) from an atom, optionally restricted to
a target namespace, ranked by pairing strength. It is the ONE shared mechanism; each domain
(wine.pairs → cheese, cheese.pairs → wine, …) skins it with a clear, single-purpose operator.

  PA1 target-ns    — wine → only the cheese pairings (a dish pairing on the same node is
                     excluded when target_ns='cheese').
  PA2 no filter    — with no target_ns, all pairings come back (cheese + dish).
  PA3 incoming     — the cheese side sees the wine back through the incoming edge.
  PA4 strength     — a wine paired to a cheese by two relations outranks a one-relation pair.

Run:  python test/formula_pairing_eval.py
"""
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
os.environ["AKASHA_NO_AUTOLEARN"] = "1"

_results = []


def record(name, ok, detail=""):
    _results.append((name, ok, detail))
    print(f"  {'OK  ' if ok else '!! FAIL'}  {name:14} {detail}")


def main():
    print("\n  FormulaConcept._pairings eval — shared pairing traversal\n")
    from lib.akasha.kernel import KernelDispatcher
    from lib.akasha.concepts.recipe import RecipeConcept
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_pair_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin", "passphrase": "pw"}}, "id": "g"}, "local")

    def loc(m, **data):
        return k.dispatch({"jsonrpc": "2.0", "method": m,
                           "params": {"session_token": "admin", "data": data}, "id": 1}, "local")

    # A tiny gastronomy graph (universal, so it is scope-visible): one wine paired to a cheese
    # (by two relations) and a dish (by one).
    keys = {}
    for alias, desc in (("wine:test_barolo", "Barolo — Nebbiolo, Piedmont."),
                        ("cheese:test_parm", "Parmigiano Reggiano."),
                        ("dish:test_risotto", "Risotto alla Milanese.")):
        r = loc("def", name=alias, description=desc, scope="universal")
        keys[alias] = (r.get("result") or {}).get("key")

    loc("ln", src="wine:test_barolo", dst="cheese:test_parm", rel="pairing:regional_pairing",
        scope="universal")
    loc("ln", src="wine:test_barolo", dst="cheese:test_parm", rel="pairing:accord",
        scope="universal")
    loc("ln", src="wine:test_barolo", dst="dish:test_risotto", rel="pairing:regional_pairing",
        scope="universal")

    session = k.manager.get_session("admin")
    rc = RecipeConcept(session)
    RELS = ["pairing:regional_pairing", "pairing:accord", "pairing:sweetness_with_saltiness"]

    # PA1 — wine → cheese only.
    p1 = rc._pairings(keys["wine:test_barolo"], RELS, target_ns="cheese")
    names1 = [x["name"] for x in p1]
    record("PA1 target-ns", names1 == ["cheese:test_parm"], f"cheese_pairs={names1}")

    # PA2 — no target filter → cheese + dish.
    p2 = rc._pairings(keys["wine:test_barolo"], RELS)
    names2 = {x["name"] for x in p2}
    record("PA2 no filter", names2 == {"cheese:test_parm", "dish:test_risotto"},
           f"all_pairs={sorted(names2)}")

    # PA3 — the cheese sees the wine back through the incoming edge.
    p3 = rc._pairings(keys["cheese:test_parm"], RELS, target_ns="wine", incoming=True)
    names3 = [x["name"] for x in p3]
    record("PA3 incoming", names3 == ["wine:test_barolo"], f"wine_pairs={names3}")

    # PA4 — the two-relation cheese pair outranks the one-relation dish pair.
    strengths = {x["name"]: x["strength"] for x in p2}
    record("PA4 strength",
           strengths.get("cheese:test_parm", 0) > strengths.get("dish:test_risotto", 0),
           f"strengths={strengths}")

    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"\n  {passed}/{total} passed\n")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
