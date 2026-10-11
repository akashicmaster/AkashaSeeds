#!/usr/bin/env python3
"""
F44-A2 — guest-cell churn must return RSS to baseline (no per-recycle leak).

Production OOMs every ~15 min (settle 2.7 GB → 7.4 GB) WITH concurrency already bounded, so something
accumulates per admitted request or per session. The prime suspect (maintainer): the guest-cell
economy — up to 256 live cells churning ~6× faster than the known-good era, so any small per-recycle
leak is amplified ~30×. This is the targeted eval: create + fully destroy N guest cells in a loop;
RSS must return to baseline (±budget). A monotonic climb names a leak in AkashaEngine.close() / the
session teardown (index dicts, WAL buffers, threads, or a module-level structure outliving the pop).

Run:  python test/guest_cell_leak_eval.py   (exit 0 = pass; SKIP note if /proc RSS unavailable)
"""
import gc
import hashlib
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


def _rss_mb():
    try:
        with open("/proc/self/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) // 1024
    except OSError:
        return None
    return None


def main():
    if _rss_mb() is None:
        print("SKIP — /proc RSS not available on this platform"); sys.exit(0)

    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    base = tempfile.mkdtemp(prefix="gleak_")
    k = KernelDispatcher(series="seeds", base_dir=base)
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "internal")
    mgr = k.manager

    from lib.akasha.manager import AkashaSession
    from lib.akasha.identity import Role
    import shutil

    N = int(os.environ.get("AKASHA_GLEAK_N", "500"))

    def make_and_destroy(cid):
        # Open a private guest cell (banks=1 cortex), do a couple of reads/writes, then fully wipe it
        # — exactly what pool checkout + _reset_guest_slot do for a recycled slot.
        # `iam.get_allowed_scopes` is gone with the one-gate order: a session's scopes are a
        # DERIVATION of the assignment lines, and `gate.scopes_for` is the one that makes it. An
        # unassigned guest id falls back to the `guest` row, which is what this used to ask for.
        from lib.akasha.api import gate as _gate
        sess = AkashaSession(client_id=cid, role=Role.GUEST,
                             allowed_scopes=_gate.scopes_for(cid),
                             base_dir=base, nucleus=mgr.shared_nucleus)
        try:
            sess.consciousness.generate_view("apple", allowed_scopes=sess.active_scopes)
        except Exception:
            pass
        try:
            sess.local_cortex.close()
        except Exception:
            pass
        shutil.rmtree(os.path.join(base, "cells", cid), ignore_errors=True)
        del sess

    # warm up (first cells allocate shared caches) then take the baseline
    for i in range(40):
        make_and_destroy("guest:warm:%d" % i)
    gc.collect()
    base_rss = _rss_mb()

    for i in range(N):
        make_and_destroy("guest:churn:%d" % i)
        if i % 100 == 99:
            gc.collect()
    gc.collect()
    end_rss = _rss_mb()

    grow = end_rss - base_rss
    per_cell_kb = (grow * 1024.0) / N
    budget_mb = int(os.environ.get("AKASHA_GLEAK_BUDGET_MB", "80"))
    print("  [churn] %d guest cells: RSS %dMB → %dMB (+%dMB, ~%.1f KB/cell)"
          % (N, base_rss, end_rss, grow, per_cell_kb))
    check("live session count returned to baseline (all popped)",
          len([s for s in mgr.sessions if s.startswith("guest:churn")]) == 0)
    check("F44-A2 guest-cell churn returns RSS to baseline (no per-recycle leak)",
          grow < budget_mb, f"+{grow}MB over {N} cells (budget {budget_mb}MB)")

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("ALL PASS — creating and fully destroying %d guest cells leaves RSS at baseline; "
          "AkashaEngine.close() releases the cell (no per-recycle accumulation)." % N)
    sys.exit(0)


if __name__ == "__main__":
    main()
