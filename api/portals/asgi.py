"""
Akasha ASGI / CGI Portal.

Entry points:
  run_server(gw, host, port)        — FastAPI ASGI server
  run_cgi(gw, original_stdout)      — CGI handler for legacy hosts

OpenAPI-compliant: GET /health (sys.ping), POST /rpc (JSON-RPC 2.0),
GET /docs (Swagger UI), GET /openapi.json.

No lib.* imports. Falls back to the stdio shell when FastAPI/uvicorn absent.
"""

import sys
import os
import json
import logging
from typing import Any

from api.env_detector import Symbiosis

logger = logging.getLogger("Harmonia.Portal.ASGI")

# Paths that are the shared backend/app, never a per-host document root — they
# must reach the API/RPC surface (or the shared atom viewer / SEO endpoints)
# regardless of which domain the browser came from.
_RESERVED_PREFIXES = ("/rpc", "/api/rpc", "/api/readme", "/health",
                      "/docs", "/redoc", "/openapi.json",
                      "/a", "/robots.txt", "/sitemap.xml", "/sitemap")


class HostReroute:
    """Pure-ASGI middleware: remap the document root per Host header.

    A request for ``/`` (or any static asset) arriving on ``world.<base>`` is
    rewritten to ``/world/…`` so the ``/`` StaticFiles mount serves
    ``archives/world/…``.  API/RPC paths are passed through untouched — the RPC
    backend is shared across every domain.  Falls back to the default archives
    root when the host has no matching sub-directory.  See services/host_routing.
    """

    def __init__(self, app, archives_root):
        self.app = app
        self.archives_root = archives_root

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "http":
            path = scope.get("path", "/")
            if not any(path == p or path.startswith(p + "/") for p in _RESERVED_PREFIXES):
                host = ""
                for k, v in scope.get("headers", []):
                    if k == b"host":
                        host = v.decode("latin-1", "ignore")
                        break
                try:
                    from services.host_routing import resolve_host_dir
                    host_dir = resolve_host_dir(host, self.archives_root)
                except Exception:
                    host_dir = None
                if host_dir:
                    prefix = "/" + host_dir
                    if not (path == prefix or path.startswith(prefix + "/")):
                        new_path = prefix + (path if path != "/" else "/")
                        scope = dict(scope)
                        scope["path"] = new_path
                        scope["raw_path"] = new_path.encode("utf-8")
        await self.app(scope, receive, send)


import threading as _threading
import time as _time
import html as _htmlmod
import re as _re
from xml.sax.saxutils import escape as _xml_escape

# Cached sitemap data (shared across hosts; the <loc> host/scheme is filled
# per-request so every domain gets a same-origin sitemap).
_SITEMAP_CACHE  = {"slugs": None, "ts": 0.0}          # top-salient "core" slugs
_SITEMAP_CORPUS = {"data": None, "ts": 0.0}           # {namespace: [slug, …]} (breadth)
_SITEMAP_LOCK   = _threading.Lock()
_SITEMAP_TTL    = 3600.0        # regenerate at most hourly — off the hot path
_SITEMAP_ALPHA  = "abcdefghijklmnopqrstuvwxyz"
_SITEMAP_NS_MAX = 50000         # sitemaps.org per-file URL cap
_SITEMAP_NS_RE  = _re.compile(r"^[a-z0-9_]+$")   # URL-safe, non-system namespaces only


def _sitemap_slugs(gw):
    """The top-salience 'core' slugs for the entry sitemap (/sitemap/core.xml).

    One guest read of thesaurus.reference (the glossary of named concepts, each
    carrying its salience), sorted by salience and capped to the highest-value
    slice — exactly what should be crawled first — cached for _SITEMAP_TTL.
    Broad per-namespace coverage is the separate corpus below.
    """
    now = _time.time()
    with _SITEMAP_LOCK:
        if _SITEMAP_CACHE["slugs"] is not None and (now - _SITEMAP_CACHE["ts"]) < _SITEMAP_TTL:
            return _SITEMAP_CACHE["slugs"]
    slugs = []
    try:
        res = _guest_call(gw, "thesaurus.reference", {"limit": 500})
        concepts = (res or {}).get("concepts", [])
        concepts.sort(key=lambda c: c.get("salience") or 0, reverse=True)
        for a in concepts[:200]:
            slug = a.get("name") or a.get("term")
            if slug:
                slugs.append(slug)
    except Exception as exc:
        logger.warning("[ASGI] sitemap core generation failed: %s", exc)
    with _SITEMAP_LOCK:
        _SITEMAP_CACHE["slugs"] = slugs
        _SITEMAP_CACHE["ts"] = now
    return slugs


def _sitemap_corpus(gw):
    """{namespace: [qualified-alias slug, …]} for the whole public glossary — the
    breadth behind the per-namespace child sitemaps.

    Gathered by an alpha initial-sweep (a–z) of the guest thesaurus.reference and
    grouped by the alias's first colon-segment, so a domain site exposes *all* of
    its atoms (e.g. every food), not just the global-salient slice. Guest-scoped
    (public-only), bounded (≤1000 per letter, ≤_SITEMAP_NS_MAX per namespace),
    cached for _SITEMAP_TTL. System namespaces are already excluded by the glossary
    filter; a URL-safe non-system namespace check is applied here too. Non-alpha-
    initial concepts (CJK / numeric) are not in the browseable glossary — a future
    multi-locale refinement (see multilocale-nlp-roadmap)."""
    now = _time.time()
    with _SITEMAP_LOCK:
        if _SITEMAP_CORPUS["data"] is not None and (now - _SITEMAP_CORPUS["ts"]) < _SITEMAP_TTL:
            return _SITEMAP_CORPUS["data"]
    corpus: dict = {}
    seen: set = set()
    try:
        for ch in _SITEMAP_ALPHA:
            res = _guest_call(gw, "thesaurus.reference",
                              {"initial": ch, "order": "alpha", "limit": 1000, "scan": 50000})
            for c in (res or {}).get("concepts", []):
                name = c.get("name") or c.get("term")
                if not name or ":" not in name or name in seen:
                    continue
                ns = name.split(":", 1)[0]
                if not _SITEMAP_NS_RE.match(ns):
                    continue
                bucket = corpus.setdefault(ns, [])
                if len(bucket) < _SITEMAP_NS_MAX:
                    bucket.append(name)
                    seen.add(name)
    except Exception as exc:
        logger.warning("[ASGI] sitemap corpus generation failed: %s", exc)
    with _SITEMAP_LOCK:
        _SITEMAP_CORPUS["data"] = corpus
        _SITEMAP_CORPUS["ts"] = now
    return corpus


def _xml_urlset(locs) -> str:
    """A <urlset> of <loc> entries (a leaf sitemap)."""
    urls = "\n".join(f"  <url><loc>{_xml_escape(loc)}</loc></url>" for loc in locs)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + urls + ("\n" if urls else "") + "</urlset>\n")


def _xml_sitemapindex(origin: str, namespaces) -> str:
    """A <sitemapindex> pointing at /sitemap/<ns>.xml children (same-origin)."""
    maps = "\n".join(
        f"  <sitemap><loc>{_xml_escape(origin)}/sitemap/{_xml_escape(ns)}.xml</loc></sitemap>"
        for ns in namespaces)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + maps + ("\n" if maps else "") + "</sitemapindex>\n")


def _sitemap_index_namespaces(gw):
    """Ordered child list for the index: 'core' first, then every non-empty namespace."""
    return ["core"] + sorted(ns for ns, s in _sitemap_corpus(gw).items() if s)


def _sitemap_child_locs(gw, origin: str, ns: str):
    """The <loc> URLs for one child sitemap (ns='core' = root + top-salient)."""
    if ns == "core":
        return [origin + "/"] + [origin + _slug_path(s) for s in _sitemap_slugs(gw)]
    return [origin + _slug_path(s) for s in (_sitemap_corpus(gw).get(ns) or [])]


def _origin(request) -> str:
    """scheme://host for the incoming request, honouring TLS and the Host header."""
    host = (request.headers.get("host") or request.url.netloc or "localhost").split(",")[0].strip()
    scheme = request.headers.get("x-forwarded-proto") or request.url.scheme or "http"
    return f"{scheme}://{host}"


def _slug_path(slug: str) -> str:
    """Encode a qualified alias into a clean /a/ path — keep ':' readable."""
    from urllib.parse import quote
    return "/a/" + quote(slug, safe=":")


# ── SSR prerender for /a/<slug> (SEO) ────────────────────────────────────────
# Inject SEO <head> tags + a crawlable content body into the atom-viewer shell so
# non-JS crawlers (Bing, social unfurlers, LLM bots) and Googlebot index real
# content in the INITIAL HTML — the client JS then enhances exactly as before.
# Degradation-first: any miss / private atom / error → the plain shell, never a
# 500, never a leak. Pure stdlib (import-safe without starlette) + guest-scoped
# reads (the public fence). See docs/for-llm/atom-detail-ssr-seo-spec.md.

_SSR_HEAD_MARKER      = "<!-- AKASHA:SSR_HEAD -->"
_SSR_BODY_PLACEHOLDER = '<p class="state-msg" id="state-msg">loading …</p>'
_SSR_DESC_META        = 155     # <meta description> trim
_SSR_DESC_OG          = 200     # og:description trim
_SSR_DESC_LD          = 500     # JSON-LD description trim
_SSR_MAX_RELATED      = 60      # crawlable related-link cap per page
# Bound the per-atom SSR read: a high-degree hub atom's concept build (2-hop neighbourhood)
# can take a long time server-side, which would otherwise hold the /a/<slug> HTTP response
# open for minutes (a blank browser tab). On timeout we serve the SHELL (client renders and
# degrades on its own) — the same degrade-first path as a concept miss. Tunable via env.
_SSR_FETCH_TIMEOUT    = float(os.environ.get("AKASHA_SSR_TIMEOUT", "6"))
_SSR_POOL = {"ex": None}        # lazy ThreadPoolExecutor (only when SSR is actually used)

# Rendered-HTML cache (bounded + short TTL) so a crawl burst does not re-render.
_ATOM_HTML_CACHE = {}                      # (host, slug) -> (html, ts)
_ATOM_HTML_LOCK  = _threading.Lock()
_ATOM_HTML_TTL   = 600.0
_ATOM_HTML_MAX   = 2048
# Template bytes cached by mtime (refreshes on redeploy).
_TEMPLATE_CACHE = {"path": None, "mtime": 0.0, "text": None}
# One reused guest token (re-minted on miss) — amortises session.guest.create.
_SSR_GUEST = {"tok": None}
_SSR_GUEST_LOCK = _threading.Lock()


def _e(s) -> str:
    """Attribute/text-safe HTML escape (quotes too)."""
    return _htmlmod.escape("" if s is None else str(s), quote=True)


def _collapse(text: str, limit: int) -> str:
    """Collapse whitespace and trim to `limit` chars with an ellipsis."""
    t = " ".join((text or "").split())
    if len(t) > limit:
        t = t[:limit - 1].rstrip() + "…"
    return t


def _site_name(host: str) -> str:
    h = (host or "").lower()
    if "kitchen" in h:
        return "Akashic Kitchen"
    if "archive" in h:
        return "Akashic Archives"
    return "Akasha"


def _display_name(atom: dict) -> str:
    """Server-side 'most human-readable defined form' (mirrors the client displayName):
    a namespaced alias shows its last colon-segment, underscores→spaces, title-cased;
    a bare word is shown as-is."""
    name = atom.get("name") or ""
    # geo:country:* — the description IS the country name ("Australia"); the last alias
    # segment is only the ISO3 code ("AUS") and meta.name is the qualified key. Prefer the
    # description head so the prerendered/crawlable headword reads as the country.
    if name.startswith("geo:country:"):
        desc = (atom.get("description") or "").split("—", 1)[0].strip()
        if desc:
            return desc
    term = atom.get("term") or (name.split(":")[-1] if name else "")
    if ":" in name:
        words = term.replace("_", " ").split()
        pretty = " ".join((w[:1].upper() + w[1:]) if w else w for w in words)
        return pretty or term
    return term or name


def _ssr_guest_token(gw, force: bool = False):
    """A reused guest token; re-mint when forced (pool reclaimed) or missing."""
    if not force:
        with _SSR_GUEST_LOCK:
            if _SSR_GUEST["tok"]:
                return _SSR_GUEST["tok"]
    tok = None
    try:
        g = gw.dispatch({"jsonrpc": "2.0", "method": "session.guest.create",
                         "params": {}, "id": "ssr"})
        tok = (g.get("result") or {}).get("binding_key")
    except Exception as exc:
        logger.warning("[ASGI] SSR guest create failed: %s", exc)
    with _SSR_GUEST_LOCK:
        _SSR_GUEST["tok"] = tok
    return tok


def _guest_call(gw, method: str, params: dict):
    """Dispatch a guest-scoped READ, injecting the reused guest token and retrying
    ONCE with a fresh token if the pool reclaimed it mid-flight. Returns the result
    dict/list or None. The single public-content fence for the SEO surface."""
    def _call(tok):
        p = dict(params); p["session_token"] = tok
        r = gw.dispatch({"jsonrpc": "2.0", "method": method, "params": p, "id": "seo"}) or {}
        return r.get("result")
    tok = _ssr_guest_token(gw)
    if not tok:
        return None
    res = _call(tok)
    if not res:                                       # token may have been reclaimed → retry once fresh
        tok = _ssr_guest_token(gw, force=True)
        res = _call(tok) if tok else None
    return res or None


def _ssr_fetch_concept(gw, slug: str):
    """Guest-scoped read of one concept (public-only). archives.space wraps the
    thesaurus concept payload; returns the raw result dict or None (miss/private/slow).

    Bounded by _SSR_FETCH_TIMEOUT: a slow hub atom must not hold the HTTP response open —
    on timeout we return None so the caller serves the shell (client renders instead)."""
    ex = _SSR_POOL["ex"]
    if ex is None:
        import concurrent.futures as _cf
        ex = _SSR_POOL["ex"] = _cf.ThreadPoolExecutor(max_workers=4, thread_name_prefix="ssr")
    import concurrent.futures as _cf
    try:
        return ex.submit(_guest_call, gw, "archives.space", {"name": slug}).result(
            timeout=_SSR_FETCH_TIMEOUT)
    except _cf.TimeoutError:
        logger.warning("[ASGI] SSR concept fetch for %r exceeded %ss — serving shell",
                       slug, _SSR_FETCH_TIMEOUT)
        return None
    except Exception as exc:
        logger.warning("[ASGI] SSR concept fetch failed for %r: %s", slug, exc)
        return None


def _ssr_fields(gw, slug: str, host: str):
    """Extract the render fields from a guest concept read, or None to fall to the shell."""
    payload = _ssr_fetch_concept(gw, slug)
    if not payload:
        return None
    concept = payload.get("concept") or payload      # archives.space wraps under 'concept'
    atom = concept.get("atom") or {}
    headword = _display_name(atom)
    if not headword:
        return None                                   # nothing meaningful to prerender → shell

    seen, related = set(), []
    for grp in ("broader", "narrower", "synonyms", "antonyms", "related"):
        for it in (concept.get(grp) or []):
            if not isinstance(it, dict):
                continue
            n = it.get("name")
            if not n or n in seen:
                continue
            seen.add(n)
            related.append((n, _display_name(it) or it.get("term") or n))
            if len(related) >= _SSR_MAX_RELATED:
                break
        if len(related) >= _SSR_MAX_RELATED:
            break

    refs = [r for r in (concept.get("external_refs") or [])
            if isinstance(r, dict) and r.get("url")]

    return {
        "headword":       headword,
        "canonical_slug": atom.get("name") or slug,   # canonicalise alias variants to the primary
        "description":    atom.get("description") or "",
        "related":        related,
        "refs":           refs,
        "site_name":      _site_name(host),
    }


def _ssr_build_head(fields: dict, origin: str) -> str:
    """§1a — the SEO <head> block (title/description/canonical/OGP/twitter + JSON-LD)."""
    head = fields["headword"]
    url  = origin + _slug_path(fields["canonical_slug"])
    desc = fields["description"]
    parts = [
        f'<title>{_e(head)} — Akasha</title>',
        f'<meta name="description" content="{_e(_collapse(desc, _SSR_DESC_META))}">',
        f'<link rel="canonical" href="{_e(url)}">',
        '<meta property="og:type" content="article">',
        f'<meta property="og:site_name" content="{_e(fields["site_name"])}">',
        f'<meta property="og:title" content="{_e(head)}">',
        f'<meta property="og:description" content="{_e(_collapse(desc, _SSR_DESC_OG))}">',
        f'<meta property="og:url" content="{_e(url)}">',
        '<meta name="twitter:card" content="summary">',
    ]
    ld = {
        "@context": "https://schema.org",
        "@type": "DefinedTerm",
        "name": head,
        "url": url,
        "inDefinedTermSet": {"@type": "DefinedTermSet",
                             "name": "Akasha Thesaurus", "url": origin + "/"},
    }
    if desc:
        ld["description"] = _collapse(desc, _SSR_DESC_LD)
    same = [r["url"] for r in fields["refs"] if str(r.get("url", "")).startswith("http")]
    if same:
        ld["sameAs"] = same[:12]
    # Escape '<' so no substring can close the <script> element early.
    ld_json = json.dumps(ld, ensure_ascii=False).replace("<", "\\u003c")
    parts.append('<script type="application/ld+json">' + ld_json + '</script>')
    return "\n  ".join(parts)


def _ssr_build_body(fields: dict) -> str:
    """§1b — the prerendered, crawlable content body (fills #info-inner)."""
    out = [f'<h1 class="word-display-name">{_e(fields["headword"])}</h1>']
    slug = fields["canonical_slug"]
    if slug:
        out.append(f'<span class="word-alias">{_e(slug)}</span>')
    if fields["description"]:
        out.append(f'<p class="word-description">{_e(fields["description"])}</p>')
    if fields["related"]:
        links = "".join(
            f'<a class="term" href="{_e(_slug_path(n))}">{_e(label)}</a> '
            for n, label in fields["related"])
        out.append(f'<nav aria-label="related">{links.rstrip()}</nav>')
    ref_items = "".join(
        f'<a href="{_e(r["url"])}" rel="nofollow noopener" target="_blank">'
        f'{_e(r.get("label") or r["url"])} ({_e(r.get("source") or "")})</a> '
        for r in fields["refs"] if r.get("url"))
    if ref_items:
        out.append(f'<aside aria-label="references">{ref_items.rstrip()}</aside>')
    return "\n".join(out)


def _render_atom_html(gw, template: str, slug: str, origin: str, host: str = ""):
    """Render one atom-detail page: inject the SEO head + prerendered body into the
    shell template. Returns the full HTML string, or None to serve the plain shell
    (miss / private / no marker). Pure — no starlette dependency (unit-testable)."""
    if not template or _SSR_HEAD_MARKER not in template:
        return None
    fields = _ssr_fields(gw, slug, host)
    if fields is None:
        return None
    html = template.replace(_SSR_HEAD_MARKER, _ssr_build_head(fields, origin), 1)
    # The shell ships a static <title> before the marker; our injected head adds the
    # per-atom one. HTML is first-<title>-wins, so drop the ORIGINAL static title (the
    # first one) — leaving the injected SEO title as the effective one for crawlers.
    html = _re.sub(r"<title>.*?</title>\s*", "", html, count=1, flags=_re.S)
    if _SSR_BODY_PLACEHOLDER in html:
        html = html.replace(_SSR_BODY_PLACEHOLDER, _ssr_build_body(fields), 1)
    return html


def _read_template(path: str):
    """Template bytes cached by mtime — refreshes only when the file changes."""
    try:
        mtime = os.stat(path).st_mtime
    except OSError:
        return None
    c = _TEMPLATE_CACHE
    if c["path"] == path and c["mtime"] == mtime and c["text"] is not None:
        return c["text"]
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return None
    c.update(path=path, mtime=mtime, text=text)
    return text


def _atom_html_cache_get(host: str, slug: str):
    now = _time.time()
    with _ATOM_HTML_LOCK:
        v = _ATOM_HTML_CACHE.get((host, slug))
        if v and (now - v[1]) < _ATOM_HTML_TTL:
            return v[0]
    return None


def _atom_html_cache_put(host: str, slug: str, html: str) -> None:
    now = _time.time()
    with _ATOM_HTML_LOCK:
        if len(_ATOM_HTML_CACHE) >= _ATOM_HTML_MAX:
            _ATOM_HTML_CACHE.clear()        # simple bound: dump on overflow, re-warm lazily
        _ATOM_HTML_CACHE[(host, slug)] = (html, now)


def _register_seo_routes(app, fastapi_mod, gw, root_dir):
    """Clean permalinks + crawlability, all client-rendered (same as word page):
      GET /a/<slug>     → serve the shared atom viewer (word/index.html)
      GET /robots.txt   → allow all + point to this host's sitemap
      GET /sitemap.xml  → same-origin URLs for the salient atoms
    """
    from starlette.responses import (FileResponse, PlainTextResponse, Response,
                                      HTMLResponse)

    word_index = os.path.join(root_dir, "word", "index.html")

    @app.get("/a/{slug:path}", include_in_schema=False)
    async def _atom_permalink(request: fastapi_mod.Request, slug: str):
        if not os.path.isfile(word_index):
            return Response("Atom viewer unavailable", status_code=404)
        # SSR: inject SEO head + a crawlable content body for THIS atom into the
        # shell (guest-scoped read → public content only). Degradation-first: a
        # miss / private atom / render error → the plain shell (today's behavior),
        # never a 500, never a leak. The client JS still enhances to the full view.
        host = (request.headers.get("host") or "").split(",")[0].strip()
        cached = _atom_html_cache_get(host, slug)
        if cached is not None:
            return HTMLResponse(cached, headers={"Cache-Control": "no-cache"})
        html = None
        try:
            html = _render_atom_html(gw, _read_template(word_index), slug,
                                     _origin(request), host)
        except Exception as exc:
            logger.warning("[ASGI] SSR render error for %r: %s", slug, exc)
            html = None
        if html is None:
            # no-cache → the browser revalidates every load, so a redeployed viewer
            # is picked up immediately instead of served stale from heuristic cache.
            return FileResponse(word_index, media_type="text/html",
                                headers={"Cache-Control": "no-cache"})
        _atom_html_cache_put(host, slug, html)
        return HTMLResponse(html, headers={"Cache-Control": "no-cache"})

    @app.get("/robots.txt", include_in_schema=False)
    async def _robots(request: fastapi_mod.Request):
        body = ("User-agent: *\n"
                "Allow: /\n"
                "Disallow: /rpc\n"
                "Disallow: /api/\n"
                f"Sitemap: {_origin(request)}/sitemap.xml\n")
        return PlainTextResponse(body)

    @app.get("/sitemap.xml", include_in_schema=False)
    async def _sitemap_index(request: fastapi_mod.Request):
        # A sitemap INDEX → one 'core' child (root + top-salient) + one child per
        # public namespace, so a domain site exposes ALL its atoms, paged per the
        # sitemaps.org 50k-per-file limit.
        origin = _origin(request)
        return Response(_xml_sitemapindex(origin, _sitemap_index_namespaces(gw)),
                        media_type="application/xml")

    @app.get("/sitemap/{ns}.xml", include_in_schema=False)
    async def _sitemap_child(request: fastapi_mod.Request, ns: str):
        origin = _origin(request)
        return Response(_xml_urlset(_sitemap_child_locs(gw, origin, ns)),
                        media_type="application/xml")


def run_server(gw, host: str = "0.0.0.0", port: int = 8000, static_dirs=None,
               ssl_certfile=None, ssl_keyfile=None):
    """
    FastAPI ASGI server.
    Safe to call from a background thread — uvicorn signal handlers are
    skipped automatically when not running on the main thread.
    Logs a warning and returns (does NOT fall back to CLI) when called
    from a background thread and dependencies are absent.
    """
    import threading
    _in_bg = threading.current_thread() is not threading.main_thread()

    fastapi_mod = Symbiosis.require("fastapi",  scope="[ASGI]", feature="Web Server Core",
                                    ask=not _in_bg)
    uvicorn_mod = Symbiosis.require("uvicorn",  scope="[ASGI]", feature="ASGI Engine",
                                    ask=not _in_bg)

    if not fastapi_mod or not uvicorn_mod:
        if _in_bg:
            logger.warning("[ASGI] Dependencies absent — background portal not started.")
        else:
            print("[!] ASGI dependencies offline. Web portal unavailable.")
        return

    app = fastapi_mod.FastAPI(
        title="Akasha Substrate Gateway",
        description="JSON-RPC 2.0 Interface for the Akasha Semantic Mesh",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    cors_mod = Symbiosis.require(
        "fastapi.middleware.cors", package_name="fastapi",
        scope="[ASGI]", feature="CORS", ask=False
    )
    if cors_mod:
        app.add_middleware(
            cors_mod.CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.get("/health", summary="Consciousness liveness check (sys.ping)")
    async def health():
        resp = gw.dispatch({
            "jsonrpc": "2.0", "method": "sys.ping",
            "params": {"session_token": "_health_"}, "id": "health",
        })
        result = resp.get("result", {})
        result.setdefault("status", "ok" if "error" not in resp else "degraded")
        return result

    async def _rpc_dispatch(request: fastapi_mod.Request) -> Any:
        try:
            payload = await request.json()
            # Relay Authorization header as session_token if params don't carry one.
            # API layer does not interpret the token — it is opaque to us.
            if isinstance(payload, dict):
                p = payload.get("params")
                if isinstance(p, dict) and not p.get("session_token"):
                    auth = request.headers.get("Authorization", "")
                    if auth.startswith("Bearer "):
                        p["session_token"] = auth[7:].strip()
            return gw.dispatch(payload)
        except json.JSONDecodeError:
            return {"jsonrpc": "2.0",
                    "error": {"code": -32700, "message": "Parse error: invalid JSON"},
                    "id": None}
        except Exception as exc:
            logger.error(f"[ASGI] RPC error: {exc}", exc_info=True)
            return {"jsonrpc": "2.0",
                    "error": {"code": -32603, "message": f"Internal error: {exc}"},
                    "id": None}

    app.add_api_route("/rpc",     _rpc_dispatch, methods=["POST"], summary="JSON-RPC 2.0 endpoint")
    app.add_api_route("/api/rpc", _rpc_dispatch, methods=["POST"], summary="JSON-RPC 2.0 endpoint (API path)")

    # ── MCP (Model Context Protocol) over HTTP — the remote LLM route (TRUST_NETWORK) ──
    # An anonymous caller is given a guest session (read-only); a Bearer akt: token acts with
    # that identity's scopes. The kernel is the capability gate. Session reuse via Mcp-Session-Id.
    async def _mcp_dispatch(request: fastapi_mod.Request) -> Any:
        from api.portals.mcp import mcp_http_process
        raw = await request.body()
        resp, status, headers = mcp_http_process(
            gw, raw,
            session_header=request.headers.get("Mcp-Session-Id", ""),
            auth_header=request.headers.get("Authorization", ""))
        return fastapi_mod.responses.JSONResponse(content=resp, status_code=status, headers=headers)

    app.add_api_route("/mcp",     _mcp_dispatch, methods=["POST"], summary="MCP endpoint (remote LLM route)")
    app.add_api_route("/api/mcp", _mcp_dispatch, methods=["POST"], summary="MCP endpoint (API path)")

    # SEO / permalink surface: clean atom URLs (/a/<slug>), robots.txt, sitemap.xml.
    # Registered before the static mounts so they win, and reserved in HostReroute
    # so they resolve identically on every domain (shared atom viewer).
    _root_dir = next((dp for mp, dp in (static_dirs or []) if mp == "/"), None)
    if _root_dir:
        _register_seo_routes(app, fastapi_mod, gw, os.path.abspath(_root_dir))

    # Static file serving — mounted after API routes so API always takes priority
    if static_dirs:
        try:
            from starlette.staticfiles import StaticFiles

            class _RevalidatingStatic(StaticFiles):
                """StaticFiles that tags HTML pages `Cache-Control: no-cache`.

                The archives tree is redeployed in place (seed overwrite). Without
                this, an HTML response carries only Last-Modified/ETag and browsers
                apply HEURISTIC freshness — serving a stale page for minutes/hours
                without revalidating, so a redeploy "doesn't show up". `no-cache`
                forces a conditional request every load (still cheap: 304 when
                unchanged), so a redeploy is reflected on the next reload. Hashed
                assets (js/css/images) keep normal caching — only HTML revalidates.
                """
                async def get_response(self, path, scope):
                    resp = await super().get_response(path, scope)
                    ctype = resp.headers.get("content-type", "")
                    if ctype.startswith("text/html") or str(path).endswith(".html"):
                        resp.headers["Cache-Control"] = "no-cache"
                    return resp

            for mount_path, dir_path in static_dirs:
                if os.path.isdir(dir_path):
                    name = f"static_{mount_path.strip('/').replace('/', '_') or 'root'}"
                    app.mount(mount_path, _RevalidatingStatic(directory=dir_path, html=True), name=name)
                    logger.info(f"[ASGI] Static: {mount_path!r} → {dir_path}")
                else:
                    logger.warning(f"[ASGI] Static dir not found, skipping: {dir_path}")
        except ImportError:
            logger.warning("[ASGI] starlette.staticfiles unavailable — static files not served")

    # Host-based document-root routing: front several domains/subdomains from
    # the one archives tree (apex → archives/, world.<base> → archives/world/, …).
    # Only engaged when there is a "/" archives root mount to remap into.
    app_to_run = app
    _root_dir = next((dp for mp, dp in (static_dirs or []) if mp == "/"), None)
    if _root_dir and os.path.isdir(_root_dir):
        app_to_run = HostReroute(app, os.path.abspath(_root_dir))
        logger.info(f"[ASGI] Host-based routing active over {_root_dir}")

    _scheme = "https" if (ssl_certfile and ssl_keyfile) else "http"
    logger.info(f"[ASGI] Binding portal on {host}:{port} ({_scheme})")
    try:
        _cfg_kwargs = dict(host=host, port=port, log_level="info")
        if ssl_certfile and ssl_keyfile:
            _cfg_kwargs["ssl_certfile"] = ssl_certfile
            _cfg_kwargs["ssl_keyfile"] = ssl_keyfile
        config = uvicorn_mod.Config(app_to_run, **_cfg_kwargs)
        server = uvicorn_mod.Server(config)
        # install_signal_handlers is only valid on the main thread;
        # uvicorn skips it automatically when called from a background thread,
        # but set it explicitly to avoid any version-dependent warnings.
        if _in_bg:
            config.install_signal_handlers = False
        server.run()
    except (KeyboardInterrupt, SystemExit):
        logger.info("[ASGI] Portal shut down.")
    except Exception as exc:
        logger.warning(f"[ASGI] Portal exited: {exc}")


def run_cgi(gw, original_stdout=None):
    """CGI handler for stateless traditional web servers (e.g., Apache)."""
    if original_stdout:
        sys.stdout = original_stdout

    print("Content-Type: application/json; charset=utf-8\n")

    if os.environ.get("REQUEST_METHOD") != "POST":
        print(json.dumps({"jsonrpc": "2.0",
                          "error": {"code": -32600, "message": "Only POST accepted"},
                          "id": None}))
        return

    try:
        body = sys.stdin.read()
        if not body:
            print(json.dumps({"jsonrpc": "2.0",
                              "error": {"code": -32600, "message": "Empty POST body"},
                              "id": None}))
            return
        resp = gw.dispatch(json.loads(body))
        print(json.dumps(resp, ensure_ascii=False))
    except json.JSONDecodeError:
        print(json.dumps({"jsonrpc": "2.0",
                          "error": {"code": -32700, "message": "Parse error"},
                          "id": None}))
    except Exception as exc:
        print(json.dumps({"jsonrpc": "2.0",
                          "error": {"code": -32603, "message": f"CGI error: {exc}"},
                          "id": None}))
