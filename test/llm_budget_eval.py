#!/usr/bin/env python3
"""
A53 — the free-tier BUDGET gate in llm_provider (the PROACTIVE half of the 429 back-off).

One API key is spent by every programme at once (the news station, a reading programme, any society's
auto-run). So the ceiling lives at the ONE leaf they all already go through — `llm_provider.generate` —
not in each caller: a programme that knows nothing about quotas is still governed, and adding a
programme cannot overspend the tier. This eval checks that gate:

  · a call is METERED before the request goes out (a request we sent is spent whether or not it answers)
  · at the ceiling, `generate` returns None with NO HTTP call, and `available()` is False
  · the ceiling is per UTC DAY (calls) and per UTC MONTH (estimated tokens), and rolls over
  · the host can raise/lower it by env (per-provider var wins over the global one); 0 = unmetered
  · the meter is DURABLE — a restart inside a spent day does not hand the budget back
  · calls are PACED to the provider's rate (~1 req/s) so a burst never earns the 429 back-off
  · a local provider (ollama) is never metered and never paced

And, since the station moved to a PAID tier (2026-09-19), the part that now bounds MONEY:

  · a DAILY TOKEN ceiling, because cost is per token — a call cap alone lets one fat day spend the
    whole month and leave the station silent for the rest of it
  · the shipped mistral ceiling holds the month under €10 even at the dearest price any public
    source quotes, and even if every token were charged at the dearer OUTPUT rate
  · …while still clearing the demand the studios actually declare, so the cap never starves the
    station in normal operation

Run:  python test/llm_budget_eval.py     (exit 0 = all pass)
"""
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def reset(lp, **env):
    lp._METER.clear()
    lp._NEXT_OK.clear()
    lp._BACKOFF.clear()
    lp._BACKOFF_STEP.clear()
    for k in [k for k in os.environ if k.startswith("AKASHA_LLM_")]:
        del os.environ[k]
    os.environ.update({k: str(v) for k, v in env.items()})


def main():
    import lib.akasha.workbench.llm_provider as lp
    os.environ["AKASHA_MISTRAL_KEY"] = "test-key-never-logged"
    calls = []

    def fake_http(url, body, headers, timeout=60):
        calls.append(url)
        return {"choices": [{"message": {"content": "one aired line."}}]}

    lp._http_json = fake_http
    # pacing off for the counting checks (its own check re-enables it)
    real_pace = lp._FREE_TIER["mistral"]["min_interval"]
    lp._FREE_TIER["mistral"]["min_interval"] = 0.0

    # ── metering + the ceiling ───────────────────────────────────────────────────────────────────
    reset(lp, AKASHA_LLM_MISTRAL_CALLS_PER_DAY=3, AKASHA_LLM_MISTRAL_TOKENS_PER_MONTH=0)
    print("\n  ── the daily call ceiling ──")
    outs = [lp.generate("mistral", "", "sys", "user") for _ in range(3)]
    check("calls under the ceiling go out and answer", all(outs) and len(calls) == 3,
          "http=%d" % len(calls))
    q = lp.quota("mistral")
    check("each call is metered (calls_today, calls_left)",
          q["calls_today"] == 3 and q["calls_left"] == 0, str(q["calls_today"]))
    n_before = len(calls)
    over = lp.generate("mistral", "", "sys", "user")
    check("at the ceiling generate() returns None with NO HTTP call",
          over is None and len(calls) == n_before, "http=%d" % (len(calls) - n_before))
    check("available() is False while the budget is spent", lp.available("mistral") is False)
    check("quota() reports exhausted", lp.quota("mistral")["exhausted"] is True)

    print("\n  ── the rollover IS the schedule ──")
    lp._METER["mistral"]["day"] = "1999-01-01"          # pretend the counters are yesterday's
    check("a new UTC day hands the daily allowance back",
          lp.available("mistral") is True and lp.quota("mistral")["calls_today"] == 0)
    reset(lp, AKASHA_LLM_MISTRAL_CALLS_PER_DAY=0, AKASHA_LLM_MISTRAL_TOKENS_PER_MONTH=40)
    lp.generate("mistral", "", "x" * 200, "y" * 200)     # ~100 estimated tokens in, over the 40 cap
    check("the monthly token estimate is metered and caps too",
          lp.quota("mistral")["tokens_month"] >= 40 and lp.available("mistral") is False,
          "tokens=%s" % lp.quota("mistral")["tokens_month"])
    lp._METER["mistral"]["month"] = "1999-01"
    check("a new UTC month hands the token allowance back", lp.available("mistral") is True)

    print("\n  ── who sets the ceiling ──")
    reset(lp, AKASHA_LLM_CALLS_PER_DAY=7, AKASHA_LLM_MISTRAL_CALLS_PER_DAY=2)
    check("the per-provider env var wins over the global one",
          lp.quota("mistral")["calls_per_day"] == 2, str(lp.quota("mistral")["calls_per_day"]))
    reset(lp, AKASHA_LLM_CALLS_PER_DAY=7)
    check("the global env var applies when there is no per-provider one",
          lp.quota("mistral")["calls_per_day"] == 7)
    reset(lp)
    check("with no env the built-in self-imposed default is in force",
          lp.quota("mistral")["calls_per_day"] == lp._FREE_TIER["mistral"]["calls_per_day"])
    reset(lp, AKASHA_LLM_MISTRAL_CALLS_PER_DAY=0, AKASHA_LLM_MISTRAL_TOKENS_PER_MONTH=0)
    for _ in range(5):
        lp.generate("mistral", "", "s", "u")
    check("0 = unmetered (a paid host is never held back)", lp.available("mistral") is True)

    print("\n  ── durability: a restart must not hand the budget back ──")
    # the store's save/load shape mirrors the kernel's vault (one key holding the whole dict)
    saved = {}
    lp.set_meter_store(load=lambda: dict(saved), save=lambda d: saved.clear() or saved.update(d))
    reset(lp, AKASHA_LLM_MISTRAL_CALLS_PER_DAY=2)
    lp._METER_LOADED = False
    lp.generate("mistral", "", "s", "u")
    lp.generate("mistral", "", "s", "u")
    check("the meter is persisted through the injected store",
          int((saved.get("mistral") or {}).get("calls", 0)) == 2, str(saved))
    lp._METER.clear()                                   # ← the restart
    lp._METER_LOADED = False
    check("a restart inherits the spend and stays at the ceiling",
          lp.available("mistral") is False and lp.quota("mistral")["calls_today"] == 2)
    lp.set_meter_store(load=lambda: {}, save=lambda d: None)

    print("\n  ── pacing (so a burst never earns the 429 back-off) ──")
    lp._FREE_TIER["mistral"]["min_interval"] = real_pace
    reset(lp, AKASHA_LLM_MISTRAL_CALLS_PER_DAY=0, AKASHA_LLM_MISTRAL_TOKENS_PER_MONTH=0)
    lp._PACE_WAIT_MAX = 30.0
    t0 = time.time()
    lp.generate("mistral", "", "s", "u")
    lp.generate("mistral", "", "s", "u")
    gap = time.time() - t0
    check("two consecutive calls are spaced by the provider's rate",
          gap >= real_pace * 0.9, "%.2fs apart (min_interval=%.2f)" % (gap, real_pace))
    lp._NEXT_OK["mistral"] = time.time() + 600.0        # a slot 10 min out
    lp._PACE_WAIT_MAX = 5.0
    n_before = len(calls)
    out = lp.generate("mistral", "", "s", "u")
    check("a caller is never blocked for a far-off slot — it degrades instead",
          out is None and len(calls) == n_before)
    lp._PACE_WAIT_MAX = 30.0

    print("\n  ── a local model is not a metered tier ──")
    reset(lp)
    check("ollama is unmetered and unpaced",
          lp.quota("ollama")["calls_per_day"] == 0 and lp.quota("ollama")["min_interval_s"] == 0.0)

    print("\n  ── the paid-tier ceiling: a day bounded in MONEY, not just in calls ──")
    lp._METER.clear()
    for v in list(os.environ):
        if v.startswith("AKASHA_LLM_"):
            del os.environ[v]
    lp._FREE_TIER["mistral"] = dict(lp._FREE_TIER["mistral"], calls_per_day=0, tokens_per_day=1000)
    calls = 0
    while not lp._over_budget("mistral") and calls < 50:
        lp._meter_record("mistral", 4000)      # ~1000 tokens of prompt
        calls += 1
    check("a daily TOKEN ceiling stops the day even with the call cap off",
          lp._over_budget("mistral") and calls <= 2, "calls until stop=%d" % calls)
    q = lp.quota("mistral")
    check("… and the operator surface reports the day's tokens and what is left",
          q.get("tokens_per_day") == 1000 and q.get("tokens_today") >= 1000
          and q.get("tokens_left_today") == 0, str({k: q[k] for k in
          ("tokens_today", "tokens_per_day", "tokens_left_today")}))
    check("the completion side counts against the DAY too, not only the month",
          (lambda before: (lp._meter_record_output("mistral", 400),
                           lp.quota("mistral")["tokens_today"] > before)[1])(q["tokens_today"]))
    os.environ["AKASHA_LLM_MISTRAL_TOKENS_PER_DAY"] = "9000"
    check("the host can raise the daily token ceiling by env, per provider",
          lp._budget("mistral")["tokens_per_day"] == 9000)
    del os.environ["AKASHA_LLM_MISTRAL_TOKENS_PER_DAY"]

    print("\n  ── WHICH ceiling is spent is decided once, at the gate ──")
    lp._METER.clear()
    for v in list(os.environ):
        if v.startswith("AKASHA_LLM_"):
            del os.environ[v]
    lp._FREE_TIER["mistral"] = dict(lp._FREE_TIER["mistral"], calls_per_day=1, tokens_per_day=0,
                                    tokens_per_month=0)
    lp._meter_record("mistral", 40)
    check("a spent CALL ceiling names itself `calls`", lp.quota("mistral")["limit"] == "calls",
          lp.quota("mistral")["limit"])
    lp._METER.clear()
    lp._FREE_TIER["mistral"] = dict(lp._FREE_TIER["mistral"], calls_per_day=0, tokens_per_day=10,
                                    tokens_per_month=0)
    lp._meter_record("mistral", 400)
    check("a spent DAILY TOKEN ceiling names itself `tokens_day`",
          lp.quota("mistral")["limit"] == "tokens_day", lp.quota("mistral")["limit"])
    lp._METER.clear()
    lp._FREE_TIER["mistral"] = dict(lp._FREE_TIER["mistral"], calls_per_day=0, tokens_per_day=0,
                                    tokens_per_month=10)
    lp._meter_record("mistral", 400)
    check("a spent MONTHLY TOKEN ceiling names itself `tokens_month`",
          lp.quota("mistral")["limit"] == "tokens_month", lp.quota("mistral")["limit"])
    lp._METER.clear()
    lp._FREE_TIER["mistral"] = dict(lp._FREE_TIER["mistral"], calls_per_day=99, tokens_per_day=0,
                                    tokens_per_month=0)
    check("nothing spent names nothing", lp.quota("mistral")["limit"] == "",
          repr(lp.quota("mistral")["limit"]))
    # the live incident: 219 calls of a 220 cap, tokens at 1.1% — a CALL ceiling, reported as a
    # pool refusal until 09-20. The distinction is what sends an operator to the right place.
    lp._METER.clear()
    lp._FREE_TIER["mistral"] = dict(lp._FREE_TIER["mistral"], calls_per_day=220,
                                    tokens_per_day=500000, tokens_per_month=14000000)
    for _ in range(220):
        lp._meter_record("mistral", 2800)          # ~715 tokens/call, the live figure
    q = lp.quota("mistral")
    check("the 2026-09-20 shape resolves to `calls`, with tokens far under",
          q["limit"] == "calls" and q["tokens_month"] < q["tokens_per_month"] * 0.05,
          "limit=%s tokens=%d/%d" % (q["limit"], q["tokens_month"], q["tokens_per_month"]))

    print("\n  ── the shipped ceiling holds the month under €10, and clears the declared demand ──")
    import importlib
    globals()['lp'] = importlib.reload(lp)
    b = lp._budget("mistral")
    # The dearest figure any public source quotes for this model family, applied to EVERY token as if
    # it were an output token — a mix no real traffic reaches. If the bound holds here it holds live.
    DEAREST_PER_TOKEN = 0.60 / 1e6
    month_usd = b["tokens_per_month"] * DEAREST_PER_TOKEN
    day_usd = b["tokens_per_day"] * DEAREST_PER_TOKEN
    check("the monthly ceiling is under €10 at the dearest quoted rate",
          month_usd < 10.0, "$%.2f/month at $0.60/M" % month_usd)
    check("the daily ceiling cannot eat the month in one day",
          b["tokens_per_day"] * 3 < b["tokens_per_month"],
          "$%.2f/day, %.0f days to the monthly ceiling"
          % (day_usd, b["tokens_per_month"] / float(b["tokens_per_day"])))
    # The demand side: what the WORKLOADS declare, so the cap never starves normal operation.
    # Read from the declarations themselves (seed A) rather than from the legacy studio rows — the
    # source of truth moved, and a ceiling derived from a file nobody reads is a ceiling that will
    # be hit by surprise. Every provisioned workload counts, including the ones whose source is not
    # on this cell yet: they are armed, so they will spend the day they get one.
    # There is ONE effective ceiling, and the boot line names it together with where it came from —
    # a deploy can move it from outside the process, so `cap=` alone cannot say whether an override
    # reached this host. The demand below is compared against that same effective number, not
    # against the built-in default, so this check cannot pass on a cell whose real cap is different.
    from lib.akasha.workbench import llm_pool as _lpool
    _eff_calls, _eff_tokens = _lpool.caps("mistral")
    _eff_src = _lpool.caps_source("mistral")
    check("the pool's effective ceiling IS the provider budget the eval measures against",
          (_eff_calls, _eff_tokens) == (b["calls_per_day"], b["tokens_per_month"]),
          "pool=%s/%s budget=%s/%s" % (_eff_calls, _eff_tokens,
                                       b["calls_per_day"], b["tokens_per_month"]))
    check("…and it says where it came from, so a missing override is visible at boot",
          _eff_src in ("env", "default") or "/" in _eff_src, "from=%s" % _eff_src)
    os.environ["AKASHA_LLM_MISTRAL_CALLS_PER_DAY"] = "7"
    try:
        check("…which changes to `env` when a host override actually arrives",
              _lpool.caps("mistral")[0] == 7 and _lpool.caps_source("mistral").startswith("env"),
              "cap=%s from=%s" % (_lpool.caps("mistral")[0], _lpool.caps_source("mistral")))
    finally:
        os.environ.pop("AKASHA_LLM_MISTRAL_CALLS_PER_DAY", None)

    from lib.akasha.workbench import workload as _W
    declared = sum(_W.budget(x)["per_day"] * _W.appetite(x)["llm_calls_per_run"]
                   for x in _W.declarations(None))
    check("the daily CALL cap clears the demand every declared workload asks for",
          b["calls_per_day"] > declared,
          "cap=%d declared=%d/day (%s)"
          % (b["calls_per_day"], declared,
             ", ".join("%s=%d" % (x["workflow"],
                                  _W.budget(x)["per_day"] * _W.appetite(x)["llm_calls_per_run"])
                       for x in _W.declarations(None))))

    # The check above is only worth anything if each workload RUNS at the cadence it declares. It
    # did not: on 2026-09-20 the news programme ran every ~188 s against a declared 1800 s, spent
    # 219 of a 220-call day in 3.8 hours, and every airing after that was refused. A ceiling derived
    # from a declaration nobody keeps is a ceiling that will be hit by surprise — so the two are
    # asserted together, here, where the derivation lives.
    #
    # There is no daemon config to read any more: the driver reads the declaration's own trigger,
    # so the cadence the eval bounds and the cadence the run takes are the same number by
    # construction rather than by two files agreeing.
    from lib.akasha.workbench import wl_state as _wls
    worst = []
    for x in _W.declarations(None):
        iv = _wls.interval_of(_W.policy(x))
        if iv <= 0:
            continue                       # a workload with no recurrence spends its budget, not more
        runs = min(int(_W.budget(x)["per_day"] or 0), int(86400 // iv))
        worst.append((str(x.get("workflow")), runs * _W.appetite(x)["llm_calls_per_run"], iv, runs))
    _recurring = [x for x in _W.declarations(None) if (x.get("trigger") or {}).get("then")]
    check("every declared cadence is a real recurrence the driver can read (%d declared)" % len(_recurring),
          len(worst) == len(_recurring), ", ".join("%s=%.0fs" % (n, iv) for n, _c, iv, _r in worst))
    _wants = sum(c for _n, c, _iv, _r in worst)
    check("… and a full day at every declared cadence still fits inside the ceiling",
          _wants <= b["calls_per_day"],
          "wants=%d/day cap=%d (%s)" % (_wants, b["calls_per_day"],
                                        ", ".join("%s=%d×%d" % (n, r, c // r if r else 0)
                                                  for n, c, _iv, r in worst)))

    print()
    if _fails:
        print("RESULT: FAIL (%d): %s\n" % (len(_fails), "; ".join(_fails)))
        return 1
    print("RESULT: PASS — the free-tier ceiling is enforced at the one shared leaf: calls are metered "
          "before they go out, the ceiling stops them with no HTTP, it rolls over per UTC day/month, it "
          "is host-configurable (0 = unmetered), it survives a restart, and calls are paced to the "
          "provider's rate. No caller carries a schedule of its own.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
