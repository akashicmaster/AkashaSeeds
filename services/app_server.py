"""
Akasha Sub-Service Launcher.

Single entry point for all web sub-services. Discovers custom API routes
from services/routes/<name>.py if present; otherwise serves /api/rpc and
static files only.

Usage:
    python -m services.app_server --app <name> [--port <n>] [--host <h>]

Route convention (services/routes/<name>.py):
    ROUTES = {
        "/api/<name>/action": ("POST", handler_fn),
    }
    Where handler_fn(req_data: dict) -> dict.
    req_data always contains "session_token" (validated by the HTTP layer).
"""
import sys
import os
import argparse
import importlib

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.http_gateway import BaseWebService


def load_routes(app_name: str) -> dict:
    """
    Import services/routes/<app_name>.py and return its ROUTES dict.
    Returns {} silently if the file does not exist.
    """
    try:
        mod = importlib.import_module(f"services.routes.{app_name}")
        return getattr(mod, "ROUTES", {})
    except ModuleNotFoundError:
        return {}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Akasha Sub-Service Launcher")
    parser.add_argument("--app",  required=True, help="App name (matches static/<name>/)")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8081)
    args = parser.parse_args()

    routes = load_routes(args.app)

    svc = BaseWebService(port=args.port, host=args.host)
    for path, (method, handler) in routes.items():
        svc.add_route(path, method, handler)

    print("=" * 44)
    print(f"  Akasha / {args.app}")
    print(f"  http://{args.host}:{args.port}/{args.app}/")
    if routes:
        for path in routes:
            print(f"  POST {path}")
    print("=" * 44)
    sys.stdout.flush()
    svc.start()
