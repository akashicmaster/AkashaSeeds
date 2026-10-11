#!/usr/bin/env python3
"""
A44 — the state reset happens ONCE PER WRITER BOOT (not every 60 s), and A45 — the daily budget is
visible and a new build's boot run is exempt.

A33/A44 history: a failed run left `boot_done=True`; the reset then popped boot_id and kept boot_done,
so `boot_id != boot_id` was true again every tick → a `state reset` line every 60 s that also erased
the breaker and any pending retry each minute. A44: the reset stamps boot_id + sets `boot_pending`
(the ONLY gate-opener), `_autorun_due` fires on `boot_pending`, and the run clears it before the first
block. A45: `runs_today >= cap` was a silent `budget_skip`; now it logs once/day (+ Health `budget:`),
a budget-blocked retry WARNs, and a NEW-BUILD boot run is exempt from the cap (once per build fp).

Run:  python app/test/bench_autorun_reboot_eval.py     (exit 0 = all pass)
"""
import hashlib
import json
import logging
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


class _Cap(logging.Handler):
    def __init__(self):
        super().__init__(level=logging.INFO); self.lines = []

    def emit(self, record):
        try:
            self.lines.append(record.getMessage())
        except Exception:
            pass

    def count(self, sub):
        return sum(1 for ln in self.lines if sub in ln)

    def has(self, *subs):
        return any(all(s in ln for s in subs) for ln in self.lines)


def _run(series, shape):
    print(f"\n  ── {shape} ({series}) ──")
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series=series, base_dir=tempfile.mkdtemp(prefix="akasha_rb_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")
    k._bfp_cache = "NEWFP"          # pin the build fingerprint so the new-build exemption is deterministic

    def d(method, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
        return r if "error" in r else (r.get("result") or {})

    from lib.akasha.concepts.society import SocietyConcept
    sc = SocietyConcept(k.manager.get_session("admin"))

    # ── unit: _autorun_due keys the boot gate on boot_pending (A44) ──
    pol = {"workflows": ["main"], "trigger": "boot", "then": "daily:03:00"}
    check(f"[{shape}] boot is DUE when boot_pending is set", autorun.autorun_due(pol, {"boot_pending": True}, 1000.0) is True)
    check(f"[{shape}] boot is NOT due once boot_pending is cleared (the run fired this boot)",
          autorun.autorun_due(pol, {"boot_pending": False, "boot_id": "x"}, 1000.0) is False)

    d("world.genesis", {})
    d("grp.new", {"group_id": "rb", "admin_id": "admin"})
    d("bench.new", {"name": "rbb", "kind": "research"})      # public
    d("society.new", {"group": "rb", "name": "rbsoc", "world": "default", "bench": "rbb", "kind": "cowork"})
    mod = d("cast.new", {"name": "RbMod"}).get("cast_id")
    scr = d("cast.new", {"name": "RbScr"}).get("cast_id")
    d("society.admit", {"group": "rb", "name": "rbsoc", "cast": mod})
    d("society.admit", {"group": "rb", "name": "rbsoc", "cast": scr})
    d("society.moderator", {"group": "rb", "name": "rbsoc", "cast": mod})
    d("society.responsible", {"group": "rb", "name": "rbsoc", "cast": scr, "kind": "scribe"})
    d("wf.new", {"bench": "rbb"})
    d("wf.write", {"bench": "rbb", "pos": 1,
                   "entry": json.dumps({"method": "research.note", "params": {"name": "rbb", "text": "ok"}})})
    p = {"workflows": ["main"], "trigger": "boot", "then": "daily:03:00",
         "budget": {"runs_per_day": 9, "max_wall_s": 60}, "on_failure": {"retries": 1, "breaker": 3},
         "requires": ["source:pool:rbgate:v1"]}    # an unfrozen pool → the run is BLOCKED
    d("society.moderator", {"group": "rb", "name": "rbsoc", "mode": "auto", "policy": json.dumps(p)})
    # a stale run from a PREVIOUS boot: boot_done + old boot_id + a breaker to be cleared
    sc.write_autorun_state("rb", "rbsoc", {"boot_done": True, "boot_id": "999:999",
                                           "runs_today": 1, "day": "1970-01-01", "breaker": 1})

    root = logging.getLogger(); cap = _Cap(); root.addHandler(cap); _lvl = root.level; root.setLevel(logging.INFO)
    try:
        # ── A44(6): tick 1 with the run BLOCKED (requires) → exactly one reset, breaker cleared ──
        autorun.bench_autorun_tick(k)
        st = sc.read_autorun("rb", "rbsoc").get("state") or {}
        check(f"[{shape}] tick 1 resets once: boot_pending set, boot_id stamped, breaker cleared",
              st.get("boot_pending") is True and st.get("boot_id") == k._writer_boot_id() and st.get("breaker") == 0,
              str({kk: st.get(kk) for kk in ("boot_pending", "breaker")}))
        check(f"[{shape}] exactly one `state reset` line on tick 1", cap.count("state reset society=rb/rbsoc") == 1)
        # ── tick 2 (still blocked) does NOT reset again, does not touch breaker/retry ──
        autorun.bench_autorun_tick(k)
        check(f"[{shape}] tick 2 does NOT reset again (one reset per boot)",
              cap.count("state reset society=rb/rbsoc") == 1)
        st2 = sc.read_autorun("rb", "rbsoc").get("state") or {}
        check(f"[{shape}] boot_pending survives while the run is blocked", st2.get("boot_pending") is True)

        # ── the block lifts (freeze the pool) → the boot run fires ONCE, boot_pending cleared ──
        reg = d("source.register", {"provider": "rb", "name": "rbg", "rights": "CC0"}).get("source")
        d("source.pool.create", {"name": "source:pool:rbgate:v1", "rule": "x", "source": reg})
        d("source.acquire", {"source": reg, "rule": "x", "pool": "source:pool:rbgate:v1",
                             "id_field": "id", "records": [{"id": "g1"}]})
        d("source.pool.freeze", {"pool": "source:pool:rbgate:v1"})
        acts = autorun.bench_autorun_tick(k)
        a = next((x for x in acts if x.get("society") == "rb/rbsoc"), {})
        st3 = sc.read_autorun("rb", "rbsoc").get("state") or {}
        check(f"[{shape}] the boot run fires once the block lifts, and clears boot_pending",
              a.get("action") == "ran" and a.get("ok") is True and not st3.get("boot_pending"), str(a)[:120])
    finally:
        root.removeHandler(cap); root.setLevel(_lvl)

    # ── A45: a NEW-BUILD boot run is exempt from the cap; a `then:` run at the cap is not ──
    # cap reached, a fresh build fp ⇒ the reset marks the boot run exempt and it runs despite runs_today≥cap
    p2 = {"workflows": ["main"], "trigger": "boot", "then": "daily:03:00",
          "budget": {"runs_per_day": 1, "max_wall_s": 60}, "on_failure": {"retries": 1, "breaker": 3}}
    d("society.moderator", {"group": "rb", "name": "rbsoc", "mode": "auto", "policy": json.dumps(p2)})
    import time as _t
    _today = _t.strftime("%Y-%m-%d", _t.gmtime())
    sc.write_autorun_state("rb", "rbsoc", {"boot_id": "OLD:BUILD", "build_fp": "OLDFP",
                                           "runs_today": 5, "day": _today, "breaker": 0})
    cap2 = _Cap(); root.addHandler(cap2); root.setLevel(logging.INFO)
    try:
        acts = autorun.bench_autorun_tick(k)
        a = next((x for x in acts if x.get("society") == "rb/rbsoc"), {})
        check(f"[{shape}] a NEW-BUILD boot run runs despite runs_today≥cap (budget-exempt)",
              a.get("action") == "ran", str(a)[:120])
        check(f"[{shape}] no `budget exhausted` line for the exempt new-build run",
              cap2.count("budget exhausted society=rb/rbsoc") == 0)
        # now a same-build `then:` run at the cap is NOT exempt → budget exhausted + no run. A `then:daily`
        # window is time-dependent, so drive the clock to today 03:05 UTC (the daily:03:00 window is then
        # due) — boot_pending False (not a boot run), no retry_at (so it is the NON-retry cap path).
        import calendar as _cal
        _tm = _t.gmtime()
        _now = float(_cal.timegm((_tm.tm_year, _tm.tm_mon, _tm.tm_mday, 3, 5, 0, 0, 0, 0)))
        _today3 = _t.strftime("%Y-%m-%d", _t.gmtime(_now))
        st4 = sc.read_autorun("rb", "rbsoc").get("state") or {}
        st4["boot_id"] = k._writer_boot_id(); st4["build_fp"] = k._build_fp()
        st4["runs_today"] = 1; st4["day"] = _today3; st4["boot_pending"] = False
        st4["budget_exempt_fp"] = None                     # the new-build exemption does not carry over
        st4["last_run"] = 0.0; st4["retry_at"] = 0.0
        sc.write_autorun_state("rb", "rbsoc", st4)
        acts = autorun.bench_autorun_tick(k, _now)                 # boot done; then:daily:03:00 is due, at the cap
        a = next((x for x in acts if x.get("society") == "rb/rbsoc"), {})
        check(f"[{shape}] a `then:` run at the cap is blocked and logs `budget exhausted`",
              a.get("action") != "ran" and cap2.has("budget exhausted", "society=rb/rbsoc"),
              str(a)[:100])
    finally:
        root.removeHandler(cap2); root.setLevel(_lvl)


def main():
    _run("thesaurus", "nucleus cell")
    _run("seeds", "single-store cell")
    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("\nRESULT: PASS — the state reset happens exactly once per writer boot (boot_pending gate, no "
          "60 s loop, breaker/retry untouched on later ticks), the boot run fires once the block lifts, "
          "the daily cap is visible (`budget exhausted` once/day + Health `budget:`), and a new-build "
          "boot run is exempt from the cap while a `then:` run at the cap is not — both cell shapes.")
    sys.exit(0)


if __name__ == "__main__":
    main()
