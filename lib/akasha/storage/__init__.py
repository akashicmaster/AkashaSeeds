"""S1-b — the storage abstraction beneath the semantic layer.

Three layers (plan-s1 §2.1), no S3 vocabulary above the bottom one:

    Akasha semantic layer (concepts, macros, driver)
            ↓
    SemanticArtifactStore   — artifact_id / epoch / inputs → an immutable generation
            ↓
    DurableSemanticStore    — put_immutable / read / read_range / publish_generation /
                              resolve_generation / cas_pointer / acquire_lease / renew /
                              release / list_generations, behind a negotiated CapabilitySet
            ↓
    backend: local filesystem (now) · S3 / MinIO (archives) · distributed (later)

A backend is admitted by the STORAGE SEMANTICS it proves (its CapabilitySet), never by the API it
imitates: a writer store needs CAS + leases; an archives mirror needs only immutable put + range read
+ list. `check_backend` decides, and the boot `[store] …` line makes the decision visible.
"""
from lib.akasha.storage.base import (
    CapabilitySet,
    DurableSemanticStore,
    SemanticArtifactStore,
    WRITER_REQUIRED,
    ARCHIVES_REQUIRED,
    check_backend,
)
from lib.akasha.storage.local import LocalDurableStore

# The process-wide artifact store (set by the kernel at boot); a concept reads it for `store.status`.
_ACTIVE = {"artifact": None, "durable": None, "role": "read-only", "backend": "-", "missing": []}


def set_active_store(artifact, durable, role: str, backend: str, missing) -> None:
    _ACTIVE.update({"artifact": artifact, "durable": durable, "role": role,
                    "backend": backend, "missing": list(missing or [])})


def active_store() -> dict:
    return dict(_ACTIVE)


__all__ = [
    "CapabilitySet", "DurableSemanticStore", "SemanticArtifactStore",
    "WRITER_REQUIRED", "ARCHIVES_REQUIRED", "check_backend", "LocalDurableStore",
    "set_active_store", "active_store",
]
