#!/usr/bin/env python3
"""
IngredientConcept eval — the food/ingredient dictionary (Step 5).

Ingredients are `ingred:<category>:<name>` concept atoms with allergen (bio:allergen) and
seasonality (in_season) links; the category is the alias's second segment. IngredientConcept is
a kinded dictionary (DictionaryConcept with ENTITY_DEPTH=2) with a grouped get. This eval loads
a small slice into the shared nucleus and drives the operators as an authed user AND a guest.

  IN1 search    — ingredient.search finds an ingredient by name.
  IN2 ls cat    — ingredient.ls category=nut returns the nuts, not the fruit.
  IN3 ls allerg — ingredient.ls allergen=tree_nut returns the tree-nut ingredients.
  IN4 ls season — ingredient.ls season=spring returns the spring ingredient.
  IN5 get       — ingredient.get resolves category + note + allergens list + seasons list.
  IN6 guest     — READ-level: a guest (no login) can browse.
  IN7 nutrition — ingredient.nutrition surfaces the bridged USDA food variants + per-basis
                  nutrition (the FDA data in the nutrition pack), and get shows the count.

Run:  python test/ingredient_eval.py
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
    "allergen:tree_nut": "Tree nut allergen.",
    "season:spring": "Spring.", "season:autumn": "Autumn.", "season:winter": "Winter.",
    "ingred:nut:almond": "Almond — a tree nut; sweet, buttery.",
    "ingred:nut:walnut": "Walnut — a tree nut; rich, slightly bitter.",
    "ingred:fruit:strawberry": "Strawberry — a sweet spring/early-summer berry.",
    "ingred:meat:venison": "Venison — lean game meat, autumn/winter.",
    "ingred:seafood:tuna": "Tuna — a prized sushi/ceviche fish.",
    "ingred:seafood:snapper": "Snapper — a white fish for ceviche.",
    # culinary theme labels + their membership sets (base2/culinary_sets.ak)
    "theme:sushi_neta": "寿司ネタ — classic sushi toppings.",
    "theme:ceviche": "ceviche 素材 — raw fish cured in citrus.",
    # a USDA/FDC nutrition entry (nutrition pack), bridged to the strawberry concept
    "food:fruit:strawberries_raw": ("Strawberries, raw — per 100g: 32 kcal, Protein 0.7g, "
                                    "Carbohydrate 7.7g, Sugar 4.9g, Vitamin C 58.8mg"),
}
_SETS = [
    ("culinary:sushi_neta", "ingred:seafood:tuna"),
    ("culinary:ceviche", "ingred:seafood:tuna"),
    ("culinary:ceviche", "ingred:seafood:snapper"),
]
_LINKS = [
    ("ingred:nut:almond", "allergen:tree_nut", "bio:allergen"),
    ("ingred:nut:walnut", "allergen:tree_nut", "bio:allergen"),
    ("ingred:fruit:strawberry", "season:spring", "in_season"),
    ("ingred:meat:venison", "season:autumn", "in_season"),
    ("ingred:meat:venison", "season:winter", "in_season"),
    # the FDA nutrition bridge: food:<usda> --thesaurus:related--> ingred:<concept>
    ("food:fruit:strawberries_raw", "ingred:fruit:strawberry", "thesaurus:related"),
]


def main():
    print("\n  IngredientConcept eval — food/ingredient dictionary\n")
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_ingred_"))
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
    for setname, member in _SETS:
        loc("set.add", name=setname, id=member, scope="universal")

    def net(_rpc, tok=None, **fields):
        p = {"session_token": tok} if tok else {}
        p.update(fields)
        return k.dispatch({"jsonrpc": "2.0", "method": _rpc, "params": p, "id": 9}, "network")

    atok = net("auth.verify", user_id="admin", passphrase="pw")["result"]["session_token"]

    # IN1 — search.
    r = net("ingredient.search", atok, q="strawberry").get("result") or {}
    names = [x["name"] for x in r.get("results", [])]
    record("IN1 search", any("strawberry" in n.lower() for n in names), f"results={names}")

    # IN2 — browse by category.
    r = net("ingredient.ls", atok, category="nut").get("result") or {}
    nuts = {x["name"] for x in r.get("results", [])}
    record("IN2 ls cat", nuts == {"almond", "walnut"}, f"nuts={sorted(nuts)}")

    # IN3 — browse by allergen.
    r = net("ingredient.ls", atok, allergen="tree_nut").get("result") or {}
    tn = {x["name"] for x in r.get("results", [])}
    record("IN3 ls allerg", tn == {"almond", "walnut"}, f"tree_nut={sorted(tn)}")

    # IN4 — browse by season.
    r = net("ingredient.ls", atok, season="spring").get("result") or {}
    sp = {x["name"] for x in r.get("results", [])}
    record("IN4 ls season", sp == {"strawberry"}, f"spring={sorted(sp)}")

    # IN5 — entry with category + allergens + seasons.
    r = net("ingredient.get", atok, id="ingred:meat:venison").get("result") or {}
    in5 = (r.get("category") == "meat" and bool(r.get("note"))
           and r.get("seasons") == ["autumn", "winter"] and r.get("allergens") == [])
    record("IN5 get", in5,
           f"category={r.get('category')} seasons={r.get('seasons')} allergens={r.get('allergens')}")

    # IN6 — guest READ.
    g = net("session.guest.create")
    gtok = ((g.get("result") or {}).get("binding_key")
            or (g.get("result") or {}).get("session_token"))
    rg = net("ingredient.get", gtok, id="ingred:nut:almond")
    in6 = ("result" in rg and rg["result"].get("allergens") == ["tree_nut"])
    record("IN6 guest", in6,
           f"guest_allergens={(rg.get('result') or {}).get('allergens') or rg.get('error')}")

    # IN7 — the FDA/USDA nutrition bridge: ingredient.nutrition surfaces the bridged food
    # variants with per-basis nutrition; get reports the variant count.
    r = net("ingredient.nutrition", atok, id="ingred:fruit:strawberry").get("result") or {}
    row = (r.get("results") or [None])[0]
    got = net("ingredient.get", atok, id="ingred:fruit:strawberry").get("result") or {}
    rep_kcal = ((got.get("nutrition") or {}).get("per_basis") or {}).get("kcal")
    in7 = (r.get("count") == 1 and row is not None
           and abs((row.get("per_basis") or {}).get("kcal", 0) - 32.0) < 0.5
           and got.get("nutrition_variants") == 1 and rep_kcal == 32.0)   # representative (raw)
    record("IN7 nutrition", in7,
           f"count={r.get('count')} kcal={(row or {}).get('per_basis', {}).get('kcal')} "
           f"variants={got.get('nutrition_variants')} rep_kcal={rep_kcal}")

    # IN8 — the culinary `use` grouping (a SET axis): ls use=sushi_neta / ceviche, and get's
    # reverse-lookup `uses` list.
    su = {x["name"] for x in (net("ingredient.ls", atok, use="sushi_neta").get("result") or {}).get("results", [])}
    cv = {x["name"] for x in (net("ingredient.ls", atok, use="ceviche").get("result") or {}).get("results", [])}
    tuna = net("ingredient.get", atok, id="ingred:seafood:tuna").get("result") or {}
    in8 = (su == {"tuna"} and cv == {"tuna", "snapper"}
           and tuna.get("uses") == ["ceviche", "sushi_neta"])
    record("IN8 use", in8,
           f"sushi_neta={sorted(su)} ceviche={sorted(cv)} tuna.uses={tuna.get('uses')}")

    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"\n  {passed}/{total} passed\n")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
