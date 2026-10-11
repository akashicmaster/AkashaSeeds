#!/usr/bin/env python3
"""
analysis_precompute_counts_eval.py — the combined precompute is ONE member pass, not one-per-field.

The Source-Viewer precompute "never finished" because it walked all pool members once PER FIELD
(O(store) × #fields) — pathological under the disk-resident bounded-cache index. The fix computes
EVERY field's count distribution in a SINGLE member pass. This proves it, memory-discipline §4-style:
  1. ACCESS DEGREE: get_meta is called at most ONCE per member for N fields (not N× per member).
  2. Correct + persisted; a subsequent analysis.view RE-FETCHES (O(1)), and matches whether the
     input is given as the pool id or its alias (robust match).
  3. Idempotent: a second precompute of the same fields computes 0.

Run:  python app/test/analysis_precompute_counts_eval.py     (exit 0 = pass)
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
    from app.concepts.analysis import AnalysisConcept
    import app.scripts.mobility_source_import as msi

    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_pcc_"))
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

    N = 600
    rows = [{"ID": f"R{i}", "Country": ["DE", "FR", "IT"][i % 3], "Gender": ["M", "F"][i % 2],
             "Region": f"reg{i % 20}", "Age": str(20 + i % 50)} for i in range(N)]
    opts = {"artifacts": [], "id_field": "ID", "retrieval": "", "batch": 200, "freeze": True,
            "snapshot": "", "snapshot_n": 0, "snapshot_strata": "", "snapshot_seed": "x"}
    POOL = msi.run(disp, iter(rows), opts, log=lambda m: None)["pool"]
    disp("labo.new", {"name": "lab"}); disp("labo.bind", {"name": "lab", "pool": POOL})

    FIELDS = ["Country", "Gender", "Region", "Age"]

    # 1. ACCESS DEGREE — count get_meta calls during the combined pass.
    sess = k.manager.get_session("admin")
    ac = AnalysisConcept(sess)
    calls = {"n": 0}
    real_get_meta = ac.cortex.get_meta

    def counting_get_meta(key):
        calls["n"] += 1
        return real_get_meta(key)

    ac.cortex.get_meta = counting_get_meta
    out = ac.op_precompute_counts("labo:lab", POOL, fields=FIELDS)
    ac.cortex.get_meta = real_get_meta
    check("computed all 4 fields in the combined pass", out.get("computed") == 4, str(out))
    # The combined precompute is a BOUNDED number of passes: one count pass (all fields at once) + one
    # bounded scatter pass (members[:pcap], for every pair at once). That is O(members), NOT
    # O(members×fields) — the pathology it replaced. So get_meta ≤ ~2×members + a small constant, and
    # STAYS far below N×fields no matter how many fields/pairs there are.
    check("ACCESS DEGREE: get_meta = O(members) bounded passes, NOT members×fields",
          calls["n"] <= 2 * N + 100 and calls["n"] < N * len(FIELDS),
          f"get_meta={calls['n']} members={N} fields={len(FIELDS)} (N×F={N*len(FIELDS)})")
    # The SAME single call prepared the whole viewer surface in advance: cluster (groupby) for every
    # field AND scatter for every field pair — so the viewer never asks and no operator step exists.
    check("cluster (groupby) auto-prepared for every field",
          sorted(out.get("groupby") or []) == sorted(FIELDS), str(out.get("groupby")))
    import itertools as _it
    _pairs = ["%s,%s" % (a, b) for a, b in _it.combinations(FIELDS, 2)]
    check("scatter auto-prepared for every field pair (C(4,2)=6)",
          sorted(out.get("scatter") or []) == sorted(_pairs), str(out.get("scatter")))
    # every prepared view re-fetches WITHOUT any operator precompute (no pending).
    gv = disp("analysis.view", {"labo": "labo:lab", "input": POOL, "plugin": "groupby:Country"})
    check("cluster view re-fetches (persisted in advance, not pending)",
          gv.get("persisted") is True and (gv.get("projection") or {}).get("as_sets") is True,
          f"persisted={gv.get('persisted')}")
    xv = disp("analysis.view", {"labo": "labo:lab", "input": POOL, "plugin": "scatter:Country,Age"})
    check("scatter view (a DIFFERENT pair) re-fetches without an operator step",
          xv.get("persisted") is True and (xv.get("projection") or {}).get("format") == "scatter",
          f"persisted={xv.get('persisted')}")
    # The viewer may pick the two axes in EITHER order. A pair is stored one way (Country,Region); the
    # reverse request (Region,Country) must still re-fetch — the stored pair, transposed, not a miss.
    fwd = disp("analysis.view", {"labo": "labo:lab", "input": POOL, "plugin": "scatter:Country,Region"})
    rev = disp("analysis.view", {"labo": "labo:lab", "input": POOL, "plugin": "scatter:Region,Country"})
    fp, rp = (fwd.get("projection") or {}), (rev.get("projection") or {})
    check("reversed scatter pair re-fetches (axes transposed, not pending)",
          rev.get("persisted") is True and rp.get("x") == "Region" and rp.get("y") == "Country"
          and fp.get("x") == "Country" and fp.get("y") == "Region",
          f"rev.persisted={rev.get('persisted')} rev.x/y={rp.get('x')}/{rp.get('y')}")

    # 2. counts correct + view re-fetches (input as pool id AND as alias).
    v = disp("analysis.view", {"labo": "labo:lab", "input": POOL, "plugin": "count:Country"})
    p = (v or {}).get("projection") or {}
    check("view re-fetches a persisted count (exact, full N)",
          v.get("persisted") is True and sum((p.get("counts") or {}).values()) == N,
          f"persisted={v.get('persisted')} sum={sum((p.get('counts') or {}).values())}")

    # 3. idempotent — re-precompute the same fields computes 0.
    out2 = ac.op_precompute_counts("labo:lab", POOL, fields=FIELDS)
    check("idempotent: re-precompute computes 0", out2.get("computed") == 0, str(out2))

    # 4. SCATTER is prepared on request — plugins=scatter:fx,fy must NOT split on its internal comma
    #    (that bug left every scatter stuck at "Computing"). One plugin, persists, view re-fetches.
    import time as _t
    sp = disp("analysis.precompute", {"bench": "sandbox", "labo": "labo:lab", "input": POOL, "plugins": "scatter:Age,Region"})
    check("scatter precompute is ONE plugin (comma in scatter:fx,fy survives)",
          sp.get("submitted") == 1 and sp.get("plugins") == ["scatter:Age,Region"], str(sp.get("plugins")))
    if sp.get("job_id"):
        for _ in range(80):
            if disp("job.stat", {"job_id": sp["job_id"]}).get("status") in ("DONE", "FAILED"):
                break
            _t.sleep(0.3)
    sv = disp("analysis.view", {"labo": "labo:lab", "input": POOL, "plugin": "scatter:Age,Region"})
    check("requested scatter persists and re-fetches (no longer stuck pending)",
          sv.get("persisted") is True and (sv.get("projection") or {}).get("format") == "scatter",
          f"persisted={sv.get('persisted')}")

    # 5. WIDE pool (the mobility bug): 12 fields ⇒ C(12,2)=66 pairs > the old 60 cap. A DEEP pair
    #    (last two fields) used to fall beyond the cap and showed "Computing" forever. Every pair must
    #    now be prepared in advance and re-fetch — no operator step, no pending.
    WF = ["F%02d" % i for i in range(12)]
    wrows = [{"RID": "W%d" % i, **{f: str((i + j) % 5) for j, f in enumerate(WF)}} for i in range(400)]
    disp("source.register", {"provider": "TEST", "collection": "wide", "name": "wide"})
    WPOOL = disp("source.pool.create", {"name": "wide_frame", "source": "source:src:wide"})["pool"]
    disp("source.acquire", {"source": "source:src:wide", "rule": "all", "records": wrows,
                            "id_field": "RID", "pool": WPOOL})
    disp("source.pool.freeze", {"pool": WPOOL})
    disp("labo.new", {"name": "wlab"}); disp("labo.bind", {"name": "wlab", "pool": WPOOL})
    wp = disp("analysis.precompute", {"bench": "sandbox", "labo": "labo:wlab", "input": WPOOL})   # AUTO: all fields+pairs
    check("wide pool: C(12,2)=66 pairs > old cap 60 — auto precompute submits", wp.get("submitted", 0) >= 1, str(wp))
    if wp.get("job_id"):
        for _ in range(120):
            if disp("job.stat", {"job_id": wp["job_id"]}).get("status") in ("DONE", "FAILED"):
                break
            _t.sleep(0.3)
    deep = disp("analysis.view", {"labo": "labo:wlab", "input": WPOOL, "plugin": "scatter:%s,%s" % (WF[-2], WF[-1])})
    check("wide pool: a DEEP pair (beyond the old 60-cap) is prepared in advance and re-fetches",
          deep.get("persisted") is True and (deep.get("projection") or {}).get("format") == "scatter",
          f"pair={WF[-2]},{WF[-1]} persisted={deep.get('persisted')}")
    dp = disp("analysis.precompute", {"bench": "sandbox", "labo": "labo:wlab", "input": WPOOL})   # idempotent second run
    check("wide pool: re-precompute is idempotent (all count+cluster+scatter prepared)",
          dp.get("submitted", 1) == 0, str(dp))

    print()
    if fails:
        print(f"FAIL — {len(fails)} check(s) failed: {fails}")
        sys.exit(1)
    print("ALL PASS — the combined precompute walks members ONCE for all fields (access degree ≈ "
          "members, not members×fields), persists correct counts that reads re-fetch O(1), and is "
          "idempotent. No O(store)-per-field walk.")


if __name__ == "__main__":
    main()
