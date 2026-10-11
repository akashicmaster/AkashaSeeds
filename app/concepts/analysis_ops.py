"""
APPLICATION module (group 4, 4.11): the analysis.* ops drives application Concept Models by name, so it moved
here from the platform `source` package, unchanged in behaviour; its manifest entries moved with it
to the concepts manifest. Turning it into declared workloads is the application's next step.

The analysis.* RPC ops — moved out of the kernel (backend layout order 2026-09-20).

Every function takes the kernel (the heart) as its first argument: it is the object the
dispatcher / timer registry hands in, never imported. Bodies are the kernel's own, moved
verbatim except `self.` → `kernel.` and intra-family calls.
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


def handle_analysis_precompute(kernel, rid, data, session) -> dict:
    """[analysis.precompute] Submit a Harmonia BATCH job that computes + PERSISTS a pool's
    statistical projections, so guests later RE-FETCH them via `analysis.view` with ZERO
    real-time Atom sweep. This is the sanctioned cost path (the absolute rule: no full-member
    `get_meta` walk on the interactive/read path): the walk runs in the background JCL worker at
    MAINTENANCE priority — it never delays an operator command or a user write. Without explicit
    `fields=`/`plugins=`, the pool's field names are read (bounded scan) and count+groupby are
    precomputed for each. Needs `run` on the pool (the gate decides; it enqueues a job)."""
    # WHO may run this is the GATE's answer (`access: run` on the op, then the target — the pool), not a
    # role test here: a workload's client holds `run` where its declaration says, and a check inside the
    # handler would refuse it after the gate had admitted it.
    if not (kernel.harmonia and kernel.jcl_worker and JCLJob and JCLStep):
        return _err(rid, -32002, "JCL worker not available")
    labo = (data.get("labo") or "").strip()
    inp = (data.get("input") or data.get("pool") or "").strip()
    if not labo or not inp:
        return _err(rid, -32602, "analysis.precompute requires labo= and input= (pool)")
    fields = data.get("fields")
    if isinstance(fields, str):
        fields = [f.strip() for f in fields.split(",") if f.strip()]
    plugins = data.get("plugins")
    # AUTO mode = no explicit plugins. Only then do we prepare the WHOLE viewer surface for the pool
    # (count + cluster + every scatter pair), so the viewer never asks and no operator step exists.
    # With explicit plugins= the caller gets exactly what they named (unchanged behaviour).
    _auto_mode = not plugins
    if isinstance(plugins, str):
        # Split MULTIPLE plugins on ';' — NOT ',' — because a scatter spec is `scatter:fx,fy`
        # and its internal comma must survive (','-splitting broke it into two bogus plugins).
        plugins = [p.strip() for p in plugins.split(";") if p.strip()]
    if not plugins:
        # ── AUTO path (no explicit plugins) — safety guards, because this runs unattended at boot.
        # GUARD 1: skip MEDIA/IMAGE pools. A statistical distribution over image metadata is
        # meaningless, and walking image-member metas is a MEMORY BOMB — the BL image pool
        # (bl_book_images) drove the daemon to ~4 GB RSS and got OOM-killed on every boot. Detect
        # by field schema (a bounded scan, never a member sweep).
        _MEDIA_MARKERS = {"media_type", "image_type", "dataset_id", "locator", "source_filename",
                          "iiif", "iiif_manifest", "manifest", "thumbnail", "image_url", "image",
                          "mime", "width", "height", "row_index", "record_id",
                          # media/reference locators (near-unique, never a category)
                          "url", "audio_url", "audio", "filename", "fname", "content_type", "format"}
        _status = kernel.dispatch({"jsonrpc": "2.0", "method": "source.status",
                                 "params": {"session_token": session.client_id, "data": {"pool": inp}},
                                 "id": "aps"}, TRUST_INTERNAL)
        _total = (((_status or {}).get("result") or {}).get("total")
                  if isinstance(_status, dict) else None) or 0
        # GUARD 2: skip pools too large to walk safely (member get_meta walk is O(N) memory-touch).
        try:
            _mmax = max(0, int(os.environ.get("AKASHA_PRECOMPUTE_MAX_MEMBERS", "60000")))
        except (TypeError, ValueError):
            _mmax = 60000
        if _mmax and _total > _mmax:
            return _ok(rid, {"submitted": 0, "job_id": None, "skipped": "too_large",
                             "total": _total, "note": "pool exceeds AKASHA_PRECOMPUTE_MAX_MEMBERS "
                             "— auto precompute skipped (walk too heavy); precompute explicitly if needed"})
        if not fields:
            scan = kernel.dispatch({"jsonrpc": "2.0", "method": "source.pool.scan",
                                  "params": {"session_token": session.client_id, "data": {"pool": inp}},
                                  "id": "ap"}, TRUST_INTERNAL)
            fields = (((scan or {}).get("result") or {}).get("fields", [])
                      if isinstance(scan, dict) else []) or []
        # A media pool is NOT skipped wholesale — that wrongly killed text analysis on image/audio
        # datasets that ALSO carry meaningful categorical fields (e.g. the museum corpus's
        # department / culture / technique / type). The POLICY (source-viewer rule) is: exclude only
        # categorically-meaningless columns and ALWAYS compute anything with categorical meaning. So
        # the media-technical markers are dropped from the count list below (alongside the id/date/
        # serial names), never the whole pool; the member-count guard above already bounds the walk.
        # Field cap = a SAFETY ceiling on how many coded fields are prepared, kept in step with the
        # scatter pair cap (analysis._max_pairs ≥ C(_fcap,2)) so EVERY pair of prepared fields is
        # prepared — the viewer offers only prepared category fields, so a chart appears at once,
        # never "Computing". 80 sits well above any real survey schema (mobility ≈ 46); the actual
        # filtering is by MEANING, not this count — see below.
        try:
            _fcap = max(1, int(os.environ.get("AKASHA_PRECOMPUTE_MAX_FIELDS", "80")))
        except (TypeError, ValueError):
            _fcap = 80
        # POLICY (the source-viewer rule): exclude only categorically-MEANINGLESS fields — dates,
        # serial/sequence numbers, unique ids, free text — and ALWAYS compute anything with
        # categorical meaning. Two filters: (1) a cheap NAME filter here drops the obvious meaningless
        # columns (so the accumulator never even allocates a bucket for a per-row id); (2) the robust
        # CARDINALITY filter in analysis.precompute_counts drops any field whose value set is too
        # large / near-unique to be a category (a date/serial the name filter missed). A field that
        # passes both — a small, repeating value set — is a category and is prepared, however many
        # meaningful fields the pool has.
        # Only UNAMBIGUOUSLY meaningless tokens here (the cardinality filter downstream is the robust
        # net for anything the name misses, so this stays conservative — it must never drop a field
        # that could carry categorical meaning).
        def _meaningless_name(f):
            s = str(f).lower()
            if s in {"id", "uuid", "guid", "record_id", "respondent_id", "source_record_id",
                     "row_id", "rowid", "index", "idx", "seq", "sequence", "serial", "rownum",
                     "row_number", "date", "datetime", "timestamp", "created_at", "updated_at",
                     "modified_at"}:
                return True
            return (s.endswith("_id") or s.endswith("_uuid") or s.endswith("_date")
                    or s.endswith("_timestamp") or s.endswith("_seq") or s.endswith("_serial")
                    or s.endswith("_index"))
        fields = [f for f in fields
                  if not _meaningless_name(f) and str(f).lower() not in _MEDIA_MARKERS]
        fields = list(fields)[:_fcap]
        # DEFAULT = count (distribution) ONLY — write-light (one run atom per field). groupby is
        # NOT auto-expanded: it materializes a result Set PER VALUE, which on a high-cardinality
        # field is a WriteQueue flood. Request groupby explicitly via plugins= when wanted (it is
        # Set-capped regardless). This keeps the automatic boot-time precompute cheap and safe.
        plugins = ["count:%s" % f for f in fields]
    if not plugins:
        return _ok(rid, {"submitted": 0, "job_id": None,
                         "note": "no fields to precompute (pass fields= or plugins=)"})
    AnalysisConcept = _api.concept_class(kernel, "analysis")
    _ac = AnalysisConcept(session)
    # ── LARGE-pool chunking parameters (shared by both paths) ───────────────────────────────
    _st = kernel.dispatch({"jsonrpc": "2.0", "method": "source.status",
                         "params": {"session_token": session.client_id, "data": {"pool": inp}},
                         "id": "apc"}, TRUST_INTERNAL)
    _total = (((_st or {}).get("result") or {}).get("total") if isinstance(_st, dict) else 0) or 0
    try:
        _chunk = max(200, int(os.environ.get("AKASHA_PRECOMPUTE_CHUNK", "2000")))
    except (TypeError, ValueError):
        _chunk = 2000

    steps = []
    already = 0
    if _auto_mode:
        # The viewer surface = count + cluster (groupby) + every scatter pair, prepared IN ADVANCE.
        # count is the walk; the finalize/precompute_counts op DERIVES cluster from the same tally and
        # builds every scatter from ONE bounded pass (never an O(store) fan-out). So we submit ONE
        # count job over ALL fields whenever a count OR a cluster/scatter is still missing; when only
        # cluster/scatter are missing (counts done on an older boot) the single-step op skips the
        # count walk and just does the cheap bounded scatter pass — self-healing, no operator step.
        _fields = list(fields or [])
        _count_todo = [f for f in _fields
                       if _ac._persisted_projection(labo, inp, "count:%s" % f, "") is None]
        _derived_todo = False
        try:
            _derived_todo = _ac.derived_pending(labo, inp, _fields)
        except Exception:
            _derived_todo = True
        already = (len(_fields) - len(_count_todo))
        if not _count_todo and not _derived_todo:
            return _ok(rid, {"submitted": 0, "job_id": None, "already_persisted": already,
                             "note": "all projections (count + cluster + scatter) already prepared "
                                     "— nothing to do"})
        if _count_todo and _total > _chunk:
            # LARGE pool with counts to walk: CHUNKED (job.stat shows chunk k/K), finalize fans out
            # cluster + scatter. Walk over ALL fields so the accumulator can derive every cluster.
            _n_chunks = (_total + _chunk - 1) // _chunk
            for _i in range(_n_chunks):
                steps.append(JCLStep(method="analysis.count_chunk",
                                     params={"labo": labo, "input": inp, "fields": _fields,
                                             "offset": _i * _chunk, "chunk": _chunk}))
            steps.append(JCLStep(method="analysis.count_finalize",
                                 params={"labo": labo, "input": inp, "fields": _fields}))
        else:
            # Small pool, OR only cluster/scatter left (no count walk needed): one combined step that
            # counts what is missing in a single pass and prepares cluster + scatter.
            steps.append(JCLStep(method="analysis.precompute_counts",
                                 params={"labo": labo, "input": inp, "fields": _fields}))
    else:
        # EXPLICIT plugins= — give the caller exactly what they named. Idempotent: skip persisted.
        _pending = []
        for p in plugins:
            try:
                hit = _ac._persisted_projection(labo, inp, p, "") is not None
            except Exception:
                hit = False
            if hit:
                already += 1
            else:
                _pending.append(p)
        plugins = _pending
        if not plugins:
            return _ok(rid, {"submitted": 0, "job_id": None, "already_persisted": already,
                             "note": "all requested projections already persisted — nothing to do"})
        # count: fields → ONE combined precompute_counts step (never one O(store) walk per field).
        # Other plugins (explicit groupby/scatter) keep their own analysis.run step.
        _count_fields = [p.split(":", 1)[1] for p in plugins if p.startswith("count:")]
        _other = [p for p in plugins if not p.startswith("count:")]
        if _count_fields:
            if _total > _chunk:
                _n_chunks = (_total + _chunk - 1) // _chunk
                for _i in range(_n_chunks):
                    steps.append(JCLStep(method="analysis.count_chunk",
                                         params={"labo": labo, "input": inp, "fields": _count_fields,
                                                 "offset": _i * _chunk, "chunk": _chunk}))
                steps.append(JCLStep(method="analysis.count_finalize",
                                     params={"labo": labo, "input": inp, "fields": _count_fields}))
            else:
                steps.append(JCLStep(method="analysis.precompute_counts",
                                     params={"labo": labo, "input": inp, "fields": _count_fields}))
        steps += [JCLStep(method="analysis.run", params={"labo": labo, "input": inp, "plugin": p})
                  for p in _other]
    if not steps:
        return _ok(rid, {"submitted": 0, "job_id": None, "already_persisted": already,
                         "note": "nothing to precompute"})
    job = JCLJob(owner=session.client_id, label="analysis.precompute:%s" % inp,
                 steps=steps, fail_fast=False)
    # MAINTENANCE class: the full-member walk runs in the background, never ahead of interactive work.
    kernel.harmonia.submit_job(job, job_class=CLASS_MAINTENANCE)
    return _ok(rid, {"job_id": job.job_id, "input": inp, "labo": labo, "plugins": plugins,
                     "submitted": len(steps), "already_persisted": already, "status": job.status,
                     "auto": _auto_mode,
                     "note": "precomputing in the background (MAINTENANCE priority); guests "
                             "re-fetch via analysis.view as each run persists."})


def handle_analysis_diag(kernel, rid, data, session) -> dict:
    """[analysis.diag] ONE readout that answers 'is it a bug, a library-fetch error, or still
    computing?' for every background analysis the source viewer / visual-curation lab depend on —
    so a blank chart is never ambiguous. Read-level (guest-safe: no recipe/pid/paths). Never raises.

    Four evidence lanes, then a verdict per subject:
      • phases    — the boot phases (svc.ls units) with state/detail/elapsed/stale + any step errors
                    a failed compute job left behind (a failed phase now STAYS visible, not closed).
      • jobs      — the analysis.*/vlab.* JCL jobs by status (running / pending / failed + errors).
      • libraries — which optional deps are importable on THIS cell (numpy/Pillow/sklearn/tensorflow/
                    ai_edge_litert/ultralytics) — the 'library-fetch error' signal, esp. for VCL.
      • subjects  — per source pool: frozen? how many category counts + derived views are prepared,
                    and the visual-curation run: how many machine observations exist.
    """
    import time as _t
    out = {"phases": [], "job_summary": {}, "libraries": {}, "subjects": [], "verdict": ""}

    # ── environment — the FIRST thing to check when a lib "was installed before" is now missing.
    # A Python MINOR bump (e.g. 3.11 → 3.14) commonly leaves the heavy ML wheels (tensorflow,
    # scikit-learn, torch/ultralytics) with no binary wheel yet, so --prefer-binary installs fail
    # and every observer that needs them degrades — even though numpy/Pillow (fast to publish) work.
    import platform as _plat
    _pytag = "cp%d%d" % (sys.version_info[0], sys.version_info[1])
    out["environment"] = {
        "python": _plat.python_version(), "wheel_tag": _pytag,
        "implementation": _plat.python_implementation(),
        "executable": sys.executable, "prefix": sys.prefix,
        "autoinstall": (os.environ.get("AKASHA_SKIP_AUTOINSTALL", "").strip().lower()
                        in ("", "0", "no", "false", "off")),
    }

    # ── OTHER Python interpreters on this machine — the "installed under a different Python" case.
    # A daemon that now runs 3.14 cannot see a package installed under 3.11's site-packages, even on
    # the SAME host. find_spec (no import) is fast; we report which interpreters exist and whether
    # each key package resolves THERE, so "it IS installed, just not here" becomes obvious.
    try:
        import shutil as _shutil
        _self_real = os.path.realpath(sys.executable or "")
        _probe = ("import importlib.util as u,sys;"
                  "print(sys.version.split()[0]);"
                  "print('|'.join(n for n in ['tensorflow','sklearn','ultralytics','ai_edge_litert',"
                  "'tflite_runtime','cv2','numpy','PIL'] if u.find_spec(n)))")
        _seen = set()
        others = []
        for _name in ("python3.10", "python3.11", "python3.12", "python3.13", "python3.14",
                      "python3", "python"):
            _p = _shutil.which(_name)
            if not _p:
                continue
            _rp = os.path.realpath(_p)
            if _rp in _seen:
                continue
            _seen.add(_rp)
            _is_self = (_rp == _self_real)
            try:
                import subprocess as _sp2
                _r = _sp2.run([_p, "-c", _probe], capture_output=True, text=True, timeout=15)
                _lines = (_r.stdout or "").strip().splitlines()
                _ver = _lines[0] if _lines else "?"
                _have = (_lines[1].split("|") if len(_lines) > 1 and _lines[1] else [])
                others.append({"name": _name, "path": _rp, "python": _ver,
                               "is_daemon_python": _is_self,
                               "has": sorted(x for x in _have if x)})
            except Exception as _exc:
                others.append({"name": _name, "path": _rp, "error": str(_exc)[:80]})
        out["other_interpreters"] = others
        # if a NON-daemon interpreter has a package the daemon lacks, name it (the smoking gun)
        _daemon_has = {n for o in others if o.get("is_daemon_python") for n in o.get("has", [])}
        _elsewhere = {}
        for o in others:
            if o.get("is_daemon_python"):
                continue
            for n in o.get("has", []):
                if n not in _daemon_has and n in ("tensorflow", "sklearn", "ultralytics", "cv2"):
                    _elsewhere.setdefault(n, []).append("%s (%s)" % (o.get("name"), o.get("python")))
        if _elsewhere:
            out["installed_under_other_python"] = _elsewhere
    except Exception as _exc:
        out["other_interpreters_error"] = str(_exc)

    # ── libraries — the import probe (does NOT install; just reports what is present) ──
    # `optional` marks a lib whose absence does NOT break the lab (sklearn → numpy fallback for
    # PCA/kmeans; ultralytics → mock detectors). Only tensorflow actually costs a feature space
    # (mobilenet/efficientnet embeddings); numpy/Pillow are essential (color/geometry/texture).
    _LIB_ROLE = {"numpy": "essential (color/geometry/texture)", "Pillow": "essential (image decode)",
                 "scikit-learn": "optional (PCA/kmeans fall back to numpy)",
                 "tensorflow": "needed for mobilenet/efficientnet embedding spaces only",
                 "ai-edge-litert": "vision classifier backend (image.profile)",
                 "opencv": "optional (the OpenCV feature space — edges/keypoints/contours; mock if absent)",
                 "ultralytics": "optional (YOLO detectors fall back to mock)",
                 "librosa": "audio MFCC/chroma/rhythm spaces (the spectral space works on numpy alone)",
                 "soundfile": "audio decode floor (used when librosa's own loader is unavailable)",
                 "panns_inference": "the PANNs (CNN14) general-audio ear — heavy (torch); mock if absent",
                 "birdnetlib": "the BirdNET ornithological ear (bird species) — mock if absent"}
    _pip_check = str(data.get("pip_check") or data.get("probe") or "").strip().lower() in ("1", "yes", "true", "on", "install")
    out["libraries"] = {}
    _missing_specs = {"scikit-learn": "scikit-learn", "tensorflow": "tensorflow-cpu",
                      "opencv": "opencv-python-headless", "ultralytics": "ultralytics",
                      "librosa": "librosa", "soundfile": "soundfile",
                      "panns_inference": "panns_inference", "birdnetlib": "birdnetlib"}
    for _imp, _label in (("numpy", "numpy"), ("PIL", "Pillow"), ("sklearn", "scikit-learn"),
                         ("tensorflow", "tensorflow"), ("ai_edge_litert", "ai-edge-litert"),
                         ("cv2", "opencv"), ("ultralytics", "ultralytics"),
                         ("librosa", "librosa"), ("soundfile", "soundfile"),
                         ("panns_inference", "panns_inference"), ("birdnetlib", "birdnetlib")):
        try:
            __import__(_imp); ok = True
        except Exception:
            ok = False
        out["libraries"][_label] = ok
    out["library_roles"] = _LIB_ROLE

    # ── installed VARIANT + version — same import name, different distribution (tensorflow-cpu vs
    # tensorflow vs tf-nightly; opencv-python vs -headless). importlib.metadata shows which is here.
    try:
        import importlib.metadata as _im
        _vers = {}
        for _dist in ("numpy", "Pillow", "scikit-learn", "tensorflow", "tensorflow-cpu",
                      "tf-nightly", "ai-edge-litert", "tflite-runtime", "opencv-python",
                      "opencv-python-headless", "opencv-contrib-python", "ultralytics", "torch"):
            try:
                _vers[_dist] = _im.version(_dist)
            except Exception:
                pass
        out["installed_variants"] = _vers      # only the distributions actually present are listed
    except Exception:
        pass

    # ── CAPABILITY probe (variant-aware) — the code accepts a FAMILY of backends for each job, so a
    # capability is satisfied if ANY variant imports. This is what actually decides whether a feature
    # space lights up, not a single package name.
    def _first_importable(mods):
        import importlib.util as _u
        for m in mods:
            try:
                if _u.find_spec(m) is not None:
                    return m
            except Exception:
                pass
        return None
    _CAP = {
        "vision_classifier (image.profile)": ["ai_edge_litert", "tflite_runtime", "tensorflow"],
        "embeddings (mobilenet/efficientnet)": ["tensorflow"],
        "cv_features (opencv space)": ["cv2"],
        "litert_detect (SSD-MobileNet, lightweight)": ["ai_edge_litert", "tflite_runtime", "tensorflow"],
        "cvdnn_face (opencv YuNet)": ["cv2"],
        "audio_spectral (numpy floor — always)": ["numpy"],
        "audio_mfcc/chroma/rhythm (librosa)": ["librosa"],
        "audio_yamnet (AudioSet, TFLite ear)": ["ai_edge_litert", "tflite_runtime", "tensorflow"],
        "audio_panns (CNN14 general ear)": ["panns_inference"],
        "audio_birdnet (bird species ear)": ["birdnetlib"],
        "pca/cluster": ["sklearn"],
        "detectors (YOLO — heavy, deferred)": ["ultralytics"],
    }
    caps = {}
    for _cap, _fam in _CAP.items():
        _via = _first_importable(_fam)
        # OpenCV Haar cascades were REMOVED in OpenCV 5.0 — a live cv2.CascadeClassifier check, not
        # just an import, decides that capability (cv2 imports but the class is gone on 5.x).
        if _cap.startswith("cvdnn_face"):
            try:
                import cv2 as _cv2test
                _via = "cv2" if hasattr(_cv2test, "FaceDetectorYN") else None
            except Exception:
                _via = None
        caps[_cap] = {"ok": bool(_via), "via": _via, "family": _fam,
                      "fallback": ("numpy" if _cap.startswith("pca") else
                                   None if _cap.startswith(("vision_classifier", "embeddings")) else "mock")}
    try:
        import cv2 as _cv2c
        caps["cascade (opencv Haar — OpenCV<5 only)"] = {
            "ok": hasattr(_cv2c, "CascadeClassifier"), "via": ("cv2" if hasattr(_cv2c, "CascadeClassifier") else None),
            "family": ["cv2.CascadeClassifier"], "fallback": "unavailable on OpenCV 5.x",
            "note": "removed in OpenCV 5.0; runs where OpenCV<5 is installable (e.g. a 3.12 venv)"}
    except Exception:
        caps["cascade (opencv Haar — OpenCV<5 only)"] = {"ok": False, "via": None,
            "family": ["cv2.CascadeClassifier"], "fallback": "cv2 absent"}
    out["capabilities"] = caps

    # per-missing reason (only when explicitly asked — a bounded pip dry-run is a network call).
    # Mirror the REAL installer (_ensure_pkg): on PEP 668 (externally-managed) pip refuses, so the
    # installer retries with --break-system-packages — the probe does the same to reach the true
    # answer (no cp3XX wheel vs a wheel that WOULD install), instead of stopping at the PEP 668 wall.
    if _pip_check:
        import subprocess as _sp
        def _pip_dry(spec, extra=()):
            r = _sp.run([sys.executable, "-m", "pip", "install", "--dry-run", "--prefer-binary", spec]
                        + list(extra), capture_output=True, text=True, timeout=90)
            return r.returncode, ((r.stdout or "") + (r.stderr or "")).strip()
        reasons = {}
        for _label, _spec in _missing_specs.items():
            if out["libraries"].get(_label):
                continue
            try:
                rc, blob = _pip_dry(_spec)
                _pep668 = "externally-managed" in blob.lower() or "externally managed" in blob.lower()
                if _pep668:
                    rc, blob = _pip_dry(_spec, ["--break-system-packages"])   # what _ensure_pkg does
                low = blob.lower()
                _nowheel = ("no matching distribution" in low or "could not find a version" in low)
                if "externally-managed" in low or "externally managed" in low:
                    reasons[_label] = ("BLOCKED by PEP 668 (externally-managed) even with "
                                       "--break-system-packages — pip cannot install into this "
                                       "system Python; use a venv or a pip config override")
                elif _nowheel:
                    _hit = [ln.strip() for ln in blob.splitlines()
                            if "matching distribution" in ln.lower() or "could not find" in ln.lower()]
                    reasons[_label] = ("no %s wheel for Python %s%s — %s" % (
                        _spec, out["environment"]["python"], " (PEP 668 aside)" if _pep668 else "",
                        (_hit[:1] or [""])[0][:120]))
                elif rc != 0:
                    reasons[_label] = ((blob.splitlines() or ["pip failed"])[-1][:180]
                                       + (" (after --break-system-packages)" if _pep668 else ""))
                else:
                    reasons[_label] = ("a wheel IS available%s — install just never completed "
                                       "(the observer that needs it has not run yet, or a prior "
                                       "attempt failed/timed out)"
                                       % (" once PEP 668 is bypassed" if _pep668 else ""))
            except Exception as _exc:
                reasons[_label] = "probe failed: %s" % _exc
        out["library_reasons"] = reasons

    # ── TensorFlow FAMILY probe — "which TF variant can this cell actually install?" The embedding
    # observers need FULL TF (tensorflow.keras.applications), so only the keras-carrying distributions
    # qualify — tflite-runtime / ai-edge-litert are inference-only and do NOT provide keras. Each is
    # dry-run-probed (mirroring the installer: PEP 668 → --break-system-packages) to see which has a
    # wheel for THIS Python. Opt-in (tf_family=1) — it is several bounded network calls.
    if str(data.get("tf_family") or data.get("tf") or "").strip().lower() in ("1", "yes", "true", "on"):
        import subprocess as _sp
        fam = {}
        _FAMILY = [
            ("tensorflow", "full TF (stable)"),
            ("tensorflow-cpu", "CPU-only TF (stable) — what the lab installs"),
            ("tf-nightly", "nightly build — usually the FIRST to carry a new-Python wheel"),
            ("tf-nightly-cpu", "CPU-only nightly"),
            ("intel-tensorflow", "Intel-optimized TF"),
        ]
        for _spec, _note in _FAMILY:
            try:
                def _dry(extra=()):
                    r = _sp.run([sys.executable, "-m", "pip", "install", "--dry-run",
                                 "--prefer-binary", _spec] + list(extra),
                                capture_output=True, text=True, timeout=90)
                    return r.returncode, ((r.stdout or "") + (r.stderr or "")).strip()
                rc, blob = _dry()
                if "externally-managed" in blob.lower():
                    rc, blob = _dry(["--break-system-packages"])
                low = blob.lower()
                if "no matching distribution" in low or "could not find a version" in low:
                    st = "no wheel for %s" % _pytag
                elif "externally-managed" in low:
                    st = "PEP 668 blocked (needs a venv)"
                elif rc == 0:
                    # pull the resolved version from the dry-run plan if present
                    _wl = [ln.strip() for ln in blob.splitlines()
                           if _spec.split("-")[0] in ln.lower() and ("would install" in low or "-" in ln)]
                    st = "INSTALLABLE — a wheel exists for %s" % _pytag
                else:
                    st = (blob.splitlines() or ["pip error"])[-1][:120]
                fam[_spec] = {"note": _note, "status": st,
                              "installable": st.startswith("INSTALLABLE")}
            except Exception as _exc:
                fam[_spec] = {"note": _note, "status": "probe failed: %s" % _exc, "installable": False}
        _yes = [s for s, v in fam.items() if v.get("installable")]
        out["tensorflow_family"] = {
            "note": ("embeddings need FULL TF (keras.applications); tflite-runtime / ai-edge-litert "
                     "are inference-only and do NOT qualify"),
            "candidates": fam,
            "installable_here": _yes,
            "verdict": ("installable on this cell: %s" % ", ".join(_yes)) if _yes else
                       ("NO full-TF variant has a wheel for %s — use a Python with TF wheels "
                        "(3.12/3.13) in a venv" % _pytag)}

    # ── phases — the boot-phase Supervisor units (redacted for a plain reader) ──
    # The declared corpora's units are named for their declaration (`svc:source-bootstrap:<id>`),
    # so they are DERIVED rather than listed: adding a corpus is a file, and a list here would go
    # stale the first time one arrived.
    from lib.akasha.api import source as _srcboot
    _PHASES = tuple(["svc:labo-register"]
                    + ["svc:source-bootstrap:%s" % d.get("id")
                       for d in _srcboot.source_declarations(kernel)])
    try:
        from lib.akasha.api import process as _sv
        for u in (_sv.list_units(kernel.base_dir) or []):
            if u.get("id") not in _PHASES:
                continue
            h = u.get("health") or {}
            _tick = h.get("last_tick")
            out["phases"].append({
                "id": u.get("id"), "state": h.get("state") or u.get("state"),
                "detail": h.get("detail"), "elapsed_s": h.get("elapsed_s"),
                "stale": bool(_tick and (_t.time() - _tick) > (h.get("stale_s") or 300)),
                "job": h.get("job"), "step_errors": h.get("step_errors")})
    except Exception as _exc:
        out["phases_error"] = str(_exc)

    # ── jobs — the JCL queue, narrowed to the analysis/vlab labels ──
    try:
        if kernel.jcl_worker:
            is_admin = "scope:sys:admin" in session.active_scopes
            jobs = kernel.jcl_worker.list_jobs(owner=None if is_admin else session.client_id)
            rel = [j for j in jobs if str(getattr(j, "label", "") or "").startswith(("analysis.", "vlab."))]
            by = {}
            fails = []
            for j in rel:
                st = getattr(j, "status", "?")
                by[st] = by.get(st, 0) + 1
                if st == "FAILED":
                    fails.append({"job": getattr(j, "job_id", None), "label": getattr(j, "label", None),
                                  "error": getattr(j, "error", None),
                                  "step_errors": (getattr(j, "step_errors", None) or [])[:3]})
            out["job_summary"] = {"by_status": by, "running": by.get("RUNNING", 0),
                           "pending": by.get("PENDING", 0), "failed": fails}
    except Exception as _exc:
        out["job_summary_error"] = str(_exc)

    # ── subjects — per source pool + the visual-curation run ──
    def _disp(method, d):
        r = kernel.dispatch({"jsonrpc": "2.0", "method": method,
                           "params": {"session_token": "admin", "data": d}, "id": "diag"}, TRUST_INTERNAL)
        return (r.get("result") if isinstance(r, dict) and "result" in r else None)

    _app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))     # app/
    _project_dir = os.path.dirname(_app_dir)                                    # the repository root (for `import app…`)
    if _project_dir not in sys.path:
        sys.path.insert(0, _project_dir)
    _phase_state = {p["id"]: p for p in out["phases"]}
    try:
        from app.scripts.labo_register import LABS
    except Exception:
        LABS = []
    try:
        AnalysisConcept = _api.concept_class(kernel, "analysis")
        _ac = AnalysisConcept(kernel.manager.get_session("admin"))
    except Exception:
        _ac = None
    for lab in LABS:
        pool = lab.get("pool")
        if not pool:
            continue
        subj = {"labo": "labo:%s" % lab.get("name"), "pool": pool}
        st = _disp("source.status", {"pool": pool}) or {}
        subj["frozen"] = bool(st.get("frozen"))
        subj["total"] = st.get("total")
        # media pools are intentionally NOT statistically analyzed (image metadata) — say so.
        _is_media = "bl_book_images" in pool or "visual_curation" in pool
        if _ac is not None and not _is_media:
            try:
                have = _ac._persisted_plugin_set("labo:%s" % lab.get("name"), pool)
                subj["count_fields"] = sum(1 for p in have if p.startswith("count:"))
                subj["scatter_pairs"] = sum(1 for p in have if p.startswith("scatter:"))
                subj["cluster_fields"] = sum(1 for p in have if p.startswith("groupby:"))
            except Exception as _exc:
                subj["analysis_error"] = str(_exc)
        # verdict for this pool
        if not subj["frozen"]:
            subj["verdict"] = "pool not frozen yet — analysis waits for the source layer"
        elif _is_media:
            subj["verdict"] = "media pool — statistical analysis intentionally skipped (see the VCL lab)"
        elif subj.get("count_fields"):
            # every pair of category fields must be prepared; a shortfall means the background heal
            # is still filling in pairs left over from an older, smaller cap — show it honestly.
            _cf = subj.get("count_fields") or 0
            _expect = _cf * (_cf - 1) // 2
            _sp = subj.get("scatter_pairs", 0)
            subj["expected_scatter_pairs"] = _expect
            if _expect and _sp < _expect:
                subj["verdict"] = ("PARTIAL — %d category counts prepared, but only %d of %d scatter "
                                   "pairs (the background heal is still filling the rest; re-check "
                                   "shortly)" % (_cf, _sp, _expect))
            else:
                subj["verdict"] = ("READY — %d category counts, %d scatter pairs, %d clusters prepared"
                                   % (_cf, _sp, subj.get("cluster_fields", 0)))
        elif out["job_summary"].get("running") or out["job_summary"].get("pending"):
            subj["verdict"] = "COMPUTING — a background analysis job is queued/running"
        else:
            subj["verdict"] = ("NOT PREPARED YET — no counts and no running job; the analysis_precompute workload "
                               "prepares every frozen pool on its next pass (workload.status "
                               "key=analysis-precompute/analysis_precompute)")
        out["subjects"].append(subj)

    # ── visual-curation run r1 observation readiness ──
    vc = {"run": "r1"}
    cph = _phase_state.get("svc:cma-bootstrap") or {}
    vc["phase"] = {"state": cph.get("state"), "detail": cph.get("detail"),
                   "job": cph.get("job"), "step_errors": cph.get("step_errors")}
    try:
        _sp = _disp("vlab.spaces", {"run": "r1"}) or {}
        spaces = _sp.get("spaces") if isinstance(_sp, dict) else None   # list of {space, observers, works}
        vc["spaces"] = {s.get("space"): s.get("works", 0) for s in spaces} if isinstance(spaces, list) else None
        _obs = sum((s or {}).get("works", 0) for s in spaces) if isinstance(spaces, list) else 0
        vc["observations"] = _obs
        if _obs:
            vc["verdict"] = "READY — %d feature-space observations on run r1" % _obs
        elif cph.get("state") == "failed":
            _why = cph.get("detail") or ""
            _libmiss = [k for k in ("numpy", "Pillow") if not out["libraries"].get(k)]
            vc["verdict"] = ("STALLED — CMA compute failed: %s%s" %
                             (_why, (" · missing libs: %s" % ", ".join(_libmiss)) if _libmiss else ""))
        elif cph.get("state") in ("running",):
            vc["verdict"] = "COMPUTING — CMA machine-observation job running (%s)" % (cph.get("detail") or "")
        elif not out["libraries"].get("numpy") or not out["libraries"].get("Pillow"):
            vc["verdict"] = ("LIBRARY MISSING — numpy/Pillow not importable, so the color/geometry/"
                             "texture observers produce nothing (feature spaces stay 0)")
        else:
            vc["verdict"] = "WAITING/UNKNOWN — no observations yet and no running job (%s)" % (cph.get("state") or "no phase")
    except Exception as _exc:
        vc["error"] = str(_exc)
    out["visual_curation"] = vc

    # ── overall one-liner ──
    _bad = [s["verdict"] for s in out["subjects"] if s["verdict"].startswith(("STALLED", "LIBRARY"))]
    if vc.get("verdict", "").startswith(("STALLED", "LIBRARY")):
        _bad.append(vc["verdict"])
    if _bad:
        out["verdict"] = "ATTENTION — " + "; ".join(_bad[:3])
    elif any(s["verdict"].startswith(("COMPUTING", "PARTIAL")) for s in out["subjects"]) or vc.get("verdict", "").startswith("COMPUTING"):
        out["verdict"] = "COMPUTING — background jobs still filling in; re-open in a moment"
    elif any(s["verdict"].startswith("WAITING") for s in out["subjects"]):
        out["verdict"] = "WAITING — precompute not started (relations/serve gate); check again shortly"
    else:
        out["verdict"] = "OK — analyses prepared (or intentionally skipped)"
    return _ok(rid, out)
