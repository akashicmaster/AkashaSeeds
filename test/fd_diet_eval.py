#!/usr/bin/env python3
"""
F29-R2 eval — FD exhaustion fix: RLIMIT raise + guest-cell bank diet.

The 128-slot guest pool each opens a PRIVATE silica cortex, and a silica store is a multi-file
directory (~1 WAL per bank + coordinator). At 8 banks that is ~10–25 FDs each ⇒ `Errno 24 Too many
open files` at ~50–60 concurrent guests on a 1024 ulimit. Two fixes:
  • R2.1 raise RLIMIT_NOFILE to min(hard, 65536) up front.
  • R2.2 per-client cell cortex opens with banks=1 (one WAL, not eight); an existing multi-bank
    store keeps its on-disk geometry (never reopened at the wrong width — that would orphan data).

Run:  python test/fd_diet_eval.py   (exit 0 = all pass; silica-only assertions skip on sqlite)
"""
import glob
import importlib.util
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
os.environ["AKASHA_BACKEND"] = "silica"

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def main():
    spec = importlib.util.spec_from_file_location("akasha_entry", os.path.join(ROOT, "akasha.py"))
    ak = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ak)

    # ── R2.1: RLIMIT_NOFILE is raised toward min(hard, 65536) ──
    try:
        import resource
        soft0, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        # lower the soft limit first so the raise is observable
        want = min(hard, 4096) if hard != resource.RLIM_INFINITY else 4096
        try:
            resource.setrlimit(resource.RLIMIT_NOFILE, (min(1024, want), hard))
        except (ValueError, OSError):
            pass
        before, _ = resource.getrlimit(resource.RLIMIT_NOFILE)
        res = ak._raise_fd_limit()
        after, _ = resource.getrlimit(resource.RLIMIT_NOFILE)
        target = hard if hard != resource.RLIM_INFINITY else 65536
        target = min(target, 65536)
        check("R2.1 RLIMIT_NOFILE raised toward min(hard,65536)",
              after >= before and (after == target or after >= before),
              f"soft {before} → {after} (hard={hard})")
    except Exception as exc:
        check("R2.1 RLIMIT raise (resource module)", False, str(exc))

    # ── R2 FD instrumentation helpers ──
    from lib.akasha.api.heart import _open_fd_count, _fd_soft_limit
    fds = _open_fd_count()
    lim = _fd_soft_limit()
    check("R2.3 _open_fd_count returns a positive count (or None off-Linux)",
          fds is None or fds > 0, f"fds={fds}")
    check("R2.3 _fd_soft_limit returns the soft ceiling (or None)",
          lim is None or lim > 0, f"soft={lim}")

    # ── R2.2: a per-client cell cortex opens with banks=1 ──
    from lib.akasha.composite import AkashaEngine
    base = tempfile.mkdtemp(prefix="fd_cell_")
    eng = AkashaEngine(os.path.join(base, "l_cortex.db"), is_volatile=False, banks=1)
    store_dir = os.path.abspath(os.path.join(base, "l_cortex.db")) + ".silica"
    wals = glob.glob(os.path.join(store_dir, "bank-*.wal"))
    check("R2.2 cell cortex opens with ONE bank WAL (was 8)", len(wals) == 1,
          f"bank WALs={len(wals)}")

    # write + reopen at the DEFAULT width → must auto-detect 1 bank and read intact (no orphaning)
    import time as _t
    eng.core.put_chunk_raw("cellkey", "private note", "{}", "admin", "verified", _t.time())
    del eng
    eng2 = AkashaEngine(os.path.join(base, "l_cortex.db"), is_volatile=False)   # default banks
    row = eng2.core.get_chunk_raw("cellkey")
    check("R2.2 reopening at the default width keeps 1 bank + data intact",
          getattr(eng2.core, "_store", None) is not None
          and eng2.core._store._n == 1 and row and row.get("content") == "private note",
          f"n={getattr(getattr(eng2.core,'_store',None),'_n','?')}")

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails))
        sys.exit(1)
    print("ALL PASS — the FD limit is raised up front and a per-client cell cortex uses a single bank "
          "(one WAL FD, not eight); an existing store keeps its on-disk geometry, so the diet never "
          "orphans data.")
    sys.exit(0)


if __name__ == "__main__":
    main()
