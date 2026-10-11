#!/usr/bin/env python3
"""
Daemon zombie-reaper eval (fix B) — the recurring "1 zombie process" after a redeploy.

A spawned Cell daemon is a direct child of the launcher; an interactive launcher (CLI / seed session)
left open across a daemon REPLACEMENT outlives the daemon it spawned and never waitpid()s it, so the
dead daemon lingers as a <defunct> zombie under that session. The reaper poll()s tracked spawned-daemon
children so a dead one is reaped within seconds — no zombie. This pins that behaviour with a REAL zombie.

Run:  python test/daemon_reaper_eval.py     (exit 0 = all pass)
"""
import os, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _proc_state(pid):
    """The single-letter process state from /proc, or None if the pid is gone. 'Z' = zombie/defunct."""
    try:
        with open(f"/proc/{pid}/stat") as fh:
            return fh.read().split(") ", 1)[1].split(" ", 1)[0]
    except OSError:
        return None


def main():
    import akasha

    # A child that exits immediately — simulates a spawned daemon that was replaced/killed. We do NOT
    # poll/wait it, so it becomes a real <defunct> zombie under this test process (the "launcher").
    proc = subprocess.Popen([sys.executable, "-c", "import sys; sys.exit(0)"], start_new_session=True)
    pid = proc.pid
    for _ in range(50):                     # let it exit + become a zombie
        if _proc_state(pid) == "Z":
            break
        time.sleep(0.05)
    check("a spawned-then-dead daemon child is a ZOMBIE while the launcher hasn't reaped it",
          _proc_state(pid) == "Z", "state=" + str(_proc_state(pid)))

    # Track it (as _spawn_cell_daemon does on success) and run one reap pass.
    akasha._TRACKED_DAEMON_PROCS.append(proc)
    reaped = akasha._reap_tracked_daemons()
    check("the reaper reaps the dead child (one pass)", reaped == 1, str(reaped))
    check("the zombie is GONE after reaping (no defunct entry)", _proc_state(pid) != "Z", "state=" + str(_proc_state(pid)))
    check("the reaped proc is dropped from tracking", proc not in akasha._TRACKED_DAEMON_PROCS)

    # A LIVE daemon child must NOT be reaped (only dead ones) — the reaper never disturbs a running writer.
    alive = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"], start_new_session=True)
    akasha._TRACKED_DAEMON_PROCS.append(alive)
    reaped2 = akasha._reap_tracked_daemons()
    check("a LIVE daemon child is not reaped (stays tracked, keeps running)",
          reaped2 == 0 and alive in akasha._TRACKED_DAEMON_PROCS and alive.poll() is None)
    alive.terminate()
    try:
        alive.wait(timeout=5)
    except Exception:
        pass
    akasha._TRACKED_DAEMON_PROCS[:] = []

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("All daemon-reaper checks passed."); sys.exit(0)


if __name__ == "__main__":
    main()
