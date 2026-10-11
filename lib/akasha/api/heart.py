"""
The heart's process-level helpers an application body may call — memory telemetry, the serialised
nightly-maintenance gate, the boot flags. Pure stdlib + `lib.akasha.memtrace`; imports no kernel.
Names keep their kernel spelling (the kernel imports them back from here), so a moved body is
unchanged. The `[maint]` / `[Health]` lines they emit keep the `Akasha.Kernel` logger name.
"""
import os
import re
import sys
import time
import logging
import threading as _threading_maint
from typing import Optional

logger = logging.getLogger("Akasha.Kernel")

def _rss_mb():
    """This process's resident memory in MB (Linux /proc, stdlib only), or None off-Linux.
    Used by the boot memory heartbeat so a SILENT daemon death (OOM-killer SIGKILL / C-ext
    segfault — no Python traceback) still leaves a self-diagnosis in the log: the RSS trajectory
    right up to the last line tells OOM (RSS climbing to the host ceiling) apart from a hard
    crash at flat RSS. Akasha owns its own diagnosis — the operator is never asked to run dmesg."""
    try:
        with open("/proc/self/status") as _f:
            for _line in _f:
                if _line.startswith("VmRSS:"):
                    return int(_line.split()[1]) // 1024      # kB → MB
    except (OSError, ValueError, IndexError):
        pass
    return None


# A57-b — a process-lifetime counter of semantic.search truncations, surfaced as ONE aggregate on the
# per-minute [Health] line instead of a per-call INFO (the cap is hit by every large query — 1,191
# lines in 11 h was pure noise). {cap, budget} so the RATE and the REASON are both visible at a glance.
_SEARCH_PARTIAL = {"cap": 0, "budget": 0}


def _search_partial_incr(reason: str) -> None:
    if reason in _SEARCH_PARTIAL:
        _SEARCH_PARTIAL[reason] += 1


# A56 §4 — the nightly maintenance tasks (telemetry/broadcast GC, semcache.replan, pulse.compact)
# run STRICTLY ONE AT A TIME with a 30 s gap and a memory/queue GATE, so they never overlap into the
# +600 MB / 2 min IPC stall the 09-11 nightly showed. One lock serialises them; the gate defers a
# start while the host is tight or the writer's IPC pool is backed up.
_MAINT_LOCK = _threading_maint.Lock()


_MAINT_LAST_DONE = [0.0]


_MAINT_GAP_S = 30.0


_MAINT_GATE_AVAIL_MB = 2500


_MAINT_GATE_MAX_WAIT_S = 1800     # 30 min, then skip


_MAINT_GATE_RETRY_S = 60


def _maint_gate_ok():
    """True when it is safe to start a nightly task: host MemAvailable ≥ 2.5 GB AND the writer's IPC
    accept queue is empty. Returns (ok, reason)."""
    avail = _mem_available_mb()
    if avail is not None and avail < _MAINT_GATE_AVAIL_MB:
        return False, "avail=%dMB<%d" % (avail, _MAINT_GATE_AVAIL_MB)
    try:
        import api.portals.cell_ipc as _ipc_mod
        q = int((_ipc_mod.server_stats() or {}).get("queued") or 0)
        if q > 0:
            return False, "ipc_q=%d" % q
    except Exception:
        pass
    return True, ""


def _run_gated_maint(task, fn):
    """A56 §4 — run `fn` as a serialised, gated nightly task. Acquires the shared maintenance lock
    (one task at a time), honours a 30 s gap after the previous task, then waits for the memory/queue
    gate (retry every 60 s up to 30 min, else log `[maint] skipped <task> reason=` and return None).
    Returns fn()'s result or None if skipped/shutting down."""
    from lib.akasha import lifecycle
    with _MAINT_LOCK:
        _since = time.time() - _MAINT_LAST_DONE[0]
        if _MAINT_LAST_DONE[0] and _since < _MAINT_GAP_S:
            for _ in range(int((_MAINT_GAP_S - _since) / 0.5) + 1):
                if lifecycle.is_shutting_down():
                    return None
                time.sleep(0.5)
        waited = 0.0
        while True:
            if lifecycle.is_shutting_down():
                return None
            ok, reason = _maint_gate_ok()
            if ok:
                break
            if waited >= _MAINT_GATE_MAX_WAIT_S:
                logger.warning("[maint] skipped %s reason=%s (gate not clear after %dmin)",
                               task, reason, int(_MAINT_GATE_MAX_WAIT_S / 60))
                return None
            for _ in range(int(_MAINT_GATE_RETRY_S / 0.5)):
                if lifecycle.is_shutting_down():
                    return None
                time.sleep(0.5)
            waited += _MAINT_GATE_RETRY_S
        try:
            return fn()
        finally:
            _MAINT_LAST_DONE[0] = time.time()
            # A58 — after each serialised nightly task, return freed heap arenas to the OS (gc +
            # malloc_trim) so its transient allocations do not become the writer's permanent floor; log
            # `[maint] trim Δrss=<MB>` (negative = freed). If retained stays high after this, the arena
            # was not the holder and a tracemalloc snapshot is the next step (never a guess).
            try:
                from lib.akasha import memtrace as _mt
                _dr, _trimmed = _mt.gc_trim()
                if _trimmed or (_dr is not None and abs(_dr) >= 1):
                    logger.info("[maint] trim after=%s Δrss=%sMB", task, _dr if _dr is not None else "?")
            except Exception:
                pass


def _with_rss_delta(tag, fn, concurrent=None):
    """A48.3 — run a writer-daemon task and log its memory footprint in the `[NativeLoad]` shape
    (`Δrss=…MB t=…s (rss a→b)`), INFO under 16 MB and WARNING above, so the A30 "who is climbing?"
    question is answered by the log per task, every day. Returns fn()'s result; never swallows its
    exception (the log line still prints the Δrss up to the raise).

    A54(2) — RSS is process-wide, so a Δ measured while OTHER JCL jobs ran is CONTAMINATED (e.g.
    `telemetry.evict Δrss=384MB` while `o1` was observing). `concurrent` is an optional callable →
    (n_running_jobs, [labels]); the line names them and the WARNING threshold applies ONLY when the
    task ran alone (concurrent=0)."""
    rss0 = _rss_mb()
    t0 = time.time()
    try:
        return fn()
    finally:
        rss1 = _rss_mb()
        dt = round(time.time() - t0, 1)
        d = (rss1 - rss0) if (rss0 is not None and rss1 is not None) else None
        cn, cnames = 0, []
        if concurrent is not None:
            try:
                cn, cnames = concurrent()
            except Exception:
                cn, cnames = 0, []
        _cs = (" concurrent=%d jobs=%s" % (cn, ",".join(str(x) for x in (cnames or [])[:4]))) if cn else ""
        # A56 §3 — IPC requests in flight are ALSO concurrent work whose memory the Δrss silently
        # blamed on this task; name them (a 100 s semantic.search) so the line is attributable.
        _ipc = ""
        _inflight_n = 0
        try:
            import api.portals.cell_ipc as _ipc_mod
            _st = _ipc_mod.inflight_stats() or {}
            _inflight_n = int(_st.get("count") or 0)
            if _inflight_n:
                _ipc = " ipc_inflight=%d slowest=%s:%ss" % (
                    _inflight_n, _st.get("slowest") or "-", _st.get("oldest_age") or 0)
        except Exception:
            pass
        line = "[maint] %s Δrss=%sMB t=%ss (rss %s→%s)%s%s" % (
            tag, ("%+d" % d if d is not None else "?"), dt, rss0, rss1, _cs, _ipc)
        # WARNING only when the task ran ALONE (no concurrent JCL job AND no IPC request in flight).
        if d is not None and d >= 16 and cn == 0 and _inflight_n == 0:
            logger.warning(line)
        else:
            logger.info(line)


def _mem_available_mb():
    """Host MemAvailable in MB (Linux /proc/meminfo, stdlib only), or None off-Linux. The
    heartbeat pairs this with RSS: OOM is imminent when MemAvailable falls toward zero while RSS
    climbs — it distinguishes 'this process is the hog' from 'the host is starved by neighbours'."""
    try:
        with open("/proc/meminfo") as _f:
            for _line in _f:
                if _line.startswith("MemAvailable:"):
                    return int(_line.split()[1]) // 1024      # kB → MB
    except (OSError, ValueError, IndexError):
        pass
    return None


def _smaps_rollup():
    """F49-3 — (anon_MB, file_map_MB) from /proc/self/smaps_rollup, or (None, None) off-Linux. Anon =
    heap/arena/mmap-anon growth (numpy/BLAS, glibc arenas); file_map = Rss − Anon = mapped files
    (a model, an mmap'd DB). Splitting these on the per-minute line separates the two growth kinds
    permanently and at negligible cost, so the unattributed native climb declares WHICH kind it is.
    One reader: `memtrace.smaps_rollup`, which the store's open line uses too."""
    from lib.akasha import memtrace as _mt
    return _mt.smaps_rollup()


def _thread_count():
    """This process's live thread count (Linux /proc/self/status Threads:), or None off-Linux.
    F47-3.1 — the leading OOM suspect was stacked one-thread-per-connection IPC handlers; after the
    bounded pool lands this number must be small and CONSTANT, so the heartbeat surfaces it."""
    try:
        with open("/proc/self/status") as _f:
            for _line in _f:
                if _line.startswith("Threads:"):
                    return int(_line.split()[1])
    except (OSError, ValueError, IndexError):
        pass
    return None


def _open_fd_count():
    """Count this process's open file descriptors (Linux /proc), or None off-Linux. Instruments the
    R2/F28b guest-FD story: the boot/steady heartbeat surfaces the FD count so an approaching ulimit
    is visible BEFORE `Errno 24 Too many open files` crashes a guest cell open."""
    try:
        return len(os.listdir("/proc/self/fd"))
    except OSError:
        return None


def _fd_soft_limit():
    """The process's soft RLIMIT_NOFILE (the ceiling FDs count toward), or None if unavailable."""
    try:
        import resource
        soft, _ = resource.getrlimit(resource.RLIMIT_NOFILE)
        return soft if soft != resource.RLIM_INFINITY else None
    except Exception:
        return None


def _autolearn_disabled_reason(series: Optional[str] = None) -> Optional[str]:
    """Decide whether the boot-time numpy autolearn (semantic + node embeddings) may run.
    Returns a human-readable reason string when it must be SKIPPED, or None when allowed.

    Same class of failure as the SpaCy weave gate in `_lemmatize_for_weave` — and the last
    native code left on the boot path once weave defaults to the regex floor: the two autolearn
    threads run numpy (PPMI+SVD, random-walk matrices) UNATTENDED inside the single-writer
    daemon shortly after boot. A numpy/BLAS C-extension segfault is NOT a Python exception, so
    the `try/except` in each `_run()` cannot catch it — it takes the whole writer down (the
    silent, deterministic boot death reproduced on Python 3.14 *after* SpaCy weave was already
    ruled out, and confirmed non-OOM: flat RSS, no dmesg OOM record). Autolearn is OPTIONAL
    enrichment: without it, atoms still carry the stdlib feature-hashing FLOOR vector
    (tensor.py), so semantic.search / dream / gap.scan degrade gracefully and never break.

      • Seeds line default-OFF (boot-latency Lever A / Phase 0-1): on a `seeds*` series the
        boot bake re-writes up to ~40k atoms through the single writer — a sustained CPU+disk
        burst that saturates the boot window (the CLI-open / portal-ready latency the user hit).
        It is OPTIONAL enrichment, so the seeds line skips it at boot and runs it ON DEMAND
        (`semantic.learn`) instead; the floor+mid vectors keep the meaning layer usable meanwhile.
      • Otherwise (service tiers): RUN on Python < 3.14 (numpy wheels are mature there); SKIP on
        Python >= 3.14, where the numpy/BLAS wheels are still immature and have hard-crashed the
        boot daemon. The floor tier keeps the meaning layer usable until the stack is verified.

    This mirrors the weave decision exactly: never let optional native ML kill — or, on the
    seeds line, throttle — the writer during boot.
    """
    # Decided by declared facts only — the process's role, the series, the interpreter. The
    # NO_/FORCE_ switches are deleted (the purge order §4.5).
    if os.environ.get("AKASHA_SERVE_ONLY", "").strip().lower() in ("1", "yes", "true", "on"):
        return "serve-only portal — the writer learns, the portal only reads"
    if series and str(series).lower().startswith("seeds"):
        return ("seeds line — boot autolearn default-off (the ~40k-atom bake would saturate the "
                "boot window); run `semantic.learn` on demand")
    if sys.version_info >= (3, 14):
        return ("Python %d.%d — numpy/BLAS boot autolearn is off here (a native segfault in the "
                "learn thread would crash the writer); run `semantic.learn` on demand"
                % sys.version_info[:2])
    return None


def shutting_down() -> bool:
    """True once the process has begun an orderly shutdown — the probe a long-running boot job
    polls so it stops at the next step instead of racing the store's close. Public so an
    application job asks it through the API instead of importing the lifecycle module."""
    try:
        from lib.akasha import lifecycle
        return bool(lifecycle.is_shutting_down())
    except Exception:
        return False


# The privileged identity that provisions + pulls live telemetry. A SYSTEM identity guaranteed to
# carry role:librarian (the shared-nucleus write privilege), so telemetry is PUBLISHED for public
# reads regardless of how a deployment's "admin" is scoped.
_FEED_WRITER = "system.librarian"


# The privileged identity that provisions + airs the AI News Station (svc:news-broadcast). A SYSTEM
# identity carrying role:librarian (so it may publish the public mirror to the shared nucleus) — the
# same one the broadcast relay uses. It owns the studio group, both casters, and speaks as them; the
# in-kernel broadcaster never depends on how a deployment's human "admin" is named.
_BROADCASTER = "system.broadcaster"


class _NucleusWriteCtx:
    """
    A lightweight proxy that routes all put_* operations to the nucleus engine
    while delegating read operations (and everything else) to the local cortex.

    Constructed by _route() when scope=universal and the caller has librarian
    rights.  Handlers receive this object as `ctx` and do not need to know
    which store they are writing to.
    """

    def __init__(self, local, nucleus):
        self._loc = local
        self._nuc = nucleus

    # --- write surface -------------------------------------------------------

    def put_chunk(self, content, meta=None, author="system", scopes=None):
        """Write atom to nucleus; return content-addressed key."""
        return self._nuc.put_atom(content, meta or {}, author=author)

    def put_link(self, src, dst, rel, w=1.0, author="system"):
        """Write link to nucleus."""
        return self._nuc.put_link(src, dst, rel, w=w, author=author)

    def set_alias(self, key, name, force=False):
        """Register alias in nucleus with proto-word auto-creation. force=True bypasses
        first-wins (authoritative ontology re-import superseding a prior nucleus atom)."""
        return self._nuc.set_alias(key, name, force=force)

    def add_to_set(self, name, key):
        """Add key to a named set in nucleus."""
        return self._nuc.add_to_set(name, key)

    # --- alias resolution ----------------------------------------------------

    def resolve_alias(self, alias):
        """Prefer nucleus alias resolution; fall back to local cortex."""
        return (self._nuc.core.get_key_by_alias(alias)
                or self._loc.core.get_key_by_alias(alias))

    # --- delegate all other attributes to local cortex -----------------------

    def __getattr__(self, name):
        # All read operations (get_chunk, stream, get_adjacent_links, etc.)
        # use the local cortex which already has nucleus fallback built in.
        return getattr(self._loc, name)


def _fmt_ts(ts) -> Optional[str]:
    """Unix timestamp → 'HH:MM:SS' (today) or 'YYYY-MM-DD HH:MM:SS' (older)."""
    if ts is None:
        return None
    import datetime as _dt
    try:
        dt  = _dt.datetime.fromtimestamp(ts)
        now = _dt.datetime.now()
        return (dt.strftime("%H:%M:%S") if dt.date() == now.date()
                else dt.strftime("%Y-%m-%d %H:%M:%S"))
    except (ValueError, OSError):
        return None


def _job_to_dict(job, brief: bool = False) -> dict:
    pct      = int(100 * job.step_done / job.step_count) if job.step_count else 0
    progress = f"{job.step_done}/{job.step_count}"
    if job.status == "RUNNING":
        progress += f" ({pct}%)"

    d: dict = {
        "job_id":     job.job_id,
        "owner":      job.owner,
        "label":      job.label,
        "status":     job.status,
        "progress":   progress,
        "step_done":  job.step_done,
        "step_count": job.step_count,
        "submitted":  _fmt_ts(job.submitted_at),
    }
    if job.completed_at:
        d["completed"] = _fmt_ts(job.completed_at)
        if job.submitted_at:
            d["elapsed_s"] = round(job.completed_at - job.submitted_at, 1)
    if job.error:
        d["error"] = job.error
    errs = getattr(job, "step_errors", [])
    if brief:
        if errs:
            d["step_errors"] = len(errs)   # count only in list view
    else:
        # Full detail for job.stat
        d["step_errors"]  = errs
        d["fail_fast"]    = getattr(job, "fail_fast", True)
        d["tx_id"]        = job.tx_id
        d["submitted_at"] = job.submitted_at
        d["completed_at"] = job.completed_at
        # B10 — the LLM cost ledger, filled at settle (0 for a job that used no LLM calls).
        if getattr(job, "api_calls", 0) or getattr(job, "tokens_est", 0) or getattr(job, "wall_s", 0.0):
            d["api_calls"]  = getattr(job, "api_calls", 0)
            d["tokens_est"] = getattr(job, "tokens_est", 0)
            d["wall_s"]     = getattr(job, "wall_s", 0.0)
    return d


