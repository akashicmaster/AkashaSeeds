"""The Application API — `jobs`. The names and their contracts are in `lib/akasha/api/exports.py`
(and `docs/platform/SPEC.md` §3); this module resolves them lazily, so importing it imports nothing."""
from lib.akasha.api.exports import EXPORTS as _EXPORTS, bind as _bind

__all__ = sorted(_EXPORTS["jobs"])
__getattr__, __dir__ = _bind(__name__, "jobs")


def is_blocked(method: str) -> bool:
    """True if a batch (JCL) step may not call `method`."""
    from lib.akasha.jcl import validator as _v
    m = str(method or "")
    return m in _v._BLOCKED_METHODS or any(m.startswith(p) for p in _v._BLOCKED_PREFIXES)
