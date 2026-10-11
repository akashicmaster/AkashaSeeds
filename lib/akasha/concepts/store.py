"""S1-b — `store.*`, a read-only window on the artifact store's backend + negotiated capabilities.

The store itself is a process-level object (built by the kernel at boot, `_init_artifact_store`); this
concept only reports it, so a client (or an eval) can see which backend is active, what it proves, and
whether it was admitted as a writer or refused to read-only — the same decision the boot `[store] …`
line records. Reads only; nothing here mutates the store.
"""
from typing import Any, Dict

from lib.akasha.concepts._universal import UniversalConcept


class StoreConcept(UniversalConcept):
    CONCEPT_PREFIX = "store"
    CONCEPT_METHODS = {
        "status":      {"op": "op_status", "action": "read",
                        "desc": "The artifact store's backend, capabilities, and writer/read-only role: "
                                "store.status"},
        "generations": {"op": "op_generations", "action": "read",
                        "desc": "List the generation ids published under a kind + the current pointer: "
                                "store.generations kind=<kind>"},
    }

    def op_status(self) -> Dict[str, Any]:
        from lib.akasha.storage import active_store
        st = active_store()
        durable = st.get("durable")
        caps = durable.capabilities().as_dict() if durable is not None else {}
        return {"backend": st.get("backend"), "role": st.get("role"),
                "capabilities": caps, "missing": st.get("missing") or [],
                "active": durable is not None}

    def op_generations(self, kind: str = "") -> Dict[str, Any]:
        from lib.akasha.storage import active_store
        if not kind:
            raise ValueError("store.generations requires kind=")
        durable = active_store().get("durable")
        if durable is None:
            return {"kind": kind, "generations": [], "current": None, "note": "no active store"}
        gens = durable.list_generations(kind)
        cur = durable.resolve_generation(kind)
        return {"kind": kind, "generations": gens, "count": len(gens),
                "current": cur.get("generation"), "version": cur.get("version")}
