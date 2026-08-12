"""
ScenarioConcept — a PROSPECTIVE chronon sub-network written in advance (seeds13, Part B.2 / law 2).

**chronon (past = PERFECTIVE) ≡ scenario (future = PROSPECTIVE)** — ONE structure, opposite time.
A scenario is a chain of chronons authored *before* they happen (`aspect=prospective`); running it
walks `chronon:next` and flips each PROSPECTIVE → PERFECTIVE — it *becomes the record*. Copying a
perfective sub-network back to prospective is re-execution.

Two invariants this model must hold (B.10):
  • **R5 — aspect inversion is a META transition; the body (an Operand) is immutable.** The flip
    rewrites meta only (aspect + the actual execution scribe/system_time); the chronon's body and
    its content-address key are untouched. A run that would produce a *different* transition mints
    a NEW chronon (chronon:mutates the original), it never edits the old body.
  • **R2 — a body executes under the RUNNING agent's gate, ops allowlisted.** The op each body line
    would invoke is checked against the JCL blocklist (job.*/sys.su/user.*/grp.*/session.*/auth.*/
    destructive onto.*); a scribe-authored body carrying an admin op is refused when a lower-
    privilege executor runs it (only an admin may run such a body). This is the recipe
    `_ALLOWED_ENV_KEYS` design (B1), applied to chronon bodies.

Reuses ChrononConcept._mint for the actual seals, so scenario and record share one primitive.
"""
import json
import logging
import time
from typing import Any, Dict, List, Optional

from lib.akasha.concepts.base import BaseConcept
from lib.akasha.concepts.chronon import ChrononConcept, PERFECTIVE, PROSPECTIVE, DEFAULT_SPACE
from lib.akasha.jcl.validator import _BLOCKED_METHODS, _BLOCKED_PREFIXES

logger = logging.getLogger("Akasha.Concept.Scenario")


class ScenarioConcept(BaseConcept):
    CONCEPT_PREFIX = "scenario"
    CONCEPT_LABEL = "Scenario — a prospective chronon sub-network; running it flips it into the record"
    CONCEPT_METHODS = {
        "write": {"op": "op_write"},   # author a prospective chronon chain
        "run":   {"op": "op_run"},     # flip prospective → perfective (the record)
        "ls":    {"op": "op_list"},
    }

    def _client(self) -> str:
        return getattr(self.session, "client_id", "system")

    def _group_engine(self, gid: str):
        ge = getattr(self.session, "group_engines", {}).get(gid)
        if ge is None or f"scope:group_{gid}" not in (self.allowed_scopes or []):
            raise RuntimeError(f"Not a member of group '{gid}'.")
        return ge

    def _chr(self) -> ChrononConcept:
        return ChrononConcept(self.session)

    @staticmethod
    def _resolve_space(society: str, group: str, name: str, space: str) -> (str, str):
        society = (society or "").strip()
        if society:
            gid, _, nm = society.partition("/")
            return gid.strip(), (nm.strip() or DEFAULT_SPACE)
        gid = (group or "").strip()
        nm = (space or "").strip() or (name or "").strip() or DEFAULT_SPACE
        if not gid:
            raise ValueError("a society or group is required.")
        return gid, nm

    @staticmethod
    def _scenario_alias(gid: str, space: str, sname: str) -> str:
        return f"scenario:{gid}:{space}:{sname}"

    def _meta(self, ge, key: str) -> Dict[str, Any]:
        row = ge.core.get_chunk_raw(key) or {}
        try:
            return json.loads(row.get("meta") or "{}")
        except Exception:
            return {}

    def _is_admin(self) -> bool:
        role = getattr(self.session, "role", None)
        return getattr(role, "value", str(role)) == "admin"

    @staticmethod
    def _split_steps(script: str) -> List[str]:
        """A scenario script is one step per non-empty, non-comment line (or ';'-separated)."""
        out = []
        for raw in (script or "").replace(";", "\n").split("\n"):
            s = raw.strip()
            if s and not s.startswith("#"):
                out.append(s)
        return out

    @staticmethod
    def _body_op(body: str) -> str:
        """The leading command token of a body line (what op it would invoke) — for the R2 gate."""
        for raw in (body or "").split("\n"):
            s = raw.strip()
            if s and not s.startswith("#"):
                return s.split()[0] if s.split() else ""
        return ""

    @classmethod
    def _op_blocked(cls, op: str) -> bool:
        op = (op or "").strip()
        return bool(op) and (op in _BLOCKED_METHODS or op.startswith(_BLOCKED_PREFIXES))

    # ── operators ────────────────────────────────────────────────────────────────
    def op_write(self, name: str = "", script: str = "", society: str = "", group: str = "",
                 space: str = "") -> Dict[str, Any]:
        """Author a PROSPECTIVE chronon chain (a plan) on a society. Each step of `script=` (one per
        line, or ';'-separated) becomes a prospective chronon linked by chronon:next; the root is
        aliased scenario:<gid>:<space>:<name>. Does NOT advance society:now (a plan is not the
        present). Gate: admin OR chairman (authoring the workflow face)."""
        gid, space = self._resolve_space(society, group, name if society or group else "", space)
        sname = (name or "").strip()
        if not sname:
            raise ValueError("scenario.write requires name=.")
        ge = self._group_engine(gid)
        society_key = ge.resolve_alias(f"society:{gid}:{space}")
        if not society_key:
            raise RuntimeError(f"Society '{gid}/{space}' does not exist — create it first.")
        # gate: admin OR chairman
        if not (self._is_admin() or self._meta(ge, society_key).get("chairman_client") == self._client()):
            raise RuntimeError("only an admin or the chairman may write a scenario/workflow.")
        steps = self._split_steps(script)
        if not steps:
            raise ValueError("scenario.write requires a non-empty script.")
        chr = self._chr()
        prev = ""
        root = ""
        made = []
        for i, body in enumerate(steps):
            res = chr._mint(ge, gid, space, society_key, body, label=f"{sname}:{i+1}",
                            members=[], aspect=PROSPECTIVE, from_key=prev, mutates_key="",
                            scribe=self._client(), advance_now=False)
            if i == 0:
                root = res["key"]
                ge.core.put_alias(root, self._scenario_alias(gid, space, sname))
            prev = res["key"]
            made.append(res["chronon"])
        return {"status": "written", "scenario": self._scenario_alias(gid, space, sname),
                "society_id": f"{gid}/{space}", "steps": len(made), "chronons": made}

    def op_run(self, name: str = "", society: str = "", group: str = "", space: str = "",
               **kw) -> Dict[str, Any]:
        """Run a scenario — walk its prospective chain and flip each chronon PROSPECTIVE→PERFECTIVE
        (meta-only, R5), attaching it after the society's current frontier and advancing society:now
        to the tail (the plan becomes the record). Gate: admin OR chairman OR an agent holding
        responsible:exec (B.5). Each body's op is checked against the R2 allowlist — an admin-only
        op in a body is refused unless the runner is an admin. `from=<chronon>` names the frontier
        to attach to when society:now has >1."""
        gid, space = self._resolve_space(society, group, name if society or group else "", space)
        sname = (name or "").strip()
        if not sname:
            raise ValueError("scenario.run requires name=.")
        ge = self._group_engine(gid)
        society_key = ge.resolve_alias(f"society:{gid}:{space}")
        if not society_key:
            raise RuntimeError(f"Society '{gid}/{space}' does not exist.")
        self._gate_run(ge, society_key)
        root = ge.resolve_alias(self._scenario_alias(gid, space, sname))
        if not root:
            raise RuntimeError(f"No scenario '{sname}' on {gid}/{space}.")
        # linearise the prospective chain from the root
        chain = self._chain(ge, root)
        # R2: pre-check every body's op against the allowlist under the RUNNING agent's authority
        is_admin = self._is_admin()
        for key in chain:
            op = self._body_op(ge.core.get_chunk_raw(key).get("content") or "")
            if self._op_blocked(op) and not is_admin:
                raise RuntimeError(f"body op '{op}' is not permitted for this runner "
                                   f"(privileged op — only an admin may run this body).")
        # attach after the current frontier, then flip the chain and advance now to the tail
        frontiers = [l.get("dst") for l in ge.core.get_adjacent_links(society_key, "society:now")]
        from_ = str(kw.get("from", "") or "").strip()
        anchor = ge.resolve_alias(from_) or from_ or (frontiers[0] if len(frontiers) == 1 else "")
        if len(frontiers) > 1 and not anchor:
            raise ValueError("society:now has multiple frontiers — pass from=<chronon> to attach the run.")
        if anchor and anchor in frontiers:
            if not any(l.get("dst") == root for l in ge.core.get_adjacent_links(anchor, "chronon:next")):
                ge.put_link(anchor, root, "chronon:next", author=self._client())
            ge.core.remove_link_raw(society_key, anchor, "society:now")
        flipped = []
        for key in chain:
            self._flip(ge, key)                       # meta-only aspect flip (R5)
            flipped.append(self._alias(ge, key))
        tail = chain[-1] if chain else ""
        if tail:
            ge.put_link(society_key, tail, "society:now", author=self._client())
        return {"status": "ran", "scenario": self._scenario_alias(gid, space, sname),
                "society_id": f"{gid}/{space}", "flipped": flipped, "steps": len(flipped),
                "now": self._alias(ge, tail) if tail else ""}

    def op_list(self, society: str = "", group: str = "", name: str = "", space: str = "") -> Dict[str, Any]:
        """List the scenarios (prospective roots) authored on a society."""
        gid, space = self._resolve_space(society, group, name, space)
        ge = self._group_engine(gid)
        rows = []
        for key in ge.core.get_collection_members(f"chronons:{gid}:{space}"):
            for a in ge.get_aliases_by_key(key) or []:
                if a.startswith(f"scenario:{gid}:{space}:"):
                    m = self._meta(ge, key)
                    rows.append({"scenario": a, "root": key, "aspect": m.get("aspect", "")})
        return {"society_id": f"{gid}/{space}", "count": len(rows), "scenarios": rows}

    # ── helpers ────────────────────────────────────────────────────────────────────
    def _gate_run(self, ge, society_key: str) -> None:
        client = self._client()
        if self._is_admin() or self._meta(ge, society_key).get("chairman_client") == client:
            return
        for l in ge.core.get_adjacent_links(society_key):
            if l.get("rel", "").startswith("responsible:exec"):
                if self._meta(ge, l.get("dst")).get("client") == client:
                    return
        raise RuntimeError("only an admin, the chairman, or a responsible:exec holder may run a scenario.")

    def _chain(self, ge, root: str) -> List[str]:
        """Linearise a prospective chain from root along chronon:next (first successor each hop)."""
        out, seen, cur = [], set(), root
        while cur and cur not in seen:
            out.append(cur)
            seen.add(cur)
            nxt = [l.get("dst") for l in ge.core.get_adjacent_links(cur, "chronon:next")]
            cur = nxt[0] if nxt else ""
        return out

    def _flip(self, ge, key: str) -> None:
        """R5: flip aspect prospective→perfective by rewriting META ONLY — body & key untouched."""
        row = ge.core.get_chunk_raw(key) or {}
        m = self._meta(ge, key)
        if m.get("aspect") == PERFECTIVE:
            return
        m["aspect"] = PERFECTIVE
        m["ran_by"] = self._client()
        m["system_time"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        ge.core.put_chunk_raw(key, row.get("content") or "", json.dumps(m, ensure_ascii=False),
                              row.get("author") or self._client(), "verified", time.time())
        ge.core.put_chunk_access(key, [ge.scope])

    def _alias(self, ge, key: str) -> str:
        for a in ge.get_aliases_by_key(key) or []:
            if a.startswith("chronon:"):
                return a
        return key
