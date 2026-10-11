#!/usr/bin/env python3
"""
`runs_per_day` is the EFFECT allowance — an empty or failed run does not spend it (step 0 §4, item 3).

The driver used to increment `runs_today` the moment the workflow list finished, before it knew what
the run had produced. So a run that completed but said NOTHING — every turn standing by because the
model provider refused — spent one of the day's allowance anyway. With a small cap (4/day is the
default) a provider outage in the morning spends the whole day on runs that produced nothing, and
the cap then refuses the one run that could have produced something. The workload goes quiet for a
day *because it failed*, which is exactly backwards.

The allowance is now charged once the outcome is known, at one site, and only for a run that
produced the workload's declared effect:

    publishing workload  → an airing          (aired=0 → no charge)
    recording workload   → a completed run    (it publishes nothing; there is no airing to count)
    failed run           → never charged      (the charge is on the success path only)

And the boot-owed airing stays owed: a boot run that aired nothing re-arms `boot_pending` with a
bounded backoff rather than counting itself done.

Not charging the empty run cannot run away. The attempt rate is bounded by the declared cadence, a
failure's retries by `on_failure.retries`, a boot-owed airing by `BOOT_AIRING_TRIES`, and the day's
model SPEND by the LLM pool — which is the authority for spend; `runs_per_day` never was.

Run:  python test/workload_allowance_eval.py     (exit 0 = all pass)
"""
import ast
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT); sys.path.insert(0, ROOT)

from lib.akasha.workbench import autorun, wl_state, provision                     # noqa: E402
from lib.akasha.workbench import workload as W                         # noqa: E402

_fails = []
DRIVER = "lib/akasha/workbench/autorun.py"


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


PUBLISHES = {"effect": W.EFFECT_PUBLISH}
RECORDS = {"effect": W.EFFECT_RECORD}


def _spend(pol, outcomes, cap=4):
    """Replay the driver's charge rule over a sequence of run outcomes; return the day's count."""
    state = {"runs_today": 0}
    for aired in outcomes:
        if int(state["runs_today"]) >= cap:
            continue                                   # the cap blocks the attempt, as the driver does
        if autorun.run_charges_allowance(pol, aired):
            state["runs_today"] += 1
    return state["runs_today"]


def _unpaced(src, node):
    """Leaf branches of the empty-run ladder that set no `retry_at` — each one is a workload the
    trigger would attempt again on the very next tick."""
    bad = []
    def walk(n, path):
        if isinstance(n, ast.If):
            walk_body(n.body, path + [n.lineno]); walk_body(n.orelse or [], path + [n.lineno])
            return
        return
    def walk_body(body, path):
        ifs = [x for x in body if isinstance(x, ast.If)]
        if ifs:
            for x in ifs:
                walk(x, path)
            return
        if not body:
            bad.append(path); return
        seg = "\n".join(ast.get_source_segment(src, x) or "" for x in body)
        if 'state["retry_at"]' not in seg:
            bad.append(body[0].lineno)
    walk(node, [])
    return bad


def main():
    print("=" * 78)
    print("runs_per_day is spent by the effect, not by the attempt")
    print("=" * 78)

    # ── the rule itself ──────────────────────────────────────────────────────────────────────────
    check("a publishing run that aired nothing leaves the count unchanged",
          autorun.run_charges_allowance(PUBLISHES, 0) is False)
    check("a publishing run that aired spends one",
          autorun.run_charges_allowance(PUBLISHES, 1) is True)
    check("several airings in one run still spend ONE (the run is the unit)",
          _spend(PUBLISHES, [3]) == 1)
    check("a recording run spends one on completion — it has no airing to count",
          autorun.run_charges_allowance(RECORDS, 0) is True)

    # ── the day the provider was down ────────────────────────────────────────────────────────────
    quiet = _spend(PUBLISHES, [0] * 20)
    check("a whole day of runs that produced nothing spends none of the allowance",
          quiet == 0, "runs_today=%d after 20 empty runs" % quiet)
    after = _spend(PUBLISHES, [0] * 20 + [1])
    check("…and the run that finally airs is not refused by a cap the outage filled",
          after == 1, "runs_today=%d" % after)
    check("a workload that airs every time still stops at its cap",
          _spend(PUBLISHES, [1] * 10, cap=4) == 4)

    # ── exactly one site moves the counter, and it is guarded ────────────────────────────────────
    src = open(DRIVER, encoding="utf-8").read()
    tree = ast.parse(src)
    def _pairs(n):
        """(target, assigned-value) for every write in one statement, tuple assignments unpacked."""
        if isinstance(n, ast.AugAssign):
            return [(n.target, n.value)]
        if not isinstance(n, ast.Assign):
            return []
        out = []
        for t in n.targets:
            if isinstance(t, ast.Tuple) and isinstance(n.value, ast.Tuple) \
                    and len(t.elts) == len(n.value.elts):
                out.extend(zip(t.elts, n.value.elts))
            else:
                out.append((t, n.value))
        return out

    sites = []
    for n in ast.walk(tree):
        for tgt, val in _pairs(n):
            if (isinstance(tgt, ast.Subscript) and isinstance(tgt.slice, ast.Constant)
                    and tgt.slice.value == "runs_today"):
                # The UTC-day rollover assigns a bare 0; that is a reset, not a charge.
                if not (isinstance(val, ast.Constant) and val.value == 0):
                    sites.append(n.lineno)
    check("the driver has exactly one site that charges the allowance "
          "(the UTC-day reset to 0 aside)", len(sites) == 1, "lines %s" % sites)
    if len(sites) == 1:
        # …and the statement guarding it is the charge rule, not an unconditional increment.
        guard = [ln for ln in src.splitlines()[max(0, sites[0] - 4):sites[0] - 1]
                 if ln.lstrip().startswith("if ") and "run_charges_allowance(" in ln]
        check("…and it is guarded by the declared charge rule", bool(guard),
              (guard[0].strip() if guard else "no `if run_charges_allowance(…)` above line %d"
               % sites[0]))

    # ── the failure path never reaches the charge ────────────────────────────────────────────────
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "bench_autorun_tick")
    charge_line = sites[0] if sites else -1
    in_failure = []
    for n in ast.walk(fn):
        if isinstance(n, ast.If) and n.orelse and n.lineno < charge_line:
            lo = n.orelse[0].lineno
            hi = max(getattr(x, "end_lineno", x.lineno) for x in n.orelse)
            if lo <= charge_line <= hi:
                in_failure.append(n.lineno)
    check("the charge is on the success path, never in the else that handles a failed run",
          not in_failure, "reached from the else at line(s) %s" % in_failure)

    # ── and the cap's own reporting: once per society per window, per kind ───────────────────────
    # The window is the one the line names — `next=00:00Z`, the UTC day the budget resets on. The
    # retry line used to fire on every tick, so one blocked retry wrote a WARNING a minute for the
    # rest of the day.
    import logging

    class _Cap(logging.Handler):
        def __init__(self):
            super().__init__()
            self.lines = []

        def emit(self, rec):
            self.lines.append(rec.getMessage())

    class _K:
        pass

    cap_h = _Cap()
    lg = logging.getLogger(autorun.logger.name)
    lg.addHandler(cap_h)
    lg.setLevel(logging.INFO)
    k = _K()
    for _ in range(120):                                   # two hours of one-a-minute ticks
        autorun.autorun_budget_log(k, "g", "one", 4, 4, "2026-09-21", is_retry=True)
        autorun.autorun_budget_log(k, "g", "one", 4, 4, "2026-09-21", is_retry=False)
    deferred = [ln for ln in cap_h.lines if "retry deferred" in ln]
    exhausted = [ln for ln in cap_h.lines if "budget exhausted" in ln]
    check("a blocked retry logs once per society per window, not once per tick",
          len(deferred) == 1, "%d lines in 120 ticks" % len(deferred))
    check("…and the cap-reached line is throttled separately, so both are still said once",
          len(exhausted) == 1, "%d lines" % len(exhausted))
    check("…and the deferral line carries the numbers that explain it",
          bool(deferred) and "runs_today=4/4" in deferred[0] and "next=00:00Z" in deferred[0],
          deferred[0] if deferred else "")
    autorun.autorun_budget_log(k, "g", "two", 4, 4, "2026-09-21", is_retry=True)
    autorun.autorun_budget_log(k, "g", "one", 4, 4, "2026-09-22", is_retry=True)
    deferred = [ln for ln in cap_h.lines if "retry deferred" in ln]
    check("…while another society, and the next window, each say it again",
          len(deferred) == 3, "%d lines" % len(deferred))
    lg.removeHandler(cap_h)

    # ── the boot-owed airing survives an empty run ───────────────────────────────────────────────
    check("a bounded number of boot retries is declared, so 'still owed' cannot loop",
          isinstance(wl_state.BOOT_AIRING_TRIES, int) and 1 <= wl_state.BOOT_AIRING_TRIES <= 24,
          "BOOT_AIRING_TRIES=%s" % wl_state.BOOT_AIRING_TRIES)
    check("the driver re-arms the boot obligation when a boot run aired nothing",
          'state["boot_pending"] = True' in src and "boot_tries" in src)

    # ── §3 the clock the window reads is the EFFECT clock ────────────────────────────────────────
    # `last_run` was stamped the moment the workflow list finished, before the outcome was known.
    # For a `daily:` workload that meant one empty boot run satisfied the day's window, so the
    # failure bought a whole day of silence — the same inversion the allowance had, in the clock.
    # Two clocks now: `last_attempt` paces the trigger (an empty run must not turn a 60-second tick
    # into a 60-second run loop), `last_run` records the effect and is the only one a window reads.
    lr_sites = []
    for n in ast.walk(tree):
        for tgt, val in _pairs(n):
            if (isinstance(tgt, ast.Subscript) and isinstance(tgt.slice, ast.Constant)
                    and tgt.slice.value == "last_run"):
                lr_sites.append(n.lineno)
    check("the driver has exactly one site that moves the effect clock", len(lr_sites) == 1,
          "lines %s" % lr_sites)
    check("…and it is the charge site itself, so the clock and the allowance cannot disagree",
          bool(lr_sites) and bool(sites) and abs(lr_sites[0] - sites[0]) <= 1,
          "last_run@%s charge@%s" % (lr_sites, sites))

    DAY = 86400.0
    noon = (time.time() // DAY) * DAY + 12 * 3600      # 12:00 UTC today, on the day's grid
    daily = {"trigger": "daily:09:00"}
    # 10:00: the run happened and aired nothing, so the clock the window reads never moved and the
    # day is still owed. Under the old single clock this state read as "today is served", and the
    # programme's next chance was tomorrow — a whole day of silence bought by the failure itself.
    empty = {"last_run": 0.0}
    check("an empty run leaves `last_run` unchanged, so the day's window is still owed",
          autorun.autorun_due(daily, dict(empty), noon) is True)
    check("…and once the run produced its effect the window is satisfied for the day",
          autorun.autorun_due(daily, {"last_run": noon - 2 * 3600}, noon) is False)
    check("…and tomorrow it is owed again",
          autorun.autorun_due(daily, {"last_run": noon - 2 * 3600}, noon + DAY) is True)
    # What keeps that open window from being attempted on every tick is the retry the empty run
    # armed: it is the workload's schedule while it is set — it brings the next attempt forward
    # AND holds it back. Read only as "fire early", it said both "wait until 10:02" and "run on
    # any tick the window is open", and the second is the run-every-minute loop.
    check("an armed retry holds the open window closed until it is due",
          autorun.autorun_due(daily, {"last_run": 0.0, "retry_at": noon + 600}, noon) is False)
    check("…and when it comes due it fires, whatever the trigger says",
          autorun.autorun_due({"trigger": "manual"}, {"retry_at": noon - 1}, noon) is True)
    every10 = {"trigger": "interval:600"}
    check("an `interval:` workload measures its gap from the last run that produced something",
          autorun.autorun_due(every10, {"last_run": noon - 60}, noon) is False)
    check("…and the interval opens again on its own gap",
          autorun.autorun_due(every10, {"last_run": noon - 900}, noon) is True)

    # ── §3 a retry is for what a retry can fix ───────────────────────────────────────────────────
    for r in wl_state.TRANSIENT_REASONS:
        check("`%s` is transient — the pool refills, the back-off expires, the model answers"
              % wl_state.reason_id(r), wl_state.is_transient(r))
    for r in (wl_state.REASON_RUNS_PER_DAY, wl_state.REASON_WAITING_SOURCE,
              wl_state.REASON_BREAKER, wl_state.REASON_NOT_PROVISIONED,
              wl_state.REASON_PROVIDER_ABSENT, wl_state.REASON_NOT_DECLARED):
        check("`%s` is not — no retry creates a grant, a workflow or a corpus"
              % wl_state.reason_id(r), not wl_state.is_transient(r))
    check("a reason id the platform has never heard of waits for provisioning rather than spinning",
          not wl_state.is_transient("station:reason:something_an_application_invented"))
    check("…and the stored spelling resolves to the same answer as the bare id — a reason read "
          "back out of the guide is still the reason that was written",
          wl_state.is_transient(wl_state.reason_id(wl_state.REASON_LLM_POOL)))

    # The branch itself: the retry ladder is reached only when the reason is transient, and the
    # refusal says so in the vocabulary at the place that decided it (doctrine rule 3).
    arm = [n for n in ast.walk(fn)
           if isinstance(n, ast.If) and isinstance(n.test, ast.UnaryOp)
           and isinstance(n.test.op, ast.Not) and "is_transient" in ast.dump(n.test)]
    check("transience guards one branch, and the growing boot backoff is on the other side of it",
          len(arm) == 1
          and "boot_tries" not in ast.get_source_segment(src, arm[0].body[-1])
          and any("BOOT_AIRING_TRIES" in ast.get_source_segment(src, x) for x in arm[0].orelse))
    check("…and every branch of the empty run leaves a next attempt, so none is left unpaced",
          len(arm) == 1 and not _unpaced(src, arm[0]), "%s" % (_unpaced(src, arm[0]) if arm else ""))
    check("…and the non-transient run says once, by id, that it is waiting for provisioning",
          "[bench.auto] not retried society=%s/%s reason=%s" in src
          and "(waits for provisioning)" in src)

    # ── §3 the guide's next_update_at is the trigger's window, not a cadence it never had ─────────
    check("`interval:` measures from the last run that PRODUCED something",
          wl_state.next_window({"trigger": "interval:600"}, noon, noon - 60) == noon + 540)
    check("…and with nothing produced yet it is one gap from now (never a moment in the past)",
          wl_state.next_window({"trigger": "interval:600"}, noon, 0.0) == noon + 600)
    check("`daily:` is the next occurrence of its UTC minute — today's if it is still ahead",
          wl_state.next_window(daily, noon - 4 * 3600, 0.0) == noon - 3 * 3600)
    check("…and tomorrow's once it has passed",
          wl_state.next_window(daily, noon, 0.0) == noon - 3 * 3600 + DAY)
    check("a trigger with no window (boot, manual) claims none",
          wl_state.next_window({"trigger": "manual"}, noon, 0.0) == 0.0)
    nothing = [ln for ln in src.splitlines() if "next_at=_next" in ln]
    check("the driver hands that moment to the row, and only on the run that aired nothing",
          len(nothing) == 1, "%d call(s)" % len(nothing))

    # ── §3 and the two rules together do not open a loop ─────────────────────────────────────────
    # The rules interact, and the interaction is the part a structural check cannot see: once an
    # empty run stops closing the day's window, and a non-transient reason is denied its retry, a
    # `daily:` workload that aired nothing would be attempted on EVERY 60-second tick for the rest
    # of the day — 1,440 runs where the declaration asked for one. What prevents it is that every
    # branch leaves a `retry_at`, so the simulation below is the check that matters: 48 hours of
    # one-a-minute ticks, replaying what the ladder writes back, counting the attempts.
    day0 = (noon // DAY) * DAY

    def _sim(pol_, aired, reason, boot=True, last_run=None):
        """48 h of one-a-minute ticks through the REAL `autorun_due`, replaying what the REAL
        run-end ladder writes back for one outcome. Returns the attempts.

        `last_run` seeds the EFFECT clock — the state a live cell is actually in. Leaving it at 0
        (this simulation's only shape until D1) hides the whole defect: with no prior effect,
        `next_attempt` answers `now + interval`, which is in the future by construction, so every
        branch looked paced. The loop needs a run that ONCE produced something and has produced
        nothing since — then `last_run + interval` is a moment in the PAST, `retry_at <= now`
        reads as due, and the workload is attempted on every tick."""
        st, fired, t = {"boot_pending": bool(boot)}, [], day0
        if last_run is not None:
            st["last_run"] = float(last_run)
        while t < day0 + 2 * DAY:
            if autorun.autorun_due(pol_, st, t):
                fired.append(t)
                st["boot_pending"] = False
                # ── the driver's ok branch, in its own order ──
                st["breaker"] = 0
                st.pop("retry_at", None)
                st.pop("retry_count", None)
                if autorun.run_charges_allowance(pol_, aired):
                    st["runs_today"] = int(st.get("runs_today", 0)) + 1
                    st["last_run"] = t
                if aired:
                    st.pop("boot_tries", None)
                    st["retry_at"] = wl_state.next_attempt(
                        pol_, t, float(st.get("last_run") or t))
                else:
                    st["retry_at"] = wl_state.next_attempt(
                        pol_, t, float(st.get("last_run") or 0.0))
            t += 60.0
        return fired

    # THE SHAPES A DECLARATION ACTUALLY PROJECTS. The first version of this simulation used bare
    # `{"trigger": "interval:3600"}` policies — a shape `workload.policy` never writes. Every
    # declaration projects `trigger: boot|manual` with the cadence under `then:`, so the two
    # policies that were simulated were the two nobody runs, and the branch that loops was
    # covered by neither (D1).
    # The counts include the BOOT attempt where the shape declares one (`trigger: boot`), because a
    # deploy firing its workloads once is the rule, not a loop: `boot+daily` is the boot at 00:00
    # plus its 09:00 slot on each of the two days. A bare `daily:`/`interval:` policy declares no
    # boot trigger and gets only its slots.
    SHAPES = (("boot+daily:09:00", {"trigger": "boot", "then": "daily:09:00"}, 3),
              ("boot+interval:3600", {"trigger": "boot", "then": "interval:3600"}, 48),
              ("boot+interval:14400", {"trigger": "boot", "then": "interval:14400"}, 12),
              ("bare daily:09:00", {"trigger": "daily:09:00", "then": "daily:09:00"}, 2),
              ("bare interval:3600", {"trigger": "interval:3600", "then": "interval:3600"}, 48))
    # …AND EVERY OUTCOME, not only the empty one. `ok + no effect + no reason` is the branch the
    # live cell looped on; `ok + aired` is the one that wrote no `retry_at` back at all and left
    # the pacing to a fall-through on a clock an empty run cannot move.
    OUTCOMES = (("empty, no reason", 0, ""),
                ("empty, transient reason", 0, wl_state.REASON_LLM_POOL),
                ("AIRED (effect produced)", 1, ""))
    for label, pol_, want in SHAPES:
        _p = dict(pol_, effect=W.EFFECT_PUBLISH, room=True, budget={"runs_per_day": 10 ** 6})
        for oname, aired, reason in OUTCOMES:
            fired = _sim(_p, aired, reason)
            check("a `%s` workload whose run ends `%s` is attempted on its own cadence for 48h, "
                  "not on every tick" % (label, oname), len(fired) == want,
                  "%d attempts (expected %d; a tick loop would be 2880)" % (len(fired), want))

    # A policy with NO cadence at all claims no moment, and is not attempted again in this
    # process: `next_attempt` returns 0 and `autorun_due` answers False. 0 means "no moment ever
    # for this trigger", which is a different statement from "no moment yet" — and conflating the
    # two is what let a falsy `retry_at` reopen the fall-through.
    _none = {"trigger": "boot", "then": "none", "effect": W.EFFECT_RECORD}
    check("a boot-only workload claims no next moment, and is attempted once per boot and no more",
          wl_state.next_attempt(_none, noon, 0.0) == 0.0 and len(_sim(_none, 0, "")) == 1,
          "%s attempt(s)" % len(_sim(_none, 0, "")))
    check("…and `next_attempt` NEVER answers 0 for a policy that declares a cadence — that zero "
          "is what `autorun_due` reads as 'no retry armed'",
          all(wl_state.next_attempt(dict(p_), noon, 0.0) > 0 for _l, p_, _w in SHAPES),
          str([wl_state.next_attempt(dict(p_), noon, 0.0) for _l, p_, _w in SHAPES]))

    # ── D1 PROPER — a STALE effect clock, which is the state the live cell looped in ──────────────
    # `last_run + cadence` is the next slot measured from the EFFECT clock, and a run that produces
    # nothing never advances that clock. Once the gap since the last effect exceeds one cadence,
    # that sum is a moment in the PAST — the driver wrote it into `retry_at`, `retry_at <= now`
    # read as due, and a four-hourly declaration was attempted on every 60-second tick (87 runs in
    # 90 minutes). Every case above seeded `last_run = 0`, where the answer is `now + interval` and
    # in the future no matter what — which is exactly why 15 green checks sat above a live loop.
    # The count is asserted as the PACE, not as a fixed number: a stale effect clock puts the
    # cadence on its own phase, so a 48-hour window legitimately holds one more or one fewer slot
    # depending on where that phase falls. What must hold is the gap — consecutive attempts are a
    # declared cadence apart, never a tick. (The first gap is exempt: a boot trigger fires on
    # deploy and its first scheduled slot follows whenever the cadence says, which is the rule.)
    STALE_AGES = (("one cadence + a minute", 0), ("half a day", 43200), ("three days", 259200))
    for label, pol_, want in SHAPES:
        _p = dict(pol_, effect=W.EFFECT_PUBLISH, room=True, budget={"runs_per_day": 10 ** 6})
        cad = float(wl_state.interval_of(_p) or 3600.0)
        for aname, age in STALE_AGES:
            fired = _sim(_p, 0, "", last_run=day0 - (age or cad + 60.0))
            gaps = [b - a for a, b in zip(fired, fired[1:])][1:]
            check("a `%s` workload with its last effect %s ago, producing nothing, is STILL "
                  "attempted a cadence apart — never on every tick" % (label, aname),
                  len(fired) <= want + 1 and all(g >= cad - 60 for g in gaps),
                  "%d attempts (≈%d), smallest gap %s s vs cadence %d (the D1 loop is 2880 "
                  "attempts, 60 s apart)"
                  % (len(fired), want, int(min(gaps)) if gaps else "n/a", int(cad)))

    # The property under all of it, stated once: a next attempt is either "no moment ever" (0) or a
    # moment in the FUTURE. There is no third answer, and a past moment is not a schedule — it is
    # the absence of one wearing a number.
    _stales = [0.0, noon - 1, noon - 86400 * 7, noon - 0.5]
    _bad = [(p_["then"], s, wl_state.next_attempt(dict(p_), noon, s))
            for _l, p_, _w in SHAPES for s in _stales
            if 0 < wl_state.next_attempt(dict(p_), noon, s) <= noon]
    check("`next_attempt` answers 0 or a moment strictly in the FUTURE — never a past one, for "
          "any declared shape at any age of the effect clock", not _bad, str(_bad[:3]))

    # And the guide asks the SAME function the driver writes back, so it can never promise an
    # update at a moment the driver has no intention of trying.
    _st_src = open(os.path.join(ROOT, "lib/akasha/workbench/wl_state.py"), encoding="utf-8").read()
    check("`status()` reports `next_at` from `next_attempt` — one question, one answer",
          "\"next_at\": next_attempt(" in _st_src and "\"next_at\": next_window(" not in _st_src)

    # ── ONE SOCIETY, ONE SCHEDULE — the collision that produces the same symptom ─────────────────
    # A society carries one autorun record. Two declarations naming it share a `retry_at` that each
    # tick overwrites, so both are due on every tick while both files say hours. It has happened
    # once (`news_show_x` on the news show's society) and nothing noticed. Two checks: the
    # declarations on disk do not collide, and provisioning SAYS SO when they do.
    print("\n  ── one society, one schedule ──")
    _seen = {}
    for _x in (W.declarations(None) or []):
        if not W.problems(_x):
            _seen.setdefault("%s/%s" % W.society_of(_x), []).append(W.key(_x))
    _clash = {k_: v for k_, v in _seen.items() if len(v) > 1}
    check("no two declarations on disk name the same society", not _clash, str(_clash))

    import logging as _lg

    class _Cap(_lg.Handler):
        def __init__(self):
            _lg.Handler.__init__(self); self.lines = []

        def emit(self, rec):
            try:
                self.lines.append(rec.getMessage())
            except Exception:
                pass

    _cap = _Cap()
    _log = _lg.getLogger("Akasha.Kernel")
    _log.addHandler(_cap)
    _real_decls = W.declarations
    try:
        # two fixture declarations sharing one society — the collision, made on purpose
        _a = {"bench": "wb:fx", "workflow": "fx_a", "society": "fxg/fxs", "trigger": {"boot": True},
              "duty": "wb:duty:best_effort", "effect": "record",
              "appetite": {"llm_calls_per_run": 1, "weight": 1},
              "budget": {"per_day": 1, "max_wall_s": 60, "max_steps": 5}, "pins": {},
              "space": {"client": "fx_client"}, "_file": "fx_a.json"}
        _b = dict(_a, workflow="fx_b", _file="fx_b.json")
        W.declarations = lambda _k=None: [_a, _b]
        provision.provision_workloads(None)
    except Exception:
        pass                                          # provisioning a None kernel stops early —
    finally:                                          # the conflict line is emitted before that
        W.declarations = _real_decls
        _log.removeHandler(_cap)
    check("provisioning REPORTS two workloads that share one society, naming both and the society",
          any("provision CONFLICT" in l and _a["society"] in l
              and "fx/fx_b" in l for l in _cap.lines),
          str([l for l in _cap.lines if "CONFLICT" in l])[:150])

    print()
    if _fails:
        print("RESULT: FAIL — %d check(s) failed:" % len(_fails))
        for f in _fails:
            print("   - " + f)
        sys.exit(1)
    print("RESULT: PASS — the allowance is charged at one guarded site, for the declared effect "
          "only; an empty or failed run leaves the count unchanged and the boot airing stays owed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
