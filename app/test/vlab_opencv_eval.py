#!/usr/bin/env python3
"""
vlab_opencv_eval.py — OpenCV is a first-class machine viewpoint (a new feature space).

The Visual Curation Lab's v0.2 multi-axis principle: many small, explicitly DIFFERENT machine
senses observe one corpus (§13/§24). This adds OpenCV (classical CV: Canny edges, ORB keypoints,
external contours, Shi-Tomasi corners, Hough lines, Laplacian focus) as its own `opencv` space,
degradation-first (opencv-python-headless installed on demand; mock vector of the right shape if
absent, so it never breaks the lab).

Pins:
  1. the `opencv` observer is registered, kind=feature, and `opencv` is a selectable feature space;
  2. run.execute populates the opencv space with a vector per work;
  3. §24: the opencv space produces a DIFFERENT structure than color (co-clustering disagreement) —
     it is a genuinely distinct machine sense, not a duplicate;
  4. a missing OpenCV never breaks the lab (degradation-first is inherited from FeatureObserver).

Run:  python app/test/vlab_opencv_eval.py     (exit 0 = pass)
"""
import hashlib
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


def _cluster_map(core, clusters):
    """{member_key: cluster_name} read off the nucleus collections (op_cluster returns {set: count})."""
    m = {}
    for name in (clusters or {}):
        try:
            for s in (core.get_collection_members(name) or []):
                m[s] = name
        except Exception:
            pass
    return m


def _coclustering_disagrees(a, b):
    keys = [x for x in a if x in b]
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            x, y = keys[i], keys[j]
            if (a[x] == a[y]) != (b[x] == b[y]):
                return True
    return False


def main():
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_vcv_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def d(method, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
        return r.get("result") if "result" in r else {"__error__": r.get("error")}

    # (1) registered, kind=feature, selectable space
    obs = {o["observer"]: o for o in d("vlab.observers", {}).get("observers", [])}
    check("opencv observer registered", "opencv" in obs, str(sorted(obs)))
    check("opencv observer declares kind=feature",
          obs.get("opencv", {}).get("kind") == "feature", str(obs.get("opencv")))

    N = 12
    POOL = "vc:opencv:v1"
    srcs = []
    for i in range(N):
        r = d("vlab.source.add", {"pool": POOL, "object_id": "art-%02d" % i,
                                  "image": "art_%02d.png" % i, "scheme": "remote",
                                  "title": "Work %d" % i, "provider": "cma"})
        srcs.append(r.get("source"))

    d("vlab.run.new", {"pool": POOL, "observers": "color,opencv", "run": "m1"})
    ex = d("vlab.run.execute", {"run": "m1"})
    check("run.execute observed the corpus with the opencv observer",
          ex.get("sources") == N and ex.get("observed", 0) >= N * 2, str(ex))

    spaces = {s["space"]: s for s in d("vlab.spaces", {"run": "m1"}).get("spaces", [])}
    check("the opencv feature space is populated (a vector per work)",
          spaces.get("opencv", {}).get("works", 0) == N,
          {s: spaces.get(s, {}).get("works") for s in ("color", "opencv")})

    # the Machine-Observation view reads the CONCRETE extraction result — vlab.observation returns the
    # named measurements + feature_vector the observer produced (not just 'computed').
    obs = d("vlab.observation", {"id": "obs:vision:cma:art_00:opencv:m1"})
    f = obs.get("features") or {}
    check("vlab.observation returns the opencv measurements (edge_density/keypoints/…) + vector",
          isinstance(f, dict) and "edge_density" in f and f.get("feature_space") == "opencv"
          and len(f.get("feature_vector") or []) >= 6,
          "keys=%s" % [k for k in f if k != "feature_vector"][:6])

    # (3) §24 — opencv structure differs from color
    cc = d("vlab.cluster", {"run": "m1", "space": "color", "k": "3"})
    co = d("vlab.cluster", {"run": "m1", "space": "opencv", "k": "3"})
    check("opencv clustering is SET membership (set:analysis:cluster:opencv:*)",
          any(str(n).startswith("set:analysis:cluster:opencv:") for n in (co.get("clusters") or {})),
          str(list(co.get("clusters", {}))[:1]))
    _core = k.manager.shared_nucleus.core
    check("§24: opencv space != color space (different machine sense → different structure)",
          _coclustering_disagrees(_cluster_map(_core, cc.get("clusters", {})),
                                  _cluster_map(_core, co.get("clusters", {}))))

    print("\nRESULT:", "PASS" if not _fails else "FAIL — " + ", ".join(_fails))
    return 1 if _fails else 0


if __name__ == "__main__":
    sys.exit(main())
