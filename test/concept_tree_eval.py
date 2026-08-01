#!/usr/bin/env python3
"""
ConceptConcept eval — the concept-hierarchy navigator (sys:is_a up/down only).

Builds a tiny lattice (roles → domains → sub-concepts → a leaf, plus a non-is_a link and a
membership set that must be IGNORED) and drives the navigator as an authed user AND a guest.

  CT1 roots      — concept.roots lists the universal roles with their domain children.
  CT2 field      — concept.roots field=meal descends one field.
  CT3 tree       — concept.tree root=drink descends the sys:is_a tree (cocktail under drink).
  CT4 children   — concept.children id=drink lists immediate sub-concepts, with count.
  CT5 is_a only  — a non-is_a link (made_from) and a membership set are NOT followed.
  CT6 tree ext   — `tree <c> concept=yes` (graph.tree extension) returns the concept tree.
  CT7 guest      — READ-level: a guest can navigate.
  CT8 taxonomy   — taxonomic view: meal expands the branch (dish:tapa) but folds the leaf
                   instance (dish:gilda direct child) into leaf_count; leaves=yes shows it.

Run:  python test/concept_tree_eval.py
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
    "role:product": "product role.", "role:component": "component role.",
    "role:method": "method role.", "role:producer": "producer role.",
    "meal": "Meal — food product.", "drink": "Drink — beverage product.",
    "ingredient": "Ingredient — component.", "cocktail": "Cocktail category.",
    "dish:tapa": "Tapa concept.", "dish:gilda": "Gilda — a tapa.",
    "dish:paella": "Paella — a direct meal instance.",
    "cocktail:margarita": "Margarita — a cocktail instance.",
    "ingred:veg:tomato": "Tomato.",
}
# sys:is_a lattice: role:product ← meal, drink ; drink ← cocktail ← margarita ;
# meal ← dish:tapa ← dish:gilda, and (canon-style flattening) meal ← dish:gilda, dish:paella.
_ISA = [
    ("meal", "role:product"), ("drink", "role:product"),
    ("ingredient", "role:component"), ("cocktail", "drink"),
    ("cocktail:margarita", "cocktail"),
    ("dish:tapa", "meal"), ("dish:gilda", "dish:tapa"),
    ("dish:gilda", "meal"), ("dish:paella", "meal"),      # direct leaf instances of meal
]
# a NON-is_a link and a set that must be ignored by the navigator:
_OTHER = [("dish:gilda", "ingred:veg:tomato", "sys:made_from")]
_SETS = [("meal:all", "dish:gilda")]


def main():
    print("\n  ConceptConcept eval — concept-hierarchy navigator (sys:is_a only)\n")
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_ctree_"))
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
    for s, d, rel in _OTHER:
        loc("ln", src=s, dst=d, rel=rel, scope="universal")
    for setname, member in _SETS:
        loc("set.add", name=setname, id=member, scope="universal")

    def net(_rpc, tok=None, **fields):
        p = {"session_token": tok} if tok else {}
        p.update(fields)
        return k.dispatch({"jsonrpc": "2.0", "method": _rpc, "params": p, "id": 9}, "network")

    atok = net("auth.verify", user_id="admin", passphrase="pw")["result"]["session_token"]

    # CT1 — roots: the roles, each with domain children.
    r = net("concept.roots", atok).get("result") or {}
    roles = {x["id"] for x in r.get("roots", [])}
    prod = next((x for x in r.get("roots", []) if x["id"] == "role:product"), {})
    prod_kids = {c["id"] for c in prod.get("children", [])}
    record("CT1 roots", roles == set(["role:product", "role:component", "role:method", "role:producer"])
           and {"meal", "drink"} <= prod_kids, f"roles={sorted(roles)} product→{sorted(prod_kids)}")

    # CT2 — field descent.
    r = net("concept.roots", atok, field="meal").get("result") or {}
    node = (r.get("roots") or [{}])[0]
    kids = {c["id"] for c in node.get("children", [])}
    record("CT2 field", node.get("field") is None and r.get("field") == "meal" and "dish:tapa" in kids,
           f"meal→{sorted(kids)}")

    # CT3 — tree from drink.
    r = net("concept.tree", atok, root="drink", depth=2).get("result") or {}
    t = r.get("tree", {})
    ck = {c["id"] for c in t.get("children", [])}
    record("CT3 tree", t.get("id") == "drink" and "cocktail" in ck and "ascii" in r,
           f"drink→{sorted(ck)}")

    # CT4 — children of drink.
    r = net("concept.children", atok, id="drink").get("result") or {}
    kids = {c["id"] for c in r.get("results", [])}
    record("CT4 children", kids == {"cocktail"} and r.get("count") == 1, f"drink children={sorted(kids)}")

    # CT5 — is_a only: gilda has a made_from link + a set membership, but NO sys:is_a children,
    # so its concept tree is empty (non-is_a link and the set are ignored).
    r = net("concept.tree", atok, root="dish:gilda", depth=2).get("result") or {}
    g = r.get("tree", {})
    record("CT5 is_a only", g.get("child_count") == 0 and not g.get("children"),
           f"gilda.child_count={g.get('child_count')}")

    # CT6 — the tree command extension: tree <c> concept=yes.
    r = net("graph.tree", atok, target="drink", concept="yes").get("result") or {}
    ck2 = {c["id"] for c in (r.get("tree") or {}).get("children", [])}
    record("CT6 tree ext", r.get("type") == "concept:tree" and "cocktail" in ck2, f"ext drink→{sorted(ck2)}")

    # CT7 — guest READ.
    g = net("session.guest.create")
    gtok = ((g.get("result") or {}).get("binding_key")
            or (g.get("result") or {}).get("session_token"))
    rg = net("concept.roots", gtok)
    record("CT7 guest", "result" in rg and len((rg["result"] or {}).get("roots", [])) >= 1,
           f"guest_roots={len((rg.get('result') or {}).get('roots', []))}")

    # CT8 — taxonomic: meal expands the branch (dish:tapa) but FOLDS the direct leaf instances
    # (dish:paella, dish:gilda) into leaf_count; leaves=yes shows them all.
    mt = (net("concept.tree", atok, root="meal", depth=1).get("result") or {}).get("tree", {})
    branch_ids = {c["id"] for c in mt.get("children", [])}
    all_ids = {c["id"] for c in ((net("concept.tree", atok, root="meal", depth=1, leaves="yes")
                                  .get("result") or {}).get("tree") or {}).get("children", [])}
    record("CT8 taxonomy", branch_ids == {"dish:tapa"} and mt.get("leaf_count") == 2
           and {"dish:tapa", "dish:paella", "dish:gilda"} <= all_ids,
           f"branches={sorted(branch_ids)} leaf_count={mt.get('leaf_count')} all={sorted(all_ids)}")

    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"\n  {passed}/{total} passed\n")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
