#!/usr/bin/env python3
"""
Recipe reference eval — ontology dish → structured recipe (description → steps).

The recipe ontology (TheMealDB, ~744 dishes) stores each dish as ONE described atom in
the shared nucleus: "<Title> (<Cat> · <Cuisine> · <Country>). Ingredients: <m> <name>; ….
Method: <step 1 …> step 2 …. Source: <url>". This eval drives the two operators that turn
that back into the recipe model:

  RF1 parse       — _parse_dish splits title/axes/ingredients(+measures)/steps/source.
  RF2 get         — recipe.reference.get PROJECTS a dish atom into a card (steps parsed
                    on the fly), guest-readable, no materialisation.
  RF3 clone       — recipe.reference.clone MATERIALISES it into the caller's own editable
                    recipe (a real step per instruction, an ingredient per parsed line);
                    the new recipe is then a normal editable recipe.view.
  RF4 markers     — a dish with explicit 'step N' markers splits on them; one without
                    falls back to sentences.

Run:  python test/recipe_reference_eval.py
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


# Two real-shaped dish atoms (the exact grammar the importer emits).
_DISH_STEPMARK = ("Adana kebab (Lamb · Turkish · Turkey). Ingredients: 2 large Romano Pepper; "
                  "800g Lamb Mince; 3 tablespoons Red Pepper Paste; 1 tsp Salt. Method: "
                  "step 1 Finely chop the peppers in a food processor. step 2 Tip into a bowl "
                  "with the mince and paste. step 3 Knead well for 2-3 mins. step 4 Shape onto "
                  "skewers and grill. Source: https://example.com/adana")
_DISH_PROSE = ("Achiote Oil (Miscellaneous · Colombia). Ingredients: 2 cups Vegetable Oil; "
               "4 tablespoons Achiote Seeds. Method: Heat the oil and Achiote seeds in a small "
               "skillet over medium heat for 2 to 3 minutes. Don't let the seeds turn black. "
               "Remove from the heat and let stand for 5 minutes. Strain the oil and store. "
               "Source: https://example.com/achiote")


def main():
    print("\n  recipe reference eval — ontology dish → structured recipe\n")
    from lib.akasha.concepts.recipe import _parse_dish
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_ref_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin", "passphrase": "pw"}}, "id": "g"}, "local")

    # RF1 — pure parser check.
    p = _parse_dish(_DISH_STEPMARK)
    rf1 = (p["title"] == "Adana kebab" and p["category"] == "Lamb" and p["cuisine"] == "Turkish"
           and len(p["ingredients"]) == 4 and len(p["steps"]) == 4
           and p["ingredients"][1] == {"raw": "800g Lamb Mince", "qty": "800", "unit": "g",
                                       "name": "Lamb Mince"}
           and p["ingredients"][0]["name"] == "large Romano Pepper"
           and p["ingredients"][2] == {"raw": "3 tablespoons Red Pepper Paste", "qty": "3",
                                       "unit": "tablespoons", "name": "Red Pepper Paste"}
           and p["source"].endswith("/adana"))
    record("RF1 parse", rf1,
           f"title={p['title']!r} ings={len(p['ingredients'])} steps={len(p['steps'])} "
           f"ing1={p['ingredients'][1]}")

    # Load the two dishes into the shared nucleus (the way a universal ontology load does).
    from lib.akasha.jcl.workspace_context import system_context
    nuc = k.manager.get_session("admin").nucleus
    with system_context():
        a = nuc.put_atom(_DISH_STEPMARK, {"type": "atom"}, author="system.librarian")
        nuc.set_alias(a, "recipe:adana_kebab"); nuc.set_alias(a, "recipe:mealdb:53262")
        nuc.put_link(a, nuc.put_atom("lamb", {"type": "atom"}, author="system.librarian"),
                     "thesaurus:related")   # (ingred link shape isn't asserted here)
        b = nuc.put_atom(_DISH_PROSE, {"type": "atom"}, author="system.librarian")
        nuc.set_alias(b, "recipe:achiote_oil"); nuc.set_alias(b, "recipe:mealdb:53527")

    def net(method, tok=None, **fields):
        p_ = {"session_token": tok} if tok else {}
        p_.update(fields)
        return k.dispatch({"jsonrpc": "2.0", "method": method, "params": p_, "id": 9}, "network")

    atok = net("auth.verify", user_id="admin", passphrase="pw")["result"]["session_token"]

    # RF2 — reference.get projects a dish (guest-readable).
    g = net("session.guest.create")
    gtok = (g.get("result") or {}).get("binding_key") or (g.get("result") or {}).get("session_token")
    ref = net("recipe.reference.get", gtok, id="recipe:mealdb:53262")["result"]
    rf2 = (ref.get("reference") is True and ref["title"] == "Adana kebab"
           and len(ref["steps"]) == 4 and len(ref["ingredients"]) == 4
           and ref["axes"]["ethnic"] == ["Turkish"])
    record("RF2 get", rf2,
           f"title={ref.get('title')!r} steps={len(ref.get('steps', []))} guest_ok={'reference' in ref}")

    # RF3 — reference.clone materialises an editable recipe in the caller's cortex.
    cl = net("recipe.reference.clone", atok, id="recipe:mealdb:53262")["result"]
    rid = cl["recipe_id"]
    card = net("recipe.view", atok, recipe=rid)["result"]
    rf3 = (cl.get("status") == "cloned" and cl["steps"] == 4 and cl["ingredients"] == 4
           and card["counts"]["steps"] == 4 and card["mine"] is True
           and card["steps"][0]["text"].startswith("Finely chop")
           and any(i["name"] == "Lamb Mince" and i["qty"] == "800" for i in card["ingredients"]))
    record("RF3 clone", rf3,
           f"status={cl.get('status')} steps={card['counts']['steps']} "
           f"editable_mine={card.get('mine')}")

    # RF4 — the prose dish (no 'step N') splits into sentence steps.
    ref2 = net("recipe.reference.get", atok, id="recipe:achiote_oil")["result"]
    rf4 = (len(ref2["steps"]) >= 3 and ref2["title"] == "Achiote Oil"
           and ref2["ingredients"][0]["name"] == "Vegetable Oil")
    record("RF4 markers", rf4,
           f"prose_steps={len(ref2['steps'])} title={ref2['title']!r}")

    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"\n  {passed}/{total} passed\n")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
