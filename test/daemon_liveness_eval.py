#!/usr/bin/env python3
"""
Liveness-aware daemon attach — the CLI must NEVER kill a healthy booting daemon, NEVER become a
second nucleus writer, and must converge to exactly ONE daemon on an abrupt SSH-drop reconnect.

Background (the bug this guards): a user SSHes into the VPS and runs `python akasha.py`. The CLI
spawns a detached Cell daemon (the sole nucleus writer) and attaches over the local socket. If the
SSH link drops, the foreground CLI dies abruptly (SIGHUP), but the detached daemon keeps BOOTING.
On reconnect the CLI runs again — and the earlier code, seeing `cell_ipc.ping` fail (the daemon's
socket is not bound yet, mid-boot), read that as 'no daemon' and REAPED the healthy booting daemon
+ spawned a new one. Every reconnect repeated it → the perpetual '起動→抜けて→起動し直し' restart loop,
and briefly TWO writers into one nucleus (the crash). Process management is entirely code-side;
the user is never asked to run pkill/kill.

The fix under test (`akasha.py`):
  • `_daemon_process_alive(base_dir)` — reads cell.pid and returns the pid ONLY if it is a genuinely
    live akasha `--daemon` process (its /proc cmdline), so a booting daemon (no socket yet) is still
    seen as ALIVE, and a dead/recycled/foreign/self pid is rejected.
  • `_wait_for_daemon_socket(base_dir, deadline)` — waits for that booting daemon's socket to answer;
    returns True on answer, False if it dies while booting or never binds within the ceiling.
  • `_ensure_daemon(...)` — the single client entry: ANSWERS→attach; ALIVE-but-booting→wait+attach
    (never reap, never spawn a second); HUNG→reap+respawn; NONE→spawn.

These are /proc-based (Linux). This test drives them with REAL helper processes whose argv carries
the `akasha --daemon` marker (so /proc/<pid>/cmdline matches), plus a real UNIX socket to stand in
for a daemon that has 'come online', and monkeypatches only `_spawn_cell_daemon` to assert the
branch decisions WITHOUT spawning a heavy real daemon (which times out in a sandbox).

Run:  python test/daemon_liveness_eval.py
"""
import os, sys, time, socket, tempfile, shutil, subprocess, importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_results = []
def record(name, ok, detail=""):
    _results.append((name, ok, detail))
    print(f"  {'OK  ' if ok else '!! FAIL'}  {name:34} {detail}")


def _load_akasha():
    os.environ.setdefault("AKASHA_SKIP_AUTOINSTALL", "1")
    spec = importlib.util.spec_from_file_location("akmod", os.path.join(ROOT, "akasha.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _spawn_marker_proc(*extra):
    """A live child process whose argv carries the given markers (so /proc/<pid>/cmdline shows
    them). Sleeps quietly; caller terminates it. Used to fake an 'akasha --daemon' process."""
    return subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)", *extra])


def _write_pid(base_dir, pid):
    central = os.path.join(base_dir, "central")
    os.makedirs(central, exist_ok=True)
    with open(os.path.join(central, "cell.pid"), "w") as fh:
        fh.write(str(pid))


def _kill(proc):
    try:
        proc.terminate(); proc.wait(timeout=5)
    except Exception:
        try: proc.kill()
        except Exception: pass


def main():
    if not os.path.isdir("/proc"):
        print("SKIP — /proc unavailable (liveness detection is Linux-only).")
        return 0
    ak = _load_akasha()
    print("\n  liveness-aware daemon attach — never reap/embed a healthy booting daemon\n")

    # ── _daemon_process_alive ───────────────────────────────────────────────────
    base = tempfile.mkdtemp(prefix="akasha_live_")
    procs = []
    try:
        # (a) no cell.pid → None
        record("alive: no cell.pid", ak._daemon_process_alive(base) is None)

        # (b) cell.pid = self → None (never mistake the launcher for the daemon)
        _write_pid(base, os.getpid())
        record("alive: self pid rejected", ak._daemon_process_alive(base) is None)

        # (c) cell.pid = a live 'akasha --daemon' process → returns that pid (even with NO socket:
        #     this is the booting-daemon case the old code fatally misread as 'no daemon')
        dae = _spawn_marker_proc("akasha", "--daemon"); procs.append(dae)
        time.sleep(0.3)
        _write_pid(base, dae.pid)
        record("alive: booting daemon seen", ak._daemon_process_alive(base) == dae.pid,
               f"pid={dae.pid} (no socket yet, still ALIVE)")

        # (d) cell.pid = a live process that is NOT a daemon (no --daemon marker) → None
        other = _spawn_marker_proc("akasha", "explore"); procs.append(other)
        time.sleep(0.3)
        _write_pid(base, other.pid)
        record("alive: non-daemon rejected", ak._daemon_process_alive(base) is None,
               "an 'akasha explore' CLI is not the daemon")

        # (e) cell.pid = a live NON-akasha process → None (anti-recycle: pid reused by something else)
        foreign = _spawn_marker_proc(); procs.append(foreign)   # bare python, no markers
        time.sleep(0.3)
        _write_pid(base, foreign.pid)
        record("alive: foreign pid rejected", ak._daemon_process_alive(base) is None)

        # (f) cell.pid = a DEAD pid → None
        dead = _spawn_marker_proc("akasha", "--daemon")
        dpid = dead.pid; _kill(dead); time.sleep(0.2)
        _write_pid(base, dpid)
        record("alive: dead pid rejected", ak._daemon_process_alive(base) is None, f"pid={dpid} exited")

        # ── _wait_for_daemon_socket ─────────────────────────────────────────────
        # A booting daemon that NEVER binds a socket within the ceiling → False (→ caller reaps it).
        alive2 = _spawn_marker_proc("akasha", "--daemon"); procs.append(alive2)
        time.sleep(0.3); _write_pid(base, alive2.pid)
        t0 = time.time()
        r = ak._wait_for_daemon_socket(base, deadline_s=1.5)
        record("wait: never-binds → False", r is False and (time.time() - t0) >= 1.4,
               f"waited {time.time()-t0:.1f}s for a socket that never came")

        # A booting daemon that DIES mid-wait → False promptly (does NOT burn the whole deadline).
        alive3 = _spawn_marker_proc("akasha", "--daemon"); procs.append(alive3)
        time.sleep(0.3); _write_pid(base, alive3.pid)
        import threading
        threading.Timer(0.6, lambda: _kill(alive3)).start()
        t0 = time.time()
        r = ak._wait_for_daemon_socket(base, deadline_s=10.0)
        dt = time.time() - t0
        record("wait: dies mid-boot → False fast", r is False and dt < 5.0,
               f"returned in {dt:.1f}s (did not wait the full 10s)")
    finally:
        for p in procs:
            _kill(p)
        shutil.rmtree(base, ignore_errors=True)

    # ── _ensure_daemon branch decisions (monkeypatched spawn/ping) ───────────────
    base = tempfile.mkdtemp(prefix="akasha_ens_")
    procs = []
    try:
        from api.portals import cell_ipc as _cipc
        calls = {"spawn": 0, "reap": 0}
        orig_spawn = ak._spawn_cell_daemon
        orig_reap = ak._reap_stale_daemon
        orig_ping = _cipc.ping
        ak._spawn_cell_daemon = lambda *a, **k: (calls.__setitem__("spawn", calls["spawn"] + 1) or True)
        ak._reap_stale_daemon = lambda *a, **k: (calls.__setitem__("reap", calls["reap"] + 1) or 1)

        # (1) daemon ANSWERS → attach, no spawn, no reap.
        _cipc.ping = lambda *a, **k: True
        calls.update(spawn=0, reap=0)
        ok = ak._ensure_daemon(ROOT, base, None) is True and calls == {"spawn": 0, "reap": 0}
        record("ensure: answers → attach", ok, f"spawn={calls['spawn']} reap={calls['reap']}")

        # (2) no daemon, none alive → spawn exactly one, no reap.
        _cipc.ping = lambda *a, **k: False
        if os.path.exists(os.path.join(base, "central", "cell.pid")):
            os.remove(os.path.join(base, "central", "cell.pid"))
        calls.update(spawn=0, reap=0)
        ok = ak._ensure_daemon(ROOT, base, None) is True and calls == {"spawn": 1, "reap": 0}
        record("ensure: none → spawn one", ok, f"spawn={calls['spawn']} reap={calls['reap']}")

        # (3) a daemon is ALIVE-but-booting (never answers here) → after the wait it is treated as
        #     HUNG: reap ONCE + spawn ONCE. Critically it does NOT spawn without reaping (which would
        #     be a second writer) and does NOT skip cleanup. Uses a tiny wait via monkeypatched wait.
        dae = _spawn_marker_proc("akasha", "--daemon"); procs.append(dae)
        time.sleep(0.3); _write_pid(base, dae.pid)
        orig_wait = ak._wait_for_daemon_socket
        ak._wait_for_daemon_socket = lambda *a, **k: False       # simulate 'never bound in time'
        calls.update(spawn=0, reap=0)
        res = ak._ensure_daemon(ROOT, base, None)
        ak._wait_for_daemon_socket = orig_wait
        ok = res is True and calls == {"spawn": 1, "reap": 1}
        record("ensure: hung → reap+respawn", ok, f"spawn={calls['spawn']} reap={calls['reap']}")

        # (4) a daemon is ALIVE-but-booting and its socket COMES UP during the wait → attach, NO reap,
        #     NO spawn. This is the SSH-reconnect-mid-boot case that must NOT restart anything.
        dae2 = _spawn_marker_proc("akasha", "--daemon"); procs.append(dae2)
        time.sleep(0.3); _write_pid(base, dae2.pid)
        ak._wait_for_daemon_socket = lambda *a, **k: True        # simulate 'socket came online'
        calls.update(spawn=0, reap=0)
        res = ak._ensure_daemon(ROOT, base, None)
        ak._wait_for_daemon_socket = orig_wait
        ok = res is True and calls == {"spawn": 0, "reap": 0}
        record("ensure: booting → wait+attach", ok,
               f"spawn={calls['spawn']} reap={calls['reap']} (no restart on reconnect)")

        ak._spawn_cell_daemon = orig_spawn
        ak._reap_stale_daemon = orig_reap
        _cipc.ping = orig_ping
    finally:
        for p in procs:
            _kill(p)
        shutil.rmtree(base, ignore_errors=True)

    passed = sum(1 for _, ok, _ in _results if ok); total = len(_results)
    print(f"\n  {passed}/{total} checks passed")
    if passed == total:
        print("\nRESULT: PASS — the CLI attaches to a healthy booting daemon (never reaps it, never "
              "becomes a second writer) and converges to exactly one daemon on SSH-drop reconnect.\n")
        return 0
    print("\nRESULT: FAIL — daemon liveness handling is wrong (restart-loop / two-writers risk).\n")
    return 1


if __name__ == "__main__":
    sys.path.insert(0, ROOT)
    sys.exit(main())
