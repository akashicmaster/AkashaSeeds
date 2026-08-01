#!/usr/bin/env python3
"""
SmallplateConcept eval — the small-plate / finger-food dictionary (drinks_c-sibling smallplates_c).

Small plates are a special dictionary shape: the dishes live in the SHARED `dish:` namespace
(alongside every base dish and the family concepts), singled out by membership of the
`smallplate:all` umbrella set. SmallplateConcept enumerates its entities from that set
(DictionaryConcept's ENTITY_SET / shared-namespace mode), browses by the cultural type
(`smallplate:<type>` sub-set), country (`dish:from:<country>` set) and cuisine
(`thesaurus:related cuisine:*` link). This eval loads a small slice into the shared nucleus and
drives the operators as an authed user AND a guest.

   SM1 search    — smallplate.search finds a dish by name.
  SM2 ls type    — ls type=tapa returns the tapas (the smallplate:<type> set axis), not the meze.
  SM3 ls country — ls country=spain returns the Spanish plates (dish:from:<country> set axis).
  SM4 intersect  — type=tapa cuisine=spanish intersects the two axes.
  SM5 get        — get resolves cultural type(s) + cuisines + ingredients.
  SM6 exclude    — the umbrella concept (dish:smallplate) and family concepts are not entities;
                   base dishes NOT in smallplate:all are not entities either.
  SM7 multi-type — a dish that is both a tapa and a pincho lists both types.
  SM8 guest      — READ-level: a guest (no login) can browse (incl. a SET axis).

Run:  python test/smallplate_eval.py
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
    print(f"  {'OK  ' if ok else '!! FAIL'}  {name:13} {detail}")


_DEFS = {
    # the umbrella + a couple of family concepts (defined, not entities)
    "dish:smallplate": "Small plate — the umbrella for tapas, pinchos, meze and the rest.",
    "dish:tapa": "Tapa — a small Spanish savoury dish.",
    "dish:pincho": "Pincho — a Basque/northern-Spanish small snack on a skewer.",
    "dish:meze": "Meze — a selection of small Mediterranean dishes.",
    # cuisines
    "cuisine:spanish": "Spanish cuisine.", "cuisine:greek": "Greek cuisine.",
    # an ingredient (base vocab) the bridge points at
    "ingred:seafood:anchovy": "Anchovy — a small oily fish.",
    # the dishes themselves
    "dish:gilda": "Gilda — a Basque pincho of anchovy, olive and pepper on a skewer.",
    "dish:patatas_bravas": "Patatas bravas — fried potato tapa with a spicy sauce.",
    "dish:tzatziki": "Tzatziki — a Greek yoghurt-cucumber meze.",
    # a base dish that is NOT a small plate (must never be enumerated)
    "dish:paella": "Paella — a Valencian rice dish (not a small plate).",
}
_ISA = [
    ("dish:tapa", "dish:smallplate"),
    ("dish:pincho", "dish:smallplate"),
    ("dish:meze", "dish:smallplate"),
    # gilda is BOTH a pincho and a tapa (multi-type)
    ("dish:gilda", "dish:pincho"),
    ("dish:gilda", "dish:tapa"),
    ("dish:patatas_bravas", "dish:tapa"),
    ("dish:tzatziki", "dish:meze"),
]
_REL = [
    ("dish:gilda", "cuisine:spanish", "thesaurus:related"),
    ("dish:gilda", "ingred:seafood:anchovy", "thesaurus:related"),
    ("dish:patatas_bravas", "cuisine:spanish", "thesaurus:related"),
    ("dish:tzatziki", "cuisine:greek", "thesaurus:related"),
]
_SETS = [
    # the umbrella set = every small-plate dish (NOT the family concepts, NOT paella)
    ("smallplate:all", "dish:gilda"),
    ("smallplate:all", "dish:patatas_bravas"),
    ("smallplate:all", "dish:tzatziki"),
    # per-type sub-sets
    ("smallplate:tapa", "dish:gilda"),
    ("smallplate:tapa", "dish:patatas_bravas"),
    ("smallplate:pincho", "dish:gilda"),
    ("smallplate:meze", "dish:tzatziki"),
    # country of origin
    ("dish:from:spain", "dish:gilda"),
    ("dish:from:spain", "dish:patatas_bravas"),
    ("dish:from:greece", "dish:tzatziki"),
]


def main():
    print("\n  SmallplateConcept eval — small-plate / finger-food dictionary\n")
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_smallplate_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin", "passphrase": "pw"}}, "id": "g"}, "local")

    def loc(m, **data):
        return k.dispatch({"jsonrpc": "2.0", "method": m,
                           "params": {"session_token": "admin", "data": data}, "id": 1}, "local")

    for alias, desc in _DEFS.items():
        loc("def", name=alias, description=desc, scope="universal")
    for s, d in _ISA:
        loc("ln", src=s, dst=d, rel="sys:is_a", scope="universal")
    for s, d, rel in _REL:
        loc("ln", src=s, dst=d, rel=rel, scope="universal")
    for setname, member in _SETS:
        loc("set.add", name=setname, id=member, scope="universal")

    def net(_rpc, tok=None, **fields):
        p = {"session_token": tok} if tok else {}
        p.update(fields)
        return k.dispatch({"jsonrpc": "2.0", "method": _rpc, "params": p, "id": 9}, "network")

    atok = net("auth.verify", user_id="admin", passphrase="pw")["result"]["session_token"]

    # SM1 — search.
    r = net("smallplate.search", atok, q="gilda").get("result") or {}
    names = [x["name"] for x in r.get("results", [])]
    record("SM1 search", any("gilda" in n.lower() for n in names), f"results={names}")

    # SM2 — browse by cultural type (the smallplate:<type> set axis).
    r = net("smallplate.ls", atok, type="tapa").get("result") or {}
    tapas = {x["name"] for x in r.get("results", [])}
    record("SM2 ls type", tapas == {"gilda", "patatas bravas"}, f"tapas={sorted(tapas)}")

    # SM3 — browse by country (dish:from:<country> set axis).
    r = net("smallplate.ls", atok, country="spain").get("result") or {}
    sp = {x["name"] for x in r.get("results", [])}
    record("SM3 ls country", sp == {"gilda", "patatas bravas"}, f"spain={sorted(sp)}")

    # SM4 — intersect type and cuisine.
    r = net("smallplate.ls", atok, type="tapa", cuisine="spanish").get("result") or {}
    both = {x["name"] for x in r.get("results", [])}
    record("SM4 intersect", both == {"gilda", "patatas bravas"}, f"tapa∩spanish={sorted(both)}")

    # SM5 — profile with types + cuisines + ingredients.
    r = net("smallplate.get", atok, id="dish:gilda").get("result") or {}
    sm5 = (r.get("types") == ["pincho", "tapa"] and r.get("cuisines") == ["spanish"]
           and r.get("ingredients") == ["seafood:anchovy"])
    record("SM5 get", sm5,
           f"types={r.get('types')} cuisines={r.get('cuisines')} ingredients={r.get('ingredients')}")

    # SM6 — the umbrella/family concepts and non-small-plate base dishes are not entities.
    r = net("smallplate.search", atok, q="").get("result") or {}
    allnames = {x["name"] for x in r.get("results", [])}
    record("SM6 exclude", allnames == {"gilda", "patatas bravas", "tzatziki"},
           f"entities={sorted(allnames)}")

    # SM7 — a multi-type dish lists every family it belongs to.
    r = net("smallplate.ls", atok, type="pincho").get("result") or {}
    pinchos = {x["name"] for x in r.get("results", [])}
    gilda_types = next((x.get("types") for x in r.get("results", []) if x["name"] == "gilda"), None)
    record("SM7 multi-type", pinchos == {"gilda"} and gilda_types == ["pincho", "tapa"],
           f"pinchos={sorted(pinchos)} gilda.types={gilda_types}")

    # SM8 — guest READ (including a SET axis).
    g = net("session.guest.create")
    gtok = ((g.get("result") or {}).get("binding_key")
            or (g.get("result") or {}).get("session_token"))
    rg = net("smallplate.ls", gtok, type="meze")
    gn = {x["name"] for x in (rg.get("result") or {}).get("results", [])}
    rgg = net("smallplate.get", gtok, id="dish:tzatziki")
    record("SM8 guest", gn == {"tzatziki"} and (rgg.get("result") or {}).get("types") == ["meze"],
           f"guest_meze={sorted(gn)} guest_get_types={(rgg.get('result') or {}).get('types')}")

    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"\n  {passed}/{total} passed\n")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
