#!/usr/bin/env python3
"""
Iliad stylometry eval — the single-lens SUBSET model `sty`, two cases in one Cell.

Guards three things:
  1. Two works with overlapping bare ids do NOT collide — the Milindapañha (loci b1..b7) and the
     Iliad (loci il1..il24) build in the same Cell and each keeps its own loci/features/matrix.
     (Regression: before the Iliad loci were work-prefixed, both works minted sty:locus:b1 and the
     Milindapañha's trajectory was corrupted with the Iliad's books/layers.)
  2. `sty.compare` — the single-locus inspection (the Doloneia Test) — reports Book X's distance from
     its neighbours and the corpus centroid, its distinctiveness rank, and the features that set it
     apart, WITHOUT pre-judging it as the top seam or as an interpolation.
  3. The subset boundary holds: `sty` exposes compare/seams but NOT the genealogy-only surface
     (cross / align / alignment / genealogy).

Run:  python app/test/iliad_stylometry_eval.py     (exit 0 = all pass)
"""
import hashlib, os, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT); sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def main():
    import shlex, json
    from lib.akasha.kernel import KernelDispatcher
    from api.gateway import AkashaGateway
    import app.scripts.milinda_lab as M
    import app.scripts._iliad_corpus as IL

    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_iliad_"))
    gw = AkashaGateway(kernel_client=k)

    def C(method, **kw):
        line = " ".join([method] + [f"{a}={shlex.quote(str(v))}" for a, v in kw.items() if str(v) != ""])
        gw.dispatch({"jsonrpc": "2.0", "method": "sys.cli_exec",
                     "params": {"session_token": "admin", "data": {"command": line}}, "id": "c"}, "local")

    def D(method, data):
        r = gw.dispatch({"jsonrpc": "2.0", "method": method,
                         "params": {"session_token": "admin", "data": data}, "id": "m"}, "local")
        return r.get("result") or r.get("error") or {}

    gw.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                 "params": {"session_token": "admin", "data": {"user_name": "admin",
                            "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def build(work, loci, features, matrix, layers=(), seams=(), witness="obs"):
        C("sty.work", id=work, kind="stratified")
        for lid, lt, ly in layers:
            C("sty.layer", work=work, id=lid, title=lt, desc=lt)
        prev = ""
        for lo in loci:
            kw = dict(work=work, id=lo[0], title=lo[1], layer=lo[2], attested="")
            if prev:
                kw["after"] = prev
            C("sty.locus", **kw); prev = lo[0]
        for f in features:
            C("sty.feature", id=f[0], title=f[1], desc=f[2], higher=f[3])
        for s in seams:
            C("sty.seam", work=work, id=s[0], after=s[1], desc=s[2])
        recs = [{"locus": lo[0], "feature": f[0], "value": matrix[lo[0]][f[0]], "witness": witness}
                for lo in loci for f in features]
        D("sty.ingest", {"work": work, "records": recs})

    # build BOTH cases in the one Cell (the collision surface)
    build(M.WORK, M.LOCI, M.FEATURES, M.MATRIX, M.LAYERS, M.SEAMS, witness="pali")
    build(IL.WORK, IL.LOCI, IL.FEATURES, IL.MATRIX, IL.LAYERS, IL.SEAMS, witness="west_teubner")

    # 1 — no collision: each work keeps exactly its own loci
    mm = D("sty.matrix", {"work": M.WORK}); im = D("sty.matrix", {"work": IL.WORK})
    check("Milindapañha keeps its 7 loci (no Iliad bleed-through)", len(mm.get("loci", [])) == 7,
          f"{len(mm.get('loci', []))} loci")
    check("Iliad keeps its 24 loci", len(im.get("loci", [])) == 24, f"{len(im.get('loci', []))} loci")
    check("the two works' loci namespaces are disjoint",
          set(mm.get("loci", [])).isdisjoint(set(im.get("loci", []))),
          "b* vs il* — no shared atom")

    # 2 — the Doloneia Test (sty.compare on Book X)
    cx = D("sty.compare", {"work": IL.WORK, "locus": IL.FOCUS})
    check("sty.compare returns the Doloneia (Book X)", "Doloneia" in (cx.get("title") or ""),
          cx.get("title"))
    check("Book X is measurably distinctive but NOT pre-judged as the sole outlier",
          isinstance(cx.get("rank_by_distinctiveness"), int) and cx["rank_by_distinctiveness"] >= 2
          and cx["of"] == 24, f"rank {cx.get('rank_by_distinctiveness')} of {cx.get('of')}")
    top = [c["feature"].split(":")[-1] for c in (cx.get("feature_contributors") or [])[:3]]
    check("its distinctiveness is driven by hapax / formulaic / vocabulary (the Doloneia signature)",
          "hapax_ratio" in top and "formulaic_density" in top, ", ".join(top))
    check("it carries the honest neighbour + centroid distances",
          cx.get("distance_from_previous") and cx.get("distance_from_next")
          and cx.get("distance_from_corpus_centroid") is not None
          and cx.get("mean_adjacent_distance") is not None,
          f"prev={ (cx.get('distance_from_previous') or {}).get('distance') } "
          f"centroid={cx.get('distance_from_corpus_centroid')}")

    # 3 — the subset boundary: sty has compare/seams, not the genealogy-only verbs
    from app.concepts.sty import StyConcept
    verbs = set(StyConcept.CONCEPT_METHODS)
    check("sty exposes compare + seams (the stylometry surface)",
          {"compare", "seams", "matrix", "project"} <= verbs)
    check("sty does NOT expose the genealogy-only surface (cross/align/alignment/genealogy)",
          not ({"cross", "align", "alignment", "genealogy"} & verbs),
          "single-lens subset")

    print()
    if _fails:
        print("FAILED: " + "; ".join(_fails)); sys.exit(1)
    print("ALL PASS — two stylometry cases (Milindapañha + Iliad) stay isolated in one Cell; the "
          "Doloneia inspection reports Book X's distances and signature without calling it an "
          "interpolation; the sty subset stays narrower than gen.")


if __name__ == "__main__":
    main()
