"""
The auto-execution driver (the bench.auto tick, the readiness gate, the sweep pick, the breaker) and the leaderboard hydrate regenerator — moved out of the kernel (backend layout order 2026-09-20).

Every function takes the kernel (the heart) as its first argument: it is the object the
dispatcher / timer registry hands in, never imported. Bodies are the kernel's own, moved
verbatim except `self.` → `kernel.` and intra-family calls.
"""
import os
import re
import sys
import time
import json
import uuid
import logging

from lib.akasha.api import authority as _authority
import hashlib
import functools
from typing import Dict, Any, Optional, List, Callable
from lib.akasha.identity import Role, Capability
from lib.akasha.api.trust import (TRUST_NETWORK, TRUST_LOCAL, TRUST_INTERNAL,
                                  TRUSTED_TRANSPORTS as _TRUSTED_TRANSPORTS)
from lib.akasha.api import facts as _facts
from lib.akasha.api.heart import _rss_mb, _search_partial_incr, _SEARCH_PARTIAL, _MAINT_LOCK, _MAINT_LAST_DONE, _MAINT_GAP_S, _MAINT_GATE_AVAIL_MB, _MAINT_GATE_MAX_WAIT_S, _MAINT_GATE_RETRY_S, _maint_gate_ok, _run_gated_maint, _with_rss_delta, _mem_available_mb, _smaps_rollup, _thread_count, _open_fd_count, _fd_soft_limit, _autolearn_disabled_reason
from lib.akasha.source import bootstrap as _src_bootstrap, fetch as _src_fetch   # transitional (S3→S4/S5)
from lib.akasha.jcl import workflow_vocab as _wf
from lib.akasha.workbench import wl_state
from lib.akasha.workbench import workload as _W

logger = logging.getLogger("Akasha.Kernel")


# ── the driver's skip vocabulary ────────────────────────────────────────────────────────────────
# Every place the driver swallows an exception and carries on says WHICH place, as an id, at
# WARNING. These were `logger.debug(… skipped: %s)` — invisible at the default level, so a driver
# that had silently stopped doing something looked exactly like a driver with nothing to do, and
# the live checkpoint could not tell the two apart. The exception text rides in `detail=`; the id
# is what a log search and an eval compare against, and it never changes wording.
#
# Not throttled, deliberately, unlike the budget's cap lines: a cap reached is a NORMAL state that
# recurs by design, while each of these is an exception on a path that is supposed to work. One a
# tick for a genuinely broken society is the signal, not noise.
SKIP_TRIPPED_DERIVE = "tripped_derive"              # the breaker set could not be read
SKIP_METRICS_READ = "metrics_read"                  # a bench's last training summary could not be read
SKIP_TICK_SESSION = "tick_session"                  # no admin session / concept — the WHOLE tick is lost
SKIP_SWEEP_PICK = "sweep_pick"                      # the post-run branch pick failed
SKIP_SOCIETY_TICK = "society_tick"                  # one society's turn raised; the others continue
SKIP_DRIVER_TICK = "driver_tick"                    # the driver loop's own turn raised
SKIP_LEADERBOARD_ENUMERATE = "leaderboard_enumerate"  # hydrate could not enumerate the sweep index
SKIP_LEADERBOARD_REBUILD = "leaderboard_rebuild"    # hydrate could not rebuild one leaderboard
SKIP_REASONS = (SKIP_TRIPPED_DERIVE, SKIP_METRICS_READ, SKIP_TICK_SESSION, SKIP_SWEEP_PICK,
                SKIP_SOCIETY_TICK, SKIP_DRIVER_TICK, SKIP_LEADERBOARD_ENUMERATE,
                SKIP_LEADERBOARD_REBUILD)


def autorun_due(policy: dict, state: dict, now: float, boot_id: str = "") -> bool:
    """Evaluate a policy trigger against the last-run record. 'manual' never fires here (only
    society.run does); 'boot' fires once PER WRITER BOOT (A33); 'interval:<s>' / 'daily:HH:MM' fire
    on the clock. NOTE: 'daily:HH:MM' is evaluated in UTC (A32) — 'daily:03:00' = 03:00 UTC (12:00 JST)."""
    if state.get("run_once_done"):
        return False
    # A28(c) — a pending retry (armed after a run that failed or produced nothing) IS the schedule
    # until it fires: it answers "when will this next try?", so it both brings the next attempt
    # forward and holds it back. Read only as "fire early", an armed retry said two things at once
    # — wait until 10:02, and also run on any tick the window happens to be open — and the second
    # is what turned a run that produced nothing into a run every sixty seconds (order §3).
    retry_at = float(state.get("retry_at") or 0.0)
    if retry_at:
        return now >= retry_at
    trig = str(policy.get("trigger") or "manual")
    # `last_run` is the EFFECT clock: when this workload last PRODUCED what it declares (an airing,
    # a completed recording run). It was stamped the moment the workflow list finished, before the
    # outcome was known, so one empty boot run satisfied today's `daily:` window and bought a whole
    # day of silence for a failure nobody had yet diagnosed. It is now stamped with the charge, at
    # one site, and the window below reads it — so the day stays owed until the day is served.
    last = float(state.get("last_run") or 0.0)
    if trig == "manual":
        return False
    if trig == "boot":
        # A44 — "boot" is due while `boot_pending` is set. The reset (once per writer boot) is the
        # ONLY thing that sets it; the run clears it before the first block. This replaces the
        # `boot_id != boot_id` test (which, paired with a popped boot_id, looped every tick). After
        # the boot run clears the gate, the trigger CONTINUES as `then:` (daily/interval/none).
        if state.get("boot_pending"):
            return True
        then = str(policy.get("then") or "none")
        if then in ("none", "", "manual"):
            return False
        trig = then          # fall through to the interval/daily evaluation below
    if trig.startswith("interval:"):
        try:
            secs = float(trig.split(":", 1)[1])
        except (ValueError, IndexError):
            return False
        return (now - last) >= max(0.0, secs)
    if trig.startswith("daily:"):
        hhmm = trig.split(":", 1)[1]
        try:
            hh, mm = [int(x) for x in hhmm.split(":")]
        except (ValueError, IndexError):
            return False
        # The day is `now`'s day, not the wall clock's. This read `time.time()` twice while the
        # function was handed a `now` — harmless on the live tick, where they are the same second,
        # but it meant the window could not be evaluated for any moment except this one, so the
        # rule the whole ladder rests on had no test that could fail.
        target = now - (now % 86400) + hh * 3600 + mm * 60
        # fire once per UTC day after the target minute, if the day's EFFECT has not happened.
        # Attempts within the day are paced by `retry_at` above, not by this window.
        return now >= target and last < target
    return False


def model_ready(kernel, name: str) -> bool:
    """A `requires` entry `model:<name>` is satisfied when the bundled model file exists AND its
    sha256 matches assets/models/model.json (vision-deps-bundle §3.2). A model whose binary is
    absent/corrupt keeps the bench waiting, exactly like an unfrozen pool."""
    want = name.split(":", 1)[1] if ":" in name else name
    try:
        import hashlib as _hl
        proj = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        mdir = os.path.join(proj, "assets", "models")
        mani = json.load(open(os.path.join(mdir, "model.json"), encoding="utf-8"))
        # C(§2.1) — the manifest lists MANY models under `models[]`; find the one named. The old
        # single-object shape (top-level name/file/sha256) is still honoured as a fallback.
        entry = next((m for m in (mani.get("models") or []) if str(m.get("name")) == want), None)
        if entry is None and str(mani.get("name")) == want:
            entry = mani
        if not entry:
            return False
        fp = os.path.join(mdir, entry.get("file") or "")
        if not os.path.isfile(fp):
            return False
        h = _hl.sha256()
        with open(fp, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest() == str(entry.get("sha256") or "")
    except Exception:
        return False


def requires_missing(kernel, requires, wl_key: str = "") -> list:
    """The declared `requires` entries NOT yet ready — the readiness gate's 'missing' list (§2.3).
    A `source:pool:…` entry must be present-and-frozen; a `model:<name>` entry (§3.2) must have its
    bundled binary present with a matching sha256. Empty ⇒ the bench may run.

    THE DECISION IS THE GATE'S FACT; the pools are only how it is NAMED. `set:source:ready` holds
    WORKLOAD KEYS, because that is what the gate's step 4 asks for (`target ∈ … source_ready`), and
    the workbench states one per declaration from the pools it requires
    (`provision.workload_source_ready`). So the driver reads exactly the fact the gate reads — one
    answer to one question — and then lists the individual pools that are not frozen so the
    `waiting` line and the room can say WHICH one is missing. Naming a thing is not deciding it.

    A missing `wl_key` (a hand-armed society with no declaration) has no fact to read, so the pools
    answer for themselves as before — it is not a workload and the gate is not asked about it.

    A non-`model:` entry is named unready by `provision.requirement_ready`, the SAME predicate the
    fact is written from, so the list can never disagree with the decision it explains. It used to
    ask `pool_frozen` directly, which named every `set:` requirement as missing forever (D7)."""
    from lib.akasha.workbench import provision as _prov
    out = []
    for r in (requires or []):
        if str(r).startswith("model:"):
            if not model_ready(kernel, r):
                out.append(r)
    if not str(wl_key or "") or not _facts.has(kernel, _facts.SOURCE_READY, str(wl_key)):
        for r in (requires or []):
            if not str(r).startswith("model:") and not _prov.requirement_ready(kernel, str(r)):
                out.append(r)
    return out


def autorun_waiting_log(kernel, gid: str, name: str, missing: list) -> None:
    """Throttled-hourly `[bench.auto] waiting: society=… missing=[…]` (§2.3) — waiting is visible
    but never floods the log. Bounded table (R7)."""
    try:
        now = time.time()
        key = (gid, name)
        tbl = getattr(kernel, "_autorun_wait_log", None)
        if tbl is None:
            tbl = kernel._autorun_wait_log = {}
        if now - tbl.get(key, 0.0) >= 3600.0:
            tbl[key] = now
            if len(tbl) > 256:
                for _k in sorted(tbl, key=tbl.get)[:64]:
                    tbl.pop(_k, None)
            logger.info("[bench.auto] waiting: society=%s/%s missing=%s", gid, name, missing)
    except Exception:
        pass


def autorun_budget_log(kernel, gid: str, name: str, runs_today: int, cap: int, day: str,
                        is_retry: bool) -> None:
    """A45(1) — the daily cap is no longer silent. A budget-blocked RETRY is a WARNING; the normal
    cap-reached is one INFO per society per UTC day.

    BOTH are throttled per society per WINDOW, and the window is the one the line itself names:
    `next=00:00Z`, the UTC day the budget resets on. The retry line was not — it fired on every
    tick, so one blocked retry wrote a WARNING a minute for the rest of the day, and a log that
    repeats a decision once a minute is a log nobody reads at the moment something else goes wrong.
    The two kinds are throttled SEPARATELY (the key carries the kind), so a society that hits the
    cap and then defers a retry still says both things once."""
    try:
        tbl = getattr(kernel, "_autorun_budget_log_seen", None)
        if tbl is None:
            tbl = kernel._autorun_budget_log_seen = {}
        key = (gid, name, day, "retry" if is_retry else "cap")
        if key in tbl:
            return
        if len(tbl) > 256:
            tbl.clear()
        tbl[key] = True
        if is_retry:
            logger.warning("[bench.auto] retry deferred by budget society=%s/%s "
                           "runs_today=%d/%d next=00:00Z", gid, name, runs_today, cap)
        else:
            logger.info("[bench.auto] budget exhausted society=%s/%s runs_today=%d/%d next=00:00Z",
                        gid, name, runs_today, cap)
    except Exception:
        pass


def run_charges_allowance(pol: dict, effect_count: int) -> bool:
    """Does this run spend one of the workload's `runs_per_day`?

    The allowance is the EFFECT allowance, not a poll counter: a run pays for it by producing the
    effect the workload declared. A publishing workload produces an airing, so an airing is what it
    pays with; a recording one publishes nothing and has no airing to count, so a completed run is
    its effect. A run that produced NOTHING pays nothing, and neither does a failed run (which never
    reaches here — the driver charges only on the success path).

    Not charging the empty run is the point. While a provider is down every attempt produces
    nothing, and charging them spends the whole day's allowance on runs that said nothing — so the
    cap then blocks the one run that could have spoken, and the workload goes quiet for a day
    because it failed. The attempt rate is bounded elsewhere and by design: the declared cadence
    governs the next attempt, a failure's retries are bounded by `on_failure.retries`, a boot-owed
    airing by `BOOT_AIRING_TRIES`, and the day's model SPEND by the LLM pool, which is the authority
    for spend — `runs_per_day` never was."""
    return bool(effect_count) or not wl_state.publishes_effect(pol)


def autorun_next_hint(policy: dict, state: dict, boot_id: str = "") -> str:
    """A33(c) — a short 'what fires next' for the Health line when a society is armed but not yet
    run: `boot` (the boot run hasn't fired this writer boot), `HH:MMZ` (a daily window, UTC — the Z
    makes A32 explicit), `interval` (an interval trigger), or `then` (a fired boot awaiting `then:`).
    `manual` never auto-fires."""
    trig = str(policy.get("trigger") or "manual")
    if trig == "boot" and state.get("boot_id") != boot_id:
        return "boot"
    nxt = trig if trig != "boot" else str(policy.get("then") or "none")
    if nxt.startswith("daily:"):
        hhmm = nxt.split(":", 1)[1]
        return "%sZ" % hhmm if not hhmm.endswith("Z") else hhmm
    if nxt.startswith("interval:"):
        return "interval"
    if nxt in ("none", "", "manual"):
        return "-"
    return nxt


def await_job(kernel, job_id: str, budget_s: float = 60.0):
    """Poll a submitted JCL job to a terminal state (bounded). Returns (ok, job). ok = DONE with no
    step errors. The driver runs at PRIO_LOW so a small maintenance job settles quickly."""
    if not job_id or not kernel.jcl_worker:
        return False, None
    deadline = time.time() + max(1.0, budget_s)
    job = None
    while time.time() < deadline:
        job = kernel.jcl_worker.get_job(job_id)
        if job is not None and getattr(job, "status", "") in ("DONE", "FAILED", "CANCELLED"):
            break
        time.sleep(0.1)
    if job is None:
        return False, None
    ok = getattr(job, "status", "") == "DONE" and not getattr(job, "step_errors", None)
    return ok, job


def derive_bench_tripped(kernel) -> set:
    """A39(c) — the society names a breaker has tripped (mode=manual, mode_by=breaker), read from the
    declared workloads' societies' meta. `force_manual` drops a tripped society from the auto index,
    so `list_auto_societies` cannot see it and the in-memory `_bench_tripped` is lost on a restart;
    this rebuilds it from durable state so Health keeps showing `tripped:` across a restart until
    provisioning re-arms. Bounded (one read per declaration); best-effort."""
    out = set()
    try:
        from lib.akasha.workbench import workload as _wl
        from lib.akasha.concepts.society import SocietyConcept
        sc = SocietyConcept(_authority.elevated(kernel, "driver"))
        decls = list(_wl.declarations(kernel))
    except Exception as exc:
        logger.warning("[bench.auto] skipped reason=%s detail=%s", SKIP_TRIPPED_DERIVE, exc)
        return out
    # F2 (v1.3.2) — one society that cannot be read (not provisioned yet on a cold boot: its group
    # does not exist, or the driver is not yet a member) is skipped, and the rest are still read.
    # The whole derive used to stop at the first one.
    read, skipped = 0, []
    for decl in decls:
        try:
            if _wl.problems(decl):
                continue
            gid, sname = _wl.society_of(decl)
            cur = sc.read_autorun(gid, sname)
            read += 1
            if cur.get("mode") == "manual" and cur.get("mode_by") == "breaker":
                out.add(sname)
        except Exception as exc:                     # noqa: BLE001 — one society, not the derive
            skipped.append("%s (%s)" % (decl.get("society") or "?", exc))
    if skipped:
        logger.info("[bench.auto] tripped_derive read=%d skipped=%d (not readable yet — not "
                    "provisioned on this boot?): %s", read, len(skipped), "; ".join(skipped[:5]))
    return out


def bench_last_metrics(kernel, bench: str, gid: str = "") -> dict:
    """A41.5 — the last summary a bench stamped ({corpus, classes, accuracy}), for the driver's
    run-end line. `bench` is the alias (`wb:<name>`) or the plain name; {} when there is none.

    Read through `bench.info`, an ordinary op, rather than by importing the concept class that
    happens to stamp it. The import was `from lib.akasha.concepts.bench_learning import …` — a
    platform module reaching rightward into a USER module by name, which is the one direction the
    layer map forbids (step 2 §5). Asking the op also means a bench that stamps nothing simply
    answers {}: the driver does not learn what kinds of bench exist."""
    plain = str(bench or "")
    if plain.startswith("wb:"):
        plain = plain[3:]
    if not plain:
        return {}
    try:
        data = {"name": plain}
        if gid:
            data["group"] = gid
        r = kernel.dispatch({"jsonrpc": "2.0", "method": "bench.info",
                             "params": {"client_id": "admin", "data": data}, "id": "lastm"},
                            TRUST_INTERNAL)
        m = ((r or {}).get("result") or {}).get("last_metrics") if isinstance(r, dict) else None
        return dict(m) if isinstance(m, dict) and m else {}
    except Exception as exc:
        logger.warning("[bench.auto] skipped reason=%s bench=%s detail=%s",
                       SKIP_METRICS_READ, bench, exc)
        return {}

def bench_autorun_tick(kernel, now: float = None) -> list:
    """ONE driver pass: for each auto-mode society, if its trigger is due and it is under budget,
    run its first policy workflow as ONE PRIO_LOW JCL job (through society.run, admin/INTERNAL),
    classify the outcome, and update the autorun state. Consecutive failures trip the breaker →
    mode=manual + an axis record. Returns a per-society action list (also the test seam)."""
    now = time.time() if now is None else now
    # D12 — the pool's day turn re-states every key's headroom BEFORE any gate is asked this tick.
    try:
        from lib.akasha.workbench import admission as _adm
        _adm.observe_day_turn(kernel)
    except Exception as exc:                          # noqa: BLE001 — reported, never a dead tick
        logger.warning("[llm] day-turn headroom restate failed: %s: %s", type(exc).__name__, exc)
    actions = []
    waiting_status = []          # for the Health line: societies gated on unfrozen data
    armed_next = []              # A33(c) — armed-but-not-yet-run: (name, next_hint) for Health
    budget_status = []           # A45 — societies held at the daily cap: (name, "n/cap")
    armed_today = 0
    boot_id = kernel._writer_boot_id()
    build_fp = kernel._build_fp()
    _tripped = getattr(kernel, "_bench_tripped", None)   # A35 — persists across ticks
    if _tripped is None:
        # A39(c) — seed it from durable society meta (mode_by=breaker) so Health shows `tripped:`
        # across a restart until provisioning re-arms, not only for trips made in THIS process.
        _tripped = kernel._bench_tripped = derive_bench_tripped(kernel)
    # S2-k4 — no pick while the ontology load is IN FLIGHT. A workload's template resolves ontology
    # atoms, so a pick that beats the load runs a cycle against a graph that is not there yet and
    # records a failure that was never the workload's.
    #
    # `is_running` and not the `after:` gate, because this is a DAEMON and not a boot body. A
    # schedule is ordered against the load by the registry; this ticks every 60 s for the life of
    # the process, so the question it must ask is "is a load happening right now?" — which is False
    # both before one starts and after it ends, and False forever on a cell that never loads
    # (an eval, a seed with no packs). One line per window, not one per tick: a repeated "still
    # waiting" is how a log stops being read.
    #
    # SCOPED since 09-28 (frontend, needs platform 1): one 400-atom pack held all five programmes
    # for 17 minutes. Only a cell's FIRST load holds everything (the graph is really not there);
    # otherwise the load says which packs it is rewriting and a workload is held only when one of
    # them declares a name the workload declares it reads (`wl_state.onto_hold`, per society below).
    from lib.akasha.api import schedule as _sched
    _onto_running = _sched.is_running(kernel, "ontology.loaded")
    if _onto_running:
        from lib.akasha.ontology import loader as _onto_ld
        _fl = _onto_ld.in_flight(kernel)
        # One line per MODE, not per load: a first load turns into a scoped one when its core is in
        # (v1.3), and that change must show — a log stuck on `first_load=1` reads as the VPS stall.
        if not _fl or _fl.get("first"):
            kernel._bench_first_held = True           # F1 — every workload is owed a run at release
            if getattr(kernel, "_bench_auto_gate_logged", False) != "all":
                kernel._bench_auto_gate_logged = "all"
                logger.info("[bench.auto] pick deferred reason=onto_load scope=all first_load=1 "
                            "(the cell's first ontology load is in flight; picking resumes on the "
                            "tick after it completes)")
            return actions
        if getattr(kernel, "_bench_auto_gate_logged", False) != "touched":
            kernel._bench_auto_gate_logged = "touched"
            logger.info("[bench.auto] onto_load in flight scope=touched packs=%s — only the "
                        "workloads a changing pack touches are held", ",".join(_fl.get("packs") or [])
                        or "-")
    else:
        kernel._bench_auto_gate_logged = False
        kernel._bench_onto_held_logged = set()
    try:
        from lib.akasha.concepts.society import SocietyConcept
        sess = _authority.elevated(kernel, "driver")
        sc = SocietyConcept(sess)
    except Exception as exc:
        logger.warning("[bench.auto] skipped reason=%s detail=%s — the whole tick, not one "
                       "society: nothing runs until this is fixed", SKIP_TICK_SESSION, exc)
        return actions
    # F1 (v1.3.2) — "the load's end is itself the trigger". A workload the load held is due on the
    # first tick after the hold lifts, whatever its cadence: its next slot is not waited for, and the
    # boot run's `fresh` skip does not apply (a daily programme that aired within the day would
    # otherwise stay silent until its next HH:MM). The held set is this process's, like the hold.
    _first_release = bool(getattr(kernel, "_bench_first_held", False))
    kernel._bench_first_held = False
    _load_held = getattr(kernel, "_bench_load_held", None)
    if _load_held is None:
        _load_held = kernel._bench_load_held = set()
    for ptr in sc.list_auto_societies():
        gid, name = ptr["gid"], ptr["name"]
        try:
            info = sc.read_autorun(gid, name)
            if info.get("mode") != "auto":
                continue
            _tripped.discard(name)                    # A35 — seen in the auto index ⇒ armed again
            pol, state = info.get("policy") or {}, dict(info.get("state") or {})
            wfs = list(pol.get("workflows") or [])
            if not wfs:
                continue
            if _onto_running:
                _hold = wl_state.onto_hold(kernel, pol)
                if _hold:
                    _hk = wl_state.key_of(pol) or "%s/%s" % (gid, name)
                    _held_log = getattr(kernel, "_bench_onto_held_logged", None)
                    if _held_log is None:
                        _held_log = kernel._bench_onto_held_logged = set()
                    if _hk not in _held_log:
                        _held_log.add(_hk)
                        logger.info("[bench.auto] pick deferred reason=%s workload=%s packs=%s "
                                    "names=%s", _hold["reason"], _hk,
                                    ",".join(_hold.get("packs") or []) or "-",
                                    ",".join(_hold.get("names") or []) or "-")
                    _load_held.add("%s/%s" % (gid, name))
                    actions.append({"society": "%s/%s" % (gid, name), "action": "held",
                                    "reason": _hold["reason"], "packs": _hold.get("packs") or [],
                                    "names": _hold.get("names") or []})
                    continue
            # A44 — the reset happens ONCE PER WRITER BOOT and is the ONLY thing that opens the boot
            # gate: on a new boot_id it stamps boot_id/build_fp and sets `boot_pending=True` (NOT pop
            # boot_id — the old code popped it and kept boot_done, so the same condition re-fired
            # every 60 s while the run was blocked, erasing the breaker + any pending retry each
            # minute). Clears the stale breaker + retry (a code fix may resolve the prior failure),
            # keeps last_run + runs_today (the daily budget). Staleness test is boot_id ONLY now;
            # boot_done is a mere informational flag. An operator edit is untouched (provisioning).
            _prev_boot = state.get("boot_id")
            if _prev_boot != boot_id:
                _reason = ("new-build" if (build_fp and state.get("build_fp") not in (None, build_fp))
                           else ("restart" if _prev_boot else
                                 ("carried-state" if (state.get("boot_done") or state.get("last_run"))
                                  else "first")))
                state["boot_id"] = boot_id               # A44(1) — stamp, do NOT pop
                state["build_fp"] = build_fp
                state["boot_pending"] = True             # the gate is open until the run starts
                state.pop("retry_at", None)
                state.pop("retry_count", None)
                state["breaker"] = 0
                # A45(2) — a NEW BUILD's boot run is EXEMPT from runs_per_day, at most once per build
                # fp (a code fix must be able to prove itself the day it deploys). restart /
                # carried-state / first are NOT exempt.
                if _reason == "new-build":
                    state["budget_exempt_fp"] = build_fp
                sc.write_autorun_state(gid, name, state)
                logger.info("[bench.auto] state reset society=%s/%s reason=%s (boot gate re-opened)",
                            gid, name, _reason)
            # Readiness gate (§2.3): a bench never runs before its declared source pools are frozen.
            # The wait is DECLARED (policy `requires`), visible (throttled log + Health), never a
            # prompt. Once every pool is present-and-frozen the run starts on the next tick.
            missing = requires_missing(kernel, pol.get("requires"), wl_state.key_of(pol))
            if missing:
                autorun_waiting_log(kernel, gid, name, missing)
                if wl_state.continuous(pol):
                    wl_state.gate(kernel, gid, name, wl_state.REASON_WAITING_SOURCE, pol=pol)
                waiting_status.append(name)
                actions.append({"society": f"{gid}/{name}", "action": "waiting", "missing": missing})
                continue
            armed_today += int(state.get("runs_today", 0)) if state.get("day") == time.strftime(
                "%Y-%m-%d", time.gmtime(now)) else 0
            _skey = "%s/%s" % (gid, name)
            _released = _first_release or _skey in _load_held
            if _released:
                _load_held.discard(_skey)
                _released = (str(pol.get("trigger") or "manual") != "manual"
                             and not state.get("run_once_done"))
                if _released:
                    logger.info("[bench.auto] released society=%s from onto_load — due now (the "
                                "load's end is the trigger, not the next slot)", _skey)
            if not _released and not autorun_due(pol, state, now, boot_id):
                # A33(c) — armed but not due yet: name WHY nothing is running (next=boot|HH:MMZ).
                armed_next.append((name, autorun_next_hint(pol, state, boot_id)))
                continue
            # §2 — idempotence. §1 makes every boot a trigger, so a deploy / crash loop / container
            # move minutes after an airing would re-air AND re-reserve. If the last airing is newer
            # than the cadence interval, skip: spend the boot gate (so it does not re-check every
            # tick) and record skipped=fresh on the show row. The interval is the declared TRIGGER's
            # (`every:1800s`, or a day for a `daily:` one) — read from the policy the declaration
            # projected, so the driver never asks which studio this is.
            if state.get("boot_pending") and not _released:
                _iv = wl_state.interval_of(pol)
                # The ruling says "if the programme's last AIRING is younger than its interval" —
                # and this read `last_run`, which is not the same thing. A run that aired nothing
                # (every turn refused at the LLM gate, say) still stamped `last_run`, so the next
                # deploy's boot airing was skipped as `fresh` on the strength of a broadcast that
                # never happened. That is how a programme which had NEVER AIRED stayed silent for
                # another whole day while the guide said `warming up` — the idempotence rule (§2)
                # swallowing the deploy-airs rule (§1). Measured against the AIRING, a programme
                # that has never aired has `0` here and therefore always airs at boot, which is
                # what "deploy airs" means; and a redeploy minutes after a real airing still
                # skips, which is what `fresh` is for.
                # NARROWED TO THIS WORKLOAD (`key_of(pol)`): four of them share the station bench,
                # so an unnarrowed read answers "when did ANY of them last air", and the busiest
                # one's airing would then skip every other one's boot airing as `fresh`.
                _last = wl_state.last_effect_at(kernel, wl_state.key_of(pol), pol)
                if _iv and _last and (now - _last) < _iv:
                    state["boot_pending"] = False
                    sc.write_autorun_state(gid, name, state)
                    wl_state.note(kernel, gid, name, effect=0, skipped=wl_state.REASON_FRESH,
                                  interval_s=_iv, pol=pol)
                    actions.append({"society": f"{gid}/{name}", "action": "skipped", "reason": "fresh"})
                    logger.info("[bench.auto] skipped society=%s/%s skipped=fresh "
                                "(last effect %.0fs ago < interval %.0fs)", gid, name, now - _last, _iv)
                    continue
            # budget: reset the daily counter on a new UTC day
            day = time.strftime("%Y-%m-%d", time.gmtime(now))
            if state.get("day") != day:
                state["day"], state["runs_today"] = day, 0
            budget = pol.get("budget") or {}
            cap = int(budget.get("runs_per_day", 4))
            # A45(2) — a NEW BUILD's pending boot run is EXEMPT from the daily cap (once per build fp).
            _exempt = bool(state.get("boot_pending") and state.get("budget_exempt_fp") == build_fp
                           and build_fp)
            if int(state.get("runs_today", 0)) >= cap and not _exempt:
                # A45(1) — the cap is no longer silent. A retry blocked by the budget is a WARNING;
                # the normal cap-reached is one INFO per society per UTC day. Health carries `budget:`.
                _is_retry = bool(float(state.get("retry_at") or 0.0)
                                 and now >= float(state.get("retry_at") or 0.0))
                autorun_budget_log(kernel, gid, name, int(state.get("runs_today", 0)), cap, day, _is_retry)
                if wl_state.continuous(pol):
                    wl_state.gate(kernel, gid, name, wl_state.REASON_RUNS_PER_DAY, pol=pol)
                budget_status.append((name, "%d/%d" % (int(state.get("runs_today", 0)), cap)))
                actions.append({"society": f"{gid}/{name}", "action": "budget_skip",
                                "runs_today": int(state.get("runs_today", 0)), "cap": cap})
                continue
            # One RUN = the whole policy workflow list in order (a bench pipeline b1→…→bN); each
            # block is one PRIO_LOW JCL job, awaited before the next so a later block sees an earlier
            # block's writes. A block failure records + stops the pipeline (the rest depend on it);
            # the run counts as failed for the breaker. The list is ONE run for the daily budget.
            _budget_s = float(budget.get("max_wall_s", 14400) or 60)
            per_wf = max(30.0, _budget_s / max(1, len(wfs)))
            # Who this run goes out AS, resolved before anything is spent or closed.
            _decl = _W.for_society(kernel, gid, name)
            _as = _W.client_of(_decl) if _decl else "admin"
            # A44(3) — close the boot gate BEFORE the first block and PERSIST it, so a crash
            # mid-run does not re-open it on its own (the next writer boot re-opens it). boot_id is
            # already stamped by the reset; write the gate-closed state now. Whether THIS run is
            # the one the deploy owes an airing for is read before the gate is closed, because the
            # obligation is discharged by an AIRING, not by a run — which is also why the
            # precondition above returns BEFORE this point: a run that never started aired nothing
            # and must leave the deploy's owed airing owed.
            _was_boot_run = bool(state.get("boot_pending"))
            if state.get("boot_pending"):
                state["boot_pending"] = False
                sc.write_autorun_state(gid, name, state)
            _run_t0 = time.time()                         # this run's window, for its own outcome
            _run_spent = 0                                # model calls this run paid for (the guard)
            _refused_id, _refused_retry_at = "", 0.0      # D11 — a refusal's own id and moment
            _n_effect = 0                                 # set from the effect read once the run is ok
            _run_rss0 = _rss_mb()                         # A48.3 — Δrss per bench.auto run
            _run_cronon0 = bench_cronon_count(kernel, info.get("bench"))   # E2-2 (F5) — clock start
            job_id = None
            ok = True
            reason = ""                                  # A28(b) — the failure reason, logged + carried
            # The run goes out AS THE WORKLOAD'S DECLARED CLIENT, not as admin. Provisioning
            # creates this workload's casts owned by that client, and you may only speak as an
            # avatar you own — so a driver that provisions as X and runs as admin produces a
            # society whose speaker owns none of its casts. That is not a say that fails loudly;
            # it is a say that does not happen, and the row reads `standing_by` forever. A society
            # with NO declaration — a hand-armed research bench — keeps admin, as it always had.
            for _wf in wfs:
                logger.info("[bench.auto] run start society=%s/%s bench=%s workflow=%s as=%s "
                            "budget_left=%d", gid, name, info.get("bench"), _wf, _as,
                            cap - int(state.get("runs_today", 0)))
                resp = kernel.dispatch({"jsonrpc": "2.0", "method": "society.run",
                                      "params": {"client_id": _as,
                                                 "data": {"group": gid, "name": name,
                                                          "workflow": _wf}}, "id": "ar"},
                                     TRUST_INTERNAL)
                # A28(b) — surface EVERY non-ok outcome: a dispatcher error (society.run raised), a
                # `refused`/`error` result status, a failed job (its step_errors), or a missing job id
                # (the silent case that hid the public-bench resolution bug). Never a silent fail.
                if isinstance(resp, dict) and resp.get("error"):
                    ok = False
                    reason = "%s: %s" % (_wf, (resp["error"] or {}).get("message") or resp["error"])
                    break
                res = (resp or {}).get("result") or {}
                if res.get("status") == "refused":
                    ok = False
                    # D11 — the refusal's OWN id (`reason`) and moment (`retry_at`), as data. The
                    # human sentence is only for the log line.
                    _refused_id = str(res.get("reason") or "")
                    try:
                        _refused_retry_at = float(res.get("retry_at") or 0.0)
                    except (TypeError, ValueError):
                        _refused_retry_at = 0.0
                    reason = "%s refused: %s" % (_wf, res.get("message") or _refused_id or "-")
                    break
                if res.get("status") == "error":
                    ok = False
                    reason = "%s error: %s" % (_wf, res.get("error"))
                    break
                if res.get("status") == "text_only":
                    # A52 — every advanced entry was free text / text-suspect (a positional token, not
                    # key=value): there is no job, and this is NOT the phantom "no job id" of a
                    # dispatched run. Name it precisely so the fix is obvious in the log.
                    ok = False
                    reason = "%s: no structured steps (text_only) suspect=%s" % (
                        _wf, res.get("text_suspect"))
                    break
                job_id = res.get("job_id")
                if not job_id:
                    ok = False
                    reason = "%s: no job id (bench=%r status=%s)" % (_wf, res.get("bench"), res.get("status"))
                    break
                wf_ok, _job = await_job(kernel, job_id, budget_s=per_wf)
                _run_spent += wl_state.job_spent(_job)
                # A37 — every block reports its outcome at INFO: how many steps ran, whether it
                # errored, and (on failure) the step errors. b3 (feature extraction) was silent —
                # a run that "completed" said nothing about what it observed. The deep per-op
                # counts (observed/skipped/failed, n_labeled/classes) are logged by the ops
                # themselves (vlab.run.execute, learning.feature.extract, learning.train); this line is
                # the driver's block-level ledger tying them to the job.
                _sd = getattr(_job, "step_done", 0) if _job else 0
                _sc = getattr(_job, "step_count", 0) if _job else 0
                _se = getattr(_job, "step_errors", None) if _job else None
                logger.info("[bench.auto] block society=%s/%s workflow=%s job=%s steps=%d/%d status=%s%s",
                            gid, name, _wf, job_id, _sd, _sc, "ok" if wf_ok else "failed",
                            (" step_errors=%s" % _se) if _se else "")
                # S2-a — if this workflow is a SWEEP BRANCH lineage, stamp its condition
                # done|failed (a no-op for a static block — its name has no sweep marker). This is
                # the pending→done|failed move; done is also derived by sweep.status, but a FAILED
                # branch (no evaluation written) would otherwise stay `pending` forever.
                try:
                    _bn = info.get("bench") or ""
                    _bn = _bn[3:] if _bn.startswith("wb:") else _bn
                    kernel.dispatch({"jsonrpc": "2.0", "method": "sweep.mark",
                                   "params": {"client_id": "admin", "data": {
                                       "bench": _bn, "branch": _wf,
                                       "status": "done" if wf_ok else "failed"}}, "id": "swm"},
                                  TRUST_INTERNAL)
                except Exception:
                    pass
                if not wf_ok:
                    ok = False
                    reason = "%s job %s %s" % (_wf, job_id,
                                               ("step_errors=%s" % _se) if _se
                                               else (getattr(_job, "status", "timeout") if _job else "timeout"))
                    break
            # `last_run` is the EFFECT clock, and it is stamped below, in the same block that
            # charges `runs_per_day` — once the outcome is known. Stamped here, before it, a run
            # that produced nothing satisfied today's `daily:` window and bought a whole day of
            # silence for a failure nobody had yet diagnosed (order 2026-09-22 §3). The allowance
            # has been charged on the outcome since step 0; the clock now agrees with it.
            state["boot_done"] = True
            state["boot_id"] = boot_id                   # A33 — this boot's run is recorded
            state["build_fp"] = build_fp
            retries = int((pol.get("on_failure") or {}).get("retries", 0))
            _pick_actions = []          # appended AFTER the run action so `ran` stays first in acts
            if ok:
                state["breaker"] = 0
                state.pop("retry_at", None)
                state.pop("retry_count", None)
                if pol.get("run_once"):
                    state["run_once_done"] = True
                # A41.5 — carry the last train summary on the run-end line when the pipeline trained.
                _sum = bench_last_metrics(kernel, info.get("bench"), gid)
                _tail = ""
                if _sum:
                    _tail = " corpus=%s classes=%s accuracy=%s" % (
                        _sum.get("corpus"), _sum.get("classes"), _sum.get("accuracy"))
                _rss1 = _rss_mb()                         # A48.3 — the run's memory footprint
                if _run_rss0 is not None and _rss1 is not None:
                    _tail += " Δrss=%+dMB" % (_rss1 - _run_rss0)
                logger.info("[bench.auto] run end society=%s/%s status=ok breaker=0%s", gid, name, _tail)
                # §4 — report the run to the programme guide from what it ACTUALLY aired. This used
                # to assert `aired=1` on any job that completed, which is a different claim: the
                # shelf's five turns each stand by on their own when the model is refused, and the
                # job still succeeds. A run that aired nothing was published as an airing, and the
                # `fresh` skip then believed it. So the bench's own record decides, and a run that
                # aired nothing records the standby WITH the reason its turns recorded — which is
                # also what moves the programme out of `warming_up` instead of leaving it there.
                _n_effect, _why = wl_state.run_effect(kernel, pol, since=_run_t0)
                # THE OP'S OWN REASON, VERBATIM — OR EMPTY. The platform does not name application
                # status (ruling 2026-09-23 §2).
                #
                # This line read `_why or wl_state.REASON_NO_TEXT`, and that substitution is the
                # fault the ruling is about. `no_text` is a MODEL-PROVIDER word: it means a model
                # was called and returned nothing. Defaulting to it stamped that word on workloads
                # that never called a model at all — `news_show_x` (which posts a thread) and the
                # plants vision bench — so the rooms showed a provider failure for runs where no
                # provider was involved. The platform invented the sentence and the sentence was
                # false.
                #
                # An empty reason is the honest answer to "the op did not say", and the retry
                # ladder already treats an unknown id as NOT transient, which is the safe
                # behaviour: waiting for the next trigger cannot make anything worse, and only the
                # caller that actually made the model call knows whether a retry would help. The
                # LLM gateway writes `no_text` / `provider_429` on ITS observation of a model call,
                # which is the one place those words are true.
                _reason = _why
                # The allowance is charged HERE, once the outcome is known, and only for a run that
                # produced the declared effect (see `run_charges_allowance`). This is the ONE site
                # that moves `runs_today`.
                if run_charges_allowance(pol, _n_effect):
                    state["runs_today"] = int(state.get("runs_today", 0)) + 1
                    state["last_run"] = now           # the EFFECT clock — one site, one meaning
                # THE ROLL-UP THE HEALTH LINE READS. `wl_note` existed and NOTHING CALLED IT, so
                # `workloads(aired_today=…)` sat at 0 while the rooms showed today's airings (D6):
                # a counter with no writer, which reads exactly like a station that never aired.
                # One call, on the one path that knows a run's outcome, for BOTH outcomes — the
                # standby side is what makes a quiet workload say why it is quiet.
                wl_state.wl_note(kernel, {"effect": _n_effect, "source": "%s/%s" % (gid, name),
                                          "reason": wl_state.reason_id(_reason) or "unknown",
                                          "reason_key": wl_state.reason_id(_reason)})
                if _n_effect:
                    wl_state.note(kernel, gid, name, effect=_n_effect, pol=pol)
                else:
                    logger.info("[bench.auto] run produced NO EFFECT society=%s/%s reason=%s "
                                "(the job succeeded; the declared effect read counted none)", gid, name,
                                wl_state.reason_id(_reason))
                    # The LADDER settles FIRST, and the guide row is written from what it left
                    # behind. Written the other way round — the row computed from the state the
                    # run walked in with — a programme that had a retry armed by an earlier
                    # transient failure, and has now stopped on a grant, publishes that dead
                    # retry's moment as its next update while this very block pops it.
                    #
                    # §1 — the boot obligation is discharged by an AIRING, not by a run. A boot
                    # run that broadcast nothing leaves the deploy still owing one, so the gate
                    # re-opens and the driver tries again shortly instead of falling through to
                    # the next scheduled slot (which, for a once-a-day programme, is a day of
                    # silence). Bounded: `boot_tries` caps the attempts, and the backoff grows,
                    # so a provider that is down cannot turn this into a loop.
                    # The ladder settles FIRST, and the guide row is written from what it left
                    # behind — never from the state the run walked in with, or a programme that
                    # had a retry armed by an earlier transient failure and has now stopped on a
                    # grant publishes that dead retry as its next update while this block drops it.
                    #
                    # EVERY branch below leaves `retry_at` set to when this workload will next
                    # try, because `retry_at` is now what holds the trigger between attempts: a
                    # branch that left it unset would leave the workload unpaced, and an empty run
                    # under an open `daily:` window would be attempted on every tick of the day.
                    _win = wl_state.next_attempt(pol, now, float(state.get("last_run") or 0.0))
                    if not wl_state.is_transient(_reason):
                        # A grant or a precondition — no clock fixes it and no retry can. It waits
                        # for the thing that CAN: the next provisioning pass or boot, either of
                        # which clears this. Said once, in the vocabulary, at the place that
                        # decided it, rather than spending the day re-proving the same wall.
                        state.pop("boot_tries", None)
                        state["retry_at"] = _win
                        logger.warning("[bench.auto] not retried society=%s/%s reason=%s "
                                       "(waits for provisioning)", gid, name,
                                       wl_state.reason_id(_reason))
                    elif _was_boot_run and wl_state.continuous(pol):
                        _bt = int(state.get("boot_tries", 0)) + 1
                        if _bt <= wl_state.BOOT_AIRING_TRIES:
                            state["boot_tries"] = _bt
                            state["boot_pending"] = True
                            state["retry_at"] = now + min(1800.0, 120.0 * _bt)
                            logger.info("[bench.auto] boot run still owed society=%s/%s "
                                        "(no effect, reason=%s) — retry %d/%d in %dmin",
                                        gid, name, wl_state.reason_id(_reason), _bt, wl_state.BOOT_AIRING_TRIES,
                                        int(min(1800.0, 120.0 * _bt) / 60))
                        else:
                            state.pop("boot_tries", None)
                            state["retry_at"] = _win
                            logger.warning("[bench.auto] boot run given up society=%s/%s after "
                                           "%d tries (reason=%s) — the declared schedule takes over",
                                           gid, name, wl_state.BOOT_AIRING_TRIES, wl_state.reason_id(_reason))
                    else:
                        # Transient, outside the boot obligation: the trigger's own next window is
                        # the retry. The workload has a cadence; a run that produced nothing does
                        # not earn a faster one.
                        state["retry_at"] = _win
                    # WHEN it will next try, honestly — the moment the ladder just settled on.
                    # Never `now + interval` of a run that produced nothing: that told a reader an
                    # update was half an hour away while the programme stood by on something no
                    # clock would fix. A trigger with no window (boot, manual) has no moment to
                    # publish and none to be held by; it is the boot gate that fires it.
                    _next = float(state.get("retry_at") or 0.0)
                    wl_state.note(kernel, gid, name, effect=0,
                                  skipped=_reason, pol=pol, next_at=_next)
                if _n_effect:
                    state.pop("boot_tries", None)     # the effect happened: the deploy's obligation is paid
                    # EVERY BRANCH LEAVES A NEXT ATTEMPT — this one included (D1). The ok-and-aired
                    # path popped `retry_at` at the top of the block and wrote none back, leaving
                    # the pacing to `autorun_due`'s fall-through on `last_run`. That is a SECOND
                    # scheduling mechanism for the same question, and the ruling of 09-22 already
                    # settled it: `retry_at` is the schedule, both ways. One mechanism cannot
                    # disagree with itself; two can, and the day a branch forgets to feed the one
                    # it is not using, the workload runs on every tick.
                    state["retry_at"] = wl_state.next_attempt(
                        pol, now, float(state.get("last_run") or now))
                # E2-2 (F5) / R4 — ALWAYS one line per run end, minted=0 included (a sentinel-only run
                # that minted no coordinate is the interesting case: the clock did NOT move). Name the
                # coordinates this run minted, the branches it executed, and the thought count.
                try:
                    _cs = bench_cronon_summary(kernel, info.get("bench"), _run_cronon0) or {}
                    _mint = int(_cs.get("minted") or 0)
                    if _mint:
                        logger.info("[cronon] %s minted=%d c%s..c%s executes=%s thought=%d",
                                    info.get("bench"), _mint, _cs.get("first"), _cs.get("last"),
                                    ",".join(_cs.get("executes") or []) or "-", int(_cs.get("thought") or 0))
                    else:
                        logger.info("[cronon] %s minted=0 (no new bench coordinates this run)",
                                    info.get("bench"))
                except Exception:
                    pass
                # B1-c — after the static run ends ok, the driver PICKS a sweep branch to run
                # (budget-gated per sweep): materialise when nothing pending, pick the oldest pending
                # non-quarantined condition, run it as society.run does, stamp the cost on its
                # coordinate. Best-effort — a pick never fails the static run that already succeeded.
                # S2-k4 — NOT while a pack is loading: a sweep pick materialises + runs against the
                # graph, and the writer is busy importing during a boot/onto.reload load. `_relations_
                # ready()` is the same "load has settled" gate the boot schedulers use; until it is
                # ready the pick is DEFERRED (the next tick picks once the load finishes), never run
                # against a half-loaded graph.
                if not kernel._relations_ready():
                    _pick_actions.append({"society": f"{gid}/{name}", "action": "pick_deferred",
                                          "reason": "ontology load in progress"})
                    logger.info("[bench.auto] pick deferred society=%s/%s: ontology load in progress",
                                gid, name)
                else:
                    try:
                        picks = bench_driver_pick(kernel, sc, gid, name, info, pol, per_wf)
                        for _p in picks:
                            _pick_actions.append({"society": f"{gid}/{name}", "action": "pick", **_p})
                    except Exception as _pexc:
                        logger.warning("[bench.auto] skipped reason=%s society=%s/%s detail=%s",
                                       SKIP_SWEEP_PICK, gid, name, _pexc)
            else:
                # §4 — a run refused at LLM admission (pool exhausted, -32005) records
                # skipped=llm_pool on the show row, so the page shows `standing by · llm_pool`
                # instead of a blank wait; any other failure leaves the last skipped as-is.
                # A precondition failure is not a programme failure. "has no workflow" means the
                # cell was never reconciled to the declaration, and reporting it as a breaker
                # sent two days of diagnosis to the wrong place. It is named, and it does NOT
                # burn the breaker: retrying cannot create a workflow, only a boot can.
                _missing_wf = "has no workflow" in str(reason)
                if _missing_wf:
                    wl_state.note(kernel, gid, name, effect=0,
                                  skipped=wl_state.REASON_NOT_PROVISIONED, pol=pol)
                    logger.error("[bench.auto] society=%s/%s CANNOT RUN: %s — the cell is not "
                                 "reconciled to its declaration; a boot repairs it, a retry "
                                 "cannot", gid, name, reason)
                _transient_refusal = bool(_refused_id) and wl_state.is_transient(_refused_id)
                if _transient_refusal:
                    # D11 — REFUSED FOR A REASON TIME CURES (the pool is full today). Classified by
                    # the reason's own id, never by a substring of a message. The run is recorded
                    # with that reason; the breaker is NOT touched (nothing is broken — the run
                    # was never admitted); and the next attempt is the moment the refusing party
                    # names — the pool's day turn — not the ordinary retry ladder, which would
                    # spend its retries against the same full pool and then wait for the next
                    # DAILY window: three programmes dark for most of a day, on 09-25.
                    wl_state.note(kernel, gid, name, effect=0, skipped=_refused_id, pol=pol)
                    state["retry_at"] = (_refused_retry_at if _refused_retry_at > now
                                         else wl_state.next_attempt(
                                             pol, now, float(state.get("last_run") or 0.0)))
                    state.pop("retry_count", None)
                    logger.warning("[bench.auto] run end society=%s/%s status=refused reason=%s "
                                   "breaker=%d (unchanged) — next attempt at %s, when the refusing "
                                   "party says it can be admitted", gid, name, _refused_id,
                                   int(state.get("breaker", 0)),
                                   time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                                 time.gmtime(state["retry_at"])))
                elif _refused_id:
                    # A refusal no clock cures (a grant, a precondition): recorded by its id, and
                    # it takes the ordinary ladder below like any failed run.
                    wl_state.note(kernel, gid, name, effect=0, skipped=_refused_id, pol=pol)
                if not _missing_wf and not _transient_refusal:
                    state["breaker"] = int(state.get("breaker", 0)) + 1
                # A28(c) — retry sooner than `then:`, bounded by on_failure.retries, backoff 10min×attempt.
                rc = int(state.get("retry_count", 0))
                if _transient_refusal:
                    pass                                 # paced above, by the refusing party
                elif rc < retries:
                    rc += 1
                    state["retry_count"] = rc
                    state["retry_at"] = now + 600.0 * rc
                    logger.warning("[bench.auto] run end society=%s/%s status=failed breaker=%d "
                                   "reason=%s (retry %d/%d in %dmin)", gid, name,
                                   int(state.get("breaker", 0)), reason, rc, retries, 10 * rc)
                else:
                    # …and the exhausted-retries branch names the moment too, rather than popping
                    # the key and hoping the trigger's own window is closed (D1).
                    state["retry_at"] = wl_state.next_attempt(
                        pol, now, float(state.get("last_run") or 0.0))
                    logger.warning("[bench.auto] run end society=%s/%s status=failed breaker=%d "
                                   "reason=%s (retries exhausted — next attempt at %s)", gid, name,
                                   int(state.get("breaker", 0)), reason,
                                   time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                                 time.gmtime(state["retry_at"]))
                                   if state.get("retry_at") else "the next boot")
            # THE GUARD (order v78) — a paid run that produced nothing extends a streak; K in a
            # row stops the workload for real, whatever its duty. Decided on the run's own record
            # (D10's `run_outcome`, which now reads THIS run's rows) and its own spend.
            # D15 — ONE MEANING OF "THIS RUN DID ITS JOB": the job succeeded AND it produced the
            # declared effect (`run_charges_allowance`, the predicate the allowance and the effect
            # clock already use). The guard, the run record and so `workload.status.last.ok` all
            # read this one value. `ok` alone was the JOB's success, so since 4.12 a stood-by run
            # (`news_show_x`: job ok, `no_consent`, no effect) read as on air.
            _effect_ok = bool(ok and run_charges_allowance(pol, _n_effect))
            _guard_trip = wl_state.spent_without_effect(state, pol, _run_spent, _effect_ok)
            # THE RUN RECORD (group 4, 4.12(a)) — ONE ROW PER RUN, whatever happened, in the
            # workload's own namespace. `workload.status.last` reads this and nothing else, so a
            # refusal, a failure, or a run whose application row landed under another key is still
            # a recorded run with its reason. The reason is the op's own id or message, verbatim.
            # `ok` is the EFFECT outcome (D15); the job's own outcome stays visible as `job_ok`.
            wl_state.record_run(
                kernel, wl_state.key_of(pol) or "%s/%s" % (gid, name), at=_run_t0, ok=_effect_ok,
                reason=(_refused_id or reason) if not ok else _reason,
                effect_count=_n_effect if ok else 0, spent=_run_spent, by=_as,
                job_id=job_id or "", job_ok=ok)
            sc.write_autorun_state(gid, name, state)
            action = {"society": f"{gid}/{name}", "action": "ran", "ok": ok, "job_id": job_id,
                      "reason": reason or None, "workflows": list(wfs), "spent": _run_spent}
            if _guard_trip:
                _why = wl_state.REASON_SPENT_WITHOUT_EFFECT
                sc.force_manual(gid, name, reason=_why)
                wl_state.gate(kernel, gid, name, _why, pol=pol)
                logger.warning("[bench.auto] breaker tripped society=%s/%s reason=%s runs=%d "
                               "calls=%d — %d consecutive paid runs produced nothing; stopped "
                               "until a new build or config re-arms it", gid, name, _why,
                               int(state.get("spent_no_effect", 0)),
                               int(state.get("spent_no_effect_calls", 0)),
                               int(state.get("spent_no_effect", 0)))
                action["breaker_tripped"] = True
                action["reason"] = _why
                _tripped.add(name)                   # A35 — surfaced on Health until re-armed
                actions.append(action)
                actions.extend(_pick_actions)
                continue
            brk = int((pol.get("on_failure") or {}).get("breaker", 3))
            if int(state.get("breaker", 0)) >= brk:
                if wl_state.continuous(pol):
                    # A continuous workload stays on the schedule. Dropping to manual would make it
                    # silent until an operator noticed — the exact failure the airing ruling
                    # exists to prevent, and one nobody would see because the programme would
                    # simply stop appearing. It reports `breaker` and keeps its cadence.
                    wl_state.gate(kernel, gid, name, wl_state.REASON_BREAKER, pol=pol)
                    logger.warning("[bench.auto] breaker at %d society=%s/%s — a CONTINUOUS "
                                   "workload stays armed and keeps its cadence (reported as "
                                   "reason=%s)", brk, gid, name, wl_state.REASON_BREAKER)
                    action["breaker_reported"] = True
                else:
                    sc.force_manual(gid, name, reason=f"breaker {brk}")
                    logger.warning("[bench.auto] breaker tripped society=%s/%s workflows=%s → manual",
                                   gid, name, wfs)
                    action["breaker_tripped"] = True
                    _tripped.add(name)               # A35 — surfaced on Health until re-armed
            actions.append(action)
            actions.extend(_pick_actions)            # pick / pick_deferred come AFTER the run action
        except Exception as exc:
            logger.warning("[bench.auto] skipped reason=%s society=%s/%s detail=%s",
                           SKIP_SOCIETY_TICK, gid, name, exc)
    # Health line status: a tripped breaker is the loudest (A35 — otherwise the trip is invisible),
    # then waiting-on-data, then an armed-but-not-run society names WHY nothing runs (A33(c)), then a
    # compact runs_today roll-up. A tripped society is out of the auto index, so `_bench_tripped`
    # persists across ticks until provisioning re-arms it (a seen auto society is discarded above).
    ran = sum(1 for a in actions if a.get("action") == "ran")
    if _tripped:
        wl_state.driver_status(kernel, "tripped:%s" % ",".join(sorted(_tripped)[:3]))
    elif waiting_status:
        wl_state.driver_status(kernel, "waiting:data(%s)" % ",".join(sorted(set(waiting_status))))
    elif budget_status and not ran:
        # A45(1) — the daily cap is visible on Health instead of a bare runs_today.
        wl_state.driver_status(kernel, "budget:%s next=00:00Z" % ",".join(
            "%s=%s" % (n, r) for n, r in budget_status[:3]))
    elif armed_next and not ran:
        wl_state.driver_status(kernel, "armed next=%s" % ",".join(
            "%s" % nxt for _n, nxt in armed_next[:3]))
    else:
        wl_state.driver_status(kernel, "runs_today=%d%s" % (armed_today, (" ran=%d" % ran) if ran else ""))
    return actions


def bench_balias_norm(balias: str) -> str:
    """R4 — normalise a bench alias to the uslug form the coordinate atoms use. `info.get('bench')`
    can carry the raw society id (`wb:plants-vision`, hyphen), while `_locate_observation` writes
    `cronon:wb:plants_vision:c<n>` via `_bench_alias` (uslug). Without this the summary reads a set
    that never fills and reports minted=0 for a run that DID advance the clock."""
    import re
    tag = balias[3:] if (balias or "").startswith("wb:") else (balias or "")
    return "wb:%s" % re.sub(r"[^a-z0-9]+", "_", tag.lower()).strip("_")


def bench_cronon_all_set(kernel, balias: str) -> str:
    """The bench clock's coordinate INDEX set name (`cronon:wb:<tag>:all`), tag uslug-normalised."""
    return "cronon:%s:all" % bench_balias_norm(balias)


def bench_cronon_count(kernel, balias: str) -> int:
    """E2-2 (F5) — the number of coordinates on a bench clock right now (the run-start high-water,
    so the per-run summary can name only what THIS run minted). Nucleus read; 0 on any error."""
    try:
        nuc = getattr(kernel.manager, "shared_nucleus", None)
        core = nuc.core if nuc else None
        if core is None:
            return 0
        return len(core.get_collection_members(bench_cronon_all_set(kernel, balias)) or [])
    except Exception:
        return 0


def bench_driver_pick(kernel, sc, gid: str, name: str, info: dict, pol: dict,
                       per_wf: float) -> "List[dict]":
    """B1-c — drive a society's admitted sweeps AFTER its static run ended ok. For each sweep name in
    the policy: `SweepConcept.driver_pick` (budget-gated — materialises when nothing pending, spends
    one unit at pick start), then run the picked branch through `society.run` exactly as the static
    blocks run, stamp its condition done|failed, and record the cost {wall_s, reused, observed} on
    the branch's execution coordinate. Returns one summary dict per pick made (for the action log)."""
    out: "List[dict]" = []
    sweeps = list(pol.get("sweeps") or [])
    if not sweeps:
        return out
    from lib.akasha.concepts.sweep import SweepConcept
    from lib.akasha.jcl.workspace_context import system_context as _sys_ctx
    bench = info.get("bench") or ""
    bare = bench[3:] if bench.startswith("wb:") else bench
    swc = SweepConcept(_authority.elevated(kernel, "driver"))
    for sw in sweeps:
        pick = swc.driver_pick(bench=bare, name=sw)
        if pick.get("status") != "picked":
            continue
        branch_slug = pick.get("branch_slug")
        lineage = pick.get("branch")
        budget_left = pick.get("budget_left")
        total = pick.get("total")
        logger.info("[bench.auto] pick sweep=%s branch=%s cond8=%s budget_left=%s/%s kind=%s",
                    sw, lineage, pick.get("cond8"),
                    budget_left if budget_left is not None else "-", total if total else "-",
                    pick.get("kind"))
        _c0 = bench_cronon_count(kernel, bench)
        _t0 = time.time()
        # a drift pick re-runs a DONE branch: rewind it to its fork position so the swept tail
        # re-executes (a fresh evaluation → a result_drift deviation if the artifact_id moves).
        if pick.get("kind") == "drift" and pick.get("fork_pos") is not None:
            try:
                kernel.dispatch({"jsonrpc": "2.0", "method": "wf.rewind",
                               "params": {"client_id": "admin", "data": {
                                   "bench": bare, "branch": branch_slug,
                                   "pos": int(pick.get("fork_pos") or 0), "by": "driver"}}, "id": "dr"},
                              TRUST_INTERNAL)
            except Exception:
                pass
        resp = kernel.dispatch({"jsonrpc": "2.0", "method": "society.run",
                              "params": {"client_id": "admin", "data": {
                                  "group": gid, "name": name, "workflow": branch_slug,
                                  "branch": branch_slug}}, "id": "sp"}, TRUST_INTERNAL)
        res = (resp or {}).get("result") or {} if isinstance(resp, dict) else {}
        job_id = res.get("job_id")
        wf_ok = False
        if job_id:
            wf_ok, _job = await_job(kernel, job_id, budget_s=per_wf)
        # the pending→done|failed move (the same one the static block-status site makes for a branch)
        try:
            kernel.dispatch({"jsonrpc": "2.0", "method": "sweep.mark",
                           "params": {"client_id": "admin", "data": {
                               "bench": bare, "branch": branch_slug,
                               "status": "done" if wf_ok else "failed"}}, "id": "spm"}, TRUST_INTERNAL)
        except Exception:
            pass
        _wall = round(time.time() - _t0, 3)
        # cost on the branch's LAST execution coordinate this pick minted (universal timing metadata;
        # written under system_context — the tick thread has no per-turn workspace). Best-effort.
        _cs = bench_cronon_summary(kernel, bench, _c0) or {}
        _last = _cs.get("last")
        if _last not in (None, "?"):
            try:
                with _sys_ctx():
                    _ck = swc._key("cronon:%s:c%d" % (swc._bench_alias(bare), int(_last)))
                    if _ck:
                        _prev = getattr(swc, "_space", ""); swc._space = ""
                        try:
                            swc._set_meta(_ck, "cost", {"wall_s": _wall, "reused": 0,
                                                        "observed": int(_cs.get("minted") or 0)})
                        finally:
                            swc._space = _prev
            except Exception:
                pass
        logger.info("[bench.auto] pick end sweep=%s branch=%s job=%s status=%s wall_s=%.1f",
                    sw, lineage, job_id, "ok" if wf_ok else "failed", _wall)
        out.append({"sweep": sw, "branch": lineage, "cond8": pick.get("cond8"),
                    "kind": pick.get("kind"), "ok": wf_ok, "job_id": job_id,
                    "budget_left": budget_left, "wall_s": _wall})
    return out


def bench_cronon_summary(kernel, balias: str, n0: int) -> dict:
    """E2-2 (F5) — summarise the coordinates a bench.auto run minted (the coordinate index set is
    append-ordered, so members[n0:] are this run's): {minted, first, last, executes:[branches],
    thought}. `executes` reads each new EXECUTION coordinate's `cronon:executes` link → the plan
    entry alias `workflow:<tag>:<branch>:<n>`, distinct branches. All O(minted) — a bounded set
    read, never a scan. Nucleus-only (the coordinate atoms + links live there, §1.7)."""
    nuc = getattr(kernel.manager, "shared_nucleus", None)
    core = nuc.core if nuc else None
    if core is None:
        return {}
    members = list(core.get_collection_members(bench_cronon_all_set(kernel, balias)) or [])
    new = members[n0:]
    if not new:
        return {"minted": 0}
    _nb = bench_balias_norm(balias)             # R4 — uslug form the coordinate atoms use
    positions, thought, branches = [], 0, []
    _tag = _nb[3:]
    for ck in new:
        try:
            aliases = core.get_aliases_by_key(ck) or []
            calias = aliases[0] if aliases else ""
            if calias.startswith("cronon:%s:c" % _nb):
                try:
                    positions.append(int(calias.rsplit(":c", 1)[1]))
                except (ValueError, IndexError):
                    pass
            row = core.get_chunk_raw(ck)
            cmeta = (json.loads(row["meta"]) if row and row.get("meta") else {}) or {}
            if cmeta.get("mode") == "thought":
                thought += 1
            for l in (core.get_adjacent_links(ck, "cronon:executes") or []):
                dst = l.get("dst") if isinstance(l, dict) else None
                if not dst:
                    continue
                for ea in (core.get_aliases_by_key(dst) or []):
                    if ea.startswith("workflow:%s:" % _tag):
                        br = ea.split(":")[2] if len(ea.split(":")) > 3 else ""
                        if br and br not in branches:
                            branches.append(br)
        except Exception:
            continue
    positions.sort()
    return {"minted": len(new), "first": positions[0] if positions else "?",
            "last": positions[-1] if positions else "?", "executes": branches, "thought": thought}


def schedule_bench_autorun(kernel) -> None:
    """G3.7 — the auto-execution driver: a 60 s writer-role tick that runs due auto-mode societies
    (at most one run per society per tick), trips the breaker on repeated failure, and honours the
    stop switch (an operator's mode=manual drops the society from the index). Serve-only skips."""
    if os.environ.get("AKASHA_SERVE_ONLY", "").strip().lower() not in ("", "0", "no", "false", "off"):
        return

    def _loop():
        from lib.akasha import lifecycle
        _hb = os.path.join(kernel.base_dir, "central", "boot.heartbeat")
        _dl = time.time() + 900
        while time.time() < _dl and os.path.exists(_hb):
            if lifecycle.wait_or_shutdown(2):
                return
        # Wait for the declared-workload pass (it writes the workflow entries a run executes) before
        # the first tick — a tick ahead of it runs the previous build's entries (10-03 item 1). Ceiling
        # 30 min, then proceed with a WARNING (never wedge the driver on a stuck provisioner).
        _ev = getattr(kernel, "_workload_provision_done", None)
        if _ev is not None:
            _waited = 0.0
            while _waited < 1800.0 and not _ev.is_set():
                if lifecycle.wait_or_shutdown(2):
                    return
                _waited += 2.0
            if not _ev.is_set():
                logger.warning("[bench.auto] provisioning pass not seen after 30min — ticking on the "
                               "stored policy")
        while True:
            try:
                bench_autorun_tick(kernel)
            except Exception as exc:
                logger.warning("[bench.auto] skipped reason=%s detail=%s", SKIP_DRIVER_TICK, exc)
            if lifecycle.wait_or_shutdown(60):
                return

    import threading as _thr
    _thr.Thread(target=_loop, name="bench-autorun", daemon=True).start()


def leaderboard_hydrate_all(kernel) -> dict:
    """S2-l/S2-m — the leaderboard hydrate regenerator (hydrate registry `leaderboard`,
    on_boot=verify): rebuild every sweep's board from its evaluations Set. The board is DERIVED
    state (R0), so it is never an operator step — it is rebuilt when a sweep evaluation lands
    (learning.evaluate) and VERIFIED here at boot: a board equal to its regeneration is a no-op
    (artifact_id unchanged), a MISSING one is repaired.

    S2-m — the regenerator enumerates from the CANONICAL `sweep_def` atoms, not only from the
    `set:wb:sweeps:all` index (which sweeps defined before S2-l never joined — an index that only
    new writes join is not a source of truth, S1-a §1.3). The index is read every boot (bounded,
    O(#sweeps)); the canonical alias-index scan that backfills it runs ONCE per process/build
    (memory discipline R4 — a boot-once repair like the retention backfill; a new build is a new
    process, so it re-scans then). Returns {rebuilt, checked}; `rebuilt` is the hydrate `assigned`
    count (0 = every board current)."""
    from lib.akasha.jcl.workspace_context import system_context as _sys_ctx
    from lib.akasha.concepts.sweep import SweepConcept
    from lib.akasha.concepts._universal import UniversalConcept
    try:
        session = _authority.elevated(kernel, "driver")
    except Exception:
        return {"rebuilt": 0, "checked": 0, "note": "no admin session"}
    u = UniversalConcept(session); u._space = ""
    sw = SweepConcept(session)
    pairs = {}                                          # (bench, sweep) -> def atom key
    for k in u._members("set:wb:sweeps:all"):          # the index — bounded, every boot
        dm = u._meta(u._alias(k) or k) or {}
        if dm.get("concept") == "sweep_def" and dm.get("sweep"):
            balias = dm.get("bench") or ""              # wb:<slug>
            bench = balias[3:] if balias.startswith("wb:") else balias
            if bench:
                pairs.setdefault((bench, dm["sweep"]), k)
    # S2-m — canonical enumeration + index backfill, ONCE per process/build (the boot-once repair
    # scan). A sweep_def atom's alias is exactly `wb:<bench>:sweep:<name>` (4 segments); its Sets
    # carry the `set:` prefix / more segments and are excluded.
    nucleus = getattr(kernel.manager, "shared_nucleus", None)
    core = getattr(nucleus, "core", None) if nucleus is not None else None
    if core is not None and not getattr(kernel, "_leaderboard_reindex_done", False):
        kernel._leaderboard_reindex_done = True
        try:
            for row in (core.get_aliases_by_pattern("wb:%:sweep:%") or []):
                alias = row.get("alias") or ""
                parts = alias.split(":")
                if len(parts) != 4 or parts[0] != "wb" or parts[2] != "sweep":
                    continue
                dm = u._meta(alias) or {}
                if dm.get("concept") != "sweep_def" or not dm.get("sweep"):
                    continue
                key = row.get("key")
                if key and (parts[1], dm["sweep"]) not in pairs:
                    pairs[(parts[1], dm["sweep"])] = key
                    with _sys_ctx():                    # backfill — the index becomes an accelerator
                        u._add_to_set("set:wb:sweeps:all", key)
        except Exception as exc:
            logger.warning("[hydrate] skipped reason=%s detail=%s",
                           SKIP_LEADERBOARD_ENUMERATE, exc)
    rebuilt = checked = 0
    for (bench, sweep) in pairs:
        checked += 1
        try:
            with _sys_ctx():                            # boot write path — exempt the single-route guard
                r = sw.build_leaderboard(bench=bench, name=sweep)
            if r.get("changed"):
                rebuilt += 1
        except Exception as exc:
            logger.warning("[hydrate] skipped reason=%s bench=%s sweep=%s detail=%s",
                           SKIP_LEADERBOARD_REBUILD, bench, sweep, exc)
    return {"rebuilt": rebuilt, "checked": checked}

