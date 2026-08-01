#!/usr/bin/env python3
"""
SSR/SEO eval — server-side prerender of the atom-detail page (/a/<slug>).

Proves the render contract from docs/for-llm/atom-detail-ssr-seo-spec.md: on GET
/a/<slug>, the server injects real SEO <head> tags + a crawlable content body into
the shell's INITIAL HTML (so non-JS crawlers see content), guest-scoped (public only),
degradation-first (miss/private/error → plain shell, never a leak), and every injected
value HTML-escaped. Driven by a fake gateway so it is deterministic and starlette-free
(the render helpers are pure stdlib).

  S1 head      — title / meta description / canonical / OGP all in the raw <head>.
  S2 json-ld   — a valid schema.org DefinedTerm JSON-LD block (parses; correct @type/url).
  S3 body      — headword <h1>, description text, and related links as crawlable /a/ hrefs.
  S4 private   — a guest-unreadable slug (no result) → None (serve the shell; NO leaked text).
  S5 escaping  — hostile description/headword (<script>, quotes) is escaped, not injected raw.
  S6 no-marker — a template without the SSR marker → None (unchanged shell; no regression).
  S7 sitemap   — /sitemap.xml is a valid <sitemapindex> → core + per-namespace children;
                 each child <urlset> lists that namespace's /a/ URLs (breadth beyond top-200).

Run:  python test/ssr_seo_eval.py
"""
import os
import re
import sys
import json
import xml.dom.minidom as _minidom

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

from api.portals import asgi

_results = []


def record(name, ok, detail=""):
    _results.append((name, ok, detail))
    print(f"  {'OK  ' if ok else '!! FAIL'}  {name:12} {detail}")


def _valid_xml(s):
    try:
        _minidom.parseString(s)
        return True
    except Exception:
        return False


# A minimal shell template carrying the two injection points the real word/index.html has.
TEMPLATE = (
    "<!DOCTYPE html><html><head>\n"
    "  <title>AKASHA — Word Detail</title>\n"
    "  <!-- AKASHA:SSR_HEAD -->\n"
    "</head><body>\n"
    '  <div class="info-inner" id="info-inner">\n'
    '    <p class="state-msg" id="state-msg">loading …</p>\n'
    "  </div>\n"
    "</body></html>\n"
)

# archives.space payload shape (concept wraps a thesaurus.concept result).
CONCEPT_PAYLOAD = {
    "type": "archives:space",
    "concept": {
        "type": "thesaurus:concept",
        "atom": {
            "key": "abc123",
            "name": "concept:icarus",
            "term": "icarus",
            "description": "A figure who flew too close to the sun; a caution about hubris.",
            "aliases": ["concept:icarus", "icarus"],
            "meta": {},
        },
        "broader": [{"name": "myth:greek", "term": "greek"}],
        "narrower": [],
        "synonyms": [{"name": "concept:daedalus_son", "term": "daedalus_son"}],
        "related": [{"name": "concept:lilienthal", "term": "lilienthal", "rel": "thesaurus:related", "dir": "out"}],
        "external_refs": [
            {"label": "Icarus", "url": "https://en.wikipedia.org/wiki/Icarus", "source": "wikipedia"},
        ],
    },
}


class FakeGateway:
    """Answers only the two methods the SSR path calls: guest create + archives.space."""
    def __init__(self, payload_by_slug, reference_rows=None):
        self.payload_by_slug = payload_by_slug
        self.reference_rows = reference_rows or []   # [{"name","salience"}]

    def dispatch(self, req):
        m = req.get("method")
        if m == "session.guest.create":
            return {"jsonrpc": "2.0", "result": {"binding_key": "gbk:test"}, "id": req.get("id")}
        if m == "archives.space":
            slug = (req.get("params") or {}).get("name")
            payload = self.payload_by_slug.get(slug)
            if payload is None:
                # guest cannot read → empty result (mirrors a private/missing atom)
                return {"jsonrpc": "2.0", "result": None, "id": req.get("id")}
            return {"jsonrpc": "2.0", "result": payload, "id": req.get("id")}
        if m == "thesaurus.reference":
            p = req.get("params") or {}
            initial = (p.get("initial") or "").lower()
            rows = self.reference_rows
            if initial:
                rows = [r for r in rows
                        if (r.get("name") or "").split(":")[-1].lower().startswith(initial)]
            return {"jsonrpc": "2.0", "result": {"concepts": rows, "total": len(rows)},
                    "id": req.get("id")}
        return {"jsonrpc": "2.0", "error": {"code": -32601, "message": "method not found"}, "id": req.get("id")}


def main():
    print("\n  ssr/seo eval — prerender /a/<slug> for crawlers (guest-scoped, degradation-first)\n")
    asgi._ATOM_HTML_CACHE.clear()
    asgi._SSR_GUEST["tok"] = None

    origin = "https://akashicarchives.net"
    gw = FakeGateway({"concept:icarus": CONCEPT_PAYLOAD})

    html = asgi._render_atom_html(gw, TEMPLATE, "concept:icarus", origin, "akashicarchives.net")
    head = html.split("</head>", 1)[0] if html else ""

    # S1 — SEO head signals in the raw HTML (no JS). Exactly ONE <title>, the SEO one:
    # the shell's static <title> must be stripped (HTML is first-title-wins, else the
    # generic "AKASHA — Word Detail" would beat the per-atom title for crawlers).
    titles = re.findall(r"<title>(.*?)</title>", html or "", re.S)
    s1 = (html is not None
          and titles == ["Icarus — Akasha"]
          and "AKASHA — Word Detail" not in html
          and '<meta name="description" content="A figure who flew too close' in html
          and f'<link rel="canonical" href="{origin}/a/concept:icarus">' in html
          and '<meta property="og:title" content="Icarus">' in html
          and f'<meta property="og:url" content="{origin}/a/concept:icarus">' in html)
    record("S1 head", s1, f"single SEO <title> {titles}; description/canonical/OGP present")

    # S2 — JSON-LD parses and is a schema.org DefinedTerm with the right url/set.
    m = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    s2 = False
    if m:
        try:
            ld = json.loads(m.group(1))
            s2 = (ld.get("@type") == "DefinedTerm"
                  and ld.get("name") == "Icarus"
                  and ld.get("url") == f"{origin}/a/concept:icarus"
                  and ld.get("inDefinedTermSet", {}).get("name") == "Akasha Thesaurus"
                  and "https://en.wikipedia.org/wiki/Icarus" in (ld.get("sameAs") or []))
        except json.JSONDecodeError:
            s2 = False
    record("S2 json-ld", s2, "valid DefinedTerm JSON-LD w/ url + sameAs")

    # S3 — crawlable body: headword, description, related links as /a/ hrefs.
    s3 = (html is not None
          and '<h1 class="word-display-name">Icarus</h1>' in html
          and '<p class="word-description">A figure who flew too close to the sun' in html
          and 'href="/a/myth:greek"' in html
          and 'href="/a/concept:lilienthal"' in html
          and "loading …" not in html)     # the loading placeholder was replaced
    record("S3 body", s3, "h1 + description + related /a/ links; placeholder replaced")

    # S4 — private/missing slug → None (serve the shell). No description text leaks.
    priv = asgi._render_atom_html(gw, TEMPLATE, "secret:diary", origin, "akashicarchives.net")
    s4 = priv is None
    record("S4 private", s4, "guest-unreadable slug → shell (None), no prerender/leak")

    # S5 — escaping: a hostile payload is escaped, not injected raw.
    hostile = {
        "concept": {
            "atom": {
                "name": "concept:xss",
                "term": "xss",
                "description": 'Danger <script>alert("x")</script> & "quotes".',
                "meta": {},
            },
            "related": [], "external_refs": [],
        }
    }
    gw2 = asgi_gw = FakeGateway({"concept:xss": hostile})
    hx = asgi._render_atom_html(gw2, TEMPLATE, "concept:xss", origin, "h")
    s5 = (hx is not None
          and "<script>alert(" not in hx                  # raw script never injected
          and "&lt;script&gt;alert(" in hx                # it is escaped instead
          and "&amp;" in hx)
    record("S5 escaping", s5, "hostile <script>/quotes HTML-escaped, not injected raw")

    # S6 — a template with no SSR marker → None (unchanged shell, no regression).
    no_marker = TEMPLATE.replace(asgi._SSR_HEAD_MARKER, "")
    s6 = asgi._render_atom_html(gw, no_marker, "concept:icarus", origin, "h") is None
    record("S6 no-marker", s6, "template without marker → None (plain-file serving unchanged)")

    # S7 — sitemap index + per-namespace children. A guest glossary spanning several
    # namespaces (incl. a system one that must be excluded, and a non-URL-safe one).
    asgi._SITEMAP_CACHE.update(slugs=None, ts=0.0)
    asgi._SITEMAP_CORPUS.update(data=None, ts=0.0)
    ref_rows = [
        {"name": "food:apple", "salience": 0.9},
        {"name": "food:apricot", "salience": 0.5},
        {"name": "food:banana", "salience": 0.4},
        {"name": "ingred:almond", "salience": 0.3},
        {"name": "geo:argentina", "salience": 0.7},
        {"name": "sys:internal", "salience": 0.1},      # system prefix → excluded by glossary
        {"name": "bad ns:x", "salience": 0.1},          # non-URL-safe namespace → skipped
    ]
    # The unscoped glossary already drops system prefixes; emulate that so the corpus
    # test exercises the URL-safe-namespace guard on realistic input.
    smgw = FakeGateway({}, reference_rows=[r for r in ref_rows if not r["name"].startswith("sys:")])
    corpus = asgi._sitemap_corpus(smgw)
    # index namespaces: core first, then the URL-safe non-empty namespaces, sorted.
    ns_list = asgi._sitemap_index_namespaces(smgw)
    idx_xml = asgi._xml_sitemapindex(origin, ns_list)
    # child urlsets
    food_locs = asgi._sitemap_child_locs(smgw, origin, "food")
    food_xml = asgi._xml_urlset(food_locs)
    # core child = root + top salient
    asgi._SITEMAP_CACHE.update(slugs=None, ts=0.0)
    core_locs = asgi._sitemap_child_locs(smgw, origin, "core")

    ok_corpus = (set(corpus.keys()) == {"food", "ingred", "geo"}      # sys/bad-ns excluded
                 and set(corpus["food"]) == {"food:apple", "food:apricot", "food:banana"})
    ok_index = (_valid_xml(idx_xml)
                and "<sitemapindex" in idx_xml
                and ns_list[0] == "core"
                and f"{origin}/sitemap/food.xml" in idx_xml
                and f"{origin}/sitemap/geo.xml" in idx_xml
                and "sitemap/sys.xml" not in idx_xml)
    ok_child = (_valid_xml(food_xml)
                and "<urlset" in food_xml
                and f"{origin}/a/food:apple" in food_xml
                and f"{origin}/a/food:banana" in food_xml)
    ok_core = (core_locs and core_locs[0] == origin + "/"
               and f"{origin}/a/food:apple" in core_locs)
    s7 = ok_corpus and ok_index and ok_child and ok_core
    record("S7 sitemap", s7,
           f"index ns={ns_list}, food child urls={len(food_locs)}, core[0]={core_locs[0] if core_locs else None}")

    print()
    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"  {passed}/{total} phases passed"
          + (f", {total - passed} FAILED" if passed < total else ""))
    if passed < total:
        print("\nRESULT: FAIL — the SSR/SEO prerender contract regressed.")
        return 1
    print("\nRESULT: PASS — /a/<slug> prerenders SEO head + crawlable body into the initial "
          "HTML, guest-scoped and degradation-first; hostile values escaped, private atoms shell.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
