#!/usr/bin/env python3
"""
vlab_audio_eval.py — audio is a second machine sense on the SAME observation/analysis machinery.

The Source Viewer's Audio-analysis modality: audio observers produce the same bounded feature_vector
the image observers do, so the corpus analysis (spaces / pca / cluster / neighbours / crossobs) is
shared unchanged — only the resolver differs (waveform, not pixels). librosa backs MFCC/chroma/rhythm;
the spectral space is a NumPy-FFT floor that needs no heavy dep. This also GENERALIZES vlab to observe
ANY source pool (a source.acquire/import pool with media locators), not just vlab.source.add artworks.

Pins:
  1. the four audio observers are registered kind=feature, their spaces tagged modality=audio;
  2. degradation-first: the spectral floor computes REAL values from numpy alone; mfcc/chroma/rhythm
     degrade to a right-shape mock when librosa is absent — never a crash;
  3. vlab observes an ACQUIRED audio pool end-to-end (generic locator), the audio feature space
     populates, pca + cluster run, and the per-item observation carries the concrete measurements.

Run:  python app/test/vlab_audio_eval.py     (exit 0 = pass)
"""
import hashlib
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"   # force degradation for the librosa observers
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def main():
    import numpy as np
    import app.concepts.vision_lab as V

    # deterministic synthetic waveforms (distinct per clip) → the spectral floor yields real structure
    def fake_audio(loc):
        seed = abs(hash(loc)) % 997
        f = 110 + seed % 400
        y = np.sin(np.linspace(0, f * 2 * np.pi, 22050)).astype("float32") * (0.3 + (seed % 7) / 10.0)
        return y, 22050
    V._resolve_audio_array = fake_audio

    from app.concepts.vision_lab import (_default_observers, _SPACE_MODALITY,
                                                SpectralObserver, MFCCObserver,
                                                YAMNetObserver, PANNsObserver, BirdNETObserver)

    rost = _default_observers()
    # four measuring senses + three "learned ears" (pretrained models), all degradation-first
    for name in ("spectral", "mfcc", "chroma", "rhythm", "yamnet", "panns", "birdnet"):
        check("audio observer '%s' registered kind=feature (modality=audio)" % name,
              name in rost and rost[name].kind == "feature" and rost[name].modality == "audio",
              rost[name].modality if name in rost else "absent")
    check("all audio spaces tagged modality=audio",
          all(_SPACE_MODALITY.get(s) == "audio" for s in
              ("spectral", "mfcc", "chroma", "rhythm", "yamnet", "panns", "birdnet")))

    # the learned ears degrade cleanly (right-shape mock) when their model/lib is absent — never a crash
    for name, obs in (("yamnet", YAMNetObserver("yamnet")), ("panns", PANNsObserver("panns")),
                      ("birdnet", BirdNETObserver("birdnet"))):
        r = obs.observe({"locator": "x"})
        check("learned ear '%s' degrades cleanly (mock, no crash) with no model" % name,
              r.get("status") == "success" and r["features"].get("degraded") is True
              and len(r.get("feature_vector") or []) > 0, str(r.get("status")))

    # degradation-first
    sr = SpectralObserver("spectral").observe({"locator": "x"})
    check("spectral floor computes REAL values from numpy alone (no librosa)",
          sr["status"] == "success" and not sr["features"].get("degraded")
          and "spectral_centroid_hz" in sr["features"], str(sr["features"].get("degraded")))
    mr = MFCCObserver("mfcc").observe({"locator": "x"})
    check("mfcc degrades to a right-shape mock when librosa is absent (13-dim, no crash)",
          mr["status"] == "success" and mr["features"].get("degraded") is True
          and len(mr["feature_vector"]) == 13, str(len(mr.get("feature_vector") or [])))

    # end-to-end over an ACQUIRED audio pool (generic locator → vlab observes any pool)
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_aud_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def d(m, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": m,
                        "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
        return r.get("result") if "result" in r else {"__error__": r.get("error")}

    d("source.register", {"provider": "snd", "name": "snd"})
    d("source.pool.create", {"name": "snd", "source": "source:src:snd"})
    d("source.acquire", {"source": "source:src:snd", "rule": "t",
                         "records": [{"id": "clip%02d" % i, "url": "http://x/clip%02d.wav" % i} for i in range(12)],
                         "pool": "source:pool:snd:v1"})
    d("source.pool.freeze", {"pool": "source:pool:snd:v1"})

    mods = d("source.modalities", {"pool": "source:pool:snd:v1"}).get("modalities") or {}
    check("the acquired pool advertises the audio modality", mods.get("audio") is True and mods.get("image") is False, str(mods))

    d("vlab.run.new", {"pool": "source:pool:snd:v1", "observers": "spectral", "run": "a1"})
    ex = d("vlab.run.execute", {"run": "a1"})
    check("vlab observes the ACQUIRED audio pool (generic locator → any pool)",
          ex.get("sources") == 12 and ex.get("observed") == 12, str(ex))

    sp = {s["space"]: s for s in d("vlab.spaces", {"run": "a1"}).get("spaces", [])}
    check("the spectral audio space is populated (a vector per clip)",
          sp.get("spectral", {}).get("works") == 12 and sp.get("spectral", {}).get("modality") == "audio",
          str(sp.get("spectral", {})))
    pca = d("vlab.pca", {"run": "a1", "space": "spectral", "dims": "3"})
    cl = d("vlab.cluster", {"run": "a1", "space": "spectral", "k": "3"})
    check("pca + cluster run over the audio feature space (shared analysis machinery)",
          pca.get("works") == 12 and any(str(n).startswith("set:analysis:cluster:spectral:") for n in (cl.get("clusters") or {})),
          "pca=%s clusters=%d" % (pca.get("works"), len(cl.get("clusters") or {})))

    o = d("vlab.observation", {"id": "obs:vision:x:source_item_snd_clip00:spectral:a1"})
    f = o.get("features") or {}
    check("per-item observation carries the concrete audio measurements",
          "spectral_centroid_hz" in f and "rms" in f and not f.get("degraded"),
          str([kk for kk in f if kk != "feature_vector"][:4]))

    # ── the Source Viewer's Audio-analysis pane contract: vlab.runs (pool filter → modality/spaces) ──
    runs = d("vlab.runs", {"pool": "source:pool:snd:v1"})
    r0 = (runs.get("runs") or [{}])[0]
    check("vlab.runs lists the pool's run tagged modality=audio (the Audio tab's index)",
          runs.get("count") == 1 and r0.get("run") == "a1" and r0.get("modalities") == ["audio"]
          and "spectral" in (r0.get("spaces") or []), str(r0.get("modalities")))

    # ── vlab.reindex recovers a run whose observations exist but predate the run-index (persisted cell) ──
    from app.concepts.vision_lab import VisionLabConcept, slug
    _vl = VisionLabConcept(k.manager.get_session("admin")); _core = _vl._nuc.core
    _rk = _vl._key("vision_run:a1")
    _core.remove_from_collection("set:vlab:pool:%s:runs" % slug("source:pool:snd:v1"), _rk)
    _core.remove_from_collection("set:vlab:runs", _rk)
    gone = d("vlab.runs", {"pool": "source:pool:snd:v1"}).get("count")
    d("vlab.reindex", {"run": "a1"})
    back = d("vlab.runs", {"pool": "source:pool:snd:v1"}).get("count")
    check("vlab.reindex recovers an unindexed (pre-index) run so vlab.runs finds it again",
          gone == 0 and back == 1, "gone=%s back=%s" % (gone, back))

    # ── vlab.item: every machine sense's honest measurements of ONE item (the individual-observation view) ──
    it = d("vlab.item", {"source": "source:item:snd:clip00", "run": "a1"})
    obs = {o2.get("observer"): o2 for o2 in it.get("observations") or []}
    check("vlab.item gathers one item's per-observer feature rows (individual-observation view)",
          it.get("count") == 1 and "spectral" in obs
          and "spectral_centroid_hz" in ((obs.get("spectral") or {}).get("features") or {}),
          str(sorted(obs)))

    print("\nRESULT:", "PASS" if not _fails else "FAIL — " + ", ".join(_fails))
    return 1 if _fails else 0


if __name__ == "__main__":
    sys.exit(main())
