"""S1-b §2.2 — the local filesystem DurableSemanticStore (the first, always-available backend).

It proves the FULL writer capability set — CAS + versioning + range read + consistent list + server
time + leases — using only the filesystem: immutable generations are hash-named files; the pointer is
a small JSON file swapped by CAS under an flock, written temp→fsync→atomic-rename→dir-fsync; the lease
is a JSON file with a monotonic epoch, also under flock. The HydraDB lesson (a local backend without a
conditional put broke manifest GC) is the eval: `durable_store_eval` races two writers on cas_pointer.

Layout under `<root>/`:
    <kind>/gen/<sha256>     — immutable generation bytes (content-addressed)
    <kind>/current.json     — the pointer {generation, version}
    <kind>/.lock            — flock target for the pointer CAS
    _lease.json / _lease.lock — the single-writer lease (store-wide)
"""
import errno
import fcntl
import hashlib
import json
import os
import time
import uuid
from typing import Any, Dict, List, Optional

from lib.akasha.storage.base import CapabilitySet, DurableSemanticStore


def _fsync_dir(path: str) -> None:
    try:
        fd = os.open(path, os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    except (OSError, AttributeError):
        pass


def _atomic_write(path: str, data: bytes) -> None:
    """temp in the same dir → fsync the file → atomic rename → fsync the dir (crash-stop durable)."""
    d = os.path.dirname(path)
    os.makedirs(d, exist_ok=True)
    tmp = "%s.tmp.%s" % (path, uuid.uuid4().hex[:8])
    with open(tmp, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    _fsync_dir(d)


class _Flock:
    """A blocking exclusive flock context on a lock file (serialises the CAS read-modify-write)."""

    def __init__(self, path: str):
        self.path = path
        self._fd = None

    def __enter__(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self._fd = os.open(self.path, os.O_CREAT | os.O_RDWR, 0o600)
        fcntl.flock(self._fd, fcntl.LOCK_EX)
        return self

    def __exit__(self, *exc):
        try:
            fcntl.flock(self._fd, fcntl.LOCK_UN)
        finally:
            os.close(self._fd)
            self._fd = None


class LocalDurableStore(DurableSemanticStore):
    name = "local"

    def __init__(self, root: str) -> None:
        self.root = root
        os.makedirs(root, exist_ok=True)

    def capabilities(self) -> CapabilitySet:
        # the filesystem proves every writer capability: flock+rename+fsync = CAS + leases; hash-named
        # files = versioning; seek = range read; a local listdir is consistent; time.time = server time.
        return CapabilitySet(supports_cas=True, supports_versioning=True, supports_range_read=True,
                             supports_consistent_list=True, supports_server_time=True,
                             supports_leases=True)

    # ── paths ────────────────────────────────────────────────────────────────────
    def _kind_dir(self, kind: str) -> str:
        # a kind is a namespace; keep it a single safe path segment
        safe = kind.replace("/", "_").replace("..", "_")
        return os.path.join(self.root, safe)

    def _gen_path(self, kind: str, gen_id: str) -> str:
        return os.path.join(self._kind_dir(kind), "gen", gen_id)

    def _ptr_path(self, kind: str) -> str:
        return os.path.join(self._kind_dir(kind), "current.json")

    def _ptr_lock(self, kind: str) -> str:
        return os.path.join(self._kind_dir(kind), ".lock")

    # ── immutable generations ────────────────────────────────────────────────────
    def put_immutable(self, kind: str, data: bytes) -> str:
        if not isinstance(data, (bytes, bytearray)):
            data = str(data).encode("utf-8")
        gen_id = hashlib.sha256(data).hexdigest()
        path = self._gen_path(kind, gen_id)
        if not os.path.exists(path):          # content-addressed → write once, idempotent
            _atomic_write(path, bytes(data))
        return gen_id

    def read(self, kind: str, gen_id: str) -> bytes:
        with open(self._gen_path(kind, gen_id), "rb") as f:
            return f.read()

    def read_range(self, kind: str, gen_id: str, offset: int, length: int) -> bytes:
        with open(self._gen_path(kind, gen_id), "rb") as f:
            f.seek(max(0, int(offset)))
            return f.read(max(0, int(length)))

    def list_generations(self, kind: str) -> List[str]:
        d = os.path.join(self._kind_dir(kind), "gen")
        try:
            return sorted(os.listdir(d))
        except OSError:
            return []

    # ── the pointer (CAS) ────────────────────────────────────────────────────────
    def resolve_generation(self, kind: str) -> Dict[str, Any]:
        try:
            with open(self._ptr_path(kind), "rb") as f:
                p = json.loads(f.read() or b"{}")
            return {"generation": p.get("generation"), "version": p.get("version", 0)}
        except (OSError, ValueError):
            return {"generation": None, "version": 0}

    def cas_pointer(self, kind: str, expected: Optional[str], new: str) -> bool:
        with _Flock(self._ptr_lock(kind)):
            cur = self.resolve_generation(kind)
            if (cur.get("generation") or None) != (expected or None):
                return False                  # lost the race — current is not what the caller expected
            nxt = {"generation": new, "version": int(cur.get("version", 0)) + 1,
                   "wall": round(time.time(), 3)}
            _atomic_write(self._ptr_path(kind), json.dumps(nxt).encode("utf-8"))
            return True

    # ── the fenced single-writer lease (§2.5) ────────────────────────────────────
    def _lease_path(self) -> str:
        return os.path.join(self.root, "_lease.json")

    def _lease_lock(self) -> str:
        return os.path.join(self.root, "_lease.lock")

    def _read_lease(self) -> Dict[str, Any]:
        try:
            with open(self._lease_path(), "rb") as f:
                return json.loads(f.read() or b"{}") or {}
        except (OSError, ValueError):
            return {}

    def acquire_lease(self, holder: str, ttl_s: float = 60.0) -> Optional[Dict[str, Any]]:
        with _Flock(self._lease_lock()):
            cur = self._read_lease()
            now = time.time()
            live = cur and float(cur.get("expires", 0)) > now and cur.get("holder") != holder
            if live:
                return None                    # a DIFFERENT holder's lease is still live
            token = uuid.uuid4().hex
            epoch = int(cur.get("epoch", 0)) + 1   # monotonic — the fence
            lease = {"holder": holder, "epoch": epoch, "token": token,
                     "expires": now + float(ttl_s), "acquired": round(now, 3)}
            _atomic_write(self._lease_path(), json.dumps(lease).encode("utf-8"))
            return {"token": token, "epoch": epoch}

    def renew(self, token: str, ttl_s: float = 60.0) -> bool:
        with _Flock(self._lease_lock()):
            cur = self._read_lease()
            if cur.get("token") != token or float(cur.get("expires", 0)) <= time.time():
                return False                   # not ours, or already expired (fenced out)
            cur["expires"] = time.time() + float(ttl_s)
            _atomic_write(self._lease_path(), json.dumps(cur).encode("utf-8"))
            return True

    def release(self, token: str) -> None:
        with _Flock(self._lease_lock()):
            cur = self._read_lease()
            if cur.get("token") == token:
                # keep the epoch (monotonic across releases) but clear the holder/expiry
                nxt = {"holder": None, "epoch": int(cur.get("epoch", 0)), "token": None, "expires": 0}
                _atomic_write(self._lease_path(), json.dumps(nxt).encode("utf-8"))

    def lease_state(self) -> Dict[str, Any]:
        cur = self._read_lease()
        if not cur:
            return {}
        return {"holder": cur.get("holder"), "epoch": cur.get("epoch"),
                "expires": cur.get("expires"), "live": float(cur.get("expires", 0)) > time.time()}
