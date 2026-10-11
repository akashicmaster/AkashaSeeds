#!/usr/bin/env python3
"""
birdclef_source_import.py — a FOCUSED BirdCLEF sample into the Source Data Layer (audio corpus).

Dev-side prep (the Grand Principle: datasets are prepared off-line and the cell loads only). Reads a
BirdCLEF `train.csv` (columns primary_label, secondary_labels, type, latitude, longitude, author,
rating, filename, …; audio is .ogg) and imports a CONCENTRATED slice — a few target species, N≈100
records — as Source Atoms in a frozen Source Pool. Concentrating on few species is deliberate: the
within-species variety of `type` (song / call / courtship / alarm …) is where the interesting
expression differences show, so the audio analysis (spectral / MFCC / YAMNet / BirdNET spaces) has
something to cross.

⚠️ AUDIO-BINARY PRINCIPLE (identical to images): the .ogg binary is NEVER imported/stored. Each source
item keeps only a REFERENCE URL (built from the xeno-canto id in the filename, or an `--audio-base`
mirror, or a `--url-col`) plus the row's metadata; the audio observers fetch the clip transiently and
keep only features/embeddings. The item is marked `content_type=audio` so source.modalities detects the
audio modality even for extension-less URLs (a xeno-canto `/download` link).

Selection (concentrate, then diversify WITHIN species):
  --species aaa,bbb   explicit primary_label codes (else auto: the species with the richest `type`
                      variety + enough recordings, taking the FEWEST species needed to reach N)
  --n 100             how many records (type-balanced: round-robin across `type` so courtship / song /
                      call are all represented, not 100 songs)

Usage (against a running daemon):
  python akasha.py --serve   # in another terminal
  python app/scripts/birdclef_source_import.py --csv train.csv --n 100
  python app/scripts/birdclef_source_import.py --csv train.csv --species comsan --audio-base https://my.mirror/train_audio
"""
import argparse
import csv
import json
import os
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

SOURCE_ID = "source:src:birdclef"
POOL = "source:pool:birdclef:focus:v1"
LAB = "birdsong"
_XC_RE = re.compile(r"XC(\d+)", re.IGNORECASE)


def _audio_url(row, audio_base="", url_col=""):
    """A REFERENCE URL for the clip (never the binary). Priority: an explicit url column → an
    `--audio-base` mirror (base/filename) → the xeno-canto id in the filename (…/<id>/download)."""
    if url_col and row.get(url_col):
        return str(row[url_col])
    fn = str(row.get("filename") or "")
    if audio_base and fn:
        return audio_base.rstrip("/") + "/" + fn.lstrip("/")
    m = _XC_RE.search(os.path.basename(fn))
    if m:
        return "https://xeno-canto.org/%s/download" % m.group(1)
    return ""


def select_records(rows, n=100, species=None, audio_base="", url_col=""):
    """Pick a concentrated, type-diverse slice. Returns (records, chosen_species, per_type_counts)."""
    rows = [r for r in rows if r.get("primary_label")]
    want = [s.strip() for s in (species or "").split(",") if s.strip()]
    by_species = {}
    for r in rows:
        by_species.setdefault(r["primary_label"], []).append(r)
    if not want:
        # auto: rank species by (distinct `type` variety, then recording count); take the fewest
        # species needed to reach n — concentration first, but never a single-type monoculture.
        ranked = sorted(by_species.items(),
                        key=lambda kv: (len({str(x.get("type") or "") for x in kv[1]}), len(kv[1])),
                        reverse=True)
        want, acc = [], 0
        for code, rs in ranked:
            want.append(code); acc += len(rs)
            if acc >= n:
                break
    chosen = [r for code in want for r in by_species.get(code, [])]
    # type-balanced round-robin so courtship/song/call all appear, not n copies of one type
    buckets = {}
    for r in chosen:
        buckets.setdefault(str(r.get("type") or "unknown"), []).append(r)
    for b in buckets.values():
        b.sort(key=lambda r: str(r.get("filename") or ""))     # deterministic
    picked, order = [], sorted(buckets)
    while len(picked) < n and any(buckets[t] for t in order):
        for t in order:
            if buckets[t] and len(picked) < n:
                picked.append(buckets[t].pop(0))
    recs, per_type = [], {}
    for r in picked:
        url = _audio_url(r, audio_base, url_col)
        stem = os.path.splitext(os.path.basename(str(r.get("filename") or "")))[0] or (r.get("primary_label") + "_" + str(len(recs)))
        rec = {"id": stem, "url": url, "content_type": "audio", "format": "ogg",
               "primary_label": r.get("primary_label"), "secondary_labels": r.get("secondary_labels"),
               "type": r.get("type"), "latitude": r.get("latitude"), "longitude": r.get("longitude"),
               "author": r.get("author"), "rating": r.get("rating"), "filename": r.get("filename"),
               "common_name": r.get("common_name"), "scientific_name": r.get("scientific_name")}
        recs.append(rec)
        per_type[rec["type"] or "unknown"] = per_type.get(rec["type"] or "unknown", 0) + 1
    return recs, want, per_type


def run(dispatch, records, opts, log=print):
    """Register the BirdCLEF/xeno-canto source, create the pool, acquire the selected clips
    (audio-by-reference), freeze, declare CORPUS, audit. `records` is the already-selected slice.

    A FROZEN pool is never acquired into (the source engine refuses it): it is `skipped` ("corpus unchanged") and
    no `source.acquire`, `pool.create` or `pool.freeze` is issued. Nothing else: no derived version, no repair — a
    changed corpus is a new seed on a new cell. The mobility import makes the same decision."""
    species = opts.get("species") or []
    dispatch("source.register", {"provider": "BirdCLEF / xeno-canto", "collection": "BirdCLEF train_audio",
                                 "name": "birdclef", "uri": "https://www.kaggle.com/competitions/birdclef-2024",
                                 "rights": "See BirdCLEF competition rules / xeno-canto CC licences"})
    log("  [1] source: %s" % SOURCE_ID)
    st = dispatch("source.status", {"pool": POOL}) or {}
    if st.get("exists") and st.get("frozen"):
        have = int(st.get("total") or 0)
        log("  [2] pool %s is FROZEN with %d members — corpus unchanged, nothing to acquire" % (POOL, have))
        au = dispatch("source.audit", {"lab": LAB}) or {}
        return {"pool": POOL, "status": "skipped", "detail": "corpus unchanged", "acquired": 0,
                "members": have, "at_seq": None,
                "modalities": (dispatch("source.modalities", {"pool": POOL}) or {}).get("modalities"),
                "evidence_status": au.get("evidence_status"), "grounded": au.get("grounded")}
    dispatch("source.pool.create", {"name": "birdclef:focus", "version": "v1", "source": SOURCE_ID,
                                    "rule": "focused BirdCLEF slice — species %s, audio by reference (no binary)"
                                            % (",".join(species) or "auto")})
    log("  [2] pool created: %s" % POOL)
    r = dispatch("source.acquire", {"source": SOURCE_ID, "records": records, "id_field": "id", "pool": POOL,
                                    "rule": "focused audio corpus (%d clips, species %s)" % (len(records), ",".join(species))})
    if isinstance(r, dict) and "__error__" in r:
        raise RuntimeError("acquire: %s" % r["__error__"])
    log("  [3] acquired %d clip Source Atoms (audio by URL reference)" % (r or {}).get("acquired", 0))
    members = at_seq = None
    if opts.get("freeze", True):
        fr = dispatch("source.pool.freeze", {"pool": POOL})
        members, at_seq = (fr or {}).get("member_count"), (fr or {}).get("at_seq")
        log("  [4] pool FROZEN: %s members, at_seq=%s" % (members, at_seq))
    decl = dispatch("source.lab.declare", {"lab": LAB, "klass": "CORPUS", "pool": POOL,
                                           "primary_source": SOURCE_ID,
                                           "fixture_policy": "audio referenced by URL; the binary is never stored"})
    log("  [5] birdsong declared CORPUS → evidence_status=%s" % (decl or {}).get("evidence_status"))
    au = dispatch("source.audit", {"lab": LAB})
    return {"pool": POOL, "acquired": (r or {}).get("acquired", 0), "members": members, "at_seq": at_seq,
            "modalities": dispatch("source.modalities", {"pool": POOL}).get("modalities"),
            "evidence_status": (au or {}).get("evidence_status"), "grounded": (au or {}).get("grounded")}


def _load_csv(path):
    with open(path, "r", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def emit_bundle(recs, chosen, per_type, out_dir):
    """DEV-SIDE prep for the auto-bootstrap: write the selected slice as `records.jsonl.gz` (one
    reference record per line — id / url / coded metadata, NEVER a binary) + a `manifest.json`, so the
    seed can bundle it and the deploy target auto-loads at boot with NO operator step (the Grand
    Principle: dev-side prep → the target loads only). Mirrors app/assets/cma_visual_curation/."""
    import gzip
    import json
    os.makedirs(out_dir, exist_ok=True)
    recs_gz = os.path.join(out_dir, "records.jsonl.gz")
    with gzip.open(recs_gz, "wt", encoding="utf-8") as fh:
        for r in recs:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    man = {"corpus": "birdclef", "source": SOURCE_ID, "pool": POOL, "lab": LAB,
           "count": len(recs), "species": chosen, "per_type": per_type,
           "audio_by_reference": True,
           "note": "focused BirdCLEF audio slice — reference URLs only, no binaries; observers fetch transiently"}
    with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(man, fh, ensure_ascii=False, indent=2)
    return recs_gz, man


# What this corpus is LISTENED to with, and the spaces its panel draws. Corpus decisions, like the
# CMA's observers: installing an ear later changes the signature and the delta is observed then.
OBSERVERS = "spectral,mfcc,chroma,rhythm,yamnet,panns,birdnet"
SPACES = ("spectral", "mfcc", "chroma", "rhythm", "yamnet", "panns", "birdnet")
EARS = ("librosa", "soundfile", "ai_edge_litert", "panns_inference", "birdnetlib")
RUN = "b1"


def _ears():
    """Which audio libraries this cell can actually hear with, right now."""
    out = []
    for lib in EARS:
        try:
            __import__(lib)
            out.append(lib)
        except Exception:
            pass
    return sorted(out)


def run_declared(kernel, decl, ctl=None):
    """The DECLARED entry — what a boot calls for `app/config/source/birdclef.json`.

    AUDIO-BINARY LAW: the bundle carries reference URLs only. The observation job fetches each clip
    transiently and keeps nothing but features, so unlike the CMA's mock observers this step needs
    outbound network — and is degradation-first about not having it: a clip that cannot be fetched,
    or an ear that is not installed, records a degraded observation. The corpus and its grounding
    load either way, because what a cell could not hear is a fact about the cell, not a failure of
    the import."""
    import gzip
    import hashlib

    try:
        from app.scripts import _declared_import as di
    except ImportError:
        import _declared_import as di

    ctl = ctl or di.Ctl()
    corpus = di.corpus_dir(decl)
    recs_gz = os.path.join(corpus, "records.jsonl.gz") if corpus else ""
    if not recs_gz or not os.path.exists(recs_gz):
        return {"status": "skipped", "sentinel": False,
                "detail": "corpus bundle absent (%s) — dev side: --emit-bundle once, then commit"
                          % (recs_gz or decl.get("corpus"))}

    d = di.dispatcher(kernel)

    ears = _ears()
    sig = "obs=%s|ears=%s" % (hashlib.sha1(OBSERVERS.encode()).hexdigest()[:8], ",".join(ears))
    heard = ",".join(ears) or "floor-only"
    state, digest = di.decide(kernel, decl)
    marker = di.marker(kernel, decl)

    def _observed():
        sp = (d("vlab.spaces", {"run": RUN}) or {}).get("spaces")
        return sum((s or {}).get("works", 0) for s in sp) if isinstance(sp, list) else 0

    reobserve = False
    if state == "skip":
        seen = _observed()
        if marker.get("ears") == sig and seen > 0:
            return {"status": "skipped", "sentinel": True, "observations": seen,
                    "detail": "already prepared · %d audio observations · run %s" % (seen, RUN)}
        reobserve = True
        ctl.say("corpus unchanged but run %s has %d observations (ears=%s) — re-observing"
                % (RUN, seen, heard))

    acquired = None
    if not reobserve:
        try:
            with open(os.path.join(corpus, "manifest.json"), "r", encoding="utf-8") as fh:
                man = json.load(fh)
        except (OSError, ValueError):
            man = {}
        # The selection is already frozen in the bundle, and `run` takes the slice as a list rather
        # than a stream: a focused corpus is a hundred clips, not a hundred thousand rows.
        recs = []
        with gzip.open(recs_gz, "rt", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    recs.append(json.loads(line))
        ctl.say("loading the BirdCLEF audio corpus (references) + registering source/pool")
        out = run(d, recs, {"freeze": True, "species": man.get("species") or []}, log=ctl.say) or {}
        if out.get("status") == "skipped":
            # the pool is already frozen with this corpus (the first boot pass after every deploy): nothing to
            # acquire, so go on to the observation, which is delta-only. It is NOT "no data".
            acquired = None
        elif not out.get("acquired"):
            return {"status": "no_data", "sentinel": False, "detail": "0 clips"}
        else:
            acquired = out.get("acquired")

    if reobserve:
        try:
            from lib.akasha.api import concept_class
            concept_class(kernel, "vlab")(kernel.manager.get_session("admin")).reset_run(RUN)
        except Exception as exc:
            ctl.say("reset_run failed (%s) — the delta gate will still skip observed pairs" % exc)

    ok, detail = _observe(kernel, decl, ctl, di, heard)
    if not ok:
        return {"status": "failed", "sentinel": False, "detail": detail}

    di.record_hash(kernel, decl, digest, {"ears": sig, "run": RUN, "acquired": acquired})
    return {"status": "complete", "sentinel": True, "pool": decl.get("pool"), "acquired": acquired,
            "detail": "%s · run %s · ears=%s"
                      % (("%s clips" % acquired) if acquired is not None else "re-observed", RUN, heard)}


def _observe(kernel, decl, ctl, di, heard):
    """One MAINTENANCE job for the whole listening pass — resumable, delta-only, and waited on so a
    killed compute is retried rather than recorded as finished."""
    from lib.akasha.api.jobs import CLASS_MAINTENANCE, Job as JCLJob, Step as JCLStep

    if not kernel.harmonia:
        return False, "Harmonia unavailable — no compute was queued"
    steps = [JCLStep(method="vlab.run.new",
                     params={"pool": decl.get("pool"), "run": RUN, "observers": OBSERVERS}),
             JCLStep(method="vlab.run.execute", params={"run": RUN})]
    for sp in SPACES:
        steps.append(JCLStep(method="vlab.pca", params={"run": RUN, "space": sp, "dims": "3"}))
        steps.append(JCLStep(method="vlab.cluster", params={"run": RUN, "space": sp, "k": "4"}))
    steps.append(JCLStep(method="vlab.run.seal", params={"run": RUN}))
    ctl.say("queuing the audio observation + projection compute (Harmonia, MAINTENANCE, ears=%s)" % heard)
    job = kernel.harmonia.submit_job(
        JCLJob(owner="admin", label="vlab.birdclef.compute:%s" % RUN, steps=steps, fail_fast=False),
        job_class=CLASS_MAINTENANCE)
    if job is None:
        return False, "compute job not admitted"
    return di.await_job(kernel, job, ctl, "BirdCLEF observation compute")


def main():
    ap = argparse.ArgumentParser(description="Import a focused BirdCLEF slice into the Source Data Layer (audio by reference).")
    ap.add_argument("--as", dest="as_id", default="admin", help="THIS cell's genesis admin id")
    ap.add_argument("--base", default=None, help="daemon data dir (default AKASHA_DATA_DIR or ./data)")
    ap.add_argument("--csv", dest="csvfile", required=True, help="BirdCLEF train.csv")
    ap.add_argument("--species", default="", help="comma primary_label codes to concentrate on (else auto)")
    ap.add_argument("--n", type=int, default=100, help="how many clips to import (default 100)")
    ap.add_argument("--audio-base", default="", help="a mirror base URL; each clip = base/<filename> (else xeno-canto id)")
    ap.add_argument("--url-col", default="", help="a CSV column already holding a per-row audio URL")
    ap.add_argument("--no-freeze", dest="freeze", action="store_false", default=True, help="leave the pool OPEN")
    ap.add_argument("--emit-bundle", default="", metavar="DIR",
                    help="DEV-SIDE: write records.jsonl.gz + manifest.json for the boot auto-bootstrap "
                         "(e.g. app/assets/birdclef_corpus), then exit — no daemon needed")
    ap.add_argument("--rpc-timeout", type=float, default=300.0)
    args = ap.parse_args()

    rows = _load_csv(args.csvfile)
    recs, chosen, per_type = select_records(rows, n=args.n, species=args.species,
                                            audio_base=args.audio_base, url_col=args.url_col)
    if not recs:
        print("[!] nothing selected — check --csv / --species", file=sys.stderr); sys.exit(3)
    no_url = sum(1 for r in recs if not r["url"])
    print("  selected %d clips · species %s · types %s%s"
          % (len(recs), ",".join(chosen), per_type, ("  (%d without a URL)" % no_url) if no_url else ""))

    # DEV-SIDE bundle emit — the whole point of "本来は自動": generate the asset the seed bundles, so
    # every deploy auto-loads this corpus + observes it at boot. No daemon, no operator step on target.
    if args.emit_bundle:
        recs_gz, man = emit_bundle(recs, chosen, per_type, args.emit_bundle)
        print("  → wrote %s (%d records) + manifest.json" % (recs_gz, man["count"]))
        print("  Commit app/assets/birdclef_corpus/, set the tier's birdclef_bootstrap flag, rebuild seeds.\n")
        return

    from lib.akasha.api import client
    base = args.base or os.environ.get("AKASHA_DATA_DIR") or os.path.join(ROOT, "data")
    if not client.ping(base):
        print("[!] No Cell daemon at %s. Start one: python akasha.py --serve" % base, file=sys.stderr); sys.exit(2)
    gw = client.connect(base, timeout=args.rpc_timeout)

    def d(method, data):
        r = gw.dispatch({"jsonrpc": "2.0", "method": method,
                         "params": {"session_token": args.as_id, "data": data}, "id": "b"}, "local")
        return r["result"] if isinstance(r, dict) and "result" in r else \
            {"__error__": (r or {}).get("error") if isinstance(r, dict) else r}

    try:
        out = run(d, recs, {"freeze": args.freeze, "species": chosen})
    except Exception as exc:
        print("[!] import failed: %s" % exc, file=sys.stderr); gw.close(); sys.exit(4)
    print("  done → %s" % out)
    print("  Observe:  vlab.run.new pool=%s observers=spectral,mfcc,yamnet,birdnet run=b1  ·  vlab.run.execute run=b1" % POOL)
    print("  Inspect:  source.pool.ls pool=%s  ·  source.modalities pool=%s\n" % (POOL, POOL))
    gw.close()


if __name__ == "__main__":
    main()
