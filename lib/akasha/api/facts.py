"""
THE FACT SETS — step 4 of the gate, as data the world states rather than conditions code carries.

Order: `a7406440-directive-backend-one-gate-2026-09-22.md` §2.

Five Sets. Each has EXACTLY ONE writer, and this module is both the writer's helper and the map
that says who it is, so the answer to "who could have put this key here?" is one file:

    set:wl:declared           the declaration loader, at boot
    set:wl:armed              the driver — declared ∧ provisioned; a tripped breaker removes
    set:source:ready          the source engine, when a workload's required pool freezes
    set:pool:headroom         admission, at reserve and at settle
    set:society:public        `society.public` (and `society.new public=yes`, its create-time spelling)

WHY A SET AND NOT A FLAG. Each of these used to be an `if` at the place that needed the answer —
`_is_public` in society.py, the `pool_frozen` probe in bootstrap.py, `over_allotment` in llm_pool,
`mode`/`boot_pending`/`breaker` in the driver. A flag read by five callers is five chances to read
it differently, and the bug that started this order was exactly that. A Set is stated once by the
one party that knows, and every reader — the gate, a guest, an eval, the guide — gets the same
answer because they are all reading the same membership.

MEMBERSHIP IS THE FACT, ABSENCE IS ITS NEGATION. There is no "false" row: a workload that is not
armed is simply not in `set:wl:armed`. That is what makes `declared ∖ armed` and `declared ∩ armed`
answer the driver's questions in one line each: an undeclared workload is simply not in
`set:wl:declared`, and the gate refuses its run — there is nothing to retire.

These are written to the UNIVERSAL scope, like the `set:wl:*` field Sets they sit beside, so the
guide a guest reads and the decision the gate makes cannot disagree.
"""
import logging
from typing import Any, Dict, Iterable, List, Optional

logger = logging.getLogger("Akasha.Kernel")

# ── the names, and their one writer each ────────────────────────────────────────────────────
DECLARED = "set:wl:declared"
ARMED = "set:wl:armed"
SOURCE_READY = "set:source:ready"
HEADROOM = "set:pool:headroom"
PUBLIC = "set:society:public"

# The map, as data, so an eval can assert it and a reader does not have to grep for it.
WRITERS = {
    DECLARED: "workbench.provision — the declaration loader, at boot",
    ARMED: "workbench.autorun — the driver (declared and provisioned; a breaker removes)",
    SOURCE_READY: "source — the pool freeze",
    HEADROOM: "workbench.llm_pool — admission, at reserve and at settle",
    PUBLIC: "concepts.society — society.public, and society.new public=yes",
}


def _universal(kernel):
    """The universal-scope writer. Returns None when there is no admin session yet (a cell in
    the middle of genesis), which every caller treats as "not now", never as "no"."""
    try:
        from lib.akasha.concepts._universal import UniversalConcept as _UC
        u = _UC(kernel.manager.get_session("admin"))
        u._space = ""
        return u
    except Exception:
        return None


def _atom(u, member: str) -> str:
    """The atom a Set member is. A fact Set holds KEYS — a workload key, a pool name, a
    `<group>/<space>` — so the atom is minted from the key itself and carries nothing else."""
    return u._mk("fact:%s" % member, "[fact:%s] %s" % (member, member),
                 {"concept": "fact", "member": member})


def state(kernel, set_name: str, member: str, present: bool) -> bool:
    """Put `member` in `set_name`, or take it out. The ONE write path for all five Sets.

    Idempotent both ways, and it never raises: a fact that cannot be written is reported and the
    caller carries on — the gate's reader already treats an unreadable Set as "no", so a failed
    write closes a door rather than opening one."""
    u = _universal(kernel)
    if u is None:
        return False
    try:
        k = _atom(u, member)
        if not k:
            return False
        if present:
            u._add_to_set(set_name, k)
        else:
            u._remove_from_set(set_name, k)
        return True
    except Exception as exc:                       # noqa: BLE001 — reported, never silent
        logger.warning("[gate] fact write FAILED set=%s member=%s present=%s reason=%s: %s",
                       set_name, member, present, type(exc).__name__, exc)
        return False


def members(kernel, set_name: str) -> List[str]:
    """What a fact Set holds, as the keys that were put in it. Set algebra on the caller's side
    — `declared ∖ armed` is a one-line answer to "what is provisioned but not running"."""
    u = _universal(kernel)
    if u is None:
        return []
    try:
        out = []
        for k in (u._members(set_name) or []):
            meta = u._meta(k) or {}
            m = meta.get("member")
            out.append(str(m) if m else str(k))
        return sorted(set(out))
    except Exception:
        return []


def has(kernel, set_name: str, member: str) -> bool:
    """The reader the gate is handed. A Set that cannot be read is NOT a grant."""
    try:
        return str(member) in members(kernel, set_name)
    except Exception:
        return False


def install(kernel) -> None:
    """Hand the gate its fact reader. Called once, at boot, by the heart."""
    from lib.akasha.api import gate as _gate
    _gate.set_facts(lambda s, m: has(kernel, s, m))
    logger.info("[gate] facts installed sets=%d", len(WRITERS))


# ── the five writers, each named for the party that knows the fact ──────────────────────────

def declared(kernel, keys: Iterable[str]) -> int:
    """The declaration loader, at boot. RECONCILES: what the files say is what the Set holds,
    so removing a declaration removes the key, and the gate's step 4 refuses its run `declared`."""
    want = sorted(set(str(k) for k in keys if k))
    have = set(members(kernel, DECLARED))
    n = 0
    for k in want:
        if k not in have and state(kernel, DECLARED, k, True):
            n += 1
    for k in sorted(have - set(want)):
        if state(kernel, DECLARED, k, False):
            n += 1
    if n:
        logger.info("[gate] fact set=%s reconciled declared=%d changed=%d",
                    DECLARED, len(want), n)
    return n


def armed(kernel, key: str, is_armed: bool) -> bool:
    """The driver. A workload is armed when it is declared AND provisioned; a tripped breaker
    takes it out. This is the whole of what `mode == "auto"`, `boot_pending` and `breaker` used
    to answer between them, stated once."""
    return state(kernel, ARMED, str(key), bool(is_armed))


def source_ready(kernel, key: str, ready: bool) -> bool:
    """The source engine, at freeze. `pool_frozen()` was a probe every caller ran for itself;
    the pool states it once now, when it becomes true.

    MEMBERS ARE TARGETS, not pool names — the ruling's step 4 asks `target ∈ source_ready`, and
    a Set keyed by the pool would make the GATE resolve a target to its pool, which is knowledge
    about workloads that the gate must not have."""
    return state(kernel, SOURCE_READY, str(key), bool(ready))


def headroom(kernel, key: str, has_room: bool) -> bool:
    """Admission, at reserve and at settle — the two moments the answer can change. Members are
    targets, for the same reason as `source_ready`: admission already holds the workload key it
    is reserving for, so it states the fact about that key."""
    return state(kernel, HEADROOM, str(key), bool(has_room))


def public(kernel, key: str, is_public: bool) -> bool:
    """`society.public`. This is `_is_public`, which read a group atom's meta from inside the
    society concept and could therefore only be asked by something holding that session."""
    return state(kernel, PUBLIC, str(key), bool(is_public))
