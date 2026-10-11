"""
Learned classifier head — a tiny, portable classifier trained on machine-extracted feature vectors
(the PLANTS Vision Learning experiment, B4/B5). It is deliberately backend-agnostic and
degradation-first, exactly like the vlab observers:

    scikit-learn (logreg / mlp)  →  a pure-numpy multinomial logistic regression  →  a numpy
    nearest-centroid floor  →  a stdlib mock

The head is serialized as ONE small JSON file (the "weights artifact"): it lives OUTSIDE the atom
store (a bench artifact dir), and the store holds only a model-identity atom with its sha256 + size
(the binary-never-in-the-store law). This module has NO Akasha imports, so both the trainer
(`bench_learning.py`) and the promoted vlab observer load it without a circular dependency.

A head is a plain dict: {engine, feature_space, classes, params}. `predict` is pure and needs no
Akasha context — the observer calls it at observe time, the trainer at evaluate time.
"""
import hashlib
import json
import logging
import math
import os
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("Akasha.LearnedHead")
_sklearn_warned = set()

# S2-h — the learner KINDS that actually train a model (sklearn, else the numpy multinomial logistic
# regression). Any other `head=` would silently fall through to the centroid / majority mock, so
# learning.train refuses an unknown kind and sweep.def validates its grid `head` values against this set.
# (`mlp` degrades to the numpy logistic model when sklearn is absent — still a real fit, honestly
# labeled by `engine`; `linear`/`ridge` are NOT implemented and must not be swept as if they were.)
KINDS = ("logreg", "mlp")


def _sklearn_warn(kind: str, exc: Exception) -> None:
    """A50 — log ONCE per (kind) why sklearn was skipped, instead of the old silent `return None` that
    hid a constructor TypeError (`multi_class=` removed in sklearn 1.7+) behind a numpy fallback."""
    if kind in _sklearn_warned:
        return
    _sklearn_warned.add(kind)
    logger.warning("[learned_head] sklearn %s unavailable: %s: %s — falling back to numpy_logreg",
                   kind, type(exc).__name__, str(exc)[:160])


def _np():
    try:
        import numpy as _n
        return _n
    except Exception:
        return None


def _sklearn(kind: str):
    """Return an untrained sklearn estimator for `kind`, or None if sklearn is absent OR the
    constructor raises. A50: `multi_class="auto"` was deprecated in sklearn 1.5 and REMOVED in 1.7+ —
    it raised `TypeError: unexpected keyword argument 'multi_class'`, the bare `except` swallowed it,
    and every train silently fell to numpy even where sklearn was installed. Drop the parameter
    (multinomial is the default) and LOG any remaining constructor failure (never a silent None)."""
    try:
        if kind == "mlp":
            from sklearn.neural_network import MLPClassifier
            return MLPClassifier(hidden_layer_sizes=(64,), max_iter=300, random_state=0)
        from sklearn.linear_model import LogisticRegression
        return LogisticRegression(max_iter=1000)
    except Exception as exc:
        _sklearn_warn(kind, exc)
        return None


# ── fit ────────────────────────────────────────────────────────────────────────────
def _numpy_logreg(X: List[List[float]], y: List[str], classes: List[str],
                  seed: int = 0, iters: int = 400, lr: float = 0.5, l2: float = 1e-4) -> Dict[str, Any]:
    """Multinomial (softmax) logistic regression in pure numpy — the REAL `logreg` learner when
    scikit-learn is absent (the production tier ships numpy/Pillow/LiteRT only, no sklearn wheel).
    L2-regularized, full-batch gradient descent, a FIXED iteration count, seeded init, features
    standardized (per-dim mean/std) for stable descent — so a run is deterministic and reproducible.
    This is `engine=numpy_logreg`, NOT a mock: it fits real weights."""
    n = _np()
    Xa = n.asarray(X, dtype="float64")
    mu = Xa.mean(axis=0)
    sd = Xa.std(axis=0)
    sd = n.where(sd == 0.0, 1.0, sd)
    Xs = (Xa - mu) / sd
    m, d = Xs.shape
    cidx = {c: i for i, c in enumerate(classes)}
    K = len(classes)
    Y = n.zeros((m, K))
    for i, lbl in enumerate(y):
        Y[i, cidx[str(lbl)]] = 1.0
    rng = n.random.RandomState(seed)
    W = rng.normal(0.0, 0.01, size=(d, K))
    b = n.zeros(K)
    for _ in range(int(iters)):
        Z = Xs @ W + b
        Z -= Z.max(axis=1, keepdims=True)
        E = n.exp(Z)
        P = E / E.sum(axis=1, keepdims=True)
        G = (P - Y) / m
        W -= lr * (Xs.T @ G + l2 * W)
        b -= lr * G.sum(axis=0)
    return {"engine": "numpy_logreg", "dim": d, "classes": list(classes),
            "params": {"W": W.round(6).tolist(), "b": b.round(6).tolist(),
                       "mu": mu.round(6).tolist(), "sd": sd.round(6).tolist(),
                       "iters": int(iters), "seed": int(seed)}}


def fit(X: List[List[float]], y: List[str], kind: str = "logreg", seed: int = 0) -> Dict[str, Any]:
    """Fit a head on features X (list of equal-length float vectors) + labels y. Tries sklearn for
    kind in {logreg, mlp}; then a pure-numpy multinomial logistic regression (a REAL learner — the
    production-tier path, no sklearn wheel); then a numpy nearest-centroid classifier; then a stdlib
    majority-class mock. Returns the head dict; `engine` records which path ran (honest degradation)."""
    classes = sorted(set(str(c) for c in y))
    dim = len(X[0]) if X else 0
    n = _np()
    est = _sklearn(kind) if kind in ("logreg", "mlp") else None
    if est is not None and n is not None and len(classes) >= 2 and len(X) >= len(classes):
        try:
            est.fit(n.asarray(X, dtype="float64"), list(map(str, y)))
            import base64
            import pickle
            blob = base64.b64encode(pickle.dumps(est)).decode("ascii")
            return {"engine": f"sklearn_{kind}", "dim": dim, "classes": list(est.classes_),
                    "params": {"pickle_b64": blob}}
        except Exception:
            pass  # degrade to the numpy learner
    # numpy multinomial logistic regression — the real `logreg`/`mlp` engine without sklearn. `mlp`
    # falls back here too, recording `requested=mlp` (an MLP needs sklearn/torch; a linear model is the
    # honest, deterministic stand-in on the production tier).
    if kind in ("logreg", "mlp") and n is not None and len(classes) >= 2 and len(X) >= len(classes) and dim:
        try:
            head = _numpy_logreg(X, y, classes, seed=seed)
            if kind == "mlp":
                head["params"]["requested"] = "mlp"
            return head
        except Exception:
            pass  # degrade to the centroid floor
    # numpy nearest-centroid (a genuine learner, deterministic, no heavy deps)
    if n is not None and classes and dim:
        cents: Dict[str, List[float]] = {}
        for c in classes:
            rows = [X[i] for i in range(len(X)) if str(y[i]) == c]
            if rows:
                cents[c] = n.asarray(rows, dtype="float64").mean(axis=0).round(6).tolist()
        if cents:
            return {"engine": "numpy_centroid", "dim": dim, "classes": list(cents.keys()),
                    "params": {"centroids": cents}}
    # stdlib mock — majority class (still a pipeline, honestly labeled)
    maj = max(classes, key=lambda c: sum(1 for v in y if str(v) == c)) if classes else "unknown"
    return {"engine": "mock", "dim": dim, "classes": classes or [maj],
            "params": {"majority": maj}}


# ── predict ──────────────────────────────────────────────────────────────────────────
def _softmax(vals: List[float]) -> List[float]:
    if not vals:
        return []
    m = max(vals)
    exps = [math.exp(v - m) for v in vals]
    s = sum(exps) or 1.0
    return [e / s for e in exps]


def predict(head: Dict[str, Any], vec: List[float]) -> Tuple[str, float]:
    """Predict (label, confidence) for one feature vector — pure, no Akasha context. Mirrors the
    engine used at fit time; a shape mismatch or a load failure degrades to the head's first class
    at low confidence (never raises)."""
    engine = head.get("engine", "mock")
    classes = head.get("classes") or ["unknown"]
    try:
        if engine.startswith("sklearn_"):
            n = _np()
            import base64
            import pickle
            est = pickle.loads(base64.b64decode(head["params"]["pickle_b64"]))
            X = n.asarray([vec], dtype="float64")
            lab = str(est.predict(X)[0])
            conf = 0.5
            if hasattr(est, "predict_proba"):
                probs = est.predict_proba(X)[0]
                conf = float(max(probs))
            return lab, round(conf, 4)
        if engine == "numpy_logreg":
            n = _np()
            p = head["params"]
            W = n.asarray(p["W"], dtype="float64")
            b = n.asarray(p["b"], dtype="float64")
            mu = n.asarray(p["mu"], dtype="float64")
            sd = n.asarray(p["sd"], dtype="float64")
            x = (n.asarray(vec, dtype="float64") - mu) / sd
            z = x @ W + b
            z -= z.max()
            e = n.exp(z)
            pr = e / (e.sum() or 1.0)
            j = int(pr.argmax())
            return str(head["classes"][j]), round(float(pr[j]), 4)
        if engine == "numpy_centroid":
            n = _np()
            cents = head["params"]["centroids"]
            v = n.asarray(vec, dtype="float64")
            vn = float((v * v).sum() ** 0.5) or 1.0
            sims, labs = [], []
            for c, cen in cents.items():
                cv = n.asarray(cen, dtype="float64")
                cn = float((cv * cv).sum() ** 0.5) or 1.0
                sims.append(float((v * cv).sum()) / (vn * cn))
                labs.append(c)
            probs = _softmax([s * 4.0 for s in sims])   # temperature so a clear match is confident
            j = max(range(len(labs)), key=lambda i: sims[i])
            return labs[j], round(probs[j], 4)
    except Exception:
        pass
    # mock / degraded
    return str(head.get("params", {}).get("majority") or classes[0]), 0.25


def predict_batch(head: Dict[str, Any], X: List[List[float]]) -> List[str]:
    return [predict(head, v)[0] for v in X]


# ── serialize (the weights artifact — OUTSIDE the store) ───────────────────────────────
def save(head: Dict[str, Any], path: str) -> Tuple[str, int]:
    """Write the head to `path` as JSON and return (sha256_hex, byte_size). The file is the 'weights
    artifact' — it lives in a bench artifact dir, never as an atom body; the store keeps only its
    digest + size (the model-identity atom)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    raw = json.dumps(head, ensure_ascii=False, sort_keys=True).encode("utf-8")
    with open(path, "wb") as f:
        f.write(raw)
        f.flush()
        os.fsync(f.fileno())
    return hashlib.sha256(raw).hexdigest(), len(raw)


def load(path: str) -> Optional[Dict[str, Any]]:
    """Load a head from its artifact file, or None when the file is absent (the observer then
    degrades to mock — the standing 'weights missing → mock' rule)."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


# ── metrics (aggregates only — R5) ─────────────────────────────────────────────────────
def metrics(y_true: List[str], y_pred: List[str], classes: List[str]) -> Dict[str, Any]:
    """Compute ONE aggregate metrics dict on a held-out frame: accuracy, macro-F1, a per-class table,
    and the confusion matrix AS DATA. Never a per-example write stream."""
    classes = list(classes) or sorted(set(y_true) | set(y_pred))
    idx = {c: i for i, c in enumerate(classes)}
    cm = [[0 for _ in classes] for _ in classes]
    for t, p in zip(y_true, y_pred):
        if t in idx and p in idx:
            cm[idx[t]][idx[p]] += 1
    total = len(y_true) or 1
    correct = sum(cm[i][i] for i in range(len(classes)))
    per_class = []
    f1s = []
    for i, c in enumerate(classes):
        tp = cm[i][i]
        fp = sum(cm[r][i] for r in range(len(classes))) - tp
        fn = sum(cm[i][cc] for cc in range(len(classes))) - tp
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        rec = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        f1s.append(f1)
        per_class.append({"class": c, "support": tp + fn, "precision": round(prec, 4),
                          "recall": round(rec, 4), "f1": round(f1, 4)})
    return {"n": len(y_true), "accuracy": round(correct / total, 4),
            "macro_f1": round(sum(f1s) / len(f1s), 4) if f1s else 0.0,
            "per_class": per_class, "classes": classes, "confusion": cm}
