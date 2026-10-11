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
import time
import threading
import logging
from collections import OrderedDict
from typing import Dict, List, Optional, Tuple, Iterator

logger = logging.getLogger("Silica")


def _proc_rss_mb():
    """VmRSS in MB from /proc/self/status, or None off-Linux (the store's open line)."""
    try:
        with open("/proc/self/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) // 1024
    except (OSError, ValueError, IndexError):
        pass
    return None

def _replay_io():
    """The figures the replay span is measured by (directive 2026-10-03 item 3): (host MemAvailable
    MB, host swap-in pages `pswpin`, this process's major faults, this process's storage
    `read_bytes`). Each is None where it cannot be read (off Linux, a restricted /proc)."""
    out = [None, None, None, None]
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemAvailable:"):
                    out[0] = int(line.split()[1]) // 1024
                    break
    except (OSError, ValueError, IndexError):
        pass
    try:
        with open("/proc/vmstat") as f:
            for line in f:
                if line.startswith("pswpin "):
                    out[1] = int(line.split()[1])
                    break
    except (OSError, ValueError, IndexError):
        pass
    try:
        with open("/proc/self/stat") as f:
            out[2] = int(f.read().rsplit(")", 1)[1].split()[9])      # field 12, majflt
    except (OSError, ValueError, IndexError):
        pass
    try:
        with open("/proc/self/io") as f:
            for line in f:
                if line.startswith("read_bytes:"):
                    out[3] = int(line.split()[1])
                    break
    except (OSError, ValueError, IndexError):
        pass
    return tuple(out)


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


# '@'-index routes that are ONLY ever point-got (never bulk-scanned) — so their values do NOT need
# to be RAM-resident; the read cache + OS page cache serve the occasional point-get. These are the
# LARGE ones (one 64-byte key value per alias, millions of them), so leaving them on disk is the
# bulk of the RAM saving. `@ALIASLC`/`@ALIASCPT` are the case-insensitive / compact resolve indexes,
# read only via get() (silica_backend `get_key_by_alias`), never scanned. NOTE `@ALIAS` (the plain
# alias index) IS bulk-scanned (get_aliases_by_pattern → the concept shelf) and stays RAM-resident;
# `@ALIAS` is a prefix of the other two, so match the point-get ones explicitly.
_ROUTE_POINTGET_ONLY = (b"@ALIASLC", b"@ALIASCPT")


def _route_values_in_ram(route: bytes) -> bool:
    """Whether a route keeps its VALUES in RAM even in disk-value mode.

    Disk-value mode exists to keep large atom BODIES off RAM — but it must apply ONLY to bodies
    (and hash-routed links), NOT to the '@'-prefixed index/bookkeeping routes (alias / collection /
    scope / chunk-key / …) that are enumerated in BULK. Those are SINGLE mega-routes holding
    millions of subkeys; if their values live on disk, one `scan()` (e.g. `get_aliases_by_pattern`
    for the concept shelf) becomes millions of random preads — instant warm, but minutes cold (the
    "shelf hangs 10+ min" regression). Holding their (small) values in RAM makes enumeration a pure
    in-memory scan.

    EXCEPTION: the point-get-only alias indexes `@ALIASLC`/`@ALIASCPT` (case-insensitive / compact
    resolve) are NEVER scanned — only `get()`. Their values are the LARGE ones (a 64-byte key per
    alias × millions), so forcing them RAM-resident spent ~½ GB of RAM for no enumeration benefit,
    which on a memory-tight box tipped it into swap-thrash (slow reads → truncated dives). They stay
    on disk; the read + page cache serve their point-gets. Content + link routes are hash-addressed
    (never '@'), so this is a cheap tag check."""
    if route[:1] != b"@":
        return False
    return not any(route.startswith(p) for p in _ROUTE_POINTGET_ONLY)


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

    def read_from(self, offset: int) -> bytes:
        """Bytes from `offset` to EOF — the WAL SUFFIX past a durable-index frontier, so a warm
        boot replays only what the persisted index has not already applied (no full read)."""
        if offset <= 0:
            return self.read_all()
        with open(self.path, "rb") as f:
            f.seek(offset)
            return f.read()

    def size(self) -> int:
        return self._woff

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

    def __init__(self, bank_id: int, wal: Wal, disk: bool = False,
                 index: "IndexBackend" = None):
        self.id = bank_id
        self.wal = wal
        self.disk = disk
        self.lock = threading.Lock()
        # The primary index (route → subkey → ENTRY) is a RamIndex — always (F33): the set-algebra
        # structure must be memory-resident so any atom is reachable in one membership lookup + one
        # point-get. ENTRY is value bytes (ram-value mode) or a (voff,vlen) WAL locator (disk-value
        # mode — the independent VALUE-residency tier, where the multi-GB saving lives). The index is
        # a derived view of the WAL, rebuilt at boot. See index_backend.py.
        if index is None:
            from lib.akasha.backends.index_backend import RamIndex
            index = RamIndex()
        self.index = index

    # HPUT / HDEL — apply a decoded record to the primary index. In disk mode the value is
    # NOT stored; only its WAL location (voff, vlen) is.
    def _apply(self, op: int, key: bytes, val: bytes, voff: int = 0, vlen: int = 0,
               woff: int = None, txid: int = 0, coff: int = 0) -> None:
        route, subkey = _split(key)
        # Per-route value residency: an '@'-index/bookkeeping route keeps its (small, bulk-scanned)
        # value in RAM even in disk mode; only hash-routed bodies + links are paged to a (voff,vlen)
        # locator. See _route_values_in_ram — this is what stops a full alias enumeration from
        # turning into millions of cold preads.
        entry = (voff, vlen) if (self.disk and not _route_values_in_ram(route)) else val
        # The durable-view frontier for a persistent index. For a LIVE commit (woff=None) it is the
        # WAL size right now — this runs under bank.lock AFTER the commit marker is appended+fsync'd,
        # so it never over-states what is durable. During REPLAY the caller passes an explicit woff
        # (the record's frame end), which under-states → only ever replays a bounded suffix again.
        # `coff` is the coordinator offset a cross-bank commit depends on (passed by the store,
        # which owns the coordinator); a warm reboot validates the coordinator against it.
        if woff is None:
            woff = self.wal._woff
        self.index.apply(op, route, subkey, entry, woff=woff, txid=txid, coff=coff)

    def get_entry(self, route: bytes, subkey: bytes):               # HGET → ENTRY (unresolved)
        return self.index.get(route, subkey)

    def entries(self, route: bytes) -> List[Tuple[bytes, object]]:  # SCAN → [(subkey, ENTRY)]
        with self.lock:
            return self.index.iter_route(route)


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


def _total_ram_bytes() -> Optional[int]:
    """Total physical RAM in bytes, or None if it can't be read. Prefers psutil; falls back to
    /proc/meminfo (the Linux runtime target). Used to auto-size the disk-value read cache."""
    try:
        import psutil                                    # optional, no hard dependency
        return int(psutil.virtual_memory().total)
    except Exception:
        pass
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    return int(line.split()[1]) * 1024
    except Exception:
        pass
    return None


_DEFAULT_VALUE_CACHE_MB = 64        # the pre-regression default — proven good; see below


def _resolve_value_cache_bytes() -> int:
    """Byte budget for the disk-value SLRU read cache. **Defaults to 64 MiB.**

    An in-process value cache DOUBLE-STORES what the OS page cache already holds for the WAL, so it
    is NOT free RAM: on a memory-tight box a big cache STEALS the page cache the reads depend on and
    tips the box into swap-thrash — which slows every pread enough to trip the dive's wall-clock
    budget (observed: a large auto-sized cache regressed search from "a few seconds" to slow +
    non-deterministically truncated). The kernel page cache is the right owner of WAL residency, so
    the default is deliberately SMALL (64 MiB — just the hottest repeat reads) and leaves the bulk of
    RAM to the page cache.

    `AKASHA_SILICA_CACHE_MB`:
      * an explicit number (e.g. "512") → that many MiB, verbatim (opt in on a roomy box);
      * "auto"                          → derive from TOTAL RAM (2%, clamped [64 MiB, 256 MiB]);
      * unset                           → the 64 MiB default.
    Auto-sizing is OPT-IN, never the default: sizing a redundant cache up by machine RAM is exactly
    what hurt the tight box."""
    raw = os.environ.get("AKASHA_SILICA_CACHE_MB", "").strip().lower()
    if raw and raw != "auto":
        try:
            return int(float(raw) * 1024 * 1024)
        except ValueError:
            pass
    if raw != "auto":
        return _DEFAULT_VALUE_CACHE_MB * 1024 * 1024          # the safe default
    try:
        frac = float(os.environ.get("AKASHA_SILICA_CACHE_FRAC", "0.02"))
    except ValueError:
        frac = 0.02
    frac = min(0.5, max(0.005, frac))
    floor = 64 * 1024 * 1024
    cap = 256 * 1024 * 1024
    total = _total_ram_bytes()
    if total is None:
        return floor
    return max(floor, min(cap, int(total * frac)))


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
        # The OPEN is a long phase with no line of its own (group 1, rule 1.6): measured here, from
        # before the store exists to after the replay and the trim — see `_open_line`.
        self._open_t0 = time.monotonic()
        self._open_rss0 = _proc_rss_mb()
        self._dir = os.path.abspath(path_dir)
        os.makedirs(self._dir, exist_ok=True)
        # Bank geometry is FIXED by the store's on-disk layout: routing is `crc32(route) & (N-1)`, so
        # reopening an N-bank store with a different N sends every key to the wrong bank and orphans
        # most of the data. The requested `banks` therefore applies ONLY to a FRESH store; an EXISTING
        # store is reopened with its own geometry, detected from the number of bank WAL files on disk
        # (authoritative even for a store written before the count was persisted in store.mode). This
        # lets a per-client cell open with banks=1 (fewer WAL FDs — the R2/F28b guest-FD diet) while
        # the shared nucleus keeps its 8 banks, and neither can ever be reopened at the wrong width.
        import glob as _glob
        _existing_wals = _glob.glob(os.path.join(self._dir, "bank-*.wal"))
        if _existing_wals:
            _cnt = len(_existing_wals)
            if _cnt > 0 and (_cnt & (_cnt - 1)) == 0:      # trust only a valid power-of-two geometry
                banks = _cnt
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
        # The INDEX is RAM, always — one implementation, no modes (F33). The set-algebra structure
        # (collection membership, scope indexes, @ALIAS) MUST be memory-resident: that is the
        # condition under which Akasha's paid-up-front cost pays out — any atom reachable in one
        # membership lookup (RAM) + one point-get. A disk-resident index made every nested-scan
        # surface (cosmos/station/telemetry/curation/source-viewer) a lock convoy (scan × depth ×
        # fan-out under held bank locks); the access-path DEGREE, not size, is what broke. VALUE
        # residency (below, value_store=disk + _route_values_in_ram) is the independent, principled
        # lever for the multi-GB saving — Operand bodies to disk, set-algebra structure to RAM.
        # Persist the resolved value-mode (+ bank geometry) so the entrypoint layer reopens the store
        # the SAME way even when run without the seed's env (the AUTO-DETECT is one layer up).
        self._write_store_mode()
        self._banks = [Bank(i, Wal(os.path.join(self._dir, f"bank-{i:03d}.wal"),
                                   self._sync_full), disk=self._disk,
                            index=self._make_bank_index(i)) for i in range(banks)]
        self._coord = Wal(os.path.join(self._dir, "coord.wal"), self._sync_full)
        # The read cache accelerates the DISK-value path only (in RAM mode the bank index already
        # IS the value, so caching would just double-store it). In disk-value mode EVERY read is a
        # WAL pread, so a too-small cache makes search disk-bound (the "5x slower than the RAM-value
        # baseline" symptom): a 64 MiB cache holds almost none of a multi-GB value store's hot set.
        # Byte budget: AKASHA_SILICA_CACHE_MB — an explicit MiB number overrides; otherwise (unset or
        # "auto") it is auto-derived from TOTAL RAM. Total, not "available": the bank index is not
        # populated until the boot replay AFTER this point, so "available" here is misleadingly high
        # (it would size the cache against RAM the index is about to consume). A conservative fraction
        # of total leaves room for the index + OS page cache while giving the hot working set real
        # residency. Disk-value mode implies a large store, so this default is sized for that.
        self._cache = _SLRUCache(_resolve_value_cache_bytes()) if self._disk else None
        # F33 §5 — access-degree instrumentation (the permanent guard for the paid-for invariant).
        # Every read classifies as: a point_get (one member resolved), a membrane_scan (one route's
        # subkeys walked — a set/alias/scope membrane, RAM), or a full_scan (the whole keyspace —
        # must NEVER appear below a membrane). A set-mediated access must satisfy round-trips ≤
        # (atoms reached + sets touched) with ZERO full_scans; an eval resets and asserts on these,
        # so the lock-convoy pathology can never again be discovered only as a slow page.
        # F50 §4 — CALL counts alone hid the fetch_stream pathology: one membrane_scan CALL that
        # walked the whole 4.6 M-entry store looks identical to one that walked three. So the probe
        # ALSO weights by `entries_walked`: the number of index entries a scan iterates. The
        # concept-space bench and the fetch-stream eval assert on an entries-walked BUDGET, not
        # call counts — a "newest/sample K" read must stay O(limit) entries, never O(store).
        self._probe = {"point_get": 0, "membrane_scan": 0, "full_scan": 0, "entries_walked": 0}
        # 10-02 §6.3 — the same counters, for ONE thread: a measurement that must not count the
        # background weave/write threads touching the same store (the process-global probe adds
        # them, which is what made the concept-space bench pass alone and fail under load).
        self._probe_tid = 0
        self._probe_t = {"point_get": 0, "membrane_scan": 0, "full_scan": 0, "entries_walked": 0}
        _io0 = _replay_io()                        # the replay span's figures (10-03 item 3)
        _recs = self._boot_replay()
        self._open_io = (_io0, _replay_io())
        self._open_line(_recs)

    # A store at least this large (or any multi-bank store) is the one whose open is worth a line, a
    # tracer snapshot and a trim: the shared nucleus. A per-guest cell (banks=1, a few records) opens
    # many times a day; a trim there would cost latency on a request path for nothing to learn.
    OPEN_LINE_MIN_RECORDS = 100000

    def _open_line(self, records: int) -> None:
        """Group 2 read 2 (directive 2026-09-27 §3) — ONE line per open of the large store:

            [Silica] open rss_before=… after_replay=… after_trim=… anon=… fmap=… banks=… records=… t=…
                          avail_start=… avail_end=… swapin_pages=… majflt=… read_bytes=…

        `rss_before` is the process RSS before the store existed, `after_replay` once the WAL replay
        rebuilt the index, `after_trim` after a gc + `malloc_trim(0)` (the replay's transient buffers
        — each bank's WAL read whole, the per-transaction record lists — returned to the OS where the
        allocator can), and `anon`/`fmap` the smaps split at the end. Always on, no flag: the next
        ordinary deploy says whether the store's open leaves the band's 1.5 GB behind. A small store logs the same fields at DEBUG, untrimmed. Never raises.

        The last five (directive 2026-10-03 item 3) are measured over the REPLAY SPAN alone, so the
        next slow replay names its cause: the host's MemAvailable at its start and end, the host's
        swap-in pages, this process's major faults, and the bytes it read from storage during it
        (`-` where /proc cannot say). Same size, 85 s or 560 s: memory pressure, swap or a cold
        page cache each leave a different figure here."""
        try:
            from lib.akasha import memtrace as _mt
            big = self._n > 1 or int(records or 0) >= self.OPEN_LINE_MIN_RECORDS
            rss1 = _proc_rss_mb()
            if big:
                _mt.gc_trim()
            rss2 = _proc_rss_mb() if big else None
            anon, fmap = _mt.smaps_rollup()

            def _f(v):
                return "%dMB" % v if v is not None else "-"
            io0, io1 = getattr(self, "_open_io", None) or ((None,) * 4, (None,) * 4)

            def _d(i):
                return str(io1[i] - io0[i]) if io0[i] is not None and io1[i] is not None else "-"
            (logger.info if big else logger.debug)(
                "[Silica] open rss_before=%s after_replay=%s after_trim=%s anon=%s fmap=%s banks=%d "
                "records=%d t=%.2fs store=%s avail_start=%s avail_end=%s swapin_pages=%s majflt=%s "
                "read_bytes=%s", _f(self._open_rss0), _f(rss1), _f(rss2), _f(anon),
                _f(fmap), self._n, int(records or 0), time.monotonic() - self._open_t0,
                os.path.basename(self._dir), _f(io0[0]), _f(io1[0]), _d(1), _d(2), _d(3))
        except Exception:
            pass

    def probe_reset(self, thread_only: bool = False) -> None:
        """Zero the access-degree counters. `thread_only=True` makes the next `probe_read` report
        only the accesses made BY THE CALLING THREAD — what a measurement of one render needs when
        background threads share the store."""
        self._probe = {"point_get": 0, "membrane_scan": 0, "full_scan": 0, "entries_walked": 0}
        self._probe_t = {"point_get": 0, "membrane_scan": 0, "full_scan": 0, "entries_walked": 0}
        self._probe_tid = threading.get_ident() if thread_only else 0

    def probe_read(self) -> dict:
        return dict(self._probe_t if self._probe_tid else self._probe)

    def _make_bank_index(self, bank_id: int):
        """One bank's index is a RamIndex — always (F33). The index is a DERIVED view of the WAL,
        rebuilt by _replay() at boot; keeping the set-algebra structure in RAM is the invariant the
        whole design is paid for."""
        from lib.akasha.backends.index_backend import RamIndex
        return RamIndex()

    # ── persisted store config (value-mode + bank geometry) ────────────────────
    def _store_mode_path(self) -> str:
        return os.path.join(self._dir, "store.mode")

    def _read_store_mode(self) -> dict:
        try:
            import json
            with open(self._store_mode_path(), "r") as f:
                d = json.load(f)
                return d if isinstance(d, dict) else {}
        except (OSError, ValueError):
            return {}

    def _write_store_mode(self) -> None:
        try:
            import json
            # Only the VALUE mode + bank geometry are persisted for auto-detect on reopen (a
            # disk-value store must not reopen ram-value; an N-bank store must not reopen at a
            # different width). The index is always RAM — nothing to persist (F33).
            payload = {"values": "disk" if self._disk else "ram", "banks": self._n}
            if self._read_store_mode() == payload:
                return
            tmp = self._store_mode_path() + ".tmp"
            with open(tmp, "w") as f:
                json.dump(payload, f)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, self._store_mode_path())
        except OSError:
            pass

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
        """Resolve an index ENTRY to value bytes. Type-dispatched so RAM-resident and disk-resident
        entries can coexist in one store (disk-value mode keeps '@'-index-route values in RAM — see
        _route_values_in_ram): a `(voff, vlen)` tuple is a WAL locator to pread (value bytes are
        never a tuple, so the test is unambiguous); anything else IS the value. When a pread is
        needed the CALLER must hold bank.lock (so it cannot race a checkpoint rewriting the WAL)."""
        if entry is None:
            return None
        if isinstance(entry, tuple):           # a (voff, vlen) disk locator
            return bank.wal.pread(entry[0], entry[1])
        return entry                           # value bytes held in RAM (RAM mode, or an '@'-route)

    def get(self, route: bytes, subkey: bytes) -> Optional[bytes]:
        self._probe["point_get"] += 1                  # F33 §5 — one member resolved (the terminal step)
        if self._probe_tid and threading.get_ident() == self._probe_tid:
            self._probe_t["point_get"] += 1
        bank = self._bank_of(route)
        # RAM mode, OR a disk-mode '@'-index route whose value is RAM-resident: the entry IS the
        # value — no pread, no cache, no lock (mirrors the historical RAM-mode point read).
        if not self._disk or _route_values_in_ram(route):
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
        self._probe["membrane_scan"] += 1              # F33 §5 — one membrane (route) walked
        if self._probe_tid and threading.get_ident() == self._probe_tid:
            self._probe_t["membrane_scan"] += 1
        bank = self._bank_of(route)
        if self._disk:
            with bank.lock:
                items = bank.index.iter_route(route)
                out = [(sk, self._entry_bytes(bank, e)) for sk, e in items]
                self._probe["entries_walked"] += len(out)   # F50 §4 — weight by entries iterated
                if self._probe_tid and threading.get_ident() == self._probe_tid:
                    self._probe_t["entries_walked"] += len(out)
                return out
        out = [(sk, self._entry_bytes(bank, e)) for sk, e in bank.entries(route)]
        self._probe["entries_walked"] += len(out)          # F50 §4 — weight by entries iterated
        if self._probe_tid and threading.get_ident() == self._probe_tid:
            self._probe_t["entries_walked"] += len(out)
        return out

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
        self._probe["membrane_scan"] += 1              # F33 §5 — one membrane (route) streamed
        if self._probe_tid and threading.get_ident() == self._probe_tid:
            self._probe_t["membrane_scan"] += 1
        bank = self._bank_of(route)
        heap: List[Tuple] = []       # (key, seq, subkey, value) min-heap of the running top-k
        seq = 0
        walked = 0
        with bank.lock:
            for subkey, entry in bank.index.iter_route_stream(route):
                walked += 1
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
        self._probe["entries_walked"] += walked        # F50 §4 — weight by entries iterated
        if self._probe_tid and threading.get_ident() == self._probe_tid:
            self._probe_t["entries_walked"] += walked
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
        self._probe["membrane_scan"] += 1              # F33 §5 — one membrane (route) walked, keys only
        if self._probe_tid and threading.get_ident() == self._probe_tid:
            self._probe_t["membrane_scan"] += 1
        bank = self._bank_of(route)
        with bank.lock:
            out = bank.index.subkeys(route, prefix)
        self._probe["entries_walked"] += len(out)      # F50 §4 — weight by entries iterated
        if self._probe_tid and threading.get_ident() == self._probe_tid:
            self._probe_t["entries_walked"] += len(out)
        return out

    def scan_keys(self, route: bytes, limit: int = None) -> List[bytes]:
        """Snapshot the subkeys under one route (values UNTOUCHED), optionally capped at `limit`.
        Like scan_subkeys but it STOPS at the cap — so a "first K" caller (get_all_chunks(limit=K))
        snapshots O(K) keys, not the whole route. This is the F50 memory fix for the streaming
        chunk read: the lock is held only to copy ≤K key references, then released; the caller
        preads/decodes the K values lazily OUTSIDE the lock (the login-starvation-safe shape —
        never a lazy scan held across the whole consume). No cap ⇒ the full key snapshot."""
        self._probe["membrane_scan"] += 1              # F33 §5 — one membrane (route) walked, keys only
        if self._probe_tid and threading.get_ident() == self._probe_tid:
            self._probe_t["membrane_scan"] += 1
        bank = self._bank_of(route)
        out = []
        with bank.lock:
            for subkey, _entry in bank.index.iter_route_stream(route):
                out.append(subkey)
                if limit is not None and len(out) >= limit:
                    break
        self._probe["entries_walked"] += len(out)      # F50 §4 — weight by entries iterated (≤ limit)
        if self._probe_tid and threading.get_ident() == self._probe_tid:
            self._probe_t["entries_walked"] += len(out)
        return out

    def count_route_subkeys(self, route: bytes, subkey_pred=None) -> int:
        """Count subkeys under one route (optionally filtered by `subkey_pred(subkey)`)
        WITHOUT reading any value. This is the branch-count cue's path: a signpost only
        needs "how many edges ahead", never their contents, so — unlike scan_route_topk,
        which preads every value to rank by weight — this touches keys only. On a mega-hub
        neighbour in disk mode that turns a per-signpost pread storm into an O(1)-ish dict
        walk, which is what makes a dense-hub dive fast."""
        self._probe["membrane_scan"] += 1              # F33 §5 — one membrane (route) counted, keys only
        if self._probe_tid and threading.get_ident() == self._probe_tid:
            self._probe_t["membrane_scan"] += 1
        bank = self._bank_of(route)
        with bank.lock:
            n = bank.index.count_route(route, subkey_pred)
        self._probe["entries_walked"] += n             # F50 §4 — weight by entries iterated
        if self._probe_tid and threading.get_ident() == self._probe_tid:
            self._probe_t["entries_walked"] += n
        return n

    def scan_all(self) -> Iterator[Tuple[bytes, bytes, bytes]]:
        """(route, subkey, value) across every bank — the rare global scan
        (LIKE over the whole keyspace).  Snapshots each bank under its lock."""
        self._probe["full_scan"] += 1                  # F33 §5 — a whole-keyspace scan (never below a membrane)
        if self._probe_tid and threading.get_ident() == self._probe_tid:
            self._probe_t["full_scan"] += 1
        for bank in self._banks:
            with bank.lock:
                # Resolve under the lock so disk-mode preads cannot race a checkpoint.
                out = [(route, subkey, self._entry_bytes(bank, entry))
                       for route, subkey, entry in bank.index.iter_all()]
            self._probe["entries_walked"] += len(out)  # F50 §4 — weight by entries iterated
            if self._probe_tid and threading.get_ident() == self._probe_tid:
                self._probe_t["entries_walked"] += len(out)
            for row in out:
                yield row

    # ── write path ────────────────────────────────────────────────────────────
    def begin(self) -> Txn:                                              # TBEGIN
        return Txn(self)

    def update(self, route: bytes, subkey: bytes, fn) -> Optional[bytes]:        # TRMW
        """ATOMIC read-modify-write of ONE record: under its bank's lock, read the value, compute
        `fn(old) -> new`, and commit `new` (one frame + commit marker, fsync'd as a txn is) before the
        lock is released — so no other commit to that bank lands between the read and the write. `fn`
        returning None or the old value writes nothing; `fn` raising writes nothing and propagates.
        `fn` runs under the bank lock and must not read the store (the lock is not reentrant).
        Returns the value now stored. A Txn cannot do this: its reads are taken before its commit's
        lock, so two Txns that read-then-write one record lose one write."""
        bank = self._bank_of(route)
        with bank.lock:
            old = self._entry_bytes(bank, bank.get_entry(route, subkey))
            new = fn(old)
            if new is None or new == old:
                return old
            txid = self._next_txid()
            key = _compose(route, subkey)
            foff = bank.wal.append(_frame(OP_PUT, txid, key, new))
            bank.wal.append(_frame(OP_COMMIT, txid, b"", b""))
            if self._sync_full:
                bank.wal.fsync()
            bank._apply(OP_PUT, key, new, foff + _HDR.size + _PAY.size + len(key), len(new),
                        txid=txid)
            if self._cache is not None:
                self._cache.overwrite((route, subkey), new)
        return new

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
                    bank._apply(op, key, val, voff, vlen, txid=txid)
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
                coff = self._coord._woff        # this cross-bank commit depends on the coordinator
                for bank in locked:
                    for op, key, val, voff, vlen in staged_apply[bank.id]:
                        bank._apply(op, key, val, voff, vlen, txid=txid, coff=coff)
                    if self._cache is not None:    # write-warm while all bank locks are held
                        for ck, v in cache_by_bank.get(bank.id, ()):
                            self._cache.overwrite(ck, v)
            finally:
                for bank in reversed(locked):
                    bank.lock.release()

    # ── LCKPT — explicit checkpoint (fold live index → fresh log, truncate) ────
    def route_sizes(self) -> dict:
        """R8/F28c — merge each bank's per-route deep-size attribution. A given `@` route lives in
        exactly one bank (crc32(route) & mask), so the @-routes concatenate; the hash-route
        aggregate sums across banks. For the MemTop RAM report."""
        at_routes = []
        other_n = 0
        other_bytes = 0
        for bank in self._banks:
            try:
                rs = bank.index.route_sizes()
            except Exception:
                continue
            at_routes.extend(rs.get("at_routes") or [])
            oth = rs.get("other_routes") or {}
            other_n += oth.get("count", 0)
            other_bytes += oth.get("bytes", 0)
        at_routes.sort(key=lambda t: t[2], reverse=True)
        return {"at_routes": at_routes, "other_routes": {"count": other_n, "bytes": other_bytes}}

    def wal_bytes(self) -> int:
        """Total on-disk WAL size (every bank WAL + the coordinator). The checkpoint threshold and
        the sys.compact report read this — an ever-growing WAL is what makes a ram-mode reopen pay
        a full replay and scatters value preads over a long file (R7/F26)."""
        total = 0
        try:
            for bank in self._banks:
                total += bank.wal.size()
            total += self._coord.size()
        except Exception:
            pass
        return total

    def checkpoint(self) -> None:
        # A checkpoint REWRITES the WALs (byte offsets change). The index is RAM (rebuilt from the
        # WAL every boot), so there is nothing persisted to invalidate — the fold is pure disk
        # hygiene (F33: the index-generation coupling is gone). Writer-only; run at idle.
        for bank in self._banks:
            with bank.lock:
                # Snapshot the live records as one committed txn. In disk mode the values are
                # read back from the WAL (they are not in RAM); in RAM mode the entry IS the value.
                frames = [_frame(OP_PUT, 1, _compose(route, subkey),
                                 self._entry_bytes(bank, entry) or b"")
                          for route, subkey, entry in bank.index.iter_all()]
                frames.append(_frame(OP_COMMIT, 1, b"", b""))
                bank.wal.rewrite(frames)
                if self._disk:
                    # Offsets changed under the compaction — rebuild the location index from the
                    # freshly written (compact) WAL so every entry points at its new position.
                    bank.index.clear()
                    for op, _txid, key, val, voff in _iter_frames_off(bank.wal.read_all()):
                        if op == OP_PUT:
                            bank._apply(op, key, val, voff, len(val))
        # Live index is now fully captured in the bank snapshots → coordinator
        # history is no longer needed for recovery.
        self._coord.rewrite([])
        if self._cache is not None:
            self._cache.clear()          # cached values may sit at now-stale offsets

    # ── boot: rebuild the RAM index from the WAL (always a full replay) ─────────
    def _boot_replay(self) -> int:
        """The index is RAM, so boot is always a full rebuild from the WAL — one code path, always
        correct (F33). Replay volume is kept bounded by WAL compaction (sys.compact / the maintenance
        job), not by a persisted index. Emits ONE plain line: records replayed + seconds."""
        start_offsets = {bank.id: 0 for bank in self._banks}
        _t0 = time.monotonic()
        applied = self._replay(start_offsets, 0)
        try:
            logger.info("[Silica] index rebuilt from WAL — replayed %d record(s) across %d bank(s) "
                        "in %.2fs", applied, self._n, time.monotonic() - _t0)
        except Exception:
            pass
        return applied

    # ── LREPLAY — rebuild bank indexes from their WAL (full replay from offset 0) ──
    def _replay(self, start_offsets: Dict[int, int] = None, base_txid: int = 0) -> int:
        """Rebuild bank indexes from their WAL. Returns the number of records applied — the
        boot-open line reports it as the replay volume."""
        applied = 0
        coord_committed = set()
        for op, txid, _k, _v in _iter_frames(self._coord.read_all()):
            if op == OP_COMMIT:
                coord_committed.add(txid)
        coord_size = self._coord.size()      # a cross-bank txn's index entry depends on this

        max_txid = base_txid
        for bank in self._banks:
            start = 0 if start_offsets is None else start_offsets.get(bank.id, 0)
            records: Dict[int, List[Tuple[int, bytes, bytes, int]]] = {}
            committed: set = set()
            prepared: set = set()
            # Read only the suffix past `start` (a warm frontier); voff from the sub-blob is
            # relative, so shift it by `start` back to the ABSOLUTE file offset a disk-mode pread
            # needs. `start` is always a commit boundary, so no txn straddles it.
            blob = bank.wal.read_from(start) if start else bank.wal.read_all()
            for op, txid, key, val, voff in _iter_frames_off(blob):
                voff += start
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
                # A cross-bank txn (prepared + coord-committed) depends on the coordinator; record
                # that dependency (full coord size — a safe over-statement) so a warm reboot
                # invalidates if the coordinator later shrinks. A single-bank txn depends on no
                # coordinator → coff 0.
                coff = coord_size if (txid in prepared and txid in coord_committed) else 0
                for op, key, val, voff in records[txid]:
                    # woff = this record's frame END (absolute) — the durable frontier after it.
                    bank._apply(op, key, val, voff, len(val),
                                woff=voff + len(val), txid=txid, coff=coff)
                    applied += 1
        with self._txid_lock:
            self._txid = max_txid
        return applied

    def close(self) -> None:
        for bank in self._banks:
            bank.wal.close()
            try:
                bank.index.close()
            except Exception:
                pass
        self._coord.close()

    # ── introspection (visibility — the whole point) ──────────────────────────
    def bank_id_of(self, route: bytes) -> int:
        return zlib.crc32(route) & self._mask

    def stats(self) -> dict:
        return {
            "banks": self._n,
            "sync": "full" if self._sync_full else "batch",
            "values": "disk" if self._disk else "ram",
            "routes_per_bank": [b.index.route_count() for b in self._banks],
            "index": "ram",                     # RAM index, always — one implementation (F33)
            "next_txid": self._txid,
            # The measurement basis for the higher cache strategies: hit-rate, evictions, bytes.
            "cache": (self._cache.stats() if self._cache is not None else None),
        }
