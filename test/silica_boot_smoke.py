#!/usr/bin/env python3
"""
Silica boot smoke — the native engine boots the FULL kernel stack (the seeds12
twin-release gate).  Sets AKASHA_BACKEND=silica so the core factory
(lib/akasha/core.py) constructs SilicaBackend everywhere, then drives the real
kernel → composite → manager path: genesis, write, link, set, read.

Ontology autoload is skipped (this is a stack-wiring smoke, not the full soak —
that is the adversarial benchmark's job).  Run:  python test/silica_boot_smoke.py
"""
import os
import sys
import json
import hashlib
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
os.environ["AKASHA_BACKEND"] = "silica"        # ← select the native engine at the factory


def main():
    print("\n  silica boot smoke — native engine drives the full kernel stack\n")
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="silica_boot_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin",
                                    "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                "id": "g"}, "local")

    def d(m, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": m,
                        "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
        return r.get("result") or r.get("error")

    sess = k.manager.get_session("admin")
    backend = type(sess.local_cortex.core).__name__

    a = (d("w", {"content": "silica boots"}) or {}).get("key")
    b = (d("w", {"content": "second atom"}) or {}).get("key")
    d("ln", {"src": a, "dst": b, "rel": "rel:test"})
    d("set.add", {"name": "set:smoke", "id": a})
    rd = d("read", {"id": a})

    checks = {
        "backend is SilicaBackend": backend == "SilicaBackend",
        "genesis + write (key minted)": bool(a) and bool(b),
        "read returns content": bool(rd) and "silica boots" in json.dumps(rd, default=str),
        "link written": any(rel == "rel:test"
                            for _dst, rel in sess.local_cortex.get_adjacent_links(a)),
        "set membership": a in sess.local_cortex.get_collection_members("set:smoke"),
    }
    for name, ok in checks.items():
        print(f"  {'OK  ' if ok else '!! FAIL'}  {name}")

    passed = sum(1 for ok in checks.values() if ok)
    print(f"\n  {passed}/{len(checks)} checks passed  (backend={backend})")
    if passed < len(checks):
        print("\nRESULT: FAIL — the native engine did not boot the kernel stack cleanly.")
        return 1
    print("\nRESULT: PASS — AKASHA_BACKEND=silica boots the full kernel/composite/manager stack; "
          "genesis, write, link, set and read all work on the self-owned engine.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
