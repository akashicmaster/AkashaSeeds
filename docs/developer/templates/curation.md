# T0 Template Candidate Record — `curation`

*Draft, ratified when Phase 0 is accepted. Source: `docs/design/reference-templates-and-profiles.md` §1–§2; written for the thesaurus line's origin, with no thesaurus-only material in the shape.*

**Candidate ID:** T0-curation

**Title:** Curation — image corpus → curation layers

**Domain profiles:** private_lab

**User roles:** researcher, curator (member), chairman, scribe

**Problem:** Look at an image corpus through several machine observers and a human curator, keeping each view separate and the source untouched.

**Source types:** an image corpus referenced by URL or local directory (images are never stored — an `image_ref` only), an open-access record set

**Smallest semantic unit:** one observation of one image by one observer (success and failure both recorded)

**Entities:** image reference, observer (immutable model identity), observation, detection, feature, derived Set / cluster, curation layer

**Claims / Observations / Interpretations:** observations are machine output; a layer or a cluster is a derived, mechanically named Set; interpretation is a later, separate act

**Temporal requirements:** runs are reproducible batches; derived Sets carry the run they came from

**Competing perspectives:** different observers yield different structures; disagreement is divergence between observer spaces

**Rights / consent / disclosure:** open-access licences recorded per record (CC0 for CMA); no image binaries are redistributed

**Workflow:** source.scan / pool → vlab.run (observers) → vlab.pca / cluster / neighbors / crossobs → curation layers (`curation.*`)

**External effects:** none (record); image fetch is by reference at view time

**Outputs:** derived Sets, cluster projections, a views read across observers, curation paths

**Observation coordinates:** bench coordinate per run; observer identity and feature space on every observation

**Evaluation frames:** per observer space; thresholds carry their metadata

**General CM dependencies:** `vision_lab`, `curation`, `source`, `lens`; reserved: `bench`

**Ontology patterns:** `vis:` observers and families (`app/ontology/visual_curation`), derived Sets (`set:analysis:cluster:*`)

**Operation Profile:** `private_lab`

**Existing A25 base template:** itself

**Replay requirement:** a run records pool, observer version and parameters; the same inputs reproduce the same Sets

**Degradation mode:** optional observers degrade to the lightweight NumPy/Pillow set and then to a mock; nothing breaks when a model is absent

**Reference dataset:** thesaurus origin: `app/ontology/blvh`, `app/ontology/visual_curation`, the CMA corpus. The seeds sample is chosen in stage S

**Success criteria:** every image has an observation or a recorded failure; the source is never mutated; two observers' views can be compared

**Known limitations:** native model libraries are heavy and optional

**Open questions:** how the template relates to `observatory` (observation of a target) — curation observes a corpus

**Current files:** `app/ontology/blvh/`, `app/ontology/visual_curation/`; `app/config/source/cma_visual_curation.json`, `app/config/source/bl_real.json`; the `curation.*` model

**Declaration fields used:** none yet — a declaration would use `profile`, `bench`, `bench_kind`, `idset: researcher`, `requires` (pools, models), `trigger`, `duty`, `effect: record`, `budget`, `workflows`

**Gate facts and effect:** declared · armed · source_ready (pools) · headroom; effect `record`

**What it gets wrong today:** data and model exist but there is no declaration, so nothing drives it
