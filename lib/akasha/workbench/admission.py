"""
job.* (submit_job — the one admission point, with the LLM reservation) and workflow.* — moved out of the kernel (backend layout order 2026-09-20).

Every function takes the kernel (the heart) as its first argument: it is the object the
dispatcher / timer registry hands in, never imported. Bodies are the kernel's own, moved
verbatim except `self.` → `kernel.` and intra-family calls.
"""
import os
import re
import sys
import time
import json
import uuid
import logging
from lib.akasha.api import gate as _gate
from lib.akasha.api import facts as _facts
import hashlib
import functools
from typing import Dict, Any, Optional, List, Callable
try:
    from lib.akasha.jcl import JCLWorker, JCLJob, JCLStep
    from lib.akasha.jcl.job import CLASS_BATCH_ATOM, CLASS_LINK, CLASS_MAINTENANCE
except ImportError:
    JCLWorker = None  # type: ignore
    JCLJob    = None  # type: ignore
    JCLStep   = None  # type: ignore
    CLASS_BATCH_ATOM = "batch_atom"  # type: ignore
    CLASS_LINK       = "link"        # type: ignore
    CLASS_MAINTENANCE = "maintenance"  # type: ignore
from lib.akasha.api.rpc import ok as _ok, err as _err
from lib.akasha.api.trust import TRUST_INTERNAL
from lib.akasha.jcl import workflow_vocab as _wf
from lib.akasha.workbench import llm

from lib.akasha.api.heart import _job_to_dict

logger = logging.getLogger("Akasha.Kernel")


# The outcomes a scheduled run can have at the one admission point. Vocabulary ids, compared and
# logged as themselves — never a sentence assembled at the call site.
ADMIT_RESERVED = "reserved"     # prepaid from today's pool; the job runs metered
ADMIT_REFUSED = "refused"       # the pool had no room; the job is NOT admitted
ADMIT_UNMETERED = "unmetered"   # a scheduled run arrived asking for nothing; nothing is reserved


def state_headroom(kernel, program: str, has_room: bool) -> None:
    """State this workload's headroom where the GATE reads it — `set:pool:headroom`.

    `api/facts.py` names admission as this Set's single writer and NOTHING CALLED IT, so the fact
    was never stated for any workload. The gate's step 4 for `run` is `target ∈ declared ∩ armed ∩
    source_ready ∩ headroom`; an unstated positive fact reads as "no", so the step could never pass
    and `workload.status` answered `headroom` for programmes that were on air (D4). The moment the
    answer can change is the moment it is stated: at reserve, at refusal, and at settle.

    Never raises: a fact that cannot be written is reported by `facts.state` and the admission it
    describes proceeds — the gate already treats an unwritable Set as "no"."""
    try:
        _facts.headroom(kernel, str(program or ""), bool(has_room))
    except Exception as exc:                      # noqa: BLE001 — reported, never blocks admission
        logger.warning("[llm] headroom fact not stated program=%s reason=%s: %s",
                       program, type(exc).__name__, exc)


def _admission_line(program: str, provider: str, calls: int, declared: bool,
                    outcome: str, free, cap=None) -> None:
    """ONE line per scheduled run, at the point that decided it.

    This is the ONLY reservation line. The pool used to log its own arithmetic as well
    (`[llm] reserved`), because a second caller reserved outside admission and that path had no
    other trace; that caller is gone with `station.py`, so the two lines said the same thing twice
    and the pool's is dropped. The cap it carried is folded in here as `cap=` — committed is
    `cap − free`, so nothing the pool line said is lost.

    The pool still logs a REFUSAL of its own (`[llm] pool refused`, throttled): that one is about
    the pool's state over a window, not about this run.

    The case only this line can report is a run that asked for nothing. A run whose appetite was
    lost between the declaration and here reaches admission looking exactly like an ordinary batch
    job, so the log of an airing that ran unmetered and the log of an airing that never happened
    are the same log. `outcome=unmetered` is the difference.

    `declared=` says whether the accounting key was DERIVED from the declaration (trusted) or fell
    back to the submitter's label — a false here means carry-over credits are accruing to a key
    nobody declared."""
    logger.info("[llm] admission %s program=%s provider=%s calls=%d declared=%s free=%s cap=%s",
                outcome, program, provider, calls, str(bool(declared)).lower(),
                ("-" if free is None else int(free)),
                ("∞" if not cap else int(cap)))


def handle_job_submit(kernel, rid, data, session, transport_trust=None) -> dict:
    """`job.submit` asks the gate, and `job.submit` is not an action.

    The ruling §3: *a `run` IS a job; whoever may `run` may submit the job that runs it and
    nothing else.* So there is one question here, `gate(owner, run, …)`, and the answer is the
    same one the driver gets when it asks whether that workload may run at all.

    THE `TRUST_INTERNAL`-ONLY PATH IS GONE. It was added this morning to unblock §1 — the driver
    had started running as the workload's declared client, that client was `role: user`, and
    submitting its own run was refused. It worked, and it was a second gate: a TRANSPORT
    answering a PERMISSION question. `api.trust` says whether a caller may be BELIEVED to be who
    it claims; it never says what that identity may do. The plan's rule is that a moved call site
    keeps no old check for safety, and a window in which the gate and a transport test can
    disagree is exactly the thing being removed.

    Nothing about the job's AUTHORITY moves: `owner` is still pinned to `session.client_id` (not
    accepted from the caller, so no identity can be borrowed), every step is still
    re-authenticated as that owner, and `validate_steps` still blocklists `job.*` / `sys.su` /
    `user.*` / `grp.*` / `auth.*` / `session.*` / destructive `onto.*`."""
    _owner = getattr(session, "client_id", "")
    # `_allowed`, never `_ok`: `_ok` is this module's JSON-RPC success helper, and shadowing it
    # here made every ADMITTED submit raise `'bool' object is not callable` at the return.
    _allowed, _why = _gate.gate(_owner, _gate.RUN)
    if not _allowed:
        _gate.refuse_log(_owner, _gate.RUN, "job.submit", _why)
        return _err(rid, -32003, "%s: job.submit" % _why)
    if not kernel.jcl_worker or not JCLJob or not JCLStep:
        return _err(rid, -32002, "JCL worker not available")
    steps_raw = data.get("steps", [])
    if not steps_raw:
        return _err(rid, -32602, "job.submit requires 'steps'")
    steps = [
        JCLStep(method=s["method"], params=s.get("params", {}), cmd=s.get("cmd", ""))
        for s in steps_raw if s.get("method")
    ]
    if not steps:
        return _err(rid, -32602, "No valid steps in job submission")
    # Defense-in-depth: reject privileged/recursive methods inside a batch
    # (job control, sys.su, user/group admin, auth, destructive onto ops).
    try:
        from lib.akasha.jcl.validator import validate_steps as _validate_steps
        _valid, _vmsg = _validate_steps(steps)
        if not _valid:
            return _err(rid, -32003, _vmsg)
    except ImportError:
        pass
    # Optional slice-3 scheduling declarations: PERT dependencies (this job waits
    # for the named job_ids), bounded retry, and a soft wall-clock budget. All
    # bounded at admission so a single job cannot wedge or hog the one worker.
    _JOB_MAX_RETRIES = 8       # mirrors worker._MAX_RETRIES_CEILING
    _JOB_MAX_TIMEOUT = 3600.0  # 1 h soft ceiling
    depends_on = data.get("depends_on") or []
    if isinstance(depends_on, str):
        depends_on = [depends_on]
    depends_on = [str(d) for d in depends_on]
    # Dependencies may only reference the submitter's OWN jobs (unless admin) — a
    # cross-owner dep would let one client couple its scheduling to another's job.
    # Who may couple their scheduling to ANOTHER owner's job is a permission, so it is the gate's
    # answer — not a scope string read out of the session here (ruling §5).
    if depends_on and not _gate.gate(_owner, _gate.ADMIN)[0]:
        for dep_id in depends_on:
            dep = kernel.jcl_worker.get_job(dep_id) if kernel.jcl_worker else None
            if dep is not None and dep.owner != session.client_id:
                return _err(rid, -32003,
                            "depends_on may only reference your own jobs.")
    try:
        max_retries = min(max(0, int(data.get("max_retries", 0))), _JOB_MAX_RETRIES)
    except (TypeError, ValueError):
        max_retries = 0
    timeout_s = data.get("timeout_s")
    try:
        timeout_s = float(timeout_s) if timeout_s is not None else None
        if timeout_s is not None:
            timeout_s = max(0.0, min(timeout_s, _JOB_MAX_TIMEOUT))
    except (TypeError, ValueError):
        timeout_s = None
    # B10 — reserve at admission (the single admission point) when the owner programme declares
    # LLM calls: prepay them from today's provider pool so a run that would cross the cap is refused
    # BEFORE it is queued (§1.2). Admitted → the job carries the reservation and runs prepaid.
    llm_reservation = None
    try:
        _cpr = int(data.get("llm_calls_per_run", 0) or 0)
    except (TypeError, ValueError):
        _cpr = 0
    _scheduled = ("llm_calls_per_run" in data) or bool(data.get("llm_declared"))
    if _cpr > 0:
        from lib.akasha.workbench import llm_pool
        from lib.akasha.workbench import llm_provider as _lprov
        _prov = (str(data.get("llm_provider") or "").strip().lower() or _lprov.active(kernel))
        # B10-a §3 — the key is DERIVED from the declaration (declared=true) by the wf.advance
        # path; a submitter-supplied program is a fallback only (declared=false), because a chosen
        # key would make carry-over credits / allotments spoofable.
        _declared = bool(data.get("llm_declared"))
        _program = str(data.get("program") or data.get("label") or session.client_id)
        _cap = llm_pool.caps(_prov)[0]
        llm_reservation = llm_pool.reserve(_prov, _program, _cpr)
        if llm_reservation is None:
            _admission_line(_program, _prov, _cpr, _declared, ADMIT_REFUSED,
                            llm_pool.free(_prov), _cap)
            state_headroom(kernel, _program, False)
            llm.llm_pool_reflect(kernel, _prov)
            # THE REASON TRAVELS AS DATA (D11). The message is for a person; a caller that
            # decides anything must not parse it. `reason` is the vocabulary id, `retry_at` is the
            # pool's own answer to "when can this be admitted again" — its day turn.
            from lib.akasha.workbench import wl_state as _wls
            return _err(rid, -32005, "LLM pool exhausted for %s today — job not admitted "
                        "(need=%d free=%d)" % (_prov, _cpr, llm_pool.free(_prov)),
                        {"reason": _wls.REASON_LLM_POOL, "provider": _prov, "need": _cpr,
                         "free": llm_pool.free(_prov), "retry_at": llm_pool.next_day_turn()})
        llm_reservation["declared"] = _declared
        _admission_line(_program, _prov, _cpr, _declared, ADMIT_RESERVED,
                        llm_pool.free(_prov), _cap)
        state_headroom(kernel, _program, True)
    elif _scheduled:
        _program = str(data.get("program") or data.get("label") or session.client_id)
        _admission_line(_program,
                        str(data.get("llm_provider") or "").strip().lower() or "-",
                        0, bool(data.get("llm_declared")), ADMIT_UNMETERED, None)
        # A run that asks for NOTHING cannot be short of room. Saying nothing here left the fact
        # unstated, and an unstated fact reads as "no" — which is how `news_show_x`, a workload
        # whose appetite is zero by declaration, answered `headroom` at the gate.
        state_headroom(kernel, _program, True)
    try:
        _weight = float(data["weight"]) if data.get("weight") is not None else None
    except (TypeError, ValueError):
        _weight = None
    job = JCLJob(
        owner=session.client_id,
        label=data.get("label", ""),
        steps=steps,
        fail_fast=bool(data.get("fail_fast", True)),
        depends_on=depends_on,
        max_retries=max_retries,
        timeout_s=timeout_s,
        llm_reservation=llm_reservation,
        llm_weight=_weight,
    )
    # A user-submitted batch requires consistency as a set — Class 2.
    kernel.harmonia.submit_job(job, job_class=CLASS_BATCH_ATOM)
    return _ok(rid, {"job_id": job.job_id, "label": job.label,
                     "step_count": job.step_count, "status": job.status,
                     "depends_on": job.depends_on})


def handle_job_ls(kernel, rid, data, session) -> dict:
    if not kernel.jcl_worker:
        return _ok(rid, {"summary": {}, "jobs": [], "queue_depth": 0})
    owner_filter = (data.get("owner") if _gate.gate(getattr(session, "client_id", ""), _gate.ADMIN)[0]
                    else session.client_id)
    all_jobs     = kernel.jcl_worker.list_jobs(owner=owner_filter or None)

    from collections import Counter
    counts = Counter(j.status for j in all_jobs)

    show_all    = str(data.get("all", "")).lower() in ("true", "1", "yes")
    status_filt = data.get("status", "").strip().upper() or None
    n_done      = max(0, int(data.get("n_done", 10)))

    if show_all or status_filt:
        visible = [j for j in all_jobs if not status_filt or j.status == status_filt]
    else:
        # Default: all active + last n_done completed jobs
        active  = [j for j in all_jobs if j.status in ("RUNNING", "PENDING", "FAILED", "CANCELLED")]
        done    = [j for j in all_jobs if j.status == "DONE"][:n_done]
        visible = active + done

    return _ok(rid, {
        "summary": {
            "running":   counts.get("RUNNING", 0),
            "pending":   counts.get("PENDING", 0),
            "done":      counts.get("DONE", 0),
            "failed":    counts.get("FAILED", 0),
            "cancelled": counts.get("CANCELLED", 0),
        },
        "queue_depth": kernel.jcl_worker.queue_depth(),
        "showing":     f"{len(visible)}/{len(all_jobs)} (add all=true to see all)",
        "jobs":        [_job_to_dict(j, brief=True) for j in visible],
    })


def handle_job_stat(kernel, rid, data, session) -> dict:
    job_id = str(data.get("job_id") or "").strip()
    if not job_id:
        return _err(rid, -32602, "job.stat requires 'job_id'")
    if not kernel.jcl_worker:
        return _err(rid, -32002, "JCL worker not available")
    job = kernel.jcl_worker.get_job(job_id)
    if not job:
        return _err(rid, -32002, f"Job '{job_id}' not found")
    if job.owner != session.client_id and not _gate.gate(session.client_id, _gate.ADMIN)[0]:
        return _err(rid, -32003, "Permission denied")
    return _ok(rid, _job_to_dict(job, brief=False))


def handle_job_cancel(kernel, rid, data, session) -> dict:
    # `job.cancel` reaches here having passed the gate for its declared action; the scope-string
    # test that stood here was the second gate (ruling §5), under a rule the table cannot see.
    job_id = str(data.get("job_id") or "").strip()
    if not job_id:
        return _err(rid, -32602, "job.cancel requires 'job_id'")
    if not kernel.jcl_worker:
        return _err(rid, -32002, "JCL worker not available")
    cancelled = kernel.jcl_worker.cancel(job_id, requester=session.client_id)
    return _ok(rid, {"cancelled": cancelled, "job_id": job_id})


def handle_workflow_def(kernel, rid, data, session, ctx) -> dict:
    name   = (data.get("name") or "").strip()
    script = data.get("script") or ""
    if not name or not script:
        return _err(rid, -32602, "workflow.def requires 'name' and 'script'")
    # Reject only genuine SYNTAX errors at definition time (tokenize/parse). We do
    # NOT run the semantic method-existence validator here: it loads its own
    # ConceptRegistry which can differ from the live kernel's, producing false
    # "unknown method" rejections for perfectly valid concept-model calls. Real
    # method/param errors surface at run time via csl.run.
    try:
        from lib.akasha.csl import tokenize, parse
        parse(tokenize(script))
    except ImportError:
        pass
    except Exception as _pe:
        return _err(rid, -32602, f"workflow CSL syntax error: {_pe}")
    cid = session.client_id
    key = ctx.put_chunk(
        content=script,
        meta={"type": _wf.META_WORKFLOW, "name": name,
              "description": data.get("description", "")},
        author=cid,
        scopes=[_wf.SCOPE_EXECUTABLE, f"owner:user_{cid}", f"view:user_{cid}"],
    )
    ctx.set_alias(key, f"{_wf.WF_ALIAS_PREFIX}{name}")
    return _ok(rid, {"status": "defined", "name": name, "key": key,
                     "alias": f"{_wf.WF_ALIAS_PREFIX}{name}"})


def handle_workflow_run(kernel, rid, data, session, ctx) -> dict:
    # workflow.run submits a JCL job → the same ONE gate as job.submit, asked once, at the
    # dispatcher. The scope-string test that stood here is deleted (ruling §5).
    _allowed, _why = _gate.gate(getattr(session, "client_id", ""), _gate.RUN)
    if not _allowed:
        _gate.refuse_log(getattr(session, "client_id", ""), _gate.RUN, "workflow.run", _why)
        return _err(rid, -32003, "%s: workflow.run" % _why)
    if not kernel.jcl_worker or not JCLJob or not JCLStep:
        return _err(rid, -32002, "JCL worker not available")
    name = (data.get("name") or "").strip()
    if not name:
        return _err(rid, -32602, "workflow.run requires 'name'")
    key = ctx.resolve_alias(f"{_wf.WF_ALIAS_PREFIX}{name}")
    if not key:
        return _err(rid, -32001, f"Workflow '{name}' not found.")
    meta = ctx.get_meta(key) or {}
    if meta.get("type") != _wf.META_WORKFLOW:
        return _err(rid, -32001, f"'{name}' is not a workflow definition.")
    script = ctx.get_chunk(key) or ""
    if not script:
        return _err(rid, -32001, f"Workflow '{name}' has no script body.")
    # One bounded JCL job, one csl.run step: the CSL runtime resolves the script's
    # named $vars inline; Harmonia provides the orchestration around it.
    job = JCLJob(
        owner=session.client_id,
        label=f"wf:{name}",
        steps=[JCLStep(method="csl.run", params={"script": script})],
        fail_fast=True,
    )
    kernel.harmonia.submit_job(job, job_class=CLASS_BATCH_ATOM)
    return _ok(rid, {"status": "submitted", "workflow": name,
                     "job_id": job.job_id, "job_label": job.label})


def handle_workflow_ls(kernel, rid, data, session, ctx) -> dict:
    rows = ctx.get_aliases_by_pattern(f"{_wf.WF_ALIAS_PREFIX}%") or []
    out = []
    for r in rows:
        alias = r.get("alias") if isinstance(r, dict) else r
        key   = r.get("key") if isinstance(r, dict) else ctx.resolve_alias(alias)
        meta  = (ctx.get_meta(key) or {}) if key else {}
        if meta.get("type") == _wf.META_WORKFLOW:
            out.append({"name": meta.get("name", alias[len(_wf.WF_ALIAS_PREFIX):]),
                        "alias": alias, "description": meta.get("description", "")})
    return _ok(rid, {"workflows": out, "count": len(out)})


def handle_workflow_get(kernel, rid, data, session, ctx) -> dict:
    name = (data.get("name") or "").strip()
    if not name:
        return _err(rid, -32602, "workflow.get requires 'name'")
    key = ctx.resolve_alias(f"{_wf.WF_ALIAS_PREFIX}{name}")
    if not key:
        return _err(rid, -32001, f"Workflow '{name}' not found.")
    meta = ctx.get_meta(key) or {}
    return _ok(rid, {"name": name, "key": key,
                     "description": meta.get("description", ""),
                     "script": ctx.get_chunk(key) or ""})


def handle_workflow_rm(kernel, rid, data, session, ctx) -> dict:
    name = (data.get("name") or "").strip()
    if not name:
        return _err(rid, -32602, "workflow.rm requires 'name'")
    alias = f"{_wf.WF_ALIAS_PREFIX}{name}"
    key = ctx.resolve_alias(alias)
    if not key:
        return _err(rid, -32001, f"Workflow '{name}' not found.")
    meta = ctx.get_meta(key) or {}
    if meta.get("type") != _wf.META_WORKFLOW:
        return _err(rid, -32001, f"'{name}' is not a workflow definition.")
    # Unbind the wf:<name> alias — the workflow disappears from ls/run/get. The
    # (content-addressed, now-unreferenced) definition atom is harmless residue.
    ctx.delete_alias(alias)
    return _ok(rid, {"status": "removed", "name": name})


def reconcile_headroom(kernel) -> int:
    """Every declared workload's HEADROOM, stated from the pool's own answer — at boot, and at the
    pool's DAY TURN (D12).

    Admission states this Set at reserve, refusal and settle — the moments the answer can change.
    A workload that has not run yet has had no such moment, and an unstated positive fact reads as
    "no", so the gate answered `headroom` for a programme that was simply new (or for the whole
    cell after a restart, since the Sets do not survive one). Boot is the moment it can be known
    without a run: the pool knows whether this key is over its allotment today.

    A cell with no pool (no provider configured) leaves every workload WITH room: the pool is what
    withholds it, and a pool that does not exist withholds nothing."""
    from lib.akasha import api as _api
    from lib.akasha.workbench import workload
    over = _api.hook(kernel, "llm_over_allotment")
    prov_fn = _api.hook(kernel, "llm_active_provider")
    prov = str((prov_fn(kernel) if prov_fn else "") or "")
    room, tight = [], []
    try:
        for decl in (workload.declarations(kernel) or []):
            k = workload.key(decl)
            has = True
            if over and prov:
                try:
                    has = not bool(over(prov, k))
                except Exception:                 # noqa: BLE001 — the pool's own answer, or room
                    has = True
            _facts.headroom(kernel, k, has)
            (room if has else tight).append(k)
    except Exception as exc:                      # noqa: BLE001 — a boot never dies of bookkeeping
        logger.warning("[llm] headroom reconcile skipped: %s: %s", type(exc).__name__, exc)
    logger.info("[llm] headroom reconciled provider=%s room=%d tight=%d tight_keys=[%s]",
                prov or "-", len(room), len(tight), ",".join(sorted(tight)))
    return len(room) + len(tight)


def observe_day_turn(kernel, today: str = None) -> bool:
    """Re-state every key's headroom when the POOL'S DAY TURNS (D12). True when it turned.

    Headroom goes false at a refusal and only a reserve, a settle or a boot ever set it true again —
    so a key refused once stayed locked at the gate's step 4 after the pool had refilled: on 09-26
    the gate answered `headroom` with 476 calls free, and nothing short of a restart would clear it.
    The day turn is the moment the answer changes for EVERY key at once, so it is stated then, by
    the same function the boot uses and from the pool's own answer.

    Called from the driver's minute tick, which is always running on a live cell; the first call of
    a process only records the day (the boot reconcile has just stated it)."""
    from lib.akasha.workbench import llm_pool
    d = today or llm_pool.day()
    seen = getattr(kernel, "_pool_day_seen", None)
    kernel._pool_day_seen = d
    if seen is None or seen == d:
        return False
    logger.info("[llm] pool day turned %s → %s — headroom re-stated for every key", seen, d)
    reconcile_headroom(kernel)
    return True
