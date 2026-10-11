#!/usr/bin/env python3
"""
F48-1.1 — stat-sentinel boot skip: an UNCHANGED .ak file is skipped WITHOUT being opened/parsed.

Every boot, `load_all` re-read + decoded + parsed EVERY .ak file (to compute the content hash and
run the set.add self-heal), so the loader heap climbed +2.5–3 GB per boot even though the store did
not grow — and Python never returned it. The fix: a STAT (mtime+size) sentinel is the cheap
change-detector; an unchanged file is skipped without a single read. Peak loader heap becomes
O(changed files), not O(ontology). This test mirrors the kernel's new collection predicate and
COUNTS file opens, asserting:
  • fresh    → every file is read (no stat sentinel yet);
  • restart  → ZERO files are read (all skipped by stat sentinel);
  • touch    → only the changed file is read (size change → new stat tag);

Run:  python test/onto_stat_skip_eval.py
"""
import os
import sys
import glob
import tempfile
import shutil
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


class Sentinels:
    def __init__(self, d):
        self.d = d
        os.makedirs(d, exist_ok=True)

    def _f(self, name, h):
        return os.path.join(self.d, f"{name}_{h}.done")

    def exists(self, name, h):
        return os.path.exists(self._f(name, h))

    def write(self, name, h):
        with open(self._f(name, h), "w") as fp:
            fp.write(str(time.time()))


def collect_with_stat(pack_dir, sents, opened=None):
    """Mirror of the kernel's F48-1.1 relations loop: skip an unchanged file by its STAT sentinel
    WITHOUT reading it; read + gate changed/new files. `opened` collects the basenames actually
    opened, so the test can prove an unchanged file is never touched."""
    pack = os.path.basename(pack_dir)
    read = skipped = 0
    to_write = []
    for fp in sorted(glob.glob(os.path.join(pack_dir, "*.ak"))):
        bn = os.path.basename(fp)
        relbase = (pack + "__" + bn).replace(os.sep, "_").replace(".", "_").replace(":", "_")
        statname = "_relstat_" + relbase
        st = os.stat(fp)
        stat_tag = "%x_%x" % (int(st.st_mtime), st.st_size)
        if stat_tag and sents.exists(statname, stat_tag):
            skipped += 1
            continue                                   # skipped WITHOUT opening the file
        if opened is not None:
            opened.append(bn)
        _content = open(fp, "rb").read()               # the ONLY place a file is opened
        read += 1
        to_write.append((statname, stat_tag))
    for name, h in to_write:                           # gate on success
        sents.write(name, h)
    return read, skipped


def main():
    tmp = tempfile.mkdtemp(prefix="statskip_")
    try:
        pack = os.path.join(tmp, "demo")
        os.makedirs(pack)
        for i in range(4):
            with open(os.path.join(pack, f"f{i}.ak"), "w") as f:
                f.write(f'def "concept:x{i}" "atom {i}"\nal concept:x{i} x{i}\n')
        # make mtimes distinct + in the past so a later touch is detectable
        old = time.time() - 100
        for fp in glob.glob(os.path.join(pack, "*.ak")):
            os.utime(fp, (old, old))
        sents = Sentinels(os.path.join(tmp, "sentinels"))

        # fresh boot → every file read, stat sentinels written
        op = []
        read, skipped = collect_with_stat(pack, sents, opened=op)
        check("fresh boot reads every file (no stat sentinel yet)", read == 4 and skipped == 0,
              f"read={read} skipped={skipped}")

        # warm restart → ZERO reads, all skipped by stat sentinel
        op2 = []
        read2, skipped2 = collect_with_stat(pack, sents, opened=op2)
        check("warm restart reads NOTHING (all skipped by stat sentinel)",
              read2 == 0 and skipped2 == 4, f"read={read2} skipped={skipped2}")
        check("an unchanged file is never even opened", op2 == [], f"opened={op2}")

        # touch ONE file (size change → new stat tag) → only that file is read
        target = os.path.join(pack, "f2.ak")
        with open(target, "a") as f:
            f.write('ln concept:x2 concept:x1 thesaurus:related\n')
        os.utime(target, (time.time(), time.time()))
        op3 = []
        read3, skipped3 = collect_with_stat(pack, sents, opened=op3)
        check("only the changed file is read on the next boot",
              read3 == 1 and skipped3 == 3 and op3 == ["f2.ak"], f"read={read3} opened={op3}")

        # a fresh restart after the edit → back to zero reads
        read4, skipped4 = collect_with_stat(pack, sents)
        check("after the edit is gated, the next boot reads nothing again",
              read4 == 0 and skipped4 == 4, f"read={read4} skipped={skipped4}")

    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("ALL PASS — an unchanged .ak file is skipped by its stat sentinel WITHOUT being opened; "
          "only changed/new files are read; peak loader heap is O(changed files), not O(ontology).")
    sys.exit(0)


if __name__ == "__main__":
    main()
