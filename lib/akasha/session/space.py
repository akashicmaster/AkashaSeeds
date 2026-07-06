"""
SessionSpace — Session Instance Layer.

A client's semantic session is a virtual space: a Cortex atom that acts
as the root of a SET of concept model instances.  Ownership and location
are deliberately separated:

  LOCATION  = set membership  (set:space:{space_id}:slots)
              A slot atom can belong to multiple spaces simultaneously.
              Example: a CastConcept borrowed into a StageEncounter is
              a member of both the owner's space and the stage's space.

  OWNERSHIP = semantic link type from the SpaceRoot to the slot atom
              space:owns     — this space created and controls the instance
              space:contains — this space references an externally-owned instance

Cortex topology:

  SpaceRoot  (concept="space", role="root", client_id=...)
    │
    ├─ space:owns     ──▶  SlotAtom  {slot, model, concept_id}
    │                          └─ space:instance ──▶  ConceptRoot
    │
    └─ space:contains ──▶  SlotAtom  {slot, model, concept_id}
                               └─ space:instance ──▶  ConceptRoot (owned elsewhere)

Sets:
  set:space:index          — global index of all space roots
  set:space:{id}           — all atoms owned by this space
  set:space:{id}:slots     — slot atoms only

Session context keys managed:
  active_space_root        — SpaceRoot atom id
  space_focus              — dict: model_prefix → slot_name  (focus routing table)

Focus mechanism:
  When instance.focus(slot="bot") is called, SpaceConcept reads the slot's
  model prefix and calls session.set_context(model.CONTEXT_KEY_ACTIVE, concept_id).
  This means all existing concept model dispatch continues to work unchanged —
  CastConcept still reads "active_cast_root" from session context; SpaceConcept
  is simply the authority that sets it.
"""

import inspect
import logging
import time
from typing import Any, Dict, List, Optional

from lib.akasha.concepts.base import BaseConcept

logger = logging.getLogger("Harmonia.Session.Space")

CONCEPT_KEY_ACTIVE = "active_space_root"
INDEX_SET = "set:space:index"

# Injected by kernel at startup — avoids circular import.
_registry = None


def set_registry(reg) -> None:
    global _registry
    _registry = reg


def _filter(op, kwargs: Dict[str, Any]) -> Dict[str, Any]:
    try:
        valid = set(inspect.signature(op).parameters) - {"self"}
        return {k: v for k, v in kwargs.items() if k in valid}
    except Exception:
        return dict(kwargs)


class SpaceConcept(BaseConcept):
    """
    Session virtual space — contains instantiated concept model instances.
    Manages ownership (space:owns / space:contains) and routing focus.
    """

    CONCEPT_PREFIX = "instance"
    CONCEPT_METHODS = {
        "mount":   {"op": "op_mount"},
        "join":    {"op": "op_join"},
        "focus":   {"op": "op_focus"},
        "blur":    {"op": "op_blur"},
        "bind":    {"op": "op_bind"},
        "ls":      {"op": "op_list"},
        "unmount": {"op": "op_unmount"},
    }

    def __init__(self, session: Any):
        super().__init__(session)
        stored = getattr(self.session, "get_context", lambda k: None)(CONCEPT_KEY_ACTIVE)
        if stored:
            self.concept_id = stored

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ctx(self, key: str, default: Any = None) -> Any:
        return getattr(self.session, "get_context", lambda k, d=None: d)(key, default)

    def _set_ctx(self, key: str, value: Any) -> None:
        if hasattr(self.session, "set_context"):
            self.session.set_context(key, value)

    def _author_and_scopes(self):
        author_id = getattr(self.session, "client_id", "system")
        return author_id, [f"owner:user_{author_id}", f"view:user_{author_id}"]

    def _get_or_create_space(self) -> str:
        """Lazily create the SpaceRoot atom on first use."""
        if self.concept_id:
            return self.concept_id

        author_id, scopes = self._author_and_scopes()
        root_id = self.cortex.put_chunk(
            content=f"[ Space: {author_id} ]",
            meta={
                "type": "concept",
                "concept": "space",
                "role": "root",
                "client_id": author_id,
                "created_at": time.time(),
            },
            author=author_id,
            scopes=scopes,
        )
        self.concept_id = root_id
        self.set_name = f"set:concept:{root_id}"
        self.cortex.create_set(f"set:space:{root_id}")
        self.cortex.create_set(f"set:space:{root_id}:slots")
        self.cortex.create_set(INDEX_SET)
        self.cortex.add_to_set(INDEX_SET, root_id)
        self._set_ctx(CONCEPT_KEY_ACTIVE, root_id)
        logger.info("[SpaceConcept] Space created for '%s' (%s)", author_id, root_id[:8])
        return root_id

    def _slot_atoms(self) -> List[Dict[str, Any]]:
        if not self.concept_id:
            return []
        members = self.cortex.get_collection_members(
            f"set:space:{self.concept_id}:slots"
        )
        result = []
        for atom_id in members:
            meta = self.cortex.get_meta(atom_id) or {}
            if meta.get("type") == "space_slot":
                result.append({"id": atom_id, "meta": meta})
        return result

    def _find_slot(self, slot: str) -> Optional[Dict[str, Any]]:
        for s in self._slot_atoms():
            if s["meta"].get("slot") == slot:
                return s
        return None

    def _write_slot(
        self, slot: str, model: str, concept_id: str, relation: str
    ) -> str:
        """Write a SlotAtom, add it to the space's sets, and link from SpaceRoot."""
        space_id = self._get_or_create_space()
        author_id, scopes = self._author_and_scopes()
        slot_id = self.cortex.put_chunk(
            content=f"[ Slot: {slot} / {model} ]",
            meta={
                "type": "space_slot",
                "concept": "space",
                "slot": slot,
                "model": model,
                "concept_id": concept_id,
                "created_at": time.time(),
            },
            author=author_id,
            scopes=scopes,
        )
        self.cortex.add_to_set(f"set:space:{space_id}", slot_id)
        self.cortex.add_to_set(f"set:space:{space_id}:slots", slot_id)
        # Link: SpaceRoot --{owns|contains}--> SlotAtom --instance--> ConceptRoot
        self.cortex.put_link(space_id, slot_id, relation, author=author_id)
        self.cortex.put_link(slot_id, concept_id, "space:instance", author=author_id)
        return slot_id

    def _get_focus(self) -> Dict[str, str]:
        return self._ctx("space_focus", {}) or {}

    def _apply_focus(self, model: str, slot: str, concept_id: str) -> None:
        """Update focus map and set the model's own context key."""
        focus = self._get_focus()
        focus[model] = slot
        self._set_ctx("space_focus", focus)
        if _registry:
            cls = _registry.get_class(model)
            ctx_key = getattr(cls, "CONTEXT_KEY_ACTIVE", None) if cls else None
            if ctx_key:
                self._set_ctx(ctx_key, concept_id)

    def _clear_focus(self, model: str) -> Optional[str]:
        """Clear focus for model; returns old slot name."""
        focus = self._get_focus()
        slot = focus.pop(model, None)
        self._set_ctx("space_focus", focus)
        if _registry:
            cls = _registry.get_class(model)
            ctx_key = getattr(cls, "CONTEXT_KEY_ACTIVE", None) if cls else None
            if ctx_key:
                self._set_ctx(ctx_key, None)
        return slot

    def _resolve_plugin(self, model: str):
        if not _registry:
            raise RuntimeError("SpaceConcept: registry not initialised.")
        cls = _registry.get_class(model)
        if not cls:
            raise RuntimeError(f"Unknown concept model: '{model}'.")
        return cls

    # ------------------------------------------------------------------
    # Operators
    # ------------------------------------------------------------------

    def op_mount(
        self,
        model: str,
        slot: str,
        id: str = "",
        name: str = "",
        **kwargs,
    ) -> Dict[str, Any]:
        """[instance.mount] Mount a concept model instance into this space (space:owns)."""
        if not model or not slot:
            raise ValueError("model and slot are required.")
        if self._find_slot(slot):
            raise RuntimeError(
                f"Slot '{slot}' is already occupied. Use instance.unmount first."
            )

        cls = self._resolve_plugin(model)

        if id:
            # Mount an existing instance — validate access via op_open
            instance = cls(self.session, concept_id=id)
            instance.op_open(id)
            concept_id = id
        else:
            # Create a new instance
            instance = cls(self.session)
            op_new = getattr(instance, "op_new")
            params = _filter(op_new, {"name": name or slot, **kwargs})
            result = op_new(**params)
            concept_id = result.get("concept_id") or result.get(f"{model}_id")
            if not concept_id:
                raise RuntimeError(
                    f"op_new for '{model}' did not return a concept_id."
                )

        self._write_slot(slot, model, concept_id, "space:owns")

        # Auto-focus if this is the first instance of this model class
        focus = self._get_focus()
        auto_focused = model not in focus
        if auto_focused:
            self._apply_focus(model, slot, concept_id)

        logger.info(
            "[SpaceConcept] Mounted %s '%s' (id=%s, focused=%s)",
            model, slot, concept_id[:8], auto_focused,
        )
        return {
            "status": "mounted",
            "slot": slot,
            "model": model,
            "concept_id": concept_id,
            "relation": "space:owns",
            "focused": auto_focused,
        }

    def op_join(
        self,
        concept_id: str,
        slot: str,
        model: str = "",
    ) -> Dict[str, Any]:
        """[instance.join] Borrow an externally-owned instance into this space (space:contains).

        The instance is added to this space's slot set but ownership remains elsewhere.
        Use this for StageEncounter participation: another client's cast enters
        your space without transferring control.
        """
        if not concept_id or not slot:
            raise ValueError("concept_id and slot are required.")
        if self._find_slot(slot):
            raise RuntimeError(f"Slot '{slot}' is already occupied.")

        if not model:
            meta = self.cortex.get_meta(concept_id) or {}
            model = meta.get("concept", "")
        if not model:
            raise ValueError(
                "Cannot detect model type from atom metadata. Provide model parameter."
            )

        self._write_slot(slot, model, concept_id, "space:contains")
        logger.info(
            "[SpaceConcept] Joined %s '%s' (id=%s)", model, slot, concept_id[:8]
        )
        return {
            "status": "joined",
            "slot": slot,
            "model": model,
            "concept_id": concept_id,
            "relation": "space:contains",
        }

    def op_focus(self, slot: str) -> Dict[str, Any]:
        """[instance.focus] Route a model class's commands to the given slot."""
        s = self._find_slot(slot)
        if not s:
            raise RuntimeError(f"Slot '{slot}' not found in this space.")
        model = s["meta"]["model"]
        concept_id = s["meta"]["concept_id"]
        self._apply_focus(model, slot, concept_id)
        return {
            "status": "focused",
            "slot": slot,
            "model": model,
            "concept_id": concept_id,
        }

    def op_blur(self, model: str) -> Dict[str, Any]:
        """[instance.blur] Clear routing focus for a model class."""
        if not model:
            raise ValueError("model is required.")
        old_slot = self._clear_focus(model)
        return {
            "status": "blurred",
            "model": model,
            "was_slot": old_slot,
        }

    def op_bind(self, slot: str, atom: str) -> Dict[str, Any]:
        """[instance.bind] Link a mounted instance to its ontology atom via instance_of.

        Creates the link: concept_root --instance_of--> atom

        This is the explicit form of the abstract/concrete distinction: the target
        atom is treated as the abstract schema (proto-word or type); the mounted
        instance is its concrete operational embodiment.  Outside of proto-words and
        namespace-qualified terms this is a convention, not an enforced invariant —
        see CLAUDE.md "Known Architectural Tensions".
        """
        if not slot or not atom:
            raise ValueError("slot and atom are required.")
        s = self._find_slot(slot)
        if not s:
            raise RuntimeError(f"Slot '{slot}' not found in this space.")
        concept_id = s["meta"]["concept_id"]
        model      = s["meta"]["model"]

        # Resolve alias first (e.g. "icarus" → proto-word key), fall back to raw value
        resolved = self.cortex.resolve_alias(atom) or atom

        author_id, _ = self._author_and_scopes()
        self.cortex.put_link(concept_id, resolved, "instance_of", author=author_id)
        logger.info("[SpaceConcept] Bound %s '%s' (id=%s) → %s", model, slot, concept_id[:8], resolved[:14])
        return {
            "status":     "bound",
            "slot":       slot,
            "model":      model,
            "concept_id": concept_id,
            "atom":       resolved,
            "relation":   "instance_of",
        }

    def op_list(self) -> Dict[str, Any]:
        """[instance.ls] List all instances in this space."""
        focus = self._get_focus()
        slots = []
        for s in self._slot_atoms():
            meta = s["meta"]
            slot = meta.get("slot")
            slots.append({
                "slot": slot,
                "model": meta.get("model"),
                "concept_id": meta.get("concept_id"),
                "relation": meta.get("relation", ""),
                "focused": focus.get(meta.get("model")) == slot,
            })
        return {
            "space_id": self.concept_id,
            "instances": slots,
            "focus": focus,
        }

    def op_unmount(self, slot: str) -> Dict[str, Any]:
        """[instance.unmount] Remove a slot from this space without deleting the instance."""
        s = self._find_slot(slot)
        if not s:
            raise RuntimeError(f"Slot '{slot}' not found in this space.")
        model = s["meta"]["model"]
        concept_id = s["meta"]["concept_id"]
        space_id = self.concept_id

        # Clear focus if this slot was focused
        focus = self._get_focus()
        if focus.get(model) == slot:
            self._clear_focus(model)

        # Remove slot atom from space's sets (soft remove — atom stays in Cortex)
        self.cortex.remove_from_set(f"set:space:{space_id}:slots", s["id"])
        self.cortex.remove_from_set(f"set:space:{space_id}", s["id"])

        logger.info(
            "[SpaceConcept] Unmounted %s '%s' (id=%s)", model, slot, concept_id[:8]
        )
        return {
            "status": "unmounted",
            "slot": slot,
            "model": model,
            "concept_id": concept_id,
        }
