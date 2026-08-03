"""
Akasha HTTP portal — standalone subprocess entry point (stdlib http.server).

The non-ASGI counterpart of api/portals/web_worker.py: boots an independent
**serve-only** Gateway and serves it via services.http_gateway.BaseWebService
(pure-stdlib ThreadingHTTPServer — no uvicorn/fastapi dependency, the seeds
default). Launched by akasha.py as an OS subprocess and managed by the Harmonia
Supervisor as a recipe-respawnable process unit — this is what lets the HTTP
portal be a first-class managed service (a cross-process restart / boot respawn),
replacing the former in-process daemon thread.

Serve-only: the launching process is the sole nucleus writer (it runs the
boot-load + autolearn). This worker only serves reads — AKASHA_SERVE_ONLY /
AKASHA_NO_AUTOLEARN in its env keep it from opening a second writer.

Usage (internal — launched by akasha.py):
  python -m services.http_portal \\
      --host 0.0.0.0 --port 8080 --data /path/to/data --series seeds \\
      [--static /abs/static/root]
"""
import argparse
import os
import sys


def main() -> None:
    # Anchor sys.path to project root (two dirs above services/… → one dir above services/).
    _here = os.path.dirname(os.path.abspath(__file__))
    _root = os.path.dirname(_here)
    if _root not in sys.path:
        sys.path.insert(0, _root)

    ap = argparse.ArgumentParser(prog="akasha-http-portal", add_help=False)
    ap.add_argument("--host",   default="0.0.0.0")
    ap.add_argument("--port",   type=int, default=8080)
    ap.add_argument("--data",   default="data")
    ap.add_argument("--series", default="seeds")
    ap.add_argument("--static", default="", metavar="ABS_DIR",
                    help="Single static root to serve (absolute or repo-relative)")
    args = ap.parse_args()

    data_dir = args.data if os.path.isabs(args.data) else os.path.join(_root, args.data)
    static_dir = None
    if args.static:
        static_dir = args.static if os.path.isabs(args.static) else os.path.join(_root, args.static)

    import logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s",
    )

    from api.gateway import create_gateway
    # Single-writer invariant: this serve-only subprocess must NOT write the nucleus directly.
    # SplitGateway serves reads from this local engine and forwards writes/auth to the ONE
    # primary writer over the local socket (preserving network trust). See cell_ipc.SplitGateway.
    from api.portals.cell_ipc import SplitGateway
    gw = SplitGateway(create_gateway(series=args.series, base_dir=data_dir), data_dir)

    # R5 — daemon self-watchdog (serve-only portals only; see api/portals/daemon_watchdog.py).
    try:
        from api.portals import daemon_watchdog
        daemon_watchdog.start(data_dir)
    except Exception:
        pass

    from services.http_gateway import BaseWebService
    svc = BaseWebService(gw=gw, port=args.port, host=args.host, static_dir=static_dir)
    svc.start()   # blocking serve_forever — the subprocess's whole job


if __name__ == "__main__":
    main()
