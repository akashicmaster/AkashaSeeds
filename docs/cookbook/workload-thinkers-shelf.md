# Cookbook — a studio: The Thinker's Shelf

A worked example of the ten steps in
[`../developer/implementing-a-workload.md`](../developer/implementing-a-workload.md), on a real
programme that ships. This is a **workload with `duty: wb:duty:continuous` and `effect: publish`** —
which is all a broadcast programme is.

What it does: once a day it reads a short passage from a 19th-century bibliography, lets a listener
ask the question an ordinary listener would ask, and lets a commentator answer it and open one door
into the archive. Three voices, five turns, one model reservation.

Everything below is in the repository. Nothing in this entry is illustrative.

---

## Step 1 — The meaning

Two vocabularies already existed and were reused rather than extended:

- `app/ontology/station/programme_state.ak` — the four states a registered programme can be in, and the
  reasons a standby carries. The code compares against these ids, never against a string.
- `ontology/workbench/duty.ak` — `wb:duty:continuous` and `wb:duty:best_effort`.

The programme's own material is a pack, `app/ontology/shelf_dibdin/` — the passages as atoms, gathered
into the episode Set `shelf:dibdin:passages:ep1`.

```bash
python scripts/gen_lexicon.py && python test/verify_lexicon.py --all
# RESULT: PASS — every used relation and namespace is defined, and every vocabulary id
# the code compares against exists as an atom.
```

## Step 2 — The declaration

`app/config/workbench/workloads/thinkers_shelf.json`. The frozen part of it:

```json
{"bench": "wb:studio_ai", "workflow": "thinkers_shelf",
 "society": "studio_ai/thinkers_shelf",
 "trigger": {"boot": true, "then": "daily:21:00Z"},
 "duty": "wb:duty:continuous", "effect": "publish",
 "appetite": {"llm_calls_per_run": 15, "weight": 0.1},
 "budget": {"per_day": 2, "max_wall_s": 900, "max_steps": 500},
 "pins": {"episode_set": "shelf:dibdin:passages:ep1",
          "work": "shelf:dibdin:work:library_companion"}}
```

Read it field by field, because every one of them is load-bearing:

- **`bench` + `workflow` make the key**, `studio_ai/thinkers_shelf`. That one string is the
  accounting key at the model gate, the guide's row key, the key in Health and in the pool ledger.
  It never comes from a caller.
- **`trigger.boot`** is why a deploy airs. Without it the hours between a deploy and 21:00Z are a
  blank room, and a visitor in another time zone meets silence. `then` continues the schedule.
- **`budget.per_day: 2`** is how often it may run — and therefore the guide's denominator. It used to
  be a separate `daily_budget: 24` sitting beside a `runs_per_day: 2`, so the guide reported today's
  count against a ceiling nothing enforced. One number.
- **`appetite.llm_calls_per_run: 15`** is an ESTIMATE, not a knob. Admission holds that many calls
  from the day's pool before the run starts; the gate measures the real figure and uses it once it
  has five airings. The declaration stays as written.
- **`pins`** are what the template's steps resolve against. The episode is a Set in the graph, so the
  template never names a passage.

The rest of the file is the society (topic, category, the programme identity that owns the casts),
the moderator, the capability offers, and the three role contracts. A workload is **one file**.

The room is not in it: it is derived from the slug — `thinkers_shelf` → `/station/thinkers-shelf/`.

## Step 3 — The template

`app/config/workbench/studio_ai/templates/thinkers_shelf.ak`:

```text
#!params program=studio_ai/thinkers_shelf
society.air program=$program role=Reader source=next
society.air program=$program role=Listener source=current last=feed:last
society.air program=$program role=Commentator source=current last=feed:last
society.air program=$program role=Listener source=current last=feed:last
society.air program=$program role=Commentator source=current last=feed:last
```

Five lines, and the interesting thing about them is what is **not** there.

No passage is named. `source=next` means *the next passage of the episode with no AIRED record*;
`source=current` means *the one the last aired turn worked from*; `last=feed:last` means *the
previous aired line, read off the space's own feed*. The cursor is **derived from the record**, so a
crash or a re-run cannot desynchronise it, and there is no second store to keep in step.

A standby does not consume a passage. A turn the model failed to produce has not read anything, and
letting it count would lose that page for good — the programme would silently drop a page to a rate
limit.

No step writes an atom. `society.air` forwards to the station bench's `air` family
(`station.air.turn`), which produces the turn behind the one model gate and speaks it through the one
feed write (`society.say`).

## Step 4 — The society

`studio_ai/thinkers_shelf`, with three speaking roles and two that never speak:

| role | turn | may | must not |
|---|---|---|---|
| Reader | read | select a short passage, read it faithfully, hold the page anchor | explain at length, guess the author's intent, join the discussion |
| Listener | question | ask what a passage means, say plainly that something is not understood | answer its own question, perform expertise |
| Commentator | explain | answer directly, give context, open ONE door | state an uncertain reading as settled, blur source fact and interpretation |
| Producer | — | chairman: holds responsibility | speak |
| Scribe | — | keeps the record | speak |

The `may` / `must_not` lists are not decoration: they are compiled into the role's system prompt, so
an LLM is handed its role's turn, its allowed strata and its depth limit — never free conversation.

Producer and Scribe do not speak **by construction**. Arming auto mode rebinds the moderator agent's
controlling client; a speaking cast in that position would be taken out of the programme's own hands.

## Step 5 — Provisioning

Nothing above is a command anyone runs. At boot the provisioning pass makes the declaration true:
the group, the programme identity, the society, the casts, the grants, the bench, the cycle on that
bench, the moderator armed from `trigger` and `budget`.

It **converges** — it does not create-if-absent. The distinction cost two days: the society persists
while the workflow entries are consumable, so a boot that skipped because "it is already armed" left
a bench with no workflow at all, and the programme reported a tripped breaker for a missing
precondition. `station:reason:not_provisioned` exists so the two can never be confused again: one is
cured by a boot, the other by a code change.

## Step 6 — The duty

`wb:duty:continuous`, and it is declared rather than inferred from this being a broadcast. What it
buys: any gate that stops the programme writes a state and a reason; the breaker never unschedules
it; a boot run that aired nothing still owes an airing, and is retried rather than deferred to
tomorrow.

An operational payroll run declares exactly the same thing and gets exactly the same guarantees. A
research bench declares nothing and gets `best_effort` — see the companion entry.

## Step 7 — Reading the run back

```bash
akasha> station.air.ls name=studio_ai limit=10     # what aired, with provider and model per turn
akasha> workload.status key=studio_ai/thinkers_shelf   # last run + reason, gate, next_at, spent_today
akasha> society.feed society=studio_shelf/reading_room limit=10
akasha> cronon.executions bench=studio_ai branch=main
```

Every turn is on the record with the **exact provider and model** that produced it — including the
ones that stood by, which carry their reason. That is the evidence trail: you can tell what a model
wrote from what the graph wrote.

## Step 8 — The check

```bash
python app/test/station_workload_decl_eval.py    # the user half: shape, key, room, template, offers
python app/test/station_air_turn_eval.py         # one turn, end to end, through the one gate
python app/test/station_deploy_airs_eval.py      # a fresh cell provisions and airs with no operator
```

The conformance eval (`workload_conformance_eval`) is the platform's and arrives with seed A; it is
where the two halves meet.

## Step 9 — The room

`app/archives/station/thinkers-shelf/` renders **served values only**:

| cell | read |
|---|---|
| state · reason | `society.station` → `state`, `reason` (vocabulary ids; the sentence comes from `r id=<id>`) |
| today / daily budget | `society.station` → `today`, `daily_budget` |
| model calls today | `society.station` → `llm.spent_today` over `calls_per_run × daily_budget` |
| last airing | `society.station` → `airing` |
| the airing record | `station.air.ls name=studio_ai` |
| the live feed | `society.broadcast.live society=<gid>/<space>` |

The page computes none of it. A value the response does not carry shows as `unclassified`; a
registered programme the server sent no state for shows `state missing (server)`, which is a defect
report, not a fallback. `python app/test/station_room_state_eval.py` holds all of that in a real browser.

## Step 10 — What is still owed

- The society moves to `studio_ai/thinkers_shelf` (it is registered under `studio_shelf/reading_room`
  today) with seed A's provisioning — re-registering orphans the existing feed, so it waits.
- `rebroadcast` is not yet written between airings, so a room replays the last episode without the
  guide saying that is what it is doing.

---

## The thing to take away

A broadcast programme is a workload with two fields set. There is no station subsystem: the same
declaration, the same template, the same driver, the same recorder and the same conformance check
serve a payroll run and a research sweep. If a new programme needs a branch anywhere, **the branch
is the bug**.
