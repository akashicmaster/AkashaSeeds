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

    from api.portals.asgi import run_server
    run_server(gw, host=args.host, port=args.port, static_dirs=static_dirs or None)


if __name__ == "__main__":
    main()
