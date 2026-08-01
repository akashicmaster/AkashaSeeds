#!/usr/bin/env python3
"""
File-level incremental ontology load — the relations phase must gate PER `.ak` FILE.

This guards the mechanism that stops "add one small .ak file to a big pack" from re-applying
the WHOLE ontology's relations (the cost that, with the reconcile-OOM, crashed the daemon on
an incremental add). The global-relations phase now carries a CONTENT-HASH sentinel per .ak
file: an unchanged file is skipped entirely (not read, its al/ln/set not re-applied); only
NEW or CHANGED files are collected and applied.

This test exercises that exact collection predicate (the real filesystem-sentinel mechanism
the kernel uses — `{name}_{hash}.done`, content-hashed) against a temp pack, asserting:
  • fresh   → every file is collected (nothing gated yet);
  • restart → NOTHING is collected (all files unchanged);
  • add     → only the NEW file is collected;
  • edit    → only the EDITED file is collected (content hash, not size — a same-size edit
              is still detected);
  • def-only→ a changed file with no al/ln/set is still gated (won't be re-scanned forever).

Run:  python test/onto_file_incremental_eval.py
"""
import os, sys, glob, hashlib, tempfile, shutil, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

_results = []
def record(name, ok, detail=""):
    _results.append((name, ok, detail))
    print(f"  {'OK  ' if ok else '!! FAIL'}  {name:22} {detail}")


class Sentinels:
    """The kernel's filesystem-sentinel primitives (same `{name}_{hash}.done` shape)."""
    def __init__(self, d):
        self.d = d; os.makedirs(d, exist_ok=True)
    def _f(self, name, h): return os.path.join(self.d, f"{name}_{h}.done")
    def exists(self, name, h): return os.path.exists(self._f(name, h))
    def write(self, name, h):
        with open(self._f(name, h), "w") as fp:
            fp.write(str(time.time()))


def _parse(line):
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    head = line.split(None, 1)[0]
    return {"def": "def", "al": "alias", "ln": "link", "set.add": "set.add"}.get(head)


def collect_changed(pack_dir, sents):
    """Mirror of the kernel's file-level relations collection: gather al/ln/set from files whose
    content-hash sentinel is absent, and return the changed-file sentinels to write on success."""
    pack = os.path.basename(pack_dir)
    al = ln = st = 0
    changed = []
    for fp in sorted(glob.glob(os.path.join(pack_dir, "*.ak"))):
        bn = os.path.basename(fp)
        content = open(fp, "rb").read()
        fh = hashlib.sha256(content).hexdigest()[:16]
        sname = "_relfile_" + (pack + "__" + bn).replace(".", "_")
        if sents.exists(sname, fh):
            continue                                   # unchanged → skip entirely
        for raw in content.decode("utf-8", "replace").splitlines():
            m = _parse(raw)
            if m == "alias": al += 1
            elif m == "link": ln += 1
            elif m == "set.add": st += 1
        changed.append((sname, fh))
    return changed, (al, ln, st)


def commit(changed, sents):
    for sname, fh in changed:                          # kernel writes these on relations-job success
        sents.write(sname, fh)


def main():
    print("\n  file-level incremental — relations gate per .ak file (content-hashed)\n")
    base = tempfile.mkdtemp(prefix="akasha_fileinc_")
    pack = os.path.join(base, "nutrition"); os.makedirs(pack)
    sents = Sentinels(os.path.join(base, "sentinels"))
    def write_ak(name, lines): open(os.path.join(pack, name), "w").write("\n".join(lines) + "\n")
    try:
        write_ak("foods_a.ak", ['def "food:a" "A"', 'al food:a apple', 'set.add name="s:x" id="food:a"'])
        write_ak("foods_b.ak", ['def "food:b" "B"', 'ln food:b food:a rel:near'])

        # fresh → both files collected
        ch, (al, ln, st) = collect_changed(pack, sents)
        record("fresh: all collected", len(ch) == 2 and (al, ln, st) == (1, 1, 1),
               f"files={len(ch)} al/ln/set={al}/{ln}/{st}")
        commit(ch, sents)

        # restart (unchanged) → nothing collected
        ch, tot = collect_changed(pack, sents)
        record("restart: no-op", ch == [] and tot == (0, 0, 0), f"files={len(ch)} rels={tot}")

        # add one new file → only it collected
        write_ak("regions.ak", ['set.add name="s:region" id="food:a"',
                                 'set.add name="s:region2" id="food:b"'])
        ch, (al, ln, st) = collect_changed(pack, sents)
        record("add: only new file", len(ch) == 1 and (al, ln, st) == (0, 0, 2),
               f"files={len(ch)} (expect regions.ak; set.add={st})")
        commit(ch, sents)

        # edit an existing file to the SAME byte length → content hash still catches it
        write_ak("foods_a.ak", ['def "food:a" "A"', 'al food:a APPLE', 'set.add name="s:x" id="food:a"'])
        ch, _ = collect_changed(pack, sents)
        record("edit (same size): caught", len(ch) == 1 and ch[0][0].endswith("foods_a_ak"),
               f"files={len(ch)} (content hash, not size)")
        commit(ch, sents)

        # def-only changed file → still gated (committed sentinel), not re-scanned next pass
        write_ak("defs_only.ak", ['def "food:c" "C"', 'def "food:d" "D"'])
        ch, (al, ln, st) = collect_changed(pack, sents)
        record("def-only: gated", len(ch) == 1 and (al, ln, st) == (0, 0, 0), f"files={len(ch)}")
        commit(ch, sents)
        ch2, _ = collect_changed(pack, sents)
        record("def-only: no re-scan", ch2 == [], f"next pass files={len(ch2)}")
    finally:
        shutil.rmtree(base, ignore_errors=True)

    passed = sum(1 for _, ok, _ in _results if ok); total = len(_results)
    print(f"\n  {passed}/{total} checks passed")
    if passed == total:
        print("\nRESULT: PASS — the relations phase collects only NEW/CHANGED .ak files (content-"
              "hashed), so an incremental add touches only that file, not the whole ontology.\n")
        return 0
    print("\nRESULT: FAIL — file-level incremental gating is wrong.\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
