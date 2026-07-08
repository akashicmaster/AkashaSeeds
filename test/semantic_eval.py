#!/usr/bin/env python3
"""
Semantic embedding eval — the self-owned vector tier (G1 quick win).

Akasha's cosine paths (Jataka T2 dream, semantic search) were dead scaffolding: the
`semantic_vector` meta slot was read but never written, and `embed()` was an MD5
placeholder. This wakes them with a dependency-free, self-owned embedding (signed
feature-hashing over word tokens + character n-grams) that gives real cosine
structure for whitespace languages AND CJK — with an optional sentence-transformer
upgrade behind AKASHA_EMBED_MODEL.

  P1 separation   — similar texts score higher cosine than dissimilar ones (EN + JA),
                    using only the self-owned embedding (no external deps).
  P2 populate     — a committed text atom carries meta["semantic_vector"]; tiny/token
                    atoms do not (no meta bloat).
  P3 dream        — Jataka ranks semantically-related atoms above unrelated ones
                    (T2 cosine, previously never firing).

Run:  python test/semantic_eval.py
"""
import os
import sys
import time
import hashlib
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

_results = []


def record(name, ok, detail=""):
    _results.append((name, ok, detail))
    print(f"  {'OK  ' if ok else '!! FAIL'}  {name:14} {detail}")


def phase1_separation():
    from lib.akasha.tensor import TensorEngine
    te = TensorEngine()
    cases = [
        ("EN", "the cat sat on the mat", "a cat is sitting on a mat",
         "quantum chromodynamics lecture notes"),
        ("JA", "りんごは赤い果物です", "赤いりんごという果物", "量子力学の講義ノート"),
    ]
    ok = True
    detail = []
    for lang, anchor, similar, distant in cases:
        va = te._own_embed(anchor)
        sim = te.cosine(va, te._own_embed(similar))
        dis = te.cosine(va, te._own_embed(distant))
        ok = ok and (sim > dis) and (sim > 0.2)
        detail.append(f"{lang} sim={sim:.2f}>dis={dis:.2f}")
    record("P1 separation", ok, " | ".join(detail))


def phase2_populate():
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_sem_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin",
                                    "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                "id": "g"}, "local")

    def d(m, data):
        return k.dispatch({"jsonrpc": "2.0", "method": m,
                           "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")

    cortex = k.manager.get_session("admin").local_cortex
    big = d("w", {"content": "The migrating swallow returns north as spring arrives"})
    bk = big["result"]["key"]
    bmeta = cortex.get_meta(bk)
    has_vec = isinstance(bmeta, dict) and isinstance(bmeta.get("semantic_vector"), list)
    tiny = d("w", {"content": "hi"})     # < 8 chars → no vector (no bloat)
    tmeta = cortex.get_meta(tiny["result"]["key"])
    tiny_novec = not (isinstance(tmeta, dict) and tmeta.get("semantic_vector"))
    record("P2 populate", has_vec and tiny_novec,
           f"text atom has vector (dim={len(bmeta.get('semantic_vector', [])) if has_vec else 0}), "
           f"tiny atom skipped={tiny_novec}")
    return k, d, cortex, bk


def phase3_dream(k, d, cortex, focus_key):
    d("w", {"content": "Spring brings the swallows flying back to their northern nests"})
    d("w", {"content": "Warblers and swallows migrate north when the season warms"})
    d("w", {"content": "The stock market closed lower amid interest rate concerns"})
    from lib.jataka.engine import JatakaEngine
    j = JatakaEngine(k.manager.get_session("admin"))
    aff = j.dream_affinities(cortex, focus_key, threshold=0.15)

    def score_of(substr):
        for a in aff:
            if substr in (cortex.get_chunk(a["dst"]) or ""):
                return a["confidence"]
        return 0.0
    related = max(score_of("swallows flying back"), score_of("Warblers and swallows"))
    unrelated = score_of("stock market")
    ok = len(aff) > 0 and related > unrelated and related > 0.2
    record("P3 dream", ok,
           f"related={related:.2f} > unrelated={unrelated:.2f} (T2 cosine, {len(aff)} affinities)")


def phase4_learned():
    """The numpy learner captures *distributional* relatedness (co-occurrence) that the
    lexical feature-hashing floor cannot — words that share no characters but appear in
    similar contexts become close. Self-owned (numpy PPMI+SVD), learned from a corpus."""
    from lib.akasha.semantic_learn import OntologyLearner, tokens, cosine
    from lib.akasha.tensor import TensorEngine
    learner = OntologyLearner(dim=16, min_count=2, max_vocab=200)
    if not learner.available():
        record("P4 learned", True, "numpy absent — degrades to feature-hashing floor (ok)")
        return
    corpus = [
        "swallow migrate north spring bird nest season",
        "warbler migrate north bird sky season flight",
        "swallow bird nest egg tree branch spring",
        "finance bank interest rate loan money market",
        "bank interest rate market stock finance loan",
        "spring bloom flower garden warm season sun",
    ] * 3
    trained = learner.learn([tokens(c) for c in corpus])
    te = TensorEngine()

    def learned(a, b):
        return cosine(learner.embed_text(a), learner.embed_text(b))

    def lexical(a, b):
        return te.cosine(te._own_embed(a), te._own_embed(b))

    # "bank"/"interest" co-occur strongly but share no characters: learned >> lexical.
    l_bi, x_bi = learned("bank", "interest"), lexical("bank", "interest")
    # "swallow"/"migrate": learned finds the link the lexical floor scores at ~0.
    l_sm, x_sm = learned("swallow", "migrate"), lexical("swallow", "migrate")
    ok = trained and l_bi > 0.5 and l_bi > x_bi and l_sm > x_sm
    record("P4 learned", ok,
           f"bank~interest learned={l_bi:.2f}>lex={x_bi:.2f}, "
           f"swallow~migrate learned={l_sm:.2f}>lex={x_sm:.2f}")


def phase5_learn_persist_search():
    """semantic.learn builds the model from the full corpus and persists it to the
    nucleus vault; semantic.search then ranks with the learned tier; the model
    survives a restart (reload from the vault)."""
    from lib.akasha.semantic_learn import _SHARED
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    base = tempfile.mkdtemp(prefix="akasha_semlrn_")
    _SHARED["loaded"] = False
    _SHARED["model"] = None
    k = KernelDispatcher(series="seeds", base_dir=base)
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin",
                                    "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                "id": "g"}, "local")

    def d(m, data):
        return k.dispatch({"jsonrpc": "2.0", "method": m,
                           "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")

    corpus = [
        "The swallow migrates north as spring arrives and warms the air",
        "Warblers and swallows fly back to northern nests when the season warms",
        "Migrating birds return north each spring to breed and nest",
        "Gardeners plant flowers and seeds when the warm spring season begins",
    ] * 3
    for c in corpus:
        d("w", {"content": c})
    lr = d("semantic.learn", {"dim": 24, "max_vocab": 300}).get("result", {})
    learned_ok = lr.get("status") == "learned" and lr.get("vocab", 0) > 0
    nuc = k.manager.get_session("admin").nucleus
    persisted = bool(nuc.vault_retrieve("semantic", "model"))

    sr = d("semantic.search", {"query": "migrating birds fly north in spring", "limit": 1}).get("result", {})
    tier_learned = sr.get("tier") == "learned"
    top = (sr.get("results") or [{}])[0].get("preview", "")
    sensible = "north" in top or "spring" in top or "migrat" in top.lower()

    # restart: fresh process view → model must reload from the vault
    _SHARED["loaded"] = False
    _SHARED["model"] = None
    k2 = KernelDispatcher(series="seeds", base_dir=base)
    sr2 = k2.dispatch({"jsonrpc": "2.0", "method": "semantic.search",
                       "params": {"session_token": "admin",
                                  "data": {"query": "birds returning north", "limit": 1}},
                       "id": "t"}, "local").get("result", {})
    reload_ok = sr2.get("tier") == "learned"

    ok = learned_ok and persisted and tier_learned and sensible and reload_ok
    record("P5 learn+persist", ok,
           f"learned(vocab={lr.get('vocab')}), persisted={persisted}, "
           f"search tier={sr.get('tier')} sensible={sensible}, reload={reload_ok}")


def phase6_gap_scan():
    """gap.scan surfaces the self-expanding-loop entry points: concepts that are
    referenced a lot (important) but have few curated links (thin) rank highest; a
    well-linked concept of equal importance drops out."""
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_gap_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin",
                                    "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                "id": "g"}, "local")

    def d(m, data):
        return k.dispatch({"jsonrpc": "2.0", "method": m,
                           "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")

    def key(r):
        return (r.get("result") or {}).get("key")

    thin = key(d("w", {"content": "PhotosynthesisConceptHub"}))
    rich = key(d("w", {"content": "RespirationConceptHub"}))
    for i in range(6):
        a = key(d("w", {"content": f"observation number {i} about the biological process"}))
        d("ln", {"src": a, "dst": thin, "rel": "mentions"})
        d("ln", {"src": a, "dst": rich, "rel": "mentions"})
    for w in ["oxygen", "glucose", "cellular", "energy", "mitochondria"]:
        t = key(d("w", {"content": "TERM_" + w}))
        d("ln", {"src": rich, "dst": t, "rel": "thesaurus:related"})

    gaps = (d("gap.scan", {"limit": 10}).get("result") or {}).get("gaps", [])
    ranks = {g["key"]: i for i, g in enumerate(gaps)}
    thin_rank = ranks.get(thin, 999)
    rich_rank = ranks.get(rich, 999)
    # thin (important, uncurated) ranks strictly above rich (important, curated).
    ok = thin_rank < rich_rank and thin_rank <= 1
    record("P6 gap.scan", ok,
           f"thin@{thin_rank} < rich@{rich_rank} (important-but-thin ranks first)")


def phase7_autolearn():
    """The boot hook (_schedule_semantic_learn) builds and persists the model in the
    background from the ontology corpus — so semantic search/dream are smart from
    startup with no external model. It then BAKES the learned vector into each atom's
    meta (per-atom, IDLE bulk write) so the cosine paths use the learned tier without
    re-embedding. Skipped cleanly if numpy is absent."""
    from lib.akasha.semantic_learn import OntologyLearner, _SHARED, get_shared_model
    if not OntologyLearner.available():
        record("P7 autolearn", True, "numpy absent — auto-learn skipped, floor tier (ok)")
        return
    import json as _json
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_auto_"))
    nuc = k.manager.shared_nucleus
    corpus = [
        "Photosynthesis converts light energy into chemical energy in plant cells",
        "Chlorophyll in leaves captures sunlight to drive photosynthesis",
        "Cellular respiration releases energy from glucose in the mitochondria",
        "Plants use carbon dioxide and water to synthesize sugars in light",
        "Mitochondria are the powerhouse organelles of the eukaryotic cell",
    ] * 3
    keys = []
    for i, c in enumerate(corpus):
        keys.append(nuc.put_atom(c, {"type": "onto", "i": i}, author="admin"))
    _SHARED["loaded"] = False
    _SHARED["model"] = None
    k._schedule_semantic_learn()

    def baked_count():
        n = 0
        for key in set(keys):
            raw = nuc.core.get_chunk_raw(key)
            if not raw:
                continue
            try:
                m = _json.loads(raw.get("meta") or "{}")
            except Exception:
                m = {}
            if isinstance(m.get("semantic_vector"), list) and m["semantic_vector"]:
                n += 1
        return n

    persisted, baked = False, 0
    for _ in range(60):
        time.sleep(0.2)
        if not persisted and nuc.vault_retrieve("semantic", "model"):
            persisted = True
        if persisted:
            baked = baked_count()
            if baked > 0:
                break
    record("P7 autolearn", persisted and baked > 0,
           f"model persisted={persisted}, vectors baked into {baked}/{len(set(keys))} atoms")


def phase8_external_exclusion():
    """Externally-fetched atoms (provenance=external) are the enrichment MATERIAL, not
    a curation gap — unvetted web text must neither poison the learned model nor be
    surfaced by gap.scan. An external important-but-thin atom is excluded from
    gap.scan; an identical curated one is not (ASI06 guardrail)."""
    import json as _json
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_ext_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin",
                                    "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                "id": "g"}, "local")

    def d(m, data):
        return k.dispatch({"jsonrpc": "2.0", "method": m,
                           "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")

    def key(r):
        return (r.get("result") or {}).get("key")

    cortex = k.manager.get_session("admin").local_cortex
    native = key(d("w", {"content": "NativeCuratedConceptHub"}))
    ext = key(d("w", {"content": "ExternalFetchedConceptHub"}))
    # Tag `ext` as fetched web content (what _handle_contexa_fetch stamps).
    raw = cortex.core.get_chunk_raw(ext)
    try:
        m = _json.loads(raw.get("meta") or "{}")
    except Exception:
        m = {}
    m["provenance"] = "external"
    cortex.core.put_chunk_raw(ext, raw.get("content"), _json.dumps(m, ensure_ascii=False),
                              raw.get("author", "admin"), raw.get("status", "verified"),
                              time.time())
    # Both are important-but-thin: many inbound mentions, no curated links out.
    for i in range(6):
        a = key(d("w", {"content": f"remark {i} pointing at both concept hubs here"}))
        d("ln", {"src": a, "dst": native, "rel": "mentions"})
        d("ln", {"src": a, "dst": ext, "rel": "mentions"})

    gaps = (d("gap.scan", {"limit": 20}).get("result") or {}).get("gaps", [])
    gap_keys = {g["key"] for g in gaps}
    ok = native in gap_keys and ext not in gap_keys
    record("P8 external", ok,
           f"native surfaced={native in gap_keys}, external excluded={ext not in gap_keys}")


def phase9_gap_fetch():
    """gap.fetch closes the self-expanding loop: it finds the important-but-thin
    concepts and auto-fetches external context to enrich each, tagging every fetched
    atom provenance=external (guardrail) and linking it back to the concept via
    calc:enriches. Uses a mocked Contexa (no network); also checks the offline degrade
    path (fetch error → fetched=false, no exception) and that the fetched external atom
    is then excluded from gap.scan (no fetch→gap→fetch loop)."""
    import json as _json
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_gapf_"))
    if k.contexa is None:
        record("P9 gap.fetch", True, "ContexaEngine unavailable — gap.fetch skipped (ok)")
        return
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin",
                                    "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                "id": "g"}, "local")

    def d(m, data):
        return k.dispatch({"jsonrpc": "2.0", "method": m,
                           "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")

    def key(r):
        return (r.get("result") or {}).get("key")

    cortex = k.manager.get_session("admin").local_cortex
    thin = key(d("w", {"content": "IcarusMythConceptHub"}))
    d("al", {"id": thin, "name": "concept:icarus"})        # → gap query "icarus"
    for i in range(6):
        a = key(d("w", {"content": f"mention {i} referencing the icarus myth concept"}))
        d("ln", {"src": a, "dst": thin, "rel": "mentions"})

    # Mock the network: a canned Wikipedia-shaped result (what Contexa.fetch returns).
    calls = {"n": 0}

    def fake_fetch(query):
        calls["n"] += 1
        return {"source_type": "wikipedia",
                "text": f"[Icarus]\nIn Greek mythology Icarus flew too close to the "
                        f"sun on wings of wax and feathers, and fell into the sea. ({query})",
                "title": "Icarus", "url": "https://en.wikipedia.org/wiki/Icarus",
                "alias": "wiki:Icarus",
                "evidence": {"authority": 0.9, "reach": 1.0, "nature": "factual"}}

    k.contexa.fetch = fake_fetch
    res = (d("gap.fetch", {"limit": 1}).get("result") or {})
    fetched_ok = res.get("fetched") == 1 and res.get("enriched")
    entry = (res.get("enriched") or [{}])[0]
    fkey = entry.get("atom_key")

    # The fetched atom carries the provenance guardrail.
    fmeta = cortex.get_meta(fkey) if fkey else None
    provenance_ok = isinstance(fmeta, dict) and fmeta.get("provenance") == "external"

    # It links back to the thin concept via calc:enriches.
    inbound = cortex.get_incoming_links(thin) or []
    enriches_ok = any(fkey and str(p[0]) == fkey and "enriches" in str(p[1])
                      for p in inbound if len(p) > 1)

    # Offline degrade: a fetch error must not raise, just report fetched=false.
    def err_fetch(query):
        return {"error": "offline"}
    k.contexa.fetch = err_fetch
    thin2 = key(d("w", {"content": "DaedalusMythConceptHub"}))
    d("al", {"id": thin2, "name": "concept:daedalus"})
    for i in range(6):
        a = key(d("w", {"content": f"note {i} on daedalus the craftsman of the labyrinth"}))
        d("ln", {"src": a, "dst": thin2, "rel": "mentions"})
    res2 = (d("gap.fetch", {"limit": 5}).get("result") or {})
    degrade_ok = res2.get("fetched") == 0 and "error" not in res2

    # The fetched external atom is not itself surfaced as a gap (loop safety).
    gaps = (d("gap.scan", {"limit": 50}).get("result") or {}).get("gaps", [])
    no_loop = fkey not in {g["key"] for g in gaps}

    ok = fetched_ok and provenance_ok and enriches_ok and degrade_ok and no_loop
    record("P9 gap.fetch", ok,
           f"fetched+linked={fetched_ok and enriches_ok}, provenance=external={provenance_ok}, "
           f"offline-degrade={degrade_ok}, no-loop={no_loop}")


def phase10_node_vs_content():
    """Node-walk (structural) vs content (semantic) embeddings are complementary. Build a
    graph where the two signals are ORTHOGONAL: two link-clusters A and B (mutually linked
    within, one bridge between), where a_i and b_i (same index, different cluster) carry the
    SAME theme text. Then:
      - node-walk sees the LINK structure: a_i ~ a_j (same cluster) >> a_i ~ b_i (across).
      - content sees the TEXT:            a_i ~ b_i (same theme)   >> a_i ~ a_j (diff theme).
    The methods rank the a_i/b_i pair oppositely — each captures relatedness the other
    cannot. Self-owned, numpy; skipped cleanly if numpy is absent."""
    from lib.akasha.semantic_learn import (NodeWalkLearner, OntologyLearner, tokens, cosine)
    if not NodeWalkLearner.available():
        record("P10 node/content", True, "numpy absent — node embeddings skipped (ok)")
        return

    themes = [["apple", "fruit", "orchard", "harvest"],
              ["ocean", "wave", "tide", "salt"],
              ["mountain", "rock", "summit", "snow"],
              ["melody", "song", "rhythm", "chord"],
              ["engine", "gear", "piston", "motor"]]
    A = [f"a{i}" for i in range(5)]
    B = [f"b{i}" for i in range(5)]
    # Same neutral boilerplate for EVERY node, so cluster identity never leaks into the
    # text — content similarity is driven only by the shared theme (a_i and b_i match).
    boiler = " recorded in the shared archive index"
    content = {}
    for i, th in enumerate(themes):
        content[A[i]] = " ".join(th) + boiler
        content[B[i]] = " ".join(reversed(th)) + boiler

    # Links: mutually-connected clusters A and B, joined by a single bridge a0-b0.
    links = []
    for cluster in (A, B):
        for i in range(len(cluster)):
            for j in range(i + 1, len(cluster)):
                links.append({"src": cluster[i], "dst": cluster[j], "rel": "assoc"})
    links.append({"src": A[0], "dst": B[0], "rel": "bridge"})

    nw = NodeWalkLearner(dim=16, walks_per_node=40, length=10, seed=7)
    nw.learn(links)
    # structural: same-cluster pair vs across-cluster same-theme pair
    struct_same = nw.similarity(A[1], A[2])
    struct_across = nw.similarity(A[1], B[1])
    struct_ok = struct_same > struct_across

    cl = OntologyLearner(dim=16, min_count=1, max_vocab=400)
    cl.learn([tokens(content[k]) for k in list(A) + list(B)])
    def csim(x, y):
        return cosine(cl.embed_text(content[x]), cl.embed_text(content[y]))
    # semantic: same-theme cross-cluster pair vs diff-theme same-cluster pair
    cont_same_theme = csim(A[1], B[1])
    cont_diff_theme = csim(A[1], A[2])
    content_ok = cont_same_theme > cont_diff_theme

    # complementarity: on the SAME pair (A1,B1) the two disagree — structure says far,
    # content says near.
    complementary = struct_across < struct_same and cont_same_theme > cont_diff_theme

    ok = struct_ok and content_ok and complementary
    record("P10 node/content", ok,
           f"struct a1~a2={struct_same:.2f}>a1~b1={struct_across:.2f} | "
           f"content a1~b1={cont_same_theme:.2f}>a1~a2={cont_diff_theme:.2f} (complementary)")


def main():
    print("\n  semantic embedding eval — self-owned vector tier (G1)\n")
    phase1_separation()
    k, d, cortex, bk = phase2_populate()
    phase3_dream(k, d, cortex, bk)
    phase4_learned()
    phase5_learn_persist_search()
    phase6_gap_scan()
    phase7_autolearn()
    phase8_external_exclusion()
    phase9_gap_fetch()
    phase10_node_vs_content()

    print()
    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"  {passed}/{total} phases passed"
          + (f", {total - passed} FAILED" if passed < total else ""))
    if passed < total:
        print("\nRESULT: FAIL — the self-owned semantic tier regressed.")
        return 1
    print("\nRESULT: PASS — dependency-free embedding gives real cosine structure "
          "(EN + CJK); commit populates it; Jataka's T2 cosine tier is alive.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
