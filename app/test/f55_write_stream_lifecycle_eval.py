#!/usr/bin/env python3
"""
f55_write_stream_lifecycle_eval.py — the F55 write-stream lifecycle merge gate (2026-09).

Two unbounded write streams (`sys.census` on the live nucleus) were memory-discipline R5 leaks:
`provenance=telemetry` (131k, soft-evicted = atom kept) and `provenance=broadcast` (76k, mirror
atoms trimmed from the set but never dropped). This pins their bounding jobs, per
docs/for-llm/*writestreamlifecycle.md and the maintainer's rulings (telemetry demo → keep today,
delete earlier; station → overwrite/bound the aired output).

  TEL-GC   feed.gc HARD-drops (full C2: set memberships + atom + links) every telemetry atom whose
           UTC day is older than the window (keep=today). A second pass drops 0 (idempotent). The
           dropped atoms are GONE from the store (get_chunk_raw None), not merely un-set.
  TEL-CAD  op_due applies the demo cadence FLOOR (AKASHA_FEED_MIN_INTERVAL, default 3600): a 60 s
           feed is not due 120 s after its last pull; with the floor disabled it is.
  STN-TRIM _trim_broadcast HARD-drops the overflow beyond the rolling window (not soft) — the set
           stays == KEEP and the evicted mirror atoms are gone from the store.
  STN-GC   society.broadcast.gc purges ORPHANED mirror atoms (broadcast_msg not in any live window
           set) — the 76k backlog — while KEEPING atoms still in a live window; second pass drops 0.

Run:  python app/test/f55_write_stream_lifecycle_eval.py     (exit 0 = all pass)
"""
import hashlib
import json
import os
import sys
import tempfile
import time as _time
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT); sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []

NOW = int(_time.time())


def _iso(epoch):
    return datetime.fromtimestamp(epoch, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def main():
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_f55_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def d(m, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": m,
                        "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
        return r.get("result") if "result" in r else {"__error__": r.get("error")}

    nuc = k.manager.shared_nucleus
    core = nuc.core

    # ════════════════════════════ TELEMETRY (F55 §1) ════════════════════════════
    d("feed.register", {"id": "gcf", "kind": "kind:test:x", "interval": 60})
    # three observations on distinct subjects, dated today / yesterday / 3 days ago
    d("feed.ingest", {"id": "gcf", "records": [
        {"raw_id": "s_today", "lat": 10.0, "lon": 10.0, "t": _iso(NOW)},
        {"raw_id": "s_yest",  "lat": 11.0, "lon": 11.0, "t": _iso(NOW - 86400)},
        {"raw_id": "s_old",   "lat": 12.0, "lon": 12.0, "t": _iso(NOW - 3 * 86400)},
    ]})
    obs_before = list(core.get_collection_members("feed:gcf:obs") or [])
    by_day = {}
    for ok_ in obs_before:
        t = (core.get_chunk_raw(ok_) or {}).get("meta") or "{}"
        try:
            day = json.loads(t).get("t", "")[:10]
        except Exception:
            day = ""
        by_day[day] = ok_
    today_day = _iso(NOW)[:10]
    today_key = by_day.get(today_day)
    old_keys = [v for d_, v in by_day.items() if d_ and d_ < today_day]
    check("TEL setup: 3 telemetry observations across 3 distinct days minted",
          len(obs_before) == 3 and today_key and len(old_keys) == 2,
          "obs=%d days=%s" % (len(obs_before), sorted(by_day)))

    gc1 = d("feed.gc", {"keep": 1})
    obs_after = list(core.get_collection_members("feed:gcf:obs") or [])
    old_gone = all(core.get_chunk_raw(kk) is None for kk in old_keys)
    today_here = core.get_chunk_raw(today_key) is not None
    # RETIRED 2026-09-20: this used to require `dropped == 2`, counting observations only. A48.1
    # made the sweep iterate the write-time DAY collection (O(victims), never O(store)), and a day
    # carries BOTH atoms an ingest mints — the telemetry_subject and the observation — so an older
    # day of one record costs 2. Dropping the day's subject with its observations is the intent
    # (no orphan subject is left resident). The assertion is now the day's whole membership.
    check("TEL-GC: feed.gc keep=today drops both older DAYS whole (subject + observation), keeps today's",
          gc1.get("dropped") == 4 and obs_after == [today_key],
          "dropped=%s after=%d" % (gc1.get("dropped"), len(obs_after)))
    check("TEL-GC: dropped telemetry atoms are GONE from the store (full C2, not soft-evict)",
          old_gone and today_here, "old_gone=%s today=%s" % (old_gone, today_here))

    # TEL-GC-SUBJ — a subject that is STILL REPORTING survives the sweep of its oldest day.
    # `feed.ingest` re-mints the same content-addressed subject atom every time it reports, so a
    # long-lived subject is a member of every day it appeared on. The sweep used to drop whatever
    # it found in an expiring day, which killed the subject and left today's observation pointing
    # at a dead atom. (Filed from the layout seed's §7.1 diagnosis; fixed in seed A slice 2.)
    d("feed.register", {"id": "livef", "kind": "kind:test:x", "interval": 60})
    d("feed.ingest", {"id": "livef", "records": [
        {"raw_id": "station1", "lat": 1.0, "lon": 1.0, "t": _iso(NOW - 3 * 86400)},
        {"raw_id": "station1", "lat": 1.0, "lon": 1.0, "t": _iso(NOW)},
    ]})
    sub_k = core.get_key_by_alias("entity:livef:station1")
    gcs = d("feed.gc", {"keep": 1})
    live_obs = [o for o in (core.get_collection_members("feed:livef:obs") or [])]
    still = core.get_chunk_raw(sub_k) is not None
    bound = []
    for o in live_obs:
        m = json.loads((core.get_chunk_raw(o) or {}).get("meta") or "{}")
        bound.append(core.get_chunk_raw(m.get("subject")) is not None)
    check("TEL-GC: a subject still reporting TODAY survives the sweep of its oldest day",
          still, "subject alive=%s dropped=%s" % (still, gcs.get("dropped")))
    check("TEL-GC: …so today's surviving observation still resolves its subject (no dangling obs:of)",
          bool(live_obs) and all(bound), "obs=%d bound=%s" % (len(live_obs), bound))
    check("TEL-GC: the sweep says how many it spared (`still_reporting=`), not only what it dropped",
          int(gcs.get("still_reporting", -1)) >= 1, str(gcs))

    gc2 = d("feed.gc", {"keep": 1})
    check("TEL-GC: a second pass is idempotent (drops 0)", gc2.get("dropped") == 0, str(gc2.get("dropped")))

    # cadence floor: 120 s after the last pull, a 60 s feed is NOT due under the demo floor (3600),
    # but IS due with the floor disabled.
    at120 = _iso(NOW + 120)
    os.environ.pop("AKASHA_FEED_MIN_INTERVAL", None)                 # default floor = 3600
    due_floored = d("feed.due", {"at": at120})
    ids_floored = {x["id"] for x in due_floored.get("due", [])}
    os.environ["AKASHA_FEED_MIN_INTERVAL"] = "0"                     # honor each feed's interval
    due_raw = d("feed.due", {"at": at120})
    ids_raw = {x["id"] for x in due_raw.get("due", [])}
    os.environ.pop("AKASHA_FEED_MIN_INTERVAL", None)
    check("TEL-CAD: the demo cadence floor holds back a 60 s feed 120 s after its pull; floor=0 releases it",
          "gcf" not in ids_floored and "gcf" in ids_raw,
          "floored=%s raw=%s" % (ids_floored, ids_raw))

    # ════════════════════════════ STATION (F55 §2) ════════════════════════════
    from lib.akasha.concepts.society import SocietyConcept
    sc = SocietyConcept(k.manager.get_session("admin"))
    snuc = sc._mirror_writer()
    score = snuc.core
    KEEP = sc._BROADCAST_KEEP

    # RETIRED 2026-09-20 (the harness, not the assertion): this used to mint mirror atoms with NO
    # `broadcast:mirror:<gid>` membership and expect the sweep to find them. A48.1 deliberately
    # stopped walking the store — the sweep is O(mirror), iterating the per-society mirror registry
    # the mirror writer itself fills (society.py `_nuc_put(..., sets=(bset, "broadcast:mirror:<gid>"))`),
    # because an O(store) nightly sweep left ~110 MB resident every night (F33/F50 R1). An atom that
    # is in no registry was never written by the mirror, so it is not the 76k class. The harness now
    # registers them the way the writer does; the assertion below is unchanged.
    def mk_msg(alias, created, gid, in_set=None):
        key = hashlib.sha256(alias.encode()).hexdigest()
        meta = {"concept": "broadcast_msg", "provenance": "broadcast", "created_at": created}
        score.put_chunk_raw(key, alias, json.dumps(meta), "admin", "verified", created)
        try:
            score.put_chunk_access(key, ["scope:sys:universal"])
        except Exception:
            pass
        score.put_alias(key, alias)
        score.add_to_collection("broadcast:mirror:%s" % gid, key)    # the mirror registry the writer fills
        if in_set:
            score.add_to_collection(in_set, key)
        return key

    # STN-GC — orphans (not in any live window) vs live (in a broadcast:<gid>:<space> window)
    live_set = "broadcast:g1:main"
    orphans = [mk_msg("broadcast:msg:orph%02d" % i, NOW - 100000 + i, "g1") for i in range(5)]
    lives = [mk_msg("broadcast:msg:live%02d" % i, NOW - 10 + i, "g1", in_set=live_set) for i in range(3)]
    bg1 = d("society.broadcast.gc", {})
    orph_gone = all(score.get_chunk_raw(x) is None for x in orphans)
    live_here = all(score.get_chunk_raw(x) is not None for x in lives)
    check("STN-GC: broadcast.gc drops orphaned mirror atoms (the 76k class) and KEEPS live-window atoms",
          bg1.get("dropped") == 5 and orph_gone and live_here,
          "dropped=%s orph_gone=%s live_here=%s" % (bg1.get("dropped"), orph_gone, live_here))
    bg2 = d("society.broadcast.gc", {})
    check("STN-GC: a second pass is idempotent (drops 0)", bg2.get("dropped") == 0, str(bg2.get("dropped")))

    # STN-TRIM — _trim_broadcast HARD-drops the overflow beyond the rolling window
    trim_set = "broadcast:g2:main"
    tkeys = [mk_msg("broadcast:msg:t%04d" % i, NOW - (KEEP + 4) + i, "g2", in_set=trim_set)
             for i in range(KEEP + 4)]
    sc._trim_broadcast(snuc, trim_set)
    remaining = list(score.get_collection_members(trim_set) or [])
    oldest4_gone = all(score.get_chunk_raw(x) is None for x in tkeys[:4])
    newest_here = score.get_chunk_raw(tkeys[-1]) is not None
    check("STN-TRIM: _trim_broadcast keeps the set at the rolling window AND drops the overflow atoms",
          len(remaining) == KEEP and oldest4_gone and newest_here,
          "remaining=%d KEEP=%d oldest_gone=%s" % (len(remaining), KEEP, oldest4_gone))

    print()
    if _fails:
        print("FAILED (%d): %s" % (len(_fails), "; ".join(_fails))); sys.exit(1)
    print("ALL PASS — F55 write-stream lifecycle: telemetry is HARD-evicted to keep=today (full C2, "
          "idempotent) and its capture is cadence-floored for demo; the station mirror is HARD-trimmed "
          "to its rolling window and its orphan backlog is purged — both permanent write streams now "
          "ship their bounding job (memory-discipline R5).")
    sys.exit(0)


if __name__ == "__main__":
    main()
