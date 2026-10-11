"""The Application API — `client`. The names and their contracts are in `lib/akasha/api/exports.py`
(and `docs/platform/SPEC.md` §3); this module resolves them lazily, so importing it imports nothing."""
from lib.akasha.api.exports import EXPORTS as _EXPORTS, bind as _bind

__all__ = sorted(_EXPORTS["client"])
__getattr__, __dir__ = _bind(__name__, "client")


def embedded(base_dir: str, series: str = "seeds", load_ontology: bool = True):
    """A gateway over an in-process cell (offline scripts, evals) — never beside a running writer.
    `.dispatch(payload)` answers like a running cell; `.kernel_client.dispatch(payload, trust)` is the
    in-process dispatcher. `load_ontology=False` boots the cell without its packs (a lab script that
    describes its own data) — per cell, nothing global is patched."""
    from lib.akasha.kernel import KernelDispatcher
    from api.gateway import AkashaGateway
    cls = KernelDispatcher
    if not load_ontology:
        cls = type("EmbeddedCellNoPacks", (KernelDispatcher,), {"_boot_load_ontology": lambda self: None})
    return AkashaGateway(kernel_client=cls(series=series, base_dir=base_dir))
