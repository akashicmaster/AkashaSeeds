#!/usr/bin/env python3
"""
F47-S1 — lazy / shared cell: a read-only visitor holds NO private cell (the OOM structural fix).

The 2026-08-28 kill was the guest-cell ECONOMY: every anonymous page view got a private banks=1
silica engine (~25 MB) and RSS climbed ~25 MB/guest at bot churn until the 8 GB ceiling. The fix:
a read-only visitor (guest) SHARES one process-wide read cortex bound to the shared nucleus and holds
its context in memory — zero per-visitor engine. The private cell materializes only on a first write
(a guest can never write). This eval asserts the invariants:

  I1  a visitor creates NO private cell dir and NO per-visitor engine; RSS is independent of the
      number of visitors (100 guests do not each cost ~25 MB).
  --  a visitor's reads resolve nucleus atoms EXACTLY as an owning session would (behaviour parity).
  I2  materialize_cell() (a first write) upgrades the session to an owning private cell.
  --  recycling a shared-cortex visitor never closes the shared cortex (other visitors keep working).

Run:  python test/lazy_cell_eval.py   (exit 0 = all pass)
"""
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
            for ln in f:
                if ln.startswith("VmRSS:"):
                    return int(ln.split()[1]) // 1024
    except OSError:
        pass
    return None


def main():
    from lib.akasha.kernel import KernelDispatcher
    from api.gateway import AkashaGateway
    from lib.akasha.identity import Role
    from lib.akasha.jcl.workspace_context import system_context
    KernelDispatcher._boot_load_ontology = lambda self: None
    base = tempfile.mkdtemp(prefix="lazycell_")
    k = KernelDispatcher(series="seeds", base_dir=base)
    gw = AkashaGateway(kernel_client=k)
    gw.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                 "params": {"session_token": "admin", "data": {"user_name": "admin",
                            "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")
    mgr = k.manager

    # Seed a PUBLIC atom directly into the shared nucleus so a guest can read it.
    import time as _tm
    nkey = "atom:sparrow_test"
    with system_context():
        mgr.shared_nucleus.core.put_chunk_raw(nkey, "a small bird.", "{}", "system", "verified", _tm.time())
        mgr.shared_nucleus.core.put_alias(nkey, "concept:sparrow")

    # ── I1: many visitors, NO per-visitor cell dir, RSS ~flat ──
    rss0 = _rss_mb()
    sessions = [mgr.get_session("guest:pool:%d" % i, requested_role="leaf") for i in range(100)]
    rss1 = _rss_mb()
    ro = all(s.read_only and not s.owns_cortex for s in sessions)
    shared = all(s.local_cortex is mgr._guest_read_cortex for s in sessions)
    check("I1 every visitor is read-only and shares ONE read cortex", ro and shared)
    cell_dirs = [c for c in os.listdir(os.path.join(base, "cells")) if c.startswith("guest:pool:")]
    check("I1 NO per-visitor private cell dir is created", cell_dirs == [], "dirs=%s" % cell_dirs[:3])
    if rss0 is not None and rss1 is not None:
        check("I1 RSS is independent of visitor count (100 guests add < 40 MB, not ~2.5 GB)",
              rss1 - rss0 < 40, "delta=%dMB (%d→%d)" % (rss1 - rss0, rss0, rss1))

    # ── behaviour parity: a visitor resolves the nucleus atom exactly as an owning session does ──
    g = mgr.get_session("guest:pool:0", requested_role="leaf")
    admin = mgr.get_session("admin", requested_role="admin")
    gk = g.local_cortex.resolve_alias("concept:sparrow")
    ak = admin.local_cortex.resolve_alias("concept:sparrow")
    check("visitor resolves a nucleus atom identically to an owning session",
          bool(gk) and gk == ak, "guest=%s admin=%s" % (gk, ak))
    check("owning (admin) session is NOT read-only and owns its cortex",
          admin.owns_cortex and not admin.read_only)

    # ── in-memory context for a visitor (no persisted anchor) ──
    g.set_context("locale_primary", "ja")
    check("a visitor's context is held in memory (no cell write)",
          g.get_context("locale_primary") == "ja" and g._ctx_mem.get("locale_primary") == "ja")

    # ── I2: materialize_cell() upgrades a visitor to an owning private cell ──
    g.materialize_cell()
    check("I2 materialize_cell() → owns a private cell, no longer read-only",
          g.owns_cortex and not g.read_only and g.local_cortex is not mgr._guest_read_cortex)
    check("I2 the materialized cell has its own dir on disk",
          os.path.isdir(os.path.join(base, "cells", "guest:pool:0")))
    check("I2 the in-memory context carried forward into the durable cell",
          g.get_context("locale_primary") == "ja")

    # ── recycling a shared-cortex visitor must NOT close the shared cortex ──
    shared_cortex = mgr._guest_read_cortex
    mgr._reset_guest_slot("guest:pool:1")
    import time as _t
    _t.sleep(0.3)
    still_ok = bool(mgr._guest_read_cortex.resolve_alias("concept:sparrow") or True)
    # a still-live visitor keeps reading through the shared cortex
    g2 = mgr.get_session("guest:pool:2", requested_role="leaf")
    check("recycling one visitor leaves the shared cortex usable for others",
          g2.local_cortex is shared_cortex and g2.local_cortex.resolve_alias("concept:sparrow") == ak)

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("ALL PASS — read-only visitors share one cortex (no private cell, RSS flat with visitor "
          "count); reads resolve nucleus atoms identically; a first write materializes a private "
          "cell; recycling one visitor never breaks the shared cortex.")
    sys.exit(0)


if __name__ == "__main__":
    main()
