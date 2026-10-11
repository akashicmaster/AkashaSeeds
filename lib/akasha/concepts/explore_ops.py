"""
Exploration ops (explore, graph.tree, view, cosmos.*, dive.*), moved out of the kernel (backend layout order 2026-09-20). Bodies verbatim except `self.` → `kernel.`.

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

from lib.akasha.concepts import associate_ops
from lib.akasha.concepts import horizon_ops
from lib.akasha.concepts import registry as _registry_mod

logger = logging.getLogger("Akasha.Kernel")


def handle_explore(kernel, rid, data, session, ctx, scopes, history) -> dict:
    """
    explore — query/filter tool for discovering atoms in the ontology.

    Filters (at least one required):
      ns=    namespace prefix (aliases matching ns:*)
      set=   set membership (atoms in this named set)
      type=  meta.type filter
      pat=   alias wildcard pattern (% and _ wildcards)
      id=    positional alias/pattern (falls through to pat= if no other filter)

    Multiple filters are ANDed. Results are numbered for dive navigation.
    """
    ns        = (data.get("ns") or "").strip()
    set_filt  = (data.get("set") or "").strip()
    atom_type = (data.get("type") or "").strip()
    pat       = (data.get("pat") or data.get("id") or "").strip()
    limit     = int(data.get("limit", 50))
    nucleus   = getattr(session, 'nucleus', None)

    if not (ns or set_filt or atom_type or pat):
        return _err(rid, -32602,
            "explore requires at least one filter: ns=, set=, type=, or pat= (or a positional pattern)")

    # ── Delegate to the shared discovery core (also backs thesaurus.explore) ──
    from lib.akasha.discovery import discover_atoms
    group_engines = kernel._member_group_engines(session, scopes) if session else []
    results = discover_atoms(
        ctx, nucleus, group_engines, scopes,
        ns=ns, set_filt=set_filt, atom_type=atom_type, pat=pat, limit=limit)

    session.set_context("last_signposts",
        [{"key": r["key"], "alias": r["alias"]} for r in results])

    filters = {k: v for k, v in
               {"ns": ns, "set": set_filt, "type": atom_type, "pat": pat}.items() if v}
    return _ok(rid, {
        "atoms":   results,
        "count":   len(results),
        "filters": filters,
    })


def handle_graph_tree(kernel, rid, data, session, ctx, scopes) -> dict:
    """
    graph.tree — BFS link-traversal tree from an atom, set, or namespace.

      target= atom alias/key, set:<name>, or ns:<prefix>
      depth=  traversal depth (default 2, capped 1–5)
      follow= relation type filter (empty = all outgoing)
      format= rich | ascii (default rich)
      concept= yes → the CONCEPT tree (sys:is_a subset/superset only), delegated to
               the concept navigator (the op implementing `concept_tree`) — ignores every other link type + sets
    """
    # Concept-hierarchy mode: `tree <c> concept=yes` walks the sys:is_a up/down lattice only.
    # The navigator is whatever op IMPLEMENTS `concept_tree` (group 4) — not named here.
    from lib.akasha.api import manifest as _manifest
    _nav = _manifest.declared_implementer("concept_tree")
    if str(data.get("concept", "")).strip().lower() in ("yes", "true", "1", "y") \
            and _nav and _registry_mod.get_active():
        r = _registry_mod.get_active().dispatch_if_handled(
            _nav, session,
            {"root": data.get("target") or data.get("id") or "",
             "depth": data.get("depth", ""), "limit": data.get("limit", ""),
             "leaves": data.get("leaves", "")},
            rid)
        if r is not None:
            return r

    target = (data.get("target") or data.get("id") or "").strip()
    depth  = int(data.get("depth", 2))
    follow = (data.get("follow") or "").strip()
    fmt    = (data.get("format") or "rich").strip()

    if not target:
        return _err(rid, -32602, "graph.tree requires target= (atom alias/key, set:<name>, or ns:<prefix>)")

    try:
        tv = ctx.graph_tree(
            target         = target,
            depth          = depth,
            follow         = follow,
            fmt            = fmt,
            allowed_scopes = scopes or [],
        )
        return _ok(rid, tv)
    except Exception as e:
        logger.error("[graph.tree] %s", e, exc_info=True)
        return _err(rid, -32000, f"graph.tree error: {e}")


def handle_view(kernel, rid, data, session, scopes) -> dict:
    """view id= — the consciousness view of an atom on its own: signposts (1-hop),
    resonance (2-hop / semantic neighbours), cosmos_nd (spatial-emotional vector), and
    aura_color. Same payload dive/look produces, but standalone and without changing the
    session focus or signpost stack — a read-only 'show me the meaning of this'."""
    ctx = session.local_cortex
    target = (data.get("id") or data.get("key")
              or session.last_written_id or session.get_context("focus", "")).strip()
    if not target:
        return _err(rid, -32602, "view requires 'id' or a focus/last-written atom")
    resolved = _universal.resolve_target(kernel, target, session, ctx.stream(10)) or target
    if session.consciousness is None:
        return _err(rid, -32001, "consciousness engine unavailable")
    result = session.consciousness.generate_view(resolved, allowed_scopes=scopes)
    if isinstance(result, dict) and "error" in result:
        return _err(rid, -32002, _focus_error(kernel, result))
    return _ok(rid, result)


def _focus_error(kernel, result: dict) -> str:
    """The view's error, unless the focus was simply not found while the ontology is still loading:
    then that, and where to look (findings F1). A retriable `busy` keeps its own words."""
    from lib.akasha.ontology.loader import loading_note
    note = "" if result.get("retry") else loading_note(kernel)
    return ("Focus not found: " + note) if note else result["error"]


def route_node(kernel, ctx, key) -> dict:
    """A route waypoint for the cosmos chart: {id, alias, ns, label} (display-readable)."""
    try:
        aliases = ctx.get_aliases_by_key(key) or []
    except Exception:
        aliases = []
    alias = next((a for a in aliases if ":" in a), aliases[0] if aliases else key)
    ns = alias.split(":", 1)[0] if ":" in alias else ""
    label = (alias.split(":")[-1].replace("_", " ") if ":" in alias else alias)[:48]
    return {"id": key, "alias": alias, "ns": ns, "label": label}


def handle_cosmos_route(kernel, rid, data, session, scopes) -> dict:
    """[cosmos.route] BFS shortest route from a source atom to a destination atom over the
    WHOLE link graph (scope-filtered, both directions), plus up to k-1 alternate routes that
    detour around the primary path. Feeds the cosmos 'star route chart' view. Read-only."""
    ctx = session.local_cortex
    history = ctx.stream(10)
    src_in = data.get("src") or session.get_context("focus", "$origin")
    dst_in = (data.get("dst") or "").strip()
    if not dst_in:
        return _err(rid, -32602, "route requires 'dst' (destination atom / alias).")
    src = _universal.resolve_target(kernel, src_in, session, history) or src_in
    dst = _universal.resolve_target(kernel, dst_in, session, history) or dst_in
    if not (ctx.get_chunk(dst) or ctx.resolve_alias(dst) or ctx.get_chunk(dst_in)):
        return _err(rid, -32002, f"Destination not found: '{dst_in}'")
    from lib.akasha.graph.query import GraphQueryEngine
    _vis = (lambda k: True) if scopes is None else (lambda k: bool(ctx.check_access(k, scopes)))
    gq = GraphQueryEngine(cortex=ctx, visible_fn=_vis,
                          meta_fn=lambda k: ctx.get_meta(k) or {},
                          content_fn=lambda k: ctx.get_chunk(k) or "")
    max_depth = max(1, min(int(data.get("max_depth", 6) or 6), 8))
    k = max(1, min(int(data.get("k", 1) or 1), 3))
    rels = data.get("rels") or None
    src_node = route_node(kernel, ctx, src)
    dst_node = route_node(kernel, ctx, dst)
    _first = gq.path(src, dst, rels=rels, max_depth=max_depth, include_incoming=True)
    if not _first.get("found"):
        return _ok(rid, {"found": False, "src": src_node, "dst": dst_node, "routes": [],
                         "reason": f"no route within {max_depth} hops"})
    routes = [_first]
    if k > 1 and _first.get("length", 0) > 1:
        _seen = {tuple(_first["path"])}
        for _mid in _first["path"][1:-1]:
            if len(routes) >= k:
                break
            _alt = gq.path(src, dst, rels=rels, max_depth=max_depth,
                           include_incoming=True, avoid={_mid})
            if _alt.get("found") and tuple(_alt["path"]) not in _seen:
                _seen.add(tuple(_alt["path"]))
                routes.append(_alt)
    def _fmt(r):
        return {"path": [route_node(kernel, ctx, kk) for kk in r["path"]],
                "relations": r["relations"], "length": r["length"]}
    return _ok(rid, {"found": True, "src": src_node, "dst": dst_node,
                     "routes": [_fmt(r) for r in routes]})


def handle_cosmos_web(kernel, rid, data, session, scopes) -> dict:
    """[cosmos.web] A bounded semantic-network subgraph around a focal atom, for the pannable
    'semantic network' mesh view. Each node carries a REAL 2-D semantic position (projection
    of the atom's own embedding — near in meaning ⇒ near in space) plus its degree size and
    emotion/sense aura; the edges are the inter-node links among the collected set. BFS over
    the WHOLE link graph (scope-filtered, both directions), bounded by depth + node budget.
    Read-only — never renders more than 'limit' nodes, the client pans/scrolls for the rest."""
    ctx = session.local_cortex
    history = ctx.stream(10)
    focal_in = data.get("id") or data.get("focus") or session.get_context("focus", "$origin")
    focal = _universal.resolve_target(kernel, focal_in, session, history) or focal_in
    if not (ctx.get_chunk(focal) or ctx.resolve_alias(focal)):
        return _err(rid, -32002, f"Focal atom not found: '{focal_in}'")
    _vis = (lambda k: True) if scopes is None else (lambda k: bool(ctx.check_access(k, scopes)))
    depth     = max(1, min(int(data.get("depth", 2) or 2), 3))
    max_nodes = max(12, min(int(data.get("limit", 180) or 180), 400))
    fan       = max(6,  min(int(data.get("fan", 32) or 32), 64))

    # ── BFS collect (undirected: outgoing + incoming), node-budget bounded ──
    from collections import deque
    collected = [focal]
    seen = {focal}
    q = deque([(focal, 0)])

    def _neigh(k):
        out = ctx.get_adjacent_links(k, None, limit=fan, order_by_weight=True) or []
        inc = (ctx.get_incoming_links(k) or [])[:fan]
        return [d for d, _r in out] + [s for s, _r in inc]

    while q and len(collected) < max_nodes:
        cur, d = q.popleft()
        if d >= depth:
            continue
        for nb in _neigh(cur):
            if nb in seen or not _vis(nb):
                continue
            seen.add(nb); collected.append(nb)
            q.append((nb, d + 1))
            if len(collected) >= max_nodes:
                break

    idx = {k: i for i, k in enumerate(collected)}

    # ── nodes: semantic 2-D position + degree size + aura colour ──────────
    nodes = []
    for k in collected:
        rn = route_node(kernel, ctx, k)          # {id, alias, ns, label}
        try:
            x, y, _z = CosmosMapper.position(ctx, k)
        except Exception:
            x, y = 0.0, 0.0
        try:
            deg = len(ctx.get_adjacent_links(k, None, limit=64))
        except Exception:
            deg = 0
        try:
            aura = CosmosMapper.get_aura_color(ctx, k)
        except Exception:
            aura = None
        rn.update({"x": round(x, 4), "y": round(y, 4),
                   "val": round(3 + min(deg, 40) * 0.5, 2),
                   "color": aura, "deg": deg})
        nodes.append(rn)

    # ── edges among the collected set (dedup unordered, keep dir + rel) ────
    edges = []
    epairs = set()
    for k in collected:
        for dst, rel in (ctx.get_adjacent_links(k, None, limit=fan, order_by_weight=True) or []):
            j = idx.get(dst)
            if j is None:
                continue
            pr = (min(idx[k], j), max(idx[k], j))
            if pr in epairs or pr[0] == pr[1]:
                continue
            epairs.add(pr)
            edges.append({"s": idx[k], "t": j, "rel": rel})

    return _ok(rid, {"found": True, "focal": route_node(kernel, ctx, focal),
                     "nodes": nodes, "edges": edges,
                     "count": len(nodes), "edge_count": len(edges),
                     "truncated": len(collected) >= max_nodes})


def handle_dive_look(kernel, rid, data, session, scopes) -> dict:
    ctx = session.local_cortex

    # Signpost navigation: bare number resolves to stored signpost key
    signpost_idx = data.get("signpost")
    target = data.get("id", "")

    if signpost_idx is not None:
        stored = session.get_context("last_signposts") or []
        idx = int(signpost_idx)
        if 0 <= idx < len(stored):
            target = stored[idx]["key"]
        else:
            return _err(rid, -32602, f"No signpost {idx}. Run 'look' first.")

    if not target:
        target = session.get_context("focus", "$origin")

    history = ctx.stream(10)
    resolved = _universal.resolve_target(kernel, target, session, history) or target

    nucleus = getattr(session, 'nucleus', None)
    focus   = horizon_ops.get_display_focus(kernel, session)
    if focus and not horizon_ops.passes_display_focus(kernel, resolved, focus, ctx, nucleus):
        return _err(rid, -32002, f"Atom not in current focus: '{target}'")

    session.set_context("focus", resolved)
    result = session.consciousness.generate_view(resolved, allowed_scopes=scopes)

    if "error" in result:
        return _err(rid, -32002, _focus_error(kernel, result))

    # Apply display focus to signposts
    if focus:
        result["signposts"] = [
            sp for sp in result.get("signposts", [])
            if horizon_ops.passes_display_focus(kernel, sp["key"], focus, ctx, nucleus)
        ]

    # Persist signpost index for number navigation
    session.set_context("last_signposts",
        [{"key": sp["key"], "alias": sp.get("alias")}
         for sp in result.get("signposts", [])])

    # Enrich: associations + resonance via the same pipeline as kernel.associate
    _sess  = horizon_ops.get_scope_state(kernel, session)
    axis   = data.get("axis") or _sess.get("axis") or None
    scope  = int(data.get("scope") or _sess.get("scope") or 2)
    assoc  = ctx.associate(resolved, axis=axis, scope=scope, allowed_scopes=scopes)
    # F53 Stage 3 — apply the session horizon (guarded: no horizon ⇒ unchanged, bit-identical).
    _assocs, _hz_ann = horizon_ops.apply_horizon(kernel, session, assoc.get("associations", []), ctx)
    result["associations"] = _assocs
    if "lens" in _hz_ann:
        result["lens"] = _hz_ann["lens"]

    # Annotate resonance items with a readable via_alias
    resonance = assoc.get("resonance", [])
    for r in resonance:
        via_key = r.get("via", "")
        via_aliases = ctx.get_aliases_by_key(via_key) if via_key else []
        r["via_alias"] = via_aliases[0] if via_aliases else via_key[:12]
    result["resonance"] = resonance

    # Cosmos graph format (nodes + links for 3D visualization)
    content       = ctx.get_chunk(resolved) or ""
    focal_aliases = ctx.get_aliases_by_key(resolved)
    focal_info    = {
        "key":     resolved,
        "content": content,
        "preview": content[:50],
        "alias":   focal_aliases[0] if focal_aliases else None,
    }
    result["cosmos"] = associate_ops.format_associate_cosmos(
        focal_info, axis, assoc, {"status": "unavailable"}, ctx
    )

    # Attach active_time from session (consumed by UI; consciousness layer
    # does not yet filter by time, so it is passed as context metadata only)
    active_time = data.get("time") or session.get_context("active_time")
    if active_time:
        result["active_time"] = active_time

    return _ok(rid, result)


def handle_dive_out(kernel, rid, data, session, scopes) -> dict:
    target = data.get("id", "")
    if not target:
        target = session.get_context("focus", "$origin")

    history = session.local_cortex.stream(10)
    resolved = _universal.resolve_target(kernel, target, session, history) or target

    result = session.consciousness.zoom_out(resolved, allowed_scopes=scopes)
    return _ok(rid, result)
