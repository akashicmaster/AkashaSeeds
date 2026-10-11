"""
nebula.* ops (the cartographer's survey / confirm / forget), moved out of the kernel (backend layout order 2026-09-20). Bodies verbatim except `self.` → `kernel.`.

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
    from lib.akasha.jcl import JCLWorker, JCLJob, JCLStep
    from lib.akasha.jcl.job import CLASS_BATCH_ATOM, CLASS_LINK, CLASS_MAINTENANCE
except ImportError:
    JCLWorker = None  # type: ignore
    JCLJob    = None  # type: ignore
    JCLStep   = None  # type: ignore
    CLASS_BATCH_ATOM = "batch_atom"  # type: ignore
    CLASS_LINK       = "link"        # type: ignore
    CLASS_MAINTENANCE = "maintenance"  # type: ignore
from lib.akasha.api.rpc import ok as _ok, err as _err
from lib.akasha import lexicon

logger = logging.getLogger("Akasha.Kernel")


def nebula_cartographer(kernel, ctx):
    from lib.akasha.concepts.nebula import NebulaCartographer
    node_vec = None
    try:
        from lib.akasha.semantic_learn import get_node_model
        nucleus = getattr(kernel.manager, "shared_nucleus", None)
        nm = get_node_model(nucleus) if nucleus else None
        if nm is not None:
            node_vec = nm.node_vector
    except Exception:
        node_vec = None
    return NebulaCartographer(ctx, node_vec=node_vec)


def nebula_vault_key(kernel, session) -> str:
    return getattr(session, "client_id", "system")


def nebula_store(kernel, session, payload) -> None:
    try:
        kernel._nucleus().vault_store("nebula", nebula_vault_key(kernel, session), payload)
    except Exception:
        pass


def nebula_load(kernel, session):
    try:
        return kernel._nucleus().vault_retrieve("nebula", nebula_vault_key(kernel, session)) or {}
    except Exception:
        return {}


def nebula_survey(kernel, ctx, session, scopes, params) -> list:
    cands = nebula_cartographer(kernel, ctx).survey(scopes=scopes, params=params)
    nebula_store(kernel, session, {"candidates": cands, "params": params})
    return cands


def handle_nebula(kernel, rid, data, session, ctx, scopes, history) -> dict:
    """nebula [again=yes] [ns=] [limit=] [min_size=] [threshold=] [scan=] — survey the
    accumulated atoms for regions that are becoming a concept model (dense clumps sharing
    a relation schema), asynchronously. First call submits a background survey and returns
    status="surveying"; call again to get status="ready" with ranked candidate regions,
    each with an inferred salient-rel profile. Confirm one with `nebula.confirm id=`. The
    machine only proposes — a human names + plants the concept. Degrades to a synchronous
    run when JCL is unavailable."""
    again = str(data.get("again", "")).lower() in ("yes", "true", "1")
    params = {
        "scan":       int(data.get("scan", 4000)),
        "cluster_cap": int(data.get("cluster_cap", 600)),
        "min_size":   int(data.get("min_size", 4)),
        "limit":      int(data.get("limit", 8)),
        "threshold":  float(data.get("threshold", 0.34)),
        "salience":   float(data.get("salience", 0.0)),
    }

    # Poll an in-flight survey.
    job_id = session.get_context("nebula:job")
    job = kernel.jcl_worker.get_job(job_id) if (job_id and kernel.jcl_worker) else None
    if job and job.status in ("PENDING", "RUNNING") and not again:
        elapsed = round(time.time() - (job.started_at or job.submitted_at), 1)
        return _ok(rid, {"kind": "nebula", "status": "surveying", "job_id": job_id, "elapsed_s": elapsed,
                         "hint": "still mapping the universe — come back with `nebula` later"})

    # A finished survey: read candidates back from the vault.
    if not again:
        stored = nebula_load(kernel, session)
        cands = stored.get("candidates") if isinstance(stored, dict) else None
        if cands:
            return _ok(rid, {"kind": "nebula", "status": "ready", "candidates": cands, "count": len(cands),
                             "hint": "plant one with `nebula.confirm id=<neb:…> name=<concept>`, "
                                     "or drop it with `nebula.forget id=`"})
        if job and job.status == "FAILED":
            session.set_context("nebula:job", None)
            return _ok(rid, {"kind": "nebula", "status": "failed", "error": job.error})

    # Submit a fresh survey (background), or run synchronously if JCL is unavailable.
    if kernel.harmonia and kernel.jcl_worker and JCLJob and JCLStep:
        job = JCLJob(owner=session.client_id, label="nebula:survey",
                     steps=[JCLStep(method="nebula.run", params=params)])
        kernel.harmonia.submit_job(job, job_class=CLASS_LINK)
        session.set_context("nebula:job", job.job_id)
        return _ok(rid, {"kind": "nebula", "status": "surveying", "job_id": job.job_id,
                         "hint": "surveying… come back with `nebula` to see candidate regions"})
    cands = nebula_survey(kernel, ctx, session, scopes, params)
    return _ok(rid, {"kind": "nebula", "status": "ready", "candidates": cands, "count": len(cands),
                     "note": "computed synchronously (JCL unavailable)"})


def handle_nebula_run(kernel, rid, data, session, ctx, scopes) -> dict:
    """nebula.run — the background survey (JCL-dispatched, internal). Not for direct use."""
    params = {k: data.get(k) for k in
              ("scan", "cluster_cap", "min_size", "limit", "threshold", "salience")}
    cands = nebula_survey(kernel, ctx, session, scopes, params)
    return _ok(rid, {"status": "surveyed", "candidates": len(cands)})


def handle_nebula_forget(kernel, rid, data, session, ctx, scopes, history) -> dict:
    """nebula.forget [id=] [all=yes] — drop a proposed region (or all) from the survey."""
    cid = (data.get("id") or "").strip()
    stored = nebula_load(kernel, session)
    cands = stored.get("candidates", []) if isinstance(stored, dict) else []
    drop_all = str(data.get("all", "")).lower() in ("yes", "true", "1") or not cid
    if drop_all:
        nebula_store(kernel, session, {"candidates": [], "params": stored.get("params", {})})
        session.set_context("nebula:job", None)
        return _ok(rid, {"status": "forgotten", "dropped": len(cands)})
    kept = [c for c in cands if c.get("id") != cid]
    nebula_store(kernel, session, {"candidates": kept, "params": stored.get("params", {})})
    return _ok(rid, {"status": "forgotten", "dropped": len(cands) - len(kept)})


def handle_nebula_confirm(kernel, rid, data, session, ctx, scopes, history) -> dict:
    """nebula.confirm id=<neb:…> [name=<concept>] — the human's approval of a proposed
    region. Names the emerging concept, materialises its set (members + sys:is_a spine),
    plants the inferred salient-rel profile (reldef + rel:salient) so `resolve_salient_rels`
    picks it up, and returns a concept-model SKELETON (Python class + .ak lexicon block) to
    review and place. The machine never writes the skeleton file itself."""
    cid = (data.get("id") or "").strip()
    if not cid:
        return _err(rid, -32602, "nebula.confirm requires 'id' (a neb:… candidate id)")
    stored = nebula_load(kernel, session)
    cands = stored.get("candidates", []) if isinstance(stored, dict) else []
    cand = next((c for c in cands if c.get("id") == cid), None)
    if not cand:
        return _err(rid, -32002, "no such nebula candidate — run `nebula` and use its id")
    raw_name = (data.get("name") or cand.get("name") or "concept").strip().lower()
    name = re.sub(r"[^a-z0-9_]+", "_", raw_name).strip("_") or "concept"
    author = getattr(session, "client_id", "system")

    planted = {"set": name, "members": 0, "salient_rels": []}
    set_proto = None
    try:
        for mk in cand.get("members", []):
            ctx.add_to_set(name, mk)
            planted["members"] += 1
        set_proto = ctx.resolve_alias(name)
    except Exception as exc:
        log.debug("[nebula] set materialise partial: %s", exc)
    # sys:is_a spine + rel:salient profile (best-effort; the skeleton is returned regardless).
    if set_proto:
        for mk in cand.get("members", []):
            try:
                ctx.put_link(mk, set_proto, "sys:is_a", author=author)
            except Exception:
                pass
        for rel in cand.get("salient_rels", []):
            try:
                reldef_key = nebula_ensure_reldef(kernel, ctx, rel, author)
                if reldef_key:
                    ctx.put_link(set_proto, reldef_key, "rel:salient", author=author)
                    planted["salient_rels"].append(rel)
            except Exception:
                pass

    # Remove the confirmed candidate from the survey.
    nebula_store(kernel, session, {"candidates": [c for c in cands if c.get("id") != cid],
                                 "params": stored.get("params", {})})
    skeleton = nebula_scaffold(kernel, name, cand)
    return _ok(rid, {"status": "planted", "name": name, "planted": planted,
                     "kind": cand.get("kind"), "skeleton": skeleton,
                     "hint": "review the skeleton, then drop the .py into lib/akasha/concepts/ "
                             "and the .ak block into ontology/lexicon/ (onto.csl.transpile if CSL)"})


def nebula_ensure_reldef(kernel, ctx, rel, author):
    """Ensure a reldef:<rel> atom exists (aliased, in the `rels` set); return its key."""
    alias = f"reldef:{rel}"
    key = ctx.resolve_alias(alias)
    if not key:
        desc = f"{rel} — '{rel}' relation asserted between two atoms."
        key = ctx.put_chunk(content=desc, meta={"type": "lexicon:reldef", "rel": rel},
                            author=author)
        ctx.set_alias(key, alias)
    try:
        ctx.add_to_set("rels", key)
    except Exception:
        pass
    return key


def nebula_scaffold(kernel, name: str, cand: dict) -> dict:
    """Generate the concept-model skeleton (Python class + .ak lexicon block) as TEXT —
    the inductive→deductive bridge. Reviewed and placed by the human; never auto-written."""
    cls = "".join(p.capitalize() for p in name.split("_")) + "Concept"
    rels = cand.get("salient_rels", [])
    aliases = cand.get("member_aliases", [])[:8]
    py = (
        f'# lib/akasha/concepts/{name}.py — nebula-proposed skeleton (#52). REVIEW before use.\n'
        f'# Discovered region: {cand.get("size")} members, dominant ns "{cand.get("dominant_ns")}",\n'
        f'# kind={cand.get("kind")}, score={cand.get("score")}. Examples: {", ".join(aliases)}\n'
        f'from lib.akasha.concepts.base import BaseConcept\n\n'
        f'class {cls}(BaseConcept):\n'
        f'    CONCEPT_PREFIX = "{name}"\n'
        f'    CONCEPT_LABEL  = "{name} — nebula-discovered concept (rename me)"\n'
        f'    # Inferred salient relations (shared across members): {", ".join(rels) or "(none)"}\n'
        f'    CONCEPT_METHODS = {{\n'
        f'        "new": {{"op": "op_new", "action": "record"}},\n'
        f'        "ls":  {{"op": "op_list", "action": "read"}},\n'
        f'        "get": {{"op": "op_get", "action": "read"}},\n'
        f'    }}\n\n'
        f'    def op_new(kernel, title):\n'
        f'        """Create a {name}."""\n'
        f'        ...\n\n'
        f'    def op_list(kernel):\n'
        f'        """List {name} instances."""\n'
        f'        ...\n\n'
        f'    def op_get(kernel, id):\n'
        f'        """Read one {name}."""\n'
        f'        ...\n'
    )
    ak_lines = [f'# ontology/lexicon — nebula-proposed salient-rels for "{name}"']
    for i, rel in enumerate(rels):
        ak_lines.append(f'def "reldef:{rel}" "{rel} — \'{rel}\' relation asserted between two atoms."')
        ak_lines.append(f'set.add name="rels" id="reldef:{rel}"')
    for rel in rels:                       # author most-important-first (link order = priority)
        ak_lines.append(f'ln {name} reldef:{rel} rel:salient')
    return {"python": py, "ak": "\n".join(ak_lines),
            "salient_rels": rels, "class_name": cls}
