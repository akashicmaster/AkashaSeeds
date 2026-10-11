#!/usr/bin/env python3
"""
F39-P1a — admission control on dive-bearing serving requests.

Crawler traffic drives many CONCURRENT concept-space / dive renders; each builds a neighbourhood in
RAM, so daemon RSS scales with the request arrival rate and OOM-kills the writer. Admission bounds
CONCURRENCY: `cap` dives run at once, a small queue absorbs bursts, and beyond that a request is
refused FAST with a millisecond Retry-After — never a 60 s hang, never a death. Internal/local calls
bypass the gate (they must never wait on a slot they might hold).

Run:  python test/dive_admission_eval.py   (exit 0 = all pass)
"""
import hashlib
import os
import sys
import tempfile
import threading
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
os.environ["AKASHA_BACKEND"] = "silica"
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "test"))

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def main():
    import lib.akasha.kernel as K

    # ── unit: the bounded controller ──
    os.environ["AKASHA_DIVE_ADMIT"] = "1"
    os.environ["AKASHA_DIVE_QUEUE"] = "1"
    os.environ["AKASHA_DIVE_WAIT_MS"] = "150"
    adm = K._DiveAdmission()
    ok1, _ = adm.acquire()
    check("P1a cap slot admits the first request", ok1 is True)

    # a second caller WAITS (holds the one queue slot) — start it in a thread and let it block
    waiting_started = threading.Event()
    result = {}

    def _waiter():
        waiting_started.set()
        result["r"] = adm.acquire()          # blocks up to wait_ms, then refused (slot never freed)
    tw = threading.Thread(target=_waiter, daemon=True)
    tw.start()
    waiting_started.wait(1.0)
    time.sleep(0.03)                          # let it enter the sem wait (waiting == 1 == queue)

    # a THIRD caller: queue is full → refused IMMEDIATELY (fast, ms retry)
    t0 = time.time()
    ok3, retry3 = adm.acquire()
    dt_ms = (time.time() - t0) * 1000
    check("P1a queue-full request is refused", ok3 is False, f"retry_after_ms={retry3}")
    check("P1a refusal is FAST (< 50 ms), not a long wait", dt_ms < 50, f"{dt_ms:.1f}ms")
    check("P1a refusal carries a millisecond Retry-After", isinstance(retry3, int) and retry3 > 0,
          f"retry={retry3}")

    tw.join(1.0)
    check("P1a the queued waiter is bounded (refused after wait_ms, never hangs)",
          result.get("r", (None,))[0] is False, str(result.get("r")))
    adm.release()

    # ── wiring: a NETWORK dive-bearing method is gated; LOCAL bypasses ──
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="adm_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "internal")
    k.dispatch({"jsonrpc": "2.0", "method": "w",
                "params": {"session_token": "admin", "data": {"content": "an apple"}}, "id": "w"}, "internal")
    # A guest binding key — the archives read path — so the NETWORK request authenticates (a bare
    # 'admin' over the network is correctly refused before admission is even reached).
    gk = (k.dispatch({"jsonrpc": "2.0", "method": "session.guest.create",
                      "params": {"data": {}}, "id": "gk"}, "network").get("result") or {}).get("binding_key")
    check("P1a guest binding key issued (network read path available)", bool(gk), str(gk)[:12])

    # Exhaust admission: hold cap + fill queue with blocked waiters, then dispatch a NETWORK view.
    K._DIVE_ADMISSION = K._DiveAdmission()     # fresh 1/1 controller (env still 1/1/150)
    held = []
    for _ in range(K._DIVE_ADMISSION.cap):
        held.append(K._DIVE_ADMISSION.acquire())      # occupy every slot
    fillers = []
    for _ in range(K._DIVE_ADMISSION.queue):
        ev = threading.Event()
        th = threading.Thread(target=lambda e=ev: (e.set(), K._DIVE_ADMISSION.acquire()), daemon=True)
        th.start(); ev.wait(1.0); fillers.append(th)
    time.sleep(0.05)                            # waiters settle into the queue

    r_net = k.dispatch({"jsonrpc": "2.0", "method": "view",
                        "params": {"session_token": gk, "data": {"id": "apple"}}, "id": "v"}, "network")
    err = r_net.get("error") or {}
    check("P1a NETWORK dive is refused when admission is exhausted (busy error)",
          err.get("code") == -32029 and (err.get("data") or {}).get("retry_after_ms", 0) > 0, str(err))

    # a LOCAL/internal dive is NOT gated — it bypasses admission entirely (no busy error)
    r_loc = k.dispatch({"jsonrpc": "2.0", "method": "view",
                        "params": {"session_token": "admin", "data": {"id": "apple"}}, "id": "v2"}, "local")
    check("P1a LOCAL/internal dive bypasses admission (never refused)",
          "error" not in r_loc or (r_loc.get("error") or {}).get("code") != -32029, str(r_loc.get("error")))

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("ALL PASS — dive-bearing NETWORK requests are admission-bounded: cap slots + a small queue, "
          "then a fast millisecond-Retry-After busy error; internal/local calls bypass. Concurrency "
          "(and thus RAM) is bounded regardless of arrival rate.")
    sys.exit(0)


if __name__ == "__main__":
    main()
