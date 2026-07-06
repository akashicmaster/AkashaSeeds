"""
JCL Security Validator — enforces kernel method allowlist for submitted steps.

Only kernel RPC methods that read/write the cognitive graph are permitted.
OS-level commands, arbitrary imports, and recursion (job.submit inside JCL)
are structurally impossible here — the worker only calls kernel.dispatch().
"""
from typing import List, Tuple
from lib.akasha.jcl.job import JCLStep

# Whitelist of methods that JCL steps may invoke.
# job.* and sys.monitor are excluded to prevent recursion / privilege escalation.
ALLOWED_METHODS: frozenset = frozenset({
    # Memory
    "kernel.memory.write", "kernel.memory.define",
    "kernel.memory.read",  "kernel.memory.drop",
    "kernel.memory.link",
    # Links
    "link.list", "link.reinforce",
    # Meta & Aliases
    "meta.set",
    "kernel.identity.alias",
    "kernel.identity.alias.list",
    "kernel.identity.alias.find",
    # Exploration
    "explore", "sys.tree",
    # Dive
    "dive.look", "dive.out",
    # Sets
    "set.add", "set.rm", "set.ls", "set.clear", "set.op",
    # Notes
    "note.new", "note.add",
    # Log
    "log.new", "log.checkpoint", "log.annotate", "log.read",
    # Whiteboard
    "wb.new", "wb.pin", "wb.unpin", "wb.focus", "wb.ls", "wb.show",
    # Cross
    "sys.cross.query", "sys.cross.axes",
    # Associate
    "kernel.associate", "associate.unwritten",
    # Scope
    "sys.scope.set", "sys.scope.get", "sys.scope.reset",
    # Contexa
    "contexa.fetch",
    # Sys (read-only sys ops)
    "sys.history", "sys.ls",
    # Jataka
    "jataka.dream",
})


def validate_steps(steps: List[JCLStep]) -> Tuple[bool, str]:
    """
    Check every step against the allowlist.
    Returns (True, "") on success, (False, error_message) on first violation.
    """
    for i, step in enumerate(steps):
        if step.method not in ALLOWED_METHODS:
            return False, (
                f"Step {i + 1}: method '{step.method}' is not permitted in JCL. "
                f"Only kernel graph operations are allowed."
            )
    return True, ""
