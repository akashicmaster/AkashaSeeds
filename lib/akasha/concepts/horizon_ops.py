"""
The normalized semantic session's self-directed part (F53): focus / scope / horizon / sys.session.state / wb.* / log.* ops, moved out of the kernel (backend layout order 2026-09-20). Bodies verbatim except `self.` → `kernel.`.

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
    from lib.akasha.concepts.log import LogConcept
except ImportError:
    LogConcept = None  # type: ignore
try:
    from lib.akasha.concepts.whiteboard import WhiteboardConcept
except ImportError:
    WhiteboardConcept = None  # type: ignore
from lib.akasha.api.rpc import ok as _ok, err as _err

# ── constants moved from the kernel class (backend layout order 2026-09-20) ──
# ------------------------------------------------------------------
# F53 Phase 0 — the normalized semantic session
#
# Every connected client (admin / resident / guest / LLM) holds ONE session
# shaped as three parts: IDENTITY (who is answerable), GRANTED (what the world
# lets it SEE/WRITE — IAM, unchanged), and SELF-DIRECTED (the client's own
# whiteboard: horizon / focus / radius / axis — client-writable, world-ignorable,
# dies with the session). Invariant: self-directed can NEVER widen granted — a
# horizon entry naming an unreadable set is retained but inert, reported
# `ungranted` (visible, never silently dropped). All ops here are session-local
# (no store writes) and guest-callable; storage rides the existing
# get_context/set_context (in-memory for read-only sessions, session-atom meta
# for owning ones — same shape both kinds: that IS the normalization).
# ------------------------------------------------------------------
_HORIZON_CAP = 8
_HORIZON_MODES = ("soft", "lens")


from lib.akasha.concepts import cross_ops
logger = logging.getLogger("Akasha.Kernel")


def get_scope_state(kernel, session) -> dict:
    """Effective scope state. F54: reads ONLY the session-global keys — the whiteboard-local scope
    branch is retired; a board's axis/radius/time now ride its wb:<name>:state, restored into these
    global keys by wb.focus. `radius` is the depth spelling; reads prefer `radius` and fall back to
    the RETIRED-but-still-readable `active_scope` (writers stopped writing it in F54; the fallback
    stays one more series so pre-F54 sessions/checkpoints still resolve). `scope` tracks the same
    effective depth so every existing reader keeps working."""
    _scope = session.get_context("active_scope")           # retired write key — read fallback only
    _radius = session.get_context("radius")
    _depth = _radius if _radius is not None else _scope
    return {
        "axis":   session.get_context("active_axis"),
        "scope":  _depth,
        "radius": _depth,
        "time":   session.get_context("active_time"),
    }


def parse_focus_tokens(kernel, tokens: list, client_id: str) -> dict:
    """Parse @-prefixed focus tokens into a structured filter dict."""
    scopes: list = []
    ns_prefixes: list = []
    for tok in tokens:
        if tok == "@me":
            scopes.append(f"owner:{client_id}")
        elif tok.startswith("@group:"):
            scopes.append(f"scope:group:{tok[len('@group:'):]}")
        elif tok.startswith("@ns:"):
            ns_prefixes.append(tok[len("@ns:"):] + ":")
    return {"scopes": scopes, "ns_prefixes": ns_prefixes}


def get_display_focus(kernel, session) -> dict:
    return session.get_context("display_focus") or {}


def passes_display_focus(kernel, key: str, focus: dict, ctx, nucleus) -> bool:
    """Return True if atom passes all active display focus filters (AND logic)."""
    if not focus:
        return True
    for scope in focus.get("scopes", []):
        ok = ctx.core.check_chunk_access_any(key, [scope])
        if not ok and nucleus:
            ok = nucleus.core.check_chunk_access_any(key, [scope])
        if not ok:
            return False
    for prefix in focus.get("ns_prefixes", []):
        aliases = ctx.core.get_aliases_by_key(key) or []
        if nucleus:
            aliases += nucleus.core.get_aliases_by_key(key) or []
        if not any(a.startswith(prefix) for a in aliases):
            return False
    return True


def handle_focus(kernel, rid, data, session, client_id) -> dict:
    tokens = data.get("tokens", [])
    nucleus = getattr(session, 'nucleus', None)
    ctx    = session.local_cortex

    if not tokens:
        current = session.get_context("display_focus") or {}
        active: list = []
        for s in current.get("scopes", []):
            if s == f"owner:{client_id}":
                active.append("@me")
            elif s.startswith("scope:group:"):
                active.append("@group:" + s[len("scope:group:"):])
            else:
                active.append(s)
        for p in current.get("ns_prefixes", []):
            active.append("@ns:" + p.rstrip(":"))
        return _ok(rid, {"focus_state": " + ".join(active) if active else "@all"})

    if tokens == ["@all"]:
        session.set_context("display_focus", None)
        return _ok(rid, {"focus_state": "@all", "status": "cleared"})

    focus = parse_focus_tokens(kernel, tokens, client_id)
    session.set_context("display_focus", focus)
    labels: list = []
    for s in focus["scopes"]:
        if s == f"owner:{client_id}":
            labels.append("@me")
        elif s.startswith("scope:group:"):
            labels.append("@group:" + s[len("scope:group:"):])
    for p in focus["ns_prefixes"]:
        labels.append("@ns:" + p.rstrip(":"))
    return _ok(rid, {"focus_state": " + ".join(labels), "status": "set"})


def handle_scope_set(kernel, rid, data, session) -> dict:
    # F54 — `active_scope` is RETIRED as a WRITTEN key: writers write ONLY `radius` (readers keep
    # the active_scope fallback one more series). The whiteboard-local branch is gone — a board's
    # scope rides wb:<name>:state, restored into the global keys by wb.focus. Accept radius|scope
    # (radius wins).
    if "axis" in data:
        session.set_context("active_axis", data["axis"] or None)
    if ("radius" in data) or ("scope" in data):
        _raw = data["radius"] if "radius" in data else data.get("scope")
        session.set_context("radius", int(_raw) if _raw is not None else None)
    if "time" in data:
        session.set_context("active_time", data["time"] or None)
    st = get_scope_state(kernel, session)
    return _ok(rid, {
        "status":       "scope_updated",
        "active_axis":  st["axis"],
        "active_scope": st["scope"],   # response mirrors the effective depth (= radius)
        "radius":       st["radius"],
        "active_time":  st["time"],
    })


def handle_scope_get(kernel, rid, session) -> dict:
    scope = get_scope_state(kernel, session)
    result = {
        "active_axis":  scope["axis"],
        "active_scope": scope["scope"],
        "radius":       scope["radius"],
        "active_time":  scope["time"],
    }
    active_wb = session.get_context("active_whiteboard")
    if active_wb:
        result["whiteboard"] = active_wb   # informational only — no longer drives scope state
    return _ok(rid, result)


def handle_scope_reset(kernel, rid, session) -> dict:
    # F54 — no whiteboard-local branch; clear the global keys (incl. the retired active_scope so a
    # stale fallback never lingers).
    for key in ("active_axis", "radius", "active_scope", "active_time"):
        session.set_context(key, None)
    return _ok(rid, {
        "status":       "scope_reset",
        "active_axis":  None,
        "active_scope": None,
        "radius":       None,
        "active_time":  None,
    })


def horizon_get(kernel, session) -> list:
    hz = session.get_context("horizon")
    return list(hz) if isinstance(hz, list) else []


def horizon_resolve(kernel, entry, session):
    """(set_name_or_None) for a horizon entry — via the SAME resolver cross.query uses. An entry
    that resolves to no active root in this session is ungranted (inert)."""
    raw = (entry or {}).get("set", "")
    return cross_ops.resolve_concept_to_set_name(kernel, raw, session)


def horizon_granted(kernel, entry, session) -> bool:
    return horizon_resolve(kernel, entry, session) is not None


def horizon_view(kernel, hz, session) -> list:
    """The reportable horizon: {set, mode, granted}. No member sweep (grant is one resolver call)."""
    return [{"set": e.get("set"), "mode": e.get("mode", "soft"),
             "granted": horizon_granted(kernel, e, session)} for e in hz]


def handle_horizon_add(kernel, rid, data, session) -> dict:
    raw = (data.get("set") or data.get("name") or data.get("concept") or "").strip()
    if not raw:
        return _err(rid, -32602, "horizon.add requires set=<name-or-concept>")
    mode = (data.get("mode") or "soft").strip().lower()
    if mode not in _HORIZON_MODES:
        return _err(rid, -32602, "horizon mode must be 'soft' (re-rank) or 'lens' (clip)")
    hz = horizon_get(kernel, session)
    for e in hz:                                    # already present → update its mode in place
        if e.get("set") == raw:
            e["mode"] = mode
            session.set_context("horizon", hz)
            return _ok(rid, {"status": "horizon_updated", "set": raw, "mode": mode,
                             "ungranted": not horizon_granted(kernel, e, session),
                             "horizon": horizon_view(kernel, hz, session)})
    if len(hz) >= _HORIZON_CAP:                # cap: refuse LOUDLY, never trim (spec §1)
        return _err(rid, -32602,
                    "horizon is full (%d entries) — horizon.rm one first; entries are never "
                    "silently trimmed" % _HORIZON_CAP)
    entry = {"set": raw, "mode": mode}
    hz.append(entry)
    session.set_context("horizon", hz)
    granted = horizon_granted(kernel, entry, session)
    return _ok(rid, {"status": "horizon_added", "set": raw, "mode": mode,
                     "ungranted": not granted, "horizon": horizon_view(kernel, hz, session)})


def handle_horizon_rm(kernel, rid, data, session) -> dict:
    raw = (data.get("set") or data.get("name") or data.get("concept") or "").strip()
    hz = horizon_get(kernel, session)
    kept = [e for e in hz if e.get("set") != raw]
    session.set_context("horizon", kept)
    return _ok(rid, {"status": "horizon_removed", "set": raw, "removed": len(hz) - len(kept),
                     "horizon": horizon_view(kernel, kept, session)})


def handle_horizon_clear(kernel, rid, session) -> dict:
    session.set_context("horizon", [])
    return _ok(rid, {"status": "horizon_cleared", "horizon": []})


def handle_horizon_mode(kernel, rid, data, session) -> dict:
    raw = (data.get("set") or data.get("name") or data.get("concept") or "").strip()
    mode = (data.get("mode") or "").strip().lower()
    if mode not in _HORIZON_MODES:
        return _err(rid, -32602, "horizon mode must be 'soft' or 'lens'")
    hz = horizon_get(kernel, session)
    hit = False
    for e in hz:
        if e.get("set") == raw:
            e["mode"] = mode
            hit = True
    if not hit:
        return _err(rid, -32602, "no horizon entry for '%s' — horizon.add it first" % raw)
    session.set_context("horizon", hz)
    return _ok(rid, {"status": "horizon_mode_set", "set": raw, "mode": mode,
                     "horizon": horizon_view(kernel, hz, session)})


def handle_horizon_ls(kernel, rid, session) -> dict:
    hz = horizon_get(kernel, session)
    return _ok(rid, {"horizon": horizon_view(kernel, hz, session),
                     "count": len(hz), "cap": _HORIZON_CAP})


def session_kind(kernel, session) -> str:
    rv = getattr(getattr(session, "role", None), "value", getattr(session, "role", None))
    if rv == "admin":
        return "admin"
    if rv == "guest":
        return "guest"
    return "resident"          # user / librarian / group_admin — and any LLM authenticated as one


def handle_session_state(kernel, rid, session) -> dict:
    """[sys.session.state] The normalized session triple — identically shaped for EVERY client kind
    (admin / resident / guest / LLM-over-MCP). Absorbs sys.scope.get + the cogito scope fragments as
    a superset READ; those keep answering as today. Guest-callable, no store writes."""
    kind = session_kind(kernel, session)
    identity = {"client": getattr(session, "client_id", None), "kind": kind}
    if kind == "guest":        # a guest's TTL is part of the grant (best-effort from last_active)
        la = getattr(session, "last_active", None)
        if la is not None:
            try:
                ttl = int(os.environ.get("AKASHA_GUEST_TTL", "900") or 900)
                identity["expires_at"] = round(float(la) + ttl, 3)
            except (TypeError, ValueError):
                pass
    st = get_scope_state(kernel, session)
    radius = session.get_context("radius")
    if radius is None:
        radius = st.get("scope")                    # prefer radius, fall back active_scope
    hz = horizon_get(kernel, session)
    return _ok(rid, {
        "identity": identity,
        "granted": {"read_scopes": list(getattr(session, "active_scopes", []) or []),
                    "write": (not getattr(session, "read_only", False)),
                    "class": kind},
        "self_directed": {"horizon": horizon_view(kernel, hz, session),
                          "focus": session.get_context("focus"),
                          "radius": radius,
                          "axis": st.get("axis")},
    })


def apply_horizon(kernel, session, associations, ctx):
    """F53 Stage 3 — the ONE consumer of the self-directed horizon on the enrichment path.

    GUARDED: with no horizon it returns the association list UNCHANGED (this is the archives/default
    path — bit-identical; no archives client ever has a horizon). With a horizon:
      • SOFT entries re-rank: weight × (1 + 0.25·k) for membership in k soft horizon sets — a nudge,
        never a filter (result COUNT is unchanged).
      • LENS entries CLIP the list to the UNION of the lens sets and annotate ({"lens": [...]}).
    Strictly inside the caller's grant: the associations are ALREADY IAM-filtered, and an
    ungranted/unresolvable horizon entry is inert (self-directed can never widen granted).
    Membership is one get_collections_for_key per candidate — bounded by the association list (R1).
    Returns (associations, annotation)."""
    hz = session.get_context("horizon") or []
    if not hz:
        return associations, {}          # ← the archives / no-horizon path: unchanged, bit-identical
    soft, lens = set(), set()
    for e in hz:
        sname = cross_ops.resolve_concept_to_set_name(kernel, e.get("set", ""), session)
        if not sname:
            continue                     # ungranted / unresolvable → inert
        (lens if e.get("mode") == "lens" else soft).add(sname)
    if not soft and not lens:
        return associations, {}
    # Membership is checked against BOTH the session cortex AND the shared nucleus — public sets
    # (set:concept:*, set:thesaurus:*, …) live in the nucleus, the same union the association
    # traversal itself uses. One get_collections_for_key per candidate (bounded by the list — R1).
    core = getattr(ctx, "core", None)
    _nuc = getattr(ctx, "_nucleus", None)
    nuc_core = getattr(_nuc, "core", None) if _nuc is not None else None

    def _collections(key):
        s = set()
        for c in (core, nuc_core):
            if c is None:
                continue
            try:
                s |= set(c.get_collections_for_key(key) or [])
            except Exception:
                pass
        return s
    memb = {a.get("key"): _collections(a.get("key")) for a in associations}
    out, ann = associations, {}
    if lens:                             # clip to the UNION of lens sets, annotate survivors
        clipped = []
        for a in out:
            hits = memb.get(a.get("key"), set()) & lens
            if hits:
                a2 = dict(a)
                a2["lens"] = sorted(hits)
                clipped.append(a2)
        out = clipped
        ann["lens"] = sorted(lens)       # present even when the clip is empty (empty list, not error)
    if soft:                             # nudge membership up; stable, never drops
        out = sorted(out, key=lambda a: float(a.get("weight", 1.0) or 1.0)
                     * (1.0 + 0.25 * len(memb.get(a.get("key"), set()) & soft)), reverse=True)
    return out, ann


def handle_horizon_enclose(kernel, rid, data, session, ctx, scopes) -> dict:
    """[horizon.enclose] Stage 4 — the ONLY store-writing horizon op: persist the intersection of
    the current GRANTED LENS horizon entries (>=2 required) as a named set, stamped with its
    provenance {derived_from_horizon, by, at}. Write-gated as any set op (METHOD_TO_ACTION 'write'),
    so a guest is refused by the ordinary gate before reaching here. The intersection is
    scope-filtered (it agrees with cross.query mode=strict) and ungranted entries are excluded —
    self-directed never widens granted."""
    name = (data.get("name") or data.get("set") or "").strip()
    if not name:
        return _err(rid, -32602, "horizon.enclose requires name=<result set>")
    lens_sets, seen = [], set()
    for e in horizon_get(kernel, session):
        if e.get("mode") != "lens":
            continue
        sname = cross_ops.resolve_concept_to_set_name(kernel, e.get("set", ""), session)
        if sname and sname not in seen:   # granted only; ungranted lens entries are excluded
            seen.add(sname)
            lens_sets.append(sname)
    if len(lens_sets) < 2:
        return _err(rid, -32602, "horizon.enclose needs >=2 GRANTED lens horizon entries "
                    "(horizon.add set=<name> mode=lens); have %d" % len(lens_sets))
    # the isect of the lens sets (the same operation as set.op 'isect'; agrees with
    # cross.query mode=strict). Members are read from BOTH the cortex and the shared nucleus
    # (public sets live in the nucleus); the durable enclosure is written to the nucleus when
    # present so it is a shared, inspectable set.
    _nuc = getattr(ctx, "_nucleus", None)
    nuc_core = getattr(_nuc, "core", None) if _nuc is not None else None

    def _members(sname):
        s = set(ctx.get_collection_members(sname) or [])
        if nuc_core is not None:
            try:
                s |= set(nuc_core.get_collection_members(sname) or [])
            except Exception:
                pass
        return s
    common = _members(lens_sets[0])
    for s in lens_sets[1:]:
        common &= _members(s)
    store = nuc_core if nuc_core is not None else ctx.core
    for kk in common:
        store.add_to_collection(name, kk)
    members = sorted(_members(name))
    at = time.time()
    by = getattr(session, "client_id", "unknown")
    prov = {"type": "horizon:enclosure", "derived_from_horizon": lens_sets, "by": by, "at": at}
    descriptor = None
    try:                                  # a descriptor atom carries the provenance; the set name
        if nuc_core is not None and hasattr(_nuc, "put_atom"):
            descriptor = _nuc.put_atom("horizon enclosure of " + ", ".join(lens_sets), prov, author=by)
            nuc_core.put_alias(descriptor, name)
        else:
            descriptor = ctx.put_chunk("horizon enclosure of " + ", ".join(lens_sets),
                                       meta=prov, author=by)
            ctx.core.put_alias(descriptor, name)
    except Exception as exc:
        logger.debug("[horizon.enclose] provenance descriptor skipped: %s", exc)
    return _ok(rid, {"status": "enclosed", "set": name, "count": len(members),
                     "members": members[:200], "derived_from_horizon": lens_sets,
                     "by": by, "at": at, "descriptor": descriptor})


def handle_wb_new(kernel, rid, data, session) -> dict:
    name = data.get("name", "")
    if not name:
        return _err(rid, -32602, "wb.new requires 'name'")
    try:
        res = WhiteboardConcept(session).op_new(name=name)
    except Exception as e:
        return _err(rid, -32603, str(e))
    return _ok(rid, res)


def handle_wb_pin(kernel, rid, data, session) -> dict:
    concept = data.get("concept", "")
    if not concept:
        return _err(rid, -32602, "wb.pin requires 'concept'")
    try:
        res = WhiteboardConcept(session).op_pin(concept=concept)
    except Exception as e:
        return _err(rid, -32603, str(e))
    return _ok(rid, res)


def handle_wb_unpin(kernel, rid, data, session) -> dict:
    concept = data.get("concept", "")
    if not concept:
        return _err(rid, -32602, "wb.unpin requires 'concept'")
    try:
        res = WhiteboardConcept(session).op_unpin(concept=concept)
    except Exception as e:
        return _err(rid, -32603, str(e))
    return _ok(rid, res)


def handle_wb_focus(kernel, rid, data, session) -> dict:
    name = data.get("name", "")
    if not name:
        return _err(rid, -32602, "wb.focus requires 'name'")
    try:
        res = WhiteboardConcept(session).op_focus(name=name)
    except Exception as e:
        return _err(rid, -32603, str(e))
    return _ok(rid, res)


def handle_wb_ls(kernel, rid, session) -> dict:
    try:
        res = WhiteboardConcept(session).op_list()
    except Exception as e:
        return _err(rid, -32603, str(e))
    return _ok(rid, res)


def handle_wb_show(kernel, rid, session) -> dict:
    try:
        res = WhiteboardConcept(session).op_show()
    except Exception as e:
        return _err(rid, -32603, str(e))
    return _ok(rid, res)


def handle_wb_rm(kernel, rid, data, session) -> dict:
    name = data.get("name", "")
    if not name:
        return _err(rid, -32602, "wb.rm requires 'name'")
    try:
        res = WhiteboardConcept(session).op_delete(name=name)
    except Exception as e:
        return _err(rid, -32603, str(e))
    return _ok(rid, res)


def handle_log_new(kernel, rid, data, session) -> dict:
    name = data.get("name", "")
    if not name:
        return _err(rid, -32602, "log.new requires 'name'")
    try:
        concept = LogConcept(session)
        res = concept.op_new(name=name)
    except Exception as e:
        return _err(rid, -32603, str(e))
    return _ok(rid, res)


def handle_log_ls(kernel, rid, session) -> dict:
    try:
        concept = LogConcept(session)
        res = concept.op_ls()
    except Exception as e:
        return _err(rid, -32603, str(e))
    return _ok(rid, res)


def handle_log_checkpoint(kernel, rid, data, session) -> dict:
    concept = LogConcept(session)
    if not concept.concept_id:
        return _err(rid, -32002, "No active log. Use log.new first.")
    try:
        res = concept.op_checkpoint(note=data.get("note") or None)
    except Exception as e:
        return _err(rid, -32603, str(e))
    return _ok(rid, res)


def handle_log_annotate(kernel, rid, data, session) -> dict:
    text = data.get("text", "")
    if not text:
        return _err(rid, -32602, "log.annotate requires 'text'")
    concept = LogConcept(session)
    if not concept.concept_id:
        return _err(rid, -32002, "No active log. Use log.new first.")
    try:
        res = concept.op_annotate(text=text)
    except Exception as e:
        return _err(rid, -32603, str(e))
    return _ok(rid, res)


def handle_log_replay(kernel, rid, session) -> dict:
    concept = LogConcept(session)
    if not concept.concept_id:
        return _err(rid, -32002, "No active log. Use log.new first.")
    try:
        res = concept.op_replay()
    except Exception as e:
        return _err(rid, -32603, str(e))
    return _ok(rid, res)


def handle_log_read(kernel, rid, session) -> dict:
    concept = LogConcept(session)
    if not concept.concept_id:
        return _err(rid, -32002, "No active log. Use log.new first.")
    try:
        res = concept.op_read()
    except Exception as e:
        return _err(rid, -32603, str(e))
    return _ok(rid, res)


def handle_log_rm(kernel, rid, session) -> dict:
    concept = LogConcept(session)
    if not concept.concept_id:
        return _err(rid, -32002, "No active log. Use log.new first.")
    try:
        res = concept.op_delete()
    except Exception as e:
        return _err(rid, -32603, str(e))
    return _ok(rid, res)
