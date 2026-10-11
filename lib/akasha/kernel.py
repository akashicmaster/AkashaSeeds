"""
Akasha Kernel Dispatcher.
The single authoritative boundary between the Shell (api/, remote/) and the
cognitive engine (lib/). All JSON-RPC 2.0 requests enter through `dispatch()`.

[RESPONSIBILITIES]
- Bootstrap all kernel subsystems: HarmoniaEngine, AkashaManager, ContexaEngine
- Authenticate every request via IAM before touching a session
- Route method calls to the appropriate cognitive engine
- Return well-formed JSON-RPC 2.0 response dicts (never raise to the caller)

[WHAT DOES NOT LIVE HERE]
- CLI rendering, ANSI colors, multi-line input, pipe/redirect handling
- HTTP server startup, ASGI lifecycle
- Any import of api.*, remote.*, or services.*
"""

import os
import re
import sys
import time
import json
import uuid
import logging
import hashlib
from typing import Dict, Any, Optional, List

from lib.akasha.manager import AkashaManager
from lib.akasha.identity import Role, Capability
from lib.akasha.kernel_methods import METHOD_TO_ACTION as _METHOD_TO_ACTION
from lib.akasha.api import gate as _gate   # the one function that decides (2026-09-22)
from lib.akasha.pagination import paginate as _paginate, resolve_limit as _rlimit, resolve_offset as _roffset

try:
    from lib.akasha import __version__ as _AKASHA_VERSION
except ImportError:
    _AKASHA_VERSION = "dev"

logger = logging.getLogger("Akasha.Kernel")

# ── Transport trust levels ──────────────────────────────────────────────────
# Trust is a property of the *server-side transport binding*, set by the portal
# that received the request — never a value the client can supply.  It governs
# whether a bare client_id may assert an identity:
#
#   TRUST_NETWORK  (default) — untrusted remote (HTTP/ASGI, web worker, CGI).
#                              A privileged identity must prove itself with a
#                              signed akt: session token; a bare client_id is
#                              only ever accepted as an anonymous GUEST.
#   TRUST_LOCAL              — the local operator's stdio console.  The OS
#                              process boundary is the real gate, so a bare
#                              client_id (incl. the admin) is accepted.
#   TRUST_INTERNAL           — kernel-originated in-process dispatch (JCL worker,
#                              boot loader, self-dispatch).  Bare client_id and
#                              system.* process identities are accepted.
from lib.akasha.api.trust import (TRUST_NETWORK, TRUST_LOCAL, TRUST_INTERNAL,
                                  TRUSTED_TRANSPORTS as _TRUSTED_TRANSPORTS)
from lib.akasha.api.rpc import ok as _ok, err as _err
from lib.akasha.api.ops import Req as _Req
from lib.akasha.api import manifest as _manifest
from lib.akasha import api as _api
from lib.akasha.api.heart import _NucleusWriteCtx
from lib.akasha.api.heart import _rss_mb, _SEARCH_PARTIAL, _run_gated_maint, _with_rss_delta, _mem_available_mb, _smaps_rollup, _thread_count

_HEART_AGG = None


def _heart_aggregate():
    """The aggregated manifests (heart + packages): the dispatch table, the timer registry, the
    provisioning hooks. Built once per process, on the first kernel; a manifest entry that does not
    resolve raises here — a boot error naming the entry, never a silent -32601 at request time."""
    global _HEART_AGG
    if _HEART_AGG is None:
        _HEART_AGG = _manifest.load_manifests(
            _manifest.default_manifest_paths(os.path.dirname(os.path.abspath(__file__))))
    return _HEART_AGG


# The ACTIONS whose turns the per-turn workspace seam wraps (single-route guard) — a list of
# names saying which turns must be TRANSACTIONAL, never a permission. It had to move with the
# eight-action vocabulary: the old `write`/`link.create`/`meta.set`/`sync.pull` set matched
# nothing after the remap, so no workspace opened and every write outside JCL was refused by the
# guard it serves. `read`/`run` stay out (a read never trips it; a run's job carries its own);
# `admin` is in for `sync.pull`, and the rest of that row only pays an empty workspace.
_WRITE_ACTIONS = frozenset({
    "record", "say", "annotate", "publish", "provision", "admin",
})

# Optional engines — degrade gracefully if missing
try:
    from lib.harmonia.engine import HarmoniaEngine
except ImportError:
    HarmoniaEngine = None  # type: ignore

try:
    from lib.contexa.engine import ContexaEngine
except ImportError:
    ContexaEngine = None  # type: ignore

try:
    from lib.harmonia.fileio import FileIO
    from lib.harmonia.infra import HarmoniaInfra
except ImportError:
    FileIO = None  # type: ignore
    HarmoniaInfra = None  # type: ignore

from lib.akasha.jcl.workspace_context import (
    active as _workspace_active,
    _in_workspace,
)

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

ScriptConcept = None  # ScriptConcept removed; kept as None for backward-compat guards

# ── Concept Model routers — the packages' dynamic dispatchers, declared in their manifests
#    (`routers`, e.g. the Concept Model registry). The heart consults them through the router
#    protocol only (dispatch_if_handled / get_method_actions / get_class) and never names a package.
#    Their auto-derived method→action entries merge into the live METHOD_TO_ACTION dict; existing
#    hand-written entries are never overwritten (they take precedence).
#    (merged when the first kernel builds the aggregate — the manifests name this class's own
#    handlers, so the aggregate cannot be built while this module is still importing.)


import threading as _threading_maint

# ── F39-P1a — admission control on dive-bearing serving requests ─────────────────
# The confirmed production failure: crawler traffic drives many CONCURRENT concept-space / dive
# renders, each building a signpost+resonance neighbourhood in RAM; daemon RSS then scales with the
# request ARRIVAL RATE and OOM-kills the writer (~every 18 min, three kills logged 8/28). A blackout
# test proved causality (zero traffic → RSS flat). The fix bounds CONCURRENCY, not arrival: at most
# `cap` dives run at once (so peak RAM = cap × per-dive), a small queue absorbs bursts, and beyond
# that a request is refused FAST with a millisecond Retry-After — never a 60 s hang, never a death.
# The invariant (P5 eval): daemon RSS must not scale with arrival rate.
# WHICH methods are dive-bearing is what each op DECLARES about itself — `"dive_bearing": true` on
# its manifest entry — and the set is built from the aggregate (group 4, 4.2). The heart kept a
# list of nine names, five of them an application's; `node` and `dive` had not been ops for a
# while, which is what a list of names does when nobody owns it.
def _dive_bearing(kernel) -> frozenset:
    cached = getattr(kernel, "_dive_bearing_cache", None)
    if cached is None:
        cached = frozenset(_api.ops_with(kernel, "dive_bearing"))
        kernel._dive_bearing_cache = cached
        logger.info("[api] dive_bearing ops=%d %s", len(cached), sorted(cached))
    return cached


class _DiveAdmission:
    """Bounded concurrency for dive-bearing work. `cap` slots run concurrently; up to `queue`
    callers WAIT for a slot (bounded by `wait_ms`); anyone beyond that is refused immediately. Never
    unbounded: the whole point is that overload degrades to fast refusals, not memory growth."""

    def __init__(self):
        import threading as _t

        def _envint(name, default):
            try:
                return max(1, int(os.environ.get(name, "").strip() or default))
            except (TypeError, ValueError):
                return default
        self.cap = _envint("AKASHA_DIVE_ADMIT", 3)
        self.queue = _envint("AKASHA_DIVE_QUEUE", 10)
        self.wait_ms = _envint("AKASHA_DIVE_WAIT_MS", 5000)
        self._sem = _t.Semaphore(self.cap)
        self._lock = _t.Lock()
        self._waiting = 0
        self._admitted = 0        # process-lifetime counters (F44-A1.1 health heartbeat)
        self._refused = 0

    def acquire(self):
        """Return (True, 0) if admitted (caller MUST release), or (False, retry_after_ms) if refused
        fast — the queue is full, or no slot freed within the bounded wait."""
        with self._lock:
            if self._waiting >= self.queue:
                self._refused += 1
                return False, max(50, self.wait_ms // 2)      # queue full → refuse now
            self._waiting += 1
        try:
            if self._sem.acquire(timeout=self.wait_ms / 1000.0):
                with self._lock:
                    self._admitted += 1
                return True, 0
            with self._lock:
                self._refused += 1
            return False, max(50, self.wait_ms // 2)          # waited, no slot → refuse
        finally:
            with self._lock:
                self._waiting -= 1

    def release(self):
        self._sem.release()

    def stats(self):
        return {"cap": self.cap, "queue": self.queue, "wait_ms": self.wait_ms,
                "waiting": self._waiting, "admitted": self._admitted, "refused": self._refused}


_DIVE_ADMISSION = _DiveAdmission()




# Method → IAM action mapping imported from lib/akasha/kernel_methods.py


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

# _ok / _err: the JSON-RPC envelope, from lib.akasha.api.rpc (imported above).



def _is_sys_atom(item: dict) -> bool:
    """Return True for internally-managed system atoms (session anchors, etc.)."""
    raw_meta = item.get("meta")
    if not raw_meta:
        return False
    try:
        meta = json.loads(raw_meta) if isinstance(raw_meta, str) else raw_meta
        return str(meta.get("type", "")).startswith("sys:")
    except (json.JSONDecodeError, AttributeError):
        return False



# ---------------------------------------------------------------------------
# _NucleusWriteCtx — transparent write-routing proxy
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# KernelDispatcher
# ---------------------------------------------------------------------------

class KernelDispatcher:
    """
    The cognitive engine gateway.
    Instantiated once at boot; shared across all portal types (stdio, ASGI, MCP…).
    """

    # F52 §2 — WAL auto-fold baseline: the WAL size right after the last fold (auto or manual). The
    # auto-checkpoint daemon folds on GROWTH since this baseline, not on total size (a 2.4 GB live
    # store must not re-fold every idle check). None ⇒ re-baseline on the daemon's first check (boot
    # size IS the post-replay live baseline, so no persistence is needed). In-memory by design.
    _wal_last_fold_bytes = None

    def __init__(self, series: str = "seeds", base_dir: str = "data"):
        self.api = _heart_aggregate()   # §A21 — the manifests: dispatch table + timer registry
        for _dyn_method, _dyn_action in self.api.method_actions.items():   # routers' method→action
            if _dyn_method not in _METHOD_TO_ACTION:
                _METHOD_TO_ACTION[_dyn_method] = _dyn_action
        self.series, self.base_dir = series, base_dir
        from lib.akasha import data_format as _df    # §4.4 — before ANYTHING opens or writes the cell
        _df.check(base_dir)
        if os.environ.get("AKASHA_SERVE_ONLY", "").strip().lower() not in ("1", "yes", "true", "on"):
            _df.stamp(base_dir)                      # a fresh directory's genesis; never overwrites
        _gate.bind(base_dir)   # the gate reads THIS cell's identity files, not the shipped seed

        # Env from the operator secrets file (keys set once via `llm.key`, no Linux export). A real
        # env var already set wins; the file only fills what is missing, and having none is normal.
        try:
            from lib.akasha import secrets as _secrets
            _secrets.load_into_env(base_dir)
        except Exception:
            pass

        self.harmonia = HarmoniaEngine() if HarmoniaEngine else None
        self.manager = AkashaManager(series_name=series, base_dir=base_dir)
        self.iam = self.manager.iam
        self.contexa = ContexaEngine(self.manager, self.harmonia) if ContexaEngine else None
        # Vision inference (image → labels). Lazy: no model/runtime touched until the
        # first image.profile call, so boot never installs or loads anything for it.
        # General file import/export — the single Harmonia-owned disk I/O route (CSV/JSON/
        # MD/TXT). Confined to an allow-list of roots (data/import, data/export, data);
        # admins permit more via io.allow. Graph writes still go through the guarded path.
        self.fileio = FileIO(HarmoniaInfra()) if (FileIO and HarmoniaInfra) else None

        if self.harmonia:
            self._register_harmonia_plugins()

        # JCL worker — started after all other subsystems are ready so that
        # worker threads can safely call self.dispatch() and self.manager.
        # max_workers=1: the phase-1 atoms sentinel is appended to the LAST file's
        # JCL job.  With a single worker, every earlier atom job has already
        # completed by the time the sentinel is written — giving a sound guarantee
        # that all atoms are in nucleus before phase-2 links run.
        # With max_workers>1 the sentinel can fire while large earlier files are
        # still being processed, causing intermittent "not found" on recent atoms.
        # This matches the JCL design principle: serial writes over parallelism.
        #
        # Ownership: the JCL executor is Harmonia's initiator, not a kernel sibling.
        # The kernel builds it (it needs the dispatch ref) and hands ownership to
        # Harmonia; from here the kernel submits jobs via `harmonia.submit_job(...)`,
        # and `self.jcl_worker` is a read-only view onto Harmonia's executor.
        _jcl = JCLWorker(self, max_workers=1) if JCLWorker else None
        if self.harmonia and _jcl:
            self.harmonia.attach_jcl(_jcl)

        # G3 — let the workflow concept reach the SECURED job.submit path (validate_steps +
        # owner-pinning) for `wf.advance as=job`, without a concept reaching into the JCL worker.
        # §A21 — a package that needs a kernel handle DECLARES it (`binds` in its manifest) and
        # the heart hands itself over here, so the heart imports no application module by name.
        for _bind in self.api.binds:
            try:
                _bind(self)
            except Exception as _bexc:
                logger.debug("[Kernel] bind %s skipped: %s", getattr(_bind, "__name__", _bind), _bexc)

        logger.info(
            f"[Kernel] Dispatcher online — series={series}, "
            f"harmonia={'on' if self.harmonia else 'off'}, "
            f"contexa={'on' if self.contexa else 'off'}, "
            f"jcl={'on' if self.jcl_worker else 'off'}"
        )

        # F60 §2 — writer-role background daemons run RIGHT HERE, not inside _boot_load_ontology.
        # They used to live behind the ontology-load path, which `return`s early at several phases
        # (the SERVE_ONLY gate, the atoms-loaded wait, the global-relations wait, the curation gate);
        # a re-extracted seed whose load short-circuited stranded the writer's own health heartbeat +
        # replan (the daemon-#2 incident: no [Health], no [semcache.replan] for hours). A WRITER must
        # keep these regardless of how the load goes; a genuinely serve-only process skips them.
        # The application's declared identities: validated here — an invalid declaration stops the
        # boot, naming the entry — and, on a cell past Genesis, converged (missing ones created
        # credential-less). A serve-only process validates and writes nothing.
        from lib.akasha import identities as _ids
        _declared = _ids.load()
        if _declared and os.environ.get("AKASHA_SERVE_ONLY", "").strip().lower() in ("", "0", "no", "false", "off"):
            try:
                self.iam.authenticate("admin")
                _ids.reconcile(self, _declared)
            except PermissionError:
                pass                                 # before Genesis: the rite makes them
        self._start_writer_role_daemons()

        # Boot-time ontology load — queue CSL files as JCL jobs if sentinel absent.
        # Runs in a daemon thread so boot is never blocked.
        if self.jcl_worker:
            import threading as _t
            _t.Thread(target=self._boot_load_ontology, daemon=True,
                      name="ont-boot-loader").start()

    def _boot_load_ontology(self) -> None:
        """The boot LOAD phase — the seam the boot thread ("ont-boot-loader") and the post-genesis
        thread run. Its bodies are declared by the manifests (`schedules` with phase `load`), so the
        heart names no loader; evals patch this method to skip the load (the test seam)."""
        self.api.schedules.run_phase(self, "load")

    def _start_writer_role_daemons(self) -> None:
        """F60 §2 — the WRITER's own lifecycle daemons: health heartbeat, WAL maintenance, pulse
        compact, telemetry/broadcast GC, semcache replan, alloc trace. Run once per process, right
        after 'Kernel online', INDEPENDENT of the ontology-load path (which can return early at any
        phase and used to strand these). A genuinely serve-only process (the portal) is never a
        writer and skips them; a writer runs them regardless. They already self-gate on relations
        readiness (poll `_relations_ready()`), so starting them before the load completes is safe."""
        if getattr(self, "_writer_daemons_started", False):
            return
        if os.environ.get("AKASHA_SERVE_ONLY", "").strip().lower() not in ("", "0", "no", "false", "off"):
            logger.info("[Kernel] serve-only process — writer-role daemons not started (portal role)")
            return
        self._writer_daemons_started = True
        # 10-03 item 1: the driver's first tick waits for the declared-workload pass; released on shutdown.
        self._workload_provision_done = _threading_maint.Event()
        from lib.akasha import lifecycle as _lc
        _lc.register_wake(self._workload_provision_done.set)
        try:
            self.api.schedules.run_phase(self, "writer")   # the manifests' writer-phase bodies, in order
            logger.info("[Kernel] writer-role daemons started (health, wal, pulse-compact, "
                        "telemetry/broadcast gc, semcache replan, alloc trace, bench-provision, "
                        "bench-autorun)")
        except Exception as _wexc:
            logger.warning("[Kernel] writer-role daemon start incomplete: %s", _wexc)

    def _concurrent_jobs(self):
        """A54(2) — (n, labels) of JCL jobs currently RUNNING, so a maintenance task's Δrss line can say
        whether the number is contaminated by concurrent work. Best-effort; never raises."""
        try:
            w = self.jcl_worker
            if not w:
                return (0, [])
            from lib.akasha.jcl.job import RUNNING as _RUN
            running = [j for j in (w.list_jobs() or []) if getattr(j, "status", None) == _RUN]
            return (len(running), [getattr(j, "label", None) or getattr(j, "job_id", "?") for j in running])
        except Exception:
            return (0, [])


    def _schedule_hydrate_boot(self) -> None:
        """H1 — after `_relations_ready()`, run the hydrate registry's boot pass ONCE per writer boot:
        each entry's boot policy is executed through the registry (`boot_verify=run` re-runs the cheap
        idempotent regenerator; `record` stamps the epoch), so no entry reads `last_run_epoch=null` and
        the log carries one `[hydrate]` line per accelerator. Runs after the legacy backfills, so a
        `run` entry verifies at assigned=0. Serve-only skips; failure degrades to silence."""
        if os.environ.get("AKASHA_SERVE_ONLY", "").strip().lower() not in ("", "0", "no", "false", "off"):
            return

        def _run():
            from lib.akasha import lifecycle
            try:
                deadline = time.time() + 1800
                while time.time() < deadline:
                    if lifecycle.is_shutting_down():
                        return
                    if self._relations_ready():
                        break
                    time.sleep(5)
                if lifecycle.is_shutting_down():
                    return
                self.dispatch({"jsonrpc": "2.0", "method": "hydrate.boot_pass",
                               "params": {"client_id": "system.librarian", "data": {}}, "id": "hydb"},
                              TRUST_INTERNAL)
            except Exception as exc:
                logger.debug("[hydrate] boot pass skipped: %s", exc)

        import threading as _thr
        _thr.Thread(target=_run, name="hydrate-boot", daemon=True).start()

    def _init_artifact_store(self) -> None:
        """S1-b §2.2 — build the artifact store's durable backend, negotiate its capabilities against
        the tier's requirement, and emit ONE `[store] backend=<name> caps=… missing=… → writer|read-only`
        line (like `[vision] roster`). The default backend is the local filesystem under
        `<base_dir>/store` — it proves the full writer capability set; a backend that cannot CAS + lease
        is admitted as a reader but REFUSED as a writer (the single-writer invariant, §2.5). This store
        is the NEW accelerator/generation layer; it does not replace Silica (the canonical store)."""
        try:
            from lib.akasha import storage as _st
            root = os.path.join(self.base_dir, "store")
            durable = _st.LocalDurableStore(root)
            caps = durable.capabilities()
            required = self._store_required_caps()
            admitted, missing = _st.check_backend(caps, required)
            role = "writer" if admitted else "read-only"
            artifact = _st.SemanticArtifactStore(durable)
            self.durable_store = durable
            self.artifact_store = artifact
            _st.set_active_store(artifact, durable, role, durable.name, missing)
            logger.info("[store] backend=%s %s missing=%s → %s",
                        durable.name, caps, ",".join(missing) or "-", role)
            if not admitted:
                logger.warning("[store] backend=%s cannot be a writer (missing %s) — running read-only",
                               durable.name, ",".join(missing))
        except Exception as exc:
            logger.warning("[store] artifact store init skipped: %s", exc)

    def _store_required_caps(self) -> list:
        """The capabilities the tier REQUIRES of its writer store — from `config/tier_policy.json`
        `store.requires`, else the writer default (CAS + versioning + leases)."""
        from lib.akasha.storage import WRITER_REQUIRED
        try:
            _tp = _api.hook(self, "tier_policy")
            pol = (_tp() if _tp else None) or {}
            req = ((pol.get("store") or {}).get("requires"))
            if isinstance(req, list) and req:
                return req
        except Exception:
            pass
        return list(WRITER_REQUIRED)

    def _log_iam_refused(self, client_id: str, method: str) -> None:
        """F58 1B.2 — a refused identity must be visible from the WRITER's log too (until now the
        portal saw the -32001 but the writer logged nothing, so an anonymous-refused portal was
        invisible in system.log). Throttled to once per (identity, method) per hour so a hammering
        client cannot flood the log; the table is bounded (R7)."""
        try:
            now = time.time()
            key = (client_id, method)
            tbl = getattr(self, "_iam_refuse_log", None)
            if tbl is None:
                tbl = self._iam_refuse_log = {}
            if now - tbl.get(key, 0.0) >= 3600.0:
                tbl[key] = now
                if len(tbl) > 512:                          # bound: drop the oldest 128
                    for _k in sorted(tbl, key=tbl.get)[:128]:
                        tbl.pop(_k, None)
                logger.warning("[iam] refused identity=%s method=%s series=%s",
                               client_id, method, self.series)
        except Exception:
            pass

    @property
    def jcl_worker(self):
        """Read-only view onto Harmonia's JCL executor (job submission goes through
        `self.harmonia.submit_job`, not this)."""
        return self.harmonia.jcl if self.harmonia else None

    # ------------------------------------------------------------------
    # Boot-time ontology loader
    # ------------------------------------------------------------------


    # ── public-experiment broadcast relay (society.broadcast.*) ──────────────────────


    def _router_class(self, prefix: str):
        """The Concept Model class registered under `prefix` by any manifest-declared router, or None."""
        for _router in self.api.routers:
            cls = _router.get_class(prefix)
            if cls is not None:
                return cls
        return None

    def _start_thread_units(self) -> None:
        """Start every manifest-declared host-bound THREAD unit (feed poller, station, relay, …) in
        manifest order. Each starter is idempotent and gates on its own opt-out / persisted switch;
        a starter that raises is logged at debug and skipped, as the launcher's per-unit calls did.
        Called by the launcher once svc:cell is recorded; the launcher names no unit (backend layout
        order 2026-09-20)."""
        for name, _wanted, _attr, start in self.api.schedules.units():
            try:
                start(self)
            except Exception as exc:
                logger.debug("[Boot] %s not started: %s", name, exc)

    def _schedule_thread_guard(self) -> None:
        """F22 — the owning interpreter's self-heal for host-bound THREAD units (which the process
        Supervisor correctly cannot respawn: only this interpreter can restart its own threads). A
        light daemon: every ~60 s, RE-CREATE any thread unit that should be on but has died, via its
        idempotent starter, with one WARNING. Alive-but-stale is NOT killed here (no safe kill exists)
        — that is left to the Supervisor's stale-heartbeat log plus the feed-poll tick's per-stage
        timing (which now names the slow stage). Idempotent; started from the convergence."""
        if getattr(self, "_thread_guard_thread", None) and self._thread_guard_thread.is_alive():
            return
        import threading
        from lib.akasha import lifecycle
        interval = float(os.environ.get("AKASHA_THREAD_GUARD_INTERVAL", "60") or 60)
        # (wanted-predicate, thread-attr, idempotent-starter, unit-name) — declared by the manifests
        units = [((lambda w=w: w(self)), attr, (lambda st=st: st(self)), name)
                 for name, w, attr, st in self.api.schedules.units()]

        def _run():
            while not lifecycle.is_shutting_down():
                for _wanted, _attr, _starter, _name in units:
                    try:
                        if not _wanted():
                            continue
                        th = getattr(self, _attr, None)
                        if not (th and th.is_alive()):
                            _starter()
                            logger.warning("[Kernel] thread unit '%s' died — re-created", _name)
                    except Exception as exc:
                        logger.info("[Kernel] thread guard '%s' tick error (non-fatal): %s", _name, exc)
                for _ in range(int(max(2, interval) // 2)):
                    if lifecycle.is_shutting_down():
                        break
                    time.sleep(2)

        th = threading.Thread(target=_run, name="thread-guard", daemon=True)
        self._thread_guard_thread = th
        th.start()
        logger.info("[Kernel] thread guard started (interval=%.0fs, %d units)", interval, len(units))

    # ── live-telemetry auto-fetch scheduler (feed.*) ─────────────────────────────


    def _feed_poll_off_path(self) -> str:
        """The persisted opt-out sentinel: present ⇒ the poller is OFF across restarts (set by
        `feed.poll off` from the prompt). A filesystem sentinel, like the other restart-skip flags."""
        d = os.path.join(self.base_dir, "central", "sentinels")
        try:
            os.makedirs(d, exist_ok=True)
        except Exception:
            pass
        return os.path.join(d, "feed_poll.off")







                                      # waits the SAME so seal-rate == play-rate stays synced



























































    def _arm_boot_flood_pacing(self) -> None:
        """Keep the daemon interactively responsive WHILE the ontology loads.

        Root cause of the 'CLI takes 5 min / portal never renders' boot: the single writer + the
        CPU-bound boot weave saturate the GIL, so the O(1) interactive dispatch — the CLI's
        `sys.ping` and the portal's forwarded `session.guest.create`/`auth.verify` (SplitGateway
        sends every write/auth to this primary) — cannot get a slice for the whole load window, on
        a multi-core VPS just as on a small box. Turning on WriteQueue boot-flood pacing cedes a
        sliver of CPU after every boot write so those interactive threads are serviced promptly.

        Self-clearing: a tiny watcher drops the flood once the GLOBAL relations phase is complete
        (the load has settled — the atom + relation write burst is done; the remaining weave is
        IDLE-class and covered by steady-state pacing), with a hard cap so the flag can never stick.
        Set AKASHA_WQ_YIELD_MS=0 to disable pacing entirely."""
        try:
            from lib.akasha.jcl import write_queue as _wq
        except Exception:
            return
        _wq.set_boot_flood(True)
        logger.info("[Kernel] Boot-flood pacing ON — daemon stays responsive (CLI ping / portal "
                    "guest) while the ontology loads")

        # Keep the boot heartbeat FRESH for the whole load, so a busy-loading daemon is never
        # mistaken for a WEDGED one and reaped (the false-wedged respawn loop: the launcher /
        # daemon-watchdog reap on 'not answering sys.ping AND boot heartbeat stale'; the heartbeat
        # was cleared at socket-bind, so during the multi-minute load neither signal held and a
        # healthy daemon was killed + respawned hundreds of times, restarting the load each time).
        # The file's mtime is the freshness; we rewrite it every few seconds until the load settles,
        # then clear it so post-load liveness returns to sys.ping. base_dir/central/boot.heartbeat
        # is the same path the launcher reads (akasha._boot_heartbeat_*).
        _hb_path = os.path.join(self.base_dir, "central", "boot.heartbeat")

        def _touch_hb():
            try:
                os.makedirs(os.path.dirname(_hb_path), exist_ok=True)
                with open(_hb_path, "w") as _fh:
                    _fh.write(str(os.getpid()))
            except OSError:
                pass

        def _clear_when_settled():
            from lib.akasha import lifecycle
            _touch_hb()                            # advertise 'alive & loading' immediately
            deadline = time.time() + 1800          # hard cap (30 min) — never let the flag stick
            while time.time() < deadline:
                if lifecycle.is_shutting_down():
                    break
                if self._relations_ready():
                    break
                _touch_hb()                        # every 3 s ≪ the 20 s stale threshold (6× margin)
                time.sleep(3)
            _wq.set_boot_flood(False)
            try:
                os.remove(_hb_path)                # load settled → back to sys.ping liveness
            except OSError:
                pass
            logger.info("[Kernel] Boot-flood pacing OFF + boot heartbeat cleared — load settled")

        import threading
        threading.Thread(target=_clear_when_settled, name="boot-flood-clear", daemon=True).start()



    def _bg_phase_unit(self, unit_id: str, deps=None):
        """Register a one-shot background boot phase as a Supervisor unit so an operator can MONITOR
        it from the CLI (`svc.ls`) — the same management plane feed-poll uses. Returns
        `(update, close)`:

          • `update(state, detail="", **extra)` stamps the unit's health with a heartbeat
            (`last_tick` + `stale_s`), so a phase that HANGS (e.g. a wedged network call) stops
            ticking and shows up STALE in `svc.ls` instead of being an invisible zombie thread.
          • `close()` removes the unit descriptor (registered as a shutdown closer too).

        `restart=NEVER` so the reconcile loop never respawns a finished one-shot. Registration only
        happens when this process is SUPERVISED (svc:cell present — i.e. a --serve/daemon deploy);
        a foreground CLI run gets no-op callbacks (nothing to monitor there). Never raises."""
        import time as _t
        started = _t.time()
        def _mk(state, detail="", **extra):
            h = {"kind": "phase", "state": state, "detail": (detail or None)[:200] if detail else None,
                 "started": round(started, 1), "last_tick": _t.time(),
                 "elapsed_s": round(_t.time() - started, 1), "stale_s": 300}
            h.update(extra)
            return h
        try:
            from lib.harmonia import supervisor as _sv
            if not _sv.read_unit(self.base_dir, "svc:cell"):
                raise RuntimeError("not supervised (foreground) — nothing to monitor")
            _sv.Supervisor(self.base_dir).record_running(
                unit_id, os.getpid(), engine=unit_id.split(":")[-1], grace_s=1.0,
                restart=_sv.RESTART_NEVER, deps=deps or ["svc:cell"],
                substrate=_sv.SUBSTRATE_THREAD, health=_mk("armed"))
            _sv.mark_unit_ready(self.base_dir, unit_id)
        except Exception as exc:
            logger.debug("[Kernel] bg phase unit %s not registered: %s", unit_id, exc)
            def _noop(*a, **k):
                return None
            return _noop, _noop
        def _update(state, detail="", **extra):
            try:
                _sv.update_unit_health(self.base_dir, unit_id, _mk(state, detail, **extra))
            except Exception:
                pass
        _closed = {"v": False}
        def _close():
            if _closed["v"]:
                return
            _closed["v"] = True
            try:
                _sv.remove_unit(self.base_dir, unit_id)
            except Exception:
                pass
        try:
            from lib.akasha import lifecycle
            lifecycle.register_closer(_close)
        except Exception:
            pass
        return _update, _close

    def _relations_ready(self) -> bool:
        """True once the ontology's GLOBAL relations phase has completed — the real
        'load has settled' signal the boot schedulers gate on before writing.

        The relations phase records a PERSISTENT completion alias
        `ont:ak:relations:all:<hash>` in the admin cortex (and, for packs whose files
        changed this boot, per-file `_relfile_*` sentinels); a `_relations_*.done` FS
        marker is ALSO accepted for forward-compat. An earlier gate globbed ONLY
        `_relations_*.done`, which nothing writes — so every scheduler blocked on its full
        ceiling (~2 h) before proceeding, i.e. never appeared to run. This checks the
        marker that actually exists, so the gate opens as soon as the graph is whole."""
        try:
            import glob as _g
            sent_dir = os.path.join(self.base_dir, "central", "sentinels")
            if _g.glob(os.path.join(sent_dir, "_relations_*.done")):
                return True
            s = self.manager.get_session("admin")
            return bool(s.local_cortex.get_aliases_by_pattern("ont:ak:relations:all:%"))
        except Exception:
            return False

    def _schedule_wal_maintenance(self) -> None:
        """R7/F26 — auto-fold the shared nucleus WAL when it grows past a threshold, at idle. The
        cached index removes boot-replay pain for cached openers, but the WAL still grows forever on
        disk: any ram-mode opener still pays a FULL replay, and value preads scatter over an
        ever-longer file. This daemon checkpoints it — writer-only (the nucleus core owns the single
        writer here), gated on (a) the boot load having settled, (b) no JCL job running (idle), and
        (c) WAL bytes over AKASHA_CKPT_THRESHOLD (default 1 GiB). A serving portal replica only reads
        the WAL at open, so folding under it is safe. A threshold of 0 disables it. Silica-only; a no-op on SQLite (no compact/wal_bytes)."""
        try:
            threshold = int(os.environ.get("AKASHA_CKPT_THRESHOLD", "").strip() or (1 << 30))
        except (TypeError, ValueError):
            threshold = 1 << 30
        if threshold <= 0:
            return
        nucleus = getattr(self.manager, "shared_nucleus", None)
        core = getattr(nucleus, "core", None) if nucleus is not None else None
        if core is None or not hasattr(core, "compact") or not hasattr(core, "wal_bytes"):
            return                                     # SQLite / no Silica compact → nothing to do

        def _run():
            from lib.akasha import lifecycle
            # Gate on the relations-complete signal so we never fold mid-boot-load (which competes
            # with the boot import for the store); then poll on a slow cadence.
            deadline = time.time() + 7200
            while time.time() < deadline:
                if lifecycle.is_shutting_down():
                    return
                if self._relations_ready():
                    break
                time.sleep(5)
            _interval = 300.0                          # re-check every ~5 min
            while not lifecycle.is_shutting_down():
                try:
                    wb = core.wal_bytes()
                    # F52 §2 — trigger on GROWTH since the last fold, not total size. A 2.4 GB live
                    # store is already over a 1 GiB total-size threshold, so total-size triggering would
                    # fold a ~90 s near-no-op EVERY generation. Baseline None ⇒ first check re-baselines
                    # to the current (post-replay live) size and does not fold.
                    if KernelDispatcher._wal_last_fold_bytes is None:
                        KernelDispatcher._wal_last_fold_bytes = wb
                    baseline = KernelDispatcher._wal_last_fold_bytes
                    grown = wb - baseline
                    idle = True
                    try:
                        jobs = self.jcl_worker.list_jobs() if self.jcl_worker else []
                        idle = not any(getattr(j, "status", "") == "RUNNING" for j in jobs)
                    except Exception:
                        idle = True
                    if grown > threshold and idle:
                        logger.info("[compact] nucleus WAL %d bytes, grown %d since last fold "
                                    "(baseline=%d) > threshold %d — folding at idle",
                                    wb, grown, baseline, threshold)
                        res = core.compact()
                        try:
                            KernelDispatcher._wal_last_fold_bytes = int(core.wal_bytes())
                        except Exception:
                            KernelDispatcher._wal_last_fold_bytes = res.get("after_bytes")
                        logger.info("[compact] nucleus WAL %d → %d bytes in %.2fs (auto-maintenance; "
                                    "baseline=%d grown=%d new_baseline=%s)",
                                    res.get("before_bytes", 0), res.get("after_bytes", 0),
                                    res.get("seconds", 0.0), baseline, grown,
                                    KernelDispatcher._wal_last_fold_bytes)
                except Exception as exc:
                    logger.warning("[compact] auto-maintenance skipped: %s", exc)
                # Sleep in short slices so shutdown is prompt.
                for _ in range(int(_interval / 0.5)):
                    if lifecycle.is_shutting_down():
                        return
                    time.sleep(0.5)

        import threading as _thr
        _thr.Thread(target=_run, name="wal-maintenance", daemon=True).start()


    def _schedule_world_genesis(self) -> None:
        """G0.3 — create the shared `world:default` (the commons: world atom + its own clock, through
        the platform's `WorldAxis`) on the WRITER, ONCE per deploy, serve-first, behind a fsync'd sentinel (cryptobiosis —
        never rewritten). Runs on EVERY series/tier — the world model is public foundation, no config
        gate — and is independent of the ontology load (it writes two atoms). R0: no operator command.
        On a single-store edge cell the commons ops write to the local cortex with the universal scope."""
        if os.environ.get("AKASHA_SERVE_ONLY", "").strip().lower() not in ("", "0", "no", "false", "off"):
            return  # only the sole nucleus writer runs genesis
        nucleus = getattr(self.manager, "shared_nucleus", None)
        # nucleus may be None on a single-store cell — genesis still runs (writes to the local cortex).

        def _run():
            from lib.akasha import lifecycle
            _hb = os.path.join(self.base_dir, "central", "boot.heartbeat")     # serve-first
            _dl = time.time() + 900
            while time.time() < _dl and os.path.exists(_hb):
                if lifecycle.is_shutting_down():
                    return
                time.sleep(2)
            if lifecycle.is_shutting_down():
                return
            try:
                sent_dir = os.path.join(self.base_dir, "central", "sentinels")
                os.makedirs(sent_dir, exist_ok=True)
                done = os.path.join(sent_dir, "world_default.done")
                if os.path.exists(done):
                    return
                # The commons is the PLATFORM's: its society, benches and workflow write their
                # records onto this axis, so it exists whatever application is installed.
                from lib.akasha.api.concepts import WorldAxis
                from lib.akasha.jcl.workspace_context import system_context as _sys_ctx
                with _sys_ctx():
                    res = WorldAxis(self.manager.get_session("system.librarian")).genesis() or {}
                try:
                    with open(done, "w") as _f:
                        _f.write("1"); _f.flush(); os.fsync(_f.fileno())
                except OSError:
                    pass
                _wall = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                if res.get("status") == "created":
                    logger.info("[world] genesis world:default created clock=%s at=%s",
                                res.get("clock"), _wall)
                else:
                    logger.info("[world] genesis world:default present (clock=%s)", res.get("clock"))
            except Exception as exc:
                logger.debug("[world] genesis skipped: %s", exc)

        import threading as _thr
        _thr.Thread(target=_run, name="world-genesis", daemon=True).start()

    # ── G3.7 — the auto-execution driver (writer-role daemon) ──────────────────────
    def _writer_boot_id(self) -> str:
        """A33 — a stable id for THIS writer boot (process lifetime): pid + init time. It changes on
        every restart / new-build respawn, so `trigger: boot` can tell 'already ran this boot' from
        'a fresh boot' — the persisted autorun state alone cannot (it survives restarts)."""
        bid = getattr(self, "_wbid", None)
        if bid is None:
            bid = self._wbid = "%d:%d" % (os.getpid(), int(getattr(self, "_boot_wall", time.time())))
        return bid

    def _build_fp(self) -> str:
        """The build content-fingerprint (D1, akasha_build.json) — lets the driver tell a NEW BUILD
        from a plain restart when it resets the boot gate. '' when unavailable."""
        fp = getattr(self, "_bfp_cache", None)
        if fp is None:
            fp = ""
            try:
                proj = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                with open(os.path.join(proj, "akasha_build.json"), "r", encoding="utf-8") as f:
                    fp = str((json.load(f) or {}).get("content_fingerprint") or "")
            except Exception:
                fp = ""
            self._bfp_cache = fp
        return fp

















    # ── Provisioning framework (interface contract v1) ─────────────────────────────







    # ── Seed-time autonomy §2.1/§2.2 — source packs imported at boot ────────────────





    def _is_method_known(self, method: str) -> bool:
        """Best-effort: is a method routable on this cell? Used to gate §2.2 boot acquisition so an
        unknown fetcher `kind` is a wait, not an error storm."""
        try:
            from lib.akasha import kernel_methods as _km
            if method in getattr(_km, "METHOD_TO_ACTION", {}):
                return True
        except Exception:
            pass
        try:
            from api.router import COMMAND_SPECS as _cs
            return method in _cs
        except Exception:
            return False

    def _write_sentinel(self, path: str, body: str = "1") -> None:
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(body); f.flush(); os.fsync(f.fileno())
        except OSError:
            pass





    def _schedule_backlog_gc(self, name: str, method: str, vault_ns: str, log_tag: str) -> None:
        """F55 — a shared writer-side, boot-if-behind retention job (memory-discipline R5). Runs the
        given HARD-eviction `method` (feed.gc / society.broadcast.gc) on the writer daemon: it LOOPS
        the op while `truncated` (draining the existing backlog in bounded passes, yielding between
        passes so it never blocks interactive work), records the UTC day in the vault, and thereafter
        re-runs once per day rollover. The web-portal process respawns every deploy so it can never
        live across midnight — the long-lived writer is the right home, exactly like pulse.compact."""
        nucleus = getattr(self.manager, "shared_nucleus", None)
        if nucleus is None:
            return

        def _run():
            from lib.akasha import lifecycle
            deadline = time.time() + 7200
            while time.time() < deadline:
                if lifecycle.is_shutting_down():
                    return
                if self._relations_ready():
                    break
                time.sleep(5)
            while not lifecycle.is_shutting_down():
                try:
                    today = time.strftime("%Y-%m-%d", time.gmtime())
                    last = nucleus.vault_retrieve(vault_ns, "last_gc_day") or ""
                    if today != last:
                        # Drain the backlog in bounded passes (each returns truncated while more
                        # remains). Dispatched as the system librarian (holds write + role:librarian
                        # for the nucleus mirror/telemetry) over INTERNAL trust. Idempotent. A56 §4 —
                        # the whole drain is ONE gated, serialised maintenance task.
                        def _drain():
                            total = passes = 0
                            for _ in range(400):             # hard ceiling on passes per rollover
                                if lifecycle.is_shutting_down():
                                    return total, passes
                                resp = self.dispatch({"jsonrpc": "2.0", "method": method,
                                                      "params": {"client_id": "system.librarian",
                                                                 "data": {}}, "id": "gc"}, TRUST_INTERNAL)
                                res = (resp or {}).get("result") or {}
                                passes += 1
                                total += int(res.get("dropped") or 0)
                                if not res.get("truncated"):
                                    break
                                for _s in range(20):         # yield ~10 s between passes (interruptible)
                                    if lifecycle.is_shutting_down():
                                        return total, passes
                                    time.sleep(0.5)
                            return total, passes
                        _res = _run_gated_maint(log_tag, _drain)
                        if _res is None:                     # gate skipped / shutting down — retry later
                            for _ in range(int(3600 / 0.5)):
                                if lifecycle.is_shutting_down():
                                    return
                                time.sleep(0.5)
                            continue
                        total, passes = _res
                        nucleus.vault_store(vault_ns, "last_gc_day", today)
                        logger.info("[%s] retention swept (writer) — dropped=%d passes=%d",
                                    log_tag, total, passes)
                except Exception as exc:
                    logger.debug("[%s] retention check skipped: %s", log_tag, exc)
                for _ in range(int(3600 / 0.5)):             # re-check ~hourly for a day rollover
                    if lifecycle.is_shutting_down():
                        return
                    time.sleep(0.5)

        import threading as _thr
        _thr.Thread(target=_run, name=name, daemon=True).start()





    def _schedule_cache_replan(self) -> None:
        """Semantic macro-cache — author the residency plan (set:stage:cache_plan) from the curated
        seed (set:stage:featured), on the WRITER (nucleus writes) — like pulse.compact, boot-if-behind.
        Replans ONCE shortly after boot (so the plan reflects the current featured set + pulse demand)
        and thereafter on each UTC day rollover. Self-gating: cache.replan returns {active:False} and
        does nothing when there is no featured seed, so on a non-curated cell this daemon is a cheap
        no-op. The portal-side warm daemon reads the plan set this authors.

        A4 (R0 — ignition is a consequence of boot, never of a command or a calendar). Hardened:
          (a) HONESTY — when the internal cache.replan carries an error, log `[semcache] replan REFUSED:
              <code> <message>` at WARNING and record it on the counters (surfaced by cache.plan /
              Health) — never the old silent `atoms=None seed=None` line;
          (b) READINESS — gate the first replan on the SAME condition the §12.5 featured seeder uses
              (relations ready + boot heartbeat cleared, serve-first), and — on a tier that ships the
              featured config — wait for the seeder's sentinel so the first replan sees a NON-EMPTY seed
              rather than racing ahead of the seed and returning inactive;
          (c) RETRY — on failure, retry with backoff (60 s ×5) and do NOT advance last_replan_day or
              clear `first`, so a failed first replan is retried (hourly thereafter) and never costs a day;
          (d) COUNTERS — the last SUCCESSFUL replan + `last_error` live on cache.semcache_counters()."""
        nucleus = getattr(self.manager, "shared_nucleus", None)
        if nucleus is None:
            return

        def _replan_once():
            """Dispatch one cache.replan as the boot librarian. Returns (ok, active, res); on an error
            response it is HONEST — records the refusal on the counters and logs it at WARNING (A4(a))."""
            # A56 §4 — semcache.replan is part of the serialised nightly sequence, not a parallel
            # timer; run it behind the shared memory/queue gate so it never overlaps a GC sweep.
            resp = _run_gated_maint("semcache.replan", lambda: _with_rss_delta(
                "semcache.replan", lambda: self.dispatch(   # A48.3
                    {"jsonrpc": "2.0", "method": "cache.replan",
                     "params": {"client_id": "system.librarian", "data": {}}, "id": "cr"}, TRUST_INTERNAL),
                concurrent=self._concurrent_jobs))
            if resp is None:                          # gate skipped / shutting down
                return False, None, {}
            err = (resp or {}).get("error")
            if err:
                if isinstance(err, dict):
                    msg = "%s %s" % (err.get("code"), err.get("message"))
                else:
                    msg = str(err)
                try:
                    _rre = _api.hook(self, "cache_replan_error")
                    _rre and _rre(msg)
                except Exception:
                    pass
                logger.warning("[semcache] replan REFUSED: %s", msg)
                return False, None, {}
            res = (resp or {}).get("result") or {}
            return True, (res.get("active") is not False), res

        def _run():
            from lib.akasha import lifecycle
            deadline = time.time() + 7200
            while time.time() < deadline:
                if lifecycle.is_shutting_down():
                    return
                if self._relations_ready():
                    break
                time.sleep(5)
            if lifecycle.is_shutting_down():
                return
            # (b) readiness — serve-first: wait out the boot heartbeat like the featured seeder.
            _hb = os.path.join(self.base_dir, "central", "boot.heartbeat")
            _dl = time.time() + 900
            while time.time() < _dl and os.path.exists(_hb):
                if lifecycle.is_shutting_down():
                    return
                time.sleep(2)
            # (b) ordering — if this tier ships the §12.5 featured config, let the seeder plant the set
            # first (wait for its run-once sentinel) so the first replan never sees an empty seed.
            _pdir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            if os.path.exists(os.path.join(_pdir, "config", "semcache_featured.json")):
                _sent = os.path.join(self.base_dir, "central", "sentinels", "semcache_featured_v1.done")
                _sdl = time.time() + 300
                while time.time() < _sdl and not os.path.exists(_sent):
                    if lifecycle.is_shutting_down():
                        return
                    time.sleep(2)
            first = True
            while not lifecycle.is_shutting_down():
                try:
                    today = time.strftime("%Y-%m-%d", time.gmtime())
                    last = nucleus.vault_retrieve("cache", "last_replan_day") or ""
                    if first or today != last:
                        ok, active, res = _replan_once()
                        if not ok:
                            # (c) retry — 60 s ×5 backoff; do NOT advance the day / clear `first`, so a
                            # failed first replan is retried now and hourly, never costing a full day.
                            for _n in range(5):
                                for _s in range(120):        # 60 s, interruptible
                                    if lifecycle.is_shutting_down():
                                        return
                                    time.sleep(0.5)
                                ok, active, res = _replan_once()
                                if ok:
                                    break
                        if ok:
                            nucleus.vault_store("cache", "last_replan_day", today)
                            first = False
                            if active:
                                logger.info("[semcache] plan authored (writer) — atoms=%s seed=%s "
                                            "expanded=%s budget_used=%s%%", res.get("atoms"),
                                            res.get("seed"), res.get("expanded"),
                                            res.get("budget_used_pct"))
                            else:
                                logger.info("[semcache] no curated seed (set:stage:featured empty) — "
                                            "semantic cache stays OFF on this cell")
                except Exception as exc:
                    logger.debug("[semcache] replan check skipped: %s", exc)
                for _ in range(int(3600 / 0.5)):        # re-check ~hourly for a day rollover
                    if lifecycle.is_shutting_down():
                        return
                    time.sleep(0.5)

        import threading as _thr
        _thr.Thread(target=_run, name="cache-replan", daemon=True).start()

    def _dump_memtop(self, rss, reason=""):
        """F44-A1.2/A1.3 — one MemTop report: the largest in-memory Python containers, the Silica
        index attributed per `@`route, AND the guest-cell footprint (A1.3). Shared by the boot
        heartbeat (one-shot at AKASHA_MEMTOP_MB) and the permanent health heartbeat (at the 4 GB and
        6 GB high-water marks) so the accumulator names itself in the log with no operator step."""
        try:
            import gc as _gc, sys as _sys
            _big = []
            for _o in _gc.get_objects():
                try:
                    _tn = type(_o).__name__
                    if _tn in ("list", "dict", "set", "tuple", "bytearray", "frozenset"):
                        _n = len(_o)
                        if _n >= 50000:
                            _big.append((_n, _tn, _sys.getsizeof(_o)))
                except Exception:
                    continue
            _big.sort(reverse=True)
            logger.warning("[MemTop] rss=%dMB (%s) — largest in-memory containers "
                           "(a store meant for disk should have NONE this big):", rss, reason or "hw")
            for _n, _tn, _sz in _big[:10]:
                logger.warning("[MemTop]   %-9s len=%-10d shallow=%dKB", _tn, _n, _sz // 1024)
            if not _big:
                logger.warning("[MemTop]   (no oversized Python container — RSS is likely "
                               "SQLite/native, e.g. mmap/page-cache)")
            # Silica index attributed per @route (RAM-resident bookkeeping structures).
            try:
                _nuc = getattr(self.manager, "shared_nucleus", None)
                _ncore = getattr(_nuc, "core", None) if _nuc else None
                if _ncore is not None and hasattr(_ncore, "route_sizes"):
                    _rs = _ncore.route_sizes()
                    _ats = _rs.get("at_routes") or []
                    if _ats:
                        logger.warning("[MemTop] Silica index by @route (RAM-resident bookkeeping):")
                        for _rt, _cnt, _by in _ats[:10]:
                            _name = _rt.decode("ascii", "replace") \
                                if isinstance(_rt, (bytes, bytearray)) else str(_rt)
                            logger.warning("[MemTop]   %-12s entries=%-9d ~%dMB",
                                           _name, _cnt, _by // (1 << 20))
                        _oth = _rs.get("other_routes") or {}
                        logger.warning("[MemTop]   %-12s entries=%-9d ~%dMB (hash-routed atom bodies)",
                                       "@chunks", _oth.get("count", 0),
                                       _oth.get("bytes", 0) // (1 << 20))
            except Exception as _rsx:
                logger.warning("[MemTop] route-size attribution skipped: %s", _rsx)
            # A1.3 — guest-cell footprint: how many private cortices are live and their on-disk
            # size, so a leaking guest economy (many cells, each with its own silica store) is
            # visible in the same report rather than hidden behind the aggregate RSS.
            try:
                _mgr = getattr(self, "manager", None)
                _gp = getattr(_mgr, "guest_pool", None)
                _gs = _gp.stats() if _gp is not None else {}
                _base = getattr(_mgr, "base_dir", None)
                _cells_dir = os.path.join(_base, "cells") if _base else None
                _disk_mb = None
                _ncells = None
                if _cells_dir and os.path.isdir(_cells_dir):
                    _tot = 0
                    _ncells = 0
                    for _entry in os.scandir(_cells_dir):
                        if _entry.is_dir():
                            _ncells += 1
                    for _dp, _dn, _fn in os.walk(_cells_dir):
                        for _f in _fn:
                            try:
                                _tot += os.path.getsize(os.path.join(_dp, _f))
                            except OSError:
                                pass
                    _disk_mb = _tot // (1 << 20)
                logger.warning("[MemTop] guest cells: in_use=%s pool_size=%s on_disk_dirs=%s on_disk=%s",
                               _gs.get("in_use", "?"), _gs.get("pool_size", "?"),
                               _ncells if _ncells is not None else "?",
                               ("%dMB" % _disk_mb) if _disk_mb is not None else "?")
            except Exception as _gx:
                logger.warning("[MemTop] guest-cell footprint skipped: %s", _gx)
        except Exception as _mtx:
            logger.warning("[MemTop] scan failed: %s", _mtx)

    def _schedule_health_heartbeat(self) -> None:
        """F44-A1.1 — a PERMANENT once-a-minute health line that NEVER turns off (unlike BootWatch,
        which is bounded to the boot window and stops at settle). Every line names the four quantities
        that together tell an accumulator from a spike: rss / MemAvailable (host pressure), live guest
        cells (the per-client economy), dive admitted+refused (the F39 admission valve), and pulse
        emits vs bulk summaries (the F44-C write source). Because the OOM was intermittent and silent,
        the LAST minute-line before a kill is the post-mortem. It also fires a MemTop dump the first
        time RSS crosses the 4 GB and 6 GB high-water marks (A1.2/A1.3)."""
        if getattr(self, "_heartbeat_running", False):
            return
        self._heartbeat_running = True

        def _hw_marks():
            raw = os.environ.get("AKASHA_HEARTBEAT_MEMTOP_MB", "4096,6144")
            marks = []
            for tok in raw.split(","):
                try:
                    marks.append(int(tok.strip()))
                except (TypeError, ValueError):
                    continue
            return sorted(m for m in marks if m > 0) or [4096, 6144]

        def _run():
            from lib.akasha import lifecycle
            marks = _hw_marks()
            fired = set()
            _t0 = time.time()
            _peak_rss = 0                            # A53 item 6 — process-lifetime RSS high-water
            while not lifecycle.is_shutting_down():
                rss = _rss_mb()
                if rss is not None:
                    _peak_rss = max(_peak_rss, rss)
                    avail = _mem_available_mb()
                    try:
                        _gp = getattr(getattr(self, "manager", None), "guest_pool", None)
                        _cells = _gp.stats().get("in_use", "?") if _gp is not None else "?"
                    except Exception:
                        _cells = "?"
                    _adm = _DIVE_ADMISSION.stats()
                    try:
                        _pec = _api.hook(self, "pulse_counters")
                        _pe = (_pec() if _pec else None) or {}
                    except Exception:
                        _pe = {"emits": "?", "bulk": "?"}
                    try:
                        _scf = _api.hook(self, "semcache_counters")
                        _sc = _scf() if _scf else {}
                    except Exception:
                        _sc = {}
                    # F57 §2.2 — human byte format: KB under 10 MB, one-decimal MB above, so a small
                    # plan (est_bytes≈1 MB) reads as `≈984KB`, never a misleading `0MB`.
                    _scb_raw = int(_sc.get("bytes", 0) or 0)
                    _scb = ("%dKB" % (_scb_raw // 1024) if _scb_raw < 10 * 1024 * 1024
                            else "%.1fMB" % (_scb_raw / (1024 * 1024)))
                    _threads = _thread_count()
                    _anon, _fmap = _smaps_rollup()      # F49-3 — heap vs mapped-file split
                    # The workload layer's own segment, through the `workload_health_segment` hook —
                    # what produced output today, whether anything is standing by and why, and what
                    # the driver is doing. It was two fields the heart authored, one of which named a
                    # single programme and one of which read a kernel attribute; both are workload
                    # facts, and the heart composes a line it does not author (order §3).
                    _wl = ""
                    try:
                        _whs = _api.hook(self, "workload_health_segment")
                        _wl = _whs(self) if _whs else ""
                    except Exception:
                        _wl = ""
                    # A23 — while a source pack is importing (the ~2 h boot import), show it here so the
                    # multi-hour gap between "daemons started" and "imported" is visible; absent otherwise.
                    _sps = getattr(self, "_source_pack_status", None)
                    _packs = (" packs(importing=%s %s/%s)" % (_sps.get("pool"), _sps.get("n"),
                              _sps.get("total") if _sps.get("total") is not None else "?")) if _sps else ""
                    try:
                        import api.portals.cell_ipc as _ipc_mod
                        _ipc = _ipc_mod.server_stats()
                    except Exception:
                        _ipc = {}
                    # A57-b — the aggregate rate of semantic.search truncation (no per-call INFO for the
                    # cap case); shown only once either counter is non-zero so a quiet cell stays clean.
                    _srch = ""
                    if _SEARCH_PARTIAL["cap"] or _SEARCH_PARTIAL["budget"]:
                        _srch = " search(partial cap=%d budget=%d)" % (
                            _SEARCH_PARTIAL["cap"], _SEARCH_PARTIAL["budget"])
                    # B10 — the shared LLM pool for the active provider; empty until the pool has
                    # activity today (the empty-string-when-absent idiom, like packs/search).
                    _llm = ""
                    try:
                        _lhs = _api.hook(self, "llm_health_segment")
                        _act = _api.hook(self, "llm_active_provider")
                        _llm = _lhs(_act(self)) if (_lhs and _act) else ""
                    except Exception:
                        _llm = ""
                    logger.info("[Health] rss=%dMB peak_rss=%dMB anon=%sMB fmap=%sMB avail=%sMB threads=%s "
                                "ipc(pool=%s q=%s refused=%s) guests=%s dive(admit=%s refuse=%s) "
                                "pulse(seen=%s emit=%s bulk=%s miss=%s rej=%s) "
                                "semcache(plan=%s bytes≈%s age=%ss)%s%s%s%s up=%.0fs",
                                rss, _peak_rss, _anon if _anon is not None else "?",
                                _fmap if _fmap is not None else "?",
                                avail if avail is not None else "?",
                                _threads if _threads is not None else "?",
                                _ipc.get("pool", "-"), _ipc.get("queued", "-"), _ipc.get("refused", "-"),
                                _cells, _adm.get("admitted"), _adm.get("refused"),
                                _pe.get("seen"), _pe.get("emits"), _pe.get("bulk"),
                                _pe.get("miss"), _pe.get("rejected"),
                                _sc.get("plan", 0), _scb,
                                _sc.get("plan_age") if _sc.get("plan_age") is not None else "-",
                                _wl, _packs, _srch, _llm, time.time() - _t0)
                    for m in marks:
                        if m not in fired and rss >= m:
                            fired.add(m)
                            logger.warning("[Health] RSS crossed %dMB high-water mark — MemTop:", m)
                            self._dump_memtop(rss, reason="hw>%dMB" % m)
                for _ in range(120):                     # ~60s, but wake promptly on shutdown
                    if lifecycle.is_shutting_down():
                        return
                    time.sleep(0.5)
            self._heartbeat_running = False

        import threading as _thr
        _thr.Thread(target=_run, name="health-heartbeat", daemon=True).start()







    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def dispatch(self, payload: dict, transport_trust: str = TRUST_NETWORK) -> dict:
        """
        Unified JSON-RPC 2.0 entry point.
        Every shell portal calls this and only this.

        transport_trust is supplied by the calling portal (never by the client)
        and defaults to the safe TRUST_NETWORK.  See the trust-level constants.
        """
        if not isinstance(payload, dict) or payload.get("jsonrpc") != "2.0" or "method" not in payload:
            return _err(payload.get("id") if isinstance(payload, dict) else None,
                        -32600, "Invalid Request: not valid JSON-RPC 2.0")

        rid = payload.get("id", str(uuid.uuid4()))
        method: str = payload["method"]
        params = payload.get("params", {})
        # A29 — positional JSON-RPC params (a LIST, e.g. a scanner's `getVersion`/`getHealth` probe) are
        # not supported by design; without this guard a non-dict `params` reached `params.get(...)` in
        # `_authenticated_dispatch` and raised AttributeError → an ugly traceback in the writer log for
        # every drive-by scan. Answer -32602 cleanly instead.
        if not isinstance(params, dict):
            return _err(rid, -32602, "Invalid params: object (named) params required; "
                                     "positional/array params are not supported")

        # F47-S1 — stamp pulse capture's true state at this choke point (every emit that reaches the
        # writer, success OR reject), so the Health line answers world-a/world-b definitively.
        _is_pulse = method in ("pulse.emit", "pulse.emit_bulk")

        def _note_pulse(ok):
            if _is_pulse:
                try:
                    _nd = _api.hook(self, "pulse_note_dispatch")
                    _nd and _nd(ok)
                except Exception:
                    pass

        try:
            resp = self._authenticated_dispatch(method, params, rid, transport_trust)
            _note_pulse(not (isinstance(resp, dict) and resp.get("error")))
            return resp
        except PermissionError as e:
            _note_pulse(False)
            return _err(rid, -32001, f"Permission Denied: {e}")
        except Exception as e:
            _note_pulse(False)
            logger.error(f"[Kernel] Unhandled error in dispatch: {e}", exc_info=True)
            return _err(rid, -32000, f"Internal Kernel Error: {e}")

    # ------------------------------------------------------------------
    # Auth + session resolution
    # ------------------------------------------------------------------

    def _authenticated_dispatch(self, method: str, params: dict, rid: str,
                                transport_trust: str = TRUST_NETWORK) -> dict:
        # Raw token as supplied by the transport layer (HTTP header or RPC param).
        # Akasha does not trust the transport; this value is opaque until resolved.
        raw_token: str = params.get("session_token") or params.get("client_id") or "anonymous"
        trusted = transport_trust in _TRUSTED_TRANSPORTS
        data = params.get("data", {})
        # S2-c — a dict `params` may still carry a LIST-shaped (or otherwise non-object) `data` (a
        # malformed client / scanner probe). `{**_top, **data}` below and every handler's `data.get(...)`
        # assume a dict, so a list `data` raised → -32000 traceback in the writer log. Coerce to {}.
        if not isinstance(data, dict):
            return _err(rid, -32602, "Invalid params: 'data' must be an object (named) — "
                                     "array/positional data is not supported")
        # Merge any top-level non-auth params into data so concept registry
        # handlers receive them regardless of nesting style used by the caller.
        # Nested data keys take priority over same-named top-level keys.
        _top = {k: v for k, v in params.items()
                if k not in ("session_token", "client_id", "data")}
        if _top:
            data = {**_top, **data}

        # Ops that run before a session exists (ping, status, genesis, auth.*, guest sessions) —
        # stage `pre_identity` in the manifests.
        req = _Req(rid=rid, method=method, data=data, raw_token=raw_token,
                   transport_trust=transport_trust)
        _e = self.api.ops.resolve(method, "pre_identity")
        if _e is not None:
            return _e.call(self, req)

        # ── Identity resolution ──────────────────────────────────────────────
        # The identity is resolved from the token, never asserted by a bare
        # client_id over an untrusted transport.  Four cases:
        if self.iam.guest_bindings.is_guest_key(raw_token):
            # gbk: signed guest binding → an Akasha-internal "guest:" session id.
            try:
                client_id = self.iam.guest_bindings.resolve(raw_token)
                role      = self.iam.authenticate(client_id)
            except PermissionError as e:
                return _err(rid, -32001, str(e))
            # Renew the pool slot timer so the sweeper doesn't reclaim an active
            # visitor's session mid-use.
            self.manager.touch_guest_session(client_id)
        elif self.iam.guest_bindings.is_auth_key(raw_token):
            # akt: signed session token — proof of identity on ANY transport.
            try:
                client_id, role = self.iam.resolve_session_token(raw_token)
            except PermissionError as e:
                return _err(rid, -32001, str(e))
        elif trusted:
            # Trusted transport (local console / internal): a bare client_id may
            # assert an identity — the OS/process boundary is the real gate.
            client_id = raw_token
            if self.iam.is_system_identity(client_id) and transport_trust != TRUST_INTERNAL:
                return _err(rid, -32001, "System identities are internal-only.")
            try:
                role = self.iam.authenticate(client_id)
            except PermissionError as e:
                self._log_iam_refused(client_id, method)                  # F58 1B.2
                return _err(rid, -32001, str(e))
        else:
            # Untrusted network transport with a bare (unsigned) identity claim.
            # Resolve it, but accept ONLY an anonymous GUEST.  A known privileged
            # identity MUST present a signed akt: token (obtained via auth.verify)
            # — this closes the "the username is the credential" bypass.
            try:
                role = self.iam.authenticate(raw_token)
            except PermissionError as e:
                self._log_iam_refused(raw_token or "anonymous", method)   # F58 1B.2
                return _err(rid, -32001, str(e))
            if role != Role.GUEST:
                return _err(rid, -32001,
                            "This identity requires a signed session token over the "
                            "network. Call auth.verify to obtain one.")
            client_id = raw_token

        # Ops that need the RESOLVED identity but no capability (whoami) — stage `post_identity`.
        req.client_id, req.role = client_id, role
        _e = self.api.ops.resolve(method, "post_identity")
        if _e is not None:
            return _e.call(self, req)

        # Map full RPC method names to the capability action tokens IAM understands.
        # A method with no capability mapping (and not one of the capability-free built-ins
        # authorize() accepts directly) has no handler here — it is genuinely
        # unimplemented, so return -32601 (Method not found), NOT -32001 (permission), so a
        # client can tell "not built yet" apart from "not allowed". Pre-auth methods
        # (auth.*, session.guest.*, sys.ping/status) were already handled above.
        action = _METHOD_TO_ACTION.get(method)
        if action is None:
            if method not in ("echo", "help", "status", "ping"):
                return _err(rid, -32601, f"Method not found: {method}")
            action = method
        # THE GATE (§0/§6). The boundary asks the ACTION; the op asks again with its target.
        _ok, _why = _gate.gate(client_id, action)
        if not _ok:
            _gate.refuse_log(client_id, action, method, _why)
            return _err(rid, -32001, "%s: %s" % (_why, method))

        session = self.manager.get_session(client_id)
        ctx = session.local_cortex
        # Build user-authored history for $0/$N context references.
        # Skip the DB fetch for internal bulk-write calls (JCL/CSL batch) where
        # history context is never needed — avoids 25k+ SELECT queries per boot load.
        if data.get("_skip_history"):
            history: list = []
        else:
            _raw = ctx.stream(50)
            history = [item for item in _raw
                       if item.get("author") == client_id and not _is_sys_atom(item)][:20]

        # Per-token su slot: elevation (su root/librarian/impersonate) is bound to
        # THIS token, not shared across every connection that presents the same
        # client_id — prevents su state bleeding between concurrent sessions.
        su_key = "su_target:" + hashlib.sha256(raw_token.encode()).hexdigest()[:16]

        # ── Single-route write turn ───────────────────────────────────────────
        # A synchronous graph-writing method runs inside ONE Harmonia workspace so
        # its atom/link bundle (proto-word + w + set + alias — the ~4-6-write critical
        # bundle) is atomic and reversible: commit on success, rollback on any error.
        # This is the seam the hard guard enforces — a composite write with no
        # workspace is rejected once ENFORCE is on. Skipped when a workspace is
        # already active on this thread: a JCL step re-enters dispatch under its
        # job's workspace and must not nest (nor steal) a second tracked context.
        if (action in _WRITE_ACTIONS and self.harmonia
                and not _workspace_active()[0] and not _in_workspace()):
            return self._write_turn(method, data, session, ctx, history, rid, su_key, transport_trust)
        # F39-P1a — admission control: bound CONCURRENT dive-bearing renders on the NETWORK serving
        # path so a crawler burst degrades to fast refusals, not OOM. Internal/local calls (JCL steps,
        # the console) bypass it — they must never wait on a slot they might themselves hold. Refused
        # requests get a millisecond Retry-After, never a 60 s hang.
        if (transport_trust == TRUST_NETWORK and method in _dive_bearing(self)):
            _ok, _retry_ms = _DIVE_ADMISSION.acquire()
            if not _ok:
                return _err(rid, -32029,
                            "Server busy — too many concurrent requests; retry shortly.",
                            {"retry_after_ms": _retry_ms, "reason": "admission_cap"})
            try:
                return self._route(method, data, session, ctx, history, rid, su_key, transport_trust)
            finally:
                _DIVE_ADMISSION.release()
        return self._route(method, data, session, ctx, history, rid, su_key, transport_trust)

    # ── heart ops that were inline in the dispatch chain (table entries in lib/akasha/MANIFEST.json) ──
    def _handle_genesis_rite_rpc(self, rid, data, transport_trust):
        # Genesis seizes (or creates) the admin account.  Restrict it to the
        # local console / internal boot so a network client cannot land-grab
        # admin on a Cell that is exposed before its first-boot ceremony.
        if transport_trust not in _TRUSTED_TRANSPORTS:
            return _err(rid, -32001,
                        "genesis_rite must be performed from the local console.")
        return self._handle_genesis_rite(rid, data)

    def _handle_auth_local_rpc(self, rid, data, transport_trust):
        # Passwordless admin login for the LOCAL console only: the OS process boundary is the
        # gate (TRUST_LOCAL / TRUST_INTERNAL) — an operator who can run the CLI already owns the
        # machine. A NETWORK caller never reaches this (it falls through to the passphrase gate).
        if transport_trust not in _TRUSTED_TRANSPORTS:
            return _err(rid, -32001,
                        "auth.local is only available on the local console.")
        return self._handle_auth_local(rid, data)

    def _handle_auth_whoami(self, rid, client_id, role):
        # whoami: echo the RESOLVED identity (after token/trust resolution). A pure read
        # used by a thin forwarding portal to resolve a token for its OWN access gate (e.g.
        # the Concept-Lab gate) without holding a local IAM engine. Reveals only the caller's
        # own identity, so it needs no capability.
        return _ok(rid, {"client_id": client_id, "role": role.value})



    def _handle_cogito(self, rid, session):
        return _ok(rid, session.consciousness.cogito(session))

    def _handle_history(self, rid, history):
        return _ok(rid, {"history": history})

    def _handle_session_close(self, rid, client_id):
        self.manager.close_session(client_id)
        return _ok(rid, {"status": "session_closed", "client_id": client_id})


    def _write_turn(self, method, data, session, ctx, history, rid, su_key,
                    transport_trust: str = TRUST_NETWORK) -> dict:
        """Run a write-action dispatch inside one atomic, reversible workspace.

        Opened on the session's local cortex (the engine that records the tracking
        set). Universal/nucleus writes route to a different engine, so they are
        presence-guarded but not per-atom tracked — acceptable: those are idempotent
        content-addressed system writes, not the user's reversible conversation
        bundle. evidence=False keeps the per-turn workspace off the critical path."""
        # HIGH priority (0): a user turn is the perceived-immediate critical path;
        # its writes are ordered ahead of background batch/link work at the WriteQueue.
        tx_id = self.harmonia.begin_workspace(
            session.local_cortex, f"turn:{method}", tracked=True, evidence=False,
            priority=0)
        try:
            resp = self._route(method, data, session, ctx, history, rid, su_key, transport_trust)
        except Exception:
            self.harmonia.rollback_workspace(session.local_cortex, tx_id)
            raise
        if isinstance(resp, dict) and "error" in resp:
            # Failed op → all-or-nothing: drop anything the handler already wrote.
            self.harmonia.rollback_workspace(session.local_cortex, tx_id)
        else:
            self.harmonia.commit_workspace(session.local_cortex, tx_id)
        return resp

    # ------------------------------------------------------------------
    # Routing table
    # ------------------------------------------------------------------

    def _route(self, method: str, data: dict, session, ctx, history: list, rid: str,
               su_key: str = "su_target", transport_trust: str = TRUST_NETWORK) -> dict:
        client_id = session.client_id
        scopes = session.active_scopes

        req = _Req(rid=rid, method=method, data=data, session=session, ctx=ctx, scopes=scopes,
                   client_id=client_id, history=history, su_key=su_key,
                   transport_trust=transport_trust, role=session.role)
        # Ops that must see the REAL identity (session context, su itself) — stage `pre_su`.
        _e = self.api.ops.resolve(method, "pre_su")
        if _e is not None:
            return _e.call(self, req)

        # Apply su state — override client_id / scopes for all other commands.
        # su_key is per-token so elevation does not leak across connections.
        su_target = session.get_context(su_key)
        if su_target == "root":
            scopes = list(scopes) + ["scope:sys:root"]
        elif su_target == "librarian":
            scopes = list(scopes) + ["role:librarian", "scope:sys:collective"]
        elif su_target:
            try:   # `su` becomes another identity; its reach is that identity's lines
                scopes = _gate.scopes_for(su_target, groups_of=self.manager._groups_of)
            except Exception:
                pass
            client_id = su_target

        # `scope=universal` from a caller the gate admits there routes every put_* to the nucleus.
        nucleus = getattr(session, 'nucleus', None)
        if (data.get("scope") == "universal"
                and _gate.gate(client_id, _gate.RECORD, _gate.UNIVERSAL)[0]
                and nucleus is not None):
            ctx = _NucleusWriteCtx(session.local_cortex, nucleus)

        # su / scope resolution is applied; the request now carries the EFFECTIVE identity.
        req.client_id, req.scopes, req.ctx = client_id, scopes, ctx

        # ── stage `pre`: ops that take precedence over the Concept Model registry ──
        _e = self.api.ops.resolve(method, "pre")
        if _e is not None:
            return _e.call(self, req)

        # ── Concept Models (router-dispatched — the manifests' `routers`) ──
        if self.api.routers:
            # B4-b — a horizon / accelerator read (hydrate/store/cache inventory) is not durable history,
            # so as_of is not defined there: refuse it with -32602 (the same as a horizon Set/atom read).
            if method in self._ASOF_HORIZON_METHODS and data.get("as_of") not in (None, ""):
                return _err(rid, -32602, "as_of is not defined for a horizon read")
            _reg_result = None
            for _router in self.api.routers:
                _reg_result = _router.dispatch_if_handled(method, session, data, rid)
                if _reg_result is not None:
                    break
            if _reg_result is not None:
                # Propagate the created atom key so $it/$0 resolve correctly
                _reg_payload = _reg_result.get("result", {})
                if isinstance(_reg_payload, dict) and "key" in _reg_payload:
                    session.last_written_id = _reg_payload["key"]
                return _reg_result

        # ── stage `post`: everything the registry did not claim ──
        _e = self.api.ops.resolve(method, "post")
        if _e is not None:
            return _e.call(self, req)

        # ── Unknown ───────────────────────────────────────────────────
        return _err(rid, -32601, f"Method not found: '{method}'")

    # ------------------------------------------------------------------
    # su — privileged identity switch (admin only)
    # ------------------------------------------------------------------

    def _handle_su(self, rid: str, data: dict, session, real_client_id: str,
                   su_key: str = "su_target") -> dict:
        # Verify the caller holds admin role
        try:
            role = self.iam.authenticate(real_client_id)
        except PermissionError:
            return _err(rid, -32003, "Permission denied: su requires admin role")
        if role.value not in ("admin",):
            return _err(rid, -32003, "Permission denied: su requires admin role")

        target = data.get("target", "").strip()
        passphrase = data.get("passphrase", "")

        # Exit su (no passphrase required)
        if not target or target == "exit":
            prev = session.get_context(su_key)
            session.set_context(su_key, None)
            return _ok(rid, {"status": "su_exited", "previous": prev})

        # All other su targets require passphrase re-verification
        if not passphrase:
            return _err(rid, -32602, "su requires 'passphrase'")

        presented_hash = hashlib.sha256(passphrase.encode("utf-8")).hexdigest()
        if not self.iam.verify_passphrase(real_client_id, presented_hash):
            return _err(rid, -32001, "Authentication failed: invalid passphrase")

        # Root mode
        if target == "root":
            session.set_context(su_key, "root")
            return _ok(rid, {
                "status": "su_active",
                "target": "root",
                "warning": "All scope restrictions lifted. Full system access active.",
            })

        # Librarian mode — adds role:librarian to current admin session
        if target == "librarian":
            session.set_context(su_key, "librarian")
            return _ok(rid, {
                "status": "su_active",
                "target": "librarian",
                "warning": "Librarian mode active. Nucleus write access and ontology operations enabled.",
            })

        # Impersonate another client — verify identity exists
        try:
            self.iam.authenticate(target)
        except PermissionError:
            return _err(rid, -32002, f"su: unknown identity '{target}'")

        session.set_context(su_key, target)
        return _ok(rid, {"status": "su_active", "target": target})

    # ------------------------------------------------------------------
    # User management handlers (admin only)
    # ------------------------------------------------------------------

    def _assert_admin(self, session) -> Optional[str]:
        """Return error message string if caller is not admin, else None."""
        try:
            role = self.iam.authenticate(session.client_id)
        except PermissionError:
            return "Permission denied: admin role required"
        if role != Role.ADMIN:
            return "Permission denied: admin role required"
        return None

    def _handle_census(self, rid, data, session) -> dict:
        """A1.4/F44 — sys.census: what is the store actually MADE OF. Histograms the shared nucleus
        chunks by meta.role and meta.provenance (and the top alias namespaces), so nobody has to
        guess what the millions of @chunks are (vocabulary senses? feed observations? pulse events?).
        Admin-only. Bounded by AKASHA_CENSUS_CAP (default 3M) with a truncated flag — a diagnostic
        scan, run on demand, never on the serving path."""
        err = self._assert_admin(session)
        if err:
            return _err(rid, -32003, err)
        nucleus = getattr(self.manager, "shared_nucleus", None)
        core = getattr(nucleus, "core", None) if nucleus is not None else None
        if core is None or not hasattr(core, "iter_all_chunks"):
            return _err(rid, -32004, "census requires a store with iter_all_chunks.")
        try:
            cap = int(data.get("cap") or os.environ.get("AKASHA_CENSUS_CAP", "3000000"))
        except (TypeError, ValueError):
            cap = 3000000
        import json as _json
        roles, provs, nsp = {}, {}, {}
        n = 0
        truncated = False
        for row in core.iter_all_chunks(limit=cap + 1):
            if n >= cap:
                truncated = True
                break
            n += 1
            try:
                m = _json.loads(row.get("meta") or "{}")
            except Exception:
                m = {}
            r = (m.get("role") or "(none)") if isinstance(m, dict) else "(none)"
            p = (m.get("provenance") or "(none)") if isinstance(m, dict) else "(none)"
            roles[r] = roles.get(r, 0) + 1
            provs[p] = provs.get(p, 0) + 1
        # Top namespaces from the ns:* collection sizes (cheap: O(namespaces)); safe if unavailable.
        try:
            for cname in (core.list_collection_names() if hasattr(core, "list_collection_names") else []):
                if cname.startswith("ns:"):
                    nsp[cname] = core.count_collection(cname) if hasattr(core, "count_collection") \
                        else len(core.get_collection_members(cname) or [])
        except Exception:
            pass

        def _topn(d, k=25):
            return dict(sorted(d.items(), key=lambda kv: kv[1], reverse=True)[:k])

        return _ok(rid, {"scanned": n, "truncated": truncated,
                         "by_role": _topn(roles), "by_provenance": _topn(provs),
                         "top_namespaces": _topn(nsp)})

    def _handle_space_probe(self, rid, data, session) -> dict:
        """F47-2.4 — sys.space_probe name=<alias>: the one-command production proof that the ENGINE
        stays innocent. Renders ONE concept the same way the public page does (archives.space →
        op_concept → generate_view) but ENGINE-SIDE and BYPASSING admission, then returns
        {ms, point_get, membrane_scan, full_scan} straight off the store's access-degree probe. On
        live data this must be < ~200 ms with zero full_scans; a slow public page with a fast probe
        proves the latency is coupling/admission, not the semantic system. Admin-only, diagnostic —
        never on the serving path. Dispatched over TRUST_INTERNAL, which is not admission-gated
        (admission is TRUST_NETWORK-only), so the probe measures the render itself, not the queue."""
        err = self._assert_admin(session)
        if err:
            return _err(rid, -32003, err)
        name = (data.get("name") or data.get("alias") or "").strip()
        if not name:
            return _err(rid, -32602, "sys.space_probe requires name=<alias>.")
        nucleus = getattr(self.manager, "shared_nucleus", None)
        core = getattr(nucleus, "core", None) if nucleus is not None else None
        has_probe = core is not None and hasattr(core, "probe_reset") and hasattr(core, "probe_read")
        if has_probe:
            try:
                core.probe_reset()
            except Exception:
                has_probe = False
        author = getattr(session, "client_id", "admin")
        # The RENDER_CONCEPT point — the op that renders one concept the way the public page does —
        # is declared by the op itself (`"implements": "render_concept"`, group 4, 4.3).
        _rm = _api.implementer(self, "render_concept")
        if not _rm:
            return _err(rid, -32601, "sys.space_probe: no op implements `render_concept` on this "
                                     "cell (the application registers its concept renderer)")
        t0 = time.perf_counter()
        resp = self.dispatch({"jsonrpc": "2.0", "method": _rm,
                              "params": {"client_id": author, "data": {"name": name}}, "id": "sp"},
                             TRUST_INTERNAL)
        ms = (time.perf_counter() - t0) * 1000.0
        probe = {}
        if has_probe:
            try:
                probe = core.probe_read()
            except Exception:
                probe = {}
        ok = isinstance(resp, dict) and "result" in resp and not (resp.get("error"))
        result = (resp.get("result") if isinstance(resp, dict) else {}) or {}
        found = bool(ok and (result.get("concept") or result.get("atom") or result.get("name")))
        return _ok(rid, {"name": name, "ms": round(ms, 3), "ok": ok, "found": found,
                         "point_get": probe.get("point_get"),
                         "membrane_scan": probe.get("membrane_scan"),
                         "full_scan": probe.get("full_scan"),
                         "entries_walked": probe.get("entries_walked"),   # F50 §4 — entries iterated
                         "probe_available": has_probe,
                         "note": ("engine-side render bypassing admission; "
                                  "expect < 200 ms and full_scan=0 on healthy live data")})

    def _running_compact_job(self):
        """The job_id of an in-flight sys.compact fold (PENDING or RUNNING), or None. Used to REFUSE a
        second submission so the operator's retry reflex (which each time ran another full fold, pausing
        writers bank-by-bank) costs nothing (F52 §1)."""
        try:
            jobs = self.jcl_worker.list_jobs() if self.jcl_worker else []
        except Exception:
            jobs = []
        for j in jobs:
            if getattr(j, "label", "") == "sys.compact" and getattr(j, "status", "") in ("PENDING", "RUNNING"):
                return getattr(j, "job_id", None)
        return None

    def _handle_compact(self, rid, session) -> dict:
        """R7/F26/F52 — sys.compact: fold the shared nucleus WAL. The fold's duration SCALES WITH STORE
        SIZE (an 11.5 M-record WAL exceeds the 60 s cell-IPC reply window → the client sees a spurious
        'daemon busy' while the fold completes inside the daemon, inviting the harmful retry reflex). So
        this is ASYNC: submit the fold as a background JCL job (the machinery the .ak test scripts use)
        and return IMMEDIATELY with the job id — the 60 s IPC window is for answers, not for work (F52).
        Admin-only, Silica-only. Poll `job.stat <id>`; completion is logged as [compact]. A second
        submission while a fold is running is refused (returns the running id)."""
        err = self._assert_admin(session)
        if err:
            return _err(rid, -32003, err)
        nucleus = getattr(self.manager, "shared_nucleus", None)
        core = getattr(nucleus, "core", None) if nucleus is not None else None
        if core is None or not hasattr(core, "compact"):
            return _err(rid, -32004, "sys.compact requires the Silica backend (AKASHA_BACKEND=silica).")
        running = self._running_compact_job()
        if running is not None:
            return _ok(rid, {"type": "sys:compact", "started": False, "job": running,
                             "note": "a WAL fold is already running — poll job.stat %s (the retry "
                                     "reflex costs nothing; a second fold is not started)" % running})
        if not (self.harmonia and JCLJob and JCLStep):
            # No JCL available (bare/edge build) — fall back to the synchronous fold rather than fail.
            return self._handle_compact_run(rid, session)
        before = 0
        try:
            before = int(core.wal_bytes()) if hasattr(core, "wal_bytes") else 0
        except Exception:
            before = 0
        job = JCLJob(owner=session.client_id, label="sys.compact",
                     steps=[JCLStep(method="sys.compact.run", params={})], fail_fast=True)
        self.harmonia.submit_job(job, job_class=CLASS_MAINTENANCE)
        return _ok(rid, {"type": "sys:compact", "started": True, "job": job.job_id,
                         "wal_bytes": before,
                         "note": "poll job.stat %s; completion is logged as [compact]" % job.job_id})

    def _handle_compact_run(self, rid, session) -> dict:
        """[sys.compact.run] The actual WAL fold — the job body submitted by sys.compact (F52 §1), or a
        synchronous fallback when JCL is unavailable. Runs writer-side: each bank pauses its writers
        under bank.lock for its fold, so it runs to completion here on the writer daemon; a serving
        portal replica only reads the WAL at open, so folding under it is safe. Records the post-fold
        WAL size as the auto-checkpoint baseline (F52 §2) so the idle daemon re-folds on GROWTH, not
        total size. Admin-only, Silica-only."""
        err = self._assert_admin(session)
        if err:
            return _err(rid, -32003, err)
        nucleus = getattr(self.manager, "shared_nucleus", None)
        core = getattr(nucleus, "core", None) if nucleus is not None else None
        if core is None or not hasattr(core, "compact"):
            return _err(rid, -32004, "sys.compact requires the Silica backend (AKASHA_BACKEND=silica).")
        try:
            res = core.compact()
        except Exception as exc:
            logger.warning("[compact] failed: %s", exc)
            return _err(rid, -32004, f"compact failed: {exc}")
        try:
            KernelDispatcher._wal_last_fold_bytes = int(core.wal_bytes())   # re-baseline the auto-daemon
        except Exception:
            KernelDispatcher._wal_last_fold_bytes = res.get("after_bytes")
        logger.info("[compact] nucleus WAL %d → %d bytes in %.2fs (baseline=%s)",
                    res.get("before_bytes", 0), res.get("after_bytes", 0), res.get("seconds", 0.0),
                    KernelDispatcher._wal_last_fold_bytes)
        return _ok(rid, res)

    def _handle_user_ls(self, rid, session) -> dict:
        err = self._assert_admin(session)
        if err:
            return _err(rid, -32003, err)
        users = self.iam.list_clients()
        # Strip passphrase hash from output
        sanitized = [
            {k: v for k, v in u.items() if k != "passphrase_hash"}
            for u in users
        ]
        return _ok(rid, {"users": sanitized, "count": len(sanitized)})

    def _handle_user_add(self, rid, data, session) -> dict:
        err = self._assert_admin(session)
        if err:
            return _err(rid, -32003, err)
        client_id   = (data.get("client_id") or data.get("id") or "").strip()
        role_str    = data.get("role", "user").strip().lower()
        phash       = data.get("passphrase_hash", "")
        display     = data.get("display_name", client_id)
        if not client_id:
            return _err(rid, -32602, "user.add requires 'client_id'")
        try:
            role = Role(role_str)
        except ValueError:
            return _err(rid, -32602, f"Unknown role '{role_str}'. Valid: user, librarian, group_admin, admin")
        try:
            record = self.iam.register_client(
                client_id, role,
                passphrase_hash=phash or None,
                created_by=session.client_id,
                display_name=display,
            )
        except ValueError as e:
            return _err(rid, -32602, str(e))

        # Account and ASSIGNMENT LINE are made together — without one it reads as a guest.
        _gate.identity_changed(self, client_id, role_str)
        # Create a private HumanConcept identity record for the new client.
        # Scope: owner:user_{client_id} + view:user_{client_id} — accessible only
        # by the client themselves and by admins (via view:admin_override).
        # Note: Role.GUEST clients lack owner:user_* in their active_scopes and
        # therefore cannot read back their own Human atom until the role is upgraded.
        human_id = None
        _HumanConcept = self._router_class("human")
        if _HumanConcept is not None:
            try:
                from lib.akasha.jcl.workspace_context import system_context as _sys_ctx
                new_session = self.manager.get_session(client_id)
                human = _HumanConcept(new_session)
                # System-initiated identity write: it does not run under a user
                # conversation workspace, so exempt it from the single-route guard
                # (same pattern as genesis/anchor writes). Without this the
                # HumanConcept atom is rejected and the member has no identity record.
                with _sys_ctx():
                    result = human.op_new(
                        name=display,
                        description=f"Identity record for registered client '{client_id}'",
                        client_id=client_id,
                    )
                human_id = result.get("human_id")
                # Store the mapping so the user can retrieve their identity later
                new_session.set_context("identity_human_id", human_id)
            except Exception as exc:
                logger.warning("[user.add] HumanConcept creation failed for '%s': %s", client_id, exc)

        return _ok(rid, {"status": "created", "client_id": client_id, "role": role.value,
                         "human_id": human_id})

    def _handle_user_rm(self, rid, data, session) -> dict:
        err = self._assert_admin(session)
        if err:
            return _err(rid, -32003, err)
        client_id = (data.get("client_id") or data.get("id") or "").strip()
        if not client_id:
            return _err(rid, -32602, "user.rm requires 'client_id'")
        if client_id == session.client_id:
            return _err(rid, -32602, "Cannot remove yourself")
        try:
            self.iam.deregister_client(client_id)
        except (KeyError, ValueError) as e:
            return _err(rid, -32602, str(e))
        return _ok(rid, {"status": "removed", "client_id": client_id})

    def _handle_user_mod(self, rid, data, session) -> dict:
        err = self._assert_admin(session)
        if err:
            return _err(rid, -32003, err)
        client_id = (data.get("client_id") or data.get("id") or "").strip()
        role_str  = data.get("role", "").strip().lower()
        if not client_id or not role_str:
            return _err(rid, -32602, "user.mod requires 'client_id' and 'role'")
        try:
            role = Role(role_str)
            self.iam.set_role(client_id, role)
        except ValueError as e:
            return _err(rid, -32602, str(e))
        return _ok(rid, {"status": "updated", "client_id": client_id, "role": role_str})

    def _handle_user_id(self, rid, data, session) -> dict:
        err = self._assert_admin(session)
        if err:
            return _err(rid, -32003, err)
        client_id = (data.get("client_id") or data.get("id") or "").strip()
        if not client_id:
            return _err(rid, -32602, "user.id requires 'client_id'")
        record = self.iam.get_client(client_id)
        if not record:
            return _err(rid, -32002, f"User '{client_id}' not found")
        groups = self.iam.get_client_groups(client_id)
        info = {k: v for k, v in record.items() if k != "passphrase_hash"}
        info.update({"client_id": client_id, "groups": groups,
                     "has_passphrase": bool(record.get("passphrase_hash"))})
        return _ok(rid, info)

    def _handle_passwd_self(self, rid, data, session) -> dict:
        """Self-service passphrase change — any authenticated user, own account only."""
        current_hash = data.get("current_hash", "").strip()
        new_hash     = data.get("new_hash", "").strip()
        if not current_hash or not new_hash:
            return _err(rid, -32602, "passwd requires 'current_hash' and 'new_hash'")
        if not self.iam.verify_passphrase(session.client_id, current_hash):
            return _err(rid, -32001, "Authentication failed: incorrect current passphrase")
        try:
            self.iam.set_passphrase(session.client_id, new_hash)
        except (KeyError, ValueError) as e:
            return _err(rid, -32602, str(e))
        return _ok(rid, {"status": "passphrase_updated", "client_id": session.client_id})

    def _handle_user_passwd(self, rid, data, session) -> dict:
        err = self._assert_admin(session)
        if err:
            return _err(rid, -32003, err)
        client_id = (data.get("client_id") or data.get("id") or "").strip()
        phash     = data.get("passphrase_hash", "").strip()
        if not client_id or not phash:
            return _err(rid, -32602, "user.passwd requires 'client_id' and 'passphrase_hash'")
        try:
            self.iam.set_passphrase(client_id, phash)
        except (KeyError, ValueError) as e:
            return _err(rid, -32602, str(e))
        return _ok(rid, {"status": "passphrase_updated", "client_id": client_id})

    # ------------------------------------------------------------------
    # Group management handlers
    # ------------------------------------------------------------------

    def _handle_grp_ls(self, rid, data, session) -> dict:
        # S2-g — member ids stay inside the admitted circle, and ONE question decides it per
        # group: may this caller READ it? A row reaching `*` and a line naming this group both
        # answer yes; everyone else gets {group_id, member_count}. The scope-string test plus the
        # `admin ==` / `cid in members` branches that stood here asked the same thing three ways.
        cid = getattr(session, "client_id", "")

        def _view(g):
            members = g.get("members") or []
            if _gate.gate(cid, _gate.READ, g.get("group_id") or "")[0]:
                return g
            return {"group_id": g.get("group_id"), "member_count": len(members)}

        group_id = (data.get("group_id") or data.get("id") or "").strip()
        if group_id:
            g = self.iam.get_group(group_id)
            if not g:
                return _err(rid, -32002, f"Group '{group_id}' not found")
            return _ok(rid, {"group": _view(g)})
        groups = self.iam.list_groups()
        return _ok(rid, {"groups": [_view(g) for g in groups], "count": len(groups)})

    def _handle_grp_new(self, rid, data, session) -> dict:
        err = self._assert_admin(session)
        if err:
            return _err(rid, -32003, err)
        group_id  = (data.get("group_id") or data.get("id") or "").strip()
        admin_id  = (data.get("admin_id") or data.get("admin") or "").strip()
        if not group_id or not admin_id:
            return _err(rid, -32602, "grp.new requires 'group_id' and 'admin_id'")
        self.iam.create_group(group_id, admin_id)
        return _ok(rid, {"status": "created", "group_id": group_id, "admin": admin_id})

    def _handle_grp_add(self, rid, data, session) -> dict:
        group_id  = (data.get("group_id") or "").strip()
        member_id = (data.get("member_id") or data.get("member") or "").strip()
        if not group_id or not member_id:
            return _err(rid, -32602, "grp.add requires 'group_id' and 'member_id'")
        if not self.iam.get_group(group_id):           # S2-f — only grp.new creates a group
            return _err(rid, -32002, f"Group '{group_id}' not found (create it with grp.new first)")
        try:
            self.iam.add_group_member(group_id, session.client_id, member_id)
        except PermissionError as e:
            return _err(rid, -32003, str(e))
        _gate.identity_changed(self, member_id)   # membership IS an assignment line (§2b)
        return _ok(rid, {"status": "added", "group_id": group_id, "member": member_id})

    def _handle_grp_rm(self, rid, data, session) -> dict:
        group_id  = (data.get("group_id") or "").strip()
        member_id = (data.get("member_id") or data.get("member") or "").strip()
        if not group_id or not member_id:
            return _err(rid, -32602, "grp.rm requires 'group_id' and 'member_id'")
        if not self.iam.get_group(group_id):           # S2-f
            return _err(rid, -32002, f"Group '{group_id}' not found")
        try:
            self.iam.remove_group_member(group_id, session.client_id, member_id)
        except PermissionError as e:
            return _err(rid, -32003, str(e))
        return _ok(rid, {"status": "removed", "group_id": group_id, "member": member_id})

    def _handle_grp_lib(self, rid, data, session) -> dict:
        group_id  = (data.get("group_id") or "").strip()
        action    = (data.get("action") or "").strip().lower()
        member_id = (data.get("member_id") or data.get("member") or "").strip()
        if not group_id or action not in ("grant", "revoke") or not member_id:
            return _err(rid, -32602, "grp.lib requires 'group_id', 'action' (grant|revoke), 'member_id'")
        if not self.iam.get_group(group_id):           # S2-f
            return _err(rid, -32002, f"Group '{group_id}' not found")
        try:
            if action == "grant":
                self.iam.grant_group_librarian(group_id, session.client_id, member_id)
            else:
                self.iam.revoke_group_librarian(group_id, session.client_id, member_id)
        except PermissionError as e:
            return _err(rid, -32003, str(e))
        return _ok(rid, {"status": f"librarian_{action}ed", "group_id": group_id, "member": member_id})

    def _handle_grp_del(self, rid, data, session) -> dict:
        err = self._assert_admin(session)
        if err:
            return _err(rid, -32003, err)
        group_id = (data.get("group_id") or data.get("id") or "").strip()
        if not group_id:
            return _err(rid, -32602, "grp.del requires 'group_id'")
        if not self.iam.get_group(group_id):
            return _err(rid, -32002, f"Group '{group_id}' not found")
        self.iam.delete_group(group_id)
        return _ok(rid, {"status": "deleted", "group_id": group_id})

    # ------------------------------------------------------------------
    # Donation / Delegation Sets (dont.*)
    # ------------------------------------------------------------------
    # Delegation sets are named collections used to transfer (donate) a bundle
    # of atoms to a shared space: the nucleus (universal) or a group space.
    # Metadata on the set records provenance on both origin and destination.
    # Set name convention: "dont:<user_name>" e.g. dont:love_vocab






    # ------------------------------------------------------------------
    # Unauthenticated handlers
    # ------------------------------------------------------------------

    def _handle_ping(self, rid: str, client_id: str) -> dict:
        # CONSTANT-TIME LIVENESS ONLY. sys.ping is the reachability probe the portal /
        # CLI client (cell_ipc.ping) uses to decide "is the Cell daemon there?" — it only
        # needs "the daemon answered", nothing more. It therefore touches NO iam / manager /
        # session / consciousness / DB: those calls run on the same GIL as the writer, so a
        # heavy dive (mega-hub fan-out) or boot-time index/cache warming holding the CPU could
        # otherwise stall this probe past its timeout and be MISREAD as "writer unreachable",
        # fail-closing the write-forwarding path even though the daemon is alive but busy.
        # Keeping it O(1) means once the probe gets a GIL slice it returns instantly.
        # The rich cogito view (consciousness.ping) is served by _handle_status_full / sys.status.
        return _ok(rid, {
            "status": "kernel_online",
            "series": self.series,
            "timestamp": time.time(),
            "alive": True,
            # Running-code fingerprint (stamped by the launcher at daemon boot). A re-extracted
            # seed / pulled repo boots argument-less → attaches to THIS daemon over the socket;
            # if its on-disk code differs from what this daemon is running, the client replaces
            # the daemon instead of running new tests on stale code. Constant-time env read.
            # Prefer the CODE-CONTENT fingerprint (AKASHA_HANDSHAKE_BUILD) for the replace
            # handshake — it is identical for identical code however the daemon was launched (seed
            # vs plain `python akasha.py`). AKASHA_BUILD_ID may be a git-SHA display label the seed
            # stamped, which differs from a plain reconnect's content hash and would wrongly trigger
            # a daemon-replace (the silent no-trace daemon kill + boot loop). Fall back to it only
            # for a daemon booted before this field existed.
            "build": os.environ.get("AKASHA_HANDSHAKE_BUILD") or os.environ.get("AKASHA_BUILD_ID", ""),
        })

    def _handle_status(self, rid: str) -> dict:
        return _ok(rid, {
            "status": "online",
            "series": self.series,
            "harmonia": self.harmonia is not None,
            "contexa": self.contexa is not None,
            "active_sessions": len(self.manager.sessions),
            "timestamp": time.time()
        })



    def _handle_status_full(self, rid: str, session) -> dict:
        """Aggregate status: cogito payload + akasha_name, series, display_focus, JCL summary."""
        result = session.consciousness.ping(session)
        try:
            akasha_name = self._nucleus().vault_retrieve("system", "akasha_name") or "AKASHA"
        except Exception:
            akasha_name = "AKASHA"
        result["akasha_name"]   = akasha_name
        result["series"]        = self.series
        result["version"]       = _AKASHA_VERSION
        result["display_focus"] = session.get_context("display_focus") or {}
        if self.jcl_worker:
            from collections import Counter as _Ctr
            all_jobs = self.jcl_worker.list_jobs(owner=session.client_id)
            counts   = _Ctr(j.status for j in all_jobs)
            result["jcl"] = {
                "running":     counts.get("RUNNING", 0),
                "pending":     counts.get("PENDING", 0),
                "queue_depth": self.jcl_worker.queue_depth(),
            }
        else:
            result["jcl"] = None
        # Silica store health — value-mode, index-kind, and (disk mode) the read-cache hit-rate.
        # This is the measurement basis for the "search feels slow" diagnosis: a low disk-value
        # cache hit-rate means most reads are WAL preads (I/O-bound), pointing at the value-cache
        # budget rather than the index. Best-effort + duck-typed so a non-silica backend just omits
        # it; never fails the status call.
        try:
            store = getattr(getattr(self._nucleus(), "core", None), "_store", None)
            st = store.stats() if store is not None and hasattr(store, "stats") else None
            if st is not None:
                c = st.get("cache") or {}
                result["silica"] = {
                    "values": st.get("values"),
                    "index": st.get("index"),
                    "cache_hit_rate": c.get("hit_rate"),
                    "cache_bytes": c.get("bytes"),
                    "cache_budget": c.get("budget"),
                }
        except Exception:
            pass
        return _ok(rid, result)

    def _handle_sys_ls(self, rid: str, data: dict, ctx, scopes, client_id: str) -> dict:
        # Cursor pagination over the recent-atom stream. Fetch enough of the stream to
        # cover offset+limit AFTER filtering (×5 slack for excluded sys/other-author
        # atoms), then page the filtered list.
        lim = _rlimit(data.get("limit"), default=10, max_limit=100)
        off = _roffset(data.get("cursor"))
        need = off + (lim or 100)
        raw = ctx.stream(need * 5 + 20)
        # su root: expose all atoms including system-owned ones
        if scopes and "scope:sys:root" in scopes:
            filtered = list(raw)
        else:
            # Keep only atoms authored by this user; exclude internal sys: atoms.
            filtered = [item for item in raw
                        if item.get("author") == client_id and not _is_sys_atom(item)]
        window, page = _paginate(filtered, data.get("limit"), data.get("cursor"),
                                 default=10, max_limit=100)
        atoms = []
        for i, item in enumerate(window):
            key     = item.get("key", "")
            content = item.get("content") or ctx.get_chunk(key) or ""
            aliases = ctx.get_aliases_by_key(key)
            atoms.append({"idx": page["offset"] + i, "key": key, "preview": content[:60], "aliases": aliases})
        return _ok(rid, {"atoms": atoms, "count": len(atoms), "page": page})

    def _handle_genesis_rite(self, rid: str, data: dict) -> dict:
        akasha_name = data.get("akasha_name", "AKASHA")
        user_name = data.get("user_name", "")
        raw_passphrase = data.get("passphrase", "")

        if not user_name or not raw_passphrase:
            return _err(rid, -32602, "genesis_rite requires 'user_name' and 'passphrase'")

        passphrase_hash = hashlib.sha256(raw_passphrase.encode("utf-8")).hexdigest()

        # Bootstrap a temporary system session for the ceremony
        # Use the existing manager without strict IAM (pre-genesis state)
        try:
            session = self.manager.get_session("sys:genesis_bootstrap")
        except Exception:
            session = None

        # Perform the rite via the consciousness layer
        consciousness = session.consciousness if session else None
        if not consciousness:
            # Fallback: create bare-minimum cortex for the ceremony
            from lib.akasha.composite import AkashaEngine
            import os
            os.makedirs(f"{self.base_dir}/cells/sys_genesis", exist_ok=True)
            bare_cortex = AkashaEngine(f"{self.base_dir}/cells/sys_genesis/genesis.db")
            from lib.akasha.consciousness import ConsciousnessEngine
            consciousness = ConsciousnessEngine(bare_cortex)

        # The genesis ceremony writes the akasha-name / keeper anchor atoms outside
        # any request workspace (it runs before the first session/turn). Exempt those
        # system writes from the single-route guard.
        from lib.akasha.jcl.workspace_context import system_context as _sys_ctx
        with _sys_ctx():
            result = consciousness.genesis_rite(akasha_name, user_name, passphrase_hash, session)

        # If rite succeeded, register the genesis admin in the persistent IAM store
        if result.get("status") == "bound":
            self.iam.register_client(user_name, Role.ADMIN,
                                     passphrase_hash=passphrase_hash,
                                     created_by="genesis",
                                     display_name=user_name)
            if user_name != "admin":
                # Also register the canonical "admin" alias used by automation
                self.iam.register_client("admin", Role.ADMIN,
                                         passphrase_hash=passphrase_hash,
                                         created_by="genesis",
                                         display_name="admin")
            # THE OPERATOR'S LINE, with the account — no line is a GUEST (§4 step 1), so a Genesis
            # operator not named the literal `admin` was ADMIN in IAM and refused by the gate.
            _gate.identity_changed(self, user_name, Role.ADMIN.value)
            # The application's DECLARED identities, made credential-less (platform-spec v1).
            from lib.akasha import identities as _ids
            _ids.reconcile(self)

            # Trigger ontology boot load now that admin exists.
            # _boot_load_ontology is a no-op when called at kernel init on a
            # fresh install (no admin yet), so we re-run it after genesis_rite.
            if self.jcl_worker:
                import threading as _thr_g
                _thr_g.Thread(target=self._boot_load_ontology, daemon=True,
                              name="ont-genesis-load").start()

        return _ok(rid, result)

    def _maybe_auto_genesis(self) -> bool:
        """Fresh-install automation: when no admin exists AND the deployer supplied an
        admin passphrase out-of-band via ``AKASHA_ADMIN_PASS``, run genesis_rite
        internally so a seed self-initializes with NO interactive ceremony — the
        "seeds からすべて自動" path for a truly fresh box (a daemon has no TTY to
        prompt at).

        Security: NEVER bakes a default passphrase. Absent the env (or if it is too
        short), this is a no-op and the interactive local-console genesis remains the
        only way in — so a seed can never ship a known admin credential. The passphrase
        is read from the environment only, never persisted as an atom. Idempotent: once
        an admin exists this returns False without acting.

        Returns True iff it performed the rite (genesis_rite then re-triggers the
        ontology boot-load on its own thread)."""
        import os as _os
        raw = _os.environ.get("AKASHA_ADMIN_PASS", "")
        if not raw:
            return False
        if len(raw) < 8:
            logger.warning("[Genesis] AKASHA_ADMIN_PASS is set but shorter than 8 chars — "
                           "ignoring. Set a passphrase of at least 8 chars to "
                           "auto-initialize a fresh install.")
            return False
        # Only when TRULY uninitialized — never overwrite an existing admin.
        try:
            self.iam.authenticate("admin")
            return False
        except PermissionError:
            pass
        user_name = (_os.environ.get("AKASHA_ADMIN_ID", "").strip() or "admin")
        akasha_name = (_os.environ.get("AKASHA_SYSTEM_NAME", "").strip() or "AKASHA")
        logger.info("[Genesis] AKASHA_ADMIN_PASS present on a fresh install — "
                    "self-initializing admin '%s' (no interactive ceremony).", user_name)
        try:
            resp = self.dispatch({
                "jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"data": {"akasha_name": akasha_name,
                                    "user_name": user_name, "passphrase": raw}},
                "id": "auto-genesis",
            }, TRUST_INTERNAL)
        except Exception as exc:                                # never crash boot on this
            logger.warning("[Genesis] auto-genesis dispatch error: %s", exc)
            return False
        if isinstance(resp, dict) and "error" in resp:
            logger.warning("[Genesis] auto-genesis failed: %s",
                           resp["error"].get("message"))
            return False
        logger.info("[Genesis] auto-genesis complete — ontology boot-load will follow.")
        return True

    def _nucleus(self):
        """Returns the process-shared NucleusEngine from the manager."""
        return self.manager.shared_nucleus

    def _handle_auth_status(self, rid: str) -> dict:
        # Pre-auth endpoint: report only whether the Cell is initialized.  The
        # admin username is NOT disclosed — under the token model the username is
        # the login identifier, so leaking it pre-auth hands an attacker half the
        # credential (and the whole of it under the old bare-id model).
        try:
            n = self._nucleus()
            admin_name = n.vault_retrieve("system", "admin_name")
            akasha_name = n.vault_retrieve("system", "akasha_name") or "AKASHA"
        except Exception:
            n, admin_name, akasha_name = None, None, "AKASHA"
        # `initialized` requires BOTH an admin name AND a usable passphrase credential — not just
        # the name. A crash mid-genesis (or the old Silica read-fd race aborting a genesis write)
        # can leave a HALF-WRITTEN genesis vault: `system/admin_name` persisted but the matching
        # credential (`iam/user:<name>` / `iam/user:admin` / legacy `system/passphrase_hash`) did
        # not. With the old `admin_name is not None` test that reads as initialized, so the console
        # shows a login prompt that can NEVER succeed (no credential to verify against) — a soft
        # brick. Treating "name present, no credential" as NOT initialized lets the local console
        # re-run the genesis ceremony and re-establish the admin, WITHOUT touching the graph
        # (genesis only overwrites the genesis vault + admin record; every ontology/user atom is
        # preserved). Safe: genesis_rite is local-console-only (TRUST_LOCAL), so this never opens a
        # network admin land-grab. Reads the durable vault directly (not the cache), so it reflects
        # ground truth, not a boot-timing gap.
        credential_present = False
        if n is not None and admin_name:
            try:
                rec = (n.vault_retrieve("iam", f"user:{admin_name}")
                       or n.vault_retrieve("iam", "user:admin"))
                if isinstance(rec, dict) and rec.get("passphrase_hash"):
                    credential_present = True
                elif n.vault_retrieve("system", "passphrase_hash"):
                    credential_present = True          # legacy single-hash genesis vault entry
            except Exception:
                credential_present = False
            if not credential_present:
                logger.warning("[IAM] auth.status: admin_name=%r present but NO usable passphrase "
                               "credential in the vault — reporting uninitialized so the local "
                               "console can re-run genesis (graph is preserved).", admin_name)
        # `booting` = the boot content-load is still in progress (BootWatch runs during the load and
        # clears ~30s after it settles). While booting, a transient not-initialized read (the store /
        # IAM snapshot not yet attached — pronounced on the native Silica twin) must NOT be mistaken
        # for a fresh install: the local console waits instead of prompting a premature Genesis rite on
        # a cell whose admin is actually present (public requirement — a redeploy must never look reset).
        return _ok(rid, {
            "initialized": bool(admin_name is not None and credential_present),
            "akasha_name": akasha_name,
            "booting": bool(getattr(self, "_bootwatch_running", False)),
        })

    def _handle_auth_local(self, rid: str, data: dict) -> dict:
        """Passwordless admin login for the LOCAL console (gated to TRUST_LOCAL /
        TRUST_INTERNAL by the dispatcher). The OS process boundary is the gate, so a
        local operator opens an admin session with no passphrase — the hot-start path
        that makes a redeploy land straight at the prompt. Requires an initialized
        cell (an admin already exists via the genesis ceremony); otherwise it returns
        an error and the console runs genesis instead. Network callers never reach
        here, so this opens no remote login."""
        try:
            n = self._nucleus()
            admin_name = n.vault_retrieve("system", "admin_name")
        except Exception:
            admin_name = None
        try:
            ttl = max(60, min(int(data.get("ttl", 86400)), 86400))
        except (TypeError, ValueError):
            ttl = 86400
        # Prefer the recorded admin identity; fall back to the canonical "admin".
        for uid in [c for c in (admin_name, "admin") if c]:
            try:
                role = self.iam.authenticate(uid)
            except PermissionError:
                continue
            try:
                minted = self.iam.issue_session_token(uid, ttl)
            except PermissionError as e:
                return _err(rid, -32001, str(e))
            return _ok(rid, {
                "status": "authenticated",
                "user_id": uid,
                "session_token": minted["session_token"],
                "expires_at": minted["expires_at"],
                "role": role.value,
            })
        return _err(rid, -32001, "No admin identity yet — run the genesis ceremony first.")

    def _handle_auth_verify(self, rid: str, data: dict) -> dict:
        user_id = data.get("user_id", "")
        passphrase = data.get("passphrase", "")
        if not user_id or not passphrase:
            return _err(rid, -32602, "auth.verify requires 'user_id' and 'passphrase'")

        # System process identities have no passphrase and are never a login.
        if self.iam.is_system_identity(user_id):
            return _err(rid, -32001, "Authentication failed: invalid credentials")

        passphrase_hash = hashlib.sha256(passphrase.encode("utf-8")).hexdigest()

        # Verify passphrase through IAM (covers per-user hashes + genesis fallback)
        if not self.iam.verify_passphrase(user_id, passphrase_hash):
            return _err(rid, -32001, "Authentication failed: invalid credentials")

        try:
            role = self.iam.authenticate(user_id)
        except PermissionError:
            return _err(rid, -32001, "Authentication failed: unknown user")

        # Mint a signed, expiring session token bound to this identity.  This —
        # not the bare username — is what the client presents on subsequent calls.
        try:
            ttl = max(60, min(int(data.get("ttl", 1800)), 86400))
        except (TypeError, ValueError):
            ttl = 1800
        try:
            minted = self.iam.issue_session_token(user_id, ttl)
        except PermissionError as e:
            return _err(rid, -32001, str(e))

        return _ok(rid, {
            "status": "authenticated",
            "user_id": user_id,
            "session_token": minted["session_token"],
            "expires_at": minted["expires_at"],
            "role": role.value,
        })

    # ------------------------------------------------------------------
    # Self-service registration + entitlement plan (general, product-neutral)
    # ------------------------------------------------------------------
    @staticmethod
    def _self_register_enabled() -> bool:
        return str(os.environ.get("AKASHA_ALLOW_SELF_REGISTER", "")).strip().lower() \
            in ("1", "yes", "true", "on")

    def _get_plan(self, uid: str) -> str:
        """A user's entitlement tier from the shared nucleus vault ('entitlement' KV).
        Product-neutral; 'paid' only if explicitly set, else 'free'."""
        try:
            v = self._nucleus().vault_retrieve("entitlement", uid)
        except Exception:
            v = None
        return "paid" if str(v or "").strip().lower() == "paid" else "free"

    def _set_plan(self, uid: str, tier: str) -> None:
        self._nucleus().vault_store("entitlement", uid, tier)

    def _handle_auth_register(self, rid, data) -> dict:
        """Self-service account creation. DELIBERATELY BOUNDED (a loosening of the
        admin-only user-management rule): OFF unless AKASHA_ALLOW_SELF_REGISTER is set;
        role is FORCED to 'user' (never client-supplied, no privilege escalation); an
        existing id is REJECTED (never overwritten → no account hijack); a passphrase is
        required. Abuse controls (rate limiting, email/CAPTCHA) are a deployment concern.
        On success it auto-logs-in (returns a session token) and starts on the free plan."""
        if not self._self_register_enabled():
            return _err(rid, -32601, "Self-registration is not enabled on this server.")
        client_id  = (data.get("user_id") or data.get("client_id") or "").strip()
        passphrase = data.get("passphrase", "")
        display    = (data.get("display_name") or client_id).strip()
        if not client_id or not passphrase:
            return _err(rid, -32602, "auth.register requires 'user_id' and 'passphrase'.")
        if not (3 <= len(client_id) <= 64) or not all(
                c.isalnum() or c in "_.-" for c in client_id):
            return _err(rid, -32602, "user_id must be 3-64 chars of [A-Za-z0-9_.-].")
        if len(passphrase) < 8:
            return _err(rid, -32602, "passphrase must be at least 8 characters.")
        if self.iam.is_system_identity(client_id):
            return _err(rid, -32001, "That identity is reserved.")
        # No overwrite: a taken id is rejected (prevents account takeover).
        try:
            taken = self.iam._cache.get(client_id) is not None
        except Exception:
            taken = False
        if taken:
            return _err(rid, -32602, "That user id is already taken.")

        presented = hashlib.sha256(passphrase.encode("utf-8")).hexdigest()
        try:
            self.iam.register_client(client_id, Role.USER,          # role FORCED to user
                                     passphrase_hash=presented,
                                     created_by="self-register", display_name=display)
        except ValueError as e:
            return _err(rid, -32602, str(e))
        # The FOURTH entrance — the door the consumer apps come through (`resident`, §1).
        _gate.identity_changed(self, client_id, Role.USER.value)

        # Best-effort private identity record (same as admin user.add).
        _HumanConcept = self._router_class("human")
        if _HumanConcept is not None:
            try:
                from lib.akasha.jcl.workspace_context import system_context as _sys_ctx
                new_session = self.manager.get_session(client_id)
                with _sys_ctx():
                    _HumanConcept(new_session).op_new(
                        name=display, description=f"Self-registered client '{client_id}'",
                        client_id=client_id)
            except Exception as exc:
                logger.warning("[auth.register] identity record for '%s' failed: %s", client_id, exc)

        try:
            ttl = max(60, min(int(data.get("ttl", 1800)), 86400))
        except (TypeError, ValueError):
            ttl = 1800
        try:
            minted = self.iam.issue_session_token(client_id, ttl)
        except PermissionError as e:
            return _err(rid, -32001, str(e))
        return _ok(rid, {"status": "registered", "user_id": client_id,
                         "session_token": minted["session_token"],
                         "expires_at": minted["expires_at"], "role": "user", "tier": "free"})

    def _handle_account_delete(self, rid, data, session, role) -> dict:
        """Self-service account deletion — the caller erases their OWN account. Deletes:
        the identity (soft-deleted in IAM: active=False, so the login can never be used
        again but the record is retained as the legally-required audit trail), the entire
        private cell (l_cortex.db — every recipe, personal food, measurement, and private
        atom the user authored), and the entitlement/plan entry. It never targets another
        user, and it does not touch the shared nucleus/catalogue.

        Requires an explicit confirmation (`confirm=true` or `confirm=<your user_id>`) so a
        stray call can't wipe an account. Guests (no account) and admins (removed via
        user-management so the Cell can't be locked out of its last admin) are refused."""
        uid = session.client_id
        confirm = str(data.get("confirm", "")).strip().lower()
        if confirm not in ("true", "yes", "1", "delete", uid.lower()):
            return _err(rid, -32602,
                        "auth.account.delete requires confirm=true (irreversible: this "
                        "erases your account, recipes, personal foods, and measurements).")
        # "has no account" and "is the operator" are both read off the assignment file now: no
        # line of its own falls back to `guest` (§4 step 1); the operator holds the `admin` row.
        if not _gate.lines_for(uid) or self.iam.is_system_identity(uid):
            return _err(rid, -32001, "This session has no deletable account.")
        if _gate.gate(uid, _gate.ADMIN)[0]:
            return _err(rid, -32001,
                        "Admin accounts are removed via user management, not self-deletion "
                        "(prevents locking the Cell out of its last admin).")
        # 1. Identity → soft-delete (audit retained).
        try:
            self.iam.deregister_client(uid)
        except (KeyError, ValueError) as e:
            return _err(rid, -32001, f"Account deletion failed: {e}")
        # 2. Entitlement/plan entry → purge.
        try:
            self._nucleus().vault_delete("entitlement", uid)
        except Exception as e:
            logger.warning("[account.delete] entitlement purge for '%s' failed: %s", uid, e)
        # 3. Private cell (all user-authored data) → erase.
        purged = False
        try:
            purged = bool(self.manager.purge_client_cell(uid))
        except Exception as e:
            logger.warning("[account.delete] cell purge for '%s' failed: %s", uid, e)
        # 4. Drop the live session (token can no longer resolve an active identity).
        try:
            self.manager.close_session(uid)
        except Exception:
            pass
        return _ok(rid, {"status": "deleted", "user_id": uid, "cell_purged": purged,
                         "note": "identity retained as audit (deactivated); all private "
                                 "data erased. Sign-in with this id is no longer possible."})

    def _handle_auth_plan(self, rid, session) -> dict:
        """Read the caller's entitlement tier (product-neutral)."""
        uid = session.client_id
        return _ok(rid, {"user_id": uid, "tier": self._get_plan(uid)})

    def _handle_auth_plan_set(self, rid, data, session) -> dict:
        """(admin) Set a user's entitlement tier — the server-side billing hook. An
        external billing service validates the store receipt (App Store / Play) and then
        calls this with an admin token; the client can never set its own plan."""
        err = self._assert_admin(session)
        if err:
            return _err(rid, -32003, err)
        uid  = (data.get("user") or data.get("user_id") or "").strip()
        tier = (data.get("tier") or "").strip().lower()
        if not uid or tier not in ("free", "paid"):
            return _err(rid, -32602, "auth.plan.set requires user=<id> and tier=free|paid.")
        self._set_plan(uid, tier)
        return _ok(rid, {"status": "set", "user_id": uid, "tier": tier})

    # ------------------------------------------------------------------
    # Memory handlers
    # ------------------------------------------------------------------




    # ------------------------------------------------------------------
    # Weaver — constituent-word → protoword links
    # ------------------------------------------------------------------








    # ------------------------------------------------------------------
    # Unified post-write hook
    # ------------------------------------------------------------------







    def _member_group_engines(self, session, scopes):
        """(gid, engine) for each group the caller is a scoped member of.

        Read / navigation handlers use this to surface atoms shared into the
        caller's groups — the same associative reach a member has via `look`.
        Other members' PRIVATE atoms never live in the group space (they carry
        owner:/view: scopes, not scope:group_<gid>), so scope does the
        black-holing automatically: a member sees the shared graph but not each
        other's private cortex."""
        out = []
        for gid, ge in getattr(session, 'group_engines', {}).items():
            if f"scope:group_{gid}" in scopes:
                out.append((gid, ge))
        return out

    # ── B4 §A5 — as-of reads (durable universe only) ─────────────────────────────
    _ASOF_HORIZON_PREFIXES = ("set:stage:", "set:exec:", "set:cache:", "cronon:", "hydrate", "store:")
    # B4-b — methods that read a horizon / accelerator inventory (never durable history): as_of is not
    # defined for them, so they refuse it with -32602 like a horizon Set/atom read (§A5).
    _ASOF_HORIZON_METHODS = frozenset({"hydrate.ls", "hydrate.verify", "store.status",
                                       "cache.plan", "cache.stat"})
    _ASOF_MAX_WALK = 5000                 # as-of reads count against the search budget (A57); over → partial













    # ------------------------------------------------------------------
    # Alias handlers
    # ------------------------------------------------------------------



    # ------------------------------------------------------------------
    # Ontology dump & collision report
    # ------------------------------------------------------------------


    # ------------------------------------------------------------------
    # Ontology export  (DB → .ak files)
    # ------------------------------------------------------------------


    # ------------------------------------------------------------------
    # Ontology reload / reset
    # ------------------------------------------------------------------










    def _handle_iam_grants(self, rid, data, session) -> dict:
        """`iam.grants` lists a principal's grants (own, or any for an admin)
        (capability-delegation-iam-spec §4.1)."""
        iam = self.iam
        client_id = getattr(session, "client_id", "")
        role = getattr(session, "role", None)
        target = (data.get("grantee") or data.get("id") or client_id).strip()
        # A non-admin may only list its OWN grants.
        if target != client_id:
            from lib.akasha.identity import Capability
            pol = iam._policies.get(role)
            if not (pol and pol.has(Capability.IAM_MANAGE)):
                return _err(rid, -32001, "listing another principal's grants requires admin")
        return _ok(rid, {"grantee": target, "grants": iam.grants_list(target)})

    def _handle_iam_revoke(self, rid, data, session) -> dict:
        """`iam.revoke` — IAM_MANAGE-gated (enforced by METHOD_TO_ACTION)."""
        iam = self.iam
        grantee = (data.get("grantee") or "").strip()
        gid = (data.get("grant_id") or data.get("id") or "").strip()
        if not grantee or not gid:
            return _err(rid, -32602, "iam.revoke requires grantee= and grant_id=")
        ok = iam.grant_revoke(grantee, gid)
        return _ok(rid, {"revoked": ok, "grantee": grantee, "grant_id": gid})

    def _handle_iam_grant(self, rid, data, session) -> dict:
        """Admin composes per-client authority as grants (capability-delegation-iam-spec §4.1).
        `iam.grant` is IAM_MANAGE-gated (enforced by METHOD_TO_ACTION). The bounded sub-admin
        request→approve flow (§4.2) and enterprise signing are staged."""
        iam = self.iam
        client_id = getattr(session, "client_id", "")
        grantee = (data.get("grantee") or "").strip()
        capability = (data.get("capability") or data.get("cap") or "").strip().lower()
        resource = (data.get("resource") or "*").strip()
        if not grantee or not capability:
            return _err(rid, -32602, "iam.grant requires grantee= and capability=")
        # Fail-closed: only known, delegable capabilities may be granted.
        from lib.akasha.identity import Capability
        try:
            Capability(capability)
        except ValueError:
            return _err(rid, -32602, f"unknown capability '{capability}'")
        # Reserved-unit safety for service grants: a grant selector may never cover the
        # writer/root or job units (service-extension-and-delegation-spec §5).
        if capability == Capability.SVC_OPERATE.value:
            if resource in ("*", "svc:*") or resource.startswith(("svc:cell", "job:")):
                return _err(rid, -32003,
                            "svc_operate grant selector may not cover svc:cell/job:* "
                            "(use svc:app:<operator>:* — never the writer/root)")
        verbs = data.get("verbs") or "*"
        expires = data.get("expires")
        grant = iam.grant_add(grantor=client_id, grantee=grantee, capability=capability,
                              resource=resource, verbs=verbs, expires=expires)
        return _ok(rid, {"granted": grant})

    # svc.ls fields that are safe to reveal to a plain READ caller (e.g. a network guest on
    # a deployment that exposes the RPC, like thesaurus08). The respawn RECIPE (argv/env), the
    # pid, filesystem log paths, and deps are internal machinery — shown only to a holder of
    # SVC_OPERATE (operators/admin), never leaked to a reader.
    _SVC_LS_PUBLIC_FIELDS = ("id", "kind", "state", "engine", "host", "port",
                             "live", "restart", "substrate", "trust", "serve_only", "detail")

    def _svc_plane(self, rid):
        """The Supervisor plane for the svc.* ops: (supervisor_module, Supervisor, Capability, None) or
        (None, None, None, error_response) when the supervisor is unavailable."""
        try:
            from lib.harmonia import supervisor as sv
            from lib.akasha.identity import Capability
        except Exception as exc:
            return None, None, None, _err(rid, -32603, f"supervisor unavailable: {exc}")
        return sv, sv.Supervisor(self.base_dir), Capability, None

    def _handle_svc_ls(self, rid, data, session) -> dict:
        """`svc ls` lists the run-dir. Only an operator (base SVC_OPERATE — admin today) sees the full
        descriptor; a plain reader gets a redacted operational view with no recipe/pid/paths. Authz
        (svc.read) is enforced by the dispatcher via METHOD_TO_ACTION before this handler runs."""
        sv, sup, Capability, err = self._svc_plane(rid)
        if err is not None:
            return err
        units = sv.list_units(self.base_dir)
        pol = self.iam._policies.get(getattr(session, "role", None))
        if not (pol and pol.has(Capability.SVC_OPERATE)):
            units = [{k: u[k] for k in self._SVC_LS_PUBLIC_FIELDS if k in u} for u in units]
        return _ok(rid, {"units": units})

    def _svc_operate(self, rid, data, verb: str) -> dict:
        """Operate one unit over RPC: `svc start/restart` respawn from the persisted recipe (P1) —
        spawned HERE, in the daemon that hosts the Supervisor (P3), never by the client. Authz
        (svc.operate) is enforced by the dispatcher via METHOD_TO_ACTION before this runs."""
        sv, sup, Capability, err = self._svc_plane(rid)
        if err is not None:
            return err
        unit_id = (data.get("id") or data.get("name") or "").strip()
        if not unit_id:
            return _err(rid, -32602, "svc requires id=<unit>")
        if not unit_id.startswith(("svc:", "job:")):
            unit_id = f"svc:{unit_id}"
        # Reserved units are never client-operable via this path (writer/root + jobs).
        if verb in ("start", "restart") and unit_id == "svc:cell":
            return _err(rid, -32003, "svc:cell is the daemon root — not restartable via RPC")
        if unit_id.startswith("job:"):
            return _err(rid, -32003, "job units are executor-owned, not svc-operable")
        try:
            result = getattr(sup, verb)(unit_id)
        except Exception as exc:
            return _err(rid, -32603, f"svc svc.{verb} failed: {exc}")
        if isinstance(result, dict) and result.get("error"):
            return _err(rid, -32003, result["error"])
        return _ok(rid, result)

    def _handle_svc_start(self, rid, data) -> dict:
        return self._svc_operate(rid, data, "start")

    def _handle_svc_restart(self, rid, data) -> dict:
        return self._svc_operate(rid, data, "restart")

    def _handle_svc_stop(self, rid, data) -> dict:
        return self._svc_operate(rid, data, "stop")


    # ------------------------------------------------------------------
    # Exploration
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Scope session state (sys.scope.*)
    # ------------------------------------------------------------------


    # ------------------------------------------------------------------
    # Display Focus
    # ------------------------------------------------------------------






















    # ------------------------------------------------------------------
    # Exploration
    # ------------------------------------------------------------------













    # ------------------------------------------------------------------
    # Graph Tree (link-traversal tree view)
    # ------------------------------------------------------------------


    # ------------------------------------------------------------------
    # Dive / View (consciousness layer)
    # ------------------------------------------------------------------







    # ------------------------------------------------------------------
    # Sets
    # ------------------------------------------------------------------






    # ------------------------------------------------------------------
    # JCL (job.*)
    # ------------------------------------------------------------------





    # ------------------------------------------------------------------
    # Workflow (workflow.*) — a stored CSL script run as an orchestrated JCL job.
    #
    # Minimal reception layer (jcl/workflow_vocab). A workflow is one executable
    # atom whose body is a CSL script; running it submits ONE bounded JCL job with a
    # single `csl.run` step, so it inherits the whole orchestration stack (priority,
    # bounded retry/timeout, single-route guard, workspace rollback). Step-granular
    # DAG projection (ref:therefore/ref:if traversal, $var→edges, conditions) is the
    # post-launch work the reserved vocabulary is there to receive.
    # ------------------------------------------------------------------






    # ------------------------------------------------------------------
    # Macro (macro.*) — G4 §3.2: a saved, PARAMETERIZED CSL script that is a coarser reader
    # expressed as Set operations. The saved-script mechanism is workflow.def/run (workflow.* stays
    # for compatibility); macros add (a) named parameters with defaults, bound as $name at run, and
    # (b) a synchronous `as=inline` mode that runs read-only for ANY admitted agent (the per-call
    # capability gate still denies writes to a guest) and renders the last result — vs the default
    # background-job mode that, like workflow.run, needs admin/librarian.
    # ------------------------------------------------------------------








    # ------------------------------------------------------------------
    # Locale (locale.*)
    # ------------------------------------------------------------------



    # ------------------------------------------------------------------
    # CSL (csl.*)
    # ------------------------------------------------------------------


    # ------------------------------------------------------------------
    # Onboarding (sys.onboarding.*)
    # ------------------------------------------------------------------


    # ------------------------------------------------------------------
    # Log (log.*)
    # ------------------------------------------------------------------








    # ------------------------------------------------------------------
    # Whiteboard (wb.*)
    # ------------------------------------------------------------------








    # ------------------------------------------------------------------
    # Cross-concept intersection (sys.cross.*)
    # ------------------------------------------------------------------






    # ------------------------------------------------------------------
    # Jataka
    # ------------------------------------------------------------------









    # ── nebula — the cartographer: inductive concept-model discovery ──────────────────────
    #
    # The third explorer (assoc=local, dream=pairwise, nebula=global). Surveys the whole
    # meaning-universe for REGIONS becoming a concept model — dense clumps of atoms that
    # independently grew the SAME schema (shared relation signature) — and PROPOSES them
    # with an inferred salient-rel profile. Like dream it runs as a LOW-priority background
    # job ("the surveyor of the universe") and only PROPOSES: a human confirms + names, which
    # plants the cluster set + rel:salient profile and emits a concept-model skeleton to review.
    # Proposals live in the nucleus vault (focus-less — nebula has no single anchor atom).












    # ------------------------------------------------------------------
    # Contexa
    # ------------------------------------------------------------------





    # ------------------------------------------------------------------
    # General file import/export — the single disk-I/O route (io.*)
    # ------------------------------------------------------------------


    # The kernel builds pipeline endpoints from injected closures so lib/harmonia/pipeline.py
    # stays graph-agnostic (it never imports akasha). io.* is just "wire a Source to a Sink".











    # ── Contexa ingest / Jataka present — the client session's I/O sides ──────────
    # These are the survey round-trip on the pipe: Contexa reads collected responses IN (with
    # macro context-binding), the client projects/analyses via concept models (lens / table),
    # and Jataka presents OUT. Consciousness is the substrate both flow through — Contexa's
    # writes are auto-woven; Jataka's reads pass through generate_view — never a pipe endpoint.








    # ------------------------------------------------------------------
    # Associate (kernel.associate + associate.unwritten)
    # ------------------------------------------------------------------






    # ------------------------------------------------------------------
    # Guest session handlers
    # ------------------------------------------------------------------

    def _handle_guest_create(self, rid: str, data: dict) -> dict:
        """
        Claim a pool slot and issue a self-verifying guest binding token tied to it.
        No authentication required — any HTTP client may call this.  Returns an
        opaque binding_key (prefix "gbk:") signed with the Akasha HMAC secret.
        """
        # Clamp the token TTL to the pool's inactivity TTL.  A token that outlives
        # its slot could otherwise re-activate a slot that has since been reclaimed
        # (and possibly handed to another visitor), so the two must not diverge.
        _pool_ttl = getattr(getattr(self.manager, "guest_pool", None), "ttl", 600)
        try:
            _req_ttl = int(data.get("ttl", _pool_ttl))
        except (TypeError, ValueError):
            _req_ttl = _pool_ttl
        ttl     = max(60, min(_req_ttl, _pool_ttl))
        slot_id = self.manager.checkout_guest_session()
        if slot_id is None:
            return _err(rid, -32000, "Guest pool exhausted — try again shortly.")
        binding = self.iam.guest_bindings.create_for_session(slot_id, ttl)
        return _ok(rid, {
            "binding_key": binding["binding_key"],
            "expires_at":  binding["expires_at"],
            "ttl":         ttl,
        })

    def _handle_guest_extend(self, rid: str, raw_token: str, data: dict) -> dict:
        """
        Issue a replacement token for the same session with a fresh TTL.
        Also touches the pool slot so the sweeper doesn't reclaim it early.
        Returns a new binding_key; the client should switch to it.
        """
        if not self.iam.guest_bindings.is_guest_key(raw_token):
            return _err(rid, -32001, "session.guest.extend requires a guest binding key.")
        try:
            _pool_ttl = getattr(getattr(self.manager, "guest_pool", None), "ttl", 600)
            try:
                _req_ttl = int(data.get("ttl", _pool_ttl))
            except (TypeError, ValueError):
                _req_ttl = _pool_ttl
            ttl    = max(60, min(_req_ttl, _pool_ttl))
            result = self.iam.guest_bindings.extend(raw_token, ttl)
            self.manager.touch_guest_session(result["session_id"])
            return _ok(rid, {
                "binding_key": result["binding_key"],
                "expires_at":  result["expires_at"],
                "ttl":         ttl,
            })
        except PermissionError as e:
            return _err(rid, -32001, str(e))

    def _handle_session_ctx_set(self, rid: str, data: dict, session) -> dict:
        """Store a context value in the current Akasha session."""
        key   = data.get("key")
        value = data.get("value")
        if not key:
            return _err(rid, -32602, "session.context.set requires 'key'.")
        session.set_context(key, value)
        return _ok(rid, {"key": key, "stored": True})

    def _handle_session_ctx_get(self, rid: str, data: dict, session) -> dict:
        """Retrieve a context value from the current Akasha session."""
        key = data.get("key")
        if not key:
            return _err(rid, -32602, "session.context.get requires 'key'.")
        return _ok(rid, {"key": key, "value": session.get_context(key)})

    # ------------------------------------------------------------------
    # Plugin registration
    # ------------------------------------------------------------------

    def _register_harmonia_plugins(self):
        """Wire up the cognitive metabolism plugins that Harmonia orchestrates.

        nlp.extract is registered by lib/harmonia/plugins/__init__.py (MultiLocaleNLP
        via SpaCy) and is already present in self.harmonia._plugins by the time this
        method runs.  No kernel-level override is needed.
        """
        if not self.harmonia:
            return
        logger.info("[Kernel] Harmonia plugin hook ready (nlp.extract via plugins/__init__)")
