"""
workload — the DECLARATION is the workload, and this module is the only thing that reads it.

Seed A slice 1 (`directive-backend-seedA-2026-09-21.md` §1, addendum 2026-09-21 §2). A scheduled
workload on a workbench — a research experiment, a broadcast programme, an operational process —
is DECLARED in one file under `config/workbench/workloads/<slug>.json` and the platform reads it.
Nothing in the driver knows what the workload is ABOUT. It reads five fields:

    trigger   when it is due            duty      what the driver owes it when a gate stops it
    effect    what a run produces       appetite  what one run costs the model provider
    budget    what a day of it may cost

and no sixth. There is no `kind`, no `"station"`, no studio name and no society-name comparison
anywhere downstream — `workload_grep_eval` holds that down, because every one of those was in the
driver before this seed and each was a place where a new programme meant a new branch.

Why a module rather than a dict passed around: the frozen shape (frontend order §5) has exactly
nine fields, and a missing one is a PROVISIONING ERROR naming the field rather than a `None` that
travels three layers and surfaces as a programme that silently never airs. Validation happens once,
at boot, in `problems()`; everything after it reads a declaration that has already been checked.

THE KEY.  `<bench>/<slug>` with the bench's `wb:` prefix dropped — `studio_ai/news_show`. That is
not cosmetic: it is the same string the in-kernel news daemon has always emitted, so the LLM pool
ledger, the day's spend and the carry-over credit stay continuous across the convergence. Renaming
it would silently reset every programme's spend history, which is why the declarations pin it in
their own `_key` note and why `key()` derives it rather than accepting one.

THE SETS.  Every field is also a MEMBERSHIP on the workload atom (`set:wl:*`), mechanically named,
so the declaration is inspectable as data by anything that can read a Set — including a guest, and
including `bench.info`, whose `programmes` count is now `set:wl:effect:publish` ∩ the bench rather
than a test for what a society is called (order §1.3, closing L5). The Sets are DERIVED: the file
is the source of truth and a boot reconciles them to it.
"""
import json
import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("Akasha.Kernel")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
# the declaration ROOT the API defines (the purge order, §1.3)
from lib.akasha.api import reserved as _roots
WORKLOAD_DIR = _roots.root("workloads")
PROFILE_DIR = _roots.root("profiles")

# The frozen shape (frontend order §5). A declaration missing one of these is refused BY NAME.
REQUIRED = ("bench", "workflow", "society", "trigger", "duty", "effect", "appetite", "budget", "pins")

# OPTIONAL fields. `effect_read` says how the platform counts a run's effect: the op to read, its
# args, and the row fields that carry effect/reason/time (group 4, 4.12(b)). Absent, a job that
# succeeded IS its effect. Read by the state layer, never by the driver.
#
# The lab fields (frontend 26b/26c, "needs platform 2"):
#   `idset`     the ID set provisioning assigns the workload's CLIENT on the workload's own places
#               (its space and its bench). Absent → `programme`. Only a row whose `on` is `assigned`
#               may be named — read from `config/identity/idsets.json`, so a declaration can never
#               give its client `admin`, `librarian` or anything that reaches beyond its own lines.
#   `workflows` the BRANCHES this workload runs, in order, each loaded from the template of the same
#               name (`config/workbench/<bench>/templates/<name>.ak`). Absent → one branch, the
#               workflow slug. `workflow` stays the workload's NAME: the accounting key, the client.
#   `sweeps`    sweep definitions applied at provisioning (`config/workbench/<bench>/sweeps/<name>.json`)
#               and handed to the driver, which picks their branches after a static run ends ok.
#   `grants`    cast → responsibility kinds (`operator:<family>`, `decide`) the workload's casts hold on
#               its society, beside the default `operator:air`.
#   `profile`   names a file under the profiles root (`config/profiles/<p>.json`, ruling of 4 October).
#               Its fields are the declaration's DEFAULTS: a field the declaration states explicitly
#               wins, and a dict field merges key by key (the declaration's keys win at every level).
#               An unknown profile is a provisioning error by name (`reason=profile`, and one
#               `[bench] workload profile unknown` line naming it). It is also a Set membership
#               (`set:wl:profile:<p>`) a page can group by.
#
# The bench fields (frontend 26d, "needs platform 3") — what the legacy bench SCAFFOLD
# (`workloads/bench_<name>.json`, create-if-absent) carried that the workload did not, so the
# scaffold can go and the bench has ONE author that reconciles every boot:
#   `bench_kind`   the kind the bench records (`bench.ls`/`bench.info`, and the families a
#                  registered kind records). Absent → the declared `effect`, as the order-§3 ruling
#                  set: the declaration may STATE a kind, the platform never maps one.
#   `bench_public` true → the bench lives in the NUCLEUS (guest-readable, its own place `wb:<slug>`)
#                  rather than in the workload's group (`<gid>/wb:<slug>`). The client's ID-set line
#                  follows the bench to whichever place it is. Absent → false.
#   `space.kind` / `space.identity`  passed to `society.new` (`chat`|`cowork`, `open`|`locked`).
OPTIONAL = ("effect_read", "idset", "workflows", "sweeps", "grants", "profile",
            "bench_kind", "bench_public", "labo")
_SPACE_KINDS = ("chat", "cowork")
_SPACE_IDENTITIES = ("open", "locked")

DEFAULT_IDSET = "programme"
_NAME_RE = re.compile(r"^[A-Za-z0-9_.:-]+$")

# The five the driver reads, and the whole list of them. Kept here so `workload_grep_eval` can
# assert the driver touches these and nothing else.
DRIVER_FIELDS = ("trigger", "duty", "effect", "appetite", "budget")

DUTY_CONTINUOUS = "wb:duty:continuous"
DUTY_BEST_EFFORT = "wb:duty:best_effort"
_DUTIES = (DUTY_CONTINUOUS, DUTY_BEST_EFFORT)

EFFECT_PUBLISH = "publish"          # the run puts something in front of the public
EFFECT_RECORD = "record"            # the run writes to the graph and nothing leaves the cell
_EFFECTS = (EFFECT_PUBLISH, EFFECT_RECORD)

_EVERY_RE = re.compile(r"^every:(\d+(?:\.\d+)?)s$")
_DAILY_RE = re.compile(r"^daily:([01]\d|2[0-3]):([0-5]\d)Z$")


# ── reading the declarations ──────────────────────────────────────────────────────────────────

def _is_workload(doc: Any) -> bool:
    """A file in the workloads directory is a WORKLOAD when it declares the three that identify
    one: what it runs on, what it runs, and where it speaks. The directory also holds the legacy
    station pair and a research bench contract, which declare none of the three — this is a shape
    test, not a filename list, so retiring those files needs no edit here."""
    return (isinstance(doc, dict) and isinstance(doc.get("bench"), str)
            and isinstance(doc.get("workflow"), str) and isinstance(doc.get("society"), str))


def declarations(kernel=None) -> List[Dict[str, Any]]:
    """Every workload declaration on this cell, in slug order, cached per kernel.

    Bounded by the number of files in one config directory (a handful), read once. A file that is
    not JSON is REPORTED and skipped — a broken declaration must not take a boot down, and it must
    not be silent either (§0: no debug-level skip)."""
    cached = getattr(kernel, "_workload_decl_cache", None) if kernel is not None else None
    if cached is not None:
        return cached
    out = []
    try:
        names = sorted(n for n in os.listdir(WORKLOAD_DIR) if n.endswith(".json"))
    except OSError:
        names = []
    for n in names:
        path = os.path.join(WORKLOAD_DIR, n)
        try:
            with open(path, encoding="utf-8") as f:
                doc = json.load(f)
        except (OSError, ValueError) as exc:
            logger.warning("[bench] workload declaration unreadable file=%s reason=unparseable: %s",
                           n, exc)
            continue
        if not _is_workload(doc):
            continue
        doc = with_profile(doc, n)
        doc["_file"] = n
        out.append(doc)
    if kernel is not None:
        kernel._workload_decl_cache = out
    return out


def profile(name: str) -> Optional[Dict[str, Any]]:
    """The profile `name` (`<profiles root>/<name>.json`), or None when there is no such file or it
    does not parse. A name outside `[A-Za-z0-9_.:-]` is no profile."""
    if not name or not _NAME_RE.match(str(name)) or "/" in str(name) or str(name).startswith("."):
        return None
    try:
        with open(os.path.join(PROFILE_DIR, str(name) + ".json"), encoding="utf-8") as f:
            doc = json.load(f)
    except (OSError, ValueError):
        return None
    return doc if isinstance(doc, dict) else None


def _defaults(base: Dict[str, Any], explicit: Dict[str, Any]) -> Dict[str, Any]:
    """`explicit` over `base`: every key `explicit` states wins; a dict on both sides merges key by
    key under the same rule."""
    out = dict(base)
    for k, v in explicit.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _defaults(out[k], v)
        else:
            out[k] = v
    return out


def with_profile(doc: Dict[str, Any], file: str = "?") -> Dict[str, Any]:
    """The declaration with its profile's fields applied as defaults (ruling of 4 October). No
    `profile` → the declaration as written. An unknown profile → the declaration as written, marked
    so `problems()` refuses it with `reason=profile`, and one line naming the profile."""
    name = doc.get("profile")
    if not name:
        return doc
    prof = profile(str(name))
    if prof is None:
        logger.warning("[bench] workload profile unknown file=%s profile=%s root=%s", file, name,
                       os.path.relpath(PROFILE_DIR, ROOT))
        return dict(doc, _profile_unknown=str(name))
    return _defaults({k: v for k, v in prof.items() if not str(k).startswith("_")}, doc)


def problems(decl: Dict[str, Any]) -> List[str]:
    """The field ids this declaration is missing or has malformed — [] when it is well-formed.

    Returns IDS, not prose, because the caller logs them as `reason=<id>` and the frozen schema is
    the contract between two teams: "reason=trigger" tells the frontend exactly which line of their
    file to look at, where "reason=invalid" would start a conversation."""
    bad = []
    for f in REQUIRED:
        if f not in decl:
            bad.append(f)
    if "trigger" in decl and not _trigger_ok(decl.get("trigger")):
        bad.append("trigger")
    if "labo" in decl:
        _lab = decl.get("labo")
        # a dict with a name; and when the workload can require more than one pool, the name must
        # vary by pool — one labo name bound to every pool is not what `{pool}` is for
        if (not isinstance(_lab, dict) or not str(_lab.get("name") or "").strip()
                or str(_lab.get("when") or "always").strip() not in LABO_WHEN
                or (str(_lab.get("name")).count("{pool}") == 0
                    and (requires_frozen_pools(decl) or len(resource_requires(decl)) > 1))):
            bad.append("labo")
    if "duty" in decl and str(decl.get("duty") or "") not in _DUTIES:
        bad.append("duty")
    if "effect" in decl and str(decl.get("effect") or "") not in _EFFECTS:
        bad.append("effect")
    if "effect_read" in decl:
        er = decl.get("effect_read")
        if not (isinstance(er, dict) and str(er.get("op") or "").strip()
                and isinstance(er.get("args", {}), dict)):
            bad.append("effect_read")
    if "society" in decl and len(str(decl.get("society") or "").split("/")) != 2:
        bad.append("society")
    if "idset" in decl and str(decl.get("idset") or "") not in assignable_idsets():
        bad.append("idset")
    for f in ("workflows", "sweeps"):
        if f in decl and not (isinstance(decl.get(f), list) and decl.get(f)
                              and all(isinstance(x, str) and _NAME_RE.match(x) for x in decl[f])):
            bad.append(f)
    if "grants" in decl:
        g = decl.get("grants")
        if not (isinstance(g, dict) and all(
                isinstance(v, list) and all(isinstance(x, str) and x for x in v)
                for k, v in g.items() if not str(k).startswith("_"))):
            bad.append("grants")
    if ("profile" in decl and not _NAME_RE.match(str(decl.get("profile") or ""))) \
            or decl.get("_profile_unknown"):
        bad.append("profile")
    if "bench_kind" in decl and not _NAME_RE.match(str(decl.get("bench_kind") or "")):
        bad.append("bench_kind")
    if "bench_public" in decl and not isinstance(decl.get("bench_public"), bool):
        bad.append("bench_public")
    sp = decl.get("space") if isinstance(decl.get("space"), dict) else {}
    # the client is the declaration's OWN id — required; the platform invents none (the purge order
    # §2: the `llm:programme:<workflow>` default was a legacy ledger id)
    if ("kind" in sp and sp.get("kind") not in _SPACE_KINDS) \
            or ("identity" in sp and sp.get("identity") not in _SPACE_IDENTITIES) \
            or not str(sp.get("client") or "").strip():
        bad.append("space")
    for f in ("appetite", "budget", "pins"):
        if f in decl and not isinstance(decl.get(f), dict):
            bad.append(f)
    return sorted(set(bad))


def _trigger_ok(trig: Any) -> bool:
    if not isinstance(trig, dict):
        return False
    then = trig.get("then")
    if then is not None and not (isinstance(then, str)
                                 and (_EVERY_RE.match(then) or _DAILY_RE.match(then))):
        return False
    return bool(trig.get("boot")) or then is not None


# ── identity ──────────────────────────────────────────────────────────────────────────────────

def bench_slug(decl: Dict[str, Any]) -> str:
    """The bench without its `wb:` prefix — `wb:studio_ai` → `studio_ai`."""
    b = str(decl.get("bench") or "").strip()
    return b[3:] if b.startswith("wb:") else b


def bench_atom(decl: Dict[str, Any]) -> str:
    """The bench atom alias — always `wb:`-prefixed, whichever way it was declared."""
    b = str(decl.get("bench") or "").strip()
    return b if b.startswith("wb:") else ("wb:%s" % b if b else "")


def key(decl: Dict[str, Any]) -> str:
    """`<bench>/<slug>` — the accounting key. See THE KEY in the module docstring: this is the
    string the LLM pool ledger is keyed on and it must not drift."""
    b, w = bench_slug(decl), str(decl.get("workflow") or "").strip()
    return "%s/%s" % (b, w) if (b and w) else ""


def client_of(decl: Dict[str, Any]) -> str:
    """The ONE client identity that owns every cast of this workload — and the identity the driver
    RUNS the workload as.

    A workflow step runs as one client and you speak only as an avatar you own, so the roles share
    an identity and the ROLE is enforced per turn by its contract and by the cast stamped on the
    utterance.

    It lives HERE, with the declaration's other fields, because two layers ask for it and neither
    owns it: `workload_provision` provisions the casts as this client, and `autorun` dispatches the
    run as this client. Provisioning-as-X while running-as-Y is the defect that produced a society
    whose casts the speaker did not own — which is not a say that fails loudly, it is a say that
    does not happen.

    Declared in `space.client` and nowhere else: the platform invents no client id (the purge order
    §2 — the `llm:programme:<workflow>` default was a legacy ledger id). A declaration without one
    is refused by `problems` (`space`); here it is ""."""
    sp = decl.get("space") if isinstance(decl.get("space"), dict) else {}
    return str(sp.get("client") or "").strip()


def assignable_idsets() -> List[str]:
    """The ID sets a declaration may name for its client: every row of `config/identity/idsets.json`
    whose `on` is `assigned` — a row that grants nothing until a line names its target. Read from
    the gate's table, never listed here.

    A row that says `facts: false` (`consumer`) is excluded: it is the grant a client holds on a
    RESOURCE its declaration requires, written by provisioning from `requires`, never the client's
    main ID set on its own places (directive 2026-10-02 §5.2)."""
    try:
        from lib.akasha.api import gate as _gate
        return sorted(r for r, row in (_gate.idsets() or {}).items()
                      if row.get("on") == "assigned" and row.get("facts", True) is not False)
    except Exception:
        return [DEFAULT_IDSET]


def idset_of(decl: Dict[str, Any]) -> str:
    """The ID set the workload's client holds on its own places — declared, or `programme`."""
    return str(decl.get("idset") or DEFAULT_IDSET).strip()


def client_places(decl: Dict[str, Any]) -> List[str]:
    """The workload's own places, spelled the way an assignment line spells them: its SPACE
    (`<gid>/<space>`) and its BENCH (what a bench op's `gate_target` answers — `<gid>/wb:<bench>`
    for a bench in the group, `wb:<bench>` for a PUBLIC bench, which has no group). A lab's client
    records on its bench; a line on the space alone does not reach `<gid>/wb:…`, which is exactly
    the refusal the 09-26 lab draft hit, and a line on `<gid>/wb:…` does not reach a public bench,
    which is the refusal the scaffold's public bench caused (26d)."""
    gid, space = society_of(decl)
    group_bench, public_bench = bench_places(decl)
    return ["%s/%s" % (gid, space), public_bench if bench_public(decl) else group_bench]


def bench_places(decl: Dict[str, Any]) -> Tuple[str, str]:
    """(the bench's place in its group, the bench's place as a public bench). The bench spelled as
    its alias is spelled (`wb:` + the slug the bench concept mints), so `plants-vision` and
    `plants_vision` name one place, as they do for `gate_target`."""
    gid, _space = society_of(decl)
    bench = "wb:" + re.sub(r"[^a-z0-9]+", "_", bench_slug(decl).lower()).strip("_")
    return "%s/%s" % (gid, bench), bench


def bench_public(decl: Dict[str, Any]) -> bool:
    """Does the bench live in the nucleus (`bench_public: true`)? Absent → in the group."""
    return decl.get("bench_public") is True


def bench_kind(decl: Dict[str, Any]) -> str:
    """The kind the bench records — the declared `bench_kind`, else the declared `effect`."""
    return str(decl.get("bench_kind") or "").strip() or effect(decl)


def workflows_of(decl: Dict[str, Any]) -> List[str]:
    """The branches this workload runs, in order — the declared `workflows`, or the one branch."""
    wfs = decl.get("workflows")
    if isinstance(wfs, list) and wfs:
        return [str(w).strip() for w in wfs if str(w).strip()]
    return [branch_of(decl)]


def sweeps_of(decl: Dict[str, Any]) -> List[str]:
    sw = decl.get("sweeps")
    return [str(s).strip() for s in sw if str(s).strip()] if isinstance(sw, list) else []


def publishes_to_room(decl: Dict[str, Any]) -> bool:
    """Does this workload publish to a ROOM — a space with a page someone can open?

    `effect: publish` says the output faces the public; it does not say WHERE. A workload that
    posts to an external channel publishes too, and has no room: no page to list, an empty society
    of its own, and nothing for a guide row to show.

    It lives HERE, with the declaration's other questions, because it was answered in TWO places
    and they disagreed: provisioning asked this question and gave a channel workload no guide row,
    while `wl_state.note` asked `effect == publish` and grew one for it on the first driver tick —
    so the guide showed a programme whose room reads `unclassified`, which is the very symptom
    asking the right question was meant to remove. One question, one answer, carried in the policy
    the driver reads (`room`).

    The declaration is deliberately NOT given a fake `public` space to quiet that line: flagging a
    society public is a person's consent to be shown on the web, and manufacturing it to silence a
    log message is the habit the consent gate exists to prevent."""
    if effect(decl) != EFFECT_PUBLISH:
        return False
    pins = decl.get("pins") if isinstance(decl.get("pins"), dict) else {}
    return not str(pins.get("channel") or "").strip()


def society_of(decl: Dict[str, Any]) -> Tuple[str, str]:
    """(group, space) from the declared `society`, or ("", "")."""
    parts = str(decl.get("society") or "").split("/")
    return (parts[0].strip(), parts[1].strip()) if len(parts) == 2 else ("", "")


# ── the two the application layer asks the platform for ──────────────────────────────────────
# Declared as manifest HOOKS (`workload.for_society`, `workload.by_key`), so a package to the right
# of this one reaches them through `kernel.api.hooks` and the platform never imports it back. They
# return the declaration dict or **None** — not an empty dict — because a caller's natural test is
# `if w is None`, and an empty dict would quietly take the found branch and then answer every
# `.get()` with a default. The contract is the manifest's; the shapes are in
# `docs/handoff/backend-step0-2026-09-21.md`.

def for_society(kernel, gid: str, space: str) -> Optional[Dict[str, Any]]:
    """The workload that speaks in this society, or None.

    This is the ONE lookup by society, and it replaces every "is this a declared programme?" test
    that used to stand in for it. A society with no declaration is not a lesser kind of society —
    it simply has no workload, and a caller treats it as it always did."""
    g, s = (gid or "").strip(), (space or "").strip()
    for d in declarations(kernel):
        if society_of(d) == (g, s):
            return d
    return None


def by_key(kernel, wl_key: str) -> Optional[Dict[str, Any]]:
    """The workload with this accounting key (`<bench>/<slug>`), or None."""
    k = (wl_key or "").strip()
    for d in declarations(kernel):
        if key(d) == k:
            return d
    return None


def ontology_names(decl: Dict[str, Any]) -> List[str]:
    """The ontology names this workload DECLARES it reads: every string value of `pins` (a Set or
    an atom its template resolves) and the bare name of every `set:` requirement. What a loading
    pack declares is compared against exactly these (frontend 09-28, needs platform 1) — so a
    workload whose template reads an ontology name it does not declare is not protected from a
    load in flight; declaring it is the contract."""
    out = []
    pins = decl.get("pins") if isinstance(decl.get("pins"), dict) else {}
    for k, v in pins.items():
        if not str(k).startswith("_") and isinstance(v, str) and v.strip():
            out.append(v.strip())
    for r in (decl.get("requires") or []):
        r = str(r)
        if r.startswith("set:"):
            out.append(r[len("set:"):])
    return sorted(set(out))


# The `requires` entries a workload's client is bound to as a CONSUMER (§5.2): read + run on the
# resource, never record. `set:` entries are ontology Sets, read as they always were — no line.
RESOURCE_PREFIXES = ("source:pool:", "model:")
CONSUMER_IDSET = "consumer"


def resource_requires(decl: Dict[str, Any]) -> List[str]:
    """The `source:pool:…` / `model:…` entries of `requires`, verbatim — each is the target of one
    `<client> consumer on <resource>` line. The string is the resource KEY itself, which is what a
    gate question about the resource names (`gate(client, run, "source:pool:x:v1")`)."""
    out = []
    for r in (decl.get("requires") or []):
        r = str(r).strip()
        if r.startswith(RESOURCE_PREFIXES) and r not in out:
            out.append(r)
    return out


FROZEN_POOLS_SET = "set:source:pool:frozen"     # the source engine's Set (source.bootstrap.POOL_FROZEN)

# §6.4 — `labo: {name: "<pattern with {pool}>", about, scope}`: provisioning ensures one labo per
# pool the workload requires (members of a required Set included) and binds the pool to it, through
# the two extension points below. The application's `labo.new` / `labo.bind` declare
# `implements: <point>`; the platform names the POINT, never the application method (ownership a).
LABO_NEW_POINT = "workload.labo.new"            # called with {name, about, scope}
LABO_BIND_POINT = "workload.labo.bind"          # called with {name, pool, origin: "shadow"}
# 3 October decision 2 — REGISTERED LABS WIN. A declared labo with `when: "unbound"` is a SHADOW labo:
# it is made only for a pool bound to no other lab. The platform asks which labs a pool is bound to
# through this READ point — `{pool}` → `{"labos": [{"labo": "labo:<name>", "origin": "registered" |
# "shadow" | ""}]}` — and never reads the application's labo model itself. A bound labo that is not
# this workload's own shadow, and is not marked `shadow`, is a registered lab: the pool gets none.
LABO_OF_POINT = "workload.labo.of"
LABO_WHEN = ("always", "unbound")


def labo_of(decl: Dict[str, Any]) -> Dict[str, str]:
    """The declared per-pool labo, normalized — {} when none is declared. `when` defaults to
    `always` (every required pool); `unbound` makes it a shadow for pools bound to no lab."""
    lab = decl.get("labo")
    if not isinstance(lab, dict) or not str(lab.get("name") or "").strip():
        return {}
    return {"name": str(lab["name"]).strip(), "about": str(lab.get("about") or ""),
            "scope": str(lab.get("scope") or "public"),
            "when": str(lab.get("when") or "always").strip()}


def pool_slug(pool: str) -> str:
    """`source:pool:plants_images:v1` → `plants_images_v1` — what `{pool}` expands to in a name."""
    return re.sub(r"[^a-z0-9]+", "_", str(pool).replace("source:pool:", "").lower()).strip("_") or "pool"


def labo_name(decl: Dict[str, Any], pool: str) -> str:
    """The labo this workload keeps for `pool` — its `labo.name` with `{pool}` expanded."""
    return labo_of(decl).get("name", "").replace("{pool}", pool_slug(pool))


def requires_frozen_pools(decl: Dict[str, Any]) -> bool:
    """Does this declaration require EVERY frozen pool (§6.1)? Then its client is bound to each
    member of `set:source:pool:frozen`, and to each pool that freezes later, at its freeze."""
    return FROZEN_POOLS_SET in [str(r).strip() for r in (decl.get("requires") or [])]


def branch_of(decl: Dict[str, Any]) -> str:
    """The BRANCH this workload's cycle lives on — the workflow slug.

    Four workloads share `wb:studio_ai`, and a bench's branches are its parallel lines of work, so
    the slug is the branch: loading all four onto `main` would have each overwrite the last. The
    policy's `workflows` list names branches (that is what the driver runs), and it is generated
    from this, so the two cannot drift. A declaration that names its own lineage in
    `moderator.branch` gets `<slug>/<lineage>`; all four currently say `main`, which is the default
    line of the workload and therefore the slug itself."""
    slug = str(decl.get("workflow") or "").strip()
    mod = decl.get("moderator") if isinstance(decl.get("moderator"), dict) else {}
    lineage = str(mod.get("branch") or "main").strip()
    return slug if lineage in ("", "main") else "%s/%s" % (slug, lineage)


def for_bench_branch(kernel, bench: str, branch: str) -> Dict[str, Any]:
    """The workload whose cycle is this bench's branch, or {}.

    This is how a RUN finds its declaration: a scheduled job knows the bench it is advancing and
    the branch it is on, and that pair identifies the workload without anyone passing a name
    along. It is what lets the reservation derive its appetite from the declaration rather than
    from whoever submitted the job."""
    b = (bench or "").strip()
    b = b[3:] if b.startswith("wb:") else b
    br = (branch or "").strip()
    for d in declarations(kernel):
        if bench_slug(d) == b and branch_of(d) == br:
            return d
    return {}


def workload_appetite(kernel, bench: str, branch: str):
    """The hook the workflow layer calls to DERIVE a reservation's accounting key + appetite.

    `(key, llm_calls_per_run)` from the declaration this (bench, branch) belongs to, or `(None, 0)`
    when it belongs to none. Derived, never submitter-chosen: a client that could name its own key
    could spend another programme's carry-over credit."""
    d = for_bench_branch(kernel, bench, branch)
    if not d:
        return None, 0
    return key(d) or None, appetite(d)["llm_calls_per_run"]


def on_bench(kernel, bench: str) -> List[Dict[str, Any]]:
    """Every workload declared on this bench (accepts `wb:studio_ai` or `studio_ai`)."""
    b = (bench or "").strip()
    b = b[3:] if b.startswith("wb:") else b
    return [d for d in declarations(kernel) if bench_slug(d) == b]


# ── the five fields the driver reads ──────────────────────────────────────────────────────────

def trigger(decl: Dict[str, Any]) -> Dict[str, Any]:
    """The trigger, normalized: `{"boot": bool, "every_s": float, "daily": "HH:MM"}`.

    `every:1800s` and `daily:07:00Z` are the two forms the schema freezes. Daily is UTC — the `Z`
    is in the declaration's own spelling so nobody has to remember which clock it is on."""
    t = decl.get("trigger") if isinstance(decl.get("trigger"), dict) else {}
    out = {"boot": bool(t.get("boot")), "every_s": 0.0, "daily": ""}
    then = str(t.get("then") or "")
    m = _EVERY_RE.match(then)
    if m:
        out["every_s"] = float(m.group(1))
        return out
    m = _DAILY_RE.match(then)
    if m:
        out["daily"] = "%s:%s" % (m.group(1), m.group(2))
    return out


def duty(decl: Dict[str, Any]) -> str:
    """The declared duty id, defaulting to best-effort — the guarantee you get when you ask for
    none. Never inferred from the domain (workbench doctrine rule 2)."""
    d = str(decl.get("duty") or "").strip()
    return d if d in _DUTIES else DUTY_BEST_EFFORT


def is_continuous(decl: Dict[str, Any]) -> bool:
    return duty(decl) == DUTY_CONTINUOUS


def effect(decl: Dict[str, Any]) -> str:
    e = str(decl.get("effect") or "").strip()
    return e if e in _EFFECTS else EFFECT_RECORD


def appetite(decl: Dict[str, Any]) -> Dict[str, Any]:
    """`{"llm_calls_per_run": int, "weight": float}` — what ONE run asks of the model provider."""
    a = decl.get("appetite") if isinstance(decl.get("appetite"), dict) else {}
    return {"llm_calls_per_run": _int(a.get("llm_calls_per_run"), 0),
            "weight": _float(a.get("weight"), 0.0)}


def budget(decl: Dict[str, Any]) -> Dict[str, Any]:
    """`{"per_day": int, "max_wall_s": float, "max_steps": int}` — what a DAY of it may cost.

    `per_day` is the airing allowance: how many times this workload may run in a UTC day. It is
    not a poll count, and the distinction is not academic — reading it as poll beats is what
    served `219 / 4320` to guests on the day the real ceiling was spent."""
    b = decl.get("budget") if isinstance(decl.get("budget"), dict) else {}
    return {"per_day": _int(b.get("per_day"), 0),
            "max_wall_s": _float(b.get("max_wall_s"), 0.0),
            "max_steps": _int(b.get("max_steps"), 0)}


def interval_s(decl: Dict[str, Any]) -> float:
    """The nominal gap between runs, from the TRIGGER — `every_s`, else 86400 for a daily one,
    else 0 (no cadence, so no freshness guard and no next-slot hint)."""
    t = trigger(decl)
    if t["every_s"]:
        return t["every_s"]
    return 86400.0 if t["daily"] else 0.0


def _int(v, dflt):
    try:
        return int(v)
    except (TypeError, ValueError):
        return dflt


def _float(v, dflt):
    try:
        return float(v)
    except (TypeError, ValueError):
        return dflt


# ── the automation policy a society stores ────────────────────────────────────────────────────

def policy(decl: Dict[str, Any]) -> Dict[str, Any]:
    """The autorun policy this declaration projects onto its society.

    The society's stored policy is what the driver reads on every tick, so it carries the five
    fields verbatim — not a translation of them. `workflows` and `requires` ride along because the
    driver needs to know WHAT to run and WHAT it waits for, and both are derived mechanically:
    the workflow list is the declared `workflows` (or the one workflow branch), `sweeps` rides
    along when declared, and `requires` is the declaration's own."""
    t = trigger(decl)
    # The trigger in the policy's OWN grammar (`trigger: boot|manual`, `then: interval:<s>|
    # daily:HH:MM|none`). The declaration spells it `{"boot": true, "then": "every:1800s"}`, which
    # reads better in a file; the policy keeps the spelling the driver's `autorun_due` has always
    # parsed, so this is a projection and not a second scheduler grammar to keep in step.
    pol = {
        "workflows": workflows_of(decl),
        "duty": duty(decl),
        "effect": effect(decl),
        # Whether the output faces a ROOM, decided once from the declaration and
        # carried — `effect` alone cannot answer it (a channel publishes too).
        "room": publishes_to_room(decl),
        "appetite": appetite(decl),
        # The policy's own three budget keys. `per_day` and `runs_per_day` are ONE number under two
        # names — the declaration says `per_day` because that is what a day's allowance is called in
        # a file, the policy says `runs_per_day` because that is what the driver has always read.
        # Carrying both would be two places to change it.
        "budget": {"runs_per_day": budget(decl)["per_day"] or 4,
                   "max_steps": budget(decl)["max_steps"] or 500,
                   "max_wall_s": budget(decl)["max_wall_s"] or 14400},
        "trigger": "boot" if t["boot"] else "manual",
        "then": ("interval:%g" % t["every_s"]) if t["every_s"] else
                ("daily:%s" % t["daily"]) if t["daily"] else "none",
        "workload": key(decl),
    }
    if isinstance(decl.get("effect_read"), dict):
        pol["effect_read"] = dict(decl["effect_read"])
    if sweeps_of(decl):
        pol["sweeps"] = sweeps_of(decl)
    req = decl.get("requires")
    if isinstance(req, list) and req:
        pol["requires"] = list(req)
    return pol


# ── the Sets: every field a membership on the workload atom ───────────────────────────────────

SET_PREFIX = "set:wl:"


def _tok(s: str) -> str:
    """A Set-name token: lowercase, and anything that is not a word character or `:` becomes `_`.
    Mechanical, so a Set name is derivable from the declaration by hand and never invented."""
    return re.sub(r"[^a-z0-9:_.-]+", "_", str(s or "").strip().lower())


def field_sets(decl: Dict[str, Any]) -> List[str]:
    """The `set:wl:*` names this declaration's fields put the workload atom in.

    One membership per FIELD VALUE, named mechanically. Reading them back reconstructs the
    declaration's shape without opening the file, which is what makes `bench.info programmes`
    (= `set:wl:effect:publish` on the bench) a Set read instead of a name test."""
    t = trigger(decl)
    names = ["%sbench:%s" % (SET_PREFIX, _tok(bench_slug(decl))),
             "%sworkflow:%s" % (SET_PREFIX, _tok(decl.get("workflow"))),
             "%ssociety:%s:%s" % (SET_PREFIX, _tok(society_of(decl)[0]), _tok(society_of(decl)[1])),
             "%sduty:%s" % (SET_PREFIX, _tok(duty(decl).rsplit(":", 1)[-1])),
             "%seffect:%s" % (SET_PREFIX, _tok(effect(decl))),
             "%sappetite:calls:%d" % (SET_PREFIX, appetite(decl)["llm_calls_per_run"]),
             "%sbudget:per_day:%d" % (SET_PREFIX, budget(decl)["per_day"])]
    if t["boot"]:
        names.append("%strigger:boot" % SET_PREFIX)
    if t["every_s"]:
        names.append("%strigger:every:%ss" % (SET_PREFIX, _tok("%g" % t["every_s"])))
    if t["daily"]:
        names.append("%strigger:daily:%s" % (SET_PREFIX, _tok(t["daily"])))
    if decl.get("profile"):
        names.append("%sprofile:%s" % (SET_PREFIX, _tok(decl.get("profile"))))
    names.append("%sidset:%s" % (SET_PREFIX, _tok(idset_of(decl))))
    pins = decl.get("pins") if isinstance(decl.get("pins"), dict) else {}
    for p in sorted(pins):
        if not p.startswith("_"):
            names.append("%spins:%s" % (SET_PREFIX, _tok(p)))
    return names


def atom_alias(decl: Dict[str, Any]) -> str:
    """The workload atom's alias — `wl:<bench>:<slug>`."""
    return "wl:%s:%s" % (_tok(bench_slug(decl)), _tok(decl.get("workflow")))
