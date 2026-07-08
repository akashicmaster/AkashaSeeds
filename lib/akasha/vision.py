"""
Vision inference — self-owned image profiling for Akasha (image → classification labels).

The edge/IoT inference runtime, chosen by a benchmark (see docs): the standalone
`tflite-runtime` is frozen at 2.14 and CRASHES under numpy 2.x, so the primary backend is
**LiteRT** (`ai_edge_litert`, the official TensorFlow-Lite successor: numpy-2 clean, modern
Python, aarch64 / Apple-Silicon / x86_64 wheels, XNNPACK CPU delegate). The interpreter API
is identical across LiteRT, tflite-runtime and `tensorflow.lite`, so one code path degrades
across all three; if none is importable (or numpy/PIL/model absent) `classify` returns an
error dict and the caller degrades — nothing here ever crashes boot.

The model is a quantised MobileNet classifier, fetched on demand and cached under
`env/models/` (never shipped, never loaded at boot). Feeds the same graph as the rest of the
semantic layer: labels are written as atoms carrying the provenance=external guardrail, so
model-inferred content can neither poison the learned model nor masquerade as curated
ontology (ASI06).
"""
import io
import os
import re
import zipfile
import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("Akasha.Vision")

try:
    import numpy as _np
    _HAS_NUMPY = True
except Exception:
    _np = None
    _HAS_NUMPY = False

# Backend probe result: None = not tried, False = none available, else (name, Interpreter).
_BACKEND: Any = None

# Default model: MobileNetV1 (quantised, 224²) + its 1001-label map. A small (~4 MB), stable,
# widely-mirrored classifier — enough to prove the path; swap via env for a better one.
_MODEL_URL = os.environ.get(
    "AKASHA_VISION_MODEL_URL",
    "https://storage.googleapis.com/download.tensorflow.org/models/tflite/"
    "mobilenet_v1_1.0_224_quant_and_labels.zip")
_MODEL_FILE = "mobilenet_v1_1.0_224_quant.tflite"
_LABELS_FILE = "labels_mobilenet_quant_v1_224.txt"


def _resolve_backend(allow_install: bool = True) -> Optional[Tuple[str, Any]]:
    """Return (backend_name, Interpreter class) for the best available TFLite runtime, or
    None. Ladder: LiteRT → tflite-runtime → tensorflow.lite. Optionally lazy-installs LiteRT
    (respecting AKASHA_SKIP_AUTOINSTALL) on first use — on demand, never at boot."""
    global _BACKEND
    if _BACKEND is not None:
        return _BACKEND or None

    def _try_imports():
        try:
            from ai_edge_litert.interpreter import Interpreter          # LiteRT (primary)
            return ("ai_edge_litert", Interpreter)
        except Exception:
            pass
        try:
            from tflite_runtime.interpreter import Interpreter          # legacy 32-bit ARM
            return ("tflite_runtime", Interpreter)
        except Exception:
            pass
        try:
            from tensorflow.lite import Interpreter                     # full TF (dev boxes)
            return ("tensorflow.lite", Interpreter)
        except Exception:
            pass
        return None

    found = _try_imports()
    if found is None and allow_install and not os.environ.get("AKASHA_SKIP_AUTOINSTALL"):
        try:
            import subprocess
            import sys
            logger.info("[Vision] Installing LiteRT (ai-edge-litert) on demand…")
            subprocess.run([sys.executable, "-m", "pip", "install", "--quiet",
                            "ai-edge-litert"], check=False, timeout=300)
            found = _try_imports()
        except Exception as exc:
            logger.warning("[Vision] LiteRT install failed (non-fatal): %s", exc)

    _BACKEND = found if found else False
    if found:
        logger.info("[Vision] inference backend: %s", found[0])
    return _BACKEND or None


class VisionEngine:
    """Classify images into labels via a quantised MobileNet on the LiteRT ladder.
    Self-owned, dependency-graceful: unavailable → classify() returns {'error': …}."""

    def __init__(self, models_dir: Optional[str] = None):
        self.models_dir = models_dir or os.path.join(os.getcwd(), "env", "models")
        self._interp = None
        self._in = None
        self._out = None
        self._labels: List[str] = []
        self._backend_name: Optional[str] = None

    # ── availability ────────────────────────────────────────────────────────────
    @staticmethod
    def backend_available(allow_install: bool = False) -> bool:
        """True if any TFLite interpreter backend is importable (no install probe by
        default, so a cheap check never triggers a network pip)."""
        return _HAS_NUMPY and _resolve_backend(allow_install=allow_install) is not None

    def available(self) -> bool:
        """Backend + numpy + PIL importable. Model is fetched lazily, so not required here."""
        if not (_HAS_NUMPY and self.backend_available()):
            return False
        try:
            import PIL  # noqa: F401
            return True
        except Exception:
            return False

    # ── model management (on demand, cached under env/models) ─────────────────────
    def _ensure_model(self) -> Optional[Tuple[str, List[str]]]:
        model_path = os.path.join(self.models_dir, _MODEL_FILE)
        labels_path = os.path.join(self.models_dir, _LABELS_FILE)
        if not (os.path.exists(model_path) and os.path.exists(labels_path)):
            if not self._download_model():
                return None
        if not (os.path.exists(model_path) and os.path.exists(labels_path)):
            return None
        labels = [l.strip() for l in open(labels_path, encoding="utf-8")]
        return model_path, labels

    def _download_model(self) -> bool:
        """Fetch + unzip the model bundle into env/models. Network; graceful on failure."""
        try:
            import urllib.request
            os.makedirs(self.models_dir, exist_ok=True)
            logger.info("[Vision] fetching model bundle: %s", _MODEL_URL)
            req = urllib.request.Request(_MODEL_URL, headers={"User-Agent": "AkashaVision/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                blob = resp.read()
            with zipfile.ZipFile(io.BytesIO(blob)) as z:
                for name in z.namelist():
                    base = os.path.basename(name)
                    if base in (_MODEL_FILE, _LABELS_FILE):
                        with z.open(name) as src, \
                                open(os.path.join(self.models_dir, base), "wb") as dst:
                            dst.write(src.read())
            return True
        except Exception as exc:
            logger.warning("[Vision] model download failed (non-fatal): %s", exc)
            return False

    def _load(self) -> bool:
        if self._interp is not None:
            return True
        backend = _resolve_backend()
        if backend is None:
            return False
        ready = self._ensure_model()
        if ready is None:
            return False
        model_path, labels = ready
        try:
            name, Interpreter = backend
            itp = Interpreter(model_path=model_path)
            itp.allocate_tensors()
            self._interp = itp
            self._in = itp.get_input_details()[0]
            self._out = itp.get_output_details()[0]
            self._labels = labels
            self._backend_name = name
            return True
        except Exception as exc:
            logger.warning("[Vision] interpreter load failed (non-fatal): %s", exc)
            return False

    # ── image loading (local path / URL / raw bytes) ──────────────────────────────
    @staticmethod
    def _load_image(src, size: Tuple[int, int]):
        from PIL import Image
        if isinstance(src, (bytes, bytearray)):
            img = Image.open(io.BytesIO(src))
        elif isinstance(src, str) and re.match(r"^https?://", src):
            import urllib.request
            req = urllib.request.Request(src, headers={"User-Agent": "AkashaVision/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                img = Image.open(io.BytesIO(resp.read()))
        else:
            img = Image.open(src)
        return img.convert("RGB").resize(size)

    # ── inference ─────────────────────────────────────────────────────────────────
    def classify(self, src, top_k: int = 5) -> Dict[str, Any]:
        """src = local path | http(s) URL | raw bytes. Returns
        {labels:[{label,score}], backend, model} or {'error': …} (never raises)."""
        if not _HAS_NUMPY:
            return {"error": "numpy unavailable"}
        if not self._load():
            return {"error": "vision backend/model unavailable (offline or no runtime)"}
        try:
            _, h, w, _ = self._in["shape"]
            arr = _np.asarray(self._load_image(src, (int(w), int(h))))
        except Exception as exc:
            return {"error": f"image load failed: {str(exc)[:120]}"}
        try:
            dtype = self._in["dtype"]
            x = arr.astype(dtype)
            if dtype in (_np.float32, _np.float16):     # float model → normalise to [-1,1]
                x = (arr.astype(_np.float32) - 127.5) / 127.5
            x = _np.expand_dims(x, 0)
            self._interp.set_tensor(self._in["index"], x)
            self._interp.invoke()
            out = self._interp.get_tensor(self._out["index"])[0]
            # Dequantise a uint8 output to comparable scores.
            scale, zero = self._out.get("quantization", (0.0, 0)) or (0.0, 0)
            scores = (out.astype(_np.float32) - zero) * scale if scale else out.astype(_np.float32)
            order = _np.argsort(scores)[::-1][:max(1, top_k)]
            labels = [{"label": self._clean(self._labels[int(i)]),
                       "score": round(float(scores[int(i)]), 4)}
                      for i in order if int(i) < len(self._labels)]
            return {"labels": labels, "backend": self._backend_name, "model": _MODEL_FILE}
        except Exception as exc:
            return {"error": f"inference failed: {str(exc)[:120]}"}

    @staticmethod
    def _clean(label: str) -> str:
        """MobileNet labels sometimes carry an index prefix / synonyms — take the first."""
        lab = re.sub(r"^\d+\s*[:\-]?\s*", "", (label or "").strip())
        return lab.split(",")[0].strip()
