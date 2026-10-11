#!/usr/bin/env python3
"""
A22 — provider 429 back-off in llm_provider.

A persistent HTTP 429 on a free tier (quota / rate cap) means "stop calling". This eval drives
`llm_provider.generate` with a mocked HTTP layer and checks: a 429 arms a per-provider back-off; while
back off, calls are SUPPRESSED without any HTTP request and `available()` is False; `Retry-After` is
honoured when present, else the delay is exponential (60 s → 1 h) and grows per consecutive 429; and a
successful turn clears the back-off. The API key is never logged (handled by _redact + no key in test).

R8: the back-off survives a RESTART. A 429 persists `{provider, since, until, step}` through an injected
durable store (the shared-nucleus vault in production); a boot inside a still-live window inherits it on
first use WITHOUT calling the provider, keeping `since` stable so the station's standby line is unchanged.

Run:  python test/llm_backoff_eval.py     (exit 0 = all pass)
"""
import email.message
import os
import sys
import time
import urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _http_error(code, retry_after=None):
    hdrs = email.message.Message()
    if retry_after is not None:
        hdrs["Retry-After"] = str(retry_after)
    return urllib.error.HTTPError("https://x/v1/chat/completions", code, "Too Many Requests", hdrs, None)


def main():
    import lib.akasha.workbench.llm_provider as lp
    os.environ["AKASHA_MISTRAL_KEY"] = "test-key-never-logged"
    lp._BACKOFF.clear(); lp._BACKOFF_STEP.clear()

    calls = {"n": 0}

    def raise_429(*a, **k):
        calls["n"] += 1
        raise _http_error(429)

    lp._http_json = raise_429

    # ── first 429 arms the back-off (exponential floor 60 s), returns None ──
    out = lp.generate("mistral", "", "sys", "user")
    check("a 429 returns None (caller degrades)", out is None)
    check("the first 429 arms a 60 s exponential back-off",
          58 <= lp._backoff_remaining("mistral") <= 60, str(lp._backoff_remaining("mistral")))
    check("the endpoint was called exactly once so far", calls["n"] == 1, str(calls["n"]))

    # ── while backed off, calls are SUPPRESSED (no HTTP), available() is False ──
    out = lp.generate("mistral", "", "sys", "user")
    check("a call during back-off is suppressed without an HTTP request",
          out is None and calls["n"] == 1, str(calls["n"]))
    check("available() reports the backed-off provider as unavailable",
          lp.available("mistral") is False)

    # ── exponential growth per consecutive 429 (clear the deadline, force another 429) ──
    lp._BACKOFF["mistral"] = 0.0                       # deadline passed → next call reaches HTTP
    lp.generate("mistral", "", "sys", "user")
    check("a second consecutive 429 grows the back-off toward the cap (≈120 s)",
          118 <= lp._backoff_remaining("mistral") <= 120, str(lp._backoff_remaining("mistral")))
    check("the endpoint was reached again for the second 429", calls["n"] == 2, str(calls["n"]))

    # ── Retry-After is honoured when the server sends one ──
    lp._BACKOFF.clear(); lp._BACKOFF_STEP.clear()
    def raise_429_ra(*a, **k):
        raise _http_error(429, retry_after=300)
    lp._http_json = raise_429_ra
    lp.generate("mistral", "", "sys", "user")
    check("Retry-After (300 s) is honoured over the exponential schedule",
          298 <= lp._backoff_remaining("mistral") <= 300, str(lp._backoff_remaining("mistral")))

    # ── a successful turn clears the back-off ──
    lp._BACKOFF["mistral"] = 0.0                       # let the next call through
    def ok_turn(url, body, headers, timeout=60):
        return {"choices": [{"message": {"content": "hello from the model"}}]}
    lp._http_json = ok_turn
    out = lp.generate("mistral", "", "sys", "user")
    check("a successful turn returns the text", out == "hello from the model", repr(out))
    check("a success clears the back-off (provider usable again)",
          lp._backoff_remaining("mistral") == 0 and "mistral" not in lp._BACKOFF)

    # ── a non-429 HTTP error does NOT arm the back-off ──
    lp._BACKOFF.clear(); lp._BACKOFF_STEP.clear()
    def raise_500(*a, **k):
        raise _http_error(500)
    lp._http_json = raise_500
    out = lp.generate("mistral", "", "sys", "user")
    check("a non-429 HTTP error returns None but does NOT arm a back-off",
          out is None and "mistral" not in lp._BACKOFF)

    # ── R8: a restart INSIDE a back-off window does NOT call the provider ──
    # A 429 arms the back-off and persists {provider, since, until, step} through the injected durable
    # store (in production: the shared-nucleus vault). A restart = process memory wiped, the store
    # reinstalled at boot. The inherited window must suppress the very first call after boot — no HTTP.
    lp._BACKOFF.clear(); lp._BACKOFF_STEP.clear()
    getattr(lp, "_BACKOFF_SINCE", {}).clear()
    _vault = {}                                           # stands in for the nucleus vault
    lp.set_backoff_store(load=lambda: dict(_vault),
                         save=lambda d: _vault.clear() or _vault.update(d))
    calls2 = {"n": 0}
    def raise_429_persist(*a, **k):
        calls2["n"] += 1
        raise _http_error(429, retry_after=300)
    lp._http_json = raise_429_persist
    lp.generate("mistral", "", "sys", "user")            # arms + persists (until ≈ now+300)
    check("R8: the back-off state is persisted to the durable store on a 429",
          "mistral" in _vault and _vault["mistral"].get("until", 0) > 0, str(_vault))
    since_before = lp.backoff_since("mistral")
    check("R8: the window records a stable `since`", since_before > 0, str(since_before))

    # R8 (§3.3) — 3×429 within ONE window keep ONE `since`: the first 429 opens the window and stamps
    # `since`; each further 429 while the window is still live GROWS the back-off (60→120→240) but does
    # NOT reset `since`, so the standby line reads one continuous window, not three restarts. Driven on
    # a fresh provider key so it is isolated from the mistral state above.
    lp._BACKOFF.pop("gemini", None); lp._BACKOFF_STEP.pop("gemini", None)
    lp._BACKOFF_SINCE.pop("gemini", None)
    lp._enter_backoff("gemini")                              # 1st 429 — opens the window
    _g_since = lp.backoff_since("gemini")
    _g_step1 = lp._BACKOFF_STEP.get("gemini")
    lp._enter_backoff("gemini")                              # 2nd 429 — same window
    lp._enter_backoff("gemini")                              # 3rd 429 — same window
    _g_step3 = lp._BACKOFF_STEP.get("gemini")
    check("R8 (§3.3) three consecutive 429s keep ONE `since` (one window, not three)",
          abs(lp.backoff_since("gemini") - _g_since) < 1e-6 and _g_since > 0,
          f"{_g_since} -> {lp.backoff_since('gemini')}")
    check("R8 (§3.3) … while each further 429 grows the back-off (60 → 240)",
          _g_step1 == 60.0 and _g_step3 == 240.0, f"step {_g_step1} → {_g_step3}")

    # R8 (seed A slice 2) — the window LAPSING does not end the refusal. A provider that 429s all
    # night is retried after each window expires; `_enter_backoff` used to re-stamp `since` whenever
    # the previous deadline had passed (`if not already`), so the standby line walked forward
    # (04:09Z → 04:41Z → 05:14Z) and claimed the outage had just begun. Only a SUCCESS ends it.
    lp._BACKOFF["gemini"] = time.time() - 1.0            # the window has lapsed; the refusal has not
    lp._enter_backoff("gemini")                          # the retry is refused again
    check("R8: a refusal that CONTINUES past the window keeps its original `since` — only a success "
          "ends it", abs(lp.backoff_since("gemini") - _g_since) < 1e-6,
          f"{_g_since} -> {lp.backoff_since('gemini')}")
    check("R8: … and the deadline still advances (until/step move, `since` does not)",
          lp.backoff_seconds("gemini") > 0, str(lp.backoff_seconds("gemini")))
    lp._clear_backoff("gemini")
    lp._enter_backoff("gemini")                          # a NEW outage after a success starts fresh
    check("R8: a new outage AFTER a success stamps a new `since`",
          lp.backoff_since("gemini") > _g_since,
          f"{_g_since} -> {lp.backoff_since('gemini')}")
    lp._clear_backoff("gemini")

    # simulate a RESTART: wipe process memory, reinstall the store over the SAME vault, reload
    lp._BACKOFF.clear(); lp._BACKOFF_STEP.clear(); lp._BACKOFF_SINCE.clear()
    lp._BACKOFF_LOADED = False
    lp.set_backoff_store(load=lambda: dict(_vault),
                         save=lambda d: _vault.clear() or _vault.update(d))
    lp.load_persisted_backoff()                           # boot: inherit the still-live window
    check("R8: the inherited window is re-armed after the restart (no reset)",
          lp._in_backoff("mistral") is True, str(lp._backoff_remaining("mistral")))
    calls2["n"] = 0
    def must_not_call(*a, **k):
        calls2["n"] += 1
        raise AssertionError("provider called inside an inherited back-off window")
    lp._http_json = must_not_call
    out = lp.generate("mistral", "", "sys", "user")       # first call after boot
    check("R8: a restart inside a back-off window does not call the provider",
          out is None and calls2["n"] == 0, str(calls2["n"]))
    check("R8: the `since` is unchanged across the restart (standby line stable)",
          abs(lp.backoff_since("mistral") - since_before) < 1.0,
          f"{since_before} -> {lp.backoff_since('mistral')}")

    # an EXPIRED window in the store is NOT inherited (and never calls on load)
    lp._BACKOFF.clear(); lp._BACKOFF_STEP.clear(); lp._BACKOFF_SINCE.clear()
    _vault.clear()
    _vault["mistral"] = {"until": 1.0, "step": 60.0, "since": 0.5}   # long past
    lp._BACKOFF_LOADED = False
    lp.set_backoff_store(load=lambda: dict(_vault),
                         save=lambda d: _vault.clear() or _vault.update(d))
    lp.load_persisted_backoff()
    check("R8: an expired persisted window is not inherited",
          lp._in_backoff("mistral") is False)

    lp.set_backoff_store(load=lambda: {}, save=lambda d: None)       # detach the store
    lp._BACKOFF_LOADED = True
    os.environ.pop("AKASHA_MISTRAL_KEY", None)
    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("RESULT: PASS — a 429 arms a per-provider back-off (Retry-After honoured, else exponential "
          "60 s→1 h, growing per consecutive 429); backed-off calls are suppressed with no HTTP and "
          "available() is False; a success clears it; a non-429 error never arms it; and (R8) the "
          "back-off is persisted and inherited across a restart — a boot inside the window does not "
          "call the provider and keeps `since` stable.")
    sys.exit(0)


if __name__ == "__main__":
    main()
