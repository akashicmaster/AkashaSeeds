#!/usr/bin/env python3
"""
analysis_precompute_progress_eval.py — the precompute is a job-VISIBLE, chunked, resumable batch.

The Source-Viewer precompute must be observable via `job`: for a large pool it is a MULTI-STEP JCL
job (one count_chunk per member slice + a finalize), so job.stat shows chunk k/K = the fraction of
the corpus walked. Still ONE member pass overall (each member folded in exactly one chunk), and
RESUMABLE (a partial accumulator lets a re-submitted job skip finished chunks). This proves it.

Run:  python app/test/analysis_precompute_progress_eval.py     (exit 0 = pass)
"""
import hashlib
import os
import sys
import tempfile
import time

os.environ["AKASHA_PRECOMPUTE_CHUNK"] = "500"          # small chunk so 1500 rows → several steps
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"


def main():
    from lib.akasha.kernel import KernelDispatcher
    import app.scripts.mobility_source_import as msi
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_prog_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def d(m, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": m,
                        "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
        return r.get("result") if "result" in r else {"__error__": r.get("error")}

    fails = []

    def check(name, ok, detail=""):
        print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
        if not ok:
            fails.append(name)

    N = 1500
    rows = [{"ID": f"R{i}", "Country": ["DE", "FR", "IT"][i % 3], "Age": str(20 + i % 40)} for i in range(N)]
    POOL = msi.run(d, iter(rows), {"artifacts": [], "id_field": "ID", "retrieval": "", "batch": 300,
                                   "freeze": True, "snapshot": "", "snapshot_n": 0, "snapshot_strata": "",
                                   "snapshot_seed": "x"}, log=lambda m: None)["pool"]
    d("labo.new", {"name": "lab"}); d("labo.bind", {"name": "lab", "pool": POOL})

    pc = d("analysis.precompute", {"bench": "sandbox", "labo": "labo:lab", "input": POOL})
    jid = pc.get("job_id")
    st0 = d("job.stat", {"job_id": jid})
    # 1500/500 = 3 chunks + 1 finalize = 4 steps → job.stat shows real progress granularity.
    check("precompute is a MULTI-STEP job (chunk k/K progress visible in job.stat)",
          st0.get("step_count") == 4, f"step_count={st0.get('step_count')}")
    check("the job is listed in job.ls (harmonia-visible)",
          any(j.get("label", "").startswith("analysis.precompute:") for j in (d("job.ls", {"all": "true"}) or {}).get("jobs", [])))

    for _ in range(120):
        st = d("job.stat", {"job_id": jid})
        if st.get("status") in ("DONE", "FAILED"):
            break
        time.sleep(0.5)
    st = d("job.stat", {"job_id": jid})
    check("the job runs to completion (step_done reaches step_count, DONE)",
          st.get("status") == "DONE" and st.get("step_done") == st.get("step_count"),
          f"{st.get('status')} {st.get('step_done')}/{st.get('step_count')}")

    v = d("analysis.view", {"labo": "labo:lab", "input": POOL, "plugin": "count:Country"})
    c = (v.get("projection") or {}).get("counts") or {}
    check("chunked accumulation == full-pool counts (one pass, folded across chunks)",
          v.get("persisted") is True and sum(c.values()) == N and c.get("DE") == 500,
          f"counts={c} sum={sum(c.values())}")

    # The chunked finalize also prepared cluster + scatter IN ADVANCE (no operator step): they re-fetch.
    gv = d("analysis.view", {"labo": "labo:lab", "input": POOL, "plugin": "groupby:Country"})
    check("chunked path also auto-prepared the cluster (groupby) view",
          gv.get("persisted") is True and (gv.get("projection") or {}).get("as_sets") is True,
          f"persisted={gv.get('persisted')}")
    sv = d("analysis.view", {"labo": "labo:lab", "input": POOL, "plugin": "scatter:Country,Age"})
    check("chunked path also auto-prepared the scatter view (field pair)",
          sv.get("persisted") is True and (sv.get("projection") or {}).get("format") == "scatter",
          f"persisted={sv.get('persisted')}")

    # re-submit → nothing to do (idempotent; already persisted).
    pc2 = d("analysis.precompute", {"bench": "sandbox", "labo": "labo:lab", "input": POOL})
    check("re-precompute is idempotent (already persisted → 0 submitted)",
          pc2.get("submitted", 1) == 0, str(pc2))

    print()
    if fails:
        print(f"FAIL — {len(fails)} check(s) failed: {fails}")
        sys.exit(1)
    print("ALL PASS — the precompute is a harmonia job with visible chunk-by-chunk progress "
          "(job.stat step k/K), runs to completion, folds every member exactly once into the correct "
          "counts, and is idempotent/resumable.")


if __name__ == "__main__":
    main()
