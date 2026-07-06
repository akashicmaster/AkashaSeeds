"""
WhiteboardConcept — named meaning session.

A Whiteboard pins multiple Concept Models together to define their
intersection. When active, all traversal and association operations
execute within the combined semantic context of all pinned concepts.

State is stored entirely in session context keys (no cortex atoms written):

  active_whiteboard        — name of the currently active whiteboard
  wb_names                 — list of all known whiteboard names
  wb:<name>:pinned         — list of pinned concept model names
  wb:<name>:scope_axis     — whiteboard-local active_axis
  wb:<name>:scope_scope    — whiteboard-local active_scope (int | None)
  wb:<name>:scope_time     — whiteboard-local active_time

Switching whiteboards via wb.focus restores that board's scope state
automatically because sys.scope.get/set read from wb:<name>:scope_*
when a whiteboard is active.
"""

import json
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger("Harmonia.Concept.Whiteboard")


class WhiteboardConcept:
    """
    Session-local Whiteboard manager.
    Does not inherit BaseConcept — no cortex atoms are created for the board itself.
    """

    def __init__(self, session: Any):
        self.session = session

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_wb_names(self) -> List[str]:
        raw = self.session.get_context("wb_names")
        if not raw:
            return []
        if isinstance(raw, list):
            return raw
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return []

    def _set_wb_names(self, names: List[str]):
        self.session.set_context("wb_names", names)

    def _get_pinned(self, name: str) -> List[str]:
        raw = self.session.get_context(f"wb:{name}:pinned")
        if not raw:
            return []
        if isinstance(raw, list):
            return raw
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return []

    def _set_pinned(self, name: str, pinned: List[str]):
        self.session.set_context(f"wb:{name}:pinned", pinned)

    def _get_scope(self, name: str) -> Dict[str, Any]:
        return {
            "axis":  self.session.get_context(f"wb:{name}:scope_axis"),
            "scope": self.session.get_context(f"wb:{name}:scope_scope"),
            "time":  self.session.get_context(f"wb:{name}:scope_time"),
        }

    def _active_name(self) -> Optional[str]:
        return self.session.get_context("active_whiteboard")

    def _require_active(self) -> str:
        name = self._active_name()
        if not name:
            raise RuntimeError("No active whiteboard. Use wb.new or wb.focus first.")
        return name

    def _require_whiteboard(self, name: str):
        if name not in self._get_wb_names():
            raise RuntimeError(f"Whiteboard '{name}' does not exist.")

    # ------------------------------------------------------------------
    # Operators
    # ------------------------------------------------------------------

    def op_new(self, name: str) -> Dict[str, Any]:
        """[wb.new] Create a new Whiteboard and make it active."""
        names = self._get_wb_names()
        if name not in names:
            names.append(name)
            self._set_wb_names(names)
        self._set_pinned(name, [])
        self.session.set_context("active_whiteboard", name)
        logger.info(f"[WhiteboardConcept] New whiteboard: '{name}'")
        return {"name": name, "pinned": [], "status": "created", "active": True}

    def op_pin(self, concept: str) -> Dict[str, Any]:
        """[wb.pin] Pin a Concept Model to the active Whiteboard."""
        name = self._require_active()
        pinned = self._get_pinned(name)
        if concept not in pinned:
            pinned.append(concept)
            self._set_pinned(name, pinned)
        return {"whiteboard": name, "pinned": pinned, "status": "pinned"}

    def op_unpin(self, concept: str) -> Dict[str, Any]:
        """[wb.unpin] Remove a Concept Model from the active Whiteboard."""
        name = self._require_active()
        pinned = [c for c in self._get_pinned(name) if c != concept]
        self._set_pinned(name, pinned)
        return {"whiteboard": name, "pinned": pinned, "status": "unpinned"}

    def op_focus(self, name: str) -> Dict[str, Any]:
        """[wb.focus] Switch the active Whiteboard and restore its scope state."""
        self._require_whiteboard(name)
        self.session.set_context("active_whiteboard", name)
        pinned = self._get_pinned(name)
        scope  = self._get_scope(name)
        return {
            "active_whiteboard": name,
            "pinned":            pinned,
            "scope":             scope,
            "status":            "focused",
        }

    def op_list(self) -> Dict[str, Any]:
        """[wb.ls] List all Whiteboards in this session."""
        names  = self._get_wb_names()
        active = self._active_name()
        boards = [
            {"name": n, "pinned": self._get_pinned(n), "active": n == active}
            for n in names
        ]
        return {"whiteboards": boards, "count": len(boards)}

    def op_show(self) -> Dict[str, Any]:
        """[wb.show] Show the current state of the active Whiteboard."""
        name   = self._require_active()
        pinned = self._get_pinned(name)
        scope  = self._get_scope(name)
        return {
            "name":         name,
            "pinned":       pinned,
            "scope":        scope,
            "active_note":  self.session.get_context("active_note_root"),
            "active_log":   self.session.get_context("active_log_root"),
            "active_focus": self.session.get_context("focus"),
        }

    def op_delete(self, name: str) -> Dict[str, Any]:
        """[wb.rm] Remove a Whiteboard from this session."""
        self._require_whiteboard(name)
        names = [n for n in self._get_wb_names() if n != name]
        self._set_wb_names(names)
        for key in (f"wb:{name}:pinned", f"wb:{name}:scope_axis",
                    f"wb:{name}:scope_scope", f"wb:{name}:scope_time"):
            self.session.set_context(key, None)
        if self._active_name() == name:
            self.session.set_context("active_whiteboard", None)
        return {"status": "deleted", "name": name}
