# T0 Template Candidate Record — `broadcast`

*Draft, ratified when Phase 0 is accepted. Source: `docs/design/reference-templates-and-profiles.md` §1–§2; written for the thesaurus line's origin, with no thesaurus-only material in the shape.*

**Candidate ID:** T0-broadcast

**Title:** Broadcast — turn / react / wrap on a source Set, with roles and a room

**Domain profiles:** broadcast

**User roles:** programme (the workload's own client), speaking roles per declaration (Anchor/Commentator, Curator/Visitor/Explorer, Reader/…), producer, scribe; guest read

**Problem:** Air a programme around the clock from a curated source, honestly attributed, without a person operating it.

**Source types:** an ontology Set of items or passages (a pack: ネタ帖, a works pack, a passages file); a provider/model for turns

**Smallest semantic unit:** one aired line: a turn by one cast, grounded in one source atom

**Entities:** programme (workload), society + space, cast/role, source item, aired record, room

**Claims / Observations / Interpretations:** the aired record is an observation (provider, model, source, atom, turn, grounded); the line is generated interpretation of the source and is marked AI-generated

**Temporal requirements:** continuous cadence (`every:1800s`, `daily:HH:MMZ`); a turn is the beats of one source; the cursor is derived from the record

**Competing perspectives:** a second voice that is told to push back (Commentator); the Explorer must mark an interpretation as one

**Rights / consent / disclosure:** per-message AI disclosure and licence attribution; public broadcast is a separate creator-gated consent; outbound LLM use needs `open_guest`/consent; sources are licensed (CC0 works, public-domain text)

**Workflow:** `society.air` per beat (→ `station.air.turn`), then `society.broadcast.relay`; templates `app/config/workbench/studio_ai/templates/*.ak`

**External effects:** publish: the public mirror (rooms); a channel workload (`news_show_x`) republishes to an external channel and is the same template's egress, not a ninth template

**Outputs:** the live feed, the aired record, the room page, a channel post

**Observation coordinates:** bench coordinate per aired row; turn number continued across the beats of one source

**Evaluation frames:** none; the gate's run outcome (aired / stood-by with its reason) is the frame

**General CM dependencies:** `society`, `cast`, `bench_station` (`station.*`), `cronon`; reserved: `bench`

**Ontology patterns:** `neta:…` item Sets, `art:work:cma:…`, `shelf:…:passages:…`; companion atoms `<item>:angle` / `:image` / `:label` / `:credit`

**Operation Profile:** `broadcast`

**Existing A25 base template:** itself

**Replay requirement:** the aired rows regenerate the cursor and the turn numbers; a line is never re-generated, only re-shown

**Degradation mode:** no model or no network → the programme stands by with a coded `station:reason:*`, nothing is invented; no source → `waiting_source`

**Reference dataset:** thesaurus origin: studio_ai (news show, art explorer, plant geek, thinkers shelf). The seeds sample is chosen in stage S

**Success criteria:** every run airs or names why not; each item airs once per cycle then wraps to the least recently aired; the room shows exactly what aired

**Known limitations:** a source with no declared order airs in alias order; the room's seats are two

**Open questions:** the egress channel as the reference egress binding (W2)

**Current files:** `app/config/workbench/workloads/{news_show, art_explorer, plant_geek, thinkers_shelf}.json`; `app/config/workbench/studio_ai/templates/*.ak`; `concepts/bench_station.py`; the rooms under `app/archives/station/`

**Declaration fields used:** `profile`, `bench`, `bench_public`, `bench_kind`, `workflow`, `society`, `trigger`, `duty`, `effect`, `effect_read`, `appetite`, `budget`, `on_exhausted`, `unmarked_rows`, `pins` (`item_set`/`episode_set`), `space`, `moderator`, `offers`, `roles`, `source`

**Gate facts and effect:** declared · armed · source_ready (the item Set has members) · headroom; effect `publish`

**What it gets wrong today:** the station's turn logic lives in `bench_station` rather than in a `turn` line (W2); the declarations restate the profile in full
