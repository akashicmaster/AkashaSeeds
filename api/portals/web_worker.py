"""
Akasha web worker — standalone subprocess entry point.

Boots an independent Gateway instance and serves it via uvicorn/FastAPI.
Launched by akasha.py when the ASGI portal is requested.

Usage (internal — called by ServiceManager):
  python -m api.portals.web_worker \\
      --host 0.0.0.0 --port 8000 --data /path/to/data \\
      [--static /mount:abs/dir ...]
"""
import argparse
import os
import sys


def _start_renewal_watcher(data_dir: str, certfile: str) -> None:
    """In the long-running detached portal, watch the cert and renew it before
    expiry. The portal already runs the port-80 responder that serves the ACME
    challenge, so renewal only writes challenge tokens into the shared dir. On a
    successful renewal the worker re-execs itself so uvicorn picks up the new
    cert (SSL cannot be hot-swapped in place). Opt out with AKASHA_ACME_NO_RENEW.
    """
    import os as _os
    if _os.environ.get("AKASHA_ACME_NO_RENEW"):
        return
    if not _os.environ.get("AKASHA_TLS_DOMAINS", "").strip() \
            and not _os.environ.get("AKASHA_BASE_DOMAIN", "").strip():
        return   # nothing to renew against — cert is operator-supplied

    import threading, time, sys as _sys, logging as _logging
    log = _logging.getLogger("akasha-web-worker")

    def _loop():
        from services.acme import needs_issue, _renew_days, obtain_certificate, _domains_from_env
        check_every = 12 * 3600     # twice a day
        while True:
            time.sleep(check_every)
            try:
                if not needs_issue(certfile, _renew_days()):
                    continue
                domains = _domains_from_env()
                if not domains:
                    continue
                log.info("[TLS] Certificate near expiry — renewing via ACME.")
                obtain_certificate(
                    data_dir, domains,
                    email=_os.environ.get("AKASHA_TLS_EMAIL", "").strip(),
                )
                log.info("[TLS] Renewed — re-executing worker to load the new cert.")
                _os.execv(_sys.executable, [_sys.executable] + _sys.argv)
            except Exception as exc:
                log.warning("[TLS] Renewal attempt failed (will retry): %s", exc)

    threading.Thread(target=_loop, daemon=True, name="tls-renewal-watcher").start()


def main() -> None:
    # Anchor sys.path to project root (two dirs above api/portals/)
    _here = os.path.dirname(os.path.abspath(__file__))
    _root = os.path.dirname(os.path.dirname(_here))
    if _root not in sys.path:
        sys.path.insert(0, _root)

    ap = argparse.ArgumentParser(prog="akasha-web-worker", add_help=False)
    ap.add_argument("--host",   default="0.0.0.0")
    ap.add_argument("--port",   type=int, default=8000)
    ap.add_argument("--data",   default="data")
    ap.add_argument("--series", default="seeds")
    ap.add_argument("--static", action="append", default=[], metavar="MOUNT:DIR",
                    help="Static mount point: /path:abs/dir (repeatable)")
    args = ap.parse_args()

    data_dir = args.data if os.path.isabs(args.data) else os.path.join(_root, args.data)

    static_dirs = []
    for spec in args.static:
        mount, _, path = spec.partition(":")
        if path and not os.path.isabs(path):
            path = os.path.join(_root, path)
        if mount and path:
            static_dirs.append((mount, path))

    import logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s",
    )

    from api.gateway import create_gateway
    gw = create_gateway(series=args.series, base_dir=data_dir)

    # TLS: if a cert/key pair is present, terminate HTTPS in uvicorn and stand
    # the port-80 responder (ACME http-01 challenge + HTTP→HTTPS redirect). The
    # detached portal process owns the responder thread, so it survives SSH
    # hangup just like the HTTPS listener. Plain HTTP is unchanged when inactive.
    # TLS is optional — a missing/broken services.tls must not take the portal
    # down; degrade to plain HTTP instead of crashing this worker subprocess.
    ssl_cert = ssl_key = None
    try:
        from services.tls import resolve_tls, start_http_responder
        tls = resolve_tls(data_dir)
        if tls["active"]:
            ssl_cert, ssl_key = tls["certfile"], tls["keyfile"]
            start_http_responder(tls["challenge"], tls["https_port"],
                                 host=args.host, http_port=tls["http_port"])
            logging.getLogger("akasha-web-worker").info(
                "[TLS] HTTPS active on %s:%s (cert=%s)", args.host, args.port, ssl_cert)
            _start_renewal_watcher(data_dir, ssl_cert)
    except Exception as exc:
        logging.getLogger("akasha-web-worker").warning(
            "[TLS] layer unavailable (%s) — serving HTTP.", exc)
        ssl_cert = ssl_key = None

    from api.portals.asgi import run_server
    run_server(gw, host=args.host, port=args.port, static_dirs=static_dirs or None,
               ssl_certfile=ssl_cert, ssl_keyfile=ssl_key)


if __name__ == "__main__":
    main()
