"""
hello_service — the minimal Akasha service program (cookbook example).

A "service program" is any long-lived OS process Akasha's Supervisor manages: it is
spawned from a validated recipe, appears in `svc ls`, and is restarted from that recipe
by the Cell daemon — exactly like the built-in web portal. This file is the smallest
complete example of the service-extension contract
(docs/for-llm/service-extension-and-delegation-spec.md §2).

Run standalone:
    python -m services.hello_service --port 8899

Under the Supervisor it is launched the same way (`python -m services.hello_service …`);
because it lives under `services/`, it is on the spawn allow-list out of the box, so a
recipe can respawn it with no code change to the Supervisor.

It does nothing but stay alive and answer a health check — the point is the lifecycle,
not the payload. It shuts down cleanly on SIGTERM (what `svc stop` / the stop cascade
send), so it never has to be SIGKILLed.
"""
import argparse
import http.server
import signal
import sys
import threading


def _run(host: str, port: int) -> None:
    stop = threading.Event()

    class _H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            # A trivial /healthz so a Supervisor health probe (kind:"http") can check it.
            body = b'{"service":"hello","status":"ok"}'
            self.send_response(200 if self.path in ("/healthz", "/") else 404)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            if self.command == "GET":
                self.wfile.write(body)

        def log_message(self, *a):        # keep the log quiet
            pass

    httpd = http.server.HTTPServer((host, port), _H)

    def _term(_sig, _frame):
        stop.set()
        threading.Thread(target=httpd.shutdown, daemon=True).start()

    signal.signal(signal.SIGTERM, _term)
    signal.signal(signal.SIGINT, _term)
    print(f"[hello_service] serving on {host}:{port} (Ctrl-C / SIGTERM to stop)", flush=True)
    try:
        httpd.serve_forever(poll_interval=0.5)
    finally:
        print("[hello_service] stopped.", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser(prog="hello_service")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8899)
    # The Supervisor may pass --engine to service modules; accept and ignore it so the same
    # module works whether launched by hand or by the plane.
    ap.add_argument("--engine", default="", help=argparse.SUPPRESS)
    args = ap.parse_args()
    _run(args.host, args.port)


if __name__ == "__main__":
    main()
