#!/usr/bin/env python3
"""
Exploration eval — do the navigation commands actually reach the meaning layer?

An audit found the meaning layer was built (`semantic_vector`, learned model, `NodeWalkLearner`,
`generate_view`, `emotion_profile`) but the exploration commands barely tapped it. These five
additions wire the exploration surface to it:

  X1 sim        — semantic.search id=<atom> anchors on an EXISTING atom's meaning ("find atoms
                  like THIS"), excluding the anchor. (Was: id treated as free text.)
  X2 view       — a standalone consciousness view (signposts / resonance / focus) without diving
                  or changing focus. (Was: generate_view reachable only through look/dive.)
  X3 emotion.find — the reverse of emotion.profile: atoms that FEEL a given emotion. (New.)
  X4 node.learn — learn structural node embeddings from the typed-link graph (was dead code).
  X5 node.sim   — atoms structurally similar to an atom ("connected the same way").

Run:  python test/explore_eval.py
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
    print(f"  {'OK  ' if ok else '!! FAIL'}  {name:14} {detail}")


def main():
    print("\n  exploration eval — navigation commands over the meaning layer\n")
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_expl_"))
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

    # X1 — atom-anchored semantic similarity.
    anchor = key(d("w", {"content": "The swallow migrates north as spring arrives and warms the air"}))
    d("w", {"content": "Warblers and swallows fly back to northern nests when the season warms"})
    d("w", {"content": "Migrating birds return north each spring to breed and nest"})
    d("w", {"content": "The stock market closed lower amid interest rate concerns about bonds"})
    r = d("sim", {"id": anchor, "limit": 3})
    res = r.get("results", [])
    anchor_excluded = all(x["key"] != anchor for x in res)
    top_is_bird = res and ("swallow" in res[0]["preview"].lower() or "migrat" in res[0]["preview"].lower()
                           or "bird" in res[0]["preview"].lower() or "north" in res[0]["preview"].lower())
    record("X1 sim", r.get("anchor") == anchor and anchor_excluded and bool(top_is_bird),
           f"anchored={r.get('anchor')==anchor}, anchor-excluded={anchor_excluded}, "
           f"top='{res[0]['preview'][:34] if res else None}'")

    # Emotion setup.
    for e in ("awe", "fear", "joy"):
        d("def", {"name": f"emo:{e}", "description": e})
    ic = key(d("def", {"name": "concept:icarus", "description": "Icarus flew too close to the sun"}))
    d("ln", {"src": "concept:icarus", "dst": "emo:awe", "rel": "calc:associated_with"})
    d("ln", {"src": "concept:icarus", "dst": "emo:fear", "rel": "has_emotion"})

    # X2 — standalone view (consciousness payload, no dive).
    v = d("view", {"id": "concept:icarus"})
    x2 = isinstance(v, dict) and "error" not in v and "signposts" in v and "resonance" in v \
        and v.get("focus", {}).get("alias") == "concept:icarus"
    record("X2 view", x2,
           f"keys={sorted(v.keys()) if isinstance(v, dict) else v}")

    # X3 — find-by-emotion (reverse lookup).
    ef = d("emotion.find", {"emo": "awe"})
    x3 = ef.get("count", 0) >= 1 and any(x["key"] == ic for x in ef.get("results", []))
    record("X3 emotion.find", x3,
           f"emotion={ef.get('emotion')}, count={ef.get('count')}, icarus={any(x['key']==ic for x in ef.get('results',[]))}")

    # X4 + X5 — structural node embeddings: two link-clusters bridged once. Contents are
    # DIGIT strings, which the weaver skips (no proto-word links), so the learned graph is
    # exactly the two explicit cliques + one bridge — deterministic and noise-free, isolating
    # the structural signal (X5 asserts "connected the same", not "worded the same").
    A = [key(d("w", {"content": s})) for s in ("10", "11", "12", "13", "14")]
    B = [key(d("w", {"content": s})) for s in ("20", "21", "22", "23", "24")]
    for cl in (A, B):
        for i in range(len(cl)):
            for j in range(i + 1, len(cl)):
                d("ln", {"src": cl[i], "dst": cl[j], "rel": "assoc"})
    d("ln", {"src": A[0], "dst": B[0], "rel": "bridge"})
    nl = d("node.learn", {"dim": 16, "walks": 40, "length": 10})
    record("X4 node.learn", nl.get("status") == "learned" and nl.get("nodes", 0) >= 10,
           f"status={nl.get('status')}, nodes={nl.get('nodes')}")

    ns = d("node.sim", {"id": A[1], "limit": 20})
    scores = {x["key"]: x["score"] for x in ns.get("results", [])}
    a_sc = [scores[a] for a in A if a in scores and a != A[1]]   # A1's four clique-mates
    # node.sim surfaces the anchor's structural neighbours: its clique-mates (identical
    # connectivity) all score high. (Cross-cluster B-members may also score high — the two
    # cliques are structurally isomorphic, and structural embeddings capture *role*, not just
    # community; content-vs-structure separation is proven cleanly in semantic_eval P10.)
    x5 = ns.get("mode") == "structural" and len(a_sc) >= 4 and min(a_sc) > 0.5
    record("X5 node.sim", x5,
           f"4 clique-mates surfaced, min structural score={min(a_sc):.2f}>0.5"
           if a_sc else "no clique-mates surfaced")

    print()
    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"  {passed}/{total} phases passed"
          + (f", {total - passed} FAILED" if passed < total else ""))
    if passed < total:
        print("\nRESULT: FAIL — an exploration→meaning-layer hook regressed.")
        return 1
    print("\nRESULT: PASS — exploration reaches the meaning layer: anchored similarity, a "
          "standalone view, find-by-emotion, and structural (node-walk) navigation.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
