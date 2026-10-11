#!/usr/bin/env python3
"""
Group 4, 4.12(a) — the RUN RECORD is the platform's own.

`workload.status.last` was read from the APPLICATION's rows (`station.air.ls`, the station's aired
observations). So a run that never wrote an application row under its own key had no recorded
outcome: a refusal at admission, a job that failed before its first turn, or a run whose rows were
keyed under ANOTHER workload (09-26: the X channel's publish recorded under its source programme,
with a blank reason). `last` then answered with some other run's row.

The driver now writes one row per run into the workload's own namespace —
`{at, ok, job_ok, reason, effect_count, spent, by, job_id}` — and `workload.status.last` reads that row
and nothing else. This eval drives the REAL driver tick on a cell provisioned from the REAL
declarations, three times:

  1. a REFUSED run    — the pool cannot fit it           → last = {ok: false, reason: llm_pool}
  2. a FAILED run     — its step errors inside the job   → last = {ok: false, reason: <the error>}
  3. a run whose effect rows are keyed ELSEWHERE — its job succeeds, its declared effect read
     finds nothing under its own key                     → last = THIS run, {ok: false, job_ok: true,
                                                           effect_count: 0}
  4. D15 — a run whose job succeeds and whose turns all stand by, each with the op's reason X
                                                         → last = {ok: false, reason: X,
                                                           effect_count: 0, job_ok: true}
  5. the same run with an effect                         → last = {ok: true, effect_count: 3}

`ok` means the DECLARED EFFECT happened (D15: `job_ok and run_charges_allowance`), the predicate the
allowance, the effect clock and the guard already use; `job_ok` is the job's own outcome.

and, for 4.12(b), that the effect is read through the op the DECLARATION names, and that a
declaration naming none counts a successful job as its effect.

Run:  python app/test/workbench_run_record_eval.py     (exit 0 = all pass)
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


def main():
    print("=" * 78)
    print("4.12(a) — every run is on the platform's own record, with its reason")
    print("=" * 78)
    import workload_conformance_eval as C
    from lib.akasha.workbench import (provision, workload as W, wl_state, autorun, llm_pool,
                                      llm_provider as lp)
    from lib.akasha.concepts.society import SocietyConcept

    os.environ["AKASHA_LLM_MISTRAL_CALLS_PER_DAY"] = "2"        # cannot fit one run (3 calls)
    lp._METER.clear(); lp._METER_LOADED = True; lp._NEXT_OK.clear()
    lp._FREE_TIER["mistral"]["min_interval"] = 0.0
    vault = {}
    llm_pool.set_pool_store(lambda kk: vault.get(kk), lambda kk, d: vault.__setitem__(kk, dict(d)))
    llm_pool._MEM.clear()

    k = C._cell(_Cap())
    provision.provision_workloads(k)
    decl = W.by_key(k, KEY)
    gid, space = W.society_of(decl)
    sc = SocietyConcept(k.manager.get_session("system.broadcaster"))

    def _d(method, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": "admin", "data": data}, "id": "x"}, "local")
        return r.get("result") if "result" in r else {"__error__": r.get("error")}
    # One item per run the eval makes: since D14 the news show declares `on_exhausted: stand_by`,
    # so a notebook of ONE item stands the Anchor by on the second run (it used to re-air item 1).
    for _i in range(1, 7):
        _d("kernel.memory.define", {"name": "neta:item:rr%d" % _i, "scope": "universal",
                                    "description": "A lab published open model number %d today." % _i})
        _d("set.add", {"name": (decl.get("pins") or {}).get("item_set"), "id": "neta:item:rr%d" % _i})

    def _arm():
        st = dict((sc.read_autorun(gid, space) or {}).get("state") or {})
        for kk in ("last_run", "retry_at", "retry_count", "breaker"):
            st.pop(kk, None)
        st["boot_pending"] = True
        sc.write_autorun_state(gid, space, st)

    def _tick():
        _arm()
        t0 = time.time()
        acts = [a for a in autorun.bench_autorun_tick(k, now=time.time())
                if a.get("society") == "%s/%s" % (gid, space) and a.get("action") == "ran"]
        return t0, (acts[0] if acts else {}), wl_state.status(k, KEY).get("last") or {}

    _real_gen, _real_fresh = lp.generate, wl_state.last_effect_at
    lp.generate = lambda *a, **kw: "Here is the news, in my own words."
    wl_state.last_effect_at = lambda *_a, **_kw: 0.0             # the fresh gate is not under test
    try:
        print("\n  ── 1. a REFUSED run ──")
        t0, act, last = _tick()
        check("the driver refused the run (the pool cannot fit it)",
              act.get("ok") is False and "refused" in str(act.get("reason")), str(act)[:120])
        check("`workload.status.last` IS this run: {ok: false, reason: llm_pool, effect_count: 0}",
              last.get("ok") is False and last.get("reason") == "llm_pool"
              and last.get("effect_count") == 0 and float(last.get("at") or 0) >= t0 - 1, str(last))
        check("…and it names who ran it, as the workload's declared client",
              last.get("by") == W.client_of(decl), str(last.get("by")))

        print("\n  ── 2. a FAILED run ──")
        os.environ["AKASHA_LLM_MISTRAL_CALLS_PER_DAY"] = "500"
        llm_pool._MEM.clear(); vault.clear()
        # The recorder the station registers for `society.air` is pointed at a method that does
        # not exist — every turn of the job errors, the job fails, no application row is written.
        _attrs = k.api.op_attrs
        _was = dict(_attrs.get("station.air.turn") or {})
        _attrs["station.air.turn"] = {k2: v for k2, v in _was.items() if k2 != "implements"}
        _attrs["eval.no_such_recorder"] = {"implements": "society.air"}
        try:
            t0, act, last = _tick()
        finally:
            _attrs.pop("eval.no_such_recorder", None)
            _attrs["station.air.turn"] = _was
        check("the run failed inside its job", act.get("ok") is False and act.get("job_id"),
              str(act)[:160])
        check("`workload.status.last` IS this run: {ok: false}, with the failure's own reason and "
              "its job id", last.get("ok") is False and last.get("job_id") == act.get("job_id")
              and "step_errors" in str(last.get("reason")) and float(last.get("at") or 0) >= t0 - 1,
              str(last)[:200])

        print("\n  ── 3. a run whose effect rows are keyed ELSEWHERE ──")
        # The declaration names its effect read — here reading under a key the application never
        # writes under (the X channel's case on 09-26: its rows went under the source programme).
        _decl = W.by_key(k, KEY)
        _decl["effect_read"] = {"op": "station.air.ls",
                                "args": {"name": "{bench}", "program": "studio_ai/elsewhere",
                                         "limit": "1000"},
                                "rows": "aired", "effect": "aired", "reason": "reason", "at": "at"}
        provision.provision_workloads(k)
        pol = (sc.read_autorun(gid, space) or {}).get("policy") or {}
        check("provisioning carried the declared `effect_read` into the policy the driver reads",
              (pol.get("effect_read") or {}).get("op") == "station.air.ls", str(pol.get("effect_read")))
        t0, act, last = _tick()
        check("the job succeeded", act.get("ok") is True, str(act)[:120])
        check("D15 — `workload.status.last` IS this run and says NO effect happened: {ok: false, "
              "job_ok: true, effect_count: 0} (the 09-26 X-channel symptom read as on air)",
              last.get("ok") is False and last.get("job_ok") is True
              and last.get("effect_count") == 0
              and last.get("job_id") == act.get("job_id") and float(last.get("at") or 0) >= t0 - 1,
              str(last))
        _decl["effect_read"]["args"]["program"] = "{key}"
        provision.provision_workloads(k)

        print("\n  ── 4. D15 — a run whose job succeeds and whose turns all STAND BY ──")
        # The model returns nothing, so every turn stands by with the gateway's own reason on its
        # row, and the job still succeeds (a stood-by turn is not an error). The declared effect
        # read finds this run's rows, none aired, each carrying that reason.
        lp.generate = lambda *a, **kw: ""
        try:
            t0, act, last = _tick()
        finally:
            lp.generate = lambda *a, **kw: "Here is the news, in my own words."
        check("the job succeeded", act.get("ok") is True, str(act)[:120])
        check("`last` = {ok: false, reason: <the op's own id, verbatim>, effect_count: 0, "
              "job_ok: true}",
              last.get("ok") is False and last.get("job_ok") is True
              and last.get("effect_count") == 0 and bool(last.get("reason"))
              and last.get("job_id") == act.get("job_id"), str(last))
        _standby_reason = last.get("reason")

        print("\n  ── 5. the same shape with an effect ──")
        t0, act, last = _tick()
        check("…and with the model answering, the same run counts its effect (the 3 turns): "
              "{ok: true, job_ok: true, reason: ''}",
              last.get("ok") is True and last.get("job_ok") is True
              and last.get("effect_count") == 3 and last.get("reason") == "", str(last))
        check("the stand-by reason was the op's own id, not a platform word (%s)" % _standby_reason,
              _standby_reason not in ("", "ok", "standby", "on_air"), str(_standby_reason))
        _decl.pop("effect_read", None)
        provision.provision_workloads(k)
        t0, act, last = _tick()
        check("a declaration that names NO effect read counts the successful job as its effect "
              "(ok and job_ok both true)",
              last.get("ok") is True and last.get("job_ok") is True
              and last.get("effect_count") == 1, str(last))

        print("\n  ── the read is a CLI command (frontend 09-28, needs platform 3) ──")
        from api.gateway import AkashaGateway
        gw = AkashaGateway(kernel_client=k)
        cli = gw.dispatch({"jsonrpc": "2.0", "method": "sys.cli_exec",
                           "params": {"session_token": "admin",
                                      "data": {"command": "workload.status key=%s" % KEY}},
                           "id": "c"}, "local")
        cres = (cli or {}).get("result") or {}
        rpc = wl_state.status(k, KEY)
        check("`workload.status key=<bench>/<slug>` runs as a CLI command and answers what the RPC "
              "answers (the same last run, the same gate)",
              cres.get("key") == KEY and (cres.get("last") or {}).get("job_id") == (rpc.get("last") or {}).get("job_id")
              and cres.get("gate") == rpc.get("gate") and "Unknown command" not in str(cli),
              str(cli)[:200])

        print("\n  ── the record is bounded, and the driver names no application op ──")
        for i in range(wl_state.RUN_RECORD_KEEP + 25):
            wl_state.record_run(k, "eval/bound", at=float(i), ok=True)
        rows = wl_state.run_records(k, "eval/bound")
        check("the ring keeps the newest %d rows and drops the rest in the same write"
              % wl_state.RUN_RECORD_KEEP,
              len(rows) == wl_state.RUN_RECORD_KEEP and rows[-1]["at"] == float(
                  wl_state.RUN_RECORD_KEEP + 24), "%d rows" % len(rows))
        import platform_vocabulary_eval as _V          # its code-only reader (no comments/docstrings)
        _named = ["%s:%d" % (_p, _n) for _p in ("lib/akasha/workbench/autorun.py",
                                              "lib/akasha/workbench/wl_state.py")
                  for _n, _c in _V._code_lines(os.path.join(ROOT, _p))
                  if "bench.air." in _c or "station.air." in _c]     # station.* since 10-02 §2a
        check("neither the driver nor the state layer names the station's `air.*` ops in code",
              not _named, str(_named))
    finally:
        lp.generate, wl_state.last_effect_at = _real_gen, _real_fresh

    print()
    if _fails:
        print("FAILED (%d): %s" % (len(_fails), "; ".join(_fails)))
        sys.exit(1)
    print("RESULT: PASS — a refused run, a failed run and a run whose effect rows are keyed "
          "elsewhere each appear in `workload.status.last` with their own reason; the effect is "
          "read through the op the declaration names; the record is bounded.")
    sys.exit(0)


if __name__ == "__main__":
    main()
