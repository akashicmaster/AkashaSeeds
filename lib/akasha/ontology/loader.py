"""
The boot load — REGISTRY / PACK.json → JCL jobs, per-pack sentinels, the global-relations phase, the weave queue, the post-load phase — moved out of the kernel (backend layout order 2026-09-20).

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
import shlex
import functools
from typing import Dict, Any, Optional, List, Callable

from lib.akasha.identity import Role, Capability
from lib.akasha import lexicon
from lib.akasha.api.heart import _rss_mb, _open_fd_count, _fd_soft_limit

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

logger = logging.getLogger("Akasha.Kernel")


# ── one CONTENT KEY per file (group 1, 1.1) ───────────────────────────────────────────────────────
# Every "has this file changed?" question the loader asks is answered by ONE key: the sha256 of the
# file with its `#` comment lines and blank lines removed. Three different keys used to answer it —
# the pack manifest on (basename:size), the per-file atom sentinel on size, the relations gate on
# (mtime:size) then the raw bytes — so a header comment re-parsed a pack and a fresh extraction (all
# mtimes new) re-read every file. A comment is not content, and an mtime is never a key.
#
# Computed once per boot per file (cached on the kernel by path + stat), streamed line by line.

def content_key(path: str, cache: Optional[Dict] = None) -> str:
    try:
        st = os.stat(path)
        tag = (path, st.st_mtime_ns, st.st_size)
    except OSError:
        return ""
    if cache is not None and tag in cache:
        return cache[tag]
    h = hashlib.sha256()
    try:
        with open(path, "rb") as fh:
            for raw in fh:
                s = raw.strip()
                if not s or s.startswith(b"#"):
                    continue
                h.update(raw.rstrip(b"\r\n"))
                h.update(b"\n")
    except OSError:
        return ""
    ck = h.hexdigest()[:16]
    if cache is not None:
        cache[tag] = ck
    return ck


def project_dir() -> str:
    """The project root the ontology and its config are read from. `AKASHA_PROJECT_DIR` overrides it
    so an eval can run the REAL loader over a small ontology of its own — the loader's evals used to
    mirror its logic in a copy, which is a check that cannot see the code it is checking."""
    env = (os.environ.get("AKASHA_PROJECT_DIR") or "").strip()
    if env:
        return env
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def boot_load_ontology(kernel) -> None:
    """The `load` phase body, and the producer of the `ontology.loaded` gate.

    Declared `provides: "ontology.loaded"` in the ontology manifest, so every schedule that
    declares `after: "ontology.loaded"` is held until this returns — however it returns. That is
    what the `finally` is for: this function has a dozen early exits (no JCL, no admin yet,
    sentinels already present, a pack that fails), and a gate opened on only the happy path is a
    gate that strands its consumers on exactly the boots where something went wrong.

    A workload's provisioning is such a consumer: its templates resolve ontology atoms, so
    provisioning before the packs are in writes a workflow against a graph that does not exist
    yet. It waits; it does not poll."""
    from lib.akasha.api import schedule as _sched
    _sched.mark_running(kernel, "ontology.loaded")
    _sched.mark_running(kernel, "ontology.normalized")
    try:
        _boot_load_ontology(kernel)
    finally:
        # 1.3 — TWO gates. `ontology.loaded` (atoms + global relations) is opened inside the load
        # the moment the relations are applied; `ontology.normalized` (the reconcile) when the
        # load returns. Both are opened here too, however the load ended, for the same reason as
        # before: a gate opened only on the happy path strands its consumers on the bad boots.
        if not _sched.gate_open(kernel, "ontology.loaded") or _sched.is_running(kernel, "ontology.loaded"):
            _sched.open_gate(kernel, "ontology.loaded")
        _sched.open_gate(kernel, "ontology.normalized")
        publish_in_flight(kernel, clear=True)


def _boot_load_ontology(kernel) -> None:
    """
    Queue all ontology files (.ak and .csl) as JCL jobs on kernel boot if
    sentinels are absent.  Runs in a daemon thread — never blocks boot.

    Requires an admin user in IAM (created via genesis_rite).  If no admin
    exists yet (first boot before genesis), this is a no-op.
    """
    import time as _time
    import hashlib as _hl
    import shlex as _shlex
    from lib.akasha import lifecycle

    if not JCLJob or not JCLStep:
        return  # JCL imports failed at module load

    # Serve-only worker (spawned by akasha.py alongside the loader main process):
    # the MAIN process is the SOLE nucleus writer (it runs this boot-load + the
    # learn daemons). The uvicorn worker boots its own gateway against the SAME
    # nucleus; if it ALSO ran the boot-load, two processes would import the ontology
    # into the one store at once — a single-writer violation that kills the worker
    # on first boot ("Dead (Check logs)"), which is exactly what a slow full re-import
    # (bigger than the launcher's sentinel wait) triggered. Skip it here; the worker
    # only serves reads while main loads (WAL → concurrent readers are safe).
    if os.environ.get("AKASHA_SERVE_ONLY", "").strip().lower() not in ("", "0", "no", "false", "off"):
        logger.info("[Kernel] AKASHA_SERVE_ONLY — skipping ontology boot load (serve-only worker)")
        return

    # Boot memory heartbeat — self-diagnosis for a SILENT daemon death during the load
    # (OOM-killer SIGKILL / C-ext segfault leave NO Python traceback, so the process just
    # stops logging). This logs RSS every few seconds until the load finishes or shutdown,
    # so the LAST line before a silent death shows whether RSS was climbing to the host
    # ceiling (→ OOM) or flat (→ a hard crash, e.g. a C-extension on a bleeding-edge
    # interpreter). No operator dmesg needed — Akasha reports its own memory.
    if not getattr(kernel, "_bootwatch_running", False):
        kernel._bootwatch_running = True            # one heartbeat per process, not per reload
        def _bootwatch():
            _t0 = _time.time(); _peak = 0; _idle = 0; _memtop_done = False
            _fdwarn_done = False
            _CAP = 900.0                                    # bounded to the boot window (~15min)
            try:
                _memtop_at = int(os.environ.get("AKASHA_MEMTOP_MB", "2500"))
            except (TypeError, ValueError):
                _memtop_at = 2500
            while not lifecycle.is_shutting_down() and _time.time() - _t0 < _CAP:
                rss = _rss_mb()
                if rss is not None:
                    _peak = max(_peak, rss)
                    # Automatic memory-culprit report (no operator step, per the seeds-only
                    # principle): the FIRST time RSS crosses the threshold, walk the GC heap and
                    # log the largest in-memory containers, so a runaway structure (a design
                    # violation — the store is meant to live on disk, not in RAM) names itself in
                    # the log. One-shot per boot; tunable via AKASHA_MEMTOP_MB.
                    if not _memtop_done and rss >= _memtop_at:
                        _memtop_done = True
                        # Automatic memory-culprit report (no operator step): the largest
                        # in-memory containers + the Silica index per @route + the guest-cell
                        # footprint. Shared with the permanent health heartbeat's high-water dump.
                        kernel._dump_memtop(rss, reason="boot")
                    # name the JCL job in flight, if any — ties an RSS spike to a phase.
                    _cur = ""
                    try:
                        _jobs = kernel.jcl_worker.list_jobs() if kernel.jcl_worker else []
                        _run = [j for j in _jobs if getattr(j, "status", "") == "RUNNING"]
                        if _run:
                            _cur = getattr(_run[0], "label", "") or ""
                    except Exception:
                        _cur = ""
                    # R2/F28b — surface the open-FD count (and a one-shot WARN at 70 % of the
                    # soft limit, naming the biggest consumer class) so an approaching ulimit is
                    # visible BEFORE a guest cell open crashes with Errno 24.
                    _fds = _open_fd_count()
                    _fdlim = _fd_soft_limit()
                    _fdstr = ("%d/%d" % (_fds, _fdlim)) if (_fds is not None and _fdlim) \
                        else (str(_fds) if _fds is not None else "?")
                    if (not _fdwarn_done and _fds is not None and _fdlim
                            and _fds >= 0.7 * _fdlim):
                        _fdwarn_done = True
                        try:
                            _gp = getattr(getattr(kernel, "manager", None), "guest_pool", None)
                            _guests = _gp.stats().get("in_use", "?") if _gp is not None else "?"
                        except Exception:
                            _guests = "?"
                        logger.warning("[BootWatch] open FDs %d/%d ≥ 70%% of the soft limit — the "
                                       "likely consumer is per-client cell stores (active guests=%s; "
                                       "each private silica cortex holds ~1 WAL FD). Raise the "
                                       "ulimit or reduce concurrency.", _fds, _fdlim, _guests)
                    logger.info("[BootWatch] rss=%dMB peak=%dMB fds=%s t=%.0fs job=%s",
                                rss, _peak, _fdstr, _time.time() - _t0, _cur or "-")
                    # Once the load has been quiet (no running job) for a while, stop — the
                    # boot window is over; no need to heartbeat steady-state forever.
                    _idle = _idle + 1 if not _cur else 0
                    if _idle >= 10:                         # ~30s idle after the load settled
                        logger.info("[BootWatch] load settled — heartbeat off (peak=%dMB)", _peak)
                        kernel._bootwatch_running = False
                        return
                for _ in range(6):                          # ~3s, but wake promptly on shutdown
                    if lifecycle.is_shutting_down():
                        return
                    _time.sleep(0.5)
            kernel._bootwatch_running = False
        import threading as _thr_bw
        _thr_bw.Thread(target=_bootwatch, name="boot-memwatch", daemon=True).start()

    # Wait briefly so the JCL worker threads are fully started
    _time.sleep(0.5)

    try:
        # Verify admin exists and has librarian privileges
        from lib.akasha.identity import Role
        try:
            admin_role = kernel.iam.authenticate("admin")
        except PermissionError:
            # No admin yet. If the deployer provisioned an admin passphrase
            # out-of-band (AKASHA_ADMIN_PASS), self-initialize now so a fresh
            # seed comes up FULLY AUTOMATIC — no interactive genesis ceremony,
            # no operator step. genesis_rite re-triggers this boot-load on its
            # own thread when it succeeds, so we return either way.
            kernel._maybe_auto_genesis()
            return  # admin absent (or auto-genesis kicked off a fresh load)

        if admin_role not in (Role.ADMIN, Role.LIBRARIAN):
            return

        from lib.akasha.api import authority as _authority
        admin_session = _authority.elevated(kernel, "ontology.load")

        # Start the post-load daemons FIRST — before any of the ontology-load phases below, each
        # of which can `return` early (the atoms-loaded wait, the global-relations job wait, the
        # curation-sentinel gate). Placed late, ANY of those returns silently strands the corpus
        # bootstraps and the learners (the VPS symptom: svc:bl-bootstrap / svc:mobility-bootstrap
        # never appeared, the corpora never loaded). These daemons only spawn threads that
        # self-gate on the RELATIONS phase (they poll _relations_ready()), so starting them up
        # front is safe and makes them impossible to skip. Guarded to run once per process.
        if not getattr(kernel, "_boot_daemons_started", False):
            kernel._boot_daemons_started = True
            kernel.api.schedules.run_phase(kernel, "post_load")   # the manifests' post-load bodies, in order
            # F60 §2 — the writer-role lifecycle daemons (health heartbeat, wal maintenance,
            # pulse compact, telemetry/broadcast gc, semcache replan, alloc trace) NO LONGER live
            # here: an early `return` in the load phases below stranded them (daemon-#2 incident).
            # They now start from __init__ via _start_writer_role_daemons(), independent of this
            # path. Only the corpus bootstraps + learners (which genuinely follow the load) remain.

        # Locate ontology directory relative to project root
        _project_dir = project_dir()
        _roots = ontology_roots()
        if not _roots:
            logger.info("[Kernel] No pack root found — skipping boot load")
            return
        ont_dir = _roots[0]

        def _collect(ext: str) -> List[str]:
            files: List[str] = []
            for root_d, _, names in (w for _r in _roots for w in os.walk(_r)):
                for n in sorted(names):
                    if n.endswith(ext):
                        files.append(os.path.join(root_d, n))
            return files

        def _submit_file_job(fpath: str, steps_raw: List[dict], label: str):
            steps = [JCLStep(method=s["method"], params=s.get("params", {}))
                     for s in steps_raw]
            job = JCLJob(owner="admin", label=label, steps=steps, fail_fast=False)
            # Ontology atom phase — Class 2 (consistent as a set, not real-time).
            return kernel.harmonia.submit_job(job, job_class=CLASS_BATCH_ATOM)

        # ── .ak files (vocab / thesaurus links) ───────────────────────────
        # The `.ak` line parser lives at module level (`parse_ak_line`) so the reconcile's keep-set
        # reads a def exactly as this load writes it (D16).
        _parse_ak_line = parse_ak_line

        # ── .ak files — two-phase load to eliminate ordering races ──────────
        # Phase 1: atom-only jobs (write/define/alias/set.add — NO links).
        #          The last atom job gets an "atoms:loaded" sentinel appended.
        # Phase 2: boot-load thread polls for the sentinel, then submits ONE
        #          link job containing ALL ln steps from ALL files.  By the
        #          time the link job runs every atom is guaranteed to be in
        #          nucleus, so alias resolution cannot fail on ordering.

        # Manifest hash: sha256 of (basename:size) for all files. Stat-only (no file
        # reads), so it is fast even for large ontologies, and it gates the PACK-LEVEL
        # phases (load / reconcile / csl / curations) — "did this pack's content change?"
        #
        # ⚠️ mtime is DELIBERATELY EXCLUDED. The seed self-extractor (python akasha_seeds_*.py)
        # is the supported deploy/recovery path, and unzip stamps EVERY extracted file with a
        # fresh mtime (it does not restore the source time). An mtime-inclusive manifest
        # therefore flipped every pack's hash on every re-extraction → every one of the ~25
        # packs re-entered load AND re-materialised its def-keys for reconcile (the heavy pass
        # that OOM-killed the Cell daemon; see the per-pack reconcile fix). That made the
        # per-pack incremental gating a no-op for the ONE path users actually deploy through.
        # Keying on (basename:size) is stable across re-extraction, so a deploy reloads ONLY
        # the packs whose content genuinely changed (different file list or byte size).
        #
        # A size-preserving edit (same byte count, changed bytes) is invisible to THIS gate,
        # but it is still caught downstream: the global-relations phase gates each file by a
        # full CONTENT hash and re-applies changed al/ln/set; the per-file atom sentinel is
        # likewise size-keyed, so mtime never bought an atom re-import here in the first place.
        # NOTE: re-import is ADDITIVE (content-addressed) — it applies additions and edits but
        # does not purge atoms deleted from the ontology; wipe <data>/central for a clean slate.
        # Group 1 (1.1): the manifest is the files' CONTENT KEYS (comments and blank lines out), so
        # a header comment changes nothing and a byte-count-preserving edit is still a change.
        _ck_cache = getattr(kernel, "_onto_ck_cache", None)
        if _ck_cache is None:
            _ck_cache = kernel._onto_ck_cache = {}

        def _ck(f: str) -> str:
            return content_key(f, _ck_cache)

        def _manifest_hash(files: List[str]) -> str:
            parts = ["%s:%s" % (os.path.basename(f), _ck(f) or "-") for f in sorted(files)]
            return _hl.sha256("\n".join(parts).encode()).hexdigest()[:16]

        # ── Pack loading — flat ontology/{name}/ structure ─────────────
        # Packages are defined in ontology/REGISTRY.json.
        # autoload:true  → always loaded (base)
        # autoload:false → loaded only when listed in config/ontology/packs.json["enabled"]
        # Each pack has its own two-phase sentinel:
        #   ont:ak:atoms:loaded:{pack}:{hash}  — phase-1 complete
        #   ont:ak:loaded:{pack}:{hash}         — phase-2 complete

        # Directories under ontology/ that are NOT packs, named by the registry itself
        # (`"reserved_dirs": [...]` in REGISTRY.json). The loader used to name two series here
        # (group 4, 4.9); neither directory exists any more, and a series is not the loader's word.
        RESERVED_DIRS = reserved_dirs()

        def _collect_from_dir(d, ext):
            files = []
            if os.path.isdir(d):
                for root_d, _, names in os.walk(d):
                    for n in sorted(names):
                        if n.endswith(ext):
                            files.append(os.path.join(root_d, n))
            return sorted(files)

        def _read_registry():
            return registry_packages()

        def _read_enabled_packs():
            import json as _json
            cfg = os.path.join(_project_dir, "config", "ontology", "packs.json")
            try:
                with open(cfg, "r") as _f:
                    return set(_json.load(_f).get("enabled", []))
            except Exception:
                return set()

        def _read_load_all():
            # Service tiers (thesaurus/enterprise) ship config/ontology/packs.json
            # with "load_all": true — the standing instruction to auto-load EVERY
            # registered pack sequentially (in REGISTRY order), including specialist
            # B/C packs added after the seed was built. The seeds tier omits the
            # flag, so its optional packs stay opt-in (onto.pack.enable).
            import json as _json
            cfg = os.path.join(_project_dir, "config", "ontology", "packs.json")
            try:
                with open(cfg, "r") as _f:
                    return bool(_json.load(_f).get("load_all", False))
            except Exception:
                return False

        # ── Filesystem-based pack sentinel helpers ─────────────────────────
        # These files are the authoritative "was pack X fully loaded?" record.
        # Independent of SQLite WAL behaviour — a plain file on disk survives
        # any backend swap, sync-mode change, or WAL corruption scenario.
        # DB sentinels (ont:ak:atoms:loaded:* / ont:ak:loaded:*) continue to
        # serve as within-session phase-coordination signals only.
        _sent_dir = os.path.join(kernel.base_dir, "central", "sentinels")
        os.makedirs(_sent_dir, exist_ok=True)

        # What this load actually did, for the `[onto]` phase lines (1.6) and for the later phases
        # that must work on the CHANGED packs only (1.2): a pack whose sentinel hit is not changed.
        from lib.akasha.ontology import validate as _validate
        _pack_rules = [r for _r in _roots for r in _validate.declared_rules(_r)]
        _onto_stats = {"unchanged": 0, "refused": [], "changed": [], "atom_jobs": 0,
                       "pack_hash": {}}
        # THE LOAD IN FLIGHT, as data (frontend 09-28, needs platform 1). A consumer that ticks
        # while this runs — the workload driver — asks what the load TOUCHES instead of treating
        # any load as "the graph is not there": `first` (this cell has never finished a pack, so
        # the graph really is empty) and `packs` (the packs found CHANGED so far, appended as the
        # loop finds them; an unchanged pack's atoms are already in place). Cleared when the
        # `ontology.loaded` gate opens.
        publish_in_flight(kernel, first=not _any_pack_sentinel(_sent_dir), packs=[])
        _deferred_weaves: List[tuple] = []        # (pack, JCLJob) — submitted after the gate (1.5)
        _deferred_sentinels: List[tuple] = []     # P2 — (pack, hash, done alias) still landing
        _onto_t0 = _time.time()
        _onto_rss0 = _rss_mb()

        def _phase_tail(t0, rss0) -> str:
            rss1 = _rss_mb()
            return "t=%.1fs Δrss=%s" % (_time.time() - t0,
                                        ("%+dMB" % (rss1 - rss0)) if (rss1 is not None
                                                                     and rss0 is not None) else "?")

        def _poll_after(elapsed: float) -> float:
            """How long to sleep before looking again at a job we are waiting on: short while it is
            young (a small pack's atoms finish in well under a second, and a fixed 5 s poll cost
            every pack five seconds of nothing), longer once it has proved to be a long one."""
            return 0.1 if elapsed < 5 else (1.0 if elapsed < 60 else 5.0)

        def _sent_file(pack_name, phash):
            return os.path.join(_sent_dir, f"{pack_name}_{phash}.done")

        def _sent_exists(pack_name, phash):
            return os.path.exists(_sent_file(pack_name, phash))

        def _write_sent(pack_name, phash):
            path = _sent_file(pack_name, phash)
            with open(path, "w") as _fp:
                _fp.write(str(_time.time()))
                _fp.flush()
                os.fsync(_fp.fileno())
            logger.info("[Kernel] Pack '%s': sentinel file written", pack_name)

        def _wait_boot_job(_job, _alias, _on_done, _stall=1800):
            """F20 — wait on a boot JCL job's LIVENESS, not a wall-clock ceiling. Success = the
            completion `_alias` appears → `_on_done()` gates the sentinel(s). Gives up (the phase
            re-runs next boot) ONLY on a terminal FAILED/CANCELLED, a DONE without its alias, or a
            STALL (no completed-step progress for `_stall` s). A live, progressing job — even one
            past the old 3600 s ceiling — is never aborted by total wall time. Returns True on
            success, False on give-up, None on shutdown (caller should return)."""
            _s0 = _time.time(); _lastp = _s0; _lastd = -1
            while True:
                _time.sleep(_poll_after(_time.time() - _s0))
                if lifecycle.is_shutting_down():
                    return None
                if admin_session.local_cortex.get_aliases_by_pattern(_alias):
                    _on_done()
                    logger.info("[Kernel] boot job %s applied in %.1fs (%s steps)",
                                getattr(_job, "job_id", "?"), _time.time() - _s0,
                                getattr(_job, "step_done", 0))
                    return True
                _st = getattr(_job, "status", ""); _d = getattr(_job, "step_done", 0)
                if _d != _lastd:
                    _lastd = _d; _lastp = _time.time()          # progress → reset the stall clock
                if _st in ("FAILED", "CANCELLED", "DONE"):
                    if _st == "DONE" and admin_session.local_cortex.get_aliases_by_pattern(_alias):
                        _on_done(); return True                 # close the read race
                    logger.warning("[Kernel] boot job %s ended %s WITHOUT completion alias %s "
                                   "(%d steps) — phase re-runs next boot",
                                   getattr(_job, "job_id", "?"), _st, _alias, _d)
                    return False
                if _time.time() - _lastp > _stall:
                    logger.warning("[Kernel] boot job %s STALLED — no progress for %.0fs "
                                   "(status=%s, %d steps) — phase re-runs next boot",
                                   getattr(_job, "job_id", "?"), _time.time() - _lastp, _st, _d)
                    return False

        def _pack_def_aliases(ak_files, cap=512):
            """Up to `cap` aliases `def`'d across a pack's files, in file order. Capped so the
            boot-time presence probe never has to parse a very large pack in full every boot; a
            few hundred defs (spanning past any leading shared-lexicon file into the pack's own
            namespace) is plenty to sample."""
            _al: List[str] = []
            for _fp in ak_files:
                try:
                    with open(_fp, "r", encoding="utf-8") as _f:
                        for _raw in _f:
                            _s = _parse_ak_line(_raw)
                            if _s and _s["method"] == "kernel.memory.define":
                                _a = (_s.get("params") or {}).get("name")
                                if _a:
                                    _al.append(_a)
                                    if len(_al) >= cap:
                                        return _al
                except OSError:
                    continue
            return _al

        def _pack_atoms_present(ak_files):
            """True iff the pack's atoms actually still resolve to stored chunks.

            A `.done` sentinel lives under data/central/sentinels/ (the protected data/ tree,
            preserved across deploys), so it can outlive the atoms it vouches for when the
            nucleus is rebuilt/reset. Verify before trusting a skip. SAMPLE across ALL files —
            the first def is often a SHARED lexicon atom (nsdef:/reldef:) that survives a
            content wipe, so checking only it would miss a gutted pack; the later files carry
            the pack's own namespace. Exact resolution (resolve_alias → chunk), not a LIKE
            probe (pack aliases contain `_`, a LIKE wildcard). Present iff most of the sample
            resolves; on any probe error return True (never spuriously reload a healthy pack)."""
            _defs = _pack_def_aliases(ak_files)
            if not _defs:
                return True   # link-only pack — no atom to verify
            # up to ~16 aliases spread evenly across the (file-ordered) defs so the sample
            # includes the pack's own namespace, not just a leading shared-lexicon block.
            _n = len(_defs); _cap = min(16, _n)
            _sample = [_defs[(_i * _n) // _cap] for _i in range(_cap)]
            try:
                _hits = 0
                for _alias in _sample:
                    # local_cortex has the nucleus attached as a fallback, so this resolves
                    # universal-scope pack atoms too. (resolve_alias lives on the cortex, NOT
                    # the session.)
                    _k = admin_session.local_cortex.resolve_alias(_alias)
                    if not _k:
                        continue
                    try:
                        _present = admin_session.local_cortex.get_chunk_raw(_k)
                    except Exception:
                        _present = True   # can't verify the chunk → the resolved alias is enough
                    if _present:
                        _hits += 1
                return _hits >= (len(_sample) + 1) // 2   # majority present → trust the sentinel
            except Exception:
                return True

        def _file_unbound_defs(fpath):
            """The def names in this file that do NOT resolve to the key this file's line defines,
            or whose atom is not live (evicted). One alias get + one point get per def; asked only
            for a pack that is loading anyway (R1/R4: O(the changing pack), never O(store))."""
            _nuc_core = getattr(getattr(admin_session, "nucleus", None), "core", None)
            if _nuc_core is None:
                return []
            out = []
            for _nm, _key in file_def_keys(fpath):
                try:
                    if _nuc_core.get_key_by_alias(_nm) != _key:
                        out.append(_nm)
                        continue
                    _row = _nuc_core.get_chunk_raw(_key)
                    if not _row or str(_row.get("status") or "") == "evicted":
                        out.append(_nm)
                except Exception:
                    continue
            return out

        def _clear_file_relation_sentinels(pack_name, basename):
            """Drop ONE file's relation sentinels (content + stat) so the global relations phase
            re-applies that file's `al` / `ln` / `set.add` this load."""
            import glob as _glob
            _rb = (pack_name + "__" + basename).replace(os.sep, "_").replace(".", "_").replace(":", "_")
            for _pat in ("_relfile_" + _rb + "_*.done", "_relstat_" + _rb + "_*.done"):
                for _p in _glob.glob(os.path.join(_sent_dir, _pat)):
                    try:
                        os.remove(_p)
                    except OSError:
                        pass
            # …and the GLOBAL relations gate, as `_clear_pack_sentinels` does: keyed on relation
            # content that did not change, it would skip the phase whole. Every other file stays
            # gated by its own intact `_relfile_` sentinel, so only this file is re-applied.
            for _store in (getattr(getattr(admin_session, "nucleus", None), "core", None),
                           getattr(admin_session.local_cortex, "core", None)):
                if _store is None:
                    continue
                try:
                    for _row in (_store.get_aliases_by_pattern("ont:ak:relations:all:%") or []):
                        _store.delete_alias(_row["alias"] if isinstance(_row, dict) else _row)
                except Exception:
                    pass

        def _clear_pack_sentinels(pack_name, pmhash):
            """Drop EVERY restart-skip signal for a pack so its next load runs clean:
              • the FS pack sentinel + its per-file relation sentinels (`_relfile_<pack>__*`,
                so the global relations phase re-binds the pack's links/sets);
              • the DB pack aliases `ont:ak:atoms:loaded:*` / `ont:ak:loaded:*` (so the
                `atoms_done` gate doesn't short-circuit phase-1);
              • the DB PER-FILE aliases `ont:ak:f:<pack>:*` — CRUCIAL: each file's atom job
                skips while its per-file sentinel is present, so leaving these behind makes the
                reload a silent no-op (files_to_queue empty → 0 atoms written). Same reason
                onto.reload clears `ont:ak:f:` first."""
            import glob as _glob
            _fs = [_sent_file(pack_name, pmhash)]
            _fs += _glob.glob(os.path.join(_sent_dir, "_relfile_" + pack_name + "__*.done"))
            for _p in _fs:
                try:
                    if os.path.exists(_p):
                        os.remove(_p)
                except OSError:
                    pass
            _db_aliases = [f"ont:ak:atoms:loaded:{pack_name}:{pmhash}",
                           f"ont:ak:loaded:{pack_name}:{pmhash}"]
            try:
                for _row in (admin_session.local_cortex.get_aliases_by_pattern(
                        f"ont:ak:f:{pack_name}:%") or []):
                    _db_aliases.append(_row["alias"] if isinstance(_row, dict) else _row)
            except Exception:
                pass
            # The GLOBAL relations gate (ont:ak:relations:all:<content-hash>) is keyed on the
            # changed relation content — unchanged for this pack, so it would skip re-applying
            # the pack's links/sets even though we just cleared its per-file relfile sentinels
            # (→ blvh:root readable but with no children/sets). Drop the gate so the relations
            # phase re-runs; with only THIS pack's relfile sentinels cleared, it re-applies just
            # this pack's relations (every other pack stays gated by its intact relfile sentinel).
            try:
                for _row in (admin_session.local_cortex.get_aliases_by_pattern(
                        "ont:ak:relations:all:%") or []):
                    _db_aliases.append(_row["alias"] if isinstance(_row, dict) else _row)
            except Exception:
                pass
            # Delete from BOTH stores: per-file/atoms/done sentinels are universal (nucleus),
            # but the global relations-complete alias is written to the admin LOCAL cortex — so
            # a nucleus-only delete leaves the relations gate standing and the pack's links/sets
            # never re-bind. Belt-and-suspenders: try each alias in nucleus AND local cortex.
            for _al in _db_aliases:
                try:
                    _nuc = getattr(admin_session, "nucleus", None)
                    if _nuc is not None:
                        _nuc.core.delete_alias(_al)
                except Exception:
                    pass
                try:
                    admin_session.local_cortex.delete_alias(_al)
                except Exception:
                    pass

        def _load_ak_pack(pack_name, ak_files):
            """
            Three-phase .ak load for one pack.

            Phase 1: atom-only JCL jobs → DB signal ont:ak:atoms:loaded:*
            Phase 2: link JCL job       → DB signal ont:ak:loaded:*
                     → filesystem sentinel {base_dir}/central/sentinels/{pack}_{hash}.done
            Phase 3: weave JCL job      → sys:refers_to + set:word:* links (background)

            The filesystem sentinel is the authoritative restart-skip signal.
            """
            if not ak_files:
                logger.info("[Kernel] Pack '%s': no .ak files — skipping", pack_name)
                return
            _pack_start = _time.time()
            pmhash = _manifest_hash(ak_files)
            _onto_stats["pack_hash"][pack_name] = pmhash

            # Primary restart-skip check: filesystem sentinel — but SELF-HEAL a stale one.
            # The `.done` sentinel is preserved across deploys (it lives under the protected
            # data/ tree), so a sentinel written by an earlier load can outlive the atoms it
            # vouches for when the nucleus is later rebuilt/reset. Trusting it blindly then
            # skips the pack on EVERY boot and its atoms never come back — so a correctly-synced
            # deploy can stay permanently missing a pack (e.g. blvh: sentinel present, atoms gone
            # → blvh:root unreadable across restarts). So verify the atoms actually exist before
            # honoring the skip; if they don't, clear EVERY restart-skip signal for the pack (the
            # FS pack sentinel, its per-file relation sentinels, and the DB atoms/done aliases —
            # any one left behind re-triggers the same skip downstream) and fall through to a
            # clean, idempotent reload.
            if _sent_exists(pack_name, pmhash):
                if _pack_atoms_present(ak_files):
                    _onto_stats["unchanged"] += 1
                    # F48-1.4 — per-pack accounting: a fully-loaded pack costs ~0 (sentinel hit,
                    # nothing parsed or written) and says so in one line, so a boot-heap regression
                    # of this class names itself in the log instead of hiding in an RSS curve.
                    logger.info("[Kernel] pack=%s sentinel=hit parsed=0 written=0 t=%.2fs",
                                pack_name, _time.time() - _pack_start)
                    return
                logger.warning("[Kernel] Pack '%s': sentinel present but atoms MISSING — stale "
                               "sentinel, clearing and reloading", pack_name)
                _clear_pack_sentinels(pack_name, pmhash)
            # §3 — the pack is loaded AS WRITTEN or refused: the rules the application declares in
            # `ontology/*/canon.json` are checked against the pack's own statements BEFORE anything
            # of it is written. A refused pack writes nothing, gets no sentinel (the next boot asks
            # again), and its relations are left out of the global phase. Nothing is repaired.
            _breach = _validate.validate_pack(ak_files, _pack_rules)
            if _breach:
                _onto_stats["refused"].append(pack_name)
                logger.warning("[onto] pack refused pack=%s rule=%s entry=%s at=%s:%d need=%s "
                               "declared_in=%s", pack_name, _breach["rule"], _breach["entry"],
                               _breach["file"], _breach["line"], _breach["need"],
                               _breach.get("declared_in") or "-")
                return
            _onto_stats["changed"].append(pack_name)
            _fl_packs = in_flight(kernel).setdefault("packs", [])
            if pack_name not in _fl_packs:
                _fl_packs.append(pack_name)

            # ── growth narration ──────────────────────────────────────────
            # Announce the theme now being woven so the progressive base1→
            # base2→base3 load reads as the world tree *growing*, whatever the
            # host speed.  The PACK.json "theme"/"label" is the human line.
            try:
                import json as _pj
                _pmeta = _pj.load(open(os.path.join(pack_dir(pack_name), "PACK.json")))
                _theme = _pmeta.get("theme") or _pmeta.get("label") or pack_name
            except Exception:
                _theme = pack_name
            logger.info("[Kernel] 🌱 growing — %s  (%s, %d files)",
                        _theme, pack_name, len(ak_files))

            atoms_text  = f"[ont:ak] Pack '{pack_name}' atoms written"
            atoms_key   = _hl.sha256(atoms_text.encode()).hexdigest()
            atoms_alias = f"ont:ak:atoms:loaded:{pack_name}:{pmhash}"
            done_text   = f"[ont:ak] Pack '{pack_name}' fully loaded"
            done_key    = _hl.sha256(done_text.encode()).hexdigest()
            done_alias  = f"ont:ak:loaded:{pack_name}:{pmhash}"

            pack_max_wait = max(PACK_WAIT_FLOOR_S, len(ak_files) * PACK_WAIT_PER_FILE_S)
            # P2 (VPS 10-11) — a cap is how long the LOADER waits, never a reason to drop the pack.
            # Past it the pack's atom jobs keep running in the background; its sentinel job is
            # queued behind them (a link-class job runs after every queued atom job), its weave is
            # queued like any other pack's, and its sentinel FILE is written once the atoms land
            # (`_settle_deferred`, after the relations phase). "skipping link phase" left the pack
            # unwoven and unsentinelled, so every boot loaded it again.
            _deferred = False
            atoms_done = admin_session.local_cortex.get_aliases_by_pattern(atoms_alias)
            all_link_steps: List[dict] = []
            all_atom_defs: List[dict] = []   # [{alias, text}] for weave phase

            if atoms_done:
                # Atoms already written. Links/aliases/sets are handled by the single
                # global relations phase after ALL packs (not per-pack) — so here we
                # only re-collect atom defs for the (idempotent) weave phase.
                logger.info("[Kernel] Pack '%s': atoms sentinel found — collecting defs for weave…", pack_name)
                for fpath in ak_files:
                    try:
                        with open(fpath, "r", encoding="utf-8") as _f:
                            for raw in _f:
                                s = _parse_ak_line(raw)
                                if s is None:
                                    continue
                                if s["method"] == "kernel.memory.define":
                                    _p = s["params"]
                                    _desc = _p.get("description", "")
                                    # Raw Source Data rows (source:item:*) are NLP-exempt — never
                                    # queue their verbatim JSON for weave. Extracted txt:* atoms
                                    # are NOT exempt and weave normally.
                                    if (_desc and not _desc.startswith("Conceptual hub:")
                                            and not _p.get("name", "").startswith("source:item:")):
                                        all_atom_defs.append({
                                            "alias": _p.get("name", ""),
                                            "text": _desc,
                                        })
                    except Exception as exc:
                        logger.warning("[Kernel] Pack '%s' defs (recovery) %s: %s",
                                       pack_name, os.path.basename(fpath), exc)
            else:
                logger.info("[Kernel] Pack '%s': scanning %d files (phase 1)…",
                            pack_name, len(ak_files))
                files_to_queue: List[tuple] = []
                _p1_jobs: List[Any] = []
                for fpath in ak_files:
                    basename = os.path.basename(fpath)
                    try:
                        atom_steps: List[dict] = []
                        with open(fpath, "r", encoding="utf-8") as _f:
                            for raw in _f:
                                s = _parse_ak_line(raw)
                                if s is None:
                                    continue
                                if s["method"] in ("kernel.memory.link", "alias", "set.add"):
                                    # Deferred: ln / al / set.add all resolve a target to a
                                    # nucleus key, so they MUST run after EVERY pack's atoms
                                    # exist. Run per-pack (before a cross-pack target is
                                    # defined) they bind to the bare proto-word instead of the
                                    # real body atom (e.g. base1 linking base2's ingred:fruit:apple
                                    # attaches to the proto-word "apple"). Collected and run once,
                                    # in order alias→link→set, in the global relations phase below.
                                    continue
                                else:
                                    if s["method"] == "kernel.memory.define":
                                        _p = s["params"]
                                        _desc = _p.get("description", "")
                                        if _desc and not _desc.startswith("Conceptual hub:"):
                                            all_atom_defs.append({
                                                "alias": _p.get("name", ""),
                                                "text": _desc,
                                            })
                                    atom_steps.append(s)
                    except Exception as exc:
                        logger.warning("[Kernel] Pack '%s' atoms %s: %s",
                                       pack_name, basename, exc)
                        continue

                    if not atom_steps:
                        continue

                    # Per-file restart-skip sentinel, keyed by the file's CONTENT KEY (1.1) only.
                    f_alias = f"ont:ak:f:{pack_name}:{basename}:{_ck(fpath)}"
                    if admin_session.local_cortex.get_aliases_by_pattern(f_alias):
                        # D16 — a file's sentinel says its defines RAN, not that their names still
                        # point at its text. A cell the reconcile damaged (a redefined name deleted
                        # from under its new text, the new atom retired) keeps the sentinel, so the
                        # file was skipped for ever and the name stayed unbound. For a pack that is
                        # loading anyway, check this file's defs: every name must resolve to the
                        # key its line defines, and that atom must be live. If not, re-run the file
                        # and let the relations phase re-apply its `set.add`/`al`/`ln`.
                        _unbound = _file_unbound_defs(fpath)
                        if not _unbound:
                            logger.debug("[Kernel] Pack '%s' '%s': file sentinel present — skip",
                                         pack_name, basename)
                            continue
                        logger.warning("[Kernel] Pack '%s' '%s': file sentinel present but %d def(s) "
                                       "not bound to this file's text (e.g. %s) — reloading the file",
                                       pack_name, basename, len(_unbound), ", ".join(_unbound[:3]))
                        _clear_file_relation_sentinels(pack_name, basename)

                    # Append per-file sentinel at end of this file's atom job.
                    f_text = f"[ont:ak] Pack '{pack_name}' file '{basename}' atoms loaded"
                    f_key  = _hl.sha256(f_text.encode()).hexdigest()
                    atom_steps.append({"method": "write",
                                       "params": {"text": f_text, "scope": "universal"}})
                    atom_steps.append({"method": "alias",
                                       "params": {"id": f_key, "name": f_alias}})

                    files_to_queue.append((fpath, atom_steps, basename))

                if files_to_queue:
                    # Pack-level atoms sentinel goes on the LAST file still being queued.
                    _lf, _ls, _lb = files_to_queue[-1]
                    _ls.append({"method": "write",
                                "params": {"text": atoms_text, "scope": "universal"}})
                    _ls.append({"method": "alias",
                                "params": {"id": atoms_key, "name": atoms_alias}})
                    logger.info("[Kernel] Pack '%s': queuing %d/%d atom jobs (phase 1)…",
                                pack_name, len(files_to_queue), len(ak_files))
                    for _fp, _steps, _bn in files_to_queue:
                        _p1_jobs.append(_submit_file_job(_fp, _steps, f"ont.ak.{pack_name}:{_bn}"))
                    _onto_stats["atom_jobs"] += len(files_to_queue)
                else:
                    # All per-file sentinels present but pack sentinel absent.
                    # Write it now as a lightweight standalone job.
                    logger.info("[Kernel] Pack '%s': all file sentinels present — writing pack sentinel",
                                pack_name)
                    _p1_jobs.append(kernel.harmonia.submit_job(JCLJob(
                        owner="admin",
                        label=f"ont.ak.atoms_sentinel:{pack_name}",
                        steps=[
                            JCLStep(method="write",
                                    params={"text": atoms_text, "scope": "universal"}),
                            JCLStep(method="alias",
                                    params={"id": atoms_key, "name": atoms_alias}),
                        ],
                        fail_fast=False,
                    ), job_class=CLASS_BATCH_ATOM))

                # 1.5 — measured against THIS PACK'S OWN atom jobs. A fixed 5 s poll on a sentinel
                # alias cost every pack five seconds, and the pack's jobs could sit behind another
                # pack's weave in the same queue; the weave is now submitted after the gate, and the
                # wait looks at the jobs it queued.
                logger.info("[Kernel] Pack '%s': waiting for its %d phase-1 job(s) (max %ds)…",
                            pack_name, len(_p1_jobs), pack_max_wait)
                _p1_start = _time.time()
                while _time.time() - _p1_start < pack_max_wait:
                    _time.sleep(_poll_after(_time.time() - _p1_start))
                    if lifecycle.is_shutting_down(): return
                    _own_done = all(getattr(_j, "status", "DONE") in ("DONE", "FAILED", "CANCELLED")
                                    for _j in _p1_jobs if _j is not None)
                    if _own_done and admin_session.local_cortex.get_aliases_by_pattern(atoms_alias):
                        logger.info("[Kernel] Pack '%s': phase-1 done in %.1fs",
                                    pack_name, _time.time() - _p1_start)
                        break
                else:
                    _deferred = True
                    logger.warning("[Kernel] Pack '%s': phase-1 still running after %.1fs (cap %ds) — "
                                   "its atom jobs continue in the background; sentinel and weave are "
                                   "queued behind them", pack_name, _time.time() - _p1_start,
                                   pack_max_wait)

            _p2_job = None
            if all_link_steps:
                logger.info("[Kernel] Pack '%s': submitting %d link steps (phase 2)…",
                            pack_name, len(all_link_steps))
                all_link_steps.append({"method": "write",
                                       "params": {"text": done_text, "scope": "universal"}})
                all_link_steps.append({"method": "alias",
                                       "params": {"id": done_key, "name": done_alias}})
                _p2_job = kernel.harmonia.submit_job(JCLJob(
                    owner="admin",
                    label=f"ont.ak.links:{pack_name}",
                    steps=[JCLStep(method=s["method"], params=s.get("params", {}))
                           for s in all_link_steps],
                    fail_fast=False,
                ))
            else:
                _p2_job = kernel.harmonia.submit_job(JCLJob(
                    owner="admin", label=f"ont.ak.sentinel:{pack_name}", steps=[
                        JCLStep(method="write",
                                params={"text": done_text, "scope": "universal"}),
                        JCLStep(method="alias",
                                params={"id": done_key, "name": done_alias}),
                    ], fail_fast=False))

            # Wait for phase-2 DB sentinel (written by link/sentinel job above),
            # then write the filesystem sentinel so restart-skip is durable.
            if _deferred:
                _deferred_sentinels.append((pack_name, pmhash, done_alias))
            else:
                logger.info("[Kernel] Pack '%s': waiting for phase-2 completion (max %ds)…",
                            pack_name, pack_max_wait)
                _p2_start = _time.time()
                while _time.time() - _p2_start < pack_max_wait:
                    _time.sleep(_poll_after(_time.time() - _p2_start))
                    if lifecycle.is_shutting_down(): return
                    if admin_session.local_cortex.get_aliases_by_pattern(done_alias):
                        _write_sent(pack_name, pmhash)
                        logger.info("[Kernel] Pack '%s': phase-2 done in %.1fs",
                                    pack_name, _time.time() - _p2_start)
                        break
                else:
                    _deferred = True
                    _deferred_sentinels.append((pack_name, pmhash, done_alias))
                    logger.warning("[Kernel] Pack '%s': phase-2 still running after %.1fs — the "
                                   "sentinel file is written when it lands",
                                   pack_name, _time.time() - _p2_start)

            # Phase 3 — Weave: link each atom's description tokens to nucleus protowords.
            # Runs as a single LOW-priority JCL job after phases 1 and 2 are done.
            # Idempotent: duplicate put_link calls are silently ignored by the backend.
            # Resilience valve: the weave is OPTIONAL background enrichment ("while
            # sleeping") — the graph is fully usable without it (dive/explore/read work off
            # the atoms + relations already loaded). If a weave is ever the thing taking the
            # daemon down, the weave is the regex floor (it cannot crash the process) and runs at
            # the maintenance class.
            _p3_queued = False
            if all_atom_defs and kernel.jcl_worker and JCLJob and JCLStep:
                # Chunk the weave into many steps (not one monolithic step): the job then
                # reports visible progress (k/M) and the single JCL worker can YIELD to
                # higher-priority ready jobs at every chunk boundary. Weave is background
                # enrichment ("while sleeping"), so it runs at the IDLE (maintenance) class.
                _WEAVE_CHUNK = 400
                _weave_steps = [
                    JCLStep(method="sys.weaver.weave_batch",
                            params={"items": all_atom_defs[_wi:_wi + _WEAVE_CHUNK]})
                    for _wi in range(0, len(all_atom_defs), _WEAVE_CHUNK)
                ]
                # 1.5 — NOT submitted here. Queued now, it sat in front of the NEXT pack's atom
                # jobs (287 s of one pack's phase-1 wait on 09-26 was another pack's weave). It is
                # background enrichment; it goes in after `ontology.loaded` opens.
                _deferred_weaves.append((pack_name, JCLJob(
                    owner="admin",
                    label=f"sys.weaver.batch:{pack_name}",
                    steps=_weave_steps,
                    fail_fast=False,
                )))
                _p3_queued = True

            _total = _time.time() - _pack_start
            logger.info(
                "[Kernel] Pack '%s': load complete — total %.1fs | "
                "files=%d atoms=%d links=%d weave=%s%s",
                pack_name, _total, len(ak_files), len(all_atom_defs),
                len(all_link_steps),
                f"queued({len(all_atom_defs)} atoms)" if _p3_queued else "skipped",
                " deferred=background" if _deferred else "",
            )
            return _deferred

        def _relbase_of(pack, fpath):
            return (pack + "__" + os.path.basename(fpath)).replace(
                os.sep, "_").replace(".", "_").replace(":", "_")

        def _core_ready(core_dirs, rest_packs, late_core):
            """P1 — the first load's core is in: bind what it can bind now, then release the driver.

            The relations (al → ln → set) of every core file are applied now — except a file with
            a step that names something a pack still to load declares (a `def` or an `al` name):
            bound now, that step would land on a proto-word or on a definition about to be
            replaced, the reason relations wait for every pack. Such a file is left WHOLE to the
            global relations phase (no sentinel written for it here). Then the load stops being a
            first load for the driver: from here a workload waits only when a pack still to load
            declares a name it reads (`wl_state.onto_hold`) — or when it reads an alias or a Set
            that a held file binds, declared under the in-flight entry `relations:core`.
            Returns None on shutdown, else whether the driver was released."""
            _t0, _rss0 = _time.time(), _rss_mb()
            later: set = set()
            for _pn, _d in rest_packs:
                for _fp in _collect_from_dir(_d, ".ak"):
                    try:
                        with open(_fp, "r", encoding="utf-8", errors="replace") as _fh:
                            for _raw in _fh:
                                _tok = _raw.lstrip()[:7].lower()
                                if not (_tok.startswith("def") or _tok.startswith("al ")
                                        or _tok.startswith("alias")):
                                    continue
                                _st = _parse_ak_line(_raw)
                                if _st and _st["method"] in ("kernel.memory.define", "alias"):
                                    _nm = str(_st["params"].get("name") or "")
                                    if _nm:
                                        later.add(_nm)
                    except OSError:
                        continue
            al, ln, st, gates = [], [], [], []
            held_files, held_names = 0, set()
            for _d in core_dirs:
                _pn = os.path.basename(_d)
                for _fp in _collect_from_dir(_d, ".ak"):
                    _rb = _relbase_of(_pn, _fp)
                    _ck_f = _ck(_fp)
                    if not _ck_f or _sent_exists("_relfile_" + _rb, _ck_f):
                        continue
                    steps, names, safe = [], set(), True
                    try:
                        with open(_fp, "r", encoding="utf-8", errors="replace") as _fh:
                            for _raw in _fh:
                                _s = _parse_ak_line(_raw)
                                if not _s or _s["method"] not in ("alias", "kernel.memory.link",
                                                                  "set.add"):
                                    continue
                                _p = _s.get("params", {})
                                _refs = {_p.get("src"), _p.get("dst"), _p.get("id")}
                                if _s["method"] == "alias":
                                    _refs.add(_p.get("name"))
                                if _s["method"] != "kernel.memory.link" and _p.get("name"):
                                    names.add(str(_p["name"]))       # an alias, or a Set
                                if _refs & later:
                                    safe = False
                                steps.append(_s)
                    except OSError:
                        continue
                    if safe:
                        for _s in steps:
                            {"alias": al, "kernel.memory.link": ln,
                             "set.add": st}[_s["method"]].append(_s)
                        try:
                            _stv = os.stat(_fp)
                            _stag = "%x_%x" % (int(_stv.st_mtime), _stv.st_size)
                        except OSError:
                            _stag = ""
                        gates.append((_rb, _ck_f, _stag))
                    else:
                        held_files += 1
                        held_names |= names
            later = None

            def _gate():
                for _rb, _ck_f, _stag in gates:
                    _write_sent("_relfile_" + _rb, _ck_f)
                    if _stag:
                        with open(_sent_file("_relstat_" + _rb, _stag), "w") as _fh:
                            _fh.write(_ck_f); _fh.flush(); os.fsync(_fh.fileno())

            ok = True
            steps = al + ln + st
            if steps:
                _sig = "\n".join(f"{_s['method']}|{_s['params'].get('id','')}|"
                                 f"{_s['params'].get('name','')}|{_s['params'].get('src','')}|"
                                 f"{_s['params'].get('dst','')}|{_s['params'].get('rel','')}"
                                 for _s in steps)
                _h = _hl.sha256(_sig.encode()).hexdigest()[:16]
                _text = "[ont:ak] Core relations (al/ln/set) applied"
                _alias = f"ont:ak:relations:core:{_h}"
                if admin_session.local_cortex.get_aliases_by_pattern(_alias):
                    _gate()
                else:
                    _js = [JCLStep(method=_s["method"], params=_s.get("params", {})) for _s in steps]
                    _js.append(JCLStep(method="write", params={"text": _text, "scope": "universal"}))
                    _js.append(JCLStep(method="alias", params={
                        "id": _hl.sha256((_text + _h).encode()).hexdigest(), "name": _alias}))
                    _job = kernel.harmonia.submit_job(JCLJob(
                        owner="admin", label="ont.ak.relations:core", steps=_js, fail_fast=False))
                    ok = _wait_boot_job(_job, _alias, _gate, max(3600, len(steps)))
                    if ok is None:
                        return None
            elif gates:
                _gate()
            rest = [p for p, _ in rest_packs] + list(late_core)
            if not ok:
                logger.warning("[onto] core relations did not complete — the driver stays held "
                               "until the whole load is in")
                return False
            publish_in_flight(kernel, first=False,
                              packs=rest + (["relations:core"] if held_names else []))
            if held_names:
                in_flight(kernel)["declares"]["relations:core"] = held_names
            logger.info("[onto] core ready packs=%d al=%d ln=%d set=%d held_files=%d — workloads "
                        "resume; %d pack(s) still to load hold only the workloads that read their "
                        "names %s", len(core_dirs), len(al), len(ln), len(st), held_files, len(rest),
                        _phase_tail(_t0, _rss0))
            return True

        # ── Load packs: the AUTOLOAD TIER first, then the rest, each in REGISTRY.json order ──
        # autoload:true  → always load (base)
        # load_all:true  → load EVERY registered pack (thesaurus/service tiers)
        # autoload:false → otherwise, load only if the pack name is in
        #                  config/ontology/packs.json["enabled"] (seeds opt-in)
        # P1 (VPS 10-11) — the autoload tier (autoload:true, and on a tier without load_all every
        # pack the cell enabled) is the cell's core: it loads first, and on a FIRST load the
        # workload driver is released as soon as it is in (`_core_ready`), so the deep packs a
        # load_all tier carries can take hours without holding every workload. Moving the late
        # autoload packs ahead changes which `def` wins a name only where an autoload pack and an
        # earlier non-autoload pack define the same name differently; none does.
        _enabled  = _read_enabled_packs()
        _load_all = _read_load_all()
        if _load_all:
            logger.info("[Kernel] load_all is set — auto-loading every registered pack sequentially")
        _core_packs: List[tuple] = []
        _rest_packs: List[tuple] = []
        for _pkg in _read_registry():
            _pname     = _pkg.get("name", "")
            _autoload  = _pkg.get("autoload", False)
            if not _pname or _pname in RESERVED_DIRS:
                continue
            if not _autoload and not _load_all and _pname not in _enabled:
                continue
            _pack_dir = pack_dir(_pname)
            if not os.path.isdir(_pack_dir):
                logger.warning("[Kernel] Pack '%s': directory not found — skipping", _pname)
                continue
            # an operator's own pack (`ontology/user/`) loads after every registered pack (§5.6)
            _core = (_autoload or not _load_all) and not _pkg.get("user")
            (_core_packs if _core else _rest_packs).append((_pname, _pack_dir))

        # Packs enabled in config but absent from REGISTRY (user-added externals)
        _registry_names = {p.get("name") for p in _read_registry()}
        for _pname in sorted(_enabled - _registry_names):
            if _pname in RESERVED_DIRS:
                continue
            _pack_dir = pack_dir(_pname)
            if os.path.isdir(_pack_dir):
                logger.info("[Kernel] Pack '%s': enabled but not in REGISTRY — loading", _pname)
                _rest_packs.append((_pname, _pack_dir))
            else:
                logger.warning("[Kernel] Enabled pack '%s': not found in ontology/", _pname)

        _late_core: List[str] = []                # core packs whose atoms are still landing (P2)
        for _pname, _pack_dir in _core_packs:
            if _load_ak_pack(_pname, _collect_from_dir(_pack_dir, ".ak")):
                _late_core.append(_pname)
        if _rest_packs and in_flight(kernel).get("first"):
            if _core_ready([d for _, d in _core_packs], _rest_packs, _late_core) is None:
                return
        for _pname, _pack_dir in _rest_packs:
            _load_ak_pack(_pname, _collect_from_dir(_pack_dir, ".ak"))

        # ── Global relations phase — run ALL al / ln / set.add AFTER every pack's
        # atoms exist. Every one of these resolves a target to a nucleus key, so run
        # per-pack (before a cross-pack target is defined) it binds to the bare
        # proto-word instead of the real body atom — e.g. base1's
        #   al ingred:fruit:apple apple   /   ln ingred:fruit:apple score:0.25 rec:acidity
        # attaches to the proto-word "apple" because base2 defines ingred:fruit:apple.
        # v1.0 ran links as one all-packs job; v1.1's per-pack split reintroduced the
        # ordering bug. Fix: collect al/ln/set across the active packs and run them as
        # ONE deferred job in order alias→link→set (so links/sets can resolve by alias),
        # gated by a content-hash sentinel. All three are idempotent, so a re-run after a
        # new pack is enabled is safe.
        try:
            _active_dirs: List[str] = []
            for _pkg in _read_registry():
                _pn = _pkg.get("name", "")
                if not _pn or _pn in RESERVED_DIRS:
                    continue
                if not _pkg.get("autoload", False) and not _load_all and _pn not in _enabled:
                    continue
                _d = pack_dir(_pn)
                if os.path.isdir(_d) and _pn not in _onto_stats["refused"]:
                    _active_dirs.append(_d)
            _reg_names = {p.get("name") for p in _read_registry()}
            for _pn in sorted(_enabled - _reg_names):
                if _pn in RESERVED_DIRS:
                    continue
                _d = pack_dir(_pn)
                if os.path.isdir(_d) and _pn not in _onto_stats["refused"]:
                    _active_dirs.append(_d)

            # FILE-LEVEL incremental (was: re-read EVERY file and re-apply EVERY al/ln/set
            # whenever one GLOBAL relations hash changed — so adding one small .ak file to a
            # big pack re-applied the entire ontology's relations). Now each .ak file carries
            # its own CONTENT-HASH sentinel: a file whose content is unchanged is skipped
            # entirely (not read, its relations not re-applied), and only NEW/CHANGED files'
            # relations are collected + applied. Adding one file touches only that file.
            # Correctness holds: targets in unchanged files were aliased on a prior boot (their
            # aliases already resolve), and within this batch the ordered al→ln→set guarantees
            # a changed file's links/sets resolve names defined in the same batch.
            _al_steps: List[dict] = []
            _ln_steps: List[dict] = []
            _set_steps: List[dict] = []
            _relfile_sentinels: List[tuple] = []      # (sentinel_name, filehash) to write on success
            _stat_after: List[tuple] = []             # (stat sentinel, tag, content key), same moment

            # F48-1.1 — a STAT (mtime+size) sentinel is the cheap change-detector: an unchanged
            # file is skipped WITHOUT opening/decoding/parsing it. Previously EVERY .ak file was
            # read + decoded + parsed EVERY boot, so `load_all` re-walked the whole ontology into
            # the loader heap each boot — a +2.5–3 GB per-boot climb Python never returned to the
            # OS, even though the STORE did not grow. Peak loader heap is O(changed files).
            _rel_t0, _rel_rss0 = _time.time(), _rss_mb()
            _rel_read = _rel_skipped = _rel_reparsed = 0
            _rel_changed_packs: set = set()

            def _read_sent(name, tag) -> str:
                try:
                    with open(_sent_file(name, tag), "r") as _fh:
                        return _fh.read().strip()
                except OSError:
                    return ""

            def _write_sent_value(name, tag, value) -> None:
                with open(_sent_file(name, tag), "w") as _fh:
                    _fh.write(value)
                    _fh.flush()
                    os.fsync(_fh.fileno())

            # 1.1 — ONE key per file: its CONTENT KEY (comments and blank lines out). `_relfile_<f>_
            # <ck>` says "these relations are applied". The STAT sentinel is only a fast path to
            # that key: it records the content key it saw, and is trusted only when that key's
            # `_relfile_` sentinel exists — so an mtime is never itself a key, and a fresh
            # extraction (every mtime new) costs one READ per file and no parse.
            for _d in _active_dirs:
                _pn_r = os.path.basename(_d)
                for _fp in _collect_from_dir(_d, ".ak"):
                    _bn_r = os.path.basename(_fp)
                    _relbase = (_pn_r + "__" + _bn_r).replace(
                        os.sep, "_").replace(".", "_").replace(":", "_")
                    _statname = "_relstat_" + _relbase
                    _sname_r = "_relfile_" + _relbase
                    try:
                        _st = os.stat(_fp)
                        _stat_tag = "%x_%x" % (int(_st.st_mtime), _st.st_size)
                    except OSError:
                        _stat_tag = ""
                    if _stat_tag:
                        _seen_ck = _read_sent(_statname, _stat_tag)
                        if _seen_ck and _sent_exists(_sname_r, _seen_ck):
                            _rel_skipped += 1          # not opened at all
                            continue
                    _fh_r = _ck(_fp)                   # one streamed read, no parse
                    _rel_read += 1
                    if not _fh_r:
                        continue
                    _applied = _sent_exists(_sname_r, _fh_r)
                    if _applied:
                        if _stat_tag:
                            _write_sent_value(_statname, _stat_tag, _fh_r)
                        continue
                    try:
                        _content_r = open(_fp, "rb").read()
                    except OSError as _exc:
                        logger.warning("[Kernel] Global relations read %s: %s", _fp, _exc)
                        continue
                    _rel_reparsed += 1
                    try:
                        for _raw in _content_r.decode("utf-8", "replace").splitlines():
                            _s = _parse_ak_line(_raw)
                            if not _s:
                                continue
                            if _s["method"] == "alias":
                                _al_steps.append(_s)
                            elif _s["method"] == "kernel.memory.link":
                                _ln_steps.append(_s)
                            elif _s["method"] == "set.add":
                                _set_steps.append(_s)
                    except Exception as _exc:
                        logger.warning("[Kernel] Global relations scan %s: %s", _fp, _exc)
                        _content_r = None
                        continue                       # do NOT sentinel a file we failed to parse
                    _content_r = None                  # release the file body before the next file
                    _rel_changed_packs.add(_pn_r)
                    _relfile_sentinels.append((_sname_r, _fh_r))
                    if _stat_tag:
                        _stat_after.append((_statname, _stat_tag, _fh_r))
            _rel_skipped_total = _rel_skipped

            # Ordered: aliases first (so ln/set can resolve short names), then links,
            # then set memberships. Single FIFO job guarantees the order.
            _rel_steps = _al_steps + _ln_steps + _set_steps
            if not _rel_steps and not _relfile_sentinels:
                logger.info("[Kernel] Global relations: no changed .ak files — skipping")
            if _rel_steps:
                _sig = "\n".join(
                    f"{_s['method']}|{_s['params'].get('id','')}|"
                    f"{_s['params'].get('name','')}|{_s['params'].get('src','')}|"
                    f"{_s['params'].get('dst','')}|{_s['params'].get('rel','')}"
                    for _s in _rel_steps)
                _rhash = _hl.sha256(_sig.encode()).hexdigest()[:16]
                if True:
                    _rel_text  = "[ont:ak] Global relations (al/ln/set) applied"
                    _rel_key   = _hl.sha256((_rel_text + _rhash).encode()).hexdigest()
                    _rel_alias = f"ont:ak:relations:all:{_rhash}"

                    def _gate_rel_files():
                        for _sn, _fh in _relfile_sentinels:
                            _write_sent(_sn, _fh)
                        for _sn, _tag, _fh in _stat_after:
                            _write_sent_value(_sn, _tag, _fh)

                    # F20 self-heal: a PRIOR boot may have submitted this exact content-hash job,
                    # had its wait abandoned (timeout), yet the job COMPLETED afterwards — the
                    # completion alias then already exists this boot. Gate the files and skip the
                    # replay instead of re-running the whole (possibly 40k-step) phase.
                    if admin_session.local_cortex.get_aliases_by_pattern(_rel_alias):
                        _gate_rel_files()
                        logger.info("[Kernel] Global relations already applied (%s) — gated, "
                                    "skipped replay", _rel_alias)
                    else:
                        logger.info("[Kernel] Global relations phase: %d aliases + %d links + "
                                    "%d set.add across %d CHANGED file(s)…",
                                    len(_al_steps), len(_ln_steps), len(_set_steps),
                                    len(_relfile_sentinels))
                        _job_steps = [JCLStep(method=_s["method"], params=_s.get("params", {}))
                                      for _s in _rel_steps]
                        _job_steps.append(JCLStep(method="write",
                                                  params={"text": _rel_text, "scope": "universal"}))
                        _job_steps.append(JCLStep(method="alias",
                                                  params={"id": _rel_key, "name": _rel_alias}))
                        _rel_job = kernel.harmonia.submit_job(JCLJob(
                            owner="admin", label="ont.ak.relations:all",
                            steps=_job_steps, fail_fast=False,
                        ))
                        # F20 progress-gating: wait on the job's liveness, not a wall-clock ceiling
                        # (a large changed set legitimately runs past the old 3600 s). The old
                        # ceiling becomes the stall-window floor.
                        if _wait_boot_job(_rel_job, _rel_alias, _gate_rel_files,
                                          max(3600, len(_rel_steps))) is None:
                            return
            elif _relfile_sentinels:
                # Changed files that carried NO al/ln/set (def-only) — nothing to apply, but
                # they must still be gated so they are not re-scanned every boot.
                for _sn, _fh in _relfile_sentinels:
                    _write_sent(_sn, _fh)
                for _sn, _tag, _fh in _stat_after:
                    _write_sent_value(_sn, _tag, _fh)
                logger.info("[Kernel] Global relations: %d changed def-only file(s) gated",
                            len(_relfile_sentinels))
        except Exception as _exc:
            logger.warning("[Kernel] Global relations phase error: %s", _exc)

        # ── 1.6 the load phases, in one line each ─────────────────────────────────────────────
        _rp = locals()
        logger.info("[onto] atoms packs=%d unchanged=%d refused=%d changed=%d jobs=%d %s",
                    len(_onto_stats["pack_hash"]), _onto_stats["unchanged"],
                    len(_onto_stats["refused"]),
                    len(_onto_stats["changed"]), _onto_stats["atom_jobs"],
                    _phase_tail(_onto_t0, _onto_rss0))
        if "_rel_t0" in _rp:
            logger.info("[onto] relations files_read=%d reparsed=%d skipped=%d al=%d ln=%d set=%d %s",
                        _rp.get("_rel_read", 0), _rp.get("_rel_reparsed", 0),
                        _rp.get("_rel_skipped_total", 0), len(_rp.get("_al_steps", [])),
                        len(_rp.get("_ln_steps", [])), len(_rp.get("_set_steps", [])),
                        _phase_tail(_rp["_rel_t0"], _rp["_rel_rss0"]))

        # P2 — the packs whose atoms were still landing when the loader's wait ran out. Their sentinel
        # jobs were queued behind their atom jobs, and the relations job above behind both, so by
        # now they have normally landed: write the sentinel FILES so the next boot skips them. One
        # still out (a stalled job) keeps its per-file sentinels; the next boot loads only what is left.
        for _dpn, _dph, _dal in _deferred_sentinels:
            if admin_session.local_cortex.get_aliases_by_pattern(_dal):
                _write_sent(_dpn, _dph)
                logger.info("[Kernel] Pack '%s': background atoms landed — load complete", _dpn)
            else:
                logger.warning("[Kernel] Pack '%s': atoms still landing at the gate — the next boot "
                               "loads only the files not yet in", _dpn)

        # ── 1.3 the FIRST gate: atoms + global relations ──────────────────────────────────────
        # Everything a consumer of the ontology needs to RESOLVE a name is in place now. Canon and
        # reconcile derive and prune; they are the second gate's work, not a reason to keep
        # provisioning, the corpus bootstraps and every `after: ontology.loaded` body waiting.
        from lib.akasha.api import schedule as _sched_g
        _sched_g.open_gate(kernel, "ontology.loaded")
        publish_in_flight(kernel, clear=True)

        # 1.5 — the weaves, now that no pack's gate can queue behind them.
        for _wpn, _wjob in _deferred_weaves:
            try:
                kernel.harmonia.submit_job(_wjob, job_class=CLASS_MAINTENANCE)
            except Exception as _we:
                logger.warning("[Kernel] weave for pack '%s' not queued: %s", _wpn, _we)
        if _deferred_weaves:
            logger.info("[onto] weave queued packs=%d (after the gate)", len(_deferred_weaves))

        # ── Ontology reconciliation phase — retire atoms a pack no longer contributes
        # (the data-side analog of the seed CODE prune). Additive re-import handles adds +
        # edits; this adds the missing REMOVAL half so a retired concept doesn't linger
        # forever in an operation-mode server without a data wipe. Fenced so it can NEVER
        # touch user knowledge: provenance="ontology" + no user access scope + no still-owning
        # pack (ref-counted). Soft-evict only (recoverable); hard drop is superuser-only via
        # onto.reconcile compact=yes. Sentinel-gated (runs once per ontology content change)
        # and idempotent. ON exactly for a `load_all` tier (the tier's declared fact; no
        # environment override — the purge order §4.5).
        # Spec: docs/for-llm/ontology-reconciliation-spec.md.
        try:
            if _load_all:
                from lib.akasha.ontology_reconcile import OntologyReconciler as _Recon
                _R = _Recon(admin_session.nucleus)
                _recon_packs: List[str] = []
                for _pkg in _read_registry():
                    _pn = _pkg.get("name", "")
                    if not _pn or _pn in RESERVED_DIRS:
                        continue
                    if not _pkg.get("autoload", False) and not _load_all and _pn not in _enabled:
                        continue
                    if os.path.isdir(pack_dir(_pn)) and _pn not in _onto_stats["refused"]:
                        _recon_packs.append(_pn)       # a refused pack loaded nothing to reconcile
                # PER-PACK gating (was ONE GLOBAL sentinel over every pack's manifest). The
                # global sentinel meant ANY single pack change invalidated it and re-ran the
                # reconcile for ALL packs — re-materialising each pack's def-keys AND re-stamping
                # them on top of the fully-resident graph. On an incremental add (one small file
                # dropped into a big pack) that peak OOM-killed the Cell daemon mid-reload. Now
                # each pack is gated by its OWN manifest sentinel, exactly like the load phase:
                # only a pack whose .ak content actually changed is reconciled, so an incremental
                # add touches ONE pack, never all 25. The reconcile itself retires only
                # (old_ledger − new_keys), so an additive-only change (nothing dropped) retires
                # nothing and stays bounded to that single pack.
                _total_retired = 0
                _reconciled_n = 0
                _recon_t0, _recon_rss0 = _time.time(), _rss_mb()
                for _pn in _recon_packs:
                    try:
                        _pfiles = _collect_from_dir(pack_dir(_pn), ".ak")
                        _pmh = _manifest_hash(_pfiles)
                        if _sent_exists("_reconcile_" + _pn, _pmh):
                            continue                        # unchanged since last reconcile → skip
                        _p_t0, _p_rss0 = _time.time(), _rss_mb()
                        # 1.4 — a SET of keys, streamed from the files; no list of names beside it.
                        _keys = pack_def_key_set(kernel, admin_session, _pn)
                        _names = bool(_keys)
                        if not _names:
                            # empty / failed parse — do NOT write a sentinel (retry next boot),
                            # and never let an empty new_keys wipe the ledger via reconcile.
                            continue
                        _batch: List[str] = []
                        for _k in _keys:                   # stamped in bounded batches, not one copy
                            _batch.append(_k)
                            if len(_batch) >= 2000:
                                _R.stamp_provenance(_pn, _batch)
                                _batch = []
                        if _batch:
                            _R.stamp_provenance(_pn, _batch)
                        _rep = _R.reconcile(_pn, _keys, dry_run=False)
                        _total_retired += len(_rep["retired"])
                        logger.info("[Kernel] Reconcile '%s': keys=%d retired=%d %s%s", _pn,
                                    len(_keys), len(_rep["retired"]),
                                    _phase_tail(_p_t0, _p_rss0),
                                    (" first=%s" % _rep["retired"][:10]) if _rep["retired"] else "")
                        _keys = None
                        _write_sent("_reconcile_" + _pn, _pmh)   # gate THIS pack at THIS manifest
                        _reconciled_n += 1
                    except Exception as _pe:
                        # DEGRADE, never crash the daemon: a pack that fails to reconcile is left
                        # as-is (no sentinel → retried next boot); the process stays alive so the
                        # rest of the ontology still serves. (Same posture as the dive OOM fix.)
                        logger.warning("[Kernel] Reconcile '%s' degraded (skipped): %s", _pn, _pe)
                logger.info("[onto] reconcile packs=%d retired=%d %s", _reconciled_n,
                            _total_retired, _phase_tail(_recon_t0, _recon_rss0))
        except Exception as _exc:
            logger.warning("[Kernel] Ontology reconcile phase error: %s", _exc)

        # ── ontology corrections (ship a fix as ontology/corrections/*.ak) ──
        # Correct a mis-authored release atom by dropping a normal `def` line into
        # ontology/corrections/*.ak. Because ak defs are dispatched scope=universal, a
        # CHANGED definition force-rebinds its alias to the corrected atom and soft-retires
        # the stale one (see _handle_define) — UPDATING an already-loaded nucleus with no
        # data wipe, no `rm`, no Linux. Runs after ALL packs (so any target already exists),
        # gated by a CONTENT hash of the corrections so it applies once per change on every
        # install that has not yet applied it, and is idempotent (an already-correct def is a
        # content-addressed no-op). This is the safe, seed-shippable way to push a fix.
        try:
            _corr_files = [f for _r in _roots
                           for f in _collect_from_dir(os.path.join(_r, "corrections"), ".ak")]
            if _corr_files:
                _corr_ch = _hl.sha256(
                    b"".join(open(_f, "rb").read() for _f in _corr_files)).hexdigest()[:16]
                if not _sent_exists("_corrections", _corr_ch):
                    _corr_steps = []
                    for _cf in _corr_files:
                        try:
                            for _raw in open(_cf, "rb").read().decode("utf-8", "replace").splitlines():
                                _cs = _parse_ak_line(_raw)
                                if _cs:
                                    _corr_steps.append(JCLStep(method=_cs["method"], params=_cs.get("params", {})))
                        except Exception as _ce:
                            logger.warning("[Kernel] correction file %s degraded: %s", _cf, _ce)
                    if _corr_steps:
                        _corr_text  = "[ont:ak] Ontology corrections applied"
                        _corr_key   = _hl.sha256((_corr_text + _corr_ch).encode()).hexdigest()
                        _corr_alias = f"ont:ak:corrections:{_corr_ch}"
                        _corr_steps.append(JCLStep(method="write", params={"text": _corr_text, "scope": "universal"}))
                        _corr_steps.append(JCLStep(method="alias", params={"id": _corr_key, "name": _corr_alias}))
                        logger.info("[Kernel] Ontology corrections phase: applying %d op(s)…", len(_corr_steps) - 2)
                        kernel.harmonia.submit_job(JCLJob(
                            owner="admin", label="ont.ak.corrections", steps=_corr_steps, fail_fast=False))
                        _c_start = _time.time()
                        while _time.time() - _c_start < 600:
                            _time.sleep(3)
                            if lifecycle.is_shutting_down():
                                return
                            if admin_session.local_cortex.get_aliases_by_pattern(_corr_alias):
                                _write_sent("_corrections", _corr_ch)
                                logger.info("[Kernel] Ontology corrections applied.")
                                break
        except Exception as _exc:
            logger.warning("[Kernel] Corrections phase error: %s", _exc)

        # ── .csl files (concept graph) ─────────────────────────────────────
        _csl_files_probe = _collect(".csl")
        _csl_mhash = _manifest_hash(_csl_files_probe) if _csl_files_probe else "empty"

        _SENT_TEXT  = "[ont:csl] Ontology CSL scripts loaded"
        _SENT_KEY   = _hl.sha256(_SENT_TEXT.encode()).hexdigest()
        _SENT_ALIAS = f"ont:csl:loaded:{_csl_mhash}"

        csl_loaded = admin_session.local_cortex.get_aliases_by_pattern(_SENT_ALIAS)
        if not csl_loaded:
            csl_files = _csl_files_probe
            if csl_files:
                logger.info("[Kernel] Queuing %d .csl ontology files as JCL boot jobs…", len(csl_files))
                for idx, fpath in enumerate(csl_files):
                    try:
                        with open(fpath, "r", encoding="utf-8") as _f:
                            source = _f.read()
                        steps_raw = [{"method": "csl.run", "params": {"script": source}}]
                        if idx == len(csl_files) - 1:
                            steps_raw.append({
                                "method": "write",
                                "params": {"text": _SENT_TEXT, "scope": "universal"},
                            })
                            steps_raw.append({
                                "method": "alias",
                                "params": {"id": _SENT_KEY, "name": _SENT_ALIAS},
                            })
                        _submit_file_job(fpath, steps_raw,
                                         f"ont.csl.boot:{os.path.basename(fpath)}")
                    except Exception as exc:
                        logger.warning("[Kernel] boot-load .csl: could not queue %s: %s",
                                       os.path.basename(fpath), exc)
                logger.info("[Kernel] .csl boot load queued (%d files)", len(csl_files))
            else:
                # No ontology .csl (e.g. a minimal seeds series without the thesaurus
                # pack). The ont:csl sentinel is normally written by the last .csl job;
                # with zero .csl jobs it would never fire, so the curations phase below
                # would wait out its full timeout and skip. Queue a sentinel-only job —
                # it runs AFTER the already-queued .ak atom jobs (same class, FIFO), so
                # it still marks "atoms are loaded" and the curations phase proceeds.
                _submit_file_job("(no ontology csl)", [
                    {"method": "write", "params": {"text": _SENT_TEXT, "scope": "universal"}},
                    {"method": "alias", "params": {"id": _SENT_KEY, "name": _SENT_ALIAS}},
                ], "ont.csl.boot:sentinel-only")
                logger.info("[Kernel] no ontology .csl — ont:csl sentinel queued directly")

        # ── curations/ (thesaurus enrichments) ────────────────────────────
        # Loaded automatically AFTER ontology .csl sentinel is set.
        # curations/ lives at project root alongside ontology/ — these are
        # example enrichments that ship with the system so a fresh install
        # already has curated content to explore.
        _CUR_SENT_TEXT  = "[ont:curation] Curation scripts loaded"
        _CUR_SENT_KEY   = _hl.sha256(_CUR_SENT_TEXT.encode()).hexdigest()

        from lib.akasha.api import reserved as _reserved
        cur_dir = _reserved.root("curations")
        _cur_files_probe: List[str] = []
        if os.path.exists(cur_dir):
            for _rd, _, _ns in os.walk(cur_dir):
                for _n in sorted(_ns):
                    if _n.endswith(".csl"):
                        _cur_files_probe.append(os.path.join(_rd, _n))
        _cur_mhash = _manifest_hash(_cur_files_probe) if _cur_files_probe else "empty"
        _CUR_SENT_ALIAS = f"ont:curation:loaded:{_cur_mhash}"

        cur_loaded = admin_session.local_cortex.get_aliases_by_pattern(_CUR_SENT_ALIAS)
        if not cur_loaded:
            cur_files = _cur_files_probe

            if cur_files:
                # Wait for the .csl ontology sentinel before loading curations. F27-7:
                # (1) NAME the sentinel alias at start AND on timeout — the old lines named
                #     nothing, so a timeout left the operator no thread to pull.
                # (2) SELF-HEAL (the F20 pattern) — if the sentinel alias is ALREADY present
                #     (CSL completed earlier this boot, or a warm restart), proceed at once
                #     instead of sleeping toward the 1 h ceiling. Skip-only on genuine timeout.
                logger.info("[Kernel] Curation gate: waiting for CSL sentinel '%s'…", _SENT_ALIAS)
                _wait_start = _time.time()
                _max_wait = 3600  # 1 hour ceiling (skip-only on timeout; no replay — see F20)
                if admin_session.local_cortex.get_aliases_by_pattern(_SENT_ALIAS):
                    logger.info("[Kernel] Curation gate: CSL sentinel '%s' already present — "
                                "proceeding without wait", _SENT_ALIAS)
                else:
                    while _time.time() - _wait_start < _max_wait:
                        _time.sleep(5)
                        if lifecycle.is_shutting_down(): return
                        if admin_session.local_cortex.get_aliases_by_pattern(_SENT_ALIAS):
                            break
                    else:
                        logger.warning("[Kernel] Curation gate: CSL sentinel '%s' not seen within "
                                       "%ds — skipping curation load", _SENT_ALIAS, _max_wait)
                        return

                logger.info("[Kernel] Queuing %d curation scripts…", len(cur_files))
                for idx, fpath in enumerate(cur_files):
                    try:
                        with open(fpath, "r", encoding="utf-8") as _f:
                            source = _f.read()
                        steps_raw = [{"method": "csl.run", "params": {"script": source}}]
                        if idx == len(cur_files) - 1:
                            steps_raw.append({
                                "method": "write",
                                "params": {"text": _CUR_SENT_TEXT, "scope": "universal"},
                            })
                            steps_raw.append({
                                "method": "alias",
                                "params": {"id": _CUR_SENT_KEY, "name": _CUR_SENT_ALIAS},
                            })
                        _submit_file_job(fpath, steps_raw,
                                         f"ont.curation:{os.path.basename(fpath)}")
                    except Exception as exc:
                        logger.warning("[Kernel] boot-load curation: %s: %s",
                                       os.path.basename(fpath), exc)
                logger.info("[Kernel] Curation load queued (%d files)", len(cur_files))

        # (the post-load daemons were already started above, BEFORE the curation gate, so a
        # curation time-out/skip can never strand them — see the guarded block there.)
        # NOTE: the live-telemetry poller is NOT started here. It is a first-class Supervisor
        # managed unit (svc:feed-poll) whose lifecycle belongs to the nucleus writer, not the
        # ontology load — started via _schedule_feed_poll() from the daemon convergence right after
        # svc:cell is recorded (akasha.py), so it can mount as a managed unit tied to the writer.

    except Exception as exc:
        logger.warning("[Kernel] Ontology boot load failed (non-fatal): %s", exc, exc_info=True)


# A token is a key=value arg only when the key part is a bare identifier;
# this keeps a quoted free-text argument that contains '=' positional (see
# _parse_ak_line below).
AK_KWARG_KEY_RE = re.compile(r"^[A-Za-z_][\w.:-]*$")
AK_WRITE = frozenset({"w", "write", "kernel.memory.write",
                       "def", "define", "kernel.memory.define"})
AK_MAP = {
    "w":   ("kernel.memory.write",  ["text"]),
    "write": ("kernel.memory.write", ["text"]),
    "def": ("kernel.memory.define",  ["name", "description"]),
    "define": ("kernel.memory.define", ["name", "description"]),
    "al":  ("alias",                 ["id", "name"]),
    "alias": ("alias",               ["id", "name"]),
    "ln":  ("kernel.memory.link",    ["src", "dst", "rel"]),
    "set.add": ("set.add",           ["name", "id"]),
}

def parse_ak_line(raw: str):
    """One `.ak` line → `{method, params}` or None — THE parser: the load and the reconcile's
    keep-set both read a line through it, so the keep-set's `def` is the load's `def` (D16)."""
    line = raw.strip()
    if not line or line.startswith("#"):
        return None
    try:
        parts = shlex.split(line)
    except ValueError:
        # Defensive strip: remove surrounding quotes left by plain split
        parts = [p.strip('"\'') for p in line.split()]
    if not parts:
        return None
    cmd = parts[0].lower()
    if cmd not in AK_MAP:
        return None
    method, arg_names = AK_MAP[cmd]
    args = parts[1:]
    params: dict = {}
    # Separate keyword args (key=value) from positional args so that
    # `set.add name="set:foo" id="bar"` maps correctly.
    kw: dict = {}
    pos: list = []
    for token in args:
        # Only a bare-identifier key is a real key=value arg. A quoted
        # free-text argument that legitimately contains '=' — e.g. a
        # `def "blvh:slot:001" "sampling_operation; slot=001; …"` description —
        # must stay POSITIONAL, else the '=' shreds it into a bogus kwarg
        # (key "sampling_operation; slot") and the description is silently
        # lost, leaving a bare hub atom. Real kwargs (name=, id=, content=)
        # always have identifier keys.
        if "=" in token:
            k, v = token.split("=", 1)
            if AK_KWARG_KEY_RE.match(k.strip()):
                kw[k] = v
                continue
        pos.append(token)
    for i, aname in enumerate(arg_names):
        if aname in kw:
            params[aname] = kw[aname]
        elif i < len(pos):
            params[aname] = pos[i]
        else:
            params[aname] = ""
    # Mark write/define as universal so they go to nucleus
    if method in AK_WRITE or method in ("kernel.memory.write", "kernel.memory.define"):
        params["scope"] = "universal"
    return {"method": method, "params": params}


def def_hub_content(name: str, description: str = "") -> str:
    """The exact content a `def` writes — `[name]\\ndescription` — and so, hashed, its KEY.

    `kernel.memory.define` writes this (it calls here) and content-addressing makes its sha256 the
    atom's key. The reconcile's keep-set computes the same thing from the files, so "the keys the
    current files define" is read from the files and not asked of the store (D16)."""
    desc = description or ("Conceptual hub: %s" % name)
    return "[%s]\n%s" % (str(name).replace(" ", "_"), desc)


def def_key(name: str, description: str = "") -> str:
    """The key a `def name "description"` line produces (sha256 of `def_hub_content`)."""
    import hashlib as _h
    return _h.sha256(def_hub_content(name, description).encode("utf-8")).hexdigest()


def file_def_keys(path: str):
    """(name, key) for every `def` in one `.ak` file — STREAMED through `parse_ak_line`."""
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            for raw in f:
                if raw.lstrip()[:4].lower() not in ("def ", "defi"):
                    continue
                st = parse_ak_line(raw)
                if not st or st["method"] != "kernel.memory.define":
                    continue
                nm = str(st["params"].get("name") or "").strip()
                if nm:
                    yield nm, def_key(nm, st["params"].get("description") or "")
    except OSError:
        return


# How long the loader WAITS on one pack's atom jobs (and then on its sentinel) before it moves on —
# a wait, never a cut: past it the pack completes in the background (P2).
PACK_WAIT_FLOOR_S = 1800
PACK_WAIT_PER_FILE_S = 60


def publish_in_flight(kernel, first: bool = False, packs=None, clear: bool = False) -> None:
    """Set (or clear) the load-in-flight record the driver reads — see `in_flight`."""
    kernel._onto_in_flight = None if clear else {"first": bool(first), "packs": list(packs or []),
                                                  "declares": {}}


def in_flight(kernel) -> dict:
    """The ontology load running now: `{first, packs, declares}`, or {} when none is."""
    return getattr(kernel, "_onto_in_flight", None) or {}


LOADING_NOTE = ("the ontology is still loading, so this may not exist yet — run `onto.status` to "
                "see its progress, and try again when it reports complete")


def loading_note(kernel) -> str:
    """`LOADING_NOTE` while an ontology load is in flight, else "". A read that finds nothing during
    the load answers with this instead of a verdict it cannot yet give (seeds 13 findings F1: a
    focus not loaded yet read as `dissolved or locked behind scope boundaries`)."""
    try:
        from lib.akasha.api import schedule as _sched
        if in_flight(kernel) or _sched.is_running(kernel, "ontology.loaded"):
            return LOADING_NOTE
    except Exception:
        pass
    return ""


def ontology_roots() -> List[str]:
    """The pack roots, in load order: the platform's `ontology/`, then the application's (the
    `packs` declaration root, `app/ontology/`). Each holds its own REGISTRY.json."""
    from lib.akasha.api import reserved as _reserved
    out = []
    for d in (os.path.join(project_dir(), "ontology"), _reserved.root("packs")):
        if os.path.isdir(d) and d not in out:
            out.append(d)
    return out


def user_root() -> str:
    """The cell operator's own packs: `ontology/user/` beside the platform's packs. Never shipped,
    never pruned, and needs no REGISTRY.json — a directory holding a `PACK.json` is a pack."""
    return os.path.join(project_dir(), "ontology", "user")


def user_packages() -> List[Dict[str, Any]]:
    """The self-describing packs under `ontology/user/`, by directory name: each `<dir>/PACK.json`
    is one pack, autoloaded unless its PACK.json says `"autoload": false` (then `onto.pack.enable`
    turns it on). A directory with no PACK.json is not a pack and is skipped."""
    import json as _json
    out = []
    root = user_root()
    try:
        names = sorted(os.listdir(root))
    except OSError:
        return out
    for n in names:
        d = os.path.join(root, n)
        pj = os.path.join(d, "PACK.json")
        if not os.path.isfile(pj):
            continue
        try:
            with open(pj, encoding="utf-8") as _f:
                meta = _json.load(_f) or {}
        except Exception as exc:
            logger.warning("[onto] user pack %s skipped: PACK.json unreadable (%s)", n, exc)
            continue
        entry = {"name": n, "autoload": bool(meta.get("autoload", True)), "user": True, "_dir": d}
        if meta.get("tier"):
            entry["tier"] = meta["tier"]
        out.append(entry)
    return out


def registry_packages() -> List[Dict[str, Any]]:
    """Every REGISTRY.json's `packages`, platform root first, then the operator's own packs
    (`user_packages`), each entry carrying `_dir` (its pack directory). A name registered twice
    keeps the first and logs the second."""
    import json as _json
    out, seen = [], set()
    for root in ontology_roots():
        try:
            with open(os.path.join(root, "REGISTRY.json"), encoding="utf-8") as _f:
                pkgs = _json.load(_f).get("packages", [])
        except Exception:
            continue
        for p in pkgs:
            n = p.get("name", "")
            if n in seen:
                logger.warning("[onto] pack %s registered twice — %s ignored", n, root)
                continue
            seen.add(n)
            out.append(dict(p, _dir=os.path.join(root, n)))
    for p in user_packages():
        if p["name"] in seen:
            logger.warning("[onto] pack %s registered twice — %s ignored", p["name"], p["_dir"])
            continue
        seen.add(p["name"])
        out.append(p)
    return out


def pack_dir(pack_name: str) -> str:
    """The directory of pack `pack_name` in whichever root holds it (the platform's when none does)."""
    for root in ontology_roots():
        d = os.path.join(root, pack_name)
        if os.path.isdir(d):
            return d
    d = os.path.join(user_root(), pack_name)
    if os.path.isfile(os.path.join(d, "PACK.json")):
        return d
    return os.path.join(project_dir(), "ontology", pack_name)


def _any_pack_sentinel(sent_dir: str, ont_dir: str = "") -> bool:
    """Has this cell EVER finished a pack? A pack's sentinel is `<pack>_<hash>.done`; other boot
    sentinels share the directory, so only names that start with a pack directory count."""
    try:
        packs = {d for r in ontology_roots() for d in os.listdir(r) if os.path.isdir(os.path.join(r, d))}
        packs |= {p["name"] for p in user_packages()}
        for fn in os.listdir(sent_dir):
            if fn.endswith(".done") and "_" in fn and fn.rsplit("_", 1)[0] in packs:
                return True
    except OSError:
        pass
    return False


def pack_declares(pack_name: str, names) -> set:
    """Which of `names` this pack DECLARES — as a `def` id, an `al` alias or a `set.add name=` Set.

    STREAMED one line at a time with nothing held but the answer, and asked only about the handful
    of names workloads declare (their `pins` and their `requires` Sets), so a pack of any size costs
    one read and a set of a few strings. The driver asks it about the packs in flight."""
    import shlex as _shlex
    want = {str(n) for n in (names or ()) if str(n)}
    found = set()
    pack_dir_ = pack_dir(pack_name)
    if not want or not os.path.isdir(pack_dir_):
        return found
    for _root, _dirs, _files in os.walk(pack_dir_):
        for fn in sorted(_files):
            if not fn.endswith(".ak"):
                continue
            try:
                with open(os.path.join(_root, fn), encoding="utf-8", errors="ignore") as _f:
                    for raw in _f:
                        if not any(w in raw for w in want):
                            continue
                        line = raw.strip()
                        try:
                            parts = _shlex.split(line)
                        except ValueError:
                            continue
                        if not parts:
                            continue
                        head = parts[0].lower()
                        if head in ("def", "al") and len(parts) >= 2:
                            cand = parts[1:3] if head == "al" else parts[1:2]
                        elif head == "set.add":
                            cand = [p.split("=", 1)[1] for p in parts[1:] if p.startswith("name=")]
                        else:
                            continue
                        found |= want & set(cand)
            except OSError:
                continue
    return found


def reserved_dirs(ont_dir: str = "") -> set:
    """The directories under the pack roots each REGISTRY says are not packs — `reserved_dirs`."""
    out = set()
    for root in ([ont_dir] if ont_dir else ontology_roots()):
        try:
            with open(os.path.join(root, "REGISTRY.json"), encoding="utf-8") as f:
                out |= {str(x) for x in (json.load(f).get("reserved_dirs") or []) if str(x).strip()}
        except Exception:
            pass
    return out


def pack_def_key_set(kernel, session, pack_name: str) -> set:
    """The keys a pack's defs DEFINE — computed from the files, a SET of keys and nothing else.

    D16 (directive 2026-10-02 §1). This used to resolve each def NAME through the store's alias
    index (`resolver.resolve_alias(nm)`) and keep whatever key the name pointed at. That answers a
    different question — "where does this name point NOW?" — and it is wrong exactly when a def is
    redefined: a name left on its old text, or unbound, keeps the old key and leaves the new text
    out, so the reconcile retired the keys the current files define (`station_neta`, 09-28:
    `keys=59 retired=45` for 104 defs). A def's key is the sha256 of the content it writes
    (`def_key`, the same function `kernel.memory.define` hashes), so the files answer this alone,
    whatever state the alias index is in. Streamed per file; nothing but the set is held."""
    out = set()
    pack_dir_ = pack_dir(pack_name)
    if not os.path.isdir(pack_dir_):
        return out
    for _root, _dirs, _files in os.walk(pack_dir_):
        for fn in sorted(_files):
            if fn.endswith(".ak"):
                for _nm, key in file_def_keys(os.path.join(_root, fn)):
                    out.add(key)
    return out


def pack_def_keys(kernel, session, pack_name: str):
    """(keys:set, names:list) a pack's .ak files define — the keys COMPUTED from the files'
    content (`file_def_keys`), not resolved through the alias index (D16; see
    `pack_def_key_set`). The `onto.reconcile` op reads this; the boot reconcile reads the set."""
    keys, names = set(), []
    pack_dir_ = pack_dir(pack_name)
    if not os.path.isdir(pack_dir_):
        return keys, names
    for _root, _dirs, _files in os.walk(pack_dir_):
        for fn in sorted(_files):
            if fn.endswith(".ak"):
                for nm, key in file_def_keys(os.path.join(_root, fn)):
                    names.append(nm)
                    keys.add(key)
    return keys, names


def active_reconcile_packs(kernel, session, explicit: str = ""):
    """Packs to reconcile: an explicit `pack=` if given, else every pack that already has a
    member-ledger (`ont:pack:members:<name>`) — i.e. one we have tracked on a prior load."""
    if explicit:
        return [explicit]
    nucleus = getattr(session, "nucleus", None)
    core = nucleus.core if nucleus else session.local_cortex.core
    out = []
    try:
        for nm in (core.get_distinct_collection_names("ont:pack:members:") or []):
            p = nm[len("ont:pack:members:"):]
            if p:
                out.append(p)
    except Exception:
        pass
    return sorted(set(out))
