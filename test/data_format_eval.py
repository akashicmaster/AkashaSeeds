#!/usr/bin/env python3
"""
The cell's data-format id (the purge order, 3 October §4.4).

  §1  a fresh directory's first boot stamps this build's id (`central/DATA_FORMAT`) before the store
      exists; a second boot of it boots.
  §2  a directory stamped with ANOTHER id stops the kernel before anything opens or writes it: one
      `[cell] data format found=… expected=…` line with both instructions, `DataFormatMismatch`
      raised, and the directory byte-for-byte as it was.
  §3  a store written before stamps existed (a `central/nucleus.db` and no stamp) is `found=none`
      and stops the same way.
  §4  the launcher stops too, before its lock, heartbeat or backend marker: exit 3, the line on
      stderr, the directory unchanged.

Run:  python test/data_format_eval.py     (exit 0 = all pass)
"""
import hashlib
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _snapshot(d):
    out = {}
    for root, _dirs, files in os.walk(d):
        out[os.path.relpath(root, d) + "/"] = None
        for f in files:
            p = os.path.join(root, f)
            with open(p, "rb") as fh:
                out[os.path.relpath(p, d)] = hashlib.sha256(fh.read()).hexdigest()
    return out


def main():
    from lib.akasha import data_format as DF
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None

    print("\n  ── §1 a fresh directory ──")
    fresh = tempfile.mkdtemp(prefix="dfmt_fresh_")
    KernelDispatcher(series="seeds", base_dir=fresh)
    stamped = open(DF.stamp_path(fresh), encoding="utf-8").read().strip()
    check("§1 the first boot stamps this build's id", stamped == DF.DATA_FORMAT_ID, stamped)
    try:
        KernelDispatcher(series="seeds", base_dir=fresh)
        again = True
    except DF.DataFormatMismatch:
        again = False
    check("§1 a second boot of the stamped directory boots", again)

    def stops(base, label, found):
        before = _snapshot(base)
        err = None
        try:
            KernelDispatcher(series="seeds", base_dir=base)
        except DF.DataFormatMismatch as exc:
            err = str(exc)
        check("%s the kernel stops (DataFormatMismatch)" % label, err is not None)
        e = err or ""
        check("%s one line: found=%s expected=%s, start fresh, dump and describe again as a pack in "
              "ontology/user/" % (label, found, DF.DATA_FORMAT_ID),
              ("found=%s" % found) in e and ("expected=%s" % DF.DATA_FORMAT_ID) in e
              and "start fresh" in e and "ontology/user/" in e and "\n" not in e, e[:200])
        after = _snapshot(base)
        check("%s nothing written: the directory is as it was" % label, before == after,
              str(sorted(set(after) ^ set(before)))[:200])

    print("\n  ── §2 another id ──")
    foreign = tempfile.mkdtemp(prefix="dfmt_foreign_")
    os.makedirs(os.path.join(foreign, "central"))
    open(DF.stamp_path(foreign), "w").write("akasha-cell-1999-01-01\n")
    open(os.path.join(foreign, "central", "nucleus.db"), "wb").write(b"not ours")
    stops(foreign, "§2", "akasha-cell-1999-01-01")

    print("\n  ── §3 a store from before stamps ──")
    old = tempfile.mkdtemp(prefix="dfmt_old_")
    os.makedirs(os.path.join(old, "central", "nucleus.db.silica"))
    open(os.path.join(old, "central", "nucleus.db.silica", "bank0.wal"), "wb").write(b"\0" * 64)
    stops(old, "§3", "none")

    print("\n  ── §4 the launcher ──")
    before = _snapshot(foreign)
    env = dict(os.environ, AKASHA_DATA_DIR=foreign)
    r = subprocess.run([sys.executable, os.path.join(ROOT, "akasha.py"), "--stdio"], cwd=ROOT,
                       env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=120)
    check("§4 the launcher exits 3 with the line on stderr",
          r.returncode == 3 and "data format found=akasha-cell-1999-01-01" in r.stderr,
          "rc=%s err=%s" % (r.returncode, r.stderr.strip()[-200:]))
    check("§4 …and writes nothing in the directory (no lock, heartbeat or marker)",
          _snapshot(foreign) == before)

    print()
    if _fails:
        print("FAILED (%d): %s" % (len(_fails), "; ".join(_fails)))
        sys.exit(1)
    print("RESULT: PASS — a fresh cell is stamped with this build's data-format id; a directory with "
          "another id, or a store from before stamps, stops the kernel and the launcher before "
          "anything opens or writes it, in one line that says what to do.")
    sys.exit(0)


if __name__ == "__main__":
    main()
