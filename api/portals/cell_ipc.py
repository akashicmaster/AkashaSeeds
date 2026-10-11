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
import hashlib
import hmac
import json
import logging
import os
import queue
import socket
import threading
import time
from typing import Optional

logger = logging.getLogger("Akasha.CellIPC")

# F47-3.1 — the daemon's health heartbeat (lib/akasha/kernel.py) reads the live IPC pool stats
# through this module-level pointer, so the per-minute line can show pool saturation / refusals
# without the kernel holding a reference to the server object.
_CURRENT_SERVER = {"srv": None}


def server_stats() -> dict:
    """The running CellIPCServer's pool stats, or {} if none is listening in this process."""
    srv = _CURRENT_SERVER["srv"]
    try:
        return srv.stats() if srv is not None else {}
    except Exception:
        return {}


def inflight_stats() -> dict:
    """A56 §3 — the IPC requests IN FLIGHT right now: {count, slowest, oldest_age}. So a `[maint] Δrss`
    line can name the concurrent IPC work (a 100 s `semantic.search`) that its RSS delta was silently
    blaming on the maintenance task. Constant-time (reads the pool's in-flight map). {} if no server."""
    srv = _CURRENT_SERVER["srv"]
    if srv is None:
        return {}
    try:
        now = time.time()
        with srv._inflight_lock:
            items = list(srv._inflight.values())
        if not items:
            return {"count": 0, "slowest": None, "oldest_age": 0.0}
        slow = max(items, key=lambda mt: now - mt[1])
        return {"count": len(items), "slowest": slow[0], "oldest_age": round(now - slow[1], 1)}
    except Exception:
        return {}

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


# ── F16 — signed trust ELEVATION for the analytics writer over the local socket ──────
#
# The DOWNGRADE-ONLY rule above is correct for arbitrary local processes, but it structurally
# kills the split-topology pulse capture: PulseRecorder emits as `system.librarian` asking for
# `internal`, the socket clamps it to `local`, and the kernel then rejects the system identity
# (-32001). The narrow, safe exception: a request may be RAISED to `internal` iff it carries a
# valid HMAC signature over (method, params, ts) with the deployment's shared AKASHA_SECRET, the
# ts is fresh (±_ELEVATION_SKEW_S, replay-bounded), and the method is on a tiny allowlist. A
# same-UID process without the secret still cannot elevate (it clamps exactly as before), and the
# blast radius is analytics-only even if the secret leaked. The secret is the SAME one the daemon
# already shares into the portal's env (akasha.py — "shared the session-signing secret").
_INTERNAL_ELEVATION_METHODS = frozenset({"pulse.emit", "pulse.emit_bulk", "pulse.compact"})
_ELEVATION_SKEW_S = 60.0


# F48-2.1 — the elevation secret must be IDENTICAL in the signer (portal) and verifier (daemon), or
# every F16 pulse.emit is clamped to local and rejected (-32001) — the silent capture loss the Health
# line confirmed (seen>0 emit=0 rej>0). Guest TOKENS survived this because they are minted AND
# verified within one process (self-consistent even if the two processes' secrets differ), so a
# working site does NOT prove the elevation secret is shared. AKASHA_SECRET env is the primary
# channel, but env propagation depends on spawn ordering; as a robust fallback the daemon also writes
# the resolved secret to a 0600 file under the shared base_dir, and both sign/verify read it when env
# is absent. Env-first keeps the working path byte-identical; the file only RECOVERS a missing env.
_ELEVATION_BASE = {"dir": None}       # base_dir registered by whoever knows it (CellIPCServer / recorder)


def register_elevation_base(base_dir: str) -> None:
    if base_dir:
        _ELEVATION_BASE["dir"] = base_dir


def elevation_secret_path(base_dir: str) -> str:
    return os.path.join(_central_dir(base_dir), "elevation.secret")


def write_elevation_secret(base_dir: str, secret_hex: str) -> None:
    """Daemon-side: persist the resolved elevation secret (hex) to a 0600 file so a portal subprocess
    that did NOT inherit AKASHA_SECRET can still sign emits the daemon will verify. Best-effort."""
    if not (base_dir and secret_hex):
        return
    try:
        p = elevation_secret_path(base_dir)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(secret_hex)
        try:
            os.chmod(p, 0o600)
        except OSError:
            pass
        register_elevation_base(base_dir)
    except OSError:
        pass


def _elevation_secret() -> Optional[bytes]:
    s = os.environ.get("AKASHA_SECRET")
    if not s:
        # Env absent (propagation/ordering gap) → fall back to the shared 0600 secret file, so the
        # signer and verifier still resolve the SAME key across the process split.
        _base = _ELEVATION_BASE["dir"]
        if _base:
            try:
                with open(elevation_secret_path(_base), "r", encoding="utf-8") as fh:
                    s = fh.read().strip()
            except OSError:
                s = None
    if not s:
        return None
    try:
        return bytes.fromhex(s)                       # the daemon exports/persists it as .hex()
    except ValueError:
        return s.encode("utf-8")                      # operator-set raw string → use as-is


def _elevation_canonical(method, params, ts) -> bytes:
    """Deterministic bytes bound by the signature — method + params + ts, so a captured sig
    cannot be replayed for a different method/content/time."""
    return json.dumps({"m": method, "p": params, "t": ts},
                      sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def sign_internal(method, params, ts) -> Optional[str]:
    """Client side: HMAC-SHA256 over the canonical (method, params, ts), or None if no secret is
    available (embedded topology needs no elevation — the dispatch stays in-process)."""
    sec = _elevation_secret()
    if not sec:
        return None
    return hmac.new(sec, _elevation_canonical(method, params, ts), hashlib.sha256).hexdigest()


def verify_internal(method, params, ts, sig) -> bool:
    """Server side: grant `internal` only for an allowlisted method with a fresh, valid signature."""
    if method not in _INTERNAL_ELEVATION_METHODS or not sig:
        return False
    sec = _elevation_secret()
    if not sec:
        return False
    try:
        if abs(time.time() - float(ts)) > _ELEVATION_SKEW_S:
            return False
    except (TypeError, ValueError):
        return False
    expected = hmac.new(sec, _elevation_canonical(method, params, ts), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, str(sig))

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
        # F47-1.1 — a FIXED worker pool drains a BOUNDED accept queue, replacing the old
        # thread-per-connection (unbounded → a bot storm holding tens of connections stacked
        # tens of GIL-contending render threads: 3 concurrent renders were already SLOWER than
        # serial, and the stacked in-flight state was the leading RSS-climb suspect). Now the
        # daemon's thread census is constant by construction; overflow is refused fast (one JSON
        # busy line) instead of spawning another thread. Tunables: AKASHA_IPC_WORKERS (6),
        # AKASHA_IPC_QUEUE (32).
        def _envint(name, default):
            try:
                return max(1, int((os.environ.get(name, "") or "").strip() or default))
            except (TypeError, ValueError):
                return default
        self._pool_size = _envint("AKASHA_IPC_WORKERS", 6)
        self._queue_max = _envint("AKASHA_IPC_QUEUE", 32)
        self._connq: "Optional[queue.Queue]" = None
        self._workers = []
        self._refused = 0                          # process-lifetime overflow refusals (health line)
        self._served = 0                           # connections handed to a worker
        # A53 item 5 — saturation observability. Track when the accept queue first went non-empty
        # and what each worker is CURRENTLY dispatching, so a backlog that PERSISTS (>10 s) can be
        # reported with the slowest in-flight method — the datum that tells "busy, not wedged" from
        # a genuinely stuck writer. Throttled to one WARNING / 60 s so a sustained storm is one line.
        self._q_since = 0.0
        self._last_sat_warn = 0.0
        self._sat_warned = False                   # A55 — did we warn about the current backlog?
        self._inflight = {}                        # conn-key → (method, start_ts)
        self._inflight_lock = threading.Lock()
        self._sat_thread = None

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

        # Start the fixed worker pool BEFORE the accept loop, so a connection accepted on the very
        # first tick already has a drainer waiting.
        self._connq = queue.Queue(maxsize=self._queue_max)
        self._workers = []
        for _i in range(self._pool_size):
            _w = threading.Thread(target=self._worker_loop, name="cell-ipc-w%d" % _i, daemon=True)
            _w.start()
            self._workers.append(_w)

        # F48-2.1 — make the elevation secret reachable across the process split: register this
        # base_dir and, if the secret is already in env, persist it to the shared 0600 file so a
        # portal subprocess that missed AKASHA_SECRET can still sign verifiable emits.
        register_elevation_base(self._base_dir)
        _env_sec = os.environ.get("AKASHA_SECRET")
        if _env_sec:
            write_elevation_secret(self._base_dir, _env_sec)

        self._thread = threading.Thread(target=self._accept_loop, name="cell-ipc",
                                        daemon=True)
        self._thread.start()
        # A55 — a 1 Hz saturation sampler OFF the accept path. The accept-loop probe (A53) fired
        # right after put_nowait, where the queue is non-empty by construction, so a single steady
        # q=1 read 10 s later warned every minute — noise that would hide a real storm. Sample once
        # a second, reset on ANY empty read, and warn only on a SUSTAINED (>10 s) backlog that is
        # actually deep (q≥2) or slow (oldest_wait≥5 s); log a `drained` line on recovery.
        self._sat_thread = threading.Thread(target=self._saturation_sampler,
                                            name="cell-ipc-sat", daemon=True)
        self._sat_thread.start()
        _CURRENT_SERVER["srv"] = self              # expose pool stats to the health heartbeat
        logger.info("[CellIPC] listening (%s): %s  [pool=%d queue=%d]",
                    self._kind, descriptor, self._pool_size, self._queue_max)
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
            try:
                self._connq.put_nowait(conn)       # hand off to a pooled worker
                self._served += 1
            except queue.Full:
                # The pool + queue are saturated — the daemon's scarce internal resource is spent.
                # Refuse FAST (one JSON busy line, then close) instead of spawning another thread;
                # the portal maps -32029 to 503/Retry-After for bots and an auto-retry for humans.
                self._refused += 1
                self._reject_busy(conn)

    def _worker_loop(self) -> None:
        """One of the fixed pool. Blocks on the connection queue, serves one connection to
        completion (the portal opens a fresh short-lived connection per request, so turnover is
        fast), then returns to the pool. A poison-pill None (from stop()) ends the worker."""
        while not self._stop.is_set():
            try:
                conn = self._connq.get(timeout=0.5)
            except queue.Empty:
                continue
            if conn is None:                       # poison pill
                return
            try:
                self._serve_conn(conn)
            except Exception:                      # a serve bug must never kill a pool worker
                logger.exception("[CellIPC] worker error")

    def _reject_busy(self, conn) -> None:
        """Accept-queue overflow → write ONE JSON-RPC busy line (-32029 + retry_after_ms) and close.
        No request has been read yet, so id is null. Bounded, allocation-free, always closes."""
        try:
            conn.sendall(b'{"jsonrpc":"2.0","error":{"code":-32029,'
                         b'"message":"Server busy: daemon connection pool saturated",'
                         b'"data":{"retry_after_ms":500}},"id":null}\n')
        except OSError:
            pass
        finally:
            try:
                conn.close()
            except OSError:
                pass

    def _saturation_sampler(self) -> None:
        """A55 — sample the accept-queue depth once a second, OFF the accept path. A backlog only
        counts when it is SUSTAINED (>10 s) AND materially bad — deep (q≥2) or slow (the oldest
        in-flight request has run ≥5 s); a single steady q=1 (one connection being served, the
        normal case) never warns. Any empty sample resets the timer, and a recovery after a warning
        logs a `drained` line so the storm has a clear end. One WARNING / 60 s while it holds."""
        while not self._stop.wait(1.0):
            self._saturation_tick()

    def _saturation_tick(self, now: float = None) -> None:
        """One saturation sample (extracted so it is unit-testable — A55). Warns only on a
        SUSTAINED + material backlog; resets on empty; logs `drained` on recovery. Never raises."""
        try:
            now = time.time() if now is None else now
            q = self._connq
            depth = q.qsize() if q is not None else 0
            if depth <= 0:
                if self._sat_warned:
                    _for = now - self._q_since if self._q_since else 0.0
                    logger.warning("[ipc] drained pool=%d after=%.0fs", self._pool_size, _for)
                    self._sat_warned = False
                self._q_since = 0.0
                return
            if self._q_since == 0.0:
                self._q_since = now
                return
            with self._inflight_lock:
                items = list(self._inflight.values())
            oldest = max((now - t for _, t in items), default=0.0)
            sustained = (now - self._q_since) > 10.0
            material = depth >= 2 or oldest >= 5.0
            if sustained and material and (now - self._last_sat_warn) > 60.0:
                self._last_sat_warn = now
                self._sat_warned = True
                slowest = max(items, key=lambda mt: now - mt[1])[0] if items else "?"
                logger.warning("[ipc] pool saturated pool=%d q=%d oldest_wait=%.1fs slowest=%s",
                               self._pool_size, depth, oldest, slowest)
        except Exception:
            pass

    def stats(self) -> dict:
        """Pool health for the daemon's per-minute log line (F47-3.1)."""
        q = self._connq
        return {"pool": self._pool_size, "queue_max": self._queue_max,
                "q": (q.qsize() if q is not None else 0),
                "queued": (q.qsize() if q is not None else 0),
                "served": self._served, "refused": self._refused,
                "workers": len(self._workers)}

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
        # request `_trust:"network"`). The socket's ceiling (self._trust) can never be raised —
        # EXCEPT the F16 signed analytics elevation: an allowlisted method (pulse.emit/compact)
        # with a valid, fresh HMAC over (method, params, ts) may be RAISED to `internal`. All
        # trust-hint / signature keys are stripped before the payload reaches the kernel.
        trust = self._trust
        if isinstance(payload, dict) and "_trust" in payload:
            requested = payload.pop("_trust")
            sig = payload.pop("_sig", None)
            ts = payload.pop("_ts", None)
            if (requested == TRUST_INTERNAL
                    and _TRUST_RANK.get(requested, 0) > _TRUST_RANK.get(self._trust, 2)
                    and verify_internal(payload.get("method"), payload.get("params"), ts, sig)):
                trust = TRUST_INTERNAL                # signed analytics-writer elevation (F16)
            else:
                trust = _effective_trust(self._trust, requested)   # forged/absent sig → clamp
        elif isinstance(payload, dict):
            payload.pop("_sig", None)                 # strip stray signing keys if any
            payload.pop("_ts", None)
        _mid = (payload.get("method") if isinstance(payload, dict) else None) or "?"
        _ik = id(f)
        with self._inflight_lock:                  # A53 item 5 — track the in-flight method + start
            self._inflight[_ik] = (_mid, time.time())
        try:
            resp = self._gw.dispatch(payload, trust)
        except Exception as exc:                   # a dispatch bug must not kill the loop
            logger.exception("[CellIPC] dispatch error")
            resp = {"jsonrpc": "2.0",
                    "error": {"code": -32603, "message": f"internal error: {exc}"},
                    "id": rid}
        finally:
            with self._inflight_lock:
                self._inflight.pop(_ik, None)
        f.write((json.dumps(resp, ensure_ascii=False) + "\n").encode("utf-8"))
        f.flush()

    def stop(self) -> None:
        self._stop.set()
        try:
            if self._srv is not None:
                self._srv.close()
        except OSError:
            pass
        # Poison the pool so idle workers waiting on the queue exit promptly, and close any
        # connections still queued but not yet picked up (no leaked FDs on shutdown).
        if self._connq is not None:
            while True:
                try:
                    _c = self._connq.get_nowait()
                except queue.Empty:
                    break
                if _c is not None:
                    try:
                        _c.close()
                    except OSError:
                        pass
            for _ in self._workers:
                try:
                    self._connq.put_nowait(None)
                except queue.Full:
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
            except socket.timeout:
                # F27-4 — a timeout is NOT the same failure as a dead socket: the daemon is up but
                # did not answer within our read window (heavy I/O). Say so, so the operator does
                # not chase a "daemon gone" ghost when it is merely slow. (socket.timeout is an
                # OSError subclass, so this must be caught BEFORE the OSError arm below.)
                self.close()
                return {"jsonrpc": "2.0",
                        "error": {"code": -32000,
                                  "message": (f"Cell daemon is busy — no reply within "
                                              f"{self._timeout:.0f}s (it is still running; retry or "
                                              f"check `svc.ls`)")},
                        "id": rid}
            except (OSError, ValueError, ConnectionError) as exc:
                # A daemon whose pool is saturated answers a new connection with ONE busy line
                # (-32029) and closes it at once. A client still sending its request then fails the
                # send (`Broken pipe`) — but the busy line is already in its receive buffer. Read it
                # before calling the daemon unreachable: "busy, retry" and "gone" are different
                # answers, and the portal treats them differently (503/Retry-After vs a revive).
                # (Directive 2026-10-03 §6: `ipc_pool_eval` failed under load on exactly this.)
                said = self._read_refusal()
                self.close()
                if said is not None:
                    said["id"] = rid
                    return said
                return {"jsonrpc": "2.0",
                        "error": {"code": -32000, "message": f"Cell daemon unreachable: {exc}"},
                        "id": rid}

    def _read_refusal(self):
        """The one JSON-RPC error line the daemon wrote before closing, if there is one — else None.
        Bounded (one recv, 1 s); only an error line is returned, never a result."""
        sock = self._sock
        if sock is None:
            return None
        try:
            sock.settimeout(1.0)
            data = sock.recv(4096)
        except OSError:
            return None
        line = (data or b"").split(b"\n", 1)[0].strip()
        if not line:
            return None
        try:
            msg = json.loads(line)
        except ValueError:
            return None
        return msg if isinstance(msg, dict) and isinstance(msg.get("error"), dict) else None


def ping(base_dir: str, timeout: float = 3.0) -> bool:
    """True if a Cell daemon answers sys.ping on its local socket."""
    gw = SocketGateway(base_dir, timeout=timeout)
    try:
        resp = gw.dispatch({"jsonrpc": "2.0", "method": "sys.ping", "params": {}, "id": "ping"})
        return isinstance(resp, dict) and "error" not in resp
    finally:
        gw.close()


def ping_build(base_dir: str, timeout: float = 3.0):
    """Tri-state probe of the running daemon (F60 §4.1). Returns a (status, build) tuple:
      ("ok", <build>)     — answered sys.ping WITH a code fingerprint;
      ("no-build", None)  — answered but reported no build (pre-handshake / too old);
      ("silent", None)    — no answer at all (timeout, refused, socket error).
    The launcher REPLACES on `ok`-with-a-different-build and on `no-build` (a pre-handshake daemon is
    strictly older); on `silent` it does NOT replace — a busy/slow daemon must not be evicted on one
    missed ping, so it waits heartbeat-gated and leaves the verdict to the watchdog's advancing probe.
    (Was: the running build string or None — which conflated 'answered, no build' with 'no answer',
    so a merely-slow daemon that timed out the probe was replaced like a stale one.)"""
    gw = SocketGateway(base_dir, timeout=timeout)
    try:
        resp = gw.dispatch({"jsonrpc": "2.0", "method": "sys.ping", "params": {}, "id": "pingv"})
        if isinstance(resp, dict) and "error" not in resp:
            b = (resp.get("result") or {}).get("build") or None
            return ("ok", b) if b else ("no-build", None)
        return ("silent", None)                          # error response = not a usable answer
    except Exception:
        return ("silent", None)                          # timeout / refused / socket error
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
#
# ONE ACTION, because there is one read action. This named nine — `read`, `explore`, `dive.look`,
# `dive.out`, `network.tree`, `link.list`, `sys.history`, `status`, `svc.read` — and after the
# one-gate remap every one of them IS `read`, so eight were dead names. A list of action tokens in
# a second file is the same hazard `_WRITE_ACTIONS` was: it keeps matching just enough to look
# alive while the vocabulary moves out from under it.
_LOCAL_READ_ACTIONS = frozenset({"read"})

# Pre-auth methods with no METHOD_TO_ACTION entry that are pure reads / stateless handshake —
# served locally so the portal answers them without a round-trip (and without a writer).
#
# `session.guest.*` belongs HERE, not above: it is pre-auth and carries no action entry at all, so
# classifying it by action routed it to the writer. Guest sessions are a READ-SIDE concern — they
# claim a slot in the portal's OWN pool and mint a self-verifying token, no nucleus write — and
# with the daemon's signing secret in the portal's env the portal mints AND verifies locally, so
# an anonymous read-only front (the archives) needs no primary writer at all. Forwarding them made
# every guest fail with "write path unavailable" whenever the writer was busy or absent; that
# outage was fixed once already, and the remap reintroduced it by emptying the name it hung on.
# A guest still cannot write: a real write action is not served locally, so it forwards and is
# denied there as a guest.
_LOCAL_PREAUTH_METHODS = frozenset({
    "sys.ping", "sys.status", "kernel.auth.status", "auth.status",
    "session.guest.create", "session.guest.extend",
})

# Guest-facing reads whose data is RUNTIME state produced by the WRITER (the public broadcast
# mirror + station lineup, written by system.broadcaster / the relay; the live-telemetry feed
# surface, written by the poller). Even though these classify as "read", the serve-only portal's
# LOCAL engine does not run the broadcaster/poller and does not reflect the writer's live nucleus
# writes — so serving them locally returns an EMPTY view while the writer holds the data. FORWARD
# them to the one writer (the authoritative source), exactly like feed.* already forwards by being
# unclassified. This is what makes the public archives station page show the live broadcast.
# (Regression: the public feed reads returned empty payloads on the public portal
# while the daemon's own read had them — the station page sat on STANDING BY forever.)
_FORWARD_READ_METHODS = frozenset({
    "society.feed.read", "society.broadcast.live", "society.broadcast", "society.feed",
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
        if method not in _FORWARD_READ_METHODS and (
                method in _LOCAL_PREAUTH_METHODS or act in _LOCAL_READ_ACTIONS):
            return self._local.dispatch(payload, transport_trust)
        # Anything that could mutate (or that we can't classify), and the runtime-writer reads in
        # _FORWARD_READ_METHODS, go to the one writer,
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


# ─────────────────────────────────────────────────────────────────────────────
# Thin portal gateway — the memory-frugal serve-only portal (holds NO index).
# ─────────────────────────────────────────────────────────────────────────────
class _ThinIAM:
    """Minimal IAM stand-in for ThinPortalGateway. The portal's ONE local IAM use is
    the restricted-prefix gate (resolve a token → which client, which role?). The thin portal
    holds no engine, so it forwards that resolution to the daemon's authoritative IAM
    via auth.whoami (the daemon does the real epoch/active checks)."""

    def __init__(self, base_dir: str):
        self._base_dir = base_dir

    def resolve_session_token(self, token: str):
        from lib.akasha.identity import Role
        sg = SocketGateway(self._base_dir)
        try:
            resp = sg.dispatch({"jsonrpc": "2.0", "method": "auth.whoami",
                                "params": {"session_token": token}, "id": "whoami"},
                               TRUST_NETWORK)
        finally:
            try:
                sg.close()
            except Exception:
                pass
        if not isinstance(resp, dict) or "result" not in resp:
            raise PermissionError("token resolution unavailable (writer not reachable)")
        r = resp["result"]
        return r.get("client_id"), Role(r.get("role", "guest"))


class _ThinKernelClient:
    def __init__(self, base_dir: str):
        self.iam = _ThinIAM(base_dir)


class ThinPortalGateway:
    """Serve-only portal gateway that holds NO local engine (no Silica index).

    Silica search is in-RAM and fast on the DAEMON, which already holds the ~5 GB index.
    A SECOND copy in the portal's own create_gateway is pure waste and OOMs an 8 GB host
    (daemon 5 GB + portal 5 GB > 8 GB → the daemon is OOM-killed → the whole site churns).
    This gateway keeps ONE index by forwarding EVERY RPC to the daemon over the IPC socket;
    the socket round-trip is negligible next to loading a duplicate multi-GB index.

    - sys.ping is answered locally (portal liveness, constant time) with a writer_online probe.
    - Everything else forwards to the one writer (its in-RAM index serves the read fast).
    - The Concept-Lab gate's token resolution forwards to the daemon (auth.whoami)."""

    def __init__(self, base_dir: str):
        self._base_dir = base_dir
        self.kernel_client = _ThinKernelClient(base_dir)
        # A53 item 4a — the writer_online liveness is CACHED and refreshed by a background thread,
        # so sys.ping is answered in constant time WITHOUT a socket round-trip. Under threadpool
        # saturation (a burst of slow forwards holding every worker), a sys.ping that had to make
        # its own blocking round-trip would queue behind them and the /health probe would time out
        # → a false 'unhealthy' → a portal respawn → the OOM churn. A dict read never blocks.
        self._writer_online = False
        self._writer_probe_at = 0.0
        self._ping_stop = threading.Event()
        self._ping_thr = threading.Thread(target=self._ping_refresh_loop, name="portal-ping-refresh",
                                          daemon=True)
        self._ping_thr.start()
        logging.getLogger("Harmonia.Portal.ASGI").info("[ThinPortal] serving reads by forwarding to the writer's in-RAM index — NO local index loaded.")

    def _ping_refresh_loop(self) -> None:
        """Refresh the cached writer_online liveness ~every 3 s off the request path (A53)."""
        while not self._ping_stop.wait(0.0 if self._writer_probe_at == 0.0 else 3.0):
            try:
                self._writer_online = bool(ping(self._base_dir))
            except Exception:
                self._writer_online = False
            self._writer_probe_at = time.time()

    def ping_cached(self) -> dict:
        """The constant-time liveness answer (cached writer_online) — read on the ASGI event loop
        so /health never touches the (possibly saturated) request threadpool (A53 item 4a)."""
        _age = (round(max(0.0, time.time() - self._writer_probe_at), 1)
                if self._writer_probe_at > 0.0 else None)   # None = not yet probed (constant-time still)
        return {"status": "ok", "kernel_online": True, "writer_online": bool(self._writer_online),
                "writer_probe_age": _age}

    def dispatch(self, payload: dict, transport_trust: str = TRUST_NETWORK) -> dict:
        method = payload.get("method", "") if isinstance(payload, dict) else ""
        rid = payload.get("id") if isinstance(payload, dict) else None
        if method == "sys.ping":
            return {"jsonrpc": "2.0", "id": rid, "result": self.ping_cached()}
        # A fresh connection per request so concurrent portal requests are not serialised
        # through one socket lock (a Unix-socket connect is microseconds; the daemon's IPC
        # server accepts concurrent connections).
        sg = SocketGateway(self._base_dir)
        try:
            return sg.dispatch(payload, transport_trust)
        except Exception as exc:                    # never crash the portal on a transport error
            return {"jsonrpc": "2.0", "id": rid,
                    "error": {"code": -32000, "message": "primary writer unreachable: %s" % exc}}
        finally:
            try:
                sg.close()
            except Exception:
                pass
