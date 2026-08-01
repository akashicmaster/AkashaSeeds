#!/usr/bin/env python3
"""
Silica engine eval (Slice A) — the pseudo-ISA store's mechanism guarantees.

Proves the primitive engine (docs/for-llm/silica-store-pseudo-isa-spec.md) BEFORE
the 59-method AkashaBackend boundary is layered on (Slice B):

  E1 persist      — put/delete then reopen: the index rebuilds from the WAL (replay).
  E2 crash-stop   — a torn WAL tail is dropped on replay; committed data survives
                    (the "only the in-flight write is lost" guarantee).
  E3 rollback     — an aborted txn leaves NO trace, even across a reopen.
  E4 cross-bank   — a two-phase txn whose coordinator COMMIT is lost reverts in
                    BOTH banks (all-or-nothing atomicity across banks).
  E5 bank-parallel— concurrent writes to different banks don't block/deadlock and
                    all land; same-bank writes serialize correctly (no lost writes).
  E6 scan+ckpt    — single-route scan is correct; checkpoint shrinks the WAL and
                    the data still survives a reopen.

Run:  python test/silica_store_eval.py
"""
import os
import sys
import shutil
import struct
import tempfile
import threading

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from lib.akasha.backends.silica import SilicaStore, Wal, _HDR

_results = []


def record(name, ok, detail=""):
    _results.append((name, ok, detail))
    print(f"  {'OK  ' if ok else '!! FAIL'}  {name:14} {detail}")


def reopen(d, **kw):
    return SilicaStore(d, **kw)


def main():
    print("\n  silica engine eval — banked pseudo-ISA store (crash-stop / rollback / bank-parallel)\n")
    work = tempfile.mkdtemp(prefix="silica_")
    try:
        # ── E1 persist ────────────────────────────────────────────────────────
        d1 = os.path.join(work, "e1")
        s = reopen(d1, banks=8)
        with s.begin() as t:
            t.put(b"user:1", b"name", b"Henri")
            t.put(b"user:1", b"city", b"Tokyo")
            t.put(b"user:2", b"name", b"Alice")
        with s.begin() as t:
            t.delete(b"user:1", b"city")
        s.close()
        s = reopen(d1, banks=8)   # rebuild purely from WAL
        e1 = (s.get(b"user:1", b"name") == b"Henri"
              and s.get(b"user:1", b"city") is None       # deleted
              and s.get(b"user:2", b"name") == b"Alice")
        record("E1 persist", e1, f"replay rebuilt index; stats={s.stats()['routes_per_bank'][:4]}…")
        s.close()

        # ── E2 crash-stop (torn tail) ──────────────────────────────────────────
        d2 = os.path.join(work, "e2")
        s = reopen(d2, banks=4)
        with s.begin() as t:
            t.put(b"k", b"a", b"committed")
        s.close()
        # Simulate a power-cut mid-write: append a half-written frame to the bank
        # that owns route b"k".
        bank_id = SilicaStore(d2, banks=4).bank_id_of(b"k")
        walp = os.path.join(d2, f"bank-{bank_id:03d}.wal")
        with open(walp, "ab") as f:
            f.write(_HDR.pack(9999, 0xDEADBEEF))   # claims 9999 bytes, writes none
            f.write(b"\x01\x02\x03")               # + a few stray bytes
        s = reopen(d2, banks=4)
        e2 = s.get(b"k", b"a") == b"committed"     # committed survived; torn tail ignored
        record("E2 crash-stop", e2, "torn WAL tail dropped on replay; committed record intact")
        s.close()

        # ── E3 rollback ─────────────────────────────────────────────────────────
        d3 = os.path.join(work, "e3")
        s = reopen(d3, banks=4)
        with s.begin() as t:
            t.put(b"acct", b"bal", b"100")
        t = s.begin()
        t.put(b"acct", b"bal", b"999")
        t.put(b"acct", b"new", b"x")
        assert t.get(b"acct", b"bal") == b"999"    # read-your-writes inside the txn
        t.abort()
        e3_live = (s.get(b"acct", b"bal") == b"100" and s.get(b"acct", b"new") is None)
        s.close()
        s = reopen(d3, banks=4)                     # abort left nothing on disk either
        e3 = e3_live and s.get(b"acct", b"bal") == b"100" and s.get(b"acct", b"new") is None
        record("E3 rollback", e3, "abort leaves no trace in RAM or on disk (reopen clean)")
        s.close()

        # ── E4 cross-bank atomicity ─────────────────────────────────────────────
        d4 = os.path.join(work, "e4")
        s = reopen(d4, banks=8)
        # Find two routes on different banks so their txn is two-phase.
        ra, rb = None, None
        for i in range(1000):
            r = f"r{i}".encode()
            bid = s.bank_id_of(r)
            if ra is None:
                ra, ba = r, bid
            elif bid != ba:
                rb = r
                break
        with s.begin() as t:                         # single-bank baseline (survives)
            t.put(ra, b"s", b"solo")
        with s.begin() as t:                         # cross-bank txn (needs coordinator)
            t.put(ra, b"x", b"1")
            t.put(rb, b"y", b"2")
        s.close()
        # Simulate the coordinator COMMIT being lost (power-cut after prepares, before
        # the atomic point): truncate the coordinator log.
        open(os.path.join(d4, "coord.wal"), "wb").close()
        s = reopen(d4, banks=8)
        e4 = (s.get(ra, b"s") == b"solo"             # single-bank txn unaffected
              and s.get(ra, b"x") is None            # cross-bank txn reverted…
              and s.get(rb, b"y") is None)           # …in BOTH banks (all-or-nothing)
        record("E4 cross-bank", e4, "prepared-but-not-coord-committed txn reverts in both banks")
        s.close()

        # ── E5 bank parallelism ─────────────────────────────────────────────────
        d5 = os.path.join(work, "e5")
        s = reopen(d5, banks=8)
        N = 400
        def writer(tid):
            for i in range(N):
                r = f"t{tid}:{i}".encode()
                with s.begin() as t:
                    t.put(r, b"v", str(i).encode())
        threads = [threading.Thread(target=writer, args=(k,)) for k in range(4)]
        for th in threads: th.start()
        for th in threads: th.join()
        got = all(s.get(f"t{k}:{i}".encode(), b"v") == str(i).encode()
                  for k in range(4) for i in range(N))
        touched_banks = sum(1 for c in s.stats()["routes_per_bank"] if c > 0)
        e5 = got and touched_banks >= 2              # concurrent writes spread & all landed
        record("E5 bank-parallel", e5,
               f"4 threads × {N} writes, all present; banks touched={touched_banks}/8")
        s.close()

        # ── E6 scan + checkpoint ────────────────────────────────────────────────
        d6 = os.path.join(work, "e6")
        s = reopen(d6, banks=4)
        for i in range(50):
            with s.begin() as t:
                t.put(b"set:fruit", f"m{i}".encode(), b"1")
        members_before = dict(s.scan(b"set:fruit"))
        bank_id = s.bank_id_of(b"set:fruit")
        walp = os.path.join(d6, f"bank-{bank_id:03d}.wal")
        size_before = os.path.getsize(walp)
        s.checkpoint()                                # LCKPT — fold + truncate
        size_after = os.path.getsize(walp)
        s.close()
        s = reopen(d6, banks=4)
        members_after = dict(s.scan(b"set:fruit"))
        e6 = (len(members_before) == 50 and members_after == members_before
              and size_after < size_before)          # 50 append records → 1 snapshot
        record("E6 scan+ckpt", e6,
               f"scan=50; WAL {size_before}→{size_after}B after checkpoint; survived reopen")
        s.close()

        print()
        passed = sum(1 for _, ok, _ in _results if ok)
        total = len(_results)
        print(f"  {passed}/{total} phases passed"
              + (f", {total - passed} FAILED" if passed < total else ""))
        if passed < total:
            print("\nRESULT: FAIL — the Silica engine's mechanism guarantees regressed.")
            return 1
        print("\nRESULT: PASS — banked hash keyspace + custom WAL give crash-stop (last-write-only), "
              "clean rollback, cross-bank all-or-nothing, bank-parallel writes, and explicit checkpoint.")
        return 0
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
