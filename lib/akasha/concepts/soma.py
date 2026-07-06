"""
SomaConcept — mech frame (physical body).
Manages slot constraints, capacity budget, and damage state.
Part of the Homonoia game world (see homonoia.py).
"""
import time
from typing import Any, Dict, List, Optional

from lib.akasha.concepts.base import BaseConcept

CONTEXT_KEY_ACTIVE = "active_soma_root"
INDEX_SET = "set:soma:index"

SOMA_SLOTS: Dict[str, int] = {
    "head": 1, "arm_r": 1, "arm_l": 1,
    "core": 1, "booster": 2, "weapon": 3,
}


class SomaConcept(BaseConcept):
    """Mech frame (physical body) model. Handles part equipping, status management, and repair."""

    CONCEPT_PREFIX = "soma"
    CONTEXT_KEY_ACTIVE = CONTEXT_KEY_ACTIVE  # Required for SpaceConcept focus routing

    CONCEPT_METHODS = {
        "new":    {"op": "op_new"},
        "equip":  {"op": "op_equip"},
        "status": {"op": "op_status"},
        "repair": {"op": "op_repair"},
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

    def _soma_set(self, suffix: Optional[str] = None) -> str:
        base = f"set:soma:{self.concept_id}"
        return f"{base}:{suffix}" if suffix else base

    def _get_author_and_scopes(self):
        author_id = getattr(self.session, "client_id", "system")
        return author_id, [f"owner:user_{author_id}", f"view:user_{author_id}"]

    def _require_access(self, atom_id: str, label: str = "Atom") -> None:
        if not atom_id:
            raise ValueError(f"{label} id is required.")
        if not self.cortex.check_access(atom_id, self.allowed_scopes):
            raise RuntimeError(f"{label} not accessible: {atom_id[:12]}")

    def _visible_members(self, suffix: str) -> List[str]:
        return [
            k for k in self.cortex.get_collection_members(self._soma_set(suffix))
            if self.cortex.check_access(k, self.allowed_scopes)
        ]

    def _register(self, key: str, subset_suffix: Optional[str] = None) -> None:
        """Register an atom in the soma content set and optional subset."""
        self.cortex.add_to_set(self._soma_set(), key)
        if subset_suffix:
            self.cortex.add_to_set(self._soma_set(subset_suffix), key)

    # ------------------------------------------------------------------
    # Operators
    # ------------------------------------------------------------------

    def op_new(self, name: str, max_capacity: int = 100) -> Dict[str, Any]:
        if not name:
            raise ValueError("soma.new requires name.")
        author_id, scopes = self._get_author_and_scopes()
        root_id = self.cortex.put_chunk(
            content=f"[ Soma: {name} ]",
            meta={
                "type": "concept", "concept": "soma", "role": "root",
                "name": name, "status": "active",
                "max_capacity": max_capacity,
                "created_at": time.time(),
            },
            author=author_id, scopes=scopes,
        )
        self.concept_id = root_id
        self.set_name = f"set:concept:{self.concept_id}"

        # B1: create all sets before writes
        self.cortex.create_set(self.set_name)
        self.cortex.create_set(self._soma_set())
        self.cortex.create_set(self._soma_set("equipment"))
        for slot in SOMA_SLOTS:
            self.cortex.create_set(self._soma_set(f"slot:{slot}"))
        self.cortex.create_set(INDEX_SET)

        # Root → content set only (Two-Namespace Rule)
        self.cortex.add_to_set(self._soma_set(), root_id)
        self.cortex.add_to_set(INDEX_SET, root_id)

        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, root_id)
        return {"status": "constructed", "concept_id": root_id, "soma_id": root_id, "name": name}

    def op_equip(self, part_id: str, slot: str, cost: int = 0) -> Dict[str, Any]:
        self._require_concept()
        if slot not in SOMA_SLOTS:
            raise ValueError(f"Invalid slot '{slot}'. Valid: {list(SOMA_SLOTS.keys())}")
        self._require_access(part_id, "Part atom")

        # Slot capacity enforced via per-slot set membership count
        occupied = len(self.cortex.get_collection_members(self._soma_set(f"slot:{slot}")))
        if occupied >= SOMA_SLOTS[slot]:
            raise RuntimeError(f"Slot '{slot}' is full ({occupied}/{SOMA_SLOTS[slot]}).")

        author_id, _ = self._get_author_and_scopes()
        self._register(part_id, "equipment")
        self.cortex.add_to_set(self._soma_set(f"slot:{slot}"), part_id)
        # cost is stored as link weight for future capacity budgeting
        self.cortex.put_link(self.concept_id, part_id, f"har:equipped:{slot}",
                             w=float(cost), author=author_id)
        return {"status": "equipped", "part_id": part_id, "slot": slot, "cost": cost}

    def op_status(self) -> Dict[str, Any]:
        self._require_concept()
        meta = self.cortex.get_meta(self.concept_id) or {}
        slots_detail = {
            slot: {
                "parts": self._visible_members(f"slot:{slot}"),
                "capacity": cap,
            }
            for slot, cap in SOMA_SLOTS.items()
        }
        return {
            "soma_id":      self.concept_id,
            "name":         meta.get("name", ""),
            "status":       meta.get("status", "unknown"),
            "max_capacity": meta.get("max_capacity", 100),
            "equipment":    self._visible_members("equipment"),
            "slots":        slots_detail,
        }

    def op_repair(self) -> Dict[str, Any]:
        self._require_concept()
        author_id, scopes = self._get_author_and_scopes()
        repair_id = self.cortex.put_chunk(
            content=f"[ Event: Soma {self.concept_id[:8]} Repaired ]",
            meta={
                "type": "event", "event_type": "repair",
                "soma_id": self.concept_id,
                "timestamp": time.time(),
            },
            author=author_id, scopes=scopes,
        )
        self._register(repair_id)
        self.cortex.put_link(self.concept_id, repair_id, "sys:state_change", author=author_id)
        return {"status": "repaired", "soma_id": self.concept_id, "record_id": repair_id}
