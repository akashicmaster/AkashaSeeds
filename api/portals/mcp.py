"""
Akasha MCP portal — Model Context Protocol server (stdlib, no external SDK).

Exposes Akasha as a set of MCP tools so any MCP-speaking LLM client — Claude Desktop, a local
Ollama-driven agent, an editor plugin — can read and grow the memory mesh through the standard
protocol. MCP is just JSON-RPC 2.0 with a fixed method set (`initialize`, `tools/list`,
`tools/call`, `ping`, `notifications/*`), so the whole server is implemented here in stdlib —
no `mcp-python-sdk` dependency, which keeps it installable on the seeds/edge tier.

TWO transports, shipped together (the point of #30):

  • **stdio (local)** — `python akasha.py --mcp`. A newline-delimited JSON-RPC loop over
    stdin/stdout, the transport an MCP client spawns as a subprocess. Carries TRUST_LOCAL, so
    the client acts as an authenticated LOCAL Akasha client (read + its own-scope write) — the
    route for a co-located LLM (e.g. Ollama on the same VPS) collaborating as one client.

  • **HTTP (remote)** — POST to `/mcp` (ASGI) / `/api/mcp` (httpd). Carries TRUST_NETWORK: an
    anonymous caller is given a guest session (read-only, the prove-don't-assert default); a
    caller presenting a Bearer `akt:` token acts with that identity's scopes (scoped write).

Both transports call the SAME `AkashaMCPPortal` bridge → `gw.dispatch(...)`; the KERNEL is the
security gate (a guest calling a write tool is denied there, not here). Trust is set by the
transport, never the client — exactly as for every other portal.
"""
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("Harmonia.Portal.MCP")

# Trust levels (kept local so the light MCP path never imports the heavy kernel).
TRUST_LOCAL = "local"
TRUST_NETWORK = "network"

# Protocol version we implement. We echo the client's requested version when it sends one
# (maximising interop across MCP revisions) and fall back to this otherwise.
_DEFAULT_PROTOCOL = "2024-11-05"
_SERVER_INFO = {"name": "akasha", "version": "seeds12"}

# ── Tool catalogue — each maps to an existing kernel JSON-RPC method ──────────────
# `access` is documentation of the underlying capability; the KERNEL enforces it (a guest
# calling a write tool is denied at the capability gate). read tools work for a guest session;
# write tools need an authenticated (akt:) token or the local (stdio) route.
MCP_TOOLS: List[Dict[str, Any]] = [
    {"name": "akasha_ping", "access": "read", "rpc_method": "sys.ping",
     "description": "Check Akasha liveness.",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "akasha_read", "access": "read", "rpc_method": "read",
     "description": "Read an atom by id, alias, or $-reference. Returns content + metadata.",
     "inputSchema": {"type": "object", "properties": {"id": {"type": "string"}},
                     "required": ["id"]}},
    {"name": "akasha_explore", "access": "read", "rpc_method": "explore",
     "description": "Search/glossary: find concepts by name, namespace, or type.",
     "inputSchema": {"type": "object",
                     "properties": {"query": {"type": "string"},
                                    "ns": {"type": "string"},
                                    "limit": {"type": "integer", "default": 20}},
                     "required": ["query"]}},
    {"name": "akasha_concept", "access": "read", "rpc_method": "thesaurus.concept",
     "description": "Concept page for a word: neighbourhood, synonyms/broader/narrower, usage, "
                    "and external references — the primary lookup before writing prose.",
     "inputSchema": {"type": "object",
                     "properties": {"name": {"type": "string"}, "id": {"type": "string"}}}},
    {"name": "akasha_search", "access": "read", "rpc_method": "semantic.search",
     "description": "Semantic (meaning) search — nearest atoms by learned embedding. Give "
                    "`query` (text) or `id` (an atom to find neighbours of).",
     "inputSchema": {"type": "object",
                     "properties": {"query": {"type": "string"}, "id": {"type": "string"},
                                    "limit": {"type": "integer", "default": 10}}}},
    {"name": "akasha_gap_scan", "access": "read", "rpc_method": "gap.scan",
     "description": "Find important-but-thin concepts (ontology gaps) — the self-expanding "
                    "loop's discovery step: where the graph wants enrichment.",
     "inputSchema": {"type": "object",
                     "properties": {"limit": {"type": "integer", "default": 12}}}},
    {"name": "akasha_write", "access": "write", "rpc_method": "kernel.memory.write",
     "description": "Write a new atom (memory node). Requires an authenticated or local session.",
     "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}},
                     "required": ["text"]}},
    {"name": "akasha_link", "access": "write", "rpc_method": "kernel.memory.link",
     "description": "Link two atoms with a typed relation. Requires write access.",
     "inputSchema": {"type": "object",
                     "properties": {"src": {"type": "string"}, "dst": {"type": "string"},
                                    "rel": {"type": "string"}},
                     "required": ["src", "dst", "rel"]}},
    {"name": "akasha_fetch", "access": "write", "rpc_method": "contexa.fetch",
     "description": "Fetch external context (Wikipedia/URL) into the mesh. Requires write access.",
     "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}},
                     "required": ["query"]}},
    {"name": "akasha_command", "access": "write", "rpc_method": "sys.cli_exec",
     "description": "Run any Akasha CLI command as a raw string and get its result — the "
                    "CLI-equivalent escape hatch for operations the typed tools above don't cover "
                    "(e.g. 'explore icarus', 'w content=...', 'set.ls name=...', 'cast.new "
                    "name=Bot', 'society.feed group=salon'). The kernel gates each command by the "
                    "session's role (a guest can only run read commands); over the local stdio "
                    "route it is full CLI. Use this to carry out a user's request and report back.",
     "inputSchema": {"type": "object", "properties": {"command": {"type": "string"}},
                     "required": ["command"]}},
    # ── Society: the virtual dialogue space — avatar-mediated chat on a group ──
    # A society is a named channel (`space`, default "main") in a group; you speak AS an avatar
    # (cast) you own. LLM-agnostic — an LLM is just one more avatar here.
    {"name": "akasha_society_feed", "access": "read", "rpc_method": "society.feed",
     "description": "Read a dialogue space's timeline — the recent utterances by the avatars, "
                    "oldest→newest. Poll this to follow the conversation. `space` selects the "
                    "channel (default 'main'); `thread` filters to a message and its replies.",
     "inputSchema": {"type": "object",
                     "properties": {"group": {"type": "string"},
                                    "space": {"type": "string", "default": "main"},
                                    "thread": {"type": "string"},
                                    "limit": {"type": "integer", "default": 20}},
                     "required": ["group"]}},
    {"name": "akasha_society_say", "access": "write", "rpc_method": "society.say",
     "description": "Speak AS your avatar into a dialogue space (posts to the shared timeline). "
                    "Pass `cast` (your avatar id or name), `group`, optional `space` (channel) "
                    "and `reply` (a message key, to thread). Requires write access.",
     "inputSchema": {"type": "object",
                     "properties": {"text": {"type": "string"}, "cast": {"type": "string"},
                                    "group": {"type": "string"},
                                    "space": {"type": "string", "default": "main"},
                                    "reply": {"type": "string"}},
                     "required": ["text", "cast", "group"]}},
    {"name": "akasha_society_turn", "access": "read", "rpc_method": "society.turn",
     "description": "Whose turn it is: the last speaker and a suggested next avatar in a space "
                    "(the space defines turn order, so all participants share one rule).",
     "inputSchema": {"type": "object",
                     "properties": {"group": {"type": "string"},
                                    "space": {"type": "string", "default": "main"}},
                     "required": ["group"]}},
    {"name": "akasha_society_new", "access": "write", "rpc_method": "society.new",
     "description": "Create a dialogue space (channel) in a group (idempotent). `space` names it "
                    "(default 'main'); `topic` describes it. Requires write access.",
     "inputSchema": {"type": "object",
                     "properties": {"group": {"type": "string"},
                                    "space": {"type": "string", "default": "main"},
                                    "topic": {"type": "string"}},
                     "required": ["group"]}},
    {"name": "akasha_society_roster", "access": "read", "rpc_method": "society.roster",
     "description": "List the avatars present in a dialogue space (society discovery).",
     "inputSchema": {"type": "object",
                     "properties": {"group": {"type": "string"},
                                    "space": {"type": "string", "default": "main"}},
                     "required": ["group"]}},
]

_TOOL_BY_NAME = {t["name"]: t for t in MCP_TOOLS}


def _rpc_ok(rid, result):
    return {"jsonrpc": "2.0", "id": rid, "result": result}


def _rpc_err(rid, code, message):
    return {"jsonrpc": "2.0", "id": rid, "error": {"code": code, "message": message}}


class AkashaMCPPortal:
    """Transport-agnostic MCP server: turns MCP JSON-RPC messages into kernel dispatches.

    Construct with a live gateway, the transport's trust level, and (for stdio) the local
    client identity. `handle(msg, session_token)` processes one MCP message and returns a
    response dict (or None for a notification, which gets no reply)."""

    def __init__(self, gw, trust: str = TRUST_NETWORK, client_id: Optional[str] = None):
        self.gw = gw
        self.trust = trust
        # The identity a LOCAL (stdio) client acts as — a real, own-scope Akasha client.
        self.client_id = client_id or os.environ.get("AKASHA_MCP_CLIENT", "mcp:local")

    # -- session resolution (trust-appropriate) --
    def resolve_session(self, provided: Optional[str]) -> str:
        """Pick the session token for a request. A client-supplied token wins (an authenticated
        akt: or a guest gbk:); otherwise LOCAL acts as the configured client, and NETWORK mints
        a fresh guest session (read-only) so anonymous reads work without client-side setup."""
        if provided:
            return provided
        if self.trust == TRUST_LOCAL:
            return self.client_id
        return self._mint_guest()

    def _mint_guest(self) -> str:
        try:
            resp = self.gw.dispatch({"jsonrpc": "2.0", "method": "session.guest.create",
                                     "params": {"data": {}}, "id": "mcp_guest"}, self.trust)
            return (resp.get("result") or {}).get("binding_key", "") if isinstance(resp, dict) else ""
        except Exception:
            return ""

    # -- MCP protocol --
    def list_tools(self) -> List[Dict[str, Any]]:
        return [{"name": t["name"], "description": t["description"],
                 "inputSchema": t["inputSchema"]} for t in MCP_TOOLS]

    def call_tool(self, name: str, arguments: dict, session_token: str) -> Dict[str, Any]:
        """Dispatch a tool to its kernel method; wrap the result as MCP tool content."""
        tool = _TOOL_BY_NAME.get(name)
        if not tool:
            return {"content": [{"type": "text", "text": f"Unknown tool: {name}"}], "isError": True}
        resp = self.gw.dispatch({
            "jsonrpc": "2.0", "method": tool["rpc_method"],
            "params": {"session_token": session_token, "data": arguments or {}},
            "id": f"mcp:{name}",
        }, self.trust)
        if isinstance(resp, dict) and "error" in resp:
            msg = resp["error"].get("message", str(resp["error"])) if isinstance(resp["error"], dict) else str(resp["error"])
            return {"content": [{"type": "text", "text": msg}], "isError": True}
        result = resp.get("result", {}) if isinstance(resp, dict) else resp
        text = result if isinstance(result, str) else json.dumps(result, ensure_ascii=False, indent=2)
        return {"content": [{"type": "text", "text": text}], "isError": False}

    def handle(self, msg: dict, session_token: str) -> Optional[dict]:
        """Process one MCP JSON-RPC message. Returns a response dict, or None for a
        notification (a request with no id / a `notifications/*` method) which gets no reply."""
        if not isinstance(msg, dict):
            return _rpc_err(None, -32600, "invalid request")
        method = msg.get("method", "")
        rid = msg.get("id")
        is_notification = "id" not in msg or str(method).startswith("notifications/")

        if method == "initialize":
            params = msg.get("params") or {}
            proto = params.get("protocolVersion") or _DEFAULT_PROTOCOL
            return _rpc_ok(rid, {
                "protocolVersion": proto,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": _SERVER_INFO,
                "instructions": "Akasha semantic memory. Use akasha_concept/akasha_explore/"
                                "akasha_search to look up meaning; akasha_write/akasha_link to "
                                "grow it (needs write access); akasha_gap_scan to find gaps.",
            })
        if is_notification:
            return None                       # initialized / cancelled / progress — no reply
        if method == "ping":
            return _rpc_ok(rid, {})
        if method == "tools/list":
            return _rpc_ok(rid, {"tools": self.list_tools()})
        if method == "tools/call":
            params = msg.get("params") or {}
            name = params.get("name", "")
            args = params.get("arguments") or {}
            return _rpc_ok(rid, self.call_tool(name, args, session_token))
        return _rpc_err(rid, -32601, f"Method not found: {method}")


# ── stdio transport (local) ──────────────────────────────────────────────────────

def run_mcp_stdio(gw, client_id: Optional[str] = None, trust: str = TRUST_LOCAL) -> None:
    """Serve MCP over stdin/stdout (newline-delimited JSON-RPC). Blocks until EOF. This is the
    subprocess transport an MCP client (Claude Desktop, a local Ollama agent) spawns; it runs
    at TRUST_LOCAL, so the client is an authenticated local Akasha client."""
    portal = AkashaMCPPortal(gw, trust=trust, client_id=client_id)
    session_token = portal.resolve_session(None)     # LOCAL → the configured client identity
    logger.info("[MCP] stdio server ready (client=%s, trust=%s)", portal.client_id, trust)
    _in = sys.stdin
    _out = sys.stdout
    for line in _in:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except (ValueError, UnicodeDecodeError):
            _write_line(_out, _rpc_err(None, -32700, "parse error"))
            continue
        try:
            resp = portal.handle(msg, session_token)
        except Exception as exc:                     # a bug must not kill the loop
            logger.exception("[MCP] handler error")
            resp = _rpc_err(msg.get("id") if isinstance(msg, dict) else None,
                            -32603, f"internal error: {exc}")
        if resp is not None:
            _write_line(_out, resp)


def _write_line(out, obj) -> None:
    out.write(json.dumps(obj, ensure_ascii=False) + "\n")
    out.flush()


# ── HTTP transport (remote) — shared by ASGI (/mcp) and httpd (/api/mcp) ──────────

def mcp_http_process(gw, raw_body: bytes, session_header: str = "",
                     auth_header: str = "", trust: str = TRUST_NETWORK
                     ) -> Tuple[dict, int, Dict[str, str]]:
    """Handle one MCP HTTP POST. Returns (json_response, http_status, extra_headers).

    Session resolution: an `Authorization: Bearer <token>` wins (authenticated / guest token
    the client already holds), else an `Mcp-Session-Id` from a prior initialize, else a fresh
    guest session is minted and returned as `Mcp-Session-Id` so the client can reuse it. The
    kernel enforces capability — a guest calling a write tool is denied there."""
    portal = AkashaMCPPortal(gw, trust=trust)
    try:
        msg = json.loads(raw_body.decode("utf-8")) if raw_body else {}
    except (ValueError, UnicodeDecodeError):
        return _rpc_err(None, -32700, "parse error"), 400, {}

    provided = ""
    if auth_header.startswith("Bearer "):
        provided = auth_header[7:].strip()
    elif session_header:
        provided = session_header.strip()
    session_token = portal.resolve_session(provided or None)

    try:
        resp = portal.handle(msg, session_token)
    except Exception as exc:
        logger.exception("[MCP] http handler error")
        return _rpc_err(msg.get("id") if isinstance(msg, dict) else None,
                        -32603, f"internal error: {exc}"), 200, {}

    headers: Dict[str, str] = {}
    # Surface the session so the client reuses one guest slot instead of minting per request.
    if session_token and session_token != provided:
        headers["Mcp-Session-Id"] = session_token
    if resp is None:                                  # notification → 202 Accepted, no body
        return {}, 202, headers
    return resp, 200, headers


# ── back-compat / launcher entry ─────────────────────────────────────────────────

def run_mcp(gw, client_id: str = None):
    """Default entry point (stdio). Kept for api.portals.__init__ export compatibility."""
    run_mcp_stdio(gw, client_id=client_id, trust=TRUST_LOCAL)
