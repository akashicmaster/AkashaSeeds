"""
llm_provider — minimal, degradation-first adapters for FREE external LLM tiers.

Stdlib only (urllib; honours HTTPS_PROXY). Keys come from the environment, NEVER an atom. Every call
returns a plain string, or None on ANY failure (missing key, rate limit, network) — the caller
degrades gracefully. This is the shared LLM surface for the LLM-participation experiment: the caller
hands a system prompt + a user turn and gets back the model's own words, tagged with the exact model
id for the evidence trail.

Providers — most are OpenAI-compatible (same /v1/chat/completions wire format), so EU-hosted options
are drop-in. Free tiers, EU data residency noted:

  • openrouter — OpenAI-compatible; many `:free` models under one key. US-based (some `:free` models /
                 the router may be geo-limited).                       key: AKASHA_OPENROUTER_KEY
  • mistral    — 🇪🇺 Mistral AI (France), OpenAI-compatible. Free "Experiment" tier (~1B tok/month,
                 ~1 req/s; phone verification). EU data residency.     key: AKASHA_MISTRAL_KEY
  • openai     — 🇪🇺-ready GENERIC OpenAI-compatible endpoint: point AKASHA_LLM_BASE_URL at ANY
                 compatible EU host (Scaleway https://api.scaleway.ai/v1 · Nebius
                 https://api.studio.nebius.com/v1 · OVHcloud AI Endpoints · IONOS …), key from
                 AKASHA_LLM_API_KEY. Free-tier/beta on Scaleway & Nebius; all EU-hosted.
  • gemini     — Google AI Studio free tier. ⚠️ free Gemini may NOT serve EEA/CH/UK → avoid for a
                 global public page.                                   key: AKASHA_GEMINI_KEY
  • ollama     — a local open model, no key.                           AKASHA_OLLAMA_URL
"""
import json
import logging
import os
import re
import time
import urllib.error
import urllib.request

logger = logging.getLogger("Akasha.LLM")

# A20(b) — throttle provider-failure WARNINGs to at most one per (provider, kind) per hour, so a
# station standing by on a dead provider (missing key / 429 quota / network) becomes VISIBLE in the
# log without flooding it. The API KEY is NEVER logged (a URL query key / Bearer token is redacted).
_LLM_FAIL_LOG: dict = {}

# A22 — provider rate-limit (HTTP 429) back-off. A persistent 429 on a free tier (quota / rate cap)
# means "stop calling"; the station tick would otherwise hammer the endpoint every interval. On a 429
# a provider is suppressed until a deadline: `Retry-After` when the server sends one, else exponential
# 60 s → 1 h cap, growing per consecutive 429. A SUCCESS resets it. Enforced in `generate` (a
# suppressed call returns None immediately, no HTTP), so every caller degrades the same way.
_BACKOFF: dict = {}         # provider → unix ts until which calls are suppressed
_BACKOFF_STEP: dict = {}    # provider → current exponential step (seconds)
_BACKOFF_SINCE: dict = {}   # provider → unix ts the CURRENT back-off window began (stable across grows)
_BACKOFF_WHY: dict = {}     # provider → the provider's OWN words for the refusal (its 429 body)
_BACKOFF_MIN = 60.0
_BACKOFF_MAX = 3600.0

# R8 — the 429 back-off must survive a RESTART: a boot inside a back-off window that resets the state and
# hits the provider again is a defect. The DURABLE store is injected by the kernel (`set_backoff_store`)
# so this module stays stdlib-pure; without it (a bare test / no kernel) the back-off is process-memory
# only, as before. State is loaded ONCE on first use after boot and re-saved whenever it changes.
_BACKOFF_STORE = None       # {"load": ()->dict, "save": (dict)->None} or None
_BACKOFF_LOADED = False

# ── A53 — the free-tier BUDGET: the PROACTIVE half of the 429 back-off ───────────────────────────────
# The back-off above is REACTIVE — it only fires once the provider has already refused us. A metered
# free tier needs the proactive half too, and it needs it HERE, at the single leaf every caller already
# goes through: one shared key is spent by every programme at once (the news station, a reading
# programme, a society's auto-run), so a budget wired per-caller is a budget the next programme
# overspends. Same shape as the `_weave_exempt` gate: ONE predicate at the leaf, never per-caller.
#
# The numbers below are a SELF-IMPOSED ceiling, deliberately under whatever the provider advertises —
# NOT a published limit (the exact figures change and are not ours to assert). `min_interval` is the
# one hard provider fact we act on (~1 req/s), enforced by pacing so a burst never earns the
# hour-long back-off.
#
# ⚠️ On a PAID tier this ceiling is a SPEND cap, and the three dimensions are not interchangeable:
#   · `calls_per_day`    bounds how OFTEN — it stops a loop, but says nothing about cost;
#   · `tokens_per_day`   bounds a DAY in money — cost is per token, so a call cap alone lets one fat
#                        day spend the whole month and leave the station silent for the rest of it;
#   · `tokens_per_month` bounds the BILL.
# A ceiling reached is reported as OURS (`llm.diag`), never as the provider refusing.
#
# The mistral figures are set to hold the month UNDER €10 (owner's instruction, 2026-09-19), derived
# so they hold even at the WORST price any public source quotes and even if every token were charged
# at the dearer OUTPUT rate — a mix no real traffic reaches:
#     14M tokens/month × $0.60 per M  ≈  $8.40/month        ← the bill's bound   (UNCHANGED)
#      0.5M tokens/day  × $0.60 per M ≈  $0.30/day          ← one bad day cannot eat the month
#     220 calls/day                                          ← above the 174/day the four declare
# The token counters are Akasha's own chars/4 ESTIMATE, not the provider's accounting, which is why
# the bound is taken at the dearest rate rather than a realistic blend. Re-derive these if the
# declared cadences grow: `config/workbench/workloads/*.json` is the demand side.
#
# RE-CHECKED 2026-09-21 (seed A slice 1), and the figure STANDS at 220. Provisioning all four
# workloads briefly put the declared demand at 222 (3×48 + 15×2 + 12×2 + 12×2) — over by two calls,
# which this figure could not have anticipated because it was derived when only two programmes were
# driven and the demand was 183. The answer was not a higher ceiling: the three reading programmes
# were over-declaring their appetite (15 and 12 against a cycle of five steps, and one
# `society.air` step is at most one model call), so admission RESERVED three times what they spend
# and starved the shared pool. Corrected on the demand side, the day is 3×48 + 5×2 + 5×2 + 5×2 =
# 174, and 220 keeps its headroom.
#
# The distinction is worth keeping: `calls_per_day` bounds how OFTEN and stops a loop; the €10/month
# instruction is held by `tokens_per_month`, which is the number to defend. Raising the call ceiling
# to fit an over-declared appetite would have hidden the over-reservation rather than fixing it.
# Override per host — `llm.budget` writes these, so no operator touches an export:
#     AKASHA_LLM_CALLS_PER_DAY / AKASHA_LLM_TOKENS_PER_DAY / AKASHA_LLM_TOKENS_PER_MONTH  (all)
#     AKASHA_LLM_MISTRAL_CALLS_PER_DAY / …_TOKENS_PER_DAY / …_TOKENS_PER_MONTH      (one provider)
# 0 = unmetered. A local model is never metered.
_FREE_TIER = {
    "mistral":    {"calls_per_day": 220, "tokens_per_day": 500000,
                   "tokens_per_month": 14000000, "min_interval": 1.1},
    "openrouter": {"calls_per_day": 150, "tokens_per_day": 0, "tokens_per_month": 0, "min_interval": 1.0},
    "gemini":     {"calls_per_day": 1000, "tokens_per_day": 0, "tokens_per_month": 0, "min_interval": 1.0},
    "openai":     {"calls_per_day": 0,   "tokens_per_day": 0, "tokens_per_month": 0, "min_interval": 1.0},
    "ollama":     {"calls_per_day": 0,   "tokens_per_day": 0, "tokens_per_month": 0, "min_interval": 0.0},
}
_METER: dict = {}           # provider → {day, calls, month, tokens}
_METER_STORE = None         # durable store, injected by the kernel (same vault as the back-off)
_METER_LOADED = False
_NEXT_OK: dict = {}         # provider → unix ts the next call may go out (lock-free pacing ticket)
_PACE_WAIT_MAX = 30.0       # never block a caller longer than this waiting for a pacing slot


def set_backoff_store(load, save) -> None:
    """R8 — install the durable back-off store (kernel: the shared-nucleus vault). Forces a reload so the
    next use inherits any persisted, still-live back-off from before the restart."""
    global _BACKOFF_STORE, _BACKOFF_LOADED
    _BACKOFF_STORE = {"load": load, "save": save}
    _BACKOFF_LOADED = False


def _persist_backoff() -> None:
    """Save every STILL-LIVE back-off {provider: {until, step, since}} through the injected store."""
    if not _BACKOFF_STORE:
        return
    now = time.time()
    data = {p: {"until": float(u), "step": float(_BACKOFF_STEP.get(p, 0.0)),
                "since": float(_BACKOFF_SINCE.get(p, now)),
                "why": str(_BACKOFF_WHY.get(p, ""))[:300]}
            for p, u in _BACKOFF.items() if float(u) > now}
    try:
        _BACKOFF_STORE["save"](data)
    except Exception:
        pass


def _load_backoff_once() -> None:
    """R8 — inherit the persisted back-off ONCE per process (first use after boot). A window still live
    at load time is re-armed WITHOUT calling the provider; its `since` is preserved so the station's
    standby line is unchanged across the deploy. Logs one `[llm] backoff inherited …` per window."""
    global _BACKOFF_LOADED
    if _BACKOFF_LOADED or not _BACKOFF_STORE:
        return
    _BACKOFF_LOADED = True
    try:
        data = _BACKOFF_STORE["load"]() or {}
    except Exception:
        return
    now = time.time()
    for prov, st in (data.items() if isinstance(data, dict) else []):
        try:
            until = float((st or {}).get("until", 0.0))
        except (TypeError, ValueError):
            continue
        if until > now:                                   # still suppressed → inherit, do NOT call
            _BACKOFF[prov] = until
            _BACKOFF_STEP[prov] = float((st or {}).get("step", 0.0) or 0.0)
            _BACKOFF_SINCE[prov] = float((st or {}).get("since", now) or now)
            _BACKOFF_WHY[prov] = str((st or {}).get("why", "") or "")
            logger.info("[llm] backoff inherited provider=%s until=%d (since=%d)%s",
                        prov, int(until), int(_BACKOFF_SINCE[prov]),
                        (" why=%s" % _BACKOFF_WHY[prov]) if _BACKOFF_WHY[prov] else "")


def load_persisted_backoff() -> None:
    """Public — the kernel calls this at boot (after installing the store) so the inherited back-off is
    re-armed + logged before the first station tick."""
    _load_backoff_once()


def _in_backoff(provider: str) -> bool:
    _load_backoff_once()
    return time.time() < float(_BACKOFF.get(provider, 0.0))


def _backoff_remaining(provider: str) -> int:
    _load_backoff_once()
    return max(0, int(float(_BACKOFF.get(provider, 0.0)) - time.time()))


def _enter_backoff(provider: str, retry_after=None) -> float:
    """Suppress `provider` after a 429. Honour a numeric `Retry-After` (seconds), else grow the
    exponential step (60 s → 1 h cap). Records the window's `since` (first 429 of the window only) and
    persists the state (R8). Returns the chosen back-off in seconds."""
    _load_backoff_once()
    if retry_after is not None:
        try:
            secs = max(_BACKOFF_MIN, min(_BACKOFF_MAX, float(retry_after)))
        except (TypeError, ValueError):
            retry_after = None
    if retry_after is None:
        step = float(_BACKOFF_STEP.get(provider, 0.0))
        secs = _BACKOFF_MIN if step <= 0 else min(_BACKOFF_MAX, step * 2.0)
        _BACKOFF_STEP[provider] = secs
    _BACKOFF[provider] = time.time() + secs
    # R8 — `since` is the FIRST 429 of a CONTINUOUS refusal, and only a SUCCESSFUL call ends it
    # (`_clear_backoff` pops it). It used to be re-stamped whenever the previous window had already
    # lapsed (`if not already`), so a provider refusing all night reported a `since` that walked
    # forward with every retry — 04:09Z → 04:41Z → 05:14Z — and the station's standby line claimed
    # the outage had just started each time. `until` and `step` advance per retry, as they must;
    # `since` does not move while the refusal continues.
    _BACKOFF_SINCE.setdefault(provider, time.time())
    _persist_backoff()
    return secs


def _clear_backoff(provider: str) -> None:
    _BACKOFF.pop(provider, None)
    _BACKOFF_STEP.pop(provider, None)
    _BACKOFF_SINCE.pop(provider, None)
    _BACKOFF_WHY.pop(provider, None)
    _persist_backoff()


def backoff_reason(provider: str) -> str:
    """Public: the provider's OWN words for the current refusal — the `message` out of its 429 body.

    A 429 has more than one cause, and they call for opposite actions: a frequency cap says *wait*,
    an exhausted monthly allowance says *wait until the month turns*, an inactive plan or a model the
    tier may not serve says *the waiting will never end*. Only the provider knows which, and it says
    so in the body. Discarding that body was why a station could stand by for fifteen days reporting
    nothing but `429`, at one call an hour — a rate no frequency cap on earth would refuse. Empty when
    the provider sent no body, or when nothing is backed off."""
    _load_backoff_once()
    prov = (provider or "").strip().lower()
    if time.time() < float(_BACKOFF.get(prov, 0.0)):
        return str(_BACKOFF_WHY.get(prov, "") or "")
    return ""


def _http_detail(he, limit: int = 300) -> str:
    """The provider's words out of an error response, flattened to one line. Bounded (the body is
    read once and capped): a refusal explains itself in a sentence, and an unbounded read of an error
    body is an unbounded allocation on a path that is already going wrong."""
    try:
        raw = he.read(8192).decode("utf-8", "replace")
    except Exception:
        return ""
    try:
        obj = json.loads(raw)
        err = obj.get("error") if isinstance(obj.get("error"), dict) else {}
        msg = obj.get("message") or err.get("message") or obj.get("detail") or ""
        typ = err.get("type") or obj.get("type") or obj.get("code") or err.get("code") or ""
        out = " ".join(str(x) for x in (typ, msg) if x)
    except Exception:
        out = raw
    return " ".join(out.split())[:limit]


def probe(provider: str, model: str = "", timeout: int = 30) -> dict:
    """One deliberate call, to make the provider SAY what is wrong — the operator's diagnostic.

    A 429 arms an hour-long back-off, so waiting for the next scheduled airing to learn anything
    costs an hour per question. This sends a single minimal completion NOW, bypassing the back-off
    suppression (never the budget — an exhausted ceiling is an answer, not an obstacle), and reports
    the status, the provider's message and its rate-limit headers. It never returns or logs the key.

    Bypassing the back-off is safe because it is one call an operator asked for: it is metered like
    any other, and a 429 it receives re-arms the window with the message attached.
    """
    prov = (provider or "").strip().lower()
    out = {"provider": prov, "model": model or DEFAULT_MODELS.get(prov, ""),
           "configured": False, "ok": False, "status": 0, "message": "", "rate_headers": "",
           "backoff_s": _backoff_remaining(prov), "quota": {}}
    if prov not in _OPENAI_COMPAT and prov not in ("gemini", "ollama"):
        out["message"] = "unknown provider"
        return out
    if prov in _OPENAI_COMPAT and not (_base_url(prov) and _key_from(_OPENAI_COMPAT[prov][1])):
        out["message"] = "no key or base URL configured on this host (llm.key set %s <key>)" % prov
        return out
    out["configured"] = True
    out["quota"] = quota(prov)
    if _over_budget(prov):
        out["message"] = ("the SELF-IMPOSED free-tier ceiling is reached (%s calls today / %s tokens "
                          "this month) — this is Akasha's own gate, not the provider's"
                          % (out["quota"].get("calls_today"), out["quota"].get("tokens_month")))
        return out
    sysmsg, usermsg = "You are a connectivity probe.", "Reply with the single word: ok"
    _meter_record(prov, len(sysmsg) + len(usermsg))
    try:
        if prov in _OPENAI_COMPAT:
            text = _openai_compatible(prov, out["model"], sysmsg, usermsg, timeout)
        elif prov == "gemini":
            text = _gemini(out["model"], sysmsg, usermsg, timeout)
        else:
            text = _ollama(out["model"], sysmsg, usermsg, timeout)
        out["ok"] = bool((text or "").strip())
        out["status"] = 200
        out["message"] = (text or "").strip()[:200] or "reached the provider, got no text"
        if out["ok"]:
            _clear_backoff(prov)              # a good call ends the window, as any good turn does
            out["backoff_s"] = 0
    except urllib.error.HTTPError as he:
        out["status"] = int(getattr(he, "code", 0) or 0)
        out["message"] = _http_detail(he) or ("HTTP %s %s" % (out["status"], he.reason))
        out["rate_headers"] = _rate_headers(he)
        if out["status"] == 429:
            ra = he.headers.get("Retry-After") if getattr(he, "headers", None) else None
            secs = _enter_backoff(prov, ra)
            _BACKOFF_WHY[prov] = " · ".join(x for x in (out["message"], out["rate_headers"]) if x)
            _persist_backoff()
            out["backoff_s"] = int(secs)
    except Exception as exc:
        out["message"] = "%s: %s" % (type(exc).__name__, exc)
    return out


def _rate_headers(he, limit: int = 200) -> str:
    """The provider's rate-limit headers, which say WHICH budget was hit and when it resets."""
    try:
        hdrs = he.headers or {}
    except Exception:
        return ""
    keep = [(k, v) for k, v in hdrs.items()
            if k.lower().startswith(("x-ratelimit", "ratelimit", "retry-after"))]
    return " ".join("%s=%s" % (k.lower(), v) for k, v in keep)[:limit]


_PROVIDER_ENV = "AKASHA_LLM_PROVIDER"
_PROVIDER_DEFAULT = "mistral"


def active(kernel=None) -> str:
    """The provider this cell speaks to, read in ONE place.

    One reader, one default. Any workload that reserves a call uses this provider; nothing about it
    is a programme's. (The old station-named variable is deleted, not aliased — the purge order
    rule 1; the env loader refuses it by name.)"""
    return (os.environ.get(_PROVIDER_ENV) or "").strip().lower() or _PROVIDER_DEFAULT


def backoff_seconds(provider: str) -> int:
    """Public: seconds remaining on a provider's 429 back-off, 0 if not backed off (A27 — lets a
    workload report ONE stable standby reason while a provider is rate-limited)."""
    return _backoff_remaining((provider or "").strip().lower())


def backoff_since(provider: str) -> float:
    """Public (R8): the unix ts the provider's CURRENT back-off window began (0 if not backed off). The
    station reports its standby `since` from this so the line is unchanged across a restart."""
    _load_backoff_once()
    prov = (provider or "").strip().lower()
    if time.time() < float(_BACKOFF.get(prov, 0.0)):
        return float(_BACKOFF_SINCE.get(prov, 0.0))
    return 0.0


def set_meter_store(load, save) -> None:
    """Install the durable budget meter store (kernel: the shared-nucleus vault, beside the back-off).
    Without it the meter is process-memory only — correct, but a restart forgets what was spent."""
    global _METER_STORE, _METER_LOADED
    _METER_STORE = {"load": load, "save": save}
    _METER_LOADED = False


def _meter_load_once() -> None:
    global _METER_LOADED
    if _METER_LOADED or not _METER_STORE:
        return
    _METER_LOADED = True
    try:
        data = _METER_STORE["load"]() or {}
    except Exception:
        return
    if isinstance(data, dict):
        for prov, st in data.items():
            if isinstance(st, dict):
                _METER[prov] = {"day": str(st.get("day") or ""), "calls": int(st.get("calls") or 0),
                                "month": str(st.get("month") or ""), "tokens": int(st.get("tokens") or 0)}


def _meter_save() -> None:
    if not _METER_STORE:
        return
    try:
        _METER_STORE["save"](dict(_METER))
    except Exception:
        pass


def budget_with_sources(provider: str):
    """`(ceiling, {field: "env" | "default"})` — the ceiling in force for this provider AND where each
    number came from: the built-in self-imposed default, or a host override (the per-provider var
    wins over the global one). 0 = unmetered.

    The SOURCE is not decoration. One effective ceiling is in force and a deploy can move it from the
    outside, so a log that prints only the number cannot answer the first question an operator asks
    when the pool refuses under a cap that looks wrong: did my override reach this process? `env`
    says it did; `default` says the environment variable never arrived, whatever the deploy file
    says. This is the same reasoning as the `[iam] token signing secret source=` line."""
    tier = dict(_FREE_TIER.get(provider) or {"calls_per_day": 0, "tokens_per_day": 0,
                                             "tokens_per_month": 0, "min_interval": 1.0})
    tier.setdefault("tokens_per_day", 0)
    sources = {}
    up = provider.upper()
    for field, var in (("calls_per_day", "CALLS_PER_DAY"),
                       ("tokens_per_day", "TOKENS_PER_DAY"),
                       ("tokens_per_month", "TOKENS_PER_MONTH")):
        sources[field] = "default"
        for name in ("AKASHA_LLM_%s_%s" % (up, var), "AKASHA_LLM_%s" % var):
            v = (os.environ.get(name) or "").strip()
            if v:
                try:
                    tier[field] = max(0, int(v))
                    sources[field] = "env"
                except ValueError:
                    pass
                break
    return tier, sources


def _budget(provider: str) -> dict:
    """The ceiling in force for this provider. `budget_with_sources` also says where it came from."""
    return budget_with_sources(provider)[0]


def _meter_of(provider: str, now: float) -> dict:
    """This provider's counters, rolled over on a new UTC day / month (the reset is the schedule)."""
    _meter_load_once()
    day = time.strftime("%Y-%m-%d", time.gmtime(now))
    month = day[:7]
    st = _METER.get(provider)
    if not isinstance(st, dict):
        st = _METER[provider] = {"day": day, "calls": 0, "day_tokens": 0,
                                 "month": month, "tokens": 0}
    st.setdefault("day_tokens", 0)                    # a meter written before the daily token ceiling
    if st.get("day") != day:
        st["day"], st["calls"], st["day_tokens"] = day, 0, 0
    if st.get("month") != month:
        st["month"], st["tokens"] = month, 0
    return st


def quota(provider: str) -> dict:
    """Public read — what is left of this provider's self-imposed free-tier budget, for an operator
    surface (`llm.key ls`) and for a scheduler that wants to know before it plans a run."""
    provider = (provider or "").strip().lower()
    b, st = _budget(provider), _meter_of(provider, time.time())
    cpd, tpm = int(b.get("calls_per_day", 0)), int(b.get("tokens_per_month", 0))
    tpd = int(b.get("tokens_per_day", 0))
    return {"provider": provider, "day": st["day"], "month": st["month"],
            "calls_today": int(st["calls"]), "calls_per_day": cpd,
            "tokens_today": int(st.get("day_tokens", 0)), "tokens_per_day": tpd,
            "tokens_month": int(st["tokens"]), "tokens_per_month": tpm,
            "calls_left": (max(0, cpd - int(st["calls"])) if cpd else None),
            "tokens_left_today": (max(0, tpd - int(st.get("day_tokens", 0))) if tpd else None),
            "tokens_left": (max(0, tpm - int(st["tokens"])) if tpm else None),
            "exhausted": _over_budget(provider), "limit": _limit_reached(provider),
            "min_interval_s": float(b.get("min_interval", 1.0))}


def _limit_reached(provider: str, now: float = None) -> str:
    """WHICH ceiling is spent: "calls" | "tokens_day" | "tokens_month" | "" .

    `exhausted` alone conflates three different facts that ask for three different actions — raise
    the cadence, raise the money bound, or wait for the month. A caller that has to re-derive which
    one from the numbers will get it wrong (and did: the station reported a spent CALL ceiling as
    `llm_pool`, sending an operator to the provider when the limit was ours). So the decision is made
    once, here, beside the gate that makes it."""
    now = time.time() if now is None else now
    b, st = _budget(provider), _meter_of(provider, now)
    cpd = int(b.get("calls_per_day", 0))
    tpd, tpm = int(b.get("tokens_per_day", 0)), int(b.get("tokens_per_month", 0))
    if cpd and int(st["calls"]) >= cpd:
        return "calls"
    if tpd and int(st.get("day_tokens", 0)) >= tpd:
        return "tokens_day"
    if tpm and int(st["tokens"]) >= tpm:
        return "tokens_month"
    return ""


def _over_budget(provider: str, now: float = None) -> bool:
    """True when this provider's budget for the current UTC day/month is spent. Unmetered → never."""
    now = time.time() if now is None else now
    b, st = _budget(provider), _meter_of(provider, now)
    cpd = int(b.get("calls_per_day", 0))
    tpd, tpm = int(b.get("tokens_per_day", 0)), int(b.get("tokens_per_month", 0))
    if cpd and int(st["calls"]) >= cpd:
        return True
    # The DAILY token ceiling is the one that bounds a day in money: cost is per token, so a call
    # cap alone lets one fat day spend a month. With both, a runaway is contained to its own day
    # and the month survives it.
    if tpd and int(st.get("day_tokens", 0)) >= tpd:
        return True
    return bool(tpm and int(st["tokens"]) >= tpm)


def _meter_record(provider: str, chars: int) -> None:
    """Count one call and its rough token cost (chars/4 — an ESTIMATE, rounded up, never the provider's
    own accounting). Persisted so a restart does not hand the budget back."""
    st = _meter_of(provider, time.time())
    st["calls"] = int(st["calls"]) + 1
    n = max(1, int(chars / 4) + 1)
    st["tokens"] = int(st["tokens"]) + n
    st["day_tokens"] = int(st.get("day_tokens", 0)) + n
    _meter_save()


def _meter_record_output(provider: str, chars: int) -> None:
    """Add the completion's estimated cost to the day's and the month's tokens (the call itself was
    already counted
    before the request went out — a request we sent is spent whether or not it answered)."""
    st = _meter_of(provider, time.time())
    n = max(0, int(chars / 4))
    st["tokens"] = int(st["tokens"]) + n
    st["day_tokens"] = int(st.get("day_tokens", 0)) + n
    _meter_save()


def _pace(provider: str) -> bool:
    """Hold the caller until this provider's next slot (~1 req/s on a free tier), so a burst never earns
    the hour-long 429 back-off. Lock-free: each caller TAKES a ticket by advancing the shared deadline,
    then waits for its own — nothing is held across the sleep. False = the wait was too long to be worth
    it (the caller degrades instead of blocking a thread)."""
    gap = float((_FREE_TIER.get(provider) or {}).get("min_interval", 1.0) or 0.0)
    if gap <= 0:
        return True
    now = time.time()
    slot = max(now, float(_NEXT_OK.get(provider, 0.0)))
    if slot - now > _PACE_WAIT_MAX:
        return False
    _NEXT_OK[provider] = slot + gap
    if slot > now:
        time.sleep(slot - now)
    return True


def _redact(msg: str) -> str:
    """Strip anything key-shaped from a provider error before it reaches the log."""
    s = str(msg or "")[:200]
    return re.sub(r"(key=|Bearer\s+|api[_-]?key[=:]\s*)[A-Za-z0-9._\-]{6,}", r"\1***", s, flags=re.I)


def _log_llm_fail(provider: str, kind: str, detail: str = "") -> None:
    now = time.time()
    k = (provider or "?", kind)
    if now - float(_LLM_FAIL_LOG.get(k, 0.0)) >= 3600.0:
        _LLM_FAIL_LOG[k] = now
        if len(_LLM_FAIL_LOG) > 256:                      # bound the table (R7)
            for _k in sorted(_LLM_FAIL_LOG, key=_LLM_FAIL_LOG.get)[:64]:
                _LLM_FAIL_LOG.pop(_k, None)
        logger.warning("[llm] %s %s%s", provider or "?", kind,
                       (" — " + _redact(detail)) if detail else "")


# OpenAI-compatible providers: name → (base_url, key env vars, default model, EU-hosted?).
# `openai` is the generic escape hatch — its base URL comes from the environment.
_OPENAI_COMPAT = {
    "openrouter": ("https://openrouter.ai/api/v1",
                   ("AKASHA_OPENROUTER_KEY", "OPENROUTER_API_KEY"),
                   "meta-llama/llama-3.3-70b-instruct:free", False),
    "mistral":    ("https://api.mistral.ai/v1",
                   ("AKASHA_MISTRAL_KEY", "MISTRAL_API_KEY"),
                   "mistral-small-latest", True),
    "openai":     (None,   # ← from AKASHA_LLM_BASE_URL (any EU OpenAI-compatible host)
                   ("AKASHA_LLM_API_KEY", "OPENAI_API_KEY"),
                   "", True),
}

DEFAULT_MODELS = {name: cfg[2] for name, cfg in _OPENAI_COMPAT.items()}
DEFAULT_MODELS.update({"gemini": "gemini-2.0-flash", "ollama": "llama3"})


def default_model(provider: str) -> str:
    """The model this provider is called with when a caller names none — the reader behind the
    workbench's `llm_default_model` hook, so a concept asks for it instead of importing the gate."""
    return DEFAULT_MODELS.get(str(provider or "").strip().lower(), "")

# Providers hosted in the EU (data residency) — for operator guidance / a global public page.
EU_PROVIDERS = tuple(sorted(n for n, cfg in _OPENAI_COMPAT.items() if cfg[3]))


def _key_from(env_names):
    for n in env_names:
        v = os.environ.get(n)
        if v:
            return v
    return None


def _base_url(provider):
    base = _OPENAI_COMPAT[provider][0]
    if base is None:                       # generic "openai" → operator-supplied EU endpoint
        base = (os.environ.get("AKASHA_LLM_BASE_URL") or "").strip().rstrip("/")
    return base or None


def _http_json(url, body, headers, timeout=60):
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def _openai_compatible(provider, model, system, user, timeout):
    base = _base_url(provider)
    key = _key_from(_OPENAI_COMPAT[provider][1])
    if not base or not key:
        return None
    data = _http_json(base + "/chat/completions",
                      {"model": model, "messages": [{"role": "system", "content": system},
                                                     {"role": "user", "content": user}]},
                      {"Authorization": f"Bearer {key}"}, timeout)
    return ((data.get("choices") or [{}])[0].get("message", {}).get("content", "") or "").strip()


def _gemini(model, system, user, timeout):
    key = _key_from(("AKASHA_GEMINI_KEY", "GEMINI_API_KEY"))
    if not key:
        return None
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{model}:generateContent?key={key}")
    data = _http_json(url, {"system_instruction": {"parts": [{"text": system}]},
                            "contents": [{"role": "user", "parts": [{"text": user}]}]}, {}, timeout)
    return "".join(p.get("text", "") for p in
                   (data.get("candidates") or [{}])[0].get("content", {}).get("parts", [])).strip()


def _ollama(model, system, user, timeout):
    url = os.environ.get("AKASHA_OLLAMA_URL", "http://localhost:11434").rstrip("/") + "/api/chat"
    data = _http_json(url, {"model": model, "stream": False,
                            "messages": [{"role": "system", "content": system},
                                         {"role": "user", "content": user}]}, {}, timeout)
    return (data.get("message", {}).get("content", "") or "").strip()


def available(provider: str) -> bool:
    """Whether this provider is usable right now (known provider + key present / reachable). A provider
    under a 429 back-off (A22), or one whose self-imposed free-tier budget for today/this month is spent
    (A53), is reported unavailable — so a caller stands by honestly instead of overspending the tier."""
    provider = (provider or "").strip().lower()
    if _in_backoff(provider) or _over_budget(provider):
        return False
    if provider in _OPENAI_COMPAT:
        return bool(_base_url(provider) and _key_from(_OPENAI_COMPAT[provider][1]))
    if provider == "gemini":
        return bool(_key_from(("AKASHA_GEMINI_KEY", "GEMINI_API_KEY")))
    if provider == "ollama":
        return True
    return False


def generate(provider: str, model: str, system: str, user: str, timeout: float = 60.0):
    """Ask a free-tier model for one turn. Returns the model's text, or None on ANY failure so the
    caller can degrade. `model` empty → the provider's default. Never raises."""
    provider = (provider or "").strip().lower()
    model = (model or "").strip() or DEFAULT_MODELS.get(provider, "")
    # A22 — a provider under a 429 back-off is suppressed WITHOUT an HTTP call, so the station stops
    # hammering a rate-limited endpoint every interval. The one-per-hour throttle keeps this quiet.
    if _in_backoff(provider):
        _log_llm_fail(provider, "backoff", "suppressed for %ds after 429" % _backoff_remaining(provider))
        return None
    # A53 — the budget is checked BEFORE the HTTP call and the call is PACED, at the one leaf every
    # programme shares. A caller that knows nothing about quotas cannot overspend the free tier. This is
    # the HARD FLOOR B10 sits on top of — B10's reservation layer prepays against this same ceiling.
    if _over_budget(provider):
        q = quota(provider)
        _log_llm_fail(provider, "budget", "free-tier ceiling reached: %s calls today / %s tokens this "
                                          "month — standing by until the UTC rollover"
                      % (q["calls_today"], q["tokens_month"]))
        return None
    if not _pace(provider):
        _log_llm_fail(provider, "paced", "next slot > %ds away (provider is ~1 req/s)" % int(_PACE_WAIT_MAX))
        return None
    _meter_record(provider, len(system or "") + len(user or ""))
    try:
        if provider in _OPENAI_COMPAT:
            out = _openai_compatible(provider, model, system, user, timeout)
        elif provider == "gemini":
            out = _gemini(model, system, user, timeout)
        elif provider == "ollama":
            out = _ollama(model, system, user, timeout)
        else:
            _log_llm_fail(provider, "unknown-provider")
            return None
        text = (out or "").strip() or None
        if text is None:                                  # reached the provider, got nothing usable
            _log_llm_fail(provider, "empty", "no text this turn (missing key / quota / refusal)")
        else:
            _clear_backoff(provider)                      # a good turn resets any prior back-off
            _meter_record_output(provider, len(text))     # A53 — the completion side of the estimate
            try:                                          # B10 — debit the active reservation (for the
                from lib.akasha.workbench import llm_pool as _pool   # settle refund); the SPEND is A53's meter above
                _pool.note_consumed(provider, len(system or "") + len(user or "") + len(text or ""))
            except Exception:
                pass
        return text
    except urllib.error.HTTPError as he:                  # A22 — a 429 arms the per-provider back-off
        # The provider's own words are read BEFORE the back-off is armed, and kept with it. A 429 has
        # several causes that ask for opposite responses, and only the body distinguishes them; a log
        # line that says `429` and nothing else cannot be acted on, which is how a station stood by
        # for fifteen days at one call an hour.
        detail = _http_detail(he)
        rates = _rate_headers(he)
        if getattr(he, "code", None) == 429:
            ra = he.headers.get("Retry-After") if getattr(he, "headers", None) else None
            secs = _enter_backoff(provider, ra)
            _BACKOFF_WHY[provider] = " · ".join(x for x in (detail, rates) if x)
            _persist_backoff()
            _log_llm_fail(provider, "429", "backing off %ds (%s)%s%s"
                          % (int(secs), "Retry-After" if ra else "exponential",
                             (" — provider says: %s" % detail) if detail else
                             " — provider sent no message",
                             (" [%s]" % rates) if rates else ""))
        else:
            _log_llm_fail(provider, "exception", "HTTP %s %s%s"
                          % (getattr(he, "code", "?"), he.reason,
                             (" — %s" % detail) if detail else ""))
        return None
    except Exception as exc:                              # network / decode — the status
        _log_llm_fail(provider, "exception", "%s: %s" % (type(exc).__name__, exc))
        return None
