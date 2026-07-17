# AKASHA User Manual

**Version 1.3 — June 2026**

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Core Concepts](#2-core-concepts)
3. [Getting Started](#3-getting-started)
4. [Quick Start: A Complete Workflow](#4-quick-start-a-complete-workflow)
5. [Shell Commands](#5-shell-commands)
6. [Kernel Commands Reference](#6-kernel-commands-reference)
   - [Memory](#61-memory)
   - [Links](#62-links)
   - [Aliases](#63-aliases)
   - [Navigation](#64-navigation)
   - [Sets](#65-sets)
   - [Notes](#66-notes)
   - [JCL Job Control](#67-jcl-job-control)
   - [System](#68-system)
   - [Contexa](#69-contexa)
   - [Jataka](#610-jataka)
   - [Session Instance Layer](#611-session-instance-layer)
   - [CSL — Concept Specific Language](#612-csl--concept-specific-language)
7. [Context References ($-syntax)](#7-context-references--syntax)
8. [Rel Normalization](#8-rel-normalization)
9. [Ontology: Innate vs Acquired](#9-ontology-innate-vs-acquired)
10. [JCL Batch Jobs](#10-jcl-batch-jobs)
11. [Groups and Scopes](#11-groups-and-scopes)
12. [Group Administrator Commands](#12-group-administrator-commands)
13. [Sharing Knowledge — Delegation Sets](#13-sharing-knowledge--delegation-sets)
14. [Roles and Permissions](#14-roles-and-permissions)
15. [Tips and Patterns](#15-tips-and-patterns)

---

## 1. Introduction

AKASHA is a **local-first semantic memory system** — a living graph of ideas, observations, and connections that grows alongside your thinking. Unlike traditional note-taking apps or flat databases, AKASHA organizes knowledge as a **graph-based memory mesh**: every piece of information is an **Atom** (a node), and Atoms are joined by typed **Links** (edges) that carry meaning.

AKASHA runs entirely on your local machine. There is no cloud account to create, no subscription to manage, and no network connection required. Your knowledge graph stays private, portable, and fast — whether you are in a university library, on a remote field expedition, or working offline on a long-haul flight.

The system is structured around two main components:

- **The Kernel** — the cognitive engine that stores atoms, resolves relationships, manages scopes, and runs background jobs.
- **The Shell** — the interactive command-line interface through which you communicate with the kernel via JSON-RPC 2.0.

Every command you type in the shell is translated into a JSON-RPC 2.0 request that passes through the **Gateway** to the Kernel. This clean separation means the same kernel can be driven by a local terminal, a remote portal, or an automated script.

### Two Ways to Give Instructions

**Shell commands** (covered in this manual) are short and efficient — designed for fast, single operations:

```
akasha/user $ w "Memory is a constructive process."
akasha/user $ ln $0 $1 @supports
```

**CSL** (Concept Specific Language) is an alternative that uses explicit `option=value` syntax — more readable, chainable, and suitable for complex multi-step work or AI-assisted knowledge entry:

```
csl> $atom = write text="Memory is a constructive process."
csl> link.create src=$atom.key dst="bartlett.finding" rel="@supports"
```

Both reach the same kernel. For new users, the **CSL interactive interpreter** (type `csl` at the shell prompt) is often an easier starting point. A full CLI ↔ CSL correspondence table is in §6.12.

> **→ CSL Manual:** [`docs/csl-manual.md`](csl-manual.md)

---

## 2. Core Concepts

### Atoms

An **Atom** is the fundamental unit of memory in AKASHA. It is a node in the graph containing a piece of text — a thought, a quote, a definition, a paragraph, or any free-form content. Each atom is identified by a 64-character hexadecimal key (its cryptographic hash) and can optionally carry a human-readable alias.

### Links

A **Link** is a directed, typed edge between two atoms. Links have:
- A **source** atom
- A **destination** atom
- A **relation** (`rel`) — a label describing the nature of the connection (e.g., `@causes`, `@leads_to`, `sys:is_a`)

Links can be reinforced over time, increasing their weight to reflect stronger associations.

### Scopes

Atoms live in **scopes** — access-controlled namespaces:
- **Personal scope** — private to the individual user
- **Group scope** — shared with members of a group
- **Collective scope** (`scope:sys:universal`) — visible to all users; home of the global ontology

Scopes behave like physical dimensions in the database. Atoms outside your scope are invisible during graph traversal — they exist as "dark matter" that does not interfere with your view.

### The Shell Prompt

When you launch AKASHA, you are greeted by a prompt like:

```
akasha/user $
```

This is your command line. Everything after the `$` is a command sent to the kernel (or handled by the shell itself).

---

## 3. Getting Started

### Launching AKASHA

If you have already germinated your local cell, start the shell with:

```bash
python akasha.py
```

You will see something like:

```
[Akasha] Soma is active. Accessing local neural pathways.

akasha/user $
```

### Your First Liveness Check

Confirm the kernel is running:

```
akasha/user $ ping
{"status": "ok", "message": "Kernel is alive."}
```

### Getting Help

Display the command reference table at any time:

```
akasha/user $ help
```

---

## 4. Quick Start: A Complete Workflow

This section walks you through a realistic end-to-end session: writing atoms, linking them, assigning aliases, diving into a node, and exploring the graph.

**Scenario:** You are a researcher studying the philosophy of memory. You want to capture three interconnected ideas and build a small knowledge cluster.

```
akasha/user $ ping
{"status": "ok", "message": "Kernel is alive."}

# Step 1: Write three atoms

akasha/user $ w "Memory is not a recording device. It is a constructive process that rebuilds the past from fragments."
{"id": "a3f7...c19e", "alias": null}

akasha/user $ w "Frederic Bartlett showed in 1932 that recalled stories drift toward the subject's cultural schema."
{"id": "b80d...44fa", "alias": null}

akasha/user $ w "This means two people can remember the same event in completely incompatible ways — both sincerely."
{"id": "cc29...08b2", "alias": null}

# $it now points to the third atom; $0, $1, $2 are the three atoms in reverse order.

# Step 2: Link them in sequence

akasha/user $ ln $2 $1 supports
akasha/user $ ln $1 $0 illustrates

# Step 3: Link the third atom back to the first as a consequence

akasha/user $ ln $2 $0 implies

# Step 4: Assign human-readable aliases

akasha/user $ al $2 memory.constructive
akasha/user $ al $1 bartlett.finding
akasha/user $ al $0 memory.incompatible

# Step 5: Define a conceptual hub that ties them together

akasha/user $ def reconstructive_memory
{"id": "d10a...77c3", "alias": "reconstructive_memory"}

akasha/user $ ln reconstructive_memory memory.constructive sys:is_a
akasha/user $ ln reconstructive_memory bartlett.finding sys:evidenced_by
akasha/user $ ln reconstructive_memory memory.incompatible sys:implies

# Step 6: Dive into the hub atom to see its full context

akasha/user $ look reconstructive_memory
--- Atom: reconstructive_memory ---
[Hub] reconstructive_memory

Signposts (links):
  --> memory.constructive       [sys:is_a]
  --> bartlett.finding          [sys:evidenced_by]
  --> memory.incompatible       [sys:implies]

# Step 7: Explore the graph by BFS from the hub

akasha/user $ exp reconstructive_memory 2
[Depth 0] reconstructive_memory
  [Depth 1] memory.constructive       (@supports --> bartlett.finding)
  [Depth 1] bartlett.finding          (@illustrates --> memory.incompatible)
  [Depth 1] memory.incompatible
  [Depth 2] ... (further neighbors)

# Step 8: View the tree structure

akasha/user $ tree reconstructive_memory 2
reconstructive_memory
├── memory.constructive [sys:is_a]
│   └── bartlett.finding [@supports]
├── bartlett.finding [sys:evidenced_by]
│   └── memory.incompatible [@illustrates]
└── memory.incompatible [sys:implies]
```

In a few minutes you have built a structured, navigable cluster of ideas linked by meaningful relations. This is the core loop of AKASHA.

---

## 5. Shell Commands

Shell commands are available **only in the interactive terminal**. They cannot be used inside `.ak` script files.

### `help`

Displays the full command reference table.

```
akasha/user $ help
```

### `exit` / `quit`

Ends the session and disconnects from the kernel.

```
akasha/user $ exit
Disconnected. Goodbye.
```

### `history [n]` — Command History

Shows the last *n* commands typed in this session (default 50). History is also saved to `~/.akasha_history` across sessions (requires the `readline` library).

```
akasha/user $ history 10
    1  ping
    2  w "Memory is a constructive process."
    3  al $it memory.constructive
    4  ln memory.constructive bartlett.finding @supports
    5  dive memory.constructive
    6  history 10
```

**History expansion** — re-run a previous command by reference:

```
akasha/user $ !!          → repeat last command
akasha/user $ !1          → repeat command #1 (ping)
akasha/user $ !-1         → repeat last command (same as !!)
akasha/user $ !-2         → repeat second-to-last
akasha/user $ !ln         → repeat last command starting with "ln"
```

When a history reference matches, the expanded command is echoed before execution:

```
akasha/user $ !!
  → ln memory.constructive bartlett.finding @supports
Link created.
```

### `onto.reload` / `onto.reset`

Two commands for ontology lifecycle management (LIBRARIAN role required). Both require an explicit confirmation argument to prevent accidental invocation:

- **`onto.reload confirm=RELOAD`** — soft reload: clears ontology sentinels, re-triggers the boot load sequence for all common and acquired ontology files.
- **`onto.reset confirm=RESET`** — hard reset: wipes all nucleus ontology data except DNA atoms, then performs a full reload. Use this when the ontology is in an inconsistent state.

```
akasha/user(su:librarian) $ onto.reload confirm=RELOAD
  [ont] ⚠  This will clear all ontology sentinels and re-run the full boot load.
  [ont] Proceeding...
  [ont] ✓ Reload triggered.

akasha/user(su:librarian) $ onto.reset confirm=RESET
  [ont] ⚠  DESTRUCTIVE: this wipes all nucleus ontology data (DNA preserved).
  [ont] Proceeding...
  [ont] ✓ Reset and reload triggered.
```

See the Admin Manual §9 for `onto.genesis.redo` and `onto.scope.drop`.

### `run <file>`

Submits a `.ak` script file as a **non-blocking JCL batch job**. The shell returns immediately with a job ID; the script runs in the background.

```
akasha/user $ run my_notes.ak
Job submitted: job_id=jcl-8841
```

You can then monitor progress with `job.st jcl-8841`.

### `<cmd> > <file>`

Redirects the JSON output of any command to a local file on your machine. Useful for archiving query results or exporting atom data.

```
akasha/user $ ls 20 > recent_atoms.json
Output written to recent_atoms.json
```

### `svc ls`

Lists all registered background services and their current status. Available to all authenticated users.

Columns: **name**, **status** (Active / Dead), **engine** (thread / uvicorn / httpd), **address or PID**, **uptime**.

```
akasha/user $ svc ls

  name                   status   engine   address / pid          uptime
  ────────────────────────────────────────────────────────────────────────
  http_portal            Active   thread   http://0.0.0.0:8000    42s
  cosmos_visualizer      Active   uvicorn  PID=12345               120s
```

The `http_portal` entry is the main JSON-RPC web gateway. Thread-based services show a URL; subprocess-based services show their OS process ID.

### `svc stop <name>`

Stops the named service. **Admin only.** Regular users receive a permission error.

```
akasha/user $ svc stop cosmos_visualizer
  ✓ cosmos_visualizer stopped
```

### `svc restart <name>`

Stops and restarts the named service. **Admin only.** For thread-based services such as `http_portal`, the old HTTP server is shut down cleanly and a new one is started on the same port.

```
akasha/user $ svc restart http_portal
  Restarting http_portal…
  ✓ http_portal restarted
```

> **Note:** `svc stop` and `svc restart` require admin or `su root` privileges. Attempting them as a regular user prints `Permission denied`.

---

## 6. Kernel Commands Reference

Kernel commands are the core language of AKASHA. They work both in the interactive shell and inside `.ak` script files.

### 6.1 Memory

#### `w <text>` — Write an Atom

Creates a new atom containing `<text>`. After writing, `$it` and `$0` are updated to point to this atom. Use triple quotes for multi-line content.

```
akasha/user $ w "The Silk Road was not a single road, but a network of overland and maritime routes."
{"id": "f3a1...9c42", "alias": null}

akasha/user $ w """
The city of Samarkand stood at the crossroads of these routes.
It was a meeting point for Chinese silk, Indian spices, and Persian glass.
"""
{"id": "7b2c...e301", "alias": null}
```

#### Background: Constituent-Word Weaving

Every time you write an atom (`w`), define a hub (`def`), name an atom (`al`), or add it to a set (`s.add`), AKASHA automatically queues a **Weaver** background job. The Weaver tokenises the text (or name/label) and creates `sys:refers_to` links from the atom to matching *protoword* atoms in the shared nucleus ontology, and records membership in `set:word:*` collections.

This means that even a plain `w "…"` immediately becomes part of the semantic graph — no manual `ln` to ontology atoms is required. The Weaver runs asynchronously (you won't see it in `job.ls` unless you look); it is never called twice for the same atom in the same context (the batch loader uses a separate path), and it never creates new protowords in the nucleus for client-space atoms — it only connects to what already exists.

**Practical consequence:** after writing two atoms about the same topic, `assoc` will surface connections between them through shared protowords — even without any explicit `ln` command.

#### `def <name>` — Define a Conceptual Hub

Creates a special hub atom and assigns it a global alias in one step. Use hub atoms as thematic anchors around which related atoms cluster.

```
akasha/user $ def silk_road_trade
{"id": "a09f...1d88", "alias": "silk_road_trade"}
```

#### `r <id>` — Remember an Atom

Recalls and displays an atom from memory. The `<id>` can be an alias, a `$ref`, or the full 64-character hex key.

> The name `r` stands for *remember*, not *read*. Akasha's metaphor is human memory — you are not fetching a file; you are bringing something back into focus.

```
akasha/user $ r silk_road_trade
[Hub] silk_road_trade

akasha/user $ r $1
"The Silk Road was not a single road, but a network of overland and maritime routes."

akasha/user $ r f3a1...9c42
"The Silk Road was not a single road, but a network of overland and maritime routes."
```

#### `rm <id>` — Remove an Atom

Permanently deletes an atom from the graph. Requires DELETE capability (available to atom owners and ADMINs).

```
akasha/user $ rm $0
Atom cc29...08b2 dropped.
```

> **Caution:** Deletion is permanent. Links pointing to the deleted atom become dangling references. Verify with `r <id>` before deleting.

#### `meta <id> <key> <value>` — Set Metadata

Attaches a metadata key-value pair to an atom. Useful for tagging atoms with source information, dates, or confidence levels.

```
akasha/user $ meta silk_road_trade source "Frankopan, The Silk Roads (2015)"
akasha/user $ meta silk_road_trade confidence high
akasha/user $ meta $0 language en
```

> **CSL equivalents:** `write text="..."` · `define name="..." description="..."` · `read id="..."` · `drop id="..."` · `meta.set id="..." key="..." value="..."`  
> **→ Full comparison table:** [§6.12](#612-csl--concept-specific-language) · [`docs/csl-manual.md §3`](csl-manual.md#3-csl-vs-shell-commands--a-complete-comparison)

---

### 6.2 Links

#### `ln <src> <dst> <rel>` — Create a Link

Creates a directed link from `<src>` to `<dst>` with relation type `<rel>`. Both src and dst accept aliases, `$refs`, or hex keys. The rel is auto-normalized (see [Rel Normalization](#8-rel-normalization)).

```
akasha/user $ ln silk_road_trade $1 sys:includes
akasha/user $ ln $1 $0 @preceded_by
akasha/user $ ln $0 silk_road_trade part_of
# "part_of" becomes "@part_of" automatically
```

**Multi-word names:** `src` and `dst` are positional — if either contains spaces, quote it. The final argument (`rel`) absorbs all trailing tokens, so it never needs quoting.

```
akasha/user $ ln "first kiss" apple taste:sweet   → OK, src quoted
akasha/user $ ln apple "first kiss" taste:sweet   → OK, dst quoted
akasha/user $ ln $0 apple @causes sadness         → rel = "@causes sadness" (unintended)
akasha/user $ ln $0 apple @causes                 → rel = "@causes" (correct)
```

#### `ln.ls [id]` — List Links

Lists all inbound and outbound links for an atom. Defaults to `$it` if no id is given.

```
akasha/user $ ln.ls silk_road_trade
Outbound:
  --> f3a1...9c42 (The Silk Road was not...)   [sys:includes]
  --> 7b2c...e301 (The city of Samarkand...)   [sys:includes]

Inbound:
  <-- cc29...08b2 (This means two people...)   [@part_of]
```

#### `ln.+ <src> <dst> <rel>` — Reinforce a Link

Increases the weight of an existing link by +0.1. Use this to strengthen associations that have proven meaningful over time.

```
akasha/user $ ln.+ silk_road_trade $1 sys:includes
Link weight updated: 0.6 -> 0.7
```

> **Late-binding:** If `<dst>` (or `<src>`) is not yet registered, the kernel falls back to the bare-segment proto-word and stores the link with a valid key immediately. Prefix with `=` for strict targeting: `ln memory.constructive =nar:tragedy @exemplifies` stores `nar:tragedy` as a placeholder for that specific atom rather than resolving to the proto-word `tragedy`.
>
> **CSL equivalents:** `link.create src="..." dst="..." rel="..."` · `link.list id="..."` · `link.reinforce src="..." dst="..." rel="..."`  
> **→** [`docs/csl-manual.md §4.4`](csl-manual.md#44-connecting-atoms-links)

#### `ln.rm <src> <dst> <rel>` — Remove a Link

Removes a single typed link. All three arguments must match the existing link exactly — partial matches are not performed.

```
akasha/user $ ln.ls silk_road_trade
Outbound:
  --> f3a1...9c42   [sys:includes]
  --> 7b2c...e301   [sys:includes]

akasha/user $ ln.rm silk_road_trade 7b2c...e301 sys:includes
Link removed.

akasha/user $ ln.rm silk_road_trade silk_road.overview sys:includes
Link removed.
```

> **Note:** Removing a link does not delete either atom. The atoms remain in the graph; only the edge between them is erased.

---

### 6.3 Aliases

#### `al <id> <name>` — Name an Atom

Gives a human-readable name to an atom. The alias becomes a permanent, globally unique identifier usable anywhere an atom id is expected.

```
akasha/user $ al f3a1...9c42 silk_road.overview
akasha/user $ r silk_road.overview
"The Silk Road was not a single road..."
```

**Argument order:** atom id first, name second.

```
akasha/user $ w "Cities preserve memory in their street layouts."
akasha/user $ al $it city.memory.street
```

**Multi-word names** work without quotes — all tokens after the id are joined:

```
akasha/user $ al $it first kiss          → name: "first kiss"
akasha/user $ al $it all roads lead Rome → name: "all roads lead Rome"
```

**Naming conventions:**

| Style | Example | When to use |
|---|---|---|
| Dotted namespace | `geo.paris.haussmann` | Ontology atoms, permanent concepts |
| Single word | `nostalgia` | Common concepts, emotion atoms |
| Multi-word phrase | `first kiss` | Personal memory, proper phrases |
| Colon namespace | `emo:bittersweet` | System ontology (reserved) |

Names that contain only printable characters (no quotes needed) are preferred. Avoid `/`, `\`, or control characters. Spaces in multi-word names are preserved exactly.

#### `al.ls` — List All Aliases

Shows every alias defined in your accessible scopes.

```
akasha/user $ al.ls
silk_road_trade       -> a09f...1d88
silk_road.overview    -> f3a1...9c42
memory.constructive   -> a3f7...c19e
bartlett.finding      -> b80d...44fa
reconstructive_memory -> d10a...77c3
```

#### `al.find <pattern>` — Search Aliases

Searches aliases using a SQL `LIKE` pattern. Use `%` as a wildcard.

```
akasha/user $ al.find silk%
silk_road_trade       -> a09f...1d88
silk_road.overview    -> f3a1...9c42

akasha/user $ al.find %memory%
memory.constructive   -> a3f7...c19e
memory.incompatible   -> cc29...08b2
reconstructive_memory -> d10a...77c3
```

#### `al.rm <name>` — Remove an Alias Binding

Removes the named alias. The atom it pointed to is **not deleted** — only the human-readable name is unlinked. The atom remains accessible by its full hex key or any other aliases it holds.

```
akasha/user $ al.rm silk_road.overview
Alias 'silk_road.overview' removed. Atom f3a1...9c42 still exists.

akasha/user $ r f3a1...9c42
"The Silk Road was not a single road, but a network of overland and maritime routes."
```

> Use `al.rm` to clean up temporary or typo-generated aliases. Use `rm` to delete the atom itself.

> **CSL equivalents:** `alias name="..." id="..."` · `alias.list` · `alias.find name="..."`  
> **→** [`docs/csl-manual.md §4.3`](csl-manual.md#43-giving-atoms-names-aliases)

---

### 6.4 Navigation

#### `dive <id>` — Dive Into an Atom

Steps into an atom and shows its full **meaning space**: content, signposts (direct links), semantic resonance (atoms sharing the same tags), and the surrounding field.

```
akasha/user $ dive silk_road_trade
────────────────────────────────────────────────────
▶ a09f...1d88…  [silk_road_trade]
  [Hub] silk_road_trade

Signposts:
   0. sys:includes  → [silk_road.overview]  The Silk Road was not a single road...
   1. sys:includes  → 7b2c…e301             ...
   2. @part_of      ← cc29…08b2             ...
     (type 0–2 to navigate)

Resonance:
      ≈ via [trade]  "The amber road predates..."
      ≈ via [route]  "Via Egnatia connected..."

Field: 12 nodes  [atom:7  link:3  set:2]
```

After diving, type a **number** to follow a signpost:

```
akasha/user $ 0       → dives into silk_road.overview
akasha/user $ 2       → dives into cc29…08b2
```

> `look` and `d` are legacy aliases for `dive` and continue to work.

#### `out [id]` — Zoom Out

Shifts focus to the macro view from the current atom, showing the broader neighborhood in the graph.

```
akasha/user $ out silk_road_trade
Zooming out from: silk_road_trade
Macro context: [parent hubs and cluster summary]
```

#### `tree [id] [depth]` — Hierarchical Link Tree

Renders the outbound link tree from an atom down to a given depth. Defaults: `$it`, depth 3.

```
akasha/user $ tree silk_road_trade 2
silk_road_trade
├── silk_road.overview [sys:includes]
│   └── (no further outbound links)
└── 7b2c...e301 [sys:includes]
    └── (no further outbound links)
```

#### `exp <id> [depth]` — BFS Graph Exploration

Performs a breadth-first search from the given atom, expanding outward to the specified depth (default 2). Useful for discovering how far an idea extends into the graph.

```
akasha/user $ exp reconstructive_memory 3
[D0] reconstructive_memory
[D1]   memory.constructive       (via sys:is_a)
[D1]   bartlett.finding          (via sys:evidenced_by)
[D1]   memory.incompatible       (via sys:implies)
[D2]     (atoms linked from memory.constructive...)
[D2]     (atoms linked from bartlett.finding...)
[D3]     ...
```

> **CSL equivalents:** `dive id="..."` · `look id="..."` (legacy) · `out` · `explore id="..." depth=<n>`  
> **→** [`docs/csl-manual.md §4.5`](csl-manual.md#45-exploring-the-graph)

#### Navigation Modes — Mode Prompt and Numeric Input

`dive`, `explore`, `assoc`, and `dream` each activate a **named mode** that is shown in the prompt. The mode tag indicates that bare-number input has special meaning:

```
[assoc] akasha/user $      ← assoc mode active
[dream] akasha/user $      ← dream mode active
[dive]  akasha/user $      ← dive mode active
```

**Exiting a mode:** type `exit` or `quit`. The first call exits the mode and returns to the normal prompt. A second `exit` closes the REPL session. Any normal command (e.g. `w "..."`, `ln ...`) works inside a mode without interrupting it.

---

#### `assoc <id>` — Semantic Gap Detection

Scans the focal atom's one-level outgoing links and identifies which **semantic axes** are absent. Candidate links are drawn from peer atoms that share the same collections — no inference is used.

```
[assoc] akasha/user $ assoc icarus
⊘ assoc [icarus]  axis=all
  Icarus, the one who flew too close to the sun

  emo  No emotional link found.
    candidates:
       1. calc:associated_with → [awe]   feeling of awe   ×3
       2. calc:associated_with → [fear]  fear and trembling  ×2

  context  No context link found.
    (no candidates — ln icarus <target> calc:context)

     (type 1–2 to create link)
```

**Interactive selection:** while inside assoc mode, type a bare number to immediately create that link. The system auto-refreshes the void view so you can see the remaining gaps.

**Axis filter:** `assoc icarus axis=emo` limits the scan to the emotional axis.

**Bulk fill:** `assoc icarus fill=yes` automatically accepts the top candidate for every void and writes the links in one step.

For voids with no candidates, the display shows a `ln focal <target> rel` hint. Write the missing atom with `w "..."` then `ln icarus last rel`, or type the `ln` command directly.

> **Semantic axes scanned:** emotion (`emo:`), color (`word:color:`), sense (`word:sense:`), time (`chrono:`), context (`calc:context`), story (`polti:`), structure (`sys:is_a` / `sys:antonym` etc.)

#### Meaning-Layer Search — `sim` / `node.sim` / `view` / `emotion.find`

`dive`, `tree`, and `assoc` all reason over the **explicit** links in the graph. Underneath them
Akasha keeps a **meaning layer**: every text atom carries a learned semantic vector (from its
words) and a structural vector (from its position in the link graph). These commands query that
layer, so they surface relatives that no explicit link records. All are read-only and
scope-filtered.

**`sim <id>` (aliases `similar`) — atoms that *mean* the same thing.** Anchored on the atom's own
content, not a typed phrase; the anchor is excluded from its own results.

```
akasha/user $ sim icarus              # atoms semantically nearest to Icarus
akasha/user $ sim icarus limit=20     # widen the list (default 10)
akasha/user $ search query="flight and hubris"   # free-text variant
```

**`node.sim <id>` — atoms *connected* the same way.** Structural (node-walk) similarity —
"wired into the graph the same way" — independent of meaning. `sim` and `node.sim` deliberately
disagree: `sim` answers *"means the same"*, `node.sim` answers *"connected the same"*.

```
akasha/user $ node.sim icarus
```

> **Implicit behaviour:** `node.sim` needs a trained structural model. The boot auto-learn builds
> one; on a fresh, sparsely-linked Cell an admin can run `node.learn` once to train it, otherwise
> `node.sim` returns nothing until enough structure exists.

**`view <id>` (alias `cosmos`) — the consciousness view of one atom, in place.** Signposts (1-hop
links), resonance (semantically-near atoms two hops out, ranked by real vector cosine), and the
atom's cosmos position + aura colour — **without** diving or changing your current focus.

```
akasha/user $ view icarus
```

**`emotion.find emo=<name>` — atoms that *feel* an emotion.** The reverse of `emotion.profile`;
emotions are ontology atoms (`emo:awe`, `emo:fear`, …). `emotion.profile <id>` gives the emotion
**vector** of a single atom instead.

```
akasha/user $ emotion.find emo=awe    # atoms that link to awe
akasha/user $ emotion.profile icarus  # Icarus's emotional vector
```

> **`sim` vs `node.sim` vs `dream`.** `sim`/`node.sim` rank what is *already* near (in meaning or
> structure). `dream` (§6.10) does the opposite — it hunts atoms near in meaning but **far** in the
> graph, the affinity gap, and stages them for you to confirm.

---

### 6.5 Sets

Named sets let you group atoms under a label for batch operations, filtering, or later processing.

**Set naming rules:** Single words and dotted names are clearest. Multi-word set names must be quoted in `s.add` because `name` is not the last positional argument (the `id` argument absorbs trailing tokens, not `name`).

```
akasha/user $ s.add memory_cluster $it              # single-word: no quotes needed
akasha/user $ s.add "urban memory" $it              # multi-word: quote the name
akasha/user $ s.add research.2026 some.alias        # dotted: fine, no quotes
```

**Finding sets for an atom:** Use `onto.dump mode=sets` to see set membership across the graph.

#### `s.add <name> <id>` — Add to Set

```
akasha/user $ s.add memory_cluster memory.constructive
akasha/user $ s.add memory_cluster bartlett.finding
akasha/user $ s.add memory_cluster memory.incompatible
akasha/user $ s.add memory_cluster reconstructive_memory
```

#### `s.rm <name> <id>` — Remove from Set

```
akasha/user $ s.rm memory_cluster memory.incompatible
```

#### `s.ls <name>` — List Set Members

```
akasha/user $ s.ls memory_cluster
Set: memory_cluster (3 members)
  - memory.constructive   [a3f7...c19e]
  - bartlett.finding      [b80d...44fa]
  - reconstructive_memory [d10a...77c3]
```

#### `s.clear <name>` — Clear a Set

Removes all members from the named set. The set name itself is preserved for future use.

```
akasha/user $ s.clear memory_cluster
Set 'memory_cluster' cleared (3 members removed).
```

#### `s.op <op> <result> <a> <b>` — Set Operation

Performs a set operation between sets `a` and `b` and stores the result in set `result`. Valid operations: `union`, `isect` (intersection), `diff` (difference).

```
akasha/user $ s.add philosophy_cluster reconstructive_memory
akasha/user $ s.add philosophy_cluster silk_road_trade

akasha/user $ s.op isect common_atoms memory_cluster philosophy_cluster
Intersection stored in 'common_atoms': 1 member
  - reconstructive_memory

akasha/user $ s.op union all_topics memory_cluster philosophy_cluster
Union stored in 'all_topics': 5 members
```

> **CSL equivalents:** `set.add name="..." id="..."` · `set.rm` · `set.ls` · `set.clear` · `set.op op=union|isect|diff result="..." a="..." b="..."`  
> **→ Full sets tutorial with examples:** [`docs/csl-manual.md §4.6`](csl-manual.md#46-working-with-sets)

---

### 6.6 Notes

The Notes subsystem provides a structured document layer on top of the graph. A note is itself an atom, and paragraphs are atoms linked as children.

#### `n.new <title>` — Create a Note

Creates a new document atom and makes it the active note.

```
akasha/user $ n.new "Field Notes: Unit B7 Excavation"
Note created: "Field Notes: Unit B7 Excavation" [note_id: 9d3f...a801]
Active note set.
```

#### `n.add <text>` — Append a Paragraph

Appends a paragraph atom to the currently active note.

```
akasha/user $ n.add "Excavation began at 09:00. The stratum at 1.5m depth showed charcoal deposits consistent with a fire event circa 14th century."

akasha/user $ n.add "A ceramic shard (catalog ref B7-144) was recovered. Surface decoration suggests a trade import, possibly from the Longquan kilns."

akasha/user $ n.add "Photographs taken. Sample sent to lab for radiocarbon dating."
```

The note now has three paragraph atoms, linked in sequence and anchored to the parent note atom. You can navigate the note using `look`, `tree`, or `exp`.

> **Other concept models** — Notes (`n.*`) is one of several structured knowledge models
> available in AKASHA. Other bundled models include **FieldNote** (`fn.*`) for timestamped
> field observations, **Survey** (`sv.*`) for questionnaires, and **Cockpit** (`cp.*`) for
> personal research dashboards. AKASHA's concept model system is extensible; additional
> models can be added without modifying the core kernel. See
> `docs/concept-extensions.md` for details on the bundled models.

---

### 6.7 JCL Job Control

JCL (Job Control Language) lets you submit scripts and long-running tasks as asynchronous background jobs. This keeps the shell responsive while heavy operations run in a worker queue.

#### `job.ls [owner]` — List Your Jobs

Without arguments, lists your own jobs. ADMINs can pass `owner=<id>` or `owner=all` to see other users' jobs.

```
akasha/user $ job.ls
JOB ID       Status     Submitted            Label
jcl-8841     DONE       2026-05-25 14:03     my_notes
jcl-8855     RUNNING    2026-05-25 14:22     load_corpus
jcl-8860     PENDING    2026-05-25 14:30     analysis
```

#### `job.stat <job_id>` — Show Job Status

```
akasha/user $ job.stat jcl-8855
Job:     jcl-8855
Label:   load_corpus
Status:  RUNNING
Started: 2026-05-25 14:22:01
```

#### `job.cancel <job_id>` — Cancel a Pending Job *(admin / librarian only)*

Only PENDING jobs can be cancelled. A RUNNING job must complete. Requires ADMIN or LIBRARIAN role.

```
akasha/user $ job.cancel jcl-8860
Job jcl-8860 cancelled.
```

#### `job.submit` — Submit a JCL Job *(admin / librarian only)*

Submit a structured job with an explicit steps array. Requires ADMIN or LIBRARIAN role. Regular users use `run <file>` to submit `.ak` batch scripts instead.

```
akasha/user $ job.submit steps=[{"method":"kernel.memory.write","params":{"text":"test"}}] label=batch_test
Job submitted: jcl-8870
```

> **Standard users:** use `run <file>` in the REPL to submit a `.ak` file as a background job. The file is parsed into steps automatically and executed by the JCL worker queue.

---

### 6.8 System

#### `ping` — Liveness Check

Confirms the kernel is online and responsive.

```
akasha/user $ ping
{"status": "ok", "message": "Kernel is alive."}
```

#### `cog` — Full Self-Awareness Pulse

Triggers a complete **cogito** (self-awareness diagnostic). The kernel introspects its current state: atom counts, link counts, scope sizes, and ontology integrity.

```
akasha/user $ cog
--- Cogito Pulse ---
Atoms in scope:   1,247
Links total:      4,832
Aliases defined:  88
Active jobs:      1
Ontology layers:  3 (DNA + 2 acquired)
Health: OK
```

#### `hist` — Recent Atom Stream

Shows the most recently created atoms across your accessible scopes, ordered by creation time.

```
akasha/user $ hist
[14:30:22] cc29...08b2  "This means two people can remember..."
[14:29:55] b80d...44fa  "Frederic Bartlett showed in 1932..."
[14:29:33] a3f7...c19e  "Memory is not a recording device..."
```

#### `passwd` — Change Your Passphrase

Changes your own passphrase. The shell prompts for your current passphrase, then the new passphrase twice for confirmation. No arguments are required — the command always applies to your own account.

```
akasha/user $ passwd
Current passphrase: ••••••••••
New passphrase:     ••••••••••
Confirm new passphrase: ••••••••••
{"status": "passphrase_updated"}
```

If you enter the wrong current passphrase, the change is rejected:

```
akasha/user $ passwd
Current passphrase: ••••••••••
✖ Authentication failed: incorrect current passphrase
```

> Only you can change your own passphrase with `passwd`. An administrator can reset anyone's passphrase using a separate admin command if you are locked out.

---

#### `ls [N]` — List Your Atoms

Lists the last N atoms authored by you (default 10).

```
akasha/user $ ls 5
1. cc29...08b2  "This means two people can remember..."
2. b80d...44fa  "Frederic Bartlett showed in 1932..."
3. a3f7...c19e  "Memory is not a recording device..."
4. 7b2c...e301  "The city of Samarkand stood at the crossroads..."
5. f3a1...9c42  "The Silk Road was not a single road..."
```

---

### 6.9 Contexa

Contexa provides web and knowledge-base enrichment, mapping external information into your local graph.

#### `fetch <query>` — Fetch External Context

Fetches a summary of the given query from the web or Wikipedia and writes the result as a new atom, ready to be linked into your graph.

```
akasha/user $ fetch "Bartlett reconstructive memory experiment 1932"
Fetching context for: "Bartlett reconstructive memory experiment 1932"
Atom written: e77b...3301
"Bartlett (1932) used the 'War of the Ghosts' folk tale to demonstrate that recall is
 reconstructive: participants unconsciously normalized the story to fit their own cultural
 expectations, altering details with each successive retelling."
```

---

### 6.10 Jataka

#### `dream <id>` — Affinity-Gap Incubation ("sleep on it")

`dream` occupies a distinct niche from the fast explorers. `assoc` fills 1-hop high-confidence
voids; `sim` / `node.sim` rank what is *already* near. `dream` searches the **affinity gap** —
atoms **near in meaning but far in the explicit graph** — the connections a person tends to notice
only after sleeping on a problem. It runs as a **low-priority background job**, and every candidate
is staged as a *tentative* link that a **human confirms**. It never writes a real edge on its own.

**Scoring.** Each candidate fuses three signals into a *nearness* — `content` (tensor cosine on the
semantic vector), `struct` (node-walk cosine), and `tag` (neighbour-set Jaccard) — then multiplies
by a **gap** term (`1/(1+shared_neighbours)`) so that only *missing* connections score. Two knobs
tune it, both conservative by default:

| Parameter | Default | Effect |
|---|---|---|
| `boldness=` | `0.2` | `0` = consensus of all signals present; `1` = the single boldest signal. |
| `reach=` | `0.5` | How hard the gap term is weighted — higher = only very-disconnected atoms score. |
| `again=yes` | — | Re-dream a focus that already has staged candidates (recompute from scratch). |

**It is asynchronous — call it twice.** The first call submits the job and returns immediately:

```
[dream] akasha/user $ dream icarus
☾ dream [icarus]  incubating…
  Come back with the same `dream id=` to see the staged bridges.
```

The job stages its candidates as `tent:calc:hidden_affinity` links in the background. Do other
work, then call `dream` again for the same focus to collect the result:

```
[dream] akasha/user $ dream icarus
✦ dream [icarus]  status=ready  2 bridge(s)

Bridges (near in meaning, far in the graph):
     1. [lilienthal]  pioneer of flight        0.612
     2. [ambition]    the drive to exceed      0.481

     (type a number or `dream.confirm dst=` to approve  |  `dream.forget all=yes` to drop)
```

**Human confirmation is mandatory — there is no auto-approval by design.** The question a dream
asks is whether a proposed connection **resonates with your own recall**, so the decision is
always yours:

| Command | Effect |
|---|---|
| *(type a bare number in dream mode)* | Confirms that bridge — calls `dream.confirm`, promoting the staged `tent:` link to a real `calc:hidden_affinity` edge. The list auto-refreshes. |
| `dream.confirm dst=<atom> [src=<focus>]` | Same, by name. `src` defaults to the last-dreamed focus. |
| `dream.forget dst=<atom>` | Drops a single staged bridge. |
| `dream.forget all=yes` | Drops every staged bridge on the focus. |

**Fallback.** If the JCL background layer is unavailable, `dream` degrades to a synchronous run —
it computes and stages the candidates in one call and returns `status=ready` directly.

**IAM.** A dream always inherits the session's active scopes — out-of-scope atoms are never
proposed as bridges.

---

### 6.11 Session Instance Layer

The Session Instance Layer lets you mount any concept model as a **named instance** inside your semantic session. Your session is a virtual space — a bag — and instances are objects in that bag. The same `instance.*` commands work for any concept model: cast personas, field note sets, synthesis projects, and future models.

Two relations are possible between your space and an instance:

| Relation | Meaning |
|----------|---------|
| `space:owns` | You created it; it lives here |
| `space:contains` | You borrowed it from another space (e.g. a StageEncounter) |

#### `instance.mount model=<model> slot=<name>` — Mount an Instance

Creates a new concept model instance and mounts it in your space. The `slot` is the name you use to address it.

```
akasha/user $ instance.mount model=cast slot=bot name="aria"
{
  "status": "mounted",
  "slot": "bot",
  "model": "cast",
  "concept_id": "3a9f...c201",
  "relation": "space:owns",
  "focused": true
}
```

The first instance of each model class is automatically focused. After mounting, all `cast.*` commands route to `aria` with no further steps.

To mount an **existing** cast instead of creating a new one:

```
akasha/user $ cast.ls
[{"cast_id": "a1b2...ef01", "name": "kenji"}, ...]

akasha/user $ instance.mount model=cast slot=kenji id=a1b2...ef01
```

#### `instance.focus slot=<name>` — Switch Focus

Routes a model class's commands to a different slot. Use this to switch between multiple mounted instances of the same model.

```
akasha/user $ instance.mount model=cast slot=aria  name="aria"
akasha/user $ instance.mount model=cast slot=kenji name="kenji"
# cast.* → aria (auto-focused on first mount)

akasha/user $ instance.focus slot=kenji
# cast.* → kenji

akasha/user $ instance.focus slot=aria
# cast.* → aria
```

#### `instance.blur model=<model>` — Step Out of Focus

Clears routing focus for a model class. After blur, `cast.*` commands no longer route to any instance until you call `instance.focus` again.

```
akasha/user $ instance.blur model=cast
{"status": "blurred", "model": "cast", "was_slot": "aria"}
```

#### `instance.ls` — List All Instances in This Space

```
akasha/user $ instance.ls
{
  "space_id": "f8a1...0011",
  "instances": [
    {"slot": "bot",   "model": "cast",      "focused": true,  "relation": "space:owns"},
    {"slot": "diary", "model": "fieldnote", "focused": true,  "relation": "space:owns"}
  ],
  "focus": {"cast": "bot", "fieldnote": "diary"}
}
```

#### `instance.unmount slot=<name>` — Remove a Slot

Removes the slot from your space. The underlying concept model instance (the cast, the field note, etc.) is **not deleted** — it remains in Cortex and can be re-mounted later.

```
akasha/user $ instance.unmount slot=bot
{"status": "unmounted", "slot": "bot", "model": "cast", "concept_id": "3a9f...c201"}
```

#### `instance.join concept_id=<id> slot=<name>` — Borrow an External Instance

Adds an instance owned by another space into your space as `space:contains`. Used for Stage participation: another client's cast persona enters your space without transferring ownership. IAM scopes continue to protect private data — you can see only what the owner has marked `audience=public`.

```
akasha/user $ instance.join concept_id=d7c2...aa03 slot=guest_kenji
{"status": "joined", "slot": "guest_kenji", "model": "cast", "relation": "space:contains"}
```

---

### Cloning a Mounted Cast

Because `cast.*` commands route to the currently focused cast, cloning the mounted cast is simply:

```
akasha/user $ cast.clone name="aria_v1"
{
  "status": "cloned",
  "src_id": "3a9f...c201",
  "cast_id": "7c1d...e804",
  "name": "aria_v1",
  "atoms_cloned": 23
}
```

Session focus is restored to the original after cloning. To restore a snapshot:

```
akasha/user $ instance.unmount slot=bot
akasha/user $ instance.mount model=cast slot=bot id=7c1d...e804
```

---

### Privacy

All atoms created by `instance.mount` are tagged with your user ID as both owner and viewer — other clients cannot read, list, or link to your instances. This is enforced at the database read layer, not the application layer.

Borrowed instances (`instance.join`, `space:contains`) respect the same IAM rules: private layers of the borrowed instance remain invisible to your session. Only atoms the owner has made accessible (e.g. `audience=public` masks on a cast) are visible.

> **Stage Integration.** When multi-client features are added, a `StageConcept` will manage shared spaces. `instance.join` is already the integration point: a participant's cast enters the stage space as `space:contains`, and IAM scopes ensure only the public-facing mask atoms are shared. This architecture is already reflected in the `audience` parameter of `cast.mask.add`.

### Available Concept Models

Any of the following models can be mounted via `instance.mount model=<name>`:

| Model | Prefix | Purpose |
|-------|--------|---------|
| Note | `note` | Hierarchical notes with span annotations |
| FieldNote | `fieldnote` | Field observation journals |
| Survey | `survey` | Structured questionnaires and responses |
| Aggregation | `agg` | Statistical summaries and group comparisons |
| Synthesis | `synth` | Qualitative coding, themes, interpretive claims |
| Presentation | `pres` | Structured argument decks |
| Cast | `cast` | Persona and character modeling |
| World | `world` | Topology of worlds — places, laws, events, history |

Full API reference for each model: [`docs/concept-model/concept-model-intelligence.md`](../concept-model/concept-model-intelligence.md)

---

### 6.12 CSL — Concept Specific Language

CSL (Concept Specific Language) is an alternative way to give instructions to Akasha. Shell commands (§6.1–6.11) are short and positional — designed for speed. CSL uses explicit `option=value` syntax that is easier to read, chain together, and share.

Type `csl` at the shell prompt to open the CSL interactive interpreter:

```
akasha/user $ csl
Akasha CSL interpreter (Phase 1). Type 'exit' or Ctrl-D to quit.
csl> write text="Memory is a constructive process."
{
  "id": "a3f7...c19e"
}
csl> exit
akasha/user $
```

#### Shell ↔ CSL Quick Reference

The table below shows the most common operations in both forms. You can use either in the CSL interpreter — the short shell aliases (`w`, `ln`, `al`, etc.) are also valid CSL.

| Shell | CSL | Operation |
|-------|-----|-----------|
| `w "text"` | `write text="text"` | Write an atom |
| `def <label>` | `define label="label"` | Write and name an atom |
| `r <id>` | `read id="id"` | Read an atom |
| `rm <id>` | `drop id="id"` | Delete an atom |
| `ln <src> <dst> <rel>` | `link.create src="src" dst="dst" rel="@rel"` | Create a link |
| `ln.ls <id>` | `link.list id="id"` | List links |
| `al <id> <name>` | `alias name="name" id="id"` | Name an atom |
| `al.find <pattern>` | `alias.find name="pattern"` | Search names |
| `dive <id>` | `dive id="id"` | Dive into atom — meaning space + signposts |
| `look <id>` | `look id="id"` | Legacy alias for dive |
| `exp <id> <depth>` | `explore id="id" depth=2` | Explore the graph |
| `s.add <name> <id>` | `set.add name="name" id="id"` | Add to set |
| `s.ls <name>` | `set.ls name="name"` | List set members |
| `s.op union <r> <a> <b>` | `set.op op=union result="r" set_a="a" set_b="b"` | Union of two sets |
| `ping` | `sys.ping` | Liveness check |

#### Why use CSL instead of shell commands?

**Named options, not positional arguments.** In the shell, `ln $0 $1 @supports` requires you to remember which position means source and which means destination. In CSL, `link.create src=$a.key dst=$b.key rel="@supports"` is self-explanatory.

**Chaining steps with named results.** CSL lets you save the result of one command and pass it to the next:

```
csl> $atom_a = write text="Memory is constructive."
csl> $atom_b = write text="Bartlett demonstrated schema drift."
csl> link.create src=$atom_a.key dst=$atom_b.key rel="@evidenced_by"
```

No copying IDs. No relying on `$0`, `$1` ordering.

**Block syntax for complex commands.** Long commands become readable:

```
csl> $req = intel.req:
...     question         = "What is the sovereignty status of Kaliningrad?"
...     requirement_type = strategic
...     priority         = high
...
```

**Concept model commands.** `ft.*`, `cur.*`, and `intel.*` commands (fact collection, curation, intelligence) are only available through CSL.

#### Script mode — running many commands at once

From the Akasha shell, you can run a whole CSL script in one go:

```
akasha/user $ csl.check script="..."   # validate without executing
akasha/user $ csl.dry   script="..."   # preview every operation
akasha/user $ csl.run   script="..."   # execute
```

Recommended order: check → dry → run.

> **→ Full CSL Manual:** [`docs/csl-manual.md`](csl-manual.md)  
> **→ Implementation spec:** [`docs/csl-spec.md`](csl-spec.md)

---

## 7. Context References ($-syntax)

AKASHA maintains a live **context stack** — a rolling history of atoms you have interacted with. The `$`-syntax lets you reference atoms by their position in this stack without memorizing hex keys.

| Reference | Meaning |
|---|---|
| `$it` | The last atom you explicitly wrote (`w` or `def`) |
| `$0` | The most recent user atom in history |
| `$1`, `$2`, `$3`… | Older atoms in reverse chronological order |
| `$0:5` | A slice: atoms 0 through 4 (returns a list) |
| `set:name` | All members of the named set |
| `#trait` | All atoms associated with a given trait |
| `@here` | The current GPS anchor atom (location-aware) |
| `@now` | The current chrono anchor atom (time-aware) |
| `@2025` | A temporal era anchor for the year 2025 |
| `alias.child` | All outgoing link targets from the given alias |
| `alias.parent` | All incoming link sources to the given alias |
| `~emo:sadness` | Tensor/semantic nearest-neighbor match |

### Practical Examples

```
# Link the last two written atoms
akasha/user $ ln $1 $0 @follows

# List links for the atom before last
akasha/user $ ln.ls $1

# Set metadata on atoms 0 through 4
# (processed as a batch in a .ak script)
akasha/user $ meta $0:5 reviewed true

# Find all atoms semantically near 'nostalgia'
akasha/user $ exp ~emo:nostalgia 2

# Link to the current GPS location anchor
akasha/user $ ln $0 @here @recorded_at

# Reference all members of a named set
akasha/user $ tree set:memory_cluster
```

---

## 8. Rel Normalization

When you create a link with `ln`, the `rel` argument is automatically normalized according to these rules:

| Input `rel` | Stored as | Rule |
|---|---|---|
| `next` | `@next` | No namespace prefix, no `@` → prepend `@` |
| `causes` | `@causes` | Same as above |
| `sys:implies` | `sys:implies` | Has namespace prefix (`:`) → unchanged |
| `calc:associated_with` | `calc:associated_with` | Has namespace prefix → unchanged |
| `@followed_by` | `@followed_by` | Already starts with `@` → unchanged |
| `~embodies` | `~embodies` | Starts with `~` (tensor) → unchanged |

### Namespace Convention

| Prefix | Meaning |
|---|---|
| `@` | User-defined or generic relation |
| `sys:` | System-level structural relation (is_a, part_of, etc.) |
| `calc:` | Computed or statistical relation (associated_with, etc.) |
| `~` | Tensor/semantic relation (soft, weighted) |

```
# These are all equivalent in practice:
akasha/user $ ln $0 $1 next          # stored as @next
akasha/user $ ln $0 $1 @next         # stored as @next

# Namespace-qualified rels are preserved:
akasha/user $ ln $0 $1 sys:causes    # stored as sys:causes
akasha/user $ ln $0 $1 calc:similar  # stored as calc:similar
```

---

## 9. Ontology: Innate vs Acquired

AKASHA's knowledge layer is divided into two tiers: **innate** (built into the kernel at birth) and **acquired** (loaded from external files).

### 9.1 Innate Ontology (DNA)

The innate ontology is the kernel's **DNA** — a set of foundational relation types, structural primitives, and system namespaces that are compiled directly into the kernel and always present. You cannot remove or modify innate ontology entries; they are the bedrock on which all other knowledge is built.

Innate elements include:
- Core system relations: `sys:is_a`, `sys:part_of`, `sys:implies`, `sys:causes`
- Scope definitions: `scope:sys:universal`, `scope:personal`, `scope:group`
- IAM role definitions: `ADMIN`, `LIBRARIAN`, `GROUP_ADMIN`, `USER`, `GUEST`
- Tensor relation primitives: `~` prefix handling

These are invisible in the sense that they require no loading step — they are always available from the first command.

### 9.2 Acquired Ontology (.ak files)

Acquired ontology files are `.ak` scripts stored in the `ontology/` directory. They extend the graph with domain-specific knowledge: emotional spectrums, narrative archetypes, vocabulary corpora, and more. They are written in the same command language as user scripts.

Current acquired ontology files (loaded alphabetically at login):

| File | Contents |
|---|---|
| `a_emotions_27.ak` | 21 compound emotions extending the 8 DNA primaries |
| `b_polti_36.ak` | Polti's 36 Dramatic Situations as hub atoms |
| `c_vocab_core1–9.ak` | ~823 English word atoms (basic vocabulary corpus) |
| `d_community_gaming.csl` | Online / gaming culture vocabulary |
| `e_business_core.csl` | Business & commerce concepts |
| `f_writing_authorship.csl` | Writing craft, roles, and structure |
| `g_writing_screen_stage.csl` | Screen, stage, and cinema concepts |
| `h_public_governance.csl` | Civic governance and policy concepts |
| `i_entertainment_fantasy.csl` | Fantasy subgenres and tropes |
| `j_narrative_typology.csl` | Narrative structure, archetypes, story curves |
| `k_narrative_typology2.csl` | Abstract narrative mode types (quest, tragedy, etc.) |
| `l_system_architecture.csl` | System design and architecture concepts |

**Seed ontology** files in `ontology/seeds/` provide foundational narrative and conceptual scaffolding:

| File | Contents |
|---|---|
| `a_ quotes.ak` | Curated quotations as atoms |
| `b_ semantics.ak` | Semantic primitives and relation exemplars |
| `c_ narrative.ak` | Grand narrative archetypes and story structure |

### Loading Acquired Ontology

Ontology files in `ontology/` are loaded **automatically at first startup**. Boot sentinels (`ont:ak:loaded`, `ont:csl:loaded`, `ont:curation:loaded`) prevent double-loading on subsequent starts.

To re-trigger loading after modifying ontology files (LIBRARIAN role required):

```
akasha/user $ onto.reload
{"status": "reload_triggered", "sentinels_cleared": [...]}
```

To load a single script file manually:

```
akasha/admin $ run ontology/common/a_emotions_27.ak
Job submitted: job_id=jcl-9011
```

Once loaded, ontology atoms are available to all users in the collective scope:

```
akasha/user $ r emo:nostalgia
"[emo:nostalgia]\nA sentimental longing or wistful affection for the past."

akasha/user $ ln $0 emo:nostalgia ~evokes
akasha/user $ exp emo:awe 2
[D0] emo:awe
[D1]   emo:surprise  (via sys:is_a)
[D1]   emo:fear      (via sys:is_a)
[D1]   word:en:sun   (via calc:associated_with)
```

### Writing Your Own Ontology Files

Any `.ak` file can serve as an ontology module. The canonical form uses `def "namespace:name" "description"` for concept definitions. The proto-word (bare alias) is created automatically. A minimal example:

```
# my_domain.ak  — Botanical taxonomy fragment

# def "namespace:name" "description" — canonical form
# Proto-word is auto-created; no bare alias line needed
def "plant:angiosperm" "A flowering plant that produces seeds enclosed in a fruit."
def "plant:gymnosperm" "A seed-producing plant with seeds unenclosed (e.g. conifers)."

def "plant:oak" "Quercus robur. Deciduous oak tree of Europe and western Asia."
def "plant:pine" "Pinus sylvestris. Scots pine, a conifer native to Eurasia."

# ln uses bare aliases (proto-words) on both sides
ln oak angiosperm sys:is_a
ln pine gymnosperm sys:is_a
ln angiosperm gymnosperm sys:diverged_from
```

For hub atoms with no namespace (proper nouns, archetypes), use single-arg `def`:

```
def "Atlantis"
def "Quantum Mechanics"
```

Load it with:

```
akasha/user $ run my_domain.ak
```

### Inspecting the Ontology

Two commands let you verify what is actually loaded in the live graph:

#### `onto.dump` — Browse ontology data

```
akasha/user $ onto.dump atoms ns=word:en limit=20
akasha/user $ onto.dump antonyms
akasha/user $ onto.dump namespaces
akasha/user $ onto.dump sets collection=ontology.narrative_typology
akasha/user $ onto.dump links rel=calc:has_emotion
akasha/user $ onto.dump aliases pattern=nar:%
```

| Mode | What you see |
|---|---|
| `atoms` | All atoms in a namespace: alias + definition preview |
| `links` / `antonyms` | Semantic links, filterable by relation type |
| `aliases` | All registered aliases; supports `pattern=` wildcard |
| `sets` | Members of a named collection |
| `namespaces` | Count of atoms per namespace prefix |

#### `onto.report` — Alias collision report

Shows any alias conflicts detected during the last ontology load. Printed
automatically at login if collisions occurred.

```
akasha/user $ onto.report
{
  "overwrites": 0,
  "leaf_skips": 14,
  ...
}
```

- **`overwrites: 0`** — the load was clean. Any overwrite means two ontology
  files defined the same term and the later one silently replaced the earlier.
- **`leaf_skips: N`** — normal. A bare alias like `comedy` was already claimed
  by the first file to define it; subsequent registrations were skipped.

#### `onto.reload` — Soft reload (LIBRARIAN only)

Removes the four boot sentinels and re-triggers the full ontology boot sequence in the background. Existing atoms are idempotent — same content means same key, so nothing changes unless the file changed. New or modified `.ak`/`.csl`/curations files will be picked up.

```
akasha/user $ onto.reload
{"status": "reload_triggered", "sentinels_cleared": [...], "message": "..."}
```

#### `onto.reset` — Hard nuclear reset (LIBRARIAN only) ⚠️

**DANGEROUS ZONE.** Deletes ALL data from nucleus except the 35 DNA primal atoms (relations, emotion axes, logic operators). Ontology, thesaurus, curations — all cleared. Then re-triggers boot. **Cannot be undone.** Use when you want a completely clean state, e.g. after major ontology restructuring.

```
akasha/user $ onto.reset confirm="RESET"
{"status": "reset_complete", "dna_atoms_preserved": 35, "message": "..."}
```

Running without `confirm="RESET"` shows the warning without acting.

---

## 10. JCL Batch Jobs

JCL (Job Control Language) is AKASHA's mechanism for running scripts asynchronously. When you submit a job, it enters a worker queue and runs without blocking your shell session. This is essential for large import operations, ontology loading, or automated knowledge construction.

### Why Use JCL?

- **Non-blocking:** The shell remains responsive while the job runs.
- **Auditable:** Every operation is logged in the Harmonia evidence log.
- **Cancellable:** PENDING jobs can be stopped before they start.
- **Scheduled:** Multiple jobs queue up and execute in order.

### Writing a .ak Script

A `.ak` file is a plain text file where each line is a kernel command. Comments begin with `#`. The same `$`-syntax and all kernel commands are available.

**Example: `field_notes_may.ak`**

```
# field_notes_may.ak
# Batch import: Field notes from the Samarkand dig, May 2026

# --- Site Overview ---
def @"site:samarkand_b7"
meta @"site:samarkand_b7" location "Samarkand, Uzbekistan"
meta @"site:samarkand_b7" season "Spring 2026"

# --- Day 1 Notes ---
w "Excavation of Unit B7 commenced. Soil layer at 0–0.5m: disturbed modern fill."
al $it note.b7.day1.layer1
ln note.b7.day1.layer1 @"site:samarkand_b7" sys:part_of

w "Layer at 0.5–1.2m: compact clay with medieval pottery sherds. Dating: 13th–14th c."
al $it note.b7.day1.layer2
ln note.b7.day1.layer1 note.b7.day1.layer2 @overlies

w "Ceramic shard B7-144 recovered. Celadon glaze. Possible Longquan origin."
al $it artifact.B7_144
ln artifact.B7_144 note.b7.day1.layer2 @found_in
meta artifact.B7_144 catalog_ref "B7-144"
meta artifact.B7_144 material "ceramic"

# --- Contextual links to ontology ---
ln note.b7.day1.layer2 @"polti:12" ~illustrates
# polti:12 = "Obtaining. Gaining something desired through effort."

# --- Group the day's notes into a set ---
s.add b7_may26 note.b7.day1.layer1
s.add b7_may26 note.b7.day1.layer2
s.add b7_may26 artifact.B7_144
```

### Submitting the Script

```
akasha/user $ run field_notes_may.ak
Job submitted: job_id=jcl-9100
```

### Monitoring Progress

```
akasha/user $ job.st jcl-9100
Job:    jcl-9100
Script: field_notes_may.ak
Status: RUNNING
Progress: 8 / 14 operations
Started: 2026-05-25 16:04:12

akasha/user $ job.st jcl-9100
Job:    jcl-9100
Status: DONE
Operations: 14 / 14
Completed: 2026-05-25 16:04:13
```

### Reviewing the Evidence Log

```
akasha/user $ job.log jcl-9100
[16:04:12] JOB jcl-9100 START (field_notes_may.ak)
[16:04:12] def @"site:samarkand_b7"  ->  fa3c...7801  OK
[16:04:12] meta site:samarkand_b7 location ...  OK
[16:04:12] meta site:samarkand_b7 season ...  OK
[16:04:12] w "Excavation of Unit B7..."  ->  1b9a...cc12  OK
[16:04:12] al 1b9a... note.b7.day1.layer1  OK
[16:04:12] ln note.b7.day1.layer1 -> site:samarkand_b7 [sys:part_of]  OK
[16:04:12] w "Layer at 0.5–1.2m..."  ->  2d3e...7f01  OK
[16:04:12] al 2d3e... note.b7.day1.layer2  OK
[16:04:12] ln note.b7.day1.layer1 -> note.b7.day1.layer2 [@overlies]  OK
[16:04:12] w "Ceramic shard B7-144..."  ->  8c77...a320  OK
[16:04:12] al 8c77... artifact.B7_144  OK
[16:04:12] ln artifact.B7_144 -> note.b7.day1.layer2 [@found_in]  OK
[16:04:13] meta artifact.B7_144 catalog_ref B7-144  OK
[16:04:13] meta artifact.B7_144 material ceramic  OK
[16:04:13] JOB jcl-9100 DONE (14 ops, 0 errors)
```

### Exploring the Imported Data

```
akasha/user $ look @"site:samarkand_b7"
--- Atom: site:samarkand_b7 ---
[Hub] site:samarkand_b7
metadata: location = Samarkand, Uzbekistan
metadata: season = Spring 2026

Signposts:
  <-- note.b7.day1.layer1  [sys:part_of]

akasha/user $ tree @"site:samarkand_b7" 3
site:samarkand_b7
└── note.b7.day1.layer1 [sys:part_of (inbound)]
    └── note.b7.day1.layer2 [@overlies]
        └── artifact.B7_144 [@found_in]
```

---

## 11. Groups and Scopes

AKASHA's scope system is the mechanism by which knowledge is shared, isolated, and governed. Scopes are not folders or tags — they are physical dimensions of the database, meaning access control is enforced at the read level before any data reaches your session.

### The Three Scope Levels

| Scope | Who can see it | Who can write to it |
|---|---|---|
| **Personal** (`scope:user:<id>`) | Only the owner | Only the owner |
| **Group** (`scope:group:<name>`) | Group members | GROUP_ADMIN and higher |
| **Collective** (`scope:sys:universal`) | Everyone | LIBRARIAN and higher |

### Dark Matter Privacy

Atoms outside your accessible scopes are invisible during graph traversal. If a colleague creates a private atom that links to a public atom you can both see, you will see the public atom normally — the private atom simply does not appear in your view. It exists in the database but behaves as dark matter.

### Group Scopes

Groups are named collections of users that share a dedicated knowledge space. Each group has its **own separate database** (`data/groups/{group_id}/g_space.db`) — group atoms are physically isolated from both user cells and the collective nucleus. A group might represent a research team, a project, or an organization.

**How it works:**

1. An ADMIN creates a group and designates a GROUP_ADMIN.
2. The GROUP_ADMIN manages membership for their group.
3. Atoms reach the group space via the **Delegation & Donation Sets** API (`dont.*`) — see [§13](#13-sharing-knowledge--delegation-sets).
4. Group atoms are visible to all group members and only to them.
5. Group atoms are not visible to users outside the group (unless also in the collective scope).

**Example workflow — a collaborative research team:**

```
# GROUP_ADMIN sets up shared reference material (written to group scope)
akasha/group_admin $ w "Team protocol: all artifact photos stored in /media/dig2026/"
akasha/group_admin $ al $it team.protocol.photos
akasha/group_admin $ meta $it scope group:dig2026

# Regular team member reads the shared atom
akasha/team_member $ r team.protocol.photos
"Team protocol: all artifact photos stored in /media/dig2026/"

# Team member writes a personal note (private scope, not visible to team)
akasha/team_member $ w "Personal: the stratigraphy in B7 reminds me of the Petra site from 2023."
# This atom is visible only to team_member.

# Team member contributes a finding to the group scope
akasha/team_member $ w "Unit B7, trench wall profile: limestone bedrock visible at 2.1m depth."
akasha/team_member $ al $it b7.bedrock_depth
# (GROUP_ADMIN or ADMIN must move this to group scope, or permissions allow team members to write to group)
```

### Collective Scope

The collective scope (`scope:sys:universal`) is the shared knowledge commons. Ontology atoms — emotion definitions, narrative archetypes, vocabulary — live here. All users can read collective atoms. Only LIBRARIANs and ADMINs can write to the collective scope.

```
# LIBRARIAN loads a new ontology module into collective scope
akasha/librarian $ run ontology/b_polti_36.ak
Job submitted: job_id=jcl-9200

# All users can now reference Polti situations
akasha/guest $ r polti:09
"Situation: Daring Enterprise. A bold attempt to achieve a difficult goal."
```

### Scope Visibility Formula

Your visible atom set at any moment is:

```
S_visible = S_personal ∪ S_groups ∪ S_collective
```

filtered by your active language scopes. This means reading a linked atom list or performing `exp` will only ever surface atoms you have permission to see.

---

## 12. Group Administrator Commands

> This section applies only to users with the **GROUP_ADMIN** role. These commands are not visible in the standard `help` output. If you have been designated as a group administrator by your system administrator, the commands below are available to you.

A GROUP_ADMIN manages the membership of one specific group. This role grants the ability to add and remove members, and to promote members to group-level librarian status (which allows them to write atoms to the group's shared scope).

### What a GROUP_ADMIN can and cannot do

**Can do:**
- View the members of their own group
- Add new users to their group
- Remove users from their group
- Grant or revoke group-librarian status within their group

**Cannot do:**
- Read private atoms belonging to group members
- Manage any other group
- Use `user.*` admin commands
- See other groups' membership or atoms
- Access system administration features

---

### `grp.ls <group_id>` — View Group Members

Lists the current members of your group. Users marked `[lib]` hold group-librarian status and can write to the group scope.

```
akasha/team_bob $ grp.ls dig2026

  dig2026  admin: team_bob
    · team_bob
    · alice
    · carol [lib]
```

---

### `grp.add <group_id> <member_id>` — Add a Member

Adds a registered user to your group. Once added, the user gains read access to all atoms in the group scope.

```
akasha/team_bob $ grp.add dig2026 david
{"status": "added", "group_id": "dig2026", "member": "david"}
```

> The user to be added must already have an AKASHA account created by the administrator. If the add fails, contact your administrator to verify the account exists.

---

### `grp.rm <group_id> <member_id>` — Remove a Member

Removes a user from your group. After removal, the user loses access to group-scoped atoms. Their personal atoms are not affected.

```
akasha/team_bob $ grp.rm dig2026 david
{"status": "removed", "group_id": "dig2026", "member": "david"}
```

> You cannot remove yourself (the group administrator) from the group.

---

### `grp.lib <group_id> grant|revoke <member_id>` — Manage Group Librarian Rights

Promotes a member to group librarian (allowing them to write atoms to the group scope), or revokes that status.

```
akasha/team_bob $ grp.lib dig2026 grant carol
{"status": "librarian_granted", "group_id": "dig2026", "member": "carol"}

akasha/team_bob $ grp.lib dig2026 revoke carol
{"status": "librarian_revoked", "group_id": "dig2026", "member": "carol"}
```

Group librarians can write to the group scope. Without this status, group members are read-only within the group — they can see group atoms but cannot create new ones in the shared space.

> Group librarian status is limited to your group. It does not affect the user's permissions in other groups or in the collective scope.

---

### Privacy Guarantee

As a GROUP_ADMIN, you manage membership — you do not gain any additional visibility into members' private data. Every user's personal atoms remain invisible to you, exactly as they are to any other user.

The scope system enforces this at the database level: your session can only see atoms that are explicitly tagged with your group's scope token or the collective scope. Personal atoms belonging to other users carry only their private scope tags and are never surfaced in your graph traversals, searches, or link lists.

---

## 13. Sharing Knowledge — Delegation Sets

Delegation sets (`dont:*`) let you collect atoms and donate them to a shared space: the collective nucleus (visible to all users) or a specific group space (visible only to group members). The donation preserves provenance: both sides retain a record of what was shared, when, and by whom.

### When to use delegation sets

- You have done private research and want to contribute vocabulary, definitions, or findings to your team's group space.
- You are a librarian uploading curated knowledge to the collective scope.
- You want to track a batch of atoms you have shared, together with the provenance history.

### The two donation modes

| Mode | Command | Effect |
|---|---|---|
| **Copy** (default) | `dont.send` | Atom is copied to the target space. Your original is unchanged. Group members work on the copy independently. |
| **Open** | `dont.open` | The original atom's scope is extended to include the target. No copy is made; the group sees your original directly. |

Copy mode is recommended for group donations. It lets your team collaborate on the copy without touching your original work.

### Workflow

#### Step 1 — Create a delegation set

```
akasha/user $ dont.create my_vocab "Core emotion vocabulary for history project"
{"set": "dont:my_vocab", "status": "created"}
```

#### Step 2 — Add atoms to the set

You can add atoms by alias, `$`-reference, or direct key. Multiple targets can be listed space-separated.

```
akasha/user $ dont.add my_vocab emo:love emo:joy emo:sadness
{"set": "dont:my_vocab", "added": 3}

akasha/user $ dont.add my_vocab $0 $1
{"set": "dont:my_vocab", "added": 2}
```

#### Step 3 — Donate to a group or the collective scope

Donate to your group:

```
akasha/user $ dont.send my_vocab group:history_lab
{"status": "donated", "set": "dont:my_vocab", "to": "group:history_lab", "mode": "copy", "donated": 5}
```

Donate to the collective scope (librarian/admin only):

```
akasha/librarian $ dont.send my_vocab universal
{"status": "donated", "set": "dont:my_vocab", "to": "nucleus", "mode": "copy", "donated": 5}
```

#### Step 4 — View donation history

Check the provenance record at any time:

```
akasha/user $ dont.ls my_vocab
--- dont:my_vocab ---
Atoms: 5
Donations:
  → group:history_lab  (2026-06-09, 5 atoms, copy)
```

### Command reference

| Command | Description |
|---|---|
| `dont.create <name> [description]` | Create a new delegation set |
| `dont.add <name> <targets...>` | Add atoms to a set (aliases, `$`-refs, or hex keys, space-separated) |
| `dont.send <name> <to>` | Copy atoms from the set to `"group:<id>"` or `"universal"` |
| `dont.open <name> <to>` | Extend scope of original atoms to target (no copy) |
| `dont.ls [name]` | List all sets (no arg) or detail a single set (with name) |

> **Note:** Delegation sets are reusable. You can add more atoms and donate again; each call appends a new entry to the donation history. The set itself acts as a persistent provenance record.

> **Re-integration:** If group members have modified the donated copy and you want to bring those changes back to your original, this is not yet automated. Use the group space's atoms as a reference and update your originals manually.

---

## 14. Roles and Permissions

| Role | Writes to | JCL | Sees others' jobs | Group management |
|---|---|---|---|---|
| **ADMIN** | All scopes | Yes (all jobs visible) | Yes | Yes (all groups) |
| **LIBRARIAN** | Collective scope | Yes (own jobs) | No | No |
| **GROUP_ADMIN** | Group scope | Yes (own jobs) | No | Own group only |
| **USER** | Personal scope | Yes (own jobs) | No | No |
| **GUEST** | None | No | No | No |

### Role Notes

- **ADMIN** has full visibility across all scopes and all JCL jobs. The `mon` command shows the complete worker queue. Administrators also have access to privileged commands not shown in `help`; refer to the Administrator Manual for details.
- **LIBRARIAN** is the trusted curator role. Use this for accounts responsible for loading shared ontology and collective-scope reference material.
- **GROUP_ADMIN** can write to a specific group scope and manage that group's membership. See [Section 12](#12-group-administrator-commands) for the commands available to group administrators.
- **USER** is the standard role for researchers and contributors. All personal atoms are private by default.
- **GUEST** is a read-only observer. GUESTs can read atoms in the collective scope and any group they are explicitly granted read access to, but cannot create atoms or run jobs.

---

## 15. Tips and Patterns

### Build a Vocabulary Before Linking

Define your hub atoms and assign aliases before writing detail atoms. This makes linking cleaner because you can use readable names everywhere.

```
def field_site
def excavation_unit
def artifact_type
# Now write detail atoms and link them to the hubs
```

### Use CSL for Bulk Data Entry and LLM Collaboration

When converting research notes or documents into graph entries, use CSL rather than typing commands one by one. Paste your notes to an LLM with the CSL grammar in the system prompt; review the generated script with `csl.dry`; then run it.

```
1. Paste notes to LLM → receive a .csl script
2. csl.check script="..."  → fix any errors
3. csl.dry   script="..."  → verify what will be written
4. csl.run   script="..."  → execute
```

For validation errors, paste the `csl.check` output back to the LLM — the `suggestion` field gives close-match hints that let the LLM fix the script without knowing the full method list.

See [`docs/csl-manual.md`](csl-manual.md) for the complete CSL reference.

### Use `.ak` Scripts for Repeated Structures

If you have a standard workflow (e.g., a daily field note template), write a reusable `.ak` script. Parameterize it with comments to remind yourself what to fill in.

### Reinforce Links That Matter

Use `ln.+` when you revisit a connection and find it repeatedly useful. Over time, high-weight links form the "highways" of your graph, making navigation faster and dream-cycle consolidation more effective.

### Semantic Search With `~`

The `~` prefix performs a tensor/nearest-neighbor search rather than an exact lookup. Use it when you remember a concept but not the exact alias.

```
akasha/user $ look ~emo:melancholy
# Finds the closest atom semantically matching "melancholy"
# even if the exact alias is emo:nostalgia or emo:sadness
```

### Redirect Output for Archiving

Use the `>` redirect to save query results locally for sharing or analysis.

```
akasha/user $ exp reconstructive_memory 3 > memory_graph.json
Output written to memory_graph.json
```

### Run `cog` After Large Imports

After a big batch job, run `cog` to get a health snapshot and confirm atom counts match expectations.

```
akasha/user $ cog
Atoms in scope: 1,589   (+342 from last pulse)
Links total:    5,201   (+369)
Health: OK
```

### Let the System Dream

After an intensive research session, trigger a manual `dream` cycle or simply leave the system idle. The Jataka engine will consolidate your graph, reinforcing meaningful pathways and pruning noise — so that when you return, your knowledge space is cleaner and more navigable.

---

*AKASHA User Manual — Version 1.3*  
*© 2026 Akasha Protocol Project*
