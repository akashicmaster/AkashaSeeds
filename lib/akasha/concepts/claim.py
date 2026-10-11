"""
Claim Concept Model — claim.* (B1 §A6).

A claim is a stated assertion ABOUT a bench (the seminar's or the driver's). It is a first-class
atom, but its STATUS is never stored — it is DERIVED at read time from whether its evidence resolves
and holds:

    attached      ≥ 1 `evidenced_by` evidence resolves
    unattached    no evidence
    contradicted  every evidence's own status negates it (a failed execution coordinate, evidence
                  whose alias a newer atom has taken, a retired condition)

There is no `false`. A guest reads only counts (never the claim texts); a member reads the rows.
Written UNIVERSAL (nucleus) so a public bench's claims are guest-readable; a group bench's claims
are its members' (the scope gate decides, by membership).
"""
import hashlib
import logging
from typing import Any, Dict, List

from lib.akasha.concepts.workflow import WorkflowConcept
from lib.akasha.concepts._universal import slug as _uslug

logger = logging.getLogger("Harmonia.Concept.Claim")


class ClaimConcept(WorkflowConcept):
    """claim.* — assertions about a bench, with a DERIVED status (B1 §A6)."""

    CONCEPT_PREFIX = "claim"
    CONCEPT_LABEL = "Claim — a bench assertion whose status is derived from its evidence"
    CONCEPT_METHODS = {
        "make":   {"op": "op_make", "action": "record",
                   "desc": "State a claim about a bench: claim.make bench= text= [about=] [evidence=<alias>]"},
        "attach": {"op": "op_attach", "action": "record",
                   "desc": "Attach evidence to a claim: claim.attach bench= claim= evidence=<alias>"},
        "status": {"op": "op_status", "action": "read",
                   "desc": "The claim's derived status (guest: counts only): claim.status bench= [claim=]"},
    }

    # ── helpers ──────────────────────────────────────────────────────────────────
    def _claims_set(self, name: str) -> str:
        balias = self._bench_alias(name)
        return "set:wb:%s:claims" % _uslug(balias[3:] if balias.startswith("wb:") else balias)

    def _evidence_negates(self, evkey: str) -> bool:
        """B1 §A6 — does this evidence's OWN status negate the claim it supports?"""
        alias = self._alias(evkey) or evkey
        m = self._meta(alias) or {}
        concept = m.get("concept")
        # SUPERSEDED — any evidence whose alias now resolves to a different key (a newer row took the
        # name). Read from the alias table, whatever the evidence's concept: the claim engine names no
        # application concept (the purge order §2).
        if alias and alias != evkey and self._key(alias) not in (None, evkey):
            return True
        # a sweep condition RETIRED
        if concept == "sweep_cond":
            return m.get("status") == "retired"
        # an EXECUTION COORDINATE whose block ended failed (a member observation failed). The
        # observation atom's TOP-LEVEL status is the source-atom lifecycle (`ACQUIRED`); the op's
        # ok/failed outcome lives in `source_metadata.status` (what `_observe` recorded).
        if str(alias).startswith("cronon:"):
            for ok in self._members(alias):
                om = self._meta(self._alias(ok) or ok) or {}
                if om.get("status") == "failed" or (om.get("source_metadata") or {}).get("status") == "failed":
                    return True
            return False
        return False

    def _derive_status(self, claim_key: str) -> str:
        """B1 §A6 — attached / unattached / contradicted, computed from the evidence at read time."""
        ev = [dst for (dst, _rel) in self._links(claim_key, "evidenced_by")]
        ev = [self._key(e) or e for e in ev if e]
        ev = [e for e in ev if e and self._meta(self._alias(e) or e)]
        if not ev:
            return "unattached"
        if all(self._evidence_negates(e) for e in ev):
            return "contradicted"
        return "attached"

    # ── ops ──────────────────────────────────────────────────────────────────────
    def op_make(self, bench: str = "", text: str = "", about: str = "", evidence: str = "",
                cast: str = "") -> Dict[str, Any]:
        name = bench
        gid = self._bench_gid(name); self._bind(gid)
        if not self._key(self._bench_alias(name)):
            raise ValueError(f"unknown bench '{name}' — bench.new it first")
        if not str(text).strip():
            raise ValueError("claim.make requires text=")
        balias = self._bench_alias(name)
        by = cast or self._client()
        cronon = self._akasha_now()
        sha8 = hashlib.sha256(("%s|%s|%s|%s" % (balias, by, text, cronon)).encode("utf-8")).hexdigest()[:8]
        alias = "claim:%s" % sha8
        _prev = getattr(self, "_space", ""); self._space = ""     # universal — guest-readable
        try:
            key = self._mk(alias, "[%s] %s" % (alias, text),
                           {"concept": "claim", "bench": balias, "text": text, "by": by,
                            "cronon": cronon, "at_seq": cronon, "about": about or None,
                            "author": self._client()})
            self._add_to_set(self._claims_set(name), key)
            if evidence:
                self._link(alias, self._key(evidence) or evidence, "evidenced_by")
        finally:
            self._space = _prev
        st = self._derive_status(key)
        logger.info("[claim] bench=%s by=%s status=%s evidence=%d", balias, by, st, 1 if evidence else 0)
        return {"status": "made", "claim": alias, "bench": balias, "by": by,
                "cronon": cronon, "derived_status": st}

    def op_attach(self, bench: str = "", claim: str = "", evidence: str = "") -> Dict[str, Any]:
        name = bench
        gid = self._bench_gid(name); self._bind(gid)
        ck = self._key(claim)
        if not ck:
            return {"status": "not_found", "claim": claim}
        if not evidence:
            raise ValueError("claim.attach requires evidence=")
        _prev = getattr(self, "_space", ""); self._space = ""
        try:
            self._link(claim, self._key(evidence) or evidence, "evidenced_by")
        finally:
            self._space = _prev
        return {"status": "attached", "claim": claim, "evidence": evidence,
                "derived_status": self._derive_status(ck)}

    def op_status(self, bench: str = "", claim: str = "") -> Dict[str, Any]:
        name = bench
        gid = self._bench_gid(name); self._bind(gid)
        balias = self._bench_alias(name)
        guest = self._is_guest()
        if claim:
            ck = self._key(claim)
            if not ck:
                return {"status": "not_found", "claim": claim}
            st = self._derive_status(ck)
            out = {"bench": balias, "claim": claim, "derived_status": st}
            if not guest:
                out["text"] = (self._meta(claim) or {}).get("text")
            return out
        counts = {"attached": 0, "unattached": 0, "contradicted": 0}
        rows = []
        for k in self._members(self._claims_set(name)):
            m = self._meta(self._alias(k) or k) or {}
            if m.get("concept") != "claim":
                continue
            st = self._derive_status(k)
            counts[st] = counts.get(st, 0) + 1
            if not guest:
                rows.append({"claim": self._alias(k) or k, "text": m.get("text"), "by": m.get("by"),
                             "status": st, "at_seq": m.get("at_seq")})
        res = {"bench": balias, "counts": counts}
        if not guest:
            res["claims"] = rows
        return res
