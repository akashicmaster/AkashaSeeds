# =============================================================================
# AKASHA Test Suite 10 — Workbench end-to-end (world · bench · society · workflow)
# =============================================================================
# PURPOSE: Exercise the whole world-model foundation on one small "sandbox" bench —
#          the test bench that stands in for a real research model, and the seeds
#          series' quick-start example of the world model.
#
# HOW TO RUN: type these at the akasha> prompt on a fresh cell (they use group /
#   society / bench / workflow ops that are LOCAL-console commands, not a JCL batch,
#   so run them interactively rather than `run test/test_10_workbench.ak`). A second
#   run is idempotent (every create is create-if-absent; the axis records do not
#   duplicate).
#
# HOW TO VERIFY (after the sequence):
#   world.axis                      → society.formed, society.connected, bench.created
#                                     and ONE sync record (from wf.dispatch), each with a
#                                     wall-clock stamp
#   source.stream wb:sandbox space=group:bench-sandbox
#                                   → every op below in observation order (the rewind is
#                                     an observation, not an erasure)
#   bench.grants name=sandbox       → the five operator grants + decide
# =============================================================================

# ── the shared world (idempotent; normally created at boot) ──────────────────
world.genesis

# ── a group + a society bound to a world + a research bench ───────────────────
grp.new group_id=bench-sandbox admin_id=admin
bench.new name=sandbox kind=research group=bench-sandbox
society.new group=bench-sandbox name=sandbox world=default bench=sandbox kind=cowork identity=locked

# ── roles: the moderator is self (admin's cast); the scribe keeps the record ──
# (admit a cast into the society BEFORE giving it a role — a role attaches to an agent)
cast.new name=Chair
society.admit group=bench-sandbox name=sandbox cast=Chair
society.moderator group=bench-sandbox name=sandbox cast=Chair
cast.new name=Scribe
society.admit group=bench-sandbox name=sandbox cast=Scribe
society.responsible group=bench-sandbox name=sandbox cast=Scribe kind=scribe

# ── grants: the moderator holds every operator family + decide ────────────────
society.responsible group=bench-sandbox name=sandbox cast=Chair kind=operator:source
society.responsible group=bench-sandbox name=sandbox cast=Chair kind=operator:hypothesis
society.responsible group=bench-sandbox name=sandbox cast=Chair kind=operator:evidence
society.responsible group=bench-sandbox name=sandbox cast=Chair kind=operator:note
society.responsible group=bench-sandbox name=sandbox cast=Chair kind=decide

# ── a source referenced into the bench (never copied) ─────────────────────────
source.register provider=sandbox name=sample-1 uri=sample:1 rights=CC0 space=group:bench-sandbox
source.acquire source=sample-1 rule=inline text="Paragraph one. Paragraph two restates it." space=group:bench-sandbox
source.pool.create name=sandbox-pool source=sample-1 space=group:bench-sandbox
research.source.bind name=sandbox pool=sandbox-pool

# ── a hypothesis, evidence, a note — each teed as one observation ─────────────
research.hyp.new name=sandbox text="paragraph 2 restates paragraph 1"
research.note name=sandbox text="first pass"

# ── a workflow: script ahead of the cursor, log behind it ─────────────────────
wf.new bench=sandbox
wf.write bench=sandbox pos=1 entry="read sample-1"
wf.write bench=sandbox pos=2 entry="state hypothesis 1"
wf.advance bench=sandbox n=2
wf.rewind bench=sandbox pos=1
wf.branch bench=sandbox from=1 name=alt

# ── dispatch a run to the world (the sync event) — needs decide ───────────────
wf.dispatch bench=sandbox branch=main from=1 to=2

# ── read the world axis + the bench's observation stream ──────────────────────
world.axis
source.stream wb:sandbox space=group:bench-sandbox
bench.grants name=sandbox
