"""
Geo Concept Model.
Models grounded spatial knowledge:
coordinates, places, features, observations, events, layers, snapshots,
connections, affine transforms, place clones, and transitions.
"""
import time
import logging
from typing import Any, Dict, List, Optional
from lib.akasha.concepts.base import BaseConcept
from lib.akasha.concepts.mixins.temporal import TemporalMixin
from lib.akasha.concepts.mixins.visibility import VisibilityMixin
from lib.akasha.graph.query import GraphQueryEngine

logger = logging.getLogger("Harmonia.Concept.Geo")

CONTEXT_KEY_ACTIVE = "active_geo_root"
INDEX_SET = "set:geo:index"
_CONCEPT_WORD_ALIAS_PREFIX = "concept:word:"

SUBSET_TO_RELATION: Dict[str, str] = {
    "coordinates":  "geo:has_coordinate",
    "places":       "geo:has_place",
    "features":     "geo:has_feature",
    "observations": "geo:has_observation",
    "events":       "geo:has_event",
    "layers":       "geo:has_layer",
    "snapshots":    "geo:has_snapshot",
    "states":       "geo:has_state",
    "connections":  "geo:has_connection",
    "affines":      "geo:has_affine",
    "clones":       "geo:has_clone",
    "transitions":  "geo:has_transition",
}

COORDINATE_SYSTEMS = (
    "wgs84",
    "local_grid",
    "utm",
    "pixel",
    "relative",
    "symbolic",
    "other",
)

PLACE_TYPES = (
    "site",
    "region",
    "building",
    "room",
    "road",
    "boundary",
    "landmark",
    "zone",
    "world_place",
    "other",
)

FEATURE_TYPES = (
    "natural",
    "built",
    "archaeological",
    "political",
    "ecological",
    "infrastructure",
    "symbolic",
    "hidden",
    "other",
)

OBSERVATION_METHODS = (
    "human",
    "sensor",
    "survey",
    "satellite",
    "map",
    "fieldnote",
    "llm",
    "other",
)

CONNECTION_TYPES = (
    "adjacent_to",
    "contains",
    "overlaps",
    "near",
    "route",
    "boundary",
    "visible_from",
    "accessible_from",
    "symbolically_linked",
    "other",
)

TRANSITION_TYPES = (
    "created",
    "destroyed",
    "moved",
    "renamed",
    "merged",
    "split",
    "revealed",
    "hidden",
    "state_changed",
    "other",
)


DEFAULT_NEARBY_RELS = (
    "geo:adjacent_to",
    "geo:near",
    "geo:route",
    "geo:accessible_from",
    "geo:visible_from",
    "geo:contains",
    "sys:part_of",
    "geo:overlaps",
)

DEFAULT_PATH_RELS = (
    "geo:adjacent_to",
    "geo:near",
    "geo:route",
    "geo:accessible_from",
    "geo:contains",
    "sys:part_of",
)


class GeoConcept(VisibilityMixin, BaseConcept, TemporalMixin):
    """Spatial / geographic concept model."""

    CONCEPT_PREFIX = "geo"
    CONTEXT_KEY_ACTIVE = CONTEXT_KEY_ACTIVE

    TEMPORAL_TYPES = (
        "geo_event",
        "geo_transition",
        "geo_place_state",
        "geo_observation",
        "geo_snapshot",
    )
    TEMPORAL_SUBSETS = (
        "events",
        "transitions",
        "states",
        "observations",
        "snapshots",
    )

    CONCEPT_METHODS = {
        "new":  {"op": "op_new"},
        "open": {
            "op": "op_open",
            "coerce": lambda d: {
                "geo_id": d.get("geo_id") or d.get("concept_id") or d.get("id", "")
            },
        },
        "ls":   {"op": "op_list_all"},
        "map":  {"op": "op_map"},
        "rm":   {"op": "op_delete"},
        "coord.add":    {"op": "op_add_coordinate"},
        "place.add":    {"op": "op_add_place"},
        "place.state":  {"op": "op_set_place_state"},
        "feature.add":  {"op": "op_add_feature"},
        "observe.add":  {"op": "op_add_observation"},
        "event.add":    {"op": "op_add_event"},
        "layer.add":    {"op": "op_add_layer"},
        "snapshot.add": {"op": "op_add_snapshot"},
        "connect":        {"op": "op_connect"},
        "affine.add":     {"op": "op_add_affine"},
        "clone":          {"op": "op_clone_place"},
        "transition.add": {"op": "op_add_transition"},
        "nearby":         {"op": "op_nearby"},
        "path":           {"op": "op_path"},
        "reveal":         {"op": "op_reveal"},
        "diagnose":       {"op": "op_diagnose"},
        "history":        {"op": "op_history"},
        "timeview":       {"op": "op_history"},   # alias
        "time.rebuild":   {"op": "op_time_rebuild"},
        # Future — coordinate transform execution:
        # "analyze": {"op": "op_analyze"},
    }

    SUBSETS = list(SUBSET_TO_RELATION.keys())  # evaluated after all SUBSET_TO_RELATION entries are added

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

    def _geo_set(self, suffix: Optional[str] = None) -> str:
        base = f"set:geo:{self.concept_id}"
        return f"{base}:{suffix}" if suffix else base

    def _author_and_scopes(self):
        author_id = getattr(self.session, "client_id", "system")
        scopes = [f"owner:user_{author_id}", f"view:user_{author_id}"]
        return author_id, scopes

    def _create_sets(self) -> None:
        self.ensure_concept_set()
        self.cortex.create_set(self._geo_set())
        for suffix in self.SUBSETS:
            self.cortex.create_set(self._geo_set(suffix))
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
                "concept_model": "geo",
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
        self.cortex.add_to_set(self._geo_set(), key)
        if subset_suffix:
            self.cortex.add_to_set(self._geo_set(subset_suffix), key)
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
        return self._visible_semantic(atom_id)

    def _visible_geo(self, atom_id: str, include_hidden: bool = False) -> bool:
        return self._visible_semantic(
            atom_id,
            include_hidden=include_hidden,
            include_archived=True,
            include_tombstoned=False,
        )

    def _members(self, suffix: str) -> List[str]:
        return [
            key for key in self.cortex.get_collection_members(self._geo_set(suffix))
            if self._base_access_visible(key)
        ]

    def _meta(self, key: str) -> Dict[str, Any]:
        return self.cortex.get_meta(key) or {}

    def _content(self, key: str) -> str:
        return self.cortex.get_chunk(key) or ""

    def _summary(self, key: str) -> Dict[str, Any]:
        return {"id": key, "meta": self._meta(key), "content": self._content(key)}

    def _graph(self) -> GraphQueryEngine:
        """Return a GraphQueryEngine bound to this concept's cortex and visibility rules."""
        return GraphQueryEngine(
            cortex=self.cortex,
            visible_fn=self._visible_geo,
            meta_fn=self._meta,
            content_fn=self._content,
        )

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
            "concept": "geo",
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
        rel = SUBSET_TO_RELATION.get(subset, f"geo:has_{subset}")
        self.cortex.put_link(self.concept_id, key, rel, author=author_id)
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
        title: str,
        description: str = "",
        coordinate_system: str = "wgs84",
    ) -> Dict[str, Any]:
        if not title:
            raise ValueError("geo.new requires title.")
        if coordinate_system not in COORDINATE_SYSTEMS:
            raise ValueError(f"coordinate_system must be one of {COORDINATE_SYSTEMS}.")
        author_id, scopes = self._author_and_scopes()
        root_id = self.cortex.put_chunk(
            content=f"[ Geo: {title} ]",
            meta={
                "type": "concept",
                "concept": "geo",
                "role": "root",
                "title": title,
                "description": description,
                "coordinate_system": coordinate_system,
                "created_at": time.time(),
            },
            author=author_id,
            scopes=scopes,
        )
        self.concept_id = root_id
        self.set_name = f"set:concept:{self.concept_id}"
        self._create_sets()
        self.cortex.add_to_set(self._geo_set(), root_id)
        self.cortex.add_to_set(INDEX_SET, root_id)
        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, root_id)
        return {
            "status": "created",
            "concept_id": root_id,
            "geo_id": root_id,
            "title": title,
            "coordinate_system": coordinate_system,
        }

    def op_open(self, geo_id: str) -> Dict[str, Any]:
        meta = self._meta(geo_id)
        if not meta or meta.get("concept") != "geo":
            raise RuntimeError(f"Atom '{geo_id[:12]}' is not a geo root.")
        if not self._visible(geo_id):
            raise RuntimeError(f"Geo not accessible: {geo_id[:12]}")
        self.concept_id = geo_id
        self.set_name = f"set:concept:{self.concept_id}"
        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, geo_id)
        return {
            "status": "opened",
            "concept_id": geo_id,
            "geo_id": geo_id,
            "title": meta.get("title", ""),
            "coordinate_system": meta.get("coordinate_system", ""),
        }

    def op_list_all(self) -> Dict[str, Any]:
        geos = []
        for key in self.cortex.get_collection_members(INDEX_SET):
            if not self._visible(key):
                continue
            meta = self._meta(key)
            if meta.get("concept") != "geo":
                continue
            geos.append({
                "geo_id": key,
                "concept_id": key,
                "title": meta.get("title", ""),
                "coordinate_system": meta.get("coordinate_system", ""),
                "created_at": meta.get("created_at", 0),
            })
        geos.sort(key=lambda x: x.get("created_at", 0), reverse=True)
        return {"geos": geos, "count": len(geos)}

    def op_delete(self) -> Dict[str, Any]:
        self._require_concept()
        target = self.concept_id
        self.cortex.remove_from_set(INDEX_SET, target)
        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, None)
        self.concept_id = None
        return {"status": "deleted", "geo_id": target}

    # ------------------------------------------------------------------
    # Core spatial atoms
    # ------------------------------------------------------------------

    def op_add_coordinate(
        self,
        label: str = "",
        system: str = "wgs84",
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        alt: Optional[float] = None,
        x: Optional[float] = None,
        y: Optional[float] = None,
        z: Optional[float] = None,
        precision: str = "",
        source_id: str = "",
        confidence: float = 0.8,
        note: str = "",
    ) -> Dict[str, Any]:
        self._require_concept()
        if system not in COORDINATE_SYSTEMS:
            raise ValueError(f"system must be one of {COORDINATE_SYSTEMS}.")
        if source_id:
            self._require_access(source_id, "Coordinate source")
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=note or label or f"coordinate:{system}",
            atom_type="geo_coordinate",
            subset="coordinates",
            meta_extra={
                "role": "coordinate",
                "label": label,
                "system": system,
                "lat": lat,
                "lon": lon,
                "alt": alt,
                "x": x,
                "y": y,
                "z": z,
                "precision": precision,
                "source_id": source_id or None,
                "confidence": self._clamp01(confidence, 0.8),
            },
            concept_word="coordinate",
        )
        if source_id:
            self.cortex.put_link(key, source_id, "geo:evidenced_by", author=author_id)
        return {"status": "coordinate_added", "coordinate_id": key}

    def op_add_place(
        self,
        name: str,
        place_type: str = "site",
        coordinate_id: str = "",
        parent_place_id: str = "",
        description: str = "",
        source_id: str = "",
        confidence: float = 0.8,
        hidden: bool = False,
    ) -> Dict[str, Any]:
        self._require_concept()
        if not name:
            raise ValueError("place name is required.")
        if place_type not in PLACE_TYPES:
            raise ValueError(f"place_type must be one of {PLACE_TYPES}.")
        if coordinate_id:
            self._require_access(coordinate_id, "Coordinate")
        if parent_place_id:
            self._require_access(parent_place_id, "Parent place")
        if source_id:
            self._require_access(source_id, "Place source")
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=description or name,
            atom_type="geo_place",
            subset="places",
            meta_extra={
                "role": "place",
                "name": name,
                "place_type": place_type,
                "coordinate_id": coordinate_id or None,
                "parent_place_id": parent_place_id or None,
                "source_id": source_id or None,
                "confidence": self._clamp01(confidence, 0.8),
                "hidden": bool(hidden),
            },
            concept_word="place",
        )
        if coordinate_id:
            self.cortex.put_link(key, coordinate_id, "geo:located_at", author=author_id)
        if parent_place_id:
            self.cortex.put_link(parent_place_id, key, "sys:contains", author=author_id)
            self.cortex.put_link(key, parent_place_id, "sys:part_of", author=author_id)
        if source_id:
            self.cortex.put_link(key, source_id, "geo:evidenced_by", author=author_id)
        return {"status": "place_added", "place_id": key, "name": name}

    def op_set_place_state(
        self,
        place_id: str,
        state: str,
        event_id: str = "",
        occurred_at: str = "",
        intensity: float = 0.5,
        note: str = "",
    ) -> Dict[str, Any]:
        """
        Explicitly record Place.State.
        Manual in v1: geo.event.add records the cause, geo.place.state records the effect.
        """
        self._require_concept()
        self._require_access(place_id, "Place")
        if event_id:
            self._require_access(event_id, "State event")
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=note or state,
            atom_type="geo_place_state",
            subset="states",
            meta_extra={
                "role": "place_state",
                "place_id": place_id,
                "state": state,
                "event_id": event_id or None,
                "occurred_at": occurred_at,
                "time_sort": self._normalize_time_sort(occurred_at),
                "intensity": self._clamp01(intensity, 0.5),
            },
            concept_word="state",
        )
        self.cortex.put_link(place_id, key, "geo:has_state", author=author_id)
        if event_id:
            self.cortex.put_link(key, event_id, "geo:caused_by", author=author_id)
        self._append_to_time_index(key, author_id)
        return {
            "status": "place_state_set",
            "state_id": key,
            "place_id": place_id,
            "state": state,
        }

    def op_add_feature(
        self,
        place_id: str,
        name: str,
        feature_type: str = "other",
        description: str = "",
        source_id: str = "",
        confidence: float = 0.7,
        properties: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        self._require_concept()
        self._require_access(place_id, "Place")
        if feature_type not in FEATURE_TYPES:
            raise ValueError(f"feature_type must be one of {FEATURE_TYPES}.")
        if source_id:
            self._require_access(source_id, "Feature source")
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=description or name,
            atom_type="geo_feature",
            subset="features",
            meta_extra={
                "role": "feature",
                "place_id": place_id,
                "name": name,
                "feature_type": feature_type,
                "source_id": source_id or None,
                "confidence": self._clamp01(confidence, 0.7),
                "properties": properties or {},
            },
            concept_word="feature",
        )
        self.cortex.put_link(place_id, key, "geo:has_feature", author=author_id)
        if source_id:
            self.cortex.put_link(key, source_id, "geo:evidenced_by", author=author_id)
        return {"status": "feature_added", "feature_id": key, "place_id": place_id}

    def op_add_observation(
        self,
        target_id: str,
        text: str,
        method: str = "human",
        observer: str = "",
        observed_at: str = "",
        source_id: str = "",
        confidence: float = 0.7,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        self._require_concept()
        self._require_access(target_id, "Observation target")
        if method not in OBSERVATION_METHODS:
            raise ValueError(f"method must be one of {OBSERVATION_METHODS}.")
        if source_id:
            self._require_access(source_id, "Observation source")
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=text,
            atom_type="geo_observation",
            subset="observations",
            meta_extra={
                "role": "observation",
                "target_id": target_id,
                "method": method,
                "observer": observer,
                "observed_at": observed_at,
                "occurred_at": observed_at,
                "time_sort": self._normalize_time_sort(observed_at),
                "source_id": source_id or None,
                "confidence": self._clamp01(confidence, 0.7),
                "data": data or {},
            },
            concept_word="observation",
        )
        self.cortex.put_link(key, target_id, "geo:observes", author=author_id)
        self.cortex.put_link(target_id, key, "geo:observed_by", author=author_id)
        if source_id:
            self.cortex.put_link(key, source_id, "geo:evidenced_by", author=author_id)
        self._append_to_time_index(key, author_id)
        return {"status": "observation_added", "observation_id": key}

    def op_add_event(
        self,
        description: str,
        place_id: str = "",
        event_time: str = "",
        intensity: float = 0.5,
        event_type: str = "event",
        source_id: str = "",
        affects: Optional[List[str]] = None,
        confidence: float = 0.7,
    ) -> Dict[str, Any]:
        self._require_concept()
        if place_id:
            self._require_access(place_id, "Event place")
        if source_id:
            self._require_access(source_id, "Event source")
        for target in self._as_list(affects):
            self._require_access(target, "Affected target")
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=description,
            atom_type="geo_event",
            subset="events",
            meta_extra={
                "role": "event",
                "event_type": event_type,
                "place_id": place_id or None,
                "event_time": event_time,
                "occurred_at": event_time,
                "time_sort": self._normalize_time_sort(event_time),
                "intensity": self._clamp01(intensity, 0.5),
                "source_id": source_id or None,
                "affects": affects or [],
                "confidence": self._clamp01(confidence, 0.7),
            },
            concept_word="event",
        )
        if place_id:
            self.cortex.put_link(key, place_id, "geo:occurred_at", author=author_id)
        if source_id:
            self.cortex.put_link(key, source_id, "geo:evidenced_by", author=author_id)
        for target in self._as_list(affects):
            self.cortex.put_link(key, target, "geo:affects", author=author_id)
        self._append_to_time_index(key, author_id)
        return {"status": "event_added", "event_id": key}

    def op_add_layer(
        self,
        label: str,
        layer_type: str = "data",
        members: Optional[List[str]] = None,
        description: str = "",
        source_id: str = "",
    ) -> Dict[str, Any]:
        self._require_concept()
        if not label:
            raise ValueError("layer label is required.")
        if source_id:
            self._require_access(source_id, "Layer source")
        for member in self._as_list(members):
            self._require_access(member, "Layer member")
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=description or label,
            atom_type="geo_layer",
            subset="layers",
            meta_extra={
                "role": "layer",
                "label": label,
                "layer_type": layer_type,
                "members": members or [],
                "source_id": source_id or None,
            },
            concept_word="layer",
        )
        for member in self._as_list(members):
            self.cortex.put_link(key, member, "geo:contains_member", author=author_id)
        if source_id:
            self.cortex.put_link(key, source_id, "geo:evidenced_by", author=author_id)
        return {"status": "layer_added", "layer_id": key, "label": label}

    def op_add_snapshot(
        self,
        label: str,
        captured_at: str = "",
        members: Optional[List[str]] = None,
        note: str = "",
        source_id: str = "",
    ) -> Dict[str, Any]:
        self._require_concept()
        if not label:
            raise ValueError("snapshot label is required.")
        if source_id:
            self._require_access(source_id, "Snapshot source")
        for member in self._as_list(members):
            self._require_access(member, "Snapshot member")
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=note or label,
            atom_type="geo_snapshot",
            subset="snapshots",
            meta_extra={
                "role": "snapshot",
                "label": label,
                "captured_at": captured_at,
                "occurred_at": captured_at,
                "time_sort": self._normalize_time_sort(captured_at),
                "members": members or [],
                "source_id": source_id or None,
            },
            concept_word="snapshot",
        )
        for member in self._as_list(members):
            self.cortex.put_link(key, member, "geo:snapshots", author=author_id)
        if source_id:
            self.cortex.put_link(key, source_id, "geo:evidenced_by", author=author_id)
        self._append_to_time_index(key, author_id)
        return {"status": "snapshot_added", "snapshot_id": key, "label": label}

    # ------------------------------------------------------------------
    # Read operators
    # ------------------------------------------------------------------

    def op_map(self) -> Dict[str, Any]:
        self._require_concept()
        meta = self._meta(self.concept_id)
        return {
            "geo_id": self.concept_id,
            "concept_id": self.concept_id,
            "title": meta.get("title", ""),
            "coordinate_system": meta.get("coordinate_system", ""),
            **{suffix: self._members(suffix) for suffix in self.SUBSETS},
        }

    # ------------------------------------------------------------------
    # Phase 2 — topology / transform / clone / transition
    # ------------------------------------------------------------------

    def op_connect(
        self,
        src_id: str,
        dst_id: str,
        connection_type: str = "adjacent_to",
        direction: str = "directed",
        distance: Optional[float] = None,
        weight: float = 1.0,
        evidence: Optional[List[str]] = None,
        note: str = "",
    ) -> Dict[str, Any]:
        """
        Connect two spatial atoms.
        direction=mutual creates bidirectional links.
        """
        self._require_concept()
        self._require_access(src_id, "Source spatial atom")
        self._require_access(dst_id, "Destination spatial atom")
        if connection_type not in CONNECTION_TYPES:
            raise ValueError(f"connection_type must be one of {CONNECTION_TYPES}.")
        if direction not in ("directed", "mutual"):
            raise ValueError("direction must be directed or mutual.")
        for ev in self._as_list(evidence):
            self._require_access(ev, "Connection evidence")
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=note or f"{connection_type}:{src_id[:8]}->{dst_id[:8]}",
            atom_type="geo_connection",
            subset="connections",
            meta_extra={
                "role": "connection",
                "src_id": src_id,
                "dst_id": dst_id,
                "connection_type": connection_type,
                "direction": direction,
                "distance": distance,
                "weight": float(weight),
                "evidence": evidence or [],
            },
            concept_word="connection",
        )
        rel = f"geo:{connection_type}"
        self.cortex.put_link(src_id, dst_id, rel, author=author_id)
        self.cortex.put_link(key, src_id, "geo:from", author=author_id)
        self.cortex.put_link(key, dst_id, "geo:to", author=author_id)
        if direction == "mutual":
            self.cortex.put_link(dst_id, src_id, rel, author=author_id)
        for ev in self._as_list(evidence):
            self.cortex.put_link(key, ev, "geo:evidenced_by", author=author_id)
        return {
            "status": "connected",
            "connection_id": key,
            "src_id": src_id,
            "dst_id": dst_id,
            "connection_type": connection_type,
        }

    def op_add_affine(
        self,
        label: str,
        source_system: str,
        target_system: str,
        matrix: List[List[float]],
        offset: Optional[List[float]] = None,
        source_id: str = "",
        confidence: float = 0.8,
        note: str = "",
    ) -> Dict[str, Any]:
        """
        Register an affine transform between coordinate systems.
        Records the mapping rule as an inspectable graph atom; does not
        automatically transform existing coordinate atoms.
        """
        self._require_concept()
        if not label:
            raise ValueError("affine label is required.")
        if not isinstance(matrix, list) or not matrix:
            raise ValueError("matrix must be a non-empty list of lists.")
        if source_id:
            self._require_access(source_id, "Affine source")
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=note or label,
            atom_type="geo_affine",
            subset="affines",
            meta_extra={
                "role": "affine",
                "label": label,
                "source_system": source_system,
                "target_system": target_system,
                "matrix": matrix,
                "offset": offset or [],
                "source_id": source_id or None,
                "confidence": self._clamp01(confidence, 0.8),
            },
            concept_word="affine",
        )
        if source_id:
            self.cortex.put_link(key, source_id, "geo:evidenced_by", author=author_id)
        return {
            "status": "affine_added",
            "affine_id": key,
            "label": label,
            "source_system": source_system,
            "target_system": target_system,
        }

    def op_clone_place(
        self,
        place_id: str,
        name: str = "",
        clone_type: str = "alternate",
        reason: str = "",
        source_id: str = "",
        preserve_coordinates: bool = True,
        hidden: bool = False,
        snapshot_id: str = "",
    ) -> Dict[str, Any]:
        """
        Clone a Place as an alternate representation.
        Use cases: disputed geography, historical reconstruction,
        fictional/symbolic layer, hidden place revealed later.
        snapshot_id: if provided, records which geo.snapshot this clone was
                     based on (geo:cloned_from_snapshot link). Enables
                     'build a WorldModel from 1940 terrain' workflows.
        """
        self._require_concept()
        self._require_access(place_id, "Place to clone")
        if source_id:
            self._require_access(source_id, "Clone source")
        if snapshot_id:
            self._require_access(snapshot_id, "Snapshot")
        author_id, _ = self._author_and_scopes()
        src_meta = self._meta(place_id)
        src_content = self._content(place_id)
        clone_name = name or f"{src_meta.get('name', 'place')} ({clone_type})"
        coordinate_id = src_meta.get("coordinate_id") if preserve_coordinates else None
        key = self._put_atom(
            content=src_content,
            atom_type="geo_place",
            subset="places",
            meta_extra={
                "role": "place",
                "name": clone_name,
                "place_type": src_meta.get("place_type", "other"),
                "coordinate_id": coordinate_id,
                "parent_place_id": src_meta.get("parent_place_id"),
                "source_id": source_id or src_meta.get("source_id"),
                "confidence": src_meta.get("confidence", 0.5),
                "hidden": bool(hidden),
                "clone_of": place_id,
                "clone_type": clone_type,
                "reason": reason,
                "snapshot_id": snapshot_id or None,
            },
            concept_word="place",
        )
        self._register(key, subset_suffix="clones", concept_word="clone")
        self.cortex.put_link(place_id, key, "geo:cloned_as", author=author_id)
        self.cortex.put_link(key, place_id, "geo:clone_of", author=author_id)
        if coordinate_id:
            self.cortex.put_link(key, coordinate_id, "geo:located_at", author=author_id)
        if source_id:
            self.cortex.put_link(key, source_id, "geo:evidenced_by", author=author_id)
        if snapshot_id:
            self.cortex.put_link(key, snapshot_id, "geo:cloned_from_snapshot", author=author_id)
        return {
            "status": "place_cloned",
            "original_place_id": place_id,
            "clone_place_id": key,
            "name": clone_name,
            "clone_type": clone_type,
            "snapshot_id": snapshot_id or None,
        }

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
        """
        Record a spatial transition as an auditable event-sourced atom.
        Does not mutate existing atoms.
        """
        self._require_concept()
        self._require_access(target_id, "Transition target")
        if transition_type not in TRANSITION_TYPES:
            raise ValueError(f"transition_type must be one of {TRANSITION_TYPES}.")
        if event_id:
            self._require_access(event_id, "Transition event")
        for ev in self._as_list(evidence):
            self._require_access(ev, "Transition evidence")
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=description,
            atom_type="geo_transition",
            subset="transitions",
            meta_extra={
                "role": "transition",
                "target_id": target_id,
                "transition_type": transition_type,
                "event_id": event_id or None,
                "from_state": from_state,
                "to_state": to_state,
                "occurred_at": occurred_at,
                "time_sort": self._normalize_time_sort(occurred_at),
                "evidence": evidence or [],
                "confidence": self._clamp01(confidence, 0.7),
            },
            concept_word="transition",
        )
        self.cortex.put_link(target_id, key, "geo:changed_by", author=author_id)
        if event_id:
            self.cortex.put_link(key, event_id, "geo:caused_by", author=author_id)
        for ev in self._as_list(evidence):
            self.cortex.put_link(key, ev, "geo:evidenced_by", author=author_id)
        if transition_type == "revealed":
            self.cortex.put_link(target_id, key, "geo:revealed_by", author=author_id)
            self.cortex.put_link(target_id, key, "sys:revealed_by", author=author_id)
        elif transition_type == "hidden":
            self.cortex.put_link(target_id, key, "geo:hidden_by", author=author_id)
            self.cortex.put_link(target_id, key, "sys:hidden_by", author=author_id)
        elif transition_type in ("deleted", "tombstoned"):
            self.cortex.put_link(target_id, key, "sys:tombstoned_by", author=author_id)
        elif transition_type == "moved":
            self.cortex.put_link(target_id, key, "geo:moved_by", author=author_id)
        self._append_to_time_index(key, author_id)
        return {
            "status": "transition_added",
            "transition_id": key,
            "target_id": target_id,
            "transition_type": transition_type,
        }

    # ------------------------------------------------------------------
    # Phase 3 — spatial query / discovery / diagnosis
    # ------------------------------------------------------------------

    def op_nearby(
        self,
        place_id: str,
        rels: Optional[List[str]] = None,
        include_hidden: bool = False,
        depth: int = 1,
    ) -> Dict[str, Any]:
        """Return nearby / connected places by walking geo:* links."""
        self._require_concept()
        self._require_access(place_id, "Place")
        result = self._graph().walk(
            start_id=place_id,
            rels=list(rels or DEFAULT_NEARBY_RELS),
            depth=max(1, int(depth)),
            include_hidden=include_hidden,
        )
        return {
            "place_id": place_id,
            "nearby":   result["neighbors"],
            "count":    result["count"],
        }

    def op_path(
        self,
        src_id: str,
        dst_id: str,
        rels: Optional[List[str]] = None,
        max_depth: int = 6,
        include_hidden: bool = False,
    ) -> Dict[str, Any]:
        """Find the shortest BFS path between two spatial atoms."""
        self._require_concept()
        self._require_access(src_id, "Source place")
        self._require_access(dst_id, "Destination place")
        return self._graph().path(
            src_id=src_id,
            dst_id=dst_id,
            rels=list(rels or DEFAULT_PATH_RELS),
            max_depth=max_depth,
            include_hidden=include_hidden,
        )

    def op_reveal(
        self,
        place_id: str,
        revealed_by: str = "",
        note: str = "",
        confidence: float = 0.8,
    ) -> Dict[str, Any]:
        """
        Reveal a hidden place by recording a transition.
        Does not mutate the original atom — the revealed state is event-sourced.
        """
        self._require_concept()
        self._require_access(place_id, "Place")
        if revealed_by:
            self._require_access(revealed_by, "Revealing evidence/event")
        transition = self.op_add_transition(
            target_id=place_id,
            transition_type="revealed",
            description=note or f"Place revealed: {place_id[:12]}",
            event_id=revealed_by,
            to_state="revealed",
            evidence=[revealed_by] if revealed_by else [],
            confidence=confidence,
        )
        return {
            "status": "revealed",
            "place_id": place_id,
            "transition_id": transition["transition_id"],
        }

    def op_diagnose(self) -> Dict[str, Any]:
        """Diagnose spatial consistency and modeling gaps."""
        self._require_concept()
        places      = [self._summary(k) for k in self._members("places")]
        coords      = [self._summary(k) for k in self._members("coordinates")]
        connections = [self._summary(k) for k in self._members("connections")]
        affines     = [self._summary(k) for k in self._members("affines")]
        clones      = [self._summary(k) for k in self._members("clones")]
        transitions = [self._summary(k) for k in self._members("transitions")]

        coord_ids = {c["id"] for c in coords}
        place_ids = {p["id"] for p in places}

        places_without_coordinates = []
        hidden_places = []
        orphan_connections = []
        clone_without_original = []
        low_confidence = []

        for p in places:
            meta = p["meta"]
            cid = meta.get("coordinate_id")
            if not cid or (cid not in coord_ids and not self._visible(cid)):
                places_without_coordinates.append(p)
            if meta.get("hidden") and not self._is_revealed(p["id"]):
                hidden_places.append(p)
            if float(meta.get("confidence", 1.0)) < 0.4:
                low_confidence.append(p)

        for c in connections:
            meta = c["meta"]
            if meta.get("src_id") not in place_ids or meta.get("dst_id") not in place_ids:
                orphan_connections.append(c)

        for cl in clones:
            original = cl["meta"].get("clone_of")
            if original and not self._visible(original):
                clone_without_original.append(cl)

        return {
            "geo_root_id": self.concept_id,
            "counts": {
                "places":      len(places),
                "coordinates": len(coords),
                "connections": len(connections),
                "affines":     len(affines),
                "clones":      len(clones),
                "transitions": len(transitions),
            },
            "diagnosis": {
                "places_without_coordinates": places_without_coordinates[-10:],
                "hidden_places":              hidden_places[-10:],
                "orphan_connections":         orphan_connections[-10:],
                "clone_without_original":     clone_without_original[-10:],
                "low_confidence_places":      low_confidence[-10:],
                "has_affine_systems":         bool(affines),
                "has_transition_history":     bool(transitions),
            },
        }

    # ------------------------------------------------------------------
    # Temporal linked-list index (TemporalMixin)
    # ------------------------------------------------------------------

    def op_history(
        self,
        limit: int = 100,
        include_hidden: bool = False,
        atom_types: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Walk the temporal index chronologically (oldest → newest)."""
        self._require_concept()
        effective_types = list(atom_types) if atom_types else list(self.TEMPORAL_TYPES)
        history = self._walk_time_index(
            limit=limit,
            atom_types=effective_types,
            include_hidden=include_hidden,
        )
        return {"geo_id": self.concept_id, "history": history, "count": len(history)}

    def op_time_rebuild(self) -> Dict[str, Any]:
        """Rebuild the temporal linked list from TEMPORAL_SUBSETS.
        Run once after importing historical Geo data that predates the index."""
        self._require_concept()
        author_id, _ = self._author_and_scopes()
        result = self._rebuild_time_index(author_id)
        return {"status": "time_rebuilt", "geo_id": self.concept_id, "count": result["count"]}
