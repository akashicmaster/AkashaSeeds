#!/usr/bin/env python3
"""
A37 — a bench run's blocks are no longer silent: every stage reports its counts at INFO.

The v20 box symptom: b3 (feature extraction) "completed" but logged NOTHING — an operator watching the
run could not tell how many images were observed, skipped, or failed, nor how the fit went. The fix
threads a result line through every layer:
  • the DRIVER logs each block's job outcome — `[bench.auto] block=… job=… steps=N/N status=…`;
  • `vlab.run.execute` logs `observed=/skipped=/failed=` (b3 — the previously-silent stage);
  • `learning.train` logs `n_labeled=/classes=/engine=/accuracy=/macro_f1=` (added with A34);
  • `learning.evaluate` logs `n=/classes=/engine=/accuracy=/macro_f1=`.

This eval captures the log stream and asserts each line is emitted, on both cell shapes.

Run:  python app/test/bench_result_logging_eval.py     (exit 0 = all pass)
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
from lib.akasha.source import bootstrap
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []
_CLASSES = ["AAA", "BBB", "CCC"]


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


class _Capture(logging.Handler):
    def __init__(self):
        super().__init__(level=logging.INFO)
        self.lines = []

    def emit(self, record):
        try:
            self.lines.append(record.getMessage())
        except Exception:
            pass

    def has(self, *subs):
        return any(all(s in ln for s in subs) for ln in self.lines)


def _write_pack(pack_dir, pool, n):
    dd = os.path.join(pack_dir, "mini")
    os.makedirs(dd, exist_ok=True)
    json.dump({"pool": pool, "provider": "mini", "name": "mini", "rights": "CC0", "format": "jsonl",
               "data": "d.jsonl", "id_field": "id", "label_field": "species_symbol", "freeze": True,
               "rule": "mini image refs"}, open(os.path.join(dd, "pack.json"), "w"))
    with open(os.path.join(dd, "d.jsonl"), "w") as f:
        for i in range(n):
            f.write(json.dumps({"id": f"img{i}", "species_symbol": _CLASSES[i % 3],
                                "image_url": f"mock://leaf/{i}.jpg"}) + "\n")


def _run(series, shape):
    print(f"\n  ── {shape} ({series}) ──")
    base = tempfile.mkdtemp(prefix="akasha_rl_")
    pack_dir = tempfile.mkdtemp(prefix="akasha_rlpk_")
    os.environ["AKASHA_SOURCE_PACK_DIR"] = pack_dir
    POOL = "source:pool:mini_images:v1"
    _write_pack(pack_dir, POOL, 18)

    cap = _Capture()
    root = logging.getLogger()
    root.addHandler(cap)
    _prev_level = root.level
    root.setLevel(logging.INFO)
    try:
        from lib.akasha.kernel import KernelDispatcher
        KernelDispatcher._boot_load_ontology = lambda self: None
        k = KernelDispatcher(series=series, base_dir=base)
        k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                    "params": {"session_token": "admin", "data": {"user_name": "admin",
                               "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

        def d(method, data):
            r = k.dispatch({"jsonrpc": "2.0", "method": method,
                            "params": {"client_id": "admin", "data": data}, "id": "t"}, "internal")
            return r if "error" in r else (r.get("result") or {})

        d("world.genesis", {})
        bootstrap.source_packs_once(k)
        d("grp.new", {"group_id": "lab", "admin_id": "admin"})
        d("bench.new", {"name": "mini", "kind": "learning"})
        d("society.new", {"group": "lab", "name": "minisoc", "world": "default", "bench": "mini", "kind": "cowork"})
        d("learning.dataset.bind", {"name": "mini", "pool": POOL})

        # ── b3: feature.extract → vlab.run.execute logs observed/skipped/failed ──
        cap.lines.clear()
        d("learning.feature.extract", {"name": "mini", "pool": POOL, "observers": "color", "run": "r1"})
        check(f"[{shape}] vlab.run.execute logs observed/skipped/failed (b3 no longer silent)",
              cap.has("[vlab] run.execute", "observed=", "skipped=", "failed="),
              next((ln for ln in cap.lines if "run.execute" in ln), "(none)"))

        # ── b4: train logs n_labeled/classes/engine ──
        cap.lines.clear()
        tr = d("learning.train", {"name": "mini", "run": "r1", "space": "color", "head": "logreg", "seed": "s1"})
        model = tr.get("model")
        check(f"[{shape}] learning.train logs n_labeled/classes/engine/accuracy",
              cap.has("[bench] train", "n_labeled=", "classes=", "engine=", "accuracy="),
              next((ln for ln in cap.lines if "[bench] train" in ln), "(none)"))

        # ── evaluate logs n/classes/engine ──
        cap.lines.clear()
        d("learning.evaluate", {"name": "mini", "model": model, "sample": "test"})
        check(f"[{shape}] learning.evaluate logs n/classes/engine/accuracy",
              cap.has("[bench] evaluate", "n=", "classes=", "engine=", "accuracy="),
              next((ln for ln in cap.lines if "[bench] evaluate" in ln), "(none)"))

        # ── the DRIVER logs each block's job outcome (steps N/N) ──
        # a public research bench with a one-step workflow, armed auto + boot, driven once.
        d("grp.new", {"group_id": "dlab", "admin_id": "admin"})
        d("bench.new", {"name": "dbench", "kind": "research"})
        d("society.new", {"group": "dlab", "name": "dsoc", "world": "default", "bench": "dbench", "kind": "cowork"})
        dm = d("cast.new", {"name": "DMod"}).get("cast_id")
        ds = d("cast.new", {"name": "DScr"}).get("cast_id")
        d("society.admit", {"group": "dlab", "name": "dsoc", "cast": dm})
        d("society.admit", {"group": "dlab", "name": "dsoc", "cast": ds})
        d("society.moderator", {"group": "dlab", "name": "dsoc", "cast": dm})
        d("society.responsible", {"group": "dlab", "name": "dsoc", "cast": ds, "kind": "scribe"})
        d("wf.new", {"bench": "dbench"})
        d("wf.write", {"bench": "dbench", "pos": 1,
                       "entry": json.dumps({"method": "research.note", "params": {"name": "dbench", "text": "ok"}})})
        pol = {"workflows": ["main"], "trigger": "boot", "budget": {"runs_per_day": 9, "max_wall_s": 60},
               "on_failure": {"retries": 1, "breaker": 3}, "run_once": False}
        d("society.moderator", {"group": "dlab", "name": "dsoc", "mode": "auto", "policy": json.dumps(pol)})
        cap.lines.clear()
        acts = autorun.bench_autorun_tick(k)
        a = next((x for x in acts if x.get("society") == "dlab/dsoc"), {})
        check(f"[{shape}] the run completed (driver ran the block)",
              a.get("action") == "ran" and a.get("ok") is True, str(a)[:140])
        check(f"[{shape}] the driver logs each block's job outcome (steps N/N status)",
              cap.has("[bench.auto] block", "workflow=main", "steps=", "status=ok"),
              next((ln for ln in cap.lines if "[bench.auto] block" in ln), "(none)"))
    finally:
        root.removeHandler(cap)
        root.setLevel(_prev_level)
        os.environ.pop("AKASHA_SOURCE_PACK_DIR", None)


def main():
    _run("thesaurus", "nucleus cell")
    _run("seeds", "single-store cell")
    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("\nRESULT: PASS — every stage of a bench run reports at INFO: the driver logs each block's "
          "job outcome (steps N/N), vlab.run.execute logs observed/skipped/failed (b3), and "
          "train/evaluate log n_labeled/classes/engine/accuracy — on both cell shapes.")
    sys.exit(0)


if __name__ == "__main__":
    main()
