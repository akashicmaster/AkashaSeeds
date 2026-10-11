#!/usr/bin/env python3
"""
A first ontology load releases the workload driver when its core is in, and no pack is dropped.

VPS 10-11: a thesaurus cell's first load held every workload all day — the driver resumes only
when the whole load is over, and a `load_all` tier's deep packs take hours. Two of them hit the
loader's wait cap and logged "phase-1 timeout — skipping link phase": the loader gave up on them,
so they were left unwoven and without a sentinel, and loaded again on every boot.

This runs the REAL loader (`ontology/loader.py`) over a fixture ontology of its own
(`AKASHA_PROJECT_DIR`) on a real cell: two core packs (`autoload: true`, one listed AFTER the deep
pack), and one deep pack (`autoload: false`, loaded by `load_all`) big enough to outlast a cap
shortened for the eval. One core file links to a name the deep pack defines.

  C1 the core packs load first, whatever their REGISTRY position
  C2 the driver is released (in_flight first=False) before the deep pack's atoms are queued, with
     the deep pack listed as still to load; `wl_state.onto_hold` holds only a workload reading it,
     or reading a Set a held core file binds (`relations:core`)
  C3 the core relations are applied then — except the file naming a deep name, left whole to the
     global phase, which binds its link to the deep DEFINITION (not a proto-word)
  D1 the deep pack outlasts the cap: no "skipping link phase"; it completes in the background
     (`load complete … deferred=background`), its weave is queued, its sentinel file is written
  D2 a restart skips every pack (sentinel hits, no atom job)

Run:  python test/first_load_core_eval.py     (exit 0 = all pass)
"""
import hashlib
import json
import logging
import os
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

_fails = []
DEEP_DEFS = 3000


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


class _Log(logging.Handler):
    def __init__(self):
        super().__init__()
        self.lines = []

    def emit(self, rec):
        self.lines.append(rec.getMessage())


def _write(path, lines):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def _project(root):
    ont = os.path.join(root, "ontology")
    _write(os.path.join(ont, "core_a", "a.ak"), [
        'def "core:a" "Core A — a core concept"',
        'def "core:b" "Core B — a core concept"',
        "ln core:a core:b thesaurus:related",
        'set.add name="core:set" id="core:a"',
    ])
    _write(os.path.join(ont, "core_a", "cross.ak"), [
        "ln core:b deep:x thesaurus:related",            # names a deep-pack definition
        'set.add name="core:crossset" id="core:b"',      # a Set this held file binds
    ])
    _write(os.path.join(ont, "core_late", "l.ak"), [
        'def "core:late" "Core late — listed after the deep pack in REGISTRY"',
        "ln core:late core:a thesaurus:related",
    ])
    deep = ['def "deep:x" "Deep X — defined by the deep pack"']
    deep += ['def "deep:item%05d" "Deep item %d"' % (i, i) for i in range(DEEP_DEFS)]
    _write(os.path.join(ont, "deep", "d.ak"), deep)
    for pn in ("core_a", "core_late", "deep"):
        _write(os.path.join(ont, pn, "PACK.json"), [json.dumps({"label": pn})])
    _write(os.path.join(ont, "REGISTRY.json"), [json.dumps({"version": 2, "packages": [
        {"name": "core_a", "autoload": True},
        {"name": "deep", "autoload": False},
        {"name": "core_late", "autoload": True}]})])
    _write(os.path.join(root, "config", "ontology", "packs.json"), [json.dumps({"load_all": True})])
    return ont


def main():
    print("=" * 78)
    print("A first load releases the driver at its core; a pack past the cap completes in background")
    print("=" * 78)
    root = tempfile.mkdtemp(prefix="first_load_core_eval_")
    _project(root)
    os.environ["AKASHA_PROJECT_DIR"] = root
    os.environ["AKASHA_APP_DIR"] = os.path.join(root, "app")

    from lib.akasha.kernel import KernelDispatcher
    from lib.akasha.ontology import loader as L
    from lib.akasha.workbench import wl_state
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="thesaurus", base_dir=os.path.join(root, "cell"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin",
                                    "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                "id": "g"}, "local")
    time.sleep(1.0)
    k._boot_daemons_started = True
    log = _Log()
    logging.getLogger("Akasha.Kernel").addHandler(log)
    logging.getLogger("Akasha.Kernel").setLevel(logging.INFO)

    # the cap, shortened so the deep pack (3,000 defs) outlasts it; the core packs do not
    L.PACK_WAIT_FLOOR_S, L.PACK_WAIT_PER_FILE_S = 0.3, 0

    jobs, seen = [], {}
    orig = k.harmonia.submit_job

    def _submit(job, job_class=None):
        label = str(getattr(job, "label", ""))
        jobs.append(label)
        if label.startswith("ont.ak.deep:") and "deep_first" not in seen:
            fl = dict(L.in_flight(k))
            seen["deep_first"] = fl
            # what the driver's scoped hold says now, for a workload reading a deep name and one
            # reading a core name (declarations are stubbed: the hold reads only their names)
            _by_key, _names = wl_state.W.by_key, wl_state.W.ontology_names
            _decls = {"t/deep": {"pins": ["deep:x"]}, "t/core": {"pins": ["core:a"]},
                      "t/heldset": {"pins": ["core:crossset"]}}
            wl_state.W.by_key = lambda kern, key: _decls.get(key)
            wl_state.W.ontology_names = lambda d: list((d or {}).get("pins") or [])
            _decl_all = wl_state.W.declarations
            wl_state.W.declarations = lambda kern: list(_decls.values())
            try:
                seen["hold_deep"] = wl_state.onto_hold(k, {"key": "t/deep"})
                seen["hold_core"] = wl_state.onto_hold(k, {"key": "t/core"})
                seen["hold_heldset"] = wl_state.onto_hold(k, {"key": "t/heldset"})
            finally:
                wl_state.W.by_key, wl_state.W.ontology_names = _by_key, _names
                wl_state.W.declarations = _decl_all
            # the REAL driver tick, now: it must say it left `scope=all`
            from lib.akasha.workbench import autorun as _ar
            k._bench_auto_gate_logged = "all"            # as a tick during the core load left it
            try:
                _ar.bench_autorun_tick(k)
            except Exception as exc:                      # noqa: BLE001 — reported by the check
                seen["tick_exc"] = repr(exc)
        return orig(job, job_class=job_class) if job_class is not None else orig(job)

    k.harmonia.submit_job = _submit
    wl_state.key_of = (lambda f: (lambda pol: pol.get("key") or f(pol)))(wl_state.key_of)

    print("\n  ── first load of a fresh cell ──")
    k._schedule_gates = None
    L.boot_load_ontology(k)

    # C1
    atom_order = [j.split(":")[0].replace("ont.ak.", "") for j in jobs
                  if j.startswith("ont.ak.") and j.split(":")[0].replace("ont.ak.", "")
                  in ("core_a", "core_late", "deep")]
    first_deep = atom_order.index("deep") if "deep" in atom_order else -1
    check("C1 both core packs' atom jobs precede the deep pack's",
          first_deep > 0 and "core_late" in atom_order[:first_deep], str(atom_order))

    # C2
    fl = seen.get("deep_first") or {}
    check("C2 the driver is released before the deep pack's atoms are queued",
          fl.get("first") is False and "deep" in (fl.get("packs") or []), str(fl))
    hd, hc = seen.get("hold_deep"), seen.get("hold_core")
    check("…a workload reading a deep name is held; one reading a core name is not",
          bool(hd) and hd.get("packs") == ["deep"] and hc == {}, f"deep={hd} core={hc}")
    hh = seen.get("hold_heldset")
    check("…and one reading a Set a held core file binds is held under `relations:core`",
          bool(hh) and hh.get("packs") == ["relations:core"], str(hh))
    touched = [l for l in log.lines if l.startswith("[bench.auto] onto_load in flight scope=touched")]
    check("…and a driver tick then logs the change (`scope=touched`)",
          bool(touched) and "deep" in touched[0] and not seen.get("tick_exc"),
          (touched[0] if touched else seen.get("tick_exc") or "no scope=touched line")[:120])
    core_line = next((l for l in log.lines if l.startswith("[onto] core ready")), "")
    check("…said in one `[onto] core ready` line", bool(core_line), core_line)

    # C3
    check("C3 core relations applied before the deep atoms, the cross file held whole",
          "ont.ak.relations:core" in jobs and jobs.index("ont.ak.relations:core") <
          next((i for i, j in enumerate(jobs) if j.startswith("ont.ak.deep:")), 10 ** 9)
          and "held_files=1" in core_line, core_line)
    nuc = k.manager.shared_nucleus
    rk = nuc.resolve_alias
    links = {(l["dst"], l["rel"]) for l in (nuc.core.get_adjacent_links(rk("core:b")) or [])}
    check("…and the global phase binds core:b → deep:x to the deep DEFINITION",
          (rk("deep:x"), "thesaurus:related") in links
          and (nuc.core.get_chunk_raw(rk("deep:x")) or {}).get("content", "").startswith("[deep:x]"),
          f"deep:x={rk('deep:x')}")
    late = {(l["dst"], l["rel"]) for l in (nuc.core.get_adjacent_links(rk("core:late")) or [])}
    check("…core_late's own link bound in the core pass", (rk("core:a"), "thesaurus:related") in late)

    # D1
    check("D1 no pack is dropped: no 'skipping link phase'",
          not any("skipping link phase" in l for l in log.lines))
    deep_done = next((l for l in log.lines if l.startswith("[Kernel] Pack 'deep': load complete")), "")
    check("…the deep pack outlasted the cap and completed in the background",
          any(l.startswith("[Kernel] Pack 'deep': phase-1 still running") for l in log.lines)
          and "deferred=background" in deep_done and "weave=queued" in deep_done, deep_done)
    check("…its weave was queued", "sys.weaver.batch:deep" in jobs)
    sent = os.path.join(root, "cell", "central", "sentinels")
    check("…and its sentinel file was written in this load",
          any(f.startswith("deep_") and f.endswith(".done") for f in os.listdir(sent))
          and any("Pack 'deep': background atoms landed" in l for l in log.lines))

    # D2
    print("\n  ── an unchanged restart ──")
    jobs.clear(); log.lines.clear()
    k._schedule_gates = None
    t0 = time.time()
    L.boot_load_ontology(k)
    atom_jobs = [j for j in jobs if j.startswith(("ont.ak.core_a:", "ont.ak.core_late:", "ont.ak.deep:"))]
    hits = [l for l in log.lines if "sentinel=hit" in l]
    check("D2 every pack is a sentinel hit, no atom job (%.1fs)" % (time.time() - t0),
          not atom_jobs and len(hits) == 3, f"atom_jobs={atom_jobs} hits={len(hits)}")

    print()
    if _fails:
        print(f"RESULT: FAIL — {len(_fails)} check(s): {_fails}")
        return 1
    print("RESULT: PASS — a first load releases the workload driver when its core is in, holding only "
          "the workloads a pack still to load touches, and a pack past the loader's wait completes in "
          "the background — woven, sentinelled, skipped on the next boot.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
