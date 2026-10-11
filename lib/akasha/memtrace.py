"""
F49-2 — native-load RSS accounting.

The unattributed +2-3 GB boot climb is native (invisible to MemTop's Python-container walk): a
LITERT/TFLite model load, a numpy/BLAS allocation, a spaCy model, or an mmap of a multi-GB file.
`native_load(name)` wraps such an entry point and logs ONE line — `[NativeLoad] what=<name>
Δrss=<MB> t=<s>` — so each known native surface's contribution is named directly in the log,
independent of tracemalloc (which only sees Python allocations). Stdlib-only, negligible cost, never
raises out of the context.
"""
import logging
import time
from contextlib import contextmanager

logger = logging.getLogger("Akasha.NativeLoad")


def _rss_mb():
    try:
        with open("/proc/self/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) // 1024
    except (OSError, ValueError, IndexError):
        pass
    return None


def smaps_rollup():
    """(anon_MB, file_map_MB) from /proc/self/smaps_rollup, or (None, None) off-Linux. Anon = heap /
    arena / anonymous mmap; file_map = Rss − Anon = mapped files. The heart's per-minute line and the
    store's open line read the same split from here."""
    _rss = _anon = None
    try:
        with open("/proc/self/smaps_rollup") as _f:
            for _line in _f:
                if _line.startswith("Rss:"):
                    _rss = int(_line.split()[1]) // 1024
                elif _line.startswith("Anonymous:"):
                    _anon = int(_line.split()[1]) // 1024
    except (OSError, ValueError, IndexError):
        return None, None
    if _rss is None or _anon is None:
        return _anon, None
    return _anon, max(0, _rss - _anon)


def malloc_trim() -> bool:
    """A58 — return freed heap arenas to the OS (glibc `malloc_trim(0)`), so a nightly sweep's transient
    allocations do not become the process's permanent RSS floor (Python frees to the allocator, not the
    OS). Linux/glibc only; a no-op (returns False) elsewhere. Never raises."""
    try:
        import ctypes
        libc = ctypes.CDLL("libc.so.6", use_errno=False)
        libc.malloc_trim(0)
        return True
    except Exception:
        return False


def gc_trim():
    """A58 — gc.collect() + malloc_trim(0); returns (Δrss_MB or None, trimmed_bool). The Δrss is the RSS
    the trim actually returned to the OS (negative = freed). Used after a maintenance sweep / the nightly
    sequence to log `[maint] trim Δrss=<MB>` — if the retained figure drops, the arena was the holder."""
    import gc as _gc
    r0 = _rss_mb()
    _gc.collect()
    trimmed = malloc_trim()
    r1 = _rss_mb()
    dr = round(r1 - r0, 1) if (r0 is not None and r1 is not None) else None
    return dr, trimmed


@contextmanager
def native_load(name: str, min_delta_mb: int = 1):
    """Log the RSS delta across a native allocation site. Only emits when Δrss ≥ min_delta_mb (default
    1 MB) so trivial calls stay quiet; a big load names itself. Best-effort — the wrapped work runs
    even if the /proc read fails, and the log never masks an exception from the body."""
    before = _rss_mb()
    t0 = time.time()
    try:
        yield
    finally:
        after = _rss_mb()
        try:
            if before is not None and after is not None:
                d = after - before
                if d >= min_delta_mb:
                    logger.warning("[NativeLoad] what=%s Δrss=%dMB t=%.2fs (rss %d→%d)",
                                   name, d, time.time() - t0, before, after)
        except Exception:
            pass
