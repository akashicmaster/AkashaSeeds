"""
Cockpit Concept Model.

[OPERAND-FIRST DESIGN]
Represents the Observer's Cockpit — a stateful navigational vessel for the Semantic
Cosmos.  It manipulates the session's active scope and focus, and persists the
exploratory wake (beacons / traces) into the Cortex only when explicitly commanded.

Topology:
  - Root atom (concept: "cockpit", role: "root") anchors the vessel in the Cortex.
  - Beacons are content atoms linked to the root via sys:contains and appended to an
    absolute timeline (sys:top → sys:next → sys:bottom) identical to the Note model.
  - Transient state (active_focus, active_axis, active_scope) lives in the session
    context only; it is never written to the Cortex between beacon drops.

Namespace contract (two-namespace rule):
  - Content atoms → set:cockpit:{concept_id}   (cockpit-model scope)
  - All atoms registered in concept catalog → set:concept:{concept_id}
"""

import json
import time
import logging
from typing import List, Dict, Any, Optional

from lib.akasha.concepts.base import BaseConcept

logger = logging.getLogger("Harmonia.Concept.Cockpit")

CONTEXT_KEY_ACTIVE = "active_cockpit_root"


class CockpitConcept(BaseConcept):
    """The Observer's vessel for navigating and annotating the Semantic Cosmos."""

    CONCEPT_PREFIX = "cockpit"
    CONCEPT_METHODS = {
        "new": {
            "op": "op_new",
            "coerce": lambda d: {"name": d.get("name") or d.get("title", "")},
        },
        "open": {"op": "op_open"},
        "ls":   {"op": "op_ls"},
        "lock": {
            "op": "op_lock",
            "coerce": lambda d: {"target_id": d.get("target") or d.get("id", "")},
        },
        "tune": {
            "op": "op_tune_lens",
            "coerce": lambda d: {
                "axis":  d.get("axis") or None,
                "scope": int(d["scope"]) if d.get("scope") is not None else None,
            },
        },
        "beacon": {
            "op": "op_drop_beacon",
            "coerce": lambda d: {"note": d.get("note") or d.get("text", "")},
        },
        "wake":   {"op": "op_wake"},
        "status": {"op": "op_status"},
        "rm":     {"op": "op_delete"},
    }

    def __init__(self, session: Any, concept_id: Optional[str] = None):
        super().__init__(session, concept_id)
        # Auto-mount the last active cockpit from session context
        if not self.concept_id:
            stored = getattr(self.session, "get_context", lambda k: None)(CONTEXT_KEY_ACTIVE)
            if stored:
                self.concept_id = stored
                self.set_name = f"set:concept:{self.concept_id}"

    # ── Private helpers ───────────────────────────────────────────────────────

    def _author_and_scopes(self):
        """Returns (author_id, user_scopes) from the current session."""
        author_id = getattr(self.session, "client_id", "system")
        scopes = [f"owner:user_{author_id}", f"view:user_{author_id}"]
        return author_id, scopes

    def _content_set(self) -> str:
        """Content-scope set for this cockpit (distinct from concept catalog)."""
        return f"set:cockpit:{self.concept_id}"

    def _append_to_timeline(self, node_id: str, author_id: str):
        """Chronological wake of dropped beacons (sys:top → sys:next → sys:bottom)."""
        tail_links = self.cortex.get_adjacent_links(self.concept_id, "sys:bottom")
        if not tail_links:
            self.cortex.put_link(self.concept_id, node_id, "sys:top", author=author_id)
        else:
            last_node_id = tail_links[0][0]
            self.cortex.put_link(last_node_id, node_id, "sys:next",     author=author_id)
            self.cortex.put_link(node_id, last_node_id, "sys:previous", author=author_id)
            self.cortex.remove_link(self.concept_id, last_node_id, "sys:bottom")
        self.cortex.put_link(self.concept_id, node_id, "sys:bottom", author=author_id)

    # ── Operators (public API) ────────────────────────────────────────────────

    def op_new(self, name: str) -> Dict[str, Any]:
        """[cockpit.new] Commission a new Cockpit observation deck."""
        author_id, scopes = self._author_and_scopes()

        root_meta = {
            "type":       "concept",
            "concept":    "cockpit",
            "role":       "root",
            "name":       name,
            "created_at": time.time(),
        }
        root_id = self.cortex.put_chunk(
            content=f"[ Cockpit: {name} ]",
            meta=root_meta,
            author=author_id,
            scopes=scopes,
        )

        self.concept_id = root_id
        self.set_name   = f"set:concept:{self.concept_id}"

        self.cortex.create_set(self.set_name)
        self.cortex.create_set(self._content_set())
        self.register_concept_node(root_id)

        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, root_id)
            self.session.set_context("active_focus", None)
            self.session.set_context("active_axis",  None)
            self.session.set_context("active_scope", 2)

        logger.info(f"[CockpitConcept] Commissioned: '{name}' ({root_id[:8]})")
        return {"status": "commissioned", "cockpit_id": root_id, "name": name}

    def op_ls(self) -> Dict[str, Any]:
        """[cockpit.ls] List all cockpits accessible to this session."""
        client_id = getattr(self.session, "client_id", "system")
        rows = self.cortex.fetch_by_meta_field("concept", "cockpit", author=client_id)
        cockpits = []
        for row in rows:
            try:
                meta = json.loads(row.get("meta") or "{}")
            except Exception:
                meta = {}
            if meta.get("role") == "root":
                cockpits.append({
                    "cockpit_id": row["key"],
                    "name":       meta.get("name", ""),
                    "created_at": meta.get("created_at", 0),
                })
        cockpits.sort(key=lambda x: x["created_at"], reverse=True)
        return {"cockpits": cockpits}

    def op_open(self, cockpit_id: str) -> Dict[str, Any]:
        """[cockpit.open] Mount an existing cockpit as the session's active vessel."""
        meta = self.cortex.get_meta(cockpit_id)
        if not meta or meta.get("concept") != "cockpit":
            raise RuntimeError(f"Atom '{cockpit_id[:12]}' is not a cockpit root.")

        self.concept_id = cockpit_id
        self.set_name   = f"set:concept:{self.concept_id}"

        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, cockpit_id)
            # Restore persisted navigation state so reconnects resume where the pilot left off
            if meta.get("last_focus"):
                self.session.set_context("active_focus", meta["last_focus"])
            if meta.get("last_axis"):
                self.session.set_context("active_axis", meta["last_axis"])
            if meta.get("last_scope") is not None:
                self.session.set_context("active_scope", meta["last_scope"])

        return {"status": "opened", "cockpit_id": cockpit_id, "name": meta.get("name", "")}

    def op_lock(self, target_id: str) -> Dict[str, Any]:
        """[cockpit.lock] Set the spatial focal point of the Cosmos."""
        self._require_concept()
        if hasattr(self.session, "set_context"):
            self.session.set_context("active_focus", target_id)
        self.cortex.set_meta(self.concept_id, "last_focus", target_id)
        return {"status": "locked", "target": target_id}

    def op_tune_lens(self, axis: Optional[str] = None, scope: Optional[int] = None) -> Dict[str, Any]:
        """[cockpit.tune] Adjust dimensional lens filters."""
        self._require_concept()
        if hasattr(self.session, "set_context"):
            if axis is not None:
                self.session.set_context("active_axis", axis)
            if scope is not None:
                self.session.set_context("active_scope", scope)
        if axis is not None:
            self.cortex.set_meta(self.concept_id, "last_axis", axis)
        if scope is not None:
            self.cortex.set_meta(self.concept_id, "last_scope", scope)
        return {"status": "tuned", "axis": axis, "scope": scope}

    def op_drop_beacon(self, note: str) -> Dict[str, Any]:
        """[cockpit.beacon] Persist a navigational beacon at the current focal point."""
        self._require_concept()
        if not note:
            raise ValueError("Beacon note text is required.")

        author_id, scopes = self._author_and_scopes()

        get_ctx       = getattr(self.session, "get_context", lambda k: None)
        current_focus = get_ctx("active_focus")
        current_axis  = get_ctx("active_axis")
        current_scope = get_ctx("active_scope")

        if not current_focus:
            raise RuntimeError("No focal target. Use cockpit.lock <id> first.")

        focal_aliases = self.cortex.get_aliases_by_key(current_focus)
        focal_alias   = focal_aliases[0] if focal_aliases else None

        beacon_id = self.cortex.put_chunk(
            content=note,
            meta={
                "type":        "beacon",
                "role":        "beacon",
                "focal_key":   current_focus,
                "focal_alias": focal_alias,
                "axis":        current_axis,
                "scope":       current_scope,
                "created_at":  time.time(),
            },
            author=author_id,
            scopes=scopes,
        )

        # Dual-namespace registration:
        # 1. cockpit content set (model-scope)
        self.cortex.add_to_set(self._content_set(), beacon_id)
        # 2. concept catalog (BaseConcept catalog for cross-concept queries)
        self.register_concept_node(beacon_id)

        # Structural links
        self.cortex.put_link(self.concept_id, beacon_id, "sys:contains",      author=author_id)
        self.cortex.put_link(beacon_id, current_focus,   "sys:associated_with", author=author_id)

        # Chronological wake
        self._append_to_timeline(beacon_id, author_id)

        logger.info(f"[CockpitConcept] Beacon deployed at {current_focus[:8]} ({beacon_id[:8]})")
        return {
            "status":    "beacon_deployed",
            "beacon_id": beacon_id,
            "telemetry": {
                "focus": current_focus,
                "axis":  current_axis,
                "scope": current_scope,
            },
        }

    def op_wake(self) -> Dict[str, Any]:
        """[cockpit.wake] Read the chronological beacon trail (top → bottom)."""
        self._require_concept()

        allowed = self.allowed_scopes
        wake    = []

        top_links = self.cortex.get_adjacent_links(self.concept_id, "sys:top")
        if not top_links:
            return {"wake": [], "count": 0}

        seen = set()
        current_id = top_links[0][0]
        while current_id and current_id not in seen:
            seen.add(current_id)
            if self.cortex.check_access(current_id, allowed):
                content = self.cortex.get_chunk(current_id)
                meta    = self.cortex.get_meta(current_id)
                wake.append({
                    "id":          current_id,
                    "content":     content,
                    "focal_key":   meta.get("focal_key"),
                    "focal_alias": meta.get("focal_alias"),
                    "axis":        meta.get("axis"),
                    "scope":       meta.get("scope"),
                    "created_at":  meta.get("created_at"),
                })
            next_links = self.cortex.get_adjacent_links(current_id, "sys:next")
            current_id = next_links[0][0] if next_links else None

        return {"wake": wake, "count": len(wake)}

    def op_status(self) -> Dict[str, Any]:
        """[cockpit.status] Read the current instrument panel state."""
        self._require_concept()
        get_ctx = getattr(self.session, "get_context", lambda k: None)
        return {
            "cockpit_id": self.concept_id,
            "focus":      get_ctx("active_focus"),
            "axis":       get_ctx("active_axis"),
            "scope":      get_ctx("active_scope"),
        }

    def op_delete(self) -> Dict[str, Any]:
        """[cockpit.rm] Decommission the vessel and clear session context."""
        self._require_concept()
        cockpit_id = self.concept_id
        self.cortex.drop_chunk(cockpit_id, requester_scopes=self.allowed_scopes)
        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, None)
            self.session.set_context("active_focus", None)
            self.session.set_context("active_axis",  None)
        return {"status": "decommissioned", "cockpit_id": cockpit_id}
