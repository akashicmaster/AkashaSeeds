#!/usr/bin/env python3
"""
D11 and D12 — a full pool refuses a run CLEANLY, and the refusal lifts when the pool's day turns.

D11  `wf.advance` logged a `job.submit` refusal and dropped it. The cursor moved as if the steps had
     run, the driver saw "no job id", burned its breaker and took the ordinary retry ladder into the
     same full pool, then waited for the next daily window: three programmes dark for most of 09-25.
     Now the refusal is an ANSWER — `{status: refused, reason: llm_pool, retry_at: <day turn>}`,
     the reason as the error's own id, never parsed from a message — and the driver records the run
     with that reason, leaves the breaker and the cursor alone, and tries again at the moment the
     refusing party names.

D12  Headroom went false at the refusal and only a reserve, a settle or a boot set it true again,
     so a key refused once stayed locked at the gate after the pool refilled (476 calls free, gate
     answering `headroom`). The pool's day turn now re-states every key's headroom, through
     admission's own function, before the driver asks any gate.

On a real cell provisioned from the real declarations, through the real driver tick.

Run:  python app/test/workbench_pool_refusal_eval.py     (exit 0 = all pass)
"""
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "test"))
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

_fails = []
KEY = "studio_ai/news_show"


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


class _Cap:
    lines = []


class _LogCap:
    """Collect the driver's log lines, so the eval can read what an operator would read."""
    def __init__(self):
        import logging
        self.lines = []
        cap = self

        class H(logging.Handler):
            def emit(self, rec):
                cap.lines.append(rec.getMessage())
        self.h = H()
        logging.getLogger("Akasha.Kernel").addHandler(self.h)
        logging.getLogger("Akasha.Kernel").setLevel(logging.INFO)


def main():
    print("=" * 78)
    print("D11 / D12 — a full pool refuses cleanly; the pool's day turn lifts the refusal")
    print("=" * 78)
    import workload_conformance_eval as C
    from lib.akasha.workbench import (provision, workload as W, wl_state, autorun, admission,
                                      llm_pool, llm_provider as lp)
    from lib.akasha.api import facts as _facts
    from lib.akasha.concepts.society import SocietyConcept
    from lib.akasha.concepts.workflow import WorkflowConcept

    log = _LogCap()
    # A pool that cannot fit one run of the news show (3 calls), a meter that never paces.
    os.environ["AKASHA_LLM_MISTRAL_CALLS_PER_DAY"] = "2"
    lp._METER.clear(); lp._METER_LOADED = True; lp._NEXT_OK.clear()
    lp._FREE_TIER["mistral"]["min_interval"] = 0.0
    vault = {}
    llm_pool.set_pool_store(lambda kk: vault.get(kk), lambda kk, d: vault.__setitem__(kk, dict(d)))
    llm_pool._MEM.clear()

    k = C._cell(_Cap())
    provision.provision_workloads(k)
    decl = W.by_key(k, KEY)
    gid, space = W.society_of(decl)
    bench = W.bench_slug(decl)
    branch = W.branch_of(decl)

    # The ネタ帖 has one item, so a run that IS admitted has something to air.
    def _d(method, data, who="admin"):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": who, "data": data}, "id": "x"}, "local")
        return r.get("result") if "result" in r else {"__error__": r.get("error")}
    _d("kernel.memory.define", {"name": "neta:item:eval1", "scope": "universal",
                                "description": "An AI lab released an open model today."})
    _d("set.add", {"name": (decl.get("pins") or {}).get("item_set") or "neta:studio_ai:news_show:src",
                   "id": "neta:item:eval1"})

    sc = SocietyConcept(k.manager.get_session("system.broadcaster"))
    wf = WorkflowConcept(k.manager.get_session("admin"))

    def _arm():
        st = dict((sc.read_autorun(gid, space) or {}).get("state") or {})
        for kk in ("last_run", "retry_at", "retry_count"):
            st.pop(kk, None)
        st["boot_pending"] = True
        sc.write_autorun_state(gid, space, st)

    def _state():
        return dict((sc.read_autorun(gid, space) or {}).get("state") or {})

    def _cursor():
        # Bound to the bench's own engine first, as `society.run` binds before it reads — unbound,
        # this read a different store and saw 0 whatever happened, so a "cursor unchanged" check
        # built on it proved nothing (the first version of this eval did exactly that).
        wf._bind(wf._bench_gid(bench))
        return int(wf._cursors(bench).get(branch, 0))

    _real_gen, _real_last = lp.generate, wl_state.last_effect_at
    lp.generate = lambda *a, **kw: "Here is the news, in my own words."
    wl_state.last_effect_at = lambda *_a, **_kw: 0.0       # the fresh gate is not under test
    try:
        print("\n  ── D11: a run the pool cannot fit ──")
        _arm()
        before = _state()
        cur0 = _cursor()
        now = time.time()
        acts = [a for a in autorun.bench_autorun_tick(k, now=now)
                if a.get("society") == "%s/%s" % (gid, space)]
        st = _state()
        act = acts[0] if acts else {}
        check("the run is recorded NOT ok, with the refusal as its reason",
              act.get("ok") is False and "refused" in str(act.get("reason") or ""),
              str(act)[:160])
        check("…and the operator's line names the reason by its ID, `llm_pool`",
              any("status=refused reason=llm_pool" in l for l in log.lines),
              [l for l in log.lines if "status=refused" in l][-1:] or "no line")
        check("…and the run is recorded as stood by with that id",
              any("run stood by workload=%s/%s reason=llm_pool" % (gid, space) in l
                  for l in log.lines))
        check("the breaker is UNCHANGED (nothing is broken — the run was never admitted)",
              int(st.get("breaker", 0)) == int(before.get("breaker", 0)),
              "before=%s after=%s" % (before.get("breaker", 0), st.get("breaker", 0)))
        check("the workflow cursor is UNCHANGED (those steps did not run)",
              _cursor() == cur0, "before=%s after=%s" % (cur0, _cursor()))
        check("`retry_at` is the POOL's day turn — the moment the refusing party names",
              abs(float(st.get("retry_at") or 0) - llm_pool.next_day_turn(now)) < 2,
              "retry_at=%s turn=%s" % (st.get("retry_at"), llm_pool.next_day_turn(now)))
        check("…not the ordinary ladder (no retry_count was spent against a full pool)",
              "retry_count" not in st, str(st.get("retry_count")))
        _lr = wl_state.last_run(k, KEY)
        check("the PLATFORM'S run record carries the refusal: `workload.status.last` = "
              "{ok: false, reason: llm_pool, effect_count: 0}",
              _lr.get("ok") is False and _lr.get("reason") == "llm_pool"
              and _lr.get("effect_count") == 0
              and wl_state.status(k, KEY).get("last") == _lr, str(_lr))
        src = open(os.path.join(ROOT, "lib/akasha/workbench/autorun.py"), encoding="utf-8").read()
        check("the driver classifies by the reason's ID, never by a substring of a message",
              '"32005" in str(reason)' not in src and '"LLM pool" in str(reason)' not in src
              and "wl_state.is_transient(_refused_id)" in src)

        print("\n  ── D12: the refusal locked the gate; the pool's day turn unlocks it ──")
        check("after the refusal the gate answers `headroom` for the key",
              not _facts.has(k, _facts.HEADROOM, KEY)
              and (wl_state.status(k, KEY).get("gate") or {}).get("run") == "headroom",
              str(wl_state.status(k, KEY).get("gate")))
        admission.observe_day_turn(k)                       # the tick's first act: records today
        _today = llm_pool.day()
        _tomorrow = time.strftime("%Y-%m-%d", time.gmtime(llm_pool.next_day_turn() + 60))
        _real_day = llm_pool.day
        llm_pool.day = lambda: _tomorrow                    # the pool's day turns
        os.environ["AKASHA_LLM_MISTRAL_CALLS_PER_DAY"] = "500"
        try:
            turned = admission.observe_day_turn(k)
            check("the day turn is SEEN (%s → %s) and every key's headroom re-stated" % (_today, _tomorrow),
                  turned and any("pool day turned" in l for l in log.lines))
            check("with NO RUN in between, `workload.status` answers `gate.run = ok`",
                  (wl_state.status(k, KEY).get("gate") or {}).get("run") == "ok",
                  str(wl_state.status(k, KEY).get("gate")))
            check("the driver tick observes the day turn BEFORE it asks any gate",
                  src.find("_adm.observe_day_turn(kernel)") < src.find("actions = []")
                  and src.find("_adm.observe_day_turn(kernel)") > 0)

            print("\n  ── after the turn, the same programme runs and airs ──")
            def _aired():
                # The APPLICATION's own rows — an eval may read them; the platform no longer does.
                r = k.dispatch({"jsonrpc": "2.0", "method": "station.air.ls",
                                "params": {"client_id": "admin",
                                           "data": {"name": bench[3:] if bench.startswith("wb:")
                                                    else bench, "program": KEY, "limit": "100000"}},
                                "id": "n"}, "internal")
                return sum(1 for x in ((r.get("result") or {}).get("aired") or []) if x.get("aired"))
            n0 = _aired()
            acts2 = [a for a in autorun.bench_autorun_tick(k, now=float(st["retry_at"]) + 1)
                     if a.get("society") == "%s/%s" % (gid, space)]
            n1 = _aired()
            check("the programme is admitted and its run ends ok",
                  bool(acts2) and acts2[0].get("ok") is True, str(acts2)[:160])
            check("…and it AIRS (%d turn(s) on the application's record)" % (n1 - n0), n1 > n0)
            _lr2 = wl_state.last_run(k, KEY)
            check("…and the platform's run record now says ok, with its effect counted",
                  _lr2.get("ok") is True and int(_lr2.get("effect_count") or 0) >= 1, str(_lr2))
            check("…and the cursor has moved now that the steps ran (%d → %d)" % (cur0, _cursor()),
                  _cursor() > cur0)
        finally:
            llm_pool.day = _real_day
    finally:
        lp.generate, wl_state.last_effect_at = _real_gen, _real_last

    print()
    if _fails:
        print("FAILED (%d): %s" % (len(_fails), "; ".join(_fails)))
        sys.exit(1)
    print("RESULT: PASS — a pool refusal is returned as data, recorded with its id, leaves the "
          "breaker and the cursor alone and waits for the pool's day turn; the day turn re-states "
          "headroom for every key, and the same programme then runs and airs.")
    sys.exit(0)


if __name__ == "__main__":
    main()
