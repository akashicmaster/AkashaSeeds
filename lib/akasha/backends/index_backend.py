"""Silica's per-bank RAM index — ``route → subkey → ENTRY``.

The index is RAM, always — one implementation, no modes (F33). The set-algebra structure it holds
(collection membership, scope indexes, ``@ALIAS``) MUST be memory-resident: that is the condition
under which Akasha's paid-up-front cost pays out — every needed concept group is enclosed in sets at
write time, so any atom is reachable in one membership lookup (RAM) + one point-get (disk is fine).
A disk-resident index made every nested-scan surface a lock convoy (scan × depth × fan-out under
held bank locks); the access-path DEGREE, not raw size, is what broke — so the cached-index
mechanism was discarded and this reverted to the single RAM implementation.

Per-atom Operand BODIES are the independent residency lever (``SilicaStore`` value_store=disk +
``_route_values_in_ram``): a body ENTRY is then a ``(voff, vlen)`` WAL locator, pread on demand,
while alias/collection/scope values stay RAM-resident. The index stores and returns ENTRY unchanged
— resolution to value bytes is the store's job (``SilicaStore._entry_bytes``), never the index's.

The index is a DERIVED view of the WAL, rebuilt by ``SilicaStore._replay()`` at boot; replay volume
is kept bounded by WAL compaction, not by any persisted index.
"""
from __future__ import annotations

from typing import Dict, Iterator, List, Optional, Tuple

# Op codes — mirror silica.OP_PUT / OP_DEL without importing silica (keep this module standalone so
# it can be unit-tested with no store/WAL dependency).
OP_PUT = 1
OP_DEL = 2

Entry = object          # value bytes (ram-value mode) | (voff, vlen) locator (disk-value mode)


class RamIndex:
    """The per-bank index: today's dict-of-dicts semantics with a SINGLETON-ROUTE collapse so the
    common 1:1 route (chunk store: route=<hash>, subkey=b"C") does NOT pay for a per-route inner
    ``dict``.

    Memory motivation (the deterministic-on-one-load OOM this fixes): the primary chunk store keys
    every Atom as its OWN route (``route = sha256-hex``, ``subkey = b"C"``), so a naive
    ``route → {subkey: entry}`` allocates one inner ``dict`` PER ATOM. A CPython single-entry dict is
    ~232 bytes; at millions of atoms that wrapper alone is multiple GB of pure overhead. Multi-subkey
    routes (aliases / collections / scopes) are the rare case that genuinely needs a dict.

    Representation (private): ``self._idx[route]`` is EITHER
      * a 2-tuple ``(subkey, entry)`` — a route with exactly ONE live subkey (the common case), or
      * a ``dict`` ``{subkey: entry, …}`` — a route with ≥2 live subkeys.
    ``type(bucket) is dict`` distinguishes them; ``entry`` is opaque (value bytes, or a
    ``(voff, vlen)`` locator) and is never a ``dict``, so the test is unambiguous. A route is present
    iff it has ≥1 live subkey (empties are always removed), so ``route in self._idx`` IS "has a live
    subkey". Behaviour — point read, route/subkey scans, counts, insertion order, and the
    PUT-after-DEL-appends rule — is the historical ``Bank.data`` semantics, byte-for-byte.
    """

    __slots__ = ("_idx",)

    def __init__(self) -> None:
        # route -> (subkey, entry) singleton  |  {subkey: entry, …} for ≥2 subkeys
        self._idx: Dict[bytes, object] = {}

    def close(self) -> None:
        pass

    def flush(self) -> None:
        pass

    def clear(self) -> None:
        self._idx.clear()

    def apply(self, op: int, route: bytes, subkey: bytes, entry: Entry = None,
              woff: int = 0, txid: int = 0, coff: int = 0) -> None:
        if op == OP_PUT:
            bucket = self._idx.get(route)
            if bucket is None:
                self._idx[route] = (subkey, entry)          # new route → singleton
            elif type(bucket) is dict:
                bucket[subkey] = entry
            elif bucket[0] == subkey:
                self._idx[route] = (subkey, entry)          # replace the one subkey's entry
            else:
                # 2nd distinct subkey → promote to a dict, old subkey first (insertion order)
                self._idx[route] = {bucket[0]: bucket[1], subkey: entry}
        elif op == OP_DEL:
            bucket = self._idx.get(route)
            if bucket is None:
                return
            if type(bucket) is dict:
                bucket.pop(subkey, None)
                if not bucket:
                    del self._idx[route]
                elif len(bucket) == 1:
                    # shrank back to one subkey → demote to a singleton, reclaiming the dict
                    (sk0, e0), = bucket.items()
                    self._idx[route] = (sk0, e0)
            elif bucket[0] == subkey:
                del self._idx[route]

    def get(self, route: bytes, subkey: bytes) -> Optional[Entry]:
        bucket = self._idx.get(route)
        if bucket is None:
            return None
        if type(bucket) is dict:
            return bucket.get(subkey)
        return bucket[1] if bucket[0] == subkey else None

    def iter_route(self, route: bytes) -> List[Tuple[bytes, Entry]]:
        bucket = self._idx.get(route)
        if bucket is None:
            return []
        if type(bucket) is dict:
            return list(bucket.items())
        return [bucket]                # bucket IS the (subkey, entry) pair

    def iter_route_stream(self, route: bytes):
        bucket = self._idx.get(route)
        if bucket is None:
            return ()
        if type(bucket) is dict:
            return bucket.items()      # live view — zero-copy, identical to today's d.items()
        return (bucket,)               # 1-tuple of the (subkey, entry) pair

    def subkeys(self, route: bytes, prefix: Optional[bytes] = None) -> List[bytes]:
        bucket = self._idx.get(route)
        if bucket is None:
            return []
        if type(bucket) is dict:
            if prefix is None:
                return list(bucket.keys())
            return [sk for sk in bucket.keys() if sk.startswith(prefix)]
        sk0 = bucket[0]
        if prefix is None or sk0.startswith(prefix):
            return [sk0]
        return []

    def count_route(self, route: bytes, subkey_pred=None) -> int:
        bucket = self._idx.get(route)
        if bucket is None:
            return 0
        if type(bucket) is dict:
            if subkey_pred is None:
                return len(bucket)
            n = 0
            for sk in bucket.keys():
                if subkey_pred(sk):
                    n += 1
            return n
        if subkey_pred is None:
            return 1
        return 1 if subkey_pred(bucket[0]) else 0

    def contains_route(self, route: bytes) -> bool:
        return route in self._idx     # present ⟺ ≥1 live subkey (empties are always removed)

    def iter_all(self) -> Iterator[Tuple[bytes, bytes, Entry]]:
        for route, bucket in self._idx.items():
            if type(bucket) is dict:
                for subkey, entry in bucket.items():
                    yield route, subkey, entry
            else:
                yield route, bucket[0], bucket[1]

    def route_count(self) -> int:
        return len(self._idx)

    def route_sizes(self) -> dict:
        """R8/F28c RAM attribution: deep size (approx bytes of keys + value/locator entries +
        container overhead) of each `@`-prefixed bookkeeping route (@ALIAS, @LINK, @SET, …) — the
        bulk-scanned structures that stay RAM-resident — plus ONE aggregate for the millions of
        hash-routed chunk bodies. Only the handful of `@` routes are returned individually; the rest
        is summed so the pass never builds a giant list. O(routes) once, called by MemTop."""
        import sys as _s

        def _esz(e) -> int:
            if e is None:
                return 0
            if isinstance(e, (bytes, bytearray)):
                return len(e) + 33                     # bytes payload + object header
            return _s.getsizeof(e)                     # (voff,vlen) locator tuple (disk mode)

        def _ksz(sk) -> int:
            return (len(sk) + 33) if isinstance(sk, (bytes, bytearray)) else _s.getsizeof(sk)

        at_routes = []
        other_n = 0
        other_bytes = 0
        for route, bucket in self._idx.items():
            if type(bucket) is dict:
                n = len(bucket)
                b = _s.getsizeof(bucket)
                for sk, e in bucket.items():
                    b += _ksz(sk) + _esz(e)
            else:
                n = 1
                b = _s.getsizeof(bucket) + _ksz(bucket[0]) + _esz(bucket[1])
            if route[:1] == b"@":
                at_routes.append((route, n, b))
            else:
                other_n += n
                other_bytes += b
        at_routes.sort(key=lambda t: t[2], reverse=True)
        return {"at_routes": at_routes,
                "other_routes": {"count": other_n, "bytes": other_bytes}}
