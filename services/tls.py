"""
TLS for the Akasha web portal — self-contained HTTPS, no external tooling.

Search engines will not crawl (and browsers reject) a site without a trusted
certificate, so HTTPS is a prerequisite for the archives being discoverable.
This module keeps the whole thing inside `python akasha.py` — no nginx, no
certbot invocation, OS-agnostic (Windows included) — in two layers:

  Layer A (here): terminate TLS in uvicorn from a cert/key on disk, and stand a
                  tiny port-80 responder that (1) answers ACME http-01 challenges
                  and (2) 301-redirects everything else to HTTPS. Works the moment
                  a cert exists, whoever obtained it.
  Layer B (acme.py): akasha-managed Let's Encrypt — obtain/renew the cert into the
                  path Layer A serves from, using the port-80 challenge responder.

Certificate resolution (first match wins):
  AKASHA_TLS_CERT / AKASHA_TLS_KEY   — explicit paths (env / secrets manager)
  <data>/tls/fullchain.pem + privkey.pem   — the akasha-managed default location

TLS is "active" only when both files exist and are readable; otherwise the portal
serves plain HTTP exactly as before (no regression on a local seeds cell).

Ports:
  AKASHA_HTTPS_PORT  (default 443)   — the TLS listener (uvicorn)
  the HTTP responder is always :80   — ACME challenge + HTTPS redirect
"""
import os
import ssl
import threading
import logging
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

logger = logging.getLogger("Harmonia.TLS")

_WELL_KNOWN = "/.well-known/acme-challenge/"


def tls_dir(data_dir: str) -> str:
    """The akasha-managed TLS directory (cert, key, ACME challenge tokens)."""
    return os.path.join(os.path.abspath(data_dir), "tls")


def challenge_dir(data_dir: str) -> str:
    d = os.path.join(tls_dir(data_dir), "acme-challenge")
    return d


def resolve_tls(data_dir: str) -> dict:
    """Resolve the TLS configuration for this cell.

    Returns a dict with keys:
      active     — bool, True iff a usable cert+key pair is present
      certfile   — resolved cert path (may not exist when inactive)
      keyfile    — resolved key path
      https_port — int, the TLS listener port (default 443)
      http_port  — int, the challenge/redirect responder port (80)
      challenge  — the ACME http-01 challenge directory (always created)
    """
    cert = os.environ.get("AKASHA_TLS_CERT", "").strip() \
        or os.path.join(tls_dir(data_dir), "fullchain.pem")
    key = os.environ.get("AKASHA_TLS_KEY", "").strip() \
        or os.path.join(tls_dir(data_dir), "privkey.pem")

    chal = challenge_dir(data_dir)
    try:
        os.makedirs(chal, exist_ok=True)
    except OSError:
        pass

    active = _readable(cert) and _readable(key)

    https_env = os.environ.get("AKASHA_HTTPS_PORT", "").strip()
    https_port = int(https_env) if https_env.isdigit() else 443

    return {
        "active":     active,
        "certfile":   cert,
        "keyfile":    key,
        "https_port": https_port,
        "http_port":  80,
        "challenge":  chal,
    }


def _readable(path: str) -> bool:
    try:
        return os.path.isfile(path) and os.access(path, os.R_OK)
    except OSError:
        return False


# ── Port-80 responder: ACME http-01 challenge + HTTPS redirect ────────────────

def make_http_responder_class(challenge_directory: str, https_port: int):
    """Build a request handler that serves ACME challenge tokens as plain text
    and 301-redirects every other GET/HEAD to the same host over HTTPS.

    Multi-domain aware: the redirect target is built from the request's own Host
    header, so world.<base> and akashickitchen.net each redirect to themselves.
    """
    _chal = os.path.abspath(challenge_directory)
    _hport = https_port

    class _Responder(BaseHTTPRequestHandler):
        server_version = "AkashaTLSRedirect/1.0"

        # Quiet by default — this runs in the detached portal process.
        def log_message(self, fmt, *args):
            logger.debug("[TLS:80] " + fmt, *args)

        def _acme_token_path(self, path: str):
            """Map /.well-known/acme-challenge/<token> to a file, traversal-safe."""
            if not path.startswith(_WELL_KNOWN):
                return None
            token = path[len(_WELL_KNOWN):]
            # A single safe segment only — no slashes, no traversal.
            if not token or "/" in token or "\\" in token or token in (".", ".."):
                return None
            candidate = os.path.realpath(os.path.join(_chal, token))
            if candidate != _chal and not candidate.startswith(_chal + os.sep):
                return None
            return candidate

        def _https_location(self) -> str:
            host = (self.headers.get("Host", "") or "").split(",")[0].strip()
            host = host.split(":", 1)[0]                    # drop any :port
            if not host:
                host = "localhost"
            suffix = "" if _hport == 443 else f":{_hport}"
            return f"https://{host}{suffix}{self.path}"

        def do_GET(self):
            token_file = self._acme_token_path(self.path)
            if token_file and os.path.isfile(token_file):
                try:
                    with open(token_file, "rb") as f:
                        body = f.read()
                except OSError:
                    self.send_error(404)
                    return
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            # Everything else → permanent redirect to HTTPS.
            self.send_response(301)
            self.send_header("Location", self._https_location())
            self.send_header("Content-Length", "0")
            self.end_headers()

        def do_HEAD(self):
            self.send_response(301)
            self.send_header("Location", self._https_location())
            self.send_header("Content-Length", "0")
            self.end_headers()

    return _Responder


def start_http_responder(challenge_directory: str, https_port: int,
                         host: str = "0.0.0.0", http_port: int = 80):
    """Start the port-80 ACME-challenge + HTTPS-redirect responder in a daemon
    thread. Returns the server (with .shutdown()) or None if the port can't be
    bound (e.g. not root) — HTTPS on 443 still works, only auto-redirect is lost.
    """
    handler = make_http_responder_class(challenge_directory, https_port)
    try:
        httpd = ThreadingHTTPServer((host, http_port), handler)
    except OSError as exc:
        logger.warning("[TLS] Port-%d responder not started (%s) — HTTPS still "
                       "serves, but there is no HTTP→HTTPS redirect.", http_port, exc)
        return None
    t = threading.Thread(target=httpd.serve_forever, daemon=True,
                         name="tls-http-responder")
    t.start()
    logger.info("[TLS] HTTP responder on :%d — ACME challenge + HTTPS redirect.",
                http_port)
    return httpd


def make_ssl_context(certfile: str, keyfile: str):
    """A server SSLContext for the given cert/key (used by the httpd portal;
    uvicorn takes the paths directly)."""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(certfile=certfile, keyfile=keyfile)
    return ctx
