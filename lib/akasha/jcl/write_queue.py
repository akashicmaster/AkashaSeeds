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

import os
import queue
import time
import itertools
import threading
import concurrent.futures
import logging
from typing import Any, Callable, Optional

logger = logging.getLogger("Harmonia.WriteQueue")


def _host_is_constrained() -> bool:
    """A single-GIL host where a background write flood (boot ontology load) can
    starve the interactive threads that serve the web portal — chiefly a-Shell /
    iOS (which the runtime reports as iPadOS/iOS) and genuinely low-core machines.
    On a capable desktop the GIL's own time-slicing keeps the portal responsive, so
    the pacing below is a no-op there."""
    try:
        import platform
        s = platform.system().lower()
        if s in ("ios", "ipados", "iphoneos"):
            return True
        if platform.machine().lower().startswith(("ipad", "iphone")):
            return True
    except Exception:
        pass
    return (os.cpu_count() or 4) <= 2


# Background-write pacing (constrained hosts only). While a background job (priority
# >= _BG_PRIO) is flooding the queue, cede the CPU for _YIELD_S every _YIELD_INTERVAL
# of processing so interactive threads (the portal's RPCs) get a fair share. Only
# background items are paced — interactive writes (priority 0) are never delayed. The
# overhead is proportional (~_YIELD_S/_YIELD_INTERVAL of background time) and tunable.
_CONSTRAINED = _host_is_constrained()
_BG_PRIO = 2                                                    # 0=HIGH..3=IDLE; >=2 is background
# Defaults cede ~35% of background time to interactive threads — enough to keep the
# portal responsive on a-Shell; boot (already slow there) is proportionally longer.
# Tune with AKASHA_WQ_YIELD_INTERVAL_MS / AKASHA_WQ_YIELD_MS (larger yield = snappier
# portal, slower boot; set yield to 0 to disable pacing entirely).
_YIELD_INTERVAL = float(os.environ.get("AKASHA_WQ_YIELD_INTERVAL_MS", "15")) / 1000.0
_YIELD_S = float(os.environ.get("AKASHA_WQ_YIELD_MS", "8")) / 1000.0
_PACING = _CONSTRAINED and _YIELD_S > 0                         # off on desktop / when disabled


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
        # Set once close/shutdown begins: from then on, ordinary submits from OTHER
        # threads are dropped instead of queued, so a still-running background feeder
        # (the boot-load daemon) stops handing the worker new SQLite writes. That lets
        # the worker reach the shutdown sentinel and EXIT before the connection is closed
        # and the interpreter finalizes the sqlite3 C module — closing the teardown race
        # that segfaulted an `exit` issued mid-load. Dropped late writes are acceptable
        # under the crash-stop model ("only the last in-flight write is lost").
        self._closing = False
        t = threading.Thread(target=self._run, daemon=True, name=name)
        t.start()

    def _run(self) -> None:
        self._worker = threading.current_thread()
        _last_yield = time.monotonic()
        while True:
            _prio, _seq, item = self._q.get()
            if item is None:       # shutdown sentinel
                return
            fn, future = item
            try:
                future.set_result(fn())
            except Exception as exc:
                future.set_exception(exc)
            # Constrained hosts only: while a background flood (boot ontology load)
            # runs, briefly cede the CPU so the web portal's interactive RPCs are not
            # starved. Paces BACKGROUND items only; interactive writes run full speed.
            if _PACING and _prio >= _BG_PRIO:
                if time.monotonic() - _last_yield >= _YIELD_INTERVAL:
                    time.sleep(_YIELD_S)
                    _last_yield = time.monotonic()

    def submit(self, fn: Callable[[], Any], priority: Optional[int] = None,
               force: bool = False) -> Any:
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
        # Shutting down: drop late writes from feeder threads so no new SQLite work is
        # started while the connection is being closed (crash-stop). `force=True` (the
        # close-path checkpoint) still runs.
        if self._closing and not force:
            return None
        if priority is None:
            from lib.akasha.jcl.workspace_context import current_priority
            priority = current_priority()
        f: concurrent.futures.Future = concurrent.futures.Future()
        self._q.put((int(priority), next(self._seq), (fn, f)))
        return f.result()

    def begin_closing(self) -> None:
        """Stop accepting new writes from other threads (feeders drain to no-ops)."""
        self._closing = True

    def shutdown(self, join_timeout: float = 15.0) -> None:
        """Stop the worker and WAIT for it to exit, so no write is in flight when the
        caller closes the SQLite connection / the interpreter tears the C module down.
        The sentinel is HIGH priority (-1) so the worker exits right after the current
        item — dropping any not-yet-started backlog (crash-stop) rather than draining a
        possibly-huge boot-load queue at exit."""
        self._closing = True
        self._q.put((-1, next(self._seq), None))
        w = self._worker
        if w is not None and w.is_alive() and threading.current_thread() is not w:
            w.join(join_timeout)
