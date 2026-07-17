#!/usr/bin/env python3
"""
Cosmos eval — is the semantic *space* real, or decorative?

The cosmos viewport is a projection of the cockpit's navigation over the semantic universe.
Its premise is spatial: "near in space ⇒ near in meaning". That premise was fake — `cosmos_nd`
was a hash placeholder (`calculate_nd` never used the real embedding), and the cosmos graph fed
ForceGraph3D positionless nodes (layout was pure physics). Now the position is a projection of
each atom's real self-owned `semantic_vector` (fixed seeded random projection → distance-
preserving), and the graph payload carries x/y/z + a degree-based size.

  C1 semantic layout — at the population level (3 topics × 5), atoms of the SAME topic land
                       closer together than atoms of a DIFFERENT topic (mean intra-cluster
                       distance < mean inter-cluster). A single fixed random projection to 3-D
                       is distance-preserving in expectation, so this holds over a real sample
                       (it is noisy for a handful of atoms; the learned tier sharpens it).
  C2 not degenerate  — positions are not all-zero / not all-identical (the old failure mode).
  C3 graph geometry  — dive.look's cosmos nodes carry x/y/z coordinates and a degree-based
                       `val` that actually varies (the hub is bigger than a leaf).
  C4 scatter spread  — jataka.present as=scatter positions responses across the plane, not all
                       stacked at the origin (the downstream consumer of the real position).
  C5 fitted layout   — once a learned model exists, positions project onto its PRINCIPAL (SVD)
                       axes (a crisp, server-side fitted layout — no GUI algorithm) and still
                       cluster by topic; the floor tier degrades to the random-projection seed.

Run:  python test/cosmos_eval.py
"""
import os
import sys
import math
import hashlib
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
# Deterministic floor tier: don't let the boot daemon re-bake vectors from a degenerate
# 6-atom learned model mid-test (in production the learned tier makes positions even sharper).
os.environ["AKASHA_NO_AUTOLEARN"] = "1"

_results = []


def record(name, ok, detail=""):
    _results.append((name, ok, detail))
    print(f"  {'OK  ' if ok else '!! FAIL'}  {name:16} {detail}")


def dist(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def main():
    print("\n  cosmos eval — real semantic position (projection of the self-owned embedding)\n")
    from lib.akasha.kernel import KernelDispatcher
    from lib.akasha.consciousness import CosmosMapper
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_cosmos_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin",
                                    "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                "id": "g"}, "local")

    def d(m, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": m,
                        "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
        return r.get("result") or r.get("error")

    def key(r):
        return (r or {}).get("key")

    cortex = k.manager.get_session("admin").local_cortex

    # Three topic clusters (5 each) with shared vocabulary within, disjoint across.
    topics = {
        "bird":    ["swallow migrates north spring warm nesting season",
                    "warbler flies north in spring to the warm nest",
                    "migrating bird returns north each spring to breed",
                    "northern nest spring migration warm season arrives",
                    "spring swallow warm north migrate to nesting ground"],
        "finance": ["stock market lower interest rate bond yield today",
                    "bond yield rose as stock fell interest inflation",
                    "interest rate stock price bond market investor concern",
                    "market closed lower rate concern over bond yields",
                    "stock bond yield interest rate inflation falling"],
        "cooking": ["recipe onion garlic simmer tomato sauce basil",
                    "chop garlic and onion fry in olive oil pan",
                    "simmer tomato sauce with basil garlic over pasta",
                    "bake bread with flour yeast in the hot oven",
                    "fry onion garlic in butter over the pan heat"],
    }
    keys = {t: [key(d("w", {"content": c})) for c in cs] for t, cs in topics.items()}
    allk = [kk for t in keys for kk in keys[t]]
    pos = {kk: CosmosMapper.position(cortex, kk) for kk in allk}

    # C1 — semantic layout: same-topic pairs closer than cross-topic pairs (population mean).
    intra_ds, cross_ds = [], []
    for i, a in enumerate(allk):
        for b in allk[i + 1:]:
            same = any(a in keys[t] and b in keys[t] for t in keys)
            (intra_ds if same else cross_ds).append(dist(pos[a], pos[b]))
    intra = sum(intra_ds) / len(intra_ds)
    cross = sum(cross_ds) / len(cross_ds)
    record("C1 layout", intra < cross,
           f"mean intra-topic dist={intra:.3f} < cross-topic dist={cross:.3f} "
           f"({len(intra_ds)}+{len(cross_ds)} pairs)")

    # C2 — not degenerate: positions vary and are not all zero (the old hash-placeholder bug).
    allpos = list(pos.values())
    nonzero = any(abs(x) > 1e-6 for p in allpos for x in p)
    distinct = len({tuple(round(x, 3) for x in p) for p in allpos}) == len(allpos)
    record("C2 non-degenerate", nonzero and distinct,
           f"nonzero={nonzero}, all-distinct={distinct}")

    # C3 — graph geometry: dive.look cosmos nodes carry x/y/z + a varying degree-based val.
    # Give the focus extra links so its degree (hence a neighbour's val) is meaningful.
    hub = keys["bird"][0]
    for b in keys["bird"][1:] + keys["finance"][:1]:
        d("ln", {"src": hub, "dst": b, "rel": "sys:associated_with"})
    dive = d("look", {"id": hub, "scope": 2})
    cnodes = ((dive or {}).get("cosmos") or {}).get("nodes", [])
    has_xyz = all(all(ax in n for ax in ("x", "y", "z")) for n in cnodes) and len(cnodes) >= 3
    vals = [n.get("val") for n in cnodes]
    val_varies = len(set(vals)) > 1
    record("C3 graph geom", has_xyz and val_varies,
           f"nodes={len(cnodes)}, all-have-xyz={has_xyz}, val-varies={val_varies} ({sorted(set(vals))[:5]})")

    # C4 — scatter spread: the present-scatter consumer now gets a real spread, not origin-stack.
    sv = d("survey.new", {"title": "T"})
    q = (d("survey.q.add", {"text": "How do you commute to work each weekday morning?", "order": 1})
         or {}).get("question_id")
    csv = ("respondent,commute\nalice,the express train downtown\nbob,a long bicycle ride\n"
           "carol,driving the car on the highway\ndave,walking through the city park\n")
    d("contexa.ingest", {"survey": sv.get("survey_id"), "text": csv, "format": "csv",
                         "map": f"commute:{q}"})
    sc = d("jataka.present", {"survey": sv.get("survey_id"), "as": "scatter"})
    pts = (sc or {}).get("points", [])
    uniq = {(round(p["x"], 3), round(p["y"], 3)) for p in pts}
    record("C4 scatter spread", len(pts) >= 3 and len(uniq) >= 3,
           f"points={len(pts)}, distinct-positions={len(uniq)}")

    # C5 — fitted layout (server-side, zero GUI algorithm): once a learned distributional
    # model exists, positions project onto its PRINCIPAL (SVD-ordered) axes instead of the
    # floor random projection — and still cluster by topic. The GUI is unchanged (still just
    # reads x/y/z); the crisper layout is fit on the server, matching the "no algorithm in the
    # GUI" constraint. (In production the boot auto-learn builds this model; here we build it.)
    from lib.akasha.semantic_learn import get_shared_model
    d("semantic.learn", {})
    lm = get_shared_model(getattr(cortex, "_nucleus", None))
    fpos = {kk: CosmosMapper.position(cortex, kk) for kk in allk}
    # The principal path is taken: position == _principal_3d(learned embed of the content).
    sample = allk[0]
    uses_principal = bool(lm) and fpos[sample] == CosmosMapper._principal_3d(
        lm.embed_text(cortex.get_chunk(sample)))
    fi, fc = [], []
    for i, a in enumerate(allk):
        for b in allk[i + 1:]:
            same = any(a in keys[t] and b in keys[t] for t in keys)
            (fi if same else fc).append(dist(fpos[a], fpos[b]))
    fitted_clusters = (sum(fi) / len(fi)) < (sum(fc) / len(fc))
    record("C5 fitted layout", uses_principal and fitted_clusters,
           f"learned-principal-path={uses_principal}, "
           f"clusters(intra={sum(fi)/len(fi):.3f}<cross={sum(fc)/len(fc):.3f})={fitted_clusters}")

    print()
    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"  {passed}/{total} phases passed"
          + (f", {total - passed} FAILED" if passed < total else ""))
    if passed < total:
        print("\nRESULT: FAIL — cosmos position is not reflecting the real semantic layer.")
        return 1
    print("\nRESULT: PASS — the cosmos space is real: positions project the self-owned embedding "
          "(same topic clusters together), the graph carries coordinates + degree size, and "
          "downstream scatter spreads.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
