#!/usr/bin/env python3
"""
THE BUMPER PLAYS BETWEEN NEWS ITEMS, NEVER INSIDE ONE (D18, room side).

The AI News room plays a bumper where a new turn starts. A turn is one item's three beats, which share
the item (`source`); a turn NUMBER that changes between those beats (the backend's old sliding-window
count: 68/67/66) is a numbering fault and must not cut the item. Held on the page's own predicate (extracted as written) in
Chromium:  same item + changed number → no bumper;  new item + changed number → bumper;
same number → none;  first line → none;  no source on a line → the number decides.

Run:  python app/test/station_bumper_boundary_eval.py     (exit 0 = all pass; skips without Chromium)
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PAGE = os.path.join(ROOT, "app", "archives", "station", "ai-news", "index.html")
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("SKIP — playwright is not installed here"); return 0
    if not os.path.exists(CHROME):
        print("SKIP — no Chromium at %s" % CHROME); return 0
    html = open(PAGE, encoding="utf-8").read()
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=CHROME)
        pg = br.new_page()
        i = html.index("function _isNewTurn")
        j = html.index("function startPlayer", i)
        src = html[i:j]                      # the page's own predicate, run as written
        pg.set_content("<html></html>")
        f = lambda *a: pg.evaluate("a => { %s return _isNewTurn(a[0], a[1], a[2]); }" % src, list(a))
        check("first line: no bumper", f(None, None, {"turn": 5, "source": "x"}) is False)
        check("same number: no bumper", f(5, "x", {"turn": 5, "source": "x"}) is False)
        check("SAME item, number changed (68→67): no bumper — the owner's report",
              f(68, "item1", {"turn": 67, "source": "item1"}) is False)
        check("NEW item, number changed: bumper", f(66, "item1", {"turn": 67, "source": "item2"}) is True)
        check("no source on the line: the number decides", f(5, "x", {"turn": 6}) is True)
        check("no previous source: the number decides", f(5, None, {"turn": 6, "source": "y"}) is True)
        br.close()
    print()
    if _fails:
        print("RESULT: FAIL (%d): %s\n" % (len(_fails), "; ".join(_fails)))
        return 1
    print("RESULT: PASS — a bumper marks a change of item, and a turn number that wobbles inside one "
          "item cannot cut it.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
