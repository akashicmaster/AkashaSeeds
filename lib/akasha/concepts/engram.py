"""
EngramConcept — a client's persistent alter-ego / companion bot.

An Engram is NOT just a game avatar. It is a first-class Akasha agent tied to
a client's identity. It persists in the graph and can operate autonomously while
the client is offline ("go do this while I'm away" — secretary mode).

Two roles:
  1. Companion bot — lives alongside the client across all of Akasha at all times,
                     regardless of whether the game is running.
  2. Game proxy    — can be loaded into a Soma (mech frame) and deployed into the
                     Homonoia game world as the client's in-game representative.

Async / offline operation is handled by Akasha's pending_links / DTN mechanism,
not by Harmonia. Harmonia (lib/harmonia/) is JCL infrastructure and is unrelated
to Engram's autonomous behaviour.
Part of the Homonoia game world (see homonoia.py).

Subsets:
    memories — utterance/memory atoms recorded by op_talk
    bonds    — resonance link atoms recorded by op_bond
"""
import time
from typing import Any, Dict, List, Optional

from lib.akasha.concepts.base import BaseConcept

CONTEXT_KEY_ACTIVE = "active_engram_root"
INDEX_SET = "set:engram:index"


class EngramConcept(BaseConcept):
    """Psyche (engram) model. Handles memories, resonance bonds, utterances, and metaphors."""

    CONCEPT_PREFIX = "engram"
    CONTEXT_KEY_ACTIVE = CONTEXT_KEY_ACTIVE  # Required for SpaceConcept focus routing

    CONCEPT_METHODS = {
        "new":      {"op": "op_new"},
        "talk":     {"op": "op_talk"},
        "bond":     {"op": "op_bond"},
        "metaphor": {"op": "op_generate_metaphor"},
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

    def _engram_set(self, suffix: Optional[str] = None) -> str:
        base = f"set:engram:{self.concept_id}"
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
            k for k in self.cortex.get_collection_members(self._engram_set(suffix))
            if self.cortex.check_access(k, self.allowed_scopes)
        ]

    # ------------------------------------------------------------------
    # Operators
    # ------------------------------------------------------------------

    def op_new(self, name: str) -> Dict[str, Any]:
        if not name:
            raise ValueError("engram.new requires name.")
        author_id, scopes = self._get_author_and_scopes()
        root_id = self.cortex.put_chunk(
            content=f"[ Engram: {name} ]",
            meta={
                "type": "concept", "concept": "engram", "role": "root",
                "name": name, "created_at": time.time(),
            },
            author=author_id, scopes=scopes,
        )
        self.concept_id = root_id
        self.set_name = f"set:concept:{self.concept_id}"

        # B1: create all sets before writes
        self.cortex.create_set(self.set_name)
        self.cortex.create_set(self._engram_set())
        self.cortex.create_set(self._engram_set("memories"))
        self.cortex.create_set(self._engram_set("bonds"))
        self.cortex.create_set(INDEX_SET)

        # Root → content set only (Two-Namespace Rule)
        self.cortex.add_to_set(self._engram_set(), root_id)
        self.cortex.add_to_set(INDEX_SET, root_id)

        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, root_id)
        return {"status": "created", "concept_id": root_id, "engram_id": root_id, "name": name}

    def op_talk(self, text: str, mood: str = "neutral") -> Dict[str, Any]:
        """Record an utterance or memory."""
        self._require_concept()
        if not text:
            raise ValueError("engram.talk requires text.")
        author_id, scopes = self._get_author_and_scopes()
        key = self.cortex.put_chunk(
            content=text,
            meta={
                "type": "engram_memory",
                "mood": mood,
                "engram_id": self.concept_id,
                "created_at": time.time(),
            },
            author=author_id, scopes=scopes,
        )
        self.cortex.add_to_set(self._engram_set(), key)
        self.cortex.add_to_set(self._engram_set("memories"), key)
        self.cortex.put_link(self.concept_id, key, "har:said", author=author_id)
        return {"status": "recorded", "memory_id": key, "mood": mood}

    def op_bond(self, target_engram_id: str, resonance_boost: float = 1.0) -> Dict[str, Any]:
        """Record a resonance bond to another psyche. resonance_boost is stored as the link weight."""
        self._require_concept()
        self._require_access(target_engram_id, "Target Engram atom")
        author_id, scopes = self._get_author_and_scopes()

        clamped = max(0.0, min(1.0, float(resonance_boost)))

        # Bond event atom — event-sourcing: each call appends, never overwrites
        bond_key = self.cortex.put_chunk(
            content=f"bond:{self.concept_id[:8]}->{target_engram_id[:8]}",
            meta={
                "type": "engram_bond",
                "resonance_boost": clamped,
                "from": self.concept_id,
                "to": target_engram_id,
                "created_at": time.time(),
            },
            author=author_id, scopes=scopes,
        )
        self.cortex.add_to_set(self._engram_set(), bond_key)
        self.cortex.add_to_set(self._engram_set("bonds"), bond_key)
        self.cortex.put_link(self.concept_id, target_engram_id, "har:resonance",
                             w=clamped, author=author_id)
        self.cortex.put_link(self.concept_id, bond_key, "har:has_bond", author=author_id)
        return {"status": "bonded", "bond_id": bond_key, "target": target_engram_id,
                "added_weight": clamped}

    def op_generate_metaphor(self, target_user_context: str, location_id: str) -> Dict[str, Any]:
        """Generate a metaphor message and attach it to the given location. Written with public scope."""
        self._require_concept()
        self._require_access(location_id, "Location atom")
        author_id, _ = self._get_author_and_scopes()

        generated_text = f"(A soliloquy hinting at '{target_user_context}', unclear to whom it is addressed)"
        scopes = [f"owner:user_{author_id}", "view:public"]

        msg_id = self.cortex.put_chunk(
            content=generated_text,
            meta={
                "type": "engram_message", "role": "speech",
                "is_metaphor": True, "engram_id": self.concept_id,
                "created_at": time.time(),
            },
            author=author_id, scopes=scopes,
        )
        self.cortex.add_to_set(self._engram_set(), msg_id)
        self.cortex.put_link(self.concept_id, msg_id, "sys:speaks", author=author_id)
        self.cortex.put_link(msg_id, location_id, "sys:located_in", author=author_id)
        return {"status": "metaphor_cast", "msg_id": msg_id}
