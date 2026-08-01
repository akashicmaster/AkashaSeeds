"""
MCP portal eval (#30) — protocol handshake + tool dispatch + trust-appropriate session.

Verifies the stdlib MCP server (no mcp-python-sdk): the initialize/tools/list/tools/call
handshake, that tools bridge to the right kernel methods, and that the TWO transports resolve
sessions per their trust — LOCAL acts as the configured client, NETWORK mints a guest.
Uses a mock gateway that records dispatches (no boot).

Run:  python test/mcp_eval.py      (exit 0 = all pass)
"""
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from api.portals.mcp import (
    AkashaMCPPortal, mcp_http_process, MCP_TOOLS, TRUST_LOCAL, TRUST_NETWORK,
)

_fails = []


def check(name, cond, detail=""):
    print(("  PASS  " if cond else "  FAIL  ") + name + (f"   ({detail})" if detail and not cond else ""))
    if not cond:
        _fails.append(name)


class MockGateway:
    """Records (method, params, trust) and returns a canned result per method."""
    def __init__(self):
        self.calls = []

    def dispatch(self, payload, transport_trust="network"):
        method = payload.get("method")
        params = payload.get("params", {})
        self.calls.append((method, params, transport_trust))
        rid = payload.get("id")
        if method == "session.guest.create":
            return {"jsonrpc": "2.0", "id": rid, "result": {"binding_key": "gbk:MOCKGUEST", "ttl": 600}}
        if method == "sys.ping":
            return {"jsonrpc": "2.0", "id": rid, "result": {"pong": True}}
        if method == "kernel.memory.write":
            # simulate the kernel denying a guest write
            if params.get("session_token", "").startswith("gbk:") or params.get("session_token") == "":
                return {"jsonrpc": "2.0", "id": rid,
                        "error": {"code": -32001, "message": "Capability denied for 'kernel.memory.write'"}}
            return {"jsonrpc": "2.0", "id": rid, "result": {"key": "K_new"}}
        return {"jsonrpc": "2.0", "id": rid, "result": {"ok": method}}


def test_handshake():
    print("[1] initialize / tools/list handshake")
    gw = MockGateway()
    p = AkashaMCPPortal(gw, trust=TRUST_LOCAL, client_id="mcp:local")
    init = p.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                     "params": {"protocolVersion": "2025-03-26"}}, "mcp:local")
    check("initialize returns a result", "result" in init)
    check("protocolVersion is echoed back", init["result"]["protocolVersion"] == "2025-03-26")
    check("advertises tools capability", "tools" in init["result"]["capabilities"])
    check("serverInfo names akasha", init["result"]["serverInfo"]["name"] == "akasha")

    # notifications get no reply
    n = p.handle({"jsonrpc": "2.0", "method": "notifications/initialized"}, "mcp:local")
    check("notifications/initialized → no response", n is None)

    tl = p.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}, "mcp:local")
    names = {t["name"] for t in tl["result"]["tools"]}
    check("tools/list returns all tools", names == {t["name"] for t in MCP_TOOLS})
    check("every tool has an inputSchema", all("inputSchema" in t for t in tl["result"]["tools"]))


def test_tool_dispatch():
    print("[2] tools/call bridges to the right kernel method, with the session token + trust")
    gw = MockGateway()
    p = AkashaMCPPortal(gw, trust=TRUST_LOCAL, client_id="mcp:local")
    r = p.handle({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                  "params": {"name": "akasha_concept", "arguments": {"name": "icarus"}}}, "mcp:local")
    check("tools/call returns MCP content", "result" in r and "content" in r["result"])
    check("content is a text block", r["result"]["content"][0]["type"] == "text")
    m, params, trust = gw.calls[-1]
    check("dispatched to thesaurus.concept", m == "thesaurus.concept")
    check("passed the session token", params["session_token"] == "mcp:local")
    check("passed the arguments as data", params["data"] == {"name": "icarus"})
    check("dispatched at LOCAL trust", trust == TRUST_LOCAL)

    # unknown tool → isError
    e = p.handle({"jsonrpc": "2.0", "id": 4, "method": "tools/call",
                  "params": {"name": "nope", "arguments": {}}}, "mcp:local")
    check("unknown tool → isError", e["result"]["isError"] is True)

    # unknown protocol method → -32601
    nf = p.handle({"jsonrpc": "2.0", "id": 5, "method": "resources/list"}, "mcp:local")
    check("unknown MCP method → -32601", nf.get("error", {}).get("code") == -32601)


def test_local_session():
    print("[3] LOCAL transport acts as the configured client")
    gw = MockGateway()
    p = AkashaMCPPortal(gw, trust=TRUST_LOCAL, client_id="mcp:local")
    tok = p.resolve_session(None)
    check("LOCAL with no token → the client identity", tok == "mcp:local")
    check("LOCAL does NOT mint a guest",
          not any(c[0] == "session.guest.create" for c in gw.calls))


def test_network_guest():
    print("[4] NETWORK transport mints a guest (read-only) for an anonymous caller")
    gw = MockGateway()
    # anonymous initialize over HTTP → guest minted, returned as Mcp-Session-Id
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                       "params": {"name": "akasha_read", "arguments": {"id": "x"}}}).encode()
    resp, status, headers = mcp_http_process(gw, body, session_header="", auth_header="")
    check("guest session minted", any(c[0] == "session.guest.create" for c in gw.calls))
    check("guest token surfaced as Mcp-Session-Id", headers.get("Mcp-Session-Id") == "gbk:MOCKGUEST")
    read_call = next(c for c in gw.calls if c[0] == "read")
    check("read dispatched with the guest token", read_call[1]["session_token"] == "gbk:MOCKGUEST")
    check("dispatched at NETWORK trust", read_call[2] == TRUST_NETWORK)

    # a Bearer token wins (no guest minted), and reuse via Mcp-Session-Id (no re-mint)
    gw2 = MockGateway()
    body2 = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                        "params": {"name": "akasha_read", "arguments": {"id": "y"}}}).encode()
    resp2, _, headers2 = mcp_http_process(gw2, body2, session_header="", auth_header="Bearer akt:REAL")
    rc = next(c for c in gw2.calls if c[0] == "read")
    check("Bearer token used as session", rc[1]["session_token"] == "akt:REAL")
    check("Bearer path mints no guest", not any(c[0] == "session.guest.create" for c in gw2.calls))
    check("no new session header when the client already holds one", "Mcp-Session-Id" not in headers2)


def test_guest_write_denied():
    print("[5] a guest write tool is denied by the kernel (surfaced as isError)")
    gw = MockGateway()
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                       "params": {"name": "akasha_write", "arguments": {"text": "hi"}}}).encode()
    resp, status, headers = mcp_http_process(gw, body, session_header="gbk:MOCKGUEST", auth_header="")
    check("guest write → isError (kernel-denied)", resp["result"]["isError"] is True)
    check("the denial message is surfaced",
          "denied" in resp["result"]["content"][0]["text"].lower())


def main():
    test_handshake()
    test_tool_dispatch()
    test_local_session()
    test_network_guest()
    test_guest_write_denied()
    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails))
        sys.exit(1)
    print("ALL PASS — MCP handshake + tool dispatch + both transports (LOCAL client / NETWORK guest).")
    sys.exit(0)


if __name__ == "__main__":
    main()
