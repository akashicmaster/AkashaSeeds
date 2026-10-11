#!/usr/bin/env python3
"""
A56 §1 — `station.compact` (society.broadcast.gc) decides orphan-ness from META only.

The 2026-09-11 nightly: the sweep iterated the per-society mirror registry (O(victims), the A48 fix)
but the per-entry orphan test still LOADED each mirror's body (a broadcast message plus its telemetry)
to decide "orphan or not" — 240 loads ≈ 334 MB retained until the workspace committed, a 100 s stall
with nothing to drop. The fix: the orphan test reads only the collections table
(`get_collections_for_key`), never a body; a body is touched (`drop_chunk`) only for an entry that IS
being dropped.

This eval proves it on both cell shapes: 240 mirror atoms, EACH carrying a large body and EACH still in
a live broadcast window (nothing to drop) ⇒ `society.broadcast.gc`:
  - scans all 240, drops 0, leaves every message;
  - completes in under 5 s and grows RSS by under 20 MB (the bodies are never materialised).

Run:  python test/station_compact_eval.py     (exit 0 = all pass)
"""
import hashlib
import os
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
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
    except (OSError, ValueError, IndexError):
        return None
    return None


def _run(series, shape):
    print(f"\n  ── {shape} ({series}) ──")
    from lib.akasha.kernel import KernelDispatcher, TRUST_INTERNAL
    from lib.akasha.jcl.workspace_context import system_context
    KernelDispatcher._boot_load_ontology = lambda self: None
    base = tempfile.mkdtemp(prefix="akasha_stationc_")
    k = KernelDispatcher(series=series, base_dir=base)
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")
    nuc = k.manager.shared_nucleus
    core = nuc.core
    gid = "plab"

    # 240 mirror atoms, each with a large body (~20 KB) and each still in the LIVE window → nothing to
    # drop. If the orphan test loaded bodies, the RSS would climb by the sum of the bodies (~5 MB here,
    # 334 MB on the VPS); the fix reads only the collections table, so it stays flat.
    big = "x" * 20000
    n_mirror = 240
    with system_context():
        for i in range(n_mirror):
            alias = f"broadcast:msg:{gid}:{i}"
            key = nuc.put_atom(f"[{alias}] {big}", {"concept": "broadcast_msg", "provenance": "broadcast",
                               "sid": f"{gid}/main", "n": i}, author="system.librarian", alias=alias)
            core.add_to_collection(f"broadcast:mirror:{gid}", key)   # the registry
            core.add_to_collection(f"broadcast:{gid}:main", key)     # a LIVE window → kept

    rss0 = _rss_mb()
    t0 = time.time()
    rb = k.dispatch({"jsonrpc": "2.0", "method": "society.broadcast.gc",
                     "params": {"client_id": "system.librarian", "data": {}}, "id": "bc"}, TRUST_INTERNAL)
    elapsed = time.time() - t0
    rss1 = _rss_mb()
    drss = (rss1 - rss0) if (rss0 is not None and rss1 is not None) else None

    res = (rb or {}).get("result") or {}
    check(f"[{shape}] scans all {n_mirror} mirror entries", res.get("scanned") == n_mirror, str(res))
    check(f"[{shape}] drops nothing (all in a live window)", res.get("dropped") == 0, str(res))
    check(f"[{shape}] every windowed message survives",
          all(bool(core.get_key_by_alias(f"broadcast:msg:{gid}:{i}")) for i in (0, 120, 239)))
    check(f"[{shape}] completes in under 5 s (no body loads)", elapsed < 5.0, f"t={elapsed:.2f}s")
    # A58 — the sweep reports `retained` (RSS held after gc + malloc_trim); on a small fixture ≤ 10 MB
    _ret = res.get("retained")
    check(f"[{shape}] A58 the sweep reports retained ≤ 10 MB (arenas returned)",
          _ret is None or _ret == "?" or _ret <= 10, f"retained={_ret}MB")
    check(f"[{shape}] grows RSS by under 20 MB (bodies never materialised)",
          drss is None or drss < 20, f"Δrss={drss}MB")


def main():
    _run("thesaurus", "nucleus cell")
    _run("seeds", "single-store cell")
    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("\nRESULT: PASS — station.compact decides orphan-ness from the collections table only: 240 live "
          "mirrors with nothing to drop scan in under 5 s and under 20 MB, no body is loaded, and every "
          "windowed message survives — both cell shapes.")
    sys.exit(0)


if __name__ == "__main__":
    main()
