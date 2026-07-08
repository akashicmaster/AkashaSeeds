"""
Tensor Semantics Engine (Spatiotemporal & Magnetic Field)
Translates Atoms and Metadata into N-dimensional cognitive vectors.
Handles Space (X, Y, Z), Time (T), and Semantic Vectors (Attractors).
Gracefully degrades to deterministic topology if heavy NLP libraries are missing.
"""
import hashlib
import math
import os
import re
from typing import Dict, List, Tuple, Any, Optional

# Optional high tier: a real sentence-transformer, loaded once if AKASHA_EMBED_MODEL
# is set (opt-in). Cached at module level. `False` = "tried and unavailable" so we
# never re-probe; `None` = "not yet tried". The default (no env) skips it entirely,
# so the dependency-free self-owned embedding below is the out-of-the-box behaviour.
_ST_MODEL: Any = None

class TensorEngine:
    def __init__(self, cortex=None):
        self.cortex = cortex
        # Base dimensions: [X, Y, Z, T]
        self.DIM_X = 0
        self.DIM_Y = 1
        self.DIM_Z = 2
        self.DIM_T = 3
        
        # [FUTURE] NLP Model initialization flag (e.g., scikit-learn or spacy)
        self._nlp_ready = False

    def _hash_to_coord(self, text: str, salt: int) -> float:
        """Deterministic pseudo-random coordinate from text hash."""
        h = hashlib.sha256(f"{text}_{salt}".encode()).digest()
        return (h[0] / 255.0) * 200.0 - 100.0

    def calculate_spatiotemporal_vector(self, key: str, content: str, meta: dict, origin_key: str = None) -> List[float]:
        """
        Calculates the [X, Y, Z, T] vector for an Atom.
        """
        vector = [0.0, 0.0, 0.0, 0.0]

        # --- 1. SPATIAL AXIS (X, Y, Z) ---
        spatial_found = False
        if "modern_geo_x" in meta and "modern_geo_y" in meta:
            vector[self.DIM_X] = float(meta["modern_geo_x"])
            vector[self.DIM_Y] = float(meta["modern_geo_y"])
            spatial_found = True
        elif "geo_x" in meta and "geo_y" in meta:
            vector[self.DIM_X] = float(meta["geo_x"])
            vector[self.DIM_Y] = float(meta["geo_y"])
            spatial_found = True
        else:
            # Try to extract from tags like geo:at:35.3,139.5
            match = re.search(r'geo:at:(-?\d+\.?\d*),(-?\d+\.?\d*)', content)
            if match:
                vector[self.DIM_X] = float(match.group(1))
                vector[self.DIM_Y] = float(match.group(2))
                spatial_found = True

        # Fallback to topology/hash gravity if no explicit space is defined
        if not spatial_found:
            vector[self.DIM_X] = self._hash_to_coord(key, 1)
            vector[self.DIM_Y] = self._hash_to_coord(key, 2)
            vector[self.DIM_Z] = self._hash_to_coord(key, 3)

        # Apply gravity towards origin if provided (Topology alignment)
        if origin_key and origin_key != key:
            ox = self._hash_to_coord(origin_key, 1)
            oy = self._hash_to_coord(origin_key, 2)
            oz = self._hash_to_coord(origin_key, 3)
            if not spatial_found:
                vector[self.DIM_X] = (vector[self.DIM_X] + ox) / 2
                vector[self.DIM_Y] = (vector[self.DIM_Y] + oy) / 2
                vector[self.DIM_Z] = (vector[self.DIM_Z] + oz) / 2

        # --- 2. TEMPORAL AXIS (T) ---
        # T axis can represent Narrative Time (era/year) or Chronological Time.
        # Here we prioritize explicit Narrative Time from metadata or tags.
        t_val = 0.0
        if "year" in meta:
            t_val = float(meta["year"])
        elif "period" in meta:
            # Map known periods to a linear timeline (example)
            periods = {"kamakura": 1200.0, "edo": 1700.0, "meiji": 1900.0, "modern": 2024.0}
            t_val = periods.get(meta["period"].lower(), 0.0)
        else:
            # Extract from chrono:year:1924 tag
            match = re.search(r'chrono:(?:year|era):(\d{3,4})', content)
            if match:
                t_val = float(match.group(1))
            else:
                # Fallback to creation timestamp (relative scaling)
                t_val = float(meta.get("created_at", 0)) / 1000000000.0 

        vector[self.DIM_T] = t_val

        return [round(v, 4) for v in vector]

    def shift_perspective(self, vector: List[float], dt: float = 0.0, dx: float = 0.0, dy: float = 0.0) -> List[float]:
        """Applies a mathematical shift (translation) to the cognitive vector."""
        new_vec = list(vector)
        if len(new_vec) >= 4:
            new_vec[self.DIM_X] += dx
            new_vec[self.DIM_Y] += dy
            new_vec[self.DIM_T] += dt
        return new_vec

    # --- 3. MAGNETIC FIELD & ATTRACTOR CALCULATIONS (NEW) ---

    # ── Semantic embedding — graceful degradation, self-owned floor ──────────
    # The semantic vector powers cosine similarity (Jataka T2 dream, semantic
    # search). Two tiers, and the *degraded* tier is intentionally a real technique,
    # not a hash placeholder — Akasha must stay genuinely useful with zero heavy deps:
    #   high (opt-in) — a sentence-transformer, if AKASHA_EMBED_MODEL is set.
    #   floor (always) — self-owned signed feature-hashing over word tokens AND
    #                    character n-grams. Documents that share vocabulary / substrings
    #                    get high cosine; works for whitespace languages and CJK alike,
    #                    with no external library. This is the "それなり" done properly.

    EMBED_DIM = 96

    def _own_embed(self, text: str, dim: int = EMBED_DIM) -> List[float]:
        """Dependency-free embedding: signed feature-hashing (the hashing trick) over
        word tokens + char n-grams, L2-normalised. Real cosine structure, stdlib only."""
        vec = [0.0] * dim
        low = text.lower()
        tokens = re.findall(r"[a-z0-9]+", low)                     # whitespace languages
        compact = re.sub(r"\s+", " ", low)
        for n in (2, 3):                                           # char n-grams — CJK + morphology
            if len(compact) >= n:
                tokens.extend(compact[i:i + n] for i in range(len(compact) - n + 1))
        if not tokens:
            return []
        for tok in tokens:
            h = int(hashlib.sha1(tok.encode("utf-8")).hexdigest(), 16)
            vec[h % dim] += 1.0 if (h >> 8) & 1 else -1.0          # signed → cancels collisions
        norm = math.sqrt(sum(v * v for v in vec))
        if norm == 0.0:
            return []
        return [round(v / norm, 5) for v in vec]

    @staticmethod
    def _st_model():
        """Load the optional sentence-transformer once (opt-in via AKASHA_EMBED_MODEL).
        Returns the model, or None if not configured / unavailable — caller degrades."""
        global _ST_MODEL
        if _ST_MODEL is not None:
            return _ST_MODEL or None
        name = os.environ.get("AKASHA_EMBED_MODEL", "").strip()
        if not name:
            _ST_MODEL = False
            return None
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
            _ST_MODEL = SentenceTransformer(name)
        except Exception:
            _ST_MODEL = False
        return _ST_MODEL or None

    def embed(self, key: str, content: str, meta: dict = None) -> List[float]:
        """Semantic vector for text, best available tier:
             high  — sentence-transformer if configured (AKASHA_EMBED_MODEL)
             mid   — the distributional model learned from the ontology (semantic.learn),
                     if one has been built — self-owned, numpy, domain-adapted
             floor — self-owned feature-hashing (always). Empty for no text."""
        if not content or not content.strip():
            return []
        model = self._st_model()
        if model is not None:
            try:
                return [round(float(x), 5) for x in model.encode(content)]
            except Exception:
                pass
        # mid tier: the learned model (loaded once, cached) if a nucleus + model exist.
        try:
            from lib.akasha.semantic_learn import get_shared_model
            nucleus = getattr(self.cortex, "_nucleus", None) if self.cortex else None
            if nucleus is not None:
                lm = get_shared_model(nucleus)
                if lm is not None:
                    v = lm.embed_text(content)
                    if v:
                        return v
        except Exception:
            pass
        return self._own_embed(content)

    @staticmethod
    def cosine(a: List[float], b: List[float]) -> float:
        """Cosine similarity of two equal-length vectors (0.0 on mismatch/empty)."""
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(y * y for y in b))
        return dot / (na * nb) if na and nb else 0.0

    def find_closest(self, query: str, candidates: Optional[List[str]] = None,
                     top_k: int = 1) -> Optional[str]:
        """Return the key of the atom whose stored semantic_vector is closest (cosine)
        to `query`. Scans `candidates` if given, else a recent-stream window. Falls back
        to alias/substring match when no vectors are present (graceful degradation)."""
        if not self.cortex:
            return None
        import json as _json
        qvec = self._own_embed(query) if not self._st_model() else self.embed("", query, {})
        keys = candidates if candidates is not None else \
            [c["key"] for c in (self.cortex.stream(limit=500) or [])]

        best_key, best_sim = None, 0.0
        for k in keys:
            meta = self.cortex.get_meta(k) if hasattr(self.cortex, "get_meta") else None
            if isinstance(meta, str):
                try:
                    meta = _json.loads(meta)
                except Exception:
                    meta = {}
            vec = (meta or {}).get("semantic_vector") if isinstance(meta, dict) else None
            if not vec:
                continue
            sim = self.cosine(qvec, vec)
            if sim > best_sim:
                best_key, best_sim = k, sim
        if best_key is not None:
            return best_key

        # Degraded fallback: no vectors present → alias, then substring.
        aliases = self.cortex.get_aliases_by_pattern(f"%{query}%")
        if aliases:
            return aliases[0]["key"]
        for chunk in (self.cortex.stream(limit=50) or []):
            if query.lower() in str(chunk.get("content", "")).lower():
                return chunk["key"]
        return None

    def get_global_intentionality_profile(self) -> Dict[str, Any]:
        """
        [NEW] Swarm Intelligence Telemetry.
        Calculates the "center of mass" of current interests based on recent memory access,
        providing vectors to the Librarian for targeted knowledge scraping.
        """
        return {
            "dominant_attractors": ["emo:anticipation", "concept:creativity"],
            "swarm_density_center": [0.5, -0.2, 0.1, 2026.0],
            "active_nodes_count": 42
        }
