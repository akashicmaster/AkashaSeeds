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
must never be able to kill the writer. It is decided by DECLARED FACTS only (the purge order §4.5
deleted the NO_/FORCE_ environment switches): a serve-only portal never learns, the seeds line
learns on demand, Python >= 3.14 learns on demand, anything else learns at boot.

This test drives the REAL `_autolearn_disabled_reason` across the fact matrix and asserts the gate
returns skip/allow exactly as designed. If it ever regresses (autolearn silently re-enabled on a
fragile interpreter) this fails and the boot-crash class is back.

Run:  python test/autolearn_native_gate_eval.py
"""
import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

from lib.akasha.api import heart as K   # the gate lives in the heart's helper module (backend layout order 2026-09-20)

_results = []
def record(name, ok, detail=""):
    _results.append((name, ok, detail))
    print(f"  {'OK  ' if ok else '!! FAIL'}  {name:44} {detail}")


def _verdict(series=None, serve_only=False):
    if serve_only:
        os.environ["AKASHA_SERVE_ONLY"] = "1"
    else:
        os.environ.pop("AKASHA_SERVE_ONLY", None)
    try:
        return K._autolearn_disabled_reason(series)
    finally:
        os.environ.pop("AKASHA_SERVE_ONLY", None)


def main():
    py = sys.version_info[:2]
    print(f"\n  autolearn native-crash gate — running under Python {py[0]}.{py[1]}\n")
    fragile = py >= (3, 14)

    # 1. A service tier follows the interpreter: allowed < 3.14, skipped >= 3.14.
    d = _verdict("thesaurus")
    record("service tier follows interpreter", (d is not None) == fragile,
           f"reason={d!r} (fragile={fragile})")

    # 2. The seeds line learns on demand, on any interpreter.
    record("seeds line → skip (on demand)", _verdict("seeds14") is not None)

    # 3. A serve-only portal never learns, whatever the series.
    record("serve-only portal → skip", _verdict("thesaurus", serve_only=True) is not None)

    # 4. No environment switch exists to change any of this.
    os.environ["AKASHA_NO_AUTOLEARN"] = "1"
    try:
        record("a deleted switch changes nothing", (_verdict("thesaurus") is not None) == fragile)
    finally:
        os.environ.pop("AKASHA_NO_AUTOLEARN", None)

    # 5. The gate is pure/side-effect-free: calling it never imports numpy (import stays lazy,
    #    behind the gate, so a fragile numpy is never even loaded when skipped).
    _verdict("thesaurus")
    record("no numpy import as a side effect of the gate",
           "numpy" not in sys.modules, "(numpy must stay behind the skip)")

    passed = sum(1 for _, ok, _ in _results if ok); total = len(_results)
    print(f"\n  {passed}/{total} checks passed")
    if passed == total:
        print("\nRESULT: PASS — boot autolearn is gated by declared facts so numpy/BLAS can never "
              "hard-crash the writer at boot: on demand on the seeds line and on Python >= 3.14, "
              "never on a portal; the floor tier keeps the meaning layer alive.\n")
        return 0
    print("\nRESULT: FAIL — the autolearn native-crash gate regressed.\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
