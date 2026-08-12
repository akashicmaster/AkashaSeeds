"""
AgentConcept — an agent is a CAST admitted to a SOCIETY (seeds13, Part A / B.3).

There is no "general agent" — an agent is always an agent OF a society. The agent atom is the
cast×society *binding* (`agent:<gid>:<space>:<cast>`): it names which persona (cast) is a
participant of which space, and it is the anchor for two things the bare cast cannot carry —

  • **responsibilities** (責務) — incoming `responsible:*` links from the society (chairman /
    scribe / broadcaster / a workflow step's approver-exec). Separate from the permission `role:`.
  • **per-workflow state** — the reserved CSL-state seam: state lives on the agent×workflow
    junction (`agent:state` links), NOT inside the CSL. One cast → many agents (one per society),
    each with its own state.

Storage lives in the GROUP engine (society-scoped, `scope:group_<gid>`), like the society object
and its feed — so every admitted agent of the society can read it (the R1 invariant: chronon
`:members` and agent bindings written under the group scope are enumerable from every member's
session). Minting an agent is `society.admit` (in `society.py`); this model is the READ surface
plus the agent's own per-workflow state.

Anonymity note: the FEED stays pseudonymous (an utterance shows only the cast name). The agent
binding additionally records the controlling `client` — that is governance metadata (who may act
as this agent), the same client-level bookkeeping `society.created_by` / `disclose` already keep,
and it never changes what the feed shows.
"""
import json
import logging
import time
from typing import Any, Dict, List, Optional

from lib.akasha.concepts.base import BaseConcept

logger = logging.getLogger("Akasha.Concept.Agent")

DEFAULT_SPACE = "main"


class AgentConcept(BaseConcept):
    CONCEPT_PREFIX = "agent"
    CONCEPT_LABEL = "Agent — a cast admitted to a society (the cast×society binding); holds responsibilities + per-workflow state"
    CONCEPT_METHODS = {
        "open":        {"op": "op_open"},          # read a binding
        "ls":          {"op": "op_list"},          # list a society's agents
        "responsible": {"op": "op_responsible"},   # an agent's duties (incoming responsible:*)
        "state":       {"op": "op_state"},         # read/write per-workflow state (write-gated)
    }

    # ── conventions (shared with society.py — keep in lock-step) ──────────────────
    @staticmethod
    def _sid(gid: str, space: str) -> str:
        return f"{gid}/{space}"

    @staticmethod
    def _agents_set(gid: str, space: str) -> str:
        return f"soc:{gid}:agents" if space == DEFAULT_SPACE else f"soc:{gid}:{space}:agents"

    @staticmethod
    def _society_alias(gid: str, space: str) -> str:
        return f"society:{gid}:{space}"

    # ── plumbing ──────────────────────────────────────────────────────────────────
    def _client(self) -> str:
        return getattr(self.session, "client_id", "system")

    def _group_engine(self, gid: str):
        ge = getattr(self.session, "group_engines", {}).get(gid)
        if ge is None or f"scope:group_{gid}" not in (self.allowed_scopes or []):
            raise RuntimeError(f"Not a member of group '{gid}'.")
        return ge

    def _parse_agent_ref(self, agent: str) -> (str, str):
        """An agent ref is either an agent alias `agent:<gid>:<space>:<cast>` or an agent atom key.
        Returns (gid, space) so we can reach the right group engine; space defaults to main."""
        agent = (agent or "").strip()
        if not agent:
            raise ValueError("an agent is required (agent:<gid>:<space>:<cast>).")
        if agent.startswith("agent:"):
            parts = agent.split(":")
            if len(parts) >= 3:
                return parts[1], parts[2]
        # a raw key — we must scan groups the caller belongs to (rare path); resolve via meta below.
        for gid in getattr(self.session, "group_engines", {}):
            ge = getattr(self.session, "group_engines", {}).get(gid)
            try:
                row = ge.core.get_chunk_raw(agent)
            except Exception:
                row = None
            if row:
                try:
                    m = json.loads(row.get("meta") or "{}")
                except Exception:
                    m = {}
                if m.get("concept") == "agent":
                    return m.get("group", gid), m.get("space", DEFAULT_SPACE)
        raise RuntimeError(f"Cannot locate agent '{agent}'.")

    def _resolve_agent(self, ge, agent: str) -> Optional[str]:
        """Resolve an agent ref (alias or key) to its atom key in the group engine."""
        agent = (agent or "").strip()
        if not agent:
            return None
        row = None
        try:
            row = ge.core.get_chunk_raw(agent)
        except Exception:
            row = None
        if row:
            return agent
        return ge.resolve_alias(agent)

    def _agent_meta(self, ge, key: str) -> Dict[str, Any]:
        row = ge.core.get_chunk_raw(key) or {}
        try:
            return json.loads(row.get("meta") or "{}")
        except Exception:
            return {}

    # ── operators ────────────────────────────────────────────────────────────────
    def op_open(self, agent: str = "") -> Dict[str, Any]:
        """Read an agent binding: its cast, society, responsibilities, and per-workflow state keys.
        agent.open agent=agent:<gid>:<space>:<cast>"""
        gid, space = self._parse_agent_ref(agent)
        ge = self._group_engine(gid)
        key = self._resolve_agent(ge, agent)
        if not key:
            raise RuntimeError(f"No such agent '{agent}'.")
        m = self._agent_meta(ge, key)
        if m.get("concept") != "agent":
            raise ValueError("that atom is not an agent binding.")
        cast = next((l.get("dst") for l in ge.core.get_adjacent_links(key, "agent:as")), "")
        society = next((l.get("dst") for l in ge.core.get_adjacent_links(key, "agent:in")), "")
        duties = self._duties(ge, gid, space, key)
        states = [l.get("dst") for l in ge.core.get_adjacent_links(key, "agent:state")]
        return {"type": "agent", "agent": agent, "key": key, "society_id": self._sid(gid, space),
                "cast": cast, "cast_name": m.get("cast_name", ""), "client": m.get("client", ""),
                "responsibilities": duties, "state_atoms": states}

    def op_list(self, society: str = "", group: str = "", name: str = "", space: str = "") -> Dict[str, Any]:
        """List the agents (admitted casts) of a society: agent.ls society=<gid>/<space>."""
        gid, space = self._resolve_space(society, group, name, space)
        ge = self._group_engine(gid)
        rows = []
        for key in ge.core.get_collection_members(self._agents_set(gid, space)):
            m = self._agent_meta(ge, key)
            if m.get("concept") != "agent":
                continue
            cast = next((l.get("dst") for l in ge.core.get_adjacent_links(key, "agent:as")), "")
            rows.append({"agent": self._agent_alias_of(m, gid, space), "key": key, "cast": cast,
                         "cast_name": m.get("cast_name", ""), "client": m.get("client", ""),
                         "responsibilities": self._duties(ge, gid, space, key)})
        return {"society_id": self._sid(gid, space), "count": len(rows), "agents": rows}

    def op_responsible(self, agent: str = "") -> Dict[str, Any]:
        """The duties an agent bears in its society — the incoming responsible:* links (chairman /
        scribe / broadcaster / approve:<step> / exec:<step>). agent.responsible agent=<agent>"""
        gid, space = self._parse_agent_ref(agent)
        ge = self._group_engine(gid)
        key = self._resolve_agent(ge, agent)
        if not key:
            raise RuntimeError(f"No such agent '{agent}'.")
        return {"type": "agent_responsible", "agent": agent, "society_id": self._sid(gid, space),
                "responsibilities": self._duties(ge, gid, space, key)}

    def op_state(self, agent: str = "", wf: str = "", key: str = "", value: str = "") -> Dict[str, Any]:
        """Read or write an agent's PER-WORKFLOW state (the reserved CSL-state seam — state lives on
        the agent×workflow junction, not in the CSL). With no key= it reads the whole state map for
        wf=; with key=[ value=] it writes one field (B.5 gate: the agent itself, or chairman/admin).
        agent.state agent=<agent> wf=<workflow> [key= value=]"""
        gid, space = self._parse_agent_ref(agent)
        ge = self._group_engine(gid)
        akey = self._resolve_agent(ge, agent)
        if not akey:
            raise RuntimeError(f"No such agent '{agent}'.")
        wf = (wf or "").strip()
        if not wf:
            raise ValueError("agent.state requires wf= (state is keyed by workflow).")
        m = self._agent_meta(ge, akey)
        state_alias = f"agent:state:{gid}:{space}:{m.get('cast_slug', akey[:8])}:{wf}"
        skey = ge.resolve_alias(state_alias)
        if str(key or "").strip() == "":                 # READ
            data = self._state_map(ge, skey) if skey else {}
            return {"type": "agent_state", "agent": agent, "wf": wf, "state": data}
        # WRITE — gate: the agent itself (its controlling client), or chairman/admin.
        client = self._client()
        if not (m.get("client") == client or self._is_admin() or self._is_chairman(ge, gid, space, client)):
            raise RuntimeError("only the agent itself, the chairman, or an admin may write agent state.")
        data = self._state_map(ge, skey) if skey else {}
        data[str(key).strip()] = value
        author = client
        content = json.dumps({"wf": wf, "agent": akey, "state": data}, ensure_ascii=False)
        new_key = ge.put_atom(content, {"concept": "agent_state", "type": "agent_state",
                                        "agent": akey, "wf": wf, "updated_by": author,
                                        "updated_at": time.time()}, author=author)
        ge.core.put_alias(new_key, state_alias)
        # rebind the agent→state link to the freshest state atom for this wf (idempotent)
        for l in ge.core.get_adjacent_links(akey, "agent:state"):
            dm = self._agent_meta(ge, l.get("dst"))
            if dm.get("wf") == wf:
                ge.core.remove_link_raw(akey, l.get("dst"), "agent:state")
        ge.put_link(akey, new_key, "agent:state", author=author)
        return {"type": "agent_state", "agent": agent, "wf": wf, "state": data, "status": "set"}

    # ── helpers ────────────────────────────────────────────────────────────────────
    def _resolve_space(self, society: str, group: str, name: str, space: str) -> (str, str):
        society = (society or "").strip()
        if society:
            gid, _, nm = society.partition("/")
            return gid.strip(), (nm.strip() or DEFAULT_SPACE)
        gid = (group or "").strip()
        nm = (space or "").strip() or (name or "").strip() or DEFAULT_SPACE
        if not gid:
            raise ValueError("a society or group is required.")
        return gid, nm

    def _agent_alias_of(self, meta: Dict[str, Any], gid: str, space: str) -> str:
        slug = meta.get("cast_slug") or (meta.get("cast_name") or "").lower().replace(" ", "_")
        return f"agent:{gid}:{space}:{slug}" if slug else ""

    def _duties(self, ge, gid: str, space: str, agent_key: str) -> List[str]:
        society = ge.resolve_alias(self._society_alias(gid, space))
        out = []
        if society:
            for l in ge.core.get_adjacent_links(society):
                rel = l.get("rel", "")
                if rel.startswith("responsible:") and l.get("dst") == agent_key:
                    out.append(rel.split(":", 1)[1])
        return out

    def _state_map(self, ge, skey: str) -> Dict[str, Any]:
        if not skey:
            return {}
        row = ge.core.get_chunk_raw(skey) or {}
        try:
            return (json.loads(row.get("content") or "{}") or {}).get("state", {})
        except Exception:
            return {}

    def _is_admin(self) -> bool:
        role = getattr(self.session, "role", None)
        return getattr(role, "value", str(role)) == "admin"

    def _is_chairman(self, ge, gid: str, space: str, client: str) -> bool:
        society = ge.resolve_alias(self._society_alias(gid, space))
        if not society:
            return False
        row = ge.core.get_chunk_raw(society) or {}
        try:
            m = json.loads(row.get("meta") or "{}")
        except Exception:
            m = {}
        return bool(client) and m.get("chairman_client") == client
