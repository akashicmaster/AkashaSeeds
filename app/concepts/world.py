"""
World Concept Model (`world.*`) — the COMMONS: the shared world's genesis, clock and axis.

The topology half (places, laws, portals, stages — `world.new/open/place.add/…`) is `topos.py`
(`topos.*`). What stays here is the axis every world has: `world.genesis`, `world.tick`,
`world.env.record`, `world.sync`, `world.axis`. The clock, the env / sync records and the genesis
are the platform's `WorldAxis` (`world_axis.py`); these ops delegate to it, so an axis written
through an op and one written by a platform model are one axis.
"""
import datetime
import logging
from typing import Any, Dict, List, Optional

from lib.akasha.api.concepts import BaseConcept
from lib.akasha.api.concepts import UniversalConcept
from lib.akasha.api.concepts import WorldAxis

logger = logging.getLogger("Harmonia.Concept.World")
_AXIS_DEPRECATION_LOGGED = False   # G4 §3.4 — one [deprecated] world.axis line per session


class WorldConcept(BaseConcept):
    """The shared world's commons — genesis, the clock, and the env / sync axis (delegating to WorldAxis)."""

    CONCEPT_PREFIX = "world"
    _ENV_KINDS = WorldAxis.ENV_KINDS

    CONCEPT_METHODS = {
        "genesis":      {"op": "op_genesis", "action": "record",
                         "desc": "[internal/boot] Create the shared world:default (commons) in the "
                                 "nucleus — atom + env/sync sets + its own clock. Idempotent."},
        "tick":         {"op": "op_tick", "action": "record",
                         "desc": "Mint one coordinate on a world's clock with a wall-clock stamp: "
                                 "world.tick reason=env|sync ref=<atom> [world=default]"},
        "env.record":   {"op": "op_env_record", "action": "record",
                         "desc": "Record one environment event on the world axis: world.env.record "
                                 "kind=<bench.created|society.formed|…> ref=<atom> [note=] [world=default]"},
        "sync":         {"op": "op_sync", "action": "record",
                         "desc": "Mark a bench moment on the world (G4 §1.6 — a cronon:sync link "
                                 "world ↔ bench; needs responsible:decide): world.sync bench=<b> "
                                 "at=<cronon:wb:…:c<n>> [world=default]"},
        "axis": {
            "op": "op_axis", "action": "read",
            "coerce": lambda d: {"world": d.get("world") or "default",
                                 "start": d.get("from", ""), "end": d.get("to", ""),
                                 "limit": int(d.get("limit", 200) or 200)},
            "desc": "The world axis (env + sync events in clock order, wall-stamped): "
                    "world.axis [world=default] [from=<c>] [to=<c>] [limit=200]",
        },
    }

    def __init__(self, session: Any, concept_id: Optional[str] = None):
        super().__init__(session, concept_id)
        self._axis_cache = None

    @property
    def _axis(self) -> WorldAxis:
        a = getattr(self, "_axis_cache", None)
        if a is None:
            a = self._axis_cache = WorldAxis(self.session)
        return a

    @property
    def _u(self):
        """A UniversalConcept bound to this session (the nucleus-write helper)."""
        u = getattr(self, "_u_cache", None)
        if u is None:
            u = self._u_cache = UniversalConcept(self.session)
        return u

    _commons_alias = staticmethod(WorldAxis.commons_alias)
    _commons_clock = staticmethod(WorldAxis.clock)
    _env_set = staticmethod(WorldAxis.env_set)
    _sync_set = staticmethod(WorldAxis.sync_set)

    @staticmethod
    def _pos_of(x: Any) -> Optional[int]:
        """Parse a from=/to= bound: an int position, or a cronon id whose trailing c<n> is the pos."""
        if x is None or str(x).strip() == "":
            return None
        s = str(x).strip()
        if s.isdigit():
            return int(s)
        if ":c" in s:
            tail = s.rsplit(":c", 1)[-1]
            if tail.isdigit():
                return int(tail)
        return None

    def op_genesis(self, world: str = "default") -> Dict[str, Any]:
        """[world.genesis] (internal / boot) Create the shared `world:<world>` (default: the commons):
        the world atom {concept: world, kind: commons, color: none}, its env/sync sets, and its own
        clock. Colorless: no places, laws or theme. Idempotent by alias."""
        return self._axis.genesis(world=world)

    def op_tick(self, reason: str = "env", ref: str = "", world: str = "default") -> Dict[str, Any]:
        """[world.tick] Mint one coordinate on the world's clock and stamp `cronon:maps_to`
        frame=wall_clock value=`<ISO8601>|<epoch.ms>` at mint (D2b). Returns the coordinate."""
        return self._axis.op_tick(reason=reason, ref=ref, world=world)

    def op_env_record(self, kind: str, ref: str = "", note: str = "",
                      world: str = "default") -> Dict[str, Any]:
        """[world.env.record] Record ONE environment event on the world axis (delegates to WorldAxis)."""
        return self._axis.op_env_record(kind=kind, ref=ref, note=note, world=world)

    def op_sync_record(self, exec_id: str, bench: str = "", branch: str = "main",
                       from_pos: Any = None, to_pos: Any = None, agents: Any = None,
                       world: str = "default", note: str = "") -> Dict[str, Any]:
        """Record ONE workflow dispatch on the world axis (delegates to WorldAxis). Internal."""
        return self._axis.op_sync_record(exec_id=exec_id, bench=bench, branch=branch, from_pos=from_pos,
                                         to_pos=to_pos, agents=agents, world=world, note=note)

    def op_sync(self, bench: str = "", at: str = "", world: str = "default",
                via: str = "run") -> Dict[str, Any]:
        """[world.sync] Mark a bench moment on the world — a `cronon:sync` link between a freshly ticked
        world SYNC coordinate and the given bench coordinate `at=` (G4 §1.6). The auto-run driver uses
        this to sync a run's first/last bench coordinate to the world; a moderator uses it to mark a
        thought reading as presented (the only way a thought record reaches the world). world ↔ bench
        only — never a branch coordinate."""
        if not at or ":c" not in str(at):
            raise ValueError("world.sync requires at=<bench coordinate, e.g. cronon:wb:<bench>:c<n>>")
        tick = self._axis.op_tick(reason="sync", ref=at, world=world)
        cid = tick["cronon"]
        self._u.cronon_locate(self._commons_clock(world), tick["position"], self._u.key(cid) or cid)
        self._u.link(cid, at, "cronon:sync")
        logger.info("[cronon] sync %s ↔ %s via=%s", cid, at, via)
        return {"world": self._commons_alias(world), "cronon": cid, "position": tick["position"],
                "bench_coordinate": at, "wall": tick["wall"]}

    def op_axis(self, world: str = "default", start: str = "", end: str = "",
                limit: int = 200) -> Dict[str, Any]:
        """[world.axis] The shared world's axis — env and sync records interleaved in clock order,
        each with its wall-clock stamp. Read. NOT guest-readable: a guest session is refused (the
        per-atom `scope:world:<world>:axis` grant to admitted agents lands in G2.5)."""
        cid = str(getattr(self.session, "client_id", "") or "")
        if cid.startswith("guest:"):
            return {"status": "refused", "world": self._commons_alias(world),
                    "reason": "world.axis is not guest-readable (admitted agents of a society in "
                              "the world only)"}
        # G4 §3.4 — world.axis is retired in favour of the `timeline` macro (macro.run timeline
        # clock=world:<w>); it stays ONE release as an alias and logs the deprecation once per session.
        global _AXIS_DEPRECATION_LOGGED
        if not _AXIS_DEPRECATION_LOGGED:
            _AXIS_DEPRECATION_LOGGED = True
            logger.info("[deprecated] world.axis → macro.run timeline clock=world:%s", world)
        lo, hi = self._pos_of(start), self._pos_of(end)
        rows: List[Dict[str, Any]] = []
        for setname, rectype in ((self._env_set(world), "env"), (self._sync_set(world), "sync")):
            for k in self._u.members(setname):
                m = self._u.cortex.get_meta(k) or {}
                row = {"type": rectype, "id": self._u.alias(k), "kind": m.get("kind"),
                       "ref": m.get("ref"), "note": m.get("note"), "cronon": m.get("cronon"),
                       "position": int(m.get("cronon_pos") or 0), "wall": m.get("wall")}
                if rectype == "sync":
                    row.update({"exec": m.get("exec"), "bench": m.get("bench"),
                                "branch": m.get("branch"), "agents": m.get("agents")})
                rows.append(row)
        rows.sort(key=lambda r: r.get("position") or 0)
        if lo is not None:
            rows = [r for r in rows if (r.get("position") or 0) >= lo]
        if hi is not None:
            rows = [r for r in rows if (r.get("position") or 0) <= hi]
        return {"world": self._commons_alias(world), "axis": rows[:max(1, int(limit))],
                "count": len(rows)}
