"""
Macro ops (macro.def/run/ls/get/rm) + the boot macro load, moved out of the kernel (backend layout order 2026-09-20). Bodies verbatim except `self.` → `kernel.`.

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
from lib.akasha.api.trust import (TRUST_NETWORK, TRUST_LOCAL, TRUST_INTERNAL,
                                  TRUSTED_TRANSPORTS as _TRUSTED_TRANSPORTS)
from lib.akasha.api.heart import _rss_mb, _search_partial_incr, _SEARCH_PARTIAL, _MAINT_LOCK, _MAINT_LAST_DONE, _MAINT_GAP_S, _MAINT_GATE_AVAIL_MB, _MAINT_GATE_MAX_WAIT_S, _MAINT_GATE_RETRY_S, _maint_gate_ok, _run_gated_maint, _with_rss_delta, _mem_available_mb, _smaps_rollup, _thread_count, _open_fd_count, _fd_soft_limit, _autolearn_disabled_reason
from lib.akasha.api.rpc import ok as _ok, err as _err
from lib.akasha.jcl import workflow_vocab as _wf

from lib.akasha.concepts import csl_ops
logger = logging.getLogger("Akasha.Kernel")


def parse_macro_params(spec: str) -> "list":
    """Parse a params spec `"clock=world:default,from=1,to="` into ordered (name, default) pairs.
    A bare `name` (no `=`) is a required parameter (default ''); `name=` is an explicit empty
    default. Commas separate params; the FIRST `=` in each splits name from default (so a default
    may itself contain `=`/`:`)."""
    out = []
    for part in str(spec or "").split(","):
        part = part.strip()
        if not part:
            continue
        if "=" in part:
            nm, dv = part.split("=", 1)
            out.append((nm.strip(), dv))            # `name=` → explicit (possibly empty) default
        else:
            out.append((part, None))                # bare `name` → REQUIRED (no default)
    return out


def bind_macro_params(script: str, params: "list", provided: dict) -> "tuple":
    """Substitute `$name` occurrences in `script` with the provided value (or the default). Returns
    (bound_script, resolved_dict, missing_list). Whole-token match so `$from` never eats `$fromx`."""
    import re as _re
    resolved = {}
    missing = []
    bound = script
    for nm, default in params:
        val = provided.get(nm)
        if val is None or val == "":
            # default None means a bare `name` — REQUIRED; `name=` (default "") is optional-empty.
            if default is None and (val is None or val == "") and (provided.get(nm) in (None, "")):
                missing.append(nm)
                val = ""
            else:
                val = default if default is not None else ""
        resolved[nm] = val
        bound = _re.sub(r"\$" + _re.escape(nm) + r"\b", str(val), bound)
    return bound, resolved, missing


def handle_macro_def(kernel, rid, data, session, ctx,
                      transport_trust: str = TRUST_NETWORK) -> dict:
    name   = (data.get("name") or "").strip()
    script = data.get("script") or ""
    params = (data.get("params") or "").strip()
    if not name or not script:
        return _err(rid, -32602, "macro.def requires 'name' and 'script'")
    # syntax-check the script AFTER stripping the $param placeholders (they are not CSL tokens
    # until bound) — replace each $name with a harmless literal so tokenize/parse can validate shape.
    try:
        import re as _re
        probe = script
        for nm, _dv in parse_macro_params(params):
            probe = _re.sub(r"\$" + _re.escape(nm) + r"\b", "x", probe)
        from lib.akasha.csl import tokenize, parse
        parse(tokenize(probe))
    except ImportError:
        pass
    except Exception as _pe:
        return _err(rid, -32602, f"macro CSL syntax error: {_pe}")
    cid = session.client_id
    # A shipped macro (boot loader) is written UNIVERSAL so any admitted agent / a bench block run
    # by any owner can resolve it; `scope=universal` is honoured ONLY over a trusted transport
    # (local console / kernel-internal boot), never a network client. A user's own macro.def stays
    # private to that user.
    trusted = transport_trust in _TRUSTED_TRANSPORTS
    if str(data.get("scope") or "").strip() == "universal" and trusted:
        scopes = [_wf.SCOPE_EXECUTABLE, "scope:sys:universal"]
    else:
        scopes = [_wf.SCOPE_EXECUTABLE, f"owner:user_{cid}", f"view:user_{cid}"]
    key = ctx.put_chunk(
        content=script,
        meta={"type": _wf.META_MACRO, "name": name, "params": params,
              "description": data.get("description", "")},
        author=cid,
        scopes=scopes,
    )
    ctx.set_alias(key, f"{_wf.MACRO_ALIAS_PREFIX}{name}")
    return _ok(rid, {"status": "defined", "name": name, "key": key, "params": params,
                     "scope": "universal" if scopes[1].startswith("scope:sys:universal") else "owner",
                     "alias": f"{_wf.MACRO_ALIAS_PREFIX}{name}"})


def handle_macro_run(kernel, rid, data, session, ctx, transport_trust: str = TRUST_NETWORK) -> dict:
    name = (data.get("name") or "").strip()
    if not name:
        return _err(rid, -32602, "macro.run requires 'name'")
    key = ctx.resolve_alias(f"{_wf.MACRO_ALIAS_PREFIX}{name}")
    if not key:
        return _err(rid, -32001, f"Macro '{name}' not found.")
    meta = ctx.get_meta(key) or {}
    if meta.get("type") != _wf.META_MACRO:
        return _err(rid, -32001, f"'{name}' is not a macro definition.")
    script = ctx.get_chunk(key) or ""
    if not script:
        return _err(rid, -32001, f"Macro '{name}' has no script body.")
    params = parse_macro_params(meta.get("params") or "")
    # provided values come from data (minus the control keys), so `macro.run name=X clock=… from=…`
    provided = {k: v for k, v in (data or {}).items()
                if k not in ("name", "as", "session_token", "data")}
    bound, resolved, missing = bind_macro_params(script, params, provided)
    if missing:
        return _err(rid, -32602, f"macro.run '{name}' missing required params: {', '.join(missing)}")
    mode = str(data.get("as") or "").strip().lower()
    if mode == "inline":
        # Synchronous, read-only-by-capability: run the bound CSL in-process and render the last
        # result. The per-call kernel gate denies any write to a caller without the role, so a guest
        # inline macro can only READ. Reuse the csl.run machinery.
        resp = csl_ops.handle_csl_run(kernel, rid, {"script": bound}, session, transport_trust)
        if isinstance(resp, dict) and resp.get("error"):
            return resp
        results = ((resp or {}).get("result") or {}).get("results") or []
        last = results[-1] if results else None
        return _ok(rid, {"macro": name, "mode": "inline", "params": resolved,
                         "results": results, "last": last})
    # default — a background JCL job (like workflow.run): admin/librarian only.
    scopes = session.active_scopes
    if "scope:sys:admin" not in scopes and "role:librarian" not in scopes:
        return _err(rid, -32003, "macro.run (background) requires admin or librarian role — "
                                 "use as=inline for a read-only macro")
    if not kernel.jcl_worker or not JCLJob or not JCLStep:
        return _err(rid, -32002, "JCL worker not available")
    job = JCLJob(owner=session.client_id, label=f"macro:{name}",
                 steps=[JCLStep(method="csl.run",
                                params={"script": bound, "fail_on_refused": True})], fail_fast=True)
    kernel.harmonia.submit_job(job, job_class=CLASS_BATCH_ATOM)
    return _ok(rid, {"macro": name, "mode": "job", "params": resolved,
                     "status": "submitted", "job_id": job.job_id, "job_label": job.label})


def handle_macro_ls(kernel, rid, data, session, ctx) -> dict:
    rows = ctx.get_aliases_by_pattern(f"{_wf.MACRO_ALIAS_PREFIX}%") or []
    out = []
    for r in rows:
        alias = r.get("alias") if isinstance(r, dict) else r
        k = r.get("key") if isinstance(r, dict) else ctx.resolve_alias(alias)
        m = (ctx.get_meta(k) or {}) if k else {}
        if m.get("type") == _wf.META_MACRO:
            out.append({"name": m.get("name", alias[len(_wf.MACRO_ALIAS_PREFIX):]),
                        "alias": alias, "params": m.get("params", ""),
                        "description": m.get("description", "")})
    return _ok(rid, {"macros": out, "count": len(out)})


def handle_macro_get(kernel, rid, data, session, ctx) -> dict:
    name = (data.get("name") or "").strip()
    if not name:
        return _err(rid, -32602, "macro.get requires 'name'")
    key = ctx.resolve_alias(f"{_wf.MACRO_ALIAS_PREFIX}{name}")
    if not key:
        return _err(rid, -32001, f"Macro '{name}' not found.")
    meta = ctx.get_meta(key) or {}
    return _ok(rid, {"name": name, "key": key, "params": meta.get("params", ""),
                     "description": meta.get("description", ""), "script": ctx.get_chunk(key) or ""})


def handle_macro_rm(kernel, rid, data, session, ctx) -> dict:
    name = (data.get("name") or "").strip()
    if not name:
        return _err(rid, -32602, "macro.rm requires 'name'")
    alias = f"{_wf.MACRO_ALIAS_PREFIX}{name}"
    key = ctx.resolve_alias(alias)
    if not key:
        return _err(rid, -32001, f"Macro '{name}' not found.")
    meta = ctx.get_meta(key) or {}
    if meta.get("type") != _wf.META_MACRO:
        return _err(rid, -32001, f"'{name}' is not a macro definition.")
    ctx.delete_alias(alias)
    return _ok(rid, {"status": "removed", "name": name})


def schedule_macro_load(kernel) -> None:
    """G4 §3.1 — load the application's MACROS (the `macros` declaration root, `*.csl`) at boot, behind a per-macro content
    sentinel, as UNIVERSAL macros so any admitted agent / a bench block run by any owner can call
    them. Each file's first `#!params …` line declares its parameters; the rest is the CSL body.
    Writer-only, run-once per (name, sha), NON-CLOBBERING re-def on a content change. Cheap (a few
    small files, no relations dependency), so it runs inline on the writer-daemon thread."""
    if os.environ.get("AKASHA_SERVE_ONLY", "").strip().lower() not in ("", "0", "no", "false", "off"):
        return
    import glob as _glob
    from lib.akasha.api import reserved as _reserved
    mdir = _reserved.root("macros")
    files = sorted(_glob.glob(os.path.join(mdir, "*.csl")))
    if not files:
        return
    sent_dir = os.path.join(kernel.base_dir, "central", "sentinels")
    try:
        os.makedirs(sent_dir, exist_ok=True)
    except Exception:
        pass
    for path in files:
        try:
            name = os.path.splitext(os.path.basename(path))[0]
            with open(path, "r", encoding="utf-8") as f:
                raw = f.read()
            params = ""
            body_lines = []
            for ln in raw.splitlines():
                st = ln.strip()
                if st.startswith("#!params"):
                    params = st[len("#!params"):].strip()
                    continue
                if st.startswith("#"):
                    continue
                body_lines.append(ln)
            script = "\n".join(body_lines).strip()
            if not script:
                continue
            import hashlib as _hl
            sha = _hl.sha256((params + "\0" + script).encode("utf-8")).hexdigest()[:16]
            sentinel = os.path.join(sent_dir, "macro_%s_%s.done" % (name, sha))
            if os.path.exists(sentinel):
                continue
            resp = kernel.dispatch({"jsonrpc": "2.0", "method": "macro.def",
                                  "params": {"client_id": "system.librarian",
                                             "data": {"name": name, "params": params,
                                                      "script": script, "scope": "universal"}},
                                  "id": "macroboot"}, TRUST_INTERNAL)
            if isinstance(resp, dict) and resp.get("error"):
                logger.warning("[macro] load failed name=%s: %s", name, resp["error"].get("message"))
                continue
            try:
                with open(sentinel, "w") as f:
                    f.write(sha)
            except Exception:
                pass
            logger.info("[macro] loaded name=%s sha=%s params=%s", name, sha, params or "-")
        except Exception as exc:
            logger.warning("[macro] load skipped for %s: %s", os.path.basename(path), exc)
