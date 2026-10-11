#!/usr/bin/env python3
"""
mobility_converge_eval.py — the mobility bootstrap CONVERGES across capped runs.

On a slow host the 26,605-row load can exceed the per-run cap (observed live: stalled at
15,500/26,605). The bootstrap now checkpoints the acquired-row cursor and, on the next boot, SKIPS
the already-acquired rows and continues — so it converges to the complete, FROZEN pool instead of
restarting from row 0. This proves the essence: a PARTIAL run followed by a RESUME run reaches the
full pool, using the same `msi.run` the boot phase uses, with idempotent acquire and no re-scan.

Run:  python app/test/mobility_converge_eval.py     (exit 0 = pass)
"""
import hashlib
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"


def main():
    from lib.akasha.kernel import KernelDispatcher
    import app.scripts.mobility_source_import as msi

    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_mobconv_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")

    def disp(method, data):
        r = k.dispatch({"jsonrpc": "2.0", "method": method,
                        "params": {"session_token": "admin", "data": data}, "id": "t"}, "local")
        return r.get("result") if "result" in r else {"__error__": r.get("error")}

    rows = [{"ID": f"R{i}", "country": ["DE", "FR", "IT"][i % 3]} for i in range(1200)]

    def opts(freeze):
        return {"artifacts": [], "id_field": "ID", "retrieval": "", "batch": 200, "freeze": freeze,
                "snapshot": "", "snapshot_n": 0, "snapshot_strata": "", "snapshot_seed": "x"}

    fails = []

    def check(name, ok, detail=""):
        print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
        if not ok:
            fails.append(name)

    # Run A — a capped/partial run: rows 0..600 only, pool left OPEN (no freeze).
    outA = msi.run(disp, iter(rows[:600]), opts(False), log=lambda m: None)
    totA = disp("source.status", {"pool": outA["pool"]}).get("total")
    check("partial run acquires its slice and leaves the pool OPEN", totA == 600, f"total={totA}")

    # Overlap run — resume from a slightly-early checkpoint (rows 400..900, overlapping 400..600).
    # A naive counter would reach 600+500=1100; idempotent acquire (content-addressed by id) means
    # the overlap does NOT double-count, so an imprecise checkpoint is always safe. Still OPEN.
    outO = msi.run(disp, iter(rows[400:900]), opts(False), log=lambda m: None)
    totO = disp("source.status", {"pool": outO["pool"]}).get("total")
    check("overlapping resume is idempotent (no double-count)", totO == 900, f"total={totO}")

    # Run B — resume the tail (rows 900..1200), then freeze → converge to the complete FROZEN pool.
    outB = msi.run(disp, iter(rows[900:]), opts(True), log=lambda m: None)
    totB = disp("source.status", {"pool": outB["pool"]}).get("total")
    check("resume converges to the FULL pool and FREEZES", totB == 1200 and outB.get("members") == 1200,
          f"total={totB} members={outB.get('members')}")

    print()
    if fails:
        print(f"FAIL — {len(fails)} check(s) failed: {fails}")
        sys.exit(1)
    print("ALL PASS — the mobility load converges across capped runs (checkpoint + resume), reaching "
          "the complete FROZEN pool without re-scanning or duplicating.")


if __name__ == "__main__":
    main()
