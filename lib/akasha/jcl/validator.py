"""
JCL Security Validator — blocks privileged / recursive methods in submitted steps.

Every JCL step is re-dispatched through the normal kernel auth path as the job
owner, so a step can never do more than the owner could do interactively — the
worker only calls kernel.dispatch(); OS commands and arbitrary imports are
structurally impossible.  This validator is defense-in-depth on top of that: it
rejects a small, explicit set of methods that must never run *inside* a batch
job regardless of the owner's role, namely

  - job control      — recursion / fork-bomb (a job that submits jobs)
  - identity switch  — sys.su (elevation inside an unattended batch)
  - user/group admin — user.* / grp.* (account mutation from a batch)
  - session/auth      — session.* / auth.* / kernel.genesis_rite
  - destructive onto  — onto.reset / onto.genesis.redo / onto.scope.drop

A blocklist (not an allowlist) is used deliberately: ordinary graph and
concept-model operations (rec.*, table.*, lens*, quadrant.*, note.*, set.*,
weave, …) are the whole point of a batch job and must keep working, while new
concept models must not silently become un-runnable in JCL.
"""
from typing import List, Tuple
from lib.akasha.jcl.job import JCLStep

# Exact method names that are forbidden inside a JCL step.
_BLOCKED_METHODS: frozenset = frozenset({
    "sys.su",
    "kernel.genesis_rite",
    "auth.verify", "auth.status", "kernel.auth.verify", "kernel.auth.status",
    "onto.reset", "onto.genesis.redo", "onto.scope.drop",
})

# Any method beginning with one of these prefixes is forbidden.
_BLOCKED_PREFIXES: tuple = (
    "job.",       # recursion / fork-bomb
    "user.",      # account mutation
    "grp.",       # group mutation
    "session.",   # guest binding / session context management
    "sys.su",     # identity switch (defensive; also blocked exactly above)
)


def validate_steps(steps: List[JCLStep]) -> Tuple[bool, str]:
    """
    Reject a job if any step invokes a privileged / recursive method.
    Returns (True, "") on success, (False, error_message) on first violation.
    """
    for i, step in enumerate(steps):
        m = step.method or ""
        if m in _BLOCKED_METHODS or m.startswith(_BLOCKED_PREFIXES):
            return False, (
                f"Step {i + 1}: method '{m}' is not permitted inside a JCL job "
                f"(privileged or recursive)."
            )
    return True, ""
