#!/usr/bin/env python3
"""
vlab_detectors_eval.py — the lightweight detector/observer roster (the YOLO-front-stage).

The user's direction: "as many installable machine senses as possible; LiteRT should also stand on
its own." This adds, degradation-first, alongside color/geometry/texture/opencv:
  - litert          — a LiteRT (MobileNet classifier) semantic-emphasis FEATURE space;
  - litert_detect    — LiteRT SSD-MobileNet OBJECT detection (works on the current OpenCV-5/3.14 cell);
  - cvdnn_face       — OpenCV DNN (YuNet) face detection (cv2.dnn is present even in OpenCV 5.0);
  - cascade          — OpenCV Haar cascades (runs where OpenCV<5 is installable; guarded otherwise).
YOLO (heavy torch) stays deferred.

Pins (must hold with no models fetched / restricted host, so the CI/offline contract is exercised):
  1. every new observer is registered with the right kind (litert=feature, the three detectors=detector);
  2. each contributes a selectable feature SPACE (litert/objdet/face/cascade);
  3. degradation-first: with AKASHA_SKIP_AUTOINSTALL + no models, observe() NEVER raises — it returns a
     clean status (a detector reports failure_type=backend_unavailable; the litert feature space returns
     a right-shape mock vector). A missing dep/model never breaks the lab (§18).

Run:  python app/test/vlab_detectors_eval.py     (exit 0 = pass)
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"   # force degradation — no model fetch, no heavy install
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def main():
    import numpy as np
    import app.concepts.vision_lab as V
    # a deterministic image of the requested size (so observers take their real/degrade path, no network)
    V._resolve_image_array = lambda loc, size=(64, 64): (
        np.random.RandomState(3).rand(size[1], size[0], 3) * 255).astype("uint8")
    from app.concepts.vision_lab import _default_observers, _FEATURE_SPACES

    rost = _default_observers()
    for name, kind in (("litert", "feature"), ("litert_detect", "detector"),
                       ("cascade", "detector"), ("cvdnn_face", "detector")):
        check("%s registered as kind=%s" % (name, kind),
              name in rost and rost[name].kind == kind,
              rost[name].kind if name in rost else "absent")

    for sp in ("litert", "objdet", "cascade", "face"):
        check("feature space '%s' is selectable" % sp, sp in _FEATURE_SPACES, str(sorted(_FEATURE_SPACES)))

    # degradation-first: observe() never raises; detectors report a clean unavailable, litert mock-vectors
    for name in ("litert_detect", "cascade", "cvdnn_face"):
        try:
            r = rost[name].observe({"locator": "art.png"})
            ok = isinstance(r, dict) and r.get("status") in ("success", "failed")
        except Exception as exc:
            ok = False; r = {"exc": str(exc)}
        check("%s degrades cleanly (no crash, clean status)" % name, ok, str(r.get("status") or r))

    try:
        lr = rost["litert"].observe({"locator": "art.png"})
        vec = lr.get("feature_vector") or []
        ok = lr.get("status") == "success" and len(vec) == 12
    except Exception as exc:
        ok = False; vec = []; lr = {"exc": str(exc)}
    check("litert feature space returns a right-shape vector even without the model (mock, 12-dim)",
          ok, "len=%d degraded=%s" % (len(vec), (lr.get('features', {}) or {}).get('degraded')))

    print("\nRESULT:", "PASS" if not _fails else "FAIL — " + ", ".join(_fails))
    return 1 if _fails else 0


if __name__ == "__main__":
    sys.exit(main())
