#!/usr/bin/env python3
"""
HostReroute path-aware rewrite eval (F56 A14) — the `/lib/*` 404 on per-host domains.

HostReroute fronts several domains from one app/archives/ tree: world.<base> → app/archives/world/. It
rewrote EVERY non-reserved path to /<host_dir>/…, so `/lib/plotly.js` on world.<base> became
/world/lib/plotly.js → 404 (the /a/<slug> template loads plotly from the SHARED /lib mount, which
is not under app/archives/). Fix: reserve the shared static mounts, AND rewrite PATH-AWARE — only when
app/archives/<host_dir>/<path> actually exists; otherwise keep the original path (fall back to the
shared mount / default root), which also fixes the favicon 404s.

Run:  python app/test/host_reroute_eval.py     (exit 0 = all pass)
"""
import asyncio
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
os.environ["AKASHA_BASE_DOMAIN"] = "akashicarchives.net"
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _mk_tree():
    root = tempfile.mkdtemp(prefix="akasha_hostreroute_")
    os.makedirs(os.path.join(root, "world", "about"), exist_ok=True)
    for p in (("world", "index.html"), ("world", "about", "index.html"),
              ("index.html",), ("favicon.ico",)):
        with open(os.path.join(root, *p), "w") as f:
            f.write("x")
    # NB: no world/lib/ and no world/favicon.ico — those must fall back to the shared/default root.
    return root


async def _final_path(app, host, path):
    """Drive one HTTP scope through the middleware and return the path the inner app received."""
    box = {"path": None}

    async def inner(scope, receive, send):
        box["path"] = scope.get("path")
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b""})

    # HostReroute takes (app, archives_root); patch its inner app to our recorder.
    app.app = inner

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(_):
        pass

    scope = {"type": "http", "path": path,
             "headers": [(b"host", host.encode())], "raw_path": path.encode()}
    await app(scope, receive, send)
    return box["path"]


def main():
    import api.portals.asgi as A
    root = _mk_tree()
    hr = A.HostReroute(lambda *a: None, os.path.abspath(root))

    async def run():
        H = "world.akashicarchives.net"
        # /lib/*.js — shared mount, NOT under app/archives/world → keep original (was rewritten → 404).
        p = await _final_path(hr, H, "/lib/plotly-2.27.0.min.js")
        check("A14 /lib/*.js on a host is NOT rewritten (shared mount serves it)",
              p == "/lib/plotly-2.27.0.min.js", "got %s" % p)
        # host ROOT → rewritten to the host index dir.
        p = await _final_path(hr, H, "/")
        check("host root '/' rewrites to the host dir", p == "/world/", "got %s" % p)
        # a page the host HAS → rewritten.
        p = await _final_path(hr, H, "/about")
        check("a path the host has (app/archives/world/about) is rewritten",
              p == "/world/about", "got %s" % p)
        # favicon the host does NOT have → keep original (falls back to the shared root favicon).
        p = await _final_path(hr, H, "/favicon.ico")
        check("a missing host path (favicon) keeps the original (default-root fallback)",
              p == "/favicon.ico", "got %s" % p)
        # a reserved API path is never touched.
        p = await _final_path(hr, H, "/rpc")
        check("a reserved path (/rpc) is never rewritten", p == "/rpc", "got %s" % p)
        # the apex host maps to the default root → nothing rewritten.
        p = await _final_path(hr, "akashicarchives.net", "/lib/plotly-2.27.0.min.js")
        check("apex host does not rewrite (default root)", p == "/lib/plotly-2.27.0.min.js", "got %s" % p)

    asyncio.run(run())

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("RESULT: PASS — per-host rewriting is path-aware: shared mounts (/lib) and missing host "
          "paths (favicon) keep the original path, while the host's own pages still reroute.")
    sys.exit(0)


if __name__ == "__main__":
    main()
