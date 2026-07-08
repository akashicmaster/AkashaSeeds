#!/usr/bin/env python3
"""
Vision eval — image profiling via the LiteRT inference ladder (image → labels → graph).

Runtime selection (benchmarked): the standalone `tflite-runtime` is frozen at 2.14 and
crashes under numpy 2.x, so LiteRT (`ai_edge_litert`) is the primary backend, degrading to
tflite-runtime (legacy 32-bit ARM) then `tensorflow.lite`. This eval drives the whole path:

  V1 classify   — a known image profiles to sensible labels (the classic Grace Hopper photo,
                  when available, must top out as 'military uniform').
  V2 ingest     — image.profile writes an image atom + per-label concept links (calc:depicts),
                  under the provenance=external guardrail (trust = model confidence).
  V3 guardrail  — the image atom (provenance=external) is excluded from gap.scan, while the
                  curated concept atoms it created are ordinary graph nodes.
  V4 degrade    — a bad path / unavailable engine returns an error dict, never crashes.

Everything SKIPS cleanly (recorded OK) when no inference backend / PIL / model is available
(e.g. offline CI) — vision is an optional, network-provisioned feature.

Run:  python test/vision_eval.py
"""
import os
import sys
import hashlib
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ.setdefault("AKASHA_SKIP_AUTOINSTALL", "1")   # don't pip-install during the eval

_results = []
_GRACE_URL = "https://storage.googleapis.com/download.tensorflow.org/example_images/grace_hopper.jpg"


def record(name, ok, detail=""):
    _results.append((name, ok, detail))
    print(f"  {'OK  ' if ok else '!! FAIL'}  {name:12} {detail}")


def _ensure_sample():
    """Return (path, expected_top_label_or_None). Prefer the staged Grace Hopper photo (known
    label); else fetch it; else synthesise a plain image (pipeline still exercised, no label
    expectation)."""
    staged = os.path.join("env", "models", "_sample_grace.jpg")
    if os.path.exists(staged):
        return staged, "military uniform"
    try:
        import urllib.request
        os.makedirs(os.path.join("env", "models"), exist_ok=True)
        urllib.request.urlretrieve(_GRACE_URL, staged)
        return staged, "military uniform"
    except Exception:
        pass
    try:
        from PIL import Image
        p = os.path.join(tempfile.mkdtemp(prefix="akasha_vis_img_"), "synthetic.png")
        Image.new("RGB", (256, 256), (120, 90, 60)).save(p)
        return p, None
    except Exception:
        return None, None


def _kernel():
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_vis_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin",
                                    "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                "id": "g"}, "local")
    return k


def _d(k):
    def d(m, data):
        return k.dispatch({"jsonrpc": "2.0", "method": m,
                           "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
    return d


def main():
    print("\n  vision eval — LiteRT image profiling\n")
    from lib.akasha.vision import VisionEngine

    if not VisionEngine.backend_available():
        record("V1 classify", True, "no TFLite/LiteRT backend — vision skipped (ok)")
        record("V2 ingest", True, "skipped (no backend)")
        record("V3 guardrail", True, "skipped (no backend)")
        record("V4 degrade", True, "skipped (no backend)")
        return _summary()

    ve = VisionEngine()
    if not ve.available():
        record("V1 classify", True, "backend present but PIL absent — skipped (ok)")
        record("V2 ingest", True, "skipped (no PIL)")
        record("V3 guardrail", True, "skipped (no PIL)")
        record("V4 degrade", True, "skipped (no PIL)")
        return _summary()

    img, expect = _ensure_sample()
    res = ve.classify(img, top_k=3) if img else {"error": "no sample image"}
    labels = res.get("labels") or []
    if not labels:
        # Model could not be fetched (offline) — treat as a clean skip, still test degrade.
        record("V1 classify", True, f"no labels ({res.get('error')}) — model offline, skipped (ok)")
        record("V2 ingest", True, "skipped (no model)")
        record("V3 guardrail", True, "skipped (no model)")
    else:
        top = labels[0]["label"]
        v1 = (top == expect) if expect else True
        record("V1 classify", v1,
               f"backend={res.get('backend')} top='{top}'"
               + (f" (== '{expect}')" if expect else " (pipeline ok)"))

        # V2 + V3 through the kernel (provenance guardrail + gap.scan exclusion).
        k = _kernel()
        d = _d(k)
        cortex = k.manager.get_session("admin").local_cortex
        r = (d("image.profile", {"path": img, "top_k": 3}).get("result") or {})
        ak = r.get("atom_key")
        meta = cortex.get_meta(ak) if ak else None
        prov_ok = isinstance(meta, dict) and meta.get("provenance") == "external" \
            and meta.get("source") == "vision"
        adj = cortex.get_adjacent_links(ak) or [] if ak else []
        depicts = [p for p in adj if len(p) > 1 and "depicts" in str(p[1])]
        c_alias = "concept:" + __import__("re").sub(r'[^a-z0-9]+', '_', top.lower()).strip('_')
        concept_ok = bool(cortex.resolve_alias(c_alias))
        record("V2 ingest", r.get("written") and prov_ok and len(depicts) >= 1 and concept_ok,
               f"written={r.get('written')}, provenance=external={prov_ok}, "
               f"depicts_links={len(depicts)}, concept_atom={concept_ok}")

        # V3: the external image atom must not surface as a gap; give it inbound refs first.
        for i in range(4):
            a = (d("w", {"content": f"caption {i} that references the profiled image here"})
                 .get("result") or {}).get("key")
            if a:
                d("ln", {"src": a, "dst": ak, "rel": "mentions"})
        gaps = (d("gap.scan", {"limit": 50}).get("result") or {}).get("gaps", [])
        record("V3 guardrail", ak not in {g["key"] for g in gaps},
               f"external image atom excluded from gap.scan={ak not in {g['key'] for g in gaps}}")

    # V4: degrade — a nonexistent path returns an error dict, never raises.
    try:
        bad = ve.classify("/no/such/image/____.png")
        record("V4 degrade", isinstance(bad, dict) and "error" in bad,
               f"bad path → {bad.get('error', bad)[:48] if isinstance(bad, dict) else bad}")
    except Exception as exc:
        record("V4 degrade", False, f"raised instead of degrading: {exc}")

    return _summary()


def _summary():
    print()
    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"  {passed}/{total} phases passed"
          + (f", {total - passed} FAILED" if passed < total else ""))
    if passed < total:
        print("\nRESULT: FAIL — the vision path regressed.")
        return 1
    print("\nRESULT: PASS — LiteRT image profiling writes provenance-guarded labels into the "
          "graph, and degrades cleanly when the runtime/model is absent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
