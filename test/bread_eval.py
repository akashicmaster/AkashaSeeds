#!/usr/bin/env python3
"""
BreadConcept eval — the bread / パン dictionary (sweets_bread_c, Wikidata).

Same family shape as small plates and sweets: dish:* items singled out by bread:all, each sys:is_a
one or more sub-types (dish:flatbread / dish:sourdough … sys:is_a dish:bread), per-type set
bread:<type>, P495 country, P2012 cuisine, P186 ingredient. Loads a small slice into the shared
nucleus and drives the operators as an authed user AND a guest.

  BR1 search    — bread.search finds a bread by name.
  BR2 ls type   — bread.ls type=flatbread returns the flatbreads (the bread:<type> set axis).
  BR3 ls country— bread.ls country=india returns the Indian breads (dish:from set axis).
  BR4 intersect — type=flatbread cuisine=indian intersects the axes.
  BR5 get       — bread.get resolves sub-type(s) + cuisines + ingredients.
  BR6 exclude   — the umbrella (dish:bread) and sub-type concepts are not items.
  BR7 guest     — READ-level: a guest can browse.

Run:  python test/bread_eval.py
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
    print(f"  {'OK  ' if ok else '!! FAIL'}  {name:12} {detail}")


_DEFS = {
    "dish:bread": "Bread — the bread umbrella (パン).",
    "dish:flatbread": "Flatbread — a flat bread.", "dish:sourdough": "Sourdough — a leavened bread.",
    "cuisine:indian": "Indian cuisine.", "cuisine:french": "French cuisine.",
    "ingred:grain:wheat": "Wheat — a cereal grain.",
    "dish:naan": "Naan — an Indian leavened flatbread.",
    "dish:roti": "Roti — an Indian unleavened flatbread.",
    "dish:pain_au_levain": "Pain au levain — a French sourdough.",
}
_ISA = [
    ("dish:flatbread", "dish:bread"), ("dish:sourdough", "dish:bread"),
    ("dish:naan", "dish:flatbread"), ("dish:roti", "dish:flatbread"),
    ("dish:pain_au_levain", "dish:sourdough"),
]
_REL = [
    ("dish:naan", "cuisine:indian", "thesaurus:related"),
    ("dish:naan", "ingred:grain:wheat", "thesaurus:related"),
    ("dish:roti", "cuisine:indian", "thesaurus:related"),
    ("dish:pain_au_levain", "cuisine:french", "thesaurus:related"),
]
_SETS = [
    ("bread:all", "dish:naan"), ("bread:all", "dish:roti"), ("bread:all", "dish:pain_au_levain"),
    ("bread:flatbread", "dish:naan"), ("bread:flatbread", "dish:roti"),
    ("bread:sourdough", "dish:pain_au_levain"),
    ("dish:from:india", "dish:naan"), ("dish:from:india", "dish:roti"),
    ("dish:from:france", "dish:pain_au_levain"),
]


def main():
    print("\n  BreadConcept eval — bread / パン dictionary\n")
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_bread_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin", "passphrase": "pw"}}, "id": "g"}, "local")

    def loc(m, **data):
        return k.dispatch({"jsonrpc": "2.0", "method": m,
                           "params": {"session_token": "admin", "data": data}, "id": 1}, "local")

    for a, d in _DEFS.items():
        loc("def", name=a, description=d, scope="universal")
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

    r = net("bread.search", atok, q="naan").get("result") or {}
    record("BR1 search", any("naan" in x["name"].lower() for x in r.get("results", [])),
           f"n={r.get('count')}")

    fb = {x["name"] for x in (net("bread.ls", atok, type="flatbread").get("result") or {}).get("results", [])}
    record("BR2 ls type", fb == {"naan", "roti"}, f"flatbread={sorted(fb)}")

    ind = {x["name"] for x in (net("bread.ls", atok, country="india").get("result") or {}).get("results", [])}
    record("BR3 ls country", ind == {"naan", "roti"}, f"india={sorted(ind)}")

    both = {x["name"] for x in (net("bread.ls", atok, type="flatbread", cuisine="indian").get("result") or {}).get("results", [])}
    record("BR4 intersect", both == {"naan", "roti"}, f"flatbread∩indian={sorted(both)}")

    r = net("bread.get", atok, id="dish:naan").get("result") or {}
    record("BR5 get", r.get("types") == ["flatbread"] and r.get("cuisines") == ["indian"]
           and r.get("ingredients") == ["grain:wheat"],
           f"types={r.get('types')} cuisines={r.get('cuisines')} ingredients={r.get('ingredients')}")

    alln = {x["name"] for x in (net("bread.search", atok, q="").get("result") or {}).get("results", [])}
    record("BR6 exclude", alln == {"naan", "roti", "pain au levain"}, f"items={sorted(alln)}")

    g = net("session.guest.create")
    gtok = ((g.get("result") or {}).get("binding_key")
            or (g.get("result") or {}).get("session_token"))
    rg = net("bread.get", gtok, id="dish:pain_au_levain")
    record("BR7 guest", "result" in rg and rg["result"].get("types") == ["sourdough"],
           f"guest_types={(rg.get('result') or {}).get('types') or rg.get('error')}")

    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"\n  {passed}/{total} passed\n")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
