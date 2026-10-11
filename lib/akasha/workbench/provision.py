"""
The ONE provisioning authority: every declared workload — its bench, society, casts, capabilities and resources — reconciled at boot from the declarations as the boot admin — moved out of the kernel (backend layout order 2026-09-20).

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
from lib.akasha.api.trust import (TRUST_NETWORK, TRUST_LOCAL, TRUST_INTERNAL,
                                  TRUSTED_TRANSPORTS as _TRUSTED_TRANSPORTS)
from lib.akasha.api.heart import _NucleusWriteCtx, _FEED_WRITER, _BROADCASTER
from lib.akasha.api.heart import _rss_mb, _search_partial_incr, _SEARCH_PARTIAL, _MAINT_LOCK, _MAINT_LAST_DONE, _MAINT_GAP_S, _MAINT_GATE_AVAIL_MB, _MAINT_GATE_MAX_WAIT_S, _MAINT_GATE_RETRY_S, _maint_gate_ok, _run_gated_maint, _with_rss_delta, _mem_available_mb, _smaps_rollup, _thread_count, _open_fd_count, _fd_soft_limit, _autolearn_disabled_reason
from lib.akasha.workbench import workload
from lib.akasha.api import facts as _facts
from lib.akasha.workbench import workload_provision
from lib.akasha.workbench import wl_state
from lib.akasha.concepts import society as _soc

logger = logging.getLogger("Akasha.Kernel")




def _retire_stale_capability_generations(u, oset: str, fp8: str, prev_fp: str = "") -> int:
    """B5-b — keep at most ONE stale generation in an offered-capability Set.

    Members are `cap:<name>@<fp8>`. Group them by fingerprint, keep the CURRENT build's and the one
    immediately before it (so a read taken mid-deploy still resolves), and retire every older
    generation: remove it from the offered Set and join it to a validity membrane already in the
    past, so the nightly retention phase evicts it from the horizon. The atom itself is never
    deleted — a capability that was once offered stays readable, it simply stops being offered.

    Bounded: reads one Set's members (a handful per role), never the store. Returns how many
    members were retired."""
    try:
        members = list(u._members(oset) or [])
    except Exception:
        return 0
    if not members:
        return 0
    by_fp = {}
    for mk in members:
        fp = str((u._meta(mk) or {}).get("fingerprint") or "")
        if fp:
            by_fp.setdefault(fp, []).append(mk)
    if len(by_fp) <= 2:
        return 0                                  # current + at most one stale — nothing to do
    # Which generation is "previous" is NOT inferable from the Set: `get_collection_members` is
    # hash-ordered, not insertion-ordered, and a fingerprint carries no sequence of its own. It is
    # recorded instead: `cap:build` holds the fingerprint of the build that last provisioned, read
    # by the caller BEFORE it stamps the current one. An authoritative predecessor, not a guess.
    keep_prev = prev_fp or None
    retired = 0
    past = int(time.time()) - 1                   # a membrane already behind the wall clock
    for fp, keys in by_fp.items():
        if fp == fp8 or fp == keep_prev:
            continue
        for mk in keys:
            try:
                u._remove_from_set(oset, mk)
            except Exception:
                pass
            try:
                u._set_meta(mk, "retired_build", fp)
                u._add_to_set("set:valid:until:wall:%d" % past, mk)
            except Exception:
                pass
            retired += 1
    return retired


def provision_capabilities(kernel, gid: str, sname: str, bname: str, grants: dict,
                            public_bench: bool) -> None:
    """B5 §A7 — declare, per society + role, the capabilities a role is OFFERED:
    `set:cap:offered:<gid>:<sname>:<role>` holds one `cap:<name>@<fp8>` atom per grant, `fp8` = the
    running seed's content_fingerprint[:8] (the P3 identity rule). Idempotent (content-addressed by
    the fingerprinted alias); a NEW build adds new-fp members while the old ones stay and read
    `stale_build`. Also stamps `society_sid` on the bench atom so effective.at / cap.ls resolve the
    society from the bench. The `visible` Set (which atoms a role may read) is RESERVED — absent means
    no restriction on a public bench, exactly what effective.at expects."""
    try:
        from lib.akasha.concepts._universal import UniversalConcept as _UC, slug as _slug
        u = _UC(kernel.manager.get_session("admin"))
        u._space = ("group:%s" % gid) if not public_bench else ""
        fp8 = (kernel._build_fp() or "")[:8] or "nofp"
        # record the CURRENT build fingerprint so cap.ls can tell a live capability from a stale one
        # (the runtime fp, not just akasha_build.json — a pinned/test build resolves too).
        # B5-b — read the PREVIOUS build's fingerprint before overwriting it: that atom is the only
        # authoritative record of which capability generation came immediately before this one.
        _prev_fp = ""
        try:
            _prev_fp = str((u._meta("cap:build") or {}).get("fingerprint") or "")
        except Exception:
            _prev_fp = ""
        _cbk = u._mk("cap:build", "[cap:build] current build fingerprint",
                     {"concept": "cap_build", "fingerprint": fp8})
        if _cbk:
            u._set_meta(_cbk, "fingerprint", fp8)
        sidk = "%s:%s" % (_slug(gid), _slug(sname))
        # stamp the society id on the bench atom (universal, so a public bench resolves it too)
        _bk = u._key("wb:%s" % _slug(bname))
        if _bk:
            u._set_meta(_bk, "society_sid", "%s/%s" % (gid, sname))
        for cname, glist in (grants or {}).items():
            oset = "set:cap:offered:%s:%s" % (sidk, _slug(cname))
            # B5-b — the offered Set is per (society, role) and GROWS BY ONE GENERATION PER BUILD:
            # each build mints `cap:<name>@<fp8>` under a new fingerprint and the old members stay.
            # By 09-21 `cap.ls` carried EIGHT fingerprints per capability, seven of them dead, and
            # two from fingerprints that never booted on the host at all. The offered Set is what a
            # role's grant is read from, so an unbounded pile of dead generations is both a memory
            # residue and a read nobody can scan by eye.
            #
            # The rule: **at most ONE stale generation survives a provisioning pass.** On each pass
            # the PREVIOUS generation is left alone (an operator mid-deploy still resolves it) and
            # everything OLDER is retired by the existing B3 validity machinery — joined to a
            # `set:valid:until:<clock>:<pos>` membrane in the past, which the nightly retention
            # phase evicts from the horizon. Nothing is deleted: the atoms stay readable, they only
            # stop being offered.
            n = 0
            for g in (glist or []):
                if not g:
                    continue
                alias = "cap:%s@%s" % (g, fp8)
                ck = u._mk(alias, "[%s] capability %s (build %s)" % (alias, g, fp8),
                           {"concept": "capability", "cap_name": g, "fingerprint": fp8,
                            "society": "%s/%s" % (gid, sname), "role": cname})
                u._add_to_set(oset, ck)
                n += 1
            # Retire AFTER the current generation is in the Set — the keep rule is "current +
            # one previous", and the current one has to be present to be kept.
            _retired = _retire_stale_capability_generations(u, oset, fp8, _prev_fp)
            if n:
                logger.info("[bench] provision capabilities society=%s/%s role=%s offered=%d fp=%s "
                            "retired=%d", gid, sname, cname, n, fp8, _retired)
    except Exception as exc:
        # NOT debug. This block writes the Set a role's grant is READ from; a failure here means a
        # society silently offers nothing, or keeps offering a generation that should have gone.
        # It stayed non-fatal (a broken capability write must not stop a boot) but it now says so
        # at WARNING with the exception named — the seed-A §0 rule, and the rule that would have
        # surfaced the retirement bug in this very function instead of hiding it at debug level.
        logger.warning("[bench] provision capabilities FAILED society=%s/%s: %s: %s",
                       gid, sname, type(exc).__name__, exc)


def provision_workloads(kernel) -> list:
    """Seed A §2 — reconcile every DECLARED workload to its declaration. The one authority.

    Replaces `station_autoarm_registered` / `station_converge` / `station_provision`, which read
    the legacy studio pair and split the work across an "is it already armed?" branch. There is one
    path here and it is all ensures, because *a declaration is a DESIRED STATE and a boot
    RECONCILES to it* — the rule the Thinker's Shelf paid two days for when the arm-check skipped
    the plan that writes the workflow entries.

    Returns the per-workload report list (the eval's seam). Never raises: a workload that cannot be
    provisioned is reported by NAME with a reason id and the rest still run — a broken declaration
    must not cost the other three their airing."""
    reports = []
    decls = workload.declarations(kernel)
    # `set:wl:declared` — reconciled to the FILES, before anything is provisioned, so the gate's
    # step 4 and the guide read the same answer as the loader. Unconditional and both ways: a
    # declaration that was removed loses its key here, which is what makes "retire what nothing
    # declares" set algebra (`declared ∖ armed`) instead of a scan that has to know what a
    # workload is (order 2026-09-22 §2).
    _facts.declared(kernel, [workload.key(x) for x in decls if not workload.problems(x)])
    if not decls:
        return reports

    # TWO WORKLOADS MAY NOT NAME ONE SOCIETY, and this is where that is said out loud.
    #
    # A society carries ONE autorun record: one policy, one `retry_at`, one `last_run`. Two
    # declarations pointing at the same society therefore share a schedule they both write: each
    # provisioning pass overwrites the other's policy, and each tick's `write_autorun_state`
    # drops the other's next attempt — so both are due on every tick, for ever, while each
    # declaration on disk says four hours. It has happened once already (`news_show_x` shared the
    # news show's society and "the programme silently stopped being scheduled", as its own
    # `_society` note records), and nothing in the platform noticed either time.
    #
    # It is REPORTED, not refused: refusing would take down both programmes for a collision an
    # operator can fix in one file, and the pair still provisions — the last writer wins, exactly
    # as before. What changes is that the log names both keys and the society, so the symptom
    # ("it runs every minute") is one grep from its cause.
    _by_society = {}
    for _x in decls:
        if workload.problems(_x):
            continue
        _by_society.setdefault("%s/%s" % workload.society_of(_x), []).append(workload.key(_x))
    for _sid, _keys in sorted(_by_society.items()):
        if len(_keys) > 1:
            logger.error("[bench] provision CONFLICT society=%s workloads=[%s] — one society "
                         "carries ONE schedule, so these share a `retry_at` and each tick drops "
                         "the other's: both will be due on every tick. Give each its own society.",
                         _sid, ",".join(sorted(_keys)))

    def d(client, method, data):
        return kernel.dispatch({"jsonrpc": "2.0", "method": method,
                                "params": {"session_token": client, "data": data},
                                "id": "workload-provision"}, TRUST_INTERNAL)

    for decl in decls:
        wl_key = workload.key(decl) or decl.get("_file") or "?"
        bad = workload.problems(decl)
        if bad:
            # The field id, not prose: this line crosses a team boundary, and "reason=trigger"
            # names the line of the declaration to look at (order §1.1).
            for field in bad:
                logger.warning("[bench] provision failed workload=%s reason=%s file=%s",
                               wl_key, field, decl.get("_file") or "?")
            reports.append({"workload": wl_key, "status": "failed", "reason": bad[0]})
            continue
        _missing_tpl = [b for b, t in workload_provision.templates_of(decl) if not t]
        if _missing_tpl:
            # Armed with no workflow is the failure that looks like health: the society exists, the
            # guide shows a programme, and every run dies `has no workflow` while the driver reports
            # a breaker. So a workload with no template is not provisioned at all — it is REFUSED,
            # by name, and the operator sees why on the first boot rather than on the third day.
            logger.warning("[bench] provision failed workload=%s reason=template expected=%s",
                           wl_key, ",".join("config/workbench/%s/templates/%s.ak"
                                            % (workload.bench_slug(decl), b) for b in _missing_tpl))
            reports.append({"workload": wl_key, "status": "failed", "reason": "template"})
            continue
        try:
            rep = workload_provision.provision(
                d, decl, note=lambda m: logger.debug("[bench] provision %s", m),
                kernel_session=lambda: kernel.manager.get_session(_BROADCASTER))
        except Exception as exc:                   # noqa: BLE001 — one workload, not the boot
            logger.warning("[bench] provision failed workload=%s reason=exception detail=%s: %s",
                           wl_key, type(exc).__name__, exc)
            reports.append({"workload": wl_key, "status": "failed", "reason": "exception"})
            continue
        write_workload_sets(kernel, decl)
        # The capabilities its casts are OFFERED (B5 §A7), from the declaration's own `grants` — the
        # only provisioning path there is (the legacy bench_*.json / auto_exec.json pass is gone).
        if isinstance(decl.get("grants"), dict) and decl["grants"]:
            provision_capabilities(kernel, rep.get("gid") or workload.society_of(decl)[0],
                                   rep.get("space") or workload.society_of(decl)[1],
                                   workload.bench_slug(decl),
                                   {k: v for k, v in decl["grants"].items() if not str(k).startswith("_")},
                                   workload.bench_public(decl))
        # A provision that FAILED names itself and arms nothing. Today the only such failure is a
        # governance cast the declaration names and this run could not create; it is reported by
        # `workload_provision` at the moment it happens, in its own vocabulary.
        if rep.get("failed"):
            reports.append({"workload": wl_key, "status": "failed", "reason": rep["failed"]})
            continue
        # The workload is DECLARED and PROVISIONED, so it is armed — and that conjunction is the
        # whole of it. Arming is a FACT WRITE, not a decision: it checks no precondition, asks
        # about no admission, and waits for no governance cast (the ruling, 2026-09-22). This is
        # the fact the gate's step 4 reads before it lets a run through. `mode == "auto"`,
        # `boot_pending` and `breaker` each used to answer part of the question at the place that
        # asked it; the Set answers all of it, once, where it becomes true.
        _facts.armed(kernel, wl_key, True)
        t = workload.trigger(decl)
        logger.info("[bench] provisioned workload=%s society=%s/%s workflow=%s trigger=%s duty=%s "
                    "effect=%s entries=%d armed=%s problems=%d",
                    wl_key, rep.get("gid"), rep.get("space"), decl.get("workflow"),
                    _trigger_str(t), workload.duty(decl), workload.effect(decl),
                    rep.get("entries") or 0, rep.get("armed"), len(rep.get("problems") or []))
        rep["status"] = "provisioned"
        reports.append(rep)
    # The resources each provisioned workload requires — consumer lines (and, §6.4, its labos).
    try:
        reconcile_workload_resources(kernel, [d for d in decls if workload.key(d) in
                                              {r.get("workload") for r in reports
                                               if r.get("status") == "provisioned"}])
    except Exception as exc:                       # noqa: BLE001 — reported; provisioning stands
        logger.warning("[bench] resources not reconciled: %s: %s", type(exc).__name__, exc)
    return reports


def _trigger_str(t: dict) -> str:
    """The trigger as one readable token for the provisioned line — `boot+every:1800s`."""
    parts = []
    if t.get("boot"):
        parts.append("boot")
    if t.get("every_s"):
        parts.append("every:%gs" % t["every_s"])
    if t.get("daily"):
        parts.append("daily:%sZ" % t["daily"])
    return "+".join(parts) or "none"


def write_workload_sets(kernel, decl: dict) -> int:
    """§1.1 — every field of the declaration as a membership on the workload atom (`set:wl:*`).

    DERIVED from the file, reconciled on every boot, and written to the UNIVERSAL scope so a guest
    reading the guide sees the same shape the driver does. The names are mechanical
    (`workload.field_sets`), so a Set name can be written out by hand from the declaration and
    never has to be looked up."""
    try:
        from lib.akasha.concepts._universal import UniversalConcept as _UC
        u = _UC(kernel.manager.get_session("admin"))
        u._space = ""
        alias = workload.atom_alias(decl)
        k = u._mk(alias, "[%s] workload %s — %s on %s, %s"
                  % (alias, workload.key(decl), decl.get("workflow"), decl.get("bench"),
                     workload.duty(decl)),
                  {"concept": "workload", "workload": workload.key(decl),
                   "bench": workload.bench_atom(decl), "society": decl.get("society"),
                   "duty": workload.duty(decl), "effect": workload.effect(decl),
                   "trigger": _trigger_str(workload.trigger(decl)),
                   "llm_calls_per_run": workload.appetite(decl)["llm_calls_per_run"],
                   "per_day": workload.budget(decl)["per_day"]})
        if not k:
            return 0
        n = 0
        for name in workload.field_sets(decl):
            u._add_to_set(name, k)
            n += 1
        return n
    except Exception as exc:                       # noqa: BLE001 — reported, never silent
        logger.warning("[bench] workload sets FAILED workload=%s reason=%s: %s",
                       workload.key(decl), type(exc).__name__, exc)
        return 0


def schedule_workload_provision(kernel) -> None:
    """The declared writer-phase body (manifest `workload_provision`, `after: ontology.loaded`).

    Sets `kernel._workload_provision_done` when it ends, however it ends — with declarations or
    without, ok or raising (10-03 item 1). The auto-run driver waits on it before its first tick:
    this body writes the workflow entries a run executes, so a tick ahead of it runs the PREVIOUS
    build's entries (3 Oct: a publish step under its pre-rename method name → `Method not found`,
    breaker=1)."""
    try:
        reports = provision_workloads(kernel)
        if reports:
            ok = sum(1 for r in reports if r.get("status") == "provisioned")
            logger.info("[bench] workloads reconciled provisioned=%d failed=%d of=%d",
                        ok, len(reports) - ok, len(reports))
    finally:
        _ev = getattr(kernel, "_workload_provision_done", None)
        if _ev is not None:
            _ev.set()


def workload_source_ready(kernel, decl) -> bool:
    """Is EVERY pool this workload declares `requires` ready? A workload that requires nothing is.

    THE FACT IS ABOUT THE WORKLOAD, NOT THE POOL. `set:source:ready` is one of the gate's five fact
    Sets and all five hold TARGETS — the gate's step 4 asks `target ∈ declared ∩ armed ∩
    source_ready ∩ headroom`, and a Set keyed by the pool would make the gate resolve a target to
    its pool, which is knowledge about workloads the gate must not have (`api/gate.py` says so at
    the Set's definition).

    The first pass wrote POOL NAMES into it. The gate then asked for `studio_ai/news_show`, found
    the member `source:pool:plants:v1`, and answered `source_ready` — a refusal term — for a
    programme that was on air (D4). Two shapes in one Set is one shape too many.

    Which pools a workload needs is the WORKBENCH's knowledge (it reads the declarations); whether
    a pool is frozen is the SOURCE engine's (it owns the pool). Each answers only what it knows.

    **THREE KINDS OF REQUIREMENT, TOLD APART BY THEIR PREFIX** (D7). Every non-`model:` entry used
    to be handed to `pool_frozen`, which asks the source engine about a POOL — so a declaration
    that required `set:bio:plants:field_guide:ep1`, an ONTOLOGY SET, asked whether a pool of that
    name was frozen, was told no by a pool that does not exist, and waited for ever. The Plant Geek
    stood by on `source_ready` for a reason no amount of loading could clear, and the declared wait
    was inert: the programme was not waiting for the thing it had asked for.

        `model:<…>`  a bundled binary — shipped with the seed, nothing to wait for.
        `set:<…>`    an ontology Set — ready when the Set has members, which is what a pack
                     landing means. An empty or absent Set is the honest "not yet".
        anything else  a source pool — ready when the SOURCE engine says it is frozen and non-empty.

    A requirement whose kind the platform cannot name is treated as a pool, as before: the
    conservative answer for an unknown id is to wait, never to admit."""
    for r in (workload.policy(decl).get("requires") or []):
        if not requirement_ready(kernel, str(r)):
            return False
    return True


def requirement_ready(kernel, r: str) -> bool:
    """Is ONE declared requirement satisfied? The single predicate behind both the gate's fact and
    the driver's `missing` list.

    They were two readings of one question — `workload_source_ready` deciding, `requires_missing`
    naming — and each asked `pool_frozen` about every non-`model:` entry. Two readings can
    disagree, and once a `set:` requirement existed they did: the decider waited for a pool that
    was never a pool, and the namer listed a Set as missing whether or not it had landed. One
    predicate, one answer (the same rule D1 settles for the schedule).

    `model:` is answered by its caller, which owns the bundled-binary check."""
    r = str(r or "")
    if not r or r.startswith("model:"):
        return True
    if r.startswith("set:"):
        return _ontology_set_filled(kernel, r)
    from lib.akasha.source import bootstrap as _src
    return bool(_src.pool_frozen(kernel, r))


def _ontology_set_filled(kernel, name: str) -> bool:
    """Does this ontology Set exist with at least one member? The readiness probe for a `set:`
    requirement (D7).

    Membership is the whole test. A pack that has landed has put its atoms in its Set, and a Set
    with no members is indistinguishable from one whose pack has not loaded — which is exactly the
    state a workload requiring it should wait in. Read from the SHARED NUCLEUS, because an ontology
    pack is the cell's, not one client's, and read defensively: a cell with no shared nucleus (a
    bare personal seed) has no ontology to wait for, and answers not-ready rather than guessing.

    **`set:` IS THE REQUIREMENT'S KIND, NOT PART OF THE SET'S NAME** (P6). The first version looked
    the requirement up verbatim, prefix and all — `get_collection_members("set:bio:plants:…")` —
    while an `.ak` names its collection bare: `set.add name="bio:plants:field_guide:ep1"`, the
    convention across the ontology tree by 40,880 uses to 1,587. So the Plant Geek's wait went from
    inert to evaluated-and-never-ready: the same silence with one more moving part.

    The BARE name is asked first, because that is the convention. The literal spelling is asked
    second, because the 1,587 are real: the platform's own fact Sets (`set:wl:*`,
    `set:source:ready`) are stored with the prefix in their name, and a declaration may one day
    require one of them. Two point reads, the second only when the first is empty."""
    try:
        nuc = getattr(kernel.manager, "shared_nucleus", None)
        if nuc is None:
            return False
        bare = name[len("set:"):] if name.startswith("set:") else name
        for spelling in (bare, name) if bare != name else (name,):
            if nuc.core.get_collection_members(spelling):
                return True
        return False
    except Exception as exc:                      # noqa: BLE001 — a probe never fails a boot
        logger.warning("[source] ontology-set readiness unreadable set=%s reason=%s: %s",
                       name, type(exc).__name__, exc)
        return False


def reconcile_source_ready(kernel) -> int:
    """Every DECLARED WORKLOAD's source readiness, stated as a fact about that workload. Every boot.

    A fact written only when a pool freezes is absent on a cell that booted with its pools already
    frozen — every workload would wait for ever on a Set nobody had filled — so it is reconciled to
    the world at boot, the way `set:wl:declared` is. It is also re-stated the moment a pool freezes
    (the `source_ready_changed` hook the source engine fires), so a pool frozen DURING a run does
    not leave its workloads waiting until the next boot.

    The line names the keys, and both sides of the answer: a reconcile that reports only a count
    cannot tell a reader WHICH workload is waiting, which is the one thing they need."""
    ready, waiting = [], []
    try:
        for decl in (workload.declarations(kernel) or []):
            k = workload.key(decl)
            ok = workload_source_ready(kernel, decl)
            _facts.source_ready(kernel, k, ok)
            (ready if ok else waiting).append(k)
    except Exception as exc:                      # noqa: BLE001 — a boot never dies of bookkeeping
        logger.warning("[source] readiness reconcile skipped: %s: %s", type(exc).__name__, exc)
    logger.info("[source] readiness reconciled ready=%d waiting=%d ready_keys=[%s] waiting_keys=[%s]",
                len(ready), len(waiting), ",".join(sorted(ready)), ",".join(sorted(waiting)))
    return len(ready) + len(waiting)


def reconcile_headroom(kernel) -> int:
    """Every declared workload's headroom — ADMISSION's function, called here at boot.

    Moved to `admission.reconcile_headroom` (D12): `api/facts.py` names admission as the one writer
    of `set:pool:headroom`, and a second copy of the reconcile in provisioning was a second writer
    the moment the pool's day turn needed it too. This delegate keeps the boot call site."""
    from lib.akasha.workbench import admission as _adm
    return _adm.reconcile_headroom(kernel)


def reconcile_run_facts(kernel) -> int:
    """The two RUN facts a boot can state without a run — `source_ready` and `headroom`.

    The gate's step 4 for `run` is `target ∈ declared ∩ armed ∩ source_ready ∩ headroom`. The
    loader states `declared`, the driver states `armed`, and these two had NO WRITER AT ALL, so the
    step could never pass and `workload.status` reported a refusal term for programmes that were on
    air (D4). Each is stated by the party that knows it — and at boot, by the party that can ask
    them both — so the answer the gate gives is the answer the cell is actually living."""
    # §6.1 — the frozen-pool Set first (its writer is the source engine; a cell whose pools froze
    # before the Set existed has it empty until this), then the workloads that require it.
    try:
        from lib.akasha.source import bootstrap as _src
        _src.reconcile_pool_frozen(kernel)
        reconcile_workload_resources(kernel, [d for d in (workload.declarations(kernel) or [])
                                              if workload.requires_frozen_pools(d)])
    except Exception as exc:                      # noqa: BLE001 — a boot never dies of bookkeeping
        logger.warning("[source] frozen-pool reconcile at boot skipped: %s: %s",
                       type(exc).__name__, exc)
    return reconcile_source_ready(kernel) + reconcile_headroom(kernel)


# ── THE RESOURCES A WORKLOAD REQUIRES (directive 2026-10-02 §5.2, §6.1, §6.4) ─────────────────
#
# One reconcile, for every declaration, run by provisioning and again by the freeze hook. It makes
# what the declaration says about its resources TRUE on the cell:
#   · one `<client> consumer on <resource>` line per required `source:pool:` / `model:` entry —
#     and, when `requires` names `set:source:pool:frozen`, per MEMBER of that Set (§6.1);
#   · a line for a resource no longer required is removed (converge, both ways).
# `consumer` is read · run only, so nothing here can give a client `record` on a shared pool.

def workload_resources(kernel, decl) -> List[str]:
    """The resource targets this workload's client is bound to: its explicit `source:pool:` /
    `model:` requirements, plus every frozen pool when it requires `set:source:pool:frozen`."""
    out = list(workload.resource_requires(decl))
    if workload.requires_frozen_pools(decl):
        from lib.akasha.source import bootstrap as _src
        for p in _src.frozen_pools(kernel):
            if p not in out:
                out.append(p)
    return out


def reconcile_workload_resources(kernel, decls=None) -> Dict[str, Dict[str, int]]:
    """Converge every (or the given) declaration's resource lines. Returns per-workload counts and
    logs one `[bench] resources reconciled …` line per workload that has any."""
    from lib.akasha.api import gate as _gate
    report: Dict[str, Dict[str, int]] = {}
    cons = workload.CONSUMER_IDSET
    if cons not in _gate.idsets():
        logger.warning("[bench] resources not reconciled: the gate has no `%s` row", cons)
        return report
    for decl in (decls if decls is not None else (workload.declarations(kernel) or [])):
        if workload.problems(decl):
            continue
        prog, key = workload.client_of(decl), workload.key(decl)
        want = workload_resources(kernel, decl)
        have = [str(l.get("on") or "") for l in _gate.lines_for(prog) if l.get("idset") == cons]
        removed = 0
        for on in have:
            if on not in want:
                removed += _gate.unassign(prog, cons, on)
        added = 0
        for r in want:
            if r not in have:
                _gate.assign(prog, cons, r)
                added += 1
        pools = [r for r in want if r.startswith("source:pool:")]   # never a `model:` or a `set:`
        bound = _bind_bench_pools(kernel, decl, pools)
        labos = _ensure_labos(kernel, decl, pools)
        if want or removed or labos or bound:
            report[key] = {"consumer": len(want), "added": added, "removed": removed, "labos": labos,
                           "bound": bound}
            logger.info("[bench] resources reconciled workload=%s client=%s consumer=%d added=%d "
                        "removed=%d bound=%d labos=%d frozen_set=%s", key, prog, len(want), added,
                        removed, bound, labos, "yes" if workload.requires_frozen_pools(decl) else "no")
    return report


BIND_POOL_POINT = "bench.bind_pool"


def _bind_bench_pools(kernel, decl, pools: List[str]) -> int:
    """Ground the workload's bench in each pool it requires, through whatever op IMPLEMENTS
    `bench.bind_pool` (a bench kind's op — the platform names none), dispatched as admin (the one
    provisioning authority). Only source pools are passed: a `model:` is a bundled binary and a `set:`
    an ontology Set — neither is a pool. Re-run by the freeze hook, so a pool frozen later is bound
    then; the op is idempotent. No implementer → nothing bound, said once per workload. Returns the
    pools bound."""
    if not pools:
        return 0
    from lib.akasha import api as _api
    bind_m = _api.implementer(kernel, BIND_POOL_POINT)
    if not bind_m:
        logger.info("[bench] provision workload=%s pools_unbound reason=no_bind_pool_declared",
                    workload.key(decl))
        return 0
    done = 0
    for pool in pools:
        r = kernel.dispatch({"jsonrpc": "2.0", "method": bind_m,
                             "params": {"session_token": "admin",
                                        "data": {"name": workload.bench_slug(decl), "pool": pool}},
                             "id": "workload-bind-pool"}, TRUST_INTERNAL)
        if isinstance(r, dict) and "error" in r:
            logger.warning("[bench] pool not bound workload=%s pool=%s reason=%s", workload.key(decl),
                           pool, str((r.get("error") or {}).get("message"))[:160])
            continue
        done += 1
    return done


def _ensure_labos(kernel, decl, pools: List[str]) -> int:
    """§6.4 — the per-pool labos a declaration states (`labo: {name, about, scope}`), made true:
    for each required pool, ensure the labo and bind the pool to it. It acts under the installer's
    `provision` (dispatched as admin, the one provisioning authority) and is re-run by the freeze
    hook, so a pool frozen later gets its labo then. Both calls go through EXTENSION POINTS the
    application's labo ops declare (`workload.labo.new` / `workload.labo.bind`) — the platform
    names no application method. Idempotent: both ops are. Returns the pools handled.

    `when: "unbound"` (3 October, decision 2 — REGISTERED LABS WIN) makes it a SHADOW labo: before a
    pool gets one, the `workload.labo.of` point says which labs already hold it; a lab that is not
    this workload's own and not marked `shadow` is a registered lab, and the pool is skipped. With
    no implementer of that point, no shadow is made at all. The bind passes `origin: "shadow"`."""
    lab = workload.labo_of(decl)
    if not lab or not pools:
        return 0
    from lib.akasha import api as _api
    new_m = _api.implementer(kernel, workload.LABO_NEW_POINT)
    bind_m = _api.implementer(kernel, workload.LABO_BIND_POINT)
    if not (new_m and bind_m):
        logger.warning("[bench] labo not provisioned workload=%s reason=no_implementer point=%s",
                       workload.key(decl),
                       workload.LABO_NEW_POINT if not new_m else workload.LABO_BIND_POINT)
        return 0

    def d(method, data):
        r = kernel.dispatch({"jsonrpc": "2.0", "method": method,
                             "params": {"session_token": "admin", "data": data},
                             "id": "workload-labo"}, TRUST_INTERNAL)
        return r if isinstance(r, dict) else {}
    shadow = lab.get("when") == "unbound"
    of_m = _api.implementer(kernel, workload.LABO_OF_POINT) if shadow else ""
    if shadow and not of_m:
        # A shadow labo may not be made without asking whether a registered lab already holds the
        # pool — the safe answer when nobody can say is "make none" (registered labs win).
        logger.warning("[bench] labo not provisioned workload=%s reason=no_implementer point=%s",
                       workload.key(decl), workload.LABO_OF_POINT)
        return 0
    done = 0
    for pool in pools:
        name = workload.labo_name(decl, pool)
        if shadow:
            held = (d(of_m, {"pool": pool}).get("result") or {}).get("labos") or []
            mine = {name, "labo:%s" % name}
            registered = [str(h.get("labo")) for h in held if isinstance(h, dict)
                          and str(h.get("labo")) not in mine and h.get("origin") != "shadow"]
            if registered:
                logger.info("[bench] labo shadow skipped workload=%s pool=%s registered=%s",
                            workload.key(decl), pool, ",".join(registered))
                continue
        r1 = d(new_m, {"name": name, "about": lab["about"] or ("labo for %s" % pool),
                       "scope": lab["scope"]})
        r2 = d(bind_m, {"name": name, "pool": pool, "origin": "shadow"})
        if "error" in r1 or "error" in r2:
            logger.warning("[bench] labo not provisioned workload=%s pool=%s labo=%s reason=%s",
                           workload.key(decl), pool, name,
                           str((r1.get("error") or r2.get("error") or {}).get("message"))[:160])
            continue
        done += 1
    return done


def source_ready_changed(kernel, pool: str = "") -> int:
    """A pool's readiness changed (the source engine fires this at freeze): re-state the workloads.

    The source engine cannot do this itself — it would have to read the declarations, and `source`
    is LEFT of `workbench` on the layer map. It knows a pool froze; this package knows who was
    waiting for it. The hook is the one declared upward call between them."""
    logger.info("[source] readiness changed pool=%s — re-stating the workloads that require it",
                pool or "-")
    n = reconcile_source_ready(kernel)
    # §6.1 — a workload that requires the frozen-pool Set gains this pool's line now, not at the
    # next boot (the source engine stated the Set before firing this hook).
    try:
        reconcile_workload_resources(kernel, [d for d in (workload.declarations(kernel) or [])
                                              if workload.requires_frozen_pools(d)
                                              or pool in workload.resource_requires(d)])
    except Exception as exc:                      # noqa: BLE001 — a freeze never dies of bookkeeping
        logger.warning("[bench] resources not reconciled at freeze pool=%s: %s: %s",
                       pool, type(exc).__name__, exc)
    return n
