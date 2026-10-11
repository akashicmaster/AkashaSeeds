"""
Workflow on a bench + the sync event (world-workbench-society spec v1.0, G3).

A workflow is the bench's SCRIPT and its LOG in one structure: entries ahead of the cursor are the
plan, entries behind it are the record. There is no canonical branch and no deletion — a rewind is
itself an observation (the record of rewinding is never rewound), and a branch shares the prefix
(content addressing makes it free). Every `wf.*` call tees ONE observation onto the bench stream
through the base `_perform`/`_observe`, so the workflow's whole life is replayable.

Entry atoms are aliased `workflow:<bench>:<branch>:<pos>` — NOT `wf:` (the old CSL `workflow.def`
templates own the `wf:` alias/set space; this is a different, bench-scoped layer). The command
namespace is `wf.*` (CONCEPT_PREFIX="wf"). Atoms live in the bench's engine (the society's group
engine for a closed bench), exactly like the bench's own atoms.

`wf.dispatch` is the SYNC EVENT: it mints an `exec:<bench>:<n>` membrane over a run of entry atoms
and records ONE world chronon on the shared axis (`world.tick reason=sync` → `set:world:default:sync`)
— dispatch to the world is a governed act (capability `responsible:decide`). The workflow original is
never touched; a corrected dispatch makes a NEW exec record.

This module reuses the workbench base (`WorkbenchConcept`) for the space-aware storage helpers, the
grant model, and the observing dispatcher — it is NOT a bench kind (no `KIND`), so it is never
registered as a `bench.new kind=…` target; it registers on its own `wf.*` prefix.
"""
import hashlib
import json
import logging
import os
import string
import time
from typing import Any, Dict, List, Optional, Tuple

from lib.akasha.concepts._universal import UniversalConcept, slug as _uslug
from lib.akasha.concepts.workbench import WorkbenchConcept

# The cell's internal RECORDER. Bookkeeping a run leaves behind (a sweep condition's terminal
# status, an execution trace) is the recorder's write, not the running client's: a workload's
# client is scoped to its own society and has no business writing on the bench it airs on. Its
# line is in `config/identity/assign.ak` (`system.librarian librarian`), reachable only over
# TRUST_INTERNAL, and every such write names the acting client in `by=`.
_RECORDER = "system.librarian"


logger = logging.getLogger("Harmonia.Concept.Workflow")

# The active kernel, injected once at boot (kernel.__init__). `wf.advance as=job` submits its steps
# through the SECURED job.submit path (validate_steps + owner-pinning) rather than reaching into the
# JCL worker directly — a concept must never bypass the kernel's write-model gates.
_ACTIVE_KERNEL = None

# S2-i — `wf.advance as=job` awaits its submitted job to a terminal state so it can record the
# execution trace (per-step cronon:executes) exactly as the inline path does. This is a POLL CAP,
# not a job soft-timeout: the poll returns the instant the job is DONE/FAILED, so a fast job (the
# common case) returns in well under a second; the cap only bounds a wedged/long job. A branch's
# own `timeout_s`, when the caller supplies one, overrides this.
_JOB_AWAIT_CAP_S = 3600.0


def active_kernel():
    """The kernel handed to this package at boot (the manifest's `bind`), or None before boot.
    A sibling concept reads it here instead of keeping a second global."""
    return _ACTIVE_KERNEL


def set_active_kernel(kernel) -> None:
    global _ACTIVE_KERNEL
    _ACTIVE_KERNEL = kernel


class WorkflowConcept(WorkbenchConcept):
    """`wf.*` — the workflow layer on a bench (script⇄log, branches, dispatch). Subclasses the
    workbench base for storage/grant/observe; declares no KIND (not a bench kind)."""

    CONCEPT_PREFIX = "wf"
    CONCEPT_LABEL = "Workflow — a bench's script and log in one structure (dispatch = the sync event)"

    # This family spells the bench `bench=`, where `bench.*` spells it `name=` (a `wf.*` op's
    # `name=` is the workflow's). Same declaration, the family's own word for it — inherited by
    # `sweep.*`, which is the surface where a missing target was measurable: a public bench is
    # nucleus-resident and readable by everyone, so its writes are refused by the table or by
    # nothing, and with no target there is no table answer to give.
    CONCEPT_TARGET_ARG = "bench"

    CONCEPT_METHODS: Dict[str, Any] = {
        "new":     {"op": "op_new_wf", "action": "record",
                    "desc": "Start a bench's workflow (1:1): wf.new bench="},
        "load":    {"op": "op_load", "action": "record",
                    "desc": "Load entries from an .ak file (one {method,params} per line, idempotent): "
                            "wf.load bench= name= file=<path> [branch=main]"},
        "write":   {"op": "op_write", "action": "record",
                    "desc": "Write one entry: wf.write bench= pos=<int> entry=<text|json> [branch=main]"},
        "cursor":  {"op": "op_cursor", "action": "read",
                    "desc": "The workflow cursor(s): wf.cursor bench= [branch=]"},
        "advance": {"op": "op_advance", "action": "record",
                    "desc": "Advance the cursor: wf.advance bench= [n=1] [branch=main] "
                            "[as=inline|job] [mode=execution|thought]"},
        "rewind":  {"op": "op_rewind", "action": "record",
                    "desc": "Move the cursor back: wf.rewind bench= pos=<int> [branch=main]"},
        "branch":  {"op": "op_branch", "action": "record",
                    "desc": "Fork a branch by position — wf.branch bench= from=<pos> name=<branch> — OR "
                            "a PARAMETERIZED sweep branch from a template: wf.branch bench= "
                            "from=<template> params=k=v,k=v [parent=main] [at=<pos>] (loads "
                            "config/<bench>/templates/<template>.ak with $param substitution, derives "
                            "the lineage branch name + cond8, joins set:wb:<b>:cond:<k>:<v>, idempotent)"},
        "ls":      {"op": "op_ls", "action": "read",
                    "desc": "List entries: wf.ls bench= [branch=main] [from=] [to=]"},
        "dispatch": {"op": "op_dispatch", "action": "record",
                     "desc": "Dispatch a run to the world (the sync event, needs decide): "
                             "wf.dispatch bench= branch=main from=<pos> to=<pos>"},
        "deviation": {"op": "op_deviation", "action": "record",
                      "desc": "Record a DEVIATION — `actual` diverged from the plan at a position: "
                              "wf.deviation bench= branch= pos=<int> kind=<id> planned= actual= "
                              "[exec_id=] [at_seq=] [entry_key=]"},
    }

    # ── entry / head aliases ───────────────────────────────────────────────────────
    @staticmethod
    def _wf_head(name: str) -> str:
        return f"workflow:{_uslug(name)}"

    @staticmethod
    def _entry_alias(name: str, branch: str, pos: int) -> str:
        return f"workflow:{_uslug(name)}:{_uslug(branch) or 'main'}:{int(pos)}"

    def _wf_meta(self, name: str) -> Dict[str, Any]:
        return self._meta(self._wf_head(name))

    def _cursors(self, name: str) -> Dict[str, int]:
        m = self._wf_meta(name)
        cur = m.get("cursors")
        return dict(cur) if isinstance(cur, dict) else {}

    def _set_cursor(self, name: str, branch: str, pos: int) -> None:
        cur = self._cursors(name)
        cur[branch] = int(pos)
        self._set_meta(self._key(self._wf_head(name)), "cursors", cur)

    def _require_wf(self, name: str) -> None:
        if not self._key(self._wf_head(name)):
            raise ValueError(f"bench '{name}' has no workflow — wf.new bench={name} first")

    def _entries(self, name: str, branch: str, include_retired: bool = False) -> List[Dict[str, Any]]:
        """The ACTIVE entries on a branch, ordered by pos (behind the cursor = log, ahead = script).
        A43.3 — an entry a shorter re-load RETIRED (status=retired) is kept in the store but excluded
        here (and from wf.advance), so a trimmed workflow no longer runs the dropped tail; a later,
        longer load re-activates it by replacing. Pass include_retired=True to see the full history."""
        rows = []
        pos = 1
        while True:
            alias = self._entry_alias(name, branch, pos)
            if not self._key(alias):
                break
            m = self._meta(alias)
            status = m.get("status") or "pending"
            if include_retired or status != "retired":
                rows.append({"pos": pos, "alias": alias, "body": m.get("body"),
                             "method": m.get("method"), "params": m.get("params") or {},
                             "results": m.get("results") or [], "status": status,
                             "replaced_wall": m.get("replaced_wall"), "branch": branch})
            pos += 1
        return rows

    # ── the grant gates are GONE (ruling §5) ──────────────────────────────────────────
    # `_caller_holds` / `_caller_is_participant` / `_caller_can_dispatch` walked the connected
    # societies for a `responsible:*` link on an agent the CALLER owned. Three things were wrong
    # with that, and the third is what broke the bench: (1) it is a permission table kept in the
    # graph, which the one gate cannot see and no eval can enumerate; (2) `responsible:` is one of
    # the names ruling §2 collapses into the assignment line; (3) provisioning now runs as `admin`,
    # so every cast belongs to admin and the ownership half refused the programme its own workflow.
    # `wf.write` / `wf.load` / `wf.advance` / `wf.dispatch` are gated at the dispatcher by their
    # declared action (`record` / `run`), and `_agents_note` below still reads the same links —
    # as PROVENANCE, which is all they ever were.

    def _agents_note(self, name: str, gid: str) -> List[str]:
        """The connected societies' agent aliases (provenance for an exec membrane)."""
        out: List[str] = []
        bench_key = self._key(self._bench_alias(name))
        for skey, sgid in self._society_connections(name, gid, bench_key):
            core = self._society_core(sgid)
            if core is None:
                continue
            for l in (core.get_adjacent_links(skey) or []):
                dst, rel = self._link_dst_rel(l)
                if rel and rel.startswith("responsible:"):
                    a = (core.get_aliases_by_key(dst) or [None])[0]
                    if a and a not in out:
                        out.append(a)
        return out

    # ── ops ──────────────────────────────────────────────────────────────────────────
    def op_new_wf(self, bench: str = "", cast: str = "") -> Dict[str, Any]:
        """[wf.new] Start the bench's workflow (1:1 — a second is refused). Records one observation."""
        name = bench
        gid = self._bench_gid(name); self._bind(gid)
        if not self._key(self._bench_alias(name)):
            raise ValueError(f"unknown bench '{name}' — bench.new it first")
        head = self._wf_head(name)
        if self._key(head):
            return {"status": "exists", "workflow": head, "bench": self._bench_alias(name)}
        self._mk(head, f"[{head}] workflow of {self._bench_alias(name)}",
                 {"concept": "workflow", "bench": self._bench_alias(name), "cursors": {"main": 0},
                  "author": self._client(), "created_wall": round(time.time(), 3)})
        self._observe(name, gid, "workflow", "new", {"cast": cast}, {"workflow": head})
        return {"status": "created", "workflow": head, "bench": self._bench_alias(name), "branch": "main"}

    def _write_entry(self, name: str, gid: str, branch: str, pos: int, entry: Any) -> Dict[str, Any]:
        """Write/replace one entry atom. `entry` is free text OR a {method, params} dict/JSON — a
        structured entry is executable by wf.advance as=job; free text is a human plan line."""
        body, method, params, kind = entry, None, {}, "text"
        if isinstance(entry, dict):
            method, params, body = entry.get("method"), entry.get("params") or {}, \
                entry.get("body") or entry.get("method") or json.dumps(entry, ensure_ascii=False)
            # A52 — a text-suspect line (method-shaped but a positional token) is stored as TEXT, flagged,
            # so it is visible in wf.ls and never silently swallowed as a plan line.
            kind = str(entry.get("kind") or ("structured" if method else "text"))
        else:
            s = str(entry or "").strip()
            if s.startswith("{"):
                try:
                    d = json.loads(s)
                    if isinstance(d, dict) and d.get("method"):
                        method, params, body = d["method"], d.get("params") or {}, s
                except Exception:
                    pass
        alias = self._entry_alias(name, branch, pos)
        # put_atom is CONTENT-ADDRESSED — two entries whose content string is identical collapse to one
        # atom (and the later meta clobbers the earlier). A structured entry's readable `body` can repeat
        # across positions (e.g. two `learning.dataset.bind` lines that differ only in pool=), so the stored
        # CONTENT is prefixed with the position-unique alias to keep each entry a DISTINCT atom.
        # A43 — REPLACE semantics: `_mk` is create-if-absent, so a changed `.ak` line was silently
        # ignored on every deploy that already held the branch (the bug A36 was meant to serve). Use
        # `_mk_replace`: identical body/method/params ⇒ no-op; a changed line ⇒ a NEW content-addressed
        # atom, the alias re-pointed, old→new linked `wf:superseded_by`, and the replaced step reset to a
        # fresh pending state (empty members/results/agents — a replaced step has not run yet).
        key, changed, old_key = self._mk_replace(
            alias, f"{alias}\n{body}",
            {"concept": "wf_entry", "bench": self._bench_alias(name), "branch": branch,
             "pos": int(pos), "body": body, "method": method, "params": params, "kind": kind,
             "members": [], "results": [], "agents": [], "status": "pending",
             "author": self._client(), "created_wall": round(time.time(), 3)},
            compare_meta=("body", "method", "params"))
        change = "created" if (changed and old_key is None) else \
                 ("replaced" if changed else "unchanged")
        if old_key:
            self._link(alias, old_key, "wf:superseded_by")   # new → old (history reachable for rollback)
        # the scope set gains the new key and KEEPS the old (history stays in scope)
        self._add_to_set(self._scope_set(name), key)
        # G4 §1.3/§1.7 — the plan entry is a MEMBER of its BRANCH coordinate
        # cronon:wf:<bench>:<branch>:p<pos> (the ONLY membership a branch coordinate has: the plan and
        # its revisions — never a record). The branch clock is `wf:<bench>:<branch>`.
        _wf_clock = "wf:%s:%s" % (_uslug(name), branch)
        _prev = getattr(self, "_space", ""); self._space = ""    # coordinates are UNIVERSAL (nucleus)
        try:
            self._cronon_locate(_wf_clock, int(pos), key, prefix="p")
            if old_key:                                      # a revision joins the same plan coordinate
                self._add_to_set("cronon:%s:p%d" % (_wf_clock, int(pos)), old_key)
        finally:
            self._space = _prev
        # A43.3 — a re-load of a position that a shorter file had RETIRED re-activates it: an unchanged
        # atom still carrying status=retired is flipped back to pending (within the loaded range).
        if not changed and (self._meta(alias) or {}).get("status") == "retired":
            self._set_meta(key, "status", "pending")
            change = "reactivated"
        return {"entry": alias, "pos": int(pos), "branch": branch, "method": method,
                "change": change, "key": key, "old_key": old_key}

    def op_write(self, bench: str = "", pos: Any = 0, entry: Any = "", branch: str = "main",
                 cast: str = "") -> Dict[str, Any]:
        """[wf.write] Write one entry at pos (1-based) on a branch. Ahead of the cursor = plan; a
        rewrite is content-addressed (idempotent for the same body)."""
        name = bench
        gid = self._bench_gid(name); self._bind(gid)
        self._require_wf(name)
        try:
            p = int(pos)
        except (TypeError, ValueError):
            raise ValueError("wf.write requires an integer pos=")
        if p < 1:
            raise ValueError("wf.write pos is 1-based")
        if not str(entry).strip() and not isinstance(entry, dict):
            raise ValueError("wf.write requires entry=")
        branch = _uslug(branch) or "main"
        res = self._write_entry(name, gid, branch, p, entry)
        if res.get("change") in ("replaced", "reactivated"):
            logger.info("[wf] write bench=%s branch=%s pos=%d %s method=%s",
                        self._bench_alias(name), branch, p, res["change"], res.get("method"))
        self._observe(name, gid, "workflow", "write",
                      {"pos": p, "branch": branch, "cast": cast}, res)
        return {"status": "written", **res}

    def op_load(self, bench: str = "", name: str = "", file: str = "", branch: str = "main",
                cast: str = "", params: str = "") -> Dict[str, Any]:
        """[wf.load] Load entries from an .ak file — each non-comment line is one entry. A line that
        is `method key=value …` becomes a structured {method, params} entry (executable by as=job); a
        line that is not a known command shape is stored as a free-text plan line. Idempotent by
        content (re-loading the same file rewrites the same positions).

        `params=` substitutes the file's `$placeholders`, over the defaults its `#!params` header
        declares — `k=v,k=v` or a JSON object (JSON when a value may contain a comma or a space).
        Without it a template's `$program` was written to the bench LITERALLY, which is why a
        template had to be pre-substituted into a second committed file before it could be loaded
        onto `main`; that second file is a copy of the first and copies drift. `safe_substitute`
        leaves an unknown `$name` intact, so a file with no header and no params loads byte-for-byte
        as it always did."""
        b = bench
        gid = self._bench_gid(b); self._bind(gid)
        self._require_wf(b)
        if not file:
            raise ValueError("wf.load requires file=")
        try:
            with open(file, "r", encoding="utf-8") as fh:
                lines = fh.read().splitlines()
        except OSError as exc:
            raise ValueError(f"wf.load cannot read {file}: {exc}")
        branch = _uslug(branch) or "main"
        # `#!params` defaults, overlaid with the caller's — the same precedence the template branch
        # path uses, so one template reads identically whichever way it is put on a bench.
        sub: Dict[str, str] = {}
        for ln in lines:
            if ln.strip().startswith("#!params"):
                sub.update(self._parse_params(ln.strip()[len("#!params"):]))
        if params:
            p = str(params).strip()
            if p.startswith("{"):
                try:
                    sub.update({str(k): str(v) for k, v in (json.loads(p) or {}).items()})
                except ValueError as exc:
                    raise ValueError(f"wf.load params= is not valid JSON: {exc}")
            else:
                sub.update(self._parse_params(p))
        pos, written = 1, []
        for ln in lines:
            s = ln.strip()
            if not s or s.startswith("#"):
                continue
            if sub:
                s = string.Template(s).safe_substitute(sub)
            entry = self._parse_ak_line(s)
            if isinstance(entry, dict):
                entry.setdefault("body", s)   # keep the readable source line as the display body
                if entry.get("kind") == "text_suspect":
                    # A52 — a line that LOOKS like a command but has a positional token would never run.
                    logger.warning("[wf] load bench=%s branch=%s pos=%d parsed as TEXT (positional token "
                                   "'%s' after method '%s') — use key=value",
                                   self._bench_alias(b), branch, pos, entry.get("bad_token"),
                                   entry.get("method_hint"))
            res = self._write_entry(b, gid, branch, pos, entry)
            written.append(res)
            # A43.4 — one INFO per changed position so a reload is legible in the log.
            if res.get("change") in ("replaced", "reactivated"):
                logger.info("[wf] reload bench=%s branch=%s pos=%d %s method=%s",
                            self._bench_alias(b), branch, pos, res["change"], res.get("method"))
            pos += 1
        count = len(written)
        replaced = sum(1 for w in written if w.get("change") in ("replaced", "reactivated"))
        # A43.3 — a SHORTER file retires the trailing positions this load did not write (kept + linked,
        # excluded from _entries/wf.advance). A later longer load re-activates them by replacing.
        retired = []
        p = count + 1
        while True:
            alias = self._entry_alias(b, branch, p)
            k = self._key(alias)
            if not k:
                break
            if (self._meta(alias) or {}).get("status") != "retired":
                self._set_meta(k, "status", "retired")
                self._set_meta(k, "retired_wall", round(time.time(), 3))
                self._link(alias, self._wf_head(b), "wf:retired_by")
                logger.info("[wf] reload bench=%s branch=%s pos=%d retired", self._bench_alias(b), branch, p)
            retired.append(p)
            p += 1
        # A43.3 — clamp the branch cursor if it is beyond the new active count.
        cur = int(self._cursors(b).get(branch, 0))
        if cur > count:
            self._set_cursor(b, branch, count)
        self._observe(b, gid, "workflow", "load",
                      {"file": file, "branch": branch, "cast": cast},
                      {"count": count, "replaced": replaced, "retired": len(retired)})
        logger.info("[wf] reload bench=%s branch=%s file=%s entries=%d replaced=%d retired=%d",
                    self._bench_alias(b), branch, file, count, replaced, len(retired))
        return {"status": "loaded", "bench": self._bench_alias(b), "branch": branch,
                "count": count, "replaced": replaced, "retired": len(retired), "entries": written}

    @staticmethod
    def _parse_ak_line(s: str) -> Any:
        """`method key=value key="v v" …` → {method, params}; a genuine plan line → the raw str.
        A52: a line whose first token IS a `namespace.method` shape but that carries a POSITIONAL
        (non key=value) token — e.g. `macro.run observe.diff …` — is a TEXT-SUSPECT: it looks like a
        command but will not run as one. It is returned as {kind:'text_suspect', body, bad_token,
        method_hint} so wf.load can warn and mark it, instead of silently becoming an unrunnable plan line."""
        import shlex
        try:
            toks = shlex.split(s)
        except ValueError:
            return s
        if not toks:
            return s
        first = toks[0]
        if "=" in first or "." not in first:
            return s   # `key=value …` or no namespace.method shape → a genuine plan line
        method = first
        params: Dict[str, Any] = {}
        for t in toks[1:]:
            if "=" in t and not t.startswith("="):
                k, v = t.split("=", 1)
                params[k] = v
            else:
                # method-shaped but a positional token → not a clean command (A52): flag it, keep as text
                return {"kind": "text_suspect", "body": s, "bad_token": t, "method_hint": method}
        return {"method": method, "params": params}

    def op_cursor(self, bench: str = "", branch: str = "") -> Dict[str, Any]:
        name = bench
        gid = self._bench_gid(name); self._bind(gid)
        self._require_wf(name)
        cur = self._cursors(name)
        if branch:
            b = _uslug(branch) or "main"
            return {"bench": self._bench_alias(name), "branch": b, "cursor": int(cur.get(b, 0))}
        return {"bench": self._bench_alias(name), "cursors": cur}

    def op_advance(self, bench: str = "", n: Any = 1, branch: str = "main", **kw) -> Dict[str, Any]:
        """[wf.advance] Move the cursor forward over up to n entries. `as=inline` (default) annotates
        each advanced entry with a result and moves the cursor — for a plan line that IS the execution.
        `as=job` submits the structured entries ahead of the cursor as ONE background JCL job
        (maintenance / LOW / fail_fast=False): each step re-dispatches its method, which for a bench op
        passes `_perform` (grant + observation); free-text entries are annotated, not run."""
        as_ = str(kw.get("as") or kw.get("as_") or "inline").lower()
        mode = str(kw.get("mode") or "execution").lower()
        cast = kw.get("cast", "")
        by = kw.get("by", "agent")          # E2-1 (F4) — who advanced (the driver passes by=driver)
        name = bench
        gid = self._bench_gid(name); self._bind(gid)
        self._require_wf(name)
        branch = _uslug(branch) or "main"
        try:
            count = max(1, int(n))
        except (TypeError, ValueError):
            count = 1
        entries = self._entries(name, branch)
        cur = int(self._cursors(name).get(branch, 0))
        ahead = [e for e in entries if e["pos"] > cur][:count]
        if not ahead:
            return {"status": "at_end", "bench": self._bench_alias(name), "branch": branch,
                    "cursor": cur, "advanced": 0}
        # G4 §1.5b — mode=thought: WALK the plan from the cursor WITHOUT dispatching any operator. Each
        # step visited is one thought bench record ({method, params_digest, pos} "considered",
        # cronon:rehearses the entry KEY); NOTHING reaches _perform's operators. The cursor moves as in a
        # real advance. This is how a seminar reads a plan aloud, or an agent checks it before `decide`.
        if mode == "thought":
            walked = []
            for e in ahead:
                self._observe(name, gid, "workflow", "advance",
                              {"pos": e["pos"], "branch": branch, "mode": "thought",
                               "plan_entry_key": self._key(e["alias"]), "cast": cast, "by": by},
                              {"entry": e["alias"], "considered": e.get("method") or "text"})
                logger.info("[wf] thought bench=%s branch=%s act=advance pos=%s → wb:considered",
                            self._bench_alias(name), branch, e["pos"])
                walked.append(e["pos"])
            self._set_cursor(name, branch, ahead[-1]["pos"])
            return {"status": "rehearsed", "bench": self._bench_alias(name), "branch": branch,
                    "cursor": ahead[-1]["pos"], "advanced": walked, "as": "thought", "mode": "thought"}
        if as_ == "job":
            return self._advance_as_job(name, gid, branch, cur, ahead,
                                        timeout_s=kw.get("timeout_s"), cast=cast,
                                        driver=kw.get("driver"), run=kw.get("run"))
        # inline: annotate + move the cursor, one entry at a time (a plan line that IS the execution).
        # S2-i — through the ONE shared recorder, so inline and as=job leave an identical trace.
        advanced = []
        for e in ahead:
            self._record_execution(name, gid, branch, e["pos"], e["alias"], self._key(e["alias"]),
                                   status="ok", result={"status": "noted"}, mode="execution",
                                   cast=cast, driver=kw.get("driver"), run=kw.get("run"), by=by)
            advanced.append(e["pos"])
        self._set_cursor(name, branch, ahead[-1]["pos"])
        return {"status": "advanced", "bench": self._bench_alias(name), "branch": branch,
                "cursor": ahead[-1]["pos"], "advanced": advanced, "as": "inline"}

    def _advance_as_job(self, name: str, gid: str, branch: str, cur: int,
                        ahead: List[Dict[str, Any]], timeout_s: Any = None,
                        cast: str = "", driver: str = None, run: str = None) -> Dict[str, Any]:
        """Submit the structured entries ahead of the cursor as one JCL job through the SECURED
        job.submit path. Free-text entries are annotated inline (not runnable). The cursor advances to
        the end of the dispatched run (the job carries the results into each entry's log as it runs)."""
        # R2 — the branch is BLOCK CONTEXT: an op advanced under branch `plants_t3` belongs to it
        # even when its `.ak` line omits `branch=`. Stamp the advancing branch onto a step that lacks
        # one, so its run atom / observations carry the coordinate; an explicit `branch=` in the line
        # still wins (override). WHICH ops take the block's branch is what each op DECLARES about
        # itself — `"block_branch": true` on its manifest entry (group 4, 4.12(c)) — never a list of
        # method names here: the steps are dispatched as written, and a kind's behaviour is its own.
        from lib.akasha import api as _api_attrs
        steps = []
        step_entries = []                      # S2-i — parallel to `steps`: (pos, alias, key) per step
        for e in ahead:
            if e.get("method"):
                _params = dict(e.get("params") or {})
                if _api_attrs.op_attr(_ACTIVE_KERNEL, e["method"], "block_branch") \
                        and not (_params.get("branch") or "").strip() \
                        and branch and branch != "main":
                    _params["branch"] = branch
                steps.append({"method": e["method"], "params": _params,
                              "cmd": f"wf:{name}:{branch}:{e['pos']}"})
                step_entries.append((e["pos"], e["alias"], self._key(e["alias"])))
            else:
                self._annotate(name, branch, e["pos"], {"status": "noted", "at": round(time.time(), 3)})
        self._observe(name, gid, "workflow", "advance",
                      {"branch": branch, "as": "job", "cast": cast, "driver": driver, "run": run},
                      {"steps": len(steps)})
        # A52 — with ZERO structured steps (every advanced entry is free text / text-suspect) there is no
        # job to submit: return `text_only`, never `dispatched` (a `dispatched` with no job_id made the
        # driver report a phantom "no job id"). The cursor still advances past the annotated text entries.
        if not steps:
            self._set_cursor(name, branch, ahead[-1]["pos"])
            _suspect = [e["pos"] for e in ahead if (self._meta(e["alias"]) or {}).get("kind") == "text_suspect"]
            if _suspect:
                logger.warning("[wf] advance bench=%s branch=%s: %d text-suspect entr%s not run "
                               "(positional token — use key=value) pos=%s", self._bench_alias(name),
                               branch, len(_suspect), "y" if len(_suspect) == 1 else "ies", _suspect)
            return {"status": "text_only", "bench": self._bench_alias(name), "branch": branch,
                    "cursor": ahead[-1]["pos"], "as": "job", "job_id": None, "steps": 0,
                    "text_suspect": _suspect, "advanced": [e["pos"] for e in ahead]}
        job_id = None
        if steps and _ACTIVE_KERNEL is not None:
            try:
                t = float(timeout_s) if timeout_s is not None else None
            except (TypeError, ValueError):
                t = None
            _data = {"steps": steps, "fail_fast": False,
                     "label": f"wf.advance {name}:{branch}",
                     "timeout_s": t, "job_class": "maintenance"}
            # B10-a §3 — DERIVE the reservation's accounting key + appetite from the WORKLOAD this
            # (bench, branch) belongs to, so a scheduled airing reserves against the pool. Keyed on
            # the pair and not on the group: four workloads share `wb:studio_ai`, and a group-keyed
            # lookup would hand all four the first one's appetite. The key is derived, not
            # submitter-chosen (which would make carry-over credits / allotments spoofable);
            # `declared=true` marks it as the trusted source.
            try:
                _appetite = (getattr(getattr(_ACTIVE_KERNEL, "api", None), "hooks", None) or {}).get("workload_appetite")
                if _ACTIVE_KERNEL is not None and _appetite is not None:   # the workbench's hook (manifest)
                    _prog, _cpr = _appetite(_ACTIVE_KERNEL, name, branch)
                    # Carried even when the appetite is ZERO: admission then knows a scheduled run
                    # arrived and asked for nothing, and says so (`outcome=unmetered`). Without the
                    # zero case, a run whose appetite was lost on the way reaches admission looking
                    # exactly like an ordinary batch job — indistinguishable, in the log, from a run
                    # that never happened. An appetite of 0 still reserves nothing.
                    _data["program"] = _prog or f"{gid}/{name}"
                    _data["llm_calls_per_run"] = int(_cpr or 0)
                    _data["llm_declared"] = bool(_prog)
            except Exception:
                pass
            payload = {"jsonrpc": "2.0", "method": "job.submit", "id": "wf.advance",
                       "params": {"session_token": self._client(), "data": _data}}
            try:
                r = _ACTIVE_KERNEL.dispatch(payload, "internal")
                if isinstance(r, dict) and r.get("error"):
                    # D11 — A REFUSED SUBMIT IS AN ANSWER, NOT A LOG LINE. It used to be logged
                    # and dropped: the cursor then moved as if the steps had run, the caller got
                    # `dispatched` with no job, and the driver burned its breaker on a run that
                    # never started and could not have. Three programmes went dark until their
                    # next daily window because the pool was full for one afternoon.
                    #
                    # Returned at once, the cursor untouched (those steps did NOT run), with the
                    # reason as the error's own id (`data.reason`) — never parsed from a message.
                    _e = r["error"]
                    _ed = _e.get("data") if isinstance(_e.get("data"), dict) else {}
                    logger.warning("[wf] as=job refused for %s: %s %s reason=%s", name,
                                   _e.get("code"), _e.get("message"), _ed.get("reason") or "-")
                    return {"status": "refused", "bench": self._bench_alias(name),
                            "branch": branch, "as": "job", "job_id": None,
                            "reason": str(_ed.get("reason") or ""), "code": _e.get("code"),
                            "message": _e.get("message"),
                            "retry_at": _ed.get("retry_at"),
                            "cursor": self._cursors(name).get(branch, 0)}
                job_id = (r.get("result") or {}).get("job_id") if isinstance(r, dict) else None
            except Exception as exc:
                logger.warning("[wf] as=job submission failed for %s: %s", name, exc)
        if steps and _ACTIVE_KERNEL is not None and not job_id:
            # No job, no refusal answer either (the dispatch raised). The steps did not run, so
            # the cursor does not move — the same rule as a refusal, for the same reason.
            return {"status": "refused", "bench": self._bench_alias(name), "branch": branch,
                    "as": "job", "job_id": None, "reason": "", "code": None,
                    "message": "job.submit returned no job", "cursor": self._cursors(name).get(branch, 0)}
        self._set_cursor(name, branch, ahead[-1]["pos"])
        # S2-i — await the job to a terminal state and record the EXECUTION TRACE through the SAME
        # recorder the inline path uses (per-step entry annotation + cronon:executes coordinate), then
        # stamp the sweep condition from the terminal state. This makes a manual `wf.advance as=job` and
        # a driver run leave an identical trace. The await is a poll cap (returns the instant the job is
        # terminal), not a new job soft-timeout; on a wedge past the cap we skip recording (best-effort).
        job_status, minted, ok = self._await_and_record(
            name, gid, branch, job_id, step_entries, cast=cast, driver=driver, run=run,
            cap_s=(t if t else _JOB_AWAIT_CAP_S))
        return {"status": "dispatched", "bench": self._bench_alias(name), "branch": branch,
                "cursor": ahead[-1]["pos"], "as": "job", "job_id": job_id,
                "steps": len(steps), "advanced": [e["pos"] for e in ahead],
                "job_status": job_status, "minted": minted}

    @staticmethod
    def _failed_step_indices(job) -> set:
        """Parse a completed job's `step_errors` (each 'Step N [method]: msg', N 1-based over the job's
        steps) into the 0-based indices that FAILED. With fail_fast=False every step runs, so this maps
        cleanly onto the parallel step_entries; a job that raised (fail_fast) reports one error and the
        remaining steps never ran (treated as not-executed, not recorded as ok)."""
        out = set()
        for err in (getattr(job, "step_errors", None) or []):
            s = str(err)
            if s.startswith("Step "):
                num = s[len("Step "):].split(" ", 1)[0].strip()
                try:
                    out.add(int(num) - 1)
                except ValueError:
                    pass
        return out

    def _await_and_record(self, name: str, gid: str, branch: str, job_id: Optional[str],
                          step_entries: List[Tuple[int, str, str]], cast: str = "",
                          driver: str = None, run: str = None,
                          cap_s: float = _JOB_AWAIT_CAP_S) -> Tuple[str, int, bool]:
        """S2-i — poll the submitted job to DONE/FAILED (bounded by cap_s) and, for every structured step
        that RAN, call the shared execution recorder (entry status + cronon:executes coordinate). Marks
        the sweep condition from the terminal state (no-op for a static branch). Returns
        (job_status, minted_count, ok). Best-effort: a missing kernel/job, or a wedge past the cap,
        records nothing (the trace is simply absent, never wrong)."""
        if not job_id or _ACTIVE_KERNEL is None or not getattr(_ACTIVE_KERNEL, "jcl_worker", None):
            return ("unknown", 0, False)
        worker = _ACTIVE_KERNEL.jcl_worker
        deadline = time.time() + max(1.0, float(cap_s))
        job = None
        while time.time() < deadline:
            job = worker.get_job(job_id)
            if job is not None and getattr(job, "status", "") in ("DONE", "FAILED", "CANCELLED"):
                break
            time.sleep(0.1)
        if job is None or getattr(job, "status", "") not in ("DONE", "FAILED", "CANCELLED"):
            logger.warning("[wf] as=job %s did not settle within %.0fs — execution trace not recorded",
                           job_id, cap_s)
            return (getattr(job, "status", "running") if job else "unknown", 0, False)
        status = getattr(job, "status", "")
        step_done = int(getattr(job, "step_done", 0) or 0)
        # a 0-based index → its error message, parsed from `Step N [method]: msg` (B1 — the deviation's
        # `actual` carries the step's error text, not just the fact of failure).
        errmap = {}
        for err in (getattr(job, "step_errors", None) or []):
            s = str(err)
            if s.startswith("Step "):
                try:
                    errmap[int(s[len("Step "):].split(" ", 1)[0]) - 1] = s
                except ValueError:
                    pass
        failed = set(errmap)
        minted = 0
        for i, (pos, alias, key) in enumerate(step_entries):
            if i >= step_done and status != "DONE":
                # fail_fast job aborted before this step ran — it did NOT execute, so no coordinate.
                continue
            st = "failed" if i in failed else "ok"
            self._record_execution(name, gid, branch, pos, alias, key, status=st,
                                   result={"job": job_id, "error": errmap.get(i)}, mode="execution",
                                   cast=cast, driver=driver, run=run, by="driver" if driver else "agent")
            minted += 1
        ok = status == "DONE" and not getattr(job, "step_errors", None)
        # at job end — stamp the sweep condition from the terminal state (pending→done|failed). A no-op
        # for a static (non-sweep) branch; idempotent with the driver's own S2-a mark.
        #
        # THE RECORDER WRITES THE BOOKKEEPING; THE CLIENT IS NAMED ON IT (D2). This dispatched as
        # `self._client()` — the workload's own client, because that is who happened to be running —
        # and a programme client has no scope over the bench it airs on, so EVERY run of EVERY
        # programme ended with `[gate] refused … action=record target=wb:studio_ai
        # reason=out_of_scope`. The refusal was harmless (the mark is best-effort) and that is
        # exactly what made it bad: a real refusal, logged at every run, that meant nothing — the
        # kind of line that teaches a reader to stop reading refusals.
        #
        # Stamping a condition's terminal status is the RECORDER's own bookkeeping, not an act of
        # the workload. `system.librarian` is the cell's internal recorder (its line is in
        # `config/identity/assign.ak`), so the write is made under the line that may make it, and
        # `by=` carries WHO the run belonged to. Provenance is a field, never a borrowed authority.
        try:
            _bare = name[3:] if str(name).startswith("wb:") else name
            _ACTIVE_KERNEL.dispatch({"jsonrpc": "2.0", "method": "sweep.mark", "id": "wf.mark",
                                     "params": {"session_token": _RECORDER,
                                                "data": {"bench": _bare, "branch": branch,
                                                         "status": "done" if ok else "failed",
                                                         "by": self._client()}}},
                                    "internal")
        except Exception:
            pass
        # E2-2/F5 — for a MANUAL run (no driver) emit the per-run cronon line here; a DRIVER run gets its
        # authoritative [cronon] line from the bench.auto loop (which reads the same coordinates), so
        # gating on driver avoids a duplicate line.
        if driver is None:
            _pos = [str(p) for (p, _a, _k) in step_entries]
            logger.info("[cronon] %s minted=%d branch=%s executes=%s", self._bench_alias(name),
                        minted, branch, ",".join(_pos) or "-")
        return (status, minted, ok)

    def _annotate(self, name: str, branch: str, pos: int, result: Dict[str, Any],
                  status: str = "done") -> None:
        alias = self._entry_alias(name, branch, pos)
        key = self._key(alias)
        if not key:
            return
        m = self._meta(alias)
        results = list(m.get("results") or [])
        results.append(result)
        self._set_meta(key, "results", results)
        # S2-i — the entry's terminal status reflects the step outcome (done | failed), so a failed
        # as=job step is not silently recorded as "done". Default "done" keeps every existing caller.
        self._set_meta(key, "status", status)

    def _record_execution(self, name: str, gid: str, branch: str, pos: int, entry_alias: str,
                          entry_key: str, status: str = "ok", result: Optional[Dict[str, Any]] = None,
                          mode: str = "execution", cast: str = "", driver: str = None,
                          run: str = None, by: str = "agent") -> None:
        """S2-i — the ONE execution recorder shared by BOTH the inline and the `as=job` advance paths, so
        a manual run and a driver run leave the SAME trace. It (1) annotates the entry with its terminal
        status + result summary and (2) tees ONE `workflow.advance` observation carrying `plan_entry_key`,
        which is what makes `_locate_observation` mint the bench EXECUTION coordinate + `cronon:executes`
        link back to the entry KEY (exactly as the inline path always did). A step that FAILED still ran
        the plan position, so it still mints the coordinate (the observation is marked failed)."""
        res = dict(result or {})
        res.setdefault("status", status)
        res.setdefault("at", round(time.time(), 3))
        self._annotate(name, branch, pos, res, status=("failed" if status == "failed" else "done"))
        obs_seq = self._observe(name, gid, "workflow", "advance",
                                {"pos": pos, "branch": branch, "driver": driver, "run": run,
                                 "mode": mode, "by": by, "plan_entry_key": entry_key, "cast": cast,
                                 "status": status},
                                {"entry": entry_alias, "status": status},
                                failed=(status == "failed"))
        # B1 §A3 — a step that ended in error / refusal diverged from plan: mint a `step_failed` deviation
        # at the execution coordinate this record just minted (the one recorder is the only writer).
        if status == "failed":
            em = self._meta(entry_alias) or {}
            planned = ({"method": em.get("method"), "params": em.get("params")}
                       if em.get("method") else (em.get("body") or entry_alias))
            self._mint_deviation(name, gid, branch, pos, "step_failed", planned,
                                 (res.get("error") or "step failed"),
                                 exec_id=(res.get("job") or ""), at_seq=obs_seq, entry_key=entry_key)

    def op_deviation(self, bench: str = "", branch: str = "main", pos: Any = 0, kind: str = "",
                     planned: Any = "", actual: Any = "", exec_id: str = "", at_seq: Any = None,
                     entry_key: str = "") -> Dict[str, Any]:
        """[wf.deviation] Record a deviation on a bench's workflow — the PUBLISHED door onto the
        single writer below (group 4, 4.16). An application model that needs to record one calls
        this op, or `mint_deviation` on a WorkflowConcept it holds; it never reaches a private
        member of this class."""
        if not bench or not kind:
            raise ValueError("wf.deviation requires bench= and kind=")
        gid = self._bench_gid(bench)
        self._bind(gid)
        try:
            _seq = int(at_seq) if at_seq not in (None, "") else None
        except (TypeError, ValueError):
            _seq = None
        key = self.mint_deviation(bench, gid, branch or "main", int(pos or 0), str(kind), planned,
                                  actual, exec_id=str(exec_id or ""), at_seq=_seq,
                                  entry_key=(entry_key or None))
        return {"status": "recorded" if key else "not_recorded", "key": key,
                "bench": self._bench_alias(bench), "branch": branch or "main", "kind": kind}

    def mint_deviation(self, name: str, gid: str, branch: str, pos: Any, kind: str,
                       planned: Any, actual: Any, exec_id: str = "", at_seq: Optional[int] = None,
                       entry_key: Optional[str] = None) -> Optional[str]:
        """PUBLIC (group 4, 4.16; `_mint_deviation` kept one seed).
        B1 §A3 — THE single writer of deviation atoms (a deviation is a FACT: `_mk`, never replace).
        Minted the moment `actual` diverges from `plan`; joined to the deviations / kind / branch Sets
        and linked `deviates_from` → the plan entry key and `observed_in` → the execution coordinate.
        Written UNIVERSAL (nucleus) so the Sets are guest-readable, like the coordinates it references.
        `exec8` = the first 8 chars of the execution id's last segment (job id, or the coordinate id)."""
        try:
            balias = self._bench_alias(name)
            slug_b = _uslug(balias[3:] if balias.startswith("wb:") else balias)
            branch_slug = _uslug(branch or "")
            exec8 = (str(exec_id or "").split(":")[-1])[:8] or "x"
            alias = "%s:deviation:%s:%d" % (balias, exec8, int(pos))
            coord_alias = ("cronon:%s:c%d" % (balias, int(at_seq))) if at_seq else None
            _seq = self._akasha_now()
            _prev = getattr(self, "_space", ""); self._space = ""     # universal — guest-readable
            try:
                meta = {"concept": "deviation", "bench": balias, "branch": branch or "",
                        "branch_slug": branch_slug, "pos": int(pos), "kind": kind,
                        "planned": planned, "actual": actual, "coordinate": coord_alias,
                        "at_seq": _seq, "cronon": _seq, "author": self._client()}
                key = self._mk(alias, "[%s] %s at p%d on %s" % (alias, kind, int(pos), branch or "-"), meta)
                self._add_to_set("set:wb:%s:deviations" % slug_b, key)
                self._add_to_set("set:wb:%s:deviation:kind:%s" % (slug_b, _uslug(kind)), key)
                if branch_slug:
                    self._add_to_set("set:wb:%s:deviation:branch:%s" % (slug_b, branch_slug), key)
                if entry_key:
                    self._link(alias, entry_key, "deviates_from")
                if coord_alias and self._key(coord_alias):
                    self._link(alias, coord_alias, "observed_in")
            finally:
                self._space = _prev
            logger.info("[deviation] bench=%s kind=%s branch=%s pos=%d coordinate=%s",
                        balias, kind, branch or "-", int(pos), coord_alias or "-")
            return key
        except Exception as exc:
            logger.debug("[deviation] mint skipped bench=%s kind=%s: %s", name, kind, exc)
            return None


    _mint_deviation = mint_deviation     # the old spelling, kept ONE seed (4.16)

    def op_rewind(self, bench: str = "", pos: Any = 0, branch: str = "main",
                  cast: str = "", by: str = "agent", reason: str = "") -> Dict[str, Any]:
        """[wf.rewind] Move the cursor back to pos (the entries between stay — a rewind is a new
        observation, it never erases the record of rewinding).

        E2-1 (F4) — `by` says WHO rewound. `by=agent` (default) is a genuine THOUGHT act on the plan
        (mode=thought, `cronon:rehearses`, joins the thought record). `by=driver` is the society
        driver's MECHANICAL reset-before-rerun (`_run_bench_workflow` rewinds to 0 then advances the
        whole branch): nobody thought it, so it is recorded under the EXECUTION coordinate
        (mode=execution, act=rewind reason=rerun), joins NO thought record, and logs at DEBUG — else the
        daily reruns fill the 'Thought experiments' view with resets.

        B1-a — `reason` distinguishes the DRIVER's two rewinds. The scheduled reset-to-0 before a rerun
        (`reason=rerun`, the run's precondition) is NOT a divergence from plan and mints NO deviation; an
        IN-RUN rewind — a retry after a failed step (`reason=retry`) or a rewind to a non-zero position —
        IS a divergence and mints a `rewound` deviation. Default reason for a driver rewind is `rerun`."""
        name = bench
        gid = self._bench_gid(name); self._bind(gid)
        self._require_wf(name)
        branch = _uslug(branch) or "main"
        try:
            p = int(pos)
        except (TypeError, ValueError):
            raise ValueError("wf.rewind requires an integer pos=")
        self._set_cursor(name, branch, max(0, p))
        _is_driver = str(by).lower() == "driver"
        _mode = "execution" if _is_driver else "thought"
        _reason = (str(reason).strip().lower() or "rerun") if _is_driver else None
        # G4 §1.5b — an AGENT rewind is a THOUGHT act (rehearses the entry at the target position);
        # a DRIVER rewind is part of the rerun's execution (mode=execution, reason=rerun).
        _ek = self._key(self._entry_alias(name, branch, max(1, p)))
        _rw_seq = self._observe(name, gid, "workflow", "rewind",
                                {"pos": p, "branch": branch, "mode": _mode, "plan_entry_key": _ek,
                                 "cast": cast, "by": by, "reason": _reason},
                                {"cursor": max(0, p)})
        # B1-a §A3 — a DRIVER rewind mints a `rewound` deviation ONLY when it is an IN-RUN divergence:
        # a retry after a failed step (`reason=retry`) or a rewind to a non-zero position. The scheduled
        # `reason=rerun` reset to 0 is the run's mechanical precondition, not a divergence, and mints
        # nothing (else the daily reruns add eight `rewound` atoms a day). An agent rewind is a THOUGHT
        # act (mode=thought) and never mints here.
        if _is_driver and (_reason == "retry" or p != 0):
            self._mint_deviation(name, gid, branch, max(1, p), "rewound",
                                 {"cursor": p}, {"reason": _reason, "reset_to": max(0, p)},
                                 exec_id=(str(_rw_seq or "")), at_seq=_rw_seq, entry_key=_ek)
        if _is_driver:
            logger.debug("[wf] rerun bench=%s branch=%s from=%s by=driver",
                         self._bench_alias(name), branch, p)
        else:
            logger.info("[wf] thought bench=%s branch=%s act=rewind pos=%s → wb:considered",
                        self._bench_alias(name), branch, p)
        return {"status": "rewound", "bench": self._bench_alias(name), "branch": branch,
                "cursor": max(0, p), "by": by, "mode": _mode}

    # ── P0-a — parameterized sweep templates ────────────────────────────────────────
    @staticmethod
    def _sweep_marker(name: str, branch: str) -> str:
        return "wf:sweep:%s:%s" % (_uslug(name), _uslug(branch))

    @staticmethod
    def _parse_params(params: str) -> Dict[str, str]:
        """`k=v,k=v` (comma- or whitespace-separated) → {k: v}. A bare token without '=' is ignored."""
        out: Dict[str, str] = {}
        for chunk in str(params or "").replace("\n", ",").split(","):
            for tok in chunk.split():
                if "=" in tok:
                    k, v = tok.split("=", 1)
                    if k.strip():
                        out[k.strip()] = v.strip()
        return out

    def _template_path(self, name: str, template: str) -> str:
        """Resolve a sweep template. `template` may be a path ending in .ak (used as-is) or a bare name
        resolved against config/workbench/<bench>/templates/<name>.ak — trying the bench name and its slug/hyphen
        variants so `plants-vision` and `plants_vision` both find `config/workbench/plants-vision/templates/`."""
        t = str(template or "").strip()
        if t.endswith(".ak"):
            if os.path.isfile(t):
                return t
            raise ValueError(f"wf.branch template file not found: {t}")
        # repo root = .../ (workflow.py is lib/akasha/concepts/workflow.py → 4 dirnames up)
        from lib.akasha.api import reserved as _reserved
        base = getattr(self, "_config_root", None) or os.path.dirname(os.path.dirname(
            _reserved.root("templates", "_")))
        stem = _uslug(t)
        cands = []
        for dirname in (name, _uslug(name), _uslug(name).replace("_", "-")):
            cands.append(os.path.join(base, dirname, "templates", f"{stem}.ak"))
            cands.append(os.path.join(base, dirname, "templates", f"{t}.ak"))
        for c in cands:
            if os.path.isfile(c):
                return c
        raise ValueError(f"wf.branch template '{template}' not found under config/workbench/<bench>/templates/ "
                         f"(tried: {', '.join(sorted(set(cands)))})")

    def _load_template(self, name: str, template: str) -> Tuple[List[str], Dict[str, str]]:
        """Read a template .ak → (body_lines, declared_defaults). A leading `#!params k=v k=v` header
        declares parameter names + defaults; every other non-comment line is a body line (with `$param`
        placeholders left intact for substitution at branch time)."""
        path = self._template_path(name, template)
        with open(path, "r", encoding="utf-8") as fh:
            raw = fh.read().splitlines()
        defaults: Dict[str, str] = {}
        body: List[str] = []
        for ln in raw:
            s = ln.strip()
            if not s:
                continue
            if s.startswith("#!params"):
                defaults.update(self._parse_params(s[len("#!params"):]))
                continue
            if s.startswith("#"):
                continue
            body.append(s)
        return body, defaults

    def op_branch(self, bench: str = "", **kw) -> Dict[str, Any]:
        """[wf.branch] Fork a new branch. Two forms:

        • POSITION fork (default): `from=<int> name=<branch>` copies entries 1..from of `main` into a
          NEW named branch (chains share the prefix; content addressing makes the copy free).
        • TEMPLATE sweep (P0-a): `from=<template> params=k=v,k=v [parent=main] [at=<pos>]`. The branch
          name is DERIVED — `<parent>@p<fork_pos>/<template>@<cond8>` (slugged) — where `cond8` is a
          sha256 over the sorted effective `k=v` bindings (declared defaults overlaid with params). It
          copies the parent prefix 1..fork_pos, then loads the template's body with `$param`
          substitution as the swept tail (wf.load / A43 `_mk_replace` semantics), joins the faceting
          Sets `set:wb:<b>:cond:<k>:<v>` (+ `set:wb:<b>:branches`) via a `wf:sweep:<b>:<branch>` marker,
          and is IDEMPOTENT: re-running with the same params re-points nothing and returns already=true.
        No canonical branch."""
        frm = kw.get("from") or kw.get("from_") or 0
        new = kw.get("name") or ""
        cast = kw.get("cast", "")
        by = kw.get("by", "agent")          # E2-1 (F4) — who forked (recorded on the observation)
        name = bench
        gid = self._bench_gid(name); self._bind(gid)
        self._require_wf(name)
        # TEMPLATE mode: `from=` is a non-integer token → a template name (params= carries the bindings)
        _is_template = False
        try:
            int(frm)
        except (TypeError, ValueError):
            _is_template = bool(str(frm).strip())
        if _is_template:
            return self._branch_from_template(name, gid, str(frm).strip(), kw, cast, by)
        new = _uslug(new)
        if not new or new == "main":
            raise ValueError("wf.branch requires a name= (not 'main')")
        try:
            upto = int(frm)
        except (TypeError, ValueError):
            raise ValueError("wf.branch requires an integer from=")
        src = [e for e in self._entries(name, "main") if e["pos"] <= upto]
        for e in src:
            body = e["body"] if e.get("method") is None else \
                {"method": e["method"], "params": e.get("params") or {}, "body": e["body"]}
            self._write_entry(name, gid, new, e["pos"], body)
        cur = self._cursors(name)
        cur[new] = min(int(cur.get("main", 0)), upto)
        self._set_meta(self._key(self._wf_head(name)), "cursors", cur)
        # G4 §1.4/§1.5b — the fork link on the branch clocks (new p1 → parent p<from>), and a THOUGHT
        # bench record of the forking act itself (a fork is a plan act, not an execution).
        if upto >= 1:
            _pv = getattr(self, "_space", ""); self._space = ""
            try:
                self._link("cronon:wf:%s:%s:p1" % (_uslug(name), new),
                           "cronon:wf:%s:main:p%d" % (_uslug(name), upto), "cronon:forked_from")
            finally:
                self._space = _pv
        self._observe(name, gid, "workflow", "branch",
                      {"from": upto, "name": new, "mode": "thought", "by": by,
                       "plan_entry_key": self._key(self._entry_alias(name, "main", max(1, upto))),
                       "cast": cast}, {"branch": new, "copied": len(src)})
        logger.info("[wf] thought bench=%s branch=%s act=branch pos=%s → wb:considered",
                    self._bench_alias(name), new, upto)
        return {"status": "branched", "bench": self._bench_alias(name), "branch": new,
                "from": upto, "copied": len(src)}

    def _branch_from_template(self, name: str, gid: str, template: str, kw: Dict[str, Any],
                              cast: str, by: str) -> Dict[str, Any]:
        """P0-a — the TEMPLATE-mode body of wf.branch (a parameterized sweep branch). See op_branch."""
        body_lines, defaults = self._load_template(name, template)
        bindings = dict(defaults)
        bindings.update(self._parse_params(kw.get("params") or ""))
        # cond8 — a stable digest over the sorted effective bindings (defaults ⊕ params), so the SAME
        # sweep point always resolves to the SAME branch (idempotency + faceting key).
        canon = ",".join("%s=%s" % (k, bindings[k]) for k in sorted(bindings))
        cond8 = hashlib.sha256(canon.encode("utf-8")).hexdigest()[:8]
        tname = _uslug(os.path.splitext(os.path.basename(str(template)))[0]) or "tmpl"
        parent = _uslug(kw.get("parent") or "main") or "main"
        parent_entries = self._entries(name, parent)
        try:
            fork_pos = int(kw["at"]) if str(kw.get("at", "")).strip() else len(parent_entries)
        except (TypeError, ValueError):
            raise ValueError("wf.branch at= must be an integer position")
        fork_pos = max(0, min(fork_pos, len(parent_entries)))
        lineage = "%s@p%d/%s@%s" % (parent, fork_pos, tname, cond8)
        branch = _uslug(lineage)
        marker = self._sweep_marker(name, branch)
        # idempotent — the same sweep point already materialized (marker + entries) is a no-op
        if self._key(marker) and self._entries(name, branch):
            return {"status": "branched", "already": True, "bench": self._bench_alias(name),
                    "branch": branch, "lineage": lineage, "template": template, "cond8": cond8,
                    "bindings": bindings, "parent": parent, "fork_pos": fork_pos}
        # copy the parent prefix 1..fork_pos (shared, content-addressed)
        src = [e for e in parent_entries if e["pos"] <= fork_pos]
        for e in src:
            pbody = e["body"] if e.get("method") is None else \
                {"method": e["method"], "params": e.get("params") or {}, "body": e["body"]}
            self._write_entry(name, gid, branch, e["pos"], pbody)
        # load the substituted template body as the swept tail (wf.load / A43 semantics). The swept
        # bindings drive the hash; a few DERIVED names (cond8, branch, bench, bench_slug) are also
        # available to `$…` so a template can mint per-branch run/model/observer ids without colliding.
        sub = dict(bindings)
        sub.update({"cond8": cond8, "branch": branch, "bench": name, "bench_slug": _uslug(name)})
        pos, steps = fork_pos, 0
        for raw in body_lines:
            line = string.Template(raw).safe_substitute(sub)
            entry = self._parse_ak_line(line)
            if isinstance(entry, dict):
                entry.setdefault("body", line)
            pos += 1
            self._write_entry(name, gid, branch, pos, entry)
            steps += 1
        cur = self._cursors(name)
        cur[branch] = min(int(cur.get(parent, 0)), fork_pos)
        self._set_meta(self._key(self._wf_head(name)), "cursors", cur)
        # the sweep marker carries the coordinate (cond8 + bindings + lineage); it is the member of the
        # faceting Sets so a leaderboard can select "all branches where head=logreg" in pure set algebra.
        mk, _chg, _old = self._mk_replace(
            marker, "[%s] %s" % (marker, canon or "(no bindings)"),
            {"concept": "wf_sweep_branch", "bench": self._bench_alias(name), "branch": branch,
             "template": template, "cond8": cond8, "bindings": bindings, "parent": parent,
             "fork_pos": fork_pos, "lineage": lineage, "author": self._client()},
            compare_meta=("cond8", "template"))
        self._add_to_set("set:wb:%s:branches" % _uslug(name), mk)
        for k, v in bindings.items():
            self._add_to_set("set:wb:%s:cond:%s:%s" % (_uslug(name), _uslug(k), _uslug(str(v))), mk)
        # B1 §A3 — param_override: a MANUAL wf.branch that overrides a template DEFAULT the sweep's
        # condition did not bind. A materialise passes the condition's bindings AND sets `_sweep_bound`,
        # so its params ARE the sweep dimensions (never an override); only a hand branch mints this.
        if not kw.get("_sweep_bound"):
            _passed = self._parse_params(kw.get("params") or "")
            for _pk, _pv in _passed.items():
                if _pk in defaults and str(defaults.get(_pk)) != str(_pv):
                    self._mint_deviation(name, gid, lineage, fork_pos + 1, "param_override",
                                         {_pk: defaults.get(_pk)}, {_pk: _pv}, exec_id=cond8,
                                         entry_key=self._key(self._entry_alias(name, branch, fork_pos + 1)))
        # fork link on the branch clocks (new p1 → parent p<fork_pos>) — a fork is a plan act
        if fork_pos >= 1:
            _pv = getattr(self, "_space", ""); self._space = ""
            try:
                self._link("cronon:wf:%s:%s:p1" % (_uslug(name), branch),
                           "cronon:wf:%s:%s:p%d" % (_uslug(name), parent, fork_pos), "cronon:forked_from")
            finally:
                self._space = _pv
        self._observe(name, gid, "workflow", "branch",
                      {"from": fork_pos, "name": branch, "mode": "thought", "by": by,
                       "template": template, "cond8": cond8, "cast": cast},
                      {"branch": branch, "copied": len(src), "steps": steps, "cond8": cond8})
        logger.info("[wf] sweep bench=%s branch=%s template=%s cond8=%s copied=%d steps=%d bindings=%s",
                    self._bench_alias(name), branch, template, cond8, len(src), steps, canon)
        return {"status": "branched", "bench": self._bench_alias(name), "branch": branch,
                "lineage": lineage, "template": template, "cond8": cond8, "bindings": bindings,
                "parent": parent, "fork_pos": fork_pos, "copied": len(src), "steps": steps}

    def op_ls(self, bench: str = "", branch: str = "main", **kw) -> Dict[str, Any]:
        frm, to = kw.get("from") or kw.get("from_"), kw.get("to")
        name = bench
        gid = self._bench_gid(name); self._bind(gid)
        self._require_wf(name)
        branch = _uslug(branch) or "main"
        rows = self._entries(name, branch)
        try:
            lo = int(frm) if frm not in (None, "") else None
        except (TypeError, ValueError):
            lo = None
        try:
            hi = int(to) if to not in (None, "") else None
        except (TypeError, ValueError):
            hi = None
        if lo is not None:
            rows = [r for r in rows if r["pos"] >= lo]
        if hi is not None:
            rows = [r for r in rows if r["pos"] <= hi]
        cur = int(self._cursors(name).get(branch, 0))
        for r in rows:
            r["phase"] = "log" if r["pos"] <= cur else "script"
        return {"bench": self._bench_alias(name), "branch": branch, "cursor": cur,
                "entries": rows, "count": len(rows)}

    def op_dispatch(self, bench: str = "", branch: str = "main", **kw) -> Dict[str, Any]:
        """[wf.dispatch] The SYNC EVENT — mint an `exec:<bench>:<n>` membrane over entries from..to and
        record ONE world chronon on the shared axis (governed by `responsible:decide`). Copy-and-fix:
        the workflow original is untouched; a corrected dispatch makes a NEW exec record."""
        frm, to = kw.get("from") or kw.get("from_") or 1, kw.get("to") or 0
        cast = kw.get("cast", "")
        name = bench
        gid = self._bench_gid(name); self._bind(gid)
        self._require_wf(name)
        branch = _uslug(branch) or "main"
        try:
            lo, hi = int(frm), int(to) if to else 0
        except (TypeError, ValueError):
            raise ValueError("wf.dispatch requires integer from=/to=")
        run = [e for e in self._entries(name, branch) if e["pos"] >= lo and (hi == 0 or e["pos"] <= hi)]
        if not run:
            raise ValueError(f"no entries in {branch}[{lo}..{hi or 'end'}] to dispatch")
        member_keys = [self._key(e["alias"]) for e in run if self._key(e["alias"])]
        at_lo, at_hi = run[0]["pos"], run[-1]["pos"]
        n = len(self._members(f"exec:{_uslug(name)}:all")) + 1
        exec_alias = f"exec:{_uslug(name)}:{n}"
        agents = self._agents_note(name, gid)
        key = self._mk(exec_alias, f"[{exec_alias}] dispatch of {self._bench_alias(name)}:{branch}"
                       f"[{at_lo}..{at_hi}]",
                       {"concept": "exec", "bench": self._bench_alias(name), "workflow": self._wf_head(name),
                        "branch": branch, "from": at_lo, "to": at_hi, "members": member_keys,
                        "agents": agents, "n": n, "author": self._client(),
                        "dispatched_wall": round(time.time(), 3)})
        self._add_to_set(f"exec:{_uslug(name)}:all", key)
        for mk in member_keys:
            self._link(exec_alias, mk, "exec:covers")
        # ONE world chronon per dispatch (never per entry) — the shared sync record.
        world = self._bench_meta(name).get("world") or "default"
        sync = self._world().op_sync_record(exec_id=exec_alias, bench=self._bench_alias(name),
                                            branch=branch, from_pos=at_lo, to_pos=at_hi,
                                            agents=agents, world=world)
        obs_seq = self._observe(name, gid, "dispatch", "dispatch",
                                {"branch": branch, "from": at_lo, "to": at_hi, "cast": cast},
                                {"exec": exec_alias, "sync": sync.get("sync")})
        # G4 §1.6 — sync = a link world ↔ workbench ONLY. The world coordinate the dispatch minted is
        # joined `cronon:sync` to the bench coordinate its run produced (here, the dispatch record's
        # own bench coordinate). The exec membrane already `exec:covers` the plan range (provenance).
        if obs_seq and sync.get("cronon"):
            _wbcoord = "cronon:%s:c%d" % (self._bench_alias(name), int(obs_seq))
            _pv = getattr(self, "_space", ""); self._space = ""   # sync link is UNIVERSAL (nucleus)
            try:
                self._link(sync["cronon"], _wbcoord, "cronon:sync")
            finally:
                self._space = _pv
            logger.info("[cronon] sync %s ↔ %s via=dispatch", sync["cronon"], _wbcoord)
        return {"status": "dispatched", "exec": exec_alias, "bench": self._bench_alias(name),
                "branch": branch, "from": at_lo, "to": at_hi, "members": len(member_keys),
                "sync": sync.get("sync"), "cronon": sync.get("cronon"), "wall": sync.get("wall")}


class ExecReadConcept(UniversalConcept):
    """`exec.read` — read a dispatched execution membrane (the sync record's target). A separate,
    read-only surface so the exec namespace reads cleanly; the record itself is minted by wf.dispatch."""

    CONCEPT_PREFIX = "exec"
    CONCEPT_LABEL = "Execution record — a dispatched workflow run (read-only membrane)"

    CONCEPT_METHODS: Dict[str, Any] = {
        "read": {"op": "op_read", "action": "read",
                 "desc": "Read a dispatched execution: exec.read id=<exec:bench:n> [group=<gid>]"},
    }

    def op_read(self, id: str = "", group: str = "") -> Dict[str, Any]:
        """[exec.read] Read an exec membrane by id. A closed bench's exec lives in its group engine, so
        pass group= (or it is resolved from the caller's memberships)."""
        if not id:
            raise ValueError("exec.read requires id=")
        gids = [group] if group else list(getattr(self.session, "group_engines", {}) or {})
        for gid in gids + [""]:
            self._space = f"group:{gid}" if gid else ""
            key = self._key(id)
            if key:
                m = self._meta(id)
                return {"exec": id, "bench": m.get("bench"), "branch": m.get("branch"),
                        "from": m.get("from"), "to": m.get("to"), "agents": m.get("agents") or [],
                        "members": m.get("members") or [], "workflow": m.get("workflow"),
                        "dispatched_wall": m.get("dispatched_wall")}
        return {"status": "not_found", "id": id}
