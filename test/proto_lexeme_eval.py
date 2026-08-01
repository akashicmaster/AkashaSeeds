#!/usr/bin/env python3
"""
Proto-word / lexeme eval — the concept navigator follows the sys:is_a FAMILY (sys:is_a ∪
specializes) and roots the vocabulary at `lexeme`, per docs/for-llm/proto-word-subsumption-spec.md.

Seeds the reldef subsumption (reldef:specializes sys:is_a reldef:sys:is_a), a proto-word (apple)
with a sense (ingred:fruit:apple specializes apple; ingred:fruit:apple sys:is_a ingredient), then
runs the normalizer's lexeme back-fill and drives the navigator.

  PL1 family    — the navigator's is-a family = {sys:is_a, specializes}.
  PL2 lexeme    — normalizer rolls the proto-word up: concept.roots field=lexeme → apple.
  PL3 sense     — apple's sub-concept (via specializes) is the sense (leaves=yes).
  PL4 multi-parent — the sense appears under BOTH ingredient (sys:is_a) and apple (specializes).
  PL5 dag-safe  — no infinite recursion / duplicate; child_counts are sane.

Run:  python test/proto_lexeme_eval.py
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
    print("\n  Proto-word / lexeme eval — is-a family + vocabulary rooting\n")
    from lib.akasha.kernel import KernelDispatcher
    from lib.akasha.ontology_normalize import OntologyNormalizer
    from lib.akasha.concepts.concept import ConceptConcept
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_lex_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin", "passphrase": "pw"}}, "id": "g"}, "local")

    def loc(m, **data):
        return k.dispatch({"jsonrpc": "2.0", "method": m,
                           "params": {"session_token": "admin", "data": data}, "id": 1}, "local")

    for a, d in [("reldef:sys:is_a", "is a."), ("reldef:specializes", "specializes — a kind of is-a."),
                 ("lexeme", "Lexeme apex."), ("role:component", "component role."),
                 ("ingredient", "Ingredient."), ("apple", "apple"),  # a proto-word (bare)
                 ("ingred:fruit:apple", "Apple — a fruit.")]:
        loc("def", name=a, description=d, scope="universal")
    # the relation subsumption + the sense links
    loc("ln", src="reldef:specializes", dst="reldef:sys:is_a", rel="sys:is_a", scope="universal")
    loc("ln", src="ingredient", dst="role:component", rel="sys:is_a", scope="universal")
    loc("ln", src="ingred:fruit:apple", dst="ingredient", rel="sys:is_a", scope="universal")
    loc("ln", src="ingred:fruit:apple", dst="apple", rel="specializes", scope="universal")

    sess = k.manager.get_session("admin")
    cores = [getattr(sess.local_cortex, "core", None),
             getattr(getattr(sess, "nucleus", None), "core", None)]
    # normalizer lexeme back-fill: apple (a specializes-target) → sys:is_a lexeme
    for s in OntologyNormalizer(cores).plan_lexeme():
        loc(s["method"], **s["params"])

    def net(_rpc, tok=None, **fields):
        p = {"session_token": tok} if tok else {}
        p.update(fields)
        return k.dispatch({"jsonrpc": "2.0", "method": _rpc, "params": p, "id": 9}, "network")

    atok = net("auth.verify", user_id="admin", passphrase="pw")["result"]["session_token"]

    # PL1 — the is-a family includes specializes.
    fam = set(ConceptConcept(sess)._family())
    record("PL1 family", fam == {"sys:is_a", "specializes"}, f"family={sorted(fam)}")

    # PL2 — lexeme roots the proto-word.
    r = net("concept.roots", atok, field="lexeme", depth=1).get("result") or {}
    lex_kids = {c["id"] for c in (r.get("roots") or [{}])[0].get("children", [])}
    record("PL2 lexeme", "apple" in lex_kids, f"lexeme→{sorted(lex_kids)}")

    # PL3 — apple's sub-concept via specializes is the sense.
    r = net("concept.tree", atok, root="apple", depth=1, leaves="yes").get("result") or {}
    apple_kids = {c["id"] for c in (r.get("tree") or {}).get("children", [])}
    record("PL3 sense", "ingred:fruit:apple" in apple_kids, f"apple→{sorted(apple_kids)}")

    # PL4 — the sense also appears under ingredient (via sys:is_a). Multi-parent DAG.
    r = net("concept.tree", atok, root="ingredient", depth=1, leaves="yes").get("result") or {}
    ing_kids = {c["id"] for c in (r.get("tree") or {}).get("children", [])}
    record("PL4 multi-parent", "ingred:fruit:apple" in ing_kids, f"ingredient→{sorted(ing_kids)}")

    # PL5 — DAG-safe: apple has exactly one child (the sense, counted once despite the
    # sys:is_a ∪ specializes family union); expanded with leaves=yes the sense is a childless leaf.
    ra = net("concept.tree", atok, root="apple", depth=2, leaves="yes").get("result") or {}
    at = ra.get("tree", {})
    sense = next((c for c in at.get("children", []) if c["id"] == "ingred:fruit:apple"), None)
    record("PL5 dag-safe",
           at.get("child_count") == 1 and sense is not None and sense.get("child_count", -1) == 0,
           f"apple.child_count={at.get('child_count')} sense.child_count={(sense or {}).get('child_count')}")

    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"\n  {passed}/{total} passed\n")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
