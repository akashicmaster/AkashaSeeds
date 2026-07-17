"""
Fact Concept Model.
A model for recording, classifying, and tracing facts extracted from sources.

Core distinction:
    Direct Fact:   Verified by a single Source alone.
                   credibility = Quelle.credibility (via _effective_source_credibility)

    Inferred Fact: Derived from multiple Sources via Curation.
                   credibility = extraction_algo.confidence
                               × inference_algo.confidence
                               × Σ(source_i.credibility_effective × weight_i / total_weight)

Namespace contract:
    - Content atoms      -> set:fact:{concept_id} and subset sets
    - Concept-word atoms -> set:concept:{concept_id}

Version: 1.0.1 (ChatGPT review / bug fixes applied)
Fixes:
    - Fix 1: _effective_source_credibility helper added;
             op_add_fact/claim/absence/trace now use latest source_eval credibility
    - Fix 2: weight normalisation in op_add_inferred (prevents credibility > 1.0)
    - Fix 3: source_evals is now a separate subset (not mixed with sources)
    - Fix 4: op_add_inferred reads credibility internally; caller passes only
             {source_id, weight, role} — no caller-supplied credibility
    - Fix 5: Fact status field added (active/disputed/retracted/superseded/unverified)
    - Fix 6: double author_id variable in op_link_entity removed
Reserved relations for v1.1:
    fact:disputed_by / fact:superseded_by / fact:contradicts
"""
import logging
import time
from typing import Any, Dict, List, Optional

from lib.akasha.concepts.base import BaseConcept
from lib.akasha.concepts.mixins.provenance import ProvenanceMixin

logger = logging.getLogger("Akasha.Concept.Fact")

CONTEXT_KEY_ACTIVE = "active_fact_root"
INDEX_SET = "set:fact:index"
_CONCEPT_WORD_ALIAS_PREFIX = "concept:word:"

SUBSET_TO_RELATION: Dict[str, str] = {
    "sources":      "fact:has_source",
    "source_evals": "fact:has_source_eval",   # Fix 3: separate from sources
    "facts":        "fact:has_fact",
    "fact_sets":    "fact:has_fact_set",
    "entities":     "fact:has_entity",
    "provenances":  "fact:has_provenance",
}

FACT_TYPES    = ("event", "state", "claim", "relation", "absence")
FACT_STATUSES = ("active", "disputed", "retracted", "superseded", "unverified")
ORIGIN_TYPES  = ("direct", "inferred")
ENTITY_TYPES  = ("human", "organization", "community", "geo")
SOURCE_KINDS  = (
    "news_article", "official_doc", "testimony", "sensor",
    "social_media", "academic_paper", "legal_doc", "financial_report",
    "other",
)
ALGO_METHODS  = ("human", "llm", "rule_based", "statistical", "pattern_matching", "hybrid")

# Reserved relations for v1.1 (dispute / supersede workflow)
# fact:disputed_by   — this fact is disputed by another fact
# fact:superseded_by — this fact has been replaced by a newer fact
# fact:contradicts   — two facts that contradict each other


class FactConcept(BaseConcept, ProvenanceMixin):
    """Fact recording, classification, and provenance tracking."""

    CONCEPT_PREFIX = "fact"
    CONTEXT_KEY_ACTIVE = CONTEXT_KEY_ACTIVE

    CONCEPT_METHODS = {
        "new":  {"op": "op_new"},
        "open": {
            "op": "op_open",
            "coerce": lambda d: {
                "fact_root_id": (
                    d.get("fact_root_id") or d.get("id") or d.get("concept_id", "")
                )
            },
        },
        "ls":           {"op": "op_list_all"},
        "map":          {"op": "op_map"},
        "rm":           {"op": "op_delete"},
        # Source management
        "source.add":   {"op": "op_add_source"},
        "source.eval":  {"op": "op_eval_source"},
        # Direct Facts
        "add":          {"op": "op_add_fact"},
        "claim":        {"op": "op_add_claim"},
        "absent":       {"op": "op_add_absence"},
        # Inferred Facts
        "infer":        {"op": "op_add_inferred"},
        # FactSet
        "set.new":      {"op": "op_new_factset"},
        "set.add":      {"op": "op_add_to_factset"},
        # Entity linking
        "entity.link":  {"op": "op_link_entity"},
        # Analysis
        "diagnose":     {"op": "op_diagnose"},
        "trace":        {"op": "op_trace"},
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

    def _fact_set(self, suffix: Optional[str] = None) -> str:
        base = f"set:fact:{self.concept_id}"
        return f"{base}:{suffix}" if suffix else base

    def _author_and_scopes(self):
        author_id = getattr(self.session, "client_id", "system")
        return author_id, [f"owner:user_{author_id}", f"view:user_{author_id}"]

    def _create_sets(self) -> None:
        self.ensure_concept_set()
        self.cortex.create_set(self._fact_set())
        for suffix in self.SUBSETS:
            self.cortex.create_set(self._fact_set(suffix))
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
                "concept_model": "fact", "created_at": time.time(),
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
        self.cortex.add_to_set(self._fact_set(), key)
        if subset_suffix:
            self.cortex.add_to_set(self._fact_set(subset_suffix), key)
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
            k for k in self.cortex.get_collection_members(self._fact_set(suffix))
            if self._visible(k)
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
        meta: Dict[str, Any] = {
            "type": atom_type, "concept": "fact", "created_at": time.time(),
        }
        if meta_extra:
            meta.update(meta_extra)
        key = self.cortex.put_chunk(
            content=content, meta=meta, author=author_id, scopes=scopes,
        )
        self._register(key, subset_suffix=subset, concept_word=concept_word)
        relation = SUBSET_TO_RELATION.get(subset, f"fact:has_{subset}")
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
        return value if isinstance(value, list) else [value]

    # ------------------------------------------------------------------
    # Basic operators
    # ------------------------------------------------------------------

    def op_new(self, title: str, description: str = "") -> Dict[str, Any]:
        if not title:
            raise ValueError("fact.new requires title.")
        author_id, scopes = self._author_and_scopes()
        root_id = self.cortex.put_chunk(
            content=f"[ Fact: {title} ]",
            meta={
                "type": "concept", "concept": "fact", "role": "root",
                "title": title, "description": description,
                "created_at": time.time(),
            },
            author=author_id, scopes=scopes,
        )
        self.concept_id = root_id
        self.set_name = f"set:concept:{self.concept_id}"
        self._create_sets()
        # Root → content set only (Two-Namespace Rule)
        self.cortex.add_to_set(self._fact_set(), root_id)
        self.cortex.add_to_set(INDEX_SET, root_id)
        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, root_id)
        logger.info("[FactConcept] Created '%s' (%s)", title, root_id[:8])
        return {
            "status": "created", "concept_id": root_id,
            "fact_root_id": root_id, "title": title,
        }

    def op_open(self, fact_root_id: str) -> Dict[str, Any]:
        meta = self._meta(fact_root_id)
        if not meta or meta.get("concept") != "fact":
            raise RuntimeError(f"Atom '{fact_root_id[:12]}' is not a fact root.")
        if not self._visible(fact_root_id):
            raise RuntimeError(f"Fact not accessible: {fact_root_id[:12]}")
        self.concept_id = fact_root_id
        self.set_name = f"set:concept:{self.concept_id}"
        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, fact_root_id)
        return {
            "status": "opened", "concept_id": fact_root_id,
            "fact_root_id": fact_root_id, "title": meta.get("title", ""),
        }

    def op_list_all(self) -> Dict[str, Any]:
        facts = []
        for key in self.cortex.get_collection_members(INDEX_SET):
            if not self._visible(key):
                continue
            meta = self._meta(key)
            if meta.get("concept") != "fact":
                continue
            facts.append({
                "fact_root_id": key, "concept_id": key,
                "title": meta.get("title", ""),
                "created_at": meta.get("created_at", 0),
            })
        facts.sort(key=lambda x: x.get("created_at", 0), reverse=True)
        return {"facts": facts, "count": len(facts)}

    def op_delete(self) -> Dict[str, Any]:
        """Soft delete: remove from INDEX_SET and clear context. Atom is retained in Cortex."""
        self._require_concept()
        target = self.concept_id
        self.cortex.remove_from_set(INDEX_SET, target)
        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, None)
        return {"status": "deleted", "fact_root_id": target}

    # ------------------------------------------------------------------
    # Source management
    # ------------------------------------------------------------------

    def op_add_source(
        self,
        url: str = "",
        kind: str = "news_article",
        title: str = "",
        author: str = "",
        publisher: str = "",
        language: str = "",
        published: str = "",
        retrieved: str = "",
        quelle_level: int = 2,
        independence: float = 0.5,
        credibility: float = 0.5,
        bias: str = "unknown",
        motivation: str = "",
        note: str = "",
    ) -> Dict[str, Any]:
        """
        Add a Source atom — the evidentiary anchor for Direct Facts.

        quelle_level: 1=primary (first-hand), 2=secondary, 3+=tertiary
        independence: 0.0=entirely dependent, 1.0=fully independent
        credibility:  initial value. Use fact.source.eval to update.
                      _effective_source_credibility() always reads the latest.
        """
        self._require_concept()
        if kind not in SOURCE_KINDS:
            raise ValueError(f"kind must be one of {SOURCE_KINDS}.")
        if not (1 <= quelle_level <= 5):
            raise ValueError("quelle_level must be between 1 and 5.")
        key = self._put_atom(
            content=note or title or url,
            atom_type="fact_source",
            subset="sources",
            meta_extra={
                "role": "source",
                "url": url, "kind": kind, "title": title,
                "author": author, "publisher": publisher,
                "language": language, "published": published, "retrieved": retrieved,
                "quelle_level": quelle_level,
                "independence": self._clamp01(independence, 0.5),
                "credibility": self._clamp01(credibility, 0.5),
                "bias": bias, "motivation": motivation,
            },
            concept_word="source",
        )
        return {
            "status": "source_added", "source_id": key,
            "kind": kind, "credibility": self._clamp01(credibility, 0.5),
        }

    def op_eval_source(
        self,
        source_id: str,
        credibility: Optional[float] = None,
        independence: Optional[float] = None,
        quelle_level: Optional[int] = None,
        bias: str = "",
        note: str = "",
    ) -> Dict[str, Any]:
        """
        Record an updated credibility evaluation for a Source.

        Fix 1 + Fix 3: Event-sourced into source_evals subset. Original Source
        atom is never mutated. _effective_source_credibility() reads this eval.
        """
        self._require_concept()
        self._require_access(source_id, "Source")
        author_id, _ = self._author_and_scopes()
        src_meta = self._meta(source_id)
        updates: Dict[str, Any] = {}
        if credibility is not None:
            updates["credibility"] = self._clamp01(credibility)
        if independence is not None:
            updates["independence"] = self._clamp01(independence)
        if quelle_level is not None:
            if not (1 <= quelle_level <= 5):
                raise ValueError("quelle_level must be between 1 and 5.")
            updates["quelle_level"] = quelle_level
        if bias:
            updates["bias"] = bias
        key = self._put_atom(
            content=note or f"eval:{source_id[:12]}",
            atom_type="fact_source_eval",
            subset="source_evals",
            meta_extra={
                "role": "source_eval", "source_id": source_id,
                "previous": {
                    "credibility":  src_meta.get("credibility"),
                    "independence": src_meta.get("independence"),
                    "quelle_level": src_meta.get("quelle_level"),
                },
                "updates": updates,
            },
            concept_word="source_eval",
        )
        self.cortex.put_link(source_id, key, "fact:evaluated_by", author=author_id)
        return {"status": "source_evaluated", "eval_id": key, "updates": updates}

    # ------------------------------------------------------------------
    # Direct Facts
    # ------------------------------------------------------------------

    def op_add_fact(
        self,
        fact_type: str,
        content: str,
        source_id: str,
        event_time: str = "",
        event_time_precision: str = "date",
        place: Optional[Dict[str, Any]] = None,
        entities: Optional[List[Dict[str, Any]]] = None,
        visibility: str = "public",
        polarity: Optional[Dict[str, Any]] = None,
        corroboration: Optional[List[str]] = None,
        status: str = "active",
        note: str = "",
    ) -> Dict[str, Any]:
        """
        Add a Direct Fact — verified by a single Source alone.

        Fix 1: credibility from _effective_source_credibility() (latest eval applied).
        Fix 5: status field (active/disputed/retracted/superseded/unverified).
        """
        self._require_concept()
        if fact_type not in FACT_TYPES:
            raise ValueError(f"fact_type must be one of {FACT_TYPES}.")
        if status not in FACT_STATUSES:
            raise ValueError(f"status must be one of {FACT_STATUSES}.")
        self._require_access(source_id, "Source")
        for corr_id in self._as_list(corroboration):
            self._require_access(corr_id, "Corroboration source")
        author_id, _ = self._author_and_scopes()
        credibility = self._effective_source_credibility(source_id)

        key = self._put_atom(
            content=content,
            atom_type="fact_direct",
            subset="facts",
            meta_extra={
                "role": "fact", "origin": "direct", "fact_type": fact_type,
                "status": status, "source_id": source_id,
                "corroboration": corroboration or [],
                "credibility": credibility,
                "event_time": event_time, "event_time_precision": event_time_precision,
                "place": place or {}, "entities": entities or [],
                "visibility": visibility, "polarity": polarity or {},
                "note": note,
            },
            concept_word=fact_type,
        )
        self.cortex.put_link(key, source_id, "fact:derived_from_source", author=author_id)
        for corr_id in self._as_list(corroboration):
            self.cortex.put_link(key, corr_id, "fact:corroborated_by", author=author_id)
        return {
            "status": "fact_added", "fact_id": key,
            "fact_type": fact_type, "origin": "direct",
            "fact_status": status, "credibility": credibility,
        }

    def op_add_claim(
        self,
        speaker: str,
        content: str,
        source_id: str,
        context: str = "",
        medium: str = "",
        event_time: str = "",
        entities: Optional[List[Dict[str, Any]]] = None,
        status: str = "active",
        note: str = "",
    ) -> Dict[str, Any]:
        """
        Add a Claim Fact — records what someone said, not whether it is true.

        The fact is: 'speaker said X in this source'. Content truth is not asserted.
        Fix 1 + Fix 5 applied.
        """
        self._require_concept()
        self._require_access(source_id, "Source")
        if status not in FACT_STATUSES:
            raise ValueError(f"status must be one of {FACT_STATUSES}.")
        author_id, _ = self._author_and_scopes()
        credibility = self._effective_source_credibility(source_id)

        label = note or f'[Claim] {speaker}: "{content[:60]}"'
        key = self._put_atom(
            content=label,
            atom_type="fact_direct",
            subset="facts",
            meta_extra={
                "role": "fact", "origin": "direct", "fact_type": "claim",
                "status": status, "source_id": source_id,
                "speaker": speaker, "claim": content,
                "context": context, "medium": medium, "event_time": event_time,
                "entities": entities or [], "credibility": credibility,
            },
            concept_word="claim",
        )
        self.cortex.put_link(key, source_id, "fact:derived_from_source", author=author_id)
        return {
            "status": "claim_added", "fact_id": key,
            "fact_type": "claim", "origin": "direct",
            "fact_status": status, "credibility": credibility, "speaker": speaker,
        }

    def op_add_absence(
        self,
        description: str,
        source_id: str,
        expected: str = "",
        gap_type: str = "no_statement",
        entities: Optional[List[Dict[str, Any]]] = None,
        status: str = "active",
        note: str = "",
    ) -> Dict[str, Any]:
        """
        Add an Absence Fact — records that something expected is missing.
        Corresponds to Intelligence.Gap.

        gap_type: no_statement / no_document / no_action / no_record
        Fix 1 + Fix 5 applied.
        """
        self._require_concept()
        self._require_access(source_id, "Source")
        if status not in FACT_STATUSES:
            raise ValueError(f"status must be one of {FACT_STATUSES}.")
        author_id, _ = self._author_and_scopes()
        credibility = self._effective_source_credibility(source_id)

        key = self._put_atom(
            content=description,
            atom_type="fact_direct",
            subset="facts",
            meta_extra={
                "role": "fact", "origin": "direct", "fact_type": "absence",
                "status": status, "source_id": source_id,
                "description": description, "expected": expected,
                "gap_type": gap_type, "entities": entities or [],
                "credibility": credibility, "note": note,
            },
            concept_word="absence",
        )
        self.cortex.put_link(key, source_id, "fact:derived_from_source", author=author_id)
        return {
            "status": "absence_added", "fact_id": key,
            "fact_type": "absence", "origin": "direct",
            "fact_status": status, "gap_type": gap_type, "credibility": credibility,
        }

    # ------------------------------------------------------------------
    # Inferred Facts
    # ------------------------------------------------------------------

    def op_add_inferred(
        self,
        fact_type: str,
        content: str,
        inputs: List[Dict[str, Any]],
        extraction_method: str = "human",
        extraction_confidence: float = 0.8,
        extraction_model: str = "",
        extraction_llm_trust: float = 1.0,
        inference_method: str = "human",
        inference_confidence: float = 0.8,
        inference_model: str = "",
        inference_llm_trust: float = 1.0,
        steps: Optional[List[Dict[str, Any]]] = None,
        event_time: str = "",
        event_time_precision: str = "date",
        place: Optional[Dict[str, Any]] = None,
        entities: Optional[List[Dict[str, Any]]] = None,
        visibility: str = "inferred",
        polarity: Optional[Dict[str, Any]] = None,
        status: str = "unverified",
        note: str = "",
    ) -> Dict[str, Any]:
        """
        Add an Inferred Fact — derived from multiple Sources via Curation.

        credibility = extraction_conf × inference_conf
                    × Σ(source_i.credibility_effective × weight_i / total_weight)

        LLM usage: algo.confidence = task_confidence × llm_trust

        Fix 2: weight normalisation prevents credibility > 1.0.
        Fix 4: inputs carry only {source_id, weight, role}; credibility read internally.
        Fix 5: status defaults to "unverified".

        inputs: list of {source_id, weight, role}
        """
        self._require_concept()
        if fact_type not in FACT_TYPES:
            raise ValueError(f"fact_type must be one of {FACT_TYPES}.")
        if status not in FACT_STATUSES:
            raise ValueError(f"status must be one of {FACT_STATUSES}.")
        if not inputs:
            raise ValueError("inferred fact requires at least one input source.")
        if extraction_method not in ALGO_METHODS:
            raise ValueError(f"extraction_method must be one of {ALGO_METHODS}.")
        if inference_method not in ALGO_METHODS:
            raise ValueError(f"inference_method must be one of {ALGO_METHODS}.")
        for inp in inputs:
            self._require_access(inp["source_id"], "Input source")

        author_id, _ = self._author_and_scopes()

        # Fix 2: require non-zero weight sum
        total_weight = sum(float(inp.get("weight", 0.0)) for inp in inputs)
        if total_weight <= 0:
            raise ValueError("inputs weight sum must be > 0.")

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
        provenance["curator"] = extraction_method
        overall_confidence = provenance["overall_confidence"]
        source_weighted    = provenance["source_weighted_credibility"]

        key = self._put_atom(
            content=content,
            atom_type="fact_inferred",
            subset="facts",
            meta_extra={
                "role": "fact", "origin": "inferred", "fact_type": fact_type,
                "status": status,
                "source_ids": [inp["source_id"] for inp in inputs],
                "provenance": provenance,
                "credibility": overall_confidence,
                "event_time": event_time, "event_time_precision": event_time_precision,
                "place": place or {}, "entities": entities or [],
                "visibility": visibility, "polarity": polarity or {},
                "note": note,
            },
            concept_word=f"inferred_{fact_type}",
        )
        for inp in inputs:
            self.cortex.put_link(
                key, inp["source_id"], "fact:derived_from_source", author=author_id,
            )
        # Separate provenance atom for traceable audit trail
        prov_key = self._put_atom(
            content=f"provenance:{key[:12]}",
            atom_type="fact_provenance",
            subset="provenances",
            meta_extra={
                "role": "provenance", "fact_id": key, "provenance": provenance,
            },
            concept_word="provenance",
        )
        self.cortex.put_link(key, prov_key, "fact:has_provenance", author=author_id)
        return {
            "status": "inferred_fact_added", "fact_id": key, "provenance_id": prov_key,
            "fact_type": fact_type, "origin": "inferred",
            "fact_status": status, "credibility": overall_confidence,
            "source_weighted_credibility": round(source_weighted, 4),
        }

    # ------------------------------------------------------------------
    # FactSet
    # ------------------------------------------------------------------

    def op_new_factset(
        self,
        label: str,
        criteria: str = "",
        extraction_method: str = "manual",
        note: str = "",
    ) -> Dict[str, Any]:
        """
        Create a FactSet — a purpose-driven subset of Facts.
        The same Fact can belong to multiple FactSets simultaneously.
        """
        self._require_concept()
        if not label:
            raise ValueError("factset label is required.")
        key = self._put_atom(
            content=note or label,
            atom_type="fact_set",
            subset="fact_sets",
            meta_extra={
                "role": "fact_set", "label": label,
                "criteria": criteria, "extraction_method": extraction_method,
            },
            concept_word="fact_set",
        )
        return {"status": "factset_created", "factset_id": key, "label": label}

    def op_add_to_factset(
        self, factset_id: str, fact_id: str,
    ) -> Dict[str, Any]:
        """Add a Fact to a FactSet. The same Fact can belong to multiple FactSets."""
        self._require_concept()
        self._require_access(factset_id, "FactSet")
        self._require_access(fact_id, "Fact")
        author_id, _ = self._author_and_scopes()
        self.cortex.put_link(factset_id, fact_id, "fact:contains",  author=author_id)
        self.cortex.put_link(fact_id, factset_id, "fact:member_of", author=author_id)
        return {"status": "added_to_factset", "factset_id": factset_id, "fact_id": fact_id}

    # ------------------------------------------------------------------
    # Entity linking
    # ------------------------------------------------------------------

    def op_link_entity(
        self,
        fact_id: str,
        entity_id: str,
        entity_type: str,
        role: str = "involved",
    ) -> Dict[str, Any]:
        """
        Link a Fact to an Entity (Human / Organization / Community / Geo).

        Fix 6: single _author_and_scopes() call.
        entity_type: human / organization / community / geo
        role: involved / speaker / subject / location / beneficiary / victim
        """
        self._require_concept()
        self._require_access(fact_id,   "Fact")
        self._require_access(entity_id, "Entity")
        if entity_type not in ENTITY_TYPES:
            raise ValueError(f"entity_type must be one of {ENTITY_TYPES}.")
        author_id, scopes = self._author_and_scopes()

        link_key = self.cortex.put_chunk(
            content=f"entity_link:{fact_id[:8]}-{entity_id[:8]}",
            meta={
                "type": "fact_entity_link", "concept": "fact",
                "fact_id": fact_id, "entity_id": entity_id,
                "entity_type": entity_type, "role": role,
                "created_at": time.time(),
            },
            author=author_id, scopes=scopes,
        )
        self._register(link_key, subset_suffix="entities")
        self.cortex.put_link(fact_id,   entity_id, f"fact:involves_{entity_type}", author=author_id)
        self.cortex.put_link(entity_id, fact_id,   "fact:evidenced_by",            author=author_id)
        self.cortex.put_link(link_key,  fact_id,   "fact:about_fact",              author=author_id)
        self.cortex.put_link(link_key,  entity_id, "fact:about_entity",            author=author_id)
        return {
            "status": "entity_linked", "link_id": link_key,
            "fact_id": fact_id, "entity_id": entity_id,
            "entity_type": entity_type, "role": role,
        }

    # ------------------------------------------------------------------
    # Analysis
    # ------------------------------------------------------------------

    def op_map(self) -> Dict[str, Any]:
        self._require_concept()
        meta = self._meta(self.concept_id)
        return {
            "fact_root_id": self.concept_id, "concept_id": self.concept_id,
            "title": meta.get("title", ""),
            **{suffix: self._members(suffix) for suffix in self.SUBSETS},
        }

    def op_diagnose(self, limit: int = 10) -> Dict[str, Any]:
        """
        Diagnose quality and completeness of the fact collection.

        Flags:
            low_credibility_facts:          credibility < 0.4
            absence_facts:                  Intelligence.Gap candidates
            claims_without_corroboration:   claim with no corroboration list
            inferred_without_provenance:    inferred fact missing provenance
            llm_generated_facts:            LLM used for extraction or inference
            stale_facts:                    no event_time recorded
            disputed_or_retracted:          status != active/unverified
        """
        self._require_concept()
        all_facts    = [self._summary(k) for k in self._members("facts")]
        all_sources  = [self._summary(k) for k in self._members("sources")]
        all_evals    = [self._summary(k) for k in self._members("source_evals")]
        all_factsets = [self._summary(k) for k in self._members("fact_sets")]

        low_cred = [
            f for f in all_facts if float(f["meta"].get("credibility", 1.0)) < 0.4
        ]
        absence_facts = [
            f for f in all_facts if f["meta"].get("fact_type") == "absence"
        ]
        claims_no_corr = [
            f for f in all_facts
            if f["meta"].get("fact_type") == "claim"
            and not f["meta"].get("corroboration")
        ]
        inferred_no_prov = [
            f for f in all_facts
            if f["meta"].get("origin") == "inferred"
            and not f["meta"].get("provenance")
        ]
        llm_gen = [
            f for f in all_facts
            if f["meta"].get("origin") == "inferred"
            and (
                (f["meta"].get("provenance") or {})
                .get("extraction_algorithm", {}).get("method") == "llm"
                or
                (f["meta"].get("provenance") or {})
                .get("inference_algorithm",  {}).get("method") == "llm"
            )
        ]
        stale = [f for f in all_facts if not f["meta"].get("event_time")]
        disputed = [
            f for f in all_facts
            if f["meta"].get("status") in ("disputed", "retracted", "superseded")
        ]

        return {
            "fact_root_id": self.concept_id,
            "counts": {
                "facts": len(all_facts), "sources": len(all_sources),
                "source_evals": len(all_evals), "fact_sets": len(all_factsets),
            },
            "diagnosis": {
                "low_credibility_facts":        low_cred[-limit:],
                "absence_facts":                absence_facts[-limit:],
                "claims_without_corroboration": claims_no_corr[-limit:],
                "inferred_without_provenance":  inferred_no_prov[-limit:],
                "llm_generated_facts":          llm_gen[-limit:],
                "stale_facts":                  stale[-limit:],
                "disputed_or_retracted":        disputed[-limit:],
            },
        }

    def op_trace(self, fact_id: str) -> Dict[str, Any]:
        """
        Trace the evidence chain of a Fact back to its Sources.

        Fix 1: For Direct Facts, shows effective credibility (latest eval applied).
        Direct:   fact → source (+ corroboration sources)
        Inferred: fact → provenance → expanded inputs + steps
        """
        self._require_concept()
        self._require_access(fact_id, "Fact")
        fact_meta = self._meta(fact_id)
        origin    = fact_meta.get("origin", "direct")

        result: Dict[str, Any] = {
            "fact_id":    fact_id,
            "fact_type":  fact_meta.get("fact_type"),
            "origin":     origin,
            "fact_status": fact_meta.get("status", "active"),
            "credibility": fact_meta.get("credibility"),
            "content":    self._content(fact_id),
        }

        if origin == "direct":
            src_id = fact_meta.get("source_id", "")
            corr   = fact_meta.get("corroboration", [])
            if src_id and self._visible(src_id):
                src_summary = self._summary(src_id)
                # Fix 1: effective credibility (latest eval)
                src_summary["effective_credibility"] = \
                    self._effective_source_credibility(src_id)
                result["source"] = src_summary
            else:
                result["source"] = None
            result["corroboration"] = [
                self._summary(c) for c in corr if self._visible(c)
            ]

        elif origin == "inferred":
            prov = fact_meta.get("provenance", {})
            result["provenance"] = prov
            result["input_sources"] = [
                self._summary(inp["source_id"])
                for inp in prov.get("inputs", [])
                if self._visible(inp.get("source_id", ""))
            ]
            result["steps"] = prov.get("steps", [])
            result["credibility_breakdown"] = {
                "extraction_confidence":       (
                    prov.get("extraction_algorithm", {}).get("confidence")
                ),
                "inference_confidence":        (
                    prov.get("inference_algorithm", {}).get("confidence")
                ),
                "source_weighted_credibility": prov.get("source_weighted_credibility"),
                "overall_confidence":          prov.get("overall_confidence"),
                "formula": (
                    "extraction_conf × inference_conf × "
                    "Σ(source_i.credibility × weight_i / total_weight)"
                ),
            }

        return result
