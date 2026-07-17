"""
Intelligence Concept Model.
Decision-cycle orchestration layer for Akasha Intelligence.
Intelligence does not replace Fact, Curation, Synthesis, or Presentation.
It coordinates them.
Pipeline:
    Requirement
        ↓
    Scan
        ↓
    Gap
        ↓
    Tasking
        ↓
    Assessment
        ↓
    Estimate
        ↓
    Option
        ↓
    Recommendation
Design principle:
    Intelligence is not a truth engine.
    It is an auditable reasoning and decision-support cycle.
Version: 1.0.0
"""
import time
import logging
from typing import Any, Dict, List, Optional
from lib.akasha.concepts.base import BaseConcept

logger = logging.getLogger("Harmonia.Concept.Intelligence")

CONTEXT_KEY_ACTIVE = "active_intelligence_root"
INDEX_SET = "set:intelligence:index"
_CONCEPT_WORD_ALIAS_PREFIX = "concept:word:"

SUBSET_TO_RELATION: Dict[str, str] = {
    "requirements":    "intel:has_requirement",
    "scans":           "intel:has_scan",
    "gaps":            "intel:has_gap",
    "taskings":        "intel:has_tasking",
    "assessments":     "intel:has_assessment",
    "estimates":       "intel:has_estimate",
    "options":         "intel:has_option",
    "recommendations": "intel:has_recommendation",
    "decisions":       "intel:has_decision",
    "disputes":        "intel:has_dispute",
}

REQUIREMENT_TYPES = (
    "research",
    "policy",
    "fieldwork",
    "osint",
    "historical",
    "strategic",
    "operational",
    "creative",
    "other",
)

PRIORITY_LEVELS = ("low", "medium", "high", "critical")

SCAN_TYPES = (
    "fact",
    "curation_view",
    "synthesis",
    "aggregation",
    "country",
    "geo",
    "map",
    "human",
    "source",
    "other",
)

GAP_TYPES = (
    "missing_source",
    "low_confidence",
    "contradiction",
    "outdated",
    "unresolved",
    "insufficient_coverage",
    "missing_fieldwork",
    "missing_analysis",
    "other",
)

TASKING_TYPES = (
    "collect",
    "verify",
    "interview",
    "survey",
    "field_observe",
    "analyze",
    "curate",
    "synthesize",
    "present",
    "other",
)

ASSESSMENT_TYPES = (
    "situation",
    "risk",
    "opportunity",
    "capability",
    "intent",
    "reliability",
    "control",
    "trend",
    "other",
)

ESTIMATE_TYPES = (
    "probability",
    "timeline",
    "impact",
    "scenario",
    "forecast",
    "range",
    "other",
)

OPTION_TYPES = (
    "research_action",
    "field_action",
    "policy_action",
    "presentation_action",
    "collection_plan",
    "analysis_plan",
    "other",
)

RECOMMENDATION_STATUS = (
    "draft",
    "reviewed",
    "issued",
)

DECISION_STATUS = (
    "accepted",
    "rejected",
    "deferred",
    "superseded",
    "unknown",
)


class IntelligenceConcept(BaseConcept):
    """Auditable intelligence cycle for requirements, gaps, assessments, options, and recommendations."""

    CONCEPT_PREFIX = "intelligence"
    CONTEXT_KEY_ACTIVE = CONTEXT_KEY_ACTIVE

    CONCEPT_METHODS = {
        "new": {"op": "op_new"},
        "open": {
            "op": "op_open",
            "coerce": lambda d: {
                "intelligence_id": d.get("intelligence_id")
                or d.get("intel_id")
                or d.get("id")
                or d.get("concept_id", "")
            },
        },
        "ls":       {"op": "op_list_all"},
        "map":      {"op": "op_map"},
        "rm":       {"op": "op_delete"},
        "req.add":       {"op": "op_add_requirement"},
        "scan.add":      {"op": "op_add_scan"},
        "gap.add":       {"op": "op_add_gap"},
        "task.add":      {"op": "op_add_tasking"},
        "assess.add":    {"op": "op_add_assessment"},
        "estimate.add":  {"op": "op_add_estimate"},
        "option.add":    {"op": "op_add_option"},
        "recommend.add": {"op": "op_add_recommendation"},
        "decision.add":  {"op": "op_add_decision"},
        "dispute.add":   {"op": "op_add_dispute"},
        "cycle":    {"op": "op_cycle"},
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

    def _intel_set(self, suffix: Optional[str] = None) -> str:
        base = f"set:intelligence:{self.concept_id}"
        return f"{base}:{suffix}" if suffix else base

    def _author_and_scopes(self):
        author_id = getattr(self.session, "client_id", "system")
        scopes = [f"owner:user_{author_id}", f"view:user_{author_id}"]
        return author_id, scopes

    def _create_sets(self) -> None:
        self.ensure_concept_set()
        self.cortex.create_set(self._intel_set())
        for suffix in self.SUBSETS:
            self.cortex.create_set(self._intel_set(suffix))
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
                "concept_model": "intelligence",
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
        self.cortex.add_to_set(self._intel_set(), key)
        if subset_suffix:
            self.cortex.add_to_set(self._intel_set(subset_suffix), key)
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
            key for key in self.cortex.get_collection_members(self._intel_set(suffix))
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
            "concept": "intelligence",
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
        relation = SUBSET_TO_RELATION.get(subset, f"intel:has_{subset}")
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

    def _require_requirement_if_given(self, requirement_id: str) -> None:
        if requirement_id:
            self._require_access(requirement_id, "Requirement")

    def _link_requirement(self, atom_id: str, requirement_id: str, author_id: str) -> None:
        if requirement_id:
            self.cortex.put_link(atom_id, requirement_id, "intel:answers_requirement", author=author_id)
            self.cortex.put_link(requirement_id, atom_id, "intel:has_work_product", author=author_id)

    # ------------------------------------------------------------------
    # Basic operators
    # ------------------------------------------------------------------

    def op_new(self, title: str, description: str = "") -> Dict[str, Any]:
        author_id, scopes = self._author_and_scopes()
        if not title:
            raise ValueError("intelligence.new requires title.")
        root_id = self.cortex.put_chunk(
            content=f"[ Intelligence: {title} ]",
            meta={
                "type": "concept",
                "concept": "intelligence",
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
        self.cortex.add_to_set(self._intel_set(), root_id)
        self.cortex.add_to_set(INDEX_SET, root_id)
        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, root_id)
        return {
            "status": "created",
            "concept_id": root_id,
            "intelligence_id": root_id,
            "intel_id": root_id,
            "title": title,
        }

    def op_open(self, intelligence_id: str) -> Dict[str, Any]:
        meta = self._meta(intelligence_id)
        if not meta or meta.get("concept") != "intelligence":
            raise RuntimeError(f"Atom '{intelligence_id[:12]}' is not an intelligence root.")
        if not self._visible(intelligence_id):
            raise RuntimeError(f"Intelligence not accessible: {intelligence_id[:12]}")
        self.concept_id = intelligence_id
        self.set_name = f"set:concept:{self.concept_id}"
        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, intelligence_id)
        return {
            "status": "opened",
            "concept_id": intelligence_id,
            "intelligence_id": intelligence_id,
            "intel_id": intelligence_id,
            "title": meta.get("title", ""),
        }

    def op_list_all(self) -> Dict[str, Any]:
        items = []
        for key in self.cortex.get_collection_members(INDEX_SET):
            if not self._visible(key):
                continue
            meta = self._meta(key)
            if meta.get("concept") != "intelligence":
                continue
            items.append({
                "intelligence_id": key,
                "concept_id": key,
                "title": meta.get("title", ""),
                "created_at": meta.get("created_at", 0),
            })
        items.sort(key=lambda x: x.get("created_at", 0), reverse=True)
        return {"intelligence_roots": items, "count": len(items)}

    def op_delete(self) -> Dict[str, Any]:
        self._require_concept()
        target = self.concept_id
        # Soft delete for auditability.
        self.cortex.remove_from_set(INDEX_SET, target)
        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, None)
        return {"status": "deleted", "intelligence_id": target, "soft_delete": True}

    # ------------------------------------------------------------------
    # Requirement / Scan / Gap / Tasking
    # ------------------------------------------------------------------

    def op_add_requirement(
        self,
        question: str,
        requirement_type: str = "research",
        priority: str = "medium",
        owner: str = "",
        due: str = "",
        scope: Optional[Dict[str, Any]] = None,
        success_criteria: Optional[List[str]] = None,
        note: str = "",
    ) -> Dict[str, Any]:
        """
        Requirement is the centre of the Intelligence cycle.

        Every downstream work product (Scan, Gap, Tasking, Assessment, Estimate,
        Option, Recommendation) should carry this requirement_id so that
        op_cycle can reconstruct the full picture.
        """
        self._require_concept()
        if not question:
            raise ValueError("requirement question is required.")
        if requirement_type not in REQUIREMENT_TYPES:
            raise ValueError(f"requirement_type must be one of {REQUIREMENT_TYPES}.")
        if priority not in PRIORITY_LEVELS:
            raise ValueError(f"priority must be one of {PRIORITY_LEVELS}.")
        key = self._put_atom(
            content=note or question,
            atom_type="intel_requirement",
            subset="requirements",
            meta_extra={
                "role": "requirement",
                "question": question,
                "requirement_type": requirement_type,
                "priority": priority,
                "owner": owner,
                "due": due,
                "scope": scope or {},
                "success_criteria": success_criteria or [],
                "status": "open",
            },
            concept_word="requirement",
        )
        return {"status": "requirement_added", "requirement_id": key, "priority": priority}

    def op_add_scan(
        self,
        requirement_id: str,
        target_id: str,
        scan_type: str = "other",
        signal: str = "",
        summary: str = "",
        confidence: float = 0.5,
        source_model: str = "",
        note: str = "",
    ) -> Dict[str, Any]:
        """
        Scan records a signal from an existing atom.

        Scan does not judge — it observes. Judgment belongs to Assessment.
        """
        self._require_concept()
        self._require_access(requirement_id, "Requirement")
        self._require_access(target_id, "Scan target")
        if scan_type not in SCAN_TYPES:
            raise ValueError(f"scan_type must be one of {SCAN_TYPES}.")
        author_id, _ = self._author_and_scopes()
        target_meta = self._meta(target_id)
        key = self._put_atom(
            content=note or summary or signal or f"scan:{target_id[:12]}",
            atom_type="intel_scan",
            subset="scans",
            meta_extra={
                "role": "scan",
                "requirement_id": requirement_id,
                "target_id": target_id,
                "scan_type": scan_type,
                "signal": signal,
                "summary": summary,
                "confidence": self._clamp01(confidence, 0.5),
                "source_model": source_model or target_meta.get("concept", ""),
            },
            concept_word="scan",
        )
        self._link_requirement(key, requirement_id, author_id)
        self.cortex.put_link(key, target_id, "intel:scans", author=author_id)
        return {"status": "scan_added", "scan_id": key, "target_id": target_id}

    def op_add_gap(
        self,
        requirement_id: str,
        description: str,
        gap_type: str = "missing_source",
        related_ids: Optional[List[str]] = None,
        severity: str = "medium",
        note: str = "",
    ) -> Dict[str, Any]:
        """
        Gap records what is missing.

        Unresolved or missing knowledge is itself intelligence — recording it
        drives Taskings and shapes the credibility of downstream Assessments.
        """
        self._require_concept()
        self._require_access(requirement_id, "Requirement")
        if gap_type not in GAP_TYPES:
            raise ValueError(f"gap_type must be one of {GAP_TYPES}.")
        if severity not in PRIORITY_LEVELS:
            raise ValueError(f"severity must be one of {PRIORITY_LEVELS}.")
        for rid in self._as_list(related_ids):
            self._require_access(rid, "Related atom")
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=note or description,
            atom_type="intel_gap",
            subset="gaps",
            meta_extra={
                "role": "gap",
                "requirement_id": requirement_id,
                "description": description,
                "gap_type": gap_type,
                "related_ids": related_ids or [],
                "severity": severity,
                "status": "open",
            },
            concept_word="gap",
        )
        self._link_requirement(key, requirement_id, author_id)
        for rid in self._as_list(related_ids):
            self.cortex.put_link(key, rid, "intel:gap_about", author=author_id)
        return {"status": "gap_added", "gap_id": key, "gap_type": gap_type}

    def op_add_tasking(
        self,
        requirement_id: str,
        description: str,
        tasking_type: str = "collect",
        gap_id: str = "",
        target_model: str = "",
        target_hint: str = "",
        priority: str = "medium",
        assigned_to: str = "",
        due: str = "",
        note: str = "",
    ) -> Dict[str, Any]:
        """
        Tasking records an instruction to collect, verify, analyze, or present.

        Tasking is instructional only — it does not directly write to Survey,
        Fact, or FieldNote. External execution may later fulfill the task.
        """
        self._require_concept()
        self._require_access(requirement_id, "Requirement")
        if gap_id:
            self._require_access(gap_id, "Gap")
        if tasking_type not in TASKING_TYPES:
            raise ValueError(f"tasking_type must be one of {TASKING_TYPES}.")
        if priority not in PRIORITY_LEVELS:
            raise ValueError(f"priority must be one of {PRIORITY_LEVELS}.")
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=note or description,
            atom_type="intel_tasking",
            subset="taskings",
            meta_extra={
                "role": "tasking",
                "requirement_id": requirement_id,
                "gap_id": gap_id or None,
                "description": description,
                "tasking_type": tasking_type,
                "target_model": target_model,
                "target_hint": target_hint,
                "priority": priority,
                "assigned_to": assigned_to,
                "due": due,
                "status": "open",
            },
            concept_word="tasking",
        )
        self._link_requirement(key, requirement_id, author_id)
        if gap_id:
            self.cortex.put_link(key, gap_id, "intel:addresses_gap", author=author_id)
        return {"status": "tasking_added", "tasking_id": key, "priority": priority}

    # ------------------------------------------------------------------
    # Assessment / Estimate / Option / Recommendation / Decision
    # ------------------------------------------------------------------

    def op_add_assessment(
        self,
        requirement_id: str,
        assessment_type: str,
        judgment: str,
        basis: Optional[List[str]] = None,
        confidence: float = 0.5,
        method: str = "human",
        caveats: Optional[List[str]] = None,
        note: str = "",
    ) -> Dict[str, Any]:
        """
        Assessment is where judgment happens.

        Basis should usually include Curation View, Fact, Synthesis Claim,
        or Scan atoms — all accessible within the Cortex.
        """
        self._require_concept()
        self._require_access(requirement_id, "Requirement")
        if assessment_type not in ASSESSMENT_TYPES:
            raise ValueError(f"assessment_type must be one of {ASSESSMENT_TYPES}.")
        if not judgment:
            raise ValueError("assessment judgment is required.")
        for bid in self._as_list(basis):
            self._require_access(bid, "Basis atom")
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=note or judgment,
            atom_type="intel_assessment",
            subset="assessments",
            meta_extra={
                "role": "assessment",
                "requirement_id": requirement_id,
                "assessment_type": assessment_type,
                "judgment": judgment,
                "basis": basis or [],
                "confidence": self._clamp01(confidence, 0.5),
                "method": method,
                "caveats": caveats or [],
            },
            concept_word="assessment",
        )
        self._link_requirement(key, requirement_id, author_id)
        for bid in self._as_list(basis):
            self.cortex.put_link(key, bid, "intel:based_on", author=author_id)
        return {
            "status": "assessment_added",
            "assessment_id": key,
            "confidence": self._clamp01(confidence, 0.5),
        }

    def op_add_estimate(
        self,
        requirement_id: str,
        estimate_type: str,
        statement: str,
        basis: Optional[List[str]] = None,
        probability: Optional[float] = None,
        range_low: Optional[float] = None,
        range_high: Optional[float] = None,
        horizon: str = "",
        confidence: float = 0.5,
        assumptions: Optional[List[str]] = None,
        note: str = "",
    ) -> Dict[str, Any]:
        self._require_concept()
        self._require_access(requirement_id, "Requirement")
        if estimate_type not in ESTIMATE_TYPES:
            raise ValueError(f"estimate_type must be one of {ESTIMATE_TYPES}.")
        if not statement:
            raise ValueError("estimate statement is required.")
        for bid in self._as_list(basis):
            self._require_access(bid, "Basis atom")
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=note or statement,
            atom_type="intel_estimate",
            subset="estimates",
            meta_extra={
                "role": "estimate",
                "requirement_id": requirement_id,
                "estimate_type": estimate_type,
                "statement": statement,
                "basis": basis or [],
                "probability": self._clamp01(probability, 0.5) if probability is not None else None,
                "range": {
                    "low": range_low,
                    "high": range_high,
                },
                "horizon": horizon,
                "confidence": self._clamp01(confidence, 0.5),
                "assumptions": assumptions or [],
            },
            concept_word="estimate",
        )
        self._link_requirement(key, requirement_id, author_id)
        for bid in self._as_list(basis):
            self.cortex.put_link(key, bid, "intel:based_on", author=author_id)
        return {"status": "estimate_added", "estimate_id": key}

    def op_add_option(
        self,
        requirement_id: str,
        title: str,
        option_type: str = "research_action",
        description: str = "",
        basis: Optional[List[str]] = None,
        benefits: Optional[List[str]] = None,
        risks: Optional[List[str]] = None,
        cost: str = "",
        feasibility: float = 0.5,
        expected_value: float = 0.5,
        note: str = "",
    ) -> Dict[str, Any]:
        self._require_concept()
        self._require_access(requirement_id, "Requirement")
        if option_type not in OPTION_TYPES:
            raise ValueError(f"option_type must be one of {OPTION_TYPES}.")
        if not title:
            raise ValueError("option title is required.")
        for bid in self._as_list(basis):
            self._require_access(bid, "Basis atom")
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=note or description or title,
            atom_type="intel_option",
            subset="options",
            meta_extra={
                "role": "option",
                "requirement_id": requirement_id,
                "title": title,
                "option_type": option_type,
                "description": description,
                "basis": basis or [],
                "benefits": benefits or [],
                "risks": risks or [],
                "cost": cost,
                "feasibility": self._clamp01(feasibility, 0.5),
                "expected_value": self._clamp01(expected_value, 0.5),
            },
            concept_word="option",
        )
        self._link_requirement(key, requirement_id, author_id)
        for bid in self._as_list(basis):
            self.cortex.put_link(key, bid, "intel:based_on", author=author_id)
        return {"status": "option_added", "option_id": key}

    def op_add_recommendation(
        self,
        requirement_id: str,
        statement: str,
        recommended_option_id: str = "",
        basis: Optional[List[str]] = None,
        confidence: float = 0.5,
        status: str = "draft",
        decision_status: str = "unknown",
        rationale: str = "",
        caveats: Optional[List[str]] = None,
        note: str = "",
    ) -> Dict[str, Any]:
        """
        Recommendation is issued by Intelligence; decision handling is tracked separately.

        status:         draft / reviewed / issued
        decision_status: accepted / rejected / deferred / superseded / unknown

        This preserves both what analysts recommended and what decision-makers
        did with it — they are separate, event-sourced records.
        """
        self._require_concept()
        self._require_access(requirement_id, "Requirement")
        if recommended_option_id:
            self._require_access(recommended_option_id, "Recommended option")
        if status not in RECOMMENDATION_STATUS:
            raise ValueError(f"status must be one of {RECOMMENDATION_STATUS}.")
        if decision_status not in DECISION_STATUS:
            raise ValueError(f"decision_status must be one of {DECISION_STATUS}.")
        if not statement:
            raise ValueError("recommendation statement is required.")
        for bid in self._as_list(basis):
            self._require_access(bid, "Basis atom")
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=note or statement,
            atom_type="intel_recommendation",
            subset="recommendations",
            meta_extra={
                "role": "recommendation",
                "requirement_id": requirement_id,
                "statement": statement,
                "recommended_option_id": recommended_option_id or None,
                "basis": basis or [],
                "confidence": self._clamp01(confidence, 0.5),
                "status": status,
                "decision_status": decision_status,
                "rationale": rationale,
                "caveats": caveats or [],
            },
            concept_word="recommendation",
        )
        self._link_requirement(key, requirement_id, author_id)
        if recommended_option_id:
            self.cortex.put_link(key, recommended_option_id, "intel:recommends_option", author=author_id)
        for bid in self._as_list(basis):
            self.cortex.put_link(key, bid, "intel:grounded_in", author=author_id)
        return {
            "status": "recommendation_added",
            "recommendation_id": key,
            "decision_status": decision_status,
        }

    def op_add_decision(
        self,
        recommendation_id: str,
        decision_status: str,
        decided_by: str = "",
        decided_at: str = "",
        reason: str = "",
        note: str = "",
    ) -> Dict[str, Any]:
        """
        Event-sourced decision record. Does not mutate the Recommendation atom.
        """
        self._require_concept()
        self._require_access(recommendation_id, "Recommendation")
        if decision_status not in DECISION_STATUS:
            raise ValueError(f"decision_status must be one of {DECISION_STATUS}.")
        author_id, _ = self._author_and_scopes()
        rec_meta = self._meta(recommendation_id)
        requirement_id = rec_meta.get("requirement_id", "")
        key = self._put_atom(
            content=note or reason or f"decision:{decision_status}",
            atom_type="intel_decision",
            subset="decisions",
            meta_extra={
                "role": "decision",
                "recommendation_id": recommendation_id,
                "requirement_id": requirement_id or None,
                "decision_status": decision_status,
                "decided_by": decided_by,
                "decided_at": decided_at,
                "reason": reason,
            },
            concept_word="decision",
        )
        self.cortex.put_link(recommendation_id, key, "intel:decided_by", author=author_id)
        if requirement_id:
            self._link_requirement(key, requirement_id, author_id)
        return {
            "status": "decision_added",
            "decision_id": key,
            "recommendation_id": recommendation_id,
            "decision_status": decision_status,
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
            atom_type="intel_dispute",
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
        self.cortex.put_link(target_id, key, "intel:disputed_by", author=author_id)
        if source_id:
            self.cortex.put_link(key, source_id, "intel:evidenced_by", author=author_id)
        return {"status": "dispute_added", "dispute_id": key, "target_id": target_id}

    # ------------------------------------------------------------------
    # Cycle / Trace / Diagnose
    # ------------------------------------------------------------------

    def op_cycle(self, requirement_id: str) -> Dict[str, Any]:
        """Return the full intelligence cycle view for a single Requirement."""
        self._require_concept()
        self._require_access(requirement_id, "Requirement")

        def linked(subset: str) -> List[Dict[str, Any]]:
            return [
                self._summary(k)
                for k in self._members(subset)
                if self._meta(k).get("requirement_id") == requirement_id
            ]

        return {
            "requirement":    self._summary(requirement_id),
            "scans":          linked("scans"),
            "gaps":           linked("gaps"),
            "taskings":       linked("taskings"),
            "assessments":    linked("assessments"),
            "estimates":      linked("estimates"),
            "options":        linked("options"),
            "recommendations": linked("recommendations"),
            "decisions":      linked("decisions"),
        }

    def op_trace(self, target_id: str) -> Dict[str, Any]:
        """
        Trace an Intelligence atom.

        For Recommendations: requirement, option, basis, decisions, disputes.
        For all atoms: requirement link and basis chain.
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
        requirement_id = meta.get("requirement_id", "")
        if requirement_id and self._visible(requirement_id):
            result["requirement"] = self._summary(requirement_id)
        basis = meta.get("basis", []) or meta.get("grounded_in", [])
        result["basis"] = [
            self._summary(bid) for bid in basis if self._visible(bid)
        ]
        if atom_type == "intel_recommendation":
            opt_id = meta.get("recommended_option_id")
            result["recommended_option"] = (
                self._summary(opt_id) if opt_id and self._visible(opt_id) else None
            )
            result["decisions"] = [
                self._summary(d)
                for d in self._members("decisions")
                if self._meta(d).get("recommendation_id") == target_id
            ]
        result["disputes"] = [
            self._summary(d)
            for d in self._members("disputes")
            if self._meta(d).get("target_id") == target_id
        ]
        return result

    def op_map(self) -> Dict[str, Any]:
        self._require_concept()
        meta = self._meta(self.concept_id)
        return {
            "intelligence_id": self.concept_id,
            "concept_id": self.concept_id,
            "title": meta.get("title", ""),
            **{suffix: self._members(suffix) for suffix in self.SUBSETS},
        }

    def op_diagnose(self, limit: int = 10) -> Dict[str, Any]:
        self._require_concept()
        requirements   = [self._summary(k) for k in self._members("requirements")]
        scans          = [self._summary(k) for k in self._members("scans")]
        gaps           = [self._summary(k) for k in self._members("gaps")]
        taskings       = [self._summary(k) for k in self._members("taskings")]
        assessments    = [self._summary(k) for k in self._members("assessments")]
        estimates      = [self._summary(k) for k in self._members("estimates")]
        options        = [self._summary(k) for k in self._members("options")]
        recommendations = [self._summary(k) for k in self._members("recommendations")]
        decisions      = [self._summary(k) for k in self._members("decisions")]
        disputes       = [self._summary(k) for k in self._members("disputes")]

        req_ids = {r["id"] for r in requirements}
        orphaned_work = []
        for collection in [scans, gaps, taskings, assessments, estimates, options, recommendations]:
            for item in collection:
                rid = item["meta"].get("requirement_id")
                if not rid or rid not in req_ids:
                    orphaned_work.append(item)

        open_gaps = [g for g in gaps if g["meta"].get("status", "open") == "open"]
        open_taskings = [t for t in taskings if t["meta"].get("status", "open") == "open"]
        low_confidence_assessments = [
            a for a in assessments if float(a["meta"].get("confidence", 1.0)) < 0.4
        ]
        recommendations_without_decision = [
            r for r in recommendations
            if not any(d["meta"].get("recommendation_id") == r["id"] for d in decisions)
            and r["meta"].get("decision_status", "unknown") == "unknown"
        ]
        issued_recommendations = [
            r for r in recommendations if r["meta"].get("status") == "issued"
        ]
        requirements_without_assessment = [
            r for r in requirements
            if not any(a["meta"].get("requirement_id") == r["id"] for a in assessments)
        ]
        return {
            "intelligence_id": self.concept_id,
            "counts": {
                "requirements":    len(requirements),
                "scans":           len(scans),
                "gaps":            len(gaps),
                "taskings":        len(taskings),
                "assessments":     len(assessments),
                "estimates":       len(estimates),
                "options":         len(options),
                "recommendations": len(recommendations),
                "decisions":       len(decisions),
                "disputes":        len(disputes),
            },
            "diagnosis": {
                "open_gaps":                       open_gaps[-limit:],
                "open_taskings":                   open_taskings[-limit:],
                "low_confidence_assessments":      low_confidence_assessments[-limit:],
                "recommendations_without_decision": recommendations_without_decision[-limit:],
                "requirements_without_assessment": requirements_without_assessment[-limit:],
                "orphaned_work_products":          orphaned_work[-limit:],
                "issued_recommendations":          issued_recommendations[-limit:],
                "has_open_gaps":                   bool(open_gaps),
                "has_open_taskings":               bool(open_taskings),
                "has_disputes":                    bool(disputes),
            },
        }
