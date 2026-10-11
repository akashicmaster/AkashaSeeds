#!/usr/bin/env python3
"""
F47-6.3 / F36 — the manual-restart marker keeps a stop/start from racing the guard tick.

`stop` takes the daemon down; the operator then starts a fresh one. In that gap the 5-min guard tick
must NOT cold-spawn its own daemon (two writers = the double-death class). The `stop` handler arms an
fsync'd marker; the guard tick DEFERS while it is fresh; the daemon clears it once it has booted; and
a stale marker (operator stopped and never restarted) ages out so the guard resumes its duty. This
eval drives those marker primitives directly.

Run:  python test/manual_restart_marker_eval.py   (exit 0 = all pass)
"""
import os
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def main():
    import importlib.util as _ilu
    spec = _ilu.spec_from_file_location("akasha_entry", os.path.join(ROOT, "akasha.py"))
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)

    base = tempfile.mkdtemp(prefix="manrestart_")

    # (0) nothing armed → guard is free to act
    check("no marker → guard is NOT deferred", not mod._manual_restart_active(base))

    # (1) stop arms it → guard defers
    mod._arm_manual_restart(base)
    check("marker file exists after arming", os.path.exists(mod._manual_restart_marker_path(base)))
    check("armed marker → guard tick defers", mod._manual_restart_active(base) is True)

    # (2) the daemon boot clears it → guard resumes
    mod._clear_manual_restart(base)
    check("daemon boot clears the marker → guard resumes", not mod._manual_restart_active(base))
    check("marker file removed", not os.path.exists(mod._manual_restart_marker_path(base)))

    # (3) a STALE marker (older than the TTL) ages out — the operator stopped and never restarted.
    # The TTL has a 10 s floor by design, so backdate well beyond it.
    p = mod._manual_restart_marker_path(base)
    with open(p, "w") as fh:
        fh.write(str(time.time() - (mod._manual_restart_ttl() + 30.0)))
    check("a stale (aged-out) marker does NOT defer the guard", not mod._manual_restart_active(base))
    check("the stale marker is cleared on read", not os.path.exists(p))

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("ALL PASS — the manual-restart marker defers the guard during a stop/start, is cleared when "
          "the daemon boots, and ages out if the operator never restarts (F36).")
    sys.exit(0)


if __name__ == "__main__":
    main()
