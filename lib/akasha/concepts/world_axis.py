"""
The minimal SYSTEM world container — the world's axis (group 4, 4.14; ruling Q1).

The society and the workbench are platform models, and they record on the shared world's axis: a
society formed, connected or severed, a bench created or retired, a workflow dispatch synced. They
reached that axis through the APPLICATION's `world` Concept Model (`concept_class("world")`), so a
platform model depended on an application one, and a cell without it silently lost its history.

What they need is not the world model — places, laws, portals, stages, the topology an application
authors — but the axis every world has: its clock, one coordinate per event, the env and sync sets.
That is this module. It writes EXACTLY the atoms the world model's commons ops write (the same
aliases `world:<w>:env:<n>` / `world:<w>:sync:<n>`, the same clock `world:<w>`, the same Sets and
coordinate Sets), through the same platform primitives (`UniversalConcept`, `CrononConcept`), so an
axis written here and one written there are one axis. The topology model stays the application's;
its commons ops may delegate here.

Not a Concept Model: it declares no prefix and registers no op. A platform model holds one.
"""
import datetime
from typing import Any, Dict, Optional

from lib.akasha.concepts._universal import UniversalConcept
from lib.akasha.concepts.cronon import CrononConcept


class WorldAxis:
    """The world's clock and its env / sync records, bound to one session."""

    # The event kinds the axis records. The same list the world model accepts on `world.env.record`.
    ENV_KINDS = frozenset({
        "bench.created", "bench.retired", "society.formed", "society.dissolved",
        "society.connected", "society.severed", "workflow.connected",
        "world.created", "world.retired",
        "society.moderator.mode",
        "bench.trained", "bench.evaluated", "bench.promoted",
    })

    def __init__(self, session: Any):
        self.session = session
        self._u = UniversalConcept(session)
        self._cronon = CrononConcept(session)

    # ── names ────────────────────────────────────────────────────────────────────────────────────
    @staticmethod
    def commons_alias(world: str = "default") -> str:
        return f"world:{world}"

    @staticmethod
    def clock(world: str = "default") -> str:
        """The world's clock NAME (atom `cronon:clock:world:<w>`, coordinates `cronon:world:<w>:c<n>`)."""
        return f"world:{world}"

    @staticmethod
    def env_set(world: str = "default") -> str:
        return f"set:world:{world}:env"

    @staticmethod
    def sync_set(world: str = "default") -> str:
        return f"set:world:{world}:sync"

    # ── the axis ─────────────────────────────────────────────────────────────────────────────────
    def genesis(self, world: str = "default", title: str = "Akasha — the shared world (the commons)",
                kind: str = "commons", color: str = "none") -> Dict[str, Any]:
        """The world atom and its clock, idempotent by alias (the env / sync Sets appear on first add)."""
        alias = self.commons_alias(world)
        clock_atom = self._u.clock_alias(self.clock(world))
        if self._u.key(alias):
            return {"world": alias, "status": "present", "clock": clock_atom}
        self._u.mk(alias, f"[{alias}] {title}",
                   {"concept": "world", "kind": kind, "color": color, "world": world,
                    "title": title, "clock": clock_atom, "created_wall": self._u.now_wall()})
        if not self._u.key(clock_atom):
            self._u.mk(clock_atom, f"[{clock_atom}] world:{world} axis clock (Akasha-Time coordinate "
                       "counter — NOT a scheduler)",
                       {"concept": "cronon_clock", "at_seq": 0, "clock": self.clock(world)})
        return {"world": alias, "status": "created", "clock": clock_atom}

    def _wall_stamp(self) -> tuple:
        wall = self._u.now_wall()
        iso = datetime.datetime.utcfromtimestamp(wall).strftime("%Y-%m-%dT%H:%M:%S.")
        iso += "%03dZ" % int(round((wall - int(wall)) * 1000))
        return iso, wall

    def op_tick(self, reason: str = "env", ref: str = "", world: str = "default") -> Dict[str, Any]:
        """Mint one coordinate on the world's clock, stamped `cronon:maps_to` frame=wall_clock."""
        if reason not in ("env", "sync"):
            raise ValueError("world tick reason must be 'env' or 'sync'")
        r = self._cronon.op_mint(label=f"world:{world}:{reason}", clock=self.clock(world))
        cid, seq = r["cronon"], r["position"]
        iso, wall = self._wall_stamp()
        val = f"{iso}|{wall}"
        self._cronon.op_map(cronon=cid, frame="wall_clock", value=val)
        return {"cronon": cid, "position": seq, "reason": reason, "wall": val,
                "ref": ref or None, "world": world}

    def op_env_record(self, kind: str, ref: str = "", note: str = "",
                      world: str = "default") -> Dict[str, Any]:
        """Record ONE environment event on the world axis (`world:<w>:env:<n>`, numbered by the
        coordinate's monotonic POSITION; content stamped with kind + alias so no two events share)."""
        if kind not in self.ENV_KINDS:
            raise ValueError(f"world env kind must be one of {sorted(self.ENV_KINDS)}")
        tick = self.op_tick(reason="env", ref=ref, world=world)
        cid, seq = tick["cronon"], tick["position"]
        alias = f"world:{world}:env:{seq}"
        key = self._u.mk(alias, f"[{alias}] {kind}" + (f": {note}" if note else ""),
                         {"concept": "world_env", "kind": kind, "ref": ref or None,
                          "note": note or None, "cronon": cid, "cronon_pos": seq,
                          "world": world, "wall": tick["wall"]})
        self._u.add_to_set(self.env_set(world), key)
        self._u.cronon_locate(self.clock(world), seq, key)
        return {"env": alias, "kind": kind, "cronon": cid, "position": seq,
                "wall": tick["wall"], "world": world}

    def op_sync_record(self, exec_id: str, bench: str = "", branch: str = "main",
                       from_pos: Any = None, to_pos: Any = None, agents: Any = None,
                       world: str = "default", note: str = "") -> Dict[str, Any]:
        """Record ONE workflow dispatch on the world axis (`world:<w>:sync:<n>`) — one per dispatch."""
        tick = self.op_tick(reason="sync", ref=exec_id, world=world)
        cid, seq = tick["cronon"], tick["position"]
        alias = f"world:{world}:sync:{seq}"
        key = self._u.mk(alias, note or f"dispatch {exec_id}",
                         {"concept": "world_sync", "kind": "workflow.dispatched", "exec": exec_id,
                          "bench": bench or None, "branch": branch or None,
                          "from": from_pos, "to": to_pos, "agents": agents or [],
                          "ref": exec_id, "cronon": cid, "cronon_pos": seq,
                          "world": world, "wall": tick["wall"]})
        self._u.add_to_set(self.sync_set(world), key)
        self._u.cronon_locate(self.clock(world), seq, key)
        return {"sync": alias, "exec": exec_id, "cronon": cid, "position": seq,
                "wall": tick["wall"], "world": world}


def axis(session: Any) -> Optional[WorldAxis]:
    """A WorldAxis for this session, or None when the session cannot hold one."""
    try:
        return WorldAxis(session)
    except Exception:
        return None
