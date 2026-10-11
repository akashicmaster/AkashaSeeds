#!/usr/bin/env python3
"""
The station's durable stores install at boot, and a failure is REPORTED (F56 v64).

The layout seed replaced the launcher's `_schedule_station()` — which installed four things and
then started the broadcaster thread — with the generic thread-unit start, whose declared starter is
`start_station`: the thread alone. All four preamble steps were silently lost, and the only trace
was a `debug`-level "skipped (non-fatal)" nobody reads. One boot later the LLM pool, A53's spend
meter and the 429 back-off were all back in process memory, the guest pool atom froze at the first
airing's counts, and nothing in the log said why.

The fix is the mechanism the layout seed built: the four steps are a DECLARED writer-phase
schedule, so the boot names them on its phase line and an exception is `status=error` instead of a
debug skip.

Checked here:
  1. `install_workload_stores` is declared as a writer-phase schedule in the workbench manifest, and
     the aggregate resolves it (a hook nothing calls is exactly the bug)
  2. running it installs the durable pool store, the back-off store AND A53's meter store — the
     three that make a restart remember what it spent
  3. it emits the `[llm] pool provider=… day=… cap=… spent=… reserved=…` boot line
  4. a store that RAISES is not swallowed: the exception reaches `run_phase`, which reports
     `status=error` naming the body, and the rest of the phase still runs
  5. `llm_pool_reflect` logs one `[llm] pool reflected …` line per call, and logs a FAILURE at
     warning level rather than debug — the guest atom is its only writer
  6. the thread unit is still `start_station` (the stores are not the thread, and must install even
     when the station is opted out — any LLM-using workflow reserves against the same pool)

Run:  python test/workload_stores_boot_eval.py     (exit 0 = all pass)
"""
import hashlib
import json
import logging
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT); sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


class _Capture(logging.Handler):
    def __init__(self):
        super().__init__(); self.rows = []

    def emit(self, record):
        self.rows.append((record.levelno, record.getMessage()))

    def text(self):
        return "\n".join(m for _l, m in self.rows)


def main():
    from lib.akasha.kernel import KernelDispatcher
    from lib.akasha.api.schedule import ScheduleRegistry

    # ── 1. the hook is DECLARED, and the aggregate resolves it ───────────────────────────────
    man = json.load(open("lib/akasha/workbench/MANIFEST.json", encoding="utf-8"))
    spec = (man.get("schedules") or {}).get("workload_stores") or {}
    check("the workbench manifest declares `workload_stores` as a writer-phase schedule",
          spec.get("fn", "").endswith(":install_workload_stores")
          and spec.get("phase") == "writer" and spec.get("when") in ("every_boot", "new_build"),
          str(spec))
    check("…and it runs BEFORE the driver arms (order < bench_autorun), so a pick reserves against "
          "the durable pool", int(spec.get("order", 9999)) < int(
              ((man.get("schedules") or {}).get("bench_autorun") or {}).get("order", 0)),
          "workload_stores=%s bench_autorun=%s" % (
              spec.get("order"), ((man.get("schedules") or {}).get("bench_autorun") or {}).get("order")))

    from lib.akasha import kernel as _kmod
    agg = _kmod._heart_aggregate()
    body = agg.schedules.get("workload_stores")
    check("the aggregate resolves the body — a hook nothing calls is the bug itself", callable(body))
    meta = agg.schedules.meta("workload_stores")
    check("the boot line will attribute it to the workbench", meta.get("package") == "workbench",
          str(meta))

    # Seed A §2.6 — the broadcaster thread unit is GONE: the news programme's cadence is its
    # declared `trigger`, read by the one driver, so there is no second clock, no second admission
    # point and no second count of what aired today. The stores were never the thread (that is what
    # this eval was written for), and they install exactly as before with the thread retired.
    units = {u["name"]: u for u in (man.get("thread_units") or [])}
    check("the broadcaster's own timer is retired — no `svc:news-broadcast` thread unit, because "
          "a declared trigger is the only cadence",
          "svc:news-broadcast" not in units, str(sorted(units)))
    check("…and the stores still install on their own writer-phase schedule",
          (man.get("schedules") or {}).get("workload_stores", {}).get("phase") == "writer")

    # ── 2/3. running it installs all three stores and logs the boot line ─────────────────────
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="thesaurus", base_dir=tempfile.mkdtemp(prefix="akasha_stst_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    from lib.akasha.workbench import llm_pool as _lpool, llm_provider as _lp, workload_provision as _st
    _lpool._STORE = None
    _lp._BACKOFF_STORE = getattr(_lp, "_BACKOFF_STORE", None) and None
    check("before the hook runs, the pool is on its process-memory fallback (the bug's state)",
          _lpool._STORE is None)

    cap = _Capture()
    lg = logging.getLogger("Akasha.Kernel")
    lg.addHandler(cap); old = lg.level; lg.setLevel(logging.DEBUG)
    try:
        _st.install_workload_stores(k)
    finally:
        lg.removeHandler(cap); lg.setLevel(old)

    check("the hook installs the DURABLE pool store (spent/reserved/refused survive a restart)",
          _lpool._STORE is not None)
    check("…the 429 back-off store (a restart inside a window does not re-hit the provider)",
          getattr(_lp, "_BACKOFF_STORE", None) is not None)
    check("…and A53's spend meter store (what a restart forgets, it overspends)",
          getattr(_lp, "_METER_STORE", None) is not None)
    boot_line = [m for _l, m in cap.rows if m.startswith("[llm] pool provider=")]
    check("the boot line is emitted — its ABSENCE is how the whole regression showed on the VPS",
          len(boot_line) == 1 and "cap=" in boot_line[0] and "spent=" in boot_line[0],
          str(boot_line))

    # the durable store really round-trips through the vault
    _lpool._save("evalprobe", {"reserved": 7})
    check("the installed store round-trips through the shared-nucleus vault (durable, not _MEM)",
          int((_lpool._load("evalprobe") or {}).get("reserved", 0)) == 7
          and "evalprobe" not in _lpool._MEM,
          str(_lpool._load("evalprobe")))

    # ── 4. a raising store is REPORTED by the phase, not swallowed ───────────────────────────
    reg = ScheduleRegistry()
    after = []
    reg.register("workload_stores", lambda _k: (_ for _ in ()).throw(RuntimeError("no vault")),
                 phase="writer", order=40, source="workbench:x", when="every_boot",
                 package="workbench")
    reg.register("later", lambda _k: after.append(1), phase="writer", order=50,
                 source="workbench:y", when="every_boot", package="workbench")
    cap2 = _Capture(); lg.addHandler(cap2); lg.setLevel(logging.INFO)
    try:
        reg.run_phase(None, "writer")
    finally:
        lg.removeHandler(cap2); lg.setLevel(old)
    line = next((m for _l, m in cap2.rows if "name=workload_stores" in m), "")
    check("a store that RAISES is reported `status=error` with the exception named — never a "
          "debug-level 'skipped (non-fatal)'",
          "status=error" in line and "RuntimeError" in line and "no vault" in line, line)
    check("…and the rest of the writer phase still runs", after == [1], str(after))

    # ── 5. reflect logs its line, and a failure is LOUD ──────────────────────────────────────
    from lib.akasha.workbench import llm as _llm
    cap3 = _Capture(); lg.addHandler(cap3); lg.setLevel(logging.INFO)
    try:
        _llm.llm_pool_reflect(k, "mistral")
    finally:
        lg.removeHandler(cap3); lg.setLevel(old)
    refl = [m for _l, m in cap3.rows if m.startswith("[llm] pool reflected ")]
    check("every reflect logs one line, so a stale guest atom and a reflect that never ran are "
          "distinguishable from the log alone",
          len(refl) == 1 and "spent=" in refl[0] and "runs=" in refl[0], str(refl))

    class _BoomMgr:
        @property
        def shared_nucleus(self):
            raise RuntimeError("vault gone")

    class _Boom:
        manager = _BoomMgr()                 # reading the nucleus raises, as a broken store would
    cap4 = _Capture(); lg.addHandler(cap4); lg.setLevel(logging.DEBUG)
    try:
        _llm.llm_pool_reflect(_Boom(), "mistral")     # must not raise out
    except Exception as exc:
        check("a failing reflect does not take the airing down with it", False, str(exc))
    finally:
        lg.removeHandler(cap4); lg.setLevel(old)
    warned = [m for lv, m in cap4.rows if lv >= logging.WARNING and "pool reflect FAILED" in m]
    check("a failing reflect is logged at WARNING with the exception named (it is the only writer "
          "of the guest-readable atom)", len(warned) == 1, str(cap4.rows[-2:]))

    # ── 6. a public bench NAMES ITSELF and the hook that asked ───────────────────────────────
    # Two benches (wb:plants_lab, wb:studio_shelf) appeared between deploys with no line in either
    # log saying which path created them, so a provisioning hook and an operator step were
    # indistinguishable after the fact. There is one creation seam; it logs.
    from app.concepts.bench_station import BenchStationConcept
    sess = k.manager.get_session("admin")
    wlg = logging.getLogger("Harmonia.Concept.Workbench")
    cap5 = _Capture(); wlg.addHandler(cap5); w_old = wlg.level; wlg.setLevel(logging.INFO)
    try:
        BenchStationConcept(sess)._ensure_public_bench("evalstudio", "station", by="eval.probe")
        BenchStationConcept(sess)._ensure_public_bench("evalstudio", "station", by="eval.probe")
    finally:
        wlg.removeHandler(cap5); wlg.setLevel(w_old)
    made = [m for _l, m in cap5.rows if m.startswith("[bench] new ")]
    check("creating a public bench logs `[bench] new <alias> kind=… by=<hook>` — a durable, "
          "guest-visible object never appears anonymously",
          len(made) == 1 and "wb:evalstudio" in made[0] and "kind=station" in made[0]
          and "by=eval.probe" in made[0], str(made))
    check("…and the idempotent second call is silent (only the transition is news)", len(made) == 1)

    import glob as _glob
    import re as _re
    calls, unnamed, raw = 0, [], []
    for f in (_glob.glob("lib/akasha/**/*.py", recursive=True) + _glob.glob("app/concepts/**/*.py", recursive=True)):
        for i, ln in enumerate(open(f, encoding="utf-8", errors="replace"), 1):
            # either spelling: the 4.16 public name `ensure_public_bench` and the underscore alias
            # kept one seed — the claim is about every call, not about which name it uses
            if (_re.search(r"\b_?ensure_public_bench\(", ln)
                    and not _re.search(r"def\s+_?ensure_public_bench", ln)):
                calls += 1
                if "by=" not in ln:
                    unnamed.append("%s:%d" % (f, i))
            if _re.search(r"\.op_new\(\s*name=[^)]*kind=[\"'](station|research)[\"']", ln):
                raw.append("%s:%d" % (f, i))
    # The floor is 2, not 3: the third call site was `ensure_station` in the platform's own
    # station.py, deleted in step 2. The claim is unchanged — every call that EXISTS names its
    # hook — and the floor is only there so a scan that found nothing cannot pass by accident.
    check("every `_ensure_public_bench` call names its hook — no bench is created anonymously "
          "(%d call sites)" % calls, calls >= 2 and not unnamed, str(unnamed))
    check("and nothing creates a public bench AROUND the seam with a raw op_new", not raw, str(raw))

    # ── 7. no function shadows a module it also calls through ───────────────────────────────
    # `station_air_burst` assigned a local named `llm` (the (provider, model) pair) while the file
    # imports the MODULE `llm` at the top — so every `llm.llm_pool_reflect(...)` and
    # `llm.llm_admission_log(...)` in that function raised AttributeError on a tuple. A bare
    # `except: pass` hid it, and the day's pool atom sat frozen while Health climbed. This is a
    # whole class of silent bug, so it is checked as a class.
    import ast as _ast
    import glob as _g
    # Deliberate rebinds where the local holds the SAME object the import names, so calling through
    # it is correct. Each is listed by name with its reason; the list may only shrink.
    _SHADOW_OK = {
        # `_svc_plane()` hands back the very Capability enum the module imports, so the local is
        # that class and `Capability.SVC_OPERATE` resolves exactly as the import would.
        ("lib/akasha/kernel.py", "_handle_svc_ls", "Capability"),
        ("lib/akasha/kernel.py", "_handle_svc_stop", "Capability"),
        ("lib/akasha/kernel.py", "_handle_svc_start", "Capability"),
    }
    shadows = []
    for f in _g.glob("lib/akasha/**/*.py", recursive=True):
        try:
            tree = _ast.parse(open(f, encoding="utf-8", errors="replace").read(), f)
        except SyntaxError:
            continue
        mods = set()
        for n in tree.body:                      # module-level imports only
            if isinstance(n, _ast.Import):
                mods |= {(a.asname or a.name.split(".")[0]) for a in n.names}
            elif isinstance(n, _ast.ImportFrom):
                mods |= {(a.asname or a.name) for a in n.names}
        for fn in _ast.walk(tree):
            if not isinstance(fn, (_ast.FunctionDef, _ast.AsyncFunctionDef)):
                continue
            assigned, attr_used = set(), set()
            for n in _ast.walk(fn):
                if isinstance(n, _ast.Name) and isinstance(n.ctx, _ast.Store):
                    assigned.add(n.id)
                elif isinstance(n, _ast.arg):
                    assigned.add(n.arg)
                elif isinstance(n, _ast.Attribute) and isinstance(n.value, _ast.Name):
                    attr_used.add(n.value.id)
            for bad in sorted(mods & assigned & attr_used):
                if (f.replace("\\", "/"), fn.name, bad) in _SHADOW_OK:
                    continue
                shadows.append("%s:%d %s() rebinds `%s` and also calls `%s.…`"
                               % (f, fn.lineno, fn.name, bad, bad))
    check("no function rebinds a module-level import it also calls through — the shadowing that "
          "made every pool reflect raise on a tuple", not shadows,
          "%d: %s" % (len(shadows), "; ".join(shadows[:3])))

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("RESULT: PASS — the station's durable stores are a declared writer-phase schedule the boot "
          "names and reports; the pool, the back-off and A53's meter all install; a store that "
          "raises is `status=error`, not a debug skip; and every pool reflect leaves a line.")
    sys.exit(0)


if __name__ == "__main__":
    main()
