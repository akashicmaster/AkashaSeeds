"""
UniversalConcept — a shared base for the Labo world-model layer (cronon / labo / research / analysis).

These concept models write UNIVERSAL, guest-readable atoms — a public laboratory exposes its Source,
Concept, Society and Notebook material to anyone. So, exactly like the Source Data Layer, their
WRITES are routed to the shared NUCLEUS (not the calling session's private cortex); reads stay on
`self.cortex`, which already unions the nucleus. This module factors out that write path plus a
single monotonic **Akasha-Time** counter (the `cronon:clock`) that the whole layer shares, so
Research Chunks, analysis runs and interpretations all order on ONE logical clock.

The filename starts with `_`, so the ConceptRegistry does NOT discover it as a model (it is a base,
not a command surface).
"""
import json
import re
import threading
import time
from typing import Any, Dict, List, Optional

from lib.akasha.concepts.base import BaseConcept

# ── imports for the universal ops moved from the kernel (backend layout order 2026-09-20) ──
import os
import re
import sys
import time
import json
import uuid
import logging
import hashlib
import functools
from typing import Dict, Any, Optional, List, Callable
from lib.akasha.resolver import ContextResolver
from lib.akasha.api.heart import _NucleusWriteCtx, _FEED_WRITER, _BROADCASTER
from lib.akasha.api.rpc import ok as _ok, err as _err
from lib.akasha.pagination import paginate as _paginate, resolve_limit as _rlimit, resolve_offset as _roffset
from lib.akasha import lexicon
from lib.akasha.ontology import weave
import logging
from lib.akasha.concepts import horizon_ops
from lib.akasha.ontology.weave import _is_external, _is_raw_source

logger = logging.getLogger("Akasha.Kernel")

# Process-local high-water mark per (store, clock) for the Akasha-Time counter. There is ONE writer
# process, so an in-memory monotonic mark is the AUTHORITY that makes the counter race-free even when
# the durable atom's value is momentarily stale to a reader (SQLite WAL: a same-turn write committed on
# the WriteQueue worker connection is not always visible to a fresh read on the caller-thread
# connection, so two mints in quick succession could otherwise read the same base and allocate a
# COLLIDING position). The atom is still written for durability; on process start the mark seeds from
# it. Guarded by a lock — mint is called from portal + JCL threads.
_CLOCK_HWM: Dict[str, int] = {}
_CLOCK_HWM_LOCK = threading.Lock()

UNIVERSAL = "scope:sys:universal"


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(s or "").lower()).strip("_")


class UniversalConcept(BaseConcept):
    """Nucleus-routed universal writes + a shared Akasha-Time coordinate."""

    # ── store plumbing ──────────────────────────────────────────────────────────
    @property
    def _nuc(self):
        """The shared nucleus engine (universal, guest-readable store), or None on a single-store
        edge cell (where the local cortex IS the shared store)."""
        return getattr(self.cortex, "_nucleus", None)

    # ── G1.2 — optional space routing: nucleus (default) OR a group engine (a closed bench). A
    #    subclass sets `self._space = "group:<gid>"` to place its atoms in that group's engine
    #    (private to members). Empty keeps the exact universal (nucleus) path — cronon/labo unchanged.
    def _group_engine(self, gid: str):
        ge = getattr(self.session, "group_engines", {}).get(gid)
        if ge is None or f"scope:group_{gid}" not in (self.allowed_scopes or []):
            raise RuntimeError(f"Not a member of group '{gid}'.")
        return ge

    def _store(self):
        """The engine writes route to for the active space: a group engine for `space=group:<gid>`,
        else the shared nucleus. None ⇒ a single-store edge cell (the local cortex)."""
        sp = getattr(self, "_space", "") or ""
        if sp.startswith("group:"):
            return self._group_engine(sp.split(":", 1)[1])
        return self._nuc

    def _read_core(self):
        """The group-space core to read from when a group space is active (self.cortex does not union
        a group engine), else None ⇒ read via self.cortex (which unions local+nucleus)."""
        sp = getattr(self, "_space", "") or ""
        if sp.startswith("group:"):
            try:
                return self._group_engine(sp.split(":", 1)[1]).core
            except Exception:
                return None
        return None

    def _author(self) -> str:
        return getattr(self.session, "client_id", "system") or "system"

    def key(self, ident: Optional[str]) -> Optional[str]:
        """Resolve an id (alias OR raw key) to a stored key across the active group space (when set),
        then local + nucleus, or None."""
        if not ident:
            return None
        rc = self._read_core()
        if rc is not None:
            if rc.get_chunk_raw(ident):
                return ident
            k = rc.get_key_by_alias(ident)
            if k:
                return k
        core = self.cortex.core
        if core.get_chunk_raw(ident):
            return ident
        nuc = self._nuc
        if nuc and nuc.core.get_chunk_raw(ident):
            return ident
        k = core.get_key_by_alias(ident)
        if k:
            return k
        if nuc:
            k = nuc.core.get_key_by_alias(ident)
            if k:
                return k
        return None

    def alias(self, key: Optional[str]) -> Optional[str]:
        if not key:
            return key
        rc = self._read_core()
        if rc is not None:
            al = rc.get_aliases_by_key(key)
            if al:
                return al[0]
        al = self.cortex.core.get_aliases_by_key(key)
        if not al and self._nuc:
            al = self._nuc.core.get_aliases_by_key(key)
        return al[0] if al else key

    def mk(self, alias: str, content: str, meta: Dict[str, Any]) -> str:
        """Write a universal atom to the active store (nucleus, or a group engine for space=group:<gid>)
        and alias it (stable id). Idempotent by alias — a re-run returns the existing atom unchanged."""
        existing = self._key(alias)
        if existing:
            return existing
        meta = dict(meta or {})
        nuc = self._store()
        if nuc is not None:
            key = nuc.put_atom(content, meta, author=self._author())
            nuc.core.put_alias(key, alias)
            return key
        key = self.cortex.put_chunk(content=content, meta=meta, author=self._author(), scopes=[UNIVERSAL])
        self.cortex.core.put_alias(key, alias)
        return key

    def mk_replace(self, alias: str, content: str, meta: Dict[str, Any],
                    compare_meta=()) -> tuple:
        """A43 — create-or-REPLACE a universal atom by alias. Unlike `_mk` (create-if-absent, which
        many callers rely on and which is UNCHANGED), when the alias already exists and any of the
        caller-named `compare_meta` keys differs from the stored meta, mint a NEW content-addressed
        atom, RE-POINT the alias to it (INSERT OR REPLACE on the alias), and stamp the new atom with
        `supersedes`/`replaced_wall`/`replaced_by` provenance. The OLD atom stays in the store — history
        is knowledge, and rollback must be able to reach it. Returns `(key, changed, old_key)`:
        `changed` is True when a new atom was minted (created OR replaced); `old_key` is the superseded
        key on a replace, else None. On an identical entry it is a no-op (`changed=False`)."""
        existing = self._key(alias)
        meta = dict(meta or {})
        if not existing:
            return self._mk(alias, content, meta), True, None
        old_meta = self._meta(alias) or {}
        if all(old_meta.get(k) == meta.get(k) for k in (compare_meta or ())):
            return existing, False, None                 # identical on the named keys — no-op
        # replace: mint the new content-addressed atom, re-point the alias, record provenance
        _by = None
        _cl = getattr(self, "_client", None)
        if callable(_cl):
            try:
                _by = _cl()
            except Exception:
                _by = None
        meta.setdefault("supersedes", existing)
        meta.setdefault("replaced_wall", round(__import__("time").time(), 3))
        meta.setdefault("replaced_by", _by or self._author())
        nuc = self._store()
        if nuc is not None:
            key = nuc.put_atom(content, meta, author=self._author())
            nuc.core.put_alias(key, alias)
        else:
            key = self.cortex.put_chunk(content=content, meta=meta, author=self._author(),
                                        scopes=[UNIVERSAL])
            self.cortex.core.put_alias(key, alias)
        return key, True, existing

    def link(self, src_id: str, dst_id: str, rel: str) -> bool:
        """Link two atoms by key (resolving aliases), in the active store. A dst that is not yet a
        stored atom (an external/foreign id) is linked as given."""
        sk = self._key(src_id)
        if not sk:
            return False
        dk = self._key(dst_id) or dst_id
        nuc = self._store()
        if nuc is not None:
            nuc.put_link(sk, dk, rel, author=self._author())
        else:
            self.cortex.put_link(sk, dk, rel, author=self._author())
        return True

    def add_to_set(self, name: str, key: str) -> None:
        nuc = self._store()
        if nuc is not None:
            nuc.add_to_set(name, key)
        else:
            self.cortex.add_to_set(name, key)

    def remove_from_set(self, name: str, key: str) -> None:
        """Space-aware set removal (mirror of _add_to_set): the active group engine / nucleus / local
        cortex, whichever _store() selects for the current _space."""
        nuc = self._store()
        try:
            if nuc is not None:
                nuc.core.remove_from_collection(name, key)
            else:
                self.cortex.remove_from_collection(name, key)
        except Exception:
            pass

    def set_meta(self, key: str, meta_key: str, value: Any) -> None:
        nuc = self._store()                  # one atomic merge in the store that holds the row
        if nuc is not None and nuc.core.merge_meta(key, {meta_key: value}) is not None:
            return
        self.cortex.set_meta(key, meta_key, value)

    def meta(self, ident: str) -> Dict[str, Any]:
        k = self._key(ident)
        if not k:
            return {}
        rc = self._read_core()
        if rc is not None:
            try:
                row = rc.get_chunk_raw(k)
                if row is not None:
                    return (json.loads(row["meta"]) if row.get("meta") else {}) or {}
            except Exception:
                pass
        return (self.cortex.get_meta(k) or {})

    def members(self, set_name: str) -> List[str]:
        rc = self._read_core()
        if rc is not None:
            try:
                return list(rc.get_collection_members(set_name) or [])
            except Exception:
                return []
        try:
            return list(self.cortex.get_collection_members(set_name) or [])
        except Exception:
            return []

    def collections_for(self, key: str) -> List[str]:
        """The collection names a key belongs to (META only — the collections table, never a body).
        Space-aware, mirroring `_members`/`_meta`. Empty on any error."""
        rc = self._read_core()
        if rc is not None:
            try:
                return list(rc.get_collections_for_key(key) or [])
            except Exception:
                return []
        try:
            return list(self.cortex.get_collections_for_key(key) or [])
        except Exception:
            return []

    def links(self, ident: str, rel: Optional[str] = None):
        """Outgoing (dst_alias, rel) pairs for an atom, resolved for display."""
        k = self._key(ident)
        if not k:
            return []
        out = []
        for dst, r in self.cortex.get_adjacent_links(k, rel):
            out.append((self._alias(dst), r))
        return out

    # ── shared Akasha-Time coordinate (the cronon clock) ─────────────────────────
    def clock_alias(self, clock: str = "") -> str:
        """The clock atom's alias. Empty ⇒ the shared default clock `cronon:clock` (unchanged);
        a non-empty name ⇒ its own clock atom `cronon:clock:<name>` (G0.1 — the world model runs
        the `world:default` axis on its own clock `cronon:clock:world:default`)."""
        return "cronon:clock" if not clock else f"cronon:clock:{clock}"

    def akasha_now(self, clock: str = "") -> int:
        """The current Akasha-Time position on the given clock — a monotonic logical counter. Empty
        `clock` is the ONE shared default clock the whole Labo layer orders on (Research Chunks,
        analysis runs, interpretations); a named clock (G0.1) is an independent counter (the shared
        `world:default` axis). Serial writes make it effectively race-free. A COORDINATE, not an
        execution step (§1.1)."""
        alias = self._clock_alias(clock)
        clk = self._key(alias)
        if not clk:
            clk = self._mk(alias, f"[{alias}] Akasha-Time counter (monotonic coordinate; NOT a "
                           "scheduler — execution synchronizes on Akasha Time, Akasha Time executes "
                           "nothing).", {"concept": "cronon_clock", "at_seq": 0, "clock": clock or "default"})
        # The durable value (may be momentarily stale to a reader — see _CLOCK_HWM above).
        store = self._store()
        if store is not None:
            row = store.core.get_chunk_raw(clk)
            try:
                durable = int((json.loads(row["meta"]) if row and row.get("meta") else {}).get("at_seq", 0))
            except Exception:
                durable = 0
        else:
            durable = int((self.cortex.get_meta(clk) or {}).get("at_seq", 0))
        # The process-local mark is the monotonic AUTHORITY (single writer process); seed it from the
        # durable value the first time this clock is seen, then advance it in memory so no two mints
        # can collide even if the durable read lags.
        with _CLOCK_HWM_LOCK:
            seq = max(_CLOCK_HWM.get(clk, 0), durable) + 1
            _CLOCK_HWM[clk] = seq
        self._set_meta(clk, "at_seq", seq)
        return seq

    def now_wall(self) -> float:
        return round(time.time(), 3)

    # ── G4 — coordinate = Set. A cronon coordinate `cronon:<clock>:c<n>` is ALSO the name of a Set;
    #    anything located at that coordinate is a MEMBER of it. These helpers are the ONE write path
    #    for "locate X at coordinate n on clock C" — the coordinate atom (position + ordering) is
    #    minted idempotently, and X joins its Set. `cronon:at` is no longer the location mechanism
    #    (kept only through the migration window, §5).
    def cronon_coord(self, clock: str, seq: int, wall: str = "", prefix: str = "c") -> str:
        """Ensure the coordinate atom `cronon:<clock>:<prefix><seq>` exists (concept=cronon,
        position=seq), indexed in `cronon:<clock>:all` and chained `cronon:follows`. `prefix` is `c`
        for the world/bench RECORD clocks and `p` for a workflow BRANCH (plan) clock (§1.3). Returns
        the coordinate alias. Idempotent."""
        cid = f"cronon:{clock}:{prefix}{int(seq)}"
        if not self._key(cid):
            meta = {"concept": "cronon", "position": int(seq), "clock": clock,
                    "minted_wall": self._now_wall(),
                    "mappings": ([{"frame": "wall_clock", "value": wall}] if wall else [])}
            self._mk(cid, f"[{cid}] Akasha-Time position {int(seq)}", meta)
            self._add_to_set(f"cronon:{clock}:all", self._key(cid))
            prev = f"cronon:{clock}:{prefix}{int(seq) - 1}"
            if int(seq) > 1 and self._key(prev):
                self._link(cid, prev, "cronon:follows")
        elif wall and not (self._meta(cid) or {}).get("mappings"):
            self._set_meta(self._key(cid), "mappings", [{"frame": "wall_clock", "value": wall}])
        return cid

    def akasha_peek(self, clock: str = "") -> int:
        """The current position on `clock` WITHOUT advancing it (a read, not a tick) — used to place a
        record at the world's CURRENT coordinate (G4 §1.7b) without minting a new one."""
        clk = self._key(self._clock_alias(clock))
        if not clk:
            return 0
        rc = self._read_core()
        try:
            if rc is not None:
                row = rc.get_chunk_raw(clk)
                return int((json.loads(row["meta"]) if row and row.get("meta") else {}).get("at_seq", 0))
        except Exception:
            pass
        return int((self.cortex.get_meta(clk) or {}).get("at_seq", 0))

    def cronon_locate(self, clock: str, seq: int, member_key: str, wall: str = "",
                       prefix: str = "c") -> str:
        """Locate `member_key` at coordinate `seq` on `clock` — membership IS the location (G4 §1.7).
        Returns the coordinate alias."""
        cid = self._cronon_coord(clock, seq, wall, prefix)
        if member_key:
            self._add_to_set(cid, member_key)
        return cid

    # ── THE SDK, and its old spelling (group 4, 4.16) ────────────────────────────────────────────
    # These helpers are the application's SDK: every Concept Model a client authors builds its atoms,
    # Sets, links and coordinates through them. They had underscore names, so an application model
    # calling them was reaching into a PLATFORM class's private members — 37 such reaches on
    # 2026-09-26, held by `ownership_eval`'s ratchet. The ruling: the base class IS the SDK, so the
    # helpers get public, documented names (above). The underscore spellings below are ALIASES,
    # kept for ONE seed while the application switches; then they go, and the ratchet reaches 0.
    # A subclass that overrides an underscore name keeps its override for the underscore name, as
    # before; the public name always means the base helper.
    _key = key
    _alias = alias
    _mk = mk
    _mk_replace = mk_replace
    _link = link
    _add_to_set = add_to_set
    _remove_from_set = remove_from_set
    _set_meta = set_meta
    _meta = meta
    _members = members
    _collections_for = collections_for
    _links = links
    _clock_alias = clock_alias
    _akasha_now = akasha_now
    _now_wall = now_wall
    _cronon_coord = cronon_coord
    _akasha_peek = akasha_peek
    _cronon_locate = cronon_locate


# ── the universal ops (read/write/define/link/alias/meta/set), moved from the kernel ──
def resolve_target(kernel, target: str, session, history: list) -> Optional[str]:
    """Resolves $-references, aliases, and direct keys. Returns None on failure."""
    try:
        return ContextResolver.resolve(session, target, history)
    except Exception:
        return None


def handle_write(kernel, rid, data, session, ctx, scopes, client_id) -> dict:
    text = data.get("text") or data.get("content", "")
    if not text:
        return _err(rid, -32602, "write requires 'text'")

    meta = data.get("meta", {})
    if isinstance(meta, str):
        try:
            meta = json.loads(meta)
        except Exception:
            meta = {}

    # Derive write scopes: user's private scope + any explicit overrides.
    # When ctx is _NucleusWriteCtx (scope=universal + librarian), put_chunk
    # routes to nucleus automatically — no branching needed here.
    write_scopes = [f"owner:user_{client_id}", f"view:user_{client_id}"]
    if "view:public" in scopes and data.get("public"):
        write_scopes.append("view:public")
    key = ctx.put_chunk(content=text, meta=meta, author=client_id, scopes=write_scopes)

    session.set_context("last_written_id", key)
    session.last_written_id = key

    weave.post_write(kernel, session, isinstance(ctx, _NucleusWriteCtx), key, text)

    return _ok(rid, {"key": key, "status": "written"})


def handle_define(kernel, rid, data, session, ctx, scopes, client_id) -> dict:
    name = data.get("name", "").strip()
    if not name:
        return _err(rid, -32602, "define requires 'name'")

    description = data.get("description") or f"Conceptual hub: {name}"
    # ONE definition of what a def writes — the reconcile's keep-set hashes the same thing from the
    # files to know which keys they define (D16), so the two can never disagree.
    from lib.akasha.ontology.loader import def_hub_content as _def_hub_content
    hub_content = _def_hub_content(name, description)

    # canonical=True marks this as the authoritative, explicitly-authored definition.
    # Implicit/auto-created atoms (proto-words) have auto_created=True instead.
    # Inferred links (specializes, proto-word scaffolding) carry status="inferred".
    meta = {"type": "hub", "name": name, "role": "concept", "canonical": True}
    write_scopes = [f"owner:user_{client_id}", f"view:user_{client_id}"]
    key = ctx.put_chunk(content=hub_content, meta=meta, author=client_id, scopes=write_scopes)
    # Authoritative ontology re-import (scope=universal) must UPDATE a changed def, not
    # silently keep the stale atom. Content-addressing gives edited text a NEW key, so
    # plain first-wins would leave the alias on the old atom and orphan the new content
    # (the release's fix never reaches the user). When the incumbent lives in the NUCLEUS
    # it is pack/ontology content (users can't write there) → rebind is safe and the
    # collision is logged for onto.report. A user cell atom holding the alias keeps
    # first-wins untouched. Ordinary (non-universal) user defines are unaffected.
    _force = False
    if str(data.get("scope", "")) == "universal":
        _nuc = getattr(session, "nucleus", None)
        if _nuc is not None:
            _prev = _nuc.core.get_key_by_alias(name)
            if _prev and _prev != key:
                _force = True
    ctx.set_alias(key, name, force=_force)

    session.set_context("last_written_id", key)

    weave.post_write(kernel, session, isinstance(ctx, _NucleusWriteCtx), key,
                     description, f"sys.weaver:{name[:40]}")

    return _ok(rid, {"key": key, "alias": name, "status": "defined"})


def asof_param(data):
    """Parse as_of=<epoch> → int, or None when absent/blank. A non-integer raises (caller -32602)."""
    v = data.get("as_of")
    if v is None or str(v).strip() == "":
        return None
    return int(str(v).strip())


def atom_epoch(meta):
    """The atom's FIRST recorded Akasha-Time position — the earliest at_seq it can be placed at
    (at_seq / cronon / built_at_epoch). None when the atom carries no epoch (pre-history → it cannot
    be proven newer than any as_of, so an as-of read includes it — honest per §A5)."""
    for k in ("at_seq", "cronon", "built_at_epoch", "created_epoch"):
        v = (meta or {}).get(k)
        if isinstance(v, int):
            return v
        try:
            if v is not None and str(v).strip() != "":
                return int(v)
        except (TypeError, ValueError):
            continue
    return None


def is_horizon_name(kernel, name):
    """True for a horizon / accelerator Set or atom (semcache/exec/stage/hydrate/store/coordinate) —
    a materialized horizon is an accelerator, never durable truth, so as-of is refused there (§A5)."""
    s = str(name or "")
    return any(s.startswith(p) for p in kernel._ASOF_HORIZON_PREFIXES)


def atom_meta_resolved(ctx, nucleus, key):
    """B4-a — an atom's meta resolved NUCLEUS-AWARE. A Set member often lives in the shared nucleus,
    which a guest's read cortex does NOT union for `get_meta` — so an as-of read that reads only
    `ctx.get_meta(key)` sees `None` for every nucleus atom, reads it as pre-history, and keeps it
    (the B4-a defect). Fall back to the nucleus the way `r` does (the resolver the display-focus
    filter receives as `nucleus`). Returns {} when neither engine resolves the key."""
    m = None
    try:
        m = ctx.get_meta(key)
    except Exception:
        m = None
    if not m and nucleus is not None:
        try:
            m = nucleus.get_meta(key)
        except Exception:
            m = None
    return m or {}


def meta_as_of(kernel, meta, epoch):
    """The atom's meta AS OF `epoch`: the newest `_asof_hist` version whose at_seq ≤ epoch, else the
    current meta (an atom with no recorded history has none before its first at_seq — honest)."""
    hist = (meta or {}).get("_asof_hist") or []
    picked = None
    for h in sorted(hist, key=lambda e: int(e.get("at_seq", 0))):
        if int(h.get("at_seq", 0)) <= int(epoch):
            picked = h.get("meta")
    return picked if picked is not None else meta


def handle_read(kernel, rid, data, session, ctx, scopes, history) -> dict:
    target = data.get("id") or data.get("target", "")
    if not target:
        target = session.last_written_id or ""
    if not target:
        return _err(rid, -32602, "read requires 'id' or an active session context")

    resolved = resolve_target(kernel, target, session, history) or target
    # Scoped read only.  get_scoped_chunk applies check_access and returns
    # None on BOTH "denied" and "not found" — we must NOT fall back to an
    # unscoped get_chunk(), which would leak atoms outside the caller's
    # scope (including nucleus-resident collective/DNA/admin atoms).
    content = ctx.get_scoped_chunk(resolved, scopes)
    if content is None:
        # Group-space fallback: an atom shared into one of the caller's groups
        # lives in that group's engine, not the local cortex. Membership is
        # proven two ways before revealing it: scope:group_<gid> is in the
        # caller's scopes AND the atom carries that group's scope
        # (ge.check_access) — mirrors the consciousness/view fallback so `r` is
        # consistent with `look`. Link-graph traversal is not attempted for a
        # group atom here; `look` gives the full associative view.
        for gid, ge in kernel._member_group_engines(session, scopes):
            if not ge.check_access(resolved):
                continue
            gc = ge.get_chunk(resolved)
            if gc is None:
                continue
            grow = ge.get_chunk_raw(resolved) or {}
            try:
                import json as _json
                gmeta = _json.loads(grow.get("meta") or "{}")
            except Exception:
                gmeta = {}
            return _ok(rid, {
                "key":       resolved,
                "content":   gc,
                "meta":      gmeta,
                "aliases":   ge.get_aliases_by_key(resolved),
                "out_links": [],
                "in_links":  [],
                "sets":      ge.core.get_collections_for_key(resolved),
                "shared_from": f"group:{gid}",
            })
        from lib.akasha.ontology.loader import loading_note as _loading_note
        _note = _loading_note(kernel)
        if _note:
            return _err(rid, -32002, f"Atom not found: '{target}' — {_note}")
        return _err(rid, -32002, f"Atom not found or out of scope: '{target}'")

    nucleus = getattr(session, 'nucleus', None)
    focus   = horizon_ops.get_display_focus(kernel, session)
    if focus and not horizon_ops.passes_display_focus(kernel, resolved, focus, ctx, nucleus):
        return _err(rid, -32002, f"Atom not in current focus: '{target}'")

    meta    = ctx.get_meta(resolved)
    aliases = ctx.get_aliases_by_key(resolved)

    # B4 §A5 — as-of: read the atom's META as of an epoch (content is immutable, returned as-is). A
    # horizon/accelerator atom (a coordinate, a stage/exec cache) has no durable history → refuse.
    # Before the atom's FIRST recorded at_seq it did not exist → absent (honest). `_asof_hist` (a
    # versioned writer's bounded meta history) is replayed when present; otherwise the current meta is
    # the only recorded version.
    _asof = asof_param(data)
    _asof_first = None
    if _asof is not None:
        if is_horizon_name(kernel, resolved) or any(is_horizon_name(kernel, a) for a in (aliases or [])):
            return _err(rid, -32602, "as_of is not defined for a horizon read")
        _asof_first = atom_epoch(meta or {})
        if _asof_first is not None and _asof < _asof_first:
            return _err(rid, -32002, f"Atom did not exist as of {_asof}: '{target}'")
        meta = meta_as_of(kernel, meta, _asof)

    # Build link list with previews for display.  A neighbour's content and
    # aliases are only revealed if the caller may actually see that neighbour;
    # out-of-scope endpoints show the edge but redact the payload so links
    # cannot be used to enumerate private/nucleus atoms.
    _rel_desc_cache: dict = {}
    def _rd(rel: str):
        # First-class relation: the reldef:<rel> full-spelling, memoised per rel.
        if rel not in _rel_desc_cache:
            _rel_desc_cache[rel] = lexicon.rel_description(ctx, rel)
        return _rel_desc_cache[rel]

    def _link_entry(key: str, rel: str, direction: str) -> dict:
        rd = _rd(rel)
        if not ctx.check_access(key, scopes):
            entry = {
                "key":       key,
                "rel":       rel,
                "direction": direction,
                "aliases":   [],
                "preview":   "",
                "restricted": True,
            }
            if rd: entry["rel_desc"] = rd
            return entry
        preview = ctx.get_chunk(key) or ""
        entry = {
            "key":       key,
            "rel":       rel,
            "direction": direction,
            "aliases":   ctx.get_aliases_by_key(key),
            "preview":   preview[:60],
        }
        if rd: entry["rel_desc"] = rd
        return entry

    out_links = [_link_entry(dst, rel, "out")
                 for dst, rel in ctx.get_adjacent_links(resolved)
                 if not focus or horizon_ops.passes_display_focus(kernel, dst, focus, ctx, nucleus)]
    in_links  = [_link_entry(src, rel, "in")
                 for src, rel in ctx.get_incoming_links(resolved)
                 if not focus or horizon_ops.passes_display_focus(kernel, src, focus, ctx, nucleus)]

    # Set membership: which collections contain this atom
    # local and nucleus merged — a membership recorded in either store is the atom's (findings P1:
    # an atom with any local membership hid every set the nucleus held for it)
    sets: list = list(ctx.core.get_collections_for_key(resolved) or [])
    if nucleus:
        _seen = set(sets)
        sets += [n for n in (nucleus.core.get_collections_for_key(resolved) or []) if n not in _seen]

    # First-class namespace: plain-language gloss of the atom's namespace prefix.
    ns_desc = lexicon.namespace_description(
        ctx, lexicon.namespace_of_alias(aliases[0] if aliases else None))

    result = {
        "key":      resolved,
        "content":  content,
        "meta":     meta,
        "aliases":  aliases,
        "out_links": out_links,
        "in_links":  in_links,
        "sets":     sets,
    }
    if ns_desc:
        result["namespace_desc"] = ns_desc
    if _asof is not None:
        result["as_of"] = _asof
        result["history_from"] = _asof_first
    return _ok(rid, result)


def handle_drop(kernel, rid, data, session, ctx, scopes) -> dict:
    target = data.get("id") or data.get("target", "")
    if not target:
        return _err(rid, -32602, "drop requires 'id'")

    history = ctx.stream(10)
    resolved = resolve_target(kernel, target, session, history) or target

    result = ctx.drop_chunk(resolved, requester_scopes=scopes)
    if "error" in result:
        return _err(rid, -32001, result["error"])

    return _ok(rid, result)


def handle_link(kernel, rid, data, session, ctx, client_id) -> dict:
    src = data.get("src", "")
    dst = data.get("dst", "")
    rel = data.get("rel", "sys:associated_with")
    w   = float(data.get("w", 1.0))

    if not src or not dst:
        return _err(rid, -32602, "link requires 'src' and 'dst'")

    # "=" prefix on src/dst opts into strict alias resolution: the link
    # dangles permanently if the target is not registered, rather than
    # falling back to the bare-segment proto-word (the default behaviour).
    # Used when two namespace atoms are intentionally distinct senses
    # and the link must target the specific sense, not the shared proto-word.
    src_strict = src.startswith("=")
    if src_strict:
        src = src[1:]
    dst_strict = dst.startswith("=")
    if dst_strict:
        dst = dst[1:]

    # Normalize bare-word relations to proper semantic namespace at write-time.
    # Known types remap to their canonical ns (antonym→sys:antonym, evoked_by→emo:, …).
    # All other bare words default to calc: (general conceptual vocabulary).
    if rel and ':' not in rel and not rel.startswith('@'):
        from lib.akasha.composite import _BARE_REL_REMAP
        rel = _BARE_REL_REMAP.get(rel, f"calc:{rel}")

    _src_alias_resolved = ctx.resolve_alias(src)
    src_key = _src_alias_resolved or src
    _dst_alias_resolved = ctx.resolve_alias(dst)
    dst_key = _dst_alias_resolved or dst

    # ctx.put_link routes to the correct store when ctx is _NucleusWriteCtx.
    # For local_cortex ctx: if the src atom lives in nucleus, write the link
    # there so it is visible to all cells (not buried in one cell's DB).
    # When ctx is _NucleusWriteCtx, resolve_alias already preferred nucleus
    # keys, so no extra alias lookup is needed.
    nucleus = getattr(session, 'nucleus', None)
    # A 64-char hex value is a raw atom key ($var.key expansions, or the
    # canon normalizer's proto-word roll-up which targets an exact key to
    # avoid alias ambiguity) — never a proto-word to mint. Guard both write
    # branches so a raw key is used verbatim, not content-addressed into a
    # new atom whose text is the hash string.
    _is_hex = lambda v: len(v) == 64 and all(c in '0123456789abcdef' for c in v)
    if isinstance(ctx, _NucleusWriteCtx):
        # Late-binding: auto-create proto-words for any unresolved alias.
        # Using the bare segment (last ':'-delimited token) as the universal
        # anchor means ordering and repeated execution are both irrelevant.
        # When the qualified atom is later defined, it links back to the
        # same proto-word via 'specializes', making the graph path traversable.
        if _src_alias_resolved is None and not _is_hex(src):
            bare_src = src.rsplit(":", 1)[-1] if ":" in src else src
            src_key = nucleus._ensure_protoword(bare_src)
        if _dst_alias_resolved is None and not _is_hex(dst):
            bare_dst = dst.rsplit(":", 1)[-1] if ":" in dst else dst
            dst_key = nucleus._ensure_protoword(bare_dst)
        ctx.put_link(src_key, dst_key, rel, w=w, author=client_id)
    else:
        # Prefer nucleus alias resolution over ctx for local_cortex case:
        # the local cortex may hold stale aliases whose keys are absent from
        # nucleus, which would silently route the link to the wrong DB.
        _src_nucleus_key = nucleus.core.get_key_by_alias(src) if nucleus else None
        if _src_nucleus_key:
            src_key = _src_nucleus_key
        _dst_nucleus_key = nucleus.core.get_key_by_alias(dst) if nucleus else None
        if _dst_nucleus_key:
            dst_key = _dst_nucleus_key
        # Proto-word fallback for unresolved alias strings (default behaviour).
        # Skipped when "=" strict prefix is set, or for raw hex key values
        # ($var.key expansions are 64-char all-hex strings).
        _is_hex = lambda v: len(v) == 64 and all(c in '0123456789abcdef' for c in v)
        if not src_strict and nucleus and \
                _src_alias_resolved is None and _src_nucleus_key is None and not _is_hex(src):
            bare_src = src.rsplit(":", 1)[-1] if ":" in src else src
            src_key = nucleus._ensure_protoword(bare_src)
        if not dst_strict and nucleus and \
                _dst_alias_resolved is None and _dst_nucleus_key is None and not _is_hex(dst):
            bare_dst = dst.rsplit(":", 1)[-1] if ":" in dst else dst
            dst_key = nucleus._ensure_protoword(bare_dst)
        if nucleus and nucleus.core.get_chunk_raw(src_key):
            nucleus.put_link(src_key, dst_key, rel, w=w, author=client_id)
        else:
            ctx.put_link(src_key, dst_key, rel, w=w, author=client_id)
    return _ok(rid, {"status": "linked", "src": src_key, "dst": dst_key, "rel": rel, "w": w})


def handle_link_list(kernel, rid, data, ctx, scopes) -> dict:
    target = data.get("id", "")
    if not target:
        return _err(rid, -32602, "link.list requires 'id'")
    resolved = ctx.resolve_alias(target) or target
    # get_magnetic_neighborhood returns List[Dict] with "direction","rel","key","w"
    # (get_adjacent_links returns List[List] which the renderer cannot use)
    links = ctx.get_magnetic_neighborhood(resolved)
    window, page = _paginate(links, data.get("limit"), data.get("cursor"),
                             default=0, max_limit=500)   # default: whole list (link.list is literal)
    return _ok(rid, {"key": resolved, "links": window, "count": len(window), "page": page})


def handle_link_reinforce(kernel, rid, data, ctx, client_id) -> dict:
    src = data.get("src", "")
    dst = data.get("dst", "")
    rel = data.get("rel", "sys:associated_with")
    delta = float(data.get("delta", 0.1))
    if not src or not dst:
        return _err(rid, -32602, "link.reinforce requires 'src' and 'dst'")
    if rel and ':' not in rel and not rel.startswith('@'):
        from lib.akasha.composite import _BARE_REL_REMAP
        rel = _BARE_REL_REMAP.get(rel, f"calc:{rel}")
    src_key = ctx.resolve_alias(src) or src
    dst_key = ctx.resolve_alias(dst) or dst
    new_w = ctx.reinforce_link(src_key, dst_key, rel, delta_w=delta, author=client_id)
    return _ok(rid, {"status": "reinforced", "src": src_key, "dst": dst_key, "rel": rel, "w": new_w})


def handle_link_rm(kernel, rid, data, session, ctx) -> dict:
    src = data.get("src", "")
    dst = data.get("dst", "")
    rel = data.get("rel", "")
    if not src or not dst or not rel:
        return _err(rid, -32602, "ln.rm requires 'src', 'dst', and 'rel'")
    history = getattr(session, 'last_written_ids', [])
    src_key = resolve_target(kernel, src, session, history) or ctx.resolve_alias(src) or src
    dst_key = resolve_target(kernel, dst, session, history) or ctx.resolve_alias(dst) or dst
    ctx.remove_link(src_key, dst_key, rel)
    return _ok(rid, {"status": "removed", "src": src_key, "dst": dst_key, "rel": rel})


def handle_meta_set(kernel, rid, data, ctx) -> dict:
    target = data.get("id", "")
    key = data.get("key", "")
    value = data.get("value")
    if not target or not key:
        return _err(rid, -32602, "meta.set requires 'id' and 'key'")
    resolved = ctx.resolve_alias(target) or target
    result = ctx.set_meta(resolved, key, value)
    return _ok(rid, result)


def handle_alias(kernel, rid, data, session, ctx, history) -> dict:
    target = data.get("id", "")
    name = data.get("name", "")
    if not target or not name:
        return _err(rid, -32602, "alias requires 'id' and 'name'")
    resolved = resolve_target(kernel, target, session, history) or ctx.resolve_alias(target) or target
    # If target lives in nucleus, register the alias there (with proto-word creation).
    # force=True: explicit management command — intentional rebind, bypasses first-wins.
    nucleus = getattr(session, 'nucleus', None)
    _in_nucleus = bool(nucleus and nucleus.core.get_chunk_raw(resolved))
    # Reject aliasing a target that names no stored atom. Without this guard an
    # unresolved `target` falls through to the raw string above and a DANGLING
    # alias is bound (key column holds a literal like "place:france" with no atom
    # body). That dangling alias then SHADOWS the real nucleus atom of the same
    # name on every later read — a silent trap (`al place:france france` before
    # place:france exists locks the user out of the shared `france` atom). A valid
    # target has a body in the local cortex, the nucleus, or a visible group space.
    #
    # ⚠️ EXEMPT explicit 64-hex content-addresses (F6). A `write`→`alias` pair (the
    # global-relations phase COMPLETION SENTINEL is exactly this) aliases the key the
    # write just returned; that key is a legitimate content-address even when the
    # cross-context get_chunk_raw here cannot see it (separate re-authenticated JCL
    # step contexts / an async commit). Rejecting it made the sentinel alias fail →
    # the sentinel never landed → the relations phase REPLAYED on every boot → RSS
    # climbed into the OOM ceiling and the daemon was killed. Only NON-hash raw
    # strings (the true dangling-alias case) are rejected.
    _is_hexkey = (len(resolved) == 64
                  and all(c in "0123456789abcdef" for c in resolved.lower()))
    if not _is_hexkey and not _in_nucleus and not ctx.core.get_chunk_raw(resolved):
        _scopes = getattr(session, "active_scopes", None) or []
        _in_group = any(
            ge.check_access(resolved) and ge.get_chunk_raw(resolved)
            for _gid, ge in kernel._member_group_engines(session, _scopes)
        )
        if not _in_group:
            return _err(rid, -32602,
                        f"cannot alias '{target}': no such atom — write or define it first")
    if _in_nucleus:
        result = nucleus.set_alias(resolved, name, force=True)
    else:
        result = ctx.set_alias(resolved, name, force=True)
    # Weave alias label words → protoword links so alias names enrich graph connectivity
    weave.post_write(kernel, session, _in_nucleus, resolved, name, f"sys.weaver:al:{name[:30]}")
    return _ok(rid, result)


def handle_alias_rm(kernel, rid, data, session, ctx) -> dict:
    alias = (data.get("name") or data.get("alias") or "").strip()
    if not alias:
        return _err(rid, -32602, "al.rm requires 'name'")
    nucleus = getattr(session, 'nucleus', None)
    if nucleus and nucleus.resolve_alias(alias):
        nucleus.core.delete_alias(alias)
    else:
        ctx.delete_alias(alias)
    return _ok(rid, {"status": "removed", "alias": alias})


def handle_alias_list(kernel, rid, ctx):
    return _ok(rid, {"aliases": ctx.get_all_aliases()})


def handle_alias_find(kernel, rid, data, session, ctx, scopes):
    pattern = data.get("pattern") or data.get("name", "%")
    aliases = ctx.get_aliases_by_pattern(pattern)
    # Group-space aliases: a member also sees aliases of atoms shared into
    # their groups (scope-gated); other members' private aliases are not in
    # the group space, so they never surface here.
    _seen_a = {(a.get("key"), a.get("alias")) for a in aliases}
    for _gid, _ge in kernel._member_group_engines(session, scopes):
        for a in (_ge.core.get_aliases_by_pattern(pattern) or []):
            _ka = (a.get("key"), a.get("alias"))
            if _ka not in _seen_a:
                _seen_a.add(_ka)
                aliases.append(a)
    focus   = horizon_ops.get_display_focus(kernel, session)
    nucleus = getattr(session, 'nucleus', None)
    if focus:
        ns_prefixes = focus.get("ns_prefixes", [])
        scope_list  = focus.get("scopes", [])
        def _alias_passes(entry: dict) -> bool:
            alias_str = entry.get("alias", "")
            key       = entry.get("key", "")
            if ns_prefixes and not any(alias_str.startswith(p) for p in ns_prefixes):
                return False
            if scope_list and not horizon_ops.passes_display_focus(kernel, key, {"scopes": scope_list, "ns_prefixes": []}, ctx, nucleus):
                return False
            return True
        aliases = [a for a in aliases if _alias_passes(a)]
    return _ok(rid, {"aliases": aliases})


def handle_set_add(kernel, rid, data, session, ctx) -> dict:
    name = data.get("name", "")
    target = data.get("id", "")
    if not name or not target:
        return _err(rid, -32602, "set.add requires 'name' and 'id'")
    # 'ws:' (Harmonia workspace tracking, reclaimed by the boot orphan scan) and
    # 'wf:' (named workflow definitions) are reserved set-name prefixes.
    if name.startswith("ws:") or name.startswith("wf:"):
        return _err(rid, -32602,
                    f"Set name prefix '{name.split(':', 1)[0]}:' is reserved for internal use.")
    nucleus = getattr(session, 'nucleus', None)
    # An ontology / shared-set membership MUST live in the nucleus so EVERY session — guests
    # included — can see it. resolve_alias() is local-first, so when a spurious local
    # "Conceptual hub" proto-word shadows the real nucleus content atom for the same alias
    # (e.g. a cross-file set.add whose target is defined in another pack), the membership
    # would land in the writer's PRIVATE cortex: visible to admin (all-scope/librarian read)
    # but invisible to guests, which merge scoped-local + UNSCOPED-NUCLEUS only — the empty
    # cuisine/pairing sets. For an ONTOLOGY writer (librarian: boot pack-load, onto.reload),
    # resolve the target against the NUCLEUS first and, if it's a real nucleus atom, add
    # there. Regular users keep local-first (their set.add targets their own cell atoms, and
    # they cannot write the nucleus anyway).
    from lib.akasha.api import gate as _gate
    _is_onto_writer = _gate.gate(getattr(session, "client_id", ""),
                                 _gate.RECORD, _gate.UNIVERSAL)[0]
    key = None
    if _is_onto_writer and nucleus:
        _nk = nucleus.core.get_key_by_alias(target)
        if _nk and nucleus.core.get_chunk_raw(_nk):
            key = _nk
            nucleus.add_to_set(name, key)
    if key is None:
        key = ctx.resolve_alias(target) or target
        _in_nucleus = bool(nucleus and nucleus.core.get_chunk_raw(key))
        if _in_nucleus:
            nucleus.add_to_set(name, key)
        else:
            ctx.add_to_set(name, key)
    _in_nucleus = bool(nucleus and nucleus.core.get_chunk_raw(key))
    # Weave the Atom's own content through the unified post-write hook.
    # (Atom may have been bulk-imported without prior weaving; this is idempotent
    # if it was already weaved at write time.)
    _atom_raw = None
    try:
        if _in_nucleus and nucleus:
            _atom_raw = nucleus.core.get_chunk_raw(key)
        elif hasattr(ctx, 'get_chunk_raw'):
            _atom_raw = ctx.get_chunk_raw(key)
    except Exception:
        pass
    _atom_text = ""
    if _atom_raw:
        _atom_text = (_atom_raw.get("content", "")
                      if isinstance(_atom_raw, dict) else str(_atom_raw))
    if _atom_text:
        weave.post_write(kernel, session, _in_nucleus, key, _atom_text,
                         f"sys.weaver:s.add:{key[:20]}")
    return _ok(rid, {"status": "added", "set": name, "key": key})


def handle_set_rm(kernel, rid, data, ctx) -> dict:
    name = data.get("name", "")
    target = data.get("id", "")
    if not name or not target:
        return _err(rid, -32602, "set.rm requires 'name' and 'id'")
    key = ctx.resolve_alias(target) or target
    ctx.remove_from_set(name, key)
    return _ok(rid, {"status": "removed", "set": name, "key": key})


def handle_set_ls(kernel, rid, data, ctx, scopes, session=None) -> dict:
    name = data.get("name", "")
    if not name:
        # No-arg: list all user-defined set names
        names = ctx.list_set_names()
        return _ok(rid, {"sets": names, "count": len(names)})
    members = ctx.list_set(name, allowed_scopes=scopes)
    # Fallback: if no members found and name lacks "set:" prefix, retry with it.
    if not members and not name.startswith("set:"):
        members = ctx.list_set(f"set:{name}", allowed_scopes=scopes)
        if members:
            name = f"set:{name}"
    # Group-space fallback: a set shared into the caller's group lives in the
    # group engine, not the local cortex. Merge its members (scope-gated),
    # deduped by key, so a member can list a shared set.
    group_engines = kernel._member_group_engines(session, scopes) if session else []
    if group_engines:
        _seen = {m["key"] for m in members}
        for _gid, _ge in group_engines:
            for gm in _ge.list_set(name):
                if gm["key"] not in _seen:
                    _seen.add(gm["key"])
                    members.append(gm)
    if session:
        nucleus = getattr(session, 'nucleus', None)
        focus   = horizon_ops.get_display_focus(kernel, session)
        if focus:
            members = [m for m in members
                       if horizon_ops.passes_display_focus(kernel, m["key"], focus, ctx, nucleus)]
    # B4 §A5 — as-of: the membership AS IT STOOD at an epoch. A horizon/accelerator Set has no durable
    # history to read (it IS the horizon), so as_of is refused there. Otherwise keep the members whose
    # FIRST recorded at_seq is ≤ as_of (an append-only Set's membership at that epoch); a member with
    # no epoch cannot be proven newer and is kept (honest). O(K) point-gets, budget-bounded.
    _asof = asof_param(data)
    _asof_partial = False
    _asof_history_from = None
    if _asof is not None:
        if is_horizon_name(kernel, name):
            return _err(rid, -32602, "as_of is not defined for a horizon read")
        _nuc = getattr(session, "nucleus", None)
        _kept, _walked = [], 0
        for m in members:
            _walked += 1
            if _walked > kernel._ASOF_MAX_WALK:
                _asof_partial = True
                break
            _ep = atom_epoch(atom_meta_resolved(ctx, _nuc, m["key"]))
            if _ep is not None:
                _asof_history_from = _ep if _asof_history_from is None else min(_asof_history_from, _ep)
                if _ep > _asof:
                    continue
            _kept.append(m)
        members = _kept
    # Cursor pagination: page the member list, then enrich only the window.
    window, page = _paginate(members, data.get("limit"), data.get("cursor"),
                             default=20, max_limit=200)
    for m in window:
        aliases = ctx.get_aliases_by_key(m["key"])
        if not aliases and group_engines:
            for _gid, _ge in group_engines:
                aliases = _ge.get_aliases_by_key(m["key"])
                if aliases:
                    break
        m["alias"] = aliases[0] if aliases else None
    _out = {"set": name, "members": window, "count": len(window), "page": page}
    if not members:
        from lib.akasha.ontology.loader import loading_note as _loading_note
        _note = _loading_note(kernel)
        if _note:
            _out["note"] = _note
    if _asof is not None:
        _out["as_of"] = _asof
        _out["history_from"] = _asof_history_from
        if _asof_partial:
            _out["partial"] = True
            _out["reason"] = "budget"
    return _ok(rid, _out)


def handle_set_clear(kernel, rid, data, ctx) -> dict:
    name = data.get("name", "")
    if not name:
        return _err(rid, -32602, "set.clear requires 'name'")
    result = ctx.clear_set(name)
    return _ok(rid, result)


def handle_set_op(kernel, rid, data, ctx) -> dict:
    op = data.get("op", "")
    res = data.get("result", "")
    a = data.get("a", "")
    b = data.get("b", "")
    if not all([op, res, a, b]):
        return _err(rid, -32602, "set.op requires 'op', 'result', 'a', 'b'")
    if op not in ("union", "isect", "diff"):
        return _err(rid, -32602, "set.op 'op' must be union|isect|diff")
    members = ctx.set_operation(op, res, a, b)
    return _ok(rid, {"result_set": res, "members": members})


def _excluded_from_learning(raw_meta, aliases=None) -> bool:
    """The learning/gap exclusion predicate: non-curated external content OR raw Source Data.
    Neither may teach the semantic model or count as a curation gap. `aliases` (optional) lets the
    caller catch raw rows that carry no meta.concept (the .ak-loaded corpus model) by their
    `source:item:` namespace."""
    if _is_external(raw_meta) or _is_raw_source(raw_meta):
        return True
    return any(str(a).startswith("source:item:") for a in (aliases or []))


def _readable(ctx, key: str) -> str:
    """A human-facing label for an atom key: its namespaced alias (`geo:athens`) if any,
    else a bareword alias, else a short key prefix. Result rows (sim/search/emotion.find)
    carry this as `name` so the shell shows names, not raw hashes."""
    try:
        aliases = ctx.get_aliases_by_key(key) or []
    except Exception:
        aliases = []
    named = [a for a in aliases if ":" in a]
    if named:
        return named[0]
    if aliases:
        return aliases[0]
    return str(key)[:12]


def handle_ref_set(kernel, rid: str, data: dict, session) -> dict:
    """Set a typed context slot: ref.set dim=who target=<atom>."""
    from lib.akasha.ref_primitives import REF_SLOT_DIMENSIONS
    dim    = data.get("dim", "").strip()
    target = data.get("target", "").strip()
    if not dim or not target:
        return _err(rid, -32602, "ref.set requires 'dim' and 'target'")
    if dim not in REF_SLOT_DIMENSIONS:
        return _err(rid, -32602,
                    f"Unknown ref dimension '{dim}'. "
                    f"Valid: {', '.join(sorted(REF_SLOT_DIMENSIONS))}")
    resolved = resolve_target(kernel, target, session, []) or target
    session.set_ref_slot(dim, resolved)
    return _ok(rid, {"dim": dim, "key": resolved, "var": f"${dim}"})


def handle_ref_get(kernel, rid: str, data: dict, session) -> dict:
    """Get all (or one) typed context slot values."""
    from lib.akasha.ref_primitives import REF_SLOT_DIMENSIONS
    dim = data.get("dim", "").strip()
    if dim:
        if dim not in REF_SLOT_DIMENSIONS:
            return _err(rid, -32602, f"Unknown ref dimension '{dim}'")
        key = session.get_ref_slot(dim)
        return _ok(rid, {"dim": dim, "key": key, "var": f"${dim}"})
    slots = {
        d: session.get_ref_slot(d)
        for d in sorted(REF_SLOT_DIMENSIONS)
    }
    return _ok(rid, {"slots": slots})
