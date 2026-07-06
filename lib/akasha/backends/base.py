"""
AkashaBackend — Abstract interface for the Akasha physical layer.

This is the assembler instruction set contract.  Every backend satisfies
this surface; composite, session, and IAM layers depend only on it.

Design rationale (instruction-set principle):
  Abstraction is confined to core only — composite and above are unaffected.
  Each method is a primitive with no dependency on other methods in the class.
  Composite.py builds compound behaviour from these primitives in pure Python.
  A new backend (cloud, IoT, Cython) only needs to satisfy this ~40-method set;
  all higher-level logic is inherited automatically.

Scalability targets:
  1. Cloud/distributed storage (S3+DynamoDB, Firestore, CockroachDB …)
  2. IoT / sensor-actuator mapping via get_chunk_raw / put_chunk_raw overrides
  3. DTN (Delay-Tolerant Networking) — pending_links → SQS/PubSub message queue
  4. Cython port — only this surface needs C-extension reimplementation

Sensor / actuator binding and the simulation-first control loop:
  get_chunk_raw and put_chunk_raw are the two hardware seams in this ISA.
  Overriding them in an IoT backend maps physical I/O onto the graph:

    get_chunk_raw(sensor_key)    → live sensor read   (input, world → graph)
    put_chunk_raw(actuator_key)  → actuator command   (output, graph → world)

  The intended development order is simulation-first:
    1. Build a causal model in the graph using ref:if / ref:because /
       ref:therefore links between sensor and actuator Atoms.
    2. Seed sensor Atoms with synthetic values; run Harmonia jobs to verify
       the causal model behaves correctly in memory.
    3. Swap in the IoT backend — the same graph now drives real hardware.
       composite.py and Harmonia are unaware of the substitution.

  This means a single graph simultaneously serves as:
    - a semantic knowledge representation (ontology layer)
    - a simulation model (validation layer)
    - a real-time control loop (execution layer)

  The ref: cognitive primitives (ref_primitives.py) supply the control-flow
  vocabulary for condition evaluation: ref:if gates execution, ref:because /
  ref:therefore express causal ordering, ref:and / ref:or / ref:not compose
  conditions — all without introducing a separate control DSL.
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Any


class AkashaBackend(ABC):
    """Abstract base for Akasha physical storage backends."""

    # Prefixes that belong to the access-control dimension (chunk_access table).
    _ACCESS_PREFIXES: tuple = ("scope:", "owner:", "view:")

    # ── Atom CRUD ──────────────────────────────────────────────────────────────

    @abstractmethod
    def put_chunk_raw(self, key: str, content: Optional[str], meta_str: str,
                      author: str, status: str, ts: float) -> None:
        """
        Write or replace an atom.

        IoT / hardware seam: override to dispatch an actuator command keyed
        by `key`.  The content field carries the command payload; the upper
        layers (composite, Harmonia) are unaware of the substitution.
        See module docstring for the simulation-first development order.
        """

    @abstractmethod
    def update_chunk_status(self, key: str, status: str,
                            content: Optional[str] = None) -> None:
        """Update the status (and optionally content) of an existing atom."""

    @abstractmethod
    def get_chunk_raw(self, key: str) -> Optional[dict]:
        """
        Return raw atom dict {content, meta, status, author} or None.

        IoT / hardware seam: override to perform a live sensor read keyed by
        `key`.  Return the measurement in the `content` field using the same
        dict shape as SQLiteBackend — callers remain backend-agnostic.
        See module docstring for the simulation-first development order.
        """

    @abstractmethod
    def drop_chunk(self, key: str) -> None:
        """Delete an atom and all its aliases, links, collections, and access entries."""

    @abstractmethod
    def update_meta(self, key: str, meta_dict: dict) -> None:
        """Replace the atom's meta JSON with meta_dict."""

    # ── Access Control ─────────────────────────────────────────────────────────

    @abstractmethod
    def put_chunk_access(self, key: str, scopes: List[str]) -> None:
        """Register access-control scopes (scope:/owner:/view:) for an atom."""

    @abstractmethod
    def remove_chunk_access(self, key: str, scope: Optional[str] = None) -> None:
        """Remove one specific access scope, or all scopes for a key."""

    @abstractmethod
    def get_chunk_access_scopes(self, key: str) -> List[str]:
        """Return all access scopes assigned to this atom."""

    @abstractmethod
    def check_chunk_access_any(self, key: str, allowed_scopes: List[str]) -> bool:
        """True if the atom has at least one scope in allowed_scopes."""

    # ── Aliases ────────────────────────────────────────────────────────────────

    @abstractmethod
    def put_alias(self, key: str, alias: str) -> Optional[str]:
        """Register alias → key mapping. Returns alias on success, None on failure."""

    @abstractmethod
    def log_alias_collision(self, alias: str, old_key: str, new_key: str,
                            event: str = "overwrite") -> None:
        """Record an alias rebinding for later review."""

    @abstractmethod
    def get_alias_collision_log(self, since: float = 0.0, limit: int = 200,
                                unresolved_only: bool = False) -> list:
        """Return collision records newer than `since`, newest first."""

    @abstractmethod
    def resolve_alias_collision(self, alias: str) -> int:
        """Mark all unresolved collisions for this alias as resolved. Returns count updated."""

    @abstractmethod
    def delete_alias(self, alias: str) -> None:
        """Remove an alias binding.  The atom itself is NOT deleted.
        If the alias does not exist this is a no-op (idempotent).

        Migration note: in KV stores, simply delete the alias → key entry.
        In DynamoDB / Firestore, delete the alias record directly.
        """

    @abstractmethod
    def get_key_by_alias(self, alias: str) -> Optional[str]:
        """Resolve an alias to its atom key (case-insensitive, compound-normalised)."""

    @abstractmethod
    def get_aliases_by_key(self, key: str) -> List[str]:
        """Return all aliases registered for a key."""

    @abstractmethod
    def get_aliases_by_pattern(self, pattern: str) -> List[dict]:
        """Return [{alias, key}] for aliases matching a wildcard pattern.

        Contract (backend-agnostic):
          '%'  matches any sequence of characters (including empty)
          '_'  matches exactly one character
          Matching must be case-insensitive for the full Unicode range.

        SQLite note: the current implementation uses LOWER(alias) LIKE LOWER(?).
        LOWER() is ASCII-only in SQLite by default — Unicode letters above U+007F are
        NOT case-folded. This is acceptable while aliases are restricted to ASCII
        namespaced identifiers (e.g. "word:icarus"). If non-ASCII aliases are introduced,
        either compile SQLite with ICU or add a custom collation before that migration.

        Non-SQL backend migration guide:
          The caller passes user-typed patterns like "word:%" or "emo:_oy" to drive
          explore and al.find. The backend must supply equivalent prefix/substring/
          single-char matching. Typical approaches by storage type:
            KV store   — scan all alias keys; filter with fnmatch or re.
            DynamoDB   — use a begins_with KeyConditionExpression for prefix patterns
                         ("%"-only at the right end); fall back to a full scan for
                         interior "%" or "_" wildcards.
            Firestore  — range query [pattern_prefix, pattern_prefix + '￿'] for
                         simple prefix; full collection scan for general wildcards.
            Hardware   — if the alias index lives in on-chip SRAM, implement as a
                         linear scan over the alias table during boot; cache results
                         in a trie for runtime use.
          Whatever the mechanism, the return contract must be identical:
          a list of {"alias": str, "key": str} dicts, unordered.
        """

    @abstractmethod
    def get_distinct_collection_names(self, prefix: str = None) -> List[str]:
        """Return sorted list of all distinct collection names in this store.

        prefix: optional SQL LIKE prefix pattern (e.g. 'dont:%') to filter.
        Returns every collection name that exists in the collections table,
        regardless of whether it has a corresponding collection_def record.

        Migration note: non-SQL backends must maintain a separate name index
        (e.g. a Redis SET of known collection names, or a secondary index in
        DynamoDB) since the collections data structure is typically keyed by
        (name, member_key), not by name alone.
        """

    # ── Links ──────────────────────────────────────────────────────────────────

    @abstractmethod
    def remove_link_raw(self, src: str, dst: str, rel: str) -> None:
        """Delete a directed link."""

    @abstractmethod
    def put_link_raw(self, src: str, dst: str, rel: str, w: float = 1.0,
                     d: str = "forward", t: str = "atom", author: str = "system",
                     status: str = "verified", ts: float = 0.0) -> None:
        """Write or replace a directed link."""

    @abstractmethod
    def get_adjacent_links(self, src: str,
                           rel_pattern: Optional[str] = None) -> List[dict]:
        """Return outgoing link dicts {dst, rel, w, dir, type} from src."""

    @abstractmethod
    def get_incoming_links(self, dst: str,
                           rel_pattern: Optional[str] = None) -> List[dict]:
        """Return incoming link dicts {src, rel, w, dir, type} to dst."""

    # ── Collections ───────────────────────────────────────────────────────────

    @abstractmethod
    def get_collection_members_scoped(self, collection_name: str,
                                      allowed_scopes: List[str]) -> List[str]:
        """Members of collection_name that are visible within allowed_scopes."""

    @abstractmethod
    def get_collection_members_locale_ordered(
        self, collection_name: str, allowed_scopes: List[str],
        locale_codes: List[str],
    ) -> List[str]:
        """Permission-filtered, locale-filtered and ordered collection members."""

    @abstractmethod
    def add_to_collection(self, name: str, key: str) -> None:
        """Add key to the named collection."""

    @abstractmethod
    def remove_from_collection(self, name: str, key: str) -> None:
        """Remove key from the named collection."""

    @abstractmethod
    def get_collection_members(self, name: str) -> List[str]:
        """Return all keys in the named collection (no access filter)."""

    @abstractmethod
    def get_collections_for_key(self, key: str) -> List[str]:
        """Return all collection names an atom belongs to."""

    @abstractmethod
    def get_keys_in_any_collection(self, names: List[str]) -> List[str]:
        """Scope-union: keys belonging to at least one of the named collections."""

    @abstractmethod
    def get_keys_in_all_collections(self, names: List[str]) -> List[str]:
        """Scope-intersection: keys belonging to all named collections simultaneously."""

    @abstractmethod
    def clear_collection(self, name: str) -> None:
        """Remove all keys from the named collection."""

    # ── Collection Definitions ────────────────────────────────────────────────

    @abstractmethod
    def upsert_collection_def(self, name: str, meta: dict) -> None:
        """Write or replace collection definition metadata."""

    @abstractmethod
    def get_collection_def(self, name: str) -> Optional[dict]:
        """Return collection definition metadata dict, or None."""

    @abstractmethod
    def merge_collection_def_meta(self, name: str, updates: dict) -> None:
        """Merge updates into the collection's metadata dict (upsert)."""

    @abstractmethod
    def list_collection_defs(self, prefix: str = None) -> List[dict]:
        """Return [{name, meta}] for all collection definitions."""

    # ── Deferred Derivation Queue ─────────────────────────────────────────────

    @abstractmethod
    def enqueue_derivation(self, key: str, alias: str) -> None:
        """Enqueue collection derivation for an alias."""

    @abstractmethod
    def drain_derivations(self) -> int:
        """Process all pending derivations. Returns count processed."""

    # ── Pending Links (DTN) ────────────────────────────────────────────────────

    @abstractmethod
    def enqueue_pending_link(self, src: str, dst: str, rel: str,
                             author: str, ts: float) -> None:
        """
        Store a link for deferred delivery.
        DTN: maps to SQS/PubSub message in a distributed backend.
        """

    @abstractmethod
    def get_pending_links(self) -> List[dict]:
        """Return all pending links."""

    @abstractmethod
    def delete_pending_link(self, pid: int) -> None:
        """Acknowledge (delete) a delivered pending link."""

    # ── Vault (Nucleus / Config) ───────────────────────────────────────────────

    @abstractmethod
    def vault_store(self, cat: str, ident: str, data: Any) -> None:
        """Persist a JSON-serialisable value under (category, identifier)."""

    @abstractmethod
    def vault_retrieve(self, cat: str, ident: str) -> Optional[Any]:
        """Retrieve a value by (category, identifier), or None."""

    @abstractmethod
    def vault_scan(self, cat: str, prefix: str = None) -> List[tuple]:
        """Return all (identifier, data) pairs for a category, optionally prefix-filtered."""

    @abstractmethod
    def vault_delete(self, cat: str, ident: str) -> None:
        """Remove a single vault entry."""

    # ── Streaming & Export ─────────────────────────────────────────────────────

    @abstractmethod
    def fetch_stream(self, limit: int = 10) -> List[dict]:
        """Return the most recent `limit` atoms, newest first."""

    @abstractmethod
    def get_all_chunks(self) -> List[dict]:
        """Return all atoms (for export/backup)."""

    @abstractmethod
    def get_all_links(self, rel_filter: Optional[str] = None,
                      limit: int = 5000) -> List[dict]:
        """Return all links, optionally filtered by relation type."""

    @abstractmethod
    def get_all_keys(self) -> List[str]:
        """Return all atom keys."""

    @abstractmethod
    def get_recent_atom_hashes(self, since: float) -> List[str]:
        """Return keys of atoms created after `since` (epoch float)."""

    @abstractmethod
    def get_recent_links(self, since: float) -> List[dict]:
        """Return links updated after `since` (epoch float)."""

    @abstractmethod
    def get_namespace_counts(self) -> List[dict]:
        """Return [{ns, count}] namespace statistics, sorted by count desc."""

    @abstractmethod
    def fetch_by_meta_field(self, field: str, value: str, author: str = None,
                            limit: int = 200) -> List[dict]:
        """Return atoms where meta[field] == value."""

    @abstractmethod
    def get_keys_by_scope(self, scope: str) -> List[str]:
        """Return all atom keys that carry the given access scope.

        Used by onto.scope.drop to find atoms to delete.
        Implementations must query chunk_access directly — do NOT iterate
        get_all_keys() + check_chunk_access_any(); that is O(n) round-trips.
        """
