"""
The LLM gate's durable stores (pool, back-off) and llm.key / llm.budget / llm.diag — moved out of the kernel (backend layout order 2026-09-20).

Every function takes the kernel (the heart) as its first argument: it is the object the
dispatcher / timer registry hands in, never imported. Bodies are the kernel's own, moved
verbatim except `self.` → `kernel.` and intra-family calls.
"""
import os
import re
import sys
import time
import json
import uuid
import logging
import hashlib
import functools
from typing import Dict, Any, Optional, List, Callable
from lib.akasha.api.rpc import ok as _ok, err as _err
from lib.akasha.workbench import llm_provider as _lprov

# ── constants moved from the kernel class (backend layout order 2026-09-20) ──
_LLM_KEY_ENV = {"mistral": "AKASHA_MISTRAL_KEY", "openrouter": "AKASHA_OPENROUTER_KEY",
                "openai": "AKASHA_LLM_API_KEY", "gemini": "AKASHA_GEMINI_KEY"}


logger = logging.getLogger("Akasha.Kernel")


def install_llm_pool_store(kernel) -> None:
    """B10 — back the llm_pool reservation layer with the shared-nucleus vault (category `llm_pool`,
    key `<provider>:<day>`), so `reserved` survives a restart (memory discipline R5). The SPEND +
    the hard floor are A53's meter (installed with the back-off store). Emit the boot `[llm] pool …`
    line for the station provider and reflect its guest-readable atom. Idempotent.

    **Not best-effort.** A cell with no shared nucleus has no pool to back, and says so; anything
    else RAISES, so the boot phase reports `status=error` naming this body. It used to log the
    failure at `debug` and carry on, which is how a whole boot went by with the pool, the meter and
    the back-off all back in process memory and nothing in the log to say so."""
    from lib.akasha.workbench import llm_pool as _lpool
    nuc = getattr(kernel.manager, "shared_nucleus", None)
    if nuc is None:
        logger.info("[llm] pool store not installed — this cell has no shared nucleus")
        return
    _lpool.set_pool_store(
        load=lambda k: nuc.vault_retrieve("llm_pool", k),
        save=lambda k, d: nuc.vault_store("llm_pool", k, d))
    prov = _lprov.active(kernel)
    d = _lpool.day()
    # §4 — a reservation belongs to a RUN OF A PROCESS. It is settled at its job's terminal
    # transition, so one that is still open here was left by a process that is gone, and admission
    # would answer against a ceiling that much lower for the rest of the day (a boot inherited
    # `reserved=65` from jobs that no longer existed). Released before the line below reports the
    # pool, so the number in the log is the pool this process actually has. Every known provider,
    # not just the active one: a deploy that switched providers would otherwise strand the old
    # one's claim where nothing will ever read it again.
    for _p in set(_lpool.known_providers()) | {prov}:
        _n = _lpool.release_reservations(_p, d)
        if _n:
            logger.info("[llm] pool released stale reservations provider=%s n=%d", _p, _n)
    pv = _lpool.pool_view(prov, d)
    cap_calls, cap_tokens = _lpool.caps(prov)
    # `from=` is the diagnostic half: ONE effective ceiling is in force and a deploy can move it
    # from outside the process, so the number alone cannot say whether an override reached THIS
    # host. `default` on a cell whose deploy file sets a cap means the variable never arrived.
    logger.info("[llm] pool provider=%s day=%s cap=%s/%s from=%s spent=%s reserved=%s",
                prov, d, cap_calls or "∞", cap_tokens or "∞", _lpool.caps_source(prov),
                int(pv.get("spent_calls", 0)), int(pv.get("reserved", 0)))
    llm_pool_reflect(kernel, prov)


def install_llm_backoff_store(kernel) -> None:
    """R8 — back the llm_provider 429 back-off with the shared-nucleus vault (`llm_backoff/state`),
    then inherit + log any window still live from before the restart. Idempotent.

    Not best-effort, for the same reason as the pool store above: without it every boot re-hits the
    provider inside a live back-off window and A53's spend meter restarts at zero."""
    from lib.akasha.workbench import llm_provider as _lp
    nuc = getattr(kernel.manager, "shared_nucleus", None)
    if nuc is None:
        logger.info("[llm] back-off store not installed — this cell has no shared nucleus")
        return
    _lp.set_backoff_store(
        load=lambda: (nuc.vault_retrieve("llm_backoff", "state") or {}),
        save=lambda d: nuc.vault_store("llm_backoff", "state", d))
    _lp.load_persisted_backoff()
    # A53 — the free-tier BUDGET meter rides the same vault: what a restart forgets, it
    # overspends. Nothing else to wire — the gate lives at the llm_provider leaf, so every
    # programme sharing the one key is governed without knowing about it.
    _lp.set_meter_store(
        load=lambda: (nuc.vault_retrieve("llm_quota", "state") or {}),
        save=lambda d: nuc.vault_store("llm_quota", "state", d))


# B10-c — `llm_admission_log` is GONE. It logged a refusal a second time, from the caller, without
# the reason id or the numbers that explain it, and (until the shadowing fix) it raised on a tuple
# and logged nothing at all. The refusal is now logged once, by `llm_pool.reserve()` — the place
# that decided it — with `reason=<id>` and the `committed / headroom / cap` arithmetic. One
# guest-visible decision, one logged writer (seed-A order §0).


def llm_pool_reflect(kernel, provider: str) -> None:
    """B10 — write/refresh the guest-readable pool atom `llm:pool:<provider>:<day>` from the durable
    accounting (COUNTS only, never keys/prompts), joined to the telemetry day Set so retention
    compacts it. A stable alias-keyed atom whose META carries the counts (upsert on each change) —
    ONE atom per provider per day (bounded)."""
    try:
        from lib.akasha.workbench import llm_pool as _lpool
        nuc = getattr(kernel.manager, "shared_nucleus", None)
        if nuc is None:
            return
        d = _lpool.day()
        pv = _lpool.pool_view(provider, d)
        alias = "llm:pool:%s:%s" % (_lpool._norm(provider), d)
        import hashlib
        core = nuc.core
        key = core.get_key_by_alias(alias) or hashlib.sha256(alias.encode("utf-8")).hexdigest()
        meta = {"concept": "llm_pool", "provider": _lpool._norm(provider), "day": d,
                "provenance": "system",
                "capacity_calls": int(pv.get("capacity_calls", 0)),
                "capacity_tokens_est": int(pv.get("capacity_tokens_est", 0)),
                "reserved": int(pv.get("reserved", 0)),
                "spent_calls": int(pv.get("spent_calls", 0)),
                "spent_tokens_est": int(pv.get("spent_tokens_est", 0)),
                "refused": int(pv.get("refused", 0)),
                "by": pv.get("by", {})}
        content = "LLM pool %s %s" % (_lpool._norm(provider), d)
        core.put_chunk_raw(key, content, json.dumps(meta, ensure_ascii=False),
                           "system", "verified", time.time())
        core.put_chunk_access(key, ["scope:sys:universal"])
        try:
            core.put_alias(key, alias)
        except Exception:
            pass
        try:
            core.add_to_collection("telemetry:day:%s" % d, key)
        except Exception:
            pass
        # One line per reflect, so the guest-readable atom and the log agree or the log says why.
        # Without it, a reflect that wrote a stale view and a reflect that never ran looked the
        # same from outside — which is how the pool atom sat at the first airing's counts for a
        # whole day while Health kept climbing.
        logger.info("[llm] pool reflected provider=%s day=%s spent=%s pool_spent=%s reserved=%s "
                    "refused=%s runs=%s", meta["provider"], d, meta["spent_calls"],
                    int(pv.get("pool_spent_calls", 0)), meta["reserved"], meta["refused"],
                    sum(int((b or {}).get("runs", 0)) for b in (meta["by"] or {}).values()))
    except Exception as exc:
        # NOT debug: a reflect that fails makes the guest read lie, and it is the only writer of
        # that atom. Loud, with the exception named, and never fatal to the caller's airing.
        logger.warning("[llm] pool reflect FAILED provider=%s: %s: %s",
                       provider, type(exc).__name__, exc)


def handle_llm_budget(kernel, rid, data, session, scopes) -> dict:
    """[llm.budget [set <provider> [calls=N] [tokens_day=N] [tokens_month=N]]] Read or set the
    self-imposed spending ceiling.

    On a paid tier this IS the money knob, so it belongs to the operator and not to a release:
    baking it into the code would mean a rebuild and a redeploy to change what the month costs.
    Three dimensions, and they are not interchangeable — `calls` bounds how OFTEN, `tokens_day`
    bounds a DAY in money (cost is per token, so a call cap alone lets one fat day spend the
    month), `tokens_month` bounds the bill. 0 means unmetered, and is refused unless `force=yes`,
    because an unmetered paid key is a bill with no ceiling.

    Written to the host's env store (the same chmod-0600 file the keys use, never the repo or a
    seed) and applied LIVE, so a change takes effect on the next call without a restart.
    Librarian/admin; the ceiling reached is reported as OURS, never as the provider refusing."""
    if not ({"role:librarian", "role:superuser", "scope:sys:admin"} & set(scopes or [])):
        return _err(rid, -32001, "llm.budget requires a librarian/admin session")
    from lib.akasha.workbench import llm_provider as _llm
    from lib.akasha import secrets as _secrets
    action = str((data or {}).get("action") or "").strip().lower()
    prov = str((data or {}).get("provider") or "").strip().lower()
    if action not in ("set", ""):
        return _err(rid, -32602, "llm.budget takes no action, or `set <provider> …`")
    if action == "set":
        if not prov:
            return _err(rid, -32602, "llm.budget set requires a provider")
        fields = (("calls", "CALLS_PER_DAY"), ("tokens_day", "TOKENS_PER_DAY"),
                  ("tokens_month", "TOKENS_PER_MONTH"))
        wrote = {}
        force = str((data or {}).get("force") or "").strip().lower() in ("1", "yes", "true")
        for key, var in fields:
            raw = str((data or {}).get(key) or "").strip()
            if not raw:
                continue
            try:
                n = int(raw)
            except ValueError:
                return _err(rid, -32602, "%s must be a whole number (0 = unmetered)" % key)
            if n < 0:
                return _err(rid, -32602, "%s cannot be negative" % key)
            if n == 0 and not force:
                return _err(rid, -32602, "%s=0 means UNMETERED — an unmetered paid key is a bill "
                                         "with no ceiling. Pass force=yes if that is intended." % key)
            v = "AKASHA_LLM_%s_%s" % (prov.upper(), var)
            _secrets.set_var(kernel.base_dir, v, str(n))
            wrote[key] = n
        if not wrote:
            return _err(rid, -32602, "nothing to set: give calls= / tokens_day= / tokens_month=")
        logger.info("[llm] budget set provider=%s %s (live, persisted host-side)",
                    prov, " ".join("%s=%s" % kv for kv in sorted(wrote.items())))
        return _ok(rid, {"provider": prov, "set": wrote, "now": _llm.quota(prov),
                         "note": "applied live and persisted in the host env store; it is not "
                                 "in the repo or any seed"})
    provs = [prov] if prov else sorted(_llm.DEFAULT_MODELS)
    return _ok(rid, {"budgets": [_llm.quota(p) for p in provs],
                     "note": "a self-imposed ceiling, not the provider's. 0 = unmetered."})


def handle_llm_diag(kernel, rid, data, session, scopes) -> dict:
    """[llm.diag [provider=<p>] [model=<m>]] Ask the provider, NOW, why it is refusing.

    A 429 arms an hour-long back-off, so without this the only way to learn anything is to wait
    an hour per question — and the log line said `429` and nothing more, which cannot be acted
    on: a frequency cap, an exhausted monthly allowance and an inactive plan all return 429 and
    ask for opposite responses. This sends ONE minimal completion and reports the status, the
    provider's own message and its rate-limit headers, plus the self-imposed budget for context.

    It bypasses the back-off (that is the point of a diagnostic) but not the budget, and it is
    metered like any other call. The key is never returned. Librarian/admin only."""
    if not ({"role:librarian", "role:superuser", "scope:sys:admin"} & set(scopes or [])):
        return _err(rid, -32001, "llm.diag requires a librarian/admin session")
    from lib.akasha.workbench import llm_provider as _llm
    prov = (str((data or {}).get("provider") or "").strip().lower()
            or _lprov.active(kernel))
    r = _llm.probe(prov, str((data or {}).get("model") or "").strip())
    logger.info("[llm] diag provider=%s model=%s status=%s ok=%s msg=%s%s",
                r.get("provider"), r.get("model"), r.get("status"), r.get("ok"),
                str(r.get("message"))[:160],
                (" [%s]" % r["rate_headers"]) if r.get("rate_headers") else "")
    return _ok(rid, r)


def handle_llm_key(kernel, rid, data, session, scopes) -> dict:
    """[llm.key set <provider> <key> [base=<url>] | ls | rm <provider>] Store an LLM API key ONCE
    on this host so an operator NEVER touches Linux `export`. Written to a chmod-0600 secrets file
    under the data dir (gitignored, never in the repo/seed) and applied to the live environment;
    it is reloaded on every restart. `set openai … base=<url>` also stores AKASHA_LLM_BASE_URL
    for a generic EU OpenAI-compatible host. `ls` shows which providers have a key (masked).
    Librarian/admin only; keys stay env-only at runtime."""
    if not ({"role:librarian", "role:superuser", "scope:sys:admin"} & set(scopes or [])):
        return _err(rid, -32001, "llm.key requires a librarian/admin session")
    from lib.akasha import secrets as _secrets
    env_of = _LLM_KEY_ENV
    action = str((data or {}).get("action") or "ls").strip().lower()
    provider = str((data or {}).get("provider") or "").strip().lower()

    def _mask(v):
        return (v[:3] + "…" + v[-4:]) if v and len(v) > 10 else ("set" if v else "")

    if action in ("set", "add"):
        if provider not in env_of:
            return _err(rid, -32602, f"unknown provider '{provider}' (have {', '.join(env_of)})")
        key = str((data or {}).get("key") or "").strip()
        if not key:
            return _err(rid, -32602, "llm.key set requires a key: llm.key set <provider> <key>")
        var = env_of[provider]
        _secrets.set_var(kernel.base_dir, var, key)
        base = str((data or {}).get("base") or "").strip()
        if base and provider == "openai":
            _secrets.set_var(kernel.base_dir, "AKASHA_LLM_BASE_URL", base)
        return _ok(rid, {"stored": provider, "var": var, "value": _mask(key),
                         "base_url": base or None,
                         "note": "saved to the host secrets file + applied live; persists across "
                                 "restarts, no export needed). The next scheduled run uses it."})
    if action in ("rm", "remove", "del", "delete", "off"):
        if provider not in env_of:
            return _err(rid, -32602, f"unknown provider '{provider}' (have {', '.join(env_of)})")
        was = _secrets.remove_var(kernel.base_dir, env_of[provider])
        return _ok(rid, {"removed": provider, "was_set": was})
    present = {p: {"var": var, "set": bool(os.environ.get(var)), "value": _mask(os.environ.get(var, ""))}
               for p, var in env_of.items()}
    active = _lprov.active(kernel)
    try:                                  # A53 — what is left of the self-imposed free-tier budget
        from lib.akasha.workbench import llm_provider as _lp
        budget = _lp.quota(active)
    except Exception:
        budget = None
    return _ok(rid, {"providers": present, "active_provider": active, "budget": budget,
                     "base_url": os.environ.get("AKASHA_LLM_BASE_URL", "") or None})
