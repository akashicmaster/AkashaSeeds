#!/usr/bin/env python3
"""
F39-P1b / F30-2 — the feed due-scan must be O(feeds), never O(observations).

Nine `feed-poll tick slow` convictions in one night (due_scan 316.5 s … 38.5 s, list_jobs=0.0 s in
every line) traced to op_due/op_feeds deriving last_pull as max(t) over EVERY observation of every
feed — an O(N_obs) point-get storm on each scheduler tick, behind the "no reply within 60 s"
incidents. The fix persists per-feed last_pull as O(1) mutable meta (set_meta side-store) on ingest,
so the due check is a dict lookup; a legacy feed with no marker self-heals on first access.

This asserts, via the store's access-degree probe (F33 §5), that op_due's store round-trips do NOT
grow with the observation count.

Run:  python app/test/feed_due_scan_eval.py   (exit 0 = all pass)
"""
import hashlib
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
os.environ["AKASHA_BACKEND"] = "silica"

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def main():
    from lib.akasha.kernel import KernelDispatcher
    from api.gateway import AkashaGateway
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="feeddue_"))
    gw = AkashaGateway(kernel_client=k)

    def D(m, d):
        r = gw.dispatch({"jsonrpc": "2.0", "method": m,
                         "params": {"session_token": "admin", "data": d}, "id": "c"}, "local")
        return r.get("result") or r.get("error") or {}

    gw.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                 "params": {"session_token": "admin", "data": {"user_name": "admin",
                            "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")
    core = k.manager.shared_nucleus.core
    if not hasattr(core, "probe_read"):
        check("probe available (silica)", False, "backend has no access-degree probe")
        print("SKIP — needs the silica backend"); sys.exit(0)

    D("feed.register", {"id": "quakes", "kind": "kind:geo:quake", "interval": 300})

    def ingest(n_start, n):
        # DISTINCT (raw_id, bucket) so observations do NOT collapse — each is its own atom.
        recs = [{"lat": 35 + 0.001 * i, "lon": 139 + 0.001 * i, "raw_id": "q%d" % i,
                 "t": "2026-08-28T%02d:%02d:00Z" % ((i // 60) % 24, i % 60), "mag": 3.0,
                 "title": "quake %d" % i} for i in range(n_start, n_start + n)]
        return D("feed.ingest", {"id": "quakes", "records": recs}).get("observations_new", 0)

    # small feed → measure op_due round-trips
    ingest(0, 20)
    core.probe_reset()
    D("feed.due", {})
    small = core.probe_read()

    # 10× the observations → op_due round-trips must NOT scale with it
    ingest(1000, 200)
    feeds = D("feed.feeds", {})
    # the built-in feeds are registered at boot now (the `feed_defaults` schedule), so pick OUR feed by id
    _q = ([f for f in (feeds.get("feeds") or []) if str(f.get("id", "")).replace("feed:", "") == "quakes"]
          or [{}])[0]
    obs_count = _q.get("observations", 0)
    core.probe_reset()
    D("feed.due", {})
    big = core.probe_read()

    check("last_pull is persisted (O(1) marker present)",
          bool(_q.get("last_pull")), f"last_pull={_q.get('last_pull')}")
    check("op_due does ZERO full scans", big["full_scan"] == 0, str(big))
    check("op_due round-trips are O(feeds), NOT O(observations)",
          big["point_get"] <= small["point_get"] + 3 and big["point_get"] < obs_count,
          f"small={small['point_get']} big={big['point_get']} obs={obs_count}")

    # legacy feed (marker cleared) self-heals: first op_due scans once + persists, next is O(1).
    # The feed atom lives in the shared nucleus — clear the marker there to simulate a pre-upgrade feed.
    import json as _json
    nuc = k.manager.shared_nucleus
    fk = nuc.core.get_key_by_alias("feed:quakes") or nuc.core.get_key_by_alias("quakes")
    if fk:
        row = nuc.core.get_chunk_raw(fk)
        cur = _json.loads(row["meta"]) if row and row.get("meta") else {}
        cur.pop("last_pull", None)
        nuc.core.update_meta(fk, cur)                 # simulate a pre-upgrade feed (no marker)
    core.probe_reset()
    D("feed.due", {})            # heals (scan once, persist)
    core.probe_reset()
    D("feed.due", {})            # now O(1)
    healed = core.probe_read()
    check("legacy feed self-heals → subsequent op_due is O(feeds) again",
          healed["point_get"] <= small["point_get"] + 3 and healed["full_scan"] == 0,
          f"healed={healed}")

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("ALL PASS — feed due/feeds read a persisted O(1) last_pull; the scheduler tick no longer "
          "scans every observation (the 300 s+ due-scan behind the stale-heartbeat incidents is gone).")
    sys.exit(0)


if __name__ == "__main__":
    main()
