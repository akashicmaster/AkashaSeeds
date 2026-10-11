#!/usr/bin/env python3
"""
THE ART EXPLORER'S GALLERY — the work on the wall is the work being discussed, or the wall is empty.

The room (app/archives/station/art-explorer/) is a studio like the reading room: the Curator (with the
Explorer a step behind) and the Visitor face each other across a framed work, and only the figure
whose turn it is moves its mouth. The work is the museum's own image — Cleveland Museum of Art Open
Access, CC0 — read from the aired line's `source` companions `<work>:image` / `:label` / `:credit`
(the `art_cma` pack). Rendered in Chromium against a mocked RPC, on a desk and a phone width:

  · the frame shows exactly `<source>:image`; the wall label is `<source>:label`; the credit names
    the museum and links the work's page from `<source>:credit`
  · the speaking role's mouth moves (`talk-c` for the Curator), and no page error is thrown
  · a line whose work has NO `:image` leaves the frame empty and SAYS so — nothing else is hung
  · a non-https image reference is refused (the frame stays empty)
  · on a phone the caption sits below the scene, and the work stays inside its frame

Run:  python app/test/station_gallery_eval.py     (exit 0 = all pass; skips if Chromium is absent)
"""
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PAGE = os.path.join(ROOT, "app", "archives", "station", "art-explorer", "index.html")
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
# a 1x1 PNG — the museum CDN is not reached from an eval
PNG = bytes.fromhex("89504e470d0a1a0a0000000d4948445200000001000000010806000000"
                    "1f15c4890000000d49444154789c6360f8cfc0f01f0005000201e5270de4"
                    "0000000049454e44ae426082")
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

    print("\n  ── static ──")
    check("the room reads the work's companions (:image, :label, :credit)",
          all(("':%s'" % c) in html for c in ("image", "label", "credit")))
    check("the image is embedded EXACTLY as the Source Viewer embeds it: a bare Image() with a src — "
          "no crossOrigin, no referrerPolicy, no hidden 'loading' state",
          "crossOrigin" not in html.replace("no crossOrigin", "")
          and "im.referrerPolicy" not in html and "im.className" not in html
          and "img.loading" not in html)

    W = "art:work:cma:1953_424"
    NOIMG = "art:work:cma:0000_000"
    BAD = "art:work:cma:0000_001"
    now = time.time()
    atoms = {W + ":image": "https://openaccess-cdn.clevelandart.org/1953.424/1953.424_web.jpg",
             W + ":label": "Madonna and Child with Saints — Example Maker · c. 1540",
             W + ":credit": "The Cleveland Museum of Art · Open Access (CC0) · https://clevelandart.org/art/1953.424",
             NOIMG + ":label": "A work with no image",
             BAD + ":image": "http://example.invalid/x.jpg"}

    def run(source, width, image_status=200):
        msgs = [{"cast_name": "Curator", "text": "Before us, a work.", "source": source,
                 "turn": "present#1", "ai_notice": "AI-generated · Mistral AI model",
                 "created_at": now - 30}]

        def rpc(route):
            b = json.loads(route.request.post_data or "{}")
            m, p = b.get("method"), b.get("params") or {}
            res = None
            if m == "session.guest.create":
                res = {"binding_key": "gbk:x", "expires_at": now + 3000}
            elif m == "workload.status":
                res = {"key": "studio_ai/art_explorer", "society": "studio_ai/art_explorer",
                       "last": {"at": now - 30, "ok": True}, "gate": {"run": "ok"},
                       "next_at": now + 3600, "spent_today": 5}
            elif m == "station.air.ls":
                res = {"aired": [], "count": 0}
            elif m == "society.broadcast.live":
                res = {"messages": msgs if not p.get("since") else [], "cursor": "c1"}
            elif m == "society.broadcast":
                res = {"messages": msgs}
            elif m == "r" and p.get("id") in atoms:
                res = {"content": "[%s]\n%s" % (p["id"], atoms[p["id"]])}
            body = ({"jsonrpc": "2.0", "id": m, "result": res} if res is not None else
                    {"jsonrpc": "2.0", "id": m, "error": {"code": -32002, "message": "not found"}})
            route.fulfill(status=200, content_type="application/json", body=json.dumps(body))

        pg = br.new_page(viewport={"width": width, "height": 900})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.route("http://station.test/station/art-explorer/",
                 lambda r: r.fulfill(status=200, content_type="text/html", body=html))
        pg.route("http://station.test/rpc", rpc)
        pg.route("http://station.test/pulse", lambda r: r.fulfill(status=204, body=""))
        pg.route("https://openaccess-cdn.clevelandart.org/**",
                 lambda r: r.fulfill(status=image_status, content_type="image/png",
                                     body=PNG if image_status == 200 else b""))
        pg.goto("http://station.test/station/art-explorer/")
        pg.wait_for_timeout(3500)
        out = {
            "errs": errs,
            "img": pg.eval_on_selector("#work", "e => { var i = e.querySelector('img'); return i ? i.src : null; }"),
            "none": pg.eval_on_selector("#work", "e => e.innerText"),
            "label": pg.inner_text("#wlabel"),
            "credit": pg.inner_html("#credit"),
            "stage": pg.eval_on_selector("#stage", "e => e.className"),
            "frame_ok": pg.evaluate("""() => {
                var s = document.querySelector('.scene').getBoundingClientRect(),
                    w = document.querySelector('#work').getBoundingClientRect(),
                    c = document.querySelector('#cap').getBoundingClientRect();
                return {inside: w.top >= s.top && w.bottom <= s.bottom,
                        cap_below: c.top >= s.bottom - 1};
            }"""),
        }
        pg.close()
        return out

    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=CHROME)
        print("\n  ── a work with its image (desk) ──")
        o = run(W, 1100)
        check("no page error", not o["errs"], str(o["errs"])[:120])
        check("the frame shows exactly <source>:image", o["img"] == atoms[W + ":image"], str(o["img"]))
        check("the wall label is <source>:label", o["label"] == atoms[W + ":label"], o["label"])
        check("the credit names the museum and CC0, and links the work's page",
              "Cleveland Museum of Art" in o["credit"] and "CC0" in o["credit"]
              and "https://clevelandart.org/art/1953.424" in o["credit"], o["credit"][:140])
        check("the Curator's mouth is the one moving", "talk-c" in o["stage"], o["stage"])
        check("the work sits inside the scene", o["frame_ok"]["inside"], str(o["frame_ok"]))

        print("\n  ── a work with NO image ──")
        o = run(NOIMG, 1100)
        check("nothing is hung, and the frame says why",
              o["img"] is None and "no image" in o["none"].lower(), repr(o["none"]))
        check("…and no credit is shown for an image that is not there", not o["credit"].strip())

        print("\n  ── the image fails to load (the CDN blocks it) ──")
        o = run(W, 1100, image_status=403)
        check("the frame says the image did not load", o["img"] is None and "did not load" in o["none"].lower(),
              repr(o["none"]))
        check("…but the wall label and the museum link STAY (the message promises the museum page)",
              o["label"] == atoms[W + ":label"] and "https://clevelandart.org/art/1953.424" in o["credit"],
              "%r | %s" % (o["label"], o["credit"][:80]))

        print("\n  ── a non-https reference ──")
        o = run(BAD, 1100)
        check("an http:// image reference is refused — the frame stays empty",
              o["img"] is None, str(o["img"]))

        print("\n  ── a phone ──")
        o = run(W, 390)
        check("no page error on a phone", not o["errs"], str(o["errs"])[:120])
        check("the caption sits BELOW the scene, and the work stays in its frame",
              o["frame_ok"]["cap_below"] and o["frame_ok"]["inside"], str(o["frame_ok"]))
        br.close()

    print()
    if _fails:
        print("RESULT: FAIL (%d): %s\n" % (len(_fails), "; ".join(_fails)))
        return 1
    print("RESULT: PASS — the gallery hangs exactly the work being discussed (its own :image, "
          "label and CC0 credit), moves only the speaker's mouth, leaves the frame empty and says "
          "so when a work has no image or an unsafe reference, and keeps the work in its frame on a "
          "phone with the caption below.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
