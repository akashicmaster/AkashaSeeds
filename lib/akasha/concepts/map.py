"""
Map Concept Model.
Records how geography was drawn, named, projected, omitted, revised,
and interpreted by a map maker or map edition.
Geo = what exists.
Map = how someone depicted it.
Correspondence = how systems are mapped to each other.
Version: 1.0.0
"""
import time
import logging
from typing import Any, Dict, List, Optional
from lib.akasha.concepts.base import BaseConcept
from lib.akasha.concepts.mixins.temporal import TemporalMixin

logger = logging.getLogger("Harmonia.Concept.Map")

CONTEXT_KEY_ACTIVE = "active_map_root"
INDEX_SET = "set:map:index"
_CONCEPT_WORD_ALIAS_PREFIX = "concept:word:"


SUBSET_TO_RELATION: Dict[str, str] = {
    "editions":     "map:has_edition",
    "features":     "map:has_feature",
    "geometries":   "map:has_geometry",
    "labels":       "map:has_label",
    "projections":  "map:has_projection",
    "groundings":   "map:has_grounding",
    "snapshots":    "map:has_snapshot",
    "transitions":  "map:has_transition",
    "evals":        "map:has_eval",
}


COORDINATE_SYSTEMS = (
    "local_grid", "pixel", "wgs84", "utm", "relative", "symbolic", "other",
)
FEATURE_TYPES = (
    "border", "road", "admin_boundary", "coastline", "settlement",
    "landmark", "annotation", "route", "terrain", "symbolic", "other",
)
GEOMETRY_TYPES = (
    "point", "line", "polygon", "multipoint", "multiline",
    "multipolygon", "raster", "symbolic", "other",
)
STATUS_TYPES = (
    "active", "disputed", "retracted", "superseded", "unverified",
)
TRANSITION_TYPES = (
    "created", "superseded", "revised", "annotated", "translated",
    "derived", "suppressed", "redacted", "restored", "renamed", "other",
)
EVAL_TARGET_TYPES = (
    "edition", "feature", "geometry", "label", "projection", "grounding",
)
SOURCE_KINDS = (
    "map", "atlas", "archive", "official_doc", "survey",
    "fieldnote", "academic_paper", "news_article", "other",
)
PROJECTION_METHODS = (
    "manual", "affine", "georeference", "control_points",
    "rubber_sheet", "llm", "other",
)


class MapConcept(BaseConcept, TemporalMixin):
    """Social-scientific model of cartographic depiction."""

    CONCEPT_PREFIX = "map"
    CONTEXT_KEY_ACTIVE = CONTEXT_KEY_ACTIVE

    TEMPORAL_TYPES = (
        "map_edition",
        "map_snapshot",
        "map_transition",
        "map_eval",
    )
    TEMPORAL_SUBSETS = (
        "editions",
        "snapshots",
        "transitions",
        "evals",
    )

    CONCEPT_METHODS = {
        "new": {"op": "op_new"},
        "open": {
            "op": "op_open",
            "coerce": lambda d: {
                "map_id": d.get("map_id") or d.get("id") or d.get("concept_id", "")
            },
        },
        "ls": {"op": "op_list_all"},
        "map": {"op": "op_show"},
        "show": {"op": "op_show"},
        "rm": {"op": "op_delete"},
        "edition.add": {"op": "op_add_edition"},
        "feature.add": {"op": "op_add_feature"},
        "geometry.add": {"op": "op_add_geometry"},
        "label.add": {"op": "op_add_label"},
        "projection.add": {"op": "op_add_projection"},
        "ground": {"op": "op_ground"},
        "snapshot.add": {"op": "op_add_snapshot"},
        "transition.add": {"op": "op_add_transition"},
        "history": {"op": "op_history"},
        "timeview": {"op": "op_history"},
        "time.rebuild": {"op": "op_time_rebuild"},
        "eval": {"op": "op_eval"},
        "diagnose": {"op": "op_diagnose"},
        "trace": {"op": "op_trace"},
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

    def _map_set(self, suffix: Optional[str] = None) -> str:
        base = f"set:map:{self.concept_id}"
        return f"{base}:{suffix}" if suffix else base

    def _author_and_scopes(self):
        author_id = getattr(self.session, "client_id", "system")
        scopes = [f"owner:user_{author_id}", f"view:user_{author_id}"]
        return author_id, scopes

    def _create_sets(self) -> None:
        self.cortex.create_set(self.set_name)
        self.cortex.create_set(self._map_set())
        for suffix in self.SUBSETS:
            self.cortex.create_set(self._map_set(suffix))
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
                "concept_model": "map",
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
        self.cortex.add_to_set(self._map_set(), key)
        if subset_suffix:
            self.cortex.add_to_set(self._map_set(subset_suffix), key)
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
            key for key in self.cortex.get_collection_members(self._map_set(suffix))
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
        temporal: bool = False,
        occurred_at: str = "",
    ) -> str:
        author_id, scopes = self._author_and_scopes()
        meta = {
            "type": atom_type,
            "concept": "map",
            "created_at": time.time(),
        }
        if temporal:
            meta["occurred_at"] = occurred_at
            meta["time_sort"] = self._normalize_time_sort(occurred_at)
        if meta_extra:
            meta.update(meta_extra)
        key = self.cortex.put_chunk(
            content=content,
            meta=meta,
            author=author_id,
            scopes=scopes,
        )
        self._register(key, subset_suffix=subset, concept_word=concept_word)
        relation = SUBSET_TO_RELATION.get(subset, f"map:has_{subset}")
        self.cortex.put_link(self.concept_id, key, relation, author=author_id)
        if temporal:
            self._append_to_time_index(key, author_id)
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


    def _effective_eval(self, target_id: str) -> Dict[str, Any]:
        latest = None
        latest_time = -1.0
        for eval_id in self._members("evals"):
            meta = self._meta(eval_id)
            if meta.get("target_id") != target_id:
                continue
            created = float(meta.get("created_at", 0))
            if created >= latest_time:
                latest = meta
                latest_time = created
        return latest or {}

    def _effective_confidence(self, atom_id: str) -> float:
        meta = self._meta(atom_id)
        confidence = meta.get("credibility", meta.get("confidence", 0.5))
        eval_meta = self._effective_eval(atom_id)
        updates = eval_meta.get("updates", {})
        if "credibility" in updates:
            confidence = updates["credibility"]
        if "confidence" in updates:
            confidence = updates["confidence"]
        return self._clamp01(confidence, 0.5)

    # ------------------------------------------------------------------
    # Basic operators
    # ------------------------------------------------------------------

    def op_new(self, title: str, description: str = "") -> Dict[str, Any]:
        if not title:
            raise ValueError("map.new requires title.")
        author_id, scopes = self._author_and_scopes()
        root_id = self.cortex.put_chunk(
            content=f"[ Map: {title} ]",
            meta={
                "type": "concept",
                "concept": "map",
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
        self.cortex.add_to_set(self._map_set(), root_id)
        self.cortex.add_to_set(INDEX_SET, root_id)
        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, root_id)
        return {
            "status": "created",
            "concept_id": root_id,
            "map_id": root_id,
            "title": title,
        }

    def op_open(self, map_id: str) -> Dict[str, Any]:
        meta = self._meta(map_id)
        if not meta or meta.get("concept") != "map":
            raise RuntimeError(f"Atom '{map_id[:12]}' is not a map root.")
        if not self._visible(map_id):
            raise RuntimeError(f"Map not accessible: {map_id[:12]}")
        self.concept_id = map_id
        self.set_name = f"set:concept:{self.concept_id}"
        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, map_id)
        return {
            "status": "opened",
            "concept_id": map_id,
            "map_id": map_id,
            "title": meta.get("title", ""),
        }

    def op_list_all(self) -> Dict[str, Any]:
        maps = []
        for key in self.cortex.get_collection_members(INDEX_SET):
            if not self._visible(key):
                continue
            meta = self._meta(key)
            if meta.get("concept") != "map":
                continue
            maps.append({
                "map_id": key,
                "concept_id": key,
                "title": meta.get("title", ""),
                "created_at": meta.get("created_at", 0),
            })
        maps.sort(key=lambda x: x.get("created_at", 0), reverse=True)
        return {"maps": maps, "count": len(maps)}

    def op_delete(self) -> Dict[str, Any]:
        self._require_concept()
        target = self.concept_id
        try:
            self.cortex.remove_from_set(INDEX_SET, target)
        except Exception:
            pass
        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, None)
        self.concept_id = None
        return {"status": "soft_deleted", "map_id": target}

    # ------------------------------------------------------------------
    # Core atoms
    # ------------------------------------------------------------------

    def op_add_edition(
        self,
        title: str,
        maker: str = "",
        publisher: str = "",
        created_at: str = "",
        projection: str = "",
        scale: str = "",
        coordinate_system: str = "symbolic",
        purpose: str = "",
        purpose_tags: Optional[List[str]] = None,
        quelle_level: int = 2,
        independence: float = 0.5,
        credibility: float = 0.5,
        bias: str = "unknown",
        bias_tags: Optional[List[str]] = None,
        motivation: str = "",
        source_kind: str = "map",
        status: str = "active",
        note: str = "",
    ) -> Dict[str, Any]:
        self._require_concept()
        if not title:
            raise ValueError("edition title is required.")
        if coordinate_system not in COORDINATE_SYSTEMS:
            raise ValueError(f"coordinate_system must be one of {COORDINATE_SYSTEMS}.")
        if source_kind not in SOURCE_KINDS:
            raise ValueError(f"source_kind must be one of {SOURCE_KINDS}.")
        if status not in STATUS_TYPES:
            raise ValueError(f"status must be one of {STATUS_TYPES}.")
        if not (1 <= int(quelle_level) <= 5):
            raise ValueError("quelle_level must be between 1 and 5.")
        key = self._put_atom(
            content=note or f"[MapEdition] {title}",
            atom_type="map_edition",
            subset="editions",
            meta_extra={
                "role": "edition",
                "title": title,
                "maker": maker,
                "publisher": publisher,
                "created_at_label": created_at,
                "projection": projection,
                "scale": scale,
                "coordinate_system": coordinate_system,
                "purpose": purpose,
                "purpose_tags": purpose_tags or [],
                "quelle_level": int(quelle_level),
                "independence": self._clamp01(independence, 0.5),
                "credibility": self._clamp01(credibility, 0.5),
                "bias": bias,
                "bias_tags": bias_tags or [],
                "motivation": motivation,
                "source_kind": source_kind,
                "status": status,
            },
            concept_word="edition",
            temporal=True,
            occurred_at=created_at,
        )
        return {
            "status": "edition_added",
            "edition_id": key,
            "title": title,
            "credibility": self._clamp01(credibility, 0.5),
        }

    def op_add_feature(
        self,
        edition_id: str,
        name: str,
        feature_type: str = "other",
        description: str = "",
        source_id: str = "",
        confidence: float = 0.7,
        status: str = "active",
        feature_state: str = "visible",
        properties: Optional[Dict[str, Any]] = None,
        note: str = "",
    ) -> Dict[str, Any]:
        self._require_concept()
        self._require_access(edition_id, "MapEdition")
        if source_id:
            self._require_access(source_id, "Source")
        if feature_type not in FEATURE_TYPES:
            raise ValueError(f"feature_type must be one of {FEATURE_TYPES}.")
        if status not in STATUS_TYPES:
            raise ValueError(f"status must be one of {STATUS_TYPES}.")
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=note or name,
            atom_type="map_feature",
            subset="features",
            meta_extra={
                "role": "feature",
                "edition_id": edition_id,
                "name": name,
                "feature_type": feature_type,
                "description": description,
                "source_id": source_id or None,
                "confidence": self._clamp01(confidence, 0.7),
                "status": status,
                "feature_state": feature_state,
                "properties": properties or {},
            },
            concept_word="feature",
        )
        self.cortex.put_link(edition_id, key, "map:depicts_feature", author=author_id)
        if source_id:
            self.cortex.put_link(key, source_id, "map:evidenced_by", author=author_id)
        return {
            "status": "feature_added",
            "feature_id": key,
            "edition_id": edition_id,
            "feature_type": feature_type,
        }

    def op_add_geometry(
        self,
        feature_id: str,
        geometry_type: str,
        coordinates: Any,
        coordinate_system: str = "",
        precision: str = "",
        extracted_by: str = "human",
        source_id: str = "",
        confidence: float = 0.7,
        status: str = "active",
        note: str = "",
    ) -> Dict[str, Any]:
        self._require_concept()
        self._require_access(feature_id, "MapFeature")
        if source_id:
            self._require_access(source_id, "Source")
        if geometry_type not in GEOMETRY_TYPES:
            raise ValueError(f"geometry_type must be one of {GEOMETRY_TYPES}.")
        if coordinate_system and coordinate_system not in COORDINATE_SYSTEMS:
            raise ValueError(f"coordinate_system must be one of {COORDINATE_SYSTEMS}.")
        if status not in STATUS_TYPES:
            raise ValueError(f"status must be one of {STATUS_TYPES}.")
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=note or f"geometry:{geometry_type}:{feature_id[:12]}",
            atom_type="map_geometry",
            subset="geometries",
            meta_extra={
                "role": "geometry",
                "feature_id": feature_id,
                "geometry_type": geometry_type,
                "coordinates": coordinates,
                "coordinate_system": coordinate_system,
                "precision": precision,
                "extracted_by": extracted_by,
                "source_id": source_id or None,
                "confidence": self._clamp01(confidence, 0.7),
                "status": status,
            },
            concept_word="geometry",
        )
        self.cortex.put_link(feature_id, key, "map:has_geometry", author=author_id)
        if source_id:
            self.cortex.put_link(key, source_id, "map:evidenced_by", author=author_id)
        return {
            "status": "geometry_added",
            "geometry_id": key,
            "feature_id": feature_id,
            "geometry_type": geometry_type,
        }

    def op_add_label(
        self,
        edition_id: str,
        target_id: str,
        text: str,
        language: str = "",
        script: str = "",
        romanization: str = "",
        transliteration_system: str = "",
        source_id: str = "",
        confidence: float = 0.7,
        status: str = "active",
        note: str = "",
    ) -> Dict[str, Any]:
        self._require_concept()
        self._require_access(edition_id, "MapEdition")
        self._require_access(target_id, "Label target")
        if source_id:
            self._require_access(source_id, "Source")
        if not text:
            raise ValueError("label text is required.")
        if status not in STATUS_TYPES:
            raise ValueError(f"status must be one of {STATUS_TYPES}.")
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=note or text,
            atom_type="map_label",
            subset="labels",
            meta_extra={
                "role": "label",
                "edition_id": edition_id,
                "target_id": target_id,
                "text": text,
                "language": language,
                "script": script,
                "romanization": romanization,
                "transliteration_system": transliteration_system,
                "source_id": source_id or None,
                "confidence": self._clamp01(confidence, 0.7),
                "status": status,
            },
            concept_word="label",
        )
        self.cortex.put_link(edition_id, key, "map:uses_label", author=author_id)
        self.cortex.put_link(key, target_id, "map:labels", author=author_id)
        if source_id:
            self.cortex.put_link(key, source_id, "map:evidenced_by", author=author_id)
        return {
            "status": "label_added",
            "label_id": key,
            "target_id": target_id,
            "text": text,
        }

    def op_add_projection(
        self,
        edition_id: str,
        target_system: str,
        method: str = "manual",
        source_system: str = "",
        matrix: Optional[List[List[float]]] = None,
        offset: Optional[List[float]] = None,
        control_points: Optional[List[Dict[str, Any]]] = None,
        source_id: str = "",
        confidence: float = 0.7,
        status: str = "active",
        note: str = "",
    ) -> Dict[str, Any]:
        self._require_concept()
        self._require_access(edition_id, "MapEdition")
        if source_id:
            self._require_access(source_id, "Source")
        if method not in PROJECTION_METHODS:
            raise ValueError(f"method must be one of {PROJECTION_METHODS}.")
        if status not in STATUS_TYPES:
            raise ValueError(f"status must be one of {STATUS_TYPES}.")
        author_id, _ = self._author_and_scopes()
        edition_meta = self._meta(edition_id)
        source_system = source_system or edition_meta.get("coordinate_system", "")
        key = self._put_atom(
            content=note or f"projection:{source_system}->{target_system}",
            atom_type="map_projection",
            subset="projections",
            meta_extra={
                "role": "projection",
                "edition_id": edition_id,
                "source_system": source_system,
                "target_system": target_system,
                "method": method,
                "matrix": matrix or [],
                "offset": offset or [],
                "control_points": control_points or [],
                "source_id": source_id or None,
                "confidence": self._clamp01(confidence, 0.7),
                "status": status,
            },
            concept_word="projection",
        )
        self.cortex.put_link(edition_id, key, "map:projected_by", author=author_id)
        if source_id:
            self.cortex.put_link(key, source_id, "map:evidenced_by", author=author_id)
        return {
            "status": "projection_added",
            "projection_id": key,
            "edition_id": edition_id,
            "source_system": source_system,
            "target_system": target_system,
        }

    def op_ground(
        self,
        src_id: str,
        dst_id: str,
        relation: str = "grounds",
        source_id: str = "",
        confidence: float = 0.7,
        status: str = "active",
        context: str = "",
        note: str = "",
    ) -> Dict[str, Any]:
        """
        Record a map-local grounding claim.
        This does not replace CorrespondenceConcept. It creates an auditable
        local grounding atom and also emits corr:* style links so CorrConcept
        or later curation can consume the relationship.
        """
        self._require_concept()
        self._require_access(src_id, "Source map atom")
        self._require_access(dst_id, "Destination atom")
        if source_id:
            self._require_access(source_id, "Evidence source")
        if status not in STATUS_TYPES:
            raise ValueError(f"status must be one of {STATUS_TYPES}.")
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=note or f"grounding:{src_id[:12]}->{dst_id[:12]}",
            atom_type="map_grounding",
            subset="groundings",
            meta_extra={
                "role": "grounding",
                "src_id": src_id,
                "dst_id": dst_id,
                "relation": relation,
                "source_id": source_id or None,
                "confidence": self._clamp01(confidence, 0.7),
                "status": status,
                "context": context,
            },
            concept_word="grounding",
        )
        self.cortex.put_link(key, src_id, "corr:from", author=author_id)
        self.cortex.put_link(key, dst_id, "corr:to", author=author_id)
        self.cortex.put_link(src_id, dst_id, f"corr:{relation}", author=author_id)
        if source_id:
            self.cortex.put_link(key, source_id, "corr:evidenced_by", author=author_id)
            self.cortex.put_link(key, source_id, "map:evidenced_by", author=author_id)
        return {
            "status": "grounding_added",
            "grounding_id": key,
            "src_id": src_id,
            "dst_id": dst_id,
            "relation": relation,
        }

    # ------------------------------------------------------------------
    # Temporal / transitions
    # ------------------------------------------------------------------

    def op_add_snapshot(
        self,
        label: str,
        captured_at: str = "",
        members: Optional[List[str]] = None,
        source_id: str = "",
        note: str = "",
    ) -> Dict[str, Any]:
        self._require_concept()
        if not label:
            raise ValueError("snapshot label is required.")
        for member in self._as_list(members):
            self._require_access(member, "Snapshot member")
        if source_id:
            self._require_access(source_id, "Source")
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=note or label,
            atom_type="map_snapshot",
            subset="snapshots",
            meta_extra={
                "role": "snapshot",
                "label": label,
                "captured_at": captured_at,
                "members": members or [],
                "source_id": source_id or None,
            },
            concept_word="snapshot",
            temporal=True,
            occurred_at=captured_at,
        )
        for member in self._as_list(members):
            self.cortex.put_link(key, member, "map:includes", author=author_id)
        if source_id:
            self.cortex.put_link(key, source_id, "map:evidenced_by", author=author_id)
        return {"status": "snapshot_added", "snapshot_id": key, "label": label}

    def op_add_transition(
        self,
        target_id: str,
        transition_type: str,
        description: str,
        event_id: str = "",
        from_state: str = "",
        to_state: str = "",
        occurred_at: str = "",
        evidence: Optional[List[str]] = None,
        confidence: float = 0.7,
    ) -> Dict[str, Any]:
        self._require_concept()
        self._require_access(target_id, "Transition target")
        if event_id:
            self._require_access(event_id, "Event")
        for ev in self._as_list(evidence):
            self._require_access(ev, "Evidence")
        if transition_type not in TRANSITION_TYPES:
            raise ValueError(f"transition_type must be one of {TRANSITION_TYPES}.")
        if not description:
            raise ValueError("transition description is required.")
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=description,
            atom_type="map_transition",
            subset="transitions",
            meta_extra={
                "role": "transition",
                "target_id": target_id,
                "transition_type": transition_type,
                "event_id": event_id or None,
                "from_state": from_state,
                "to_state": to_state,
                "evidence": evidence or [],
                "confidence": self._clamp01(confidence, 0.7),
            },
            concept_word="transition",
            temporal=True,
            occurred_at=occurred_at,
        )
        self.cortex.put_link(target_id, key, "map:changed_by", author=author_id)
        self.cortex.put_link(target_id, key, f"map:{transition_type}_by", author=author_id)
        if event_id:
            self.cortex.put_link(key, event_id, "map:caused_by", author=author_id)
        for ev in self._as_list(evidence):
            self.cortex.put_link(key, ev, "map:evidenced_by", author=author_id)
        return {
            "status": "transition_added",
            "transition_id": key,
            "target_id": target_id,
            "transition_type": transition_type,
        }

    def op_history(
        self,
        limit: int = 100,
        atom_types: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        self._require_concept()
        effective_types = list(atom_types) if atom_types else list(self.TEMPORAL_TYPES)
        history = self._walk_time_index(limit=limit, atom_types=effective_types)
        return {"map_id": self.concept_id, "history": history, "count": len(history)}

    def op_time_rebuild(self) -> Dict[str, Any]:
        self._require_concept()
        author_id, _ = self._author_and_scopes()
        result = self._rebuild_time_index(author_id)
        return {"status": "time_rebuilt", "map_id": self.concept_id, "count": result["count"]}

    # ------------------------------------------------------------------
    # Evaluation / trace / diagnose
    # ------------------------------------------------------------------

    def op_eval(
        self,
        target_id: str,
        target_type: str = "",
        confidence: Optional[float] = None,
        credibility: Optional[float] = None,
        status: str = "",
        bias: str = "",
        bias_tags: Optional[List[str]] = None,
        note: str = "",
    ) -> Dict[str, Any]:
        self._require_concept()
        self._require_access(target_id, "Evaluation target")
        if target_type and target_type not in EVAL_TARGET_TYPES:
            raise ValueError(f"target_type must be one of {EVAL_TARGET_TYPES}.")
        if status and status not in STATUS_TYPES:
            raise ValueError(f"status must be one of {STATUS_TYPES}.")
        author_id, _ = self._author_and_scopes()
        updates: Dict[str, Any] = {}
        if confidence is not None:
            updates["confidence"] = self._clamp01(confidence)
        if credibility is not None:
            updates["credibility"] = self._clamp01(credibility)
        if status:
            updates["status"] = status
        if bias:
            updates["bias"] = bias
        if bias_tags is not None:
            updates["bias_tags"] = bias_tags
        key = self._put_atom(
            content=note or f"eval:{target_id[:12]}",
            atom_type="map_eval",
            subset="evals",
            meta_extra={
                "role": "eval",
                "target_id": target_id,
                "target_type": target_type,
                "updates": updates,
            },
            concept_word="eval",
            temporal=True,
            occurred_at="",
        )
        self.cortex.put_link(target_id, key, "map:evaluated_by", author=author_id)
        return {"status": "evaluated", "eval_id": key, "target_id": target_id, "updates": updates}

    def op_trace(self, target_id: str) -> Dict[str, Any]:
        self._require_concept()
        self._require_access(target_id, "Trace target")
        meta = self._meta(target_id)
        eval_meta = self._effective_eval(target_id)
        evidence = []
        for dst, rel in self.cortex.get_adjacent_links(target_id) or []:
            if rel in ("map:evidenced_by", "corr:evidenced_by") and self._visible(dst):
                evidence.append(self._summary(dst))
        transitions = []
        for dst, rel in self.cortex.get_adjacent_links(target_id) or []:
            if rel.startswith("map:") and rel.endswith("_by") and self._visible(dst):
                transitions.append(self._summary(dst))
        return {
            "target_id": target_id,
            "content": self._content(target_id),
            "meta": meta,
            "effective_confidence": self._effective_confidence(target_id),
            "latest_eval": eval_meta,
            "evidence": evidence,
            "transitions": transitions,
        }

    def op_show(self) -> Dict[str, Any]:
        self._require_concept()
        meta = self._meta(self.concept_id)
        return {
            "map_id": self.concept_id,
            "concept_id": self.concept_id,
            "title": meta.get("title", ""),
            **{suffix: self._members(suffix) for suffix in self.SUBSETS},
        }

    def op_diagnose(self, limit: int = 10) -> Dict[str, Any]:
        self._require_concept()
        editions = [self._summary(k) for k in self._members("editions")]
        features = [self._summary(k) for k in self._members("features")]
        geometries = [self._summary(k) for k in self._members("geometries")]
        labels = [self._summary(k) for k in self._members("labels")]
        projections = [self._summary(k) for k in self._members("projections")]
        groundings = [self._summary(k) for k in self._members("groundings")]
        transitions = [self._summary(k) for k in self._members("transitions")]

        edition_ids = {e["id"] for e in editions}
        feature_ids = {f["id"] for f in features}
        geometry_feature_ids = {
            g["meta"].get("feature_id") for g in geometries
        }

        editions_without_provenance = [
            e for e in editions
            if not e["meta"].get("maker")
            or e["meta"].get("credibility") is None
        ]
        features_without_geometry = [
            f for f in features
            if f["id"] not in geometry_feature_ids
        ]
        features_not_grounded = [
            f for f in features
            if not any(g["meta"].get("src_id") == f["id"] for g in groundings)
        ]
        labels_without_target = [
            lbl for lbl in labels
            if not lbl["meta"].get("target_id")
            or not self._visible(lbl["meta"].get("target_id", ""))
        ]
        low_confidence_features = [
            f for f in features
            if self._effective_confidence(f["id"]) < 0.4
        ]
        projection_without_grounding = [
            e for e in editions
            if e["meta"].get("coordinate_system") not in ("symbolic", "other", "")
            and not any(p["meta"].get("edition_id") == e["id"] for p in projections)
        ]

        multiple_conflicting_groundings = []
        grounding_by_src: Dict[str, List[Dict[str, Any]]] = {}
        for g in groundings:
            grounding_by_src.setdefault(g["meta"].get("src_id", ""), []).append(g)
        for src, items in grounding_by_src.items():
            dsts = {x["meta"].get("dst_id") for x in items}
            if src and len(dsts) > 1:
                multiple_conflicting_groundings.extend(items)

        conflicting_labels = []
        labels_by_target: Dict[str, List[Dict[str, Any]]] = {}
        for lbl in labels:
            labels_by_target.setdefault(lbl["meta"].get("target_id", ""), []).append(lbl)
        for target, items in labels_by_target.items():
            texts = {x["meta"].get("text") for x in items}
            if target and len(texts) > 1:
                conflicting_labels.extend(items)

        suppressed_features = [
            f for f in features
            if f["meta"].get("feature_state") in ("suppressed", "redacted", "omitted")
        ]
        orphan_geometries = [
            g for g in geometries
            if g["meta"].get("feature_id") not in feature_ids
        ]
        editions_missing_projection_metadata = [
            e for e in editions
            if not e["meta"].get("projection")
            and e["meta"].get("coordinate_system") not in ("symbolic", "other")
        ]
        transitions_without_target = [
            t for t in transitions
            if not t["meta"].get("target_id")
            or not self._visible(t["meta"].get("target_id", ""))
        ]

        return {
            "map_id": self.concept_id,
            "counts": {
                "editions": len(editions),
                "features": len(features),
                "geometries": len(geometries),
                "labels": len(labels),
                "projections": len(projections),
                "groundings": len(groundings),
                "transitions": len(transitions),
            },
            "diagnosis": {
                "editions_without_provenance": editions_without_provenance[-limit:],
                "features_without_geometry": features_without_geometry[-limit:],
                "features_not_grounded": features_not_grounded[-limit:],
                "labels_without_target": labels_without_target[-limit:],
                "conflicting_labels": conflicting_labels[-limit:],
                "low_confidence_features": low_confidence_features[-limit:],
                "projection_without_grounding": projection_without_grounding[-limit:],
                "multiple_conflicting_groundings": multiple_conflicting_groundings[-limit:],
                "suppressed_features": suppressed_features[-limit:],
                "orphan_geometries": orphan_geometries[-limit:],
                "editions_missing_projection_metadata": editions_missing_projection_metadata[-limit:],
                "transitions_without_target": transitions_without_target[-limit:],
                "has_projection": bool(projections),
                "has_transition_history": bool(transitions),
            },
        }
