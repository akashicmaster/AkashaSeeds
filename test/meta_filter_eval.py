#!/usr/bin/env python3
"""
meta-filter eval — lexicon definition atoms are excluded from sim/search by default.

The reldef:/nsdef: definition layer has lexically dense glosses, so once loaded it
crowds the top of content similarity (e.g. `sim Rome` returning `reldef:sys:part_of`).
sim / semantic.search now drop atoms that are members of the `rels`/`namespaces` sets
by default; `meta=1` (or `all=1`) opts them back in.

  MF1 default excludes  — a dense reldef atom does NOT appear in default search results,
                          while real content atoms do.
  MF2 opt-in includes   — with meta=1 the same reldef atom is allowed back in.
  MF3 node.sim excludes  — structural sim also drops the definition atom by default.

Run:  python test/meta_filter_eval.py
"""
import os, sys, hashlib, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT); sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
os.environ["AKASHA_NO_AUTOLEARN"] = "1"

_results = []
def record(name, ok, detail=""):
    _results.append((name, ok, detail))
    print(f"  {'OK  ' if ok else '!! FAIL'}  {name:18} {detail}")


def main():
    print("\n  meta-filter eval — lexicon atoms excluded from sim/search by default\n")
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_meta_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin",
                                    "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                "id": "g"}, "local")

    def d(m, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": m,
                        "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
        return r.get("result") or r.get("error")

    # Content atoms that share the query vocabulary.
    for s in ("Rome was an ancient mediterranean city and empire",
              "Carthage was an ancient mediterranean city and sea power",
              "Athens was an ancient mediterranean city of philosophers"):
        d("w", {"content": s})

    # Two crowding populations, both with glosses sharing the query vocabulary:
    #  • lexicon layer  — reldef: atom in the `rels` set
    #  • abstract hub   — an emo:/sys: definition atom (indexed by ns:emo / ns:sys)
    reldef = d("def", {"name": "reldef:geo:near",
                       "description": "near — ancient mediterranean city adjacency relation between two places"})
    reldef_key = reldef["key"]
    d("set.add", {"name": "rels", "id": reldef_key})

    emo_hub = d("def", {"name": "emo:testawe",
                        "description": "awe — ancient mediterranean city reverence wonder emotion definition"})
    emo_key = emo_hub["key"]        # member of ns:emo (abstract hub, NOT in rels/namespaces)
    sys_hub = d("def", {"name": "sys:testrel",
                        "description": "ancient mediterranean city structural relation definition"})
    sys_key = sys_hub["key"]        # member of ns:sys

    # A CONTENT-namespace atom that must NOT be excluded (guards over-exclusion).
    concept_hub = d("def", {"name": "concept:testcity",
                            "description": "an ancient mediterranean city concept"})
    concept_key = concept_hub["key"]

    q = "ancient mediterranean city"

    # MF1 — default search excludes BOTH lexicon and abstract-hub atoms; keeps content.
    r1 = d("semantic.search", {"query": q, "limit": 15})
    keys1 = [x["key"] for x in r1.get("results", [])]
    has_content = any("Rome" in x["preview"] or "Carthage" in x["preview"] or "Athens" in x["preview"]
                      for x in r1.get("results", []))
    excluded = reldef_key not in keys1 and emo_key not in keys1 and sys_key not in keys1
    record("MF1 default excludes", excluded and has_content,
           f"reldef={reldef_key not in keys1} emo={emo_key not in keys1} sys={sys_key not in keys1} content={has_content}")

    # MF2 — meta=1 opts them all back in.
    r2 = d("semantic.search", {"query": q, "limit": 15, "meta": 1})
    keys2 = [x["key"] for x in r2.get("results", [])]
    record("MF2 opt-in includes",
           reldef_key in keys2 and emo_key in keys2 and sys_key in keys2,
           f"reldef={reldef_key in keys2} emo={emo_key in keys2} sys={sys_key in keys2}")

    # MF2b — a CONTENT namespace atom is never excluded (present in the default results).
    record("MF2b content kept", concept_key in keys1,
           f"concept_present_default={concept_key in keys1}")

    # MF3 — node.sim (structural) also drops the definition atom by default. Build a tiny
    # clique of content atoms + link the reldef atom in, learn, then sim from a content node.
    A = [d("w", {"content": f"citynode {i}"})["key"] for i in range(4)]
    for i in range(len(A)):
        for j in range(i + 1, len(A)):
            d("ln", {"src": A[i], "dst": A[j], "rel": "assoc"})
    d("ln", {"src": A[0], "dst": reldef_key, "rel": "assoc"})   # reldef is a linked node too
    d("node.learn", {"dim": 16, "walks": 40, "length": 8})
    ns = d("node.sim", {"id": A[1], "limit": 20})
    ns_keys = [x["key"] for x in ns.get("results", [])] if isinstance(ns, dict) else []
    ns_meta = d("node.sim", {"id": A[1], "limit": 20, "meta": 1})
    ns_meta_keys = [x["key"] for x in ns_meta.get("results", [])] if isinstance(ns_meta, dict) else []
    # Excluded by default; allowed with meta=1 (if the model placed it near A[1]).
    record("MF3 node.sim excludes", reldef_key not in ns_keys,
           f"reldef_excluded_default={reldef_key not in ns_keys} present_with_meta={reldef_key in ns_meta_keys}")

    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"\n  {passed}/{total} passed\n")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
