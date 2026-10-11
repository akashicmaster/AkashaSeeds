"""
Source Data Layer Concept Model — source.*

The Akasha-wide substrate that preserves externally acquired or directly observed data
**before** any analytical interpretation. Concept Labo is one consumer of the layer, not its
owner (spec §12). It answers a single non-negotiable question a laboratory must never fake:
*what material existed at the start of an experiment, when it was acquired, and why an item
entered the research model* — the sampling frame, made visible.

Design (Akasha Source Data Layer Spec v0.3):
- **Raw evidence is not an interpretation.** A Source Atom carries source-supplied metadata and
  acquisition metadata, never an inferred subject label, classification, hypothesis membership,
  or conclusion. Interpretation lives in SEPARATE atoms and is attached only by a Bridge.
- **The sampling frame must be visible.** Every interpreted sample is traceable to the Source
  Pool it was eligible to be selected from, including pool version and acquisition rule.
- **Acquisition precedes experiment-specific selection.** A lab must not silently fetch new
  records merely because its model now finds them interesting.
- **Pools are immutable after freeze.** A correction/addition produces a NEW pool version
  (`derived_from` v1); it never rewrites the historical pool an earlier experiment used.
- **Bridges are additive.** Selecting/observing/interpreting/rejecting a source item creates a
  relation + a bridge event; it never mutates the Source Atom into an interpreted object.
- **Failure is evidence.** Missing files, failed joins, unavailable URLs, malformed metadata
  stay explicit states (UNRESOLVED / MISSING / WITHDRAWN), never silently dropped from counts.
- **External location is not identity.** A Source Atom has a stable internal id; its locators
  (URLs, IIIF endpoints, repo paths) may change independently.
- **Akasha Time.** Acquisition/freeze and every bridge stamp a monotonic Akasha-Time marker, so
  a later model version can be proven to have run against an EARLIER frozen pool.

CLI first (spec §15): the Source Viewer GUI (docs/for-llm/source-viewer-gui-spec.md) calls these
same operators; neither interface owns a separate copy of the data. Canonical names are
`source_*` (§12.7); the older `raw`/`evidence` wording remains only as status adjectives.
"""
import hashlib
import json
import logging
import re
import time
from typing import Any, Dict, List, Optional

from lib.akasha.concepts.base import BaseConcept

logger = logging.getLogger("Harmonia.Concept.Source")

UNIVERSAL = "scope:sys:universal"          # source material is human-inspectable before any model runs

# ── Relations (all defined in the core lexicon: gen_lexicon CORE_RELS, `source:` namespace) ──
R_SUPPLIED_BY   = "source:supplied_by"     # source item → external source
R_ACQUIRED_BY   = "source:acquired_by"     # source item → acquisition event
R_IN_POOL       = "source:in_pool"         # source item → pool  (mirrors set membership)
R_POOL_OF       = "source:pool_of"         # pool → external source it draws from
R_DERIVED_FROM  = "source:derived_from"    # pool v2 → v1 ; snapshot → stream
R_SAMPLES_FROM  = "source:samples_from"    # lab/experiment → pool (the visible sampling frame)
R_OBSERVES_FROM = "source:observes_from"   # lab → stream
R_SNAPSHOT_OF   = "source:snapshot_of"     # snapshot → stream
R_IN_STREAM     = "source:in_stream"       # observation → stream
R_AUTHORED_SCOPE = "source:authored_scope" # lab → its explicit authored set (AUTHORED class)
R_GENERATED_BY  = "source:generated_by"    # bridge/acquisition → model/process that produced it
# Interpretation bridge (direction: interpreted atom → source item)
R_SELECTED_FROM = "source:selected_from"
R_OBSERVED_FROM = "source:observed_from"
R_INTERPRETS    = "source:interprets"
R_REJECTS       = "source:rejects"
R_BASED_ON      = "source:based_on"        # an interpreted claim/observation is based on a source item (§8)
BRIDGE_RELS = {"selected_from": R_SELECTED_FROM, "observed_from": R_OBSERVED_FROM,
               "interprets": R_INTERPRETS, "rejects": R_REJECTS, "based_on": R_BASED_ON}
# Bridge-event endpoints (the operation that caused a relationship to exist)
R_BRIDGE_INTERP = "source:bridge_interp"   # bridge event → the interpreted atom
R_BRIDGE_SRC    = "source:bridge_src"      # bridge event → the source item

# ── Status vocabularies (kept as explicit states — failure is evidence) ──
ITEM_STATUS   = ("ACQUIRED", "METADATA_ONLY", "UNRESOLVED", "MISSING", "WITHDRAWN")

# ENGINE-OWNED FIELDS (purge order §1.4). This engine alone writes an item's `status` — an item being
# any MEMBER of a pool's member Set, whatever its concept (the §6 ruling) — and a pool's `by_status`
# tally. The store refuses any other writer, naming the field and this engine; the engine's own writes
# (`_mk`, `_set_meta`) run inside `writing_as("source")`. The public door is `source.item.status`.
from lib.akasha import owned_fields as _owned
_owned.declare("source", "status", member_of=("source:pool:", ":members"))
_owned.declare("source", "by_status", concept="source_pool")
POOL_STATUS   = ("OPEN", "FROZEN")
STREAM_STATUS = ("ACTIVE", "CLOSED")
EVIDENCE_STATUS = ("GROUNDED", "PARTIAL", "UNGROUNDED")
ACQ_CLASSES   = ("AUTHORED", "CORPUS", "OBSERVATIONAL")

# Fields that count as a display/download LOCATOR when present on a source record.
_LOCATOR_FIELDS = ("url", "uri", "iiif", "image", "image_url", "media_url", "download_url",
                   "locator", "endpoint", "src")
# media-type detection for the Source Viewer's per-pool modality switcher (§4 of the hub spec)
_IMG_EXT = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".tif", ".tiff", ".bmp")
_AUD_EXT = (".wav", ".mp3", ".flac", ".ogg", ".oga", ".m4a", ".aac", ".opus", ".aiff")


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(s or "").lower()).strip("_")


def _record_hash(rec: Dict[str, Any]) -> str:
    """A stable content hash of a source record's fields, so a re-acquire can tell an identical record
    (reused) from a changed one (divergent) — B2's mode-1 verify."""
    return hashlib.sha256(json.dumps(rec or {}, sort_keys=True, ensure_ascii=False,
                                     default=str).encode("utf-8")).hexdigest()


class SourceDataLayer(BaseConcept):
    """The shared Source Data Layer: acquire → pool/stream → freeze/snapshot → bridge → trace.

    A drop-in concept model (auto-discovered): every op is CLI-invokable (`source.*`) and the
    Source Viewer GUI calls the same operators. Source atoms are written at universal scope so a
    user (authenticated OR guest) can browse and verify the frozen material before any research
    model runs. Interpretation is never written here — it is BRIDGED from a separate atom.
    """

    CONCEPT_PREFIX = "source"
    CONCEPT_LABEL = "Source Data Layer — acquire/freeze/bridge external evidence (spec v0.3)"

    CONCEPT_METHODS: Dict[str, Any] = {
        # ── External source registry ──
        "register":       {"op": "op_register", "action": "record",
                           "desc": "Register an external source (provider/collection/uri/rights)."},
        "inspect":        {"op": "op_inspect", "action": "read",
                           "desc": "Inspect one external source: its metadata, acquisitions, and pools."},
        "sources":        {"op": "op_sources", "action": "read",
                           "desc": "List every registered external source."},
        # ── Acquisition (job-capable) + source atoms ──
        "acquire":        {"op": "op_acquire", "action": "record",
                           "desc": "Run a recorded acquisition: create an event + Source Atoms from records/path/text."},
        "reload":         {"op": "op_reload", "action": "record",
                           "desc": "Mode-1 REPLACEMENT: reset a source's items/acquisitions/pools, then re-acquire corrected records (the new file IS the original; ids stable, traces survive). Corpus originals are replaceable, not item-versioned."},
        "import.set":     {"op": "op_import_set", "action": "record",
                           "desc": "Import an existing in-graph SET (ontology collection) into a frozen Source Pool — one Source Atom per member (meta→source_metadata, content→text). Lets existing ontology become browsable+analysable in the Source Viewer."},
        "item.status":    {"op": "op_item_status", "action": "record", "target": "pool",
                           "target_required": True,
                           "desc": "Set a pool member's status (ACQUIRED|METADATA_ONLY|UNRESOLVED|MISSING|WITHDRAWN) through the source engine — the one writer of the item's status, its status Set and every tally: source.item.status pool= item= status= (gated `record` on the pool)."},
        "resolve":        {"op": "op_resolve", "action": "record",
                           "desc": "Resolve/refresh a source item's display locator WITHOUT changing its identity."},
        "read":           {"op": "op_read", "action": "read",
                           "desc": "Read one Source Atom (source + acquisition metadata + locators + status) — no interpretation."},
        "display":        {"op": "op_display", "action": "read",
                           "desc": "The externally-hosted media locator(s) + status for a source item (browser resolves)."},
        "search":         {"op": "op_search", "action": "read",
                           "desc": "Search source-supplied metadata and stable identifiers (before any interpretation)."},
        "status":         {"op": "op_status", "action": "read",
                           "desc": "Counts by status incl. unresolved/failed — for an item, pool, or source."},
        "modalities":     {"op": "op_modalities", "action": "read",
                           "desc": "Which analysis modalities a pool supports (text always; image/audio iff members carry that media) — drives the Source Viewer's per-pool tab switcher."},
        # ── Pools (corpus sampling frames) ──
        "pool.create":    {"op": "op_pool_create", "action": "record",
                           "desc": "Create a Source Pool (a bounded sampling frame) with a declared membership rule."},
        "pool.add":       {"op": "op_pool_add", "action": "record",
                           "desc": "Add source item(s) to an OPEN pool (rejected once frozen)."},
        "pool.freeze":    {"op": "op_pool_freeze", "action": "record",
                           "desc": "Freeze a pool: membership becomes immutable, stamped with an Akasha-Time marker."},
        "pool.diff":      {"op": "op_pool_diff", "action": "read",
                           "desc": "Compare two pool versions' membership + acquisition failures before using a newer one."},
        "pool.ls":        {"op": "op_pool_ls", "action": "read",
                           "desc": "Enumerate the COMPLETE pool (every eligible member, not merely selected results)."},
        "pool.scan":      {"op": "op_pool_scan", "action": "read",
                           "desc": "Project source_metadata fields across a pool (raw, bounded) for charting/scatter; no fields = list field names."},
        "pool.sample":    {"op": "op_pool_sample", "action": "record",
                           "desc": "Create a FROZEN deterministic experiment subset of a frozen pool (keeps the full population visible)."},
        "pools":          {"op": "op_pools", "action": "read",
                           "desc": "List every Source Pool with version, count, and freeze state."},
        "samples":        {"op": "op_samples", "action": "read",
                           "desc": "List every Source Sample (experiment subset) with its pool, selection rule, and size."},
        # ── Streams + snapshots (observational sources) ──
        "stream.create":  {"op": "op_stream_create", "action": "record",
                           "desc": "Register a Source Stream (append-oriented observations) with a versioned polling rule. [space=]"},
        "stream":         {"op": "op_stream", "action": "read",
                           "desc": "Read a Source Stream's observations in Akasha-Time order (Source Viewer): source.stream <id> [as_of=<τ>] [space=]"},
        "stream.append":  {"op": "op_stream_append", "action": "record",
                           "desc": "Append observation(s) to a stream (each independently addressable, ordered by Akasha Time)."},
        "snapshot.create":{"op": "op_snapshot_create", "action": "record",
                           "desc": "Freeze a reproducible time-bounded window of a stream as a Source Snapshot."},
        # ── Interpretation bridge ──
        "bridge":         {"op": "op_bridge", "action": "record",
                           "desc": "Bridge an interpreted atom to the source item it used (selected_from/observed_from/interprets/rejects)."},
        "trace":          {"op": "op_trace", "action": "read",
                           "desc": "Trace an item BOTH ways: from a source item → every interpretation; from an interpreted atom → its sources."},
        # ── Laboratory evidence declaration + audit ──
        "lab.declare":    {"op": "op_lab_declare", "action": "record",
                           "desc": "Declare a laboratory's evidence profile (AUTHORED|CORPUS|OBSERVATIONAL + its source structures)."},
        "lab.profile":    {"op": "op_lab_profile", "action": "read",
                           "desc": "Read a laboratory's evidence profile + resolved evidence status."},
        "labs":           {"op": "op_labs", "action": "read",
                           "desc": "List every laboratory that declared a source evidence profile (with live status/class/pool)."},
        "audit":          {"op": "op_audit", "action": "read",
                           "desc": "Audit a laboratory for a real, traceable sampling frame (missing pool/source/bridge provenance)."},
    }

    # ── low-level helpers ──────────────────────────────────────────────────────
    def _author(self) -> str:
        return getattr(self.session, "client_id", "system") or "system"

    @property
    def _nuc(self):
        """The shared NUCLEUS engine, if this cell has one. Source atoms are UNIVERSAL and must be
        physically placed in the nucleus (like memory.write scope=universal) so a GUEST session —
        the real Source Viewer — can read them. Without it a librarian-session write would land in
        that session's private cortex, invisible to guests. None = a single-store local/edge cell
        (the local cortex IS the shared store there)."""
        return getattr(self.cortex, "_nucleus", None)

    # ── G1.2 — space selector: nucleus (today) OR a group engine (a closed bench, member-only) ──
    def _group_engine(self, gid: str):
        """The group engine for gid, gated by membership scope (`scope:group_<gid>`). A closed bench's
        source atoms live here, private to members — the same store society.py writes the feed to."""
        ge = getattr(self.session, "group_engines", {}).get(gid)
        if ge is None or f"scope:group_{gid}" not in (self.allowed_scopes or []):
            raise RuntimeError(f"Not a member of group '{gid}'.")
        return ge

    def _space_store(self):
        """The ENGINE that the active space (`self._space`) writes to: a group engine for
        `space=group:<gid>` (member-only), else the shared nucleus (today's universal path). None ⇒ a
        single-store edge cell (the local cortex IS the store). Empty space keeps the exact old path."""
        sp = getattr(self, "_space", "") or ""
        if sp.startswith("group:"):
            return self._group_engine(sp.split(":", 1)[1])
        return self._nuc

    def _read_core(self):
        """The core to read a SPACE's atoms/sets from — the group engine's core when a group space is
        active (self.cortex does NOT union a group engine), else None ⇒ read via self.cortex (which
        already unions local+nucleus)."""
        sp = getattr(self, "_space", "") or ""
        if sp.startswith("group:"):
            try:
                return self._group_engine(sp.split(":", 1)[1]).core
            except Exception:
                return None
        return None

    def _key(self, ident: Optional[str]) -> Optional[str]:
        """Resolve an id (alias OR raw key) to a stored key, or None if it does not exist. Checks the
        active group space (when one is set), then the local cortex and the nucleus."""
        if not ident:
            return None
        rc = self._read_core()               # the group-space core, when a space is active
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
            return ident                         # a nucleus key
        k = core.get_key_by_alias(ident)
        if k:
            return k
        if nuc:
            k = nuc.core.get_key_by_alias(ident)
            if k:
                return k
        return None

    def _alias(self, key: Optional[str]) -> Optional[str]:
        """The human-readable alias of a key (display precedence), or the key if none."""
        if not key:
            return key
        rc = self._read_core()               # a group-space atom's alias lives in the group core
        if rc is not None:
            al = rc.get_aliases_by_key(key)
            if al:
                return al[0]
        core = self.cortex.core
        al = core.get_aliases_by_key(key)
        if not al:
            nuc = getattr(self.cortex, "_nucleus", None)
            if nuc:
                al = nuc.core.get_aliases_by_key(key)
        return al[0] if al else key

    def _mk(self, alias: str, content: str, meta: Dict[str, Any]) -> str:
        """Write a UNIVERSAL atom to the shared nucleus (guest-readable) and alias it (stable id).
        Idempotent by alias: if the alias already resolves, its atom is returned unchanged
        (content-addressed re-writes unify). Falls back to the local cortex on a single-store cell."""
        with _owned.writing_as("source"):
            return self._mk_as_engine(alias, content, meta)

    def _mk_as_engine(self, alias: str, content: str, meta: Dict[str, Any]) -> str:
        existing = self._key(alias)
        if existing:
            return existing
        meta = dict(meta or {})
        nuc = self._space_store()             # nucleus, OR a group engine for space=group:<gid>
        if nuc is not None:
            key = nuc.put_atom(content, meta, author=self._author())   # → the space's store
            nuc.core.put_alias(key, alias)                             # raw alias (no proto-word churn)
            return key
        key = self.cortex.put_chunk(content=content, meta=meta, author=self._author(),
                                    scopes=[UNIVERSAL])
        self.cortex.core.put_alias(key, alias)
        return key

    def _link(self, src_id: str, dst_id: str, rel: str) -> bool:
        """Link two atoms by KEY (resolving aliases), so traversal + display stay canonical. Written
        to the nucleus (where the source atoms live). A dst that is not yet a stored atom (an
        external interpreted id) is linked as given."""
        sk = self._key(src_id)
        if not sk:
            return False
        dk = self._key(dst_id) or dst_id
        nuc = self._space_store()
        if nuc is not None:
            nuc.put_link(sk, dk, rel, author=self._author())
        else:
            self.cortex.put_link(sk, dk, rel, author=self._author())
        return True

    def _add_to_set(self, name: str, key: str) -> None:
        """Add a key to a named set in the active space's store — the SHARED nucleus (so guest reads
        see the pool/status membership), or a group engine for space=group:<gid> (member-only)."""
        nuc = self._space_store()
        if nuc is not None:
            nuc.add_to_set(name, key)
        else:
            self.cortex.add_to_set(name, key)

    def _rm_from_set(self, name: str, key: str) -> None:
        """The mirror of `_add_to_set`: remove from the SAME store the membership was added to.
        (`_set_item_status` removed from `self.cortex.core`, a different store from the one
        `_add_to_set` writes, and swallowed the failure — so an item that changed status stayed a
        member of its old `source:status:<s>` Set too. Found by `source_item_status_eval`.)"""
        nuc = self._space_store()
        try:
            if nuc is not None:
                nuc.core.remove_from_collection(name, key)
            else:
                self.cortex.remove_from_collection(name, key)
        except Exception as exc:
            logger.warning("[source] set removal failed set=%s key=%s detail=%s", name, key, exc)

    def _set_meta(self, key: str, meta_key: str, value: Any) -> Optional[Dict[str, Any]]:
        """Update one meta field on a source atom, in whichever store physically holds it (the
        nucleus for universal source atoms, or the group engine for a closed bench). Returns the meta
        as written."""
        with _owned.writing_as("source"):
            return self._set_meta_as_engine(key, meta_key, value)

    def _set_meta_as_engine(self, key: str, meta_key: str, value: Any) -> Optional[Dict[str, Any]]:
        """One atomic merge (`merge_meta`) in the store that holds the row. `value` may be a callable
        given the current meta and returning the field's new value — a counter or a tally moved
        against the record as it is at the write, never against a copy read earlier."""
        upd = (lambda m: {meta_key: value(m)}) if callable(value) else {meta_key: value}
        nuc = self._space_store()
        if nuc is not None:
            out = nuc.core.merge_meta(key, upd)
            if out is not None:
                return out
        return self.cortex.core.merge_meta(key, upd)

    def _store_meta(self, key: str) -> Dict[str, Any]:
        """An atom's meta read from the SAME store `_set_meta` writes it to (the space's store when it
        holds the row, else the local cortex). The status / tally paths read through this: reading
        `self.cortex.get_meta` (local-first) while writing nucleus-first lets a key held in BOTH stores
        read a stale value, and a stale `was` moves the wrong bucket (found by `owned_fields_eval` once
        the tally adoption that masked it was deleted)."""
        nuc = self._space_store()
        if nuc is not None:
            row = nuc.core.get_chunk_raw(key)
            if row is not None:
                return json.loads(row["meta"]) if row.get("meta") else {}
        return self.cortex.get_meta(key) or {}

    def _meta(self, ident: str) -> Dict[str, Any]:
        k = self._key(ident)
        if not k:
            return {}
        rc = self._read_core()               # a group-space atom's meta lives in the group core only
        if rc is not None:
            try:
                row = rc.get_chunk_raw(k)
                if row is not None:
                    return (json.loads(row["meta"]) if row.get("meta") else {}) or {}
            except Exception:
                pass
        return (self.cortex.get_meta(k) or {})

    def _get_meta(self, k: str) -> Dict[str, Any]:
        """Meta of a raw KEY across the active group space + the shared stores (a group-space obs
        atom's meta is not visible via self.cortex.get_meta)."""
        rc = self._read_core()
        cores = ([rc] if rc is not None else []) + [self.cortex.core,
                                                    (self._nuc.core if self._nuc else None)]
        for core in cores:
            if not core:
                continue
            try:
                row = core.get_chunk_raw(k)
                if row is not None:
                    return (json.loads(row["meta"]) if row.get("meta") else {}) or {}
            except Exception:
                pass
        return {}

    def _create_set(self, name: str) -> None:
        """Create a set in the active space's store (best-effort; membership also auto-creates it)."""
        st = self._space_store()
        try:
            if st is not None and hasattr(st, "create_set"):
                st.create_set(name)
            elif st is not None and hasattr(st, "core") and hasattr(st.core, "create_collection"):
                st.core.create_collection(name)
            else:
                self.cortex.create_set(name)
        except Exception:
            pass

    def _content(self, ident_or_key: str) -> str:
        """Content of an atom in the active space (group core when set) or the shared stores."""
        k = self._key(ident_or_key) or ident_or_key
        rc = self._read_core()
        if rc is not None:
            try:
                row = rc.get_chunk_raw(k)
                if row is not None:
                    return row.get("content") or ""
            except Exception:
                pass
        v = self.cortex.get_chunk(k)
        if isinstance(v, dict):
            return v.get("content", "")
        return v or ""

    def _members(self, set_name: str) -> List[str]:
        rc = self._read_core()               # a group space's sets are not unioned by self.cortex
        if rc is not None:
            try:
                return list(rc.get_collection_members(set_name) or [])
            except Exception:
                return []
        try:
            return list(self.cortex.get_collection_members(set_name) or [])
        except Exception:
            return []

    def _collections_for_key(self, key: str) -> set:
        """The UNION of the collections a key belongs to across BOTH stores. Set membership for source
        atoms is written to the nucleus (`_add_to_set`), so the reverse probe must union local+nucleus —
        `self.cortex.core.get_collections_for_key` alone would miss a nucleus-stored membership (this is
        the inverse of get_collection_members, which already unions)."""
        out: set = set()
        rc = self._read_core()
        for core in (self.cortex.core, (self._nuc.core if self._nuc else None), rc):
            if not core:
                continue
            try:
                out.update(core.get_collections_for_key(key) or [])
            except Exception:
                pass
        return out

    def _at_now(self) -> Dict[str, Any]:
        """A monotonic Akasha-Time marker for a source-layer event. Logical (a discrete counter
        on the `source:clock` anchor) + wall time, so 'the pool was frozen BEFORE this bridge'
        is provable by comparing markers. Serial writes make the counter effectively race-free.
        G1.2 — the counter is ALWAYS the nucleus `source:clock` (a counter is not content), even when
        the active op writes its content to a group space; the at_seq numbers observations across the
        whole cell, so a bench stream's numbering is globally comparable."""
        saved = getattr(self, "_space", "")
        self._space = ""                     # pin the clock to the nucleus regardless of the op's space
        try:
            clk = self._key("source:clock")
            if not clk:
                clk = self._mk("source:clock",
                               "[source:clock] Source Data Layer Akasha-Time counter (monotonic).",
                               {"concept": "source_clock", "at_seq": 0})
            out = self._set_meta(clk, "at_seq", lambda m: int(m.get("at_seq", 0) or 0) + 1) or {}
            seq = int(out.get("at_seq", 0))
        finally:
            self._space = saved
        return {"at_seq": seq, "at_wall": round(time.time(), 3)}

    # ── pay-at-write status tally (A3): one tally atom per source, updated by the SAME writes that
    #    change an item's status, so op_status(source=)/(all) is O(1)/O(#sources) — never a member sweep.
    @staticmethod
    def _src_slug(src_alias: str) -> str:
        return _slug(str(src_alias or "").replace("source:src:", ""))

    def _tally_bump(self, src_slug: str, status: Optional[str], delta: int) -> None:
        """Move one count in a source's status tally. Created lazily; single-writer serial → no lock."""
        if not status:
            return
        tid = f"source:tally:{src_slug}"
        tk = self._key(tid)
        if not tk:
            tk = self._mk(tid, f"[{tid}] Per-source status tally (pay-at-write).",
                          {"concept": "source_tally", "source_slug": src_slug, "total": 0,
                           "by_status": {s: 0 for s in ITEM_STATUS}})
        self._set_meta(tk, "by_status", lambda m: self._moved(m, status, delta))
        self._set_meta(tk, "total", lambda m: max(0, int(m.get("total", 0) or 0) + delta))

    @staticmethod
    def _moved(meta: Dict[str, Any], status: str, delta: int) -> Dict[str, int]:
        """`by_status` with one bucket moved by `delta` — computed from the record AT the write."""
        bs = dict(meta.get("by_status") or {s: 0 for s in ITEM_STATUS})
        bs[status] = max(0, int(bs.get(status, 0)) + delta)
        return bs

    def _set_item_status(self, key: str, new_status: str) -> None:
        """The ONE door for a source item's status change: update the item meta, MOVE its
        source:status:<old>→<new> set membership, and MOVE its tally bucket — so no write path can
        drift the counters or the status sets (the idiom keeps read-side tallies exact)."""
        seen: Dict[str, Any] = {}

        def _status(cur):                  # the old status is the one this write REPLACES
            seen["old"] = cur.get("status")
            return new_status
        m = self._set_meta(key, "status", _status) or {}
        old = seen.get("old")
        if old == new_status or "old" not in seen:
            return
        if old:
            self._rm_from_set(f"source:status:{old.lower()}", key)
        self._add_to_set(f"source:status:{new_status.lower()}", key)
        slug = self._src_slug(m.get("source") or "")
        if slug:
            self._tally_bump(slug, old, -1)
            self._tally_bump(slug, new_status, +1)
        # …and every POOL this item is a member of (directive 2026-10-02 §6.4): the pool's
        # by-status tally is derived state, produced by the write that changes its input — here —
        # so no command ever has to recount it (`source.pool.freeze` used to, called by a consumer).
        for pk in self._pools_of_item(key):
            self._pool_tally_bump(pk, old, -1)
            self._pool_tally_bump(pk, new_status, +1)

    # ── the POOL's by-status tally, pay-at-write (§6.4) ───────────────────────────────────────────
    # `tally: "live"` on a pool atom says its `by_status` is maintained by the writes themselves:
    # a member added (`_pool_add_one`) counts its status, a member's status change
    # (`_set_item_status`) moves one count. Every pool this engine creates is live from creation;
    # nothing adopts or recounts a tally (the purge order §2).
    def _pools_of_item(self, key: str) -> List[str]:
        out = []
        for col in self._collections_for_key(key):
            if col.startswith("source:pool:") and col.endswith(":members"):
                pk = self._key(col[:-len(":members")])
                if pk and pk not in out:
                    out.append(pk)
        return out

    def _pool_tally_bump(self, pk: str, status: Optional[str], delta: int) -> None:
        if not status:
            return
        if self._store_meta(pk).get("tally") != "live":
            return                        # not a pool this engine created
        self._set_meta(pk, "by_status", lambda m: self._moved(m, status, delta))

    def _ensure_pool_tally(self, pk: str) -> Dict[str, int]:
        """The pool's live by-status tally, as stored. It is live from `source.pool.create` (zero) and
        moved only by the writes that change it — a member added (`_pool_add_one`), a member's status
        changed (`_set_item_status`) — and the store refuses any other writer of `status` / `by_status`
        (engine-owned fields). So there is nothing to adopt and no drift to recount (the purge order
        §2): a pool without a live tally was not made by this engine, and reads zero."""
        m = self._store_meta(pk)
        bs = m.get("by_status") if m.get("tally") == "live" else None
        return {s: int((bs or {}).get(s, 0)) for s in ITEM_STATUS}

    def _member_is_private(self, key: str) -> bool:
        """True if an atom carries a NON-universal access scope (C1). No access rows, or a universal
        scope, = public. A private-scoped atom must not be silently republished as a guest-readable
        source item. Checks BOTH stores (a member may live in the local cortex OR the nucleus, like
        `_key`), so a private atom is never missed by looking in the wrong store."""
        scopes: List[str] = []
        for core in (self.cortex.core, (self._nuc.core if self._nuc else None)):
            if not core:
                continue
            try:
                s = core.get_chunk_access_scopes(key) or []
            except Exception:
                s = []
            if s:
                scopes = s
                break
        if not scopes:
            return False
        return not any("universal" in str(s) for s in scopes)

    def _bridge_index_add(self, bridge_key: str, source_item_alias: str, interpreted_id: str) -> None:
        """A4: file a bridge into its two ENDPOINT index sets at write time — keyed by ALIAS/slug (not
        store key), so a source.reload that re-mints items under the same ids leaves the index valid
        (trace continuity survives replacement). trace then reads one membrane instead of the registry."""
        if source_item_alias:
            self._add_to_set(f"source:bridges:src:{_slug(source_item_alias)}", bridge_key)
        if interpreted_id:
            self._add_to_set(f"source:bridges:interp:{_slug(str(interpreted_id))}", bridge_key)

    @staticmethod
    def _looks_like_locator(v: Any) -> bool:
        """A value is a locator only if it LOOKS like one — a URI (`scheme://…`), a media-extension
        filename, or an absolute path with an extension. So a generic metadata field legitimately named
        `src` (common in CSV exports) carrying an id/label is NOT mistaken for a download URL (B4)."""
        s = str(v or "").strip()
        if "://" in s:
            return True
        low = s.lower()
        if low.endswith(_IMG_EXT + _AUD_EXT):
            return True
        return s.startswith("/") and "." in s.rsplit("/", 1)[-1]     # /path/to/file.ext

    @staticmethod
    def _locator_of(record: Dict[str, Any]) -> Dict[str, Any]:
        """Extract a display/download locator from a source record, if a URI-like one is present."""
        for f in _LOCATOR_FIELDS:
            v = record.get(f)
            if v and SourceDataLayer._looks_like_locator(v):
                return {"kind": "external", "field": f, "uri": str(v),
                        "locator_status": "UNRESOLVED", "resolved_at": None}
        return {}

    @staticmethod
    def _parse_records(records, text, path) -> List[Dict[str, Any]]:
        """Records may arrive as a list (RPC), a JSON array / JSONL string (text=), or a file
        (path=). CLI-native single records use text=. Malformed lines are kept as failures."""
        out: List[Dict[str, Any]] = []
        if isinstance(records, list):
            out.extend(r for r in records if isinstance(r, dict))
            return out
        raw = ""
        if text:
            raw = str(text)
        elif path:
            with open(path, "r", encoding="utf-8") as fh:
                raw = fh.read()
        raw = raw.strip()
        if not raw:
            return out
        # JSON array first, else JSONL (one object per line; a bad line is recorded as malformed).
        try:
            val = json.loads(raw)
            if isinstance(val, list):
                return [r for r in val if isinstance(r, dict)]
            if isinstance(val, dict):
                return [val]
        except json.JSONDecodeError:
            pass
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                out.append(obj if isinstance(obj, dict) else {"__malformed__": line})
            except json.JSONDecodeError:
                out.append({"__malformed__": line})
        return out

    # ── 1. External source registry ────────────────────────────────────────────
    def op_register(self, provider: str, collection: str = "", uri: str = "",
                    rights: str = "", name: str = "", id: str = "", doi: str = "",
                    version: str = "", retrieval_uri: str = "", mirror: str = "",
                    space: str = "") -> Dict[str, Any]:
        """Register the authoritative or supplying collection an acquisition draws from. Records
        provider / collection / source URI / licence / DOI / version — never a research
        interpretation. **Logical source identity (`uri`/`doi`) is kept DISTINCT from the retrieval
        location (`retrieval_uri`/`mirror`)** — locators may change without changing identity (§4).
        `space=group:<gid>` registers into that group engine (closed bench); empty = the nucleus."""
        self._space = space
        sid = id or f"source:src:{_slug(name or collection or provider)}"
        meta = {"concept": "source_external", "provider": provider, "collection": collection,
                "source_uri": uri, "doi": doi, "dataset_version": version, "rights": rights,
                "name": name or collection or provider,
                "retrieval": {"uri": retrieval_uri, "mirror": mirror} if (retrieval_uri or mirror) else {},
                "registered_at": round(time.time(), 3)}
        key = self._mk(sid, f"[{sid}] External source — {meta['name']} ({provider}).", meta)
        self._add_to_set("source:sources", key)
        return {"source": self._alias(key), "provider": provider, "collection": collection,
                "uri": uri, "doi": doi or None, "version": version or None, "rights": rights,
                "status": "registered"}

    def op_sources(self) -> Dict[str, Any]:
        """List every registered external source (provider, collection, rights)."""
        out = []
        for k in self._members("source:sources"):
            m = self.cortex.get_meta(k) or {}
            out.append({"source": self._alias(k), "provider": m.get("provider"),
                        "collection": m.get("collection"), "rights": m.get("rights"),
                        "uri": m.get("source_uri"), "doi": m.get("doi") or None,
                        "version": m.get("dataset_version") or None})
        return {"sources": out, "count": len(out)}

    def op_inspect(self, id: str) -> Dict[str, Any]:
        """Inspect one external source: its registration metadata, acquisition events, and pools.

        SET-based, NOT a link walk: every acquired item does `item → source` (R_SUPPLIED_BY), so a
        source with a 26k-row corpus has 26k incoming links — scanning them (the old `get_adjacent_
        links` loop) was O(#items) and made this view hang. Acquisitions and pools are each registered
        in a small GLOBAL set (`source:acquisitions`, `source:pools`) and carry their `source` in meta,
        so we filter those instead — O(#acquisitions + #pools), independent of item count."""
        k = self._key(id)
        if not k:
            raise ValueError(f"unknown source '{id}'")
        m = self.cortex.get_meta(k) or {}
        src_alias = self._alias(k)

        def _src_of(meta):
            s = (meta or {}).get("source")
            if not s:
                return None
            if s == src_alias:
                return src_alias
            sk = self._key(s)
            return self._alias(sk) if sk else s

        acqs = [self._alias(a) for a in self._members("source:acquisitions")
                if _src_of(self.cortex.get_meta(a)) == src_alias]
        pools = [self._alias(p) for p in self._members("source:pools")
                 if _src_of(self.cortex.get_meta(p)) == src_alias]
        return {"source": src_alias, "provider": m.get("provider"),
                "collection": m.get("collection"), "rights": m.get("rights"),
                "uri": m.get("source_uri"), "doi": m.get("doi") or None,
                "version": m.get("dataset_version") or None, "retrieval": m.get("retrieval") or {},
                "acquisitions": sorted(set(acqs)), "pools": sorted(set(pools))}

    def op_reset(self, source: str = "", pause=None) -> Dict[str, Any]:
        """INTERNAL (not a public RPC — deliberately absent from CONCEPT_METHODS): drop every item /
        acquisition / pool belonging to ONE source, FENCED to that source, so a CORRECTED corpus can
        be re-imported cleanly. A frozen pool + idempotent-by-alias atoms cannot be updated in place,
        so a pre-launch data correction (e.g. an upstream ENCODING fix) removes the stale atoms and the
        normal import re-creates corrected ones under the SAME ids. Streamed (constant memory); `pause`
        is an optional callable invoked every 1000 drops so a caller can yield to interactive work.
        Never deletes a PUBLISHED frame — that is superseded by a new version; this is boot-internal."""
        nuc = self._nuc
        if not nuc:
            raise RuntimeError("no shared nucleus — reset unavailable")
        core = nuc.core
        sk = self._key(source)
        if not sk:
            return {"source": source, "dropped": {}, "note": "unknown source — nothing to reset"}
        src_alias = self._alias(sk)
        item_prefix = "source:item:%s:" % _slug(src_alias.replace("source:src:", ""))
        counts = {"items": 0, "acquisitions": 0, "pools": 0, "sets_cleared": 0}
        n = [0]

        def _tick():
            n[0] += 1
            if pause and n[0] % 1000 == 0:
                try:
                    pause()
                except Exception:
                    pass

        def _src_of(meta):
            s = (meta or {}).get("source")
            if not s:
                return None
            return s if s == src_alias else (self._alias(self._key(s)) if self._key(s) else s)

        def _drop(key):
            for coll in list(core.get_collections_for_key(key) or []):
                try:
                    core.remove_from_collection(coll, key); counts["sets_cleared"] += 1
                except Exception:
                    pass
            for al in list(core.get_aliases_by_key(key) or []):
                try:
                    core.delete_alias(al)
                except Exception:
                    pass
            try:
                core.drop_chunk(key)
            except Exception:
                pass
            _tick()

        # 1) items — fenced by BOTH the item-alias namespace AND meta.source (belt-and-suspenders).
        for k in list(self._members("source:items")):
            al = self._alias(k) or ""
            if al.startswith(item_prefix) or _src_of(self.cortex.get_meta(k)) == src_alias:
                _drop(k); counts["items"] += 1
        # 2) acquisitions of this source (+ their :items index sets)
        for k in list(self._members("source:acquisitions")):
            if _src_of(self.cortex.get_meta(k)) == src_alias:
                try:
                    core.clear_collection("%s:items" % (self._alias(k) or "")); counts["sets_cleared"] += 1
                except Exception:
                    pass
                _drop(k); counts["acquisitions"] += 1
        # 3) pools of this source (+ their :members frame sets)
        for k in list(self._members("source:pools")):
            if _src_of(self.cortex.get_meta(k)) == src_alias:
                try:
                    core.clear_collection("%s:members" % (self._alias(k) or "")); counts["sets_cleared"] += 1
                except Exception:
                    pass
                _drop(k); counts["pools"] += 1
        # 4) the per-source tally (A3) — recreated by the re-acquire; drop it so counts don't double.
        tk = self._key("source:tally:%s" % _slug(src_alias.replace("source:src:", "")))
        if tk:
            _drop(tk); counts["tally"] = 1
        logger.info("[source.reset] %s → dropped %s", src_alias, counts)
        return {"source": src_alias, "dropped": counts}

    def op_reload(self, source: str, rule: str = "corrected reload", records: Any = None, text: str = "",
                  path: str = "", id_field: str = "id", pool: str = "", freeze: str = "yes",
                  dataset_version: str = "", artifacts: Any = None) -> Dict[str, Any]:
        """[source.reload] Mode-1 REPLACEMENT (B2): replace a source's corpus with a corrected one —
        reset THIS source's items / acquisitions / pools, then acquire the new records. The new file IS
        the original; prior values are not retained (corpus originals are replaceable, not item-versioned).
        Item ids are stable across a reload and the bridge index is alias-keyed, so interpretation traces
        survive the replacement intact. Pool VERSIONS (v2 derived_from v1) are for changes of the sampling
        FRAME — never a record-correction mechanism. Admin-gated (destructive), fenced to the named source
        exactly as the internal reset is. If `pool=` is given it is recreated + (by default) frozen."""
        src_key = self._key(source)
        if not src_key:
            raise ValueError(f"unknown source '{source}' — nothing to reload")
        reset = self.op_reset(source=source)                 # fenced drop of this source's items/acq/pools
        if pool:
            self.op_pool_create(name=pool, source=self._alias(src_key), version="v1",
                                rule=rule, dataset_version=dataset_version)
        out = self.op_acquire(source=source, rule=rule, records=records, text=text, path=path,
                              id_field=id_field, pool=pool or "", dataset_version=dataset_version,
                              artifacts=artifacts)
        do_freeze = pool and str(freeze).strip().lower() in ("", "yes", "y", "true", "1", "on")
        if do_freeze:
            self.op_pool_freeze(pool)
        out.update({"reloaded": True, "reset": reset.get("dropped"), "pool": pool or None,
                    "frozen": bool(do_freeze),
                    "note": "corpus replaced (the new file IS the original); ids stable, interpretation "
                            "traces survive (alias-keyed bridge index)."})
        return out

    # ── 2. Acquisition + source atoms ──────────────────────────────────────────
    def op_acquire(self, source: str, rule: str, records: Any = None, text: str = "",
                   path: str = "", id_field: str = "id", pool: str = "",
                   by: str = "", dataset_version: str = "", artifacts: Any = None,
                   space: str = "", label_field: str = "") -> Dict[str, Any]:
        """Run a recorded acquisition. Creates an Acquisition Event and one Source Atom per record,
        RETAINING unresolved/malformed records as explicit failures. `rule` (the inspectable,
        versioned acquisition scope) is stored on the event, along with `dataset_version` and
        `artifacts` (a list of {name, sha256, size, uri} — the hashed data + documentation files,
        the retrieval provenance §4/§12.3). Optionally drops every acquired item into an OPEN `pool`.
        Acquisition PRECEDES experiment-specific selection — this op never applies a research filter;
        it only records what was obtained (never filter by country/mode/age/attitude/completeness).
        `space=group:<gid>` acquires into that group engine (closed bench); empty = the nucleus."""
        self._space = space
        src_key = self._key(source)
        if not src_key:
            raise ValueError(f"unknown source '{source}' — source.register it first")
        src_slug = _slug(self._alias(src_key).replace("source:src:", ""))
        at = self._at_now()
        seq = len(self._members("source:acquisitions")) + 1
        acq_id = f"source:acq:{src_slug}:{seq}"
        recs = self._parse_records(records, text, path)
        arts = artifacts if isinstance(artifacts, list) else ([] if artifacts is None else [artifacts])
        acquired = unresolved = reused = divergent = 0
        item_ids: List[str] = []
        acq_meta = {"concept": "source_acquisition", "source": self._alias(src_key),
                    "rule": rule, "tool": by or self._author(), "started_at": at["at_wall"],
                    "at_seq": at["at_seq"], "record_count": len(recs),
                    "dataset_version": dataset_version, "artifacts": arts}
        acq_key = self._mk(acq_id, f"[{acq_id}] Acquisition from {self._alias(src_key)} — rule: {rule}", acq_meta)
        self._link(acq_id, source, R_SUPPLIED_BY)
        for i, rec in enumerate(recs):
            malformed = "__malformed__" in rec
            stable = None if malformed else rec.get(id_field)
            if stable in (None, ""):
                stable = "u_" + hashlib.sha256(json.dumps(rec, sort_keys=True,
                         ensure_ascii=False).encode()).hexdigest()[:12]
                status = "UNRESOLVED"
                unresolved += 1
            else:
                status = "ACQUIRED"
                acquired += 1
            item_id = f"source:item:{src_slug}:{_slug(str(stable))}"
            locator = {} if malformed else self._locator_of(rec)
            if status == "ACQUIRED" and not locator:
                status = "METADATA_ONLY"
            # B2 — mode-1 originals are REPLACEABLE, not item-versioned. `_mk` is idempotent-by-alias
            # (returns the existing atom UNCHANGED), so a re-acquire onto an existing id must be verified,
            # never silently kept: hash the incoming record against the stored one and report reused
            # (identical) vs divergent (changed). A divergent record is NEVER silently persisted or
            # ignored — it is filed into source:status:divergent and the report directs the operator to
            # `source.reload` (the declared replacement op). New ids mint + increment the pay-at-write tally.
            existing = self._key(item_id)
            if existing:
                stored_sm = (self.cortex.get_meta(existing) or {}).get("source_metadata") or {}
                same = _record_hash(stored_sm) == _record_hash({} if malformed else rec)
                if same:
                    reused += 1
                else:
                    divergent += 1
                    self._add_to_set("source:status:divergent", existing)
                self._link(item_id, acq_id, R_ACQUIRED_BY)
                self._add_to_set(f"{acq_id}:items", existing)
                if pool:
                    self._pool_add_one(pool, item_id)
                item_ids.append(item_id)
                continue
            imeta = {
                "concept": "source_item",
                "source": self._alias(src_key),
                "source_record_id": None if malformed else stable,
                "source_metadata": {} if malformed else rec,      # verbatim source-supplied fields
                "acquisition": {"event": acq_id, "acquired_at": at["at_wall"], "at_seq": at["at_seq"]},
                "locator": locator,
                "status": status,
                # Failure is evidence — the malformed line is retained, not dropped.
                "failure": (rec.get("__malformed__") if malformed else None),
            }
            # A34(a) — hoist the declared class label to a TOP-LEVEL `label` so a downstream learner
            # (learning.train) finds it without knowing the corpus's field name. The verbatim value stays in
            # source_metadata; this is an additional, non-destructive projection.
            if label_field and not malformed:
                _lv = rec.get(label_field)
                if _lv not in (None, ""):
                    imeta["label"] = str(_lv)
            self._mk(item_id, f"[{item_id}] Source item — {status} (from {self._alias(src_key)}).", imeta)
            self._link(item_id, source, R_SUPPLIED_BY)
            self._link(item_id, acq_id, R_ACQUIRED_BY)
            self._add_to_set("source:items", self._key(item_id))
            self._add_to_set(f"source:status:{status.lower()}", self._key(item_id))
            self._add_to_set(f"{acq_id}:items", self._key(item_id))
            self._tally_bump(src_slug, status, +1)            # pay-at-write per-source tally (A3)
            if pool:
                self._pool_add_one(pool, item_id)
            item_ids.append(item_id)
        # finalize the event
        self._set_meta(acq_key, "acquired_count", acquired)
        self._set_meta(acq_key, "unresolved_count", unresolved)
        self._set_meta(acq_key, "completed_at", round(time.time(), 3))
        self._add_to_set("source:acquisitions", acq_key)
        out = {"acquisition": acq_id, "source": self._alias(src_key), "rule": rule,
               "acquired": acquired, "unresolved": unresolved, "reused": reused, "divergent": divergent,
               "total": len(recs), "at_seq": at["at_seq"], "pool": pool or None, "items": item_ids[:50]}
        if divergent:
            out["note"] = ("%d record(s) DIVERGED from the stored version and were NOT overwritten "
                           "(filed under source:status:divergent) — corpus originals are replaceable via "
                           "`source.reload`, not by re-acquire." % divergent)
        return out

    def op_import_set(self, set: str, pool: str = "", provider: str = "ontology", name: str = "",
                      version: str = "v1", text_field: str = "content", freeze: str = "yes",
                      batch: str = "500", limit: str = "", allow_private: str = "") -> Dict[str, Any]:
        """[source.import.set] Import an existing in-graph SET (any `set.add`-defined ontology
        collection) into a frozen Source Pool: enumerate its members, mint ONE `source_item` per member
        (member alias → stable id, each scalar meta field → a `source_metadata` field, the atom's content
        → a `text` field), reusing the acquisition minting/filing (source:items / <pool>:members /
        source:status:*), then freeze. So the existing ontology becomes browsable + analysable through
        the SAME Source Viewer, and any lab can bind the resulting pool. Idempotent by alias (re-import
        unifies). Bounded + streamed (per-`batch`, optional `limit` cap) — a large set never materializes
        at once. Membership is by reference — the ontology atoms are NOT copied, only projected as source
        records (content-addressed, so a member that is itself a source item unifies)."""
        members = self._members(set)
        if not members:
            raise ValueError("set '%s' has no members (or does not exist)" % set)
        cap = int(limit) if str(limit).strip().isdigit() else 0
        if cap:
            members = members[:cap]
        # C1 — visibility is declared, never accidental. Republishing a private-scoped atom as a
        # guest-readable universal source item is a footgun; inspect member scopes FIRST. Any private
        # member REFUSES the import (all-or-nothing — a silently filtered corpus is a corrupted frame)
        # unless the operator passes allow_private=yes, in which case the elevation is recorded on the pool.
        _priv_ok = str(allow_private).strip().lower() in ("yes", "y", "true", "1", "on")
        priv_keys = [k for k in members if self._member_is_private(self._key(k) or k)]
        if priv_keys and not _priv_ok:
            sample = ", ".join((self._alias(self._key(k) or k) or str(k)) for k in priv_keys[:5])
            raise ValueError(
                "set '%s' has %d private-scoped member(s) (e.g. %s%s) — importing would republish them as "
                "guest-readable universal source items. Pass allow_private=yes to consent (the pool records "
                "the elevation), or import a universal-scoped set." %
                (set, len(priv_keys), sample, (" …" if len(priv_keys) > 5 else "")))
        bsz = max(1, int(batch)) if str(batch).strip().isdigit() else 500
        base = _slug(set.replace("set:", "").replace(":", "_"))
        src = self.op_register(provider=provider, collection=set, name=name or ("ontology:" + base))
        source_id = src["source"]
        pinfo = self.op_pool_create(name=(pool or ("ontology:" + base)), source=source_id, version=version,
                                    rule="ontology set %s — one source item per member atom" % set)
        pool_id = pinfo["pool"]
        if priv_keys:                                        # C1 — record the consented elevation on the pool
            pkk = self._key(pool_id)
            if pkk:
                self._set_meta(pkk, "imported_private", True)
                self._set_meta(pkk, "private_members", len(priv_keys))
                self._set_meta(pkk, "imported_by", self._author())
        tf = (text_field or "content").strip() or "content"
        _SKIP = {"concept", "semantic_vector", "embedding"}
        imported = 0
        for off in range(0, len(members), bsz):
            recs = []
            for k in members[off:off + bsz]:
                kk = self._key(k) or k                       # a set may hold an ALIAS — resolve to the key
                alias = self._alias(kk) or k                 # so meta + content actually read (not empty)
                rec = {"id": alias, "atom": alias}
                for mk, mv in (self.cortex.get_meta(kk) or {}).items():
                    if mk in _SKIP:
                        continue
                    if mv is None or isinstance(mv, (str, int, float, bool)):
                        rec[mk] = mv                         # scalar meta → a projectable source field
                try:
                    content = self.cortex.get_chunk(kk)
                except Exception:
                    content = None
                if content:
                    s = str(content)
                    rec[tf] = s[:2000]                       # the atom's description → a text field
                    if len(s) > 2000:                        # never truncate silently (B3)
                        rec["text_truncated"] = True
                        rec["text_length"] = len(s)
                recs.append(rec)
            self.op_acquire(source=source_id, rule="ontology set %s" % set,
                            records=recs, id_field="id", pool=pool_id)
            imported += len(recs)
        do_freeze = str(freeze).strip().lower() in ("", "yes", "y", "true", "1", "on")
        if do_freeze:
            self.op_pool_freeze(pool_id)
        return {"set": set, "source": source_id, "pool": pool_id,
                "imported": imported, "members": len(members), "frozen": do_freeze,
                "imported_private": bool(priv_keys), "private_members": len(priv_keys)}

    def op_modalities(self, pool: str, sample: str = "60") -> Dict[str, Any]:
        """[source.modalities] Which analysis MODALITIES a pool supports — a bounded probe of its
        members' locators/references. TEXT is always available (every source atom has metadata/content);
        IMAGE iff members carry an image reference (a vlab `image_reference`, or a locator/metadata uri
        that looks like an image); AUDIO iff an audio reference (an `audio_reference`, or an audio uri).
        This drives the Source Viewer's per-pool tab switcher (Source / Text / Image / Audio) so image/
        audio tabs appear only for pools that actually have that media. Bounded read (samples ≤ `sample`
        members, default 60) — never a full sweep."""
        cap = int(sample) if str(sample).strip().isdigit() else 60
        members = self._pool_members(pool)[:max(1, cap)]
        has_image = has_audio = False
        for k in members:
            m = self.cortex.get_meta(k) or {}
            if not has_image and ((m.get("image_reference") or {}).get("locator") or (m.get("image_reference") or {}).get("uri")):
                has_image = True
            if not has_audio and ((m.get("audio_reference") or {}).get("locator") or (m.get("audio_reference") or {}).get("uri")):
                has_audio = True
            sm = m.get("source_metadata") or {}
            # an EXPLICIT media-type field wins — a locator URL need not carry an extension (e.g. a
            # xeno-canto `/download` link is audio with no `.ogg` suffix); an importer states the kind.
            _mt = str(sm.get("media_type") or sm.get("content_type") or sm.get("file_type") or "").lower()
            if "audio" in _mt or sm.get("audio_url") or sm.get("audio"):
                has_audio = True
            if "image" in _mt:
                has_image = True
            uris = []
            loc = m.get("locator") or {}
            if loc.get("uri"):
                uris.append(str(loc["uri"]))
            for f in _LOCATOR_FIELDS + ("audio", "audio_url", "sound", "sound_url"):
                if sm.get(f):
                    uris.append(str(sm[f]))
            for u in uris:
                ul = u.lower().split("?")[0].split("#")[0]
                if not has_image and (ul.endswith(_IMG_EXT) or "iiif" in ul):
                    has_image = True
                if not has_audio and ul.endswith(_AUD_EXT):
                    has_audio = True
            if has_image and has_audio:
                break
        return {"pool": pool, "probed": len(members),
                "modalities": {"text": True, "image": has_image, "audio": has_audio}}

    def op_item_status(self, pool: str, item: str, status: str) -> Dict[str, Any]:
        """Set ONE pool member's status, through the engine's one door (directive 2026-10-03 item 5).

        The public form of `_set_item_status`: the item's meta, its `source:status:<s>` Set
        membership, its source's tally and the `by_status` tally of EVERY pool it belongs to move in
        the same write, so nothing outside the engine has to write an item's status into its meta
        (which is what drifts a pool's tally). Gated `record` ON THE POOL (the declared target).

        WHAT IS AN ITEM is decided by MEMBERSHIP, not by concept name (10-03 §6 ruling): an atom
        that is a member of `pool=` is an item of that pool, whatever its concept — the same fact
        `source.status` counts in `total`. A non-member is refused `not a member of <pool>`. The
        engine names no application concept (a vlab artwork is an item because it is a member).

        A member with no prior status that is given one moves its pool's tally +1 into that bucket
        (`changed: true`) — the path `vlab.source.add` uses — so `sum(by_status) == total` holds for
        every member that only ever got its status here. The same status twice is `changed: false`
        and moves nothing. A status cannot be written around the door: the store refuses any other
        writer of an item's `status` (engine-owned fields, the purge order §1.4)."""
        st = str(status or "").strip().upper()
        if st not in ITEM_STATUS:
            raise ValueError("status must be one of %s, not %r" % ("|".join(ITEM_STATUS), status))
        pk = self._key(pool)
        if not pk or (self.cortex.get_meta(pk) or {}).get("concept") != "source_pool":
            raise ValueError(f"unknown source pool '{pool}'")
        k = self._key(item)
        if not k or pk not in self._pools_of_item(k):
            raise ValueError(f"'{item}' is not a member of {self._alias(pk)}")
        was = self._store_meta(k).get("status")
        self._set_item_status(k, st)
        return {"pool": self._alias(pk), "item": self._alias(k), "status": st, "was": was,
                "changed": was != st}

    def op_resolve(self, id: str, locator: str = "", status: str = "") -> Dict[str, Any]:
        """Resolve/refresh a source item's display locator WITHOUT changing its stable identity
        (external location is not identity). Updates locator uri/status only; the raw id is fixed."""
        k = self._key(id)
        if not k:
            raise ValueError(f"unknown source item '{id}'")
        m = self.cortex.get_meta(k) or {}
        if m.get("concept") != "source_item":
            raise ValueError(f"'{id}' is not a source item")
        loc = dict(m.get("locator") or {})
        if locator:
            loc.update({"kind": "external", "uri": locator})
        loc["locator_status"] = (status or "RESOLVED").upper()
        loc["resolved_at"] = round(time.time(), 3)
        self._set_meta(k, "locator", loc)
        # a resolved locator lifts a METADATA_ONLY item to ACQUIRED (identity unchanged). The ONE door
        # (_set_item_status) moves the status set membership AND the pay-at-write tally in the same step.
        if m.get("status") == "METADATA_ONLY" and loc["locator_status"] == "RESOLVED":
            self._set_item_status(k, "ACQUIRED")
        return {"item": self._alias(k), "locator": loc, "status": self._meta(id).get("status")}

    def op_read(self, id: str) -> Dict[str, Any]:
        """Read ONE Source Atom exactly as acquired: source-supplied metadata + acquisition
        metadata + locators + status. It NEVER carries an experiment-derived claim as a source
        fact — interpretation is reached only via source.trace."""
        k = self._key(id)
        if not k:
            raise ValueError(f"unknown source item '{id}'")
        m = self.cortex.get_meta(k) or {}
        if m.get("concept") != "source_item":
            raise ValueError(f"'{id}' is not a source item (it is {m.get('concept')})")
        return {"item": self._alias(k), "source": m.get("source"),
                "source_record_id": m.get("source_record_id"),
                "source_metadata": m.get("source_metadata") or {},
                "acquisition": m.get("acquisition") or {},
                "locator": m.get("locator") or {}, "status": m.get("status"),
                "failure": m.get("failure"),
                "note": "Source Atom — no interpretation. Use source.trace to see what read it."}

    def op_display(self, id: str) -> Dict[str, Any]:
        """The externally-hosted media locator(s) + status for a source item, for the Source
        Viewer to embed browser-side. Binary media is NEVER stored in the atom payload; a failed
        locator returns its explicit failure state, never a hidden atom."""
        k = self._key(id)
        if not k:
            raise ValueError(f"unknown source item '{id}'")
        m = self.cortex.get_meta(k) or {}
        loc = m.get("locator") or {}
        return {"item": self._alias(k), "media_type": (m.get("source_metadata") or {}).get("media_type"),
                "locator": loc, "displayable": bool(loc.get("uri")),
                "status": m.get("status"),
                "failure_state": None if loc.get("uri") else "no locator resolved (source item shown without media)"}

    def op_search(self, q: str = "", source: str = "", status: str = "",
                  limit: int = 50, offset: Any = "0", budget: Any = "5000") -> Dict[str, Any]:
        """Search source-supplied metadata and stable identifiers BEFORE interpretation. Filters
        by `source` and `status`; `q` matches the stable id or any source metadata value.

        BUDGETED (F50 / F56-A2): a no-match query used to iterate ALL items (CPU-O(store)) on the guest
        surface. Now each call examines at most `budget` entries (default 5000, HARD-capped at 5000 —
        the same guest-surface ceiling as pool.scan) from `offset`, and returns `scanned` + `truncated`
        + a continuation `offset` so a caller pages a long scan instead of one uncapped sweep. A caller
        wanting more pages the scan with `offset`; no single call examines > 5000. (Right altitude
        later: a pre-lowered search blob paid at acquisition.)"""
        ql = (q or "").lower()
        pool = self._members(f"source:status:{status.lower()}") if status else self._members("source:items")
        try:
            off = max(0, int(offset)) if str(offset).strip() else 0
        except (TypeError, ValueError):
            off = 0
        try:
            bud = max(1, min(int(budget or 5000), 5000))     # F56-A2: hard ≤5000 examined per call
        except (TypeError, ValueError):
            bud = 5000
        lim = max(1, int(limit))
        hits = []
        scanned = 0
        for k in pool[off:off + bud]:
            scanned += 1
            m = self.cortex.get_meta(k) or {}
            m_source = m.get("source")
            if source and m_source != source and self._alias(self._key(source)) != m_source:
                continue
            if ql:
                hay = (str(m.get("source_record_id") or "") + " " +
                       json.dumps(m.get("source_metadata") or {}, ensure_ascii=False)).lower()
                if ql not in hay:
                    continue
            hits.append({"item": self._alias(k), "source": m_source,
                         "source_record_id": m.get("source_record_id") or m.get("provider_object_id"),
                         "status": m.get("status")})
            if len(hits) >= lim:
                break
        next_off = off + scanned
        # more to page if we stopped on the limit/budget before the pool ended
        truncated = next_off < len(pool)
        return {"query": q, "source": source or None, "status": status or None,
                "results": hits, "count": len(hits), "scanned": scanned, "offset": off,
                "next_offset": next_off if truncated else None, "truncated": truncated,
                "total_candidates": len(pool)}

    def op_status(self, id: str = "", pool: str = "", source: str = "", space: str = "") -> Dict[str, Any]:
        """Counts by status — including unresolved/failed — for one item, a pool, or a source.
        Failed external joins remain visible in the counts (they never disappear). `space=group:<gid>`
        reads a group pool's status; empty = the nucleus."""
        self._space = space
        if id:
            m = self._meta(id)
            return {"item": id, "status": m.get("status"), "failure": m.get("failure")}
        if pool:
            # ⚠️ NO real-time Atom sweep on the read path. A pool's by-status tally is PRECOMPUTED at
            # freeze (the immutability point, inside the import BATCH) and stored on the pool atom; here
            # we RE-FETCH it. `total` is the member-KEY list length (one indexed read, not a per-atom
            # sweep). An unfrozen pool has no final tally yet → `by_status` is pending (never swept).
            pk = self._key(pool)
            pm = (self.cortex.get_meta(pk) or {}) if pk else {}
            total = pm.get("member_count")
            if total is None:
                total = len(self._pool_members(pool))     # key-list length only — no get_meta per member
            stored = pm.get("by_status")
            exists = bool(pk)
            if stored is not None:
                counts = {s: int(stored.get(s, 0)) for s in ITEM_STATUS}
                return {"scope": pool, "total": total, "by_status": counts, "frozen": pm.get("status") == "FROZEN",
                        "exists": exists, "label_field": pm.get("label_field"),
                        "unresolved_or_failed": counts["UNRESOLVED"] + counts["MISSING"] + counts["WITHDRAWN"]}
            return {"scope": pool, "total": total, "by_status": None, "pending": True,
                    "frozen": pm.get("status") == "FROZEN",
                    "exists": exists, "label_field": pm.get("label_field"),
                    "note": "the pool's by-status tally is live (pay-at-write, §6.4) and is never swept "
                            "on read."}
        # source= / all: PAY-AT-WRITE tallies (A3) — one tally atom per source, maintained by acquire/
        # resolve/reset. NO member sweep on the read path. source= → one tally fetch (O(1)); all → sum
        # over source:sources' tallies (O(#sources)). A source with no tally has acquired nothing through
        # this engine and is reported pending — never swept here, and nothing fills it in later.
        def _tally_of(src_slug):
            tk = self._key("source:tally:%s" % src_slug)
            return self._store_meta(tk) if tk else {}

        if source:
            src_alias = self._alias(self._key(source)) if self._key(source) else source
            tm = _tally_of(self._src_slug(src_alias))
            bs = tm.get("by_status")
            if bs is None:
                return {"scope": src_alias, "total": None, "by_status": None, "pending": True,
                        "note": "per-source tally is pay-at-write (built by acquire/resolve); a source "
                                "without one has acquired nothing through this engine — never swept on read."}
            counts = {s: int(bs.get(s, 0)) for s in ITEM_STATUS}
            return {"scope": src_alias, "total": int(tm.get("total", sum(counts.values()))),
                    "by_status": counts,
                    "unresolved_or_failed": counts["UNRESOLVED"] + counts["MISSING"] + counts["WITHDRAWN"]}
        # all: sum the per-source tallies
        counts = {s: 0 for s in ITEM_STATUS}
        total = 0
        missing = 0
        for sk in self._members("source:sources"):
            tm = _tally_of(self._src_slug(self._alias(sk) or ""))
            bs = tm.get("by_status")
            if bs is None:
                missing += 1
                continue
            for s in ITEM_STATUS:
                counts[s] += int(bs.get(s, 0))
            total += int(tm.get("total", 0))
        return {"scope": "all", "total": total, "by_status": counts,
                "sources_without_tally": missing,
                "unresolved_or_failed": counts["UNRESOLVED"] + counts["MISSING"] + counts["WITHDRAWN"]}

    # ── 3. Pools ────────────────────────────────────────────────────────────────
    def _pool_members_set(self, pool_id: str) -> str:
        return f"{pool_id}:members"

    def _pool_members(self, pool: str) -> List[str]:
        pk = self._key(pool)
        pool_id = self._alias(pk) if pk else pool
        members = self._members(self._pool_members_set(pool_id))
        if not members:
            # A vlab-built pool (vlab.source.add) tracks membership on the pool set itself,
            # not the :members frame set — fall back so source.pool.ls / source.pools report
            # the same corpus the lab runs over (mirrors VisionLabConcept._pool_members).
            members = self._members(pool_id)
        return members

    def op_pool_create(self, name: str, source: str = "", rule: str = "", version: str = "v1",
                       derived_from: str = "", doi: str = "", dataset_version: str = "",
                       artifacts: Any = None, retrieval: str = "", space: str = "",
                       label_field: str = "") -> Dict[str, Any]:
        """Create a Source Pool — the explicit, bounded sampling frame — with a declared, inspectable
        membership rule. A pool is OPEN until frozen. Records the dataset provenance so a frozen frame
        is fully attributable: `doi`, `dataset_version`, `artifacts` (list of {name,sha256,size,uri}),
        and `retrieval` (the locator/mirror — kept DISTINCT from logical identity). A `derived_from`
        records a v2's descent from an earlier version (an addition/correction NEVER rewrites the
        historical pool). `space=group:<gid>` creates the pool in that group engine; empty = nucleus.
        `label_field` (A34) records WHICH source-record field is the class label for a learner — a join
        HINT, not membership, so it is settable even on a FROZEN pool (it never changes the frame)."""
        self._space = space
        # Preserve a namespaced name's colons (e.g. mobility:eu_travel_survey_2014 → the directive's
        # canonical source:pool:mobility:eu_travel_survey_2014:v1_1); only slug a bare single word.
        if name.startswith("source:pool:"):
            base = name
        elif ":" in name:
            base = f"source:pool:{name}"
        else:
            base = f"source:pool:{_slug(name)}"
        pool_id = f"{base}:{version}" if not re.search(r":v\d+$", base) else base
        arts = artifacts if isinstance(artifacts, list) else ([] if artifacts is None else [artifacts])
        meta = {"concept": "source_pool", "name": name, "version": version,
                "membership_rule": rule, "source": source, "status": "OPEN",
                "doi": doi, "dataset_version": dataset_version, "artifacts": arts,
                "retrieval": retrieval, "created_at": round(time.time(), 3),
                "frozen_at": None, "at_seq": None}
        key = self._mk(pool_id, f"[{pool_id}] Source Pool — {rule or 'sampling frame'} [OPEN]", meta)
        # `_mk` is content-addressed and does NOT update an existing atom's meta. A pool a consumer
        # created bare first (e.g. vlab's per-artwork safety net writes source="") would keep the empty
        # provenance, so `source.inspect` could not list it under its source. Enrich the provenance
        # fields on an OPEN pool when this call supplies them — never mutates a FROZEN pool.
        existing = self.cortex.get_meta(key) or {}
        # A34(c) — `label_field` is a descriptive JOIN HINT (which record field is the class label), not
        # membership or a tally, so it is safe to (re)set even on a FROZEN pool. This is what fixes a
        # LIVE pool already frozen without it — one meta write, the frozen members untouched.
        if label_field and existing.get("label_field") != label_field:
            self._set_meta(key, "label_field", label_field)
        if existing.get("status") != "FROZEN":
            for fld, val in (("source", source), ("membership_rule", rule), ("doi", doi),
                             ("dataset_version", dataset_version), ("retrieval", retrieval)):
                if val and existing.get(fld) != val:
                    self._set_meta(key, fld, val)
        elif source and existing.get("source") != source and not self._key(existing.get("source") or ""):
            # A FROZEN pool's membership and tally are immutable — but a pool frozen while its
            # `source` pointer was empty or DANGLING (no such source atom — e.g. the pre-integration
            # CMA import stamped 'source:src:cma', which was never registered) can otherwise never be
            # attributed: source.inspect lists nothing under the real source, forever. Correcting a
            # dangling bookkeeping pointer to the registered source supplied by the re-import is a
            # provenance repair, not a frame mutation. A source that RESOLVES is never overwritten.
            self._set_meta(key, "source", source)
        self.cortex.create_set(self._pool_members_set(pool_id))
        if existing.get("tally") != "live" and not self._members(self._pool_members_set(pool_id)):
            # a new, empty pool starts with a LIVE tally at zero (§6.4) — every member it gains counts
            self._set_meta(key, "by_status", {s: 0 for s in ITEM_STATUS})
            self._set_meta(key, "tally", "live")
        self._add_to_set("source:pools", key)
        if source:
            self._link(pool_id, source, R_POOL_OF)
        if derived_from:
            self._link(pool_id, derived_from, R_DERIVED_FROM)
        return {"pool": pool_id, "version": version, "rule": rule, "status": "OPEN",
                "doi": doi or None, "dataset_version": dataset_version or None,
                "artifacts": len(arts), "derived_from": derived_from or None}

    def _pool_add_one(self, pool: str, item: str) -> str:
        pk = self._key(pool)
        if not pk:
            raise ValueError(f"unknown pool '{pool}' — source.pool.create it first")
        pool_id = self._alias(pk)
        pm = self.cortex.get_meta(pk) or {}
        if pm.get("status") == "FROZEN":
            raise RuntimeError(f"pool '{pool_id}' is FROZEN — create a new version (pool.create derived_from=) "
                               f"instead of mutating a historical frame")
        ik = self._key(item)
        if not ik:
            raise ValueError(f"unknown source item '{item}'")
        mset = self._pool_members_set(pool_id)
        already = mset in self._collections_for_key(ik)      # O(the item's collections), not O(pool)
        self._add_to_set(mset, ik)
        self._link(item, pool_id, R_IN_POOL)
        if not already:
            self._pool_tally_bump(pk, self._store_meta(ik).get("status"), +1)
        return pool_id

    def op_pool_add(self, pool: str, id: str = "", ids: Any = None) -> Dict[str, Any]:
        """Add source item(s) to an OPEN pool. Rejected on a FROZEN pool (immutability)."""
        targets: List[str] = []
        if id:
            targets.append(id)
        if isinstance(ids, list):
            targets.extend(ids)
        elif isinstance(ids, str) and ids:
            targets.extend(x.strip() for x in ids.split(",") if x.strip())
        if not targets:
            raise ValueError("pass id= or ids= (a list / comma-separated)")
        pool_id = None
        for t in targets:
            pool_id = self._pool_add_one(pool, t)
        return {"pool": pool_id, "added": len(targets), "size": len(self._pool_members(pool_id))}

    def _state_ready(self, pool: str) -> None:
        """STATE this pool's readiness the moment it becomes immutable — ruling 2026-09-23 §1 P3.

        The source engine is the one party that knows whether a pool is frozen and non-empty, so it
        is the one party that may say so, and the gate's step 4 reads the fact it states. Before
        this the fact was written only by the boot reconcile, so a pool frozen DURING a run left
        every workload requiring it waiting until the next boot — and the driver's own answer to
        the same question was a private probe, which is the readiness fact held outside the gate
        that this ruling removes. Never raises: an unwritten fact reads as "not ready", which
        closes a door rather than opening one."""
        try:
            from lib.akasha.concepts.workflow import active_kernel as _ak
            from lib.akasha.source.bootstrap import state_source_ready as _state
            k = _ak()
            if k is not None:
                _state(k, str(pool))
        except Exception as exc:                   # noqa: BLE001 — reported, never fatal to a freeze
            logger.warning("[source] readiness fact not stated at freeze pool=%s reason=%s: %s",
                           pool, type(exc).__name__, exc)

    def op_pool_freeze(self, pool: str, space: str = "") -> Dict[str, Any]:
        """Freeze a pool: membership becomes immutable and it is stamped with an Akasha-Time marker,
        so a later model version can be proven to have run against THIS exact evidence population.
        `space=group:<gid>` freezes a group pool; empty = the nucleus (default)."""
        self._space = space
        pk = self._key(pool)
        if not pk:
            raise ValueError(f"unknown pool '{pool}'")
        m = self.cortex.get_meta(pk) or {}
        if m.get("status") == "FROZEN":
            members = self._pool_members(pool)
            n = len(members)
            # Re-freezing a frozen pool recounts NOTHING: its tally is live, kept by the writes.
            by_status = self._ensure_pool_tally(pk)
            if m.get("member_count") is None:
                self._set_meta(pk, "member_count", n)
            self._state_ready(self._alias(pk))
            return {"pool": self._alias(pk), "status": "FROZEN", "already": True,
                    "frozen_at": m.get("frozen_at"), "at_seq": m.get("at_seq"),
                    "member_count": n, "by_status": by_status}
        at = self._at_now()
        members = self._pool_members(pool)
        n = len(members)
        # The by-status tally is LIVE (§6.4): counted member by member and moved by every status
        # change. Freezing reads it; it is never recounted.
        by_status = self._ensure_pool_tally(pk)
        self._set_meta(pk, "status", "FROZEN")
        self._set_meta(pk, "frozen_at", at["at_wall"])
        self._set_meta(pk, "at_seq", at["at_seq"])
        self._set_meta(pk, "member_count", n)
        self._state_ready(self._alias(pk))
        return {"pool": self._alias(pk), "status": "FROZEN", "member_count": n,
                "frozen_at": at["at_wall"], "at_seq": at["at_seq"], "by_status": by_status}

    def op_pool_ls(self, pool: str, limit: Any = "", offset: Any = "") -> Dict[str, Any]:
        """Enumerate a pool's members — the full sampling frame is inspectable, but PAGED so a large
        corpus (e.g. 26k rows) does not force one `get_meta` per member or a 26k-row payload. `count`
        is always the true total; `members` is the requested page (per-member reads are bounded to it).
        No/zero `limit` → a capped default page (never the whole pool); page with `limit`/`offset`."""
        pk = self._key(pool)
        if not pk:
            raise ValueError(f"unknown pool '{pool}'")
        m = self.cortex.get_meta(pk) or {}
        keys = self._pool_members(pool)                 # member KEYS only — no per-member read yet
        total = len(keys)
        # SERVER-SIDE PAGE CAP (F50): a guest must never be able to request an uncapped stream. No/zero
        # limit → a default page; any explicit limit is hard-capped. The full sampling frame stays fully
        # inspectable — via paging (offset), for CLI/admin too; `truncated`+`count` say how to continue.
        _DEF, _MAX = 500, 1000
        try:
            lim = int(limit) if str(limit).strip() else _DEF
        except (TypeError, ValueError):
            lim = _DEF
        if lim <= 0:
            lim = _DEF
        lim = min(lim, _MAX)
        try:
            off = max(0, int(offset)) if str(offset).strip() else 0
        except (TypeError, ValueError):
            off = 0
        page_keys = keys[off:off + lim]
        members = []
        for k in page_keys:                             # read meta ONLY for the page
            im = self.cortex.get_meta(k) or {}
            members.append({"item": self._alias(k), "status": im.get("status"),
                            "source_record_id": im.get("source_record_id")})
        return {"pool": self._alias(pk), "source": m.get("source") or None,
                "version": m.get("version"), "status": m.get("status"),
                "rule": m.get("membership_rule"), "doi": m.get("doi") or None,
                "dataset_version": m.get("dataset_version") or None,
                "artifacts": m.get("artifacts") or [], "retrieval": m.get("retrieval") or None,
                "frozen_at": m.get("frozen_at"), "at_seq": m.get("at_seq"),
                "count": total, "offset": off, "returned": len(members),
                "truncated": (off + len(members)) < total, "members": members}

    def op_pool_scan(self, pool: str, fields: Any = "", limit: Any = 5000) -> Dict[str, Any]:
        """Project selected `source_metadata` fields across a pool's items — a bounded, guest-safe
        read so a viewer can chart / scatter / aggregate the RAW data without one read per atom.

        RAW ONLY: it returns the verbatim source_metadata values, adds no interpretation. With no
        `fields`, it returns the available field NAMES (the union of keys seen in a sample) so the
        caller can pick axes. The Source Data Viewer's Analysis View is built on this."""
        pk = self._key(pool)
        if not pk:
            raise ValueError(f"unknown pool '{pool}'")
        mem = self._pool_members(pool)
        try:
            lim = max(1, min(int(limit or 5000), 5000))   # guest surface — hard-capped rows/reads (F50)
        except (TypeError, ValueError):
            lim = 5000
        flds = ([f.strip() for f in fields.split(",") if f.strip()] if isinstance(fields, str)
                else [str(f) for f in (fields or [])])
        if not flds:
            seen: List[str] = []
            for k in mem[:200]:                       # sample the frame for its field names
                sm = (self.cortex.get_meta(k) or {}).get("source_metadata") or {}
                for key in sm.keys():
                    if key not in seen:
                        seen.append(key)
            return {"pool": self._alias(pk), "count": len(mem), "fields": seen}
        rows = []
        for k in mem[:lim]:
            sm = (self.cortex.get_meta(k) or {}).get("source_metadata") or {}
            row = {"item": self._alias(k)}
            for f in flds:
                row[f] = sm.get(f)
            rows.append(row)
        return {"pool": self._alias(pk), "count": len(mem), "returned": len(rows),
                "fields": flds, "rows": rows, "truncated": len(mem) > lim}

    def _samples_by_pool(self) -> Dict[str, List[Dict[str, Any]]]:
        """D2-M §4.4 — samples grouped by their pool id: {pool: [{sample, role, n, seed,
        complement_of}]}. O(#samples), read once so op_pools stays O(#pools + #samples)."""
        by: Dict[str, List[Dict[str, Any]]] = {}
        for sk in self._members("source:samples"):
            sm = self.cortex.get_meta(sk) or {}
            if sm.get("concept") != "source_sample":
                continue
            sid = self._alias(sk)
            by.setdefault(sm.get("pool") or "", []).append(
                {"sample": sid, "role": sm.get("role") or (sid.rsplit(":", 1)[-1] if sid else None),
                 "n": sm.get("member_count"), "seed": sm.get("seed"),
                 "complement_of": sm.get("complement_of")})
        return by

    def sample_roles_for(self, item_key: str, pool: str = "") -> List[Dict[str, Any]]:
        """D2-M §4.1 — every sample the item is a member of, as {sample, role, n}. Bounded by the
        samples of the item's pool (a handful), each a Set membership test — never a store scan."""
        out: List[Dict[str, Any]] = []
        for sk in self._members("source:samples"):
            sm = self.cortex.get_meta(sk) or {}
            if sm.get("concept") != "source_sample":
                continue
            if pool and sm.get("pool") and sm.get("pool") != pool:
                continue
            sid = self._alias(sk)
            if item_key in set(self._members(f"{sid}:members")):
                out.append({"sample": sid, "role": sm.get("role")
                            or (sid.rsplit(":", 1)[-1] if sid else None), "n": sm.get("member_count")})
        return out

    def op_pools(self) -> Dict[str, Any]:
        """List every Source Pool with version, member count, freeze state, provenance, and its
        samples (D2-M §4.4 — role/n/seed/complement_of per sample)."""
        out = []
        samples = self._samples_by_pool()
        for k in self._members("source:pools"):
            m = self.cortex.get_meta(k) or {}
            pid = self._alias(k)
            out.append({"pool": pid, "version": m.get("version"),
                        "status": m.get("status"), "rule": m.get("membership_rule"),
                        "source": m.get("source") or None,       # origin — lets the viewer group datasets by source
                        "doi": m.get("doi") or None, "dataset_version": m.get("dataset_version") or None,
                        "artifacts": len(m.get("artifacts") or []),
                        # O(#pools): a frozen pool stores member_count at freeze; only an OPEN pool
                        # (no stored count) falls back to a key-list length. Never a per-member sweep.
                        "count": (m.get("member_count") if m.get("member_count") is not None
                                  else len(self._pool_members(pid))),
                        "samples": samples.get(pid, []),
                        "frozen_at": m.get("frozen_at"), "at_seq": m.get("at_seq")})
        return {"pools": out, "count": len(out)}

    def op_pool_diff(self, a: str, b: str) -> Dict[str, Any]:
        """Compare two pool versions' membership + acquisition failures before using a newer one,
        so a changed result can be attributed to the experiment, not a silently changed corpus."""
        ma = {self._alias(k) for k in self._pool_members(a)}
        mb = {self._alias(k) for k in self._pool_members(b)}
        def _fails(pool):
            return sum(1 for k in self._pool_members(pool)
                       if (self.cortex.get_meta(k) or {}).get("status") in ("UNRESOLVED", "MISSING", "WITHDRAWN"))
        return {"a": self._alias(self._key(a)) if self._key(a) else a,
                "b": self._alias(self._key(b)) if self._key(b) else b,
                "only_in_a": sorted(ma - mb), "only_in_b": sorted(mb - ma),
                "shared": len(ma & mb), "a_count": len(ma), "b_count": len(mb),
                "a_failures": _fails(a), "b_failures": _fails(b)}

    def op_pool_sample(self, pool: str, name: str, rule: str = "", n: str = "", seed: str = "akasha",
                       strata: str = "", weight: str = "", model: str = "") -> Dict[str, Any]:
        """Create a FROZEN, DETERMINISTIC sampled Set from a FROZEN pool — an experiment-specific
        subset that keeps the full population visible (§9). Only AFTER the pool is frozen. Records the
        selection `rule`, `seed`, optional `strata` (a source_metadata field to balance across, e.g.
        country), `weight` handling, `model` version, and an Akasha-Time marker. Members are
        REFERENCES into the pool — the source atoms are never copied, and the pool stays the frame.
        Deterministic: ordering is hash(seed+item), so the same (pool,seed,n,strata) reproduces the
        same sample for a later rerun."""
        pk = self._key(pool)
        if not pk:
            raise ValueError(f"unknown pool '{pool}'")
        pm = self.cortex.get_meta(pk) or {}
        if pm.get("status") != "FROZEN":
            raise RuntimeError(f"pool '{self._alias(pk)}' must be FROZEN before sampling — the full "
                               f"population must exist and be fixed before an experiment subsets it")
        pool_id = self._alias(pk)
        members = self._pool_members(pool)

        # rule=complement:<sample> (Part D §1.1) — restrict the candidate members to those NOT in the
        # named sibling sample, so a train/target split from the SAME frozen pool is disjoint by
        # construction. The named sample lives at source:sample:<pool_short>:<name>; its :members set is
        # the exclusion. Deterministic (the seeded/stratified sampling below then runs over the remainder).
        # keep the pool's namespaced tail verbatim (colons preserved, like op_pool_create) so a sample of
        # source:pool:plants_images:v1 is source:sample:plants_images:v1:<name> — not a slug-flattened id.
        _pool_tail = pool_id.replace("source:pool:", "")
        complement_of = None
        _rule_s = str(rule or "")
        if _rule_s.startswith("complement:"):
            refname = _rule_s.split(":", 1)[1].strip()
            ref_sample = f"source:sample:{_pool_tail}:{_slug(refname)}"
            excluded = set(self._members(f"{ref_sample}:members"))
            if not self._key(ref_sample):
                raise ValueError(f"complement:{refname} — no sample '{ref_sample}' to take the "
                                 f"complement of (create it first)")
            members = [k for k in members if k not in excluded]
            complement_of = ref_sample

        def _rank(k):
            return hashlib.sha256((str(seed) + self._alias(k)).encode()).hexdigest()

        want = int(n) if str(n).isdigit() and int(n) > 0 else len(members)
        if strata:
            buckets: Dict[str, List[str]] = {}
            for k in members:
                v = str(((self.cortex.get_meta(k) or {}).get("source_metadata") or {}).get(strata, "?"))
                buckets.setdefault(v, []).append(k)
            for v in buckets:
                buckets[v].sort(key=_rank)
            chosen: List[str] = []
            keys = sorted(buckets)
            i = 0
            while len(chosen) < want and any(buckets[v] for v in keys):
                v = keys[i % len(keys)]
                if buckets[v]:
                    chosen.append(buckets[v].pop(0))
                i += 1
        else:
            chosen = sorted(members, key=_rank)[:want]
        at = self._at_now()
        sample_id = f"source:sample:{_pool_tail}:{_slug(name)}"
        meta = {"concept": "source_sample", "pool": pool_id, "selection_rule": rule, "seed": str(seed),
                "n_requested": want, "strata": strata or None, "weight_handling": weight or None,
                "model_version": model or None, "status": "FROZEN", "frozen_at": at["at_wall"],
                "at_seq": at["at_seq"], "member_count": len(chosen), "complement_of": complement_of,
                # D2-M §4.1/§4.4 — the sample NAME is the role a workflow addresses it by (role:target,
                # role:train), so vlab.item's sample_roles + source.pools' samples can name it directly.
                "role": _slug(name)}
        self._mk(sample_id, f"[{sample_id}] Source Sample of {pool_id} (n={len(chosen)}) [FROZEN]", meta)
        self.cortex.create_set(f"{sample_id}:members")
        for k in chosen:
            self._add_to_set(f"{sample_id}:members", k)
        self._add_to_set("source:samples", self._key(sample_id))
        self._link(sample_id, pool_id, R_DERIVED_FROM)
        logger.info("[pool.sample] name=%s n=%s complement_of=%s", name, len(chosen),
                    complement_of or "-")
        return {"sample": sample_id, "pool": pool_id, "member_count": len(chosen), "n_requested": want,
                "seed": str(seed), "strata": strata or None, "model_version": model or None,
                "complement_of": complement_of,
                "status": "FROZEN", "at_seq": at["at_seq"],
                "note": "the full population stays visible in the pool; this is an experiment subset (§9)"}

    def op_samples(self) -> Dict[str, Any]:
        """List every Source Sample (experiment subset) with its pool, selection rule, and size."""
        out = []
        for k in self._members("source:samples"):
            m = self.cortex.get_meta(k) or {}
            out.append({"sample": self._alias(k), "pool": m.get("pool"), "rule": m.get("selection_rule"),
                        "seed": m.get("seed"), "strata": m.get("strata"),
                        "count": m.get("member_count"), "at_seq": m.get("at_seq")})
        return {"samples": out, "count": len(out)}

    # ── 4. Streams + snapshots (observational) ──────────────────────────────────
    def op_stream_create(self, id: str, source: str = "", rule: str = "",
                         polling: str = "", space: str = "") -> Dict[str, Any]:
        """Register a Source Stream — an append-oriented sequence whose population changes over
        Akasha Time. The acquisition/polling rule is FROZEN (versioned) while observations append.
        G1.2 — `space=group:<gid>` places the stream in that group's engine (a closed bench's
        observation stream, private to members); empty = the shared nucleus (today)."""
        self._space = space
        sid = id if id.startswith("source:stream:") else f"source:stream:{_slug(id)}"
        at = self._at_now()
        meta = {"concept": "source_stream", "source": source, "acquisition_rule": rule,
                "acquisition_rule_version": 1, "polling_rule": polling, "status": "ACTIVE",
                "space": space or None, "started_at": at["at_wall"], "at_seq": at["at_seq"]}
        key = self._mk(sid, f"[{sid}] Source Stream — {rule or 'observation stream'} [ACTIVE]", meta)
        self._create_set(f"{sid}:obs")
        self._add_to_set("source:streams", key)
        if source:
            self._link(sid, source, R_SUPPLIED_BY)
        return {"stream": sid, "status": "ACTIVE", "rule": rule, "at_seq": at["at_seq"],
                "space": space or None}

    def op_stream_append(self, stream: str, records: Any = None, text: str = "",
                         id_field: str = "id", space: str = "") -> Dict[str, Any]:
        """Append observation(s) to a stream. Each retained observation is independently
        addressable and ordered by Akasha Time (never only the latest GUI state). `space=` targets a
        group stream (G1.2); the at_seq counter stays the nucleus source:clock (globally comparable)."""
        self._space = space
        sk = self._key(stream)
        if not sk:
            raise ValueError(f"unknown stream '{stream}'")
        stream_id = self._alias(sk)
        recs = self._parse_records(records, text, "")
        base_n = len(self._members(f"{stream_id}:obs"))
        appended = 0
        obs_ids = []
        last_seq = None
        for rec in recs:
            # Number each observation by its own Akasha-Time at_seq — the RECORDING order, a monotonic
            # global counter that is UNIQUE FOREVER and never reused. The old `obs:{len+1}` id reused an id
            # after any removal (compaction/reset/retry), and alias-idempotency then swallowed the NEW
            # observation into the OLD atom — silent data loss (B1). at_seq ids also compare directly with
            # snapshot windows (this snapshot froze before that observation is provable from ids alone).
            at = self._at_now()
            obs_id = f"{stream_id}:obs:{at['at_seq']}"
            om = {"concept": "source_observation", "stream": stream_id,
                  "source_metadata": rec if "__malformed__" not in rec else {},
                  "observed_at": at["at_wall"], "at_seq": at["at_seq"],
                  "status": "ACQUIRED" if "__malformed__" not in rec else "UNRESOLVED",
                  "failure": rec.get("__malformed__")}
            self._mk(obs_id, f"[{obs_id}] Stream observation @ at_seq {at['at_seq']}.", om)
            self._link(obs_id, stream_id, R_IN_STREAM)
            self._add_to_set(f"{stream_id}:obs", self._key(obs_id))
            obs_ids.append(obs_id)
            appended += 1
            last_seq = at["at_seq"]
        return {"stream": stream_id, "appended": appended, "at_seq": last_seq,
                "total_observations": base_n + appended, "observations": obs_ids[:50]}

    def op_stream(self, stream: str, as_of: str = "", limit: Any = 200,
                  space: str = "") -> Dict[str, Any]:
        """[source.stream] Read a Source Stream's observations in Akasha-Time order — the Source Viewer
        view (G1.4). `as_of=<at_seq τ>` clips to observations at or before τ (the bench view 'as of'
        a coordinate); `space=group:<gid>` reads a closed bench's stream. Read-only; never mutates."""
        self._space = space
        # accept the full stream id, or a short form the bench uses (source.stream wb:<name> →
        # source:stream:wb:<name>) — prefer the actual stream atom over any same-named atom.
        cand = stream if str(stream).startswith("source:stream:") else f"source:stream:{stream}"
        sk = self._key(cand) or self._key(stream)
        if not sk:
            raise ValueError(f"unknown stream '{stream}'")
        stream_id = self._alias(sk)
        tau = int(as_of) if str(as_of).strip().isdigit() else None
        try:
            lim = max(1, int(limit))
        except (TypeError, ValueError):
            lim = 200
        rows = []
        for k in self._members(f"{stream_id}:obs"):
            m = self._get_meta(k)
            seq = int(m.get("at_seq") or 0)
            if tau is not None and seq > tau:
                continue
            rows.append({"id": self._alias(k), "at_seq": seq,
                         "source_metadata": m.get("source_metadata") or {},
                         "observed_at": m.get("observed_at"), "status": m.get("status")})
        rows.sort(key=lambda r: r.get("at_seq") or 0)
        sm = self._meta(stream_id)
        return {"stream": stream_id, "as_of": tau, "count": len(rows),
                "space": sm.get("space"), "observations": rows[:lim]}

    def op_snapshot_create(self, stream: str, from_seq: str = "", to_seq: str = "",
                           name: str = "", space: str = "") -> Dict[str, Any]:
        """Freeze a reproducible time-bounded window of a stream as a Source Snapshot, so a later
        analysis version can be rerun against the SAME historical observation window. `space=` for a
        group stream (G1.2)."""
        self._space = space
        sk = self._key(stream)
        if not sk:
            raise ValueError(f"unknown stream '{stream}'")
        stream_id = self._alias(sk)
        obs = self._members(f"{stream_id}:obs")
        lo = int(from_seq) if str(from_seq).isdigit() else 0
        hi = int(to_seq) if str(to_seq).isdigit() else 10 ** 12
        window = [k for k in obs if lo <= int(self._get_meta(k).get("at_seq", 0)) <= hi]
        at = self._at_now()
        snap_id = f"source:snapshot:{_slug(stream_id.replace('source:stream:', ''))}:{name or f'{lo}-{hi}'}"
        meta = {"concept": "source_snapshot", "stream": stream_id, "window": [lo, hi],
                "status": "FROZEN", "frozen_at": at["at_wall"], "at_seq": at["at_seq"],
                "member_count": len(window)}
        key = self._mk(snap_id, f"[{snap_id}] Source Snapshot of {stream_id} window [{lo},{hi}] [FROZEN]", meta)
        self._create_set(f"{snap_id}:members")
        for k in window:
            self._add_to_set(f"{snap_id}:members", k)
        self._add_to_set("source:snapshots", key)
        self._link(snap_id, stream_id, R_SNAPSHOT_OF)
        self._link(snap_id, stream_id, R_DERIVED_FROM)
        return {"snapshot": snap_id, "stream": stream_id, "window": [lo, hi],
                "member_count": len(window), "status": "FROZEN", "at_seq": at["at_seq"]}

    # ── 5. Interpretation bridge ─────────────────────────────────────────────────
    def op_bridge(self, src: str, dst: str, rel: str = "selected_from", by: str = "",
                  run: str = "", params: str = "", status: str = "") -> Dict[str, Any]:
        """Bridge an interpreted atom to the source item it used. `src` is the INTERPRETED atom
        (e.g. blvh:slot:051), `dst` is the SOURCE item (e.g. source:item:bl:037); `rel` ∈
        selected_from / observed_from / interprets / rejects. The bridge is ADDITIVE — it creates
        a relation + a bridge EVENT (recording the operation: model/run/params/Akasha-Time) and
        NEVER mutates the source atom into an interpreted object."""
        if rel not in BRIDGE_RELS:
            raise ValueError(f"rel must be one of {sorted(BRIDGE_RELS)} (got '{rel}')")
        dk = self._key(dst)
        if not dk or (self.cortex.get_meta(dk) or {}).get("concept") not in (
                "source_item", "source_observation", "source_snapshot"):
            raise ValueError(f"'{dst}' is not a source item/observation/snapshot — bridge targets the SOURCE")
        # the interpreted atom may live in any laboratory (blvh:slot:*, lab:*, obs:*) — link as given
        self._link(src, dst, BRIDGE_RELS[rel])
        at = self._at_now()
        seq = len(self._members("source:bridges")) + 1
        bid = f"source:bridge:{seq}"
        bmeta = {"concept": "source_bridge", "interpreted": src, "source_item": self._alias(dk),
                 "relation": rel, "generated_by": by or None, "run": run or None,
                 "parameters": params or None, "status": status or "recorded",
                 "at_seq": at["at_seq"], "at_wall": at["at_wall"]}
        self._mk(bid, f"[{bid}] Bridge: {src} --{rel}--> {self._alias(dk)}", bmeta)
        self._link(bid, src, R_BRIDGE_INTERP)
        self._link(bid, dst, R_BRIDGE_SRC)
        if by:
            self._link(bid, by, R_GENERATED_BY)
        self._add_to_set("source:bridges", self._key(bid))
        self._bridge_index_add(self._key(bid), self._alias(dk), src)   # A4 — endpoint indexes (alias-keyed)
        return {"bridge": bid, "interpreted": src, "source_item": self._alias(dk),
                "relation": rel, "generated_by": by or None, "at_seq": at["at_seq"]}

    def record_observation_bridge(self, observation: str, source: str, observer: str = "",
                                  model: str = "", run: str = "", model_sha8: str = "",
                                  degraded: bool = False, detection_count: int = 0,
                                  cronon: Any = None, family: str = "", bench: str = "",
                                  wf_branch: str = "", mode: str = "") -> Dict[str, Any]:
        """Part D §4.2 — register (idempotently) ONE bridge event for a vlab observation → its source
        item, so `source.trace` lists the observation under `interpretations` without a scan. rel is
        `observed_by` (the observation observed the source); the observer / model / model sha8 (the
        observer VERSION for a learned head) / degraded / detection count / cronon travel on the bridge
        so the trace renders the reading directly. One bridge per observation (the interp endpoint index
        is the idempotency guard). Called on the observation's own write path — never a scan."""
        dk = self._key(source)
        if not dk or (self.cortex.get_meta(dk) or {}).get("concept") not in (
                "source_item", "source_observation", "source_snapshot"):
            return {"bridge": None, "skipped": "not a source item"}
        if self._members("source:bridges:interp:%s" % _slug(str(observation))):
            return {"bridge": None, "already": True}          # one bridge per observation
        self._link(observation, source, R_OBSERVED_FROM)
        at = self._at_now()
        seq = len(self._members("source:bridges")) + 1
        bid = f"source:bridge:{seq}"
        bmeta = {"concept": "source_bridge", "interpreted": observation, "source_item": self._alias(dk),
                 "relation": "observed_by", "generated_by": observer or None, "run": run or None,
                 "parameters": model_sha8 or None, "observer_version": model_sha8 or None,
                 "model": model or None, "degraded": bool(degraded),
                 "detection_count": int(detection_count or 0), "cronon": cronon,
                 # D2-M §4.6 — the coordinate layer travels on the bridge, so source.trace renders
                 # family / bench / wf_branch / mode without a second lookup.
                 "family": family or None, "bench": bench or None,
                 "wf_branch": wf_branch or None, "mode": mode or None,
                 "status": "recorded", "at_seq": at["at_seq"], "at_wall": at["at_wall"]}
        self._mk(bid, f"[{bid}] Bridge: {observation} --observed_by--> {self._alias(dk)}", bmeta)
        self._link(bid, observation, R_BRIDGE_INTERP)
        self._link(bid, source, R_BRIDGE_SRC)
        self._add_to_set("source:bridges", self._key(bid))
        self._bridge_index_add(self._key(bid), self._alias(dk), observation)
        return {"bridge": bid, "observation": observation, "source_item": self._alias(dk)}

    def op_trace(self, id: str) -> Dict[str, Any]:
        """Trace BOTH directions without collapsing readings into the source. From a SOURCE item →
        every experiment/model/human interpretation that referenced it. From an INTERPRETED atom →
        the source items it used. Each edge names the bridge operation. Works even when the
        interpreted atom lives in another laboratory (or is not yet materialized) — the bridge
        registry is the authoritative reverse index, so an id is resolvable by alias OR bare string."""
        k = self._key(id)                       # may be None for an external/interpreted id
        m = (self.cortex.get_meta(k) or {}) if k else {}
        is_source = m.get("concept") in ("source_item", "source_observation", "source_snapshot")
        id_alias = self._alias(k) if k else id
        interpretations: List[Dict[str, Any]] = []
        sources: Dict[str, Dict[str, Any]] = {}
        # A stored SOURCE atom may also carry direct outgoing bridge relations (defensive; the
        # registry below is the primary index).
        if k and not is_source:
            inv = {v: kk for kk, v in BRIDGE_RELS.items()}
            for dst, rel in self.cortex.get_adjacent_links(k):
                if rel in inv:
                    a = self._alias(dst)
                    sources[a] = {"source_item": a, "relation": inv[rel]}
        # A4 — read the ONE endpoint membrane for this id (O(bridges-of-this-atom)), not the whole
        # registry. The index is alias-keyed, so it survives a source.reload that re-mints items.
        if is_source:
            idx = self._members("source:bridges:src:%s" % _slug(id_alias))
        else:
            idx = self._members("source:bridges:interp:%s" % _slug(str(id_alias)))
            if id_alias != id:
                idx = list(dict.fromkeys(idx + self._members("source:bridges:interp:%s" % _slug(str(id)))))
        observations: List[Dict[str, Any]] = []
        for bk in idx:
            bm = self.cortex.get_meta(bk) or {}
            if is_source and bm.get("source_item") == id_alias:
                interpretations.append({"interpreted": bm.get("interpreted"), "relation": bm.get("relation"),
                                        "generated_by": bm.get("generated_by"), "run": bm.get("run"),
                                        "observer_version": bm.get("observer_version"),
                                        "family": bm.get("family"), "bench": bm.get("bench"),
                                        "wf_branch": bm.get("wf_branch"), "mode": bm.get("mode"),
                                        "at_seq": bm.get("at_seq"), "bridge": self._alias(bk)})
                # an OBSERVATION bridge (`record_observation_bridge`) carries the reading itself —
                # observer, version, degraded, detections, cronon — so the trace renders it from the
                # bridge alone: the engine reads its own record, never the observing model's atoms.
                if bm.get("relation") == "observed_by":
                    observations.append({"observation": bm.get("interpreted"),
                                         "observer": bm.get("generated_by"),
                                         "observer_version": bm.get("observer_version"),
                                         "run": bm.get("run"), "family": bm.get("family"),
                                         "bench": bm.get("bench"), "wf_branch": bm.get("wf_branch"),
                                         "mode": bm.get("mode"), "status": bm.get("status"),
                                         "degraded": bool(bm.get("degraded")),
                                         "detections": int(bm.get("detection_count") or 0),
                                         "cronon": bm.get("cronon"), "at_seq": bm.get("at_seq")})
            if (not is_source) and bm.get("interpreted") in (id, id_alias):
                si = bm.get("source_item")
                sources[si] = {"source_item": si, "relation": bm.get("relation"),
                               "generated_by": bm.get("generated_by"), "at_seq": bm.get("at_seq"),
                               "bridge": self._alias(bk)}
        observations.sort(key=lambda r: (r.get("at_seq") or 0, str(r.get("run") or "")))
        return {"atom": id_alias, "kind": "source" if is_source else "interpretation",
                "interpretations": interpretations, "observations": observations,
                "sources": list(sources.values()),
                "note": "readings are not collapsed into the source — the same item may carry incompatible interpretations"}

    # ── 6. Laboratory evidence declaration + audit ───────────────────────────────
    def op_lab_declare(self, lab: str, klass: str, primary_source: str = "", pool: str = "",
                       stream: str = "", authored_scope: str = "",
                       fixture_policy: str = "") -> Dict[str, Any]:
        """Declare a laboratory's evidence profile: how it is grounded (AUTHORED | CORPUS |
        OBSERVATIONAL) and which source structures must exist before it can claim an
        evidence-backed run. Metadata ABOUT the lab — it does not duplicate the research model."""
        kl = (klass or "").upper()
        if kl not in ACQ_CLASSES:
            raise ValueError(f"klass must be one of {ACQ_CLASSES} (got '{klass}')")
        prof_id = f"source:evidence:{_slug(lab)}"
        # evidence status derives from whether the required source structure is present + frozen
        status = self._eval_evidence(kl, pool, stream, authored_scope)
        at = self._at_now()
        meta = {"concept": "source_evidence_profile", "lab_id": lab, "acquisition_class": kl,
                "primary_source_ids": primary_source, "raw_pool_ids": pool, "observation_stream_ids": stream,
                "authored_scope_id": authored_scope, "fixture_policy": fixture_policy,
                "evidence_status": status, "audited_at": at["at_wall"], "at_seq": at["at_seq"]}
        key = self._mk(prof_id, f"[{prof_id}] Evidence profile for {lab}: {kl} → {status}", meta)
        # _mk is content-addressed and never updates an existing atom's meta — but a RE-declare is
        # exactly how a profile is corrected (a fixed fixture_policy, or a status that changed once
        # the pool froze). Update any field whose freshly-declared value differs, so the stored
        # profile always reflects the LATEST declaration + evaluation.
        existing = self.cortex.get_meta(key) or {}
        for fld, val in meta.items():
            if existing.get(fld) != val:
                self._set_meta(key, fld, val)
        self._add_to_set("source:evidence_profiles", self._key(prof_id))
        # connect the lab to its source structure (samples_from / observes_from / authored_scope)
        if kl == "CORPUS" and pool:
            self._link(lab, pool, R_SAMPLES_FROM)
        elif kl == "OBSERVATIONAL" and stream:
            self._link(lab, stream, R_OBSERVES_FROM)
        elif kl == "AUTHORED" and authored_scope:
            self._link(lab, authored_scope, R_AUTHORED_SCOPE)
        return {"lab": lab, "acquisition_class": kl, "evidence_status": status,
                "pool": pool or None, "stream": stream or None, "authored_scope": authored_scope or None}

    def _eval_evidence(self, kl: str, pool: str, stream: str, authored_scope: str) -> str:
        """GROUNDED only when the class's required source structure exists AND (for CORPUS) is frozen."""
        if kl == "AUTHORED":
            return "GROUNDED" if authored_scope else "PARTIAL"
        if kl == "CORPUS":
            pk = self._key(pool)
            if not pk:
                return "UNGROUNDED"
            return "GROUNDED" if (self.cortex.get_meta(pk) or {}).get("status") == "FROZEN" else "PARTIAL"
        if kl == "OBSERVATIONAL":
            return "GROUNDED" if self._key(stream) else "UNGROUNDED"
        return "UNGROUNDED"

    def op_lab_profile(self, lab: str) -> Dict[str, Any]:
        """Read a laboratory's evidence profile + its (re-evaluated) evidence status."""
        prof_id = f"source:evidence:{_slug(lab)}"
        k = self._key(prof_id)
        if not k:
            return {"lab": lab, "declared": False,
                    "note": "no evidence profile — run source.lab.declare (or source.audit)"}
        m = self.cortex.get_meta(k) or {}
        live = self._eval_evidence(m.get("acquisition_class", ""), m.get("raw_pool_ids", ""),
                                   m.get("observation_stream_ids", ""), m.get("authored_scope_id", ""))
        return {"lab": lab, "declared": True, "acquisition_class": m.get("acquisition_class"),
                "evidence_status": live, "declared_status": m.get("evidence_status"),
                "pool": m.get("raw_pool_ids") or None, "stream": m.get("observation_stream_ids") or None,
                "authored_scope": m.get("authored_scope_id") or None,
                "primary_source": m.get("primary_source_ids") or None,
                "fixture_policy": m.get("fixture_policy") or None, "audited_at": m.get("audited_at")}

    def op_labs(self) -> Dict[str, Any]:
        """[source.labs] List every laboratory that has DECLARED a source evidence profile
        (source.lab.declare) — the labs the Source Viewer's evidence panel is about. Each row carries
        the lab's live-evaluated evidence status, acquisition class, and bound pool. O(K) over the
        evidence-profiles membrane (no scan). This is DISTINCT from `labo.ls` (the labo world-model
        namespace): a lab can ground itself on a source pool via `source.lab.declare` without ever
        minting a `labo:` — so the hub lists the union of both."""
        out = []
        for pk in self._members("source:evidence_profiles"):
            m = self._meta(pk) or {}
            lab = m.get("lab_id") or (self._alias(pk) or "").replace("source:evidence:", "")
            if not lab:
                continue
            live = self._eval_evidence(m.get("acquisition_class", ""), m.get("raw_pool_ids", ""),
                                       m.get("observation_stream_ids", ""), m.get("authored_scope_id", ""))
            out.append({"lab": lab, "acquisition_class": m.get("acquisition_class"),
                        "evidence_status": live, "pool": m.get("raw_pool_ids") or None,
                        "primary_source": m.get("primary_source_ids") or None})
        out.sort(key=lambda r: str(r.get("lab") or ""))
        return {"labs": out, "count": len(out)}

    def op_audit(self, lab: str) -> Dict[str, Any]:
        """Audit a laboratory for a real, traceable sampling frame. Reports whether it declares an
        evidence profile, whether its required source structure exists and is frozen, and (for a
        CORPUS lab) whether its interpreted atoms actually bridge to source items. A lab is NOT
        evidence-grounded merely because it displays plausible records or has a complete ontology."""
        prof = self.op_lab_profile(lab)
        findings: List[str] = []
        if not prof.get("declared"):
            findings.append("no evidence profile declared (source.lab.declare)")
            return {"lab": lab, "evidence_status": "UNGROUNDED", "grounded": False,
                    "bridged": 0, "findings": findings}
        kl = prof.get("acquisition_class")
        bridged = 0
        if kl == "CORPUS":
            pool = prof.get("pool")
            if not pool or not self._key(pool):
                findings.append("CORPUS lab has no Source Pool")
            elif (self._meta(pool).get("status") != "FROZEN"):
                findings.append(f"Source Pool '{pool}' is not FROZEN (sampling frame not fixed)")
            # are any interpreted atoms actually bridged to source items IN THIS FRAME? (precise — a
            # bridge counts only if its source item is a member of the declared pool). A7: test membership
            # via the item's collections containing `<pool>:members` — O(#bridges) with an O(1) probe, no
            # full-pool alias set materialized. Admin-frequency, so the honest bridge walk is the right cost.
            members_set = ("%s:members" % self._alias(self._key(pool))) if (pool and self._key(pool)) else None
            bridged = 0
            if members_set:
                for bk in self._members("source:bridges"):
                    si = (self.cortex.get_meta(bk) or {}).get("source_item")
                    sk = self._key(si) if si else None
                    if sk and members_set in self._collections_for_key(sk):
                        bridged += 1
            if bridged == 0:
                findings.append("no interpretation bridges to source items yet (results not traceable to the frame)")
        elif kl == "OBSERVATIONAL":
            if not prof.get("stream") or not self._key(prof.get("stream")):
                findings.append("OBSERVATIONAL lab has no Source Stream")
        elif kl == "AUTHORED":
            if not prof.get("authored_scope"):
                findings.append("AUTHORED lab has no explicit authored scope")
        status = prof.get("evidence_status")
        return {"lab": lab, "acquisition_class": kl, "evidence_status": status,
                "grounded": status == "GROUNDED" and not findings, "bridged": bridged,
                "findings": findings or ["evidence boundary is visible and traceable"]}
