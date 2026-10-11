"""S1-b §2.7 — an S3 / MinIO DurableSemanticStore LIMITED to the capabilities the archives move needs.

The VPS `archives/` (static portals + assets) become the first *published generation*: the seed writes
them immutably, hash-named per release, behind one `current` pointer per site; a portal (this host or a
replica) resolves `archives/<site>` through `resolve_generation` and serves ranges. For THIS use the
backend needs only immutable put + read + range read + consistent list + a pointer — NO CAS beyond the
pointer, NO lease. So this backend declares `supports_cas=False` / `supports_leases=False`: the
capability check ADMITS it as an archives mirror and REFUSES it as the store's writer backend
(`[store] … missing=supports_cas,supports_leases → read-only`). A full object-store writer backend
(conditional put for CAS, a CAS lease object) is S1-c, not this slice.

boto3 is OPTIONAL (degradation-first, like the vision observers): absent ⇒ the backend still declares
its capabilities (so the negotiation is testable) but every I/O method raises a clear, single error
rather than importing at module load. It is NEVER pip-installed at run time on a production tier.
"""
from typing import Any, Dict, List, Optional

from lib.akasha.storage.base import CapabilitySet, DurableSemanticStore


def boto3_available() -> bool:
    try:
        import boto3  # noqa: F401
        return True
    except Exception:
        return False


class S3DurableStore(DurableSemanticStore):
    """An S3/MinIO-backed archives mirror. `bucket` + optional `endpoint_url` (MinIO) + `prefix`."""

    name = "s3"

    def __init__(self, bucket: str, endpoint_url: str = "", prefix: str = "",
                 region: str = "", client: Any = None) -> None:
        self.bucket = bucket
        self.endpoint_url = endpoint_url or None
        self.prefix = (prefix or "").strip("/")
        self.region = region or None
        self._client = client            # injectable for tests; else lazily built from boto3

    def capabilities(self) -> CapabilitySet:
        # what a PLAIN bucket proves: immutable objects (versioning), byte-range GET, strongly-
        # consistent list, a server clock. NOT conditional-put CAS, NOT a fenced lease — so it is an
        # archives mirror, refused as a writer backend by check_backend(WRITER_REQUIRED).
        return CapabilitySet(supports_cas=False, supports_versioning=True, supports_range_read=True,
                             supports_consistent_list=True, supports_server_time=True,
                             supports_leases=False)

    # ── lazy client (never imports boto3 at module load; never pip) ────────────────
    def _s3(self):
        if self._client is not None:
            return self._client
        if not boto3_available():
            raise RuntimeError("[store] s3 backend unavailable: boto3 is not installed "
                               "(prepared as the environment on a production tier, never pip at run time)")
        import boto3
        self._client = boto3.client("s3", endpoint_url=self.endpoint_url, region_name=self.region)
        return self._client

    def _key(self, kind: str, *parts: str) -> str:
        segs = [p for p in [self.prefix, kind.replace("/", "_")] + list(parts) if p]
        return "/".join(segs)

    # ── immutable generations ────────────────────────────────────────────────────
    def put_immutable(self, kind: str, data: bytes) -> str:
        import hashlib
        if not isinstance(data, (bytes, bytearray)):
            data = str(data).encode("utf-8")
        gen_id = hashlib.sha256(data).hexdigest()
        self._s3().put_object(Bucket=self.bucket, Key=self._key(kind, "gen", gen_id), Body=bytes(data))
        return gen_id

    def read(self, kind: str, gen_id: str) -> bytes:
        obj = self._s3().get_object(Bucket=self.bucket, Key=self._key(kind, "gen", gen_id))
        return obj["Body"].read()

    def read_range(self, kind: str, gen_id: str, offset: int, length: int) -> bytes:
        end = int(offset) + int(length) - 1
        obj = self._s3().get_object(Bucket=self.bucket, Key=self._key(kind, "gen", gen_id),
                                    Range="bytes=%d-%d" % (int(offset), end))
        return obj["Body"].read()

    def list_generations(self, kind: str) -> List[str]:
        pfx = self._key(kind, "gen") + "/"
        out: List[str] = []
        token = None
        while True:
            kw = {"Bucket": self.bucket, "Prefix": pfx}
            if token:
                kw["ContinuationToken"] = token
            resp = self._s3().list_objects_v2(**kw)
            for it in resp.get("Contents", []) or []:
                out.append(it["Key"].rsplit("/", 1)[-1])
            if not resp.get("IsTruncated"):
                break
            token = resp.get("NextContinuationToken")
        return sorted(out)

    # ── the pointer (a small object; NO conditional-put CAS in this slice) ─────────
    def resolve_generation(self, kind: str) -> Dict[str, Any]:
        import json
        try:
            obj = self._s3().get_object(Bucket=self.bucket, Key=self._key(kind, "current.json"))
            p = json.loads(obj["Body"].read() or b"{}")
            return {"generation": p.get("generation"), "version": p.get("version", 0)}
        except Exception:
            return {"generation": None, "version": 0}

    def cas_pointer(self, kind: str, expected: Optional[str], new: str) -> bool:
        # This backend does NOT prove CAS (supports_cas=False), so it must not be used as a writer
        # store. The archives pointer is written by the seed writer out of band (last-writer-wins over a
        # single release), not raced. Refuse a CAS here so a mis-wired writer fails loudly.
        raise RuntimeError("[store] s3 backend does not support cas_pointer (archives mirror only)")

    # ── leases (unsupported — archives mirror is read-mostly) ─────────────────────
    def acquire_lease(self, holder: str, ttl_s: float = 60.0) -> Optional[Dict[str, Any]]:
        raise RuntimeError("[store] s3 backend does not support leases (archives mirror only)")

    def renew(self, token: str, ttl_s: float = 60.0) -> bool:
        raise RuntimeError("[store] s3 backend does not support leases (archives mirror only)")

    def release(self, token: str) -> None:
        return None

    def lease_state(self) -> Dict[str, Any]:
        return {}
