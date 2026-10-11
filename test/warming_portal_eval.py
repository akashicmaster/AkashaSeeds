#!/usr/bin/env python3
"""
Warming-portal deferred-startup eval (F60 §5.5) — the semcache warm loop that NEVER started.

Under Lever C the port is bound by a warming holder (`_warming_asgi`) that answers the ASGI
`lifespan` protocol itself, then swaps in the live app (`_build_app`, returned as a `HostReroute`
wrapper) on a later request. Two bugs kept the warm loop dead:

  1. `_start_deferred_startups` read `app.state.deferred_startups`, but the live app is a
     `HostReroute` with NO `.state` — the list read empty and nothing was scheduled (§5.1).
  2. The build-thread scheduling could run before uvicorn's loop existed / after the wrong order,
     so nothing started (§5.2 — start from the loop thread on the first request after the swap).

This pins the fix: BOTH orderings (lifespan→swap→request and swap→lifespan→request) schedule the
deferred warm task EXACTLY ONCE, and a `HostReroute`-wrapped app yields its deferred list.

Run:  python test/warming_portal_eval.py     (exit 0 = all pass)
"""
import asyncio
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


class _State:
    pass


class FakeApp:
    """A minimal ASGI app carrying a deferred-startup list on `.state`, like the FastAPI app."""
    def __init__(self, box):
        self.state = _State()
        self.state.deferred_startups = [self._warm]
        self._box = box

    async def _warm(self):
        self._box["n"] += 1

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "http":
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b"ok"})


async def _drive_http(app):
    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}
    sent = []
    async def send(m):
        sent.append(m)
    await app({"type": "http", "path": "/", "headers": []}, receive, send)


async def _drive_lifespan_startup(app):
    """Send lifespan.startup, wait for complete, then shutdown so the handler returns."""
    msgs = [{"type": "lifespan.startup"}, {"type": "lifespan.shutdown"}]
    got = []
    async def receive():
        return msgs.pop(0) if msgs else {"type": "lifespan.shutdown"}
    async def send(m):
        got.append(m["type"])
    await app({"type": "lifespan"}, receive, send)
    return got


async def scenario(order):
    import api.portals.asgi as A
    box = {"n": 0}
    holder = {"app": None, "error": None, "loop": None, "warm_started": False}
    warming = A._warming_asgi(holder)
    wrapped = A.HostReroute(FakeApp(box), "/tmp")

    if order == "lifespan_first":
        await _drive_lifespan_startup(warming)      # captures holder["loop"]
        holder["app"] = wrapped                      # swap
        await _drive_http(warming)                   # first request → first-scope start
        await _drive_http(warming)                   # second request → must NOT start again
    else:  # swap_first
        holder["app"] = wrapped                      # swap BEFORE any lifespan
        await _drive_http(warming)                   # first request → first-scope start (get_running_loop)
        await _drive_http(warming)
    await asyncio.sleep(0.05)                        # let the scheduled warm task run
    return box["n"]


def main():
    import api.portals.asgi as A

    # (0) a HostReroute-wrapped app yields its deferred list via the unwrap walk.
    box = {"n": 0}
    wrapped = A.HostReroute(FakeApp(box), "/tmp")
    inner = A._unwrap_app(wrapped)
    check("HostReroute unwraps to the app carrying .state.deferred_startups",
          hasattr(inner, "state") and len(getattr(inner.state, "deferred_startups", [])) == 1,
          "unwrapped=%s" % type(inner).__name__)

    n1 = asyncio.run(scenario("lifespan_first"))
    check("lifespan → swap → request: warm task scheduled EXACTLY once", n1 == 1, "ran=%d" % n1)

    n2 = asyncio.run(scenario("swap_first"))
    check("swap → lifespan-less → request: warm task scheduled EXACTLY once", n2 == 1, "ran=%d" % n2)

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("RESULT: PASS — the warming portal starts the deferred warm task exactly once in both swap "
          "orderings, and HostReroute yields its deferred list (the loop can no longer stay dead).")
    sys.exit(0)


if __name__ == "__main__":
    main()
