#!/usr/bin/env python3
"""
Silica vs SQLite — operational metrics (write/read latency, WAL bloat, checkpoint time,
cache hit-rate, memory under load, boundary-condition parity).

Direct-backend benchmark (no kernel boot / no ontology load, so it runs in a constrained
container). Writes N content-addressed atoms to each backend and measures the seven metrics the
release check calls for. SQLite is the oracle for the boundary comparison.

Run:  python test/silica_metrics.py [N]        (default N=8000)
"""
import os, sys, time, gc, hashlib, tempfile, shutil, random, statistics

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

from lib.akasha.backends.sqlite import SQLiteBackend
from lib.akasha.backends.silica_backend import SilicaBackend

N = int(sys.argv[1]) if len(sys.argv) > 1 else 8000


def rss_mb():
    try:
        for line in open("/proc/self/status"):
            if line.startswith("VmRSS:"):
                return int(line.split()[1]) / 1024.0
    except Exception:
        pass
    import resource
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


def pctl(xs, p):
    if not xs:
        return 0.0
    xs = sorted(xs)
    k = min(len(xs) - 1, int(round((p / 100.0) * (len(xs) - 1))))
    return xs[k] * 1000.0  # ms


def wal_bytes(kind, path):
    """On-disk WAL/journal footprint."""
    total = 0
    if kind == "sqlite":
        for suf in ("-wal", "-shm"):
            p = path + suf
            if os.path.exists(p):
                total += os.path.getsize(p)
    else:  # silica: bank-*.wal + coord.wal under the .silica dir
        d = path
        if os.path.isdir(d):
            for f in os.listdir(d):
                if f.endswith(".wal"):
                    total += os.path.getsize(os.path.join(d, f))
    return total


def make(kind, base):
    if kind == "sqlite":
        db = os.path.join(base, "nucleus.db")
        return SQLiteBackend(db, sync_mode="FULL"), db
    b = SilicaBackend(os.path.join(base, "nucleus"), sync_mode="FULL")
    return b, b._dir


def checkpoint(kind, be):
    if kind == "sqlite":
        be.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    else:
        be.checkpoint()


def bench(kind):
    base = tempfile.mkdtemp(prefix=f"met_{kind}_")
    gc.collect()
    rss0 = rss_mb()
    be, path = make(kind, base)
    keys = []
    meta = '{"type":"note"}'
    # ── write latency ──
    wlat = []
    for i in range(N):
        content = f"atom-{i}-{'x'*40}"
        k = hashlib.sha256(content.encode()).hexdigest()
        t = time.perf_counter()
        be.put_chunk_raw(k, content, meta, "bench", "active", 1785000000.0 + i)
        wlat.append(time.perf_counter() - t)
        keys.append(k)
    rss_after_write = rss_mb()
    wal_after_write = wal_bytes(kind, path)

    # ── read latency (cold: each key once, random order) ──
    rlat = []
    for k in random.sample(keys, min(N, 4000)):
        t = time.perf_counter()
        be.get_chunk_raw(k)
        rlat.append(time.perf_counter() - t)

    # ── cache hit-rate (Silica disk-value mode only): read the built-in SLRU counters over a
    #    repeated hot working set. In RAM mode there is no read cache (the index IS the value).
    hit = miss = 0
    store = be._store if kind == "silica" else None
    cstats0 = (store.stats() or {}).get("cache") if store is not None else None
    if cstats0:                                    # Silica disk mode → cache present + instrumented
        hot = keys[:min(2000, len(keys))]
        for k in hot:                              # warm
            be.get_chunk_raw(k)
        h0 = store.stats()["cache"]["hits"]; m0 = store.stats()["cache"]["misses"]
        for _ in range(3):                         # repeated hot reads should hit
            for k in hot:
                be.get_chunk_raw(k)
        cs = store.stats()["cache"]
        hit = cs["hits"] - h0
        miss = cs["misses"] - m0

    # ── checkpoint time + WAL shrink ──
    t = time.perf_counter()
    checkpoint(kind, be)
    ckpt_s = time.perf_counter() - t
    wal_after_ckpt = wal_bytes(kind, path)

    result = {
        "write_p50": pctl(wlat, 50), "write_p99": pctl(wlat, 99),
        "write_mean": (sum(wlat) / len(wlat)) * 1000.0,
        "read_p50": pctl(rlat, 50), "read_p99": pctl(rlat, 99),
        "wal_write_mb": wal_after_write / 1e6, "wal_ckpt_mb": wal_after_ckpt / 1e6,
        "ckpt_ms": ckpt_s * 1000.0,
        "rss_delta_mb": rss_after_write - rss0,
        "cache_hit_pct": (100.0 * hit / (hit + miss)) if (hit + miss) else None,
        "throughput_ws": N / sum(wlat),
    }
    try:
        be.close()
    except Exception:
        pass
    shutil.rmtree(base, ignore_errors=True)
    gc.collect()
    return result


def boundary_parity():
    """Identical edge ops on both backends → field-by-field parity (SQLite is the oracle)."""
    cases = [
        ("empty content", ""),
        ("large 64KB", "L" * 65536),
        ("unicode", "日本語 café 🍶 —"),
        ("newlines/quotes", 'a\nb\t"c"\\d'),
    ]
    bases = {k: tempfile.mkdtemp(prefix=f"bnd_{k}_") for k in ("sqlite", "silica")}
    bes = {k: make(k, bases[k])[0] for k in bases}
    rows = []
    for label, content in cases:
        key = hashlib.sha256(("bnd:" + label).encode()).hexdigest()
        got = {}
        for k, be in bes.items():
            be.put_chunk_raw(key, content, '{"t":1}', "b", "active", 1.0)
            r = be.get_chunk_raw(key) or {}
            got[k] = (r.get("content"), r.get("status"), r.get("author"))
        rows.append((label, got["sqlite"] == got["silica"], got["sqlite"], got["silica"]))
    # idempotent re-put (dedup) + missing key + delete
    extra = []
    for k, be in bes.items():
        kk = hashlib.sha256(b"dup").hexdigest()
        be.put_chunk_raw(kk, "v", "{}", "b", "active", 1.0)
        be.put_chunk_raw(kk, "v", "{}", "b", "active", 1.0)  # re-put same key
        dup_ok = (be.get_chunk_raw(kk) or {}).get("content") == "v"
        missing_ok = be.get_chunk_raw("f" * 64) is None
        be.drop_chunk(kk)
        del_ok = be.get_chunk_raw(kk) is None
        extra.append((k, dup_ok, missing_ok, del_ok))
    for k, be in bes.items():
        try: be.close()
        except Exception: pass
    for b in bases.values():
        shutil.rmtree(b, ignore_errors=True)
    return rows, extra


def main():
    print(f"Silica vs SQLite — operational metrics (N={N} atoms, sync=FULL)\n")
    sq = bench("sqlite")
    si = bench("silica")

    def row(label, key, fmt="{:.2f}", unit=""):
        a, b = sq[key], si[key]
        af = "n/a" if a is None else fmt.format(a)
        bf = "n/a" if b is None else fmt.format(b)
        print(f"  {label:26} {af:>12}{unit}   {bf:>12}{unit}")

    print(f"  {'metric':26} {'sqlite':>12}   {'silica':>12}")
    print("  " + "-" * 56)
    row("write latency p50 (ms)", "write_p50")
    row("write latency p99 (ms)", "write_p99")
    row("write throughput (w/s)", "throughput_ws", "{:.0f}")
    row("read latency p50 (ms)", "read_p50", "{:.3f}")
    row("read latency p99 (ms)", "read_p99", "{:.3f}")
    row("WAL after write (MB)", "wal_write_mb")
    row("WAL after checkpoint (MB)", "wal_ckpt_mb")
    row("checkpoint time (ms)", "ckpt_ms")
    row("RSS delta / load (MB)", "rss_delta_mb")
    row("cache hit-rate (%)", "cache_hit_pct", "{:.1f}")

    print("\n  Boundary-condition parity (SQLite = oracle):")
    rows, extra = boundary_parity()
    allok = True
    for label, ok, a, b in rows:
        allok &= ok
        print(f"    {label:20} parity={'OK' if ok else 'MISMATCH'}" + ("" if ok else f"  sqlite={a} silica={b}"))
    for k, dup, miss, dele in extra:
        allok &= dup and miss and dele
        print(f"    {k:20} dedup={'OK' if dup else 'X'} missing→None={'OK' if miss else 'X'} delete→None={'OK' if dele else 'X'}")

    print("\n  " + ("ALL boundary parity OK" if allok else "!! BOUNDARY MISMATCH — investigate"))
    sys.exit(0 if allok else 1)


if __name__ == "__main__":
    main()
