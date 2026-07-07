# Akasha CLI Quick Reference

**Version 1.1 — July 2026**

Type `help` at the prompt for a live version of this table.  
Type `help -c <model>` for detailed operators of any concept model.

---

## REPL Shell — Interactive Commands

These directives are handled by the shell itself and are not sent to the kernel.

| Command | Description |
|---|---|
| `help` | Command table and concept model list |
| `help -c <model>` | All operators for a concept model (e.g. `help -c note`) |
| `help <cmd>` | Detail for a single command |
| `history [n]` | Show last *n* commands (default 50) |
| `!!` | Repeat last command |
| `!n` | Repeat command number *n* |
| `!-n` | Repeat *n*-th from last (`!-1` = last) |
| `!prefix` | Repeat last command starting with *prefix* |
| `csl` | Open the CSL interactive interpreter |
| `ont.load` | Load acquired ontology (`.ak` files from `ontology/acquired/`) |
| `run <file>` | Submit a `.ak` file as a background JCL batch job |
| `<cmd> > <file>` | Redirect command output to a local file |
| `su root` | Unrestricted root mode — all scope restrictions lifted *(admin only)* |
| `su librarian` | Inject librarian + collective-scope privileges *(admin only)* |
| `su <user>` | Impersonate another user *(admin only)* |
| `su exit` | Return to normal identity |
| `svc ls` | List background services and connected session count |
| `svc stop <name>` | Stop a service *(admin only)* |
| `svc restart <name>` | Restart a service *(admin only)* |
| `exit` | Disconnect and end the session |

---

## Memory

| Command | Args | Description |
|---|---|---|
| `w` | `<text>` | Write an atom into memory |
| `def` | `<name>` | Define a conceptual hub (atom + alias in one step) |
| `r` | `<id>` | Remember — recall an atom by id / alias / `$ref` |
| `rm` | `<id>` | Drop an atom from memory |
| `meta` | `<id> <key> <value>` | Set a metadata key on an atom |

After `w`, `$it` and `$0` point to the new atom. `$1`, `$2`… are older atoms in reverse write order.

> **Weaver** — every `w`, `def`, `al`, and `s.add` queues a background job that links the atom to matching protowords in the nucleus ontology (`sys:refers_to`). This makes atoms semantically reachable through `assoc` and graph traversal without any manual `ln` to ontology nodes.

---

## Links

| Command | Args | Description |
|---|---|---|
| `ln` | `<src> <dst> <rel>` | Create a typed link |
| `ln.rm` | `<src> <dst> <rel>` | Remove a typed link |
| `ln.ls` | `<id>` | List all inbound and outbound links on an atom |
| `ln.+` | `<src> <dst> <rel>` | Reinforce a link weight (+0.1) |

Relations are auto-normalised: `supports` → `@supports`, `sys:is_a` kept as-is.

---

## Aliases

| Command | Args | Description |
|---|---|---|
| `al` | `<id> <name>` | Name an atom (multi-word: `al $it first kiss`) |
| `al.rm` | `<name>` | Remove an alias binding (atom itself is not deleted) |
| `al.ls` | — | List all named atoms |
| `al.find` | `<pattern>` | Find aliases matching a pattern (`%` wildcard) |

---

## Navigation & Exploration

| Command | Args | Description |
|---|---|---|
| `dive` / `d` | `<id>` | Dive into an atom — meaning space, signposts, cosmos field |
| `explore` / `exp` | `<id> [depth]` | BFS graph exploration from a node |
| `tree` | `<target> [depth=2] [follow=<rel>] [format=rich\|ascii]` | Link-traversal tree from an atom, set, or namespace |
| `assoc` | `<id> [axis=] [fill=yes]` | Gap detection — find absent semantic links, number the candidates |
| `dream` | `<id> [axis=] [commit=yes]` | Hypothetical linking — propose new connections via inference |
| `out` | `[id]` | Zoom out to the macro view |
| `<n>` | *(bare number)* | Context-sensitive: follow signpost *(dive)*, create link *(assoc)*, approve proposal *(dream)* |

### `tree` — Link-Traversal Tree

`tree` walks outgoing links from a starting point and renders the result as a tree.

**Target types** — auto-detected from the first argument:

| Target form | What it shows |
|---|---|
| `<alias>` or `<key>` | Atom's outgoing link tree (depth-first BFS) |
| `set:<name>` | Set members as top-level nodes, each with their link sub-trees |
| `ns:<prefix>` | All atoms in a namespace as top-level nodes |

**Optional parameters:**

| Parameter | Default | Description |
|---|---|---|
| `depth=` | `2` | Traversal depth (1–5) |
| `follow=` | *(all)* | Only follow links of this relation type (e.g. `follow=sys:part_of`) |
| `format=` | `rich` | `rich` uses colour + Unicode box-drawing; `ascii` uses plain line-drawing |

```
tree icarus depth=3
tree set:rec:fruit depth=2
tree ns:concept depth=1 follow=thesaurus:related format=ascii
```

A depth-1 tree shows only direct links. Depth-3 shows three levels of connected atoms. Nodes are capped at 20 children and 150 total to keep output readable.

### Navigation Modes

`dive`, `explore`, `assoc`, and `dream` each activate a **named mode** displayed in the prompt:

```
[assoc] akasha/user $      ← in assoc mode
[dream] akasha/user $      ← in dream mode
[dive]  akasha/user $      ← in dive mode
```

| Behaviour | What happens |
|---|---|
| `exit` or `quit` inside a mode | Exits the current mode and returns to the normal prompt. A second `exit` closes the session. |
| Bare number in **assoc** mode | Creates the link for candidate *n* immediately, then refreshes the void list. |
| Bare number in **dream** mode | Approves proposal *n* as a permanent link (strips `tent:` prefix), then refreshes proposals. |
| Bare number in **dive** mode | Navigates into signpost *n*. |
| Any other command | Passes through to the kernel as normal — all commands work inside any mode. |

#### `assoc` — Gap Detection

Scans the focal atom's outgoing links and identifies which **semantic axes** are absent (voids). Candidates are drawn from peer atoms in shared collections.

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

Type a number to create that link and automatically refresh the void list. Use `fill=yes` to accept all top candidates at once.

#### `dream` — Hypothetical Linking

Proposes links that do not yet exist using three complementary strategies:

| Label | Strategy | How it works |
|---|---|---|
| `[struct]` | Structural | Peers in shared collections carry this link — why doesn't the focal atom? |
| `[trans]` | Transitive | A→B, B→C — propose A→C when the path recurs across multiple neighbours |
| `[affin]` | Affinity | Cosine similarity on stored embeddings; Jaccard on keyword-extract sets |

```
[dream] akasha/user $ dream icarus
✦ dream [icarus]  axis=all  status=proposed

Proposals:
     1. tent:calc:associated_with → [awe]        feeling of awe  [emo]     [struct]
     2. tent:calc:associated_with → [hubris]      excessive pride  [transitive]  [trans]
     3. tent:calc:hidden_affinity → [lilienthal]  pioneer of flight  [affinity]  [affin]

     (type 1–3 to approve  |  commit=yes to write all as tent:)
```

Type a number to approve that proposal as a **permanent** link. Use `commit=yes` to write all proposals as `tent:` (tentative) links for later review.

---

## Sets

| Command | Args | Description |
|---|---|---|
| `s.add` | `<name> <id>` | Add atom to a named set |
| `s.rm` | `<name> <id>` | Remove atom from a set |
| `s.ls` | `<name>` | List set members |
| `s.clear` | `<name>` | Remove all members from a set |
| `s.op` | `<op> <result> <a> <b>` | Set operation: `union` / `isect` / `diff` |

---

## Query & Discovery

| Command | Args | Description |
|---|---|---|
| `assoc` | `<id> [axis=] [fill=yes]` | Gap detection: find absent semantic links — see *Navigation & Exploration* for interactive use |
| `cross` | `<concept> …` | Cross-concept atom intersection |
| `cross.axes` | `<concept> …` | Axes available across listed concepts |
| `focus` | `<tokens>` | Set display focus (`@me @group:name @ns:prefix @all`) |
| `scope` | `[get \| reset \| key=val …]` | Show or set session scope state |
| `locale` | `[set <primary> [<supported>]]` | Show or set priority locale |
| `onto.dump` | `<mode> …` | Dump ontology (atoms / links / aliases / sets / namespaces) |
| `onto.report` | `[since=<epoch>] [limit=N] [clear=true]` | Alias overwrite collision report |

---

## Record Model (`rec.*`)

Schema-free structured records. Each record is an Atom; attributes are typed links (`rec:{key}`→value atom).

| Command | Args | Description |
|---|---|---|
| `rec.new` | `type=<t> content=<text> [attr=val …]` | Create a record; inline attrs stored immediately as `rec:` links |
| `rec.set` | `key=<k> attr=<name> val=<v>` | Add or replace an attribute on a record |
| `rec.get` | `key=<k>` | Retrieve a record with all attributes |
| `rec.ls` | `type=<t>` or `in_set=<set>` | List records by type and/or set membership |
| `rec.idx` | `key=<k> sets=<s1,s2,…>` | Add a record to one or more named sets |
| `rec.sum` | `attr=<a> in_set=<set>` | Sum a numeric attribute across records |
| `rec.table` | `in_set=<set> [type=<t>] [limit=N]` | Display records as a formatted CLI table |
| `rec.rm` | `key=<k>` | Delete a record atom |

`rec.new type=fruit` automatically indexes the atom into `set:rec:fruit`. Additional `key=val` pairs become attributes.

```
rec.new type=expense content="Coffee" date=2026-07-01 amount=4.50
rec.ls   type=expense
rec.sum  attr=amount in_set=set:rec:expense
rec.table in_set=set:rec:expense
```

**Applying to existing atoms** — `rec.set` and `rec.idx` are not limited to atoms created with `rec.new`.
They also work on atoms written with `w` or loaded from the ontology.
This is the route for enrolling existing atoms into the rec ecosystem.

```
# Example: scoring and rec-enrolling concept atoms from the ontology
rec.set key=concept:icarus attr=hubris_score val=0.9
rec.set key=concept:icarus attr=mythos_depth val=0.7
rec.idx key=concept:icarus sets=rec:myth_analysis

rec.set key=concept:daedalus attr=hubris_score val=0.4
rec.set key=concept:daedalus attr=mythos_depth val=0.85
rec.idx key=concept:daedalus sets=rec:myth_analysis

# Aggregate and visualise with the same rec.* / quadrant.* commands
rec.table   in_set=set:rec:myth_analysis
quadrant.plot in_set=set:rec:myth_analysis x=hubris_score y=mythos_depth
```

The original atoms (`concept:icarus`, etc.) are preserved as-is.
`rec.set` only adds a `rec:hubris_score → "0.9"` link to the atom;
it does not affect the atom's content or its meaning in the ontology.

---

## Table Model (`table.*`)

Structured tables with explicit columns and typed rows. Supports import/export and CSV round-trip.

| Command | Args | Description |
|---|---|---|
| `table.new` | `name=<n> cols="col:type,…"` | Create a named table |
| `table.col.add` | `table=<t> name=<col>` | Define a column |
| `table.col.ls` | `<table>` | List columns |
| `table.row.add` | `table=<t> col1=val1 …` | Append a row |
| `table.row.get` | `<table> <row_id>` | Retrieve a single row |
| `table.row.rm` | `<table> <row_id>` | Remove a row |
| `table.ls` | `<table> [limit=N]` | List rows (raw form) |
| `table.view` | `<table> [limit=N]` | Display table as a formatted CLI table |
| `table.export` | `<table>` | Export to CSV text |
| `table.import` | `table=<t> csv="…"` | Import from CSV text |
| `table.get` | `<table>` | Show table schema |
| `table.rm` | `<table>` | Delete a table |

`table.view` uses the TextViewConcept protocol and renders via rich — column widths auto-fit, numeric columns right-align.

---

## Lens — Source Scanner and Projection (`lens.*`)

`lens` scans a source, profiles its structure, scores compatible concept models as
projection candidates, and can flatten the result into a `rec:` set or cast it directly
to a chosen concept model.

| Command | Args | Description |
|---|---|---|
| `lens` | `src=<source>` | Scan source and show structure preview + candidates |
| `lens` | `src=<source> follow=<rel> [depth=N]` | BFS tree scan from an atom, following a named link type |
| `lens.cast` | `[signpost=N] [into=<set>] [model=<concept>]` | Project last scan into candidate N (or named model) |
| `lens.flatten` | `into=<set_name>` | Persist last scan as new rec atoms in a named set |

### `src=` — what lens accepts

`lens` accepts **any named source**, not just `tbl:` tables:

| `src=` form | What is scanned |
|---|---|
| `tbl:expenses` | Rows of a structured tbl table |
| `set:rec:fruit` | Members of a rec index set |
| `set:my:custom:set` | Members of any named set |
| `leaf:en` | Atoms in the English word leaf set |
| `concept:mythology` | Start atom for tree traversal (needs `follow=`) |

### Set scan — flat list of atoms

```
# Scan any atom set
lens src=set:rec:fruit            # rec atoms with attribute profile
lens src=leaf:en                  # ontology word atoms — content available, few rec: attrs

# Profile shows attribute coverage; candidates propose matching concept models
lens.flatten into=snapshot        # create new rec atoms from scanned atoms
rec.table in_set=set:snapshot
```

### Tree scan — follow a link type outward from a root

```
# Walk the ontology from a concept node, depth 3, following sys:part_of
lens src=concept:mythology follow=sys:part_of depth=3

# Or follow thematic links from a whiteboard hub
lens src=my_project_hub follow=calc:associated_with depth=2

lens.flatten into=myth_subtree
rec.table in_set=set:myth_subtree
```

### CSV / tbl → rec pipeline

```
table.import table=expenses csv="..."
lens src=tbl:expenses
lens.flatten into=expenses_rec
rec.table in_set=set:expenses_rec
```

### `lens.flatten` vs `rec.set` / `rec.idx`

| Method | What it does | Use when |
|---|---|---|
| `lens.flatten into=X` | Creates **new** rec atoms mirroring each scanned atom | You want a clean rec snapshot without touching the originals |
| `rec.set` + `rec.idx` | Attaches `rec:` attributes **directly** to the existing atom | You want the original atom (ontology node, etc.) to carry rec attributes in-place |

---

## 4-Quadrant Scatter Plot (`quadrant.*`)

Projects a set of rec atoms onto a 48×12 ASCII scatter grid — no browser required.

| Command | Args | Description |
|---|---|---|
| `quadrant.plot` | `in_set=<set> x=<attr> y=<attr> [options]` | Render rec atoms as a 4-quadrant scatter plot |

Key options:

| Option | Description |
|---|---|
| `x_mid=<float>` | X-axis dividing line (default: data midpoint) |
| `y_mid=<float>` | Y-axis dividing line (default: data midpoint) |
| `x_label=<text>` | X-axis display label |
| `y_label=<text>` | Y-axis display label |
| `q1=<text>` | Corner label — top-right (X large, Y large) |
| `q2=<text>` | Corner label — top-left (X small, Y large) |
| `q3=<text>` | Corner label — bottom-left (X small, Y small) |
| `q4=<text>` | Corner label — bottom-right (X large, Y small) |

```
rec.new type=fruit content="Mango"  acidity=0.20 sweetness=0.90
rec.new type=fruit content="Lemon"  acidity=0.95 sweetness=0.10
quadrant.plot in_set=set:rec:fruit x=acidity y=sweetness \
    q1="sweet & tart" q2="sweet & mild" q3="bland" q4="sour"
```

→ Full walkthrough: [`docs/cookbook/quadrant-scatter.md`](../cookbook/quadrant-scatter.md)

---

## Concept Model Casting — any Atom → View

Akasha's concept models function as **projection operators**: they read atoms from any set,
extract the attributes relevant to their view type, and return a TextViewConcept descriptor
that the CLI renderer displays.

```
any atom (rec.new / w / ontology)
    → rec.set / rec.idx        ← attach rec: attributes + enroll in set
        OR
    → lens.flatten             ← create new rec atoms from any scanned source
            ↓
    concept model operator (rec.table / quadrant.plot / …)
        → TextViewConcept (_view = "table" | "scatter" | …)
            → CLI renderer (rich table, ASCII scatter grid, …)
```

### Route A — atoms created with `rec.new` (attributes at write time)

```
rec.new type=wine content="Riesling" acidity=0.75 sweetness=0.85
rec.new type=wine content="Lemon"    acidity=0.95 sweetness=0.10
quadrant.plot in_set=set:rec:wine x=acidity y=sweetness
```

### Route B — existing atoms annotated in-place with `rec.set` + `rec.idx`

Use this when atoms already exist — written with `w`, defined with `def`,
or loaded from the ontology. The original atom is unchanged; only new `rec:` links are added.

```
# Ontology atoms: concept:icarus and concept:daedalus already exist
rec.set key=concept:icarus   attr=hubris_score val=0.9
rec.set key=concept:icarus   attr=mythos_depth val=0.7
rec.idx key=concept:icarus   sets=rec:myth_analysis

rec.set key=concept:daedalus attr=hubris_score val=0.4
rec.set key=concept:daedalus attr=mythos_depth val=0.85
rec.idx key=concept:daedalus sets=rec:myth_analysis

# Now cast to any view
rec.table    in_set=set:rec:myth_analysis
quadrant.plot in_set=set:rec:myth_analysis x=hubris_score y=mythos_depth \
    q1="dangerous glory" q2="quiet craft" q3="forgotten" q4="prudent skill"
```

### Route C — general atom set → `lens.flatten` → rec snapshot

Use this when atoms were not written with rec in mind, and you want a clean,
independently queryable rec copy without touching the originals.

```
# Scan any atom set (ontology subtree, word set, search result set, …)
lens src=concept:mythology follow=sys:part_of depth=3
lens.flatten into=myth_snapshot

# Annotate the new rec atoms post-flatten
rec.table in_set=set:myth_snapshot         # see what was captured
rec.set   key=<key> attr=relevance val=0.8 # annotate individual atoms
quadrant.plot in_set=set:myth_snapshot x=relevance y=…
```

### Same data, different views

No schema declaration is needed at any point. Columns and axes are discovered at
cast time from the `rec:` links actually present on each atom.

```
# Route A, B, or C all end up with the same rec set — same cast commands work
rec.table    in_set=set:rec:wine               # tabular breakdown
rec.sum      attr=acidity in_set=set:rec:wine  # aggregate
quadrant.plot in_set=set:rec:wine x=acidity y=sweetness  # 4-quadrant map
```

| Route | Atoms modified? | New atoms created? | Use when |
|---|---|---|---|
| A — `rec.new` | n/a (new atom) | yes | Starting fresh with structured data |
| B — `rec.set` + `rec.idx` | yes (new links added) | no | Annotating existing atoms in-place |
| C — `lens.flatten` | no | yes (rec copies) | Snapshotting any atom set without touching originals |

---

## Batch Jobs (JCL)

| Command | Args | Description |
|---|---|---|
| `job.ls` | `[owner]` | List background JCL jobs |
| `job.stat` | `<job_id>` | Show status of a specific job |
| `job.submit` | `<steps> [label] [fail_fast]` | Submit a JCL job *(admin / librarian only)* |
| `job.cancel` | `<job_id>` | Cancel a pending job *(admin / librarian only)* |

Use `run <file>` in the REPL to submit a `.ak` file without constructing a steps array.

---

## CSL — Concept Specific Language

| Command | Args | Description |
|---|---|---|
| `csl` | `<filename.csl>` | Run a local `.csl` file |
| `csl.run` | `script="…"` | Execute a CSL script inline |
| `csl.check` | `script="…"` | Validate CSL without executing |
| `csl.build` | `script="…" [out=<path>]` | Transpile CSL to `.ak` (dry run / save to file) |

→ Full CSL reference: [`docs/users/csl-manual.md`](csl-manual.md)

---

## Ontology Management

Regular users can inspect; **librarian** role required to reload/reset; **admin** for genesis.redo.

| Command | Args | Description | Role |
|---|---|---|---|
| `onto.pack.list` | — | List available ontology packs | any |
| `onto.dump` | `<mode> …` | Dump atoms / links / aliases / sets / namespaces | any |
| `onto.report` | `[clear=true]` | Alias overwrite collision report | any |
| `onto.pack.enable` | `<name>` | Enable an optional pack and trigger load | librarian |
| `onto.pack.disable` | `<name>` | Disable a pack (atoms remain until reset) | librarian |
| `onto.reload` | `confirm=RELOAD` | Clear sentinels and re-trigger boot load | librarian |
| `onto.reset` | `confirm=RESET` | ⚠ Wipe nucleus ontology then reload | librarian |
| `onto.scope.drop` | `<scope> confirm=DROP:<scope>` | ⚠ Delete all atoms in a scope | librarian |
| `onto.genesis.redo` | `confirm=GENESIS` | ⚠ Remove genesis anchors for re-rite | admin |

---

## System

| Command | Args | Description |
|---|---|---|
| `status` | — | Memory, session, focus, and JCL queue summary |
| `ping` | — | Kernel liveness check |
| `cog` | — | Full self-awareness pulse |
| `hist` | — | Recent atom stream |
| `ls` | `[limit]` | List last N atoms |
| `passwd` | — | Change your passphrase |
| `ref.set` | `<dim> <target>` | Set a typed context variable (`who` / `where` / `why` …) |
| `ref.get` | `[dim]` | Get typed context variable(s) |
| `fetch` | `<query>` | Fetch from web / Wikipedia |
| `instance.ls` | — | List mounted concept model instances |

---

## Concept Models

Each concept model exposes its own command family. Use `help -c <model>` for the full operator list, or consult the user guide below.

### Data / Analysis Models

| Model | Prefix | Brief description |
|---|---|---|
| **rec** | `rec.` | Schema-free record store — typed attributes, set-based indexing, CLI table view |
| **table** | `table.` | Structured table — explicit columns, row CRUD, CSV import/export, formatted view |
| **lens** | `lens.` | Source scanner — profiles table/rec sources, flattens to rec sets, casts to concept models |
| **quadrant** | `quadrant.` | 4-quadrant ASCII scatter plot from two numeric rec attributes |
| **aggregation** | `ag.` | Grouping and statistical summary — measures, hierarchies |
| **synthesis** | `sy.` | Qualitative analysis — codes, themes, interpretations, claims |

### Research / Field Models

| Model | Prefix | Brief description |
|---|---|---|
| **note** | `n.` | Structured documents with sections, chapters, versioned edits |
| **log** | `log.` | Exploration log — checkpoints, annotations, replay |
| **whiteboard** | `wb.` | Concept pinboard for ideas under active exploration |
| **fieldnote** | `fn.` | Field observation logs with project, region, season context |
| **survey** | `sv.` | Survey forms — questions, options, respondents, responses |
| **fact** | `ft.` | Fact collections with direct, inferred, and absence facts |
| **intelligence** | `intel.` | Decision-cycle: requirements → gaps → tasking → recommendation |

### People / Geography / World Models

| Model | Prefix | Brief description |
|---|---|---|
| **human** | `hum.` | Evidence-based actor records — bonds, assessments, timeline |
| **country** | `country.` | Evidence-grounded country / polity with event sourcing |
| **geo** | `ge.` | Geospatial model — places, coordinates, connections, snapshots |
| **map** | `mp.` / `map.` | Cartographic depictions — editions, features, projections |

### Narrative / Design Models

| Model | Prefix | Brief description |
|---|---|---|
| **world** | `wd.` | Fictional world builder — places, objects, laws, portals |
| **cast** | `cs.` | Fictional character — emotions, wounds, bonds, arcs, masks |
| **homonoia** | `hom.` | Game city — districts, factions, laws, events |
| **presentation** | `pr.` | Slide / layout model — decks, frames, regions |

### Semantic / Ontology Models

| Model | Prefix | Brief description |
|---|---|---|
| **curation** | `cur.` | Premise-bound view construction and conflict folding |
| **correspondence** | `corr.` | Cross-system conceptual mapping with evidence provenance |
| **cockpit** | `cp.` | Dimensional lens navigator with focal point and beacon trail |

→ User manual: [`docs/users/user-manual.md`](user-manual.md)  
→ Concept model spec: [`docs/concept-model/concept-model-spec.md`](../concept-model/concept-model-spec.md)  
→ Cookbook — 4-quadrant scatter: [`docs/cookbook/quadrant-scatter.md`](../cookbook/quadrant-scatter.md)

---

## Context References (`$`-syntax)

| Reference | Meaning |
|---|---|
| `$it` | Most recently written or touched atom |
| `$0`, `$1`, `$2` | Atoms in reverse write order (`$0` = most recent) |
| `$<alias>` | Atom bearing the given alias |
| `=<alias>` | Strict target: bypass late-binding, use exact atom key |

---

## Admin-Only Commands

Hidden from `help`. Require ADMIN role (or `su root`).

| Command | Description |
|---|---|
| `user.ls` | List all users |
| `user.add <id> [role]` | Create a user |
| `user.rm <id>` | Remove a user |
| `user.mod <id> <role>` | Change a user's role |
| `user.id <id>` | Show user details |
| `user.passwd <id>` | Change any user's passphrase |
| `grp.ls [group_id]` | List groups or group members |
| `grp.new <group_id> <admin_id>` | Create a group |
| `grp.add <group_id> <member_id>` | Add a member to a group |
| `grp.rm <group_id> <member_id>` | Remove a member from a group |
| `grp.lib <group_id> grant\|revoke <member>` | Grant/revoke group librarian rights |
| `grp.del <group_id>` | Dissolve a group |

→ Full admin reference: [`docs/users/admin-manual.md`](admin-manual.md)
