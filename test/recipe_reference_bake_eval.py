#!/usr/bin/env python3
"""
recipe.reference.bake eval — the shared reference library becomes guest-searchable.

The ontology ships ~744 `recipe:<slug>` reference dishes (TheMealDB etc.). They are
readable one-at-a-time via recipe.reference.get, but recipe.ls / recipe.suggest — the
multi-axis pickers the app needs — only list *recipe-model instances*, so the library
was invisible to browse/suggest. recipe.reference.bake materialises each reference dish
into a structured recipe-model instance IN THE NUCLEUS (universal), reusing
recipe.reference.clone's decomposition, so every session (guests included) can list and
suggest them.

  RB1 bake         — admin bakes the reference library → structured cards created, no errors.
  RB2 guest ls     — a guest (no login) sees the baked recipes via recipe.ls.
  RB3 guest axis   — a guest can recipe.suggest by axis (ethnic=…) and get the right recipe.
  RB4 idempotent   — re-baking bakes nothing new (all skipped) — no duplicate steps.
  RB5 admin-only   — a guest cannot bake (catalog-manager gate holds).

Run:  python test/recipe_reference_bake_eval.py
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


# Two reference dishes in the shared catalogue's description format
# ("<Title> (<category> · <cuisine> · <country>). Ingredients: …. Method: …. Source: …").
_DISHES = {
    "recipe:test_adobo": (
        "Chicken Adobo (Main · Filipino · Philippines). "
        "Ingredients: chicken 500 g; soy sauce 60 ml; vinegar 60 ml; garlic 4 clove. "
        "Method: Brown the chicken pieces. Add soy sauce, vinegar and garlic, then "
        "simmer 30 min. Reduce the sauce and serve. Source: test-adobo"),
    "recipe:test_ratatouille": (
        "Ratatouille (Vegetarian · French · France). "
        "Ingredients: aubergine 1; courgette 2; tomato 4; onion 1. "
        "Method: Slice the vegetables thinly. Layer in a dish and bake 45 min. "
        "Source: test-rata"),
}


def _load_reference_dishes(session):
    """Write the reference dishes into the shared nucleus (universal), as the ontology
    loader does for `recipe:*` atoms."""
    from lib.akasha.jcl.workspace_context import system_context
    nuc = session.nucleus
    with system_context():
        for alias, content in _DISHES.items():
            key = nuc.put_atom(content, {"type": "atom", "role": "dish"},
                               author="system.librarian")
            nuc.set_alias(key, alias)


def _list_field(res, *names):
    for n in names:
        v = (res or {}).get(n)
        if isinstance(v, list):
            return v
    return []


def main():
    print("\n  recipe.reference.bake eval — shared library → guest-searchable recipes\n")
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_rbake_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin", "passphrase": "pw"}}, "id": "g"}, "local")

    _load_reference_dishes(k.manager.get_session("admin"))

    def net(method, tok=None, **fields):
        p = {"session_token": tok} if tok else {}
        p.update(fields)
        return k.dispatch({"jsonrpc": "2.0", "method": method, "params": p, "id": 9}, "network")

    atok = net("auth.verify", user_id="admin", passphrase="pw")["result"]["session_token"]

    # RB1 — admin bakes the reference library.
    b = net("recipe.reference.bake", atok, all="yes")
    br = b.get("result") or {}
    rb1 = (br.get("baked") == 2 and not br.get("errors") and br.get("total") >= 2)
    record("RB1 bake", rb1,
           f"baked={br.get('baked')} skipped={br.get('skipped')} "
           f"errors={br.get('errors')} total={br.get('total')}")

    # RB2 — a guest sees the baked recipes via recipe.ls.
    g = net("session.guest.create")
    gtok = ((g.get("result") or {}).get("binding_key")
            or (g.get("result") or {}).get("session_token"))
    ls = net("recipe.ls", gtok).get("result") or {}
    titles = {r.get("title", "") for r in _list_field(ls, "recipes")}
    rb2 = (ls.get("count", 0) >= 2 and "Chicken Adobo" in titles and "Ratatouille" in titles)
    record("RB2 guest ls", rb2, f"count={ls.get('count')} titles={sorted(titles)}")

    # RB3 — a guest can suggest by axis (ethnic=Filipino → adobo).
    sg = net("recipe.suggest", gtok, ethnic="Filipino").get("result") or {}
    sug = _list_field(sg, "suggestions", "recipes")
    rb3 = any("Adobo" in (s.get("title") or "") for s in sug)
    record("RB3 guest axis", rb3,
           f"ethnic=Filipino -> {[s.get('title') for s in sug]}")

    # RB4 — re-baking is idempotent (nothing new; all skipped).
    b2 = net("recipe.reference.bake", atok, all="yes").get("result") or {}
    rb4 = (b2.get("baked") == 0 and b2.get("skipped") >= 2)
    record("RB4 idempotent", rb4,
           f"baked={b2.get('baked')} skipped={b2.get('skipped')}")

    # RB5 — a guest cannot bake (catalog-manager gate).
    gb = net("recipe.reference.bake", gtok, all="yes")
    err = gb.get("error") or {}
    rb5 = ("result" not in gb) and ("catalog_denied" in str(err) or err.get("code") in (-32003, -32001))
    record("RB5 admin-only", rb5, f"guest_bake_error={err.get('code')} {str(err.get('message'))[:40]}")

    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"\n  {passed}/{total} passed\n")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
