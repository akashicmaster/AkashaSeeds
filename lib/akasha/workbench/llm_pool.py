"""
llm_pool — B10: shared LLM resource ALLOCATION, the reservation layer that sits ON TOP of the A53
free-tier floor. Stdlib only. Credentials NEVER touch this module — it holds COUNTS, never keys/prompts.

The hard floor is A53's (`llm_provider._budget` / `_meter` / `_over_budget`, checked inside the one gate
`generate`): a metered self-imposed ceiling (calls/UTC-day + tokens/UTC-month), durable in the vault,
the LAST line of defence that trips even for a call that bypassed a reservation. B10 does NOT re-count
spend or re-check the floor — it reads A53's meter for `spent` and A53's budget for `capacity`, and adds
the ALLOCATION on top:

  • A programme RESERVES its per-run calls at admission (prepay) and runs prepaid; a reservation that
    would cross the ceiling is refused BEFORE anything is called, so a run never exhausts the cap
    halfway. Settled at the end (the unused returns).
  • A refused programme gains a CARRY-OVER credit; its owed calls are held back as headroom so a hog
    cannot starve a once-a-day programme (§2.1).
  • A rolling MEASURED mean overrides the declaration for the reservation when it diverges (§3).
  • The pool is projected into a guest-readable atom `llm:pool:<provider>:<day>` (COUNTS only), and a
    Health segment.

B10's own state (reserved / refused / by[program] / credits / measures) persists through an INJECTED
durable store (the kernel backs it with the shared-nucleus vault, category `llm_pool`), so `reserved`
survives a restart the same way A53's meter does. No thread, queue or parallelism is added.
"""
import logging
import threading
import time
import uuid

logger = logging.getLogger("Akasha.LLM")

_STORE = None                # injected durable store {"load": (key)->dict|None, "save": (key, dict)->None}
_MEM: dict = {}              # process-memory fallback (a bare test / no kernel)
_LOCAL = threading.local()   # the thread's active reservation, if any (set by begin_run)

_CREDITS_KEY = "credits"     # {program: {n, calls, since}} — carry-over, persists across days
_MEASURES_KEY = "measures"   # {program: {mean, n}} — the rolling call-count mean per program
# How many settled reservation ids one provider-day record remembers. A settle follows its reserve
# within one run, so a repeat arrives close behind the original and a recent window answers it; the
# cap is what stops a runaway from growing a day's record without bound (R5, the lifecycle ships
# with the write). The list dies with its day.
_SETTLED_CAP = 4096
_MEASURE_MIN_N = 5           # Stage 3: use the measured mean only once we have this many settles
_MEASURE_DELTA = 0.25        # …and it differs from the declaration by more than 25 %
_TOKENS_PER_CALL_EST = 1500  # reservation-time per-call token estimate


_REFUSE_LOG_AT: dict = {}     # (provider, program) -> last refusal log time; bounded by programmes
_REFUSE_LOG_EVERY_S = 3600.0  # a poll that finds no room must not log per poll


def _throttled_log(provider: str, program: str, fmt: str, *args) -> None:
    """One refusal line per (provider, programme) per hour, at WARNING — the decision is news, a
    poll loop repeating it is not. Bounded population: one entry per programme (memory R3)."""
    now = time.time()
    k = (_norm(provider), program or "?")
    if now - float(_REFUSE_LOG_AT.get(k, 0.0)) < _REFUSE_LOG_EVERY_S:
        return
    _REFUSE_LOG_AT[k] = now
    logger.warning(fmt, *args)


def set_pool_store(load, save) -> None:
    """Install the durable store (kernel: the shared-nucleus vault category `llm_pool`)."""
    global _STORE
    _STORE = {"load": load, "save": save}


def _load(key: str) -> dict:
    if _STORE:
        try:
            return dict(_STORE["load"](key) or {})
        except Exception:
            return {}
    return dict(_MEM.get(key) or {})


def _save(key: str, data: dict) -> None:
    if _STORE:
        try:
            _STORE["save"](key, data)
        except Exception:
            pass
    else:
        _MEM[key] = dict(data)


def _norm(provider: str) -> str:
    return (provider or "").strip().lower()


def day() -> str:
    """The pool day — the UTC date, matching A53's meter rollover and the telemetry day Set."""
    return time.strftime("%Y-%m-%d", time.gmtime())


def next_day_turn(now: float = None) -> float:
    """The moment the pool's day turns next — the next UTC midnight, which is when `day()` changes,
    the meter resets and a refused programme can be admitted again (D11). The POOL answers this,
    because the pool owns the day: a driver that guessed would retry into the same wall."""
    t = time.time() if now is None else float(now)
    return (t // 86400 + 1) * 86400.0


# ── the A53 floor is the source of truth for capacity + spend ───────────────────────────────────────

def _budget_of(provider: str) -> dict:
    """A53's self-imposed ceiling for this provider (calls_per_day / tokens_per_month), env-overridable.
    This IS the capacity — B10 never invents its own caps (directive §1.1)."""
    try:
        from lib.akasha.workbench import llm_provider
        return dict(llm_provider._budget(_norm(provider)) or {})
    except Exception:
        return {"calls_per_day": 0, "tokens_per_month": 0}


def _spent_of(provider: str) -> dict:
    """A53's meter for this provider (calls_today / tokens_month) — the authoritative spend. B10 reads
    it; the gate (A53) is the only writer of spend."""
    try:
        from lib.akasha.workbench import llm_provider
        q = llm_provider.quota(_norm(provider))
        return {"calls_today": int(q.get("calls_today", 0)), "tokens_month": int(q.get("tokens_month", 0))}
    except Exception:
        return {"calls_today": 0, "tokens_month": 0}


def caps(provider: str):
    """(cap_calls_per_day, cap_tokens_per_month) from A53's budget."""
    b = _budget_of(provider)
    return int(b.get("calls_per_day", 0)), int(b.get("tokens_per_month", 0))


def caps_source(provider: str) -> str:
    """Where the effective ceiling came from: `env`, `default`, or `<calls>/<tokens>` when the two
    disagree — one word when they agree, mirroring how `caps()` is printed.

    ONE ceiling is in force and a deploy can move it from outside the process, so the number alone
    cannot answer "did my override reach this host?". This is what makes the boot line diagnostic
    rather than decorative."""
    try:
        from lib.akasha.workbench import llm_provider
        _b, src = llm_provider.budget_with_sources(_norm(provider))
    except Exception:
        return "unknown"
    c, t = src.get("calls_per_day", "default"), src.get("tokens_per_month", "default")
    return c if c == t else "%s/%s" % (c, t)


def tokens_per_call() -> int:
    return _TOKENS_PER_CALL_EST


def route_provider(base: str, route: str = "shared") -> str:
    """§4 — resolve a society's `llm.route` to the provider whose pool the reservation draws from:
      • shared    (default) — the base provider's shared free tier;
      • dedicated — a SECOND record (`<base>#2`) with its own pool, so a society is isolated;
      • local     — `ollama` (unmetered by A53, but still reserved+settled so the ledger stays
                    comparable).
    Each distinct provider string is a distinct pool key + a distinct A53 meter key."""
    base = _norm(base) or "mistral"
    r = (route or "shared").strip().lower()
    if r == "local":
        return "ollama"
    if r == "dedicated":
        return base + "#2"
    return base


# ── B10's own per-(provider,day) state: reserved / refused / by[program] ─────────────────────────────

def _pool_key(provider: str, d: str) -> str:
    return "%s:%s" % (_norm(provider), d)


def _get_own(provider: str, d: str) -> dict:
    p = _load(_pool_key(provider, d))
    p.setdefault("reserved", 0)
    p.setdefault("refused", 0)
    p.setdefault("by", {})
    return p


def _by(pool: dict, program: str) -> dict:
    b = pool["by"].get(program)
    if not b:
        b = {"reserved": 0, "spent": 0, "tokens": 0, "runs": 0}
        pool["by"][program] = b
    return b


def _credits() -> dict:
    return _load(_CREDITS_KEY)


def credits(program: str) -> int:
    return int((_credits().get(program) or {}).get("n", 0))


def _measured_calls(program: str, declared: int) -> int:
    """Stage 3 — the reservation size the pool will actually use: the DECLARED value, unless a rolling
    mean over ≥5 settles differs from it by >25 %, in which case the measured mean is used (the
    declaration itself is never rewritten)."""
    m = (_load(_MEASURES_KEY).get(program) or {})
    n = int(m.get("n", 0))
    mean = float(m.get("mean", 0.0))
    if n >= _MEASURE_MIN_N and declared > 0 and mean > 0 and abs(mean - declared) / declared > _MEASURE_DELTA:
        logger.info("[llm] estimate program=%s declared=%d measured=%.2f using=measured", program, declared, mean)
        return max(1, int(round(mean)))
    return declared


def reserve(provider: str, program: str, calls: int, tokens_est: int = None):
    """Prepay `calls` from today's ceiling for `program`. Returns a reservation dict on success, or None
    when it would cross A53's cap — NOTHING is called, `refused` is incremented, and the programme gains
    a carry-over credit (§2.1).

    Admission uses committed = A53's spent (calls_today) + B10's reserved: the sum of all commitments
    stays within capacity, so a run never exhausts the cap halfway and two programmes never exceed it
    together. A credited programme is admitted ahead of uncredited ones (their owed calls are headroom).
    Stage 3: the reservation size uses the measured mean when it has diverged from the declaration."""
    provider = _norm(provider)
    program = program or "?"
    declared = max(0, int(calls or 0))
    if declared <= 0:
        return None
    calls = _measured_calls(program, declared)
    if tokens_est is None:
        tokens_est = calls * tokens_per_call()
    d = day()
    cap_calls, cap_tokens = caps(provider)
    spent = _spent_of(provider)
    own = _get_own(provider, d)
    cr = _credits()
    mine = cr.get(program) or {}
    credited = int(mine.get("n", 0)) > 0
    headroom = 0 if credited else sum(int((c or {}).get("calls", 0))
                                      for p, c in cr.items() if p != program and int((c or {}).get("n", 0)) > 0)
    committed = int(spent["calls_today"]) + int(own["reserved"])
    over = (cap_calls and committed + calls + headroom > cap_calls)
    over_tok = (cap_tokens and int(spent["tokens_month"]) + int(tokens_est) > cap_tokens)
    if over or over_tok:
        own["refused"] = int(own.get("refused", 0)) + 1
        _by(own, program)
        _save(_pool_key(provider, d), own)
        mine = cr.get(program) or {"n": 0, "calls": calls, "since": time.time()}
        mine["n"] = int(mine.get("n", 0)) + 1
        mine["calls"] = calls
        mine.setdefault("since", time.time())
        cr[program] = mine
        _save(_CREDITS_KEY, cr)
        # B10-c / the `refused=88 with spent=219 ≪ cap 3000` case — the refusal is logged HERE, at
        # the place that decided it, with the numbers that explain it. The reason stays a vocabulary
        # id (`llm_pool` / `budget_tokens`); WHY the pool had no room when the cap looks empty is in
        # the FIELDS: `headroom` is the calls other CREDITED programmes are owed (§2.1), which are
        # held out of this programme's admission so a repeatedly-refused show goes first next time.
        # Read `committed + need + headroom > cap` and the arithmetic is on the line.
        _throttled_log(
            provider, program,
            "[llm] pool refused program=%s provider=%s reason=%s need=%d free=%d "
            "committed=%d headroom=%d cap=%s credited=%s refused_today=%d",
            program, provider, ("budget_tokens" if (over_tok and not over) else "llm_pool"),
            calls, max(0, int(cap_calls) - committed) if cap_calls else -1,
            committed, headroom, (cap_calls or "∞"), credited, int(own["refused"]))
        return None
    own["reserved"] = int(own["reserved"]) + calls
    b = _by(own, program)
    b["reserved"] = int(b["reserved"]) + calls
    _save(_pool_key(provider, d), own)
    if credited:                                          # §2.1 — a successful admission consumes one credit
        mine["n"] = int(mine.get("n", 0)) - 1
        if mine["n"] <= 0:
            cr.pop(program, None)
        else:
            cr[program] = mine
        _save(_CREDITS_KEY, cr)
        logger.info("[llm] carry-over program=%s credits=%d", program, int(mine.get("n", 0)))
    # B10-c's `[llm] reserved` line lived here because a second caller reserved outside admission
    # and had no other trace. That caller is gone (step 2), so the one admission point logs the one
    # line — `[llm] admission reserved … free= cap=`, which carries this arithmetic. Logging it
    # twice from two layers is how a reader starts counting one reservation as two.
    return {"id": "res:" + uuid.uuid4().hex[:10], "provider": provider, "program": program,
            "day": d, "calls": calls, "declared": declared, "tokens": int(tokens_est),
            "consumed": 0, "tokens_spent": 0}


def free(provider: str, program: str = None) -> int:
    """Calls still reservable today (cap − committed). A large sentinel when the provider is uncapped."""
    provider = _norm(provider)
    cap_calls, _ = caps(provider)
    if not cap_calls:
        return 1 << 30
    committed = int(_spent_of(provider)["calls_today"]) + int(_get_own(provider, day())["reserved"])
    return max(0, cap_calls - committed)


def settle(reservation: dict, wall_s: float = 0.0) -> dict:
    """Release the reservation at the job's TERMINAL transition — DONE, FAILED or CANCELLED alike:
    return the unused calls, record the actual spend into by[program], roll the measured mean. A53's
    meter already counted the real spend on each call, so this never double-counts. Returns
    {reserved, spent, returned, tokens_spent}.

    Released ONCE per reservation. The caller settles at every terminal transition, and a job that
    never entered the run loop is settled by the path that ended it, so the same dict can reach here
    twice; a second release would subtract another job's calls from today's pool and count a run that
    never happened. The repeat is answered with zeros and `repeat: true` — no state moves.

    **ONCE PER RESERVATION ID, ON THE DURABLE RECORD — not once per dict.** The `settled` flag was
    stamped on the passed dict and nowhere else, so it answered only for the one object in one
    process's memory. A reservation read back from the vault, or copied across a hand-off, arrives
    without it and settles a second time: `by[program].spent` gains another `consumed` that no
    model call produced. That is D5 — `workload.status` reporting 240 calls charged to a workload
    on a day the provider's own meter counted 21. The spend was never spent; it was counted twice.

    So the ledger itself remembers. `settled_ids` lives on the pool record beside the tally it
    protects, which is the thing that survives the process, and the dict flag is kept as the cheap
    first answer. R5 — the bound ships with the write: the list is per provider-day (it dies with
    the day) and capped at `_SETTLED_CAP` ids, oldest dropped, because a runaway loop must not be
    able to grow one day's record without limit."""
    if not reservation:
        return {"reserved": 0, "spent": 0, "returned": 0, "tokens_spent": 0}
    provider = _norm(reservation.get("provider"))
    program = reservation.get("program") or "?"
    d = reservation.get("day") or day()
    rid = str(reservation.get("id") or "")
    own = _get_own(provider, d)
    if reservation.get("settled") or (rid and rid in (own.get("settled_ids") or ())):
        reservation["settled"] = True                 # the record knew; the dict now does too
        return {"reserved": 0, "spent": 0, "returned": 0, "tokens_spent": 0,
                "wall_s": round(float(wall_s or 0.0), 3), "repeat": True}
    reserved = int(reservation.get("calls", 0))
    consumed = int(reservation.get("consumed", 0))
    tok_spent = int(reservation.get("tokens_spent", 0))
    own["reserved"] = max(0, int(own["reserved"]) - reserved)
    b = _by(own, program)
    b["reserved"] = max(0, int(b["reserved"]) - reserved)
    b["spent"] = int(b["spent"]) + consumed
    b["tokens"] = int(b.get("tokens", 0)) + tok_spent          # B10-b — per-program token tally
    b["runs"] = int(b["runs"]) + 1
    if rid:
        ids = list(own.get("settled_ids") or ())
        ids.append(rid)
        own["settled_ids"] = ids[-_SETTLED_CAP:]      # bounded, and the day's record carries it
    _save(_pool_key(provider, d), own)
    ms = _load(_MEASURES_KEY)
    m = ms.get(program) or {"mean": 0.0, "n": 0}
    n = int(m.get("n", 0)) + 1
    m["n"] = n
    m["mean"] = float(m.get("mean", 0.0)) + (consumed - float(m.get("mean", 0.0))) / n
    ms[program] = m
    _save(_MEASURES_KEY, ms)
    reservation["settled"] = True      # stamped last: a settle that raised part-way may be re-tried
    return {"reserved": reserved, "spent": consumed, "returned": max(0, reserved - consumed),
            "tokens_spent": tok_spent, "wall_s": round(float(wall_s or 0.0), 3)}


def known_providers() -> tuple:
    """Every provider name the gate can be configured to use. The pool is keyed by provider, so a
    sweep over the pool has to know the whole set — the ACTIVE one alone leaves a reservation
    stranded on any provider the deploy has since switched away from."""
    try:
        from lib.akasha.workbench import llm_provider
        return tuple(sorted(llm_provider.DEFAULT_MODELS.keys()))
    except Exception:
        return ()


def release_reservations(provider: str, d: str = None) -> int:
    """Drop every reservation carried on this provider's pool for `d` (default: today). Returns how
    many calls were released.

    A RESERVATION BELONGS TO A RUN OF A PROCESS. It is a claim on today's ceiling held open by a job
    that is running, and it is settled at that job's terminal transition — so a process that dies
    between `reserve` and `settle` leaves the claim behind with nobody left to release it. The state
    is durable by design (R5: what a restart forgets, it overspends), and the reservation rode along
    with the spend it was stored beside, which is the half that SHOULD survive: a boot inherited
    `reserved=65` from jobs that no longer exist, and admission answered every request against a
    ceiling 65 calls lower than the real one for the rest of the day.

    Released at pool-store install, once, while no job of this process can yet hold one. The spend
    (A53's meter), the refusal count and the per-program tallies are untouched — those record what
    HAPPENED, which the restart does not undo."""
    d = d or day()
    own = _get_own(provider, d)
    n = int(own.get("reserved", 0))
    by_held = sum(int((b or {}).get("reserved", 0)) for b in (own.get("by") or {}).values())
    if not n and not by_held:
        return 0
    own["reserved"] = 0
    for b in (own.get("by") or {}).values():
        if isinstance(b, dict):
            b["reserved"] = 0
    _save(_pool_key(provider, d), own)
    return max(n, by_held)


# ── the run context the gate reads (debit the reservation only; A53 owns the spend) ─────────────────

def begin_run(reservation: dict) -> None:
    _LOCAL.res = reservation


def end_run() -> None:
    _LOCAL.res = None


def note_consumed(provider: str, chars: int) -> None:
    """B10 — the gate calls this on each SUCCESSFUL call: debit the calling thread's active reservation
    (its consumed count + estimated tokens) so settle can refund the unused. This does NOT touch the
    spend — A53's meter is the sole writer of spend."""
    res = getattr(_LOCAL, "res", None)
    if res is not None and _norm(res.get("provider")) == _norm(provider):
        res["consumed"] = int(res.get("consumed", 0)) + 1
        res["tokens_spent"] = int(res.get("tokens_spent", 0)) + max(1, int((chars or 0) / 4))


# ── read surfaces (pool atom, Health) ───────────────────────────────────────────────────────────────

_RENAMES_KEY = "renames"     # {old: new} — done one-time migrations (decision (i)b), so it runs once


def rename_program(old: str, new: str, provider: str = None) -> dict:
    """Decision (i)b — migrate a programme's accounting from `old` to `new` ONCE, carrying its CREDITS
    and its measured MEAN (and, when `provider` is given, today's by[program] tally in that provider's
    day pool). Idempotent via a durable marker (`renames`): after the first migration the rename is
    recorded and never re-applied — the gate accepts no alias to the old key afterwards. No-op when
    old==new, when already migrated, or when nothing exists under `old`."""
    old = (old or "").strip()
    new = (new or "").strip()
    if not old or not new or old == new:
        return {"renamed": False, "reason": "noop"}
    done = _load(_RENAMES_KEY)
    if done.get(old) == new:
        return {"renamed": False, "reason": "already"}
    carried = []
    # carry-over credits (provider-agnostic)
    cr = _credits()
    if old in cr:
        if new in cr:
            cr[new]["n"] = int(cr[new].get("n", 0)) + int((cr[old] or {}).get("n", 0))
            cr[new]["since"] = min(float(cr[new].get("since", time.time())),
                                   float((cr[old] or {}).get("since", time.time())))
        else:
            cr[new] = cr[old]
        cr.pop(old, None)
        _save(_CREDITS_KEY, cr)
        carried.append("credits")
    # measured mean (provider-agnostic): combine as a weighted mean when both exist
    ms = _load(_MEASURES_KEY)
    if old in ms:
        if new in ms:
            a, b = ms[new], ms[old]
            na, nb = int(a.get("n", 0)), int(b.get("n", 0))
            if na + nb > 0:
                a["mean"] = (float(a.get("mean", 0.0)) * na + float(b.get("mean", 0.0)) * nb) / (na + nb)
                a["n"] = na + nb
        else:
            ms[new] = ms[old]
        ms.pop(old, None)
        _save(_MEASURES_KEY, ms)
        carried.append("measures")
    # today's by[program] tally, when the provider is known (the day pool is per-(provider,day))
    if provider:
        d = day()
        own = _get_own(provider, d)
        by = own.get("by", {})
        if old in by:
            nb = _by(own, new)
            ob = by.pop(old)
            nb["reserved"] = int(nb.get("reserved", 0)) + int(ob.get("reserved", 0))
            nb["spent"] = int(nb.get("spent", 0)) + int(ob.get("spent", 0))
            nb["runs"] = int(nb.get("runs", 0)) + int(ob.get("runs", 0))
            _save(_pool_key(provider, d), own)
            carried.append("by")
    done[old] = new
    _save(_RENAMES_KEY, done)
    return {"renamed": True, "old": old, "new": new, "carried": carried}


def pool_view(provider: str, d: str = None) -> dict:
    """The visible counts for the guest-readable atom `llm:pool:<provider>:<day>` and Health: capacity +
    spend from A53's meter, reserved / refused / by from B10. Counts only — never keys or prompts."""
    provider = _norm(provider)
    d = d or day()
    cap_calls, cap_tokens = caps(provider)
    spent = _spent_of(provider)
    own = _get_own(provider, d)
    by = own.get("by", {})
    # B10-b — the pool's OWN aggregate, summed from the per-program tallies settle writes. A53's meter
    # (spent_calls/spent_tokens_est) counts every call on the provider; this counts only what B10
    # reserved-and-settled, and it is per-program attributable (see program_spent). The two agree when
    # every call went through a reservation; a divergence is exactly the un-reserved spend to find.
    pool_spent = sum(int((b or {}).get("spent", 0)) for b in by.values())
    # The meter counts a call BEFORE the request goes out; B10 counts one only when text came back.
    # So the meter is an upper bound on this sum, ALWAYS — and the day it is not, the pool has
    # counted spend that no call produced, which is the whole of D5 (240 attributed against 21
    # metered). One line names both numbers at the moment they disagree, so the next one is found
    # here rather than from a guide reading eleven times the truth. The inflated tally dies with
    # its own day: the record is per provider-day and tomorrow's starts empty.
    if pool_spent > int(spent["calls_today"]):
        logger.warning("[llm] pool tally EXCEEDS the meter provider=%s day=%s pool_spent=%d "
                       "metered=%d — settle counted spend no call produced (by=%s)",
                       provider, d, pool_spent, int(spent["calls_today"]),
                       ",".join("%s:%s" % (k, (v or {}).get("spent", 0)) for k, v in by.items()))
    return {"provider": provider, "day": d, "capacity_calls": cap_calls,
            "capacity_tokens_est": cap_tokens, "reserved": int(own["reserved"]),
            "spent_calls": int(spent["calls_today"]), "spent_tokens_est": int(spent["tokens_month"]),
            "pool_spent_calls": sum(int((b or {}).get("spent", 0)) for b in by.values()),
            "pool_spent_tokens": sum(int((b or {}).get("tokens", 0)) for b in by.values()),
            "refused": int(own["refused"]), "by": by}


def program_spent(program: str, provider: str, d: str = None) -> dict:
    """B10-b — one programme's spend today, from B10's own by[program] tally: {calls, tokens, runs}.
    This is the per-show `spent_today` the station guide reads (the pool meters per provider-day; this
    attributes it back to the programme). Absent programme → all zero."""
    own = _get_own(_norm(provider), d or day())
    b = (own.get("by", {}) or {}).get(program) or {}
    return {"calls": int(b.get("spent", 0)), "tokens": int(b.get("tokens", 0)),
            "runs": int(b.get("runs", 0))}


def over_allotment(provider: str, program: str) -> bool:
    """Stage 2.2 — True when this programme's committed calls (its by[program] spent + reserved) exceed
    its fair share of today's cap (cap ÷ programmes seen today). The batch cost-axis sorts an
    over-allotment programme AFTER those under it, so no single programme monopolises the pool."""
    pv = pool_view(provider)
    cap = int(pv.get("capacity_calls", 0))
    by = pv.get("by", {})
    if not cap or not by:
        return False
    share = cap / max(1, len(by))
    b = by.get(program) or {}
    return (int(b.get("spent", 0)) + int(b.get("reserved", 0))) > share


def health_segment(provider: str) -> str:
    """The Health-line ` llm(pool=… spent=…/… reserved=… refused_today=…)` segment, or "" when the
    provider has no pool activity or budget today (the empty-string-when-absent idiom)."""
    provider = _norm(provider)
    own = _load(_pool_key(provider, day()))
    spent = _spent_of(provider)
    cap_calls, _ = caps(provider)
    if not own and not spent.get("calls_today") and not cap_calls:
        return ""
    return " llm(pool=%s spent=%s/%s reserved=%s refused_today=%s)" % (
        provider, int(spent.get("calls_today", 0)), cap_calls or "∞",
        int((own or {}).get("reserved", 0)), int((own or {}).get("refused", 0)))
