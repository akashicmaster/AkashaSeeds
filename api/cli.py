"""Backward-compatibility shim. Logic lives in api/portals/stdio.py."""
from api.portals.stdio import run_cli, run_single_shot

__all__ = ["run_cli", "run_single_shot"]
