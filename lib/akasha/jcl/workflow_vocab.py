"""
Workflow vocabulary — the reserved conventions for representing a workflow AS a
graph of atoms (the "reception layer" for CSL→JCL orchestration).

This module enshrines the naming so the *static* atom graph can be re-read as a
*dynamic* execution model. It is intentionally small: the minimal pre-launch cut
stores a workflow as one executable atom whose body is a CSL script, and runs it as
one bounded JCL job (see kernel `workflow.run`). The `ref:*` relations below are
RESERVED now so the post-launch work — projecting a workflow into per-step atoms
wired by a dependency/condition DAG that Harmonia *traverses* (the homoiconic job
graph described in `jcl/write_queue.py`) — slots in without renaming anything.

Homoiconic model (target, incremental):
  - An atom carrying `SCOPE_EXECUTABLE` is an executable workflow or step.
  - `REL_THEREFORE` (A → B) declares "B runs after A" — the order-pair / PERT edge.
    `REL_BECAUSE` is its inverse (B ← A), for traversing provenance.
  - `REL_IF` gates a step on a declarative condition (evaluated at eligibility time
    by Harmonia — NOT an inline branch; CSL stays declarative, holds no flow/state).
  - A named workflow definition is aliased `WF_ALIAS_PREFIX + name` (e.g. `wf:enrich`).
  - Control emerges from traversing these links + the Agent concept model holding
    state — never from procedural constructs inside CSL. (See the CSL declarative
    policy: dependencies / conditions / order-pairs only.)
"""

# An atom with this scope is an executable workflow or step (homoiconic job graph).
SCOPE_EXECUTABLE = "scope:job:executable"

# DAG relations (reserved now; used by the post-launch step-granular projection).
REL_THEREFORE = "ref:therefore"   # A → B : B is eligible after A completes
REL_BECAUSE   = "ref:because"     # inverse of therefore (provenance direction)
REL_IF        = "ref:if"          # declarative condition gate on a step

# Reserved alias prefix for named workflow definitions (protected like `ws:`).
WF_ALIAS_PREFIX = "wf:"

# Atom meta `type` markers.
META_WORKFLOW = "job:workflow"    # the definition atom (body = CSL source)
META_STEP     = "job:step"        # a projected step atom (post-launch)
