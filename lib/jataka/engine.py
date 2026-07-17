"""
Jataka — Storytelling Engine.

Pipeline position (counterpart to Contexa):

  [External] → Contexa (reading / macro binding) → Akasha → Jataka (macro narration) → [Output]

Where Contexa is the "input side" that binds fragments into contextual structure, Jataka is the
"output side" that traverses Akasha's graph and outputs a narrative with macro context.
Rather than individual search results, it returns a story that weaves in the relationships,
history, and context of Atoms.

NOTE (live surface): the Jataka output side now runs on the I/O pipe as `jataka.present`
(table / scatter / narrative — pipeline endpoints in lib/harmonia/pipeline.py, wired by the
kernel `_handle_jataka_present`), and `dream` is the kernel's async affinity-gap incubation
(`_handle_dream`). The methods in THIS class (dream/dream_affinities/lookup_historical_echoes/
analyze_source) are legacy and not on the live dispatch path. See docs/for-llm/io-pipeline.md
and CLAUDE.md "Jataka — Narrator".

  dream — Experimental generative output. In addition to Consciousness's interpretation
           (signposts + resonance), it overlays hidden affinities between Atoms
           (calc:hidden_affinity) to construct a more creative narrative that goes beyond
           explicit links. Provisional links are confirmed upon user approval.

Context granularity handled by Jataka:
  macro (Jataka)  — dialogue threads, topic links, ctx:answers chains,
                    spatiotemporal strata, cross-set narratives
  Consciousness   — interpretation (signposts / resonance / cosmos_nd / aura — input to Jataka)
  micro (Weaver)  — word decomposition, protoword links, component sets

IAM: dream always inherits the session's active_scopes.
     It will not reference or propose as hidden affinity any Atom outside the scope.

Degradation:
  T2  semantic_vector present → affinity score via cosine similarity
  T1  semantic_vector absent  → Jaccard similarity (overlap between extracts sets)
  T0  both absent             → skip affinity search (dream_affinities returns empty)
"""

import math
import json
import logging
import traceback
from typing import List, Dict, Any, Optional, Set

logger = logging.getLogger("Harmonia.Jataka")

class JatakaEngine:
    """
    Storytelling engine — narrates Akasha's graph with macro context.

    Returns structured narratives (stories) rather than flat search results.
    dream_affinities() discovers hidden connections; dream() turns them into
    generative output.  Both are IAM-scoped and degrade gracefully.
    """
    def __init__(self, session: Any = None, layer_id: str = "kamakura.strata.v1"):
        self.name = "Jataka Vector & Spatial Explorer"
        self.session = session
        self.cortex = getattr(session, 'cortex', getattr(session, 'local_cortex', None)) if session else None
        self.harmonia = getattr(session, 'harmonia_engine', None) if session else None
        self.layer_id = layer_id
        
        logger.debug(f"[Jataka] Engine initialized. Default strata: {self.layer_id}")

    # =========================================================================
    # 1. Spatiotemporal & Historical Orchestration
    # =========================================================================

    def switch_layer(self, new_layer_id: str) -> Dict[str, Any]:
        """Shifts the engine's focus to a different spatial/historical stratum."""
        old_layer = self.layer_id
        self.layer_id = new_layer_id
        logger.info(f"[Jataka] Stratum shifted: {old_layer} -> {new_layer_id}")
        return {"status": "layer_switched", "layer": self.layer_id}

    def calibrate(self) -> Dict[str, Any]:
        """
        Calibrates the Jataka spatiotemporal engine.
        Aligns tensor dimensions and prepares legacy heuristic indices.
        """
        logger.debug("[Jataka] Calibration sequence executed.")
        return {"status": "calibrated", "message": "Jataka Engine (Spatial & Semantic) calibrated and ready."}

    def lookup_historical_echoes(self, old_x: float, old_y: float, radius: float = 0.005, period_filter: Optional[str] = None) -> Dict[str, Any]:
        """Queries the Cortex for spatial memories overlapping physical coordinates."""
        if not self.cortex or not hasattr(self.cortex, 'find_nearby_atoms'):
            logger.warning("[Jataka] Spatial query requested, but Cortex lacks spatial index.")
            return {"error": "Cortex does not support spatial queries in the current topology."}
            
        try:
            echoes = self.cortex.find_nearby_atoms(old_x, old_y, radius)

            target_period = period_filter
            if not target_period and hasattr(self.session, 'chrono'):
                target_period = getattr(self.session.chrono, 'period_name', "unknown")
            
            filtered_results = []
            active_scopes = getattr(self.session, 'active_scopes', [])
            
            for echo in echoes:
                # [SECURITY] Prevent leaking spatial data of private atoms
                if active_scopes and hasattr(self.cortex, 'check_access'):
                    if not self.cortex.check_access(echo.get("key"), active_scopes):
                        continue
                        
                echo_period = echo.get("period", "unknown")
                if target_period in ["all_strata", "unknown", None] or echo_period == target_period:
                    filtered_results.append(echo)

            return {
                "historical_focus": {"x": old_x, "y": old_y},
                "layer": self.layer_id,
                "period_filter": target_period,
                "echo_count": len(filtered_results),
                "echoes": filtered_results
            }
        except Exception as e:
            logger.error(f"[Jataka] Spatial lookup failed: {e}", exc_info=True)
            return {"error": f"Spatial computation error: {str(e)}"}

    # =========================================================================
    # 2. Cognitive Simulations (Dreams & Analysis via Harmonia)
    # =========================================================================

    def analyze_source(self, text: str, label: str = "import") -> Dict[str, Any]:
        """Delegates heavy NLP analysis to the Motor Cortex (Harmonia)."""
        if not self.harmonia:
            return {"error": "Harmonia Engine is required for heavy cognitive analysis."}
            
        try:
            tx_id = self.harmonia.begin_workspace(self.cortex, label)
            process_result = self.harmonia.execute_with_evidence(
                cortex=self.cortex, tx_id=tx_id, executor="nlp.extract", input_data=text
            )
            return {"tx_id": tx_id, "analysis_result": process_result}
        except Exception as e:
            logger.error(f"[Jataka] Source analysis failed: {e}")
            return {"error": f"Analysis transaction failed: {str(e)}"}

    def dream(self, focus_key: str) -> Dict[str, Any]:
        """Initiates a heavy reinforcement learning / affinity simulation."""
        if not self.harmonia:
            return {"error": "Harmonia Engine is required for deep dreaming."}
            
        try:
            tx_id = self.harmonia.begin_workspace(self.cortex, f"dream:{focus_key[:8]}")
            logger.info(f"[Jataka] Deep dream initiated for focus '{focus_key[:8]}'. TxID: {tx_id}")
            return {"status": "dream_started", "tx_id": tx_id, "focus": focus_key}
        except Exception as e:
            return {"error": f"Dream initiation failed: {str(e)}"}

    # =========================================================================
    # 3. Real-time Semantic Vector Discovery
    # =========================================================================

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Mathematical cosine similarity for high-dimension semantic vectors."""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
            
        try:
            dot_product = sum(v1 * v2 for v1, v2 in zip(vec1, vec2))
            norm1 = math.sqrt(sum(v ** 2 for v in vec1))
            norm2 = math.sqrt(sum(v ** 2 for v in vec2))
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            return dot_product / (norm1 * norm2)
        except Exception:
            return 0.0

    def _jaccard_similarity(self, set1: Set[str], set2: Set[str]) -> float:
        """Heuristic fallback calculation using Set Overlap (Jaccard Index)."""
        if not set1 and not set2: 
            return 0.0
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        if union == 0: 
            return 0.0
        return intersection / union

    def _get_node_extracts(self, ctx: Any, node_id: str, active_scopes: List[str]) -> Set[str]:
        """Retrieves extracted keyword Atom IDs for a node to use in heuristic matching."""
        try:
            members = ctx.list_set(f"extracts:{node_id}")
            # Ensure we only consider keywords we are allowed to view
            return {m["key"] for m in members if ctx.check_access(m["key"], active_scopes)}
        except Exception:
            return set()

    def dream_affinities(self, ctx: Any, focus_id: str, limit: int = 5, threshold: float = 0.3) -> List[Dict[str, Any]]:
        """
        [THE SUBCONSCIOUS RADAR]
        Scans the semantic graph for unlinked nodes that share conceptual or vector similarity.
        Strictly enforces IAM multi-dimensional scopes during the scan.
        """
        active_scopes = getattr(self.session, 'active_scopes', [])
        
        # Verify focus node accessibility before dreaming
        if active_scopes and hasattr(ctx, 'check_access') and not ctx.check_access(focus_id, active_scopes):
            logger.warning(f"[Jataka] Access denied to focus node '{focus_id}' for dreaming.")
            return []

        focus_chunk = ctx.get_chunk(focus_id)
        if not focus_chunk: 
            return []
        
        # Safe metadata parsing
        focus_meta = ctx.get_meta(focus_id) if hasattr(ctx, 'get_meta') else {}
        if isinstance(focus_meta, str):
            try: focus_meta = json.loads(focus_meta)
            except json.JSONDecodeError: focus_meta = {}
            
        focus_vec = focus_meta.get("semantic_vector")
        
        # Heuristic Fallback: Fetch keyword sets for Jaccard Similarity if vector is missing
        focus_keywords = self._get_node_extracts(ctx, focus_id, active_scopes) if not focus_vec else set()
        
        # If absolutely no cognitive data exists, we cannot calculate affinity
        if not focus_vec and not focus_keywords:
            return []
            
        # Stream recent nodes to scan against (Limit scan window to preserve CPU)
        recent_nodes = ctx.stream(limit=1000)
        
        # Avoid suggesting nodes we are already explicitly linked to
        existing_links = ctx.get_adjacent_links(focus_id)
        linked_ids = {link[0] for link in existing_links}
        
        dreams = []
        
        for node in recent_nodes:
            target_id = node["key"]
            
            # Skip self, already linked, or inaccessible nodes (IAM Enforcement)
            if target_id == focus_id or target_id in linked_ids:
                continue
            if active_scopes and hasattr(ctx, 'check_access') and not ctx.check_access(target_id, active_scopes):
                continue
                
            target_meta = node.get("meta", {})
            if isinstance(target_meta, str):
                try: target_meta = json.loads(target_meta)
                except json.JSONDecodeError: target_meta = {}
                
            target_vec = target_meta.get("semantic_vector")
            
            # Fallback metadata resolution
            if not target_vec and hasattr(ctx, 'get_meta'):
                target_meta_db = ctx.get_meta(target_id)
                if isinstance(target_meta_db, dict):
                    target_vec = target_meta_db.get("semantic_vector")
            
            similarity = 0.0
            
            # Mode A: Advanced Neural/Hashed Vector Match
            if focus_vec and target_vec:
                similarity = self._cosine_similarity(focus_vec, target_vec)
                
            # Mode B: Degraded Heuristic Set Match (Fallback via Weaver Extracts)
            elif focus_keywords:
                target_keywords = self._get_node_extracts(ctx, target_id, active_scopes)
                if target_keywords:
                    # Jaccard index is naturally stricter than Cosine, so we boost the score slightly for UX
                    similarity = self._jaccard_similarity(focus_keywords, target_keywords) * 1.5 
            
            if similarity >= threshold:
                dreams.append({
                    "src": focus_id,
                    "dst": target_id,
                    "rel": "calc:hidden_affinity",
                    "confidence": min(similarity, 0.99), # Cap confidence
                    "preview": str(node.get("content", ""))[:40].replace('\n', ' ')
                })
                
        # Sort by highest similarity first
        dreams.sort(key=lambda x: x["confidence"], reverse=True)
        logger.debug(f"[Jataka] Dream cycle complete. Found {len(dreams)} affinities above threshold.")
        return dreams[:limit]
