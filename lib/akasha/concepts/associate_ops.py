"""
emotion.* + associate ops, moved out of the kernel (backend layout order 2026-09-20). Bodies verbatim except `self.` → `kernel.`.

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
from lib.akasha.consciousness import CosmosMapper
from lib.akasha.api.rpc import ok as _ok, err as _err
from lib.akasha.concepts import _universal
from lib.akasha.concepts import horizon_ops

from lib.akasha.concepts._universal import _readable

logger = logging.getLogger("Akasha.Kernel")

# ── lifted from the kernel module level (backend layout order 2026-09-20) ──
# Axis filter map shared between _handle_associate and _handle_associate_unwritten
_AXIS_PREFIXES: Dict[str, List[str]] = {
    "emotion": ["emo:"],
    "color":   ["word:color:", "calc:color"],
    "sense":   ["word:sense:", "calc:sense"],
    "time":    ["chrono:", "calc:time"],
    "context": ["calc:context", "calc:associated_with"],
    "story":   ["polti:", "story:"],
}


def handle_emotion_profile(kernel, rid, data, session, ctx, scopes) -> dict:
    """emotion.profile id= [scope=] [normalize=] — the Akasha-native emotion vector of an
    atom: the emo:* atoms it is linked to (via calc:associated_with / has_emotion / …),
    weighted by edge strength and depth, ranked and (by default) L1-normalised. This is
    the link-based track of the two-track emotion design; the external-NLP sentiment track
    is separate. Scope-filtered; an atom with no emotion links returns an empty vector."""
    target = data.get("id") or data.get("key") or session.last_written_id or ""
    if not target:
        return _err(rid, -32602, "emotion.profile requires 'id' or a last-written atom")
    focal_key = ctx.resolve_alias(target) or target
    content = ctx.get_scoped_chunk(focal_key, scopes) if scopes else ctx.get_chunk(focal_key)
    if content is None:
        return _err(rid, -32002, f"Atom '{focal_key}' not found or access denied")
    scope = max(1, min(int(data.get("scope", 2)), 4))
    normalize = str(data.get("normalize", "true")).lower() not in ("0", "false", "no")
    profile = ctx.emotion_profile(focal_key, scope=scope,
                                  allowed_scopes=scopes, normalize=normalize)
    return _ok(rid, profile)


def handle_emotion_find(kernel, rid, data, session, ctx, scopes) -> dict:
    """emotion.find emo= [limit=] — the reverse of emotion.profile: the atoms that FEEL a
    given emotion, i.e. those linking to the `emo:*` atom (incoming edges), ranked by edge
    strength. `emo=` accepts 'awe' or 'emo:awe'. Scope-filtered (fail-closed)."""
    emo = (data.get("emo") or data.get("emotion") or data.get("id") or "").strip()
    if not emo:
        return _err(rid, -32602, "emotion.find requires 'emo' (e.g. emo=awe)")
    alias = emo if emo.startswith("emo:") else f"emo:{emo}"
    emo_key = ctx.resolve_alias(alias) or (emo if emo != alias else None)
    if not emo_key:
        return _err(rid, -32002, f"emotion '{alias}' not found")
    # Every atom the alias names, not only the first one. A cell unfolds its own innate copy
    # of each `emo:*` axis (dna.py), and the local alias wins resolution — but the ontology's
    # links point at the nucleus atom of the same alias. Reading only the local key saw none.
    keys = [emo_key]
    nucleus = getattr(ctx, "_nucleus", None)
    if nucleus is not None:
        nk = nucleus.core.get_key_by_alias(alias)
        if nk and nk not in keys:
            keys.append(nk)
    limit = max(1, min(int(data.get("limit", 20)), 200))
    seen, results = set(), []
    incoming = [l for k in keys for l in (ctx.get_incoming_links(k) or [])]
    for link in incoming:
        src = link.get("src") if isinstance(link, dict) else (link[0] if link else None)
        if not src or src in seen:
            continue
        seen.add(src)
        if scopes and not ctx.check_access(src, scopes):
            continue
        content = ctx.get_chunk(src)
        if content is None:
            continue
        w = link.get("w", 1.0) if isinstance(link, dict) else 1.0
        rel = link.get("rel", "") if isinstance(link, dict) else (link[1] if len(link) > 1 else "")
        results.append({"key": src, "name": _readable(ctx, src),
                        "weight": float(w or 1.0), "rel": rel,
                        "preview": content[:80]})
    results.sort(key=lambda r: r["weight"], reverse=True)
    return _ok(rid, {"emotion": alias, "results": results[:limit],
                     "count": min(len(results), limit)})


def handle_associate(kernel, rid, data, session, ctx, scopes, history) -> dict:
    """
    assoc — gap detection and fill for a specific atom.

    Scans ONE-LEVEL outgoing links from the target atom.
    Identifies which semantic axes are absent (voids).
    Finds structural candidates from peer atoms in shared sets (no inference).
    Optionally fills each void with the top structural candidate.

    Parameters:
      id=   target atom (required, or falls back to last-written)
      axis= focus on one axis only (optional)
      fill= yes → write a link for the top candidate of each void
    """
    target = data.get("id", "") or session.last_written_id or ""
    if not target:
        return _err(rid, -32602, "assoc requires 'id' or a last-written atom")

    axis = (data.get("axis") or "").strip() or None
    # F53 Stage 3 — inherit the session's self-directed axis ONLY when the request omits it AND the
    # session has one set (guests/archives never do → unchanged). Explicit axis is untouched.
    if axis is None:
        axis = horizon_ops.get_scope_state(kernel, session).get("axis") or None
    fill = data.get("fill", "").strip().lower() in ("yes", "true", "1")

    focal_key = (
        _universal.resolve_target(kernel, target, session, history)
        or ctx.resolve_alias(target)
        or target
    )

    content = ctx.get_scoped_chunk(focal_key, scopes) if scopes else ctx.get_chunk(focal_key)
    if content is None:
        return _err(rid, -32002, f"Atom '{focal_key}' not found or access denied")

    # Gap detection — structural, one level, no inference
    voids = ctx.find_link_voids(focal_key, axis=axis, allowed_scopes=scopes)

    filled: List[Dict[str, Any]] = []
    if fill:
        author_id = getattr(session, 'client_id', 'system')
        for void in voids:
            cands = void.get("candidates", [])
            if not cands:
                continue
            best = cands[0]
            rel  = best["rel"]
            dst  = best["key"]
            ctx.put_link(focal_key, dst, rel, author=author_id)
            filled.append({
                "axis":  void["axis"],
                "rel":   rel,
                "dst":   dst,
                "alias": best.get("alias"),
            })

    focal_aliases = ctx.get_aliases_by_key(focal_key)
    return _ok(rid, {
        "focal":   {"key": focal_key, "alias": focal_aliases[0] if focal_aliases else None,
                    "preview": content[:60]},
        "axis":    axis or "all",
        "voids":   voids,
        "filled":  filled,
    })


def handle_associate_unwritten(kernel, rid, data, session, ctx, scopes) -> dict:
    """
    Heuristic UnwrittenVoid detection.
    Checks which semantic axes are absent from the focal atom's outgoing links.
    When TensorEngine is available, vector distance replaces heuristics.
    Executed as an async JCL step — result retrievable via job.log.
    """
    focal_key = data.get("focal_key", "")
    axis      = data.get("axis") or None

    if not focal_key:
        return _err(rid, -32602, "associate.unwritten requires 'focal_key'")

    # Collect axes that ARE present in the focal atom's outgoing links
    present_axes: set = set()
    for dst, rel in ctx.get_adjacent_links(focal_key):
        for ax_name, ax_prefixes in _AXIS_PREFIXES.items():
            if any(rel.startswith(p) for p in ax_prefixes):
                present_axes.add(ax_name)

    # Determine which axes to check
    check_axes = [axis] if (axis and axis in _AXIS_PREFIXES) else list(_AXIS_PREFIXES.keys())

    voids = []
    for ax in check_axes:
        if ax not in present_axes:
            ax_prefixes = _AXIS_PREFIXES.get(ax, [])
            example_rel = ax_prefixes[0] if ax_prefixes else ax
            voids.append({
                "axis":    ax,
                "missing": example_rel,
                "hint":    f"No '{ax}' links found on this atom.",
            })

    # Write result to cortex so job.log can surface it
    if voids:
        ctx.put_chunk(
            content=f"[UnwrittenVoid] focal={focal_key[:8]} missing={[v['axis'] for v in voids]}",
            meta={
                "type":      "sys:associate_unwritten",
                "focal_key": focal_key,
                "voids":     voids,
            },
            author="system.associate",
            scopes=["scope:sys:universal"],
        )

    return _ok(rid, {"focal_key": focal_key, "voids": voids})


def format_associate_cosmos(
    focal: Dict[str, Any],
    axis: Optional[str],
    result: Dict[str, Any],
    unwritten: Dict[str, Any],
    ctx=None,
) -> Dict[str, Any]:
    """Formats associate result as a Cosmos/3D-Force-Graph ready payload.

    Each node carries a REAL semantic position (x/y/z = projection of its self-owned
    embedding via CosmosMapper.position, scaled to force-graph units) so the layout means
    something — near in space ⇒ near in meaning — and a degree-based size (val). A
    front-end that seeds ForceGraph positions from x/y/z gets a semantic layout instead of
    pure physics; one that ignores them is unaffected (additive, backward-compatible)."""
    _POS_SCALE = 60.0   # force-graph world units (position() returns ~unit-scale)

    def _geom(key: str, base_val: float):
        x, y, z = CosmosMapper.position(ctx, key) if ctx else (0.0, 0.0, 0.0)
        deg = len(ctx.get_adjacent_links(key)) if ctx else 0
        return {"x": round(x * _POS_SCALE, 3), "y": round(y * _POS_SCALE, 3),
                "z": round(z * _POS_SCALE, 3), "val": round(base_val + min(deg, 40) * 0.6, 2)}

    _focal_node = {
        "id":    focal["key"],
        "name":  focal["preview"],
        "alias": focal.get("alias"),
        "group": "focus",
        "color": "#ffffff",
    }
    _focal_node.update(_geom(focal["key"], 20))
    _focal_node["val"] = 20          # focus stays visually dominant regardless of degree
    nodes: List[Dict[str, Any]] = [_focal_node]
    links: List[Dict[str, Any]] = []
    seen: set = {focal["key"]}

    def _alias(key: str):
        if not ctx:
            return None
        aliases = ctx.get_aliases_by_key(key)
        return aliases[0] if aliases else None

    _ATYPE_COLOR = {
        "emotion":   "#ff6699",
        "concept":   "#00ffcc",
        "word":      "#66ccff",
        "structure": "#cc99ff",
        "relation":  "#ffcc44",  # bare-word, pre-namespace ontology
        "chunk":     "#aaaaaa",
    }

    def _node_color(key: str, atype: str) -> str:
        # Emotion/sense aura takes priority over structural type color
        if ctx:
            aura = CosmosMapper.get_aura_color(ctx, key)
            if aura:
                return aura
        return _ATYPE_COLOR.get(atype, "#00ffcc")

    for a in result.get("associations", []):
        if a["key"] not in seen:
            color = _node_color(a["key"], a.get("type", "chunk"))
            node = {
                "id":    a["key"],
                "name":  a["preview"],
                "alias": _alias(a["key"]),
                "group": a.get("type", "association"),
                "color": color,
            }
            node.update(_geom(a["key"], 8))
            nodes.append(node)
            seen.add(a["key"])
        links.append({
            "source": focal["key"],
            "target": a["key"],
            "rel":    a.get("rel"),
            "type":   a.get("type", "association"),
        })

    for r in result.get("resonance", []):
        if r["key"] not in seen:
            color = _node_color(r["key"], "resonance")
            node = {
                "id":    r["key"],
                "name":  r["preview"],
                "alias": _alias(r["key"]),
                "group": "resonance",
                "color": color,
            }
            node.update(_geom(r["key"], 10))
            nodes.append(node)
            seen.add(r["key"])
        links.append({
            "source": focal["key"],
            "target": r["key"],
            "rel":    r.get("rel"),
            "type":   "resonance",
        })

    return {
        "focal":     {"key": focal["key"], "preview": focal["preview"], "alias": focal.get("alias")},
        "axis":      axis or "all",
        "nodes":     nodes,
        "links":     links,
        "unwritten": unwritten,
    }
