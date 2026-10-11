"""
Visual Curation Laboratory — Phase 1 (Machine Observation), concept model `vlab`.

Core research question: when different machine-vision models observe the SAME artworks, what
remains stable and what changes? Phase 1 RECORDS what each machine observed; it does not decide
what an artwork means (that is Phase 2 — LLM / Society — which consumes Phase 1 BY REFERENCE).

Two laws this layer is built to hold (spec: docs/for-llm/visual-curation-lab-spec.md):

  1. Never present a machine observation as an artwork property. An observation is
     `observation → observes source, by model M, class person @ 0.91`, never
     `artwork.contains_person = true`. Observer, model version, config, confidence stay attached,
     and the Source Atom is IMMUTABLE — an observer never mutates it.

  2. Memory discipline (docs/for-llm/memory-discipline.md — the five OOMs this file was written
     AFTER). The image binary is NEVER stored in an atom; an atom holds only an `image_ref`. A run
     is a WRITER-SIDE batch that streams the pool ONE image at a time (R1/R4), resumable via a
     per-(source,observer) sentinel (R5). Observer model loads are wrapped in `native_load` (R6).
     Every read is O(K) (R1). This is why the layer cannot collapse the writer.

It sits on the existing Source layer (artwork records + pools), the VisionEngine (Observer A's
LiteRT backend), and the universal-write base (guest-readable public lab). Observers are
degradation-first plugins: with no real model installed, an observer degrades to a DETERMINISTIC
mock (pseudo-detections seeded from a stable hash of the image_ref) so the whole pipeline and the
eval run reproducibly with no weights; the mock's model identity says variant=mock and is never
presented as a real model. Real TF/YOLO adapters are drop-in (weights supplied deploy-side).
"""
import hashlib
import json
import logging
import os
from typing import Any, Dict, List, Optional

from lib.akasha.api.concepts import UniversalConcept, UNIVERSAL, slug


def _wb_tag(bench: str) -> str:
    """The Set-name component for a bench coordinate (D2-M §2): the bare bench name, `wb:` stripped,
    slugged — so `wb:plants_vision` → `set:wb:plants_vision:observations` (the meta keeps `wb:...`)."""
    b = bench or ""
    if b.startswith("wb:"):
        b = b[3:]
    return slug(b)

logger = logging.getLogger("Akasha.VisionLab")

# Image extensions the local-directory scanner accepts (bounded, explicit — never "all files").
_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tif", ".tiff"}

# A small, fixed detection vocabulary for the deterministic mock observer. Real observers report
# their own classes; the mock draws from this so agreement/disagreement is meaningful and stable.
_MOCK_CLASSES = ["person", "dog", "cat", "bird", "chair", "bottle", "car", "book",
                 "horse", "boat", "vase", "clock"]
_ANIMAL_CLASSES = {"dog", "cat", "bird", "horse"}
_OBJECT_DENSE = 4          # ≥ this many detections ⇒ set:vision:object_dense
_OBJECT_SPARSE = 1         # ≤ this many detections ⇒ set:vision:object_sparse


# ══ Observer framework (generic, degradation-first) ════════════════════════════════════════════

class VisionObserver:
    """Generic machine-vision observer. Resolves an image_ref, runs a model, normalizes output,
    returns an ObservationSet — and NEVER touches the Source Atom. A distinct configuration is a
    distinct model identity (§11): a new config → a new observation, never an overwrite."""

    family = "generic"
    model_name = "generic"
    variant = "mock"
    version = "0"
    framework = "none"
    framework_version = "0"
    kind = "detector"        # detector | classifier
    modality = "image"       # image | audio — every observer carries it (detectors default to image);
                             # FeatureObserver/AudioFeatureObserver override. Prevents an AttributeError
                             # in vlab.runs/spaces when a run includes a detector (tf/yolo) observer.

    def __init__(self, observer_id: str, config: Optional[Dict[str, Any]] = None):
        self.observer_id = observer_id
        self.config = dict(config or {})

    def model_identity(self) -> Dict[str, Any]:
        """IMMUTABLE provenance (§11): a label like 'yolov8' is insufficient — store the full
        identity. The model alias is derived from family:variant:version so a new config mints a
        new identity atom rather than overwriting one."""
        return {
            "family": self.family, "model_name": self.model_name, "variant": self.variant,
            "version": self.version, "weights_id": self.config.get("weights_id", self.variant),
            "framework": self.framework, "framework_version": self.framework_version,
            "confidence_threshold": self.config.get("confidence_threshold", 0.25),
            "iou_threshold": self.config.get("iou_threshold", 0.45),
            "input_resolution": self.config.get("input_resolution", 640),
            "preprocess_profile": self.config.get("preprocess_profile", "default"),
            "kind": self.kind,
        }

    def model_alias(self) -> str:
        return "model:%s:%s:%s" % (self.family, self.variant, self.version)

    def observe(self, image_ref: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        raise NotImplementedError

    def readiness(self) -> Dict[str, str]:
        """VPS-vision-coverage §2.5 — a cheap, SIDE-EFFECT-FREE readiness probe: it inspects deps and
        bundled files ONLY, never downloads a model or loads weights. Returns
        {status: ok|degraded, reason, model_file, model_sha8}. A pure-compute observer is always ok;
        a model-/dep-backed observer overrides this to say whether it would run its REAL model or
        degrade to a mock. Used by the `[vision] roster` boot line and the `vlab.roster` read op."""
        return {"status": "ok", "reason": "", "model_file": "", "model_sha8": ""}


def _stable_hash(*parts: str) -> int:
    h = hashlib.sha256("|".join(parts).encode("utf-8")).digest()
    return int.from_bytes(h[:8], "big")


class MockVisionObserver(VisionObserver):
    """Deterministic pseudo-observer: detections are a stable function of (observer_id, locator), so
    the full pipeline + eval run reproducibly with NO model, and two mock observers (v8 vs v10)
    disagree in a stable, comparable way. A base set of classes is seeded from the LOCATOR (shared
    across observers) plus an observer-specific delta (so shared/only-class comparison is non-trivial).
    Never presented as a real model — its variant stays 'mock'."""

    family = "mock"
    model_name = "mock-detector"
    framework = "deterministic"

    def observe(self, image_ref: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        loc = str((image_ref or {}).get("locator", ""))
        base = _stable_hash(loc)
        # shared base objects (same for every observer on this image)
        n_base = base % 4                                   # 0..3
        classes: List[str] = []
        for i in range(n_base):
            classes.append(_MOCK_CLASSES[_stable_hash(loc, "base", str(i)) % len(_MOCK_CLASSES)])
        # observer-specific delta: maybe add one, maybe drop one — the model disagreement (§19)
        d = _stable_hash(self.observer_id, loc)
        if d % 3 == 0 and classes:
            classes = classes[:-1]                          # this observer misses the last base object
        if d % 2 == 0:
            classes.append(_MOCK_CLASSES[(d >> 8) % len(_MOCK_CLASSES)])   # ...and sees an extra one
        detections = []
        for i, cls in enumerate(classes):
            g = _stable_hash(self.observer_id, loc, cls, str(i))
            detections.append({
                "class": cls,
                "confidence": round(0.50 + (g % 50) / 100.0, 3),        # 0.50..0.99, stable
                "bbox_x": round((g % 1000) / 1000.0, 3),
                "bbox_y": round(((g >> 10) % 1000) / 1000.0, 3),
                "bbox_width": round(0.05 + ((g >> 20) % 400) / 1000.0, 3),
                "bbox_height": round(0.05 + ((g >> 30) % 400) / 1000.0, 3),
            })
        return {"status": "success", "detections": detections, "features": {}}


class TFObserver(VisionObserver):
    """Observer A — global visual features via the existing VisionEngine (LiteRT MobileNet ladder).
    A CLASSIFIER, not a detector: it returns global features (top labels + backend), no bounding
    boxes. Degradation-first: when the backend/model is unavailable it records a FAILED observation
    (which is itself data — §12) rather than raising. The model load is native_load-wrapped inside
    VisionEngine (R6)."""

    family = "tensorflow"
    model_name = "mobilenet"
    variant = "litert"
    version = "1"
    framework = "litert"
    kind = "classifier"

    def __init__(self, observer_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(observer_id, config)
        self._engine = None

    def _engine_or_none(self):
        if self._engine is None:
            try:
                from lib.akasha.api.vision import VisionEngine
                self._engine = VisionEngine()
            except Exception as exc:                        # pragma: no cover - import guard
                logger.warning("[vlab] TFObserver engine unavailable: %s", exc)
                self._engine = False
        return self._engine or None

    def readiness(self) -> Dict[str, str]:
        try:
            from lib.akasha.api.vision import MODEL_FILE as _MODEL_FILE
        except Exception:
            _MODEL_FILE = "mobilenet_v1_1.0_224_quant.tflite"
        return _litert_readiness(_MODEL_FILE)

    def observe(self, image_ref: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        eng = self._engine_or_none()
        loc = str((image_ref or {}).get("locator", ""))
        if eng is None or not eng.available():
            return {"status": "failed", "failure_type": "backend_unavailable",
                    "failure_detail": "no LiteRT/numpy/PIL runtime", "detections": [], "features": {}}
        res = eng.classify(loc, top_k=int((config or {}).get("top_k", 5)))
        if "error" in res:
            return {"status": "failed", "failure_type": "inference_error",
                    "failure_detail": str(res.get("error"))[:200], "detections": [], "features": {}}
        labels = res.get("labels", [])
        return {"status": "success", "detections": [],
                "features": {"top_labels": labels, "backend": res.get("backend"),
                             "model": res.get("model"),
                             "dominant_class": labels[0]["label"] if labels else None}}


class YoloObserver(VisionObserver):
    """Observer B/C — object detection (YOLOv8 / YOLOv10). Adapter framework: if `ultralytics` is
    importable the real model runs (construction wrapped in native_load, R6); otherwise it DEGRADES
    to the deterministic mock and marks the observation degraded=True + variant reflects it, so the
    difference between v8 and v10 is still exercised end-to-end without weights. The maintainer
    supplies weights deploy-side to switch to the real detector — no code change here."""

    family = "yolo"
    framework = "ultralytics"

    def __init__(self, observer_id: str, config: Optional[Dict[str, Any]] = None,
                 version: str = "8", weights: Optional[str] = None):
        super().__init__(observer_id, config)
        self.version = version
        self.model_name = "yolov%s" % version
        self.variant = "n"
        self._weights = weights or self.config.get("weights")
        self._model = None
        self._degraded = None
        self._mock = MockVisionObserver(observer_id, config)

    def readiness(self) -> Dict[str, str]:
        # torch/ultralytics are too heavy for the current cell; absent ⇒ deterministic mock (§2.5).
        if not _pkg_present("ultralytics"):
            return {"status": "absent", "reason": "ultralytics",
                    "model_file": "", "model_sha8": ""}
        return {"status": "ok", "reason": "", "model_file": "", "model_sha8": ""}

    def _real_model(self):
        if self._model is not None:
            return self._model or None
        try:
            from ultralytics import YOLO                     # pragma: no cover - optional dep
            from lib.akasha.api.process import native_load
            with native_load("vlab.observer:%s" % self.observer_id):
                self._model = YOLO(self._weights or ("yolov%s%s.pt" % (self.version, self.variant)))
            self._degraded = False
        except Exception as exc:
            logger.warning("[vlab] %s degraded to mock (no ultralytics/weights): %s",
                           self.observer_id, exc)
            self._model = False
            self._degraded = True
        return self._model or None

    def observe(self, image_ref: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        model = self._real_model()
        if model is None:                                    # degraded → deterministic mock
            out = self._mock.observe(image_ref, config)
            out["degraded"] = True
            return out
        loc = str((image_ref or {}).get("locator", ""))      # pragma: no cover - needs weights
        try:
            res = model(loc, verbose=False)
            dets = []
            for r in res:
                for b in getattr(r, "boxes", []) or []:
                    xywhn = b.xywhn[0].tolist()
                    cls_id = int(b.cls[0]); conf = float(b.conf[0])
                    name = model.names.get(cls_id, str(cls_id)) if hasattr(model, "names") else str(cls_id)
                    dets.append({"class": name, "confidence": round(conf, 3),
                                 "bbox_x": round(xywhn[0], 3), "bbox_y": round(xywhn[1], 3),
                                 "bbox_width": round(xywhn[2], 3), "bbox_height": round(xywhn[3], 3)})
            return {"status": "success", "detections": dets, "features": {}, "degraded": False}
        except Exception as exc:
            return {"status": "failed", "failure_type": "inference_error",
                    "failure_detail": str(exc)[:200], "detections": [], "features": {}}


# ══ v0.2 — lightweight, multi-axis feature observers ═══════════════════════════════════════════
# The addendum's shift: from one object-detection-heavy viewpoint to MANY small, explicitly
# different machine viewpoints (color / geometry / texture / global embedding). Every observer is
# INDEPENDENT and degradation-first: a missing optional dependency (Pillow, numpy, TensorFlow,
# scikit-learn, OpenCV) degrades THAT observer to a deterministic mock feature vector — it never
# makes the whole laboratory unavailable (§18). Vectors are BOUNDED (memory discipline R1): a few
# dozen floats for color/geometry/texture, ≤ _EMBED_DIM for embeddings — the image binary is never
# stored, only measurements. Real computation is used when the deps are present; otherwise a stable
# hash-seeded vector keeps the pipeline + eval reproducible and the observer spaces distinct.

_EMBED_DIM = 32                      # bounded stored embedding width (real encoders are referenced/pooled)
_FEAT_SIZE = (64, 64)               # small fixed analysis resolution — measurements, not the image


# Operator-free provisioning: the observers' optional libraries are installed ON FIRST USE, never at
# boot — so a run computes REAL features on a fresh deploy without the operator touching pip. Same
# contract as VisionEngine's self-provisioning: lazy, cached per-process, best-effort, and honouring
# the single existing gate AKASHA_SKIP_AUTOINSTALL (a restricted/offline host sets it and every
# observer just degrades to its deterministic mock — startup NEVER depends on an install). This is
# disk provisioning; the model LOAD stays native_load-wrapped (R6) so its RSS is logged, and loading
# is lazy + reused across the run (R3), so the memory-discipline envelope is unchanged.
_PKG_CACHE: Dict[str, bool] = {}
_DEP_LOG: Dict[str, float] = {}          # throttle the [deps] absent lines (per pkg, hourly)
# F6 — the "[vlab] <observer> model absent" WARNING is throttled per (observer, model file), not
# per process: it fires once for each missing model (so the roster is diagnosable) and then stays
# quiet under a per-request readiness sweep (no log spam). `reset_model_absent_log()` clears it so an
# eval that removes a bundled model can assert the WARNING deterministically.
_MODEL_ABSENT_LOGGED: set = set()

# R1 — the observation coordinate-layer VERSION. Backfill idempotence keys on this, NOT on the mere
# presence of `family`: the previous build's backfill stamped `family` while the run atoms still had
# empty coords, so those observations carry family but blank bench/wf_branch/purpose. Bumping the
# version re-runs the backfill once (now that the run atoms are fixed) and re-stamps the coords.
_LAYER_V = 2


def _warn_model_absent(observer_id: str, model_file: str, hint: str = "") -> None:
    """One WARNING per (observer, model file) that the model is missing — throttled so a per-request
    readiness check does not re-log, but at least once so the operator sees it."""
    _k = (observer_id, model_file)
    if _k in _MODEL_ABSENT_LOGGED:
        return
    _MODEL_ABSENT_LOGGED.add(_k)
    logger.warning("[vlab] %s model absent: %s%s", observer_id, model_file,
                   (" (%s)" % hint) if hint else "")


def reset_model_absent_log() -> None:
    """Clear the per-(observer, file) model-absent throttle — for evals that remove a bundled model
    and assert the WARNING fires."""
    _MODEL_ABSENT_LOGGED.clear()


def _tier_policy() -> Dict[str, Any]:
    """The bundled per-tier dependency policy (vision-deps-bundle-order §3.1): app/config/tier_policy.json
    `{autoinstall: false, essential: [...]}`. A production tier (thesaurus) ships it with
    autoinstall=false → NO runtime pip; seeds omit it → the default (current) behavior. Cached."""
    cached = getattr(_tier_policy, "_c", None)
    if cached is not None:
        return cached
    pol: Dict[str, Any] = {}
    try:
        import json as _json
        from lib.akasha.api import declarations as _decl
        p = _decl.root("tier_policy")                  # the specification's `tier_policy` root (SPEC §2)
        if os.path.isfile(p):
            with open(p, "r", encoding="utf-8") as f:
                pol = _json.load(f) or {}
    except Exception:
        pol = {}
    _tier_policy._c = pol
    return pol


def _dep_absent_log(pkg: str, essential: bool) -> None:
    """One throttled line when a dep is absent on a no-autoinstall tier (§3.1). Essential → ERROR,
    otherwise WARNING. Bounded table (R7)."""
    import time as _t
    now = _t.time()
    if now - float(_DEP_LOG.get(pkg, 0.0)) < 3600.0:
        return
    _DEP_LOG[pkg] = now
    if len(_DEP_LOG) > 256:
        for _k in sorted(_DEP_LOG, key=_DEP_LOG.get)[:64]:
            _DEP_LOG.pop(_k, None)
    if essential:
        logger.error("[deps] %s absent AND essential; autoinstall is off for this tier — a bundled "
                     "essential is missing", pkg)
    else:
        logger.warning("[deps] %s absent; autoinstall is off for this tier — degrading", pkg)


def _ensure_pkg(import_name: str, pip_spec: str, timeout: int = 600, essential: bool = False) -> bool:
    """True if `import_name` is importable, installing `pip_spec` on demand. `essential=True` (numpy,
    Pillow — the lab's lightweight baseline) installs even under AKASHA_SKIP_AUTOINSTALL; heavy optional
    deps stay gated by it. §3.1 — a bundled `app/config/tier_policy.json {autoinstall:false}` (the R0 form
    of AKASHA_SKIP_AUTOINSTALL) forbids ALL runtime pip on a production tier: a missing package degrades
    with one throttled `[deps]` line (ERROR if essential/bundled, else WARNING), never a pip. Cached;
    failure is non-fatal (the caller degrades to mock)."""
    if import_name in _PKG_CACHE:
        return _PKG_CACHE[import_name]

    def _try():
        try:
            __import__(import_name)
            return True
        except Exception:
            return False

    ok = _try()
    if not ok:
        _pol = _tier_policy()
        _is_essential = essential or (import_name in set(_pol.get("essential") or []))
        if _pol.get("autoinstall") is False:
            # production tier: NO runtime pip — the deps are bundled at seed generation.
            _dep_absent_log(import_name, _is_essential)
            _PKG_CACHE[import_name] = False
            return False
    if not ok and (essential or not os.environ.get("AKASHA_SKIP_AUTOINSTALL")):
        try:
            import subprocess
            import sys
            logger.info("[vlab] installing %s on demand (operator-free provisioning)…", pip_spec)
            cmd = [sys.executable, "-m", "pip", "install", "--quiet", "--prefer-binary"] + pip_spec.split()
            r = subprocess.run(cmd, check=False, timeout=timeout,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if r.returncode != 0 and b"externally-managed" in (r.stderr or b""):
                subprocess.run(cmd + ["--break-system-packages"], check=False, timeout=timeout)
            ok = _try()
        except Exception as exc:
            logger.warning("[vlab] %s install failed (non-fatal, degrading to mock): %s", pip_spec, exc)
    _PKG_CACHE[import_name] = bool(ok)
    return _PKG_CACHE[import_name]


def _np():
    try:
        import numpy as _n
        return _n
    except Exception:
        if _ensure_pkg("numpy", "numpy", essential=True):
            try:
                import numpy as _n
                return _n
            except Exception:
                return None
        return None


def _resolve_image_array(locator: str, size=_FEAT_SIZE):
    """Resolve an image_ref locator (remote URL or local path) to a small HxWx3 uint8 numpy array,
    or None when Pillow/numpy is unavailable or the image cannot be loaded. Reuses VisionEngine's
    loader (URL / local path / bytes). One image at a time — never a bulk load."""
    n = _np()
    if n is None or not locator:
        return None
    _ensure_pkg("PIL", "Pillow", essential=True)            # operator-free: the lab's lightweight baseline, installed even under SKIP
    try:
        from lib.akasha.api.vision import VisionEngine
        img = VisionEngine.load_image(locator, size)      # PIL RGB, resized
        return n.asarray(img).astype("float32")
    except Exception:
        return None


def _mock_vector(dim: int, *seed_parts: str):
    """A deterministic unit-ish vector seeded by (observer family, locator, …) — the degraded path.
    Distinct per observer family, so different observer SPACES still yield different structure."""
    n = _np()
    vals = []
    for i in range(dim):
        vals.append((_stable_hash(*seed_parts, str(i)) % 100000) / 100000.0)
    if n is not None:
        v = n.asarray(vals, dtype="float32")
        nrm = float((v * v).sum() ** 0.5) or 1.0
        return (v / nrm).tolist()
    s = sum(x * x for x in vals) ** 0.5 or 1.0
    return [x / s for x in vals]


class FeatureObserver(VisionObserver):
    """Base for a lightweight measurement observer. Produces a `features` dict (named measurements)
    plus a bounded, normalized `feature_vector` for cross-artwork analysis (PCA / clustering /
    nearest-neighbour). NOT a detector and NOT a classifier — it answers 'what is measured?', never
    'what object is depicted?'. Stores measurable values only — never a semantic label like 'solemn'
    (§7/§22). Degradation-first: on any load/compute failure it emits a deterministic mock vector of
    the right shape (marked degraded=True) so the observer never breaks the lab."""

    kind = "feature"
    space = "generic"
    modality = "image"                 # the sense this feature space belongs to (image | audio)
    vector_keys: List[str] = []

    def _measure(self, arr) -> Dict[str, Any]:
        raise NotImplementedError

    def readiness(self) -> Dict[str, str]:
        # numpy + Pillow are the essential lightweight baseline; present ⇒ real measurements, absent ⇒
        # a deterministic mock vector (the lab never breaks). §2.5 probe is import-only, never installs.
        if not (_pkg_present("numpy") and _pkg_present("PIL")):
            return {"status": "absent", "reason": "numpy/Pillow",
                    "model_file": "", "model_sha8": ""}
        return {"status": "ok", "reason": "", "model_file": "", "model_sha8": ""}

    def observe(self, image_ref: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        loc = str((image_ref or {}).get("locator", ""))
        # A learned encoder (e.g. the LiteRT MobileNet) needs its native input resolution; a measurement
        # observer keeps the small analysis size. `resolve_size` defaults to _FEAT_SIZE for all the others.
        arr = _resolve_image_array(loc, size=getattr(self, "resolve_size", _FEAT_SIZE))
        if arr is None:
            vec = _mock_vector(len(self.vector_keys) or _EMBED_DIM, self.family, loc)
            feats = {"feature_space": self.space, "feature_vector": vec, "degraded": True,
                     **{k: round(vec[i], 4) for i, k in enumerate(self.vector_keys)}}
            return {"status": "success", "detections": [], "features": feats,
                    "feature_vector": vec, "feature_space": self.space, "degraded": True}
        try:
            feats = self._measure(arr)
        except Exception as exc:
            vec = _mock_vector(len(self.vector_keys) or _EMBED_DIM, self.family, loc)
            return {"status": "success", "detections": [],
                    "features": {"feature_space": self.space, "feature_vector": vec,
                                 "degraded": True, "measure_error": str(exc)[:120]},
                    "feature_vector": vec, "feature_space": self.space, "degraded": True}
        vec = feats.get("feature_vector") or [feats.get(k, 0.0) for k in self.vector_keys]
        feats["feature_space"] = self.space
        feats["feature_vector"] = [round(float(x), 5) for x in vec]
        return {"status": "success", "detections": [], "features": feats,
                "feature_vector": feats["feature_vector"], "feature_space": self.space}


class ColorObserver(FeatureObserver):
    """Chromatic observation (§7): RGB/HSV means, luminance & saturation statistics, warm/cool and
    dark/light ratios, colorfulness. NumPy + Pillow only — no learned model. Stores values, never
    labels ('solemn'/'cold' belong to Phase 2)."""
    family = "color"; model_name = "color-stats"; variant = "v1"; framework = "numpy"; space = "color"
    vector_keys = ["mean_r", "mean_g", "mean_b", "sat_mean", "val_mean", "lum_mean",
                   "colorfulness", "warm_ratio", "dark_ratio", "sat_var"]

    def _measure(self, arr) -> Dict[str, Any]:
        n = _np()
        r, g, b = arr[..., 0] / 255.0, arr[..., 1] / 255.0, arr[..., 2] / 255.0
        mx = n.maximum(n.maximum(r, g), b); mn = n.minimum(n.minimum(r, g), b)
        val = mx; sat = n.where(mx > 0, (mx - mn) / n.maximum(mx, 1e-6), 0.0)
        lum = 0.299 * r + 0.587 * g + 0.114 * b
        rg = n.abs(r - g); yb = n.abs(0.5 * (r + g) - b)
        colorfulness = float((rg.std() ** 2 + yb.std() ** 2) ** 0.5
                             + 0.3 * (rg.mean() ** 2 + yb.mean() ** 2) ** 0.5)
        warm = float((r > b).mean()); dark = float((lum < 0.4).mean())
        vec = [float(r.mean()), float(g.mean()), float(b.mean()), float(sat.mean()),
               float(val.mean()), float(lum.mean()), min(1.0, colorfulness),
               warm, dark, float(sat.var())]
        return {"feature_vector": vec, "rgb_mean": [round(float(r.mean()), 4), round(float(g.mean()), 4),
                round(float(b.mean()), 4)], "saturation_mean": round(float(sat.mean()), 4),
                "luminance_mean": round(float(lum.mean()), 4), "colorfulness": round(min(1.0, colorfulness), 4),
                "warm_ratio": round(warm, 4), "dark_ratio": round(dark, 4)}


class GeometryObserver(FeatureObserver):
    """Structural observation (§8): edge density and orientation ratios, left-right / top-bottom
    symmetry, center weight, centre of mass. Conventional NumPy gradient operators — no object
    semantics. Answers 'what structural tendencies?', not 'what object?'."""
    family = "geometry"; model_name = "geometry-stats"; variant = "v1"; framework = "numpy"
    space = "geometry"
    vector_keys = ["edge_density", "h_ratio", "v_ratio", "d_ratio", "lr_symmetry",
                   "tb_symmetry", "center_weight", "com_x", "com_y", "fg_density"]

    def _measure(self, arr) -> Dict[str, Any]:
        n = _np()
        gray = arr.mean(axis=2) / 255.0
        gy, gx = n.gradient(gray)
        mag = n.hypot(gx, gy)
        thr = float(mag.mean() + mag.std())
        edges = mag > thr
        edge_density = float(edges.mean())
        h = float((n.abs(gx) > n.abs(gy) * 2).mean())
        v = float((n.abs(gy) > n.abs(gx) * 2).mean())
        d = max(0.0, edge_density - h - v)
        lr = 1.0 - float(n.abs(gray - gray[:, ::-1]).mean())
        tb = 1.0 - float(n.abs(gray - gray[::-1, :]).mean())
        H, W = gray.shape
        cy, cx = H // 4, W // 4
        center_weight = float(gray[cy:3 * cy, cx:3 * cx].mean() / (gray.mean() + 1e-6))
        ys, xs = n.mgrid[0:H, 0:W]
        tot = gray.sum() + 1e-6
        com_x = float((xs * gray).sum() / tot / W); com_y = float((ys * gray).sum() / tot / H)
        fg = float((gray > gray.mean()).mean())
        vec = [edge_density, h, v, d, max(0.0, min(1.0, lr)), max(0.0, min(1.0, tb)),
               min(2.0, center_weight) / 2.0, com_x, com_y, fg]
        return {"feature_vector": vec, "edge_density": round(edge_density, 4),
                "lr_symmetry": round(lr, 4), "tb_symmetry": round(tb, 4),
                "center_weight": round(center_weight, 4),
                "center_of_mass": [round(com_x, 4), round(com_y, 4)]}


class TextureObserver(FeatureObserver):
    """Surface-complexity observation (§9): entropy, variance, gradient/Laplacian variance,
    high/low-frequency ratio, uniformity, complexity. NumPy + FFT — no heavy texture descriptors."""
    family = "texture"; model_name = "texture-stats"; variant = "v1"; framework = "numpy"
    space = "texture"
    vector_keys = ["entropy", "variance", "grad_var", "lap_var", "hi_freq", "lo_freq",
                   "uniformity", "complexity"]

    def _measure(self, arr) -> Dict[str, Any]:
        n = _np()
        gray = arr.mean(axis=2) / 255.0
        hist, _ = n.histogram(gray, bins=32, range=(0.0, 1.0), density=True)
        p = hist / (hist.sum() + 1e-9)
        entropy = float(-(p[p > 0] * n.log2(p[p > 0])).sum()) / 5.0     # ~0..1
        gy, gx = n.gradient(gray)
        grad_var = float(n.hypot(gx, gy).var())
        lap = n.abs(n.gradient(gx)[1] + n.gradient(gy)[0])
        lap_var = float(lap.var())
        f = n.abs(n.fft.fftshift(n.fft.fft2(gray)))
        H, W = gray.shape
        cy, cx = H // 2, W // 2
        lo = float(f[cy - H // 8:cy + H // 8, cx - W // 8:cx + W // 8].sum())
        tot = float(f.sum()) + 1e-9
        lo_ratio = lo / tot; hi_ratio = 1.0 - lo_ratio
        uniformity = float((p * p).sum())
        complexity = min(1.0, grad_var * 10 + entropy)
        vec = [min(1.0, entropy), min(1.0, float(gray.var()) * 4), min(1.0, grad_var * 20),
               min(1.0, lap_var * 40), hi_ratio, lo_ratio, uniformity, complexity]
        return {"feature_vector": vec, "entropy": round(entropy, 4),
                "variance": round(float(gray.var()), 5), "laplacian_var": round(lap_var, 6),
                "hi_freq_ratio": round(hi_ratio, 4), "uniformity": round(uniformity, 4),
                "complexity": round(complexity, 4)}


class CVObserver(FeatureObserver):
    """OpenCV structural observation (§8, a distinct machine sense): measurements the NumPy geometry/
    texture observers cannot cheaply produce — Canny edge density, ORB keypoint density, external
    contour count + mean area, Shi-Tomasi corner density, probabilistic Hough line count, and a
    Laplacian focus (sharpness) measure. Answers 'what structural features does a classical CV pipeline
    find?', never 'what object?' (values only, no labels — §7/§22). Degradation-first: OpenCV is
    installed on first use (opencv-python-headless — no GUI deps, right for a server); if it is absent
    or a compute fails, the base class emits a deterministic mock vector of the right shape so the lab
    never breaks. numpy (already essential) is OpenCV's only heavy dependency here."""
    family = "opencv"; model_name = "opencv-features"; variant = "v1"; framework = "opencv"
    space = "opencv"
    vector_keys = ["edge_density", "kp_density", "kp_count", "contour_count", "mean_contour_area",
                   "corner_density", "line_count", "focus"]

    def readiness(self) -> Dict[str, str]:
        if not (_pkg_present("numpy") and _pkg_present("cv2")):
            return {"status": "absent", "reason": "cv2",
                    "model_file": "", "model_sha8": ""}
        return {"status": "ok", "reason": "", "model_file": "", "model_sha8": ""}

    def _cv(self):
        """Import cv2, installing opencv-python-headless on demand (operator-free, SKIP-gated). Cached
        by _ensure_pkg. Returns the module or None (→ _measure raises → base class mock vector)."""
        try:
            import cv2  # noqa
            return cv2
        except Exception:
            if _ensure_pkg("cv2", "opencv-python-headless", timeout=900):
                try:
                    import cv2  # noqa
                    return cv2
                except Exception:
                    return None
            return None

    def _measure(self, arr) -> Dict[str, Any]:
        n = _np()
        cv2 = self._cv()
        if cv2 is None:
            raise RuntimeError("opencv unavailable")                 # → base class emits a mock vector
        # native_load-wrap the first real compute (R6 — bounded, logged); cheap per-image after import.
        try:
            from lib.akasha.api.process import native_load
            _ctx = native_load("vlab.observer:%s" % self.observer_id)
        except Exception:
            import contextlib
            _ctx = contextlib.nullcontext()
        with _ctx:
            gray = cv2.cvtColor(arr.astype("uint8"), cv2.COLOR_RGB2GRAY)
            H, W = gray.shape
            area = float(H * W) or 1.0
            edges = cv2.Canny(gray, 100, 200)
            edge_density = float((edges > 0).mean())
            # ORB keypoints (rotation/scale-robust corners+blobs) — a classic CV "interest" measure.
            try:
                orb = cv2.ORB_create(nfeatures=500)
                kps = orb.detect(gray, None) or []
            except Exception:
                kps = []
            kp_count = len(kps)
            kp_density = min(1.0, kp_count / 500.0)
            # external contours from the edge map
            _found = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cnts = _found[-2] if len(_found) >= 2 else []            # v3 returns 3-tuple, v4 returns 2
            contour_count = len(cnts)
            areas = [float(cv2.contourArea(c)) for c in cnts] if cnts else [0.0]
            mean_area = (sum(areas) / len(areas)) / area
            # Shi-Tomasi corners
            try:
                corners = cv2.goodFeaturesToTrack(gray, maxCorners=200, qualityLevel=0.01, minDistance=5)
                corner_count = int(0 if corners is None else len(corners))
            except Exception:
                corner_count = 0
            corner_density = min(1.0, corner_count / 200.0)
            # probabilistic Hough lines
            try:
                lines = cv2.HoughLinesP(edges, 1, n.pi / 180.0, threshold=50,
                                        minLineLength=float(min(H, W)) * 0.2, maxLineGap=10)
                line_count = int(0 if lines is None else len(lines))
            except Exception:
                line_count = 0
            focus = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        vec = [edge_density, kp_density, min(1.0, kp_count / 500.0), min(1.0, contour_count / 300.0),
               min(1.0, mean_area * 50.0), corner_density, min(1.0, line_count / 100.0),
               min(1.0, focus / 2000.0)]
        return {"feature_vector": vec, "edge_density": round(edge_density, 4),
                "keypoints": kp_count, "contours": contour_count,
                "corners": corner_count, "hough_lines": line_count,
                "focus_laplacian_var": round(focus, 2)}


class LiteRTFeatureObserver(FeatureObserver):
    """Semantic-emphasis observation via the LiteRT MobileNet classifier (the ai-edge-litert ladder —
    already present on the cell, no heavy dep). Turns the classifier's score profile into a bounded
    analysis vector: top-1 confidence, top-5 mass, entropy + effective distinct classes (how decisive
    the classifier is), and an 8-bucket score-weighted hash-fingerprint of the top labels (a compact
    'what does a pretrained classifier emphasize' axis). This enriches ANALYSIS with a lightweight
    semantic space — distinct from color/geometry/texture/opencv — using the SAME model that already
    labels the corpus for machine observation. Degradation-first: no LiteRT/model → a mock vector of
    the right shape (the lab never breaks). Values only, never a curatorial label (§7/§22)."""
    family = "litert"; model_name = "mobilenet"; variant = "litert"; framework = "litert"
    space = "litert"
    vector_keys = ["top1", "top5_mass", "entropy", "eff_classes",
                   "h0", "h1", "h2", "h3", "h4", "h5", "h6", "h7"]

    def __init__(self, observer_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(observer_id, config)
        self._engine = None

    def readiness(self) -> Dict[str, str]:
        try:
            from lib.akasha.api.vision import MODEL_FILE as _MODEL_FILE
        except Exception:
            _MODEL_FILE = "mobilenet_v1_1.0_224_quant.tflite"
        return _litert_readiness(_MODEL_FILE)

    def _engine_or_none(self):
        if self._engine is None:
            try:
                from lib.akasha.api.vision import VisionEngine
                self._engine = VisionEngine()
            except Exception:
                self._engine = False
        return self._engine or None

    def observe(self, image_ref: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        loc = str((image_ref or {}).get("locator", ""))
        eng = self._engine_or_none()
        res = eng.classify(loc, top_k=20) if (eng and eng.available()) else {"error": "no litert"}
        if not isinstance(res, dict) or "error" in res or not res.get("labels"):
            vec = _mock_vector(len(self.vector_keys), self.family, loc)          # degradation-first
            feats = {"feature_space": self.space, "feature_vector": vec, "degraded": True,
                     "degraded_reason": (res.get("error") if isinstance(res, dict) else "no labels")}
            return {"status": "success", "detections": [], "features": feats,
                    "feature_vector": vec, "feature_space": self.space, "degraded": True}
        labels = res["labels"]
        n = _np()
        scores = n.asarray([max(0.0, float(l.get("score", 0.0))) for l in labels], dtype="float32")
        s = float(scores.sum()) or 1.0
        p = scores / s
        top1 = float(scores[0]) if len(scores) else 0.0
        top5_mass = float(scores[:5].sum() / s)
        entropy = float(-(p[p > 0] * n.log2(p[p > 0])).sum()) / 5.0                # ~0..1
        eff = float(2.0 ** (entropy * 5.0)) / max(1, len(scores))                  # effective #classes, 0..1
        buckets = [0.0] * 8
        for l in labels:                                                          # score-weighted label hash
            b = (hash(str(l.get("label", ""))) & 0x7fffffff) % 8
            buckets[b] += max(0.0, float(l.get("score", 0.0)))
        bs = sum(buckets) or 1.0
        buckets = [x / bs for x in buckets]
        vec = [min(1.0, top1), min(1.0, top5_mass), min(1.0, entropy), min(1.0, eff)] + buckets
        return {"status": "success", "detections": [],
                "features": {"feature_space": self.space, "feature_vector": [round(float(x), 5) for x in vec],
                             "dominant_class": labels[0].get("label"), "top1_score": round(top1, 4),
                             "entropy": round(entropy, 4), "backend": res.get("backend")},
                "feature_vector": [round(float(x), 5) for x in vec], "feature_space": self.space}


# ── lightweight DETECTORS (the YOLO-front-stage: many installable machine senses) ───────────────
# The addendum's multi-axis principle applied to detection: as many INSTALLABLE detectors as the cell
# supports, each degradation-first. A detector that cannot load its backend/model records a clean
# "unavailable" observation (data, not a crash) so the lab never breaks — the SAME contract as the
# feature observers and YOLO. Each detector ALSO emits a bounded feature vector derived from its
# detections, so it contributes an analysis SPACE too (diverse observations enrich BOTH surfaces).
def _vlab_models_dir() -> str:
    return os.path.join(os.getcwd(), "env", "models")


def _fetch_model(url: str, dest: str, timeout: int = 60) -> bool:
    """Fetch a model file to `dest` on demand (gated by AKASHA_SKIP_AUTOINSTALL — a restricted/offline
    host just degrades). Network; graceful on any failure. Same lazy-fetch contract as VisionEngine."""
    if os.path.exists(dest):
        return True
    if os.environ.get("AKASHA_SKIP_AUTOINSTALL"):
        return False
    try:
        import urllib.request
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        logger.info("[vlab] fetching detection model: %s", url)
        req = urllib.request.Request(url, headers={"User-Agent": "AkashaVision/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            blob = resp.read()
        if url.endswith(".zip") or dest.endswith(".zip"):
            with open(dest, "wb") as f:
                f.write(blob)
        else:
            with open(dest, "wb") as f:
                f.write(blob)
        return os.path.exists(dest)
    except Exception as exc:
        logger.warning("[vlab] model fetch failed (non-fatal): %s", exc)
        return False


class DetectorObserver(VisionObserver):
    """Base for a lightweight detector. `_detect(arr, loc)` returns a list of detections
    ({class, confidence, bbox_x/y/width/height} — normalized, matching the YOLO shape), or None when
    the backend/model is UNAVAILABLE on this cell (→ a clean 'unavailable' observation, never a crash).
    The base derives a bounded feature vector from the detections so the detector is ALSO a selectable
    analysis space. Values only (§7/§22) — a detected class name is an observation BY the model, never a
    property asserted of the artwork."""
    kind = "detector"
    space = None
    input_size = (320, 320)
    vector_keys = ["n_det", "mean_conf", "max_conf", "mean_area", "max_area",
                   "c0", "c1", "c2", "c3", "c4", "c5", "c6", "c7"]

    def _detect(self, arr, loc):
        raise NotImplementedError

    def _det_vector(self, dets):
        confs = [float(d.get("confidence", 0.0)) for d in dets] or [0.0]
        areas = [float(d.get("bbox_width", 0.0)) * float(d.get("bbox_height", 0.0)) for d in dets] or [0.0]
        buckets = [0.0] * 8
        for d in dets:
            b = (hash(str(d.get("class", ""))) & 0x7fffffff) % 8
            buckets[b] += max(0.0, float(d.get("confidence", 0.0)))
        bs = sum(buckets) or 1.0
        buckets = [x / bs for x in buckets]
        return [min(1.0, len(dets) / 10.0), sum(confs) / len(confs), max(confs),
                sum(areas) / len(areas), max(areas)] + buckets

    def observe(self, image_ref: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        loc = str((image_ref or {}).get("locator", ""))
        arr = _resolve_image_array(loc, size=self.input_size)
        try:
            dets = self._detect(arr, loc)
        except Exception as exc:
            return {"status": "failed", "failure_type": "inference_error",
                    "failure_detail": str(exc)[:200], "detections": [], "features": {}}
        if dets is None:                                        # backend/model unavailable on this cell
            return {"status": "failed", "failure_type": "backend_unavailable",
                    "failure_detail": "%s detector unavailable (dep/model missing on this cell)" % self.family,
                    "detections": [], "features": {}}
        vec = [round(float(x), 5) for x in self._det_vector(dets)]
        feats = {"detection_count": len(dets)}
        if self.space:
            feats.update({"feature_space": self.space, "feature_vector": vec})
        out = {"status": "success", "detections": dets, "features": feats}
        if self.space:
            out["feature_vector"] = vec
            out["feature_space"] = self.space
        return out


class CascadeObserver(DetectorObserver):
    """OpenCV Haar cascade detection (faces / eyes / bodies). The classic lightweight detector — no
    heavy dep, no weights download (the cascades ship inside the OpenCV wheel, cv2.data). ⚠️ OpenCV 5.0
    REMOVED cv2.CascadeClassifier; this observer is therefore version-guarded — it runs where OpenCV
    ≤4.x is available (e.g. a 3.12 venv) and cleanly reports 'unavailable' on an OpenCV-5 cell (the same
    'enable when the environment allows' pattern as YOLO)."""
    family = "cascade"; model_name = "haar"; variant = "v1"; framework = "opencv"; space = "cascade"
    input_size = (320, 240)
    _CASCADES = [("face", "haarcascade_frontalface_default.xml"),
                 ("eye", "haarcascade_eye.xml"),
                 ("body", "haarcascade_fullbody.xml")]

    def readiness(self) -> Dict[str, str]:
        if not _pkg_present("cv2"):
            return {"status": "absent", "reason": "cv2", "model_file": "", "model_sha8": ""}
        try:
            import cv2  # noqa
            if not hasattr(cv2, "CascadeClassifier"):
                # OpenCV 5.0 removed CascadeClassifier — the classic detector is unavailable here.
                return {"status": "absent", "reason": "CascadeClassifier",
                        "model_file": "", "model_sha8": ""}
        except Exception:
            return {"status": "absent", "reason": "cv2", "model_file": "", "model_sha8": ""}
        return {"status": "ok", "reason": "cv2 cascades", "model_file": "", "model_sha8": ""}

    def _detect(self, arr, loc):
        try:
            import cv2  # noqa
        except Exception:
            if not _ensure_pkg("cv2", "opencv-python-headless", timeout=900):
                return None
            import cv2  # noqa
        if not hasattr(cv2, "CascadeClassifier") or not hasattr(cv2, "data"):
            return None                                         # OpenCV 5.0 removed cascades
        if arr is None:
            return None
        n = _np()
        gray = cv2.cvtColor(arr.astype("uint8"), cv2.COLOR_RGB2GRAY)
        H, W = gray.shape
        dets = []
        for cls, xml in self._CASCADES:
            path = os.path.join(cv2.data.haarcascades, xml)
            if not os.path.exists(path):
                continue
            clf = cv2.CascadeClassifier(path)
            if clf.empty():
                continue
            for (x, y, w, h) in (clf.detectMultiScale(gray, 1.1, 4) or []):
                dets.append({"class": cls, "confidence": 0.9,
                             "bbox_x": round((x + w / 2.0) / W, 3), "bbox_y": round((y + h / 2.0) / H, 3),
                             "bbox_width": round(w / float(W), 3), "bbox_height": round(h / float(H), 3)})
        return dets


class LiteRTDetectObserver(DetectorObserver):
    """LiteRT object detection — SSD-MobileNet V1 (COCO 80 classes) on the ai-edge-litert ladder that
    already runs on the cell. A genuinely lightweight OBJECT detector (not just features), working on
    the current OpenCV-5 / Python-3.14 cell where YOLO (torch) is too heavy. Model fetched on demand
    (gated), interpreter native_load-wrapped (R6). Degradation-first: no backend/model → 'unavailable'."""
    family = "litert_detect"; model_name = "ssd_mobilenet_v1"; variant = "coco"; framework = "litert"
    space = "objdet"
    input_size = (300, 300)
    _URL = ("https://storage.googleapis.com/download.tensorflow.org/models/tflite/"
            "coco_ssd_mobilenet_v1_1.0_quant_2018_06_29.zip")

    def __init__(self, observer_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(observer_id, config)
        self._interp = None; self._labels = None; self._io = None

    def readiness(self) -> Dict[str, str]:
        return _litert_readiness("ssd_mobilenet_v1_coco_quant.tflite")

    def _load(self):
        if self._interp is not None:
            return self._interp or None
        try:
            from lib.akasha.api.vision import resolve_backend as _resolve_backend
            backend = _resolve_backend()
            if backend is None:
                self._interp = False; return None
            import zipfile as _zip
            # §2.2 — BUNDLED-FIRST: the SSD detector + COCO labelmap ship in assets/models/
            # (model:ssd_mobilenet_v1_coco). Use them if present; download only under
            # tier_policy.autoinstall, else degrade with one WARNING and NO network.
            bdir = _bundled_models_dir()
            b_model = os.path.join(bdir, "ssd_mobilenet_v1_coco_quant.tflite")
            b_labels = os.path.join(bdir, "coco_labelmap.txt")
            mdir = _vlab_models_dir()
            zpath = os.path.join(mdir, "coco_ssd_mobilenet_v1.zip")
            if os.path.exists(b_model):
                model_path, labels_path = b_model, b_labels
            else:
                model_path = os.path.join(mdir, "ssd_detect.tflite")
                labels_path = os.path.join(mdir, "ssd_labelmap.txt")
                if not os.path.exists(model_path):
                    if _tier_policy().get("autoinstall") is False:
                        _warn_model_absent("litert_detect", "ssd_mobilenet_v1_coco_quant.tflite",
                                           "bundle it under assets/models/")
                        self._interp = False; return None
                    if not _fetch_model(self._URL, zpath):
                        self._interp = False; return None
                    with _zip.ZipFile(zpath) as z:
                        for nm in z.namelist():
                            b = os.path.basename(nm)
                            if b == "detect.tflite":
                                open(model_path, "wb").write(z.read(nm))
                            elif b == "labelmap.txt":
                                open(labels_path, "wb").write(z.read(nm))
            self._labels = [l.strip() for l in open(labels_path, encoding="utf-8")] if os.path.exists(labels_path) else []
            name, Interpreter = backend
            from lib.akasha.api.process import native_load
            with native_load("vlab.observer:%s" % self.observer_id):
                itp = Interpreter(model_path=model_path); itp.allocate_tensors()
            self._interp = itp
            self._io = (itp.get_input_details(), itp.get_output_details())
        except Exception as exc:
            logger.warning("[vlab] litert_detect load failed (non-fatal): %s", exc)
            self._interp = False
        return self._interp or None

    def _detect(self, arr, loc):
        itp = self._load()
        if itp is None or arr is None:
            return None
        n = _np()
        inp, outp = self._io
        x = n.expand_dims(arr.astype(inp[0]["dtype"]), 0)
        itp.set_tensor(inp[0]["index"], x); itp.invoke()
        # SSD postprocess emits 4 tensors in the canonical order: locations, classes, scores, num.
        vals = [itp.get_tensor(o["index"]) for o in sorted(outp, key=lambda d: d["index"])]
        try:
            boxes = vals[0][0]; classes = vals[1][0]; scores = vals[2][0]
        except Exception:
            return []
        dets = []
        for i in range(min(len(scores), 20)):
            sc = float(scores[i])
            if sc < 0.4:
                continue
            ymin, xmin, ymax, xmax = [float(v) for v in boxes[i]]
            cid = int(classes[i]) + 1                            # labelmap has a leading background entry
            name = self._labels[cid] if self._labels and 0 <= cid < len(self._labels) else str(cid)
            dets.append({"class": name, "confidence": round(sc, 3),
                         "bbox_x": round((xmin + xmax) / 2.0, 3), "bbox_y": round((ymin + ymax) / 2.0, 3),
                         "bbox_width": round(max(0.0, xmax - xmin), 3),
                         "bbox_height": round(max(0.0, ymax - ymin), 3)})
        return dets


class CVDnnFaceObserver(DetectorObserver):
    """OpenCV DNN face detection (YuNet) — cv2.dnn is present even in OpenCV 5.0, so this is the
    OpenCV-native detector that DOES run on the current cell. Tiny model (~350 KB) fetched on demand.
    Uses cv2.FaceDetectorYN when available, else a raw cv2.dnn path; degradation-first otherwise."""
    family = "cvdnn_face"; model_name = "yunet"; variant = "2023mar"; framework = "opencv"; space = "face"
    input_size = (320, 320)
    _URL = ("https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/"
            "face_detection_yunet_2023mar.onnx")

    def readiness(self) -> Dict[str, str]:
        mf = "face_detection_yunet_2023mar.onnx"
        if not _pkg_present("cv2"):
            return {"status": "absent", "reason": "cv2", "model_file": mf, "model_sha8": ""}
        try:
            import cv2  # noqa
            if not hasattr(cv2, "FaceDetectorYN"):
                return {"status": "absent", "reason": "FaceDetectorYN", "model_file": mf, "model_sha8": ""}
        except Exception:
            return {"status": "absent", "reason": "cv2", "model_file": mf, "model_sha8": ""}
        return _model_probe(mf)

    def _detect(self, arr, loc):
        try:
            import cv2  # noqa
        except Exception:
            if not _ensure_pkg("cv2", "opencv-python-headless", timeout=900):
                return None
            import cv2  # noqa
        if not hasattr(cv2, "FaceDetectorYN") or arr is None:
            return None                                         # no YuNet API on this build
        # §2.3 — BUNDLED-FIRST: the YuNet model ships in assets/models/; download only under
        # tier_policy.autoinstall, else degrade (one WARNING, no network).
        b_yunet = os.path.join(_bundled_models_dir(), "face_detection_yunet_2023mar.onnx")
        if os.path.exists(b_yunet):
            mpath = b_yunet
        else:
            mpath = os.path.join(_vlab_models_dir(), "yunet_2023mar.onnx")
            if not os.path.exists(mpath):
                if _tier_policy().get("autoinstall") is False:
                    _warn_model_absent("cvdnn_face", "face_detection_yunet_2023mar.onnx",
                                       "bundle it under assets/models/")
                    return None
                if not _fetch_model(self._URL, mpath):
                    return None
        n = _np()
        bgr = cv2.cvtColor(arr.astype("uint8"), cv2.COLOR_RGB2BGR)
        H, W = bgr.shape[:2]
        det = cv2.FaceDetectorYN.create(mpath, "", (W, H), 0.6, 0.3, 5000)
        det.setInputSize((W, H))
        _rc, faces = det.detect(bgr)
        dets = []
        for f in (faces if faces is not None else []):
            x, y, w, h = float(f[0]), float(f[1]), float(f[2]), float(f[3])
            conf = float(f[-1])
            dets.append({"class": "face", "confidence": round(conf, 3),
                         "bbox_x": round((x + w / 2.0) / W, 3), "bbox_y": round((y + h / 2.0) / H, 3),
                         "bbox_width": round(w / float(W), 3), "bbox_height": round(h / float(H), 3)})
        return dets


class EmbeddingObserver(FeatureObserver):
    """Global visual embedding (§5/§6): a compact feature vector for similarity / neighbourhood /
    PCA / clustering — NOT a classifier. Tries a TensorFlow/Keras encoder (MobileNetV3 Small /
    EfficientNet-B0) with the load native_load-wrapped (R6); when TF is absent it degrades to a
    deterministic mock embedding (bounded _EMBED_DIM). Two encoders give two global spaces — the
    research value is how the SAME corpus reorganizes between them (§6/§15)."""
    kind = "feature"

    def __init__(self, observer_id: str, config: Optional[Dict[str, Any]] = None,
                 keras_app: str = "MobileNetV3Small", family: str = "mobilenet", space: str = "mobilenet"):
        super().__init__(observer_id, config)
        self.family = family; self.model_name = keras_app; self.variant = "keras"
        self.framework = "tensorflow"; self.space = space
        self._keras_app = keras_app; self._model = None

    def readiness(self) -> Dict[str, str]:
        # a heavy Keras encoder — dev-machine only; absent TF ⇒ deterministic mock embedding (§2.5).
        if not _pkg_present("tensorflow"):
            return {"status": "absent", "reason": "tensorflow",
                    "model_file": "", "model_sha8": ""}
        return {"status": "ok", "reason": "", "model_file": "", "model_sha8": ""}

    def _real(self):
        if self._model is not None:
            return self._model or None
        # Operator-free: install TensorFlow (CPU wheel) on first use, then load native_load-wrapped
        # (R6 — the heaviest observer; install is lazy + gated, the load's RSS is logged, the model is
        # reused across the run). A restricted host (AKASHA_SKIP_AUTOINSTALL) just uses the mock embedding.
        _ensure_pkg("tensorflow", "tensorflow-cpu", timeout=1200)
        try:
            from lib.akasha.api.process import native_load
            with native_load("vlab.observer:%s" % self.observer_id):
                import tensorflow as tf  # noqa
                from tensorflow.keras import applications as A
                ctor = getattr(A, self._keras_app)
                self._model = ctor(include_top=False, pooling="avg", weights="imagenet")
        except Exception as exc:
            logger.warning("[vlab] %s degraded to mock embedding (no TF/Keras): %s",
                           self.observer_id, exc)
            self._model = False
        return self._model or None

    def _measure(self, arr) -> Dict[str, Any]:
        n = _np()
        model = self._real()
        if model is None:                                        # deterministic mock embedding
            raise RuntimeError("mock")                           # → base class emits a mock vector
        x = n.expand_dims(arr, 0)                                # pragma: no cover - needs TF
        emb = model.predict(x, verbose=0)[0]
        emb = n.asarray(emb, dtype="float32")
        nrm = float((emb * emb).sum() ** 0.5) or 1.0
        emb = emb / nrm
        vec = emb[:_EMBED_DIM].tolist()                          # bounded stored width; full stays a ref
        return {"feature_vector": vec, "embedding_dimension": int(emb.shape[0]),
                "embedding_norm": round(float(nrm), 4), "stored_dims": len(vec)}


def _bundled_models_dir() -> str:
    """The seed-bundled model dir (vision-deps-bundle-order §1): assets/models/, shipped at seed
    generation on the thesaurus tier — numpy/Pillow/LiteRT read it with no runtime pip."""
    return os.path.join(os.getcwd(), "assets", "models")


def _bundled_model(filename: str):
    """Resolve a bundled model file, verifying its sha256 against assets/models/model.json when the
    manifest names it. Returns (path, ok, reason); ok=False → the observer degrades to a labelled mock.
    Falls back to env/models (a dev machine may have fetched the file there)."""
    mdir = _bundled_models_dir()
    path = os.path.join(mdir, filename)
    if not os.path.isfile(path):
        alt = os.path.join(_vlab_models_dir(), filename)
        if os.path.isfile(alt):
            path = alt
        else:
            return path, False, "model file absent"
    try:
        want = _manifest_sha(filename)       # top-level embedder OR any models[] entry
        if want:
            import hashlib as _hl
            h = _hl.sha256()
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(1 << 20), b""):
                    h.update(chunk)
            if h.hexdigest() != want:
                return path, False, "sha256 mismatch"
    except Exception:
        pass
    return path, True, ""


def _pkg_present(import_name: str) -> bool:
    """Side-effect-free presence probe: True if importable, no install ever attempted (used by the
    §2.5 readiness roster — a probe must never trigger a pip)."""
    try:
        __import__(import_name)
        return True
    except Exception:
        return False


def _manifest_sha(filename: str) -> str:
    """The expected sha256 for a bundled file, from assets/models/model.json — matching the top-level
    embedder fields OR any `models[]` entry (`file` or `labels`). '' when the manifest is silent."""
    try:
        import json as _json
        p = os.path.join(_bundled_models_dir(), "model.json")
        if not os.path.isfile(p):
            return ""
        mani = _json.load(open(p, encoding="utf-8")) or {}
        if mani.get("file") == filename and mani.get("sha256"):
            return str(mani["sha256"])
        for e in (mani.get("models") or []):
            if e.get("file") == filename and e.get("sha256"):
                return str(e["sha256"])
            if e.get("labels") == filename and e.get("labels_sha256"):
                return str(e["labels_sha256"])
    except Exception:
        pass
    return ""


def _model_probe(filename: str) -> Dict[str, str]:
    """§2.5 readiness of a single bundled model file (no download, no weights load): resolves the
    bundled path + verifies sha against the manifest. ok ⇒ present + verified; else `absent` with a
    compact reason token. The reported sha8 is the manifest's (equal to the file's when ok, since
    _bundled_model verifies)."""
    _path, ok, reason = _bundled_model(filename)
    sha8 = _manifest_sha(filename)[:8]
    if ok:
        return {"status": "ok", "reason": "model bundled",
                "model_file": filename, "model_sha8": sha8}
    # compact reason token for the one-line roster ("absent(model file)")
    tok = "model file" if reason in ("", "model file absent") else reason
    return {"status": "absent", "reason": tok, "model_file": filename, "model_sha8": ""}


def _litert_readiness(model_file: str) -> Dict[str, str]:
    """§2.5 readiness for a LiteRT-backed observer: the bundled model file must be present + verified
    AND a TFLite interpreter backend importable (no install probe). Shared by the litert classifier,
    the SSD detector, and the mobilenet embedder."""
    p = _model_probe(model_file)
    if p["status"] != "ok":
        return p
    try:
        from lib.akasha.api.vision import VisionEngine
        backed = VisionEngine.backend_available(allow_install=False)
    except Exception:
        backed = False
    if not backed:
        return {"status": "absent", "reason": "litert",
                "model_file": model_file, "model_sha8": p["model_sha8"]}
    return p


class LiteRTEmbeddingObserver(FeatureObserver):
    """Global visual embedding on the LiteRT ladder (vision-deps-bundle-order §1.2). A BUNDLED
    MobileNetV3-Small feature-vector .tflite (assets/models/, numpy/Pillow/ai_edge_litert only — no
    TensorFlow, NO runtime pip) → a 1024-d vector, stored bounded to _EMBED_DIM (the SAME Feature atom
    shape the Keras path produced, so B4/B5 and vlab.spaces are unchanged). A missing model file or a
    sha256 mismatch → a labelled mock, ONE WARNING (degradation-first). The heavy Keras encoder stays
    reachable under `mobilenet_keras` for dev machines."""
    kind = "feature"
    resolve_size = (224, 224)          # the model's native input; the base resolves the image here

    def __init__(self, observer_id: str, config: Optional[Dict[str, Any]] = None,
                 model_file: str = "mobilenet_v3_small_fv.tflite",
                 family: str = "mobilenet", space: str = "mobilenet", variant: str = "v3small_fv"):
        super().__init__(observer_id, config)
        self.family = family
        self.model_name = "mobilenet_v3_small"
        self.variant = variant
        self.framework = "litert"
        self.space = space
        self._model_file = model_file
        self._interp = None
        self._io = None
        self._native_dim = 0

    def readiness(self) -> Dict[str, str]:
        return _litert_readiness(self._model_file)

    def _load(self):
        if self._interp is not None:
            return self._interp or None
        path, ok, reason = _bundled_model(self._model_file)
        if not ok:
            logger.warning("[vlab] %s degraded to mock embedding — bundled model %s (%s)",
                           self.observer_id, self._model_file, reason)
            self._interp = False
            return None
        try:
            from lib.akasha.api.vision import resolve_backend as _resolve_backend
            backend = _resolve_backend(allow_install=False)     # never pip at observe time (§3)
            if backend is None:
                logger.warning("[vlab] %s degraded to mock — no LiteRT backend", self.observer_id)
                self._interp = False
                return None
            _name, Interpreter = backend
            from lib.akasha.api.process import native_load
            with native_load("vlab.observer:%s" % self.observer_id):
                itp = Interpreter(model_path=path)
                itp.allocate_tensors()
            self._interp = itp
            self._io = (itp.get_input_details(), itp.get_output_details())
            try:
                self._native_dim = int(list(self._io[1][0]["shape"])[-1])
            except Exception:
                self._native_dim = 0
            logger.info("[vlab] mobilenet litert model=%s dim=%s", self._model_file, self._native_dim or "?")
        except Exception as exc:
            logger.warning("[vlab] %s litert load failed (non-fatal, mock): %s", self.observer_id, exc)
            self._interp = False
        return self._interp or None

    def _measure(self, arr) -> Dict[str, Any]:
        n = _np()
        itp = self._load()
        if itp is None:
            raise RuntimeError("mock")                          # → base class emits a labelled mock vector
        inp, outp = self._io
        x = n.asarray(arr, dtype="float32")
        # the resolver gave the model's native size; cast to the input dtype (float models expect [0,1]-ish
        # floats — the resolver returns uint8, so scale to [0,1] for a float input, pass through for uint8).
        idt = inp[0]["dtype"]
        if "float" in str(idt):
            x = (x / 255.0).astype(idt)
        else:
            x = x.astype(idt)
        x = n.expand_dims(x, 0)
        itp.set_tensor(inp[0]["index"], x)
        itp.invoke()
        emb = n.asarray(itp.get_tensor(outp[0]["index"])[0], dtype="float32").reshape(-1)
        nrm = float((emb * emb).sum() ** 0.5) or 1.0
        emb = emb / nrm
        vec = emb[:_EMBED_DIM].tolist()                         # bounded stored width; the full stays a ref
        return {"feature_vector": vec, "embedding_dimension": int(emb.shape[0]),
                "embedding_norm": round(float(nrm), 4), "stored_dims": len(vec), "degraded": False}


# The nucleus set the roster reads to load PROMOTED learned heads (must match
# bench_learning.LEARNED_OBSERVERS_SET). Kept in the shared nucleus so a fresh VisionLabConcept
# instance (one per dispatch) rediscovers a head promoted by `learning.promote`.
LEARNED_OBSERVERS_SET = "set:vlab:learned"


class LearnedHeadObserver(VisionObserver):
    """A CLASSIFIER promoted from a learning bench (`learning.promote`): its model = a trained head file
    (OUTSIDE the store) over a declared base feature SPACE. `observe()` embeds the image transiently in
    the base space (reusing the existing observer for that space — no binary stored), runs the head,
    and returns species predictions @ confidence — `variant=learned`, never presented as a fact (the
    standing vlab principle §11). Degradation-first: a missing weights file, or a base space that can
    only mock, still yields a deterministic labeled prediction marked degraded — the bench stays
    honest. The head-predict is pure (`lib.akasha.learned_head`), so no heavy dep at observe time."""

    family = "learned"
    variant = "learned"
    version = "1"
    framework = "learned_head"
    kind = "classifier"
    modality = "image"

    def __init__(self, observer_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(observer_id, config)
        self.version = slug(str(self.config.get("model", observer_id)))[-24:] or "1"
        self._base = None
        self._head = None
        self._head_loaded = False

    def model_alias(self) -> str:
        return str(self.config.get("model") or ("model:learned:%s:%s" % (self.observer_id, self.version)))

    def _base_observer(self):
        if self._base is None:
            space = str(self.config.get("base_space") or "mobilenet")
            self._base = _default_observers().get(space) or EmbeddingObserver(
                "base", family="mobilenet", space="mobilenet")
        return self._base

    def _load_head(self):
        if not self._head_loaded:
            self._head_loaded = True
            try:
                from lib.akasha.api import learned as lh
                self._head = lh.load(str(self.config.get("weights_path") or ""))
            except Exception:
                self._head = None
        return self._head

    def observe(self, image_ref: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        from lib.akasha.api import learned as lh
        classes = list(self.config.get("classes") or [])
        cfg = config or {}
        # S2-k2 — the concept layer may hand us the item's ALREADY-COMPUTED base embedding (an earlier
        # feature run of the same base space); when it does, run ONLY the head and skip re-embedding —
        # the encoder is the ten-minute cost of a learned-head observe. Otherwise embed transiently (the
        # base observer degrades to a mock vector itself).
        import time as _t
        _base_vec = cfg.get("base_vector")
        reused_base = False
        # S2-k3 — split the observe cost into t_fetch / t_embed / t_head so the log shows where a
        # learned-head observe spends its time. When a base_vector is supplied the encoder AND the image
        # are skipped entirely (t_fetch=t_embed=0 — the observer must not touch the image on reuse).
        _t_fetch = _t_embed = 0.0
        if isinstance(_base_vec, (list, tuple)) and _base_vec:
            vec = [float(x) for x in _base_vec]
            base_degraded = False
            reused_base = True
        else:
            _e0 = _t.perf_counter()
            try:
                emb = self._base_observer().observe(image_ref) or {}
                vec = emb.get("feature_vector") or []
                base_degraded = bool(emb.get("degraded"))
                _t_fetch = float(emb.get("t_fetch") or 0.0)   # the base observer reports its fetch/decode
            except Exception:
                vec, base_degraded = [], True
            _t_embed = round(_t.perf_counter() - _e0, 4)
        _h0 = _t.perf_counter()
        head = self._load_head()
        if head is None or not vec:                              # weights missing → honest mock
            loc = str((image_ref or {}).get("locator", ""))
            label = classes[_stable_hash(self.observer_id, loc) % len(classes)] if classes else "unknown"
            return {"status": "success",
                    "detections": [{"class": label, "confidence": 0.25, "kind": "prediction"}],
                    "features": {}, "variant": "learned", "degraded": True, "reused_base": reused_base,
                    "_timing": {"t_fetch": _t_fetch, "t_embed": _t_embed,
                                "t_head": round(_t.perf_counter() - _h0, 4)}}
        # the head ran (degraded is about the LEARNED EYE — weights present ⇒ not degraded); whether the
        # base EMBEDDING was itself a mock (no image resolved) is carried separately for observability.
        label, conf = lh.predict(head, [float(x) for x in vec])
        return {"status": "success",
                "detections": [{"class": label, "confidence": conf, "kind": "prediction",
                                "base_degraded": base_degraded}],
                "features": {}, "variant": "learned", "degraded": False,
                # S2-k3 — per-observe timing split (t_fetch=t_embed=0 when the base_vector was reused).
                "_timing": {"t_fetch": _t_fetch, "t_embed": _t_embed,
                            "t_head": round(_t.perf_counter() - _h0, 4)},
                # S2-k2 — `reused_base` says the encoder was skipped; when it was NOT (a genuine transient
                # embedding), the base vector is handed up so the concept layer can PERSIST it once, for
                # the next head to reuse. A DEGRADED (mock) base vector is still deterministic per item, so
                # it is cached too — the base sha8 the cache is keyed on distinguishes a mock-model reading
                # from a real one, so a later real embedding is never served the mock. Never inlined into
                # `features` (that would stamp the head's sha8, not the base's).
                "reused_base": reused_base,
                "base_vector": (None if reused_base else [round(float(x), 6) for x in vec]),
                "base_space": str(self.config.get("base_space") or "mobilenet")}


# ══ AUDIO — a second machine sense over the SAME run/observation/analysis machinery ═════════════
# The multi-axis principle extends past vision: audio observers produce the same bounded feature_vector
# the spaces/pca/cluster/neighbors/crossobs analysis consumes — modality-agnostic. Only the resolver
# differs (waveform, not pixels). Degradation-first ladder: librosa (MFCC/chroma/tempo) → a NumPy-FFT
# floor (spectral stats, no heavy dep) → a deterministic mock.
#
# ⚠️ AUDIO-BINARY PRINCIPLE — identical to images: the audio binary is NEVER stored. The corpus keeps
# only a REFERENCE (an audio_ref / a source_item locator URL); a clip is fetched TRANSIENTLY (bounded
# ≤ 30 s, mono, 22 050 Hz), analysed one at a time in RAM, and the fetched bytes are discarded (any temp
# file is deleted in `finally`). Only the derived features / embeddings — never the waveform — are
# persisted. The viewer resolves the URL per-play, never persisting it (same contract as image media).
_AUDIO_SR = 22050
_AUDIO_MAX_S = 30.0


def _resolve_audio_array(locator: str):
    """Resolve an audio locator (URL or local path) → (mono float32 waveform, sample_rate), or
    (None, None). librosa preferred (installs on demand, gated); soundfile is the floor. One clip at a
    time, bounded to _AUDIO_MAX_S — the binary is never persisted."""
    n = _np()
    if n is None or not locator:
        return None, None
    path = locator
    _tmp = None
    try:
        if str(locator).lower().startswith(("http://", "https://")):
            import urllib.request, tempfile
            if os.environ.get("AKASHA_SKIP_AUTOINSTALL"):
                pass  # SKIP still allows a bounded fetch of the analysed clip (no install), so leave as-is
            req = urllib.request.Request(locator, headers={"User-Agent": "AkashaVision/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                blob = resp.read()
            ext = os.path.splitext(str(locator).split("?")[0])[1] or ".wav"
            _tmp = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
            _tmp.write(blob); _tmp.flush(); _tmp.close()
            path = _tmp.name
        y = sr = None
        if _ensure_pkg("librosa", "librosa", timeout=1200):
            try:
                import librosa
                y, sr = librosa.load(path, sr=_AUDIO_SR, mono=True, duration=_AUDIO_MAX_S)
            except Exception:
                y = None
        if y is None and _ensure_pkg("soundfile", "soundfile"):
            try:
                import soundfile as sf
                y, sr = sf.read(path, dtype="float32")
                if getattr(y, "ndim", 1) > 1:
                    y = y.mean(axis=1)
                if sr and len(y) > int(sr * _AUDIO_MAX_S):
                    y = y[: int(sr * _AUDIO_MAX_S)]
            except Exception:
                y = None
        if y is None:
            return None, None
        return n.asarray(y, dtype="float32"), int(sr or _AUDIO_SR)
    except Exception:
        return None, None
    finally:
        if _tmp is not None:
            try:
                os.unlink(_tmp.name)
            except Exception:
                pass


class AudioFeatureObserver(FeatureObserver):
    """Base for an audio measurement observer: same feature_vector contract as the image feature
    observers (so the corpus analysis — spaces/pca/cluster/neighbours/crossobs — is shared unchanged),
    but resolves a waveform instead of pixels. Degradation-first: no audio/lib → a mock vector of the
    right shape. Values only, never a curatorial label (§7/§22)."""
    kind = "feature"
    modality = "audio"

    def _measure_audio(self, y, sr) -> Dict[str, Any]:
        raise NotImplementedError

    def observe(self, image_ref: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        loc = str((image_ref or {}).get("locator", ""))
        y, sr = _resolve_audio_array(loc)
        if y is None or getattr(y, "size", 0) == 0:
            vec = _mock_vector(len(self.vector_keys) or _EMBED_DIM, self.family, loc)
            feats = {"feature_space": self.space, "feature_vector": vec, "degraded": True}
            return {"status": "success", "detections": [], "features": feats,
                    "feature_vector": vec, "feature_space": self.space, "degraded": True}
        try:
            feats = self._measure_audio(y, sr)
        except Exception as exc:
            vec = _mock_vector(len(self.vector_keys) or _EMBED_DIM, self.family, loc)
            return {"status": "success", "detections": [],
                    "features": {"feature_space": self.space, "feature_vector": vec, "degraded": True,
                                 "measure_error": str(exc)[:120]},
                    "feature_vector": vec, "feature_space": self.space, "degraded": True}
        vec = feats.get("feature_vector") or [feats.get(k, 0.0) for k in self.vector_keys]
        feats["feature_space"] = self.space
        feats["feature_vector"] = [round(float(x), 5) for x in vec]
        return {"status": "success", "detections": [], "features": feats,
                "feature_vector": feats["feature_vector"], "feature_space": self.space}


class SpectralObserver(AudioFeatureObserver):
    """Spectral + energy statistics — the reliable NumPy-FFT floor (no librosa needed): RMS energy,
    zero-crossing rate, spectral centroid/bandwidth/rolloff/flatness, duration, peak. Answers 'what does
    the signal measure like?', never 'what is said/played?'."""
    family = "spectral"; model_name = "spectral-stats"; variant = "v1"; framework = "numpy"; space = "spectral"
    vector_keys = ["rms", "zcr", "centroid", "bandwidth", "rolloff", "flatness", "duration", "peak"]

    def _measure_audio(self, y, sr) -> Dict[str, Any]:
        n = _np()
        y = n.asarray(y, dtype="float32")
        rms = float(n.sqrt(n.mean(y * y) + 1e-12))
        zcr = float(n.mean((n.abs(n.diff(n.sign(y))) > 0).astype("float32"))) if y.size > 1 else 0.0
        w = y * n.hanning(len(y)) if y.size > 1 else y
        Y = n.abs(n.fft.rfft(w))
        freqs = n.fft.rfftfreq(len(y), 1.0 / sr)
        ysum = float(Y.sum()) + 1e-9
        centroid = float((freqs * Y).sum() / ysum)
        bandwidth = float((((freqs - centroid) ** 2 * Y).sum() / ysum) ** 0.5)
        cum = n.cumsum(Y)
        rolloff = float(freqs[min(int(n.searchsorted(cum, 0.85 * cum[-1])), len(freqs) - 1)]) if cum[-1] > 0 else 0.0
        flatness = float(n.exp(n.log(Y + 1e-9).mean()) / (Y.mean() + 1e-9))
        duration = float(len(y) / sr)
        nyq = sr / 2.0
        vec = [min(1.0, rms * 3), zcr, min(1.0, centroid / nyq), min(1.0, bandwidth / nyq),
               min(1.0, rolloff / nyq), min(1.0, flatness), min(1.0, duration / _AUDIO_MAX_S),
               min(1.0, float(n.abs(y).max()))]
        return {"feature_vector": vec, "rms": round(rms, 5), "zero_crossing_rate": round(zcr, 4),
                "spectral_centroid_hz": round(centroid, 1), "spectral_bandwidth_hz": round(bandwidth, 1),
                "spectral_rolloff_hz": round(rolloff, 1), "spectral_flatness": round(flatness, 4),
                "duration_s": round(duration, 2)}


class _LibrosaAudioObserver(AudioFeatureObserver):
    """Shared librosa-backed observer: computes a per-frame feature matrix, stores its per-dimension
    MEAN as the bounded vector. librosa installs on demand (gated); absent → mock (degradation-first)."""
    _n_dims = 13

    def _feature_matrix(self, librosa, y, sr):
        raise NotImplementedError

    def _measure_audio(self, y, sr) -> Dict[str, Any]:
        if not _ensure_pkg("librosa", "librosa", timeout=1200):
            raise RuntimeError("librosa unavailable")
        n = _np()
        try:
            from lib.akasha.api.process import native_load
            _ctx = native_load("vlab.observer:%s" % self.observer_id)
        except Exception:
            import contextlib
            _ctx = contextlib.nullcontext()
        with _ctx:
            import librosa
            mat = self._feature_matrix(librosa, n.asarray(y, dtype="float32"), sr)
        means = n.asarray(mat, dtype="float32").mean(axis=1)
        v = means / (float(n.abs(means).max()) or 1.0)
        vec = [float(x) for x in v[: self._n_dims]]
        while len(vec) < self._n_dims:
            vec.append(0.0)
        return {"feature_vector": vec, "dims": len(vec),
                **{self.vector_keys[i]: round(vec[i], 4) for i in range(min(len(vec), len(self.vector_keys)))}}


class MFCCObserver(_LibrosaAudioObserver):
    """Timbre — MFCC means (librosa). The classic 'what does it sound like' descriptor."""
    family = "mfcc"; model_name = "mfcc"; variant = "v1"; framework = "librosa"; space = "mfcc"
    _n_dims = 13
    vector_keys = ["mfcc%d" % i for i in range(13)]

    def _feature_matrix(self, librosa, y, sr):
        return librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)


class ChromaObserver(_LibrosaAudioObserver):
    """Harmony — 12-bin chroma means (librosa): pitch-class energy, the tonal fingerprint."""
    family = "chroma"; model_name = "chroma"; variant = "v1"; framework = "librosa"; space = "chroma"
    _n_dims = 12
    vector_keys = ["chroma%d" % i for i in range(12)]

    def _feature_matrix(self, librosa, y, sr):
        return librosa.feature.chroma_stft(y=y, sr=sr)


class RhythmObserver(AudioFeatureObserver):
    """Rhythm — tempo + onset/beat statistics (librosa). Degradation-first mock when librosa absent."""
    family = "rhythm"; model_name = "rhythm"; variant = "v1"; framework = "librosa"; space = "rhythm"
    vector_keys = ["tempo", "onset_rate", "onset_strength_mean", "onset_strength_var",
                   "beat_count", "pulse_clarity"]

    def _measure_audio(self, y, sr) -> Dict[str, Any]:
        if not _ensure_pkg("librosa", "librosa", timeout=1200):
            raise RuntimeError("librosa unavailable")
        n = _np()
        import librosa
        y = n.asarray(y, dtype="float32")
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        tempo, beats = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
        tempo = float(n.atleast_1d(tempo)[0])
        dur = float(len(y) / sr) or 1.0
        onsets = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr)
        vec = [min(1.0, tempo / 240.0), min(1.0, len(onsets) / dur / 10.0),
               min(1.0, float(onset_env.mean())), min(1.0, float(onset_env.var())),
               min(1.0, len(beats) / dur / 5.0), min(1.0, float(onset_env.max() / (onset_env.mean() + 1e-9)) / 10.0)]
        return {"feature_vector": vec, "tempo_bpm": round(tempo, 1), "onsets": int(len(onsets)),
                "beats": int(len(beats)), "duration_s": round(dur, 2)}


# ── the "learned ears": pretrained audio models, each a DIFFERENT world-view — all degradation-first ──
# librosa (above) measures the sound itself; these three are models trained on a world of sound:
#   YAMNet  — Google AudioSet (general sounds), TFLite on the ai-edge-litert ladder already here;
#   PANNs   — a DIFFERENT architecture on the same general world (CNN14, torch);
#   BirdNET — the ornithological world (bird species), TFLite via birdnetlib.
# Each produces the shared feature_vector (a bounded embedding / score fingerprint) so the corpus
# analysis is unchanged, PLUS named labels/detections. A missing model/lib → a mock vector (§18).
def _resample_mono(y, sr, target_sr):
    """Resample a mono waveform to target_sr — librosa if present, else a bounded linear interp floor."""
    n = _np()
    if sr == target_sr:
        return n.asarray(y, dtype="float32")
    if _ensure_pkg("librosa", "librosa"):
        try:
            import librosa
            return librosa.resample(n.asarray(y, dtype="float32"), orig_sr=sr, target_sr=target_sr)
        except Exception:
            pass
    m = int(len(y) * target_sr / float(sr or target_sr))
    if m <= 1:
        return n.asarray(y, dtype="float32")
    xp = n.linspace(0.0, 1.0, num=len(y))
    xq = n.linspace(0.0, 1.0, num=m)
    return n.interp(xq, xp, n.asarray(y, dtype="float32")).astype("float32")


class YAMNetObserver(AudioFeatureObserver):
    """YAMNet (Google AudioSet, 521 general-sound classes) on the LiteRT ladder that already runs on
    the cell. Emits a bounded embedding as the feature_vector (the 'general-audio' space) + the top
    AudioSet labels. 16 kHz mono. Model + class map fetched on demand (gated). Degradation-first."""
    family = "yamnet"; model_name = "yamnet"; variant = "audioset"; framework = "litert"; space = "yamnet"
    vector_keys = ["e%d" % i for i in range(_EMBED_DIM)]
    _MODEL = ("https://storage.googleapis.com/mediapipe-models/audio_classifier/yamnet/"
              "float32/latest/yamnet.tflite")

    def __init__(self, observer_id, config=None):
        super().__init__(observer_id, config)
        self._itp = None; self._io = None

    def _load(self):
        if self._itp is not None:
            return self._itp or None
        try:
            from lib.akasha.api.vision import resolve_backend as _resolve_backend
            backend = _resolve_backend()
            if backend is None:
                self._itp = False; return None
            mdir = _vlab_models_dir()
            mp = os.path.join(mdir, "yamnet.tflite")
            if not os.path.exists(mp) and not _fetch_model(self._MODEL, mp):
                self._itp = False; return None
            name, Interpreter = backend
            from lib.akasha.api.process import native_load
            with native_load("vlab.observer:%s" % self.observer_id):
                itp = Interpreter(model_path=mp); itp.allocate_tensors()
            self._itp = itp; self._io = (itp.get_input_details(), itp.get_output_details())
        except Exception as exc:
            logger.warning("[vlab] yamnet load failed (non-fatal): %s", exc)
            self._itp = False
        return self._itp or None

    def _measure_audio(self, y, sr):
        itp = self._load()
        if itp is None:
            raise RuntimeError("yamnet unavailable")
        n = _np()
        w = _resample_mono(y, sr, 16000).astype("float32")
        inp, outp = self._io
        try:                                                    # dynamic-length input if the model allows
            itp.resize_tensor_input(inp[0]["index"], [len(w)]); itp.allocate_tensors()
        except Exception:
            need = int(inp[0]["shape"][-1]) if len(inp[0]["shape"]) else len(w)
            w = (w[:need] if len(w) >= need else n.pad(w, (0, need - len(w))))
        itp.set_tensor(inp[0]["index"], w if len(inp[0]["shape"]) == 1 else w.reshape(inp[0]["shape"]))
        itp.invoke()
        outs = [itp.get_tensor(o["index"]) for o in outp]
        scores = next((o for o in outs if o.ndim >= 1 and o.shape[-1] in (521, 520)), outs[0])
        emb = next((o for o in outs if o.ndim >= 1 and o.shape[-1] in (1024, 2048)), None)
        sc = n.asarray(scores, dtype="float32")
        sc = sc.mean(axis=0) if sc.ndim > 1 else sc
        if emb is not None:
            e = n.asarray(emb, dtype="float32"); e = e.mean(axis=0) if e.ndim > 1 else e
            nrm = float((e * e).sum() ** 0.5) or 1.0
            vec = (e[:_EMBED_DIM] / nrm).tolist()
        else:
            vec = (sc[:_EMBED_DIM] / (float(sc.max()) or 1.0)).tolist()
        while len(vec) < _EMBED_DIM:
            vec.append(0.0)
        top = n.argsort(sc)[::-1][:5]
        return {"feature_vector": vec, "top_classes": [int(i) for i in top],
                "top_score": round(float(sc[int(top[0])]), 4)}


class PANNsObserver(AudioFeatureObserver):
    """PANNs (CNN14, AudioSet) — a DIFFERENT architecture on the same general-audio world (torch).
    Emits the model embedding as the feature_vector (the 'panns' space) + top AudioSet tags. Heavy
    (torch); degradation-first — a cell without a torch wheel just gets a mock vector."""
    family = "panns"; model_name = "cnn14"; variant = "audioset"; framework = "torch"; space = "panns"
    vector_keys = ["e%d" % i for i in range(_EMBED_DIM)]

    def __init__(self, observer_id, config=None):
        super().__init__(observer_id, config)
        self._at = None

    def _model(self):
        if self._at is not None:
            return self._at or None
        if not _ensure_pkg("panns_inference", "panns_inference", timeout=1800):
            self._at = False; return None
        try:
            from lib.akasha.api.process import native_load
            with native_load("vlab.observer:%s" % self.observer_id):
                from panns_inference import AudioTagging
                self._at = AudioTagging(checkpoint_path=None, device="cpu")
        except Exception as exc:
            logger.warning("[vlab] panns load failed (non-fatal): %s", exc)
            self._at = False
        return self._at or None

    def _measure_audio(self, y, sr):
        at = self._model()
        if at is None:
            raise RuntimeError("panns unavailable")
        n = _np()
        w = _resample_mono(y, sr, 32000).astype("float32")[None, :]   # PANNs expects 32 kHz
        clipwise, emb = at.inference(w)
        e = n.asarray(emb, dtype="float32").reshape(-1)
        nrm = float((e * e).sum() ** 0.5) or 1.0
        vec = (e[:_EMBED_DIM] / nrm).tolist()
        while len(vec) < _EMBED_DIM:
            vec.append(0.0)
        cw = n.asarray(clipwise, dtype="float32").reshape(-1)
        top = n.argsort(cw)[::-1][:5]
        return {"feature_vector": vec, "top_tags": [int(i) for i in top], "top_score": round(float(cw[int(top[0])]), 4)}


class BirdNETObserver(AudioFeatureObserver):
    """BirdNET (the ornithological world — bird species) via birdnetlib (TFLite). Emits bird-species
    DETECTIONS (common/scientific name @ confidence) + a bounded score fingerprint as the feature_vector
    (the 'birdnet' space). Needs a real audio file on disk (writes the clip to a temp wav). Degradation-
    first — no birdnetlib/model → a mock vector."""
    family = "birdnet"; model_name = "birdnet"; variant = "analyzer"; framework = "birdnetlib"; space = "birdnet"
    vector_keys = ["b%d" % i for i in range(8)]

    def __init__(self, observer_id, config=None):
        super().__init__(observer_id, config)
        self._analyzer = None

    def _get_analyzer(self):
        if self._analyzer is not None:
            return self._analyzer or None
        if not _ensure_pkg("birdnetlib", "birdnetlib", timeout=1800):
            self._analyzer = False; return None
        try:
            from lib.akasha.api.process import native_load
            with native_load("vlab.observer:%s" % self.observer_id):
                from birdnetlib.analyzer import Analyzer
                self._analyzer = Analyzer()
        except Exception as exc:
            logger.warning("[vlab] birdnet load failed (non-fatal): %s", exc)
            self._analyzer = False
        return self._analyzer or None

    def observe(self, image_ref, config=None):
        loc = str((image_ref or {}).get("locator", ""))
        y, sr = _resolve_audio_array(loc)
        an = self._get_analyzer() if y is not None else None
        if y is None or an is None:
            vec = _mock_vector(len(self.vector_keys), self.family, loc)
            return {"status": "success", "detections": [],
                    "features": {"feature_space": self.space, "feature_vector": vec, "degraded": True},
                    "feature_vector": vec, "feature_space": self.space, "degraded": True}
        # AUDIO-BINARY PRINCIPLE (mirrors images): the clip is NEVER stored. birdnetlib needs a file
        # path, so the in-memory waveform is written to a TEMP wav for the single analysis and deleted
        # immediately in `finally` — the corpus keeps only the referenced URL + the detections/features.
        _tmp = None
        try:
            import tempfile
            from birdnetlib import Recording
            import soundfile as sf
            _tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            sf.write(_tmp.name, _np().asarray(y, dtype="float32"), int(sr)); _tmp.close()
            rec = Recording(an, _tmp.name, min_conf=0.25)
            rec.analyze()
            dets = [{"class": dd.get("common_name") or dd.get("scientific_name"),
                     "confidence": round(float(dd.get("confidence", 0.0)), 3),
                     "scientific_name": dd.get("scientific_name")} for dd in (rec.detections or [])][:20]
        except Exception as exc:
            vec = _mock_vector(len(self.vector_keys), self.family, loc)
            return {"status": "success", "detections": [],
                    "features": {"feature_space": self.space, "feature_vector": vec, "degraded": True,
                                 "measure_error": str(exc)[:120]},
                    "feature_vector": vec, "feature_space": self.space, "degraded": True}
        finally:
            if _tmp is not None:
                try:
                    os.unlink(_tmp.name)                      # the clip is never kept — only the URL + features
                except Exception:
                    pass
        n = _np()
        confs = [d["confidence"] for d in dets] or [0.0]
        buckets = [0.0] * 6
        for d in dets:
            b = (hash(str(d.get("class", ""))) & 0x7fffffff) % 6
            buckets[b] += d["confidence"]
        bs = sum(buckets) or 1.0
        vec = [min(1.0, len(dets) / 5.0), max(confs)] + [x / bs for x in buckets]
        feats = {"feature_space": self.space, "feature_vector": [round(x, 5) for x in vec],
                 "species": len(dets), "top_species": dets[0]["class"] if dets else None,
                 "top_confidence": max(confs)}
        return {"status": "success", "detections": dets, "features": feats,
                "feature_vector": feats["feature_vector"], "feature_space": self.space}


def _default_observers() -> Dict[str, VisionObserver]:
    """The Phase-1 observer roster (bounded population, R3). Construction is cheap — no model is
    loaded until the first `observe`, and then once, reused across the whole run. v0.2 adds the
    lightweight multi-axis observers (color / geometry / texture) + two global embedding encoders;
    YOLOv8/v10 stay mock object observers until weights are supplied."""
    return {
        "color": ColorObserver("color"),
        "geometry": GeometryObserver("geometry"),
        "texture": TextureObserver("texture"),
        "opencv": CVObserver("opencv"),
        "litert": LiteRTFeatureObserver("litert"),
        "litert_detect": LiteRTDetectObserver("litert_detect"),
        "cascade": CascadeObserver("cascade"),
        "cvdnn_face": CVDnnFaceObserver("cvdnn_face"),
        # ── audio machine senses (same feature-vector contract; librosa/numpy, degradation-first) ──
        "spectral": SpectralObserver("spectral"),
        "mfcc": MFCCObserver("mfcc"),
        "chroma": ChromaObserver("chroma"),
        "rhythm": RhythmObserver("rhythm"),
        # the learned ears (pretrained audio models; degradation-first)
        "yamnet": YAMNetObserver("yamnet"),
        "panns": PANNsObserver("panns"),
        "birdnet": BirdNETObserver("birdnet"),
        # `mobilenet` is now the BUNDLED LiteRT embedder (vision-deps-bundle-order §1.2 — no TF, no
        # runtime pip); the heavy Keras encoder stays reachable as `mobilenet_keras` for dev machines.
        "mobilenet": LiteRTEmbeddingObserver("mobilenet", family="mobilenet", space="mobilenet"),
        "mobilenet_keras": EmbeddingObserver("mobilenet_keras", keras_app="MobileNetV3Small",
                                             family="mobilenet", space="mobilenet"),
        "efficientnet": EmbeddingObserver("efficientnet", keras_app="EfficientNetB0",
                                          family="efficientnet", space="efficientnet"),
        "tf": TFObserver("tf"),
        "yolov8": YoloObserver("yolov8", version="8"),
        "yolov10": YoloObserver("yolov10", version="10"),
        "mock": MockVisionObserver("mock"),
    }


# Feature-space registry (§13): a selectable analysis space → the observer whose feature_vector
# defines it. "lightweight" is the derived Color+Geometry+Texture combination (§10), assembled on
# read from the three observers (the originating observations are never erased).
_FEATURE_SPACES = {
    "color": ["color"], "geometry": ["geometry"], "texture": ["texture"],
    "opencv": ["opencv"], "litert": ["litert"],
    "objdet": ["litert_detect"], "cascade": ["cascade"], "face": ["cvdnn_face"],
    "mobilenet": ["mobilenet"], "efficientnet": ["efficientnet"],
    "lightweight": ["color", "geometry", "texture"],
    # audio spaces (modality=audio) — same analysis machinery, different sense
    "spectral": ["spectral"], "mfcc": ["mfcc"], "chroma": ["chroma"], "rhythm": ["rhythm"],
    "yamnet": ["yamnet"], "panns": ["panns"], "birdnet": ["birdnet"],
}
# each feature space's modality (image | audio) — lets the Source Viewer separate Image/Audio tabs.
_SPACE_MODALITY = {s: "audio" for s in ("spectral", "mfcc", "chroma", "rhythm", "yamnet", "panns", "birdnet")}


def _roster_rows(observers: Dict[str, VisionObserver]) -> List[Dict[str, str]]:
    """VPS-vision-coverage §2.5 — one readiness row per IMAGE observer (the audio senses + the `mock`
    pseudo-observer are excluded): {observer, framework, status, reason, model_file, model_sha8}.
    Side-effect-free (each observer's readiness() probes deps + bundled files only)."""
    rows: List[Dict[str, str]] = []
    for oid, obs in observers.items():
        if oid == "mock" or getattr(obs, "modality", "image") != "image":
            continue
        try:
            r = obs.readiness()
        except Exception as exc:                                 # a broken probe never breaks the roster
            r = {"status": "absent", "reason": "probe error: %s" % str(exc)[:80],
                 "model_file": "", "model_sha8": ""}
        rows.append({"observer": oid, "framework": getattr(obs, "framework", "none"),
                     "status": str(r.get("status", "ok")), "reason": str(r.get("reason", "")),
                     "model_file": str(r.get("model_file", "")), "model_sha8": str(r.get("model_sha8", ""))})
    return rows


def vision_roster() -> List[Dict[str, str]]:
    """The default (session-less) image-observer roster table — used by the `[vision] roster` boot
    line. The `vlab.roster` op uses the LIVE roster (which also carries any promoted learned heads)."""
    return _roster_rows(_default_observers())


def vision_roster_line(rows: Optional[List[Dict[str, str]]] = None) -> str:
    """The compact one-line `[vision] roster …` boot log (§2.5): `<observer>=<status>(<reason>)`."""
    if rows is None:
        rows = vision_roster()
    parts = []
    for row in rows:
        tag = row["status"]
        if row.get("reason"):
            tag = "%s(%s)" % (tag, row["reason"])
        parts.append("%s=%s" % (row["observer"], tag))
    return "[vision] roster " + " ".join(parts)


# ══ Concept model ══════════════════════════════════════════════════════════════════════════════

class VisionLabConcept(UniversalConcept):
    """`vlab.*` — the Phase-1 machine-observation surface (see module docstring + spec)."""

    CONCEPT_PREFIX = "vlab"
    CONCEPT_LABEL = "Visual Curation Laboratory (Phase 1 — machine observation)"

    # `on_bench` (optional) on the media precompute's steps — the bench the call is made ON, the place the
    # gate is asked about (platform 2026-10-03, decision 3: a target per STEP, never a class `gate_target`,
    # which would change the gate of every vlab.* caller, PLANTS included). Absent → the gate is exactly what
    # it was. It is deliberately NOT `bench`: `run.new bench=` stamps the run's own coordinate, and a
    # precompute run is minted bench="" (purpose=precompute) — naming the place must not rename the run.
    CONCEPT_METHODS = {
        "observers":    {"op": "op_observers",    "action": "read"},
        "roster":       {"op": "op_roster",       "action": "read"},
        "observer.reg": {"op": "op_observer_reg", "action": "record"},
        "source.scan":  {"op": "op_source_scan",  "action": "record"},
        "source.add":   {"op": "op_source_add",   "action": "record"},
        "observe":      {"op": "op_observe",      "action": "record"},
        "run.new":      {"op": "op_run_new",      "action": "record", "target": "on_bench", "target_kind": "bench"},
        "run.execute":  {"op": "op_run_execute",  "action": "record", "target": "on_bench", "target_kind": "bench"},
        "run.seal":     {"op": "op_run_seal",     "action": "record", "target": "on_bench", "target_kind": "bench"},
        "run.info":     {"op": "op_run_info",     "action": "read"},
        "reindex":      {"op": "op_reindex",      "action": "record"},
        "runs":         {"op": "op_runs",         "action": "read"},
        "item":         {"op": "op_item",         "action": "read"},
        "item.versions": {"op": "op_item_versions", "action": "read"},
        "layer.backfill": {"op": "op_layer_backfill", "action": "record"},
        "compare":      {"op": "op_compare",      "action": "record"},
        "set.derive":   {"op": "op_set_derive",   "action": "record"},
        "cluster":      {"op": "op_cluster",      "action": "record", "target": "on_bench", "target_kind": "bench"},
        "project":      {"op": "op_project",      "action": "read"},
        "matrix":       {"op": "op_matrix",       "action": "read"},
        "observation":  {"op": "op_observation",  "action": "read"},
        "detections":   {"op": "op_detections",   "action": "read"},
        "features":     {"op": "op_features",     "action": "read"},
        # ── v0.2 lightweight multi-axis: analysis over selectable feature SPACES ──
        "spaces":       {"op": "op_spaces",       "action": "read"},
        "combine":      {"op": "op_combine",      "action": "record", "target": "on_bench", "target_kind": "bench"},
        "pca":          {"op": "op_pca",          "action": "record", "target": "on_bench", "target_kind": "bench"},
        "neighbors":    {"op": "op_neighbors",    "action": "read"},
        "views":        {"op": "op_views",        "action": "read"},
        "crossobs":     {"op": "op_crossobs",     "action": "read"},
    }

    def __init__(self, session, namespace: Optional[str] = None):
        super().__init__(session, namespace=namespace)
        self._observers: Optional[Dict[str, VisionObserver]] = None

    # ── observer roster ──────────────────────────────────────────────────────────
    def _roster(self) -> Dict[str, VisionObserver]:
        if self._observers is None:
            obs = _default_observers()
            # Learned heads promoted by a learning bench (learning.promote) join the roster so their
            # predictions are observable exactly like the reference observers. The records live in the
            # shared nucleus; a fresh instance rediscovers them here (no runtime-injection state to lose).
            try:
                for k in self._members(LEARNED_OBSERVERS_SET):
                    a = self._alias(k)
                    m = self._meta(a) if a else {}
                    oid = m.get("observer")
                    if m.get("concept") == "vlab_learned" and oid:
                        obs[oid] = LearnedHeadObserver(oid, config={
                            "weights_path": m.get("weights_path"), "base_space": m.get("base_space"),
                            "classes": m.get("classes") or [], "model": m.get("model"),
                            # D2-M — the model fingerprint + provenance travel on the observer config so
                            # a promoted head stamps a real model_sha8 without a cross-space lookup.
                            "weights_sha256": m.get("weights_sha256"), "engine": m.get("engine"),
                            "accuracy": m.get("accuracy"), "feature_run": m.get("feature_run")})
            except Exception as exc:
                logger.debug("[vlab] learned-observer roster load skipped: %s", exc)
            self._observers = obs
        return self._observers

    def _observer(self, observer_id: str) -> VisionObserver:
        obs = self._roster().get(observer_id)
        if obs is None:
            raise ValueError("unknown observer '%s' (known: %s)"
                             % (observer_id, ", ".join(sorted(self._roster()))))
        return obs

    # ── scoped writers (public → nucleus/universal; local → private owner scope) ──
    def _scopes_for(self, visibility: str) -> List[str]:
        if visibility == "local":
            c = self._author()
            return ["owner:user_%s" % c, "view:user_%s" % c]
        return [UNIVERSAL]

    def _mint(self, alias: str, content: str, meta: Dict[str, Any], visibility: str = "public") -> str:
        """Idempotent-by-alias atom write, routed by visibility. Public atoms go universal
        (guest-readable, nucleus on a real deployment); local atoms stay in the operator's private
        scope and are NEVER guest-visible (§8)."""
        if visibility == "local":
            existing = self._key(alias)
            if existing:
                return existing
            key = self.cortex.put_chunk(content=content, meta=dict(meta or {}),
                                        author=self._author(), scopes=self._scopes_for("local"))
            self.cortex.core.put_alias(key, alias)
            return key
        return self._mk(alias, content, meta)

    def _link_v(self, src_alias: str, dst_alias: str, rel: str, visibility: str = "public") -> None:
        if visibility == "local":
            sk = self._key(src_alias)
            if sk:
                self.cortex.put_link(sk, self._key(dst_alias) or dst_alias, rel, author=self._author())
        else:
            self._link(src_alias, dst_alias, rel)

    def _addset_v(self, name: str, key: str, visibility: str = "public") -> None:
        if visibility == "local":
            self.cortex.add_to_set(name, key)
        else:
            self._add_to_set(name, key)

    # ══ Sources ══════════════════════════════════════════════════════════════════

    def op_source_add(self, pool: str, object_id: str, image: str, scheme: str = "remote",
                      title: str = "", provider: str = "", **fields) -> Dict[str, Any]:
        """[vlab.source.add] Register ONE artwork Source Atom (image_ref = {scheme, locator=image}).
        The image BINARY is never stored — only the reference + metadata. Used by the CMA off-line
        adapter (scheme=remote) and available for a single local file (scheme=local)."""
        visibility = "local" if scheme == "local" else "public"
        prov = provider or ("cma" if scheme == "remote" else "local")
        alias = "source:artwork:%s:%s" % (prov, slug(object_id))
        meta = {
            "concept": "source_artwork", "provider": prov, "provider_object_id": object_id,
            # A Source Atom carries a stable record id like any acquired item. Its STATUS is NOT written here:
            # the source engine is the single writer of an item's status (directive 2026-10-03 item 3) —
            # `source.item.status` moves the meta, the `source:status:<s>` Set and every pool's tally in one
            # write, so a status written around it is exactly what drifted the tally. (A LOCAL artwork is not a
            # Source-layer citizen — see below — and keeps its own mark.)
            "source_record_id": object_id,
            "title": title, "image_reference": {"scheme": scheme, "locator": image},
            "source_pool": pool, "visibility": visibility, "acquired_at": self._now_wall(),
        }
        # Only a pool the Source ENGINE knows (`source:pool:…`) has a tally the door can move. An ad hoc vlab-private
        # pool name (a scratch pool in an eval, `vc:cma:v1`) is not in the engine's domain, nor is a LOCAL
        # artwork: those keep their own mark, as before.
        engine_pool = visibility == "public" and str(pool).startswith("source:pool:")
        if not engine_pool:
            meta["status"] = "METADATA_ONLY"
        for k, v in fields.items():
            meta[k] = v
        key = self._mint(alias, "[artwork] %s" % (title or object_id), meta, visibility)
        door = None
        self._addset_v(pool, key, visibility)
        self._addset_v("set:vlab:pool:%s:members" % slug(pool), key, visibility)
        # Make the artwork a FIRST-CLASS Source-Data-Layer citizen so the Source Viewer surfaces it
        # (sources list, pools list, item browse, status) — not only the vlab-private sets. All writes
        # are idempotent and public (shared nucleus) — a PUBLIC artwork IS public source data (§ the
        # Source Data Layer principle). A local (private) scan stays in the vlab-only sets (§8).
        if visibility == "public":
            self._register_source_citizen(pool, prov, key)
            if engine_pool:
                door = self._set_status_through_the_door(pool, alias)
            else:
                self._addset_v("source:status:metadata_only", key, "public")
                door = None
        out = {"source": alias, "key": key, "pool": pool, "visibility": visibility}
        if door is not None:
            out["status"] = door               # the engine's answer: {status, was, changed}
        return out

    def _register_source_citizen(self, pool: str, prov: str, key: str) -> None:
        """Idempotently register the pool + provider source in the Source-layer global registries and
        file the artwork as a browsable source item, so the Source Viewer surfaces vlab corpora exactly
        like an acquired dataset. Mirrors source.op_acquire's registrations; never mutates the artwork."""
        # (a) the source pool atom → lists in `source:pools`, is inspectable/freezable. A safety net:
        #     only if the off-line import did not already create it via source.pool.create (which owns
        #     the pool's provenance + the source registration, so we do NOT register a second source).
        if not self._key(pool):
            self._mint(pool, "[%s] Source Pool — machine-observation corpus [OPEN]" % pool,
                       {"concept": "source_pool", "name": pool, "version": "v1",
                        "membership_rule": "machine-observation corpus", "source": "",
                        "status": "OPEN", "created_at": self._now_wall(),
                        "frozen_at": None, "at_seq": None}, "public")
            self._addset_v("source:pools", self._key(pool), "public")
        # (b) the artwork itself → browsable + counted (`source:items`, the pool's canonical members
        #     set, and the status bucket the Source Viewer filters on).
        self._addset_v("source:items", key, "public")
        self._addset_v("%s:members" % pool, key, "public")

    def _set_status_through_the_door(self, pool: str, alias: str) -> Dict[str, Any]:
        """The artwork's status is `METADATA_ONLY` (the image is a reference, never a binary) — set through the
        source engine's ONE door, `source.item.status` (`SourceDataLayer.op_item_status`), so the item meta, its
        `source:status:<s>` Set, its source's tally and every pool's `by_status` move in the same write. The door
        counts only a change it makes: had the mint already written the status it would answer `changed: false`
        and the tally would stay at 0 for this item. Its error is RETURNED (raised), never swallowed and never
        replaced by writing the status some other way. Artworks that already exist are corrected by the engine's
        own drift check (`_ensure_pool_tally(check_drift=True)` at freeze / `source.backfill`), not by a pass here."""
        from lib.akasha.api.concepts import model as _model
        return _model(self.session, "source").op_item_status(pool=pool, item=alias, status="METADATA_ONLY")

    def op_source_scan(self, dir: str, pool: str, glob: str = "", limit: str = "",
                       provider: str = "local") -> Dict[str, Any]:
        """[vlab.source.scan] Reference a LOCAL DIRECTORY of images a whole directory at a time →
        one Source Atom per image file (image_ref.scheme=local, locator=path). The generic
        local-curation capability: the SAME pool/observation pipeline as the public experiment.

        Memory discipline (R1/R4): a BOUNDED, STREAMING walk — resolves + registers ONE file at a
        time, never loading the directory's images into RAM. `limit` caps the count; the image
        binary is never read into the atom (only its path + basic metadata). Local pools are
        PRIVATE (owner scope) and are never guest-visible (§8). The named directory is permitted
        for THIS scan (the operator naming it is the permit act); it must resolve inside the
        FileIO allow-list."""
        from lib.akasha.api.files import FileIO
        ab_dir = os.path.abspath(os.path.expanduser(dir))
        fio = FileIO(extra_roots=[ab_dir])
        exts = None
        if glob:
            exts = {e if e.startswith(".") else "." + e
                    for e in (g.strip().lstrip("*").lower() for g in glob.split(",")) if e}
        exts = exts or set(_IMAGE_EXTS)
        cap = int(limit) if str(limit).strip().isdigit() else None

        n = 0
        added: List[str] = []
        # STREAM: one path at a time from the generator; O(cap) work, never O(directory).
        for path in fio.iter_dir(ab_dir, exts=exts, recursive=True):
            if cap is not None and n >= cap:
                break
            object_id = os.path.relpath(path, ab_dir)
            res = self.op_source_add(pool=pool, object_id=object_id, image=path,
                                     scheme="local", title=os.path.basename(path),
                                     provider=provider)
            added.append(res["source"])
            n += 1
        self._mint("source:pool:%s" % slug(pool),
                   "[pool] %s (local directory scan)" % pool,
                   {"concept": "source_pool", "visibility": "local", "provider": provider,
                    "root": ab_dir, "members": n, "status": "open"}, "local")
        return {"pool": pool, "scanned": n, "root": ab_dir, "visibility": "local",
                "sources": added[:50], "truncated": len(added) > 50}

    # ══ Model identity ════════════════════════════════════════════════════════════

    def op_observer_reg(self, id: str, **config) -> Dict[str, Any]:
        """[vlab.observer.reg] Mint (idempotently) the IMMUTABLE model-identity atom for an
        observer under a given config. A distinct config is a distinct identity — a new config mints
        a new atom, never overwrites (§11)."""
        obs = self._observer(id)
        if config:
            obs.config.update(config)
        return {"observer": id, "model": self._mint_model(obs)}

    def _mint_model(self, obs: VisionObserver) -> str:
        ident = obs.model_identity()
        alias = obs.model_alias()
        self._mk(alias, "[model] %s %s v%s (%s)"
                 % (ident["family"], ident["model_name"], ident["version"], ident["variant"]),
                 {"concept": "vision_model", **ident})
        return alias

    def op_observers(self, verbose: str = "") -> Dict[str, Any]:
        """[vlab.observers] List the registered observers and their immutable model identity."""
        rows = []
        for oid, obs in sorted(self._roster().items()):
            row = {"observer": oid, "family": obs.family, "kind": obs.kind,
                   "model_alias": obs.model_alias()}
            if verbose:
                row["identity"] = obs.model_identity()
            rows.append(row)
        return {"observers": rows, "count": len(rows)}

    def op_roster(self) -> Dict[str, Any]:
        """[vlab.roster] VPS-vision-coverage §2.5 — the machine-observer readiness table: per IMAGE
        observer, {observer, framework, status(ok|degraded), reason, model_file, model_sha8}. The SAME
        table the `[vision] roster` boot line prints. Side-effect-free (probes deps + bundled model
        files only — never a download or a weights load), so a guest read is safe. Uses the LIVE roster,
        so a bench-promoted learned head appears alongside the reference observers."""
        rows = _roster_rows(self._roster())
        ok = sum(1 for r in rows if r["status"] == "ok")
        return {"observers": rows, "count": len(rows), "ok": ok,
                "degraded": len(rows) - ok, "line": vision_roster_line(rows)}

    # ══ Observation ═══════════════════════════════════════════════════════════════

    def _source_meta(self, source: str) -> Dict[str, Any]:
        m = self._meta(source)
        if not m:
            raise ValueError("unknown source '%s'" % source)
        return m

    def _source_concept(self):
        sc = getattr(self, "_source_cache", None)
        if sc is None:
            from lib.akasha.api.concepts import model as _model
            sc = self._source_cache = _model(self.session, "source")
        return sc

    def _register_observation_bridge(self, obs_alias: str, source_alias: str, obs: "VisionObserver",
                                     model_alias: str, run: str, meta: Dict[str, Any],
                                     visibility: str) -> None:
        """Part D §4.2 — one source bridge event per observation (rel=observed_by), on the observation's
        OWN write path, so source.trace surfaces the reading with no scan. Best-effort: a failure never
        breaks the observation. Local observations are NOT bridged into the shared (nucleus) registry."""
        if visibility != "public":
            return
        try:
            # D2-M M4 — the observation's OWN model_sha8 (the coordinate layer's, from _obs_sha8) is the
            # authoritative version; the bridge copies it so `source.trace` never shows
            # `observer_version=null` while `family` is set. Fall back to readiness / model meta only if
            # the layer somehow lacks it (a legacy observation).
            sha8 = str(meta.get("model_sha8") or "")
            if not sha8:
                try:
                    sha8 = str((obs.readiness() or {}).get("model_sha8") or "")
                except Exception:
                    sha8 = ""
            if not sha8:
                mm = self._meta(model_alias) or {}
                sha8 = str(mm.get("weights_sha256") or mm.get("sha256") or "")[:8]
            self._source_concept().record_observation_bridge(
                observation=obs_alias, source=source_alias, observer=obs.observer_id,
                model=model_alias, run=run, model_sha8=sha8,
                degraded=bool(meta.get("degraded")),
                detection_count=int(meta.get("detection_count") or 0), cronon=meta.get("cronon"),
                family=meta.get("family"), bench=meta.get("bench"),
                wf_branch=meta.get("wf_branch"), mode=meta.get("mode"))
        except Exception as exc:
            logger.debug("[vlab] observation bridge skipped for %s: %s", obs_alias, exc)

    def _obs_alias(self, provider: str, object_id: str, observer_id: str, run: str) -> str:
        return "obs:vision:%s:%s:%s:%s" % (provider, slug(object_id), observer_id, slug(run or "r0"))

    # ── D2-M — observation coordinates (Set-as-coordinate) ─────────────────────────
    def _obs_family(self, obs: "VisionObserver", degraded: bool) -> str:
        """The NORMALIZED reading family (D2-M §1): `learned` (a promoted head that actually ran),
        `mock` (the MockObserver, or any observer that DEGRADED to the deterministic mock — no
        backend), else `sense` (a learning-free measurement / classifier / detector / embedder)."""
        fam = getattr(obs, "family", "") or ""
        if fam == "learned":
            return "mock" if degraded else "learned"    # a weightless head fell back to mock
        if fam == "mock" or degraded:
            return "mock"
        return "sense"

    def _obs_sha8(self, obs: "VisionObserver", model_alias: str) -> str:
        """sha8 of the model identity — the bundled model file (sense) or the learned weights. A
        promoted head carries its `weights_sha256` on its config (stamped at promote), so we read it
        WITHOUT a cross-space model-atom lookup (the identity atom lives in the bench's group space)."""
        sha8 = ""
        try:
            sha8 = str((obs.readiness() or {}).get("model_sha8") or "")
        except Exception:
            sha8 = ""
        if not sha8 and obs is not None:
            sha8 = str((getattr(obs, "config", None) or {}).get("weights_sha256") or "")[:8]
        if not sha8:
            mm = self._meta(model_alias) or {}
            sha8 = str(mm.get("weights_sha256") or mm.get("sha256") or "")[:8]
        return sha8 or "nomodel"

    def _run_coords(self, run: str) -> Dict[str, Any]:
        """The coordinates a run carries onto every observation it mints (D2-M §2): bench / wf_branch
        / mode / purpose, read from the run atom (a point-get — cheap, always current). A run carries the
        bench it was started on, or none — nothing is derived from where the run happens to be filed
        (the purge order: no migration path for a run minted before the coordinate layer)."""
        ralias = "vision_run:%s" % slug(run)
        m = self._meta(ralias) or {}
        bench = m.get("bench", "") or ""
        purpose = m.get("purpose", "") or ("bench" if bench else "manual")
        return {"bench": bench, "wf_branch": m.get("wf_branch", "") or "",
                "mode": m.get("mode", "execution") or "execution", "purpose": purpose}

    def _observation_layer(self, obs: "VisionObserver", model_alias: str, run: str,
                           degraded: bool, at_seq: int) -> Dict[str, Any]:
        """The D2-M §1 layer: the coordinates copied onto the observation meta AT WRITE (no lookup
        later). family / model_sha8 / observer_version / bench / wf_branch / mode / purpose / at_seq."""
        sha8 = self._obs_sha8(obs, model_alias)
        c = self._run_coords(run)
        return {"family": self._obs_family(obs, degraded), "model_sha8": sha8,
                "observer_version": sha8, "bench": c["bench"], "wf_branch": c["wf_branch"],
                "mode": c["mode"], "purpose": c["purpose"], "at_seq": at_seq, "layer_v": _LAYER_V}

    def _add_layer_sets(self, okey: str, layer: Dict[str, Any], observer_id: str,
                        visibility: str) -> None:
        """Add ONE membership per coordinate (D2-M §2), all at mint. A reading is then an intersection
        of these Sets; a coarser question is a macro over intersections, never a handler."""
        self._addset_v("set:vlab:family:%s" % slug(layer["family"]), okey, visibility)
        self._addset_v("set:vlab:observer:%s:observations" % slug(observer_id), okey, visibility)
        self._addset_v("set:vlab:model:%s:observations" % slug(layer["model_sha8"]), okey, visibility)
        self._addset_v("set:vlab:purpose:%s" % slug(layer["purpose"]), okey, visibility)
        if layer["mode"] == "thought":                   # execution is the complement (never a Set)
            self._addset_v("set:vlab:mode:thought", okey, visibility)
        b = layer["bench"]
        if b:                                             # empty bench (precompute/manual) → not added
            self._addset_v("set:wb:%s:observations" % _wb_tag(b), okey, visibility)
            if layer["wf_branch"]:
                self._addset_v("set:wb:%s:branch:%s:observations"
                               % (_wb_tag(b), slug(layer["wf_branch"])), okey, visibility)

    def op_observe(self, source: str, observer: str, run: str = "", config: str = "") -> Dict[str, Any]:
        """[vlab.observe] Run ONE observer on ONE source's image_ref → an Observation Atom (+
        Detection/Feature atoms). Success AND failure are both recorded (a failed observation
        documents what the observer could not process — §12). The Source Atom is NEVER mutated."""
        smeta = self._source_meta(source)
        visibility = smeta.get("visibility", "public")
        # Media reference, modality-general: a vlab artwork carries `image_reference`; an audio item an
        # `audio_reference`; a plain acquired/imported `source_item` carries the generic `locator`
        # ({kind, uri}). Normalize all three to {locator: <uri>} so image AND audio observers read the
        # same key — this is what lets vlab observe ANY source pool (image, audio, or acquired), not just
        # vlab.source.add artworks.
        image_ref = smeta.get("image_reference") or smeta.get("audio_reference") or {}
        if not (image_ref.get("locator") or image_ref.get("uri")):
            _loc = smeta.get("locator") or {}
            if _loc.get("uri"):
                image_ref = {"locator": _loc["uri"], "scheme": _loc.get("kind", "external")}
        obs = self._observer(observer)
        cfg = {}
        if config:
            try:
                cfg = json.loads(config)
            except Exception:
                cfg = {}
        # S2-k2 — a learned-head observe's cost is the base ENCODER, not the head. Keyed on (item,
        # base_space, base sha8): if this item already has a base-space embedding (stored by an earlier
        # head's transient embedding), hand it to the observer so it runs ONLY the head and skips
        # re-embedding; otherwise the observer embeds as before (degradation-first, unchanged) and we
        # PERSIST that transient embedding once, below, for the next head to reuse. The base observer's
        # sha8 is a cheap file hash (readiness), never an interpreter load.
        _is_learned = getattr(obs, "family", "") == "learned"
        _object_id = smeta.get("provider_object_id", source)
        _bspace = _bsha = ""
        if _is_learned:
            try:
                _bspace = str((getattr(obs, "config", None) or {}).get("base_space") or "mobilenet")
                try:
                    _bsha = str((obs._base_observer().readiness() or {}).get("model_sha8") or "")
                except Exception:
                    _bsha = ""
                if "base_vector" not in cfg:
                    _bv = self._reusable_base_vector(_object_id, _bspace, _bsha)
                    if _bv is not None:
                        cfg = dict(cfg); cfg["base_vector"] = _bv
            except Exception:
                pass
        model_alias = self._mint_model(obs)
        import time as _t
        _o0 = _t.perf_counter()
        try:
            obset = obs.observe(image_ref, cfg)
        except Exception as exc:                             # never let one image kill the run
            obset = {"status": "failed", "failure_type": "observer_exception",
                     "failure_detail": str(exc)[:200], "detections": [], "features": {}}
        _t_observe = round(_t.perf_counter() - _o0, 4)
        _w0 = _t.perf_counter()
        res = self._write_observation(source, smeta, obs, model_alias, run or "r0", obset, visibility)
        # S2-k3 — the per-observe cost split (t_fetch/t_embed/t_head from the observer + t_write here), so
        # op_run_execute can log where the time goes and prove the reuse path never touches the image.
        _tm = dict(obset.get("_timing") or {})
        _tm["t_write"] = round(_t.perf_counter() - _w0, 4)
        _tm["t_observe"] = _t_observe
        res["_timing"] = _tm
        if obset.get("reused_base"):                          # S2-k2 — surfaced to op_run_execute's tally
            res["reused_base"] = True
        elif _is_learned and obset.get("base_vector") and _bspace:
            # persist the head's transient base embedding as a base-space feature atom (stamped with the
            # BASE model sha8, not the head's) so the next head reuses it — paid once, at write time (R2).
            self._store_base_embedding(source, smeta, _bspace, _bsha, obset["base_vector"],
                                       run or "r0", visibility)
        return res

    def _store_base_embedding(self, source: str, smeta: Dict[str, Any], base_space: str,
                              base_sha8: str, vec: List[float], run: str, visibility: str) -> None:
        """S2-k2 — persist a learned-head observe's transient base embedding as a base-space
        `vision_feature` atom, keyed on (item, base_space, base sha8), so `_reusable_base_vector` finds it
        for the next head and the encoder never runs again on this item. The atom carries the BASE
        observer's identity (observer=<base_space>, model_sha8=<base sha8>), never the head's — else the
        reuse lookup would mismatch. Idempotent: content-addressed by the alias (per item, space, run)."""
        try:
            provider = smeta.get("provider", "x")
            object_id = smeta.get("provider_object_id", source)
            falias = "obs:feature:%s:%s:%s:%s" % (provider, slug(str(object_id)), slug(base_space), slug(run))
            fmeta = {"concept": "vision_feature", "observer": base_space, "run": run,
                     "feature_space": base_space, "source": source, "model_sha8": base_sha8 or None,
                     "feature_vector": [round(float(x), 6) for x in vec], "base_embedding": True}
            fkey = self._mint(falias, "[features] %s base=%s (reuse cache)" % (object_id, base_space),
                              fmeta, visibility)
            self._link_v(falias, source, "vis:observes", visibility)
            self._addset_v("set:vlab:src:%s:feat" % slug(str(object_id)), fkey, visibility)
            self._addset_v("set:vlab:feat:%s:%s" % (slug(run), slug(base_space)), fkey, visibility)
        except Exception as exc:
            logger.debug("[vlab] base-embedding cache skipped %s: %s", source, exc)

    def _write_observation(self, source: str, smeta: Dict[str, Any], obs: VisionObserver,
                           model_alias: str, run: str, obset: Dict[str, Any],
                           visibility: str) -> Dict[str, Any]:
        provider = smeta.get("provider", "x")
        object_id = smeta.get("provider_object_id", source)
        oalias = self._obs_alias(provider, object_id, obs.observer_id, run)
        status = obset.get("status", "success")
        _at_seq = self._akasha_now()
        degraded = bool(obset.get("degraded", False))
        # D2-M §1 — the coordinate LAYER, copied onto the observation meta AT WRITE (no lookup later):
        # family / model_sha8 / observer_version / bench / wf_branch / mode / purpose / at_seq.
        layer = self._observation_layer(obs, model_alias, run, degraded, _at_seq)
        meta = {"concept": "vision_observation", "observer": obs.observer_id,
                "model": model_alias, "run": run, "status": status,
                "processed_at": self._now_wall(), "cronon": _at_seq,
                "degraded": degraded,
                "detection_count": len(obset.get("detections") or []), **layer}
        # The observation's top label, stamped AT WRITE (the generic `lens.compare` reads the member's own
        # `label` / `confidence`; it derives nothing from detection Sets or feature atoms).
        _feat = obset.get("features") or {}
        _dets = [d for d in (obset.get("detections") or []) if d.get("class") is not None]
        if _feat.get("dominant_class"):
            meta["label"] = _feat.get("dominant_class")
            meta["confidence"] = _feat.get("dominant_score", _feat.get("score"))
        elif _dets:
            _top = max(_dets, key=lambda d: float(d.get("confidence") or 0))
            meta["label"], meta["confidence"] = _top.get("class"), round(float(_top.get("confidence") or 0), 4)
        if status == "failed":
            meta["failure_type"] = obset.get("failure_type", "unknown")
            meta["failure_detail"] = obset.get("failure_detail", "")
        # D2-M §4.2 — the model_sha8 is part of the observation CONTENT, so two VERSIONS of the same
        # observer on the same item are DISTINCT content-addressed atoms (the version stack); the SAME
        # (observer, model) across runs stays one atom (idempotent — the reuse/sentinel case).
        okey = self._mint(oalias, "[observation] %s by %s (%s) [m:%s]"
                          % (object_id, obs.observer_id, status, layer["model_sha8"]),
                          meta, visibility)
        self._link_v(oalias, source, "vis:observes", visibility)
        self._link_v(oalias, model_alias, "vis:observer", visibility)
        if run:
            self._link_v(oalias, "vision_run:%s" % slug(run), "vis:in_run", visibility)
        self._addset_v("set:vlab:run:%s:obs" % slug(run), okey, visibility)
        # Part D §4.1 — the observation-run membership set: "the observations of run <run>" is one
        # `s.ls set:vlab:run:<run>:observations`, so observe.diff (T7) is Set algebra (item ∩ run) via
        # `lens … within=` — not a scan. (Parallel to the feature membranes set:vlab:feat:<run>:<fam>.)
        self._addset_v("set:vlab:run:%s:observations" % slug(run), okey, visibility)
        self._addset_v("set:vlab:src:%s:obs" % slug(str(object_id)), okey, visibility)
        # D2-M §2 — one membership per coordinate (family/observer/model/wb/branch/mode/purpose).
        self._add_layer_sets(okey, layer, obs.observer_id, visibility)
        logger.debug("[vlab] mint %s family=%s bench=%s branch=%s run=%s model=%s",
                     oalias, layer["family"], layer["bench"] or "-", layer["wf_branch"] or "-",
                     run, layer["model_sha8"])
        # Part D §4.2 — register ONE source bridge event in the same write, so source.trace surfaces this
        # observation under `interpretations` without a scan (best-effort; never fails the observation).
        self._register_observation_bridge(oalias, source, obs, model_alias, run, meta, visibility)

        # Detections (§13) — normalized bbox canonical.
        det_set = "set:vlab:det:%s" % slug(oalias)
        for i, d in enumerate(obset.get("detections") or []):
            dalias = "obs:detection:%s:%s:%s:%03d" % (provider, slug(object_id), obs.observer_id, i)
            dkey = self._mint(dalias, "[detection] %s @ %.2f" % (d.get("class"), d.get("confidence", 0)),
                              {"concept": "vision_detection", "class": d.get("class"),
                               "confidence": d.get("confidence"), "bbox_x": d.get("bbox_x"),
                               "bbox_y": d.get("bbox_y"), "bbox_width": d.get("bbox_width"),
                               "bbox_height": d.get("bbox_height"), "observer": obs.observer_id,
                               "run": run}, visibility)
            self._link_v(dalias, oalias, "sys:part_of", visibility)
            self._link_v(dalias, source, "vis:observes", visibility)
            self._addset_v(det_set, dkey, visibility)

        # Global / lightweight feature observation (§5/§7/§8/§9/§14). Large embeddings are stored
        # BOUNDED (≤ _EMBED_DIM) — the full encoder output stays a reference, never inlined. The
        # feature_vector + feature_space travel with the atom so the Analysis layer (PCA / cluster /
        # neighbour) can read a space's matrix by membrane, O(K).
        feats = obset.get("features") or {}
        space = obset.get("feature_space") or feats.get("feature_space")
        if feats:
            falias = "obs:feature:%s:%s:%s:%s" % (provider, slug(object_id), obs.observer_id, slug(run))
            fmeta = {"concept": "vision_feature", "observer": obs.observer_id, "run": run,
                     "feature_space": space, "source": source,
                     # S2-k2 — the base model's sha8 travels on the feature atom so a later learned-head
                     # observe can reuse THIS embedding keyed on (item, base_space, base sha8).
                     "model_sha8": layer.get("model_sha8")}
            fmeta.update({k: v for k, v in feats.items() if k != "embedding"})
            fkey = self._mint(falias, "[features] %s by %s" % (object_id, obs.observer_id), fmeta, visibility)
            self._link_v(falias, source, "vis:observes", visibility)
            self._addset_v("set:vlab:src:%s:feat" % slug(str(object_id)), fkey, visibility)
            if space:                                            # per-(run, space) feature membrane
                self._addset_v("set:vlab:feat:%s:%s" % (slug(run), slug(space)), fkey, visibility)

        return {"observation": oalias, "status": status, "observer": obs.observer_id,
                "detections": meta["detection_count"], "degraded": meta["degraded"],
                "feature_space": space}

    # ══ Runs (reproducibility, §24) ════════════════════════════════════════════════

    def op_run_new(self, pool: str, observers: str, run: str = "", config: str = "",
                   bench: str = "", branch: str = "", mode: str = "execution",
                   purpose: str = "") -> Dict[str, Any]:
        """[vlab.run.new] Create a vision-run provenance record (§24) over a pool with a set of
        observers. Re-running the experiment uses a NEW run id; previous runs stay intact.

        D2-M §2 — the run carries the COORDINATES it stamps onto every observation it mints:
        `bench` (`wb:<name>` or ""), `branch` (the workflow branch that issued it), `mode`
        (execution|thought), `purpose` (bench|precompute|manual — defaults to bench when a bench is
        named, else manual). A bench keeps `set:wb:<b>:runs` so "the runs of this bench" is one Set."""
        run = run or "r%03d" % (self._akasha_now())
        obs_ids = [o.strip() for o in observers.split(",") if o.strip()]
        for oid in obs_ids:
            self._observer(oid)                              # validate
        vis = "local" if self._meta(pool).get("visibility") == "local" \
            or self._meta("source:pool:%s" % slug(pool)).get("visibility") == "local" else "public"
        purpose = purpose or ("bench" if bench else "manual")
        mode = mode or "execution"
        # the model sha8s this run will read with — provenance on the run atom (D2-M §2)
        sha8s = []
        for oid in obs_ids:
            try:
                sha8s.append(self._obs_sha8(self._observer(oid), self._mint_model(self._observer(oid))))
            except Exception:
                pass
        alias = "vision_run:%s" % slug(run)
        existed = bool(self._key(alias))
        self._mint(alias, "[vision_run] %s over %s" % (run, pool),
                   {"concept": "vision_run", "run": run, "source_pool": pool,
                    "observers": obs_ids, "config": config, "status": "open",
                    "started_at": self._now_wall(), "cronon": self._akasha_now(),
                    "success_count": 0, "failure_count": 0, "visibility": vis,
                    "bench": bench or "", "wf_branch": branch or "", "mode": mode,
                    "purpose": purpose, "model_sha8s": sorted(set(sha8s))}, vis)
        # pay-at-write run index so the Source Viewer can list a pool's runs in O(K) (no scan)
        rkey = self._key(alias)
        # D2-M M1 — `_mint` is idempotent-by-alias, so a run atom minted BEFORE the coordinate layer
        # existed (o0/f1/o1, which persist across builds) keeps its empty bench/wf_branch/purpose on a
        # re-`run.new`. MERGE the coordinates the caller supplies: a NON-EMPTY arg overwrites the stored
        # field (a re-provisioned workflow now carries them), an empty arg leaves the stored value intact
        # (a bare re-run never wipes a bench). So the coords the observations copy at mint are current.
        if existed and rkey:
            cur = self._meta(alias) or {}
            updates = {}
            if bench and cur.get("bench") != bench:
                updates["bench"] = bench
            if branch and cur.get("wf_branch") != branch:
                updates["wf_branch"] = branch
            if purpose and cur.get("purpose") != purpose:
                updates["purpose"] = purpose
            if mode and cur.get("mode") != mode:
                updates["mode"] = mode
            _shas = sorted(set(sha8s))
            if _shas and cur.get("model_sha8s") != _shas:
                updates["model_sha8s"] = _shas
            for _mk_, _mv in updates.items():
                self._set_meta(rkey, _mk_, _mv)
        self._addset_v("set:vlab:runs", rkey, vis)
        self._addset_v("set:vlab:pool:%s:runs" % slug(pool), rkey, vis)
        if bench:                                            # "the runs of this bench" is one Set
            self._addset_v("set:wb:%s:runs" % _wb_tag(bench), rkey, vis)
        if mode == "thought":
            self._addset_v("set:vlab:mode:thought:runs", rkey, vis)
        return {"run": run, "pool": pool, "observers": obs_ids, "visibility": vis,
                "bench": bench or "", "wf_branch": branch or "", "mode": mode, "purpose": purpose}

    def reset_run(self, run: str) -> Dict[str, Any]:
        """Drop a vision run's observations + detections + the run atom, so a following run.execute
        RE-observes from scratch. Observations are content-addressed (idempotent by alias), so a
        re-execute would otherwise keep the old (e.g. mock) results — this clears them so a newly
        available real detector actually replaces them. Fenced to `set:vlab:run:<run>:obs` (+ each
        observation's detection set) and `vision_run:<run>`; never touches a Source Atom."""
        core = self._nuc.core if self._nuc else None
        if not core:
            return {"run": run, "note": "no nucleus"}

        def _drop(k):
            for coll in list(core.get_collections_for_key(k) or []):
                try:
                    core.remove_from_collection(coll, k)
                except Exception:
                    pass
            for al in list(core.get_aliases_by_key(k) or []):
                try:
                    core.delete_alias(al)
                except Exception:
                    pass
            try:
                core.drop_chunk(k)
            except Exception:
                pass

        n_obs = n_det = 0
        run_set = "set:vlab:run:%s:obs" % slug(run)
        for okey in list(self._members(run_set)):
            det_set = "set:vlab:det:%s" % slug(self._alias(okey) or "")
            for dk in list(self._members(det_set)):
                _drop(dk); n_det += 1
            try:
                core.clear_collection(det_set)
            except Exception:
                pass
            _drop(okey); n_obs += 1
        try:
            core.clear_collection(run_set)
        except Exception:
            pass
        rk = self._key("vision_run:%s" % slug(run))
        if rk:
            _drop(rk)
        logger.info("[vlab.reset_run] %s → dropped %d observations, %d detections", run, n_obs, n_det)
        return {"run": run, "dropped_observations": n_obs, "dropped_detections": n_det}

    def _pool_members(self, pool: str) -> List[str]:
        # A pool is a Set; members are the source atom keys. Bounded (a frozen corpus is ~100).
        # Three conventions, so vlab observes ANY pool: a vlab.source.add pool tracks membership on the
        # pool set itself; a source.acquire/import pool uses the source-layer `<pool>:members` frame; a
        # legacy vlab pool uses `set:vlab:pool:<slug>:members`.
        members = self._members(pool)
        if not members:
            members = self._members("%s:members" % pool)          # source-layer pool frame
        if not members:
            members = self._members("set:vlab:pool:%s:members" % slug(pool))
        return members

    def _find_reusable_observation(self, object_id: str, observer_id: str, sha8: str,
                                   run: str) -> Optional[str]:
        """D2-M §3 — an identical (item, observer, model_sha8) reading from an EARLIER run. The item's
        obs membrane is small, so this is O(readings-of-this-item), never a scan. None if none match.
        Deterministic observers reproduce their reading, so reuse is valid even for a model-less
        observer (`nomodel`) as long as the observer id AND the sha8 both match."""
        if not sha8:
            return None
        for okey in self._members("set:vlab:src:%s:obs" % slug(str(object_id))):
            m = self._meta(okey) or {}
            if (m.get("observer") == observer_id and str(m.get("model_sha8") or "") == sha8
                    and m.get("status") == "success" and slug(m.get("run", "")) != slug(run)):
                return okey
        return None

    def _reusable_base_vector(self, object_id: str, base_space: str,
                              base_sha8: str = "") -> Optional[List[float]]:
        """S2-k2 — the BASE-SPACE embedding of an item, from ANY earlier feature run of the same base
        space, so a learned-head observe reuses it instead of re-embedding (the encoder never runs). Keyed
        on (item, base_space, base sha8): the item's feature membrane is small, so O(features-of-this-item),
        never a scan. `base_sha8` tightens the match when the feature atom carries one; an older atom
        without a stamped sha8 matches on the space alone. None if no base embedding exists yet."""
        if not object_id or not base_space:
            return None
        for fkey in self._members("set:vlab:src:%s:feat" % slug(str(object_id))):
            m = self._meta(fkey) or {}
            if m.get("feature_space") != base_space:
                continue
            if base_sha8 and m.get("model_sha8") and str(m.get("model_sha8")) != str(base_sha8):
                continue
            vec = m.get("feature_vector")
            if vec:
                return [float(x) for x in vec]
        return None

    def _reuse_into_run(self, okey: str, run: str, coords: Dict[str, Any], visibility: str) -> None:
        """Add an existing observation atom to a new run's run/bench/branch Sets WITHOUT re-minting
        (D2-M §3). The family/observer/model Sets it already joined at its original mint are unchanged."""
        self._addset_v("set:vlab:run:%s:obs" % slug(run), okey, visibility)
        self._addset_v("set:vlab:run:%s:observations" % slug(run), okey, visibility)
        b = coords.get("bench")
        if b:
            self._addset_v("set:wb:%s:observations" % _wb_tag(b), okey, visibility)
            if coords.get("wf_branch"):
                self._addset_v("set:wb:%s:branch:%s:observations"
                               % (_wb_tag(b), slug(coords["wf_branch"])), okey, visibility)

    def _register_reuse_coverage(self, okey: str, provider: str, object_id: str, observer: str,
                                 run: str, visibility: str) -> None:
        """B2 (S2-k) — make a REUSED reading COUNT for `run` without re-running the encoder, so a sweep's
        second condition (same frozen train pool, same embedder) trains in seconds instead of re-embedding
        the whole pool (~40 min). Two things the plain observation-Set reuse (`_reuse_into_run`) does not
        do, both needed by the LEARNING pipeline:
          (1) register THIS run's per-source SENTINEL alias (`obs:vision:…:<run>`) → the shared
              observation atom, so op_run_execute's `pending` check and learning.train's seal probe
              (`remaining==0`) see (source, observer) as covered for this run;
          (2) add the shared FEATURE atom (`obs:feature:…:<orig_run>`) to THIS run's feature membrane
              `set:vlab:feat:<run>:<space>`, so learning.train's `_space_vectors` finds the reused embedding.
        The embedding is genuinely identical (same item, observer, model_sha8), so it is SHARED, never
        recomputed and never duplicated — only the run-scoped sentinel + membrane membership are new."""
        oalias = self._obs_alias(provider, object_id, observer, run)
        if not self._key(oalias):
            if visibility == "local":
                self.cortex.core.put_alias(okey, oalias)
            else:
                nuc = self._store()
                (nuc.core if nuc is not None else self.cortex.core).put_alias(okey, oalias)
        orig_run = (self._meta(okey) or {}).get("run") or run
        falias = "obs:feature:%s:%s:%s:%s" % (provider, slug(str(object_id)), observer, slug(orig_run))
        fkey = self._key(falias)
        if fkey:
            sp = (self._meta(falias) or {}).get("feature_space")
            if sp:
                self._addset_v("set:vlab:feat:%s:%s" % (slug(run), slug(sp)), fkey, visibility)

    def op_run_execute(self, run: str, limit: str = "", reuse: str = "") -> Dict[str, Any]:
        """[vlab.run.execute] WRITER-SIDE batch: stream the run's pool and run every observer on
        every source, ONE image at a time (memory discipline R1/R4 — the images are never held in
        bulk). Resumable: a (source, observer) already observed in this run is SKIPPED (sentinel,
        R5), so a re-run only fills gaps. remote and local sources go through the identical path.

        A41.1 — `limit=N` bounds the number of sources on which at least one observation is ATTEMPTED
        in THIS call (NEW work), NOT the number examined: a source whose every observer is already
        sentinelled is skipped for free and does not consume the cap, so a resumed execute always
        advances past the sources it already covered (the v21 bug: the cap was spent on skips, so the
        corpus never grew past the first N). `limit=0` examines and counts WITHOUT observing (the
        seal/remaining probe). The result adds `remaining` = pool sources still needing ≥1 observer
        after this call, computed on the SAME streaming pass (walk continues counting once capped)."""
        rmeta = self._meta("vision_run:%s" % slug(run))
        if not rmeta:
            raise ValueError("unknown run '%s'" % run)
        _wall0 = self._now_wall()                             # B1-b — time this pass (cumulative on the run)
        pool = rmeta.get("source_pool")
        obs_ids = rmeta.get("observers") or []
        cap = int(limit) if str(limit).strip().isdigit() else None   # None = unbounded; 0 = count-only
        do_reuse = str(reuse).strip().lower() in ("1", "yes", "true", "on")
        vis = rmeta.get("visibility", "public")
        coords = self._run_coords(run)                       # bench/wf_branch/mode/purpose of THIS run
        # D2-M §3 — the model sha8 each observer reads with, computed once (reuse matches on it).
        sha8_map = {}
        if do_reuse:
            for oid in obs_ids:
                try:
                    o = self._observer(oid)
                    sha8_map[oid] = self._obs_sha8(o, self._mint_model(o))
                except Exception:
                    sha8_map[oid] = ""
        observed = skipped = failed = degraded = reused = 0
        reused_embeddings = 0   # S2-k2 — learned-head observes that reused a cached base embedding
        # S2-k3 — per-chunk timing accumulators (t_fetch/t_embed/t_head/t_write), flushed as a DEBUG line
        # every _TIMING_CHUNK observes, so the log shows where a reused-embedding observe spends its time.
        _TIMING_CHUNK = 100
        _tt = {"t_fetch": 0.0, "t_embed": 0.0, "t_head": 0.0, "t_write": 0.0, "t_observe": 0.0}
        _tt_n = 0
        seen_sources = 0        # sources examined for observation (pre-cap)
        attempted = 0           # sources with ≥1 observation attempted this call — the CAP axis
        remaining = 0           # sources still needing ≥1 observer after this call
        over_cap = False
        for src_key in self._pool_members(pool):             # bounded stream over the pool
            src_alias = self._alias(src_key)
            smeta = self._meta(src_key)
            provider = smeta.get("provider", "x")
            object_id = smeta.get("provider_object_id", src_alias)
            pending = [oid for oid in obs_ids
                       if not self._key(self._obs_alias(provider, object_id, oid, run))]
            if not pending:                                  # fully observed — a FREE skip (no cap cost)
                if not over_cap:
                    seen_sources += 1
                    skipped += len(obs_ids)
                continue
            # D2-M §3 — REUSE pass: an identical earlier reading is added to this run's Sets for free
            # (no observer re-run, no cap cost); only the genuinely-new observers fall through to observe.
            still_new = []
            for oid in pending:
                if do_reuse:
                    rk = self._find_reusable_observation(object_id, oid, sha8_map.get(oid, ""), run)
                    if rk:
                        self._reuse_into_run(rk, run, coords, vis)
                        # B2 (S2-k) — register this run's sentinel alias + feature membrane so the seal
                        # probe (remaining==0) and learning.train's _space_vectors both see this run as
                        # covered, without re-running the encoder.
                        self._register_reuse_coverage(rk, provider, object_id, oid, run, vis)
                        reused += 1
                        continue
                still_new.append(oid)
            if not still_new:                                # fully covered by reuse — no cap cost
                if not over_cap:
                    seen_sources += 1
                continue
            # this source is NEW WORK
            if over_cap or (cap is not None and attempted >= cap):
                over_cap = True
                remaining += 1                               # over the cap: count only, do not observe
                continue
            seen_sources += 1
            skipped += (len(obs_ids) - len(pending))
            for oid in still_new:
                res = self.op_observe(source=src_alias, observer=oid, run=run)
                _tm = res.get("_timing") or {}
                if _tm:                               # S2-k3 — accumulate the per-observe cost split
                    for _k in _tt:
                        _tt[_k] += float(_tm.get(_k) or 0.0)
                    _tt_n += 1
                    if _tt_n % _TIMING_CHUNK == 0:     # per-chunk DEBUG: where a reused observe spends time
                        logger.debug("[vlab] observe chunk run=%s at=%d t_fetch=%.2f t_embed=%.2f "
                                     "t_head=%.2f t_write=%.2f t_observe=%.2f (per-item write=%.3fs)",
                                     run, _tt_n, _tt["t_fetch"], _tt["t_embed"], _tt["t_head"],
                                     _tt["t_write"], _tt["t_observe"], _tt["t_write"] / max(1, _tt_n))
                if res.get("status") == "failed":
                    failed += 1
                else:
                    observed += 1
                    if res.get("degraded"):
                        degraded += 1
                    if res.get("reused_base"):        # S2-k2 — the encoder was skipped for this observe
                        reused_embeddings += 1
            attempted += 1
        # update counts (a run's tally is provenance)
        _rk = self._key("vision_run:%s" % slug(run))
        self._set_meta(_rk, "success_count", int(rmeta.get("success_count", 0)) + observed)
        self._set_meta(_rk, "failure_count", int(rmeta.get("failure_count", 0)) + failed)
        # B1-b — the run's CUMULATIVE reuse count and wall time (GUI §7 reads them off the run atom via
        # learning.runs). Both accumulate across chunked executes so a resumed run reports its whole cost.
        self._set_meta(_rk, "reused_count", int(rmeta.get("reused_count", 0)) + reused)
        # S2-k2 — cumulative count of learned-head observes that reused a cached base embedding.
        self._set_meta(_rk, "reused_embeddings",
                       int(rmeta.get("reused_embeddings", 0)) + reused_embeddings)
        self._set_meta(_rk, "wall_s", round(float(rmeta.get("wall_s", 0) or 0)
                                            + (self._now_wall() - _wall0), 3))
        # A37/A41.1 — the batch reports what it observed AND how much of the pool is still uncovered,
        # so a bench block (b3) that "completed" is legible in the log without inspecting the store.
        # S2-k2 — reused_embeddings= names the learned-head observes that skipped the encoder.
        logger.info("[vlab] run.execute run=%s pool=%s sources=%d observers=%d observed=%d reused=%d "
                    "reused_embeddings=%d skipped=%d failed=%d remaining=%d", run, pool, seen_sources,
                    len(obs_ids), observed, reused, reused_embeddings, skipped, failed, remaining)
        # S2-k3 — the cost split across the observes this pass, so the observe cost is legible without
        # DEBUG: t_embed=0 confirms the encoder was skipped (base_vector reuse); a high t_write points the
        # optimisation at the write path, not the encoder.
        _timing = {k: round(v, 3) for k, v in _tt.items()}
        _timing["n"] = _tt_n
        if _tt_n:
            logger.info("[vlab] observe cost run=%s n=%d t_embed=%.1fs t_head=%.2fs t_write=%.1fs "
                        "(per-item %.3fs)", run, _tt_n, _tt["t_embed"], _tt["t_head"], _tt["t_write"],
                        (_tt["t_observe"] + _tt["t_write"]) / max(1, _tt_n))
        return {"run": run, "pool": pool, "sources": seen_sources, "observed": observed,
                "reused": reused, "reused_embeddings": reused_embeddings, "skipped": skipped,
                "failed": failed, "degraded": degraded, "remaining": remaining, "timing": _timing}

    def op_run_seal(self, run: str) -> Dict[str, Any]:
        """[vlab.run.seal] Finalize a run: stamp completed_at and freeze its status. Previous runs
        remain intact; a new experiment is a new run."""
        rk = self._key("vision_run:%s" % slug(run))
        if not rk:
            raise ValueError("unknown run '%s'" % run)
        self._set_meta(rk, "status", "sealed")
        self._set_meta(rk, "completed_at", self._now_wall())
        return {"run": run, "status": "sealed", **{k: self._meta(rk).get(k)
                for k in ("success_count", "failure_count")}}

    def op_reindex(self, run: str) -> Dict[str, Any]:
        """[vlab.reindex] Idempotently (re-)add an EXISTING vision run to the run-index membranes
        (`set:vlab:runs` + `set:vlab:pool:<pool>:runs`) so `vlab.runs` finds it. Needed for a run minted
        BEFORE the run-index existed on a cell whose data persisted across the upgrade — its observations
        are intact but were never indexed, so the Source Viewer showed 'no observation'. The bootstraps
        call this each boot for their canonical runs (idempotent); an operator can call it directly."""
        alias = "vision_run:%s" % slug(run)
        rk = self._key(alias)
        if not rk:
            return {"run": run, "indexed": False, "note": "unknown run"}
        m = self._meta(alias) or {}
        pool = m.get("source_pool")
        vis = m.get("visibility", "public")
        self._addset_v("set:vlab:runs", rk, vis)
        if pool:
            self._addset_v("set:vlab:pool:%s:runs" % slug(pool), rk, vis)
        return {"run": run, "indexed": True, "pool": pool}

    def op_run_info(self, run: str) -> Dict[str, Any]:
        """[vlab.run.info] Read a run's reproducibility record."""
        m = self._meta("vision_run:%s" % slug(run))
        if not m:
            raise ValueError("unknown run '%s'" % run)
        return {"run": run, **{k: m.get(k) for k in
                ("source_pool", "observers", "config", "status", "started_at", "completed_at",
                 "success_count", "failure_count", "visibility")}}

    def op_runs(self, pool: str = "", limit: str = "") -> Dict[str, Any]:
        """[vlab.runs] List the observation runs, newest first — the index the Source Viewer reads to
        show a pool's Image/Audio analysis (which runs exist, what senses they measured). With `pool=`
        only that pool's runs (O(K) via the per-pool run membrane); without, every run. Each row
        carries its observers, the modalities they measured (image | audio → the viewer's tabs), the
        feature spaces they populate, status and success/failure counts."""
        idx = ("set:vlab:pool:%s:runs" % slug(pool)) if pool else "set:vlab:runs"
        cap = int(limit) if str(limit).strip().isdigit() else 200
        roster = self._roster()
        rows = []
        for rkey in self._members(idx):
            m = self._meta(rkey)
            if not m or m.get("concept") != "vision_run":
                continue
            obs_ids = m.get("observers") or []
            mods = sorted({getattr(roster[o], "modality", "image") for o in obs_ids if o in roster})
            spaces = sorted({s for o in obs_ids for s, fams in _FEATURE_SPACES.items() if o in fams})
            rows.append({"run": m.get("run"), "pool": m.get("source_pool"), "observers": obs_ids,
                         "modalities": mods, "spaces": spaces, "status": m.get("status"),
                         "success_count": m.get("success_count"), "failure_count": m.get("failure_count"),
                         "started_at": m.get("started_at"), "cronon": m.get("cronon")})
        rows.sort(key=lambda r: r.get("cronon") or 0, reverse=True)
        return {"pool": pool or None, "runs": rows[:cap], "count": len(rows)}

    def _backfill_observation_layer(self, okey: str, m: Dict[str, Any]) -> Dict[str, Any]:
        """D2-M §1 — an observation minted before the coordinate layer lacks it. On first READ of the
        item, compute it (bounded by the item's obs in-degree) and stamp the keys + the coordinate Sets.

        R1 — idempotence keys on `layer_v == _LAYER_V`, NOT on `family`: the v1 backfill stamped `family`
        while the run atoms still had empty coords, so those observations carry family but blank
        bench/wf_branch/purpose. Bumping `_LAYER_V` re-runs the backfill once (the run atoms are fixed
        now) and re-stamps the coords + the missing bench/branch Sets. A v2 observation is skipped."""
        if m.get("layer_v") == _LAYER_V:
            return m
        try:
            obs = self._observer(m.get("observer") or "")
        except Exception:
            obs = None
        model_alias = m.get("model") or ""
        sha8 = ""
        if obs is not None:
            sha8 = self._obs_sha8(obs, model_alias)
        else:
            mm = self._meta(model_alias) or {}
            sha8 = str(mm.get("weights_sha256") or mm.get("sha256") or "")[:8] or "nomodel"
        fam = self._obs_family(obs, bool(m.get("degraded"))) if obs is not None else "sense"
        coords = self._run_coords(m.get("run") or "")
        layer = {"family": fam, "model_sha8": sha8, "observer_version": sha8,
                 "bench": coords["bench"], "wf_branch": coords["wf_branch"],
                 "mode": coords["mode"], "purpose": coords["purpose"],
                 "at_seq": m.get("at_seq") or m.get("cronon") or 0, "layer_v": _LAYER_V}
        for kk, vv in layer.items():
            self._set_meta(okey, kk, vv)
        vis = m.get("visibility", "public") or "public"
        self._add_layer_sets(okey, layer, m.get("observer") or "", vis)
        m = dict(m); m.update(layer)
        return m

    def _obs_headline(self, oalias: str, m: Dict[str, Any]) -> Dict[str, Any]:
        """The ONE value a human compares (D2-M §4.1): {label, score} for a classifier/head, {dominant,
        n} for a detector, {summary} for a sense (a few named feature scalars)."""
        info = self.op_observation(oalias) if oalias else {}
        features = info.get("features") or {}
        dets = []
        for dk in self._members("set:vlab:det:%s" % slug(oalias or "")):
            dm = self._meta(dk)
            if dm:
                dets.append(dm)
        if dets:
            kind = ((self._meta(m.get("model") or "") or {}).get("kind") or "")
            if kind == "classifier" or getattr(self._safe_observer(m.get("observer")), "family", "") == "learned":
                top = max(dets, key=lambda d: float(d.get("confidence") or 0))
                return {"label": top.get("class"), "score": round(float(top.get("confidence") or 0), 4)}
            counts: Dict[str, int] = {}
            for d in dets:
                counts[str(d.get("class"))] = counts.get(str(d.get("class")), 0) + 1
            dom = max(counts.items(), key=lambda kv: kv[1])[0] if counts else None
            return {"dominant": dom, "n": len(dets)}
        # a sense: a short, human-readable summary of the measurement
        summ = {}
        if features.get("feature_space"):
            summ["space"] = features["feature_space"]
        for kk, vv in features.items():
            if kk in ("feature_vector", "embedding", "feature_space", "source"):
                continue
            if isinstance(vv, (int, float, str)) and len(summ) < 4:
                summ[kk] = vv
        return {"summary": summ}

    def _safe_observer(self, oid: str):
        try:
            return self._observer(oid or "")
        except Exception:
            return None

    def op_item(self, source: str, family: str = "", bench: str = "", branch: str = "", run: str = "",
                model: str = "", mode: str = "", purpose: str = "", limit: str = "50",
                offset: str = "0") -> Dict[str, Any]:
        """[vlab.item] Every machine observation of ONE source item, filterable by any coordinate
        (D2-M §4.1). Each filter is an intersection of the §2 Sets — evaluated per the item's own obs
        membrane (O(K), the item's in-degree), never a store scan. Rows sort by `at_seq` desc and carry
        {observation, observer, family, model_sha8, run, bench, wf_branch, mode, purpose, status,
        degraded, at_seq, headline, features}; plus `sample_roles` for the item and `count_total` for
        paging. `limit`/`offset` page. A legacy observation is layer-backfilled on this first read."""
        sk = self._key(source) or source
        smeta = self._meta(sk) or self._meta(source) or {}
        object_id = smeta.get("provider_object_id", self._alias(sk) or source)
        _bn = (bench if bench.startswith("wb:") else "wb:" + bench) if bench else ""
        try:
            lim = max(1, int(limit))
        except (TypeError, ValueError):
            lim = 50
        try:
            off = max(0, int(offset))
        except (TypeError, ValueError):
            off = 0
        # D2-M §4.1 — filters are INTERSECTIONS of the §2 Sets. The PLACEMENT coordinates (run / bench
        # / branch) are filtered by Set membership so a reading REUSED into a run/bench (§3, its own
        # meta still names its origin) is correctly included; the INTRINSIC coordinates (family /
        # model / purpose / mode, stamped at mint) are filtered on the meta. Each filter Set is read
        # once (bounded by that run/bench's size — a collection read, never a store scan).
        run_set = set(self._members("set:vlab:run:%s:observations" % slug(run))) if run else None
        bench_set = set(self._members("set:wb:%s:observations" % _wb_tag(_bn))) if _bn else None
        branch_set = (set(self._members("set:wb:%s:branch:%s:observations"
                                        % (_wb_tag(_bn), slug(branch)))) if (branch and _bn) else None)
        rows = []
        for okey in self._members("set:vlab:src:%s:obs" % slug(str(object_id))):
            m = self._meta(okey)
            if not m or m.get("concept") != "vision_observation":
                continue
            m = self._backfill_observation_layer(okey, m)     # §1 lazy backfill (idempotent)
            if run_set is not None and okey not in run_set:
                continue
            if bench_set is not None and okey not in bench_set:
                continue
            if branch_set is not None and okey not in branch_set:
                continue
            if branch and not _bn and m.get("wf_branch") != branch:      # branch without bench → meta
                continue
            if family and m.get("family") != family:
                continue
            if model and str(m.get("model_sha8") or "") != model:
                continue
            if purpose and m.get("purpose") != purpose:
                continue
            if mode == "execution" and m.get("mode") == "thought":
                continue
            if mode == "thought" and m.get("mode") != "thought":
                continue
            oalias = self._alias(okey)
            info = self.op_observation(oalias) if oalias else {}
            # R1 — a reader never sees vlab.item contradict learning.runs: when the observation's own
            # coords are empty (a legacy row not yet re-backfilled), fall back to its run atom's coords
            # (one meta read, no scan). A stored non-empty value on the observation always wins.
            _rc = None
            _r_bench = m.get("bench") or ""
            _r_branch = m.get("wf_branch") or ""
            _r_purpose = m.get("purpose") or ""
            if not (_r_bench and _r_purpose):
                _rc = self._run_coords(m.get("run") or "")
                _r_bench = _r_bench or _rc["bench"]
                _r_branch = _r_branch or _rc["wf_branch"]
                _r_purpose = _r_purpose or _rc["purpose"]
            rows.append({"observation": oalias, "observer": m.get("observer"),
                         "family": m.get("family"), "model_sha8": m.get("model_sha8"),
                         "run": m.get("run"), "bench": _r_bench, "wf_branch": _r_branch,
                         "mode": m.get("mode"), "purpose": _r_purpose,
                         "status": m.get("status"), "degraded": m.get("degraded"),
                         "at_seq": m.get("at_seq") or m.get("cronon") or 0,
                         "headline": self._obs_headline(oalias, m), "features": info.get("features")})
        rows.sort(key=lambda r: r.get("at_seq") or 0, reverse=True)
        total = len(rows)
        try:
            sample_roles = self._source_concept().sample_roles_for(sk, "")
        except Exception:
            sample_roles = []
        return {"source": self._alias(sk) or source, "observations": rows[off:off + lim],
                "count": len(rows[off:off + lim]), "count_total": total,
                "sample_roles": sample_roles, "limit": lim, "offset": off}

    def _backfill_run_atom(self, run: str) -> Dict[str, Any]:
        """D2-M M3 — a run atom minted before the coordinate layer has `bench=""`, `purpose=null`,
        `wf_branch=""`, `model_sha8s=[]`, so `learning.runs` cannot filter or describe it. DERIVE the
        coords the graph already knows and stamp any that are missing (a stored non-empty value is never
        overwritten): `bench`/`purpose` via `_run_coords`; `model_sha8s` = the distinct `model_sha8` of
        the run's observations; `wf_branch` = the branch its observations were placed under. Bounded by
        the run's observation count (O(K), a membrane read — never a scan). Returns the fields written."""
        ralias = "vision_run:%s" % slug(run)
        rk = self._key(ralias)
        if not rk:
            return {}
        m = self._meta(ralias) or {}
        updates: Dict[str, Any] = {}
        coords = self._run_coords(run)
        if not (m.get("bench") or "") and coords["bench"]:
            updates["bench"] = coords["bench"]
        if not (m.get("purpose") or "") and coords["purpose"]:
            updates["purpose"] = coords["purpose"]
        if not (m.get("model_sha8s")) or not (m.get("wf_branch") or ""):
            shas: set = set()
            wbr = ""
            for okey in self._members("set:vlab:run:%s:observations" % slug(str(run))):
                om = self._meta(okey) or {}
                if om.get("model_sha8"):
                    shas.add(str(om["model_sha8"]))
                if not wbr and (om.get("wf_branch") or ""):
                    wbr = om["wf_branch"]
            if shas and not m.get("model_sha8s"):
                updates["model_sha8s"] = sorted(shas)
            if wbr and not (m.get("wf_branch") or ""):
                updates["wf_branch"] = wbr
        # ensure the bench run-index Set membership too (so learning.runs sees a legacy run at all)
        if updates.get("bench") or (m.get("bench") or ""):
            _b = updates.get("bench") or m.get("bench")
            self._addset_v("set:wb:%s:runs" % _wb_tag(_b), rk, m.get("visibility", "public") or "public")
        for kk, vv in updates.items():
            self._set_meta(rk, kk, vv)
        return updates

    def _backfill_compares(self) -> Dict[str, Any]:
        """D2-M M2 / M2-b — reconcile stored `lens.compare` diff atoms whose alias carries the RAW bench
        (`wb:plants-vision:diff:…`) with the uslug twin (`wb:plants_vision:diff:…`):

        - if NO slug-aliased twin exists, RE-ALIAS the old atom to the slug form (a pure rename);
        - if a twin DOES exist (both minted — the epoch-keyed rebuild made a new atom), M2-b: link the
          OLD atom → the new twin with `bench:superseded_by`, and REMOVE the old atom from
          `set:wb:<tag>:diffs` so only the newest per (a,b) stays indexed (history one hop away);
        - re-index the surviving atom into `set:wb:<tag>:diffs` from its `bench:compares` run atoms.

        Bounded by the number of stored compares; idempotent. Returns counts."""
        core = self._nuc.core if self._nuc else (self.cortex.core if self.cortex else None)
        if core is None:
            return {"realiased": 0, "reindexed": 0, "superseded": 0}
        realiased = reindexed = superseded = 0
        for stored in list(self._members("set:vlab:compares")):
            alias = self._alias(stored) or ""
            keep = True                      # does THIS atom stay the indexed one for its pair?
            if alias.startswith("wb:"):
                parts = alias.split(":")
                if len(parts) >= 2 and parts[1] and slug(parts[1]) != parts[1]:
                    parts[1] = slug(parts[1])
                    new_alias = ":".join(parts)
                    twin = self._key(new_alias)
                    if twin and twin != stored:
                        # M2-b — a slug-aliased twin exists: supersede the old, drop it from the index
                        try:
                            self._link(alias, new_alias, "bench:superseded_by")
                        except Exception:
                            pass
                        for _b in self._compare_benches(alias or stored):
                            self._remove_from_set("set:wb:%s:diffs" % _wb_tag(_b), stored)
                        superseded += 1
                        keep = False
                    else:
                        try:
                            core.put_alias(stored, new_alias)   # no twin → pure rename
                            realiased += 1
                            alias = new_alias
                        except Exception:
                            pass
            if not keep:
                continue
            for _b in self._compare_benches(alias or stored):
                self._addset_v("set:wb:%s:diffs" % _wb_tag(_b), stored)
                reindexed += 1
        return {"realiased": realiased, "reindexed": reindexed, "superseded": superseded}

    def _compare_benches(self, alias_or_key: str) -> set:
        """The benches a stored compare belongs to — from its `bench:compares` run atoms' `bench`."""
        benches = set()
        for dst, rel in (self._links(alias_or_key) or []):
            if rel == "bench:compares" and dst:
                rb = (self._meta(dst) or {}).get("bench")
                if rb:
                    benches.add(rb)
        return benches

    def op_layer_backfill(self, run: str = "") -> Dict[str, Any]:
        """[vlab.layer.backfill] D2-M §1 — stamp the coordinate layer + Sets onto observations minted
        before this change. With `run=`, one run's observations (`set:vlab:run:<run>:observations`);
        else every indexed run. Bounded per run; idempotent (an observation with `family` is skipped).
        M3 — the RUN ATOM is backfilled too (bench/purpose/wf_branch/model_sha8s) so `learning.runs` can
        describe a legacy run; M2 — stored compares re-aliased + re-indexed. Called by the boot pass
        (throttled) and available to an operator."""
        runs = [run] if run else [ (self._meta(self._alias(rk)) or {}).get("run")
                                   for rk in self._members("set:vlab:runs") ]
        total = 0
        per = []
        for r in runs:
            if not r:
                continue
            n = 0
            for okey in self._members("set:vlab:run:%s:observations" % slug(str(r))):
                m = self._meta(okey)
                if not m or m.get("concept") != "vision_observation" or m.get("layer_v") == _LAYER_V:
                    continue                          # R1 — key on the layer version, not `family`
                self._backfill_observation_layer(okey, m)
                n += 1
            run_upd = self._backfill_run_atom(r)                # M3 — fix the run atom's coords too
            if n or run_upd:
                logger.info("[vlab] layer backfill run=%s assigned=%d run_atom=%s",
                            r, n, ",".join(sorted(run_upd)) or "-")
                per.append({"run": r, "assigned": n, "run_atom": sorted(run_upd)})
                total += n
        # M2 — once the run atoms carry their bench (above), re-alias + re-index stored compares. Global
        # (not per-run), so only on a full backfill pass.
        comp = self._backfill_compares() if not run else {"realiased": 0, "reindexed": 0}
        if comp.get("realiased") or comp.get("reindexed"):
            logger.info("[vlab] layer backfill compares realiased=%d reindexed=%d",
                        comp["realiased"], comp["reindexed"])
        return {"runs": len(per), "assigned": total, "detail": per, "compares": comp}

    def op_item_versions(self, source: str, observer: str) -> Dict[str, Any]:
        """[vlab.item.versions] The item's readings BY ONE observer, one row per model version
        (`model_sha8`), newest first — the version stack (D2-M §4.2). Each row carries the model
        provenance {model_sha8, run, wf_branch, trained_on_run, engine, accuracy}."""
        sk = self._key(source) or source
        smeta = self._meta(sk) or self._meta(source) or {}
        object_id = smeta.get("provider_object_id", self._alias(sk) or source)
        seen = {}
        for okey in self._members("set:vlab:src:%s:obs" % slug(str(object_id))):
            m = self._meta(okey)
            if not m or m.get("concept") != "vision_observation" or m.get("observer") != observer:
                continue
            m = self._backfill_observation_layer(okey, m)
            sha8 = str(m.get("model_sha8") or "")
            mm = self._meta(m.get("model") or "") or {}
            cfg = getattr(self._safe_observer(observer), "config", None) or {}
            row = {"model_sha8": sha8, "run": m.get("run"), "wf_branch": m.get("wf_branch"),
                   "trained_on_run": mm.get("feature_run") or cfg.get("feature_run"),
                   "engine": mm.get("engine") or cfg.get("engine"),
                   "accuracy": mm.get("accuracy") if mm.get("accuracy") is not None else cfg.get("accuracy"),
                   "at_seq": m.get("at_seq") or m.get("cronon") or 0,
                   "observation": self._alias(okey)}
            # keep the newest reading per version
            if sha8 not in seen or (row["at_seq"] or 0) > (seen[sha8]["at_seq"] or 0):
                seen[sha8] = row
        versions = sorted(seen.values(), key=lambda r: r.get("at_seq") or 0, reverse=True)
        return {"source": self._alias(sk) or source, "observer": observer,
                "versions": versions, "count": len(versions)}

    # ══ Reads (O(K)) ═══════════════════════════════════════════════════════════════

    def op_observation(self, id: str) -> Dict[str, Any]:
        """[vlab.observation] Read one observation + its model identity + status AND the concrete
        extraction result — the named FEATURE measurements a feature observer produced (edge_density,
        keypoints, entropy, dominant_class, …) and the feature_vector that analysis crosses. The
        feature atom is keyed by (source, observer, run) exactly like the observation, so its alias is
        the same id with the `obs:vision:` head swapped for `obs:feature:`. So the Machine Observation
        view can show the actual numbers, not just 'computed'."""
        m = self._meta(id)
        if not m:
            raise ValueError("unknown observation '%s'" % id)
        model = self._meta(m.get("model", "")) if m.get("model") else {}
        # the concrete extraction result — the feature measurements this observer stored
        features = None
        if id.startswith("obs:vision:"):
            fmeta = self._meta("obs:feature:" + id[len("obs:vision:"):])
            if fmeta:
                _skip = {"concept", "observer", "run"}
                features = {k: v for k, v in fmeta.items() if k not in _skip}
        return {"observation": id, "observer": m.get("observer"), "status": m.get("status"),
                "run": m.get("run"), "detection_count": m.get("detection_count"),
                "degraded": m.get("degraded"), "processed_at": m.get("processed_at"),
                "features": features,
                "model_identity": {k: model.get(k) for k in
                                   ("family", "model_name", "variant", "version", "framework")},
                "observes": [a for a, r in self._links(id, "vis:observes")]}

    def op_detections(self, obs: str, limit: str = "") -> Dict[str, Any]:
        """[vlab.detections] Read the detections under one observation (O(K) via a membrane set)."""
        cap = int(limit) if str(limit).strip().isdigit() else None
        det_set = "set:vlab:det:%s" % slug(obs)
        rows = []
        for i, k in enumerate(self._members(det_set)):
            if cap is not None and i >= cap:
                break
            m = self._meta(k)
            rows.append({k2: m.get(k2) for k2 in
                         ("class", "confidence", "bbox_x", "bbox_y", "bbox_width", "bbox_height")})
        return {"observation": obs, "detections": rows, "count": len(rows)}

    def op_features(self, obs: str) -> Dict[str, Any]:
        """[vlab.features] Read the concrete feature measurements for one observation (the named values
        + feature_vector the observer produced). `obs` may be the observation alias (obs:vision:…) or
        the feature alias (obs:feature:…) directly."""
        falias = ("obs:feature:" + obs[len("obs:vision:"):]) if obs.startswith("obs:vision:") else obs
        fmeta = self._meta(falias)
        if not fmeta:
            raise ValueError("no feature observation for '%s'" % obs)
        _skip = {"concept", "observer", "run"}
        return {"observation": obs, "feature_atom": falias,
                "features": {k: v for k, v in fmeta.items() if k not in _skip}}

    # ══ Model comparison (§19 — first-class data) ═════════════════════════════════

    def _detections_of(self, provider: str, object_id: str, observer: str, run: str) -> List[Dict[str, Any]]:
        oalias = self._obs_alias(provider, object_id, observer, run)
        return self.op_detections(oalias).get("detections", [])

    def op_compare(self, source: str, a: str, b: str, run: str = "r0") -> Dict[str, Any]:
        """[vlab.compare] Compute + persist a model-comparison record between two observers on one
        source (§19). The DIFFERENCE between models is first-class research data — usable in Sets
        and projections — not debugging noise."""
        smeta = self._source_meta(source)
        visibility = smeta.get("visibility", "public")
        provider = smeta.get("provider", "x")
        object_id = smeta.get("provider_object_id", source)
        da = self._detections_of(provider, object_id, a, run)
        db = self._detections_of(provider, object_id, b, run)
        ca = {d["class"] for d in da if d.get("class")}
        cb = {d["class"] for d in db if d.get("class")}
        shared = sorted(ca & cb)
        a_only = sorted(ca - cb)
        b_only = sorted(cb - ca)
        union = ca | cb
        agreement = round(len(ca & cb) / len(union), 3) if union else 1.0
        mean_conf = lambda ds: round(sum(d.get("confidence", 0) for d in ds) / len(ds), 3) if ds else 0.0
        calias = "comparison:vision:%s:%s:%s" % (slug(object_id), a, b)
        meta = {"concept": "vision_comparison", "source": source, "run": run,
                "observer_a": a, "observer_b": b, "shared_classes": shared,
                "model_a_only_classes": a_only, "model_b_only_classes": b_only,
                "count_difference": len(da) - len(db),
                "confidence_difference": round(mean_conf(da) - mean_conf(db), 3),
                "bbox_overlap": self._bbox_overlap(da, db), "agreement_score": agreement}
        self._mint(calias, "[comparison] %s: %s vs %s (agree=%.2f)" % (object_id, a, b, agreement),
                   meta, visibility)
        self._link_v(calias, self._obs_alias(provider, object_id, a, run), "vis:compares", visibility)
        self._link_v(calias, self._obs_alias(provider, object_id, b, run), "vis:compares", visibility)
        self._addset_v("set:vlab:run:%s:cmp" % slug(run), self._key(calias), visibility)
        return {"comparison": calias, "agreement_score": agreement, "shared_classes": shared,
                "model_a_only_classes": a_only, "model_b_only_classes": b_only,
                "count_difference": meta["count_difference"]}

    @staticmethod
    def _bbox_overlap(da: List[Dict[str, Any]], db: List[Dict[str, Any]]) -> float:
        """Mean best-match IoU between the two detection sets (normalized boxes). 0 when either is
        empty. A coarse agreement-of-placement signal, not a precise metric."""
        def iou(p, q):
            ax0, ay0 = p["bbox_x"] - p["bbox_width"] / 2, p["bbox_y"] - p["bbox_height"] / 2
            ax1, ay1 = p["bbox_x"] + p["bbox_width"] / 2, p["bbox_y"] + p["bbox_height"] / 2
            bx0, by0 = q["bbox_x"] - q["bbox_width"] / 2, q["bbox_y"] - q["bbox_height"] / 2
            bx1, by1 = q["bbox_x"] + q["bbox_width"] / 2, q["bbox_y"] + q["bbox_height"] / 2
            ix0, iy0, ix1, iy1 = max(ax0, bx0), max(ay0, by0), min(ax1, bx1), min(ay1, by1)
            iw, ih = max(0.0, ix1 - ix0), max(0.0, iy1 - iy0)
            inter = iw * ih
            ua = (ax1 - ax0) * (ay1 - ay0) + (bx1 - bx0) * (by1 - by0) - inter
            return inter / ua if ua > 0 else 0.0
        if not da or not db:
            return 0.0
        best = [max(iou(p, q) for q in db) for p in da]
        return round(sum(best) / len(best), 3)

    # ══ Derived Sets (§16 — overlapping, mechanically named) ══════════════════════

    def op_set_derive(self, run: str, kind: str = "") -> Dict[str, Any]:
        """[vlab.set.derive] Materialize derived Sets from the run's observations (person_present,
        multiple_persons, animal_present, object_dense/sparse, and yolo agreement/disagreement).
        A work may belong to MANY sets at once (overlap is expected, §16); membership is via set
        membrane, not a scan. Machine BLINDNESS is data too (§20): zero-detection works are queryable
        via object_sparse. Sets keep mechanical names — no semantic labeling (that is Phase 2)."""
        rmeta = self._meta("vision_run:%s" % slug(run))
        if not rmeta:
            raise ValueError("unknown run '%s'" % run)
        visibility = rmeta.get("visibility", "public")
        counts: Dict[str, int] = {}

        def add(setname, key):
            self._addset_v(setname, key, visibility)
            counts[setname] = counts.get(setname, 0) + 1

        for okey in self._members("set:vlab:run:%s:obs" % slug(run)):
            m = self._meta(okey)
            if m.get("status") != "success" or not m.get("observes"):
                # `observes` isn't in meta; resolve source via link
                pass
            src = self._first_link(okey, "vis:observes")
            if not src:
                continue
            dets = self.op_detections(self._alias(okey)).get("detections", [])
            classes = [d.get("class") for d in dets]
            n_person = classes.count("person")
            n_total = len(dets)
            if n_person >= 1:
                add("set:vision:person_present", src)
            if n_person >= 2:
                add("set:vision:multiple_persons", src)
            if any(c in _ANIMAL_CLASSES for c in classes):
                add("set:vision:animal_present", src)
            if n_total >= _OBJECT_DENSE:
                add("set:vision:object_dense", src)
            if n_total <= _OBJECT_SPARSE:
                add("set:vision:object_sparse", src)

        # model agreement/disagreement from persisted comparisons
        for ckey in self._members("set:vlab:run:%s:cmp" % slug(run)):
            cm = self._meta(ckey)
            src = cm.get("source")
            if not src:
                continue
            agree = cm.get("agreement_score", 0)
            skey = self._key(src) or src
            if agree >= 0.8:
                add("set:model:yolo_agreement", skey)
            elif agree <= 0.3:
                add("set:model:high_disagreement", skey)
            else:
                add("set:model:yolo_disagreement", skey)

        # v0.2 threshold feature Sets (§16). Each is a percentile threshold over ONE measured feature
        # of ONE observer, WITH its threshold metadata preserved (method / percentile / numeric
        # threshold / observer / feature / run / corpus). Mechanically named — never a semantic label.
        corpus = rmeta.get("source_pool")
        self._threshold_set(run, "color", "saturation_mean", "set:vision:low_saturation",
                            0.20, "low", visibility, corpus, add)
        self._threshold_set(run, "geometry", "edge_density", "set:vision:high_edge_density",
                            0.80, "high", visibility, corpus, add)
        self._threshold_set(run, "geometry", "lr_symmetry", "set:vision:high_symmetry",
                            0.80, "high", visibility, corpus, add)
        self._threshold_set(run, "texture", "entropy", "set:vision:high_entropy",
                            0.80, "high", visibility, corpus, add)
        self._outlier_set(run, "color", "set:vision:color_outlier", 0.90, visibility, corpus, add)
        self._outlier_set(run, "geometry", "set:vision:geometry_outlier", 0.90, visibility, corpus, add)
        return {"run": run, "sets": counts}

    def _space_scalar(self, run: str, space: str, field: str) -> Dict[str, float]:
        """{source: measured value} for a named scalar feature of one observer space (O(K))."""
        out: Dict[str, float] = {}
        for fkey in self._members("set:vlab:feat:%s:%s" % (slug(run), slug(space))):
            m = self._meta(fkey)
            src, v = m.get("source"), m.get(field)
            if src is not None and isinstance(v, (int, float)):
                out[self._alias(self._key(src) or src) or src] = float(v)
        return out

    @staticmethod
    def _percentile(vals: List[float], pct: float) -> float:
        if not vals:
            return 0.0
        s = sorted(vals)
        i = max(0, min(len(s) - 1, int(round((pct / 100.0) * (len(s) - 1)))))
        return s[i]

    def _threshold_set(self, run, space, field, setname, pct, side, visibility, corpus, add):
        vals = self._space_scalar(run, space, field)
        if len(vals) < 3:
            return
        thr = self._percentile(list(vals.values()), pct * 100 if pct <= 1 else pct)
        n_added = 0
        for src, v in vals.items():
            hit = v >= thr if side == "high" else v <= thr
            if hit:
                add(setname, self._key(src) or src)
                n_added += 1
        # threshold provenance travels with the Set (§16)
        self._mint("analysis:threshold:%s:%s" % (slug(setname), slug(run)),
                   "[threshold] %s = %s-%.0f%% of %s.%s" % (setname, side, pct * 100 if pct <= 1 else pct,
                                                            space, field),
                   {"concept": "analysis_threshold", "set": setname, "method": "percentile",
                    "percentile": pct * 100 if pct <= 1 else pct, "numeric_threshold": round(thr, 5),
                    "side": side, "observer": space, "feature": field, "run": run, "corpus": corpus,
                    "members": n_added}, visibility)

    def _outlier_set(self, run, space, setname, pct, visibility, corpus, add):
        """Mark artworks whose feature vector is far from the space's centroid (top-(1-pct) by
        distance) — an OUTLIER in that machine sense (§15/§16). Deterministic, bounded."""
        vecs = self._space_vectors(run, space)
        if len(vecs) < 3:
            return
        srcs = sorted(vecs)
        width = max(len(vecs[s]) for s in srcs)
        rows = {s: (vecs[s] + [0.0] * width)[:width] for s in srcs}
        cent = [sum(rows[s][j] for s in srcs) / len(srcs) for j in range(width)]
        dist = {s: sum((rows[s][j] - cent[j]) ** 2 for j in range(width)) ** 0.5 for s in srcs}
        thr = self._percentile(list(dist.values()), pct * 100 if pct <= 1 else pct)
        n_added = 0
        for s, dcur in dist.items():
            if dcur >= thr:
                add(setname, self._key(s) or s)
                n_added += 1
        self._mint("analysis:threshold:%s:%s" % (slug(setname), slug(run)),
                   "[threshold] %s = centroid-distance ≥ %.0f%% (%s space)"
                   % (setname, pct * 100 if pct <= 1 else pct, space),
                   {"concept": "analysis_threshold", "set": setname, "method": "centroid_distance_percentile",
                    "percentile": pct * 100 if pct <= 1 else pct, "numeric_threshold": round(thr, 5),
                    "observer": space, "feature": "feature_vector", "run": run, "corpus": corpus,
                    "members": n_added}, visibility)

    def _first_link(self, key: str, rel: str) -> Optional[str]:
        for dst, r in self.cortex.get_adjacent_links(key, rel):
            return dst
        return None

    # ══ Clustering + projections (§17/§18 — mechanical names, read-only) ══════════

    def op_cluster(self, run: str, k: str = "3", features: str = "", space: str = "") -> Dict[str, Any]:
        """[vlab.cluster] Unsupervised clustering as an ANALYSIS result, represented as SET membership
        (§12/§17). With `space=` (color/geometry/texture/mobilenet/efficientnet/lightweight) it k-means
        the run's works in that feature space → mechanically named `set:analysis:cluster:<space>:<run>:cNN`
        (+ an `analysis:cluster:kmeans:<space>:<run>` descriptor recording method/k/corpus). Without a
        space it falls back to the coarse detection-count bucketing → `set:visual:cluster:NNN`. Phase 1
        must NEVER assign a semantic name to an unsupervised cluster (§17); that is Phase 2. Deterministic,
        reproducible, bounded (pool size)."""
        rmeta = self._meta("vision_run:%s" % slug(run))
        if not rmeta:
            raise ValueError("unknown run '%s'" % run)
        visibility = rmeta.get("visibility", "public")
        kk = max(1, int(k) if str(k).strip().isdigit() else 3)
        if space:
            vecs = self._space_vectors(run, space)
            srcs, X = self._matrix_of(vecs)
            if not srcs:
                return {"run": run, "space": space, "clusters": {}, "note": "no vectors in this space"}
            assign = self._kmeans(srcs, X, kk)
            sizes: Dict[str, int] = {}
            for src, c in assign.items():
                cname = "set:analysis:cluster:%s:%s:c%02d" % (slug(space), slug(run), c + 1)
                self._addset_v(cname, self._key(src) or src, visibility)
                sizes[cname] = sizes.get(cname, 0) + 1
            self._mint("analysis:cluster:kmeans:%s:%s" % (slug(space), slug(run)),
                       "[cluster] kmeans %s over %s (k=%d, %d works)" % (space, run, kk, len(srcs)),
                       {"concept": "analysis_cluster", "method": "kmeans", "k": kk,
                        "feature_space": space, "run": run, "corpus": rmeta.get("source_pool"),
                        "works": len(srcs)}, visibility)
            return {"run": run, "space": space, "k": kk, "clusters": sizes,
                    "note": "mechanically named — semantic naming is Phase 2 (§17)"}
        # feature per source (bounded): total detection count across observers
        by_src: Dict[str, int] = {}
        for okey in self._members("set:vlab:run:%s:obs" % slug(run)):
            src = self._first_link(okey, "vis:observes")
            if not src:
                continue
            by_src[src] = by_src.get(src, 0) + int(self._meta(okey).get("detection_count", 0))
        if not by_src:
            return {"run": run, "clusters": {}, "note": "no observations to cluster"}
        vals = sorted(set(by_src.values()))
        # quantile buckets over the observed density range → kk mechanical clusters
        buckets: Dict[int, str] = {}
        for src, v in by_src.items():
            idx = min(kk - 1, int(vals.index(v) * kk / max(1, len(vals))))
            cname = "set:visual:cluster:%03d" % (idx + 1)
            self._addset_v(cname, self._key(src) or src, visibility)
            buckets[idx + 1] = buckets.get(idx + 1, "")
        sizes = {}
        for src, v in by_src.items():
            idx = min(kk - 1, int(vals.index(v) * kk / max(1, len(vals)))) + 1
            sizes["set:visual:cluster:%03d" % idx] = sizes.get("set:visual:cluster:%03d" % idx, 0) + 1
        return {"run": run, "k": kk, "clusters": sizes,
                "note": "mechanically named — semantic naming is Phase 2 (§17)"}

    def op_project(self, run: str, **kw) -> Dict[str, Any]:
        """[vlab.project] A persisted, reproducible, READ-ONLY projection payload for the GUI
        (§18): as=distribution|scatter|cluster|similarity|comparison. Never mutates the raw source
        or observations; the GUI draws the payload and computes nothing itself."""
        mode = kw.get("as", "distribution")
        space = kw.get("space", "")
        rmeta = self._meta("vision_run:%s" % slug(run))
        if not rmeta:
            raise ValueError("unknown run '%s'" % run)
        if space:                                            # v0.2 — space-aware READ for the Analysis UI
            return self._project_space(run, mode, space, rmeta)
        obs_keys = self._members("set:vlab:run:%s:obs" % slug(run))
        if mode == "distribution":
            hist: Dict[int, int] = {}
            cls_freq: Dict[str, int] = {}
            for okey in obs_keys:
                n = int(self._meta(okey).get("detection_count", 0))
                hist[n] = hist.get(n, 0) + 1
                for d in self.op_detections(self._alias(okey)).get("detections", []):
                    cls_freq[d.get("class")] = cls_freq.get(d.get("class"), 0) + 1
            return {"run": run, "as": "distribution", "detection_count_hist": hist,
                    "class_frequency": dict(sorted(cls_freq.items(), key=lambda t: -t[1]))}
        if mode == "comparison":
            rows = self._matrix_rows(rmeta)
            return {"run": run, "as": "comparison",
                    "points": [{"source": r["source"], "yolov8": r.get("yolov8"),
                                "yolov10": r.get("yolov10"), "agreement": r.get("agreement")}
                               for r in rows]}
        if mode == "scatter":
            pts = []
            for okey in obs_keys:
                src = self._first_link(okey, "vis:observes")
                m = self._meta(okey)
                pts.append({"source": self._alias(src) if src else None,
                            "x": int(m.get("detection_count", 0)), "y": m.get("cronon", 0),
                            "observer": m.get("observer")})
            return {"run": run, "as": "scatter", "points": pts,
                    "axes": {"x": "detection_count", "y": "cronon"}}
        if mode == "cluster":
            return {"run": run, "as": "cluster",
                    "clusters": {c: len(self._members(c)) for c in
                                 ("set:visual:cluster:001", "set:visual:cluster:002",
                                  "set:visual:cluster:003") if self._members(c)}}
        if mode == "similarity":
            return {"run": run, "as": "similarity", "note": "embedding similarity reuses tensor refs (Phase 1.1)"}
        raise ValueError("unknown projection mode '%s'" % mode)

    def _project_space(self, run: str, mode: str, space: str, rmeta: Dict[str, Any]) -> Dict[str, Any]:
        """v0.2 space-aware READ for the Analysis UI (§13/§21) — the SAME projection modes over a
        SELECTED feature space, read-only, bounded (frozen corpus). scatter/pca read the persisted
        PCA coordinates (computing on the fly if the operator has not run vlab.pca yet); cluster reads
        the k-means Set membership; distribution histograms a representative measured feature."""
        if mode in ("scatter", "pca"):
            pm = self._meta("analysis:pca:%s:%s" % (slug(space), slug(run)))
            coords = pm.get("coords") if pm else None
            if not coords:                                   # not precomputed → leading dims of the raw vectors
                coords = {s: (v + [0.0, 0.0])[:2] for s, v in self._space_vectors(run, space).items()}
            pts = [{"source": s, "x": c[0], "y": (c[1] if len(c) > 1 else 0.0)}
                   for s, c in coords.items()]
            return {"run": run, "space": space, "as": "scatter", "points": pts,
                    "axes": {"x": "PC1", "y": "PC2"},
                    "explained_variance_ratio": (pm or {}).get("explained_variance_ratio"),
                    "precomputed": bool(pm)}
        if mode == "cluster":
            desc = self._meta("analysis:cluster:kmeans:%s:%s" % (slug(space), slug(run)))
            kk = int(desc.get("k", 3)) if desc else 3
            clusters = {}
            for c in range(1, kk + 1):
                name = "set:analysis:cluster:%s:%s:c%02d" % (slug(space), slug(run), c)
                members = [self._alias(m) for m in self._members(name)]
                if members:
                    clusters[name] = members
            return {"run": run, "space": space, "as": "cluster", "clusters": clusters,
                    "sizes": {n: len(m) for n, m in clusters.items()},
                    "note": "mechanically named — semantic naming is Phase 2 (§17)"}
        if mode == "distribution":
            field = {"color": "saturation_mean", "geometry": "edge_density",
                     "texture": "entropy"}.get(space, "")
            if field:
                vals = list(self._space_scalar(run, space, field).values())
                bins: Dict[str, int] = {}
                for v in vals:
                    b = "%.1f" % (round(v * 10) / 10.0)
                    bins[b] = bins.get(b, 0) + 1
                return {"run": run, "space": space, "as": "distribution", "feature": field,
                        "histogram": dict(sorted(bins.items()))}
            # embedding spaces have no single scalar — report vector norms instead
            vecs = self._space_vectors(run, space)
            norms = {s: round(sum(x * x for x in v) ** 0.5, 4) for s, v in vecs.items()}
            return {"run": run, "space": space, "as": "distribution", "feature": "vector_norm",
                    "values": norms}
        raise ValueError("space projection mode '%s' not supported (use scatter|pca|cluster|distribution)" % mode)

    def _matrix_rows(self, rmeta: Dict[str, Any]) -> List[Dict[str, Any]]:
        pool = rmeta.get("source_pool")
        run = rmeta.get("run")
        rows = []
        for src_key in self._pool_members(pool):             # bounded (frozen corpus)
            smeta = self._meta(src_key)
            provider = smeta.get("provider", "x")
            object_id = smeta.get("provider_object_id", src_key)
            def obs_meta(observer):
                return self._meta(self._obs_alias(provider, object_id, observer, run))
            y8, y10, tf = obs_meta("yolov8"), obs_meta("yolov10"), obs_meta("tf")
            cmp = self._meta("comparison:vision:%s:yolov8:yolov10" % slug(str(object_id)))
            rows.append({"source": self._alias(src_key),
                         "tf_available": bool(tf and tf.get("status") == "success"),
                         "yolov8": y8.get("detection_count") if y8 else None,
                         "yolov10": y10.get("detection_count") if y10 else None,
                         "agreement": cmp.get("agreement_score") if cmp else None})
        return rows

    def op_matrix(self, run: str) -> Dict[str, Any]:
        """[vlab.matrix] Corpus-level observer comparison matrix (§23): per work, TensorFlow
        availability, YOLOv8/YOLOv10 detection counts, and agreement score. Bounded read over the
        frozen pool (R1). The GUI sorts/filters this; it computes nothing."""
        rmeta = self._meta("vision_run:%s" % slug(run))
        if not rmeta:
            raise ValueError("unknown run '%s'" % run)
        rows = self._matrix_rows(rmeta)
        return {"run": run, "works": len(rows), "rows": rows}

    # ══ v0.2 — multi-axis feature analysis (PCA / cluster / neighbour / cross-observer) ═══════════
    # PCA and clustering are ANALYSIS PROJECTIONS, not observers (§11/§12): they apply ONE analytical
    # operation to ONE selected feature space without changing the source or observations. All reads
    # are O(corpus) over a bounded frozen pool (~100). Coordinates/clusters are valid ONLY within the
    # corpus + feature space + parameters + run that produced them.

    def op_spaces(self, run: str = "") -> Dict[str, Any]:
        """[vlab.spaces] List the selectable analysis feature spaces (§13) and the observers that
        define each. With `run=`, also report how many artworks have a vector in each space."""
        out = []
        for space, fams in _FEATURE_SPACES.items():
            row = {"space": space, "observers": fams,
                   "modality": _SPACE_MODALITY.get(space, "image")}   # image | audio — for the viewer tabs
            if run:
                row["works"] = len(self._space_vectors(run, space))
            out.append(row)
        return {"spaces": out, "count": len(out)}

    def _space_vectors(self, run: str, space: str) -> Dict[str, List[float]]:
        """{source_alias: feature_vector} for a feature space over a run — assembled from the per-
        (run, observer-space) feature membranes (O(K), no scan). For the derived 'lightweight' space
        the Color+Geometry+Texture vectors are concatenated per source (§10); only sources observed
        by ALL required observers are included (a partial vector is not comparable)."""
        fams = _FEATURE_SPACES.get(space)
        if not fams:
            raise ValueError("unknown feature space '%s' (known: %s)"
                             % (space, ", ".join(sorted(_FEATURE_SPACES))))
        per_src: Dict[str, Dict[str, List[float]]] = {}
        for fam in fams:
            for fkey in self._members("set:vlab:feat:%s:%s" % (slug(run), slug(fam))):
                m = self._meta(fkey)
                src, vec = m.get("source"), m.get("feature_vector")
                if src and vec:
                    per_src.setdefault(self._alias(self._key(src) or src) or src, {})[fam] = vec
        out = {}
        for src, got in per_src.items():
            if all(f in got for f in fams):
                out[src] = [float(x) for f in fams for x in got[f]]
        return out

    def op_combine(self, run: str) -> Dict[str, Any]:
        """[vlab.combine] Assemble the DERIVED lightweight feature vector (§10) = Color ⊕ Geometry ⊕
        Texture per artwork, as a new derived feature observation that `vis:derived_from` its three
        originating observations (which are NEVER erased — the derived vector is an analytical
        derivative, not a source fact)."""
        rmeta = self._meta("vision_run:%s" % slug(run))
        if not rmeta:
            raise ValueError("unknown run '%s'" % run)
        visibility = rmeta.get("visibility", "public")
        made = 0
        for src, vec in self._space_vectors(run, "lightweight").items():
            skey = self._key(src)
            smeta = self._meta(src)
            object_id = smeta.get("provider_object_id", src)
            provider = smeta.get("provider", "x")
            falias = "obs:feature:%s:%s:lightweight:%s" % (provider, slug(str(object_id)), slug(run))
            self._mint(falias, "[features] %s lightweight combined" % object_id,
                       {"concept": "vision_feature", "observer": "lightweight", "run": run,
                        "feature_space": "lightweight", "source": src,
                        "feature_vector": [round(x, 5) for x in vec], "derived": True}, visibility)
            self._link_v(falias, src, "vis:observes", visibility)
            self._addset_v("set:vlab:feat:%s:lightweight" % slug(run), self._key(falias), visibility)
            for fam in ("color", "geometry", "texture"):
                self._link_v(falias, "obs:feature:%s:%s:%s:%s"
                             % (provider, slug(str(object_id)), fam, slug(run)),
                             "vis:derived_from", visibility)
            made += 1
        return {"run": run, "combined": made, "space": "lightweight"}

    def _matrix_of(self, vecs: Dict[str, List[float]]):
        """(sources, numpy 2-D array) padded to a common width, or (sources, None) without numpy."""
        n = _np()
        srcs = sorted(vecs)
        if not srcs:
            return srcs, None
        width = max(len(vecs[s]) for s in srcs)
        rows = [(vecs[s] + [0.0] * width)[:width] for s in srcs]
        return srcs, (n.asarray(rows, dtype="float32") if n is not None else rows)

    def op_pca(self, run: str, space: str = "mobilenet", dims: str = "3") -> Dict[str, Any]:
        """[vlab.pca] PCA as an ANALYSIS PROJECTION over one feature space (§11) → per-artwork PC1..PCk
        coordinates, persisted + reproducible as `analysis:pca:<space>:<run>`. Coordinates are valid
        ONLY within this corpus, space, parameters and run. Uses scikit-learn if present, else a NumPy
        SVD; degrades to leading dims without NumPy. Never mutates a source or observation."""
        rmeta = self._meta("vision_run:%s" % slug(run))
        if not rmeta:
            raise ValueError("unknown run '%s'" % run)
        visibility = rmeta.get("visibility", "public")
        kdim = max(1, min(3, int(dims) if str(dims).strip().isdigit() else 3))
        vecs = self._space_vectors(run, space)
        srcs, X = self._matrix_of(vecs)
        coords: Dict[str, List[float]] = {}
        evr: List[float] = []
        if X is not None and len(srcs) >= 2:
            n = _np()
            Xc = X - X.mean(axis=0, keepdims=True)
            _ensure_pkg("sklearn", "scikit-learn")             # operator-free; NumPy-SVD is the floor
            try:
                from sklearn.decomposition import PCA          # pragma: no cover - optional dep
                p = PCA(n_components=min(kdim, Xc.shape[1]))
                Y = p.fit_transform(Xc)
                evr = [round(float(v), 4) for v in p.explained_variance_ratio_]
            except Exception:
                U, S, Vt = n.linalg.svd(Xc, full_matrices=False)
                Y = U[:, :kdim] * S[:kdim]
                tot = float((S ** 2).sum()) or 1.0
                evr = [round(float((S[i] ** 2) / tot), 4) for i in range(min(kdim, len(S)))]
            for i, s in enumerate(srcs):
                coords[s] = [round(float(Y[i][j]), 4) for j in range(min(kdim, Y.shape[1]))]
        else:
            for s in srcs:                                       # numpy-less degrade: leading dims
                coords[s] = [round(float(x), 4) for x in (vecs[s] + [0.0, 0.0, 0.0])[:kdim]]
        alias = "analysis:pca:%s:%s" % (slug(space), slug(run))
        self._mint(alias, "[pca] %s over %s (%d works, %dD)" % (space, run, len(srcs), kdim),
                   {"concept": "analysis_pca", "run": run, "feature_space": space, "dims": kdim,
                    "method": "sklearn|numpy-svd", "works": len(srcs),
                    "explained_variance_ratio": evr, "coords": coords}, visibility)
        return {"projection": alias, "space": space, "run": run, "works": len(srcs),
                "dims": kdim, "explained_variance_ratio": evr, "coords": coords}

    def _kmeans(self, srcs, X, k):
        """{source: cluster_index} — scikit-learn KMeans if present, else a deterministic NumPy
        Lloyd's (fixed init), else a stable hash bucket. Bounded, reproducible."""
        n = _np()
        if X is None or len(srcs) == 0:
            return {s: _stable_hash(s) % k for s in srcs}
        _ensure_pkg("sklearn", "scikit-learn")                 # operator-free; NumPy Lloyd's is the floor
        try:
            from sklearn.cluster import KMeans                  # pragma: no cover - optional dep
            lab = KMeans(n_clusters=min(k, len(srcs)), n_init=10, random_state=0).fit_predict(X)
            return {srcs[i]: int(lab[i]) for i in range(len(srcs))}
        except Exception:
            pass
        kk = min(k, len(srcs))
        cent = X[:kk].copy()                                     # deterministic init: first kk points
        assign = [0] * len(srcs)
        for _ in range(10):
            for i in range(len(srcs)):
                d = ((X[i] - cent) ** 2).sum(axis=1)
                assign[i] = int(d.argmin())
            for c in range(kk):
                pts = X[[i for i in range(len(srcs)) if assign[i] == c]]
                if len(pts):
                    cent[c] = pts.mean(axis=0)
        return {srcs[i]: assign[i] for i in range(len(srcs))}

    def op_neighbors(self, source: str, run: str, space: str = "mobilenet", k: str = "5") -> Dict[str, Any]:
        """[vlab.neighbors] Nearest neighbours of one artwork within a feature space by cosine
        similarity (§13/§24) — the neighbourhood structure that differs between observer spaces.
        Read-only, O(corpus)."""
        vecs = self._space_vectors(run, space)
        target = self._alias(self._key(source) or source) or source
        if target not in vecs:
            # try matching by object slug
            hit = [s for s in vecs if slug(str(source)) in slug(str(s))]
            if hit:
                target = hit[0]
        if target not in vecs:
            return {"source": source, "space": space, "neighbors": [], "note": "no vector in this space"}
        kk = int(k) if str(k).strip().isdigit() else 5
        tv = vecs[target]

        def cos(a, b):
            dot = sum(x * y for x, y in zip(a, b))
            na = sum(x * x for x in a) ** 0.5 or 1.0
            nb = sum(y * y for y in b) ** 0.5 or 1.0
            return dot / (na * nb)
        sims = [(s, round(cos(tv, v), 4)) for s, v in vecs.items() if s != target]
        sims.sort(key=lambda t: -t[1])
        return {"source": target, "space": space, "run": run,
                "neighbors": [{"source": s, "similarity": c} for s, c in sims[:kk]]}

    def op_views(self, source: str, run: str = "") -> Dict[str, Any]:
        """[vlab.views] Same Artwork, Different Machine Views (§14): every observer's perspective on
        ONE artwork side by side — SOURCE, COLOR, GEOMETRY, TEXTURE, MOBILENET, EFFICIENTNET, YOLOv8,
        YOLOv10 — for COMPARISON, never synthesized into a single verdict. Read-only."""
        smeta = self._source_meta(source)
        provider = smeta.get("provider", "x")
        object_id = smeta.get("provider_object_id", source)
        views = []
        for oid in ("color", "geometry", "texture", "mobilenet", "efficientnet", "tf",
                    "yolov8", "yolov10"):
            # search the observer's observation across runs (prefer the named run)
            runs = [run] if run else []
            found = None
            for rr in runs or [""]:
                cand = self._obs_alias(provider, object_id, oid, rr or self._latest_run_for(oid, provider, object_id))
                m = self._meta(cand)
                if m:
                    found = (cand, m); break
            if not found:
                # fall back: scan the source's obs set for this observer
                for okey in self._members("set:vlab:src:%s:obs" % slug(str(object_id))):
                    m = self._meta(okey)
                    if m.get("observer") == oid:
                        found = (self._alias(okey), m); break
            if found:
                al, m = found
                fm = self._meta("obs:feature:%s:%s:%s:%s"
                                % (provider, slug(str(object_id)), oid, slug(m.get("run", ""))))
                views.append({"observer": oid, "kind": self._roster()[oid].kind if oid in self._roster() else "?",
                              "status": m.get("status"), "detections": m.get("detection_count"),
                              "feature_space": fm.get("feature_space"),
                              "degraded": m.get("degraded")})
            else:
                views.append({"observer": oid, "status": "not_observed"})
        return {"source": source, "object_id": object_id, "views": views,
                "note": "comparison across machine senses — NOT a single verdict (§14)"}

    def _latest_run_for(self, oid, provider, object_id):
        return ""

    def op_crossobs(self, run: str, space_a: str = "color", space_b: str = "geometry",
                    k: str = "5") -> Dict[str, Any]:
        """[vlab.crossobs] Machine disagreement REDEFINED (§15): not YOLOv8-vs-YOLOv10, but how the
        STRUCTURE of the collection changes between two observer SPACES — the divergence of each
        artwork's neighbourhood from space A to space B (mean Jaccard of the top-k neighbour sets:
        low overlap = the two machine senses organize the corpus differently). Read-only, O(corpus)."""
        va, vb = self._space_vectors(run, space_a), self._space_vectors(run, space_b)
        common = sorted(set(va) & set(vb))
        kk = int(k) if str(k).strip().isdigit() else 5

        def topk(vecs, target):
            tv = vecs[target]
            def cos(a, b):
                dot = sum(x * y for x, y in zip(a, b))
                na = sum(x * x for x in a) ** 0.5 or 1.0
                nb = sum(y * y for y in b) ** 0.5 or 1.0
                return dot / (na * nb)
            sims = [(s, cos(tv, vecs[s])) for s in vecs if s != target]
            sims.sort(key=lambda t: -t[1])
            return {s for s, _ in sims[:kk]}
        rows = []
        divs = []
        for s in common:
            na, nb = topk(va, s), topk(vb, s)
            inter = len(na & nb); union = len(na | nb) or 1
            jac = inter / union
            div = round(1.0 - jac, 3)
            divs.append(div)
            rows.append({"source": s, "neighbour_divergence": div,
                         "shared_neighbours": inter})
        rows.sort(key=lambda r: -r["neighbour_divergence"])
        mean_div = round(sum(divs) / len(divs), 3) if divs else 0.0
        return {"run": run, "space_a": space_a, "space_b": space_b, "k": kk,
                "works": len(common), "mean_neighbour_divergence": mean_div,
                "most_divergent": rows[:10],
                "note": "how the collection reorganizes when the machine's mode of seeing changes (§15)"}
