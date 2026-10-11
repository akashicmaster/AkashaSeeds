"""Transport trust levels — a property of the SERVER-SIDE transport binding, set by the portal that
received the request, never a value the client can supply. It governs whether a bare client_id may
assert an identity:

    TRUST_NETWORK  (default) — untrusted remote (HTTP/ASGI, web worker, CGI). A privileged identity
                               must prove itself with a signed akt: session token; a bare client_id
                               is only ever accepted as an anonymous GUEST.
    TRUST_LOCAL              — the local operator's stdio console. The OS process boundary is the
                               real gate, so a bare client_id (incl. the admin) is accepted.
    TRUST_INTERNAL           — kernel-originated in-process dispatch (JCL worker, boot loader,
                               self-dispatch). Bare client_id and system.* identities are accepted.
"""
TRUST_NETWORK = "network"
TRUST_LOCAL = "local"
TRUST_INTERNAL = "internal"
TRUSTED_TRANSPORTS = frozenset({TRUST_LOCAL, TRUST_INTERNAL})


# ── system identities, REGISTERED by the module that owns each one (group 4, 4.15) ──────────────
# An internal identity (`system.<name>`) is reachable only over TRUST_INTERNAL / TRUST_LOCAL. The
# heart names its own (the weaver, the librarian, the narrator); every other one is registered at
# load by the module that acts as it — the broadcaster relay, the auto-run moderator and scribe
# belong to the society module and are registered there. The heart used to list them all.
_SYSTEM_IDENTITIES = {}


def system_identity(name: str, role: str) -> None:
    """Register `name` as an internal identity acting under `role` (a Role value: guest, user,
    librarian, group_admin, admin). Idempotent; the last registration of a name wins."""
    if name and role:
        _SYSTEM_IDENTITIES[str(name)] = str(role)


def system_identities() -> dict:
    """name → role value, for every identity a module has registered."""
    return dict(_SYSTEM_IDENTITIES)
