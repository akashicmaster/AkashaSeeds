"""
WhiteboardConcept — named meaning session (F53 Phase 0 Stage 2: the naming layer over the horizon).

A Whiteboard is a NAMED bundle of the session's self-directed state. As of F53 it is a thin naming
layer over the ONE normalized session horizon (see kernel `horizon.*` / `sys.session.state`): pinning
is just adding a soft horizon entry, and switching boards saves the outgoing board's whole
self-directed tuple and restores the incoming one. F54: axis / radius / time now ride the board
STATE too (the whiteboard-local `wb:<name>:scope_*` branch in the sys.scope.* handlers is retired) —
wb.focus restores them into the session-global keys. No cortex atoms are written — pure session context.

State is stored entirely in session context keys:

  active_whiteboard        — name of the currently active whiteboard
  wb_names                 — list of all known whiteboard names
  wb:<name>:state          — the board's saved self-directed tuple (F54):
                             {"horizon": [{set, mode}], "focus": <key|None>,
                              "axis": <str|None>, "radius": <int|None>, "time": <str|None>}
                             The ACTIVE board's live copy is the session-global keys
                             (horizon / focus / active_axis / radius / active_time).

Legacy: wb:<name>:pinned (pre-F53 pins) and wb:<name>:scope_* (pre-F54 wb-local scope) are READ ONCE
for migration the first time a legacy board is focused — pins become soft horizon entries, wb-local
scope folds into the board state — then never read again.

Switching whiteboards via wb.focus saves the outgoing board's tuple into wb:<name>:state and restores
the incoming board's tuple into the session-global keys; the sys.scope.* handlers read only those.
"""

import json
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger("Harmonia.Concept.Whiteboard")

_HORIZON_CAP = 8


class WhiteboardConcept:
    """Session-local Whiteboard manager — the naming layer over the normalized session horizon.
    Does not inherit BaseConcept — no cortex atoms are created for the board itself."""

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

    # ── the ONE session horizon (same shape as the kernel horizon.* ops) ──
    def _get_horizon(self) -> List[Dict[str, Any]]:
        hz = self.session.get_context("horizon")
        return list(hz) if isinstance(hz, list) else []

    def _set_horizon(self, hz: List[Dict[str, Any]]):
        self.session.set_context("horizon", hz)

    @staticmethod
    def _view(hz: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [{"set": e.get("set"), "mode": e.get("mode", "soft")} for e in hz]

    # ── per-board saved state {horizon, focus} ──
    def _get_state(self, name: str) -> Optional[Dict[str, Any]]:
        raw = self.session.get_context(f"wb:{name}:state")
        if raw is None:
            return None
        if isinstance(raw, dict):
            return raw
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return None

    def _set_state(self, name: str, state: Dict[str, Any]):
        self.session.set_context(f"wb:{name}:state", state)

    def _legacy_pinned(self, name: str) -> List[str]:
        raw = self.session.get_context(f"wb:{name}:pinned")
        if not raw:
            return []
        if isinstance(raw, list):
            return raw
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return []

    def _get_scope(self, name: str) -> Dict[str, Any]:
        # F54 — a board's scope IS the session-global state while active (the wb-local scope keys are
        # retired; saved into wb:<name>:state on focus-out). Active board → live global keys; other
        # board → its saved state.
        if name == self._active_name():
            _scope = self.session.get_context("active_scope")
            _radius = self.session.get_context("radius")
            _depth = _radius if _radius is not None else _scope
            return {"axis": self.session.get_context("active_axis"), "scope": _depth,
                    "radius": _depth, "time": self.session.get_context("active_time")}
        st = self._get_state(name) or {}
        return {"axis": st.get("axis"), "scope": st.get("radius"),
                "radius": st.get("radius"), "time": st.get("time")}

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

    def _save_active_state(self):
        """Persist the currently-active board's live (horizon, focus, axis, radius, time) before
        switching away. F54: axis/radius/time now ride the board state (not wb-local scope keys)."""
        cur = self._active_name()
        if cur and cur in self._get_wb_names():
            _scope = self.session.get_context("active_scope")
            _radius = self.session.get_context("radius")
            self._set_state(cur, {
                "horizon": self._get_horizon(),
                "focus":   self.session.get_context("focus"),
                "axis":    self.session.get_context("active_axis"),
                "radius":  _radius if _radius is not None else _scope,
                "time":    self.session.get_context("active_time"),
            })

    def _load_state(self, name: str) -> bool:
        """Restore a board's (horizon, focus, axis, radius, time) into the live session-global keys.
        F54: axis/radius/time are restored globally (the wb-local scope branch is gone). A board with
        no F54 state yet MIGRATES ONCE — its legacy pins → soft horizon entries, and any pre-F54
        wb-local scope keys → the board state. Returns True iff a legacy migration happened."""
        state = self._get_state(name)
        if state is not None:
            self._set_horizon(state.get("horizon") or [])
            self.session.set_context("focus", state.get("focus"))
            self.session.set_context("active_axis", state.get("axis"))
            self.session.set_context("radius", state.get("radius"))
            self.session.set_context("active_scope", None)      # retired write key — keep it clear
            self.session.set_context("active_time", state.get("time"))
            return False
        legacy = self._legacy_pinned(name)
        hz = [{"set": c, "mode": "soft"} for c in legacy][:_HORIZON_CAP]
        _lscope = self.session.get_context(f"wb:{name}:scope_scope")     # pre-F54 wb-local scope
        _lradius = self.session.get_context(f"wb:{name}:radius")
        _ldepth = _lradius if _lradius is not None else _lscope
        _laxis = self.session.get_context(f"wb:{name}:scope_axis")
        _ltime = self.session.get_context(f"wb:{name}:scope_time")
        self._set_horizon(hz)
        self.session.set_context("focus", None)
        self.session.set_context("active_axis", _laxis)
        self.session.set_context("radius", _ldepth)
        self.session.set_context("active_scope", None)
        self.session.set_context("active_time", _ltime)
        self._set_state(name, {"horizon": hz, "focus": None, "axis": _laxis,
                               "radius": _ldepth, "time": _ltime})       # write once; legacy inert
        return bool(legacy)

    # ------------------------------------------------------------------
    # Operators
    # ------------------------------------------------------------------

    def op_new(self, name: str) -> Dict[str, Any]:
        """[wb.new] Create a new Whiteboard and make it active. Recreating an EXISTING name is FOCUS
        semantics (never erases its horizon) — the fix for the old pins-wipe bug."""
        names = self._get_wb_names()
        if name in names:
            return self.op_focus(name)          # recreation must never erase — focus instead
        self._save_active_state()               # persist the outgoing board first
        names.append(name)
        self._set_wb_names(names)
        self._set_state(name, {"horizon": [], "focus": None, "axis": None, "radius": None, "time": None})
        self._set_horizon([])                   # a fresh board starts with an empty horizon + scope
        self.session.set_context("focus", None)
        self.session.set_context("active_axis", None)
        self.session.set_context("radius", None)
        self.session.set_context("active_scope", None)
        self.session.set_context("active_time", None)
        self.session.set_context("active_whiteboard", name)
        logger.info(f"[WhiteboardConcept] New whiteboard: '{name}'")
        return {"name": name, "horizon": [], "pinned": [], "status": "created", "active": True}

    def op_pin(self, concept: str) -> Dict[str, Any]:
        """[wb.pin] Pin a concept/set to the active board — i.e. add a SOFT horizon entry (= horizon.add)."""
        hz = self._get_horizon()
        for e in hz:
            if e.get("set") == concept:
                e["mode"] = "soft"
                self._set_horizon(hz)
                return {"whiteboard": self._active_name(), "horizon": self._view(hz),
                        "pinned": [x["set"] for x in hz], "status": "pinned"}
        if len(hz) >= _HORIZON_CAP:             # cap: refuse loudly, never trim
            return {"whiteboard": self._active_name(), "horizon": self._view(hz),
                    "status": "error",
                    "error": f"horizon is full ({_HORIZON_CAP}) — wb.unpin one first"}
        hz.append({"set": concept, "mode": "soft"})
        self._set_horizon(hz)
        return {"whiteboard": self._active_name(), "horizon": self._view(hz),
                "pinned": [x["set"] for x in hz], "status": "pinned"}

    def op_unpin(self, concept: str) -> Dict[str, Any]:
        """[wb.unpin] Remove a concept/set from the active board (= horizon.rm)."""
        hz = [e for e in self._get_horizon() if e.get("set") != concept]
        self._set_horizon(hz)
        return {"whiteboard": self._active_name(), "horizon": self._view(hz),
                "pinned": [x["set"] for x in hz], "status": "unpinned"}

    def op_focus(self, name: str) -> Dict[str, Any]:
        """[wb.focus] Switch the active board: save the outgoing board's (horizon, focus), restore the
        incoming one (or migrate its legacy pins once); axis/radius/time follow via active_whiteboard."""
        self._require_whiteboard(name)
        self._save_active_state()
        self.session.set_context("active_whiteboard", name)
        migrated = self._load_state(name)
        hz = self._get_horizon()
        return {
            "active_whiteboard": name,
            "horizon":           self._view(hz),
            "pinned":            [x["set"] for x in hz],
            "scope":             self._get_scope(name),
            "focus":             self.session.get_context("focus"),
            "migrated":          migrated,
            "status":            "focused",
        }

    def op_list(self) -> Dict[str, Any]:
        """[wb.ls] List all Whiteboards in this session (horizon size per board — O(1), no member sweep)."""
        names = self._get_wb_names()
        active = self._active_name()
        boards = []
        for n in names:
            if n == active:
                hcount = len(self._get_horizon())          # the live copy is authoritative
            else:
                st = self._get_state(n)
                hcount = len(st.get("horizon") or []) if st is not None else len(self._legacy_pinned(n))
            boards.append({"name": n, "horizon": hcount, "active": n == active})
        return {"whiteboards": boards, "count": len(boards)}

    def op_show(self) -> Dict[str, Any]:
        """[wb.show] Show the current state of the active Whiteboard."""
        name = self._require_active()
        hz = self._get_horizon()
        return {
            "name":         name,
            "horizon":      self._view(hz),
            "pinned":       [x["set"] for x in hz],
            "scope":        self._get_scope(name),
            "active_log":   self.session.get_context("active_log_root"),
            "active_focus": self.session.get_context("focus"),
        }

    def op_delete(self, name: str) -> Dict[str, Any]:
        """[wb.rm] Remove a Whiteboard from this session."""
        self._require_whiteboard(name)
        names = [n for n in self._get_wb_names() if n != name]
        self._set_wb_names(names)
        for key in (f"wb:{name}:state", f"wb:{name}:pinned", f"wb:{name}:scope_axis",
                    f"wb:{name}:scope_scope", f"wb:{name}:radius", f"wb:{name}:scope_time"):
            self.session.set_context(key, None)
        if self._active_name() == name:
            self.session.set_context("active_whiteboard", None)
            self._set_horizon([])               # the active board is gone — clear the live horizon
            self.session.set_context("focus", None)
        return {"status": "deleted", "name": name}
