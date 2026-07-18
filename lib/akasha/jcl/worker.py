"""
JCL Worker — background job executor under Harmonia orchestration.

Scheduling model (orchestration-architecture.md E.1–E.3 — slice 3):
  - A single worker thread is the mainframe *initiator*: one unit runs at a time, in
    priority order (priority changes ORDER, never adds parallelism — the serial-write
    invariant holds). Interactive/HIGH work is served before background/LOW work.
  - **Atomic units (Class-1 conversation)** run all their steps in ONE tracked
    workspace, to completion, never yielding — the perceived-immediate bundle is
    all-or-nothing.
  - **Interruptible units (Class 2/3/4 batch/link/maintenance)** run in bounded
    groups; at each group boundary they *yield* to a higher-priority ready job by
    re-queuing a continuation (resume cursor on the job). A long background job can
    therefore never monopolize the worker — a just-arrived higher-priority job
    overtakes at the next unit boundary. This is "overtake at unit boundaries"; the
    priority queue + continuation-requeue *is* the interruption stack.
  - **PERT dependency edges** — a job with `depends_on` is held out of execution
    until every listed job is DONE; if a dependency FAILs/CANCELs, the dependent is
    cancelled (failure cascade). Harmonia holds the blocked set; a completing job
    wakes its dependents.
  - **Retry + soft timeout** — an idempotent step (batch/link/maintenance) is retried
    up to `max_retries` before it counts as failed; a per-job soft deadline is checked
    at unit boundaries (a running step is never hard-preempted — no thread-kill,
    single-worker determinism preserved; an over-budget interruptible job yields).

  Rollback evidence is always written to Cortex on failure, so the audit trail is
  recoverable via job.log.
"""
import time
import queue
import itertools
import threading
import logging
from typing import Dict, Optional, List, Tuple

from lib.akasha.jcl.job import (JCLJob, JCLStep, PENDING, RUNNING, DONE, FAILED,
                                CANCELLED, CLASS_CONVERSATION, CLASS_BATCH_ATOM,
                                CLASS_LINK, CLASS_MAINTENANCE)

logger = logging.getLogger("Akasha.JCL.Worker")

_MAX_JOBS_RETAINED = 2000  # oldest jobs are evicted after this cap

# Interruptible jobs commit + check for a higher-priority overtaker every N steps.
# Smaller = finer yield/discard granularity (owner: "finer discard granularity is better") at the
# cost of one workspace open/commit per group; this balances responsiveness vs churn.
_GROUP_SIZE = 16

# Classes whose steps are safe to retry (content-addressed / idempotent writes).
_IDEMPOTENT_CLASSES = frozenset({CLASS_BATCH_ATOM, CLASS_LINK, CLASS_MAINTENANCE})

# Hard ceiling on a job's retry budget (defence against a wedged single worker — a
# huge max_retries on a deterministically-failing step would otherwise spin the one
# worker thread and starve every other job). Enforced at admission AND here.
_MAX_RETRIES_CEILING = 8

# Deterministic client-error codes: a retry cannot change the outcome (bad params,
# unknown method, capability/role/auth denial), so retrying only burns the worker.
# Only NON-deterministic / transient/internal errors are retried, and only bounded.
_NON_RETRYABLE_CODES = frozenset({-32700, -32600, -32601, -32602, -32001, -32003})


class JCLWorker:
    """Thread-pool JCL executor. Injected into KernelDispatcher at boot."""

    def __init__(self, kernel_dispatcher, max_workers: int = 2):
        self._kernel = kernel_dispatcher
        self._jobs: Dict[str, JCLJob] = {}
        self._order: List[str] = []           # insertion order for eviction
        # Priority queue ordered by (job.priority, seq): lower priority number runs
        # first (0=HIGH conversation .. 3=IDLE), and same-priority jobs run FIFO via
        # a monotonic sequence — the mainframe initiator model. A single worker is
        # preserved: priority changes ORDER, never parallelism. The priority scalar is
        # the projection Harmonia computed at admission; the executor never re-derives.
        self._queue: "queue.PriorityQueue" = queue.PriorityQueue()
        self._seq = itertools.count()
        self._lock = threading.Lock()
        # PERT: jobs whose dependencies are not yet satisfied wait here (not spinning
        # on the queue). A completing job wakes those whose deps are now resolved.
        self._blocked: Dict[str, JCLJob] = {}

        for _ in range(max_workers):
            t = threading.Thread(target=self._run_loop, daemon=True, name="JCLWorker")
            t.start()

    # ------------------------------------------------------------------ public

    def submit(self, job: JCLJob) -> JCLJob:
        with self._lock:
            self._jobs[job.job_id] = job
            self._order.append(job.job_id)
            while len(self._order) > _MAX_JOBS_RETAINED:
                old_id = self._order.pop(0)
                self._jobs.pop(old_id, None)
        self._enqueue(job)
        logger.info(f"[JCL] Queued {job.job_id} owner={job.owner} "
                    f"class={job.job_class} prio={job.priority} steps={job.step_count} "
                    f"deps={job.depends_on or '-'}")
        return job

    def get_job(self, job_id: str) -> Optional[JCLJob]:
        return self._jobs.get(job_id)

    def list_jobs(self, owner: Optional[str] = None) -> List[JCLJob]:
        with self._lock:
            jobs = list(self._jobs.values())
        if owner:
            jobs = [j for j in jobs if j.owner == owner]
        return sorted(jobs, key=lambda j: j.submitted_at, reverse=True)

    def cancel(self, job_id: str, requester: str) -> bool:
        job = self._jobs.get(job_id)
        if not job or job.owner != requester:
            return False
        if job.status == PENDING:
            job.status = CANCELLED
            job.completed_at = time.time()
            with self._lock:
                self._blocked.pop(job_id, None)
            logger.info(f"[JCL] Cancelled {job_id}")
            return True
        return False   # already RUNNING / DONE / FAILED

    def queue_depth(self) -> int:
        return self._queue.qsize()

    # ----------------------------------------------------------------- queue ops

    def _enqueue(self, job: JCLJob) -> None:
        # (priority, seq, job_id): PriorityQueue orders by the tuple; seq breaks ties
        # FIFO and guarantees job_id is never compared (job_ids are not ordered).
        self._queue.put((int(getattr(job, "priority", 2)), next(self._seq), job.job_id))

    def _higher_priority_waiting(self, job: JCLJob) -> bool:
        """True if a strictly-higher-priority job is queued right now — the signal for
        an interruptible job to yield at the next unit boundary. Peeks the heap head
        under the queue mutex (single consumer; producers only push)."""
        with self._queue.mutex:
            q = self._queue.queue
            head_prio = q[0][0] if q else None
        return head_prio is not None and head_prio < int(getattr(job, "priority", 2))

    # -------------------------------------------------------------- dependencies

    def _dep_state(self, job: JCLJob) -> str:
        """READY / WAIT / CANCEL — PERT gate over job.depends_on."""
        if not job.depends_on:
            return "READY"
        for dep_id in job.depends_on:
            dep = self._jobs.get(dep_id)
            if dep is None:
                # Dep not submitted yet — WAIT, not satisfied. A dependent may be
                # admitted before its dependency; it must hold until the dep appears
                # and completes (order-independent). A completing job wakes it; if the
                # id is a typo the job simply stays blocked (visible in job.ls).
                return "WAIT"
            if dep.status in (FAILED, CANCELLED):
                return "CANCEL"
            if dep.status != DONE:
                return "WAIT"
        return "READY"

    def _wake_dependents(self, finished: JCLJob) -> None:
        """A job reached a terminal state — re-admit or cancel any blocked dependents."""
        with self._lock:
            blocked = list(self._blocked.values())
        for job in blocked:
            if finished.job_id not in job.depends_on:
                continue
            state = self._dep_state(job)
            if state == "READY":
                with self._lock:
                    self._blocked.pop(job.job_id, None)
                self._enqueue(job)
                logger.info(f"[JCL] {job.job_id} unblocked (dep {finished.job_id} DONE)")
            elif state == "CANCEL":
                with self._lock:
                    self._blocked.pop(job.job_id, None)
                job.status = CANCELLED
                job.error = f"dependency {finished.job_id} did not complete"
                job.completed_at = time.time()
                logger.warning(f"[JCL] {job.job_id} CANCELLED (dep {finished.job_id} "
                               f"{finished.status})")
                # Propagate the cascade: this job's own dependents must fall too.
                self._wake_dependents(job)

    # ----------------------------------------------------------------- private

    @staticmethod
    def _expand_it(params: dict, last_key: Optional[str]) -> dict:
        """Pre-expand $it in step params using the job-local last written key.

        $it is "the atom I just wrote in this job" — job-local, not session-global.
        Expanding here keeps the resolver off the shared session.last_written_id
        attribute (a data race when max_workers > 1)."""
        if not last_key:
            return params

        def _expand(v):
            if v == "$it":
                return last_key
            if isinstance(v, dict):
                return {k2: _expand(v2) for k2, v2 in v.items()}
            if isinstance(v, list):
                return [_expand(item) for item in v]
            return v

        return {k: _expand(v) for k, v in params.items()}

    def _run_loop(self):
        while True:
            _prio, _seq, job_id = self._queue.get()
            job = self._jobs.get(job_id)
            if not job or job.status in (CANCELLED, DONE, FAILED):
                continue

            # PERT gate — hold the job out of execution until its deps resolve.
            state = self._dep_state(job)
            if state == "WAIT":
                with self._lock:
                    self._blocked[job.job_id] = job
                # Re-check after parking: if a dependency reached a terminal state in
                # the window between the check above and the park (its _wake_dependents
                # would have missed this job), re-admit/cancel it now instead of
                # blocking forever.
                restate = self._dep_state(job)
                if restate != "WAIT":
                    with self._lock:
                        parked = self._blocked.pop(job.job_id, None)
                    if parked is not None:
                        if restate == "CANCEL":
                            job.status = CANCELLED
                            job.error = "dependency did not complete"
                            job.completed_at = time.time()
                            self._wake_dependents(job)
                        else:
                            self._enqueue(job)
                continue
            if state == "CANCEL":
                job.status = CANCELLED
                job.error = "dependency did not complete"
                job.completed_at = time.time()
                self._wake_dependents(job)
                continue

            try:
                self._execute_job(job)
            except Exception as exc:
                logger.error(f"[JCL] Unhandled exception in worker loop: {exc}", exc_info=True)

    # ---- session / cortex acquisition -------------------------------------

    def _acquire(self, job: JCLJob):
        try:
            session = self._kernel.manager.get_session(job.owner)
            return session, session.local_cortex
        except Exception as e:
            job.status = FAILED
            job.error = f"Session unavailable: {e}"
            job.completed_at = time.time()
            logger.error(f"[JCL] {job.job_id} session error: {e}")
            return None, None

    # ---- one step, with idempotent retry ----------------------------------

    def _run_step(self, job: JCLJob, step: JCLStep, index: int,
                  last_key: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
        """Dispatch one step (with $it expansion + bounded retry for idempotent
        classes). Returns (new_last_key, error_message-or-None). Retries only
        transient errors and only up to a hard-capped budget, so a deterministically
        failing step can never spin the single worker."""
        retryable = job.job_class in _IDEMPOTENT_CLASSES
        budget = min(int(getattr(job, "max_retries", 0) or 0), _MAX_RETRIES_CEILING)
        while True:
            expanded = self._expand_it(step.params, last_key)
            payload = {
                "jsonrpc": "2.0",
                "method":  step.method,
                "params":  {"session_token": job.owner, "data": expanded},
                "id":      f"{job.job_id}:s{index}",
            }
            # Kernel-originated in-process dispatch: the job owner is trusted here.
            resp = self._kernel.dispatch(payload, "internal")

            if "error" not in resp:
                new_key = None
                if isinstance(resp.get("result"), dict):
                    new_key = resp["result"].get("key")
                return (new_key or last_key), None

            err = resp["error"]
            code = err.get("code") if isinstance(err, dict) else None
            msg = err.get("message", str(err)) if isinstance(err, dict) else str(err)
            # Deterministic errors are never retried (retrying can't change the result);
            # only transient/internal ones, and only within the capped budget.
            transient = code not in _NON_RETRYABLE_CODES
            if retryable and transient and job.retries_used < budget:
                job.retries_used += 1
                logger.warning(f"[JCL] {job.job_id} step {index + 1} retry "
                               f"{job.retries_used}/{budget} (code={code}): {msg}")
                continue  # idempotent + transient — safe to re-dispatch
            return last_key, f"Step {index + 1} [{step.method}]: {msg}"

    # ---- soft timeout ------------------------------------------------------

    def _over_budget(self, job: JCLJob) -> bool:
        if not job.timeout_s or not job.started_at:
            return False
        return (time.time() - job.started_at) > job.timeout_s

    # ---- dispatch by class -------------------------------------------------

    def _execute_job(self, job: JCLJob):
        if job.started_at is None:
            job.started_at = time.time()
        if job.job_class == CLASS_CONVERSATION:
            self._run_atomic(job)
        else:
            self._run_interruptible(job)

    # ---- atomic (Class-1 conversation): one workspace, no yielding ---------

    def _run_atomic(self, job: JCLJob):
        job.status = RUNNING
        logger.info(f"[JCL] Starting {job.job_id} atomic ({job.step_count} steps)")
        session, ctx = self._acquire(job)
        if ctx is None:
            return

        tx_id = None
        if self._kernel.harmonia:
            try:
                tx_id = self._kernel.harmonia.begin_workspace(
                    ctx, f"jcl:{job.label or job.job_id}", tracked=True,
                    evidence=False, priority=int(getattr(job, "priority", 0)))
                job.tx_id = tx_id
            except Exception as e:
                logger.warning(f"[JCL] Harmonia workspace unavailable (non-fatal): {e}")

        last_key = job.last_key
        try:
            for i, step in enumerate(job.steps):
                if job.status == CANCELLED:
                    break
                last_key, err = self._run_step(job, step, i, last_key)
                if err:
                    if job.fail_fast:
                        raise RuntimeError(err)
                    job.step_errors.append(err)
                    logger.warning(f"[JCL] {job.job_id}: {err}")
                job.step_done = i + 1
            if tx_id and self._kernel.harmonia:
                self._kernel.harmonia.commit_workspace(ctx, tx_id)
            self._drain(job, ctx)
            self._finish_done(job)
        except Exception as exc:
            self._finish_failed(job, exc, ctx, tx_id, rollback=True)

    # ---- interruptible (Class 2/3/4): grouped, yields at unit boundaries ----

    def _run_interruptible(self, job: JCLJob):
        job.status = RUNNING
        session, ctx = self._acquire(job)
        if ctx is None:
            return

        n = job.step_count
        try:
            while job.cursor < n:
                if job.status == CANCELLED:
                    return
                group_end = min(job.cursor + _GROUP_SIZE, n)

                tx_id = None
                if self._kernel.harmonia:
                    try:
                        # Untracked, evidence-free per-group workspace: presence +
                        # priority for the guard/WriteQueue; batch/link atoms are
                        # content-addressed and commit verified directly, so no
                        # per-atom rollback state is needed across the group.
                        tx_id = self._kernel.harmonia.begin_workspace(
                            ctx, f"jcl:{job.label or job.job_id}:g{job.cursor}",
                            tracked=False, evidence=False,
                            priority=int(getattr(job, "priority", 2)))
                    except Exception as e:
                        logger.warning(f"[JCL] workspace unavailable (non-fatal): {e}")

                try:
                    for i in range(job.cursor, group_end):
                        if job.status == CANCELLED:
                            break
                        job.last_key, err = self._run_step(job, job.steps[i], i, job.last_key)
                        if err:
                            if job.fail_fast:
                                raise RuntimeError(err)
                            job.step_errors.append(err)
                            logger.warning(f"[JCL] {job.job_id}: {err}")
                        job.step_done = i + 1
                        job.cursor = i + 1
                    if tx_id and self._kernel.harmonia:
                        self._kernel.harmonia.commit_workspace(ctx, tx_id)
                except Exception as exc:
                    # A group failed: reverse only this group's workspace, fail the job.
                    self._finish_failed(job, exc, ctx, tx_id, rollback=True)
                    return

                # ── Unit boundary: yield to a higher-priority overtaker, or if this
                # job has blown its soft deadline (let a fresh unit take a turn). ──
                if job.cursor < n and (self._higher_priority_waiting(job)
                                       or self._over_budget(job)):
                    reason = "overtaken" if self._higher_priority_waiting(job) else "over-budget"
                    logger.info(f"[JCL] {job.job_id} yields at step {job.cursor}/{n} "
                                f"({reason}) — re-queued to resume")
                    self._enqueue(job)   # continuation; resumes from job.cursor
                    return

            self._drain(job, ctx)
            self._finish_done(job)
        except Exception as exc:
            self._finish_failed(job, exc, ctx, None, rollback=False)

    # ---- shared completion paths ------------------------------------------

    def _drain(self, job: JCLJob, ctx):
        """Drain deferred collection derivations accumulated during this job."""
        try:
            nd = ctx.drain_derivation_queue()
            if nd:
                logger.info(f"[JCL] {job.job_id}: derived collections for {nd} alias(es)")
        except Exception as _de:
            logger.warning(f"[JCL] {job.job_id}: derivation drain failed (non-fatal): {_de}")

    def _finish_done(self, job: JCLJob):
        job.status = DONE
        job.completed_at = time.time()
        logger.info(f"[JCL] {job.job_id} DONE ({job.step_done}/{job.step_count})")
        self._wake_dependents(job)

    def _finish_failed(self, job: JCLJob, exc, ctx, tx_id, rollback: bool):
        job.error = str(exc)
        job.status = FAILED
        job.completed_at = time.time()
        logger.error(f"[JCL] {job.job_id} FAILED: {exc}")

        if rollback and tx_id and self._kernel.harmonia:
            try:
                self._kernel.harmonia.rollback_workspace(ctx, tx_id)
            except Exception as rb_err:
                logger.error(f"[JCL] Rollback failed for {tx_id}: {rb_err}")

        # Permanent failure record for job.log. Runs AFTER rollback (workspace closed),
        # so it is a system audit write with no workspace — exempt via system_context.
        try:
            from lib.akasha.jcl.workspace_context import system_context as _sys_ctx
            with _sys_ctx():
                ctx.put_chunk(
                    content=f"JCL FAILED: {job.job_id} — {job.error}",
                    meta={
                        "type":       "sys:jcl_failure_log",
                        "job_id":     job.job_id,
                        "label":      job.label,
                        "tx_id":      tx_id or "",
                        "step_done":  job.step_done,
                        "step_total": job.step_count,
                    },
                    author="system.jcl",
                    scopes=["scope:sys:universal"],
                )
        except Exception:
            pass   # best-effort; don't mask the original failure

        self._wake_dependents(job)
