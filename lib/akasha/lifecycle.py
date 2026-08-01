"""
Process lifecycle — coordinated graceful shutdown.

Why this exists: on exit, Akasha's background daemons (the ontology boot-load, the
JCL worker, the semantic/node learn daemons) and the per-thread SQLite connections
must be STOPPED and CLOSED *before* the interpreter finalizes the C-extension modules
(sqlite3, numpy). If a daemon is still executing C code — a SQLite write, a numpy op —
when the interpreter tears those modules down, the process segfaults during shutdown
(observed prominently on the very new Python 3.14, whose C internals are less forgiving).

This is deliberately backend-agnostic: it knows nothing about WAL or SQLite specifics.
It holds ONE shutdown flag that long-running loops check, a registry of open
connections to close, and `begin_shutdown()` which joins the daemons then closes the
connections. Correctness/durability do not depend on any of this (the WriteQueue +
synchronous=FULL already guarantee crash-stop); this only makes the *graceful* exit
clean instead of relying on the C module's finalization behaviour.
"""
import threading
import logging

logger = logging.getLogger("Akasha.Lifecycle")

_shutting_down = threading.Event()
_conns = []                       # every sqlite3 connection created, for a clean close
_wakes = []                       # callbacks that nudge a blocked worker to re-check the flag
_closers = []                     # backend.close callbacks (checkpoint + WriteQueue join)
_lock = threading.Lock()

# Background daemon thread names (see the start sites in kernel.py / jcl/worker.py /
# manager.py). The WriteQueue workers are stopped by the backend closers (which also
# checkpoint), NOT joined here — joining them before the checkpoint would deadlock.
_DAEMON_NAMES = {
    "ont-boot-loader", "ont-genesis-load", "ontology-reload", "ontology-reset-reload",
    "semantic-autolearn", "node-autolearn", "JCLWorker", "session-sweeper",
    "onto-load-watcher", "supervisor-health",
}


def is_shutting_down() -> bool:
    """True once graceful shutdown has begun. Long-running daemon loops check this at
    their boundaries and return, so no thread is mid-C-op at interpreter teardown."""
    return _shutting_down.is_set()


def wait_or_shutdown(timeout: float) -> bool:
    """Sleep up to `timeout` seconds, but wake IMMEDIATELY if shutdown begins. Returns
    True if shutting down (caller should return). Use in daemons with long sleeps so they
    exit promptly instead of forcing a join timeout."""
    return _shutting_down.wait(timeout)


def register_conn(conn) -> None:
    """Track a freshly-created SQLite connection so it can be closed on shutdown."""
    with _lock:
        _conns.append(conn)


def register_wake(fn) -> None:
    """Register a callback that unblocks a worker parked on a queue (e.g. by putting a
    poison-pill), so it wakes, sees is_shutting_down(), and exits."""
    with _lock:
        _wakes.append(fn)


def register_closer(fn) -> None:
    """Register a backend close() — checkpoints and drains+joins its WriteQueue worker.
    Run on shutdown AFTER the daemons stop feeding writes, BEFORE connections close."""
    with _lock:
        _closers.append(fn)


def begin_shutdown(join_timeout: float = 4.0) -> None:
    """Signal the shutdown flag, wake + join the background daemons, then close every
    tracked SQLite connection. Idempotent and safe to call from the exit path AND atexit.
    Never raises."""
    if _shutting_down.is_set():
        return
    _shutting_down.set()
    try:
        with _lock:
            wakes = list(_wakes)
        for fn in wakes:
            try:
                fn()
            except Exception:
                pass
        # 1. Join the C-op daemons (they check is_shutting_down() and return), so nothing
        #    keeps feeding the write queues or reading during teardown.
        me = threading.current_thread()
        for t in list(threading.enumerate()):
            if t is me or not t.is_alive():
                continue
            if t.name in _DAEMON_NAMES:
                try:
                    t.join(timeout=join_timeout)
                except Exception:
                    pass
        # 2. Close the backends (checkpoint WAL + drain/join each WriteQueue worker), so
        #    no writer thread is alive when we close connections.
        with _lock:
            closers = list(_closers)
        for fn in closers:
            try:
                fn()
            except Exception:
                pass
        # 3. Now every thread that could touch SQLite is stopped — close all connections
        #    so the sqlite3 C module finalizes with nothing open/in-use.
        with _lock:
            conns = list(_conns)
            _conns.clear()
        for c in conns:
            try:
                c.close()
            except Exception:
                pass
    except Exception as exc:                       # shutdown must never itself crash
        logger.debug("[Lifecycle] begin_shutdown non-fatal error: %s", exc)
