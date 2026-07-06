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
