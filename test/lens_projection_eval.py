#!/usr/bin/env python3
"""
Lens projection eval — per-model import_projection / export_projection (#43 Part B).

Before this, `table` was the ONLY model wired into the lens projection contract:
`io.project model=table` cast a scan into a table, and only a `table` atom could be
scanned back OUT (ExportableMixin). This proves the contract now reaches two more
models — `rec` as an Importable target and `survey` as an Exportable source — so
`io.project model=<m>` targets more than table and a survey round-trips OUT of the graph.

  LP1 set→rec        — io.project model=rec casts an in-graph set into schema-free rec
                       atoms (the universal Importable fallback target).
  LP2 rec candidate  — lens.scan on a plain set lists `rec` among the candidate models
                       (rec always qualifies; a specific model like `table` outscores it).
  LP3 survey→rec     — io.project src=<survey_root> exports the survey's responses
                       (ExportableMixin) and casts them into rec, one per response, with
                       answer/question/respondent preserved as rec: attributes.
  LP4 survey→table   — the same survey export cast into a table (default model), proving
                       the exported stream feeds ANY Importable target.
  LP5 meta_match     — scanning a NON-survey concept atom (meta type="concept" but
                       concept!="survey") does NOT trigger the survey exporter — the
                       meta_match refinement keeps the shared "concept" meta_type safe.

Run:  python test/lens_projection_eval.py
"""
import os
import sys
import hashlib
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

_results = []


def record(name, ok, detail=""):
    _results.append((name, ok, detail))
    print(f"  {'OK  ' if ok else '!! FAIL'}  {name:18} {detail}")


def main():
    print("\n  lens projection eval — rec (import) + survey (export) join the contract\n")
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_lp_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin",
                                    "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                "id": "g"}, "local")

    def d(m, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": m,
                        "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
        return r.get("result") or r.get("error")

    cortex = k.manager.get_session("admin").local_cortex

    # ── Build an in-graph set of records (three rec-style atoms) ────────────────
    setname = "set:rec:expense"
    for payee, amount in [("Cafe", "4"), ("Books", "22"), ("Fuel", "58")]:
        a  = (d("w", {"content": f"expense {payee}"}) or {}).get("key")
        vp = (d("w", {"content": payee}) or {}).get("key")
        va = (d("w", {"content": amount}) or {}).get("key")
        d("ln", {"src": a, "dst": vp, "rel": "rec:payee"})
        d("ln", {"src": a, "dst": va, "rel": "rec:amount"})
        d("set.add", {"name": setname, "id": a})

    # LP1 — cast the set INTO rec (io.project model=rec). New Importable target.
    projr = d("io.project", {"src": setname, "model": "rec", "into": "expense_rec"})
    cast  = (projr.get("cast") or {}).get("result") or {} if isinstance(projr, dict) else {}
    into_set = cast.get("into")
    members  = cortex.get_collection_members(into_set) if into_set else []
    # each projected rec atom should carry rec:payee / rec:amount + a ctx:source back-link
    carried = 0
    src_links = 0
    for mk in members:
        rels = {rel for _dst, rel in cortex.get_adjacent_links(mk)}
        if "rec:payee" in rels and "rec:amount" in rels:
            carried += 1
        if "ctx:source" in rels:
            src_links += 1
    lp1 = (isinstance(projr, dict) and projr.get("kind") == "cast"
           and projr.get("model") == "rec" and cast.get("written") == 3
           and carried == 3 and src_links == 3)
    record("LP1 set→rec", lp1,
           f"written={cast.get('written')}, attrs_carried={carried}, ctx:source={src_links}")

    # LP2 — rec appears as a candidate on a plain-set scan (universal fallback).
    scan = d("lens.scan", {"src": setname})
    cands = {c.get("model") for c in (scan.get("candidates") or [])} if isinstance(scan, dict) else set()
    lp2 = "rec" in cands and "table" in cands
    record("LP2 rec candidate", lp2, f"candidates={sorted(cands)}")

    # ── Build a small survey with explicit responses (meta.answer populated) ────
    survey = (d("survey.new", {"title": "Colors", "description": "favorite color"})
              or {}).get("survey_id")
    q1 = (d("survey.q.add", {"text": "Favorite color?", "order": 1}) or {}).get("question_id")
    r1 = (d("survey.res.add", {"respondent_id": "u1"}) or {}).get("respondent_atom")
    r2 = (d("survey.res.add", {"respondent_id": "u2"}) or {}).get("respondent_atom")
    d("survey.ans", {"question_id": q1, "respondent_atom": r1, "answer": "blue"})
    d("survey.ans", {"question_id": q1, "respondent_atom": r2, "answer": "green"})

    # LP3 — export the survey (ExportableMixin) and cast into rec.
    projs = d("io.project", {"src": survey, "model": "rec", "into": "survey_rec"})
    scast = (projs.get("cast") or {}).get("result") or {} if isinstance(projs, dict) else {}
    smembers = cortex.get_collection_members(scast.get("into")) if scast.get("into") else []
    answers = set()
    for mk in smembers:
        for dst, rel in cortex.get_adjacent_links(mk):
            if rel == "rec:answer":
                answers.add(cortex.get_chunk(dst) or "")
    lp3 = (isinstance(projs, dict) and projs.get("kind") == "cast"
           and scast.get("written") == 2 and answers == {"blue", "green"})
    record("LP3 survey→rec", lp3,
           f"responses_written={scast.get('written')}, answers={sorted(answers)}")

    # LP4 — the same survey export cast into a TABLE (default model): the exported
    # stream feeds any Importable target, not just rec.
    projt = d("io.project", {"src": survey, "model": "table", "into": "survey_tbl"})
    tcast = (projt.get("cast") or {}).get("result") or {} if isinstance(projt, dict) else {}
    lp4 = (isinstance(projt, dict) and projt.get("kind") == "cast"
           and tcast.get("rows_inserted") == 2
           and bool(cortex.resolve_alias("tbl:survey_tbl")))
    record("LP4 survey→table", lp4,
           f"rows_inserted={tcast.get('rows_inserted')}, tbl:survey_tbl={bool(cortex.resolve_alias('tbl:survey_tbl'))}")

    # LP5 — meta_match safety: another concept model's root ALSO carries meta type="concept"
    # (curation roots are type="concept", concept="curation"). The survey exporter must NOT
    # capture it — meta_match={"concept":"survey"} keeps the shared meta_type disambiguated.
    cur = d("curation.new", {"title": "Spend story", "set": setname, "mode": "authored"})
    cur_id = cur.get("curation_id") if isinstance(cur, dict) else None
    scan2 = d("lens.scan", {"src": cur_id}) if cur_id else {}
    # A curation root is not a survey → survey.export_projection is never invoked, so the
    # scan is a plain tree/set scan, NOT scope="model_export".
    prof_scope = (scan2.get("profile") or {}).get("scope") if isinstance(scan2, dict) else "err"
    lp5 = bool(cur_id) and prof_scope != "model_export"
    record("LP5 meta_match", lp5,
           f"curation(concept≠survey) scan scope={prof_scope} (not model_export)")

    # LP6 — non-destructive: after projecting the survey OUT (into rec AND table, both of
    # which store the question/response text as VALUES), the SOURCE atoms must be untouched.
    # Content-addressing + INSERT-OR-REPLACE would clobber them if a value were re-put; the
    # value-key resolver reuses existing atoms instead. Assert the sources kept their meta.
    q_meta = cortex.get_meta(q1) or {}
    resp_set = f"set:survey:{survey}:responses"
    resp_types = [(cortex.get_meta(rk) or {}).get("type")
                  for rk in cortex.get_collection_members(resp_set)]
    lp6 = (q_meta.get("type") == "survey_question"
           and resp_types == ["survey_response", "survey_response"])
    record("LP6 non-destructive", lp6,
           f"question.type={q_meta.get('type')}, responses={resp_types}")

    print()
    passed = sum(1 for _, ok, _ in _results if ok)
    total  = len(_results)
    print(f"  {passed}/{total} phases passed"
          + (f", {total - passed} FAILED" if passed < total else ""))
    if passed < total:
        print("\nRESULT: FAIL — the per-model projection contract regressed.")
        return 1
    print("\nRESULT: PASS — rec is a universal Importable target and survey is an "
          "Exportable source; io.project model=<m> now reaches beyond table.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
