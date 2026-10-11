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
from lib.akasha.api import gate as _gate
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
                 group_engines: Dict[str, "GroupEngine"] = None,
                 read_only: bool = False, shared_cortex=None):
        self.client_id = client_id
        self.role = role

        # Last time this session served (or was refreshed for) a request. The
        # AkashaManager idle-sweeper reaps authenticated sessions idle past
        # AKASHA_SESSION_TTL, closing their cortex to bound server-side retention.
        # Reaping is transparent: the token stays valid, so get_session() lazily
        # recreates the session on the next call.
        import time as _t
        self.last_active = _t.time()

        # [IAM SCOPES] Injected by the IdentityManager upon authentication
        self.base_scopes = allowed_scopes

        # nucleus is shared across all sessions (single WriteQueue → single writer to nucleus.db).
        # AkashaManager creates one instance and passes it here; never create per-session.
        self.nucleus = nucleus if nucleus is not None else NucleusEngine(f"{base_dir}/central/nucleus.db")

        # ── F47-S1 — LAZY / SHARED cell (the OOM structural fix) ─────────────────────────────
        # The 2026-08-28 kill was the guest-cell ECONOMY, not a leak: every anonymous page view got
        # a private writable banks=1 silica engine (~25 MB) and RSS climbed ~25 MB/guest at bot churn
        # rates until the 8 GB ceiling. But a read-only VISITOR (guest/passerby/human-visitor, and a
        # resident BEFORE its first write) never needs a private cell — it only reads the shared
        # nucleus. So a read-only session SHARES one process-wide read cortex (zero per-session
        # engine) and holds its transient context IN MEMORY; the private cell materializes only on a
        # first write (materialize_cell(), reached by an authenticated writer, never by a guest).
        self.read_only = bool(read_only) and shared_cortex is not None
        self.owns_cortex = not self.read_only        # reset/reap must NEVER close a shared cortex
        self._ctx_mem: Dict[str, any] = {}           # in-memory context for a cell-less session
        self._base_dir = base_dir
        self.root_path = f"{base_dir}/cells/{client_id}"

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

        if self.read_only:
            # Zero-cost path: point at the shared read cortex (already nucleus-attached + tensor-
            # bearing), skip the private-db open, the orphan scan, and the persisted session anchor.
            self.local_cortex = shared_cortex
            self.tensor = getattr(shared_cortex, "tensor", None) or TensorEngine(shared_cortex)
            self.session_node_id = f"@session:{client_id}"   # synthetic — never written to disk
        else:
            os.makedirs(self.root_path, exist_ok=True)
            os.makedirs(f"{base_dir}/central", exist_ok=True)  # Nucleus shared path
            # 1. Memory Layers (via Composite Layer)
            # banks=1 for a per-client cell cortex (R2/F28b guest-FD diet): a cell store is small and
            # private, so it needs no bank fan-out, and one bank means ONE WAL file instead of eight.
            # SQLite ignores banks; an existing multi-bank cell keeps its on-disk geometry (the store
            # auto-detects its width). The shared nucleus keeps its default 8 banks.
            self.local_cortex = AkashaEngine(f"{self.root_path}/l_cortex.db", is_volatile=False, banks=1)
            self.local_cortex.attach_nucleus(self.nucleus)   # proto-word dual-write + fallback
            # Boot orphan scan (slice 4) for this cell's private cortex: roll back any conversation
            # bundle whose process crashed mid-transaction (its ws:{tx_id} tracking set survived
            # without a commit/rollback). drop_members=True — the cortex atoms are private and
            # uncommitted, so dropping them restores the crash-stop 'last write only' guarantee.
            HarmoniaEngine.reconcile_orphan_workspaces(self.local_cortex, drop_members=True)
            # 1.5 Cognitive layer
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
        if self.owns_cortex:
            self.session_node_id = self._anchor_consciousness()

        # Fast caches for continuous dialogue
        self.last_written_id = self.get_context("last_written_id")
        self.last_written_vector = self.get_context("last_written_vector")
        self._restore_locale()  # needs session_node_id → must come after the anchor

    @property
    def active_scopes(self) -> List[str]:
        """All scope entries for this session: permission scopes + capability flags.
        Locale preferences are intentionally excluded — they live in locale_scopes
        and must not bleed into SQL permission queries (Dim-3 ≠ Dim-1)."""
        return self.base_scopes

    def refresh_group_engines(self, engines: Dict[str, "GroupEngine"]) -> None:
        """Rewire this live session's group spaces after a membership change.

        A session created before the client joined a group starts with an empty
        group_engines dict; ConsciousnessEngine then captured its *own* separate
        empty dict (`group_engines or {}`), and the resolver reads
        `session.group_engines` live. So a later grp.add must (a) reference-swap the
        session's dict and (b) re-point consciousness at the same new dict — else the
        member holds the group scope but has no engine to reach the shared space, and
        both donation (`dont.send to=group:`) and shared reads fail with "Group space
        not loaded". Reference-swap (not in-place mutation) keeps a concurrent reader
        iterating the old dict safe."""
        new = dict(engines)
        self.group_engines = new
        if getattr(self, "consciousness", None) is not None:
            self.consciousness.group_engines = new

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
        # F47-S1 — a cell-less (read-only) session keeps its transient context in memory: it has no
        # persisted session anchor to read meta from, and a visitor's locale/dialogue caches need not
        # survive a recycle. An owning session persists in its private cortex as before.
        if self.read_only:
            return self._ctx_mem.get(key, default)
        meta = self.local_cortex.get_meta(self.session_node_id)
        return meta.get(key, default)

    def set_context(self, key: str, value):
        if self.read_only:
            self._ctx_mem[key] = value
        else:
            self.local_cortex.set_meta(self.session_node_id, key, value)
        if key == "last_written_id": self.last_written_id = value
        if key == "last_written_vector": self.last_written_vector = value

    def materialize_cell(self):
        """F47-S1 — upgrade a read-only (shared-cortex) session to an OWNING one with a private cell.
        Reached ONLY on a first write by an authenticated identity (a guest can never write). Idempotent:
        a session that already owns its cortex returns immediately. After this the session persists its
        own atoms and context, and reset/reap will close+wipe its cell like any owning session."""
        if self.owns_cortex:
            return
        os.makedirs(self.root_path, exist_ok=True)
        os.makedirs(f"{self._base_dir}/central", exist_ok=True)
        cortex = AkashaEngine(f"{self.root_path}/l_cortex.db", is_volatile=False, banks=1)
        cortex.attach_nucleus(self.nucleus)
        HarmoniaEngine.reconcile_orphan_workspaces(cortex, drop_members=True)
        tensor = TensorEngine(cortex)
        cortex.attach_tensor_engine(tensor)
        self.local_cortex = cortex
        self.tensor = tensor
        self.owns_cortex = True
        self.read_only = False
        self.consciousness = ConsciousnessEngine(
            self.local_cortex, nucleus=self.nucleus, group_engines=self.group_engines)
        self.session_node_id = self._anchor_consciousness()
        # carry the in-memory context forward into the durable anchor
        for _k, _v in list(self._ctx_mem.items()):
            try:
                self.local_cortex.set_meta(self.session_node_id, _k, _v)
            except Exception:
                pass
        self._ctx_mem = {}

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
        # F35/F47-6.4 — STRUCTURAL RESERVE: a handful of session slots are reserved for
        # authenticated (non-guest) identities so a guest/bot storm can NEVER occupy the last
        # slot and lock the operator out of their own Cell. A GUEST is refused once the cap minus
        # the reserve is reached; an admin/user still gets in. Clamped to leave at least one guest
        # slot. This incident class bit once before — hold it by construction.
        try:
            _reserve = int(_os.environ.get("AKASHA_ADMIN_SESSION_RESERVE", "2"))
        except (TypeError, ValueError):
            _reserve = 2
        self._admin_session_reserve = max(0, min(_reserve, self.max_sessions - 1))
        nucleus_path = _os.path.join(base_dir, "central", "nucleus.db")

        # Single shared NucleusEngine for the entire process.
        # One instance = one WriteQueue = one writer thread for nucleus.db.
        # Created BEFORE IdentityManager so IAM can share this instance
        # rather than lazy-creating its own (which would be a second WQ).
        _os.makedirs(_os.path.join(base_dir, "central"), exist_ok=True)
        self.shared_nucleus = NucleusEngine(nucleus_path)
        atexit.register(self.shared_nucleus.close)

        # F47-S1 — ONE process-wide read cortex shared by every read-only visitor session (guests /
        # passersby / human visitors). Created lazily on the first visitor so a write-only deployment
        # pays nothing. Bound to the shared nucleus with a tensor for semantic reads; NEVER written by
        # a visitor (guests are write-denied at the capability gate), so sharing is safe and leaks no
        # visitor's data to the next. This replaces the per-guest ~25 MB private cell that was the
        # 2026-08-28 OOM driver — visitor RSS cost drops from ~25 MB/guest to ~0.
        self._guest_read_cortex = None

        # SINGLE-WRITER INVARIANT: the serve-only portal subprocess must NOT write the shared
        # nucleus. Both the orphan reconcile (clears stray ws:* sets) and the ref-primitive seed
        # WRITE it, and the PRIMARY writer already ran them before spawning the portal — a serve-only
        # worker re-running them is a second writer into one nucleus.db (the "Dead" crash the portal
        # hit). Skip both here; the portal only reads (and forwards writes to the primary).
        _serve_only = _os.environ.get("AKASHA_SERVE_ONLY", "").strip().lower() in ("1", "yes", "true", "on")
        if not _serve_only:
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

        # Guest session pool — slots are allocated lazily (an idle slot costs
        # nothing), so default generously enough for a small public portal.
        # A visitor reuses ONE slot across page views (front-end caches the token),
        # so this is ~concurrent-visitors, not page-views. Override with
        # AKASHA_GUEST_POOL_SIZE for a busier deployment.
        from lib.akasha.jcl.guest_pool import GuestPool
        _pool_size = int(_os.environ.get("AKASHA_GUEST_POOL_SIZE", "128"))
        # F47-S1 / visitor-classes spec — 15 min default, sized to a human VISIT (dwell time with
        # margin), NOT to memory. The renovation-era 5-min cut was a memory stopgap when each guest
        # cost ~25 MB; with lazy/shared cells (above) a visitor costs ~0, so TTL has no memory
        # dimension — recycling destroys only bookkeeping. A human visitor's session never expires
        # mid-visit. Override with AKASHA_GUEST_TTL (operator note: keep 300 only until this ships,
        # then restore 900 in env/deployment.env in the same deploy).
        _pool_ttl  = int(_os.environ.get("AKASHA_GUEST_TTL",       "900"))
        self.guest_pool = GuestPool(
            size=_pool_size, ttl=_pool_ttl,
            on_reclaim=self._reset_guest_slot,
        )

        # Authenticated-session idle sweeper. Unlike guests (reclaimed by the pool
        # above), admin/user sessions were retained for the whole process life —
        # created lazily per identity, never freed without an explicit logout, so a
        # long-running multi-user server accumulated open cortex handles and crept
        # toward the session cap. This daemon reaps any non-guest, non-system session
        # idle past AKASHA_SESSION_TTL (default 1800s), closing its cortex. It is
        # transparent: the akt: token stays valid, so get_session() recreates the
        # session on the next request. Set AKASHA_SESSION_TTL=0 to disable.
        self._sess_ttl = int(_os.environ.get("AKASHA_SESSION_TTL", "1800"))
        if self._sess_ttl > 0:
            self._start_session_sweeper()

    def _groups_of(self, client_id):
        """The group registry, handed to `gate.scopes_for` as a callback.

        The gate must not import the manager — it decides FOR the heart, so it may not depend
        on it — and the registry lives here. `client_id is None` means "every group the cell
        knows", which is what a `groups: all` row asks for."""
        try:
            if client_id is None:
                # EVERY group the cell knows, from the registry's own mirror. Without it a
                # `groups: all` row picks up no group scope at all, and the operator reads
                # downstream as "Not a member of group X" for a group it owns.
                return sorted(set(self.iam._group_members) | set(self.iam._group_admins)
                              | set(self.iam._group_librarians))
            return list(self.iam.get_client_groups(client_id) or [])
        except Exception:
            return []

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

        # THE GATE IS THE SOURCE OF THE SCOPE LIST. `iam.get_allowed_scopes` is gone: a session
        # is the gate's view of an identity, derived from the assignment file, and the store
        # then ENFORCES that list (§2b allows enforcement, never a second decision). The role
        # above is still resolved because the session carries it for display and for the
        # engines it opens — it is not consulted for a permission any more.
        allowed_scopes = _gate.scopes_for(client_id, groups_of=self._groups_of)

        # The check-then-create on self.sessions is serialized through the queue.
        def _create_or_update():
            # Recompute group membership every call so a live session picks up a
            # grp.add/grp.rm that happened after it was created (mirrors the
            # base_scopes refresh below). Engines are pooled, so this is a cheap
            # dict rebuild, not new DB connections.
            group_ids = self.iam.get_client_groups(client_id)
            grp_engines = {gid: self._get_group_engine(gid) for gid in group_ids}
            # A session's ROLE is not fixed for life. An identity may be registered or
            # elevated AFTER its session was first created (e.g. the "admin" session a
            # boot daemon opens before genesis_rite registers admin — authenticate then
            # returns GUEST, so the cached session would stay GUEST forever), or a
            # passphrase/role change may re-grade it. When the privilege CLASS flips
            # (guest ⇄ owner — the bit that decides read_only + shared-vs-private cortex),
            # drop the stale session so it is rebuilt with the right cortex; a same-class
            # role change is refreshed in place below (like base_scopes).
            _cached = self.sessions.get(client_id)
            if _cached is not None and (_cached.role == Role.GUEST) != (actual_role == Role.GUEST):
                self.sessions.pop(client_id, None)
            if client_id not in self.sessions:
                # F35 — a guest is capped BELOW the hard limit so the reserved slots stay open for
                # an authenticated operator; admin/user may use the full cap.
                _is_guest = (actual_role == Role.GUEST)
                _cap = (self.max_sessions - self._admin_session_reserve) if _is_guest else self.max_sessions
                if len(self.sessions) >= _cap:
                    if _is_guest and len(self.sessions) < self.max_sessions:
                        raise PermissionError(
                            f"Akasha Limit Reached: guest capacity full "
                            f"({_cap}); {self._admin_session_reserve} slot(s) reserved for sign-in.")
                    raise PermissionError(f"Akasha Limit Reached: Max {self.max_sessions} sessions allowed.")
                # F47-S1 — a GUEST is a read-only visitor: no private cell, share the read cortex.
                _ro = _is_guest
                self.sessions[client_id] = AkashaSession(
                    client_id=client_id,
                    role=actual_role,
                    allowed_scopes=allowed_scopes,
                    base_dir=self.base_dir,
                    group_engines=grp_engines,
                    nucleus=self.shared_nucleus,
                    read_only=_ro,
                    shared_cortex=(self._get_guest_read_cortex() if _ro else None),
                )
            else:
                self.sessions[client_id].role = actual_role
                self.sessions[client_id].base_scopes = allowed_scopes
                self.sessions[client_id].refresh_group_engines(grp_engines)
            sess = self.sessions[client_id]
            import time as _t
            sess.last_active = _t.time()   # activity marker for the idle-sweeper
            return sess

        return self._session_wq.submit(_create_or_update)

    def close_session(self, client_id: str):
        self._session_wq.submit(lambda: self.sessions.pop(client_id, None))

    # ── Authenticated-session idle sweeper ─────────────────────────────────────
    def _start_session_sweeper(self) -> None:
        """Daemon that reaps idle authenticated sessions (see __init__)."""
        import threading, time as _t
        interval = max(60, self._sess_ttl // 4)

        from lib.akasha import lifecycle
        def _loop() -> None:
            while True:
                if lifecycle.wait_or_shutdown(interval):   # wakes at once on shutdown
                    return
                try:
                    self._sweep_sessions()
                except Exception as exc:            # never let the sweeper die
                    logger.warning("[Session] idle sweep error: %s", exc)

        threading.Thread(target=_loop, daemon=True, name="session-sweeper").start()

    @staticmethod
    def _mem_available_mb():
        """Host MemAvailable in MB (Linux /proc/meminfo), or None off-Linux."""
        try:
            with open("/proc/meminfo") as f:
                for ln in f:
                    if ln.startswith("MemAvailable:"):
                        return int(ln.split()[1]) // 1024
        except (OSError, ValueError, IndexError):
            pass
        return None

    def _sweep_sessions(self) -> None:
        """Find non-guest, non-system sessions idle past the TTL and reap them.
        Guests are reclaimed by the GuestPool; system/bootstrap ids are never reaped.

        F47-S1 #2 — force-recycle at memory pressure: when MemAvailable falls below
        AKASHA_MEM_PRESSURE_MB (default 0 = off), also reap the OLDEST idle owning sessions ahead of
        their TTL (they each hold a private cell), so a materialized-cell build-up is shed
        immediately instead of waiting out the full idle window. With lazy cells a guest costs ~0, so
        this now guards only owning (resident/materialized) sessions — the durable safety net."""
        import time as _t
        now = _t.time()
        deadline = now - self._sess_ttl
        stale, owning_idle = [], []
        for cid, sess in list(self.sessions.items()):     # snapshot; read-only
            if sess.role == Role.GUEST:
                continue
            if cid.startswith("sys:") or self.iam.is_system_identity(cid):
                continue
            _la = getattr(sess, "last_active", 0.0)
            if _la < deadline:
                stale.append(cid)
            elif getattr(sess, "owns_cortex", True):
                owning_idle.append((_la, cid))
        for cid in stale:
            self._reap_session(cid)
        # Memory-pressure force-recycle (opt-in).
        try:
            _floor = int(os.environ.get("AKASHA_MEM_PRESSURE_MB", "0") or "0")
        except (TypeError, ValueError):
            _floor = 0
        if _floor > 0:
            avail = self._mem_available_mb()
            if avail is not None and avail < _floor:
                # reap the oldest idle owning sessions first (they carry a private cell); a small
                # batch per sweep so a burst does not stall the queue. A session touched since is
                # protected by the re-check inside _reap_session.
                owning_idle.sort()
                _batch = max(1, int(os.environ.get("AKASHA_MEM_PRESSURE_BATCH", "8") or "8"))
                victims = [cid for _la, cid in owning_idle[:_batch] if cid not in stale]
                if victims:
                    logger.warning("[Session] memory pressure (avail=%dMB < %dMB) — force-recycling "
                                   "%d idle owning session(s) ahead of TTL", avail, _floor, len(victims))
                    for cid in victims:
                        self._reap_session(cid)

    def _reap_session(self, client_id: str) -> None:
        """Pop + close one idle session, serialized through the session queue so it
        cannot race get_session(). Re-checks last_active under the queue: a request
        that touched the session just before reaping wins and the reap is skipped."""
        def _do() -> None:
            import time as _t
            sess = self.sessions.get(client_id)
            if sess is None:
                return
            if getattr(sess, "last_active", 0.0) >= _t.time() - self._sess_ttl:
                return                                # touched since the sweep — keep it
            self.sessions.pop(client_id, None)
            if getattr(sess, "owns_cortex", True):       # F47-S1 — never close the SHARED read cortex
                try:
                    sess.local_cortex.close()
                except Exception as exc:
                    logger.warning("[Session] cortex close failed for %s: %s", client_id, exc)
            logger.info("[Session] reaped idle session %s (idle > %ss)", client_id, self._sess_ttl)
        self._session_wq.submit(_do)

    def purge_client_cell(self, client_id: str) -> bool:
        """Erase a client's entire private cell (its l_cortex.db and everything in it —
        recipes, personal foods, measurements, all private atoms). Used by account
        deletion. Closes the live session and deletes the cell directory; the shared
        nucleus (and the retained IAM audit record) are never touched. Serialized through
        _session_wq so it cannot race session creation. A guest slot / system id is never
        a valid target here (the caller must gate that)."""
        def _wipe() -> bool:
            session = self.sessions.pop(client_id, None)
            if session is not None and getattr(session, "owns_cortex", True):
                try:
                    session.local_cortex.close()
                except Exception as e:
                    logger.warning("[Account] cortex close failed for %s: %s", client_id, e)
            import shutil as _shutil
            cell_dir = os.path.join(self.base_dir, "cells", client_id)
            _shutil.rmtree(cell_dir, ignore_errors=True)
            return True
        return self._session_wq.submit(_wipe)

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

    def _get_guest_read_cortex(self):
        """F47-S1 — the ONE shared read cortex for read-only visitor sessions. Lazily created (a
        single banks=1 engine over a shared db, nucleus-attached, tensor-bearing) and reused by every
        visitor, so per-visitor memory cost is ~zero. Called only inside the _session_wq (single
        worker), so the lazy init needs no lock. Closed once at process exit, never on a guest recycle."""
        if self._guest_read_cortex is None:
            root = os.path.join(self.base_dir, "cells", "_guest_read")
            os.makedirs(root, exist_ok=True)
            eng = AkashaEngine(os.path.join(root, "l_cortex.db"), is_volatile=False, banks=1)
            eng.attach_nucleus(self.shared_nucleus)
            try:
                eng.attach_tensor_engine(TensorEngine(eng))
            except Exception as exc:
                logger.debug("[Guest] shared read cortex tensor attach skipped: %s", exc)
            self._guest_read_cortex = eng
            atexit.register(eng.close)
            logger.info("[Guest] shared read cortex created — read-only visitors hold NO private cell.")
        return self._guest_read_cortex

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
        # A GUEST SLOT IS THE `anonymous guest` LINE plus a token. The token is TRUST (may this
        # caller be believed to be anonymous); the line is PERMISSION. There is no guest branch
        # here any more — the slot resolves through the same derivation as every other identity,
        # and lands on the `guest` row because no line names it (§4 step 1).
        allowed_scopes = _gate.scopes_for(slot_id, groups_of=self._groups_of)
        self.sessions[slot_id] = AkashaSession(
            client_id=slot_id,
            role=Role.GUEST,
            allowed_scopes=allowed_scopes,
            base_dir=self.base_dir,
            nucleus=self.shared_nucleus,
            read_only=True,                              # F47-S1 — no private cell for a visitor
            shared_cortex=self._get_guest_read_cortex(),
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
            # F47-S1 — a read-only visitor shares the process read cortex and wrote nothing private;
            # only pop it. Closing the shared cortex would break every other live visitor. An OWNING
            # slot (a resident that materialized a cell on this id, or a legacy multi-bank guest cell)
            # still gets closed + wiped so the next visitor cannot read stale private data.
            if session is not None and getattr(session, "owns_cortex", True):
                try:
                    session.local_cortex.close()
                except Exception as e:
                    logger.warning("[Guest] cortex close failed for %s: %s", slot_id, e)
                import shutil as _shutil
                cell_dir = os.path.join(self.base_dir, "cells", slot_id)
                _shutil.rmtree(cell_dir, ignore_errors=True)
        self._session_wq.submit(_wipe)
