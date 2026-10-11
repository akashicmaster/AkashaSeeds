#!/usr/bin/env python3
"""
Orphan writer-daemon reap eval — the "old feed daemon not killed" route.

The live-telemetry feed poller runs INSIDE the writer (Cell) daemon (`akasha.py --daemon`), as a
host-bound thread. A THREAD unit shares the host pid, so the ONLY way to stop an orphaned poller is
to kill its host process. The run-dir cascade (`akasha.py stop`) and cell.pid only cover the ONE
recorded writer — a respawn-race survivor or a PRE-REINSTALL daemon whose pid is no longer the
recorded svc:cell keeps its feed thread running and is invisible to that cascade. `_akasha_daemon_pids`
/ `_reap_leaked_daemons` close that route by scanning /proc for EVERY `akasha.py --daemon` writer
bound to THIS data dir and reaping the orphans.

This eval spawns fake `--daemon` writers (a sleeper script literally named akasha.py) and asserts:
  • the scan matches a writer for OUR data dir,
  • it does NOT match a writer for a DIFFERENT data dir (scoping), nor a non-`--daemon` akasha.py,
  • the reaper kills the orphan while sparing a kept pid + the foreign-data-dir writer.

Linux /proc only (the scan is a no-op elsewhere); on such a host the eval self-skips. Run:
  python test/orphan_writer_reap_eval.py     (exit 0 = all pass / skipped)
"""
import os
import sys
import time
import tempfile
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

_FAIL = []


def check(name, ok, detail=""):
    print(("  OK    " if ok else "  !! FAIL  ") + name + (f"   [{detail}]" if detail and not ok else ""))
    if not ok:
        _FAIL.append(name)


def main():
    import akasha

    if not os.path.isdir("/proc"):
        print("  SKIP  /proc unavailable (non-Linux) — daemon reap is a documented no-op here.")
        print("RESULT: PASS (skipped).")
        return 0

    tmp = tempfile.mkdtemp(prefix="akasha_reapd_")
    base = os.path.join(tmp, "data")               # OUR data dir
    other = os.path.join(tmp, "other_data")        # a DIFFERENT cell's data dir
    os.makedirs(base, exist_ok=True)
    os.makedirs(other, exist_ok=True)
    # a sleeper script literally named akasha.py, so a spawned process's cmdline carries the writer
    # signature (`…/akasha.py --daemon`) exactly like the real Cell daemon.
    fake = os.path.join(tmp, "akasha.py")
    with open(fake, "w", encoding="utf-8") as fh:
        fh.write("import time\nimport sys\ntime.sleep(120)\n")

    def spawn(data_dir, *extra):
        env = dict(os.environ)
        if data_dir is not None:
            env["AKASHA_DATA_DIR"] = data_dir
        else:
            env.pop("AKASHA_DATA_DIR", None)
        return subprocess.Popen([sys.executable, fake, *extra], env=env,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    procs = []
    try:
        ours = spawn(base, "--daemon")             # a writer for OUR data dir  → must be found/reaped
        keep = spawn(base, "--daemon")             # another writer for OUR dir → spared via keep_pids
        foreign = spawn(other, "--daemon")         # a writer for a DIFFERENT dir → never touched
        client = spawn(base)                       # akasha.py WITHOUT --daemon (a CLI client) → never touched
        # an ONLOOKER whose single arg literally contains the substring "akasha.py --daemon" (like a
        # `ps|grep "akasha.py --daemon"`): token-based matching must NOT mistake it for a writer.
        env = dict(os.environ); env["AKASHA_DATA_DIR"] = base
        grep = subprocess.Popen([sys.executable, "-c", "import time;time.sleep(120)",
                                 "akasha.py --daemon"], env=env,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        procs = [ours, keep, foreign, client, grep]
        time.sleep(0.6)                            # let them show up in /proc

        found = {pid for pid, _c in akasha._akasha_daemon_pids(base)}
        check("scan: an `akasha.py --daemon` writer for OUR data dir is found", ours.pid in found,
              f"found={sorted(found)} ours={ours.pid}")
        check("scan scoping: a writer for a DIFFERENT data dir is NOT matched (AKASHA_DATA_DIR)",
              foreign.pid not in found, f"foreign={foreign.pid} found={sorted(found)}")
        check("scan scoping: an `akasha.py` process WITHOUT --daemon (a CLI client) is NOT matched",
              client.pid not in found, f"client={client.pid} found={sorted(found)}")
        check("scan precision: a grep-style onlooker with 'akasha.py --daemon' as ONE substring token "
              "is NOT matched (token-based, not substring)", grep.pid not in found,
              f"grep={grep.pid} found={sorted(found)}")

        reaped = set(akasha._reap_leaked_daemons(base, keep_pids={keep.pid}, grace_s=3.0))
        # NOTE: `ours` is a CHILD of this test, so after the reaper's signal it becomes a ZOMBIE
        # (defunct) until we wait() it — and os.kill(pid,0) still succeeds on a zombie. A REAL orphan
        # writer is re-parented to init and auto-reaped, so _pid_alive is accurate there; here we
        # wait() first to clear the zombie, then assert the process actually terminated.
        try:
            ours.wait(timeout=3)
        except Exception:
            pass
        check("reap: the orphan writer for OUR data dir is killed (terminated)",
              ours.poll() is not None and ours.pid in reaped, f"reaped={sorted(reaped)} rc={ours.poll()}")
        check("reap: a kept pid (keep_pids) is SPARED — no collateral to the live writer",
              keep.poll() is None and keep.pid not in reaped)
        check("reap: a foreign-data-dir writer is SPARED (scoping holds through the reaper)",
              foreign.poll() is None and foreign.pid not in reaped)
        check("reap: a non-daemon akasha.py client is SPARED", client.poll() is None)

        # The AUTOMATIC start-path cleanup (`_reap_stale_local` — "the stop collection folded into
        # the START path, no `stop` needed") must ALSO reap an orphan writer, so a plain re-run /
        # reinstall / restart self-heals the feed daemon exactly like `stop` does. No svc:cell /
        # cell.pid is recorded for `base` here, so the orphan is untracked — only the writer sweep
        # inside _reap_stale_local can find it.
        stale = spawn(base, "--daemon")            # a fresh UNTRACKED orphan writer for OUR data dir
        procs.append(stale)
        time.sleep(0.5)
        akasha._reap_stale_local(base, quiet=True)
        try:
            stale.wait(timeout=3)                  # clear the child zombie (see note above)
        except Exception:
            pass
        check("start-path (_reap_stale_local): an UNTRACKED orphan writer is reaped WITHOUT `stop` "
              "(the self-heal the feed daemon had broken)", stale.poll() is not None,
              f"rc={stale.poll()}")
        check("start-path (_reap_stale_local): a foreign-data-dir writer is still SPARED",
              foreign.poll() is None)
    finally:
        for p in procs:
            try:
                p.terminate(); p.wait(timeout=3)
            except Exception:
                try:
                    p.kill()
                except Exception:
                    pass

    print()
    total = 10
    if _FAIL:
        print(f"RESULT: FAIL — {len(_FAIL)}/{total} checks failed: {_FAIL}")
        return 1
    print("RESULT: PASS — orphan writer daemons (hence orphaned feed pollers) are found by /proc "
          "scan, scoped strictly to this data dir, and reaped on stop/restart/reinstall without "
          "collateral to the live writer or foreign cells.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
