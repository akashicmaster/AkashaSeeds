#!/usr/bin/env python3
"""
stylometry_lab.py — the Stylometry Laboratory driver (single-lens seam detection).

Builds the Milindapañha on one throwaway Cell via the `sty.*` operators — the single-lens SUBSET of
the Genealogy model (app/concepts/sty.py ⊂ gen.py) — streams its feature×locus matrix through
`io.ingest model=sty`, and emits the per-work projection fixtures for `/labo/stylometry/`. The
multi-lens cross-provenance corpus (Ayurveda: Caraka & Suśruta + the source-stemma) lives in the
Genealogy lab (app/scripts/genealogy_lab.py, the superset `gen.*` surface) — this driver is deliberately
the narrow one: one work, one lens, where does its seam fall.

  python app/scripts/stylometry_lab.py --emit-projection app/archives/labo/stylometry
  python app/scripts/stylometry_lab.py --trace

FLOW via the CLI (`sys.cli_exec`), VISUALISE via RPC.
"""
import argparse, hashlib, json, os, sys, tempfile, shlex

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.environ.setdefault("AKASHA_SKIP_AUTOINSTALL", "1")

import app.scripts.milinda_lab as M
import app.scripts._iliad_corpus as IL

# each case as a uniform work spec (data only — no per-case operator; the sty.* surface builds both)
MILINDA = {
    "id": M.WORK, "title": "Milindapañha — the Questions of King Milinda", "lang": "pali",
    "witnesses": M.WITNESSES, "layers": M.LAYERS, "loci": M.LOCI,
    "features": M.FEATURES, "seams": M.SEAMS, "hyps": M.HYPS, "matrix": M.MATRIX, "sources": M.SOURCES,
    "question": "Where do the strata of a transmitted text meet — and which seam does the evidence support?",
    "intro": ("The Milindapañha is treated as an ordered sequence of books. Each is measured across "
              "lexical, formulaic and dialogic features; adjacent-book discontinuities are surfaced as "
              "candidate seams and compared against competing stratification hypotheses and the Chinese "
              "parallel. A discontinuity is not an attribution."),
}
ILIAD = {
    "id": IL.WORK, "title": "Iliad — the Homeric Epic", "lang": "grc",
    "witnesses": IL.WITNESSES, "layers": IL.LAYERS, "loci": IL.LOCI,
    "features": IL.FEATURES, "seams": IL.SEAMS, "hyps": IL.HYPS, "matrix": IL.MATRIX, "sources": IL.SOURCES,
    "question": IL.QUESTION, "intro": IL.INTRO, "focus": IL.FOCUS, "provenance": IL.PROVENANCE,
}
WORKS = [MILINDA, ILIAD]
SOURCES = list(M.SOURCES) + list(IL.SOURCES)


def main():
    ap = argparse.ArgumentParser(description="Build the Stylometry lab (the Milindapañha) and emit fixtures.")
    ap.add_argument("--emit-projection", metavar="DIR", help="write the per-work fixtures + index")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--keep", action="store_true")
    args = ap.parse_args()

    from lib.akasha.api import client
    base = tempfile.mkdtemp(prefix="stylab_")
    gw = client.embedded(base, "seeds", load_ontology=False)
    k = gw.kernel_client

    step = [0]
    def _trace(kind, line):
        if args.trace:
            step[0] += 1
            print("%3d ┃ [%s] %s" % (step[0], kind, line))

    def D(method, data, tok="admin"):
        _trace("rpc", method + " " + json.dumps(data, ensure_ascii=False)[:80])
        r = gw.dispatch({"jsonrpc": "2.0", "method": method,
                         "params": {"session_token": tok, "data": data}, "id": "m"}, "local")
        return r.get("result") if isinstance(r, dict) else r

    def C(method, **kw):
        line = " ".join([method] + ["%s=%s" % (kk, shlex.quote(str(vv))) for kk, vv in kw.items()])
        _trace("cli", line)
        return gw.dispatch({"jsonrpc": "2.0", "method": "sys.cli_exec",
                            "params": {"session_token": "admin", "data": {"command": line}}, "id": "c"}, "local")

    D("kernel.genesis_rite", {"user_name": "admin", "passphrase": hashlib.sha256(b"pw").hexdigest()})

    def build_work(spec):
        wid = spec["id"]
        C("sty.work", id=wid, title=spec["title"], lang=spec.get("lang", ""), kind="stratified")
        for w in spec.get("witnesses", []):
            C("sty.witness", work=wid, id=w[0], title=w[1], lang=w[2])
        for l in spec.get("layers", []):
            C("sty.layer", work=wid, id=l[0], title=l[1], desc=l[2])
        prev = ""
        for lo in spec["loci"]:
            kw = dict(work=wid, id=lo[0], title=lo[1], layer=lo[2], attested=lo[3])
            if prev:
                kw["after"] = prev
            C("sty.locus", **kw)
            prev = lo[0]
        for f in spec.get("features", []):
            C("sty.feature", id=f[0], title=f[1], desc=f[2], higher=f[3], lens=(f[4] if len(f) > 4 else "stylometry"))
        for s in spec.get("seams", []):
            C("sty.seam", work=wid, id=s[0], after=s[1], desc=s[2])
        for h in spec.get("hyps", []):
            C("sty.hyp", work=wid, id=h[0], title=h[1], desc=h[2], seams=h[3], layers=h[4])
        mpath = os.path.join(base, wid + "_matrix.jsonl")
        with open(mpath, "w", encoding="utf-8") as fh:
            for lo in spec["loci"]:
                for f in spec["features"]:
                    fh.write(json.dumps({"locus": lo[0], "feature": f[0],
                                         "value": spec["matrix"][lo[0]][f[0]], "witness": spec["witnesses"][0][0]}) + "\n")
        C("io.allow", dir=os.path.dirname(mpath))
        C("io.ingest", model="sty", into=wid, path=mpath)

    for spec in WORKS:
        build_work(spec)
    for s in SOURCES:
        C("sty.source", id=s[0], title=s[1], author=s[2], year=s[3],
          supports=s[4], contests=s[5], locator=s[6])

    for spec in WORKS:
        seams = D("sty.seams", {"work": spec["id"]}) or {}
        pr = seams.get("primary_seam") or {}
        lt = (seams.get("locus_titles") or {})
        print("▸ %-18s primary seam after %s  (strength %.2f)" % (
            spec["id"], lt.get(pr.get("after", ""), pr.get("after", "—")), pr.get("strength", 0.0)))

    if args.emit_projection:
        outdir = os.path.abspath(args.emit_projection)
        os.makedirs(outdir, exist_ok=True)
        index = {"works": []}
        for spec in WORKS:
            wid = spec["id"]
            wdir = os.path.join(outdir, wid)
            os.makedirs(wdir, exist_ok=True)
            fixtures = {
                "sty_trajectory.json": D("sty.project", {"work": wid, "mode": "trajectory"}),
                "sty_matrix.json":     D("sty.matrix", {"work": wid}),
                "sty_seams.json":      D("sty.seams", {"work": wid}),
                "sty_hypotheses.json": D("sty.project", {"work": wid, "mode": "hypotheses"}),
                "sty_layers.json":     D("sty.project", {"work": wid, "mode": "layers"}),
                "sty_sources.json":    D("sty.project", {"work": wid, "mode": "sources"}),
            }
            # optional per-case fixtures: the single-locus inspection (Doloneia Test) + provenance
            if spec.get("focus"):
                fixtures["sty_compare.json"] = D("sty.compare", {"work": wid, "locus": spec["focus"]})
            if spec.get("provenance"):
                fixtures["sty_provenance.json"] = {"work": wid, "provenance": spec["provenance"]}
            for fn, payload in fixtures.items():
                with open(os.path.join(wdir, fn), "w", encoding="utf-8") as fh:
                    json.dump(payload, fh, ensure_ascii=False, indent=2)
            traj = fixtures["sty_trajectory.json"] or {}
            index["works"].append({"id": wid, "dir": wid,
                                   "title": (traj.get("meta") or {}).get("work_title") or spec["title"],
                                   "question": spec.get("question", ""), "lenses": ["stylometry"],
                                   "has_compare": bool(spec.get("focus")),
                                   "has_provenance": bool(spec.get("provenance"))})
        with open(os.path.join(outdir, "sty_index.json"), "w", encoding="utf-8") as fh:
            json.dump(index, fh, ensure_ascii=False, indent=2)
        print("\n▸ wrote %d work fixture-set(s) + index to %s" % (len(WORKS), outdir))

    if not args.keep:
        import shutil
        shutil.rmtree(base, ignore_errors=True)


if __name__ == "__main__":
    main()
