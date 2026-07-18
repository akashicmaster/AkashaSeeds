#!/usr/bin/env python3
"""
Post-load set-membership verifier — the runtime half of the cross-pack orphan guard.

`test/check_invariants.py::check_set_membership_orphans` is STATIC: it proves every
`set.add id=Y` in the ontology has a matching `def`/`al` SOMEWHERE. That catches a
genuinely-undefined id, but NOT the failure the test context found — where the id IS
defined (in another pack) yet its membership is silently dropped at load time because
`set.add` ran before the target atom existed.

This script is the RUNTIME assertion the static check cannot make. Point it at a loaded
nucleus DB (the real thing, after a full ontology load) and it asserts, for every
`set.add name=X id=Y` in the ontology:

    1. Y resolves to a nucleus key (via the aliases table, or Y is itself a chunk key), AND
    2. that key exists as an atom (chunks), AND
    3. (X, key) is present in the collections table.

An atom that simply was not loaded (an opt-in pack disabled in this edition) is reported
as SKIPPED, not failed — so the check is correct for both Seeds (partial load) and
Thesaurus (full load). A FAILURE means: the atom IS loaded but its set membership was
LOST — exactly the pack-split regression. Any failure exits non-zero.

Usage:
    python test/verify_set_memberships.py [path/to/nucleus.db]
    (defaults to data/central/nucleus.db — the standard runtime location)

Run it as the post-load smoke step of a release soak test, right after the ontology
finishes loading. It would have caught the set:ingred:* regression (static check passes,
this fails with 'membership dropped').
"""
import glob
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def collect_set_adds(ont_dir):
    """Return [(name, id, relpath)] for every set.add across the ontology .ak files."""
    import re
    name_re = re.compile(r'\bname="([^"]+)"')
    id_re = re.compile(r'\bid="([^"]+)"')
    out = []
    for fp in glob.glob(os.path.join(ont_dir, "**", "*.ak"), recursive=True):
        rel = os.path.relpath(fp, ROOT)
        for raw in open(fp, encoding="utf-8", errors="replace"):
            s = raw.strip()
            if not s.startswith("set.add"):
                continue
            n = name_re.search(s)
            i = id_re.search(s)
            if n and i:
                out.append((n.group(1), i.group(1), rel))
    return out


def verify(db_path, ont_dir):
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    cur = con.cursor()

    def resolve(atom_id):
        cur.execute("SELECT key FROM aliases WHERE alias=?", (atom_id,))
        r = cur.fetchone()
        if r:
            return r[0]
        # id may itself be a content-address key
        cur.execute("SELECT 1 FROM chunks WHERE key=?", (atom_id,))
        return atom_id if cur.fetchone() else None

    def chunk_exists(key):
        cur.execute("SELECT 1 FROM chunks WHERE key=?", (key,))
        return cur.fetchone() is not None

    def in_collection(name, key):
        cur.execute("SELECT 1 FROM collections WHERE name=? AND key=?", (name, key))
        return cur.fetchone() is not None

    set_adds = collect_set_adds(ont_dir)
    checked = skipped = ok = 0
    dropped = []          # (name, id, file) — atom loaded but membership lost  → FAIL
    for name, atom_id, rel in set_adds:
        key = resolve(atom_id)
        if not key or not chunk_exists(key):
            skipped += 1     # atom not loaded (opt-in pack disabled) — not a failure
            continue
        checked += 1
        if in_collection(name, key):
            ok += 1
        else:
            dropped.append((name, atom_id, rel))
    con.close()
    return {"total": len(set_adds), "checked": checked, "ok": ok,
            "skipped": skipped, "dropped": dropped}


def main(argv):
    db_path = argv[1] if len(argv) > 1 else os.path.join(ROOT, "data", "central", "nucleus.db")
    ont_dir = os.path.join(ROOT, "ontology")
    if not os.path.isfile(db_path):
        print(f"  SKIP  no loaded nucleus at {db_path} — run after a full ontology load")
        return 0
    r = verify(db_path, ont_dir)
    print(f"\n  set.add total: {r['total']}  |  loaded & checked: {r['checked']}  "
          f"|  in-set OK: {r['ok']}  |  skipped (atom not loaded): {r['skipped']}")
    if r["dropped"]:
        print(f"\n  FAIL — {len(r['dropped'])} set membership(s) LOST at load "
              f"(atom loaded but not in its set):")
        for name, atom_id, rel in r["dropped"][:20]:
            print(f"    {name} ← {atom_id}   ({rel})")
        if len(r["dropped"]) > 20:
            print(f"    …+{len(r['dropped']) - 20} more")
        print("\nRESULT: FAIL — cross-pack set memberships regressed.")
        return 1
    print("\nRESULT: PASS — every loaded set.add membership survived.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
