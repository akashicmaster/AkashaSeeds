#!/usr/bin/env python3
"""
Seed-time autonomy §2.3 — the readiness gate + `trigger: boot` + `then:`.

Readiness is DECLARED, not inferred: an auto policy lists the source pools its workflows need
(`requires`); the driver opens the society's `boot` trigger ONLY when every required pool exists AND is
FROZEN. Until then the wait is VISIBLE (a `waiting` action + Health `workloads(… auto=waiting:data …)`), never
a prompt and never a run. Once the pools freeze, the boot run fires on the next tick; a `then:` clause
then schedules recurrence. Both cell shapes.

Run:  python app/test/bench_autorun_ready_eval.py     (exit 0 = all pass)
"""
import hashlib
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from lib.akasha.workbench import autorun
from lib.akasha.workbench import wl_state
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _run(series, shape):
    print(f"\n  ── {shape} ({series}) ──")
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series=series, base_dir=tempfile.mkdtemp(prefix="akasha_rdy_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def d(method, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
        return r if "error" in r else (r.get("result") or {})

    POOL = "source:pool:rdy:frame:v1"
    d("world.genesis", {})
    d("grp.new", {"group_id": "rlab", "admin_id": "admin"})
    d("bench.new", {"name": "rbench", "kind": "research", "group": "rlab"})
    d("society.new", {"group": "rlab", "name": "rsoc", "world": "default",
                      "bench": "rbench", "kind": "cowork"})
    mod = d("cast.new", {"name": "RMod"}).get("cast_id")
    scr = d("cast.new", {"name": "RScr"}).get("cast_id")
    d("society.admit", {"group": "rlab", "name": "rsoc", "cast": mod})
    d("society.admit", {"group": "rlab", "name": "rsoc", "cast": scr})
    d("society.moderator", {"group": "rlab", "name": "rsoc", "cast": mod})
    d("society.responsible", {"group": "rlab", "name": "rsoc", "cast": scr, "kind": "scribe"})
    d("wf.new", {"bench": "rbench"})
    d("wf.write", {"bench": "rbench", "pos": 1,
                   "entry": json.dumps({"method": "research.note",
                                        "params": {"name": "rbench", "text": "ready run"}})})
    policy = {"workflows": ["main"], "requires": [POOL], "trigger": "boot", "then": "interval:0",
              "auto_dispatch": False, "budget": {"runs_per_day": 4, "max_steps": 500, "max_wall_s": 60},
              "on_failure": {"retries": 1, "breaker": 3}, "run_once": False}
    d("society.moderator", {"group": "rlab", "name": "rsoc", "mode": "auto",
                            "policy": json.dumps(policy)})

    # ── the required pool does not exist yet ⇒ the driver WAITS, does not run ──
    acts = autorun.bench_autorun_tick(k)
    a = next((x for x in acts if x.get("society") == "rlab/rsoc"), {})
    check(f"[{shape}] a boot bench WAITS while its required pool is missing (no run)",
          a.get("action") == "waiting" and POOL in (a.get("missing") or []), str(a)[:160])
    # Step 2 §2: the driver's status is a WORKLOAD fact, so it is a record in wl_state and the
    # Health line composes it through the `workload_health_segment` hook. It used to be the kernel
    # attribute `_bench_auto_status` — the heart carrying a field about what a workload was doing.
    check(f"[{shape}] Health shows workloads(… auto=waiting:data …) while waiting",
          wl_state.driver_status(k).startswith("waiting:data")
          and "auto=waiting:data" in wl_state.health_segment(k),
          wl_state.health_segment(k))

    # ── create the pool but DON'T freeze it: still not ready (exists ≠ frozen) ──
    reg = d("source.register", {"provider": "eval", "name": "rdyframe", "rights": "CC0"})
    src = reg.get("source")
    d("source.pool.create", {"name": POOL, "rule": "frame", "source": src})
    d("source.acquire", {"source": src, "rule": "frame", "pool": POOL,
                         "records": [{"id": "a"}, {"id": "b"}], "id_field": "id"})
    acts = autorun.bench_autorun_tick(k)
    a = next((x for x in acts if x.get("society") == "rlab/rsoc"), {})
    check(f"[{shape}] an OPEN (unfrozen) pool is still not ready — the bench keeps waiting",
          a.get("action") == "waiting", str(a)[:140])

    # ── freeze the pool ⇒ readiness opens; the boot run fires on the next tick ──
    d("source.pool.freeze", {"pool": POOL})
    acts = autorun.bench_autorun_tick(k)
    # a tick may append more than one action for a society (the run, then a pick / pick_deferred),
    # so select the RUN action explicitly rather than the first entry.
    a = next((x for x in acts if x.get("society") == "rlab/rsoc" and x.get("action") == "ran"), {})
    check(f"[{shape}] once the pool is FROZEN the boot run fires (a JCL job)",
          a.get("action") == "ran" and a.get("ok") is True and a.get("job_id"), str(a)[:160])

    # ── `then: interval:0` recurs after the boot run (boot_done ⇒ then evaluated) ──
    acts = autorun.bench_autorun_tick(k)
    a = next((x for x in acts if x.get("society") == "rlab/rsoc" and x.get("action") == "ran"), {})
    check(f"[{shape}] after the boot run, `then:` schedules recurrence (ran again)",
          a.get("action") == "ran", str(a)[:140])

    # ── S2-k4 — a sweep pick is NOT taken while a pack is loading. This cell loaded no ontology, so
    # `_relations_ready()` is False (the same "load has settled" gate the boot schedulers use); after a
    # successful run the driver DEFERS the pick rather than materialising/running against a half-loaded
    # graph. Once the relations phase completes (its sentinel present) the deferral is gone. ──
    check(f"[{shape}] S2-k4 relations not ready on a cell that loaded no ontology",
          k._relations_ready() is False)
    acts = autorun.bench_autorun_tick(k)
    defer = next((x for x in acts if x.get("society") == "rlab/rsoc"
                  and x.get("action") == "pick_deferred"), None)
    check(f"[{shape}] S2-k4 the pick is DEFERRED while the ontology load is in progress",
          defer is not None and "load" in str(defer.get("reason", "")), str(defer))
    # mark the relations phase complete → the deferral lifts on the next tick
    _sent = os.path.join(k.base_dir, "central", "sentinels")
    os.makedirs(_sent, exist_ok=True)
    open(os.path.join(_sent, "_relations_all.done"), "w").write("done")
    check(f"[{shape}] S2-k4 once the relations phase is complete, relations read ready",
          k._relations_ready() is True)
    acts = autorun.bench_autorun_tick(k)
    defer2 = next((x for x in acts if x.get("society") == "rlab/rsoc"
                   and x.get("action") == "pick_deferred"), None)
    check(f"[{shape}] S2-k4 with the load settled the pick is no longer deferred", defer2 is None,
          str(defer2))


def main():
    _run("thesaurus", "nucleus cell")
    _run("seeds", "single-store cell")
    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("\nRESULT: PASS — the readiness gate withholds a boot bench's run until every declared "
          "`requires` pool EXISTS and is FROZEN (an OPEN pool still waits), the wait is visible on the "
          "Health line, the boot run fires once the pools freeze, and `then:` schedules the recurrence "
          "— on both cell shapes.")
    sys.exit(0)


if __name__ == "__main__":
    main()
