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


# ── 8. Main ───────────────────────────────────────────────────────────────────

def main() -> None:
    import argparse
    import logging
    import threading

    try:
        _ensure_dirs(_root)
    except Exception as exc:
        sys.stderr.write(f"[CRITICAL] Infrastructure init failed: {exc}\n")
        sys.exit(1)

    _setup_logging(_root, _is_cgi)
    log = logging.getLogger("Harmonia.Boot")
    log.info("Akasha boot sequence initiated.")

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

    try:
        live_gw = create_gateway(series="seeds", base_dir=base_dir)
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

        # ML / Neural engine: try lightweight tflite first, fall back to full TF
        if _boot_env.get_ml_engine_status() == "installable":
            _BootSymbiosis.ensure_one_of(
                [
                    ("tflite_runtime", "tflite-runtime"),
                    ("tensorflow",     "tensorflow-cpu"),
                    ("tensorflow",     "tensorflow"),
                ],
                scope="[ML]", feature="Neural Engine (TFLite)",
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

        # Engine / host / port resolution
        _web_engine = args.server
        _web_host   = args.host
        if _has_archives and _web_host == "127.0.0.1":
            _web_host = "0.0.0.0"
        if _has_archives:
            _web_engine = "uvicorn"

        _web_port = args.port or _free_port(8000, _web_host)

        # Static dirs for ASGI
        _cosmos_static   = os.path.join(_root, "services", "static", "cosmos")
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
        def _launch_http_portal():
            from services.http_gateway import BaseWebService
            _sd = _archives_path if _has_archives else None
            web_svc = BaseWebService(gw=live_gw, port=_web_port, host=_web_host, static_dir=_sd)
            _svc_mgr.register_thread_service(
                "http_portal", web_svc, _launch_http_portal,
                host=_web_host, port=_web_port,
            )
            web_svc.start()

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
                proc = _subprocess.Popen(
                    cmd, stdout=log_fh, stderr=_subprocess.STDOUT,
                    cwd=_root, env=env,
                )
            except Exception as exc:
                log.error(f"[Boot] Failed to start web worker: {exc}")
                return {"error": str(exc)}

            _svc_mgr.register_process_service(
                "web-portal", proc, log_fh,
                engine="uvicorn", host=_web_host, port=_web_port,
                spawn_fn=_launch_uvicorn_worker,
            )
            log.info(f"[Boot] Web worker PID {proc.pid} on {_web_host}:{_web_port}")
            print(f"  [+] Web portal → http://{_web_host}:{_web_port}"
                  f"  (PID {proc.pid} · logs/web-portal.log)\n", flush=True)
            return {"status": "started", "pid": proc.pid}

        # ── Launch ────────────────────────────────────────────────────
        if _web_engine == "uvicorn":
            _launch_uvicorn_worker()
        else:
            def _http_thread():
                try:
                    _launch_http_portal()
                except Exception as exc:
                    log.warning(f"[Boot] HTTP portal exited: {exc}")
            _t = threading.Thread(target=_http_thread, daemon=True, name="http-portal")
            _t.start()

        _mode_label = "archives/uvicorn" if _has_archives else _web_engine
        log.info(f"Web portal ({_mode_label}) starting on {_web_host}:{_web_port}.")

    # ── CLI — always foreground ───────────────────────────────────────
    # EOFError / KeyboardInterrupt during auth (e.g. Codespaces stdin not yet
    # ready after hibernate resume) must NOT kill the web portal via atexit.
    # Only a clean user-initiated exit ("exit"/"quit") should stop the portal.
    _stdin_died = False
    from api.portals.stdio import run_cli
    try:
        run_cli(live_gw)
    except (KeyboardInterrupt, EOFError):
        _stdin_died = True
        log.info("[Boot] stdin disconnected before CLI session started.")

    # If stdin died and the web portal is still running, keep the process alive
    # so atexit doesn't send SIGTERM to uvicorn prematurely.
    if _stdin_died and not args.stdio:
        _portal_info = _svc_mgr.services.get("web-portal") or {}
        _portal_proc = _portal_info.get("process")
        if _portal_proc and _portal_proc.poll() is None:
            log.info("[Boot] Web portal running — waiting for manual shutdown (Ctrl+C).")
            print("  [+] CLI unavailable (stdin closed). Web portal is running.\n"
                  "      Press Ctrl+C to shut down.", flush=True)
            try:
                _portal_proc.wait()
            except (KeyboardInterrupt, EOFError):
                pass


if __name__ == "__main__":
    main()
