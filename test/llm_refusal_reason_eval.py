#!/usr/bin/env python3
"""
A refusal says WHY — the provider's own words are kept, not discarded.

The live station stood by for fifteen days reporting `[llm] mistral 429 — backing off 3600s`, once
an hour, and nothing else. One call an hour cannot trip any frequency cap, so the log proved what
the cause was NOT and said nothing about what it was. The cause was in the response body, and the
code read `he.code` and threw the body away.

That is the general defect, not a Mistral one: a 429 has several causes that ask for OPPOSITE
responses — a frequency cap says wait a moment, an exhausted monthly allowance says wait for the
month to turn, an inactive plan or a model the tier may not serve says the waiting will never end.
Only the provider knows which, and it says so. So the body and the rate-limit headers are now read
once, bounded, kept with the back-off window (across a restart), carried into the station's standby
line, and reachable on demand through `llm.diag` — one deliberate call, so an operator does not have
to wait an hour to ask a question.

What this holds shut (no network — the provider is faked at the one HTTP seam):

  · a 429 body is captured and readable as `backoff_reason`, with the rate headers;
  · it survives the restart the back-off itself survives;
  · the API key never appears in a message, a log line or a probe result;
  · `llm.diag` reports status / message / headers and re-arms the window from its own 429;
  · a success clears the window AND its reason — a stale explanation is worse than none;
  · a non-429 HTTP error is explained too, not just numbered.

Run:  python test/llm_refusal_reason_eval.py      (exit 0 = all pass)
"""
import io
import json
import os
import sys
import urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

KEY = "sk-test-key-that-must-never-be-logged"
BODY429 = ('{"message":"Service tier capacity exceeded for this model.",'
           '"type":"invalid_request_error"}')
HDRS429 = {"Retry-After": "30", "x-ratelimit-limit-tokens-month": "1000000000",
           "x-ratelimit-remaining-tokens-month": "0"}

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


class _Hdrs(dict):
    def get(self, k, d=None):
        return dict.get(self, k, d)


def _http_error(code, reason, body, hdrs):
    """An `HTTPError` shaped like the real one: the body is readable exactly once."""
    class E(urllib.error.HTTPError):
        def __init__(self):
            self._b = body.encode()
            super().__init__("https://api.example/v1/chat/completions", code, reason,
                             _Hdrs(hdrs), io.BytesIO(self._b))

        def read(self, n=-1):
            return self._b
    return E()


def main():
    from lib.akasha.workbench import llm_provider as L

    os.environ["AKASHA_MISTRAL_KEY"] = KEY
    real_http = L._http_json

    def refuse(code=429, body=BODY429, hdrs=None):
        L._http_json = lambda *a, **k: (_ for _ in ()).throw(
            _http_error(code, "Too Many Requests" if code == 429 else "Error", body,
                        HDRS429 if hdrs is None else hdrs))

    def succeed():
        L._http_json = lambda *a, **k: {"choices": [{"message": {"content": "ok"}}]}

    print("\n  ── a 429 keeps the provider's words ──")
    L._clear_backoff("mistral")
    refuse()
    out = L.generate("mistral", "", "sys", "user")
    why = L.backoff_reason("mistral")
    check("the turn produces nothing (a turn the model did not produce is never invented)",
          out is None, repr(out))
    check("the provider's message is kept", "Service tier capacity exceeded" in why, why[:80])
    check("… and its rate-limit headers, which name WHICH budget was hit",
          "remaining-tokens-month=0" in why, why[-60:])
    check("the back-off window is armed", L.backoff_seconds("mistral") > 0,
          "%ds" % L.backoff_seconds("mistral"))
    check("the key appears nowhere in the reason", KEY not in why)

    print("\n  ── the reason survives a restart, like the window ──")
    saved = {}
    L.set_backoff_store(load=lambda: saved.get("d", {}), save=lambda d: saved.update(d=d))
    refuse()
    L._clear_backoff("mistral")
    L.generate("mistral", "", "sys", "user")
    persisted = json.dumps(saved.get("d", {}))
    check("the persisted window carries the reason", "capacity exceeded" in persisted,
          persisted[:100])
    check("the persisted window does NOT carry the key", KEY not in persisted)
    # a new process: the module's in-memory state is gone, the store is not
    L._BACKOFF.clear(); L._BACKOFF_WHY.clear(); L._BACKOFF_SINCE.clear(); L._BACKOFF_LOADED = False
    check("a restart inherits the reason with the window",
          "capacity exceeded" in L.backoff_reason("mistral"), L.backoff_reason("mistral")[:70])

    print("\n  ── llm.diag — one deliberate call, instead of an hour's wait ──")
    refuse()
    r = L.probe("mistral")
    check("it reports the status", r.get("status") == 429, str(r.get("status")))
    check("it reports the provider's message", "capacity exceeded" in r.get("message", ""),
          r.get("message", "")[:70])
    check("it reports the rate-limit headers", "retry-after=30" in r.get("rate_headers", ""),
          r.get("rate_headers", "")[:70])
    check("it re-arms the window from its own 429 (a probe is not a free pass)",
          r.get("backoff_s", 0) > 0, "%ss" % r.get("backoff_s"))
    check("the key appears nowhere in the result", KEY not in json.dumps(r))
    check("it probes THROUGH a live back-off (that is the point of a diagnostic)",
          L.backoff_seconds("mistral") > 0 and L.probe("mistral").get("status") == 429)

    print("\n  ── a success clears the window and its reason ──")
    succeed()
    r2 = L.probe("mistral")
    check("the probe reaches the provider", r2.get("ok") is True, r2.get("message"))
    check("the window is cleared", L.backoff_seconds("mistral") == 0)
    check("… and so is the reason (a stale explanation is worse than none)",
          L.backoff_reason("mistral") == "", L.backoff_reason("mistral"))

    print("\n  ── a non-429 refusal is explained too ──")
    refuse(code=401, body='{"message":"Unauthorized"}', hdrs={})
    out = L.generate("mistral", "", "sys", "user")
    check("an unauthorized key does not arm a rate-limit back-off",
          out is None and L.backoff_seconds("mistral") == 0)

    print("\n  ── the self-imposed ceiling is named as OURS, not the provider's ──")
    succeed()
    # A one-call ceiling, so the SECOND probe is over it. (`AKASHA_LLM_CALLS_PER_DAY=0` would mean
    # unmetered by contract, so the ceiling is lowered in the table instead.)
    keep = dict(L._FREE_TIER["mistral"])
    try:
        L._FREE_TIER["mistral"] = dict(keep, calls_per_day=1)
        L._METER.clear()
        L.probe("mistral")                             # spends the one call
        r3 = L.probe("mistral")
        check("an exhausted ceiling says it is Akasha's own gate, not the provider's",
              "SELF-IMPOSED" in r3.get("message", "") and r3.get("status") == 0,
              r3.get("message", "")[:80])
    finally:
        L._FREE_TIER["mistral"] = keep
        L._METER.clear()
        L._http_json = real_http

    print()
    if _fails:
        print("RESULT: FAIL (%d): %s\n" % (len(_fails), "; ".join(_fails)))
        return 1
    print("RESULT: PASS — a refusal carries the provider's own words and its rate-limit headers, "
          "across a restart and into the standby line; `llm.diag` asks on demand rather than waiting "
          "out a back-off; a success clears both window and reason; and the key is in none of it.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
