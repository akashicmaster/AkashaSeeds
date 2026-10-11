#!/usr/bin/env python3
"""
F44 Part A1 — the permanent health heartbeat + high-water MemTop name the OOM accumulator.

The writer OOMs intermittently and SILENTLY: BootWatch stops at settle, so the minutes leading up
to a mid-life kill had no memory trace at all. A1.1 adds a heartbeat that NEVER turns off and prints
one line a minute carrying the four quantities that tell an accumulator from a spike — rss /
MemAvailable / live guest cells / dive admit+refuse / pulse emit+bulk. A1.2/A1.3 fire a MemTop dump
(largest containers + Silica @route sizes + the guest-cell footprint) the first time RSS crosses the
4 GB and 6 GB marks. This eval drives those code paths directly (no 60 s wait, no real OOM) and
asserts the lines carry the right fields.

Run:  python test/health_heartbeat_eval.py   (exit 0 = all pass)
"""
import hashlib
import logging
import os
import sys
import tempfile

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
    from lib.akasha.kernel import KernelDispatcher, _DIVE_ADMISSION, _rss_mb, _mem_available_mb
    from api.gateway import AkashaGateway
    import lib.akasha.concepts.pulse as pulse_mod

    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="health_"))
    gw = AkashaGateway(kernel_client=k)
    gw.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                 "params": {"session_token": "admin", "data": {"user_name": "admin",
                            "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    cap = _Capture()
    root = logging.getLogger()
    root.addHandler(cap)
    root.setLevel(logging.INFO)

    # ── helpers are Linux /proc readers — present or gracefully None ──
    rss = _rss_mb()
    check("A1.1 _rss_mb returns a positive MB on Linux (or None off-Linux)",
          rss is None or rss > 0, f"rss={rss}")
    avail = _mem_available_mb()
    check("A1.1 _mem_available_mb returns MB (or None off-Linux)",
          avail is None or avail > 0, f"avail={avail}")

    # ── the counters the heartbeat reads ──
    _DIVE_ADMISSION.stats()  # smoke
    st = _DIVE_ADMISSION.stats()
    check("A1.1 dive admission exposes admitted + refused counters",
          "admitted" in st and "refused" in st, str(st))
    pe = pulse_mod.emit_counters()
    check("A1.1 pulse exposes emit + bulk lifetime counters",
          set(pe) >= {"emits", "bulk"}, str(pe))

    # ── MemTop dump (A1.2 content + A1.3 guest-cell footprint) fires on demand ──
    cap.lines.clear()
    k._dump_memtop(rss or 4096, reason="hw>4096MB")
    joined = "\n".join(cap.lines)
    check("A1.2 MemTop reports rss + the high-water reason", "[MemTop]" in joined and "hw>4096MB" in joined,
          joined[:160])
    check("A1.3 MemTop includes the guest-cell footprint line", "guest cells:" in joined,
          [l for l in cap.lines if "guest cells" in l][:1])

    # ── the heartbeat thread prints a [Health] line with all four quantities ──
    # Drive exactly one iteration: let the FIRST is_shutting_down() poll pass (so the health line +
    # high-water dump run), then have the patched sleep flip it True so the loop returns cleanly on
    # the next poll — no 60 s wait, no SystemExit noise, no real OOM.
    import lib.akasha.lifecycle as lifecycle
    import threading
    import time as _time
    cap.lines.clear()
    os.environ["AKASHA_HEARTBEAT_MEMTOP_MB"] = "1"      # force the high-water dump on the first tick

    _orig_shutdown = lifecycle.is_shutting_down
    _orig_sleep = _time.sleep
    _state = {"ticks": 0}
    done = threading.Event()

    def _fake_shutdown():
        return _state["ticks"] > 0

    def _fake_sleep(_):
        _state["ticks"] += 1        # after the first health line, the next poll ends the loop
        done.set()

    lifecycle.is_shutting_down = _fake_shutdown
    _time.sleep = _fake_sleep
    try:
        # F60 §2 — the writer-role hook now starts the health heartbeat at kernel __init__ (independent
        # of the ontology-load path), which sets the once-guard. Reset it so THIS controlled invocation
        # (with the patched sleep/shutdown) runs and its [Health] line is captured.
        k._heartbeat_running = False
        k._schedule_health_heartbeat()
        done.wait(timeout=5.0)
        _orig_sleep(0.3)            # let the worker's next poll observe shutdown and return
    finally:
        lifecycle.is_shutting_down = _orig_shutdown
        _time.sleep = _orig_sleep

    hb = [l for l in cap.lines if l.startswith("[Health]")]
    ok_line = bool(hb) and all(tok in hb[0] for tok in ("rss=", "avail=", "guests=", "dive(", "pulse("))
    check("A1.1 heartbeat prints a [Health] line with rss/avail/guests/dive/pulse", ok_line,
          (hb[0] if hb else "no [Health] line"))
    memtop_hw = any("high-water mark" in l for l in cap.lines)
    check("A1.2 heartbeat fires the MemTop dump at the high-water mark", memtop_hw,
          [l for l in cap.lines if "high-water" in l][:1])

    root.removeHandler(cap)
    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("ALL PASS — the permanent heartbeat names rss/avail/guests/dive/pulse every tick (A1.1); "
          "the high-water MemTop dumps the largest containers + Silica @routes + the guest-cell "
          "footprint (A1.2/A1.3).")
    sys.exit(0)


if __name__ == "__main__":
    main()
