#!/usr/bin/env python3
"""
MealConcept eval — the whole-meal (dish) PRODUCT dictionary (the superset), with the recipe and
ingredient layers visible as present-or-missing subsets.

Seeds a food slice, runs the canonical normalizer (as the ingestion hook does) so meal:all /
sys:made_from / sys:method_of exist, then drives the operators as an authed user AND a guest.

  ML1 search    — meal.search finds a meal across the superset.
  ML2 superset  — every dish is listed, whether or not it has a recipe (gazpacho + paella + a
                  recipe-less dish are ALL present).
  ML3 has_recipe— meal.ls recipe=yes limits to the with-method subset.
  ML4 get parts — meal.get shows ingredients (made_from) + recipes (method_of) + present flags.
  ML5 missing   — a meal with neither recipe nor ingredients reports has_recipe/has_ingredients
                  False but is STILL a full dictionary entry.
  ML6 guest     — READ-level: a guest can browse the superset.

Run:  python test/meal_eval.py
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


def main():
    print("\n  MealConcept eval — whole-meal product dictionary (superset)\n")
    from lib.akasha.kernel import KernelDispatcher
    from lib.akasha.ontology_normalize import OntologyNormalizer
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_meal_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin", "passphrase": "pw"}}, "id": "g"}, "local")

    def loc(m, **data):
        return k.dispatch({"jsonrpc": "2.0", "method": m,
                           "params": {"session_token": "admin", "data": data}, "id": 1}, "local")

    for a, d in [("role:product", "product."), ("role:component", "component."),
                 ("role:method", "method."), ("meal", "Meal super-concept."),
                 ("recipe", "Recipe super-concept."), ("ingredient", "Ingredient super-concept.")]:
        loc("def", name=a, description=d, scope="universal")
    for a, d in [("dish:gazpacho", "Gazpacho — a cold Spanish tomato soup."),
                 ("dish:croqueta", "Croqueta — a fried Spanish snack (no recipe yet)."),
                 ("recipe:gazpacho", "Gazpacho (Starter · Spain). Method: blend and chill."),
                 ("recipe:paella", "Paella (Rice · Spain). Method: simmer rice with saffron."),
                 ("ingred:veg:tomato", "Tomato — a red culinary fruit."),
                 ("cuisine:spanish", "Spanish cuisine.")]:
        loc("def", name=a, description=d, scope="universal")
    ln = [{"method": "kernel.memory.link",
           "params": {"src": "dish:gazpacho", "dst": "ingred:veg:tomato", "rel": "thesaurus:related"}},
          {"method": "kernel.memory.link",
           "params": {"src": "dish:gazpacho", "dst": "cuisine:spanish", "rel": "thesaurus:related"}},
          {"method": "kernel.memory.link",
           "params": {"src": "recipe:paella", "dst": "ingred:veg:tomato", "rel": "thesaurus:related"}}]
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

    # ML1 — search.
    r = net("meal.search", atok, q="gazpacho").get("result") or {}
    record("ML1 search", any("gazpacho" in x["name"].lower() for x in r.get("results", [])),
           f"n={r.get('count')}")

    # ML2 — superset: gazpacho, croqueta, AND the minted paella are all present.
    r = net("meal.search", atok, q="").get("result") or {}
    names = {x["name"] for x in r.get("results", [])}
    record("ML2 superset", {"gazpacho", "croqueta", "paella"} <= names, f"meals={sorted(names)}")

    # ML3 — the with-recipe subset.
    r = net("meal.ls", atok, recipe="yes").get("result") or {}
    wr = {x["name"] for x in r.get("results", [])}
    record("ML3 has_recipe", wr == {"gazpacho", "paella"}, f"with_recipe={sorted(wr)}")

    # ML4 — get shows components + methods + flags.
    r = net("meal.get", atok, id="dish:gazpacho").get("result") or {}
    ml4 = (r.get("ingredients") == ["veg:tomato"] and r.get("recipes") == ["gazpacho"]
           and r.get("has_recipe") and r.get("has_ingredients") and r.get("cuisine") == "spanish")
    record("ML4 get parts", ml4,
           f"ing={r.get('ingredients')} rec={r.get('recipes')} cuisine={r.get('cuisine')}")

    # ML5 — a bare meal is still a full entry, with both layers reported missing.
    r = net("meal.get", atok, id="dish:croqueta").get("result") or {}
    record("ML5 missing", r.get("has_recipe") is False and r.get("has_ingredients") is False
           and r.get("name") == "croqueta",
           f"has_recipe={r.get('has_recipe')} has_ingredients={r.get('has_ingredients')}")

    # ML6 — guest READ.
    g = net("session.guest.create")
    gtok = ((g.get("result") or {}).get("binding_key")
            or (g.get("result") or {}).get("session_token"))
    rg = net("meal.get", gtok, id="dish:paella")
    record("ML6 guest", "result" in rg and rg["result"].get("recipes") == ["paella"],
           f"guest_recipes={(rg.get('result') or {}).get('recipes') or rg.get('error')}")

    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"\n  {passed}/{total} passed\n")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
