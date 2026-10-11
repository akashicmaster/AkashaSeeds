"""
dream.* ops (affinity-gap incubation, human-confirmed), moved out of the kernel (backend layout order 2026-09-20). Bodies verbatim except `self.` → `kernel.`.

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
from lib.akasha.concepts import _universal

# ── constants moved from the kernel class (backend layout order 2026-09-20) ──
# ── dream — the asynchronous incubation / bridge-proposer ─────────────────────────────
#
# Unlike assoc (1-hop, high-confidence gap-fill) and sim/node.sim (rank what is already
# near), dream finds atoms that are NEAR in meaning/emotion but FAR in the explicit graph
# — the connections the graph is missing — and stages them as tentative (tent:) links for
# a HUMAN to confirm. It runs as a LOW-priority background JCL job ("sleep on it"): the
# first call submits and returns "dreaming…"; a later call returns the staged candidates.
_DREAM_REL = "tent:calc:hidden_affinity"


logger = logging.getLogger("Akasha.Kernel")


def dream_pending(kernel, ctx, focus_key, scopes):
    """The tent: candidates already staged on a focus (a completed dream awaiting approval)."""
    out = []
    try:
        raw = ctx.core.get_adjacent_links(focus_key) or []
    except Exception:
        raw = []
    for l in raw:
        dst = l.get("dst") if isinstance(l, dict) else (l[0] if l else None)
        rel = l.get("rel") if isinstance(l, dict) else (l[1] if len(l) > 1 else "")
        if not dst or not str(rel).startswith("tent:"):
            continue
        if scopes and not ctx.check_access(dst, scopes):
            continue
        w = float(l.get("w", 0.0) or 0.0) if isinstance(l, dict) else 0.0
        al = ctx.get_aliases_by_key(dst)
        out.append({"dst": dst, "alias": al[0] if al else None,
                    "score": round(w, 4), "rel": rel,
                    "preview": (ctx.get_chunk(dst) or "")[:60]})
    out.sort(key=lambda c: c["score"], reverse=True)
    return out


def handle_dream(kernel, rid, data, session, ctx, scopes, history) -> dict:
    """dream id= [boldness=] [reach=] [again=yes] — incubate hidden connections for a
    focus atom, asynchronously. First call submits a background job and returns
    status="dreaming"; call again later to get status="ready" with the staged candidates
    (near-in-meaning, far-in-graph) for you to confirm with dream.confirm. Human approval
    is mandatory — dream never links on its own. Degrades to a synchronous run if JCL is
    unavailable."""
    target = (data.get("id") or session.get_context("dream:last") or "").strip()
    if not target:
        return _err(rid, -32602, "dream requires 'id' (the atom to dream around)")
    focus = _universal.resolve_target(kernel, target, session, history) or ctx.resolve_alias(target) or target
    if (ctx.get_scoped_chunk(focus, scopes) if scopes else ctx.get_chunk(focus)) is None:
        return _err(rid, -32002, f"Atom '{focus}' not found or access denied")
    session.set_context("dream:last", focus)
    again = str(data.get("again", "")).lower() in ("yes", "true", "1")

    # Poll an in-flight job for this focus.
    job_id = session.get_context(f"dream:{focus}")
    job = kernel.jcl_worker.get_job(job_id) if (job_id and kernel.jcl_worker) else None
    if job and job.status in ("PENDING", "RUNNING") and not again:
        elapsed = round(time.time() - (job.started_at or job.submitted_at), 1)
        return _ok(rid, {"status": "dreaming", "focus": focus, "job_id": job_id,
                         "elapsed_s": elapsed,
                         "hint": "still incubating — come back with `dream id=` later"})

    # A finished dream: staged tent: candidates awaiting approval.
    if not again:
        pending = dream_pending(kernel, ctx, focus, scopes)
        if pending:
            return _ok(rid, {"status": "ready", "focus": focus,
                             "candidates": pending, "count": len(pending),
                             "hint": "approve with `dream.confirm dst=` or drop with `dream.forget`"})
        if job and job.status == "FAILED":
            session.set_context(f"dream:{focus}", None)
            return _ok(rid, {"status": "failed", "focus": focus, "error": job.error})

    # Nothing pending (or again=yes) → start a fresh dream.
    if again:
        for c in dream_pending(kernel, ctx, focus, scopes):
            try:
                ctx.remove_link(focus, c["dst"], c["rel"])
            except Exception:
                pass
    params = {"focus": focus,
              "boldness": float(data.get("boldness", 0.2)),
              "reach":    float(data.get("reach", 0.5)),
              "threshold": float(data.get("threshold", 0.12)),
              "limit":    int(data.get("limit", 5)),
              "scan":     int(data.get("scan", 2000))}
    # Prefer the background JCL job (the "while sleeping" tier); degrade to synchronous.
    if kernel.harmonia and kernel.jcl_worker and JCLJob and JCLStep:
        job = JCLJob(owner=session.client_id, label=f"dream:{target[:32]}",
                     steps=[JCLStep(method="dream.run", params=params)])
        kernel.harmonia.submit_job(job, job_class=CLASS_LINK)
        session.set_context(f"dream:{focus}", job.job_id)
        return _ok(rid, {"status": "dreaming", "focus": focus, "job_id": job.job_id,
                         "hint": "dreaming… come back with `dream id=` to see the candidates"})
    # Synchronous fallback (no JCL): compute + stage now.
    n = dream_stage(kernel, ctx, session, scopes, params)
    return _ok(rid, {"status": "ready", "focus": focus,
                     "candidates": dream_pending(kernel, ctx, focus, scopes),
                     "count": n, "note": "computed synchronously (JCL unavailable)"})


def handle_dream_run(kernel, rid, data, session, ctx, scopes) -> dict:
    """dream.run — the background computation (JCL-dispatched, internal). Computes the
    affinity-gap candidates and stages them as tent: links. Not for direct use."""
    params = {"focus": data.get("focus", ""),
              "boldness": float(data.get("boldness", 0.2)),
              "reach":    float(data.get("reach", 0.5)),
              "threshold": float(data.get("threshold", 0.12)),
              "limit":    int(data.get("limit", 5)),
              "scan":     int(data.get("scan", 2000))}
    n = dream_stage(kernel, ctx, session, scopes, params)
    return _ok(rid, {"status": "dreamed", "focus": params["focus"], "staged": n})


def dream_stage(kernel, ctx, session, scopes, params) -> int:
    """Compute affinity-gap candidates for a focus and write them as tent: links."""
    focus = params["focus"]
    cands = dream_affinities(kernel, ctx, session, focus, scopes, params)
    author = getattr(session, "client_id", "system")
    n = 0
    for c in cands:
        try:
            ctx.put_link(focus, c["dst"], _DREAM_REL, w=c["score"], author=author)
            n += 1
        except Exception:
            pass
    return n


def dream_affinities(kernel, ctx, session, focus, scopes, params) -> list:
    """The affinity gap: atoms NEAR in meaning/emotion/structure but FAR in the explicit
    graph. Multi-signal, scope-filtered. Conservative by default (rewards signal
    agreement and graph distance); `boldness` shifts toward a single strong signal, `reach`
    strengthens the graph-distance reward."""
    import json as _json
    boldness = max(0.0, min(params.get("boldness", 0.2), 1.0))
    reach = max(0.0, min(params.get("reach", 0.5), 2.0))
    threshold = max(0.0, params.get("threshold", 0.12))
    limit = max(1, min(int(params.get("limit", 5)), 50))
    scan = max(1, min(int(params.get("scan", 2000)), 20000))

    tensor = getattr(ctx, "tensor", None)
    nucleus = getattr(session, "nucleus", None)
    try:
        from lib.akasha.semantic_learn import get_node_model, cosine as _lcos
        node_model = get_node_model(nucleus) if nucleus is not None else None
    except Exception:
        node_model, _lcos = None, None

    def _meta_vec(key, row=None):
        try:
            raw = row if row is not None else ctx.core.get_chunk_raw(key)
            m = _json.loads(raw["meta"]) if raw and raw.get("meta") else {}
            v = m.get("semantic_vector") if isinstance(m, dict) else None
            return v if isinstance(v, list) and v else None
        except Exception:
            return None

    def _neighbors(key):
        out = set()
        try:
            for l in (ctx.get_adjacent_links(key) or []):
                d = l[0] if not isinstance(l, dict) else l.get("dst")
                if d:
                    out.add(d)
        except Exception:
            pass
        return out

    def _tags(nbrs):
        return {n for n in nbrs}  # neighbour set doubles as the emo:/calc: tag set for overlap

    focus_vec = _meta_vec(focus)
    focus_nbrs = _neighbors(focus)
    focus_nvec = node_model.node_vector(focus) if node_model else None
    linked = focus_nbrs | {focus}

    scored = []
    for row in (ctx.stream(limit=scan) or []):
        dst = row.get("key")
        if not dst or dst in linked:
            continue
        if scopes and not ctx.check_access(dst, scopes):
            continue
        # signals in [0,1]
        content = 0.0
        if tensor is not None and focus_vec:
            cv = _meta_vec(dst, row)
            if cv:
                content = max(0.0, tensor.cosine(focus_vec, cv))
        struct = 0.0
        if node_model is not None and focus_nvec:
            nv = node_model.node_vector(dst)
            if nv:
                struct = max(0.0, _lcos(focus_nvec, nv))
        dst_nbrs = _neighbors(dst)
        shared = len(focus_nbrs & dst_nbrs)
        tag = (shared / len(focus_nbrs | dst_nbrs)) if (focus_nbrs or dst_nbrs) else 0.0
        present = [s for s in (content, struct, tag) if s > 0.05]
        if not present:
            continue
        gap = 1.0 / (1.0 + shared)                       # far in the graph → near 1.0
        agreement = len(present) / 3.0
        strength_cons = (sum(present) / len(present)) * (0.5 + 0.5 * agreement)
        strength_bold = max(present)
        nearness = (1.0 - boldness) * strength_cons + boldness * strength_bold
        score = nearness * (gap ** reach)
        if score >= threshold:
            scored.append({"dst": dst, "score": round(score, 4),
                           "signals": {"content": round(content, 3),
                                       "struct": round(struct, 3),
                                       "tag": round(tag, 3)},
                           "shared_neighbours": shared})
    scored.sort(key=lambda c: c["score"], reverse=True)
    return scored[:limit]


def handle_dream_confirm(kernel, rid, data, session, ctx, scopes, history) -> dict:
    """dream.confirm dst= [src=] — promote a staged (tent:) dream link to a real link.
    Human approval of a proposed connection: the tent: prefix is stripped so the affinity
    becomes a first-class edge. `src` defaults to the last-dreamed focus."""
    src_ref = (data.get("src") or data.get("id") or session.get_context("dream:last") or "").strip()
    dst_ref = (data.get("dst") or "").strip()
    if not src_ref or not dst_ref:
        return _err(rid, -32602, "dream.confirm requires 'dst' (and 'src' or a last-dreamed focus)")
    src = _universal.resolve_target(kernel, src_ref, session, history) or ctx.resolve_alias(src_ref) or src_ref
    dst = ctx.resolve_alias(dst_ref) or dst_ref
    # Find the staged tent: link src→dst.
    rel = next((c["rel"] for c in dream_pending(kernel, ctx, src, scopes) if c["dst"] == dst), None)
    if not rel:
        return _err(rid, -32002, "no staged dream link from that focus to that atom")
    real_rel = rel[len("tent:"):] if rel.startswith("tent:") else rel
    author = getattr(session, "client_id", "system")
    try:
        ctx.remove_link(src, dst, rel)
        ctx.put_link(src, dst, real_rel, author=author)
    except Exception as exc:
        return _err(rid, -32000, f"confirm failed: {exc}")
    return _ok(rid, {"status": "confirmed", "src": src, "dst": dst, "rel": real_rel})


def handle_dream_forget(kernel, rid, data, session, ctx, scopes, history) -> dict:
    """dream.forget [dst=] [src=] [all=yes] — drop staged (tent:) dream links that did not
    resonate. Without dst=, `all=yes` clears every staged candidate on the focus."""
    src_ref = (data.get("src") or data.get("id") or session.get_context("dream:last") or "").strip()
    if not src_ref:
        return _err(rid, -32602, "dream.forget requires 'src' or a last-dreamed focus")
    src = _universal.resolve_target(kernel, src_ref, session, history) or ctx.resolve_alias(src_ref) or src_ref
    dst_ref = (data.get("dst") or "").strip()
    drop_all = str(data.get("all", "")).lower() in ("yes", "true", "1") or not dst_ref
    pending = dream_pending(kernel, ctx, src, scopes)
    dropped = 0
    for c in pending:
        if drop_all or (dst_ref and (c["dst"] == (ctx.resolve_alias(dst_ref) or dst_ref)
                                     or c["alias"] == dst_ref)):
            try:
                ctx.remove_link(src, c["dst"], c["rel"])
                dropped += 1
            except Exception:
                pass
    session.set_context(f"dream:{src}", None)
    return _ok(rid, {"status": "forgotten", "src": src, "dropped": dropped})
