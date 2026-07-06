"""
Harmonia Engine — Arbitration and Orchestration Layer.

"Harmonia (Harmony)" is named after the goddess of harmony in Greek mythology, and is
designed with arbitration between competing jobs as its core purpose.

## Current Role

- Plugin orchestration: execution management of NLP / Weaver / Tensor / Jataka
- Workspace transaction: begin → execute_with_evidence → commit / rollback
- CostLedger: recording execution time, API tokens, and cost

## Target Role (Harmonia as Process-Level Scheduler)

Harmonia is ultimately intended to become the job scheduler for the entire Akasha process,
handling all four of the following phases:

### Phase 1 — Pre-admission
Before the `submit()` call to the queue, determines the nature of the job and assigns
a priority. Determination criteria:
- Job type (operator command / user write / background LLM processing / maintenance)
- Estimated processing time (described below)
- Completion state of dependent jobs
- Current queue load and estimated wait time

### Phase 2 — Queue management
- Reorder jobs within WriteQueue by priority (convert to PriorityQueue)
- Reposition when an operator manually changes a job's priority
- Priority model:
    HIGH   — session management and operator commands (absolute priority)
    NORMAL — user w / ln / set operations (interactive response)
    LOW    — ontology loading, LLM batch processing, exports
    IDLE   — periodic maintenance (index optimization, WAL checkpoint, etc.)

### Phase 3 — Mid-execution arbitration
Monitors running jobs and makes the following decisions:
- **Timeout handling**: if the time limit is exceeded, determines between two options:
    a. Skip + Report: abort the job and notify the owner of the timeout.
       → Suitable for one-shot operations (user requests, etc.).
    b. Requeue for Retry: reattach the job to the end of the queue and retry.
       → Suitable for idempotent background processing (maintenance, exports, etc.).
  The choice is determined by the job's `fail_fast` flag and `max_retries` setting.
- **Retry limit**: jobs that exceed the maximum retry count are recorded as FAILED.
- **Dependency chain**: if a job becomes FAILED, all subsequent jobs that depend on
  it are cancelled in a cascade.

### Phase 4 — Post-completion
- Record job results (DONE / FAILED / CANCELLED)
- Update the state of downstream jobs (dependency resolution)
- Deliver events to subscribers
- CostLedger aggregation (tracking processing time and cost)

## Pre-execution Estimation of Processing Time

At enterprise scale, multiple background LLM jobs run continuously.
Harmonia must estimate processing time at job submission and reflect it in scheduling:
- Ontology loading: atom count × known average write time
- LLM inference batch: token count × per-model throughput history
- Maintenance jobs: DB size (pages) × historical performance data

Estimates improve in accuracy by learning from CostLedger history.

## Background Maintenance Jobs

As the ontology grows large, the following periodic maintenance becomes necessary:
- WAL checkpoint (periodic DB file compaction)
- Orphaned Atom detection (detecting and reporting ghost nodes without links)
- Index optimization (statistics updates for collections / chunk_access)
- Scope consistency check (consistency verification of access control)

All of these are registered in the queue at IDLE priority and do not interfere with user
operations at all.

## Current Implementation State

Currently HarmoniaEngine handles only transaction management and plugin execution.
Implementation order for scheduling features:
1. (Current) Block writes in WriteQueue with the `ontology_loading` flag
2. (Next) Convert WriteQueue to PriorityQueue; add `submit(priority=NORMAL)`
3. (After that) Harmonia determines and assigns priority before `submit()` is called
4. (Future) Harmonia manages timeout monitoring, retry decisions, and maintenance job registration
"""

import time
import json
import logging
import traceback
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Callable

logger = logging.getLogger("Harmonia.Engine")

# Optional import for backward compatibility or direct type hinting
try:
    from lib.harmonia.service import HarmoniaService
except ImportError:
    pass

@dataclass
class CostLedger:
    """
    Performance and resource audit trail.
    Tracks execution time and computing costs (e.g., API tokens, memory usage)
    for a specific operation or plugin execution.
    """
    start_time: float = 0.0
    elapsed_ms: float = 0.0
    api_tokens: int = 0
    total_cost_usd: float = 0.0
    status: str = "PENDING"

    def start(self):
        """Initializes the timer and sets the status to RUNNING."""
        self.start_time = time.time()
        self.status = "RUNNING"

    def stop(self, status: str = "SUCCESS"):
        """Calculates the elapsed time and records the final execution status."""
        self.elapsed_ms = (time.time() - self.start_time) * 1000
        self.status = status

@dataclass
class ActionNode:
    """
    Workflow execution unit (Action Atom).
    Defines a single processing step, including the execution plugin, 
    I/O markers, and a dedicated ledger for performance tracking.
    """
    action_id: str
    executor: str
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    params: Dict[str, Any] = field(default_factory=dict)
    ledger: CostLedger = field(default_factory=CostLedger)

@dataclass
class HarmoniaTransaction:
    """Data class holding the deterministic state of an active workspace transaction."""
    tx_id: str
    name: str
    start_time: float
    status: str = "active" # active, committed, rolled_back
    # When True, every graph write on the owning thread is recorded into this tx's
    # tracking set (jcl/workspace_context), making the unit reversible: rollback
    # drops the tracked keys, commit releases them. Untracked = legacy behaviour.
    tracked: bool = False

class HarmoniaEngine:
    """
    Akasha's orchestration foundation. Currently handles plugin execution and workspace
    transactions, but will ultimately become the process-level job scheduler.

    See the module docstring for full design intent.
    """
    def __init__(self):
        self._plugins: Dict[str, Callable] = {}
        # Tracks live transactional workspaces to prevent state corruption
        self._active_workspaces: Dict[str, HarmoniaTransaction] = {}
        # JCL executor — Harmonia's initiator (see docstring Phase 1-4). Attached at
        # boot by the kernel; Harmonia owns job submission from here on. JCL is
        # subordinate to Harmonia, not a sibling of the kernel.
        self._jcl = None
        logger.debug("[HarmoniaEngine] Motor Cortex initialized.")

    # =========================================================================
    # Job admission — the single route for background/memory-mutating jobs
    # =========================================================================

    def attach_jcl(self, jcl_worker) -> None:
        """Mount the JCL executor as Harmonia's initiator (called once at boot)."""
        self._jcl = jcl_worker

    @property
    def jcl(self):
        """The JCL executor Harmonia drives (None if unavailable)."""
        return self._jcl

    def submit_job(self, job, job_class: str = None):
        """
        Single admission point for JCL jobs. All background / memory-mutating work
        enters here so Harmonia — not the kernel — owns scheduling.

        Admission assigns the job's write-transaction CLASS (Appendix C taxonomy),
        which is the primary scheduling axis. Priority is a *projection* over the
        scheduling axes (today: class only — see priority_of); more axes (owner,
        cost, deadline) can be added later without changing callers, because memory
        is modelled as a multi-dimensional tensor.

        Phase 1 pre-admission and Phase 2 priority ordering both hook in here. The
        class is recorded and its priority computed at admission, and the executor
        HONOURS that projection: the JCL worker queue and the WriteQueue are both
        priority queues (slice 3), so higher-priority work is scheduled first — a
        single worker still runs one unit at a time (priority changes ORDER, never
        parallelism). Returns the submitted job, or None if no executor is attached.
        """
        if self._jcl is None:
            return None
        if job_class is not None:
            job.job_class = job_class
        # Project the scheduling axes onto the scalar the executor orders by.
        # Done here, once, at admission — the executor never re-derives it.
        job.priority = self.priority_of(job.job_class)
        return self._jcl.submit(job)

    @staticmethod
    def priority_of(job_class: str) -> int:
        """Project a job class onto a scalar priority (lower = scheduled first).

        This is the one place the class→priority mapping lives. When a second axis
        (owner/session-type, cost, deadline) is added, this becomes a projection
        over several axes rather than a single lookup — callers do not change.
        """
        from lib.akasha.jcl.job import (CLASS_CONVERSATION, CLASS_BATCH_ATOM,
                                        CLASS_LINK, CLASS_MAINTENANCE)
        return {
            CLASS_CONVERSATION: 0,   # HIGH  — perceived-immediate
            CLASS_BATCH_ATOM:   1,   # NORMAL — consistent as a set
            CLASS_LINK:         2,   # LOW   — eventual, resumable
            CLASS_MAINTENANCE:  3,   # IDLE  — housekeeping
        }.get(job_class, 2)

    def register_plugin(self, executor_name: str, func: Callable):
        """Registers a callable function or object as an executable plugin."""
        self._plugins[executor_name] = func
        logger.info(f"[Harmonia] Plugin mounted: '{executor_name}'")

    def execute_step(self, step: ActionNode, context_data: Any, **kwargs) -> Any:
        """
        Executes a single action node (plugin) against the provided context data,
        tracking performance metrics inside the ActionNode's CostLedger.
        """
        step.ledger.start()
        try:
            if step.executor not in self._plugins:
                raise ValueError(f"Executor plugin '{step.executor}' not found in registry.")
            
            plugin_func = self._plugins[step.executor]
            merged_params = {**step.params, **kwargs}
            
            result = plugin_func(context_data, **merged_params)
            
            step.ledger.stop("SUCCESS")
            return result
            
        except Exception as e:
            error_trace = traceback.format_exc()
            logger.error(f"[Harmonia] Plugin Execution Failed [{step.executor}]:\n{error_trace}")
            
            step.ledger.stop(f"FAILED: {str(e)}")
            return {"status": "error", "error": f"Execution Error [{step.executor}]: {str(e)}"}

    def list_executors(self) -> List[str]:
        """Returns a list of all currently registered plugin executors."""
        return list(self._plugins.keys())

    # =========================================================================
    # Workspace & Transaction Management
    # =========================================================================

    def begin_workspace(self, cortex: Any, label: str, tracked: bool = False,
                        evidence: bool = True, priority: int = 1) -> str:
        """
        Starts a new atomic Workspace transaction and records the origin of
        evidence as an un-mutable Atom.

        tracked=True makes the unit *reversible*: from here until commit/rollback,
        every graph write this thread's engine commits is recorded into the tx's
        tracking set (via jcl/workspace_context), so rollback drops exactly those
        keys. The evidence atom below is written BEFORE the context is activated, so
        it is never rolled back (audit trail survives a rollback).

        evidence=False skips the origin atom — used for the lightweight per-turn
        conversation workspace, where the atoms of the bundle (and JCL/audit logs)
        are the record and an extra evidence write per keystroke-turn would only
        add latency to the perceived-immediate critical path.

        priority is the projection Harmonia computed at admission (0=HIGH
        conversation .. 3=IDLE). It is carried on the workspace-presence stack and
        read by the WriteQueue so this workspace's writes are ordered at the single
        serialization point — interactive ahead of background — without any lock.
        """
        tx_id = f"ws:{label}:{int(time.time() * 1000)}"

        # Mark workspace presence on this thread for the single-route guard. Done
        # BEFORE the evidence write so that write (and every write until commit/
        # rollback) counts as orchestrated — tracked or not. Tracking (key recording
        # for rollback) is a separate, tracked-only concern activated further down.
        from lib.akasha.jcl import workspace_context as _wctx
        _wctx.enter_workspace(priority)

        # Sprout a system-level evidence Atom to track the history of this transaction
        if evidence:
            meta = {
                "type": "sys:workspace_info",
                "label": label,
                "status": "active",
                "start_time": time.time()
            }

            cortex.put_chunk(
                content=f"Workspace Execution Origin: {label}",
                meta=meta,
                author="system.harmonia",
                scopes=["scope:sys:universal", "view:public"]
            )

        self._active_workspaces[tx_id] = HarmoniaTransaction(
            tx_id=tx_id, name=label, start_time=time.time(), tracked=tracked
        )

        if tracked:
            # Activate AFTER the evidence write so evidence is not itself tracked.
            from lib.akasha.jcl import workspace_context as _wctx
            _wctx.begin(tx_id, cortex)

        logger.debug(f"[Harmonia] Workspace [{tx_id}] opened (tracked=%s)." % tracked)
        return tx_id

    def execute_with_evidence(self, cortex: Any, tx_id: str, executor: str, input_data: Any, **params) -> Dict[str, Any]:
        """
        Executes a plugin while recording absolute evidence and cost (Ledger), 
        sprouting the intermediate results as 'pending' atoms tied to the Workspace.
        """
        if tx_id not in self._active_workspaces:
            raise ValueError(f"Invalid or expired Workspace ID: {tx_id}")
            
        # 1. Record pre-execution action evidence
        # Strip non-serializable objects from params before storing in meta
        safe_params = {k: v for k, v in params.items() if isinstance(v, (str, int, float, bool, type(None)))}
        evidence_key = cortex.put_chunk(
            content=f"Action Trace: {executor} within {tx_id}",
            meta={
                "type": "sys:action_evidence",
                "tx_id": tx_id,
                "executor": executor,
                "params": safe_params
            },
            author="system.harmonia"
        )

        # 2. Execute plugin (including Ledger tracking)
        step = ActionNode(action_id=f"step:{int(time.time()*1000)}", executor=executor, params=params)
        result = self.execute_step(step, input_data)
        
        # Bail out cleanly if the plugin failed natively
        if isinstance(result, dict) and result.get("status") == "error":
            return {"status": "error", "evidence_key": evidence_key, "error": result.get("error")}

        # 3. Temporary registration of results (Pending Atoms)
        nodes_created = []
        items = result if isinstance(result, list) else [result]
        
        for item in items:
            meta = {
                "status": "pending",
                "tx_id": tx_id,
                "evidence_key": evidence_key
            }
            # Stringify complex objects like dictionaries to make them viable physical Atoms
            content_str = str(item) if not isinstance(item, dict) else json.dumps(item, ensure_ascii=False)
            
            # Save into the physical mesh as a pending state
            key = cortex.put_chunk(content=content_str, meta=meta, author="system.harmonia")
            
            # Map node into the transaction's subset for easy batch tracking/rollback
            cortex.add_to_set(tx_id, key)
            nodes_created.append(key)

        return {
            "status": "success", 
            "evidence_key": evidence_key, 
            "nodes": nodes_created, 
            "ledger": asdict(step.ledger),
            "raw_result": result
        }

    def commit_workspace(self, cortex: Any, tx_id: str):
        """Commit — the point of no return for a management unit.

        Two paths coexist: the legacy execute_with_evidence path crystallises any
        `pending` atoms in the tx set to verified; the tracked-workspace path (slice 1)
        simply releases the tracking set (its writes are already durable). For a
        cross-DB bundle it also clears the nucleus-side tracking set (slice 4).
        """
        if tx_id not in self._active_workspaces:
            logger.warning(f"[Harmonia] Attempted to commit unknown workspace: {tx_id}")
            return

        tx = self._active_workspaces[tx_id]

        # Legacy pending-atom path (execute_with_evidence): crystallize pending→active.
        members = cortex.get_set_members(tx_id)
        committed_count = 0
        for m in members:
            k = m["key"]
            content = m.get("content", "")
            meta = cortex.get_meta(k)
            if meta.get("status") == "pending":
                meta["status"] = "active"
                meta.pop("tx_id", None)  # Release workspace binding
                cortex.put_chunk(content=content, meta=meta, author="system.harmonia", status="verified")
                committed_count += 1

        # Release workspace presence (every workspace) and, for tracked units,
        # deactivate the tracking context and clear the tracking set. Tracked path:
        # writes are already durable; commit is the point of no return.
        from lib.akasha.jcl import workspace_context as _wctx
        _wctx.exit_workspace()
        if tx.tracked:
            _wctx.end()
            try:
                cortex.clear_set(tx_id)
            except Exception:
                pass
            # Cross-DB bundle: the proto-word footprint lives in the nucleus's
            # ws:{tx_id} set. Commit = release both stores' bookkeeping (proto-words
            # stand — they are the shared growth this bundle contributed).
            _nuc = getattr(cortex, "_nucleus", None)
            if _nuc is not None:
                try:
                    _nuc.core.clear_collection(tx_id)
                except Exception:
                    pass

        tx.status = "committed"
        logger.info(f"[Harmonia] Workspace [{tx_id}] committed. Crystallized {committed_count} nodes.")

    def rollback_workspace(self, cortex: Any, tx_id: str):
        """Reverse a management unit's writes — per-unit reversibility.

        A tracked unit (slice 1) reverses ALL keys it recorded in the tx set (they were
        written verified); the legacy execute_with_evidence path reverses only its
        `pending` atoms. Cross-DB (slice 4): the cortex writes are dropped (private,
        reversible) but the nucleus proto-words stand (shared/content-addressed,
        commit-forward) — only the nucleus tracking set is cleared.
        """
        if tx_id not in self._active_workspaces:
            return

        tx = self._active_workspaces[tx_id]

        # Release workspace presence, and for tracked units deactivate the tracking
        # context first so writes done *during* rollback (there should be none) are
        # never re-tracked.
        from lib.akasha.jcl import workspace_context as _wctx
        _wctx.exit_workspace()
        if tx.tracked:
            _wctx.end()

        members = cortex.get_set_members(tx_id)
        rollback_count = 0
        for m in members:
            k = m["key"]
            meta = cortex.get_meta(k)
            # Tracked units record verified writes → reverse ALL tracked keys.
            # Legacy (untracked) units only ever hold 'pending' atoms → reverse those.
            if tx.tracked or meta.get("status") == "pending":
                # Bypass IAM: core physical drop for internal transaction aborts.
                cortex.core.drop_chunk(k)
                rollback_count += 1

        # Purge the transaction set tracking bag
        cortex.clear_set(tx_id)

        # Cross-DB bundle: reverse the CORTEX writes (private, safe to drop) but keep
        # the nucleus proto-words — they are shared, content-addressed, and may already
        # be referenced by committed bundles, so dropping them would corrupt others.
        # Clear only the nucleus tracking set (commit-forward). This asymmetry is the
        # crux of the no-2PC cross-DB model: private data rolls back, shared growth stands.
        _nuc = getattr(cortex, "_nucleus", None)
        if _nuc is not None:
            try:
                _nuc.core.clear_collection(tx_id)
            except Exception:
                pass

        tx.status = "rolled_back"
        if rollback_count:
            logger.warning(f"[Harmonia] Workspace [{tx_id}] ROLLED BACK. "
                           f"Reversed {rollback_count} nodes (tracked={tx.tracked}).")
        else:
            logger.debug(f"[Harmonia] Workspace [{tx_id}] closed (no pending nodes to purge).")

    @staticmethod
    def reconcile_orphan_workspaces(store: Any, drop_members: bool) -> dict:
        """Boot-time crash healing (orchestration-architecture.md E.4 — slice 4).

        A tracked workspace clears its `ws:{tx_id}` tracking set on commit AND on
        rollback, so any `ws:*` set still present when a store is opened is the residue
        of a bundle whose process died mid-transaction (crash-stop 'last write only').
        Reconcile every such orphan:

          - drop_members=True  (private cortex): roll it back — drop the uncommitted
            member atoms and clear the set. The in-flight bundle is undone as if it
            never happened; every previously-committed bundle is untouched.
          - drop_members=False (shared nucleus): KEEP the members — proto-words are
            content-addressed and shared with committed bundles, so dropping them is
            unsafe; just clear the stray tracking set (commit-forward).

        Runs once when a store is opened, before it serves any request, so no live
        workspace can be mistaken for an orphan. Uses backend primitives directly
        (no composite `commit`/`put_link`), so it neither trips nor needs the guard.
        """
        core = getattr(store, "core", None)
        if core is None:
            return {"sets": 0, "atoms": 0}
        try:
            names = core.get_distinct_collection_names("ws:%")
        except Exception:
            return {"sets": 0, "atoms": 0}
        sets = 0
        atoms = 0
        for name in names:
            if drop_members:
                try:
                    members = core.get_collection_members(name)
                except Exception:
                    members = []
                for k in members:
                    try:
                        core.drop_chunk(k)
                        atoms += 1
                    except Exception:
                        pass
            try:
                core.clear_collection(name)
                sets += 1
            except Exception:
                pass
        if sets:
            logger.warning(
                "[Harmonia] Orphan scan (%s): reconciled %d crashed workspace(s), "
                "reversed %d atom(s) (drop_members=%s).",
                getattr(store, "_db_path", getattr(core, "_db_path", "?")),
                sets, atoms, drop_members)
        return {"sets": sets, "atoms": atoms}
