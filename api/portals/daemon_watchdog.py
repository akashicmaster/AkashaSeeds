"""
Daemon self-watchdog (R5) — hosted in the serve-only web-portal subprocess.

A WEDGED Cell daemon (alive, holds the boot flock, but not answering — OOM thrash, disk stall,
GIL deadlock during a B-scale load) cannot heal itself from the inside, and nothing outside
watched it. This turns the currently-manual `stop`-then-start recovery into the automatic path,
reusing the SAME convergence code every entry path shares (`akasha._converge_daemon`).

Role placement: the portal is the natural watchdog — it is serve-only (never a nucleus writer),
already knows the writer's data dir, and outlives the daemon (its own session survives an SSH
SIGHUP). Every M seconds it pings the daemon socket; after K consecutive SILENT rounds AND a stale
boot heartbeat (so a legitimately-slow BOOT is never mistaken for a wedge), it runs convergence
with spawn=True — reaping the wedged writer and spawning a fresh one — then logs one line.

Guards:
  • only the portal RECORDED in the run-dir watches (no thundering herd from a leaked orphan);
  • disabled with AKASHA_NO_WATCHDOG=1;
  • the portal NEVER becomes a writer — it spawns a separate --daemon process, never an engine.

Tunables (env): AKASHA_WATCHDOG_INTERVAL (default 60 s), AKASHA_WATCHDOG_SILENT_K (default 3).
"""
import os
import threading


def _is_recorded_portal(base_dir: str) -> bool:
    """True only for the web-portal process RECORDED in the run-dir — so a leaked/orphaned portal
    from a prior crash never also tries to revive the daemon (no thundering herd)."""
    try:
        with open(os.path.join(base_dir, "web-portal.pid")) as fh:
            return int((fh.read() or "0").strip() or 0) == os.getpid()
    except (OSError, ValueError):
        return False


def _system_log(root: str, msg: str) -> None:
    import time as _t
    try:
        p = os.path.join(root, "logs", "system.log")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        stamp = _t.strftime("%Y-%m-%d %H:%M:%S", _t.localtime())
        with open(p, "a") as fh:
            fh.write(f"{stamp} [watchdog] {msg}\n")
    except OSError:
        pass


def _revive(akasha, root: str, base_dir: str) -> str:
    """Reap the wedged writer and spawn an IDENTICAL replacement (same --server/--host/--port/
    --portal, reconstructed from the daemon argv the daemon handed us). wait_ceiling=0: the wedge
    is already CONFIRMED (K silent rounds + stale heartbeat), so do not re-wait the boot ceiling —
    but a daemon whose heartbeat turns fresh mid-check is still respected (converge keeps waiting)."""
    import json as _json
    saved = []
    try:
        saved = _json.loads(os.environ.get("AKASHA_DAEMON_ARGV") or "[]") or []
    except Exception:
        saved = []
    try:
        args = akasha._build_arg_parser().parse_args(saved)
    except SystemExit:
        args = akasha._build_arg_parser().parse_args([])   # bad saved argv → deployment defaults
    return akasha._converge_daemon(root, base_dir, args, spawn=True, quiet=True, wait_ceiling=0)


def _loop(base_dir: str, interval: float, silent_k: int) -> None:
    import time as _t
    import logging as _lg
    log = _lg.getLogger("akasha-web-worker")
    try:
        import akasha
        from api.portals import cell_ipc
    except Exception as exc:                       # can't import the lifecycle helpers → no watchdog
        log.debug("[Watchdog] disabled (import failed): %s", exc)
        return
    root = getattr(akasha, "_root", os.getcwd())
    silent = 0
    while True:
        _t.sleep(interval)
        if not _is_recorded_portal(base_dir):
            silent = 0
            continue                               # not the recorded portal → do not act
        if cell_ipc.ping(base_dir):
            silent = 0
            continue                               # writer answers → healthy
        # The daemon did not answer. A legitimately BOOTING daemon touches the boot heartbeat, so a
        # fresh heartbeat means "slow boot, not wedged" — never count it toward a revive.
        if akasha._boot_heartbeat_fresh(base_dir):
            silent = 0
            continue
        silent += 1
        if silent < silent_k:
            continue
        silent = 0
        try:
            state = _revive(akasha, root, base_dir)
            log.warning("[Watchdog] Cell daemon was unresponsive for %d rounds — ran convergence "
                        "(%s).", silent_k, state)
            _system_log(root, f"Cell daemon unresponsive — portal watchdog ran convergence: {state}")
        except Exception as exc:
            log.warning("[Watchdog] revive attempt failed: %s", exc)


def start(base_dir: str) -> bool:
    """Start the watchdog thread if this is a serve-only portal and the watchdog is enabled.
    Returns True if started. Idempotent-ish (a second call starts a second thread — call once)."""
    if os.environ.get("AKASHA_NO_WATCHDOG", "").strip().lower() in ("1", "yes", "true", "on"):
        return False
    # Only the serve-only portal subprocess watches (never the interactive foreground, which is the
    # writer itself). AKASHA_SERVE_ONLY is set by akasha.py when it spawns the portal subprocess.
    if os.environ.get("AKASHA_SERVE_ONLY", "").strip().lower() not in ("1", "yes", "true", "on"):
        return False
    if not base_dir:
        return False
    try:
        interval = float(os.environ.get("AKASHA_WATCHDOG_INTERVAL", "").strip() or 60)
        silent_k = int(os.environ.get("AKASHA_WATCHDOG_SILENT_K", "").strip() or 3)
    except ValueError:
        interval, silent_k = 60.0, 3
    interval = max(5.0, interval)
    silent_k = max(1, silent_k)
    threading.Thread(target=_loop, args=(base_dir, interval, silent_k),
                     name="daemon-watchdog", daemon=True).start()
    return True
