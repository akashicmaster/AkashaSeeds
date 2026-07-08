#!/usr/bin/env python3
"""
Emotion eval — the Akasha-native (link-based) emotion axis.

Emotions in Akasha are atoms in the `emo:` namespace; an atom "feels" an emotion by a
link (calc:associated_with / has_emotion / …) whose TARGET is an emo:* atom. Because atoms
are content-addressed, the stored link dst is a hash — the namespace lives in the alias — so
the emotion axis must resolve the target's ALIAS (the signal CosmosMapper.get_aura_color
uses), NOT string-match the relation. This eval guards that:

  E1 axis        — associate(axis="emotion") returns the emotion links (was silently empty:
                   the ontology has 0 emo:* relations but 500+ links TARGETING emo:* atoms).
  E2 profile     — emotion.profile returns a ranked, L1-normalised emotion vector.
  E3 weight/depth— stronger edges and nearer hops score higher (depth decay 1/depth).
  E4 empty       — an atom with no emotion links returns an empty vector, not an error.
  E5 void        — find_link_voids does NOT report 'emotion' as missing when it is present.

Run:  python test/emotion_eval.py
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


def _kernel():
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_emo_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin",
                                    "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                "id": "g"}, "local")
    return k


def main():
    print("\n  emotion eval — Akasha-native (link-based) emotion axis\n")
    k = _kernel()

    def d(m, data):
        return (k.dispatch({"jsonrpc": "2.0", "method": m,
                            "params": {"session_token": "admin", "data": data}, "id": "t"},
                           "local").get("result") or {})

    cortex = k.manager.get_session("admin").local_cortex
    # Emotion atoms (emo: aliases) — the ontology vocabulary.
    for e in ("fear", "awe", "sadness", "joy"):
        d("def", {"name": f"emo:{e}", "description": e})
    icarus = d("def", {"name": "concept:icarus",
                       "description": "Icarus flew too close to the sun"}).get("key")
    neutral = d("def", {"name": "concept:ledger",
                        "description": "A plain accounting ledger of numbers"}).get("key")
    # A 2-hop emotion: icarus → concept:fall → emo:sadness
    d("def", {"name": "concept:fall", "description": "a great fall"})

    # Emotion links the ontology way (relation is calc:/has_emotion; TARGET is emo:*).
    d("ln", {"src": "concept:icarus", "dst": "emo:fear", "rel": "calc:associated_with"})
    d("ln", {"src": "concept:icarus", "dst": "emo:awe", "rel": "has_emotion"})
    d("ln", {"src": "concept:icarus", "dst": "concept:fall", "rel": "calc:associated_with"})
    d("ln", {"src": "concept:fall", "dst": "emo:sadness", "rel": "calc:associated_with"})

    # E1 — associate axis=emotion returns emotion links (not empty).
    asc = cortex.associate(icarus, axis="emotion", scope=1)
    emo_assoc = [a for a in asc["associations"] if a["type"] == "emotion"]
    record("E1 axis", len(emo_assoc) >= 2,
           f"axis=emotion returned {len(emo_assoc)} emotion links (all type=emotion)")

    # E2 — emotion.profile: ranked, normalised vector containing the linked emotions.
    prof = d("emotion.profile", {"id": "concept:icarus", "scope": 1})
    emos = {e["emotion"]: e["score"] for e in prof.get("emotions", [])}
    total = round(sum(emos.values()), 3)
    e2 = "emo:fear" in emos and "emo:awe" in emos and abs(total - 1.0) < 1e-6
    record("E2 profile", e2,
           f"emotions={list(emos)}, sum={total}, dominant={prof.get('dominant')}")

    # E3 — depth decay: a 2-hop emotion (emo:sadness via concept:fall) scores below the
    # 1-hop ones. scope=2 so it is reachable; 1/depth weighting → sadness < fear/awe.
    prof2 = d("emotion.profile", {"id": "concept:icarus", "scope": 2, "normalize": "false"})
    raw = {e["emotion"]: e["score"] for e in prof2.get("emotions", [])}
    e3 = (raw.get("emo:sadness", 9) < raw.get("emo:fear", 0)
          and abs(raw.get("emo:sadness", 0) - 0.5) < 1e-6      # depth 2 → 1/2
          and abs(raw.get("emo:fear", 0) - 1.0) < 1e-6)        # depth 1 → 1/1
    record("E3 weight/depth", e3,
           f"1-hop fear={raw.get('emo:fear')}, 2-hop sadness={raw.get('emo:sadness')} (1/depth)")

    # E4 — an atom with no emotion links → empty vector, not an error.
    prof_n = d("emotion.profile", {"id": "concept:ledger"})
    e4 = prof_n.get("emotions") == [] and prof_n.get("dominant") is None
    record("E4 empty", e4, f"neutral atom → emotions={prof_n.get('emotions')} (no error)")

    # E5 — find_link_voids must NOT flag 'emotion' as missing when it is present.
    voids = cortex.find_link_voids(icarus)
    void_axes = {v["axis"] for v in voids}
    record("E5 void", "emotion" not in void_axes,
           f"'emotion' reported missing={('emotion' in void_axes)} (should be False)")

    print()
    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"  {passed}/{total} phases passed"
          + (f", {total - passed} FAILED" if passed < total else ""))
    if passed < total:
        print("\nRESULT: FAIL — the Akasha-native emotion axis regressed.")
        return 1
    print("\nRESULT: PASS — the link-based emotion axis evaluates: emotions are resolved by "
          "target namespace, weighted by strength and depth, into a normalised vector.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
