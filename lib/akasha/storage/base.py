"""S1-b §2.1/§2.2 — the storage interfaces and capability negotiation.

`CapabilitySet` is what a backend PROVES it can do; a tier declares what it REQUIRES; `check_backend`
admits or refuses. This is the HydraDB lesson made law: a backend is admitted by the semantics it
proves, not the API it imitates — a local filesystem that implements CAS + leases is a full writer
store; a plain S3 bucket that only puts immutable objects and serves ranges is an archives mirror and
is REFUSED as a writer backend (`[store] … missing=supports_cas → read-only`).
"""
from typing import Any, Dict, List, Optional, Tuple

# the capability flags a backend declares (plan-s1 §2.2)
_CAP_FLAGS = (
    "supports_cas",              # compare-and-swap a pointer (publish a generation atomically)
    "supports_versioning",      # immutable, hash-named generations kept side by side
    "supports_range_read",      # read a byte range of an object (serve archive ranges)
    "supports_consistent_list", # list_generations reflects the latest publish
    "supports_server_time",     # a trustworthy server clock (lease TTLs)
    "supports_leases",          # a fenced single-writer lease
)


class CapabilitySet:
    """The storage semantics a backend proves. Compared against a tier's requirement at boot."""

    __slots__ = _CAP_FLAGS

    def __init__(self, **flags: bool) -> None:
        for f in _CAP_FLAGS:
            setattr(self, f, bool(flags.get(f, False)))

    def as_dict(self) -> Dict[str, bool]:
        return {f: getattr(self, f) for f in _CAP_FLAGS}

    def has(self, flag: str) -> bool:
        return bool(getattr(self, flag, False))

    def missing(self, required: List[str]) -> List[str]:
        """The required capabilities this backend does NOT provide (empty ⇒ admitted)."""
        return [f for f in (required or []) if not self.has(f)]

    def __repr__(self) -> str:
        on = [f[len("supports_"):] for f in _CAP_FLAGS if self.has(f)]
        return "caps(%s)" % ",".join(on) if on else "caps(none)"


# A WRITER store must CAS a pointer and hold a fenced lease (the single-writer invariant, §2.5); an
# archives mirror needs only immutable put + range read + consistent list (§2.7).
WRITER_REQUIRED = ["supports_cas", "supports_versioning", "supports_leases"]
ARCHIVES_REQUIRED = ["supports_versioning", "supports_range_read", "supports_consistent_list"]


def check_backend(caps: CapabilitySet, required: List[str]) -> Tuple[bool, List[str]]:
    """(admitted, missing) — a backend is admitted for a role iff it provides every required capability."""
    miss = caps.missing(required)
    return (not miss, miss)


class DurableSemanticStore:
    """The bottom interface (plan-s1 §2.1). A backend implements these; nothing above it speaks S3.
    All methods are keyed by a `kind` (a namespace like "archives:demo" or "model:plants_head") and,
    for content, a `gen_id` (the sha256 of the bytes — a generation is immutable and content-named)."""

    name = "abstract"

    def capabilities(self) -> CapabilitySet:
        raise NotImplementedError

    # ── immutable generations ───────────────────────────────────────────────────
    def put_immutable(self, kind: str, data: bytes) -> str:
        """Write `data` as an immutable, hash-named generation under `kind`; return its gen_id (sha256).
        Idempotent (content-addressed): re-putting identical bytes returns the same id, writes once."""
        raise NotImplementedError

    def publish_generation(self, kind: str, data: bytes) -> str:
        """Semantic alias of put_immutable: publish a new generation (does NOT move the pointer — the
        caller CAS-swaps the pointer after verifying the hash, §2.3)."""
        return self.put_immutable(kind, data)

    def read(self, kind: str, gen_id: str) -> bytes:
        raise NotImplementedError

    def read_range(self, kind: str, gen_id: str, offset: int, length: int) -> bytes:
        raise NotImplementedError

    def list_generations(self, kind: str) -> List[str]:
        raise NotImplementedError

    # ── the pointer (which generation is current), moved only by CAS ─────────────
    def resolve_generation(self, kind: str) -> Dict[str, Any]:
        """The current pointer for `kind`: {generation, version} (generation None when unset)."""
        raise NotImplementedError

    def cas_pointer(self, kind: str, expected: Optional[str], new: str) -> bool:
        """Compare-and-swap the `kind` pointer: set it to `new` iff its current generation equals
        `expected` (None ⇒ expect no pointer yet). Returns True on success, False on a losing race."""
        raise NotImplementedError

    # ── the single-writer lease (fenced, §2.5) ──────────────────────────────────
    def acquire_lease(self, holder: str, ttl_s: float = 60.0) -> Optional[Dict[str, Any]]:
        """Acquire (or steal an EXPIRED) writer lease: returns {token, epoch} or None if a live lease is
        held by someone else. The epoch is monotonic — a later holder always has a higher epoch, so a
        stale holder's commits are refused by epoch (the fence)."""
        raise NotImplementedError

    def renew(self, token: str, ttl_s: float = 60.0) -> bool:
        raise NotImplementedError

    def release(self, token: str) -> None:
        raise NotImplementedError

    def lease_state(self) -> Dict[str, Any]:
        """The current lease {holder, epoch, expires} or {} — the watchdog reads this instead of the
        pidfile (§2.5)."""
        raise NotImplementedError


class SemanticArtifactStore:
    """The middle layer (§2.1/§2.6): a derived artifact (macro-cache / materialized Set / projection /
    leaderboard / model weights / snapshot) is identified by its `artifact_id` (§1.4) and stored as an
    immutable generation in the durable store; the artifact_id IS the content identity, so "did we
    recompute the same thing" is a store lookup. Thin over a DurableSemanticStore — no S3 vocabulary."""

    def __init__(self, durable: DurableSemanticStore) -> None:
        self.durable = durable

    def put(self, kind: str, artifact_id: str, data: bytes) -> Dict[str, Any]:
        """Publish an artifact generation and point `<kind>:<artifact_id>` at it (CAS from whatever it
        was). Returns {generation, kind, artifact_id}."""
        gen = self.durable.publish_generation(kind, data)
        cur = self.durable.resolve_generation("%s:%s" % (kind, artifact_id)).get("generation")
        self.durable.cas_pointer("%s:%s" % (kind, artifact_id), cur, gen)
        return {"generation": gen, "kind": kind, "artifact_id": artifact_id}

    def get(self, kind: str, artifact_id: str) -> Optional[bytes]:
        gen = self.durable.resolve_generation("%s:%s" % (kind, artifact_id)).get("generation")
        if not gen:
            return None
        return self.durable.read(kind, gen)

    def capabilities(self) -> CapabilitySet:
        return self.durable.capabilities()
