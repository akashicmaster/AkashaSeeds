# Cookbook — contents

Working examples. Every entry walks a **real, shipped thing** in the order of the steps in
[`../developer/implementing-a-workload.md`](../developer/implementing-a-workload.md): the
declaration, the template, the pack, the room, the conformance run, and the reads a page uses.

An entry ships with its example or it does not ship. If you can read an entry here, the thing it
describes is in the repository and you can run the commands in it.

---

## Workbench — adding something that runs

The workbench runs research, broadcast and operational processes on **one** driver. These entries
are meant to be read in order, and the second one is the argument: it is the first one with the
broadcast parts absent, not a different subsystem.

| entry | what it is | duty · effect |
|---|---|---|
| [A studio: The Thinker's Shelf](workload-thinkers-shelf.md) | a daily reading programme — three voices, five turns, one model reservation | `continuous` · `publish` |
| [A research bench: `research`](workload-research-bench.md) | research chunks with provenance, on demand, no audience | `best_effort` · `execute` |
| [A programme with no corpus](workload-no-corpus.md) | reading the graph's own atoms — and what a programme does when its source has not arrived | `continuous` · `publish` |
| [An effect that leaves the building](workload-external-channel.md) | the AI News Station posting to X — no model call, no voice, no room | `best_effort` · `publish` |

Read the first two side by side: their declarations differ in four values, and nothing underneath
them knows which kind of thing it is running — which is the claim the workbench makes, and those two
files are the test of it. The third is about **sources**: most programmes will not have a
transcribed corpus and should not need one. The fourth is about **effects**: where a workload's
work ends up is a pin, so reaching a new channel is a declaration, not a code path.

## Concept models and the graph

| entry | what it is |
|---|---|
| [Beginners guide](cookbook-beginners.md) | first steps at the CLI — write an atom, link it, explore |
| [LLM beginners](cookbook-llm-beginners.md) | the same, for a language model driving the CLI |
| [Chapter 0 — basic operations](chapter-0-basic-ops.md) | the operations everything else is built from |
| [Map: the ancient world](map-ancient-world.md) | a projection, not an image: place atoms stay in GEO |
| [Quadrant scatter](quadrant-scatter.md) | positioning a set by its own computed coordinates |
| [Brainstorm society](brainstorm-society.md) | external models as guests in a room, with the two consent gates |
| [Services](chapter-services.md) | running a bundled app beside the archives |

## Tracks

The three colour tracks are the guided path; the entries above are the reference.

| track | what it teaches |
|---|---|
| [Red](red/chapter-0.md) | the CLI, one command at a time |
| [Blue](blue/chapter-0.md) | concept models and the UI — design before implementation |
| [Green](green/chapter-0.md) | CSL and language models — growing the space |

---

## What belongs here

An entry is a cookbook entry when it walks a shipped example end to end. It is **not** a
specification (those live in `docs/developer/` and `docs/ontology/`) and **not** a design note.

Two standing rules, from the documentation principles:

- **Self-contained.** No "see ~" references inside the body. Everything you need to follow the
  example is on the page; references for advanced topics go at the end.
- **No economy of explanation.** Careful explanation and abundant examples beat a low page count,
  and the more invisibly a behaviour works — idempotency, first-wins, upsert — the more thoroughly
  it is written down.
