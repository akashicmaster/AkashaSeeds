#!/usr/bin/env python3
"""
DrinkConcept eval — the beverage PRODUCT dictionary (the superset), with components, producer and
the method flag, plus the spirit product/component DUAL ROLE.

Seeds a drink slice the way the packs deliver it (cocktails with cocktail:base/uses material
links, a wine varietal, a spirit brand + its distillery via whiskey:made_by, a wine region that
is NOT a drink), runs the canonical normalizer as the ingestion hook does, then drives the
operators.

  DR1 search    — drink.search finds a drink by name across categories.
  DR2 superset  — drink:all = cocktails + wine varietals + spirit brands; NOT wine regions and
                  NOT producers (distilleries).
  DR3 category  — drink.ls category=spirit / cocktail selects by category (the sub-domain).
  DR4 has_recipe— drink.ls recipe=yes = the method-carrying drinks (cocktails).
  DR5 made_from — a cocktail's components (cocktail:base/uses → sys:made_from).
  DR6 made_by   — a spirit's producer (whiskey:made_by → sys:made_by); category=spirit.
  DR7 dual role — a spirit BRAND is a drink PRODUCT and also a cocktail COMPONENT (made_from).
  DR8 guest     — READ-level: a guest can browse the superset.

Run:  python test/drink_eval.py
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


def main():
    print("\n  DrinkConcept eval — beverage product dictionary (superset) + dual role\n")
    from lib.akasha.kernel import KernelDispatcher
    from lib.akasha.ontology_normalize import OntologyNormalizer
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_drink_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin", "passphrase": "pw"}}, "id": "g"}, "local")

    def loc(m, **data):
        return k.dispatch({"jsonrpc": "2.0", "method": m,
                           "params": {"session_token": "admin", "data": data}, "id": 1}, "local")

    for a, d in [("role:product", "product."), ("role:component", "component."),
                 ("role:method", "method."), ("role:producer", "producer."),
                 ("drink", "Drink super-concept."), ("cocktail", "Cocktail category."),
                 ("wine", "Wine category."), ("spirit", "Spirit category."),
                 ("producer", "Producer super-concept."), ("meal", "Meal."),
                 ("ingredient", "Ingredient."), ("recipe", "Recipe.")]:
        loc("def", name=a, description=d, scope="universal")

    for a, d in [("cocktail:margarita", "Margarita — a tequila sour cocktail."),
                 ("cocktail:rusty_nail", "Rusty Nail — Scotch and Drambuie."),
                 ("wine:varietal:merlot", "Merlot — a soft red wine grape."),
                 ("wine:region:rioja", "Rioja — a Spanish wine region (a place, not a drink)."),
                 ("whiskey:brand:lagavulin_16", "Lagavulin 16 — an Islay single malt Scotch."),
                 ("whiskey:distillery:lagavulin", "Lagavulin distillery — an Islay distillery."),
                 ("spirit:tequila", "Tequila — an agave base spirit."),
                 ("ing:lime", "Lime — a citrus fruit.")]:
        loc("def", name=a, description=d, scope="universal")

    # legacy per-pack material + producer links:
    ln = [{"method": "kernel.memory.link",
           "params": {"src": "cocktail:margarita", "dst": "spirit:tequila", "rel": "cocktail:base"}},
          {"method": "kernel.memory.link",
           "params": {"src": "cocktail:margarita", "dst": "ing:lime", "rel": "cocktail:uses"}},
          {"method": "kernel.memory.link",
           "params": {"src": "cocktail:rusty_nail", "dst": "whiskey:brand:lagavulin_16",
                      "rel": "cocktail:base"}},   # a cocktail made from a spirit BRAND (dual role)
          {"method": "kernel.memory.link",
           "params": {"src": "whiskey:brand:lagavulin_16", "dst": "whiskey:distillery:lagavulin",
                      "rel": "whiskey:made_by"}}]
    for s in ln:
        loc(s["method"], **s["params"])

    sess = k.manager.get_session("admin")
    cores = [getattr(sess.local_cortex, "core", None),
             getattr(getattr(sess, "nucleus", None), "core", None)]
    for s in OntologyNormalizer(cores).plan(link_steps=ln):
        loc(s["method"], **s["params"])

    def net(_rpc, tok=None, **fields):
        p = {"session_token": tok} if tok else {}
        p.update(fields)
        return k.dispatch({"jsonrpc": "2.0", "method": _rpc, "params": p, "id": 9}, "network")

    atok = net("auth.verify", user_id="admin", passphrase="pw")["result"]["session_token"]

    # DR1 — search.
    r = net("drink.search", atok, q="margarita").get("result") or {}
    record("DR1 search", any("margarita" in x["name"].lower() for x in r.get("results", [])),
           f"n={r.get('count')}")

    # DR2 — superset: cocktails + wine varietals + spirit brands; not regions/producers.
    r = net("drink.search", atok, q="").get("result") or {}
    names = {x["name"] for x in r.get("results", [])}
    ok2 = ({"margarita", "rusty nail", "merlot", "lagavulin 16"} <= names
           and "rioja" not in names and "lagavulin distillery" not in names)
    record("DR2 superset", ok2, f"drinks={sorted(names)}")

    # DR3 — category axis.
    sp = {x["name"] for x in (net("drink.ls", atok, category="spirit").get("result") or {}).get("results", [])}
    co = {x["name"] for x in (net("drink.ls", atok, category="cocktail").get("result") or {}).get("results", [])}
    record("DR3 category", sp == {"lagavulin 16"} and co == {"margarita", "rusty nail"},
           f"spirit={sorted(sp)} cocktail={sorted(co)}")

    # DR4 — the method-carrying subset (cocktails).
    wr = {x["name"] for x in (net("drink.ls", atok, recipe="yes").get("result") or {}).get("results", [])}
    record("DR4 has_recipe", wr == {"margarita", "rusty nail"}, f"with_recipe={sorted(wr)}")

    # DR5 — a cocktail's components.
    r = net("drink.get", atok, id="cocktail:margarita").get("result") or {}
    mf = r.get("made_from") or []
    record("DR5 made_from", r.get("category") == "cocktail" and r.get("has_recipe")
           and any("tequila" in x for x in mf) and any("lime" in x for x in mf),
           f"category={r.get('category')} made_from={mf}")

    # DR6 — a spirit's producer.
    r = net("drink.get", atok, id="whiskey:brand:lagavulin_16").get("result") or {}
    record("DR6 made_by", r.get("category") == "spirit"
           and any("lagavulin" in x for x in (r.get("made_by") or [])),
           f"category={r.get('category')} made_by={r.get('made_by')}")

    # DR7 — dual role: the spirit brand is a PRODUCT (above) AND a cocktail COMPONENT here.
    r = net("drink.get", atok, id="cocktail:rusty_nail").get("result") or {}
    record("DR7 dual role", any("lagavulin" in x for x in (r.get("made_from") or [])),
           f"rusty_nail.made_from={r.get('made_from')}")

    # DR8 — guest READ.
    g = net("session.guest.create")
    gtok = ((g.get("result") or {}).get("binding_key")
            or (g.get("result") or {}).get("session_token"))
    rg = net("drink.get", gtok, id="wine:varietal:merlot")
    record("DR8 guest", "result" in rg and rg["result"].get("category") == "wine",
           f"guest_category={(rg.get('result') or {}).get('category') or rg.get('error')}")

    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"\n  {passed}/{total} passed\n")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
