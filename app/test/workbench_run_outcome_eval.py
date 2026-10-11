#!/usr/bin/env python3
"""
A run's outcome is read from THAT run's record — and a paid run that produced nothing is counted.

Order v78, two platform items, and the second is only safe because of the first.

D10  The op's stood-by reason never reached the run record: `reason=''` on every run, while the
     op had written its reason onto the bench's own observation. Measured on a real kernel, the
     cause is ORDER. `station.air.ls` returns a Set's members in the store's order — hash order,
     `s18, s17, s39, s9, s28, …` for rows written s0…s39 — and trims its `limit` after that walk.
     Every platform reader walked the result "newest last":

       - `run_outcome` walked back from the "newest" row and stopped at the first one older than
         the run, which in hash order is almost always the first one it looked at. Reason dropped.
       - the aired count was `after - before`, two counts over two ARBITRARY 500-row slices. Past
         500 rows a run that aired counted ZERO. The news show has thousands of rows: every run it
         aired was recorded as "aired NOTHING", the effect clock never moved, and on the seed that
         still had D1 the 60-second loop spent the day's pool (09-25 13:36–17:00, ~160 paid runs).

     So this is the incident's root, not a cosmetic field. The rows are now read whole and put in
     time order in ONE place, and a run's outcome is counted from the rows stamped after it began.

GUARD  A continuous workload keeps its cadence through its breaker — stopping a broadcaster is the
     silence the airing ruling forbids. That is right when a retry is free and wrong when every
     retry is paid for. K consecutive runs that SPENT calls and produced nothing now stop the
     workload for real (`spent_without_effect`), whatever its duty; a new build or config re-arms
     it (A35).

     THE ORDER MATTERS. Without D10, the news show — which WAS airing — reads as "spent, aired
     nothing" on every run, and this guard would take a live programme off the air. The last
     section replays exactly that and asserts the guard stays quiet.

Run:  python app/test/workbench_run_outcome_eval.py     (exit 0 = all pass)
"""
import ast
import hashlib
import os
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

from lib.akasha.workbench import wl_state                    # noqa: E402
from lib.akasha.workbench import workload as W               # noqa: E402

_fails = []
PROGRAM = "studio_ai/news_show"
BENCH = "wb:probe"


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _kernel():
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="thesaurus", base_dir=tempfile.mkdtemp(prefix="run_outcome_eval_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "henri",
                           "data": {"user_name": "henri",
                                    "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                "id": "g"}, "local")
    return k


def _air(k, source, aired=1, reason="", program=PROGRAM):
    """One row, written by the application's own recorder — the same op the station turn calls."""
    d = {"name": BENCH[3:], "source": source, "aired": str(aired), "program": program, "turn": "t"}
    if reason:
        d["reason"] = reason
    r = k.dispatch({"jsonrpc": "2.0", "method": "station.air.record",
                    "params": {"session_token": "henri", "data": d}, "id": "a"}, "local")
    assert "result" in r, r


# The declared effect read (group 4, 4.12(b)) — the shape a publishing workload's declaration
# carries. The platform no longer names `station.air.ls`; this FIXTURE names it, as the application's
# own declaration does.
EFFECT_READ = {"op": "station.air.ls", "args": {"name": BENCH[3:], "program": "{key}", "limit": "1000"},
               "rows": "aired", "effect": "aired", "reason": "reason", "at": "at"}
POL = {"workload": PROGRAM, "effect_read": EFFECT_READ,
       "duty": W.DUTY_CONTINUOUS, "effect": W.EFFECT_PUBLISH}


def _run(k, *turns):
    """One driver run: stamp the window, write the run's turns, read the effect exactly as
    `autorun` does — through the declared read, with `since=` the run's start."""
    t0 = time.time()
    time.sleep(0.01)
    for t in turns:
        _air(k, *t)
    return wl_state.run_effect(k, POL, since=t0)


def main():
    print("=" * 78)
    print("A run's outcome is read from that run's record; paid runs that produce nothing stop")
    print("=" * 78)

    print("\n  ── D10 on a REAL kernel: the store does not return rows in time order ──")
    k = _kernel()
    for i in range(40):
        _air(k, "s%d" % i)
    raw = (k.dispatch({"jsonrpc": "2.0", "method": "station.air.ls",
                       "params": {"session_token": "henri",
                                  "data": {"name": BENCH[3:], "program": PROGRAM, "limit": "1000"}},
                       "id": "l"}, "local").get("result") or {}).get("aired") or []
    raw_at = [r["at"] for r in raw]
    # The op's CONTRACT, now that the application fixed its side (`station.air.ls` sorts by time
    # before `limit`, and takes `since=`). This check used to assert the opposite — that the op
    # returned STORE order, `s18, s17, s39, s9, s28, …` — which was D10's cause; it said that when
    # the op was fixed this line would fail and say so, and it did. `_air_rows` still sorts, so a
    # platform running against an older application is right either way.
    check("the op returns rows in TIME order, newest last (its contract since the D10 note)",
          raw_at == sorted(raw_at), "first sources: %s" % [r.get("source") for r in raw[:5]])
    rows = wl_state.effect_rows(k, POL)
    check("the declared effect read is put in time order, newest last — the order every reader "
          "assumes", bool(rows) and [r["at"] for r in rows] == sorted(r["at"] for r in rows)
          and rows[-1]["source"] == "s39", "newest=%s" % (rows[-1].get("source") if rows else None))
    check("…and with no `effect_read` declared there is NO read: a job that succeeded is its "
          "effect", wl_state.effect_rows(k, {"workload": PROGRAM}) is None
          and wl_state.run_effect(k, {"workload": PROGRAM}, time.time()) == (1, ""))

    print("\n  ── D10: the op's reason reaches the run record ──")
    n, why = _run(k, ("sb", 0, "provider_429"))
    check("a run whose turn stood by with `provider_429` reports THAT reason, verbatim",
          (n, why) == (0, "provider_429"), "got %r" % ((n, why),))
    n, why = _run(k, ("sb2", 0, "llm_pool"), ("sb3", 0, "not_said"))
    check("…the NEWEST standby of this run is the one reported", (n, why) == (0, "not_said"),
          "got %r" % ((n, why),))
    n, why = _run(k, ("sb4", 0, ""))
    check("…a turn that gave NO reason is reported empty — never an earlier run's reason, never "
          "an invented one", (n, why) == (0, ""), "got %r" % ((n, why),))
    n, why = _run(k, ("ok", 1, ""))
    check("a run that produced its effect counts it", (n, why) == (1, ""), "got %r" % ((n, why),))

    # O(the run), not O(the history): the outcome read asks the op for rows after the run began.
    _seen = []
    _orig = k.dispatch

    def _spy(payload, *a, **kw):
        if payload.get("method") == "station.air.ls":
            _seen.append(dict(((payload.get("params") or {}).get("data") or {})))
        return _orig(payload, *a, **kw)
    k.dispatch = _spy
    try:
        _run(k, ("spy", 1, ""))
    finally:
        k.dispatch = _orig
    _last = _seen[-1] if _seen else {}
    check("the effect read asks the declared op for ONE RUN'S rows (`since=` the run's start) — "
          "not the whole history", bool(_last.get("since"))
          and _last.get("program") == PROGRAM, str(_last))

    print("\n  ── D10: past 500 rows a real airing still counts (the news show's size) ──")
    for i in range(480):
        _air(k, "bulk%d" % i)
    total = len(wl_state.effect_rows(k, POL) or [])
    n, why = _run(k, ("fresh", 1, ""))
    check("with %d rows on record, ONE airing counts ONE (it counted 0 — the incident)" % total,
          total > 500 and (n, why) == (1, ""), "got %r with %d rows" % ((n, why), total))
    n, why = _run(k, ("sb5", 0, "provider_429"))
    check("…and a standby's reason still arrives with that history behind it",
          (n, why) == (0, "provider_429"), "got %r" % ((n, why),))
    n, why = _run(k, ("a1", 1, ""), ("a2", 1, ""), ("a3", 1, ""))
    check("…and a three-beat run counts three", n == 3, "got %r" % ((n, why),))

    print("\n  ── the guard: a paid run that produced nothing extends a streak ──")
    pol = {"duty": W.DUTY_CONTINUOUS, "effect": W.EFFECT_PUBLISH}
    st = {}
    trips = [wl_state.spent_without_effect(st, pol, 3, False) for _ in range(3)]
    check("K=3 consecutive paid runs with no effect: quiet, quiet, TRIP",
          trips == [False, False, True], str(trips))
    check("…and the streak carries the calls it cost", st.get("spent_no_effect_calls") == 9,
          str(st))
    st = {}
    wl_state.spent_without_effect(st, pol, 3, False)
    wl_state.spent_without_effect(st, pol, 3, False)
    wl_state.spent_without_effect(st, pol, 3, True)            # it aired
    check("a run that PRODUCED its effect ends the streak", "spent_no_effect" not in st, str(st))
    st = {}
    wl_state.spent_without_effect(st, pol, 3, False)
    wl_state.spent_without_effect(st, pol, 3, False)
    wl_state.spent_without_effect(st, pol, 0, False)            # a free failure (a 429 costs nothing)
    check("a run that SPENT NOTHING ends it too — a free retry is what the cadence rule protects",
          "spent_no_effect" not in st, str(st))
    st = {}
    check("a best-effort workload is never counted — its ordinary breaker already stops it",
          not any(wl_state.spent_without_effect(st, {"duty": "wb:duty:best_effort"}, 3, False)
                  for _ in range(10)) and not st, str(st))
    st = {}
    _p5 = dict(pol, on_failure={"spent_without_effect": 5})
    check("a declaration may set its own K (`on_failure.spent_without_effect`)",
          [wl_state.spent_without_effect(st, _p5, 1, False) for _ in range(5)]
          == [False, False, False, False, True])

    print("\n  ── the guard reads each job's spend without racing the settle ──")
    class _Job:
        pass
    j = _Job()
    j.llm_reservation = {"consumed": 3}                        # DONE, settle not yet run
    j.api_calls = 0
    check("before the settle: the reservation's running `consumed` count", wl_state.job_spent(j) == 3)
    j.llm_reservation = None                                   # settled: handle released
    j.api_calls = 3
    check("after the settle: the job's settled `api_calls`", wl_state.job_spent(j) == 3)
    check("no job: nothing spent", wl_state.job_spent(None) == 0)

    print("\n  ── the driver wires it, in the right place ──")
    src = open(os.path.join(ROOT, "lib/akasha/workbench/autorun.py"), encoding="utf-8").read()
    tree = ast.parse(src)
    body = ast.get_source_segment
    check("each job's spend is added to the run's (`_run_spent += wl_state.job_spent(_job)`)",
          "_run_spent += wl_state.job_spent(_job)" in src)
    i_guard = src.find("wl_state.spent_without_effect(")
    i_write = src.find("sc.write_autorun_state(gid, name, state)", i_guard)
    check("the streak is updated BEFORE the state is written, so it survives the process",
          0 < i_guard < i_write)
    trip = src[i_guard:src.find("brk = int(", i_guard)]
    check("a trip goes to manual for real, names the reason, and is surfaced for A35's re-arm",
          "sc.force_manual(gid, name, reason=_why)" in trip
          and "REASON_SPENT_WITHOUT_EFFECT" in trip and "_tripped.add(name)" in trip)
    check("the effect the guard asks about is the one the allowance is charged for — one meaning",
          "run_charges_allowance(pol, _n_effect)" in src[i_guard - 200:i_guard + 300])

    print("\n  ── THE INCIDENT REPLAYED: a live programme with a long history is NOT stopped ──")
    # The news show at its real size, airing every run. Before D10 each of these runs read as
    # "spent 3, aired nothing" and this guard would have tripped on the third. After D10 the
    # effect is seen, the streak never starts, and the programme stays on the air.
    st = {}
    tripped = []
    for i in range(6):
        n, _ = _run(k, ("live%d" % i, 1, ""), ("live%db" % i, 1, ""), ("live%dc" % i, 1, ""))
        tripped.append(wl_state.spent_without_effect(st, pol, 3, n > 0))
    check("six paid runs of a programme with >500 rows, each airing: the guard never trips",
          not any(tripped) and "spent_no_effect" not in st, "trips=%s state=%s" % (tripped, st))
    st = {}
    tripped = []
    for i in range(3):
        n, _ = _run(k, ("dark%d" % i, 0, "not_said"))
        tripped.append(wl_state.spent_without_effect(st, pol, 3, n > 0))
    check("…and the same programme paying for three runs that all stood by IS stopped, on the "
          "third", tripped == [False, False, True], str(tripped))

    print()
    if _fails:
        print("FAILED (%d): %s" % (len(_fails), "; ".join(_fails)))
        sys.exit(1)
    print("RESULT: PASS — the rows are read whole and in time order in one place, so a run's "
          "airings and the op's own stood-by reason come from the rows that run wrote, at any "
          "history size; and K consecutive paid runs without the declared effect stop a "
          "continuous workload by name, while one that is airing is never touched.")
    sys.exit(0)


if __name__ == "__main__":
    main()
