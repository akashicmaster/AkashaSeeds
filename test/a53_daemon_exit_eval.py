#!/usr/bin/env python3
"""
A53 — the writer's clean, attributable, self-inflicted-exit prevention.

The writer used to VANISH silently: its `--daemon` main thread waited on the FIRST portal
subprocess's `Popen.wait()`, so when the Supervisor health tick (a sibling thread) reaped/replaced
that portal, wait() returned, main() returned, atexit tore the single nucleus writer down — no log
line, and the whole cell rebooted (振り出しに戻る). This eval locks in the fix and its visibility.

Four checks (process/lifecycle machinery — independent of cell shape, so run once):
  (a) `_daemon_serve_loop` KEEPS RUNNING when the boot portal exits (logs the exit, Supervisor owns
      the respawn) and only the LIFECYCLE shutdown Event releases it (returns "stop rpc").
  (b) `Supervisor.stop()` on a live unit writes a `[reap] SIGTERM … unit=…` record (logger + system.log).
  (c) the serve-only portal answers sys.ping from a CACHED writer_online in constant time — even when
      the underlying writer probe is slow (a saturated request threadpool can no longer stall /health).
  (d) `maintain()` on a probe-FAILING but CPU-ADVANCING unit does NOT respawn it and logs the
      "busy, not wedged" line (Linux/proc only).

Run:  python test/a53_daemon_exit_eval.py     (exit 0 = all pass)
"""
import logging
import os
import subprocess
import sys
import tempfile
import threading
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


class _Cap(logging.Handler):
    """Capture log messages at/above `level` on the root logger."""
    def __init__(self, level=logging.INFO):
        super().__init__(level)
        self.lines = []

    def emit(self, r):
        try:
            self.lines.append(r.getMessage())
        except Exception:
            pass

    def has(self, *subs):
        return any(all(x in ln for x in subs) for ln in self.lines)


class _FakePortal:
    """A stand-in Popen: poll() returns None until `die_after` calls, then `rc`."""
    def __init__(self, pid=4242, die_after=2, rc=0):
        self.pid = pid
        self._n = 0
        self._die_after = die_after
        self._rc = rc

    def poll(self):
        self._n += 1
        return self._rc if self._n > self._die_after else None


def test_serve_loop():
    import akasha
    from lib.akasha import lifecycle
    lifecycle._shutting_down.clear()                 # fresh slate for the test loop
    log = logging.getLogger("Harmonia.Boot")
    cap = _Cap(logging.INFO)
    root = logging.getLogger(); root.addHandler(cap); lvl = root.level; root.setLevel(logging.INFO)
    holder = {}
    portal = _FakePortal(pid=4242, die_after=2, rc=0)

    def _run():
        holder["reason"] = akasha._daemon_serve_loop(portal, log, poll_interval=0.05)

    t = threading.Thread(target=_run, daemon=True)
    try:
        t.start()
        time.sleep(0.6)                              # let the portal "die" and the loop notice
        alive_after_portal_death = t.is_alive()
        logged_exit = cap.has("[Cell] boot portal", "exited status=0", "Supervisor owns")
        lifecycle._shutting_down.set()               # the real shutdown signal
        t.join(timeout=2.0)
        check("(a) serve loop KEEPS RUNNING after the boot portal exits (writer does not leave)",
              alive_after_portal_death is True)
        check("(a) serve loop LOGS the boot-portal exit (Supervisor owns respawn)", logged_exit,
              str(cap.lines)[-200:])
        check("(a) only the lifecycle shutdown Event releases the loop → reason='stop rpc'",
              holder.get("reason") == "stop rpc" and not t.is_alive(), str(holder))
    finally:
        lifecycle._shutting_down.set()
        root.removeHandler(cap); root.setLevel(lvl)
        lifecycle._shutting_down.clear()


def test_supervisor_stop_reap():
    import lib.harmonia.supervisor as sv
    base = tempfile.mkdtemp(prefix="a53_reap_")
    os.makedirs(os.path.join(base, "central"), exist_ok=True)
    sv._ensure_run_dir(base)
    cap = _Cap(logging.INFO)
    slog = logging.getLogger("Harmonia.Supervisor")
    slog.addHandler(cap); _lvl = slog.level; slog.setLevel(logging.INFO)
    try:
        child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"], cwd=ROOT)
        sup = sv.Supervisor(base)
        sup.record_running("svc:sleeper", child.pid, engine="test", proc=child,
                           restart=sv.RESTART_NEVER, serve_only=True)
        res = sup.stop("svc:sleeper")
        check("(b) Supervisor.stop() stops the live unit", res.get("status") == "stopped", str(res))
        check("(b) Supervisor.stop() writes a [reap] SIGTERM record naming the unit + caller",
              cap.has("[reap] SIGTERM", "unit=svc:sleeper", "caller="), str(cap.lines)[-200:])
        # mirrored to system.log
        _sysp = os.path.join(base, "logs", "system.log")
        _mirror = os.path.exists(_sysp) and "[reap] SIGTERM" in open(_sysp).read()
        check("(b) the [reap] record is mirrored to system.log (writer-visible)", _mirror)
        try:
            child.wait(timeout=5)
        except Exception:
            child.kill()
    finally:
        slog.removeHandler(cap); slog.setLevel(_lvl)


def test_ping_cached_constant_time():
    import api.portals.cell_ipc as C
    base = tempfile.mkdtemp(prefix="a53_ping_")
    os.makedirs(os.path.join(base, "central"), exist_ok=True)
    # Make the underlying writer probe SLOW: a saturated request path would stall a probe that had
    # to make its own round-trip. ping_cached() must NOT call it — it reads the cached bool.
    _orig = C.ping
    C.ping = lambda *a, **k: (time.sleep(5.0) or False)
    try:
        gw = C.ThinPortalGateway(base)               # starts the background refresher
        time.sleep(0.05)
        t0 = time.time()
        r = gw.ping_cached()
        dt = time.time() - t0
        check("(c) portal ping_cached() answers in constant time (<0.2s) off the request path",
              dt < 0.2 and r.get("kernel_online") is True and "writer_online" in r,
              f"dt={dt:.3f}s r={r}")
        # sys.ping dispatch uses the same cached answer (no socket round-trip)
        t1 = time.time()
        resp = gw.dispatch({"jsonrpc": "2.0", "method": "sys.ping", "id": "p"})
        dt1 = time.time() - t1
        check("(c) sys.ping over the portal gateway is likewise constant-time (cached)",
              dt1 < 0.2 and (resp.get("result") or {}).get("kernel_online") is True,
              f"dt={dt1:.3f}s")
        gw._ping_stop.set()
    finally:
        C.ping = _orig


def test_maintain_busy_defer():
    if not (sys.platform.startswith("linux") and os.path.isdir("/proc")):
        check("(d) maintain() spares a busy-advancing unit  [skipped: no /proc]", True)
        return
    import lib.harmonia.supervisor as sv
    base = tempfile.mkdtemp(prefix="a53_busy_")
    os.makedirs(os.path.join(base, "central"), exist_ok=True)
    sv._ensure_run_dir(base)
    cap = _Cap(logging.INFO)
    slog = logging.getLogger("Harmonia.Supervisor")
    slog.addHandler(cap); _lvl = slog.level; slog.setLevel(logging.INFO)
    busy = subprocess.Popen([sys.executable, "-c", "x=0\nwhile True:\n x+=1"], cwd=ROOT)
    try:
        sup = sv.Supervisor(base)
        # probe target = a closed port → the health probe FAILS every tick; the process is BURNING
        # CPU → advancing. record it READY (past boot grace gate) with an on-failure PROCESS recipe.
        sup.record_running("svc:busy", busy.pid, engine="test",
                           restart=sv.RESTART_ON_FAILURE,
                           spec={"substrate": sv.SUBSTRATE_PROCESS},
                           health={"kind": "tcp", "target": "127.0.0.1:1"}, serve_only=True)
        sv.mark_unit_ready(base, "svc:busy")
        respawned = False
        for _ in range(sup._HEALTH_FAIL_THRESHOLD):
            time.sleep(0.2)                          # let _proc_advancing see fresh CPU ticks
            acts = sup.maintain()
            if any(a.get("id") == "svc:busy" and not a.get("error") and a.get("pid") != busy.pid
                   for a in acts):
                respawned = True
        u = sv.read_unit(base, "svc:busy")
        check("(d) a probe-failing but ADVANCING unit is NOT respawned (busy ≠ wedged)",
              not respawned and u and u.get("pid") == busy.pid, f"respawned={respawned}")
        check("(d) maintain() logs the 'busy, not wedged' line naming the writer ipc",
              cap.has("busy, not wedged") and cap.has("[Supervisor]", "advancing"),
              str(cap.lines)[-240:])
    finally:
        slog.removeHandler(cap); slog.setLevel(_lvl)
        busy.kill(); busy.wait()


def test_ipc_saturation_sampler():
    """A55 — the 1 Hz sampler warns only on a SUSTAINED + MATERIAL backlog, not on a steady q=1."""
    import queue as _q
    import api.portals.cell_ipc as C
    base = tempfile.mkdtemp(prefix="a55_sat_")
    cap = _Cap(logging.WARNING)
    lg = logging.getLogger("Akasha.CellIPC")
    lg.addHandler(cap); _lvl = lg.level; lg.setLevel(logging.WARNING)
    try:
        srv = C.CellIPCServer(gateway=None, base_dir=base)
        # (i) steady q=1 for >10 s → NOT material (depth 1, no slow request) → no warning
        srv._connq = _q.Queue(); srv._connq.put_nowait(object())
        t = 1000.0
        srv._saturation_tick(now=t)                 # first non-empty sample sets the timer
        srv._saturation_tick(now=t + 11.0)          # sustained, but depth=1 → no warn
        check("(A55) a steady q=1 backlog does NOT warn (no false saturation)",
              not cap.has("pool saturated"), str(cap.lines))
        # (ii) q≥2 sustained → warns once
        cap.lines.clear()
        srv._connq.put_nowait(object())             # depth now 2
        srv._q_since = t                            # pretend the backlog began at t
        srv._last_sat_warn = 0.0
        srv._saturation_tick(now=t + 12.0)
        check("(A55) a sustained q≥2 backlog warns once (pool saturated)",
              cap.has("[ipc] pool saturated", "q=2"), str(cap.lines))
        # (iii) recovery → drained line
        cap.lines.clear()
        srv._connq = _q.Queue()                     # empty
        srv._saturation_tick(now=t + 20.0)
        check("(A55) recovery after a warning logs a [ipc] drained line",
              cap.has("[ipc] drained"), str(cap.lines))
    finally:
        lg.removeHandler(cap); lg.setLevel(_lvl)


def main():
    print("\n  A53 — writer clean-exit + attributable reap + constant-time liveness\n")
    test_serve_loop()
    test_supervisor_stop_reap()
    test_ping_cached_constant_time()
    test_maintain_busy_defer()
    test_ipc_saturation_sampler()
    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("\nRESULT: PASS — the daemon main thread parks on the lifecycle shutdown Event (the boot "
          "portal's death no longer takes the writer with it, and is logged), Supervisor.stop() writes "
          "an attributable [reap] record, the portal answers sys.ping from a constant-time cache, and "
          "maintain() spares a busy-but-advancing unit with a 'busy, not wedged' line.")
    sys.exit(0)


if __name__ == "__main__":
    main()
