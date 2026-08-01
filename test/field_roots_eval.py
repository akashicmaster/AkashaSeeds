#!/usr/bin/env python3
"""
Field-root eval — the new apex concepts (philosophy / narrative / ling / emo:emotion) that unify
each field's sys:is_a branches so the concept navigator can show a room as a taxonomy
(archives ROOM_ROOT). Mirrors the roll-up the ontology/*/*_root.ak files perform once loaded next
to their branches: apex ← branch ← entry.

  FR1 philosophy  — concept.tree root=philosophy shows its branches (logic, ethics) as taxa.
  FR2 emo:emotion — root=emo:emotion shows the basic emotions; a finer feeling folds under joy.
  FR3 narrative   — root=narrative → narrative.typology → a story type (2-tier).
  FR4 ling        — root=ling shows the linguistics branches.
  FR5 room path   — a room entry (phil:truth) is reachable by descending from the apex.

Run:  python test/field_roots_eval.py
"""
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
os.environ["AKASHA_NO_AUTOLEARN"] = "1"

_results = []


def record(name, ok, detail=""):
    _results.append((name, ok, detail))
    print(f"  {'OK  ' if ok else '!! FAIL'}  {name:14} {detail}")


# apexes + a representative branch/entry slice per field (the real packs have the full sets).
_DEFS = {
    "philosophy": "Philosophy apex.", "philosophy.logic": "Logic branch.",
    "philosophy.ethics": "Ethics branch.", "phil:truth": "truth (a logic entry).",
    "phil:virtue": "virtue (an ethics entry).",
    "emo:emotion": "Emotion apex.", "emo:joy": "Joy family.", "emo:elation": "elation (joy).",
    "narrative": "Narrative apex.", "narrative.typology": "Typology group.",
    "narrative.typology.journey": "The Journey.", "nar:odyssey": "odyssey (a journey).",
    "ling": "Linguistics apex.", "ling.syntax": "Syntax branch.", "ling:phrase": "phrase (syntax).",
}
_ISA = [
    # roll-ups (what *_root.ak adds)
    ("philosophy.logic", "philosophy"), ("philosophy.ethics", "philosophy"),
    ("emo:joy", "emo:emotion"),
    ("narrative.typology.journey", "narrative.typology"), ("narrative.typology", "narrative"),
    ("ling.syntax", "ling"),
    # existing room-entry / finer-feeling links (already in the packs)
    ("phil:truth", "philosophy.logic"), ("phil:virtue", "philosophy.ethics"),
    ("emo:elation", "emo:joy"),
    ("nar:odyssey", "narrative.typology.journey"), ("ling:phrase", "ling.syntax"),
]


def main():
    print("\n  Field-root eval — apex concepts light up each room's taxonomy\n")
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_froot_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin", "passphrase": "pw"}}, "id": "g"}, "local")

    def loc(m, **data):
        return k.dispatch({"jsonrpc": "2.0", "method": m,
                           "params": {"session_token": "admin", "data": data}, "id": 1}, "local")

    for a, d in _DEFS.items():
        loc("def", name=a, description=d, scope="universal")
    for s, d in _ISA:
        loc("ln", src=s, dst=d, rel="sys:is_a", scope="universal")

    def net(_rpc, tok=None, **fields):
        p = {"session_token": tok} if tok else {}
        p.update(fields)
        return k.dispatch({"jsonrpc": "2.0", "method": _rpc, "params": p, "id": 9}, "network")

    atok = net("auth.verify", user_id="admin", passphrase="pw")["result"]["session_token"]

    def branches(root):
        r = net("concept.tree", atok, root=root, depth=1).get("result") or {}
        return {c["id"] for c in (r.get("tree") or {}).get("children", [])}

    record("FR1 philosophy", branches("philosophy") == {"philosophy.logic", "philosophy.ethics"},
           f"philosophy→{sorted(branches('philosophy'))}")
    record("FR2 emo:emotion", branches("emo:emotion") == {"emo:joy"},
           f"emo:emotion→{sorted(branches('emo:emotion'))}")
    record("FR3 narrative", branches("narrative") == {"narrative.typology"},
           f"narrative→{sorted(branches('narrative'))}")
    record("FR4 ling", branches("ling") == {"ling.syntax"},
           f"ling→{sorted(branches('ling'))}")

    # FR5 — a room entry is reachable by descending the apex (depth 2: apex→branch→entry).
    r = net("concept.tree", atok, root="philosophy", depth=2, leaves="yes").get("result") or {}
    def walk(n):  # collect all ids in the tree
        ids = {n["id"]}
        for c in n.get("children", []):
            ids |= walk(c)
        return ids
    allids = walk(r.get("tree", {}))
    record("FR5 room path", {"philosophy", "philosophy.logic", "phil:truth"} <= allids,
           f"reachable={'phil:truth' in allids}")

    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"\n  {passed}/{total} passed\n")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
