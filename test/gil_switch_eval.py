#!/usr/bin/env python3
"""
The writer daemon's GIL switch interval — why an atom step cost 1.7 s on a busy cell.

Frontend note 2026-09-28, "needs platform" 2: 400 small atoms took 990 s (one 404-step job: 680 s)
while the IPC pool was saturated. Measured here: the same atom step costs ~6 ms alone and ~1.4 s
beside four CPU-bound threads. It is the GIL CONVOY: the write path releases the GIL tens of times a
step (~26 fsyncs per atom step on a `sync=full` nucleus, plus the JCL worker ↔ WriteQueue handoff),
and each time it waits up to one switch interval (CPython's default 5 ms) per CPU-bound thread to
get it back. The daemon now sets the interval to 1 ms (`AKASHA_GIL_SWITCH_MS`).

This eval holds, on a real process entry and a real convoy:

  1. importing `akasha.py` on the daemon path sets the switch interval to 1 ms and records the old
     value; the override is read; an out-of-range override is ignored; a portal (`--serve`) and a
     plain import are untouched;
  2. only the WRITER logs one `[boot] gil switch_interval=…` line — not logging setup, which every
     cron-heal probe that defers also runs (directive 10-02 §4), and not merely a `--daemon` holding
     the boot lock, which wrote it a second time per deploy (directive 10-03 item 5): the line comes
     after the kernel is online and only where that kernel started the writer-role daemons;
  3. THE CONVOY, measured: an fsync-bound thread beside four CPU-bound threads makes at least TWICE
     the progress at 1 ms as at 5 ms (≈5× measured when this landed).

Run:  python test/gil_switch_eval.py     (exit 0 = all pass)
"""
import json
import os
import subprocess
import sys
import tempfile
import threading
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _child(argv, env_ms=None):
    env = dict(os.environ)
    env.pop("AKASHA_GIL_SWITCH_MS", None)
    if env_ms is not None:
        env["AKASHA_GIL_SWITCH_MS"] = env_ms
    src = ("import sys, json; sys.path.insert(0, %r); sys.argv = ['akasha.py'] + %r\n"
           "import akasha\n"
           "print('R ' + json.dumps({'now': sys.getswitchinterval(), 'was': akasha._GIL_SWITCH_WAS}))"
           % (ROOT, argv))
    p = subprocess.run([sys.executable, "-c", src], cwd=ROOT, env=env, capture_output=True,
                       text=True, timeout=120)
    for ln in p.stdout.splitlines():
        if ln.startswith("R "):
            return json.loads(ln[2:])
    return {"err": p.stderr[-300:]}


def _convoy(sw, secs=2.0, busy=4):
    """(cpu units, fsyncs) done in `secs` by `busy` CPU-bound threads beside one fsync-bound one."""
    old = sys.getswitchinterval()
    sys.setswitchinterval(sw)
    stop = [False]
    counts = [0] * busy
    io = [0]
    path = os.path.join(tempfile.mkdtemp(prefix="gil_"), "f")

    def cpu(i):
        while not stop[0]:
            x = 0
            for k in range(2000):
                x += k * k
            counts[i] += 1

    def fs():
        fd = os.open(path, os.O_CREAT | os.O_WRONLY, 0o600)
        while not stop[0]:
            os.write(fd, b"x" * 64)
            os.fsync(fd)
            io[0] += 1
        os.close(fd)
    ts = [threading.Thread(target=cpu, args=(i,)) for i in range(busy)] + [threading.Thread(target=fs)]
    for t in ts:
        t.start()
    time.sleep(secs)
    stop[0] = True
    for t in ts:
        t.join()
    sys.setswitchinterval(old)
    return sum(counts), io[0]


def main():
    print("=" * 78)
    print("The writer daemon's GIL switch interval")
    print("=" * 78)

    print("\n  ── 1. set at process entry, on the daemon path only ──")
    r = _child(["--daemon"])
    check("--daemon → 1 ms, and the previous value (5 ms) is recorded",
          abs(r.get("now", 0) - 0.001) < 1e-9 and abs((r.get("was") or 0) - 0.005) < 1e-9, str(r))
    r = _child(["--daemon"], "0.5")
    check("AKASHA_GIL_SWITCH_MS=0.5 is read", abs(r.get("now", 0) - 0.0005) < 1e-9, str(r))
    r = _child(["--daemon"], "500")
    check("an out-of-range override is ignored (interval left at 5 ms)",
          abs(r.get("now", 0) - 0.005) < 1e-9 and r.get("was") is None, str(r))
    r = _child(["--serve"])
    check("a portal (--serve) is untouched", abs(r.get("now", 0) - 0.005) < 1e-9 and r.get("was") is None,
          str(r))

    print("\n  ── 2. the boot line: the writer only, once it holds the boot lock ──")
    # Directive 2026-10-02 §4: logged at logging setup, the line was written by every cron-heal
    # probe (a `--daemon` that finds a daemon serving and defers) — 412 times in two days.
    src = open(os.path.join(ROOT, "akasha.py"), encoding="utf-8").read()
    main_src = src[src.find("\ndef main("):]
    i = main_src.find("_setup_logging(_root, _is_cgi, arm_fault=not _short_lived)")
    check("logging setup no longer writes it",
          i > 0 and "gil switch_interval" not in main_src[i:i + 1200]
          and "_log_gil_switch" not in main_src[i:i + 1200])
    calls = [j for j in range(len(main_src)) if main_src.startswith("_log_gil_switch()", j)]
    locks = [j for j in range(len(main_src))
             if main_src.startswith("_HELD_BOOT_LOCK = _acquire_boot_lock(", j)]
    defers = [j for j in range(len(main_src)) if main_src.startswith("deferring", j)]
    check("one call site in main(), AFTER every boot-lock acquisition and every defer-and-return",
          len(calls) == 1 and locks and calls[0] > max(locks) and defers and calls[0] > max(defers),
          "calls=%s locks=%s last_defer=%s" % (calls, locks, max(defers) if defers else None))
    seg = main_src[max(locks):calls[0]] if calls and locks else ""
    check("…between the lock and the call, every path that does not hold the lock exits",
          "_HELD_BOOT_LOCK is None" in seg and "sys.exit(1)" in seg and "return" in seg, seg[:80])
    # Directive 2026-10-03 item 5: logged at the lock, a deploy still wrote it TWICE — the `--daemon`
    # launcher and the cell. Only the process whose KERNEL started the writer-role daemons owns the
    # writer, so the call sits after the kernel exists and is guarded by that fact.
    online = main_src.find('log.info("Kernel online.')
    guard = main_src.rfind("_writer_daemons_started", 0, calls[0]) if calls else -1
    check("the call comes after the kernel is online, guarded by `_writer_daemons_started`",
          calls and 0 < online < guard < calls[0] and calls[0] - guard < 120,
          "online=%s guard=%s call=%s" % (online, guard, calls[0] if calls else None))
    flag = subprocess.run(
        [sys.executable, "-c",
         "import sys, os, json, tempfile, hashlib; sys.path.insert(0, %r)\n"
         "os.environ['AKASHA_SKIP_AUTOINSTALL'] = '1'\n"
         "from lib.akasha.kernel import KernelDispatcher\n"
         "KernelDispatcher._boot_load_ontology = lambda self: None\n"
         "k = KernelDispatcher(series='seeds', base_dir=tempfile.mkdtemp(prefix='gil_k_'))\n"
         "print('F ' + json.dumps(getattr(k, '_writer_daemons_started', None)))" % ROOT],
        cwd=ROOT, env=dict(os.environ, AKASHA_SERVE_ONLY=""), capture_output=True, text=True,
        timeout=300)
    flag_so = subprocess.run(
        [sys.executable, "-c",
         "import sys, os, json, tempfile; sys.path.insert(0, %r)\n"
         "os.environ['AKASHA_SKIP_AUTOINSTALL'] = '1'\n"
         "from lib.akasha.kernel import KernelDispatcher\n"
         "KernelDispatcher._boot_load_ontology = lambda self: None\n"
         "k = KernelDispatcher(series='seeds', base_dir=tempfile.mkdtemp(prefix='gil_k_'))\n"
         "print('F ' + json.dumps(getattr(k, '_writer_daemons_started', None)))" % ROOT],
        cwd=ROOT, env=dict(os.environ, AKASHA_SERVE_ONLY="1"), capture_output=True, text=True,
        timeout=300)

    def _f(p):
        return next((ln[2:] for ln in p.stdout.splitlines() if ln.startswith("F ")), p.stderr[-200:])
    check("…a writer kernel has the flag set; a serve-only kernel does not (it never writes the line)",
          _f(flag) == "true" and _f(flag_so) in ("false", "null"), "%s / %s" % (_f(flag), _f(flag_so)))

    def _logged(argv):
        p = subprocess.run([sys.executable, "-c",
                            "import sys, logging; sys.path.insert(0, %r); sys.argv = ['akasha.py'] + %r\n"
                            "logging.basicConfig(level=logging.INFO, stream=sys.stdout, format='%%(message)s')\n"
                            "import akasha; akasha._log_gil_switch()" % (ROOT, argv)],
                           cwd=ROOT, env={k: v for k, v in os.environ.items()
                                          if k != "AKASHA_GIL_SWITCH_MS"},
                           capture_output=True, text=True, timeout=120)
        return [ln for ln in p.stdout.splitlines() if "gil switch_interval" in ln]
    got = _logged(["--daemon"])
    check("the writer's call writes ONE line naming the interval and the old value",
          len(got) == 1 and "switch_interval=1.00ms (was 5.00ms)" in got[0], str(got))
    check("a process that did not set it (a portal) writes nothing", _logged(["--serve"]) == [])

    print("\n  ── 3. the convoy, measured ──")
    c5, io5 = _convoy(0.005)
    c1, io1 = _convoy(0.001)
    ratio = (io1 / io5) if io5 else float("inf")
    check("an fsync-bound thread beside four CPU-bound threads makes ≥ 2× the progress at 1 ms "
          "as at 5 ms", ratio >= 2.0, "fsyncs %d → %d (%.1f×); cpu units %d → %d (%+.0f%%)"
          % (io5, io1, ratio, c5, c1, 100.0 * (c1 - c5) / max(1, c5)))

    print()
    if _fails:
        print("FAILED (%d): %s" % (len(_fails), "; ".join(_fails)))
        sys.exit(1)
    print("RESULT: PASS — the writer daemon runs at a 1 ms GIL switch interval (overridable, daemon "
          "only), only the process whose kernel owns the writer says so, and its I/O-bound threads make several times the progress beside "
          "CPU-bound request threads.")
    sys.exit(0)


if __name__ == "__main__":
    main()
