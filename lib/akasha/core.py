"""
Backwards-compatibility shim.

AkashaCore has been split into:
  AkashaBackend  — abstract instruction-set interface  (backends/base.py)
  SQLiteBackend  — current SQLite implementation       (backends/sqlite.py)

This alias keeps all existing call sites (composite.py, etc.) unchanged.
New code should import directly from the backends package.
"""
from lib.akasha.backends.sqlite import SQLiteBackend as AkashaCore

__all__ = ["AkashaCore"]
