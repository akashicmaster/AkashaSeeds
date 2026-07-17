"""
Human Concept Model.
Evidence-based actor/person model for field notes, journalism, history,
policy research, and future CastConcept-compatible analysis.

Core principle:
    Human is not a fictional character.
    Every meaningful attribute must be observable, evidenced, estimated,
    or explicitly disputed.

HumanConcept is designed to sit downstream of FactConcept:
    FieldNote / Source scraping -> Fact -> Human -> Synthesis / Presentation

Namespace contract:
    - Content atoms      -> set:human:{concept_id} and subset sets
    - Concept-word atoms -> set:concept:{concept_id}

Version: 1.0.0
"""
import time
import logging
from typing import Any, Dict, List, Optional

from lib.akasha.concepts.base import BaseConcept

logger = logging.getLogger("Akasha.Concept.Human")

CONTEXT_KEY_ACTIVE = "active_human_root"
INDEX_SET = "set:human:index"
_CONCEPT_WORD_ALIAS_PREFIX = "concept:word:"

SUBSET_TO_RELATION: Dict[str, str] = {
    "names":        "human:has_name",
    "life_events":  "human:has_life_event",
    "statuses":     "human:has_status",
    "pseudonyms":   "human:has_pseudonym",
    "assessments":  "human:has_assessment",
    "estimates":    "human:has_estimate",
    "merge_links":  "human:has_merge_link",
    "aliases":      "human:has_alias",
    "disputes":     "human:has_dispute",
    "fictional":    "human:has_fictional_projection",
    "bonds":        "human:has_bond",
    "bond_updates": "human:has_bond_update",
}

ASSESSMENT_TYPES = (
    "trait", "policy", "habit", "risk", "capacity", "role", "motivation", "reputation"
)
LIFE_EVENT_TYPES = ("birth", "death", "education", "career", "residence", "membership", "other")
STATUS_TYPES = ("alive", "deceased", "unknown", "active", "inactive", "missing", "disputed")
ENTITY_TYPES = ("human", "organization", "community", "geo", "cast", "world_place")


class HumanConcept(BaseConcept):
    """Evidence-based model for real or source-grounded human actors."""

    CONCEPT_PREFIX = "human"
    CONTEXT_KEY_ACTIVE = CONTEXT_KEY_ACTIVE

    CONCEPT_METHODS = {
        "new":  {"op": "op_new"},
        "open": {
            "op": "op_open",
            "coerce": lambda d: {
                "human_id": d.get("human_id") or d.get("id") or d.get("concept_id", "")
            },
        },
        "ls":       {"op": "op_list_all"},
        "map":      {"op": "op_map"},
        "rm":       {"op": "op_delete"},
        # Identity / life data
        "name.add":   {"op": "op_add_name"},
        "birth.set":  {"op": "op_set_birth"},
        "death.set":  {"op": "op_set_death"},
        "status.set": {"op": "op_set_status"},
        "pseudo.add": {"op": "op_add_pseudonym"},
        # Assessment / estimate
        "assess":   {"op": "op_add_assessment"},
        "estimate": {"op": "op_add_estimate"},
        # Entity resolution
        "merge.link":    {"op": "op_link_possible_merge"},
        "merge.confirm": {"op": "op_confirm_merge"},
        "alias":         {"op": "op_add_alias"},
        "dispute":       {"op": "op_add_dispute"},
        # Fictional projection
        "fictionalize": {"op": "op_fictionalize"},
        # Bonds
        "bond.add":    {"op": "op_add_bond"},
        "bond.update": {"op": "op_update_bond"},
        # Analysis
        "observable": {"op": "op_observable"},
        "timeline":   {"op": "op_timeline"},
        "profile":    {"op": "op_profile"},
        "diagnose":   {"op": "op_diagnose"},
        "trace":      {"op": "op_trace"},
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

    def _human_set(self, suffix: Optional[str] = None) -> str:
        base = f"set:human:{self.concept_id}"
        return f"{base}:{suffix}" if suffix else base

    def _author_and_scopes(self):
        author_id = getattr(self.session, "client_id", "system")
        scopes = [f"owner:user_{author_id}", f"view:user_{author_id}"]
        return author_id, scopes

    def _create_sets(self) -> None:
        self.ensure_concept_set()
        self.cortex.create_set(self._human_set())
        for suffix in self.SUBSETS:
            self.cortex.create_set(self._human_set(suffix))
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
                "type": "concept_word", "word": word,
                "concept_model": "human", "created_at": time.time(),
            },
            author=author_id, scopes=scopes,
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
        self.cortex.add_to_set(self._human_set(), key)
        if subset_suffix:
            self.cortex.add_to_set(self._human_set(subset_suffix), key)
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
            key for key in self.cortex.get_collection_members(self._human_set(suffix))
            if self._visible(key)
        ]

    def _meta(self, key: str) -> Dict[str, Any]:
        return self.cortex.get_meta(key) or {}

    def _content(self, key: str) -> str:
        return self.cortex.get_chunk(key) or ""

    def _summary(self, key: str) -> Dict[str, Any]:
        return {"id": key, "content": self._content(key), "meta": self._meta(key)}

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
        return value if isinstance(value, list) else [value]

    def _put_atom(
        self,
        content: str,
        atom_type: str,
        subset: str,
        meta_extra: Optional[Dict[str, Any]] = None,
        concept_word: Optional[str] = None,
    ) -> str:
        author_id, scopes = self._author_and_scopes()
        meta: Dict[str, Any] = {
            "type": atom_type, "concept": "human", "created_at": time.time(),
        }
        if meta_extra:
            meta.update(meta_extra)
        key = self.cortex.put_chunk(
            content=content, meta=meta, author=author_id, scopes=scopes,
        )
        self._register(key, subset_suffix=subset, concept_word=concept_word)
        relation = SUBSET_TO_RELATION.get(subset, f"human:has_{subset}")
        self.cortex.put_link(self.concept_id, key, relation, author=author_id)
        return key

    def _latest_by_subset(self, suffix: str) -> Optional[Dict[str, Any]]:
        members = self._members(suffix)
        if not members:
            return None
        return self._summary(members[-1])

    def _evidence_links(self, key: str, evidence: List[str], rel: str = "human:evidenced_by") -> None:
        author_id, _ = self._author_and_scopes()
        for ev in evidence:
            self._require_access(ev, "Evidence")
            self.cortex.put_link(key, ev, rel, author=author_id)

    # ------------------------------------------------------------------
    # Basic operators
    # ------------------------------------------------------------------

    def op_new(
        self,
        name: str,
        description: str = "",
        source_id: str = "",
        evidence: Optional[List[str]] = None,
        client_id: str = "",
    ) -> Dict[str, Any]:
        """
        Create a new Human record.
        client_id: if this Human represents a registered system client, pass the
                   client_id here. An alias 'human:identity:{client_id}' is set
                   in the local cortex for reverse lookup.
        """
        if not name:
            raise ValueError("human.new requires name.")
        author_id, scopes = self._author_and_scopes()
        if source_id:
            self._require_access(source_id, "Source")
        for ev in self._as_list(evidence):
            self._require_access(ev, "Evidence")
        root_id = self.cortex.put_chunk(
            content=f"[ Human: {name} ]",
            meta={
                "type": "concept", "concept": "human", "role": "root",
                "name": name, "description": description,
                "source_id": source_id or None,
                "evidence": evidence or [],
                "client_id": client_id or None,
                "created_at": time.time(),
            },
            author=author_id, scopes=scopes,
        )
        self.concept_id = root_id
        self.set_name = f"set:concept:{self.concept_id}"
        self._create_sets()
        # Root → content set only (Two-Namespace Rule)
        self.cortex.add_to_set(self._human_set(), root_id)
        self.cortex.add_to_set(INDEX_SET, root_id)
        if source_id:
            self.cortex.put_link(root_id, source_id, "human:identified_from", author=author_id)
        for ev in self._as_list(evidence):
            self.cortex.put_link(root_id, ev, "human:evidenced_by", author=author_id)
        if client_id:
            # Alias for reverse lookup: human:identity:{client_id} → human_id
            self.cortex.set_alias(root_id, f"human:identity:{client_id}")
        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, root_id)
        logger.info("[HumanConcept] Created '%s' (%s)", name, root_id[:8])
        return {
            "status": "created", "concept_id": root_id,
            "human_id": root_id, "name": name,
        }

    def op_open(self, human_id: str) -> Dict[str, Any]:
        meta = self._meta(human_id)
        if not meta or meta.get("concept") != "human":
            raise RuntimeError(f"Atom '{human_id[:12]}' is not a human root.")
        if not self._visible(human_id):
            raise RuntimeError(f"Human not accessible: {human_id[:12]}")
        self.concept_id = human_id
        self.set_name = f"set:concept:{self.concept_id}"
        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, human_id)
        return {
            "status": "opened", "concept_id": human_id,
            "human_id": human_id, "name": meta.get("name", ""),
        }

    def op_list_all(self) -> Dict[str, Any]:
        humans = []
        for key in self.cortex.get_collection_members(INDEX_SET):
            if not self._visible(key):
                continue
            meta = self._meta(key)
            if meta.get("concept") != "human":
                continue
            humans.append({
                "human_id": key, "concept_id": key,
                "name": meta.get("name", ""),
                "description": meta.get("description", ""),
                "created_at": meta.get("created_at", 0),
            })
        humans.sort(key=lambda x: x.get("created_at", 0), reverse=True)
        return {"humans": humans, "count": len(humans)}

    def op_delete(self) -> Dict[str, Any]:
        """Soft delete: remove from INDEX_SET and clear context. Atom retained in Cortex."""
        self._require_concept()
        target = self.concept_id
        self.cortex.remove_from_set(INDEX_SET, target)
        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, None)
        return {"status": "deleted", "human_id": target}

    # ------------------------------------------------------------------
    # Identity / life data
    # ------------------------------------------------------------------

    def op_add_name(
        self,
        name: str,
        name_type: str = "primary",
        language: str = "",
        source_id: str = "",
        evidence: Optional[List[str]] = None,
        confidence: float = 0.8,
    ) -> Dict[str, Any]:
        self._require_concept()
        if not name:
            raise ValueError("name is required.")
        evidence_list = self._as_list(evidence)
        if source_id:
            evidence_list.append(source_id)
        key = self._put_atom(
            content=name,
            atom_type="human_name",
            subset="names",
            meta_extra={
                "role": "name", "name": name, "name_type": name_type,
                "language": language, "source_id": source_id or None,
                "evidence": evidence or [],
                "confidence": self._clamp01(confidence, 0.8),
            },
            concept_word="name",
        )
        self._evidence_links(key, evidence_list)
        return {"status": "name_added", "name_id": key, "name": name}

    def _add_life_event(
        self,
        event_type: str,
        value: str,
        source_id: str = "",
        evidence: Optional[List[str]] = None,
        confidence: float = 0.8,
        note: str = "",
    ) -> Dict[str, Any]:
        if event_type not in LIFE_EVENT_TYPES:
            raise ValueError(f"event_type must be one of {LIFE_EVENT_TYPES}.")
        evidence_list = self._as_list(evidence)
        if source_id:
            evidence_list.append(source_id)
        key = self._put_atom(
            content=note or f"{event_type}:{value}",
            atom_type="human_life_event",
            subset="life_events",
            meta_extra={
                "role": "life_event", "event_type": event_type, "value": value,
                "source_id": source_id or None,
                "evidence": evidence or [],
                "confidence": self._clamp01(confidence, 0.8),
            },
            concept_word=event_type,
        )
        self._evidence_links(key, evidence_list)
        return {"status": f"{event_type}_set", "life_event_id": key, "value": value}

    def op_set_birth(
        self, date: str = "", place: str = "", source_id: str = "",
        evidence: Optional[List[str]] = None, confidence: float = 0.8,
    ) -> Dict[str, Any]:
        self._require_concept()
        return self._add_life_event(
            "birth", value=date or place, source_id=source_id,
            evidence=evidence, confidence=confidence,
            note=f"birth: date={date}, place={place}",
        )

    def op_set_death(
        self, date: str = "", place: str = "", source_id: str = "",
        evidence: Optional[List[str]] = None, confidence: float = 0.8,
    ) -> Dict[str, Any]:
        self._require_concept()
        return self._add_life_event(
            "death", value=date or place, source_id=source_id,
            evidence=evidence, confidence=confidence,
            note=f"death: date={date}, place={place}",
        )

    def op_set_status(
        self,
        status: str,
        source_id: str = "",
        evidence: Optional[List[str]] = None,
        confidence: float = 0.8,
        note: str = "",
    ) -> Dict[str, Any]:
        self._require_concept()
        if status not in STATUS_TYPES:
            raise ValueError(f"status must be one of {STATUS_TYPES}.")
        evidence_list = self._as_list(evidence)
        if source_id:
            evidence_list.append(source_id)
        key = self._put_atom(
            content=note or status,
            atom_type="human_status",
            subset="statuses",
            meta_extra={
                "role": "status", "status": status,
                "source_id": source_id or None,
                "evidence": evidence or [],
                "confidence": self._clamp01(confidence, 0.8),
            },
            concept_word="status",
        )
        self._evidence_links(key, evidence_list)
        return {"status": "status_set", "status_id": key, "value": status}

    def op_add_pseudonym(
        self,
        pseudonym: str,
        context: str = "",
        source_id: str = "",
        evidence: Optional[List[str]] = None,
        confidence: float = 0.7,
    ) -> Dict[str, Any]:
        self._require_concept()
        if not pseudonym:
            raise ValueError("pseudonym is required.")
        evidence_list = self._as_list(evidence)
        if source_id:
            evidence_list.append(source_id)
        key = self._put_atom(
            content=pseudonym,
            atom_type="human_pseudonym",
            subset="pseudonyms",
            meta_extra={
                "role": "pseudonym", "pseudonym": pseudonym, "context": context,
                "source_id": source_id or None,
                "evidence": evidence or [],
                "confidence": self._clamp01(confidence, 0.7),
            },
            concept_word="pseudonym",
        )
        self._evidence_links(key, evidence_list)
        return {"status": "pseudonym_added", "pseudonym_id": key}

    # ------------------------------------------------------------------
    # Assessment / estimate
    # ------------------------------------------------------------------

    def op_add_assessment(
        self,
        assessment_type: str,
        content: str,
        source_id: str = "",
        evidence: Optional[List[str]] = None,
        confidence: float = 0.6,
        method: str = "human",
        note: str = "",
    ) -> Dict[str, Any]:
        self._require_concept()
        if assessment_type not in ASSESSMENT_TYPES:
            raise ValueError(f"assessment_type must be one of {ASSESSMENT_TYPES}.")
        evidence_list = self._as_list(evidence)
        if source_id:
            evidence_list.append(source_id)
        if not evidence_list:
            raise ValueError("assessment requires source_id or evidence.")
        key = self._put_atom(
            content=note or content,
            atom_type="human_assessment",
            subset="assessments",
            meta_extra={
                "role": "assessment", "assessment_type": assessment_type,
                "content": content, "source_id": source_id or None,
                "evidence": evidence or [],
                "confidence": self._clamp01(confidence, 0.6), "method": method,
            },
            concept_word=assessment_type,
        )
        self._evidence_links(key, evidence_list)
        return {
            "status": "assessment_added", "assessment_id": key,
            "assessment_type": assessment_type,
            "confidence": self._clamp01(confidence, 0.6),
        }

    def op_add_estimate(
        self,
        estimate_type: str,
        value: Any,
        basis: Optional[List[str]] = None,
        confidence: float = 0.5,
        method: str = "human",
        note: str = "",
    ) -> Dict[str, Any]:
        self._require_concept()
        basis_list = self._as_list(basis)
        if not basis_list:
            raise ValueError("estimate requires basis evidence.")
        for ev in basis_list:
            self._require_access(ev, "Basis evidence")
        key = self._put_atom(
            content=note or f"{estimate_type}:{value}",
            atom_type="human_estimate",
            subset="estimates",
            meta_extra={
                "role": "estimate", "estimate_type": estimate_type, "value": value,
                "basis": basis_list,
                "confidence": self._clamp01(confidence, 0.5), "method": method,
            },
            concept_word="estimate",
        )
        self._evidence_links(key, basis_list, rel="human:estimated_from")
        return {
            "status": "estimate_added", "estimate_id": key,
            "estimate_type": estimate_type,
            "confidence": self._clamp01(confidence, 0.5),
        }

    # ------------------------------------------------------------------
    # Entity resolution
    # ------------------------------------------------------------------

    def op_link_possible_merge(
        self,
        other_human_id: str,
        reason: str = "",
        confidence: float = 0.5,
        evidence: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        self._require_concept()
        self._require_access(other_human_id, "Other human")
        for ev in self._as_list(evidence):
            self._require_access(ev, "Evidence")
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=reason or f"possible_merge:{other_human_id[:12]}",
            atom_type="human_merge_link",
            subset="merge_links",
            meta_extra={
                "role": "merge_link", "other_human_id": other_human_id,
                "reason": reason, "confidence": self._clamp01(confidence, 0.5),
                "confirmed": False, "evidence": evidence or [],
            },
            concept_word="merge_link",
        )
        self.cortex.put_link(self.concept_id, other_human_id, "human:possibly_same_as", author=author_id)
        self._evidence_links(key, self._as_list(evidence))
        return {"status": "merge_linked", "merge_link_id": key}

    def op_confirm_merge(
        self,
        merge_link_id: str,
        note: str = "",
    ) -> Dict[str, Any]:
        self._require_concept()
        self._require_access(merge_link_id, "Merge link")
        old = self._meta(merge_link_id)
        other = old.get("other_human_id", "")
        if other:
            self._require_access(other, "Other human")
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=note or f"confirmed_merge:{other[:12]}",
            atom_type="human_merge_link",
            subset="merge_links",
            meta_extra={
                "role": "merge_confirmation", "merge_link_id": merge_link_id,
                "other_human_id": other, "confirmed": True,
            },
            concept_word="merge_confirmation",
        )
        if other:
            self.cortex.put_link(self.concept_id, other, "human:same_as", author=author_id)
        self.cortex.put_link(merge_link_id, key, "human:confirmed_by", author=author_id)
        return {"status": "merge_confirmed", "confirmation_id": key}

    def op_add_alias(
        self,
        alias: str,
        target_id: str = "",
        source_id: str = "",
        evidence: Optional[List[str]] = None,
        confidence: float = 0.7,
    ) -> Dict[str, Any]:
        self._require_concept()
        if target_id:
            self._require_access(target_id, "Alias target")
        evidence_list = self._as_list(evidence)
        if source_id:
            evidence_list.append(source_id)
        key = self._put_atom(
            content=alias,
            atom_type="human_alias",
            subset="aliases",
            meta_extra={
                "role": "alias", "alias": alias,
                "target_id": target_id or self.concept_id,
                "source_id": source_id or None,
                "evidence": evidence or [],
                "confidence": self._clamp01(confidence, 0.7),
            },
            concept_word="alias",
        )
        self._evidence_links(key, evidence_list)
        return {"status": "alias_added", "alias_id": key}

    def op_add_dispute(
        self,
        target_id: str,
        reason: str,
        evidence: Optional[List[str]] = None,
        severity: float = 0.5,
    ) -> Dict[str, Any]:
        self._require_concept()
        self._require_access(target_id, "Disputed target")
        for ev in self._as_list(evidence):
            self._require_access(ev, "Evidence")
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=reason,
            atom_type="human_dispute",
            subset="disputes",
            meta_extra={
                "role": "dispute", "target_id": target_id, "reason": reason,
                "evidence": evidence or [],
                "severity": self._clamp01(severity, 0.5),
            },
            concept_word="dispute",
        )
        self.cortex.put_link(key, target_id, "human:disputes", author=author_id)
        self._evidence_links(key, self._as_list(evidence))
        return {"status": "dispute_added", "dispute_id": key}

    # ------------------------------------------------------------------
    # Fictional projection
    # ------------------------------------------------------------------

    def op_fictionalize(
        self,
        cast_id: str = "",
        transformation: str = "",
        preserve: Optional[List[str]] = None,
        note: str = "",
    ) -> Dict[str, Any]:
        """
        Link this Human to a fictional Cast projection.
        Does not create CastConcept; only records the projection metadata.
        """
        self._require_concept()
        if cast_id:
            self._require_access(cast_id, "Cast projection")
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=note or transformation or "fictional_projection",
            atom_type="human_fictional_projection",
            subset="fictional",
            meta_extra={
                "role": "fictional_projection",
                "cast_id": cast_id or None,
                "transformation": transformation,
                "preserve": preserve or [],
            },
            concept_word="fictional_projection",
        )
        if cast_id:
            self.cortex.put_link(self.concept_id, cast_id, "human:fictionalized_as", author=author_id)
        return {"status": "fictional_projection_added", "projection_id": key}

    # ------------------------------------------------------------------
    # Bonds
    # ------------------------------------------------------------------

    def op_add_bond(
        self,
        target_id: str,
        target_type: str = "human",
        relation: str = "associated_with",
        direction: str = "directed",
        strength: float = 0.5,
        visibility: str = "unknown",
        evidence: Optional[List[str]] = None,
        history: Optional[List[str]] = None,
        note: str = "",
    ) -> Dict[str, Any]:
        self._require_concept()
        self._require_access(target_id, "Bond target")
        if target_type not in ENTITY_TYPES:
            raise ValueError(f"target_type must be one of {ENTITY_TYPES}.")
        evidence_list = self._as_list(evidence)
        history_list = self._as_list(history)
        if not evidence_list and not history_list:
            raise ValueError("bond requires evidence or history.")
        for ev in evidence_list + history_list:
            self._require_access(ev, "Bond evidence")
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=note or f"bond:{relation}->{target_id[:12]}",
            atom_type="human_bond",
            subset="bonds",
            meta_extra={
                "role": "bond", "target_id": target_id, "target_type": target_type,
                "relation": relation, "direction": direction,
                "strength": self._clamp01(strength, 0.5),
                "visibility": visibility,
                "evidence": evidence or [], "history": history or [],
            },
            concept_word="bond",
        )
        self.cortex.put_link(self.concept_id, target_id, f"human:{relation}", author=author_id)
        self.cortex.put_link(key, target_id, "human:refers_to", author=author_id)
        self._evidence_links(key, evidence_list + history_list)
        return {"status": "bond_added", "bond_id": key}

    def op_update_bond(
        self,
        bond_id: str,
        delta: Dict[str, Any],
        event_id: str = "",
        evidence: Optional[List[str]] = None,
        note: str = "",
    ) -> Dict[str, Any]:
        self._require_concept()
        self._require_access(bond_id, "Bond")
        evidence_list = self._as_list(evidence)
        if event_id:
            evidence_list.append(event_id)
        if not evidence_list:
            raise ValueError("bond.update requires event_id or evidence.")
        for ev in evidence_list:
            self._require_access(ev, "Bond update evidence")
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=note or f"bond_update:{delta}",
            atom_type="human_bond_update",
            subset="bond_updates",
            meta_extra={
                "role": "bond_update", "bond_id": bond_id,
                "event_id": event_id or None,
                "evidence": evidence or [], "delta": delta,
            },
            concept_word="bond_update",
        )
        self.cortex.put_link(bond_id, key, "human:updated_by", author=author_id)
        self._evidence_links(key, evidence_list)
        return {"status": "bond_updated", "bond_update_id": key}

    # ------------------------------------------------------------------
    # Read / analysis operators
    # ------------------------------------------------------------------

    def op_observable(self, include_claims: bool = True) -> Dict[str, Any]:
        """
        Return externally evidenced observable facts linked to this Human.
        Scans incoming links from FactConcept atoms (fact:evidenced_by, fact:involves_human)
        and outgoing links with fact: or human: prefixed relations.
        """
        self._require_concept()
        observable = []
        incoming = self.cortex.get_incoming_links(self.concept_id) or []
        outgoing = self.cortex.get_adjacent_links(self.concept_id) or []
        candidates = set()
        for src, rel in incoming:
            if rel in ("fact:evidenced_by", "fact:involves_human", "human:evidenced_by"):
                candidates.add(src)
        for dst, rel in outgoing:
            if rel.startswith("fact:") or rel.startswith("human:"):
                if self._visible(dst):
                    candidates.add(dst)
        for key in candidates:
            if not self._visible(key):
                continue
            meta = self._meta(key)
            if not include_claims and meta.get("fact_type") == "claim":
                continue
            observable.append(self._summary(key))
        observable.sort(
            key=lambda x: x["meta"].get("event_time", "") or str(x["meta"].get("created_at", ""))
        )
        return {"human_id": self.concept_id, "observable": observable, "count": len(observable)}

    def op_timeline(self, include_internal: bool = True) -> Dict[str, Any]:
        self._require_concept()
        items = []
        for suffix in ("life_events", "statuses", "bonds", "bond_updates"):
            for key in self._members(suffix):
                s = self._summary(key)
                meta = s["meta"]
                items.append({
                    "id": key, "kind": suffix,
                    "time": meta.get("event_time") or meta.get("value") or meta.get("created_at"),
                    "content": s["content"], "meta": meta,
                })
        if include_internal:
            for s in self.op_observable().get("observable", []):
                meta = s["meta"]
                items.append({
                    "id": s["id"], "kind": "observable_fact",
                    "time": meta.get("event_time") or meta.get("created_at"),
                    "content": s["content"], "meta": meta,
                })
        items.sort(key=lambda x: str(x.get("time", "")))
        return {"human_id": self.concept_id, "timeline": items, "count": len(items)}

    def op_profile(self) -> Dict[str, Any]:
        self._require_concept()
        root_meta = self._meta(self.concept_id)
        return {
            "human_id": self.concept_id,
            "name": root_meta.get("name", ""),
            "description": root_meta.get("description", ""),
            "names":       [self._summary(k) for k in self._members("names")],
            "life_events": [self._summary(k) for k in self._members("life_events")],
            "status":      self._latest_by_subset("statuses"),
            "pseudonyms":  [self._summary(k) for k in self._members("pseudonyms")],
            "assessments": [self._summary(k) for k in self._members("assessments")],
            "estimates":   [self._summary(k) for k in self._members("estimates")],
            "bonds":       [self._summary(k) for k in self._members("bonds")],
            "disputes":    [self._summary(k) for k in self._members("disputes")],
        }

    def op_map(self) -> Dict[str, Any]:
        self._require_concept()
        meta = self._meta(self.concept_id)
        return {
            "human_id": self.concept_id, "concept_id": self.concept_id,
            "name": meta.get("name", ""),
            **{suffix: self._members(suffix) for suffix in self.SUBSETS},
        }

    def op_diagnose(self, limit: int = 10) -> Dict[str, Any]:
        self._require_concept()
        assessments  = [self._summary(k) for k in self._members("assessments")]
        estimates    = [self._summary(k) for k in self._members("estimates")]
        disputes     = [self._summary(k) for k in self._members("disputes")]
        bonds        = [self._summary(k) for k in self._members("bonds")]
        merge_links  = [self._summary(k) for k in self._members("merge_links")]
        observable   = self.op_observable().get("observable", [])

        low_confidence_assessments = [
            a for a in assessments if float(a["meta"].get("confidence", 1.0)) < 0.4
        ]
        low_confidence_estimates = [
            e for e in estimates if float(e["meta"].get("confidence", 1.0)) < 0.4
        ]
        unevidenced_bonds = [
            b for b in bonds
            if not b["meta"].get("evidence") and not b["meta"].get("history")
        ]
        possible_duplicates = [
            m for m in merge_links if not m["meta"].get("confirmed")
        ]
        return {
            "human_id": self.concept_id,
            "counts": {
                "observable": len(observable), "assessments": len(assessments),
                "estimates": len(estimates), "bonds": len(bonds),
                "disputes": len(disputes), "possible_duplicates": len(possible_duplicates),
            },
            "diagnosis": {
                "low_confidence_assessments": low_confidence_assessments[-limit:],
                "low_confidence_estimates":   low_confidence_estimates[-limit:],
                "unevidenced_bonds":          unevidenced_bonds[-limit:],
                "disputes":                   disputes[-limit:],
                "possible_duplicates":        possible_duplicates[-limit:],
                "has_observable_facts":       bool(observable),
            },
        }

    def op_trace(self, target_id: str = "") -> Dict[str, Any]:
        """Trace evidence chain for a Human atom or the Human root."""
        self._require_concept()
        target = target_id or self.concept_id
        self._require_access(target, "Trace target")
        meta = self._meta(target)

        evidence_ids = []
        if meta.get("source_id"):
            evidence_ids.append(meta["source_id"])
        evidence_ids.extend(self._as_list(meta.get("evidence")))
        evidence_ids.extend(self._as_list(meta.get("basis")))
        evidence_ids.extend(self._as_list(meta.get("history")))

        for dst, rel in (self.cortex.get_adjacent_links(target) or []):
            if rel in ("human:evidenced_by", "human:estimated_from", "human:identified_from"):
                evidence_ids.append(dst)

        seen: set = set()
        linked_evidence = []
        for ev in evidence_ids:
            if ev in seen or not self._visible(ev):
                continue
            seen.add(ev)
            linked_evidence.append(self._summary(ev))

        return {
            "human_id": self.concept_id,
            "target": self._summary(target),
            "evidence": linked_evidence,
            "count": len(linked_evidence),
        }
