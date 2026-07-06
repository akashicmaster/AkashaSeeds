"""
Correspondence Concept Model.
A neutral mapping layer for recording correspondences between two systems:
maps, countries, historical borders, administrative units, symbolic spaces,
or any two conceptual coordinate systems.
Core idea:
    A correspondence is not the same as identity.
    It is a scoped, evidenced, directional or mutual mapping claim.
Namespace contract:
    - Content atoms      -> set:corr:{concept_id} and subset sets
    - Concept-word atoms -> set:concept:{concept_id}
Version: 1.0.0
"""
import time
import logging
from typing import Any, Dict, List, Optional
from lib.akasha.concepts.base import BaseConcept
from lib.akasha.concepts.mixins.provenance import ProvenanceMixin
from lib.akasha.graph.query import GraphQueryEngine

logger = logging.getLogger("Harmonia.Concept.Correspondence")

CONTEXT_KEY_ACTIVE = "active_corr_root"
INDEX_SET = "set:corr:index"
_CONCEPT_WORD_ALIAS_PREFIX = "concept:word:"

SUBSET_TO_RELATION: Dict[str, str] = {
    "systems":      "corr:has_system",
    "links":        "corr:has_link",
    "projections":  "corr:has_projection",
    "sources":      "corr:has_source",
    "source_evals": "corr:has_source_eval",
    "evals":        "corr:has_eval",
    "disputes":     "corr:has_dispute",   # was "conflicts" in submitted code — renamed for consistency
}

RELATION_TYPES = (
    "equals",
    "overlaps",
    "contains",
    "part_of",
    "adjacent_to",
    "replaces",
    "derived_from",
    "claims",
    "governs",
    "administers",
    "symbolically_matches",
    "other",
)

ORIGIN_TYPES = ("direct", "inferred")

STATUS_TYPES = (
    "active",
    "disputed",
    "retracted",
    "superseded",
    "unverified",
)

SOURCE_KINDS = (
    "map",
    "official_doc",
    "treaty",
    "archive",
    "fieldnote",
    "fact",
    "geo",
    "country",
    "academic_paper",
    "news_article",
    "other",
)

ALGO_METHODS = (
    "human",
    "llm",
    "rule_based",
    "statistical",
    "pattern_matching",
    "hybrid",
)


class CorrespondenceConcept(BaseConcept, ProvenanceMixin):
    """Evidence-grounded correspondence mapping between systems."""

    CONCEPT_PREFIX = "corr"
    CONTEXT_KEY_ACTIVE = CONTEXT_KEY_ACTIVE

    CONCEPT_METHODS = {
        "new": {"op": "op_new"},
        "open": {
            "op": "op_open",
            "coerce": lambda d: {
                "corr_id": d.get("corr_id") or d.get("id") or d.get("concept_id", "")
            },
        },
        "ls":          {"op": "op_list_all"},
        "map":         {"op": "op_map"},
        "rm":          {"op": "op_delete"},
        "system.add":  {"op": "op_add_system"},
        "source.add":  {"op": "op_add_source"},
        "source.eval": {"op": "op_eval_source"},
        "link.add":    {"op": "op_add_link"},
        "link.infer":  {"op": "op_add_inferred_link"},
        "project.add": {"op": "op_add_projection"},
        "eval.add":    {"op": "op_eval"},
        "dispute.add": {"op": "op_dispute"},
        "trace":       {"op": "op_trace"},
        "diagnose":    {"op": "op_diagnose"},
    }

    SUBSETS = list(SUBSET_TO_RELATION.keys())

    def __init__(self, session: Any, concept_id: Optional[str] = None):
        super().__init__(session, concept_id)
        if not self.concept_id:
            stored = getattr(self.session, "get_context", lambda k: None)(CONTEXT_KEY_ACTIVE)
            if stored:
                self.concept_id = stored
                self.set_name = f"set:concept:{self.concept_id}"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _corr_set(self, suffix: Optional[str] = None) -> str:
        base = f"set:corr:{self.concept_id}"
        return f"{base}:{suffix}" if suffix else base

    def _author_and_scopes(self):
        author_id = getattr(self.session, "client_id", "system")
        scopes = [f"owner:user_{author_id}", f"view:user_{author_id}"]
        return author_id, scopes

    def _create_sets(self) -> None:
        self.cortex.create_set(self.set_name)
        self.cortex.create_set(self._corr_set())
        for suffix in self.SUBSETS:
            self.cortex.create_set(self._corr_set(suffix))
        self.cortex.create_set(INDEX_SET)

    def _get_or_create_concept_word(self, word: str) -> str:
        alias = f"{_CONCEPT_WORD_ALIAS_PREFIX}{word}"
        existing = self.cortex.resolve_alias(alias)
        if existing:
            return existing
        author_id, scopes = self._author_and_scopes()
        key = self.cortex.put_chunk(
            content=word,
            meta={
                "type": "concept_word",
                "word": word,
                "concept_model": "correspondence",
                "created_at": time.time(),
            },
            author=author_id,
            scopes=scopes,
        )
        self.cortex.set_alias(key, alias)
        return key

    def _register(
        self,
        key: str,
        subset_suffix: Optional[str] = None,
        concept_word: Optional[str] = None,
    ) -> None:
        author_id, _ = self._author_and_scopes()
        self.cortex.add_to_set(self._corr_set(), key)
        if subset_suffix:
            self.cortex.add_to_set(self._corr_set(subset_suffix), key)
        if concept_word:
            cw_key = self._get_or_create_concept_word(concept_word)
            self.register_concept_node(cw_key)
            self.cortex.put_link(key, cw_key, "sys:derived_from", author=author_id)

    def _require_access(self, atom_id: str, label: str = "Atom") -> None:
        if not atom_id:
            raise ValueError(f"{label} id is required.")
        if not self.cortex.check_access(atom_id, self.allowed_scopes):
            raise RuntimeError(f"{label} not accessible: {atom_id[:12]}")

    def _visible(self, atom_id: str) -> bool:
        return bool(atom_id and self.cortex.check_access(atom_id, self.allowed_scopes))

    def _members(self, suffix: str) -> List[str]:
        return [
            key for key in self.cortex.get_collection_members(self._corr_set(suffix))
            if self._visible(key)
        ]

    def _meta(self, key: str) -> Dict[str, Any]:
        return self.cortex.get_meta(key) or {}

    def _content(self, key: str) -> str:
        return self.cortex.get_chunk(key) or ""

    def _summary(self, key: str) -> Dict[str, Any]:
        return {"id": key, "content": self._content(key), "meta": self._meta(key)}

    def _put_atom(
        self,
        content: str,
        atom_type: str,
        subset: str,
        meta_extra: Optional[Dict[str, Any]] = None,
        concept_word: Optional[str] = None,
    ) -> str:
        author_id, scopes = self._author_and_scopes()
        meta = {
            "type": atom_type,
            "concept": "corr",
            "created_at": time.time(),
        }
        if meta_extra:
            meta.update(meta_extra)
        key = self.cortex.put_chunk(
            content=content,
            meta=meta,
            author=author_id,
            scopes=scopes,
        )
        self._register(key, subset_suffix=subset, concept_word=concept_word)
        relation = SUBSET_TO_RELATION.get(subset, f"corr:has_{subset}")
        self.cortex.put_link(self.concept_id, key, relation, author=author_id)
        return key

    @staticmethod
    def _clamp01(value: Any, default: float = 0.0) -> float:
        try:
            return max(0.0, min(1.0, float(value)))
        except Exception:
            return default

    @staticmethod
    def _as_list(value: Any) -> List[Any]:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        return [value]

    def _normal_scope(
        self,
        scope: Optional[Dict[str, Any]] = None,
        valid_from: str = "",
        valid_to: str = "",
        context: str = "",
        perspective: str = "",
    ) -> Dict[str, Any]:
        base = {
            "valid_from": valid_from,
            "valid_to": valid_to,
            "context": context,
            "perspective": perspective,
        }
        if isinstance(scope, dict):
            base.update(scope)
        return base

    def _graph(self) -> GraphQueryEngine:
        """Return a GraphQueryEngine bound to this concept's cortex."""
        return GraphQueryEngine(
            cortex=self.cortex,
            visible_fn=self._visible,
            meta_fn=self._meta,
            content_fn=self._content,
        )

    # ------------------------------------------------------------------
    # Basic operators
    # ------------------------------------------------------------------

    def op_new(self, title: str, description: str = "") -> Dict[str, Any]:
        if not title:
            raise ValueError("corr.new requires title.")
        author_id, scopes = self._author_and_scopes()
        root_id = self.cortex.put_chunk(
            content=f"[ Correspondence: {title} ]",
            meta={
                "type": "concept",
                "concept": "corr",
                "role": "root",
                "title": title,
                "description": description,
                "created_at": time.time(),
            },
            author=author_id,
            scopes=scopes,
        )
        self.concept_id = root_id
        self.set_name = f"set:concept:{self.concept_id}"
        self._create_sets()
        self.cortex.add_to_set(self._corr_set(), root_id)
        self.cortex.add_to_set(INDEX_SET, root_id)
        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, root_id)
        return {
            "status": "created",
            "concept_id": root_id,
            "corr_id": root_id,
            "title": title,
        }

    def op_open(self, corr_id: str) -> Dict[str, Any]:
        meta = self._meta(corr_id)
        if not meta or meta.get("concept") != "corr":
            raise RuntimeError(f"Atom '{corr_id[:12]}' is not a correspondence root.")
        if not self._visible(corr_id):
            raise RuntimeError(f"Correspondence not accessible: {corr_id[:12]}")
        self.concept_id = corr_id
        self.set_name = f"set:concept:{self.concept_id}"
        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, corr_id)
        return {
            "status": "opened",
            "concept_id": corr_id,
            "corr_id": corr_id,
            "title": meta.get("title", ""),
        }

    def op_list_all(self) -> Dict[str, Any]:
        roots = []
        for key in self.cortex.get_collection_members(INDEX_SET):
            if not self._visible(key):
                continue
            meta = self._meta(key)
            if meta.get("concept") != "corr":
                continue
            roots.append({
                "corr_id": key,
                "concept_id": key,
                "title": meta.get("title", ""),
                "created_at": meta.get("created_at", 0),
            })
        roots.sort(key=lambda x: x.get("created_at", 0), reverse=True)
        return {"correspondences": roots, "count": len(roots)}

    def op_map(self) -> Dict[str, Any]:
        self._require_concept()
        meta = self._meta(self.concept_id)
        return {
            "corr_id": self.concept_id,
            "concept_id": self.concept_id,
            "title": meta.get("title", ""),
            **{suffix: self._members(suffix) for suffix in self.SUBSETS},
        }

    def op_delete(self) -> Dict[str, Any]:
        self._require_concept()
        target = self.concept_id
        self.cortex.remove_from_set(INDEX_SET, target)
        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, None)
        self.concept_id = None
        return {"status": "deleted", "corr_id": target, "soft_delete": True}

    # ------------------------------------------------------------------
    # Systems
    # ------------------------------------------------------------------

    def op_add_system(
        self,
        label: str,
        system_type: str = "generic",
        ref_id: str = "",
        ref_universe: str = "",
        description: str = "",
    ) -> Dict[str, Any]:
        self._require_concept()
        if not label:
            raise ValueError("system label is required.")
        if ref_id:
            self._require_access(ref_id, "Referenced system atom")
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=description or label,
            atom_type="corr_system",
            subset="systems",
            meta_extra={
                "role": "system",
                "label": label,
                "system_type": system_type,
                "ref_id": ref_id or None,
                "ref_universe": ref_universe,
            },
            concept_word="system",
        )
        if ref_id:
            self.cortex.put_link(key, ref_id, "corr:refers_to", author=author_id)
        return {
            "status": "system_added",
            "system_id": key,
            "label": label,
            "system_type": system_type,
        }

    # ------------------------------------------------------------------
    # Source management
    # ------------------------------------------------------------------

    def op_add_source(
        self,
        ref_id: str = "",
        kind: str = "other",
        title: str = "",
        url: str = "",
        author: str = "",
        publisher: str = "",
        published: str = "",
        retrieved: str = "",
        credibility: float = 0.5,
        independence: float = 0.5,
        note: str = "",
    ) -> Dict[str, Any]:
        self._require_concept()
        if kind not in SOURCE_KINDS:
            raise ValueError(f"kind must be one of {SOURCE_KINDS}.")
        if ref_id:
            self._require_access(ref_id, "Source reference")
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=note or title or url or ref_id,
            atom_type="corr_source",
            subset="sources",
            meta_extra={
                "role": "source",
                "ref_id": ref_id or None,
                "kind": kind,
                "title": title,
                "url": url,
                "author": author,
                "publisher": publisher,
                "published": published,
                "retrieved": retrieved,
                "credibility": self._clamp01(credibility, 0.5),
                "independence": self._clamp01(independence, 0.5),
            },
            concept_word="source",
        )
        if ref_id:
            self.cortex.put_link(key, ref_id, "corr:refers_to", author=author_id)
        return {
            "status": "source_added",
            "source_id": key,
            "kind": kind,
            "credibility": self._clamp01(credibility, 0.5),
        }

    def op_eval_source(
        self,
        source_id: str,
        credibility: Optional[float] = None,
        independence: Optional[float] = None,
        note: str = "",
    ) -> Dict[str, Any]:
        self._require_concept()
        self._require_access(source_id, "Source")
        author_id, _ = self._author_and_scopes()
        source_meta = self._meta(source_id)
        updates: Dict[str, Any] = {}
        if credibility is not None:
            updates["credibility"] = self._clamp01(credibility, 0.5)
        if independence is not None:
            updates["independence"] = self._clamp01(independence, 0.5)
        key = self._put_atom(
            content=note or f"source_eval:{source_id[:12]}",
            atom_type="corr_source_eval",
            subset="source_evals",
            meta_extra={
                "role": "source_eval",
                "source_id": source_id,
                "previous": {
                    "credibility": source_meta.get("credibility"),
                    "independence": source_meta.get("independence"),
                },
                "updates": updates,
            },
            concept_word="source_eval",
        )
        self.cortex.put_link(source_id, key, "corr:evaluated_by", author=author_id)
        return {
            "status": "source_evaluated",
            "eval_id": key,
            "source_id": source_id,
            "updates": updates,
        }

    # ------------------------------------------------------------------
    # Direct correspondence links
    # ------------------------------------------------------------------

    def op_add_link(
        self,
        src_id: str,
        dst_id: str,
        relation: str,
        source_id: str,
        src_system_id: str = "",
        dst_system_id: str = "",
        direction: str = "directed",
        confidence: float = 0.7,
        status: str = "active",
        scope: Optional[Dict[str, Any]] = None,
        valid_from: str = "",
        valid_to: str = "",
        context: str = "",
        perspective: str = "",
        note: str = "",
    ) -> Dict[str, Any]:
        self._require_concept()
        self._require_access(src_id, "Source-side atom")
        self._require_access(dst_id, "Destination-side atom")
        self._require_access(source_id, "Evidence source")
        if src_system_id:
            self._require_access(src_system_id, "Source system")
        if dst_system_id:
            self._require_access(dst_system_id, "Destination system")
        if relation not in RELATION_TYPES:
            raise ValueError(f"relation must be one of {RELATION_TYPES}.")
        if status not in STATUS_TYPES:
            raise ValueError(f"status must be one of {STATUS_TYPES}.")
        if direction not in ("directed", "mutual"):
            raise ValueError("direction must be directed or mutual.")
        author_id, _ = self._author_and_scopes()
        credibility = self._effective_source_credibility(source_id)
        final_confidence = round(self._clamp01(confidence, 0.7) * credibility, 4)
        mapping_scope = self._normal_scope(
            scope=scope, valid_from=valid_from, valid_to=valid_to,
            context=context, perspective=perspective,
        )
        key = self._put_atom(
            content=note or f"{src_id[:8]} {relation} {dst_id[:8]}",
            atom_type="corr_link",
            subset="links",
            meta_extra={
                "role": "link",
                "origin": "direct",
                "src_id": src_id,
                "dst_id": dst_id,
                "src_system_id": src_system_id or None,
                "dst_system_id": dst_system_id or None,
                "relation": relation,
                "direction": direction,
                "source_id": source_id,
                "scope": mapping_scope,
                "confidence": final_confidence,
                "raw_confidence": self._clamp01(confidence, 0.7),
                "source_credibility": credibility,
                "status": status,
            },
            concept_word=relation,
        )
        rel = f"corr:{relation}"
        self.cortex.put_link(src_id, dst_id, rel, author=author_id)
        if direction == "mutual":
            self.cortex.put_link(dst_id, src_id, rel, author=author_id)
        self.cortex.put_link(key, src_id, "corr:from", author=author_id)
        self.cortex.put_link(key, dst_id, "corr:to", author=author_id)
        self.cortex.put_link(key, source_id, "corr:evidenced_by", author=author_id)
        if src_system_id:
            self.cortex.put_link(key, src_system_id, "corr:src_system", author=author_id)
        if dst_system_id:
            self.cortex.put_link(key, dst_system_id, "corr:dst_system", author=author_id)
        return {
            "status": "link_added",
            "link_id": key,
            "relation": relation,
            "confidence": final_confidence,
        }

    def op_add_inferred_link(
        self,
        src_id: str,
        dst_id: str,
        relation: str,
        inputs: List[Dict[str, Any]],
        src_system_id: str = "",
        dst_system_id: str = "",
        direction: str = "directed",
        extraction_method: str = "human",
        extraction_confidence: float = 0.8,
        extraction_model: str = "",
        extraction_llm_trust: float = 1.0,
        inference_method: str = "human",
        inference_confidence: float = 0.8,
        inference_model: str = "",
        inference_llm_trust: float = 1.0,
        steps: Optional[List[Dict[str, Any]]] = None,
        status: str = "active",
        scope: Optional[Dict[str, Any]] = None,
        valid_from: str = "",
        valid_to: str = "",
        context: str = "",
        perspective: str = "",
        note: str = "",
    ) -> Dict[str, Any]:
        self._require_concept()
        self._require_access(src_id, "Source-side atom")
        self._require_access(dst_id, "Destination-side atom")
        if relation not in RELATION_TYPES:
            raise ValueError(f"relation must be one of {RELATION_TYPES}.")
        if not inputs:
            raise ValueError("inferred link requires at least one input source.")
        if extraction_method not in ALGO_METHODS:
            raise ValueError(f"extraction_method must be one of {ALGO_METHODS}.")
        if inference_method not in ALGO_METHODS:
            raise ValueError(f"inference_method must be one of {ALGO_METHODS}.")
        if status not in STATUS_TYPES:
            raise ValueError(f"status must be one of {STATUS_TYPES}.")
        if direction not in ("directed", "mutual"):
            raise ValueError("direction must be directed or mutual.")
        if src_system_id:
            self._require_access(src_system_id, "Source system")
        if dst_system_id:
            self._require_access(dst_system_id, "Destination system")
        for inp in inputs:
            self._require_access(inp.get("source_id", ""), "Input source")
        author_id, _ = self._author_and_scopes()
        provenance = self._build_provenance(
            inputs=inputs,
            extraction_method=extraction_method,
            extraction_confidence=extraction_confidence,
            extraction_model=extraction_model,
            extraction_llm_trust=extraction_llm_trust,
            inference_method=inference_method,
            inference_confidence=inference_confidence,
            inference_model=inference_model,
            inference_llm_trust=inference_llm_trust,
            steps=steps,
        )
        final_confidence = provenance["overall_confidence"]
        source_weighted = provenance["source_weighted_credibility"]
        mapping_scope = self._normal_scope(
            scope=scope, valid_from=valid_from, valid_to=valid_to,
            context=context, perspective=perspective,
        )
        key = self._put_atom(
            content=note or f"inferred:{src_id[:8]} {relation} {dst_id[:8]}",
            atom_type="corr_link",
            subset="links",
            meta_extra={
                "role": "link",
                "origin": "inferred",
                "src_id": src_id,
                "dst_id": dst_id,
                "src_system_id": src_system_id or None,
                "dst_system_id": dst_system_id or None,
                "relation": relation,
                "direction": direction,
                "scope": mapping_scope,
                "confidence": final_confidence,
                "status": status,
                "provenance": provenance,
            },
            concept_word=f"inferred_{relation}",
        )
        rel = f"corr:{relation}"
        self.cortex.put_link(src_id, dst_id, rel, author=author_id)
        if direction == "mutual":
            self.cortex.put_link(dst_id, src_id, rel, author=author_id)
        self.cortex.put_link(key, src_id, "corr:from", author=author_id)
        self.cortex.put_link(key, dst_id, "corr:to", author=author_id)
        for inp in inputs:
            self.cortex.put_link(key, inp["source_id"], "corr:evidenced_by", author=author_id)
        if src_system_id:
            self.cortex.put_link(key, src_system_id, "corr:src_system", author=author_id)
        if dst_system_id:
            self.cortex.put_link(key, dst_system_id, "corr:dst_system", author=author_id)
        return {
            "status": "inferred_link_added",
            "link_id": key,
            "relation": relation,
            "confidence": final_confidence,
            "source_weighted_credibility": source_weighted,
        }

    # ------------------------------------------------------------------
    # Projection
    # ------------------------------------------------------------------

    def op_add_projection(
        self,
        link_id: str,
        target_system_id: str,
        projected_relation: str = "",
        confidence_modifier: float = 1.0,
        source_id: str = "",
        note: str = "",
    ) -> Dict[str, Any]:
        """Project an existing correspondence into another system.

        Example:
            historical_region ↔ modern_prefecture
            then projected into game_world_region
        """
        self._require_concept()
        self._require_access(link_id, "Link")
        self._require_access(target_system_id, "Target system")
        if source_id:
            self._require_access(source_id, "Projection source")
        link_meta = self._meta(link_id)
        if link_meta.get("type") != "corr_link":
            raise RuntimeError(f"{link_id[:12]} is not a corr_link atom.")
        relation = projected_relation or link_meta.get("relation", "corresponds_to")
        if relation not in RELATION_TYPES:
            raise ValueError(f"relation must be one of {RELATION_TYPES}.")
        author_id, _ = self._author_and_scopes()
        base_conf = self._clamp01(link_meta.get("confidence", 0.5), 0.5)
        projected_conf = round(base_conf * self._clamp01(confidence_modifier, 1.0), 4)
        key = self._put_atom(
            content=note or f"projection:{link_id[:8]}",
            atom_type="corr_projection",
            subset="projections",
            meta_extra={
                "role": "projection",
                "source_link_id": link_id,
                "relation": relation,
                "target_system_id": target_system_id,
                "confidence": projected_conf,
                "confidence_modifier": confidence_modifier,
                "source_id": source_id or None,
            },
            concept_word="projection",
        )
        self.cortex.put_link(key, link_id, "corr:projects_from", author=author_id)
        self.cortex.put_link(key, target_system_id, "corr:projects_into", author=author_id)
        if source_id:
            self.cortex.put_link(key, source_id, "corr:evidenced_by", author=author_id)
        return {
            "status": "projection_added",
            "projection_id": key,
            "source_link_id": link_id,
            "target_system_id": target_system_id,
            "confidence": projected_conf,
        }

    # ------------------------------------------------------------------
    # Dispute
    # ------------------------------------------------------------------

    def op_dispute(
        self,
        target_id: str,
        reason: str,
        severity: str = "medium",
        source_id: str = "",
        note: str = "",
    ) -> Dict[str, Any]:
        """Record a dispute against a correspondence atom."""
        self._require_concept()
        self._require_access(target_id, "Target atom")
        if source_id:
            self._require_access(source_id, "Evidence source")
        if severity not in ("low", "medium", "high", "critical"):
            raise ValueError("severity must be one of: low, medium, high, critical.")
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=note or reason,
            atom_type="corr_dispute",
            subset="disputes",
            meta_extra={
                "role": "dispute",
                "target_id": target_id,
                "reason": reason,
                "severity": severity,
                "source_id": source_id or None,
            },
            concept_word="dispute",
        )
        self.cortex.put_link(target_id, key, "corr:disputed_by", author=author_id)
        if source_id:
            self.cortex.put_link(key, source_id, "corr:evidenced_by", author=author_id)
        return {
            "status": "dispute_recorded",
            "dispute_id": key,
            "target_id": target_id,
            "severity": severity,
        }

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------

    def op_eval(
        self,
        link_id: str,
        confidence: Optional[float] = None,
        status: str = "",
        note: str = "",
    ) -> Dict[str, Any]:
        """Event-sourced evaluation for correspondence links."""
        self._require_concept()
        self._require_access(link_id, "Link")
        link_meta = self._meta(link_id)
        if link_meta.get("type") != "corr_link":
            raise RuntimeError(f"{link_id[:12]} is not a corr_link atom.")
        if status and status not in STATUS_TYPES:
            raise ValueError(f"status must be one of {STATUS_TYPES}.")
        updates: Dict[str, Any] = {}
        if confidence is not None:
            updates["confidence"] = self._clamp01(confidence, 0.5)
        if status:
            updates["status"] = status
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=note or f"link_eval:{link_id[:12]}",
            atom_type="corr_eval",
            subset="evals",
            meta_extra={
                "role": "evaluation",
                "target_id": link_id,
                "previous": {
                    "confidence": link_meta.get("confidence"),
                    "status": link_meta.get("status"),
                },
                "updates": updates,
            },
            concept_word="evaluation",
        )
        self.cortex.put_link(link_id, key, "corr:evaluated_by", author=author_id)
        return {
            "status": "evaluation_added",
            "evaluation_id": key,
            "target_id": link_id,
            "updates": updates,
        }

    # ------------------------------------------------------------------
    # Trace
    # ------------------------------------------------------------------

    def op_trace(self, link_id: str) -> Dict[str, Any]:
        """Trace provenance and evidence chain for a correspondence link."""
        self._require_concept()
        self._require_access(link_id, "Link")
        meta = self._meta(link_id)
        if meta.get("type") != "corr_link":
            raise RuntimeError(f"{link_id[:12]} is not a corr_link atom.")
        result: Dict[str, Any] = {
            "link_id": link_id,
            "relation": meta.get("relation"),
            "origin": meta.get("origin"),
            "confidence": meta.get("confidence"),
            "status": meta.get("status"),
            "scope": meta.get("scope", {}),
            "src_id": meta.get("src_id"),
            "dst_id": meta.get("dst_id"),
            "content": self._content(link_id),
        }
        if meta.get("origin") == "direct":
            src = meta.get("source_id")
            result["source"] = (
                self._summary(src) if src and self._visible(src) else None
            )
            result["confidence_breakdown"] = {
                "raw_confidence": meta.get("raw_confidence"),
                "source_credibility": meta.get("source_credibility"),
                "formula": "raw_confidence × source_credibility",
            }
        elif meta.get("origin") == "inferred":
            prov = meta.get("provenance", {})
            result["provenance"] = prov
            result["input_sources"] = [
                self._summary(inp["source_id"])
                for inp in prov.get("inputs", [])
                if self._visible(inp.get("source_id", ""))
            ]
            result["credibility_breakdown"] = {
                "extraction_confidence": prov.get("extraction_algorithm", {}).get("confidence"),
                "inference_confidence": prov.get("inference_algorithm", {}).get("confidence"),
                "source_weighted_credibility": prov.get("source_weighted_credibility"),
                "overall_confidence": prov.get("overall_confidence"),
                "formula": prov.get("formula"),
            }
        disputes = [
            self._summary(d)
            for d in self._members("disputes")
            if self._meta(d).get("target_id") == link_id
        ]
        result["disputes"] = disputes
        result["graph_trace"] = self._graph().trace(
            start_id=link_id,
            rels=[
                "corr:evidenced_by",
                "corr:evaluated_by",
                "corr:disputed_by",
            ],
            depth=4,
            include_incoming=True,
        )
        return result

    # ------------------------------------------------------------------
    # Diagnose
    # ------------------------------------------------------------------

    def op_diagnose(self, limit: int = 10) -> Dict[str, Any]:
        """Diagnose correspondence quality and modeling gaps."""
        self._require_concept()
        links      = [self._summary(k) for k in self._members("links")]
        disputes   = [self._summary(k) for k in self._members("disputes")]
        projections = [self._summary(k) for k in self._members("projections")]

        low_confidence_links = [
            lnk for lnk in links
            if float(lnk["meta"].get("confidence", 1.0)) < 0.4
        ]
        disputed_links = [
            lnk for lnk in links
            if any(d["meta"].get("target_id") == lnk["id"] for d in disputes)
        ]
        expired_links = [
            lnk for lnk in links
            if (lnk["meta"].get("scope") or {}).get("valid_to")
        ]
        inferred_links = [
            lnk for lnk in links if lnk["meta"].get("origin") == "inferred"
        ]
        projections_without_target = [
            p for p in projections
            if not self._visible(p["meta"].get("target_system_id", ""))
        ]
        return {
            "corr_root_id": self.concept_id,
            "counts": {
                "links":       len(links),
                "disputes":    len(disputes),
                "projections": len(projections),
            },
            "diagnosis": {
                "low_confidence_links":       low_confidence_links[-limit:],
                "disputed_links":             disputed_links[-limit:],
                "expired_links":              expired_links[-limit:],
                "inferred_links":             inferred_links[-limit:],
                "projections_without_target": projections_without_target[-limit:],
            },
        }
