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
import stat as _stat
import json
import urllib.parse
import socket
import logging
import traceback
from http.server import HTTPServer, SimpleHTTPRequestHandler
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

class BaseWebHandler(SimpleHTTPRequestHandler):
    """
    HTTP Request Handler.
    Routes incoming traffic to static assets or the Akasha RPC gateway.
    """
    routes: Dict[str, Dict[str, Any]] = {}
    gw = None  # injected by BaseWebService.start() via dynamic subclass
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "static"))

    def __init__(self, *args, **kwargs):
        # Allow dynamic subclass to override static_dir via class attribute
        super().__init__(*args, directory=self.static_dir, **kwargs)

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

        if path == '/api/rpc':
            self._handle_rpc()
        elif path in self.routes and self.routes[path]['method'] == 'POST':
            self._execute_custom_handler(self.routes[path]['handler'])
        else:
            self._send_json({"error": "Endpoint not found."}, status=404)

    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        if path == '/api/readme':
            self._serve_readme()
        elif path in self.routes and self.routes[path]['method'] == 'GET':
            self._execute_custom_handler(self.routes[path]['handler'])
        else:
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

    def translate_path(self, path):
        """
        Override to serve <static>/<name>/index.html directly for /<name> and /<name>/
        requests, avoiding the 301 redirect that SimpleHTTPRequestHandler normally issues
        for directory paths (the redirect breaks Codespace port-forwarding proxies).
        """
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
            
            gw = self.gw or _gw_module.gateway
            res = gw.dispatch(req)
            self._send_json(res)
            
        except json.JSONDecodeError:
            self._send_json({"jsonrpc": "2.0", "error": {"code": -32700, "message": "Invalid JSON"}, "id": None})
        except Exception as e:
            logger.error(f"[RPC Failure] {traceback.format_exc()}")
            self._send_json({"jsonrpc": "2.0", "error": {"code": -32603, "message": str(e)}, "id": None})

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

    def _send_json(self, data: Any, status: int = 200):
        self.send_response(status)
        self._send_cors_headers()
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def log_message(self, format: str, *args):
        logger.debug(f"[HTTP] {format % args}")

class BaseWebService:
    """Manager for the HTTP Server lifecycle."""
    def __init__(self, gw=None, port: int = 8080, host: str = '0.0.0.0', static_dir: str = None):
        self.gw           = gw
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

    def start(self):
        self.port = self._find_free_port()
        attrs = {
            'routes': self.routes,
            'gw':     self.gw or _gw_module.gateway,
        }
        if self._static_dir:
            attrs['static_dir'] = os.path.abspath(self._static_dir)
        handler_class = type('DynamicWebHandler', (BaseWebHandler,), attrs)
        try:
            self._httpd = HTTPServer((self.host, self.port), handler_class)
            print(f"{Colors.GREEN}[+] Gateway Online: http://{self.host}:{self.port}/{Colors.ENDC}")
            self._httpd.serve_forever()
        except Exception as e:
            print(f"{Colors.FAIL}[!] Gateway Failure: {e}{Colors.ENDC}")

    def stop(self):
        if self._httpd:
            self._httpd.shutdown()
            self._httpd.server_close()
            self._httpd = None
