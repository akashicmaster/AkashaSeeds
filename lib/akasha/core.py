"""
Backwards-compatibility shim + engine factory.

AkashaCore has been split into:
  AkashaBackend  — abstract instruction-set interface  (backends/base.py)
  SQLiteBackend  — current SQLite implementation       (backends/sqlite.py)
  SilicaBackend  — self-owned pseudo-ISA store          (backends/silica_backend.py)

`AkashaCore(db_path, …)` keeps every existing call site unchanged and now selects
the backend from the `AKASHA_BACKEND` env var — the ONE swap point for the twin
release (正規版 = sqlite, ネイティブ版 = silica).  Default is sqlite, so normal
boot is byte-for-byte unchanged; silica is opt-in and lazily imported.

  AKASHA_BACKEND=sqlite   (default) → SQLiteBackend
  AKASHA_BACKEND=silica            → SilicaBackend
"""
import os

from lib.akasha.backends.sqlite import SQLiteBackend

__all__ = ["AkashaCore"]


def AkashaCore(db_path, is_volatile: bool = False, sync_mode: str = "NORMAL", banks: int = None):
    """Construct the configured storage backend (drop-in for the old class alias).

    `banks` (silica only) sizes a FRESH store's bank fan-out; None → the backend default (8). A
    per-client cell cortex passes banks=1 (fewer WAL FDs — the guest-FD diet); an existing store
    keeps its own on-disk geometry regardless. SQLite ignores it (single file)."""
    backend = os.environ.get("AKASHA_BACKEND", "sqlite").strip().lower()
    if backend in ("silica", "native"):
        from lib.akasha.backends.silica_backend import SilicaBackend
        kw = {} if banks is None else {"banks": banks}
        return SilicaBackend(db_path, is_volatile=is_volatile, sync_mode=sync_mode, **kw)
    return SQLiteBackend(db_path, is_volatile=is_volatile, sync_mode=sync_mode)
