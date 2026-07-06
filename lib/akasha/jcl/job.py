"""JCL Job — data model and status constants."""
import uuid
import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

PENDING   = "PENDING"
RUNNING   = "RUNNING"
DONE      = "DONE"
FAILED    = "FAILED"
CANCELLED = "CANCELLED"

# Job classes — the write-transaction taxonomy (docs/for-llm/orchestration-
# architecture.md, Appendix C). The class is the primary scheduling axis: it
# (not the caller) decides priority, atomicity, and interruptibility.
CLASS_CONVERSATION = "conversation"  # Class 1 — perceived-immediate, atomic bundle
CLASS_BATCH_ATOM   = "batch_atom"    # Class 2 — consistent as a set, not real-time
CLASS_LINK         = "link"          # Class 3 — eventual, interruptible, resumable
CLASS_MAINTENANCE  = "maintenance"   # Class 4 — idle housekeeping


@dataclass
class JCLStep:
    method: str                               # kernel RPC method
    params: Dict[str, Any] = field(default_factory=dict)
    cmd: str = ""                             # original command string (audit trail)


@dataclass
class JCLJob:
    job_id: str    = field(default_factory=lambda: f"job:{uuid.uuid4().hex[:12]}")
    owner: str     = ""        # client_id / session_token
    label: str     = ""        # human-readable name (filename, etc.)
    steps: List[JCLStep] = field(default_factory=list)
    status: str    = PENDING
    tx_id: Optional[str]   = None  # Harmonia workspace tx_id
    submitted_at: float    = field(default_factory=time.time)
    completed_at: Optional[float] = None
    error: Optional[str]   = None
    step_done: int = 0
    # When False: step errors are recorded in step_errors but processing continues.
    # Suitable for bulk ontology loads where partial success is acceptable.
    fail_fast: bool = True
    step_errors: List[str] = field(default_factory=list)
    # Write-transaction class (see Appendix C). Default LINK = background: an
    # unclassified job is treated as the lowest interactive-safe tier so it can
    # never accidentally jump ahead of a conversation job.
    job_class: str = CLASS_LINK
    # Scalar priority the executor orders by (lower = scheduled first). This is the
    # PROJECTION of the job's scheduling axes, computed once at admission by
    # Harmonia (priority_of); the executor never re-derives it. Default = LINK.
    priority: int = 2

    # ── Slice 3 — step-granular scheduling (orchestration-architecture.md E.1–E.3) ──
    # PERT dependency edges: job_ids that must reach DONE before this job is eligible.
    # If any listed job FAILs/CANCELs, this job is cancelled (failure cascade).
    depends_on: List[str] = field(default_factory=list)
    # Bounded per-step retry budget for *idempotent* classes (batch/link/maintenance).
    # One-shot conversation jobs never retry. 0 = no retry (current behaviour).
    max_retries: int = 0
    # Soft per-job wall-clock budget (seconds). Checked at unit boundaries — a step
    # already running is never hard-preempted (single-worker determinism); an
    # over-budget interruptible job simply yields sooner. None = no budget.
    timeout_s: Optional[float] = None

    # Runtime resume state (NOT part of the submitted spec — set by the executor as a
    # job yields at a unit boundary and is re-queued to resume where it left off).
    cursor: int = 0                       # next step index to run
    last_key: Optional[str] = None        # $it carried across yields
    retries_used: int = 0                 # retries consumed so far
    started_at: Optional[float] = None    # first RUNNING transition (for timeout_s)

    @property
    def step_count(self) -> int:
        return len(self.steps)
