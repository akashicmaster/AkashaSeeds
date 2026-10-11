#!/usr/bin/env python3
"""
analysis_scatter_prepared_eval.py — EVERY field pair the viewer can offer is prepared IN ADVANCE.

The Source-Viewer scatter showed "Computing…" for a selectable pair (e.g. Education × Income_level)
because the field menu offered raw columns (all of them) while the background Harmonia precompute
prepared scatter for only a capped subset — so a pair the viewer could pick had no persisted result,
and (guests may never trigger a compute) it spun forever.

The contract this pins:
  1. The viewer offers ONLY prepared fields — the fields that have a persisted `count:<field>` run.
  2. The precompute prepares a scatter for EVERY pair of those fields (invariant: the pair cap
     _max_pairs ≥ C(field_cap, 2)), so every offered pair re-fetches at once — never "Computing".
  3. A WIDE pool (>40 coded fields, like the EU Travel Survey) is fully covered by the 60-field cap.
  4. Self-heal: raising the field/pair cap on a later boot BACKFILLS the newly-eligible pairs
     (the missing/deficit portion is prepaid, never left for a read-path sweep).

Run:  python app/test/analysis_scatter_prepared_eval.py     (exit 0 = pass)
"""
import hashlib
import itertools
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
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_scat_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def disp(method, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
        return r.get("result") if "result" in r else {"__error__": r.get("error")}

    def drain(deadline_s=600.0):
        """Wait for the background precompute to finish — by WALL CLOCK, not by iteration count.

        This used to be `for _ in range(300): sleep(0.2)` — a 60 s ceiling that was ample alone and
        not ample when the suite runs several evals in parallel: the job was still fanning out the
        990 scatter pairs, so the eval read a half-prepared pool and reported `missing=84` as if the
        policy had dropped them. A test that measures how busy the box is, is measuring the wrong
        thing. It still returns the moment the queue is empty, so the fast path costs nothing."""
        t0 = time.time()
        while time.time() - t0 < deadline_s:
            jobs = disp("job.ls", {}).get("jobs") or []
            if not [j for j in jobs if j.get("status") in ("PENDING", "RUNNING")]:
                return
            time.sleep(0.2)
        print("  ----  drain: background jobs still running after %.0fs" % deadline_s)

    fails = []

    def check(name, ok, detail=""):
        print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
        if not ok:
            fails.append(name)

    # A WIDE survey-like pool: 45 coded CATEGORY fields (> the old 40 cap) + categorically-MEANINGLESS
    # columns (a unique id, a date, a serial, free text) that the policy must exclude, 300 rows.
    NF = 45
    FIELDS = ["Education", "Income_level"] + ["F%02d" % i for i in range(NF - 2)]
    rows = [dict({"ID": "R%d" % i,
                  "survey_date": "2014-%02d-%02d" % (1 + i % 12, 1 + i % 28),   # date NAME → excluded
                  "serial_no": str(10000 + i),                                  # near-unique → excluded
                  "free_text": "unique remark %d / %d" % (i, i * 7)},           # near-unique → excluded
                 **{f: "v%d" % ((i + j) % 4) for j, f in enumerate(FIELDS)}) for i in range(300)]
    opts = {"artifacts": [], "id_field": "ID", "retrieval": "", "batch": 200, "freeze": True,
            "snapshot": "", "snapshot_n": 0, "snapshot_strata": "", "snapshot_seed": "x"}
    POOL = msi.run(disp, iter(rows), opts, log=lambda m: None)["pool"]
    disp("labo.new", {"name": "lab"})
    disp("labo.bind", {"name": "lab", "pool": POOL})

    # AUTO precompute (the boot-scheduler path) + drain the background job.
    sub = disp("analysis.precompute", {"bench": "sandbox", "labo": "labo:lab", "input": POOL})
    check("auto precompute submitted a background job", bool(sub.get("submitted")), str(sub.get("job_id")))
    drain()

    # (1) the viewer's field menu = prepared CATEGORY fields (count:<field> with categorical != false).
    runs = disp("analysis.runs", {"labo": "labo:lab"}).get("runs") or []
    gui_fields = sorted({(R.get("plugin") or "")[6:] for R in runs
                         if (R.get("plugin") or "").startswith("count:") and R.get("categorical") is not False})
    noncat = sorted({(R.get("plugin") or "")[6:] for R in runs
                     if (R.get("plugin") or "").startswith("count:") and R.get("categorical") is False})
    check("every MEANINGFUL category field is computed (all 45), none dropped by a count cap",
          len(gui_fields) == 45 and "Education" in gui_fields and "Income_level" in gui_fields,
          "prepared=%d" % len(gui_fields))
    check("categorically-MEANINGLESS fields are excluded (id/date by name; serial/free-text by cardinality)",
          "ID" not in gui_fields and "survey_date" not in gui_fields
          and "serial_no" not in gui_fields and "free_text" not in gui_fields
          and set(noncat) <= {"serial_no", "free_text"},
          "offered=%s noncat=%s" % (gui_fields[:0] or "45 categories", noncat))

    # (2)+(3) EVERY pair of offered fields re-fetches a persisted scatter — never pending.
    def scatter_ready(a, b):
        v = disp("analysis.view", {"labo": "labo:lab", "input": POOL, "plugin": "scatter:%s,%s" % (a, b)})
        return isinstance(v, dict) and v.get("projection") is not None and not v.get("pending")

    pairs = list(itertools.combinations(gui_fields, 2))
    missing = [(a, b) for a, b in pairs if not scatter_ready(a, b)]
    check("EVERY viewer-selectable pair has a prepared scatter (no 'Computing')",
          not missing, "pairs=%d missing=%d%s" % (len(pairs), len(missing),
                                                  (" e.g. %s" % (missing[:3],)) if missing else ""))

    # the exact pair from the report, both orderings (transpose re-fetch)
    check("Education × Income_level is prepared (and the reversed order too)",
          scatter_ready("Education", "Income_level") and scatter_ready("Income_level", "Education"))

    # (4) CONVERGENCE — a 2nd precompute submits nothing: the excluded date/serial/id columns must not
    # keep the pool "pending" and re-walk every boot (run once, then re-fetch forever).
    again = disp("analysis.precompute", {"bench": "sandbox", "labo": "labo:lab", "input": POOL})
    check("re-precompute is a no-op — excluded fields never keep it pending (runs once)",
          again.get("submitted") == 0, str(again.get("note")))

    print("\nRESULT:", "PASS" if not fails else "FAIL — " + ", ".join(fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
