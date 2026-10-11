#!/usr/bin/env python3
"""
F48-A — the L1 rendered-HTML cache: LRU eviction (1.6) + stale-while-revalidate (1.7).

The operator's "slow → fast on retry → slower-than-first later" staircase was the L1 cache's
600 s TTL landing on a degradation-phase daemon, plus a clear-all on overflow that cold-started
EVERY page at once under a crawl (a self-inflicted render stampede). Two fixes:
  1.6  overflow evicts the OLDEST ~10% (LRU), never clear-all — the newest pages survive.
  1.7  an EXPIRED entry is still a COMPLETE page (a truncated render is never cached), so it is
       served instantly (marked with its age) while a background render refreshes it — removing the
       "slower than the first visit" step and masking a daemon restart for every seen page.

This eval drives the cache primitives + the single-flight revalidation guard directly.

Run:  python test/l1_cache_eval.py   (exit 0 = all pass)
"""
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def main():
    import api.portals.asgi as asgi

    # ── 1.6 LRU eviction, not clear-all ──
    asgi._ATOM_HTML_CACHE.clear()
    asgi._ATOM_HTML_MAX = 20
    for i in range(40):
        asgi._atom_html_cache_put("h", "slug%03d" % i, "<html>%d</html>" % i)
        time.sleep(0.001)                              # distinct timestamps for a deterministic LRU
    size = len(asgi._ATOM_HTML_CACHE)
    check("1.6 overflow keeps the cache bounded (never grows past max)", size <= asgi._ATOM_HTML_MAX,
          "size=%d max=%d" % (size, asgi._ATOM_HTML_MAX))
    check("1.6 overflow is NOT a clear-all (cache is not emptied)", size > 1, "size=%d" % size)
    check("1.6 the NEWEST page survives; the OLDEST was evicted",
          asgi._atom_html_cache_get("h", "slug039") is not None
          and asgi._atom_html_cache_get("h", "slug000") is None,
          "newest=%s oldest=%s" % (asgi._atom_html_cache_get("h", "slug039") is not None,
                                   asgi._atom_html_cache_get("h", "slug000") is not None))

    # ── 1.7 stale-while-revalidate: expired entry is still served (complete), marked with age ──
    asgi._ATOM_HTML_CACHE.clear()
    asgi._ATOM_HTML_TTL = 0.05
    asgi._atom_html_cache_put("h", "bird", "<html>bird complete</html>")
    fresh = asgi._atom_html_cache_get("h", "bird")
    check("1.7 a fresh entry is returned normally", fresh == "<html>bird complete</html>")
    fresh2 = asgi._atom_html_cache_get("h", "bird", allow_stale=True)
    check("1.7 allow_stale on a FRESH entry → (html, age≈0)",
          isinstance(fresh2, tuple) and fresh2[0] == "<html>bird complete</html>" and fresh2[1] == 0.0)
    time.sleep(0.08)                                   # let it expire
    check("1.7 an EXPIRED entry is a miss for a normal get", asgi._atom_html_cache_get("h", "bird") is None)
    stale = asgi._atom_html_cache_get("h", "bird", allow_stale=True)
    check("1.7 an EXPIRED entry is served as (complete html, age>0) with allow_stale",
          isinstance(stale, tuple) and stale[0] == "<html>bird complete</html>" and stale[1] > 0,
          "stale=%s" % (stale,))
    check("1.7 an ABSENT entry is None even with allow_stale",
          asgi._atom_html_cache_get("h", "nope", allow_stale=True) is None)

    # ── single-flight revalidation guard (no refresh stampede) ──
    check("1.7 first revalidation claim on a slug succeeds", asgi._bg_refresh_claim("h", "bird") is True)
    check("1.7 a second concurrent claim on the same slug is refused",
          asgi._bg_refresh_claim("h", "bird") is False)
    asgi._bg_refresh_release("h", "bird")
    check("1.7 after release the slug can be claimed again", asgi._bg_refresh_claim("h", "bird") is True)
    asgi._bg_refresh_release("h", "bird")

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("ALL PASS — overflow evicts oldest-first (no clear-all stampede); an expired entry is served "
          "as a complete, age-marked page and revalidated single-flight in the background.")
    sys.exit(0)


if __name__ == "__main__":
    main()
