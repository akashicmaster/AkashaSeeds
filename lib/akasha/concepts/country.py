"""
Country Concept Model.
- root / open / list / map / soft delete
- names, territory, capital, government, population, economy
- dual namespace
- SpaceConcept compatible
"""
import time
import logging
from typing import Any, Dict, List, Optional
from lib.akasha.concepts.base import BaseConcept

logger = logging.getLogger("Harmonia.Concept.Country")

CONTEXT_KEY_ACTIVE = "active_country_root"
INDEX_SET = "set:country:index"
_CONCEPT_WORD_ALIAS_PREFIX = "concept:word:"

COUNTRY_TYPES = (
    "state", "polity", "empire", "kingdom", "republic", "federation",
    "colony", "autonomous_region", "disputed_state", "historical_state", "other",
)
NAME_TYPES = (
    "official", "short", "legal", "historical", "native", "exonym",
    "abbreviation", "former", "other",
)
TERRITORY_TYPES = (
    "sovereign", "claimed", "administered", "occupied", "historical",
    "disputed", "overseas", "core", "other",
)
GOVERNMENT_TYPES = (
    "monarchy", "republic", "federal_republic", "constitutional_monarchy",
    "dictatorship", "military", "theocracy", "colony", "protectorate",
    "transitional", "unknown", "other",
)
ECONOMY_TYPES = (
    "gdp", "gdp_per_capita", "currency", "trade", "sector",
    "resource", "sanction", "debt", "inflation", "other",
)
SOVEREIGNTY_TYPES = (
    "recognized", "partially_recognized", "disputed", "occupied",
    "dependent", "protectorate", "colony", "de_facto", "de_jure",
    "historical", "unknown", "other",
)
CLAIM_TYPES = (
    "territorial", "sovereignty", "maritime", "border",
    "administrative", "historical", "symbolic", "other",
)
ADMINISTRATION_TYPES = (
    "governs", "administers", "occupies", "claims",
    "leases", "protects", "oversees", "contests", "other",
)
LAW_TYPES = (
    "constitution", "statute", "decree", "treaty", "customary",
    "emergency", "administrative", "international", "other",
)
LAW_STATUS_TYPES = (
    "active", "suspended", "repealed", "superseded",
    "disputed", "draft", "unknown",
)
COUNTRY_EVENT_TYPES = (
    "founding", "independence", "annexation", "cession",
    "war", "civil_war", "revolution", "coup", "treaty",
    "election", "regime_change", "collapse", "recognition",
    "border_change", "law_change", "capital_change",
    "population_change", "economic_event", "other",
)

SUBSET_TO_RELATION: Dict[str, str] = {
    "names":           "country:has_name",
    "territories":     "country:has_territory",
    "capitals":        "country:has_capital",
    "governments":     "country:has_government",
    "populations":     "country:has_population",
    "economies":       "country:has_economy",
    "sovereignties":   "country:has_sovereignty",
    "claims":          "country:has_claim",
    "administrations": "country:has_administration",
    "laws":            "country:has_law",
    "law_changes":     "country:has_law_change",
    "corr_links":      "country:has_correspondence",
    "events":          "country:has_event",
    "evals":           "country:has_eval",
    "disputes":        "country:has_dispute",
}


class CountryConcept(BaseConcept):
    """Evidence-grounded country / polity / administrative entity model."""

    CONCEPT_PREFIX = "country"
    CONTEXT_KEY_ACTIVE = CONTEXT_KEY_ACTIVE
    CONCEPT_METHODS = {
        "new": {
            "op": "op_new",
        },
        "open": {
            "op": "op_open",
            "coerce": lambda d: {
                "country_id": (
                    d.get("country_id")
                    or d.get("id")
                    or d.get("concept_id")
                    or ""
                )
            },
        },
        "ls": {
            "op": "op_list_all",
        },
        "map": {
            "op": "op_map",
        },
        "rm": {
            "op": "op_delete",
        },
        # Basic country attributes
        "name.add":      {"op": "op_add_name"},
        "territory.add": {"op": "op_add_territory"},
        "capital.set":   {"op": "op_set_capital"},
        "gov.set":       {"op": "op_set_government"},
        "pop.set":       {"op": "op_set_population"},
        "econ.add":      {"op": "op_add_economy"},
        # Sovereignty / political geography / law / events
        "sovereignty.set": {"op": "op_set_sovereignty"},
        "claim.add":       {"op": "op_add_claim"},
        "admin.add":       {"op": "op_add_administration"},
        "law.add":         {"op": "op_add_law"},
        "law.change":      {"op": "op_change_law"},
        "event.add":       {"op": "op_add_event"},
        "corr.link":       {"op": "op_link_correspondence"},
        # Read / analysis
        "profile":    {"op": "op_profile"},
        "timeline":   {"op": "op_timeline"},
        "observable": {"op": "op_observable"},
        "diagnose":   {"op": "op_diagnose"},
        "trace":      {"op": "op_trace"},
    }
    SUBSETS = list(SUBSET_TO_RELATION.keys())

    def __init__(self, session: Any, concept_id: Optional[str] = None):
        super().__init__(session, concept_id)
        if not self.concept_id:
            stored = getattr(self.session, "get_context", lambda k: None)(
                CONTEXT_KEY_ACTIVE
            )
            if stored:
                self.concept_id = stored
                self.set_name = f"set:concept:{self.concept_id}"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _country_set(self, suffix: Optional[str] = None) -> str:
        base = f"set:country:{self.concept_id}"
        return f"{base}:{suffix}" if suffix else base

    def _author_and_scopes(self):
        author_id = getattr(self.session, "client_id", "system")
        scopes = [f"owner:user_{author_id}", f"view:user_{author_id}"]
        return author_id, scopes

    def _create_sets(self) -> None:
        self.ensure_concept_set()
        self.cortex.create_set(self._country_set())
        for suffix in self.SUBSETS:
            self.cortex.create_set(self._country_set(suffix))
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
                "concept_model": "country",
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
        self.cortex.add_to_set(self._country_set(), key)
        if subset_suffix:
            self.cortex.add_to_set(self._country_set(subset_suffix), key)
        if concept_word:
            cw_key = self._get_or_create_concept_word(concept_word)
            self.register_concept_node(cw_key)
            self.cortex.put_link(
                key,
                cw_key,
                "sys:derived_from",
                author=author_id,
            )

    def _require_access(self, atom_id: str, label: str = "Atom") -> None:
        if not atom_id:
            raise ValueError(f"{label} id is required.")
        if not self.cortex.check_access(atom_id, self.allowed_scopes):
            raise RuntimeError(f"{label} not accessible: {atom_id[:12]}")

    def _visible(self, atom_id: str) -> bool:
        return bool(atom_id and self.cortex.check_access(atom_id, self.allowed_scopes))

    def _members(self, suffix: str) -> List[str]:
        return [
            key
            for key in self.cortex.get_collection_members(self._country_set(suffix))
            if self._visible(key)
        ]

    def _meta(self, key: str) -> Dict[str, Any]:
        return self.cortex.get_meta(key) or {}

    def _content(self, key: str) -> str:
        return self.cortex.get_chunk(key) or ""

    def _summary(self, key: str) -> Dict[str, Any]:
        return {
            "id": key,
            "content": self._content(key),
            "meta": self._meta(key),
        }

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
            "concept": "country",
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
        self._register(
            key,
            subset_suffix=subset,
            concept_word=concept_word,
        )
        relation = SUBSET_TO_RELATION.get(subset, f"country:has_{subset}")
        self.cortex.put_link(
            self.concept_id,
            key,
            relation,
            author=author_id,
        )
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

    def op_new(
        self,
        name: str,
        description: str = "",
        country_type: str = "state",
        source_id: str = "",
        evidence: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new Country root.
        country_type examples:
            state / polity / empire / kingdom / republic / federation /
            colony / autonomous_region / disputed_state / historical_state / other
        """
        if not name:
            raise ValueError("country.new requires name.")
        if country_type not in COUNTRY_TYPES:
            raise ValueError(f"country_type must be one of {COUNTRY_TYPES}.")
        author_id, scopes = self._author_and_scopes()
        if source_id:
            self._require_access(source_id, "Source")
        for ev_id in self._as_list(evidence):
            self._require_access(ev_id, "Evidence")
        root_id = self.cortex.put_chunk(
            content=f"[ Country: {name} ]",
            meta={
                "type": "concept",
                "concept": "country",
                "role": "root",
                "name": name,
                "description": description,
                "country_type": country_type,
                "source_id": source_id or None,
                "evidence": evidence or [],
                "created_at": time.time(),
                "deleted": False,
            },
            author=author_id,
            scopes=scopes,
        )
        self.concept_id = root_id
        self.set_name = f"set:concept:{self.concept_id}"
        self._create_sets()
        self.cortex.add_to_set(self._country_set(), root_id)
        self.cortex.add_to_set(INDEX_SET, root_id)
        if source_id:
            self.cortex.put_link(
                root_id,
                source_id,
                "country:identified_from",
                author=author_id,
            )
        for ev_id in self._as_list(evidence):
            self.cortex.put_link(
                root_id,
                ev_id,
                "country:evidenced_by",
                author=author_id,
            )
        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, root_id)
        logger.info("[CountryConcept] Created '%s' (%s)", name, root_id[:8])
        return {
            "status": "created",
            "concept_id": root_id,
            "country_id": root_id,
            "name": name,
            "country_type": country_type,
        }

    def op_open(self, country_id: str) -> Dict[str, Any]:
        meta = self._meta(country_id)
        if not meta or meta.get("concept") != "country":
            raise RuntimeError(f"Atom '{country_id[:12]}' is not a country root.")
        if not self._visible(country_id):
            raise RuntimeError(f"Country not accessible: {country_id[:12]}")
        self.concept_id = country_id
        self.set_name = f"set:concept:{self.concept_id}"
        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, country_id)
        return {
            "status": "opened",
            "concept_id": country_id,
            "country_id": country_id,
            "name": meta.get("name", ""),
            "country_type": meta.get("country_type", ""),
        }

    def op_list_all(self) -> Dict[str, Any]:
        countries = []
        for key in self.cortex.get_collection_members(INDEX_SET):
            if not self._visible(key):
                continue
            meta = self._meta(key)
            if meta.get("concept") != "country":
                continue
            if meta.get("deleted"):
                continue
            countries.append(
                {
                    "country_id": key,
                    "concept_id": key,
                    "name": meta.get("name", ""),
                    "country_type": meta.get("country_type", ""),
                    "description": meta.get("description", ""),
                    "created_at": meta.get("created_at", 0),
                }
            )
        countries.sort(key=lambda x: x.get("created_at", 0), reverse=True)
        return {
            "countries": countries,
            "count": len(countries),
        }

    def op_map(self) -> Dict[str, Any]:
        self._require_concept()
        meta = self._meta(self.concept_id)
        return {
            "country_id": self.concept_id,
            "concept_id": self.concept_id,
            "name": meta.get("name", ""),
            "country_type": meta.get("country_type", ""),
            "description": meta.get("description", ""),
            **{suffix: self._members(suffix) for suffix in self.SUBSETS},
        }

    def op_delete(self) -> Dict[str, Any]:
        """
        Soft-delete the active Country root.
        The root is removed from set:country:index.
        Child atoms are retained for auditability.
        """
        self._require_concept()
        target = self.concept_id
        try:
            self.cortex.remove_from_set(INDEX_SET, target)
        except Exception:
            logger.warning(
                "[CountryConcept] Failed to remove %s from index",
                target[:8],
                exc_info=True,
            )
        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, None)
        self.concept_id = None
        return {
            "status": "deleted",
            "country_id": target,
            "soft_delete": True,
        }

    # ------------------------------------------------------------------
    # Basic country attributes
    # ------------------------------------------------------------------

    def _link_evidence(
        self,
        atom_id: str,
        source_id: str = "",
        evidence: Optional[List[str]] = None,
    ) -> None:
        author_id, _ = self._author_and_scopes()
        if source_id:
            self._require_access(source_id, "Source")
            self.cortex.put_link(
                atom_id,
                source_id,
                "country:evidenced_by",
                author=author_id,
            )
        for ev_id in self._as_list(evidence):
            self._require_access(ev_id, "Evidence")
            self.cortex.put_link(
                atom_id,
                ev_id,
                "country:evidenced_by",
                author=author_id,
            )

    def op_add_name(
        self,
        name: str,
        name_type: str = "official",
        language: str = "",
        script: str = "",
        valid_from: str = "",
        valid_to: str = "",
        source_id: str = "",
        evidence: Optional[List[str]] = None,
        confidence: float = 0.8,
        note: str = "",
    ) -> Dict[str, Any]:
        """Add a country name. Event-sourced; does not mutate root name."""
        self._require_concept()
        if not name:
            raise ValueError("country.name.add requires name.")
        if name_type not in NAME_TYPES:
            raise ValueError(f"name_type must be one of {NAME_TYPES}.")
        key = self._put_atom(
            content=note or name,
            atom_type="country_name",
            subset="names",
            meta_extra={
                "role": "name",
                "name": name,
                "name_type": name_type,
                "language": language,
                "script": script,
                "valid_from": valid_from,
                "valid_to": valid_to,
                "confidence": self._clamp01(confidence, 0.8),
                "source_id": source_id or None,
                "evidence": evidence or [],
            },
            concept_word="name",
        )
        self._link_evidence(key, source_id, evidence)
        return {
            "status": "name_added",
            "name_id": key,
            "name": name,
            "name_type": name_type,
        }

    def op_add_territory(
        self,
        geo_id: str = "",
        place_id: str = "",
        corr_id: str = "",
        territory_type: str = "sovereign",
        label: str = "",
        valid_from: str = "",
        valid_to: str = "",
        source_id: str = "",
        evidence: Optional[List[str]] = None,
        confidence: float = 0.7,
        note: str = "",
    ) -> Dict[str, Any]:
        """
        Add a territory reference.
        geo_id / place_id may point to GeoConcept atoms.
        corr_id may point to a CorrespondenceConcept link.
        """
        self._require_concept()
        if territory_type not in TERRITORY_TYPES:
            raise ValueError(f"territory_type must be one of {TERRITORY_TYPES}.")
        for ref_id, label_name in (
            (geo_id, "Geo root"),
            (place_id, "Place"),
            (corr_id, "Correspondence"),
        ):
            if ref_id:
                self._require_access(ref_id, label_name)
        author_id, _ = self._author_and_scopes()
        content = note or label or f"territory:{territory_type}"
        key = self._put_atom(
            content=content,
            atom_type="country_territory",
            subset="territories",
            meta_extra={
                "role": "territory",
                "territory_type": territory_type,
                "label": label,
                "geo_id": geo_id or None,
                "place_id": place_id or None,
                "corr_id": corr_id or None,
                "valid_from": valid_from,
                "valid_to": valid_to,
                "confidence": self._clamp01(confidence, 0.7),
                "source_id": source_id or None,
                "evidence": evidence or [],
            },
            concept_word="territory",
        )
        if geo_id:
            self.cortex.put_link(key, geo_id, "country:uses_geo", author=author_id)
        if place_id:
            self.cortex.put_link(key, place_id, "country:territory_place", author=author_id)
        if corr_id:
            self.cortex.put_link(key, corr_id, "country:territory_correspondence", author=author_id)
        self._link_evidence(key, source_id, evidence)
        return {
            "status": "territory_added",
            "territory_id": key,
            "territory_type": territory_type,
            "place_id": place_id or None,
            "corr_id": corr_id or None,
        }

    def op_set_capital(
        self,
        name: str = "",
        place_id: str = "",
        corr_id: str = "",
        capital_type: str = "official",
        valid_from: str = "",
        valid_to: str = "",
        source_id: str = "",
        evidence: Optional[List[str]] = None,
        confidence: float = 0.8,
        note: str = "",
    ) -> Dict[str, Any]:
        """Record a capital. Event-sourced; latest active capital is derived at read time."""
        self._require_concept()
        if not name and not place_id:
            raise ValueError("country.capital.set requires name or place_id.")
        if place_id:
            self._require_access(place_id, "Capital place")
        if corr_id:
            self._require_access(corr_id, "Correspondence")
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=note or name or f"capital:{place_id[:12]}",
            atom_type="country_capital",
            subset="capitals",
            meta_extra={
                "role": "capital",
                "name": name,
                "place_id": place_id or None,
                "corr_id": corr_id or None,
                "capital_type": capital_type,
                "valid_from": valid_from,
                "valid_to": valid_to,
                "confidence": self._clamp01(confidence, 0.8),
                "source_id": source_id or None,
                "evidence": evidence or [],
            },
            concept_word="capital",
        )
        if place_id:
            self.cortex.put_link(key, place_id, "country:capital_place", author=author_id)
        if corr_id:
            self.cortex.put_link(key, corr_id, "country:capital_correspondence", author=author_id)
        self._link_evidence(key, source_id, evidence)
        return {
            "status": "capital_set",
            "capital_id": key,
            "name": name,
            "place_id": place_id or None,
        }

    def op_set_government(
        self,
        government_type: str,
        head_of_state: str = "",
        head_of_government: str = "",
        ruling_party: str = "",
        constitution: str = "",
        valid_from: str = "",
        valid_to: str = "",
        source_id: str = "",
        evidence: Optional[List[str]] = None,
        confidence: float = 0.7,
        note: str = "",
    ) -> Dict[str, Any]:
        """Record a government form or regime state."""
        self._require_concept()
        if government_type not in GOVERNMENT_TYPES:
            raise ValueError(f"government_type must be one of {GOVERNMENT_TYPES}.")
        for ref_id, label in (
            (head_of_state, "Head of state"),
            (head_of_government, "Head of government"),
            (ruling_party, "Ruling party"),
        ):
            if ref_id:
                self._require_access(ref_id, label)
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=note or f"government:{government_type}",
            atom_type="country_government",
            subset="governments",
            meta_extra={
                "role": "government",
                "government_type": government_type,
                "head_of_state": head_of_state or None,
                "head_of_government": head_of_government or None,
                "ruling_party": ruling_party or None,
                "constitution": constitution,
                "valid_from": valid_from,
                "valid_to": valid_to,
                "confidence": self._clamp01(confidence, 0.7),
                "source_id": source_id or None,
                "evidence": evidence or [],
            },
            concept_word="government",
        )
        if head_of_state:
            self.cortex.put_link(key, head_of_state, "country:head_of_state", author=author_id)
        if head_of_government:
            self.cortex.put_link(key, head_of_government, "country:head_of_government", author=author_id)
        if ruling_party:
            self.cortex.put_link(key, ruling_party, "country:ruling_party", author=author_id)
        self._link_evidence(key, source_id, evidence)
        return {
            "status": "government_set",
            "government_id": key,
            "government_type": government_type,
        }

    def op_set_population(
        self,
        value: Any,
        year: str = "",
        unit: str = "persons",
        estimate_type: str = "estimate",
        method: str = "",
        source_id: str = "",
        evidence: Optional[List[str]] = None,
        confidence: float = 0.7,
        note: str = "",
    ) -> Dict[str, Any]:
        """Record a population value or estimate."""
        self._require_concept()
        key = self._put_atom(
            content=note or f"population:{value}",
            atom_type="country_population",
            subset="populations",
            meta_extra={
                "role": "population",
                "value": value,
                "year": year,
                "unit": unit,
                "estimate_type": estimate_type,
                "method": method,
                "confidence": self._clamp01(confidence, 0.7),
                "source_id": source_id or None,
                "evidence": evidence or [],
            },
            concept_word="population",
        )
        self._link_evidence(key, source_id, evidence)
        return {
            "status": "population_set",
            "population_id": key,
            "value": value,
            "year": year,
        }

    def op_add_economy(
        self,
        economy_type: str,
        value: Any = None,
        unit: str = "",
        year: str = "",
        label: str = "",
        source_id: str = "",
        evidence: Optional[List[str]] = None,
        confidence: float = 0.7,
        note: str = "",
    ) -> Dict[str, Any]:
        """Record an economic datum: GDP, currency, resource, sanction, trade, etc."""
        self._require_concept()
        if economy_type not in ECONOMY_TYPES:
            raise ValueError(f"economy_type must be one of {ECONOMY_TYPES}.")
        key = self._put_atom(
            content=note or label or f"economy:{economy_type}:{value}",
            atom_type="country_economy",
            subset="economies",
            meta_extra={
                "role": "economy",
                "economy_type": economy_type,
                "label": label,
                "value": value,
                "unit": unit,
                "year": year,
                "confidence": self._clamp01(confidence, 0.7),
                "source_id": source_id or None,
                "evidence": evidence or [],
            },
            concept_word="economy",
        )
        self._link_evidence(key, source_id, evidence)
        return {
            "status": "economy_added",
            "economy_id": key,
            "economy_type": economy_type,
            "value": value,
            "unit": unit,
        }

    # ------------------------------------------------------------------
    # Sovereignty / political geography / law / events
    # ------------------------------------------------------------------

    def op_set_sovereignty(
        self,
        sovereignty_type: str,
        recognized_by: Optional[List[str]] = None,
        disputed_by: Optional[List[str]] = None,
        valid_from: str = "",
        valid_to: str = "",
        basis: str = "",
        source_id: str = "",
        evidence: Optional[List[str]] = None,
        confidence: float = 0.7,
        note: str = "",
    ) -> Dict[str, Any]:
        """Record sovereignty status. Event-sourced; does not mutate prior status."""
        self._require_concept()
        if sovereignty_type not in SOVEREIGNTY_TYPES:
            raise ValueError(f"sovereignty_type must be one of {SOVEREIGNTY_TYPES}.")
        for rid in self._as_list(recognized_by):
            self._require_access(rid, "Recognizing entity")
        for did in self._as_list(disputed_by):
            self._require_access(did, "Disputing entity")
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=note or f"sovereignty:{sovereignty_type}",
            atom_type="country_sovereignty",
            subset="sovereignties",
            meta_extra={
                "role": "sovereignty",
                "sovereignty_type": sovereignty_type,
                "recognized_by": recognized_by or [],
                "disputed_by": disputed_by or [],
                "valid_from": valid_from,
                "valid_to": valid_to,
                "basis": basis,
                "confidence": self._clamp01(confidence, 0.7),
                "source_id": source_id or None,
                "evidence": evidence or [],
            },
            concept_word="sovereignty",
        )
        for rid in self._as_list(recognized_by):
            self.cortex.put_link(key, rid, "country:recognized_by", author=author_id)
        for did in self._as_list(disputed_by):
            self.cortex.put_link(key, did, "country:disputed_by", author=author_id)
        self._link_evidence(key, source_id, evidence)
        return {
            "status": "sovereignty_set",
            "sovereignty_id": key,
            "sovereignty_type": sovereignty_type,
        }

    def op_add_claim(
        self,
        claim_type: str,
        target_id: str,
        description: str = "",
        claimant_id: str = "",
        corr_id: str = "",
        valid_from: str = "",
        valid_to: str = "",
        status: str = "active",
        source_id: str = "",
        evidence: Optional[List[str]] = None,
        confidence: float = 0.6,
        note: str = "",
    ) -> Dict[str, Any]:
        """Record a political or territorial claim."""
        self._require_concept()
        if claim_type not in CLAIM_TYPES:
            raise ValueError(f"claim_type must be one of {CLAIM_TYPES}.")
        self._require_access(target_id, "Claim target")
        if claimant_id:
            self._require_access(claimant_id, "Claimant")
        if corr_id:
            self._require_access(corr_id, "Correspondence")
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=note or description or f"claim:{claim_type}",
            atom_type="country_claim",
            subset="claims",
            meta_extra={
                "role": "claim",
                "claim_type": claim_type,
                "target_id": target_id,
                "claimant_id": claimant_id or self.concept_id,
                "corr_id": corr_id or None,
                "description": description,
                "valid_from": valid_from,
                "valid_to": valid_to,
                "status": status,
                "confidence": self._clamp01(confidence, 0.6),
                "source_id": source_id or None,
                "evidence": evidence or [],
            },
            concept_word="claim",
        )
        self.cortex.put_link(key, target_id, "country:claims", author=author_id)
        self.cortex.put_link(self.concept_id, target_id, "country:claims", author=author_id)
        if claimant_id:
            self.cortex.put_link(key, claimant_id, "country:claimant", author=author_id)
        if corr_id:
            self.cortex.put_link(key, corr_id, "country:claim_correspondence", author=author_id)
        self._link_evidence(key, source_id, evidence)
        return {
            "status": "claim_added",
            "claim_id": key,
            "claim_type": claim_type,
            "target_id": target_id,
        }

    def op_add_administration(
        self,
        target_id: str,
        administration_type: str = "administers",
        corr_id: str = "",
        valid_from: str = "",
        valid_to: str = "",
        legal_basis: str = "",
        source_id: str = "",
        evidence: Optional[List[str]] = None,
        confidence: float = 0.7,
        note: str = "",
    ) -> Dict[str, Any]:
        """Record administrative control over a place, territory, region, or entity."""
        self._require_concept()
        if administration_type not in ADMINISTRATION_TYPES:
            raise ValueError(
                f"administration_type must be one of {ADMINISTRATION_TYPES}."
            )
        self._require_access(target_id, "Administration target")
        if corr_id:
            self._require_access(corr_id, "Correspondence")
        author_id, _ = self._author_and_scopes()
        relation = f"country:{administration_type}"
        key = self._put_atom(
            content=note or f"administration:{administration_type}",
            atom_type="country_administration",
            subset="administrations",
            meta_extra={
                "role": "administration",
                "administration_type": administration_type,
                "target_id": target_id,
                "corr_id": corr_id or None,
                "valid_from": valid_from,
                "valid_to": valid_to,
                "legal_basis": legal_basis,
                "confidence": self._clamp01(confidence, 0.7),
                "source_id": source_id or None,
                "evidence": evidence or [],
            },
            concept_word="administration",
        )
        self.cortex.put_link(key, target_id, relation, author=author_id)
        self.cortex.put_link(self.concept_id, target_id, relation, author=author_id)
        if corr_id:
            self.cortex.put_link(
                key, corr_id, "country:administration_correspondence", author=author_id
            )
        self._link_evidence(key, source_id, evidence)
        return {
            "status": "administration_added",
            "administration_id": key,
            "administration_type": administration_type,
            "target_id": target_id,
        }

    def op_add_law(
        self,
        title: str,
        law_type: str = "statute",
        status: str = "active",
        text: str = "",
        jurisdiction_id: str = "",
        valid_from: str = "",
        valid_to: str = "",
        source_id: str = "",
        evidence: Optional[List[str]] = None,
        confidence: float = 0.8,
        note: str = "",
    ) -> Dict[str, Any]:
        """Record a law, treaty, constitution, decree, or governing rule."""
        self._require_concept()
        if not title:
            raise ValueError("country.law.add requires title.")
        if law_type not in LAW_TYPES:
            raise ValueError(f"law_type must be one of {LAW_TYPES}.")
        if status not in LAW_STATUS_TYPES:
            raise ValueError(f"status must be one of {LAW_STATUS_TYPES}.")
        if jurisdiction_id:
            self._require_access(jurisdiction_id, "Jurisdiction")
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=note or title,
            atom_type="country_law",
            subset="laws",
            meta_extra={
                "role": "law",
                "title": title,
                "law_type": law_type,
                "status": status,
                "text": text,
                "jurisdiction_id": jurisdiction_id or None,
                "valid_from": valid_from,
                "valid_to": valid_to,
                "confidence": self._clamp01(confidence, 0.8),
                "source_id": source_id or None,
                "evidence": evidence or [],
            },
            concept_word="law",
        )
        if jurisdiction_id:
            self.cortex.put_link(key, jurisdiction_id, "country:applies_to", author=author_id)
        self._link_evidence(key, source_id, evidence)
        return {
            "status": "law_added",
            "law_id": key,
            "title": title,
            "law_type": law_type,
        }

    def op_change_law(
        self,
        law_id: str,
        change: str,
        new_status: str = "",
        event_id: str = "",
        effective_from: str = "",
        source_id: str = "",
        evidence: Optional[List[str]] = None,
        confidence: float = 0.7,
        note: str = "",
    ) -> Dict[str, Any]:
        """Record an immutable law change event. Original law atom is not mutated."""
        self._require_concept()
        self._require_access(law_id, "Law")
        if not change:
            raise ValueError("country.law.change requires change.")
        if new_status and new_status not in LAW_STATUS_TYPES:
            raise ValueError(f"new_status must be one of {LAW_STATUS_TYPES}.")
        if event_id:
            self._require_access(event_id, "Country event")
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=note or change,
            atom_type="country_law_change",
            subset="law_changes",
            meta_extra={
                "role": "law_change",
                "law_id": law_id,
                "change": change,
                "new_status": new_status or None,
                "event_id": event_id or None,
                "effective_from": effective_from,
                "confidence": self._clamp01(confidence, 0.7),
                "source_id": source_id or None,
                "evidence": evidence or [],
            },
            concept_word="law_change",
        )
        self.cortex.put_link(law_id, key, "country:changed_by", author=author_id)
        self.cortex.put_link(key, law_id, "country:changes_law", author=author_id)
        if event_id:
            self.cortex.put_link(key, event_id, "country:caused_by", author=author_id)
        self._link_evidence(key, source_id, evidence)
        return {
            "status": "law_changed",
            "law_change_id": key,
            "law_id": law_id,
            "new_status": new_status or None,
        }

    def op_add_event(
        self,
        event_type: str,
        description: str,
        event_time: str = "",
        place_id: str = "",
        actors: Optional[List[str]] = None,
        affects: Optional[List[str]] = None,
        source_id: str = "",
        evidence: Optional[List[str]] = None,
        confidence: float = 0.7,
        note: str = "",
    ) -> Dict[str, Any]:
        """Record a country-level historical or political event."""
        self._require_concept()
        if event_type not in COUNTRY_EVENT_TYPES:
            raise ValueError(f"event_type must be one of {COUNTRY_EVENT_TYPES}.")
        if not description:
            raise ValueError("country.event.add requires description.")
        if place_id:
            self._require_access(place_id, "Event place")
        for actor_id in self._as_list(actors):
            self._require_access(actor_id, "Actor")
        for target_id in self._as_list(affects):
            self._require_access(target_id, "Affected atom")
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=note or description,
            atom_type="country_event",
            subset="events",
            meta_extra={
                "role": "event",
                "event_type": event_type,
                "description": description,
                "event_time": event_time,
                "place_id": place_id or None,
                "actors": actors or [],
                "affects": affects or [],
                "confidence": self._clamp01(confidence, 0.7),
                "source_id": source_id or None,
                "evidence": evidence or [],
            },
            concept_word="event",
        )
        if place_id:
            self.cortex.put_link(key, place_id, "country:occurred_at", author=author_id)
        for actor_id in self._as_list(actors):
            self.cortex.put_link(key, actor_id, "country:has_actor", author=author_id)
        for target_id in self._as_list(affects):
            self.cortex.put_link(key, target_id, "country:affects", author=author_id)
        self._link_evidence(key, source_id, evidence)
        return {
            "status": "event_added",
            "event_id": key,
            "event_type": event_type,
            "event_time": event_time,
        }

    def op_link_correspondence(
        self,
        corr_id: str,
        relation: str = "associated_with",
        target_id: str = "",
        source_id: str = "",
        evidence: Optional[List[str]] = None,
        confidence: float = 0.7,
        note: str = "",
    ) -> Dict[str, Any]:
        """
        Link this Country record to a CorrespondenceConcept atom.
        Useful for country ↔ geo, historical polity ↔ modern state,
        country ↔ map layer, or disputed territory mappings.
        """
        self._require_concept()
        self._require_access(corr_id, "Correspondence")
        if target_id:
            self._require_access(target_id, "Correspondence target")
        author_id, _ = self._author_and_scopes()
        rel = relation if relation.startswith("country:") else f"country:{relation}"
        key = self._put_atom(
            content=note or f"correspondence:{corr_id[:12]}",
            atom_type="country_correspondence_link",
            subset="corr_links",
            meta_extra={
                "role": "correspondence_link",
                "corr_id": corr_id,
                "target_id": target_id or None,
                "relation": rel,
                "confidence": self._clamp01(confidence, 0.7),
                "source_id": source_id or None,
                "evidence": evidence or [],
            },
            concept_word="correspondence",
        )
        self.cortex.put_link(key, corr_id, "country:uses_correspondence", author=author_id)
        self.cortex.put_link(self.concept_id, corr_id, rel, author=author_id)
        if target_id:
            self.cortex.put_link(
                key, target_id, "country:correspondence_target", author=author_id
            )
        self._link_evidence(key, source_id, evidence)
        return {
            "status": "correspondence_linked",
            "corr_link_id": key,
            "corr_id": corr_id,
            "relation": rel,
        }

    # ------------------------------------------------------------------
    # Read / analysis operators
    # ------------------------------------------------------------------

    def op_profile(self) -> Dict[str, Any]:
        """Return a structured country profile."""
        self._require_concept()
        root_meta = self._meta(self.concept_id)

        def summaries(suffix: str) -> List[Dict[str, Any]]:
            return [self._summary(k) for k in self._members(suffix)]

        names           = summaries("names")
        sovereignties   = summaries("sovereignties")
        capitals        = summaries("capitals")
        governments     = summaries("governments")
        populations     = summaries("populations")
        economies       = summaries("economies")
        claims          = summaries("claims")
        administrations = summaries("administrations")
        laws            = summaries("laws")
        events          = summaries("events")
        corr_links      = summaries("corr_links")

        return {
            "country_id": self.concept_id,
            "name": root_meta.get("name", ""),
            "description": root_meta.get("description", ""),
            "country_type": root_meta.get("country_type", ""),
            "names": names,
            "current": {
                "sovereignty": sovereignties[-1] if sovereignties else None,
                "capital":     capitals[-1]     if capitals     else None,
                "government":  governments[-1]  if governments  else None,
                "population":  populations[-1]  if populations  else None,
                "economy":     economies[-1]    if economies    else None,
            },
            "sovereignties":   sovereignties,
            "claims":          claims,
            "administrations": administrations,
            "laws":            laws,
            "events":          events,
            "correspondences": corr_links,
        }

    def op_timeline(
        self,
        limit: int = 100,
        include_law_changes: bool = True,
        include_states: bool = True,
    ) -> Dict[str, Any]:
        """
        Return chronological country timeline.
        Uses string-sortable dates. Prefer ISO date strings:
            YYYY / YYYY-MM / YYYY-MM-DD / YYYY-MM-DDTHH:MM:SS
        """
        self._require_concept()
        items: List[Dict[str, Any]] = []

        for key in self._members("events"):
            meta = self._meta(key)
            items.append({
                "id": key,
                "kind": "event",
                "time": meta.get("event_time", ""),
                "sort": meta.get("event_time", "") or "9999-12-31T23:59:59",
                "content": self._content(key),
                "meta": meta,
            })

        if include_law_changes:
            for key in self._members("law_changes"):
                meta = self._meta(key)
                items.append({
                    "id": key,
                    "kind": "law_change",
                    "time": meta.get("effective_from", ""),
                    "sort": meta.get("effective_from", "") or "9999-12-31T23:59:59",
                    "content": self._content(key),
                    "meta": meta,
                })

        if include_states:
            _kind_map = {
                "sovereignties":   "sovereignty",
                "claims":          "claim",
                "administrations": "administration",
            }
            for suffix in ("sovereignties", "claims", "administrations"):
                for key in self._members(suffix):
                    meta = self._meta(key)
                    items.append({
                        "id": key,
                        "kind": _kind_map[suffix],
                        "time": meta.get("valid_from", ""),
                        "sort": meta.get("valid_from", "") or "9999-12-31T23:59:59",
                        "content": self._content(key),
                        "meta": meta,
                    })

        items.sort(key=lambda x: x["sort"])
        cap = max(0, int(limit))
        return {
            "country_id": self.concept_id,
            "timeline": items[:cap],
            "count": min(len(items), cap),
            "total": len(items),
        }

    def op_observable(self, limit: int = 100) -> Dict[str, Any]:
        """
        Surface externally linked observable atoms.
        Scans incoming/outgoing links that connect Fact, Geo, Human,
        Correspondence, or other country-relevant atoms to this Country root.
        """
        self._require_concept()
        observed: Dict[str, Dict[str, Any]] = {}

        incoming_rels = {
            "fact:evidenced_by",
            "fact:involves_organization",
            "fact:involves_geo",
            "fact:involves_human",
            "corr:from",
            "corr:to",
            "country:recognized_by",
            "country:disputed_by",
            "country:claimant",
        }
        outgoing_prefixes = ("fact:", "geo:", "corr:", "human:", "country:")

        for src, rel in self.cortex.get_incoming_links(self.concept_id) or []:
            if rel in incoming_rels and self._visible(src):
                observed[src] = self._summary(src)

        for dst, rel in self.cortex.get_adjacent_links(self.concept_id) or []:
            if not self._visible(dst):
                continue
            if any(rel.startswith(p) for p in outgoing_prefixes):
                observed[dst] = self._summary(dst)

        cap = max(0, int(limit))
        values = list(observed.values())
        return {
            "country_id": self.concept_id,
            "observable": values[:cap],
            "count": min(len(values), cap),
            "total": len(observed),
        }

    def op_diagnose(self, limit: int = 10) -> Dict[str, Any]:
        """Diagnose completeness, evidence quality, and modeling gaps."""
        self._require_concept()

        def summaries(suffix: str) -> List[Dict[str, Any]]:
            return [self._summary(k) for k in self._members(suffix)]

        names           = summaries("names")
        sovereignties   = summaries("sovereignties")
        claims          = summaries("claims")
        administrations = summaries("administrations")
        laws            = summaries("laws")
        law_changes     = summaries("law_changes")
        events          = summaries("events")
        corr_links      = summaries("corr_links")

        all_atoms = (
            names + sovereignties + claims + administrations
            + laws + law_changes + events + corr_links
        )

        unevidenced = [
            a for a in all_atoms
            if not a["meta"].get("source_id") and not a["meta"].get("evidence")
        ]
        low_confidence = [
            a for a in all_atoms
            if float(a["meta"].get("confidence", 1.0)) < 0.4
        ]
        disputed_claims = [
            c for c in claims
            if c["meta"].get("status") == "disputed"
        ]
        open_ended_claims = [
            c for c in claims
            if c["meta"].get("status") == "active"
            and not c["meta"].get("valid_to")
        ]
        laws_without_jurisdiction = [
            law for law in laws
            if not law["meta"].get("jurisdiction_id")
        ]
        administrations_without_corr = [
            adm for adm in administrations
            if not adm["meta"].get("corr_id")
        ]
        events_without_time = [
            ev for ev in events
            if not ev["meta"].get("event_time")
        ]

        return {
            "country_id": self.concept_id,
            "counts": {
                "names":           len(names),
                "sovereignties":   len(sovereignties),
                "claims":          len(claims),
                "administrations": len(administrations),
                "laws":            len(laws),
                "law_changes":     len(law_changes),
                "events":          len(events),
                "corr_links":      len(corr_links),
            },
            "diagnosis": {
                "has_name":           bool(names),
                "has_sovereignty":    bool(sovereignties),
                "has_events":         bool(events),
                "has_correspondence": bool(corr_links),
                "unevidenced_atoms":                    unevidenced[-limit:],
                "low_confidence_atoms":                 low_confidence[-limit:],
                "disputed_claims":                      disputed_claims[-limit:],
                "open_ended_claims":                    open_ended_claims[-limit:],
                "laws_without_jurisdiction":            laws_without_jurisdiction[-limit:],
                "administrations_without_correspondence": administrations_without_corr[-limit:],
                "events_without_time":                  events_without_time[-limit:],
            },
        }

    def op_trace(self, target_id: str = "") -> Dict[str, Any]:
        """
        Trace evidence and graph context for a Country atom.
        If target_id is omitted, traces the active Country root.
        """
        self._require_concept()
        target = target_id or self.concept_id
        self._require_access(target, "Trace target")
        meta = self._meta(target)

        result: Dict[str, Any] = {
            "country_id": self.concept_id,
            "target_id": target,
            "content": self._content(target),
            "meta": meta,
            "evidence": [],
            "outgoing": [],
            "incoming": [],
        }

        source_id = meta.get("source_id")
        if source_id and self._visible(source_id):
            result["evidence"].append({
                "kind": "source_id",
                "atom": self._summary(source_id),
            })
        for ev_id in self._as_list(meta.get("evidence")):
            if self._visible(ev_id):
                result["evidence"].append({
                    "kind": "evidence",
                    "atom": self._summary(ev_id),
                })

        for dst, rel in self.cortex.get_adjacent_links(target) or []:
            if self._visible(dst):
                result["outgoing"].append({"rel": rel, "target": self._summary(dst)})

        for src, rel in self.cortex.get_incoming_links(target) or []:
            if self._visible(src):
                result["incoming"].append({"rel": rel, "source": self._summary(src)})

        return result
