"""
Cognitive Session & Orchestration Layer.
Represents an active cognitive session for a specific client.
Ties together Memory (Cortex/Nucleus), Spatiotemporal (Jataka), 
Linguistics (Locale), and Tensor/Dive layers.

[MULTIDIMENSIONAL SCOPE UPDATE]
The Session now holds the 'allowed_scopes' inherited from IAM, dynamically 
combining them with 'Language Scopes' (Locale) to ensure ultra-fast, 
hardware-level filtering of all graph traversals and memory retrievals.
"""
import atexit
import logging
import os
import json
from typing import Dict, Optional, List
from lib.akasha.jcl.write_queue import WriteQueue

logger = logging.getLogger("Akasha.Manager")

from .composite import AkashaEngine, NucleusEngine, GroupEngine
from .locale import LocaleContext
from .resolver import ContextResolver
from .chrono import TemporalContext
from .identity import IdentityManager, Role
from .ref_primitives import bootstrap_ref_primitives
from .tensor import TensorEngine
from .consciousness import ConsciousnessEngine
from lib.jataka.engine import JatakaEngine
from lib.harmonia.engine import HarmoniaEngine

class AkashaSession:
    """
    The unified consciousness and orchestration anchor for a client's Cell.
    """
    def __init__(self, client_id: str, role: Role, allowed_scopes: List[str],
                 base_dir: str = "data", harmonia_engine=None, group_ids: List[str] = None,
                 nucleus: "NucleusEngine" = None,
                 group_engines: Dict[str, "GroupEngine"] = None):
        self.client_id = client_id
        self.role = role

        # [IAM SCOPES] Injected by the IdentityManager upon authentication
        self.base_scopes = allowed_scopes

        # Ensure directory structure exists for this local cell
        self.root_path = f"{base_dir}/cells/{client_id}"
        os.makedirs(self.root_path, exist_ok=True)
        os.makedirs(f"{base_dir}/central", exist_ok=True) # Nucleus shared path

        # 1. Memory Layers (via Composite Layer)
        self.local_cortex = AkashaEngine(f"{self.root_path}/l_cortex.db", is_volatile=False)
        # nucleus is shared across all sessions (single WriteQueue → single writer to nucleus.db).
        # AkashaManager creates one instance and passes it here; never create per-session.
        self.nucleus = nucleus if nucleus is not None else NucleusEngine(f"{base_dir}/central/nucleus.db")
        self.local_cortex.attach_nucleus(self.nucleus)  # proto-word dual-write + fallback

        # Boot orphan scan (slice 4) for this cell's private cortex: roll back any
        # conversation bundle whose process crashed mid-transaction (its ws:{tx_id}
        # tracking set survived without a commit/rollback). drop_members=True — the
        # cortex atoms are private and uncommitted, so dropping them restores the
        # crash-stop 'last write only' guarantee. Runs once at cortex open, before the
        # session serves any request; a fresh/guest cortex has no orphans (fast no-op).
        HarmoniaEngine.reconcile_orphan_workspaces(self.local_cortex, drop_members=True)

        # Group knowledge spaces — shared engines passed in from AkashaManager pool.
        # If group_engines is provided (normal path via AkashaManager), use it directly.
        # Fallback: create per-session (backwards compat / standalone use).
        self.group_engines: Dict[str, GroupEngine] = {}
        if group_engines is not None:
            self.group_engines = group_engines
        else:
            for gid in (group_ids or []):
                try:
                    self.group_engines[gid] = GroupEngine(gid, base_dir)
                except Exception as e:
                    logger.warning("[Session] Could not load group engine '%s': %s", gid, e)

        # 1.5 Cognitive & Navigation Layers
        self.tensor = TensorEngine(self.local_cortex)
        self.local_cortex.attach_tensor_engine(self.tensor)
        self.consciousness = ConsciousnessEngine(
            self.local_cortex, nucleus=self.nucleus, group_engines=self.group_engines
        )
        
        # 2. Contextual Layers
        self.locale = LocaleContext()
        self.chrono = TemporalContext()
        self.harmonia_engine = harmonia_engine if harmonia_engine is not None else HarmoniaEngine()
        self.jataka = JatakaEngine(self) # Spatiotemporal Sync & Dreams

        # 3. Session Transient State & Graph Anchor
        self.temp_staging = []
        self.symbols = {}
        self.session_node_id = self._anchor_consciousness()

        # Fast caches for continuous dialogue
        self.last_written_id = self.get_context("last_written_id")
        self.last_written_vector = self.get_context("last_written_vector")
        self._restore_locale()  # needs session_node_id → must come after _anchor_consciousness

    @property
    def active_scopes(self) -> List[str]:
        """All scope entries for this session: permission scopes + capability flags.
        Locale preferences are intentionally excluded — they live in locale_scopes
        and must not bleed into SQL permission queries (Dim-3 ≠ Dim-1)."""
        return self.base_scopes

    @property
    def locale_scopes(self) -> List[str]:
        """Dimension-3: user's priority locale list.
        Use for display/result-ordering filters only — never for access control SQL."""
        return self.locale.get_language_scopes()

    def _anchor_consciousness(self) -> str:
        """Locates or creates the physical anchor for this session in the local graph."""
        alias_name = f"sys:session:{self.client_id}"
        
        existing_key = self.local_cortex.resolve_alias(alias_name)
        if existing_key:
            return existing_key
            
        initial_meta = {
            "type": "sys:session",
            "client_id": self.client_id,
            "focus": "@origin",
            "mode": "root"
        }
        
        # Secure the session anchor so only the owner (and admins) can see/modify it
        private_scopes = [f"owner:user_{self.client_id}", f"view:user_{self.client_id}"]

        # Session-lifecycle write, not a user memory op: it runs at session
        # creation, outside any request workspace. Exempt it from the single-route
        # guard via system_context (still content-addressed and auditable — the
        # exemption is only from the workspace requirement).
        from lib.akasha.jcl.workspace_context import system_context as _sys_ctx
        with _sys_ctx():
            node_id = self.local_cortex.put_chunk(
                content=f"Shared Consciousness Anchor for {self.client_id}",
                meta=initial_meta,
                author=self.client_id,
                scopes=private_scopes
            )
            self.local_cortex.set_alias(node_id, alias_name)
        return node_id

    # --- Locale Persistence ---
    def _restore_locale(self):
        """Load locale preferences from session context on startup."""
        primary   = self.get_context("locale_primary")
        supported = self.get_context("locale_supported")
        if primary:
            self.locale.primary = primary
        if supported and isinstance(supported, list):
            self.locale.supported = supported
        # Ensure primary is always in supported
        if self.locale.primary not in self.locale.supported:
            self.locale.supported.insert(0, self.locale.primary)

    def save_locale(self):
        """Persist current locale settings to session context."""
        self.set_context("locale_primary",   self.locale.primary)
        self.set_context("locale_supported",  self.locale.supported)

    # --- Context Recall & Persistence ---
    def get_context(self, key: str, default=None):
        meta = self.local_cortex.get_meta(self.session_node_id)
        return meta.get(key, default)

    def set_context(self, key: str, value):
        self.local_cortex.set_meta(self.session_node_id, key, value)
        if key == "last_written_id": self.last_written_id = value
        if key == "last_written_vector": self.last_written_vector = value

    # --- Ref-slot helpers ($who / $where / $why / …) ---
    def get_ref_slot(self, dim: str) -> Optional[str]:
        """Return the atom key currently bound to the typed context slot $<dim>."""
        return self.get_context(f"ref_slot:{dim}")

    def set_ref_slot(self, dim: str, key: str) -> None:
        """Bind an atom key to the typed context slot $<dim>."""
        self.set_context(f"ref_slot:{dim}", key)

    # --- Vault Helpers ---
    def vault_store(self, collection: str, key: str, data: any):
        self.nucleus.vault_store(collection, key, data)

    def vault_retrieve(self, collection: str, key: str):
        return self.nucleus.vault_retrieve(collection, key)


class AkashaManager:
    """
    Manages multiple AkashaSessions and handles authentication/policy.
    Integrated with IAM (IdentityManager) for capability-based access control.
    """
    def __init__(self, series_name: str = "seeds", base_dir: str = "data"):
        self.sessions: Dict[str, AkashaSession] = {}
        self.base_dir = base_dir
        import os as _os
        # [DNA_TARGET:MAX_SESSIONS] — overridden at runtime by AKASHA_MAX_LEAVES env var (set by seed script)
        _env_limit = _os.environ.get("AKASHA_MAX_LEAVES")
        self.max_sessions = int(_env_limit) if _env_limit else 999
        nucleus_path = _os.path.join(base_dir, "central", "nucleus.db")

        # Single shared NucleusEngine for the entire process.
        # One instance = one WriteQueue = one writer thread for nucleus.db.
        # Created BEFORE IdentityManager so IAM can share this instance
        # rather than lazy-creating its own (which would be a second WQ).
        _os.makedirs(_os.path.join(base_dir, "central"), exist_ok=True)
        self.shared_nucleus = NucleusEngine(nucleus_path)
        atexit.register(self.shared_nucleus.close)

        # Boot orphan scan (slice 4): heal any nucleus tracking sets left by a bundle
        # whose process crashed mid-transaction on the previous run. Runs before any
        # session exists, so nothing live can be mistaken for an orphan. Proto-words
        # are kept (drop_members=False) — shared/content-addressed, dropping is unsafe.
        HarmoniaEngine.reconcile_orphan_workspaces(self.shared_nucleus, drop_members=False)

        # Seed ref: cognitive primitives (idempotent — no-op if already present).
        # Must run before .ak ontology loading and before any user sessions exist.
        bootstrap_ref_primitives(self.shared_nucleus)

        # IAM uses the shared nucleus so all vault writes go through the same WQ.
        self.iam = IdentityManager(series_name, nucleus=self.shared_nucleus)

        # Shared GroupEngine pool — one instance per group_id, keyed by group_id.
        # Multiple sessions belonging to the same group share one GroupEngine (one WQ),
        # preventing parallel writes to the same group DB file.
        self.shared_group_engines: Dict[str, GroupEngine] = {}
        atexit.register(lambda: [ge.close() for ge in self.shared_group_engines.values()])

        # All session create/update/delete operations are serialized through this
        # queue — eliminates check-then-set races without any locks.
        self._session_wq = WriteQueue(name="session-writer")

        # Guest session pool — pre-allocated slots recycled on TTL expiry.
        from lib.akasha.jcl.guest_pool import GuestPool
        _pool_size = int(_os.environ.get("AKASHA_GUEST_POOL_SIZE", "20"))
        _pool_ttl  = int(_os.environ.get("AKASHA_GUEST_TTL",       "600"))
        self.guest_pool = GuestPool(
            size=_pool_size, ttl=_pool_ttl,
            on_reclaim=self._reset_guest_slot,
        )

    def get_session(self, client_id: str, requested_role: str = "admin") -> AkashaSession:
        """
        Retrieves or creates a session for the client.
        Enforces IAM Authentication and generates Multidimensional Scopes.
        """
        # IAM calls are read-only and safe to run outside the queue.
        try:
            actual_role = self.iam.authenticate(client_id)
        except PermissionError:
            role_map = {"admin": Role.ADMIN, "cell": Role.USER, "leaf": Role.GUEST}
            actual_role = role_map.get(requested_role.lower(), Role.GUEST)

        allowed_scopes = self.iam.get_allowed_scopes(client_id, actual_role)

        # The check-then-create on self.sessions is serialized through the queue.
        def _create_or_update():
            if client_id not in self.sessions:
                if len(self.sessions) >= self.max_sessions:
                    raise PermissionError(f"Akasha Limit Reached: Max {self.max_sessions} sessions allowed.")
                group_ids = self.iam.get_client_groups(client_id)
                grp_engines = {gid: self._get_group_engine(gid) for gid in group_ids}
                self.sessions[client_id] = AkashaSession(
                    client_id=client_id,
                    role=actual_role,
                    allowed_scopes=allowed_scopes,
                    base_dir=self.base_dir,
                    group_engines=grp_engines,
                    nucleus=self.shared_nucleus,
                )
            else:
                self.sessions[client_id].base_scopes = allowed_scopes
            return self.sessions[client_id]

        return self._session_wq.submit(_create_or_update)

    def close_session(self, client_id: str):
        self._session_wq.submit(lambda: self.sessions.pop(client_id, None))

    def count_sessions(self) -> dict:
        """Return live session counts broken down by role. Thread-safe (read-only snapshot)."""
        from collections import Counter
        snap = list(self.sessions.values())
        counts = Counter(s.role.value for s in snap)
        return {
            "total":       len(snap),
            "admin":       counts.get("admin", 0),
            "librarian":   counts.get("librarian", 0),
            "user":        counts.get("user", 0),
            "group_admin": counts.get("group_admin", 0),
            "guest":       counts.get("guest", 0),
        }

    def _get_group_engine(self, gid: str) -> "GroupEngine":
        """Return the process-singleton GroupEngine for a group, creating it on first access."""
        if gid not in self.shared_group_engines:
            self.shared_group_engines[gid] = GroupEngine(gid, self.base_dir)
        return self.shared_group_engines[gid]

    # ── Guest pool helpers ────────────────────────────────────────────────────

    def checkout_guest_session(self) -> Optional[str]:
        """
        Claim a free guest pool slot and ensure a warm AkashaSession exists for it.
        Returns the slot_id or None if the pool is exhausted.
        """
        slot_id = self.guest_pool.checkout()
        if slot_id is None:
            return None
        if slot_id not in self.sessions:
            self._session_wq.submit(lambda: self._ensure_guest_slot(slot_id))
        return slot_id

    def _ensure_guest_slot(self, slot_id: str) -> None:
        """Create an AkashaSession for a pool slot if it doesn't exist yet (queue context)."""
        if slot_id in self.sessions:
            return
        allowed_scopes = self.iam.get_allowed_scopes(slot_id, Role.GUEST)
        self.sessions[slot_id] = AkashaSession(
            client_id=slot_id,
            role=Role.GUEST,
            allowed_scopes=allowed_scopes,
            base_dir=self.base_dir,
            nucleus=self.shared_nucleus,
        )

    def touch_guest_session(self, slot_id: str) -> bool:
        """
        Renew the inactivity timer for a pool slot.
        Called on every request that carries a guest binding key.
        Returns False if the slot_id is not a pool slot.
        """
        return self.guest_pool.touch(slot_id)

    def _reset_guest_slot(self, slot_id: str) -> None:
        """
        Fully wipe a reclaimed guest slot so the next visitor cannot read the
        previous visitor's data.  Clearing only in-memory state is not enough:
        the slot's private cortex DB persists on disk and every visitor to a
        pool slot shares the same client_id/author tag, so residual atoms would
        be readable by the next visitor.  We therefore close and delete the
        slot's private cell directory entirely; the next checkout recreates a
        fresh, empty session.  The shared nucleus is never touched.

        Runs serialized through _session_wq so it cannot race session creation.
        """
        def _wipe() -> None:
            session = self.sessions.pop(slot_id, None)
            if session is not None:
                try:
                    session.local_cortex.close()
                except Exception as e:
                    logger.warning("[Guest] cortex close failed for %s: %s", slot_id, e)
            import shutil as _shutil
            cell_dir = os.path.join(self.base_dir, "cells", slot_id)
            _shutil.rmtree(cell_dir, ignore_errors=True)
        self._session_wq.submit(_wipe)
