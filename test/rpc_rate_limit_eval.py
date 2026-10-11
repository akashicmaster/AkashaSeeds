#!/usr/bin/env python3
"""
F39-P3 — crawler policy at the HTTP edge: per-IP RPC rate limit + Retry-After on the busy error.

robots.txt Crawl-delay asks polite crawlers to pace; the P1a admission cap bounds the daemon once a
request is in. This closes the third side: an IMPOLITE crawler is shed at the HTTP edge (a per-IP
token bucket) BEFORE it reaches the kernel, and both the rate-limit refusal AND the admission busy
error return a real 429 with a Retry-After header so a well-behaved client backs off instead of
hammering a 200.

Run:  python test/rpc_rate_limit_eval.py   (exit 0 = all pass; SKIP if fastapi/starlette absent)
"""
import hashlib
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
os.environ["AKASHA_BACKEND"] = "silica"
os.environ["AKASHA_RPC_RATE_PER_MIN"] = "5"          # tiny so a few calls trip it
os.environ["AKASHA_TRUST_XFF"] = "1"

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def main():
    try:
        import fastapi as fastapi_mod
        from starlette.testclient import TestClient
    except Exception as exc:
        print("SKIP — fastapi/starlette not available:", exc); sys.exit(0)

    import api.portals.asgi as asgi
    from lib.akasha.kernel import KernelDispatcher
    from api.gateway import AkashaGateway

    # ── unit: the token bucket ──
    lim = asgi._IPRateLimiter(per_min=5)
    now = 1000.0
    allowed = sum(1 for _ in range(5) if lim.check("1.2.3.4", now)[0])
    ok6, wait6 = lim.check("1.2.3.4", now)
    check("P3 token bucket admits `per_min` then refuses", allowed == 5 and ok6 is False,
          f"allowed={allowed} sixth={ok6} retry={wait6}s")
    check("P3 refusal carries a Retry-After (seconds)", isinstance(wait6, int) and wait6 >= 1, f"{wait6}s")
    check("P3 a different IP is independent", lim.check("9.9.9.9", now)[0] is True)
    check("P3 bucket refills over time", lim.check("1.2.3.4", now + 60)[0] is True)
    check("P3 disabled limiter (0) always allows",
          asgi._IPRateLimiter(0).check("1.2.3.4", now)[0] is True)

    # ── integration: /rpc returns 429 + Retry-After under the limit ──
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="rl_"))
    gw = AkashaGateway(kernel_client=k)
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "internal")
    asgi._RPC_RATE_LIMITER = asgi._IPRateLimiter(5)   # fresh bucket for the app
    app = asgi._build_app(fastapi_mod, gw)
    client = TestClient(app)

    body = {"jsonrpc": "2.0", "method": "sys.ping", "params": {}, "id": "p"}
    hdr = {"X-Forwarded-For": "203.0.113.7"}
    codes = [client.post("/rpc", json=body, headers=hdr).status_code for _ in range(8)]
    got429 = next((r for r in [client.post("/rpc", json=body, headers=hdr)] if True), None)
    # after 5 allowed, subsequent are 429
    n429 = sum(1 for c in codes if c == 429)
    check("P3 /rpc rate-limits a hammering IP (429 after the budget)", n429 >= 1, f"codes={codes}")
    # find a 429 response and check the header
    r429 = None
    for _ in range(6):
        rr = client.post("/rpc", json=body, headers=hdr)
        if rr.status_code == 429:
            r429 = rr; break
    check("P3 429 carries a Retry-After header",
          r429 is not None and r429.headers.get("Retry-After") is not None,
          (r429.headers.get("Retry-After") if r429 else "no 429"))
    check("P3 a DIFFERENT IP is not rate-limited by another IP's burst",
          client.post("/rpc", json=body, headers={"X-Forwarded-For": "198.51.100.9"}).status_code == 200)

    # ── integration: the P1a admission busy error surfaces as 429 + Retry-After ──
    asgi._RPC_RATE_LIMITER = asgi._IPRateLimiter(0)    # disable rate limit to isolate admission
    import lib.akasha.kernel as K
    K._DIVE_ADMISSION = K._DiveAdmission()
    held = [K._DIVE_ADMISSION.acquire() for _ in range(K._DIVE_ADMISSION.cap)]
    import threading
    for _ in range(K._DIVE_ADMISSION.queue):
        threading.Thread(target=K._DIVE_ADMISSION.acquire, daemon=True).start()
    import time as _t
    _t.sleep(0.05)
    gk = (k.dispatch({"jsonrpc": "2.0", "method": "session.guest.create",
                      "params": {"data": {}}, "id": "gk"}, "network").get("result") or {}).get("binding_key")
    rv = client.post("/rpc", json={"jsonrpc": "2.0", "method": "view",
                                   "params": {"session_token": gk, "data": {"id": "apple"}}, "id": "v"},
                     headers={"X-Forwarded-For": "203.0.113.50"})
    check("P3 admission busy error surfaces as HTTP 429 + Retry-After",
          rv.status_code == 429 and rv.headers.get("Retry-After") is not None
          and (rv.json().get("error") or {}).get("code") == -32029,
          f"status={rv.status_code} retry={rv.headers.get('Retry-After')}")

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("ALL PASS — the RPC edge rate-limits per IP (token bucket, independent per IP, refills) and "
          "both the rate-limit refusal and the P1a admission busy error return HTTP 429 + Retry-After.")
    sys.exit(0)


if __name__ == "__main__":
    main()
