#!/usr/bin/env python3
"""
F44 Part B — the public tier: bots off the engine, SEO kept.

A verified crawler is served a materialized snapshot from disk with ZERO cell-daemon RPCs; an
unverified/impostor bot is rate-limited but never trusted; a human keeps the live path. When no fresh
snapshot exists and the render slots are busy, a crawler gets 503+Retry-After (never a soft-404
shell). This eval exercises the pure classification + snapshot-store + accounting helpers directly
(no live daemon, no network): a UA claiming Googlebot is only a `crawler` when its reverse DNS
forward-confirms; the disk snapshot round-trips and expires on TTL; per-class accounting tallies.

Run:  python app/test/public_tier_eval.py   (exit 0 = all pass)
"""
import os
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def main():
    os.environ["AKASHA_SNAPSHOT_DIR"] = tempfile.mkdtemp(prefix="snap_")
    import api.portals.asgi as asgi

    GBOT = ("Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)")
    HUMAN = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
             "(KHTML, like Gecko) Chrome/120 Safari/537.36")
    GENERIC_BOT = "python-requests/2.31.0"

    # ── B1: an injectable resolver simulates forward-confirmed reverse DNS ──
    def good_resolver(kind, arg):
        if kind == "ptr":
            return "crawl-66-249-66-1.googlebot.com"
        if kind == "fwd":
            return ["66.249.66.1"]            # forward-confirms back to the same IP
        return None

    def spoof_resolver(kind, arg):
        # PTR points at googlebot.com but the forward lookup does NOT return the caller IP → impostor.
        if kind == "ptr":
            return "crawl-1-2-3-4.googlebot.com"
        if kind == "fwd":
            return ["66.249.66.1"]            # forward resolves elsewhere, not the caller 9.9.9.9
        return None

    asgi._RDNS_CACHE.clear()
    c1 = asgi._classify_client(GBOT, "66.249.66.1", resolver=good_resolver)
    check("B1 Googlebot UA + forward-confirmed rDNS → crawler(verified)",
          c1["class"] == "crawler" and c1["verified"], str(c1))

    asgi._RDNS_CACHE.clear()
    c2 = asgi._classify_client(GBOT, "9.9.9.9", resolver=spoof_resolver)
    check("B1 Googlebot UA WITHOUT forward-confirm → passerby (impostor, not trusted)",
          c2["class"] == "passerby" and not c2["verified"], str(c2))

    c3 = asgi._classify_client(GENERIC_BOT, "5.5.5.5")
    check("B1 generic automated UA → passerby", c3["class"] == "passerby", str(c3))

    c4 = asgi._classify_client(HUMAN, "5.5.5.5")
    check("B1 browser UA → human (served generously)", c4["class"] == "human", str(c4))

    # upgrade ladder: an IP that PROVED humanity (fired the beacon) is human even with an odd UA
    asgi._HUMAN_IPS.clear()
    asgi._mark_human("7.7.7.7")
    cup = asgi._classify_client(GENERIC_BOT, "7.7.7.7")
    check("ladder: a passerby-UA IP that proved humanity → human",
          cup["class"] == "human" and cup["verified"], str(cup))


    # ── B2: the disk snapshot store round-trips and respects TTL ──
    host, slug = "archives.space", "concept:bird"
    check("B2 read before write → miss", asgi._snapshot_read(host, slug) is None)
    ok = asgi._snapshot_write(host, slug, "<html>bird snapshot</html>")
    check("B2 snapshot_write persists to disk", ok and asgi._snapshot_read(host, slug) is not None)
    got = asgi._snapshot_read(host, slug)
    check("B2 snapshot round-trips the exact HTML", got == "<html>bird snapshot</html>", repr(got))
    # a distinct slug does not collide
    asgi._snapshot_write(host, "concept:fish", "<html>fish</html>")
    check("B2 distinct slugs do not collide",
          asgi._snapshot_read(host, "concept:fish") == "<html>fish</html>"
          and asgi._snapshot_read(host, slug) == "<html>bird snapshot</html>")
    # TTL: a zero-age-tolerance read of an old file is a miss
    p = asgi._snapshot_path(host, slug)
    old = time.time() - 10 * 86400
    os.utime(p, (old, old))
    check("B2 a snapshot older than the 7-day TTL is a miss (regenerate)",
          asgi._snapshot_read(host, slug, ttl=7 * 86400) is None)
    check("B2 the same old snapshot is still served under a longer TTL",
          asgi._snapshot_read(host, slug, ttl=30 * 86400) == "<html>bird snapshot</html>")

    # ── B5: per-class accounting tallies by outcome ──
    asgi._CLASS_STATS.clear()
    asgi._class_note("crawler", "snapshot")
    asgi._class_note("crawler", "snapshot")
    asgi._class_note("crawler", "503")
    asgi._class_note("human", "live")
    snap = asgi._class_stats_snapshot()
    check("B5 per-class accounting tallies outcomes",
          snap.get("crawler", {}).get("snapshot") == 2
          and snap.get("crawler", {}).get("503") == 1
          and snap.get("crawler", {}).get("total") == 3
          and snap.get("human", {}).get("total") == 1, str(snap))

    # ── 2.1: a budget-truncated render is MARKED and never persisted as a snapshot ──
    body_full = asgi._ssr_build_body({"headword": "Bird", "canonical_slug": "concept:bird",
                                      "description": "d", "related": [], "refs": [], "truncated": False})
    body_part = asgi._ssr_build_body({"headword": "Bird", "canonical_slug": "concept:bird",
                                      "description": "d", "related": [], "refs": [], "truncated": True})
    check("2.1 a full render carries NO truncation marker", not asgi._html_truncated(body_full))
    check("2.1 a truncated render is MARKED (machine marker + 'partial view' banner)",
          asgi._html_truncated(body_part) and "Partial view" in body_part, body_part[:120])

    # ── 5.1: an unverified bot over its /a budget trips the rate limiter (→ snapshot/shell only) ──
    lim = asgi._IPRateLimiter(5)                    # 5/min bucket
    now = time.time()
    allowed = sum(1 for _ in range(20) if lim.check("9.9.9.9", now)[0])
    check("5.1 the per-IP /a bot budget sheds an over-rate IP", 1 <= allowed <= 6,
          "allowed=%d of 20" % allowed)

    # ── 5.3: per-class serve-time percentiles ──
    check("5.3 _pctile computes nearest-rank percentiles",
          asgi._pctile([10, 20, 30, 40, 50], 50) == 30 and asgi._pctile([], 50) is None)
    asgi._CLASS_STATS.clear(); asgi._CLASS_TIMES.clear()
    tok = asgi._REQ_START.set(time.time() - 0.012)   # 12 ms ago → a recorded serve time
    try:
        asgi._class_note("human", "live")
    finally:
        asgi._REQ_START.reset(tok)
    check("5.3 _class_note records a serve-time when a request-start is set",
          len(asgi._CLASS_TIMES.get("human") or []) == 1
          and asgi._CLASS_TIMES["human"][0] >= 10,
          "times=%s" % list(asgi._CLASS_TIMES.get("human") or []))

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("ALL PASS — a Googlebot UA is only a trusted crawler when its reverse DNS forward-confirms "
          "(B1); the disk snapshot store round-trips and expires on TTL so crawlers are served from "
          "disk with zero daemon RPCs (B2); per-class outcomes are accounted (B5).")
    sys.exit(0)


if __name__ == "__main__":
    main()
