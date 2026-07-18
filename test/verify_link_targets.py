#!/usr/bin/env python3
"""
Post-load link-target verifier — the runtime guard for cross-pack `ln` mis-binding.

Sibling to verify_set_memberships.py. It catches the failure the test context found:
a cross-pack `ln` (e.g. base1's `ln ingred:fruit:apple score:0.25 rec:acidity`) that ran
before its namespaced source atom (defined in base2) existed, so the link attached to the
bare proto-word "apple" instead of the real body atom `ingred:fruit:apple`.

Point it at a loaded nucleus DB. For every `ln SRC DST REL` in the ontology whose SRC is a
namespaced atom that IS loaded, it asserts a link with that relation actually hangs off the
REAL atom (SRC resolves to its body key, and the links table has a row from that key with
REL). An atom that was not loaded (opt-in pack disabled) is SKIPPED, so the check is correct
for both Seeds and Thesaurus loads. A FAILURE means the source atom is loaded but carries no
such link — the link went to a proto-word instead. Any failure exits non-zero.

Usage:
    python test/verify_link_targets.py [path/to/nucleus.db]
    (defaults to data/central/nucleus.db)

Only namespaced sources (id contains ':') are checked — bare proto-words legitimately are
the source of weave links, and checking those would be noise.
"""
import glob
import os
import re
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def collect_links(ont_dir):
    """Return [(src, rel, relpath)] for every `ln SRC DST REL` in the ontology."""
    out = []
    for fp in glob.glob(os.path.join(ont_dir, "**", "*.ak"), recursive=True):
        rel = os.path.relpath(fp, ROOT)
        for raw in open(fp, encoding="utf-8", errors="replace"):
            s = raw.strip()
            if not s.startswith("ln "):
                continue
            parts = s.split()
            if len(parts) < 4:
                continue
            src, _dst, relation = parts[1], parts[2], parts[3]
            out.append((src, relation, rel))
    return out


def verify(db_path, ont_dir):
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    cur = con.cursor()

    def resolve(atom_id):
        cur.execute("SELECT key FROM aliases WHERE alias=?", (atom_id,))
        r = cur.fetchone()
        if r:
            return r[0]
        cur.execute("SELECT 1 FROM chunks WHERE key=?", (atom_id,))
        return atom_id if cur.fetchone() else None

    def has_link(src_key, relation):
        cur.execute("SELECT 1 FROM links WHERE src=? AND rel=? LIMIT 1", (src_key, relation))
        return cur.fetchone() is not None

    links = collect_links(ont_dir)
    checked = skipped = ok = 0
    seen = set()
    misbound = []          # (src, rel, file) — source loaded but no link off the real atom
    for src, relation, rel in links:
        # only namespaced sources — bare proto-words are legitimate weave-link sources
        if ":" not in src:
            skipped += 1
            continue
        key = (src, relation)
        if key in seen:
            continue
        seen.add(key)
        src_key = resolve(src)
        if not src_key:
            skipped += 1     # source atom not loaded (opt-in pack) — not a failure
            continue
        checked += 1
        if has_link(src_key, relation):
            ok += 1
        else:
            misbound.append((src, relation, rel))
    con.close()
    return {"total": len(links), "checked": checked, "ok": ok,
            "skipped": skipped, "misbound": misbound}


def main(argv):
    db_path = argv[1] if len(argv) > 1 else os.path.join(ROOT, "data", "central", "nucleus.db")
    ont_dir = os.path.join(ROOT, "ontology")
    if not os.path.isfile(db_path):
        print(f"  SKIP  no loaded nucleus at {db_path} — run after a full ontology load")
        return 0
    r = verify(db_path, ont_dir)
    print(f"\n  ln (namespaced src) checked: {r['checked']}  |  linked OK: {r['ok']}  "
          f"|  skipped: {r['skipped']}")
    if r["misbound"]:
        print(f"\n  FAIL — {len(r['misbound'])} link(s) mis-bound (source atom loaded but the "
              f"relation hangs off a proto-word, not the real atom):")
        for src, relation, rel in r["misbound"][:20]:
            print(f"    {src} —{relation}→ ?   ({rel})")
        if len(r["misbound"]) > 20:
            print(f"    …+{len(r['misbound']) - 20} more")
        print("\nRESULT: FAIL — cross-pack links regressed (proto-word mis-binding).")
        return 1
    print("\nRESULT: PASS — every loaded namespaced link hangs off its real atom.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
