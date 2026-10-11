#!/usr/bin/env python3
"""
Group 2, read 2 — the store's OPEN states itself.

Directive 2026-09-27 §3. The steady band's jump is complete before the first phase-2 line
(`rss=4984MB` on 09-26), and the store's open was the one long phase with no line of its own. The
always-on line below closed Group 2. (The allocation tracer is deleted — ruling 4 October: tracing
changes the running product; a deeper investigation runs out of band with `PYTHONTRACEMALLOC`.)
This eval holds the line on real stores:

  1. ALWAYS ON — reopening a multi-bank store logs ONE line at INFO:
       [Silica] open rss_before=… after_replay=… after_trim=… anon=… fmap=… banks=8 records=N t=…
                    avail_start=… avail_end=… swapin_pages=… majflt=… read_bytes=…
     with `records` equal to the records the WAL actually holds and every figure measured — the last
     five over the replay span (directive 2026-10-03 item 3), checked as deltas on known inputs;
  2. a per-guest cell (banks=1, a few records) logs the same fields at DEBUG only and is NOT trimmed
     (`after_trim=-`), so a request-path open pays for nothing;

Run:  python test/silica_open_line_eval.py     (exit 0 = all pass)
"""
import logging
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


class _Cap(logging.Handler):
    def __init__(self):
        super().__init__(logging.DEBUG)
        self.rows = []

    def emit(self, record):
        self.rows.append((record.levelno, record.getMessage()))


def _fill(d, banks, n, blob=64):
    from lib.akasha.backends.silica import SilicaStore
    st = SilicaStore(d, banks=banks, sync="batch")
    for i in range(0, n, 500):
        tx = st.begin()
        for j in range(i, min(n, i + 500)):
            tx.put(b"@eval:%d" % (j % 97), b"k%08d" % j, b"v" * blob)
        tx.commit()
    st.close()


def _fields(line):
    out = {}
    for tok in line.split():
        if "=" in tok:
            k, v = tok.split("=", 1)
            out[k] = v
    return out


def main():
    print("=" * 78)
    print("Group 2 read 2 — the store's open states itself; the tracer starts at process entry")
    print("=" * 78)
    from lib.akasha.backends.silica import SilicaStore

    print("\n  ── 1. the large store's open line (always on) ──")
    big = tempfile.mkdtemp(prefix="open_big_")
    n_big = SilicaStore.OPEN_LINE_MIN_RECORDS // 4       # banks=8 alone makes it the large store
    _fill(big, 8, n_big)
    cap = _Cap()
    lg = logging.getLogger("Silica")
    lg.addHandler(cap); lg.setLevel(logging.DEBUG)
    try:
        SilicaStore(big, banks=8, sync="batch").close()
    finally:
        lg.removeHandler(cap)
    opens = [(lv, m) for lv, m in cap.rows if m.startswith("[Silica] open ")]
    check("ONE `[Silica] open` line for the reopen", len(opens) == 1, str(opens))
    lv, line = opens[0] if opens else (0, "")
    f = _fields(line)
    check("…at INFO (it is always on, no flag)", lv == logging.INFO, logging.getLevelName(lv))
    for key in ("rss_before", "after_replay", "after_trim", "anon", "fmap"):
        check("…`%s` is measured (MB)" % key, f.get(key, "").endswith("MB"), f.get(key))
    check("…`banks=8` and `records=` equals the records the WAL holds (%d)" % n_big,
          f.get("banks") == "8" and f.get("records") == str(n_big), "%s %s" % (f.get("banks"), f.get("records")))
    check("…and `t=` states the open's duration", f.get("t", "").endswith("s"), f.get("t"))

    # directive 2026-10-03 item 3 — the replay span's own figures, on the same line
    on_linux = os.path.exists("/proc/self/stat")
    for key in ("avail_start", "avail_end"):
        check("…`%s` is the host's MemAvailable (MB)" % key,
              f.get(key, "").endswith("MB") if on_linux else key in f, f.get(key))
    for key in ("swapin_pages", "majflt", "read_bytes"):
        check("…`%s` is a count over the replay span" % key,
              (f.get(key, "").isdigit() if on_linux else key in f), f.get(key))
    import lib.akasha.backends.silica as _SB
    _real_io = _SB._replay_io
    _seq = iter([(9000, 10, 100, 4096), (2000, 25, 1100, 4096 + 7 * 1048576)])
    _SB._replay_io = lambda: next(_seq)
    cap2 = _Cap()
    lg.addHandler(cap2)
    try:
        SilicaStore(big, banks=8, sync="batch").close()
    finally:
        lg.removeHandler(cap2)
        _SB._replay_io = _real_io
    f2 = _fields(next((m for _lv, m in cap2.rows if m.startswith("[Silica] open ")), ""))
    check("the figures are the replay span's: start/end MemAvailable, and the DELTAS of swap-in, "
          "major faults and bytes read between them",
          (f2.get("avail_start"), f2.get("avail_end"), f2.get("swapin_pages"), f2.get("majflt"),
           f2.get("read_bytes")) == ("9000MB", "2000MB", "15", "1000", str(7 * 1048576)),
          str({kk: f2.get(kk) for kk in ("avail_start", "avail_end", "swapin_pages", "majflt",
                                          "read_bytes")}))

    print("\n  ── 2. a per-guest cell pays for nothing ──")
    small = tempfile.mkdtemp(prefix="open_small_")
    _fill(small, 1, 50)
    cap = _Cap()
    lg.addHandler(cap)
    try:
        SilicaStore(small, banks=1, sync="batch").close()
    finally:
        lg.removeHandler(cap)
    s_opens = [(lv, m) for lv, m in cap.rows if m.startswith("[Silica] open ")]
    check("a banks=1 cell's open line is DEBUG, not INFO",
          len(s_opens) == 1 and s_opens[0][0] == logging.DEBUG, str(s_opens))
    check("…and it is not trimmed (`after_trim=-`)",
          bool(s_opens) and _fields(s_opens[0][1]).get("after_trim") == "-", str(s_opens[:1]))

    print()
    if _fails:
        print("FAILED (%d): %s" % (len(_fails), "; ".join(_fails)))
        sys.exit(1)
    print("RESULT: PASS — the large store's open states rss_before / after_replay / after_trim / "
          "anon / fmap / banks / records / t on every boot; a guest cell pays nothing.")
    sys.exit(0)


if __name__ == "__main__":
    main()
