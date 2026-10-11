#!/usr/bin/env python3
"""
Cross-laboratory provenance eval — `gen.cross` (the Genealogy model's interdisciplinary overlay).

Two studies, no network:
  1. A synthetic 4-lens study proving the cross LOGIC: two lenses corroborate a boundary (a
     coincidence = corroborated provenance), one lens is a gradual cline (it ABSTAINS instead of
     casting a spurious vote), one lens breaks elsewhere (a held DIVERGENCE).
  2. The real Ayurveda object — the Caraka Saṃhitā's sthānas (scripts/_ayurveda_corpus) measured by
     many lenses at once (stylometry · attestation · chronology · concept · TRADITION 伝承 · botany ·
     geography). The stylometric/chronological/conceptual/tradition/attestation boundaries COINCIDE
     at the Dṛḍhabala seam (after Cikitsā I–XIII) — a corroborated provenance seam no single lens
     could claim; geography ABSTAINS (both strata NW Indian); botany DIVERGES (its boundary tracks
     the therapeutic subject-matter, not the compositional seam). Non-forcing: nothing is collapsed.

Run:  python app/test/cross_provenance_eval.py     (exit 0 = all pass)
"""
import hashlib, os, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT); sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def main():
    from lib.akasha.kernel import KernelDispatcher
    from api.gateway import AkashaGateway
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_cross_"))
    gw = AkashaGateway(kernel_client=k)
    import shlex

    def C(method, **kw):
        line = " ".join([method] + [f"{a}={shlex.quote(str(v))}" for a, v in kw.items() if str(v) != ""])
        gw.dispatch({"jsonrpc": "2.0", "method": "sys.cli_exec",
                     "params": {"session_token": "admin", "data": {"command": line}}, "id": "c"}, "local")

    def D(method, data):
        r = gw.dispatch({"jsonrpc": "2.0", "method": method,
                         "params": {"session_token": "admin", "data": data}, "id": "m"}, "local")
        return r.get("result") or r.get("error") or {}

    gw.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                 "params": {"session_token": "admin", "data": {"user_name": "admin",
                            "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def build(wid, loci, features, matrix, layers=()):
        C("gen.work", id=wid, title=wid, kind="stratified")
        for lid, ltitle, ldesc in layers:
            C("gen.layer", work=wid, id=lid, title=ltitle, desc=ldesc)
        prev = ""
        for lo in loci:
            kw = dict(work=wid, id=lo[0], title=lo[1])
            if len(lo) > 2 and lo[2]:
                kw["layer"] = lo[2]
            if len(lo) > 3 and lo[3]:
                kw["attested"] = lo[3]
            if prev:
                kw["after"] = prev
            C("gen.locus", **kw)
            prev = lo[0]
        for f in features:
            C("gen.feature", id=f[0], title=f[1], desc=f[2] if len(f) > 2 else "",
              higher=f[3] if len(f) > 3 else "", lens=f[-1])
        for lo in loci:
            for f in features:
                C("gen.measure", work=wid, locus=lo[0], feature=f[0], value=matrix[lo[0]][f[0]])

    # ══ 1. synthetic 4-lens study ══════════════════════════════════════════════
    LOCI = [("l1", "L1"), ("l2", "L2"), ("l3", "L3"), ("l4", "L4"), ("l5", "L5")]
    FEATS = [("fa", "A", "", "", "alpha"), ("fb", "B", "", "", "beta"),
             ("fc", "C", "", "", "gamma"), ("fd", "D", "", "", "delta")]
    #  alpha & beta break sharply after L2; gamma is a gradual cline (abstains); delta breaks after L4.
    MX = {
        "l1": {"fa": 0.10, "fb": 0.10, "fc": 0.50, "fd": 0.10},
        "l2": {"fa": 0.12, "fb": 0.11, "fc": 0.55, "fd": 0.11},
        "l3": {"fa": 0.80, "fb": 0.82, "fc": 0.60, "fd": 0.12},
        "l4": {"fa": 0.79, "fb": 0.80, "fc": 0.65, "fd": 0.13},
        "l5": {"fa": 0.81, "fb": 0.83, "fc": 0.70, "fd": 0.90},
    }
    build("synth", LOCI, FEATS, MX)
    x = D("gen.cross", {"work": "synth", "threshold": "0.6"})
    lanes = {L["lens"]: L for L in x.get("lenses", [])}
    coincide = x.get("coincidence", [])
    check("synthetic: the consensus boundary is after L2 (where alpha & beta both break)",
          (x.get("consensus_after") or "").endswith("l2"), str(x.get("consensus_after")))
    check("synthetic: alpha & beta COINCIDE at L2 (≥2 lenses = corroborated provenance)",
          coincide and coincide[0]["count"] >= 2
          and {"alpha", "beta"} <= set(coincide[0]["lenses"]), str(coincide[:1]))
    check("synthetic: the gradual lens ABSTAINS (no dominant gap → no spurious vote)",
          lanes.get("gamma", {}).get("abstains") is True,
          f"gamma decisiveness={lanes.get('gamma', {}).get('decisiveness')}")
    div = {d["lens"]: d for d in x.get("divergence", [])}
    check("synthetic: the delta lens DIVERGES (its boundary falls elsewhere, after L4) — a held tension",
          div.get("delta", {}).get("kind") == "elsewhere"
          and (div.get("delta", {}).get("top_gap") or "").endswith("l4"), str(div.get("delta")))

    # ══ 2. the real Caraka Saṃhitā ═════════════════════════════════════════════
    from app.scripts._ayurveda_corpus import CARAKA as CS
    build(CS["id"], [(l[0], l[1], l[2], l[3]) for l in CS["loci"]],
          [(f[0], f[1], f[2], f[3], f[4]) for f in CS["features"]], CS["matrix"],
          layers=[(l[0], l[1], l[2]) for l in CS.get("layers", [])])
    cx = D("gen.cross", {"work": CS["id"], "threshold": "0.6"})
    lanes = {L["lens"]: L for L in cx.get("lenses", [])}
    co = cx.get("coincidence", [])
    div = {d["lens"]: d for d in cx.get("divergence", [])}
    check("Caraka: the consensus seam is after Cikitsā I–XIII (the Dṛḍhabala supplement boundary)",
          (cx.get("consensus_after") or "").endswith("cs_cikitsa_a"), str(cx.get("consensus_after")))
    check("Caraka: ≥4 lenses corroborate the seam, INCLUDING tradition (伝承) + stylometry",
          co and co[0]["count"] >= 4 and {"tradition", "stylometry"} <= set(co[0]["lenses"]),
          str(co[:1]))
    check("Caraka: geography ABSTAINS (both strata NW Indian — no spatial break)",
          lanes.get("geography", {}).get("abstains") is True, str(lanes.get("geography", {}).get("decisiveness")))
    check("Caraka: botany DIVERGES (materia-medica tracks the therapeutic subject, not the seam)",
          div.get("botany", {}).get("kind") == "elsewhere", str(div.get("botany")))
    # every projected mark traces back to evidence (P5)
    tr = D("gen.trace", {"id": cx.get("consensus_after")})
    check("provenance (P5): the consensus locus traces back to its evidence atom",
          bool(tr) and "error" not in tr, str(list(tr)[:4]))

    # ══ 3. cross-witness / cross-work alignment (divergent numbering) ═══════════
    # two recensions that number differently: a Pali work (books I–III) and a Chinese work whose
    # chapter 2 corresponds to Pali book III. @attested_in only flags THAT a parallel exists;
    # gen.align records WHICH locus ↔ which — the correspondence that survives the numbering gap.
    C("gen.work", id="pali_r", title="Pali recension", kind="stratified")
    C("gen.work", id="chin_r", title="Chinese recension", kind="stratified")
    prev = ""
    for lid, t in (("pr_b1", "I"), ("pr_b2", "II"), ("pr_b3", "III")):
        C("gen.locus", work="pali_r", id=lid, title=t, **({"after": prev} if prev else {})); prev = lid
    prev = ""
    for lid, t in (("cr_c1", "chapter 1"), ("cr_c2", "chapter 2")):
        C("gen.locus", work="chin_r", id=lid, title=t, **({"after": prev} if prev else {})); prev = lid
    a1 = D("gen.align", {"a": "pr_b1", "b": "cr_c1", "kind": "translation"})
    a2 = D("gen.align", {"a": "pr_b3", "b": "cr_c2", "kind": "translation",
                         "note": "Pali book III = Chinese chapter 2 (numbering diverges)"})
    check("gen.align records an explicit locus↔locus correspondence across recensions",
          a1.get("status") == "ok" and a2.get("status") == "ok" and a2.get("kind") == "translation",
          str(a2))
    al = D("gen.alignment", {"work": "pali_r"})
    by = {r["locus"].split(":")[-1]: r for r in al.get("alignment", [])}
    b3 = by.get("pr_b3", {}).get("aligned", [{}])[0]
    check("gen.alignment surfaces the cross-work correspondence despite divergent numbering "
          "(Pali III ↔ Chinese chapter 2)",
          al.get("pairs") == 2 and b3.get("locus", "").endswith("cr_c2")
          and b3.get("work", "").endswith("chin_r") and b3.get("kind") == "translation", str(b3))
    # the alignment is a first-class, traceable atom (P5)
    atr = D("gen.trace", {"id": b3.get("source_atom")})
    check("the alignment is a first-class traceable atom (kind=alignment, P5)",
          atr.get("kind") == "alignment", str(atr.get("kind")))

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("ALL PASS — cross-laboratory provenance: many lenses measure the SAME loci; coincidence is "
          "corroborated provenance, a flat lens abstains, a lens that breaks elsewhere is a held "
          "divergence — nothing collapsed. The Caraka Dṛḍhabala seam is corroborated across stylometry, "
          "chronology, concept, tradition (伝承) and attestation; geography abstains; botany diverges.")
    sys.exit(0)


if __name__ == "__main__":
    main()
