#!/usr/bin/env python3
"""
Contexa/Jataka eval — the client session's INPUT and OUTPUT sides on the pipe.

Contexa is the client's INPUT side: it reads the external world into the graph. Jataka is the
OUTPUT side: it presents a graph selection back out. Consciousness is the substrate both flow
THROUGH — Contexa's writes are auto-woven; Jataka's reads pass through generate_view — never a
pipe endpoint itself. The driving use case is a survey round-trip: build a questionnaire,
ingest collected answers (with Contexa macro-binding), then present the result three ways.

  C1 ingest     — contexa.ingest reads a responses CSV into the survey graph, mapping columns
                  to questions and writing one response per (respondent, question) cell.
  C2 binding    — each response is macro-bound: ctx:answers → its question, ctx:from → its
                  respondent (Contexa's context layer over the survey model's structural links).
  J1 table      — jataka.present as=table aggregates responses per (question, answer) with counts.
  J2 scatter    — jataka.present as=scatter positions the response atoms by cosmos_nd (the
                  Consciousness substrate supplies the coordinates), returning 2-D points.
  J3 narrative  — jataka.present as=narrative renders prose from generate_view; LLM-optional,
                  so with no LLM it still returns a non-empty structural narration (the floor).
  X  substrate  — Consciousness is not a pipe endpoint: present reads through generate_view and
                  never writes; the graph is unchanged by a presentation.

Run:  python test/contexa_jataka_eval.py
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
    print(f"  {'OK  ' if ok else '!! FAIL'}  {name:12} {detail}")


def main():
    print("\n  contexa/jataka eval — client INPUT (ingest) + OUTPUT (present) on the pipe\n")
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_cj_"))
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

    # ── Build a questionnaire (client, directly) ──────────────────────────────
    survey = (d("survey.new", {"title": "Commute", "description": "how people get to work"})
              or {}).get("survey_id")
    q1 = (d("survey.q.add", {"text": "How do you commute?", "order": 1}) or {}).get("question_id")
    q2 = (d("survey.q.add", {"text": "How long is your commute?", "order": 2}) or {}).get("question_id")

    # ── Collected responses as a CSV (paper→excel / web / chatbot all land here) ──
    csv = ("respondent,commute,minutes\n"
           "alice,train,30\n"
           "bob,bike,15\n"
           "carol,train,45\n"
           "dave,car,30\n")

    # C1 — ingest the CSV into the survey graph (inline upload path, WRITE client).
    ing = d("contexa.ingest", {"survey": survey, "text": csv, "format": "csv",
                               "respondent_col": "respondent",
                               "map": f"commute:{q1},minutes:{q2}"})
    ok_ingest = (isinstance(ing, dict) and ing.get("responses") == 8
                 and ing.get("respondents") == 4 and ing.get("errors") == 0)
    record("C1 ingest", ok_ingest,
           f"respondents={ing.get('respondents')}, responses={ing.get('responses')}, "
           f"errors={ing.get('errors')}")

    # C2 — Contexa macro-binding: responses carry ctx:answers (→question) + ctx:from (→respondent).
    inv = d("survey.list", {}) or {}
    resp_ids = inv.get("responses", [])
    answers = froms = 0
    for r_id in resp_ids:
        rels = {rel for (_dst, rel) in (cortex.get_adjacent_links(r_id) or [])}
        if "ctx:answers" in rels:
            answers += 1
        if "ctx:from" in rels:
            froms += 1
    record("C2 binding", answers == len(resp_ids) and froms == len(resp_ids) and len(resp_ids) == 8,
           f"responses={len(resp_ids)}, ctx:answers={answers}, ctx:from={froms}")

    # J1 — present as table: aggregate per (question, answer) with counts.
    tbl = d("jataka.present", {"survey": survey, "as": "table"})
    rows = (tbl or {}).get("rows", [])
    by_answer = {r["answer"]: r["count"] for r in rows}
    ok_table = (tbl.get("format") == "table" and by_answer.get("train") == 2
                and by_answer.get("30") == 2 and tbl.get("total_responses") == 8)
    record("J1 table", ok_table,
           f"rows={len(rows)}, train={by_answer.get('train')}, "
           f"min30={by_answer.get('30')}, total={tbl.get('total_responses')}")

    # J2 — present as scatter: each response atom positioned by cosmos_nd (substrate coords).
    sc = d("jataka.present", {"survey": survey, "as": "scatter"})
    pts = (sc or {}).get("points", [])
    ok_scatter = (sc.get("format") == "scatter" and len(pts) == 8
                  and all(isinstance(p.get("x"), (int, float))
                          and isinstance(p.get("y"), (int, float)) for p in pts))
    record("J2 scatter", ok_scatter,
           f"points={len(pts)}, first=({pts[0]['x']:.2f},{pts[0]['y']:.2f})" if pts else "no points")

    # J3 — present as narrative: prose from generate_view; non-empty even with no LLM (floor).
    nar = d("jataka.present", {"survey": survey, "as": "narrative"})
    text = (nar or {}).get("text", "")
    ok_narr = (nar.get("format") == "narrative" and nar.get("llm_used") is False
               and len(text) > 40 and "response" in text.lower())
    record("J3 narrative", ok_narr,
           f"llm_used={nar.get('llm_used')}, chars={len(text)}, text='{text[:60]}...'")

    # X — substrate: a presentation reads through Consciousness and writes nothing.
    before = len(cortex.stream(limit=100000) or [])
    d("jataka.present", {"survey": survey, "as": "table"})
    d("jataka.present", {"survey": survey, "as": "narrative"})
    after = len(cortex.stream(limit=100000) or [])
    record("X substrate", before == after,
           f"atoms before={before}, after={after} (present is read-only through generate_view)")

    print()
    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"  {passed}/{total} phases passed"
          + (f", {total - passed} FAILED" if passed < total else ""))
    if passed < total:
        print("\nRESULT: FAIL — the Contexa/Jataka survey round-trip regressed.")
        return 1
    print("\nRESULT: PASS — Contexa ingests responses IN (with ctx macro-binding), the client "
          "analyses, Jataka presents OUT three ways; Consciousness is the read-through substrate.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
