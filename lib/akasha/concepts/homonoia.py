"""
HomonioaConcept — city model for the game world Homonoia.

Homonoia (ὁμόνοια) — Greek: "unanimity, concord, living in harmony together."
A fictional city-state where all residents coexist in mutual accord; the primary
setting of a network-game built on the Akasha platform.

NAMING — THREE DISTINCT THINGS, DO NOT CONFUSE:
  1. Homonoia (this file)     — the fictional in-game city; a concept model in Akasha.
  2. Harmonia (lib/harmonia/) — a JCL orchestration library (plugin dispatch,
                                transactional workspaces, execution logging).
                                It is general-purpose infrastructure, NOT a game engine.
                                The library was named after this city, but they are
                                architecturally unrelated.
  3. Akasha (lib/akasha/)     — the knowledge-graph platform the game runs on.
                                Homonoia uses Akasha's session, IAM, GroupEngine, and
                                pending_links as its multiplayer infrastructure.

This concept model represents Homonoia the city as a semantic object within
Akasha: its districts, factions, laws, and historical events.

Game entity models that operate within this world:
    soma.py     — mech frame; becomes operational when an Engram is loaded into it
    engram.py   — a client's persistent alter-ego / companion bot; exists in Akasha
                  even when the client is offline; can be deployed into a Soma as
                  a proxy agent ("go do this while I'm away")
    operator.py — tactician who pairs with a Soma/Engram to direct combat
    eidolon.py  — the dark outer world surrounding Homonoia; invisible, malevolent;
                  design in progress

Game infrastructure note:
    Multiplayer is handled by Akasha's AkashaSession / GroupEngine.
    Async agent handoff (Engram acting while client is offline) uses pending_links / DTN.
    Harmonia (lib/harmonia/) may be used as JCL plumbing inside the game runtime,
    but it is NOT the game engine and has no game-specific knowledge.

Atom namespace:  homonoia:*
Index set:       set:homonoia:index
Context key:     active_homonoia_root
"""

import time
import logging
from typing import Any, Dict, List, Optional

from lib.akasha.concepts.base import BaseConcept

logger = logging.getLogger("Homonoia.Concept.City")

CONTEXT_KEY_ACTIVE = "active_homonoia_root"
INDEX_SET           = "set:homonoia:index"

_SUBSETS = ["districts", "factions", "laws", "events"]

_SUBSET_RELATION = {
    "districts": "homonoia:has_district",
    "factions":  "homonoia:has_faction",
    "laws":      "homonoia:has_law",
    "events":    "homonoia:has_event",
}


class HomonioaConcept(BaseConcept):
    """
    City model for Homonoia.

    Tracks the structural, social, and historical state of the city.
    Each HomonoiaRoot atom anchors a sub-graph of districts, factions,
    laws, and events.
    """

    CONCEPT_PREFIX     = "homonoia"
    CONTEXT_KEY_ACTIVE = CONTEXT_KEY_ACTIVE

    CONCEPT_METHODS = {
        "new":          {"op": "op_new"},
        "open":         {"op": "op_open"},
        "ls":           {"op": "op_list_all"},
        "map":          {"op": "op_map"},
        "rm":           {"op": "op_delete"},
        "district.add": {"op": "op_add_district"},
        "faction.add":  {"op": "op_add_faction"},
        "law.add":      {"op": "op_add_law"},
        "event.add":    {"op": "op_add_event"},
        "profile":      {"op": "op_profile"},
        "diagnose":     {"op": "op_diagnose"},
    }

    def __init__(self, session: Any, concept_id: Optional[str] = None):
        super().__init__(session, concept_id)
        if not self.concept_id:
            stored = getattr(self.session, "get_context", lambda k: None)(CONTEXT_KEY_ACTIVE)
            if stored:
                self.concept_id = stored
                self.set_name = f"set:concept:{self.concept_id}"

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _city_set(self, suffix: Optional[str] = None) -> str:
        base = f"set:homonoia:{self.concept_id}"
        return f"{base}:{suffix}" if suffix else base

    def _author_and_scopes(self):
        author_id = getattr(self.session, "client_id", "system")
        scopes = [f"owner:user_{author_id}", f"view:user_{author_id}"]
        return author_id, scopes

    def _create_sets(self) -> None:
        self.ensure_concept_set()
        self.cortex.create_set(self._city_set())
        for s in _SUBSETS:
            self.cortex.create_set(self._city_set(s))
        self.cortex.create_set(INDEX_SET)

    def _require_active(self) -> str:
        if not self.concept_id:
            raise RuntimeError("No active Homonoia city. Use homonoia.open or homonoia.new first.")
        return self.concept_id

    def _members(self, subset: str) -> List[str]:
        return [
            k for k in self.cortex.get_collection_members(self._city_set(subset))
            if self.cortex.check_access(k, self.allowed_scopes)
        ]

    def _put_atom(self, content: str, atom_type: str, subset: str,
                  meta_extra: Optional[Dict[str, Any]] = None) -> str:
        root_id = self._require_active()
        author_id, scopes = self._author_and_scopes()
        meta = {"type": atom_type, "concept": "homonoia",
                "root_id": root_id, "created_at": time.time()}
        if meta_extra:
            meta.update(meta_extra)
        key = self.cortex.put_chunk(content=content, meta=meta,
                                    author=author_id, scopes=scopes)
        self.cortex.add_to_set(self._city_set(), key)
        self.cortex.add_to_set(self._city_set(subset), key)
        rel = _SUBSET_RELATION.get(subset, f"homonoia:has_{subset}")
        self.cortex.put_link(root_id, key, rel, author=author_id)
        return key

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def op_new(self, name: str, description: str = "") -> Dict[str, Any]:
        """Create a new Homonoia city root."""
        author_id, scopes = self._author_and_scopes()
        root_id = self.cortex.put_chunk(
            content=f"[ Homonoia: {name} ]",
            meta={"type": "concept", "concept": "homonoia", "role": "root",
                  "name": name, "description": description, "created_at": time.time()},
            author=author_id, scopes=scopes,
        )
        self.concept_id = root_id
        self.set_name = f"set:concept:{self.concept_id}"
        self._create_sets()
        self.cortex.add_to_set(self._city_set(), root_id)
        self.cortex.add_to_set(INDEX_SET, root_id)
        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, root_id)
        logger.info("[HomonioaConcept] Created '%s' (%s)", name, root_id[:8])
        return {"status": "created", "concept_id": root_id, "name": name}

    def op_open(self, homonoia_id: str) -> Dict[str, Any]:
        """Mount an existing Homonoia city as the session's active city."""
        meta = self.cortex.get_meta(homonoia_id)
        if not meta:
            raise RuntimeError(f"Homonoia city not found: {homonoia_id}")
        self.concept_id = homonoia_id
        self.set_name = f"set:concept:{self.concept_id}"
        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, homonoia_id)
        return {"concept_id": homonoia_id, "name": meta.get("name", "?")}

    def op_list_all(self) -> List[Dict[str, Any]]:
        """List all Homonoia city roots accessible in this session."""
        ids = self.cortex.get_collection_members(INDEX_SET) or []
        result = []
        for cid in ids:
            if self.cortex.check_access(cid, self.allowed_scopes):
                m = self.cortex.get_meta(cid) or {}
                result.append({"id": cid, "name": m.get("name", "?"),
                                "description": m.get("description", "")})
        return result

    def op_map(self) -> Dict[str, Any]:
        """Return the structural inventory of the active Homonoia city."""
        root_id = self._require_active()
        meta = self.cortex.get_meta(root_id) or {}
        return {
            "concept_id": root_id,
            "name":       meta.get("name", "?"),
            "districts":  self._members("districts"),
            "factions":   self._members("factions"),
            "laws":       self._members("laws"),
            "events":     self._members("events"),
        }

    def op_delete(self) -> Dict[str, Any]:
        """Remove the active Homonoia city from the index and clear session context."""
        root_id = self._require_active()
        self.cortex.remove_from_set(INDEX_SET, root_id)
        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, None)
        self.concept_id = None
        return {"deleted": root_id}

    # ── City structure ────────────────────────────────────────────────────────

    def op_add_district(self, name: str, district_type: str = "residential",
                        description: str = "") -> Dict[str, Any]:
        """Add a district (quarter, ward, zone) to the active city."""
        key = self._put_atom(
            content=f"[District] {name}",
            atom_type="homonoia_district",
            subset="districts",
            meta_extra={"name": name, "district_type": district_type,
                        "description": description},
        )
        return {"district_id": key, "name": name, "district_type": district_type}

    def op_add_faction(self, name: str, faction_type: str = "civic",
                       description: str = "") -> Dict[str, Any]:
        """Add a social faction or organisation active in the city."""
        key = self._put_atom(
            content=f"[Faction] {name}",
            atom_type="homonoia_faction",
            subset="factions",
            meta_extra={"name": name, "faction_type": faction_type,
                        "description": description},
        )
        return {"faction_id": key, "name": name, "faction_type": faction_type}

    def op_add_law(self, title: str, law_type: str = "ordinance",
                   content: str = "", status: str = "active") -> Dict[str, Any]:
        """Record a city law, charter clause, or ordinance."""
        key = self._put_atom(
            content=f"[Law] {title}",
            atom_type="homonoia_law",
            subset="laws",
            meta_extra={"title": title, "law_type": law_type,
                        "content": content, "status": status},
        )
        return {"law_id": key, "title": title, "law_type": law_type}

    def op_add_event(self, description: str, event_type: str = "civic",
                     occurred_at: str = "") -> Dict[str, Any]:
        """Record a historical or ongoing city event."""
        key = self._put_atom(
            content=f"[Event] {description[:80]}",
            atom_type="homonoia_event",
            subset="events",
            meta_extra={"description": description, "event_type": event_type,
                        "occurred_at": occurred_at},
        )
        return {"event_id": key, "event_type": event_type}

    # ── Views ─────────────────────────────────────────────────────────────────

    def op_profile(self) -> Dict[str, Any]:
        """Show the full profile of the active Homonoia city."""
        inv = self.op_map()

        def _enrich(ids):
            out = []
            for cid in ids:
                m = self.cortex.get_meta(cid) or {}
                out.append({"id": cid, **{k: v for k, v in m.items()
                                          if k not in ("root_id", "concept", "created_at")}})
            return out

        return {**inv,
                "districts": _enrich(inv["districts"]),
                "factions":  _enrich(inv["factions"]),
                "laws":      _enrich(inv["laws"]),
                "events":    _enrich(inv["events"])}

    def op_diagnose(self) -> Dict[str, Any]:
        """Report structural gaps in the active Homonoia city model."""
        inv = self.op_map()
        issues = []
        if not inv["districts"]:
            issues.append("No districts defined — city has no spatial structure")
        if not inv["factions"]:
            issues.append("No factions defined — social dynamics unmodelled")
        if not inv["laws"]:
            issues.append("No laws defined — civic charter empty")
        return {
            "concept_id":  inv["concept_id"],
            "name":        inv["name"],
            "issues":      issues,
            "district_ct": len(inv["districts"]),
            "faction_ct":  len(inv["factions"]),
            "law_ct":      len(inv["laws"]),
            "event_ct":    len(inv["events"]),
        }
