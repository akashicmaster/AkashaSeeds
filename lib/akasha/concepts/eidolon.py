"""
EidolonConcept — the dark world outside Homonoia.
An invisible, malevolent outer realm whose internal topology (locations, hierarchies,
occupants) can be mapped but whose nature remains unknown. Design in progress.
Part of the Homonoia game world (see homonoia.py).
"""
import time
from typing import Any, Dict, List, Optional

from lib.akasha.concepts.base import BaseConcept

CONTEXT_KEY_ACTIVE = "active_eidolon_root"
INDEX_SET = "set:eidolon:index"


class EidolonConcept(BaseConcept):
    """Spatial (eidolon) model. Handles hierarchical topology and actor placement."""

    CONCEPT_PREFIX = "eidolon"
    CONTEXT_KEY_ACTIVE = CONTEXT_KEY_ACTIVE  # Required for SpaceConcept focus routing

    CONCEPT_METHODS = {
        "new":  {"op": "op_new"},
        "open": {"op": "op_open",
                 "coerce": lambda d: {"eidolon_id": d.get("eidolon_id") or d.get("id", "")}},
        "ls":   {"op": "op_list_all"},
        "link": {"op": "op_link_location"},
        "move": {"op": "op_move"},
        "map":  {"op": "op_map"},
        "rm":   {"op": "op_delete"},
    }

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

    def _eidolon_set(self, suffix: Optional[str] = None) -> str:
        base = f"set:eidolon:{self.concept_id}"
        return f"{base}:{suffix}" if suffix else base

    def _author_and_scopes(self):
        author_id = getattr(self.session, "client_id", "system")
        return author_id, [f"owner:user_{author_id}", f"view:user_{author_id}"]

    def _require_access(self, atom_id: str, label: str = "Atom") -> None:
        if not atom_id:
            raise ValueError(f"{label} id is required.")
        if not self.cortex.check_access(atom_id, self.allowed_scopes):
            raise RuntimeError(f"{label} not accessible: {atom_id[:12]}")

    def _visible_members(self, suffix: str) -> List[str]:
        return [
            k for k in self.cortex.get_collection_members(self._eidolon_set(suffix))
            if self.cortex.check_access(k, self.allowed_scopes)
        ]

    def _register(self, key: str, subset_suffix: Optional[str] = None) -> None:
        """Register an atom in the eidolon content set and optional subset."""
        self.cortex.add_to_set(self._eidolon_set(), key)
        if subset_suffix:
            self.cortex.add_to_set(self._eidolon_set(subset_suffix), key)

    # ------------------------------------------------------------------
    # Operators
    # ------------------------------------------------------------------

    def op_new(self, name: str, location_type: str) -> Dict[str, Any]:
        """Manifest a new spatial location (world, city, facility, etc.)."""
        author_id, scopes = self._author_and_scopes()
        root_id = self.cortex.put_chunk(
            content=f"[ Eidolon: {name} ({location_type}) ]",
            meta={
                "type": "concept", "concept": "eidolon", "role": "root",
                "name": name, "location_type": location_type,
                "created_at": time.time(),
            },
            author=author_id, scopes=scopes,
        )
        self.concept_id = root_id
        self.set_name = f"set:concept:{self.concept_id}"

        # B1: create all sets before writes
        self.cortex.create_set(self.set_name)
        self.cortex.create_set(self._eidolon_set())
        self.cortex.create_set(self._eidolon_set("sub_locations"))
        self.cortex.create_set(self._eidolon_set("occupants"))
        self.cortex.create_set(INDEX_SET)

        # Root → content set only (Two-Namespace Rule)
        self.cortex.add_to_set(self._eidolon_set(), root_id)
        self.cortex.add_to_set(INDEX_SET, root_id)

        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, root_id)
        return {"status": "manifested", "concept_id": root_id, "name": name,
                "location_type": location_type}

    def op_open(self, eidolon_id: str) -> Dict[str, Any]:
        """Activate an existing spatial location."""
        self._require_access(eidolon_id, "Eidolon atom")
        self.concept_id = eidolon_id
        self.set_name = f"set:concept:{self.concept_id}"
        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, eidolon_id)
        return {"status": "opened", "concept_id": eidolon_id}

    def op_list_all(self) -> Dict[str, Any]:
        """List all Eidolon root atoms."""
        members = self.cortex.get_collection_members(INDEX_SET)
        visible = [k for k in members if self.cortex.check_access(k, self.allowed_scopes)]
        return {"status": "listed", "items": visible, "count": len(visible)}

    def op_link_location(self, child_location_id: str) -> Dict[str, Any]:
        """Connect locations hierarchically (this location is the parent, child_location_id is the child)."""
        self._require_concept()
        self._require_access(child_location_id, "Child location atom")
        author_id, _ = self._author_and_scopes()

        # Bidirectional topology links
        self.cortex.put_link(self.concept_id, child_location_id, "sys:contains",
                             author=author_id)
        self.cortex.put_link(child_location_id, self.concept_id, "sys:located_in",
                             author=author_id)
        self._register(child_location_id, "sub_locations")
        return {"status": "linked", "parent": self.concept_id, "child": child_location_id}

    def op_move(self, actor_id: str) -> Dict[str, Any]:
        """Move an actor (Soma/Engram) into this location. Always cleans up the previous location."""
        self._require_concept()
        self._require_access(actor_id, "Actor atom")
        author_id, _ = self._author_and_scopes()

        old_locations = self.cortex.get_adjacent_links(actor_id, "sys:located_in")
        for old_loc_id, _ in old_locations:
            self.cortex.remove_link(actor_id, old_loc_id, "sys:located_in")
            self.cortex.remove_from_set(f"set:eidolon:{old_loc_id}:occupants", actor_id)
            self.cortex.remove_from_set(f"set:eidolon:{old_loc_id}", actor_id)

        self.cortex.put_link(actor_id, self.concept_id, "sys:located_in", author=author_id)
        self._register(actor_id, "occupants")
        return {"status": "moved", "actor": actor_id, "destination": self.concept_id}

    def op_map(self) -> Dict[str, Any]:
        """Return the topology map of this location."""
        self._require_concept()
        meta = self.cortex.get_meta(self.concept_id) or {}
        sub_locations = self._visible_members("sub_locations")
        occupants = self._visible_members("occupants")
        return {
            "status": "mapped",
            "concept_id": self.concept_id,
            "name": meta.get("name", ""),
            "location_type": meta.get("location_type", ""),
            "sub_locations": sub_locations,
            "occupants": occupants,
        }

    def op_delete(self) -> Dict[str, Any]:
        """Soft-delete the location root."""
        self._require_concept()
        author_id, _ = self._author_and_scopes()
        self.cortex.remove_from_set(INDEX_SET, self.concept_id)
        return {"status": "deleted", "concept_id": self.concept_id}
