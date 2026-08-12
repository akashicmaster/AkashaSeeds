"""
ChrononConcept — the chronon network (seeds13, Part B.2; the second grand principle's spine).

A **chronon** is a *semantic state boundary* (意味状態境界) kept in the graph in native form (links +
sets), NOT flushed into a linear stream. It is the coarse, client-visible, programmable layer;
Harmonia (WriteQueue/JCL) is the fine layer that executes underneath.

The three things that make a chronon a chronon (do not conflate them):
  • **body** — a small declarative, directly-executable state script (`.ak`/CSL shape) describing
    the state/transition this boundary seals. Replay/execution is link+set ops, no parsing.
  • **members** (`chronon:<sid>:<id>:members`) — the semantic boundary: the meaning-bound
    *references* that belong to this state. **NEITHER a snapshot** (not "every atom alive at seal
    time" — that bloats and re-derives full state) **NOR a delta** (not "only atoms since the last
    chronon" — that is what the linear *log* already is). The scribe curates it.
  • **the change (差分)** — how we got here / what varied — lives in `chronon:mutates` + the `body`,
    **never in members**.

Two relations: `chronon:next` = temporal succession (reverse = the past; multiple = branches);
`chronon:mutates` = variation/derivation. Their succession-and-mutation IS Akasha Time.

Aspect: PERFECTIVE = record (議事); PROSPECTIVE = scenario. Flipping aspect is a **meta-only**
transition — the body (an Operand) is immutable (R5). Identity is content-addressed (R6).

Storage is the GROUP engine (society-scoped), so every admitted agent can traverse it (R1).
"""
import hashlib
import json
import logging
import time
from typing import Any, Dict, List, Optional

from lib.akasha.concepts.base import BaseConcept

logger = logging.getLogger("Akasha.Concept.Chronon")

DEFAULT_SPACE = "main"
PERFECTIVE = "perfective"
PROSPECTIVE = "prospective"


class ChrononConcept(BaseConcept):
    CONCEPT_PREFIX = "chronon"
    CONCEPT_LABEL = "Chronon — a semantic state boundary on a society's chronon network (Akasha Time)"
    CONCEPT_METHODS = {
        "seal":   {"op": "op_seal"},     # scribe/chairman/admin: draw a boundary, advance society:now (CAS)
        "read":   {"op": "op_read"},
        "ls":     {"op": "op_list"},
        "next":   {"op": "op_next"},
        "prev":   {"op": "op_prev"},
        "replay": {"op": "op_replay"},
    }

    # ── conventions ────────────────────────────────────────────────────────────────
    @staticmethod
    def _sid(gid: str, space: str) -> str:
        return f"{gid}/{space}"

    @staticmethod
    def _society_alias(gid: str, space: str) -> str:
        return f"society:{gid}:{space}"

    @staticmethod
    def _chronons_set(gid: str, space: str) -> str:
        return f"chronons:{gid}:{space}"

    @staticmethod
    def _members_set(sid: str, cid: str) -> str:
        return f"chronon:{sid}:{cid}:members"

    @staticmethod
    def _chronon_alias(sid: str, cid: str) -> str:
        return f"chronon:{sid}:{cid}"

    # ── plumbing ────────────────────────────────────────────────────────────────────
    def _client(self) -> str:
        return getattr(self.session, "client_id", "system")

    def _group_engine(self, gid: str):
        ge = getattr(self.session, "group_engines", {}).get(gid)
        if ge is None or f"scope:group_{gid}" not in (self.allowed_scopes or []):
            raise RuntimeError(f"Not a member of group '{gid}'.")
        return ge

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

    def _meta(self, ge, key: str) -> Dict[str, Any]:
        row = ge.core.get_chunk_raw(key) or {}
        try:
            return json.loads(row.get("meta") or "{}")
        except Exception:
            return {}

    def _is_admin(self) -> bool:
        role = getattr(self.session, "role", None)
        return getattr(role, "value", str(role)) == "admin"

    def _holder_client(self, ge, society_key: str, rel: str) -> str:
        """The controlling client of the agent holding a responsibility (chairman/scribe)."""
        for l in ge.core.get_adjacent_links(society_key, rel):
            return self._meta(ge, l.get("dst")).get("client", "")
        return ""

    def _gate_seal(self, ge, society_key: str) -> str:
        """chronon.seal gate (B.5): scribe OR chairman OR admin. Returns the acting role tag."""
        client = self._client()
        if self._is_admin():
            return "admin"
        smeta = self._meta(ge, society_key)
        if client and smeta.get("chairman_client") == client:
            return "chairman"
        if client and self._holder_client(ge, society_key, "responsible:scribe") == client:
            return "scribe"
        raise RuntimeError("only the scribe, the chairman, or an admin may seal a chronon.")

    def _resolve_ref(self, ge, ref: str) -> Optional[str]:
        ref = (ref or "").strip()
        if not ref:
            return None
        try:
            if ge.core.get_chunk_raw(ref):
                return ref
        except Exception:
            pass
        return ge.resolve_alias(ref)

    def _frontiers(self, ge, society_key: str) -> List[str]:
        return [l.get("dst") for l in ge.core.get_adjacent_links(society_key, "society:now")]

    # ── the seal (shared with scenario.run / society.workflow) ───────────────────────
    def _mint(self, ge, gid: str, space: str, society_key: str, body: str,
              label: str = "", members: List[str] = None, aspect: str = PERFECTIVE,
              from_key: str = "", mutates_key: str = "", scribe: str = "",
              advance_now: bool = True) -> Dict[str, Any]:
        """Mint one chronon and (optionally) advance society:now by compare-and-set. This is the
        single sealing primitive; scenario.run and society.workflow call it too.

        R6 identity: content-addressed over (society|body|mutates) — STABLE across the aspect flip,
        so R5 (aspect is meta-only, body immutable) and R6 (content-addressed, idempotent) both
        hold. Aspect lives in meta and may flip without re-keying."""
        sid = self._sid(gid, space)
        ident = f"{sid}\x1f{body}\x1f{mutates_key or ''}"
        key = hashlib.sha256(ident.encode("utf-8")).hexdigest()
        # per-society monotone readable id
        existing = list(ge.core.get_collection_members(self._chronons_set(gid, space)) or [])
        cid = f"c{len(existing) + 1}"
        meta = {"type": "chronon", "concept": "chronon", "group": gid, "space": space, "sid": sid,
                "aspect": aspect, "scribe": scribe or self._client(), "society": society_key,
                "label": (label or "").strip(), "system_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "cid": cid, "created_at": time.time()}
        ge.core.put_chunk_raw(key, body, json.dumps(meta, ensure_ascii=False),
                              self._client(), "verified", time.time())
        ge.core.put_chunk_access(key, [ge.scope])
        ge.core.put_alias(key, self._chronon_alias(sid, cid))
        ge.add_to_set(self._chronons_set(gid, space), key)
        ge.put_link(key, society_key, "chronon:of", author=self._client())
        # members = the semantic boundary (references, curated) — never snapshot/delta
        for ref in (members or []):
            rk = self._resolve_ref(ge, ref)
            if rk:
                ge.add_to_set(self._members_set(sid, cid), rk)
        # succession + variation
        if from_key:
            ge.put_link(from_key, key, "chronon:next", author=self._client())
        if mutates_key:
            ge.put_link(key, mutates_key, "chronon:mutates", author=self._client())
        # advance society:now by compare-and-set (R4 — the lost-update guard). The new chronon is a
        # frontier; whether it REPLACES from_key (linear advance) or ADDS alongside it (a branch)
        # depends on whether from_key is still a frontier — decided atomically here (the WriteQueue
        # serialises, so two concurrent seals from one branch-point become two frontiers, dropping
        # neither, instead of one blind advance clobbering the other).
        moved = "no"
        if advance_now:
            frontiers = self._frontiers(ge, society_key)
            if from_key and from_key in frontiers:
                ge.core.remove_link_raw(society_key, from_key, "society:now")   # linear advance
                ge.put_link(society_key, key, "society:now", author=self._client())
                moved = "advance"
            elif from_key:
                ge.put_link(society_key, key, "society:now", author=self._client())  # branch (fork)
                moved = "branch"
            else:
                ge.put_link(society_key, key, "society:now", author=self._client())  # first seal
                moved = "advance"
        return {"chronon": self._chronon_alias(sid, cid), "key": key, "cid": cid, "aspect": aspect,
                "advanced_now": moved != "no", "frontier_op": moved, "members": len(members or [])}

    # ── operators ────────────────────────────────────────────────────────────────────
    def op_seal(self, society: str = "", group: str = "", name: str = "", space: str = "",
                label: str = "", members: str = "", body: str = "", **kw) -> Dict[str, Any]:
        """Draw a semantic state boundary — mint a PERFECTIVE chronon and advance society:now.

        `from=<chronon>` names the frontier to extend (CAS-checked; **required when society:now
        holds >1 frontier**, defaulted to the single frontier otherwise). `members=` is a
        comma-separated list of the references the scribe designates as belonging to this state's
        MEANING (neither snapshot nor delta). `label=` is a human tag. `body=` is an optional
        declarative transition script (a descriptor is synthesized when omitted). Gate: scribe OR
        chairman OR admin."""
        from_ = str(kw.get("from", "") or "").strip()
        gid, space = self._resolve_space(society, group, name, space)
        ge = self._group_engine(gid)
        society_key = ge.resolve_alias(self._society_alias(gid, space))
        if not society_key:
            raise RuntimeError(f"Society '{self._sid(gid, space)}' does not exist — create it first.")
        role = self._gate_seal(ge, society_key)
        # resolve the frontier to extend. A `from` that is still a frontier advances it linearly;
        # a `from` that is a historical (non-frontier) node forks a new branch; both are decided by
        # CAS in _mint. Only the ambiguous "which of several frontiers?" case is refused up front.
        frontiers = self._frontiers(ge, society_key)
        from_key = self._resolve_ref(ge, from_) if from_ else ""
        if not from_key:
            if len(frontiers) > 1:
                raise ValueError("society:now has multiple frontiers — pass from=<chronon> to name "
                                 "the one to extend (lost-update guard, R4).")
            from_key = frontiers[0] if frontiers else ""
        mem = [r.strip() for r in (members or "").split(",") if r.strip()]
        lbl = (label or "").strip()
        transition = (body or "").strip() or (f"# chronon {lbl or 'seal'} @ {self._sid(gid, space)}\n"
                                              + "".join(f"# member {r}\n" for r in mem))
        scribe_client = self._client()
        res = self._mint(ge, gid, space, society_key, transition, label=lbl, members=mem,
                         aspect=PERFECTIVE, from_key=from_key, mutates_key=from_key,
                         scribe=scribe_client)
        res["status"] = "sealed"
        res["role"] = role
        res["society_id"] = self._sid(gid, space)
        return res

    def op_read(self, chronon: str = "") -> Dict[str, Any]:
        """Read one chronon: its body, aspect, scribe, members (the semantic boundary), and its
        next/mutates edges. chronon.read chronon=chronon:<gid>/<space>:<id>"""
        gid, space, key = self._locate(chronon)
        ge = self._group_engine(gid)
        m = self._meta(ge, key)
        row = ge.core.get_chunk_raw(key) or {}
        sid = self._sid(gid, space)
        mem = list(ge.core.get_collection_members(self._members_set(sid, m.get("cid", ""))) or [])
        nxt = [self._alias_of(ge, l.get("dst")) for l in ge.core.get_adjacent_links(key, "chronon:next")]
        mut = [self._alias_of(ge, l.get("dst")) for l in ge.core.get_adjacent_links(key, "chronon:mutates")]
        return {"type": "chronon", "chronon": self._alias_of(ge, key), "key": key,
                "aspect": m.get("aspect", ""), "label": m.get("label", ""), "scribe": m.get("scribe", ""),
                "system_time": m.get("system_time", ""), "body": row.get("content") or "",
                "members": mem, "member_count": len(mem), "next": nxt, "mutates": mut,
                "society_id": sid}

    def op_list(self, society: str = "", group: str = "", name: str = "", space: str = "") -> Dict[str, Any]:
        """List a society's chronons in seal order, with aspect + label. chronon.ls society=<sid>"""
        gid, space = self._resolve_space(society, group, name, space)
        ge = self._group_engine(gid)
        rows = []
        for key in ge.core.get_collection_members(self._chronons_set(gid, space)):
            m = self._meta(ge, key)
            if m.get("concept") != "chronon":
                continue
            rows.append({"chronon": self._alias_of(ge, key), "key": key, "cid": m.get("cid", ""),
                         "aspect": m.get("aspect", ""), "label": m.get("label", ""),
                         "at": m.get("created_at", 0)})
        rows.sort(key=lambda r: r["at"])
        frontiers = [self._alias_of(ge, k) for k in self._frontiers(ge, ge.resolve_alias(self._society_alias(gid, space)) or "")]
        return {"society_id": self._sid(gid, space), "count": len(rows), "chronons": rows,
                "frontiers": frontiers}

    def op_next(self, chronon: str = "") -> Dict[str, Any]:
        """The successor chronon(s) — the future(s) branching forward (Akasha Time forward)."""
        gid, space, key = self._locate(chronon)
        ge = self._group_engine(gid)
        nxt = [self._alias_of(ge, l.get("dst")) for l in ge.core.get_adjacent_links(key, "chronon:next")]
        return {"chronon": self._alias_of(ge, key), "next": nxt, "count": len(nxt)}

    def op_prev(self, chronon: str = "") -> Dict[str, Any]:
        """The predecessor chronon(s) — reverse traversal = the past record (Akasha Time reverse)."""
        gid, space, key = self._locate(chronon)
        ge = self._group_engine(gid)
        prev = []
        for other in ge.core.get_collection_members(self._chronons_set(gid, space)):
            for l in ge.core.get_adjacent_links(other, "chronon:next"):
                if l.get("dst") == key:
                    prev.append(self._alias_of(ge, other))
        return {"chronon": self._alias_of(ge, key), "prev": prev, "count": len(prev)}

    def op_replay(self, society: str = "", group: str = "", name: str = "", space: str = "",
                  limit: Any = 200) -> Dict[str, Any]:
        """Reconstruct the society's chronon network in seal order — Akasha Time as it unfolded."""
        ls = self.op_list(society=society, group=group, name=name, space=space)
        try:
            lim = max(1, min(int(limit), 1000))
        except (TypeError, ValueError):
            lim = 200
        seq = [{"n": i + 1, "chronon": r["chronon"], "aspect": r["aspect"], "label": r["label"]}
               for i, r in enumerate(ls["chronons"][:lim])]
        return {"society_id": ls["society_id"], "steps": len(seq), "sequence": seq,
                "frontiers": ls["frontiers"]}

    # ── helpers ────────────────────────────────────────────────────────────────────
    def _locate(self, chronon: str) -> (str, str, str):
        """Resolve a chronon ref (alias `chronon:<gid>/<space>:<id>` or key) to (gid, space, key)."""
        chronon = (chronon or "").strip()
        if not chronon:
            raise ValueError("a chronon is required.")
        if chronon.startswith("chronon:") and "/" in chronon:
            head = chronon[len("chronon:"):]
            sidpart, _, _cid = head.partition(":")
            gid, _, space = sidpart.partition("/")
            gid, space = gid.strip(), (space.strip() or DEFAULT_SPACE)
            ge = self._group_engine(gid)
            key = self._resolve_ref(ge, chronon)
            if not key:
                raise RuntimeError(f"No such chronon '{chronon}'.")
            return gid, space, key
        # a raw key — scan the caller's groups
        for gid in getattr(self.session, "group_engines", {}):
            ge = getattr(self.session, "group_engines", {}).get(gid)
            m = self._meta(ge, chronon)
            if m.get("concept") == "chronon":
                return m.get("group", gid), m.get("space", DEFAULT_SPACE), chronon
        raise RuntimeError(f"Cannot locate chronon '{chronon}'.")

    def _alias_of(self, ge, key: str) -> str:
        for a in ge.get_aliases_by_key(key) or []:
            if a.startswith("chronon:"):
                return a
        return key
