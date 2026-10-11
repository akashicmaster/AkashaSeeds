"""
wl_state — what a workload IS right now, and why. The driver's whole vocabulary.

Seed A slice 1 §4. A workload is in exactly ONE state at a time and a stop always carries a REASON,
both as vocabulary ids rather than strings assembled at the call site. Before this module the
driver said `skipped="station:reason:not_provisioned"` inline, which is two defects in one line:
the driver knew the word "station", and the id was a literal that no lexicon check could see.

THE PLATFORM RECORDS AND ANSWERS; THE APPLICATION NAMES (ruling 2026-09-23). The four states are
gone from this module: `on air`, `standing by`, `warming up` and `rebroadcast` are the STATION's
words for the station's own surface, and a platform module that stamps them has decided what an
application's status MEANS. What is left here is what the platform owns — the reasons a STOP can
carry that the platform itself decided, the cadence reads, the run record, and `workload.status`,
which returns `last` (what was recorded, with the op's own reason verbatim or empty) and `gate`
(the gate's own term). The sentence is composed by the application from those two.

WHO GETS A ROW — nobody. There is no guide row: `station:show:*` is deleted with the rest of the
stamped register. `publishes(pol)` survives as the one predicate for "does this workload have a
room someone can open", which is a DECLARATION field and not a status.

THE DUTY is the only behavioural switch (workbench doctrine rule 2). `continuous(pol)` reads it
from the policy the declaration projected; nothing asks what the workload is about.
"""
import logging
import math
import time
from typing import Any, Dict

from lib.akasha.api.trust import TRUST_INTERNAL as _TRUST_INTERNAL
from lib.akasha import api as _api
from lib.akasha.workbench import workload as W

logger = logging.getLogger("Akasha.Kernel")

# THE FOUR STATES ARE GONE. `warming_up` / `on_air` / `rebroadcast` / `standing_by` are the
# STATION's words for the station's own surface, and a platform module that owns them is deciding
# what a workload IS rather than recording what it did (ruling 2026-09-23 §2). `workload.status`
# returns `last` and `gate`; the application composes the sentence from them. The atoms keep their
# home in `ontology/station/` as the application's vocabulary.

# ── the eight reasons a stop carries (order §1.4) ─────────────────────────────────────────────
REASON_FRESH = "fresh"
REASON_LLM_POOL = "llm_pool"
REASON_PROVIDER_429 = "provider_429"
REASON_PROVIDER_CAPACITY = "provider_capacity"
REASON_PROVIDER_ABSENT = "provider_absent"
REASON_RUNS_PER_DAY = "runs_per_day"
REASON_NOT_PROVISIONED = "not_provisioned"
REASON_WAITING_SOURCE = "waiting_source"
REASON_BREAKER = "breaker"
REASON_NOT_DECLARED = "not_declared"   # this build carries no declaration for it — retired
# The guard's own stop (order v78): a continuous workload paid for runs that produced nothing.
REASON_SPENT_WITHOUT_EFFECT = "spent_without_effect"
# The driver's own hold (frontend 09-28): an ontology load in flight touches a name this workload
# declares (or it is the cell's first load). Held for the tick, not a run: nothing is recorded.
REASON_ONTO_LOAD = "onto_load"

REASONS = (REASON_FRESH, REASON_LLM_POOL, REASON_PROVIDER_429, REASON_PROVIDER_CAPACITY,
           REASON_PROVIDER_ABSENT, REASON_RUNS_PER_DAY, REASON_NOT_PROVISIONED,
           REASON_WAITING_SOURCE, REASON_BREAKER, REASON_NOT_DECLARED, REASON_SPENT_WITHOUT_EFFECT,
           REASON_ONTO_LOAD)

# How many CONSECUTIVE paid runs without the declared effect a continuous workload may make before
# the guard stops it. A declaration may set its own (`on_failure.spent_without_effect`).
SPENT_WITHOUT_EFFECT_K = 3


def job_spent(job) -> int:
    """The model calls one finished job actually spent — race-free.

    The worker marks a job DONE and settles its reservation a moment AFTER, so a read of the pool
    right after `await_job` can miss this very run. The job itself carries the answer on both sides
    of that moment: before the settle its reservation holds the running `consumed` count (the gate
    increments it on every call that returned text), after it `api_calls` holds the settled spend
    and the reservation handle is gone. One of the two is always there."""
    if job is None:
        return 0
    res = getattr(job, "llm_reservation", None) or {}
    try:
        return max(int(getattr(job, "api_calls", 0) or 0), int(res.get("consumed", 0) or 0))
    except (TypeError, ValueError):
        return 0


def spent_without_effect(state: Dict[str, Any], pol: Dict[str, Any], spent: int,
                         effect: bool) -> bool:
    """THE GUARD (order v78). Record one run's outcome on the streak; True when it must stop.

    A continuous workload keeps its cadence through a breaker — dropping a broadcaster to manual
    is the silence the airing ruling forbids — and that rule is what let the news show spend its
    whole day: every run failed "softly", none of them failed at all by the breaker's lights, and
    ~160 paid runs went by (09-25, pool 498/500) with nothing on air. Keeping the cadence is right
    when retrying costs nothing. It is wrong when every retry is paid for.

    So a run that SPENT calls and did not produce the declared effect extends a streak; a run that
    produced its effect, or spent nothing, ends it. K in a row trips the breaker for real, whatever
    the duty — the stop names itself (`spent_without_effect`), and a new build or config re-arms it
    (A35), which is the only thing that can change the outcome of a run that is being paid for and
    producing nothing. Only continuous workloads are counted; a best-effort workload already drops
    to manual on its ordinary breaker."""
    if not continuous(pol):
        return False
    if spent > 0 and not effect:
        state["spent_no_effect"] = int(state.get("spent_no_effect", 0)) + 1
        state["spent_no_effect_calls"] = int(state.get("spent_no_effect_calls", 0)) + int(spent)
    else:
        state.pop("spent_no_effect", None)
        state.pop("spent_no_effect_calls", None)
        return False
    try:
        k = int((pol.get("on_failure") or {}).get("spent_without_effect") or SPENT_WITHOUT_EFFECT_K)
    except (TypeError, ValueError):
        k = SPENT_WITHOUT_EFFECT_K
    return int(state["spent_no_effect"]) >= max(1, k)

_BROADCASTER = "system.broadcaster"

# How many times a start-up run that produced NO OUTPUT is retried before the obligation is
# written off. Only a `duty: continuous` workload owes one at all (`wb:duty:continuous` clause 3).
BOOT_AIRING_TRIES = 6


# ── pure reads of the policy the declaration projected ────────────────────────────────────────

def continuous(pol: Dict[str, Any]) -> bool:
    """Does this workload declare `duty: continuous`? The ONE behavioural switch."""
    return str((pol or {}).get("duty") or "") == W.DUTY_CONTINUOUS


def publishes(pol: Dict[str, Any]) -> bool:
    """Does this workload get a GUIDE ROW — i.e. does it publish to a room someone can open?

    The policy carries the answer (`room`), decided once from the declaration by
    `workload.publishes_to_room`. This used to test `effect == publish`, which is a DIFFERENT
    question: a workload that posts to an external channel publishes too and has no room. So
    provisioning gave it no guide row and the first driver tick grew one anyway — a programme in
    the guide whose room reads `unclassified`, which is exactly what asking the right question at
    provisioning was meant to prevent. Two predicates, one question, and the one that ran last won.

    THE FALLBACK IS GONE (P4, ruling 2026-09-23 §1). It read `effect == publish` when a policy
    carried no `room` key, so two predicates answered one question and the stale one won on every
    policy written before the `room` key existed — which is how the rooms showed a workload that
    posts to an external channel as having a room it does not have. `publishes_to_room` is the one
    predicate; a policy with no `room` has no room, and the next provisioning pass writes the key.
    An answer that is merely OLD is not a second source of truth, it is a wrong one."""
    return bool((pol or {}).get("room"))


def publishes_effect(pol: Dict[str, Any]) -> bool:
    """Does this workload's declared EFFECT face the public (`effect: publish`)?

    A DIFFERENT question from `publishes()` above, and the pair is exactly the conflation P4 was
    about — asked from the other side. `publishes()` answers "does it have a ROOM someone can
    open"; this answers "what does a run of it have to produce to have done its job". A workload
    that posts to an external channel has no room and its effect is still the post, so the two
    answers differ for it, and the allowance rule must ask THIS one: charged on the room predicate,
    every empty run of a channel workload would spend one of its day's runs, and a provider outage
    would eat the day's allowance on runs that said nothing — the exact failure
    `run_charges_allowance` exists to prevent."""
    return str((pol or {}).get("effect") or "") == W.EFFECT_PUBLISH


def interval_of(pol: Dict[str, Any]) -> float:
    """The nominal gap between runs, from the policy's cadence (`then`). 0 when it declares none.

    `interval:<seconds>` is the gap itself; a `daily:HH:MM` one is a day. Read from `then` and not
    from a studio registry keyed on a group — that lookup is what made the interval a property of
    who you were rather than of what you declared."""
    then = str((pol or {}).get("then") or "")
    if then.startswith("interval:"):
        try:
            return float(then.split(":", 1)[1])
        except (TypeError, ValueError):
            return 0.0
    return 86400.0 if then.startswith("daily:") else 0.0


# The reasons a RETRY can fix. A run that produced nothing for one of these failed at something
# that changes on its own — the pool refills, a provider's back-off expires, a model answers next
# time — so the driver arms its ladder and tries again in minutes. Every OTHER reason, including
# every id the platform has never heard of, is a grant or a precondition: no retry can create a
# workflow, admit a cast or load a pack, and hammering the same wall wastes the day's allowance and
# fills the log. Those wait for the next provisioning pass or boot, which is the thing that CAN fix
# them (order 2026-09-22 §3).
# The LLM gateway's "a model was called and returned nothing" is transient too: the retry ladder
# READS that outcome id on a run that reported it; the platform never writes it (group 4).
TRANSIENT_REASONS = (REASON_LLM_POOL, REASON_PROVIDER_429, REASON_PROVIDER_CAPACITY, "no_text")


def is_transient(reason: str) -> bool:
    """Is this reason one a retry can fix? An unknown id is NOT — the safe answer for a reason the
    platform does not know is to wait for provisioning, not to spin."""
    return str(reason or "").strip() in TRANSIENT_REASONS


def next_window(pol: Dict[str, Any], now: float, last_run: float = 0.0) -> float:
    """When the TRIGGER next opens — the honest answer to "when will this update?".

    Not `now + interval`: that is the gap after a run that WORKED, and using it for a run that
    produced nothing told a reader an update was coming in half an hour when the programme was
    standing by on a precondition no clock would fix. `interval:` is the gap from the last run that
    produced its effect; `daily:` is the next occurrence of its UTC minute; anything else has no
    window and returns 0.

    **THE ANSWER IS ALWAYS IN THE FUTURE.** `last_run + interval` is the next slot measured from
    the EFFECT clock, and a run that produced nothing never advances that clock — so once the gap
    since the last effect exceeds one cadence, `last_run + interval` is a moment in the PAST. The
    driver wrote it into `retry_at`, `retry_at <= now` read as "due", and a four-hourly declaration
    was attempted on every 60-second tick of the day (D1: 87 runs in 90 minutes). The window is
    therefore rolled forward by whole cadences until it is strictly after `now`, which is what
    `daily:` has always done with its `+ 86400`; `interval:` simply never did the same.

    Rolling by WHOLE cadences, rather than answering `now + interval`, keeps the declared phase: a
    programme that airs on the hour still airs on the hour after a day of standing by."""
    then = str((pol or {}).get("then") or (pol or {}).get("trigger") or "")
    if then.startswith("interval:"):
        try:
            iv = float(then.split(":", 1)[1])
        except (TypeError, ValueError):
            return 0.0
        if iv <= 0:
            return 0.0                            # a cadence of zero is no cadence, not a busy loop
        anchor = float(last_run or 0.0)
        if not anchor:
            return now + iv
        nxt = anchor + iv
        if nxt <= now:                            # overdue: advance to the next slot AFTER now
            nxt = anchor + (math.floor((now - anchor) / iv) + 1) * iv
        return nxt if nxt > now else now + iv     # float drift, answered rather than trusted
    if then.startswith("daily:"):
        try:
            hh, mm = [int(x) for x in then.split(":", 1)[1].split(":")]
        except (TypeError, ValueError, IndexError):
            return 0.0
        target = now - (now % 86400) + hh * 3600 + mm * 60
        return target if target > now else target + 86400.0
    return 0.0


def next_attempt(pol: Dict[str, Any], now: float, last_run: float = 0.0) -> float:
    """WHEN THIS WORKLOAD NEXT TRIES — the one moment every run-end branch writes back.

    `next_window` answers "when does the TRIGGER next open", and for a policy whose cadence it
    cannot read that is honestly 0. A driver that writes 0 into `retry_at` has written nothing:
    the key reads falsy, `autorun_due` falls through to the trigger's own evaluation, and that
    evaluation measures from `last_run` — the EFFECT clock, which a run that produced nothing
    never advances. The window is then open for ever and the workload is attempted on every tick
    of the day (D1: 87 runs in 90 minutes for a four-hourly declaration).

    So: the trigger's window if it has one; else one declared cadence from NOW; else 0, and 0 here
    means the policy declares no cadence at all (`boot` with `then: none`, or `manual`), for which
    `autorun_due` already answers False and the next boot is the next attempt. The difference
    between "no moment yet" and "no moment ever" is the whole of the bug.

    **THIS IS THE ONE FUNCTION.** The driver writes what it returns into `retry_at`, and
    `status()` reports it as `next_at` — one question, one answer. They used to be two calls to
    two functions, and two functions that answer one question are two functions that can disagree:
    the guide can promise an update at a moment the driver has no intention of trying.

    A non-zero answer is ALWAYS strictly in the future (asserted here, not merely intended). A
    `retry_at` in the past is not a schedule — it is the absence of one wearing a number, and it
    reads as "due" on every tick for the rest of the day."""
    w = next_window(pol, now, last_run)
    if not w:
        iv = interval_of(pol)
        w = (now + iv) if iv else 0.0
    if w and w <= now:
        # Unreachable by construction; kept because the cost of being wrong here is a 60-second
        # loop against a paid provider, and one comparison is cheaper than finding that again.
        logger.warning("[bench] next_attempt computed a past moment (%.0f <= %.0f) for then=%r — "
                       "answered one cadence out instead", w, now, (pol or {}).get("then"))
        w = now + (interval_of(pol) or 3600.0)
    return w


def key_of(pol: Dict[str, Any]) -> str:
    """The workload's accounting key, as the declaration set it."""
    return str((pol or {}).get("workload") or "")


def reason_id(reason: str) -> str:
    """The reason, as it was given. Whitespace off, and nothing else.

    It used to NAMESPACE a bare id into `station:reason:<id>` — the platform taking an op's word
    and restating it in the station's vocabulary, which is the fault this ruling is about in its
    smallest form. A reason the op wrote passes through; a reason the op did not write stays
    empty."""
    return str(reason or "").strip()


# ── writing what happened ─────────────────────────────────────────────────────────────────────

def note(kernel, gid: str, space: str, effect: int = 0, skipped: str = "",
         interval_s: float = None, pol: Dict[str, Any] = None, next_at: float = None) -> None:
    """The run is RECORDED, and the record is the bench's own observation. Nothing is stamped.

    This used to upsert a platform-owned guide row — `station:show:<gid>:<space>` — carrying
    `state`, `reason`, `today`, `next_burst_at`, `skipped`. That row is deleted (ruling 2026-09-23):
    every field on it was the platform NAMING application status, and it was a second copy of facts
    the bench stream already held, so the two could and did disagree. `workload.status` derives the
    same answers from the one record, and the station's words are composed by the station.

    The function survives as the ONE place the driver reports a run, because the log line and the
    roll-up the Health segment reads are the platform's own observability and they stay."""
    if int(effect or 0) <= 0 and str(skipped or ""):
        logger.info("[bench] run stood by workload=%s/%s reason=%s", gid, space,
                    reason_id(skipped) or "-")


def gate(kernel, gid: str, space: str, reason: str, pol: Dict[str, Any] = None) -> None:
    """A gate stopped this workload: say so, in the vocabulary, at the place that decided it.

    A research bench that waits is simply idle; a publishing workload that waits is a listener
    looking at a room, so the stop is written where the room reads it."""
    note(kernel, gid, space, effect=0, skipped=reason, pol=pol)


def _policy(kernel, gid: str, space: str) -> Dict[str, Any]:
    """The policy for this society, from its declaration — the fallback when the caller has not
    already read one. A society with no declaration answers {}, and every predicate above is
    False for it, which is precisely the old behaviour for a society that was not a programme."""
    decl = W.for_society(kernel, gid, space)
    return W.policy(decl) if decl else {}


# ── THE RUN RECORD — the platform's own (group 4, 4.12(a)) ────────────────────────────────────
#
# `workload.status.last` used to be read from the APPLICATION's rows (the station's aired
# observations, `station.air.ls` since 10-02): the platform took the application's record for its
# own. So a run that never wrote an application row — refused at admission, failed before its
# first step, or whose row was keyed under another workload (the X channel's row under its source
# programme, 09-26) — had NO recorded outcome at all, and `last` answered with some other run's row.
#
# The driver now writes ONE ROW PER RUN into the workload's own namespace, whatever happened:
#
#     {at, ok, reason, effect_count, spent, by, job_id}
#
# `reason` is the op's own id or message, verbatim, or empty; the platform never substitutes one.
# Storage is a bounded ring in the nucleus vault (`wl_run/<key>`): the newest RUN_RECORD_KEEP rows,
# each write O(1) and pruned in the same write — the lifecycle ships with the write (memory
# discipline R5), and the population is one ring per DECLARED workload (R2).
RUN_RECORD_NS = "wl_run"
RUN_RECORD_KEEP = 200


def _vault(kernel):
    return getattr(getattr(kernel, "manager", None), "shared_nucleus", None)


def onto_hold(kernel, pol: Dict[str, Any]) -> Dict[str, Any]:
    """Must this workload wait for the ontology load in flight? `{}` when it need not, else
    `{"reason": "onto_load", "first": bool, "packs": [...], "names": [...]}`.

    A load used to hold EVERY workload (S2-k4), so one 400-atom pack stopped five programmes for 17
    minutes (frontend 09-28, needs platform 1). Now the load says what it TOUCHES
    (`ontology.loader.in_flight`: `first`, and the packs found changed so far):

      * on a cell's FIRST load the graph is genuinely empty, so everything waits, as before;
      * otherwise a workload waits only when a pack in flight declares one of the ontology names
        the workload declares (`W.ontology_names`: its `pins`, its `requires` Sets). An unchanged
        pack's atoms are already in place, and a Set a workload `requires` that has not landed yet
        is already the `source_ready` fact's to hold.

    Each loading pack is scanned once per load, for the union of every declaration's names, and
    the answer is kept on the in-flight record. Never raises: an unreadable answer holds."""
    from lib.akasha.api import schedule as _sched
    if not _sched.is_running(kernel, "ontology.loaded"):
        return {}
    try:
        from lib.akasha.ontology import loader as _ld
        fl = _ld.in_flight(kernel)
        if not fl or fl.get("first"):
            return {"reason": REASON_ONTO_LOAD, "first": True, "packs": list(fl.get("packs") or []),
                    "names": []}
        decl = W.by_key(kernel, key_of(pol)) or {}
        mine = set(W.ontology_names(decl))
        if not mine:
            return {}
        declares = fl.setdefault("declares", {})
        wanted = None
        touched, packs = set(), []
        for pack in list(fl.get("packs") or []):
            if pack not in declares:
                if wanted is None:
                    wanted = set()
                    for d in W.declarations(kernel):
                        wanted |= set(W.ontology_names(d))
                declares[pack] = _ld.pack_declares(pack, wanted)
            hit = mine & declares[pack]
            if hit:
                touched |= hit
                packs.append(pack)
        if not touched:
            return {}
        return {"reason": REASON_ONTO_LOAD, "first": False, "packs": packs, "names": sorted(touched)}
    except Exception as exc:                      # noqa: BLE001 — unsure means wait, and say so
        logger.warning("[bench.auto] onto_hold unreadable key=%s: %s: %s", key_of(pol),
                       type(exc).__name__, exc)
        return {"reason": REASON_ONTO_LOAD, "first": False, "packs": [], "names": []}


def record_run(kernel, wl_key: str, at: float, ok: bool, reason: str = "", effect_count: int = 0,
               spent: int = 0, by: str = "", job_id: str = "", job_ok: bool = None) -> Dict[str, Any]:
    """Write this run's row. Never raises: a run whose record could not be written is logged at
    WARNING with the row, so the outcome still reaches the operator.

    `ok` means THE DECLARED EFFECT HAPPENED (D15) — the job succeeded and the run produced what the
    workload declared, by `run_charges_allowance`. `job_ok` is the job's own outcome, kept beside it
    so a stood-by run (job fine, no effect, a reason) is not mistaken for a failed one either.
    Absent, `job_ok` is `ok`."""
    row = {"at": float(at or time.time()), "ok": bool(ok), "reason": str(reason or ""),
           "effect_count": int(effect_count or 0), "spent": int(spent or 0),
           "by": str(by or ""), "job_id": str(job_id or ""),
           "job_ok": bool(ok if job_ok is None else job_ok)}
    k = str(wl_key or "").strip()
    nuc = _vault(kernel)
    if not k or nuc is None:
        return row
    try:
        cur = nuc.vault_retrieve(RUN_RECORD_NS, k) or {}
        rows = list(cur.get("rows") or [])
        rows.append(row)
        if len(rows) > RUN_RECORD_KEEP:
            rows = rows[-RUN_RECORD_KEEP:]
        nuc.vault_store(RUN_RECORD_NS, k, {"seq": int(cur.get("seq", 0)) + 1, "rows": rows})
    except Exception as exc:                      # noqa: BLE001 — reported, never a lost outcome
        logger.warning("[bench] run record NOT written workload=%s row=%s: %s", k, row, exc)
    return row


def run_records(kernel, wl_key: str, limit: int = 0):
    """This workload's recorded runs, oldest first (the ring is written in time order)."""
    nuc = _vault(kernel)
    if nuc is None:
        return []
    try:
        rows = list((nuc.vault_retrieve(RUN_RECORD_NS, str(wl_key or "").strip()) or {}).get("rows")
                    or [])
    except Exception:
        return []
    return rows[-int(limit):] if limit and int(limit) > 0 else rows


def last_run(kernel, wl_key: str) -> Dict[str, Any]:
    """The newest recorded run, or {}."""
    rows = run_records(kernel, wl_key, limit=1)
    return dict(rows[-1]) if rows else {}


# ── THE EFFECT, read through the op the declaration names (4.12(b)) ──────────────────────────
#
# The driver used to count a run's airings by asking the station's list op (`station.air.ls` since
# 10-02) itself — the platform naming an application's method and reading its rows as if they were
# the platform's. A declaration now SAYS how its effect is read:
#
#     "effect_read": {"op": "<method>", "args": {...}, "rows": "<result key>",
#                     "effect": "<row field>", "reason": "<row field>", "at": "<row field>"}
#
# The op is dispatched (as admin, internal) with `args` — `{bench}`, `{key}`, `{gid}`, `{space}`
# substituted — plus `since=<the run's start>`, so it returns ONE RUN's rows. The effect count is
# the rows whose `effect` field is truthy; the reason is the newest non-effect row's `reason`,
# verbatim. `rows`/`effect`/`reason`/`at` default to those very words. A declaration that names no
# read has no effect the platform can count: a job that succeeded IS its effect.
_EFFECT_DEFAULTS = {"rows": "rows", "effect": "effect", "reason": "reason", "at": "at"}


def effect_read(pol: Dict[str, Any]) -> Dict[str, Any]:
    """The declared read, as the policy carries it — {} when none (or malformed)."""
    er = (pol or {}).get("effect_read")
    if not isinstance(er, dict) or not str(er.get("op") or "").strip():
        return {}
    out = dict(_EFFECT_DEFAULTS)
    out.update({k: v for k, v in er.items() if v not in (None, "")})
    return out


def _subst(v, ctx: Dict[str, str]):
    if isinstance(v, str):
        for k, val in ctx.items():
            v = v.replace("{%s}" % k, val)
    return v


def _row_at(r: Dict[str, Any], field: str = "at") -> float:
    """A row's wall-clock moment — its declared `at` field, or `created_at`."""
    try:
        return float(r.get(field) or r.get("created_at") or 0.0)
    except (TypeError, ValueError, AttributeError):
        return 0.0


def effect_rows(kernel, pol: Dict[str, Any], since: float = 0.0):
    """The rows the declared effect read returns, in time order — or None when the workload
    declares no read (or the op refused: a read that did not happen is not a read of nothing)."""
    er = effect_read(pol)
    if not er:
        return None
    key = key_of(pol)
    decl = W.by_key(kernel, key) or {}
    gid, space = W.society_of(decl) if decl else ("", "")
    bench = str(W.bench_slug(decl) or "") if decl else ""
    ctx = {"bench": bench[3:] if bench.startswith("wb:") else bench, "key": key,
           "gid": gid or "", "space": space or ""}
    data = {k: _subst(v, ctx) for k, v in (er.get("args") or {}).items()}
    if since:
        data["since"] = repr(float(since))
    try:
        r = kernel.dispatch({"jsonrpc": "2.0", "method": str(er["op"]),
                             "params": {"client_id": "admin", "data": data},
                             "id": "wl-effect"}, _TRUST_INTERNAL)
    except Exception as exc:                      # noqa: BLE001 — reported
        logger.warning("[bench] effect read FAILED workload=%s op=%s: %s", key, er["op"], exc)
        return None
    if not isinstance(r, dict) or "result" not in r:
        logger.warning("[bench] effect read refused workload=%s op=%s error=%s", key, er["op"],
                       (r or {}).get("error") if isinstance(r, dict) else r)
        return None
    rows = [x for x in ((r["result"] or {}).get(er["rows"]) or []) if isinstance(x, dict)]
    rows.sort(key=lambda x: _row_at(x, er["at"]))
    return rows


def run_effect(kernel, pol: Dict[str, Any], since: float):
    """(effect count, reason) for the run that began at `since` — read through the declared op.

    No declared read → (1, ""): the job succeeded, and that is the effect. A declared read that
    returns rows counts the ones stamped after the run began whose effect field is truthy; when
    there are none, the newest such row's own reason — verbatim, or empty."""
    er = effect_read(pol)
    rows = effect_rows(kernel, pol, since=since)
    if rows is None:
        return (1, "") if not er else (0, "")
    mine = [x for x in rows if _row_at(x, er["at"]) > float(since or 0)]
    n = sum(1 for x in mine if x.get(er["effect"]))
    if n:
        return n, ""
    for x in reversed(mine):
        if not x.get(er["effect"]) and x.get(er["reason"]):
            return 0, str(x[er["reason"]])
    return 0, ""


def wl_status(kernel) -> Dict[str, Any]:
    """The driver's live roll-up — what the Health line reports, in one record.

    It lived on the kernel as `_station_status`, which is application state on the heart and a name
    for one programme besides. It is the workload layer's own record now, and the Health hook reads
    it from here (order §3): no heart attribute carries what a workload is doing."""
    st = getattr(kernel, "_wl_status", None)
    if st is None:
        st = kernel._wl_status = {"effects_today": 0, "day": "", "standby": False,
                                  "reason": None, "since": 0.0, "last_log": 0.0, "consec_zero": 0}
    return st


def wl_note(kernel, r: Dict[str, Any]) -> None:
    """Report one run's outcome into the roll-up, and make a STANDBY visible.

    A workload that produced nothing used to be silent by design — the loop logged only when it had
    output, so a run standing by (no material, no model, the model produced nothing) said nothing at
    all. Now: the output is logged as before, and a zero-output run logs its reason at WARNING once
    per reason CHANGE and at most hourly, with a `resumed` line when output returns. Also rolls the
    daily counter the Health segment reads.

    `reason_key` is the CHANGE-detection key, and it is separate from the displayed `reason` for a
    reason: a provider back-off's display carries a live "retry in <s>" countdown that changes every
    run, which would defeat the once-per-change throttle. The key stays constant while backed off."""
    now = time.time()
    st = wl_status(kernel)
    day = time.strftime("%Y-%m-%d", time.gmtime(now))
    if st.get("day") != day:
        st["day"], st["effects_today"] = day, 0
    produced = int(r.get("effect") or 0)
    if produced:
        st["effects_today"] = st.get("effects_today", 0) + produced
        if st.get("standby"):
            logger.info("[bench] resumed — produced %s from %s (was standing by: %s)",
                        produced, r.get("source"), st.get("reason"))
        st.update({"standby": False, "reason": None, "consec_zero": 0})
        logger.info("[bench] produced %s from %s", produced, r.get("source"))
        return
    reason = r.get("reason") or "unknown"
    key = r.get("reason_key") or reason
    st["consec_zero"] = int(st.get("consec_zero", 0)) + 1
    first = not st.get("standby")
    changed = key != st.get("reason_key")
    if first:
        st["since"] = now
    # While standing by on a provider back-off, `since` is the back-off window's PERSISTED start, so
    # the line is unchanged across a restart (the window is inherited, not reset).
    if "backoff" in str(key):
        try:
            from lib.akasha.workbench import llm_provider as _lp
            _since = _lp.backoff_since(_lp.active(kernel))
            if _since:
                st["since"] = _since
        except Exception:
            pass
    if first or changed or (now - float(st.get("last_log", 0.0)) >= 3600.0):
        logger.warning("[bench] standing by: %s (since %s)", reason,
                       time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(st.get("since", now))))
        st["last_log"] = now
    st.update({"standby": True, "reason": reason, "reason_key": key})


def health_segment(kernel) -> str:
    """The Health line's workload segment — `workloads(effects_today=… standby=… auto=…)`.

    Registered as the `workload_health_segment` hook and called the way `llm_health_segment` is, so
    the heart composes a line it does not author. It replaces two heart-authored fields, one of
    which named a single programme (`station(…)`) and one of which read a kernel attribute
    (`bench(auto=…)`) — both are workload facts and both are read from here now."""
    st = wl_status(kernel)
    return " workloads(effects_today=%s standby=%s auto=%s)" % (
        st.get("effects_today", 0),
        (st.get("reason") or "-") if st.get("standby") else "-",
        driver_status(kernel) or "-")


def driver_status(kernel, status: str = None) -> str:
    """The driver's one-line status, read or written — `waiting:data(…)`, `budget:…`, `runs_today=N`.

    A record here rather than `kernel._bench_auto_status`: the heart carries no attribute that says
    what a workload is doing."""
    if status is not None:
        wl_status(kernel)["driver"] = str(status)
    return str(wl_status(kernel).get("driver") or "")


# ── the public mirror's housekeeping (moved from station.py; §2) ──────────────────────────────

def schedule_mirror_gc(kernel) -> None:
    """Nightly HARD purge of orphaned mirror atoms — the copies trimmed out of a public space's
    rolling window, which the trim unlinks but does not delete.

    The method it drives (`society.broadcast.gc`) is unchanged; only the schedule's home moved."""
    kernel._schedule_backlog_gc("mirror-gc", "society.broadcast.gc", "broadcast", "mirror.compact")


def last_effect_at(kernel, wl_key: str, pol: Dict[str, Any] = None) -> float:
    """When this workload last PRODUCED ITS EFFECT — from the platform's own run record.

    NOT the time of the last run: a run that produced nothing is recorded too, and treating it as
    an effect is how a `fresh` skip once swallowed a deploy's boot run for a workload that had
    never produced anything. The record is keyed by the WORKLOAD, so four workloads sharing one
    bench each answer for themselves.

    A cell whose ring is still empty (the first boot of the build that introduced it) asks the
    declared effect read once, so a redeploy minutes after a real effect is still `fresh`."""
    rows = run_records(kernel, wl_key)
    for r in reversed(rows):
        if int(r.get("effect_count") or 0) > 0:
            return float(r.get("at") or 0.0)
    if rows or not pol:
        return 0.0
    er = effect_read(pol)
    for x in reversed(effect_rows(kernel, pol) or []):
        if x.get(er["effect"]):
            return _row_at(x, er["at"])
    return 0.0


def spent_today(kernel, wl_key: str) -> int:
    """The model calls charged to this workload key today, from the pool's own by[program] tally.

    It asked a hook called `llm_spent_today`, which NOTHING REGISTERS — so the `except` swallowed
    the `None` and `spent_today` was 0 for every workload while the pool settled three calls a run
    (D5). The registered hooks are `llm_program_spent(program, provider)` and
    `llm_active_provider(kernel)`; a hook name that no manifest carries is a spelling mistake the
    platform cannot see at boot, so this reads them by their real names and reports a miss instead
    of returning a confident zero."""
    try:
        spent_fn = _api.hook(kernel, "llm_program_spent")
        prov_fn = _api.hook(kernel, "llm_active_provider")
        if not spent_fn or not prov_fn:
            logger.debug("[bench] spent_today unavailable key=%s (no llm hooks on this cell)", wl_key)
            return 0
        return int((spent_fn(str(wl_key or ""), str(prov_fn(kernel) or "")) or {}).get("calls", 0))
    except Exception as exc:                      # noqa: BLE001 — reported, never a failed read
        logger.warning("[bench] spent_today FAILED key=%s reason=%s: %s", wl_key,
                       type(exc).__name__, exc)
        return 0


def status(kernel, wl_key: str) -> Dict[str, Any]:
    """`workload.status key=` — what the platform RECORDED and what the gate ANSWERS. No `state`.

    Ruling 2026-09-23 §2. Four fields and not one word of application vocabulary:

        last        {at, ok, job_ok, reason, effect_count, spent, by, job_id}
                                          the newest run the DRIVER recorded for this workload —
                                          the platform's own run record, one row per run whatever
                                          happened. `ok` = the declared EFFECT happened (D15),
                                          `job_ok` = the job succeeded. `reason` is the op's own
                                          id or message, verbatim, and empty when it gave none.
        gate        {run: "ok" | <term>}  the gate's answer for `run` on this key: one of
                                          `declared`/`armed`/`source_ready`/`headroom`, which is
                                          the only reason vocabulary the platform owns.
        next_at     when this workload next TRIES — `next_attempt`, the same function the driver
                    writes into `retry_at`. One question, one answer: a guide that computed its
                    own could promise an update at a moment the driver never intended to try.
        spent_today the model calls charged to this key today, from the pool.

    "On air", "standing by", "rebroadcast" and the sentences around them are the APPLICATION's
    words. The station Concept Model composes them from `last` and `gate` — `ok` inside the trigger
    window is on air, anything else is standing by with the reason or the term. The platform does
    not know what those phrases mean and has no business deciding when they are true."""
    from lib.akasha.api import gate as _gate
    decl = W.by_key(kernel, str(wl_key or "")) or {}
    if not decl:
        return {"key": str(wl_key or ""), "declared": False, "last": {}, "gate": {},
                "next_at": 0.0, "spent_today": 0}
    gid, space = W.society_of(decl)
    pol = W.policy(decl)
    # THE PLATFORM'S OWN RECORD (4.12(a)) — a refused run, a failed run and a run whose
    # application row is keyed elsewhere are each still a recorded run with its reason.
    last = last_run(kernel, str(wl_key or ""))
    # REACH is asked of the workload's own SPACE, the FACTS of its key (frontend 26d, needs
    # platform 1): the key is not a place, and a lab's key does not spell its space.
    ok, why = _gate.gate(W.client_of(decl), _gate.RUN, str(wl_key or ""),
                         place=W.client_places(decl)[0])
    spent = spent_today(kernel, str(wl_key or ""))
    return {"key": str(wl_key or ""), "declared": True, "society": "%s/%s" % (gid, space),
            "last": last, "gate": {"run": "ok" if ok else (why or "")},
            "next_at": next_attempt(pol, time.time(), last_effect_at(kernel, str(wl_key or ""))),
            "spent_today": spent}


def handle_status(kernel, rid, data, session, ctx) -> dict:
    """`workload.status key=` — the RPC door onto `status()` above.

    A read, and guest-safe by the same reasoning as the rest of the guide: everything it returns
    is either an observation the bench already publishes or the gate's own answer, and a guest who
    may not read the bench gets an empty `last` from the op it asks, not a decision taken here."""
    from lib.akasha.api.rpc import err as _e, ok as _o
    k = str((data or {}).get("key") or "").strip()
    if not k:
        return _e(rid, -32602, "workload.status requires 'key'")
    return _o(rid, status(kernel, k))

