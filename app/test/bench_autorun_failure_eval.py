#!/usr/bin/env python3
"""
A28 — the auto-run driver surfaces failures and retries them.

The v18 box symptom: the first PLANTS run failed in 107 ms and NOTHING said why. Two bugs:
  • society.run could not resolve a PUBLIC bench (bench= empty → no job id → status=failed), and
  • the driver logged the failure only at DEBUG (the WARNING path was `status==refused` only).
This eval proves the fixes on both cell shapes:
  1. a public bench + group society → the driver's run RESOLVES the bench and runs (ok);
  2. a run whose block always fails is reported with a reason and RETRIED within a bounded back-off
     (on_failure.retries), before the breaker trips it to manual.

Run:  python app/test/bench_autorun_failure_eval.py     (exit 0 = all pass)
"""
import hashlib
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from lib.akasha.workbench import autorun
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
    k = KernelDispatcher(series=series, base_dir=tempfile.mkdtemp(prefix="akasha_arf_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def d(method, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
        return r if "error" in r else (r.get("result") or {})

    from lib.akasha.concepts.society import SocietyConcept

    # ── 1. a PUBLIC bench (nucleus) + group society; the driver resolves + runs it ──
    d("world.genesis", {})
    d("grp.new", {"group_id": "plab", "admin_id": "admin"})
    d("bench.new", {"name": "pubb", "kind": "research"})          # public: no group=
    d("society.new", {"group": "plab", "name": "psoc", "world": "default", "bench": "pubb", "kind": "cowork"})
    mod = d("cast.new", {"name": "PMod"}).get("cast_id")
    scr = d("cast.new", {"name": "PScr"}).get("cast_id")
    d("society.admit", {"group": "plab", "name": "psoc", "cast": mod})
    d("society.admit", {"group": "plab", "name": "psoc", "cast": scr})
    d("society.moderator", {"group": "plab", "name": "psoc", "cast": mod})
    d("society.responsible", {"group": "plab", "name": "psoc", "cast": scr, "kind": "scribe"})
    d("wf.new", {"bench": "pubb"})
    d("wf.write", {"bench": "pubb", "pos": 1,
                   "entry": json.dumps({"method": "research.note", "params": {"name": "pubb", "text": "ok"}})})
    # simulate the box: a society whose meta lacks bench_name (created pre-fix)
    sc = SocietyConcept(k.manager.get_session("admin"))
    ge = sc._group_engine("plab"); sk = sc._society_key(ge, "plab", "psoc")
    sm = sc._society_meta(ge, sk); sm.pop("bench_name", None); sc._write_society_meta(ge, sk, sm)
    pol = {"workflows": ["main"], "trigger": "boot", "budget": {"runs_per_day": 9, "max_wall_s": 60},
           "on_failure": {"retries": 1, "breaker": 3}, "run_once": False}
    d("society.moderator", {"group": "plab", "name": "psoc", "mode": "auto", "policy": json.dumps(pol)})
    acts = autorun.bench_autorun_tick(k)
    a = next((x for x in acts if x.get("society") == "plab/psoc"), {})
    check(f"[{shape}] the driver RESOLVES + runs a public bench (no silent no-job-id failure)",
          a.get("action") == "ran" and a.get("ok") is True and a.get("job_id"), str(a)[:180])

    # ── 2. a failing block is reported with a reason and RETRIED within the back-off ──
    d("grp.new", {"group_id": "flab", "admin_id": "admin"})
    d("bench.new", {"name": "fbench", "kind": "research"})        # public
    d("society.new", {"group": "flab", "name": "fsoc", "world": "default", "bench": "fbench", "kind": "cowork"})
    fm = d("cast.new", {"name": "FMod"}).get("cast_id")
    fs = d("cast.new", {"name": "FScr"}).get("cast_id")
    d("society.admit", {"group": "flab", "name": "fsoc", "cast": fm})
    d("society.admit", {"group": "flab", "name": "fsoc", "cast": fs})
    d("society.moderator", {"group": "flab", "name": "fsoc", "cast": fm})
    d("society.responsible", {"group": "flab", "name": "fsoc", "cast": fs, "kind": "scribe"})
    d("wf.new", {"bench": "fbench"})
    # a structured entry that always raises (research.hyp.new with no text=)
    d("wf.write", {"bench": "fbench", "pos": 1,
                   "entry": json.dumps({"method": "research.hyp.new", "params": {"name": "fbench"}})})
    fpol = {"workflows": ["main"], "trigger": "boot", "budget": {"runs_per_day": 9, "max_wall_s": 60},
            "on_failure": {"retries": 1, "breaker": 3}, "run_once": False}
    d("society.moderator", {"group": "flab", "name": "fsoc", "mode": "auto", "policy": json.dumps(fpol)})

    now = 1_000_000.0
    acts = autorun.bench_autorun_tick(k, now)
    a = next((x for x in acts if x.get("society") == "flab/fsoc"), {})
    check(f"[{shape}] a failed run reports a non-empty reason (not a silent failure)",
          a.get("action") == "ran" and a.get("ok") is False and a.get("reason"), str(a)[:180])
    st = sc.read_autorun("flab", "fsoc").get("state") or {}
    check(f"[{shape}] a retry is armed after the failure (retry_at in the near future, bounded)",
          float(st.get("retry_at") or 0) > now and int(st.get("retry_count", 0)) == 1,
          f"retry_at-now={float(st.get('retry_at', 0)) - now} rc={st.get('retry_count')}")

    # before the back-off elapses, the run does NOT re-fire
    acts = autorun.bench_autorun_tick(k, now + 60)          # 1 min later, back-off is 10 min
    a = next((x for x in acts if x.get("society") == "flab/fsoc"), {})
    check(f"[{shape}] the retry does not fire before its back-off elapses",
          a.get("action") != "ran", str(a)[:120])

    # after the back-off, the retry fires (and, retries now exhausted, no further retry is armed)
    acts = autorun.bench_autorun_tick(k, now + 700)         # >10 min later
    a = next((x for x in acts if x.get("society") == "flab/fsoc"), {})
    st = sc.read_autorun("flab", "fsoc").get("state") or {}
    check(f"[{shape}] the retry FIRES after the back-off, then no more retries are armed",
          a.get("action") == "ran" and a.get("ok") is False and not st.get("retry_at"),
          f"action={a.get('action')} retry_at={st.get('retry_at')}")


def main():
    _run("thesaurus", "nucleus cell")
    _run("seeds", "single-store cell")
    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("\nRESULT: PASS — the driver resolves + runs a PUBLIC bench (no silent no-job-id failure), "
          "reports a failed run with a reason, and retries it within a bounded back-off (on_failure."
          "retries) before the breaker trips — on both cell shapes.")
    sys.exit(0)


if __name__ == "__main__":
    main()
