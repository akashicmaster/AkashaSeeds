"""The Application API — `graph`. The names and their contracts are in `lib/akasha/api/exports.py`
(and `docs/platform/SPEC.md` §3); this module resolves them lazily, so importing it imports nothing."""
from lib.akasha.api.exports import EXPORTS as _EXPORTS, bind as _bind

__all__ = sorted(_EXPORTS["graph"])
__getattr__, __dir__ = _bind(__name__, "graph")
