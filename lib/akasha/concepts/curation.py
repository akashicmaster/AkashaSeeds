"""
Curation Concept Model.
Premise-bound reconciliation engine.
Curation is NOT a truth engine.
It creates conditional, auditable views from conflicting facts, correspondences,
country events, claims, sovereignty records, and other evidence-bearing atoms.
Core idea:
    Inputs remain intact.
    Curation creates a View under a stated Premise.
    Conflicts are folded only inside that View.
    Unresolved conflicts are first-class outputs.
Version: 1.0.0
"""
import time
import logging
from typing import Any, Dict, List, Optional
from lib.akasha.concepts.base import BaseConcept

logger = logging.getLogger("Harmonia.Concept.Curation")

CONTEXT_KEY_ACTIVE = "active_curation_root"
INDEX_SET = "set:curation:index"
_CONCEPT_WORD_ALIAS_PREFIX = "concept:word:"

SUBSET_TO_RELATION: Dict[str, str] = {
    "premises":    "curation:has_premise",
    "inputs":      "curation:has_input",
    "views":       "curation:has_view",
    "folds":       "curation:has_fold",
    "conclusions": "curation:has_conclusion",
    "disputes":    "curation:has_dispute",
}

CONFLICT_POLICIES = (
    "highest_credibility",
    "most_recent",
    "perspective_preferred",
    "source_policy",
    "leave_unresolved",
    "manual",
    "composite",
)

INPUT_ROLES = (
    "fact",
    "correspondence",
    "country_event",
    "country_claim",
    "sovereignty",
    "administration",
    "law",
    "source",
    "assessment",
    "other",
)

CONCLUSION_TYPES = (
    "state",
    "event",
    "relation",
    "assessment",
    "estimate",
    "recommendation_basis",
    "unresolved",
    "other",
)

VIEW_STATUS = (
    "draft",
    "active",
    "superseded",
    "disputed",
    "archived",
)


class CurationConcept(BaseConcept):
    """Premise-bound conflict reconciliation and view construction."""

    CONCEPT_PREFIX = "curation"
    CONTEXT_KEY_ACTIVE = CONTEXT_KEY_ACTIVE

    CONCEPT_METHODS = {
        "new": {"op": "op_new"},
        "open": {
            "op": "op_open",
            "coerce": lambda d: {
                "curation_id": d.get("curation_id") or d.get("id") or d.get("concept_id", "")
            },
        },
        "ls":       {"op": "op_list_all"},
        "map":      {"op": "op_map"},
        "rm":       {"op": "op_delete"},
        "premise.add":    {"op": "op_add_premise"},
        "input.add":      {"op": "op_add_input"},
        "view.run":       {"op": "op_run_view"},
        "fold.add":       {"op": "op_add_fold"},
        "conclusion.add": {"op": "op_add_conclusion"},
        "dispute.add":    {"op": "op_add_dispute"},
        "trace":    {"op": "op_trace"},
        "diagnose": {"op": "op_diagnose"},
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

    def _cur_set(self, suffix: Optional[str] = None) -> str:
        base = f"set:curation:{self.concept_id}"
        return f"{base}:{suffix}" if suffix else base

    def _author_and_scopes(self):
        author_id = getattr(self.session, "client_id", "system")
        scopes = [f"owner:user_{author_id}", f"view:user_{author_id}"]
        return author_id, scopes

    def _create_sets(self) -> None:
        self.cortex.create_set(self.set_name)
        self.cortex.create_set(self._cur_set())
        for suffix in self.SUBSETS:
            self.cortex.create_set(self._cur_set(suffix))
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
                "concept_model": "curation",
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
        self.cortex.add_to_set(self._cur_set(), key)
        if subset_suffix:
            self.cortex.add_to_set(self._cur_set(subset_suffix), key)
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
            key for key in self.cortex.get_collection_members(self._cur_set(suffix))
            if self._visible(key)
        ]

    def _meta(self, key: str) -> Dict[str, Any]:
        return self.cortex.get_meta(key) or {}

    def _content(self, key: str) -> str:
        value = self.cortex.get_chunk(key)
        if isinstance(value, dict):
            return value.get("content", "")
        return value or ""

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
            "concept": "curation",
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
        relation = SUBSET_TO_RELATION.get(subset, f"curation:has_{subset}")
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

    # ------------------------------------------------------------------
    # Basic operators
    # ------------------------------------------------------------------

    def op_new(self, title: str, description: str = "") -> Dict[str, Any]:
        author_id, scopes = self._author_and_scopes()
        if not title:
            raise ValueError("curation.new requires title.")
        root_id = self.cortex.put_chunk(
            content=f"[ Curation: {title} ]",
            meta={
                "type": "concept",
                "concept": "curation",
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
        self.cortex.add_to_set(self._cur_set(), root_id)
        self.cortex.add_to_set(INDEX_SET, root_id)
        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, root_id)
        return {
            "status": "created",
            "concept_id": root_id,
            "curation_id": root_id,
            "title": title,
        }

    def op_open(self, curation_id: str) -> Dict[str, Any]:
        meta = self._meta(curation_id)
        if not meta or meta.get("concept") != "curation":
            raise RuntimeError(f"Atom '{curation_id[:12]}' is not a curation root.")
        if not self._visible(curation_id):
            raise RuntimeError(f"Curation not accessible: {curation_id[:12]}")
        self.concept_id = curation_id
        self.set_name = f"set:concept:{self.concept_id}"
        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, curation_id)
        return {
            "status": "opened",
            "concept_id": curation_id,
            "curation_id": curation_id,
            "title": meta.get("title", ""),
        }

    def op_list_all(self) -> Dict[str, Any]:
        items = []
        for key in self.cortex.get_collection_members(INDEX_SET):
            if not self._visible(key):
                continue
            meta = self._meta(key)
            if meta.get("concept") != "curation":
                continue
            items.append({
                "curation_id": key,
                "concept_id": key,
                "title": meta.get("title", ""),
                "created_at": meta.get("created_at", 0),
            })
        items.sort(key=lambda x: x.get("created_at", 0), reverse=True)
        return {"curations": items, "count": len(items)}

    def op_delete(self) -> Dict[str, Any]:
        self._require_concept()
        target = self.concept_id
        # Soft delete: remove from index, preserve atoms for auditability.
        self.cortex.remove_from_set(INDEX_SET, target)
        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, None)
        return {"status": "deleted", "curation_id": target, "soft_delete": True}

    # ------------------------------------------------------------------
    # Premise / Input
    # ------------------------------------------------------------------

    def op_add_premise(
        self,
        label: str,
        as_of: str = "",
        perspective: str = "",
        source_policy: str = "all_accessible",
        conflict_policy: str = "leave_unresolved",
        policy_steps: Optional[List[Dict[str, Any]]] = None,
        mode: str = "normal",
        scope: Optional[Dict[str, Any]] = None,
        note: str = "",
    ) -> Dict[str, Any]:
        """
        Add a premise.

        A Premise defines the world-view under which conflicts may be folded.
        Curation is conditional — outputs are always relative to their premise.

        policy_steps: composable conflict resolution pipeline.
            Example:
                [
                  {"op": "filter", "field": "confidence", "gte": 0.5},
                  {"op": "prefer", "field": "perspective", "value": "de_facto"},
                  {"op": "prefer", "field": "time", "order": "newest"},
                  {"op": "fallback", "action": "leave_unresolved"}
                ]
        """
        self._require_concept()
        if not label:
            raise ValueError("premise label is required.")
        if conflict_policy not in CONFLICT_POLICIES:
            raise ValueError(f"conflict_policy must be one of {CONFLICT_POLICIES}.")
        key = self._put_atom(
            content=note or label,
            atom_type="curation_premise",
            subset="premises",
            meta_extra={
                "role": "premise",
                "label": label,
                "as_of": as_of,
                "perspective": perspective,
                "source_policy": source_policy,
                "conflict_policy": conflict_policy,
                "policy_steps": policy_steps or [],
                "mode": mode,
                "scope": scope or {},
            },
            concept_word="premise",
        )
        return {"status": "premise_added", "premise_id": key, "label": label}

    def op_add_input(
        self,
        ref_id: str,
        role: str = "other",
        source_model: str = "",
        premise_id: str = "",
        weight: float = 1.0,
        confidence: Optional[float] = None,
        status: str = "candidate",
        note: str = "",
    ) -> Dict[str, Any]:
        """
        Register an input atom for curation.

        Inputs can be facts, correspondences, country claims, sovereignty states,
        administrations, events, or any other evidence-bearing atom.
        The referenced atom is not copied — only a pointer is stored.
        """
        self._require_concept()
        self._require_access(ref_id, "Input")
        if premise_id:
            self._require_access(premise_id, "Premise")
        if role not in INPUT_ROLES:
            raise ValueError(f"role must be one of {INPUT_ROLES}.")
        author_id, _ = self._author_and_scopes()
        ref_meta = self._meta(ref_id)
        input_confidence = (
            self._clamp01(confidence, 0.5)
            if confidence is not None
            else self._clamp01(ref_meta.get("confidence", ref_meta.get("credibility", 0.5)), 0.5)
        )
        key = self._put_atom(
            content=note or f"input:{role}:{ref_id[:12]}",
            atom_type="curation_input",
            subset="inputs",
            meta_extra={
                "role": "input",
                "input_role": role,
                "ref_id": ref_id,
                "source_model": source_model or ref_meta.get("concept", ""),
                "premise_id": premise_id or None,
                "weight": float(weight),
                "confidence": input_confidence,
                "status": status,
            },
            concept_word="input",
        )
        self.cortex.put_link(key, ref_id, "curation:refers_to", author=author_id)
        if premise_id:
            self.cortex.put_link(key, premise_id, "curation:under_premise", author=author_id)
        return {
            "status": "input_added",
            "input_id": key,
            "ref_id": ref_id,
            "role": role,
            "confidence": input_confidence,
        }

    # ------------------------------------------------------------------
    # View / Fold / Conclusion
    # ------------------------------------------------------------------

    def op_run_view(
        self,
        premise_id: str,
        label: str = "",
        input_ids: Optional[List[str]] = None,
        derive_from_view_id: str = "",
        status: str = "draft",
        note: str = "",
    ) -> Dict[str, Any]:
        """
        Create a View under a Premise.

        Does not automatically decide truth — gathers candidate inputs and
        records the premise-bound view state. Views may be derived from
        prior views for historiography lineage.
        """
        self._require_concept()
        self._require_access(premise_id, "Premise")
        if derive_from_view_id:
            self._require_access(derive_from_view_id, "Parent view")
        if status not in VIEW_STATUS:
            raise ValueError(f"status must be one of {VIEW_STATUS}.")
        author_id, _ = self._author_and_scopes()
        selected_inputs = input_ids or [
            i for i in self._members("inputs")
            if not self._meta(i).get("premise_id")
            or self._meta(i).get("premise_id") == premise_id
        ]
        for input_id in selected_inputs:
            self._require_access(input_id, "Input")
        premise_meta = self._meta(premise_id)
        view_label = label or f"view:{premise_meta.get('label', premise_id[:12])}"
        key = self._put_atom(
            content=note or view_label,
            atom_type="curation_view",
            subset="views",
            meta_extra={
                "role": "view",
                "label": view_label,
                "premise_id": premise_id,
                "input_ids": selected_inputs,
                "status": status,
                "derived_from_view_id": derive_from_view_id or None,
                "created_under": {
                    "as_of": premise_meta.get("as_of", ""),
                    "perspective": premise_meta.get("perspective", ""),
                    "conflict_policy": premise_meta.get("conflict_policy", ""),
                    "policy_steps": premise_meta.get("policy_steps", []),
                    "mode": premise_meta.get("mode", "normal"),
                },
            },
            concept_word="view",
        )
        self.cortex.put_link(key, premise_id, "curation:uses_premise", author=author_id)
        for input_id in selected_inputs:
            self.cortex.put_link(key, input_id, "curation:uses_input", author=author_id)
        if derive_from_view_id:
            self.cortex.put_link(key, derive_from_view_id, "curation:derived_from_view", author=author_id)
        return {
            "status": "view_created",
            "view_id": key,
            "premise_id": premise_id,
            "input_count": len(selected_inputs),
        }

    def op_add_fold(
        self,
        view_id: str,
        resolution_scope: Dict[str, Any],
        competing_input_ids: List[str],
        winner_id: str = "",
        dropped_ids: Optional[List[str]] = None,
        unresolved: bool = False,
        rationale: Optional[Dict[str, Any]] = None,
        note: str = "",
    ) -> Dict[str, Any]:
        """
        Record how a conflict was folded inside a View.

        Fold is an audit atom. It records what conflict was being resolved,
        which inputs competed, and the outcome (winner, dropped, or unresolved).

        resolution_scope example:
            {"entity": "<id>", "relation": "controlled_by",
             "time": "1940", "perspective": "de_facto"}
        """
        self._require_concept()
        self._require_access(view_id, "View")
        if not competing_input_ids:
            raise ValueError("fold requires competing_input_ids.")
        for input_id in competing_input_ids:
            self._require_access(input_id, "Competing input")
        if winner_id:
            self._require_access(winner_id, "Winner input")
        for dropped_id in self._as_list(dropped_ids):
            self._require_access(dropped_id, "Dropped input")
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=note or f"fold:{resolution_scope}",
            atom_type="curation_fold",
            subset="folds",
            meta_extra={
                "role": "fold",
                "view_id": view_id,
                "resolution_scope": resolution_scope,
                "competing_input_ids": competing_input_ids,
                "winner_id": winner_id or None,
                "dropped_ids": dropped_ids or [],
                "unresolved": bool(unresolved),
                "rationale": rationale or {},
            },
            concept_word="fold",
        )
        self.cortex.put_link(key, view_id, "curation:in_view", author=author_id)
        for input_id in competing_input_ids:
            self.cortex.put_link(key, input_id, "curation:compares", author=author_id)
        if winner_id:
            self.cortex.put_link(key, winner_id, "curation:selects", author=author_id)
        for dropped_id in self._as_list(dropped_ids):
            self.cortex.put_link(key, dropped_id, "curation:drops", author=author_id)
        return {
            "status": "fold_added",
            "fold_id": key,
            "view_id": view_id,
            "unresolved": bool(unresolved),
            "winner_id": winner_id or None,
        }

    def op_add_conclusion(
        self,
        view_id: str,
        statement: str,
        conclusion_type: str = "state",
        subject: str = "",
        predicate: str = "",
        obj: str = "",
        scope: Optional[Dict[str, Any]] = None,
        supported_by: Optional[List[str]] = None,
        confidence: float = 0.5,
        status: str = "provisional",
        note: str = "",
    ) -> Dict[str, Any]:
        """
        Add a structured conclusion inside a View.

        The natural-language statement is preserved alongside the
        subject/predicate/object triple for downstream processing.
        """
        self._require_concept()
        self._require_access(view_id, "View")
        if conclusion_type not in CONCLUSION_TYPES:
            raise ValueError(f"conclusion_type must be one of {CONCLUSION_TYPES}.")
        if not statement:
            raise ValueError("conclusion statement is required.")
        for support_id in self._as_list(supported_by):
            self._require_access(support_id, "Support atom")
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=note or statement,
            atom_type="curation_conclusion",
            subset="conclusions",
            meta_extra={
                "role": "conclusion",
                "view_id": view_id,
                "conclusion_type": conclusion_type,
                "statement": statement,
                "subject": subject,
                "predicate": predicate,
                "object": obj,
                "scope": scope or {},
                "supported_by": supported_by or [],
                "confidence": self._clamp01(confidence, 0.5),
                "status": status,
            },
            concept_word="conclusion",
        )
        self.cortex.put_link(key, view_id, "curation:concluded_in", author=author_id)
        for support_id in self._as_list(supported_by):
            self.cortex.put_link(key, support_id, "curation:supported_by", author=author_id)
        return {
            "status": "conclusion_added",
            "conclusion_id": key,
            "view_id": view_id,
            "confidence": self._clamp01(confidence, 0.5),
        }

    def op_add_dispute(
        self,
        target_id: str,
        reason: str,
        severity: str = "medium",
        source_id: str = "",
        note: str = "",
    ) -> Dict[str, Any]:
        self._require_concept()
        self._require_access(target_id, "Target")
        if source_id:
            self._require_access(source_id, "Source")
        if not reason:
            raise ValueError("dispute reason is required.")
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=note or reason,
            atom_type="curation_dispute",
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
        self.cortex.put_link(target_id, key, "curation:disputed_by", author=author_id)
        if source_id:
            self.cortex.put_link(key, source_id, "curation:evidenced_by", author=author_id)
        return {"status": "dispute_added", "dispute_id": key, "target_id": target_id}

    # ------------------------------------------------------------------
    # Analysis
    # ------------------------------------------------------------------

    def op_map(self) -> Dict[str, Any]:
        self._require_concept()
        meta = self._meta(self.concept_id)
        return {
            "curation_id": self.concept_id,
            "concept_id": self.concept_id,
            "title": meta.get("title", ""),
            **{suffix: self._members(suffix) for suffix in self.SUBSETS},
        }

    def op_trace(self, target_id: str) -> Dict[str, Any]:
        """
        Trace a Curation atom.

        View  → premise, inputs, folds, conclusions
        Fold  → competing inputs, winner, dropped
        Conclusion → view and support chain
        """
        self._require_concept()
        self._require_access(target_id, "Target")
        meta = self._meta(target_id)
        atom_type = meta.get("type", "")
        result: Dict[str, Any] = {
            "target_id": target_id,
            "type": atom_type,
            "content": self._content(target_id),
            "meta": meta,
        }
        if atom_type == "curation_view":
            premise_id = meta.get("premise_id")
            input_ids = meta.get("input_ids", [])
            result["premise"] = self._summary(premise_id) if self._visible(premise_id) else None
            result["inputs"] = [self._summary(i) for i in input_ids if self._visible(i)]
            result["folds"] = [
                self._summary(f)
                for f in self._members("folds")
                if self._meta(f).get("view_id") == target_id
            ]
            result["conclusions"] = [
                self._summary(c)
                for c in self._members("conclusions")
                if self._meta(c).get("view_id") == target_id
            ]
        elif atom_type == "curation_fold":
            view_id = meta.get("view_id", "")
            result["view"] = self._summary(view_id) if self._visible(view_id) else None
            result["competing_inputs"] = [
                self._summary(i)
                for i in meta.get("competing_input_ids", [])
                if self._visible(i)
            ]
            winner_id = meta.get("winner_id", "")
            result["winner"] = self._summary(winner_id) if self._visible(winner_id) else None
            result["dropped"] = [
                self._summary(i)
                for i in meta.get("dropped_ids", [])
                if self._visible(i)
            ]
        elif atom_type == "curation_conclusion":
            view_id = meta.get("view_id", "")
            result["view"] = self._summary(view_id) if self._visible(view_id) else None
            result["supported_by"] = [
                self._summary(i)
                for i in meta.get("supported_by", [])
                if self._visible(i)
            ]
        return result

    def op_diagnose(self, limit: int = 10) -> Dict[str, Any]:
        self._require_concept()
        premises    = [self._summary(k) for k in self._members("premises")]
        inputs      = [self._summary(k) for k in self._members("inputs")]
        views       = [self._summary(k) for k in self._members("views")]
        folds       = [self._summary(k) for k in self._members("folds")]
        conclusions = [self._summary(k) for k in self._members("conclusions")]
        disputes    = [self._summary(k) for k in self._members("disputes")]

        unresolved_folds = [f for f in folds if f["meta"].get("unresolved")]
        low_confidence_conclusions = [
            c for c in conclusions if float(c["meta"].get("confidence", 1.0)) < 0.4
        ]
        views_without_conclusions = [
            v for v in views
            if not any(c["meta"].get("view_id") == v["id"] for c in conclusions)
        ]
        inputs_without_view = [
            i for i in inputs
            if not any(i["id"] in v["meta"].get("input_ids", []) for v in views)
        ]
        composite_premises = [
            p for p in premises
            if p["meta"].get("conflict_policy") == "composite"
            or p["meta"].get("policy_steps")
        ]
        return {
            "curation_id": self.concept_id,
            "counts": {
                "premises":    len(premises),
                "inputs":      len(inputs),
                "views":       len(views),
                "folds":       len(folds),
                "conclusions": len(conclusions),
                "disputes":    len(disputes),
            },
            "diagnosis": {
                "unresolved_folds":            unresolved_folds[-limit:],
                "low_confidence_conclusions":  low_confidence_conclusions[-limit:],
                "views_without_conclusions":   views_without_conclusions[-limit:],
                "inputs_without_view":         inputs_without_view[-limit:],
                "composite_premises":          composite_premises[-limit:],
                "has_unresolved":              bool(unresolved_folds),
                "has_disputes":                bool(disputes),
            },
        }
