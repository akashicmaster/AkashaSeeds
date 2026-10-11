"""
CSL ops (csl / csl.check / csl.build), locale.*, onboarding.seed, moved out of the kernel (backend layout order 2026-09-20). Bodies verbatim except `self.` → `kernel.`.

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
from lib.akasha.api.rpc import ok as _ok, err as _err

logger = logging.getLogger("Akasha.Kernel")


def _csl_load(kernel, rid, data):
    """Shared prelude of the csl ops: the CSL runtime, the input (inline CSL text or a path to a
    .csl file), and the parse. Returns (error_response, None, None, None) or
    (None, (validate, compile_script, CslRuntime), source, ast)."""
    try:
        from lib.akasha.csl import tokenize, parse, validate, compile_script, CslRuntime
    except ImportError as exc:
        return _err(rid, -32603, f"CSL runtime not available: {exc}"), None, None, None

    # Resolve input — inline CSL text or path to a .csl file
    source = (data.get("script") or data.get("source") or "").strip()
    if not source:
        return _err(rid, -32602, "csl requires 'script' (inline CSL text or path to a .csl file)"), None, None, None

    from_file = None
    if source.endswith(".csl") and "\n" not in source:
        from_file = source
        try:
            with open(from_file, "r", encoding="utf-8") as fh:
                source = fh.read().strip()
        except OSError as exc:
            return _err(rid, -32602, f"Cannot read CSL file '{from_file}': {exc}"), None, None, None

    # ── Parse ─────────────────────────────────────────────────────────
    try:
        tokens = tokenize(source)
        ast    = parse(tokens)
    except Exception as exc:
        return _err(rid, -32602, f"CSL parse error: {exc}"), None, None, None
    return None, (validate, compile_script, CslRuntime), source, ast


def _csl_compile(rid, validate, compile_script, ast):
    """Validate before compile/run; (error_response, None) or (None, calls)."""
    errors      = validate(ast)
    hard_errors = [e for e in errors if e.level == "error"]
    if hard_errors:
        return _err(
            rid, -32602,
            f"CSL validation failed: {hard_errors[0].error} (line {hard_errors[0].line})",
        ), None
    return None, compile_script(ast)


def handle_csl_check(kernel, rid, data: dict, session,
                     transport_trust: str = TRUST_NETWORK) -> dict:
    """csl.check — validation only."""
    err, rt, source, ast = _csl_load(kernel, rid, data)
    if err is not None:
        return err
    validate, _compile_script, _CslRuntime = rt
    errors = validate(ast)
    return _ok(rid, {
        "valid": not any(e.level == "error" for e in errors),
        "errors": [
            {
                "line":       e.line,
                "col":        e.col,
                "error":      e.error,
                "parameter":  e.parameter,
                "suggestion": e.suggestion,
                "level":      e.level,
            }
            for e in errors
        ],
    })


def handle_csl_build(kernel, rid, data: dict, session,
                     transport_trust: str = TRUST_NETWORK) -> dict:
    """csl.build — transpile to .ak."""
    err, rt, source, ast = _csl_load(kernel, rid, data)
    if err is not None:
        return err
    validate, compile_script, _CslRuntime = rt
    err, calls = _csl_compile(rid, validate, compile_script, ast)
    if err is not None:
        return err
    ak_lines = _csl_calls_to_ak(calls)
    out_path = (data.get("out") or "").strip() or None
    if out_path:
        try:
            with open(out_path, "w", encoding="utf-8") as fh:
                fh.write(ak_lines)
        except OSError as exc:
            return _err(rid, -32603, f"Cannot write .ak file '{out_path}': {exc}")
    return _ok(rid, {
        "ak":           ak_lines,
        "call_count":   len(calls),
        "source_lines": len(source.splitlines()),
        "out":          out_path,
    })


def handle_csl_run(kernel, rid, data: dict, session,
                   transport_trust: str = TRUST_NETWORK) -> dict:
    """csl / csl.run — check + build + execute via CslRuntime."""
    err, rt, source, ast = _csl_load(kernel, rid, data)
    if err is not None:
        return err
    validate, compile_script, CslRuntime = rt
    err, calls = _csl_compile(rid, validate, compile_script, ast)
    if err is not None:
        return err
    # begin_batch() / set_sync_fast() on the DB WriteQueue threads so
    # each commit is instant (synchronous=OFF) without losing cross-thread
    # read visibility.  Restored in the finally block.
    nucleus   = getattr(session, 'nucleus', None)
    _nuc_core = nucleus.core if nucleus else None
    _loc_core = getattr(getattr(session, 'local_cortex', None), 'core', None)
    for _core in (_nuc_core, _loc_core):
        if _core is not None:
            try:
                _core.begin_batch()
                _core.set_sync_fast()
            except Exception:
                pass
    try:
        runtime = CslRuntime(session, dispatcher=kernel, transport_trust=transport_trust)
        results = runtime.run(calls)
    finally:
        for _core in (_nuc_core, _loc_core):
            if _core is not None:
                try:
                    _core.end_batch()
                    _core.set_sync_normal()
                except Exception:
                    pass
    # S2-d(3) — `fail_on_refused` (set by macro.run's background job): a script whose command was
    # REFUSED (a grant denial returns status=refused, not an exception) must FAIL the job, not end
    # DONE 1/1 with nothing written. Surface the first refusal as an error the JCL step reports.
    if data.get("fail_on_refused"):
        for r in results:
            _res = r.result if isinstance(r.result, dict) else {}
            if r.error or _res.get("status") == "refused":
                _why = r.error or _res.get("reason") or "refused"
                return _err(rid, -32003, f"{r.method}: {_why}")
    return _ok(rid, {
        "results": [
            {
                "method":     r.method,
                "result":     r.result,
                "error":      r.error,
                "assigns_to": r.assigns_to,
            }
            for r in results
        ]
    })


def handle_locale_get(kernel, rid, session) -> dict:
    loc = session.locale
    return _ok(rid, {
        "primary":   loc.primary,
        "supported": loc.supported,
        "priority":  loc.get_priority_list(),
    })


def handle_locale_set(kernel, rid, data, session) -> dict:
    """
    locale.set  primary=<code>  [supported=<code>,<code>,...]

    If only 'primary' is given, the code is moved to the front of the
    existing supported list (added if absent).
    If 'supported' is given, it replaces the full supported list
    (primary is always prepended automatically).
    """
    primary   = data.get("primary", "").strip().lower()
    supported = data.get("supported", "")

    if not primary and not supported:
        return _err(rid, -32602, "locale.set requires 'primary' and/or 'supported'")

    loc = session.locale

    if supported:
        codes = [c.strip().lower() for c in supported.replace(",", " ").split() if c.strip()]
        if not codes:
            return _err(rid, -32602, "locale.set: 'supported' must be a non-empty list")
        loc.supported = codes

    if primary:
        loc.set_primary(primary)

    session.save_locale()
    return _ok(rid, {
        "primary":   loc.primary,
        "supported": loc.supported,
        "priority":  loc.get_priority_list(),
    })


def _csl_calls_to_ak(calls) -> str:
    """Convert a list of CompiledCall objects to .ak format text."""
    lines = []
    for call in calls:
        if getattr(call, 'comment', None):
            lines.append(f"# {call.comment}")
        m = call.method
        p = call.params
        if m in ("define", "kernel.memory.define", "def"):
            name = p.get("name", "")
            desc = p.get("description", "")
            lines.append(f'def "{name}" "{desc}"')
        elif m in ("ln", "link.create", "kernel.memory.link"):
            src = p.get("src", "")
            dst = p.get("dst", "")
            rel = p.get("rel", "thesaurus:related")
            lines.append(f"ln {src} {dst} {rel}")
        elif m in ("al", "alias", "kernel.identity.alias"):
            atom_id = p.get("id", "")
            name    = p.get("name", "")
            lines.append(f"al {atom_id} {name}")
        elif m == "set.add":
            name    = p.get("name", "")
            atom_id = p.get("id", "")
            lines.append(f'set.add name="{name}" id="{atom_id}"')
        else:
            lines.append(f"# [method: {m}] {json.dumps(p, ensure_ascii=False)}")
    return "\n".join(lines)
