# T0 Template Candidate Record — `survey`

*Draft, ratified when Phase 0 is accepted. Source: `docs/design/reference-templates-and-profiles.md` §1–§2; written for the thesaurus line's origin, with no thesaurus-only material in the shape.*

**Candidate ID:** T0-survey

**Title:** Survey — coded survey → deliberation record

**Domain profiles:** seminar

**User roles:** researcher, member (invited), chairman, scribe; guest read of the record

**Problem:** Turn collected public feedback into an auditable deliberation: aggregate by stance, project to a concept laboratory, and post proposals and a conclusion for discussion.

**Source types:** a coded survey or consultation corpus (CSV/JSONL), pre-processed off-line into an ontology pack with the raw rows verbatim

**Smallest semantic unit:** one response, content-addressed by respondent + question

**Entities:** survey, question, respondent, response, aggregation (stance groups), clab field, society

**Claims / Observations / Interpretations:** responses are observations; stance classification is a derived, degradation-first interpretation; the conclusion is a first-class claim that never forces collapse of the conceptual world

**Temporal requirements:** batch ingest; the deliberation proceeds by society turns

**Competing perspectives:** stance groups and theoretical families are kept side by side

**Rights / consent / disclosure:** dataset provenance (DOI/version/hashes) on the source; the feed is shown publicly only with the society's public consent

**Workflow:** `delib.aggregate` → `delib.to_labo` → `delib.to_society` (`delib.pipeline` runs all three)

**External effects:** publish: the seminar digest (record-visible); no outbound channel

**Outputs:** aggregation, a clab projection, a society feed of proposals and a conclusion

**Observation coordinates:** provenance edges per stage (`sys:has_aggregation`, `delib:projects`, `delib:deliberates`)

**Evaluation frames:** per question / per stance measure

**General CM dependencies:** `survey`, `aggregation`, `clab`, `society`, `delib`, `source`

**Ontology patterns:** `set:<corpus>:<field>:<value>` coded Sets and `source:item:<corpus>:*` raw atoms (the source-data-as-ontology rule)

**Operation Profile:** `seminar`

**Existing A25 base template:** itself

**Replay requirement:** the pipeline is deterministic over the frozen pool; each stage's edge records its inputs

**Degradation mode:** keyword-lexicon stance classification with no LLM and no network

**Reference dataset:** thesaurus origin: the EU mobility 2014 consultation. The seeds sample is chosen in stage S

**Success criteria:** every stance group traces to its responses; the conclusion cites its families; a re-run reproduces the aggregation

**Known limitations:** multi-locale NLP is the floor (bigram/regex) until per-segment language-ID lands

**Open questions:** whether the digest is a daily publish (seminar default) or on demand

**Current files:** `app/config/source/mobility_eu_2014.json`, `app/config/source/corpus_policy/mobility.json`, `app/config/mobility_stance_map.json`; `concepts/delib.py`

**Declaration fields used:** none yet — a declaration would use `profile`, `bench`, `idset: researcher`, `requires` (the frozen pool), `trigger` (`every:86400s`), `effect: publish`, `space`, `roles`

**Gate facts and effect:** declared · armed · headroom; effect `publish` (the digest)

**What it gets wrong today:** data and model exist but there is no declaration
