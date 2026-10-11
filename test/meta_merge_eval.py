#!/usr/bin/env python3
"""
`merge_meta` — the atomic read-merge-write of an atom's meta (an ISA primitive, both backends).

Found when the purge order (3 October §2) deleted the pool-tally adoption: on a single-store cell a
`source.item.status` write was lost one run in three. The weave's salience bump (a JCL thread) read
the item's whole meta, the status door wrote the new status, and the bump then wrote its stale copy
back — the status reverted, the tally (already moved) no longer matched. Every caller that read the
meta, edited one field and wrote the whole meta back had the same lost update; the adoption had been
recounting the damage. The store now does the read, the merge and the write as ONE step: SQLite on
its single writer thread, Silica under the record's bank lock (`SilicaStore.update`, TRMW).

  §1  N threads × M increments of one field through `merge_meta(key, callable)` → exactly N·M.
  §2  two threads writing DIFFERENT fields of one atom both survive (no stale whole-meta copy).
  §3  `update_meta` with a stale copy that would revert an engine-owned field is refused at the
      write, against the record it replaces (the owned-field check runs inside the atomic step).
  §4  merge on a missing atom → None, nothing written; a merge that changes nothing writes nothing.
  §5  the composite writers that were read-edit-write (salience bump, set_meta) keep a concurrent
      writer's field: salience bumps on one thread + set_meta on another, both land.

Each section runs on SQLite and on Silica.

Run:  python test/meta_merge_eval.py     (exit 0 = all pass)
"""
import json
import os
import sys
import tempfile
import threading

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _backend(kind):
    d = tempfile.mkdtemp(prefix="akasha_merge_")
    if kind == "silica":
        from lib.akasha.backends.silica_backend import SilicaBackend
        return SilicaBackend(os.path.join(d, "t.db"))
    from lib.akasha.backends.sqlite import SQLiteBackend
    return SQLiteBackend(os.path.join(d, "t.db"))


def _meta(core, key):
    row = core.get_chunk_raw(key)
    return json.loads(row["meta"]) if row and row.get("meta") else {}


def _atom(core, key, meta):
    core.put_chunk_raw(key, "content " + key, json.dumps(meta), "eval", "verified", 0.0)
    return key


def _run(threads):
    ts = [threading.Thread(target=t) for t in threads]
    for t in ts:
        t.start()
    for t in ts:
        t.join()


def section_counter(kind, core):
    key = _atom(core, "k_counter", {"n": 0})
    N, M = 8, 60

    def worker():
        for _ in range(M):
            core.merge_meta(key, lambda m: {"n": int(m.get("n", 0)) + 1})
    _run([worker] * N)
    n = _meta(core, key).get("n")
    check(f"[{kind}] §1 {N} threads × {M} merges of one counter → {N * M}", n == N * M, f"n={n}")


def section_fields(kind, core):
    key = _atom(core, "k_fields", {"a": 0, "b": 0, "keep": "x"})
    M = 150

    def wa():
        for i in range(1, M + 1):
            core.merge_meta(key, {"a": i})

    def wb():
        for i in range(1, M + 1):
            core.merge_meta(key, {"b": i})
    _run([wa, wb])
    m = _meta(core, key)
    check(f"[{kind}] §2 two writers of different fields both survive",
          m.get("a") == M and m.get("b") == M and m.get("keep") == "x", str(m))


def section_owned(kind, core):
    from lib.akasha import owned_fields as OF
    OF.declare("evalmerge", "evalmerge_state", concept="evalmerge_thing")
    with OF.writing_as("evalmerge"):
        key = _atom(core, "k_owned", {"concept": "evalmerge_thing", "evalmerge_state": "A", "x": 1})
    stale = _meta(core, key)                         # a writer's copy, read BEFORE the owner's change
    with OF.writing_as("evalmerge"):
        core.merge_meta(key, {"evalmerge_state": "B"})
    stale["x"] = 2
    refused = None
    try:
        core.update_meta(key, stale)                 # would revert evalmerge_state B → A
    except OF.OwnedFieldRefused as exc:
        refused = str(exc)
    m = _meta(core, key)
    check(f"[{kind}] §3 a stale whole-meta copy reverting an owned field is refused at the write",
          refused is not None and m.get("evalmerge_state") == "B" and m.get("x") == 1,
          (refused or "not refused")[:120] + " meta=%s" % m)
    try:
        core.merge_meta(key, {"evalmerge_state": "C"})
        merged_refused = False
    except OF.OwnedFieldRefused:
        merged_refused = True
    check(f"[{kind}] §3 a non-owner merge of the owned field is refused too",
          merged_refused and _meta(core, key).get("evalmerge_state") == "B")


def section_edges(kind, core):
    check(f"[{kind}] §4 merge on a missing atom → None", core.merge_meta("k_absent", {"a": 1}) is None)
    key = _atom(core, "k_same", {"a": 1})
    before = core.get_chunk_raw(key)
    out = core.merge_meta(key, {"a": 1})
    check(f"[{kind}] §4 a merge that changes nothing returns the meta and writes nothing",
          out == {"a": 1} and core.get_chunk_raw(key) == before)


def section_composite(kind, core):
    from lib.akasha import composite as C
    key = _atom(core, "k_comp", {"tag": 0})
    M = 120

    def bumps():
        for _ in range(M):
            C._bump_salience(core, key, 1.0)

    def tags():
        for i in range(1, M + 1):
            core.merge_meta(key, {"tag": i})
    _run([bumps, tags])
    m = _meta(core, key)
    check(f"[{kind}] §5 salience bumps on one thread + a field on another: both land",
          m.get("tag") == M and abs(float(m.get("salience", 0)) - M) < 1e-6, str(m))


def main():
    for kind in ("sqlite", "silica"):
        print(f"\n  ── {kind} ──")
        core = _backend(kind)
        section_counter(kind, core)
        section_fields(kind, core)
        section_owned(kind, core)
        section_edges(kind, core)
        section_composite(kind, core)
    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails))
        sys.exit(1)
    print("RESULT: PASS — merge_meta is one atomic read-merge-write on both backends; concurrent "
          "writers of one atom keep each other's fields, and a stale copy cannot revert an owned field.")
    sys.exit(0)


if __name__ == "__main__":
    main()
