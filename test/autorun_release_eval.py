#!/usr/bin/env python3
"""
A workload the ontology load held runs on the first driver tick after the hold lifts.

Designer, 11 October: "the instant the hold lifts the workload becomes eligible on the very next
driver tick and runs. 'Load complete' is itself the trigger. It must not wait for its next scheduled
time." Before v1.3.2 a released boot-triggered workload went through the boot run's `fresh` skip —
a `daily:` programme that had aired within the day (its interval is a day) was skipped as `fresh`
and stayed silent until its next HH:MM.

This drives the REAL `bench_autorun_tick` on a real cell. What it stands in for is only the edge:
the society store (three auto societies, their policies and states), the load's hold answer
(`wl_state.onto_hold`), the source gate (none missing), the last-effect clock (an hour ago), and
the run itself — `society.run` is recorded (the airing) and stopped there.

  R1 while the FIRST load holds everything, nothing runs
  R2 the tick after the first load releases its core, the two released workloads run — the daily one
     too, which aired an hour ago and is not due by its clock (not `fresh`, not its next slot);
     the one still held by a pack in flight does not
  R3 the tick after the whole load ends, that last one runs
  R4 a later tick, with nothing held, runs nothing more: the release was one owed run, not a loop
  F2 `derive_bench_tripped` reads every society though the first two cannot be read

Run:  python test/autorun_release_eval.py     (exit 0 = all pass)
"""
import hashlib
import os
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def main():
    print("=" * 78)
    print("A workload the load held runs on the first tick after the hold lifts")
    print("=" * 78)
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_release_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin",
                                    "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                "id": "g"}, "local")
    time.sleep(0.5)

    from lib.akasha.workbench import autorun, wl_state
    from lib.akasha.workbench import workload as W
    from lib.akasha.ontology import loader as L
    from lib.akasha.api import schedule as S
    import lib.akasha.concepts.society as society_mod

    now0 = time.time()
    hh = time.gmtime(now0 + 6 * 3600)                    # the daily slot: six hours from now
    daily = "daily:%02d:%02d" % (hh.tm_hour, hh.tm_min)
    pols = {
        "t/daily":    {"trigger": "boot", "then": daily, "workflows": ["w"], "workload": "b/daily",
                       "budget": {"runs_per_day": 4}},
        "t/interval": {"trigger": "boot", "then": "interval:1800", "workflows": ["w"],
                       "workload": "b/interval", "budget": {"runs_per_day": 48}},
        "t/touched":  {"trigger": "boot", "then": daily, "workflows": ["w"], "workload": "b/touched",
                       "budget": {"runs_per_day": 4}},
    }
    states = {key: {"boot_id": "an-earlier-boot", "day": time.strftime("%Y-%m-%d", time.gmtime()),
                    "runs_today": 1, "last_run": now0 - 3600} for key in pols}

    class _FakeSociety:
        def __init__(self, *_a, **_k):
            pass

        def list_auto_societies(self):
            return [{"gid": key.split("/")[0], "name": key.split("/")[1]} for key in pols]

        def read_autorun(self, gid, name):
            key = "%s/%s" % (gid, name)
            if key in unreadable:
                raise PermissionError("Not a member of group '%s'." % gid)
            return {"mode": "auto", "policy": dict(pols.get(key) or {}),
                    "state": dict(states.get(key) or {}), "bench": None, "mode_by": None}

        def write_autorun_state(self, gid, name, state):
            states["%s/%s" % (gid, name)] = dict(state)

        def force_manual(self, *_a, **_k):
            pass

    unreadable = set()
    society_mod.SocietyConcept = _FakeSociety
    autorun.requires_missing = lambda *_a, **_k: []
    wl_state.last_effect_at = lambda *_a, **_k: now0 - 3600          # aired an hour ago
    wl_state.note = lambda *_a, **_k: None
    autorun._W.for_society = lambda *_a, **_k: None
    touched_held = {"on": True}
    _real_hold = wl_state.onto_hold

    def _hold(kern, pol):
        if pol.get("workload") == "b/touched" and touched_held["on"]:
            return {"reason": "onto_load", "first": False, "packs": ["deep"], "names": ["x"]}
        return {}
    wl_state.onto_hold = _hold

    aired = []

    class _Picked(Exception):
        pass

    _dispatch = k.dispatch

    def _dispatch_spy(payload, *a, **kw):
        if payload.get("method") == "society.run":
            d = (payload.get("params") or {}).get("data") or {}
            key = "%s/%s" % (d.get("group"), d.get("name"))
            aired.append(key)
            states[key]["last_run"] = time.time()          # what the airing's charge stamps
            raise _Picked("aired")                         # the run itself is not under test
        return _dispatch(payload, *a, **kw)
    k.dispatch = _dispatch_spy
    k._bench_tripped = set()

    def tick():
        aired.clear()
        autorun.bench_autorun_tick(k, now=time.time())
        return sorted(aired)

    # R1 — the first load
    S.mark_running(k, "ontology.loaded")
    L.publish_in_flight(k, first=True, packs=[])
    got = tick()
    check("R1 during the first load nothing runs", got == [], str(got))

    # R2 — the core is in: the first load becomes a scoped one; `t/touched` reads a pack in flight
    L.publish_in_flight(k, first=False, packs=["deep"])
    got = tick()
    check("R2 the tick after the release runs both released workloads",
          got == ["t/daily", "t/interval"], str(got))
    check("…the daily one although it aired an hour ago and its slot is six hours away (no "
          "`fresh` skip, no wait for %s)" % daily, "t/daily" in got)
    check("…and not the one a pack still in flight holds", "t/touched" not in got)

    # R3 — the load ends
    touched_held["on"] = False
    L.publish_in_flight(k, clear=True)
    S.open_gate(k, "ontology.loaded")
    got = tick()
    check("R3 the tick after the load ends runs the last held workload", got == ["t/touched"], str(got))

    # R4 — nothing owed any more
    for key in states:                                    # as the runs would have left them
        states[key].update({"boot_pending": False, "last_run": time.time()})
    got = tick()
    check("R4 a later tick runs nothing more (one owed run, not a loop)", got == [], str(got))

    # F2 — the tripped derive reads past an unreadable society
    wl_state.onto_hold = _real_hold
    decls = [{"society": key} for key in pols]
    W.declarations = lambda kern: list(decls)
    W.problems = lambda d: []
    W.society_of = lambda d: tuple(d["society"].split("/"))
    unreadable |= {"t/daily", "t/interval"}
    states["t/touched"]["_"] = 1
    pols_tripped = {"t/touched"}

    class _TrippedSociety(_FakeSociety):
        def read_autorun(self, gid, name):
            r = _FakeSociety.read_autorun(self, gid, name)
            if "%s/%s" % (gid, name) in pols_tripped:
                r.update({"mode": "manual", "mode_by": "breaker"})
            return r
    society_mod.SocietyConcept = _TrippedSociety
    tripped = autorun.derive_bench_tripped(k)
    check("F2 the tripped derive skips the two unreadable societies and still reads the third",
          tripped == {"touched"}, str(tripped))

    print()
    if _fails:
        print(f"RESULT: FAIL — {len(_fails)} check(s): {_fails}")
        return 1
    print("RESULT: PASS — a workload the load held runs on the first tick after the hold lifts (not "
          "its next slot, not skipped as fresh), once; the tripped derive reads every society it can.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
