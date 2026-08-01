"""
SilicaBackend (Slice B) — the AkashaBackend ISA on top of the Silica engine.

A drop-in for SQLiteBackend: it satisfies the SAME 59-method contract
(lib/akasha/backends/base.py), so the swap is a one-line factory change and the
runtime — already SQL-free through that interface — is unaffected.  The engine
(lib/akasha/backends/silica.py) is the hardware-mappable pseudo-ISA store; this
file is only the encoding of Akasha's 11 "tables" into (route, subkey) keys plus
dual-indexing for the reverse lookups (spec §4).

Route policy (the memory-management unit):
  Everything OWNED BY ONE ATOM — its content chunk, its access scopes, its meta,
  its set-membership back-refs, its alias back-refs — is routed by the ATOM KEY,
  so the whole bundle lives in ONE bank.  `atom_bundle()` writes it as ONE Silica
  transaction → the atom is a single atomic primitive (the payoff: what SQLite
  does as several separate commits).  Cross-atom edges (links, forward set
  membership, forward alias) are routed by their own anchor and become small
  cross-bank transactions.

This is a prototype: values are JSON blobs (not packed structs) and rowid-exact
ordering is approximated by a monotonic seq.  Correctness is proven by
test/silica_backend_eval.py (parity vs SQLiteBackend) + the engine's crash/rollback
guarantees.
"""

import os
import re
import json
import hashlib
import fnmatch
import threading
from typing import Optional, List, Dict, Any

from lib.akasha.backends.base import AkashaBackend
from lib.akasha.backends.silica import SilicaStore
from lib.akasha.dna import get_primal_sequence

# ── ISO-639-1 language codes (mirror SQLiteBackend for lang: derivation) ──────
_ISO_639_1 = {
    "aa","ab","ae","af","ak","am","an","ar","as","av","ay","az","ba","be","bg",
    "bh","bi","bm","bn","bo","br","bs","ca","ce","ch","co","cr","cs","cu","cv",
    "cy","da","de","dv","dz","ee","el","en","eo","es","et","eu","fa","ff","fi",
    "fj","fo","fr","fy","ga","gd","gl","gn","gu","gv","ha","he","hi","ho","hr",
    "ht","hu","hy","hz","ia","id","ie","ig","ii","ik","io","is","it","iu","ja",
    "jv","ka","kg","ki","kj","kk","kl","km","kn","ko","kr","ks","ku","kv","kw",
    "ky","la","lb","lg","li","ln","lo","lt","lu","lv","mg","mh","mi","mk","ml",
    "mn","mr","ms","mt","my","na","nb","nd","ne","ng","nl","nn","no","nr","nv",
    "ny","oc","oj","om","or","os","pa","pi","pl","ps","pt","qu","rm","rn","ro",
    "ru","rw","sa","sc","sd","se","sg","si","sk","sl","sm","sn","so","sq","sr",
    "ss","st","su","sv","sw","ta","te","tg","th","ti","tk","tl","tn","to","tr",
    "ts","tt","tw","ty","ug","uk","ur","uz","ve","vi","vo","wa","wo","xh","yi",
    "yo","za","zh","zu",
}

_ACCESS_PREFIXES = ("scope:", "owner:", "view:")


def _j(obj) -> bytes:
    return json.dumps(obj, ensure_ascii=False).encode("utf-8")


def _u(b: Optional[bytes]):
    return json.loads(b.decode("utf-8")) if b else None


def _norm_alias(alias: str):
    """(lowercase, compact) forms used by the case-insensitive / compound-normalised
    alias resolution — mirrors SQLiteBackend.get_key_by_alias's LOWER()/REPLACE()."""
    lc = alias.lower()
    return lc, re.sub(r"[\s\-]+", "", lc)


# Sub-key tags within an atom's own route (co-located → one bank, one bundle).
_SUB_CHUNK = b"C"                      # the content chunk
_PFX_ACCESS = b"X:"                    # X:<scope>            → access scope (forward)
_PFX_ALIAS  = b"A:"                    # A:<alias>           → alias back-ref
_PFX_COLL   = b"S:"                    # S:<name>            → set-membership back-ref
_PFX_LOUT   = b"L>"                    # L><dst>\0<rel>      → outgoing link (val=linkdict)
_PFX_LIN    = b"L<"                    # L<<src>\0<rel>      → incoming link (val=linkdict)

# Dedicated routes for cross-atom / global indexes.
_R_ALIAS   = b"@ALIAS"                 # subkey=<alias>      → key           (alias index)
_R_ALIAS_LC  = b"@ALIASLC"             # subkey=lower(alias) → key  (case-insensitive resolve, O(1))
_R_ALIAS_CPT = b"@ALIASCPT"            # subkey=compact(alias)→ key (space/hyphen-stripped resolve, O(1))
_R_COLL    = b"@COLL\x00"              # route _R_COLL+name, subkey=<key> → 1 (members)
_R_SCOPE   = b"@SCOPE\x00"             # route _R_SCOPE+scope, subkey=<key> → 1 (keys-by-scope)
_R_CDEF    = b"@CDEF"                  # subkey=<name>       → meta          (collection defs)
_R_NSC     = b"@NSC"                   # subkey=<ns>         → count         (namespace counts)
_R_VAULT   = b"@V\x00"                 # route _R_VAULT+cat, subkey=<ident> → data
_R_PLINK   = b"@PLINK"                 # subkey=<id>         → pending link
_R_PDERIV  = b"@PDERIV"                # subkey=<key>\0<alias> → seq (dedup + FIFO)
_R_ACL     = b"@ACL"                   # subkey=<id>         → collision record
_R_CHUNKS  = b"@CHUNKS"                # subkey=<chunk key>  → seq  (the chunk-key index —
                                       #   a SINGLE route so enumerate/recent/stream are one
                                       #   bounded scan, not an O(all-routes) scan_all)


class SilicaBackend(AkashaBackend):
    """AkashaBackend implemented on the Silica banked pseudo-ISA store."""

    def __init__(self, db_path, is_volatile: bool = False, sync_mode: str = "NORMAL",
                 banks: int = 8):
        self._dir = os.path.abspath(db_path) + ".silica"
        if is_volatile and os.path.isdir(self._dir):
            import shutil
            shutil.rmtree(self._dir, ignore_errors=True)
        sync = "full" if sync_mode.upper() == "FULL" else "batch"
        # Value residency (AKASHA_SILICA_VALUES): "ram" (default) keeps values in the index —
        # fast, but the whole dataset must fit in RAM; "disk" keeps only a (offset,len) location
        # and preads values from the WAL on demand, so a large ontology (e.g. the full thesaurus)
        # no longer has to be RAM-resident. Same on-disk format either way.
        value_store = os.environ.get("AKASHA_SILICA_VALUES", "ram").strip().lower()
        self._store = SilicaStore(self._dir, banks=banks, sync=sync, value_store=value_store)
        self._seq_lock = threading.Lock()
        self._unfold_dna()

    @property
    def db_path(self) -> str:
        """The on-disk store location (parity with SQLiteBackend's path attr). Silica persists to
        this `.silica` directory (WAL + fsync); exposing it stops status readers that probe
        `db_path`/`_db_path` from mislabelling a persistent native cell as 'in-memory'."""
        return self._dir

    def _unfold_dna(self) -> None:
        """Seed the primal DNA atoms (boot parity with SQLiteBackend): each DNA
        alias → a universal-scoped atom + its derived leaf:/ns:/lang: collections."""
        for alias, text in get_primal_sequence().items():
            if self.get_key_by_alias(alias):
                continue
            key = hashlib.sha256(text.encode()).hexdigest()
            self.write_atom(key, text, "{}", "system.dna", "verified", 0.0,
                            scopes=["scope:sys:universal"])
            self.put_alias(key, alias)
            self.derive_alias_collections(alias, key)

    # ── helpers ───────────────────────────────────────────────────────────────
    def _rk(self, s: str) -> bytes:
        return s.encode("utf-8")

    def _write(self, *ops):
        """Run a set of (route, subkey, value|None) ops as ONE atomic Silica txn."""
        with self._store.begin() as t:
            for route, subkey, val in ops:
                if val is None:
                    t.delete(route, subkey)
                else:
                    t.put(route, subkey, val)

    # ══ Atom CRUD ══════════════════════════════════════════════════════════════
    def put_chunk_raw(self, key, content, meta_str, author, status, ts) -> None:
        rec = {"content": content, "meta": meta_str, "created_at": str(ts),
               "author": author, "status": status, "seq": self._store.next_id()}
        self._write((self._rk(key), _SUB_CHUNK, _j(rec)),
                    (_R_CHUNKS, self._rk(key), str(rec["seq"]).encode()))

    def write_atom(self, key, content, meta_str, author, status, ts,
                   scopes=None) -> None:
        """The atom as ONE atomic memory-management unit — content chunk + access
        scopes (+ their reverse index) + stream index, committed as a SINGLE Silica
        transaction (all-or-nothing).  Everything is routed by the atom key, so the
        whole bundle lands in one bank.  This is the payoff over SQLite, where the
        same bundle is several separate commits (a torn atom on crash); here the
        memory-management unit IS one primitive.  Composite may call this instead of
        put_chunk_raw + put_chunk_access + update_meta."""
        rk = self._rk(key)
        seq = self._store.next_id()
        rec = {"content": content, "meta": meta_str, "created_at": str(ts),
               "author": author, "status": status, "seq": seq}
        ops = [(rk, _SUB_CHUNK, _j(rec)),
               (_R_CHUNKS, rk, str(seq).encode())]
        for s in (scopes or []):
            sb = self._rk(s)
            ops.append((rk, _PFX_ACCESS + sb, b"1"))
            ops.append((_R_SCOPE + sb, rk, b"1"))
        self._write(*ops)

    def update_chunk_status(self, key, status, content=None) -> None:
        cur = self._store.get(self._rk(key), _SUB_CHUNK)
        if cur is None:
            return
        rec = _u(cur)
        rec["status"] = status
        if content is not None:
            rec["content"] = content
        self._write((self._rk(key), _SUB_CHUNK, _j(rec)))

    def get_chunk_raw(self, key) -> Optional[dict]:
        rec = _u(self._store.get(self._rk(key), _SUB_CHUNK))
        if rec is None:
            return None
        return {"content": rec["content"], "meta": rec["meta"],
                "status": rec["status"], "author": rec["author"]}

    def update_meta(self, key, meta_dict) -> None:
        cur = self._store.get(self._rk(key), _SUB_CHUNK)
        if cur is None:
            return
        rec = _u(cur)
        rec["meta"] = json.dumps(meta_dict)
        self._write((self._rk(key), _SUB_CHUNK, _j(rec)))

    def drop_chunk(self, key) -> None:
        rk = self._rk(key)
        ops = [(_R_CHUNKS, rk, None)]       # remove from the chunk-key index
        # Everything under the atom's own route (chunk, access fwd, alias back-refs,
        # set back-refs, outgoing + incoming link records) + the reverse indexes.
        for subkey, val in self._store.scan(rk):
            ops.append((rk, subkey, None))
            if subkey.startswith(_PFX_ACCESS):
                scope = subkey[len(_PFX_ACCESS):]
                ops.append((_R_SCOPE + scope, rk, None))
            elif subkey.startswith(_PFX_ALIAS):
                al = subkey[len(_PFX_ALIAS):]
                lc, cpt = _norm_alias(al.decode())
                ops.append((_R_ALIAS, al, None))
                ops.append((_R_ALIAS_LC, lc.encode("utf-8"), None))
                ops.append((_R_ALIAS_CPT, cpt.encode("utf-8"), None))
            elif subkey.startswith(_PFX_COLL):
                name = subkey[len(_PFX_COLL):]
                ops.append((_R_COLL + name, rk, None))
            elif subkey.startswith(_PFX_LOUT):
                dst, _, rel = subkey[len(_PFX_LOUT):].partition(b"\x00")
                ops.append((dst, _PFX_LIN + rk + b"\x00" + rel, None))
            elif subkey.startswith(_PFX_LIN):
                src, _, rel = subkey[len(_PFX_LIN):].partition(b"\x00")
                ops.append((src, _PFX_LOUT + rk + b"\x00" + rel, None))
        if ops:
            self._write(*ops)

    # ══ Access control ═════════════════════════════════════════════════════════
    def put_chunk_access(self, key, scopes) -> None:
        rk = self._rk(key)
        ops = []
        for s in scopes:
            sb = self._rk(s)
            ops.append((rk, _PFX_ACCESS + sb, b"1"))
            ops.append((_R_SCOPE + sb, rk, b"1"))
        if ops:
            self._write(*ops)

    def remove_chunk_access(self, key, scope=None) -> None:
        rk = self._rk(key)
        ops = []
        if scope:
            sb = self._rk(scope)
            ops.append((rk, _PFX_ACCESS + sb, None))
            ops.append((_R_SCOPE + sb, rk, None))
        else:
            for subkey, _v in self._store.scan(rk):
                if subkey.startswith(_PFX_ACCESS):
                    sb = subkey[len(_PFX_ACCESS):]
                    ops.append((rk, subkey, None))
                    ops.append((_R_SCOPE + sb, rk, None))
        if ops:
            self._write(*ops)

    def get_chunk_access_scopes(self, key) -> List[str]:
        # Scope text lives in the subkey (_PFX_ACCESS + scope) — no value needed. scan_subkeys
        # reads keys only, so this stays cheap even when the atom's route also holds a mega-hub's
        # worth of link values (which a value-reading scan would pread in full — the dive's
        # check_access path called this per neighbour).
        return [sk[len(_PFX_ACCESS):].decode()
                for sk in self._store.scan_subkeys(self._rk(key), _PFX_ACCESS)]

    def check_chunk_access_any(self, key, allowed_scopes) -> bool:
        if not allowed_scopes:
            return False
        have = set(self.get_chunk_access_scopes(key))
        return any(s in have for s in allowed_scopes)

    # ══ Aliases ══════════════════════════════════════════════════════════════════
    def put_alias(self, key, alias) -> Optional[str]:
        rk = self._rk(key)
        lc, cpt = _norm_alias(alias)
        # Dual-index the normalised forms so case-insensitive / compound-normalised
        # resolution is O(1), not an O(N) scan of the whole alias table (the weave
        # hot path — resolving a proto-word MISS degrades to O(N) per call otherwise).
        self._write((_R_ALIAS, self._rk(alias), rk),
                    (rk, _PFX_ALIAS + self._rk(alias), b"1"),
                    (_R_ALIAS_LC, lc.encode("utf-8"), rk),
                    (_R_ALIAS_CPT, cpt.encode("utf-8"), rk))
        return alias

    def delete_alias(self, alias) -> None:
        cur = self._store.get(_R_ALIAS, self._rk(alias))
        lc, cpt = _norm_alias(alias)
        ops = [(_R_ALIAS, self._rk(alias), None),
               (_R_ALIAS_LC, lc.encode("utf-8"), None),
               (_R_ALIAS_CPT, cpt.encode("utf-8"), None)]
        if cur is not None:
            ops.append((cur, _PFX_ALIAS + self._rk(alias), None))
        self._write(*ops)

    def get_key_by_alias(self, alias) -> Optional[str]:
        # exact → case-insensitive → compound-normalised, each an O(1) index hit.
        r = self._store.get(_R_ALIAS, self._rk(alias))
        if r is not None:
            return r.decode()
        lc, cpt = _norm_alias(alias)
        r = self._store.get(_R_ALIAS_LC, lc.encode("utf-8"))
        if r is not None:
            return r.decode()
        r = self._store.get(_R_ALIAS_CPT, cpt.encode("utf-8"))
        return r.decode() if r is not None else None

    def get_aliases_by_key(self, key) -> List[str]:
        # The alias text IS the subkey tail (_PFX_ALIAS + alias) — the value is never needed.
        # scan_subkeys reads keys only; scan() would pread every value in the route, so on a
        # mega-hub (whose route also holds all its incoming/outgoing link values) this lookup
        # was preading tens of thousands of link values per call. It is called ~once per
        # signpost on a dive, so that full-route pread WAS the dominant dive latency.
        return [sk[len(_PFX_ALIAS):].decode()
                for sk in self._store.scan_subkeys(self._rk(key), _PFX_ALIAS)]

    def get_aliases_by_pattern(self, pattern) -> List[dict]:
        # '%'→'*', '_'→'?'  (SQL LIKE → fnmatch), case-insensitive.
        glob = pattern.lower().replace("%", "*").replace("_", "?")
        out = []
        for subkey, key in self._store.scan(_R_ALIAS):
            a = subkey.decode()
            if fnmatch.fnmatch(a.lower(), glob):
                out.append({"alias": a, "key": key.decode()})
        return out

    # ══ Alias collision log ═════════════════════════════════════════════════════
    def log_alias_collision(self, alias, old_key, new_key, event="overwrite") -> None:
        cid = self._store.next_id()
        import time
        rec = {"id": cid, "alias": alias, "old_key": old_key, "new_key": new_key,
               "ts": time.time(), "event": event, "resolved": 0}
        self._write((_R_ACL, str(cid).zfill(20).encode(), _j(rec)))

    def get_alias_collision_log(self, since=0.0, limit=200, unresolved_only=False) -> list:
        rows = [_u(v) for _s, v in self._store.scan(_R_ACL)]
        rows = [r for r in rows if r["ts"] >= since and (not unresolved_only or not r["resolved"])]
        rows.sort(key=lambda r: r["ts"], reverse=True)
        return rows[:limit]

    def resolve_alias_collision(self, alias) -> int:
        n = 0
        ops = []
        for subkey, v in self._store.scan(_R_ACL):
            rec = _u(v)
            if rec["alias"] == alias and not rec["resolved"]:
                rec["resolved"] = 1
                ops.append((_R_ACL, subkey, _j(rec)))
                n += 1
        if ops:
            self._write(*ops)
        return n

    def clear_alias_collision_log(self) -> int:
        rows = self._store.scan(_R_ACL)
        if rows:
            self._write(*[(_R_ACL, s, None) for s, _v in rows])
        return len(rows)

    # ══ Links ════════════════════════════════════════════════════════════════════
    def put_link_raw(self, src, dst, rel, w=1.0, d="forward", t="atom",
                     author="system", status="verified", ts=0.0) -> None:
        rk_s, rk_d, rk_r = self._rk(src), self._rk(dst), self._rk(rel)
        rec = {"src": src, "dst": dst, "rel": rel, "w": w, "dir": d, "type": t,
               "author": author, "status": status, "updated_at": ts}
        self._write((rk_s, _PFX_LOUT + rk_d + b"\x00" + rk_r, _j(rec)),
                    (rk_d, _PFX_LIN + rk_s + b"\x00" + rk_r, _j(rec)))

    def remove_link_raw(self, src, dst, rel) -> None:
        rk_s, rk_d, rk_r = self._rk(src), self._rk(dst), self._rk(rel)
        self._write((rk_s, _PFX_LOUT + rk_d + b"\x00" + rk_r, None),
                    (rk_d, _PFX_LIN + rk_s + b"\x00" + rk_r, None))

    def get_adjacent_links(self, src, rel_pattern=None, limit=None,
                           order_by_weight=False) -> List[dict]:
        if order_by_weight and limit is not None:
            # STREAM the top-N outgoing by weight — memory O(limit), not O(density). Same OOM guard
            # as get_incoming_links: a plain scan() materializes every value first (disk mode preads
            # them all). _PFX_LOUT filters to outgoing edges BEFORE the pread.
            def _w_of(v: bytes) -> float:
                try:
                    return float(_u(v).get("w", 1.0) or 1.0)
                except Exception:
                    return 0.0
            _is_out = lambda sk: sk.startswith(_PFX_LOUT)
            out = []
            for _sk, v in self._store.scan_route_topk(self._rk(src), int(limit), _w_of,
                                                      subkey_pred=_is_out):
                rec = _u(v)
                if rel_pattern and not _like(rec["rel"], rel_pattern):
                    continue
                out.append({"dst": rec["dst"], "rel": rec["rel"], "w": rec["w"],
                            "dir": rec["dir"], "type": rec["type"],
                            "author": rec["author"], "status": rec["status"]})
            return out
        out = []
        for subkey, v in self._store.scan(self._rk(src)):
            if not subkey.startswith(_PFX_LOUT):
                continue
            rec = _u(v)
            if rel_pattern and not _like(rec["rel"], rel_pattern):
                continue
            out.append({"dst": rec["dst"], "rel": rec["rel"], "w": rec["w"],
                        "dir": rec["dir"], "type": rec["type"],
                        "author": rec["author"], "status": rec["status"]})
        return out

    def count_adjacent_links(self, src) -> int:
        """Number of OUTGOING edges of `src`, counted from keys only (no value read /
        no disk pread). For the dive's per-signpost "branches ahead" cue, where the count
        is all that is wanted — never the edge contents."""
        _is_out = lambda sk: sk.startswith(_PFX_LOUT)
        return self._store.count_route_subkeys(self._rk(src), subkey_pred=_is_out)

    def count_incoming_links(self, dst) -> int:
        """Number of INCOMING edges of `dst`, counted from keys only (no value read)."""
        _is_in = lambda sk: sk.startswith(_PFX_LIN)
        return self._store.count_route_subkeys(self._rk(dst), subkey_pred=_is_in)

    def get_incoming_links(self, dst, rel_pattern=None, limit=None,
                           order_by_weight=False) -> List[dict]:
        # Weight-ordered top-N (order_by_weight + limit): a mega-hub (a country/company/common
        # tag) can have tens of thousands of incoming edges. Materializing them all is the RAM/GIL
        # storm the dive must avoid. There is no SQL here, so keep only the top-`limit` by weight in
        # a bounded min-heap while scanning — O(density) scan but O(limit) MEMORY, and the strongest
        # edges (the ones the display picks) are never dropped. Plain `limit` (no ordering) still
        # short-circuits the scan for callers that only want "some, bounded".
        if order_by_weight and limit is not None:
            # STREAM the top-N by weight — memory O(limit), not O(density). Materializing every
            # incoming edge of a mega-hub first (what a plain scan does — and in disk mode that
            # preads them all) is the O(density) RAM spike that OOM-killed the daemon on a dive of
            # a dense hub. scan_route_topk reads one value at a time and keeps only the running
            # top-N. The subkey layout is _PFX_LIN + rk_src + \x00 + rk_rel, so this route holds
            # ONLY incoming edges — no _PFX filter needed (unlike the mixed-prefix full scan).
            def _w_of(v: bytes) -> float:
                try:
                    return float(_u(v).get("w", 1.0) or 1.0)
                except Exception:
                    return 0.0
            _is_in = lambda sk: sk.startswith(_PFX_LIN)   # incoming edges only — skip before pread
            out = []
            for _sk, v in self._store.scan_route_topk(self._rk(dst), int(limit), _w_of,
                                                      subkey_pred=_is_in):
                rec = _u(v)
                if rel_pattern and not _like(rec["rel"], rel_pattern):
                    continue
                out.append({"src": rec["src"], "rel": rec["rel"], "w": rec["w"],
                            "dir": rec["dir"], "type": rec["type"],
                            "author": rec["author"], "status": rec["status"]})
            return out
        out = []
        for subkey, v in self._store.scan(self._rk(dst)):
            if not subkey.startswith(_PFX_LIN):
                continue
            rec = _u(v)
            if rel_pattern and not _like(rec["rel"], rel_pattern):
                continue
            out.append({"src": rec["src"], "rel": rec["rel"], "w": rec["w"],
                        "dir": rec["dir"], "type": rec["type"],
                        "author": rec["author"], "status": rec["status"]})
            if limit is not None and len(out) >= limit:
                break
        return out

    # ══ Collections ═══════════════════════════════════════════════════════════════
    def add_to_collection(self, name, key) -> None:
        self._write((_R_COLL + self._rk(name), self._rk(key), b"1"),
                    (self._rk(key), _PFX_COLL + self._rk(name), b"1"))

    def remove_from_collection(self, name, key) -> None:
        self._write((_R_COLL + self._rk(name), self._rk(key), None),
                    (self._rk(key), _PFX_COLL + self._rk(name), None))

    def get_collection_members(self, name) -> List[str]:
        return [s.decode() for s, _v in self._store.scan(_R_COLL + self._rk(name))]

    def collection_exists(self, name) -> bool:
        # Existence only — never read the members' values. scan() would pread every member
        # value (a large set has tens of thousands); count_route_subkeys touches keys only.
        # generate_view calls this on its very first line for every dive focus.
        return self._store.count_route_subkeys(_R_COLL + self._rk(name)) > 0

    def get_collections_for_key(self, key) -> List[str]:
        # Collection name lives in the subkey (_PFX_COLL + name) — no value read needed.
        # Same full-route-pread avoidance as get_aliases_by_key / get_chunk_access_scopes.
        return [sk[len(_PFX_COLL):].decode()
                for sk in self._store.scan_subkeys(self._rk(key), _PFX_COLL)]

    def clear_collection(self, name) -> None:
        rn = _R_COLL + self._rk(name)
        ops = []
        for keyb, _v in self._store.scan(rn):
            ops.append((rn, keyb, None))
            ops.append((keyb, _PFX_COLL + self._rk(name), None))
        if ops:
            self._write(*ops)

    def get_keys_in_any_collection(self, names) -> List[str]:
        seen, out = set(), []
        for name in names:
            for keyb, _v in self._store.scan(_R_COLL + self._rk(name)):
                k = keyb.decode()
                if k not in seen:
                    seen.add(k); out.append(k)
        return out

    def get_keys_in_all_collections(self, names) -> List[str]:
        if not names:
            return []
        sets = [set(k.decode() for k, _v in self._store.scan(_R_COLL + self._rk(n)))
                for n in names]
        common = set.intersection(*sets) if sets else set()
        return list(common)

    def get_collection_members_scoped(self, collection_name, allowed_scopes) -> List[str]:
        perm = [s for s in allowed_scopes if s.startswith(_ACCESS_PREFIXES)]
        if not perm:
            return []
        permset = set(perm)
        members = [k.decode() for k, _v in self._store.scan(_R_COLL + self._rk(collection_name))]
        return [k for k in members if permset & set(self.get_chunk_access_scopes(k))]

    def get_collection_members_locale_ordered(self, collection_name, allowed_scopes,
                                               locale_codes) -> List[str]:
        perm = [s for s in allowed_scopes if s.startswith(_ACCESS_PREFIXES)]
        if not perm:
            return []
        if not locale_codes:
            return self.get_collection_members_scoped(collection_name, allowed_scopes)
        permset = set(perm)
        rank_of = {f"lang:{c}": i for i, c in enumerate(locale_codes)}
        neutral = len(locale_codes)
        scored = []
        for k, _v in self._store.scan(_R_COLL + self._rk(collection_name)):
            key = k.decode()
            if not (permset & set(self.get_chunk_access_scopes(key))):
                continue
            langs = [n for n in self.get_collections_for_key(key) if n.startswith("lang:")]
            if langs:
                rank = min((rank_of.get(l, 999) for l in langs), default=999)
                if rank == 999:                          # has a lang, none requested → excluded
                    continue
            else:
                rank = neutral                            # language-neutral atom is kept
            scored.append((rank, key))
        scored.sort(key=lambda t: t[0])
        return [k for _r, k in scored]

    # ══ Collection defs ═══════════════════════════════════════════════════════════
    def upsert_collection_def(self, name, meta) -> None:
        self._write((_R_CDEF, self._rk(name), _j(meta or {})))

    def get_collection_def(self, name) -> Optional[dict]:
        return _u(self._store.get(_R_CDEF, self._rk(name)))

    def merge_collection_def_meta(self, name, updates) -> None:
        cur = _u(self._store.get(_R_CDEF, self._rk(name))) or {}
        cur.update(updates or {})
        self._write((_R_CDEF, self._rk(name), _j(cur)))

    def list_collection_defs(self, prefix=None) -> List[dict]:
        out = []
        for s, v in self._store.scan(_R_CDEF):
            name = s.decode()
            if prefix and not _like(name, prefix):
                continue
            out.append({"name": name, "meta": _u(v)})
        return out

    def get_distinct_collection_names(self, prefix=None) -> List[str]:
        # Collection names live as the route _R_COLL+name and as forward defs; the
        # authoritative membership index is _R_COLL. Enumerate names via scan_all on
        # that route family.
        names = set()
        rlen = len(_R_COLL)
        for route, _sub, _v in self._store.scan_all():
            if route.startswith(_R_COLL):
                names.add(route[rlen:].decode())
        if prefix:
            names = {n for n in names if _like(n, prefix)}
        return sorted(names)

    # ══ Deferred derivation queue ═════════════════════════════════════════════════
    def _derive_alias_collections(self, alias, key, ops) -> None:
        if ":" not in alias:
            return
        rk = self._rk(key)
        parts = alias.split(":")
        leaf = parts[-1]
        if leaf:
            ops.append((_R_COLL + self._rk(f"leaf:{leaf}"), rk, b"1"))
            ops.append((rk, _PFX_COLL + self._rk(f"leaf:{leaf}"), b"1"))
        prefix = ""
        for ns in parts[:-1]:
            prefix = f"{prefix}:{ns}" if prefix else ns
            nsname = f"ns:{prefix}"
            was = self._store.get(_R_COLL + self._rk(nsname), rk)
            ops.append((_R_COLL + self._rk(nsname), rk, b"1"))
            ops.append((rk, _PFX_COLL + self._rk(nsname), b"1"))
            if was is None:                              # newly a member → bump counter
                cur = self._store.get(_R_NSC, self._rk(prefix))
                cnt = (int(cur) if cur else 0) + 1
                ops.append((_R_NSC, self._rk(prefix), str(cnt).encode()))
            if ns in _ISO_639_1:
                ops.append((_R_COLL + self._rk(f"lang:{ns}"), rk, b"1"))
                ops.append((rk, _PFX_COLL + self._rk(f"lang:{ns}"), b"1"))

    def derive_alias_collections(self, alias, key) -> None:
        ops = []
        self._derive_alias_collections(alias, key, ops)
        if ops:
            self._write(*ops)

    def enqueue_derivation(self, key, alias) -> None:
        import time
        sub = self._rk(key) + b"\x00" + self._rk(alias)
        if self._store.get(_R_PDERIV, sub) is None:       # UNIQUE(key, alias)
            self._write((_R_PDERIV, sub, _j({"seq": self._store.next_id(), "at": time.time()})))

    def peek_pending_derivations(self) -> List[dict]:
        rows = []
        for sub, v in self._store.scan(_R_PDERIV):
            key, _, alias = sub.partition(b"\x00")
            rows.append((_u(v)["seq"], {"key": key.decode(), "alias": alias.decode()}))
        rows.sort(key=lambda t: t[0])
        return [r for _s, r in rows]

    def drain_derivations(self) -> int:
        pend = []
        for sub, v in self._store.scan(_R_PDERIV):
            key, _, alias = sub.partition(b"\x00")
            pend.append((_u(v)["seq"], sub, key.decode(), alias.decode()))
        pend.sort(key=lambda t: t[0])
        count = 0
        for _seq, sub, key, alias in pend:
            ops = [(_R_PDERIV, sub, None)]
            self._derive_alias_collections(alias, key, ops)
            self._write(*ops)
            count += 1
        return count

    # ══ Pending links (DTN) ════════════════════════════════════════════════════════
    def enqueue_pending_link(self, src, dst, rel, author, ts) -> None:
        pid = self._store.next_id()
        rec = {"id": pid, "src": src, "dst": dst, "rel": rel, "author": author, "timestamp": ts}
        self._write((_R_PLINK, str(pid).zfill(20).encode(), _j(rec)))

    def get_pending_links(self) -> List[dict]:
        rows = [_u(v) for _s, v in self._store.scan(_R_PLINK)]
        rows.sort(key=lambda r: r["id"])
        return rows

    def delete_pending_link(self, pid) -> None:
        self._write((_R_PLINK, str(int(pid)).zfill(20).encode(), None))

    # ══ Vault (nucleus / config) ═════════════════════════════════════════════════════
    def vault_store(self, cat, ident, data) -> None:
        self._write((_R_VAULT + self._rk(cat), self._rk(ident), _j(data)))

    def vault_retrieve(self, cat, ident):
        return _u(self._store.get(_R_VAULT + self._rk(cat), self._rk(ident)))

    def vault_scan(self, cat, prefix=None) -> List[tuple]:
        out = []
        for ident_b, v in self._store.scan(_R_VAULT + self._rk(cat)):
            ident = ident_b.decode()
            if prefix and not ident.startswith(prefix):
                continue
            out.append((ident, _u(v)))
        return out

    def vault_delete(self, cat, ident) -> None:
        self._write((_R_VAULT + self._rk(cat), self._rk(ident), None))

    # ══ Streaming & export ═══════════════════════════════════════════════════════════
    def _all_chunk_recs(self):
        # ONE bounded scan of the chunk-key index (not scan_all over every route).
        for keyb, _seq in self._store.scan(_R_CHUNKS):
            rec = _u(self._store.get(keyb, _SUB_CHUNK))
            if rec is not None:
                yield keyb.decode(), rec

    def fetch_stream(self, limit=10) -> List[dict]:
        pairs = []
        for keyb, seqb in self._store.scan(_R_CHUNKS):
            rec = _u(self._store.get(keyb, _SUB_CHUNK))
            if rec is not None:
                pairs.append((int(seqb), keyb.decode(), rec))
        pairs.sort(key=lambda t: t[0], reverse=True)
        return [{"key": k, "content": r["content"], "created_at": r["created_at"],
                 "meta": r["meta"], "author": r["author"], "status": r["status"]}
                for _s, k, r in pairs[:limit]]

    def get_all_chunks(self, limit=None) -> List[dict]:
        # `_all_chunk_recs()` is a generator that preads ONE value at a time; when a `limit`
        # is given we stop iterating at the cap, so on the disk-value store we pread at most
        # `limit` values (never the whole corpus into RAM — the boot-autolearn OOM guard).
        out = []
        for k, r in self._all_chunk_recs():
            out.append({"key": k, "content": r["content"], "created_at": r["created_at"],
                        "meta": r["meta"], "author": r["author"], "status": r["status"]})
            if limit is not None and len(out) >= limit:
                break
        return out

    def get_all_keys(self) -> List[str]:
        return [k.decode() for k, _seq in self._store.scan(_R_CHUNKS)]

    def get_all_links(self, rel_filter=None, limit=5000) -> List[dict]:
        # Cap the ACCUMULATION at `limit` (not just the returned slice): the scan used to
        # materialize EVERY link before slicing, an unbounded RAM allocation at boot
        # (node-autolearn passes a large limit). Stopping the scan at the cap keeps peak
        # memory proportional to what is actually returned.
        out = []
        for route, subkey, v in self._store.scan_all():
            if not subkey.startswith(_PFX_LOUT):
                continue
            rec = _u(v)
            if rel_filter and rec["rel"] != rel_filter:
                continue
            out.append({"src": rec["src"], "dst": rec["dst"], "rel": rec["rel"], "w": rec["w"]})
            if limit is not None and len(out) >= limit:
                break
        out.sort(key=lambda r: (r["rel"], r["src"]))
        return out

    def get_recent_atom_hashes(self, since) -> List[str]:
        out = []
        for k, r in self._all_chunk_recs():
            try:
                if float(r["created_at"]) > since:
                    out.append(k)
            except (ValueError, TypeError):
                pass
        return out

    def get_recent_links(self, since) -> List[dict]:
        out = []
        for route, subkey, v in self._store.scan_all():
            if not subkey.startswith(_PFX_LOUT):
                continue
            rec = _u(v)
            if (rec.get("updated_at") or 0) > since:
                out.append({"src": rec["src"], "dst": rec["dst"], "rel": rec["rel"],
                            "author": rec["author"], "timestamp": rec["updated_at"]})
        return out

    def get_namespace_counts(self, depth=1) -> List[dict]:
        rows = [{"ns": s.decode(), "count": int(v)} for s, v in self._store.scan(_R_NSC)]
        if depth == 1:
            rows = [r for r in rows if ":" not in r["ns"]]
        rows.sort(key=lambda r: (-r["count"], r["ns"]))
        return rows

    def fetch_by_meta_field(self, field, value, author=None, limit=200) -> List[dict]:
        out = []
        for k, r in self._all_chunk_recs():
            try:
                meta = json.loads(r["meta"]) if r["meta"] else {}
            except Exception:
                meta = {}
            if str(meta.get(field)) != str(value):
                continue
            if author and r["author"] != author:
                continue
            out.append({"key": k, "content": r["content"], "created_at": r["created_at"],
                        "meta": r["meta"], "author": r["author"], "status": r["status"]})
        return out[:limit]

    def get_keys_by_scope(self, scope) -> List[str]:
        return [k.decode() for k, _v in self._store.scan(_R_SCOPE + self._rk(scope))]

    def get_keys_by_status(self, status, limit=None) -> List[str]:
        out = [k for k, r in self._all_chunk_recs() if r["status"] == status]
        return out[:limit] if limit is not None else out

    # ══ Aggregates ═══════════════════════════════════════════════════════════════════
    def get_store_totals(self) -> dict:
        chunks = links = aliases = 0
        coll_names = set()
        for route, subkey, _v in self._store.scan_all():
            if subkey == _SUB_CHUNK:
                chunks += 1
            elif subkey.startswith(_PFX_LOUT):
                links += 1
            elif route == _R_ALIAS:
                aliases += 1
            elif route.startswith(_R_COLL):
                coll_names.add(route)
        return {"chunks": chunks, "links": links, "aliases": aliases,
                "collections": len(coll_names)}

    # ══ Lifecycle ════════════════════════════════════════════════════════════════════
    def checkpoint(self) -> None:
        self._store.checkpoint()

    def close(self) -> None:
        self._store.close()


def _like(text: str, pattern: str) -> bool:
    """SQL LIKE (case-insensitive) via fnmatch — '%'→'*', '_'→'?'."""
    return fnmatch.fnmatch(text.lower(), pattern.lower().replace("%", "*").replace("_", "?"))
