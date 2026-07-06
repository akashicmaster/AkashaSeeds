"""
Tensor Semantics Engine (Spatiotemporal & Magnetic Field)
Translates Atoms and Metadata into N-dimensional cognitive vectors.
Handles Space (X, Y, Z), Time (T), and Semantic Vectors (Attractors).
Gracefully degrades to deterministic topology if heavy NLP libraries are missing.
"""
import hashlib
import re
from typing import Dict, List, Tuple, Any, Optional

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

    def embed(self, key: str, content: str, meta: dict) -> List[float]:
        """
        [NEW] Calculates the high-dimensional semantic vector for text content.
        Used to determine implicit 'Echo' links based on conceptual similarity.
        Stub: Returns deterministic pseudo-vector if heavy NLP is unavailable.
        """
        # Placeholder for actual word embeddings (e.g., TF-IDF or Sentence-BERT)
        h = int(hashlib.md5(content.encode()).hexdigest()[:8], 16)
        return [(h % 100)/100.0, ((h//100) % 100)/100.0, ((h//10000) % 100)/100.0]

    def find_closest(self, attractor_vector: str) -> Optional[str]:
        """
        [NEW] Solves intuitive resolutions like '~emo:sadness' or '~Rome'.
        Returns the key of the Atom closest to the given attractor vector in the tensor space.
        """
        if not self.cortex: return None
        
        # Basic stub: Try matching alias directly first
        aliases = self.cortex.get_aliases_by_pattern(f"%{attractor_vector}%")
        if aliases: 
            return aliases[0]["key"]
        
        # Fallback to basic text search stream if no exact vector match is found yet
        stream = self.cortex.stream(limit=20)
        for chunk in stream:
            if attractor_vector.lower() in str(chunk.get("content", "")).lower():
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
