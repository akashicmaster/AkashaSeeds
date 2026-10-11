#!/usr/bin/env python3
"""
The live-telemetry PAGE, driven in a real browser.

`app/test/live_telemetry_eval.py` covers the backend foundation and never opens the page, so every
fault this surface has shipped was a fault nothing could have caught:

  • `msg(text)` was called on three lines and defined on none, so every path that needed to explain
    itself threw instead — including the one that says "live is not ready, this is the demo
    snapshot" (fixed 2026-09-23)
  • pressing play made the whole map unclickable (fixed 2026-09-25). A point was created FRESH on
    every animation frame, and a click needs the same element under the mousedown and the mouseup;
    at thirty rebuilds a second there never was one. Reported as "every click event stops getting
    through", which is exactly what it looks like from outside.
  • and the sweep LOOPED: at the end of the window the clock snapped back before the first
    observation, so the map emptied — every fourteen seconds, silently, for as long as the page
    was open.

So this eval holds the two properties those cost, and it drives them the way a person does: a real
mouse, pressed and released, on a real point, while the clock is running.

Run:  python app/test/live_page_eval.py        (exit 0 = all pass)
"""
import glob
import os
import shutil
import socket
import sys
import tempfile
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LIVE = os.path.join(ROOT, "app", "archives", "live")

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _serve(dirpath):
    """The page fetches its fixtures by relative path, which a `file://` origin refuses. So it is
    served over http, like the deployed cell serves it."""
    class H(SimpleHTTPRequestHandler):
        def __init__(self, *a, **k):
            super().__init__(*a, directory=dirpath, **k)

        def log_message(self, *a):
            pass

    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    srv = ThreadingHTTPServer(("127.0.0.1", port), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, port


def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("\n  SKIP — playwright is not installed; this eval drives the real page.\n")
        return 0
    if not os.path.isfile(os.path.join(LIVE, "feed_map.json")):
        print("\n  SKIP — the demo fixtures are not built in app/archives/live/.\n")
        return 0

    root = tempfile.mkdtemp(prefix="livepage_")
    shutil.copytree(LIVE, os.path.join(root, "live"))
    srv, port = _serve(root)
    base = "http://127.0.0.1:%d/live/?mode=demo" % port
    exe = next(iter(sorted(glob.glob("/opt/pw-browsers/chromium-*/chrome-linux/chrome"))), "")

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(**({"executable_path": exe} if exe else {}))
            page = browser.new_page()
            errs = []
            page.on("pageerror", lambda e: errs.append(str(e)))
            page.goto(base, wait_until="networkidle")
            page.wait_for_timeout(2000)

            def detail():
                return page.evaluate(
                    "()=>document.getElementById('detail').innerText.slice(0,30)")

            def visible():
                return page.evaluate(
                    # Implementation-agnostic on purpose: a point is a point wherever the page
                    # keeps it. Pinning this to the group the fix introduced would make the eval
                    # fail on the OLD page for the wrong reason — a missing selector rather than
                    # the behaviour, which is the only thing worth holding.
                    "()=>Array.from(document.querySelectorAll('svg#map g.pt'))"
                    ".filter(g=>g.style.display!=='none').length")

            def boxes():
                return page.evaluate(
                    "()=>Array.from(document.querySelectorAll('svg#map g.pt'))"
                    ".filter(g=>g.style.display!=='none')"
                    ".map(g=>{const r=g.getBoundingClientRect();"
                    "return {x:r.x+r.width/2,y:r.y+r.height/2};})")

            def press(box, hold_ms):
                """A REAL press: move, down, hold, up. `click(force=True)` dispatches the event at
                the element and would have passed against the broken page — the whole defect was
                that the element does not survive from the down to the up."""
                page.mouse.move(box["x"], box["y"])
                page.mouse.down()
                page.wait_for_timeout(hold_ms)
                page.mouse.up()
                page.wait_for_timeout(250)

            print("\n  ── at rest ──")
            n0 = visible()
            check("the map shows the whole window at rest", n0 > 1, "points=%d" % n0)
            bs = boxes()
            before = detail()
            press(bs[0], 300)
            check("a point selects on a human-length press", detail() != before, detail())

            print("\n  ── while the clock is sweeping ──")
            page.click("#play")
            page.wait_for_timeout(1200)
            check("play says what it is doing rather than silently wiping the map",
                  "replaying" in page.evaluate(
                      "()=>document.getElementById('msg').textContent").lower())
            page.wait_for_timeout(6000)
            bs = boxes()
            check("the sweep has put points back on the map", len(bs) >= 2,
                  "visible=%d" % len(bs))
            hits = []
            for b in bs[:4]:
                before = detail()
                press(b, 300)
                hits.append(detail() != before)
            check("a point is CLICKABLE while the clock runs — the regression that reads as "
                  "'every click stops working'", any(hits), "hits=%s" % hits)
            check("… and the play control itself still answers",
                  page.evaluate("()=>document.getElementById('play').textContent").strip()
                  .endswith("pause"))

            print("\n  ── when the sweep finishes ──")
            for _ in range(30):                       # DUR is ~14s; wait for the end, not a clock
                if not page.evaluate("()=>document.getElementById('play')"
                                     ".textContent.indexOf('pause')>=0"):
                    break
                page.wait_for_timeout(1000)
            check("it STOPS rather than looping back to an empty map",
                  page.evaluate("()=>document.getElementById('play').textContent")
                  .strip().startswith("▶"),
                  page.evaluate("()=>document.getElementById('play').textContent"))
            n1 = visible()
            check("… ending on the complete window, not on a blank one", n1 == n0,
                  "%d of %d" % (n1, n0))
            check("… and it says so", "swept" in page.evaluate(
                "()=>document.getElementById('msg').textContent").lower())
            # Several points, because two markers can resolve to the SAME observation and a
            # press that re-selects what is already open changes nothing — which is a fact about
            # the fixture, not about the page.
            bs = boxes()
            after = []
            for b in bs[:4]:
                before = detail()
                press(b, 300)
                after.append(detail() != before)
            check("a point still selects afterwards", any(after), "hits=%s" % after)

            check("no page errors at any point", not errs, str(errs[:2]))
            browser.close()
    finally:
        srv.shutdown()
        shutil.rmtree(root, ignore_errors=True)

    print()
    if _fails:
        print("RESULT: FAIL (%d): %s\n" % (len(_fails), "; ".join(_fails)))
        return 1
    print("RESULT: PASS — the telemetry map stays CLICKABLE while the clock sweeps (a real press, "
          "held as a person holds one, on a point that is being animated), the sweep announces the "
          "rewind instead of silently emptying the map, and it finishes on the whole window and "
          "stops rather than looping back to nothing.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
