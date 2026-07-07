# Akasha CSL Manual

**Concept Specific Language**

---

## Table of Contents

1. [What Is CSL?](#1-what-is-csl)
2. [Two Ways to Use CSL](#2-two-ways-to-use-csl)
3. [CSL vs Shell Commands — A Complete Comparison](#3-csl-vs-shell-commands--a-complete-comparison)
   - [3.1 Why Shell Commands Look Cryptic](#31-why-shell-commands-look-cryptic)
   - [3.2 How CSL Is Different](#32-how-csl-is-different)
   - [3.3 Full CLI ↔ CSL Correspondence Table](#33-full-cli--csl-correspondence-table)
4. [Part I — The Interactive Interpreter](#4-part-i--the-interactive-interpreter)
   - [4.1 Starting and Stopping](#41-starting-and-stopping)
   - [4.2 Writing and Reading Atoms](#42-writing-and-reading-atoms)
   - [4.3 Aliases — Permanent Names for Atoms](#43-aliases--permanent-names-for-atoms)
   - [4.4 Connecting Atoms (Links)](#44-connecting-atoms-links)
   - [4.5 Exploring the Graph](#45-exploring-the-graph)
   - [4.6 Working with Sets](#46-working-with-sets)
   - [4.7 Saving Results with $-Names](#47-saving-results-with--names)
   - [4.8 Block Syntax — Spreading a Command over Multiple Lines](#48-block-syntax--spreading-a-command-over-multiple-lines)
   - [4.9 Comments](#49-comments)
5. [Part II — Concept Model Commands](#5-part-ii--concept-model-commands)
   - [5.1 What Are Concept Models?](#51-what-are-concept-models)
   - [5.2 Fact Collection](#52-fact-collection)
   - [5.3 Curation](#53-curation)
   - [5.4 Intelligence](#54-intelligence)
6. [Part III — Script Mode](#6-part-iii--script-mode)
   - [6.1 When to Use Script Mode](#61-when-to-use-script-mode)
   - [6.2 Writing a CSL Script](#62-writing-a-csl-script)
   - [6.3 Checking Before Running](#63-checking-before-running)
   - [6.4 The Dry Run](#64-the-dry-run)
   - [6.5 Running the Script](#65-running-the-script)
   - [6.6 Saving and Reusing Scripts](#66-saving-and-reusing-scripts)
7. [Value Types Reference](#7-value-types-reference)
8. [Validation and Error Messages](#8-validation-and-error-messages)
9. [Common Mistakes](#9-common-mistakes)

> **→ Akasha Shell Reference:** [`docs/user-manual.md`](user-manual.md)  
> **→ CSL Implementation Spec:** [`docs/csl-spec.md`](csl-spec.md)

---

## 1. What Is CSL?

Akasha stores knowledge as a **graph** — a web of connected pieces of information. Every piece of information is called an **atom**. Atoms are connected to each other by **links**, and each link has a label that describes the relationship (for example: *supports*, *contradicts*, *is a kind of*).

Normally, you interact with this graph through the Akasha shell, typing short commands like `w "some text"` or `ln $0 $1 @supports`. These commands work well for quick operations, but they are terse and do not explain themselves.

**CSL** (Concept Specific Language) is an alternative way to give instructions to Akasha. Instead of short, positional commands, CSL uses explicit `option=value` syntax that reads more like a form or a structured note:

```
Shell:   w "France held sovereignty over Alsace from 1648"
CSL:     write text="France held sovereignty over Alsace from 1648"
```

Both do exactly the same thing. CSL is more words, but the intent is clear at a glance. For multi-step operations that build on each other, CSL is much easier to read, review, and share.

CSL also enables a powerful workflow: you describe your research in natural language to an AI assistant, the AI writes a CSL script for you, you review each step before anything is stored, and then you run it.

---

## 2. Two Ways to Use CSL

### The Interactive Interpreter

You type one CSL command at a time at a `csl>` prompt. Each command runs immediately. This is the best way to get started.

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

### Script Mode

You write all your commands in one block and run them together from the Akasha shell. Before running, you can check for errors and preview every operation.

```
akasha/user $ csl.check script="
write text='Memory is a constructive process.'
write text='Bartlett showed recalled stories drift toward cultural schema.'
"
{"valid": true, "errors": []}
```

### Which should I use?

| Situation | Use |
|-----------|-----|
| Just getting started | Interactive interpreter |
| One or two commands | Interactive interpreter |
| Keeping results across multiple steps | Interactive interpreter |
| Processing many facts from a document | Script mode |
| AI-generated scripts you want to review first | Script mode |
| Repeating the same workflow | Script mode |

**Start with the interactive interpreter.** Move to script mode once you are comfortable.

---

## 3. CSL vs Shell Commands — A Complete Comparison

### 3.1 Why Shell Commands Look Cryptic

The Akasha shell was designed for speed. Its commands are short and positional:

```
akasha/user $ w "Memory is a constructive process."
akasha/user $ ln $0 $1 @supports
akasha/user $ al $it memory.constructive
```

These are powerful, but you have to know:
- What each command means (`w` = write, `ln` = link, `al` = alias)
- What each positional argument means (first? second? third?)
- What `$0`, `$1`, `$it` refer to (the last atoms you worked with, in reverse order)

For quick individual operations, this works well. For reviewing a complex sequence of steps — or for sharing your work with a colleague — it is hard to read.

### 3.2 How CSL Is Different

CSL makes every argument explicit:

```csl
write text="Memory is a constructive process."
link.create src=$a.key dst=$b.key rel="@supports"
alias name="memory.constructive" id=$a.key
```

You do not need to count positions. You do not need to remember what `$0` means. Every option has a name.

CSL also lets you **capture results in named variables** and **chain steps together**:

```csl
$a = write text="Memory is a constructive process."
$b = write text="Bartlett showed recalled stories drift toward cultural schema."
link.create src=$a.key dst=$b.key rel="@supports"
alias name="memory.constructive" id=$a.key
```

This is a complete four-step sequence. The result of each step is available to the next. In the shell, you would have to note down IDs manually or rely on `$0`, `$1` shortcuts.

### 3.3 Full CLI ↔ CSL Correspondence Table

Every shell command has a CSL equivalent. You can use either form inside the CSL interpreter.

> **Reading the table:**  
> CLI columns show the **shell command** and its positional arguments.  
> CSL columns show the **CSL command** with named `key=value` arguments.  
> Arguments in angle brackets `<like this>` are placeholders for actual values.

#### Memory — Writing and Reading Atoms

| Shell command | What it does | CSL equivalent |
|---------------|-------------|----------------|
| `w "text"` | Write a new atom | `write text="text"` |
| `def <name>` | Write an atom and name it | `define name="name"` |
| `def <name> "<description>"` | Write text and name it | `define name="name" description="description"` |
| `r <id>` | Read an atom | `read id="id"` |
| `rm <id>` | Delete an atom | `drop id="id"` |
| `meta <id> <key> <value>` | Set a metadata field | `meta.set id="id" key="key" value="value"` |
| `ls <n>` | List your last N atoms | `sys.ls limit=<n>` |
| `hist` | See recent activity | `sys.history` |

#### Links — Connecting Atoms

| Shell command | What it does | CSL equivalent |
|---------------|-------------|----------------|
| `ln <src> <dst> <rel>` | Create a link between two atoms | `link.create src="src" dst="dst" rel="@rel"` |
| `ln.ls <id>` | List all links from an atom | `link.list id="id"` |
| `ln.+ <src> <dst> <rel>` | Reinforce an existing link | `link.reinforce src="src" dst="dst" rel="@rel"` |

#### Aliases — Naming Atoms

| Shell command | What it does | CSL equivalent |
|---------------|-------------|----------------|
| `al <id> <name>` | Assign a human-readable name | `alias name="name" id="id"` |
| `al.ls` | List all names you have assigned | `alias.list` |
| `al.find <pattern>` | Search for a name | `alias.find name="pattern"` |

#### Navigation — Exploring the Graph

| Shell command | What it does | CSL equivalent |
|---------------|-------------|----------------|
| `look <id>` | View an atom and its connections | `look id="id"` |
| `d <id>` | Same as `look` | `look id="id"` |
| `out` | Zoom out to surrounding context | `out` |
| `exp <id> <depth>` | Explore the graph outward from an atom | `explore id="id" depth=<n>` |

#### Sets — Named Collections

| Shell command | What it does | CSL equivalent |
|---------------|-------------|----------------|
| `s.add <name> <id>` | Add an atom to a named set | `set.add name="name" id="id"` |
| `s.rm <name> <id>` | Remove an atom from a set | `set.rm name="name" id="id"` |
| `s.ls <name>` | List all atoms in a set | `set.ls name="name"` |
| `s.clear <name>` | Empty a set (does not delete atoms) | `set.clear name="name"` |
| `s.op union <result> <a> <b>` | All atoms in set A or set B | `set.op op=union result="result" a="a" b="b"` |
| `s.op isect <result> <a> <b>` | Atoms in both set A and set B | `set.op op=isect result="result" a="a" b="b"` |
| `s.op diff <result> <a> <b>` | Atoms in set A but not in set B | `set.op op=diff result="result" a="a" b="b"` |

#### System

| Shell command | What it does | CSL equivalent |
|---------------|-------------|----------------|
| `ping` | Check that the kernel is running | `sys.ping` |
| `cog` | Full self-awareness pulse | `sys.cogito` |

> **→ For full shell command documentation, see the Akasha User Manual, §6:** [`docs/user-manual.md`](user-manual.md#6-kernel-commands-reference)

---

## 4. Part I — The Interactive Interpreter

### 4.1 Starting and Stopping

From the Akasha shell, type `csl` to open the interpreter:

```
akasha/user $ csl
Akasha CSL interpreter (Phase 1). Type 'exit' or Ctrl-D to quit.
csl>
```

The `csl>` prompt means the interpreter is ready. To return to the Akasha shell, type `exit` or press Ctrl-D.

### 4.2 Writing and Reading Atoms

An **atom** is a single piece of information — a sentence, a thought, a fact, a quote. You store it with `write`:

```
csl> write text="Memory is not a recording device. It reconstructs the past."
{
  "id": "a3f7...c19e"
}
```

Akasha returns an **ID** — a long string of letters and numbers that uniquely identifies this atom. Every atom has one.

To read an atom back:

```
csl> read id="a3f7...c19e"
{
  "content": "Memory is not a recording device. It reconstructs the past."
}
```

To write several atoms in sequence:

```
csl> write text="Frederic Bartlett showed in 1932 that recalled stories drift toward cultural schema."
{
  "id": "b80d...44fa"
}

csl> write text="Two people can remember the same event in completely incompatible ways — both sincerely."
{
  "id": "cc29...08b2"
}
```

To see your recent atoms:

```
csl> sys.ls limit=5
[
  {"id": "cc29...08b2", "content": "Two people can remember..."},
  {"id": "b80d...44fa", "content": "Frederic Bartlett showed..."},
  {"id": "a3f7...c19e", "content": "Memory is not a recording device..."}
]
```

**Shell equivalent:** `ls 5`

### 4.3 Aliases — Permanent Names for Atoms

#### Two kinds of names in CSL

CSL gives you two ways to refer to an atom by name. They are **very different**:

| | `$variable` | Alias |
|-|-------------|-------|
| Where it lives | Your session only | Stored permanently in the graph |
| When it disappears | When you type `exit` | Never (unless you delete it) |
| Who can use it | You, this session | Anyone with access to the same scope |
| Purpose | Chaining steps together | Building a lasting vocabulary |

**`$variable`** is a temporary label. Write `$src = ft.src.add ...` and `$src` holds the result for the rest of this session. Exit and it is gone.

**Alias** is a permanent name woven into the graph itself. Name an atom `alsace.sovereignty.1648` and that name will be there next week, next year. You — and your collaborators — can use it in any command, any session.

Think of aliases as the index of your knowledge graph. The more carefully you name things, the easier they are to find and connect later.

#### Assigning a name to an existing atom

```
csl> alias name="memory.constructive" id="a3f7...c19e"
{"status": "ok"}
```

Now `memory.constructive` can be used anywhere instead of `a3f7...c19e`.

#### Creating an atom and naming it at the same time

The `define` command writes an atom and names it in one step:

```
csl> define name="reconstructive_memory" description="The idea that memory actively reconstructs the past, rather than replaying a stored recording."
{
  "id": "d10a...77c3",
  "alias": "reconstructive_memory"
}
```

You can also combine `define` with a `$-name` to use the result in the same session:

```
csl> $hub = define name="reconstructive_memory" description="Memory reconstructs rather than replays."
csl> link.create src=$hub.key dst="bartlett.finding" rel="sys:evidenced_by"
```

#### Using an alias anywhere

Once named, you can use the alias as a value wherever an atom ID is expected — in `read`, `link.create`, `look`, `explore`, `set.add`, and anywhere else:

```
csl> read id="memory.constructive"
{"content": "Memory is not a recording device. It reconstructs the past."}

csl> link.create src="reconstructive_memory" dst="memory.constructive" rel="sys:is_a"
{"status": "linked"}

csl> look id="reconstructive_memory"
--- Atom: reconstructive_memory ---
Memory reconstructs rather than replays.
Signposts:
  --> memory.constructive  [sys:is_a]
  --> bartlett.finding     [sys:evidenced_by]

csl> set.add name="memory_project" id="memory.constructive"
{"status": "added"}
```

#### Listing all your aliases

```
csl> alias.list
[
  {"name": "memory.constructive",   "atom_id": "a3f7...c19e"},
  {"name": "bartlett.finding",      "atom_id": "b80d...44fa"},
  {"name": "memory.incompatible",   "atom_id": "cc29...08b2"},
  {"name": "reconstructive_memory", "atom_id": "d10a...77c3"}
]
```

#### Searching for aliases by pattern

Use `%` as a wildcard:

```
csl> alias.find name="memory%"
[
  {"name": "memory.constructive",  "atom_id": "a3f7...c19e"},
  {"name": "memory.incompatible",  "atom_id": "cc29...08b2"}
]

csl> alias.find name="%alsace%"
[
  {"name": "alsace.sovereignty.1648", "atom_id": "e44d...99ab"},
  {"name": "alsace.occupation.1871",  "atom_id": "f71b...cc10"},
  {"name": "alsace.dejure.1939",      "atom_id": "g92c...aa04"}
]
```

`alias.find name="%"` with a single `%` lists everything — same as `alias.list`.

#### Naming conventions

Aliases are free-form, but using dots as separators creates a natural namespace:

```
# Topic . concept . qualifier
memory.constructive
memory.incompatible

# Domain . subject . time or perspective
alsace.sovereignty.1648
alsace.occupation.1871
alsace.dejure.1939
alsace.defacto.1942

# Project . type . detail
kaliningrad.req.q3_2024
kaliningrad.assessment.situation
```

A consistent naming scheme makes `alias.find` much more powerful: `alias.find name="alsace.%"` finds every atom in your Alsace project instantly.

#### Aliases with saved variables — the full pattern

In practice, you will use both together: `$-names` for the current session's flow, and `alias` for atoms that need to be found later:

```
csl> # Create and name the atom — $hub holds the result this session
csl> $hub = define:
...     label = "reconstructive_memory"
...     text  = "Memory actively reconstructs the past rather than replaying it."
...

csl> # Use $hub.key to build links without typing the full key
csl> $detail_a = define name="memory.constructive" description="Memory is a constructive process."
csl> $detail_b = define name="bartlett.finding" description="Bartlett 1932: recalled stories drift toward cultural schema."

csl> link.create src=$hub.key dst=$detail_a.key rel="sys:is_a"
csl> link.create src=$hub.key dst=$detail_b.key rel="sys:evidenced_by"

csl> # Next session: no $-names — use aliases directly
csl> look id="reconstructive_memory"
csl> link.create src="reconstructive_memory" dst="new_finding_2024" rel="sys:evidenced_by"
```

**Shell equivalents:** `al <id> <name>`, `al.ls`, `al.find <pattern>`, `def <label> "<text>"`  
**→ User Manual §6.3:** [`docs/user-manual.md`](user-manual.md#63-aliases)

### 4.4 Connecting Atoms (Links)

A **link** is a directed connection between two atoms. It always has a **label** (called a `rel`) that describes the relationship.

```
csl> link.create src="memory.constructive" dst="bartlett.finding" rel="@evidenced_by"
{"status": "linked"}
```

This says: the idea that *memory is constructive* is evidenced by *Bartlett's 1932 finding*.

You can use atom IDs, aliases, or saved results (see §4.7) as the `from` and `to` values.

**Common relationship labels:**

| Label | Meaning |
|-------|---------|
| `@supports` | A supports B — B is more credible because of A |
| `@contradicts` | A contradicts B — they make incompatible claims |
| `@evidenced_by` | A is supported by evidence B |
| `@implies` | A logically leads to B |
| `@causes` | A causes B |
| `@part_of` | A is a component of B |
| `sys:is_a` | A is a type of B |
| `sys:evidenced_by` | Structural/ontological evidence relation |

**Late-binding: linking to atoms that don't exist yet.**  
If the alias in `dst` (or `src`) is not yet registered, Akasha does not fail. The kernel falls back to the bare-segment proto-word, creating it on demand, and stores the link with a valid key immediately. When the target atom is defined later, it receives a `specializes` link to that proto-word, making the full path traversable.

```
csl> link.create src="memory.constructive" dst="future.discovery" rel="@implies"
{"status": "linked"}
# 'future.discovery' not yet registered → proto-word 'discovery' created;
# link stored correctly. When 'future.discovery' is defined later, it
# specializes 'discovery' and the path becomes traversable.
```

**Strict targeting (`=` prefix, opt-in).**  
To target a specific future namespace atom rather than its proto-word, prefix the alias with `=`. The alias string is stored as a placeholder for that exact atom — no proto-word fallback is applied.

```
csl> link.create src="quote:shakespeare_et_tu" dst="=nar:tragedy" rel="@exemplifies"
{"status": "linked"}
# Stores "nar:tragedy" as a placeholder; waits for that exact atom.
```

Use this only when two distinct namespace atoms share a proto-word and you need to target one specifically.

To see all connections of an atom:

```
csl> link.list id="reconstructive_memory"
{
  "outgoing": [
    {"to": "memory.constructive", "rel": "sys:is_a"},
    {"to": "bartlett.finding",    "rel": "sys:evidenced_by"}
  ],
  "incoming": []
}
```

To make a connection stronger (reinforce it):

```
csl> link.reinforce src="reconstructive_memory" dst="bartlett.finding" rel="sys:evidenced_by"
{"status": "reinforced", "new_weight": 2}
```

**Shell equivalents:** `ln <src> <dst> <rel>`, `ln.ls <id>`, `ln.+ <src> <dst> <rel>`

#### A complete example — building a small knowledge cluster

```
csl> # Create three atoms
csl> define:
...     label = "memory.constructive"
...     text  = "Memory is not a recording device — it reconstructs the past from fragments."
...
{"id": "a3f7...c19e", "alias": "memory.constructive"}

csl> define:
...     label = "bartlett.finding"
...     text  = "Bartlett showed in 1932 that recalled stories drift toward the subject's cultural schema."
...
{"id": "b80d...44fa", "alias": "bartlett.finding"}

csl> define:
...     label = "memory.incompatible"
...     text  = "Two people can remember the same event in incompatible ways — both sincerely."
...
{"id": "cc29...08b2", "alias": "memory.incompatible"}

csl> # Connect them
csl> link.create src="memory.constructive" dst="bartlett.finding"  rel="@evidenced_by"
{"status": "linked"}

csl> link.create src="bartlett.finding" dst="memory.incompatible" rel="@implies"
{"status": "linked"}

csl> link.create src="memory.constructive" dst="memory.incompatible" rel="@implies"
{"status": "linked"}

csl> # Create a hub atom that ties all three together
csl> define:
...     label = "reconstructive_memory"
...     text  = "The umbrella concept: memory actively reconstructs rather than replays."
...
{"id": "d10a...77c3", "alias": "reconstructive_memory"}

csl> link.create src="reconstructive_memory" dst="memory.constructive"  rel="sys:is_a"
csl> link.create src="reconstructive_memory" dst="bartlett.finding"     rel="sys:evidenced_by"
csl> link.create src="reconstructive_memory" dst="memory.incompatible"  rel="sys:implies"
```

You have now built a connected cluster of four atoms with six links.

### 4.5 Exploring the Graph

Once you have atoms and links, you can explore the structure.

**Look at one atom and its connections:**

```
csl> look id="reconstructive_memory"
--- Atom: reconstructive_memory ---
The umbrella concept: memory actively reconstructs rather than replays.

Signposts (links):
  --> memory.constructive     [sys:is_a]
  --> bartlett.finding        [sys:evidenced_by]
  --> memory.incompatible     [sys:implies]
```

**Explore outward from an atom (breadth-first):**

```
csl> explore id="reconstructive_memory" depth=2
[Depth 0] reconstructive_memory
  [Depth 1] memory.constructive   (sys:is_a)
    [Depth 2] bartlett.finding    (@evidenced_by)
  [Depth 1] bartlett.finding      (sys:evidenced_by)
    [Depth 2] memory.incompatible (@implies)
  [Depth 1] memory.incompatible   (sys:implies)
```

`depth=1` shows only immediate neighbours. `depth=2` shows one step further. Start with `depth=2` and increase if needed.

**Shell equivalents:** `look <id>`, `exp <id> <depth>`

### 4.6 Working with Sets

A **set** is a named collection of atoms. Think of it as a labelled basket — you can put any number of atoms in it, and atoms can belong to multiple baskets at the same time. Removing an atom from a set does not delete the atom itself.

Sets are useful for:
- Grouping atoms by topic or project
- Collecting atoms that need review
- Doing bulk operations on a group of atoms

#### Adding atoms to a set

```
csl> set.add name="memory_project" id="reconstructive_memory"
{"status": "added"}

csl> set.add name="memory_project" id="memory.constructive"
{"status": "added"}

csl> set.add name="memory_project" id="bartlett.finding"
{"status": "added"}

csl> set.add name="memory_project" id="memory.incompatible"
{"status": "added"}
```

#### Listing what is in a set

```
csl> set.ls name="memory_project"
[
  {"id": "d10a...77c3", "alias": "reconstructive_memory"},
  {"id": "a3f7...c19e", "alias": "memory.constructive"},
  {"id": "b80d...44fa", "alias": "bartlett.finding"},
  {"id": "cc29...08b2", "alias": "memory.incompatible"}
]
```

#### Set operations — finding atoms in common or only in one set

Suppose you have two projects and want to find overlap:

```
csl> # First project: memory research
csl> set.add name="memory_project"   id="reconstructive_memory"
csl> set.add name="memory_project"   id="bartlett.finding"

csl> # Second project: psychology of testimony
csl> set.add name="testimony_project" id="bartlett.finding"
csl> set.add name="testimony_project" id="memory.incompatible"

csl> # Find atoms that appear in BOTH sets (intersection)
csl> set.op op=isect result="both_projects" a="memory_project" b="testimony_project"
{"status": "ok", "count": 1}

csl> set.ls name="both_projects"
[
  {"id": "b80d...44fa", "alias": "bartlett.finding"}
]

csl> # Find ALL atoms across both sets (union)
csl> set.op op=union result="all_atoms" a="memory_project" b="testimony_project"
{"status": "ok", "count": 4}

csl> # Find atoms only in the memory project but NOT in testimony (difference)
csl> set.op op=diff result="memory_only" a="memory_project" b="testimony_project"
{"status": "ok", "count": 1}

csl> set.ls name="memory_only"
[
  {"id": "d10a...77c3", "alias": "reconstructive_memory"}
]
```

#### Removing from a set or clearing it

```
csl> set.rm name="memory_project" id="bartlett.finding"
{"status": "removed"}

csl> set.clear name="temp_set"
{"status": "cleared"}
```

**Shell equivalents:** `s.add <name> <id>`, `s.rm <name> <id>`, `s.ls <name>`, `s.clear <name>`, `s.op union|isect|diff <result> <a> <b>`

### 4.7 Saving Results with $-Names

When you run a command, the result disappears after being shown — you would have to copy the ID to use it in the next command. CSL gives you a much easier way: **save the result under a name**.

Write `$name =` before any command:

```
csl> $hub = define name="reconstructive_memory" description="Memory actively reconstructs the past."
  -> $hub = <define result>
{
  "id": "d10a...77c3",
  "alias": "reconstructive_memory"
}
```

The `-> $hub` line confirms the result was saved. Now use `$hub` anywhere:

```
csl> $atom_a = write text="Memory is constructive."
csl> $atom_b = write text="Bartlett demonstrated schema drift in 1932."

csl> link.create src=$atom_a.key dst=$atom_b.key rel="@evidenced_by"
```

`$atom_a.key` automatically becomes the key that was returned when `$atom_a` was created.

**What fields can you access?** It depends on what the command returns. Common ones:

| Command | Available fields |
|---------|-----------------|
| `write` | `.key` |
| `define` | `.key`, `.alias` |
| `ft.src.add` | `.source_id` |
| `ft.fact.add` | `.fact_id` |
| `cur.premise` | `.premise_id` |
| `cur.view` | `.view_id` |
| `intel.req` | `.requirement_id` |
| `intel.assess` | `.assessment_id` |
| `intel.recommend` | `.recommendation_id` |

You can only access one level: `$name.field` — not `$name.field.subfield`.

**Names persist for the entire interpreter session.** If you type `exit` and return, they are gone.

#### A complete example with saved results

```
csl> # Write two atoms, save the results
csl> $memory = define:
...     label = "memory.constructive"
...     text  = "Memory reconstructs rather than replays."
...

csl> $bartlett = define:
...     label = "bartlett.finding"
...     text  = "Bartlett 1932: recalled stories drift toward cultural schema."
...

csl> # Connect them using saved IDs — no copying required
csl> link.create src=$memory.key dst=$bartlett.key rel="@evidenced_by"
{"status": "linked"}

csl> # Add both to a set using saved IDs
csl> set.add name="reading_list" id=$memory.key
csl> set.add name="reading_list" id=$bartlett.key
```

### 4.8 Block Syntax — Spreading a Command over Multiple Lines

When a command has many options, writing it all on one line becomes hard to read. Block syntax lets you spread options across multiple lines.

Write the command name followed by `:`, press Enter, then write each option on its own indented line. Press Enter on a blank line to finish:

```
csl> $src = define:
...     label = "alsace.sovereignty.1648"
...     text  = "By the Peace of Westphalia (1648), France gained sovereign rights over most of Alsace."
...
{"id": "e44d...99ab", "alias": "alsace.sovereignty.1648"}
```

The `...` prompt means the interpreter is waiting for more lines. A blank line closes the block.

Block syntax is especially useful for concept model commands (§5), where commands often have five or more options.

### 4.9 Comments

Add notes to yourself with `#` or `//`. They are ignored when the command runs:

```
csl> # This atom represents the de jure position under international law
csl> define name="alsace.dejure.1939" description="France held de jure sovereignty as of 1939."
```

Comments are useful for documenting your intent, especially in multi-step sessions.

---

## 5. Part II — Concept Model Commands

### 5.1 What Are Concept Models?

The commands in §4 — `write`, `read`, `define`, `link.create`, `set.add` — are **general-purpose**. They store text and build connections without imposing any particular structure.

Akasha also includes **concept models**: pre-built structures for specific types of intellectual work. Instead of building everything from scratch, a concept model gives you commands that match the way a particular task is actually done.

Three concept models are available for researchers:

| Model | What it is for |
|-------|---------------|
| **Fact collection** | Recording what sources say, how credible they are, what is absent |
| **Curation** | Organising competing claims about the same topic under different viewpoints |
| **Intelligence** | Working through a structured analytical process from question to decision |

You never have to use these models — `write`, `link.create`, and sets are always available. But for research, analysis, and structured knowledge work, the concept models save considerable effort and create a structured, traceable record.

### 5.2 Fact Collection

Fact collection is for recording information from sources: books, articles, interviews, datasets. It tracks what you found, where you found it, and how reliable that source is.

**The basic workflow:**

1. Register the source
2. Record facts from that source (with the source ID linking them)
3. Record direct quotes
4. Note gaps in the evidence

#### Example: Recording a newspaper article

```
csl> # Step 1: Register the source
csl> $src = ft.src.add:
...     kind        = newspaper
...     title       = "The Guardian — Climate Policy Report — 12 June 2023"
...     credibility = 0.82
...
  -> $src = <ft.src.add result>
{
  "status": "created",
  "source_id": "a3f9...cc01"
}

csl> # Step 2: Record facts from this source
csl> $f1 = ft.fact.add:
...     fact_type = event
...     content   = "UK government confirmed the 2035 deadline for ending new petrol car sales."
...     source_id = $src.source_id
...
{"status": "created", "fact_id": "b72c...d304"}

csl> $f2 = ft.fact.add:
...     fact_type = statement
...     content   = "The policy was announced without an independent economic assessment."
...     source_id = $src.source_id
...
{"status": "created", "fact_id": "c81e...a203"}

csl> # Step 3: Record a direct quote
csl> ft.claim:
...     speaker   = "Transport Secretary"
...     content   = "This is a historic step toward a cleaner, greener future."
...     source_id = $src.source_id
...

csl> # Step 4: Note missing evidence
csl> ft.absent:
...     description = "No independent cost-benefit analysis of the 2035 transition found in this source."
...     source_id   = $src.source_id
...

csl> # Step 5: Check the collection
csl> ft.diagnose
```

#### Example: Recording a historical document

```
csl> $src_vt = ft.src.add:
...     kind        = official_doc
...     title       = "Treaty of Versailles, Article 51"
...     credibility = 0.99
...

csl> ft.fact.add:
...     fact_type = event
...     content   = "Alsace-Lorraine was returned to France under Article 51 of the Treaty of Versailles, signed 28 June 1919."
...     source_id = $src_vt.source_id
...     as_of     = "1919-06-28"
...

csl> ft.fact.add:
...     fact_type = statement
...     content   = "The return was unconditional and without plebiscite, unlike the 1871 annexation."
...     source_id = $src_vt.source_id
...
```

#### Source kinds and what they mean

| Kind | Use for |
|------|---------|
| `newspaper` | Press articles, journalism |
| `website` | Online sources, web pages |
| `book` | Published books |
| `journal` | Academic papers |
| `official_doc` | Treaties, laws, government documents |
| `interview` | First-hand accounts |
| `broadcast` | TV, radio, podcast |
| `dataset` | Statistical or structured data |

#### Credibility — a guide

| Range | Meaning |
|-------|---------|
| 0.95–1.00 | Primary source, verified, authoritative |
| 0.80–0.95 | Established outlet, usually reliable |
| 0.60–0.80 | Secondary or aggregated; treat with care |
| 0.40–0.60 | Unverified; corroborate before relying on it |
| 0.00–0.40 | Speculative or unreliable |

#### Fact collection command reference

| Command | Required options | Description |
|---------|-----------------|-------------|
| `ft.src.add` | `kind`, `title` | Register a source |
| `ft.src.ls` | — | List registered sources |
| `ft.fact.add` | `fact_type`, `content`, `source_id` | Add a fact |
| `ft.claim` | `speaker`, `content`, `source_id` | Record a direct quote |
| `ft.absent` | `description`, `source_id` | Note missing evidence |
| `ft.ls` | — | List facts in this collection |
| `ft.open` | `fact_id` | Open an existing collection |
| `ft.rm` | `fact_id` | Remove a collection |
| `ft.trace` | `fact_id` | Show provenance of a fact |
| `ft.diagnose` | — | Check the collection for problems |

### 5.3 Curation

**What curation is for:**  
When you have multiple sources saying different — or even contradictory — things about the same topic, curation helps you organise them without simply picking a winner. It lets you maintain multiple perspectives simultaneously.

**The key principle:** Curation never modifies the original source atoms. It creates a separate analytical layer above them. You compare and resolve, while all the original evidence stays intact and traceable.

**A useful analogy:** Imagine you have three historians who each wrote different things about who controlled Alsace in 1942. Curation is like creating a transparent sheet over their writings: you can write your analysis on the sheet, compare what they said, and draw conclusions — without crossing anything out in the original texts.

**The workflow:**

1. Open a curation workspace
2. Register source atoms as **inputs** (by reference, not by copying)
3. Define **premises** — the analytical viewpoint you are working from (a time period, a legal perspective)
4. Create **views** — one analysis window per premise
5. Resolve conflicts with **fold** commands
6. Record **conclusions**

#### Example: Alsace sovereignty 1871–1945

This example curates three competing claims about who controlled Alsace:

```
csl> # Open a workspace
csl> cur.new title="Sovereignty of Alsace-Lorraine 1871–1945"
{"status": "created", "curation_id": "c41d...e820"}

csl> # Register three existing source atoms as inputs (references only)
csl> $i_fr  = cur.input ref_id="bartlett.de_jure_france"  role=sovereignty
csl> $i_de  = cur.input ref_id="german.occupation.record" role=administration
csl> $i_vt  = cur.input ref_id="versailles.article51"     role=treaty

csl> # Define two premises — different analytical lenses
csl> $p_jure = cur.premise:
...     label           = de_jure_1939
...     as_of           = "1939-09-01"
...     perspective     = de_jure
...     conflict_policy = perspective_preferred
...

csl> $p_facto = cur.premise:
...     label           = de_facto_1942
...     as_of           = "1942-01-01"
...     perspective     = de_facto
...     conflict_policy = most_recent
...

csl> # Create views (one per premise)
csl> $v_jure  = cur.view premise_id=$p_jure.premise_id  label="Alsace: de jure 1939"
csl> $v_facto = cur.view premise_id=$p_facto.premise_id label="Alsace: de facto 1942"

csl> # Inside the de facto view: resolve the conflict between French and German claims
csl> cur.fold:
...     view_id             = $v_facto.view_id
...     competing_input_ids = [$i_fr.input_id, $i_de.input_id]
...     winner_id           = $i_de.input_id
...     rationale           = "German administration atom is more recent per most_recent policy"
...

csl> # Record conclusions for each view
csl> cur.conclude:
...     view_id         = $v_facto.view_id
...     statement       = "As of 1942, Alsace was under German de facto administration."
...     conclusion_type = state
...     confidence      = 0.85
...

csl> cur.conclude:
...     view_id         = $v_jure.view_id
...     statement       = "France retained de jure sovereignty under international law throughout the occupation."
...     conclusion_type = state
...     confidence      = 0.92
...

csl> # Check for consistency
csl> cur.diagnose
```

Both conclusions can coexist — one describes the legal reality, the other describes what was happening on the ground.

#### Conflict policies

| Policy | What it means |
|--------|--------------|
| `perspective_preferred` | Keep only inputs that match the premise's perspective label |
| `most_recent` | The most recently written atom wins |
| `highest_credibility` | The most credible source wins |
| `manual` | No automatic resolution — you resolve explicitly with `cur.fold` |

#### Curation command reference

| Command | Description |
|---------|-------------|
| `cur.new` | Create a curation workspace |
| `cur.open` | Open an existing workspace |
| `cur.ls` | List workspaces |
| `cur.rm` | Remove a workspace (soft delete) |
| `cur.premise` | Define a premise (time, perspective, policy) |
| `cur.input` | Register a source atom as input |
| `cur.view` | Create a view under a premise |
| `cur.fold` | Resolve competing inputs inside a view |
| `cur.conclude` | Record a conclusion for a view |
| `cur.dispute` | Flag an unresolved disagreement |
| `cur.trace` | Show the full reasoning chain |
| `cur.diagnose` | Check for missing inputs, open disputes |

### 5.4 Intelligence

Intelligence is a structured workflow for analytical questions. It takes you from *"What do I need to know?"* all the way through to *"What did we decide and why?"*, leaving a documented record at every step.

**When to use it:**  
When your research has a decision at the end — not just passive accumulation of knowledge. Intelligence is for questions like: *Is this claim credible? What risks does this situation present? What should we recommend?*

**The cycle:**

```
Requirement → Scan → Gap → Tasking → Assessment → Estimate → Option → Recommendation → Decision
```

You do not have to complete every stage. Start with the ones relevant to your work.

#### Example: Assessing the status of Kaliningrad

```
csl> # Open a workspace
csl> intel.new title="Kaliningrad strategic assessment Q3 2024"
{"status": "created"}

csl> # State the question
csl> $req = intel.req:
...     question         = "What is the current legal and factual control status of Kaliningrad, and what are the primary risk vectors?"
...     requirement_type = strategic
...     priority         = high
...

csl> # Scan existing atoms for relevance
csl> intel.scan:
...     requirement_id = $req.requirement_id
...     target_id      = "kaliningrad.sovereignty.1991"
...     scan_type      = fact
...     signal         = "Russian sovereignty confirmed by the 1991 border treaty"
...

csl> intel.scan:
...     requirement_id = $req.requirement_id
...     target_id      = "kaliningrad.curation.v1"
...     scan_type      = curation_view
...     signal         = "De facto / de jure gap documented for 1939–1945 period"
...

csl> # Record what is missing
csl> $gap = intel.gap:
...     requirement_id = $req.requirement_id
...     description    = "No post-2022 independent sovereignty review on record"
...     gap_type       = outdated
...     severity       = high
...

csl> # Task a collection action to fill the gap
csl> intel.task:
...     requirement_id = $req.requirement_id
...     gap_id         = $gap.gap_id
...     description    = "Collect 2022–2024 academic and legal sources on Kaliningrad status"
...     tasking_type   = collect
...     priority       = high
...

csl> # Assessment — after completing the tasking
csl> $assess = intel.assess:
...     requirement_id  = $req.requirement_id
...     assessment_type = situation
...     judgment        = "Russia retains uncontested de facto and internationally recognised de jure control over Kaliningrad."
...     confidence      = 0.88
...

csl> # Estimate the probability of a specific event
csl> $est = intel.estimate:
...     requirement_id = $req.requirement_id
...     estimate_type  = probability
...     statement      = "Probability of a formal legal challenge to Russian sovereignty within 5 years: below 5%."
...     basis          = [$assess.assessment_id]
...     probability    = 0.04
...     confidence     = 0.70
...

csl> # Recommendation
csl> $rec = intel.recommend:
...     requirement_id = $req.requirement_id
...     statement      = "Close requirement. No ongoing tracking required. Revisit if NATO–Russia relations deteriorate significantly."
...     confidence     = 0.82
...

csl> # Record the decision
csl> intel.decision:
...     recommendation_id = $rec.recommendation_id
...     decision_status   = accepted
...     decided_by        = "Research Director"
...     reason            = "Assessment complete and approved for filing."
...

csl> # See the full cycle for this requirement
csl> intel.cycle requirement_id=$req.requirement_id
```

#### Intelligence command reference

| Command | Description |
|---------|-------------|
| `intel.new` | Create an intelligence workspace |
| `intel.open` | Open an existing workspace |
| `intel.ls` | List workspaces |
| `intel.rm` | Remove a workspace (soft delete) |
| `intel.req` | State an information requirement (the question) |
| `intel.scan` | Scan an existing atom for relevance to a requirement |
| `intel.gap` | Record a gap in the available evidence |
| `intel.task` | Task a collection action to fill a gap |
| `intel.assess` | Record a situation or risk assessment |
| `intel.estimate` | Record a probabilistic estimate |
| `intel.option` | Define a decision option |
| `intel.recommend` | Record a recommendation |
| `intel.decision` | Record an accepted or rejected decision |
| `intel.dispute` | Flag an analytic disagreement |
| `intel.cycle` | View the full cycle for a requirement |
| `intel.trace` | Show provenance |
| `intel.diagnose` | Check cycle completeness |

---

## 6. Part III — Script Mode

### 6.1 When to Use Script Mode

The interactive interpreter is great for exploration and for sessions you build up step by step. Switch to script mode when:

- You have many commands to run at once (more than five or six)
- An AI assistant has generated a CSL script from your notes
- You want to save and reuse a workflow
- You want to carefully review everything before committing

Script mode is accessed from the **Akasha shell** (the `akasha/user $` prompt), not from inside the CSL interpreter.

### 6.2 Writing a CSL Script

A CSL script is just CSL commands, written out in a text block. Every rule from the interactive interpreter applies: `$name =` assignments, block syntax, comments.

Example script (you can paste this as the `script=` value):

```
# Research: UK 2035 petrol car ban
# Source: The Guardian, 12 June 2023

$src = ft.src.add:
    kind        = newspaper
    title       = "The Guardian — UK 2035 Petrol Ban"
    credibility = 0.82

$f1 = ft.fact.add:
    fact_type = event
    content   = "UK government confirmed 2035 deadline for ending new petrol car sales."
    source_id = $src.source_id

$f2 = ft.fact.add:
    fact_type = statement
    content   = "Policy announced without independent economic assessment."
    source_id = $src.source_id

ft.claim:
    speaker   = "Transport Secretary"
    content   = "This is a historic step toward a cleaner, greener future."
    source_id = $src.source_id

ft.absent:
    description = "No independent cost-benefit analysis found."
    source_id   = $src.source_id

ft.diagnose
```

### 6.3 Checking Before Running

Before running any script, check it for errors:

```
akasha/user $ csl.check script="
$src = ft.src.add kind=newspaper title='The Guardian' credibility=0.82
ft.fact.add fact_type=event content='UK confirmed 2035 ban' source_id=$src.source_id
"
{
  "valid": true,
  "errors": []
}
```

If there are errors:

```
{
  "valid": false,
  "errors": [
    {
      "line": 2,
      "error": "Variable '$src' used before assignment",
      "suggestion": "Assign a value to $src before using it",
      "level": "error"
    }
  ]
}
```

Fix all `"level": "error"` errors before proceeding. `"level": "warning"` errors are reported but do not stop execution.

### 6.4 The Dry Run

Once the script is valid, preview exactly what will happen — without writing anything to the graph:

```
akasha/user $ csl.dry script="
$src = ft.src.add kind=newspaper title='The Guardian' credibility=0.82
ft.fact.add fact_type=event content='UK confirmed 2035 ban' source_id=$src.source_id
"
{
  "operations": [
    {
      "method": "ft.src.add",
      "params": {"kind": "newspaper", "title": "The Guardian", "credibility": 0.82},
      "assigns_to": "src",
      "source_line": 1
    },
    {
      "method": "ft.fact.add",
      "params": {
        "fact_type": "event",
        "content": "UK confirmed 2035 ban",
        "source_id": {"__ref__": "$src.source_id"}
      },
      "assigns_to": null,
      "source_line": 2
    }
  ]
}
```

The `"__ref__": "$src.source_id"` entry means: at runtime, fill in the `source_id` value from the result of the `$src` step.

You can also get a plain-English summary with `csl.explain`:

```
akasha/user $ csl.explain script="..."
{
  "explanation": "Line 1: $src = ft.src.add(kind='newspaper', title='The Guardian', credibility=0.82)\nLine 2: ft.fact.add(fact_type='event', content='UK confirmed 2035 ban', source_id=...)"
}
```

### 6.5 Running the Script

```
akasha/user $ csl.run script="
$src = ft.src.add kind=newspaper title='The Guardian' credibility=0.82
ft.fact.add fact_type=event content='UK confirmed 2035 ban' source_id=$src.source_id
"
{
  "results": [
    {
      "method": "ft.src.add",
      "result": {"status": "created", "source_id": "a3f9...cc01"},
      "error": null,
      "assigns_to": "src"
    },
    {
      "method": "ft.fact.add",
      "result": {"status": "created", "fact_id": "b72c...d304"},
      "error": null,
      "assigns_to": null
    }
  ]
}
```

Each step shows its result. If one step fails, its `"error"` field contains the message and execution continues with the next step. All results are returned together.

**Recommended workflow:**

```
1.  csl.check   — fix any validation errors
2.  csl.dry     — review the operation list
3.  csl.explain — read the plain-English summary if any step is unclear
4.  csl.run     — execute
```

### 6.6 Saving and Reusing Scripts

Once a script works correctly you can save it to the graph and run it again by name — without keeping a separate text file.

#### Saving a script

```
akasha/user $ csl.save name="my_fact_template" script="
$src = ft.src.add kind=report title='Internal report' credibility=0.80
ft.add fact_type=event content='Placeholder event' source_id=$src.source_id
"
{
  "status": "saved",
  "name":   "my_fact_template",
  "alias":  "csl:my_fact_template",
  "key":    "a3f7...c19e"
}
```

The script is validated before saving — syntax errors are caught immediately.

#### Listing saved scripts

```
akasha/user $ csl.ls
{
  "scripts": [
    {
      "name":    "my_fact_template",
      "key":     "a3f7...c19e",
      "preview": "$src = ft.src.add kind=report title='Intern"
    }
  ],
  "count": 1
}
```

#### Loading (reading back) a script

```
akasha/user $ csl.load name="my_fact_template"
{
  "name":   "my_fact_template",
  "script": "$src = ft.src.add kind=report ...",
  "key":    "a3f7...c19e"
}
```

#### Running a saved script by name

From the Akasha shell, use `csl.exec`:

```
akasha/user $ csl.exec my_fact_template
{
  "results": [ ... ]
}
```

Or pass `name=` to `csl.run` directly from CSL:

```
csl> csl.run name="my_fact_template"
```

#### Running a local .csl file

If you have a CSL script saved as a plain text file (e.g. `setup.csl`), run it directly from the shell without first importing it:

```
akasha/user $ csl setup.csl
{
  "results": [ ... ]
}
```

The file is read, validated, and executed in one step. To save the results of a file run for later re-use, load the file content and call `csl.save`:

```
akasha/user $ csl.save name="setup" script="$(cat setup.csl)"
```

#### Deleting a saved script

```
akasha/user $ csl.rm name="my_fact_template"
{
  "status": "removed",
  "name":   "my_fact_template"
}
```

The script atom remains in the graph (the delete is non-destructive by default) but it is removed from the index of saved scripts and will no longer appear in `csl.ls`.

#### Summary table

| Command | What it does |
|---------|-------------|
| `csl.save name="…" script="…"` | Save (or overwrite) a script by name |
| `csl.ls` | List all saved scripts |
| `csl.load name="…"` | Retrieve script text by name |
| `csl.exec <name>` | Run a saved script by name (from shell) |
| `csl.run name="…"` | Run a saved script by name (from CSL) |
| `csl <filename.csl>` | Run a local .csl file directly from shell |
| `csl.rm name="…"` | Remove script from the saved index |

---

## 7. Value Types Reference

| Type | How to write it | Example |
|------|-----------------|---------|
| Text | `"..."` (double quotes) | `title="Le Monde"` |
| Long text (multi-line) | `"""..."""` (triple quotes) | `text="""line one\nline two"""` |
| Whole number | Just the number | `year=2023` |
| Decimal number | Number with `.` | `credibility=0.85` |
| Yes / No | `true` or `false` | `unresolved=true` |
| Empty / not set | `null` or `none` | `closed_at=null` |
| Saved result | `$name` | `source_id=$src` |
| Field from result | `$name.field` | `source_id=$src.source_id` |
| List | `[val, val, ...]` | `ids=[$a.key, $b.key]` |
| Keyword (bare word) | Plain word, no quotes | `kind=newspaper` |

**Keywords** — any plain word without spaces and without quotes is automatically treated as text. You do not need to quote simple words:

```
kind=newspaper          # → "newspaper"
perspective=de_facto    # → "de_facto"
assessment_type=risk    # → "risk"
priority=high           # → "high"
```

Only quote values that contain spaces or special characters.

**Multi-line text:**

```
csl> cur.conclude:
...     view_id   = $v.view_id
...     statement = """
...         Under international law as of 1939, France retained de jure
...         sovereignty over Alsace-Lorraine. German administration was
...         de facto but was not recognised by the Allied powers.
...     """
...     confidence = 0.92
...
```

---

## 8. Validation and Error Messages

### What gets checked

Every CSL command is checked before execution:

| Check | Severity | Effect |
|-------|----------|--------|
| Unknown command name | Error | Blocks execution |
| Using a `$name` before it has been assigned | Error | Blocks execution |
| `credibility`, `confidence`, `weight`, `feasibility`, or `expected_value` outside 0–1 | Warning | Reported; does not block |

### Reading error messages

**Unknown command:**

```
ERROR line 2: Unknown method 'ft.source.add'
Suggestion: Did you mean: ft.src.add, ft.src.ls?
```

The suggestion uses fuzzy matching — if your command is close to a known one, the correct name will be suggested.

**Undefined variable:**

```
ERROR line 3: Variable '$src' used before assignment
Suggestion: Assign a value to $src before using it
```

The `$src = ...` line must come before any use of `$src`.

**Value out of range (warning):**

```
WARNING line 5: Parameter 'confidence' value 1.5 is outside expected range [0, 1]
Suggestion: Use a value between 0.0 and 1.0
```

This almost always means you wrote `95` when you meant `0.95`. Warnings do not block execution.

---

## 9. Common Mistakes

### Spaces inside text — use double quotes

```
csl> ft.src.add kind=newspaper title=Le Monde   ← wrong: "Le" and "Monde" are two separate tokens
csl> ft.src.add kind=newspaper title="Le Monde" ← correct
```

Any value with a space must be in double quotes. Single words without spaces do not need quotes.

### Using a `$name` before assigning it

```
csl> ft.fact.add source_id=$src.source_id ...   ← wrong: $src is not assigned yet
csl> $src = ft.src.add kind=newspaper ...
```

The assignment must come first. Check the order of your commands.

### Confidence or credibility as a percentage instead of a fraction

```
csl> ft.src.add kind=newspaper title="Times" credibility=85  ← wrong
csl> ft.src.add kind=newspaper title="Times" credibility=0.85  ← correct
```

`credibility`, `confidence`, `weight`, `feasibility`, and `expected_value` all take values from **0 to 1**, not 0 to 100.

### Forgetting the blank line to close a block in the interpreter

```
csl> cur.conclude:
...     view_id    = $v.view_id
...     statement  = "France retained sovereignty."
...     confidence = 0.90
...                          ← press Enter on an empty line here
```

Without the blank line, the interpreter waits for more block content and does not execute.

### Using an incomplete command name

Some common mistakes:

| Wrong | Correct | Why |
|-------|---------|-----|
| `ft.source.add` | `ft.src.add` | Short alias is `src`, not `source` |
| `cur.view` | `cur.view` (with `label=` and `premise_id=`) | `cur.view` needs arguments |
| `intel.assess.add` | `intel.assess` | The short alias is `intel.assess` |
| `curation.view` | `curation.view.run` | Full method name requires `.run` |

When in doubt, use `csl.check` — the error message will suggest the correct command name.

### Writing a decimal number with a comma instead of a dot

```
csl> ft.src.add credibility=0,85  ← wrong (comma)
csl> ft.src.add credibility=0.85  ← correct (dot)
```

Decimal numbers always use a dot, regardless of your locale.

---

*For Akasha shell commands: [`docs/user-manual.md`](user-manual.md)*  
*For implementation details: [`docs/csl-spec.md`](csl-spec.md)*
