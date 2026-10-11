# Cookbook — a research bench: `research`

The companion to [the studio entry](workload-thinkers-shelf.md), and the reason it is worth reading
second: **this is the same shape with the broadcast parts absent.** Not a different subsystem, not a
different driver, not a "lab mode" — the same declaration, the same bench, the same recorder, with
`duty` and `effect` set differently and no room.

If the two entries had needed different machinery, the workbench design would be wrong.

What it does: it records research chunks — notes with provenance — on a public bench, on demand,
for a research society. No schedule, no model calls, no audience.

---

## Step 1 — The meaning

Nothing new. The research bench uses the note and publication families that already exist, and the
existing link vocabulary (`derived_from`, `evidenced_by`, `supersedes`). A bench that needed a new
link kind would need a design line first — this one did not.

## Step 2 — The declaration

`config/workbench/workloads/bench_research.json`:

```json
{"world": "default",
 "group": "research-lab",
 "society": {"name": "research", "kind": "cowork", "identity": "open", "public": false},
 "bench": {"name": "research", "kind": "research", "public": true},
 "roles": {"moderator": "Recorder", "observer": "system.observer"},
 "grants": {"Recorder": ["operator:note", "operator:publication", "decide"]},
 "workflows": [], "sweeps": [], "sources": []}
```

This is the **older bench shape**, and it is shown as it is rather than as it will be, because a
cookbook that shows an aspiration teaches the aspiration. In the workload shape it reads:

```json
{"bench": "wb:research", "workflow": "board",
 "society": "research-lab/research",
 "trigger": {"on_demand": true},
 "duty": "wb:duty:best_effort", "effect": "execute",
 "appetite": {"llm_calls_per_run": 0, "weight": 0.1},
 "budget": {"per_day": 0, "max_wall_s": 300},
 "pins": {}}
```

Compare it with the studio's, field for field. Only four values differ, and each difference is the
*absence* of a broadcast property rather than the presence of a research one:

| field | studio | research bench | why |
|---|---|---|---|
| `trigger` | `boot` then `daily:21:00Z` | `on_demand` | nobody is waiting in a room |
| `duty` | `wb:duty:continuous` | `wb:duty:best_effort` | stopping to be examined after repeated failure is CORRECT here |
| `effect` | `publish` | `execute` | it leaves no trace outside the world |
| `appetite` | 15 calls a run | 0 | it calls no model |

`duty` is the one to dwell on. `best_effort` is not a weaker promise made grudgingly — it is the
right behaviour for an experiment. A research bench that keeps retrying a failing run is burning a
researcher's afternoon on a result nobody will trust; one that stops and waits is doing its job. The
driver is told which of the two this is, and never guesses from the bench's `kind`.

## Step 3 — The template

`config/workbench/research/templates/board.ak` would hold the board's steps, and today the bench has
`"workflows": []` — it is driven by direct calls (`research.chunk`, `research.publish`), not by a
schedule. That is a legitimate state for a workload: **`on_demand` means the trigger is a person.**

When it does get a template, it obeys the same rules: `#!params`, no loops, every step an existing
op, and no step writing an atom by hand.

## Step 4 — The society

`research-lab/research`, `kind: cowork`, one role that matters:

- **Recorder** — the moderator, granted `operator:note`, `operator:publication` and `decide`.
- **system.observer** — the observer, so every act has a witness.

Note that the research society is `public: false` while the **bench** is `public: true`. That pairing
is deliberate and is the usual one for research: the workspace is closed, the record is open. A guest
can read what was observed and cannot see the deliberation.

## Step 5 — Provisioning

Identical mechanism: at boot the generic provisioning pass stands up the group, the society, the
bench and the grants from this file, idempotently, re-applied on a new build. A bench also
auto-creates on the first `research.chunk` for any lab, so a lab with no config file still records
rather than dropping the note.

## Step 6 — The duty in practice

Because it is `best_effort`, the driver owes it none of the three continuous guarantees. In exchange
it is allowed to do the thing a programme must never do: **stop**. A repeated failure may take it off
the schedule until someone looks, and that will not be reported as an outage, because nothing is on
the air.

## Step 7 — Reading it back

```bash
akasha> bench.info name=research
akasha> learning.runs name=research
akasha> cronon.executions bench=research
```

The same reads as the studio. `bench.info` returns the bench's `status` — `active`, or `retired`
after `bench.retire`, which **deletes nothing**: the bench and its observations stand, and the read
says so.

## Step 8 — The check

The conformance eval is what both entries end at, and it is the same eval. Until seed A brings it,
the research bench is covered by `app/test/labo_world_model_eval.py` and the Source Viewer's own
`app/test/labo_source_gui_eval.py`.

## Step 9 — The viewer

`#bench/research` in the Source Viewer — the same page as every other bench, with no
research-specific branch. An empty bench renders its sections empty: **no probe line**, because
`not on this server yet` belongs to a read that is ABSENT, and a read that answers empty has
answered. An empty claims Set renders three zeros, not a shrug.

## Step 10 — What is owed

- The declaration is still in the older per-bench shape; it moves to the workload shape with seed A.
- `wb:plants_lab` and `wb:studio_shelf` read `status=retired` and keep rendering, which is the
  correct treatment of a retired bench and is worth seeing in the viewer.

---

## The thing to take away

Read the two declarations side by side. The studio's extra weight is entirely in four values — a
schedule, a duty, an effect, an appetite — and the machinery underneath them is not aware which kind
of thing it is running. **That is the claim the workbench makes, and these two files are the test of
it.**
