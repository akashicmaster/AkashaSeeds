#!/usr/bin/env python3
"""
Canonical normalization eval — the Product·Component·Method upper ontology, derived AUTOMATICALLY.

Seeds a tiny food slice the way any ontology pack arrives (a dish, an ORPHAN recipe with no dish
entry, a recipe whose dish already exists, an ingredient, and material links), then runs the
OntologyNormalizer exactly as the ingestion hooks do — plan → apply through the normal write
path — and asserts the canonical structure appeared with NO hand-authored links:

  CN1 role/superset — dish sys:is_a meal + in meal:all; ingred sys:is_a ingredient + ingredient:all.
  CN2 domain roles  — meal sys:is_a role:product; recipe sys:is_a role:method.
  CN3 mint-up       — an orphan recipe (recipe:paella, no dish:paella) MINTS dish:paella.
  CN4 method_of     — recipe sys:method_of its product (minted or existing), both directions.
  CN5 subset        — recipe ⊆ meal:all, and the product joins meal:with_recipe.
  CN6 made_from     — product→component material links get a canonical sys:made_from edge.
  CN7 idempotent    — running the plan twice adds nothing new (stable).

Run:  python test/canon_normalize_eval.py
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
    print("\n  Canonical normalization eval — Product·Component·Method (auto-derived)\n")
    from lib.akasha.kernel import KernelDispatcher
    from lib.akasha.ontology_normalize import OntologyNormalizer
    from lib.akasha import canon
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_canon_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin", "passphrase": "pw"}}, "id": "g"}, "local")

    def loc(m, **data):
        return k.dispatch({"jsonrpc": "2.0", "method": m,
                           "params": {"session_token": "admin", "data": data}, "id": 1}, "local")

    # the role super-concepts (normally in ontology/base1/canon_upper.ak).
    for a, d in [("role:product", "product role."), ("role:component", "component role."),
                 ("role:method", "method role."), ("meal", "Meal super-concept."),
                 ("recipe", "Recipe super-concept."), ("ingredient", "Ingredient super-concept."),
                 ("cocktail", "Cocktail super-concept.")]:
        loc("def", name=a, description=d, scope="universal")

    # a food slice as a pack would deliver it (NO canonical links authored by hand):
    for a, d in [("dish:gazpacho", "Gazpacho — a cold Spanish tomato soup."),
                 ("recipe:gazpacho", "Gazpacho (Starter · Spain). Method: blend and chill."),
                 ("recipe:paella", "Paella (Rice · Spain). Method: simmer rice with saffron."),
                 ("ingred:veg:tomato", "Tomato — a red culinary fruit.")]:
        loc("def", name=a, description=d, scope="universal")
    # material links in the legacy per-pack form (thesaurus:related to a component):
    mat_links = [
        {"method": "kernel.memory.link",
         "params": {"src": "dish:gazpacho", "dst": "ingred:veg:tomato", "rel": "thesaurus:related"}},
        {"method": "kernel.memory.link",
         "params": {"src": "recipe:paella", "dst": "ingred:veg:tomato", "rel": "thesaurus:related"}},
    ]
    for s in mat_links:
        loc(s["method"], **s["params"])

    sess = k.manager.get_session("admin")
    cortex = sess.local_cortex
    cores = [getattr(cortex, "core", None), getattr(getattr(sess, "nucleus", None), "core", None)]

    def apply(steps):
        for s in steps:
            loc(s["method"], **s["params"])

    # ── run the normalizer exactly as the ingestion hook does ────────────────────
    plan = OntologyNormalizer(cores).plan(link_steps=mat_links)
    apply(plan)

    def adj(alias):
        key = cortex.resolve_alias(alias)
        return [(cortex._alias_or(d) if hasattr(cortex, "_alias_or") else d, r)
                for d, r in (cortex.get_adjacent_links(key) or [])] if key else []

    def linked(src, dst, rel):
        skey, dkey = cortex.resolve_alias(src), cortex.resolve_alias(dst)
        if not skey or not dkey:
            return False
        return any(d == dkey and r == rel for d, r in (cortex.get_adjacent_links(skey) or []))

    def in_set(setname, alias):
        key = cortex.resolve_alias(alias)
        return bool(key) and key in set(cortex.get_collection_members(setname) or [])

    # CN1 — role taxonomy + superset membership.
    cn1 = (linked("dish:gazpacho", "meal", canon.IS_A) and in_set("meal:all", "dish:gazpacho")
           and linked("ingred:veg:tomato", "ingredient", canon.IS_A)
           and in_set("ingredient:all", "ingred:veg:tomato"))
    record("CN1 role/set", cn1)

    # CN2 — domain super-concepts carry their role.
    cn2 = (linked("meal", "role:product", canon.IS_A)
           and linked("recipe", "role:method", canon.IS_A)
           and linked("ingredient", "role:component", canon.IS_A))
    record("CN2 domain roles", cn2)

    # CN3 — the orphan recipe minted its product.
    minted = cortex.resolve_alias("dish:paella")
    record("CN3 mint-up", bool(minted), f"dish:paella={'minted' if minted else 'MISSING'}")

    # CN4 — method_of both ways (existing product + minted product).
    cn4 = (linked("recipe:gazpacho", "dish:gazpacho", canon.METHOD_OF)
           and linked("recipe:paella", "dish:paella", canon.METHOD_OF))
    record("CN4 method_of", cn4)

    # CN5 — recipe ⊆ meal:all and the product is marked method-carrying.
    cn5 = (in_set("meal:all", "dish:paella") and in_set("meal:with_recipe", "dish:paella")
           and in_set("meal:with_recipe", "dish:gazpacho")
           and linked("recipe:paella", "recipe", canon.IS_A) and in_set("recipe:all", "recipe:paella"))
    record("CN5 subset", cn5)

    # CN6 — material links canonicalized to sys:made_from.
    cn6 = (linked("dish:gazpacho", "ingred:veg:tomato", canon.MADE_FROM)
           and linked("recipe:paella", "ingred:veg:tomato", canon.MADE_FROM))
    record("CN6 made_from", cn6)

    # CN7 — idempotent: a second pass mints nothing new (same dish:paella key, no new members).
    before = set(cortex.get_collection_members("meal:all") or [])
    apply(OntologyNormalizer(cores).plan(link_steps=mat_links))
    after = set(cortex.get_collection_members("meal:all") or [])
    record("CN7 idempotent", before == after and len(before) >= 2,
           f"meal:all={len(after)} (was {len(before)})")

    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"\n  {passed}/{total} passed\n")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
