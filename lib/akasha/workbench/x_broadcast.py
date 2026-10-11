"""
x_broadcast — minimal, degradation-first poster for X (Twitter) API v2.

Stdlib only (urllib + hmac + hashlib; honours HTTPS_PROXY). Credentials come from the ENVIRONMENT,
NEVER an atom or a seed (same rule as the LLM keys) — the operator stores them once via the `x.key`
command, which writes them to data/central/secrets.env (chmod 0600) and loads them at kernel init.

Posting a tweet is a USER-CONTEXT action, so X requires OAuth 1.0a signing (a bearer/app token cannot
post). Four long-lived credentials from the X developer portal ("Keys and tokens"):

    AKASHA_X_CONSUMER_KEY      (API Key)
    AKASHA_X_CONSUMER_SECRET   (API Key Secret)
    AKASHA_X_ACCESS_TOKEN      (Access Token)
    AKASHA_X_ACCESS_SECRET     (Access Token Secret)

Every call returns a result dict or None on ANY failure (missing creds, rate limit, network, API
error) — the caller degrades gracefully and NOTHING is posted. This module NEVER raises.

⚠️ Posting is irreversible and public. The caller (the station X relay) gates every real post behind
an explicit opt-in AND the society's `public` consent AND these creds being present; with no creds
this module reports `available() == False` and the relay stays inert.
"""
import base64
import hashlib
import hmac
import json
import logging
import os
import time
import urllib.error
import urllib.parse
import urllib.request

logger = logging.getLogger("akasha.x_broadcast")

_API = "https://api.twitter.com/2/tweets"
_ENV = ("AKASHA_X_CONSUMER_KEY", "AKASHA_X_CONSUMER_SECRET",
        "AKASHA_X_ACCESS_TOKEN", "AKASHA_X_ACCESS_SECRET")

# The four credential names the `x.key` command accepts (short alias → env var), so the operator can
# type `x.key consumer_key=… consumer_secret=… access_token=… access_secret=…`.
KEY_ALIASES = {
    "consumer_key": "AKASHA_X_CONSUMER_KEY",
    "consumer_secret": "AKASHA_X_CONSUMER_SECRET",
    "access_token": "AKASHA_X_ACCESS_TOKEN",
    "access_secret": "AKASHA_X_ACCESS_SECRET",
}


def _creds():
    ck, cs, at, asec = (os.environ.get(n, "").strip() for n in _ENV)
    if ck and cs and at and asec:
        return ck, cs, at, asec
    return None


def available() -> bool:
    """True iff all four OAuth 1.0a credentials are present. With any missing, the relay stays inert."""
    return _creds() is not None


def _q(s: str) -> str:
    """RFC 3986 percent-encoding for OAuth (unreserved = A-Za-z0-9-._~ left as-is)."""
    return urllib.parse.quote(str(s), safe="~")


def _auth_header(method: str, url: str, ck: str, cs: str, at: str, asec: str) -> str:
    """Build the OAuth 1.0a Authorization header. The tweet body is JSON, so (per the spec) only the
    oauth_* params enter the signature base string — the JSON body is NOT signed."""
    oauth = {
        "oauth_consumer_key": ck,
        "oauth_nonce": base64.b64encode(os.urandom(24)).decode().strip("=").replace("+", "").replace("/", ""),
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_token": at,
        "oauth_version": "1.0",
    }
    base = "&".join([method.upper(), _q(url),
                     _q("&".join(f"{_q(k)}={_q(oauth[k])}" for k in sorted(oauth)))])
    signing_key = f"{_q(cs)}&{_q(asec)}"
    sig = base64.b64encode(hmac.new(signing_key.encode(), base.encode(), hashlib.sha1).digest()).decode()
    oauth["oauth_signature"] = sig
    return "OAuth " + ", ".join(f'{_q(k)}="{_q(v)}"' for k, v in sorted(oauth.items()))


def post_tweet(text: str, reply_to: str = "", timeout: float = 20.0):
    """Post ONE tweet (optionally as a reply, to build a thread). Returns {"id": <tweet_id>} on success,
    or None on ANY failure. Never raises. `text` is sent as-is (caller truncates to <=280)."""
    creds = _creds()
    if not creds or not (text or "").strip():
        return None
    ck, cs, at, asec = creds
    body = {"text": text}
    if str(reply_to or "").strip():
        body["reply"] = {"in_reply_to_tweet_id": str(reply_to).strip()}
    try:
        data = json.dumps(body).encode()
        req = urllib.request.Request(_API, data=data, method="POST", headers={
            "Authorization": _auth_header("POST", _API, ck, cs, at, asec),
            "Content-Type": "application/json",
        })
        with urllib.request.urlopen(req, timeout=timeout) as r:
            out = json.loads(r.read().decode())
        tid = (out.get("data") or {}).get("id")
        return {"id": tid} if tid else None
    except urllib.error.HTTPError as e:
        # F24: NAME the failure. X returns the exact cause in the JSON body (e.g. "duplicate content",
        # OAuth signature, app permissions), and each status has a DIFFERENT remedy — 401 (auth),
        # 403 (permissions/duplicate), 429 (rate limit). Log ONE line with status + body; never the
        # credentials (they are only in the Authorization header, never logged). Never raises.
        try:
            _body = e.read().decode("utf-8", "replace")[:500]
        except Exception:
            _body = "<no body>"
        logger.warning("[x_broadcast] post failed: HTTP %s — %s", getattr(e, "code", "?"), _body)
        return None
    except Exception as e:
        logger.warning("[x_broadcast] post failed: %s: %s", type(e).__name__, e)
        return None


def post_thread(tweets, timeout: float = 20.0):
    """Post a list of tweet texts as a REPLY CHAIN (tweet[0], then each replying to the previous).
    Returns {"ids": [...], "posted": n} — partial on a mid-thread failure (the chain stops, nothing is
    retried). Returns None if no creds or the first post fails (nothing went out)."""
    tweets = [t for t in (tweets or []) if (t or "").strip()]
    if not tweets or not available():
        return None
    ids, prev = [], ""
    for t in tweets:
        r = post_tweet(t, reply_to=prev, timeout=timeout)
        if not r or not r.get("id"):
            break
        ids.append(r["id"])
        prev = r["id"]
    if not ids:
        return None
    return {"ids": ids, "posted": len(ids)}


# ── the op that stores the credential, and the hook that posts ──────────────────────────────────
# Both are platform: writing a provider credential to a chmod-0600 file, and speaking HTTP to a
# channel, are the same kind of thing as a disk or a socket. What a THREAD says, when it goes out
# and whether it goes at all are the application's — they live in the workload declaration and in
# the concept that formats the beats (step 1 §1.2). This file holds no schedule, no opt-in file and
# no idea of what is being posted.

_KEY_FIELDS = tuple(KEY_ALIASES)


def handle_x_key(kernel, rid, data, session, scopes) -> dict:
    """[x.key set <consumer_key> <consumer_secret> <access_token> <access_secret> | ls | rm] Store the
    four channel OAuth 1.0a credentials ONCE on this host (chmod-0600 secrets file, never in the
    repo/seed, applied live + reloaded on restart) so the operator never touches `export`. `ls` shows
    which are set (masked). Librarian/admin only; keys stay env-only at runtime."""
    from lib.akasha.api.rpc import ok as _ok, err as _err
    from lib.akasha import secrets as _secrets
    if not ({"role:librarian", "role:superuser", "scope:sys:admin"} & set(scopes or [])):
        return _err(rid, -32001, "x.key requires a librarian/admin session")
    action = str((data or {}).get("action") or "ls").strip().lower()

    def _mask(v):
        return (v[:3] + "…" + v[-4:]) if v and len(v) > 10 else ("set" if v else "")

    if action in ("set", "add"):
        vals = {f: str((data or {}).get(f) or "").strip() for f in _KEY_FIELDS}
        given = {f: v for f, v in vals.items() if v}
        if not given:
            return _err(rid, -32602, "x.key set requires the four values: x.key set "
                                     "<consumer_key> <consumer_secret> <access_token> <access_secret>")
        for f, v in given.items():
            _secrets.set_var(kernel.base_dir, KEY_ALIASES[f], v)
        return _ok(rid, {"stored": sorted(given), "complete": available(),
                         "note": "saved to the host secrets file + applied live (persists across "
                                 "restarts, no export). Preview a thread with the publishing op's `dry=yes`."})
    if action in ("rm", "remove", "del", "delete", "off"):
        for var in KEY_ALIASES.values():
            _secrets.remove_var(kernel.base_dir, var)
        return _ok(rid, {"removed": "x credentials"})
    present = {f: _mask(os.environ.get(KEY_ALIASES[f], "")) for f in _KEY_FIELDS}
    return _ok(rid, {"credentials": present, "complete": available()})


def post_thread_hook(tweets, dry=False):
    """The `channel.x.post_thread` hook (step 2 §1) — what the application calls to make a thread go.

    `dry` is the caller's word for "show me what would go out": it returns the same shape with
    `dry: True` and NOTHING is sent. That belongs here rather than at the caller because a dry run
    that still posted would be a silent, irreversible, public mistake, and the one place that can
    guarantee it did not is the place that would have made the call.

    Degradation-first like the rest of this module: no credentials, or any failure, is `None`."""
    texts = [str(t) for t in (tweets or []) if str(t or "").strip()]
    if not texts:
        return None
    if dry:
        return {"dry": True, "would_post": len(texts), "tweets": texts,
                "creds": available(), "ids": []}
    return post_thread(texts)
