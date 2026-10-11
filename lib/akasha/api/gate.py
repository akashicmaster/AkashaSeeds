"""
THE GATE — the one function that decides, and the only one.

Order: `a7406440-directive-backend-one-gate-2026-09-22.md`, on the ruling
`ruling-id-sets-one-gate-2026-09-22.md`: *security lives in one function, or the number of
checks explodes; Sets and intersections are the tool.*

What it replaces: `identity.authorize`, `identity.authorize_effective`, the grants table, and
every `role ==`, `in allowed_scopes`, `"role:librarian" in`, `_owned_cast`, `_pub_nucleus`,
`_is_public`, `mode == "auto"`, `boot_pending`, `breaker`-as-a-condition that used to be spread
across seventy-three files. Each of those was a decision. A decision in seventy-three places is
seventy-three chances to be wrong, and the bug that started this order was exactly that.

    gate(identity, action, target=None, cast=None) -> (ok: bool, reason: str)

Four steps, in this order, and nothing else:

  1. WHICH ID-SETS does this identity hold?   the assignment file's lines for it
  2. MAY they perform this action?            the union of their `may`
  3. ON this target?                          the intersection of their `on` with the target
  4. DO THE FACTS ALLOW IT?                   the fact Sets — declared, armed, ready, headroom,
                                              public — which are data the world writes, not
                                              conditions code carries

A refusal names itself in the vocabulary at the step that decided it, so a caller never has to
guess which of the four said no:

    [gate] refused identity=… action=… target=… reason=<term>

TRANSPORT TRUST IS NOT A PERMISSION. `api.trust` answers *may this caller be believed to be who
it says it is* — a property of the socket the request arrived on. It is never consulted here and
never stands in for a line of the assignment file. The `TRUST_INTERNAL`-only `job.submit` path
that this morning's §1 fix added is deleted by this order for precisely that reason: it made a
transport answer a permission question.

THE STORE STILL ENFORCES. `composite.py` and the backends keep filtering reads and stamping
writes with the scope list the session carries — but they decide nothing. Enforcing a list the
gate produced is the design; comparing a scope to a role, a name or a flag is a second decision
and is gone.
"""
import json
import logging
import os
import threading
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("Akasha.Kernel")

# ── the eight actions, and there are no others ──────────────────────────────────────────────
READ = "read"
SAY = "say"
RUN = "run"
RECORD = "record"
ANNOTATE = "annotate"
PUBLISH = "publish"
PROVISION = "provision"
ADMIN = "admin"

ACTIONS = (READ, SAY, RUN, RECORD, ANNOTATE, PUBLISH, PROVISION, ADMIN)

# The TARGET that names the shared store — the nucleus, the curated catalogue, the ontology.
# It is a target, not a ninth action: `gate(who, RECORD, UNIVERSAL)` is admitted by the two rows
# that reach `*` (admin, librarian) and refused for every row whose line is `on <bench>` or
# `on <group>`, which is the whole of "may this caller write to the collective space". The five
# call sites that each spelled that out as a different scope-string test (`"role:librarian" in
# scopes`, `"role:superuser" in scopes`, `scope:sys:admin`) now ask this one question, so a
# change to who may curate is a change to the table and nothing else.
UNIVERSAL = "universal"

# ── the refusal vocabulary — the ruling's, and there is no other ────────────────────────────
# §4: steps 2 and 3 name themselves; step 4 returns THE NAME OF THE FIRST MISSING FACT. That is
# deliberate and it is the whole vocabulary — "the reason the gate returns is the reason the
# guide shows and the log prints". A term, never a sentence: `workload.status` shows it, an eval
# compares against it, a log search finds it, and the explanation rides in the fields beside it.
#
# There is NO `no_idset`. An identity with no line is a GUEST (§4 step 1), so it is refused by
# step 2 or 3 like anyone else — an unknown caller and an anonymous one cannot be told apart by
# what they are allowed to do, which is the point.
R_ACTION = "not_allowed"           # step 2 — no held id-set lists this action
R_TARGET = "out_of_scope"          # step 3 — held, but not on this target
R_DECLARED = "declared"            # step 4 — `run`: the declaration Set does not hold the key
R_ARMED = "armed"                  # step 4 — `run`: declared, but not armed
R_SOURCE_READY = "source_ready"    # step 4 — `run`: a required pool is not frozen
R_HEADROOM = "headroom"            # step 4 — `run`: the provider has no headroom
R_ROLES = "roles"                  # step 4 — `say`: the cast is not one the workload declares
R_PUBLIC = "public"                # step 4 — `publish`/`read`: the public Set does not hold it
R_UNKNOWN_ACTION = "unknown_action"  # the caller asked for something that is not one of the 8

REASONS = (R_ACTION, R_TARGET, R_DECLARED, R_ARMED, R_SOURCE_READY, R_HEADROOM, R_ROLES,
           R_PUBLIC, R_UNKNOWN_ACTION)

# The facts `run` needs, in the order the ruling lists them, so the reason names the FIRST one
# missing rather than whichever a reader happened to check first.
RUN_FACTS = (R_DECLARED, R_ARMED, R_SOURCE_READY, R_HEADROOM)

OK = ""                            # the reason of an admission is the empty term
FALLBACK = "guest"                 # §4 step 1 — an identity with no line is a guest

# ── the fact Sets: each has exactly ONE writer, named here so the map is readable ───────────
# All five hold TARGETS, because that is the question the ruling's step 4 asks —
# `target ∈ declared ∩ armed ∩ source_ready ∩ headroom`. A Set keyed by the pool or the
# provider instead would make the gate resolve a target to its pool, which is knowledge about
# workloads, which the gate must not have.
SET_DECLARED = "set:wl:declared"            # the declaration loader, at boot
SET_ARMED = "set:wl:armed"                  # the driver (declared ∧ provisioned; breaker removes)
SET_SOURCE_READY = "set:source:ready"       # the source engine, when a required pool freezes
SET_HEADROOM = "set:pool:headroom"          # admission, at reserve and at settle
SET_PUBLIC = "set:society:public"           # the consent op (`society.public`)

# reason term -> the Set that answers it, so step 4 is a loop over data and not a chain of ifs
FACT_SET = {R_DECLARED: SET_DECLARED, R_ARMED: SET_ARMED,
            R_SOURCE_READY: SET_SOURCE_READY, R_HEADROOM: SET_HEADROOM, R_PUBLIC: SET_PUBLIC}

# ── where the data lives ────────────────────────────────────────────────────────────────────
#
# TWO PLACES, AND THE DIFFERENCE IS THE WHOLE POINT.
#
#   config/identity/            the SEED. Shipped, read-only. `idsets.json` — what each row MAY
#                               do — is the platform's vocabulary and is READ FROM HERE, as is
#                               (the purge order §2: no cell copy, no upgrade, no `.bak`);
#                               `assign.ak` (the platform's lines), followed by the application's
#                               `config/assign.ak`, is copied once into a cell that has none.
#   <base_dir>/central/identity/  the CELL's own `assign.ak` — who holds what. Every write
#                               (`identity.assign`, `identity_changed`) lands here, beside
#                               `nucleus.db`, under `data/` which is gitignored.
#
# THEY WERE ONE PATH, AND THAT WAS A LIVE HOLE. Writes went to the repository's `config/identity/
# assign.ak` — so every eval that boots a cell appended its test identities to the actual
# permission file (`python test/gate_eval.py` → `assign.ak` DIRTY), and `config/` now ships in the
# seed. A `t0` or an `eval-owner` line left behind by a test run was one `spawn.py` away from
# being a line in a deployed cell's gate. Separating them makes that impossible by construction
# rather than by remembering to `git checkout` afterwards.
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SEED_IDSETS_PATH = os.path.join(_ROOT, "config", "identity", "idsets.json")
from lib.akasha.api import reserved as _reserved
SEED_ASSIGN_PATH = os.path.join(_ROOT, "config", "identity", "assign.ak")
APP_ASSIGN_PATH = _reserved.root("assign")

# The live paths. `bind(base_dir)` points them at the cell; until it is called they name the
# DEFAULT cell (`data/`), never the seed — an unbound writer must not be able to reach `config/`.
IDSETS_PATH = SEED_IDSETS_PATH                  # the table is the seed's, as is
ASSIGN_PATH = os.path.join("data", "central", "identity", "assign.ak")


def bind(base_dir: str) -> str:
    """Point the gate at THIS CELL's assignment file, seeding it from the shipped config once; the
    id-set table is the shipped one, read as is.

    Called from `KernelDispatcher.__init__`, before anything can ask a question — the gate is the
    first thing every request touches, so binding it late would mean some requests answered from
    another cell's table. Seeding is create-if-absent and never overwrites: a cell's assignment
    file is operator data from the moment it exists, and a deploy that refreshed it from the seed
    would silently un-grant everyone added since.

    ONE CELL PER PROCESS. The gate's tables are process-level (`_IDSETS` / `_ASSIGN` / `_LOADED`
    always were), so this points the ONE gate at the ONE cell and the last kernel constructed
    wins. That is exactly right for a deployment, which runs a single `KernelDispatcher` per
    process; a test that builds two in one process must say which it means (`gate_cell_files_eval`
    does, and says why).

    Returns the directory, so a caller (or an eval) can say where the gate is reading from."""
    global IDSETS_PATH, ASSIGN_PATH, _LOADED
    d = os.path.join(base_dir or "data", "central", "identity")
    try:
        os.makedirs(d, mode=0o700, exist_ok=True)
    except OSError:
        pass
    live, seed = os.path.join(d, "assign.ak"), SEED_ASSIGN_PATH
    if not os.path.exists(live) and os.path.exists(seed):
        try:
            # the platform's seed lines, then the application's (when it has any); a line already
            # there is not repeated, so an application seed that restates a platform line is inert
            body, seen = "", set()
            for p in (seed, APP_ASSIGN_PATH):
                if not os.path.isfile(p):
                    continue
                with open(p, "r", encoding="utf-8") as src:
                    for raw in src:
                        line = " ".join(raw.split("#", 1)[0].split())
                        if line and line in seen:
                            continue
                        seen.add(line)
                        body += raw if raw.endswith("\n") else raw + "\n"
            with open(live, "w", encoding="utf-8") as dst:
                dst.write(body)
            os.chmod(live, 0o600)          # the permission file is owner-only at rest
            logger.info("[gate] seeded %s from the shipped config", live)
        except OSError as exc:             # noqa: BLE001 — reported; `load` raises if truly absent
            logger.warning("[gate] could not seed %s: %s", live, exc)
    IDSETS_PATH, ASSIGN_PATH = SEED_IDSETS_PATH, live
    _LOADED = False
    return d

_LOCK = threading.Lock()           # guards the two in-memory reads below; off every decision path
_IDSETS: Dict[str, dict] = {}      # role -> row
_ASSIGN: Dict[str, List[dict]] = {}   # identity -> [{idset, on}]
_LOADED = False


# ── loading: the files are the truth, the tables are their read ─────────────────────────────

def load(idsets_path: str = None, assign_path: str = None) -> None:
    """Read both files into memory. Idempotent; called at boot and after `identity.assign`.

    A malformed row or an assignment naming an id-set that does not exist RAISES, naming the
    line. A permission file that half-loads is worse than one that does not load: the first
    silently ungrants an identity, and nothing in the log says which."""
    global _LOADED
    # SELF-SEED THE DEFAULT CELL. A caller that names no path wants "this cell's table", and on a
    # cell that has never booted there is no file yet — so bind the default `data/` cell, which
    # copies the shipped seed across. Doing it here rather than only in `bind()` keeps the direct
    # `gate.load()` callers (evals, a one-shot CLI) working without either of them reaching into
    # `config/`, which is the whole point of the split.
    if assign_path is None and not os.path.exists(ASSIGN_PATH):
        bind(os.environ.get("AKASHA_BASE_DIR", "data"))
    ip = idsets_path or IDSETS_PATH
    ap = assign_path or ASSIGN_PATH
    with open(ip, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    rows = {}
    for row in (doc.get("idsets") or []):
        name = str(row.get("role") or "").strip()
        if not name:
            raise ValueError("idsets.json: a row with no `role`")
        bad = [a for a in (row.get("may") or []) if a not in ACTIONS]
        if bad:
            raise ValueError("idsets.json: row %r grants %s, which %s not an action" %
                             (name, bad, "are" if len(bad) > 1 else "is"))
        rows[name] = {"role": name, "groups": str(row.get("groups") or "none"),
                      "may": tuple(row.get("may") or ()), "on": str(row.get("on") or "own"),
                      # step 4's workload facts apply to what this row admits (default). A row
                      # that reaches a RESOURCE a workload requires (`consumer`) says `false`:
                      # `run` over a pool is a job over an input, not a workload's own run, and
                      # a pool is never declared, armed or given headroom (§5.2).
                      "facts": row.get("facts", True) is not False}
    lines = {}
    with open(ap, "r", encoding="utf-8") as fh:
        for n, raw in enumerate(fh, 1):
            line = raw.split("#", 1)[0].strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) not in (2, 4) or (len(parts) == 4 and parts[2] != "on"):
                raise ValueError("assign.ak:%d: not `<identity> <idset> [on <target>]`: %r"
                                 % (n, raw.strip()))
            ident, idset = parts[0], parts[1]
            if idset not in rows:
                raise ValueError("assign.ak:%d: id-set %r is not a row of idsets.json" % (n, idset))
            lines.setdefault(ident, []).append(
                {"idset": idset, "on": (parts[3] if len(parts) == 4 else ""), "line": n})
    with _LOCK:
        _IDSETS.clear(); _IDSETS.update(rows)
        _ASSIGN.clear(); _ASSIGN.update(lines)
        _LOADED = True
    logger.info("[gate] loaded idsets=%d identities=%d lines=%d",
                len(rows), len(lines), sum(len(v) for v in lines.values()))


def _ensure() -> None:
    if not _LOADED:
        load()


def idsets() -> Dict[str, dict]:
    """The table, for a reader that wants to show it. A copy: nobody edits policy in memory."""
    _ensure()
    return {k: dict(v) for k, v in _IDSETS.items()}


def lines_for(identity: str) -> List[dict]:
    """Every assignment line this identity holds, in file order. The audit answer to
    "why was this allowed?" — and what an admitted observation records."""
    _ensure()
    return [dict(x) for x in _ASSIGN.get(str(identity or ""), ())]


# ── step 3's question: does a line's `on` reach this target? ────────────────────────────────

def _under(target: str, scope: str) -> bool:
    """Is `target` the scope itself, or beneath it? `/` and `:` are the two separators the
    cell's names use (`<bench>/<slug>`, `owner:user_x`). Prefix alone is not enough:
    `wb:plants_other` is not beneath `wb:plants`, and treating it as though it were is how a
    permission leaks to the neighbour with the longer name."""
    return target == scope or target.startswith(scope + "/") or target.startswith(scope + ":")


# NAMED TARGETS — a line may name a CLASS of target instead of one place (directive 2026-10-02
# §5.1). `feeds` was the `telemetry` row's own word (`on: feeds`), which no declaration could
# name: `W.assignable_idsets` admits only `assigned` rows. The row is `assigned` now, and the
# bootstrap line names the class — `system.telemetry telemetry on feeds` — so the reach is the
# LINE's, exactly as for every other assigned row, and `system.telemetry` reaches what it did.
# A named target is not a group: `scopes_for` opens no group engine for it.
NAMED_TARGETS = {
    # The source feeds, and nothing else. A telemetry agent records rows; it cannot reach the
    # graph, so a compromised sensor writes rows nobody acted on.
    "feeds": lambda t: _under(t, "feed") or _under(t, "set:source") or t.startswith("source:"),
}


def _reaches(row: dict, line: dict, identity: str, target: Optional[str]) -> bool:
    """Does this LINE, of this row, reach this target?

    THE LINE NARROWS THE ROW. `may ∩ on` is the ruling's shape, and the assignment line is
    what supplies `on`: a line that names a target is bounded BY that target whatever the
    row's own word says. That is what makes `admin on <group>` a group administrator rather
    than a second operator — and getting it the other way round (the row's `on: *` winning)
    is a full-cell grant written as a one-group one, which is the worst shape a permission bug
    can take. There is no `group_admin` row precisely because this narrowing exists.

    With no target on the line, the row's word decides:

    `*`        anywhere — the operator, the collective editor
    `assigned` nothing: the row expects a line that names its target, and a line without one
               grants nothing rather than everything
    `own`      what the identity owns — its own cell's scopes, and a target that names it
    `public`   the Set decides, in step 4
    """
    where = row["on"]
    scope = str(line.get("on") or "")
    if target is None:
        # NO TARGET = "may this identity do this action AT ALL?", which is what the RPC
        # boundary asks: the dispatcher knows the method's action, and the op that serves it
        # knows the atom or key and asks again with it. A line that names a target answers YES
        # here — it may do the action, somewhere — and the second question is where.
        #
        # Reading it the other way round refused every bounded identity everything at the
        # boundary: a `member on <group>` could not call `society.ls`, because the line had a
        # target and the question did not. Two questions, one function; only the second is
        # about a place.
        return True
    t = str(target)
    if scope in NAMED_TARGETS:
        return bool(NAMED_TARGETS[scope](t))
    if scope:
        return _under(t, scope)
    if where == "*":
        return True
    if where == "assigned":
        return False
    if where == "own":
        return t == identity or _under(t, "owner:user_%s" % identity) \
            or _under(t, "view:user_%s" % identity) or t.startswith(identity + "/")
    if where == "public":
        return True                          # the Set decides, in step 4
    if where in NAMED_TARGETS:               # a row whose own word is a class (none ships today)
        return bool(NAMED_TARGETS[where](t))
    return False


# ── step 4: the facts. Data the world writes, never a condition code carries ────────────────

class Facts:
    """The five fact Sets, behind one reader.

    Injected rather than imported so the gate has no dependency on the store: the kernel hands
    it a `has(set_name, member) -> bool`, an eval hands it a dict. That is also what makes the
    gate testable as a pure function of (table, lines, facts), which `gate_eval` relies on."""

    def __init__(self, has=None):
        self._has = has or (lambda _s, _m: False)

    def has(self, set_name: str, member: str) -> bool:
        try:
            return bool(self._has(set_name, member))
        except Exception:
            # A fact Set that cannot be read is NOT a grant. The safe answer to "is this
            # workload armed?" when the store will not say is no.
            return False


_FACTS = Facts()


def set_facts(has) -> None:
    """Install the fact reader (the kernel does this once, at boot)."""
    global _FACTS
    _FACTS = Facts(has)


def _facts_allow(action: str, target: Optional[str], cast: Optional[str],
                 declared_casts=None, via_public: bool = False, identity: str = "") -> str:
    """The fourth step, exactly as the ruling §4 writes it. Returns the name of the FIRST
    missing fact, or OK.

        run      needs target ∈ declared ∩ armed ∩ source_ready ∩ headroom
        say      needs cast ∈ target.roles
        publish  needs target ∈ public
        read     needs target ∈ public   (unless idset.on covers it)

    Each question here used to be an `if` somewhere else — `_is_public` in society.py, the
    `pool_frozen` probe in bootstrap.py, `over_allotment` in llm_pool, `mode`/`boot_pending`/
    `breaker` in the driver, admission's own declared/undeclared branch. They are membership
    now, so the world states the fact once and every reader gets the same answer.

    The ORDER of the run facts matters: the reason is the first one missing, so a workload that
    is neither declared nor armed reads `declared` — the thing to fix — rather than whichever
    Set a reader happened to look at first."""
    if target is None:
        return OK
    t = str(target)
    if action == RUN:
        for term in RUN_FACTS:
            if not _FACTS.has(FACT_SET[term], t):
                return term
        return OK
    if action == SAY:
        # say-as: the cast must be one the TARGET WORKLOAD DECLARES. This was the cast-ownership check,
        # which asked who owned an avatar atom — a second store of the same fact, and the one
        # that burned two days of model calls. The declaration is the answer now, and it is the
        # same file provisioning read. An agent has no assignment of its own: it acts under the
        # client's id-set, and this is the whole of the delegation mechanism.
        # …OR THE SPEAKER'S OWN IDENTITY (ruling §1, revision 09-22). A human member needs no
        # cast of its own and no `provision` to speak: it says a turn as itself. That is what
        # makes `member` a two-action row — read and say — instead of a row that has to be able
        # to create the avatar it speaks through.
        if cast and declared_casts is not None and cast not in declared_casts \
                and cast != str(identity or ""):
            return R_ROLES
        return OK
    if action == PUBLISH:
        return OK if _FACTS.has(SET_PUBLIC, t) else R_PUBLIC
    if action == READ:
        # "unless idset.on covers it": a reader that got here through `on: *` or `on: assigned`
        # has already been admitted by step 3 on its own scope, and the public Set has nothing
        # to say about it. Only a reader whose ONLY route was the `public` row has to be in it.
        if via_public and not _FACTS.has(SET_PUBLIC, t):
            return R_PUBLIC
        return OK
    return OK


# ── the gate ────────────────────────────────────────────────────────────────────────────────

def gate(identity: str, action: str, target: str = None, cast: str = None,
         declared_casts=None, place: str = None) -> Tuple[bool, str]:
    """The one decision. `(ok, reason)` — `reason` is a term from `REASONS`, or `""` when ok.

    `place` is where step 3 asks the identity to REACH, when that is not the `target` step 4 asks
    the facts about. It exists for `run` of a workload: the run facts are keyed by the WORKLOAD
    KEY (`plants-vision/plants_vision`), and a key is not a place — the client's lines name its
    space and its bench. A station hid this because its key happens to spell its space
    (`studio_ai/news_show`); a lab's does not, and asking reach of the key answered
    `out_of_scope` for a client that runs fine (frontend 2026-09-26d, needs platform 1). Absent,
    `place` is the target, which is every other question.

    Never raises. A gate that raises is a gate a caller writes an `except` around, and the
    `except` is a second decision."""
    _ensure()
    ident = str(identity or "")
    act = str(action or "")
    if act not in ACTIONS:
        return False, R_UNKNOWN_ACTION

    # 1 — which id-set does this identity hold? ABSENT IS A GUEST, not an error (§4 step 1).
    #     An unknown caller and an anonymous one must not be distinguishable by what they are
    #     allowed to do; if an absent identity were refused with its own term, the refusal
    #     itself would tell a prober which names exist.
    held = _ASSIGN.get(ident) or ([{"idset": FALLBACK, "on": "", "line": 0}]
                                  if FALLBACK in _IDSETS else [])
    if not held:
        return False, R_ACTION

    # 2 — may any of them perform this action?
    rows = [(_IDSETS[h["idset"]], h) for h in held if h["idset"] in _IDSETS]
    can = [(r, l) for r, l in rows if act in r["may"]]
    if not can:
        return False, R_ACTION

    # 3 — on this target? One line that reaches is enough; that IS the union of the grants,
    #     which is what the old `authorize_effective` computed with a second table.
    reach = [(r, l) for r, l in can if _reaches(r, l, ident, target if place is None else place)]
    if not reach:
        return False, R_TARGET

    # 4 — do the facts allow it? `via_public` is true when EVERY line that reached did so as
    #     the public row, which is the "unless idset.on covers it" of the read rule.
    via_public = all(r["on"] == "public" and not str(l.get("on") or "") for r, l in reach)
    # A line of a row that says `facts: false` (`consumer`, §5.2) admits a job over the RESOURCE
    # it names; the workload facts are asked of the workload's own run, never of its inputs.
    if any(not r.get("facts", True) for r, _l in reach):
        return True, OK
    why = _facts_allow(act, target, cast, declared_casts, via_public, ident)
    if why:
        return False, why
    return True, OK


def refuse_log(identity: str, action: str, target: str, reason: str) -> None:
    """The refusal line, in one place so its shape cannot drift between callers."""
    logger.warning("[gate] refused identity=%s action=%s target=%s reason=%s",
                   identity or "-", action or "-", target or "-", reason or "-")


def check(identity: str, action: str, target: str = None, cast: str = None,
          declared_casts=None) -> Tuple[bool, str]:
    """`gate`, and the refusal is logged. The call sites use this one; `gate` itself stays
    silent so an eval can enumerate the whole table without filling a log."""
    ok, why = gate(identity, action, target, cast, declared_casts)
    if not ok:
        refuse_log(identity, action, target, why)
    return ok, why


def admitted(identity: str, action: str, target: str = None) -> Dict[str, Any]:
    """The provenance field an admitted effect carries: who, what, where, and UNDER WHICH LINE.

    This is the half of the order that is not about refusing anything. Every observation an
    effect writes says which line of the assignment file allowed it, so the lineage of an atom
    answers "who was allowed to make this, and why" without a second store and without a
    reader having to reconstruct the policy that was in force at the time."""
    _ensure()
    ident = str(identity or "")
    act = str(action or "")
    held = _ASSIGN.get(ident) or ([{"idset": FALLBACK, "on": "", "line": 0}]
                                  if FALLBACK in _IDSETS else [])
    rows = [(_IDSETS[h["idset"]], h) for h in held if h["idset"] in _IDSETS]
    hit = next(((r, l) for r, l in rows
                if act in r["may"] and _reaches(r, l, ident, target)), None)
    return {"identity": ident, "action": act, "target": target or None,
            "idset": (hit[0]["role"] if hit else None),
            "line": (hit[1]["line"] if hit else None)}


# ── the session's scopes — the gate's view of an identity ───────────────────────────────────

def scopes_for(identity: str, groups_of=None) -> List[str]:
    """The scope list a session carries, derived from the assignment lines and nothing else.

    This replaces `iam.get_allowed_scopes`. It is the same shape the store already enforces —
    that half does not change — but it is now a READ of the policy rather than a second
    statement of it. `groups_of(identity)` is injected (the group registry lives in the
    manager, not here); a `groups: "*"` row gets every group the callback knows.

    Session management and society management are the same mechanism after this: a society
    membership is an assignment line, and the group engine a session opens is this list."""
    _ensure()
    ident = str(identity or "")
    held = _ASSIGN.get(ident) or []
    scopes = ["scope:sys:universal", "view:public"]
    if not held:
        return scopes

    rows = [(_IDSETS[h["idset"]], h) for h in held if h["idset"] in _IDSETS]
    may = set()
    for r, _l in rows:
        may.update(r["may"])

    # A named identity always reaches its own cell. A guest has no cell, and `guest` is the
    # one row whose `groups` is `none` and whose `on` is `public` — so it stops here.
    if any(r["on"] != "public" for r, _ in rows):
        scopes += ["owner:user_%s" % ident, "view:user_%s" % ident]

    # CELL-WIDE scopes come only from a line that is itself cell-wide. A line that names a
    # target is bounded by it (see `_reaches`), so `admin on <group>` must NOT collect the
    # operator's scopes — that would hand a group administrator the whole store through the
    # side door, after the gate had correctly refused it at the front.
    def _unbounded(act):
        return any(act in r["may"] and r["on"] == "*" and not str(l.get("on") or "")
                   for r, l in rows)

    # The collective scope follows the ACTION, not the role name: an id-set that may record
    # anywhere is what `COLLECTIVE_WRITE` used to mean.
    if _unbounded(RECORD):
        scopes += ["scope:sys:collective", "role:librarian"]
    if _unbounded(ADMIN):
        scopes += ["view:admin_override", "scope:sys:dna", "role:superuser", "scope:sys:admin"]

    # Groups, in the table's own words: `all` every group the registry knows, `own` the groups
    # and benches this identity's own lines name, `source` the feeds, `none` nowhere. A line
    # that NAMES a target bounds `all` to it, the same narrowing `_reaches` applies — otherwise
    # `admin on <group>` would open every group engine on the cell.
    want_all = any(r["groups"] == "all" and not str(l.get("on") or "") for r, l in rows)
    gids = set()
    if want_all and groups_of:
        try:
            gids.update(groups_of(None) or ())
        except Exception:
            pass
    for r, l in rows:
        tgt = str(l.get("on") or "")
        if tgt and tgt not in NAMED_TARGETS and r["groups"] in ("own", "all"):
            gids.add(tgt.split("/", 1)[0])
    if groups_of and not want_all:
        try:
            gids.update(groups_of(ident) or ())
        except Exception:
            pass
    for gid in sorted(g for g in gids if g):
        scopes += ["scope:group_%s" % gid, "view:group_%s" % gid]
        # A line that may `admin` that group manages it — the group-administrator row that
        # the table deliberately does not have, expressed as `may ∩ on`.
        for r, l in rows:
            tgt = str(l.get("on") or "")
            if ADMIN in r["may"] and ((not tgt and r["on"] == "*")
                                      or tgt.split("/", 1)[0] == gid):
                scopes.append("manage:group_%s" % gid)
                break
    return sorted(set(scopes))


# ── writing the assignment file (the two writers of §1, and nobody else) ────────────────────

def assign(identity: str, idset: str, target: str = "", path: str = None) -> dict:
    """Append one line. `identity.assign` (admin) and `workload_provision` call this.

    Appends to the FILE first, then re-reads: the file is the audit trail, so a line that is
    not in it never grants anything, even for the moment between the two."""
    _ensure()
    if idset not in _IDSETS:
        raise ValueError("no such id-set: %r" % idset)
    p = path or ASSIGN_PATH
    line = "%s %s%s" % (identity, idset, (" on %s" % target) if target else "")
    for existing in lines_for(identity):
        if existing["idset"] == idset and str(existing.get("on") or "") == str(target or ""):
            return {"identity": identity, "idset": idset, "on": target or None, "added": False}
    with open(p, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    load(assign_path=p)
    logger.info("[gate] assigned identity=%s idset=%s on=%s", identity, idset, target or "-")
    return {"identity": identity, "idset": idset, "on": target or None, "added": True}


def unassign(identity: str, idset: str = "", target: str = "", path: str = None) -> int:
    """Remove matching lines. `workload_provision` calls this when a declaration is gone.

    Rewrites the file without them and re-reads. Comments and blank lines are preserved: the
    file is meant to be read by a person, and a rewrite that strips its commentary makes the
    audit trail worse every time it runs."""
    _ensure()
    p = path or ASSIGN_PATH
    kept, dropped = [], 0
    with open(p, "r", encoding="utf-8") as fh:
        for raw in fh:
            body = raw.split("#", 1)[0].strip()
            if body:
                parts = body.split()
                if parts[0] == identity and (not idset or parts[1] == idset):
                    on = parts[3] if len(parts) == 4 else ""
                    if not target or on == target:
                        dropped += 1
                        continue
            kept.append(raw)
    if dropped:
        with open(p, "w", encoding="utf-8") as fh:
            fh.writelines(kept)
        load(assign_path=p)
        logger.info("[gate] unassigned identity=%s idset=%s on=%s n=%d",
                    identity, idset or "-", target or "-", dropped)
    return dropped


# ── the bridge from the role store to the assignment file ──────────────────────────────────

# An IAM role -> the id-set row that stands for it. The roles are what the cell's user records
# already carry; the rows are the ruling's. This is a MIGRATION table, read once, and it is the
# only place the old vocabulary and the new one meet.
ROLE_IDSET = {
    "admin": "admin",
    "librarian": "librarian",
    "group_admin": "admin",     # `admin on <group>` — the line narrows it to that group
    "user": "resident",         # a person in their OWN CELL; participation is a further line
    "guest": "guest",
}


def line_for_role(role: str, groups=None) -> List[Tuple[str, str]]:
    """(idset, target) pairs an identity with this role and these groups should hold.

    A `group_admin` gets one `admin on <group>` per group it administers — never an unbounded
    `admin`, which would turn a group administrator into the cell's operator.

    A plain `user` gets `resident` — the person in their OWN CELL — plus one `member on <group>`
    per group they belong to. The two are different facts and the ruling keeps them apart: having
    a cell is not participation, and participating is not being given a cell.

    This is where the table's eighth row landed (ruling revision 09-22, second). Before it, a
    plain user resolved to `member`, which is read + say — so a consumer-app account could create
    NOTHING of its own: 564 of 864 registered methods are `record`, and `recipe.new`, `note.new`,
    `rec.new` and `fieldnote.new` were all closed to the account `auth.register` exists to make.
    A person in no group had no target to name either, so even the line they did get reached
    nothing. `resident` is sovereign in its own cell (everything but `admin`, `on own`) and
    reaches nothing outside it; a `researcher on <bench>` is still a further line a person
    writes, never one derived from an IAM role."""
    r = str(role or "guest").strip().lower()
    idset = ROLE_IDSET.get(r, "guest")
    gs = sorted(set(groups or ()))
    if r in ("admin", "librarian"):
        return [(idset, "")]                       # cell-wide, by the row's own `on`
    if r == "group_admin":
        return [(idset, g) for g in gs] or [(idset, "")]
    if idset != "resident":                        # guest, or a row that names no cell
        return [(idset, "")]
    return [("resident", "")] + [("member", g) for g in gs]


def identity_changed(kernel, identity: str, role: str = "") -> int:
    """An account was created or its membership moved: make the file say so.

    One call, so the kernel carries no knowledge of how a line is shaped — it reports the
    event, the gate writes the line. Never raises: a line that cannot be written is reported,
    and the identity then reads as a guest, which is a closed door rather than an open one.

    The alternative — refusing the account creation — would leave IAM and the file disagreeing,
    which is the two-sources-of-truth this order exists to remove."""
    try:
        r = role or str(getattr(kernel.iam.authenticate(identity), "value", "user"))
        return sync_identity(identity, r, kernel.iam.get_client_groups(identity))
    except Exception as exc:                       # noqa: BLE001 — reported, never silent
        logger.warning("[gate] assignment line FAILED identity=%s reason=%s: %s",
                       identity, type(exc).__name__, exc)
        return 0


def sync_identity(identity: str, role: str, groups=None, path: str = None) -> int:
    """Make the assignment file say what this identity's role and groups say. Returns the
    number of lines written.

    Called by `user.add`, group membership, self-registration and the genesis rite, so every
    account has its line before its first request (there is no boot migration: a cell starts at
    Genesis). Idempotent: `assign` skips a line that is already there."""
    n = 0
    for idset, target in line_for_role(role, groups):
        if assign(identity, idset, target, path=path).get("added"):
            n += 1
    return n
