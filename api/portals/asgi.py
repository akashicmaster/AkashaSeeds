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
from lib.akasha.api import manifest as _manifest

logger = logging.getLogger("Harmonia.Portal.ASGI")

# Paths that are the shared backend/app, never a per-host document root — they
# must reach the API/RPC surface (or the shared atom viewer / SEO endpoints)
# regardless of which domain the browser came from.
_RESERVED_PREFIXES = ("/rpc", "/api/rpc", "/api/readme", "/health",
                      "/docs", "/redoc", "/openapi.json",
                      "/a", "/robots.txt", "/sitemap.xml", "/sitemap", "/pulse",
                      # A14 — the SHARED static mounts (their own StaticFiles mounts, NOT under the
                      # archives root): a per-host rewrite of these to /<host_dir>/… 404s them (the
                      # /a/<slug> template loads plotly from /lib). Reserve them so every host serves
                      # the one shared copy; the path-aware fallback below covers everything else.
                      "/lib") + tuple(sorted(_manifest.declared_static()))
# ↑ The package-declared mounts (`archives/MANIFEST.json` `static`) are reserved the same way —
# they are shared mounts of their own. The portal used to name `/cosmos`, `/word` and `/field` here
# AND in the launcher; a room is its package's business, so the package declares it (group 4, 4.9).


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
                        # A14 — PATH-AWARE: reroute to the host dir ONLY when the host actually HAS
                        # this path under archives/<host_dir>/ (its own index or asset); otherwise keep
                        # the ORIGINAL path so a shared mount (/lib, …) or the default root serves it.
                        # This is the docstring's "falls back to the default root" promise applied
                        # per-path — it fixes the /lib/*.js 404s and the favicon 404s on every host.
                        import os as _os
                        _host_fs = _os.path.join(self.archives_root, host_dir, path.lstrip("/"))
                        if path == "/" or _os.path.exists(_host_fs):
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

# ── A7 — reference letter-page cache (portal-side, one cache, several readers) ───────────────────
# The A–Z browse pages are RPC PROJECTIONS (archives.reference → thesaurus.op_reference), not atoms,
# so the semantic-plan warm loop (which pre-renders atom pages) never covers them — they stay the
# 4–13 s slow spot. The daemon's own reference cache is scope+scan-keyed with a 600 s TTL, SHORTER
# than the warm interval (900 s), so it goes cold between passes. This portal-side cache sits in FRONT
# of the daemon round-trip: keyed only by (method, initial, limit) for PUBLIC/guest reads (the glossary
# is public data — a guest `gbk:` token or an anonymous read see the identical result), TTL ≥ the warm
# interval so a warmed letter never expires before the next pass. Bounded + evict-oldest (R7). Readers:
# the warm loop's "routes" pass (populates a–z), the public /rpc letter-page dispatch, and the sitemap
# sweep — one cache, several readers.
_REFERENCE_CACHE = {}                                     # (method, initial, limit) -> (expires_at, result)
_REFERENCE_LOCK  = _threading.Lock()
_REFERENCE_MAX   = 128                                    # bounded population (a–z × a few shapes)
try:
    _REFERENCE_TTL = max(30.0, float(os.environ.get("AKASHA_REFERENCE_PAGE_TTL_S", "1800") or "1800"))
except (TypeError, ValueError):
    _REFERENCE_TTL = 1800.0
def _reference_methods() -> dict:
    """{method: projection spec} for every op that declares `"projection": {"reference": …}` — the
    public letter-page reads a portal may cache. Declared on the op (group 4, 4.7); the portal used
    to keep the two method names here."""
    return _manifest.declared_projection("reference")


def _reference_role(role: str) -> str:
    """The reference read that plays `role` — `letters` (the A–Z page, cached and warmed) or
    `glossary` (the salience-ordered list the sitemap sweeps) — or "" when none declares it."""
    return _manifest.declared_reference(role)


def _reference_default_limit(method: str, fallback: int = 100) -> int:
    spec = _reference_methods().get(method)
    try:
        return int((spec or {}).get("default_limit") or fallback) if isinstance(spec, dict) else fallback
    except (TypeError, ValueError):
        return fallback


def _reference_public_token(params) -> bool:
    """A reference read is portal-cacheable only for the PUBLIC glossary: an anonymous read (no token)
    or a guest `gbk:` token. An authenticated `akt:` session may see a different visibility-filtered
    result, so it bypasses the cache entirely (never reads or writes it) — no cross-scope leak."""
    if not isinstance(params, dict):
        return False
    tok = str(params.get("session_token") or "").strip()
    return tok == "" or tok.startswith("gbk:")


def _reference_cache_get(key):
    now = _time.time()
    with _REFERENCE_LOCK:
        ent = _REFERENCE_CACHE.get(key)
        if ent is not None:
            if ent[0] > now:
                return ent[1]
            _REFERENCE_CACHE.pop(key, None)               # expired — incremental evict, never clear-all
    return None


def _reference_cache_put(key, result):
    if not isinstance(result, dict):
        return
    now = _time.time()
    with _REFERENCE_LOCK:
        if key not in _REFERENCE_CACHE and len(_REFERENCE_CACHE) >= _REFERENCE_MAX:
            oldest = min(_REFERENCE_CACHE.items(), key=lambda kv: kv[1][0])[0]
            _REFERENCE_CACHE.pop(oldest, None)
        _REFERENCE_CACHE[key] = (now + _REFERENCE_TTL, result)


def _reference_fetch(gw, method, initial, limit, extra=None):
    """Serve one PUBLIC reference letter read from the shared portal cache (A7). On a miss, dispatch it
    as an anonymous guest (public scope), store the `result`, and return it. `extra` carries any extra
    dispatch params (e.g. the sitemap's order/scan) that do NOT enter the cache key — the key stays
    (method, initial, limit) per the order, so the warm loop and the letter page share one entry."""
    key = (method, str(initial or "").strip().lower(), int(limit))
    cached = _reference_cache_get(key)
    if cached is not None:
        return cached
    params = {"initial": initial, "limit": limit}          # FLAT params (same shape as the SPA / _guest_call)
    if extra:
        params.update(extra)
    try:
        # F58 1B — under the portal's guest identity, not anonymous (else refused on a versioned series).
        resp = _guest_dispatch(gw, method, params)
        result = (resp or {}).get("result") if isinstance(resp, dict) else None
    except Exception:
        result = None
    if isinstance(result, dict):
        _reference_cache_put(key, result)
        return result
    return None


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
    _glossary = _reference_role("glossary")
    if not _glossary:
        logger.info("[ASGI] sitemap core skipped: no op declares projection.reference role=glossary")
        return slugs
    try:
        res = _guest_call(gw, _glossary, {"limit": 500})
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
    _glossary = _reference_role("glossary")
    try:
        for ch in (_SITEMAP_ALPHA if _glossary else ()):
            res = _reference_fetch(gw, _glossary, ch, 1000,
                                   extra={"order": "alpha", "scan": 50000})   # A7 — shared cache
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

# ── SSR concurrency cap — crawl-storm load shedding ──────────────────────────────
# A web crawler (Meta/Bing/…) walks EVERY /a/<slug> page, each a cache-miss dive forwarded to the
# one daemon. Unbounded, tens of these run at once (starlette's ~40-thread pool), swamping the
# daemon so it misses health probes → respawn → the "warming up" flap under load. Cap the number of
# CONCURRENT SSR renders; when saturated, SHED to the cheap client-rendered shell (a valid 200 the
# JS still enhances — the same degrade-first path as a render miss) instead of piling another dive
# onto the daemon. So the daemon load from a crawl burst is bounded no matter how hard it is hit;
# SEO returns as soon as load subsides (served renders refill the HTML cache). Tunable via env.
#
# F47-1.3 — render concurrency defaults to 1: the measured GIL anti-scaling makes SERIAL the fastest
# (3 concurrent renders were 172 ms each / 18-per-s TOTAL vs 21 ms / 46-per-s at 1). The one slot is
# HUMAN-PRIORITY: a bot-class render only takes it when it is free AND no human is waiting, so a
# human is NEVER shed while a bot holds or is queued for the slot (the F47 invariant). Bots that
# cannot get the slot degrade to the snapshot / shell / 503; humans wait (bounded) for it.
_SSR_MAX_CONCURRENCY = max(1, int(os.environ.get("AKASHA_SSR_MAX_CONCURRENCY", "1")))
_SSR_SEM = {"sem": None}        # lazily-created asyncio.Semaphore (bound to the serving loop)
_HUMAN_WAITING = {"n": 0}       # humans currently waiting for / holding a render slot (loop-thread only)


def _ssr_semaphore():
    import asyncio
    s = _SSR_SEM["sem"]
    if s is None:
        s = _SSR_SEM["sem"] = asyncio.Semaphore(_SSR_MAX_CONCURRENCY)
    return s


async def _acquire_render(is_human: bool):
    """Human-priority admission to the single render slot. Returns True if the slot was acquired
    (caller MUST release it) or False if the caller should SHED (bot-class only). The event loop is
    single-threaded, so the _HUMAN_WAITING counter needs no lock. A human always waits for the slot
    and is counted as waiting so bots defer; a bot is admitted only when the slot is free AND no
    human is waiting — it is never allowed to make a human queue behind it."""
    sem = _ssr_semaphore()
    if is_human:
        _HUMAN_WAITING["n"] += 1
        try:
            await sem.acquire()
            return True
        finally:
            _HUMAN_WAITING["n"] -= 1
    # bot / crawler class: yield to any waiting human and never block on a taken slot
    if _HUMAN_WAITING["n"] > 0 or sem.locked():
        return False
    await sem.acquire()             # slot was free and no human waiting → take it non-blockingly
    return True


def _release_render():
    try:
        _ssr_semaphore().release()
    except (ValueError, RuntimeError):
        pass


# F39-P3 — per-IP rate limit on the RPC endpoint. A token bucket sheds an impolite crawler at the
# HTTP edge (before its request even reaches the kernel), complementing robots.txt Crawl-delay (which
# polite crawlers honour) and the P1a admission cap (which bounds the daemon once a request is in).
# Generous by default so real users are never hit — only a storm. Tunable AKASHA_RPC_RATE_PER_MIN
# (0 disables). X-Forwarded-For first hop is trusted when AKASHA_TRUST_XFF=1 (public deploy behind a
# proxy), else the socket peer. The bucket map is bounded (LRU-ish prune) so distinct IPs can't grow it.
class _IPRateLimiter:
    def __init__(self, per_min: int, max_ips: int = 8192):
        self.per_min = max(0, per_min)
        self.cap = float(max(1, per_min))
        self.refill = self.cap / 60.0
        self.max_ips = max_ips
        self._b = {}                                    # ip -> [tokens, last_ts]
        self._lock = _threading.Lock()

    def check(self, ip: str, now: float):
        """(True, 0) if allowed, else (False, retry_after_seconds). Disabled → always allowed."""
        if self.per_min <= 0 or not ip:
            return True, 0
        with self._lock:
            tok, last = self._b.get(ip, (self.cap, now))
            tok = min(self.cap, tok + (now - last) * self.refill)
            if tok >= 1.0:
                self._b[ip] = (tok - 1.0, now)
                ok, wait = True, 0
            else:
                self._b[ip] = (tok, now)
                ok, wait = False, max(1, int((1.0 - tok) / self.refill) + 1)
            if len(self._b) > self.max_ips:             # bound the map: drop the oldest-seen half
                for k in sorted(self._b, key=lambda kk: self._b[kk][1])[: self.max_ips // 2]:
                    self._b.pop(k, None)
            return ok, wait


_RPC_RATE_LIMITER = _IPRateLimiter(int(os.environ.get("AKASHA_RPC_RATE_PER_MIN", "120") or "120"))
# F47-5.1 — atom-page (/a) budget for the unverified `bot` class. Over this rate an IP is served
# SNAPSHOT-FIRST ONLY: a fresh snapshot if one exists, else the cheap shell — never a live render.
# So a single aggressive unverified crawler cannot keep triggering daemon renders. Humans and
# verified crawlers are unaffected (this limiter is consulted only on the bot branch).
_A_BOT_RATE_LIMITER = _IPRateLimiter(int(os.environ.get("AKASHA_A_BOT_RATE_PER_MIN", "30") or "30"))


def _client_ip(request) -> str:
    """The requester's IP: the first X-Forwarded-For hop when AKASHA_TRUST_XFF=1 (behind a proxy),
    else the socket peer. XFF is client-spoofable when NOT behind a trusted proxy, so it is opt-in."""
    if os.environ.get("AKASHA_TRUST_XFF", "1").strip().lower() in ("1", "yes", "true", "on"):
        xff = request.headers.get("X-Forwarded-For", "")
        if xff:
            return xff.split(",")[0].strip()
    try:
        return request.client.host if request.client else ""
    except Exception:
        return ""

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


_SITE_CACHE: dict = {}


def _site_json(path: str) -> dict:
    try:
        st = os.stat(path)
    except OSError:
        return {}
    hit = _SITE_CACHE.get(path)
    if hit and hit[0] == st.st_mtime_ns:
        return hit[1]
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}
    _SITE_CACHE[path] = (st.st_mtime_ns, data if isinstance(data, dict) else {})
    return _SITE_CACHE[path][1]


def _site(host: str) -> dict:
    """What a site calls itself — from the pages root's `site.json` (group 4, 4.7). Most specific
    first: `<pages>/<host>/site.json` for a host with its own directory, then a `hosts` entry of the root
    file (a host that EQUALS the key or ends with `.<key>`), then the root `name`. The portal used to
    answer with a substring test on the host (`if "kitchen" in h`)."""
    from lib.akasha.api import reserved as _reserved
    root = _reserved.root("pages")
    h = (host or "").lower().split(":", 1)[0].strip(".")
    base = _site_json(os.path.join(root, "site.json"))
    out = {"name": str(base.get("name") or "Akasha")}
    if base.get("term_set"):
        out["term_set"] = str(base["term_set"])
    for key, entry in sorted((base.get("hosts") or {}).items()):
        if key.startswith("_") or not isinstance(entry, dict):
            continue
        if h == key or h.endswith("." + key):
            out.update({k: str(v) for k, v in entry.items() if not k.startswith("_")})
    if h and os.path.isdir(root):
        for d in sorted(os.listdir(root)):
            if (h == d or h.endswith("." + d)) and os.path.isfile(os.path.join(root, d, "site.json")):
                own = _site_json(os.path.join(root, d, "site.json"))
                out.update({k: str(v) for k, v in own.items() if not k.startswith("_")
                            and isinstance(v, (str, int, float))})
    return out


def _site_name(host: str) -> str:
    return _site(host).get("name") or "Akasha"


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


def _guest_dispatch(gw, method: str, params: dict):
    """F58 1B — dispatch a portal-internal READ under the portal's OWN GUEST identity (a `gbk:` token),
    returning the FULL JSON-RPC response (so the caller can read result AND error). A tokenless
    ('anonymous') dispatch is granted guest by the writer ONLY when the series is EXACTLY 'thesaurus'
    (identity.py) — on a versioned series like 'thesaurus09n' every anonymous read is REFUSED (-32001),
    which is what silently killed the warm loop and the sitemap sweep. A minted guest token is granted
    regardless of the series name. Retries once with a fresh token if the pool reclaimed it mid-flight."""
    def _call(tok):
        p = dict(params); p["session_token"] = tok
        return gw.dispatch({"jsonrpc": "2.0", "method": method, "params": p, "id": "pg"}) or {}
    tok = _ssr_guest_token(gw)
    if not tok:
        return {"error": {"code": -32001, "message": "portal could not mint a guest token"}}
    resp = _call(tok)
    if isinstance(resp, dict) and resp.get("error"):      # reclaimed / rejected token → one fresh retry
        tok2 = _ssr_guest_token(gw, force=True)
        if tok2:
            resp = _call(tok2)
    return resp


def _ssr_fetch_concept(gw, slug: str):
    """Guest-scoped read of one concept (public-only), through the op that implements
    `render_concept`; returns the raw result dict or None (miss/private/slow/undeclared).

    Bounded by _SSR_FETCH_TIMEOUT: a slow hub atom must not hold the HTTP response open —
    on timeout we return None so the caller serves the shell (client renders instead)."""
    ex = _SSR_POOL["ex"]
    if ex is None:
        import concurrent.futures as _cf
        ex = _SSR_POOL["ex"] = _cf.ThreadPoolExecutor(max_workers=4, thread_name_prefix="ssr")
    import concurrent.futures as _cf
    # The one-concept render is whatever op IMPLEMENTS `render_concept` (group 4) — the portal does
    # not name it. None declared → no server-side prerender; the shell renders client-side.
    render = _manifest.declared_implementer("render_concept")
    if not render:
        return None
    try:
        return ex.submit(_guest_call, gw, render, {"name": slug}).result(
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
        "term_set":       _site(host).get("term_set") or _site_name(host),
        # F47-2.1 — a budget-truncated render is a SERVICE state, not the data: carry it through so
        # the page marks itself "partial" and the caller never persists it as a canonical snapshot.
        "truncated":      bool(concept.get("truncated") or payload.get("truncated")),
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
                             "name": fields.get("term_set") or fields["site_name"],
                             "url": origin + "/"},
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


# F47-2.1 — a machine marker the caller checks to avoid persisting a partial render as a snapshot.
_SSR_TRUNCATED_MARKER = "<!-- AKASHA:TRUNCATED -->"


def _ssr_build_body(fields: dict) -> str:
    """§1b — the prerendered, crawlable content body (fills #info-inner)."""
    out = [f'<h1 class="word-display-name">{_e(fields["headword"])}</h1>']
    if fields.get("truncated"):
        # Honest copy: the neighbourhood is partial because the render ran out of time budget, NOT
        # because the concept is small. A machine marker rides along so we never cache this as canon.
        out.append(_SSR_TRUNCATED_MARKER)
        out.append('<p class="partial-view" role="status">Partial view — '
                   '<a href="" onclick="location.reload();return false">reload for the full page</a>.</p>')
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


def _atom_html_cache_get(host: str, slug: str, allow_stale: bool = False):
    """Fresh L1 HTML for (host, slug), or None. F48-A 1.7 — with allow_stale, also return an EXPIRED
    entry as (html, age_seconds): a stale L1 entry is always a COMPLETE page (a truncated render is
    never cached), so serving it while a fresh render happens in the background is honest and fast."""
    now = _time.time()
    with _ATOM_HTML_LOCK:
        v = _ATOM_HTML_CACHE.get((host, slug))
        if not v:
            return None
        age = now - v[1]
        if age < _ATOM_HTML_TTL:
            return (v[0], 0.0) if allow_stale else v[0]
        if allow_stale:
            return (v[0], age)               # expired but complete → caller may serve + revalidate
    return None


def _atom_html_cache_put(host: str, slug: str, html: str) -> None:
    now = _time.time()
    with _ATOM_HTML_LOCK:
        if len(_ATOM_HTML_CACHE) >= _ATOM_HTML_MAX:
            # F48-A 1.6 — evict OLDEST-first (LRU by insert/refresh time), never clear-all. A
            # clear-all under a crawl that exceeds 2048 slugs cold-starts EVERY page at once — a
            # self-inflicted render stampede on the daemon. Drop ~10% of the oldest entries instead.
            _drop = max(1, _ATOM_HTML_MAX // 10)
            for _k in sorted(_ATOM_HTML_CACHE, key=lambda kk: _ATOM_HTML_CACHE[kk][1])[:_drop]:
                _ATOM_HTML_CACHE.pop(_k, None)
        _ATOM_HTML_CACHE[(host, slug)] = (html, now)


# F48-A 1.7 — at most ONE background revalidation per (host, slug) in flight, so a stale-entry storm
# does not fan out into a render stampede (the very thing 1.6 avoids on eviction).
_BG_REFRESH_INFLIGHT = set()
_BG_REFRESH_LOCK = _threading.Lock()


def _bg_refresh_claim(host: str, slug: str) -> bool:
    with _BG_REFRESH_LOCK:
        k = (host, slug)
        if k in _BG_REFRESH_INFLIGHT:
            return False
        _BG_REFRESH_INFLIGHT.add(k)
        return True


def _bg_refresh_release(host: str, slug: str) -> None:
    with _BG_REFRESH_LOCK:
        _BG_REFRESH_INFLIGHT.discard((host, slug))


# ── F44 Part B — the public tier: bots off the engine, SEO kept ───────────────────
# Two products from one store. A verified crawler (and, as a bonus, anonymous first-paint) is served
# a MATERIALIZED presentation projection — static HTML persisted to disk and served WITHOUT touching
# the cell daemon. This is not the store-path caching F33 bans: it is an Operand→artifact projection,
# regenerated when the underlying render changes or a TTL lapses. The live app stays behind the
# admission semaphore for interactive humans, who — freed of the bot majority — should rarely queue.
#
# B1 classification, B2 disk snapshot store, B4 correct status codes, B5 per-class accounting. The
# functions are pure/injectable so test/public_tier_eval.py can exercise them with no live daemon.

# Known verified-crawler UA tokens → the rDNS suffixes their PTR must forward-confirm to. A match on
# the UA alone is class `bot`; a UA match PLUS a forward-confirmed PTR is class `crawler` (served ONLY
# from snapshots, zero daemon RPCs). Everything else is `human` (the live path).
_CRAWLER_RDNS = {
    "googlebot":   (".googlebot.com", ".google.com"),
    "bingbot":     (".search.msn.com",),
    "adidxbot":    (".search.msn.com",),
    "yandex":      (".yandex.ru", ".yandex.net", ".yandex.com"),
    "duckduckbot": (".duckduckgo.com",),
    "baiduspider": (".baidu.com", ".baidu.jp"),
    "applebot":    (".applebot.apple.com",),
}
# UA substrings that mark an automated client even when we cannot forward-confirm (social unfurlers,
# LLM fetchers, generic libraries). These are class `bot`: rate-limited, never given a 503, but also
# not counted as human. Kept broad on purpose — misclassifying a human as a bot only means they get
# the (identical) static snapshot instead of the live shell, never a denial.
_BOT_UA_HINTS = ("bot", "spider", "crawler", "slurp", "crawl", "facebookexternalhit", "embedly",
                 "quora link preview", "bitlybot", "python-requests", "curl/", "wget/", "httpx",
                 "aiohttp", "go-http-client", "java/", "scrapy", "gptbot", "claudebot", "ccbot",
                 "amazonbot", "petalbot", "semrush", "ahrefs", "dotbot", "mj12bot", "bytespider")

_RDNS_CACHE = {}                     # ip -> (verified_bool, ts)
_RDNS_LOCK = _threading.Lock()
_RDNS_TTL = 3600.0

# Visitor-classes spec — the upgrade ladder passerby → human visitor. An IP that PROVES humanity
# (fires the /pulse beacon, which only a real browser running JS does; or shows human-scale
# interaction) is remembered here with a TTL, and reclassified `human`. Generous by design: the cost
# of serving a scraper one live render is trivial; the cost of degrading a potential resident is a
# lost resident. Bounded + in-memory (never stored, never PII) — a classification hint, not a record.
_HUMAN_IPS = {}                      # ip -> last_proof_ts
_HUMAN_LOCK = _threading.Lock()
_HUMAN_TTL = float(os.environ.get("AKASHA_HUMAN_TTL_S", "1800") or "1800")
_HUMAN_MAX = 16384


def _mark_human(ip: str) -> None:
    """Record that this IP behaved like a human (fired the JS beacon). Bounded + TTL'd."""
    if not ip:
        return
    now = _time.time()
    with _HUMAN_LOCK:
        _HUMAN_IPS[ip] = now
        if len(_HUMAN_IPS) > _HUMAN_MAX:                 # drop the oldest-seen half
            for k in sorted(_HUMAN_IPS, key=lambda kk: _HUMAN_IPS[kk])[: _HUMAN_MAX // 2]:
                _HUMAN_IPS.pop(k, None)


def _is_proven_human(ip: str) -> bool:
    if not ip:
        return False
    with _HUMAN_LOCK:
        ts = _HUMAN_IPS.get(ip)
    return bool(ts) and (_time.time() - ts) < _HUMAN_TTL


def _rdns_verify(ip: str, suffixes, resolver=None):
    """Forward-confirmed reverse DNS: PTR(ip) ends with an allowed suffix AND that name resolves
    back to `ip`. Cached per IP. `resolver` is injectable ((kind, arg) -> value) for tests; in
    production it uses stdlib socket with a short timeout. Any failure → False (treated as unverified,
    NOT crawler) — we never upgrade trust on a lookup error."""
    if not ip or not suffixes:
        return False
    now = _time.time()
    with _RDNS_LOCK:
        v = _RDNS_CACHE.get(ip)
        if v and (now - v[1]) < _RDNS_TTL:
            return v[0]
    ok = False
    try:
        import socket as _socket
        _old = _socket.getdefaulttimeout()
        _socket.setdefaulttimeout(float(os.environ.get("AKASHA_RDNS_TIMEOUT", "2")))
        try:
            if resolver is not None:
                host = resolver("ptr", ip)
                fwd = resolver("fwd", host) if host else []
            else:
                host = _socket.gethostbyaddr(ip)[0]
                fwd = []
                if host:
                    try:
                        fwd = [ai[4][0] for ai in _socket.getaddrinfo(host, None)]
                    except Exception:
                        fwd = []
            host_l = (host or "").lower().rstrip(".")
            if host_l and any(host_l.endswith(sfx) for sfx in suffixes) and ip in set(fwd):
                ok = True
        finally:
            _socket.setdefaulttimeout(_old)
    except Exception:
        ok = False
    with _RDNS_LOCK:
        if len(_RDNS_CACHE) > 8192:
            _RDNS_CACHE.clear()
        _RDNS_CACHE[ip] = (ok, now)
    return ok


def _classify_client(ua: str, ip: str, resolver=None):
    """Visitor-classes spec — classify a request into 'crawler' (verified search bot), 'human'
    (a real browser / a proven-human IP), or 'passerby' (automated-but-unverified, or an odd client
    yet to prove humanity). Returns {'class', 'verified', 'token'}. A claimed crawler is always
    rDNS-verified (the switch that skipped it is deleted — the purge order §4.5)."""
    ual = (ua or "").lower()
    for tok, suffixes in _CRAWLER_RDNS.items():
        if tok in ual:
            if _rdns_verify(ip, suffixes, resolver=resolver):
                return {"class": "crawler", "verified": True, "token": tok}
            # UA claims a search bot but PTR does not confirm → an impostor / unverifiable: a rate-
            # limited PASSERBY, never a trusted crawler (no 503 privilege, no snapshot-only fast lane).
            return {"class": "passerby", "verified": False, "token": tok}
    # An IP that already proved humanity (fired the beacon) is a human visitor regardless of UA.
    if _is_proven_human(ip):
        return {"class": "human", "verified": True, "token": ""}
    # An automated/library/impostor UA that has NOT proved humanity is a passerby (cheap, rate-
    # limited, snapshot-first; its upgrade path stays open — the beacon rides every rendered page).
    if any(h in ual for h in _BOT_UA_HINTS):
        return {"class": "passerby", "verified": False, "token": ""}
    # A bare browser UA is served GENEROUSLY as a human visitor (the spec's generosity: never degrade
    # a potential resident). The beacon then confirms it, pinning the class for subsequent pages.
    return {"class": "human", "verified": False, "token": ""}


# B2 — the on-disk snapshot store. One static HTML per (host, canonical slug); survives a portal
# respawn (unlike the in-RAM L1 cache), so a crawl storm after every ~15-min redeploy is served from
# disk, not by re-diving the daemon. Atomic write (tmp+rename); TTL default 7 days.
def _snapshot_dir():
    return os.environ.get("AKASHA_SNAPSHOT_DIR", "").strip() or os.path.join(
        __import__("lib.akasha.api.reserved", fromlist=["root"]).root("pages"), "snapshots")


def _snapshot_ttl():
    try:
        return max(0.0, float(os.environ.get("AKASHA_SNAPSHOT_TTL_DAYS", "7"))) * 86400.0
    except (TypeError, ValueError):
        return 7 * 86400.0


def _snapshot_path(host: str, slug: str):
    """A safe, collision-resistant path under the snapshot dir, partitioned by host so each domain
    keeps its own same-origin snapshots. The slug is hashed (aliases contain ':' and '/'), keeping a
    short readable prefix for eyeballing the directory."""
    import hashlib as _hl
    h = (host or "_").split(":")[0].lower() or "_"
    h = _re.sub(r"[^a-z0-9._-]", "_", h)[:60] or "_"
    digest = _hl.sha1(("%s\n%s" % (h, slug)).encode("utf-8")).hexdigest()[:24]
    prefix = _re.sub(r"[^a-zA-Z0-9]", "-", slug)[:40].strip("-") or "atom"
    return os.path.join(_snapshot_dir(), h, "%s.%s.html" % (prefix, digest))


def _snapshot_read(host: str, slug: str, ttl=None):
    """Fresh snapshot HTML (< TTL old) or None. Never raises."""
    ttl = _snapshot_ttl() if ttl is None else ttl
    path = _snapshot_path(host, slug)
    try:
        st = os.stat(path)
    except OSError:
        return None
    if ttl and (_time.time() - st.st_mtime) >= ttl:
        return None                                     # stale — caller regenerates
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except OSError:
        return None


def _html_truncated(html: str) -> bool:
    """True if a rendered page carries the budget-truncation marker (F47-2.1) — such a page is
    served (marked 'partial') but never cached or persisted as a canonical snapshot."""
    return bool(html) and _SSR_TRUNCATED_MARKER in html


def _snapshot_write(host: str, slug: str, html: str) -> bool:
    """Persist a rendered snapshot atomically (tmp + rename). Best-effort; never raises."""
    if not html:
        return False
    path = _snapshot_path(host, slug)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = "%s.%d.tmp" % (path, os.getpid())
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(html)
        os.replace(tmp, path)
        return True
    except OSError as exc:
        logger.debug("[ASGI] snapshot write failed for %r: %s", slug, exc)
        try:
            os.remove(tmp)
        except OSError:
            pass
        return False


# B5 — per-class accounting. Bounded, lock-guarded; a periodic summary line names the traffic mix and
# where each class was served (snapshot / live / shed / 503 / 429), so the admission -32029 story and
# the bot majority are finally visible in the log instead of nowhere.
import contextvars as _contextvars
from collections import deque as _deque

_CLASS_STATS = {}
_CLASS_TIMES = {}                                  # cls -> deque of recent serve-times (ms) — F47-5.3
_CLASS_LOCK = _threading.Lock()
_CLASS_LOG = {"ts": 0.0}
_CLASS_LOG_EVERY = float(os.environ.get("AKASHA_CLASS_LOG_EVERY_S", "60") or "60")
_CLASS_TIMES_MAX = 1024
# Semantic macro-cache render-warm counters (F57 §1) — module-level so both the warm loop (defined in
# the app factory) and the periodic PublicTier line (module-level `_maybe_log_class_stats`) read them.
# `warmed` = lifetime pages warmed; `plan` = last observed plan size; `last_error` = sticky last cause.
_SEMCACHE_WARM = {"warmed": 0, "last": 0.0, "plan": 0, "last_error": None, "routes": 0}
# F60 §5.4 — when the live gateway became ready (the holder swap / direct-run startup), so the warm
# loop can log how long after 'ready' it actually started (after_ready≈0–5 s proves §5's fix worked).
_PORTAL_READY = {"at": 0.0}
# Per-request wall-clock start (set at the top of the /a handler); _class_note reads it to record the
# serve time for the p50/p95 scoreboard. A ContextVar is per-asyncio-task, so concurrent requests
# never cross-contaminate.
_REQ_START = _contextvars.ContextVar("akasha_req_start", default=None)


def _class_note(cls: str, outcome: str) -> None:
    t0 = _REQ_START.get()
    ms = ((_time.time() - t0) * 1000.0) if t0 else None
    with _CLASS_LOCK:
        d = _CLASS_STATS.setdefault(cls, {})
        d[outcome] = d.get(outcome, 0) + 1
        d["total"] = d.get("total", 0) + 1
        if ms is not None:
            dq = _CLASS_TIMES.get(cls)
            if dq is None:
                dq = _CLASS_TIMES[cls] = _deque(maxlen=_CLASS_TIMES_MAX)
            dq.append(ms)


def _pctile(vals, p):
    """The p-th percentile (0..100) of a list of serve-times, or None if empty. Nearest-rank."""
    if not vals:
        return None
    s = sorted(vals)
    idx = min(len(s) - 1, max(0, int(round((p / 100.0) * len(s) + 0.5)) - 1))
    return s[idx]


def _class_stats_snapshot():
    with _CLASS_LOCK:
        return {k: dict(v) for k, v in _CLASS_STATS.items()}


def _maybe_log_class_stats() -> None:
    now = _time.time()
    if now - _CLASS_LOG["ts"] < _CLASS_LOG_EVERY:
        return
    _CLASS_LOG["ts"] = now
    snap = _class_stats_snapshot()
    with _CLASS_LOCK:
        times = {c: list(dq) for c, dq in _CLASS_TIMES.items()}
    if snap:
        parts = []
        for cls in ("human", "crawler", "passerby"):
            d = snap.get(cls)
            if d:
                outs = " ".join("%s=%d" % (k, v) for k, v in sorted(d.items()) if k != "total")
                tv = times.get(cls) or []
                p50, p95 = _pctile(tv, 50), _pctile(tv, 95)
                speed = (" p50=%dms p95=%dms" % (p50, p95)) if p50 is not None else ""
                parts.append("%s(total=%d %s%s)" % (cls, d.get("total", 0), outs, speed))
        if parts:
            # F57 §1.4 — the semantic-cache warm progress rides the same periodic line as the class mix.
            # A17 — report PRESENT entries (warmed + already-warm this pass), so a post-restart cache
            # that is fully warm via surviving snapshots reads warm=N/N, not warm=0/N.
            warm = "warm=%d/%d" % (_SEMCACHE_WARM.get("present", _SEMCACHE_WARM.get("warmed", 0)),
                                   _SEMCACHE_WARM.get("plan", 0))
            logger.info("[PublicTier] class mix — %s  %s", "  ".join(parts), warm)


def _register_seo_routes(app, fastapi_mod, gw, root_dir):
    """Clean permalinks + crawlability, all client-rendered (same as word page):
      GET /a/<slug>     → serve the shared atom viewer (word/index.html)
      GET /robots.txt   → allow all + point to this host's sitemap
      GET /sitemap.xml  → same-origin URLs for the salient atoms
    """
    from starlette.responses import (FileResponse, PlainTextResponse, Response,
                                      HTMLResponse)
    from starlette.concurrency import run_in_threadpool   # F14b — keep the event loop free

    word_index = os.path.join(root_dir, "word", "index.html")

    async def _revalidate(slug: str, host: str, origin: str) -> None:
        """F48-A 1.7 — background re-render that refreshes a stale L1 entry (and its snapshot). Runs
        as a BOT on the human-priority render gate, so it never preempts a live human; at most one per
        (host, slug). Fire-and-forget: any failure leaves the stale-but-complete entry in place."""
        if not _bg_refresh_claim(host, slug):
            return
        try:
            if not await _acquire_render(is_human=False):
                return                                 # slot busy → skip; the stale entry stands
            try:
                html = await run_in_threadpool(_render_atom_html, gw, _read_template(word_index),
                                               slug, origin, host)
            finally:
                _release_render()
            if html and not _html_truncated(html):
                _atom_html_cache_put(host, slug, html)
                await run_in_threadpool(_snapshot_write, host, slug, html)
        except Exception as _rex:
            logger.debug("[ASGI] background revalidate failed for %r: %s", slug, _rex)
        finally:
            _bg_refresh_release(host, slug)

    # ── Semantic macro-cache — render pre-materialization (design §4a, Phase 1) ──────────
    # The writer daemon authors the plan (set:stage:cache_plan via cache.replan); THIS portal warms
    # it. For each plan member, pre-render its page into the snapshot store + L1 so the featured
    # material is hot from second zero of every portal generation (a respawn becomes invisible for the
    # demo surface). Uses only landed machinery — this is literally `_revalidate` driven by the plan
    # set instead of a stale-cache hit. Bounded: LOW-priority renders that always yield to a human
    # (the render gate), paced (≈1 page / pace seconds), skips members already warm. Active only when
    # the plan is non-empty (⇒ a curated deployment); a personal cell never warms. Host-partitioned:
    # set AKASHA_SEMCACHE_HOST to the canonical public host so warmed snapshots/L1 match request
    # partitions.
    # Counters live at module scope (_SEMCACHE_WARM) so the PublicTier line can read them (F57 §1.4).

    async def _semcache_warm_loop() -> None:
        import asyncio as _aio
        host = os.environ.get("AKASHA_SEMCACHE_HOST", "")
        origin = os.environ.get("AKASHA_SEMCACHE_ORIGIN", "")
        try:
            pace = max(0.1, float(os.environ.get("AKASHA_SEMCACHE_WARM_PACE_S", "1.0")))
            interval = max(30.0, float(os.environ.get("AKASHA_SEMCACHE_WARM_INTERVAL_S", "900")))
        except (TypeError, ValueError):
            pace, interval = 1.0, 900.0
        # F58 §0 / F60 §5.4 — prove the loop actually STARTED, and how long after the gateway became
        # ready (after_ready≈0–5 s confirms §5's HostReroute-unwrap + first-request start worked; a
        # large value or a missing line means it is still not starting).
        _ar = (_time.time() - _PORTAL_READY["at"]) if _PORTAL_READY.get("at") else -1.0
        logger.info("[semcache.warm] started — pace=%.1fs interval=%.0fs after_ready=%.1fs",
                    pace, interval, _ar)
        await _aio.sleep(20)                                # let boot settle before spending render slots
        while True:
            warmed_pass = skipped_pass = errors_pass = routes_pass = 0   # per-pass counters (INFO line)
            err_samples = []
            try:
                # F58 1B — under the portal's guest identity, never anonymous (a versioned series
                # refuses an unknown 'anonymous' id → the loop was refused every pass).
                resp = await run_in_threadpool(_guest_dispatch, gw, "cache.plan",
                                               {"data": {"slugs": "1"}})   # guest read — the plan is public
                rerr = (resp or {}).get("error")
                if rerr:                                     # §1.2 — the plan dispatch itself failed
                    msg = ("%s %s" % (rerr.get("code"), rerr.get("message"))
                           if isinstance(rerr, dict) else str(rerr))
                    _SEMCACHE_WARM["last_error"] = msg
                    logger.warning("[semcache.warm] plan unavailable: %s", msg)
                    slugs = []
                else:
                    result = (resp or {}).get("result") or {}
                    slugs = result.get("slugs") or []
                    _SEMCACHE_WARM["plan"] = int(result.get("atoms") or len(slugs))
                    if not slugs:                            # §1.2 — empty plan while the daemon claims one
                        try:
                            st = await run_in_threadpool(_guest_dispatch, gw, "cache.stat", {"data": {}})
                            dplan = int(((st or {}).get("result") or {}).get("plan") or 0)
                        except Exception:
                            dplan = 0
                        if dplan > 0:
                            _SEMCACHE_WARM["last_error"] = "empty plan (daemon reports plan=%d)" % dplan
                            logger.warning("[semcache.warm] plan unavailable: empty plan "
                                           "(daemon reports plan=%d)", dplan)
                for slug in slugs:
                    if not slug:
                        continue
                    if _snapshot_read(host, slug) is not None or _atom_html_cache_get(host, slug) is not None:
                        skipped_pass += 1                   # already warm — skip (diff, never re-warm all)
                        continue
                    if not await _acquire_render(is_human=False):
                        await _aio.sleep(pace)              # slot busy (a human) → yield
                        continue
                    try:
                        html = await run_in_threadpool(_render_atom_html, gw,
                                                       _read_template(word_index), slug, origin, host)
                        if html and not _html_truncated(html):
                            _atom_html_cache_put(host, slug, html)
                            await run_in_threadpool(_snapshot_write, host, slug, html)
                            _SEMCACHE_WARM["warmed"] += 1
                            warmed_pass += 1
                        else:                               # §1.3 — render returned None/truncated
                            errors_pass += 1
                            _SEMCACHE_WARM["last_error"] = "%s: no usable HTML (None/truncated)" % slug
                            if len(err_samples) < 3:
                                err_samples.append(slug)
                                logger.info("[semcache.warm] render produced no usable HTML for %r "
                                            "(None or truncated)", slug)
                    except Exception as _sx:                # §1.3 — render/snapshot-write raised
                        errors_pass += 1
                        _SEMCACHE_WARM["last_error"] = "%s: %s" % (slug, _sx)
                        if len(err_samples) < 3:
                            err_samples.append(slug)
                            logger.info("[semcache.warm] warm failed for %r: %s", slug, _sx)
                    finally:
                        _release_render()
                    await _aio.sleep(pace)                  # budget: ≈ one page per `pace` seconds
                # A7 — second warm target class: the A–Z reference letter pages. They are RPC
                # projections (archives.reference → thesaurus.op_reference), not atoms, so no plan
                # member covers them and they stay the demo's slow spot. Populate the shared portal
                # reference cache (TTL ≥ interval) so a live letter read is served WITHOUT the daemon
                # round-trip; skip a letter still warm (diff, never re-warm all). Paced + guest read.
                _letters = _reference_role("letters")
                for ch in (_SITEMAP_ALPHA if _letters else ()):
                    if _reference_cache_get((_letters, ch, 1000)) is not None:
                        continue
                    try:
                        _rr = await run_in_threadpool(_reference_fetch, gw,
                                                      _letters, ch, 1000)
                        if isinstance(_rr, dict):
                            routes_pass += 1
                    except Exception as _rex:
                        _SEMCACHE_WARM["last_error"] = "route %s: %s" % (ch, _rex)
                        if len(err_samples) < 3:
                            logger.info("[semcache.warm] route %s warm failed: %s", ch, _rex)
                    await _aio.sleep(pace)
                _SEMCACHE_WARM["routes"] = routes_pass
                _SEMCACHE_WARM["last"] = _time.time()
                if not rerr and errors_pass == 0:           # a fully clean pass clears the sticky error
                    _SEMCACHE_WARM["last_error"] = None
            except Exception as _wex:
                errors_pass += 1
                _SEMCACHE_WARM["last_error"] = str(_wex)
                logger.warning("[semcache.warm] pass failed: %s", _wex)
            # A17 — the PRESENT count (warmed this pass + already-warm skipped this pass) is what the
            # cache actually holds; snapshots survive a restart, so after a reboot warmed_pass=0 but
            # skipped_pass=plan and the cache IS fully warm. PublicTier reports `warm=<present>/<plan>`;
            # `total_warmed` (lifetime renders this process) stays a separate, honest counter.
            _SEMCACHE_WARM["present"] = warmed_pass + skipped_pass
            # §1.1 / A7 — one INFO line EVERY pass, unconditionally (even an empty/failed plan).
            logger.info("[semcache.warm] plan=%d present=%d warmed=%d skipped_warm=%d errors=%d "
                        "routes=%d total_warmed=%d last_error=%s", _SEMCACHE_WARM.get("plan", 0),
                        _SEMCACHE_WARM.get("present", 0), warmed_pass, skipped_pass, errors_pass,
                        routes_pass, _SEMCACHE_WARM.get("warmed", 0),
                        _SEMCACHE_WARM.get("last_error") or "-")
            await _aio.sleep(interval)                      # re-warm periodically (picks up plan diffs)

    # F58 §0 (A6) — DO NOT start the warm loop from @app.on_event("startup"): under Lever C the
    # port is bound by a warming holder that answers the ASGI `lifespan` protocol itself, then swaps
    # in this real app on a later request — so this app's lifespan startup NEVER runs and the task
    # never scheduled (4.85 h of warm=0/0). Instead register it as a DEFERRED startup that the holder
    # swap schedules on the captured uvicorn loop (see run_server_warming / _start_deferred_startups).
    # Lifespan-dependent init is banned in _build_app for exactly this reason.
    _deferred = getattr(app.state, "deferred_startups", None)
    if _deferred is None:
        _deferred = []
        app.state.deferred_startups = _deferred
    _deferred.append(_semcache_warm_loop)

    # ── Phase 1.5 — focal-membrane demand staging (design §11) ─────────────────────────────────
    # When a HUMAN dives to an atom, pre-warm the semantically connected neighbourhood they are likely
    # to traverse next: cache.stage (a guest read) computes a BOUNDED membrane (top-K depth-1 closure),
    # and this portal warms those pages the same way the static plan is warmed — LOW priority, yields to
    # a human, rate-capped per minute. The dynamic population's death is the warm cache's own TTL/LRU
    # (≈ a visitor session), NOT a nucleus write. Triggered on HUMAN dives ONLY (a bot sweep follows no
    # locality and must never spend staging budget — design §11.3).
    _SEMCACHE_STAGE = {"membranes": 0, "warmed": 0, "min_epoch": 0, "min_count": 0}
    _STAGE_RECENT: "dict[str, float]" = {}          # focal → last-staged ts (per-focal cooldown; bounded)

    def _stage_cap_per_min() -> int:
        try:
            return max(1, int(os.environ.get("AKASHA_SEMCACHE_STAGE_RENDERS_PER_MIN", "60")))
        except (TypeError, ValueError):
            return 60

    def _stage_minute_ok() -> bool:
        """Per-minute render budget (§11.3 'cap staging renders per minute'). Rolls the window."""
        ep = int(_time.time() // 60)
        if ep != _SEMCACHE_STAGE["min_epoch"]:
            _SEMCACHE_STAGE["min_epoch"] = ep
            _SEMCACHE_STAGE["min_count"] = 0
        return _SEMCACHE_STAGE["min_count"] < _stage_cap_per_min()

    def _stage_on_human_dive(slug: str, host: str, origin: str) -> None:
        """Sync trigger fired from the route for a HUMAN dive: dedupe (per-focal cooldown), respect the
        per-minute cap, then schedule the background staging. Fire-and-forget — never blocks the serve."""
        if not slug:
            return
        now = _time.time()
        cooldown = 300.0
        last = _STAGE_RECENT.get(slug)
        if last is not None and (now - last) < cooldown:
            return                                  # same focal staged recently — don't re-stage
        if not _stage_minute_ok():
            return                                  # over the per-minute render budget this minute
        _STAGE_RECENT[slug] = now
        if len(_STAGE_RECENT) > 2048:               # bound the cooldown map (memory-discipline R2/R3)
            for _k in [k for k, t in _STAGE_RECENT.items() if (now - t) > cooldown][:1024]:
                _STAGE_RECENT.pop(_k, None)
            if len(_STAGE_RECENT) > 2048:           # still over ⇒ drop the oldest half
                for _k in sorted(_STAGE_RECENT, key=_STAGE_RECENT.get)[:1024]:
                    _STAGE_RECENT.pop(_k, None)
        import asyncio as _aio
        try:
            _aio.get_event_loop().create_task(_stage_membrane(slug, host, origin))
        except Exception:
            pass

    async def _stage_membrane(focal: str, host: str, origin: str) -> None:
        import asyncio as _aio
        try:
            # A15 — under the portal's guest identity, not anonymous (a versioned series refuses an
            # unknown 'anonymous' id, so the stager was refused every human dive). guest read — computes,
            # writes nothing. This also switches Phase 1.5 on: the stager only ran refused until now.
            resp = await run_in_threadpool(_guest_dispatch, gw, "cache.stage", {"data": {"id": focal}})
            slugs = ((resp or {}).get("result") or {}).get("slugs") or []
            if not slugs:
                return
            _SEMCACHE_STAGE["membranes"] += 1
            pace = max(0.1, float(os.environ.get("AKASHA_SEMCACHE_WARM_PACE_S", "1.0")))
            for slug in slugs:
                if not slug or slug == focal:
                    continue
                if not _stage_minute_ok():
                    break                            # per-minute render budget spent — stop this burst
                if _snapshot_read(host, slug) is not None or _atom_html_cache_get(host, slug) is not None:
                    continue                         # already warm
                if not await _acquire_render(is_human=False):
                    await _aio.sleep(pace)           # a human holds the slot → yield, don't queue behind
                    continue
                try:
                    html = await run_in_threadpool(_render_atom_html, gw,
                                                   _read_template(word_index), slug, origin, host)
                finally:
                    _release_render()
                if html and not _html_truncated(html):
                    _atom_html_cache_put(host, slug, html)
                    await run_in_threadpool(_snapshot_write, host, slug, html)
                    _SEMCACHE_STAGE["warmed"] += 1
                    _SEMCACHE_STAGE["min_count"] += 1
                await _aio.sleep(pace)
            if _SEMCACHE_STAGE["membranes"] % 20 == 0:
                logger.info("[semcache.stage] membranes=%d warmed=%d (focal=%s)",
                            _SEMCACHE_STAGE["membranes"], _SEMCACHE_STAGE["warmed"], focal)
        except Exception as _sx:
            logger.debug("[semcache.stage] skipped for %s: %s", focal, _sx)

    @app.get("/a/{slug:path}", include_in_schema=False)
    async def _atom_permalink(request: fastapi_mod.Request, slug: str):
        _REQ_START.set(_time.time())               # F47-5.3 — per-class serve-time scoreboard
        if not os.path.isfile(word_index):
            return Response("Atom viewer unavailable", status_code=404)
        # F44 Part B — classify BEFORE any daemon work. A verified crawler is served the materialized
        # snapshot with ZERO cell-daemon RPCs; only humans (and a bounded lazy regeneration) reach the
        # live path. Degradation-first throughout: a miss / private atom / render error → the plain
        # shell for a human (today's behavior), a 503+Retry-After for a crawler (never a soft-404).
        host = (request.headers.get("host") or "").split(",")[0].strip()
        ip = _client_ip(request)
        ua = request.headers.get("user-agent") or ""
        cls = (await run_in_threadpool(_classify_client, ua, ip))["class"]
        _maybe_log_class_stats()

        # Phase 1.5 — a HUMAN dive stages the focal's neighbourhood for the next click (fire-and-forget,
        # rate-capped, LOW-priority warm that yields to humans). Bot/passerby dives never stage (§11.3).
        if cls == "human":
            _stage_on_human_dive(slug, host, _origin(request))

        # ── crawler class: snapshot-only fast lane (no daemon on the hot path) ──
        if cls == "crawler":
            snap = _snapshot_read(host, slug)
            if snap is not None:
                _class_note("crawler", "snapshot")
                return HTMLResponse(snap, headers={"Cache-Control": "public, max-age=3600"})
            # No fresh snapshot. Regenerate ONCE if a render slot is free — but never queue a crawl
            # storm onto the daemon: if the slots are busy, a crawler gets 503+Retry-After (B4), so
            # Google retries later instead of indexing a soft-404 shell. The snapshot fills in as the
            # bounded lazy generation catches up.
            # Human-priority render slot: a crawler only renders when the slot is free AND no human
            # is waiting — it never makes a human queue behind it (F47-1.3).
            if not await _acquire_render(is_human=False):
                _class_note("crawler", "503")
                return Response("Snapshot warming — retry shortly", status_code=503,
                                headers={"Retry-After": os.environ.get("AKASHA_SNAPSHOT_RETRY", "30")})
            html = None
            try:
                html = await run_in_threadpool(_render_atom_html, gw, _read_template(word_index),
                                               slug, _origin(request), host)
            except Exception as exc:
                logger.warning("[ASGI] crawler SSR render error for %r: %s", slug, exc)
                html = None
            finally:
                _release_render()
            if html is None:
                _class_note("crawler", "503")
                return Response("Snapshot unavailable — retry shortly", status_code=503,
                                headers={"Retry-After": os.environ.get("AKASHA_SNAPSHOT_RETRY", "30")})
            if _html_truncated(html):
                # A partial render is a degraded SERVICE state, never a canonical snapshot (2.1). For
                # a crawler, 503 + Retry-After so it comes back for the full page instead of indexing
                # a partial one — and nothing is persisted.
                _class_note("crawler", "503")
                return Response("Building the full page — retry shortly", status_code=503,
                                headers={"Retry-After": os.environ.get("AKASHA_SNAPSHOT_RETRY", "30")})
            await run_in_threadpool(_snapshot_write, host, slug, html)   # persist for the next crawl
            _atom_html_cache_put(host, slug, html)
            _class_note("crawler", "generated")
            return HTMLResponse(html, headers={"Cache-Control": "public, max-age=3600"})

        # ── human / unverified-bot class: the existing live path (L1 cache → SSR → shell) ──
        # SSR: inject SEO head + a crawlable content body for THIS atom into the shell (guest-scoped
        # read → public content only). Degradation-first: a miss / private atom / render error → the
        # plain shell, never a 500, never a leak. The client JS still enhances to the full view.
        cached = _atom_html_cache_get(host, slug)
        if cached is not None:
            _class_note(cls, "l1")
            return HTMLResponse(cached, headers={"Cache-Control": "no-cache"})
        # F48-A 1.7 — STALE-WHILE-REVALIDATE: a page seen before (its L1 entry expired) is served
        # INSTANTLY from the stale-but-COMPLETE entry (a truncated render is never cached, so a stale
        # entry is always a whole page), while a background render refreshes it. This removes the
        # "slower than the first visit" step and masks a daemon restart for every previously-seen page
        # — a human never waits for a fresh render of a page they have already loaded.
        _stale = _atom_html_cache_get(host, slug, allow_stale=True)
        if _stale is not None:
            # Trigger the background refresh only for a HUMAN — a passerby/bot gets the stale-but-
            # complete page with ZERO added daemon load (no revalidation render), so a scraper storm
            # cannot turn stale hits into a render stampede.
            if cls == "human":
                import asyncio as _aio
                try:
                    _aio.get_event_loop().create_task(_revalidate(slug, host, _origin(request)))
                except Exception:
                    pass
            _class_note(cls, "l1-stale")
            return HTMLResponse(_stale[0], headers={"Cache-Control": "no-cache",
                                                    "X-Akasha-Cache": "stale; age=%d" % int(_stale[1])})
        # A PASSERBY (unverifiable traffic) is served snapshot/shell first — a disk snapshot (warmed
        # by an earlier crawler or human) is a zero-daemon win; live only if capacity is idle.
        if cls == "passerby":
            snap = _snapshot_read(host, slug)
            if snap is not None:
                _class_note("passerby", "snapshot")
                return HTMLResponse(snap, headers={"Cache-Control": "public, max-age=3600"})
            # F47-5.1 — a passerby OVER its per-IP /a budget is snapshot-first ONLY: with no snapshot
            # it gets the cheap client-rendered shell, never a live daemon render. So one aggressive
            # IP cannot keep igniting renders; the shell is a valid 200 the JS enhances (and its
            # beacon still rides along, keeping the upgrade-to-human path open — spec I5).
            _ok_rate, _ = _A_BOT_RATE_LIMITER.check(ip, _time.time())
            if not _ok_rate:
                _class_note("passerby", "rate-shell")
                return FileResponse(word_index, media_type="text/html",
                                    headers={"Cache-Control": "no-cache"})
        # F47-1.3 — a HUMAN waits (bounded) for the single render slot and is never shed while a bot
        # holds it; an unverified BOT sheds to the shell rather than queue another dive. F14b — the
        # render does blocking guest reads, run in the threadpool so a slow render never stalls the
        # event loop and starves the sys.ping health probe (a false "unhealthy" → respawn → OOM).
        _is_human = (cls == "human")
        if not await _acquire_render(is_human=_is_human):
            _class_note(cls, "shed")
            return FileResponse(word_index, media_type="text/html",
                                headers={"Cache-Control": "no-cache"})
        html = None
        try:
            html = await run_in_threadpool(_render_atom_html, gw, _read_template(word_index),
                                           slug, _origin(request), host)
        except Exception as exc:
            logger.warning("[ASGI] SSR render error for %r: %s", slug, exc)
            html = None
        finally:
            _release_render()
        if html is None:
            # no-cache → the browser revalidates every load, so a redeployed viewer
            # is picked up immediately instead of served stale from heuristic cache.
            _class_note(cls, "shell")
            return FileResponse(word_index, media_type="text/html",
                                headers={"Cache-Control": "no-cache"})
        if _html_truncated(html):
            # 2.1 — a partial render is served (marked "partial view — reload"), but NEVER cached in
            # L1 or persisted as a snapshot: a reload must re-render fresh, and no crawler may pick it
            # up as canon. Post-Part-1 a depth-1 render should not truncate; this is the safety net.
            _class_note(cls, "live-partial")
            return HTMLResponse(html, headers={"Cache-Control": "no-cache"})
        _atom_html_cache_put(host, slug, html)
        # Bonus (B2, SEO-positive): persist the human-rendered page as the snapshot so the next
        # crawler is served from disk without ever waking the daemon.
        await run_in_threadpool(_snapshot_write, host, slug, html)
        _class_note(cls, "live")
        return HTMLResponse(html, headers={"Cache-Control": "no-cache"})

    @app.get("/robots.txt", include_in_schema=False)
    async def _robots(request: fastapi_mod.Request):
        # Crawl-delay asks a cooperative crawler (Bing, Yandex, …) to pace itself so it does not
        # walk every /a/<slug> page at once and swamp the single daemon. (Google & Meta ignore
        # Crawl-delay — the SSR concurrency cap above is the enforcement that does not rely on the
        # crawler's cooperation.) Tunable via AKASHA_ROBOTS_CRAWL_DELAY; 0 omits the line.
        _cd = os.environ.get("AKASHA_ROBOTS_CRAWL_DELAY", "10").strip()
        _cd_line = f"Crawl-delay: {_cd}\n" if (_cd and _cd != "0") else ""
        body = ("User-agent: *\n"
                "Allow: /\n"
                "Disallow: /rpc\n"
                "Disallow: /api/\n"
                + _cd_line +
                f"Sitemap: {_origin(request)}/sitemap.xml\n")
        return PlainTextResponse(body)

    @app.get("/sitemap.xml", include_in_schema=False)
    async def _sitemap_index(request: fastapi_mod.Request):
        # A sitemap INDEX → one 'core' child (root + top-salient) + one child per
        # public namespace, so a domain site exposes ALL its atoms, paged per the
        # sitemaps.org 50k-per-file limit.
        origin = _origin(request)
        # F14b — the corpus build is a heavy a–z thesaurus.reference sweep; NEVER inline on the
        # loop. A crawler hitting the sitemap ~2-4 min after boot was the prime starvation suspect.
        namespaces = await run_in_threadpool(_sitemap_index_namespaces, gw)
        return Response(_xml_sitemapindex(origin, namespaces), media_type="application/xml")

    @app.get("/sitemap/{ns}.xml", include_in_schema=False)
    async def _sitemap_child(request: fastapi_mod.Request, ns: str):
        origin = _origin(request)
        locs = await run_in_threadpool(_sitemap_child_locs, gw, origin, ns)
        return Response(_xml_urlset(locs), media_type="application/xml")


def restricted_rule(path: str, rules):
    """The restricted-prefix rule a request path falls under: `(prefix, clients)` for the LONGEST
    declared prefix the path starts with, else None. `rules` is `manifest.declared_restricted()`."""
    for prefix, clients in sorted((rules or {}).items(), key=lambda kv: -len(kv[0])):
        if path.startswith(prefix):
            return prefix, list(clients)
    return None


def restricted_allows(client_id, role, clients) -> bool:
    """May this identity read a restricted prefix? One of its declared clients, or an admin."""
    return (client_id in (clients or [])) or (str(getattr(role, "value", role)).lower() == "admin")


def _build_app(fastapi_mod, gw, static_dirs=None, ssl_certfile=None, ssl_keyfile=None):
    """Build the live FastAPI ASGI app (all routes / middleware / static mounts) over `gw`.

    Extracted from run_server so the port can be BOUND immediately by a warming wrapper
    while this — the heavy part, which needs the ~1GB gateway substrate — is built off the
    bind path (see run_server_warming). Returns the ASGI app (possibly HostReroute-wrapped)."""
    from starlette.concurrency import run_in_threadpool   # F14b — keep the event loop free

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

    # ── Restricted prefixes — declared by the packages, never named here ─────────
    # A manifest's `restricted` map ({"/prefix": ["client", …]}) keeps that URL prefix (pages + JSON
    # assets) to those clients and admins. The gate resolves an akt: token from the `akasha_restricted`
    # cookie (or Bearer) to a client id. A JSON asset → 403; an HTML page → the sign-in form below
    # (passphrase → auth.verify → cookie scoped to the prefix → reload). Read-only token resolution —
    # no write; works in the split portal (the secret is shared). Nothing declared → nothing gated.
    try:
        from lib.akasha.api.manifest import declared_restricted as _declared_restricted
        _RESTRICTED = _declared_restricted()
    except Exception as _rx:
        logger.warning("[portal] restricted prefixes unreadable: %s", _rx)
        _RESTRICTED = {}
    if _RESTRICTED:
        logger.info("[portal] restricted prefixes=%s",
                    ",".join("%s(%d)" % (p, len(c)) for p, c in sorted(_RESTRICTED.items())))
    _RESTRICTED_HTML = """<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>Restricted</title>
<style>:root{color-scheme:light dark}body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;
background:#0a1622;color:#d8e9f0;font-family:'Courier New',monospace}
.card{max-width:360px;padding:30px 26px;border:1px solid rgba(120,190,200,.25);border-radius:10px;background:#0f1f2d}
h1{font-family:Georgia,serif;font-size:1.15rem;margin:0 0 6px;color:#e6f2f6}
p{font-size:.74rem;line-height:1.6;color:#8fb0bb;margin:0 0 16px}
input{width:100%;font-family:inherit;font-size:.9rem;padding:9px 10px;margin-bottom:10px;border-radius:6px;
border:1px solid rgba(120,190,200,.3);background:#0c1a26;color:#d8e9f0}
button{width:100%;font-family:inherit;font-size:.7rem;letter-spacing:1.5px;text-transform:uppercase;cursor:pointer;
padding:10px;border-radius:6px;border:1px solid #5fc8c0;background:rgba(95,200,192,.14);color:#5fc8c0}
.err{color:#e77390;font-size:.7rem;min-height:1em;margin-top:8px}</style></head>
<body><form class=card onsubmit="return go(event)">
<h1>Restricted</h1>
<p>Access to this page is restricted. Sign in with an account that may read it.</p>
<input id=uid type=text placeholder="client id" autocomplete=username spellcheck=false autofocus>
<input id=pw type=password placeholder=passphrase autocomplete=current-password>
<button type=submit>Enter</button><div class=err id=err></div></form>
<script>
var PREFIX=__PREFIX__;
function go(e){e.preventDefault();var pw=document.getElementById('pw').value;
var uid=(document.getElementById('uid').value||'').trim();if(!pw||!uid)return false;
document.getElementById('err').textContent='Verifying…';
fetch('/rpc',{method:'POST',headers:{'Content-Type':'application/json'},
body:JSON.stringify({jsonrpc:'2.0',method:'auth.verify',params:{user_id:uid,passphrase:pw},id:'v'})})
.then(function(r){return r.json();}).then(function(j){
if(j.error||!j.result||!j.result.session_token){document.getElementById('err').textContent='Access denied.';return;}
document.cookie='akasha_restricted='+j.result.session_token+';path='+PREFIX+';max-age=86400;samesite=Lax';
location.reload();}).catch(function(){document.getElementById('err').textContent='Sign-in failed.';});
return false;}
</script></body></html>"""

    @app.middleware("http")
    async def _restricted_gate(request: fastapi_mod.Request, call_next):
        path = request.url.path
        rule = restricted_rule(path, _RESTRICTED)
        if rule is not None:
            prefix, clients = rule
            tok = request.cookies.get("akasha_restricted", "")
            if not tok:
                _a = request.headers.get("Authorization", "")
                if _a.startswith("Bearer "):
                    tok = _a[7:].strip()
            ok = False
            if tok:
                try:
                    cid, _role = await run_in_threadpool(gw.kernel_client.iam.resolve_session_token, tok)
                    ok = restricted_allows(cid, _role, clients)
                except Exception:
                    ok = False
            if not ok:
                if path.endswith(".json"):
                    return fastapi_mod.responses.JSONResponse(
                        {"error": {"code": -32001, "message": "restricted"}}, status_code=403)
                from starlette.responses import HTMLResponse as _HTML
                return _HTML(_RESTRICTED_HTML.replace("__PREFIX__", json.dumps(prefix)), status_code=401)
        return await call_next(request)

    @app.get("/health", summary="Consciousness liveness check (sys.ping)")
    async def health():
        # A53 item 4a — answer the liveness probe ON the event loop, from the gateway's CACHED
        # writer_online, when the gateway offers it (the serve-only ThinPortal does). The old path
        # dispatched sys.ping through run_in_threadpool; a burst of slow renders can hold every
        # threadpool worker, and the probe would then queue behind them and TIME OUT → a false
        # 'unhealthy' → a portal respawn → the OOM churn. A cached dict read cannot block, so the
        # probe stays truthful even while the request threadpool is saturated. Only fall back to the
        # threadpool dispatch for a gateway that has no cached liveness (an in-process full engine).
        _cached = getattr(gw, "ping_cached", None)
        if callable(_cached):
            result = _cached()
            result.setdefault("status", "ok")
            return result
        # F19: keep the probe OFF the event loop — a synchronous dispatch here blocks the asyncio
        # loop while it runs, and under load that turns the liveness probe itself into a
        # TLS-handshake-timeout → portal respawn (the recurring F19-class wedge). Same treatment as
        # the /rpc and /mcp paths (F14b).
        resp = await run_in_threadpool(gw.dispatch, {
            "jsonrpc": "2.0", "method": "sys.ping",
            "params": {"session_token": "_health_"}, "id": "health",
        })
        result = resp.get("result", {})
        result.setdefault("status", "ok" if "error" not in resp else "degraded")
        return result

    # Single-concept READ methods worth counting as a concept view, → surface label. Only
    # methods that resolve to ONE concept (never a list like *.ls / thesaurus.reference).
    # The concept ref is in params `name` (archives.space) or `id` (<model>.get).
    # The single-concept reads the pulse tap records, and the SURFACE each one is recorded as, are
    # declared on the op (`"projection": {"pulse": "<surface>"}`, group 4, 4.7). The portal kept
    # seventeen application method names here — every kitchen dictionary by name.
    _PULSE_READ_METHODS = _manifest.declared_projection("pulse")

    def _pulse_result_found(result: Any) -> bool:
        """F51 (Cause B, 2.3.1) — did a single-concept read actually FIND the concept? Gate the tap
        on SEMANTIC success, not just transport success: a well-formed 'not found' result (no error,
        but the atom does not exist) must NOT be captured. True only when the result carries a real
        concept payload."""
        if not isinstance(result, dict) or not result:
            return False
        if result.get("found") is False or result.get("not_found") or result.get("error"):
            return False
        for k in ("concept", "atom", "name", "key", "id", "record", "found"):
            if result.get(k):
                return True
        # a domain .get returns its object either as the whole dict or under a content key; if only
        # status/flags remain, treat as not-found (don't capture a hollow result).
        real = {k: v for k, v in result.items()
                if k not in ("found", "status", "ok", "type", "cached", "window")}
        return bool(real)

    def _pulse_tap_read(request: fastapi_mod.Request, method: Any, params: Any, resp: Any = None) -> None:
        """Record one concept view from a successful single-concept /rpc read. Header-complete
        (ip/ua/referer here → a real visit id); off the critical path; DNT/GPC honoured in
        capture(); bots labelled not dropped. Captures only when the read actually FOUND the concept
        (F51 — a not-found read is internet noise, not a view)."""
        surface = _PULSE_READ_METHODS.get(method or "")
        if not surface:
            return
        if resp is not None and not _pulse_result_found(resp.get("result") if isinstance(resp, dict) else None):
            return
        p = params if isinstance(params, dict) else {}
        d = p.get("data") if isinstance(p.get("data"), dict) else p       # flat OR nested params
        ref = d.get("name") or d.get("id") or d.get("slug") or d.get("key") or ""
        if not isinstance(ref, str) or not ref.strip():
            return
        try:
            from lib.harmonia.pulse_recorder import recorder as _rec
            if not _rec.configured:
                return
            hdr = request.headers
            client = request.client.host if request.client else ""
            ip = (hdr.get("x-forwarded-for", "").split(",")[0].strip() or client)
            _rec.capture(concept=ref.strip(), surface=surface, referer=hdr.get("referer", ""),
                         ip=ip, ua=hdr.get("user-agent", ""),
                         dnt=(hdr.get("dnt") == "1" or hdr.get("sec-gpc") == "1"),
                         own_host=(hdr.get("host", "").split(":", 1)[0]))
        except Exception as _cex:
            logger.debug("[ASGI] pulse tap capture failed: %s", _cex)

    def _busy_response(retry_after_s: int, rid=None, code: int = -32029,
                       msg: str = "Server busy — retry shortly."):
        """A 429 with a Retry-After header + a JSON-RPC busy error body (P1a/P3). Polite crawlers and
        well-behaved clients back off on the header; the body carries the machine-readable retry."""
        return fastapi_mod.responses.JSONResponse(
            status_code=429,
            headers={"Retry-After": str(max(1, int(retry_after_s)))},
            content={"jsonrpc": "2.0", "id": rid,
                     "error": {"code": code, "message": msg,
                               "data": {"retry_after_ms": int(max(1, retry_after_s) * 1000)}}})

    async def _rpc_dispatch(request: fastapi_mod.Request) -> Any:
        try:
            # F39-P3 — per-IP rate limit at the HTTP edge: shed an impolite crawler BEFORE the kernel.
            _allow, _wait = _RPC_RATE_LIMITER.check(_client_ip(request), _time.time())
            if not _allow:
                return _busy_response(_wait, code=-32030,
                                      msg="Rate limit exceeded — slow down.")
            payload = await request.json()
            # Relay Authorization header as session_token if params don't carry one.
            # API layer does not interpret the token — it is opaque to us.
            if isinstance(payload, dict):
                p = payload.get("params")
                if isinstance(p, dict) and not p.get("session_token"):
                    auth = request.headers.get("Authorization", "")
                    if auth.startswith("Bearer "):
                        p["session_token"] = auth[7:].strip()
            # A7 — serve a PUBLIC reference letter page from the portal cache (warmed by the semcache
            # loop's routes pass) WITHOUT the daemon round-trip. Only archives/thesaurus.reference with
            # an `initial`, for a guest/anonymous token (an authenticated `akt:` session may see a
            # different visibility-filtered result, so it bypasses). Any miss falls through to dispatch.
            if isinstance(payload, dict) and isinstance(payload.get("params"), dict):
                _p = payload["params"]
                _m = payload.get("method")
                if (_m in _reference_methods() and str(_p.get("initial") or "").strip()
                        and _reference_public_token(_p)):
                    try:
                        _lim = int(_p.get("limit") or _reference_default_limit(_m))
                    except (TypeError, ValueError):
                        _lim = 100
                    _hit = _reference_cache_get((_m, str(_p.get("initial")).strip().lower(), _lim))
                    if _hit is not None:
                        return {"jsonrpc": "2.0", "id": payload.get("id"), "result": _hit}
            # F14b — the kernel dispatch is SYNC and can be slow (a heavy read); run it in the
            # threadpool so it never blocks the event loop and starve the sys.ping health probe
            # (which is itself a POST /api/rpc — a blocked loop can't even answer it → false
            # "unhealthy" → respawn → OOM). Reads parallelise (WAL); writes still serialise in the
            # WriteQueue, so threadpool execution is safe.
            resp = await run_in_threadpool(gw.dispatch, payload)
            # ── Pulse tap (universal concept-view capture) ────────────────────────
            # Every concept view on every page/domain is a single-concept READ through /rpc
            # (the kitchen `ingredient.get`/`cheese.get`, the atom viewer + recipe pages'
            # `archives.space`, etc.). Recording HERE — the one choke point that also holds the
            # request headers — captures them all with no per-page beacon and no client-side
            # resolution loss (the beacon only ever covered 3 pages, so pulse read near-zero).
            # Off the critical path: the recorder buffers and never blocks; a failure is swallowed.
            try:
                if isinstance(payload, dict) and isinstance(resp, dict) and not resp.get("error"):
                    _pulse_tap_read(request, payload.get("method"), payload.get("params"), resp)
            except Exception as _ptx:
                logger.debug("[ASGI] pulse tap skipped: %s", _ptx)
            # F39-P1a/P3 — the kernel refused this dive at the admission cap: surface it as a real 429
            # + Retry-After header so a crawler backs off (not a 200 it keeps hammering).
            _e = resp.get("error") if isinstance(resp, dict) else None
            if isinstance(_e, dict) and _e.get("code") == -32029:
                _ms = ((_e.get("data") or {}).get("retry_after_ms") or 1000)
                return _busy_response(max(1, int(_ms) // 1000), rid=resp.get("id"),
                                      msg=_e.get("message") or "Server busy — retry shortly.")
            return resp
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

    # ── Pulse analytics beacon (server-side capture; never a guest write) ─────────
    # The archives pages POST {concept, surface, prev} here once per concept view. Capture is
    # off the critical path: the recorder buffers and records asynchronously under a system
    # identity (see lib/harmonia/pulse_recorder). Privacy is enforced server-side — DNT is
    # honoured, and the visitor id is a daily-rotating salted hash of ip‖ua (no PII stored).
    try:
        from lib.harmonia.pulse_recorder import recorder as _pulse_recorder
        # F48-2.1 — register the shared base_dir so the recorder can resolve the elevation secret
        # from the daemon's 0600 file when this portal subprocess did not inherit AKASHA_SECRET
        # (the spawn-ordering gap that silently rejected every F16 pulse.emit).
        try:
            _pbase = getattr(gw, "_base_dir", None) or getattr(
                getattr(gw, "kernel_client", None), "base_dir", None)
            if _pbase:
                from api.portals.cell_ipc import register_elevation_base as _reb
                _reb(_pbase)
        except Exception:
            pass
        _pulse_recorder.configure(gw.dispatch)
    except Exception as _pex:                       # analytics must never break the portal
        _pulse_recorder = None
        logger.debug("[ASGI] pulse recorder unavailable: %s", _pex)

    # Response is imported locally inside _register_seo_routes (a different function), so it is
    # NOT in this scope — reference it via the fastapi module to avoid a NameError 500.
    _NoContent = fastapi_mod.Response

    async def _pulse_beacon(request: fastapi_mod.Request) -> Any:
        if _pulse_recorder is None:
            return _NoContent(status_code=204)
        try:
            body = await request.json()
        except Exception:
            body = {}
        concept = (body or {}).get("concept") or ""
        if concept:
            hdr = request.headers
            client = request.client.host if request.client else ""
            ip = (hdr.get("x-forwarded-for", "").split(",")[0].strip() or client)
            # Visitor-classes upgrade ladder — a beacon POST is proof of a real browser running JS:
            # mark this IP human so its subsequent page views are served on the full live path.
            _mark_human(ip)
            # F17b — prefer the page's OWN referrer (sent in the body) over the HTTP Referer.
            # For a cross-origin beacon the Referer header is the beacon's page itself, so every
            # landing hit would bucket as that host; `page_referrer` (document.referrer) carries the
            # visitor's real origin (LinkedIn / Google / …). Capped like the other body fields.
            _ref = (str(body.get("page_referrer") or "")[:300]) or hdr.get("referer", "")
            try:
                _pulse_recorder.capture(
                    concept=concept, surface=(body.get("surface") or ""),
                    referer=_ref, prev=(body.get("prev") or ""),
                    ip=ip, ua=hdr.get("user-agent", ""),
                    dnt=(hdr.get("dnt") == "1" or hdr.get("sec-gpc") == "1"),
                    own_host=(hdr.get("host", "").split(":", 1)[0]),
                )
            except Exception as _cex:               # analytics must never 500 a page's beacon
                logger.debug("[ASGI] pulse capture error: %s", _cex)
        return _NoContent(status_code=204)

    app.add_api_route("/pulse", _pulse_beacon, methods=["POST"], include_in_schema=False,
                      summary="Access-analytics beacon (server-side capture)")

    # ── MCP (Model Context Protocol) over HTTP — the remote LLM route (TRUST_NETWORK) ──
    # An anonymous caller is given a guest session (read-only); a Bearer akt: token acts with
    # that identity's scopes. The kernel is the capability gate. Session reuse via Mcp-Session-Id.
    async def _mcp_dispatch(request: fastapi_mod.Request) -> Any:
        from api.portals.mcp import mcp_http_process
        raw = await request.body()
        # F14b — MCP processing does a blocking kernel dispatch; keep it off the event loop.
        resp, status, headers = await run_in_threadpool(
            mcp_http_process, gw, raw,
            request.headers.get("Mcp-Session-Id", ""),
            request.headers.get("Authorization", ""))
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

    return app_to_run


# ── Warming page — served the instant the port binds, before the gateway is ready ──────
# The single worst boot outcome is a server that looks DOWN (connection refused) while its
# ~1GB read-substrate loads. Lever C (docs/for-llm/boot-startup-latency-proposal.md): bind
# and listen FIRST, serve this lightweight "warming up" page, and swap in the live app the
# instant it is built. A human sees "loading", never a dead server; the page self-refreshes.
_WARMING_HTML = """<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Akasha — warming up</title>
<style>
:root{color-scheme:light dark;--bg:#f7fafc;--fg:#22303a;--mut:#5f7784;--accent:#2a9d8f;--card:#ffffff;--line:rgba(90,140,150,.22)}
@media (prefers-color-scheme:dark){:root{--bg:#0a1622;--fg:#d8e9f0;--mut:#8fb0bb;--accent:#5fc8c0;--card:#0f1f2d;--line:rgba(120,190,200,.22)}}
*{box-sizing:border-box}
body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;background:var(--bg);
color:var(--fg);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif}
.card{max-width:420px;padding:38px 32px;text-align:center;border:1px solid var(--line);border-radius:14px;background:var(--card)}
.spin{width:38px;height:38px;margin:0 auto 22px;border:3px solid var(--line);border-top-color:var(--accent);
border-radius:50%;animation:r 1s linear infinite}
@keyframes r{to{transform:rotate(360deg)}}
h1{font-family:Georgia,serif;font-size:1.3rem;margin:0 0 10px;letter-spacing:.3px}
p{font-size:.86rem;line-height:1.65;color:var(--mut);margin:0}
.sub{margin-top:14px;font-size:.7rem;letter-spacing:1.4px;text-transform:uppercase;color:var(--accent)}
</style></head>
<body><main class=card>
<div class=spin></div>
<h1>Akasha is warming up</h1>
<p>The knowledge substrate is loading. This page will open automatically the moment it is ready — no need to refresh.</p>
<div class=sub>loading ontology…</div>
</main>
<script>
// Poll the health endpoint; reload as soon as the live gateway answers. Falls back to a
// timed reload if fetch is blocked, so the page can never get permanently stuck on "loading".
(function(){
  var tries=0;
  function check(){
    tries++;
    fetch('/health',{cache:'no-store'}).then(function(r){return r.ok?r.json():null;}).then(function(j){
      if(j&&(j.status==='ok'||j.status==='degraded')){location.reload();return;}
      setTimeout(check,2500);
    }).catch(function(){setTimeout(check,2500);});
  }
  setTimeout(check,2000);
  // Hard fallback: reload every 15s regardless, in case /health is proxied away.
  setInterval(function(){location.reload();},15000);
})();
</script></body></html>"""

# API/health path prefixes that should get a JSON 503 (not the HTML page) while warming, so
# programmatic clients / the supervisor health probe get a proper machine-readable "retry".
_WARMING_API_PREFIXES = ("/rpc", "/api/rpc", "/health", "/mcp", "/api/mcp", "/pulse")


async def _send_simple(send, status, headers, body: bytes):
    await send({"type": "http.response.start", "status": status, "headers": headers})
    await send({"type": "http.response.body", "body": body})


def _unwrap_app(app):
    """F60 §5.1 — walk the middleware chain to the app that actually carries `.state`. `_build_app`
    returns `HostReroute(app, …)` (no `.state`) wrapping the FastAPI app; the deferred-startup list
    lives on the inner app. Bounded walk over `.app` links."""
    a = app
    for _ in range(8):
        if hasattr(a, "state"):
            return a
        if hasattr(a, "app"):
            a = a.app
        else:
            break
    return a


def _start_deferred_startups(app, loop) -> list:
    """F58 §0 / F60 §5 — schedule an app's deferred startup coroutines (the semcache warm loop) on the
    running event `loop`, from ANY thread. _build_app collects these on `app.state.deferred_startups`
    instead of an ASGI lifespan handler, because under Lever C the warming holder consumes the lifespan
    protocol and the swapped-in app's startup events never fire. IDEMPOTENT: both the holder swap and
    the first request after it call this — a `_deferred_started` stamp on the app state means whichever
    runs first wins and the other is a no-op (never two warm loops). Returns the names scheduled."""
    import asyncio as _aio
    a = _unwrap_app(app)                                     # §5.1 — HostReroute has no .state
    state = getattr(a, "state", None)
    if state is None:
        logger.warning("[ASGI] no deferred startups found on %s (no .state on the app chain)",
                       type(app).__name__)
        return []
    if getattr(state, "_deferred_started", False):
        return []                                           # already scheduled — idempotent
    deferred = list(getattr(state, "deferred_startups", []) or [])
    if not deferred:
        logger.warning("[ASGI] no deferred startups found on %s", type(a).__name__)
        return []
    state._deferred_started = True
    started = []
    for fn in deferred:
        name = getattr(fn, "__name__", "task")
        try:
            _aio.run_coroutine_threadsafe(fn(), loop)
            started.append(name)
        except Exception as _e:
            logger.warning("[ASGI] deferred startup %s failed to schedule: %s", name, _e)
    if started:
        logger.info("[ASGI] scheduled deferred startups: %s", ", ".join(started))
    return started


def _warming_asgi(holder):
    """A pure-ASGI app that binds the port immediately and serves the warming page until
    `holder['app']` is populated with the live app, then delegates every request to it.
    Any HTTP response here (200 page or 503 JSON) still counts as 'alive' to the Supervisor
    health probe, so a slow-but-healthy boot is never respawned mid-warm."""
    async def app(scope, receive, send):
        # A21 — the portal serves no WebSocket route; a ws probe delegated to the live app reaches the
        # StaticFiles mount at "/" and crashes on starlette's `assert scope["type"] == "http"` (4×
        # "Exception in ASGI application" + 500). Close it cleanly (1003 = unsupported data) here,
        # before HostReroute/StaticFiles ever see it.
        if scope.get("type") == "websocket":
            try:
                await send({"type": "websocket.close", "code": 1003})
            except Exception:
                pass
            logger.debug("[ASGI] websocket probe closed (no ws route on this portal)")
            return
        real = holder.get("app")
        if real is not None:
            # F60 §5.2 — start the deferred startups from the LOOP THREAD on the first scope seen after
            # the swap. This covers both observed orderings (swap before uvicorn's loop exists; swap
            # after lifespan) and backs up the build-thread attempt; _start_deferred_startups is
            # idempotent, so whichever fires first wins and there is never a second warm loop.
            if not holder.get("warm_started"):
                holder["warm_started"] = True
                try:
                    import asyncio as _aio
                    _start_deferred_startups(real, _aio.get_running_loop())
                except Exception as _wsx:
                    logger.warning("[ASGI] first-request deferred-startup scheduling failed: %s", _wsx)
            await real(scope, receive, send)
            return
        stype = scope.get("type")
        if stype == "lifespan":
            while True:
                message = await receive()
                if message["type"] == "lifespan.startup":
                    # F58 §0 (A6) — capture the uvicorn event loop here so the build thread can
                    # schedule the live app's deferred startups on it at the holder swap (the live
                    # app's own lifespan startup never runs — this warming app consumes it).
                    try:
                        import asyncio as _aio
                        holder["loop"] = _aio.get_running_loop()
                    except Exception:
                        pass
                    await send({"type": "lifespan.startup.complete"})
                elif message["type"] == "lifespan.shutdown":
                    await send({"type": "lifespan.shutdown.complete"})
                    return
        if stype != "http":
            return
        path = scope.get("path", "/")
        if any(path == p or path.startswith(p + "/") for p in _WARMING_API_PREFIXES) or path.startswith("/api/"):
            body = json.dumps({"jsonrpc": "2.0", "id": None, "status": "warming",
                               "error": {"code": -32002,
                                         "message": "Akasha is warming up — loading the substrate. Retry shortly."}},
                              ensure_ascii=False).encode("utf-8")
            headers = [(b"content-type", b"application/json"), (b"retry-after", b"3"),
                       (b"cache-control", b"no-store")]
            await _send_simple(send, 503, headers, body)
        else:
            body = _WARMING_HTML.encode("utf-8")
            headers = [(b"content-type", b"text/html; charset=utf-8"), (b"retry-after", b"3"),
                       (b"cache-control", b"no-store")]
            await _send_simple(send, 200, headers, body)
    return app


def _run_uvicorn(uvicorn_mod, app_to_run, host, port, ssl_certfile, ssl_keyfile, in_bg):
    """Run uvicorn on an already-built ASGI app. Returns the Server (for should_exit signalling
    from another thread) only after it stops; callers that need the handle pass a holder."""
    _scheme = "https" if (ssl_certfile and ssl_keyfile) else "http"
    logger.info(f"[ASGI] Binding portal on {host}:{port} ({_scheme})")
    # R7 — bound uvicorn's graceful shutdown BELOW the supervisor's SIGTERM grace (5.0s). Its default
    # graceful shutdown waits on keep-alive connections (crawlers and guests hold them open) with no
    # bound, so on a `stop` the grace expired and the supervisor SIGKILL'd the portal (a WARNING that
    # should stay reserved for a wedged portal). At 3s the portal drains its idle keep-alives and exits
    # `status=-15` inside the grace. Override with AKASHA_PORTAL_GRACEFUL_S if a slower host needs it,
    # but keep it under the reaper grace or the SIGKILL returns.
    try:
        _grace_s = float(os.environ.get("AKASHA_PORTAL_GRACEFUL_S", "3") or 3)
    except (TypeError, ValueError):
        _grace_s = 3.0
    _cfg_kwargs = dict(host=host, port=port, log_level="info",
                       timeout_graceful_shutdown=max(1, int(_grace_s)))
    if ssl_certfile and ssl_keyfile:
        _cfg_kwargs["ssl_certfile"] = ssl_certfile
        _cfg_kwargs["ssl_keyfile"] = ssl_keyfile
    config = uvicorn_mod.Config(app_to_run, **_cfg_kwargs)
    server = uvicorn_mod.Server(config)
    # install_signal_handlers is only valid on the main thread; skip it off-main.
    if in_bg:
        config.install_signal_handlers = False
    return config, server


def run_server(gw, host: str = "0.0.0.0", port: int = 8000, static_dirs=None,
               ssl_certfile=None, ssl_keyfile=None):
    """
    FastAPI ASGI server (builds the app on the calling thread, then binds).
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

    app_to_run = _build_app(fastapi_mod, gw, static_dirs, ssl_certfile, ssl_keyfile)

    # F58 §0 / F60 §5.3 — this direct path runs the real app itself, so its lifespan DOES fire;
    # schedule the deferred startups (the semcache warm loop) here rather than inside _build_app
    # (which stays lifespan-free so the warming path can't silently drop them). Register on the
    # UNWRAPPED inner app — the HostReroute wrapper has no `.on_event`.
    _inner_app = _unwrap_app(app_to_run)

    @_inner_app.on_event("startup")
    async def _run_deferred_startups() -> None:
        import asyncio as _aio
        _PORTAL_READY["at"] = _time.time()             # §5.4 — direct-run readiness marker
        try:
            _start_deferred_startups(app_to_run, _aio.get_running_loop())
        except Exception as _sx:
            logger.warning("[ASGI] deferred startups not scheduled: %s", _sx)

    _config, server = _run_uvicorn(uvicorn_mod, app_to_run, host, port,
                                   ssl_certfile, ssl_keyfile, _in_bg)
    try:
        server.run()
    except (KeyboardInterrupt, SystemExit):
        logger.info("[ASGI] Portal shut down.")
    except Exception as exc:
        logger.warning(f"[ASGI] Portal exited: {exc}")


def run_server_warming(gw_factory, host: str = "0.0.0.0", port: int = 8000, static_dirs=None,
                       ssl_certfile=None, ssl_keyfile=None, on_ready=None):
    """Lever C — bind the port IMMEDIATELY with a warming page, then build the live gateway
    (the ~1GB substrate) on a background thread and swap it in when ready.

    `gw_factory` is a zero-arg callable returning the ready-to-serve gateway (it does the heavy
    create_gateway/attach work). `on_ready(gw)` runs once the live app is serving. If the factory
    raises, the worker is told to exit so the Supervisor respawns it (never serve loading forever).
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

    holder = {"app": None, "error": None, "loop": None}
    warming = _warming_asgi(holder)
    _config, server = _run_uvicorn(uvicorn_mod, warming, host, port,
                                   ssl_certfile, ssl_keyfile, _in_bg)

    def _build():
        try:
            gw = gw_factory()
            app_to_run = _build_app(fastapi_mod, gw, static_dirs, ssl_certfile, ssl_keyfile)
            holder["app"] = app_to_run                 # atomic swap — next request serves live
            _PORTAL_READY["at"] = _time.time()         # §5.4 — mark 'ready' for the warm after_ready log
            logger.info("[ASGI] Live gateway ready — serving real content.")
            # F58 §0 (A6) — the swapped-in app's lifespan startup never fires (the warming holder
            # answered it), so schedule its deferred startups (the semcache warm loop) explicitly on
            # the captured uvicorn loop. Without this the portal warm half is dead (warm=0/0 forever).
            _loop = holder.get("loop")
            if _loop is not None:
                _started = _start_deferred_startups(app_to_run, _loop)
                if _started:
                    logger.info("[ASGI] scheduled deferred startups at swap: %s", ", ".join(_started))
            else:
                # A13(d) — NOT a failure: when the build thread wins the race to the swap before
                # uvicorn's loop exists (the common ordering with the fast ThinPortal gateway), the
                # first-scope path in _warming_asgi starts the loop a few ms later. INFO, not WARNING.
                logger.info("[ASGI] loop not captured at swap — deferring deferred startups to the "
                            "first scope (first-request start)")
            if on_ready:
                try:
                    on_ready(gw)
                except Exception as _orx:
                    logger.warning("[ASGI] on_ready callback failed: %s", _orx)
        except Exception as exc:
            holder["error"] = str(exc)
            logger.error("[ASGI] Gateway build failed — exiting so the Supervisor respawns: %s",
                         exc, exc_info=True)
            server.should_exit = True                  # stop uvicorn → worker exits non-zero below

    threading.Thread(target=_build, name="portal-gateway-build", daemon=True).start()
    try:
        server.run()
    except (KeyboardInterrupt, SystemExit):
        logger.info("[ASGI] Portal shut down.")
    except Exception as exc:
        logger.warning(f"[ASGI] Portal exited: {exc}")
    if holder["app"] is None and holder["error"]:
        raise SystemExit(f"[ASGI] portal gateway build failed: {holder['error']}")


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
