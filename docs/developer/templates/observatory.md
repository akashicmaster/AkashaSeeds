# T0 Template Candidate Record — `observatory`

*Draft, ratified when Phase 0 is accepted. Source: `docs/design/reference-templates-and-profiles.md` §1–§2; written for the thesaurus line's origin, with no thesaurus-only material in the shape.*

**Candidate ID:** T0-observatory

**Title:** Model Observatory — observe a target over chronons

**Domain profiles:** private_lab; seminar when findings are published

**User roles:** researcher, observer (plugin, with provenance), chairman, scribe

**Problem:** Watch a model or system change over time — bind a target, observe it under an Observation Profile, and read deltas, trajectories and regime changes.

**Source types:** a bound target (a model, a world, a system), stimuli, observer plugins

**Smallest semantic unit:** one observation: target, chronon, coordinate, observer, mode, condition, stimulus, state_before, response, state_after, metric, result, provenance

**Entities:** target + adapter, Observation Profile, observer, chronon, coordinate, metric, delta, trajectory, regime

**Claims / Observations / Interpretations:** observations carry the observer's mode and provenance; deltas and trajectories are derived; a regime flag is a derived claim with its thresholds

**Temporal requirements:** chronon-indexed; replay can branch from a chronon

**Competing perspectives:** several observers and modes (O0 / O1 / O2) over one target, kept separate

**Rights / consent / disclosure:** mode and observer provenance stamped on every row (method, sampling, training_writable, memory_writable, gradient_enabled, branch)

**Workflow:** bind target → Observation Profile → observe (O0/O1/O2) → chronon → compare → delta → trajectory → regime → project

**External effects:** none for O0/O1; an O2 intervention is an effectful capability under the gate

**Outputs:** observation rows, deltas, trajectories, change-points, projections

**Observation coordinates:** chronon × coordinate × metric

**Evaluation frames:** the Observation Profile (world_model, temporal, causal, source_grounding, uncertainty, spatial, affordance, recovery)

**General CM dependencies:** the platform's observation schema, observer registry and metric registry (A24); the Observation Profile concept and target adapters (application)

**Ontology patterns:** `profile.*` coordinates of the Observation Profile

**Operation Profile:** `private_lab` / `seminar` with the optional `observe` block {profile, mode, cadence, observers, thresholds}

**Existing A25 base template:** itself

**Replay requirement:** as-of reads and branching from a chronon (A5/A24)

**Degradation mode:** with no observer plugin beyond the built-in metrics the template still records and compares

**Reference dataset:** PLANTS is to be its first instance (W4); the seeds sample is chosen in stage S

**Success criteria:** PLANTS re-expressed as an observatory behaves unchanged (bind → observe → feature → train → evaluate → observe again → diff)

**Known limitations:** no SAE or mechanistic interpretability in the first version

**Open questions:** which observers ship with the template versus as plugins

**Current files:** none

**Declaration fields used:** `profile`, `observe`, `idset: researcher`, `requires`, `trigger`, `duty`, `effect`, `budget` (A24/A25)

**Gate facts and effect:** declared · armed · source_ready (the target's pools) · headroom; effect `record`; an O2 intervention is an effectful capability
