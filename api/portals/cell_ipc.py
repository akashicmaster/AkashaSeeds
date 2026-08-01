"""
Local IPC transport — a Unix-domain-socket JSON-RPC listener carrying TRUST_LOCAL.

This is the "local door" of the Cell daemon (the persistent backend/engine process).
The daemon owns the one KernelDispatcher; a co-located client (the local CLI) attaches
over this socket and issues JSON-RPC exactly as the in-process console used to. Because
the client is a *separate process*, closing the CLI never touches the daemon's jobs.

Why TRUST_LOCAL is safe here (mirrors api/portals/stdio.py:_LocalGateway):
the socket file is created 0600 inside a 0700 dir, owned by the daemon's UID, so only a
process of the SAME UID can connect(). That same-user OS boundary is exactly what
TRUST_LOCAL already means for the stdio console (see kernel.py trust-level comments) —
here it is extended from "same process" to "same user on the same host". A network
client (TRUST_NETWORK) can never reach this socket, so it can never obtain local trust.

Where AF_UNIX is unavailable (some Windows builds) the server falls back to a loopback
TCP listener gated by a 0600 token file: only a same-UID process can read the token, so
the trust argument is preserved. Clients discover which via the `cell.endpoint` descriptor.

Framing: one compact JSON object per line, UTF-8, '\\n'-delimited. `json.dumps` escapes
any newline inside string values, so the newline is an unambiguous message boundary.

Stdlib only (socket + json) — no runtime dependency, portable to any Python 3.8+.
"""
import json
import logging
import os
import socket
import threading
from typing import Optional

logger = logging.getLogger("Akasha.CellIPC")

# Kept in sync with lib/akasha/kernel.py trust levels. Defined locally so the light
# client path never has to import the heavy kernel just to name a trust level.
TRUST_LOCAL = "local"
TRUST_NETWORK = "network"
TRUST_INTERNAL = "internal"

# Privilege ordering for the DOWNGRADE-ONLY rule. The local socket's OS perms grant a
# ceiling of TRUST_LOCAL; a request on it may only LOWER its own trust below that ceiling
# (e.g. a portal forwarding a network client's write asks to be treated as TRUST_NETWORK —
# a downgrade, always safe), NEVER raise it. An upgrade attempt is ignored. This is what
# lets the write-capable portal forward to the single primary writer without laundering a
# network request into local trust.
_TRUST_RANK = {TRUST_NETWORK: 1, TRUST_LOCAL: 2, TRUST_INTERNAL: 3}


def _effective_trust(ceiling: str, requested) -> str:
    if not isinstance(requested, str) or requested not in _TRUST_RANK:
        return ceiling
    return requested if _TRUST_RANK[requested] <= _TRUST_RANK.get(ceiling, 2) else ceiling

_SOCK_NAME = "cell.sock"
_ENDPOINT_NAME = "cell.endpoint"
_TOKEN_NAME = "cell.token"


# ── path helpers ───────────────────────────────────────────────────────────────

def _central_dir(base_dir: str) -> str:
    return os.path.join(base_dir, "central")


def sock_path(base_dir: str) -> str:
    return os.path.join(_central_dir(base_dir), _SOCK_NAME)


def endpoint_path(base_dir: str) -> str:
    return os.path.join(_central_dir(base_dir), _ENDPOINT_NAME)


def token_path(base_dir: str) -> str:
    return os.path.join(_central_dir(base_dir), _TOKEN_NAME)


def _has_af_unix() -> bool:
    return hasattr(socket, "AF_UNIX")


class _UnixPathTooLong(Exception):
    """The AF_UNIX socket path overflows sun_path — caller should fall back to TCP."""


# ── server (runs inside the Cell daemon) ────────────────────────────────────────

class CellIPCServer:
    """A stateless JSON-RPC listener bound to a local socket, dispatching every request
    to the daemon's gateway with TRUST_LOCAL. One connection == one client session; the
    accept loop and per-connection reader are daemon threads. Writes still serialise
    through the gateway's single WriteQueue — this server adds no writer and no lock on
    the write path (it only forwards)."""

    def __init__(self, gateway, base_dir: str, trust: str = TRUST_LOCAL):
        self._gw = gateway
        self._base_dir = base_dir
        self._trust = trust
        self._srv: Optional[socket.socket] = None
        self._kind = "unix"
        self._sock_file: Optional[str] = None      # actual bound AF_UNIX path (may be short)
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()

    # -- lifecycle --
    def start(self) -> dict:
        central = _central_dir(self._base_dir)
        os.makedirs(central, exist_ok=True)
        try:
            os.chmod(central, 0o700)
        except OSError:
            pass

        if _has_af_unix():
            try:
                descriptor = self._bind_unix()
            except _UnixPathTooLong:
                # A long data-dir path overflows AF_UNIX's ~108-byte sun_path. The
                # endpoint descriptor carries the real path, so the socket may live
                # anywhere — fall back to a short runtime path (still 0600), and to
                # TCP+token only if even that is unavailable.
                descriptor = self._bind_tcp()
        else:
            descriptor = self._bind_tcp()

        # Publish the endpoint descriptor LAST, so a client that sees it can connect.
        with open(endpoint_path(self._base_dir), "w", encoding="utf-8") as fh:
            json.dump(descriptor, fh)
        try:
            os.chmod(endpoint_path(self._base_dir), 0o600)
        except OSError:
            pass

        self._thread = threading.Thread(target=self._accept_loop, name="cell-ipc",
                                        daemon=True)
        self._thread.start()
        logger.info("[CellIPC] listening (%s): %s", self._kind, descriptor)
        return descriptor

    def _bind_unix(self) -> dict:
        path = self._unix_path()
        try:
            os.unlink(path)                       # clear a stale socket from a prior run
        except FileNotFoundError:
            pass
        except OSError:
            pass
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.bind(path)
        try:
            os.chmod(path, 0o600)                 # same-UID only — the trust boundary
        except OSError:
            pass
        s.listen(64)
        self._srv, self._kind, self._sock_file = s, "unix", path
        return {"kind": "unix", "path": path}

    def _unix_path(self) -> str:
        """The AF_UNIX socket path. Prefer the co-located one under the data dir; if that
        overflows sun_path (~108 bytes), use a short hashed name in a private runtime dir
        instead — the endpoint descriptor records whichever, so discovery is unaffected.
        Raises _UnixPathTooLong if no short-enough path can be formed (→ TCP fallback)."""
        _LIMIT = 100                              # safe margin under the 108-byte sun_path
        preferred = sock_path(self._base_dir)
        if len(preferred) <= _LIMIT:
            return preferred
        import hashlib
        tag = hashlib.sha1(os.path.abspath(self._base_dir).encode("utf-8")).hexdigest()[:10]
        runtime = os.environ.get("XDG_RUNTIME_DIR") or "/tmp"
        short = os.path.join(runtime, f"akasha-{tag}.sock")
        if len(short) <= _LIMIT:
            return short
        raise _UnixPathTooLong(preferred)

    def _bind_tcp(self) -> dict:
        # Fallback: loopback TCP gated by a 0600 token file (same-UID reads the token).
        import secrets
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("127.0.0.1", 0))
        s.listen(64)
        host, port = s.getsockname()
        token = secrets.token_hex(32)
        tpath = token_path(self._base_dir)
        with open(tpath, "w", encoding="utf-8") as fh:
            fh.write(token)
        try:
            os.chmod(tpath, 0o600)
        except OSError:
            pass
        self._srv, self._kind = s, "tcp"
        self._token = token
        return {"kind": "tcp", "host": host, "port": port, "token_file": tpath}

    def _accept_loop(self) -> None:
        while not self._stop.is_set():
            try:
                conn, _ = self._srv.accept()
            except OSError:
                break                              # socket closed on stop()
            threading.Thread(target=self._serve_conn, args=(conn,),
                            name="cell-ipc-conn", daemon=True).start()

    def _serve_conn(self, conn: socket.socket) -> None:
        with conn:
            f = conn.makefile("rwb")
            authed = (self._kind == "unix")       # UNIX: OS perms already authed the peer
            try:
                for raw in f:
                    line = raw.strip()
                    if not line:
                        continue
                    # TCP fallback: the first line must be the token handshake.
                    if not authed:
                        authed = (line.decode("utf-8", "replace") ==
                                getattr(self, "_token", None))
                        if not authed:
                            f.write(b'{"jsonrpc":"2.0","error":{"code":-32001,'
                                    b'"message":"local token required"},"id":null}\n')
                            f.flush()
                            return
                        continue
                    self._handle_line(line, f)
            except (OSError, ValueError):
                return

    def _handle_line(self, line: bytes, f) -> None:
        try:
            payload = json.loads(line)
        except (ValueError, UnicodeDecodeError):
            f.write(b'{"jsonrpc":"2.0","error":{"code":-32700,'
                    b'"message":"parse error"},"id":null}\n')
            f.flush()
            return
        rid = payload.get("id") if isinstance(payload, dict) else None
        # Honor a DOWNGRADE-ONLY trust hint (a forwarding portal marks a network-originated
        # request `_trust:"network"`). The socket's ceiling (self._trust) can never be raised;
        # the hint is stripped before the payload reaches the kernel.
        trust = self._trust
        if isinstance(payload, dict) and "_trust" in payload:
            trust = _effective_trust(self._trust, payload.pop("_trust"))
        try:
            resp = self._gw.dispatch(payload, trust)
        except Exception as exc:                   # a dispatch bug must not kill the loop
            logger.exception("[CellIPC] dispatch error")
            resp = {"jsonrpc": "2.0",
                    "error": {"code": -32603, "message": f"internal error: {exc}"},
                    "id": rid}
        f.write((json.dumps(resp, ensure_ascii=False) + "\n").encode("utf-8"))
        f.flush()

    def stop(self) -> None:
        self._stop.set()
        try:
            if self._srv is not None:
                self._srv.close()
        except OSError:
            pass
        # Remove the actual bound socket (may be a short runtime path), the default
        # co-located socket, the endpoint descriptor, and any TCP token.
        for p in (self._sock_file, sock_path(self._base_dir),
                  endpoint_path(self._base_dir), token_path(self._base_dir)):
            if not p:
                continue
            try:
                os.unlink(p)
            except FileNotFoundError:
                pass
            except OSError:
                pass


# ── client (used by the local CLI) ──────────────────────────────────────────────

def daemon_endpoint(base_dir: str) -> Optional[dict]:
    """Return the published endpoint descriptor, or None if no daemon has advertised one."""
    try:
        with open(endpoint_path(base_dir), "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (FileNotFoundError, ValueError, OSError):
        return None


class SocketGateway:
    """Client-side stand-in for AkashaGateway: exposes `.dispatch(payload)` by tunnelling
    the payload over the Cell daemon's local socket. Drop-in for `run_cli` / `run_single_shot`
    (stdio.py touches the gateway ONLY through `.dispatch`), so the CLI is unaware it is
    talking to a separate process. The daemon stamps the real transport_trust server-side;
    the `transport_trust` arg here is accepted and ignored."""

    def __init__(self, base_dir: str, timeout: float = 60.0):
        self._base_dir = base_dir
        self._timeout = timeout
        self._sock: Optional[socket.socket] = None
        self._f = None
        self._lock = threading.Lock()

    # -- connection --
    def connect(self) -> None:
        desc = daemon_endpoint(self._base_dir)
        if not desc:
            raise ConnectionError("no Cell daemon endpoint published")
        if desc.get("kind") == "unix":
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.settimeout(self._timeout)
            s.connect(desc["path"])
            self._sock, self._f = s, s.makefile("rwb")
        elif desc.get("kind") == "tcp":
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(self._timeout)
            s.connect((desc["host"], desc["port"]))
            f = s.makefile("rwb")
            with open(desc["token_file"], "r", encoding="utf-8") as th:
                token = th.read().strip()
            f.write((token + "\n").encode("utf-8"))
            f.flush()
            self._sock, self._f = s, f
        else:
            raise ConnectionError(f"unknown endpoint kind: {desc.get('kind')}")

    def close(self) -> None:
        try:
            if self._f is not None:
                self._f.close()
        except OSError:
            pass
        try:
            if self._sock is not None:
                self._sock.close()
        except OSError:
            pass
        self._sock, self._f = None, None

    # -- the one method stdio.py needs --
    def dispatch(self, payload: dict, transport_trust: str = TRUST_LOCAL) -> dict:
        rid = payload.get("id") if isinstance(payload, dict) else None
        # Transmit the trust as a DOWNGRADE-ONLY hint (server clamps to its socket ceiling).
        # A forwarding portal passes TRUST_NETWORK; the console CLI passes TRUST_LOCAL (no-op).
        wire = payload
        if isinstance(payload, dict) and transport_trust and transport_trust != TRUST_LOCAL:
            wire = dict(payload)
            wire["_trust"] = transport_trust
        with self._lock:
            try:
                if self._f is None:
                    self.connect()
                self._f.write((json.dumps(wire, ensure_ascii=False) + "\n")
                            .encode("utf-8"))
                self._f.flush()
                raw = self._f.readline()
                if not raw:
                    raise ConnectionError("daemon closed the connection")
                return json.loads(raw)
            except (OSError, ValueError, ConnectionError) as exc:
                self.close()
                return {"jsonrpc": "2.0",
                        "error": {"code": -32000, "message": f"Cell daemon unreachable: {exc}"},
                        "id": rid}


def ping(base_dir: str, timeout: float = 3.0) -> bool:
    """True if a Cell daemon answers sys.ping on its local socket."""
    gw = SocketGateway(base_dir, timeout=timeout)
    try:
        resp = gw.dispatch({"jsonrpc": "2.0", "method": "sys.ping", "params": {}, "id": "ping"})
        return isinstance(resp, dict) and "error" not in resp
    finally:
        gw.close()


def ping_build(base_dir: str, timeout: float = 3.0):
    """The running daemon's code fingerprint (sys.ping → result.build), or None if the daemon
    is unreachable or too old to report one. The launcher compares it to the on-disk code so a
    re-extracted/updated build REPLACES a stale daemon instead of attaching to it."""
    gw = SocketGateway(base_dir, timeout=timeout)
    try:
        resp = gw.dispatch({"jsonrpc": "2.0", "method": "sys.ping", "params": {}, "id": "pingv"})
        if isinstance(resp, dict) and "error" not in resp:
            return (resp.get("result") or {}).get("build") or None
        return None
    except Exception:
        return None
    finally:
        gw.close()


# ── SplitGateway — single-writer-preserving portal gateway (approach A) ──────────
#
# The web portal runs as a serve-only SUBPROCESS with its OWN engine. Letting it execute
# WRITE RPCs there makes it a SECOND writer against the one nucleus (a single-writer-model
# violation). SplitGateway fixes that: it serves READS from the portal's local engine
# (WAL-concurrent, fast) and FORWARDS everything that could mutate — writes, auth, session,
# and any unclassified method — to the ONE primary writer over the local socket, preserving
# the caller's network trust (downgrade-only), so a guest still cannot write and only an
# authenticated WRITE-capable client can. Fail-closed: if no primary writer is reachable, a
# would-be write is REFUSED, never executed locally.

# Actions safe to serve from the portal's own read engine. Everything else forwards.
_LOCAL_READ_ACTIONS = frozenset({
    "read", "explore", "dive.look", "dive.out", "network.tree",
    "link.list", "sys.history", "status", "svc.read",
    # Guest sessions are a READ-SIDE concern: session.guest.create/extend claim a slot in
    # the portal's OWN guest pool and mint a self-verifying token — no nucleus write. With
    # the daemon's signing secret shared into the portal's env, the portal mints AND verifies
    # locally, so an anonymous read-only front (the archives) needs no primary writer at all.
    # Forwarding these made every guest fail with "write path unavailable" whenever the writer
    # was busy/absent. A guest still cannot write: any real write action is not in this set,
    # so it still forwards and is denied as a guest.
    "session.guest",
})

# Pre-auth methods with no METHOD_TO_ACTION entry that are pure reads / stateless handshake —
# served locally so the portal answers them without a round-trip (and without a writer).
_LOCAL_PREAUTH_METHODS = frozenset({
    "sys.ping", "sys.status", "kernel.auth.status", "auth.status",
})


class SplitGateway:
    """reads → local engine; writes/auth/session/unknown → the single primary writer (IPC)."""

    def __init__(self, local_gw, base_dir: str):
        self._local = local_gw
        self._base_dir = base_dir
        self._remote: Optional["SocketGateway"] = None
        try:
            from lib.akasha.kernel_methods import METHOD_TO_ACTION as _m
            self._m2a = _m
        except Exception:
            self._m2a = {}

    def _remote_gw(self) -> Optional["SocketGateway"]:
        if self._remote is None and ping(self._base_dir):
            self._remote = SocketGateway(self._base_dir)
        return self._remote

    def dispatch(self, payload: dict, transport_trust: str = TRUST_NETWORK) -> dict:
        method = payload.get("method", "") if isinstance(payload, dict) else ""
        rid = payload.get("id") if isinstance(payload, dict) else None
        act = self._m2a.get(method)
        if method == "sys.ping":
            # Served locally (constant-time, no writer round-trip) — but a read-only portal that
            # OUTLIVED a dead Cell daemon still answers kernel_online, so external monitoring can't
            # see that the WRITE PATH is down. Stamp writer_online from the daemon liveness probe
            # (same one _remote_gw uses) so a monitor gets kernel_online:true + writer_online:false
            # when the site still serves reads but the writer is gone. Best-effort; never fails ping.
            resp = self._local.dispatch(payload, transport_trust)
            try:
                if isinstance(resp, dict) and isinstance(resp.get("result"), dict):
                    resp["result"]["writer_online"] = bool(ping(self._base_dir))
            except Exception:
                pass
            return resp
        if method in _LOCAL_PREAUTH_METHODS or act in _LOCAL_READ_ACTIONS:
            return self._local.dispatch(payload, transport_trust)
        # Anything that could mutate (or that we can't classify) goes to the one writer,
        # carrying the portal's network trust so the primary authorizes it normally.
        rg = self._remote_gw()
        if rg is None:
            return {"jsonrpc": "2.0", "id": rid,
                    "error": {"code": -32000,
                              "message": "write path unavailable: the primary writer is not "
                                         "reachable — the portal serves reads only until it is up."}}
        return rg.dispatch(payload, transport_trust)

    # A few gateways expose helpers beyond .dispatch; proxy the common ones to the local
    # read engine so the portal keeps working (they are read-only).
    def __getattr__(self, name):
        return getattr(self._local, name)
