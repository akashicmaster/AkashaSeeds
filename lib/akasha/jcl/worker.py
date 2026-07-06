"""
JCL Worker — background job executor under Harmonia orchestration.

Architecture:
  - Each JCLJob runs as an atomic Harmonia Workspace (begin → steps → commit/rollback)
  - Steps execute sequentially; each step is a normal kernel.dispatch() call
  - Thread-pool is daemon threads → jobs finish before process exit only if fast;
    long batches survive as long as the main process stays alive
  - I/O deadlock is structurally impossible: each step is a self-contained RPC call;
    no step waits on another step's output (queue is the step list itself)
  - Rollback evidence is always written to Cortex even on failure, so the audit
    trail is recoverable via job.log
"""
import time
import queue
import threading
import logging
from typing import Dict, Optional, List

from lib.akasha.jcl.job import JCLJob, PENDING, RUNNING, DONE, FAILED, CANCELLED

logger = logging.getLogger("Akasha.JCL.Worker")

_MAX_JOBS_RETAINED = 2000  # oldest jobs are evicted after this cap


class JCLWorker:
    """Thread-pool JCL executor. Injected into KernelDispatcher at boot."""

    def __init__(self, kernel_dispatcher, max_workers: int = 2):
        self._kernel = kernel_dispatcher
        self._jobs: Dict[str, JCLJob] = {}
        self._order: List[str] = []           # insertion order for eviction
        self._queue: queue.Queue = queue.Queue()
        self._lock = threading.Lock()

        for _ in range(max_workers):
            t = threading.Thread(target=self._run_loop, daemon=True, name="JCLWorker")
            t.start()

    # ------------------------------------------------------------------ public

    def submit(self, job: JCLJob) -> JCLJob:
        with self._lock:
            self._jobs[job.job_id] = job
            self._order.append(job.job_id)
            # Evict oldest entries if cap exceeded
            while len(self._order) > _MAX_JOBS_RETAINED:
                old_id = self._order.pop(0)
                self._jobs.pop(old_id, None)

        self._queue.put(job.job_id)
        logger.info(f"[JCL] Queued {job.job_id} owner={job.owner} steps={job.step_count}")
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
            logger.info(f"[JCL] Cancelled {job_id}")
            return True
        return False   # already RUNNING / DONE / FAILED

    def queue_depth(self) -> int:
        return self._queue.qsize()

    # ----------------------------------------------------------------- private

    def _run_loop(self):
        while True:
            job_id = self._queue.get()
            job = self._jobs.get(job_id)
            if not job or job.status == CANCELLED:
                continue
            try:
                self._execute_job(job)
            except Exception as exc:
                logger.error(f"[JCL] Unhandled exception in worker loop: {exc}", exc_info=True)

    @staticmethod
    def _expand_it(params: dict, last_key: Optional[str]) -> dict:
        """
        Pre-expand $it in step params using the job-local last written key.

        $it is semantically "the atom I just wrote in this job" — it must be
        job-local, not session-global.  Without this expansion the resolver
        would read session.last_written_id, a plain Python attribute that is
        written outside the WriteQueue and therefore subject to data races when
        max_workers > 1.

        We expand only the top-level param dict (one level deep is sufficient
        for all known CSL patterns: target=$it, src=$it, id=$it).
        Nested dicts and lists are also handled for completeness.
        """
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

    def _execute_job(self, job: JCLJob):
        job.status = RUNNING
        logger.info(f"[JCL] Starting {job.job_id} ({job.step_count} steps)")

        # Acquire session & cortex
        try:
            session = self._kernel.manager.get_session(job.owner)
            ctx     = session.local_cortex
        except Exception as e:
            job.status      = FAILED
            job.error       = f"Session unavailable: {e}"
            job.completed_at = time.time()
            logger.error(f"[JCL] {job.job_id} session error: {e}")
            return

        # Open Harmonia workspace — each job is one atomic transaction
        tx_id = None
        if self._kernel.harmonia:
            try:
                tx_id    = self._kernel.harmonia.begin_workspace(ctx, f"jcl:{job.label or job.job_id}")
                job.tx_id = tx_id
            except Exception as e:
                logger.warning(f"[JCL] Harmonia workspace unavailable (non-fatal): {e}")

        # Job-local $it tracking: the last atom key written within this job.
        # Pre-expanded before dispatch so the resolver never touches the shared
        # session.last_written_id attribute — eliminating the data race when
        # multiple JCL workers run in parallel.
        last_key: Optional[str] = None

        # Execute steps sequentially
        # Deadlock analysis: each step is a self-contained dispatch(); no step
        # blocks waiting for another step's queue output → deadlock impossible.
        try:
            for i, step in enumerate(job.steps):
                if job.status == CANCELLED:
                    break

                # Expand $it references using the job-local last_key so that
                # parallel jobs cannot corrupt each other's context variable.
                expanded_params = self._expand_it(step.params, last_key)

                payload = {
                    "jsonrpc": "2.0",
                    "method":  step.method,
                    "params":  {
                        "session_token": job.owner,
                        "data":          expanded_params,
                    },
                    "id": f"{job.job_id}:s{i}",
                }
                # Kernel-originated in-process dispatch: the job owner (which may
                # be a bare id like "admin" or a system identity like
                # "system.weaver") is trusted here — TRUST_INTERNAL.
                resp = self._kernel.dispatch(payload, "internal")

                # Update job-local last_key from the response so the next step
                # can reference $it correctly without touching session state.
                if isinstance(resp.get("result"), dict):
                    new_key = resp["result"].get("key")
                    if new_key:
                        last_key = new_key

                if "error" in resp:
                    err = resp["error"]
                    msg = err.get("message", str(err)) if isinstance(err, dict) else str(err)
                    step_err = f"Step {i + 1} [{step.method}]: {msg}"
                    if job.fail_fast:
                        raise RuntimeError(step_err)
                    # fail_fast=False: record and continue
                    job.step_errors.append(step_err)
                    logger.warning(f"[JCL] {job.job_id}: {step_err}")

                job.step_done = i + 1

            # Crystallise workspace on success
            if tx_id and self._kernel.harmonia:
                self._kernel.harmonia.commit_workspace(ctx, tx_id)

            # Drain deferred collection derivations accumulated during this job.
            # Alias writes enqueue leaf:/ns:/lang: derivations for async processing;
            # this is the Harmonia-orchestrated index path that complements the
            # fast synchronous write path.
            try:
                n = ctx.drain_derivation_queue()
                if n:
                    logger.info(f"[JCL] {job.job_id}: derived collections for {n} alias(es)")
            except Exception as _de:
                logger.warning(f"[JCL] {job.job_id}: derivation drain failed (non-fatal): {_de}")

            job.status       = DONE
            job.completed_at = time.time()
            logger.info(f"[JCL] {job.job_id} DONE ({job.step_done}/{job.step_count})")

        except Exception as exc:
            job.error        = str(exc)
            job.status       = FAILED
            job.completed_at = time.time()
            logger.error(f"[JCL] {job.job_id} FAILED: {exc}")

            # Rollback — pending atoms are purged; evidence atoms remain for audit
            if tx_id and self._kernel.harmonia:
                try:
                    self._kernel.harmonia.rollback_workspace(ctx, tx_id)
                except Exception as rb_err:
                    logger.error(f"[JCL] Rollback failed for {tx_id}: {rb_err}")

            # Write a permanent failure record to the cortex for job.log to surface
            try:
                ctx.put_chunk(
                    content=f"JCL FAILED: {job.job_id} — {job.error}",
                    meta={
                        "type":      "sys:jcl_failure_log",
                        "job_id":    job.job_id,
                        "label":     job.label,
                        "tx_id":     tx_id or "",
                        "step_done": job.step_done,
                        "step_total": job.step_count,
                    },
                    author="system.jcl",
                    scopes=["scope:sys:universal"],
                )
            except Exception:
                pass   # best-effort; don't mask the original failure
