"""
Semantic Operations Engine (Composite Layer).
Acts as the global memory mesh interface (Context-Preserving Routing).
Strictly decoupled from raw persistence (SQLite), rendering it fully
compatible with distributed environments (S3, DynamoDB, Lambda, Edge Caching).

[MULTIDIMENSIONAL SCOPE INTEGRATION]
Enforces IAM (Identity & Access Management) directly at the graph level.
Read/Explore operations now strictly require 'allowed_scopes' to filter
out inaccessible memories using hardware-accelerated Set operations.

SCOPE DIMENSION TAXONOMY
========================
Scopes passed around the system carry values from three distinct dimensions
that must NEVER be conflated at the SQL layer:

  Dimension 1 — Permission (access control, used in SQL WHERE):
    scope:sys:*   owner:user_X   view:user_X   view:group_G
    scope:group_G view:public    view:admin_override

  Dimension 2 — Capability flags (authorize() checks only, NOT SQL):
    role:librarian   role:superuser   write:group_G   manage:group_G

  Dimension 3 — Locale preference (display filter only, NOT SQL):
    lang:en   lang:ja   ...

_perm_scopes() strips Dim-2 and Dim-3 entries before any SQL query so
that capability flags and locale markers never contaminate security logic.

[DUAL-PRIVILEGE MODEL: SUPERUSER vs. LIBRARIAN]
Enforces a strict separation of duties (SoD) similar to UNIX/Linux:
1. Superuser ('role:superuser' / 'scope:sys:admin'): Controls destructive,
   low-level infrastructure operations like physical deletion (drop_chunk).
   They cannot read private user scopes arbitrarily to preserve absolute privacy.
2. Librarian ('role:librarian'): Controls cognitive metadata, ontology structuring,
   and scope reallocations (reassign_scopes). They cannot execute destructive
   infrastructure actions.

[COGNITIVE METABOLISM & HARMONIA ASYNC TRIGGER]
Integrates an asynchronous event-listener bridge. Every physical commit automatically
triggers a background cognitive metabolism event (Weaving, NLP slicing, thesaurus bridging)
orchestrated non-blockingly by Harmonia, complete with recursive ingestion guards.
"""

import re
import json
import hashlib
import time
import os
import uuid
import importlib.util
import logging
from typing import List, Dict, Any, Optional, Callable, Set
from lib.akasha.core import AkashaCore
from lib.akasha.jcl.workspace_context import active as _workspace_active
from lib.akasha.jcl.workspace_context import guard as _workspace_guard

_onto_logger = logging.getLogger("Akasha.Ontology")

# ---------------------------------------------------------------------------
# Scope dimension filter
# ---------------------------------------------------------------------------

# Access-control scope prefixes → stored in chunk_access, never in collections.
# Capability flags (role:, write:, manage:) and locale markers (lang:) must
# never reach SQL permission queries.
_PERM_PREFIXES: tuple = ("scope:", "owner:", "view:")

def _perm_scopes(scopes: List[str]) -> List[str]:
    """Return only Dimension-1 (access-control) entries from a mixed scope list."""
    return [s for s in scopes if s.startswith(_PERM_PREFIXES)]

def _is_access_scope(s: str) -> bool:
    """True for access-control scopes (→ chunk_access table)."""
    return s.startswith(_PERM_PREFIXES)

# ---------------------------------------------------------------------------
# Semantic traversal constants (used by associate / AssociativeThread)
# ---------------------------------------------------------------------------

# Namespaces eligible for association traversal
_ASSOC_NAMESPACES = (
    "calc:", "emo:", "word:", "chrono:", "polti:", "story:",
    "sys:is_a", "sys:antonym", "sys:causes", "sys:associated_with",
    "sys:requires", "sys:similar_to", "sys:part_of",
)

# Internal structural namespaces excluded from association traversal
_EXCLUDED_PREFIXES = ("sys:", "@")

# Bare-word relations that map to a specific semantic namespace.
# All other bare words default to calc: (general conceptual vocabulary).
# This table is used at both write-time (new links) and read-time
# (backward-compat with pre-namespace ontology data already in the DB).
_BARE_REL_REMAP: Dict[str, str] = {
    # Semantic opposition / similarity
    "antonym":          "sys:antonym",
    "synonym":          "sys:synonym",
    "opposite":         "sys:antonym",
    "similar_to":       "sys:similar_to",
    # Emotional
    "evoked_by":        "emo:evoked_by",
    "resonates_with":   "emo:resonates_with",
    "goal_of":          "emo:goal_of",
    # Story / narrative
    "authored_by":      "story:authored_by",
    "addressed_to":     "story:addressed_to",
    "addresses":        "story:addresses",
    "describes":        "story:describes",
    "features":         "story:features",
    "involves":         "story:involves",
    "references":       "story:references",
    "embodies":         "story:embodies",
    "illustrates":      "story:illustrates",
    "starts_with":      "story:starts_with",
    "parallels":        "story:parallels",
    "shares_archetype_with": "story:shares_archetype_with",
    "exemplified_by":   "story:exemplified_by",
    "demonstrated_by":  "story:demonstrated_by",
    "synthesizes":      "story:synthesizes",
    "underlies":        "story:underlies",
    "foundational_to":  "story:foundational_to",
    # Default for all other bare words → calc: (general conceptual)
}

# Relations that encode "src belongs to the category/container named by dst".
# When a link with one of these rels is written, src is automatically added
# to a collection named after dst's primary alias.  This makes set membership
# a first-class index built in parallel with the graph edge, so exploration
# can use SQL set operations instead of BFS traversal.
#
#   sys:is_a   — "apple is a fruit"    → apple ∈ collection "fruit"
#   sys:part_of — "wheel is part of car" → wheel ∈ collection "car"
#
# sys:member_of is intentionally excluded: add_to_set() is the canonical
# entry point for user-facing set membership and handles proto-word creation.
_AUTO_COLLECTION_RELS: frozenset = frozenset({"sys:is_a", "sys:part_of"})

# Axis → matched rel prefixes (spec §5)
_AXIS_PREFIXES: Dict[str, List[str]] = {
    "emotion":   ["emo:"],
    "color":     ["word:color:", "calc:color"],
    "sense":     ["word:sense:", "calc:sense"],
    "time":      ["chrono:", "calc:time"],
    "context":   ["calc:context", "calc:associated_with"],
    "story":     ["polti:", "story:"],
    "structure": ["sys:is_a", "sys:antonym", "sys:causes", "sys:associated_with", "sys:requires"],
}

class AkashaEngine:
    def __init__(self, db_path: str, is_volatile: bool = False):
        self.core = AkashaCore(db_path, is_volatile)
        self.rw = None
        self.tensor = None
        self._fault_handler: Optional[Callable[[str], Optional[str]]] = None
        self._virtual_handler: Optional[Callable[[str, str], Optional[str]]] = None
        self._transforms: Dict[str, Callable[[str, dict], tuple[str, dict]]] = {}
        
        # Harmonia Orchestration Event Listener Bridge
        self._commit_listener: Optional[Callable[[str, str, Optional[dict], List[str]], None]] = None

    # --- Engine Attachments & Pluggables ---
    def attach_replicaware(self, rw_module):
        self.rw = rw_module

    def attach_tensor_engine(self, tensor_module):
        self.tensor = tensor_module

    def attach_nucleus(self, nucleus):
        """Attach nucleus engine for universal atom dual-write (proto-words)."""
        self._nucleus = nucleus
        
    def register_fault_handler(self, handler: Callable[[str], Optional[str]]): 
        self._fault_handler = handler
        
    def register_virtual_handler(self, handler: Callable[[str, str], Optional[str]]): 
        self._virtual_handler = handler
        
    def register_transform(self, name: str, func: Callable[[str, dict], tuple[str, dict]]): 
        self._transforms[name] = func

    def register_commit_listener(self, listener: Callable[[str, str, Optional[dict], List[str]], None]):
        """Registers the Harmonia background task-broker listener for asynchronous weaving."""
        self._commit_listener = listener

    def load_transform_plugins(self, plugins_dir: str = None):
        """Loads pure stateless mathematical transformations."""
        if plugins_dir is None:
            lib_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            plugins_dir = os.path.join(lib_dir, "transforms")
        if not os.path.exists(plugins_dir): return
        for filename in os.listdir(plugins_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                filepath = os.path.join(plugins_dir, filename)
                module_name = filename[:-3]
                try:
                    spec = importlib.util.spec_from_file_location(module_name, filepath)
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        if hasattr(module, "TRANSFORM_NAME") and hasattr(module, "transform"):
                            self.register_transform(module.TRANSFORM_NAME, module.transform)
                except Exception as e: 
                    print(f"[Composite] [!] Error loading transform plugin {filename}: {e}")

    # --- Core Write Operations (With Multidimensional Scopes) ---
    def commit(self, content: str, meta: dict = None, author: str = "system", 
               status: str = "verified", context_links: List[Dict] = None, 
               scopes: List[str] = None) -> Dict[str, str]:
        """Commits an atom to the graph and assigns it to multidimensional scope sets."""
        # Single-route guard (ENFORCE=True): a memory write MUST run under a Harmonia
        # workspace or an explicit system_context exemption, else this raises. (During
        # the historical rollout the guard ran in observe mode and only recorded
        # unguarded writes for a coverage map; it now rejects them.)
        _workspace_guard(author)
        key = hashlib.sha256(content.encode('utf-8')).hexdigest() if content else uuid.uuid4().hex
        meta_str = json.dumps(meta, ensure_ascii=False) if meta else "{}"
        
        # 1. Physical Write
        self.core.put_chunk_raw(key, content, meta_str, author, status, time.time())
        self._weave_pending_links()
        
        # 2. Scope Assignment — split by dimension:
        #    Access-control scopes (scope:/owner:/view:) → chunk_access table
        #    Computational scopes (leaf:/ns:/lang:/custom) → collections table
        if scopes:
            access_scopes = [s for s in scopes if _is_access_scope(s)]
            calc_scopes   = [s for s in scopes if not _is_access_scope(s)]
            if access_scopes:
                self.core.put_chunk_access(key, access_scopes)
            for s in calc_scopes:
                self.core.add_to_collection(s, key)

        # 3. Context Links Processing
        if context_links:
            for link in context_links:
                dst = link.get("dst")
                rel = link.get("rel", "sys:associated_with")
                w = float(link.get("w", 1.0))
                if dst:
                    dst_key = self.core.get_key_by_alias(dst) or dst
                    self.put_link(src=key, dst=dst_key, rel=rel, w=w, author=author, status="verified")
                    
        # 4. Distributed/Actuator Hooks
        if self.rw and self.rw.is_actuator(key): 
            self.rw.trigger_actuator(key, content)

        # 5. Cognitive Metabolism Async Trigger
        if self._commit_listener:
            role = meta.get("role") if meta else None
            is_primitive = role in [
                "token", "annotation", "meta:title", "meta:author", "meta:isbn"
            ] or (meta and meta.get("type") == "primitive:chunk")

            if not is_primitive:
                self._commit_listener(key, content, meta, scopes or [])

        # 6. Workspace tracking — if a tracked Harmonia workspace is active on this
        # thread and this is the tracking engine, record the key so the unit is
        # reversible (rollback drops it; commit releases it). Untracked → no-op
        # (one thread-local read). See jcl/workspace_context.
        _tx, _eng = _workspace_active()
        if _tx and _eng is self:
            self.core.add_to_collection(_tx, key)

        return {"key": key, "status": "committed"}

    def put_chunk(self, content: str, meta: dict = None, author: str = "system", 
                  status: str = "verified", context_links: List[Dict] = None, 
                  scopes: List[str] = None) -> str:
        return self.commit(content, meta, author, status, context_links, scopes)["key"]

    def put_virtual_node(self, device_uri: str, author: str = "system") -> str:
        key = hashlib.sha256(device_uri.encode('utf-8')).hexdigest()
        self.core.put_chunk_raw(key, device_uri, "{}", author, "virtual", time.time())
        return key

    # --- Security-Aware Read Operations ---
    def check_access(self, key: str, allowed_scopes: List[str]) -> bool:
        """
        Ultra-fast O(1)~O(N) intersection to verify if the user's allowed_scopes
        overlap with the scopes the memory node belongs to.

        [LIBRARIAN PRIVILEGE]
        If the client session possesses 'role:librarian', this check immediately 
        bypasses the scope boundary, allowing perfect trans-galactic visibility 
        for structuring ontologies.
        
        [SUPERUSER LIMITATION]
        The 'role:superuser' does NOT bypass read restrictions here. This ensures
        absolute privacy of users' private thinking (Soma contents) even from 
        system administrators.
        """
        if not allowed_scopes:
            return False  # Strict Deny

        # Capability-flag bypasses — checked before dimension filtering
        # (these are Dim-2 markers, intentionally not in the SQL path)
        if "scope:sys:root" in allowed_scopes:
            return True
        if "role:librarian" in allowed_scopes:
            return True  # Librarian reads all for cataloging; superuser does NOT bypass

        # Strip Dim-2 (capability) and Dim-3 (locale) before the access check.
        # Access scopes live in chunk_access, not collections.
        perm = _perm_scopes(allowed_scopes)
        if not perm:
            return False

        if self.core.check_chunk_access_any(key, perm):
            return True
        # Nucleus fallback for atoms that live only in the shared nucleus DB.
        # Two cases:
        #   1. scope:sys:universal — readable by every authenticated session.
        #      Universal atoms use this scope; it is never in a user's perm list,
        #      so we must check for it explicitly rather than using `perm`.
        #   2. User-specific scopes stored in nucleus (e.g. admin's private atoms).
        nucleus = getattr(self, '_nucleus', None)
        if nucleus:
            if nucleus.core.check_chunk_access_any(key, ["scope:sys:universal"]):
                return True
            return nucleus.core.check_chunk_access_any(key, perm)
        return False

    def get_scoped_chunk(self, key: str, allowed_scopes: List[str]) -> Optional[str]:
        """
        Retrieves a chunk ONLY if the client holds the appropriate scope.
        Handles distributed edge-misses (evicted) and virtual nodes.
        """
        if not self.check_access(key, allowed_scopes):
            return None # Access Denied or Invisible
            
        return self.get_chunk(key)

    def get_chunk(self, key: str) -> Optional[str]:
        """Raw retrieval (Internal use or System-level operations)."""
        if self.rw and self.rw.is_sensor(key): return self.rw.read_sensor(key)

        row = self.core.get_chunk_raw(key)
        if not row:
            nucleus = getattr(self, '_nucleus', None)
            if nucleus:
                row = nucleus.core.get_chunk_raw(key)
            if not row:
                if self.rw:
                    remote_content = self.rw.fetch_remote_memory(key)
                    if remote_content:
                        self.put_chunk(remote_content)
                        return remote_content
                return None
            
        content, status = row["content"], row["status"]
        
        if status == "evicted":
            if self._fault_handler:
                fetched = self._fault_handler(key)
                if fetched:
                    self.core.update_chunk_status(key, "verified", fetched)
                    return fetched
            return "[Evicted Node: Content is offloaded]"
            
        if status == "virtual":
            if self._virtual_handler: return self._virtual_handler(key, content)
            return f"[Virtual Node: Device '{content}' disconnected]"
            
        return content

    def evict_chunk(self, key: str):
        """Marks a chunk to free up local edge memory."""
        self.core.update_chunk_status(key, "evicted", None)

    def close(self) -> None:
        """Checkpoint WAL and shut down this engine's write queue / connections.
        Called when a per-slot guest cortex is wiped, or on graceful shutdown."""
        try:
            self.core.close()
        except Exception:
            pass

    # =========================================================================
    # 🛠️ DESTRUCTIVE SUPERUSER PRIVILEGES (Linux root-level operations)
    # =========================================================================
    def drop_chunk(self, key: str, requester_scopes: List[str] = None) -> Dict[str, str]:
        """
        [SUPERUSER EXCLUSIVE]
        Allows raw physical destruction of an Atom (Somatic Cleanup).
        Only executable by clients holding 'role:superuser' or 'scope:sys:admin'.
        Librarians cannot execute this.
        """
        if not requester_scopes or ("role:superuser" not in requester_scopes and "scope:sys:admin" not in requester_scopes):
            return {"error": "Security Rejection: Only superusers can physically drop chunks."}
            
        self.core.drop_chunk(key)
        return {"status": "dropped", "key": key}

    # =========================================================================
    # 📚 LIBRARIAN OPERATION: SCOPE REALLOCATION MECHANIC
    # =========================================================================
    def reassign_scopes(self, key: str, new_scopes: List[str], requester_scopes: List[str]) -> bool:
        """
        [LIBRARIAN EXCLUSIVE]
        Allows a system administrator or ontology builder possessing 'role:librarian' 
        to dynamically strip away existing scopes of an Atom and assign new ones.
        Used to catalog and publish raw private nodes into 'scope:sys:universal'.
        Superusers cannot execute this unless they also hold the 'role:librarian' role.
        """
        if not requester_scopes or "role:librarian" not in requester_scopes:
            return False

        new_access = [s for s in new_scopes if _is_access_scope(s)]
        new_calc   = [s for s in new_scopes if not _is_access_scope(s)]

        # Replace access-control scopes in chunk_access
        if new_access:
            self.core.remove_chunk_access(key)      # remove all old access scopes
            self.core.put_chunk_access(key, new_access)

        # Replace computational scopes in collections
        if new_calc is not None:
            old_calc = self.core.get_collections_for_key(key)
            for s in old_calc:
                self.core.remove_from_collection(s, key)
            for s in new_calc:
                self.core.add_to_collection(s, key)

        return True

    # --- Links & Graph Topology ---
    def remove_link(self, src: str, dst: str, rel: str) -> None:
        self.core.remove_link_raw(src, dst, rel)

    def delete_alias(self, alias: str) -> None:
        self.core.delete_alias(alias)

    def put_link(self, src: str, dst: str, rel: str = "sys:associated_with",
                 w: float = 1.0, author: str = "system", status: str = "verified"):
        _workspace_guard(author)
        self.core.put_link_raw(src, dst, rel, w=w, author=author, status=status, ts=time.time())
        if rel in _AUTO_COLLECTION_RELS:
            nucleus = getattr(self, '_nucleus', None)
            dst_aliases = self.core.get_aliases_by_key(dst)
            if not dst_aliases and nucleus:
                dst_aliases = nucleus.core.get_aliases_by_key(dst)
            if dst_aliases:
                self.core.add_to_collection(dst_aliases[0], src)

    def reinforce_link(self, src: str, dst: str, rel: str, delta_w: float = 0.1, 
                       max_w: float = 1.0, min_w: float = 0.0, 
                       author: str = "system.dream") -> float:
        existing_links = self.core.get_adjacent_links(src, rel_pattern=rel)
        current_w = 1.0
        for link in existing_links:
            if link["dst"] == dst:
                current_w = float(link.get("w", 1.0))
                break
        new_w = max(min_w, min(max_w, current_w + delta_w))
        self.put_link(src, dst, rel, w=new_w, author=author)
        return new_w

    def enqueue_pending_link(self, src: str, dst: str, rel: str, author: str, ts: float): 
        self.core.enqueue_pending_link(src, dst, rel, author, ts)

    def _weave_pending_links(self):
        pendings = self.core.get_pending_links()
        for p in pendings:
            src_ok = self.core.get_chunk_raw(p["src"]) or self.core.get_key_by_alias(p["src"])
            dst_ok = self.core.get_chunk_raw(p["dst"]) or self.core.get_key_by_alias(p["dst"])
            if src_ok and dst_ok:
                self.core.put_link_raw(p["src"], p["dst"], p["rel"], w=1.0, author=p["author"], status="pending", ts=p["timestamp"])
                self.core.delete_pending_link(p["id"])

    # --- Metadata & Aliases ---
    def set_meta(self, key: str, meta_key: str, value: Any) -> Dict[str, str]:
        row = self.core.get_chunk_raw(key)
        if not row: return {"error": "Chunk not found"}
        meta = json.loads(row["meta"]) if row["meta"] else {}
        meta[meta_key] = value
        self.core.update_meta(key, meta)
        return {"status": "meta_updated", "key": key}

    def add_meta(self, key: str, meta_key: str, value: Any) -> Dict[str, str]:
        row = self.core.get_chunk_raw(key)
        if not row: return {"error": "Chunk not found"}
        meta = json.loads(row["meta"]) if row["meta"] else {}
        if meta_key not in meta: meta[meta_key] = []
        elif not isinstance(meta[meta_key], list): meta[meta_key] = [meta[meta_key]]
        if value not in meta[meta_key]: meta[meta_key].append(value)
        self.core.update_meta(key, meta)
        return {"status": "meta_added", "key": key}
        
    def get_meta(self, key: str) -> dict:
        row = self.core.get_chunk_raw(key)
        if not row:
            nucleus = getattr(self, '_nucleus', None)
            if nucleus:
                row = nucleus.core.get_chunk_raw(key)
        if not row or not row["meta"]: return {}
        return json.loads(row["meta"])

    def verify_chunk(self, key: str, reviewer: str = "admin") -> bool:
        row = self.core.get_chunk_raw(key)
        if not row: return False
        if row["status"] == "pending": self.core.update_chunk_status(key, "verified", row["content"])
        meta = json.loads(row["meta"]) if row["meta"] else {}
        meta["verified"] = True
        self.core.update_meta(key, meta)
        return True

    def set_alias(self, key: str, alias: str, force: bool = False) -> Dict[str, str]:
        """
        Register an alias for an atom.

        DESIGN PRINCIPLE — first-wins for all aliases:
          Every alias (bare or qualified) follows the same first-wins rule.
          The first registrant holds the alias permanently. Later atoms
          claiming the same alias receive a 'specializes' link instead of
          displacing the incumbent. This makes authoring forgiving: humans
          and LLMs can define freely without coordination overhead.

          Bare aliases (no ':') → proto-word declaration; first-wins always.
          Qualified aliases (':') → first-wins by default; also ensure their
            bare terminal segment has a proto-word atom and create a
            'specializes' link from this atom to that proto-word.

          force=True bypasses first-wins (used by the explicit 'alias'
          management command when a librarian intentionally rebinds).
          Forced rebinds are logged to alias_collision_log for onto.report.

        INDEX PATH (async via Harmonia/JCL):
          Qualified aliases enqueue full collection derivation (leaf:, ns:, lang:).
          JCL worker drains this queue; _migrate_tables drains at startup.
        """
        if ":" in alias:
            # ── Qualified alias ──────────────────────────────────────────
            bare = alias.rsplit(":", 1)[-1]
            if bare:
                proto_key = self._ensure_protoword(bare)
                if proto_key and proto_key != key:
                    self.core.put_link_raw(key, proto_key, "specializes",
                                           author="system", status="inferred", ts=time.time())
            _prev = self.core.get_key_by_alias(alias)
            if _prev is not None and _prev != key:
                if force:
                    # Explicit librarian rebind — log and overwrite.
                    self.core.log_alias_collision(alias, _prev, key, event="overwrite")
                    self.core.put_alias(key, alias)
                else:
                    # First-wins: later atom specializes the incumbent, no rebind.
                    _onto_logger.debug("[alias:first-wins] '%s' qual incumbent=%s new=%s→specializes",
                                       alias, _prev[:8], key[:8])
                    self.core.put_link_raw(key, _prev, "specializes",
                                           author="system", status="inferred", ts=time.time())
            else:
                self.core.put_alias(key, alias)
            self.core.enqueue_derivation(key, alias)
        else:
            # ── Bare alias ───────────────────────────────────────────────
            existing = self.core.get_key_by_alias(alias)
            if existing is None:
                self.core.put_alias(key, alias)
                _SYS_PREFIXES = ("leaf:", "ns:", "lang:", "scope:", "sys:")
                if not any(alias.startswith(p) for p in _SYS_PREFIXES):
                    self._ensure_protoword(alias)
            elif existing != key:
                _onto_logger.debug("[alias:first-wins] '%s' proto=%s new=%s→specializes",
                                   alias, existing[:8], key[:8])
                self.core.put_link_raw(key, existing, "specializes",
                                       author="system", status="inferred", ts=time.time())

        # Compound-word fast-path: "rain coat" ↔ "raincoat"
        compact = re.sub(r'[\s\-]+', '', alias).lower()
        if compact and compact != alias.lower() and not self.core.get_key_by_alias(compact):
            self.core.put_alias(key, compact)
        return {"alias": alias, "key": key}

    def _ensure_protoword(self, bare: str) -> Optional[str]:
        """
        Ensure a proto-word atom exists for the given bare word. Returns its key.

        If a bare alias is already registered that atom IS the proto-word.
        Otherwise a minimal lexical atom is created: content = the bare word
        itself (scope:sys:universal), keyed by sha256(bare). This is a purely
        structural declaration — semantic content arrives later through qualified
        atoms and their specializes links.
        """
        nucleus = getattr(self, '_nucleus', None)

        # Check local first (bare alias registered by a user in this cell)
        existing = self.core.get_key_by_alias(bare)
        if existing:
            return existing
        # Then check nucleus (proto-word from another cell or a previous boot)
        if nucleus:
            existing = nucleus.core.get_key_by_alias(bare)
            if existing:
                return existing

        key = hashlib.sha256(bare.encode("utf-8")).hexdigest()
        bare_lower = bare.lower()

        if nucleus:
            # Proto-words are universal — store in nucleus only (no local duplication).
            # The specializes link created by the caller stays local; the target atom lives
            # in the shared nucleus so every cell can read it via the nucleus fallback.
            ncore = nucleus.core
            ncore.put_chunk_raw(key, bare, "{}", "system", "verified", time.time())
            ncore.put_chunk_access(key, ["scope:sys:universal"])
            ncore.put_alias(key, bare)
            # Also register lowercase variant (e.g. ISO3 "USA" → also alias "usa")
            # so `look usa` resolves without requiring exact-case input.
            if bare_lower != bare and not ncore.get_key_by_alias(bare_lower):
                ncore.put_alias(key, bare_lower)
        else:
            # No nucleus attached — fall back to local storage.
            self.core.put_chunk_raw(key, bare, "{}", "system", "verified", time.time())
            self.core.put_chunk_access(key, ["scope:sys:universal"])
            self.core.put_alias(key, bare)
            if bare_lower != bare and not self.core.get_key_by_alias(bare_lower):
                self.core.put_alias(key, bare_lower)

        # Cross-DB bundle tracking (orchestration-architecture.md E.4). If this NEW
        # proto-word was created inside a tracked conversation bundle, record it in the
        # nucleus's ws:{tx_id} set so the bundle's nucleus footprint is durable and
        # reconcilable by the boot orphan scan. Proto-words are commit-forward: shared,
        # content-addressed, and possibly referenced by already-committed bundles, so
        # rollback / the orphan scan clear the tracking set but never drop the atom.
        _txid, _ = _workspace_active()
        if _txid:
            try:
                (nucleus if nucleus else self).core.add_to_collection(_txid, key)
            except Exception:
                pass

        _onto_logger.debug("[protoword:auto] '%s' → %s (nucleus=%s)", bare, key[:8], nucleus is not None)
        return key

    def _link_instance_to_universals(self, key: str, leaf: str) -> int:
        """
        Create sys:instance_of links from a private atom to any universal atoms
        that share the same leaf name.  One-directional (private → universal) per
        the Private Instance → Universal Concept pattern in scope-dimension-model §8.

        Called after collection derivation so that leaf: membership is already in place.
        Returns the number of links created.
        """
        leaf_coll = f"leaf:{leaf}"
        count = 0
        for universal_key in self.core.get_collection_members(leaf_coll):
            if universal_key == key:
                continue
            if self.core.check_chunk_access_any(universal_key, ["scope:sys:universal"]):
                self.core.put_link_raw(
                    key, universal_key,
                    rel="sys:instance_of",
                    w=1.0, author="system.weaver", status="verified",
                    ts=time.time(),
                )
                count += 1
        return count

    def drain_derivation_queue(self) -> int:
        """
        Drain all pending collection derivations synchronously, then wire
        sys:instance_of links from each newly-indexed private atom to any
        universal atoms sharing the same leaf name.
        Called by JCLWorker on job completion and directly on demand.
        Returns the number of alias derivations processed.
        """
        # Snapshot pending work BEFORE drain so we can post-process after rows are gone
        pending = self.core.peek_pending_derivations()
        n = self.core.drain_derivations()
        seen: set = set()
        for row in pending:
            key   = row["key"]
            alias = row["alias"]
            if ":" in alias:
                leaf = alias.rsplit(":", 1)[-1]
                if leaf and (key, leaf) not in seen:
                    seen.add((key, leaf))
                    self._link_instance_to_universals(key, leaf)
        return n

    def put_alias(self, key: str, alias: str): return self.set_alias(key, alias)

    def resolve_alias(self, alias: str) -> Optional[str]:
        key = self.core.get_key_by_alias(alias)
        if not key:
            nucleus = getattr(self, '_nucleus', None)
            if nucleus:
                key = nucleus.core.get_key_by_alias(alias)
        return key

    def get_aliases_by_key(self, key: str) -> List[str]:
        aliases = self.core.get_aliases_by_key(key)
        if not aliases:
            nucleus = getattr(self, '_nucleus', None)
            if nucleus:
                aliases = nucleus.core.get_aliases_by_key(key)
        return aliases or []

    def get_aliases_by_pattern(self, pattern: str) -> List[Dict[str, str]]:
        # Pattern semantics ('%' / '_' wildcards, case-insensitive) are defined
        # in AkashaBackend.get_aliases_by_pattern and must be honoured by any
        # replacement backend. See base.py for the migration guide.
        local = self.core.get_aliases_by_pattern(pattern) or []
        if not local:
            nucleus = getattr(self, '_nucleus', None)
            if nucleus:
                local = nucleus.core.get_aliases_by_pattern(pattern) or []
        return local

    def get_all_aliases(self) -> List[Dict[str, str]]: return self.core.get_aliases_by_pattern('%')

    def get_adjacent_links(self, key: str, rel_pattern: Optional[str] = None) -> List[List[str]]:
        links = self.core.get_adjacent_links(key, rel_pattern)
        if not links:
            nucleus = getattr(self, '_nucleus', None)
            if nucleus:
                links = nucleus.core.get_adjacent_links(key, rel_pattern)
        return [[r["dst"], r["rel"]] for r in (links or [])]

    def get_incoming_links(self, key: str, rel_pattern: Optional[str] = None) -> List[List[str]]:
        links = self.core.get_incoming_links(key, rel_pattern)
        if not links:
            nucleus = getattr(self, '_nucleus', None)
            if nucleus:
                links = nucleus.core.get_incoming_links(key, rel_pattern)
        return [[r["src"], r["rel"]] for r in (links or [])]
    
    def get_magnetic_neighborhood(self, key: str, radius_threshold: float = 0.5) -> List[Dict]:
        nucleus = getattr(self, '_nucleus', None)
        out_links = self.core.get_adjacent_links(key)
        if not out_links and nucleus:
            out_links = nucleus.core.get_adjacent_links(key)
        in_links = self.core.get_incoming_links(key)
        if not in_links and nucleus:
            in_links = nucleus.core.get_incoming_links(key)
        results = []
        for link in (out_links or []):
            results.append({"key": link["dst"], "rel": link["rel"], "w": link["w"], "type": "explicit", "direction": "out"})
        for link in (in_links or []):
            results.append({"key": link["src"], "rel": link["rel"], "w": link["w"], "type": "explicit", "direction": "in"})
        return results

    # --- Sets, Morphisms & Advanced Exploration ---
    def create_set(self, name: str) -> None: pass
    # Prefixes used by auto-generated system collections — excluded from user listings.
    _SYS_COLLECTION_PREFIXES = (
        "leaf:", "ns:", "lang:", "scope:", "sys:", "temp:",
        "set:word:", "dont:", "ont:", "chunk:", "pending:",
    )

    def add_to_set(self, name: str, key: str):
        # `ws:` is RESERVED for Harmonia workspace tracking sets (ws:{tx_id}). The
        # boot orphan scan drops the members of any stray ws:* collection, so letting
        # user-facing set membership create one would risk deleting real atoms on the
        # next restart. Internal tracking bypasses this method (it calls
        # core.add_to_collection directly), so this reservation costs it nothing.
        # `wf:` is RESERVED for named workflow definitions (jcl/workflow_vocab).
        if name.startswith("ws:") or name.startswith("wf:"):
            raise ValueError(f"Set name prefix '{name.split(':', 1)[0]}:' is reserved for internal use.")
        _SYS_PREFIXES = ("leaf:", "ns:", "lang:", "scope:", "sys:")
        if not any(name.startswith(p) for p in _SYS_PREFIXES):
            proto_key = self._ensure_protoword(name)
            if proto_key and proto_key != key:
                self.put_link(key, proto_key, "sys:member_of", author="system")
        self.core.add_to_collection(name, key)
    def remove_from_set(self, name: str, key: str): self.core.remove_from_collection(name, key)

    def list_set_names(self, exclude_prefixes: tuple = None) -> List[str]:
        """Return sorted user-defined set names (system-generated collections excluded)."""
        excl = exclude_prefixes if exclude_prefixes is not None else self._SYS_COLLECTION_PREFIXES
        names: set = {
            n for n in self.core.get_distinct_collection_names()
            if not any(n.startswith(p) for p in excl)
        }
        nucleus = getattr(self, '_nucleus', None)
        if nucleus:
            for n in nucleus.core.get_distinct_collection_names():
                if not any(n.startswith(p) for p in excl):
                    names.add(n)
        return sorted(names)
    def get_collection_members(self, name: str) -> list:
        local = self.core.get_collection_members(name) or []
        nucleus = getattr(self, '_nucleus', None)
        if nucleus:
            nuc = nucleus.core.get_collection_members(name) or []
            if nuc:
                seen = set(local)
                for k in nuc:
                    if k not in seen:
                        local = local + [k]
                        seen.add(k)
        return local
    def clear_set(self, name: str) -> Dict[str, str]: 
        self.core.clear_collection(name)
        return {"status": "set_cleared", "name": name}
        
    def list_set(self, name: str, allowed_scopes: List[str] = None, locale_codes: List[str] = None) -> List[Dict]:
        """Set members with scope + locale filtering via single SQL JOIN — no Python loops.
        Capability bypasses (role:librarian) skip both permission and locale filtering.
        Always merges nucleus members so universal vocabulary sets (stored in nucleus.db
        when atoms were written with scope=universal) are visible to every session.

        `allowed_scopes is None` = internal bypass (all members).  An EMPTY list
        takes the scoped SQL path (which matches nothing) so a scoped caller with
        no scopes sees nothing — fail-closed, never fall through to unscoped."""
        if allowed_scopes is not None and "role:librarian" not in allowed_scopes:
            if locale_codes:
                keys = self.core.get_collection_members_locale_ordered(name, allowed_scopes, locale_codes)
            else:
                keys = self.core.get_collection_members_scoped(name, allowed_scopes)
        else:
            keys = self.core.get_collection_members(name)
        # Merge nucleus members (universal atoms tracked in nucleus collections table).
        nucleus = getattr(self, '_nucleus', None)
        if nucleus:
            nuc_keys = nucleus.core.get_collection_members(name) or []
            if nuc_keys:
                seen = set(keys)
                for k in nuc_keys:
                    if k not in seen:
                        keys = keys + [k]
        return [{"key": k, "content": self.get_chunk(k)} for k in keys]

    def list_leaf(self, leaf: str, allowed_scopes: List[str] = None, locale_codes: List[str] = None) -> List[str]:
        """All atom keys whose namespaced alias has `leaf` as the right-hand part.
        Locale-ordered when locale_codes provided; librarian bypass skips all filters."""
        coll = f"leaf:{leaf}"
        if allowed_scopes is not None and "role:librarian" not in allowed_scopes:
            if locale_codes:
                keys = self.core.get_collection_members_locale_ordered(coll, allowed_scopes, locale_codes)
            else:
                keys = self.core.get_collection_members_scoped(coll, allowed_scopes)
        else:
            keys = self.core.get_collection_members(coll)
        if not keys:
            nucleus = getattr(self, '_nucleus', None)
            if nucleus:
                keys = nucleus.core.get_collection_members(coll) or []
        return keys
        
    def get_set_members(self, name: str) -> List[Dict]: return self.list_set(name)

    def set_operation(self, op: str, res_name: str, a_name: str, b_name: str) -> List[Dict]:
        a_keys = set(self.get_collection_members(a_name))
        b_keys = set(self.get_collection_members(b_name))
        if op == "union": res_keys = a_keys | b_keys
        elif op == "isect": res_keys = a_keys & b_keys
        elif op == "diff": res_keys = a_keys - b_keys
        else: res_keys = set()
        for k in res_keys: self.core.add_to_collection(res_name, k)
        return self.get_set_members(res_name)

    def set_map(self, transform_name: str, src_set: str, dst_set: str, append: bool = False, author: str = "system") -> Dict[str, Any]:
        if transform_name not in self._transforms: return {"error": f"Transform '{transform_name}' is not registered."}
        transform_func = self._transforms[transform_name]
        src_keys = self.core.get_collection_members(src_set)
        if not append: self.core.clear_collection(dst_set)
        mapped_count = 0
        for src_key in src_keys:
            try:
                content = self.get_chunk(src_key) or ""
                meta = self.get_meta(src_key)
                new_content, new_meta = transform_func(content, meta)
                if new_content:
                    dst_key = self.put_chunk(new_content, meta=new_meta, author=f"map:{transform_name}")
                    self.core.add_to_collection(dst_set, dst_key)
                    self.core.put_link_raw(src_key, dst_key, rel="sys:mapped_to", w=1.0, author=author)
                    self.core.put_link_raw(dst_key, src_key, rel="sys:mapped_from", w=1.0, author=author)
                    mapped_count += 1
            except Exception as e: print(f"[Set Morphism] Error applying '{transform_name}': {e}")
        return {"status": "success", "transform": transform_name, "processed": len(src_keys), "mapped": mapped_count, "target_set": dst_set}

    def explore(self, node_id: str, set_name: str, depth: int, rel_pattern: Optional[str] = None, allowed_scopes: List[str] = None, seed_discovery: Optional[Dict[str, str]] = None) -> List[Dict]:
        """
        Set-based semantic exploration.

        Expands outward through collection membership rather than BFS graph traversal.
        O(depth × |collections|) SQL queries — no graph scanning.

        depth=1: find all collections node_id belongs to → return their members
        depth=N: repeat outward from each newly discovered frontier
        If node_id is itself a collection name, its members seed the depth-0 frontier.

        seed_discovery: when provided ({key: via_label}), those keys form the depth-0
        frontier instead of expanding from a single node_id. Used for pattern-matched
        multi-seed exploration (e.g. exp "word:%" depth=1).

        Each returned dict includes a 'via_collection' key recording which collection
        first yielded that atom, enabling grouped display in the renderer.
        """
        nucleus = getattr(self, '_nucleus', None)

        def _collections_for(key: str) -> set:
            c = set(self.core.get_collections_for_key(key))
            if nucleus:
                c.update(nucleus.core.get_collections_for_key(key))
            return c

        def _members_with_source(names: list) -> dict:
            """Returns {key: first_collection_name} for all members of given collections."""
            result: dict = {}
            for name in names:
                for k in self.core.get_collection_members(name):
                    if k not in result:
                        result[k] = name
                if nucleus:
                    for k in nucleus.core.get_collection_members(name):
                        if k not in result:
                            result[k] = name
            return result

        if seed_discovery is not None:
            # Multi-seed mode: matched atoms are the starting frontier
            found: set = set(seed_discovery.keys())
            discovery: dict = dict(seed_discovery)
            frontier: set = set(seed_discovery.keys())
            effective_depth = depth
            discard_origin = False
        else:
            found = {node_id}
            discovery = {}
            frontier = set()
            effective_depth = depth
            discard_origin = True

            # If node_id names a collection directly, its members are the depth-0 frontier
            direct = _members_with_source([node_id])
            if direct:
                new_keys = set(direct) - found
                found |= new_keys
                frontier = new_keys
                discovery.update({k: direct[k] for k in new_keys})
                effective_depth -= 1

        for _ in range(effective_depth):
            if not frontier:
                break
            collections: set = set()
            for k in frontier:
                collections.update(_collections_for(k))
            if not collections:
                break
            members = _members_with_source(list(collections))
            new_keys = set(members) - found
            found |= new_keys
            frontier = new_keys
            discovery.update({k: members[k] for k in new_keys})

        if discard_origin:
            found.discard(node_id)

        self.core.clear_collection(set_name)
        for k in found:
            self.core.add_to_collection(set_name, k)

        rows = self.list_set(set_name, allowed_scopes)
        for row in rows:
            row['via_collection'] = discovery.get(row['key'])
        return rows

    # =========================================================================
    # 🌲 GRAPH TREE — BFS link-traversal tree (graph.tree)
    # =========================================================================

    _TREE_MAX_CHILDREN = 20
    _TREE_MAX_NODES    = 150

    def graph_tree(
        self,
        target: str,
        depth: int = 2,
        follow: str = "",
        fmt: str = "rich",
        allowed_scopes: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Build a BFS link-traversal tree rooted at an atom, set, or namespace.

        target  — atom alias/key, "set:<name>", or "ns:<prefix>"
        depth   — traversal depth (capped 1–5)
        follow  — relation-type filter; empty = all outgoing links
        fmt     — "rich" (default) | "ascii"
        """
        from lib.akasha.concepts.textview import TextViewConcept

        depth   = max(1, min(int(depth), 5))
        total   = [0]
        nucleus = getattr(self, '_nucleus', None)

        # Fail-closed visibility gate.  `allowed_scopes is None` means an explicit
        # internal bypass (no session context); an EMPTY list means "a scoped
        # caller with no scopes" and must deny everything, never allow-all.
        _enforce = allowed_scopes is not None

        def _visible(key: str) -> bool:
            return (not _enforce) or self.check_access(key, allowed_scopes)

        def _best_label(key: str) -> str:
            aliases = self.get_aliases_by_key(key)
            if aliases:
                return aliases[0]
            content = self.get_chunk(key)
            if content:
                s = content[:40]
                return s + ("…" if len(content) > 40 else "")
            return key[:20] + "…"

        def _preview(key: str) -> str:
            content = self.get_chunk(key) or ""
            s = content[:48]
            return s + ("…" if len(content) > 48 else "")

        def _build(key: str, remaining: int, via_rel: str = "") -> Optional[Dict]:
            if total[0] >= self._TREE_MAX_NODES:
                return None
            total[0] += 1
            label   = _best_label(key)
            preview = _preview(key)
            parts: List[str] = []
            if via_rel:
                parts.append(f"[{via_rel}]")
            if preview and preview != label and preview[:40] not in label:
                parts.append(preview[:40])
            sublabel = "  ".join(parts)

            if remaining <= 0:
                return TextViewConcept.node(label, sublabel)

            try:
                links = self.get_adjacent_links(key)  # [[dst, rel], ...]
            except Exception:
                links = []

            if follow:
                links = [
                    [d, r] for d, r in links
                    if r == follow or r.startswith(follow + ":")
                ]

            children: List[Dict] = []
            seen: Set[str] = set()
            for dst, rel in links[: self._TREE_MAX_CHILDREN]:
                if dst in seen:
                    continue
                seen.add(dst)
                if not _visible(dst):
                    continue
                child = _build(dst, remaining - 1, rel)
                if child is None:
                    break
                children.append(child)

            return TextViewConcept.node(label, sublabel, children or None)

        # ── target auto-detection ─────────────────────────────────────────
        if target.startswith("set:"):
            _member_rows = self.list_set(target, allowed_scopes=None)
            members = [r["key"] for r in _member_rows]
            children_list: List[Dict] = []
            for k in members[: self._TREE_MAX_CHILDREN]:
                if total[0] >= self._TREE_MAX_NODES:
                    break
                if not _visible(k):
                    continue
                node = _build(k, depth - 1)
                if node:
                    children_list.append(node)
            root_label = target
            title      = f"set  ·  {target}  ({len(members)} members)"

        elif target.startswith("ns:"):
            ns_prefix = target[3:]
            rows      = self.core.get_aliases_by_pattern(f"{ns_prefix}:%") or []
            if nucleus:
                seen_k: Set[str] = {r["key"] for r in rows}
                for r in (nucleus.core.get_aliases_by_pattern(f"{ns_prefix}:%") or []):
                    if r["key"] not in seen_k:
                        rows.append(r)
                        seen_k.add(r["key"])
            children_list = []
            visited: Set[str] = set()
            for row in rows[: self._TREE_MAX_CHILDREN]:
                k = row["key"]
                if k in visited:
                    continue
                visited.add(k)
                if total[0] >= self._TREE_MAX_NODES:
                    break
                if not _visible(k):
                    continue
                node = _build(k, depth - 1)
                if node:
                    children_list.append(node)
            root_label = target
            title      = f"ns  ·  {target}  ({len(visited)} atoms)"

        else:
            resolved  = self.resolve_alias(target) or target
            if not _visible(resolved):
                # Root atom is out of scope — reveal nothing.
                root_node = None
            else:
                root_node = _build(resolved, depth)
            if root_node:
                root_label    = root_node.get("label", target)
                children_list = root_node.get("children") or []
            else:
                root_label    = target
                children_list = []
            title = f"atom  ·  {root_label}  (depth {depth})"

        tv = TextViewConcept.tree(
            title    = title,
            root     = root_label,
            children = children_list,
        )
        tv["format"]     = fmt
        tv["node_count"] = total[0]
        return tv

    # =========================================================================
    # 🔗 ASSOCIATIVE THREAD — semantic link traversal (kernel.associate)
    # =========================================================================

    def _traverse_associations(
        self,
        focal_key: str,
        axis: Optional[str] = None,
        scope: int = 2,
        allowed_scopes: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        BFS over semantic links (calc:*, emo:*, word:*, chrono:*, polti:*, story:*).
        Structural (sys:*) and narrative (@*) links are excluded.
        Applies axis filter and IAM scope check at every hop.
        """
        # Build the prefix whitelist for this axis
        if axis and axis in _AXIS_PREFIXES:
            axis_prefixes: Optional[List[str]] = _AXIS_PREFIXES[axis]
        elif axis:
            axis_prefixes = [axis]  # custom prefix treated as literal
        else:
            axis_prefixes = None   # all semantic namespaces

        results: List[Dict[str, Any]] = []
        visited = {focal_key}
        current_layer = {focal_key}
        _nucleus = getattr(self, '_nucleus', None)

        for depth in range(1, scope + 1):
            next_layer: set = set()
            for nid in current_layer:
                raw_links = list(self.core.get_adjacent_links(nid) or [])
                if _nucleus:
                    seen_pairs = {(l["dst"], l["rel"]) for l in raw_links}
                    for l in (_nucleus.core.get_adjacent_links(nid) or []):
                        pair = (l["dst"], l["rel"])
                        if pair not in seen_pairs:
                            raw_links.append(l)
                            seen_pairs.add(pair)
                for link in raw_links:
                    dst = link["dst"]
                    rel = link["rel"]

                    # Normalize bare-word relations (no colon, no @ prefix).
                    # Pre-namespace ontology data is remapped to the proper
                    # semantic namespace at read-time for backward compatibility.
                    if ':' not in rel and not rel.startswith('@'):
                        rel = _BARE_REL_REMAP.get(rel, f"calc:{rel}")

                    if not any(rel.startswith(ns) for ns in _ASSOC_NAMESPACES):
                        continue

                    # Apply axis filter when specified
                    if axis_prefixes and not any(rel.startswith(p) for p in axis_prefixes):
                        continue

                    if dst in visited:
                        continue

                    # IAM scope check
                    if allowed_scopes and not self.check_access(dst, allowed_scopes):
                        continue

                    visited.add(dst)
                    next_layer.add(dst)

                    content = self.get_chunk(dst) or ""
                    raw     = self.core.get_chunk_raw(dst)
                    meta    = json.loads(raw["meta"]) if raw and raw.get("meta") else {}

                    if rel.startswith("emo:"):
                        atype = "emotion"
                    elif rel.startswith("calc:"):
                        atype = "concept"
                    elif rel.startswith("word:"):
                        atype = "word"
                    elif rel.startswith("sys:"):
                        atype = "structure"
                    elif ":" not in rel:
                        atype = "relation"  # bare-word, pre-namespace ontology
                    else:
                        atype = "chunk"

                    results.append({
                        "key":     dst,
                        "rel":     rel,
                        "depth":   depth,
                        "preview": content[:60],
                        "type":    atype,
                    })

            current_layer = next_layer
            if not current_layer:
                break

        return results

    def _find_resonance(
        self,
        focal_key: str,
        allowed_scopes: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Finds written chunks that share semantic tags (emo:* or calc:* targets)
        with the focal atom.  Weight is 1.0 (cosine similarity reserved for future
        TensorEngine integration).
        """
        # Step 1: collect focal tags
        focal_tags: List[str] = []
        for link in self.core.get_adjacent_links(focal_key):
            if link["rel"].startswith("emo:") or link["rel"].startswith("calc:"):
                focal_tags.append(link["dst"])

        if not focal_tags:
            return []

        # Step 2: gather candidates that share a tag
        candidates: Dict[str, Dict[str, Any]] = {}
        for tag_key in focal_tags:
            for link in self.core.get_incoming_links(tag_key):
                src = link["src"]
                if src == focal_key or src in candidates:
                    continue

                raw = self.core.get_chunk_raw(src)
                if not raw:
                    continue

                meta = json.loads(raw["meta"]) if raw.get("meta") else {}
                role = meta.get("role", meta.get("type", "chunk"))
                if role not in ("chunk", "paragraph", ""):
                    continue

                if allowed_scopes and not self.check_access(src, allowed_scopes):
                    continue

                candidates[src] = {
                    "via":    tag_key,
                    "rel":    link["rel"],
                    "weight": 1.0,
                }

        # Step 3: build result
        results: List[Dict[str, Any]] = []
        for key, info in candidates.items():
            content = self.get_chunk(key) or ""
            results.append({
                "key":     key,
                "via":     info["via"],
                "rel":     info["rel"],
                "preview": content[:60],
                "weight":  info["weight"],
            })

        return results

    def associate(
        self,
        focal_key: str,
        axis: Optional[str] = None,
        scope: int = 2,
        allowed_scopes: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Top-level AssociativeThread entry point.
        Returns associations (semantic link traversal) and resonance (shared-tag matches).
        UnwrittenVoid detection is submitted as an async JCL job by the kernel handler.
        """
        return {
            "associations": self._traverse_associations(focal_key, axis, scope, allowed_scopes),
            "resonance":    self._find_resonance(focal_key, allowed_scopes),
        }

    # =========================================================================
    # 🕳️ ASSOC — gap detection (one level, no inference)
    # =========================================================================

    def find_link_voids(
        self,
        focal_key: str,
        axis: Optional[str] = None,
        allowed_scopes: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Scan ONE-LEVEL outgoing links from focal_key.
        Identify which semantic axes are absent (voids).
        Find structural candidates from shared sets — no inference.
        Returns list of void dicts with structural candidates.
        """
        nucleus = getattr(self, '_nucleus', None)

        # Collect axes present in one-hop outgoing links
        present_axes: set = set()
        for link in (self.core.get_adjacent_links(focal_key) or []):
            rel = link["rel"]
            for ax_name, ax_prefixes in _AXIS_PREFIXES.items():
                if any(rel.startswith(p) for p in ax_prefixes):
                    present_axes.add(ax_name)
        if nucleus:
            for link in (nucleus.core.get_adjacent_links(focal_key) or []):
                rel = link["rel"]
                for ax_name, ax_prefixes in _AXIS_PREFIXES.items():
                    if any(rel.startswith(p) for p in ax_prefixes):
                        present_axes.add(ax_name)

        check_axes = [axis] if (axis and axis in _AXIS_PREFIXES) else list(_AXIS_PREFIXES.keys())

        voids = []
        for ax in check_axes:
            if ax in present_axes:
                continue
            candidates = self._find_axis_candidates(focal_key, ax, allowed_scopes)
            ax_prefixes_list = _AXIS_PREFIXES.get(ax, [])
            voids.append({
                "axis":       ax,
                "missing":    ax_prefixes_list[0] if ax_prefixes_list else ax,
                "hint":       f"No '{ax}' links found.",
                "candidates": candidates[:3],
            })

        return voids

    def _find_axis_candidates(
        self,
        focal_key: str,
        axis: str,
        allowed_scopes: Optional[List[str]] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Find structural candidates for a missing axis from shared sets.
        Tallies how often each potential target appears among set peers.
        No inference — purely structural frequency.
        """
        ax_prefixes = _AXIS_PREFIXES.get(axis, [])
        if not ax_prefixes:
            return []

        nucleus = getattr(self, '_nucleus', None)

        sets = set(self.core.get_collections_for_key(focal_key))
        if nucleus:
            sets.update(nucleus.core.get_collections_for_key(focal_key))
        if not sets:
            return []

        MEMBER_CAP = 20
        SET_CAP    = 5
        target_counts: Dict[str, Dict[str, Any]] = {}

        for set_name in list(sets)[:SET_CAP]:
            members = list(self.core.get_collection_members(set_name) or [])
            if nucleus:
                nuc_members = nucleus.core.get_collection_members(set_name) or []
                seen_m = set(members)
                for k in nuc_members:
                    if k not in seen_m:
                        members.append(k)
                        seen_m.add(k)

            for member_key in members[:MEMBER_CAP]:
                if member_key == focal_key:
                    continue
                for store in ([self.core] + ([nucleus.core] if nucleus else [])):
                    for link in (store.get_adjacent_links(member_key) or []):
                        rel, dst = link["rel"], link["dst"]
                        if any(rel.startswith(p) for p in ax_prefixes):
                            if dst not in target_counts:
                                target_counts[dst] = {"rel": rel, "count": 0}
                            target_counts[dst]["count"] += 1

        if not target_counts:
            return []

        sorted_targets = sorted(target_counts.items(), key=lambda x: -x[1]["count"])
        results = []
        for target_key, info in sorted_targets:
            if allowed_scopes and not self.check_access(target_key, allowed_scopes):
                continue
            content = self.get_chunk(target_key) or ""
            aliases = self.get_aliases_by_key(target_key)
            results.append({
                "key":     target_key,
                "alias":   aliases[0] if aliases else None,
                "rel":     info["rel"],
                "preview": content[:40],
                "count":   info["count"],
            })
            if len(results) >= limit:
                break
        return results

    # =========================================================================
    # 🔀 CROSS-CONCEPT INTERSECTION (sys.cross.*)
    # =========================================================================

    def cross_query(
        self,
        set_names: List[str],
        concept_names: List[str],
        allowed_scopes: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Returns atoms present in the union of concept sets, weighted by coverage.
        Each atom records which concept sets it appears in; atoms in all sets get
        weight=1.0.  IAM scope filtering is applied at every key.
        """
        if not set_names:
            return {"intersection": [], "count": 0}

        # Union of all keys across all concept sets
        all_keys = self.core.get_keys_in_any_collection(set_names)

        results: List[Dict[str, Any]] = []
        for key in all_keys:
            if allowed_scopes and not self.check_access(key, allowed_scopes):
                continue

            key_collections: Set[str] = set(self.core.get_collections_for_key(key))
            present_in = [
                name for name, sname in zip(concept_names, set_names)
                if sname in key_collections
            ]
            if not present_in:
                continue

            content = self.get_chunk(key) or ""
            weight  = len(present_in) / len(concept_names) if concept_names else 0.0

            results.append({
                "key":        key,
                "preview":    content[:60],
                "present_in": present_in,
                "weight":     round(weight, 4),
            })

        results.sort(key=lambda x: x["weight"], reverse=True)
        return {"intersection": results, "count": len(results)}

    def cross_axes(
        self,
        set_names: List[str],
        concept_names: List[str],
        allowed_scopes: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Returns semantic axes present in the given concept sets.
        recommended is the axis with the broadest cross-concept coverage
        (i.e. present in the most distinct concept sets).
        """
        # axis → set of concept names that contain atoms with that axis
        axis_concept_coverage: Dict[str, Set[str]] = {}

        for concept_name, set_name in zip(concept_names, set_names):
            keys = self.core.get_collection_members(set_name)
            for key in keys:
                if allowed_scopes and not self.check_access(key, allowed_scopes):
                    continue
                for link in self.core.get_adjacent_links(key):
                    rel = link["rel"]
                    for axis_name, prefixes in _AXIS_PREFIXES.items():
                        if any(rel.startswith(p) for p in prefixes):
                            if axis_name not in axis_concept_coverage:
                                axis_concept_coverage[axis_name] = set()
                            axis_concept_coverage[axis_name].add(concept_name)
                            break

        if not axis_concept_coverage:
            return {"concepts": concept_names, "available_axes": [], "recommended": None}

        available_axes = list(axis_concept_coverage.keys())
        recommended    = max(available_axes, key=lambda a: len(axis_concept_coverage[a]))
        return {
            "concepts":       concept_names,
            "available_axes": available_axes,
            "recommended":    recommended,
        }

    def cross_atom(
        self,
        atom_key: str,
        set_names: List[str],
        concept_names: List[str],
        allowed_scopes: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Returns concept model atoms that reference the given ontology atom.

        Traverses incoming links to atom_key via:
          - sys:refers_to  (Weaver weave — implicit, created at write time)
          - instance_of    (explicit binding via instance.bind)

        If set_names are provided, results are restricted to atoms in those sets.
        Without set_names, all accessible referencing atoms are returned.

        Design note: atom_key is treated as the abstract type; found atoms are
        treated as concrete instances.  This distinction is a convention for atoms
        outside the proto-word and namespace-qualified term categories —
        see CLAUDE.md "Known Architectural Tensions".
        """
        TRAVERSAL_RELS = frozenset({"sys:refers_to", "instance_of"})

        # All atoms that link TO atom_key (incoming direction)
        incoming = self.get_incoming_links(atom_key)  # [[src, rel], ...]

        # Keep only atoms that link via a traversal relation
        ref_map: Dict[str, str] = {}  # key → relation used (prefer instance_of)
        for src, rel in incoming:
            if rel not in TRAVERSAL_RELS:
                continue
            existing = ref_map.get(src)
            if existing != "instance_of":
                ref_map[src] = rel

        if not ref_map:
            return {"matches": [], "count": 0}

        # Scope filter
        if allowed_scopes:
            ref_map = {k: v for k, v in ref_map.items() if self.check_access(k, allowed_scopes)}

        if not ref_map:
            return {"matches": [], "count": 0}

        matches: List[Dict[str, Any]] = []
        if set_names:
            for key, rel_used in ref_map.items():
                key_collections = set(self.core.get_collections_for_key(key))
                present_in = [
                    name for name, sname in zip(concept_names, set_names)
                    if sname in key_collections
                ]
                if not present_in:
                    continue
                content = self.get_chunk(key) or ""
                matches.append({
                    "key":        key,
                    "preview":    content[:60],
                    "relation":   rel_used,
                    "present_in": present_in,
                })
        else:
            for key, rel_used in ref_map.items():
                content = self.get_chunk(key) or ""
                matches.append({
                    "key":      key,
                    "preview":  content[:60],
                    "relation": rel_used,
                })

        # instance_of matches first, then sys:refers_to
        matches.sort(key=lambda m: (0 if m["relation"] == "instance_of" else 1, m["key"]))
        return {"matches": matches, "count": len(matches)}

    # --- Delegation / Donation Set Management ---
    def create_donation_set(self, name: str, meta: dict) -> None:
        """Create (or update) a named delegation set with metadata."""
        self.core.upsert_collection_def(name, meta)

    def get_donation_set_meta(self, name: str) -> Optional[dict]:
        return self.core.get_collection_def(name)

    def update_donation_set_meta(self, name: str, updates: dict) -> None:
        self.core.merge_collection_def_meta(name, updates)

    def list_donation_sets(self) -> List[dict]:
        return self.core.list_collection_defs(prefix="dont:")

    # --- System Metrics ---
    def stream(self, limit: int = 10) -> List[Dict[str, Any]]: return self.core.fetch_stream(limit)
    def fetch_by_meta_field(self, field: str, value: str, author: str = None, limit: int = 200) -> List[Dict[str, Any]]:
        return self.core.fetch_by_meta_field(field, value, author=author, limit=limit)
    def get_keys_by_scope(self, scope: str) -> List[str]: return self.core.get_keys_by_scope(scope)
    def get_all_keys(self) -> List[str]: return self.core.get_all_keys()
    def get_recent_atom_hashes(self, since: float) -> List[str]: return self.core.get_recent_atom_hashes(since)
    def get_recent_links(self, since: float) -> List[Dict[str, Any]]: return self.core.get_recent_links(since)
    def get_alias_collision_log(self, since: float = 0.0, limit: int = 200, unresolved_only: bool = False) -> list:
        return self.core.get_alias_collision_log(since=since, limit=limit, unresolved_only=unresolved_only)
    def get_system_stats(self) -> Dict[str, Any]:
        t = self.core.get_store_totals()
        stats = {
            "total_atoms":       t["chunks"],
            "total_links":       t["links"],
            "total_aliases":     t["aliases"],
            "total_collections": t["collections"],
        }
        # Include nucleus (vocabulary and shared atoms live there, not in local DB)
        nucleus = getattr(self, '_nucleus', None)
        if nucleus:
            nt = nucleus.core.get_store_totals()
            stats["total_atoms"]       += nt["chunks"]
            stats["total_links"]       += nt["links"]
            stats["total_aliases"]     += nt["aliases"]
            stats["total_collections"] += nt["collections"]
        return stats

class NucleusEngine:
    def __init__(self, db_path: str):
        # FULL sync: every WAL commit is fsynced before returning.
        # Nucleus is the shared ground-truth store; sentinel durability requires
        # this — NORMAL mode loses recent WAL pages on SIGKILL/OS crash.
        self.core = AkashaCore(db_path, sync_mode="FULL")

    def close(self) -> None:
        """Checkpoint WAL and shut down the write queue. Call on graceful exit."""
        self.core.close()
    def vault_store(self, collection: str, key: str, data: Any): self.core.vault_store(collection, key, data)
    def vault_retrieve(self, collection: str, key: str) -> Optional[Any]: return self.core.vault_retrieve(collection, key)
    def vault_scan(self, collection: str, prefix: str = None) -> list: return self.core.vault_scan(collection, prefix)
    def vault_delete(self, collection: str, key: str): self.core.vault_delete(collection, key)

    # --- Universal atom access (for proto-word & DNA atom lookups) ---
    def resolve_alias(self, alias: str) -> Optional[str]:
        return self.core.get_key_by_alias(alias)

    def get_chunk(self, key: str) -> Optional[str]:
        row = self.core.get_chunk_raw(key)
        return row["content"] if row else None

    def get_chunk_raw(self, key: str) -> Optional[dict]:
        return self.core.get_chunk_raw(key)

    def get_aliases_by_key(self, key: str) -> List[str]:
        return self.core.get_aliases_by_key(key)

    # --- Universal atom write (librarian / shared-knowledge mode) ---
    def put_atom(self, content: str, meta: dict, author: str, alias: str = None) -> str:
        """
        Writes a universal atom to the nucleus (shared knowledge mode).
        Returns the key. No Harmonia processing — the nucleus is a pure store.
        """
        import json as _json
        key = hashlib.sha256(content.encode("utf-8")).hexdigest()
        meta_str = _json.dumps(meta, ensure_ascii=False) if meta else "{}"
        self.core.put_chunk_raw(key, content, meta_str, author, "verified", time.time())
        self.core.put_chunk_access(key, ["scope:sys:universal"])
        if alias:
            self.set_alias(key, alias)
        return key

    def _ensure_protoword(self, bare: str) -> Optional[str]:
        """
        Ensure a proto-word atom exists in nucleus for the bare word.
        Creates a minimal lexical atom (content = bare word) if absent.
        Returns the key.
        """
        existing = self.core.get_key_by_alias(bare)
        if existing:
            return existing
        key = hashlib.sha256(bare.encode("utf-8")).hexdigest()
        self.core.put_chunk_raw(key, bare, '{"type":"proto_word","auto_created":true}', "system", "verified", time.time())
        self.core.put_chunk_access(key, ["scope:sys:universal"])
        self.core.put_alias(key, bare)
        # Also register lowercase variant (e.g. ISO3 "USA" → also alias "usa")
        bare_lower = bare.lower()
        if bare_lower != bare and not self.core.get_key_by_alias(bare_lower):
            self.core.put_alias(key, bare_lower)
        # Resolve any pending links that were waiting for this bare alias
        self._resolve_pending_links_for_alias(bare, key)
        return key

    def _ensure_lemma_protoword(self, lemma: str, lang: str = "en") -> Optional[str]:
        """
        Ensure a lang-qualified protoword atom exists for (lemma, lang).

        Lookup order — stops at the first hit:
          1. bare alias 'lemma'         — matches .ak atoms (al "word:en:ask" ask)
          2. qualified alias 'word:{lang}:{lemma}'
        If absent: auto-create with content=lemma, register both aliases.

        This is the Lemma-First principle: any inflected form encountered during
        Weaver processing causes its base lemma to be registered as a protoword
        anchor in the nucleus, ensuring SpaCy-lemmatized tokens always have a
        word:{lang}:{lemma} atom to link to.
        """
        import json as _json
        # 1. Bare alias (common case: pre-loaded .ak atom with `al "word:en:ask" ask`)
        key = self.core.get_key_by_alias(lemma)
        if key:
            return key
        # 2. Qualified alias
        qualified = f"word:{lang}:{lemma}"
        key = self.core.get_key_by_alias(qualified)
        if key:
            return key
        # 3. Auto-create minimal protoword atom
        key = hashlib.sha256(qualified.encode("utf-8")).hexdigest()
        meta = _json.dumps({"type": "proto_word", "lang": lang, "auto_created": True},
                           ensure_ascii=False)
        self.core.put_chunk_raw(key, lemma, meta, "system", "verified", time.time())
        self.core.put_chunk_access(key, ["scope:sys:universal"])
        self.core.put_alias(key, qualified)
        if not self.core.get_key_by_alias(lemma):
            self.core.put_alias(key, lemma)
        _onto_logger.debug("[protoword:lemma] '%s:%s' → %s", lang, lemma, key[:8])
        return key

    def _resolve_pending_links_for_alias(self, alias: str, key: str) -> None:
        """
        When an alias is newly registered, resolve any pending links whose
        dst field matches this alias and write them as real links.
        """
        pending = self.core.get_pending_links()
        for pl in pending:
            if pl["dst"] == alias:
                if self.core.get_chunk_raw(pl["src"]):
                    self.core.put_link_raw(pl["src"], key, pl["rel"],
                                           w=1.0, author=pl["author"], ts=time.time())
                self.core.delete_pending_link(pl["id"])

    def set_alias(self, key: str, alias: str, force: bool = False) -> dict:
        """
        Register an alias in nucleus with proto-word auto-creation.

        First-wins applies to all aliases (bare and qualified) when force=False.
        Qualified aliases also ensure their bare terminal segment has a proto-word
        and create a 'specializes' link from this atom to that proto-word.
        force=True is reserved for the explicit 'alias' management command;
        it overwrites the alias and logs the collision to onto.report.
        Also auto-resolves any pending links waiting for this alias.
        """
        if ":" in alias:
            bare = alias.rsplit(":", 1)[-1]
            if bare:
                proto_key = self._ensure_protoword(bare)
                if proto_key and proto_key != key:
                    existing_links = self.core.get_adjacent_links(key)
                    already = any(
                        lk["dst"] == proto_key and lk["rel"] == "specializes"
                        for lk in existing_links
                    )
                    if not already:
                        self.core.put_link_raw(key, proto_key, "specializes",
                                               author="system", status="inferred", ts=time.time())
            _prev = self.core.get_key_by_alias(alias)
            if _prev is not None and _prev != key:
                if force:
                    self.core.log_alias_collision(alias, _prev, key, event="overwrite")
                    self.core.put_alias(key, alias)
                else:
                    self.core.put_link_raw(key, _prev, "specializes",
                                           author="system", status="inferred", ts=time.time())
            else:
                self.core.put_alias(key, alias)
            # Collection derivation is serialised by the backend (its own durable
            # write path) — the composite layer does not touch the write queue.
            self.core.derive_alias_collections(alias, key)
            self._resolve_pending_links_for_alias(alias, key)
        else:
            existing = self.core.get_key_by_alias(alias)
            if existing is None:
                self.core.put_alias(key, alias)   # put_alias already commits
                self._resolve_pending_links_for_alias(alias, key)
            elif existing != key:
                self.core.put_link_raw(key, existing, "specializes",
                                       author="system", ts=time.time())
        return {"alias": alias, "key": key}

    def put_link(self, src: str, dst: str, rel: str, w: float = 1.0, author: str = "system") -> None:
        """Links two nucleus atoms (or a local atom → nucleus atom)."""
        self.core.put_link_raw(src, dst, rel, w=w, author=author, ts=time.time())

    # --- Delegation set support on nucleus (mirrors GroupEngine interface) ---
    def add_to_set(self, name: str, key: str) -> None:
        # 'ws:' (workspace tracking) and 'wf:' (workflow defs) are reserved prefixes.
        if name.startswith("ws:") or name.startswith("wf:"):
            raise ValueError(f"Set name prefix '{name.split(':', 1)[0]}:' is reserved for internal use.")
        self.core.add_to_collection(name, key)

    def list_set(self, name: str) -> List[dict]:
        keys = self.core.get_collection_members(name)
        result = []
        for k in keys:
            row = self.core.get_chunk_raw(k)
            result.append({"key": k, "content": row["content"] if row else ""})
        return result

    def upsert_set_meta(self, name: str, meta: dict) -> None:
        self.core.upsert_collection_def(name, meta)

    def get_set_meta(self, name: str) -> Optional[dict]:
        return self.core.get_collection_def(name)


class GroupEngine:
    """
    Manages a per-group shared knowledge space.
    Storage: data/groups/<group_id>/g_space.db
    Scope:   scope:group_<group_id>  (set on all atoms written here)
    """
    def __init__(self, group_id: str, base_dir: str = "data"):
        self.group_id = group_id
        self.scope = f"scope:group_{group_id}"
        db_path = os.path.join(base_dir, "groups", group_id, "g_space.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.core = AkashaCore(db_path)

    # --- Read ---
    def resolve_alias(self, alias: str) -> Optional[str]:
        return self.core.get_key_by_alias(alias)

    def get_chunk(self, key: str) -> Optional[str]:
        row = self.core.get_chunk_raw(key)
        return row["content"] if row else None

    def get_chunk_raw(self, key: str) -> Optional[dict]:
        return self.core.get_chunk_raw(key)

    def get_aliases_by_key(self, key: str) -> List[str]:
        return self.core.get_aliases_by_key(key)

    def check_access(self, key: str) -> bool:
        return self.core.check_chunk_access_any(key, [self.scope])

    # --- Write ---
    def put_atom(self, content: str, meta: dict, author: str, alias: str = None) -> str:
        """Copy an atom into this group's space with the group scope."""
        import json as _json
        key = hashlib.sha256(content.encode("utf-8")).hexdigest()
        meta_str = _json.dumps(meta, ensure_ascii=False) if meta else "{}"
        self.core.put_chunk_raw(key, content, meta_str, author, "verified", time.time())
        self.core.put_chunk_access(key, [self.scope])
        if alias:
            self.core.put_alias(key, alias)
        return key

    def put_link(self, src: str, dst: str, rel: str, w: float = 1.0, author: str = "system") -> None:
        self.core.put_link_raw(src, dst, rel, w=w, author=author, ts=time.time())

    # --- Delegation set support ---
    def add_to_set(self, name: str, key: str) -> None:
        # 'ws:' (workspace tracking) and 'wf:' (workflow defs) are reserved prefixes.
        if name.startswith("ws:") or name.startswith("wf:"):
            raise ValueError(f"Set name prefix '{name.split(':', 1)[0]}:' is reserved for internal use.")
        self.core.add_to_collection(name, key)

    def list_set(self, name: str) -> List[dict]:
        keys = self.core.get_collection_members(name)
        result = []
        for k in keys:
            row = self.core.get_chunk_raw(k)
            result.append({"key": k, "content": row["content"] if row else ""})
        return result

    def upsert_set_meta(self, name: str, meta: dict) -> None:
        self.core.upsert_collection_def(name, meta)

    def get_set_meta(self, name: str) -> Optional[dict]:
        return self.core.get_collection_def(name)

    def close(self) -> None:
        self.core.close()
