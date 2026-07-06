"""Backward-compatibility shim. Logic lives in api/portals/asgi.py."""
from api.portals.asgi import run_server, run_cgi

__all__ = ["run_server", "run_cgi"]
