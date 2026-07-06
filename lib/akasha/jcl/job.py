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

    @property
    def step_count(self) -> int:
        return len(self.steps)
