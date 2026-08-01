#!/usr/bin/env python3
"""
Silica disk-value (memory-frugal) mode — the fix for "large ontology must fit in RAM".

`AKASHA_SILICA_VALUES=disk` keeps only a (offset,len) location per record in RAM and preads the
value from the WAL on demand (LRU-cached), instead of holding every value resident. The on-disk
WAL format is unchanged, so a store written in one mode reads back in the other and crash-stop
holds. This eval pins:

  D1 round-trip + reopen — writes persist and reopen cleanly in disk mode.
  D2 checkpoint          — LCKPT compacts the WAL and re-derives the (now-shifted) offsets.
  D3 cross-mode          — a store written in RAM mode reads in DISK mode and vice versa.
  D4 memory              — disk mode's resident RAM is materially smaller than RAM mode.

Run:  python test/silica_disk_mode_eval.py     (exit 0 = all pass)
Developer verification test (not a user-facing .ak example).
"""
import os
import sys
import gc
import tempfile
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

from lib.akasha.backends.silica import SilicaStore
from lib.akasha.backends.silica_backend import SilicaBackend

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _put(s, route, sub, val):
    with s.begin() as t:
        t.put(route.encode(), sub.encode(), val.encode())


def _del(s, route, sub):
    with s.begin() as t:
        t.delete(route.encode(), sub.encode())


def _get(s, route, sub):
    v = s.get(route.encode(), sub.encode())
    return v.decode() if v is not None else None


def _rss_mb():
    try:
        for line in open("/proc/self/status"):
            if line.startswith("VmRSS:"):
                return int(line.split()[1]) / 1024.0
    except Exception:
        pass
    import resource
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


def main():
    # ── D1 round-trip + reopen ──
    d = tempfile.mkdtemp()
    s = SilicaStore(d, value_store="disk")
    for i in range(100):
        _put(s, "@atoms", f"k{i}", f"value-{i}-" + "z" * 40)
    _put(s, "@V\x00system", "admin_name", "henri")
    _del(s, "@atoms", "k5")
    ok = (_get(s, "@atoms", "k42") == "value-42-" + "z" * 40
          and _get(s, "@V\x00system", "admin_name") == "henri"
          and _get(s, "@atoms", "k5") is None)
    check("D1 disk round-trip (put/get/delete)", ok)
    s.close()
    s2 = SilicaStore(d, value_store="disk")
    check("D1 reopen persists (disk replay)",
          _get(s2, "@atoms", "k42") == "value-42-" + "z" * 40
          and _get(s2, "@V\x00system", "admin_name") == "henri"
          and _get(s2, "@atoms", "k5") is None)

    # ── D2 checkpoint re-derives offsets ──
    s2.checkpoint()
    check("D2 checkpoint keeps values (offsets recomputed)",
          _get(s2, "@atoms", "k42") == "value-42-" + "z" * 40
          and _get(s2, "@atoms", "k5") is None
          and _get(s2, "@V\x00system", "admin_name") == "henri")
    s2.close()
    check("D2 reopen after checkpoint",
          _get(SilicaStore(d, value_store="disk"), "@atoms", "k99") == "value-99-" + "z" * 40)
    shutil.rmtree(d, ignore_errors=True)

    # ── D3 cross-mode (same on-disk format) ──
    d1 = tempfile.mkdtemp()
    a = SilicaStore(d1, value_store="ram")
    _put(a, "@x", "foo", "bar-ram"); a.close()
    b = SilicaStore(d1, value_store="disk")
    check("D3 write RAM → read DISK", _get(b, "@x", "foo") == "bar-ram"); b.close()
    shutil.rmtree(d1, ignore_errors=True)
    d2 = tempfile.mkdtemp()
    c = SilicaStore(d2, value_store="disk")
    _put(c, "@x", "foo", "bar-disk"); c.close()
    e = SilicaStore(d2, value_store="ram")
    check("D3 write DISK → read RAM", _get(e, "@x", "foo") == "bar-disk"); e.close()
    shutil.rmtree(d2, ignore_errors=True)

    # ── D4 memory: disk < ram ──
    N = 15000
    meta = '{"type":"note","semantic_vector":[' + ",".join("0.123456" for _ in range(64)) + ']}'
    body = "atom body of moderate length " * 4

    def build(mode):
        os.environ["AKASHA_SILICA_VALUES"] = mode
        base = tempfile.mkdtemp()
        gc.collect(); r0 = _rss_mb()
        be = SilicaBackend(os.path.join(base, "nuc"), sync_mode="NORMAL")
        for i in range(N):
            be.put_chunk_raw("%064x" % i, body + str(i), meta, "a", "active", 1.0 + i)
        gc.collect(); resident = _rss_mb() - r0
        got = (be.get_chunk_raw("%064x" % 7777) or {}).get("content", "").endswith("7777")
        be.close(); shutil.rmtree(base, ignore_errors=True)
        return resident, got

    ram_mb, ok_r = build("ram")
    disk_mb, ok_d = build("disk")
    check("D4 disk reads correct after N writes", ok_r and ok_d)
    check("D4 disk resident RAM < ram resident RAM",
          disk_mb < ram_mb, f"ram={ram_mb:.1f}MB disk={disk_mb:.1f}MB "
                             f"({100*(ram_mb-disk_mb)/ram_mb:.0f}% less)")

    print()
    if _fails:
        print(f"FAIL — {len(_fails)}: {', '.join(_fails)}")
        sys.exit(1)
    print("PASS — Silica disk-value mode: durable, cross-mode compatible, and RAM-frugal.")
    sys.exit(0)


if __name__ == "__main__":
    main()
