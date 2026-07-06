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
        logger.debug("[HarmoniaEngine] Motor Cortex initialized.")

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

    def begin_workspace(self, cortex: Any, label: str) -> str:
        """
        Starts a new atomic Workspace transaction and records the origin of 
        evidence as an un-mutable Atom.
        """
        tx_id = f"ws:{label}:{int(time.time() * 1000)}"
        
        # Sprout a system-level evidence Atom to track the history of this transaction
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
            tx_id=tx_id, name=label, start_time=time.time()
        )
        
        logger.debug(f"[Harmonia] Workspace [{tx_id}] opened.")
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
        """
        [CRITICAL FIX APPLIED]
        Crystallizes all 'pending' Atoms in the workspace to 'active', 
        formalizing them permanently into the memory mesh.
        """
        if tx_id not in self._active_workspaces:
            logger.warning(f"[Harmonia] Attempted to commit unknown workspace: {tx_id}")
            return

        members = cortex.get_set_members(tx_id)
        committed_count = 0
        
        for m in members:
            k = m["key"]
            content = m.get("content", "")
            
            # Explicitly fetch complete metadata from the Cortex
            meta = cortex.get_meta(k)
            
            if meta.get("status") == "pending":
                meta["status"] = "active"
                meta.pop("tx_id", None) # Release workspace binding
                
                # Overwrite/finalize chunk in DB with verified status
                cortex.put_chunk(content=content, meta=meta, author="system.harmonia", status="verified")
                committed_count += 1

        self._active_workspaces[tx_id].status = "committed"
        logger.info(f"[Harmonia] Workspace [{tx_id}] committed. Crystallized {committed_count} nodes.")

    def rollback_workspace(self, cortex: Any, tx_id: str):
        """
        [CRITICAL FIX APPLIED]
        Physically purges all pending changes in the workspace, 
        effectively wiping the failed thought process without a trace.
        """
        if tx_id not in self._active_workspaces:
            return

        members = cortex.get_set_members(tx_id)
        rollback_count = 0
        
        for m in members:
            k = m["key"]
            meta = cortex.get_meta(k)
            
            if meta.get("status") == "pending":
                # Bypass IAM entirely using core physical drop for internal transaction aborts
                cortex.core.drop_chunk(k)
                rollback_count += 1
        
        # Purge the transaction set tracking bag
        cortex.clear_set(tx_id)
        
        self._active_workspaces[tx_id].status = "rolled_back"
        logger.warning(f"[Harmonia] Workspace [{tx_id}] ROLLED BACK. Purged {rollback_count} pending nodes.")
