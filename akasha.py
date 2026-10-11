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
import time

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
_PROC_T0 = time.time()          # A53 — process-start reference for the `up=<s>` daemon-leaving line
# THE WRITER'S GIL SWITCH INTERVAL (frontend 09-28, needs platform 2). The writer daemon runs the
# single write path (JCL worker ↔ WriteQueue, fsync, WAL I/O — threads that release the GIL tens of
# times per step) beside the IPC pool's CPU-bound request threads. An I/O-bound thread that releases
# the GIL waits up to one switch interval to get it back from each CPU-bound thread (the convoy
# effect), so under a saturated IPC pool a 7 ms atom step took 1.4-1.7 s — 400 atoms in 990 s.
# Measured on a 200-step atom job beside four CPU-bound threads: 5 ms (CPython's default) → 1,376
# ms/step, 1 ms → 283 ms/step, while the CPU-bound threads lose ~10 %. 1 ms is the default here;
# AKASHA_GIL_SWITCH_MS overrides it (0.05-50). The daemon only: it is the process with the writer.
_GIL_SWITCH_WAS = None
if "--daemon" in sys.argv[1:]:
    try:
        _gil_ms = float(os.environ.get("AKASHA_GIL_SWITCH_MS", "").strip() or 1.0)
        if 0.05 <= _gil_ms <= 50.0:
            _GIL_SWITCH_WAS = sys.getswitchinterval()
            sys.setswitchinterval(_gil_ms / 1000.0)
    except Exception:
        _GIL_SWITCH_WAS = None


def _log_gil_switch() -> None:
    """One `[boot] gil switch_interval=…` line — called by the writer once it holds the boot lock."""
    if _GIL_SWITCH_WAS is None:
        return
    import logging as _lg_gil
    _lg_gil.getLogger("Akasha.Kernel").info(
        "[boot] gil switch_interval=%.2fms (was %.2fms) — the writer's I/O-bound threads get the "
        "GIL back from CPU-bound request threads this often (AKASHA_GIL_SWITCH_MS)",
        sys.getswitchinterval() * 1000.0, _GIL_SWITCH_WAS * 1000.0)


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

def _manifest_dirs(root: str) -> list:
    """The directories a launch must ensure exist, DECLARED in the package manifests (`dirs`) —
    the launcher names none of them (backend layout order 2026-09-20 §5). Falls back to the
    heart's own list only if no manifest can be read (a partially-extracted tree), so a boot is
    never blocked by a missing declaration."""
    import glob as _glob
    import json as _json
    found = [os.path.join(root, "lib", "akasha", "MANIFEST.json")]
    found += sorted(_glob.glob(os.path.join(root, "lib", "akasha", "*", "MANIFEST.json")))
    found += sorted(_glob.glob(os.path.join(root, "*", "MANIFEST.json")))
    dirs = []
    for mp in dict.fromkeys(found):
        try:
            with open(mp, encoding="utf-8") as fh:
                for rel in (_json.load(fh).get("dirs") or []):
                    if isinstance(rel, str) and rel and not os.path.isabs(rel) and ".." not in rel.split("/"):
                        if rel not in dirs:
                            dirs.append(rel)
        except (OSError, ValueError):
            continue
    return dirs or ["data", "data/cells", "data/central", "data/import", "data/export",
                    "env/models", "logs", "assets"]


def _ensure_dirs(root: str) -> None:
    for rel in _manifest_dirs(root):
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


def _setup_logging(root: str, is_cgi: bool, arm_fault: bool = True) -> None:
    import logging
    # F27-9 — arm faulthandler only for LONG-LIVED roles (daemon / portal / interactive CLI /
    # single-shot). A short guard `--tick` (the 5-min cron heal) converges and exits within a
    # second and does no native weave, yet each invocation appended a "=== faulthandler armed ==="
    # line — ~2050 lines/week of pure noise that buried any real dump. Skip arming for those runs;
    # the daemon a guard tick may spawn is a SEPARATE process that arms its own faulthandler.
    if arm_fault:
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
    # R9 — system.log is bounded (50 MB × 5), so a DEBUG flood or a long-lived writer can never fill a
    # tight VPS disk and take the single writer down. Rotation announces itself with a `[log] rotated`
    # line (see lib/harmonia/logger.py).
    from lib.harmonia import logger as _hlog
    os.makedirs(os.path.join(root, "logs"), exist_ok=True)
    fh = _hlog.rotating_handler(
        os.path.join(root, "logs", "system.log"), _lvl,
        logging.Formatter("%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s"))
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


def _log_reap(action: str, pid: int, caller: str, grace_s: float) -> None:
    """F60 §3.3 / A13(c) — the KILLER writes the record. Log one `[reap] <action> pid= caller= grace=`
    line via the process logger, and — when the killer is the serve-only PORTAL (a watchdog revive /
    replace sweep) — mirror it to system.log, because the portal's own logger writes web-portal.log
    so a watchdog-driven kill of the writer would otherwise be absent from the writer's log."""
    import logging as _lg
    line = "[reap] %s pid=%d caller=%s grace=%.1fs" % (action, pid, caller, grace_s)
    _log = _lg.getLogger("Harmonia.Boot")
    (_log.warning if action == "SIGKILL" else _log.info)(line)
    if os.environ.get("AKASHA_SERVE_ONLY", "").strip().lower() in ("1", "yes", "true", "on"):
        _system_log_append(_root, line)


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
        _caller = sys._getframe(1).f_code.co_name
    except Exception:
        _caller = "?"
    _grace_s = max(0, grace_ticks) * 0.1
    try:
        os.kill(pid, 15)                       # SIGTERM — graceful
    except ProcessLookupError:
        try: os.remove(pid_path)
        except OSError: pass
        return None
    except PermissionError:
        return None
    # A13(c) — this path (operator `stop`, both launcher replace sweeps) killed directly, bypassing
    # _terminate_pid, so no [reap] line was ever written. Emit it here too; the killer writes the record.
    _log_reap("SIGTERM", pid, _caller, _grace_s)
    if wait:                                    # let it release the port, then be firm
        for _ in range(grace_ticks):
            _t.sleep(0.1)
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                break
        else:
            try:
                os.kill(pid, 9)               # SIGKILL if it won't go
                _log_reap("SIGKILL", pid, _caller, _grace_s)
            except ProcessLookupError: pass
    try: os.remove(pid_path)
    except OSError: pass
    return pid


def _terminate_pid(pid: int, wait: bool = True, grace_ticks: int = 40) -> bool:
    """SIGTERM (then SIGKILL if it won't go within grace_ticks×0.1s) a pid. True if signalled.
    A writer daemon needs a longer grace than a portal so it can checkpoint before the SIGKILL —
    pass a larger grace_ticks for those (e.g. 500 ≈ 50s).

    F60 §3.3 — the KILLER writes the record (the victim cannot): each SIGTERM and any SIGKILL
    escalation logs to system.log with the caller's name, so a daemon's disappearance is always
    attributable to who reaped it rather than looking like a silent crash."""
    import time as _t, sys as _sys
    try:
        _caller = _sys._getframe(1).f_code.co_name
    except Exception:
        _caller = "?"
    _grace_s = max(1, grace_ticks) * 0.1
    try:
        os.kill(pid, 15)
    except (ProcessLookupError, PermissionError):
        return False
    # F60 §3.3 / A13(a) — the killer writes the record; _log_reap mirrors to system.log when the
    # killer is the serve-only portal (a watchdog revive) so the writer's own log shows it.
    _log_reap("SIGTERM", pid, _caller, _grace_s)
    if wait:
        for _ in range(max(1, grace_ticks)):
            _t.sleep(0.1)
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                return True
        try:
            os.kill(pid, 9)
            _log_reap("SIGKILL", pid, _caller, _grace_s)
        except ProcessLookupError:
            pass
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
    for sub in ("lib", "api", "services", "remote"):   # the whole behaviour-defining + served tree
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
    seed may stamp its own payload fingerprint), else the on-disk code fingerprint. This is the
    BANNER id (may carry a git SHA); the daemon-replace HANDSHAKE uses `_handshake_build_id`."""
    return (os.environ.get("AKASHA_BUILD_ID") or "").strip() or _code_build_id(root)


def _handshake_build_id(root: str) -> str:
    """D1 — the build identity for the daemon-replace HANDSHAKE, advertised by the daemon
    (AKASHA_HANDSHAKE_BUILD) AND computed disk-side by the launcher so both sides agree. A seed's
    baked `content_fingerprint` (a sha256 over the WHOLE payload manifest — code + ontology + config
    + static) when present, so a redeploy that changed only an .ak / config / asset (which the
    .py-only `_code_build_id` would miss) still replaces the running daemon; else the on-disk .py
    code fingerprint (dev checkout). Read DIRECTLY from akasha_build.json (not via akasha_build_stamp,
    which prefers live git and would never surface the seed's baked id on a checkout). Deliberately
    independent of AKASHA_BUILD_ID — that banner id can carry a git SHA / operator value that differs
    across launch paths and would thrash a current daemon (see the AKASHA_HANDSHAKE_BUILD note)."""
    try:
        import json as _json
        with open(os.path.join(root, "akasha_build.json"), encoding="utf-8") as _fh:
            _fp = (dict(_json.load(_fh)).get("content_fingerprint") or "").strip()
        if _fp:
            return _fp
    except Exception:
        pass
    return _code_build_id(root)


def _should_replace_daemon(running, disk_build) -> bool:
    """The one authoritative decision, shared by the client (_run_cell_client) and server
    (--serve/--daemon) attach paths: should THIS launch (carrying the on-disk code) STOP the
    already-answering Cell daemon and take over as the writer?

    F60 §4.1 — `running` is now the tri-state from `cell_ipc.ping_build`:
      ("ok", <build>)     — answered with a fingerprint → replace ONLY on a different build;
      ("no-build", None)  — answered but pre-handshake (strictly older) → replace;
      ("silent", None)    — no answer (timeout/refused) → do NOT replace. A busy or slow daemon must
                            not be killed on a missed ping; wait heartbeat-gated and leave the verdict
                            to the watchdog's advancing probe. (The old rule replaced a silent daemon,
                            conflating 'timed out' with 'no build' — that could evict a healthy writer.)
    Back-compat: a legacy string/None is still accepted (None/'' = no-build, a string = ok), so the
    existing decision eval and any older caller keep their contract. We still require disk_build to be
    known (a launcher that cannot fingerprint its own tree never evicts — no false takeover), and an
    identical build never replaces (no needless reload / thrash loop)."""
    if isinstance(running, tuple):
        status, running_build = (tuple(running) + (None, None))[:2]
    elif running:
        status, running_build = "ok", running
    else:
        status, running_build = "no-build", None
    if not disk_build:
        return False                         # unknown own build → never evict
    if status == "silent":
        return False                         # did not answer → not replaced (watchdog decides)
    if status == "no-build":
        return True                          # pre-handshake ⇒ strictly older ⇒ replace
    return running_build != disk_build       # ok ⇒ replace only on a different build


def _replace_decision(running, disk_build):
    """F60 §4.2 — the (should_replace, one-line decision string) for the log, so both replace paths
    record WHY they replaced / attached / waited. `running` is ping_build's tri-state tuple."""
    if isinstance(running, tuple):
        status, rbuild = (tuple(running) + (None, None))[:2]
    elif running:
        status, rbuild = "ok", running
    else:
        status, rbuild = "no-build", None
    replace = _should_replace_daemon(running, disk_build)
    if replace:
        verdict, reason = "replace", ("no-build" if status == "no-build" else "fingerprint")
    elif status == "silent":
        verdict, reason = "wait", "silent"
    else:
        verdict, reason = "attach", ("same-build" if status == "ok" else "unknown-disk")
    running_desc = rbuild if status == "ok" else status
    line = ("[seed] replace decision: running=%s disk=%s → %s reason=%s"
            % (running_desc or "?", disk_build or "?", verdict, reason))
    return replace, line


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
# Absolute upper bound (seconds) on how long a still-ADVANCING but heartbeat-stale daemon boot is
# allowed to run before it is reaped anyway. A legitimately slow B/C-scale load on a swap-thrashing
# VPS can starve the boot-heartbeat thread for minutes while genuinely progressing (CPU/major-fault
# advancing); we keep waiting on it rather than reaping into an infinite respawn storm — but a
# truly pathological boot must still terminate, so cap the advancing-wait generously (15 min).
_BOOT_HARD_CEILING_S = float(os.environ.get("AKASHA_BOOT_HARD_CEILING", "").strip() or 900)

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


def _daemon_serve_loop(portal_proc, log, poll_interval: float = 2.0) -> str:
    """A53 item 1 — the Cell daemon's MAIN-thread serve loop: park on the LIFECYCLE shutdown Event,
    NEVER on the boot portal's Popen.wait().

    The regression this fixes: the old code did `portal_proc.wait()` here, so when a SIBLING thread
    (the Supervisor health tick) reaped/replaced that first portal, wait() returned, main() returned,
    and atexit tore the WRITER down — the single nucleus writer vanished with no log line and the
    whole cell rebooted (振り出しに戻る). The writer's life is bound to a real shutdown signal, not to
    any one portal it happened to spawn. So we WATCH the boot portal with poll() (its exit is logged,
    Supervisor owns the respawn) but only the shutdown Event releases the loop. Returns the leave
    reason for the single `[Cell] daemon leaving` line. Extracted so it is unit-testable (item 7a)."""
    from lib.akasha import lifecycle as _ls_daemon
    portal_pid = getattr(portal_proc, "pid", None)
    watched = portal_proc is not None
    try:
        while not _ls_daemon.wait_or_shutdown(poll_interval):
            if watched and portal_proc is not None:
                rc = portal_proc.poll()
                if rc is not None:
                    log.info("[Cell] boot portal pid=%s exited status=%s — Supervisor owns its "
                             "respawn", portal_pid, rc)
                    watched = False               # stop polling a dead handle; do NOT exit
        return "stop rpc"                          # the Event was set by begin_shutdown / a stop
    except (KeyboardInterrupt, EOFError):
        return "signal:SIGINT"


def _pidfile_state(base_dir: str) -> str:
    """A53 item 6a — classify the Cell-daemon pidfile for a watchdog revive line: `missing` (no
    cell.pid), `stale` (a pid recorded but its /proc is gone / foreign / not a --daemon), or `live`
    (a real akasha --daemon). Lets the revive line name exactly WHAT it saw, so a revive is never a
    bare verdict. Never raises."""
    try:
        with open(_cell_pid_path(base_dir)) as fh:
            pid = int((fh.read() or "0").strip() or 0)
    except (OSError, ValueError):
        return "missing"
    if not pid:
        return "missing"
    return "live" if _daemon_process_alive(base_dir) else "stale"


def _proc_progress_sample(pid: int):
    """(cpu_ticks, major_faults) for `pid` from /proc/<pid>/stat, or None if unreadable.

    cpu_ticks = utime+stime (fields 14+15); major_faults = majflt (field 12) — the count of page
    faults that required disk/swap I/O. Robust to a `comm` containing spaces/parens: fields after
    the last ')' are space-split, so utime/stime/majflt are indexed from there. Linux /proc only."""
    try:
        with open(f"/proc/{pid}/stat", "rb") as fh:
            data = fh.read()
    except OSError:
        return None
    try:
        rparen = data.rfind(b")")
        rest = data[rparen + 2:].split()            # fields from #3 (state) onward
        # post-')' index: field N → rest[N-3]. majflt=#12→9, utime=#14→11, stime=#15→13
        majflt = int(rest[9])
        cpu = int(rest[11]) + int(rest[13])
        return cpu, majflt
    except (ValueError, IndexError):
        return None


def _daemon_advancing(pid: int, window: float = 2.5) -> bool:
    """True only if `pid` POSITIVELY advances over `window` seconds — CPU time increases OR major
    page-faults increase. This distinguishes a daemon that is SLOW-BUT-WORKING (a big index rebuild
    thrashing on swap, whose separate boot-heartbeat thread is starved so the heartbeat file looks
    stale) from one that is genuinely WEDGED (GIL deadlock / dead — no CPU, no faults). Reaping the
    former restarts a progressing boot and, because the replacement meets the same memory pressure,
    spins an infinite reap→respawn storm that itself exhausts RAM. Unknown (non-Linux / unreadable
    /proc) → False, preserving the prior ceiling behaviour where progress cannot be measured."""
    import time as _t
    a = _proc_progress_sample(pid)
    if a is None:
        return False
    _t.sleep(window)
    b = _proc_progress_sample(pid)
    if b is None:
        return False
    return b[0] > a[0] or b[1] > a[1]


def _daemon_serving_from_files(base_dir: str):
    """R1.1 (F28a) — FILESYSTEM-ONLY aliveness: return the live daemon pid iff files alone prove a
    daemon is SERVING this data dir (its recorded pid is a live akasha `--daemon` process AND it has
    published a bound socket endpoint), else None. NO ping — a swap-thrashing live writer misses the
    3 s ping window, and treating that miss as death is what spawned the ~40 ram-mode `series=seeds`
    clones. The endpoint descriptor is removed on a clean stop but survives a crash, so it is paired
    with the live-pid check (a crashed daemon fails the pid check → None → the caller cold-boots). A
    'serving (possibly busy)' verdict means DEFER; wedge-reaping is the watchdog's authority alone."""
    from api.portals import cell_ipc
    pid = _daemon_process_alive(base_dir)
    if pid is None:
        return None
    if cell_ipc.daemon_endpoint(base_dir) is None:
        return None
    return pid


def _reap_stale_local(base_dir: str, quiet: bool = True) -> int:
    """The `stop` collection, folded into the START path so a plain `python akasha.py` (or a seed
    re-extract) is SELF-SUFFICIENT — the operator never needs a separate `python akasha.py stop`
    first. Process management is the code's job, not two commands the user has to remember.

    Called only when NO healthy daemon is being attached to (cold start, or after a hung/mismatched
    daemon was cleared), so reaping is always safe — it never touches a daemon a client is about to
    attach to. Collects, in order: a stale/hung recorded Cell daemon (dead pid → no-op; hung →
    SIGTERM then SIGKILL), a stale recorded web portal, EVERY orphaned portal for this data dir, and
    EVERY orphaned WRITER (Cell) daemon for this data dir (re-parented to init when its predecessor
    crashed, still holding its nucleus + the live-telemetry feed-poll thread — the leak that made a
    reinstall/restart leave an OLD feed daemon running even without `stop`). The recorded writer is
    reaped first (graceful, full checkpoint grace) so the orphan sweep only ever finds true strays.
    Returns the count reaped. Never raises."""
    reaped = 0
    try:
        if _stop_recorded_portal(_cell_pid_path(base_dir), grace_ticks=400):
            reaped += 1
        if _stop_recorded_portal(os.path.join(base_dir, "web-portal.pid")):
            reaped += 1
        _orphans = _reap_leaked_portals(base_dir)
        reaped += len(_orphans or [])
        # Symmetric with the portal sweep, for the process that carries the feed poller: any
        # `akasha.py --daemon` writer for this data dir that survives here is a stale/orphan
        # predecessor (the recorded one is already gone), so reaping it is what folds the writer
        # side of `stop` into the START path — a plain re-run/reinstall no longer leaves an old
        # feed daemon behind. Safe: this function runs only when there is no healthy daemon to
        # attach to.
        _orphd = _reap_leaked_daemons(base_dir)
        reaped += len(_orphd or [])
        if reaped and not quiet:
            print(f"  [~] Cleaned {reaped} leftover process(es) from a prior run "
                  f"(no `stop` needed).", flush=True)
    except Exception as _exc:
        logging.getLogger("Harmonia.Boot").debug("[reap] pre-spawn cleanup: %s", _exc)
    return reaped


def _wait_for_daemon_socket(base_dir: str, deadline_s: float = None,
                            progress: bool = False) -> bool:
    """Block until an alive-but-booting Cell daemon binds its socket and answers sys.ping. Returns
    True as soon as one answers; False if the booting daemon dies, or goes WEDGED (boot heartbeat
    stale AND still no ping) — the caller then reaps + respawns.

    Heartbeat-gated (R4): while the boot heartbeat is FRESH the daemon is progressing, so it is
    NEVER timed out — this removes the RC4 false-positive of reaping a healthy-but-slow B-scale
    load on a slow VPS disk. The fixed ceiling (AKASHA_BOOT_WAIT, default 90 s) applies only as a
    fallback when no heartbeat file exists (an older daemon build that predates the heartbeat).

    progress=True prints a status line during the wait (the interactive attach path) so the brief
    pre-heartbeat spawn gap + the longer index-rebuild are never a silent pause — mirroring the
    spawn path's progress. Off by default so quiet / non-interactive callers stay silent."""
    import time as _t
    from api.portals import cell_ipc
    if deadline_s is None:
        deadline_s = float(os.environ.get("AKASHA_BOOT_WAIT", "").strip() or 90)
    start = _t.time()
    end = start + deadline_s
    said_spawning = False
    last_progress = start
    while True:
        if cell_ipc.ping(base_dir, timeout=2.0):
            return True
        if _daemon_process_alive(base_dir) is None:
            return False                            # it died while booting → caller respawns
        if _boot_heartbeat_fresh(base_dir):
            if progress and _t.time() - last_progress >= 15:
                last_progress = _t.time()
                print("  [*] Cell daemon is booting — rebuilding the memory index from disk "
                      "(%ds; a large store takes a few minutes)…" % int(_t.time() - start),
                      flush=True)
            _t.sleep(0.5)                           # progressing boot → wait, no ceiling-kill
            continue
        # No fresh heartbeat yet → the pre-touch spawn gap (interpreter start, imports, opening the
        # store) before the boot heartbeat begins. Say so once (~2 s in) so it never looks frozen.
        if progress and not said_spawning and (_t.time() - start) >= 2.0:
            said_spawning = True
            print("  [*] Cell daemon is spawning — loading the engine (a moment)…", flush=True)
        # Fixed ceiling reached with a STALE heartbeat. Before reporting 'not answering' (→ the caller
        # reaps + respawns), confirm the daemon is genuinely WEDGED and not merely slow: under heavy
        # memory pressure the boot-heartbeat THREAD is starved by swap-thrash while the daemon is
        # still doing real work, and reaping it there restarts a progressing boot into an infinite
        # reap→respawn storm. A process burning CPU or faulting pages in is WORKING — keep waiting,
        # bounded by a generous hard cap so a truly-stuck daemon is still reaped eventually.
        if _t.time() >= end:
            pid = _daemon_process_alive(base_dir)
            if (pid is not None and (_t.time() - start) < _BOOT_HARD_CEILING_S
                    and _daemon_advancing(pid)):
                if progress and _t.time() - last_progress >= 15:
                    last_progress = _t.time()
                    print("  [*] Cell daemon still loading under memory pressure "
                          "(%ds; heartbeat starved by swap, but the process is advancing)…"
                          % int(_t.time() - start), flush=True)
                end = _t.time() + deadline_s          # extend while it keeps advancing
                continue
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
        if _wait_for_daemon_socket(base_dir, wait_ceiling, progress=not quiet):
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


def _akasha_daemon_pids(base_dir: str):
    """(pid, cmdline) for every RUNNING Akasha WRITER (Cell) daemon bound to THIS data dir.

    The writer daemon is `python …/akasha.py --daemon …` (see _spawn_cell_daemon); it OWNS the
    nucleus WriteQueue AND hosts the live-telemetry feed-poll thread. Scoped to this deployment by
    the daemon's EFFECTIVE data dir — AKASHA_DATA_DIR from its /proc environ, else its cwd/data — so
    it can NEVER match a foreign cell or a different data dir on the same host; matched on
    `akasha.py --daemon` so it never touches a serve-only portal (that is _akasha_portal_pids) or a
    thin CLI client. Feed-poll threads live ONLY in a writer, so scanning these is the ONLY way to
    find an ORPHANED poller: a respawn-race or pre-reinstall writer that the run-dir no longer
    tracks (its pid is not the recorded svc:cell) keeps its feed thread running but is invisible to
    the run-dir cascade. Linux /proc only; [] elsewhere (best-effort, never fatal)."""
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
                raw = fh.read()
        except OSError:
            continue
        args = [a for a in raw.decode("utf-8", "replace").split("\x00") if a]
        if not args:
            continue
        # Precise, TOKEN-based match (not a substring): argv[0] is a python interpreter running a
        # script whose path ends in akasha.py, WITH a `--daemon` argument. This deliberately excludes
        # a `ps|grep "akasha.py --daemon"` (one quoted token, no python argv[0], no `--daemon` token)
        # and a `timeout … python akasha.py --daemon` wrapper (argv[0] is `timeout`, not python) — we
        # want the real writer process, never its launcher or an onlooker.
        if "python" not in os.path.basename(args[0]).lower():
            continue
        if "--daemon" not in args or not any(a.endswith("akasha.py") for a in args):
            continue
        cmd = " ".join(args)
        # Effective data dir of THAT process: explicit AKASHA_DATA_DIR wins, else <cwd>/data —
        # exactly how base_dir itself is derived, so the comparison is apples-to-apples.
        eff = None
        try:
            with open(f"/proc/{pid_s}/environ", "rb") as ef:
                for kv in ef.read().decode("utf-8", "replace").split("\x00"):
                    if kv.startswith("AKASHA_DATA_DIR="):
                        v = kv.split("=", 1)[1].strip()
                        if v:
                            eff = os.path.abspath(v)
                        break
        except OSError:
            pass
        if eff is None:
            try:
                eff = os.path.join(os.path.realpath(f"/proc/{pid_s}/cwd"), "data")
            except OSError:
                eff = None
        if eff is not None and eff != base_abs:
            continue                                    # a different cell / data dir → not ours
        out.append((pid, cmd.strip()))
    return out


def _reap_leaked_daemons(base_dir: str, keep_pids=(), grace_s: float = 8.0):
    """SIGTERM→(grace)→SIGKILL every Akasha WRITER daemon for THIS data dir except `keep_pids`
    (and self). The counterpart of _reap_leaked_portals for the process that carries the feed
    poller: it kills an ORPHANED writer — hence its orphaned poll thread — that the run-dir no
    longer tracks (a respawn-race survivor, or a pre-reinstall daemon). That orphan is the route by
    which `stop` / restart / reinstall used to leave an old feed daemon running (public nucleus
    frozen while the orphan wrote to a private cell).

    Unlike a serve-only portal, a writer holds nucleus write state, so each gets a GRACEFUL SIGTERM
    first (its handler runs begin_shutdown → checkpoint) and a generous SHARED grace before any
    SIGKILL — crash-stop is preserved (only an in-flight write can ever be lost). Returns the pids
    stopped. Best-effort; never raises."""
    import time as _t
    keep = set(keep_pids) | {os.getpid()}
    targets = [pid for pid, _cmd in _akasha_daemon_pids(base_dir) if pid not in keep]
    if not targets:
        return []
    signalled = []
    for pid in targets:                              # phase 1: SIGTERM all orphans at once
        try:
            os.kill(pid, 15)
            signalled.append(pid)
        except (ProcessLookupError, PermissionError):
            pass
    deadline = _t.time() + max(1.0, grace_s)         # phase 2: ONE shared checkpoint grace window
    while _t.time() < deadline:
        if not any(_pid_alive(p) for p in signalled):
            break
        _t.sleep(0.1)
    for pid in signalled:                            # phase 3: SIGKILL any straggler
        if _pid_alive(pid):
            try: os.kill(pid, 9)
            except (ProcessLookupError, PermissionError): pass
    return signalled


def _reap_orphans(base_dir: str, keep_pids=()) -> list:
    """The SHARED daemon-reclamation both `stop` AND a writer boot run: reclaim every ORPHANED
    Akasha process for this data dir — leaked serve-only PORTALS and leaked WRITER DAEMONS (respawn-
    race survivors, pre-reinstall processes the run-dir no longer tracks) — via graceful SIGTERM→
    grace→SIGKILL on /proc-scanned pids, EXCLUDING self (and `keep_pids`, e.g. a healthy daemon we
    are deferring to). Entirely code-side: NEVER a shell `pkill`/`killall`. This is why the operator
    is never asked to kill anything — a boot cleans up leaked predecessors exactly as `stop` does,
    closing the 'old daemon not killed → manual pkill' gap where a boot swept only portals, not the
    writer daemon that carries the feed poller + its ~GB engine. Returns the pids stopped."""
    reaped = list(_reap_leaked_portals(base_dir, keep_pids=keep_pids))
    reaped += list(_reap_leaked_daemons(base_dir, keep_pids=keep_pids))
    return reaped


def _reclaim_orphans_on_start(base_dir: str) -> list:
    """Auto-reclaim leaked predecessors at the start of ANY akasha launch, so the operator NEVER
    runs a Linux command (stop / pkill / ps / kill) — merely starting akasha cleans up.

    Reaps orphan WRITER daemons + orphan PORTALS for this data dir (respawn-race / pre-reinstall
    survivors the run-dir no longer tracks), but SPARES the currently-recorded daemon (cell.pid) and
    portal (web-portal.pid): convergence decides defer/replace/reap for THAT one, and a healthy
    daemon we are about to attach to must not be killed. Everything else same-data-dir is a genuine
    leak (a second writer / a re-parented portal) and is graceful-SIGTERM→grace→SIGKILL reclaimed —
    code-side, never a shell pkill. Instant when there are no orphans (nothing to signal). Returns
    the pids reclaimed. This is what makes 'attach to a healthy daemon' also clean up, not only a
    fresh writer boot."""
    # Stand down while ANY daemon is actively booting (fresh boot heartbeat): a mid-boot daemon may
    # not have recorded its cell.pid yet, so it is not in `keep` — reaping here would kill a healthy
    # boot. Convergence is the heartbeat-aware owner of the in-progress-boot case; let it run.
    if _boot_heartbeat_fresh(base_dir):
        return []
    keep = set()
    for _pp in (_cell_pid_path(base_dir), os.path.join(base_dir, "web-portal.pid")):
        try:
            with open(_pp) as _fh:
                _p = int((_fh.read() or "0").strip() or 0)
            if _p:
                keep.add(_p)
        except (OSError, ValueError):
            pass
    return _reap_orphans(base_dir, keep_pids=keep)


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
        nargs="?", const="pages", default=None,
        help=argparse.SUPPRESS,  # hidden: force a portal mode ('pages' — the application's pages root)
    )
    parser.add_argument(
        "cmd", nargs=argparse.REMAINDER,
        help="Headless single-shot command then exit",
    )
    return parser


def _cell_pid_path(base_dir: str) -> str:
    return os.path.join(base_dir, "central", "cell.pid")


# ── F36 / F47-6.3 — manual-restart marker (stop/start must not race the guard tick) ──────────
# `stop` takes the daemon down, then the operator (or the seed) starts a fresh one. In that gap the
# 5-min guard tick can see "no daemon answering" and cold-spawn its OWN — colliding with the manual
# start (two writers, the F12 double-death class). The `stop` handler drops this fsync'd marker; the
# guard tick DEFERS while it is fresh, and the daemon CLEARS it the moment it has booted. If the
# operator stops and never restarts, the marker TTLs out and the guard resumes its normal duty.
def _manual_restart_marker_path(base_dir: str) -> str:
    return os.path.join(base_dir, "central", "manual.restart")


def _manual_restart_ttl() -> float:
    try:
        return max(10.0, float(os.environ.get("AKASHA_MANUAL_RESTART_TTL", "120")))
    except (TypeError, ValueError):
        return 120.0


def _arm_manual_restart(base_dir: str) -> None:
    """Drop a fresh manual-restart marker (fsync'd) so a concurrent guard tick defers."""
    p = _manual_restart_marker_path(base_dir)
    try:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as fh:
            fh.write(str(time.time()))
            fh.flush()
            os.fsync(fh.fileno())
    except OSError:
        pass


def _manual_restart_active(base_dir: str) -> bool:
    """True if a manual restart was armed within the TTL window (the guard should stand down)."""
    p = _manual_restart_marker_path(base_dir)
    try:
        with open(p) as fh:
            ts = float((fh.read() or "0").strip() or "0")
    except (OSError, ValueError):
        return False
    if time.time() - ts <= _manual_restart_ttl():
        return True
    try:
        os.remove(p)                                    # stale → clear so the guard resumes duty
    except OSError:
        pass
    return False


def _clear_manual_restart(base_dir: str) -> None:
    try:
        os.remove(_manual_restart_marker_path(base_dir))
    except OSError:
        pass


def _silica_store_bytes(base_dir: str) -> int:
    """Total on-disk size (bytes) of the nucleus silica store — WAL logs + value files.

    Used to gate the embedded-CLI fallback: a multi-GB store must NOT be loaded into the CLI
    process when the daemon is unreachable (that OOMs and feeds the crash-loop). Best-effort;
    any error (missing dir, race) returns 0 so the gate simply does not trip."""
    total = 0
    silica_dir = os.path.join(base_dir, "central", "nucleus.db.silica")
    try:
        for root, _dirs, files in os.walk(silica_dir):
            for name in files:
                try:
                    total += os.path.getsize(os.path.join(root, name))
                except OSError:
                    pass
    except OSError:
        pass
    return total


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


def _restart_portal_after_content_load(base_dir: str) -> None:
    """F25b (primary): the serve-only portal opens its store snapshot + builds its IAM cache ONCE at
    daemon-start — there is no cross-process refresh. On a FRESH install, everything the writer commits
    after that open (the whole ontology load, and the Genesis admin's IAM record) is invisible to the
    portal: guest reads see an empty space and a correctly-signed login still 401s. Once the boot load
    has settled, restart the portal ONCE so it re-opens on the populated store (terminate → wait →
    respawn, with the F12b memory stagger — Supervisor.restart handles it).

    Guarded by a durable marker so it fires only on the boot that actually LOADS content (a fresh
    install's first successful load), never on subsequent boots — on those the data pre-dates the
    portal open, so its snapshot is already correct and no restart is needed."""
    import logging as _lg
    log = _lg.getLogger("Harmonia.Boot")
    marker = os.path.join(base_dir, "central", "sentinels", "portal_hydrated.done")
    try:
        if os.path.exists(marker):
            return
        from lib.harmonia import supervisor as _sv
        if not _sv.read_unit(base_dir, "svc:web-portal"):
            return                      # no serve-only portal to refresh (stdio / mcp / embedded)
        log.info("[Boot] first content load settled — restarting the serve-only portal once so it "
                 "reads the freshly-loaded store + IAM (F25b).")
        _sv.Supervisor(base_dir).restart("svc:web-portal")
    except Exception as exc:
        log.debug("[Boot] portal hydrate-restart skipped: %s", exc)
    finally:
        # Mark it handled either way: a failed restart still self-heals on the next boot (the data now
        # pre-dates the portal), and the marker guarantees we never double-restart.
        try:
            os.makedirs(os.path.dirname(marker), exist_ok=True)
            with open(marker, "w", encoding="utf-8") as fh:
                fh.write("done\n")
        except Exception:
            pass


def _onto_load_watcher(gw, base_dir: str) -> None:
    """Mount the ontology load onto the Supervisor plane as `job:onto-load`, so it appears in
    the unified `svc` / units view alongside the service processes. Daemon-side: a read-only
    poll of onto.status mirrored into the run-dir — the kernel hot path is untouched, and the
    Supervisor host (the daemon) reflects job state, which is where it belongs. Exits on
    completion or shutdown."""
    from lib.akasha import lifecycle as _lc
    from lib.harmonia import supervisor as _sv
    # F29-R11 — a job:onto-load must NEVER render "Active … PID=None" for weeks. It settles when the
    # load is fully complete OR when the CORE graph is done (relations loaded) but a pack is stuck
    # pending and no longer advancing (the "1/26 packs" ghost). Track the last packs_loaded and stamp
    # the job terminal once progress stalls, so a long-running daemon that never reboots still shows a
    # finished job rather than a perpetual Active row (the boot reconcile only fixes it at next boot).
    _last_loaded = None
    _stall = 0
    _STALL_LIMIT = 12                                   # ~1 min of no forward progress (12 × 5 s)
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
            _loaded = load.get("packs_loaded")
            if _loaded == _last_loaded:
                _stall += 1
            else:
                _stall = 0
                _last_loaded = _loaded
            # F57 §3 / F56-A5 — the loader finishing its LAST pack settles the unit as `complete`.
            # onto.status derives complete = (relations_done AND not pending); on a cell where the
            # global `_relations_*.done` sentinel is absent (the daemon's own relations-ready gate
            # uses a different signal — the semcache replan proved relations ready) that flag can
            # stay False for hours even though all 31 packs physically loaded, pinning the unit at
            # "31/31 packs Active". `packs_present` is the FULL registry count from the very first
            # poll (not a growing discovery), so "every present pack loaded, none pending" is an
            # unambiguous final-pack-landed signal with no transient-low race — treat it as complete.
            _present = load.get("packs_present")
            _all_packs = (_loaded is not None and _present is not None and _present > 0
                          and _loaded >= _present and not load.get("packs_pending"))
            _done = bool(load.get("complete")) or _all_packs
            # stuck ghost: core relations done but a pack stays pending past the stall window
            # (the "1/26 packs" case) — settle it too, marked as WHY (a stuck pack, not a clean load).
            _settled_stuck = (bool(load.get("relations_done")) and not load.get("complete")
                              and not _all_packs and _stall >= _STALL_LIMIT)
            state = "complete" if (_done or _settled_stuck) else "running"
            _sv.record_job(base_dir, "job:onto-load", state, {
                "packs_loaded":  _loaded,
                "packs_present": load.get("packs_present"),
                "packs_pending": load.get("packs_pending"),
                "atoms":         load.get("atoms"),
                # mark WHY it terminated so svc.ls / reconcile read a truthful state: a stuck pack is
                # "core loaded, N pack(s) unresolved", not a clean full completion.
                "settled_stuck": _settled_stuck or None,
            })
            if state == "complete":
                if not _settled_stuck:
                    # F25b: a genuine full completion — refresh the serve-only portal's stale snapshot
                    # ONCE (guarded so only a fresh install's first load triggers it).
                    _restart_portal_after_content_load(base_dir)
                else:
                    import logging as _lg
                    _lg.getLogger("Harmonia.Boot").info(
                        "[onto-load] core graph loaded; %s pack(s) still pending after stall — "
                        "marking job settled so it stops rendering Active (they reload next boot).",
                        load.get("packs_pending"))
                return
        if _lc.wait_or_shutdown(5.0):
            return


# ── Zombie reaper (fix B) ─────────────────────────────────────────────────────────
# A spawned Cell daemon is a DIRECT child of the launcher (Popen + start_new_session, no double-fork
# to init). Normally the launcher exits right after spawning, so the daemon re-parents to init and
# init reaps it when it dies. But an INTERACTIVE launcher (a CLI / a seed session) that stays open
# across a daemon REPLACEMENT outlives the daemon it spawned and never waitpid()s it — so the dead
# daemon lingers as a <defunct> zombie under that session (the "1 zombie process" seen after a
# redeploy). This tiny reaper poll()s each spawned-daemon child (poll() is the subprocess-native reap:
# waitpid WNOHANG, ECHILD-safe) so a replaced daemon is reaped within seconds, no zombie. It never
# touches other subprocesses (only its own tracked Popen objects). The full root fix — detach the
# daemon to init at spawn (double-fork) so NO launcher ever parents it — is deferred to a later turn.
import threading as _threading_reap
_TRACKED_DAEMON_PROCS = []
_TRACKED_DAEMON_LOCK = _threading_reap.Lock()
_DAEMON_REAPER_STARTED = False


def _reap_tracked_daemons() -> int:
    """One reap pass: poll each tracked spawned-daemon child; a dead one is reaped by poll() and
    dropped from tracking. Returns how many were reaped this pass. Testable; safe to call repeatedly."""
    with _TRACKED_DAEMON_LOCK:
        procs = list(_TRACKED_DAEMON_PROCS)
    reaped = 0
    for p in procs:
        try:
            dead = p.poll() is not None            # poll() reaps a dead child (no zombie), None if alive
        except Exception:
            dead = True                            # already reaped elsewhere (ECHILD) — drop it
        if dead:
            with _TRACKED_DAEMON_LOCK:
                if p in _TRACKED_DAEMON_PROCS:
                    _TRACKED_DAEMON_PROCS.remove(p)
            reaped += 1
    return reaped


def _track_daemon_proc(proc) -> None:
    """Track a spawned Cell-daemon Popen so the reaper waitpid()s it if it dies while this launcher is
    still alive. Starts the reaper thread once (daemon thread → dies with the launcher, at which point
    any surviving daemon re-parents to init anyway)."""
    global _DAEMON_REAPER_STARTED
    if proc is None:
        return
    with _TRACKED_DAEMON_LOCK:
        _TRACKED_DAEMON_PROCS.append(proc)
        if _DAEMON_REAPER_STARTED:
            return
        _DAEMON_REAPER_STARTED = True

    def _loop():
        import time as _t
        while True:
            _t.sleep(5)
            try:
                _reap_tracked_daemons()
            except Exception:
                pass

    _threading_reap.Thread(target=_loop, name="daemon-reaper", daemon=True).start()


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
    # F60 §1 — a WRITER is never serve-only. Build the child env with _writer_env() (portal-role keys
    # stripped, deployment.env re-applied) so a revive spawned from the portal (watchdog / health-tick)
    # never inherits AKASHA_SERVE_ONLY. §4.3 — stamp who spawned it so the child's boot [seed] line
    # can say spawned_by=…; a portal-role parent (SERVE_ONLY in its own env) means a watchdog revive.
    _wenv = _writer_env(root)
    _portal_hosted = os.environ.get("AKASHA_SERVE_ONLY", "").strip().lower() in ("1", "yes", "true", "on")
    _wenv["AKASHA_SPAWNED_BY"] = "watchdog" if _portal_hosted else "launcher"
    try:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        from lib.harmonia import logger as _hlog
        _hlog.rotate_if_big(log_path)     # R9 — bound the daemon redirect at each (re)launch
        fh = open(log_path, "a")
        proc = _sp.Popen(cmd, stdout=fh, stderr=_sp.STDOUT, cwd=root,
                         start_new_session=True, env=_wenv)
    except Exception as exc:
        log.error("[Cell] failed to spawn daemon: %s", exc)
        if _portal_hosted:                       # §3.2 — a portal-hosted spawn logs to web-portal.log;
            _system_log_append(root, f"[Cell] failed to spawn writer daemon: {exc}")   # mirror to system.log
        return False
    if _portal_hosted:
        _system_log_append(root, "[Cell] spawned writer daemon (from portal/watchdog) pid=%d argv=%s"
                           % (proc.pid, " ".join(cmd[1:])))

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
    _start = _t.time()
    _end = _start + _ceiling
    _proc_gone_since = None
    _last_progress = _t.time()
    _said_spawning = False
    _gave_up = False
    while True:
        # Check the SOCKET first: attach to whichever daemon binds it, not necessarily the one WE
        # spawned. A restart can spawn a daemon that correctly DEFERS to a sibling already booting.
        if cell_ipc.ping(base_dir, timeout=2.0):
            _say("[+] Cell daemon online.")
            _track_daemon_proc(proc)   # reap it if it later dies while THIS launcher stays alive (no zombie)
            return True
        # A FRESH heartbeat (from our proc OR a sibling we deferred to) means the boot is
        # progressing → wait with NO ceiling. Checked BEFORE the proc-exit grace so a deferred-to
        # sibling that is still advancing is honoured too.
        if _boot_heartbeat_fresh(base_dir):
            if _t.time() - _last_progress >= 15:
                _last_progress = _t.time()
                _elapsed = int(_t.time() - (_end - _ceiling))
                _say(f"[*] Cell daemon is booting — rebuilding the memory index from disk "
                     f"({_elapsed}s; a large store takes a few minutes)…")
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
        # Alive, not answering, and NO fresh heartbeat yet → the pre-touch startup gap: the daemon
        # process is spawning (interpreter start, imports, opening the store) BEFORE it begins the
        # boot heartbeat + index rebuild. Say so once (~2 s in) so this brief silent pause shows a
        # status line instead of looking frozen; the "rebuilding the memory index" progress takes
        # over as soon as the heartbeat goes live.
        if not _said_spawning and (_t.time() - _start) >= 2.0:
            _said_spawning = True
            _say("[*] Cell daemon is spawning — loading the engine (a moment)…")
        if _t.time() >= _end:
            # Ceiling reached with a STALE heartbeat. Do NOT reap a daemon that is still ADVANCING
            # (CPU / major-faults progressing) — under memory pressure the heartbeat thread is
            # starved by swap-thrash while the boot genuinely progresses, and reaping it restarts a
            # working boot into an infinite reap→respawn storm. Keep waiting while it advances,
            # bounded by a generous hard cap so a truly-stuck boot is still reaped.
            _pid = _daemon_process_alive(base_dir)
            if (_pid is not None and (_t.time() - _start) < _BOOT_HARD_CEILING_S
                    and _daemon_advancing(_pid)):
                if _t.time() - _last_progress >= 15:
                    _last_progress = _t.time()
                    _say("[*] Cell daemon still loading under memory pressure "
                         "(%ds; heartbeat starved by swap, but the process is advancing)…"
                         % int(_t.time() - _start))
                _end = _t.time() + _ceiling           # extend while it keeps advancing
                continue
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

    # CLEAN SLATE ON BUILD CHANGE (no operator step): if the code on disk changed since the daemon
    # that owns this data dir last started — a fresh seed was extracted — the OLD world (a possibly
    # crash-looping daemon, its portal, and any guardian-respawned orphans) must be swept BEFORE we
    # bring up the new writer, or the survivors fight it (the two-writers crash). This uses the
    # persisted running-build marker, so it works even when the old daemon is DEAD and cannot be
    # pinged — closing the gap where a crash-loop kept the old code alive across a redeploy. The
    # version handshake below still covers a healthy old daemon that is answering.
    try:
        _disk_now = _handshake_build_id(root)
        _mk = os.path.join(base_dir, "central", "running_build")
        _prev_build = None
        try:
            with open(_mk) as _mf:
                # running_build is "<fp> <pid>" (F60 §4.3 added the pid); the fp is the first token.
                # Back-compat: an old fp-only file has just the one token.
                _prev_build = (_mf.read().strip().split() or [""])[0]
        except OSError:
            _prev_build = None
        if _prev_build and _prev_build != _disk_now:
            print("  [~] A newer build is on disk — sweeping the previous Cell daemon(s) + portal(s) "
                  "so this code runs cleanly (no manual stop needed)…", flush=True)
            _reap_leaked_daemons(base_dir)
            _reap_leaked_portals(base_dir)
            _reap_stale_daemon(base_dir)          # clear the recorded (now-dead) descriptor too
            try:
                os.remove(_mk)                    # the fresh daemon rewrites it on boot
            except OSError:
                pass
    except Exception as _sweep_exc:
        log.debug("[Cell] build-change sweep skipped: %s", _sweep_exc)

    # F27-3 — attach with a LONGER ping timeout + one retry before concluding the daemon is
    # absent/booting. A fully-online daemon under a heavy boot I/O storm can miss a short (3 s)
    # probe; falling straight into the convergence path then prints a false "booting" line and can
    # spawn a redundant daemon that then defers. If the pid file names a LIVE process but the ping
    # times out, say what is actually true (up but slow) and retry, instead of treating it as gone.
    _attached = cell_ipc.ping(base_dir, timeout=5.0)
    if not _attached and _daemon_process_alive(base_dir) is not None:
        print("  [*] Cell daemon is up but slow to respond (heavy I/O?) — retrying…", flush=True)
        _attached = cell_ipc.ping(base_dir, timeout=5.0)
    if _attached:
        # A daemon ANSWERS. VERSION HANDSHAKE: a re-extracted seed / pulled repo boots akasha.py
        # argument-less and lands HERE — it would otherwise attach to the running daemon and run
        # its tests on that daemon's (possibly OLD) code. If the on-disk build differs, REPLACE
        # the daemon so the new code becomes the writer; if it matches, fast-attach as before
        # (no needless ontology reload — the requirement is 'replace on code change', not
        # 'reload on every run'). A daemon that answers but reports NO build predates the handshake
        # (strictly older) and is ALSO replaced — see _should_replace_daemon (closes the no-build
        # permanent trap that left a pre-handshake writer un-replaceable by any git pull/reinstall).
        _disk_build = _handshake_build_id(root)      # D1: full-payload fingerprint on a seed, else code content
        _running_build = cell_ipc.ping_build(base_dir)
        _replace, _decision = _replace_decision(_running_build, _disk_build)
        # §4.2 into system.log; A12 — the attach (same-build) case fires every cron-heal tick
        # (~5 min, ~288/day of pure noise), so keep the line but demote attach to DEBUG; a replace
        # or a wait (silent daemon) stays INFO.
        (log.info if (_replace or "→ wait" in _decision) else log.debug)("%s", _decision)
        if _replace:
            print("  [~] A newer build is on disk — replacing the running Cell daemon so this "
                  "code runs (one-time ontology reload)…", flush=True)
            _stop_recorded_portal(_cell_pid_path(base_dir), grace_ticks=500)   # old daemon: 45s+ grace
            # Also clear the old portal so the fresh daemon binds a clean port (the new daemon's
            # _bind_unix already unlinks a stale IPC socket).
            _stop_recorded_portal(os.path.join(base_dir, "web-portal.pid"))
            _reap_leaked_portals(base_dir)
            # CLEAN SLATE on a build change (no operator step): sweep EVERY Akasha writer daemon for
            # this data dir, not just the recorded one. A crash-looping / guardian-respawned OLD
            # daemon (orphan pid) would otherwise survive the upgrade and fight the new writer (the
            # two-writers crash). The new seed must one-shot the old world; reap them all now.
            _reap_leaked_daemons(base_dir)
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
            # QUOTE each argv token before joining: nargs=REMAINDER hands us the shell's already-split
            # tokens, but run_single_shot re-parses the string with shlex. A bare " ".join then re-splits
            # a value containing spaces (e.g. fixture_policy="no synthetic artworks; …" → truncated to
            # "no"). shlex.quote makes the round-trip lossless. (CLI-first: single-shot == interactive.)
            import shlex as _shlex
            print(run_single_shot(" ".join(_shlex.quote(t) for t in args.cmd), gw))
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


# ── 7c. Outer guardian (F12a) ───────────────────────────────────────────────────
# The mutual daemon↔portal guardianship has one gap: when OOM takes BOTH in a single respawn
# window there is no reviver left (the F12 7.5-hour outage). The outer guardian closes it — an
# OS-level systemd service (Restart=on-failure) or a cron tick that runs convergence and exits.
# It is trivially safe: a healthy system defers (exit 0, touches nothing); a dead/wedged one
# converges to one daemon + portal (R1–F9). Nothing is ever installed implicitly.
_GUARD_UNIT_PATH = "/etc/systemd/system/akasha.service"
_GUARD_CRON_TAG = "# akasha-guard"

def _guard_log(root: str, msg: str) -> None:
    import time as _t
    try:
        p = os.path.join(root, "logs", "system.log")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "a") as fh:
            fh.write(f"{_t.strftime('%Y-%m-%d %H:%M:%S', _t.localtime())} [guard] {msg}\n")
    except OSError:
        pass

def _guard_systemd_unit(py: str, entry: str, root: str, daemon_flags) -> str:
    _flags = (" " + " ".join(daemon_flags)) if daemon_flags else ""
    # Type=simple, NOT forking: `akasha.py --daemon` runs the daemon in the FOREGROUND (it does not
    # double-fork), so systemd tracks that process directly and Restart=on-failure restarts it on
    # death. R2's truthful exit codes keep this correct (a healthy defer exits 0, a real failure
    # non-zero) — though under systemd the daemon is the sole instance, so it never defers.
    return ("[Unit]\n"
            "Description=Akasha Cell daemon (outer guardian)\n"
            "After=network-online.target\nWants=network-online.target\n\n"
            "[Service]\nType=simple\n"
            f"WorkingDirectory={root}\n"
            f"ExecStart={py} {entry} --daemon{_flags}\n"
            "Restart=on-failure\nRestartSec=30\n\n"
            "[Install]\nWantedBy=multi-user.target\n")

def _guard_cron_line(py: str, entry: str, root: str, daemon_flags) -> str:
    _flags = (" " + " ".join(daemon_flags)) if daemon_flags else ""
    log = os.path.join(root, "logs", "cron-heal.log")
    return (f"*/5 * * * * cd {root} && {py} {entry} guard --tick{_flags} "
            f">> {log} 2>&1  {_GUARD_CRON_TAG}")

def _guard_read_crontab():
    import subprocess as _sp
    try:
        r = _sp.run(["crontab", "-l"], capture_output=True, text=True)
        return r.stdout if r.returncode == 0 else ""
    except (FileNotFoundError, OSError):
        return None                                   # no crontab on this host

def _guard_write_crontab(text: str) -> bool:
    import subprocess as _sp
    try:
        return _sp.run(["crontab", "-"], input=text, text=True).returncode == 0
    except (FileNotFoundError, OSError):
        return False

def _guard_tick(root: str, base_dir: str, daemon_flags) -> int:
    """Run convergence ONCE and exit — the cron guardian's periodic action. Logs a heal line only
    when it actually revived something (convergence 'spawned', not 'answering').

    Fully-automatic upgrade (principle: everything from the seed, zero operator steps): if a daemon
    is answering but its RUNNING build differs from the ON-DISK build — a newer seed was extracted —
    replace it here, so the guardian brings the NEW code up on its next 5-min tick WITHOUT anyone
    re-running the seed or touching the process. Mirrors the CLI-client version handshake
    (_run_cell_client); the shared reap paths carry the writer's checkpoint grace."""
    # F36/F47-6.3 — an operator stop/start is in flight: stand down so we don't race a second daemon
    # into the gap. The manual start (or a later tick, once the marker ages out) brings it up.
    if _manual_restart_active(base_dir):
        _guard_log(root, "manual restart in progress — guard tick deferring")
        return 0
    try:
        args = _build_arg_parser().parse_args(["--daemon"] + list(daemon_flags))
    except SystemExit:
        args = _build_arg_parser().parse_args(["--daemon"])   # bad passthrough → bare daemon
    try:
        from api.portals import cell_ipc as _cipc
        if _cipc.ping(base_dir, timeout=5.0):
            _disk = _handshake_build_id(root)
            _running = _cipc.ping_build(base_dir)
            if _should_replace_daemon(_running, _disk):
                _guard_log(root, f"newer build on disk ({_disk}) — replacing daemon "
                                 f"(was {_running or 'pre-handshake'})")
                _stop_recorded_portal(_cell_pid_path(base_dir), grace_ticks=500)  # 45s+ checkpoint grace
                _stop_recorded_portal(os.path.join(base_dir, "web-portal.pid"))
                _reap_leaked_portals(base_dir)
                # → falls into convergence(spawn=True) below, which cold-spawns the NEW code.
    except Exception as _upx:                                 # a build-check hiccup must never
        _guard_log(root, f"build-replace check skipped: {_upx}")   # skip the heal tick itself
    state = _converge_daemon(root, base_dir, args, spawn=True, quiet=True)
    if state == "spawned":
        _guard_log(root, "revived cell daemon (convergence: spawned)")
    return 0 if state in ("answering", "spawned") else 1

def _run_guard(argv, root: str, base_dir: str) -> int:
    import subprocess as _sp
    action = "install"
    passthrough = []
    for a in argv:
        _s = a.lstrip("-")
        if _s in ("install", "status", "remove", "tick"):
            action = _s
        else:
            passthrough.append(a)                     # daemon flags to embed (--server uvicorn …)
    py = os.path.abspath(sys.executable)
    entry = os.path.join(root, "akasha.py")

    if action == "tick":
        return _guard_tick(root, base_dir, passthrough)

    have_systemd = os.path.isdir("/run/systemd/system")

    if action == "status":
        found = False
        if os.path.isfile(_GUARD_UNIT_PATH):
            print(f"  [guard] systemd unit present: {_GUARD_UNIT_PATH}")
            for _q in ("is-enabled", "is-active"):
                try:
                    r = _sp.run(["systemctl", _q, "akasha.service"], capture_output=True, text=True)
                    print(f"          {_q}: {(r.stdout or r.stderr).strip()}")
                except (FileNotFoundError, OSError):
                    pass
            found = True
        _ct = _guard_read_crontab()
        if _ct and _GUARD_CRON_TAG in _ct:
            print("  [guard] crontab guardian present (every 5 min).")
            found = True
        if not found:
            print("  [guard] no guardian installed. Install with:  python akasha.py guard "
                  f"({'systemd' if have_systemd else 'cron'} on this host).")
        return 0

    if action == "remove":
        removed = False
        if os.path.isfile(_GUARD_UNIT_PATH):
            try:
                _sp.run(["systemctl", "disable", "--now", "akasha.service"], check=False)
                os.remove(_GUARD_UNIT_PATH)
                _sp.run(["systemctl", "daemon-reload"], check=False)
                print(f"  [guard] removed systemd guardian {_GUARD_UNIT_PATH}.")
                removed = True
            except (PermissionError, FileNotFoundError, OSError):
                print(f"  [guard] cannot remove {_GUARD_UNIT_PATH} (need root):  "
                      f"sudo systemctl disable --now akasha.service && sudo rm {_GUARD_UNIT_PATH}")
        _ct = _guard_read_crontab()
        if _ct and _GUARD_CRON_TAG in _ct:
            _new = "".join(l + "\n" for l in _ct.splitlines() if _GUARD_CRON_TAG not in l)
            if _guard_write_crontab(_new):
                print("  [guard] removed crontab guardian.")
                removed = True
        if not removed:
            print("  [guard] nothing to remove.")
        return 0

    # ── install ──
    if have_systemd:
        unit = _guard_systemd_unit(py, entry, root, passthrough)
        try:
            with open(_GUARD_UNIT_PATH, "w") as fh:
                fh.write(unit)
        except (PermissionError, OSError):
            print("  [guard] systemd is present but writing the unit needs root. Run as root:")
            print(f"      sudo tee {_GUARD_UNIT_PATH} >/dev/null <<'UNIT'\n{unit.rstrip()}\nUNIT")
            print("      sudo systemctl daemon-reload && sudo systemctl enable --now akasha.service")
            return 1
        _sp.run(["systemctl", "daemon-reload"], check=False)
        _sp.run(["systemctl", "enable", "--now", "akasha.service"], check=False)
        print(f"  [guard] installed systemd guardian → {_GUARD_UNIT_PATH}")
        print("          enabled + started · Restart=on-failure, RestartSec=30")
        print("          status: python akasha.py guard --status   ·   remove: guard --remove")
        print("  ⚠ If you also start the daemon by hand, stop it first (python akasha.py stop) so "
              "systemd owns the single instance.")
        return 0

    _ct = _guard_read_crontab()
    if _ct is None:
        print("  [guard] no systemd and no crontab on this host. Run  python akasha.py guard --tick "
              " from your own scheduler every ~5 min (it converges and exits).")
        return 1
    if _GUARD_CRON_TAG in _ct:
        print("  [guard] crontab guardian already installed (every 5 min).")
        return 0
    line = _guard_cron_line(py, entry, root, passthrough)
    _new = (_ct if not _ct or _ct.endswith("\n") else _ct + "\n") + line + "\n"
    if _guard_write_crontab(_new):
        print("  [guard] installed crontab guardian (every 5 min):")
        print(f"      {line}")
        print("          remove: python akasha.py guard --remove")
        return 0
    print("  [guard] failed to write crontab.")
    return 1


def _raise_fd_limit():
    """R2.1 (F28b) — raise the open-file soft limit to min(hard, 65536) at start. The guest pool
    (up to 128 slots) each opens a PRIVATE silica cortex store, and a silica store is a MULTI-FILE
    directory (one WAL per bank + a coordinator log ⇒ ~10–25 FDs each). At ~50–60 concurrent guests
    that blows a default 1024 ulimit — the live `Errno 24 Too many open files` at `guest:pool:56`
    cell open. Reclaim is clean, so this is concurrency headroom, not a leak. Best-effort and never
    fatal: non-POSIX / a refused raise leaves the process running on the inherited limit. Returns
    (soft_before, soft_after) or None."""
    try:
        import resource
    except Exception:
        return None
    try:
        soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        target = hard if hard != resource.RLIM_INFINITY else 65536
        target = min(target, 65536)
        if soft != resource.RLIM_INFINITY and (target == resource.RLIM_INFINITY or soft < target):
            resource.setrlimit(resource.RLIMIT_NOFILE, (target, hard))
            new_soft, _ = resource.getrlimit(resource.RLIMIT_NOFILE)
            return (soft, new_soft)
    except (ValueError, OSError):
        return None
    return (soft, soft)


def _set_oom_score_adj(value: int) -> bool:
    """F31-2/F44-A3 — bias the Linux OOM killer's victim selection for THIS process. The writer
    daemon owns the single WriteQueue + the whole engine; if a kill ever comes it must take a
    RESTARTABLE process (a portal, a guest subprocess) instead. So the daemon sets a PROTECTIVE
    (negative) adj and the portals a SACRIFICIAL (positive) one. dmesg showed the writer killed at
    oom_score_adj 0 — never biased. Best-effort: a negative value needs privilege (root on the VPS);
    if the write is refused (non-root, non-Linux) it is a silent no-op. Returns True if it stuck."""
    try:
        with open("/proc/self/oom_score_adj", "w") as f:
            f.write(str(int(value)))
        return True
    except (OSError, ValueError):
        return False


# F60 §1 — env keys the PORTAL spawn injects (akasha.py :3085–3090 / :3114 + web_worker) that mark a
# process as serve-only / portal-role. A WRITER (cell daemon) must NEVER inherit them: a writer spawned
# FROM a portal (watchdog revive, health-tick respawn) would otherwise boot with AKASHA_SERVE_ONLY set
# and run crippled — no health heartbeat, no replan (the daemon-#2 incident).
_PORTAL_ROLE_ENV_KEYS = ("AKASHA_SERVE_ONLY", "AKASHA_DAEMON_ARGV")


def _system_log_append(root: str, msg: str) -> None:
    """F60 §3.2 — append one line to system.log directly, bypassing the process's own logging config.
    Used so a watchdog/health-tick spawn running INSIDE the serve-only portal (whose logger writes
    web-portal.log, not system.log) still records its [Cell] lifecycle lines where the writer's own
    log delivery will show them. Best-effort, never raises."""
    import time as _tl
    try:
        p = os.path.join(root, "logs", "system.log")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        stamp = _tl.strftime("%Y-%m-%d %H:%M:%S", _tl.localtime())
        with open(p, "a", encoding="utf-8") as fh:
            fh.write(f"{stamp} | Harmonia.Boot        | INFO     | {msg}\n")
    except OSError:
        pass


def _scrub_daemon_serve_only(is_daemon: bool, log=None) -> bool:
    """F60 §1.2 — a `--daemon` process is a WRITER; a writer is NEVER serve-only. If AKASHA_SERVE_ONLY
    leaked into its env, clear it BEFORE the kernel is built so the writer-role gates see a writer.
    Returns True if it cleared one. Extracted from main() so it is unit-testable (A13(b))."""
    if is_daemon and os.environ.get("AKASHA_SERVE_ONLY", "").strip().lower() in ("1", "yes", "true", "on"):
        if log is not None:
            log.error("[Boot] --daemon started with AKASHA_SERVE_ONLY set — a writer is never "
                      "serve-only; clearing it")
        os.environ.pop("AKASHA_SERVE_ONLY", None)
        return True
    return False


def _writer_env(root: str) -> dict:
    """The environment for a WRITER (cell daemon) spawn: os.environ MINUS every portal-role key,
    then the canonical deployment.env re-applied exactly as the launcher applies it (setdefault). Use
    this for every writer spawn — launcher, watchdog revive, health-tick respawn — so a writer is
    never accidentally serve-only because the process that spawned it was a portal (F60 §1)."""
    env = os.environ.copy()
    for k in _PORTAL_ROLE_ENV_KEYS:
        env.pop(k, None)
    _load_deployment_env(root, target=env)          # re-apply canonical config onto the stripped env
    return env


def _load_deployment_env(root: str, target: dict = None) -> list:
    """R1.2 (F28a) — SINGLE env source. Read `<root>/env/deployment.env` (KEY=VALUE, `#`
    comments, optional `export `) into os.environ at the very start of every launch, so cron /
    manual / systemd starters can NEVER diverge again. The divergence was concrete: the VPS
    logs showed ~40 clones each tagged `series=seeds` with no AKASHA_SERIES and no value-mode env —
    a cron/guard heal line that ran akasha WITHOUT the deployment's env, so it booted the wrong
    series (and all-RAM values) beside the real writer.

    Semantics: `setdefault` — an EXPLICITLY-exported var still wins (a one-off override is
    honoured), but a starter with an empty environment inherits the deployment's canonical
    values. Best-effort and never fatal: a missing file is normal (a plain checkout), a malformed
    line is skipped. Returns the list of keys it set (for a one-line boot log)."""
    tgt = os.environ if target is None else target      # F60 §1 — apply onto a stripped writer env too
    path = os.path.join(root, "env", "deployment.env")
    set_keys = []
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for raw in fh:
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("export "):
                    line = line[len("export "):].lstrip()
                if "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if not k:
                    continue
                if k not in tgt:
                    tgt[k] = v
                    set_keys.append(k)
    except (FileNotFoundError, OSError):
        return set_keys
    return set_keys


def _deployment_env_names(root: str) -> list:
    """Every KEY `<root>/env/deployment.env` sets, whether or not it was applied (an exported var
    wins over the file, so `_load_deployment_env`'s list can be shorter). [] with no file."""
    names = []
    try:
        with open(os.path.join(root, "env", "deployment.env"), "r", encoding="utf-8") as fh:
            for raw in fh:
                line = raw.strip()
                if line.startswith("export "):
                    line = line[len("export "):].lstrip()
                if line and not line.startswith("#") and "=" in line:
                    k = line.split("=", 1)[0].strip()
                    if k and k not in names:
                        names.append(k)
    except OSError:
        pass
    return names


def _env_refused(file_names: list) -> list:
    """The purge order §4.5 — every AKASHA_* variable set for this process (exported, or in
    `env/deployment.env`) that NO manifest declares. A declared variable is a deployment fact; an
    undeclared one is a switch nothing reads or a name a package forgot to declare, and both are
    refused by name rather than silently ignored. [] when every name is declared."""
    from lib.akasha.api import manifest as _mf
    names = {k for k in os.environ if k.startswith(_mf.ENV_PREFIX)} | set(file_names or [])
    return _mf.env_undeclared(names)


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

    # R1.2 — load the single deployment env source BEFORE any env-dependent decision (series,
    # backend, index mode), so a cron/guard/systemd starter cannot diverge from the operator's
    # canonical config. Best-effort; explicit env still wins (setdefault).
    _dep_env_keys = _load_deployment_env(_root)

    # R2.1 — raise the open-file limit up front (before the guest pool opens any private silica
    # cortex) so concurrent guests cannot hit `Errno 24 Too many open files`. Safe everywhere.
    _fd_raise = _raise_fd_limit()

    # A short-lived guard/stop run defers-and-exits — do not arm faulthandler for it (F27-9).
    _short_lived = (not _is_cgi and len(sys.argv) >= 2 and sys.argv[1] in ("guard", "stop"))
    _setup_logging(_root, _is_cgi, arm_fault=not _short_lived)
    log = logging.getLogger("Harmonia.Boot")
    # F60 §3.4 — carry pid + argv so a DOUBLE invocation (two boot lines seconds apart) is visible in
    # the log, and each boot is attributable to its process.
    log.info("Akasha boot sequence initiated. pid=%d argv=%s",
             os.getpid(), " ".join(sys.argv[1:]) or "(none)")
    _dep_env_names = _deployment_env_names(_root)
    if _dep_env_keys or _dep_env_names:
        log.info("[env] deployment.env applied %d var(s): %s",
                 len(_dep_env_keys), ", ".join(sorted(_dep_env_keys)))
    # §4.5 — refuse an undeclared AKASHA_* variable BY NAME, before anything reads the environment.
    # `stop` still runs: an operator must always be able to halt a cell.
    _refused = _env_refused(_dep_env_names)
    if _refused and not (len(sys.argv) >= 2 and sys.argv[1] == "stop"):
        for _n in _refused:
            log.error("[env] refused name=%s — no manifest declares it (docs/deployment.md lists "
                      "every declared variable); unset it, or declare it in its package's manifest", _n)
        sys.exit(3)
    if _fd_raise and _fd_raise[0] != _fd_raise[1]:
        log.info("[fd] raised RLIMIT_NOFILE soft %s → %s (guest-cell FD headroom)",
                 _fd_raise[0], _fd_raise[1])

    # ── `stop` — halt a detached web portal (no kernel boot needed) ───
    # Simple counterpart to the "exit leaves the server running" behaviour, so an
    # operator never needs a pkill/ps incantation.
    if not _is_cgi and len(sys.argv) >= 2 and sys.argv[1] == "stop":
        _base = os.environ.get("AKASHA_DATA_DIR", "").strip() or os.path.join(_root, "data")
        # F36/F47-6.3 — arm the manual-restart marker FIRST, so a guard tick that fires during this
        # stop (and the operator's follow-up start) stands down instead of racing in its own daemon.
        _arm_manual_restart(_base)
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
            _inproc = []
            for _u in _sv._reverse_dep_order(_svc_units):
                _r = _sup.stop(_u["id"], grace_s=_u.get("grace_s"))
                _st = _r.get("status")
                if _st == "stopped":
                    _any = True
                    print(f"  [+] Stopped {_u['id']} (PID {_u.get('pid')}).")
                elif _st == "host-managed":
                    # An in-process THREAD unit (e.g. svc:feed-poll): it has NO OS process of its
                    # own — it runs INSIDE its host writer and stops WITH it, so `stop()` must not
                    # signal the shared host pid (that would take the whole daemon down early). It is
                    # not skipped: we acknowledge it here, and scrub its now-stale descriptor in a
                    # second pass once the host is actually down (below).
                    _dep = (_u.get("deps") or ["svc:cell"])[0]
                    print(f"  [+] {_u['id']} (in-process poller) — stopped with its host {_dep}.")
                    _inproc.append(_u["id"])
                    _any = True
            # Second pass: the hosts are down now, so re-stop the in-process units — with the host pid
            # dead, stop() removes their leftover descriptors (belt-and-suspenders for a SIGKILLed host
            # whose lifecycle closer never ran, so `svc ls` is clean immediately, not only next boot).
            for _uid in _inproc:
                try:
                    _sup.stop(_uid)
                except Exception:
                    pass
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
        # Sweep any ORPHANED WRITER daemon for this data dir too — the process that carries the
        # feed-poll thread. The run-dir cascade + cell.pid only cover the ONE recorded writer, so a
        # respawn-race survivor or a pre-reinstall daemon (its pid no longer the recorded svc:cell)
        # keeps its poller running and is missed by `stop`. This is the "old feed daemon not killed"
        # route. Graceful (SIGTERM → checkpoint) with a shared grace, then SIGKILL any straggler.
        _orphd = _reap_leaked_daemons(_base)
        if _orphd:
            print(f"  [+] Swept {len(_orphd)} orphaned writer daemon(s): PID {', '.join(map(str, _orphd))}.")
            _any = True
        if not _any:
            print("  [!] Nothing running to stop.")
        # Clear the stale socket endpoint so a fresh boot re-advertises cleanly.
        for _f in ("central/cell.sock", "central/cell.endpoint"):
            try: os.remove(os.path.join(_base, _f))
            except OSError: pass
        return

    # ── `guard` — install / inspect / remove the OUTER guardian (F12a), or run one --tick ──
    # Guardianship is mutual (the daemon revives the portal, the portal's watchdog revives the
    # daemon); when OOM takes BOTH in one respawn window there is no reviver left. The outer
    # guardian is an OS-level timer/service that runs convergence and exits — trivially safe because
    # a healthy system defers (exit 0) and a dead/wedged one converges to one daemon+portal.
    if not _is_cgi and len(sys.argv) >= 2 and sys.argv[1] == "guard":
        _base = os.environ.get("AKASHA_DATA_DIR", "").strip() or os.path.join(_root, "data")
        sys.exit(_run_guard(sys.argv[2:], _root, _base))

    # Data dir defaults to <root>/data; AKASHA_DATA_DIR relocates it (relocatable
    # deployment, and lets a test point the daemon at a scratch cell). The client and
    # daemon share it — the daemon inherits this env when spawned.
    base_dir = os.environ.get("AKASHA_DATA_DIR", "").strip() or os.path.join(_root, "data")
    # §4.4 — a directory holding a store in another data format stops HERE, before anything below
    # takes a lock, touches a heartbeat or writes a marker in it. One line; nothing written.
    from lib.akasha import data_format as _df
    try:
        _df.check(base_dir)
    except _df.DataFormatMismatch as _dfx:
        print(str(_dfx), file=sys.stderr)
        sys.exit(3)

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

    # F60 §1.2 — a `--daemon` process is a WRITER; clear a leaked AKASHA_SERVE_ONLY (a portal that
    # spawned the revive without the writer-env scrub, an operator export, a stale systemd unit)
    # BEFORE the kernel is built so the writer-role gates all see a writer. Last-line defense behind
    # _writer_env(); extracted to _scrub_daemon_serve_only for unit coverage (A13(b)).
    _scrub_daemon_serve_only(args is not None and getattr(args, "daemon", False), log)

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
    # reliably persist. An explicit --serve/--daemon still overrides. The platform is detected, never
    # declared by a switch (the purge order §4.5).
    if args is not None and not (args.serve or args.daemon) and _is_ios():
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
        # ~cloud) — it is honoured there.
        _ap = os.path.abspath(base_dir).lower()
        _icloud = any(_m in _ap for _m in ("mobile documents", "com~apple~clouddocs",
                                           "clouddocs", "icloud"))
        if (os.environ.get("AKASHA_BACKEND", "sqlite").strip().lower() == "silica"
                and _icloud and not _has_sil):   # never orphan an existing Silica cell
            os.environ["AKASHA_BACKEND"] = "sqlite"
            print("  [i] iOS/iPadOS — the native (Silica) store is multi-file and iCloud does not "
                  "reliably persist it across launches (genesis/writes reappear lost). Using the "
                  "single-file SQLite store here so data survives. To test Silica, run from a LOCAL "
                  "folder (e.g. ~/Documents), not ~cloud.", flush=True)
        _store_desc = ("native Silica store" if os.environ.get(
            "AKASHA_BACKEND", "sqlite").strip().lower() == "silica" else "single-file SQLite store")
        print(f"  [i] iOS/iPadOS detected — running as a single embedded process "
              f"(no daemon/socket/portal); durable {_store_desc}.", flush=True)

    if args is not None:
        _server_mode = args.serve or args.daemon
        _embedded = (args.embedded or args.stdio
                     or os.environ.get("AKASHA_EMBEDDED", "").strip().lower()
                     in ("1", "yes", "true", "on"))
        # Auto-reclaim leaked predecessors on EVERY start (principle: the operator is NEVER asked to
        # run a Linux command — no stop/pkill/ps). Reap orphan writer daemons + portals for this data
        # dir, sparing the recorded daemon/portal (convergence handles that one). This covers the
        # attach-to-a-healthy-daemon path too — which never boots a new daemon — so simply launching
        # akasha cleans up a crash/respawn-race survivor. Instant when there are none; embedded (iOS
        # single-process) has no daemon to reclaim.
        if not _is_cgi and not _embedded:
            _reclaimed = _reclaim_orphans_on_start(base_dir)
            if _reclaimed:
                print(f"  [+] Reclaimed {len(_reclaimed)} orphaned Akasha process(es) from a prior "
                      f"run: PID {', '.join(map(str, _reclaimed))}.", flush=True)
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
            # R1.1 (F28a) — FILESYSTEM-FIRST aliveness. Before any ping-gated decision, defer to a
            # daemon that is demonstrably SERVING from files alone: its recorded pid is a live
            # akasha --daemon process AND it has published a bound socket endpoint. Under memory
            # pressure a live writer misses the 3 s ping window; the old guard then fell through to
            # the boot path and — from a cron/guard heal line that lacked the deployment env — built
            # a full ram-mode series=seeds kernel beside it (the ~40-clone storm in the 8/26–8/27
            # logs), re-opening the two-writer socket-steal. Ping here is used ONLY to LOG
            # responsiveness (bounded retry); it never gates the boot decision and never reaps. Wedge
            # authority is the watchdog's alone (dual-pid, reaps a confirmed-dead pid before any new
            # boot, F2 unchanged); a start never reaps a live serving daemon on a ping miss. A newer
            # on-disk build is still replaced deliberately — but on the RESPONSIVE-ping path below
            # (where the build is readable) or the client-attach handshake, never here where a swap
            # blip could reap the live writer.
            _live_pid_fs = _daemon_serving_from_files(base_dir)
            if _live_pid_fs is not None and not _cipc_guard.ping(base_dir):
                _resp = any(_cipc_guard.ping(base_dir, timeout=10.0) for _ in range(3))
                print("  [i] A Cell daemon (PID %d) is already serving this data dir%s — deferring "
                      "(a ping miss under load is not death; the watchdog owns wedge recovery, and a "
                      "second writer into one nucleus is unsafe)."
                      % (_live_pid_fs, "" if _resp else "; currently slow to respond under load"),
                      flush=True)
                return
            if _cipc_guard.ping(base_dir):
                _running_build = _cipc_guard.ping_build(base_dir)
                _disk_build = _handshake_build_id(_root)     # D1: full-payload fingerprint on a seed, else code content
                # Replace an OLDER-or-no-build answering daemon (a no-build daemon predates the
                # handshake ⇒ strictly older ⇒ must be superseded, not deferred to — the same rule
                # as the client path, _should_replace_daemon; closes the reinstall no-replace trap).
                _replace, _decision = _replace_decision(_running_build, _disk_build)
                # §4.2 into system.log; A12 — demote the same-build attach case to DEBUG (cron-heal
                # runs this every ~5 min); a replace or a wait stays INFO.
                (log.info if (_replace or "→ wait" in _decision) else log.debug)("%s", _decision)
                if _replace:
                    print("  [~] Replacing an OLDER running Cell daemon with this build "
                          f"({_decision})…", flush=True)
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
            # We now hold the boot lock ⇒ WE are the writer. Run the SAME orphan reclamation `stop`
            # runs, so a boot cleans up leaked predecessors (a respawn-race survivor or pre-reinstall
            # writer daemon the run-dir no longer tracks, plus any orphaned portal) exactly as `stop`
            # does — code-side, never a manual `pkill`. The recorded predecessor was already stopped
            # above (replace path / wedge reap); this closes the gap where a boot swept only portals
            # and left an orphaned WRITER daemon holding the feed poller + its ~GB engine.
            _swept = _reap_orphans(base_dir)
            if _swept:
                print(f"  [+] Reclaimed {len(_swept)} orphaned Akasha process(es) left by a prior "
                      f"run: PID {', '.join(map(str, _swept))}.", flush=True)
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
            # F31-2/F44-A3 — WE are the writer: bias the OOM killer AWAY from us (a kill here loses
            # the WriteQueue + engine). A restartable portal/guest subprocess should be the victim
            # instead. Protective value is env-tunable; needs privilege for a negative value (root on
            # the VPS), else a silent no-op.
            try:
                _oom = int(os.environ.get("AKASHA_DAEMON_OOM_SCORE_ADJ", "-500"))
            except (TypeError, ValueError):
                _oom = -500
            if _set_oom_score_adj(_oom):
                print(f"  [+] Writer OOM-protected (oom_score_adj={_oom}).", flush=True)
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
                # _run_cell_client returned False → the daemon could not be reached (it wedged, or
                # was reaped). For a LARGE silica store, do NOT fall through to the embedded engine:
                # loading a multi-GB store in the CLI process exhausts memory (OOM) and FEEDS the
                # crash-loop (each failed boot reloads the whole store in-process and dies). Exit
                # cleanly so the operator simply retries, instead of the box thrashing itself down.
                if _silica_store_bytes(base_dir) > (1 << 30):     # > 1 GB
                    print("  [!] The Cell daemon could not start, and this store is too large to run "
                          "in an embedded CLI engine (that would exhaust memory and worsen the "
                          "outage).\n      Retry:  python akasha.py stop ; python akasha.py\n"
                          "      Persisting? See logs/cell-daemon.log for the boot error.", flush=True)
                    sys.exit(3)
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
                # Genuinely no daemon process. Before embedding, apply the same large-store guard as
                # the interactive path: a multi-GB silica store loaded into a one-off CLI process
                # OOMs and FEEDS the crash-loop (a cron `sys.ping` probe would repeatedly build the
                # whole store in-process and die). Refuse and exit non-zero so the outage surfaces
                # cleanly instead of the box thrashing itself down.
                if _silica_store_bytes(base_dir) > (1 << 30):     # > 1 GB
                    print("  [!] No daemon reachable and this store is too large to run in an "
                          "embedded CLI engine (that would exhaust memory and worsen the outage).\n"
                          "      Retry:  python akasha.py stop ; python akasha.py\n"
                          "      Persisting? See logs/cell-daemon.log for the boot error.", flush=True)
                    sys.exit(3)
                # Small store: run embedded (built below), but say so plainly, and remember to exit
                # non-zero if a daemon was EXPECTED (a recorded pid existed) so cron/scripts can
                # react to the daemon being down.
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
    # The GIL line is the WRITER's, and the writer is the process whose kernel started the writer-role
    # daemons — not merely a `--daemon` that took the boot lock. Logged at logging setup it was written
    # by every cron-heal probe (directive 10-02 §4); logged at the lock it was still written twice per
    # deploy, by the `--daemon` launcher and by the cell (directive 10-03 item 5).
    if getattr(getattr(live_gw, "kernel_client", None), "_writer_daemons_started", False) is True:
        _log_gil_switch()

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
                # A53 item 2 — SIGTERM never returns to main(), so log the ONE leaving line HERE,
                # before begin_shutdown, so a systemd/`kill` stop of the writer is always attributed
                # (never a silent disappearance).
                try:
                    log.info("[Cell] daemon leaving: reason=signal:SIGTERM pid=%d up=%.0fs",
                             os.getpid(), time.time() - _PROC_T0)
                except Exception:
                    pass
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
        os.environ["AKASHA_HANDSHAKE_BUILD"] = _handshake_build_id(_root)
        try:
            from api.portals.cell_ipc import CellIPCServer
            _ipc = CellIPCServer(live_gw, base_dir)
            _ipc.start()
            _lifecycle.register_closer(_ipc.stop)
            os.makedirs(os.path.join(base_dir, "central"), exist_ok=True)
            with open(_cell_pid_path(base_dir), "w") as _pf:
                _pf.write(str(os.getpid()))
            # F36/F47-6.3 — the daemon is up and listening: the manual-restart window is over, so clear
            # the marker and let the guard tick resume its normal watch on this fresh daemon.
            _clear_manual_restart(base_dir)
            # Persist the running-build fingerprint so a LATER launch can detect a code change (a
            # fresh seed was extracted) and sweep this now-old daemon automatically — even if it has
            # since crashed and can no longer be pinged (clean-slate-on-deploy, no operator step).
            # A9 (D1 visibility) — the replace/keep decision otherwise prints to the launcher's STDOUT
            # only, so a system.log delivery alone cannot prove a redeploy swept the old daemon. Read
            # the previous fingerprint (the outgoing daemon wrote it here) and mirror the transition
            # into system.log at boot, so D1 is provable from the log: a changed fingerprint = replaced.
            try:
                _rb_path = os.path.join(base_dir, "central", "running_build")
                _new_hs = os.environ.get("AKASHA_HANDSHAKE_BUILD", "") or "?"
                _bid = os.environ.get("AKASHA_BUILD_ID", "") or "?"
                _spawned_by = os.environ.get("AKASHA_SPAWNED_BY", "").strip() or "launcher"
                _mypid = os.getpid()
                _old_hs, _old_pid = "", ""
                try:
                    with open(_rb_path) as _rbr:
                        _parts = (_rbr.read().strip().split() + ["", ""])
                        _old_hs, _old_pid = _parts[0], _parts[1]
                except OSError:
                    _old_hs, _old_pid = "", ""
                if _old_hs and _old_hs != _new_hs:
                    log.info("[seed] replaced daemon at boot — build %s  fp %s → %s  spawned_by=%s",
                             _bid, _old_hs, _new_hs, _spawned_by)
                elif not _old_hs:
                    log.info("[seed] fresh daemon at boot — build %s  fp %s  spawned_by=%s",
                             _bid, _new_hs, _spawned_by)
                elif _old_pid != str(_mypid):
                    # §4.3 — same fingerprint but a NEW pid = a RESPAWN (crash/wedge revive), not a
                    # no-op boot. Name it as such and who spawned it, so the log distinguishes a
                    # recovery from a plain restart.
                    log.info("[seed] respawned daemon at boot — build %s  fp %s (unchanged)  "
                             "spawned_by=%s", _bid, _new_hs, _spawned_by)
                else:
                    log.info("[seed] daemon build unchanged — build %s  fp %s  spawned_by=%s",
                             _bid, _new_hs, _spawned_by)
                with open(_rb_path, "w") as _rbf:              # "<fp> <pid>" (F60 §4.3)
                    _rbf.write("%s %d" % (os.environ.get("AKASHA_HANDSHAKE_BUILD", ""), _mypid))
            except OSError:
                pass
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
        # F48-2.1 — also persist the resolved secret to a 0600 file under the shared base_dir, so a
        # portal that did NOT inherit AKASHA_SECRET (spawn-ordering gap) can still sign F16 pulse
        # emits the daemon will verify — closing the silent pulse-capture loss (seen>0 emit=0 rej>0).
        try:
            from api.portals.cell_ipc import write_elevation_secret as _wes
            _es = os.environ.get("AKASHA_SECRET")
            if _es:
                _wes(base_dir, _es)
        except Exception as _wex:
            log.debug("[Cell] elevation-secret file write skipped: %s", _wex)

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
            # Single-writer convergence: now that WE hold svc:cell (and the boot lock — so no
            # concurrent writer can be booting), evict any OTHER `--daemon` writer for this data dir.
            # Such an orphan is a respawn-race survivor or a PRE-REINSTALL daemon whose feed poller
            # is still running and writing to the wrong (private) cell — the run-dir cascade misses
            # it because its pid is no longer the recorded svc:cell. This makes restart/reinstall
            # self-heal to exactly ONE writer (hence one feed poller). Guarded on the boot lock so a
            # (flock-prevented) concurrent boot could never mutual-kill; keep_pids={self}. Graceful.
            if _HELD_BOOT_LOCK is not None and not os.environ.get("AKASHA_SERVE_ONLY"):
                try:
                    _oldw = _reap_leaked_daemons(base_dir, keep_pids={os.getpid()})
                    if _oldw:
                        log.info("[Boot] evicted %d orphaned writer daemon(s) (stale feed poller): %s",
                                 len(_oldw), ", ".join(map(str, _oldw)))
                        print(f"  [~] Evicted {len(_oldw)} orphaned writer daemon(s) left by a prior "
                              f"run (PID {', '.join(map(str, _oldw))}).", flush=True)
                except Exception as _rw_exc:
                    log.debug("[Boot] orphan-writer eviction skipped: %s", _rw_exc)
            # Mount the live-telemetry poller as a managed unit (svc:feed-poll) — SEPARATE from the
            # ontology boot loader, and only NOW that svc:cell (the single nucleus writer) is recorded,
            # so the poller mounts as a managed unit tied to the writer (heartbeat + managed stop). The
            # poller is DEFAULT-ON (opt out via a persisted `feed.poll off`);
            # _schedule_feed_poll gates on that. Write id is system.librarian → telemetry publishes to
            # the shared nucleus, guests read it. Runtime-controllable via `feed.poll on|off|status`.
            # Every host-bound THREAD unit the packages declare (svc:feed-poll, broadcast-relay,
            # svc:news-broadcast, …) starts here through the kernel, in manifest order; the launcher
            # names none of them (backend layout order 2026-09-20). Each starter is idempotent and
            # gates on its own declared state (a persisted `feed.poll off`, say).
            try:
                live_gw.kernel_client._start_thread_units()
            except Exception as _tu_exc:
                log.debug("[Boot] thread units not started: %s", _tu_exc)
            # F22: the thread-unit guard — re-creates a feed-poll/station/relay thread that actually
            # dies (only this interpreter can restart its own threads; the Supervisor correctly cannot).
            try:
                live_gw.kernel_client._schedule_thread_guard()
            except Exception as _tg_exc:
                log.debug("[Boot] thread-guard not started: %s", _tg_exc)
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

        # Thesaurus-tier: pre-load the non-English (Latin-script) SpaCy language dictionaries at boot,
        # so original-language (原言語) analysis is ready without an on-first-use download. seeds tiers
        # support the same models but do NOT auto-install — they stay on-demand and degrade to the
        # tokenizer floor when absent. (CJK is intentionally not in the model map yet.)
        if _series and not _series.startswith("seeds") and _series != "dev" \
                and not os.environ.get("AKASHA_SKIP_AUTOINSTALL"):
            try:
                from lib.harmonia.plugins.nlp import MultiLocaleNLP as _MLNLP
                _MLNLP().ensure_models()      # non-CJK (all of model_map); no-op if spaCy absent
            except Exception as _nlp_exc:
                log.warning("[NLP] model pre-load skipped: %s", _nlp_exc)

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
        import shlex as _shlex
        # shlex.quote each token (see the note at the other run_single_shot site): a REMAINDER value
        # with spaces must survive the shlex re-parse intact.
        print(run_single_shot(" ".join(_shlex.quote(t) for t in args.cmd), live_gw))
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
    from lib.akasha.api import reserved as _reserved
    _archives_path    = _reserved.root("pages")
    _archives_index   = os.path.join(_archives_path, "index.html")
    _is_dev           = os.path.isdir(os.path.join(_root, "reproductor"))
    if args.portal == "pages":
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
        _services_static = os.path.join(_root, "services", "static")
        _docs_path       = os.path.join(_root, "docs")

        # Build mount list: most-specific paths first, "/" last.
        _asgi_static_dirs = []
        if os.path.isdir(_docs_path):
            _asgi_static_dirs.append(("/docs", _docs_path))
        # F25c: shared local assets (plotly + the world-GDP dataset) live under services/static/lib, so
        # the flagship rooms work offline. Mount /lib from that ONE copy for the archives portal too
        # (the seeds httpd already serves it natively from its docroot).
        _lib_static = os.path.join(_services_static, "lib")
        if os.path.isdir(_lib_static):
            _asgi_static_dirs.append(("/lib", _lib_static))
        # THE ROOMS A PACKAGE DECLARES (`static` in its manifest — archives' `/cosmos`, `/word`,
        # `/field`). The launcher used to name all three here (group 4, 4.9). A declared mount whose
        # directory is not on this cell is skipped with a line: a seeds cell ships no archives tree,
        # and its root mount already serves services/static/, cosmos included.
        from lib.akasha.api import manifest as _manifest
        for _mnt, _dir in sorted(_manifest.declared_static().items()):
            if os.path.isdir(_dir):
                _asgi_static_dirs.append((_mnt, _dir))
            else:
                log.info("[portal] static mount %s skipped: %s is not on this cell", _mnt, _dir)

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
            env["AKASHA_SERVE_ONLY"] = "1"          # the serve-only role also skips autolearn
            # R5: hand the portal this daemon's launch args so its self-watchdog can spawn an
            # IDENTICAL replacement (same --server/--host/--port/--portal) if the writer wedges.
            import json as _json_argv
            env["AKASHA_DAEMON_ARGV"] = _json_argv.dumps(sys.argv[1:])
            try:
                from lib.harmonia import logger as _hlog
                _hlog.rotate_if_big(log_path)    # R9 — bound the portal redirect at each (re)launch
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
                    env_add={"PYTHONUNBUFFERED": "1",
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
            # F14b#2 — 10 s probe timeout (was 3 s). With the loop-starvation fix (F14b#1) the
            # worker answers sys.ping promptly even under a heavy crawler read, but a generous
            # timeout × the 3-fail threshold (≈45 s) means only a truly wedged worker is replaced —
            # a brief stall no longer triggers a respawn whose memory spike can OOM the daemon.
            # F27-10 — build the probe URL from the SAME scheme/port this portal is being launched
            # with (single source: `scheme` + `_web_port`, the exact values in `cmd` above), so a
            # future port/TLS move can never silently leave a probe that can never pass (a permanent
            # respawn loop). One registration line makes the pairing visible at boot, not at the
            # first respawn storm.
            _probe_url = (f"{scheme}://127.0.0.1:{int(_web_port)}/api/rpc") if _web_port else None
            _portal_health = ({"kind": "http", "target": _probe_url,
                               "method": "sys.ping", "timeout": 10.0}
                              if _probe_url else None)
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
            if _probe_url:
                log.info("[Boot] svc:web-portal probe = %s (tls=%s) — derived from the portal's own "
                         "scheme/port, so a port/TLS change moves the probe in lockstep",
                         _probe_url, "on" if scheme == "https" else "off")
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

        _mode_label = "pages/uvicorn" if _has_archives else _web_engine
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
        _leave_reason = _daemon_serve_loop(_supervisor.get_proc("svc:web-portal"), log)
        _up = time.time() - _PROC_T0
        log.info("[Cell] daemon leaving: reason=%s pid=%d up=%.0fs", _leave_reason, os.getpid(), _up)
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
