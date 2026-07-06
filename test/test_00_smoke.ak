# =============================================================================
# AKASHA Test Suite 00 — JCL Smoke Test
# =============================================================================
# PURPOSE: Verify that the JCL batch execution system is working correctly.
#          This is the first script to run when setting up a new Akasha instance.
#          If this passes, the core write/link/set pipeline is healthy.
#
# HOW TO RUN:
#   In the AKASHA shell:  run test/test_00_smoke.ak
#   The shell returns a job_id immediately. Wait for DONE.
#
# HOW TO VERIFY (after job completes):
#   job.stat <job_id>          → status: DONE, step_done: 9/9
#   ls 9                       → jcl:smoke:* atoms visible near the top
#   ln.ls jcl:smoke:alpha      → one outgoing link to jcl:smoke:beta
#   tree jcl:smoke:alpha 3     → 3-node chain alpha → beta → gamma
#   s.ls test:smoke            → 3 members
# =============================================================================

# ── Step 1: Write three test atoms ───────────────────────────────────────────
w "JCL Smoke Test — node alpha: the origin"
al $0 "jcl:smoke:alpha"

w "JCL Smoke Test — node beta: the middle"
al $0 "jcl:smoke:beta"

w "JCL Smoke Test — node gamma: the terminus"
al $0 "jcl:smoke:gamma"

# ── Step 2: Chain them with directed links ────────────────────────────────────
ln jcl:smoke:alpha jcl:smoke:beta @followed_by
ln jcl:smoke:beta  jcl:smoke:gamma @followed_by

# ── Step 3: Metadata ─────────────────────────────────────────────────────────
meta jcl:smoke:alpha test_run "smoke_00"

# ── Step 4: Set membership ────────────────────────────────────────────────────
s.add test:smoke jcl:smoke:alpha
s.add test:smoke jcl:smoke:beta
s.add test:smoke jcl:smoke:gamma
