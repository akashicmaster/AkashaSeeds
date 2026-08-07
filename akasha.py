#!/usr/bin/env python3
"""
Akasha — Single Entry Point.

  python akasha.py                        → httpd (background) + CLI
  python akasha.py --server uvicorn       → uvicorn/FastAPI (background) + CLI
  python akasha.py --host 0.0.0.0         → bind to all interfaces
  python akasha.py --port 8080            → specific port
  python akasha.py --stdio                → CLI only, no web portal
  python akasha.py <cmd…>                 → headless single-shot then exit
  (CGI env detected)                      → CGI handler
"""

import sys
import os

# ── 1. Python version guard ────────────────────────────────────────────────────
if sys.version_info < (3, 8):
    sys.stderr.write("[!] FATAL: Akasha requires Python 3.8 or higher.\n")
    sys.exit(1)

# ── 2. CGI stdout protection ───────────────────────────────────────────────────
_is_cgi = "GATEWAY_INTERFACE" in os.environ or "REQUEST_METHOD" in os.environ
_original_stdout = None
if _is_cgi:
    _original_stdout = sys.stdout
    sys.stdout = sys.stderr

# ── 3. Absolute path anchor ────────────────────────────────────────────────────
_root = os.path.dirname(os.path.abspath(__file__))
if _root not in sys.path:
    sys.path.insert(0, _root)

# Hosted-Python guard (Pyto/Pythonista on iPad, embedded interpreters): the host may resolve a
# top-level `lib` / `api` / … to ITS OWN module — a cached sys.modules entry from the host's
# startup, a custom meta-path importer, or (iOS is case-insensitive) a filesystem match to the
# host's `Lib/` — so `from lib.akasha…` dies with "'lib' is not a package". Inserting our root at
# sys.path[0] does NOT win against a cached entry or a meta-path importer, and evicting is not
# enough if an importer re-resolves it. So: EVICT any stale entry not under our root, then
# explicitly PIN our own package into sys.modules bound to our root, so every later
# `import lib.<x>` resolves to our tree regardless of the host's import machinery. No-op on a
# normal machine (there our package is already the one that would load).
import importlib.util as _ilu
for _pkg in ("lib", "api", "services", "remote", "env"):
    _own_init = os.path.join(_root, _pkg, "__init__.py")
    _cached   = sys.modules.get(_pkg)
    _cf       = getattr(_cached, "__file__", None) if _cached is not None else None
    _is_ours  = bool(_cf) and os.path.abspath(_cf) == _own_init
    if _cached is not None and not _is_ours:                 # evict the foreign package + subs
        for _m in [m for m in sys.modules if m == _pkg or m.startswith(_pkg + ".")]:
            del sys.modules[_m]
        _cached = None
    if _cached is None and os.path.isfile(_own_init):        # pin ours so no importer can shadow it
        try:
            _spec = _ilu.spec_from_file_location(
                _pkg, _own_init, submodule_search_locations=[os.path.join(_root, _pkg)])
            _mod = _ilu.module_from_spec(_spec)
            sys.modules[_pkg] = _mod
            _spec.loader.exec_module(_mod)
        except Exception:
            sys.modules.pop(_pkg, None)                        # leave it to the normal machinery


def _is_ios() -> bool:
    """True on iOS/iPadOS hosts (a-Shell, Pyto, Pythonista). These sandboxes forbid the Cell
    daemon's process model — spawning a subprocess raises EBADF and binding a Unix domain socket
    raises EPERM — so Akasha must run as ONE embedded process (no daemon, no socket, no portal
    subprocess). `platform.machine()` is the reliable signal (e.g. 'iPad14,1'); `platform.system()`
    may report 'Darwin' or 'iOS' depending on the host."""
    try:
        import platform
        if platform.system().lower() in ("ios", "ipados", "iphoneos"):
            return True
        return platform.machine().lower().startswith(("ipad", "iphone", "ios"))
    except Exception:
        return False


# ── 4. Infrastructure provisioning ────────────────────────────────────────────

def _ensure_dirs(root: str) -> None:
    for rel in [
        "data", "data/cells", "data/central",
        "data/import", "data/export",
        "env/models", "logs", "assets",
    ]:
        os.makedirs(os.path.join(root, rel), exist_ok=True)


# ── 5. Logging ────────────────────────────────────────────────────────────────

_FAULT_FILE = None       # kept open for process life so faulthandler can write during a crash


def _enable_faulthandler(root: str) -> None:
    """Capture FATAL native crashes that leave NO Python traceback. A detached Cell daemon that
    dies mid-weave from a C-level fault (segfault / abort / bus error) otherwise vanishes silently
    — the log just stops, which is exactly the 'daemon self-destructs, no trace' symptom. Python's
    stdlib faulthandler dumps every thread's stack to a persistent file on SIGSEGV/SIGABRT/SIGFPE/
    SIGBUS/SIGILL, so the crash location survives the death and the next launch can show it. Near
    zero overhead; never fatal to enable. Akasha diagnoses its own fatal crashes — the operator is
    never left with an empty log."""
    global _FAULT_FILE
    if _FAULT_FILE is not None:
        return
    try:
        import faulthandler
        os.makedirs(os.path.join(root, "logs"), exist_ok=True)
        _FAULT_FILE = open(os.path.join(root, "logs", "faulthandler.log"), "a", buffering=1)
        _FAULT_FILE.write(f"\n=== faulthandler armed (pid {os.getpid()}) ===\n")
        _FAULT_FILE.flush()
        faulthandler.enable(file=_FAULT_FILE, all_threads=True)
    except Exception:
        pass


def _setup_logging(root: str, is_cgi: bool) -> None:
    import logging
    _enable_faulthandler(root)
    # Attach the system.log handler to the ROOT logger, not just "Harmonia".
    # Every subsystem uses its own named logger ("Akasha.Kernel", "Akasha.Vision",
    # "Harmonia", …). If the file handler lives only on "Harmonia", the sibling
    # "Akasha.*" trees have NO handler that reaches system.log — so all their INFO
    # output (the `[Kernel]` load lines, the `[BootWatch]` memory heartbeat, the
    # autolearn/weave gate decisions) is silently discarded, and `grep … system.log`
    # comes back empty even though the code ran. That gap masked a multi-day boot-crash
    # diagnosis (BootWatch was firing the whole time, into the void). Configuring the
    # root logger makes EVERY subsystem land in one file, tagged by %(name)s.
    rootlog = logging.getLogger()
    if any(getattr(h, "_akasha_syslog", False) for h in rootlog.handlers):
        return
    # Root at INFO filters third-party DEBUG spam (asyncio/urllib3/…) at the source
    # logger; our own trees are pinned to DEBUG below so their detail still passes.
    rootlog.setLevel(logging.INFO)

    # File-log level defaults to INFO (all the diagnostics — [BootWatch], [Kernel] load lines,
    # [Supervisor], the autolearn/weave gate decisions — are INFO). DEBUG is opt-in via
    # AKASHA_LOG_LEVEL=DEBUG. This is a DISK-SAFETY default: a full weave emits per-word DEBUG in
    # the hundreds of thousands (e.g. one line per proto-word, and — before it was fixed — one per
    # failed link write), which at DEBUG-to-disk produced a ~100 MB system.log that can fill a tight
    # VPS disk and take the single writer down. Handler-level filtering drops DEBUG at the sink, so
    # loggers may still be DEBUG-capable for an attached debugger without flooding the file.
    _lvl = getattr(logging, os.environ.get("AKASHA_LOG_LEVEL", "INFO").strip().upper(), logging.INFO)
    fh = logging.FileHandler(os.path.join(root, "logs", "system.log"), encoding="utf-8")
    fh.setLevel(_lvl)
    fh.setFormatter(logging.Formatter(
        "%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s"
    ))
    fh._akasha_syslog = True          # idempotence marker (avoid duplicate handlers on re-call)
    rootlog.addHandler(fh)

    # Loggers stay at _lvl too (so DEBUG records aren't even constructed at INFO — cheaper).
    logging.getLogger("Harmonia").setLevel(_lvl)
    logging.getLogger("Akasha").setLevel(_lvl)

    if not is_cgi:
        ch = logging.StreamHandler(sys.stderr)
        ch.setLevel(logging.WARNING)
        ch.setFormatter(logging.Formatter(
            "\033[2m[%(name)s]\033[0m %(levelname)s: %(message)s"
        ))
        ch._akasha_syslog = True
        rootlog.addHandler(ch)


# ── 6. Boot progress indicator ────────────────────────────────────────────────

def _boot_spinner(stop_event, stages):
    """Daemon thread: cycling spinner + stage labels while kernel initialises."""
    import time
    import itertools

    frames  = itertools.cycle(r'|/-\\')
    current = [stages[0]]
    idx     = [0]

    def _advance():
        idx[0] = min(idx[0] + 1, len(stages) - 1)
        current[0] = stages[idx[0]]

    stop_event.advance = _advance

    while not stop_event.is_set():
        sys.stdout.write(f"\r  {next(frames)}  {current[0]}  ")
        sys.stdout.flush()
        time.sleep(0.12)

    sys.stdout.write("\r" + " " * 60 + "\r")
    sys.stdout.flush()


# ── 7. Port helper ────────────────────────────────────────────────────────────

def _free_port(start: int = 8000, host: str = "127.0.0.1") -> int:
    import socket
    for p in range(start, 65535):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex((host, p)) != 0:
                return p
    return start


# Cmdline signatures of the processes Akasha manages: the Cell daemon (`akasha.py --daemon`)
# and the serve-only web portal (`api.portals.web_worker` / `services.http_portal`).
_AKASHA_PROC_TOKENS = ("akasha", "api.portals.web_worker", "services.http_portal")


def _pid_is_akasha_process(pid: int) -> bool:
    """True iff `pid` is a live process whose /proc cmdline is one of ours (Cell daemon or a
    serve-only portal). The anti-recycle guard for every signal path: after a crash the OS can
    reassign a recorded pid to an unrelated process, so a blind kill would hit a stranger.
    Returns False where /proc is unavailable (non-Linux) — callers then skip the kill and
    degrade safely (the socket/flock guards still prevent two writers)."""
    try:
        with open(f"/proc/{int(pid)}/cmdline", "rb") as fh:
            cmd = fh.read().replace(b"\x00", b" ").decode("utf-8", "replace").lower()
    except (OSError, ValueError):
        return False
    return any(tok in cmd for tok in _AKASHA_PROC_TOKENS)


def _stop_recorded_portal(pid_path: str, wait: bool = True, grace_ticks: int = 40):
    """Stop a previously-detached process recorded in *pid_path* (web portal or Cell
    daemon).

    A public deploy leaves its portal/daemon running on `exit` (so the site stays up
    after you disconnect). Re-running `akasha.py` must therefore REPLACE it, not
    collide on the port — so boot calls this to cleanly stop the old one first.
    The operator never has to kill a process by hand. Returns the PID stopped, or
    None if nothing was running.

    grace_ticks × 0.1s is how long we wait for a graceful SIGTERM exit before SIGKILL.
    The Cell daemon is the single WRITER: on stop it finishes the in-flight write and
    checkpoints the WAL (can take ~10s+ mid-load), so it is given a generous grace —
    SIGKILLing it mid-checkpoint is exactly the crash we are engineered to avoid. A
    serve-only web portal holds no write and keeps the short default.
    """
    import time as _t
    try:
        with open(pid_path) as f:
            pid = int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return None
    # Never signal SELF. The portal's own self-watchdog (R5) reaches here via
    # _spawn_cell_daemon → _reap_stale_local → _stop_recorded_portal(web-portal.pid), and that
    # file records the watchdog's OWN pid — SIGTERM-ing it would kill the recovery mid-flight
    # (the spawn is never reached → daemon AND portal both gone, worse than the wedge it was
    # healing). _reap_leaked_portals already self-excludes (keep | {os.getpid()}); mirror that
    # here so every caller is safe. The fresh daemon we spawn reaps this old portal itself.
    if pid == os.getpid():
        return None
    # Anti-recycle guard: the recorded process may be long dead and its pid reassigned by the
    # OS to an unrelated process (common on a long-lived server after a crash). Signalling that
    # number blind would kill a stranger. Verify the pid is genuinely one of ours (Cell daemon
    # or serve-only portal, by /proc cmdline) BEFORE any signal — the same guard _reap_stale_daemon
    # / _daemon_process_alive already apply. A foreign/gone pid → drop the stale file, kill nothing.
    if not _pid_is_akasha_process(pid):
        try: os.remove(pid_path)
        except OSError: pass
        return None
    try:
        os.kill(pid, 15)                       # SIGTERM — graceful
    except ProcessLookupError:
        try: os.remove(pid_path)
        except OSError: pass
        return None
    except PermissionError:
        return None
    if wait:                                    # let it release the port, then be firm
        for _ in range(grace_ticks):
            _t.sleep(0.1)
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                break
        else:
            try: os.kill(pid, 9)               # SIGKILL if it won't go
            except ProcessLookupError: pass
    try: os.remove(pid_path)
    except OSError: pass
    return pid


def _terminate_pid(pid: int, wait: bool = True, grace_ticks: int = 40) -> bool:
    """SIGTERM (then SIGKILL if it won't go within grace_ticks×0.1s) a pid. True if signalled.
    A writer daemon needs a longer grace than a portal so it can checkpoint before the SIGKILL —
    pass a larger grace_ticks for those (e.g. 500 ≈ 50s)."""
    import time as _t
    try:
        os.kill(pid, 15)
    except (ProcessLookupError, PermissionError):
        return False
    if wait:
        for _ in range(max(1, grace_ticks)):
            _t.sleep(0.1)
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                return True
        try: os.kill(pid, 9)
        except ProcessLookupError: pass
    return True


def akasha_build_stamp(root: str = None) -> dict:
    """The build identity shown at boot / install so seed freshness is visible at a glance.

    Two sources, in order of authority:
      1. LIVE git (a dev clone or a `git pull` deploy) — the real HEAD of this tree,
         so a stale checkout is obvious. `dirty` flags uncommitted edits.
      2. The baked `akasha_build.json` (a seed install — no .git present), written by
         the crystallizer from the commit the seed was built on.
    Returns {} if neither is available. Never raises."""
    import json as _json, subprocess as _sub
    root = root or _root
    # 1. Live git — authoritative for a repo checkout.
    try:
        _g = ["git", "-C", root]
        commit = _sub.check_output(_g + ["rev-parse", "HEAD"],
                                   stderr=_sub.DEVNULL, timeout=3).decode().strip()
        cdate = _sub.check_output(_g + ["show", "-s", "--format=%cI", "HEAD"],
                                  stderr=_sub.DEVNULL, timeout=3).decode().strip()
        dirty = _sub.call(_g + ["diff", "--quiet", "--", ".",
                                ":(exclude)akasha_seeds_*.py", ":(exclude)akasha_build.json"],
                          stdout=_sub.DEVNULL, stderr=_sub.DEVNULL, timeout=3) != 0
        if commit:
            return {"commit": commit, "commit_short": commit[:10], "commit_date": cdate,
                    "dirty": dirty, "source": "git",
                    "series": os.environ.get("AKASHA_SERIES", "")}
    except Exception:
        pass
    # 2. Baked stamp — a seed install has no git, so read what the crystallizer wrote.
    try:
        with open(os.path.join(root, "akasha_build.json"), encoding="utf-8") as _fh:
            b = dict(_json.load(_fh)); b.setdefault("source", "seed"); return b
    except Exception:
        return {}


def _format_build_stamp(b: dict) -> str:
    """One-line human form: 'seeds12 · main a1b2c3d4e5 (git, 2026-07-31) [modified]'."""
    if not b:
        return "build: unknown (no git, no akasha_build.json)"
    series = b.get("series") or os.environ.get("AKASHA_SERIES", "") or "dev"
    short  = b.get("commit_short") or (b.get("commit") or "")[:10] or "?"
    date   = (b.get("commit_date") or "")[:10]
    src    = b.get("source", "?")
    tail   = f"{src}" + (f", {date}" if date else "")
    dirty  = " [modified]" if b.get("dirty") else ""
    return f"{series} · main {short} ({tail}){dirty}"


def _port_in_use(host: str, port: int) -> bool:
    """True if something is already LISTENing on host:port."""
    import socket
    probe = "127.0.0.1" if host in ("0.0.0.0", "::", "") else host
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.6)
        try:
            return s.connect_ex((probe, port)) == 0
        except OSError:
            return False


def _free_orphan_akasha_port(port: int):
    """If an orphaned Akasha portal (one not in the pid file — e.g. a detached
    portal still running after `rm -r *`) is holding *port*, stop it. Foreign
    processes are left alone. Returns the pid stopped, or None."""
    if not _port_in_use("127.0.0.1", port):
        return None
    pid, cmd = _port_holder(port)
    if pid and ("web_worker" in cmd or "akasha" in cmd):
        _terminate_pid(pid)
        import time as _t
        _t.sleep(0.3)
        return pid
    return None


def _wait_port_bindable(host: str, port: int, timeout: float = 12.0) -> bool:
    """Block until host:port can actually be BOUND (not merely until a connect probe
    finds nothing answering — a just-stopped portal can leave the port briefly held /
    in TIME_WAIT, which `_port_in_use` misses but a real bind hits with EADDRINUSE).
    Test-binds with SO_REUSEADDR (what the worker uses), so a success means the worker's
    bind will succeed too. Returns True once bindable, False on timeout. This restores the
    port-release grace the old pre-launch load-wait used to provide incidentally, without
    the multi-minute wait — it returns immediately when the port is already free."""
    import socket, time as _t
    bind_host = host if host not in ("", None) else "0.0.0.0"
    deadline = _t.time() + timeout
    while True:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((bind_host, port))
            s.close()
            return True
        except OSError:
            s.close()
            if _t.time() >= deadline:
                return False
            _t.sleep(0.3)


def _port_holder(port: int):
    """Best-effort (Linux /proc): (pid, cmdline) of the process LISTENing on
    *port*, or (None, "") if it can't be determined (non-Linux, race, perms)."""
    try:
        inodes = set()
        for proto in ("tcp", "tcp6"):
            p = f"/proc/net/{proto}"
            if not os.path.exists(p):
                continue
            with open(p) as f:
                next(f, None)
                for line in f:
                    c = line.split()
                    if len(c) > 9 and c[3] == "0A":          # 0A = LISTEN
                        if int(c[1].rsplit(":", 1)[-1], 16) == port:
                            inodes.add(c[9])
        if not inodes:
            return (None, "")
        for pid in os.listdir("/proc"):
            if not pid.isdigit():
                continue
            try:
                for fd in os.listdir(f"/proc/{pid}/fd"):
                    try:
                        tgt = os.readlink(f"/proc/{pid}/fd/{fd}")
                    except OSError:
                        continue
                    if tgt.startswith("socket:[") and tgt[8:-1] in inodes:
                        try:
                            with open(f"/proc/{pid}/cmdline", "rb") as cf:
                                cmd = cf.read().replace(b"\x00", b" ").decode(
                                    "utf-8", "replace").strip()
                        except OSError:
                            cmd = ""
                        return (int(pid), cmd)
            except OSError:
                continue
    except Exception:
        pass
    return (None, "")


def _akasha_portal_pids(base_dir: str):
    """(pid, cmdline) for every RUNNING Akasha web-portal subprocess bound to THIS data dir.
    Matched on the serve-only portal module (`api.portals.web_worker` / `services.http_portal`)
    AND the `--data <base_dir>` arg in its cmdline, so it can NEVER match a foreign server or a
    portal of a *different* Akasha cell on the same host — the data dir is the discriminator.
    Linux /proc only; returns [] elsewhere (best-effort cleanup, never fatal)."""
    out = []
    base_abs = os.path.abspath(base_dir)
    try:
        pids = [p for p in os.listdir("/proc") if p.isdigit()]
    except OSError:
        return out
    me = os.getpid()
    for pid_s in pids:
        pid = int(pid_s)
        if pid == me:
            continue
        try:
            with open(f"/proc/{pid_s}/cmdline", "rb") as fh:
                cmd = fh.read().replace(b"\x00", b" ").decode("utf-8", "replace")
        except OSError:
            continue
        is_portal = ("api.portals.web_worker" in cmd or "services.http_portal" in cmd)
        for_this_dir = (base_abs in cmd) or (f"--data {base_dir} " in cmd + " ")
        if is_portal and for_this_dir:
            out.append((pid, cmd.strip()))
    return out


_BUILD_ID_CACHE = {}

def _code_build_id(root: str) -> str:
    """A content fingerprint of the running backend code. STABLE across an identical
    re-extract (so a plain re-run fast-attaches to the daemon, no ontology reload) but
    DIFFERENT whenever any source byte changes (so a re-extracted/updated build makes the
    launcher replace a stale daemon instead of running new tests on old code — the dive-apple
    'seed is new but the running writer is old' bug). Hashes the CONTENT of akasha.py + every
    .py under lib/ and api/ (the behaviour-defining tree); __pycache__ is skipped. Computed
    once per process (~tens of ms) and cached. Never raises — an unreadable tree returns ''."""
    cached = _BUILD_ID_CACHE.get(root)
    if cached is not None:
        return cached
    import hashlib
    h = hashlib.sha256()
    files = []
    top = os.path.join(root, "akasha.py")
    if os.path.isfile(top):
        files.append(top)
    for sub in ("lib", "api"):
        d = os.path.join(root, sub)
        if not os.path.isdir(d):
            continue
        for dirpath, dnames, fnames in os.walk(d):
            if "__pycache__" in dirpath:
                continue
            dnames[:] = [x for x in dnames if x != "__pycache__"]
            for fn in fnames:
                if fn.endswith(".py"):
                    files.append(os.path.join(dirpath, fn))
    for p in sorted(files):
        try:
            with open(p, "rb") as fh:
                data = fh.read()
        except OSError:
            continue
        h.update(os.path.relpath(p, root).encode("utf-8", "replace"))
        h.update(b"\0")
        h.update(data)
        h.update(b"\0")
    bid = h.hexdigest()[:16]
    _BUILD_ID_CACHE[root] = bid
    return bid


def _resolve_build_id(root: str) -> str:
    """The build id to advertise/compare: an operator/seed-supplied AKASHA_BUILD_ID wins (a
    seed may stamp its own payload fingerprint), else the on-disk code fingerprint."""
    return (os.environ.get("AKASHA_BUILD_ID") or "").strip() or _code_build_id(root)


_HELD_BOOT_LOCK = None   # keeps the boot-lock fd alive for this process's lifetime


# ── Boot-progress heartbeat (R4) ────────────────────────────────────────────────
# A booting daemon touches this file every few seconds. Convergence then distinguishes a
# HEALTHY-but-slow boot (heartbeat FRESH → keep waiting, NEVER reap) from a genuinely WEDGED
# process (heartbeat stale/absent AND not answering sys.ping → reap + respawn). This removes the
# fixed-ceiling false-positive of RC4 — a B-scale nucleus load on a slow VPS disk no longer risks
# being reaped as "hung" while it is legitimately still binding its socket. The file exists ONLY
# during boot: once the IPC socket answers, sys.ping is the liveness signal and the file is cleared,
# so "heartbeat fresh" is an exact synonym for "actively booting".
_BOOT_HEARTBEAT_STALE_S = float(os.environ.get("AKASHA_BOOT_HEARTBEAT_STALE", "").strip() or 20)

def _boot_heartbeat_path(base_dir: str) -> str:
    return os.path.join(base_dir, "central", "boot.heartbeat")

def _boot_heartbeat_touch(base_dir: str) -> None:
    p = _boot_heartbeat_path(base_dir)
    try:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as fh:
            fh.write(str(os.getpid()))
    except OSError:
        pass

def _boot_heartbeat_age(base_dir: str):
    """Seconds since the boot heartbeat was last written, or None if absent/unreadable."""
    import time as _t
    try:
        return max(0.0, _t.time() - os.path.getmtime(_boot_heartbeat_path(base_dir)))
    except OSError:
        return None

def _boot_heartbeat_fresh(base_dir: str, stale_s: float = _BOOT_HEARTBEAT_STALE_S) -> bool:
    """True only while a daemon is actively touching the heartbeat (a live, progressing boot)."""
    age = _boot_heartbeat_age(base_dir)
    return age is not None and age <= stale_s

def _boot_heartbeat_clear(base_dir: str) -> None:
    try:
        os.remove(_boot_heartbeat_path(base_dir))
    except OSError:
        pass

def _run_boot_heartbeat(base_dir: str, stop_event) -> None:
    """Touch the boot heartbeat every few seconds until boot completes (stop_event set) or the
    process dies. A wedged interpreter (GIL deadlock) or a stalled disk stops the touches, so a
    stale heartbeat is exactly the 'wedged, not merely slow' signal convergence needs."""
    _boot_heartbeat_touch(base_dir)
    while not stop_event.wait(3.0):
        _boot_heartbeat_touch(base_dir)


def _acquire_boot_lock(base_dir: str):
    """Exclusive, non-blocking per-data-dir BOOT LOCK. Only one process may load a given
    nucleus at a time — two daemons booting the SAME data dir concurrently is two writers into
    one nucleus (the single-writer violation), which corrupts/kills the load. The ping-based
    singleton guard cannot catch this: during the multi-second ontology-load window the IPC
    socket is not bound yet, so BOTH concurrent cold boots see 'no daemon answering' and proceed.
    An advisory `flock` closes that window — the second concurrent boot fails to acquire and
    defers. Crash-stop friendly: the lock is an open fd, so the OS releases it automatically when
    the holder exits for ANY reason (clean exit, SIGKILL, OOM) — a crashed daemon never leaves a
    stuck lock. Returns the held fd (keep it referenced for the process lifetime) or None if
    another process already holds it. Degrades to 'no lock' (returns a sentinel truthy fd) where
    fcntl is unavailable (non-POSIX) so it never blocks a legitimate boot."""
    try:
        import fcntl
    except Exception:
        return -1                                    # no flock here (non-POSIX) → do not gate
    lock_path = os.path.join(base_dir, "central", "cell.boot.lock")
    try:
        os.makedirs(os.path.dirname(lock_path), exist_ok=True)
        fd = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
    except OSError:
        return -1                                    # cannot create the lock file → do not gate
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        os.close(fd)
        return None                                  # another process holds it → caller defers
    try:
        os.ftruncate(fd, 0)
        os.write(fd, str(os.getpid()).encode())
    except OSError:
        pass
    return fd


def _reap_stale_daemon(base_dir: str, grace_ticks: int = 500):
    """Stop a stale/HUNG predecessor Cell daemon recorded in cell.pid so a replacement binds a
    clean socket — Akasha cleans up after itself; the user is NEVER asked to kill/pkill. Covers
    the case a dead-pid check misses: a daemon alive but not answering (hung on the GIL, wedged
    mid-shutdown) still passes `kill -0`, so 'no ping answer' must not be read as 'already gone'.
    The recorded pid is verified to still be an akasha process (its /proc cmdline) BEFORE it is
    signalled, so a recycled unrelated pid is never touched. Generous grace (≈50s) lets the
    writer checkpoint. Returns the pid stopped, or None."""
    try:
        with open(_cell_pid_path(base_dir)) as fh:
            pid = int((fh.read() or "0").strip() or 0)
    except (OSError, ValueError):
        return None
    if not pid or pid == os.getpid():
        return None
    try:                                            # confirm it is really our daemon (anti-recycle)
        with open(f"/proc/{pid}/cmdline", "rb") as fh:
            cmd = fh.read().replace(b"\x00", b" ").decode("utf-8", "replace")
    except OSError:
        return None                                 # pid gone or /proc unavailable → nothing to do
    if "akasha" not in cmd.lower():
        return None                                 # pid was recycled by an unrelated process
    return pid if _terminate_pid(pid, grace_ticks=grace_ticks) else None


def _daemon_process_alive(base_dir: str):
    """Return the PID of a LIVE Cell-daemon process recorded in cell.pid — INCLUDING one that is
    still mid-boot (its IPC socket not bound yet, so `cell_ipc.ping` fails). Verifies the recorded
    pid is genuinely a live akasha `--daemon` process (its /proc cmdline) so a recycled or foreign
    pid is never mistaken for our daemon. Returns the pid, or None if no live daemon process exists.

    This is the distinction the reconnecting CLI needs: 'a daemon is BOOTING, wait for it' vs 'no
    daemon, spawn one'. Without it, an SSH reconnect that pings a mid-boot daemon (no socket yet)
    reads 'no daemon' and spawns/reaps a SECOND — the perpetual restart loop the user reported
    ('起動→抜けて→起動し直し'). Process management is entirely code-side; the user is never asked to
    inspect or kill anything. /proc-based (Linux) — returns None where /proc is unavailable, which
    degrades safely to the spawn path (the socket/flock guards still prevent two writers there)."""
    try:
        with open(_cell_pid_path(base_dir)) as fh:
            pid = int((fh.read() or "0").strip() or 0)
    except (OSError, ValueError):
        return None
    if not pid or pid == os.getpid():
        return None
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as fh:
            cmd = fh.read().replace(b"\x00", b" ").decode("utf-8", "replace")
    except OSError:
        return None                                 # pid gone or /proc unavailable
    low = cmd.lower()
    if "akasha" not in low or "--daemon" not in low:
        return None                                 # recycled/foreign pid, or not a Cell daemon
    return pid


def _reap_stale_local(base_dir: str, quiet: bool = True) -> int:
    """The `stop` collection, folded into the START path so a plain `python akasha.py` (or a seed
    re-extract) is SELF-SUFFICIENT — the operator never needs a separate `python akasha.py stop`
    first. Process management is the code's job, not two commands the user has to remember.

    Called only when NO healthy daemon is being attached to (cold start, or after a hung/mismatched
    daemon was cleared), so reaping is always safe — it never touches a daemon a client is about to
    attach to. Collects, in order: a stale/hung recorded Cell daemon (dead pid → no-op; hung →
    SIGTERM then SIGKILL), a stale recorded web portal, and EVERY orphaned portal for this data dir
    (re-parented to init when its daemon crashed, still holding its port + ~1 GB RAM — the leak an
    operator used to have to pkill). Returns the count reaped. Never raises."""
    reaped = 0
    try:
        if _stop_recorded_portal(_cell_pid_path(base_dir), grace_ticks=400):
            reaped += 1
        if _stop_recorded_portal(os.path.join(base_dir, "web-portal.pid")):
            reaped += 1
        _orphans = _reap_leaked_portals(base_dir)
        reaped += len(_orphans or [])
        if reaped and not quiet:
            print(f"  [~] Cleaned {reaped} leftover process(es) from a prior run "
                  f"(no `stop` needed).", flush=True)
    except Exception as _exc:
        logging.getLogger("Harmonia.Boot").debug("[reap] pre-spawn cleanup: %s", _exc)
    return reaped


def _wait_for_daemon_socket(base_dir: str, deadline_s: float = None) -> bool:
    """Block until an alive-but-booting Cell daemon binds its socket and answers sys.ping. Returns
    True as soon as one answers; False if the booting daemon dies, or goes WEDGED (boot heartbeat
    stale AND still no ping) — the caller then reaps + respawns.

    Heartbeat-gated (R4): while the boot heartbeat is FRESH the daemon is progressing, so it is
    NEVER timed out — this removes the RC4 false-positive of reaping a healthy-but-slow B-scale
    load on a slow VPS disk. The fixed ceiling (AKASHA_BOOT_WAIT, default 90 s) applies only as a
    fallback when no heartbeat file exists (an older daemon build that predates the heartbeat)."""
    import time as _t
    from api.portals import cell_ipc
    if deadline_s is None:
        deadline_s = float(os.environ.get("AKASHA_BOOT_WAIT", "").strip() or 90)
    end = _t.time() + deadline_s
    while True:
        if cell_ipc.ping(base_dir, timeout=2.0):
            return True
        if _daemon_process_alive(base_dir) is None:
            return False                            # it died while booting → caller respawns
        if _boot_heartbeat_fresh(base_dir):
            _t.sleep(0.5)                           # progressing boot → wait, no ceiling-kill
            continue
        # No fresh heartbeat → either an old daemon (no file) or a wedged one. Honour the fixed
        # ceiling as a fallback; once it passes, report 'not answering' so the caller reaps.
        if _t.time() >= end:
            return False
        _t.sleep(0.5)


def _converge_daemon(root: str, base_dir: str, args, *, spawn: bool, quiet: bool = False,
                     wait_ceiling: float = None) -> str:
    """The ONE convergence routine every entry path shares (R1) — the actual fix for "client and
    server paths are not equivalent". From ANY daemon state it drives this data dir toward exactly
    one answering daemon, WITHOUT ever creating a second nucleus writer and WITHOUT ever reaping a
    daemon whose boot heartbeat is fresh. Returns one of:

        "answering" — a daemon answers sys.ping (attach to it).
        "spawned"   — none was answering; a fresh one was spawned and now answers (spawn=True only).
        "gone"      — no answering daemon and none could/should be spawned (spawn=False, or the
                      spawn attempt failed). The caller chooses the exit code / embedded fallback.

    Cases:
      1. A daemon ANSWERS                         → "answering".
      2. A daemon process is ALIVE but not yet answering → WAIT for its socket (heartbeat-gated:
         a fresh-heartbeat boot is never reaped). If it answers → "answering"; if it dies or goes
         wedged (heartbeat stale + no ping) → reap it (never a user pkill) and fall through.
      3. No live daemon process                   → spawn one if spawn=True, else "gone".

    Robust to an abrupt SSH-drop: the detached daemon keeps booting and the next reconnect finds it
    (case 1/2) and attaches instead of piling on a second writer. `quiet` routes status to the log
    (the MCP transport owns stdout — a banner there would corrupt its JSON-RPC stream)."""
    import logging as _lg
    from api.portals import cell_ipc
    log = _lg.getLogger("Harmonia.Boot")

    def _say(msg):
        if quiet:
            log.info("[Cell] %s", msg)
        else:
            print(f"  {msg}", flush=True)

    if cell_ipc.ping(base_dir):
        return "answering"
    alive = _daemon_process_alive(base_dir)
    if alive:
        _say(f"[*] A Cell daemon is starting up (PID {alive}) — attaching once it is ready…")
        if _wait_for_daemon_socket(base_dir, wait_ceiling):
            _say("[+] Cell daemon online.")
            return "answering"
        # Alive but not answering and no fresh boot heartbeat → WEDGED. Clean up after ourselves
        # (the user is never asked to kill/pkill) so a healthy replacement can bind a clean socket.
        if _daemon_process_alive(base_dir) is not None:
            log.warning("[Cell] daemon PID %s is alive but not answering (boot heartbeat stale) — "
                        "reaping the wedged daemon.", alive)
            _reap_stale_daemon(base_dir)
            _reap_leaked_portals(base_dir)
    if not spawn:
        return "gone"
    return "spawned" if _spawn_cell_daemon(root, base_dir, args, quiet=quiet) else "gone"


def _ensure_daemon(root: str, base_dir: str, args, quiet: bool = False) -> bool:
    """Client-path convenience wrapper (interactive CLI, MCP): converge with spawn=True and reduce
    to a bool — True if a daemon is answering (attached or freshly spawned), False if none could be
    brought up (the caller falls back to an embedded engine). All three convergence cases live in
    the shared `_converge_daemon`, so every entry path exercises the SAME logic."""
    return _converge_daemon(root, base_dir, args, spawn=True, quiet=quiet) in ("answering", "spawned")


def _reap_leaked_portals(base_dir: str, keep_pids=()):
    """Stop every Akasha web-portal PROCESS for THIS data dir except `keep_pids` (and self).

    Cleans portals ORPHANED by a crashed Cell daemon: the portal is a detached
    (start_new_session) child, so when the daemon dies the OS never reaps it — it keeps
    running and holding its port. The existing checks only free the ONE currently-configured
    port (+ port 80 for ACME), so a portal left on the OTHER port after an 80↔443 TLS flip, or
    a second leaked instance, survives across restarts and piles up (memory + a port fight that
    shows as the endless 'respawned svc:web-portal (unhealthy)' churn). This sweeps them ALL, on
    any port, scoped strictly to this deployment. Returns the pids stopped.

    Terminates in PARALLEL, not one-at-a-time: a crash-loop can leave a BACKLOG of orphaned
    portals, and reaping them sequentially (SIGTERM + a per-process grace wait each) made boot
    scale with the backlog — the 'startup got much slower' symptom. A portal is serve-only and
    holds NO write state, so it needs no checkpoint grace: SIGTERM them all at once, wait ONE
    short shared window, then SIGKILL any straggler. Total cost is one grace window regardless of
    how many orphans there are."""
    import time as _t
    keep = set(keep_pids) | {os.getpid()}
    targets = [pid for pid, _cmd in _akasha_portal_pids(base_dir) if pid not in keep]
    if not targets:
        return []
    signalled = []
    for pid in targets:                              # phase 1: SIGTERM everyone at once
        try:
            os.kill(pid, 15)
            signalled.append(pid)
        except (ProcessLookupError, PermissionError):
            pass
    for _ in range(20):                              # phase 2: ONE shared ~2s grace window
        if not any(_pid_alive(p) for p in signalled):
            break
        _t.sleep(0.1)
    for pid in signalled:                            # phase 3: SIGKILL any straggler
        if _pid_alive(pid):
            try: os.kill(pid, 9)
            except (ProcessLookupError, PermissionError): pass
    return signalled


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


# ── 7b. Cell daemon / client ────────────────────────────────────────────────────
# Restores the intended topology: the backend is a persistent process (the Cell
# daemon) that OWNS the engine and its jobs; the local CLI is a thin CLIENT that
# attaches over the local IPC socket (TRUST_LOCAL). Closing the CLI never touches
# the daemon's running jobs — the ontology load survives an SSH disconnect the same
# way httpd does, because it lives in a process whose lifetime is independent of the
# shell. Design: docs/for-llm/backend-daemon-local-ipc-spec.md.

def _build_arg_parser():
    """The single source of truth for CLI flags. Built as a module helper so main()
    can parse args EARLY (before deciding whether to build an engine) without
    duplicating the definition."""
    import argparse
    parser = argparse.ArgumentParser(
        description="Akasha Substrate — cognitive knowledge mesh"
    )
    parser.add_argument(
        "--server", metavar="ENGINE",
        nargs="?", const="httpd", default="httpd",
        choices=["httpd", "uvicorn"],
        help="Web server engine: httpd (default) or uvicorn/FastAPI",
    )
    parser.add_argument(
        "--host", default="127.0.0.1",
        help="Web server bind address (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port", type=int, default=None,
        help="Web server port (default: auto-select from 8000)",
    )
    parser.add_argument(
        "--stdio", action="store_true",
        help="CLI only — skip web portal even if available (self-contained, embedded).",
    )
    parser.add_argument(
        "--serve", action="store_true",
        help="Headless server — start the web portal and keep it running; no "
             "interactive CLI. For persistent/detached deployment (VPS, systemd). "
             "Genesis can be performed by a local CLI client over the Cell socket.",
    )
    parser.add_argument(
        "--daemon", action="store_true",
        help="Run as the Cell daemon: own the engine + jobs, serve the local IPC "
             "socket and the web portal, headless. Spawned automatically by the CLI.",
    )
    parser.add_argument(
        "--embedded", action="store_true",
        help="Escape hatch — run the engine in THIS process (old behaviour, no Cell "
             "daemon). Also enabled by AKASHA_EMBEDDED=1.",
    )
    parser.add_argument(
        "--mcp", action="store_true",
        help="Serve the Model Context Protocol over stdio (local route): a JSON-RPC "
             "loop an MCP client (Claude Desktop, a local Ollama agent) spawns as a "
             "subprocess to use Akasha as one client. Attaches to the running Cell "
             "daemon when present (shared memory), else runs embedded. TRUST_LOCAL.",
    )
    parser.add_argument(
        "--portal", metavar="MODE",
        nargs="?", const="archives", default=None,
        help=argparse.SUPPRESS,  # hidden: force a portal mode (e.g. 'archives')
    )
    parser.add_argument(
        "cmd", nargs=argparse.REMAINDER,
        help="Headless single-shot command then exit",
    )
    return parser


def _cell_pid_path(base_dir: str) -> str:
    return os.path.join(base_dir, "central", "cell.pid")


def _recorded_daemon_pid(base_dir: str):
    """The pid recorded in cell.pid (int), or None — regardless of whether it is still alive.
    'A daemon was EXPECTED' (R2) means this file names a pid: a daemon ran on this data dir and
    should be reachable, so an embedded single-shot fallback here must exit non-zero."""
    try:
        with open(_cell_pid_path(base_dir)) as fh:
            pid = int((fh.read() or "0").strip() or 0)
    except (OSError, ValueError):
        return None
    return pid or None


def _supervisor_health_tick(base_dir: str, interval: float = 15.0) -> None:
    """IDLE maintenance loop (P4): periodically health-check every service unit and respawn the
    unhealthy ones per their restart policy. Runs in the Cell daemon (the sole respawner, P3),
    so an on-failure/always service that dies or hangs is brought back without operator action.
    Guarded by the shutdown flag; exits promptly on stop."""
    from lib.akasha import lifecycle as _lc
    from lib.harmonia import supervisor as _sv
    sup = _sv.Supervisor(base_dir)
    while not _lc.wait_or_shutdown(interval):
        try:
            sup.maintain()
        except Exception:                          # a tick must never crash the daemon
            pass


def _onto_load_watcher(gw, base_dir: str) -> None:
    """Mount the ontology load onto the Supervisor plane as `job:onto-load`, so it appears in
    the unified `svc` / units view alongside the service processes. Daemon-side: a read-only
    poll of onto.status mirrored into the run-dir — the kernel hot path is untouched, and the
    Supervisor host (the daemon) reflects job state, which is where it belongs. Exits on
    completion or shutdown."""
    from lib.akasha import lifecycle as _lc
    from lib.harmonia import supervisor as _sv
    while not _lc.is_shutting_down():
        load = None
        try:
            resp = gw.dispatch({"jsonrpc": "2.0", "method": "onto.status",
                                "params": {"client_id": "admin"}, "id": "ontowatch"},
                               "internal")
            if isinstance(resp, dict):
                load = (resp.get("result") or {}).get("load")
        except Exception:
            load = None
        if load:
            state = "complete" if load.get("complete") else "running"
            _sv.record_job(base_dir, "job:onto-load", state, {
                "packs_loaded":  load.get("packs_loaded"),
                "packs_present": load.get("packs_present"),
                "packs_pending": load.get("packs_pending"),
                "atoms":         load.get("atoms"),
            })
            if state == "complete":
                return
        if _lc.wait_or_shutdown(5.0):
            return


def _spawn_cell_daemon(root: str, base_dir: str, args, quiet: bool = False) -> bool:
    """Spawn the Cell daemon detached (its own session, so SSH hangup can't reach it)
    and block until its local socket answers. Returns False on failure so the caller
    can fall back to the embedded (in-process) engine — the CLI must never be left with
    nothing.

    Callers reach this ONLY through `_ensure_daemon`, which has already established there is no
    live daemon to attach to (a genuinely cold start, or a hung predecessor it just reaped). So
    this must NOT reap a daemon of its own — a blind reap here would kill a HEALTHY booting daemon
    on an SSH reconnect (the perpetual restart loop). Concurrent cold boots are made safe by the
    daemon-side flock + socket guards (the second boot DEFERS), not by pre-emptive killing.

    `quiet` routes progress to the log instead of stdout (the MCP transport owns stdout)."""
    import subprocess as _sp, time as _t, logging as _lg
    from api.portals import cell_ipc
    log = _lg.getLogger("Harmonia.Boot")

    def _say(msg):
        if quiet:
            log.info("[Cell] %s", msg)
        else:
            print(f"  {msg}", flush=True)

    # Full pre-spawn collection (same as `stop`): clear a stale/hung daemon record AND every
    # orphaned portal for this data dir, so a plain `python akasha.py` / seed re-extract self-heals
    # any leftover from a prior crash — the operator is NEVER asked to run `stop` first. Safe here:
    # this path is reached only when no healthy daemon is being attached to.
    _reap_stale_local(base_dir, quiet=quiet)

    # Pick the akasha.py entry to re-exec. Must match "akasha.py", NOT any ".py": the R5 portal
    # watchdog reaches here from inside a portal subprocess launched with `-m services.http_portal`
    # (or api.portals.web_worker), so sys.argv[0] is `http_portal.py`/`web_worker.py`. Selecting
    # that as the entry spawned `python http_portal.py --daemon …` → argparse died on the unknown
    # `--daemon` and the daemon never came up (convergence returned "gone"). Falling back to
    # root/akasha.py when argv[0] is not the akasha entry fixes the watchdog re-spawn (B3).
    entry = os.path.abspath(sys.argv[0]) if (sys.argv and sys.argv[0].endswith("akasha.py")) \
        else os.path.join(root, "akasha.py")
    if not os.path.exists(entry):
        entry = os.path.join(root, "akasha.py")

    cmd = [sys.executable, entry, "--daemon"]
    if getattr(args, "server", None):
        cmd += ["--server", args.server]
    if getattr(args, "host", None):
        cmd += ["--host", args.host]
    if getattr(args, "port", None) is not None:
        cmd += ["--port", str(args.port)]
    if getattr(args, "portal", None):
        cmd += ["--portal", args.portal]

    log_path = os.path.join(root, "logs", "cell-daemon.log")
    try:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        fh = open(log_path, "a")
        proc = _sp.Popen(cmd, stdout=fh, stderr=_sp.STDOUT, cwd=root,
                         start_new_session=True)
    except Exception as exc:
        log.error("[Cell] failed to spawn daemon: %s", exc)
        return False

    _say("[*] Starting Cell daemon (backend) — owns the engine and its jobs…")
    # Heartbeat-gated spawn wait (F1 — the R4 gate applied to the ONE loop every spawn goes
    # through; the fixed 45 s ceiling here used to declare a healthy, still-booting B-scale daemon
    # dead). A spawned daemon touches boot.heartbeat every ~3 s from before create_gateway, so a
    # migrate-drain / orphan-scan / IAM-load / one-time-reload window that legitimately exceeds the
    # ceiling is NEVER timed out — we keep waiting while the heartbeat advances. The fallback
    # ceiling (AKASHA_BOOT_WAIT, default 90 s) applies only when there is NO fresh heartbeat (an old
    # daemon build, or the brief pre-touch startup gap). F4: a progress line every ~15 s so a long
    # legitimate wait on a VPS is not mistaken for a hang.
    _ceiling = float(os.environ.get("AKASHA_BOOT_WAIT", "").strip() or 90)
    _end = _t.time() + _ceiling
    _proc_gone_since = None
    _last_progress = _t.time()
    _gave_up = False
    while True:
        # Check the SOCKET first: attach to whichever daemon binds it, not necessarily the one WE
        # spawned. A restart can spawn a daemon that correctly DEFERS to a sibling already booting.
        if cell_ipc.ping(base_dir, timeout=2.0):
            _say("[+] Cell daemon online.")
            return True
        # A FRESH heartbeat (from our proc OR a sibling we deferred to) means the boot is
        # progressing → wait with NO ceiling. Checked BEFORE the proc-exit grace so a deferred-to
        # sibling that is still advancing is honoured too.
        if _boot_heartbeat_fresh(base_dir):
            if _t.time() - _last_progress >= 15:
                _last_progress = _t.time()
                _say("[*] Cell daemon is booting (heartbeat advancing) — a large ontology can "
                     "take several minutes…")
            _t.sleep(0.5)
            continue
        if proc.poll() is not None:
            # OUR spawned daemon exited and there is no fresh heartbeat. It may have deferred to a
            # sibling that is about to bind the socket; keep a short grace, then give up. A CLI must
            # NEVER embed while a daemon is coming up (a SECOND nucleus writer).
            if _proc_gone_since is None:
                _proc_gone_since = _t.time()
                log.info("[Cell] spawned daemon exited (likely deferred to a sibling) — waiting "
                         "for the live daemon's socket instead of embedding.")
            elif _t.time() - _proc_gone_since > 15:
                log.error("[Cell] daemon exited during startup and no sibling bound the socket "
                          "(see logs/cell-daemon.log).")
                _gave_up = True
                break
            _t.sleep(0.5)
            continue
        # Alive, not answering, and NO fresh heartbeat → apply the fallback ceiling.
        if _t.time() >= _end:
            log.error("[Cell] daemon did not answer within the startup timeout and its boot "
                      "heartbeat is stale — treating it as wedged.")
            _gave_up = True
            break
        _t.sleep(0.5)

    # F2 — a False return MUST mean "no live daemon process exists", because every caller embeds on
    # False. We only reach here with a STALE/absent heartbeat, so a still-alive daemon is genuinely
    # wedged: reap it (+ any leaked portal) before returning, so the caller's embedded fallback is
    # never a second writer beside a wedged spawn. (A fresh-heartbeat boot never falls through here.)
    if _gave_up:
        if _daemon_process_alive(base_dir) is not None:
            log.warning("[Cell] reaping the wedged spawned daemon before falling back "
                        "(a False return must mean no live daemon).")
            _reap_stale_daemon(base_dir)
            _reap_leaked_portals(base_dir)
        else:
            try:
                if proc.poll() is None:
                    proc.terminate()
            except Exception:
                pass
    return False


def _run_cell_client(root: str, base_dir: str, args, interactive: bool) -> bool:
    """Attach to the persistent Cell daemon and drive the CLI as a client over the local
    socket. Spawns the daemon first if none is running. Returns True if a client session
    ran; False to fall back to embedded mode (daemon could not be reached)."""
    import logging as _lg
    from api.portals import cell_ipc
    log = _lg.getLogger("Harmonia.Boot")

    if cell_ipc.ping(base_dir):
        # A daemon ANSWERS. VERSION HANDSHAKE: a re-extracted seed / pulled repo boots akasha.py
        # argument-less and lands HERE — it would otherwise attach to the running daemon and run
        # its tests on that daemon's (possibly OLD) code. If the on-disk build differs, REPLACE
        # the daemon so the new code becomes the writer; if it matches, fast-attach as before
        # (no needless ontology reload — the requirement is 'replace on code change', not
        # 'reload on every run'). A daemon too old to report a build (build=None) is left alone.
        _disk_build = _code_build_id(root)          # compare CODE CONTENT, not the git-SHA banner label
        _running_build = cell_ipc.ping_build(base_dir)
        if _running_build and _disk_build and _running_build != _disk_build:
            log.info("[Cell] daemon build %s != on-disk build %s — replacing the daemon.",
                     _running_build, _disk_build)
            print("  [~] A newer build is on disk — replacing the running Cell daemon so this "
                  "code runs (one-time ontology reload)…", flush=True)
            _stop_recorded_portal(_cell_pid_path(base_dir), grace_ticks=500)   # old daemon: 45s+ grace
            # Also clear the old portal so the fresh daemon binds a clean port (the new daemon's
            # _bind_unix already unlinks a stale IPC socket).
            _stop_recorded_portal(os.path.join(base_dir, "web-portal.pid"))
            _reap_leaked_portals(base_dir)
            # F3 — we have already STOPPED the healthy old daemon, so falling back to embedded here
            # is the worst option: a SECOND writer beside the still-booting replacement AND a
            # minutes-long foreground load (the VPS "idle at startup" report). With F1 the false
            # timeout is gone; a residual GENUINE failure retries the spawn once, then exits
            # NON-ZERO with a truthful message — it never embeds. (_spawn_cell_daemon's F2 guarantee
            # means a False return already left no live daemon behind.)
            if not _spawn_cell_daemon(root, base_dir, args):
                log.warning("[Cell] replacement daemon did not come up — retrying the spawn once.")
                if not _spawn_cell_daemon(root, base_dir, args):
                    print("  [!] The replacement Cell daemon failed to boot (see "
                          "logs/cell-daemon.log). The previous daemon was stopped for the upgrade; "
                          "NOT falling back to an embedded engine (that would be a second nucleus "
                          "writer). Re-run  python akasha.py  to retry.", flush=True)
                    sys.exit(1)
    else:
        # No daemon answers — bring exactly one up WITHOUT ever becoming a second writer or killing
        # a healthy booting daemon. `_ensure_daemon` attaches to an alive-but-booting daemon (SSH
        # reconnect mid-boot), respawns a genuinely hung one, or cold-spawns if none exists.
        if not _ensure_daemon(root, base_dir, args):
            log.warning("[Cell] daemon unavailable — falling back to embedded engine.")
            return False

    gw = cell_ipc.SocketGateway(base_dir)
    ping = gw.dispatch({"jsonrpc": "2.0", "method": "sys.ping", "params": {}, "id": "p"})
    if not isinstance(ping, dict) or "error" in ping:
        gw.close()
        log.warning("[Cell] daemon did not answer sys.ping — falling back to embedded.")
        return False

    from api.portals.stdio import run_cli, run_single_shot
    if not interactive:
        try:
            print(run_single_shot(" ".join(args.cmd), gw))
        finally:
            gw.close()
        return True

    try:
        run_cli(gw)
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        gw.close()
    print("\n  [+] Disconnected from the Cell daemon — it keeps running "
          "(jobs and ontology load continue).\n"
          "      Reconnect:  python akasha.py     ·     Stop:  python akasha.py stop\n",
          flush=True)
    return True


def _run_mcp_client(root: str, base_dir: str, args) -> bool:
    """Serve the MCP stdio transport as a client of the persistent Cell daemon (shared memory:
    the LLM client sees the same nucleus as the web portal). Spawns the daemon if none is
    running. Returns True if the MCP loop ran; False to fall back to an embedded engine.

    Nothing is printed to stdout — the MCP protocol OWNS stdin/stdout, so any banner would
    corrupt the JSON-RPC stream. Diagnostics go to stderr via logging."""
    import logging as _lg
    from api.portals import cell_ipc
    log = _lg.getLogger("Harmonia.Boot")
    # quiet=True: MCP owns stdout (JSON-RPC) — daemon-bring-up status goes to the log, never stdout.
    if not _ensure_daemon(root, base_dir, args, quiet=True):
        log.warning("[MCP] Cell daemon unavailable — falling back to embedded engine.")
        return False
    gw = cell_ipc.SocketGateway(base_dir)
    ping = gw.dispatch({"jsonrpc": "2.0", "method": "sys.ping", "params": {}, "id": "p"})
    if not isinstance(ping, dict) or "error" in ping:
        gw.close()
        log.warning("[MCP] daemon did not answer sys.ping — falling back to embedded.")
        return False
    from api.portals.mcp import run_mcp_stdio, TRUST_LOCAL
    try:
        run_mcp_stdio(gw, trust=TRUST_LOCAL)
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        gw.close()
    return True


# ── 8. Main ───────────────────────────────────────────────────────────────────

def main() -> None:
    import argparse
    import logging
    import threading
    import time

    try:
        _ensure_dirs(_root)
    except Exception as exc:
        sys.stderr.write(f"[CRITICAL] Infrastructure init failed: {exc}\n")
        sys.exit(1)

    _setup_logging(_root, _is_cgi)
    log = logging.getLogger("Harmonia.Boot")
    log.info("Akasha boot sequence initiated.")

    # ── `stop` — halt a detached web portal (no kernel boot needed) ───
    # Simple counterpart to the "exit leaves the server running" behaviour, so an
    # operator never needs a pkill/ps incantation.
    if not _is_cgi and len(sys.argv) >= 2 and sys.argv[1] == "stop":
        _base = os.environ.get("AKASHA_DATA_DIR", "").strip() or os.path.join(_root, "data")
        # Unified stop: cascade over the Supervisor run-dir in reverse-dependency order
        # (dependents — the web portal — before their dependency, the Cell daemon), each
        # with its own grace. The daemon is the writer: its 45 s grace lets it finish the
        # in-flight write and checkpoint before any SIGKILL. Falls back to the legacy pid
        # files for anything not yet on the plane.
        _any = False
        try:
            from lib.harmonia import supervisor as _sv
            _sup = _sv.Supervisor(_base)
            _svc_units = [u for u in _sv.list_units(_base) if u.get("kind") == _sv.KIND_SERVICE]
            for _u in _sv._reverse_dep_order(_svc_units):
                _r = _sup.stop(_u["id"], grace_s=_u.get("grace_s"))
                if _r.get("status") == "stopped":
                    _any = True
                    print(f"  [+] Stopped {_u['id']} (PID {_u.get('pid')}).")
        except Exception as _stop_exc:
            logging.getLogger("Harmonia.Boot").debug("[stop] cascade: %s", _stop_exc)
        # Legacy pid-file fallback (idempotent — a already-stopped pid is a no-op).
        _d = _stop_recorded_portal(_cell_pid_path(_base), grace_ticks=400)
        _p = _stop_recorded_portal(os.path.join(_base, "web-portal.pid"))
        if _d:
            print(f"  [+] Stopped Cell daemon (PID {_d})."); _any = True
        if _p:
            print(f"  [+] Stopped web portal (PID {_p})."); _any = True
        # Sweep any ORPHANED portal for this data dir that the cascade/pid-files missed — a
        # portal whose Cell daemon crashed is re-parented to init and drops out of the run-dir,
        # so it survives `stop` and keeps holding its port + RAM (a ~1GB engine each). This is
        # the "old process not killed" leak an operator otherwise has to pkill by hand. Parallel,
        # so it costs one grace window no matter how many piled up across crashes.
        _orph = _reap_leaked_portals(_base)
        if _orph:
            print(f"  [+] Swept {len(_orph)} orphaned portal(s): PID {', '.join(map(str, _orph))}.")
            _any = True
        if not _any:
            print("  [!] Nothing running to stop.")
        # Clear the stale socket endpoint so a fresh boot re-advertises cleanly.
        for _f in ("central/cell.sock", "central/cell.endpoint"):
            try: os.remove(os.path.join(_base, _f))
            except OSError: pass
        return

    # Data dir defaults to <root>/data; AKASHA_DATA_DIR relocates it (relocatable
    # deployment, and lets a test point the daemon at a scratch cell). The client and
    # daemon share it — the daemon inherits this env when spawned.
    base_dir = os.environ.get("AKASHA_DATA_DIR", "").strip() or os.path.join(_root, "data")

    # ── Backend memory in the tree — so `python akasha.py` (direct) matches the seed ──────
    # The storage engine is set by the seed's sprout header (native seeds export
    # AKASHA_BACKEND=silica). But the common operator move is to run the EXTRACTED
    # `python akasha.py` directly, which bypasses that header — the env is unset and the
    # backend silently defaults to SQLite, so a fresh cell is created in the wrong engine (and
    # an existing native cell re-prompts genesis until the sticky check below catches it). Fix:
    # persist the chosen engine in a `.akasha_backend` marker next to this file; read it here
    # when the env is unset, and (re)write it once the backend is resolved. A native deployment
    # then stays native no matter how it is launched.
    _backend_marker = os.path.join(_root, ".akasha_backend")
    if not os.environ.get("AKASHA_BACKEND", "").strip():
        try:
            _m = open(_backend_marker).read().strip()
            if _m:
                os.environ["AKASHA_BACKEND"] = _m
        except OSError:
            pass

    # ── Sticky backend — honour the store already on disk ─────────────────────────
    # The nucleus can be a single-file SQLite `nucleus.db` OR a native Silica
    # `nucleus.db.silica/` directory. AKASHA_BACKEND picks which — but only for a BRAND-NEW
    # cell. If a nucleus already exists, a launch that (via a stale/leaked env, the marker being
    # absent, or running the SQLite seed and the native seed in the same folder) picks the OTHER
    # backend reads an empty wrong-format nucleus and re-prompts genesis while the real cell —
    # admin identity and all — sits in the other format. So detect the existing store and pin the
    # backend to it, making the choice deterministic per data dir. If BOTH exist (two seeds in one
    # folder), prefer the native Silica store (the one full runs land in) and say so.
    _central = os.path.join(base_dir, "central")
    _sil_dir = os.path.join(_central, "nucleus.db.silica")
    _sql_file = os.path.join(_central, "nucleus.db")
    try:
        _has_sil = os.path.isdir(_sil_dir) and any(
            f.endswith(".wal") for f in os.listdir(_sil_dir))
    except OSError:
        _has_sil = False
    _has_sql = os.path.isfile(_sql_file) and os.path.getsize(_sql_file) > 0
    if _has_sil and _has_sql:
        print(f"  [!] Two nucleus stores in {_central}: a native Silica store AND a SQLite one. "
              "Using the Silica store (this cell lives there); delete 'nucleus.db' + "
              "'nucleus.db-journal' to keep only Silica and silence this.", flush=True)
        os.environ["AKASHA_BACKEND"] = "silica"
    elif _has_sil:
        os.environ["AKASHA_BACKEND"] = "silica"
    elif _has_sql:
        os.environ["AKASHA_BACKEND"] = "sqlite"
    # else: fresh cell — leave AKASHA_BACKEND (the seed/operator choice) as-is.

    # Persist the resolved engine so a later direct `python akasha.py` picks the same one.
    _resolved_backend = os.environ.get("AKASHA_BACKEND", "").strip()
    if _resolved_backend:
        try:
            _cur_marker = ""
            try:
                _cur_marker = open(_backend_marker).read().strip()
            except OSError:
                pass
            if _cur_marker != _resolved_backend:
                open(_backend_marker, "w").write(_resolved_backend)
        except OSError:
            pass

    # ── Parse CLI arguments (early — before we decide whether to build an engine) ──
    # CGI has no argv; it always runs the in-process fast-path below.
    args = None if _is_cgi else _build_arg_parser().parse_args()

    # ── Cell client mode (the default) ────────────────────────────────
    # Restore front=client / backend=server: unless we are explicitly the daemon,
    # embedded, CGI, or a pure --stdio session, attach to the persistent Cell daemon
    # as a thin client instead of building an engine in THIS process. The daemon owns
    # the jobs, so a disconnect never kills the ontology load. Falls back to embedded
    # if the daemon can't be brought up — the CLI is never left with nothing.
    # iOS/iPadOS (a-Shell, Pyto): the daemon/socket/portal process model is unsupported by the
    # sandbox (EBADF on spawn, EPERM on the Unix socket), and running multiple half-broken engines
    # against one store is what lost genesis between launches. Collapse to ONE embedded process:
    # act like `--stdio` (embedded engine + interactive CLI, no daemon, no socket, no portal
    # subprocess) and pick a journal mode without -wal/-shm sidecars, which iCloud Drive does not
    # reliably persist. An explicit --serve/--daemon still overrides. Env override: AKASHA_IOS=0.
    if args is not None and not (args.serve or args.daemon) \
            and os.environ.get("AKASHA_IOS", "").strip().lower() not in ("0", "no", "false", "off") \
            and (_is_ios() or os.environ.get("AKASHA_IOS", "").strip().lower() in ("1", "yes", "true", "on")):
        # iOS collapses to ONE embedded process (no daemon/socket/subprocess). The web portal,
        # however, was previously an IN-PROCESS thread and worked here; it regressed only when the
        # portal became subprocess-only (EBADF on spawn under the sandbox) AND this branch forced
        # `stdio` (which skips the portal block). Restore it as an in-process thread on the SAME
        # engine — but honour an EXPLICIT `--stdio` / AKASHA_NO_WEB (true "CLI only, no web").
        _user_stdio = bool(args.stdio)
        args.stdio = True
        os.environ["AKASHA_EMBEDDED"] = "1"
        _no_web = os.environ.get("AKASHA_NO_WEB", "").strip().lower() in ("1", "yes", "true", "on")
        if not _user_stdio and not _no_web and not args.mcp and not args.cmd:
            args._inproc_web = True
        os.environ.setdefault("AKASHA_SQLITE_JOURNAL", "TRUNCATE")   # single-file, iCloud-safe
        # Native store (Silica) durability on iCloud: the Silica store is a MULTI-FILE directory
        # (one WAL per bank + a coordinator log). iCloud Drive does not reliably persist a
        # multi-file store across launches — some bank files come back empty/stale — so a write
        # that landed in one bank (e.g. the genesis `admin_name` in the vault bank) is lost on the
        # next open even though other banks (ontology atoms) survive. That is exactly why the
        # iOS path uses a single-file store. So on an iCloud data dir, fall back to the durable
        # single-file SQLite store. To exercise Silica on iOS, run from a LOCAL folder (not
        # ~cloud) — it is honoured there — or force it with AKASHA_FORCE_SILICA=1.
        _ap = os.path.abspath(base_dir).lower()
        _icloud = any(_m in _ap for _m in ("mobile documents", "com~apple~clouddocs",
                                           "clouddocs", "icloud"))
        _force_silica = os.environ.get("AKASHA_FORCE_SILICA", "").strip().lower() in (
            "1", "yes", "true", "on")
        if (os.environ.get("AKASHA_BACKEND", "sqlite").strip().lower() == "silica"
                and _icloud and not _force_silica and not _has_sil):   # never orphan an existing Silica cell
            os.environ["AKASHA_BACKEND"] = "sqlite"
            print("  [i] iOS/iPadOS — the native (Silica) store is multi-file and iCloud does not "
                  "reliably persist it across launches (genesis/writes reappear lost). Using the "
                  "single-file SQLite store here so data survives. To test Silica, run from a LOCAL "
                  "folder (e.g. ~/Documents), not ~cloud — or set AKASHA_FORCE_SILICA=1.", flush=True)
        _store_desc = ("native Silica store" if os.environ.get(
            "AKASHA_BACKEND", "sqlite").strip().lower() == "silica" else "single-file SQLite store")
        print(f"  [i] iOS/iPadOS detected — running as a single embedded process "
              f"(no daemon/socket/portal); durable {_store_desc}.", flush=True)

    if args is not None:
        _server_mode = args.serve or args.daemon
        _embedded = (args.embedded or args.stdio
                     or os.environ.get("AKASHA_EMBEDDED", "").strip().lower()
                     in ("1", "yes", "true", "on"))
        # Server/daemon SINGLETON + VERSION guard. The IPC listener unlinks + rebinds its socket
        # unconditionally, so a second daemon silently STEALS the endpoint and the first keeps
        # running as a zombie nucleus writer — two writers into one nucleus, the single-writer
        # violation the design forbids. So if a daemon already ANSWERS on this data dir:
        #   • SAME build  → do NOT boot a second engine (defer; `stop` first to replace on purpose).
        #   • OLDER build → this launch carries newer code, so STOP the old daemon and take over
        #                   (the direct --serve/--daemon counterpart of the client-path handshake;
        #                   this is how a re-extracted seed's newer code becomes the live writer).
        # A crash/hung daemon does not answer, so a genuine restart still proceeds either way.
        if _server_mode and not _embedded:
            from api.portals import cell_ipc as _cipc_guard
            if _cipc_guard.ping(base_dir):
                _running_build = _cipc_guard.ping_build(base_dir)
                _disk_build = _code_build_id(_root)          # code content, not the git-SHA banner label
                if _running_build and _disk_build and _running_build != _disk_build:
                    print("  [~] Replacing an OLDER running Cell daemon with this build "
                          f"({_running_build} → {_disk_build})…", flush=True)
                    _stop_recorded_portal(_cell_pid_path(base_dir), grace_ticks=500)
                    _stop_recorded_portal(os.path.join(base_dir, "web-portal.pid"))
                    _reap_leaked_portals(base_dir)
                else:
                    print("  [i] A Cell daemon is already serving this data dir — not starting a "
                          "second (two nucleus writers is unsafe).\n"
                          "      Replace it deliberately with:  python akasha.py stop  then start.",
                          flush=True)
                    return
            # EXCLUSIVE boot lock — the ping guard above only sees a daemon that is already
            # ANSWERING; it cannot see a sibling that is mid-boot (socket not yet bound). Two such
            # cold boots racing into the SAME nucleus is the two-writers crash seen in the logs
            # (daemon dies during the early lexicon weave). flock lets exactly one proceed; the
            # loser defers. Auto-released on process death, so a crash never leaves it stuck.
            global _HELD_BOOT_LOCK
            _HELD_BOOT_LOCK = _acquire_boot_lock(base_dir)
            if _HELD_BOOT_LOCK is None:
                # R1/R2 — the boot lock is held by another process. Do NOT blindly "defer" (RC1):
                # a WEDGED holder is neither answering nor progressing, and deferring to it with
                # EXIT 0 leaves the daemon dead forever while systemd (`Restart=on-failure`) records
                # a clean start. Run the SHARED convergence routine (spawn=False): let the holder
                # answer, or reap it if it is genuinely wedged.
                _state = _converge_daemon(_root, base_dir, args, spawn=False)
                if _state == "answering":
                    print("  [i] A Cell daemon is already serving this data dir — deferring to it "
                          "(avoids two writers into one nucleus).", flush=True)
                    return                               # correct defer to an ANSWERING daemon → exit 0
                # The holder was wedged and reaped (or it died). Try ONCE more to take the boot lock
                # and continue booting THIS process into the writer role.
                _HELD_BOOT_LOCK = _acquire_boot_lock(base_dir)
                if _HELD_BOOT_LOCK is None:
                    # Another process grabbed the lock in the gap — give it a moment to bind, then
                    # defer if it serves, else refuse (non-zero) rather than defer to a wedged holder.
                    if _wait_for_daemon_socket(base_dir):
                        print("  [i] Another Cell daemon took over and is serving — deferring.",
                              flush=True)
                        return
                    print("  [!] Could not acquire the boot lock and no daemon is answering — "
                          "refusing to defer to a wedged/re-locked holder.", flush=True)
                    sys.exit(1)
                print("  [~] Reaped a wedged boot-lock holder — taking over as the Cell daemon.",
                      flush=True)
                # fall through with the lock now held → record pid + continue booting.
            # Record our pid from the START of boot — NOT late (svc:cell registers only after the
            # whole ontology load). A restart during the multi-second load window must be able to
            # FIND and reap this daemon (_reap_stale_daemon reads cell.pid); writing it late left a
            # mid-boot daemon invisible to process management, so a restart spawned a second one.
            try:
                os.makedirs(os.path.join(base_dir, "central"), exist_ok=True)
                with open(_cell_pid_path(base_dir), "w") as _pf:
                    _pf.write(str(os.getpid()))
            except OSError:
                pass
        # MCP stdio transport (local LLM route): attach to the daemon (shared memory) and
        # serve MCP over stdin/stdout. Falls through to an embedded MCP server below if the
        # daemon can't be reached. Never starts the web portal (the CLI stdout is the pipe).
        if args.mcp and not _server_mode:
            if not _embedded and _run_mcp_client(_root, base_dir, args):
                return
            # else: build the embedded engine below, then serve MCP over it.
        elif not _server_mode and not _embedded:
            if not args.cmd:                             # interactive REPL
                if _run_cell_client(_root, base_dir, args, interactive=True):
                    return
            else:                                        # single-shot one-off command
                # R1/R2: converge to a live daemon BEFORE ever running embedded. A one-off command
                # used to run silently EMBEDDED next to a wedged daemon (RC2) — a second nucleus
                # writer that also MASKS the outage (a `akasha.py sys.ping` cron probe then HIDES
                # daemon death). Embedded is now the LAST resort, reached only when no daemon
                # process exists at all.
                _state = _converge_daemon(_root, base_dir, args, spawn=True)
                if _state in ("answering", "spawned"):
                    if _run_cell_client(_root, base_dir, args, interactive=False):
                        return
                # Converge did not yield an answering daemon. If a daemon process is nonetheless
                # ALIVE (wedged, unreachable), refuse to embed beside it (that is the second-writer
                # hazard) — exit non-zero so the outage surfaces instead of being masked.
                if _daemon_process_alive(base_dir) is not None:
                    print("  [!] A Cell daemon process is alive but not reachable — refusing to run "
                          "this command in an embedded engine beside it (a second nucleus writer is "
                          "unsafe).\n      Recover with:  python akasha.py stop   then retry.",
                          flush=True)
                    sys.exit(3)
                # Genuinely no daemon process: run embedded (built below), but say so plainly, and
                # remember to exit non-zero if a daemon was EXPECTED (a recorded pid existed) so
                # cron/scripts can react to the daemon being down.
                print("  [!] No daemon reachable — running this command in an embedded engine; the "
                      "persistent daemon/portal are NOT running.", flush=True)
                args._embedded_singleshot_expected = _recorded_daemon_pid(base_dir) is not None
            # else / fall-through: build the embedded engine below for the one-off command.

    # ── Boot the kernel ──────────────────────────────────────────────
    from api.gateway import create_gateway
    import api.gateway as _gw_module

    _stop = threading.Event()
    if not _is_cgi:
        stages = [
            "Loading cognitive substrate",
            "Initializing memory cortex",
            "Wiring semantic engine",
            "Synchronizing knowledge graph",
        ]
        _spin_t = threading.Thread(
            target=_boot_spinner, args=(_stop, stages), daemon=True
        )
        _spin_t.start()

    # Series may be pinned out-of-band (e.g. a thesaurus deployment on shared
    # hosting via CGI) without editing code; defaults to the public seeds tier.
    _series = os.environ.get("AKASHA_SERIES", "seeds").strip() or "seeds"

    # ── Boot-progress heartbeat (R4) ──────────────────────────────────
    # A process that will OWN the cell socket (a daemon, or a portal-spawning foreground) touches
    # the boot heartbeat through the create_gateway window — which scales with the nucleus (migrate
    # drain, orphan scan, IAM load) and can run for many seconds on a B-scale DB + slow VPS disk.
    # A converging client/server then sees this boot as PROGRESSING (heartbeat fresh) and NEVER
    # reaps it as wedged. The thread is stopped and the file cleared once the socket is up
    # (sys.ping becomes the liveness signal); a wedged create_gateway stops the touches → stale.
    _hb_stop = None
    if not _is_cgi and args is not None and (
            args.serve or args.daemon
            or (not args.stdio and not args.mcp and not args.cmd)):
        _hb_stop = threading.Event()
        threading.Thread(target=_run_boot_heartbeat, args=(base_dir, _hb_stop),
                         name="boot-heartbeat", daemon=True).start()

    try:
        live_gw = create_gateway(series=_series, base_dir=base_dir)
    finally:
        if not _is_cgi:
            _stop.set()
            _spin_t.join(timeout=1.0)

    _gw_module.gateway = live_gw
    log.info("Kernel online. Gateway singleton wired.")

    # Graceful shutdown for the non-interactive exit paths (SIGTERM, server stop, EOF):
    # stop the background daemons + close SQLite connections before the interpreter tears
    # down the C-extension modules. Registered AFTER the manager's own atexit(close), so
    # LIFO runs THIS first — then the backend close()s it triggers are idempotent no-ops
    # when the manager's atexit fires. Interactive `exit` calls it directly (stdio.py).
    import atexit as _atexit_ls
    from lib.akasha import lifecycle as _lifecycle
    _atexit_ls.register(_lifecycle.begin_shutdown)

    # Signal handling — survive SSH hangup, exit cleanly on SIGTERM.
    #
    # The interactive CLI is often started over SSH (VPS 動作確認). When the SSH
    # session drops, the kernel delivers SIGHUP to the controlling process group.
    # The default SIGHUP disposition is to KILL the process outright — which tears
    # a C-extension thread (SQLite/numpy inside a mid-flight canon-normalize write)
    # down without unwinding, and THAT is what produced the intermittent coredump
    # and the "振り出しに戻る" full ontology re-load on the next boot.
    #
    # Ignoring SIGHUP converts the abrupt kill into an ordinary stdin-EOF, which
    # run_cli catches and drains through the SAME graceful begin_shutdown() path as
    # a typed `exit` — daemons are woken and joined, SQLite is checkpointed and
    # closed, no C-ext teardown race, no coredump. SIGTERM (systemd stop, `kill`)
    # is likewise routed through begin_shutdown() before a clean _exit(0).
    #
    # Guarded: signal handlers can only be installed from the main thread of the
    # main interpreter, and SIGHUP is POSIX-only — a non-main-thread launch (some
    # embeddings) or Windows raises ValueError/AttributeError, which is non-fatal.
    if not _is_cgi:
        try:
            import signal as _signal

            if hasattr(_signal, "SIGHUP"):
                _signal.signal(_signal.SIGHUP, _signal.SIG_IGN)

            def _on_sigterm(_signum, _frame):
                try:
                    _lifecycle.begin_shutdown()
                finally:
                    os._exit(0)

            _signal.signal(_signal.SIGTERM, _on_sigterm)
        except (ValueError, AttributeError, OSError) as _sig_exc:
            log.debug("Signal handlers not installed (%s).", _sig_exc)

    # ── Cell writer socket: open the local IPC socket + record the pid ─
    # THIS process owns live_gw and its WriteQueue — it is the SINGLE nucleus writer.
    # Expose the local TRUST_LOCAL socket so (a) a co-located CLI client can attach and
    # perform genesis without building a second engine, and (b) the serve-only web-portal
    # SUBPROCESS can forward writes/auth/session back to this ONE writer (SplitGateway,
    # trust-preserving) instead of opening a second writer into the same nucleus.
    #
    # Needed in server/daemon mode AND in the ordinary foreground CLI-with-portal case
    # (the seeds default: `python akasha.py` → interactive CLI + serve-only portal).
    # NOT needed for `--stdio` (no portal), a single-shot `args.cmd`, or CGI. Started
    # early — right after the gateway exists — so the portal's ping/forward succeeds
    # before the heavy boot load. The socket close() is registered for graceful shutdown.
    _server_mode = (args is not None) and (args.serve or args.daemon)
    _spawns_portal = ((args is not None) and (not args.stdio) and (not args.mcp)
                      and (not args.cmd) and (not _is_cgi))
    _owns_cell_socket = _server_mode or _spawns_portal
    if _owns_cell_socket:
        # Stamp the running-code fingerprint into this process's env BEFORE the IPC socket goes
        # live, so sys.ping advertises it from the first probe. A client that finds a daemon whose
        # build differs from the on-disk code replaces it instead of testing on stale code (the
        # 're-extracted seed attaches to the old daemon' bug). Authoritative for THIS daemon.
        os.environ["AKASHA_BUILD_ID"] = _resolve_build_id(_root)
        # The REPLACE handshake must compare actual CODE CONTENT, not the display label. A seed
        # stamps AKASHA_BUILD_ID with a git SHA (e.g. 00347d6194) for the banner; a plain
        # `python akasha.py` reconnect has no such env and would resolve to the content hash — so
        # `_resolve_build_id` returns DIFFERENT strings for identical code, and the reconnect would
        # SIGTERM/SIGKILL-replace a perfectly-current daemon (even mid-load → the silent, no-trace
        # daemon death + boot loop). AKASHA_HANDSHAKE_BUILD is ALWAYS the code-content fingerprint,
        # so the handshake matches whenever the code matches, regardless of how it was launched.
        os.environ["AKASHA_HANDSHAKE_BUILD"] = _code_build_id(_root)
        try:
            from api.portals.cell_ipc import CellIPCServer
            _ipc = CellIPCServer(live_gw, base_dir)
            _ipc.start()
            _lifecycle.register_closer(_ipc.stop)
            os.makedirs(os.path.join(base_dir, "central"), exist_ok=True)
            with open(_cell_pid_path(base_dir), "w") as _pf:
                _pf.write(str(os.getpid()))
        except Exception as _ipc_exc:
            log.warning("[Cell] local IPC socket failed to start (%s) — "
                        "the web portal will fall back to read-only serving.", _ipc_exc)
        finally:
            # Boot's socket-bind milestone is reached (or IPC failed) — either way the boot
            # heartbeat has done its job. Stop touching it and clear the file so 'heartbeat fresh'
            # never lingers past boot (post-boot liveness is sys.ping). Cleared again on shutdown.
            if _hb_stop is not None:
                _hb_stop.set()
            _boot_heartbeat_clear(base_dir)

        # Share the session-signing secret with the portal subprocess (fixes "Guest binding:
        # signature mismatch"). gbk:/akt: tokens are self-verifying (HMAC, no server state),
        # which assumes ONE signing authority. In the daemon + serve-only-portal split, tokens
        # are MINTED by this process (the portal forwards session/auth to the primary writer)
        # but VERIFIED LOCALLY by the portal on reads — so if the two processes resolve
        # DIFFERENT secrets, every guest token fails. Export this process's resolved secret to
        # the environment so the portal subprocess (spawned with env.copy()) and every P4
        # respawn (env_inherit) verify with the IDENTICAL key. Honor an operator-set
        # AKASHA_SECRET; otherwise seed it from the resolved (vault-or-generated) key — exactly
        # the security model's "one AKASHA_SECRET, identical across the deployment", automated
        # for the single-host process tree.
        if not os.environ.get("AKASHA_SECRET"):
            try:
                _sec = live_gw.kernel_client.iam.guest_bindings._secret()
                os.environ["AKASHA_SECRET"] = _sec.hex()
                log.info("[Cell] shared the session-signing secret with portal subprocesses.")
            except Exception as _sx:
                log.warning("[Cell] could not share the session secret (%s) — guest tokens "
                            "may mismatch across the portal split; set AKASHA_SECRET.", _sx)
        # Register this process as the Supervisor root (svc:cell) and reconcile the
        # run-dir (scrub descriptors whose pid died in a prior crash). The writer is
        # Akasha's service init: its children (the web portal, deps=["svc:cell"]) are
        # stopped before it on shutdown. Writer → generous grace to checkpoint. Done in
        # both server and foreground modes so the svc graph and the portal's forward
        # target are coherent either way.
        try:
            from lib.harmonia import supervisor as _sv
            # Clean old processes BEFORE reconcile: a Cell daemon that died (OOM/crash) leaves
            # its detached portal child running (the OS never reaps a start_new_session orphan),
            # holding its port. Reap every leaked portal for THIS data dir first — on ANY port —
            # so reconcile then sees a clean slate (it scrubs the now-dead descriptor) and the
            # boot spawns exactly one fresh portal, instead of adopting a stale orphan and
            # fighting it (the 'respawned svc:web-portal (unhealthy)' churn). Scoped to this
            # deployment's module+data-dir, so foreign servers / other cells are never touched.
            _leaked = _reap_leaked_portals(base_dir)
            if _leaked:
                log.info("[Boot] reaped %d orphaned portal(s) from a prior crash: %s",
                         len(_leaked), ", ".join(map(str, _leaked)))
                print(f"  [~] Cleaned {len(_leaked)} orphaned portal(s) left by a prior "
                      f"crash (PID {', '.join(map(str, _leaked))}).", flush=True)
            _supervisor = _sv.Supervisor(base_dir)
            _supervisor.reconcile()
            _supervisor.record_running(
                "svc:cell", os.getpid(), engine="cell-daemon",
                host=os.environ.get("AKASHA_HOST", ""), grace_s=45.0)
            _lifecycle.register_closer(
                lambda: _sv.remove_unit(base_dir, "svc:cell"))
            # Mount the ontology load onto the plane as job:onto-load (visibility only).
            threading.Thread(target=_onto_load_watcher, args=(live_gw, base_dir),
                             name="onto-load-watcher", daemon=True).start()
            # P4 — periodic health/respawn tick. Server/daemon only: the interactive
            # foreground runs its own stop-at-exit path (below), and a respawn tick there
            # would race the operator's exit → keep autonomous respawn to headless deploys.
            if _server_mode:
                threading.Thread(target=_supervisor_health_tick, args=(base_dir,),
                                 name="supervisor-health", daemon=True).start()
        except Exception as _sup_exc:
            log.debug("[Supervisor] root registration skipped: %s", _sup_exc)

    if not _is_cgi:
        print(f"  [i] Build: {_format_build_stamp(akasha_build_stamp(_root))}", flush=True)
        print("  [+] Akasha online.\n", flush=True)

    # ── Auto-ensure optional runtime libraries ────────────────────────
    # Runs only in interactive mode; CGI, and the headless Cell daemon skip this —
    # a backend daemon must come up and serve its socket immediately, never block on
    # a pip subprocess (and never touch the network) at boot.
    # Each call spins a pip subprocess with a 120 s timeout.  Errors are
    # logged but never fatal — the kernel runs fine without these.
    if not _is_cgi and not _server_mode:
        from api.env_detector import env as _boot_env, Symbiosis as _BootSymbiosis

        # ML / Neural engine: LiteRT (ai-edge-litert) is the primary runtime — the standalone
        # tflite-runtime is frozen at 2.14 and crashes under numpy 2.x, so it is only a
        # legacy 32-bit-ARM fallback; full TF is a heavier last resort. (Nothing consumes
        # this at boot today — VisionEngine installs LiteRT on demand — but keeping the ladder
        # correct means the eager path installs the right, working runtime.)
        if _boot_env.get_ml_engine_status() == "installable":
            _BootSymbiosis.ensure_one_of(
                [
                    ("ai_edge_litert", "ai-edge-litert"),
                    ("tflite_runtime", "tflite-runtime"),
                    ("tensorflow",     "tensorflow-cpu"),
                ],
                scope="[ML]", feature="Neural Engine (LiteRT)",
            )

        # NLP engine: SpaCy for semantic trait extraction and word decomposition
        if _boot_env.get_nlp_status() == "installable":
            _BootSymbiosis.ensure(
                "spacy", "spacy",
                scope="[NLP]", feature="Natural Language Processing (SpaCy)",
            )

    # ── CGI fast-path ────────────────────────────────────────────────
    if _is_cgi:
        log.info("CGI environment detected.")
        from api.portals.asgi import run_cgi
        run_cgi(live_gw, _original_stdout)
        return

    # CLI arguments were parsed early (before the engine was built) so client mode
    # could skip building one. `args` is in scope here for every embedded/server path.

    # ── Headless single-shot (embedded — no daemon was running) ───────
    if args.cmd:
        from api.portals.stdio import run_single_shot
        print(run_single_shot(" ".join(args.cmd), live_gw))
        # R2: if a daemon was EXPECTED (a recorded pid existed) but we ran embedded because it was
        # unreachable, exit non-zero so a cron/script probe reflects that the daemon is down —
        # rather than reporting success from a masking embedded run.
        sys.exit(2 if getattr(args, "_embedded_singleshot_expected", False) else 0)

    # ── Archives detection ─────────────────────────────────────────────
    # In deployed bundles (seeds/thesaurus): reproductor/ is absent, so
    # file existence determines which portal to serve.
    # On the mother machine (full repo): reproductor/ is present, so
    # the --portal flag is the only way to enable the archives portal;
    # the default is always the seeds portal (services/static).
    _archives_path    = os.path.join(_root, "archives")
    _archives_index   = os.path.join(_archives_path, "index.html")
    _is_dev           = os.path.isdir(os.path.join(_root, "reproductor"))
    if args.portal == "archives":
        _has_archives = True
    elif _is_dev:
        _has_archives = False          # dev default: seeds portal
    else:
        _has_archives = os.path.isfile(_archives_index)  # bundle: auto-detect

    # ── Web portal ─────────────────────────────────────────────────────
    # Skipped for --stdio (CLI only), --mcp (the MCP JSON-RPC stream owns stdout), and when
    # AKASHA_NO_WEB=1 — the latter runs the writer daemon WITHOUT the serve-only portal
    # subprocess (which builds its own full ~1 GB read engine). On a memory-tight host that
    # second engine is what tips the box into the OOM-killer during the load; disabling it both
    # DIAGNOSES that (daemon survives ⟺ the portal was the memory straw) and is a valid
    # headless/CLI-only or API-only deployment. Honored on every platform now (was iOS-only).
    _skip_web = os.environ.get("AKASHA_NO_WEB", "").strip().lower() in ("1", "yes", "true", "on")
    if not args.stdio and not args.mcp and not _skip_web:
        import subprocess as _subprocess
        import atexit
        from lib.harmonia import supervisor as _sv_mod
        from api.env_detector import Symbiosis as _Symbiosis
        # The Harmonia Supervisor is the ONE service registry — the volatile ServiceManager
        # is retired. Services are recipe-respawnable process units on the run-dir; this
        # instance holds THIS process's live handles for stop-at-exit + detach.
        _supervisor = _sv_mod.Supervisor(base_dir)

        # Stop the services THIS process spawned on clean exit (a detached public portal is
        # released first, so it survives — see the CLI-exit block).
        atexit.register(_supervisor.stop_local)

        # Clean RESTART semantics: a public deploy leaves its portal running on
        # `exit`, so re-running akasha.py must REPLACE that detached portal rather
        # than double-launch and collide on the port (the "Address already in use"
        # the operator hit). Stop it first — before the ACME port-80 responder or
        # the new portal binds — so the operator never kills a process by hand.
        _prev_portal = _stop_recorded_portal(os.path.join(base_dir, "web-portal.pid"))
        if _prev_portal:
            print(f"  [~] Restarting — stopped the portal left running by the last "
                  f"session (PID {_prev_portal}).", flush=True)

        # The ACME http-01 challenge (below) needs port 80. A portal orphaned by a
        # previous run — e.g. still in memory after `rm -r *` wiped its pid file —
        # can be holding it, which 404s the challenge and fails the cert. Free it
        # BEFORE ACME runs (only our own orphaned portal; foreign servers untouched).
        _orphan80 = _free_orphan_akasha_port(80)
        if _orphan80:
            print(f"  [~] Freed port 80 for the ACME challenge — stopped an orphaned "
                  f"Akasha portal (PID {_orphan80}).", flush=True)

        # Engine / host / port resolution.
        # AKASHA_HOST / AKASHA_PORT let a seed (which runs akasha.py via runpy
        # with no CLI args) bind a public interface / privileged port — e.g.
        # AKASHA_PORT=80 so a bare domain reaches the portal. CLI flags win.
        _web_engine = args.server
        _web_host   = os.environ.get("AKASHA_HOST", "").strip() or args.host
        if _has_archives and _web_host == "127.0.0.1":
            _web_host = "0.0.0.0"
        if _has_archives:
            _web_engine = "uvicorn"

        # TLS: a cert/key pair (env AKASHA_TLS_CERT/KEY or <data>/tls/) turns the
        # portal into HTTPS — required for search engines to crawl the archives.
        # TLS always uses uvicorn (clean SSL support) and the HTTPS port (443);
        # a sibling port-80 responder (started in the web worker) handles the
        # ACME challenge + HTTP→HTTPS redirect.
        # akasha-managed Let's Encrypt (layer B): if domains are configured — via
        # config/tls.json or config/tls_domains.txt (no shell/env needed), or the
        # AKASHA_TLS_DOMAINS env — and the cert is missing/near-expiry, obtain it now,
        # before the portal binds, using a temporary port-80 ACME responder. No-op
        # (fast) when unconfigured or a current cert already exists, so the local/seeds
        # path is untouched.
        try:
            from services.acme import ensure_certificate as _ensure_cert
            _acme_status = _ensure_cert(base_dir)
            if _acme_status == "issued":
                print("  [+] [TLS] Let's Encrypt certificate obtained.", flush=True)
            elif _acme_status.startswith("failed:"):
                print(f"  [!] [TLS] ACME provisioning failed — serving HTTP. "
                      f"({_acme_status[7:][:120]})", flush=True)
        except Exception as _acme_exc:
            log.warning(f"[Boot] ACME provisioning error: {_acme_exc}")

        # TLS is optional — never let it take the whole portal down. If the layer
        # is unavailable (e.g. an incomplete tree missing services/tls.py, or any
        # resolve error) degrade cleanly to HTTP instead of crashing the boot.
        try:
            from services.tls import resolve_tls as _resolve_tls
            _tls = _resolve_tls(base_dir)
        except Exception as _tls_exc:
            log.warning(f"[Boot] TLS layer unavailable ({_tls_exc}) — serving HTTP. "
                        f"Update the deployment (services/tls.py) to enable HTTPS.")
            print("  [!] [TLS] layer unavailable — serving HTTP "
                  "(incomplete tree? re-deploy to enable HTTPS).", flush=True)
            _tls = {"active": False, "https_port": 443, "certfile": "", "keyfile": "",
                    "http_port": 80, "challenge": ""}
        if _tls["active"]:
            _web_engine = "uvicorn"

        # Port: explicit --port / AKASHA_PORT win. Otherwise HTTPS → 443, the
        # public archives portal → 80 (bare domain works with no operator setup;
        # needs root), every other case auto-selects from 8000.
        _env_port = os.environ.get("AKASHA_PORT", "").strip()
        _web_port = (args.port
                     or (int(_env_port) if _env_port.isdigit() else 0)
                     or (_tls["https_port"] if _tls["active"] else None)
                     or (80 if _has_archives else _free_port(8000, _web_host)))

        # Static dirs for ASGI
        # The archives series ships its OWN cosmos instance (archives/cosmos/) —
        # a separate copy with the Archives door back into "/". The seeds series
        # uses the bundled services/static/cosmos (no archives door). Pick the
        # archives instance when this deployment is an archives.
        _archives_cosmos = os.path.join(_archives_path, "cosmos")
        _cosmos_static   = (_archives_cosmos
                            if _has_archives and os.path.isdir(_archives_cosmos)
                            else os.path.join(_root, "services", "static", "cosmos"))
        _services_static = os.path.join(_root, "services", "static")
        _docs_path       = os.path.join(_root, "docs")

        # Build mount list: most-specific paths first, "/" last.
        # Archives sub-apps (word sphere, field gallery, …) are mounted
        # individually so they are reachable from both portals.
        _asgi_static_dirs = []
        if os.path.isdir(_cosmos_static):
            _asgi_static_dirs.append(("/cosmos", _cosmos_static))
        if os.path.isdir(_docs_path):
            _asgi_static_dirs.append(("/docs", _docs_path))
        for _app in ("word", "field"):
            _app_path = os.path.join(_archives_path, _app)
            if os.path.isdir(_app_path):
                _asgi_static_dirs.append((f"/{_app}", _app_path))

        if _has_archives:
            _asgi_static_dirs.append(("/", _archives_path))
            _web_engine = "uvicorn"          # archives portal always needs ASGI
        else:
            _asgi_static_dirs.append(("/", _services_static))
            # Seeds portal: keep httpd as default.
            # Extra mounts (cosmos, cookbook, docs) are active when uvicorn is
            # chosen explicitly via --server uvicorn; httpd ignores them.

        # ── Auto-ensure ASGI dependencies (fastapi + uvicorn) ────────
        # Runs pip install as a child process with a spinner + timeout.
        # If either package cannot be installed, fall back to httpd.
        if _web_engine == "uvicorn":
            _fa = _Symbiosis.ensure(
                "fastapi", "fastapi",
                scope="[ASGI]", feature="Web Portal (FastAPI)",
            )
            _uv = _Symbiosis.ensure(
                "uvicorn", "uvicorn[standard]",
                scope="[ASGI]", feature="Web Portal (uvicorn)",
            )
            if not (_fa and _uv):
                print("  [!] ASGI portal unavailable — falling back to built-in httpd.\n",
                      flush=True)
                _web_engine = "httpd"

        # ── httpd portal (thread-based, existing) ────────────────────
        # The portal banner is printed from this thread; if it lands while the
        # CLI is prompting for genesis/auth it corrupts the prompt. We signal
        # readiness after the banner so the boot can flush it before the prompt.
        def _spawn_portal(cmd, engine, scheme="http"):
            """Spawn a serve-only portal SUBPROCESS, persist its P1 respawn recipe, and
            register it on the Supervisor as svc:web-portal. Both the stdlib httpd portal
            and the uvicorn portal go through here — one process-unit path, no thread
            special case (that is what lets ServiceManager be retired). Returns the proc,
            or {'error': …} on failure."""
            # Free any ORPHANED Akasha portal still holding this port before we spawn. When a
            # prior daemon dies it leaves its detached (start_new_session) portal bound to 443/80;
            # the fresh portal then can't bind — "[Errno 98] address already in use" — exits or
            # hangs, the Supervisor marks it unhealthy and respawns it, and it fails to bind again:
            # the endless 'respawned svc:web-portal (unhealthy)' loop (a 46 MB web-portal.log of
            # bind errors). Akasha frees its OWN port here (only akasha/web_worker holders are
            # touched — foreign processes are left alone), then waits until the port is actually
            # bindable (a just-freed port can linger in TIME_WAIT). No operator pkill — the writer
            # manages its own ports, per the process-ownership rule.
            if _web_port:
                _freed = _free_orphan_akasha_port(int(_web_port))
                if _freed:
                    log.info(f"[Boot] freed orphaned portal PID {_freed} holding port {_web_port} "
                             f"(would have caused the bind-fail respawn loop)")
                if not _wait_port_bindable(_web_host, int(_web_port)):
                    log.warning(f"[Boot] port {_web_port} still not bindable — portal spawn may "
                                f"hit EADDRINUSE; not retrying in a loop")
            log_path = os.path.join(_root, "logs", "web-portal.log")
            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"
            # Serve-only: THIS process is the sole nucleus writer (boot-load + autolearn);
            # the portal only serves reads. Two writers into one nucleus is a single-writer
            # violation that kills the worker on first boot ("Dead").
            env["AKASHA_NO_AUTOLEARN"] = "1"
            env["AKASHA_SERVE_ONLY"] = "1"
            # R5: hand the portal this daemon's launch args so its self-watchdog can spawn an
            # IDENTICAL replacement (same --server/--host/--port/--portal) if the writer wedges.
            import json as _json_argv
            env["AKASHA_DAEMON_ARGV"] = _json_argv.dumps(sys.argv[1:])
            try:
                log_fh = open(log_path, "a")
                # start_new_session: own session so an SSH SIGHUP on disconnect does not kill
                # the portal — it keeps serving after `exit` on a public deploy.
                proc = _subprocess.Popen(
                    cmd, stdout=log_fh, stderr=_subprocess.STDOUT,
                    cwd=_root, env=env, start_new_session=True,
                )
            except Exception as exc:
                log.error(f"[Boot] Failed to start portal ({engine}): {exc}")
                return {"error": str(exc)}
            # Legacy pid file — a cross-process `akasha.py stop` fallback.
            try:
                with open(os.path.join(base_dir, "web-portal.pid"), "w") as _pf:
                    _pf.write(str(proc.pid))
            except Exception:
                pass
            # P1 respawn recipe: validated + (if a supervisor key is present) HMAC-signed;
            # only the non-secret env keys are stored (the secret is inherited at respawn).
            try:
                _portal_recipe = _sv_mod.build_process_spec(
                    argv=cmd, cwd=_root,
                    env_add={"PYTHONUNBUFFERED": "1", "AKASHA_NO_AUTOLEARN": "1",
                             "AKASHA_SERVE_ONLY": "1",
                             "AKASHA_DAEMON_ARGV": _json_argv.dumps(sys.argv[1:])},
                    log=log_path, base_dir=base_dir)
            except Exception as _rex:
                log.debug("[Boot] portal recipe not persisted: %s", _rex)
                _portal_recipe = None
            # Health probe (P4/R3): a JSON-RPC POST that the worker must RUN code to answer, NOT a
            # bare TCP connect. A SIGSTOPped/hung portal still completes the kernel TCP handshake
            # into its accept backlog, so the old TCP probe reported it healthy and it was never
            # respawned (RC3). A sys.ping POST to /api/rpc gets NO response from a wedged worker →
            # the probe times out → unhealthy → respawn. Any HTTP response (even an auth error)
            # counts as alive. The health tick debounces so a transient blip never false-respawns.
            _portal_health = ({"kind": "http",
                               "target": f"{scheme}://127.0.0.1:{int(_web_port)}/api/rpc",
                               "method": "sys.ping", "timeout": 3.0}
                              if _web_port else None)
            # F9 — a B-scale serve-only worker takes ~45-60 s to load its substrate before it binds
            # its port; give it a generous readiness grace so the health tick never respawns it
            # mid-boot (the worker ends the grace early by stamping ready_at once it serves).
            _portal_boot_grace = float(os.environ.get("AKASHA_BOOT_GRACE", "").strip() or 300)
            _supervisor.record_running(
                "svc:web-portal", proc.pid, engine=engine, host=_web_host, port=_web_port,
                grace_s=5.0, restart="on-failure", deps=["svc:cell"], proc=proc,
                spec=_portal_recipe, trust="network", serve_only=True,
                health=_portal_health, boot_grace_s=_portal_boot_grace, log_fd=log_fh)
            log.info(f"[Boot] Web portal ({engine}) PID {proc.pid} on {_web_host}:{_web_port}")
            from services.http_gateway import portal_banner
            for _line in portal_banner(_web_host, _web_port, scheme=scheme):
                print("  " + _line, flush=True)
            print(f"      (PID {proc.pid} · logs/web-portal.log)\n", flush=True)
            return proc

        def _launch_http_portal():
            """Launch the stdlib HTTP portal as a serve-only subprocess (was an in-process
            thread — now a recipe-respawnable process unit like the uvicorn portal)."""
            _sd = _archives_path if _has_archives else ""
            cmd = [sys.executable, "-m", "services.http_portal",
                   "--host", _web_host, "--port", str(_web_port),
                   "--data", base_dir, "--series", _series]
            if _sd:
                cmd += ["--static", _sd]
            return _spawn_portal(cmd, "httpd", scheme="http")

        def _launch_uvicorn_worker():
            """Launch the uvicorn/ASGI portal as a serve-only subprocess (recipe-respawnable
            process unit — same path as the httpd portal via _spawn_portal)."""
            cmd = [
                sys.executable, "-m", "api.portals.web_worker",
                "--host",   _web_host,
                "--port",   str(_web_port),
                "--data",   base_dir,
                "--series", _series,          # match the main tier (else worker defaults to seeds)
            ]
            if _asgi_static_dirs:
                for mount, path in _asgi_static_dirs:
                    cmd += ["--static", f"{mount}:{path}"]
            _scheme = "https" if _tls["active"] else "http"
            return _spawn_portal(cmd, "uvicorn", scheme=_scheme)

        # ── Double-launch safety net ──────────────────────────────────
        # The pid-file stop above handles the normal case. This catches the rest:
        # a portal left by a crash, or started another way, that the pid file does
        # not know about. If the serve port is still held — self-heal an orphaned
        # Akasha portal (stop it), or refuse to start a second instance and name
        # who holds the port. Either way the operator never kills a process by hand.
        _skip_portal = False
        if _port_in_use(_web_host, _web_port):
            _hpid, _hcmd = _port_holder(_web_port)
            if _hpid and ("web_worker" in _hcmd or "akasha" in _hcmd):
                _terminate_pid(_hpid)
                print(f"  [~] Freed port {_web_port} — stopped an orphaned Akasha "
                      f"portal (PID {_hpid}).", flush=True)
                time.sleep(0.3)
            else:
                _who = (f"PID {_hpid} ({(_hcmd.split() or ['?'])[0]})"
                        if _hpid else "another process")
                print(f"  [!] Port {_web_port} is already in use by {_who} — "
                      f"NOT starting a second portal.\n"
                      f"      Stop it, or start with a free port (AKASHA_PORT=…). "
                      f"Double-launch prevented.", flush=True)
                _skip_portal = True

        # ── Launch ────────────────────────────────────────────────────
        if not _skip_portal:
            # Both portals are serve-only SUBPROCESSES (AKASHA_SERVE_ONLY in their env): they
            # never run the boot-load, so this process stays the sole nucleus writer and the
            # portal starts almost immediately — no waiting out the first-boot load. It serves
            # reads while the ontology fills in (WAL → concurrent readers are safe); watch
            # progress with `onto.status`.
            #
            # One guard remains: on a RESTART the previous portal was just stopped, and its
            # port can linger a moment (TIME_WAIT / slow release). Launching instantly would
            # make the new portal hit EADDRINUSE, die, and show a false "Dead (Check logs)"
            # in `svc ls` while a sibling serves. Wait until the port is actually bindable
            # (returns at once when already free — NOT the old multi-minute load wait).
            if not _wait_port_bindable(_web_host, _web_port, timeout=12.0):
                print(f"  [~] Port {_web_port} still settling — starting the portal anyway "
                      f"(it will retry the bind).", flush=True)
            if _web_engine == "uvicorn":
                _launch_uvicorn_worker()
            else:
                _launch_http_portal()

        _mode_label = "archives/uvicorn" if _has_archives else _web_engine
        if not _skip_portal:
            log.info(f"Web portal ({_mode_label}) starting on {_web_host}:{_web_port}.")

    # ── Headless server / Cell daemon mode (--serve / --daemon) ───────
    # Keep the engine + portal running with NO interactive CLI — the correct shape
    # for a detached / persistent deployment (the Cell daemon, nohup, systemd). This
    # process OWNS the engine and its jobs; the local IPC socket (opened above) lets a
    # CLI client attach and, if needed, perform genesis over TRUST_LOCAL — so an
    # uninitialised cell is no longer stuck at anonymous reads. Block here until
    # SIGTERM (routed through graceful begin_shutdown()).
    if _server_mode:
        _tag = "Cell daemon" if args.daemon else "headless server"
        log.info("[Boot] %s mode (no CLI).", _tag)
        print(f"  [+] {_tag} — engine + portal serving; the local socket accepts a "
              f"CLI client. Stop: python akasha.py stop\n", flush=True)
        _portal_proc = _supervisor.get_proc("svc:web-portal")
        try:
            if _portal_proc is not None:
                _portal_proc.wait()          # portal subprocess (httpd or uvicorn)
            else:
                threading.Event().wait()     # no portal handle — block here
        except (KeyboardInterrupt, EOFError):
            pass
        return

    # ── MCP stdio transport (embedded fallback — no daemon was reachable) ──
    # The MCP JSON-RPC stream owns stdin/stdout; serve it directly over this process's engine.
    if args.mcp:
        from api.portals.mcp import run_mcp_stdio, TRUST_LOCAL
        try:
            run_mcp_stdio(live_gw, trust=TRUST_LOCAL)
        except (KeyboardInterrupt, EOFError):
            log.info("[Boot] MCP stdio server ended.")
        return

    # ── iOS/embedded: in-process web portal (thread on THIS engine) ───
    # The subprocess/daemon portal model is unusable under the a-Shell/Pyto sandbox
    # (EBADF on spawn), which is why httpd auto-launch regressed there when the portal
    # became subprocess-only. Serve it as a daemon THREAD on the SAME live_gw — single
    # writer preserved (no SplitGateway, no second engine, no subprocess). Set by the iOS
    # branch unless the user asked for a true CLI-only session (--stdio / AKASHA_NO_WEB).
    if getattr(args, "_inproc_web", False):
        try:
            from services.http_gateway import BaseWebService, portal_banner
            _ih = os.environ.get("AKASHA_HOST", "").strip() or getattr(args, "host", None) or "127.0.0.1"
            try:
                _ip = int(os.environ.get("AKASHA_PORT", "").strip() or 0) \
                    or getattr(args, "port", None) or _free_port(8000, _ih)
            except (TypeError, ValueError):
                _ip = _free_port(8000, _ih)
            _isd = _archives_path if _has_archives else None
            _svc = BaseWebService(gw=live_gw, port=_ip, host=_ih, static_dir=_isd)
            _ready = threading.Event()
            threading.Thread(target=_svc.start, kwargs={"ready_event": _ready},
                             daemon=True, name="inproc-httpd").start()
            if _ready.wait(timeout=10.0):
                for _line in portal_banner(_ih, _ip, scheme="http"):
                    print("  " + _line, flush=True)
            else:
                log.warning("[Portal] in-process web portal did not come up within 10s.")
        except Exception as _pex:
            log.warning("[Portal] in-process web portal unavailable (CLI continues): %s", _pex)

    # ── CLI — always foreground ───────────────────────────────────────
    from api.portals.stdio import run_cli
    try:
        run_cli(live_gw)
    except (KeyboardInterrupt, EOFError):
        log.info("[Boot] CLI ended (exit / disconnect / interrupt).")

    # Public deploy: leaving the CLI must NOT take the server down. When the
    # portal is a detached subprocess (uvicorn — start_new_session above), drop
    # it from the service registry so atexit's stop_all skips it, and return —
    # the portal keeps serving after this process exits and after SSH closes.
    # The operator's whole job is: run → genesis → exit. (httpd runs as a thread
    # and cannot outlive the process, so that path still stops on exit; use
    # --serve for a headless httpd deploy.)
    _is_public = (not args.stdio) and (_has_archives or _web_host in ("0.0.0.0", "::"))
    _portal_proc = _supervisor.get_proc("svc:web-portal")
    if _is_public and _portal_proc is not None and _portal_proc.poll() is None:
        # The base-ontology load runs in THIS process; if we exit before it
        # finishes (first boot), the detached portal would serve a half-loaded
        # graph and nothing would complete it. Wait for the restart sentinel
        # first — instant on a warm cell, so the operator just types `exit`.
        import glob as _glob
        _sent_glob = os.path.join(base_dir, "central", "sentinels", "*.done")
        if not _glob.glob(_sent_glob):
            print("  [*] Finishing base ontology load before detaching (first boot — one moment)…",
                  flush=True)
            _deadline = time.time() + 900
            while time.time() < _deadline and not _glob.glob(_sent_glob):
                time.sleep(3)
        _supervisor.release("svc:web-portal")              # detach — survives atexit stop_local
        log.info("[Boot] Portal detached on CLI exit (PID %s) — still serving.", _portal_proc.pid)
        print(f"\n  [+] Web portal still running on {_web_host}:{_web_port} "
              f"(PID {_portal_proc.pid}) — keeps serving after you disconnect.\n"
              f"      Re-run  python akasha.py  to restart it (auto-replaces this one).\n"
              f"      Or      python akasha.py stop  to stop it. No manual kill needed.\n",
              flush=True)
        return


if __name__ == "__main__":
    main()
