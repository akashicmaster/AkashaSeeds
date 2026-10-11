#!/usr/bin/env python3
"""
milinda_lab.py — the stylometry (文献測定学) thought-experiment driver.

Builds the *Milindapañha* stratification field on a throwaway Cell, streams in a feature×locus
measurement matrix through `io.ingest model=sty`, and reads where the composition seams (成立層境界)
stand — then emits the six projection fixtures the Archives lab renders.

Convention (same as app/scripts/mobility_lab.py): FLOW via the CLI (`sys.cli_exec` — exercises the
parser + router every run), VISUALISE via RPC (direct dispatch for the projection payloads). With
--trace the run prints its `[rpc]→[cli]→[rpc]` sequence.

  python app/scripts/milinda_lab.py --trace
  python app/scripts/milinda_lab.py --emit-projection app/archives/labo/stylometry
  python app/scripts/milinda_lab.py --matrix path/to/real_matrix.jsonl   # substitute real measurements

The built-in matrix is a DEFENSIBLE ILLUSTRATIVE table grounded in the philology (the Chinese
Nāgasenabhikṣusūtra parallel ends after Book III; the dilemma-formula appears in Book IV; the
simile density spikes in Book VII — Opamma). Replace it with measured values via --matrix or, on a
live Cell, `io.ingest model=sty into=milindapanha path=<matrix.jsonl>`.
"""
import argparse, hashlib, json, os, sys, tempfile, shlex

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.environ.setdefault("AKASHA_SKIP_AUTOINSTALL", "1")

WORK = "milindapanha"

# ── the catalog (durable form lives in app/ontology/base3/stylometry.ak) ──
WITNESSES = [
    ("pali", "Pāli Milindapañha (PTS ed.)", "pali"),
    ("chinese_nagasena", "Nāgasenabhikṣusūtra 那先比丘經 (T1670)", "lzh"),
]
LAYERS = [
    ("core", "The core dialogues", "The original *Milindapañha* — the part with a Chinese parallel."),
    ("additions", "The later additions", "Books IV–VII; absent from the Chinese, likely appended in Sri Lanka."),
]
# id, title, layer, attested-in (witnesses)
LOCI = [
    ("b1", "I · Bāhira-kathā (frame)",           "core",      "pali,chinese_nagasena"),
    ("b2", "II · Lakkhaṇa-pañha",                "core",      "pali,chinese_nagasena"),
    ("b3", "III · Vimaticchedana-pañha",         "core",      "pali,chinese_nagasena"),
    ("b4", "IV · Meṇḍaka-pañha (the dilemmas)",  "additions", "pali"),
    ("b5", "V · Anumāna-pañha",                  "additions", "pali"),
    ("b6", "VI · Dhutaṅga-pañha",                "additions", "pali"),
    ("b7", "VII · Opamma-kathā-pañha (similes)", "additions", "pali"),
]
FEATURES = [
    ("dialogue_marker_rate", "Dialogue-marker rate", "Frequency of the Q/A dialogue formulae (bhante Nāgasena …).", "core"),
    ("dilemma_formula_rate", "Dilemma-formula rate", "Frequency of the meṇḍaka 'two-horned question' framing.", "additions"),
    ("simile_rate",          "Simile density",       "Rate of explicit similes (opamma).", "additions"),
    ("avg_sentence_len",     "Mean sentence length", "Average words per sentence.", ""),
    ("mattr",                "Vocabulary richness",  "Moving-average type–token ratio (MATTR).", ""),
    ("hapax_ratio",          "Hapax ratio",          "Share of once-occurring word-types.", ""),
    ("attested_in_chinese",  "Chinese attestation",  "1 if the locus has a Nāgasenabhikṣusūtra parallel, else 0.", ""),
]
SEAMS = [
    ("frame_core",     "b1", "Frame ▸ core — the secular prologue vs the doctrinal dialogues."),
    ("core_additions", "b3", "Core ▸ additions — the end of the Chinese parallel; the principal join."),
    ("similes",        "b6", "A minor join before the similes book (Opamma)."),
]
HYPS = [
    ("two_layer",  "Two-layer (mainstream)", "Books I–III are the original work translated into Chinese; "
        "IV–VII are a later Sinhalese addition. One seam, after Book III.", "core_additions", "core,additions"),
    ("three_layer","Three-layer", "A secular frame (I), a core of dialogues (II–III), and the dilemmas and "
        "later material (IV–VII). Two seams.", "frame_core,core_additions", "core,additions"),
    ("unitary",    "Substantially unified", "A minority/traditional view: the work is essentially one "
        "composition. No stylometric seam is decisive.", "", ""),
]
SOURCES = [
    ("demieville_1924", "Les versions chinoises du Milindapañha", "Paul Demiéville", "1924",
        "two_layer,three_layer", "unitary", "BEFEO 24 (1924), pp. 1–258"),
    ("rhys_davids_1890", "The Questions of King Milinda", "T.W. Rhys Davids", "1890",
        "two_layer", "", "Sacred Books of the East 35–36 (1890–94)"),
    ("vonhinuber_1996", "A Handbook of Pāli Literature", "Oskar von Hinüber", "1996",
        "two_layer,three_layer", "", "§172–174"),
    ("horner_1963", "Milinda's Questions", "I.B. Horner", "1963", "two_layer", "", "PTS translation (1963–64)"),
    ("tarn_1938", "The Greeks in Bactria and India", "W.W. Tarn", "1938", "", "",
        "on Menander/Milinda (r. c.165–130 BCE)"),
]
# the feature × locus matrix (illustrative; grounded in the philology). value per (locus, feature).
MATRIX = {
    "b1": {"dialogue_marker_rate": 0.52, "dilemma_formula_rate": 0.01, "simile_rate": 0.11, "avg_sentence_len": 14.0, "mattr": 0.71, "hapax_ratio": 0.43, "attested_in_chinese": 1},
    "b2": {"dialogue_marker_rate": 0.73, "dilemma_formula_rate": 0.02, "simile_rate": 0.14, "avg_sentence_len": 12.4, "mattr": 0.70, "hapax_ratio": 0.41, "attested_in_chinese": 1},
    "b3": {"dialogue_marker_rate": 0.70, "dilemma_formula_rate": 0.03, "simile_rate": 0.16, "avg_sentence_len": 13.1, "mattr": 0.70, "hapax_ratio": 0.41, "attested_in_chinese": 1},
    "b4": {"dialogue_marker_rate": 0.33, "dilemma_formula_rate": 0.61, "simile_rate": 0.23, "avg_sentence_len": 22.3, "mattr": 0.62, "hapax_ratio": 0.34, "attested_in_chinese": 0},
    "b5": {"dialogue_marker_rate": 0.31, "dilemma_formula_rate": 0.29, "simile_rate": 0.21, "avg_sentence_len": 21.0, "mattr": 0.61, "hapax_ratio": 0.33, "attested_in_chinese": 0},
    "b6": {"dialogue_marker_rate": 0.29, "dilemma_formula_rate": 0.17, "simile_rate": 0.25, "avg_sentence_len": 20.1, "mattr": 0.60, "hapax_ratio": 0.32, "attested_in_chinese": 0},
    "b7": {"dialogue_marker_rate": 0.41, "dilemma_formula_rate": 0.20, "simile_rate": 0.86, "avg_sentence_len": 18.6, "mattr": 0.64, "hapax_ratio": 0.38, "attested_in_chinese": 0},
}


def main():
    ap = argparse.ArgumentParser(description="Run the Milindapañha stylometry stratification experiment.")
    ap.add_argument("--matrix", help="JSONL of {locus,feature,value,witness} cells (default: built-in illustrative matrix)")
    ap.add_argument("--emit-projection", metavar="DIR", help="write the six projection fixtures (sty_*.json) to DIR")
    ap.add_argument("--trace", action="store_true", help="echo every operation as [rpc]/[cli] lines")
    ap.add_argument("--keep", action="store_true", help="keep the throwaway Cell dir")
    args = ap.parse_args()

    from lib.akasha.api import client
    base = tempfile.mkdtemp(prefix="milinda_")
    gw = client.embedded(base, "seeds", load_ontology=False)
    k = gw.kernel_client

    step = [0]
    def _trace(kind, line):
        if args.trace:
            step[0] += 1
            print("%3d ┃ [%s] %s" % (step[0], kind, line))

    def D(method, data, tok="admin"):
        _trace("rpc", method + " " + json.dumps(data, ensure_ascii=False)[:90])
        r = gw.dispatch({"jsonrpc": "2.0", "method": method,
                         "params": {"session_token": tok, "data": data}, "id": "m"}, "local")
        return r.get("result") if isinstance(r, dict) else r

    def C(method, **kw):
        parts = [method] + ["%s=%s" % (kk, shlex.quote(str(vv))) for kk, vv in kw.items()]
        line = " ".join(parts)
        _trace("cli", line)
        return gw.dispatch({"jsonrpc": "2.0", "method": "sys.cli_exec",
                            "params": {"session_token": "admin", "data": {"command": line}}, "id": "c"}, "local")

    # ── [rpc] bootstrap ──
    D("kernel.genesis_rite", {"user_name": "admin", "passphrase": hashlib.sha256(b"pw").hexdigest()})

    # ── [cli] FLOW: build the catalog ──
    C("sty.work", id=WORK, title="Milindapañha — the Questions of King Milinda", lang="pali")
    for wid, title, lang in WITNESSES:
        C("sty.witness", work=WORK, id=wid, title=title, lang=lang)
    for lid, title, desc in LAYERS:
        C("sty.layer", work=WORK, id=lid, title=title, desc=desc)
    prev = ""
    for lid, title, layer, attested in LOCI:
        kw = dict(work=WORK, id=lid, title=title, layer=layer, attested=attested)
        if prev:
            kw["after"] = prev
        C("sty.locus", **kw)
        prev = lid
    for fid, title, desc, higher in FEATURES:
        C("sty.feature", id=fid, title=title, desc=desc, higher=higher)
    for sid, after, desc in SEAMS:
        C("sty.seam", work=WORK, id=sid, after=after, desc=desc)
    for hid, title, desc, seams, layers in HYPS:
        C("sty.hyp", work=WORK, id=hid, title=title, desc=desc, seams=seams, layers=layers)
    for sid, title, author, year, supports, contests, locator in SOURCES:
        C("sty.source", id=sid, title=title, author=author, year=year,
          supports=supports, contests=contests, locator=locator)

    # ── [cli] FLOW: stream the matrix through io.ingest model=sty ──
    if args.matrix:
        mpath = os.path.abspath(args.matrix)
    else:
        mpath = os.path.join(base, "milinda_matrix.jsonl")
        with open(mpath, "w", encoding="utf-8") as fh:
            for lid, _t, _l, _a in LOCI:
                for fid, _ft, _fd, _h in FEATURES:
                    fh.write(json.dumps({"locus": lid, "feature": fid,
                                         "value": MATRIX[lid][fid], "witness": "pali"}) + "\n")
    C("io.allow", dir=os.path.dirname(mpath))
    ing = C("io.ingest", model="sty", into=WORK, path=mpath)
    if args.trace:
        res = ing.get("result") if isinstance(ing, dict) else ing
        print("    ┗━ ingested:", json.dumps(res, ensure_ascii=False)[:120])

    # ── [rpc] VISUALISE: read where the seams stand + emit the fixtures ──
    seams = D("sty.seams", {"work": WORK})
    primary = (seams or {}).get("primary_seam") or {}
    print("\n▸ primary seam falls AFTER: %s  (strength %.2f, drivers: %s)" % (
        primary.get("after", "—"), primary.get("strength", 0.0), ", ".join(primary.get("drivers", []))))
    for j in (seams or {}).get("ranked", [])[:3]:
        print("    %s ▸ %s   strength %.2f   [%s]" % (
            j["after"], j["before"], j["strength"], ", ".join(j["drivers"])))

    if args.emit_projection:
        outdir = os.path.abspath(args.emit_projection)
        os.makedirs(outdir, exist_ok=True)
        fixtures = {
            "sty_trajectory.json": D("sty.project", {"work": WORK, "mode": "trajectory"}),
            "sty_matrix.json":     D("sty.matrix", {"work": WORK}),
            "sty_seams.json":      D("sty.seams", {"work": WORK}),
            "sty_hypotheses.json": D("sty.project", {"work": WORK, "mode": "hypotheses"}),
            "sty_layers.json":     D("sty.project", {"work": WORK, "mode": "layers"}),
            "sty_sources.json":    D("sty.project", {"work": WORK, "mode": "sources"}),
        }
        for fn, payload in fixtures.items():
            with open(os.path.join(outdir, fn), "w", encoding="utf-8") as fh:
                json.dump(payload, fh, ensure_ascii=False, indent=2)
        print("\n▸ wrote %d fixtures to %s" % (len(fixtures), outdir))

    if not args.keep:
        import shutil
        shutil.rmtree(base, ignore_errors=True)


if __name__ == "__main__":
    main()
