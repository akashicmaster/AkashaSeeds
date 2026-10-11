# Cookbook — a workload that leaves the building: the AI News Station on X

The fourth entry, and the one about **effects that reach outside the archive**. The three before it
all end in a room: a programme airs, the feed grows, a page renders. This one ends somewhere Akasha
does not own — a post on X, under an account a person is responsible for.

It is worth walking because almost nothing about it is special. It is a workload like the other
three: nine declared fields, a template of steps, a society, a duty. What it does *not* have turns
out to be the interesting part.

Declared 2026-09-21, replacing twenty functions and an op that lived in the platform.

---

## What it is not

Before the steps, the two things this workload does **not** do, because both are the reason it is
short:

- **It generates nothing.** No model call, no prompt, no role. The words it posts were written,
  gated, metered and sealed hours earlier, when the news show aired them.
- **It speaks into no society.** It has one — every workload does — but it never says a line there.

So it is a *republisher*: it takes something the archive already decided to say and carries it
somewhere else.

---

## Step 1–2 — The declaration, and the three fields that carry the whole difference

`app/config/workbench/workloads/news_show_x.json`. Beside the Thinker's Shelf, the differences are:

```json
"appetite": {"llm_calls_per_run": 0, "weight": 0.0},
"duty": "wb:duty:best_effort",
"pins": {"channel": "x", "program": "studio_ai/news_show"}
```

**The appetite is zero, and that is a real number, not a placeholder.** Admission RESERVES a
workload's appetite from the shared model-call pool before every run. A workload that reserves
five calls and spends none holds them away from the programmes that do spend — which is what a
refusal-while-the-cap-looks-empty actually is. This one spends nothing, so it asks for nothing.

**The duty is `best_effort`, not `continuous`.** A broadcast that goes quiet is an outage a
listener notices; a thread that was not posted is nothing anybody was waiting for, and the next
slot picks it up. The difference is not cosmetic: `continuous` means the failure breaker does not
unschedule the workload and a start-up run that produced nothing still owes a turn. Asking for that
here would mean a dead X API kept a workload in a state it could not leave.

**The pins name the channel and the programme.** The op that posts knows neither. That is the whole
mechanism of this entry: a second channel — a Mastodon account, a newsletter, a webhook — is a
second declaration with a different `channel`, not a second code path. Likewise a second programme
posting to X: change `pins.program`.

---

## Step 3 — The template is one line

`app/config/workbench/studio_ai/templates/news_show_x.ak`:

```text
#!params channel=x program=studio_ai/news_show
station.publish channel=$channel program=$program
```

There is one thing to do, so there is one step. The parameters come from the pins; the op reads the
programme's latest sealed, unposted turn, formats the reply chain, and posts it.

---

## Step 4 — It needs its own society, and this cost a bug

The declaration says:

```json
"society": "studio_ai/news_show_x"
```

It reads the news show's feed but **does not share the news show's society**, and the first draft
did. Here is why that failed.

Provisioning ARMS the society a workload declares: it admits the moderator casts there, writes that
society's automation policy, and sets its branch and schedule. Two workloads declaring the same
society means the second one provisioned overwrites the first's policy — so the news show came out
of a boot with `workflows: ['news_show_x']` and `trigger: manual`, and stopped being scheduled at
all. Nothing errored. The programme simply went quiet.

**The society a workload IS and the society it READS are different questions.** The first is the
`society` field and it is exclusive. The second is a pin.

---

## Step 5 — A workload that says nothing still needs a chairman and a scribe

```json
"moderator": {"chairman": "Producer", "scribe": "Scribe", "branch": "news_show_x"}
```

Arming `mode=auto` is authorising an autonomous act, and an autonomous act needs someone
accountable for it and someone keeping the record. That holds whether the act is a spoken turn or a
posted thread. Leave the block out and the society does not arm — the workload is declared, visible
in the guide, and never runs.

Note also that neither cast speaks. That is the property the two governance roles are supposed to
have everywhere; here it is simply obvious, because there is no speaking role at all.

---

## Step 6 — `boot: true` does not mean "fire at the world on deploy"

```json
"trigger": {"boot": true, "then": "every:14400s"}
```

This was written `false` at first, on what sounds like the careful reasoning: a deploy should not
throw a thread at the public before anyone has looked at it.

It is wrong, and in a way worth memorising. On this platform **`boot` is not "does a deploy fire
it?" — it is "is it scheduled at all?"**. A declaration with `boot: false` projects to
`trigger: manual`, and the driver never runs it on its `then` cadence. The workload would have sat
in the guide forever, correct-looking and inert.

The caution it was reaching for is already covered, by gates that name themselves:

| gate | when | reason id |
|---|---|---|
| nothing sealed yet | a fresh cell, no turn has aired | `station:reason:waiting_source` |
| already posted | the newest sealed turn went out last run | `station:reason:fresh` |
| not consented | the space is not flagged public | `station:reason:no_consent` |

A fresh deploy hits the first. A quiet one hits the second. Neither posts.

---

## Step 7 — Consent is a person's decision, and no boot supplies it

The op **refuses** unless the space is flagged public, and returns `station:reason:no_consent`.

This is the one gate that is not about correctness. Sending a feed out of the building is a choice
somebody makes, and the presence of this declaration is not that choice — it is only the intent to.
Somebody flags the space public, deliberately, and that is the consent.

`every:14400s` is four hours, about six threads a day, and `budget.per_day` is 6 to match. A failed
post does **not** mark the turn posted, so a retry is simply the next run.

---

## What it reuses, and what that proves

Nothing here is new machinery:

- the workload shape — the same nine fields;
- provisioning — the same boot, converging on the declaration;
- the guide row, the accounting key, the budget, the duty — all the same reads;
- the conformance eval — `app/test/workload_conformance_eval.py`, unchanged, which is the point of
  Step 8 in the manual: it asserts the closure, not one programme's habits.

What changed to allow it was a **pin**. The op posts to `pins.channel`, reading the programme from
`pins.program`, and neither is in its source. Before that, "post the AI News Station to X" was
twenty functions in the platform, driven by their own timer, opted in by whether a file happened to
exist on disk, with the cursor of what had been posted living beside the process.

Now the opt-in is this file's existence, the cadence is its trigger, and the cursor is a record on
the bench — which means it survives a restart, is visible in the airing record, and can be read by
anyone who can read the bench.

---

## The checklist, for this one

| step | here |
|---|---|
| 1 — meaning in ontology | the three `station:reason:*` ids the gates return |
| 2 — declaration | `news_show_x.json`; key `studio_ai/news_show_x` |
| 3 — template | one step, two params from the pins |
| 4 — society | its **own**, `studio_ai/news_show_x` |
| 5 — provisioning | nothing to run; the boot converges |
| 6 — duty | `best_effort` — a missed thread is not an outage |
| 7 — recorded run | the bench record carries the post; the turn is marked posted only on success |
| 8 — eval | the shared conformance eval, plus `app/test/station_publish_channel_eval.py` |
| 9 — viewer | no room of its own; it links to the news show's |
| 10 — note | `docs/handoff/frontend-port-2026-09-21.md` |

---

## Further reading

- The manual and the ten steps: [`../developer/implementing-a-workload.md`](../developer/implementing-a-workload.md)
- The first studio, with roles and a corpus: [`workload-thinkers-shelf.md`](workload-thinkers-shelf.md)
- A workload with no broadcast at all: [`workload-research-bench.md`](workload-research-bench.md)
- Reading the graph's own atoms as the episode: [`workload-no-corpus.md`](workload-no-corpus.md)
