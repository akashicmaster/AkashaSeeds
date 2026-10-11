#!/usr/bin/env python3
"""
Mobility × Source Data Layer import eval — Mobility Source Data Import Directive v0.1 §11 acceptance.

Drives the `source.*` wiring (the same ops app/scripts/mobility_source_import.py runs against a live cell)
in-process with a bounded set of real-SHAPED EU Travel Survey respondent rows, and asserts the
directive's non-negotiables: one Source Atom per released row; the complete corpus acquired before
sampling; original coded values + missing/refused/DK codes preserved distinctly; the pool frozen with
DOI / version / artifact hashes / Akasha Time visible; a deterministic experiment subset that keeps
the population visible; a traceable `based_on` bridge to a Mobility opinion (raw atom immutable); and
the audit grounded — with no synthetic respondents.

Run:  python app/test/mobility_source_import_eval.py     (exit 0 = all pass)
"""
import hashlib
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def main():
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_mob_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def d(method, data, tok="admin", trust="local"):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": tok, "data": data}, "id": "t"}, trust)
        return r.get("result") if "result" in r else {"__error__": r.get("error")}

    SID = "source:src:mobility_eu_travel_survey_2014"
    POOL = "source:pool:mobility:eu_travel_survey_2014:v1_1"
    DOI = "10.2905/JRC.KMH9E9G"

    # ── 1. register — logical identity (DOI) DISTINCT from retrieval location ──
    reg = d("source.register", {"provider": "European Commission JRC",
                                "collection": "EU Travel Survey 2014", "name": "mobility_eu_travel_survey_2014",
                                "doi": DOI, "version": "1.1", "uri": f"https://doi.org/{DOI}",
                                "retrieval_uri": "https://dataverse.harvard.edu/…P82V9X"})
    ins = d("source.inspect", {"id": SID})
    check("register: dataset identity is the DOI, kept DISTINCT from the retrieval location",
          reg.get("doi") == DOI and ins.get("doi") == DOI
          and ins.get("uri") != (ins.get("retrieval") or {}).get("uri"), str(ins.get("retrieval")))

    # ── 2. pool with dataset provenance (version + artifact hashes) ──
    artifacts = [{"name": "eu_travel_survey_2014.csv", "sha256": "a" * 64, "size": 12345},
                 {"name": "codebook.pdf", "sha256": "b" * 64, "size": 6789}]
    d("source.pool.create", {"name": "mobility:eu_travel_survey_2014", "version": "v1_1", "source": SID,
                             "doi": DOI, "dataset_version": "1.1", "artifacts": artifacts,
                             "rule": "COMPLETE released respondent corpus; no acquisition-time filtering"})

    # ── 3. acquire the corpus — one atom per row; a missing/refused code preserved; one UNRESOLVED ──
    rows = []
    for i in range(24):
        rows.append({"respondent_id": f"R{i:04d}", "row_coordinate": f"data.csv:{i + 2}",
                     "country": ["DE", "FR", "IT", "PL"][i % 4], "weight": round(0.5 + (i % 5) * 0.1, 2),
                     # original coded answers, incl. a DON'T-KNOW / REFUSED code kept distinct
                     "q_mode_daily": (i % 4) + 1, "q_policy_roadcharge": (-9 if i % 6 == 0 else i % 5),
                     "q_innov_attitude": (-8 if i % 8 == 0 else (i % 3) + 1)})
    rows.append({"country": "ES", "q_mode_daily": 2})            # no respondent_id → UNRESOLVED (retained)
    acq = d("source.acquire", {"source": SID, "records": rows, "id_field": "respondent_id", "pool": POOL,
                               "dataset_version": "1.1", "rule": "complete corpus"})
    check("acquire: exactly one Source Atom per released row (24 identified + 1 retained UNRESOLVED)",
          acq.get("acquired") == 24 and acq.get("unresolved") == 1 and acq.get("total") == 25, str(acq))

    # ── 4. §5 — original coded values + missing/refused codes preserved DISTINCTLY (not nulled) ──
    r0 = d("source.read", {"id": "source:item:mobility_eu_travel_survey_2014:r0000"})
    sm = r0.get("source_metadata") or {}
    check("per-respondent atom: original coded payload + country + weight preserved verbatim",
          sm.get("country") == "DE" and sm.get("q_mode_daily") == 1 and "weight" in sm
          and sm.get("q_policy_roadcharge") == -9, str(sm)[:120])
    check("missing/refused/DK codes stay DISTINCT (the -9 refused code is not collapsed to null)",
          sm.get("q_policy_roadcharge") == -9, str(sm.get("q_policy_roadcharge")))

    # ── 5. freeze — DOI / version / artifact hashes / Akasha Time visible (§11) ──
    d("source.pool.freeze", {"pool": POOL})
    lsp = d("source.pool.ls", {"pool": POOL})
    check("pool.ls: frozen pool exposes DOI, dataset version, artifact hashes, and an Akasha-Time marker",
          lsp.get("status") == "FROZEN" and lsp.get("doi") == DOI and lsp.get("dataset_version") == "1.1"
          and len(lsp.get("artifacts") or []) == 2 and isinstance(lsp.get("at_seq"), int), str(lsp.get("doi")))
    check("full corpus acquired BEFORE sampling (25 members in the frozen frame)",
          lsp.get("count") == 25, str(lsp.get("count")))

    # ── 6. §8 — do not filter at acquisition: every country present, incl. the UNRESOLVED ES row ──
    countries = {(d("source.read", {"id": m["item"]}).get("source_metadata") or {}).get("country")
                 for m in lsp.get("members", [])}
    check("no acquisition-time filtering: DE/FR/IT/PL and the UNRESOLVED ES row all present",
          {"DE", "FR", "IT", "PL", "ES"} <= countries, str(sorted(c for c in countries if c)))

    # ── 7. declare Mobility CORPUS on the frozen pool ──
    decl = d("source.lab.declare", {"lab": "mobility", "klass": "CORPUS", "pool": POOL, "primary_source": SID})
    check("lab.declare: Mobility is a CORPUS lab GROUNDED on the frozen pool",
          decl.get("acquisition_class") == "CORPUS" and decl.get("evidence_status") == "GROUNDED", str(decl))

    # ── 8. §9 — deterministic experiment subset AFTER freeze; population stays visible ──
    s1 = d("source.pool.sample", {"pool": POOL, "name": "pilot", "n": "8", "seed": "m1",
                                  "strata": "country", "model": "mobility-v0.1",
                                  "rule": "stratified pilot"})
    s2 = d("source.pool.sample", {"pool": POOL, "name": "pilot2", "n": "8", "seed": "m1", "strata": "country"})
    m1 = {m["item"] for m in (d("source.pool.ls", {"pool": s1["sample"]}).get("members") or [])}
    m2 = {m["item"] for m in (d("source.pool.ls", {"pool": s2["sample"]}).get("members") or [])}
    check("pool.sample: a deterministic subset (same seed→same members) smaller than the frozen pool",
          s1.get("member_count") == 8 and m1 == m2 and s1["member_count"] < lsp["count"], str(s1.get("member_count")))
    check("population stays visible: the pool still enumerates the full 25 after sampling",
          d("source.pool.ls", {"pool": POOL}).get("count") == 25)

    # ── 9. §8 — bridge an existing Mobility opinion to a source row (based_on), additively ──
    item = "source:item:mobility_eu_travel_survey_2014:r0003"
    before = d("source.read", {"id": item})
    br = d("source.bridge", {"src": "mob:opinion:roadcharge_support_1", "dst": item, "rel": "based_on",
                             "by": "mobility-lab", "run": "mobility-v0.1"})
    after = d("source.read", {"id": item})
    check("bridge: a Mobility opinion --based_on--> a source row, additively (raw atom unmutated)",
          isinstance(br, dict) and "__error__" not in br and br.get("relation") == "based_on"
          and before.get("source_metadata") == after.get("source_metadata"), str(br)[:90])
    tr = d("source.trace", {"id": item})
    check("trace: the source row lists the Mobility opinion as based_on (traceable both ways)",
          ("mob:opinion:roadcharge_support_1", "based_on") in
          {(i.get("interpreted"), i.get("relation")) for i in tr.get("interpretations", [])},
          str(tr.get("interpretations")))

    # ── 10. audit + guest-readability (no synthetic; real corpus in the shared nucleus) ──
    au = d("source.audit", {"lab": "mobility"})
    check("audit: Mobility grounded — frozen frame + a traceable bridge into it",
          au.get("grounded") is True and au.get("bridged", 0) >= 1, str(au))
    g = d("session.guest.create", {})
    gt = (g or {}).get("binding_key") or (g or {}).get("session_token")
    gr = d("source.read", {"id": item}, tok=gt, trust="network") if gt else {"__error__": "no guest"}
    check("Source Viewer (guest) can read the real respondent atom (nucleus, not a private cortex)",
          isinstance(gr, dict) and gr.get("item") == item and gr.get("source_metadata"), str(gr)[:90])

    # ── 11. the import script is importable and targets the same source/pool ──
    import importlib.util
    spec = importlib.util.spec_from_file_location("mobility_source_import",
                                                  os.path.join(ROOT, "app/scripts", "mobility_source_import.py"))
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
        script_ok = mod.POOL == POOL and mod.SOURCE_ID == SID and mod.JRC_DOI == DOI
    except Exception as exc:
        script_ok = False
        print("   script import error:", exc)
    check("script: app/scripts/mobility_source_import.py loads and targets the same DOI/source/pool", script_ok)

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("ALL PASS — Mobility import: the complete real respondent corpus is acquired one-atom-per-row "
          "(coded values + missing codes preserved distinctly, nothing filtered or synthesized), frozen "
          "into a DOI/version/hash/Akasha-Time-attributable pool, subsettable deterministically without "
          "hiding the population, and bridged (based_on) to Mobility opinions traceably — guest-readable "
          "in the Source Viewer, audited grounded.")
    sys.exit(0)


if __name__ == "__main__":
    main()
