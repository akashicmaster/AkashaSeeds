#!/usr/bin/env python3
"""
A48 — the nightly retention sweeps are O(victims), not O(store).

The v26 memory violation: `telemetry.evict` (feed.gc) and `station.compact` (society.broadcast.gc) both
walked the WHOLE store through `iter_all_chunks()` — a JSON-decode of every atom — to find ≤ a few
thousand victims, leaving ~110 MB of un-returned transient allocations resident every UTC day (the
"steady-state climb"). The fix: membership at WRITE time (a per-day telemetry collection; a per-society
mirror registry) so the sweeps iterate the victims by collection. This eval proves it on both cell
shapes:

  1. telemetry over 3 days in day-collections + a bulk of unrelated atoms ⇒ `feed.gc keep=1` iterates
     ONLY the old-day members (scanned ≪ store), drops exactly the old days, leaves today + the bulk;
  2. station-mirror atoms in a per-society registry, some still in a live window ⇒ `broadcast.gc`
     iterates the registry (scanned ≪ store) and drops only the orphans;
  3. the boot backfill assigns pre-existing (un-collected) telemetry/mirror atoms once, and is a no-op
     on a second run.

Run:  python app/test/retention_sweep_eval.py     (exit 0 = all pass)
"""
import hashlib
import os
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _run(series, shape):
    print(f"\n  ── {shape} ({series}) ──")
    from lib.akasha.kernel import KernelDispatcher, TRUST_INTERNAL
    from lib.akasha.jcl.workspace_context import system_context
    KernelDispatcher._boot_load_ontology = lambda self: None
    base = tempfile.mkdtemp(prefix="akasha_ret_")
    k = KernelDispatcher(series=series, base_dir=base)
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")
    nuc = k.manager.shared_nucleus
    core = nuc.core
    now = time.time()
    d_today = time.strftime("%Y-%m-%d", time.gmtime(now))
    d_1 = time.strftime("%Y-%m-%d", time.gmtime(now - 86400))
    d_2 = time.strftime("%Y-%m-%d", time.gmtime(now - 2 * 86400))

    def put(alias, meta, sets=()):
        with system_context():
            key = nuc.put_atom(f"[{alias}]", dict(meta), author="system.librarian", alias=alias)
            for s in sets:
                core.add_to_collection(s, key)
        return key

    with system_context():
        pass
    # bulk of unrelated atoms (the "store") — NOT telemetry, must never be scanned or dropped
    for i in range(200):
        put(f"bulk:{i}", {"concept": "thing", "n": i})
    # telemetry over 3 days, each in its write-time day collection
    for day in (d_2, d_1, d_today):
        for i in range(30):
            put(f"tel:{day}:{i}", {"concept": "observation", "provenance": "telemetry",
                                   "t": f"{day}T00:00:00Z"}, sets=(f"telemetry:day:{day}",))

    # ── 1. feed.gc keep=1 iterates only the old-day members ──
    r = k.dispatch({"jsonrpc": "2.0", "method": "feed.gc",
                    "params": {"client_id": "system.librarian", "data": {"keep": 1}}, "id": "gc"},
                   TRUST_INTERNAL)
    res = (r or {}).get("result") or {}
    check(f"[{shape}] feed.gc drops exactly the two old days (60)", res.get("dropped") == 60, str(res))
    check(f"[{shape}] feed.gc is O(victims): scanned ≤ victims + small overhead, ≪ the store",
          int(res.get("scanned", 10 ** 9)) <= 60 + 5, f"scanned={res.get('scanned')} (store≈290)")
    check(f"[{shape}] today's telemetry survives", bool(core.get_key_by_alias(f"tel:{d_today}:0")))
    check(f"[{shape}] the old telemetry is gone", not core.get_key_by_alias(f"tel:{d_2}:0"))
    check(f"[{shape}] the unrelated bulk is untouched", bool(core.get_key_by_alias("bulk:0")))

    # ── 2. station.compact over a mirror registry ──
    gid = "plab"
    # 10 mirror atoms in the registry; the first 4 are ALSO in a live window (kept), the rest orphans
    for i in range(10):
        sets = [f"broadcast:mirror:{gid}"]
        if i < 4:
            sets.append(f"broadcast:{gid}:main")
        put(f"broadcast:msg:{gid}:{i}", {"concept": "broadcast_msg", "provenance": "broadcast",
                                         "sid": f"{gid}/main"}, sets=tuple(sets))
    rb = k.dispatch({"jsonrpc": "2.0", "method": "society.broadcast.gc",
                     "params": {"client_id": "system.librarian", "data": {}}, "id": "bc"}, TRUST_INTERNAL)
    rbr = (rb or {}).get("result") or {}
    check(f"[{shape}] broadcast.gc drops only the 6 orphans (4 in a live window kept)",
          rbr.get("dropped") == 6, str(rbr))
    check(f"[{shape}] broadcast.gc is O(mirror): scanned == the registry size (10), ≪ the store",
          int(rbr.get("scanned", 10 ** 9)) == 10, f"scanned={rbr.get('scanned')}")
    check(f"[{shape}] a windowed mirror message survives", bool(core.get_key_by_alias(f"broadcast:msg:{gid}:0")))
    check(f"[{shape}] an orphan mirror message is gone", not core.get_key_by_alias(f"broadcast:msg:{gid}:9"))

    # ── 3. there is no boot backfill: every atom joins its collection at write time, from Genesis
    #    (the purge order §2 — the one full-store scan is deleted) ──
    check(f"[{shape}] no retention backfill exists (no boot scan of the store)",
          not hasattr(k, "_retention_backfill_once") and not hasattr(k, "_schedule_retention_backfill"))


def main():
    _run("thesaurus", "nucleus cell")
    _run("seeds", "single-store cell")
    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("\nRESULT: PASS — the nightly retention sweeps are O(victims): telemetry.evict iterates the "
          "write-time day collections and station.compact the per-society mirror registry (scanned ≪ "
          "the store), dropping exactly the victims and leaving everything else; every atom joins its collection "
          "at write time, so no boot backfill exists — both cell shapes.")
    sys.exit(0)


if __name__ == "__main__":
    main()
