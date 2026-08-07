#!/usr/bin/env python3
"""
Concept Laboratory (Nebula) eval — clab.* over the Primary Examples corpus.

The model is deliberately hypothesis-heavy: it must PRESERVE incomplete, contradictory, and
competing structures rather than resolve them. This eval is meant to be re-run repeatedly as the
model evolves — it boots fresh, loads the tier-C philosophy corpus (ontology/primary_examples),
and exercises the operator surface against the real gravitational-wave cases, checking the
invariants that make the model useful:

  C1 corpus       — the pe:* corpus loads; pe:ligo_direct_detection resolves; pe:gravity_waves set.
  C2 workspace    — clab.new opens a Nebula (active field in session context).
  C3 non-overwrite— two assessments on the SAME (target,criterion) coexist (nothing overwritten).
  C4 dissent      — clab.compare shows BOTH judgements in one cell (competing views side by side).
  C5 attribution  — each assessment carries its explicit agent (investigator_A / critic_B).
  C6 tension      — clab.tension is preserved; clab.status reports it (not resolved away).
  C7 proposal     — clab.bridge stays tentative (NO real edge) until clab.accept materializes it.
  C8 stabilize    — clab.stabilize creates a provisional Concept and NEVER deletes the precursor.
  C9 reject-audit — clab.reject marks a proposal rejected (queryable) and creates no edge.
  C10 fork        — clab.fork copies operands into a new branch without overwriting the parent.
  C11 replay      — clab.replay reconstructs the operands in creation order.

Run:  python test/clab_eval.py           (exit 0 = all pass)
      python test/clab_eval.py --seq      (also print the command→result transcript)

Developer verification test (not a user-facing .ak example).
"""
import os
import sys
import json
import hashlib
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

SEQ = "--seq" in sys.argv
_fails = []
_log = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def boot():
    from lib.akasha.kernel import KernelDispatcher
    from api.gateway import AkashaGateway
    KernelDispatcher._boot_load_ontology = lambda self: None      # skip autoload; we load the pack
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_clab_"))
    gw = AkashaGateway(kernel_client=k)                           # gateway handles sys.cli_exec
    gw.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                 "params": {"session_token": "admin",
                            "data": {"user_name": "admin",
                                     "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                 "id": "g"}, "local")
    return k, gw


def main():
    k, gw = boot()

    def d(method, data):
        r = gw.dispatch({"jsonrpc": "2.0", "method": method,
                         "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
        return r.get("error") and {"__error__": r["error"]["message"]} or r.get("result")

    def clab(op, **data):
        res = d("clab." + op, data)
        if SEQ:
            args = " ".join(f'{kk}={json.dumps(vv, ensure_ascii=False)}' for kk, vv in data.items())
            _log.append(f"akasha> clab.{op} {args}")
            _log.append("   → " + json.dumps(res, ensure_ascii=False)[:200])
        return res or {}

    # ── load the tier-C corpus directly (deterministic; boot autoload is skipped) ──
    import glob
    loaded = errs = 0
    for ak in sorted(glob.glob(os.path.join(ROOT, "ontology", "primary_examples", "*.ak"))):
        if os.path.basename(ak) == "_lexicon.ak":
            continue
        for line in open(ak, encoding="utf-8"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            r = d("sys.cli_exec", {"command": line})
            if isinstance(r, dict) and r.get("__error__"):
                errs += 1
            else:
                loaded += 1
    gwset = d("sys.cli_exec", {"command": 'set.ls name="pe:gravity_waves"'}) or {}
    gwn = len(gwset.get("members", gwset.get("items", []))) if isinstance(gwset, dict) else 0
    ligo = k.manager.get_session("admin").local_cortex.resolve_alias("pe:ligo_direct_detection")
    check("C1 corpus loads (atoms/links/sets, no errors)", errs == 0 and loaded >= 240, f"{loaded} ok / {errs} err")
    check("C1 pe:ligo_direct_detection resolves + pe:gravity_waves populated", bool(ligo) and gwn == 9, f"gw={gwn}")

    # ── C2 workspace ──
    neb = clab("new", title="What makes a Primary Example theory-starting?")
    check("C2 clab.new opens a Nebula", neb.get("status") == "open" and neb.get("id", "").startswith("clab:nebula:"))

    # ── C3 / C4 / C5 assessments: non-overwriting, dissent preserved, attributed ──
    clab("assess", target="pe:ligo_direct_detection", criterion="pertinence",
         judgement="strong", agent="investigator_A", rationale="belongs squarely inside GR")
    clab("assess", target="pe:ligo_direct_detection", criterion="convincingness",
         judgement="strong", agent="investigator_A", rationale="perceptually grounded, replicated")
    clab("assess", target="pe:ligo_direct_detection", criterion="convincingness",
         judgement="mixed", agent="critic_B", rationale="convincingness is relationally produced")
    clab("assess", target="pe:weber_claim", criterion="convincingness",
         judgement="weak", agent="investigator_A", rationale="implausible rate, not replicated")
    cmp = clab("compare", targets="pe:ligo_direct_detection,pe:weber_claim",
               by="convincingness,pertinence")
    cell = (cmp.get("matrix", {}).get("pe:ligo_direct_detection", {}).get("convincingness", []))
    check("C3 assess is non-overwriting (2 views on same target+criterion)", len(cell) == 2)
    check("C4 compare preserves dissent (strong vs mixed in one cell)",
          {c["judgement"] for c in cell} == {"strong", "mixed"})
    check("C5 assessments are agent-attributed", {c["agent"] for c in cell} == {"investigator_A", "critic_B"})

    # ── C6 tension preserved + reported ──
    clab("tension", left="pe:int_convincingness_relational", right="pe:int_convincingness_perceptual",
         kind="underdetermination", rationale="where does convincingness live?")
    st = clab("status")
    check("C6 tension preserved + reported by status", st.get("open_tensions", 0) >= 1,
          f"open_tensions={st.get('open_tensions')}")

    # ── C7 proposal boundary: bridge tentative → accept materializes ──
    cx = k.manager.get_session("admin").local_cortex
    # a genuinely-unlinked pair (the corpus does NOT connect Weber's claim to the theory-starting
    # perception) so "no edge before accept" is a real test of the proposal boundary.
    BR_FROM, BR_TO, BR_REL = "pe:weber_claim", "pe:theory_starting_perception", "clab:bridges"
    fk = cx.resolve_alias(BR_FROM)
    tk = cx.resolve_alias(BR_TO)

    def edge_exists(src, dst, rel):
        for row in (cx.get_adjacent_links(src, rel) or []):
            if (row[0] if isinstance(row, (list, tuple)) else row) == dst:
                return True
        return False

    br = clab("bridge", **{"from": BR_FROM, "to": BR_TO, "rel": BR_REL,
                           "rationale": "could Weber's contested case still be theory-starting?"})
    before = edge_exists(fk, tk, BR_REL)
    acc = clab("accept", proposal=br.get("id", ""))
    after = edge_exists(fk, tk, BR_REL)
    check("C7 bridge is inert until accepted (no edge before)", br.get("status") == "tentative" and not before)
    check("C7 accept materializes the real edge", acc.get("status") == "accepted" and after)

    # ── C8 stabilize keeps the precursor ──
    stab = clab("stabilize", target="pe:ligo_direct_detection", **{"as": "Primary Example"})
    still = bool(cx.resolve_alias("pe:ligo_direct_detection"))
    check("C8 stabilize creates a provisional Concept, precursor kept",
          stab.get("maturity") == "tentative" and still)

    # ── C9 reject stays queryable, no edge ──
    prop = clab("propose", text="Weber's peaks were genuine GW events",
                **{"from": "pe:weber_claim", "to": "pe:gravitational_waves", "rel": "clab:supports"})
    rej = clab("reject", proposal=prop.get("id", ""), rationale="not replicated")
    wk = cx.resolve_alias("pe:weber_claim")
    gwk = cx.resolve_alias("pe:gravitational_waves")
    check("C9 reject marks it queryable + creates no edge",
          rej.get("status") == "rejected" and not edge_exists(wk, gwk, "clab:supports"))

    # ── C10 fork copies operands, parent intact ──
    parent_before = clab("status").get("operands", 0)
    frk = clab("fork", name="no-replication branch")
    fork_ops = clab("status").get("operands", 0)   # active is now the fork
    check("C10 fork copies operands into a new branch", frk.get("copied", 0) == parent_before and fork_ops == parent_before)

    # ── C11 replay in creation order ──
    clab("open", id=neb.get("id"))                  # back to the parent
    rp = clab("replay", limit=50)
    kinds = [s["kind"] for s in rp.get("sequence", [])]
    check("C11 replay reconstructs creation order", rp.get("steps", 0) >= 8 and kinds[0] == "assessment", " → ".join(kinds))

    # ══ Iteration 0.3 — research provenance / trace / aliases ══════════════════════
    # (active Nebula is the parent, reopened at C11: it carries assessments + a stabilization
    #  on pe:ligo_direct_detection from the core section.)
    src = clab("source.add", title="Primary Examples", author="Radu Tulai", year=2022, type="paper",
               journal="Romanian Journal of Analytic Philosophy", pages="179-203",
               doi="10.62229/rrfaxvi-2/9", url="https://doi.org/10.62229/rrfaxvi-2/9")
    lst = clab("source.list")
    check("T1 source.add registers an addressable Source; source.list finds it",
          src.get("id", "").startswith("clab:source:") and
          any(s["title"] == "Primary Examples" for s in lst.get("sources", [])))

    link = clab("source.link", target="pe:ligo_direct_detection", source=src.get("id"),
                role="derived_from", pages="191-192",
                section="4. Scientific experiments as cases for primary examples",
                note="Tulai's philosophical treatment of LIGO as a Primary Example.")
    show = clab("source.show", id=src.get("id"))
    cites = show.get("citations", [])
    loc_ok = bool(cites) and cites[0]["locator"].get("pages") == "191-192" and \
        "section" in cites[0]["locator"]
    check("T2 source.link carries a locator; page/section survive on the link", loc_ok,
          str(cites[0]["locator"]) if cites else "no citations")

    # a rejected interpretation (research evidence for the abandoned path)
    clab("interpret", target="pe:ligo_direct_detection",
         text="LIGO is not really perceptual at all — it is pure inference", agent="skeptic_C",
         status="rejected")

    tr = clab("trace", target="pe:ligo_direct_detection", depth="all", order="time")
    tr_srcs = tr.get("sources", [])
    check("T3 trace walks from the operand back to >=1 Source (with DOI)",
          any(s["doi"] == "10.62229/rrfaxvi-2/9" for s in tr_srcs))
    tr_conv = [a for a in tr.get("assessments", []) if a.get("id")]  # assessments gathered
    agents = {a["agent"] for a in tr.get("assessments", [])}
    check("T4 trace preserves multiple assessments + dissent (>=2 agents)",
          len(tr.get("assessments", [])) >= 2 and {"investigator_A", "critic_B"} <= agents)

    tr_def = clab("trace", target="pe:ligo_direct_detection")
    tr_rej = clab("trace", target="pe:ligo_direct_detection", include="rejected")
    def_has = any(i.get("status") == "rejected" for i in tr_def.get("interpretations", []))
    rej_has = any(i.get("status") == "rejected" for i in tr_rej.get("interpretations", []))
    check("T5 rejected paths hidden by default, surfaced by include=rejected",
          (not def_has) and rej_has)

    # alias equivalence: clab.as == clab.assess (same operand kind + fields)
    a_canon = clab("assess", target="pe:weber_claim", criterion="pertinence",
                   judgement="mixed", agent="investigator_A", rationale="contested case")
    a_alias = d("clab.as", {"target": "pe:weber_claim", "criterion": "generality",
                            "judgement": "weak", "agent": "critic_B", "rationale": "singular anomaly"})
    check("T6 alias clab.as is semantically identical to clab.assess",
          a_canon.get("type") == "clab:assessment" and a_alias.get("type") == "clab:assessment"
          and a_alias.get("criterion") == "generality")
    tr_alias = d("clab.tr", {"target": "pe:ligo_direct_detection"})
    check("T6 alias clab.tr is semantically identical to clab.trace",
          tr_alias.get("type") == "clab:trace" and tr_alias.get("target") == "pe:ligo_direct_detection")

    rp = clab("replay", limit=50)
    check("T7 replay (history) and trace (provenance) are distinct surfaces",
          rp.get("type") == "clab:replay" and "sequence" in rp and
          tr.get("type") == "clab:trace" and "sources" in tr)

    al = clab("aliases")
    check("T8 aliases are discoverable (clab.aliases lists canonical↔short)",
          al.get("count", 0) >= 20 and any(a["alias"] == "clab.tr" for a in al.get("aliases", [])))

    # ══ Deep corpus 0.4 — four Primary-Example series (Eclipse / Weber→LIGO / MICROSCOPE / TEA) ══
    CAND = {"eclipse": "pe04:example:eclipse:1919_candidate",
            "ligo": "pe04:example:gw:ligo_candidate",
            "micro": "pe04:example:eq:microscope_candidate",
            "tea": "pe04:example:tea:successful_outcome"}
    series = ["pe04:solar_eclipse", "pe04:weber_ligo", "pe04:microscope", "pe04:tea_laser",
              "pe04:crosscase_tensions"]
    scounts = {}
    for s in series:
        r = d("sys.cli_exec", {"command": f'set.ls name="{s}"'}) or {}
        scounts[s] = len(r.get("members", r.get("items", []))) if isinstance(r, dict) else 0
    check("P1 all four series + cross-case tensions loaded", all(scounts[s] > 0 for s in series),
          " ".join(f"{s.split(':')[1]}={scounts[s]}" for s in series))

    # register the Tulai source links (page/section locator) to each candidate — provenance 0.4
    pages = {"eclipse": "190-191", "ligo": "191-192", "micro": "192-194", "tea": "188-190"}
    for kk, tgt in CAND.items():
        clab("source.link", target=tgt, source=src.get("id"), role="derived_from",
             pages=pages[kk], section="4. Scientific experiments as cases for primary examples")

    # cross-case assessments (dissent) + competing interpretations + a tension (from the 0.4 script)
    clab("assess", target=CAND["eclipse"], criterion="convincingness", judgement="mixed",
         agent="historian_A", rationale="mediated by photography and later positional analysis")
    clab("assess", target=CAND["ligo"], criterion="convincingness", judgement="strong",
         agent="experimentalist_B", rationale="direct interferometric signal plus later detections")
    clab("assess", target=CAND["tea"], criterion="convincingness", judgement="strong",
         agent="philosopher_C", rationale="vaporizing concrete is a vivid operational success")
    clab("interpret", target=CAND["tea"], agent="philosopher_C",
         text="Breaks an experimenter's regress but need not initiate a new scientific concept.")
    clab("interpret", target=CAND["tea"], agent="advocate_E",
         text="Direct and operationally compelling; might share properties with Primary Examples.")
    clab("tension", left=CAND["tea"], right="pe04:position:theory_starting_perception",
         kind="boundary_dispute", rationale="experimental success may not equal theory-starting perception")

    cmp4 = clab("compare", targets=",".join(CAND.values()), by="convincingness")
    check("P2 cross-case compare spans all four candidates", len(cmp4.get("matrix", {})) == 4,
          f"{len(cmp4.get('matrix', {}))} candidates")

    trace_ok, details = True, []
    for kk, tgt in CAND.items():
        tr4 = clab("trace", target=tgt, depth="all")
        has = any(s.get("doi") == "10.62229/rrfaxvi-2/9" and s.get("locator", {}).get("pages")
                  for s in tr4.get("sources", []))
        trace_ok = trace_ok and has
        details.append(f"{kk}={'✓' if has else '✗'}")
    check("P3 all four candidates trace back to Tulai (with page locator)", trace_ok, " ".join(details))

    tr_tea = clab("trace", target=CAND["tea"], depth="all")
    check("P4 non-conclusive: candidate holds competing interpretations + tensions (no asserted truth)",
          len(tr_tea.get("interpretations", [])) >= 2 and len(tr_tea.get("tensions", [])) >= 1,
          f"interp={len(tr_tea.get('interpretations', []))} tensions={len(tr_tea.get('tensions', []))}")

    if SEQ:
        print("\n" + "=" * 70 + "\nTRANSCRIPT\n" + "=" * 70)
        print("\n".join(_log))
        for label, tgt in (("pe:ligo_direct_detection (v0.1)", "pe:ligo_direct_detection"),
                           ("pe04:example:tea:successful_outcome (0.4 TEA laser)", CAND["tea"])):
            print("\n" + "=" * 70 + f"\nRESEARCH-MODE TRACE — clab.tr target={label} include=rejected order=reason\n" + "=" * 70)
            print(clab("trace", target=tgt, depth="all", include="rejected", order="reason").get("render", ""))

    print()
    if _fails:
        print(f"RESULT: {len(_fails)} FAIL — " + "; ".join(_fails))
        sys.exit(1)
    print("RESULT: PASS — all clab invariants hold (competing structures preserved).")
    sys.exit(0)


if __name__ == "__main__":
    main()
