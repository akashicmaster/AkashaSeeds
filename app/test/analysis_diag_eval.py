#!/usr/bin/env python3
"""
analysis_diag_eval.py — analysis.diag turns a blank chart into a diagnosis.

When a Source-Viewer or Visual-Curation chart is empty and `job.ls` shows nothing, there was no way
to tell a BUG from a LIBRARY-fetch error from still-COMPUTING. `analysis.diag` is the one readout
that answers it: boot-phase states, the analysis/vlab job queue, an optional-library import probe,
and each pool's prepared-counts readiness — with a plain verdict per subject.

Pins:
  1. the four evidence lanes are present (phases / jobs / libraries / subjects) + an overall verdict;
  2. the library probe reflects reality (numpy is importable in this env → True; a bogus never → is
     not claimed present) — this is the 'library error' signal;
  3. a pool with prepared counts reads READY; before precompute it does NOT read READY;
  4. it is a READ (admin/librarian) and never raises.

Run:  python app/test/analysis_diag_eval.py     (exit 0 = pass)
"""
import hashlib
import os
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"


def main():
    from lib.akasha.kernel import KernelDispatcher
    import app.scripts.mobility_source_import as msi

    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_diag_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def disp(method, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
        return r.get("result") if "result" in r else {"__error__": r.get("error")}

    def drain():
        for _ in range(200):
            if not [j for j in (disp("job.ls", {}).get("jobs") or []) if j.get("status") in ("PENDING", "RUNNING")]:
                return
            time.sleep(0.2)

    fails = []

    def check(name, ok, detail=""):
        print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
        if not ok:
            fails.append(name)

    # (1) the four lanes + verdict
    d0 = disp("analysis.diag", {})
    check("returns the four evidence lanes + a verdict",
          all(kk in d0 for kk in ("phases", "job_summary", "libraries", "subjects", "verdict")),
          "keys=%s" % sorted(d0.keys())[:8])

    # (2) library probe reflects reality
    libs = d0.get("libraries") or {}
    check("library probe reports numpy True (it is importable here) — the 'library error' signal",
          libs.get("numpy") is True and "tensorflow" in libs, "libs=%s" % libs)

    # a mobility-like pool, then precompute
    rows = [{"ID": "R%d" % i, "Country": ["DE", "FR", "IT"][i % 3], "Gender": ["M", "F"][i % 2],
             "Education": ["A", "B", "C"][i % 3]} for i in range(200)]
    opts = {"artifacts": [], "id_field": "ID", "retrieval": "", "batch": 200, "freeze": True,
            "snapshot": "", "snapshot_n": 0, "snapshot_strata": "", "snapshot_seed": "x"}
    POOL = msi.run(disp, iter(rows), opts, log=lambda m: None)["pool"]
    disp("labo.new", {"name": "mobility"})
    disp("labo.bind", {"name": "mobility", "pool": POOL})

    # (3a) before precompute the pool must NOT read READY
    def pool_verdict(dg):
        for s in dg.get("subjects", []):
            if s.get("pool") == POOL:
                return s.get("verdict", "")
        return ""
    before = pool_verdict(disp("analysis.diag", {}))
    check("before precompute the pool does not read READY", not before.startswith("READY"), before)

    disp("analysis.precompute", {"bench": "sandbox", "labo": "labo:mobility", "input": POOL})
    drain()

    # (3b) after precompute + drain → READY, with counts reported
    after = pool_verdict(disp("analysis.diag", {}))
    check("after precompute the pool reads READY (counts prepared)", after.startswith("READY"), after)

    # (4) never raises, and reports the visual-curation lane too
    d2 = disp("analysis.diag", {})
    check("visual-curation lane present with a verdict",
          isinstance(d2.get("visual_curation"), dict) and bool(d2["visual_curation"].get("verdict")),
          str(d2.get("visual_curation", {}).get("verdict"))[:60])

    print("\nRESULT:", "PASS" if not fails else "FAIL — " + ", ".join(fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
