#!/usr/bin/env python3
"""
genealogy_lab.py — the Genealogy Laboratory driver (cross-provenance over many lenses).

Builds the Ayurveda corpus — Caraka & Suśruta multi-lens stratification, with the Atharvaveda →
classical → Vāgbhaṭa source-stemma — on one throwaway Cell via the `gen.*` operators (the SUPERSET
model), streams each work's matrix through `io.ingest model=gen`, and emits the per-work projection
fixtures + the corpus genealogy + an index, for `/labo/genealogy/`. Stylometry (scripts/
stylometry_lab.py) is the single-lens SUBSET driver; this one uses the full cross-lens surface.

  python app/scripts/genealogy_lab.py --emit-projection app/archives/labo/genealogy
  python app/scripts/genealogy_lab.py --trace

FLOW via the CLI (`sys.cli_exec`), VISUALISE via RPC.
"""
import argparse, hashlib, json, os, sys, tempfile, shlex

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.environ.setdefault("AKASHA_SKIP_AUTOINSTALL", "1")

import app.scripts._ayurveda_corpus as AY

WORKS = [AY.CARAKA, AY.SUSRUTA]                   # the multi-lens stratified works (a fixture set each)
SOURCES = list(AY.SOURCES)

# ── the demo's non-textual layer: real ayurveda:* atoms hung on each stratum (materia medica,
#    formulae, doctrine) so the lab shows Indian real examples beside the philological seams. ──
_CAT_LABEL = {"herb": "herb", "formula": "formula", "dosha": "doṣa", "rasa": "rasa"}


def _atom_label(key):
    """Human display label for an ayurveda:* atom key (last segment, title-cased)."""
    parts = key.split(":")
    tail = parts[-1].replace("_", " ")
    label = tail[:1].upper() + tail[1:] if tail else key
    cat = parts[1] if len(parts) > 2 else (parts[1] if len(parts) > 1 else "concept")
    return label, _CAT_LABEL.get(cat, cat)


def _context_fixture(spec):
    """Per-work materia-medica fixture: each stratum → the real ayurveda atoms it discusses."""
    ctx = spec.get("context") or {}
    if not ctx:
        return {"work": spec["id"], "loci": []}
    titles = {lo[0]: lo[1] for lo in spec["loci"]}
    layers = {lo[0]: lo[2] for lo in spec["loci"]}
    loci = []
    for lo in spec["loci"]:                        # preserve narrative order
        lid = lo[0]
        atoms = ctx.get(lid)
        if not atoms:
            continue
        chips = []
        for key in atoms:
            label, cat = _atom_label(key)
            chips.append({"key": key, "label": label, "category": cat})
        loci.append({"locus": lid, "title": titles.get(lid, lid),
                     "layer": layers.get(lid, ""), "atoms": chips})
    return {"work": spec["id"], "title": spec["title"], "loci": loci}


def main():
    ap = argparse.ArgumentParser(description="Build the Genealogy lab (the Ayurveda corpus) and emit fixtures.")
    ap.add_argument("--emit-projection", metavar="DIR", help="write per-work fixtures + genealogy + index")
    ap.add_argument("--genealogy-root", default="atharvaveda", help="root work for the source-stemma view")
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
        C("gen.work", id=wid, title=spec["title"], lang=spec.get("lang", ""),
          derives=",".join(spec.get("derives", [])), kind="stratified")
        for w in spec.get("witnesses", []):
            C("gen.witness", work=wid, id=w[0], title=w[1], lang=w[2])
        for l in spec.get("layers", []):
            C("gen.layer", work=wid, id=l[0], title=l[1], desc=l[2])
        prev = ""
        for lo in spec["loci"]:
            kw = dict(work=wid, id=lo[0], title=lo[1], layer=lo[2], attested=lo[3])
            if prev:
                kw["after"] = prev
            C("gen.locus", **kw)
            prev = lo[0]
        for f in spec.get("features", []):
            C("gen.feature", id=f[0], title=f[1], desc=f[2], higher=f[3], lens=(f[4] if len(f) > 4 else "stylometry"))
        for s in spec.get("seams", []):
            C("gen.seam", work=wid, id=s[0], after=s[1], desc=s[2])
        for h in spec.get("hyps", []):
            C("gen.hyp", work=wid, id=h[0], title=h[1], desc=h[2], seams=h[3], layers=h[4])
        # matrix → JSONL → io.ingest
        mpath = os.path.join(base, wid + "_matrix.jsonl")
        with open(mpath, "w", encoding="utf-8") as fh:
            for lo in spec["loci"]:
                for f in spec["features"]:
                    fh.write(json.dumps({"locus": lo[0], "feature": f[0],
                                         "value": spec["matrix"][lo[0]][f[0]], "witness": spec["witnesses"][0][0]}) + "\n")
        C("io.allow", dir=os.path.dirname(mpath))
        C("io.ingest", model="gen", into=wid, path=mpath)

    def build_source_node(node):
        nid, title, note, kind, derives = node
        C("gen.work", id=nid, title=title, desc=note, kind=kind, derives=",".join(derives))

    # ── build in dependency order so every @derives_from target already exists ──
    strat_ids = {w["id"] for w in WORKS}
    upstream = [n for n in AY.SOURCE_NODES if not (set(n[4]) & strat_ids)]   # atharvaveda, agnivesha
    downstream = [n for n in AY.SOURCE_NODES if (set(n[4]) & strat_ids)]     # astangahrdaya (synthesis)
    for node in upstream:
        build_source_node(node)
    for spec in WORKS:
        build_work(spec)
    for node in downstream:
        build_source_node(node)
    for s in SOURCES:
        C("gen.source", id=s[0], title=s[1], author=s[2], year=s[3],
          supports=s[4], contests=s[5], locator=s[6])

    # ── report the seams ──
    for spec in WORKS:
        seams = D("gen.seams", {"work": spec["id"]}) or {}
        pr = seams.get("primary_seam") or {}
        lt = (seams.get("locus_titles") or {})
        print("▸ %-18s primary seam after %s  (strength %.2f)" % (
            spec["id"], lt.get(pr.get("after", ""), pr.get("after", "—")), pr.get("strength", 0.0)))

    if args.emit_projection:
        outdir = os.path.abspath(args.emit_projection)
        os.makedirs(outdir, exist_ok=True)
        index = {"works": [], "genealogy": "gen_genealogy.json", "genealogy_root": args.genealogy_root}
        for spec in WORKS:
            wid = spec["id"]
            wdir = os.path.join(outdir, wid)
            os.makedirs(wdir, exist_ok=True)
            fixtures = {
                "gen_trajectory.json": D("gen.project", {"work": wid, "mode": "trajectory"}),
                "gen_matrix.json":     D("gen.matrix", {"work": wid}),
                "gen_seams.json":      D("gen.seams", {"work": wid}),
                "gen_hypotheses.json": D("gen.project", {"work": wid, "mode": "hypotheses"}),
                "gen_layers.json":     D("gen.project", {"work": wid, "mode": "layers"}),
                "gen_sources.json":    D("gen.project", {"work": wid, "mode": "sources"}),
                "gen_cross.json":       D("gen.cross", {"work": wid}),
                "gen_context.json":     _context_fixture(spec),
            }
            for fn, payload in fixtures.items():
                with open(os.path.join(wdir, fn), "w", encoding="utf-8") as fh:
                    json.dump(payload, fh, ensure_ascii=False, indent=2)
            traj = fixtures["gen_trajectory.json"] or {}
            crx = fixtures["gen_cross.json"] or {}
            lenses = [ln["lens"] for ln in (crx.get("lenses") or [])]
            index["works"].append({"id": wid, "dir": wid,
                                   "title": (traj.get("meta") or {}).get("work_title") or spec["title"],
                                   "lenses": lenses})
        gen = D("gen.genealogy", {"root": args.genealogy_root})
        with open(os.path.join(outdir, "gen_genealogy.json"), "w", encoding="utf-8") as fh:
            json.dump(gen, fh, ensure_ascii=False, indent=2)
        with open(os.path.join(outdir, "gen_index.json"), "w", encoding="utf-8") as fh:
            json.dump(index, fh, ensure_ascii=False, indent=2)
        print("\n▸ wrote %d work fixture-sets + genealogy + index to %s" % (len(WORKS), outdir))

    if not args.keep:
        import shutil
        shutil.rmtree(base, ignore_errors=True)


if __name__ == "__main__":
    main()
