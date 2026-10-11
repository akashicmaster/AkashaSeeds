# T0 Template Candidate Record — `trainer`

*Draft, ratified when Phase 0 is accepted. Source: `docs/design/reference-templates-and-profiles.md` §1–§2; written for the thesaurus line's origin, with no thesaurus-only material in the shape.*

**Candidate ID:** T0-trainer

**Title:** Model Trainer — observe → diagnose → propose → approve → adapt → observe again

**Domain profiles:** private_lab

**User roles:** researcher, approver (a person under the gate), chairman, scribe

**Problem:** Improve a model in a loop whose every change is proposed as a claim and approved by a person before it trains.

**Source types:** observation rows from an observatory, training data pools, a model under training

**Smallest semantic unit:** one proposal: a claim naming a diagnosis and the change it asks for

**Entities:** diagnosis, proposal (claim), approval (a person's act), training run, model version, comparison

**Claims / Observations / Interpretations:** a proposal is a claim; its approval is an act under the gate; the comparison after adaptation is an observation

**Temporal requirements:** chronon-ordered loop; each iteration observes again and compares with the previous

**Competing perspectives:** alternative proposals for one diagnosis are ranked, not merged

**Rights / consent / disclosure:** no training or adaptation without a recorded approval; the approver is named on the row

**Workflow:** observe → diagnose → propose (a claim) → approve (a person) → train/adapt → observe again → compare

**External effects:** training/adapting a model is an effectful capability, admitted only after approval

**Outputs:** proposals, approvals, model versions, before/after comparisons

**Observation coordinates:** chronon of each observation; the approval's coordinate links proposal to run

**Evaluation frames:** the observatory's Observation Profile

**General CM dependencies:** the observatory template, `learning` ops, the approval act (gate)

**Ontology patterns:** claims and acts per the thought-lab frame (A6)

**Operation Profile:** `private_lab`

**Existing A25 base template:** itself

**Replay requirement:** each approved change replays from its proposal, approval and inputs

**Degradation mode:** with no model the loop can still record diagnoses and proposals for a person to act on

**Reference dataset:** PLANTS (via the observatory); the seeds sample is chosen in stage S

**Success criteria:** no training row exists without an approval row; a before/after comparison exists for every adaptation

**Known limitations:** first version proposes by simple diagnosis only; no curriculum generation

**Open questions:** how `learning.promote` relates to the approval step

**Current files:** none

**Declaration fields used:** `profile`, `observe`, `idset: researcher`, `requires`, `trigger`, `duty`, `effect`, `grants` (the approval line), `budget`

**Gate facts and effect:** declared · armed · source_ready · headroom; effect `record`; training is an effectful capability behind an approval
