"""
cross.* ops (set-algebra queries over concepts), moved out of the kernel (backend layout order 2026-09-20). Bodies verbatim except `self.` → `kernel.`.

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

from lib.akasha.concepts import registry as _registry_mod

logger = logging.getLogger("Akasha.Kernel")


def resolve_concept_to_set_name(kernel, concept: str, session) -> Optional[str]:
    """Maps a concept name, slot name, or set: path to its active collection set name.

    Resolution order:
      1. Raw set: prefix — used as-is.
      2. Space slot — check the session Space's mounted instances by slot name
         or model prefix (requires instance.mount to have been called).
      3. ConceptRegistry — use CONTEXT_KEY_ACTIVE for any registered model prefix
         to find the active concept root set.
      4. The log model's active root (`set:log:<root>`, a platform model).
    """
    # 1. Direct set name
    if concept.startswith("set:"):
        return concept

    # 2. Space: check mounted instances by slot name or model prefix
    try:
        from lib.akasha.session.space import SpaceConcept as _SpaceConcept
        _space = _SpaceConcept(session)
        if _space.concept_id:
            for slot_info in _space._slot_atoms():
                meta = slot_info["meta"]
                if meta.get("slot") == concept or meta.get("model") == concept:
                    cid = meta.get("concept_id")
                    if cid:
                        return f"set:concept:{cid}"
    except Exception:
        pass

    # 3. Registry: CONTEXT_KEY_ACTIVE → session context → set name
    if _registry_mod.get_active():
        cls = _registry_mod.get_active().get_class(concept)
        if cls:
            ctx_key = getattr(cls, "CONTEXT_KEY_ACTIVE", None)
            if ctx_key:
                root_id = session.get_context(ctx_key)
                if root_id:
                    return f"set:concept:{root_id}"

    # 4. The log model's own active root (a platform model kept before the registry convention)
    if concept == "log":
        root = session.get_context("active_log_root")
        return f"set:log:{root}" if root else None

    return None


def handle_cross_query(kernel, rid, data, session, ctx, scopes) -> dict:
    concepts_raw = data.get("concepts", [])
    if isinstance(concepts_raw, str):
        concepts = concepts_raw.split()
    else:
        concepts = list(concepts_raw)

    # F53 Stage 3 — when `concepts` is omitted, default to the session HORIZON (its entries ARE the
    # concepts the client is attending to). An explicit `concepts` overrides (today's callers see
    # identical behavior). With no concepts AND an empty horizon, error exactly as before.
    used_horizon = False
    if not concepts:
        concepts = [e.get("set") for e in (session.get_context("horizon") or []) if e.get("set")]
        used_horizon = bool(concepts)
    if not concepts:
        return _err(rid, -32602, "sys.cross.query requires 'concepts' (list of concept names), "
                                 "or a non-empty session horizon (horizon.add …) to default to")

    set_names: List[str] = []
    resolved_names: List[str] = []
    for c in concepts:
        sname = resolve_concept_to_set_name(kernel, c, session)
        if sname:
            set_names.append(sname)
            resolved_names.append(c)

    if not set_names:
        return _err(rid, -32002, "None of the specified concepts have an active root in this session.")

    focal_raw = data.get("id", "") or session.get_context("focus") or ""
    focal_key = focal_raw or None
    fmt = data.get("format", "raw")
    # mode: coverage (default, today's behavior — union weighted by coverage) | strict (the true
    # intersection: only atoms present in EVERY named concept). strict is a post-filter of coverage.
    mode = (data.get("mode") or "coverage").strip().lower()

    try:
        result = ctx.cross_query(set_names, resolved_names, allowed_scopes=scopes)
    except Exception as e:
        return _err(rid, -32603, f"cross_query failed: {e}")

    if mode == "strict" and resolved_names:
        n = len(resolved_names)
        kept = [r for r in result.get("intersection", []) if len(r.get("present_in", [])) == n]
        result = {"intersection": kept, "count": len(kept)}

    payload = {
        "focal":    focal_key,
        "concepts": resolved_names,
        "mode":     mode,
        **result,
    }
    if used_horizon:
        payload["source"] = "horizon"

    if fmt == "cosmos":
        payload = format_cross_cosmos(focal_key, resolved_names, result)

    return _ok(rid, payload)


def handle_cross_axes(kernel, rid, data, session, ctx, scopes) -> dict:
    concepts_raw = data.get("concepts", [])
    if isinstance(concepts_raw, str):
        concepts = [c.strip() for c in concepts_raw.split() if c.strip()]
    else:
        concepts = [c for c in list(concepts_raw) if c]

    # No concepts specified: enumerate all registered models
    if not concepts and _registry_mod.get_active():
        concepts = list(_registry_mod.get_active().get_concept_prefixes().values())

    set_names: List[str] = []
    resolved_names: List[str] = []
    for c in concepts:
        sname = resolve_concept_to_set_name(kernel, c, session)
        if sname:
            set_names.append(sname)
            resolved_names.append(c)

    if not set_names:
        return _ok(rid, {"concepts": [], "available_axes": [], "recommended": None})

    try:
        result = ctx.cross_axes(set_names, resolved_names, allowed_scopes=scopes)
    except Exception as e:
        return _err(rid, -32603, f"cross_axes failed: {e}")

    return _ok(rid, result)


def handle_cross_atom(kernel, rid, data, session, ctx, scopes) -> dict:
    atom_raw = (data.get("atom") or "").strip()
    if not atom_raw:
        return _err(rid, -32602, "sys.cross.atom requires 'atom' (proto-word alias or key)")

    concepts_raw = data.get("concepts", [])
    if isinstance(concepts_raw, str):
        concepts = [c.strip() for c in concepts_raw.split() if c.strip()]
    else:
        concepts = [str(c) for c in concepts_raw if c]

    # Resolve alias (e.g. "icarus" → word:icarus key) then fall back to raw
    resolved_key = ctx.resolve_alias(atom_raw) or atom_raw

    set_names: List[str] = []
    resolved_names: List[str] = []
    for c in concepts:
        sname = resolve_concept_to_set_name(kernel, c, session)
        if sname:
            set_names.append(sname)
            resolved_names.append(c)

    try:
        result = ctx.cross_atom(resolved_key, set_names, resolved_names, allowed_scopes=scopes)
    except Exception as e:
        return _err(rid, -32603, f"cross.atom failed: {e}")

    return _ok(rid, {
        "atom":       resolved_key,
        "atom_query": atom_raw,
        "concepts":   resolved_names or None,
        **result,
    })


def format_cross_cosmos(
    focal_key: Optional[str],
    concepts: List[str],
    result: Dict[str, Any],
) -> Dict[str, Any]:
    """Formats cross_query result as a Cosmos/3D-Force-Graph ready payload."""
    nodes: List[Dict[str, Any]] = []
    links: List[Dict[str, Any]] = []
    seen: set = set()

    if focal_key and focal_key not in seen:
        nodes.append({"id": focal_key, "name": focal_key[:16], "group": "focus", "val": 20})
        seen.add(focal_key)

    for item in result.get("intersection", []):
        key = item["key"]
        if key not in seen:
            nodes.append({
                "id":         key,
                "name":       item["preview"],
                "group":      "cross",
                "val":        int(item["weight"] * 15) + 5,
                "present_in": item["present_in"],
            })
            seen.add(key)
        if focal_key:
            links.append({"source": focal_key, "target": key, "type": "cross"})

    return {
        "focal":    focal_key,
        "concepts": concepts,
        "nodes":    nodes,
        "links":    links,
        "count":    result.get("count", len(nodes)),
    }
