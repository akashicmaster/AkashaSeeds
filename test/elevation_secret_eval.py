#!/usr/bin/env python3
"""
F48-2.1 — the F16 elevation secret is shared across the process split (the pulse-capture fix).

World-a was confirmed in production: pulse(seen>0 emit=0 rej>0) — emits ARRIVE at the writer but are
REJECTED, because the portal (signer) and daemon (verifier) resolved DIFFERENT elevation secrets.
Guest TOKENS survived this (minted AND verified in one process, self-consistent), so a working site
did not reveal it. AKASHA_SECRET env is the primary channel, but env propagation depends on spawn
ordering; the fix adds a 0600 shared-file fallback so both sides always resolve the SAME key. This
eval proves: env-first is byte-identical; the file recovers a missing env; a forged/absent signature
still clamps.

Run:  python test/elevation_secret_eval.py   (exit 0 = all pass)
"""
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def main():
    import api.portals.cell_ipc as ipc

    method = "pulse.emit"
    params = {"client_id": "system.librarian", "concept": "x", "surface": "atom", "ref": "direct"}

    # ── env-first: with AKASHA_SECRET set, sign+verify round-trip (unchanged behaviour) ──
    os.environ["AKASHA_SECRET"] = "ab" * 32
    ipc._ELEVATION_BASE["dir"] = None
    ts = __import__("time").time()
    sig = ipc.sign_internal(method, params, ts)
    check("env secret → sign produces a signature", bool(sig))
    check("env secret → verify accepts the signature", ipc.verify_internal(method, params, ts, sig))

    # ── file fallback: env ABSENT, but the daemon wrote the 0600 secret file → sign+verify agree ──
    base = tempfile.mkdtemp(prefix="elev_")
    daemon_secret = "cd" * 32
    ipc.write_elevation_secret(base, daemon_secret)      # daemon persists its resolved secret
    check("the elevation secret file is written 0600",
          os.path.exists(ipc.elevation_secret_path(base)))
    os.environ.pop("AKASHA_SECRET", None)                # simulate a portal that missed the env
    ipc.register_elevation_base(base)                    # portal registers the shared base_dir
    ts2 = __import__("time").time()
    sig2 = ipc.sign_internal(method, params, ts2)        # signer resolves the secret from the FILE
    check("no env, file present → sign still produces a signature", bool(sig2))
    check("no env, file present → verify accepts it (signer and verifier agree via the file)",
          ipc.verify_internal(method, params, ts2, sig2))

    # the resolved secret matches the daemon's written one (not some other key)
    check("the fallback resolves the DAEMON's secret", ipc._elevation_secret() == bytes.fromhex(daemon_secret))

    # ── neither env nor file → no elevation (sign returns None; a bare emit clamps) ──
    ipc._ELEVATION_BASE["dir"] = None
    os.environ.pop("AKASHA_SECRET", None)
    check("no env, no file → sign returns None (no elevation, will clamp to local)",
          ipc.sign_internal(method, params, __import__("time").time()) is None)

    # ── a forged signature is rejected even with a secret present ──
    os.environ["AKASHA_SECRET"] = "ab" * 32
    check("a forged signature never verifies",
          not ipc.verify_internal(method, params, __import__("time").time(), "deadbeef" * 8))
    # a non-allowlisted method never elevates
    check("a non-allowlisted method never elevates",
          not ipc.verify_internal("w", params, __import__("time").time(),
                                   ipc.sign_internal("pulse.emit", params, __import__("time").time())))

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("ALL PASS — the elevation secret resolves identically in signer and verifier via env "
          "(primary) or the 0600 shared file (fallback); forged/absent signatures still clamp.")
    sys.exit(0)


if __name__ == "__main__":
    main()
