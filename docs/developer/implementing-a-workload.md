# Implementing a function on the workbench — the manual and the checklist

**Audience: the development user.** This is the manual for adding something that runs on the
workbench — a research lab, a broadcast programme, a business process, an experiment. On Akasha all
of them are the same thing, a **workload**, and they are added the same way.

You write — all of it under the application root, `app/`: Concept Models (`app/concepts/<model>.py`), ontology packs (`app/ontology/`), workload
declarations (`app/config/workbench/workloads/*.json`), templates
(`app/config/workbench/<bench>/templates/*.ak`), rooms (`app/archives/`), evals (`app/test/<slug>_*`), and the
seeds. You never edit the platform — everything outside `app/`: `lib/`, `api/`, the kernel, the
platform's `ontology/` and `config/`. You reach it only through its specification,
`docs/platform/SPEC.md`. When a step here needs something the platform does not provide, that is
**not** a patch you reach in and make: it is a request to change the specification —

> `needs platform: <what> — <why> — <the read or call you expected>`

— which reaches the platform as a specification request and is answered with a new specification
version. The contract is `docs/platform/SPEC.md` (with `docs/platform/CHANGELOG.md`); the platform's
working detail is [`platform-manual.md`](platform-manual.md). Read those, never the platform's source.

**If adding a workload needs a new code path in the driver, the recorder, admission or the guide,
stop.** The design is being bent, and the next workload will pay for it.

The three standing rules this manual serves are in `docs/for-llm/workbench-operating-doctrine.md`:
a declaration is a desired state and a boot reconciles to it; behaviour follows a declared DUTY,
never the domain; a stop names itself, in vocabulary, at the place that decided it.

---

## 0. The model in eight lines

1. Everything stored is an **Atom**, linked by typed **Links**, grouped into **Sets**. A coordinate
   is a Set membership written at mint. A viewer computes nothing.
2. A **Bench** (`wb:<name>`) is where a workload's coordinates, observations and artifacts live. Its
   `kind` names observer families, nothing else.
3. A **Society** (`<group>/<space>`) is who may act: roles, grants, a moderator.
4. A **Workload** is the unit the driver runs: one workflow (a template plus its params) on one
   bench, acted by one society, declaring `trigger`, `duty`, `effect`, `appetite`, `budget`, `pins`.
5. A **Programme** is a workload with `duty: wb:duty:continuous` and `effect: publish`. Nothing more.
6. **One recorder**: every step, inline or as a job, mints its coordinate and its `executes` /
   `rehearses` link. What left no trace did not happen.
7. **One gate** for every model call; **one admission point** for every job; **one provisioning** at
   boot that writes what the declarations say.
8. A value the code compares against is **vocabulary** — an atom id in the lexicon. A state is a Set
   membership. There is no `false`, no delete, no composite score.

---

## 1. The procedure — ten steps, in this order

### Step 1 — Define the meaning (ontology, before any code)

- Every term the workload will compare against gets an atom in the lexicon under one namespace
  (`nsdef:<ns>`): states, reasons, families, outcome kinds, roles. One sentence each.
- List the Sets it will join (`set:<ns>:<key>:<value>`).
- Use only the existing link vocabulary (`executes`, `rehearses`, `observed_in`, `derived_from`,
  `evidenced_by`, `decides`, `predicts`, `supersedes`, …). A new link kind needs a design line first.
- A new relation or namespace goes in `scripts/gen_lexicon.py` (`CORE_RELS` / `CORE_NS`) for core
  machinery, or the pack's own `_lexicon.ak` for a domain term.

**Check:** `python scripts/gen_lexicon.py && python test/verify_lexicon.py --all` is PASS, and `grep`
finds no string literal of a state or reason in code.

### Step 2 — Declare the workload (configuration, no code)

One file per workload: `app/config/workbench/workloads/<slug>.json`. The frozen shape:

```json
{"bench": "wb:studio_ai", "workflow": "thinkers_shelf",
 "society": "studio_ai/thinkers_shelf",
 "trigger": {"boot": true, "then": "daily:21:00Z"},
 "duty": "wb:duty:continuous", "effect": "publish",
 "appetite": {"llm_calls_per_run": 15, "weight": 0.1},
 "budget": {"per_day": 2, "max_wall_s": 900},
 "pins": {}}
```

| field | what it is |
|---|---|
| `bench` | the bench the workflow runs on, `wb:<name>` |
| `workflow` | the template's slug; with `bench` it forms the **key** `<bench>/<workflow>` |
| `society` | `<group>/<space>` — who acts |
| `trigger` | `{"boot": true, "then": "daily:HH:MMZ" \| "every:<n>s"}`. `boot` fires once per writer boot; `then` is the schedule after that |
| `duty` | `wb:duty:continuous` or `wb:duty:best_effort` — see Step 6 |
| `effect` | `publish` (it leaves the world) or `execute` |
| `appetite` | `llm_calls_per_run` is the ESTIMATE one run needs; `weight` is its share of contention |
| `budget` | `per_day` is how often it may run — and therefore the guide's denominator; `max_wall_s`, `max_steps` bound one run |
| `pins` | the atoms and Sets the template's steps resolve against; may be empty, never absent |

- The **key** is `<bench>/<workflow>`, stable for the life of the workload. It is the accounting key
  at the model gate, the row key in the guide, the key in Health and in the pool ledger. Derived from
  this file and never supplied by a submitter — a key the submitter chooses makes credits and
  allotments spoofable.
- The **room**, if there is one, is derived from the slug: `/station/<slug with - >/`. No repo path
  appears in a declaration: a repo path stamped into the guide renders as a broken link, resolved
  against whatever page is reading it.
- Anything the frozen shape does not cover — the society's topic, the role contracts, the
  capability offers — goes in the same file beside those fields. A workload is one file.

**Check:** `python app/test/station_workload_decl_eval.py` (for a station workload) or the conformance
eval on your declaration. A missing field is a provisioning error naming the field, never a silent
default.

### Step 3 — Write the workflow as a template

`app/config/workbench/<bench>/templates/<slug>.ak`, with a `#!params` header giving the parameters and
their defaults. Steps are plan lines calling existing ops.

```text
#!params program=studio_ai/thinkers_shelf
society.air program=$program role=Reader source=next
society.air program=$program role=Listener source=current last=feed:last
```

- **No loops** — the script has none; a repeated thing is a sweep.
- **No step writes an atom by hand.** It calls the concept's op, which mints through the recorder.
- A step that reaches outside the world calls a capability marked `effectful`, and that is admissible
  only under `effect: publish`.
- A step is a fixed line of data, so everything that varies is read at run time — from `pins`, from
  the record (`source=next` / `source=current`) or from the feed (`last=feed:last`). Nothing is
  threaded between steps, which is why a crash or a re-run cannot desynchronise a cursor.
- `wf.branch from=<template> params=…` substitutes `$name`; **`wf.load` does not** — it loads a file
  as entries verbatim. A template with `$` placeholders must be branched, not loaded.

**Check:** the eval lints the template — every step names an op that exists, plays only roles the
workload declares, spells no state or reason as a literal, and carries no repo path.

### Step 4 — Declare the society

Roles, the moderator, the capability offers, and who the group's members are (admin identities are
added by provisioning, never by hand).

- A role that differs from another only by prompt text is **not a role**.
- A capability is offered to the **cast that speaks**, not to a beat: a role that names
  `cast: Anchor` holds the Anchor's offer and must not be given one of its own.
- Auto mode needs a **chairman and a scribe** — every autonomous act needs a keeper of the record —
  and neither may be a speaking cast: arming auto rebinds the moderator agent's controlling client,
  which would take a speaking cast out of the programme's own hands.

**Check:** after boot, `grp.ls` shows the group with the admin identities, and
`cap.ls role=<r> context=<bench>` shows the offered capabilities at the current fingerprint.

### Step 5 — Let provisioning do the rest (never a command)

At boot, from the declaration: the bench, the society, the workflow **on the declared bench**, the
workload with its memberships, armed if `trigger` says so, registered in the guide if
`effect: publish`. One line:

```text
[bench] provisioned workload=<bench>/<slug> society=… workflow=… trigger=… duty=… effect=…
```

- Idempotent; re-applied on a new build. A second boot logs `unchanged`.
- A failure is `[bench] provision failed workload=… reason=<id>` **at boot** — never a run failure
  hours later.
- **A declaration is a DESIRED STATE and a boot RECONCILES to it.** Not "create if absent": *armed is
  not provisioned*. The society persists while the workflow entries are consumable, so any predicate
  standing in for "everything is in place" is eventually false when it matters. That is exactly what
  hid a bench with no workflow for two days.

**Check:** delete `data/` and boot — everything is reproduced with no operator command.

### Step 6 — Declare the duty, and know what it buys

```text
wb:duty:continuous     # must not go silent
wb:duty:best_effort    # the default
```

The driver never asks "is this a station?", "is this research?". It asks what the workload declared.
For `continuous` it owes three things:

1. any gate that stops it **writes a state and a reason** — never silent without one;
2. the breaker **does not unschedule** it — unscheduling *is* the silence, and an invisible one;
3. a start-up run that produced no OUTPUT **leaves the obligation owed** — bounded retry, not "next
   slot", which for a daily workload is a day of silence.

A research bench declares nothing and keeps `best_effort`, where stopping to be examined after
repeated failure is right and nobody is watching a room. If a workload needs behaviour no duty
expresses, **add a duty** — one word, one definition, one read — not a condition.

### Step 7 — Run once through the recorder and read it back

- `cronon.executions bench=<bench> branch=<slug>` lists one coordinate per step, each with
  `executes` (or `rehearses` in thought mode).
- Every reading is an observation joined to its Sets at mint; `source.trace` shows them.
- If it publishes: `[llm] admission reserved …` → `[llm] settle …`; the state Set moves
  `warming_up → on_air → rebroadcast`; the guide row shows `state`, `reason`, `airing`.

**Check:** the run's numbers agree everywhere they appear — the guide, Health, the pool ledger, the
room — because they are ONE read, not three counters.

### Step 8 — Run the conformance eval, not a bespoke one

`app/test/workload_conformance_eval.py <declaration>` runs the checklist against any declaration: fresh
store → boot → the provisioned line → one run → coordinates → observations → the state Set → the
guide row → a second boot unchanged → a gate refusal writes a reason → an effectful step rehearsed
in thought → no literal states in code. **A workload ships with this eval passing on its
declaration**, plus at most one eval for what is genuinely its own.

*Status: the conformance eval is the platform's, and arrives with seed A. Until it does,
`app/test/station_workload_decl_eval.py` holds the user half — the shape, the key, the room, the
template lint and the offers.*

**An eval that asserts a gap is safe — "left alone", "no-op when unprovisioned" — is a defect.**
Evals assert closures.

### Step 9 — The viewer needs nothing

`#bench/<slug>` renders from the generic reads (`bench.info`, the bench kind's own runs read such as `learning.runs`, `cronon.executions`, the
observation Sets, and — for a workload — `workload.status key=<key>`, which answers `last` (what the
run recorded, with the op's own reason verbatim or empty), `gate` (the gate's own term), `next_at`
and `spent_today`). A page **computes nothing about the platform**, and it **names the status
itself**: "on air", "standing by" and the sentences around them are the application's words,
composed from `last` and `gate`, because the platform records and answers and does not name an
application's status (ruling 2026-09-23). The stamped guide row `station:show:*` and `society.station`
are deleted; a page that wants a value the platform does not answer writes a `needs platform:` line
rather than deriving one. `unclassified` stays for a value that does not exist in the response. If the page needs a new element, that is a GUI order — say so in the delivery note; never a
workload-specific branch in the page.

### Step 10 — Delivery note

Build id and fingerprint; per changed file, the step above it serves; the boot lines to expect; the
sandbox tally; `needs platform:` lines; residues as `residue · reason · target seed`, or
`Pending: none`. **A seed without a note is reported, not accepted.**

---

## 2. What you may not do (each one has already cost a week)

| forbidden | why | do instead |
|---|---|---|
| branch on `kind == "station"`, on a society name, on "is this a lab" | every workload adds a branch; the driver becomes a list of exceptions | declare `duty` / `effect`; the driver reads the declaration |
| name a bench after a society, or assume `workflow=main` | the shelf failed on exactly this | the declaration names the bench and the workflow |
| a second scheduler (a daemon with its own timer) | two clocks, two admissions, two counts of what ran today | `trigger` on the workload; the daemon's logic becomes steps |
| a private record type or a private counter | invisible to `lens`, `as_of`, retention; three "today" numbers | Sets and observations; counts are reads |
| a state as a string, a reason as free text | not comparable, not countable, drifts | ids from the lexicon; Set membership |
| compute a state in a viewer | two pages, two rules, and the server serves neither | the server writes the membership; pages render it |
| a system identity over the transport | refused `-32001`; the registration silently never happened | provisioning in-process as admin |
| an operator command to produce derived or provisioned state | the seed must deploy alone | provisioning at boot from declarations |
| `debug`-level skips | invisible no-ops | INFO with a reason id |
| an eval that passes on the gap | the gap becomes permanent | assert the closure |
| rewrite meta to change a fact (aspect, status) | history lost | add a membership; end the old one on the clock |
| keys, prompts or texts in an atom | credentials never in the graph | counts and ids; keys via `llm.key` |
| a composite score | ranks across frames, hides the vector | one key per rank, grouped by frame |

---

## 3. The checklist (copy into the delivery note, tick each)

```text
Meaning
[ ] every state / reason / family id defined in the lexicon (nsdef), verify_lexicon --all PASS
[ ] no string literal of a state or reason in code (grep)
Declaration
[ ] one file app/config/workbench/workloads/<slug>.json: bench, workflow, society, trigger, duty,
    effect, appetite, budget, pins
[ ] key <bench>/<workflow> used everywhere (ledger, guide, Health, room)
[ ] room derived from the slug; no repo path in a declaration
Template
[ ] app/config/workbench/<bench>/templates/<slug>.ak with #!params; every op exists; effectful ops
    only under effect=publish; no literal state or reason in a step
Society
[ ] roles declared; offers resolved to the cast that speaks; chairman and scribe named, neither
    a speaking cast; admin identities added by provisioning
Provisioning
[ ] boot logs [bench] provisioned workload=… once per workload; a second boot logs unchanged
[ ] fresh data/ + boot reproduces everything; no operator command
[ ] a bad declaration fails at boot with the field / reason id
Run
[ ] cronon.executions lists one coordinate per step with executes / rehearses
[ ] observations carry their coordinates; source.trace shows them
[ ] publish: admission line, settle line, state Set moves, guide row has state/reason/airing
[ ] ONE number for "runs today" across guide / Health / pool
Gates
[ ] a refusal writes a state + reason id; a continuous duty is never unscheduled
[ ] effectful step rehearsed in thought mode; executes only under a grant with until=
Evals
[ ] the conformance eval PASSes on this declaration
[ ] no eval asserts a gap
Viewer
[ ] #bench/<slug> renders from generic reads; GUI order filed if an element is missing
Retirement
[ ] old ops forward or -32601; no second writer; [port] line
Note
[ ] delivery note: files by owner → steps, boot lines, tally, needs platform:, residues or
    Pending: none
```

---

## 4. Worked examples

Each is a cookbook entry that walks the ten steps on a real, shipped thing:

- **A studio** — [`../cookbook/workload-thinkers-shelf.md`](../cookbook/workload-thinkers-shelf.md):
  `duty: continuous`, `effect: publish`, a source pack, three roles, five template steps, a room.
- **A research bench** — [`../cookbook/workload-research-bench.md`](../cookbook/workload-research-bench.md):
  `duty: best_effort`, `effect: execute`, on demand, no room. The same shape with the broadcast
  parts absent — which is the claim this manual is making.
- **A programme with no corpus** — [`../cookbook/workload-no-corpus.md`](../cookbook/workload-no-corpus.md):
  reading the graph's own atoms as the episode, and what a workload does when its source has not
  arrived yet. Also the arithmetic that keeps a new workload from overrunning the day's ceiling.
- **An effect that leaves the building** — [`../cookbook/workload-external-channel.md`](../cookbook/workload-external-channel.md):
  the AI News Station posting to X. No model call (`appetite` 0), no spoken role, no room —
  the channel and the programme it republishes are PINS, so a second channel is a second
  declaration rather than a second code path. Read it for three traps it walked into: sharing
  another workload's society (which silently unschedules that one), `boot: false` on a workload
  that must still run on its cadence, and consent as a person's decision no boot supplies.

---

## 5. Bugs of September, by the rule they broke

| bug | rule |
|---|---|
| set forward-enumeration invisible to `s.ls` | §0.1 — Sets are the read path, not a private index |
| leaderboard needed an operator re-mint | Step 5 — derived state is produced by the write |
| studio registration as a system identity over the transport | §2 — provisioning in-process as admin |
| `since` moving per retry; back-off held in memory | §0.8 — durable state, one meaning |
| the programme key taken from `data.program` | Step 2 — the key comes from the declaration |
| `spent_calls` counting runs | §0.1 — one source, derived totals |
| states as constants nobody used; rooms deriving state browser-side | §0.8 + Step 9 |
| `bench 'studio_shelf' has no workflow` | Step 5 — provisioning writes the workflow on the declared bench |
| studios "left alone" by an eval | Step 8 — evals assert closures |
| three "today" counts | §0.1 — one read |
| a daemon running at 188 s against a declared 1800 s | §2 — one clock, from the declaration |
| a second workload declaring the first's society, which unscheduled it | Step 4 — the society a workload IS is exclusive; the one it READS is a pin |
| `boot: false` on a workload that then never ran on its cadence | Step 6 — `boot` is "is it scheduled at all?", not "does a deploy fire it?" |
| a turn the feed refused, recorded `aired=1` | Step 7 — the record and the feed are one claim, so a refusal is a standby with a reason |
| a scripts/ move that left every script's project root one directory short | Step 7 — run the thing, do not read the diff |
| the portal answering `Akashic Kitchen` to any host with the word in it | §A21 — no `if` on a name; a site declares its own |
