"""
Silica — a hardware-mappable pseudo-ISA memory store (Slice A: the engine).

NOT a SQLite re-implementation.  A small instruction set (~16 opcodes) over
hardware-shaped structures — hashed SRAM *banks*, an append log to NVRAM, a
bank-select address decode — that composes the whole store.  The same algorithm
runs on today's hardware, an FPGA/ASIC tomorrow, and (immutable records + append
log + idempotent replay) a distributed substrate.  Design + opcode table:
docs/for-llm/silica-store-pseudo-isa-spec.md.

This module is the ENGINE only: a banked, durable, transactional two-level
key→value map — `store.begin() → txn.put/delete → commit/abort`, `store.get`,
`store.scan`.  Slice B (SilicaBackend) maps the 59-method AkashaBackend ISA onto
it and is a drop-in for SQLiteBackend.

Data model (see spec §1):
  route  — the co-location tag; picks the bank (bank = crc32(route) & (N-1)).
  subkey — the sub-address within a route.  (route, subkey) → value bytes.
  A whole logical unit sharing one `route` lands in ONE bank → a cheap
  single-bank atomic commit; different routes spread across banks → parallel.

Crash-stop (spec §3): durability lives only at commit; a torn WAL tail is
detected on replay (length+CRC) and dropped, so only the in-flight txn is lost.
"""

import os
import errno
import struct
import zlib
import threading
from collections import OrderedDict
from typing import Dict, List, Optional, Tuple, Iterator

# ── Opcodes (the instruction set) ────────────────────────────────────────────
OP_PUT     = 1     # write (route, subkey) = val
OP_DEL     = 2     # remove (route, subkey)
OP_COMMIT  = 3     # single-bank commit marker for txid
OP_PREPARE = 4     # cross-bank prepare marker (needs a coordinator COMMIT)

_HDR = struct.Struct("<II")          # frame: [reclen u32][crc32 u32]
_PAY = struct.Struct("<BQII")        # payload head: [op u8][txid u64][klen u32][vlen u32]
_RLEN = struct.Struct("<I")          # record key = [rlen u32][route][subkey] (route may hold \x00)


def _compose(route: bytes, subkey: bytes) -> bytes:
    """Pack (route, subkey) into one record key — length-prefixed so a route
    containing NUL bytes is still split unambiguously."""
    return _RLEN.pack(len(route)) + route + subkey


def _split(key: bytes) -> Tuple[bytes, bytes]:
    rlen = _RLEN.unpack_from(key, 0)[0]
    return key[4:4 + rlen], key[4 + rlen:]


# ── LREC / LAPP / LREPLAY — the durable append log ───────────────────────────
def _frame(op: int, txid: int, key: bytes, val: bytes) -> bytes:
    """LREC — frame one record as len·crc·op·txid·klen·k·vlen·v (torn-tail safe)."""
    payload = _PAY.pack(op, txid, len(key), len(val)) + key + val
    return _HDR.pack(len(payload), zlib.crc32(payload) & 0xFFFFFFFF) + payload


def _iter_frames(blob: bytes) -> Iterator[Tuple[int, int, bytes, bytes]]:
    """LREPLAY — decode records, STOPPING at the first torn/corrupt frame."""
    off, n = 0, len(blob)
    while off + _HDR.size <= n:
        reclen, crc = _HDR.unpack_from(blob, off)
        start = off + _HDR.size
        end = start + reclen
        if end > n:
            break                                    # torn tail — record half-written
        payload = blob[start:end]
        if (zlib.crc32(payload) & 0xFFFFFFFF) != crc:
            break                                    # corrupt — stop (last-write-only)
        op, txid, klen, vlen = _PAY.unpack_from(payload, 0)
        kstart = _PAY.size
        key = payload[kstart:kstart + klen]
        val = payload[kstart + klen:kstart + klen + vlen]
        yield op, txid, key, val
        off = end


def _iter_frames_off(blob: bytes) -> Iterator[Tuple[int, int, bytes, bytes, int]]:
    """Like _iter_frames, but also yields the ABSOLUTE offset of the value bytes within
    `blob` (== the file offset, since replay reads the whole file). A disk-resident index
    records (voff, vlen) so it can pread the value later instead of holding it in RAM."""
    off, n = 0, len(blob)
    while off + _HDR.size <= n:
        reclen, crc = _HDR.unpack_from(blob, off)
        start = off + _HDR.size
        end = start + reclen
        if end > n:
            break
        payload = blob[start:end]
        if (zlib.crc32(payload) & 0xFFFFFFFF) != crc:
            break
        op, txid, klen, vlen = _PAY.unpack_from(payload, 0)
        kstart = _PAY.size
        key = payload[kstart:kstart + klen]
        val = payload[kstart + klen:kstart + klen + vlen]
        voff = start + _PAY.size + klen               # absolute file offset of the value bytes
        yield op, txid, key, val, voff
        off = end


class Wal:
    """A single append-only log segment (per bank, and one coordinator).

    LAPP appends (buffered); LSYNC is the fsync barrier; LCKPT rewrites the log
    as a snapshot and truncates it (bounded growth, explicit — not a hidden
    auto-checkpoint)."""

    def __init__(self, path: str, sync_full: bool = True):
        self.path = path
        self.sync_full = sync_full
        self._fh = open(path, "ab", buffering=0)
        self._woff = os.path.getsize(path)   # next append offset (== current file size)
        self._rfd = None                     # lazily-opened read fd for pread (disk-value mode)
        # Guards the read-fd lifecycle. pread runs on ARBITRARY caller threads (a read is not on
        # the WriteQueue), while _reopen_rfd / close can close the fd from another thread — most
        # dangerously SilicaStore.close(), which closes every bank's fd WITHOUT taking bank.lock
        # (scan/checkpoint are already mutually exclusive under bank.lock; close was the hole). A
        # reader mid-pread on a fd that close() just shut → `os.pread` raises OSError EBADF (errno 9)
        # and, uncaught in the boot-load thread, aborts the whole ontology load — leaving atoms
        # whose content chunk never got read (the empty-recipe-body symptom) and a destabilised
        # daemon. This lock makes pread and every fd-close mutually exclusive.
        self._rfd_lock = threading.Lock()
        self._closed = False                 # set by close(); a late read still serves off disk

    def append(self, frame: bytes) -> int:           # LAPP — returns the frame's start offset
        off = self._woff
        self._fh.write(frame)
        self._woff += len(frame)
        return off

    def pread(self, off: int, length: int) -> bytes:  # positional read of value bytes (disk mode)
        if not length:
            return b""
        with self._rfd_lock:
            if self._closed:
                # Store closed (teardown/shutdown) but the file is STILL on disk — serve the read
                # off a short-lived fd so a late reader never crashes and never leaks a cached fd.
                fd = os.open(self.path, os.O_RDONLY)
                try:
                    return os.pread(fd, length, off)
                finally:
                    os.close(fd)
            if self._rfd is None:
                self._rfd = os.open(self.path, os.O_RDONLY)
            try:
                return os.pread(self._rfd, length, off)
            except OSError as exc:
                if exc.errno != errno.EBADF:
                    raise
                # The fd went stale under us (a concurrent replace/close closed it). The file on
                # disk is intact — reopen once and retry. This turns the old fatal EBADF into a
                # transparent recovery, so a read can never crash the writer or abort the load.
                try:
                    os.close(self._rfd)
                except OSError:
                    pass
                self._rfd = os.open(self.path, os.O_RDONLY)
                return os.pread(self._rfd, length, off)

    def fsync(self) -> None:                          # LSYNC — durability fence
        self._fh.flush()
        os.fsync(self._fh.fileno())

    def read_all(self) -> bytes:
        with open(self.path, "rb") as f:
            return f.read()

    def _reopen_rfd(self) -> None:
        with self._rfd_lock:                 # mutually exclusive with pread — never close a fd mid-read
            if self._rfd is not None:
                try:
                    os.close(self._rfd)
                except OSError:
                    pass
                self._rfd = None             # reopened lazily on next pread (new inode after replace)

    def rewrite(self, frames: List[bytes]) -> None:   # LCKPT tail — atomic replace
        tmp = self.path + ".ckpt"
        with open(tmp, "wb") as f:
            f.write(b"".join(frames))
            f.flush()
            os.fsync(f.fileno())
        self._fh.close()
        os.replace(tmp, self.path)
        self._fh = open(self.path, "ab", buffering=0)
        self._woff = os.path.getsize(self.path)
        self._reopen_rfd()               # the old inode is gone — drop the stale read fd

    def close(self) -> None:
        try:
            self._fh.close()
        except Exception:
            pass
        with self._rfd_lock:                 # inline (don't call _reopen_rfd — the lock isn't reentrant)
            self._closed = True              # a read after this serves off a short-lived fd (see pread)
            if self._rfd is not None:
                try:
                    os.close(self._rfd)
                except OSError:
                    pass
                self._rfd = None


# ── The bank — one independent single-writer unit ────────────────────────────
class Bank:
    """One bank: an in-RAM two-level index (route → subkey → ENTRY) rebuilt from its own
    WAL on boot, plus a lock making it a single-writer unit.  Different banks proceed
    concurrently — the hardware way to write non-conflicting namespaces at the same time.

    ENTRY is the value bytes in RAM mode (`disk=False`); in disk-value mode (`disk=True`)
    it is a `(voff, vlen)` location and the value bytes stay on the WAL — read on demand via
    `wal.pread`. Disk mode bounds resident RAM to keys + 2 small ints per record, so a large
    ontology no longer has to fit its full content in memory."""

    def __init__(self, bank_id: int, wal: Wal, disk: bool = False):
        self.id = bank_id
        self.wal = wal
        self.disk = disk
        self.lock = threading.Lock()
        self.data: Dict[bytes, Dict[bytes, object]] = {}   # ENTRY: bytes (ram) | (voff,vlen) (disk)

    # HPUT / HDEL — apply a decoded record to the primary index. In disk mode the value is
    # NOT stored; only its WAL location (voff, vlen) is.
    def _apply(self, op: int, key: bytes, val: bytes, voff: int = 0, vlen: int = 0) -> None:
        route, subkey = _split(key)
        if op == OP_PUT:
            self.data.setdefault(route, {})[subkey] = (voff, vlen) if self.disk else val
        elif op == OP_DEL:
            d = self.data.get(route)
            if d is not None:
                d.pop(subkey, None)
                if not d:
                    self.data.pop(route, None)

    def get_entry(self, route: bytes, subkey: bytes):               # HGET → ENTRY (unresolved)
        d = self.data.get(route)
        return None if d is None else d.get(subkey)

    def entries(self, route: bytes) -> List[Tuple[bytes, object]]:  # SCAN → [(subkey, ENTRY)]
        with self.lock:
            d = self.data.get(route)
            return list(d.items()) if d else []


# ── The transaction — the fence unit (TBEGIN/TSTAGE/TCOMMIT/TABORT) ───────────
class Txn:
    """Stages PUT/DEL ops (read-your-writes), then commits atomically.  Single
    touched bank → fast path (one fsync, parallel with other banks); ≥2 banks →
    two-phase via the coordinator.  Abort just drops staging (nothing reached
    disk); a fault mid-commit is reverted on replay (no coordinator COMMIT)."""

    def __init__(self, store: "SilicaStore"):
        self._store = store
        self._staged: "OrderedDict[Tuple[bytes, bytes], Optional[bytes]]" = OrderedDict()
        self._done = False

    def put(self, route: bytes, subkey: bytes, val: bytes) -> None:      # TSTAGE
        self._staged[(route, subkey)] = val

    def delete(self, route: bytes, subkey: bytes) -> None:               # TSTAGE
        self._staged[(route, subkey)] = None

    def get(self, route: bytes, subkey: bytes) -> Optional[bytes]:
        if (route, subkey) in self._staged:                             # read-your-writes
            return self._staged[(route, subkey)]
        return self._store.get(route, subkey)

    def abort(self) -> None:                                            # TABORT
        self._staged.clear()
        self._done = True

    def commit(self) -> None:                                          # TCOMMIT
        if self._done:
            raise RuntimeError("txn already finished")
        self._done = True
        if not self._staged:
            return
        self._store._commit_txn(self._staged)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if not self._done:
            self.abort() if exc_type else self.commit()


# ── Read value cache — scan-resistant (SLRU) + byte-budgeted + instrumented ───
_MISSING = object()   # sentinel so a cached negative (value None) is distinguished from absent


class _SLRUCache:
    """Segmented-LRU value cache for the disk-value read path (Step 1 of the cache strategy).

    Two byte-budgeted LRU segments — a *probationary* queue for first-time sightings and a
    *protected* queue for values seen ≥2 times. A big one-shot scan (scan_all / gap.scan) only
    churns the probationary segment, so the hot protected set survives it (scan resistance). The
    budget is BYTES, not entries, so a few large values (baked semantic vectors) can't evict many
    small hot ones. Every access is counted, so the higher cache strategies (working-set pinning,
    semantic prefetch) can be tuned against measured hit-rate rather than guessed."""

    __slots__ = ("_prot", "_prob", "_cap", "_prot_cap", "_bytes", "_prot_bytes", "_lock",
                 "hits", "misses", "evictions", "inserts")

    _MISS_COST = 24            # nominal bytes charged to a cached negative (missing key) lookup

    def __init__(self, budget_bytes: int):
        self._cap = max(1 << 16, int(budget_bytes))     # ≥64 KiB
        self._prot_cap = (self._cap * 4) // 5           # ~80% protected, ~20% probationary
        self._prot: "OrderedDict[object, bytes]" = OrderedDict()
        self._prob: "OrderedDict[object, bytes]" = OrderedDict()
        self._bytes = 0            # total resident cost (both segments)
        self._prot_bytes = 0       # protected-segment cost, maintained incrementally (O(1) evict)
        self._lock = threading.Lock()
        self.hits = self.misses = self.evictions = self.inserts = 0

    @staticmethod
    def _cost(val: Optional[bytes]) -> int:
        return _SLRUCache._MISS_COST if val is None else (len(val) + 40)

    # ── segment moves, each maintaining both byte counters in O(1) ──
    def _to_prot(self, key, val) -> None:
        self._prot[key] = val
        self._prot_bytes += self._cost(val)

    def get(self, key) -> Tuple[bool, Optional[bytes]]:
        with self._lock:
            if key in self._prot:
                self._prot.move_to_end(key)
                self.hits += 1
                return True, self._prot[key]
            if key in self._prob:                       # promote: seen twice → protected
                val = self._prob.pop(key)
                self._to_prot(key, val)
                self._evict_locked()
                self.hits += 1
                return True, val
            self.misses += 1
            return False, None

    def put(self, key, val: Optional[bytes]) -> None:
        """Cold-fill from a read miss: insert-if-absent into probationary (a one-shot scan dies
        there without touching the protected hot set)."""
        with self._lock:
            if key in self._prot or key in self._prob:
                return
            self._prob[key] = val
            self._bytes += self._cost(val)
            self.inserts += 1
            self._evict_locked()

    def overwrite(self, key, val: Optional[bytes]) -> None:
        """Write-warm on commit — REFRESH ONLY. If we are already caching this key (a hot value, or
        a cached negative left by a prior read), make it agree with what was just durably written;
        if the key is not tracked, do nothing. Two payoffs, no cost:

          • Correctness — the refresh happens under the bank lock (see SilicaStore.get), so a
            concurrent read that preads the old value can no longer re-cache it over a newer commit
            (the stale-recache race the old post-lock invalidate had).
          • The measured COLD-weave gap — a freshly-minted proto-word hub is read (get→None caches a
            negative), then written; this replaces that negative with the real key, so the next word
            referencing the hub HITS instead of re-preading.

        It deliberately does NOT populate a brand-new key: write-once values (word bodies, link and
        index rows) that were never read stay out of the cache, so a bulk ontology load can't churn
        the hot read set. val=None (a committed delete) drops any cached entry."""
        with self._lock:
            if val is None:
                self._invalidate_locked(key)
                return
            if key in self._prot:
                self._prot_bytes += self._cost(val) - self._cost(self._prot[key])
                self._bytes += self._cost(val) - self._cost(self._prot[key])
                self._prot[key] = val
                self._prot.move_to_end(key)
                self._evict_locked()
            elif key in self._prob:
                self._bytes += self._cost(val) - self._cost(self._prob[key])
                self._prob[key] = val
                self._prob.move_to_end(key)
                self._evict_locked()
            # else: key not tracked → skip (no populate → no write-once pollution)

    def _invalidate_locked(self, key) -> None:
        v = self._prot.pop(key, _MISSING)
        if v is not _MISSING:
            self._prot_bytes -= self._cost(v)
            self._bytes -= self._cost(v)
            return
        v = self._prob.pop(key, _MISSING)
        if v is not _MISSING:
            self._bytes -= self._cost(v)

    def invalidate(self, key) -> None:
        with self._lock:
            self._invalidate_locked(key)

    def clear(self) -> None:
        with self._lock:
            self._prot.clear(); self._prob.clear()
            self._bytes = 0; self._prot_bytes = 0

    def _evict_locked(self) -> None:
        # Keep protected within its sub-budget by demoting its LRU into probationary (O(1) each,
        # using the incrementally-maintained counters — no full-segment scan on the write path).
        while self._prot and self._prot_bytes > self._prot_cap:
            k, v = self._prot.popitem(last=False)
            self._prot_bytes -= self._cost(v)
            self._prob[k] = v
        # Total budget: evict probationary LRU first (one-shot scans die here).
        while self._bytes > self._cap and (self._prob or self._prot):
            if self._prob:
                _k, v = self._prob.popitem(last=False)
            else:
                _k, v = self._prot.popitem(last=False)
                self._prot_bytes -= self._cost(v)
            self._bytes -= self._cost(v)
            self.evictions += 1

    def stats(self) -> dict:
        with self._lock:
            total = self.hits + self.misses
            return {"entries": len(self._prot) + len(self._prob),
                    "protected": len(self._prot), "probationary": len(self._prob),
                    "bytes": self._bytes, "budget": self._cap,
                    "hits": self.hits, "misses": self.misses,
                    "hit_rate": (self.hits / total) if total else 0.0,
                    "evictions": self.evictions, "inserts": self.inserts}


# ── The store — banks + coordinator + boot replay + checkpoint + cache ────────
class SilicaStore:
    def __init__(self, path_dir: str, banks: int = 8, sync: str = "full",
                 cache_size: int = 4096, value_store: str = "ram"):
        if banks & (banks - 1) != 0:
            raise ValueError("banks must be a power of two")
        self._dir = os.path.abspath(path_dir)
        os.makedirs(self._dir, exist_ok=True)
        self._n = banks
        self._mask = banks - 1
        self._sync_full = (sync == "full")
        # Value residency: "ram" keeps values in the index (fast, but the whole dataset must fit
        # in RAM); "disk" keeps only a (offset,len) location and preads the value from the WAL on
        # demand (a large ontology no longer has to be RAM-resident). The on-disk WAL format is
        # identical either way, so a store written in one mode reads back in the other.
        self._disk = str(value_store).strip().lower() in ("disk", "file", "mmap")
        self._txid = 0
        self._txid_lock = threading.Lock()
        self._banks = [Bank(i, Wal(os.path.join(self._dir, f"bank-{i:03d}.wal"),
                                   self._sync_full), disk=self._disk) for i in range(banks)]
        self._coord = Wal(os.path.join(self._dir, "coord.wal"), self._sync_full)
        # The read cache accelerates the DISK-value path only (in RAM mode the bank index already
        # IS the value, so caching would just double-store it). Byte budget: AKASHA_SILICA_CACHE_MB.
        try:
            _mb = float(os.environ.get("AKASHA_SILICA_CACHE_MB", "64"))
        except ValueError:
            _mb = 64.0
        self._cache = _SLRUCache(int(_mb * 1024 * 1024)) if self._disk else None
        self._replay()

    # BSEL — bank select (address decode).
    def _bank_of(self, route: bytes) -> Bank:
        return self._banks[zlib.crc32(route) & self._mask]

    def _next_txid(self) -> int:
        with self._txid_lock:
            self._txid += 1
            return self._txid

    def next_id(self) -> int:
        """A monotonic id (shares the txid counter → monotonic across reopen once the
        WAL is replayed).  Used by the backend for autoincrement ids / FIFO ordering."""
        return self._next_txid()

    # ── read path (CGET → HGET) ───────────────────────────────────────────────
    def _entry_bytes(self, bank: Bank, entry) -> Optional[bytes]:
        """Resolve an index ENTRY to value bytes. Lock-free: the CALLER must hold bank.lock
        when in disk mode (so a pread cannot race a checkpoint rewriting the same WAL)."""
        if entry is None:
            return None
        if not self._disk:
            return entry                       # entry IS the value
        return bank.wal.pread(entry[0], entry[1])

    def get(self, route: bytes, subkey: bytes) -> Optional[bytes]:
        bank = self._bank_of(route)
        if not self._disk:                     # RAM mode: the index entry IS the value
            return self._entry_bytes(bank, bank.get_entry(route, subkey))
        ck = (route, subkey)
        hit, val = self._cache.get(ck)
        if hit:
            return val
        with bank.lock:                        # cold: pread + cold-fill under the lock, so the fill
            val = self._entry_bytes(bank, bank.get_entry(route, subkey))   # cannot race a
            self._cache.put(ck, val)           # concurrent commit's write-warm and re-cache a stale
        return val                             # value (bank.lock ⊃ cache lock — one consistent order)

    def scan(self, route: bytes) -> List[Tuple[bytes, bytes]]:
        """All (subkey, value) under one route — a single-bank prefix walk."""
        bank = self._bank_of(route)
        if self._disk:
            with bank.lock:
                d = bank.data.get(route)
                items = list(d.items()) if d else []
                return [(sk, self._entry_bytes(bank, e)) for sk, e in items]
        return [(sk, self._entry_bytes(bank, e)) for sk, e in bank.entries(route)]

    def scan_route_topk(self, route: bytes, k: int, key_fn,
                        subkey_pred=None) -> List[Tuple[bytes, bytes]]:
        """Top-`k` (subkey, value) under one route by `key_fn(value)` — memory O(k), NOT O(route
        size). Unlike scan(), which materializes EVERY value first (in disk mode it preads them
        all), this streams the route: it reads one value at a time and keeps only the running
        top-k in a bounded min-heap, discarding the rest. That is what stops a mega-hub's incoming
        fan-out (a country/company pointed at by hundreds of thousands of atoms) from allocating
        O(density) memory and OOM-killing the process on a single dive. `subkey_pred(subkey)`, if
        given, filters on the SUBKEY *before* the value is read — so unrelated entries sharing the
        route (an atom's route also holds its chunk/aliases/outgoing edges) are skipped without a
        pread. The bank lock is held for the walk (same as scan()), so disk-mode preads cannot
        race a checkpoint."""
        import heapq
        bank = self._bank_of(route)
        heap: List[Tuple] = []       # (key, seq, subkey, value) min-heap of the running top-k
        seq = 0
        with bank.lock:
            d = bank.data.get(route)
            if d:
                for subkey, entry in d.items():
                    if subkey_pred is not None and not subkey_pred(subkey):
                        continue
                    val = self._entry_bytes(bank, entry)
                    if val is None:
                        continue
                    kv = key_fn(val)
                    if len(heap) < k:
                        heapq.heappush(heap, (kv, seq, subkey, val)); seq += 1
                    elif kv > heap[0][0]:
                        heapq.heapreplace(heap, (kv, seq, subkey, val)); seq += 1
        heap.sort(key=lambda t: t[0], reverse=True)
        return [(sk, v) for _k, _s, sk, v in heap]

    def scan_subkeys(self, route: bytes, prefix: bytes = None) -> List[bytes]:
        """Subkeys under one route (optionally only those starting with `prefix`), WITHOUT
        reading any value. Several per-key lookups — aliases, access scopes, collection
        membership — encode all the data they need IN the subkey (`<PFX><payload>`), so they
        never need the value at all. scan() would pread every value in the route first; on a
        mega-hub whose route also holds tens of thousands of link values, that turned an
        alias/access lookup into a full O(density) pread storm (the dominant dive latency).
        This touches keys only."""
        bank = self._bank_of(route)
        with bank.lock:
            d = bank.data.get(route)
            if not d:
                return []
            if prefix is None:
                return list(d.keys())
            return [sk for sk in d.keys() if sk.startswith(prefix)]

    def count_route_subkeys(self, route: bytes, subkey_pred=None) -> int:
        """Count subkeys under one route (optionally filtered by `subkey_pred(subkey)`)
        WITHOUT reading any value. This is the branch-count cue's path: a signpost only
        needs "how many edges ahead", never their contents, so — unlike scan_route_topk,
        which preads every value to rank by weight — this touches keys only. On a mega-hub
        neighbour in disk mode that turns a per-signpost pread storm into an O(1)-ish dict
        walk, which is what makes a dense-hub dive fast."""
        bank = self._bank_of(route)
        with bank.lock:
            d = bank.data.get(route)
            if not d:
                return 0
            if subkey_pred is None:
                return len(d)
            n = 0
            for subkey in d.keys():
                if subkey_pred(subkey):
                    n += 1
            return n

    def scan_all(self) -> Iterator[Tuple[bytes, bytes, bytes]]:
        """(route, subkey, value) across every bank — the rare global scan
        (LIKE over the whole keyspace).  Snapshots each bank under its lock."""
        for bank in self._banks:
            with bank.lock:
                # Resolve under the lock so disk-mode preads cannot race a checkpoint.
                out = [(route, subkey, self._entry_bytes(bank, entry))
                       for route, d in bank.data.items()
                       for subkey, entry in d.items()]
            for row in out:
                yield row

    # ── write path ────────────────────────────────────────────────────────────
    def begin(self) -> Txn:                                              # TBEGIN
        return Txn(self)

    def _commit_txn(self, staged: "OrderedDict[Tuple[bytes, bytes], Optional[bytes]]") -> None:
        # Group staged ops by bank. Carry the (route,subkey) cache key alongside so the disk-mode
        # cache can be write-warmed under the same bank lock that applies the frame.
        by_bank: Dict[int, List[Tuple[int, bytes, bytes]]] = {}
        cache_by_bank: Dict[int, List[Tuple[Tuple[bytes, bytes], Optional[bytes]]]] = {}
        for (route, subkey), val in staged.items():
            b = self._bank_of(route)
            op = OP_DEL if val is None else OP_PUT
            by_bank.setdefault(b.id, []).append(
                (op, _compose(route, subkey), b"" if val is None else val))
            if self._cache is not None:
                cache_by_bank.setdefault(b.id, []).append(((route, subkey), val))
        txid = self._next_txid()
        bank_ids = sorted(by_bank)

        # Append one frame and return the (op, key, val, voff, vlen) needed to index it —
        # voff is the absolute file offset of the value bytes, so disk mode can pread it later.
        def _append(bank: Bank, op: int, key: bytes, val: bytes):
            foff = bank.wal.append(_frame(op, txid, key, val))
            return (op, key, val, foff + _HDR.size + _PAY.size + len(key), len(val))

        if len(bank_ids) == 1:
            # Fast path — one bank, one commit marker, one fsync.  Fully parallel.
            bank = self._banks[bank_ids[0]]
            with bank.lock:
                applied = [_append(bank, op, key, val) for op, key, val in by_bank[bank.id]]
                bank.wal.append(_frame(OP_COMMIT, txid, b"", b""))
                if self._sync_full:
                    bank.wal.fsync()
                for op, key, val, voff, vlen in applied:
                    bank._apply(op, key, val, voff, vlen)
                if self._cache is not None:    # write-warm under the lock (correctness + COLD gap)
                    for ck, v in cache_by_bank.get(bank.id, ()):
                        self._cache.overwrite(ck, v)
        else:
            # Two-phase — prepare each bank, then the atomic coordinator commit.
            locked = [self._banks[i] for i in bank_ids]     # ascending id → deadlock-free
            for bank in locked:
                bank.lock.acquire()
            try:
                staged_apply: Dict[int, list] = {}
                for bank in locked:
                    staged_apply[bank.id] = [_append(bank, op, key, val)
                                             for op, key, val in by_bank[bank.id]]
                    bank.wal.append(_frame(OP_PREPARE, txid, b"", b""))
                    if self._sync_full:
                        bank.wal.fsync()
                self._coord.append(_frame(OP_COMMIT, txid, b"", b""))   # the atomic point
                if self._sync_full:
                    self._coord.fsync()
                for bank in locked:
                    for op, key, val, voff, vlen in staged_apply[bank.id]:
                        bank._apply(op, key, val, voff, vlen)
                    if self._cache is not None:    # write-warm while all bank locks are held
                        for ck, v in cache_by_bank.get(bank.id, ()):
                            self._cache.overwrite(ck, v)
            finally:
                for bank in reversed(locked):
                    bank.lock.release()

    # ── LCKPT — explicit checkpoint (fold live index → fresh log, truncate) ────
    def checkpoint(self) -> None:
        for bank in self._banks:
            with bank.lock:
                # Snapshot the live records as one committed txn. In disk mode the values are
                # read back from the WAL (they are not in RAM); in RAM mode the entry IS the value.
                frames = [_frame(OP_PUT, 1, _compose(route, subkey),
                                 self._entry_bytes(bank, entry) or b"")
                          for route, d in bank.data.items() for subkey, entry in d.items()]
                frames.append(_frame(OP_COMMIT, 1, b"", b""))
                bank.wal.rewrite(frames)
                if self._disk:
                    # Offsets changed under the compaction — rebuild the location index from the
                    # freshly written (compact) WAL so every entry points at its new position.
                    bank.data.clear()
                    for op, _txid, key, val, voff in _iter_frames_off(bank.wal.read_all()):
                        if op == OP_PUT:
                            bank._apply(op, key, val, voff, len(val))
        # Live index is now fully captured in the bank snapshots → coordinator
        # history is no longer needed for recovery.
        self._coord.rewrite([])
        if self._cache is not None:
            self._cache.clear()          # cached values may sit at now-stale offsets

    # ── LREPLAY — rebuild every bank index from its WAL on boot ────────────────
    def _replay(self) -> None:
        coord_committed = set()
        for op, txid, _k, _v in _iter_frames(self._coord.read_all()):
            if op == OP_COMMIT:
                coord_committed.add(txid)

        max_txid = 0
        for bank in self._banks:
            records: Dict[int, List[Tuple[int, bytes, bytes, int]]] = {}
            committed: set = set()
            prepared: set = set()
            for op, txid, key, val, voff in _iter_frames_off(bank.wal.read_all()):
                if op == OP_COMMIT:
                    committed.add(txid)
                elif op == OP_PREPARE:
                    prepared.add(txid)
                else:
                    records.setdefault(txid, []).append((op, key, val, voff))
                if txid > max_txid:
                    max_txid = txid
            apply_ids = {t for t in records
                         if t in committed or (t in prepared and t in coord_committed)}
            for txid in sorted(apply_ids):
                for op, key, val, voff in records[txid]:
                    bank._apply(op, key, val, voff, len(val))
        with self._txid_lock:
            self._txid = max_txid

    def close(self) -> None:
        for bank in self._banks:
            bank.wal.close()
        self._coord.close()

    # ── introspection (visibility — the whole point) ──────────────────────────
    def bank_id_of(self, route: bytes) -> int:
        return zlib.crc32(route) & self._mask

    def stats(self) -> dict:
        return {
            "banks": self._n,
            "sync": "full" if self._sync_full else "batch",
            "values": "disk" if self._disk else "ram",
            "routes_per_bank": [len(b.data) for b in self._banks],
            "next_txid": self._txid,
            # The measurement basis for the higher cache strategies: hit-rate, evictions, bytes.
            "cache": (self._cache.stats() if self._cache is not None else None),
        }
