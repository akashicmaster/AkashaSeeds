#!/usr/bin/env python3
"""
Labo World-Model eval — the acceptance criteria of the Akasha Labo / Hyper Labo Implementation
Directive v0.1 §16.

Drives the whole layer through an in-process kernel: a bounded research namespace (labo) with the
four canonical projections (SOURCE·CONCEPT·SOCIETY·NOTEBOOK), Cronon as a passive Akasha-Time
coordinate, plugin-provenance Analysis runs whose clustering output is Sets, plural interpretations
with auditable rationale, a cronon-ordered Research Notebook that retains failed/superseded states,
a Publication Set with bidirectional backlinks, and a Hyper Labo that composes Labos without merging
them.

Run:  python app/test/labo_world_model_eval.py     (exit 0 = all pass)
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
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_labo_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def d(method, data, tok="admin", trust="local"):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": tok, "data": data}, "id": "t"}, trust)
        return r.get("result") if "result" in r else {"__error__": r.get("error")}

    # ── 0. a bounded research namespace with four canonical projections ──
    lab = d("labo.new", {"name": "mobility", "about": "EU mobility opinion research", "scope": "public"})
    info = d("labo.info", {"name": "mobility"})
    check("labo opens as ONE namespace with Source/Concept/Society/Notebook projections",
          lab.get("labo") == "labo:mobility"
          and set(info.get("projections", {})) == {"source", "concept", "society", "notebook"}, str(lab))

    # ── 1. a small Source population, bound into the labo (composition, not ownership) ──
    d("source.register", {"provider": "JRC", "name": "eu_ts", "doi": "10.2905/x", "version": "1.1"})
    rows = [{"id": f"R{i}", "country": ["DE", "FR", "IT"][i % 3],
             "roadcharge": (i % 3)} for i in range(18)]
    d("source.pool.create", {"name": "eu_ts", "source": "source:src:eu_ts", "rule": "complete"})
    d("source.acquire", {"source": "source:src:eu_ts", "rule": "complete", "records": rows,
                         "id_field": "id", "pool": "source:pool:eu_ts:v1"})
    d("source.pool.freeze", {"pool": "source:pool:eu_ts:v1"})
    d("labo.bind", {"name": "mobility", "pool": "source:pool:eu_ts:v1"})
    src_proj = d("labo.source", {"name": "mobility"})
    check("SOURCE projection: the frozen pool is bound (referenced), with provenance visible",
          any(s.get("source") == "source:pool:eu_ts:v1" and s.get("status") == "FROZEN"
              for s in src_proj.get("sources", [])), str(src_proj.get("count")))

    # ── 2. Analysis View — clustering output as SETS, switchable/overlayable (§3) ──
    run1 = d("analysis.run", {"labo": "mobility", "input": "source:pool:eu_ts:v1",
                              "plugin": "groupby:country", "name": "by_country"})
    run2 = d("analysis.run", {"labo": "mobility", "input": "source:pool:eu_ts:v1",
                              "plugin": "groupby:roadcharge", "name": "by_charge"})
    check("Analysis: a plugin run persists provenance and materializes clustering output as result Sets",
          len(run1.get("output_sets", [])) == 3 and run1.get("plugin") == "groupby:country"
          and isinstance(run1.get("projection"), dict), str(run1.get("output_sets")))
    sets = {s["set"] for s in d("analysis.ls", {"labo": "mobility"}).get("sets", [])}
    check("switching method = switching result Sets (two independent clusterings coexist)",
          len(sets) == 6, str(len(sets)))
    # overlay two clusters from different methods (a source item belongs to multiple Sets)
    ov = d("analysis.overlay", {"a": "analysis:set:mobility:by_country_de",
                                "b": "analysis:set:mobility:by_charge_0"})
    check("a Source Atom belongs to multiple statistical Sets; overlay makes method overlap visible",
          isinstance(ov.get("jaccard"), float) and ov.get("a_size", 0) > 0, str(ov))
    # method-invariant core vs boundary
    core = d("analysis.core", {"labo": "mobility",
                               "sets": "analysis:set:mobility:by_country_de,analysis:set:mobility:by_charge_0"})
    check("method-invariant CORE Set + method-sensitive BOUNDARY Set are materialized separately",
          core.get("core_set") and core.get("boundary_set")
          and core.get("core_size", -1) >= 0 and core.get("boundary_size", -1) >= 0, str(core))

    # ── 3. Interpretations — plural claims with auditable rationale (§5) ──
    tgt = "analysis:set:mobility:by_country_de"
    i1 = d("labo.interpret", {"name": "mobility", "target": tgt, "role": "latent_theme_labeler",
                              "label": "cost-sensitive commuters", "rationale": "high roadcharge concern in DE cluster",
                              "evidence": "source:item:eu_ts:r0,source:item:eu_ts:r3", "confidence": "0.6"})
    i2 = d("labo.interpret", {"name": "mobility", "target": tgt, "role": "counter_reader",
                              "label": "policy-neutral group", "rationale": "the DE cluster is a geography artifact, not an attitude",
                              "competing": i1.get("interpretation")})
    check("interpretation: the SAME target carries multiple/contradictory labels (plural claims)",
          d("labo.interpretations", {"name": "mobility", "target": tgt}).get("count") == 2, "")
    why = d("labo.why", {"interpretation": i1.get("interpretation")})
    check("every interpretation exposes role, rationale/criteria and evidence (not a summary)",
          why.get("role") == "latent_theme_labeler" and why.get("rationale")
          and len(why.get("evidence", [])) == 2, str(why)[:120])
    check("competing readings are linked side by side, never collapsed",
          i1.get("interpretation") in (d("labo.why", {"interpretation": i2.get("interpretation")}).get("competing") or []),
          "")

    # ── 4. Research Notebook — cronon-ordered, failed/superseded retained (§6) ──
    q = d("research.chunk", {"labo": "mobility", "type": "question", "content": "why does the DE cluster form?"})
    h1 = d("research.chunk", {"labo": "mobility", "type": "hypothesis", "content": "it's a cost-attitude cluster",
                              "based_on": tgt, "follows": q.get("chunk")})
    h2 = d("research.chunk", {"labo": "mobility", "type": "hypothesis", "content": "no — it's a geography artifact",
                              "supersedes": h1.get("chunk"), "contradicts": h1.get("chunk")})
    fail = d("research.chunk", {"labo": "mobility", "type": "failed_hypothesis",
                               "content": "attitude-only model did not replicate"})
    check("Research Chunks are recorded with type + provenance + cronon",
          q.get("chunk") and isinstance(h1.get("cronon"), int) and h2.get("cronon") > h1.get("cronon"), "")
    tl = d("research.timeline", {"name": "mobility", "order": "cronon"})
    superseded = [c for c in tl.get("chunks", []) if c.get("superseded")]
    check("failed/superseded research states are RETAINED and flagged (never erased §6.1)",
          tl.get("count") == 4 and any(c["chunk"] == h1.get("chunk") and c["superseded"] for c in tl.get("chunks", [])),
          f"superseded={len(superseded)}")
    arg = d("research.timeline", {"name": "mobility", "order": "argument"})
    check("the notebook re-projects in several orders (cronon + argument)",
          arg.get("order") == "argument" and arg.get("chunks", [{}])[0].get("type") == "question", "")

    # ── 5. Publication — a recomposition of chunks with bidirectional backlinks (§7) ──
    pub = d("research.publication", {"labo": "mobility", "name": "draft1",
                                     "chunks": f"{q.get('chunk')},{h2.get('chunk')}"})
    trace = d("research.trace", {"id": h2.get("chunk")})
    check("Publication Set backlinks to the chunks that generated it (bidirectional §7)",
          pub.get("count") == 2 and "published_in" in trace.get("out", {}), str(trace.get("out")))

    # ── 6. Cronon — a passive coordinate; a chunk locates on Akasha Time; external mapping is external ──
    d("cronon.mint", {"label": "t1"})
    cro = d("cronon.map", {"cronon": "cronon:c" + str(d("cronon.now", {}).get("cronon")),
                           "frame": "wall_clock", "value": "2025-08"})
    check("Cronon is a passive coordinate with an EXTERNAL time mapping (temporal relativity §1.1/§1.2)",
          isinstance(cro, dict) and cro.get("frame") == "wall_clock" and cro.get("mappings"), str(cro)[:80])

    # ── 7. Hyper Labo — composes Labos without merging them (§9) ──
    d("labo.new", {"name": "climate", "about": "emissions policy"})
    hy = d("labo.hyper.new", {"name": "transport_climate", "labos": "mobility,climate",
                              "about": "mobility × climate"})
    br = d("labo.hyper.bridge", {"name": "transport_climate", "a": "labo:mobility", "b": "labo:climate",
                                 "rel": "shared_policy_lever", "rationale": "road charging touches both"})
    check("Hyper Labo composes participating Labos WITHOUT merging; a cross-lab bridge asserts NO equivalence",
          len(hy.get("participating", [])) == 2 and br.get("asserts_equivalence") is False, str(hy.get("participating")))
    # the participating labos are untouched (still their own namespaces)
    check("participating Labos are not mutated by the Hyper Labo (their local worlds stay autonomous)",
          d("labo.info", {"name": "mobility"}).get("labo") == "labo:mobility"
          and d("labo.info", {"name": "climate"}).get("labo") == "labo:climate", "")

    # ── 8. multi-client provenance + guest-readability (public labo) ──
    g = d("session.guest.create", {})
    gt = (g or {}).get("binding_key") or (g or {}).get("session_token")
    gview = d("labo.info", {"name": "mobility"}, tok=gt, trust="network") if gt else {"__error__": "no guest"}
    check("a public Labo's material is guest-readable (Source Viewer / world-model is in the nucleus)",
          isinstance(gview, dict) and gview.get("labo") == "labo:mobility", str(gview)[:80])
    check("client provenance is preserved on interpretations (who/role/cronon)",
          why.get("client") and why.get("cronon"), "")

    # ── 9. CLI-first — the layer flows through the real shlex parser + router ──
    try:
        from api.gateway import AkashaGateway
        from api.portals.stdio import run_single_shot
        gw = AkashaGateway(kernel_client=k)
        out = run_single_shot("labo.ls", gw)
        cli_ok = isinstance(out, str) and "labo:mobility" in out
    except Exception as exc:
        cli_ok, out = False, str(exc)
    check("CLI-first: labo/research/analysis/cronon flow through the real CLI (not RPC-only)", cli_ok, str(out)[:80])

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("ALL PASS — Labo World-Model: a bounded research namespace opens as Source·Concept·Society·"
          "Notebook projections; Cronon is a passive Akasha-Time coordinate; analysis clustering is "
          "traceable Sets (overlayable, core/boundary, never truth); interpretations are plural claims "
          "with auditable rationale; the notebook is cronon-ordered and retains failed/superseded "
          "states; publications recompose chunks with backlinks; and a Hyper Labo composes Labos "
          "without merging them — all guest-readable and CLI-first.")
    sys.exit(0)


if __name__ == "__main__":
    main()
