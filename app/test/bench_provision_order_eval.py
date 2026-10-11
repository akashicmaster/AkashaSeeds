#!/usr/bin/env python3
"""
The driver must not tick before the declared-workload pass has written this boot's workflow entries.

On 3 October the first tick after `ontology.loaded` ran the PREVIOUS build's entries (`bench.publish`,
renamed since) — `Method not found`, `breaker=1` — because the driver waited only on the legacy
bench_*.json / auto_exec.json pass's event. That pass is gone (the purge order §2); the declared pass
`workload_provision` sets `kernel._workload_provision_done` in a `finally` (with declarations or
without; and on shutdown), and the driver waits for it (ceiling 30 min, then a WARNING).

A declared workload whose template names method `a` on boot 1 and the renamed method `b` on boot 2; on
boot 2 the declared pass is held behind its gate while the driver thread starts (the 3 October order).
The first run of boot 2 dispatches `b`, and no run starts before that boot's `[bench] provisioned
workload=<key>`. With the old wait the eval reproduces 3 October's log line for line.

Run:  python app/test/bench_provision_order_eval.py     (exit 0 = all pass)
"""
import hashlib
import json
import logging
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from lib.akasha.workbench import provision
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


class _Cap(logging.Handler):
    def __init__(self):
        super().__init__(level=logging.INFO)
        self.lines = []

    def emit(self, record):
        try:
            self.lines.append(record.getMessage())
        except Exception:
            pass

    def first(self, *subs):
        return next((i for i, ln in enumerate(self.lines) if all(x in ln for x in subs)), None)


def _declared_rename(series, shape):
    """10-03 item 1 — a DECLARED workload whose template names method `a` on boot 1 and the renamed
    method `b` on boot 2. The legacy pass is done (its event set) and the declared pass is still
    behind its gate when the driver starts — the 3 October order. The first run of boot 2 must
    dispatch `b`, and no run may start before that boot's `[bench] provisioned workload=<key>`."""
    print(f"\n  ── 3. a declared workload renamed between boots ({shape}) ──")
    import threading
    import time
    from lib.akasha.kernel import KernelDispatcher
    from lib.akasha import kernel_methods as KM
    from lib.akasha.api import schedule as SCH
    from lib.akasha.workbench import autorun, workload as W, workload_provision as WP
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series=series, base_dir=tempfile.mkdtemp(prefix="akasha_ren_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")
    k.dispatch({"jsonrpc": "2.0", "method": "world.genesis",
                "params": {"session_token": "admin", "data": {}}, "id": "w"}, "local")

    calls = []

    def _op(tag):
        def fn(kernel, rid, data):
            calls.append((tag, time.time()))
            return {"jsonrpc": "2.0", "id": rid, "result": {"ok": True, "step": tag}}
        return fn
    k.api.ops.register("evalren.step_a", _op("a"), stage="pre", access="read", source="eval")
    KM.METHOD_TO_ACTION["evalren.step_a"] = "read"
    tdir = tempfile.mkdtemp(prefix="akasha_ren_tpl_")
    tpl = os.path.join(tdir, "evalren.ak")

    def write_tpl(method):
        with open(tpl, "w", encoding="utf-8") as f:
            f.write("# eval: one step\n%s\n" % method)
    with open(os.path.join(ROOT, "app", "config", "workbench", "workloads", "eonet.json"),
              encoding="utf-8") as f:
        decl = W.with_profile(json.load(f), "eonet.json")   # as the loader reads it: profile defaults
    decl.update(_file="evalren.json", workflow="evalren", society="evalren/evalren",
                bench="wb:evalren", pins={}, requires=[],
                trigger={"boot": True})
    decl["space"] = dict(decl["space"], client="feed:evalren", name="eval rename")
    check(f"[{shape}] (the eval's declaration is valid: {W.problems(decl) or 'ok'})", not W.problems(decl))
    key = W.key(decl)
    _real_tpls = WP.templates_of
    WP.templates_of = lambda dc: ([(W.branch_of(dc), tpl)] if dc.get("_file") == "evalren.json"
                                  else _real_tpls(dc))
    k._workload_decl_cache = [decl]
    root = logging.getLogger()
    _lvl = root.level
    root.setLevel(logging.INFO)
    try:
        # ── boot 1: method a ──
        write_tpl("evalren.step_a")
        # The kernel's writer phase already started ITS driver thread, waiting on the kernel's own
        # event. A real boot has exactly one driver; keep that one parked (its event is never set) so
        # the driver under test — started below for boot 2 — is the only one that ticks.
        k._workload_provision_done = threading.Event()
        provision.schedule_workload_provision(k)
        autorun.bench_autorun_tick(k)
        _dl = time.time() + 60
        while time.time() < _dl and not calls:
            time.sleep(0.5)
        check(f"[{shape}] boot 1 runs method a", [c[0] for c in calls][:1] == ["a"], str(calls))

        # ── boot 2: a renamed to b; the template says b; the driver starts before the pass ──
        k.api.ops._entries.pop("evalren.step_a", None)
        KM.METHOD_TO_ACTION.pop("evalren.step_a", None)
        k.api.ops.register("evalren.step_b", _op("b"), stage="pre", access="read", source="eval")
        KM.METHOD_TO_ACTION["evalren.step_b"] = "read"
        write_tpl("evalren.step_b")
        k._wbid = "eval:boot2"                       # a new writer boot → the boot run is owed again
        n1 = len(calls)
        k._workload_provision_done = threading.Event()
        SCH._defer(k, "evalren.loaded", "workload_provision", provision.schedule_workload_provision)
        cap = _Cap()
        root.addHandler(cap)
        try:
            autorun.schedule_bench_autorun(k)        # the driver thread, as the writer phase starts it
            time.sleep(6)                            # the gap the 3 October boot had (ontology load)
            SCH.open_gate(k, "evalren.loaded")       # the declared pass, released by its gate
            _dl = time.time() + 90
            while time.time() < _dl and len(calls) == n1 and not cap.first("Method not found"):
                time.sleep(0.5)
            time.sleep(1.0)
        finally:
            root.removeHandler(cap)
        print("\n".join("    · " + ln[:200] for ln in cap.lines if ln.startswith(("[bench", "[boot]", "[wf]", "[JCL]"))))
        after = [c[0] for c in calls[n1:]]
        i_prov = cap.first("[bench] provisioned workload=%s" % key)
        i_run = cap.first("[bench.auto] run start", "society=evalren/evalren")
        check(f"[{shape}] boot 2: the first run dispatches b (the renamed method)",
              after[:1] == ["b"] and not cap.first("Method not found"),
              "calls=%s notfound=%s" % (after, cap.first("Method not found")))
        check(f"[{shape}] boot 2: no run starts before `[bench] provisioned workload={key}`",
              i_prov is not None and i_run is not None and i_prov < i_run,
              "provisioned@%s run_start@%s" % (i_prov, i_run))
        check(f"[{shape}] the declared pass set `_workload_provision_done`",
              k._workload_provision_done.is_set())
    finally:
        root.setLevel(_lvl)
        WP.templates_of = _real_tpls
        k.api.ops._entries.pop("evalren.step_b", None)
        KM.METHOD_TO_ACTION.pop("evalren.step_b", None)

    # ── no declarations: the pass still sets the event (the driver never waits on nothing) ──
    k._workload_decl_cache = []
    k._workload_provision_done = threading.Event()
    provision.schedule_workload_provision(k)
    check(f"[{shape}] with NO declarations the declared pass still sets the event",
          k._workload_provision_done.is_set())


def main():
    _declared_rename("seeds", "single-store cell")
    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("\nRESULT: PASS — the driver waits for the declared-workload pass, so a method renamed between "
          "boots runs under its new name; the pass sets its event with no declarations too.")
    sys.exit(0)


if __name__ == "__main__":
    main()
