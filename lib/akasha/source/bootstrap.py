"""
The seed-time corpus bootstraps (the source packs and every corpus `config/source/*.json` declares) and the pool readiness probe — moved out of the kernel (backend layout order 2026-09-20).

Every function takes the kernel (the heart) as its first argument: it is the object the
dispatcher / timer registry hands in, never imported. Bodies are the kernel's own, moved
verbatim except `self.` → `kernel.` and intra-family calls.
"""
import os
import re
import sys
import glob
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
from lib.akasha.identity import Role, Capability
from lib.akasha.api.trust import (TRUST_NETWORK, TRUST_LOCAL, TRUST_INTERNAL,
                                  TRUSTED_TRANSPORTS as _TRUSTED_TRANSPORTS)
from lib.akasha.api.heart import _rss_mb, _search_partial_incr, _SEARCH_PARTIAL, _MAINT_LOCK, _MAINT_LAST_DONE, _MAINT_GAP_S, _MAINT_GATE_AVAIL_MB, _MAINT_GATE_MAX_WAIT_S, _MAINT_GATE_RETRY_S, _maint_gate_ok, _run_gated_maint, _with_rss_delta, _mem_available_mb, _smaps_rollup, _thread_count, _open_fd_count, _fd_soft_limit, _autolearn_disabled_reason
from lib.akasha import api as _api

logger = logging.getLogger("Akasha.Kernel")

_PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

_BOOTSTRAP_CAP_S = 5400       # default wall-clock ceiling for ONE declared import
_RELATIONS_WAIT_S = 1800      # how long the serve-first gate waits for the ontology load

# Reasons this package can skip something and carry on. Vocabulary ids, logged as themselves with
# the exception in `detail=` — never a `logger.debug` nobody sees at the default level.
SKIP_DECL_UNREADABLE = "decl_unreadable"    # a config/source/*.json that will not parse
SKIP_IMPORT_FAILED = "import_failed"        # one declared import raised; the others continue
SKIP_UNIT_FAILED = "unit_failed"            # the managed unit's own thread raised
SKIP_REASONS = (SKIP_DECL_UNREADABLE, SKIP_IMPORT_FAILED, SKIP_UNIT_FAILED)


def pool_frozen(kernel, pool: str) -> bool:
    """Readiness probe (§2.3): does `pool` exist AND is it FROZEN? One `source.status pool=` over
    TRUST_INTERNAL — the tally is precomputed at freeze, so this is a cheap indexed read (never an
    atom sweep). A missing pool or an OPEN one is not ready."""
    if not pool:
        return True
    try:
        resp = kernel.dispatch({"jsonrpc": "2.0", "method": "source.status",
                              "params": {"client_id": "admin", "data": {"pool": pool}}, "id": "rdy"},
                             TRUST_INTERNAL)
        res = (resp or {}).get("result") or {}
        return bool(res.get("frozen")) and (res.get("total") or 0) > 0
    except Exception:
        return False


# THE FROZEN-POOL SET (directive 2026-10-02 §6.1). The source engine is its ONLY writer: a pool
# enters it the moment it freezes (frozen and non-empty — the same answer `pool_frozen` gives),
# and the boot reconcile below states it for pools frozen before this Set existed. Members are the
# pool KEYS (`source:pool:<id>:v<n>`). A workload may name this Set in `requires`; the workbench
# then binds its client to EVERY member and re-converges on the freeze hook, so a pool frozen later
# is covered at its freeze. Not a gate fact: step 4 reads workload keys, this holds pools.
POOL_FROZEN = "set:source:pool:frozen"


def state_pool_frozen(kernel, pool: str, frozen: bool) -> bool:
    """Put `pool` in `set:source:pool:frozen`, or take it out. The ONE write path for the Set."""
    if not pool:
        return False
    from lib.akasha.api import facts as _facts
    return _facts.state(kernel, POOL_FROZEN, str(pool), bool(frozen))


def frozen_pools(kernel) -> list:
    """The members of `set:source:pool:frozen` — the pool keys, sorted."""
    from lib.akasha.api import facts as _facts
    return _facts.members(kernel, POOL_FROZEN)


def reconcile_pool_frozen(kernel) -> int:
    """State the Set from the pools as they are — every boot (O(#pools), one indexed read each).

    A Set written only at freeze is empty on a cell whose pools froze before it existed; this is
    the same reconcile-at-boot the readiness facts get. A pool that is no longer frozen (deleted or
    re-opened) leaves the Set. Returns the number of members."""
    try:
        resp = kernel.dispatch({"jsonrpc": "2.0", "method": "source.pools",
                                "params": {"client_id": "admin", "data": {}}, "id": "pf"},
                               TRUST_INTERNAL)
        pools = [str(p.get("pool")) for p in ((resp or {}).get("result") or {}).get("pools") or []
                 if isinstance(p, dict) and p.get("pool")]
    except Exception as exc:                      # noqa: BLE001 — a boot never dies of bookkeeping
        logger.warning("[source] frozen-pool reconcile skipped: %s: %s", type(exc).__name__, exc)
        return 0
    want = {p for p in pools if pool_frozen(kernel, p)}
    have = set(frozen_pools(kernel))
    for p in sorted(want - have):
        state_pool_frozen(kernel, p, True)
    for p in sorted(have - want):
        state_pool_frozen(kernel, p, False)
    logger.info("[source] frozen pools reconciled set=%s members=%d added=%d removed=%d",
                POOL_FROZEN, len(want), len(want - have), len(have - want))
    return len(want)


def state_source_ready(kernel, pool: str) -> bool:
    """This pool's readiness CHANGED — announce it, and return the answer.

    THE SOURCE ENGINE KNOWS ABOUT POOLS, NOT ABOUT WORKLOADS. It owns `pool_frozen`, and that is
    the whole of what it may say. The gate's fact Set holds WORKLOAD KEYS (its step 4 asks
    `target ∈ … source_ready`), and which workload requires which pool is read from the
    declarations — the workbench's knowledge, and `source` is LEFT of `workbench` on the layer map.

    So this states nothing itself. It fires the ONE declared upward call, `source_ready_changed`,
    and the workbench re-states the workloads that were waiting for this pool. Writing the pool
    name into the gate's Set — which the first pass did — put two shapes in one Set, and the gate
    then answered `source_ready` (a refusal) for a programme that was on air (D4).

    The hook is absent on a cell with no workbench: then nothing was waiting, and the answer below
    is still the truth about the pool."""
    ready = pool_frozen(kernel, pool)
    state_pool_frozen(kernel, pool, ready)        # §6.1 — before the hook, so it reads the new Set
    try:
        from lib.akasha import api as _api
        fn = _api.hook(kernel, "source_ready_changed")
        if fn:
            fn(kernel, str(pool))
    except Exception as exc:                      # noqa: BLE001 — reported; the read still answers
        logger.warning("[source] readiness change not announced pool=%s reason=%s: %s",
                       pool, type(exc).__name__, exc)
    return bool(ready)


# The RECONCILE lives in `workbench/provision.py`, not here. It has to read the DECLARATIONS to
# know which pools anything requires, and `source` is LEFT of `workbench` on the layer map — a
# source module importing the workbench is the rightward edge §A21 forbids, and `wiring_eval`
# caught it. The source engine owns the FACT (`state_source_ready` above); the workbench owns
# knowing which facts to ask for. Each says only what it knows.

def source_pack_dir(kernel) -> str:
    from lib.akasha.api import reserved as _reserved
    return os.environ.get("AKASHA_SOURCE_PACK_DIR") or _reserved.root("assets")


def source_pack_acquire(kernel, pool: str, pack: dict, space: str, dispatch) -> dict:
    """§2.2 — a data-less pack with `acquire:{kind,params,egress}` enqueues ONE resumable boot
    acquisition job through the concept model named by `kind` (the fetcher lives with the bench
    designer). No fetcher routed for this `kind` ⇒ leave the pool unimported and log; the readiness
    gate then keeps the bench waiting (egress closed / no fetcher = the bench waits, never fails).
    Retried at boot granularity — no sentinel is written until the pool freezes."""
    acq = pack.get("acquire") or {}
    kind = str(acq.get("kind") or "").strip()
    known = kind in getattr(kernel, "_method_action_map", {}) or kernel._is_method_known(kind)
    if not kind or not known:
        logger.info("[source.pack] %s acquiring… (kind=%s has no fetcher on this cell — bench waits)",
                    pool, kind or "?")
        return {"pool": pool, "status": "acquire_deferred", "kind": kind or None}
    try:
        params = dict(acq.get("params") or {})
        params.setdefault("pool", pool)
        if space:
            params.setdefault("space", space)
        logger.info("[source.pack] %s acquiring… (kind=%s)", pool, kind)
        r = dispatch(kind, params)
        return {"pool": pool, "status": "acquiring", "kind": kind, "result": bool(r)}
    except Exception as exc:
        logger.info("[source.pack] %s acquire kind=%s deferred: %s", pool, kind, exc)
        return {"pool": pool, "status": "acquire_deferred", "kind": kind, "error": str(exc)}


def iter_pack_records(data_path: str):
    """Stream a pack's data file ROW BY ROW (R1 — never load it whole). Gz-aware; JSONL by line,
    CSV via DictReader. A malformed JSONL line is yielded as {'__malformed__': line} (acquire keeps
    it as an explicit failure — failure is evidence, never dropped)."""
    import gzip as _gz
    import csv as _csv
    opener = (lambda p: _gz.open(p, "rt", encoding="utf-8")) if data_path.endswith(".gz") \
        else (lambda p: open(p, "r", encoding="utf-8"))
    is_csv = data_path[:-3].endswith(".csv") if data_path.endswith(".gz") else data_path.endswith(".csv")
    with opener(data_path) as fh:
        if is_csv:
            for row in _csv.DictReader(fh):
                yield dict(row)
            return
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                yield obj if isinstance(obj, dict) else {"__malformed__": line}
            except json.JSONDecodeError:
                yield {"__malformed__": line}


def count_pack_rows(data_path: str) -> int:
    """Fast row count for the progress line (A23) — a streaming line/row count, gz-aware, no JSON
    parse. One extra decompress pass over a text pack is cheap (~a few 100 ms for a 2 MB gz) and
    lets the import report rows=<n>/<total>."""
    import gzip as _gz
    opener = (lambda p: _gz.open(p, "rt", encoding="utf-8")) if data_path.endswith(".gz") \
        else (lambda p: open(p, "r", encoding="utf-8"))
    is_csv = data_path[:-3].endswith(".csv") if data_path.endswith(".gz") else data_path.endswith(".csv")
    try:
        with opener(data_path) as fh:
            n = sum(1 for ln in fh if ln.strip())
        return max(0, n - 1) if is_csv else n     # CSV: drop the header row
    except Exception:
        return 0


def source_packs_once(kernel, pack_dir: str = None, batch: int = 500) -> list:
    """Import every assets/<pack>/pack.json at boot, each behind a sha256-keyed fsync'd sentinel
    (a corrected data file re-imports; an unchanged one is a no-op), NON-CLOBBERING (an existing
    FROZEN pool of the same name is left alone). Returns the applied actions (the test seam). A
    seeds cell ships no pack → [].

    Pace (A25): the loader streams the file in batches of `batch` rows and commits each through the
    single WriteQueue at boot-admin priority — the queue is the pace, there is no sleep in the loop.
    Measured ≈500 rows / ≈70 s on the VPS writer, so a 49k-row checklist is ≈1.9 h; this is a
    ONE-TIME import (sha-keyed sentinel), off the user path. A pack may raise its own `batch` in
    pack.json (e.g. 2000 for a text-only pack) to cut the commit count when the writer would
    otherwise idle between commits; the images pack keeps the default. Progress is logged every 10
    batches and surfaced on the Health line as `packs(importing=…)` (A23)."""
    import glob as _glob
    import hashlib as _hl
    pack_dir = pack_dir or source_pack_dir(kernel)
    sent_dir = os.path.join(kernel.base_dir, "central", "sentinels")
    try:
        os.makedirs(sent_dir, exist_ok=True)
    except OSError:
        pass
    actions = []

    def _dispatch(method, data):
        r = kernel.dispatch({"jsonrpc": "2.0", "method": method,
                           "params": {"client_id": "admin", "data": data}, "id": "srcpack"},
                          TRUST_INTERNAL)
        if isinstance(r, dict) and "error" in r:
            raise RuntimeError("%s: %s" % (method, (r["error"] or {}).get("message")))
        return (r or {}).get("result") if isinstance(r, dict) and "result" in r else r

    def _sha8(path):
        h = _hl.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()

    for pj in sorted(_glob.glob(os.path.join(pack_dir, "*", "pack.json"))):
        try:
            with open(pj, "r", encoding="utf-8") as fh:
                pack = json.load(fh)
        except Exception as exc:
            logger.warning("[source.pack] %s unreadable: %s", pj, exc)
            continue
        pool = str(pack.get("pool") or "").strip()
        if not pool:
            continue
        pdir = os.path.dirname(pj)
        data_file = pack.get("data")
        data_path = os.path.join(pdir, data_file) if data_file else ""
        acquire = pack.get("acquire") or None
        space = str(pack.get("space") or "").strip()   # "" = nucleus (default), "group:<gid>"
        # §2.2 — no bundled data but an acquire directive: enqueue the fetcher (boot acquisition),
        # never block. v1 packs ALWAYS ship data; acquire on a data-bearing pack is the refresh path.
        if data_path and not os.path.isfile(data_path):
            logger.warning("[source.pack] %s declares data=%s but the file is missing", pool, data_file)
            data_path = ""
        sha = _sha8(data_path) if data_path else ""
        import re as _re
        _pslug = _re.sub(r"[^a-z0-9]+", "_", pool.lower()).strip("_") or "pool"
        tag = "%s_%s" % (_pslug, (sha[:12] or "acquire"))
        sent = os.path.join(sent_dir, "source_pack_%s.done" % tag)
        # A40(a) — the `label_field` JOIN HINT is (re)stamped on an ALREADY-PRESENT pool BEFORE the
        # import sentinel can short-circuit the pack. The live VPS imported plants_images under an
        # earlier build WITHOUT label_field; its import sentinel exists, so the frozen-pool re-stamp
        # BELOW (guarded by that same sentinel) never ran and the pool never learned its class —
        # b4 could train (label_key in the candidate list) but b5 evaluate resolves ONLY from the
        # pool's label_fields, scoring an empty frame. This runs every boot: one `source.status`
        # read per pack; the write fires only when the pool exists and its stored field differs.
        _lf = pack.get("label_field")
        if _lf:
            try:
                _st = _dispatch("source.status", {"pool": pool}) or {}
                if _st.get("exists") and _st.get("label_field") != _lf:
                    _dispatch("source.pool.create", {"name": pool, "label_field": _lf,
                                                     **({"space": space} if space else {})})
                    logger.info("[source.pack] %s label_field=%s stamped on existing pool "
                                "(join hint, frozen frame untouched)", pool, _lf)
            except Exception:
                pass
        if os.path.exists(sent):
            continue
        # NON-CLOBBERING: an already-frozen pool of this name (an operator's, or a prior boot's) is
        # never re-imported — record the sentinel so we stop re-checking, and move on. (The
        # label_field re-stamp above already ran, independent of this sentinel.)
        try:
            if pool_frozen(kernel, pool):
                logger.info("[source.pack] %s present (frozen%s) — skipped", pool,
                            (", label_field=%s" % _lf) if _lf else "")
                kernel._write_sentinel(sent, "present %s\n" % pool)
                actions.append({"pool": pool, "status": "present"})
                continue
        except Exception:
            pass
        if not data_path:
            if acquire:
                actions.append(source_pack_acquire(kernel, pool, pack, space, _dispatch))
            continue
        # ── import the bundled snapshot: register → pool.create → stream-acquire → freeze ──
        try:
            provider = pack.get("provider") or "source-pack"
            rights = pack.get("rights") or "unspecified"
            rule = pack.get("rule") or "bundled source pack"
            id_field = pack.get("id_field") or "id"
            label_field = pack.get("label_field") or ""
            sname = pack.get("name") or pack.get("collection") or pool
            reg = _dispatch("source.register", {"provider": provider, "name": sname,
                                                "collection": pack.get("collection") or "",
                                                "uri": pack.get("retrieval") or f"pack:{pool}",
                                                "rights": rights,
                                                **({"space": space} if space else {})})
            src_alias = (reg or {}).get("source") or sname
            _dispatch("source.pool.create", {"name": pool, "rule": rule, "source": src_alias,
                                             "version": pack.get("version") or "v1",
                                             **({"label_field": label_field} if label_field else {}),
                                             **({"space": space} if space else {})})
            # A25 — a pack may override the batch size (text-only packs raise it to cut commits).
            try:
                pbatch = max(1, int(pack.get("batch") or batch))
            except (TypeError, ValueError):
                pbatch = batch
            grand = count_pack_rows(data_path)     # A23 — total for the progress line
            nbatches = max(1, (grand + pbatch - 1) // pbatch) if grand else 0
            total = frozen = 0
            buf = []
            bi = [0]
            t0 = time.time()

            def _flush():
                nonlocal total
                if not buf:
                    return
                res = _dispatch("source.acquire", {"source": src_alias, "rule": rule,
                                                   "records": list(buf), "id_field": id_field,
                                                   "pool": pool,
                                                   **({"label_field": label_field} if label_field else {}),
                                                   **({"space": space} if space else {})})
                total += int((res or {}).get("total", len(buf)))
                buf.clear()
                bi[0] += 1
                # A23 — a progress line every 10 batches + a Health `packs(importing=…)` segment, so a
                # multi-hour import is never a silent gap between "daemons started" and "imported".
                kernel._source_pack_status = {"pool": pool, "n": total,
                                            "total": grand or None, "frozen": False}
                if bi[0] % 10 == 0:
                    el = max(1e-6, time.time() - t0)
                    rate = int(total / el * 60.0)
                    logger.info("[source.pack] %s importing rows=%d/%s batch=%d/%s rate=%d/min",
                                pool, total, grand or "?", bi[0], nbatches or "?", rate)

            for rec in iter_pack_records(data_path):
                buf.append(rec)
                if len(buf) >= pbatch:
                    _flush()
            _flush()
            if str(pack.get("freeze", True)).lower() not in ("0", "false", "no", "off"):
                fr = _dispatch("source.pool.freeze", {"pool": pool, **({"space": space} if space else {})})
                frozen = 1 if (fr or {}).get("status") == "FROZEN" else 0
            kernel._source_pack_status = None              # A23 — clear the Health segment when done
            kernel._write_sentinel(sent, "imported %s rows=%d frozen=%d sha=%s\n" % (pool, total, frozen, sha[:8]))
            logger.info("[source.pack] %s imported rows=%d frozen=%s sha=%s",
                        pool, total, bool(frozen), sha[:8])
            actions.append({"pool": pool, "status": "imported", "rows": total, "frozen": bool(frozen)})
        except Exception as exc:
            # Do NOT sentinel a failed/partial import — retry next boot (the pool stays OPEN/absent,
            # so the readiness gate keeps the bench waiting; never a silently-latched half pool).
            kernel._source_pack_status = None              # clear the Health segment on failure too
            logger.warning("[source.pack] %s import failed (non-fatal): %s", pool, exc)
            actions.append({"pool": pool, "status": "failed", "error": str(exc)})
    kernel._source_pack_status = None                      # all packs handled — no import in flight
    return actions


def schedule_source_packs(kernel) -> None:
    """Seed-time autonomy §2.1 — import bundled source packs (assets/<pack>/pack.json) into the
    Source Data Layer at boot, BEFORE any bench runs, so a seed-baked bench is self-sufficient
    (its data is imported+frozen with no operator action). Writer-only, serve-first (gated on
    AKASHA_SERVE_ONLY + relations-ready + the boot heartbeat), run-once per data-file sha256,
    NON-CLOBBERING. A seeds cell ships no pack ⇒ the thread exits immediately."""
    if os.environ.get("AKASHA_SERVE_ONLY", "").strip().lower() not in ("", "0", "no", "false", "off"):
        return
    import glob as _glob
    pack_dir = source_pack_dir(kernel)
    if not _glob.glob(os.path.join(pack_dir, "*", "pack.json")):
        return   # no source packs bundled on this tier

    def _run():
        from lib.akasha import lifecycle
        deadline = time.time() + 7200
        while time.time() < deadline and not kernel._relations_ready():
            if lifecycle.wait_or_shutdown(5):
                return
        _hb = os.path.join(kernel.base_dir, "central", "boot.heartbeat")
        _dl = time.time() + 900
        while time.time() < _dl and os.path.exists(_hb):
            if lifecycle.wait_or_shutdown(2):
                return
        try:
            source_packs_once(kernel)
        except Exception as exc:
            logger.debug("[source.pack] loader skipped: %s", exc)

    import threading as _thr
    _thr.Thread(target=_run, name="source-packs", daemon=True).start()


def source_declarations(kernel=None) -> List[Dict[str, Any]]:
    """Every `config/source/*.json` that declares an `importer`, in id order.

    A corpus is a DECLARATION, not a branch. The platform reads the file, runs the managed unit
    around whatever the declaration's `importer` names, and never learns which dataset it just
    imported — so a fifth corpus is a file, the way a fifth workload is."""
    out = []
    from lib.akasha.api import reserved as _roots      # the declaration ROOT (purge order §1.3)
    for path in sorted(glob.glob(os.path.join(_roots.root("source"), "*.json"))):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                decl = json.load(fh)
        except (OSError, ValueError) as exc:
            logger.warning("[source.bootstrap] skipped reason=%s file=%s detail=%s",
                           SKIP_DECL_UNREADABLE, os.path.basename(path), exc)
            continue
        if not isinstance(decl, dict) or not str(decl.get("importer") or "").strip():
            continue                      # a config file that is not a declared import
        decl = dict(decl)
        decl.setdefault("id", os.path.splitext(os.path.basename(path))[0])
        decl["_file"] = os.path.basename(path)
        out.append(decl)
    return sorted(out, key=lambda d: str(d.get("id")))


def declared_importer(decl: Dict[str, Any]):
    """Resolve a declaration's `importer` (`module:function`) to a callable, or raise.

    Late-bound through the module attribute, the way a manifest hook is: the platform holds no
    import of the user side, and a declaration naming something that is not there fails LOUDLY at
    the one place that can say which declaration did it."""
    spec = str((decl or {}).get("importer") or "").strip()
    if ":" not in spec:
        raise ValueError("importer must be 'module:function', got %r" % spec)
    mod_name, fn_name = spec.split(":", 1)
    if _PROJECT_DIR not in sys.path:
        sys.path.insert(0, _PROJECT_DIR)
    mod = __import__(mod_name, fromlist=[fn_name])
    fn = getattr(mod, fn_name, None)
    if not callable(fn):
        raise AttributeError("%s has no callable %s" % (mod_name, fn_name))
    return fn


def reset_key_digest(decl: Dict[str, Any]) -> str:
    """A hash over the files `reset_key` names, in declared order — the platform's OWN gate.

    This is what the sentinel records, and comparing it is the whole of R4: a boot that finds the
    same bundle it imported last time stops before it calls anything. The key is DECLARED rather
    than inferred from the directory, so adding a file to a bundle is a deliberate re-import.
    A named file the cell does not have contributes its absence, so losing a file is a change too.

    The importer computes its own hash for its own finer decision (import vs reload vs skip, and
    whether a derived layer must be rebuilt). That is not a duplicate: this one answers "may the
    boot stop asking", which is the managed unit's question and nobody else's."""
    h = hashlib.sha256()
    for pat in ((decl or {}).get("reset_key") or []):
        matched = sorted(glob.glob(os.path.join(_PROJECT_DIR, str(pat)))) or \
            [os.path.join(_PROJECT_DIR, str(pat))]
        for p in matched:
            h.update(os.path.relpath(p, _PROJECT_DIR).encode("utf-8"))
            try:
                with open(p, "rb") as fh:
                    for chunk in iter(lambda: fh.read(1 << 20), b""):
                        h.update(chunk)
            except OSError:
                h.update(b"\x00absent")
    return h.hexdigest()


def _sentinel_path(kernel, decl: Dict[str, Any]) -> str:
    d = os.path.join(kernel.base_dir, "central", "sentinels")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "source_bootstrap_%s.done" % str(decl.get("id") or "unknown"))


def _progress_path(kernel, decl: Dict[str, Any]) -> str:
    return _sentinel_path(kernel, decl)[:-len(".done")] + ".progress"


def _sentinel_digest(path: str) -> str:
    """The bundle hash a completed run recorded, or "" (including for a pre-hash sentinel file,
    which therefore re-imports once and then records its hash)."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("content_hash="):
                    return line.split("=", 1)[1].strip()
    except OSError:
        pass
    return ""


def _write_sentinel(path: str, digest: str, detail: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("content_hash=%s\n%s\n" % (digest, detail))
        fh.flush()
        os.fsync(fh.fileno())


def _bootstrap_skipped(decl: Dict[str, Any]) -> bool:
    """Is this declaration switched off? Only by itself — `"enabled": false` — a declared fact
    of the corpus, never an environment switch (the purge order §4.5)."""
    return (decl or {}).get("enabled") is False


def _bootstrap_cap_s(decl: Dict[str, Any]) -> int:
    """The hard wall-clock ceiling for one declared import: the declaration's, the host's override,
    or the default. A cap is what stops an unreachable network turning a boot phase into a thread
    that spins for the life of the process."""
    try:
        env = int(os.environ.get("AKASHA_SOURCE_BOOTSTRAP_MAX_S", "0") or 0)
    except (TypeError, ValueError):
        env = 0
    if env > 0:
        return env
    try:
        return max(0, int((decl or {}).get("cap_s") or 0)) or _BOOTSTRAP_CAP_S
    except (TypeError, ValueError):
        return _BOOTSTRAP_CAP_S


class _UnitCtl:
    """The seam the managed unit offers a declared importer: `say` / `progress` / `advance`.

    `say` is one phase — it beats the supervised unit's heartbeat, records the phase for `svc.ls`,
    and RAISES when the run has outlived its cap or the cell is shutting down. Raising is the point:
    an importer that swallowed it would keep working past the ceiling that exists to bound it, so
    the contract says it must let this propagate.

    `progress` / `advance` are the resume cursor, for a corpus too large to finish inside one cap.
    The cursor is written only after a batch is DURABLY acquired, so a killed run resumes at rows it
    really wrote rather than past them."""

    def __init__(self, decl, update, progress_path, cap_s, t0):
        self._id = str(decl.get("id") or "?")
        self._update = update
        self._path = progress_path
        self._cap_s = cap_s
        self._t0 = t0
        self._n = None

    def say(self, msg):
        from lib.akasha import lifecycle
        logger.info("[source.bootstrap] %s: %s", self._id, msg)
        try:
            self._update("running", str(msg))
        except Exception:
            pass
        if lifecycle.is_shutting_down():
            raise RuntimeError("shutting down")
        if self._cap_s and time.time() - self._t0 > self._cap_s:
            raise TimeoutError("exceeded %ds cap" % self._cap_s)

    def progress(self):
        if self._n is None:
            self._n = 0
            try:
                with open(self._path, "r", encoding="utf-8") as fh:
                    self._n = max(0, int((fh.read() or "0").strip() or 0))
            except (OSError, ValueError, TypeError):
                pass
        return self._n

    def advance(self, n):
        self._n = max(0, int(n))
        try:
            with open(self._path, "w", encoding="utf-8") as fh:
                fh.write(str(self._n))
                fh.flush()
                os.fsync(fh.fileno())
        except OSError:
            pass


def run_declared_import(kernel, decl: Dict[str, Any]) -> Dict[str, Any]:
    """Run ONE declared import inside its managed unit, and return the importer's report.

    The unit is everything that is true of importing a corpus and nothing that is true of any
    particular corpus: the run-once sentinel keyed on the declared bundle, the supervised unit with
    its heartbeat, the hard wall-clock cap, the resume cursor, and the dispatch identity. The
    importer supplies the dataset knowledge and says, in `sentinel`, whether this run earned the
    right not to happen again — `complete` and an unchanged `skipped` do; `no_data`, `degraded` and
    `failed` do not, so an interrupted or silently-degraded run is retried on the next boot instead
    of being recorded as finished."""
    sid = str(decl.get("id") or "unknown")
    done = _sentinel_path(kernel, decl)
    digest = reset_key_digest(decl)
    if os.path.exists(done) and _sentinel_digest(done) == digest and digest:
        return {"status": "skipped", "detail": "sentinel matches the declared bundle",
                "sentinel": True, "opened": False}

    update, close = kernel._bg_phase_unit("svc:source-bootstrap:%s" % sid)
    cap_s = _bootstrap_cap_s(decl)
    t0 = time.time()
    try:
        update("resolving", "loading the declared importer")
        fn = declared_importer(decl)
        ctl = _UnitCtl(decl, update, _progress_path(kernel, decl), cap_s, t0)
        update("running", "importing")
        rep = fn(kernel, decl, ctl) or {}
        status = str(rep.get("status") or "failed")
        detail = str(rep.get("detail") or "")
        if rep.get("sentinel"):
            _write_sentinel(done, digest, "%s %s" % (status, detail))
            try:
                os.remove(_progress_path(kernel, decl))     # the cursor's work is finished
            except OSError:
                pass
        logger.info("[source.bootstrap] %s status=%s sentinel=%s t=%.1fs detail=%s",
                    sid, status, bool(rep.get("sentinel")), time.time() - t0, detail or "-")
        update(status, detail or status)
        return rep
    except Exception as exc:
        # WITH the traceback. `detail=` carries the exception's message, and a message like
        # "'NoneType' object has no attribute 'get'" names no file, no line and no caller — the
        # 09-22 boot logged exactly that and the failure could not be diagnosed from the log at
        # all. This is an exception on a path that is supposed to work, once per declared import,
        # so the frames are the signal and there is no volume argument against them.
        logger.warning("[source.bootstrap] %s skipped reason=%s detail=%s",
                       sid, SKIP_IMPORT_FAILED, exc, exc_info=True)
        try:
            update("failed", str(exc))
        except Exception:
            pass
        return {"status": "failed", "detail": str(exc), "sentinel": False}
    finally:
        try:
            close()
        except Exception:
            pass


def schedule_source_bootstrap(kernel) -> None:
    """Import every DECLARED corpus, once, in the background — the one managed unit (step 2 §1).

    Four datasets used to be four near-identical bodies here, each ~250 lines, each holding one
    corpus's directory, pool, labo and reset rule beside the boot machinery they shared. The four
    bodies are the frontend's now (`config/source/<id>.json` → `importer`); what stays is this, the
    part that is true of importing ANY corpus:

      * run-once — a fsync'd sentinel under the protected `data/central/sentinels/` tree, keyed on
        the hash of the declared `reset_key`, so a changed bundle re-imports and an unchanged one
        stops before a corpus file is opened (memory discipline R4);
      * supervised — one `svc:source-bootstrap:<id>` unit per declaration, so `svc.ls` shows the
        phase and a wedged import goes stale instead of disappearing;
      * bounded — a hard wall-clock cap, raised through `ctl.say`, so an unreachable network cannot
        leave a thread spinning for the life of the process;
      * resumable — a progress cursor for a corpus too large for one cap;
      * serve-first and writer-only — the serve-only worker never double-writes the shared nucleus,
        and the import waits for the ontology relations phase so it does not compete with the boot
        load for the WriteQueue;
      * ONE thread for all declarations, run in id order. Four threads for four corpora was a
        population nobody bounded (memory discipline R3); serial is also what the single-writer
        WriteQueue wanted anyway.

    Off: `"enabled": false` in a declaration. The cap is `AKASHA_SOURCE_BOOTSTRAP_MAX_S` (the host's
    ceiling) or the declaration's `cap_s`."""
    if os.environ.get("AKASHA_SERVE_ONLY", "").strip().lower() not in ("", "0", "no", "false", "off"):
        return  # only the sole nucleus writer imports (mirrors the boot-load serve-only guard)

    # One line whatever the answer is. A cell that ships no corpus and a cell whose declarations
    # were DROPPED IN PACKAGING look identical from here — both have nothing to import — and the
    # silent version of this branch is what let four seeds ship without a single `config/source/
    # *.json` and import nothing, with no line anywhere saying so. `found=` is what the tree has,
    # `runnable=` what is left after the skip switches; `found=0` on a tier that is supposed to
    # carry a corpus is a PACKAGING defect, and now it is legible at boot instead of by absence.
    _all = source_declarations(kernel)
    decls = [d for d in _all if not _bootstrap_skipped(d)]
    logger.info("[source.bootstrap] declarations found=%d runnable=%d%s",
                len(_all), len(decls),
                (" ids=" + ",".join(sorted(str(d.get("id") or "?") for d in decls))) if decls else "")
    if not decls:
        return

    def _run():
        from lib.akasha import lifecycle
        try:
            try:
                admin_role = kernel.iam.authenticate("admin")
            except PermissionError:
                return                      # no admin yet — genesis_rite not done
            if admin_role not in (Role.ADMIN, Role.LIBRARIAN):
                return
            # Serve-first: wait for the ontology relations phase so the import's universal writes
            # do not contend with the boot load for the single writer.
            deadline = time.time() + _RELATIONS_WAIT_S
            while time.time() < deadline:
                if lifecycle.is_shutting_down():
                    return
                if kernel._relations_ready():
                    break
                time.sleep(5)
            if lifecycle.is_shutting_down():
                return
            if not kernel._relations_ready():
                logger.info("[source.bootstrap] relations-complete marker not seen within the "
                            "ceiling — proceeding best-effort")
            logger.info("[source.bootstrap] %d declared corpus/corpora: %s",
                        len(decls), ", ".join(str(d.get("id")) for d in decls))
            for decl in decls:
                if lifecycle.is_shutting_down():
                    return
                run_declared_import(kernel, decl)
        except Exception as exc:            # never break boot
            # Same reason as `import_failed` above, and worse: this one takes the whole unit's
            # thread with it, so every declared import after it silently does not happen.
            logger.warning("[source.bootstrap] skipped reason=%s detail=%s", SKIP_UNIT_FAILED,
                           exc, exc_info=True)

    import threading
    threading.Thread(target=_run, name="source-bootstrap", daemon=True).start()

