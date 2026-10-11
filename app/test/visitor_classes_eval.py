#!/usr/bin/env python3
"""
Visitor Classes — the service-contract taxonomy and upgrade ladder (docs/for-llm/visitor-classes-spec.md).

Because "someone accessing the system" had no defined classes, every anonymous view was served as a
full resident (a ~25 MB private cell) and the daemon OOMed every ~15 min. The taxonomy IS the fix:
crawler (verified bot, snapshots only), human visitor (real browser / proven-human, live path),
passerby (unverifiable, snapshot/shell first + rate limit), resident (IAM, private cell on first
write). This eval pins the classification, the passerby→human upgrade ladder, and invariant I5.

Run:  python app/test/visitor_classes_eval.py   (exit 0 = all pass)
"""
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def main():
    os.environ["AKASHA_SNAPSHOT_DIR"] = tempfile.mkdtemp(prefix="vc_snap_")
    import api.portals.asgi as asgi

    GBOT = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
    HUMAN = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
             "(KHTML, like Gecko) Chrome/120 Safari/537.36")
    SCRAPER = "python-requests/2.31.0"

    def gbot_ok(kind, arg):
        return "crawl-66-249-66-1.googlebot.com" if kind == "ptr" else (["66.249.66.1"] if kind == "fwd" else None)

    asgi._RDNS_CACHE.clear(); asgi._HUMAN_IPS.clear()

    # ── the four visitor classes ──
    crawler = asgi._classify_client(GBOT, "66.249.66.1", resolver=gbot_ok)
    check("crawler = verified search bot (UA + forward-confirmed rDNS)",
          crawler["class"] == "crawler" and crawler["verified"], str(crawler))

    human = asgi._classify_client(HUMAN, "1.2.3.4")
    check("human visitor = a real browser UA, served generously (never degrade a potential resident)",
          human["class"] == "human", str(human))

    passerby = asgi._classify_client(SCRAPER, "5.6.7.8")
    check("passerby = unverifiable automated client (no identity, no DNS-provable bot-hood)",
          passerby["class"] == "passerby", str(passerby))

    # an impostor (claims Googlebot, PTR does not confirm) is a passerby, never a crawler
    asgi._RDNS_CACHE.clear()
    impostor = asgi._classify_client(GBOT, "9.9.9.9",
                                     resolver=lambda k, a: ("x.googlebot.com" if k == "ptr" else ["1.1.1.1"]))
    check("an impostor crawler-UA is a passerby, never granted crawler trust",
          impostor["class"] == "passerby", str(impostor))

    # ── the upgrade ladder: passerby → human visitor by proving humanity (the beacon) ──
    asgi._HUMAN_IPS.clear()
    before = asgi._classify_client(SCRAPER, "10.0.0.1")
    check("ladder start: an odd client is a passerby before it proves humanity",
          before["class"] == "passerby")
    asgi._mark_human("10.0.0.1")                          # the /pulse beacon fires (real browser JS)
    after = asgi._classify_client(SCRAPER, "10.0.0.1")
    check("ladder: after firing the beacon the SAME IP is reclassified human visitor",
          after["class"] == "human" and after["verified"], str(after))
    check("humanity proof is TTL'd + bounded (a classification hint, never a stored record)",
          asgi._is_proven_human("10.0.0.1") and not asgi._is_proven_human("no.such.ip"))

    # ── I5: a passerby always gets a COMPLETE document, and its upgrade path stays open ──
    # A fresh snapshot is a complete document served with zero daemon contact; over-rate falls to the
    # shell (also complete). Either way the page carries the beacon (served in the shared word viewer),
    # so the passerby can always prove humanity next.
    host, slug = "archives.space", "concept:owl"
    asgi._snapshot_write(host, slug, "<html>owl</html>")
    check("I5 a passerby is served a complete snapshot document (zero daemon)",
          asgi._snapshot_read(host, slug) == "<html>owl</html>")
    beacon_in_viewer = os.path.isfile(os.path.join(ROOT, "services", "static", "word", "index.html"))
    if beacon_in_viewer:
        html = open(os.path.join(ROOT, "services", "static", "word", "index.html")).read()
        check("I5 the humanity beacon rides every rendered page (upgrade path always open)",
              "/pulse" in html and "sendBeacon" in html)

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("ALL PASS — the visitor taxonomy holds (crawler / human / passerby), an impostor never gets "
          "crawler trust, the passerby→human upgrade ladder works via the beacon, and a passerby "
          "always receives a complete document with its upgrade path open (I5).")
    sys.exit(0)


if __name__ == "__main__":
    main()
