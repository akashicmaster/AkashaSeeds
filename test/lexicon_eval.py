#!/usr/bin/env python3
"""
lexicon eval — first-class relations & namespaces (read-side).

Relations and namespaces are short cryptic strings. The lexicon makes each a defined
atom (reldef:<rel> / nsdef:<ns>) the ontology carries, and resolves a per-set SALIENT
relation profile that inherits down the is_a/part_of hierarchy. This eval builds those
definitions as plain graph writes (exactly what an `.ak` author would produce) and
checks the read side.

  L1 rel description     — reldef:<rel> content is returned for a relation string.
  L2 namespace desc      — nsdef:<ns> content resolves, incl. shorter-prefix fallback.
  L3 salient direct      — a set's own rel:salient profile is returned, weight-ordered.
  L4 salient inherited   — ingredient's salient `varieties` flows down to fruit.
  L5 pinpoint salient    — a rel:salient link on the atom itself is included, first.
  L6 graceful absence    — undefined rel/namespace → None (never an error).

Run:  python test/lexicon_eval.py
"""
import os, sys, tempfile, hashlib
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT); sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
os.environ["AKASHA_NO_AUTOLEARN"] = "1"

_results = []
def record(name, ok, detail=""):
    _results.append((name, ok, detail))
    print(f"  {'OK  ' if ok else '!! FAIL'}  {name:18} {detail}")


def main():
    print("\n  lexicon eval — first-class relations & namespaces\n")
    from lib.akasha.composite import AkashaEngine, NucleusEngine
    from lib.akasha import lexicon as lx

    base = tempfile.mkdtemp(prefix="akasha_lex_")
    nuc = NucleusEngine(f"{base}/nucleus.db")
    cell = AkashaEngine(f"{base}/cell.db")
    cell.attach_nucleus(nuc)

    def K(s): return hashlib.sha256(s.encode()).hexdigest()

    def define(alias, content, coll=None):
        k = K(alias)
        nuc.core.put_chunk_raw(k, content, "{}", "system", "verified", 1.0)
        nuc.core.put_alias(k, alias)
        if coll:
            nuc.core.add_to_collection(coll, k)
        return k

    def link(src_alias, dst_alias, rel, w=1.0):
        s = nuc.core.get_key_by_alias(src_alias) or K(src_alias)
        d = nuc.core.get_key_by_alias(dst_alias) or K(dst_alias)
        nuc.core.put_link_raw(s, d, rel, w=w, author="system", status="verified", ts=1.0)

    # ── Relation & namespace definitions (what an .ak author writes) ─────────────
    define("reldef:thesaurus:related", "related — links concepts that share meaning (thesaurus).", "rels")
    define("reldef:varieties", "varieties — the kinds/cultivars this concept subsumes.", "rels")
    define("reldef:rec:sweetness", "sweetness — perceived sugar intensity (0–10).", "rels")
    define("nsdef:dna:taste", "dna:taste — innate gustatory qualities (sweet, sour, bitter…).", "namespaces")
    define("nsdef:emo", "emo — Plutchik emotion axes.", "namespaces")

    # ── A small category hierarchy: fruit is_a ingredient ───────────────────────
    define("ingredient", "A food building block.")
    define("fruit", "A sweet edible plant part.")
    define("apple", "apple.")
    # membership: apple is_a fruit ; fruit is_a ingredient
    link("apple", "fruit", "sys:is_a")
    nuc.core.add_to_collection("fruit", nuc.core.get_key_by_alias("apple"))
    link("fruit", "ingredient", "sys:is_a")
    nuc.core.add_to_collection("ingredient", nuc.core.get_key_by_alias("fruit"))

    # salient profiles: ingredient → varieties(3); fruit → sweetness(2)
    link("ingredient", "reldef:varieties", lx.SALIENT_REL, w=3.0)
    link("fruit", "reldef:rec:sweetness", lx.SALIENT_REL, w=2.0)

    # L1 — rel description.
    d = lx.rel_description(cell, "thesaurus:related")
    record("L1 rel description", bool(d) and d.startswith("related —"), f"{d!r}")

    # L2 — namespace description + shorter-prefix fallback (dna:taste:sweet → dna:taste).
    d1 = lx.namespace_description(cell, "dna:taste")
    d2 = lx.namespace_description(cell, "dna:taste:sweet")   # falls back to dna:taste
    record("L2 namespace desc", bool(d1) and d1 == d2, f"exact={bool(d1)} fallback_match={d1==d2}")

    # L3 — salient profile of `fruit` set includes its own sweetness (weight-ordered).
    fruit_key = nuc.core.get_key_by_alias("fruit")
    fr = lx.resolve_salient_rels(cell, fruit_key)
    record("L3 salient direct", "rec:sweetness" in fr, f"fruit salient={fr}")

    # L4 — inheritance: apple (is_a fruit is_a ingredient) sees BOTH sweetness & varieties.
    apple_key = nuc.core.get_key_by_alias("apple")
    ap = lx.resolve_salient_rels(cell, apple_key)
    record("L4 salient inherited", ("varieties" in ap and "rec:sweetness" in ap),
           f"apple salient={ap}")

    # L5 — pinpoint salient on the atom itself is included and ranked first (depth 0).
    link("apple", "reldef:thesaurus:related", lx.SALIENT_REL, w=9.0)
    ap2 = lx.resolve_salient_rels(cell, apple_key)
    record("L5 pinpoint salient", ap2 and ap2[0] == "thesaurus:related", f"apple salient={ap2}")

    # L6 — graceful absence.
    none_rel = lx.rel_description(cell, "no:such:rel")
    none_ns  = lx.namespace_description(cell, "nope")
    record("L6 graceful absence", none_rel is None and none_ns is None,
           f"rel={none_rel} ns={none_ns}")

    # L7 — gap detection: `apple` (is_a fruit is_a ingredient) declares varieties &
    #      sweetness salient but has NEITHER, so find_link_voids reports both as salient
    #      voids. Add a varieties link and it drops out; the void set is category-aware.
    voids = cell.find_link_voids(apple_key)
    sal_missing = {v["missing"] for v in voids if v.get("salient")}
    record("L7 salient voids", {"varieties", "rec:sweetness"} <= sal_missing,
           f"salient voids={sorted(sal_missing)}")

    link("apple", "reldef:varieties", "varieties")   # apple now HAS a varieties edge
    voids2 = cell.find_link_voids(apple_key)
    sal_missing2 = {v["missing"] for v in voids2 if v.get("salient")}
    record("L8 void closes", "varieties" not in sal_missing2 and "rec:sweetness" in sal_missing2,
           f"after adding varieties, salient voids={sorted(sal_missing2)}")

    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"\n  {passed}/{total} passed\n")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
