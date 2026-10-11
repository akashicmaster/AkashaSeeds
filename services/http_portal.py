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
boot-load + autolearn). This worker only serves reads — AKASHA_SERVE_ONLY in its
env keeps it from opening a second writer.

Usage (internal — launched by akasha.py):
  python -m services.http_portal \\
      --host 0.0.0.0 --port 8080 --data /path/to/data --series seeds \\
      [--static /abs/static/root]
"""
import argparse
import os
import sys


def main() -> None:
    # F48-2.3 — bias this serve-only portal as the OOM killer's PREFERRED victim (positive
    # oom_score_adj, no privilege needed) so a memory spike takes the transient portal, not the
    # single writer. AKASHA_PORTAL_OOM_SCORE_ADJ tunes it (default 500); 0 disables.
    try:
        _v = int(os.environ.get("AKASHA_PORTAL_OOM_SCORE_ADJ", "500") or "0")
        if _v:
            with open("/proc/self/oom_score_adj", "w") as _f:
                _f.write(str(max(-1000, min(1000, _v))))
    except Exception:
        pass
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

    # Lever C — DEFER the heavy gateway build (create_gateway loads the ~1GB read substrate, the
    # 45–60 s window in which the port would otherwise be unbound and the site "connection refused").
    # BaseWebService binds the port immediately, serves a warming page, and runs this factory on a
    # background thread — swapping in the live gateway when ready. The cheap setup below runs first.
    def _make_gateway():
        from api.gateway import create_gateway
        # Single-writer invariant: this serve-only subprocess must NOT write the nucleus directly.
        # SplitGateway serves reads from this local engine and forwards writes/auth to the ONE
        # primary writer over the local socket (preserving network trust). See cell_ipc.SplitGateway.
        from api.portals.cell_ipc import SplitGateway
        return SplitGateway(create_gateway(series=args.series, base_dir=data_dir), data_dir)

    # R5 — daemon self-watchdog (serve-only portals only; see api/portals/daemon_watchdog.py).
    try:
        from api.portals import daemon_watchdog
        daemon_watchdog.start(data_dir)
    except Exception:
        pass

    # F9 — signal readiness: with Lever C the port binds immediately (warming page), which answers
    # the health probe, so ending the boot grace here is safe — a hung worker is still caught, while
    # the slow substrate load never looks dead.
    try:
        from lib.harmonia import supervisor as _sv
        _sv.mark_unit_ready(data_dir, "svc:web-portal")
    except Exception:
        pass

    from services.http_gateway import BaseWebService
    svc = BaseWebService(gw_factory=_make_gateway, port=args.port, host=args.host,
                         static_dir=static_dir)
    svc.start()   # binds immediately (warming), builds the gateway in the background


if __name__ == "__main__":
    main()
