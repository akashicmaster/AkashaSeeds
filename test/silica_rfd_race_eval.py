#!/usr/bin/env python3
"""
Silica disk-value READ-FD race — the akashickitchen.net boot-crash root cause.

Live crash (logs.zip, 2026-07-31 09:01, thesaurus08n on Python 3.14), reconstructed from the
daemon traceback:

    [Kernel] Ontology boot load failed (non-fatal): [Errno 9] Bad file descriptor
      kernel.py _boot_load_ontology → _load_ak_pack
      composite.py get_aliases_by_pattern → silica_backend.py get_aliases_by_pattern
      silica.py scan → _entry_bytes → pread:  os.pread(self._rfd, length, off)
    OSError: [Errno 9] Bad file descriptor

RSS was FLAT (~1154 MB, not climbing) and no OOM record — so this was NEITHER OOM, NOR numpy
autolearn (gated off on 3.14), NOR the SpaCy weave (regex-floor default). It was a file-descriptor
RACE in the disk-value store: `pread` runs on arbitrary reader threads (a read is not on the
WriteQueue), while `SilicaStore.close()` closes every bank's read fd WITHOUT taking bank.lock
(scan/checkpoint were already mutually exclusive under bank.lock — close was the hole). A reader
mid-`pread` on a fd that close() just shut raises EBADF, which — uncaught in the boot-load thread —
aborts the WHOLE ontology load, leaving atoms whose content chunk was never read (the empty
recipe-body symptom) and a destabilised daemon.

Fix: a `_rfd_lock` makes pread and every fd-close mutually exclusive; pread reopens-and-retries on
EBADF, and a read after close() serves off a short-lived fd. A concurrent close can no longer crash
a reader.

This test hammers exactly that race: many reader threads pread in a tight loop while another thread
repeatedly closes/reopens the store's fds. Pre-fix this raised EBADF within milliseconds; post-fix
every read returns correct bytes.

Run:  python test/silica_rfd_race_eval.py
"""
import os, sys, threading, tempfile, shutil, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
os.environ["AKASHA_SILICA_VALUES"] = "disk"          # the mode the race lives in

from lib.akasha.backends.silica_backend import SilicaBackend

_results = []
def record(name, ok, detail=""):
    _results.append((name, ok, detail))
    print(f"  {'OK  ' if ok else '!! FAIL'}  {name:40} {detail}")


def main():
    print("\n  silica disk-value read-fd race — close() concurrent with pread\n")
    work = tempfile.mkdtemp(prefix="akasha_rfd_")
    db = os.path.join(work, "n.db")
    try:
        be = SilicaBackend(db, is_volatile=False)
        # Seed a set of recipe-sized atoms so preads hit real value offsets on disk.
        N = 40
        bodies = {}
        for i in range(N):
            k = f"rk_{i}"
            body = f"recipe {i}: " + ("smoky mashed eggplant, roast peel mash saute fold cook. " * 30)
            bodies[k] = body
            be.put_chunk_raw(k, body, '{"type":"recipe"}', "admin", "verified", 1000.0 + i)
            be.put_alias(k, f"recipe:r{i}")
        store = be._store

        errors = []
        mismatches = []
        stop = threading.Event()

        def reader(idx):
            keys = list(bodies.keys())
            while not stop.is_set():
                k = keys[idx % len(keys)]
                try:
                    r = be.get_chunk_raw(k)
                    got = (r or {}).get("content", "")
                    if got and got != bodies[k]:
                        mismatches.append((k, len(got)))
                except OSError as exc:                 # the pre-fix failure: EBADF (errno 9)
                    errors.append(f"{type(exc).__name__}: errno={getattr(exc,'errno',None)} {exc}")
                    return
                except Exception as exc:
                    errors.append(f"{type(exc).__name__}: {exc}")
                    return
                idx += 1

        def fd_churner():
            # Repeatedly close the read fds out from under the readers — the exact thing
            # SilicaStore.close() (guest-wipe / atexit / teardown) does during a live boot.
            while not stop.is_set():
                for bank in store._banks:
                    bank.wal._reopen_rfd()             # close+drop the cached read fd
                time.sleep(0.0005)

        readers = [threading.Thread(target=reader, args=(i,), daemon=True) for i in range(8)]
        churner = threading.Thread(target=fd_churner, daemon=True)
        for t in readers:
            t.start()
        churner.start()
        time.sleep(2.5)                                # 2.5s of concurrent pread × fd-close
        stop.set()
        for t in readers:
            t.join(timeout=2)
        churner.join(timeout=2)

        record("no EBADF / read exception under fd churn", not errors,
               errors[0] if errors else "(0 read errors across 8 threads × 2.5s)")
        record("every read returned correct bytes", not mismatches,
               f"{len(mismatches)} mismatches" if mismatches else "(content intact)")

        # After an explicit close(), a late read must STILL serve off disk (not crash).
        be.close()
        late = None
        try:
            late = be.get_chunk_raw("rk_0")
        except Exception as exc:
            record("read after close() does not crash", False, f"{type(exc).__name__}: {exc}")
        else:
            record("read after close() serves off disk", bool(late and late.get("content")),
                   f"len={len((late or {}).get('content',''))}")
    finally:
        shutil.rmtree(work, ignore_errors=True)

    passed = sum(1 for _, ok, _ in _results if ok); total = len(_results)
    print(f"\n  {passed}/{total} checks passed")
    if passed == total:
        print("\nRESULT: PASS — a concurrent close() can no longer crash a disk-value reader: the "
              "read-fd race that aborted the ontology boot load (EBADF) and left empty recipe "
              "bodies is closed. Reads recover transparently and serve correct bytes.\n")
        return 0
    print("\nRESULT: FAIL — the read-fd race is still present.\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
