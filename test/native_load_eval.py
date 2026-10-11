#!/usr/bin/env python3
"""
F49 — the always-on memory instruments NAME an allocation (memory-discipline R6).

The unattributed +2-3 GB boot climb was native and invisible to MemTop. Two always-on, zero-flag
tools attribute it; this eval proves each ATTRIBUTES a deliberate allocation:
  • F49-3 smaps rollup — /proc/self/smaps_rollup gives (anon_MB, file_map_MB), the heap-vs-mapped-file
    split on the Health line.
  • F49-2 NativeLoad — native_load(name) logs [NativeLoad] what=<name> Δrss=<MB> around a native site.

(The boot-window allocation tracer and its eval are deleted — ruling 4 October: tracing changes the
running product. A deeper investigation runs out of band, on a copy of the cell, with Python's own
`PYTHONTRACEMALLOC`.)

Run:  python test/native_load_eval.py   (exit 0 = all pass)
"""
import logging
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


class _Capture(logging.Handler):
    def __init__(self):
        super().__init__()
        self.lines = []

    def emit(self, record):
        try:
            self.lines.append(record.getMessage())
        except Exception:
            pass


def main():
    _linux = sys.platform.startswith("linux")

    # ── F49-3 smaps rollup ──
    from lib.akasha.kernel import _smaps_rollup
    anon, fmap = _smaps_rollup()
    check("F49-3 smaps rollup returns (anon_MB, file_map_MB) on Linux (or None off-Linux)",
          (not _linux) or (isinstance(anon, int) and isinstance(fmap, int) and anon >= 0),
          "anon=%s fmap=%s" % (anon, fmap))

    # ── F49-2 NativeLoad names a deliberate native-ish allocation ──
    cap = _Capture()
    nl_logger = logging.getLogger("Akasha.NativeLoad")
    nl_logger.addHandler(cap); nl_logger.setLevel(logging.WARNING)
    from lib.akasha.memtrace import native_load
    _blob = None
    with native_load("test.big_alloc", min_delta_mb=10):
        _blob = bytearray(60 * 1024 * 1024)          # 60 MB — a clear RSS bump
        _blob[::4096] = b"\x01" * (len(_blob) // 4096)   # touch pages so RSS actually grows
    nl_logger.removeHandler(cap)
    nl_line = [l for l in cap.lines if "[NativeLoad]" in l and "test.big_alloc" in l]
    if _linux:
        check("F49-2 native_load logs [NativeLoad] naming the site + Δrss", bool(nl_line),
              nl_line[:1])
        # the delta should be in the tens of MB (≈60), not zero
        ok_delta = bool(nl_line) and any("Δrss=" in l and int(l.split("Δrss=")[1].split("MB")[0]) >= 40
                                         for l in nl_line)
        check("F49-2 the logged Δrss reflects the ~60 MB allocation", ok_delta, nl_line[:1])
    else:
        check("F49-2 native_load runs off-Linux without error (no RSS to log)", True)
    del _blob


    print()
    if _fails:
        print("RESULT: FAIL — %d check(s): %s" % (len(_fails), "; ".join(_fails)))
        return 1
    print("RESULT: PASS — the smaps rollup splits heap from mapped files, and [NativeLoad] names a "
          "native allocation with its Δrss.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
