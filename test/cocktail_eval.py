#!/usr/bin/env python3
"""
CocktailConcept eval — the reference cocktail library (Step 4).

Cocktails are attribute-rich `cocktail:*` entities: base spirit(s), taste, strength, glass,
method, garnish, occasion — all typed links. CocktailConcept is a dictionary (reuses the
DictionaryConcept search/ls mechanism) with a recipe-style get. This eval loads a small slice
into the shared nucleus and drives the operators as an authed user AND a guest.

  CT1 search   — cocktail.search finds a cocktail by name.
  CT2 ls base  — cocktail.ls base=gin returns the gin cocktail, not the tequila one.
  CT3 ls stren — cocktail.ls strength=non_alcoholic returns the mocktail.
  CT4 ls method— cocktail.ls method=shaken returns the shaken cocktail.
  CT5 get      — cocktail.get returns the recipe card (base list, method, glass, garnish, taste).
  CT6 exclude  — the strength vocab (cocktail:alcoholic/non_alcoholic) is NOT listed as a cocktail.
  CT7 guest    — READ-level: a guest (no login) can browse.

Run:  python test/cocktail_eval.py
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
    print(f"  {'OK  ' if ok else '!! FAIL'}  {name:11} {detail}")


_DEFS = {
    "spirit:tequila": "Tequila.", "spirit:gin": "Gin.", "liqueur:triple_sec": "Triple sec.",
    "taste:sour": "Sour.", "taste:refreshing": "Refreshing.",
    "cocktail:alcoholic": "Alcoholic strength.", "cocktail:non_alcoholic": "Non-alcoholic.",
    "cocktail:method:shaken": "Shaken.", "cocktail:method:built": "Built.",
    "glassware:coupe": "Coupe.", "glassware:highball_glass": "Highball glass.",
    "garnish:salt_rim": "Salt rim.", "garnish:lime_wedge": "Lime wedge.",
    "occasion:party": "Party.",
    "cocktail:margarita": "Margarita.",
    "cocktail:gin_tonic": "Gin & Tonic.",
    "cocktail:virgin_mojito": "Virgin Mojito — a mocktail.",
    # a TheCocktailDB-schema drink (drinks_c): different rels — cocktail:uses/method/category
    "cocktail:a1": "A1 — Cocktail, alcoholic, served in a cocktail glass.",
    "cocktail:category:cocktail": "Cocktail category.",
    "ing:gin": "Gin — a cocktail ingredient.",
    "ing:grand_marnier": "Grand Marnier — a cocktail ingredient.",
}
_LINKS = [
    ("cocktail:margarita", "spirit:tequila", "cocktail:base"),
    ("cocktail:margarita", "liqueur:triple_sec", "cocktail:base"),
    ("cocktail:margarita", "taste:sour", "cocktail:tastes"),
    ("cocktail:margarita", "cocktail:alcoholic", "cocktail:strength"),
    ("cocktail:margarita", "cocktail:method:shaken", "cocktail:mixed"),
    ("cocktail:margarita", "glassware:coupe", "cocktail:served_in"),
    ("cocktail:margarita", "garnish:salt_rim", "cocktail:garnished_with"),
    ("cocktail:margarita", "occasion:party", "occasion:served_at"),
    ("cocktail:gin_tonic", "spirit:gin", "cocktail:base"),
    ("cocktail:gin_tonic", "taste:refreshing", "cocktail:tastes"),
    ("cocktail:gin_tonic", "cocktail:alcoholic", "cocktail:strength"),
    ("cocktail:gin_tonic", "cocktail:method:built", "cocktail:mixed"),
    ("cocktail:gin_tonic", "glassware:highball_glass", "cocktail:served_in"),
    ("cocktail:virgin_mojito", "taste:refreshing", "cocktail:tastes"),
    ("cocktail:virgin_mojito", "cocktail:non_alcoholic", "cocktail:strength"),
    ("cocktail:virgin_mojito", "cocktail:method:built", "cocktail:mixed"),
    ("cocktail:virgin_mojito", "glassware:highball_glass", "cocktail:served_in"),
    # a1 uses the drinks_c (TheCocktailDB) schema: cocktail:method (not :mixed),
    # cocktail:uses→ing:* (not :base), cocktail:category via sys:is_a
    ("cocktail:a1", "cocktail:category:cocktail", "sys:is_a"),
    ("cocktail:a1", "cocktail:method:shaken",     "cocktail:method"),
    ("cocktail:a1", "glassware:coupe",            "cocktail:served_in"),
    ("cocktail:a1", "ing:gin",                    "cocktail:uses"),
    ("cocktail:a1", "ing:grand_marnier",          "cocktail:uses"),
]


def main():
    print("\n  CocktailConcept eval — reference cocktail library\n")
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_cocktail_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin", "passphrase": "pw"}}, "id": "g"}, "local")

    def loc(m, **data):
        return k.dispatch({"jsonrpc": "2.0", "method": m,
                           "params": {"session_token": "admin", "data": data}, "id": 1}, "local")

    for alias, desc in _DEFS.items():
        loc("def", name=alias, description=desc, scope="universal")
    for s, d, rel in _LINKS:
        loc("ln", src=s, dst=d, rel=rel, scope="universal")

    def net(_rpc, tok=None, **fields):
        p = {"session_token": tok} if tok else {}
        p.update(fields)
        return k.dispatch({"jsonrpc": "2.0", "method": _rpc, "params": p, "id": 9}, "network")

    atok = net("auth.verify", user_id="admin", passphrase="pw")["result"]["session_token"]

    # CT1 — search.
    r = net("cocktail.search", atok, q="margarita").get("result") or {}
    names = [x["name"] for x in r.get("results", [])]
    record("CT1 search", any("margarita" in n.lower() for n in names), f"results={names}")

    # CT2 — browse by base spirit.
    r = net("cocktail.ls", atok, base="gin").get("result") or {}
    gin = {x["name"] for x in r.get("results", [])}
    record("CT2 ls base", "gin tonic" in gin and "margarita" not in gin, f"gin={sorted(gin)}")

    # CT3 — browse by strength.
    r = net("cocktail.ls", atok, strength="non_alcoholic").get("result") or {}
    na = {x["name"] for x in r.get("results", [])}
    record("CT3 ls stren", na == {"virgin mojito"}, f"non_alcoholic={sorted(na)}")

    # CT4 — browse by method: unifies BOTH schemas (margarita via cocktail:mixed,
    # a1 via drinks_c's cocktail:method).
    r = net("cocktail.ls", atok, method="shaken").get("result") or {}
    sh = {x["name"] for x in r.get("results", [])}
    record("CT4 ls method", sh == {"margarita", "a1"}, f"shaken={sorted(sh)}")

    # CT5 — recipe card.
    r = net("cocktail.get", atok, id="cocktail:margarita").get("result") or {}
    ct5 = (set(r.get("base", [])) == {"tequila", "triple_sec"} and r.get("method") == "shaken"
           and r.get("glass") == "coupe" and r.get("garnish") == ["salt_rim"]
           and r.get("taste") == ["sour"] and r.get("strength") == "alcoholic")
    record("CT5 get", ct5,
           f"base={r.get('base')} method={r.get('method')} glass={r.get('glass')} "
           f"garnish={r.get('garnish')}")

    # CT6 — strength vocab is not enumerated as a cocktail.
    r = net("cocktail.search", atok, q="").get("result") or {}
    allnames = {x["name"] for x in r.get("results", [])}
    ct6 = ("alcoholic" not in allnames and "non alcoholic" not in allnames
           and allnames == {"margarita", "gin tonic", "virgin mojito", "a1"})
    record("CT6 exclude", ct6, f"entities={sorted(allnames)}")

    # CT9 — the drinks_c (TheCocktailDB) schema is browsable too: base via cocktail:uses→ing:*,
    # category via sys:is_a, and get gathers the ing:* ingredients into the recipe card.
    lb = {x["name"] for x in (net("cocktail.ls", atok, base="gin").get("result") or {}).get("results", [])}
    lc = {x["name"] for x in (net("cocktail.ls", atok, category="cocktail").get("result") or {}).get("results", [])}
    a1 = net("cocktail.get", atok, id="cocktail:a1").get("result") or {}
    ct9 = ("a1" in lb and lc == {"a1"}
           and set(a1.get("base", [])) == {"gin", "grand_marnier"}
           and a1.get("method") == "shaken" and a1.get("category") == "cocktail")
    record("CT9 drinks_c", ct9,
           f"base=gin→{sorted(lb)} category→{sorted(lc)} a1.base={a1.get('base')} "
           f"a1.category={a1.get('category')}")

    # CT8 — base axis resolves over liqueur:/beverage: too, not just spirit: (margarita's
    # base includes liqueur:triple_sec).
    r = net("cocktail.ls", atok, base="triple_sec").get("result") or {}
    ts = {x["name"] for x in r.get("results", [])}
    record("CT8 base multi", ts == {"margarita"}, f"base=triple_sec(liqueur)={sorted(ts)}")

    # CT7 — guest READ.
    g = net("session.guest.create")
    gtok = ((g.get("result") or {}).get("binding_key")
            or (g.get("result") or {}).get("session_token"))
    rg = net("cocktail.get", gtok, id="cocktail:margarita")
    ct7 = ("result" in rg and rg["result"].get("method") == "shaken")
    record("CT7 guest", ct7,
           f"guest_method={(rg.get('result') or {}).get('method') or rg.get('error')}")

    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"\n  {passed}/{total} passed\n")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
