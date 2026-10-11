# T0 Template Candidate Record — `feed`

*Draft, ratified when Phase 0 is accepted. Source: `docs/design/reference-templates-and-profiles.md` §1–§2; written for the thesaurus line's origin, with no thesaurus-only material in the shape.*

**Candidate ID:** T0-feed

**Title:** Feed — pull → record → map

**Domain profiles:** telemetry_feed

**User roles:** telemetry (the feed's client, idset `telemetry`); guest read

**Problem:** Pull an external, structured, frequently changing source and record it as time-stamped atoms mapped to the graph, without growing forever.

**Source types:** a polled HTTP/JSON feed (live telemetry)

**Smallest semantic unit:** one telemetry record (one atom with its observation time)

**Entities:** feed, record, mapping to concepts, retention window

**Claims / Observations / Interpretations:** observations only; the mapping is declared data, not inferred

**Temporal requirements:** interval cadence (default 300 s = 288 runs a day); observations kept 72 h then aggregated

**Competing perspectives:** none

**Rights / consent / disclosure:** the feed's licence and attribution travel with each record; no secrets in atoms or logs

**Workflow:** one `feed.pull id=<feed>` step per run (`app/config/workbench/telemetry/templates/<feed>.ak`)

**External effects:** outbound HTTP pull only; record effect; no publication

**Outputs:** telemetry atoms and their periodic aggregates (the retention hook), a room view

**Observation coordinates:** wall clock and bench coordinate per run

**Evaluation frames:** none

**General CM dependencies:** `feed` (`feed.pull`, the map DSL), `feed_poll` (default-feed registration, retention hook), the telemetry atoms (application)

**Ontology patterns:** telemetry atoms; aggregates written by the retention hook (a bounded write stream, memory discipline R5)

**Operation Profile:** `telemetry_feed`

**Existing A25 base template:** itself

**Replay requirement:** records are append-only with their source timestamp; a missed poll is a gap, not a backfill

**Degradation mode:** no network → the run records its reason and costs nothing; nothing is invented

**Reference dataset:** thesaurus origin: the live telemetry feed. The seeds sample is chosen in stage S

**Success criteria:** a run with nothing new is not stopped (free run); a failure is a run with a reason, not a log line

**Known limitations:** a thread that polled every 5 min becomes a driver run every 5 min

**Open questions:** one workload per feed or one with a list

**Current files:** `concepts/feed_poll.py` (`svc:feed-poll`, `feed.poll`); the telemetry atoms and their retention hook

*(10-02 update: `svc:feed-poll` is retired; the files are now `app/config/workbench/workloads/{eonet,usgs_eq,iss}.json`, `app/config/workbench/telemetry/templates/*.ak`, and `concepts/feed_poll.py` for default-feed registration and the retention hook.)*

**Declaration fields used:** `profile`, `bench`, `workflow`, `idset: telemetry`, client `feed:<name>`, `trigger`, `duty`, `effect: record`, `effect_read`, `requires: []`, `appetite` (0), `budget`

**Gate facts and effect:** declared · armed · headroom (none needed); effect `record`

**What it gets wrong today:** (10-02: fixed — one declared workload per feed; each run records its own outcome.) Remaining: the cadence floor is the driver's 60 s tick
