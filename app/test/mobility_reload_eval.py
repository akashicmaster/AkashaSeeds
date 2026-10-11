#!/usr/bin/env python3
"""
mobility_reload_eval.py — a CORRECTED corpus reloads cleanly (fenced reset + re-import).

A frozen pool + idempotent-by-alias atoms can't be updated in place, so when the bundled corpus
CONTENT changes (e.g. the mojibake encoding fix) the mobility bootstrap RESETS the corpus and
re-imports corrected data under the same ids. This proves the primitives that make that safe:
  1. source.op_reset(source) drops ONLY that source's items/pool/acquisitions — another source is
     untouched (fenced).
  2. analysis.reset_labo(labo) drops the labo's persisted runs (so precompute recomputes).
  3. After reset + re-import, the SAME pool id holds CORRECTED values, and a fresh analysis.run
     reflects them (no stale re-fetch).

Run:  python app/test/mobility_reload_eval.py     (exit 0 = pass)
"""
import hashlib
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"


def main():
    from lib.akasha.kernel import KernelDispatcher
    from lib.akasha.concepts.source import SourceDataLayer
    from app.concepts.analysis import AnalysisConcept
    import app.scripts.mobility_source_import as msi

    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_reload_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def disp(method, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
        return r.get("result") if "result" in r else {"__error__": r.get("error")}

    fails = []

    def check(name, ok, detail=""):
        print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
        if not ok:
            fails.append(name)

    sess = k.manager.get_session("admin")
    src = "source:src:mobility_eu_travel_survey_2014"
    opts = lambda: {"artifacts": [], "id_field": "ID", "retrieval": "", "batch": 200, "freeze": True,
                    "snapshot": "", "snapshot_n": 0, "snapshot_strata": "", "snapshot_seed": "x"}

    # v1 — a "corrupted" corpus (Region has the replacement char).
    rows_bad = [{"ID": f"R{i}", "Region": "Jihov�chod" if i % 2 else "N�rte"} for i in range(600)]
    outA = msi.run(disp, iter(rows_bad), opts(), log=lambda m: None)
    POOL = outA["pool"]
    disp("labo.new", {"name": "mobility"}); disp("labo.bind", {"name": "mobility", "pool": POOL})
    runA = disp("analysis.run", {"labo": "labo:mobility", "input": POOL, "plugin": "count:Region"})
    bad_vals = set((runA.get("projection") or {}).get("counts", {}).keys())
    check("v1 imported with corrupted Region values", any("�" in v for v in bad_vals), str(bad_vals))

    # A SECOND, unrelated source — must survive the mobility reset (fence).
    disp("source.register", {"provider": "British Library", "collection": "imgs", "name": "bl"})
    disp("source.pool.create", {"name": "blp", "source": "source:src:bl", "rule": "all"})
    disp("source.acquire", {"source": "source:src:bl", "rule": "all", "id_field": "record_id",
                            "pool": "source:pool:blp:v1",
                            "records": [{"record_id": f"b{i}", "kind": "img"} for i in range(20)]})
    bl_before = disp("source.status", {"pool": "source:pool:blp:v1"}).get("total")

    # ── RESET (fenced) + analysis reset ──
    r = SourceDataLayer(sess).op_reset(source=src)
    AnalysisConcept(sess).reset_labo("labo:mobility")
    dropped = r.get("dropped", {})
    check("op_reset dropped mobility items + pool", dropped.get("items", 0) == 600 and dropped.get("pools", 0) >= 1,
          str(dropped))
    check("mobility pool is GONE after reset",
          "__error__" in disp("source.status", {"pool": POOL}) or
          disp("source.status", {"pool": POOL}).get("total") == 0)
    check("mobility analysis runs are GONE after reset",
          len((disp("analysis.runs", {"labo": "labo:mobility"}) or {}).get("runs", [])) == 0)
    bl_after = disp("source.status", {"pool": "source:pool:blp:v1"}).get("total")
    check("the OTHER source is UNTOUCHED (fenced reset)", bl_after == bl_before == 20, f"{bl_before}->{bl_after}")

    # ── RE-IMPORT corrected corpus under the SAME ids ──
    rows_good = [{"ID": f"R{i}", "Region": "Jihovýchod" if i % 2 else "Norte"} for i in range(600)]
    outB = msi.run(disp, iter(rows_good), opts(), log=lambda m: None)
    check("re-import lands the SAME pool id", outB["pool"] == POOL, f"{outB['pool']}")
    runB = disp("analysis.run", {"labo": "labo:mobility", "input": POOL, "plugin": "count:Region"})
    good_vals = set((runB.get("projection") or {}).get("counts", {}).keys())
    check("corrected values present, NO replacement char",
          "Jihovýchod" in good_vals and not any("�" in v for v in good_vals), str(good_vals))
    check("re-import members == 600 (fresh, not duplicated)",
          disp("source.status", {"pool": POOL}).get("total") == 600,
          str(disp("source.status", {"pool": POOL}).get("total")))

    print()
    if fails:
        print(f"FAIL — {len(fails)} check(s) failed: {fails}")
        sys.exit(1)
    print("ALL PASS — a corrected corpus reloads cleanly: fenced reset drops only the target source + "
          "its analysis runs, the re-import restores the same pool id with corrected (non-mojibake) "
          "values, and unrelated sources are untouched.")


if __name__ == "__main__":
    main()
