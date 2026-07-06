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
    IAM_MANAGE        = "iam_manage"   # create/modify/delete users (ADMIN only)
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
    Self-verifying session tokens.  No server-side state required for signing.

    Two token classes share one HMAC secret and one verification path:

      gbk:<base64url(session_id|expires_at|nonce)>.<HMAC>
          Guest binding — session_id is always a "guest:" identity, role is
          implicitly GUEST.  Issued by session.guest.create/extend.

      akt:<base64url(client_id|role|expires_at|epoch|nonce)>.<HMAC>
          Authenticated session token — minted by auth.verify AFTER a passphrase
          check.  Carries the verified identity, its role, and a per-user epoch
          used for revocation.  This is what replaces the old "the username is
          the token" model: over an untrusted transport an identity is proven by
          possession of this signed token, never by asserting a bare client_id.

    Any process holding the HMAC secret can verify any token without shared
    memory — Lambda invocations are fully independent.  Cut the HTTP connection
    immediately after each call; the next call is verified from scratch.

    The HMAC secret is loaded from / persisted to nucleus.db on first use.
    If nucleus is unavailable the secret is ephemeral (single-process only).

    Session context (e.g. curation_return_point) lives in the Akasha semantic
    session, not in this store.
    """

    _PREFIX      = "gbk:"
    _AUTH_PREFIX = "akt:"
    _DEFAULT_TTL = 1800
    _SEP         = "|"   # field separator — never appears in session_id, float, or hex

    def __init__(self, nucleus_fn=None):
        self._secret_bytes: Optional[bytes] = None
        self._nucleus_fn = nucleus_fn

    # ── Secret management ─────────────────────────────────────────────────────

    def _secret(self) -> bytes:
        """Load or generate the HMAC secret (lazy, persisted to nucleus.db).

        Precedence: AKASHA_SECRET env var (hex or raw) > nucleus vault > ephemeral.
        The env override lets a networked/multi-host deployment supply the signing
        key out-of-band instead of trusting whatever is persisted in nucleus.db.

        ┌─ POST-LAUNCH PRIORITY #1 (networked / multi-host deploys) ───────────────┐
        │ This key signs EVERY guest (gbk:) and authenticated (akt:) session token. │
        │ Anyone who can read it can forge a token for ANY identity, incl. admin.   │
        │ For any deployment reachable over the network, set AKASHA_SECRET to a      │
        │ strong random value (e.g. `python -c "import secrets;print(secrets.       │
        │ token_hex(32))"`) supplied out-of-band (env / secrets manager), and keep   │
        │ it IDENTICAL across all hosts so tokens verify everywhere. Do NOT rely on  │
        │ the nucleus-vault fallback in production: it persists the key inside       │
        │ nucleus.db (0600, but still on disk) and each host would mint its own.     │
        │ A single local single-user Cell may keep the vault fallback. See CLAUDE.md │
        │ "Security Model → Post-launch priorities" and the tracking GitHub issue.  │
        └──────────────────────────────────────────────────────────────────────────┘
        """
        if self._secret_bytes is not None:
            return self._secret_bytes
        import os as _os
        env_secret = _os.environ.get("AKASHA_SECRET")
        if env_secret:
            try:
                self._secret_bytes = bytes.fromhex(env_secret)
            except ValueError:
                self._secret_bytes = hashlib.sha256(env_secret.encode()).digest()
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

    # ── Authenticated session tokens (akt:) ───────────────────────────────────

    def is_auth_key(self, token: str) -> bool:
        """True if the token carries the authenticated session-token prefix."""
        return isinstance(token, str) and token.startswith(self._AUTH_PREFIX)

    def mint_auth(self, client_id: str, role_value: str, epoch: int,
                  ttl: int = _DEFAULT_TTL) -> dict:
        """
        Issue a signed authenticated session token.  Caller (IdentityManager)
        must have already verified the passphrase.  No storage is written; the
        token is self-verifying via HMAC.
        """
        if self._SEP in client_id:
            raise ValueError("client_id must not contain the token separator.")
        expires_at = time.time() + ttl
        payload = self._SEP.join(
            [client_id, role_value, f"{expires_at:.3f}", str(int(epoch)), secrets.token_hex(8)]
        )
        b64 = base64.urlsafe_b64encode(payload.encode()).rstrip(b"=").decode()
        token = self._AUTH_PREFIX + b64 + "." + self._sign(payload)
        return {"session_token": token, "expires_at": expires_at}

    def decode_auth(self, token: str) -> tuple:
        """
        Decode + HMAC-verify an akt: token.
        Returns (client_id, role_value, expires_at, epoch) or raises PermissionError.
        Signature is checked with a constant-time compare before any field is trusted.
        """
        if not self.is_auth_key(token):
            raise PermissionError("Not an authenticated session token.")
        try:
            inner    = token[len(self._AUTH_PREFIX):]
            b64, sig = inner.rsplit(".", 1)
            pad      = (-len(b64)) % 4
            payload  = base64.urlsafe_b64decode(b64 + "=" * pad).decode()
            if not hmac.compare_digest(sig, self._sign(payload)):
                raise PermissionError("Session token: signature mismatch.")
            client_id, role_value, exp_str, epoch_str, _nonce = payload.split(self._SEP, 4)
            return client_id, role_value, float(exp_str), int(epoch_str)
        except PermissionError:
            raise
        except Exception:
            raise PermissionError("Session token: malformed.")


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
        # Register the named admin (e.g. "henri"). The legacy vault hash is a
        # presented SHA-256; seal it into salted PBKDF2 at migration time.
        if admin_name not in self._cache:
            record = _make_user_record(Role.ADMIN, None, admin_name, "genesis")
            if passphrase_hash:
                record.update(self._seal_passphrase(passphrase_hash))
            self._cache[admin_name] = record
            n.vault_store("iam", f"user:{admin_name}", record)
        # Also register the canonical "admin" alias used by automation
        if "admin" not in self._cache:
            record = _make_user_record(Role.ADMIN, None, "admin", "genesis")
            if passphrase_hash:
                record.update(self._seal_passphrase(passphrase_hash))
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

    def is_system_identity(self, client_id: str) -> bool:
        """True if client_id is a compile-time system process identity.

        These (system.jataka / system.librarian / system.weaver) are internal
        services with no passphrase.  They must never be reachable as a login
        over an untrusted transport — only kernel-internal (TRUST_INTERNAL)
        callers may act as them.
        """
        return client_id in _SYSTEM_IDENTITIES

    # ── Session tokens (akt:) — proof-of-identity for untrusted transports ─────

    def issue_session_token(self, client_id: str, ttl: int = 1800) -> dict:
        """
        Mint a signed session token for an already-authenticated identity.
        The caller (auth.verify) is responsible for the passphrase check first.
        Returns {"session_token": "akt:...", "expires_at": float}.
        """
        record = self._cache.get(client_id)
        if not record or not record.get("active", True):
            raise PermissionError(f"Cannot issue token for unknown identity '{client_id}'.")
        epoch = int(record.get("token_epoch", 0))
        return self._guest_bindings.mint_auth(client_id, record["role"], epoch, ttl)

    def resolve_session_token(self, token: str) -> tuple:
        """
        Verify an akt: token → (client_id, Role).  Raises PermissionError on
        bad signature, expiry, unknown/inactive identity, or a stale epoch
        (token revoked).  The authoritative role is the identity's CURRENT role,
        not the value embedded in the token, so a role change takes effect at once.
        """
        client_id, _role_value, expires_at, epoch = self._guest_bindings.decode_auth(token)
        if time.time() > expires_at:
            raise PermissionError("Session token has expired.")
        record = self._cache.get(client_id)
        if not record or not record.get("active", True):
            raise PermissionError("Session token: unknown or inactive identity.")
        if int(record.get("token_epoch", 0)) != epoch:
            raise PermissionError("Session token has been revoked.")
        return client_id, Role(record["role"])

    def revoke_sessions(self, client_id: str) -> None:
        """Invalidate all outstanding session tokens for a user (logout-all).

        Bumps the user's token_epoch so every previously minted akt: token fails
        the epoch check in resolve_session_token.  Also called automatically on
        passphrase change and role change.
        """
        record = self._cache.get(client_id)
        if not record:
            return
        record["token_epoch"] = int(record.get("token_epoch", 0)) + 1
        self._save_user(client_id, record)

    # ── Passphrase hashing & verification ─────────────────────────────────────
    #
    # Wire convention: clients transmit a client-side SHA-256 of the passphrase
    # ("presented hash").  The server never sees the raw passphrase for user.*
    # management calls.  At rest we do NOT store that presented hash directly —
    # it would be an unsalted single-round SHA-256 (rainbow-table friendly, and
    # identical passphrases collide across users).  Instead we stretch it with a
    # per-user-salted PBKDF2-HMAC-SHA256 and compare in constant time.

    _KDF_ITER = 200_000
    _KDF_NAME = "pbkdf2_sha256_200k"

    @staticmethod
    def _kdf(presented_hash: str, salt_hex: str) -> str:
        return hashlib.pbkdf2_hmac(
            "sha256", presented_hash.encode("utf-8"),
            bytes.fromhex(salt_hex), IdentityManager._KDF_ITER,
        ).hex()

    def _seal_passphrase(self, presented_hash: str) -> dict:
        """Salt + stretch a presented hash into the fields stored on a record."""
        salt = secrets.token_hex(16)
        return {
            "passphrase_hash": self._kdf(presented_hash, salt),
            "salt":            salt,
            "kdf":             self._KDF_NAME,
        }

    def verify_passphrase(self, client_id: str, presented_hash: str) -> bool:
        """
        Verify a presented (client-side SHA-256) passphrase hash.
        Salted PBKDF2 records are compared in constant time.  Legacy unsalted
        records (and the legacy genesis vault entry) are still accepted and are
        transparently upgraded to salted PBKDF2 on the next successful login.
        """
        if not presented_hash:
            return False
        record = self._cache.get(client_id)
        if record and record.get("passphrase_hash"):
            stored = record["passphrase_hash"]
            salt   = record.get("salt")
            kdf    = record.get("kdf")
            if kdf == self._KDF_NAME and salt:
                return hmac.compare_digest(stored, self._kdf(presented_hash, salt))
            # Legacy unsalted record — accept, then upgrade in place (no epoch bump:
            # the credential is unchanged, so outstanding tokens stay valid).
            if hmac.compare_digest(stored, presented_hash):
                try:
                    record.update(self._seal_passphrase(presented_hash))
                    self._save_user(client_id, record)
                except Exception:
                    pass
                return True
            return False
        # Fallback: legacy single-hash vault entry (pre-persistence installs)
        n = self._nucleus()
        if n:
            stored = n.vault_retrieve("system", "passphrase_hash")
            if stored:
                return hmac.compare_digest(stored, presented_hash)
        return False

    # ── User CRUD ─────────────────────────────────────────────────────────────

    def register_client(self, client_id: str, role: Role,
                        passphrase_hash: str = None, created_by: str = "admin",
                        display_name: str = None) -> dict:
        """Register a new human user. Raises ValueError for system identities.

        passphrase_hash is a presented (client-side SHA-256) hash; it is salted
        and stretched with PBKDF2 before storage.
        """
        if client_id in _SYSTEM_IDENTITIES:
            raise ValueError(f"'{client_id}' is a reserved system identity.")
        record = _make_user_record(role, None, display_name or client_id, created_by)
        if passphrase_hash:
            record.update(self._seal_passphrase(passphrase_hash))
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
        record.update(self._seal_passphrase(passphrase_hash))
        # Credential change invalidates every outstanding session token.
        record["token_epoch"] = int(record.get("token_epoch", 0)) + 1
        self._save_user(client_id, record)

    def set_role(self, client_id: str, role: Role):
        """Change a user's role."""
        if client_id in _SYSTEM_IDENTITIES:
            raise ValueError(f"Cannot change role of system identity '{client_id}'.")
        record = self._cache.get(client_id)
        if not record:
            raise KeyError(f"Identity '{client_id}' not found.")
        record["role"] = role.value
        # Role change invalidates outstanding tokens so the old role can't linger.
        record["token_epoch"] = int(record.get("token_epoch", 0)) + 1
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

        if action in ("iam.manage",):
            return policy.has(Capability.IAM_MANAGE)

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
        # Monotonic counter — bumping it invalidates every previously minted
        # session token for this user (logout-all / revoke).  See revoke_sessions.
        "token_epoch":     0,
    }
