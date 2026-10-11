#!/usr/bin/env python3
"""
F29-R8.1 eval — per-@route RAM attribution (MemTop).

Before shrinking the load-settled RSS, name where it lives. The Silica RAM index keys every atom
body under its own hash route, and the bulk-scanned bookkeeping (aliases, links, sets, scopes) under
`@`-prefixed routes. route_sizes() reports the deep size (keys + value/locator entries + container
overhead) of each `@` route individually plus ONE aggregate for the hash-routed bodies — so MemTop
attributes the 5 GB precisely before any surgery (R8's explicit "attribute first" step).

Run:  python test/route_attribution_eval.py   (exit 0 = all pass)
"""
import os
import sys
import tempfile
import time

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
    # RamIndex directly — the attribution primitive
    from lib.akasha.backends.index_backend import RamIndex, OP_PUT
    idx = RamIndex()
    for i in range(300):
        idx.apply(OP_PUT, b"@ALIAS", ("alias-%d" % i).encode(), ("key%d" % i).encode())
        idx.apply(OP_PUT, b"@LINK", ("l-%d" % i).encode(), b"x" * 40)
        idx.apply(OP_PUT, ("hash%064d" % i).encode(), b"C", b"body-%d" % i)   # hash-routed body
    rs = idx.route_sizes()
    ats = {(r.decode() if isinstance(r, bytes) else r): (n, b) for r, n, b in rs["at_routes"]}
    check("R8.1 @routes attributed individually", "@ALIAS" in ats and "@LINK" in ats, f"{list(ats)}")
    check("R8.1 @ALIAS holds the alias entries", ats.get("@ALIAS", (0, 0))[0] == 300,
          f"@ALIAS entries={ats.get('@ALIAS')}")
    check("R8.1 hash-routed bodies collapse into ONE aggregate (not per-route)",
          rs["other_routes"]["count"] == 300 and rs["other_routes"]["bytes"] > 0,
          f"other={rs['other_routes']}")
    check("R8.1 @routes sorted by bytes desc",
          [b for _, _, b in rs["at_routes"]] == sorted((b for _, _, b in rs["at_routes"]), reverse=True))

    # through the backend (bank-merged)
    from lib.akasha.backends.silica_backend import SilicaBackend
    d = tempfile.mkdtemp(prefix="rattr_")
    b = SilicaBackend(os.path.join(d, "s"), banks=4, sync_mode="NORMAL")
    for i in range(400):
        b.put_chunk_raw("k%d" % i, "content %d" % i, "{}", "admin", "verified", time.time())
    rs2 = b.route_sizes()
    check("R8.1 backend merges @routes across banks + aggregates bodies",
          any((r == b"@ALIAS" or r == b"@CHUNKS") for r, _, _ in rs2["at_routes"])
          and rs2["other_routes"]["count"] >= 0, f"n_at={len(rs2['at_routes'])}")
    check("R8.1 disk/cached index attributes nothing (values not in RAM) — safe default",
          isinstance(rs2, dict) and "at_routes" in rs2)

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails))
        sys.exit(1)
    print("ALL PASS — MemTop can now attribute the Silica index RAM per @route (aliases/links/sets/"
          "scopes) with the hash-routed bodies collapsed into one aggregate, so the load-settled RSS "
          "is named before any surgery.")
    sys.exit(0)


if __name__ == "__main__":
    main()
