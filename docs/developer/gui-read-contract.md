# The GUI read contract — a page renders, it does not decide

**Audience: the development user, writing anything under `app/archives/`.** This is the rule every
Akasha page obeys, why it exists, and the three markers that keep a page honest about what it does
not know.

One sentence: **a page renders what the server served, and computes nothing.**

---

## 1. Why this is a rule and not a preference

A page that derives a value is a second implementation of a decision the server already makes. Two
implementations drift, and the drift is invisible: the page keeps rendering something plausible.

The case this was written from. Every station room used to work out a programme's state in the
browser, from `skipped`, `last_post_at` and `next_burst_at` — a guess about the programme, dressed
as a report of it. It was wrong in the worst possible direction: a studio that had been refused by
its model provider for a fortnight read **`warming up`**, because the browser's rule for "recently
started" and the server's rule for "has aired" were not the same rule. Nobody was lying; there were
simply two rules, and the readable one was the wrong one.

The same week, a room read `station.air.ls`, got 142 real airings back, and used them to append a
number to a caption. The value was in its hands and it threw it away.

So:

- **the server decides and writes** — a state is a Set membership, a reason is a vocabulary id;
- **the page renders** — it may format, order, group and lay out; it may not conclude.

Formatting is not computing. Turning `1758434940` into `2026-09-21 06:49Z`, or `spent_today` and
`calls_per_run × daily_budget` into `30/30`, is presentation of served numbers. Deciding *from* those
numbers that the programme is fine is not.

## 2. The three markers

A page has to say three different things when a value is not simply there, and confusing them is how
a defect becomes invisible.

| marker | means | when |
|---|---|---|
| the served value | this is what the server says | the response carries it |
| `unclassified` | **this value does not exist** in the response | the read answered, and there is no such value to report |
| `state missing (server)` | **a defect, and it is the backend's** | the row is REGISTERED and the server sent no state for it |

`unclassified` is not a polite way of saying "unknown" — it is a statement that the value does not
exist. A studio the guide does not carry has no state, and `unclassified` is true of it. A
*registered* programme always has a state, so `unclassified` there would be false, and filling one
in would be worse. The page reports the gap and does not close it.

There is a fourth thing a page must be able to say, and it is about itself:

> this page could not complete its reads

Not *"the bench is not answering"* — that is a claim about the server that the browser cannot make.
A dropped connection, a blocked storage read and a server fault look identical from here. Say what
you know, and **never wipe a panel that already rendered**: a stale-but-true list beats an untrue
explanation.

## 3. The probe line, and the read that answers empty

`not on this server yet` belongs to a read that is **ABSENT** — a method this build does not have.
A read that answers with an empty list has answered, and an empty bench renders its sections empty:
no run list, three zero counts on an empty claims Set, and no probe line anywhere.

An empty answer is information. A probe line on top of it says "we could not ask", which is untrue
and sends a reader looking for a deployment problem that is not there.

## 4. Vocabulary in, sentences out

`state` and `reason` arrive as ids — `station:state:standing_by`, `station:reason:provider_429`. A
page never spells the English for one. It reads the definition once per page:

```js
soft('r', { id: id })     // → the atom's content: "standing by — registered and not playing…"
```

and renders by the project's display rule, most readable first:

**full spelling → alias → (never) the raw key.** The head of the definition (before the em dash) is
the chip's word; the whole sentence is the hover; the id itself appears only when no atom answers,
and that is a lexicon gap worth reporting.

This is what makes a new reason work with no page change. When `budget_calls` and `budget_tokens`
were added, no room was touched: the ids arrived, the definitions answered, and the chips read
`standing by · budget calls`. A page with a local reason table would have rendered all three as
whatever its fallback was — which is exactly what a closed `if/elif` list did on the server side, and
why every reason now passes through untranslated.

## 5. No literal bench or programme name in a page

Outside fixture data, a page does not name a bench, a programme or a society. It renders the rows it
is served, keyed by what they carry:

- the row key is `program` (`<bench>/<slug>`), as served;
- the link to a room is the served `room` — a **public path**, never a repo path (a repo path
  renders as a broken link, resolved against whatever page is reading it);
- a studio is picked from the served list, not matched against a hardcoded id.

A page that names one programme will need editing for the next one, and the edit will be forgotten.

## 6. Guests write nothing

Every archives page runs as a guest session and calls **read** ops only. A page never calls a write
op, never provisions, never re-mints. If a page seems to need a write, the value it needs should have
been written when the thing happened — that is a backend order, not a page feature.

## 7. What to do when a read is missing

Do not compute it. Write one line in the delivery note:

> `needs platform: <what> — <why> — <the read or call you expected>`

and render the marker in the meantime. A page that fills a gap makes the gap permanent, because
nothing is broken any more.

## 8. The evals that hold this

| eval | holds |
|---|---|
| `app/test/station_room_state_eval.py` | the static grep (no derivation left in any room) **and** the rendered half — every room and the lobby drive a real browser against a mocked read, render the vocabulary's word, mark a stateless registered row as a defect, keep `unclassified` for the one case where no value exists, and render the airing record as served. *The read the rooms mock is `society.station`, which is deleted (ruling 2026-09-23): the rooms move to `workload.status` + `society.feed.read` and this row moves with them — the user half of that ruling, named in the 2026-09-23 backend note.* |
| `app/test/labo_source_gui_eval.py` | the Source Viewer: the programme table from the served contract, a bench's `status` rendered as served (`retired` included), no probe line on a read that answered empty, two builds of a capability both rendered with the stale one muted |
| `app/test/ssr_seo_eval.py`, `test/render_gate_eval.py` | the server-rendered atom pages and the render gate |

Both page evals need `playwright`; they drive the real file, not a DOM shim, because a rule about
rendering that is checked without rendering is a rule about source code.

## 9. The checklist

```text
[ ] no value in the page is derived from other values (grep for the derivation you removed)
[ ] every state / reason id is resolved through `r id=<id>`, never spelled
[ ] `unclassified` only where the value does not exist in the response
[ ] the defect marker where a registered row lacks a value it must have
[ ] the probe line only where a read is ABSENT, never where it answered empty
[ ] a failed read says the PAGE could not complete, and does not wipe what rendered
[ ] no literal bench / programme / society name outside fixture data
[ ] the room link is the served public path
[ ] read ops only
[ ] a fixture for every read, in both states (present and absent), and the eval drives them
```
