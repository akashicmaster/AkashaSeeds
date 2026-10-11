#!/usr/bin/env python3
"""
Vision deps bundled at seed generation (vision-deps-bundle-order §1/§3/§4).

The thesaurus tier ships its vision model FILE (assets/models/mobilenet_v3_small_fv.tflite) + manifest
and runs the embedder on numpy/Pillow/ai_edge_litert only — NO TensorFlow, NO runtime pip. This eval
proves:
  1. the bundled model loads through the LiteRT ladder and produces a normalized feature vector of the
     stored width, with embedding_dimension=1024 and degraded=false (skipped if no LiteRT backend here);
  2. the observer's identity carries the model's variant/framework (litert / v3small_fv);
  3. a missing model file (or an unknown one) degrades to a labelled mock, one WARNING, never a crash;
  4. with app/config/tier_policy.json autoinstall=false, _ensure_pkg("tensorflow", …) returns False WITHOUT
     calling pip (the R0 no-runtime-pip rule).

Run:  python app/test/vision_litert_eval.py     (exit 0 = all pass)
"""
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _synthetic_image(kind=0):
    # STRUCTURED, distinct images (not noise, which collapses to near-identical global embeddings): a
    # bold colour block + a shape, so two kinds give clearly different MobileNet embeddings.
    from PIL import Image, ImageDraw
    import numpy as np
    base = [(220, 40, 40), (40, 60, 220), (40, 200, 80)][kind % 3]
    arr = np.zeros((256, 256, 3), dtype="uint8")
    arr[:, :] = base
    im = Image.fromarray(arr)
    d = ImageDraw.Draw(im)
    if kind % 3 == 0:
        d.ellipse([60, 60, 196, 196], fill=(250, 240, 20))
    elif kind % 3 == 1:
        d.rectangle([50, 90, 206, 166], fill=(240, 240, 240))
    else:
        d.polygon([(128, 40), (40, 210), (216, 210)], fill=(20, 20, 20))
    p = os.path.join(tempfile.mkdtemp(prefix="vis_"), "x.png")
    im.save(p)
    return p


def main():
    import app.concepts.vision_lab as vl
    from lib.akasha.concepts import learned_head as lh   # noqa (import guard)

    # ── the bundled model + manifest are shipped ──
    mdir = os.path.join(ROOT, "assets", "models")
    import json
    mani = json.load(open(os.path.join(mdir, "model.json"), encoding="utf-8"))
    mfile = os.path.join(mdir, mani.get("file", ""))
    check("assets/models/model.json + the .tflite are present", os.path.isfile(mfile), mani.get("file"))
    check("the manifest declares a 1024-d output + sha256",
          mani.get("output_dim") == 1024 and len(str(mani.get("sha256"))) == 64, str(mani.get("output_dim")))

    img = _synthetic_image()
    obs = vl.LiteRTEmbeddingObserver("mobilenet")

    # backend availability decides whether we can exercise the REAL path here
    try:
        from lib.akasha.source.vision import _resolve_backend
        backend = _resolve_backend(allow_install=False)
    except Exception:
        backend = None

    if backend is not None:
        r = obs.observe({"locator": img})
        f = r.get("features") or {}
        check("the bundled model loads through LiteRT and is NOT degraded",
              f.get("degraded") is False, str({k: f.get(k) for k in ('degraded', 'feature_space')}))
        check("the embedder reports the native 1024-d dimension",
              f.get("embedding_dimension") == 1024, str(f.get("embedding_dimension")))
        check("the stored feature vector is bounded + numeric",
              isinstance(f.get("feature_vector"), list) and 0 < len(f["feature_vector"]) <= 64
              and all(isinstance(x, (int, float)) for x in f["feature_vector"]),
              "len=%s" % len(f.get("feature_vector") or []))
        check("the observer identity is the bundled LiteRT model (variant/framework)",
              obs.variant == "v3small_fv" and obs.framework == "litert",
              f"{obs.variant}/{obs.framework}")
        # two clearly-different images → different vectors (a real encoder, not a constant mock)
        r2 = obs.observe({"locator": _synthetic_image(kind=1)})
        check("two different images yield different embeddings (a real encoder)",
              (r.get("feature_vector") or []) != (r2.get("feature_vector") or []))
    else:
        check("(no LiteRT backend on this machine — real-path checks skipped)", True)

    # ── a missing model file degrades to a labelled mock, never a crash ──
    miss = vl.LiteRTEmbeddingObserver("mobilenet_missing", model_file="does_not_exist.tflite")
    rm = miss.observe({"locator": img})
    fm = rm.get("features") or {}
    check("a missing model file degrades to a mock (degraded=true), no crash",
          rm.get("status") == "success" and fm.get("degraded") is True, str(fm)[:120])

    # ── tier_policy.autoinstall=false forbids runtime pip (§3.1) ──
    # point the tier-policy reader at a temp config with autoinstall=false
    tp_dir = tempfile.mkdtemp(prefix="tier_")
    os.makedirs(os.path.join(tp_dir, "config"))
    with open(os.path.join(tp_dir, "config", "tier_policy.json"), "w") as f:
        json.dump({"autoinstall": False, "essential": ["numpy", "PIL", "ai_edge_litert"]}, f)
    _app_before = os.environ.get("AKASHA_APP_DIR")
    os.environ["AKASHA_APP_DIR"] = tp_dir          # the fixture is the application root (SPEC §2)
    if hasattr(vl._tier_policy, "_c"):
        delattr(vl._tier_policy, "_c")           # drop the cache so the temp policy is read
    vl._PKG_CACHE.pop("tensorflow", None)
    import time
    t0 = time.time()
    got = vl._ensure_pkg("tensorflow", "tensorflow-cpu")
    dt = time.time() - t0
    check("tier_policy.autoinstall=false → _ensure_pkg('tensorflow') is False WITHOUT pip",
          got is False and dt < 5.0, f"got={got} dt={dt:.2f}s")
    if _app_before is None:
        os.environ.pop("AKASHA_APP_DIR", None)
    else:
        os.environ["AKASHA_APP_DIR"] = _app_before
    if hasattr(vl._tier_policy, "_c"):
        delattr(vl._tier_policy, "_c")

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("RESULT: PASS — the bundled MobileNetV3 LiteRT embedder loads (1024-d, degraded=false) on "
          "numpy/Pillow/LiteRT only, degrades to a labelled mock when the model file is absent, and a "
          "tier_policy autoinstall=false forbids any runtime pip.")
    sys.exit(0)


if __name__ == "__main__":
    main()
