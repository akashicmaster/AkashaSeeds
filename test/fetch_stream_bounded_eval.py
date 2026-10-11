#!/usr/bin/env python3
"""
F50 — the last +3 GB has a name: `fetch_stream` sorted the WHOLE store to return `limit` rows.

The overnight AllocTrace (F49) named it: `fetch_stream(limit)` / `get_all_chunks(limit)` on the
Silica store scanned all 4.6 M atoms, JSON-decoded EVERY record, built a ~10 M-entry list, sorted
the whole store, and returned only `limit` rows — the `json/decoder.py:361 — 673 MB × 8 M objects`
top site, fired by the FIRST search-class request after boot (kernel.py `nucleus.core.fetch_stream`).

The fix makes "newest / sample K" O(K), never O(store) — F33's access-degree rule applied to
recency:
  • fetch_stream(K)      — STREAMS the @CHUNKS index (route value = seq, RAM-resident: no pread,
                           no content decode) keeping only a bounded top-K heap of (key, seq),
                           then point-gets + decodes exactly the K winners. K decodes, O(K) memory.
  • get_all_chunks(K)    — snapshots ≤K index KEYS (scan_keys stops at the cap), then decodes ≤K
                           values. The old form snapshotted every key AND decoded until the break.

This eval proves the O(K) contract by the numbers the OOM was made of — JSON decodes, value
point-gets, entries-walked (F50 §4: the probe now weights by entries iterated, so one scan that
walks the whole store no longer hides behind a call count of 1), peak RSS, wall — and that
fetch_stream still returns the K NEWEST rows.

Run:  python test/fetch_stream_bounded_eval.py   (exit 0 = all pass)
"""
import os, sys, time, tempfile, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

from lib.akasha.backends import silica_backend as _sb
from lib.akasha.backends.silica_backend import SilicaBackend

_results = []
def record(name, ok, detail=""):
    _results.append((name, ok, detail))
    print(f"  {'OK  ' if ok else '!! FAIL'}  {name:34} {detail}")


# ── count JSON decodes: the memory the OOM was made of (json.loads of a chunk record) ──
# The module functions call the global `_u`; rebinding the module attribute intercepts every decode.
_DECODES = {"n": 0}
_orig_u = _sb._u
def _counting_u(b):
    if b:
        _DECODES["n"] += 1
    return _orig_u(b)
_sb._u = _counting_u


def _rss_mb():
    try:
        with open("/proc/self/statm") as f:
            pages = int(f.read().split()[1])
        return pages * (os.sysconf("SC_PAGE_SIZE") / (1024.0 * 1024.0))
    except Exception:
        try:
            import resource
            return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
        except Exception:
            return 0.0


def main():
    print("\n  F50 — a 'newest/sample K' read is O(K), never O(store)\n")
    work = tempfile.mkdtemp(prefix="akasha_f50_")
    be = SilicaBackend(os.path.join(work, "b.db"), is_volatile=True)
    store = be._store
    try:
        # A store big enough that O(store) decodes/memory would be unmistakable vs O(K).
        N = 50000
        t_build = time.time()
        for i in range(N):
            be.put_chunk_raw(f"k{i}", f"content number {i} with several real words here",
                             f'{{"i":{i}}}', "auth", "verified", 1000.0 + i)
        print(f"  (built {N} atoms in {time.time() - t_build:.1f}s)\n")
        newest_keys = {f"k{i}" for i in range(N - 10, N)}   # the last 10 committed = highest seq

        # ── (1) fetch_stream(K): decodes == K, value point-gets == K, NOT O(store) ──
        K = 10
        store.probe_reset(); _DECODES["n"] = 0
        rss0 = _rss_mb(); t0 = time.time()
        rows = be.fetch_stream(K)
        wall = time.time() - t0; rss1 = _rss_mb()
        pr = store.probe_read()
        record("fetch_stream: decodes <= K+e", _DECODES["n"] <= K + 2,
               f"decodes={_DECODES['n']} (K={K}; O(store) would be {N})")
        record("fetch_stream: value point_gets <= K+e", pr["point_get"] <= K + 2,
               f"point_get={pr['point_get']}")
        record("fetch_stream: zero full_scan", pr["full_scan"] == 0, f"full_scan={pr['full_scan']}")
        record("fetch_stream: RSS delta < 50MB", (rss1 - rss0) < 50.0,
               f"drss={rss1 - rss0:.1f}MB")
        record("fetch_stream: wall < 1s", wall < 1.0, f"wall={wall * 1000:.0f}ms")
        record("fetch_stream: returns K rows", len(rows) == K, f"rows={len(rows)}")
        record("fetch_stream: rows are the K NEWEST (highest seq)",
               {r["key"] for r in rows} == newest_keys,
               f"got={sorted(r['key'] for r in rows)}")

        # ── (2) get_all_chunks(limit=100): decodes <= limit, KEY snapshot walk <= limit ──
        L = 100
        store.probe_reset(); _DECODES["n"] = 0
        rss0 = _rss_mb(); t0 = time.time()
        rows2 = be.get_all_chunks(limit=L)
        wall2 = time.time() - t0; rss1 = _rss_mb()
        pr2 = store.probe_read()
        record("get_all_chunks: decodes <= limit+e", _DECODES["n"] <= L + 2,
               f"decodes={_DECODES['n']} (limit={L}; O(store) would be {N})")
        record("get_all_chunks: entries_walked <= limit+e (F50 §4)", pr2["entries_walked"] <= L + 2,
               f"entries_walked={pr2['entries_walked']} (key snapshot stops at the cap)")
        record("get_all_chunks: zero full_scan", pr2["full_scan"] == 0, f"full_scan={pr2['full_scan']}")
        record("get_all_chunks: RSS delta < 50MB", (rss1 - rss0) < 50.0, f"drss={rss1 - rss0:.1f}MB")
        record("get_all_chunks: wall < 1s", wall2 < 1.0, f"wall={wall2 * 1000:.0f}ms")
        record("get_all_chunks: returns limit rows", len(rows2) == L, f"rows={len(rows2)}")

        # ── (3) unbounded get_all_chunks still reads the whole store (export path intact) ──
        _DECODES["n"] = 0
        allc = be.get_all_chunks()
        record("get_all_chunks(None): whole store (export unchanged)", len(allc) >= N,
               f"rows={len(allc)} (corpus>={N})")

        # ── (4) F50 §4 — the probe now weights by entries walked, so a store-wide scan is
        #        visible even though it is ONE call. fetch_stream streams the whole index (O(store)
        #        walk) but stays O(K) in DECODES — the metric that separates cheap RAM walk from
        #        the multi-GB decode is exactly what the eval asserts above.
        store.probe_reset()
        be.fetch_stream(K)
        pr3 = store.probe_read()
        record("probe weights by entries_walked (F50 §4)", pr3["entries_walked"] >= N,
               f"entries_walked={pr3['entries_walked']} (>= {N}: the full index stream is now visible)")
    finally:
        try: be.close()
        except Exception: pass
        shutil.rmtree(work, ignore_errors=True)
        _sb._u = _orig_u

    passed = sum(1 for _, ok, _ in _results if ok); total = len(_results)
    print(f"\n  {passed}/{total} checks passed")
    if passed == total:
        print("\nRESULT: PASS — fetch_stream / get_all_chunks(limit) are O(limit) in decodes AND "
              "memory: a newest/sample-K read no longer JSON-decodes or sorts the whole store. The "
              "+3 GB boot/search allocation site is closed; the probe now weights by entries walked "
              "so a store-wide scan can never again hide behind a call count of 1.\n")
        return 0
    print("\nRESULT: FAIL — a K-read still touches the whole store (the +3 GB site is not closed).\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
