#!/usr/bin/env python3
"""
Pulse SPLIT-topology eval (F16) — the blind spot that let a production-dead feature keep passing.

Every prior pulse test dispatched IN-PROCESS, where the recorder's `internal` trust survives. In
the real thesaurus deployment the portal is a serve-only SUBPROCESS: it forwards pulse.emit over
the daemon's local socket, whose trust ceiling is LOCAL, so `internal` was clamped and the kernel
rejected the system identity (-32001) — silently. This eval reproduces the split path with a real
CellIPCServer + SplitGateway + the actual PulseRecorder, and asserts the hit is counted. It also
proves a FORGED `_trust:"internal"` (no signature) still clamps to local.

  S1 embedded    — recorder over the in-process gateway records the hit (baseline).
  S2 split       — recorder over SplitGateway→socket records the hit (the F16 fix; was 0 before).
  S3 forge-clamp — a raw socket pulse.emit asking for `internal` WITHOUT a valid signature is
                   clamped to local → kernel rejects the system identity (never elevates).
  S4 zero-drop   — a rejected emit is visible in recorder.stats()['rejected'] (never silent).

Run:  python test/pulse_split_eval.py       (exit 0 = all pass)
"""
import os
import sys
import time
import json
import hashlib
import secrets
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
os.environ["AKASHA_NO_AUTOLEARN"] = "1"
# One shared signing secret across "daemon" and "portal" — exactly what akasha.py exports into
# the portal subprocess env. Set BEFORE anything resolves it.
os.environ.setdefault("AKASHA_SECRET", secrets.token_hex(32))

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def main():
    from lib.akasha.kernel import KernelDispatcher
    from api.gateway import AkashaGateway
    from api.portals.cell_ipc import (CellIPCServer, SocketGateway, SplitGateway,
                                      TRUST_LOCAL)
    from lib.harmonia.pulse_recorder import PulseRecorder

    base = tempfile.mkdtemp(prefix="pulse_split_")
    k = KernelDispatcher(series="seeds", base_dir=base)
    daemon_gw = AkashaGateway(kernel_client=k)               # the ONE primary writer (the daemon)

    def d(method, data, tok="admin", trust="local"):
        return daemon_gw.dispatch({"jsonrpc": "2.0", "method": method,
                                   "params": {"session_token": tok, "data": data}, "id": "t"}, trust)

    d("kernel.genesis_rite", {"user_name": "admin",
                              "passphrase": hashlib.sha256(b"pw").hexdigest()})
    time.sleep(3)                                            # let the base ontology autoload settle
    target = ([c.get("name") for c in
               ((d("thesaurus.reference", {"limit": 3}).get("result") or {}).get("concepts") or [])]
              or ["acad"])[0]

    def overview_hits():
        r = d("pulse.overview", {"window": "1d"}).get("result") or {}
        return int(r.get("hits", 0))

    # ── S1 embedded — recorder over the in-process gateway ───────────────────────────
    base_hits = overview_hits()
    rec_embed = PulseRecorder()
    rec_embed.configure(daemon_gw.dispatch)                 # internal survives in-process
    rec_embed.capture(concept=target, surface="atom", referer="https://google.com/",
                      ip="1.1.1.1", ua="Mozilla/5.0")
    time.sleep(3.0)
    emb_hits = overview_hits()
    check("S1 embedded records", emb_hits == base_hits + 1,
          f"hits {base_hits}→{emb_hits}, stats={rec_embed.stats()}")

    # ── S2 split — recorder over SplitGateway → daemon socket ────────────────────────
    server = CellIPCServer(daemon_gw, base, trust=TRUST_LOCAL)
    server.start()
    try:
        # The portal's own read engine would be a separate KernelDispatcher; for the eval the
        # local side only needs to answer reads/guest — writes (pulse.emit) FORWARD over the
        # socket regardless, which is the path under test. Reuse daemon_gw as the local read gw.
        split = SplitGateway(daemon_gw, base)
        pre = overview_hits()
        rec_split = PulseRecorder()
        rec_split.configure(split.dispatch)                 # emit FORWARDS over the socket
        rec_split.capture(concept=target, surface="atom", referer="https://github.com/",
                          ip="2.2.2.2", ua="Mozilla/5.0")
        time.sleep(3.0)
        post = overview_hits()
        check("S2 split records (F16 fix)", post == pre + 1,
              f"hits {pre}→{post}, stats={rec_split.stats()}")

        # ── S3 forge-clamp — raw socket emit asking for internal WITHOUT a signature ─────
        raw = SocketGateway(base)
        try:
            forged = {"jsonrpc": "2.0", "method": "pulse.emit", "id": "forge",
                      "params": {"client_id": "system.librarian", "concept": target,
                                 "surface": "atom", "ref": "direct", "visit": "dFORGE"},
                      "_trust": "internal"}                 # no _sig / _ts → must clamp to local
            resp = raw.dispatch(forged, "internal")
            err = (resp or {}).get("error") or {}
            clamped = err.get("code") == -32001 and "internal-only" in (err.get("message") or "")
            check("S3 forged internal clamps→rejected", clamped, f"resp={json.dumps(resp)[:160]}")
        finally:
            raw.close()

        # ── S4 zero-drop — a rejected emit is visible in stats, never silent ─────────────
        rec_bad = PulseRecorder()
        rec_bad.configure(split.dispatch)
        # An unresolvable concept → the kernel rejects the emit (-32602); it must be COUNTED.
        rec_bad.capture(concept="nonexistent:zzz_no_such_atom_zzz", surface="atom",
                        ip="3.3.3.3", ua="bot")
        time.sleep(3.0)
        st = rec_bad.stats()
        check("S4 rejection visible in stats", st.get("rejected", 0) >= 1 and st.get("last_reject"),
              f"stats={st}")
    finally:
        server.stop()

    print()
    if _fails:
        print(f"RESULT: FAIL — {len(_fails)} check(s) failed: {', '.join(_fails)}")
        sys.exit(1)
    print("RESULT: PASS — pulse capture works in BOTH topologies; forged elevation is clamped; "
          "rejections are never silent.")


if __name__ == "__main__":
    main()
