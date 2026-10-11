"""
Capability Concept Model — cap.* (B5 §A7).

OFFERED ≠ GRANTED. Provisioning declares, per society and role, the capabilities a role is OFFERED
(`set:cap:offered:<society>:<role>`, one member per `cap:<name>@<fingerprint8>` where the fingerprint is
the running seed's content_fingerprint[:8] — the P3 identity rule). What a caller is actually GRANTED is
a separate question, and since the one-gate order it is asked of `gate` — not of a second `operator:*`
table in the graph. `cap.ls` reports both: `offered` to anyone (guest-readable on a public bench),
`granted` = what `gate(caller, record, <bench>)` answers for this caller.

`effectful` marks a capability whose op leaves the world (station/broadcast/feed writes, any send) —
declared as `"effectful": True` on the concept's CONCEPT_METHODS entry, read here (and, later, by replay).
A member minted under an older fingerprint is kept and flagged `stale_build` (never removed).
"""
import json
import logging
import os
from typing import Any, Dict, List, Optional

from lib.akasha.concepts.workbench import WorkbenchConcept
from lib.akasha.concepts.base import BaseConcept
from lib.akasha.concepts._universal import slug as _uslug
from lib.akasha.api import gate as _gate

logger = logging.getLogger("Harmonia.Concept.Cap")

_EFFECTFUL_CACHE: Optional[set] = None

# World-leaving families whose ops are NOT concept methods carry no CONCEPT_METHODS `effectful`
# mark, so the package that owns each one DECLARES it (`effectful_families` in its manifest, or
# `"effectful": true` on an op entry — group 4). This module kept the two family names itself.


class CapabilityConcept(WorkbenchConcept):
    """`cap.*` — the capability surface (offered ≠ granted), P3 §A7."""

    CONCEPT_PREFIX = "cap"
    CONCEPT_LABEL = "Capability — what a role is OFFERED vs what a caller is GRANTED"
    CONCEPT_METHODS = {
        "ls": {"op": "op_ls", "action": "read",
               "args": ["role", "context", "bench"],
               "desc": "The capabilities a role is offered on a bench (guest) and, for a holder, granted: "
                       "cap.ls role= context=<bench> — offered[]{name,fingerprint,effectful,stale_build}"},
    }

    # ── fingerprint (P3 identity rule) ────────────────────────────────────────────
    @staticmethod
    def _fp8() -> str:
        """The running seed's content_fingerprint[:8] — the capability identity (matches the kernel's
        _build_fp). '' when unavailable (a dev tree with no akasha_build.json)."""
        try:
            proj = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            with open(os.path.join(proj, "akasha_build.json"), "r", encoding="utf-8") as f:
                return str((json.load(f) or {}).get("content_fingerprint") or "")[:8]
        except Exception:
            return ""

    # ── effectful families (read the CONCEPT_METHODS marks — the source of truth) ──
    @staticmethod
    def _effectful_families() -> set:
        """Concept prefixes that own at least one op declared `"effectful": True` (a world-leaving op).
        Walked once from every registered concept class (they are all imported at boot) and cached; a
        capability whose family is in this set is effectful."""
        global _EFFECTFUL_CACHE
        if _EFFECTFUL_CACHE is not None:
            return _EFFECTFUL_CACHE
        from lib.akasha.api import manifest as _manifest
        fams: set = set(_manifest.declared_effectful_families())
        seen: set = set()

        def _walk(cls):
            for sub in cls.__subclasses__():
                if sub in seen:
                    continue
                seen.add(sub)
                pref = getattr(sub, "CONCEPT_PREFIX", "")
                methods = getattr(sub, "CONCEPT_METHODS", {}) or {}
                if pref:
                    for spec in methods.values():
                        if isinstance(spec, dict) and spec.get("effectful"):
                            fams.add(pref); break
                _walk(sub)

        try:
            _walk(BaseConcept)
        except Exception:
            pass
        _EFFECTFUL_CACHE = fams
        return fams

    def _effectful(self, name: str) -> bool:
        fam = str(name or "").split(":")[0].split(".")[0]
        return fam in self._effectful_families()

    # ── society-keyed Set names (must match B5 provisioning + B3 effective.at) ─────
    def _sid_key(self, bench: str) -> str:
        sid = str((self._meta(self._bench_alias(bench)) or {}).get("society_sid") or "")
        parts = sid.replace("/", ":").split(":")
        return ":".join(_uslug(p) for p in parts if p)

    @staticmethod
    def offered_set(sid_key: str, role: str) -> str:
        return "set:cap:offered:%s:%s" % (sid_key, _uslug(role))

    # ── cap.ls ─────────────────────────────────────────────────────────────────────
    def op_ls(self, role: str = "", context: str = "", bench: str = "") -> Dict[str, Any]:
        name = context or bench
        if not name:
            raise ValueError("cap.ls requires context=<bench>")
        if not role:
            raise ValueError("cap.ls requires role=")
        gid = self._bench_gid(name); self._bind(gid)
        sidk = self._sid_key(name)
        # the CURRENT build fingerprint: prefer the marker provisioning stamped (the runtime fp, so a
        # pinned/test build resolves too), fall back to akasha_build.json.
        cur = str((self._meta("cap:build") or {}).get("fingerprint") or "") or self._fp8()
        offered: List[Dict[str, Any]] = []
        for k in self._members(self.offered_set(sidk, role)):
            m = self._meta(self._alias(k) or k) or {}
            if m.get("concept") != "capability":
                continue
            nm = m.get("cap_name") or ""
            fp = m.get("fingerprint") or ""
            offered.append({"name": nm, "fingerprint": fp, "effectful": self._effectful(nm),
                            "stale_build": bool(fp and cur and fp != cur)})
        offered.sort(key=lambda o: o.get("name") or "")
        out: Dict[str, Any] = {"role": role, "context": self._bench_alias(name), "offered": offered}
        # granted — what THIS caller may actually do here, asked of the gate and nothing else.
        # The old per-family `responsible:` table is gone with `_grant_ok` (ruling §5), so one
        # question answers the whole list: may this caller OPERATE this bench?
        #
        # `record`, not `run`. A capability is a bench op and the bench-op default action is
        # `record`; `run` carries step 4's RUN FACTS (declared ∩ armed ∩ source_ready ∩
        # headroom), which are facts about a declared WORKLOAD, not about a bench. Asking `run`
        # here made `cap.ls` on an ordinary research bench answer `declared` — a refusal naming a
        # Set that has nothing to say about benches.
        # The KEY is present only for a holder, which is the contract `offered ≠ granted` states
        # and the shape the rooms read: `offered` to anyone, `granted` to whoever may operate the
        # bench. One question decides both the list and whether there is a list — a caller the
        # gate does not admit is not answered "you hold nothing", it is not asked.
        ok, _why = _gate.gate(self._client(), _gate.RECORD, self._bench_alias(name))
        if ok:
            out["granted"] = [{"name": o["name"]} for o in offered]
        return out
