#!/usr/bin/env python3
"""
F47 Part 1.1 — the daemon's IPC server is a FIXED worker pool draining a BOUNDED queue.

The stable era served public reads from the portal's own engine; the thin-client change forwards
every read into the single writer, whose old IPC server spawned ONE UNBOUNDED THREAD PER CONNECTION.
A bot storm holding tens of connections stacked tens of GIL-contending threads (3 concurrent renders
were already slower than serial) and their in-flight state was the leading RSS-climb suspect. This
eval proves the replacement: the daemon's thread census is CONSTANT by construction (== pool size,
regardless of how many clients connect), and an overflow of the bounded accept queue is refused fast
with a JSON busy line (-32029), never by spawning another thread.

Directive 2026-10-03 §6 — the saturation is STAGED, not timed: both workers held (the stub counts
in-flight dispatches), then the queue full (`stats().queued == 2`), then four overflow clients; each
stage waits for its state, so a loaded host cannot make it pass or fail. Exact counts: every overflow
client gets -32029 — which found a client defect: a refused client still sending its request failed
the send (`Broken pipe`) and reported the daemon UNREACHABLE without reading the busy line already in
its buffer. `SocketGateway` now reads that line first.

Run:  python test/ipc_pool_eval.py   (exit 0 = all pass)
"""
import os
import sys
import tempfile
import threading
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

# small pool so saturation is easy and deterministic
os.environ["AKASHA_IPC_WORKERS"] = "2"
os.environ["AKASHA_IPC_QUEUE"] = "2"

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


class StubGW:
    """A gateway whose 'slow' dispatch blocks until released — so a worker stays occupied and the
    pool/queue saturate deterministically. Everything else returns immediately."""
    def __init__(self):
        self.release = threading.Event()
        self.in_flight = 0                     # slow dispatches a worker is holding right now

    def dispatch(self, payload, trust="local"):
        m = payload.get("method") if isinstance(payload, dict) else ""
        if m == "slow":
            self.in_flight += 1
            self.release.wait(timeout=120)
        return {"jsonrpc": "2.0", "result": {"ok": True, "m": m}, "id": payload.get("id")}


def _until(cond, ceiling=60.0):
    """Wait for a STATE, not for a time (directive 2026-10-03 §6: this eval failed under the parallel
    suite because a fixed 2 s was not enough for 8 clients to connect on a loaded host). The ceiling
    is only for a server that never reaches the state — that is a failure, a slow host is not."""
    dl = time.time() + ceiling
    while time.time() < dl:
        if cond():
            return True
        time.sleep(0.05)
    return cond()


def main():
    from api.portals.cell_ipc import CellIPCServer, SocketGateway, TRUST_LOCAL

    base = tempfile.mkdtemp(prefix="ipc_pool_")
    gw = StubGW()
    server = CellIPCServer(gw, base, trust=TRUST_LOCAL)
    server.start()
    try:
        # thread census is bounded to the pool the instant it starts, before any traffic
        workers = [t for t in threading.enumerate() if t.name.startswith("cell-ipc-w")]
        check("1.1 fixed pool spawns exactly AKASHA_IPC_WORKERS worker threads",
              len(workers) == 2, "workers=%d" % len(workers))

        # ── saturate, STAGED: pool=2 + queue=2, then the overflow — each stage waits for its state ──
        results = [None] * 8

        def _fire(i):
            sg = SocketGateway(base, timeout=120)
            try:
                results[i] = sg.dispatch({"jsonrpc": "2.0", "method": "slow",
                                          "params": {}, "id": "s%d" % i})
            except Exception as exc:
                results[i] = {"error": {"code": -1, "message": str(exc)}}
            finally:
                sg.close()

        threads = [threading.Thread(target=_fire, args=(i,), daemon=True) for i in range(8)]
        for t in threads[:2]:                  # stage 1: occupy both workers
            t.start()
        check("1.1 (stage 1) both pool workers are held by a slow dispatch",
              _until(lambda: gw.in_flight == 2), "in_flight=%d" % gw.in_flight)
        for t in threads[2:4]:                 # stage 2: fill the queue
            t.start()
        check("1.1 (stage 2) the accept queue is full (queued == AKASHA_IPC_QUEUE)",
              _until(lambda: server.stats().get("queued") == 2), "stats=%s" % server.stats())
        for t in threads[4:]:                  # stage 3: the overflow — refused, answered at once
            t.start()
        _until(lambda: all(not t.is_alive() for t in threads[4:]))

        # the daemon's own counter is the authoritative proof an overflow was refused (not threaded)
        st = server.stats()
        check("1.1 accept-queue overflow is REFUSED (not a new thread)", st.get("refused", 0) >= 4,
              "stats=%s" % st)

        # thread census is STILL just the pool — 8 concurrent clients did NOT create 8 handler threads
        workers_now = [t for t in threading.enumerate() if t.name.startswith("cell-ipc-w")]
        conn_threads = [t for t in threading.enumerate() if t.name == "cell-ipc-conn"]
        check("1.1 thread census stays CONSTANT under 8 concurrent clients",
              len(workers_now) == 2 and len(conn_threads) == 0,
              "workers=%d legacy_conn_threads=%d" % (len(workers_now), len(conn_threads)))

        # release the blocked dispatches; the served/queued ones complete
        gw.release.set()
        for t in threads:
            t.join(timeout=120)

        busy = sum(1 for r in results
                   if isinstance(r, dict) and (r.get("error") or {}).get("code") == -32029)
        served = sum(1 for r in results
                     if isinstance(r, dict) and (r.get("result") or {}).get("ok"))
        check("1.1 every overflow client (4) saw the -32029 busy line", busy == 4,
              "busy=%d served=%d" % (busy, served))
        check("1.1 the admitted clients (2 served + 2 queued) all got real responses", served == 4,
              "served=%d" % served)

        # ── a normal request still works once the pool is free ──
        gw2 = SocketGateway(base, timeout=5)
        r = gw2.dispatch({"jsonrpc": "2.0", "method": "sys.ping", "params": {}, "id": "p"})
        gw2.close()
        check("1.1 a normal request is served by the freed pool",
              isinstance(r, dict) and (r.get("result") or {}).get("ok"), str(r)[:120])

        # ── the module-level stats hook the health line reads ──
        import api.portals.cell_ipc as ipc_mod
        ss = ipc_mod.server_stats()
        check("3.1 server_stats() exposes pool/queue/refused for the health line",
              set(ss) >= {"pool", "queue_max", "refused", "served"}, str(ss))
    finally:
        server.stop()

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("ALL PASS — the IPC server is a fixed pool over a bounded queue: the daemon thread census "
          "is constant under load (no thread-per-connection), overflow is refused fast with -32029, "
          "and normal requests still serve.")
    sys.exit(0)


if __name__ == "__main__":
    main()
