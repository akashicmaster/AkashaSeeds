"""
World Concept Model.
A topology model for fictional / conceptual worlds:
    "A World is a space in which paths can exist."

Phase 1:
    - Manual world-state recording
    - No automatic simulation
    - Event atoms record change pressure
    - place.state / law.change record human-authored consequences

Namespace contract:
    - Content atoms      -> set:world:{concept_id} and subset sets
    - Concept-word atoms -> set:concept:{concept_id}

Version: 1.0.1 (Claude review / bug fixes applied)
Fixes:
    - Bug 2: op_add_prop suggests stored as plain metadata, not concept_words
             (avoids alias collision with other concept models)
    - Bug 3: op_add_connection uses timeline=False (Connection is structural, not temporal)
    - Bug 4: op_add_collection uses timeline=False (Collection is structural, not temporal)
    - Bug 5: op_put_member documents cross-concept member_id scope assumption
    - Note:  history subset intentionally overlaps events subset —
             history = all changes (events + place_states + law_states)
"""

import time
import logging
from typing import Any, Dict, List, Optional

from lib.akasha.concepts.base import BaseConcept

logger = logging.getLogger("Harmonia.Concept.World")

CONTEXT_KEY_ACTIVE = "active_world_root"
INDEX_SET = "set:world:index"
_CONCEPT_WORD_ALIAS_PREFIX = "concept:word:"

SUBSET_TO_RELATION: Dict[str, str] = {
    "places":        "world:has_place",
    "objects":       "world:has_object",
    "props":         "world:has_prop",
    "suggesters":    "world:has_suggester",
    "collections":   "world:has_collection",
    "connections":   "world:has_connection",
    "portals":       "world:has_portal",
    "laws":          "world:has_law",
    "place_states":  "world:has_place_state",
    "law_states":    "world:has_law_state",
    "events":        "world:has_event",
    "history":       "world:has_history",
    "hidden":        "world:has_hidden",
}

# Default Change Thresholds per Law type
_LAW_THRESHOLDS: Dict[str, float] = {
    "physical":  0.99,
    "social":    0.7,
    "special":   0.5,
    "belief":    0.3,
    "narrative": 0.9,
}


class WorldConcept(BaseConcept):
    """Concept model for worlds, stages, places, laws, portals, and history."""

    CONCEPT_PREFIX = "world"
    CONTEXT_KEY_ACTIVE = CONTEXT_KEY_ACTIVE

    CONCEPT_METHODS = {
        "new":          {"op": "op_new"},
        "open": {
            "op": "op_open",
            "coerce": lambda d: {
                "world_id": d.get("world_id") or d.get("id") or d.get("concept_id", "")
            },
        },
        "ls":           {"op": "op_list_all"},
        "map":          {"op": "op_map"},
        "rm":           {"op": "op_delete"},
        "place.add":    {"op": "op_add_place"},
        "place.state":  {"op": "op_set_place_state"},
        "object.add":   {"op": "op_add_object"},
        "prop.add":     {"op": "op_add_prop"},
        "collect.add":  {"op": "op_add_collection"},
        "collect.put":  {"op": "op_put_member"},
        "connect":      {"op": "op_add_connection"},
        "portal.add":   {"op": "op_add_portal"},
        "law.add":      {"op": "op_add_law"},
        "law.change":   {"op": "op_change_law"},
        "hidden.add":   {"op": "op_add_hidden"},
        "event":        {"op": "op_apply_event"},
        "diagnose":     {"op": "op_diagnose"},
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

    def _world_set(self, suffix: Optional[str] = None) -> str:
        base = f"set:world:{self.concept_id}"
        return f"{base}:{suffix}" if suffix else base

    def _author_and_scopes(self):
        author_id = getattr(self.session, "client_id", "system")
        scopes = [f"owner:user_{author_id}", f"view:user_{author_id}"]
        return author_id, scopes

    def _create_sets(self) -> None:
        self.ensure_concept_set()
        self.cortex.create_set(self._world_set())
        for suffix in self.SUBSETS:
            self.cortex.create_set(self._world_set(suffix))
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
                "concept_model": "world",
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
        self.cortex.add_to_set(self._world_set(), key)
        if subset_suffix:
            self.cortex.add_to_set(self._world_set(subset_suffix), key)
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
            key for key in self.cortex.get_collection_members(self._world_set(suffix))
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
        timeline: bool = True,
    ) -> str:
        author_id, scopes = self._author_and_scopes()
        meta = {
            "type": atom_type,
            "concept": "world",
            "created_at": time.time(),
        }
        if meta_extra:
            meta.update(meta_extra)
        key = self.cortex.put_chunk(
            content=content, meta=meta, author=author_id, scopes=scopes
        )
        self._register(key, subset_suffix=subset, concept_word=concept_word)
        relation = SUBSET_TO_RELATION.get(subset, f"world:has_{subset}")
        self.cortex.put_link(self.concept_id, key, relation, author=author_id)
        if timeline:
            self._append_to_timeline(key, author_id)
        return key

    def _append_to_timeline(self, node_id: str, author_id: str) -> None:
        tail_links = self.cortex.get_adjacent_links(self.concept_id, "sys:bottom")
        if not tail_links:
            self.cortex.put_link(self.concept_id, node_id, "sys:top", author=author_id)
            self.cortex.put_link(self.concept_id, node_id, "sys:bottom", author=author_id)
            return
        last_node_id = tail_links[0][0]
        self.cortex.put_link(last_node_id, node_id, "sys:next", author=author_id)
        self.cortex.put_link(node_id, last_node_id, "sys:previous", author=author_id)
        self.cortex.remove_link(self.concept_id, last_node_id, "sys:bottom")
        self.cortex.put_link(self.concept_id, node_id, "sys:bottom", author=author_id)

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
        time_type: str = "linear",
    ) -> Dict[str, Any]:
        author_id, scopes = self._author_and_scopes()
        if not title:
            raise ValueError("world.new requires title.")
        root_id = self.cortex.put_chunk(
            content=f"[ World: {title} ]",
            meta={
                "type":        "concept",
                "concept":     "world",
                "role":        "root",
                "title":       title,
                "description": description,
                "time": {
                    "type":    time_type,
                    "current": None,
                    "speed":   1.0,
                    "unit":    "day",
                },
                "created_at": time.time(),
            },
            author=author_id,
            scopes=scopes,
        )
        self.concept_id = root_id
        self.set_name = f"set:concept:{self.concept_id}"
        self._create_sets()
        # Root belongs to content set only — no concept_word on root (Two-Namespace Rule).
        self.cortex.add_to_set(self._world_set(), root_id)
        self.cortex.add_to_set(INDEX_SET, root_id)
        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, root_id)
        logger.info("[WorldConcept] Created '%s' (%s)", title, root_id[:8])
        return {
            "status":     "created",
            "concept_id": root_id,
            "world_id":   root_id,
            "title":      title,
        }

    def op_open(self, world_id: str) -> Dict[str, Any]:
        meta = self._meta(world_id)
        if not meta or meta.get("concept") != "world":
            raise RuntimeError(f"Atom '{world_id[:12]}' is not a world root.")
        if not self._visible(world_id):
            raise RuntimeError(f"World not accessible: {world_id[:12]}")
        self.concept_id = world_id
        self.set_name = f"set:concept:{self.concept_id}"
        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, world_id)
        return {
            "status":      "opened",
            "concept_id":  world_id,
            "world_id":    world_id,
            "title":       meta.get("title", ""),
            "description": meta.get("description", ""),
        }

    def op_list_all(self) -> Dict[str, Any]:
        worlds = []
        for key in self.cortex.get_collection_members(INDEX_SET):
            if not self._visible(key):
                continue
            meta = self._meta(key)
            if meta.get("concept") != "world":
                continue
            worlds.append({
                "world_id":    key,
                "concept_id":  key,
                "title":       meta.get("title", ""),
                "description": meta.get("description", ""),
                "created_at":  meta.get("created_at", 0),
            })
        worlds.sort(key=lambda x: x.get("created_at", 0), reverse=True)
        return {"worlds": worlds, "count": len(worlds)}

    def op_delete(self) -> Dict[str, Any]:
        self._require_concept()
        target = self.concept_id
        self.cortex.drop_chunk(target, requester_scopes=self.allowed_scopes)
        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, None)
        return {"status": "deleted", "world_id": target, "concept_id": target}

    # ------------------------------------------------------------------
    # Place
    # ------------------------------------------------------------------

    def op_add_place(
        self,
        name: str,
        place_type: str = "artificial",
        category: str = "",
        layer: Optional[Dict[str, Any]] = None,
        note: str = "",
    ) -> Dict[str, Any]:
        self._require_concept()
        if not name:
            raise ValueError("place name is required.")
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=note or name,
            atom_type="world_place",
            subset="places",
            meta_extra={
                "role":       "place",
                "name":       name,
                "place_type": place_type,
                "category":   category,
                "layers":     layer or {},
            },
            concept_word="place",
        )
        self.cortex.put_link(self.concept_id, key, "sys:contains", author=author_id)
        self.cortex.put_link(key, self.concept_id, "sys:part_of", author=author_id)
        return {"status": "place_added", "place_id": key, "name": name}

    def op_set_place_state(
        self,
        place_id: str,
        state: str,
        event_id: str = "",
        layer: str = "functional",
        note: str = "",
    ) -> Dict[str, Any]:
        """
        Manual v1 state recording.
        Typical usage:
            world.event "The king is dead" intensity=0.8  → event_id
            world.place.state <castle_id> "succession_crisis" event_id=<event_id>
        """
        self._require_concept()
        self._require_access(place_id, "Place")
        if event_id:
            self._require_access(event_id, "Event")
        if not state:
            raise ValueError("state is required.")
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=note or f"{place_id[:12]}:{state}",
            atom_type="world_place_state",
            subset="place_states",
            meta_extra={
                "role":     "place_state",
                "place_id": place_id,
                "state":    state,
                "layer":    layer,
                "event_id": event_id or None,
            },
            concept_word="state",
        )
        # Also record in history — place_states are part of the change record.
        self.cortex.add_to_set(self._world_set("history"), key)
        self.cortex.put_link(place_id, key, "world:state",    author=author_id)
        self.cortex.put_link(key, place_id, "world:state_of", author=author_id)
        if event_id:
            self.cortex.put_link(event_id, key, "world:changes", author=author_id)
        return {
            "status":         "place_state_set",
            "place_state_id": key,
            "place_id":       place_id,
            "state":          state,
        }

    # ------------------------------------------------------------------
    # Object / Prop / Suggester
    # ------------------------------------------------------------------

    def op_add_object(
        self,
        place_id: str,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
        note: str = "",
    ) -> Dict[str, Any]:
        self._require_concept()
        self._require_access(place_id, "Place")
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=note or name,
            atom_type="world_object",
            subset="objects",
            meta_extra={
                "role":       "object",
                "place_id":   place_id,
                "name":       name,
                "attributes": attributes or {},
            },
            concept_word="object",
        )
        self.cortex.put_link(place_id, key, "sys:contains", author=author_id)
        self.cortex.put_link(key, place_id, "sys:part_of",  author=author_id)
        return {"status": "object_added", "object_id": key, "place_id": place_id}

    def op_add_prop(
        self,
        place_id: str,
        item: str,
        suggests: Optional[List[str]] = None,
        minimal: bool = True,
        imagination_trigger: str = "",
        note: str = "",
    ) -> Dict[str, Any]:
        """
        Bug 2 fix: suggests are stored as plain metadata strings, NOT registered
        as concept_word atoms. This avoids alias collisions with other concept
        models that may use the same words (e.g. "village", "water").
        world:suggests links are created only for the prop atom itself.
        """
        self._require_concept()
        self._require_access(place_id, "Place")
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=note or item,
            atom_type="world_prop",
            subset="props",
            meta_extra={
                "role":                "prop",
                "suggester_type":      "prop",
                "place_id":            place_id,
                "item":                item,
                "suggests":            suggests or [],   # plain strings in meta
                "minimal":             bool(minimal),
                "imagination_trigger": imagination_trigger,
            },
            concept_word="prop",
        )
        # Prop is also a Suggester.
        self.cortex.add_to_set(self._world_set("suggesters"), key)
        self.cortex.put_link(self.concept_id, key, "world:has_suggester", author=author_id)
        self.cortex.put_link(place_id, key, "sys:contains", author=author_id)
        self.cortex.put_link(key, place_id, "sys:part_of",  author=author_id)
        # world:suggests links point from the prop to a concept_word only for
        # structural terms that already exist in the catalog — never auto-created.
        # Semantic meaning of suggests lives in meta["suggests"] (plain strings).
        return {"status": "prop_added", "prop_id": key, "place_id": place_id}

    # ------------------------------------------------------------------
    # Collection
    # ------------------------------------------------------------------

    def op_add_collection(
        self,
        label: str,
        collection_type: str = "group",
        note: str = "",
    ) -> Dict[str, Any]:
        """
        Bug 4 fix: Collection is structural (not temporal) → timeline=False.
        """
        self._require_concept()
        if not label:
            raise ValueError("collection label is required.")
        key = self._put_atom(
            content=note or label,
            atom_type="world_collection",
            subset="collections",
            meta_extra={
                "role":            "collection",
                "label":           label,
                "collection_type": collection_type,
            },
            concept_word="collection",
            timeline=False,   # Bug 4 fix
        )
        return {"status": "collection_added", "collection_id": key, "label": label}

    def op_put_member(
        self,
        collect_id: str,
        member_id: str,
        relation: str = "sys:contains",
    ) -> Dict[str, Any]:
        """
        Add any accessible atom as a member of a collection.

        NOTE (Bug 5): member_id may be a Cast atom or Bot atom from another
        concept model. _require_access checks that member_id is readable by
        the current session's scopes. This works as long as the Cast/Bot atom
        was created in the same session or in a shared scope. Cross-session
        sharing requires explicit scope grants at atom creation time.
        """
        self._require_concept()
        self._require_access(collect_id, "Collection")
        self._require_access(member_id, "Member")
        author_id, _ = self._author_and_scopes()
        self.cortex.put_link(collect_id, member_id, relation,      author=author_id)
        self.cortex.put_link(member_id, collect_id, "sys:part_of", author=author_id)
        return {
            "status":        "member_added",
            "collection_id": collect_id,
            "member_id":     member_id,
        }

    # ------------------------------------------------------------------
    # Connection / Portal
    # ------------------------------------------------------------------

    def op_add_connection(
        self,
        from_id: str,
        to_id: str,
        connection_type: str = "road",
        direction: str = "bidirectional",
        difficulty: float = 0.0,
        transport: Optional[List[str]] = None,
        travel_time: str = "",
        note: str = "",
    ) -> Dict[str, Any]:
        """
        Bug 3 fix: Connection is structural (not temporal) → timeline=False.
        Connections define the graph topology of the world; they are not events.
        """
        self._require_concept()
        self._require_access(from_id, "From place")
        self._require_access(to_id,   "To place")
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=note or f"{connection_type}:{from_id[:8]}->{to_id[:8]}",
            atom_type="world_connection",
            subset="connections",
            meta_extra={
                "role":            "connection",
                "from":            from_id,
                "to":              to_id,
                "connection_type": connection_type,
                "direction":       direction,
                "difficulty":      self._clamp01(difficulty, 0.0),
                "transport":       transport or [],
                "time":            travel_time,
            },
            concept_word="connection",
            timeline=False,   # Bug 3 fix
        )
        self.cortex.put_link(from_id, to_id, "world:connects_to", author=author_id)
        self.cortex.put_link(key, from_id, "world:from", author=author_id)
        self.cortex.put_link(key, to_id,   "world:to",   author=author_id)
        if direction == "bidirectional":
            self.cortex.put_link(to_id, from_id, "world:connects_to", author=author_id)
        return {"status": "connection_added", "connection_id": key}

    def op_add_portal(
        self,
        place_id: str,
        direction: str = "outbound",
        suggests: str = "",
        connects_to: str = "",
        note: str = "",
    ) -> Dict[str, Any]:
        self._require_concept()
        self._require_access(place_id, "Place")
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=note or f"portal:{suggests or direction}",
            atom_type="world_portal",
            subset="portals",
            meta_extra={
                "role":           "portal",
                "suggester_type": "portal",
                "place_id":       place_id,
                "direction":      direction,
                "suggests":       suggests,
                "connects_to":    connects_to or None,
            },
            concept_word="portal",
        )
        # Portal is also a Suggester.
        self.cortex.add_to_set(self._world_set("suggesters"), key)
        self.cortex.put_link(self.concept_id, key, "world:has_suggester", author=author_id)
        self.cortex.put_link(place_id, key, "world:has_portal", author=author_id)
        self.cortex.put_link(key, place_id, "sys:part_of",      author=author_id)
        # suggests is stored as plain string in meta (same policy as Prop.suggests).
        # No concept_word registration to avoid alias collision.
        return {"status": "portal_added", "portal_id": key, "place_id": place_id}

    # ------------------------------------------------------------------
    # Law
    # ------------------------------------------------------------------

    def op_add_law(
        self,
        law_type: str,
        content: str,
        threshold: Optional[float] = None,
        state: str = "active",
        scope: str = "world",
        contradicts: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        self._require_concept()
        if law_type not in _LAW_THRESHOLDS:
            raise ValueError(
                f"law_type must be one of {list(_LAW_THRESHOLDS.keys())}."
            )
        threshold_value = (
            self._clamp01(threshold, _LAW_THRESHOLDS[law_type])
            if threshold is not None
            else _LAW_THRESHOLDS[law_type]
        )
        for law_id in self._as_list(contradicts):
            self._require_access(law_id, "Contradicted law")
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=content,
            atom_type="world_law",
            subset="laws",
            meta_extra={
                "role":        "law",
                "law_type":    law_type,
                "threshold":   threshold_value,
                "state":       state,
                "scope":       scope,
                "contradicts": contradicts or [],
            },
            concept_word=f"{law_type}_law",
        )
        for law_id in self._as_list(contradicts):
            self.cortex.put_link(key, law_id, "world:contradicts", author=author_id)
        return {
            "status":    "law_added",
            "law_id":    key,
            "law_type":  law_type,
            "state":     state,
            "threshold": threshold_value,
        }

    def op_change_law(
        self,
        law_id: str,
        new_state: str,
        event_id: str = "",
        reason: str = "",
    ) -> Dict[str, Any]:
        """
        Event-sourced law-state recording.
        Does NOT mutate the original law atom — appends a law_state atom so
        the full history of law changes remains auditable.
        """
        self._require_concept()
        self._require_access(law_id, "Law")
        if event_id:
            self._require_access(event_id, "Event")
        if not new_state:
            raise ValueError("new_state is required.")
        law_meta = self._meta(law_id)
        author_id, _ = self._author_and_scopes()
        key = self._put_atom(
            content=reason or f"{law_id[:12]} -> {new_state}",
            atom_type="world_law_state",
            subset="law_states",
            meta_extra={
                "role":           "law_state",
                "law_id":         law_id,
                "law_type":       law_meta.get("law_type"),
                "previous_state": law_meta.get("state"),
                "new_state":      new_state,
                "event_id":       event_id or None,
                "reason":         reason,
            },
            concept_word="law_state",
        )
        # Also record in history — law_states are part of the change record.
        self.cortex.add_to_set(self._world_set("history"), key)
        self.cortex.put_link(law_id, key, "world:state",    author=author_id)
        self.cortex.put_link(key, law_id, "world:state_of", author=author_id)
        if event_id:
            self.cortex.put_link(event_id, key, "world:changes", author=author_id)
        return {
            "status":       "law_changed",
            "law_state_id": key,
            "law_id":       law_id,
            "new_state":    new_state,
        }

    # ------------------------------------------------------------------
    # Hidden Layer
    # ------------------------------------------------------------------

    def op_add_hidden(
        self,
        hint: str,
        revealed_by: str = "",
        reveals: str = "",
        confidence: float = 0.5,
    ) -> Dict[str, Any]:
        """
        Hidden is intentionally NOT a Place.
        It exists as an undetermined atom with a hint.
        When discovered (by Cast Policy or Story event), use world.place.add
        to materialise it as a real Place, then link it to this hidden atom.
        """
        self._require_concept()
        if not hint:
            raise ValueError("hidden hint is required.")
        key = self._put_atom(
            content=hint,
            atom_type="world_hidden",
            subset="hidden",
            meta_extra={
                "role":        "hidden",
                "hint":        hint,
                "revealed_by": revealed_by,
                "reveals":     reveals,
                "confidence":  self._clamp01(confidence, 0.5),
            },
            concept_word="hidden",
        )
        return {"status": "hidden_added", "hidden_id": key, "hint": hint}

    # ------------------------------------------------------------------
    # Event / History
    # ------------------------------------------------------------------

    def op_apply_event(
        self,
        description: str,
        intensity: float = 0.5,
        frequency: float = 1.0,
        accumulation: float = 0.0,
        place_id: str = "",
        event_type: str = "world_event",
        effects: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Phase 1: create an Event atom and record it in both events and history.
        This does NOT automatically update Place.State or Law.State.

        Design note on history subset:
            history = all change records (events + place_states + law_states).
            events subset = only event atoms.
            place_states and law_states are also added to history by their
            respective operators. This intentional overlap lets op_diagnose
            query a unified timeline of changes via the history subset.

        After calling this, use:
            world.place.state <place_id> <state> event_id=<event_id>
            world.law.change  <law_id>   <state> event_id=<event_id>
        """
        self._require_concept()
        if not description:
            raise ValueError("event description is required.")
        if place_id:
            self._require_access(place_id, "Event place")
        author_id, _ = self._author_and_scopes()
        force = min(
            1.0,
            self._clamp01(intensity, 0.5) * max(1.0, float(frequency))
            + self._clamp01(accumulation, 0.0) * 0.5,
        )
        key = self._put_atom(
            content=description,
            atom_type="world_event",
            subset="events",
            meta_extra={
                "role":         "event",
                "event_type":   event_type,
                "description":  description,
                "intensity":    self._clamp01(intensity, 0.5),
                "frequency":    float(frequency),
                "accumulation": self._clamp01(accumulation, 0.0),
                "force":        round(force, 4),
                "place_id":     place_id or None,
                "effects":      effects or {},
            },
            concept_word="event",
        )
        # Events are always part of history.
        self.cortex.add_to_set(self._world_set("history"), key)
        self.cortex.put_link(self.concept_id, key, "world:has_history", author=author_id)
        if place_id:
            self.cortex.put_link(place_id, key, "world:event_at",   author=author_id)
            self.cortex.put_link(key, place_id, "world:located_at", author=author_id)
        return {
            "status":      "event_recorded",
            "event_id":    key,
            "description": description,
            "force":       round(force, 4),
            "manual_next_steps": [
                "world.place.state <place_id> <state> event_id=<event_id>",
                "world.law.change  <law_id>   <new_state> event_id=<event_id>",
            ],
        }

    # ------------------------------------------------------------------
    # Analysis
    # ------------------------------------------------------------------

    def op_map(self) -> Dict[str, Any]:
        self._require_concept()
        meta = self._meta(self.concept_id)
        return {
            "world_id":    self.concept_id,
            "concept_id":  self.concept_id,
            "title":       meta.get("title", ""),
            "description": meta.get("description", ""),
            **{suffix: self._members(suffix) for suffix in self.SUBSETS},
        }

    def op_diagnose(self, limit: int = 10) -> Dict[str, Any]:
        """
        Diagnose the world's current tensions.

        law_conflicts: Laws that explicitly contradict each other (World's
                       equivalent of Cast.contradiction).
        unstable_laws: Laws whose most recent state change moved them to a
                       destabilised, collapsed, or restricted state.
        high_force_events: Events with force >= 0.7 (threshold-level pressure).
        unrevealed_hidden: Hidden Layer atoms not yet materialised as Places.
        open_portals: Portals with no connects_to target (pure suggestion).

        limit: controls how many recent place_states / law_states to return.
        """
        self._require_concept()
        laws         = [self._summary(k) for k in self._members("laws")]
        hidden       = [self._summary(k) for k in self._members("hidden")]
        portals      = [self._summary(k) for k in self._members("portals")]
        place_states = [self._summary(k) for k in self._members("place_states")]
        law_states   = [self._summary(k) for k in self._members("law_states")]
        events       = [self._summary(k) for k in self._members("events")]

        # Law contradiction detection (World version of Cast.contradiction)
        law_conflicts = []
        for law in laws:
            for target_id in law["meta"].get("contradicts", []) or []:
                if self._visible(target_id):
                    law_conflicts.append({
                        "law":         law["id"],
                        "contradicts": target_id,
                    })

        unstable_laws = [
            s for s in law_states
            if s["meta"].get("new_state") in ("destabilized", "collapsed", "restricted")
        ]
        high_force_events = [
            e for e in events
            if float(e["meta"].get("force", 0.0)) >= 0.7
        ]

        return {
            "world_id": self.concept_id,
            "counts": {
                "places":      len(self._members("places")),
                "connections": len(self._members("connections")),
                "portals":     len(portals),
                "laws":        len(laws),
                "events":      len(events),
                "hidden":      len(hidden),
            },
            "diagnosis": {
                "law_conflicts":       law_conflicts,
                "unstable_laws":       unstable_laws,
                "high_force_events":   high_force_events,
                "unrevealed_hidden":   hidden,
                "open_portals": [
                    p for p in portals
                    if not p["meta"].get("connects_to")
                ],
                "recent_place_states": place_states[-limit:],
                "recent_law_states":   law_states[-limit:],
            },
        }
