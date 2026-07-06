"""
Identity, Capability, and Delegation Layer (IAM)

Role hierarchy (highest → lowest privilege):
  ADMIN        — full system access including DNA memory
  LIBRARIAN    — collective knowledge editor; no personal/DNA access
  GROUP_ADMIN  — manages one group; group shared knowledge editor; no personal/other access
  USER         — standard authenticated client; private scope + group scopes read
  GUEST        — unauthenticated; public read-only

Capability vs Scope separation:
  Capability — what a client can DO  (managed by Role → AccessPolicy)
  Scope      — what a client can SEE (managed by group memberships in IdentityManager)

Group system:
  - Groups are identified by string IDs (e.g. "architects", "history_lab")
  - Group knowledge lives in scope:group_<id> / view:group_<id>
  - Group atoms are NOT visible in scope:sys:universal (collective knowledge)
  - Only group participants can read group atoms
  - GROUP_ADMIN and group-level LIBRARIANs can write to group scope
  - GROUP_ADMIN can add/remove members and grant/revoke group-level librarian rights
  - GROUP_ADMIN cannot read personal atoms of group members

[PERSISTENCE]
All human user and group records are stored in the shared nucleus.db under
category "iam".  System-process identities (system.jataka, system.librarian)
remain as compile-time constants and are never editable via user management.

nucleus table schema (category="iam"):
  identifier "user:<client_id>"  → {"role","passphrase_hash","display_name",
                                     "created_at","created_by","active"}
  identifier "group:<group_id>"  → {"admin","members":[],"librarians":[]}
"""
from enum import Enum
from typing import Dict, Any, Optional, List, Set
from datetime import datetime, timezone
import secrets
import time
import base64
import hmac
import hashlib


# ---------------------------------------------------------------------------
# System-process identities — internal services, never editable via user mgmt
# ---------------------------------------------------------------------------

_SYSTEM_IDENTITIES: Dict[str, "Role"] = {}   # populated after Role is defined


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Capability(Enum):
    READ              = "read"
    WRITE             = "write"
    DELETE            = "delete"
    COLLECTIVE_WRITE  = "collective_write"
    GROUP_MANAGE      = "group_manage"
    SYNC_PULL         = "sync_pull"
    SYNC_PUSH         = "sync_push"
    FEDERATE          = "federate"
    DELEGATE          = "delegate"
    SIMULATE          = "simulate"
    TELEMETRY         = "telemetry"


class Role(Enum):
    GUEST        = "guest"
    USER         = "user"
    LIBRARIAN    = "librarian"
    GROUP_ADMIN  = "group_admin"
    ADMIN        = "admin"


# Populate after Role is defined
_SYSTEM_IDENTITIES.update({
    "system.jataka":    Role.ADMIN,
    "system.librarian": Role.LIBRARIAN,
    "system.weaver":    Role.LIBRARIAN,   # post-write Weaver jobs run under this identity
})


# ---------------------------------------------------------------------------
# Access policies
# ---------------------------------------------------------------------------

class AccessPolicy:
    """Accumulates capabilities for a Role."""
    def __init__(self, name: str):
        self.name = name
        self.capabilities: Set[Capability] = set()
        self.max_depth: int = 2
        self.max_nodes: int = 50

    def grant(self, cap: Capability) -> "AccessPolicy":
        self.capabilities.add(cap)
        return self

    def set_quota(self, depth: int, nodes: int) -> "AccessPolicy":
        self.max_depth = depth
        self.max_nodes = nodes
        return self

    def has(self, cap: Capability) -> bool:
        return cap in self.capabilities


def build_guest_policy() -> AccessPolicy:
    return AccessPolicy("Guest").grant(Capability.READ).set_quota(2, 50)

def build_user_policy() -> AccessPolicy:
    return (AccessPolicy("User")
            .grant(Capability.READ)
            .grant(Capability.WRITE)
            .grant(Capability.DELETE)
            .grant(Capability.SIMULATE)
            .grant(Capability.SYNC_PULL)
            .set_quota(10, 1000))

def build_librarian_policy() -> AccessPolicy:
    """
    Collective knowledge editor.
    Can write to scope:sys:universal, but has NO access to personal atoms of
    other users and NO access to DNA-level system atoms (scope:sys:dna).
    """
    return (AccessPolicy("Librarian")
            .grant(Capability.READ)
            .grant(Capability.WRITE)
            .grant(Capability.DELETE)
            .grant(Capability.COLLECTIVE_WRITE)
            .grant(Capability.SIMULATE)
            .grant(Capability.SYNC_PULL)
            .grant(Capability.SYNC_PUSH)
            .grant(Capability.FEDERATE)
            .set_quota(20, 5000))

def build_group_admin_policy() -> AccessPolicy:
    """
    Group administrator.
    Manages one group: add/remove members, grant group-level librarian rights.
    Can write to the group's shared scope.
    Cannot access personal atoms of group members or collective knowledge.
    """
    return (AccessPolicy("GroupAdmin")
            .grant(Capability.READ)
            .grant(Capability.WRITE)
            .grant(Capability.DELETE)
            .grant(Capability.GROUP_MANAGE)
            .grant(Capability.SIMULATE)
            .grant(Capability.SYNC_PULL)
            .set_quota(15, 2000))

def build_admin_policy() -> AccessPolicy:
    policy = AccessPolicy("Administrator")
    for cap in Capability:
        policy.grant(cap)
    return policy.set_quota(99, 9999)


# ---------------------------------------------------------------------------
# GuestBindingStore
# ---------------------------------------------------------------------------

class GuestBindingStore:
    """
    Self-verifying guest binding tokens.  No server-side state required.

    Token format:
      gbk:<base64url(session_id|expires_at|nonce)>.<base64url(HMAC-SHA256)>

    Any process holding the HMAC secret can verify any token without shared
    memory — Lambda invocations are fully independent.  Cut the HTTP connection
    immediately after each call; the next call is verified from scratch.

    The HMAC secret is loaded from / persisted to nucleus.db on first use.
    If nucleus is unavailable the secret is ephemeral (single-process only).

    Session context (e.g. curation_return_point) lives in the Akasha semantic
    session, not in this store.
    """

    _PREFIX      = "gbk:"
    _DEFAULT_TTL = 1800
    _SEP         = "|"   # field separator — never appears in session_id, float, or hex

    def __init__(self, nucleus_fn=None):
        self._secret_bytes: Optional[bytes] = None
        self._nucleus_fn = nucleus_fn

    # ── Secret management ─────────────────────────────────────────────────────

    def _secret(self) -> bytes:
        """Load or generate the HMAC secret (lazy, persisted to nucleus.db)."""
        if self._secret_bytes is not None:
            return self._secret_bytes
        n = self._nucleus_fn() if self._nucleus_fn else None
        if n:
            stored = n.vault_retrieve("system", "guest_binding_secret")
            if stored:
                self._secret_bytes = bytes.fromhex(stored)
                return self._secret_bytes
            new_key = secrets.token_bytes(32)
            n.vault_store("system", "guest_binding_secret", new_key.hex())
            self._secret_bytes = new_key
            return self._secret_bytes
        # No nucleus — ephemeral secret (not Lambda-safe across cold starts)
        self._secret_bytes = secrets.token_bytes(32)
        return self._secret_bytes

    # ── Token encode / decode ─────────────────────────────────────────────────

    def _sign(self, payload: str) -> str:
        raw = hmac.new(self._secret(), payload.encode(), hashlib.sha256).digest()
        return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()

    def _encode(self, session_id: str, expires_at: float, nonce: str) -> str:
        payload = self._SEP.join([session_id, f"{expires_at:.3f}", nonce])
        b64     = base64.urlsafe_b64encode(payload.encode()).rstrip(b"=").decode()
        return self._PREFIX + b64 + "." + self._sign(payload)

    def _decode_verify(self, key: str) -> tuple:
        """Decode + HMAC-verify. Returns (session_id, expires_at) or raises PermissionError."""
        if not self.is_guest_key(key):
            raise PermissionError("Not a guest binding key.")
        try:
            inner    = key[len(self._PREFIX):]
            b64, sig = inner.rsplit(".", 1)
            pad      = (-len(b64)) % 4
            payload  = base64.urlsafe_b64decode(b64 + "=" * pad).decode()
            if not hmac.compare_digest(sig, self._sign(payload)):
                raise PermissionError("Guest binding: signature mismatch.")
            session_id, exp_str, _nonce = payload.split(self._SEP, 2)
            return session_id, float(exp_str)
        except PermissionError:
            raise
        except Exception:
            raise PermissionError("Guest binding: malformed token.")

    # ── Public API ────────────────────────────────────────────────────────────

    def create(self, ttl: int = _DEFAULT_TTL) -> dict:
        """Issue a new guest binding token.  No storage written."""
        session_id = "guest:" + secrets.token_hex(20)
        expires_at = time.time() + ttl
        key        = self._encode(session_id, expires_at, secrets.token_hex(8))
        return {"binding_key": key, "session_id": session_id, "expires_at": expires_at}

    def create_for_session(self, session_id: str, ttl: int = _DEFAULT_TTL) -> dict:
        """Issue a token bound to a specific session_id (e.g. a pool slot)."""
        expires_at = time.time() + ttl
        key        = self._encode(session_id, expires_at, secrets.token_hex(8))
        return {"binding_key": key, "session_id": session_id, "expires_at": expires_at}

    def resolve(self, key: str) -> str:
        """Verify token → return Akasha session_id.  No storage lookup."""
        session_id, expires_at = self._decode_verify(key)
        if time.time() > expires_at:
            raise PermissionError("Guest binding has expired.")
        return session_id

    def extend(self, key: str, ttl: int = _DEFAULT_TTL) -> dict:
        """
        Issue a replacement token for the same session with a fresh TTL.
        Both the old and new tokens remain cryptographically valid until their
        respective expiry times; the client should switch to the new key.
        """
        session_id, expires_at = self._decode_verify(key)
        if time.time() > expires_at:
            raise PermissionError("Guest binding has expired.")
        new_expires = time.time() + ttl
        new_key     = self._encode(session_id, new_expires, secrets.token_hex(8))
        return {"binding_key": new_key, "session_id": session_id, "expires_at": new_expires}

    def is_guest_key(self, token: str) -> bool:
        """True if the token carries the guest binding prefix."""
        return isinstance(token, str) and token.startswith(self._PREFIX)

    def purge_expired(self) -> int:
        """No-op: self-verifying tokens carry no server-side state to purge."""
        return 0


# ---------------------------------------------------------------------------
# IdentityManager
# ---------------------------------------------------------------------------

class IdentityManager:
    """
    Manages authentication, capability-based authorization, and scope generation.
    All user records are persisted in nucleus.db under category "iam".
    """

    def __init__(self, series_name: str = "seeds", nucleus_path: str = None,
                 nucleus=None):
        self.series_name = series_name.lower()
        self._nucleus_path = nucleus_path
        # Accept a pre-built NucleusEngine (shared instance from AkashaManager)
        # so IAM and sessions share exactly one WriteQueue for nucleus.db.
        self._nucleus_engine = nucleus  # None → lazy-loaded on first use

        self._policies: Dict[Role, AccessPolicy] = {
            Role.GUEST:       build_guest_policy(),
            Role.USER:        build_user_policy(),
            Role.LIBRARIAN:   build_librarian_policy(),
            Role.GROUP_ADMIN: build_group_admin_policy(),
            Role.ADMIN:       build_admin_policy(),
        }

        # In-memory cache: client_id → record dict (populated from nucleus on init)
        self._cache: Dict[str, dict] = {}

        # Group state (mirrored from nucleus)
        self._group_members:   Dict[str, List[str]] = {}
        self._group_admins:    Dict[str, str]        = {}
        self._group_librarians: Dict[str, List[str]] = {}

        # Guest binding store: self-verifying tokens, no server-side state
        self._guest_bindings = GuestBindingStore(nucleus_fn=self._nucleus)

        if nucleus_path or nucleus:
            self._load_all()

    # ── Nucleus access ────────────────────────────────────────────────────────

    def _nucleus(self):
        if self._nucleus_engine is None and self._nucleus_path:
            from lib.akasha.composite import NucleusEngine
            self._nucleus_engine = NucleusEngine(self._nucleus_path)
        return self._nucleus_engine

    # ── Boot-time load ────────────────────────────────────────────────────────

    def _load_all(self):
        """Load all IAM state from nucleus into in-memory structures."""
        n = self._nucleus()
        if n is None:
            return
        # Users
        for ident, record in n.vault_scan("iam", prefix="user:"):
            client_id = ident[5:]   # strip "user:"
            if record.get("active", True):
                self._cache[client_id] = record
        # Groups
        for ident, record in n.vault_scan("iam", prefix="group:"):
            group_id = ident[6:]    # strip "group:"
            self._group_admins[group_id]    = record.get("admin", "")
            self._group_members[group_id]   = record.get("members", [])
            self._group_librarians[group_id] = record.get("librarians", [])
        # Migrate genesis admin if not yet in IAM records
        self._migrate_genesis()

    def _migrate_genesis(self):
        """One-time migration: lift genesis admin from system vault into IAM records."""
        n = self._nucleus()
        if n is None:
            return
        admin_name     = n.vault_retrieve("system", "admin_name")
        passphrase_hash = n.vault_retrieve("system", "passphrase_hash")
        if not admin_name:
            return
        # Register the named admin (e.g. "henri")
        if admin_name not in self._cache:
            record = _make_user_record(Role.ADMIN, passphrase_hash, admin_name, "genesis")
            self._cache[admin_name] = record
            n.vault_store("iam", f"user:{admin_name}", record)
        # Also register the canonical "admin" alias used by automation
        if "admin" not in self._cache:
            record = _make_user_record(Role.ADMIN, passphrase_hash, "admin", "genesis")
            self._cache["admin"] = record
            n.vault_store("iam", "user:admin", record)

    # ── Internal persistence helpers ──────────────────────────────────────────

    def _save_user(self, client_id: str, record: dict):
        n = self._nucleus()
        if n:
            n.vault_store("iam", f"user:{client_id}", record)
        self._cache[client_id] = record

    def _save_group(self, group_id: str):
        n = self._nucleus()
        if n:
            n.vault_store("iam", f"group:{group_id}", {
                "admin":     self._group_admins.get(group_id, ""),
                "members":   self._group_members.get(group_id, []),
                "librarians": self._group_librarians.get(group_id, []),
            })

    # ── Authentication ────────────────────────────────────────────────────────

    @property
    def guest_bindings(self) -> GuestBindingStore:
        """Access the guest binding store (HTTP key ↔ Akasha session mapping)."""
        return self._guest_bindings

    def authenticate(self, client_id: str, token: Optional[str] = None) -> Role:
        # Ephemeral guest session IDs are Akasha-internal identities resolved
        # from a guest binding key by the kernel before this call.
        if client_id.startswith("guest:"):
            return Role.GUEST
        if client_id in _SYSTEM_IDENTITIES:
            return _SYSTEM_IDENTITIES[client_id]
        record = self._cache.get(client_id)
        if record and record.get("active", True):
            return Role(record["role"])
        if self.series_name == "thesaurus":
            return Role.GUEST
        raise PermissionError(f"Access Denied: Identity '{client_id}' is unknown.")

    # ── Passphrase verification ───────────────────────────────────────────────

    def verify_passphrase(self, client_id: str, passphrase_hash: str) -> bool:
        """
        Verify a SHA-256 passphrase hash against the stored record.
        Falls back to the legacy genesis system vault for backward compatibility.
        """
        record = self._cache.get(client_id)
        if record:
            stored = record.get("passphrase_hash")
            if stored:
                return stored == passphrase_hash
        # Fallback: legacy single-hash vault entry (pre-persistence installs)
        n = self._nucleus()
        if n:
            stored = n.vault_retrieve("system", "passphrase_hash")
            if stored:
                return stored == passphrase_hash
        return False

    # ── User CRUD ─────────────────────────────────────────────────────────────

    def register_client(self, client_id: str, role: Role,
                        passphrase_hash: str = None, created_by: str = "admin",
                        display_name: str = None) -> dict:
        """Register a new human user. Raises ValueError for system identities."""
        if client_id in _SYSTEM_IDENTITIES:
            raise ValueError(f"'{client_id}' is a reserved system identity.")
        record = _make_user_record(role, passphrase_hash, display_name or client_id, created_by)
        self._save_user(client_id, record)
        return record

    def deregister_client(self, client_id: str):
        """Soft-delete a user (marks active=False, removes from cache)."""
        if client_id in _SYSTEM_IDENTITIES:
            raise ValueError(f"'{client_id}' is a reserved system identity.")
        record = self._cache.get(client_id)
        if not record:
            raise KeyError(f"Identity '{client_id}' not found.")
        record["active"] = False
        n = self._nucleus()
        if n:
            n.vault_store("iam", f"user:{client_id}", record)
        del self._cache[client_id]

    def set_passphrase(self, client_id: str, passphrase_hash: str):
        """Update a user's passphrase hash."""
        if client_id in _SYSTEM_IDENTITIES:
            raise ValueError(f"Cannot change passphrase of system identity '{client_id}'.")
        record = self._cache.get(client_id)
        if not record:
            raise KeyError(f"Identity '{client_id}' not found.")
        record["passphrase_hash"] = passphrase_hash
        self._save_user(client_id, record)

    def set_role(self, client_id: str, role: Role):
        """Change a user's role."""
        if client_id in _SYSTEM_IDENTITIES:
            raise ValueError(f"Cannot change role of system identity '{client_id}'.")
        record = self._cache.get(client_id)
        if not record:
            raise KeyError(f"Identity '{client_id}' not found.")
        record["role"] = role.value
        self._save_user(client_id, record)

    def list_clients(self) -> List[dict]:
        """Return all active human users (excludes system identities)."""
        return [{"client_id": cid, **rec}
                for cid, rec in sorted(self._cache.items())
                if rec.get("active", True)]

    def get_client(self, client_id: str) -> Optional[dict]:
        """Return a single user record (None if not found)."""
        return self._cache.get(client_id)

    def get_onboarded_apps(self, client_id: str) -> List[str]:
        """Return the list of app names already seeded for this user."""
        record = self._cache.get(client_id)
        if not record:
            return []
        return list(record.get("onboarded_apps", []))

    def mark_onboarded(self, client_id: str, app_name: str) -> None:
        """Record that app_name has been seeded for this user."""
        record = self._cache.get(client_id)
        if not record:
            return
        apps = list(record.get("onboarded_apps", []))
        if app_name not in apps:
            apps.append(app_name)
            record["onboarded_apps"] = apps
            self._save_user(client_id, record)

    # ── Scope generation ──────────────────────────────────────────────────────

    def get_allowed_scopes(self, client_id: str, role: Role) -> List[str]:
        """
        Returns the scope prefixes this client may access.
        The Cortex uses this list to filter graph traversals at the DB level.

        Scope taxonomy:
          scope:sys:universal   — collective public knowledge (all roles read)
          scope:sys:dna         — innate DNA memory (ADMIN read only)
          view:public           — publicly visible atoms
          owner:user_X          — private ownership marker for client X
          view:user_X           — private read scope for client X
          scope:group_G         — group G's shared knowledge
          view:group_G          — group G read access marker
          manage:group_G        — group G management rights (GROUP_ADMIN only)
          view:admin_override   — ADMIN can see pending/capsule atoms
        """
        scopes = ["scope:sys:universal", "view:public"]

        if role == Role.GUEST:
            return scopes

        scopes += [f"owner:user_{client_id}", f"view:user_{client_id}"]

        if role in (Role.LIBRARIAN, Role.ADMIN):
            scopes += ["scope:sys:collective", "role:librarian"]

        if role == Role.ADMIN:
            scopes += ["view:admin_override", "scope:sys:dna",
                       "role:superuser", "scope:sys:admin"]

        for group_id, members in self._group_members.items():
            if client_id in members:
                scopes += [f"scope:group_{group_id}", f"view:group_{group_id}"]

        for group_id, admin_id in self._group_admins.items():
            if admin_id == client_id:
                scopes += [f"scope:group_{group_id}", f"view:group_{group_id}",
                           f"manage:group_{group_id}"]

        for group_id, libs in self._group_librarians.items():
            if client_id in libs:
                scopes += [f"scope:group_{group_id}", f"view:group_{group_id}",
                           f"write:group_{group_id}"]

        return list(dict.fromkeys(scopes))

    def get_client_groups(self, client_id: str) -> List[str]:
        """Return all group IDs the client belongs to (member, admin, or librarian)."""
        seen: dict = {}
        for gid, members in self._group_members.items():
            if client_id in members:
                seen[gid] = True
        for gid, admin in self._group_admins.items():
            if admin == client_id:
                seen[gid] = True
        for gid, libs in self._group_librarians.items():
            if client_id in libs:
                seen[gid] = True
        return list(seen.keys())

    # ── Group management ──────────────────────────────────────────────────────

    def create_group(self, group_id: str, admin_client_id: str):
        """Create a group and assign its administrator."""
        self._group_admins[group_id] = admin_client_id
        if group_id not in self._group_members:
            self._group_members[group_id] = []
        if admin_client_id not in self._group_members[group_id]:
            self._group_members[group_id].append(admin_client_id)
        if admin_client_id not in self._cache and admin_client_id not in _SYSTEM_IDENTITIES:
            self.register_client(admin_client_id, Role.GROUP_ADMIN, created_by="system")
        self._save_group(group_id)

    def delete_group(self, group_id: str):
        """Remove a group entirely."""
        for d in (self._group_admins, self._group_members, self._group_librarians):
            d.pop(group_id, None)
        n = self._nucleus()
        if n:
            n.vault_delete("iam", f"group:{group_id}")

    def add_group_member(self, group_id: str, requester_id: str, new_member_id: str):
        """Add a client to a group (requester must be group admin or ADMIN)."""
        self._assert_group_manager(group_id, requester_id)
        if group_id not in self._group_members:
            self._group_members[group_id] = []
        if new_member_id not in self._group_members[group_id]:
            self._group_members[group_id].append(new_member_id)
        self._save_group(group_id)

    def remove_group_member(self, group_id: str, requester_id: str, member_id: str):
        """Remove a client from a group (cannot remove the group admin)."""
        self._assert_group_manager(group_id, requester_id)
        if self._group_admins.get(group_id) == member_id:
            raise PermissionError("Cannot remove the group administrator.")
        if group_id in self._group_members:
            self._group_members[group_id] = [
                m for m in self._group_members[group_id] if m != member_id
            ]
        if group_id in self._group_librarians:
            self._group_librarians[group_id] = [
                m for m in self._group_librarians[group_id] if m != member_id
            ]
        self._save_group(group_id)

    def grant_group_librarian(self, group_id: str, requester_id: str, target_id: str):
        """Grant group-level librarian rights to a group member."""
        self._assert_group_manager(group_id, requester_id)
        if target_id not in self._group_members.get(group_id, []):
            raise PermissionError(f"'{target_id}' is not a member of group '{group_id}'.")
        if group_id not in self._group_librarians:
            self._group_librarians[group_id] = []
        if target_id not in self._group_librarians[group_id]:
            self._group_librarians[group_id].append(target_id)
        self._save_group(group_id)

    def revoke_group_librarian(self, group_id: str, requester_id: str, target_id: str):
        """Revoke group-level librarian rights."""
        self._assert_group_manager(group_id, requester_id)
        if group_id in self._group_librarians:
            self._group_librarians[group_id] = [
                m for m in self._group_librarians[group_id] if m != target_id
            ]
        self._save_group(group_id)

    def list_groups(self) -> List[dict]:
        """Return all group records."""
        return [
            {
                "group_id": gid,
                "admin": self._group_admins.get(gid, ""),
                "members": self._group_members.get(gid, []),
                "librarians": self._group_librarians.get(gid, []),
            }
            for gid in sorted(self._group_admins.keys())
        ]

    def get_group(self, group_id: str) -> Optional[dict]:
        if group_id not in self._group_admins:
            return None
        return {
            "group_id": group_id,
            "admin": self._group_admins[group_id],
            "members": self._group_members.get(group_id, []),
            "librarians": self._group_librarians.get(group_id, []),
        }

    def get_client_groups(self, client_id: str) -> List[str]:
        return [g for g, members in self._group_members.items() if client_id in members]

    # ── Authorization ─────────────────────────────────────────────────────────

    def authorize(self, role: Role, action: str, params: dict = None) -> bool:
        """Evaluates if a Role has the Capability to execute an action."""
        if params is None:
            params = {}
        policy = self._policies.get(role, self._policies[Role.GUEST])

        if action in ("read", "explore", "network.tree", "sys.history",
                      "link.list", "dive.look", "dive.out"):
            if not policy.has(Capability.READ):
                return False
            req_depth = int(params.get("depth", params.get("scope", 1)))
            if req_depth > policy.max_depth:
                raise PermissionError(
                    f"Quota exceeded: depth {req_depth} > {policy.max_depth}"
                )
            return True

        if action in ("write", "define", "link.create", "meta.set",
                      "node.virt", "note.new", "note.add"):
            return policy.has(Capability.WRITE)

        if action in ("collective.write",):
            return policy.has(Capability.COLLECTIVE_WRITE)

        if action in ("drop", "rm", "node.evict", "note.remove"):
            return policy.has(Capability.DELETE)

        if action in ("sync.push", "sync.pull", "kw.sync",
                      "sys.encapsulate", "sys.decapsulate"):
            return policy.has(Capability.SYNC_PUSH) or policy.has(Capability.SYNC_PULL)

        if action in ("kw.verify", "sys.crystallize", "sys.delegate"):
            return policy.has(Capability.DELEGATE) or policy.has(Capability.FEDERATE)

        if action in ("group.manage",):
            return policy.has(Capability.GROUP_MANAGE)

        if action in ("dream", "jataka.dream", "link.reinforce"):
            return policy.has(Capability.SIMULATE)

        if action in ("sys.telemetry",):
            return policy.has(Capability.TELEMETRY)

        if action in ("jcl.execute", "job.submit"):
            return policy.has(Capability.WRITE)

        if action in ("jcl.admin",):
            return policy.has(Capability.DELEGATE)

        if action in ("echo", "help", "status", "ping"):
            return True

        return False

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _assert_group_manager(self, group_id: str, requester_id: str):
        role = Role.GUEST
        if requester_id in _SYSTEM_IDENTITIES:
            role = _SYSTEM_IDENTITIES[requester_id]
        elif requester_id in self._cache:
            role = Role(self._cache[requester_id]["role"])
        if role == Role.ADMIN:
            return
        if self._group_admins.get(group_id) == requester_id:
            return
        raise PermissionError(
            f"'{requester_id}' is not authorized to manage group '{group_id}'."
        )


# ---------------------------------------------------------------------------
# Module-level helper
# ---------------------------------------------------------------------------

def _make_user_record(role: Role, passphrase_hash: Optional[str],
                      display_name: str, created_by: str) -> dict:
    return {
        "role":            role.value,
        "passphrase_hash": passphrase_hash,
        "display_name":    display_name,
        "created_at":      datetime.now(timezone.utc).isoformat(),
        "created_by":      created_by,
        "active":          True,
        "onboarded_apps":  [],
    }
