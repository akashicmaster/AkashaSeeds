#!/usr/bin/env python3
"""
Akasha — Single Entry Point.

  python akasha.py                        → httpd (background) + CLI
  python akasha.py --server uvicorn       → uvicorn/FastAPI (background) + CLI
  python akasha.py --host 0.0.0.0         → bind to all interfaces
  python akasha.py --port 8080            → specific port
  python akasha.py --stdio                → CLI only, no web portal
  python akasha.py <cmd…>                 → headless single-shot then exit
  (CGI env detected)                      → CGI handler
"""

import sys
import os

# ── 1. Python version guard ────────────────────────────────────────────────────
if sys.version_info < (3, 8):
    sys.stderr.write("[!] FATAL: Akasha requires Python 3.8 or higher.\n")
    sys.exit(1)

# ── 2. CGI stdout protection ───────────────────────────────────────────────────
_is_cgi = "GATEWAY_INTERFACE" in os.environ or "REQUEST_METHOD" in os.environ
_original_stdout = None
if _is_cgi:
    _original_stdout = sys.stdout
    sys.stdout = sys.stderr

# ── 3. Absolute path anchor ────────────────────────────────────────────────────
_root = os.path.dirname(os.path.abspath(__file__))
if _root not in sys.path:
    sys.path.insert(0, _root)


# ── 4. Infrastructure provisioning ────────────────────────────────────────────

def _ensure_dirs(root: str) -> None:
    for rel in [
        "data", "data/cells", "data/central",
        "data/import", "data/export",
        "env/models", "logs", "assets",
    ]:
        os.makedirs(os.path.join(root, rel), exist_ok=True)


# ── 5. Logging ────────────────────────────────────────────────────────────────

def _setup_logging(root: str, is_cgi: bool) -> None:
    import logging
    logger = logging.getLogger("Harmonia")
    if logger.handlers:
        return
    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler(os.path.join(root, "logs", "system.log"), encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(
        "%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s"
    ))
    logger.addHandler(fh)

    if not is_cgi:
        ch = logging.StreamHandler(sys.stderr)
        ch.setLevel(logging.WARNING)
        ch.setFormatter(logging.Formatter(
            "\033[2m[%(name)s]\033[0m %(levelname)s: %(message)s"
        ))
        logger.addHandler(ch)


# ── 6. Boot progress indicator ────────────────────────────────────────────────

def _boot_spinner(stop_event, stages):
    """Daemon thread: cycling spinner + stage labels while kernel initialises."""
    import time
    import itertools

    frames  = itertools.cycle(r'|/-\\')
    current = [stages[0]]
    idx     = [0]

    def _advance():
        idx[0] = min(idx[0] + 1, len(stages) - 1)
        current[0] = stages[idx[0]]

    stop_event.advance = _advance

    while not stop_event.is_set():
        sys.stdout.write(f"\r  {next(frames)}  {current[0]}  ")
        sys.stdout.flush()
        time.sleep(0.12)

    sys.stdout.write("\r" + " " * 60 + "\r")
    sys.stdout.flush()


# ── 7. Port helper ────────────────────────────────────────────────────────────

def _free_port(start: int = 8000, host: str = "127.0.0.1") -> int:
    import socket
    for p in range(start, 65535):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex((host, p)) != 0:
                return p
    return start


def _stop_recorded_portal(pid_path: str, wait: bool = True):
    """Stop a previously-detached web portal recorded in *pid_path*.

    A public deploy leaves its portal running on `exit` (so the site stays up
    after you disconnect). Re-running `akasha.py` must therefore REPLACE it, not
    collide on the port — so boot calls this to cleanly stop the old one first.
    The operator never has to kill a process by hand. Returns the PID stopped, or
    None if nothing was running.
    """
    import time as _t
    try:
        with open(pid_path) as f:
            pid = int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return None
    try:
        os.kill(pid, 15)                       # SIGTERM — graceful
    except ProcessLookupError:
        try: os.remove(pid_path)
        except OSError: pass
        return None
    except PermissionError:
        return None
    if wait:                                    # let it release the port, then be firm
        for _ in range(40):
            _t.sleep(0.1)
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                break
        else:
            try: os.kill(pid, 9)               # SIGKILL if it won't go
            except ProcessLookupError: pass
    try: os.remove(pid_path)
    except OSError: pass
    return pid


def _terminate_pid(pid: int, wait: bool = True) -> bool:
    """SIGTERM (then SIGKILL if it won't go) a pid. True if it was signalled."""
    import time as _t
    try:
        os.kill(pid, 15)
    except (ProcessLookupError, PermissionError):
        return False
    if wait:
        for _ in range(40):
            _t.sleep(0.1)
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                return True
        try: os.kill(pid, 9)
        except ProcessLookupError: pass
    return True


def _port_in_use(host: str, port: int) -> bool:
    """True if something is already LISTENing on host:port."""
    import socket
    probe = "127.0.0.1" if host in ("0.0.0.0", "::", "") else host
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.6)
        try:
            return s.connect_ex((probe, port)) == 0
        except OSError:
            return False


def _free_orphan_akasha_port(port: int):
    """If an orphaned Akasha portal (one not in the pid file — e.g. a detached
    portal still running after `rm -r *`) is holding *port*, stop it. Foreign
    processes are left alone. Returns the pid stopped, or None."""
    if not _port_in_use("127.0.0.1", port):
        return None
    pid, cmd = _port_holder(port)
    if pid and ("web_worker" in cmd or "akasha" in cmd):
        _terminate_pid(pid)
        import time as _t
        _t.sleep(0.3)
        return pid
    return None


def _port_holder(port: int):
    """Best-effort (Linux /proc): (pid, cmdline) of the process LISTENing on
    *port*, or (None, "") if it can't be determined (non-Linux, race, perms)."""
    try:
        inodes = set()
        for proto in ("tcp", "tcp6"):
            p = f"/proc/net/{proto}"
            if not os.path.exists(p):
                continue
            with open(p) as f:
                next(f, None)
                for line in f:
                    c = line.split()
                    if len(c) > 9 and c[3] == "0A":          # 0A = LISTEN
                        if int(c[1].rsplit(":", 1)[-1], 16) == port:
                            inodes.add(c[9])
        if not inodes:
            return (None, "")
        for pid in os.listdir("/proc"):
            if not pid.isdigit():
                continue
            try:
                for fd in os.listdir(f"/proc/{pid}/fd"):
                    try:
                        tgt = os.readlink(f"/proc/{pid}/fd/{fd}")
                    except OSError:
                        continue
                    if tgt.startswith("socket:[") and tgt[8:-1] in inodes:
                        try:
                            with open(f"/proc/{pid}/cmdline", "rb") as cf:
                                cmd = cf.read().replace(b"\x00", b" ").decode(
                                    "utf-8", "replace").strip()
                        except OSError:
                            cmd = ""
                        return (int(pid), cmd)
            except OSError:
                continue
    except Exception:
        pass
    return (None, "")


# ── 8. Main ───────────────────────────────────────────────────────────────────

def main() -> None:
    import argparse
    import logging
    import threading
    import time

    try:
        _ensure_dirs(_root)
    except Exception as exc:
        sys.stderr.write(f"[CRITICAL] Infrastructure init failed: {exc}\n")
        sys.exit(1)

    _setup_logging(_root, _is_cgi)
    log = logging.getLogger("Harmonia.Boot")
    log.info("Akasha boot sequence initiated.")

    # ── `stop` — halt a detached web portal (no kernel boot needed) ───
    # Simple counterpart to the "exit leaves the server running" behaviour, so an
    # operator never needs a pkill/ps incantation.
    if not _is_cgi and len(sys.argv) >= 2 and sys.argv[1] == "stop":
        _pid_path = os.path.join(_root, "data", "web-portal.pid")
        _stopped = _stop_recorded_portal(_pid_path)
        if _stopped:
            print(f"  [+] Stopped web portal (PID {_stopped}).")
        else:
            print("  [!] No running web portal to stop.")
        return

    # ── Boot the kernel ──────────────────────────────────────────────
    from api.gateway import create_gateway
    import api.gateway as _gw_module

    base_dir = os.path.join(_root, "data")

    _stop = threading.Event()
    if not _is_cgi:
        stages = [
            "Loading cognitive substrate",
            "Initializing memory cortex",
            "Wiring semantic engine",
            "Synchronizing knowledge graph",
        ]
        _spin_t = threading.Thread(
            target=_boot_spinner, args=(_stop, stages), daemon=True
        )
        _spin_t.start()

    # Series may be pinned out-of-band (e.g. a thesaurus deployment on shared
    # hosting via CGI) without editing code; defaults to the public seeds tier.
    _series = os.environ.get("AKASHA_SERIES", "seeds").strip() or "seeds"

    try:
        live_gw = create_gateway(series=_series, base_dir=base_dir)
    finally:
        if not _is_cgi:
            _stop.set()
            _spin_t.join(timeout=1.0)

    _gw_module.gateway = live_gw
    log.info("Kernel online. Gateway singleton wired.")

    if not _is_cgi:
        print("  [+] Akasha online.\n", flush=True)

    # ── Auto-ensure optional runtime libraries ────────────────────────
    # Runs only in interactive mode; CGI and stdio-only modes skip this.
    # Each call spins a pip subprocess with a 120 s timeout.  Errors are
    # logged but never fatal — the kernel runs fine without these.
    if not _is_cgi:
        from api.env_detector import env as _boot_env, Symbiosis as _BootSymbiosis

        # ML / Neural engine: LiteRT (ai-edge-litert) is the primary runtime — the standalone
        # tflite-runtime is frozen at 2.14 and crashes under numpy 2.x, so it is only a
        # legacy 32-bit-ARM fallback; full TF is a heavier last resort. (Nothing consumes
        # this at boot today — VisionEngine installs LiteRT on demand — but keeping the ladder
        # correct means the eager path installs the right, working runtime.)
        if _boot_env.get_ml_engine_status() == "installable":
            _BootSymbiosis.ensure_one_of(
                [
                    ("ai_edge_litert", "ai-edge-litert"),
                    ("tflite_runtime", "tflite-runtime"),
                    ("tensorflow",     "tensorflow-cpu"),
                ],
                scope="[ML]", feature="Neural Engine (LiteRT)",
            )

        # NLP engine: SpaCy for semantic trait extraction and word decomposition
        if _boot_env.get_nlp_status() == "installable":
            _BootSymbiosis.ensure(
                "spacy", "spacy",
                scope="[NLP]", feature="Natural Language Processing (SpaCy)",
            )

    # ── CGI fast-path ────────────────────────────────────────────────
    if _is_cgi:
        log.info("CGI environment detected.")
        from api.portals.asgi import run_cgi
        run_cgi(live_gw, _original_stdout)
        return

    # ── Parse CLI arguments ──────────────────────────────────────────
    parser = argparse.ArgumentParser(
        description="Akasha Substrate — cognitive knowledge mesh"
    )
    parser.add_argument(
        "--server", metavar="ENGINE",
        nargs="?", const="httpd", default="httpd",
        choices=["httpd", "uvicorn"],
        help="Web server engine: httpd (default) or uvicorn/FastAPI",
    )
    parser.add_argument(
        "--host", default="127.0.0.1",
        help="Web server bind address (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port", type=int, default=None,
        help="Web server port (default: auto-select from 8000)",
    )
    parser.add_argument(
        "--stdio", action="store_true",
        help="CLI only — skip web portal even if available",
    )
    parser.add_argument(
        "--serve", action="store_true",
        help="Headless server — start the web portal and keep it running; no "
             "interactive CLI. For persistent/detached deployment (VPS, systemd). "
             "Run genesis interactively once first.",
    )
    parser.add_argument(
        "--portal", metavar="MODE",
        nargs="?", const="archives", default=None,
        help=argparse.SUPPRESS,  # hidden: force a portal mode (e.g. 'archives')
    )
    parser.add_argument(
        "cmd", nargs=argparse.REMAINDER,
        help="Headless single-shot command then exit",
    )
    args = parser.parse_args()

    # ── Headless single-shot ─────────────────────────────────────────
    if args.cmd:
        from api.portals.stdio import run_single_shot
        print(run_single_shot(" ".join(args.cmd), live_gw))
        sys.exit(0)

    # ── Archives detection ─────────────────────────────────────────────
    # In deployed bundles (seeds/thesaurus): reproductor/ is absent, so
    # file existence determines which portal to serve.
    # On the mother machine (full repo): reproductor/ is present, so
    # the --portal flag is the only way to enable the archives portal;
    # the default is always the seeds portal (services/static).
    _archives_path    = os.path.join(_root, "archives")
    _archives_index   = os.path.join(_archives_path, "index.html")
    _is_dev           = os.path.isdir(os.path.join(_root, "reproductor"))
    if args.portal == "archives":
        _has_archives = True
    elif _is_dev:
        _has_archives = False          # dev default: seeds portal
    else:
        _has_archives = os.path.isfile(_archives_index)  # bundle: auto-detect

    # ── Web portal ─────────────────────────────────────────────────────
    if not args.stdio:
        import subprocess as _subprocess
        import atexit
        from api.service_manager import ServiceManager
        from api.env_detector import Symbiosis as _Symbiosis
        _svc_mgr = ServiceManager.get_instance()

        # Terminate all child processes on clean exit
        atexit.register(_svc_mgr.stop_all)

        # Clean RESTART semantics: a public deploy leaves its portal running on
        # `exit`, so re-running akasha.py must REPLACE that detached portal rather
        # than double-launch and collide on the port (the "Address already in use"
        # the operator hit). Stop it first — before the ACME port-80 responder or
        # the new portal binds — so the operator never kills a process by hand.
        _prev_portal = _stop_recorded_portal(os.path.join(base_dir, "web-portal.pid"))
        if _prev_portal:
            print(f"  [~] Restarting — stopped the portal left running by the last "
                  f"session (PID {_prev_portal}).", flush=True)

        # The ACME http-01 challenge (below) needs port 80. A portal orphaned by a
        # previous run — e.g. still in memory after `rm -r *` wiped its pid file —
        # can be holding it, which 404s the challenge and fails the cert. Free it
        # BEFORE ACME runs (only our own orphaned portal; foreign servers untouched).
        _orphan80 = _free_orphan_akasha_port(80)
        if _orphan80:
            print(f"  [~] Freed port 80 for the ACME challenge — stopped an orphaned "
                  f"Akasha portal (PID {_orphan80}).", flush=True)

        # Engine / host / port resolution.
        # AKASHA_HOST / AKASHA_PORT let a seed (which runs akasha.py via runpy
        # with no CLI args) bind a public interface / privileged port — e.g.
        # AKASHA_PORT=80 so a bare domain reaches the portal. CLI flags win.
        _web_engine = args.server
        _web_host   = os.environ.get("AKASHA_HOST", "").strip() or args.host
        if _has_archives and _web_host == "127.0.0.1":
            _web_host = "0.0.0.0"
        if _has_archives:
            _web_engine = "uvicorn"

        # TLS: a cert/key pair (env AKASHA_TLS_CERT/KEY or <data>/tls/) turns the
        # portal into HTTPS — required for search engines to crawl the archives.
        # TLS always uses uvicorn (clean SSL support) and the HTTPS port (443);
        # a sibling port-80 responder (started in the web worker) handles the
        # ACME challenge + HTTP→HTTPS redirect.
        # akasha-managed Let's Encrypt (layer B): if AKASHA_TLS_DOMAINS is set and
        # the cert is missing/near-expiry, obtain it now — before the portal binds
        # — using a temporary port-80 ACME responder. No-op (fast) when unconfigured
        # or when a current cert already exists, so the local/seeds path is untouched.
        try:
            from services.acme import ensure_certificate as _ensure_cert
            _acme_status = _ensure_cert(base_dir)
            if _acme_status == "issued":
                print("  [+] [TLS] Let's Encrypt certificate obtained.", flush=True)
            elif _acme_status.startswith("failed:"):
                print(f"  [!] [TLS] ACME provisioning failed — serving HTTP. "
                      f"({_acme_status[7:][:120]})", flush=True)
        except Exception as _acme_exc:
            log.warning(f"[Boot] ACME provisioning error: {_acme_exc}")

        # TLS is optional — never let it take the whole portal down. If the layer
        # is unavailable (e.g. an incomplete tree missing services/tls.py, or any
        # resolve error) degrade cleanly to HTTP instead of crashing the boot.
        try:
            from services.tls import resolve_tls as _resolve_tls
            _tls = _resolve_tls(base_dir)
        except Exception as _tls_exc:
            log.warning(f"[Boot] TLS layer unavailable ({_tls_exc}) — serving HTTP. "
                        f"Update the deployment (services/tls.py) to enable HTTPS.")
            print("  [!] [TLS] layer unavailable — serving HTTP "
                  "(incomplete tree? re-deploy to enable HTTPS).", flush=True)
            _tls = {"active": False, "https_port": 443, "certfile": "", "keyfile": "",
                    "http_port": 80, "challenge": ""}
        if _tls["active"]:
            _web_engine = "uvicorn"

        # Port: explicit --port / AKASHA_PORT win. Otherwise HTTPS → 443, the
        # public archives portal → 80 (bare domain works with no operator setup;
        # needs root), every other case auto-selects from 8000.
        _env_port = os.environ.get("AKASHA_PORT", "").strip()
        _web_port = (args.port
                     or (int(_env_port) if _env_port.isdigit() else 0)
                     or (_tls["https_port"] if _tls["active"] else None)
                     or (80 if _has_archives else _free_port(8000, _web_host)))

        # Static dirs for ASGI
        # The archives series ships its OWN cosmos instance (archives/cosmos/) —
        # a separate copy with the Archives door back into "/". The seeds series
        # uses the bundled services/static/cosmos (no archives door). Pick the
        # archives instance when this deployment is an archives.
        _archives_cosmos = os.path.join(_archives_path, "cosmos")
        _cosmos_static   = (_archives_cosmos
                            if _has_archives and os.path.isdir(_archives_cosmos)
                            else os.path.join(_root, "services", "static", "cosmos"))
        _services_static = os.path.join(_root, "services", "static")
        _docs_path       = os.path.join(_root, "docs")

        # Build mount list: most-specific paths first, "/" last.
        # Archives sub-apps (word sphere, field gallery, …) are mounted
        # individually so they are reachable from both portals.
        _asgi_static_dirs = []
        if os.path.isdir(_cosmos_static):
            _asgi_static_dirs.append(("/cosmos", _cosmos_static))
        if os.path.isdir(_docs_path):
            _asgi_static_dirs.append(("/docs", _docs_path))
        for _app in ("word", "field"):
            _app_path = os.path.join(_archives_path, _app)
            if os.path.isdir(_app_path):
                _asgi_static_dirs.append((f"/{_app}", _app_path))

        if _has_archives:
            _asgi_static_dirs.append(("/", _archives_path))
            _web_engine = "uvicorn"          # archives portal always needs ASGI
        else:
            _asgi_static_dirs.append(("/", _services_static))
            # Seeds portal: keep httpd as default.
            # Extra mounts (cosmos, cookbook, docs) are active when uvicorn is
            # chosen explicitly via --server uvicorn; httpd ignores them.

        # ── Auto-ensure ASGI dependencies (fastapi + uvicorn) ────────
        # Runs pip install as a child process with a spinner + timeout.
        # If either package cannot be installed, fall back to httpd.
        if _web_engine == "uvicorn":
            _fa = _Symbiosis.ensure(
                "fastapi", "fastapi",
                scope="[ASGI]", feature="Web Portal (FastAPI)",
            )
            _uv = _Symbiosis.ensure(
                "uvicorn", "uvicorn[standard]",
                scope="[ASGI]", feature="Web Portal (uvicorn)",
            )
            if not (_fa and _uv):
                print("  [!] ASGI portal unavailable — falling back to built-in httpd.\n",
                      flush=True)
                _web_engine = "httpd"

        # ── httpd portal (thread-based, existing) ────────────────────
        # The portal banner is printed from this thread; if it lands while the
        # CLI is prompting for genesis/auth it corrupts the prompt. We signal
        # readiness after the banner so the boot can flush it before the prompt.
        _http_ready = threading.Event()

        def _launch_http_portal():
            from services.http_gateway import BaseWebService
            _sd = _archives_path if _has_archives else None
            web_svc = BaseWebService(gw=live_gw, port=_web_port, host=_web_host, static_dir=_sd)
            _svc_mgr.register_thread_service(
                "http_portal", web_svc, _launch_http_portal,
                host=_web_host, port=_web_port,
            )
            web_svc.start(ready_event=_http_ready)

        # ── uvicorn portal (subprocess) ───────────────────────────────
        def _launch_uvicorn_worker():
            """Spawn uvicorn as a subprocess and register with ServiceManager."""
            cmd = [
                sys.executable, "-m", "api.portals.web_worker",
                "--host",   _web_host,
                "--port",   str(_web_port),
                "--data",   base_dir,
            ]
            if _asgi_static_dirs:
                for mount, path in _asgi_static_dirs:
                    cmd += ["--static", f"{mount}:{path}"]

            log_path = os.path.join(_root, "logs", "web-portal.log")
            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"
            try:
                log_fh = open(log_path, "a")
                # start_new_session: put the portal in its own session so it is
                # NOT killed by the SSH SIGHUP when the operator disconnects — the
                # server keeps serving after `exit` on a public deploy.
                proc = _subprocess.Popen(
                    cmd, stdout=log_fh, stderr=_subprocess.STDOUT,
                    cwd=_root, env=env, start_new_session=True,
                )
            except Exception as exc:
                log.error(f"[Boot] Failed to start web worker: {exc}")
                return {"error": str(exc)}

            # Record the PID so `akasha.py stop` can find a detached portal in a
            # later, separate process (the in-memory registry is gone by then).
            try:
                with open(os.path.join(base_dir, "web-portal.pid"), "w") as _pf:
                    _pf.write(str(proc.pid))
            except Exception:
                pass

            _svc_mgr.register_process_service(
                "web-portal", proc, log_fh,
                engine="uvicorn", host=_web_host, port=_web_port,
                spawn_fn=_launch_uvicorn_worker,
            )
            log.info(f"[Boot] Web worker PID {proc.pid} on {_web_host}:{_web_port}")
            from services.http_gateway import portal_banner
            _scheme = "https" if _tls["active"] else "http"
            for _line in portal_banner(_web_host, _web_port, scheme=_scheme):
                print("  " + _line, flush=True)
            print(f"      (PID {proc.pid} · logs/web-portal.log)\n", flush=True)
            return {"status": "started", "pid": proc.pid}

        # ── Double-launch safety net ──────────────────────────────────
        # The pid-file stop above handles the normal case. This catches the rest:
        # a portal left by a crash, or started another way, that the pid file does
        # not know about. If the serve port is still held — self-heal an orphaned
        # Akasha portal (stop it), or refuse to start a second instance and name
        # who holds the port. Either way the operator never kills a process by hand.
        _skip_portal = False
        if _port_in_use(_web_host, _web_port):
            _hpid, _hcmd = _port_holder(_web_port)
            if _hpid and ("web_worker" in _hcmd or "akasha" in _hcmd):
                _terminate_pid(_hpid)
                print(f"  [~] Freed port {_web_port} — stopped an orphaned Akasha "
                      f"portal (PID {_hpid}).", flush=True)
                time.sleep(0.3)
            else:
                _who = (f"PID {_hpid} ({(_hcmd.split() or ['?'])[0]})"
                        if _hpid else "another process")
                print(f"  [!] Port {_web_port} is already in use by {_who} — "
                      f"NOT starting a second portal.\n"
                      f"      Stop it, or start with a free port (AKASHA_PORT=…). "
                      f"Double-launch prevented.", flush=True)
                _skip_portal = True

        # ── Launch ────────────────────────────────────────────────────
        if _skip_portal:
            pass
        elif _web_engine == "uvicorn":
            _launch_uvicorn_worker()
        else:
            def _http_thread():
                try:
                    _launch_http_portal()
                except Exception as exc:
                    log.warning(f"[Boot] HTTP portal exited: {exc}")
            _t = threading.Thread(target=_http_thread, daemon=True, name="http-portal")
            _t.start()
            # Let the portal print its "Gateway Online" banner before the CLI
            # prompt appears, so it never lands in the middle of a genesis/auth
            # input line (bounded — never hang boot if the bind is slow).
            _http_ready.wait(timeout=5.0)

        _mode_label = "archives/uvicorn" if _has_archives else _web_engine
        if not _skip_portal:
            log.info(f"Web portal ({_mode_label}) starting on {_web_host}:{_web_port}.")

    # ── Headless server mode (--serve) ────────────────────────────────
    # Keep the portal running with NO interactive CLI — the correct shape for a
    # detached / persistent deployment (nohup, systemd). Without this, a detached
    # run falls into run_cli, whose auth loop consumes the /dev/null EOF and
    # returns, tearing the portal down. genesis must have been done already
    # (interactively, once); an uninitialised cell serves only anonymous reads.
    if args.serve and not args.stdio:
        log.info("[Boot] --serve: headless server mode (no CLI).")
        print("  [+] Headless server mode — portal is serving; Ctrl+C to stop.\n", flush=True)
        _portal_proc = (_svc_mgr.services.get("web-portal") or {}).get("process")
        try:
            if _portal_proc is not None:
                _portal_proc.wait()          # uvicorn subprocess
            else:
                threading.Event().wait()     # httpd runs in a daemon thread — block here
        except (KeyboardInterrupt, EOFError):
            pass
        return

    # ── CLI — always foreground ───────────────────────────────────────
    from api.portals.stdio import run_cli
    try:
        run_cli(live_gw)
    except (KeyboardInterrupt, EOFError):
        log.info("[Boot] CLI ended (exit / disconnect / interrupt).")

    # Public deploy: leaving the CLI must NOT take the server down. When the
    # portal is a detached subprocess (uvicorn — start_new_session above), drop
    # it from the service registry so atexit's stop_all skips it, and return —
    # the portal keeps serving after this process exits and after SSH closes.
    # The operator's whole job is: run → genesis → exit. (httpd runs as a thread
    # and cannot outlive the process, so that path still stops on exit; use
    # --serve for a headless httpd deploy.)
    _is_public = (not args.stdio) and (_has_archives or _web_host in ("0.0.0.0", "::"))
    _portal_proc = (_svc_mgr.services.get("web-portal") or {}).get("process")
    if _is_public and _portal_proc is not None and _portal_proc.poll() is None:
        # The base-ontology load runs in THIS process; if we exit before it
        # finishes (first boot), the detached portal would serve a half-loaded
        # graph and nothing would complete it. Wait for the restart sentinel
        # first — instant on a warm cell, so the operator just types `exit`.
        import glob as _glob
        _sent_glob = os.path.join(base_dir, "central", "sentinels", "*.done")
        if not _glob.glob(_sent_glob):
            print("  [*] Finishing base ontology load before detaching (first boot — one moment)…",
                  flush=True)
            _deadline = time.time() + 900
            while time.time() < _deadline and not _glob.glob(_sent_glob):
                time.sleep(3)
        _svc_mgr.services.pop("web-portal", None)          # release from atexit
        log.info("[Boot] Portal detached on CLI exit (PID %s) — still serving.", _portal_proc.pid)
        print(f"\n  [+] Web portal still running on {_web_host}:{_web_port} "
              f"(PID {_portal_proc.pid}) — keeps serving after you disconnect.\n"
              f"      Re-run  python akasha.py  to restart it (auto-replaces this one).\n"
              f"      Or      python akasha.py stop  to stop it. No manual kill needed.\n",
              flush=True)
        return


if __name__ == "__main__":
    main()
