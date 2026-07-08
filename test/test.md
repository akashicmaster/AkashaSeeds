# Akasha Test Suite

This directory contains `.ak` test scripts that exercise the Akasha command interface.
Each script is self-contained and submits a batch job through the JCL system.
The scripts are intended as both regression tests for contributors and worked examples for anyone building on top of Akasha.

---

## Prerequisites

Start the Akasha shell:

```
python akasha.py
```

If this is a fresh instance, the base ontology loads automatically at startup.
Wait for the `akasha>` prompt before running any tests.

---

## Running a test

Inside the Akasha shell, use the `run` command:

```
akasha> run test/test_00_smoke.ak
```

The shell prints a `job_id` and returns immediately. The job runs asynchronously in the JCL queue.
Check completion:

```
akasha> job.stat <job_id>
```

A completed job shows `status: DONE` and `step_done: N/N`.

---

## Test files

Run them in order on a fresh database, or individually on an existing one.
Each script uses its own `t0N:` namespace so test data does not collide.

| File | Commands covered |
| :--- | :--- |
| `test_00_smoke.ak` | `w`, `al`, `ln`, `meta`, `s.add` — JCL execution baseline |
| `test_01_memory.ak` | `w`, `def`, `r`, `rm`, `al`, `al.rm`, `meta`, `s.add` |
| `test_02_links.ak` | `ln`, `ln.+`, `ln.rm`, `ln.ls`, `meta`, `s.add` |
| `test_03_sets.ak` | `s.add`, `s.rm`, `s.ls`, `s.clear`, `s.op` |
| `test_04_aliases_dive.ak` | `al`, `al.find`, `al.rm`, `look` / `d` / `out` |
| `test_05_notes_sys.ak` | `n.new`, `n.add`, `r`, `hist`, `log.new`, `log.cp`, `log.ann`, `log.read` |
| `test_06_explore_tree.ak` | `tree`, `exp`, `look`, `assoc` |
| `test_07_rec_lens.ak` | `rec.new`, `rec.set`, `rec.idx`, `rec.get`, `rec.ls`, `rec.sum`, `rec.rm`, `rec.table`, `lens`, `quadrant.plot`, `cross.axes`, `ref.set`, `ref.get`, `table.new`, `table.row.add`, `table.ls` |

---

## Verifying results

Each script has a `VERIFY` block in its header listing interactive commands to run
after the job completes. For example, after `test_02_links.ak`:

```
akasha> ln.ls t02:node:sun
akasha> tree t02:node:sun 3
akasha> al.find t02:%
```

Read-type commands (`tree`, `exp`, `look`, `rec.table`, `quadrant.plot`) also run
inside the batch scripts — their output is captured in the job log and can be
inspected with `job.stat <job_id>` if needed.

---

## Running all tests in sequence

```
akasha> run test/test_00_smoke.ak
# wait for DONE
akasha> run test/test_01_memory.ak
# wait for DONE
akasha> run test/test_02_links.ak
# ... and so on through test_07_rec_lens.ak
```

Each file is idempotent in terms of atom content (atoms are content-addressed;
re-running a file does not duplicate atoms). Alias bindings are additive — if
you run a file twice, the second run re-registers the same aliases over the same
atom keys, which is a no-op.

---

## Adding new tests

When adding coverage for a new command or concept model:

1. Pick the next available number (e.g. `test_08_<topic>.ak`).
2. Use a fresh namespace prefix (e.g. `t08:`) to avoid colliding with existing tests.
3. Follow the same header format: `VERIFY` block, `HOW TO RUN` line, numbered sections.
4. Generate atom content with `w` and always alias with `al $0` immediately after.
5. Close with `s.add test:NN:<topic> <alias>` for every atom written, so results are
   inspectable as a set after the job completes.

---

## Developer verification scripts (Python)

Two Python harnesses sit alongside the `.ak` examples. They are **developer /
CI tools**, not user-facing walkthroughs — they exercise structural invariants
the `.ak` batch scripts cannot see. Run them directly with `python`, not through
the shell's `run` command.

### `check_invariants.py` — structural regression guard

```
python test/check_invariants.py
```

Verifies the invariants that keep the system loosely coupled and secure. Run it
after any change to the write path, auth/scope, the WriteQueue/JCL, or a backend:

- **Single route to the core** — the write guard is present on `commit`/`put_link`,
  and an AST scan of every function that calls a raw core-write primitive is diffed
  against a reviewed baseline, so a **new back-door into the core** surfaces as a
  `REVIEW` line.
- **Security anchors** — transport-trust constants, `genesis_rite` local-only,
  system-identity gating, PBKDF2 + constant-time compare, bounded/transient-only
  retry, `ws:`/`wf:` reserved prefixes, `PriorityQueue` serialiser.
- **Junk detection** — ghost references to removed symbols; leftover
  `TODO/FIXME/XXX/HACK` markers in `lib/`.
- **Runtime guard** — boots a kernel and proves an unguarded write is rejected, a
  `system_context` write is allowed, reserved prefixes are refused, and
  `genesis_rite` over the network is refused.

Exit code `0` = all hard invariants hold. `REVIEW` lines are warnings (confirm the
new route/marker is legitimate), not failures.

### `loadtest_queue.py` — multi-client queue resilience under load

```
python test/loadtest_queue.py                 # default (~30-60s)
AKASHA_LOAD=quick python test/loadtest_queue.py   # fast smoke
AKASHA_LOAD=heavy python test/loadtest_queue.py   # stress
```

Drives the real kernel dispatch path from many concurrent client threads to prove
the single-worker WriteQueue holds under heavy load:

- **P1 write-storm** — N threads hammer one cortex; every write lands exactly once
  (no lost writes, single-queue serialisation).
- **P2 dedup** — many threads write identical content → exactly one content-addressed
  atom, intact.
- **P3 multi-client** — distinct authenticated clients write concurrently through the
  shared nucleus; nucleus stays consistent and no client can read another's atom.
- **P4 priority-order** — a HIGH write queued *after* a backlog of LOW writes still
  runs first (priority reorders, it is not FIFO).
- **P5 guest-churn** — rapid concurrent guest creation; a full pool refuses cleanly
  (fail-closed, not a crash).

A watchdog fails the run if any phase wedges (deadlock detection). Throughput and
latency percentiles are reported per phase.

### `loadtest_login.py` — concurrent-login client cap

```
python test/loadtest_login.py
```

Each Cell caps concurrent sessions at `manager.max_sessions` (the seeds family-use
default is 5, set via `AKASHA_MAX_LEAVES` — a single `if` gate, trivially changed).
This test proves the cap behaves correctly under *simultaneous* login, where the
number matters less than the guarantee that a check-then-create race cannot
overshoot it:

- **P1 all-seats** — `cap` clients log in at one barrier; each gets a distinct,
  isolated cortex.
- **P2 cap-enforced** — one more login on a full Cell is refused ("Limit Reached").
- **P3 no-overshoot** — far more clients than seats race one barrier; exactly `cap`
  win and the live session count never exceeds `cap` (the `_session_wq`-serialised
  check-then-create guarantee).
- **P4 seat-recycle** — closing a session frees a seat for a waiting client.

### `loadtest_group.py` — group-space sharing (family knowledge sharing)

```
python test/loadtest_group.py
```

A group space is the minimal unit of *shared atoms* — several clients form a group
and donate atoms into one content-addressed space they can all read. It is the
entry point to the knowledge-exchange ecosystem and the substrate under cloud
offload, multi-LLM collaboration, and DTN handoff, so it must work through the
normal flow (create user → add to group → share → read):

- **P1 membership** — members added to a group each get the group scope, a group
  engine on their live session, and a Human identity atom.
- **P2 share+read** — a member donates atoms (`dont.send to=group:`); every other
  member reads them by key, by alias, and via `look`.
- **P3 isolation** — a non-member cannot read the shared atoms.
- **P4 concurrent** — all members donate into the one group space at once; the
  group's single WriteQueue serialises them and every atom lands.
- **P5 revocation** — removing a member drops the group engine + scope from their
  live session; they can no longer read the shared atoms.
- **P6 navigation** — a member navigates shared content within group scope
  (`explore`, `alias.find`, `set.ls`, `dive.look`), while another member's *private*
  (undonated) atoms stay black-holed and a non-member sees nothing.

### `loadtest_cast.py` — cast avatars & society sessions

```
python test/loadtest_cast.py
```

A `cast` is a client's avatar — an alter-ego that represents them in a group
(organisation / society). Beyond static atom sharing, this brings near-real-time
sessions to the akasha space. Anonymity is a policy choice (SNS: the avatar hides
the human; company: `disclose=True` matches the avatar to the real member), and the
society is the persistent group space (an absent member reads the exchange later).

- **P1 lifecycle** — `cast.new` + attributes + `map`/`diagnose`/`react` + `ls`/`open`.
- **P2 agent-session** — two avatars converse in a group; utterances are anonymous
  (authored by the avatar) and persistent; a member's avatar reacts to another's line.
- **P3 impersonation** — a member cannot `say`/`publish` as an avatar they do not own.
- **P4 shared-avatar** — `cast.publish` copies the full persona into the group; another
  member opens it and reads/reacts read-only.
- **P5 disclosure** — `disclose=True` stamps the real client_id (company); the default
  hides it (SNS).
- **P6 isolation** — a non-member sees no utterances and cannot open the shared avatar.

### `benchmark.py` — evaluation & benchmark harness

```
python test/benchmark.py            # human summary
python test/benchmark.py --json     # + machine-readable report for CI
```

Turns Akasha's headline claims into measured numbers:

- **crash-stop** (the marquee) — a subprocess writes atoms to the FULL-synchronous
  nucleus and is `SIGKILL`'d mid-write; on reopen, **every atom whose commit returned
  is intact** (last-write-only: only the in-flight write is lost). Proven, not asserted.
- **throughput** — writes/sec and p50/p99 latency through the real kernel path.
- **dedup** — content-addressed unification ratio (identical content → one atom).
- **isolation** — cross-user read is refused, scored as a pass rate.

### `redteam_memory.py` — adversarial suite (OWASP ASI06)

```
python test/redteam_memory.py
```

Proves the scope model holds under *attack*, not just ordinary operation — every
scenario must be refused fail-closed (one survival = FAIL). Run it on any auth /
scope / weaver / write-path change:

- cross-user private read, bare-id-over-network privilege, tampered `akt:` token,
  single-route-guard bypass, `ws:`/`wf:` reserved-prefix injection, system-identity
  capture, network genesis land-grab, group leakage, avatar impersonation, JCL
  step-blocklist escape.

### `semantic_eval.py` — self-owned embedding tier

```
python test/semantic_eval.py
```

Verifies the dependency-free semantic vector that powers cosine similarity (Jataka
T2 dream, semantic search). The floor tier is a real technique (signed
feature-hashing over word tokens + character n-grams), not a hash placeholder, so it
degrades *gracefully* — genuine cosine structure with zero heavy deps, and an
optional sentence-transformer upgrade behind `AKASHA_EMBED_MODEL`.

- **P1 separation** — similar texts score higher cosine than dissimilar ones, for
  English *and* CJK (Japanese), using only the self-owned embedding.
- **P2 populate** — a committed text atom carries `meta["semantic_vector"]`; tiny /
  token atoms are skipped (no meta bloat).
- **P3 dream** — Jataka ranks semantically-related atoms above unrelated ones (the T2
  cosine tier that previously never fired).
- **P4 learned** — the numpy mid-tier (`lib/akasha/semantic_learn.py`, PPMI+SVD over
  co-occurrence) captures *distributional* relatedness the lexical floor misses
  (bank~interest 0.97 vs 0.20; swallow~migrate 0.18 vs 0.00), learned from a corpus
  with zero external model. Degrades to the feature-hashing floor if numpy is absent.

- **P5 learn+persist** — `semantic.learn` (admin) builds the model from the full corpus
  (nucleus ontology + cortex) and persists it to the nucleus vault; `semantic.search`
  then ranks with the learned tier, and the model survives a restart (reloads from the
  vault).

- **P6 gap.scan** — `gap.scan` surfaces self-expanding-loop entry points: a concept
  that is referenced a lot but under-curated ranks above an equally-referenced but
  well-linked one (gap = importance × (1 − structural)).
- **P7 autolearn** — the boot hook builds and persists the learned model in the
  background from the ontology corpus, *and bakes* each atom's learned vector into its
  `semantic_vector` meta (IDLE bulk write), so search/dream are smart from startup.
- **P8 external** — an important-but-thin atom tagged `provenance=external` is excluded
  from `gap.scan`, while an identical curated one is surfaced (ASI06 guardrail).
- **P9 gap.fetch** — `gap.fetch` (avatar delegate) enriches a thin concept by fetching
  external context, links it back via `calc:depicts`/`calc:enriches`, tags it
  `provenance=external`, degrades cleanly offline, and does not re-surface the fetched
  atom as a gap (no fetch→gap→fetch loop). (Mocked network.)
- **P10 node/content** — the structural node-walk embeddings (`NodeWalkLearner`,
  random walks over typed links) and the content co-occurrence embeddings rank the same
  pair oppositely — "connected the same" vs "means the same" — proving complementarity.

Kernel hooks added: `semantic.search` (learned/floor cosine ranking), `semantic.learn`
(admin — learn from the full corpus, persist to the nucleus vault, auto-run at boot via
`_schedule_semantic_learn`; disable with `AKASHA_NO_AUTOLEARN=1`), `gap.scan`
(important-but-thin concepts), and `gap.fetch` (admin — auto-enrich the gaps). Fetched web
atoms carry a `provenance:external` scope and a grounded `trust` score (from evidence:
authority/reach/nature) so external content is never indistinguishable from curated
ontology (ASI06).

### `emotion_eval.py` — Akasha-native (link-based) emotion axis

```
python test/emotion_eval.py
```

Guards the link-based track of the two-track emotion design. Emotions are `emo:` atoms; an
atom "feels" one via a link (`calc:associated_with` / `has_emotion` / …) whose TARGET is an
`emo:*` atom. Atoms are content-addressed, so the stored dst is a hash — the namespace lives
in the alias — so the emotion axis resolves the target's ALIAS (the signal
`CosmosMapper.get_aura_color` uses), not the relation string. (Previously the axis matched
relation prefix `emo:`, of which the ontology has **zero**, so `associate(axis="emotion")`
was silently empty despite 500+ links targeting `emo:*` atoms.)

- **E1 axis** — `associate(axis="emotion")` returns the emotion links (type=emotion).
- **E2 profile** — `emotion.profile id=` returns a ranked, L1-normalised emotion vector.
- **E3 weight/depth** — stronger edges and nearer hops score higher (depth decay 1/depth).
- **E4 empty** — an atom with no emotion links returns an empty vector, not an error.
- **E5 void** — `find_link_voids` does not flag `emotion` as missing when it is present.

Kernel hook: `emotion.profile id= [scope=] [normalize=]` (read; `emo.vector` / `emo.profile`
aliases). This is the link-based emotion track; the external-NLP sentiment track is separate.

### `vision_eval.py` — LiteRT image profiling

```
python test/vision_eval.py
```

Verifies image profiling (image → classification labels → graph). Backend ladder:
`ai_edge_litert` (LiteRT, primary — the standalone `tflite-runtime` is frozen at 2.14 and
crashes under numpy 2.x) → `tflite_runtime` (legacy 32-bit ARM) → `tensorflow.lite`. The
model (quantised MobileNet) is fetched on demand and cached under `env/models/`.

- **V1 classify** — a known image profiles to sensible labels (Grace Hopper → `military
  uniform`, when the sample/model are available).
- **V2 ingest** — `image.profile` writes an image atom + per-label concept links
  (`calc:depicts`) under the `provenance=external` guardrail (`trust` = model confidence).
- **V3 guardrail** — the external image atom is excluded from `gap.scan`; its concept atoms
  are ordinary graph nodes.
- **V4 degrade** — a bad path / unavailable runtime returns an error dict, never crashes.

Every phase SKIPS cleanly (recorded OK) when no inference backend / PIL / model is available
(offline CI) — vision is an optional, network-provisioned feature. Kernel hook:
`image.profile path=|url= [top_k=]` (write; `img.profile` / `vision.classify` aliases).

### `fileio_eval.py` — general file import/export route

```
python test/fileio_eval.py
```

Guards the single Harmonia-owned disk-I/O layer (`lib/harmonia/fileio.py`) and its kernel
`io.*` methods for text/semi-text formats (CSV, JSON, Markdown, TXT). Before this, real file
I/O was scattered and domain-specific (ontology-only loader; CSV as in-memory strings; dead
Harmonia `transport.py` scaffolds). Now one route: tabular files project into the `table`
model (reusing the table operators), documents become indexed atoms tagged `provenance=file`.
Reads/writes are confined to an allow-list of roots (`io.allow` permits a directory). PDF and
other binary formats are deferred (GitHub issue).

- **F1 parse** — CSV / JSON-array → table; JSON-object / MD / TXT → doc (with title).
- **F2 import** — `io.import` routes CSV/JSON into the table model; MD → `provenance=file` atom.
- **F3 export** — `io.export` a table to CSV/JSON/MD files; the CSV round-trips back to rows.
- **F4 index** — `io.index` a permitted directory → docs + tables; the index set is populated.
- **F5 safety** — a path outside the permitted roots is rejected (no host-filesystem escape).

Kernel hooks (admin/librarian): `io.import path=|text= [format=] [table=]`, `io.export path=
(table=|set=) [format=]`, `io.index dir= [exts=] [limit=]`, `io.allow dir=`.

### `pipeline_eval.py` — the I/O interface (Source | Sink)

```
python test/pipeline_eval.py
```

Guards the pipeline interface (`lib/harmonia/pipeline.py`) — the "Unix pipe" of the data
plane. Every endpoint is a **Source** (produces a `Stream`) or a **Sink** (consumes one), and
`run_pipeline(source, sink)` connects any pair: files (`FileSource`/`FileSink`), the `table`
model (`TableSource`/`TableSink`), a set of atoms (`SetSource`), a document (`DocSink`), and
an in-memory upload (`InlineSource`). The kernel's `io.*` methods are thin wirings over this,
so the same interface serves file↔model both ways and a future Web-GUI upload unchanged. The
`Stream` (structured records or a document) is the interchange currency — the pipeline's byte
stream. `lib/harmonia/pipeline.py` imports nothing from `akasha`; graph endpoints receive
their write/read closures by injection, exactly like a pipe knows nothing about the programs
it joins.

- **PL1 file→file** — `FileSource(csv) → FileSink(md)`: pure endpoint composition, no graph.
- **PL2 upload→file** — `InlineSource(in-memory csv) → FileSink(json)`: the web-upload path.
- **PL3 upload→model→file** — `io.import text=` (InlineSource→TableSink) then `io.export`
  (TableSource→FileSink); the exported rows equal the uploaded ones (round-trip both ways).
- **PL4 file→model** — `io.import path=csv` → the `table` model (the reverse of export).
- **PL5 set→model(lens)** — `io.project src= model=table` (LensScanSource→ConceptCastSink):
  an in-graph source scanned and cast into a concept model through lens. The base of the
  "project into any model" path; `table` is the working target today (other models implement
  the Importable contract as a per-model follow-up — issue #43).
- **PL6 model→client** — `io.export inline=true` (→ ResponseSink) returns the serialised
  content in the result instead of a file: the client 'receive' path, mirror of the upload.

---

## Command reference (quick lookup)

| Command | What it does |
| :--- | :--- |
| `w "text"` | Write a plain-text atom |
| `def "id"` | Define a conceptual hub atom |
| `al $0 "name"` | Alias the last written atom |
| `al.find pat%` | Find aliases matching a pattern |
| `al.rm "name"` | Remove an alias (atom is kept) |
| `r <id>` | Read an atom by key or alias |
| `rm <id>` | Drop an atom |
| `ln src dst rel` | Create a typed link |
| `ln.+ src dst rel` | Reinforce a link's weight |
| `ln.rm src dst rel` | Remove a typed link |
| `ln.ls <id>` | List an atom's links |
| `meta <id> key val` | Set metadata on an atom |
| `s.add name id` | Add atom to a set |
| `s.rm name id` | Remove atom from a set |
| `s.ls name` | List set members |
| `s.clear name` | Clear a set |
| `s.op union\|isect\|diff result a b` | Set algebra |
| `tree <id> [depth]` | Link-traversal tree |
| `exp ns=<ns>` | Explore by namespace prefix |
| `look / d <id>` | Dive into an atom's meaning space |
| `assoc <id>` | Gap detection — missing semantic links |
| `image.profile path=\|url=` | Classify an image (LiteRT) → labels as atoms/links |
| `io.allow dir=` | Permit a local directory for file import/index/export |
| `io.import path=\|text= [table=]` | Import a file/upload (CSV/JSON→table, MD/TXT→indexed atom) |
| `io.index dir= [exts=]` | Index every supported file under a permitted directory |
| `io.project src= [model=table]` | Project an in-graph source into a concept model (via lens) |
| `io.export (table=\|set=) path=\|inline=true` | Export to a file, or return content inline (client receive) |
| `hist` | Recent atom stream |
| `n.new "title"` | Create a note |
| `n.add "text"` | Append a chunk to the active note |
| `log.new "name"` | Create an exploration log |
| `log.cp "note"` | Record a checkpoint |
| `log.ann "text"` | Annotate the last checkpoint |
| `rec.new type=T attr=val …` | Create a record atom |
| `rec.set key attr val` | Update an attribute |
| `rec.idx key sets` | Add record to index sets |
| `rec.get key` | Read a record with all attributes |
| `rec.ls [type=T] [in_set=S]` | List records |
| `rec.sum attr=A [in_set=S]` | Sum a numeric attribute |
| `rec.rm key` | Delete a record |
| `rec.table in_set=S` | Formatted table view |
| `lens src=S` | Scan a set for concept model targets |
| `lens.flatten into=name` | Persist scanned nodes as rec atoms |
| `quadrant.plot in_set=S x=A y=B` | 4-quadrant ASCII scatter plot |
| `cross.axes` | List available cross-concept axes |
| `ref.set dim atom` | Bind a typed context variable |
| `ref.get [dim]` | Read typed context variable(s) |
| `table.new name=T cols="c:type,…"` | Create a flat table |
| `table.row.add table=T col=val …` | Insert a row |
| `table.ls table=T` | List table rows |
