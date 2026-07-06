"""
Single-threaded write serializer.

All submitted callables execute sequentially in one dedicated daemon thread,
eliminating concurrent write contention without any locks.

Callers block until their write completes (synchronous submission).

Re-entrance: if submit() is called from within the worker thread itself
(e.g. a write method that calls another write method internally), the
callable executes directly without re-queuing — avoiding deadlock.

Role in the homoiconic job graph:
  WriteQueue is the execution engine for Harmonia's job scheduler.  When a
  set of Atoms is granted executable permission (scope:job:executable), the
  same graph-traversal code that resolves semantic queries also drives job
  execution — Harmonia walks ref:because / ref:therefore links to determine
  dependency order, evaluates ref:if conditions, and submits each job step
  as a callable to this queue.

  The single-worker model is load-bearing here: it ensures that a simulated
  control loop (Atoms as sensor/actuator stubs) and a live hardware loop
  (get_chunk_raw / put_chunk_raw mapped to real I/O) both execute with
  identical deterministic ordering.  Parallelism between steps would
  introduce timing races that are unacceptable in closed-loop control.

  Priority order (same as knowledge writes):
    HIGH   → operator / interactive commands
    NORMAL → user job steps
    LOW    → background: LLM batch, ontology load, sensor polling loops
"""

import queue
import itertools
import threading
import concurrent.futures
import logging
from typing import Any, Callable, Optional

logger = logging.getLogger("Harmonia.WriteQueue")


class WriteQueue:
    def __init__(self, name: str = "write-queue"):
        # PriorityQueue, not FIFO: when several writer threads have work waiting,
        # the single worker serves the lowest priority number first (0=HIGH
        # conversation .. 3=IDLE background), so an interactive write is never made
        # to wait behind queued background writes at this — the actual — write
        # serialization point. A monotonic seq breaks ties FIFO within a priority and
        # guarantees the (fn, future) payload is never compared. Still ONE worker:
        # priority changes ORDER, never adds parallelism (serial-writes invariant).
        self._q: "queue.PriorityQueue" = queue.PriorityQueue()
        self._seq = itertools.count()
        self._worker: Optional[threading.Thread] = None
        t = threading.Thread(target=self._run, daemon=True, name=name)
        t.start()

    def _run(self) -> None:
        self._worker = threading.current_thread()
        while True:
            _prio, _seq, item = self._q.get()
            if item is None:       # shutdown sentinel
                return
            fn, future = item
            try:
                future.set_result(fn())
            except Exception as exc:
                future.set_exception(exc)

    def submit(self, fn: Callable[[], Any], priority: Optional[int] = None) -> Any:
        """
        Submit a zero-argument callable; block until it executes and return
        its result.  Exceptions from fn propagate to the calling thread.

        Priority (lower = served first) defaults to the priority of the active
        Harmonia workspace on the calling thread (workspace_context.current_priority
        — HIGH for a conversation turn, LOW for background jobs), so callers need no
        changes: the projection Harmonia computed at admission flows through to the
        write point automatically. An explicit priority argument overrides it.

        If called from within the worker thread (re-entrant call), fn()
        runs directly to avoid deadlock.
        """
        if threading.current_thread() is self._worker:
            return fn()
        if priority is None:
            from lib.akasha.jcl.workspace_context import current_priority
            priority = current_priority()
        f: concurrent.futures.Future = concurrent.futures.Future()
        self._q.put((int(priority), next(self._seq), (fn, f)))
        return f.result()

    def shutdown(self) -> None:
        """Signal the worker to stop after draining pending items."""
        # Highest priority number so it drains only after real work already queued.
        self._q.put((9999, next(self._seq), None))
