"""
Akasha web worker — standalone subprocess entry point.

Boots an independent Gateway instance and serves it via uvicorn/FastAPI.
Launched by akasha.py when the ASGI portal is requested.

Usage (internal — launched by akasha.py, managed by the Harmonia Supervisor):
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
    cert (SSL cannot be hot-swapped in place). An operator-supplied cert (no ACME domains
    declared) is never renewed here.
    """
    import os as _os
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


def _bias_oom_victim() -> None:
    """F48-2.3 — a serve-only portal is the SACRIFICEABLE child: bias it as the OOM killer's
    PREFERRED victim so a memory spike takes the transient portal, NOT the single writer daemon.
    A POSITIVE oom_score_adj needs no privilege (unlike the writer's protective negative one, which
    silently no-ops unprivileged — why dmesg kept showing 0). AKASHA_PORTAL_OOM_SCORE_ADJ tunes it
    (default 500); 0 disables. Best-effort, never fatal."""
    try:
        _v = int(os.environ.get("AKASHA_PORTAL_OOM_SCORE_ADJ", "500") or "0")
        if _v:
            with open("/proc/self/oom_score_adj", "w") as _f:
                _f.write(str(max(-1000, min(1000, _v))))
    except Exception:
        pass


def main() -> None:
    _bias_oom_victim()
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

    # Lever C — DEFER the heavy gateway build (create_gateway loads the ~1GB read substrate; on a
    # B-scale line that is the 45–60 s "port not yet bound" window that makes the site look DOWN).
    # We hand this factory to run_server_warming, which binds the port IMMEDIATELY with a warming
    # page and calls the factory on a background thread, swapping in the live app when ready. The
    # cheap setup below (watchdog, TLS, health-probe registration) still runs first on this thread.
    def _make_gateway():
        # The serve-only portal holds NO index. Silica search is in-RAM and fast on the DAEMON,
        # which already holds the index; a SECOND copy here is pure waste and OOMs a memory-bounded
        # host (daemon 5 GB + portal 5 GB > 8 GB → the daemon is OOM-killed → the whole site
        # churns). ThinPortalGateway forwards every RPC to the one writer, keeping ONE index. (The
        # local-engine mode is deleted with its switch — the purge order §4.5.)
        from api.portals.cell_ipc import ThinPortalGateway, ping as _ping
        # Wait for the daemon to be READY (its socket is bound only AFTER its index is loaded and
        # it can serve), so the warming page shows until forwards can actually be answered.
        import time as _t
        while not _ping(data_dir):
            _t.sleep(1.0)
        return ThinPortalGateway(data_dir)

    # R5 — daemon self-watchdog. This serve-only portal outlives the writer and never writes the
    # nucleus, so it is the natural place to watch the daemon: if the writer wedges (silent for K
    # rounds with a stale boot heartbeat) the watchdog reaps it and spawns a fresh one. No-op unless
    # AKASHA_SERVE_ONLY is set (it is, for this subprocess).
    try:
        from api.portals import daemon_watchdog
        daemon_watchdog.start(data_dir)
    except Exception:
        pass

    # TLS: if a cert/key pair is present, terminate HTTPS in uvicorn and stand
    # the port-80 responder (ACME http-01 challenge + HTTP→HTTPS redirect). The
    # detached portal process owns the responder thread, so it survives SSH
    # hangup just like the HTTPS listener. Plain HTTP is unchanged when inactive.
    # TLS is optional — a missing/broken services.tls must not take the portal
    # down; degrade to plain HTTP instead of crashing this worker subprocess.
    ssl_cert = ssl_key = None
    serve_port = args.port
    try:
        from services.tls import resolve_tls, start_http_responder
        tls = resolve_tls(data_dir)
        if tls["active"]:
            ssl_cert, ssl_key = tls["certfile"], tls["keyfile"]
            # When TLS is active, HTTPS MUST bind the https port (443) and port 80 belongs
            # to the ACME/redirect responder started below. akasha.py can resolve --port
            # to 80 when it checks the cert a moment before it becomes readable; the worker
            # then sees TLS active, so binding uvicorn on that 80 would collide with our OWN
            # responder ([Errno 98] address already in use → the worker dies and `svc ls`
            # shows "Dead" while a later 443 retry serves). Bind the https port instead.
            serve_port = tls["https_port"]
            start_http_responder(tls["challenge"], tls["https_port"],
                                 host=args.host, http_port=tls["http_port"])
            logging.getLogger("akasha-web-worker").info(
                "[TLS] HTTPS active on %s:%s (cert=%s)", args.host, serve_port, ssl_cert)
            _start_renewal_watcher(data_dir, ssl_cert)
    except Exception as exc:
        logging.getLogger("akasha-web-worker").warning(
            "[TLS] layer unavailable (%s) — serving HTTP.", exc)
        ssl_cert = ssl_key = None
        serve_port = args.port

    # F8 — the daemon registered this portal's health probe with the scheme/port it THOUGHT we'd
    # serve, but a TLS activation just moved service to HTTPS on the https port. Correct the probe
    # in the run-dir so the daemon's health tick pings the port we actually serve — else it gets no
    # answer and respawns a perfectly healthy portal every tick (the "respawned svc:web-portal
    # (unhealthy)" churn on every boot, which also structurally muted the R5 watchdog).
    try:
        from lib.harmonia import supervisor as _sv
        _scheme = "https" if ssl_cert else "http"
        _sv.update_unit_health(data_dir, "svc:web-portal", {
            "kind": "http",
            "target": f"{_scheme}://127.0.0.1:{int(serve_port)}/api/rpc",
            "method": "sys.ping", "timeout": 3.0,
        })
        # F9 — signal readiness: with Lever C the port binds IMMEDIATELY (warming page), so the
        # worker is reachable from here on. The warming page answers the sys.ping health probe with
        # a 503 (any HTTP response counts as alive), so ending the boot grace now is safe — a
        # genuinely-hung worker is still caught, while the slow substrate load never looks dead.
        _sv.mark_unit_ready(data_dir, "svc:web-portal")
    except Exception:
        pass

    # Lever C — bind the port now with a warming page; build the live gateway (the heavy substrate
    # load, via _make_gateway) on a background thread and swap it in when ready. The site is never
    # "connection refused" during boot — it shows "warming up" and self-opens the instant it's live.
    from api.portals.asgi import run_server_warming
    run_server_warming(_make_gateway, host=args.host, port=serve_port,
                       static_dirs=static_dirs or None,
                       ssl_certfile=ssl_cert, ssl_keyfile=ssl_key)


if __name__ == "__main__":
    main()
