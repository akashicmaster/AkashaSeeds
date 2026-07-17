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
                      "/a", "/robots.txt", "/sitemap.xml")


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
from xml.sax.saxutils import escape as _xml_escape

# Cached sitemap slug list (shared across hosts; the <loc> host/scheme is filled
# per-request so every domain gets a same-origin sitemap). (slugs, fetched_at).
_SITEMAP_CACHE = {"slugs": None, "ts": 0.0}
_SITEMAP_LOCK = _threading.Lock()
_SITEMAP_TTL = 3600.0        # regenerate at most hourly — off the hot path


def _sitemap_slugs(gw):
    """The qualified-alias slugs to expose in the sitemap, ranked by salience.

    Efficient by construction: one guest read of thesaurus.reference (the
    glossary of named concepts, each carrying its salience), sorted by salience
    and capped to the highest-value slice — exactly what should be crawled
    first — cached for _SITEMAP_TTL. (Broader coverage via pagination/namespace-
    walk is a later refinement.)
    """
    now = _time.time()
    with _SITEMAP_LOCK:
        if _SITEMAP_CACHE["slugs"] is not None and (now - _SITEMAP_CACHE["ts"]) < _SITEMAP_TTL:
            return _SITEMAP_CACHE["slugs"]
    slugs = []
    try:
        g = gw.dispatch({"jsonrpc": "2.0", "method": "session.guest.create",
                         "params": {}, "id": "sitemap"})
        tok = (g.get("result") or {}).get("binding_key")
        if tok:
            r = gw.dispatch({"jsonrpc": "2.0", "method": "thesaurus.reference",
                             "params": {"session_token": tok, "limit": 500}, "id": "sitemap"})
            concepts = (r.get("result") or {}).get("concepts", [])
            concepts.sort(key=lambda c: c.get("salience") or 0, reverse=True)
            for a in concepts[:200]:
                slug = a.get("name") or a.get("term")
                if slug:
                    slugs.append(slug)
    except Exception as exc:
        logger.warning("[ASGI] sitemap generation failed: %s", exc)
    with _SITEMAP_LOCK:
        _SITEMAP_CACHE["slugs"] = slugs
        _SITEMAP_CACHE["ts"] = now
    return slugs


def _origin(request) -> str:
    """scheme://host for the incoming request, honouring TLS and the Host header."""
    host = (request.headers.get("host") or request.url.netloc or "localhost").split(",")[0].strip()
    scheme = request.headers.get("x-forwarded-proto") or request.url.scheme or "http"
    return f"{scheme}://{host}"


def _slug_path(slug: str) -> str:
    """Encode a qualified alias into a clean /a/ path — keep ':' readable."""
    from urllib.parse import quote
    return "/a/" + quote(slug, safe=":")


def _register_seo_routes(app, fastapi_mod, gw, root_dir):
    """Clean permalinks + crawlability, all client-rendered (same as word page):
      GET /a/<slug>     → serve the shared atom viewer (word/index.html)
      GET /robots.txt   → allow all + point to this host's sitemap
      GET /sitemap.xml  → same-origin URLs for the salient atoms
    """
    from starlette.responses import FileResponse, PlainTextResponse, Response

    word_index = os.path.join(root_dir, "word", "index.html")

    @app.get("/a/{slug:path}", include_in_schema=False)
    async def _atom_permalink(slug: str):
        if not os.path.isfile(word_index):
            return Response("Atom viewer unavailable", status_code=404)
        # The viewer reads the slug from its own path and fetches via /rpc.
        return FileResponse(word_index, media_type="text/html")

    @app.get("/robots.txt", include_in_schema=False)
    async def _robots(request: fastapi_mod.Request):
        body = ("User-agent: *\n"
                "Allow: /\n"
                "Disallow: /rpc\n"
                "Disallow: /api/\n"
                f"Sitemap: {_origin(request)}/sitemap.xml\n")
        return PlainTextResponse(body)

    @app.get("/sitemap.xml", include_in_schema=False)
    async def _sitemap(request: fastapi_mod.Request):
        origin = _origin(request)
        urls = ["  <url><loc>%s/</loc></url>" % _xml_escape(origin)]
        for slug in _sitemap_slugs(gw):
            loc = _xml_escape(origin + _slug_path(slug))
            urls.append(f"  <url><loc>{loc}</loc></url>")
        xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
               + "\n".join(urls) + "\n</urlset>\n")
        return Response(xml, media_type="application/xml")


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
            for mount_path, dir_path in static_dirs:
                if os.path.isdir(dir_path):
                    name = f"static_{mount_path.strip('/').replace('/', '_') or 'root'}"
                    app.mount(mount_path, StaticFiles(directory=dir_path, html=True), name=name)
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
