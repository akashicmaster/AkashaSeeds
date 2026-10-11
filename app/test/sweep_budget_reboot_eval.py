#!/usr/bin/env python3
"""
B1-c — the sweep DRIVER's budget is durable: Set-free counters on the sweep_def atom (spent_today /
spent_total / day) survive a process restart (they live in the nucleus, not in memory), and spent_today
resets on a new bench day (UTC date) while spent_total does NOT.

The auto-run driver spends one budget unit per branch it picks (`SweepConcept.driver_pick`). Because the
counters ride the sweep_def atom in the durable store, a restart (a fresh KernelDispatcher on the SAME
base_dir) reads the same spend; the driver never re-spends a day's budget just because the process
bounced (memory discipline R5 — a bounded write path whose state is durable, not per-process).

This eval drives it on BOTH cell shapes:
  • spend the per_day budget (2 picks), then a third pick is budget_exhausted;
  • RESTART (new kernel, same base_dir) — spent_total / spent_today / day persist;
  • a new bench day resets spent_today (a pick is allowed again) but keeps spent_total (the total cap
    still counts every pick ever made).

Run:  python test/sweep_budget_reboot_eval.py     (exit 0 = all pass)
"""
import hashlib
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []
BENCH = "plants-vision"          # the template resolver looks under config/<bench>/templates/
SWEEP = "budg1"


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _kernel(series, base):
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    return KernelDispatcher(series=series, base_dir=base)


def _run(series, shape):
    print(f"\n  ── {shape} ({series}) ──")
    base = tempfile.mkdtemp(prefix="akasha_sbr_")
    k = _kernel(series, base)
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def a(kk, method, data):
        r = kk.dispatch({"jsonrpc": "2.0", "method": method,
                         "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
        return r if "error" in r else (r.get("result") or {})

    # a bench + workflow + a sweep whose grid has ≥2 materialisable conditions, budget per_day=2 total=5
    a(k, "world.genesis", {})
    a(k, "bench.new", {"name": BENCH, "kind": "learning"})
    a(k, "wf.new", {"bench": BENCH})
    a(k, "sweep.def", {"bench": BENCH, "name": SWEEP,
                       "grid": '{"head":["logreg","mlp"],"split":["0.8","0.7"],"seed":["1"]}',
                       "template": "learn_observe", "fixed": "space=color",
                       "budget": '{"per_day":2,"total":5}'})

    from lib.akasha.concepts.sweep import SweepConcept
    sw = SweepConcept(k.manager.get_session("admin"))
    # spend the per_day budget: two picks (materialise-then-pick each), then the third is exhausted
    p1 = sw.driver_pick(bench=BENCH, name=SWEEP)
    p2 = sw.driver_pick(bench=BENCH, name=SWEEP)
    p3 = sw.driver_pick(bench=BENCH, name=SWEEP)
    check(f"[{shape}] two picks spend the per_day budget (spent_total 1 then 2)",
          p1.get("spent_total") == 1 and p2.get("spent_total") == 2, f"{p1.get('spent_total')},{p2.get('spent_total')}")
    check(f"[{shape}] the third pick the same day is budget_exhausted (per_day=2)",
          p3.get("status") == "budget_exhausted" and p3.get("scope") == "per_day", str(p3)[:120])

    # ── RESTART — a fresh kernel on the SAME base_dir reads the durable counters (no re-spend) ──
    k2 = _kernel(series, base)
    sw2 = SweepConcept(k2.manager.get_session("admin"))
    hm = sw2._meta(sw2._sweep_head(BENCH, SWEEP)) or {}
    today = sw2._bench_day()
    check(f"[{shape}] after RESTART the budget counters survive (spent_total=2, spent_today=2, day=today)",
          int(hm.get("spent_total", 0)) == 2 and int(hm.get("spent_today", 0)) == 2
          and hm.get("day") == today,
          str({kk: hm.get(kk) for kk in ("spent_total", "spent_today", "day")}))
    # the restarted driver still refuses today (the day's budget is spent, durably)
    pr = sw2.driver_pick(bench=BENCH, name=SWEEP)
    check(f"[{shape}] the restarted driver still refuses today (durable per_day exhaustion)",
          pr.get("status") == "budget_exhausted" and pr.get("scope") == "per_day", str(pr)[:120])

    # ── a NEW bench day resets spent_today (a pick is allowed) but KEEPS spent_total ──
    sw2._set_meta(sw2._key(sw2._sweep_head(BENCH, SWEEP)), "day", "2000-01-01")
    pn = sw2.driver_pick(bench=BENCH, name=SWEEP)
    check(f"[{shape}] a new bench day resets spent_today (a pick is allowed again)",
          pn.get("status") == "picked" and pn.get("spent_today") == 1, str(pn)[:140])
    check(f"[{shape}] spent_total is NOT reset by the new day (the total cap counts every pick: 2→3)",
          pn.get("spent_total") == 3, str(pn.get("spent_total")))

    # ── the total cap eventually stops all picks even on a fresh day ──
    sw2._set_meta(sw2._key(sw2._sweep_head(BENCH, SWEEP)), "day", "2000-01-02")
    sw2.driver_pick(bench=BENCH, name=SWEEP)                     # spent_total 3 → 4
    sw2._set_meta(sw2._key(sw2._sweep_head(BENCH, SWEEP)), "day", "2000-01-03")
    sw2.driver_pick(bench=BENCH, name=SWEEP)                     # spent_total 4 → 5 (== total)
    sw2._set_meta(sw2._key(sw2._sweep_head(BENCH, SWEEP)), "day", "2000-01-04")
    pt = sw2.driver_pick(bench=BENCH, name=SWEEP)
    check(f"[{shape}] the total cap stops picks even on a fresh day (budget_exhausted total)",
          pt.get("status") == "budget_exhausted" and pt.get("scope") == "total", str(pt)[:120])


def main():
    print("=" * 78)
    print("B1-c — sweep budget durability: counters survive restart, spent_today resets on a new day")
    print("=" * 78)
    _run("thesaurus", "nucleus cell")
    _run("seeds", "single-store cell")
    print()
    if _fails:
        print("RESULT: FAIL — %d check(s) failed:" % len(_fails))
        for f in _fails:
            print("   - " + f)
        sys.exit(1)
    print("RESULT: PASS — the driver's budget counters (spent_today / spent_total / day) ride the "
          "sweep_def atom durably: they survive a process restart with no re-spend, spent_today resets "
          "on a new bench day while spent_total keeps counting, and the total cap stops all picks — "
          "both cell shapes.")


if __name__ == "__main__":
    main()
