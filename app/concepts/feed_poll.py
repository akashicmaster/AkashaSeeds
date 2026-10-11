"""
APPLICATION module (group 4, 4.11): the live-telemetry feed poller drives application Concept Models by name, so it moved
here from the platform `source` package, unchanged in behaviour; its manifest entries moved with it
to the concepts manifest. Turning it into declared workloads is the application's next step.

The live-telemetry feed poller (svc:feed-poll) and feed.poll — moved out of the kernel (backend layout order 2026-09-20).

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
try:
    from lib.akasha.api.jobs import Worker as JCLWorker, Job as JCLJob, Step as JCLStep
    from lib.akasha.api.jobs import CLASS_BATCH_ATOM, CLASS_LINK, CLASS_MAINTENANCE
except ImportError:
    JCLWorker = None  # type: ignore
    JCLJob    = None  # type: ignore
    JCLStep   = None  # type: ignore
    CLASS_BATCH_ATOM = "batch_atom"  # type: ignore
    CLASS_LINK       = "link"        # type: ignore
    CLASS_MAINTENANCE = "maintenance"  # type: ignore
from lib.akasha.api.rpc import ok as _ok, err as _err

from lib.akasha.api.heart import _FEED_WRITER
import lib.akasha.api as _api

logger = logging.getLogger("Akasha.Kernel")


def provision_default_feeds(kernel) -> None:
    """Register / SYNC the built-in PUBLIC feeds (FeedConcept.DEFAULT_FEEDS), so a deployment fetches
    live telemetry with NO manual setup — the /archives/live/ map goes live on its own. The built-in
    feeds are CONFIG-AS-DATA: DEFAULT_FEEDS is authoritative, so a feed already registered from an
    OLDER build whose stored config (url/kind/interval/retain/map/title) has drifted is RE-REGISTERED
    to match the code — otherwise a map-DSL change (e.g. eonet's stamp=now/fold=latest) would never
    reach an existing deployment and that feed stays frozen on its old map. Re-register only refreshes
    the feed atom's meta; observations are separate atoms and are untouched. Runs as system.librarian
    (guaranteed role:librarian → the shared-nucleus write privilege, so a public guest reads the
    result), never a private cell. Best-effort — a failure here never blocks the poller."""
    try:
        FeedConcept = _api.concept_class(kernel, "feed")
        defaults = list(getattr(FeedConcept, "DEFAULT_FEEDS", None) or [])
        if not defaults:
            return
        sess = kernel.manager.get_session(_FEED_WRITER)
        fc = FeedConcept(sess)
        new = synced = 0
        for f in defaults:
            fid = f["id"]
            want = {"url": f.get("url", ""), "kind": f.get("kind", ""),
                    "interval": int(f.get("interval", 300)), "retain": str(f.get("retain", "72h")),
                    "map": f.get("map", ""), "title": f.get("title", "")}
            _, meta = fc._feed_meta(fid)                 # stored config, or {} if not registered
            if not meta:
                action = "new"
            else:
                have = {"url": meta.get("url", ""), "kind": meta.get("kind", ""),
                        "interval": int(meta.get("interval", 0) or 0), "retain": str(meta.get("retain", "")),
                        "map": meta.get("map", ""), "title": meta.get("title", "")}
                if have == want:
                    continue                             # already in sync — no write
                action = "sync"
            fc.op_register(id=fid, url=want["url"], kind=want["kind"], interval=want["interval"],
                           retain=want["retain"], map=want["map"], title=want["title"])
            if action == "new":
                new += 1
            else:
                synced += 1
        if new or synced:
            logger.info("[Kernel] feed auto-provision: %d registered, %d re-synced to DEFAULT_FEEDS",
                        new, synced)
    except Exception as exc:
        logger.info("[Kernel] feed auto-provision skipped (non-fatal): %s", exc)


def feed_registered(kernel, session) -> list:
    """The feeds ACTUALLY registered + visible (the truth for status). Reads via the caller's
    session — so it reflects what a public reader sees (feeds published to the shared nucleus)."""
    try:
        FeedConcept = _api.concept_class(kernel, "feed")
        rows = (FeedConcept(session).op_feeds() or {}).get("feeds", []) or []
        return [{"id": (r.get("id", "") or "").replace("feed:", ""), "obs": r.get("observations")} for r in rows]
    except Exception:
        return []


# ── the poller is GONE (reference-templates-and-profiles §5, 10-02) ───────────────────────────────────
# `svc:feed-poll` — one supervised thread that submitted a `feed.pull` job for every DUE feed — is replaced
# by one declared WORKLOAD per feed (`app/config/workbench/workloads/<feed>.json`, template
# `app/config/workbench/telemetry/templates/<feed>.ak` = one `feed.pull id=<feed>` step). The cadence is the
# declaration's `trigger`, the driver is the one clock, each run records its own outcome (a feed that is
# down is a run with its reason, not a log line), and one feed failing stops only itself. What is left here
# is registering the built-in feeds, which a workload's `feed.pull` needs to find.


def schedule_feed_defaults(kernel) -> None:
    """Boot schedule (writer phase, every boot): register / sync the built-in PUBLIC feeds
    (`FeedConcept.DEFAULT_FEEDS`) — idempotent, so a feed edited in code is re-synced on the next boot.
    The pulls themselves are the telemetry workloads', not this schedule's."""
    provision_default_feeds(kernel)


def handle_feed_poll(kernel, rid, data, session, scopes) -> dict:
    """[feed.poll on|off|status] The live-telemetry feeds, from the prompt (librarian/admin).

    Polling is no longer a thread: each feed is a declared workload `telemetry/<feed>`. So `status`
    reports the registered feeds and the workload key each is polled under (read the run with
    `workload.status key=telemetry/<feed>`); `on` (re)registers the built-in feeds, idempotently; `off`
    does nothing but say how a feed is stopped — retire its workload (`workload.retire`), or delete its
    declaration — because a persisted opt-out beside the declarations would be a second author of
    whether a feed runs."""
    if not ({"role:librarian", "role:superuser", "scope:sys:admin"} & set(scopes or [])):
        return _err(rid, -32001, "feed.poll requires a librarian/admin session")
    action = str((data or {}).get("action") or (data or {}).get("state") or "status").strip().lower()
    if action in ("on", "start", "enable", "1", "true", "yes"):
        provision_default_feeds(kernel)
    reg = feed_registered(kernel, session)
    ids = [str(f.get("id") if isinstance(f, dict) else f) for f in (reg or [])]
    out = {"poll": "workloads", "registered": reg,
           "workloads": ["telemetry/%s" % i for i in ids if i]}
    if action in ("off", "stop", "disable", "0", "false", "no"):
        out["note"] = ("polling is a workload per feed: stop one with `workload.retire key=telemetry/<feed>` "
                       "(or delete its declaration)")
    return _ok(rid, out)
