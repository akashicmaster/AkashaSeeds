"""
Adversarial eval for the single-writer-preserving portal path (approach A).

The regression this guards: the serve-only web portal became a SECOND nucleus writer.
The fix routes portal writes/auth/session to the ONE primary writer over the local
socket, while serving reads from the portal's own (WAL-concurrent) read engine —
WITHOUT laundering a network client's trust into local trust.

What is verified here (no full engine boot — the NEW surface is the trust plumbing):

  1. _effective_trust is DOWNGRADE-ONLY: a request on the local socket may lower its
     trust below the socket ceiling (network < local), never raise it (internal > local
     is refused), and a bogus/absent hint falls back to the ceiling.

  2. Over the REAL socket, a forwarded TRUST_NETWORK request reaches the daemon's
     gateway stamped network — NOT local. This is the security core: a guest write
     forwarded by the portal is authorized as a guest, so it is denied exactly as if it
     had hit the primary directly. A default (no-hint) request keeps the socket ceiling.

  3. SplitGateway routes reads → local read engine; writes/auth/session/unknown →
     the primary writer, carrying the caller's network trust. Fail-CLOSED: with no
     primary reachable, a would-be write is REFUSED, never executed locally.

Run:  python test/split_gateway_eval.py      (exit 0 = all pass)
"""
import os
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from api.portals import cell_ipc
from api.portals.cell_ipc import (
    CellIPCServer, SocketGateway, SplitGateway, ping,
    _effective_trust, TRUST_LOCAL, TRUST_NETWORK, TRUST_INTERNAL,
)

_fails = []


def check(name, cond):
    print(("  PASS  " if cond else "  FAIL  ") + name)
    if not cond:
        _fails.append(name)


# ── 1. downgrade-only rule (pure unit) ───────────────────────────────────────────
def test_effective_trust():
    print("[1] _effective_trust — downgrade-only")
    check("network under a local ceiling → network (downgrade allowed)",
          _effective_trust(TRUST_LOCAL, TRUST_NETWORK) == TRUST_NETWORK)
    check("internal under a local ceiling → local (UPGRADE refused)",
          _effective_trust(TRUST_LOCAL, TRUST_INTERNAL) == TRUST_LOCAL)
    check("local under a local ceiling → local (no-op)",
          _effective_trust(TRUST_LOCAL, TRUST_LOCAL) == TRUST_LOCAL)
    check("bogus hint → ceiling (fail-safe)",
          _effective_trust(TRUST_LOCAL, "administrator") == TRUST_LOCAL)
    check("absent/None hint → ceiling",
          _effective_trust(TRUST_LOCAL, None) == TRUST_LOCAL)
    # A network-ceiling socket (hypothetical) can never be raised to local either.
    check("network ceiling cannot be raised to local",
          _effective_trust(TRUST_NETWORK, TRUST_LOCAL) == TRUST_NETWORK)


# ── 2. trust preserved over the real socket ──────────────────────────────────────
class _RecordingGateway:
    """Records the transport_trust it was dispatched with, and echoes it back."""
    def __init__(self):
        self.seen = []

    def dispatch(self, payload, transport_trust):
        if isinstance(payload, dict) and payload.get("method") == "sys.ping":
            return {"jsonrpc": "2.0", "id": payload.get("id"), "result": {"pong": True}}
        self.seen.append(transport_trust)
        # Prove the kernel never sees the transport marker.
        leaked = isinstance(payload, dict) and "_trust" in payload
        return {"jsonrpc": "2.0", "id": payload.get("id") if isinstance(payload, dict) else None,
                "result": {"trust": transport_trust, "leaked_marker": leaked}}


def test_socket_trust_preserved():
    print("[2] forwarded trust reaches the daemon stamped network (not laundered to local)")
    base = tempfile.mkdtemp(prefix="akasha-split-")
    gw = _RecordingGateway()
    srv = CellIPCServer(gw, base)          # ceiling = TRUST_LOCAL (default)
    srv.start()
    try:
        client = SocketGateway(base)
        try:
            # (a) portal forwards a network-originated write → daemon must see NETWORK
            r = client.dispatch({"jsonrpc": "2.0", "method": "w", "params": {}, "id": 1},
                                transport_trust=TRUST_NETWORK)
            check("forwarded network request dispatched as network",
                  r.get("result", {}).get("trust") == TRUST_NETWORK)
            check("the _trust marker never reaches the kernel payload",
                  r.get("result", {}).get("leaked_marker") is False)

            # (b) console CLI (no hint / local) → daemon keeps the local ceiling
            r2 = client.dispatch({"jsonrpc": "2.0", "method": "w", "params": {}, "id": 2},
                                 transport_trust=TRUST_LOCAL)
            check("local (console) request keeps local trust", r2.get("result", {}).get("trust") == TRUST_LOCAL)

            # (c) a malicious client asking to be INTERNAL cannot be raised past the ceiling
            r3 = client.dispatch({"jsonrpc": "2.0", "method": "w", "params": {}, "id": 3},
                                 transport_trust=TRUST_INTERNAL)
            check("internal-trust request clamped to the socket ceiling (local, not internal)",
                  r3.get("result", {}).get("trust") == TRUST_LOCAL)
        finally:
            client.close()
    finally:
        srv.stop()


# ── 3. SplitGateway routing + fail-closed ────────────────────────────────────────
class _FakeLocal:
    def __init__(self):
        self.calls = []

    def dispatch(self, payload, transport_trust=TRUST_NETWORK):
        self.calls.append((payload.get("method"), transport_trust))
        return {"jsonrpc": "2.0", "id": payload.get("id"), "result": {"served_by": "local"}}


def test_split_routing():
    print("[3] SplitGateway — reads local, writes forwarded, fail-closed on no writer")
    base = tempfile.mkdtemp(prefix="akasha-split3-")
    local = _FakeLocal()
    sg = SplitGateway(local, base)

    # No primary writer is running on this base_dir → writes must fail closed.
    check("no primary writer is reachable", ping(base) is False)

    # read method (dive.look) → served locally
    rd = sg.dispatch({"jsonrpc": "2.0", "method": "look", "params": {}, "id": 1},
                     transport_trust=TRUST_NETWORK)
    check("read (look) served by local engine", rd.get("result", {}).get("served_by") == "local")
    check("read carried its trust to local", ("look", TRUST_NETWORK) in local.calls)

    # write method (w) → forwarded; no writer → REFUSED, never run locally
    before = len(local.calls)
    wr = sg.dispatch({"jsonrpc": "2.0", "method": "w", "params": {}, "id": 2},
                     transport_trust=TRUST_NETWORK)
    check("write is refused when the primary writer is down (fail-closed)",
          "error" in wr and wr["error"].get("code") == -32000)
    check("write did NOT execute on the local read engine", len(local.calls) == before)

    # unknown/unclassified method → also forwarded (never silently served locally)
    before2 = len(local.calls)
    unk = sg.dispatch({"jsonrpc": "2.0", "method": "totally.unknown.method", "params": {}, "id": 3},
                      transport_trust=TRUST_NETWORK)
    check("unclassified method forwarded (fail-closed), not served locally",
          "error" in unk and len(local.calls) == before2)

    # Now bring a primary writer up on the SAME base_dir → the write forwards & executes.
    gw = _RecordingGateway()
    srv = CellIPCServer(gw, base)
    srv.start()
    try:
        sg2 = SplitGateway(_FakeLocal(), base)
        wr2 = sg2.dispatch({"jsonrpc": "2.0", "method": "w", "params": {}, "id": 4},
                           transport_trust=TRUST_NETWORK)
        check("with the writer up, a write forwards and executes on the primary",
              wr2.get("result", {}).get("trust") == TRUST_NETWORK)
    finally:
        srv.stop()


def main():
    test_effective_trust()
    test_socket_trust_preserved()
    test_split_routing()
    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails))
        sys.exit(1)
    print("ALL PASS — portal single-writer path preserves trust and fails closed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
