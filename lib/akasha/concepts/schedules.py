"""
Concept-model boot schedules (labo register, pulse compact), moved out of the kernel (backend layout order 2026-09-20). Bodies verbatim except `self.` → `kernel.`.

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
from lib.akasha.identity import Role, Capability
from lib.akasha.api.trust import (TRUST_NETWORK, TRUST_LOCAL, TRUST_INTERNAL,
                                  TRUSTED_TRANSPORTS as _TRUSTED_TRANSPORTS)
from lib.akasha.api.heart import _rss_mb, _search_partial_incr, _SEARCH_PARTIAL, _MAINT_LOCK, _MAINT_LAST_DONE, _MAINT_GAP_S, _MAINT_GATE_AVAIL_MB, _MAINT_GATE_MAX_WAIT_S, _MAINT_GATE_RETRY_S, _maint_gate_ok, _run_gated_maint, _with_rss_delta, _mem_available_mb, _smaps_rollup, _thread_count, _open_fd_count, _fd_soft_limit, _autolearn_disabled_reason

logger = logging.getLogger("Akasha.Kernel")


def schedule_pulse_compact(kernel) -> None:
    """C1/F44 — run the nightly pulse compaction from the WRITER, boot-if-behind. The recorder's
    own day-rollover trigger lives in the web-portal process, which respawns every deploy (lately
    ~15 min), so a process that never lives across midnight never compacts — the raw pulse events
    pile up unbounded (a permanent-RAM accumulator in ram-value mode). The writer daemon is
    long-lived (and catches up on boot), so it is the right home. Persists the last-compacted day
    in the vault; compacts whenever the UTC day has advanced past it."""
    nucleus = getattr(kernel.manager, "shared_nucleus", None)
    if nucleus is None:
        return

    def _today():
        return time.strftime("%Y-%m-%d", time.gmtime())

    def _run():
        from lib.akasha import lifecycle
        deadline = time.time() + 7200
        while time.time() < deadline:
            if lifecycle.is_shutting_down():
                return
            if kernel._relations_ready():
                break
            time.sleep(5)
        _keep = 2
        try:
            _keep = max(0, int(os.environ.get("AKASHA_PULSE_KEEP_DAYS", "2") or "2"))
        except (TypeError, ValueError):
            _keep = 2
        while not lifecycle.is_shutting_down():
            try:
                last = nucleus.vault_retrieve("pulse", "last_compact_day") or ""
                today = _today()
                if today != last:
                    # Dispatch internally as the system librarian (holds write; internal trust
                    # allows the bare id). Idempotent — already-summarised days are skipped.
                    # A48.3 — Δrss on the task so the A30 nightly step is attributed per task.
                    # A56 §4 — behind the shared serialised memory/queue gate.
                    resp = _run_gated_maint("pulse.compact", lambda: _with_rss_delta(
                        "pulse.compact", lambda: kernel.dispatch(
                            {"jsonrpc": "2.0", "method": "pulse.compact",
                             "params": {"client_id": "system.librarian", "data": {"keep": _keep}},
                             "id": "pc"}, TRUST_INTERNAL), concurrent=kernel._concurrent_jobs))
                    if resp is None:                    # gate skipped / shutting down — retry later
                        for _ in range(int(3600 / 0.5)):
                            if lifecycle.is_shutting_down():
                                return
                            time.sleep(0.5)
                        continue
                    res = (resp or {}).get("result") or {}
                    nucleus.vault_store("pulse", "last_compact_day", today)
                    logger.info("[pulse] nightly compaction ran (writer) — days=%s evicted=%s",
                                res.get("days_compacted"), res.get("events_evicted"))
            except Exception as exc:
                logger.debug("[pulse] compaction check skipped: %s", exc)
            for _ in range(int(3600 / 0.5)):        # re-check ~hourly for a day rollover
                if lifecycle.is_shutting_down():
                    return
                time.sleep(0.5)

    import threading as _thr
    _thr.Thread(target=_run, name="pulse-compact", daemon=True).start()


def schedule_semcache_featured(kernel) -> None:
    """Semantic macro-cache §12.5 — the deploy-time INITIAL value. On a tier whose seed bundles
    config/semcache_featured.json, populate `set:stage:featured` ONCE from bundled curated sources so
    the cache is ACTIVE from a fresh deploy (instead of OFF until someone hand-curates). Properties,
    all held here:
      • config-gated — ONLY the tier that ships the config runs it (a personal seeds cell ships no
        config → its cache stays OFF, the design's opt-in contract §6);
      • run-once — fsync'd filesystem sentinel;
      • NON-CLOBBERING — if an operator has already curated `set:stage:featured`, it is left as-is;
      • writer-only + serve-first — gated on AKASHA_SERVE_ONLY and the boot heartbeat, dispatched as
        the boot admin over TRUST_INTERNAL;
      • after seeding it fires ONE cache.replan so the plan is authored this generation.
    Sources: the bundled curated demo sets (`from_sets`) UNIONed, plus the top-`top_salient` public
    concepts (the sitemap canonical backbone — design §6 'the sitemap canonical set could BE the
    seed'), both bounded."""
    if os.environ.get("AKASHA_SERVE_ONLY", "").strip().lower() not in ("", "0", "no", "false", "off"):
        return  # only the sole nucleus writer seeds it
    import json as _json
    _project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    cfg_path = os.path.join(_project_dir, "config", "semcache_featured.json")
    try:
        with open(cfg_path, "r", encoding="utf-8") as _f:
            cfg = _json.load(_f)
    except Exception:
        return  # not configured for this tier → the cache stays OFF (opt-in)
    if not cfg.get("enabled"):
        return
    nucleus = getattr(kernel.manager, "shared_nucleus", None)
    core = getattr(nucleus, "core", None) if nucleus is not None else None
    if core is None:
        return

    def _run():
        from lib.akasha import lifecycle
        deadline = time.time() + 7200
        while time.time() < deadline:
            if lifecycle.is_shutting_down():
                return
            if kernel._relations_ready():
                break
            time.sleep(5)
        if lifecycle.is_shutting_down():
            return
        _hb = os.path.join(kernel.base_dir, "central", "boot.heartbeat")   # serve-first
        _dl = time.time() + 900
        while time.time() < _dl and os.path.exists(_hb):
            if lifecycle.is_shutting_down():
                return
            time.sleep(2)
        try:
            sent_dir = os.path.join(kernel.base_dir, "central", "sentinels")
            os.makedirs(sent_dir, exist_ok=True)
            done = os.path.join(sent_dir, "semcache_featured_v1.done")
            if os.path.exists(done):
                return
            added, existing = semcache_apply_featured(kernel, core, cfg)
            if added:
                # F57 §2.1 — report the DISTINCT membership too: `added` is a per-add counter that
                # double-counts atoms shared across from_sets, so it disagrees with the planner's
                # `seed=` (which reads the deduplicated set). Print both so the two never look wrong.
                try:
                    import lib.akasha.concepts.cache as _cm
                    members = len(core.get_collection_members(_cm.FEATURED) or [])
                except Exception:
                    members = added
                logger.info("[semcache.featured] seeded set:stage:featured — adds=%d members=%d "
                            "(from_sets=%d, top_salient=%d) — the semantic cache is now active on "
                            "this deploy", added, members, len(cfg.get("from_sets") or []),
                            int(cfg.get("top_salient", 0) or 0))
            elif existing:
                logger.info("[semcache.featured] set:stage:featured already curated (%d members) — "
                            "leaving the operator's curation untouched", existing)
            try:                                             # run-once even when we skipped
                with open(done, "w") as _f:
                    _f.write("1"); _f.flush(); os.fsync(_f.fileno())
            except Exception:
                pass
            if added or existing:                            # author the plan now
                kernel.dispatch({"jsonrpc": "2.0", "method": "cache.replan",
                               "params": {"client_id": "system.librarian", "data": {}},
                               "id": "scfr"}, TRUST_INTERNAL)
        except Exception as exc:
            logger.debug("[semcache.featured] seeding skipped: %s", exc)

    import threading as _thr
    _thr.Thread(target=_run, name="semcache-featured", daemon=True).start()


def semcache_apply_featured(kernel, core, cfg) -> tuple:
    """Populate set:stage:featured from the config sources, NON-CLOBBERING (pure — no sentinel/gating,
    so it is unit-testable). Sources: (a) the bundled curated demo sets in `from_sets`, UNIONed; and
    (b) the top-`top_salient` public concepts by salience (the sitemap canonical backbone, §6),
    resolved by alias. Both bounded. Returns (added, existing_count): if featured is already
    curated, returns (0, N) and touches nothing."""
    import lib.akasha.concepts.cache as _cache_mod
    FEATURED = _cache_mod.FEATURED
    try:
        existing = list(core.get_collection_members(FEATURED) or [])
    except Exception:
        existing = []
    if existing:
        return 0, len(existing)
    added = 0
    for s in (cfg.get("from_sets") or []):                # (a) bundled curated demo sets
        try:
            for k in (core.get_collection_members(s) or []):
                core.add_to_collection(FEATURED, k)
                added += 1
        except Exception:
            pass
    topn = int(cfg.get("top_salient", 0) or 0)            # (b) top-salient public concepts
    # …through the read that DECLARES itself the glossary (`projection.reference.role`), never by
    # name (group 4, 4.13). None declared → the backbone is skipped, the curated sets still seed.
    from lib.akasha.api import manifest as _manifest
    glossary = _manifest.declared_reference("glossary")
    if topn > 0 and not glossary:
        logger.info("[semcache.featured] top_salient skipped reason=no_glossary_declared")
    if topn > 0 and glossary:
        try:
            r = kernel.dispatch({"jsonrpc": "2.0", "method": glossary,
                               "params": {"session_token": "admin", "data": {"limit": topn}},
                               "id": "scf"}, TRUST_INTERNAL)
            cs = ((r.get("result") or {}).get("concepts") if isinstance(r, dict) else None) or []
            cs.sort(key=lambda c: c.get("salience") or 0, reverse=True)
            for c in cs[:topn]:
                nm = c.get("name") or c.get("term")
                key = core.get_key_by_alias(nm) if nm else None
                if key:
                    core.add_to_collection(FEATURED, key)
                    added += 1
        except Exception as _e:
            logger.debug("[semcache.featured] top-salient seed skipped: %s", _e)
    return added, 0


def schedule_validity_expiry(kernel) -> None:
    """B3 §A8 — a nightly phase that evicts EXPIRED atoms from the horizon. An atom that expires joins
    `set:valid:until:<clock>:<pos>` at write time (`cronon.valid_until`), indexed in
    `set:valid:until:all`. Once the clock passes `<pos>` its members leave the horizon (semcache /
    RAM index) the way `telemetry.evict` drops — the STORE is never touched. Reads only the bounded
    index (O(#membranes)); the plant bench has none, so the phase logs `moved=0`. Writer-role only."""
    if os.environ.get("AKASHA_SERVE_ONLY", "").strip().lower() not in ("", "0", "no", "false", "off"):
        return

    def _run():
        from lib.akasha import lifecycle
        nucleus = getattr(kernel.manager, "shared_nucleus", None)
        last = ""
        while not lifecycle.is_shutting_down():
            try:
                today = time.strftime("%Y-%m-%d", time.gmtime())
                if today != last and nucleus is not None:
                    _run_gated_maint("validity.expire", functools.partial(retention_expire_validity, kernel))
                    last = today
            except Exception as exc:
                logger.debug("[retention] validity check skipped: %s", exc)
            for _ in range(int(3600 / 0.5)):             # re-check ~hourly for a day rollover
                if lifecycle.is_shutting_down():
                    return
                time.sleep(0.5)

    import threading as _thr
    _thr.Thread(target=_run, name="validity-expiry", daemon=True).start()


def retention_expire_validity(kernel) -> dict:
    """B3 §A8 — evict the members of every `set:valid:until:<clock>:<pos>` whose `<pos>` is at or below
    the clock's current position out of the horizon (the semcache warm plan + L1), logging
    `[retention] expired clock=<c> upto=<pos> moved=<n>` per membrane. The STORE is untouched — the
    atom stays readable; only its horizon residency is dropped. Bounded: reads `set:valid:until:all`
    (the write-time index), never the store. Returns {membranes, moved} (the test seam)."""
    from lib.akasha.concepts.cronon import CrononConcept
    from lib.akasha.api import authority as _authority
    cc = CrononConcept(_authority.elevated(kernel, "retention.expiry"))
    membranes = moved = 0
    for ik in cc._members("set:valid:until:all"):
        im = cc._meta(cc._alias(ik) or ik) or {}
        if im.get("concept") != "validity_membrane" or im.get("expired"):
            continue                                      # already retired — evicting is idempotent,
        clock, pos = im.get("clock") or "", int(im.get("pos") or 0)   #   but the count is paid once
        now = cc._akasha_now(clock)                       # the clock's current position (no advance)
        if pos > now:                                     # not yet expired
            continue
        vset = cc._valid_set(clock, pos)
        keys = list(cc._members(vset))
        for mk in keys:
            evict_from_horizon(kernel, cc._alias(mk) or mk)  # best-effort; store untouched
        cc._set_meta(cc._key(cc._alias(ik) or ik), "expired", True)   # retire this membrane
        membranes += 1
        moved += len(keys)
        logger.info("[retention] expired clock=%s upto=%d moved=%d", clock, pos, len(keys))
    if membranes == 0:
        logger.info("[retention] expired clock=- upto=- moved=0 (no validity membranes)")
    return {"membranes": membranes, "moved": moved}


def evict_from_horizon(kernel, alias: str) -> None:
    """B3 §A8 — drop one atom from the horizon (semcache warm plan + L1 render cache) WITHOUT touching
    the store. Best-effort: the atom remains fully readable from the store; only its RAM residency is
    released, exactly as `telemetry.evict` drops without deleting the source."""
    try:
        store = getattr(kernel, "_snapshot_store", None) or getattr(kernel, "snapshot_store", None)
        if store is not None and hasattr(store, "drop"):
            store.drop(alias)
    except Exception:
        pass
    try:
        cache = getattr(kernel, "_ATOM_HTML_CACHE", None)
        if cache is not None and hasattr(cache, "pop"):
            cache.pop(alias, None)
    except Exception:
        pass


# ── the consent migration: a society's `public` flag becomes the FACT Set, once ─────────────────
#
# WHY THIS EXISTS. `set:society:public` is the fact step 4 of the gate consults, and it is written
# by `society.public` and by `society.new public=yes`. Neither of those runs for a society that
# already exists: `society.new` returns `exists` and states nothing, and the every-boot
# reconciliation writes only the FIVE DECLARED programmes. So the hand-made public societies —
# `hall`, `akashapolis`, `plants-lab` — are written by nobody, and on the first boot after the
# gate lands their guest reads and their `publish` are refused with `reason=public`.
#
# The consent itself is not lost: it lives in the group-local Set `soc:public:<gid>` (and its
# sibling `soc:open_guest:<gid>`), which is where `society.new` has always put it. What is missing
# is the universal statement of it. So this is a projection, not a decision — it never opens a
# space that was not already open, and it cannot: every key it states is one it read out of that
# group's own consent Set.
#
# (The order asked for the source to be the society's stored META. It is not there — `op_new`'s
# meta carries type/group/name/topic/kind/category/identity/created_by and no consent field; the
# Set is the only place the flag has ever lived. Both are read anyway, so a society from some
# older build that did carry it in meta is migrated too, and the union is the safe direction.)
#
# ONCE, by a sentinel of its own, for the same reason `gate.migrate` has one: a repeat is harmless
# (the fact write is idempotent) but a migration nobody can date is a migration nobody can reason
# about. `when: every_boot` — an existing cell is by definition not a new build, and gating it on
# `new_build` is exactly how it would never run on the cell that needs it.
#
# THE SENTINEL IS VERSIONED WITH THE MIGRATION (D3). The v1 run landed its sentinel on the live
# cell and the hand-made spaces were still not public to a guest; the corrected migration — the
# one that names the keys it stated — could then never run there, because the v1 file said a
# migration had happened and the file cannot say WHICH. A fixed migration is a different
# migration, so it carries a different version and runs once on its own account. The v1 file is
# left where it is: it is the record that v1 ran, and deleting it would destroy the only evidence
# of the thing being investigated.
#
# This is why the repeat has to be harmless by construction rather than by luck — and it is: every
# key stated is read out of that group's own consent Set, so a second pass over an already-migrated
# cell states the same facts about the same groups and changes nothing.
_CONSENT_MIGRATION_VERSION = "v2"


def schedule_society_consent_migrate(kernel) -> None:
    """Seed `set:society:public` from every group's existing `soc:public:<gid>` Set, once."""
    sent_dir = os.path.join(kernel.base_dir, "central", "sentinels")
    done = os.path.join(sent_dir, "society_consent_%s.done" % _CONSENT_MIGRATION_VERSION)
    if os.path.exists(done):
        return
    try:
        stated, guest_fixed, groups, keys = migrate_society_consent(kernel)
    except Exception as exc:                     # noqa: BLE001 — a boot never dies of bookkeeping
        logger.warning("[society] consent migration skipped: %s: %s", type(exc).__name__, exc)
        return
    try:
        os.makedirs(sent_dir, exist_ok=True)
        with open(done, "w", encoding="utf-8") as fh:
            # The keys go IN THE SENTINEL too. The log rotates; the sentinel is the durable record
            # of what this migration did, and "which spaces" is the question it exists to answer.
            fh.write("%s public=%d open_guest=%d groups=%d keys=%s\n"
                     % (time.strftime("%Y-%m-%d"), stated, guest_fixed, groups,
                        ",".join(keys) or "-"))
            fh.flush()
            os.fsync(fh.fileno())                # crash-stop: the sentinel is on disk, not in a page
    except OSError as exc:
        logger.warning("[society] consent migration ran but its sentinel did not land: %s", exc)
    logger.info("[society] consent migrated %s groups=%d public=%d open_guest=%d public_keys=[%s] "
                "— the hand-made public spaces state their consent where the gate reads it",
                _CONSENT_MIGRATION_VERSION, groups, stated, guest_fixed, ",".join(keys))


def migrate_society_consent(kernel):
    """The body, separate from the schedule so an eval can call it directly.

    Returns (public_stated, open_guest_restated, groups_seen, public_keys). Reads each group's own
    consent Sets and states what it finds; it never reads a declaration and never opens anything.

    IT RETURNS THE KEYS, AND THE LINE PRINTS THEM (D3). `public=5` is not an answer to "is the hall
    public now?" — it is a number that is equally consistent with five OTHER spaces having been
    migrated, which is exactly the ambiguity the live cell was left in. A migration that states a
    fact about a named thing names it; then a reader can tell "the space is called something else"
    from "the fact was written and then lost" without a second investigation."""
    from lib.akasha.api import facts as _facts
    from lib.akasha.concepts.society import SocietyConcept
    stated = guest_fixed = groups = 0
    keys = []
    for row in (kernel.iam.list_groups() or []):
        gid = str(row.get("group_id") or "").strip()
        if not gid:
            continue
        # EACH GROUP'S OWN ADMIN opens it. A session for the literal `admin` carries the
        # operator's cell-wide SCOPES (the bootstrap file names that row) but no GROUP ENGINES,
        # because those come from IAM membership and nobody is a member of a group they did not
        # join. On a cell whose operator is `henri` that means every group looked unreadable and
        # the migration reported `groups=0` — a silent success that migrated nothing.
        soc = SocietyConcept(kernel.manager.get_session(str(row.get("admin") or "admin")))
        try:
            ge = soc._group_engine(gid)
        except RuntimeError:
            continue                             # nobody available to this boot holds the group
        groups += 1
        core = ge.core
        for set_name, is_public in ((soc._public_set(gid), True), (soc._guest_set(gid), False)):
            for key in (core.get_collection_members(set_name) or []):
                meta = soc._society_meta(ge, key) or {}
                name = str(meta.get("name") or "").strip()
                if not name:
                    continue
                if is_public:
                    _sid = soc._sid(gid, name)
                    _facts.public(kernel, _sid, True)
                    keys.append(_sid)
                    stated += 1
                else:
                    guest_fixed += 1             # already group-local, where `_is_open_guest` reads
        # …and the same flag where an older build may have left it: on the society's own meta.
        for key in (core.get_collection_members("societies:%s" % gid) or []):
            meta = soc._society_meta(ge, key) or {}
            name = str(meta.get("name") or "").strip()
            if name and meta.get("public") and not soc._public_fact(gid, name):
                _sid = soc._sid(gid, name)
                _facts.public(kernel, _sid, True)
                keys.append(_sid)
                stated += 1
            if name and meta.get("open_guest") and not soc._is_open_guest(ge, gid, key):
                ge.add_to_set(soc._guest_set(gid), key)
                guest_fixed += 1
    return stated, guest_fixed, groups, sorted(set(keys))
