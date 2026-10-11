# T0 Template Candidate Record — `research`

*Draft, ratified when Phase 0 is accepted. Source: `docs/design/reference-templates-and-profiles.md` §1–§2; written for the thesaurus line's origin, with no thesaurus-only material in the shape.*

**Candidate ID:** T0-research

**Title:** Research bench — sources, hypotheses, evidence, proofs, notes

**Domain profiles:** private_lab; seminar when the digest is published

**User roles:** researcher, member (invited), chairman, scribe; guest read of the record under `seminar`

**Problem:** Keep a research argument as typed, ordered, attributable records so a conclusion can be traced to its evidence and re-composed for publication.

**Source types:** bound sources (`research.source.bind`), notes authored in the bench, cross-references to the lab's source pools

**Smallest semantic unit:** a note-family entry with provenance (type, author, society, role) recorded through the bench recorder

**Entities:** source, hypothesis, evidence, proof, note, publication set, lab (`labo:<name>`)

**Claims / Observations / Interpretations:** hypotheses are claims with a status; evidence binds a source to a hypothesis; a proof records a judgement with its basis; notes are interpretations marked as such

**Temporal requirements:** cronon-ordered history; four orderings (cronon / argument / evidence / publication) are macros over `research.note.timeline`

**Competing perspectives:** several hypotheses over one evidence set; dissent is a note, never an overwrite

**Rights / consent / disclosure:** private by default; a Publication Set is an explicit act; every public copy carries its provenance

**Workflow:** source.bind → hyp.new → evidence.bind → proof.new → note → publication.compose / present

**External effects:** none (record); `publication.present` returns a rendering, it does not post

**Outputs:** timelines, Publication Sets with `composed_from` / `published_in` links, presentation macros

**Observation coordinates:** bench coordinate per recorded entry; each carries the inline act {declared, judged, by}

**Evaluation frames:** none of its own; a hypothesis's status is the frame

**General CM dependencies:** `research` (the Labo notebook), `cronon`, `source`, `lens`; reserved: `bench`

**Ontology patterns:** `set:wb:<bench>:by:<author>`, `…:act:{declared,judged}`, Publication Sets

**Operation Profile:** `private_lab` or `seminar`

**Existing A25 base template:** itself

**Replay requirement:** history is append-only; a composition is a regeneration from the chunks, never a copy

**Degradation mode:** fully functional with no model and no network (it is a record keeper)

**Reference dataset:** thesaurus origin: the Labo research benches. The seeds sample is chosen in stage S

**Success criteria:** every conclusion resolves to evidence and sources by links; each ordering reproduces from the record

**Known limitations:** the Labo notebook (`research.*` chunk model) and the bench kind (`research.*` bench ops) share the `research` prefix; `ResearchNotebook` is the declared primary

**Open questions:** which of the two research models is the template's canonical surface

**Current files:** `config/workbench/workloads/bench_research.json` (still the legacy scaffold shape); the `research.*` Concept Model; `docs/for-llm/research-workbench-port.md`

**Declaration fields used:** `profile`, `world`, `group`, `society`, `bench`, `roles`, `participants`, `grants`, `workflows`, `sweeps`, `sources` (scaffold shape); a workload would add `idset: researcher`, `trigger`, `duty`, `effect`, `budget`

**Gate facts and effect:** declared · armed · headroom; effect `record` (`publish` only for the seminar digest)

**What it gets wrong today:** `bench_research.json` is a scaffold, not a workload: provisioned, but not driven by the one driver
