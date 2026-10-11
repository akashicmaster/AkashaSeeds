# T0 Template Candidate Record — `learning`

*Draft, ratified when Phase 0 is accepted. Source: `docs/design/reference-templates-and-profiles.md` §1–§2; written for the thesaurus line's origin, with no thesaurus-only material in the shape.*

**Candidate ID:** T0-learning

**Title:** Learning bench — dataset → features → train → evaluate → promote, with sweeps

**Domain profiles:** private_lab

**User roles:** researcher (the bench's client, idset `researcher`), chairman, scribe; no guest line

**Problem:** Train and compare small learners on a frozen corpus, reproducibly, and promote a model only on a recorded evaluation.

**Source types:** frozen source pools (`source:pool:<name>:v<n>`: a checklist/label table, an image pool), a bundled model binary (`model:<name>`) for feature extraction

**Smallest semantic unit:** one observation on the bench recorder (a feature run, a training run, an evaluation row), each with a bench coordinate

**Entities:** dataset binding, feature space, run (branch × mode), model version (content-named generation), evaluation frame, sweep condition

**Claims / Observations / Interpretations:** observations: runs and metrics; claims: a promotion (a person's or a rule's act with the evaluation it cites); interpretations: none written by the template

**Temporal requirements:** bench clock (`cronon:wb:<bench>:c<n>`) orders runs; wall clock `at` on each row; a model version is immutable once published

**Competing perspectives:** alternative heads / feature spaces under one sweep, ranked per frame, never merged across frames

**Rights / consent / disclosure:** private by profile (`space.public` locked); the pools' licences travel with the pool; no publication effect

**Workflow:** `plants_t1…t7`: dataset.bind → feature.extract/run/execute/seal → train → evaluate → promote; a sweep grid expands to conditions (`sweeps/heads1.json`)

**External effects:** none (record). Weights and feature files are written under the cell's data directory

**Outputs:** model versions, evaluation rows, ranked results (`lens.rank`), the run list (`learning.runs`)

**Observation coordinates:** bench coordinate per step; branch and mode on every run

**Evaluation frames:** per test set; figures from different frames are never ranked together

**General CM dependencies:** `vision_lab` (observers, features), `learned_head`, `sweep`, `lens`, `source` (pools); reserved: `bench` lifecycle

**Ontology patterns:** `set:wb:<bench>:runs`, `…:evaluations`, `cond:` Sets per sweep branch; PLANTS packs are thesaurus-only and are NOT part of the template

**Operation Profile:** `private_lab` (manual or daily; `best_effort`; `effect: record`)

**Existing A25 base template:** itself

**Replay requirement:** a run is reproducible from its recorded inputs (pool version, feature space, head, seed); a version `@<sha8>` pins weights

**Degradation mode:** with no model binary and no network the template stands by on `requires` (`model:…`/pool not ready); the mock observer still runs the pipeline shape

**Reference dataset:** thesaurus origin: the PLANTS lab (`plants:vision20`, images pool). The seeds sample is chosen in stage S

**Success criteria:** the seven workflows run to `DONE`; a re-run on the same pool and seed gives the same evaluation; a promotion cites an evaluation row

**Known limitations:** features/training are CPU-bound and long (`max_wall_s: 14400`); heavy native libraries are optional

**Open questions:** whether promotion becomes the `trainer` template's approval step (see `trainer`)

**Current files:** `app/config/workbench/workloads/plants_vision.json`; `config/workbench/plants-vision/templates/plants_t1…t7.ak`; `app/config/workbench/plants-vision/sweeps/heads1.json`; `concepts/bench_learning.py`, `vision_lab.py`

**Declaration fields used:** `profile`, `bench`, `bench_kind`, `bench_public`, `workflow`, `workflows`, `sweeps`, `idset: researcher`, `requires`, `grants`, `trigger`, `duty`, `effect`, `appetite`, `budget`, `pins`, `space`, `roles`, `moderator`

**Gate facts and effect:** declared · armed · source_ready (the `requires` pools and models) · headroom; effect `record`; no effectful capability

**What it gets wrong today:** the bench kind's ops were `bench.*` until 10-02 (now `learning.*`); the declaration restates profile defaults in full until the loader lands (W2)
