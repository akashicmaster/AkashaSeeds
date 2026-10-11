#!/usr/bin/env python3
"""
cma_visual_curation_import.py — load the VCL Phase-1 CMA corpus (produced OFF-LINE by
app/scripts/cma_visual_curation_fetch.py) into a running Cell. Mirrors app/scripts/mobility_source_import.py:
STREAMING (one artwork at a time — never the whole corpus in RAM), every record becomes ONE artwork
Source Atom via `vlab.source.add` (image_ref remote — the binary is never stored), and the pool's
deterministic provenance (seed, selection rule, snapshot date, object ids) is recorded so the frozen
corpus is fully attributable and reproducible. Downstream (`vlab.run.*`, observe, compare, derive,
cluster, project, matrix) is identical for this public pool and a private local one.

Usage (against a running Cell):
    python akasha.py --serve
    python app/scripts/cma_visual_curation_import.py --as <admin_id> \
        --records cma_vcl/records.jsonl --manifest cma_vcl/manifest.json
"""
import argparse
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
POOL = "source:pool:cma:visual_curation:v1"

# CMA record field → Source Atom meta field (verbatim; the museum is the authority).
FIELD_MAP = {
    "accession_number": "accession_number", "creators": "creator", "creation_date": "creation_date",
    "culture": "culture", "type": "type", "department": "department", "technique": "technique",
    "measurements": "dimensions", "rights": "rights", "open_access_status": "open_access_status",
    "canonical_url": "canonical_url",
}


def run(dispatch, records, manifest, log=print):
    """Stream records → one `vlab.source.add` per artwork, then record pool provenance. `records` may
    be a list OR a lazy iterator (the corpus is never fully materialized here)."""
    pool_id = (manifest or {}).get("pool_id") or POOL
    # Provenance: a frozen, deterministic sampling frame (the manifest IS the reproducibility record).
    prov = {"name": "cma:visual_curation", "source": "source:src:cma_visual_curation", "version": "v1",
            "doi": "", "dataset_version": manifest.get("snapshot_date", ""),
            "rule": "VCL Phase-1 100-work heterogeneous stress corpus — deterministic per-family "
                    "selection, seed=%s (independent of any model result); %s"
                    % (manifest.get("corpus_seed"), manifest.get("selection_rule", "")),
            "retrieval": manifest.get("api", "")}
    # Register the source + pool FIRST, so the pool carries its source provenance from the start (vlab's
    # per-artwork safety net then sees the pool exists and does not create a bare one). This makes
    # `source.inspect` list the pool under its source.
    dispatch("source.register", {"provider": "Cleveland Museum of Art (Open Access)",
                                 "collection": "CMA Open Access — CC0 artworks",
                                 "name": "cma_visual_curation", "uri": manifest.get("api", ""),
                                 "rights": "CC0 (per-record share_license_status)"})
    fr = dispatch("source.pool.create", {"name": "cma:visual_curation", "version": "v1",
                                         "source": "source:src:cma_visual_curation", "rule": prov["rule"],
                                         "dataset_version": prov["dataset_version"]})
    added = failed = 0
    for rec in records:
        oid = str(rec.get("id") or rec.get("provider_object_id") or "")
        img = rec.get("image_url") or (rec.get("image_reference") or {}).get("locator")
        if not oid or not img:
            failed += 1
            continue
        fields = {dst: rec.get(src) for src, dst in FIELD_MAP.items() if rec.get(src) is not None}
        r = dispatch("vlab.source.add", {"pool": pool_id, "object_id": oid, "image": img,
                                         "scheme": "remote", "provider": "cma",
                                         "title": rec.get("title") or oid, **fields})
        if isinstance(r, dict) and "__error__" in r:
            log("  [!] add %s failed: %s" % (oid, r["__error__"]))
            failed += 1
        else:
            added += 1
        if added and added % 25 == 0:
            log("      added %d artworks…" % added)
    # FREEZE the frame so the Source Viewer's by-status tally is populated (precomputed at freeze,
    # re-fetched on read — never a live sweep). The artworks are already filed as source items by
    # vlab.source.add, so freeze counts them.
    dispatch("source.pool.freeze", {"pool": pool_id})
    # Declare the Visual Curation lab a CORPUS laboratory that samples_from the frozen pool, so the
    # Source Viewer shows it evidence-GROUNDED (mirrors mobility_source_import / blvh_source_retrofit).
    decl = dispatch("source.lab.declare", {"lab": "visual_curation", "klass": "CORPUS", "pool": pool_id,
                                           "primary_source": "source:src:cma_visual_curation",
                                           "fixture_policy": "no synthetic artworks; CC0 open-access records only"})
    log("  visual_curation declared CORPUS → evidence_status=%s" % (decl or {}).get("evidence_status"))
    log("  imported %d artworks (%d failed) into %s" % (added, failed, pool_id))
    log("  provenance pool: %s  (seed=%s, %d object ids)" % (
        (fr or {}).get("pool") or pool_id, manifest.get("corpus_seed"),
        len(manifest.get("object_ids") or [])))
    return {"pool": pool_id, "added": added, "failed": failed}


def _rows(path):
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


# The observers this corpus is looked at with, and the feature spaces its Analysis panel draws. Both
# are CORPUS decisions, not boot decisions — adding an observer here is what makes a new machine
# viewpoint appear, and the roster's signature is folded into the marker so adding one re-observes
# the delta with no operator step. Degradation-first: an observer whose library is absent records a
# failure and leaves its space empty; it never takes the others down.
OBSERVERS = ("color,geometry,texture,opencv,litert,mobilenet,efficientnet,tf,"
             "litert_detect,cascade,cvdnn_face,yolov8,yolov10")
SPACES = ("color", "geometry", "texture", "opencv", "litert", "objdet", "cascade", "face",
          "mobilenet", "efficientnet", "lightweight")
RUN = "r1"


def _vision_mode():
    """`real` when this cell can actually detect, `mock` when it can only pretend to.

    Recorded alongside the corpus hash, so installing the weights LATER flips the signature and the
    corpus is re-observed on the next boot — the upgrade is something the cell notices, not
    something an operator has to remember."""
    try:
        import ultralytics  # noqa: F401
        return "real"
    except Exception:
        return "mock"


def run_declared(kernel, decl, ctl=None):
    """The DECLARED entry — what a boot calls for `app/config/source/cma_visual_curation.json`.

    Two things happen here and they fail differently, which is why they are sequenced rather than
    merged: the corpus LOADS (offline — the bundle carries references, and the binary is never
    stored), and it is then OBSERVED by a single Harmonia job at MAINTENANCE priority. The compute
    is the expensive half, so it is a job that yields to every interactive write at a step boundary
    rather than a run of inline dispatches on a boot thread, and the corpus is marked done only once
    that job reaches DONE — an interrupted compute must be retried, not recorded as finished."""
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
                "detail": "corpus bundle absent (%s) — dev side: run the fetch once and commit it"
                          % (recs_gz or decl.get("corpus"))}

    d = di.dispatcher(kernel)
    vision = _vision_mode()
    sig = "%s|obs=%s" % (vision, hashlib.sha1(OBSERVERS.encode()).hexdigest()[:8])
    state, digest = di.decide(kernel, decl)
    marker = di.marker(kernel, decl)

    def _observed():
        sp = (d("vlab.spaces", {"run": RUN}) or {}).get("spaces")
        return sum((s or {}).get("works", 0) for s in sp) if isinstance(sp, list) else 0

    reobserve = False
    if state == "skip":
        seen = _observed()
        if marker.get("vision") == sig and seen > 0:
            return {"status": "skipped", "sentinel": True,
                    "detail": "already prepared · %d machine observations · run %s" % (seen, RUN),
                    "observations": seen}
        # Either the cell can see differently now, or a previous run recorded itself done having
        # produced nothing (its libraries arrived afterwards). Both are re-observed; neither is a
        # re-import, because the corpus itself has not changed.
        reobserve = True
        ctl.say("corpus unchanged but run %s has %d observations (vision=%s) — re-observing"
                % (RUN, seen, vision))

    added = None
    if not reobserve:
        try:
            with open(os.path.join(corpus, "manifest.json"), "r", encoding="utf-8") as fh:
                man = json.load(fh)
        except (OSError, ValueError):
            man = {}

        def _rows_gz():
            with gzip.open(recs_gz, "rt", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        yield json.loads(line)

        ctl.say("loading the CMA corpus offline (bundle) + registering source/pool")
        out = run(d, _rows_gz(), man, log=ctl.say) or {}
        if not out.get("added"):
            return {"status": "no_data", "sentinel": False, "detail": "0 artworks"}
        added = out.get("added")

    if reobserve:
        # Drop the run's old observations so the content-addressed results are actually REPLACED —
        # otherwise an upgrade to a real detector would leave the mock's answers standing.
        try:
            from lib.akasha.api import concept_class
            concept_class(kernel, "vlab")(kernel.manager.get_session("admin")).reset_run(RUN)
        except Exception as exc:
            ctl.say("reset_run failed (%s) — the delta gate will still skip observed pairs" % exc)

    ok, detail = _observe(kernel, decl, ctl, di)
    if not ok:
        return {"status": "failed", "sentinel": False, "detail": detail}

    di.record_hash(kernel, decl, digest,
                   {"vision": sig, "run": RUN, "added": added})
    return {"status": "complete", "sentinel": True, "pool": decl.get("pool"), "vision": vision,
            "added": added,
            "detail": "%s · run %s · vision=%s"
                      % (("%s artworks" % added) if added is not None else "re-observed", RUN, vision)}


def _observe(kernel, decl, ctl, di):
    """Queue this corpus's observation + projection work as ONE job and wait for it.

    Every step is idempotent and resumable: `vlab.run.execute` skips a (source, observer) pair it has
    already observed, and the projections are content-addressed writes. So a corpus that grows only
    observes the new works, an ear or an eye installed later fills in only its own space, and a
    killed compute resumes where it stopped instead of starting over."""
    from lib.akasha.api.jobs import CLASS_MAINTENANCE, Job as JCLJob, Step as JCLStep

    if not kernel.harmonia:
        return False, "Harmonia unavailable — no compute was queued"
    steps = [JCLStep(method="vlab.run.new",
                     params={"pool": decl.get("pool"), "run": RUN, "observers": OBSERVERS}),
             JCLStep(method="vlab.run.execute", params={"run": RUN}),
             JCLStep(method="vlab.combine", params={"run": RUN})]
    for sp in SPACES:
        steps.append(JCLStep(method="vlab.pca", params={"run": RUN, "space": sp, "dims": "3"}))
        steps.append(JCLStep(method="vlab.cluster", params={"run": RUN, "space": sp, "k": "4"}))
    steps.append(JCLStep(method="vlab.set.derive", params={"run": RUN}))
    steps.append(JCLStep(method="vlab.run.seal", params={"run": RUN}))
    ctl.say("queuing the machine-observation + projection compute (Harmonia, MAINTENANCE)")
    job = kernel.harmonia.submit_job(
        JCLJob(owner="admin", label="vlab.cma.compute:%s" % RUN, steps=steps, fail_fast=False),
        job_class=CLASS_MAINTENANCE)
    if job is None:
        return False, "compute job not admitted"
    return di.await_job(kernel, job, ctl, "CMA observation compute")


def main():
    ap = argparse.ArgumentParser(description="Import the CMA VCL Phase-1 corpus into a running Cell.")
    ap.add_argument("--as", dest="as_id", default="admin", help="this cell's genesis admin id")
    ap.add_argument("--records", required=True, help="records.jsonl from cma_visual_curation_fetch.py")
    ap.add_argument("--manifest", required=True, help="manifest.json from the fetch step")
    ap.add_argument("--base", default=None, help="daemon data dir (default AKASHA_DATA_DIR or ./data)")
    args = ap.parse_args()
    sys.path.insert(0, ROOT)
    from lib.akasha.api import client

    base = args.base or os.environ.get("AKASHA_DATA_DIR") or os.path.join(ROOT, "data")
    gw = client.connect(base)

    def dispatch(method, data):
        r = gw.dispatch({"jsonrpc": "2.0", "method": method,
                         "params": {"session_token": args.as_id, "data": data}, "id": "m"}, "local")
        return (r.get("result") if isinstance(r, dict) and "result" in r
                else {"__error__": (r or {}).get("error") if isinstance(r, dict) else r})

    manifest = json.load(open(args.manifest, encoding="utf-8"))
    out = run(dispatch, _rows(args.records), manifest)
    print("  done:", out)


if __name__ == "__main__":
    main()
