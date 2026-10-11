"""
The Source Viewer's PREPAID views — the text-analysis and the media-observation precompute — as two PASS ops
that two declared workloads run (`app/config/workbench/workloads/{analysis,media}_precompute.json`, 2026-10-03).

They were boot threads (`svc:analysis-precompute`, `svc:media-precompute`) that polled for 30 minutes after every
boot, dispatching as admin. Now each is ONE bounded pass over `set:source:pool:frozen`, run by the driver
(serve-first and ontology-loaded gating are the driver's, the cadence is the declaration's `trigger`, each pass
records its own outcome) and run AS THE WORKLOAD'S CLIENT: every per-pool call goes through the gate, so the
client's `consumer` line on each pool (read · run) is what lets it see the pool, and its own public bench is
the place its writes are asked about. Nothing here dispatches as admin.

  analysis.precompute.pass bench=<own bench>   one pass of the text analysis over every frozen pool
  vlab.media.pass          bench=<own bench>   one pass of the image/audio observation over every media pool

Both are IDEMPOTENT and self-healing (a prepared pool submits nothing; a pool whose job is still in flight is
skipped), which is what makes a repeating trigger converge instead of piling up.
"""
import os
import re
import sys
import time
import json
import uuid
import logging
import hashlib
import functools
from typing import Dict, Any, Optional, List, Callable
try:
    from lib.akasha.api.jobs import Worker as JCLWorker, Job as JCLJob, Step as JCLStep
    from lib.akasha.api.jobs import CLASS_BATCH_ATOM, CLASS_LINK, CLASS_MAINTENANCE
except ImportError:
    JCLWorker = None  # type: ignore
    JCLJob    = None  # type: ignore
    JCLStep   = None  # type: ignore
    CLASS_BATCH_ATOM = "batch_atom"  # type: ignore
    CLASS_LINK       = "link"        # type: ignore
    CLASS_MAINTENANCE = "maintenance"  # type: ignore
from lib.akasha.api.trust import (TRUST_NETWORK, TRUST_LOCAL, TRUST_INTERNAL,
                                  TRUSTED_TRANSPORTS as _TRUSTED_TRANSPORTS)
from lib.akasha.api.rpc import ok as _ok, err as _err
import lib.akasha.api as _api

logger = logging.getLogger("Akasha.Kernel")


def _declared_pools(kernel) -> set:
    """The pools DECLARED corpora own — the ones whose own importer keeps them indexed."""
    try:
        from lib.akasha.api import source as _srcboot
        return {str(d.get("pool") or "") for d in _srcboot.source_declarations(kernel) if d.get("pool")}
    except Exception:
        return set()


# ── helpers ─────────────────────────────────────────────────────────────────────────────────────────
def _as_caller(kernel, session):
    """A dispatcher that speaks as the CALLER — the workload's own client — never as admin. Each call is
    asked of the gate under that identity (TRUST_INTERNAL only lets the kernel assert the bare client id; it
    adds no authority). Returns the result dict, or {"__error__": …}."""
    cid = session.client_id

    def _d(method, data):
        r = kernel.dispatch({"jsonrpc": "2.0", "method": method,
                             "params": {"session_token": cid, "data": data}, "id": "precompute"},
                            TRUST_INTERNAL)
        return (r.get("result") if isinstance(r, dict) and "result" in r
                else {"__error__": (r or {}).get("error") if isinstance(r, dict) else r})
    return _d


def _frozen_pools(kernel) -> list:
    """The pools the source engine has frozen — `set:source:pool:frozen`, its one writer (a fact the engine
    states at freeze) — as pool ids. `radu` owns its own atoms and is excluded."""
    from lib.akasha.api import source as _srcboot
    return [p for p in (_srcboot.frozen_pools(kernel) or []) if p and "radu" not in str(p).lower()]


def _inflight_labels(kernel, prefix: str) -> set:
    """Pools with a non-terminal JCL job of this label family — a repeating pass must not stack a second
    job on a pool whose first is still running."""
    out = set()
    try:
        for j in (kernel.jcl_worker.list_jobs() if kernel.jcl_worker else []):
            lbl = getattr(j, "label", "") or ""
            if lbl.startswith(prefix) and getattr(j, "status", "") not in ("DONE", "FAILED", "CANCELLED"):
                out.add(lbl[len(prefix):])
    except Exception:
        pass
    return out


def handle_analysis_precompute_pass(kernel, rid, data, session) -> dict:
    """[analysis.precompute.pass bench=] ONE bounded pass of the text-analysis precompute over every frozen
    pool, as the caller. Per pool: read its status (frozen? — a read the client's `consumer` line admits), find
    the Labo that holds it REGISTERED FIRST (`labo.of`; the workbench provisions a shadow labo only for pools no
    lab holds), and ask `analysis.precompute` for the projections still missing. Returns per-pool counts."""
    if not (kernel.harmonia and kernel.jcl_worker and JCLJob and JCLStep):
        return _err(rid, -32002, "JCL worker not available")
    bench = str((data or {}).get("bench") or "").strip()
    if not bench:
        return _err(rid, -32602, "analysis.precompute.pass requires bench= (the workload's own bench)")
    d = _as_caller(kernel, session)
    busy = _inflight_labels(kernel, "analysis.precompute:")
    pools = ready = queued = waiting = skipped = 0
    per = {}
    for pool in _frozen_pools(kernel):
        st = d("source.status", {"pool": pool})
        if not isinstance(st, dict) or "__error__" in st or not st.get("frozen"):
            skipped += 1; per[pool] = "not frozen / not readable"
            continue
        pools += 1
        held = (d("labo.of", {"pool": pool}) or {}).get("labos") or []
        if not held:
            waiting += 1; per[pool] = "no labo yet (provisioning makes the shadow at freeze)"
            continue
        if pool in busy:
            queued += 1; per[pool] = "job in flight"
            continue
        labo = str(held[0].get("labo") or "")
        r = d("analysis.precompute", {"labo": labo, "input": pool, "bench": bench})
        if isinstance(r, dict) and "__error__" in r:
            skipped += 1; per[pool] = "refused: %s" % str((r["__error__"] or {}).get("message", ""))[:80]
        elif isinstance(r, dict) and r.get("submitted"):
            queued += 1; per[pool] = "queued"
        else:
            ready += 1; per[pool] = "prepared" if not r.get("skipped") else "n/a (%s)" % r.get("skipped")
    logger.info("[analysis.precompute.pass] caller=%s bench=%s pools=%d queued=%d ready=%d waiting=%d skipped=%d",
                session.client_id, bench, pools, queued, ready, waiting, skipped)
    return _ok(rid, {"pools": pools, "queued": queued, "ready": ready, "waiting": waiting,
                     "skipped": skipped, "per_pool": per, "bench": bench})


# modality → (observer roster, the spaces to project)
_IMAGE_OBS = "color,geometry,texture,litert,mobilenet,efficientnet"
_IMAGE_SPACES = ("color", "geometry", "texture", "litert", "mobilenet", "efficientnet", "lightweight")
_AUDIO_OBS = "spectral,mfcc,chroma,rhythm,yamnet,panns,birdnet"
_AUDIO_SPACES = ("spectral", "mfcc", "chroma", "rhythm", "yamnet", "panns", "birdnet")


def handle_vlab_media_pass(kernel, rid, data, session) -> dict:
    """[vlab.media.pass bench=] ONE bounded pass of the media observation+analysis precompute over every
    frozen pool that carries IMAGE or AUDIO and has no observed vlab run yet — as the caller. Per such pool it
    submits ONE MAINTENANCE job owned by the caller: run.new → run.execute → (combine) → per-space pca/cluster
    → seal, each step carrying `on_bench=<bench>` so the gate asks about the workload's own bench. A pool a
    declared corpus owns is skipped (its own importer indexes it), text-only pools belong to the analysis pass,
    radu is excluded. D2-M §3: the run is minted purpose=precompute (bench="" — naming the place the call is
    made on does not rename the run), and only the roster's READY observers run (a mock never pollutes it)."""
    if not (kernel.harmonia and kernel.jcl_worker and JCLJob and JCLStep):
        return _err(rid, -32002, "JCL worker not available")
    bench = str((data or {}).get("bench") or "").strip()
    if not bench:
        return _err(rid, -32602, "vlab.media.pass requires bench= (the workload's own bench)")
    d = _as_caller(kernel, session)
    busy = _inflight_labels(kernel, "vlab.media.compute:")
    declared = _declared_pools(kernel)
    seen = queued = ready = skipped = 0
    per = {}

    def _has_media_run(pool):
        runs = (d("vlab.runs", {"pool": pool}) or {}).get("runs") or []
        if not runs:
            return (False, False)
        works = 0
        for rr in runs:
            sp = (d("vlab.spaces", {"run": rr.get("run")}) or {}).get("spaces") or []
            works += sum((s or {}).get("works", 0) for s in sp if isinstance(s, dict))
        return (True, works > 0)

    for pool in _frozen_pools(kernel):
        if pool in declared:
            continue
        mods = (d("source.modalities", {"pool": pool}) or {}).get("modalities") or {}
        if not (mods.get("image") or mods.get("audio")):
            continue                                     # text-only → the analysis pass owns it
        seen += 1
        run = "auto_" + re.sub(r"[^a-z0-9]+", "_", str(pool).replace("source:pool:", "").lower()).strip("_")
        if run in busy:
            queued += 1; per[pool] = "job in flight"
            continue
        run_exists, observed = _has_media_run(pool)
        if run_exists and observed:
            ready += 1; per[pool] = "prepared"
            continue
        modality = "audio" if mods.get("audio") else "image"
        observers = _AUDIO_OBS if modality == "audio" else _IMAGE_OBS
        spaces = _AUDIO_SPACES if modality == "audio" else _IMAGE_SPACES
        mocks_skipped = []
        if modality == "image":
            rr_ = (d("vlab.roster", {}) or {}).get("observers") or []
            ok_ = {r.get("observer") for r in rr_ if r.get("status") == "ok"}
            want = [o for o in observers.split(",") if o.strip()]
            keep = [o for o in want if o in ok_]
            mocks_skipped = [o for o in want if o not in ok_]
            if keep:
                observers = ",".join(keep)
                spaces = tuple(s for s in spaces if s in keep or s == "lightweight")
        if run_exists and not observed:                  # a prior empty/degraded run → re-observe
            try:
                _api.concept_class(kernel, "vlab")(session).reset_run(run)
            except Exception:
                pass
        ob = {"on_bench": bench}
        steps = [JCLStep(method="vlab.run.new", params=dict(ob, pool=pool, run=run, observers=observers,
                                                              purpose="precompute")),
                 JCLStep(method="vlab.run.execute", params=dict(ob, run=run))]
        if modality == "image":
            steps.append(JCLStep(method="vlab.combine", params=dict(ob, run=run)))
        for sp in spaces:
            steps.append(JCLStep(method="vlab.pca", params=dict(ob, run=run, space=sp, dims="3")))
            steps.append(JCLStep(method="vlab.cluster", params=dict(ob, run=run, space=sp, k="4")))
        steps.append(JCLStep(method="vlab.run.seal", params=dict(ob, run=run)))
        logger.info("[vlab] precompute run=%s observers=%s mocks_skipped=%s", run, observers,
                    ",".join(mocks_skipped) or "-")
        job = kernel.harmonia.submit_job(JCLJob(owner=session.client_id, label="vlab.media.compute:%s" % run,
                                                steps=steps, fail_fast=False), job_class=CLASS_MAINTENANCE)
        if job is not None:
            queued += 1; per[pool] = "queued %s (%s)" % (run, modality)
        else:
            skipped += 1; per[pool] = "not admitted"
    logger.info("[vlab.media.pass] caller=%s bench=%s media_pools=%d queued=%d ready=%d skipped=%d",
                session.client_id, bench, seen, queued, ready, skipped)
    return _ok(rid, {"media_pools": seen, "queued": queued, "ready": ready, "skipped": skipped,
                     "per_pool": per, "bench": bench})
