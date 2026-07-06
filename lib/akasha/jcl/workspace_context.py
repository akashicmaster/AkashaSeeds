"""
Workspace context — the thread-local "active Harmonia workspace" marker.

This is the seam that makes a management unit's writes *reversible* (Appendix E of
docs/for-llm/orchestration-architecture.md). While a tracked workspace is active on
a thread, every graph write that engine commits is recorded in the workspace's
tracking set, so:

  - rollback  → drop exactly those keys (the unit's I/O footprint) — reversibility
  - commit    → release the set; the writes stand (point of no return)

It is a leaf module (only `threading`) so both the composite engine layer (which
records writes) and Harmonia (which opens/closes the workspace) can use it without
any circular import. Per-thread by design: a JCL worker thread, or a request thread
running a conversation bundle, each has its own active workspace.

Slice 1 scope: tracking is opt-in (tracked=True), so untracked workspaces (boot /
batch / link) behave exactly as before with zero overhead — the only cost on the
untracked hot path is one thread-local read.
"""
import threading
import logging
from contextlib import contextmanager

logger = logging.getLogger("Akasha.Workspace")

_local = threading.local()

# ── Hard-guard state (slice 2) ──────────────────────────────────────────────
# ENFORCE selects the guard's mode: reject (True, shipped) vs observe/warn (False).
# It is True in production — a memory write with no workspace/exemption raises. It was
# False only during the historical rollout, so the mechanism could be built and the
# coverage map collected before flipping it on; `_unguarded` (the coverage map) is a
# vestige of that rollout and stays only as an observe-mode diagnostic if ever reset.
ENFORCE = True
_unguarded = {}          # author -> count of unguarded graph writes observed
_unguarded_lock = threading.Lock()


def begin(tx_id: str, engine) -> None:
    """Mark a tracked workspace active on this thread (engine = the AkashaEngine
    whose commits should be recorded into tx_id's tracking set)."""
    _local.tx_id = tx_id
    _local.engine = engine


def active():
    """Return (tx_id, engine) for the active tracked workspace on this thread,
    or (None, None) if none is active."""
    return getattr(_local, "tx_id", None), getattr(_local, "engine", None)


def end() -> None:
    """Clear the active tracked workspace on this thread."""
    _local.tx_id = None
    _local.engine = None


# ── Workspace presence (tracked OR untracked) + carried priority ─────────────
# `active()` above only reports *tracked* workspaces (those that record keys for
# rollback). The single-route guard, however, must accept ANY workspace — a
# batch/link job runs under an untracked workspace but is still legitimately
# orchestrated. enter/exit maintain a stack (one entry per open workspace) so the
# guard can tell "under Harmonia" from "raw write with no orchestration".
#
# Each stack entry is the workspace's PRIORITY (the projection Harmonia computed at
# admission: 0=HIGH conversation .. 3=IDLE). The WriteQueue reads the top of this
# stack (current_priority) to order writes at the single serialization point —
# interactive/conversation writes served before background batch writes. Depth and
# priority are the same structure: len(stack) is the presence depth.

# Priority levels (lower = served first), mirroring HarmoniaEngine.priority_of.
PRIO_HIGH, PRIO_NORMAL, PRIO_LOW, PRIO_IDLE = 0, 1, 2, 3


def enter_workspace(priority: int = PRIO_NORMAL) -> None:
    """Mark a Harmonia workspace (tracked or not) open on this thread, carrying the
    priority the WriteQueue should order this workspace's writes by."""
    stack = getattr(_local, "prio_stack", None)
    if stack is None:
        stack = _local.prio_stack = []
    stack.append(priority)


def exit_workspace() -> None:
    """Release one level of workspace presence on this thread."""
    stack = getattr(_local, "prio_stack", None)
    if stack:
        stack.pop()


def _in_workspace() -> bool:
    return bool(getattr(_local, "prio_stack", None))


def current_priority() -> int:
    """Priority of the innermost open workspace on this thread, or NORMAL if none.
    Read by WriteQueue.submit to order writes; a write with no workspace (system/
    bootstrap) defaults to NORMAL so it neither jumps nor is starved."""
    stack = getattr(_local, "prio_stack", None)
    return stack[-1] if stack else PRIO_NORMAL


# ── System / bootstrap exemption ────────────────────────────────────────────
# Boot/genesis/anchor/ref writes are legitimate graph writes that do not run under
# a user workspace. They wrap themselves in system_context() so the guard exempts
# them (they are still logged/auditable elsewhere — the exemption is from the
# workspace requirement, not from the record).

@contextmanager
def system_context():
    """Exempt graph writes on this thread from the workspace guard (boot/system)."""
    n = getattr(_local, "sys_depth", 0)
    _local.sys_depth = n + 1
    try:
        yield
    finally:
        _local.sys_depth = getattr(_local, "sys_depth", 1) - 1


def _in_system_context() -> bool:
    return getattr(_local, "sys_depth", 0) > 0


def guard(author: str = "") -> bool:
    """Check whether a graph write on this thread is permitted by the single-route
    rule. Allowed when a workspace is active OR inside a system_context. When
    neither: in ENFORCE mode raise PermissionError; otherwise record it (coverage
    map) and allow. Returns True if the write may proceed."""
    tx_id, _ = active()
    if tx_id is not None or _in_workspace() or _in_system_context():
        return True
    # No workspace, no exemption.
    if ENFORCE:
        raise PermissionError(
            "Memory write outside a Harmonia workspace is not permitted "
            "(single-route guard)."
        )
    with _unguarded_lock:
        _unguarded[author] = _unguarded.get(author, 0) + 1
    return True


def coverage_report() -> dict:
    """Snapshot of unguarded-write counts by author (observe-mode coverage map)."""
    with _unguarded_lock:
        return dict(_unguarded)
