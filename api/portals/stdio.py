"""
Akasha stdio Portal — interactive REPL and headless single-shot mode.

Entry points:
  run_cli(gw)               — full interactive REPL
  run_single_shot(cmd, gw)  — headless command execution, returns JSON string

No lib.* imports. All cognitive work dispatched via gateway.dispatch().
"""

import sys
import os
import time
import json
import uuid
import getpass
import logging
from typing import List, Optional, Tuple

logger = logging.getLogger("Harmonia.Portal.Stdio")

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

from api.router import CommandRouter
from api.env_detector import env, Colors
from api.shell.renderer import (render, paged_render, print_help, print_concepts_list,
                                print_concept_help, print_command_detail, c,
                                extract_assoc_menu, extract_dream_menu, extract_lens_candidates)
from api.shell.input import InputBuffer, make_prompt


# ─── Gateway helpers ──────────────────────────────────────────────────────────

class _LocalGateway:
    """
    Wraps the shared gateway so every dispatch from THIS local stdio console is
    stamped with TRUST_LOCAL.  Trust is set here — by the server-side portal that
    physically owns the operator's terminal — never by anything the client sends.

    The local operator is gated by the OS process boundary, so a bare client_id
    (including the admin) is accepted locally without a signed token.  The same
    gateway instance serves the background network portal with the default
    TRUST_NETWORK, where a bare id would instead be rejected.
    """
    __slots__ = ("_gw",)

    def __init__(self, gw):
        self._gw = gw

    def dispatch(self, payload: dict, transport_trust: str = "local") -> dict:
        return self._gw.dispatch(payload, "local")

    def __getattr__(self, name):
        return getattr(self._gw, name)


def _dispatch(gw, method: str, data: dict, session_token: str = "") -> dict:
    return gw.dispatch({
        "jsonrpc": "2.0",
        "method": method,
        "params": {"session_token": session_token, "data": data},
        "id": "stdio",
    })


# ─── Auth / Genesis ───────────────────────────────────────────────────────────

def _auth_status(gw) -> dict:
    resp = gw.dispatch({
        "jsonrpc": "2.0", "method": "kernel.auth.status",
        "params": {}, "id": "auth_status",
    })
    return resp.get("result", {"initialized": False, "akasha_name": "AKASHA"})


def _genesis_rite(gw) -> Optional[Tuple[str, str]]:
    """First-boot ceremony. Returns (user_id, session_token) or None."""
    print(c(Colors.CYAN, "\n" + "=" * 52))
    print(c(Colors.CYAN,  " [ The Pact of Genesis ]"))
    print(c(Colors.CYAN,  "=" * 52 + "\n"))

    ak_name   = input("Name this system: ").strip() or "AKASHA"
    user_name = input("Your identity (Admin ID): ").strip()
    if not user_name:
        print(c(Colors.FAIL, "[!] Admin ID is required."))
        return None

    while True:
        p1 = env.secure_input("  Set passphrase: ")
        p2 = env.secure_input("  Confirm: ")
        if p1 and p1 == p2:
            break
        print(c(Colors.FAIL, "  [!] Passphrases do not match or are empty."))

    resp = gw.dispatch({
        "jsonrpc": "2.0", "method": "kernel.genesis_rite",
        "params": {"data": {
            "akasha_name": ak_name, "user_name": user_name, "passphrase": p1
        }},
        "id": "genesis",
    })

    if "error" in resp:
        print(c(Colors.FAIL, f"[!] Genesis failed: {resp['error']['message']}"))
        return None

    print()
    for line in resp["result"].get("ceremony", []):
        print(c(Colors.CYAN, f"  {line}"))
        time.sleep(0.35)
    print()
    return user_name, user_name, "admin"


def _auth_gate(gw, akasha_name: str) -> Optional[Tuple[str, str]]:
    """Login flow. Returns (user_id, session_token, role) or None."""
    print(c(Colors.CYAN, f"\n[ {akasha_name} ]\n"))

    for attempts in range(3, 0, -1):
        uid = input("  User ID: ").strip()
        if not uid:
            continue
        pwd = env.secure_input(f"  Passphrase [{attempts} left]: ")

        resp = gw.dispatch({
            "jsonrpc": "2.0", "method": "kernel.auth.verify",
            "params": {"data": {"user_id": uid, "passphrase": pwd}},
            "id": "auth",
        })

        if "error" not in resp:
            r = resp["result"]
            return r["user_id"], r["session_token"], r.get("role", "user")

        if attempts > 1:
            print(c(Colors.FAIL, "  [!] Access denied."))

    print(c(Colors.FAIL, "\n[!] System locked."))
    return None


# ─── Ontology / file loading (shell-side) ─────────────────────────────────────
#
# The shell is solely responsible for reading local files. It parses .ak lines
# into {method, params} step objects and submits them as a JCL batch job.
# The kernel never touches the filesystem; it only receives pre-parsed steps.
#
# Two tiers of ontology memory:
#   Innate  — lib/akasha/dna.py, loaded by the kernel at boot; clients can't touch it.
#   Acquired— ontology/*.ak files, read here (shell-side) and submitted as JCL jobs.

def _parse_ak_file(filepath: str) -> Tuple[List[dict], int]:
    """
    Read a .ak file and convert each command line into {method, params, cmd}.
    Returns (steps, skipped_count).
    File I/O is 100% shell-side; kernel never sees the filesystem.
    """
    steps: List[dict] = []
    skipped = 0
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for raw in f:
                line = raw.rstrip("\n").strip()
                if not line or line.startswith("#"):
                    continue
                payload = CommandRouter.build_rpc_request(line, "__parse__")
                if payload:
                    steps.append({
                        "method": payload["method"],
                        "params": payload["params"]["data"],
                        "cmd":    line,
                    })
                else:
                    skipped += 1
    except FileNotFoundError:
        raise
    return steps, skipped


def _submit_as_job(
    steps: List[dict],
    label: str,
    session_token: str,
    gw,
    fail_fast: bool = True,
) -> Optional[str]:
    """Submit pre-parsed steps to the kernel as a JCL batch job. Returns job_id."""
    if not steps:
        return None
    resp = gw.dispatch({
        "jsonrpc": "2.0",
        "method":  "job.submit",
        "params":  {
            "session_token": session_token,
            "data": {"steps": steps, "label": label, "fail_fast": fail_fast},
        },
        "id": "shell.ont_load",
    })
    if "error" in resp:
        err = resp["error"]
        msg = err.get("message", str(err)) if isinstance(err, dict) else str(err)
        raise RuntimeError(msg)
    return resp.get("result", {}).get("job_id")


_ONT_WRITE_METHODS = frozenset({
    "w", "write", "kernel.memory.write",
    "def", "define", "kernel.memory.define",
})

def _mark_universal(steps: List[dict]) -> None:
    """Tag write/define steps so the kernel places them in scope:sys:universal."""
    for step in steps:
        if step.get("method") in _ONT_WRITE_METHODS:
            step["params"]["scope"] = "universal"


def _autoload_ontology(session_token: str, gw) -> None:
    """Load all ontology .ak files at login if not already loaded (sentinel check)."""
    # Check if vocab ontology is already present via a known alias
    probe = gw.dispatch({
        "jsonrpc": "2.0", "method": "kernel.identity.alias.find",
        "params": {"session_token": session_token, "data": {"pattern": "word:en:love"}},
        "id": "ont.probe",
    })
    result = probe.get("result", {})
    if result.get("aliases"):
        return  # already loaded

    files = _get_ontology_files()
    if not files:
        return

    print(c(Colors.DIM, "  [ont] Loading acquired ontology…"))
    total_steps = 0
    loaded: List[Tuple[str, int]] = []
    errors: List[str] = []
    for fpath in files:
        rel = os.path.relpath(fpath, _project_root)
        try:
            steps, _ = _parse_ak_file(fpath)
            if steps:
                _mark_universal(steps)
                _submit_as_job(steps, f"ont:{os.path.basename(fpath)}", session_token, gw)
                total_steps += len(steps)
                loaded.append((rel, len(steps)))
        except Exception as e:
            errors.append(f"{rel}: {e}")

    if loaded:
        for rel, n in loaded:
            print(c(Colors.DIM, f"        {rel}  ({n} steps)"))
        print(c(Colors.DIM, f"  [ont] Ready — {total_steps} steps across {len(loaded)} files."))
    if errors:
        for err in errors:
            print(c(Colors.WARNING, f"  [ont] ⚠  {err}"))


def _print_collision_report(session_token: str, gw) -> None:
    """Print alias collision summary after ontology load. Only shown when overwrites exist."""
    resp = gw.dispatch({
        "jsonrpc": "2.0", "method": "onto.report",
        "params": {"session_token": session_token, "data": {"clear": True}},
        "id": "ont.collision_report",
    })
    result = resp.get("result", {})
    overwrites = result.get("overwrites", 0)
    skips      = result.get("leaf_skips", 0)
    if overwrites == 0 and skips == 0:
        return
    if overwrites > 0:
        print(c(Colors.WARNING, f"  [ont] ⚠  Collision report: {overwrites} overwrites, {skips} leaf skips"))
        for e in result.get("entries", []):
            if e["event"] == "overwrite":
                winner = e.get("winner", "")[:8]
                loser  = e.get("loser",  "")[:8]
                print(c(Colors.WARNING, f"        ⚠  overwrite '{e['alias']}'  {loser}→{winner}"))
    else:
        print(c(Colors.DIM, f"  [ont] {skips} leaf alias skips (first-registered wins — normal)"))


def _get_ontology_files() -> List[str]:
    ont_dir = os.path.join(_project_root, "ontology")
    if not os.path.exists(ont_dir):
        return []
    files = []
    for root, _, names in os.walk(ont_dir):
        for n in sorted(names):
            if n.endswith(".ak"):
                files.append(os.path.join(root, n))
    return files


def _get_ontology_csl_files() -> List[str]:
    ont_dir = os.path.join(_project_root, "ontology")
    if not os.path.exists(ont_dir):
        return []
    files = []
    for root, _, names in os.walk(ont_dir):
        for n in sorted(names):
            if n.endswith(".csl"):
                files.append(os.path.join(root, n))
    return files


def _autoload_ontology_csl(session_token: str, gw) -> None:
    """
    Queue all ontology .csl files as JCL jobs on first login.

    Each file becomes one job with a single csl.run step so that:
      • the login prompt is never blocked (async, Harmonia-scheduled)
      • csl.run failures are logged but don't abort sibling files (fail_fast=False)
      • a sentinel write+alias step on the last job prevents double-loading

    Sentinel: ont:csl:loaded — written by the last CSL JCL job, not by the shell.
    If the system shuts down mid-load the sentinel may be absent; next login
    will re-queue (idempotent — same content → same SHA-256 keys).
    """
    import hashlib as _hl

    csl_files = _get_ontology_csl_files()
    if not csl_files:
        return

    probe = gw.dispatch({
        "jsonrpc": "2.0", "method": "kernel.identity.alias.find",
        "params": {"session_token": session_token, "data": {"pattern": "ont:csl:loaded"}},
        "id": "ont.csl.probe",
    })
    if probe.get("result", {}).get("aliases"):
        return  # already loaded

    # Pre-compute sentinel key (sha256 of sentinel text, same as write handler)
    _SENT_TEXT  = "[ont:csl] Ontology CSL scripts loaded"
    _SENT_KEY   = _hl.sha256(_SENT_TEXT.encode()).hexdigest()
    _SENT_ALIAS = "ont:csl:loaded"

    print(c(Colors.DIM, "  [ont] Queuing CSL ontology scripts as JCL jobs…"))
    queued: List[str] = []
    errors: List[str] = []

    for idx, fpath in enumerate(csl_files):
        rel = os.path.relpath(fpath, _project_root)
        try:
            with open(fpath, "r", encoding="utf-8") as _f:
                source = _f.read()
            steps = [{"method": "csl.run", "params": {"script": source}}]

            # Sentinel appended to the very last job so it lands after all CSL ops
            if idx == len(csl_files) - 1:
                steps.append({"method": "write",
                               "params": {"text": _SENT_TEXT, "scope": "universal"}})
                steps.append({"method": "alias",
                               "params": {"id": _SENT_KEY, "name": _SENT_ALIAS}})

            job_id = _submit_as_job(
                steps,
                f"ont.csl:{os.path.basename(fpath)}",
                session_token,
                gw,
                fail_fast=False,   # CSL errors are recorded; sibling files still run
            )
            queued.append(job_id or rel)
        except Exception as exc:
            errors.append(f"{rel}: {exc}")

    if queued:
        print(c(Colors.DIM,
                f"  [ont] {len(queued)} CSL file{'s' if len(queued) > 1 else ''} "
                f"queued as JCL jobs — check status with  job.ls"))
    if errors:
        for err in errors:
            print(c(Colors.WARNING, f"  [ont] ⚠  {err}"))


# ─── Command history ─────────────────────────────────────────────────────────

_HISTORY_FILE = os.path.expanduser("~/.akasha_history")
_readline_ok  = False

def _setup_readline() -> bool:
    """Enable readline if available: persistent history file + arrow-key navigation."""
    global _readline_ok
    try:
        import readline as _rl
        try:
            _rl.read_history_file(_HISTORY_FILE)
        except FileNotFoundError:
            pass
        _rl.set_history_length(2000)
        import atexit as _ae
        _ae.register(_rl.write_history_file, _HISTORY_FILE)
        _readline_ok = True
    except ImportError:
        pass
    return _readline_ok

def _rl_add(cmd: str) -> None:
    if _readline_ok:
        try:
            import readline as _rl
            _rl.add_history(cmd)
        except Exception:
            pass

def _expand_history(cmd: str, hist: List[str]) -> Optional[str]:
    """Expand Unix-style history references.  Returns expanded command, or None on error."""
    if cmd == "!!":
        if not hist:
            print(c(Colors.FAIL, "  [!] No previous command."))
            return None
        return hist[-1]

    if cmd.startswith("!") and len(cmd) > 1:
        ref = cmd[1:]

        # !n or !-n (numeric)
        if ref.lstrip("-").isdigit():
            n = int(ref)
            if n == 0:
                print(c(Colors.FAIL, "  [!] History index starts at 1."))
                return None
            idx = (len(hist) + n) if n < 0 else (n - 1)
            if idx < 0 or idx >= len(hist):
                print(c(Colors.FAIL,
                    f"  [!] !{ref}: out of range (history has {len(hist)} entries)."))
                return None
            return hist[idx]

        # !prefix — last command starting with prefix
        for entry in reversed(hist):
            if entry.startswith(ref):
                return entry
        print(c(Colors.FAIL, f"  [!] !{ref}: no match found."))
        return None

    return cmd  # not a history reference

def _print_history(hist: List[str], limit: int = 50) -> None:
    if not hist:
        print(c(Colors.DIM, "\n  (no history)\n"))
        return
    start = max(0, len(hist) - limit)
    print()
    for i, entry in enumerate(hist[start:], start=start + 1):
        print(f"  {c(Colors.DIM, str(i).rjust(5))}  {entry}")
    print()


# ─── Service control ──────────────────────────────────────────────────────────

def _handle_svc(args_str: str, user_role: str = "user", su_context: dict = None):
    try:
        from api.service_manager import ServiceManager
        svc   = ServiceManager.get_instance()
        parts = args_str.split()
        sub   = parts[0] if parts else ""

        is_admin = (user_role == "admin") or (
            su_context and su_context.get("active") and
            su_context.get("target") in ("root", None)
        )

        if sub == "ls":
            from api.shell.renderer import render_svc_list
            session_counts = None
            try:
                import api.gateway as _gw
                _mgr = getattr(getattr(_gw.gateway, "kernel_client", None), "manager", None)
                if _mgr:
                    session_counts = _mgr.count_sessions()
            except Exception:
                pass
            render_svc_list(svc.list_services(), session_counts)

        elif sub == "start":
            if not is_admin:
                print(c(Colors.FAIL, "  [!] Permission denied: svc start requires admin."))
                return
            if len(parts) < 2:
                print(c(Colors.FAIL, "  Usage: svc start <name>"))
                return
            result = svc.start_by_blueprint(parts[1])
            if "error" in result:
                print(c(Colors.FAIL, f"  [!] {result['error']}"))
            else:
                print(c(Colors.GREEN, f"  ✓ {result.get('service', parts[1])} {result.get('status', 'started')}"))

        elif sub == "stop":
            if not is_admin:
                print(c(Colors.FAIL, "  [!] Permission denied: svc stop requires admin."))
                return
            if len(parts) < 2:
                print(c(Colors.FAIL, "  Usage: svc stop <name>"))
                return
            result = svc.stop_service(parts[1])
            if "error" in result:
                print(c(Colors.FAIL, f"  [!] {result['error']}"))
            else:
                print(c(Colors.GREEN, f"  ✓ {result['service']} {result['status']}"))

        elif sub == "restart":
            if not is_admin:
                print(c(Colors.FAIL, "  [!] Permission denied: svc restart requires admin."))
                return
            if len(parts) < 2:
                print(c(Colors.FAIL, "  Usage: svc restart <name>"))
                return
            print(c(Colors.DIM, f"  Restarting {parts[1]}…"))
            result = svc.restart_service(parts[1])
            if "error" in result:
                print(c(Colors.FAIL, f"  [!] {result['error']}"))
            else:
                print(c(Colors.GREEN, f"  ✓ {result.get('service', parts[1])} {result.get('status', 'restarted')}"))

        else:
            print(c(Colors.DIM, "  Usage: svc ls  |  svc start <n>  |  svc stop <n>  |  svc restart <n>"))
            if not is_admin:
                print(c(Colors.DIM, "  (start/stop/restart require admin)"))
    except ImportError:
        print(c(Colors.WARNING, "[!] ServiceManager not available."))


# ─── REPL ─────────────────────────────────────────────────────────────────────

def run_cli(gw):
    """
    Primary interactive REPL.
    Receives a live AkashaGateway; makes no direct lib.* calls.
    """
    # The interactive console is the trusted local operator: stamp every dispatch
    # (including boot ontology autoload) with TRUST_LOCAL.
    gw = _LocalGateway(gw)
    env.print_environment_info()
    print()

    # Kernel liveness
    ping = gw.dispatch({"jsonrpc": "2.0", "method": "sys.ping", "params": {}, "id": "boot"})
    if "error" in ping:
        print(c(Colors.FAIL, f"[!] Kernel unreachable: {ping['error']['message']}"))
        sys.exit(1)

    # Auth
    status = _auth_status(gw)
    auth   = (_genesis_rite(gw) if not status.get("initialized")
              else _auth_gate(gw, status.get("akasha_name", "AKASHA")))

    if not auth:
        sys.exit(1)

    user_id, session_token, user_role = auth
    akasha_name = _auth_status(gw).get("akasha_name", "AKASHA")
    print(c(Colors.GREEN, f"[ {akasha_name} online. Welcome, {user_id}. ]"))
    print(c(Colors.DIM,   "Type 'help' for commands. 'exit' to quit.\n"))

    # Ontology is loaded by the kernel's _boot_load_ontology background thread.
    # _autoload_ontology / _autoload_ontology_csl are legacy and must not run here —
    # they walk all of ontology/ unconditionally, overriding the kernel's base-only policy.

    _setup_readline()

    buf         = InputBuffer()
    cmd_queue:  List[str] = []
    cmd_history: List[str] = []
    su_context:   dict  = {"active": False, "target": None}
    nav_mode:     dict  = {"active": False, "name": None}
    _assoc_state: dict  = {"focal_key": None, "focal_alias": None, "menu": {}}
    _dream_state: dict  = {"focal_key": None, "focal_alias": None, "menu": {}}
    _lens_state:  dict  = {"src": "", "candidates": {}}

    # Commands that enter a named navigation mode
    _NAV_ENTER = {
        "dive": "dive", "look": "dive", "d": "dive",
        "explore": "explore", "exp": "explore",
        "assoc": "assoc", "associate": "assoc",
        "lens": "lens",
    }

    while True:
        try:
            prompt = make_prompt(user_id, buf.in_multiline, su_context, nav_mode)

            if cmd_queue:
                line = cmd_queue.pop(0)
                if not buf.in_multiline and line.strip().startswith("#"):
                    continue
                time.sleep(0.03)
                print(f"{prompt}{line}")
            else:
                line = input(prompt)

            if not buf.push(line):
                continue   # still inside a multiline block

            full_cmd = buf.flush()
            if not full_cmd or full_cmd.startswith("#"):
                continue

            low = full_cmd.lower()

            if low in ("exit", "quit", "bye"):
                if nav_mode["active"]:
                    name = nav_mode["name"]
                    nav_mode["active"] = False
                    nav_mode["name"]   = None
                    if name == "assoc":
                        _assoc_state.update({"focal_key": None, "focal_alias": None, "menu": {}})
                    elif name == "dream":
                        _dream_state.update({"focal_key": None, "focal_alias": None, "menu": {}})
                    elif name == "lens":
                        _lens_state.update({"src": "", "candidates": {}})
                    print(c(Colors.DIM, f"  ↩ Leaving {name} mode."))
                    continue
                print(c(Colors.DIM, "Suspending consciousness… Goodbye."))
                break

            # ── History expansion (!! / !n / !-n / !prefix) ───────────
            if full_cmd.startswith("!"):
                expanded = _expand_history(full_cmd, cmd_history)
                if expanded is None:
                    continue
                if expanded != full_cmd:
                    print(c(Colors.DIM, f"  → {expanded}"))
                full_cmd = expanded
                low = full_cmd.lower()

            # ── history command ───────────────────────────────────────
            if low == "history" or low.startswith("history "):
                _parts_h = full_cmd.split()
                _limit_h = 50
                if len(_parts_h) > 1 and _parts_h[1].isdigit():
                    _limit_h = int(_parts_h[1])
                _print_history(cmd_history, _limit_h)
                continue

            # ── Record to history (before dispatch) ───────────────────
            cmd_history.append(full_cmd)
            _rl_add(full_cmd)

            # ── Assoc mode: numeric candidate selection ────────────────
            if (nav_mode.get("name") == "assoc"
                    and _assoc_state["menu"]
                    and full_cmd.strip().isdigit()):
                sel   = int(full_cmd.strip())
                entry = _assoc_state["menu"].get(sel)
                if not entry:
                    hi = max(_assoc_state["menu"].keys())
                    print(c(Colors.FAIL, f"  [!] No candidate {sel} (valid: 1–{hi})."))
                    continue

                focal_ref = entry["focal_alias"] or entry["focal_key"]
                dst_ref   = entry["dst_alias"]   or entry["dst_key"]
                rel       = entry["rel"]
                if " " in focal_ref:
                    focal_ref = f'"{focal_ref}"'
                if " " in dst_ref:
                    dst_ref = f'"{dst_ref}"'
                ln_cmd = f"ln {focal_ref} {dst_ref} {rel}"
                print(c(Colors.DIM, f"  → {ln_cmd}"))
                ln_payload = CommandRouter.build_rpc_request(ln_cmd, session_token)
                if ln_payload:
                    ln_resp = gw.dispatch(ln_payload)
                    paged_render(ln_resp)
                    if "error" not in ln_resp:
                        # Auto-refresh assoc to show updated voids
                        refresh_ref = entry["focal_alias"] or entry["focal_key"]
                        if " " in refresh_ref:
                            refresh_ref = f'"{refresh_ref}"'
                        refresh_payload = CommandRouter.build_rpc_request(
                            f"assoc {refresh_ref}", session_token
                        )
                        if refresh_payload:
                            refresh_resp = gw.dispatch(refresh_payload)
                            paged_render(refresh_resp)
                            if "error" not in refresh_resp:
                                _assoc_state.update(
                                    extract_assoc_menu(refresh_resp.get("result", {}))
                                )
                continue

            # ── Dream mode: numeric proposal approval ──────────────────
            if (nav_mode.get("name") == "dream"
                    and _dream_state["menu"]
                    and full_cmd.strip().isdigit()):
                sel   = int(full_cmd.strip())
                entry = _dream_state["menu"].get(sel)
                if not entry:
                    hi = max(_dream_state["menu"].keys())
                    print(c(Colors.FAIL, f"  [!] No proposal {sel} (valid: 1–{hi})."))
                    continue

                focal_ref = entry["focal_alias"] or entry["focal_key"]
                dst_ref   = entry["dst_alias"]   or entry["dst_key"]
                rel       = entry["rel"]
                if " " in focal_ref:
                    focal_ref = f'"{focal_ref}"'
                if " " in dst_ref:
                    dst_ref = f'"{dst_ref}"'
                ln_cmd = f"ln {focal_ref} {dst_ref} {rel}"
                print(c(Colors.DIM, f"  → {ln_cmd}"))
                ln_payload = CommandRouter.build_rpc_request(ln_cmd, session_token)
                if ln_payload:
                    ln_resp = gw.dispatch(ln_payload)
                    paged_render(ln_resp)
                    if "error" not in ln_resp:
                        # Auto-refresh dream to show remaining proposals
                        refresh_ref = entry["focal_alias"] or entry["focal_key"]
                        if " " in refresh_ref:
                            refresh_ref = f'"{refresh_ref}"'
                        refresh_payload = CommandRouter.build_rpc_request(
                            f"dream {refresh_ref}", session_token
                        )
                        if refresh_payload:
                            refresh_resp = gw.dispatch(refresh_payload)
                            paged_render(refresh_resp)
                            if "error" not in refresh_resp:
                                _dream_state.update(
                                    extract_dream_menu(refresh_resp.get("result", {}))
                                )
                continue

            # ── Lens mode: numeric candidate selection ─────────────────
            if (nav_mode.get("name") == "lens"
                    and _lens_state["candidates"]):
                stripped = full_cmd.strip()
                _parts_l = stripped.split(None, 1)
                if _parts_l and _parts_l[0].isdigit():
                    sel    = int(_parts_l[0])
                    cand   = _lens_state["candidates"].get(sel)
                    if not cand:
                        hi = max(_lens_state["candidates"].keys())
                        print(c(Colors.FAIL, f"  [!] No candidate {sel} (valid: 1–{hi})."))
                        continue
                    # Parse optional "N name" or "N into=name" syntax
                    into_val = ""
                    if len(_parts_l) > 1:
                        rest = _parts_l[1].strip()
                        if rest.startswith("into="):
                            into_val = rest[5:].strip().strip('"\'')
                        else:
                            into_val = rest.strip().strip('"\'')
                    cast_cmd = f"lens.cast signpost={sel}"
                    if into_val:
                        cast_cmd += f" into={into_val}"
                    print(c(Colors.DIM, f"  → {cast_cmd}"))
                    cast_payload = CommandRouter.build_rpc_request(cast_cmd, session_token)
                    if cast_payload:
                        cast_resp = gw.dispatch(cast_payload)
                        paged_render(cast_resp)
                    continue

            # ── Local directives ──────────────────────────────────────
            if low == "help" or low.startswith("help "):
                arg = full_cmd[4:].strip()
                if not arg:
                    print_help(CommandRouter.get_core_specs(),
                               CommandRouter.get_concept_info())
                elif arg == "-c":
                    print_concepts_list(CommandRouter.get_concept_info())
                elif arg.startswith("-c "):
                    group = arg[3:].strip()
                    print_concept_help(group,
                                       CommandRouter.get_concept_specs(group),
                                       CommandRouter.list_concepts())
                else:
                    spec = CommandRouter.COMMAND_SPECS.get(arg)
                    group = CommandRouter._get_concept_group(arg)
                    if group:
                        related = [k for k in CommandRouter.COMMAND_SPECS
                                   if k != arg and CommandRouter._get_concept_group(k) == group]
                    else:
                        pfx = arg.split(".")[0]
                        related = [k for k in CommandRouter.COMMAND_SPECS
                                   if k != arg and k.startswith(pfx + ".")
                                   and not CommandRouter._get_concept_group(k)]
                    print_command_detail(arg, spec, group, related)
                continue

            if low == "ont.load" or low.startswith("ont.load "):
                ont_arg = full_cmd[len("ont.load"):].strip()
                ak_files  = _get_ontology_files()
                csl_files = _get_ontology_csl_files()
                all_files = ak_files + csl_files
                if not all_files:
                    print(c(Colors.DIM, "[-] No ontology files found."))
                    continue
                targets = []
                if ont_arg:
                    matches = [f for f in all_files if ont_arg in os.path.relpath(f, _project_root)]
                    if not matches:
                        print(c(Colors.FAIL, f"  [!] No ontology file matching '{ont_arg}'"))
                        continue
                    elif len(matches) == 1:
                        targets = matches
                    else:
                        print(c(Colors.CYAN, f"\n  Matches for '{ont_arg}':"))
                        for i, f in enumerate(matches):
                            print(f"    {i}. {os.path.relpath(f, _project_root)}")
                        ans = input("Select number (or 'all', Enter to cancel): ").strip()
                        if ans.isdigit() and 0 <= int(ans) < len(matches):
                            targets = [matches[int(ans)]]
                        elif ans.lower() == "all":
                            targets = matches
                else:
                    print(c(Colors.CYAN, "\n[ Acquired Ontologies ]"))
                    for i, f in enumerate(all_files):
                        tag = ".csl" if f.endswith(".csl") else ".ak "
                        print(f"  {i}. [{tag}] {os.path.relpath(f, _project_root)}")
                    ans = input("Select number (or 'all', Enter to cancel): ").strip()
                    if ans.isdigit() and 0 <= int(ans) < len(all_files):
                        targets = [all_files[int(ans)]]
                    elif ans.lower() == "all":
                        targets = all_files
                for fpath in targets:
                    rel = os.path.relpath(fpath, _project_root)
                    try:
                        if fpath.endswith(".csl"):
                            with open(fpath, "r", encoding="utf-8") as _f:
                                _src = _f.read()
                            _resp = gw.dispatch({
                                "jsonrpc": "2.0",
                                "method": "csl.run",
                                "params": {
                                    "session_token": session_token,
                                    "data": {"script": _src},
                                },
                                "id": str(uuid.uuid4()),
                            })
                            if "error" in _resp:
                                _msg = _resp["error"]
                                _msg = _msg.get("message", str(_msg)) if isinstance(_msg, dict) else str(_msg)
                                print(c(Colors.FAIL, f"  [!] {rel}: {_msg}"))
                            else:
                                _ops = len(_resp.get("result", {}).get("results", []))
                                print(c(Colors.GREEN, f"  [+] {rel}: {_ops} ops executed"))
                        else:
                            steps, skipped = _parse_ak_file(fpath)
                            if not steps:
                                print(c(Colors.DIM, f"  [-] {os.path.basename(fpath)}: nothing to load"))
                                continue
                            job_id = _submit_as_job(steps, rel, session_token, gw)
                            print(c(Colors.GREEN,
                                    f"  [+] {rel}: {len(steps)} steps queued → {job_id}"
                                    + (f" ({skipped} skipped)" if skipped else "")))
                            print(c(Colors.DIM, f"      job.st {job_id}  to check status"))
                    except FileNotFoundError:
                        print(c(Colors.FAIL, f"  [!] File not found: {fpath}"))
                    except RuntimeError as e:
                        print(c(Colors.FAIL, f"  [!] Submit failed: {e}"))
                continue

            _csl_stripped = full_cmd.strip()
            if _csl_stripped.lower() == "csl" or _csl_stripped.lower().startswith("csl "):
                _csl_arg = _csl_stripped[3:].strip()  # everything after "csl"

                class _GwSessionProxy:
                    """Thin wrapper so the CSL runtime can dispatch via the gateway."""
                    def __init__(self, gateway, token, uid):
                        self.token     = token
                        self.client_id = uid
                        self._gw       = gateway

                    def dispatch(self, payload):
                        p = payload.setdefault("params", {})
                        if not p.get("session_token"):
                            p["session_token"] = self.token
                        return self._gw.dispatch(payload)

                if not _csl_arg:
                    # No argument → launch the interactive REPL
                    try:
                        from lib.akasha.csl.repl import run_repl
                        run_repl(_GwSessionProxy(gw, session_token, user_id))
                    except ImportError as exc:
                        print(c(Colors.FAIL, f"[!] CSL runtime not available: {exc}"))
                else:
                    # Argument → run a local .csl file
                    _csl_path = _csl_arg
                    if not os.path.isabs(_csl_path):
                        _csl_path = os.path.join(os.getcwd(), _csl_path)
                    if not os.path.exists(_csl_path):
                        print(c(Colors.FAIL, f"[!] File not found: {_csl_arg}"))
                    else:
                        try:
                            with open(_csl_path, "r", encoding="utf-8") as _f:
                                _csl_source = _f.read()
                            _resp = gw.dispatch({
                                "jsonrpc": "2.0",
                                "method":  "csl.run",
                                "params":  {
                                    "session_token": session_token,
                                    "data": {"script": _csl_source},
                                },
                                "id": str(uuid.uuid4()),
                            })
                            paged_render(_resp)
                        except Exception as exc:
                            print(c(Colors.FAIL, f"[!] CSL file error: {exc}"))
                continue



            if full_cmd.startswith("run "):
                path = full_cmd.split(" ", 1)[1].strip()
                if not os.path.exists(path):
                    print(c(Colors.FAIL, f"[!] File not found: {path}"))
                    continue
                try:
                    steps, skipped = _parse_ak_file(path)
                    if not steps:
                        print(c(Colors.DIM, f"[-] {path}: no executable steps found"))
                        continue
                    label = os.path.basename(path)
                    job_id = _submit_as_job(steps, label, session_token, gw)
                    print(c(Colors.GREEN,
                            f"[+] {label}: {len(steps)} steps → job {job_id}"
                            + (f" ({skipped} skipped)" if skipped else "")))
                    print(c(Colors.DIM, f"    job.st {job_id}  to check status"))
                except RuntimeError as e:
                    print(c(Colors.FAIL, f"[!] Submit failed: {e}"))
                continue

            if full_cmd.startswith("svc "):
                _handle_svc(full_cmd[4:].strip(), user_role, su_context)
                continue

            # ── passwd — self-service passphrase change ──────────────────
            if full_cmd.strip().lower() == "passwd":
                try:
                    cur  = getpass.getpass(c(Colors.WARNING, "Current passphrase: "))
                    pw1  = getpass.getpass(c(Colors.WARNING, "New passphrase: "))
                    pw2  = getpass.getpass(c(Colors.WARNING, "Confirm new passphrase: "))
                except (KeyboardInterrupt, EOFError):
                    print()
                    continue
                if pw1 != pw2:
                    print(c(Colors.FAIL, "  [!] Passphrases do not match."))
                    continue
                if not pw1:
                    print(c(Colors.FAIL, "  [!] Passphrase cannot be empty."))
                    continue
                import hashlib as _hl
                passwd_payload = {
                    "jsonrpc": "2.0",
                    "method": "sys.passwd",
                    "params": {
                        "session_token": session_token,
                        "data": {
                            "current_hash": _hl.sha256(cur.encode()).hexdigest(),
                            "new_hash":     _hl.sha256(pw1.encode()).hexdigest(),
                        },
                    },
                    "id": str(uuid.uuid4()),
                }
                render(gw.dispatch(passwd_payload))
                continue

            # ── user.add / user.passwd — admin passphrase injection ──────
            _parts = full_cmd.split()
            if _parts and _parts[0].lower() in ("user.add", "user.passwd"):
                payload = CommandRouter.build_rpc_request(full_cmd, session_token)
                if payload:
                    target_id = payload["params"]["data"].get("client_id", "")
                    try:
                        pw1 = getpass.getpass(c(Colors.WARNING, "New passphrase: "))
                        pw2 = getpass.getpass(c(Colors.WARNING, "Confirm passphrase: "))
                    except (KeyboardInterrupt, EOFError):
                        print()
                        continue
                    if pw1 != pw2:
                        print(c(Colors.FAIL, "  [!] Passphrases do not match."))
                        continue
                    if not pw1:
                        print(c(Colors.FAIL, "  [!] Passphrase cannot be empty."))
                        continue
                    import hashlib as _hl
                    phash = _hl.sha256(pw1.encode()).hexdigest()
                    payload["params"]["data"]["passphrase_hash"] = phash
                    resp = gw.dispatch(payload)
                    render(resp)
                    continue

            # ── su — privileged identity switch (admin only, hidden) ──
            if full_cmd == "su" or full_cmd.lower().startswith("su "):
                parts = full_cmd.split()
                target = parts[1] if len(parts) > 1 else "exit"
                pw = ""
                if target != "exit":
                    try:
                        pw = getpass.getpass(c(Colors.WARNING, "Password: "))
                    except (KeyboardInterrupt, EOFError):
                        print()
                        continue
                su_payload = {
                    "jsonrpc": "2.0",
                    "method": "sys.su",
                    "params": {
                        "session_token": session_token,
                        "data": {"target": target, "passphrase": pw},
                    },
                    "id": str(uuid.uuid4()),
                }
                resp = gw.dispatch(su_payload)
                if "error" in resp:
                    render(resp)
                else:
                    res = resp.get("result", {})
                    if res.get("status") == "su_active":
                        su_context["active"] = True
                        su_context["target"] = res["target"]
                        if res["target"] == "root":
                            print(c(Colors.FAIL,
                                    "\n  [SU] Root mode active — all scope restrictions lifted."))
                        elif res["target"] == "librarian":
                            print(c(Colors.WARNING,
                                    "\n  [SU] Librarian mode active — nucleus write and ontology operations enabled."))
                        else:
                            print(c(Colors.WARNING,
                                    f"\n  [SU] Impersonating: {res['target']}"))
                    else:
                        su_context["active"] = False
                        su_context["target"] = None
                        print(c(Colors.DIM, "\n  [SU] Returned to normal mode."))
                continue

            # ── Output redirection (shell-side: "> file") ────────────
            # Responsibility: shell captures output and writes to local file.
            # Remote CLI does the same on the remote machine's filesystem.
            redirect_path = None
            dispatch_cmd  = full_cmd
            if " > " in full_cmd:
                dispatch_cmd, redirect_path = full_cmd.rsplit(" > ", 1)
                redirect_path = redirect_path.strip()
                dispatch_cmd  = dispatch_cmd.strip()

            # ── Kernel dispatch ───────────────────────────────────────
            payload = CommandRouter.build_rpc_request(dispatch_cmd, session_token)
            if payload is None:
                print(c(Colors.FAIL,
                        f"[!] Unknown command: '{dispatch_cmd.split()[0]}'"
                        "  (type 'help')"))
                continue

            resp = gw.dispatch(payload)

            # Track navigation mode based on the dispatched command
            _nav_cmd = dispatch_cmd.split()[0].lower() if dispatch_cmd else ""
            _entered = _NAV_ENTER.get(_nav_cmd)
            if _entered and "error" not in resp:
                if nav_mode.get("name") != _entered:
                    nav_mode["active"] = True
                    nav_mode["name"]   = _entered

            # Extract assoc candidate menu for numeric selection
            if _nav_cmd in ("assoc", "associate") and "error" not in resp:
                _assoc_state.update(extract_assoc_menu(resp.get("result", {})))

            # Extract dream proposal menu for numeric approval
            if _nav_cmd == "dream" and "error" not in resp:
                _dream_state.update(extract_dream_menu(resp.get("result", {})))

            # Extract lens scan candidates for numeric selection
            if _nav_cmd == "lens" and "error" not in resp:
                _lens_state.update(extract_lens_candidates(resp.get("result", {})))

            if redirect_path:
                try:
                    with open(redirect_path, "w", encoding="utf-8") as rf:
                        json.dump(resp.get("result"), rf, ensure_ascii=False, indent=2)
                    print(c(Colors.DIM, f"  → written to {redirect_path}"))
                except OSError as e:
                    print(c(Colors.FAIL, f"[!] Redirect failed: {e}"))
                    render(resp)
            else:
                paged_render(resp)

        except (KeyboardInterrupt, EOFError):
            print(c(Colors.DIM, "\n[*] Emergency disconnect."))
            break
        except Exception as exc:
            logger.exception("[Stdio] Unhandled exception")
            print(c(Colors.FAIL, f"[!] Shell exception: {exc}"))


# ─── Headless ─────────────────────────────────────────────────────────────────

def run_single_shot(command: str, gw) -> str:
    """Executes one command non-interactively and returns raw JSON."""
    # Headless single-shot is the local operator (`python akasha.py <cmd>`).
    gw = _LocalGateway(gw)
    status = _auth_status(gw)
    if not status.get("initialized"):
        return json.dumps({"error": "System not initialized. Run interactively first."})

    payload = CommandRouter.build_rpc_request(command, "admin")
    if payload is None:
        return json.dumps({"error": f"Unknown command: '{command}'"})

    resp = gw.dispatch(payload)
    out  = resp.get("result", resp.get("error"))
    return json.dumps(out, ensure_ascii=False)
