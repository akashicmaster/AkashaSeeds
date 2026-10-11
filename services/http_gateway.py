"""
Base Web Service Framework (HTTP Gateway - Pro Edition).

A highly resilient, zero-dependency HTTP server bridging external web clients 
to the internal Akasha Matrix.

[PRO EDITION SECURITY]
- Strict adherence to JSON-RPC 2.0 error specifications.
- Autonomic port discovery (Dynamic Port Hopping).
- Secure IAM injection for pre-auth handshake procedures.
"""

import os
import sys
import stat as _stat
import json
import http.cookies
import urllib.parse
import socket
import logging
import traceback
from http.server import HTTPServer, ThreadingHTTPServer, SimpleHTTPRequestHandler
from typing import Dict, Any, Callable, Optional

import api.gateway as _gw_module

# Terminal colors for immersive observability
class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    DIM = '\033[2m'
    BOLD = '\033[1m'

logger = logging.getLogger("Harmonia.WebService")


def portal_banner(host: str, port: int, scheme: str = "http") -> list:
    """Human-readable 'the web portal is up' lines, honest about reachability.
    Shared by both portals (httpd here, uvicorn in akasha.py) so a user is never
    left guessing whether the site is local-only or actually published.
    *scheme* is "https" when TLS is terminating in the portal."""
    g, d, e = Colors.GREEN, Colors.DIM, Colors.ENDC
    _default_port = 443 if scheme == "https" else 80
    _hostport = lambda h: f"{h}" if port == _default_port else f"{h}:{port}"
    _tls_note = "  (HTTPS · port 80 redirects here)" if scheme == "https" else ""
    if host in ("0.0.0.0", "::"):
        _dom = "" if port == _default_port else f" For a bare domain, run with AKASHA_PORT={_default_port}."
        return [
            f"{g}[+] Web portal is PUBLIC — listening on all interfaces, port {port}.{_tls_note}{e}",
            f"{d}    Reach it at  {scheme}://<this-server-ip>{'' if port == _default_port else ':' + str(port)}/{e}",
            f"{d}    Open the firewall for port {port}{' and 80' if scheme == 'https' else ''}.{_dom}{e}",
        ]
    if host in ("127.0.0.1", "localhost", "::1"):
        return [
            f"{g}[+] Web portal → {scheme}://{_hostport(host)}/   {d}(THIS MACHINE ONLY){e}",
            f"{d}    To publish externally: AKASHA_HOST=0.0.0.0 [AKASHA_PORT={_default_port}] + open the firewall.{e}",
        ]
    return [f"{g}[+] Web portal → {scheme}://{_hostport(host)}/{_tls_note}{e}"]

# ── Auth gate (seeds simplified-archives) ─────────────────────────────────────────────────────
# A server-side, docroot-wide login wall for the AUTHENTICATED simplified archives (the seeds line),
# kept separate from the guest-open thesaurus archives. When AKASHA_PORTAL_GATE is set, every HTML
# page is served ONLY to a request that carries a valid akt: session cookie; everyone else gets this
# self-contained login page (verifying against kernel.auth.verify, then setting the cookie + reloading).
# Stdlib-only so it works on the seeds httpd portal (no uvicorn/FastAPI needed).
_PORTAL_GATE_HTML = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Akasha — sign in</title>
<style>
 :root{--bg:#04070d;--ink:#e6dcff;--muted:#a9a0c8;--faint:#6f6791;--line:rgba(150,130,220,.2);--violet:#b9a5ff;--amber:#ffcf8c}
 *{box-sizing:border-box;margin:0;padding:0}
 html,body{min-height:100vh;color:var(--ink);font-family:'Courier New',Courier,monospace;
  background:radial-gradient(1100px 720px at 50% -12%,#160e2e 0%,#0a0818 55%,#04070d 100%) fixed,var(--bg);
  display:flex;align-items:center;justify-content:center;padding:24px}
 .card{width:min(400px,92vw);border:1px solid var(--line);border-radius:16px;background:rgba(18,14,34,.6);
  padding:30px 26px;box-shadow:0 0 60px rgba(90,50,160,.18)}
 .brand{display:flex;align-items:center;gap:10px;justify-content:center;margin-bottom:4px}
 .brand .dot{width:9px;height:9px;border-radius:50%;background:var(--amber);box-shadow:0 0 12px var(--amber)}
 .brand b{letter-spacing:4px;font-size:.72rem;color:var(--amber);font-weight:normal;text-transform:uppercase}
 h1{text-align:center;font-size:1.15rem;letter-spacing:2px;margin:14px 0 4px;color:#e2d5ff}
 p.sub{text-align:center;font-size:.66rem;letter-spacing:1px;color:var(--faint);margin-bottom:22px}
 label{display:block;font-size:.56rem;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin:14px 0 5px}
 input{width:100%;background:rgba(8,6,17,.7);border:1px solid var(--line);border-radius:9px;color:var(--ink);
  font-family:inherit;font-size:.85rem;padding:11px 13px;outline:none}
 input:focus{border-color:var(--violet)}
 button{width:100%;margin-top:22px;font-family:inherit;font-size:.7rem;letter-spacing:2px;text-transform:uppercase;
  color:#0a0818;background:var(--violet);border:none;border-radius:10px;padding:12px;cursor:pointer;transition:.2s}
 button:hover{background:#cbb8ff}
 .msg{min-height:1.2em;margin-top:14px;text-align:center;font-size:.66rem;letter-spacing:.5px;color:var(--muted)}
 .msg.err{color:#ff9a9a}
</style></head><body>
 <form class="card" onsubmit="event.preventDefault();login()">
  <div class="brand"><span class="dot"></span><b>Akasha</b></div>
  <h1>Your Archives</h1>
  <p class="sub">a private semantic space · sign in to enter</p>
  <label for="u">User ID</label>
  <input id="u" autocomplete="username" autocapitalize="none" autocorrect="off" spellcheck="false" autofocus>
  <label for="p">Passphrase</label>
  <input id="p" type="password" autocomplete="current-password">
  <button type="submit">Enter</button>
  <div class="msg" id="m"></div>
 </form>
<script>
 async function login(){
  var u=document.getElementById('u').value.trim(),p=document.getElementById('p').value,m=document.getElementById('m');
  m.className='msg';
  if(!u||!p){m.textContent='Enter your id and passphrase.';return;}
  m.textContent='Verifying…';
  try{
   var r=await fetch('/api/rpc',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({jsonrpc:'2.0',method:'kernel.auth.verify',params:{data:{user_id:u,passphrase:p}},id:'auth'})}).then(x=>x.json());
   if(r.error) throw new Error(r.error.message||'Auth failed');
   if(r.result&&r.result.status==='authenticated'){
    document.cookie='akt='+encodeURIComponent(r.result.session_token)+'; path=/; max-age=86400; SameSite=Strict';
    try{localStorage.setItem('akasha_user',r.result.user_id||'');localStorage.setItem('akt',r.result.session_token);}catch(e){}
    location.reload();
   }else{m.className='msg err';m.textContent='Access denied.';}
  }catch(e){m.className='msg err';m.textContent='Login error: '+e.message;}
 }
</script></body></html>"""


class BaseWebHandler(SimpleHTTPRequestHandler):
    """
    HTTP Request Handler.
    Routes incoming traffic to static assets or the Akasha RPC gateway.
    """
    routes: Dict[str, Dict[str, Any]] = {}
    gw = None  # injected by BaseWebService.start() via dynamic subclass
    gw_holder = None  # {"gw": <gw|None>} for deferred (Lever C) builds; drives the live gateway
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "static"))

    def __init__(self, *args, **kwargs):
        # Allow dynamic subclass to override static_dir via class attribute
        super().__init__(*args, directory=self.static_dir, **kwargs)

    # ── Lever C — warming state (port bound, substrate still loading) ───────────────────
    def _live_gw(self):
        """The live gateway. In deferred (warming) mode it comes from the shared holder and is
        None until the background build finishes; otherwise the injected/singleton gateway."""
        if self.gw_holder is not None:
            return self.gw_holder.get("gw")
        return self._live_gw()

    def _warming(self) -> bool:
        """True while the port is bound but the gateway substrate is still loading."""
        return self.gw_holder is not None and self.gw_holder.get("gw") is None

    def _serve_warming_page(self):
        """The 'warming up' HTML — shown for every page GET while the substrate loads, so the
        site is never a refused connection or a broken shell. Reuses the shared ASGI page."""
        try:
            from api.portals.asgi import _WARMING_HTML as _html
        except Exception:
            _html = ("<!doctype html><meta charset=utf-8><title>Akasha — warming up</title>"
                     "<meta http-equiv=refresh content=3>"
                     "<body style='font-family:sans-serif;text-align:center;padding-top:20vh'>"
                     "<h1>Akasha is warming up…</h1><p>The substrate is loading. "
                     "This page refreshes automatically.</p></body>")
        body = _html.encode("utf-8")
        self.send_response(200)
        self._send_cors_headers()
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Retry-After", "3")
        self.end_headers()
        try:
            self.wfile.write(body)
        except Exception:
            pass

    def _serve_warming_json(self):
        """The API-side warming answer — a 503 (still an HTTP response → 'alive' to the health
        probe) so programmatic clients and the Supervisor tick know to retry, not that we're dead."""
        self._send_json({"jsonrpc": "2.0", "id": None, "status": "warming",
                         "error": {"code": -32002,
                                   "message": "Akasha is warming up — loading the substrate. Retry shortly."}},
                        status=503, extra_headers={"Retry-After": "3"})

    def _handle_health_get(self):
        """GET /health → sys.ping JSON (parity with the ASGI portal), so the warming page's
        poll flips to the live site promptly once the gateway is ready."""
        gw = self._live_gw()
        try:
            resp = gw.dispatch({"jsonrpc": "2.0", "method": "sys.ping",
                                "params": {"session_token": "_health_"}, "id": "health"})
            result = resp.get("result", {}) if isinstance(resp, dict) else {}
            result.setdefault("status", "ok")
            self._send_json(result)
        except Exception as exc:
            self._send_json({"status": "degraded", "error": str(exc)}, status=200)

    def do_OPTIONS(self):
        self._send_cors_headers()
        self.send_response(200)
        self.end_headers()

    def _send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')

    def do_POST(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        # Lever C — while the substrate is still loading every RPC/beacon/MCP path needs the
        # gateway, so answer a 503 'warming' (an HTTP response → 'alive' to the health probe).
        if self._warming():
            return self._serve_warming_json()

        # F25a: the archives-derived rooms (word/field/worldmap/philosophy/…) POST to /rpc, while the
        # apps (cosmos/note/…) POST to /api/rpc. The ASGI portal serves both; accept both here too so the
        # seeds simplified-archives rooms work byte-identical to their archives originals (no JS fork).
        if path in ('/api/rpc', '/rpc'):
            self._handle_rpc()
        elif path == '/pulse':
            self._handle_pulse_beacon()
        elif path in ('/api/mcp', '/mcp'):
            self._handle_mcp()
        elif path in self.routes and self.routes[path]['method'] == 'POST':
            self._execute_custom_handler(self.routes[path]['handler'])
        else:
            self._send_json({"error": "Endpoint not found."}, status=404)

    @staticmethod
    def _portal_gate_on() -> bool:
        """Whether the docroot-wide auth gate is armed (the seeds simplified-archives line). OFF by
        default so the guest-open thesaurus archives and the public seeds portal are unaffected."""
        return os.environ.get("AKASHA_PORTAL_GATE", "").strip().lower() in ("1", "true", "yes", "on")

    def _gate_authed(self) -> bool:
        """True iff the request carries an akt: token (cookie `akt`, else a Bearer header) that resolves
        to an AUTHENTICATED (non-guest) identity — the same resolver the ASGI labo gate uses."""
        tok = ""
        ck = self.headers.get("Cookie", "")
        if ck:
            try:
                jar = http.cookies.SimpleCookie(); jar.load(ck)
                if "akt" in jar:
                    tok = jar["akt"].value
            except Exception:
                tok = ""
        if not tok:
            auth = self.headers.get("Authorization", "")
            if auth.startswith("Bearer "):
                tok = auth[7:].strip()
        if not tok:
            return False
        try:
            gw = self._live_gw()
            cid, role = gw.kernel_client.iam.resolve_session_token(tok)
            rv = str(getattr(role, "value", role)).lower()
            return bool(cid) and rv not in ("guest", "")
        except Exception:
            return False

    def _serve_login_gate(self):
        body = _PORTAL_GATE_HTML.encode("utf-8")
        self.send_response(401)
        self._send_cors_headers()
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store, must-revalidate")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        # Lever C — during warming show the loading page for EVERY GET (no half-built shell whose
        # RPC calls would just 503). The page self-polls /health and opens the real site when ready.
        if self._warming():
            return self._serve_warming_page()

        if path == '/health':
            self._handle_health_get()
        elif path == '/api/readme':
            self._serve_readme()
        elif path in self.routes and self.routes[path]['method'] == 'GET':
            self._execute_custom_handler(self.routes[path]['handler'])
        else:
            # Auth gate: for the seeds simplified-archives, an unauthenticated request for an HTML PAGE
            # gets the login wall instead. Non-HTML assets pass (the login page is self-contained; page
            # DATA is separately token-gated at the kernel), so nothing sensitive leaks pre-auth.
            if self._portal_gate_on():
                try:
                    fp = self.translate_path(self.path)
                except Exception:
                    fp = ""
                if fp.endswith('.html') and not self._gate_authed():
                    return self._serve_login_gate()
            super().do_GET()

    def _serve_readme(self):
        """Serve the project README.md as plain text (no auth required)."""
        readme_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', 'README.md')
        )
        try:
            with open(readme_path, 'r', encoding='utf-8') as f:
                content = f.read().encode('utf-8')
            self.send_response(200)
            self._send_cors_headers()
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_response(404)
            self.end_headers()

    def _host_dir(self):
        """Which archives sub-directory does the request's Host header map to?
        None → default root. Shared rule with the ASGI portal (host_routing)."""
        try:
            from services.host_routing import resolve_host_dir
            return resolve_host_dir(self.headers.get("Host", ""), self.directory)
        except Exception:
            return None

    def translate_path(self, path):
        """
        Override to serve <static>/<name>/index.html directly for /<name> and /<name>/
        requests, avoiding the 301 redirect that SimpleHTTPRequestHandler normally issues
        for directory paths (the redirect breaks Codespace port-forwarding proxies).

        Also applies host-based document-root routing: a request on
        world.<base> is served from <static>/world/… (see services/host_routing).
        Only static GETs reach here — the RPC/readme endpoints are handled in
        do_POST/do_GET before this — so no reserved-path exclusion is needed.
        """
        # /docs/ (the documentation viewer + its markdown) lives at the repo root, NOT under the static
        # docroot — serve it from there so the seeds Academy's Docs link resolves. Traversal-safe.
        _pure = path.split('?', 1)[0].split('#', 1)[0]
        if _pure == '/docs' or _pure.startswith('/docs/'):
            docs_root = os.path.abspath(os.path.join(self.static_dir, '..', '..', 'docs'))
            rel = _pure[len('/docs/'):] if _pure.startswith('/docs/') else ''
            fs = os.path.normpath(os.path.join(docs_root, rel))
            if fs == docs_root or fs.startswith(docs_root + os.sep):
                if os.path.isdir(fs):
                    idx = os.path.join(fs, 'index.html')
                    if os.path.isfile(idx):
                        return idx
                return fs
        host_dir = self._host_dir()
        if host_dir:
            pure = path.split('?', 1)[0].split('#', 1)[0]
            prefix = '/' + host_dir
            if not (pure == prefix or pure.startswith(prefix + '/')):
                path = prefix + (pure if pure != '/' else '/')
        fs_path = super().translate_path(path)
        if os.path.isdir(fs_path):
            index = os.path.join(fs_path, 'index.html')
            if os.path.isfile(index):
                return index
        return fs_path

    def send_head(self):
        """Add Cache-Control: no-store for HTML files so browsers never cache stale pages."""
        path = self.translate_path(self.path)
        if path.endswith('.html') and os.path.isfile(path):
            try:
                f = open(path, 'rb')
            except OSError:
                self.send_error(404, "File not found")
                return None
            fs = os.fstat(f.fileno())
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(fs[_stat.ST_SIZE]))
            self.send_header('Cache-Control', 'no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self._send_cors_headers()
            self.end_headers()
            return f
        return super().send_head()

    def _handle_mcp(self):
        """MCP (Model Context Protocol) over HTTP — the remote LLM route (TRUST_NETWORK).
        Delegates protocol + session handling to the shared mcp_http_process; a guest session
        is minted for anonymous callers (read-only), a Bearer akt: token acts with its scopes."""
        content_length = int(self.headers.get('Content-Length', 0))
        raw = self.rfile.read(content_length) if content_length > 0 else b""
        gw = self._live_gw()
        try:
            from api.portals.mcp import mcp_http_process
            resp, status, extra = mcp_http_process(
                gw, raw,
                session_header=self.headers.get("Mcp-Session-Id", ""),
                auth_header=self.headers.get("Authorization", ""))
        except Exception as exc:
            logger.error(f"[MCP] http error: {exc}")
            resp, status, extra = ({"jsonrpc": "2.0", "error": {"code": -32603,
                                    "message": str(exc)}, "id": None}, 200, {})
        self._send_json(resp, status=status, extra_headers=extra)

    def _handle_rpc(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length) if content_length > 0 else b""

        try:
            req = json.loads(post_data.decode('utf-8'))
            
            # Pre-auth: inject guest token so kernel can route handshake methods
            # before a real session exists.
            if isinstance(req, dict):
                method = req.get("method", "")
                params = req.get("params") if isinstance(req.get("params"), dict) else {}
                pre_auth = {
                    "sys.ping", "sys.status",
                    "kernel.auth.status", "auth.status",
                    "kernel.auth.verify", "auth.verify",
                    "kernel.genesis_rite",
                }
                if method in pre_auth and not params.get("session_token"):
                    req.setdefault("params", {})["session_token"] = "guest"
            
            gw = self._live_gw()
            res = gw.dispatch(req)
            self._send_json(res)
            
        except json.JSONDecodeError:
            self._send_json({"jsonrpc": "2.0", "error": {"code": -32700, "message": "Invalid JSON"}, "id": None})
        except Exception as e:
            logger.error(f"[RPC Failure] {traceback.format_exc()}")
            self._send_json({"jsonrpc": "2.0", "error": {"code": -32603, "message": str(e)}, "id": None})

    def _handle_pulse_beacon(self):
        """Access-analytics beacon (parity with the ASGI /pulse route). Server-side capture:
        buffers the hit and records it asynchronously under a system identity — never a guest
        write. Privacy enforced here: DNT is honoured; only a coarse referrer/UA and a
        daily-rotating salted visitor hash are derived (no PII stored). Always answers 204."""
        try:
            clen = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(clen) if clen > 0 else b""
            data = json.loads(body.decode('utf-8')) if body else {}
        except Exception:
            data = {}
        try:
            from lib.harmonia.pulse_recorder import recorder as _rec
            gw = self._live_gw()
            if not _rec.configured and gw is not None:
                _rec.configure(gw.dispatch)
            concept = (data or {}).get("concept") or ""
            if concept:
                fwd = self.headers.get('X-Forwarded-For', '')
                ip = (fwd.split(',')[0].strip() if fwd else (self.client_address[0] if self.client_address else ""))
                _rec.capture(
                    concept=concept, surface=(data.get("surface") or ""),
                    referer=self.headers.get('Referer', ''), prev=(data.get("prev") or ""),
                    ip=ip, ua=self.headers.get('User-Agent', ''),
                    dnt=(self.headers.get('DNT') == '1' or self.headers.get('Sec-GPC') == '1'),
                    own_host=(self.headers.get('Host', '').split(':', 1)[0]),
                )
        except Exception:
            pass
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def _execute_custom_handler(self, handler_func: Callable):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else b""
        try:
            req_data = json.loads(body.decode('utf-8')) if body else {}
        except json.JSONDecodeError:
            req_data = {}

        # Require a valid session token — custom endpoints are not pre-auth
        if not req_data.get("session_token"):
            self._send_json(
                {"jsonrpc": "2.0", "error": {"code": -32001, "message": "Authentication required: provide session_token"}, "id": None},
                status=401
            )
            return

        try:
            self._send_json(handler_func(req_data))
        except Exception as e:
            logger.error(f"[Custom Handler Failure] {e}")
            self._send_json({"error": "Internal execution error"}, status=500)

    def _send_json(self, data: Any, status: int = 200, extra_headers: dict = None):
        self.send_response(status)
        self._send_cors_headers()
        self.send_header('Content-type', 'application/json; charset=utf-8')
        for _k, _v in (extra_headers or {}).items():
            self.send_header(_k, _v)
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def log_message(self, format: str, *args):
        logger.debug(f"[HTTP] {format % args}")

class _QuietHTTPServer(ThreadingHTTPServer):
    """The portal's HTTP server, hardened for real browsers on constrained hosts.

    Two things a plain single-thread HTTPServer gets wrong for mobile Safari / a-Shell:

    1. **Concurrency.** A browser opens several parallel + speculative connections per
       page (preconnect, prefetch, favicon, asset fan-out). Served one-at-a-time they
       queue behind each other; the browser cancels the ones it's tired of waiting for,
       and on a slow device the *actual* HTML request can starve — so the portal never
       finishes loading. Threading each connection lets the page complete regardless of
       the speculative ones. Safe here: the backend uses thread-local SQLite read
       connections and serialises every write through the WriteQueue (the design's
       read-side parallelism), so concurrent request threads never race the write path.

    2. **Disconnect noise.** When the client tears a connection down mid-response the
       server hits BrokenPipeError / ConnectionResetError inside wfile.write(), which the
       stdlib dumps as a scary 'Exception occurred during processing of request …'
       traceback. On a slow console that ~30-line dump per cancelled connection itself
       starves the server. It is client-side teardown, not a server fault — nothing is
       corrupted — so log it quietly. REAL errors still get the full report.
    """

    daemon_threads = True          # don't let in-flight requests block shutdown

    _BENIGN = (BrokenPipeError, ConnectionResetError, ConnectionAbortedError,
               TimeoutError)

    def handle_error(self, request, client_address):
        import sys
        exc = sys.exc_info()[1]
        if isinstance(exc, self._BENIGN):
            logger.debug("[HTTP] client %s disconnected mid-response (%s) — ignored",
                         client_address, type(exc).__name__)
            return
        super().handle_error(request, client_address)


class BaseWebService:
    """Manager for the HTTP Server lifecycle."""
    def __init__(self, gw=None, port: int = 8080, host: str = '0.0.0.0', static_dir: str = None,
                 gw_factory=None):
        self.gw           = gw
        self.gw_factory   = gw_factory   # Lever C: zero-arg builder run on a bg thread after bind
        self._gw_holder   = {"gw": gw}   # shared with the handler; the live gw once built
        self.host         = host
        self.target_port  = port
        self.port         = port
        self.routes: Dict[str, Dict[str, Any]] = {}
        self._httpd       = None
        self._static_dir  = static_dir  # None → use handler default (services/static)

    def _find_free_port(self):
        for port in range(self.target_port, 65535):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex((self.host, port)) != 0: return port
        return self.target_port

    def add_route(self, path: str, method: str, handler: Callable):
        self.routes[path] = {'method': method.upper(), 'handler': handler}

    @staticmethod
    def _is_ios() -> bool:
        """True on a-Shell / iOS / iPadOS. There, a server bound to the *explicit*
        loopback 127.0.0.1 is reachable only inside the same process — a separate
        client process (Safari, another curl) gets 'Connection refused'. Binding all
        interfaces works (which is why the stock `python -m http.server`, whose default
        bind is 0.0.0.0, serves Safari there). platform.system() reports 'iPadOS' /
        'iOS' and machine is like 'iPad14,1' — the same signal env_detector shows as
        'OS: Ipados'. A same-process reachability probe can't detect this (it succeeds),
        so we key off the platform directly."""
        try:
            import platform as _p
            sysname = _p.system().lower()
            machine = _p.machine().lower()
        except Exception:
            sysname = machine = ""
        return (sysname in ("ios", "ipados", "iphoneos")
                or machine.startswith(("ipad", "iphone"))
                or getattr(sys, "platform", "") == "ios")

    def start(self, ready_event=None):
        """Bind and serve. If *ready_event* is given, it is set once the banner
        has been printed (or on failure) so the boot sequence can flush all
        startup output before showing an interactive prompt — otherwise this
        message, printed from the portal thread, races the genesis/auth prompt."""
        self.port = self._find_free_port()
        # Lever C — if a factory is given, bind the port NOW and build the gateway (the heavy
        # ~1GB substrate load) on a background thread; the handler serves a warming page until the
        # holder is populated. The site is never a refused connection during boot.
        if self.gw_factory is not None:
            import threading

            def _build():
                try:
                    self._gw_holder["gw"] = self.gw_factory()
                    logger.info("[HTTP] Live gateway ready — serving real content.")
                except Exception as exc:
                    logger.error("[HTTP] Gateway build failed — exiting so the Supervisor "
                                 "respawns: %s", exc, exc_info=True)
                    try:
                        self.stop()
                    finally:
                        os._exit(1)   # never serve the warming page forever

            threading.Thread(target=_build, name="portal-gateway-build", daemon=True).start()

        attrs = {
            'routes':    self.routes,
            'gw':        self.gw,            # may be None when deferred; the holder drives the live one
            'gw_holder': self._gw_holder,
        }
        if self._static_dir:
            attrs['static_dir'] = os.path.abspath(self._static_dir)
        handler_class = type('DynamicWebHandler', (BaseWebHandler,), attrs)
        _loopback = ("127.0.0.1", "localhost", "::1")
        # On iOS/a-Shell a loopback bind is unreachable from other processes (Safari),
        # so bind all interfaces instead — with no operator action. Desktop keeps the
        # requested (safe, localhost-only) bind.
        if self.host in _loopback and self._is_ios():
            print(f"{Colors.WARNING}[i] iOS/a-Shell detected — 127.0.0.1 is only reachable "
                  f"in-process here; binding all interfaces so Safari can reach the "
                  f"portal.{Colors.ENDC}", flush=True)
            self.host = "0.0.0.0"
        try:
            # Defensive: if the requested loopback bind itself fails, fall back too.
            try:
                self._httpd = _QuietHTTPServer((self.host, self.port), handler_class)
            except OSError as _bind_err:
                if self.host not in _loopback:
                    raise
                logger.warning("[HTTP] bind to %s failed (%s) — falling back to all "
                               "interfaces", self.host, _bind_err)
                self.host = "0.0.0.0"
                self._httpd = _QuietHTTPServer((self.host, self.port), handler_class)
            for _line in portal_banner(self.host, self.port):
                print(_line, flush=True)
            if ready_event is not None:
                ready_event.set()
            self._httpd.serve_forever()
        except Exception as e:
            print(f"{Colors.FAIL}[!] Gateway Failure: {e}{Colors.ENDC}", flush=True)
            if ready_event is not None:
                ready_event.set()

    def stop(self):
        if self._httpd:
            self._httpd.shutdown()
            self._httpd.server_close()
            self._httpd = None
