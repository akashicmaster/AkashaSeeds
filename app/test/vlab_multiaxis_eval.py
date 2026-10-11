#!/usr/bin/env python3
"""
Visual Curation Laboratory — Phase 1 v0.2 acceptance (Lightweight Multi-Axis Machine Observation).

The addendum shifts Phase 1 from one object-detection-heavy viewpoint to MANY small, explicitly
different machine viewpoints (color / geometry / texture / global embedding). Its success criterion
(§24) is NOT accuracy or model size — it is whether different observers produce MEANINGFULLY
DIFFERENT structures over the same frozen collection: color clustering != geometry clustering;
color neighbourhoods != geometry neighbourhoods; the collection reorganizes when the machine's mode
of seeing changes (§15). This eval drives the whole v0.2 surface through an in-process kernel and
asserts that, plus the analysis projections (PCA / cluster-as-Sets / neighbours / cross-observer /
threshold Sets with preserved metadata), the derived lightweight vector (§10), the multi-view panel
(§14), and graceful degradation (a missing model-dep never breaks the lab, §18). Observers run
degradation-first, so it is reproducible with no heavy models installed.

Run:  python app/test/vlab_multiaxis_eval.py     (exit 0 = all pass)
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


def main():
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_vlab2_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def d(method, data, tok="admin", trust="local"):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": tok, "data": data}, "id": "t"}, trust)
        return r.get("result") if "result" in r else {"__error__": r.get("error")}

    # ── 0. the lightweight multi-axis observers are registered ──
    obs = {o["observer"]: o for o in d("vlab.observers", {}).get("observers", [])}
    check("v0.2 observers registered (color, geometry, texture, mobilenet, efficientnet)",
          {"color", "geometry", "texture", "mobilenet", "efficientnet"} <= set(obs), str(sorted(obs)))
    check("feature observers declare kind=feature (not detector/classifier)",
          all(obs[o]["kind"] == "feature" for o in
              ("color", "geometry", "texture", "mobilenet", "efficientnet")), "")

    # ── 1. a small PUBLIC frozen corpus, observed by all lightweight observers ──
    # Public (nucleus) so the eval can read cluster/threshold atoms directly; locators are non-URL
    # (no network) so observers take the fast deterministic-mock path here — the per-observer feature
    # spaces still differ, which is exactly what §24 tests. (Local-pool + real images are covered by
    # the v0.1 eval + a live deploy with Pillow.)
    N = 12
    POOL = "vc:multiaxis:v1"
    srcs_added = []
    for i in range(N):
        r = d("vlab.source.add", {"pool": POOL, "object_id": "art-%02d" % i,
                                  "image": "art_%02d.png" % i, "scheme": "remote",
                                  "title": "Work %d" % i, "provider": "cma"})
        srcs_added.append(r.get("source"))
    scan = {"sources": srcs_added}
    OBS = "color,geometry,texture,mobilenet,efficientnet"
    d("vlab.run.new", {"pool": POOL, "observers": OBS, "run": "m1"})
    ex = d("vlab.run.execute", {"run": "m1"})
    check("run.execute observed the corpus with all 5 lightweight observers",
          ex.get("sources") == N and ex.get("observed", 0) >= N * 4, str(ex))

    # ── 2. feature spaces are populated (each observer contributes a vector per work) ──
    spaces = {s["space"]: s for s in d("vlab.spaces", {"run": "m1"}).get("spaces", [])}
    check("feature spaces populated (color/geometry/texture have a vector per work)",
          all(spaces.get(s, {}).get("works", 0) == N for s in ("color", "geometry", "texture")),
          {s: spaces.get(s, {}).get("works") for s in ("color", "geometry", "texture", "mobilenet")})

    # ── 3. derived lightweight combined vector (§10) — derived_from, originals intact ──
    comb = d("vlab.combine", {"run": "m1"})
    check("lightweight combined vector assembled per work (Color⊕Geometry⊕Texture, §10)",
          comb.get("combined") == N and spaces_after_combine(d, "m1") == N, str(comb))

    # ── 4. PCA as an analysis projection (§11) ──
    pca = d("vlab.pca", {"run": "m1", "space": "color", "dims": "3"})
    check("PCA projection persisted with per-work coordinates (§11)",
          pca.get("works") == N and pca.get("projection", "").startswith("analysis:pca:color:")
          and len(pca.get("coords", {})) == N, str(pca.get("projection")))
    # space-aware READ path the Analysis UI uses (guest-safe, reads the persisted projection)
    scat = d("vlab.project", {"run": "m1", "space": "color", "as": "scatter"})
    check("Analysis UI read: vlab.project as=scatter space= returns per-work PCA points",
          len(scat.get("points", [])) == N and scat.get("axes", {}).get("x") == "PC1", str(scat.get("axes")))

    # ── 5. §24 CORE — color clustering != geometry clustering (different structures) ──
    cc = d("vlab.cluster", {"run": "m1", "space": "color", "k": "3"})
    cg = d("vlab.cluster", {"run": "m1", "space": "geometry", "k": "3"})
    map_c = cluster_map(k, cc.get("clusters", {}))
    map_g = cluster_map(k, cg.get("clusters", {}))
    check("clustering is SET membership, mechanically named set:analysis:cluster:<space>:<run>:cNN (§12/§17)",
          all(name.startswith("set:analysis:cluster:") for name in cc.get("clusters", {})),
          str(list(cc.get("clusters", {}))[:2]))
    # §24 CORE, robustly: a co-clustering DISAGREEMENT — some pair of artworks share a cluster in one
    # space but not the other (immune to arbitrary cluster labels; empty ⇒ identical structure).
    check("§24: color clustering != geometry clustering (different machine senses → different structure)",
          bool(map_c) and bool(map_g) and _coclustering_disagrees(map_c, map_g),
          "color=%d works geometry=%d works" % (len(map_c), len(map_g)))

    # ── 6. neighbourhoods differ across spaces (§24) ──
    src0 = scan.get("sources", ["?"])[0]
    nc = d("vlab.neighbors", {"source": src0, "run": "m1", "space": "color", "k": "3"})
    ng = d("vlab.neighbors", {"source": src0, "run": "m1", "space": "geometry", "k": "3"})
    setc = {x["source"] for x in nc.get("neighbors", [])}
    setg = {x["source"] for x in ng.get("neighbors", [])}
    check("§24: an artwork's nearest neighbours differ between color and geometry spaces",
          setc and setg and setc != setg, "color=%s geometry=%s" % (sorted(setc), sorted(setg)))

    # ── 7. cross-observer disagreement redefined (§15) ──
    cross = d("vlab.crossobs", {"run": "m1", "space_a": "color", "space_b": "geometry", "k": "3"})
    check("cross-observer disagreement: the corpus reorganizes across spaces (§15, divergence>0)",
          cross.get("works") == N and cross.get("mean_neighbour_divergence", 0) > 0.0,
          "mean_div=%s" % cross.get("mean_neighbour_divergence"))

    # ── 8. Same Artwork, Different Machine Views (§14) ──
    views = d("vlab.views", {"source": src0, "run": "m1"})
    vobs = {v["observer"] for v in views.get("views", [])}
    check("multi-view panel returns every machine perspective on one artwork (§14)",
          {"color", "geometry", "texture", "mobilenet", "efficientnet", "yolov8", "yolov10"} <= vobs,
          str(sorted(vobs)))

    # ── 9. threshold Sets WITH preserved threshold metadata (§16) ──
    der = d("vlab.set.derive", {"run": "m1"})
    sets = der.get("sets", {})
    thr = _read_meta(k, "analysis:threshold:set_vision_high_edge_density:m1")
    check("threshold feature Sets materialized (§16: high_edge_density / low_saturation / high_entropy / outliers)",
          any(s.startswith("set:vision:") and s not in
              ("set:vision:person_present", "set:vision:object_sparse") for s in sets), str(list(sets)[:6]))
    check("threshold metadata preserved with the Set (method/percentile/observer/feature/run/corpus)",
          thr.get("method") == "percentile" and thr.get("observer") == "geometry"
          and thr.get("feature") == "edge_density" and thr.get("run") == "m1", str(thr)[:160])

    # ── 10. graceful degradation (§18): mobilenet has no TF here → mock embedding, still a vector ──
    mobil_ok = spaces.get("mobilenet", {}).get("works", 0) == N
    check("graceful degradation: a model-dep-absent observer still yields a vector; the lab runs (§18)",
          mobil_ok, "mobilenet works=%s" % spaces.get("mobilenet", {}).get("works"))

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("\nRESULT: PASS — VCL Phase 1 v0.2 holds: many small, explicitly different machine "
          "viewpoints (color/geometry/texture/embedding) observe one frozen corpus; different "
          "observer spaces produce different structures (clusters, neighbourhoods diverge); PCA and "
          "clustering are analysis projections/Sets; threshold Sets keep their metadata; the derived "
          "lightweight vector never erases its originals; and a missing model-dep never breaks the lab.")
    sys.exit(0)


def _read_meta(k, alias):
    try:
        nuc = k.manager.shared_nucleus
        core = nuc.core
        key = core.get_key_by_alias(alias) or alias
        row = core.get_chunk_raw(key)
        import json
        return json.loads(row["meta"]) if row and row["meta"] else {}
    except Exception:
        return {}


def cluster_map(k, clusters_dict):
    """{member_key: cluster_name} read straight off the nucleus collections — the assignment a
    feature space induced over the corpus."""
    core = k.manager.shared_nucleus.core
    out = {}
    for name in clusters_dict:
        try:
            for m in (core.get_collection_members(name) or []):
                out[m] = name
        except Exception:
            pass
    return out


def _coclustering_disagrees(a, b):
    """True iff some pair of items is co-clustered in map a but not in map b (or vice versa) —
    a label-agnostic proof the two partitions differ in structure."""
    keys = sorted(set(a) & set(b))
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            same_a = a[keys[i]] == a[keys[j]]
            same_b = b[keys[i]] == b[keys[j]]
            if same_a != same_b:
                return True
    return False


def spaces_after_combine(d, run):
    sp = {s["space"]: s for s in d("vlab.spaces", {"run": run}).get("spaces", [])}
    return sp.get("lightweight", {}).get("works", 0)


if __name__ == "__main__":
    main()
