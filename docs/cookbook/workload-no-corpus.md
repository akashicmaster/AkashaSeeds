# Cookbook — a programme with no corpus: The Art Explorer and The Plant Geek

The third entry, and the one about **sources**. The [studio entry](workload-thinkers-shelf.md) reads
a corpus that was transcribed, packed and shipped: 19th-century passages, each with a page anchor. Most
programmes will not have that, and should not have to.

These two are the other case. One reads **the graph's own atoms** — no corpus, nothing transcribed,
the Set is the episode. The other has no source at all yet, is switched on anyway, and says so.

Both were declared on 2026-09-17 and ran for the first time on 2026-09-21.

---

## Step 1–2 — What changes in the declaration: almost nothing

Beside the Thinker's Shelf, the Art Explorer's declaration differs in the values you would expect —
a different slug, topic, time of day, three differently-named roles — and in exactly one thing that
matters here:

```json
"pins": {"episode_set": "ontology.art_movements"}
```

That is a Set the **`art` ontology pack already builds**. Nothing was written for this programme:
the pack defines painting movements with their periods, places and techniques, and the Set that
holds them is the episode. `art` is tier B, so it is bundled everywhere and autoloaded on the
thesaurus and service tiers — which is where the station runs. On a plain seeds cell an operator
opts it in with `onto.pack.enable art`.

The Plant Geek's is the same shape pointing at a pack that does not ship:

```json
"pins": {"episode_set": "bio:plants:field_guide:ep1"}
```

## Step 3 — The template is the same five lines

```text
#!params program=studio_ai/art_explorer
society.air program=$program role=Curator source=next
society.air program=$program role=Visitor source=current last=feed:last
society.air program=$program role=Explorer source=current last=feed:last
society.air program=$program role=Visitor source=current last=feed:last
society.air program=$program role=Explorer source=current last=feed:last
```

Present → question → explain, one follow-up, one door. That the shape repeats is the point: a second
programme needing a second shape would have meant the first was a special case.

## The mechanism this entry is about — two shapes of episode entry

`source=next` means *the next entry of the episode with no AIRED record*. What an "entry" is depends
on what the pack wrote, and there are exactly two shapes:

| the atom's body | what it is | the anchor |
|---|---|---|
| **JSON** with `text`, `book`, `section`, `anchor.page` | a transcribed PASSAGE — someone typed it out of a book, and a listener may want the page | built from the fields: `Dibdin · I · p.iii` |
| **plain text** | an ordinary ontology atom — its DESCRIPTION *is* the record, and there is no page to return to | the atom's own alias: `art:movement:baroque` |

The second shape is what lets a programme read the graph directly. Note what the anchor rule buys:
in both shapes, the string the turn RECORDS as its source and the string the episode list carries are
the same string — which is what lets the cursor be derived from the record rather than stored.

One consequence worth stating, because it is invisible until it bites: a **standby does not consume
an entry**. A turn the model failed to produce has not read anything, and letting it count would skip
that entry for good — the programme would silently lose a page to a rate limit.

## Step 5–6 — Provisioning and duty

Identical to the reading room. At boot, from the declaration: group, programme identity, society,
casts, grants, bench, the cycle on that bench, the moderator armed. Both declare
`wb:duty:continuous`, so any gate that stops them writes a state and a reason, the breaker never
unschedules them, and a boot run that aired nothing still owes an airing.

## Step 7 — What you see when it runs

The Art Explorer:

```bash
akasha> station.air.ls name=studio_art limit=10
#  source=art:movement:baroque   provider=mistral  model=mistral-small-latest  aired=1
akasha> society.feed society=studio_art/gallery limit=6
```

The record names the **atom** it read, so a listener can go straight back to it in the graph — the
plain-text equivalent of a page reference.

The Plant Geek, on every current cell:

```bash
akasha> workload.status key=studio_ai/plant_geek
#  last.reason=station:reason:waiting_source   (gate, next_at and spent_today beside it)
```

## Why switch on a programme that cannot air?

Because *a declared wait is information and silence is not*, and because **it costs nothing**: a turn
with nothing to read makes no model call at all. The programme provisions, registers, and shows a
state with its reason in the guide, which is what makes it verifiable the moment a deploy lands. The
day the pack loads, it starts airing with no further change.

The alternative — pointing it at some Set that exists so it *looks* alive — is the one thing that
must not happen. Its Geek role also forbids foraging, edibility and medicinal advice outright: a wrong
word about a plant is not a wrong reading of a book, and a listener who eats something on a
broadcast's word is the failure mode the contract is written against.

## Step 8 — The check, and the arithmetic that makes switching on safe

```bash
python app/test/station_new_studios_eval.py
```

It holds: both are driven; both provision with no operator; the Art Explorer resolves a plain-text
atom and airs under its declared contract; a second `next` moves on; the Plant Geek stands by with a
reason and spends nothing; the reading room's JSON passages are unaffected.

And one check that is not about these two at all:

> **Σ(appetite × per_day) over every programme fits the provider's daily call ceiling**, with a 90%
> headroom bound — plus a per-programme check that the appetite **equals its template's step count.**

An appetite is what admission RESERVES before a run. The declarations asked for 15 and 12 calls
against templates of five steps, because they were written before the cycle was data. One
`society.air` step is at most one model call, so the number is now *countable*, and a programme
holding three times what it spends is the mechanism behind a refusal while the cap looks empty.

| programme | appetite | × per day | = calls/day |
|---|---|---|---|
| news_show | 3 | 48 | 144 |
| thinkers_shelf | 5 (was 15) | 2 | 10 |
| art_explorer | 5 (was 12) | 2 | 10 |
| plant_geek | 5 (was 12) | 2 | 10 |
| | | **total** | **174 of 220** |

Switching a fifth programme on can no longer overrun the cap quietly. The eval says so here, rather
than a deploy discovering it at 04:00Z.

---

## The thing to take away

A programme does not need a corpus. If the meaning is already in the graph, the Set is the episode —
and if it is not there yet, say so in the guide and spend nothing until it is. Both are cheaper than
a programme nobody can watch.
