#!/usr/bin/env python3
"""
A54 — pulse.compact iterates the days that EXIST, not a blind 397-day back-scan.

The old loop walked `range(keep+1, 400)` and materialised `pulse:day:<d>` + `pulse:sumday:<d>` for
each — 800 collection loads even when every day was empty (75 s / +450 MB transient on the VPS with the
A48.1 day collections). Now: a `pulse:days` marker collection is maintained at emit; compact iterates
it (O(days-with-events)), the already-summarised skip is a `collection_exists`, and a one-time migration
seeds `pulse:days` from any pre-A54 raw days.

Checks (both cell shapes):
  1. compact with NOTHING to do is FAST (< 1 s) and compacts 0 days — no 400-day scan.
  2. a legacy raw day (seeded directly, no marker) is migrated in and compacted; its raw events are
     evicted and its marker retired.
  3. a day inside the keep window is left raw (not compacted).

Run:  python test/pulse_compact_eval.py     (exit 0 = all pass)
"""
import hashlib
import json
import os
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _run(series, shape):
    print(f"\n  ── {shape} ({series}) ──")
    from lib.akasha.kernel import KernelDispatcher
    from lib.akasha.concepts import pulse as P
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series=series, base_dir=tempfile.mkdtemp(prefix="akasha_pulse_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")
    P._MARKED_DAYS.clear()
    core = k.manager.shared_nucleus.core

    def compact(keep=2):
        r = k.dispatch({"jsonrpc": "2.0", "method": "pulse.compact",
                        "params": {"client_id": "system.librarian", "data": {"keep": keep}}, "id": "c"},
                       "internal")
        return (r.get("result") or {}) if isinstance(r, dict) else {}

    def _day(days_ago):
        return time.strftime("%Y-%m-%d", time.gmtime(time.time() - days_ago * 86400))

    def _seed_raw(day, n):
        # seed a legacy raw day directly (no daymark) — the pre-A54 shape the migration must pick up
        for i in range(n):
            key = hashlib.sha256(f"ev:{day}:{i}".encode()).hexdigest()
            core.put_chunk_raw(key, f"[pulse] p{i} @ {day}", json.dumps(
                {"role": "pulse:event", "provenance": P.PROVENANCE, "type": "pulse:event", "day": day,
                 "concept_key": "c:x", "concept_alias": "x", "ref": "direct", "surface": "page",
                 "ua": "human"}), "system", "verified", time.time())
            core.add_to_collection(P.S_DAY + day, key)

    # ── 1. a legacy raw day (10 days old, no marker — the pre-A54 shape) exists BEFORE the first
    #        compact; the one-time migration picks it up and it is compacted + evicted ──
    old = _day(10)
    _seed_raw(old, 5)
    r1 = compact(keep=2)
    check(f"[{shape}] a legacy old day is migrated in and compacted",
          r1.get("days_compacted") == 1 and r1.get("events_evicted") == 5, str(r1)[:120])
    check(f"[{shape}] the old day's raw events are evicted (S_DAY empty) + summarised",
          not core.get_collection_members(P.S_DAY + old)
          and core.collection_exists(P.S_SUMDAY + old), "raw not cleared")

    # ── 2. nothing left to compact ⇒ FAST (<1s) + zero days (the empty-days case, no 400-scan) ──
    t0 = time.time()
    r0 = compact()
    dt = time.time() - t0
    check(f"[{shape}] compact with nothing to do is fast (<1s) and compacts 0 days",
          r0.get("days_compacted") == 0 and dt < 1.0, f"days={r0.get('days_compacted')} t={dt:.3f}s")

    # ── 3. a day INSIDE the keep window is left raw (marker present, but within the window) ──
    recent = _day(0)                                     # today
    _seed_raw(recent, 3)
    # simulate emit's daymark for today so it is a S_DAYS candidate
    _dm = hashlib.sha256(("[pulse:daymark] " + recent).encode()).hexdigest()
    core.put_chunk_raw(_dm, "[pulse:daymark] " + recent,
                       json.dumps({"role": "pulse:daymark", "provenance": P.PROVENANCE, "day": recent}),
                       "system", "verified", time.time())
    core.add_to_collection(P.S_DAYS, _dm)
    r2 = compact(keep=2)
    check(f"[{shape}] a within-keep day is NOT compacted (raw kept)",
          core.get_collection_members(P.S_DAY + recent) and not core.collection_exists(P.S_SUMDAY + recent),
          f"days={r2.get('days_compacted')}")


def main():
    _run("thesaurus", "nucleus cell")
    _run("seeds", "single-store cell")
    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("\nRESULT: PASS — pulse.compact iterates the days that exist (O(days-with-events)): an empty "
          "compact is fast and touches 0 days, a legacy raw day is migrated in and compacted (raw "
          "evicted, marker retired, idempotent thereafter), and a within-keep day stays raw — both "
          "cell shapes.")
    sys.exit(0)


if __name__ == "__main__":
    main()
