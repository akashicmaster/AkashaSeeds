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


def run_server(gw, host: str = "0.0.0.0", port: int = 8000, static_dirs=None):
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

    logger.info(f"[ASGI] Binding portal on {host}:{port}")
    try:
        config = uvicorn_mod.Config(app, host=host, port=port, log_level="info")
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
