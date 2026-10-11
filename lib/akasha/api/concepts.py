"""The Application API — `concepts`. The names and their contracts are in `lib/akasha/api/exports.py`
(and `docs/platform/SPEC.md` §3); this module resolves them lazily, so importing it imports nothing."""
from lib.akasha.api.exports import EXPORTS as _EXPORTS, bind as _bind

__all__ = sorted(_EXPORTS["concepts"])
__getattr__, __dir__ = _bind(__name__, "concepts")


def model_class(prefix: str):
    """The Concept Model class that declares `prefix`, or None."""
    from lib.akasha import api as _api
    return _api.concept_class(None, prefix)


def model(session, prefix: str):
    """An instance of the Concept Model that declares `prefix`, bound to `session`, or None."""
    cls = model_class(prefix)
    return cls(session) if cls is not None else None
