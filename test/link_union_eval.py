#!/usr/bin/env python3
"""
link-union eval — adjacency merges local cell + shared nucleus, never either/or.

An atom's edges can be split across a per-user cell (local_cortex) and the shared
nucleus: a proto-word's ontology `specializes` senses live in the nucleus, while a
user's own graph may hold an unrelated edge to the same proto-word. The composite
adjacency accessors used to fall back to the nucleus ONLY when the local side was
empty (`if not links`), so one local edge hid every nucleus edge — the path to the
same-leaf namespaced atoms vanished across r / link.list / assoc / dive. These
accessors must UNION both stores (dedup by endpoint+rel).

  U1 nucleus-only        — with an empty cell, the nucleus senses are visible.
  U2 union survives local — after ONE local edge, BOTH the local edge AND the
                            nucleus senses are returned (the bug: only the local).
  U3 outgoing union       — same guarantee for get_adjacent_links.
  U4 magnetic union       — get_magnetic_neighborhood merges both directions.
  U5 dedup                — an edge present in BOTH stores appears once, not twice.

Run:  python test/link_union_eval.py
"""
import os, sys, tempfile, hashlib
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT); sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
os.environ["AKASHA_NO_AUTOLEARN"] = "1"

_results = []
def record(name, ok, detail=""):
    _results.append((name, ok, detail))
    print(f"  {'OK  ' if ok else '!! FAIL'}  {name:20} {detail}")


def main():
    print("\n  link-union eval — adjacency merges cell + nucleus (never either/or)\n")
    from lib.akasha.composite import AkashaEngine, NucleusEngine

    base = tempfile.mkdtemp(prefix="akasha_union_")
    nuc = NucleusEngine(f"{base}/nucleus.db")
    cell = AkashaEngine(f"{base}/cell.db")
    cell.attach_nucleus(nuc)

    def key(s): return hashlib.sha256(s.encode()).hexdigest()

    # Nucleus: proto-word `apple` + two senses that specialize it (ontology-shaped).
    proto = key("apple")
    nuc.core.put_chunk_raw(proto, "apple", "{}", "system", "verified", 1.0)
    nuc.core.put_alias(proto, "apple")
    sense_keys = []
    for sense, desc in [("word:en:apple", "Fruit word"), ("ingred:fruit:apple", "Culinary fruit")]:
        sk = key(sense); sense_keys.append(sk)
        nuc.core.put_chunk_raw(sk, desc, "{}", "system", "verified", 1.0)
        nuc.core.put_alias(sk, sense)
        nuc.core.put_link_raw(sk, proto, "specializes", author="system", status="inferred", ts=1.0)

    def in_srcs():  return {s for s, _ in cell.get_incoming_links(proto)}
    def out_dsts(): return {dst for dst, _ in cell.get_adjacent_links(proto)}

    # U1 — empty cell: nucleus senses visible.
    record("U1 nucleus-only", in_srcs() == set(sense_keys),
           f"incoming={len(in_srcs())} (want 2)")

    # Give the cell ONE unrelated local incoming edge to the proto-word.
    mine = key("mynote:apple")
    cell.core.put_chunk_raw(mine, "my apple note", "{}", "user", "verified", 1.0)
    cell.core.put_link_raw(mine, proto, "calc:associated_with", author="user", status="verified", ts=1.0)

    # U2 — union survives: local edge AND both nucleus senses.
    got = in_srcs()
    record("U2 union survives local", got == set(sense_keys) | {mine},
           f"incoming={len(got)} (want 3: 1 local + 2 nucleus)")

    # U3 — outgoing union: a local out-edge must not hide a nucleus out-edge.
    tgt_nuc = key("emo:joy"); tgt_loc = key("user:tag")
    nuc.core.put_chunk_raw(tgt_nuc, "joy", "{}", "system", "verified", 1.0)
    nuc.core.put_link_raw(proto, tgt_nuc, "calc:associated_with", author="system", status="verified", ts=1.0)
    cell.core.put_chunk_raw(tgt_loc, "tag", "{}", "user", "verified", 1.0)
    cell.core.put_link_raw(proto, tgt_loc, "calc:tagged", author="user", status="verified", ts=1.0)
    od = out_dsts()
    record("U3 outgoing union", {tgt_nuc, tgt_loc} <= od,
           f"outgoing={len(od)} has both nucleus+local={ {tgt_nuc, tgt_loc} <= od }")

    # U4 — magnetic neighborhood merges both directions from both stores.
    mag = cell.get_magnetic_neighborhood(proto)
    mag_keys = {m["key"] for m in mag}
    want = set(sense_keys) | {mine, tgt_nuc, tgt_loc}
    record("U4 magnetic union", want <= mag_keys,
           f"magnetic={len(mag)} covers cell+nucleus both-way={want <= mag_keys}")

    # U5 — an edge present in BOTH stores is not double-counted.
    dup = key("dup:target")
    nuc.core.put_chunk_raw(dup, "dup", "{}", "system", "verified", 1.0)
    nuc.core.put_link_raw(proto, dup, "calc:associated_with", author="system", status="verified", ts=1.0)
    cell.core.put_link_raw(proto, dup, "calc:associated_with", author="user", status="verified", ts=1.0)
    dup_count = sum(1 for dst, rel in cell.get_adjacent_links(proto)
                    if dst == dup and rel == "calc:associated_with")
    record("U5 dedup", dup_count == 1, f"same edge in both stores appears {dup_count}x (want 1)")

    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"\n  {passed}/{total} passed\n")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
