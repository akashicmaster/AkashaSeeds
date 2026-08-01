#!/usr/bin/env python3
"""
Boot-time numpy autolearn NATIVE-CRASH gate — regression for the silent Python-3.14 daemon death.

Story (docs/handoff/daemon-crash-ontology-reload-reconcile.md): the akashickitchen.net writer
daemon died silently and deterministically during boot on Python 3.14. It was proven NOT OOM
(flat RSS, no dmesg OOM record) and NOT the SpaCy weave (already made opt-in / regex-floor
default) and NOT Silica (pure Python). The one native code path left on the boot critical line is
the numpy/BLAS AUTOLEARN — `_schedule_semantic_learn` / `_schedule_node_learn` run PPMI+SVD and
random-walk matrices in background threads shortly after boot. A numpy/BLAS SEGFAULT is not a
Python exception, so the threads' try/except cannot catch it and it takes the whole writer down.

Fix (mirrors the weave opt-in exactly): `_autolearn_disabled_reason()` gates both schedulers.
Autolearn is OPTIONAL — the stdlib feature-hashing FLOOR still stamps every atom's vector — so it
must never be able to kill the writer. On Python >= 3.14 it is DEFAULT-OFF (opt back in, once the
numpy stack is verified, with AKASHA_FORCE_AUTOLEARN=1); below 3.14 numpy wheels are mature and it
stays on. AKASHA_NO_AUTOLEARN keeps its explicit always-off meaning.

This test drives the REAL `_autolearn_disabled_reason` from lib.akasha.kernel across the env/
interpreter matrix and asserts the gate returns skip/allow exactly as designed. If it ever regresses
(autolearn silently re-enabled on a fragile interpreter) this fails and the boot-crash class is back.

Run:  python test/autolearn_native_gate_eval.py
"""
import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

from lib.akasha import kernel as K

_results = []
def record(name, ok, detail=""):
    _results.append((name, ok, detail))
    print(f"  {'OK  ' if ok else '!! FAIL'}  {name:44} {detail}")


def _with_env(no_autolearn=None, force=None):
    """Set/clear the two env gates, return the real helper's verdict (reason or None)."""
    for k, v in (("AKASHA_NO_AUTOLEARN", no_autolearn), ("AKASHA_FORCE_AUTOLEARN", force)):
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    return K._autolearn_disabled_reason()


def main():
    py = sys.version_info[:2]
    print(f"\n  autolearn native-crash gate — running under Python {py[0]}.{py[1]}\n")
    fragile = py >= (3, 14)

    # 1. Default depends on the interpreter: allowed < 3.14, skipped >= 3.14.
    d = _with_env()
    record("default follows interpreter", (d is not None) == fragile,
           f"reason={d!r} (fragile={fragile})")

    # 2. Explicit NO always skips, on any interpreter.
    record("AKASHA_NO_AUTOLEARN=1 → skip", _with_env(no_autolearn="1") is not None)
    record("NO=1 skip is explicit", "AKASHA_NO_AUTOLEARN" in (_with_env(no_autolearn="1") or ""))

    # 3. FORCE overrides the interpreter gate (opt back in on a verified stack) but NOT explicit NO.
    record("FORCE=1 → allowed regardless of interpreter", _with_env(force="1") is None)
    record("explicit NO beats FORCE", _with_env(no_autolearn="1", force="1") is not None)

    # 4. NO=0 / off no longer force-disables (old bug: bare truthy-string check disabled on '0').
    off = _with_env(no_autolearn="0")
    record("NO=0 does not disable (only the interpreter gate may)", (off is not None) == fragile,
           f"reason={off!r}")

    # 5. The gate is pure/side-effect-free: calling it never imports numpy (import stays lazy,
    #    behind the gate, so a fragile numpy is never even loaded when skipped).
    _with_env()
    record("no numpy import as a side effect of the gate",
           "numpy" not in sys.modules, "(numpy must stay behind the skip)")

    # cleanup
    for k in ("AKASHA_NO_AUTOLEARN", "AKASHA_FORCE_AUTOLEARN"):
        os.environ.pop(k, None)

    passed = sum(1 for _, ok, _ in _results if ok); total = len(_results)
    print(f"\n  {passed}/{total} checks passed")
    if passed == total:
        print("\nRESULT: PASS — boot autolearn is gated so numpy/BLAS can never hard-crash the "
              "writer at boot: default-off on Python >= 3.14, opt-in via AKASHA_FORCE_AUTOLEARN, "
              "explicit AKASHA_NO_AUTOLEARN honored, floor tier keeps the meaning layer alive.\n")
        return 0
    print("\nRESULT: FAIL — the autolearn native-crash gate regressed.\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
