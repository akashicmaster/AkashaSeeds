#!/usr/bin/env python3
"""
analysis_view_bounded_eval.py — analysis.view NEVER sweeps Atoms in real time.

ABSOLUTE PRINCIPLE: a projection over a pool's members is a per-member get_meta sweep. That cost is
FORBIDDEN on the interactive/read path — it is precomputed AHEAD OF TIME in a Harmonia batch and
persisted; the read path only RE-FETCHES. This proves:
  1. Before any run, analysis.view RE-FETCHES → a miss returns pending (projection None), never a
     computed chart (no real-time sweep).
  2. analysis.run (the BATCH cost) computes the FULL population and persists it.
  3. analysis.view then re-fetches that persisted projection — exact, no sweep.
  4. analysis.precompute submits a background Harmonia job (the sanctioned cost path).

Run:  python app/test/analysis_view_bounded_eval.py     (exit 0 = pass)
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
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_avb_"))
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

    # Build a 1,200-row FROZEN source pool (3 countries) via the SAME importer the mobility boot uses.
    import app.scripts.mobility_source_import as msi
    rows = [{"ID": f"R{i}", "country": ["DE", "FR", "IT"][i % 3]} for i in range(1200)]
    opts = {"artifacts": [], "id_field": "ID", "retrieval": "", "batch": 300, "freeze": True,
            "snapshot": "", "snapshot_n": 0, "snapshot_strata": "", "snapshot_seed": "x"}
    out = msi.run(disp, iter(rows), opts, log=lambda m: None)
    POOL = out["pool"]
    disp("labo.new", {"name": "lab"})
    disp("labo.bind", {"name": "lab", "pool": POOL})

    # 0. freeze precomputed the by-status tally → source.status RE-FETCHES it (no member sweep).
    st = disp("source.status", {"pool": POOL})
    check("source.status re-fetches a precomputed by_status (no read-path sweep)",
          st.get("by_status") is not None and st.get("total") == 1200,
          f"total={st.get('total')} by_status={st.get('by_status')}")

    # 1. Un-precomputed field → analysis.view is RE-FETCH ONLY → pending, NO projection (no sweep).
    v = disp("analysis.view", {"labo": "labo:lab", "input": POOL, "plugin": "count:country"})
    check("view of un-precomputed field returns pending, not a computed chart",
          v.get("persisted") is False and v.get("pending") is True and v.get("projection") is None,
          f"persisted={v.get('persisted')} pending={v.get('pending')} proj={v.get('projection') is not None}")

    # 2. analysis.run = the BATCH cost → computes the FULL pool + persists.
    run = disp("analysis.run", {"labo": "labo:lab", "input": POOL, "plugin": "count:country"})
    rproj = (run or {}).get("projection") or {}
    check("analysis.run counts the FULL pool (1200), no sampling",
          sum((rproj.get("counts") or {}).values()) == 1200 and rproj.get("input_size") == 1200,
          f"sum={sum((rproj.get('counts') or {}).values())} input_size={rproj.get('input_size')}")

    # 3. view now RE-FETCHES the persisted projection — exact, zero sweep.
    v2 = disp("analysis.view", {"labo": "labo:lab", "input": POOL, "plugin": "count:country"})
    p2 = (v2 or {}).get("projection") or {}
    check("view re-fetches the PERSISTED projection (exact, no recompute)",
          v2.get("persisted") is True and sum((p2.get("counts") or {}).values()) == 1200,
          f"persisted={v2.get('persisted')} sum={sum((p2.get('counts') or {}).values())}")

    # 3b. analysis.run is IDEMPOTENT / recompute-free — a second run re-fetches, mints no new run.
    runs_before = len((disp("analysis.runs", {"labo": "labo:lab"}) or {}).get("runs", []))
    run2 = disp("analysis.run", {"labo": "labo:lab", "input": POOL, "plugin": "count:country"})
    runs_after = len((disp("analysis.runs", {"labo": "labo:lab"}) or {}).get("runs", []))
    check("analysis.run is idempotent (reused, no duplicate run atom)",
          run2.get("reused") is True and runs_after == runs_before,
          f"reused={run2.get('reused')} before={runs_before} after={runs_after}")

    # 4. analysis.precompute submits a background Harmonia job for a NEW field, and the JCL worker
    #    actually computes + persists it → analysis.view then re-fetches it (end-to-end batch path).
    import time as _t
    pc = disp("analysis.precompute", {"bench": "sandbox", "labo": "labo:lab", "input": POOL, "plugins": "groupby:country"})
    check("analysis.precompute submits a background batch job",
          isinstance(pc, dict) and pc.get("job_id") and pc.get("submitted", 0) >= 1,
          f"job_id={pc.get('job_id')} submitted={pc.get('submitted')}")
    persisted = False
    for _ in range(60):
        gv = disp("analysis.view", {"labo": "labo:lab", "input": POOL, "plugin": "groupby:country"})
        if gv.get("persisted"):
            persisted = True
            break
        _t.sleep(0.5)
    check("the Harmonia batch computed + persisted it; view re-fetches (no read-path sweep)",
          persisted, "waited for JCL worker")

    # 4b. re-running precompute for the SAME field submits nothing (already persisted → idempotent).
    pc2 = disp("analysis.precompute", {"bench": "sandbox", "labo": "labo:lab", "input": POOL, "plugins": "groupby:country"})
    check("precompute is idempotent (skips already-persisted → 0 submitted)",
          isinstance(pc2, dict) and pc2.get("submitted", 0) == 0 and pc2.get("already_persisted", 0) >= 1,
          f"submitted={pc2.get('submitted')} already={pc2.get('already_persisted')}")

    # 4c. WRITE-STORM GUARD: groupby on a HIGH-CARDINALITY field must NOT materialize a Set per value
    #     (that flooded the WriteQueue and blocked reads → "Load failed"). ID is unique across 1200.
    gid = disp("analysis.run", {"labo": "labo:lab", "input": POOL, "plugin": "groupby:ID"})
    check("groupby on a unique field materializes NO Set storm (capped)",
          len(gid.get("output_sets", [])) == 0 and (gid.get("projection") or {}).get("sets_skipped") is True,
          f"sets={len(gid.get('output_sets', []))}")
    # and the persisted distribution atom is bounded (top-N), not a 1200-entry blob.
    cid = disp("analysis.run", {"labo": "labo:lab", "input": POOL, "plugin": "count:ID"})
    cidp = cid.get("projection") or {}
    check("count on a unique field stores a BOUNDED top-N (not the full 1200 distinct)",
          cidp.get("row_count", 9999) <= 500 and cidp.get("distinct") == 1200 and cidp.get("truncated") is True,
          f"rows={cidp.get('row_count')} distinct={cidp.get('distinct')}")

    # 4d. OOM GUARD: auto-precompute must not walk image metadata (it drove the daemon to ~4 GB RSS
    #     → OOM-kill → boot churn). RETIRED 2026-09-20: this used to assert the whole pool is
    #     skipped with the coded reason `media_pool`. That wholesale skip was DELIBERATELY replaced
    #     (lib/akasha/source/ops.py) — it also killed the categorical analysis of image/audio
    #     datasets that carry meaningful columns (the museum corpus's department / culture /
    #     technique). The policy now excludes the media-TECHNICAL columns and keeps the categorical
    #     ones; the member-count guard bounds the walk. So the guard is asserted where it now lives:
    #     an all-technical image pool prepares nothing, and a media pool with a real category does.
    disp("source.register", {"provider": "British Library", "collection": "book images", "name": "bl"})
    disp("source.pool.create", {"name": "blimg", "source": "source:src:bl", "rule": "all"})
    disp("source.acquire", {"source": "source:src:bl", "rule": "all", "id_field": "record_id",
                            "pool": "source:pool:blimg:v1",
                            "records": [{"record_id": f"img{i}", "media_type": "image/jpeg",
                                         "dataset_id": "biglam/bl", "image_type": "plates"} for i in range(40)]})
    disp("source.pool.freeze", {"pool": "source:pool:blimg:v1"})
    disp("labo.new", {"name": "bllab"}); disp("labo.bind", {"name": "bllab", "pool": "source:pool:blimg:v1"})
    im = disp("analysis.precompute", {"bench": "sandbox", "labo": "labo:bllab", "input": "source:pool:blimg:v1"})
    check("auto-precompute walks NOTHING on an all-technical image pool (OOM guard)",
          im.get("submitted") == 0, str(im))
    # …and the same policy still prepares a MEDIA pool that carries a real category, which is why
    # the wholesale skip was dropped (the museum corpus: images with department / culture).
    disp("source.register", {"provider": "Museum", "collection": "objects", "name": "mus"})
    disp("source.pool.create", {"name": "musimg", "source": "source:src:mus", "rule": "all"})
    disp("source.acquire", {"source": "source:src:mus", "rule": "all", "id_field": "record_id",
                            "pool": "source:pool:musimg:v1",
                            "records": [{"record_id": f"obj{i}", "media_type": "image/jpeg",
                                         "department": ["prints", "textiles"][i % 2],
                                         "culture": ["french", "japanese"][i % 2]} for i in range(40)]})
    disp("source.pool.freeze", {"pool": "source:pool:musimg:v1"})
    disp("labo.new", {"name": "muslab"}); disp("labo.bind", {"name": "muslab", "pool": "source:pool:musimg:v1"})
    mu = disp("analysis.precompute", {"bench": "sandbox", "labo": "labo:muslab", "input": "source:pool:musimg:v1"})
    check("…while a media pool WITH a categorical field is still prepared (department / culture)",
          (mu.get("submitted") or 0) >= 1, str(mu))

    # 5. a GUEST cannot precompute (it enqueues a job — operator/librarian only).
    g = k.dispatch({"jsonrpc": "2.0", "method": "session.guest.create", "params": {}, "id": "gg"}, "network")
    gtok = ((g or {}).get("result") or {}).get("session_token")
    gp = k.dispatch({"jsonrpc": "2.0", "method": "analysis.precompute",
                     "params": {"session_token": gtok, "data": {"labo": "labo:lab", "input": POOL, "fields": "country"}},
                     "id": "gp"}, "network")
    check("guest is denied analysis.precompute (no background-job escalation)",
          "error" in gp, str(gp.get("result") or gp.get("error")))

    print()
    if fails:
        print(f"FAIL — {len(fails)} check(s) failed: {fails}")
        sys.exit(1)
    print("ALL PASS — analysis.view is re-fetch-only (pending before precompute, exact after), the "
          "full-member walk lives only in analysis.run/precompute (Harmonia batch), and source.status "
          "re-fetches a freeze-precomputed tally. No real-time Atom sweep on any read path.")


if __name__ == "__main__":
    main()
