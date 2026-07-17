"""
Aggregation Concept Model.

Builds a statistical analysis structure on top of an existing source corpus
(originally designed for Survey, but any Cortex atom can be the source root).

Topology:
  AggregationRoot (concept="aggregation", role="root")
    ├── Units      — any Cortex atoms indexed for this analysis (agg:unit links)
    ├── Groups     — labelled partitions of units (agg:group / agg:member links)
    ├── Measures   — key/value statistics attached to a group (agg:measure links)
    ├── Analysis   — directed relation between two groups with a score
    └── Hierarchy  — tree nodes that structure groups (agg:hierarchy / agg:child)

Namespace contract (two-namespace rule):
  - Content atoms  → set:agg:{concept_id}  AND  set:agg:{concept_id}:{subset}
  - Concept-word atom → set:concept:{concept_id}  (concept catalog scope)
"""

import time
import logging
from typing import Any, Dict, List, Optional

from lib.akasha.concepts.base import BaseConcept

logger = logging.getLogger("Harmonia.Concept.Aggregation")

INDEX_SET = "set:agg:index"
CONTEXT_KEY_ACTIVE = "active_aggregation_root"
_CONCEPT_WORD_ALIAS_PREFIX = "concept:word:"


class AggregationConcept(BaseConcept):
    """Unit → Group → Measure → Analysis → Hierarchy aggregation model."""

    CONCEPT_PREFIX = "agg"
    CONCEPT_METHODS = {
        "new":          {"op": "op_new"},
        # Accept both "agg_id" and "aggregation_id" since the API returns the latter
        "open":         {"op": "op_open",
                         "coerce": lambda d: {
                             "agg_id": d.get("agg_id") or d.get("aggregation_id", ""),
                         }},
        "ls":           {"op": "op_list_all"},
        "unit.add":     {"op": "op_add_unit"},
        "group.add":    {"op": "op_add_group"},
        "measure.add":  {"op": "op_add_measure"},
        "analysis.add": {"op": "op_add_analysis"},
        "hier.add":     {"op": "op_add_hierarchy"},
        "list":         {"op": "op_list"},
        "rm":           {"op": "op_delete"},
    }

    def __init__(self, session: Any, concept_id: Optional[str] = None):
        super().__init__(session, concept_id)
        if not self.concept_id:
            stored = getattr(self.session, "get_context", lambda k: None)(CONTEXT_KEY_ACTIVE)
            if stored:
                self.concept_id = stored
                self.set_name = f"set:concept:{self.concept_id}"

    # ── Private helpers ───────────────────────────────────────────────────────

    def _agg_set(self, suffix: Optional[str] = None) -> str:
        base = f"set:agg:{self.concept_id}"
        return f"{base}:{suffix}" if suffix else base

    def _author_and_scopes(self):
        author_id = getattr(self.session, "client_id", "system")
        scopes = [f"owner:user_{author_id}", f"view:user_{author_id}"]
        return author_id, scopes

    def _get_or_create_concept_word(self, word: str) -> str:
        alias = f"{_CONCEPT_WORD_ALIAS_PREFIX}{word}"
        existing = self.cortex.resolve_alias(alias)
        if existing:
            return existing
        author_id, scopes = self._author_and_scopes()
        key = self.cortex.put_chunk(
            content=word,
            meta={
                "type":          "concept_word",
                "word":          word,
                "concept_model": "aggregation",
                "created_at":    time.time(),
            },
            author=author_id,
            scopes=scopes,
        )
        self.cortex.set_alias(key, alias)
        return key

    def _register_to_package(self, key: str, subset_suffix: Optional[str], concept_word: str) -> None:
        """Dual-namespace: content atom → agg-scope (main + sub), concept-word → concept catalog."""
        author_id, _ = self._author_and_scopes()
        self.cortex.add_to_set(self._agg_set(), key)
        if subset_suffix:
            self.cortex.add_to_set(self._agg_set(subset_suffix), key)
        cw_key = self._get_or_create_concept_word(concept_word)
        self.register_concept_node(cw_key)
        self.cortex.put_link(key, cw_key, "sys:derived_from", author=author_id)

    def _require_access(self, atom_id: str, label: str = "Atom") -> None:
        """Guard: raises RuntimeError if atom_id is not accessible in current session."""
        if not self.cortex.check_access(atom_id, self.allowed_scopes):
            raise RuntimeError(f"{label} not accessible: {atom_id[:12]}")

    # ── Operators ─────────────────────────────────────────────────────────────

    def op_new(self, source_id: str) -> Dict[str, Any]:
        """[agg.new] Create an AggregationRoot linked to a source corpus atom."""
        author_id, scopes = self._author_and_scopes()

        agg_id = self.cortex.put_chunk(
            content=f"[Aggregation for {source_id[:8]}]",
            meta={
                "type":       "concept",
                "concept":    "aggregation",
                "role":       "root",
                "source_id":  source_id,
                "created_at": time.time(),
            },
            author=author_id,
            scopes=scopes,
        )

        self.concept_id = agg_id
        self.set_name   = f"set:concept:{self.concept_id}"

        self.ensure_concept_set()
        self._register_to_package(agg_id, subset_suffix=None, concept_word="aggregation")

        for suffix in (None, "units", "groups", "measures", "analysis", "hierarchy"):
            self.cortex.create_set(self._agg_set(suffix))

        self.cortex.create_set(INDEX_SET)
        self.cortex.add_to_set(INDEX_SET, agg_id)

        self.cortex.put_link(source_id, agg_id, "sys:has_aggregation", author=author_id)
        self.cortex.put_link(agg_id, source_id, "sys:for_source",      author=author_id)

        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, agg_id)

        logger.info("[AggregationConcept] Created aggregation for source %s (%s)", source_id[:8], agg_id[:8])
        return {"status": "created", "aggregation_id": agg_id, "source_id": source_id}

    def op_open(self, agg_id: str) -> Dict[str, Any]:
        """[agg.open] Mount an existing aggregation as the session's active aggregation."""
        meta = self.cortex.get_meta(agg_id)
        if not meta or meta.get("concept") != "aggregation":
            raise RuntimeError(f"Atom '{agg_id[:12]}' is not an aggregation root.")

        self.concept_id = agg_id
        self.set_name   = f"set:concept:{self.concept_id}"

        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, agg_id)

        return {
            "status":         "opened",
            "aggregation_id": agg_id,
            "source_id":      meta.get("source_id", ""),
        }

    def op_list_all(self) -> Dict[str, Any]:
        """[agg.ls] List all aggregation roots accessible to this session."""
        members = self.cortex.get_collection_members(INDEX_SET)
        items: List[Dict[str, Any]] = []
        for key in members:
            if not self.cortex.check_access(key, self.allowed_scopes):
                continue
            meta = self.cortex.get_meta(key) or {}
            if meta.get("concept") != "aggregation":
                continue
            items.append({
                "aggregation_id": key,
                "source_id":      meta.get("source_id", ""),
                "created_at":     meta.get("created_at", 0),
            })
        items.sort(key=lambda x: x.get("created_at", 0), reverse=True)
        return {"aggregations": items, "count": len(items)}

    def op_add_unit(self, unit_id: str) -> Dict[str, Any]:
        """[agg.unit.add] Index any accessible Cortex atom as an aggregation unit."""
        self._require_concept()
        author_id, _ = self._author_and_scopes()

        self._require_access(unit_id, "Unit atom")

        self.cortex.add_to_set(self._agg_set("units"), unit_id)
        self.cortex.put_link(self.concept_id, unit_id, "agg:unit", author=author_id)

        return {"status": "unit_added", "unit": unit_id}

    def op_add_group(
        self,
        label: str,
        members: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """[agg.group.add] Create a labelled group and optionally assign initial member atoms."""
        self._require_concept()
        author_id, scopes = self._author_and_scopes()

        group_id = self.cortex.put_chunk(
            content=f"[Group: {label}]",
            meta={
                "type":       "agg_group",
                "label":      label,
                "created_at": time.time(),
            },
            author=author_id,
            scopes=scopes,
        )
        self.cortex.add_to_set(self._agg_set(), group_id)
        self.cortex.add_to_set(self._agg_set("groups"), group_id)
        self.cortex.put_link(self.concept_id, group_id, "agg:group", author=author_id)

        for m in (members or []):
            self._require_access(m, "Member atom")
            self.cortex.put_link(group_id, m, "agg:member", author=author_id)

        return {"status": "group_added", "group_id": group_id}

    def op_add_measure(self, group_id: str, key: str, value: Any) -> Dict[str, Any]:
        """[agg.measure.add] Attach a key/value statistic to a group."""
        self._require_concept()
        author_id, scopes = self._author_and_scopes()

        self._require_access(group_id, "Group atom")

        measure_id = self.cortex.put_chunk(
            content=str(value),
            meta={
                "type":       "agg_measure",
                "group_id":   group_id,
                "key":        key,
                "value":      value,
                "created_at": time.time(),
            },
            author=author_id,
            scopes=scopes,
        )
        self.cortex.add_to_set(self._agg_set(), measure_id)
        self.cortex.add_to_set(self._agg_set("measures"), measure_id)
        self.cortex.put_link(group_id, measure_id, "agg:measure", author=author_id)

        return {"status": "measure_added", "measure_id": measure_id}

    def op_add_analysis(
        self,
        src_group: str,
        dst_group: str,
        relation: str,
        score: float,
    ) -> Dict[str, Any]:
        """[agg.analysis.add] Record a directed relation between two groups with a numeric score."""
        self._require_concept()
        author_id, scopes = self._author_and_scopes()

        self._require_access(src_group, "Source group atom")
        self._require_access(dst_group, "Destination group atom")

        rel_id = self.cortex.put_chunk(
            content=f"{relation}:{score}",
            meta={
                "type":       "agg_analysis",
                "src":        src_group,
                "dst":        dst_group,
                "relation":   relation,
                "score":      score,
                "created_at": time.time(),
            },
            author=author_id,
            scopes=scopes,
        )
        self.cortex.add_to_set(self._agg_set(), rel_id)
        self.cortex.add_to_set(self._agg_set("analysis"), rel_id)
        self.cortex.put_link(src_group, rel_id, "agg:analysis_out", author=author_id)
        self.cortex.put_link(dst_group, rel_id, "agg:analysis_in",  author=author_id)

        return {"status": "analysis_added", "analysis_id": rel_id}

    def op_add_hierarchy(
        self,
        label: str,
        children: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """[agg.hier.add] Create a hierarchy node; optionally attach existing group atoms as children."""
        self._require_concept()
        author_id, scopes = self._author_and_scopes()

        node_id = self.cortex.put_chunk(
            content=f"[Hierarchy: {label}]",
            meta={
                "type":       "agg_hierarchy",
                "label":      label,
                "created_at": time.time(),
            },
            author=author_id,
            scopes=scopes,
        )
        self.cortex.add_to_set(self._agg_set(), node_id)
        self.cortex.add_to_set(self._agg_set("hierarchy"), node_id)
        self.cortex.put_link(self.concept_id, node_id, "agg:hierarchy", author=author_id)

        for g in (children or []):
            self._require_access(g, "Child group atom")
            self.cortex.put_link(node_id, g, "agg:child", author=author_id)

        return {"status": "hierarchy_added", "node_id": node_id}

    def op_list(self) -> Dict[str, Any]:
        """[agg.list] Return the structural inventory of the active aggregation."""
        self._require_concept()
        allowed = self.allowed_scopes

        def safe_members(suffix: str) -> List[str]:
            return [
                k for k in self.cortex.get_collection_members(self._agg_set(suffix))
                if self.cortex.check_access(k, allowed)
            ]

        return {
            "aggregation_id": self.concept_id,
            "units":          safe_members("units"),
            "groups":         safe_members("groups"),
            "measures":       safe_members("measures"),
            "analysis":       safe_members("analysis"),
            "hierarchy":      safe_members("hierarchy"),
        }

    def op_delete(self) -> Dict[str, Any]:
        """[agg.rm] Delete the active aggregation root and clear session context."""
        self._require_concept()
        agg_id = self.concept_id
        self.cortex.drop_chunk(agg_id, requester_scopes=self.allowed_scopes)
        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, None)
        return {"status": "deleted", "aggregation_id": agg_id}
