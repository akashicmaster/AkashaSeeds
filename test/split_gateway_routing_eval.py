#!/usr/bin/env python3
"""
SplitGateway routing eval — the public archives portal must FORWARD the live broadcast surface.

Root cause of "the AI News Station page sat on STANDING BY while the writer had the data": the
serve-only web portal answers reads from its OWN local engine, which does not run the broadcaster
and does not reflect the writer's runtime nucleus writes. society.station / society.broadcast.live
classify as "read", so SplitGateway served them LOCALLY → studios:[] / messages:[] on the public
site, even though the writer daemon's own read returned them. feed.* worked only because it is
unclassified and therefore forwarded. This pins the routing so the broadcast surface forwards too.

Run:  python test/split_gateway_routing_eval.py     (exit 0 = all pass)
"""
import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


class _FakeGW:
    def __init__(self, tag):
        self.tag = tag
        self.calls = []
    def dispatch(self, payload, transport_trust="network"):
        self.calls.append(payload.get("method"))
        return {"jsonrpc": "2.0", "id": payload.get("id"), "result": {"served_by": self.tag}}


def main():
    from api.portals import cell_ipc
    local = _FakeGW("local")
    remote = _FakeGW("remote")
    sg = cell_ipc.SplitGateway(local, "/tmp/nonexistent-akasha-base")
    sg._remote = remote          # inject a fake writer so _remote_gw() returns it (no real socket)

    def where(method, data=None):
        r = sg.dispatch({"jsonrpc": "2.0", "method": method,
                         "params": {"session_token": "gbk:x", "data": data or {}}, "id": "t"}, "network")
        return (r.get("result") or {}).get("served_by") or (r.get("error") or {}).get("message")

    # THE FIX: the guest-facing broadcast surface forwards to the writer (authoritative runtime data)
    for m in ("society.station", "society.broadcast.live", "society.broadcast", "society.feed"):
        check(f"{m} → forwarded to the writer (not the stale local engine)", where(m) == "remote")

    # Stable/ontology reads still served locally (fast, WAL-concurrent) — unchanged
    for m in ("read", "explore", "dive.look", "network.tree"):
        check(f"{m} → still served locally", where(m) == "local")

    # Guest-session creation stays a local read-side concern (mints a self-verifying token, no writer)
    check("session.guest.create → still served locally", where("session.guest.create") == "local")

    # sys.ping stays local
    check("sys.ping → still served locally", where("sys.ping") == "local")

    # A write still forwards to the one writer
    check("write → forwarded to the writer", where("write") == "remote")

    # Fail-closed: with no reachable writer, a forwarded broadcast read is REFUSED (not silently
    # served stale from the local engine).
    sg2 = cell_ipc.SplitGateway(_FakeGW("local2"), "/tmp/nonexistent-akasha-base-2")
    r = sg2.dispatch({"jsonrpc": "2.0", "method": "society.station",
                      "params": {"session_token": "gbk:x", "data": {}}, "id": "t"}, "network")
    check("no writer reachable → broadcast read refuses, never serves stale local",
          bool(r.get("error")) and "write path unavailable" in (r.get("error") or {}).get("message", ""),
          str(r.get("error")))

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("All SplitGateway routing checks passed."); sys.exit(0)


if __name__ == "__main__":
    main()
