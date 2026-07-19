"""
Self-owned semantic learning — learn embeddings from Akasha's OWN ontology + weave.

No external model, no download. numpy is the axis (PPMI + truncated SVD, the GloVe/LSA
family); if numpy is absent the learner reports unavailable and callers fall back to the
stdlib feature-hashing floor in tensor.py. This is the mid tier of the embedding stack:

    high  — sentence-transformers (optional, AKASHA_EMBED_MODEL)
    mid   — THIS: distributional vectors learned from the graph's own co-occurrence
    floor — signed feature-hashing + char n-grams (stdlib, always)

Where feature-hashing captures *lexical* overlap (shared characters/tokens), the learned
vectors capture *distributional* meaning: words that appear in similar contexts become
close even when they share no characters (swallow ~ migrate). The corpus is Akasha's
37k-atom ontology and everything the weaver has ingested — so the vectors are
domain-adapted to this knowledge base, not generic web text.
"""
import re
import math
from collections import Counter
from typing import Dict, List, Iterable, Optional

try:
    import numpy as _np
    _HAS_NUMPY = True
except Exception:                       # pragma: no cover - numpy is a wheel, usually present
    _np = None
    _HAS_NUMPY = False

_WORD = re.compile(r"[a-z0-9]+")


def tokens(text: str) -> List[str]:
    """Word tokens + char n-grams (2,3) — same shape as the feature-hashing floor, so
    the learned tier is comparable and CJK-aware (Japanese has no whitespace)."""
    low = (text or "").lower()
    out = _WORD.findall(low)
    compact = re.sub(r"\s+", " ", low)
    for n in (2, 3):
        if len(compact) >= n:
            out.extend(compact[i:i + n] for i in range(len(compact) - n + 1))
    return out


def cosine(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


class OntologyLearner:
    """Learns token embeddings from co-occurrence within documents (atoms).

    docs = iterable of token-lists (one per atom). Co-occurrence is whole-atom
    (every pair of tokens sharing an atom), which is what the weaver's proto-word
    structure encodes. PPMI reweights, truncated SVD compresses to `dim` dense dims.
    """

    def __init__(self, dim: int = 64, min_count: int = 2, max_vocab: int = 1200):
        self.dim = dim
        self.min_count = min_count
        self.max_vocab = max_vocab
        self.vocab: Dict[str, int] = {}
        self.vectors = None             # numpy [V, k]
        self.trained = False
        self.n_docs = 0                 # corpus size at train time (for stunted-model self-heal)

    @staticmethod
    def available() -> bool:
        return _HAS_NUMPY

    def learn(self, docs: Iterable[List[str]]) -> bool:
        """Build PPMI co-occurrence and factor it. Returns True on success."""
        if not _HAS_NUMPY:
            return False
        docs = [d for d in docs if d]
        self.n_docs = len(docs)
        if len(docs) < 3:
            return False

        df = Counter()
        for d in docs:
            df.update(set(d))
        vocab = [w for w, c in df.most_common(self.max_vocab) if c >= self.min_count]
        if len(vocab) < 3:
            return False
        self.vocab = {w: i for i, w in enumerate(vocab)}
        V = len(vocab)

        C = _np.zeros((V, V), dtype=_np.float64)
        for d in docs:
            present = list({self.vocab[w] for w in d if w in self.vocab})
            for i in range(len(present)):
                ai = present[i]
                for j in range(i + 1, len(present)):
                    bj = present[j]
                    C[ai, bj] += 1.0
                    C[bj, ai] += 1.0

        tot = C.sum()
        if tot <= 0:
            return False
        rows = C.sum(1, keepdims=True)
        cols = C.sum(0, keepdims=True)
        with _np.errstate(divide="ignore", invalid="ignore"):
            P = _np.where(C > 0, _np.log((C * tot) / (rows * cols + 1e-12)), 0.0)
        P = _np.maximum(P, 0.0)          # positive PMI

        try:
            U, S, _ = _np.linalg.svd(P, full_matrices=False)
        except Exception:                # pragma: no cover
            return False
        k = int(min(self.dim, V - 1))
        E = U[:, :k] * _np.sqrt(S[:k])
        norms = _np.linalg.norm(E, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        self.vectors = E / norms
        self.trained = True
        return True

    def embed_text(self, text: str) -> List[float]:
        """Compose a document vector = mean of its known token vectors, L2-normalised.
        Empty list if untrained or no token is in-vocabulary (caller degrades)."""
        if not self.trained or self.vectors is None:
            return []
        idxs = [self.vocab[w] for w in tokens(text) if w in self.vocab]
        if not idxs:
            return []
        v = self.vectors[idxs].mean(axis=0)
        n = float(math.sqrt(float(v @ v)))
        if n == 0.0:
            return []
        return [round(float(x), 5) for x in (v / n)]

    def learn_from_cortex(self, cortex, limit: int = 3000, min_len: int = 8) -> bool:
        """Convenience: gather atom contents from a cortex stream and learn from them."""
        docs = []
        for row in (cortex.stream(limit=limit) or []):
            content = row.get("content") or ""
            if len(content) >= min_len:
                docs.append(tokens(content))
        return self.learn(docs)

    # ── persistence — the learned model lives in the nucleus vault (SQLite), not a
    #    side file, so it survives restarts and is shared across sessions. It is a
    #    derived artifact (re-learnable), stored durably as ground truth. ─────────

    def to_dict(self) -> dict:
        if not self.trained or self.vectors is None:
            return {}
        return {
            "dim": int(self.vectors.shape[1]),
            "vocab": self.vocab,
            "vectors": [[round(float(x), 5) for x in row] for row in self.vectors],
            "n_docs": int(self.n_docs),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "OntologyLearner":
        learner = cls()
        if not d or not _HAS_NUMPY:
            return learner
        try:
            learner.vocab = d["vocab"]
            learner.vectors = _np.array(d["vectors"], dtype=_np.float64)
            learner.n_docs = int(d.get("n_docs", 0) or 0)
            learner.trained = True
        except Exception:                # pragma: no cover
            learner.trained = False
        return learner


# ── Structural (relational) node embeddings — the graph-topology counterpart ─────────
#
# OntologyLearner learns from atom *content* co-occurrence: atoms whose text appears in
# similar contexts become close. NodeWalkLearner learns from the *link graph* instead:
# random walks over the typed links become "documents" of node keys, and the SAME PPMI+SVD
# factorises node co-occurrence (DeepWalk / node2vec family, self-owned, numpy). Two atoms
# that share no words but sit close in the link structure become close — the relatedness
# that content embeddings cannot see. The two are complementary, which is the point of the
# comparison: content = "means the same", structure = "connected the same".

def _build_adjacency(links: Iterable[dict], directed: bool = False) -> Dict[str, list]:
    """src/dst/rel link rows → adjacency list. Undirected by default (a typed link makes
    both endpoints reachable in a walk); directed=True follows link direction only."""
    adj: Dict[str, list] = {}
    for l in links or []:
        s, d = l.get("src"), l.get("dst")
        if not s or not d:
            continue
        adj.setdefault(s, []).append(d)
        if not directed:
            adj.setdefault(d, []).append(s)
    return adj


def random_walks(adj: Dict[str, list], walks_per_node: int = 10,
                 length: int = 8, seed: int = 1) -> List[List[str]]:
    """Generate `walks_per_node` random walks of up to `length` node keys from each node.
    Seeded (deterministic) for reproducibility — the resilience model favours determinism,
    and a fixed seed makes the learned structure stable across runs."""
    import random
    rng = random.Random(seed)
    walks: List[List[str]] = []
    for start in adj:
        for _ in range(walks_per_node):
            walk, cur = [start], start
            for _ in range(length - 1):
                nbrs = adj.get(cur)
                if not nbrs:
                    break
                cur = nbrs[rng.randrange(len(nbrs))]
                walk.append(cur)
            if len(walk) > 1:
                walks.append(walk)
    return walks


class NodeWalkLearner:
    """Structural node embeddings from random walks over the typed-link graph. Reuses
    OntologyLearner's PPMI+SVD, treating each walk as a document of node keys, so a node's
    vector is its row in the factorised node-co-occurrence matrix (NOT its text)."""

    def __init__(self, dim: int = 32, min_count: int = 1, max_vocab: int = 5000,
                 walks_per_node: int = 10, length: int = 8, seed: int = 1):
        self.learner = OntologyLearner(dim=dim, min_count=min_count, max_vocab=max_vocab)
        self.walks_per_node = walks_per_node
        self.length = length
        self.seed = seed

    @staticmethod
    def available() -> bool:
        return _HAS_NUMPY

    def learn(self, links: Iterable[dict], directed: bool = False) -> bool:
        adj = _build_adjacency(links, directed=directed)
        if len(adj) < 3:
            return False
        return self.learner.learn(random_walks(
            adj, self.walks_per_node, self.length, self.seed))

    def node_vector(self, key: str) -> List[float]:
        """The learned vector for an exact node key (empty if untrained / unseen). Unlike
        embed_text, the key is a vocab token, not re-tokenised into char n-grams."""
        lr = self.learner
        if not lr.trained or lr.vectors is None or key not in lr.vocab:
            return []
        return [round(float(x), 5) for x in lr.vectors[lr.vocab[key]]]

    def similarity(self, key_a: str, key_b: str) -> float:
        return cosine(self.node_vector(key_a), self.node_vector(key_b))

    @property
    def vocab(self) -> Dict[str, int]:
        return self.learner.vocab

    @property
    def trained(self) -> bool:
        return self.learner.trained


# ── shared model cache — one learned model per process, backed by the nucleus vault ──
_SHARED = {"loaded": False, "model": None}


def store_model(nucleus, learner: OntologyLearner) -> bool:
    """Persist a trained model to the nucleus vault and refresh the process cache."""
    if not learner.trained:
        return False
    nucleus.vault_store("semantic", "model", learner.to_dict())
    _SHARED["loaded"] = True
    _SHARED["model"] = learner
    return True


def get_shared_model(nucleus) -> Optional[OntologyLearner]:
    """Return the learned model (loading from the vault once), or None if none exists
    or numpy is unavailable — callers degrade to the feature-hashing floor."""
    if not _SHARED["loaded"]:
        _SHARED["loaded"] = True
        d = None
        try:
            d = nucleus.vault_retrieve("semantic", "model")
        except Exception:
            d = None
        m = OntologyLearner.from_dict(d) if d else None
        _SHARED["model"] = m if (m and m.trained) else None
    return _SHARED["model"]


# ── structural (node-walk) model — persisted separately from the content model ──────────
_SHARED_NODE = {"loaded": False, "model": None}


def store_node_model(nucleus, nwl: "NodeWalkLearner") -> bool:
    """Persist a trained NodeWalkLearner (its inner factorised node-vector table) to the
    vault and refresh the process cache. The vocab IS the set of node keys."""
    if not nwl.trained:
        return False
    nucleus.vault_store("semantic", "node_model", nwl.learner.to_dict())
    _SHARED_NODE["loaded"] = True
    _SHARED_NODE["model"] = nwl
    return True


def get_node_model(nucleus) -> Optional["NodeWalkLearner"]:
    """Return the structural node model (loading from the vault once), or None."""
    if not _SHARED_NODE["loaded"]:
        _SHARED_NODE["loaded"] = True
        d = None
        try:
            d = nucleus.vault_retrieve("semantic", "node_model")
        except Exception:
            d = None
        m = None
        if d:
            inner = OntologyLearner.from_dict(d)
            if inner and inner.trained:
                m = NodeWalkLearner()
                m.learner = inner
        _SHARED_NODE["model"] = m
    return _SHARED_NODE["model"]
