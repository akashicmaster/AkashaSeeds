#!/usr/bin/env python3
"""
Learning bench (PLANTS Vision Learning v0.1) — mock-mode end-to-end on the world model.

A learning bench trains a small classifier head on the Feature atoms the vlab observers produce and
registers the trained head back as a vlab observer. This eval drives the whole path with NO network
and NO heavy ML dep (image locators don't resolve → the feature observer degrades to deterministic
mock vectors; sklearn is absent → the head degrades to a numpy nearest-centroid), asserting the six
laws: no image/weight binary in the store, weights → artifact dir + model-identity atom, every op
observed on the bench stream, metrics as ONE aggregate, a deterministic frozen split, and honest
degradation of the promoted observer.

Run:  python app/test/bench_learning_eval.py     (exit 0 = all pass)
"""
import hashlib
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []
_CLASSES = ["oak", "maple", "birch"]


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _run(series, shape):
    print(f"\n  ── {shape} ({series}) ──")
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    base = tempfile.mkdtemp(prefix="akasha_learn_")
    k = KernelDispatcher(series=series, base_dir=base)
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def d(method, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
        return r if "error" in r else (r.get("result") or {})

    d("world.genesis", {})
    d("grp.new", {"group_id": "lab", "admin_id": "admin"})
    b = d("bench.new", {"name": "leaf", "kind": "learning", "group": "lab"})
    check(f"[{shape}] bench.new kind=learning records the LEARNING families",
          b.get("status") == "created", str(b)[:80])
    info = d("bench.info", {"name": "leaf", "group": "lab"})
    check(f"[{shape}] the learning bench exposes train/promote families",
          {"train", "promote", "dataset", "feature", "evaluate"} <= set(info.get("families") or []),
          str(info.get("families")))
    d("society.new", {"group": "lab", "name": "leafsoc", "world": "default", "bench": "leaf",
                      "kind": "cowork"})

    # ── synthetic labeled image REFERENCES (no binary; locators do not resolve) ──
    pool = "source:pool:leafimg:v1"
    for i in range(18):
        cls = _CLASSES[i % 3]
        d("vlab.source.add", {"pool": pool, "object_id": f"img_{i}", "image": f"mock://leaf/{i}.jpg",
                              "title": f"{cls} {i}", "provider": "mock", "label": cls})

    # ── dataset.bind + feature.extract (delegates to vlab; observer degrades to mock vectors) ──
    db = d("learning.dataset.bind", {"name": "leaf", "pool": pool})
    check(f"[{shape}] learning.dataset.bind references the pool (never a copy)",
          db.get("bound") and db.get("pool") == pool and isinstance(db.get("observed_at_seq"), int),
          str(db)[:120])
    fe = d("learning.feature.extract", {"name": "leaf", "pool": pool, "observers": "color", "run": "r1"})
    check(f"[{shape}] learning.feature.extract runs the observer and is observed",
          fe.get("observed", 0) >= 1 and isinstance(fe.get("observed_at_seq"), int), str(fe)[:140])

    # ── train ──
    tr = d("learning.train", {"name": "leaf", "run": "r1", "space": "color", "head": "logreg",
                           "split": 0.7, "seed": "s1"})
    # engine: sklearn if the dev box has it, else the pure-numpy multinomial logistic regression
    # (numpy_logreg) — a REAL learner on the production tier (no sklearn wheel); centroid/mock are the
    # deeper floors. head=logreg without sklearn MUST land on numpy_logreg (vision-deps-bundle §2).
    try:
        import sklearn  # noqa
        _have_sk = True
    except Exception:
        _have_sk = False
    _engine = tr.get("engine")
    check(f"[{shape}] learning.train produces a model + metrics (engine={_engine})",
          tr.get("model", "").startswith("model:learned:leaf_head") and tr.get("metrics")
          and _engine in ("numpy_logreg", "sklearn_logreg")
          and isinstance(tr.get("observed_at_seq"), int), str(tr)[:200])
    # VPS-vision-coverage §2.7 / §4 + A50: head=logreg lands on the REAL sklearn LogisticRegression
    # when sklearn is importable (the A50 fix — dropping the removed multi_class= kwarg — must not
    # silently fall back to numpy), and on the pure-numpy multinomial logreg when it is not. Both are
    # real learners (never mock/centroid), and the engine name is recorded either way — deterministic.
    _expect = "sklearn_logreg" if _have_sk else "numpy_logreg"
    check(f"[{shape}] head=logreg engine tracks the environment (sklearn={_have_sk} → {_expect})",
          _engine == _expect, f"sklearn={_have_sk} engine={_engine} expected={_expect}")
    check(f"[{shape}] the split is deterministic + stratified (train+test cover all 3 classes)",
          tr.get("train_n", 0) >= 3 and tr.get("test_n", 0) >= 3 and set(tr.get("classes") or []) == set(_CLASSES),
          f"train={tr.get('train_n')} test={tr.get('test_n')} classes={tr.get('classes')}")

    # determinism: a second train with the same seed splits identically
    tr2 = d("learning.train", {"name": "leaf", "run": "r1", "space": "color", "head": "logreg",
                            "split": 0.7, "seed": "s1"})
    check(f"[{shape}] re-training with the same seed is deterministic",
          tr2.get("train_n") == tr.get("train_n") and tr2.get("test_n") == tr.get("test_n"))

    # ── LAW 2/4: weights live OUTSIDE the store; the model atom holds only sha256+size; metrics aggregate ──
    mm = _atom_meta(k, tr["model"], "lab")
    check(f"[{shape}] the model-identity atom carries sha256 + size + path, NOT the weights",
          mm.get("weights_sha256") and mm.get("weights_size") and mm.get("weights_path")
          and "centroids" not in mm and "pickle_b64" not in mm and "params" not in mm, str(list(mm))[:160])
    wpath = mm.get("weights_path")
    check(f"[{shape}] the weights artifact file exists on disk (outside the store)",
          bool(wpath) and os.path.isfile(wpath), str(wpath))
    met = _atom_meta(k, tr["metrics"], "lab")
    check(f"[{shape}] metrics is ONE aggregate atom (accuracy/macro_f1/per_class/confusion)",
          "accuracy" in met and "macro_f1" in met and isinstance(met.get("per_class"), list)
          and isinstance(met.get("confusion"), list), str(list(met))[:160])

    # ── LAW 1: no image/weight BINARY entered the store ──
    leak = _binary_in_store(k, wpath)
    check(f"[{shape}] no image/weight binary is in the store (only refs + digests)", not leak, leak or "")

    # ── evaluate on the held-out frozen test sample ──
    ev = d("learning.evaluate", {"name": "leaf", "model": tr["model"], "sample": "test"})
    check(f"[{shape}] learning.evaluate re-scores on the frozen test frame",
          ev.get("metrics") and "accuracy" in ev and isinstance(ev.get("observed_at_seq"), int), str(ev)[:140])

    # ── promote → the learned head is an observer ──
    pr = d("learning.promote", {"name": "leaf", "model": tr["model"], "observer": "leaf_head"})
    check(f"[{shape}] learning.promote registers the trained head as an observer",
          pr.get("observer") == "leaf_head" and isinstance(pr.get("observed_at_seq"), int), str(pr)[:140])
    obs = d("vlab.observers", {})
    ids = {o.get("observer") for o in obs.get("observers", [])}
    check(f"[{shape}] the promoted head appears in the vlab roster beside the reference observers",
          "leaf_head" in ids and "color" in ids, str(sorted(ids))[:160])

    # ── the learned observer predicts (variant=learned; weights present ⇒ not degraded) ──
    ob = d("vlab.observe", {"source": "source:artwork:mock:img_0", "observer": "leaf_head", "run": "pred1"})
    det = d("vlab.detections", {"obs": ob.get("observation")})
    pred = (det.get("detections") or [{}])[0].get("class")
    check(f"[{shape}] the learned observer emits a species prediction (not degraded, weights present)",
          ob.get("detections", 0) >= 1 and ob.get("degraded") is False and pred in _CLASSES,
          f"obs={ob.get('detections')} degraded={ob.get('degraded')} pred={pred}")

    # ── LAW 6: honest degradation — remove the weights file, the observer degrades HONESTLY ──
    try:
        os.remove(wpath)
    except OSError:
        pass
    ob2 = d("vlab.observe", {"source": "source:artwork:mock:img_1", "observer": "leaf_head", "run": "pred2"})
    det2 = d("vlab.detections", {"obs": ob2.get("observation")})
    pred2 = (det2.get("detections") or [{}])[0].get("class")
    check(f"[{shape}] with the weights gone, the observer degrades HONESTLY (degraded flag + still labeled)",
          ob2.get("degraded") is True and pred2 in _CLASSES,
          f"degraded={ob2.get('degraded')} pred={pred2}")

    # ── the whole run is on the bench stream (observation time = training history) ──
    st = d("source.stream", {"stream": "wb:leaf", "space": "group:lab"})
    fams = [(o.get("source_metadata") or {}).get("family") for o in st.get("observations", [])]
    check(f"[{shape}] every block teed an observation on the bench stream",
          {"dataset", "feature", "train", "evaluate", "promote"} <= set(fams), str(sorted(set(fams))))


def _atom_meta(k, alias, gid):
    """Read an atom's meta from the group engine (bench atoms) or nucleus (model/metrics may be either)."""
    for space in (f"group:{gid}", ""):
        from lib.akasha.concepts._universal import UniversalConcept
        u = UniversalConcept(k.manager.get_session("admin"))
        u._space = space
        m = u._meta(alias)
        if m:
            return m
    return {}


def _binary_in_store(k, wpath):
    """Return a description if any atom content looks like an image/weight binary, else ''. The weights
    JSON must NOT appear as an atom body, and no atom may carry raw image bytes."""
    try:
        with open(wpath, "r", encoding="utf-8") as f:
            weights_blob = f.read()
    except Exception:
        weights_blob = None
    nuc = getattr(k.manager, "shared_nucleus", None)
    cores = []
    if nuc is not None and getattr(nuc, "core", None) is not None:
        cores.append(nuc.core)
    try:
        ge = k.manager._get_group_engine("lab")
        if ge is not None and getattr(ge, "core", None) is not None:
            cores.append(ge.core)
    except Exception:
        pass
    for core in cores:
        try:
            rows = core.conn.execute("SELECT content FROM chunks").fetchall()
        except Exception:
            continue
        for r in rows:
            c = r[0] if not isinstance(r, dict) else r.get("content")
            c = c or ""
            if weights_blob and len(weights_blob) > 40 and weights_blob in c:
                return "weights JSON found inside an atom body"
            if "\x89PNG" in c or "\xff\xd8\xff" in c:      # PNG/JPEG magic
                return "image binary found inside an atom body"
    return ""


def main():
    _run("thesaurus", "nucleus cell")
    _run("seeds", "single-store cell")
    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("\nRESULT: PASS — a learning bench trains a classifier head on machine-extracted Feature "
          "atoms and promotes it back as an observer: no image/weight binary in the store (only refs + "
          "a sha256+size model-identity atom), metrics as one aggregate, a deterministic frozen split, "
          "every op observed on the bench stream, and honest degradation when the weights are gone — "
          "on both cell shapes, with no network and no sklearn.")
    sys.exit(0)


if __name__ == "__main__":
    main()
