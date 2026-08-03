"""
Supervisor — the backend's one management plane for long-lived work.

Akasha runs two kinds of long-lived work:
  • jobs     — in-process work units (the ontology load, JCL steps, WriteQueue work)
  • services — OS processes (the web portal, cosmos, note, the Cell daemon itself)

Historically these were managed by three disjoint mechanisms: the volatile in-memory
ServiceManager (api/service_manager.py), ad-hoc pid files (web-portal.pid / cell.pid),
and the JCL worker. The Supervisor consolidates them into ONE persistent registry with
ONE lifecycle vocabulary. Both categories mount onto it as uniform *managed units*.

Design: docs/for-llm/transport-daemon-units-spec.md.

Placement & invariants:
  • Backend component (lib/harmonia/) — Harmonia's OS-process arm; the JCL worker is its
    in-process arm. Management is a backend responsibility, not the shell's.
  • Persistence is a FILESYSTEM run-dir (data/central/run/<id>.json [+ <id>.pid]), never the
    nucleus — process state is operational, not semantic. Same crash-stop durability model as
    the ontology sentinels: a SIGKILL leaves a recoverable descriptor to reconcile on next boot.
  • No lock on the write path and no second nucleus writer — the Supervisor only touches the
    run-dir. Graph writes still flow through the one WriteQueue.
  • The run-dir is written by ONE process at a time in practice (the Cell daemon that hosts the
    Supervisor); every write is atomic (temp + os.replace) so a concurrent reader never sees a
    torn descriptor. Any process may READ the run-dir (cross-process `svc ls`).

Stdlib only.

P1 — respawn from a persisted recipe (this module's spawn-recipe layer):
  A service descriptor may carry a `spec` = a SERIALIZABLE, re-executable spawn recipe
  (substrate/argv/cwd/env_add/…), so ANY Supervisor-hosting process can (re)start the unit
  without the original process's in-memory closure. This is what makes cross-process restart,
  boot-time policy respawn, and retiring the volatile ServiceManager possible. Design premise:
  docs/for-llm/supervisor-deferred-premises.md.

Hardened control path (経路の厳格化 — no hole even though local shell start is trusted today):
  A recipe is an argv the Supervisor will EXECUTE, so respawn is gated on every layer, cheapest
  first, and the gate is built to TIGHTEN as the roadmap's security key lands:
    1. perms   — the run-dir + descriptor must be owner-only (0700/0600, our uid); a
                 group/other-writable descriptor is refused, so a tampered recipe can't be exec'd.
    2. shape   — argv[0] must be THIS interpreter and argv[1:3] == ['-m', <allow-listed module>];
                 respawn can only ever launch Akasha's own service modules, never an arbitrary cmd.
    3. env     — env_add is a NON-SECRET operational allow-list; anything credential-shaped is
                 refused (secrets are INHERITED from the daemon's env at respawn, never stored —
                 the run-dir is world-adjacent machinery, not the 0600 nucleus vault).
    4. signature — if a supervisor key is available (AKASHA_SECRET, or a 0600 key file), the recipe
                 MUST carry a valid HMAC written by the process that had the key. No key today →
                 the OS boundary (layer 1) is the gate (the deliberate local-trust posture). Set a
                 key → only the keyed daemon can mint a respawnable recipe; interactive shells and
                 remote admins can REQUEST a restart but cannot forge one. AKASHA_SUPERVISOR_STRICT=1
                 refuses any unsigned recipe outright (enterprise: mandatory-sign).
"""
import hashlib
import hmac
import json
import logging
import os
import signal
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional, Callable, Tuple

logger = logging.getLogger("Harmonia.Supervisor")

# Unit kinds
KIND_SERVICE = "service"
KIND_JOB = "job"

# Restart policies (services)
RESTART_NEVER = "never"
RESTART_ON_FAILURE = "on-failure"
RESTART_ALWAYS = "always"

# Substrates — how a unit runs, hence how it is (re)started (premises doc P2)
SUBSTRATE_PROCESS = "process"        # OS process: fully reconstructable from argv/env/cwd
SUBSTRATE_THREAD = "thread"          # host-bound: only its owning interpreter can restart it

# Trust a transport STAMPS (premises doc P5; server-set, never client-supplied)
TRUST_LOCAL = "local"
TRUST_NETWORK = "network"

# ── respawn gate policy (path hardening) ────────────────────────────────────────
# argv the Supervisor will exec is bounded to Akasha's own service launchers. A recipe can
# only ever `python -m <module>` one of these — never an arbitrary binary or shell string.
_ALLOWED_SPAWN_MODULES = frozenset({
    "api.portals.web_worker",         # the uvicorn serve-only web portal
})
_ALLOWED_MODULE_PREFIXES = ("services.",)   # bundled app services (cosmos, note, …)

# env_add carries NON-SECRET operational keys only. Anything credential-shaped is refused;
# real secrets are inherited from the daemon's own environment at respawn (never serialized).
_ALLOWED_ENV_KEYS = frozenset({
    "PYTHONUNBUFFERED", "AKASHA_SERVE_ONLY", "AKASHA_NO_AUTOLEARN",
    "AKASHA_BACKEND", "AKASHA_HOST", "AKASHA_DATA_DIR", "AKASHA_SERIES",
    # R5: the daemon's launch argv (JSON of --server/--host/--port/--portal), so a health-tick
    # respawn keeps the portal's self-watchdog able to spawn an identical daemon. Non-secret
    # operational data; omitting it made build_process_spec raise → recipe stored spec=None →
    # the health tick could never respawn the portal (respawnable=False, silent continue).
    "AKASHA_DAEMON_ARGV",
})
_SECRET_HINTS = ("SECRET", "TOKEN", "PASSWORD", "PASSPHRASE", "PRIVATE",
                 "CRED", "APIKEY", "API_KEY", "SIGNING")


class SupervisorError(Exception):
    """A respawn was refused (recipe missing, gate failed) or a spawn failed."""


# ── run-dir paths ────────────────────────────────────────────────────────────────

def run_dir(base_dir: str) -> str:
    return os.path.join(base_dir, "central", "run")


def _unit_path(base_dir: str, unit_id: str) -> str:
    return os.path.join(run_dir(base_dir), _safe(unit_id) + ".json")


def _pid_path(base_dir: str, unit_id: str) -> str:
    return os.path.join(run_dir(base_dir), _safe(unit_id) + ".pid")


def _safe(unit_id: str) -> str:
    """Filesystem-safe file stem for a unit id ('svc:web-portal' → 'svc__web-portal')."""
    return unit_id.replace(os.sep, "_").replace(":", "__")


def _pid_alive(pid: Optional[int]) -> bool:
    if not pid:
        return False
    try:
        os.kill(pid, 0)                        # signal 0 = liveness probe, no effect
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True                            # exists but owned by another uid
    except OSError:
        return False


# ── respawn recipe: build · sign · authorize · execute (P1 + path hardening) ────

def _supervisor_key(base_dir: str) -> Optional[bytes]:
    """The key used to sign/verify respawn recipes, or None (→ perms are the sole gate).

    Env `AKASHA_SECRET` wins (same key the auth layer uses); else an optional 0600 key file
    (`<base>/central/.supervisor_key`) — the drop-in point for the roadmap's security key. A
    key file readable by group/other is IGNORED (a shared key is no key). None ⇒ local-trust:
    the OS boundary + the argv/env allow-list are the gate, which is the intended posture until
    the key lands."""
    env = os.environ.get("AKASHA_SECRET", "").strip()
    if env:
        return env.encode("utf-8")
    kp = os.path.join(base_dir, "central", ".supervisor_key")
    try:
        st = os.stat(kp)
        if st.st_mode & 0o077:                 # group/other-accessible → refuse to trust it
            logger.warning("[Supervisor] ignoring %s: not 0600 (group/other-accessible).", kp)
            return None
        with open(kp, "rb") as fh:
            data = fh.read().strip()
        return data or None
    except OSError:
        return None


def _strict_signing() -> bool:
    """Enterprise lever: refuse any unsigned recipe even when no key is otherwise required."""
    return os.environ.get("AKASHA_SUPERVISOR_STRICT", "").strip().lower() in ("1", "true", "yes")


def _canonical_recipe(spec: Dict[str, Any]) -> bytes:
    """Deterministic bytes over the security-relevant recipe fields (never the sig itself)."""
    core = {k: spec.get(k) for k in
            ("substrate", "argv", "cwd", "env_add", "env_inherit", "new_session")}
    return json.dumps(core, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _sign_recipe(spec: Dict[str, Any], key: bytes) -> str:
    return hmac.new(key, _canonical_recipe(spec), hashlib.sha256).hexdigest()


def _verify_recipe(spec: Dict[str, Any], key: bytes) -> bool:
    want = spec.get("sig")
    if not want or not isinstance(want, str):
        return False
    return hmac.compare_digest(want, _sign_recipe(spec, key))


def _validate_argv(argv: Any) -> None:
    """Bound what a recipe can ever exec: this interpreter, `-m`, an allow-listed module."""
    if not isinstance(argv, list) or not argv:
        raise ValueError("recipe argv missing or not a list")
    a0 = str(argv[0])
    if a0 != sys.executable and os.path.basename(a0) not in (
            "python", "python3", os.path.basename(sys.executable)):
        raise ValueError(f"recipe argv[0] must be the Python interpreter, got {a0!r}")
    if len(argv) < 3 or argv[1] != "-m":
        raise ValueError("recipe must launch a module via '-m <module>'")
    mod = str(argv[2])
    if mod not in _ALLOWED_SPAWN_MODULES and not mod.startswith(_ALLOWED_MODULE_PREFIXES):
        raise ValueError(f"module {mod!r} is not in the spawn allow-list")


def _sanitize_env(env_add: Any) -> Dict[str, str]:
    """Non-secret operational keys only; credential-shaped keys are refused (secrets inherit)."""
    if env_add is None:
        return {}
    if not isinstance(env_add, dict):
        raise ValueError("recipe env_add must be a dict")
    clean: Dict[str, str] = {}
    for k, v in env_add.items():
        ku = str(k).upper()
        if any(h in ku for h in _SECRET_HINTS):
            raise ValueError(f"env key {k!r} is credential-shaped — refused "
                             f"(secrets are inherited at respawn, never stored in the run-dir)")
        if k not in _ALLOWED_ENV_KEYS:
            raise ValueError(f"env key {k!r} not in the recipe allow-list")
        clean[str(k)] = str(v)
    return clean


def build_process_spec(argv: List[str], cwd: str, *, env_add: Optional[Dict[str, str]] = None,
                       env_inherit: bool = True, new_session: bool = True,
                       log: Optional[str] = None,
                       base_dir: Optional[str] = None) -> Dict[str, Any]:
    """Construct a validated (and, if a key is available, signed) process respawn recipe.

    Callers build this at registration time and hand it to the run-dir, so the descriptor is
    self-sufficient: any Supervisor host can later respawn from it without this process's memory.
    Raises ValueError if the argv/env violate the allow-list — a malformed recipe never persists.
    """
    _validate_argv(argv)
    spec: Dict[str, Any] = {
        "substrate": SUBSTRATE_PROCESS,
        "argv": [str(a) for a in argv],
        "cwd": cwd,
        "env_add": _sanitize_env(env_add),
        "env_inherit": bool(env_inherit),
        "new_session": bool(new_session),
    }
    if log:
        spec["log"] = log
    if base_dir is not None:
        key = _supervisor_key(base_dir)
        if key:
            spec["sig"] = _sign_recipe(spec, key)
    return spec


def _check_run_perms(base_dir: str, unit_id: str) -> Tuple[bool, str]:
    """The run-dir and the descriptor must be owner-only — else a tampered recipe could be exec'd.

    The run-dir (0700) is checked ALWAYS and is the real gate: being owner-only, nothing another
    principal wrote could live inside it. The descriptor file is checked only WHEN PRESENT — during
    a restart the recipe is respawned from an in-memory dict captured before stop() removed the
    file, so the file is transiently absent; the run-dir guarantee still holds and the recipe is
    re-persisted (0600) by record_running right after. An absent file is therefore not a failure;
    a present-but-wrong-perms file still is."""
    rd = run_dir(base_dir)
    try:
        st = os.stat(rd)
    except OSError as exc:
        return False, f"cannot stat {rd}: {exc}"
    if hasattr(os, "geteuid") and st.st_uid != os.geteuid():
        return False, "run-dir not owned by current uid — refusing recipe"
    if st.st_mode & 0o022:
        return False, "run-dir is group/other-writable — refusing recipe"
    dp = _unit_path(base_dir, unit_id)
    try:
        st = os.stat(dp)
    except FileNotFoundError:
        return True, ""                        # respawn-from-memory mid-restart; run-dir is the gate
    except OSError as exc:
        return False, f"cannot stat {os.path.basename(dp)}: {exc}"
    if hasattr(os, "geteuid") and st.st_uid != os.geteuid():
        return False, f"{os.path.basename(dp)} not owned by current uid — refusing its recipe"
    if st.st_mode & 0o022:
        return False, f"{os.path.basename(dp)} is group/other-writable — refusing its recipe"
    return True, ""


def authorize_recipe(base_dir: str, unit_id: str, spec: Dict[str, Any]) -> Tuple[bool, str]:
    """The full gate, cheapest layer first: perms → argv/env allow-list → signature."""
    ok, why = _check_run_perms(base_dir, unit_id)
    if not ok:
        return False, why
    try:
        _validate_argv(spec.get("argv"))
        _sanitize_env(spec.get("env_add"))
    except ValueError as exc:
        return False, str(exc)
    key = _supervisor_key(base_dir)
    if key:
        if not _verify_recipe(spec, key):
            # Hard refuse a recipe that does not verify against the current key — tamper-detection
            # stays strong (a modified argv/spec, or a foreign/old-key recipe, is never respawned).
            # The headless "old-signed recipe → respawn rejected forever" window is closed WITHOUT
            # weakening this: the boot flow re-records a FRESH portal (see Supervisor.reconcile — it
            # is remove-only for svc:web-portal, so boot always spawns and records its own), and
            # build_recipe signs that record with the CURRENT key. So after any boot the stored
            # recipe verifies, and the running health tick respawns it cleanly.
            return False, "recipe signature invalid or missing (key present)"
    elif _strict_signing():
        return False, "strict signing on but no supervisor key available to verify recipe"
    return True, ""


def respawn(base_dir: str, unit: Dict[str, Any]) -> subprocess.Popen:
    """Re-execute a service from its persisted recipe (P1), through the full gate. The ONLY
    place the Supervisor turns a stored recipe back into a running process."""
    unit_id = unit.get("id", "?")
    spec = unit.get("spec")
    if not spec or spec.get("substrate") != SUBSTRATE_PROCESS:
        raise SupervisorError(f"'{unit_id}' has no respawnable process recipe")
    ok, why = authorize_recipe(base_dir, unit_id, spec)
    if not ok:
        raise SupervisorError(f"refusing to respawn '{unit_id}': {why}")
    env = dict(os.environ) if spec.get("env_inherit", True) else {}
    env.update(spec.get("env_add") or {})      # secrets inherited above; env_add is non-secret
    stdout = None
    log = spec.get("log")
    if log:
        try:
            os.makedirs(os.path.dirname(log), exist_ok=True)
            stdout = open(log, "a")
        except OSError:
            stdout = None
    try:
        proc = subprocess.Popen(
            spec["argv"], stdout=stdout,
            stderr=subprocess.STDOUT if stdout else None,
            cwd=spec.get("cwd") or None, env=env,
            start_new_session=bool(spec.get("new_session", True)),
        )
    except Exception as exc:
        if stdout:
            try:
                stdout.close()
            except OSError:
                pass
        raise SupervisorError(f"respawn of '{unit_id}' failed to exec: {exc}") from exc
    return proc


# ── descriptor read / write (atomic, cross-process) ─────────────────────────────

def _ensure_run_dir(base_dir: str) -> str:
    d = run_dir(base_dir)
    os.makedirs(d, exist_ok=True)
    try:
        os.chmod(d, 0o700)
    except OSError:
        pass
    return d


def write_unit(base_dir: str, unit: Dict[str, Any]) -> None:
    """Persist a unit descriptor atomically. `unit` must carry at least 'id' and 'kind'."""
    _ensure_run_dir(base_dir)
    unit_id = unit["id"]
    path = _unit_path(base_dir, unit_id)
    tmp = path + f".tmp.{os.getpid()}"
    try:
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(unit, fh, ensure_ascii=False)
        try:
            os.chmod(tmp, 0o600)
        except OSError:
            pass
        os.replace(tmp, path)                  # atomic swap — readers never see a torn file
    finally:
        try:
            if os.path.exists(tmp):
                os.unlink(tmp)
        except OSError:
            pass
    pid = unit.get("pid")
    if unit.get("kind") == KIND_SERVICE and pid:
        try:
            with open(_pid_path(base_dir, unit_id), "w") as pf:
                pf.write(str(pid))
        except OSError:
            pass


def read_unit(base_dir: str, unit_id: str) -> Optional[Dict[str, Any]]:
    try:
        with open(_unit_path(base_dir, unit_id), "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (FileNotFoundError, ValueError, OSError):
        return None


def remove_unit(base_dir: str, unit_id: str) -> None:
    for p in (_unit_path(base_dir, unit_id), _pid_path(base_dir, unit_id)):
        try:
            os.unlink(p)
        except FileNotFoundError:
            pass
        except OSError:
            pass


def list_units(base_dir: str) -> List[Dict[str, Any]]:
    """Every unit in the run-dir, annotated with live=True/False (kill -0). Cross-process:
    works from ANY process, even one that did not spawn the units — this is what `svc ls`
    reads so a fresh CLI sees the detached daemon + portal."""
    d = run_dir(base_dir)
    out: List[Dict[str, Any]] = []
    try:
        names = os.listdir(d)
    except OSError:
        return out
    for name in names:
        if not name.endswith(".json"):
            continue
        try:
            with open(os.path.join(d, name), "r", encoding="utf-8") as fh:
                unit = json.load(fh)
        except (ValueError, OSError):
            continue
        if unit.get("kind") == KIND_SERVICE:
            unit["live"] = _pid_alive(unit.get("pid"))
        else:
            # jobs report their own state (running/complete/failed); they have no pid.
            unit["live"] = unit.get("state") in ("running", "starting")
        out.append(unit)
    out.sort(key=lambda u: (u.get("kind", ""), u.get("id", "")))
    return out


def record_job(base_dir: str, unit_id: str, state: str,
               detail: Optional[Dict[str, Any]] = None) -> None:
    """Mount an in-process job onto the plane as a unit (e.g. 'job:onto-load'). The JobExecutor
    (JCL/WriteQueue) still runs it; this only records state so it appears in the unified view."""
    unit = read_unit(base_dir, unit_id) or {"id": unit_id, "kind": KIND_JOB,
                                             "started_at": time.time()}
    unit["kind"] = KIND_JOB
    unit["state"] = state
    unit["updated_at"] = time.time()
    if detail:
        unit["detail"] = detail
    try:
        write_unit(base_dir, unit)
    except OSError as exc:
        logger.debug("[Supervisor] record_job(%s) failed: %s", unit_id, exc)


# ── the Supervisor (service lifecycle host) ─────────────────────────────────────

class Supervisor:
    """Hosts the service lifecycle for the process that owns it (the Cell daemon = Akasha's
    service init). Spawns children, persists their descriptors to the run-dir, stops them in
    reverse-dependency order with each unit's own grace, and reconciles/adopts on boot.

    Services are registered with a `spawn_fn` (the blueprint). The Supervisor does not itself
    keep the authoritative list in memory — the run-dir is the truth — but it holds the live
    Popen handles + blueprints for the units IT started, so it can stop/restart them precisely.
    """

    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self._procs: Dict[str, subprocess.Popen] = {}      # id → live handle (this process)
        self._specs: Dict[str, Dict[str, Any]] = {}        # id → {spawn_fn, deps, grace, restart}
        self._health_fails: Dict[str, int] = {}            # id → consecutive health-probe failures
        self._last_respawn: Dict[str, float] = {}          # id → monotonic time of last health respawn
        self._logfds: Dict[str, Any] = {}                  # id → open log file handle (this process)
        _ensure_run_dir(base_dir)

    # -- this-process handles (ServiceManager's former job) --
    def get_proc(self, unit_id: str) -> Optional[subprocess.Popen]:
        """The live Popen for a unit THIS process spawned (or None). Lets the launcher
        wait on / inspect the portal it started, without a separate registry."""
        return self._procs.get(unit_id)

    def release(self, unit_id: str) -> None:
        """Detach a unit from THIS process's lifecycle: stop tracking its handle + log fd
        so stop_local() will NOT stop it at exit, but LEAVE the run-dir descriptor so it
        stays cross-process controllable (`akasha.py stop`). Used when a public deploy leaves
        the portal serving after the CLI exits. The fd is intentionally NOT closed — the
        detached process keeps writing to it."""
        self._procs.pop(unit_id, None)
        self._logfds.pop(unit_id, None)

    def stop_local(self) -> None:
        """atexit hook: stop only the service units THIS process spawned (holds a live handle
        for), each with its own grace. A released/detached portal is untracked, so it survives.
        Replaces ServiceManager.stop_all as the process-exit cleanup."""
        for uid in list(self._procs.keys()):
            try:
                self.stop(uid)
            except Exception:
                pass

    # -- registration + spawn --
    def register(self, unit_id: str, spawn_fn: Callable[[], subprocess.Popen],
                 deps: Optional[List[str]] = None, grace_s: float = 5.0,
                 restart: str = RESTART_NEVER, host: str = "", port: int = 0,
                 engine: str = "") -> None:
        """Register a service blueprint. spawn_fn() must return a live subprocess.Popen."""
        self._specs[unit_id] = {
            "spawn_fn": spawn_fn, "deps": deps or [], "grace_s": grace_s,
            "restart": restart, "host": host, "port": port, "engine": engine,
        }

    def record_running(self, unit_id: str, pid: int, *, engine: str = "", host: str = "",
                       port: int = 0, grace_s: float = 5.0, restart: str = RESTART_NEVER,
                       deps: Optional[List[str]] = None,
                       proc: Optional[subprocess.Popen] = None,
                       spec: Optional[Dict[str, Any]] = None,
                       substrate: str = SUBSTRATE_PROCESS, trust: str = "",
                       serve_only: Optional[bool] = None,
                       health: Optional[Dict[str, Any]] = None,
                       log_fd: Optional[Any] = None) -> None:
        """Persist a service unit as running. Used both when the Supervisor spawns a child and
        when an already-launched process (e.g. the daemon itself, or a portal started elsewhere)
        wants to appear on the plane. When `spec` (a validated respawn recipe) is given it is
        stored on the descriptor, so any Supervisor host can later respawn the unit (P1).
        `log_fd`, if given, is held so it is closed when this process stops the unit."""
        if proc is not None:
            self._procs[unit_id] = proc
        if log_fd is not None:
            self._logfds[unit_id] = log_fd
        desc: Dict[str, Any] = {
            "id": unit_id, "kind": KIND_SERVICE, "state": "running", "pid": pid,
            "engine": engine, "host": host, "port": port, "grace_s": grace_s,
            "restart": restart, "deps": deps or [], "substrate": substrate,
            "log": (spec or {}).get("log") or os.path.join("logs", _safe(unit_id) + ".log"),
            "started_at": time.time(), "updated_at": time.time(),
        }
        if trust:
            desc["trust"] = trust
        if serve_only is not None:
            desc["serve_only"] = bool(serve_only)
        if health:
            desc["health"] = health
        if spec is not None:
            desc["spec"] = spec
        write_unit(self.base_dir, desc)

    def _admit(self, unit: Dict[str, Any]) -> Tuple[bool, str]:
        """Single-writer admission (premises P5): a writer-capable unit (opens its own engine,
        i.e. serve_only is explicitly False) may not start while svc:cell — the one nucleus
        writer — is live. Network fronts are always serve_only, so this only ever bites a
        misconfigured second writer."""
        if unit.get("serve_only") is False and unit.get("id") != "svc:cell":
            cell = read_unit(self.base_dir, "svc:cell")
            if cell and _pid_alive(cell.get("pid")):
                return (False, f"refusing to start writer-capable '{unit.get('id')}': "
                               f"svc:cell already holds the single nucleus writer")
        return (True, "")

    def _start_from_recipe(self, unit: Dict[str, Any]) -> Dict[str, Any]:
        """Respawn a persisted unit from its recipe (cross-process / post-restart / reconcile)."""
        ok, why = self._admit(unit)
        if not ok:
            return {"error": why}
        try:
            proc = respawn(self.base_dir, unit)
        except SupervisorError as exc:
            return {"error": str(exc)}
        self.record_running(
            unit["id"], proc.pid, engine=unit.get("engine", ""), host=unit.get("host", ""),
            port=unit.get("port", 0), grace_s=unit.get("grace_s", 5.0),
            restart=unit.get("restart", RESTART_NEVER), deps=unit.get("deps", []),
            proc=proc, spec=unit.get("spec"), substrate=unit.get("substrate", SUBSTRATE_PROCESS),
            trust=unit.get("trust", ""), serve_only=unit.get("serve_only"),
            health=unit.get("health"))
        logger.info("[Supervisor] respawned '%s' from recipe → PID %s", unit["id"], proc.pid)
        return {"status": "started", "id": unit["id"], "pid": proc.pid, "via": "recipe"}

    def start(self, unit_id: str) -> Dict[str, Any]:
        existing = read_unit(self.base_dir, unit_id)
        if existing and _pid_alive(existing.get("pid")):
            return {"error": f"'{unit_id}' already running (PID {existing['pid']})"}
        spec = self._specs.get(unit_id)               # in-memory blueprint (this process)
        # start dependencies first (from the in-memory blueprint or the persisted descriptor)
        deps = (spec or {}).get("deps") or (existing or {}).get("deps") or []
        for dep in deps:
            dstate = read_unit(self.base_dir, dep)
            if not (dstate and _pid_alive(dstate.get("pid"))):
                self.start(dep)
        if spec:
            try:
                proc = spec["spawn_fn"]()
            except Exception as exc:
                logger.error("[Supervisor] spawn '%s' failed: %s", unit_id, exc)
                return {"error": f"spawn failed: {exc}"}
            self.record_running(unit_id, proc.pid, engine=spec.get("engine", ""),
                                host=spec.get("host", ""), port=spec.get("port", 0),
                                grace_s=spec.get("grace_s", 5.0),
                                restart=spec.get("restart", RESTART_NEVER),
                                deps=spec.get("deps", []), proc=proc,
                                spec=spec.get("recipe"), trust=spec.get("trust", ""),
                                serve_only=spec.get("serve_only"))
            logger.info("[Supervisor] started '%s' PID %s", unit_id, proc.pid)
            return {"status": "started", "id": unit_id, "pid": proc.pid}
        # No in-memory blueprint → respawn from the persisted recipe (cross-process, P1).
        if existing and existing.get("spec"):
            return self._start_from_recipe(existing)
        return {"error": f"no blueprint or recipe for '{unit_id}' (restart akasha.py to re-register)"}

    # -- stop / restart --
    def stop(self, unit_id: str, grace_s: Optional[float] = None) -> Dict[str, Any]:
        unit = read_unit(self.base_dir, unit_id)
        pid = unit.get("pid") if unit else None
        if grace_s is None:
            grace_s = (unit or {}).get("grace_s", 5.0) if unit else 5.0
        proc = self._procs.get(unit_id)
        stopped = False
        if pid and _pid_alive(pid):
            try:
                os.kill(pid, signal.SIGTERM)
            except (ProcessLookupError, PermissionError):
                pass
            deadline = time.time() + max(0.5, grace_s)
            while time.time() < deadline:
                if not _pid_alive(pid):
                    stopped = True
                    break
                time.sleep(0.1)
            if not stopped and _pid_alive(pid):
                try:
                    os.kill(pid, signal.SIGKILL)          # last resort
                except (ProcessLookupError, PermissionError):
                    pass
                stopped = True
        # close a live Popen's log fd if we own it
        if proc is not None:
            try:
                proc.wait(timeout=0.1)
            except Exception:
                pass
            self._procs.pop(unit_id, None)
        fd = self._logfds.pop(unit_id, None)
        if fd is not None:
            try:
                fd.close()
            except Exception:
                pass
        remove_unit(self.base_dir, unit_id)
        return {"status": "stopped" if (stopped or not pid) else "already_dead", "id": unit_id}

    def restart(self, unit_id: str) -> Dict[str, Any]:
        # Capture the persisted descriptor BEFORE stop() removes it, so a cross-process
        # restart (no in-memory blueprint) can still respawn from the recipe (P1).
        prior = read_unit(self.base_dir, unit_id)
        self.stop(unit_id)
        time.sleep(0.3)
        if unit_id in self._specs:
            return self.start(unit_id)
        if prior and prior.get("spec"):
            return self._start_from_recipe(prior)
        return {"error": f"no blueprint or recipe to restart '{unit_id}' "
                         f"(restart akasha.py to re-register)"}

    def stop_all(self, cascade_root: Optional[str] = None) -> List[Dict[str, Any]]:
        """Stop every service unit in the run-dir, in reverse-dependency order (dependents
        before their dependencies), each with its own grace. Used on daemon shutdown."""
        units = [u for u in list_units(self.base_dir) if u.get("kind") == KIND_SERVICE]
        ordered = _reverse_dep_order(units)
        results = []
        for u in ordered:
            if cascade_root and u["id"] == cascade_root:
                continue                                   # stop the root last / by the caller
            results.append(self.stop(u["id"], grace_s=u.get("grace_s")))
        if cascade_root:
            results.append(self.stop(cascade_root))
        return results

    # -- boot reconcile --
    def reconcile(self) -> None:
        """On daemon boot, reconcile the run-dir against reality. A unit whose pid is still alive
        is adopted (left as-is). A dead service unit with an `on-failure`/`always` policy AND a
        respawnable process recipe is RESPAWNED through the gate (P1); otherwise its stale
        descriptor is scrubbed. svc:cell (the daemon itself) is never respawned from within.
        Jobs are left as-is (their executor owns them)."""
        for u in list_units(self.base_dir):
            if u.get("kind") != KIND_SERVICE:
                continue
            if _pid_alive(u.get("pid")):
                continue                                   # alive → adopt
            policy = u.get("restart", RESTART_NEVER)
            # svc:web-portal is ALSO never respawned at boot: the boot flow spawns a fresh portal
            # itself right after this reconcile, so respawning it here double-spawns — two portals
            # race the same port and the loser becomes an unmanaged ghost (httpd falls back to
            # another port; uvicorn dies EADDRINUSE while the run-dir points at the dead one — the
            # entry to the 'respawned svc:web-portal (unhealthy)' loop). Remove-only here; the
            # RUNNING health tick (maintain) still respawns it from recipe if it dies later.
            respawnable = ((u.get("spec") or {}).get("substrate") == SUBSTRATE_PROCESS
                           and u["id"] not in ("svc:cell", "svc:web-portal"))
            if policy in (RESTART_ON_FAILURE, RESTART_ALWAYS) and respawnable:
                r = self._start_from_recipe(u)
                if not r.get("error"):
                    logger.info("[Supervisor] reconciled '%s' → respawned per '%s' policy.",
                                u["id"], policy)
                    continue
                logger.warning("[Supervisor] reconcile respawn of '%s' declined: %s",
                               u["id"], r.get("error"))
            remove_unit(self.base_dir, u["id"])
            logger.info("[Supervisor] reconciled dead unit '%s' (pid gone).", u["id"])

    # A hung-but-alive service must fail its probe this many CONSECUTIVE ticks before it is
    # replaced — so a single transient blip (a slow moment, a mis-timed probe) never kills a
    # healthy service. A genuinely DEAD pid is unambiguous and respawns immediately (no debounce).
    _HEALTH_FAIL_THRESHOLD = 2
    _RESPAWN_MIN_S = 30.0                 # min seconds between health respawns of the SAME unit
                                          # (backoff — stops a can't-start service hammering in a loop)

    def maintain(self) -> List[Dict[str, Any]]:
        """Periodic health tick (P4): respawn units that FAIL their health probe, per restart
        policy — extending boot reconcile to hung-but-alive services (which pass `kill -0` but
        don't answer their tcp/http probe). Only process-substrate units respawn (P2); svc:cell
        is never touched from within. A crashed unit respawns at once; a hung one only after
        `_HEALTH_FAIL_THRESHOLD` consecutive failures (debounce). Returns the actions taken."""
        actions: List[Dict[str, Any]] = []
        for u in list_units(self.base_dir):
            uid = u["id"]
            if u.get("kind") != KIND_SERVICE or uid == "svc:cell":
                continue
            if probe_health(u):
                self._health_fails.pop(uid, None)     # healthy → reset the counter
                continue
            alive = _pid_alive(u.get("pid"))
            if alive:
                # hung (alive but not answering) — debounce before acting
                n = self._health_fails.get(uid, 0) + 1
                self._health_fails[uid] = n
                if n < self._HEALTH_FAIL_THRESHOLD:
                    continue
            self._health_fails.pop(uid, None)
            policy = u.get("restart", RESTART_NEVER)
            respawnable = (u.get("spec") or {}).get("substrate") == SUBSTRATE_PROCESS
            if policy not in (RESTART_ON_FAILURE, RESTART_ALWAYS) or not respawnable:
                continue                              # no policy / not respawnable → leave for the operator
            # Respawn BACKOFF — never respawn the same unit more often than every _RESPAWN_MIN_S.
            # A unit that keeps dying immediately (e.g. a portal that can't bind its port because a
            # prior orphan still holds it) would otherwise be respawned on EVERY health tick — an
            # unbounded tight loop that piles up ~1 GB uvicorn processes (the 46 MB web-portal.log
            # of bind errors) and can OOM the writer. The backoff turns that into a slow, bounded
            # retry so a mis-configured/stuck service degrades gracefully instead of hammering.
            _now = time.time()
            _last = self._last_respawn.get(uid, 0.0)
            if _now - _last < self._RESPAWN_MIN_S:
                continue                              # too soon since the last respawn — wait it out
            self._last_respawn[uid] = _now
            if alive:                                 # stop the hung instance before replacing it
                self.stop(uid, grace_s=u.get("grace_s", 5.0))
            r = self._start_from_recipe(u)
            r["reason"] = "unhealthy" if alive else "dead"
            actions.append({"id": uid, **r})
            if r.get("error"):
                logger.warning("[Supervisor] health respawn of '%s' declined: %s", uid, r["error"])
            else:
                logger.info("[Supervisor] health tick respawned '%s' (%s, policy=%s).",
                            uid, r["reason"], policy)
        return actions


# ── health probes (P4) — serializable, evaluated generically (no app import) ────

def _tcp_ok(target: str, timeout: float = 2.0) -> bool:
    import socket
    try:
        host, _, port = str(target).rpartition(":")
        with socket.create_connection((host or "127.0.0.1", int(port)), timeout=timeout):
            return True
    except (OSError, ValueError):
        return False


def _http_ok(url: Optional[str], expect: int = 200, timeout: float = 2.0,
             method: Optional[str] = None) -> bool:
    """HTTP liveness probe. Two modes:

      • GET (method=None): the URL must answer with `expect` (200). A plain /health route.
      • JSON-RPC POST (method set): POST {"method": method} and treat ANY HTTP-level response —
        even 4xx/5xx or a JSON-RPC error body — as ALIVE, because the worker had to RUN code to
        produce it. This is the wedged-process discriminator (RC3/R3): a SIGSTOPped/hung worker
        completes the kernel TCP handshake into its accept backlog but never runs, so no HTTP (or
        TLS) response ever comes back and the request TIMES OUT → reported dead. A bare TCP connect
        (the old probe) passed on such a process; a request that needs the worker to answer does not.

    HTTPS targets are probed with certificate verification OFF — this is a localhost liveness check,
    not an authentication; a completed TLS handshake already proves the worker ran."""
    if not url:
        return False
    import urllib.request, urllib.error, json as _json, ssl as _ssl
    ctx = None
    if str(url).lower().startswith("https:"):
        ctx = _ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = _ssl.CERT_NONE
    try:
        if method:
            body = _json.dumps({"jsonrpc": "2.0", "method": method,
                                "params": {"session_token": "_health_"}, "id": "hp"}).encode()
            req = urllib.request.Request(
                url, data=body, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout, context=ctx):   # noqa: S310
                return True                          # any HTTP response = the worker ran = alive
        with urllib.request.urlopen(url, timeout=timeout, context=ctx) as resp:   # noqa: S310
            return resp.status == expect
    except urllib.error.HTTPError:
        return True                                  # 4xx/5xx: the worker RAN and answered → alive
    except urllib.error.URLError as exc:
        # A TLS handshake that completed proves the worker ran even if the cert failed to verify;
        # a refused/timed-out connection means dead or wedged.
        return isinstance(getattr(exc, "reason", None), _ssl.SSLError)
    except Exception:
        return False                                 # timeout / refused / reset → dead or wedged


def probe_health(unit: Dict[str, Any]) -> bool:
    """Evaluate a unit's declared health probe (P4). The floor is `kill -0`; a unit may declare a
    richer probe as DATA so the Supervisor checks it without importing the service's code:
      {"kind":"pid"}                                   process alive (default)
      {"kind":"tcp","target":"host:port"}              accepting connections
      {"kind":"http","target":"http://…/healthz","expect":200}   a route answers (GET)
      {"kind":"http","target":"http://…/api/rpc","method":"sys.ping"}   the worker RUNS code
                                                 (detects a WEDGED process a TCP connect misses)
    """
    if not _pid_alive(unit.get("pid")):
        return False                              # dead → unhealthy, always
    probe = unit.get("health") or {"kind": "pid"}
    kind = probe.get("kind", "pid")
    if kind == "pid":
        return True
    if kind == "tcp":
        target = probe.get("target") or f"{unit.get('host') or '127.0.0.1'}:{unit.get('port')}"
        return _tcp_ok(target)
    if kind == "http":
        return _http_ok(probe.get("target"), int(probe.get("expect", 200)),
                        timeout=float(probe.get("timeout", 2.0)), method=probe.get("method"))
    return True                                   # unknown probe kind → don't false-kill


def _reverse_dep_order(units: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Order units for a STOP cascade: a dependent (A depends on B) is stopped BEFORE its
    dependency. Standard DFS topological sort emits dependencies-first; we reverse it so
    dependents come first. Cycle-tolerant (a back-edge is simply skipped)."""
    by_id = {u["id"]: u for u in units}
    ordered: List[Dict[str, Any]] = []       # dependencies-first
    seen = set()

    def visit(uid: str, stack: set):
        if uid in seen or uid not in by_id or uid in stack:
            return
        stack.add(uid)
        for dep in by_id[uid].get("deps", []):   # visit dependencies first
            visit(dep, stack)
        stack.discard(uid)
        seen.add(uid)
        ordered.append(by_id[uid])               # emitted AFTER its dependencies

    for u in units:
        visit(u["id"], set())
    return list(reversed(ordered))               # reverse → dependents before dependencies
