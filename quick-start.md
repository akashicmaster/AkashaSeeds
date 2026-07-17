# Akasha — Quick Start

**Estimated time: 20–30 minutes**

> **Which quick-start guide is this?**
> This is the **shell workflow guide** — it uses the `akasha/user $` prompt and shell commands (`w`, `ln`, `dive`, `tree`, `set.*`).
> For the **CSL interpreter** workflow (`csl> write text="…"` style), see `docs/users/csl-manual.md`.

> **This guide is self-contained.**
> You do not need to have read any other documentation to follow it.
> All necessary concepts are explained here, inline.
> A reference list is provided at the end for further reading.

---

## What Is Akasha?

Akasha is a local-first semantic memory system.

It stores knowledge as a graph — a web of connected pieces of text called **Atoms** — and lets you explore the relationships between them through a shell, browser applications, or APIs.

Everything runs on your machine.

No cloud account. No subscription. No network required after download.

---

### Human Memory, in Software

Human beings do not think in files or spreadsheets.

We think in chunks.

A phrase that stays with you. A place name. A quotation you heard once and never forgot. A field observation. A historical connection. A half-formed idea.

These chunks — some long, some short — are the meaningful units of thought. Akasha stores them exactly this way, as **Atoms**.

An Atom may be a single word, a sentence, a paragraph, or anything in between. What matters is that it is *one thing you can hold in your attention at once*. Akasha calls this a chunk of meaning.

Atoms acquire meaning not from their content alone, but from the relationships they form with other Atoms. A web of Atoms, connected by typed links and grouped into sets, produces something larger: a **semantic landscape** — a navigable structure of meaning.

That structure is what Akasha calls a **Concept Space**.

---

## Getting Akasha

Akasha is distributed as a single Python script called a **Seeds file**.

### What Is a Seeds File?

A Seeds file contains the complete Akasha system in a single self-extracting script:

- the knowledge kernel
- the browser applications
- the built-in ontology (Akasha's shared vocabulary)
- the startup loader
- all default assets

Nothing else is needed. No `pip install`. No dependency management. No build step.

**Why a single file?**

Akasha was designed to survive anywhere — a train, a café, an archaeological dig site, an air-gapped research server. The seeds file is Akasha in its most portable form: a dormant seed that carries everything needed to germinate into a full system.

This is why the distribution format is named *seeds*. A seed holds the complete genetic information of a plant in a compact, dormant state. Akasha's seeds file works the same way: the entire system is encoded inside, waiting to be activated.

### Download

```
https://github.com/akashicmaster/AkashaSeeds/releases
```

You will see filenames like:

| File | Contents | For |
|---|---|---|
| `akasha_seeds_seeds.py` | Kernel + browser apps | General use, independent researchers |
| `akasha_seeds_thesaurus.py` | + extended vocabulary library | Libraries, research organizations |
| `akasha_seeds_server.py` | + multi-client configuration | Programmers, institutional deployments |

Python 3.10 or later is required.

```bash
python3 --version
```

### Launch

```bash
python3 akasha_seeds_seeds10.py
```

The script unpacks Akasha into the current directory and starts immediately.

---

## First Launch: What Happens and Why It Takes a Few Minutes

The first launch is different from every subsequent launch. Three things happen in sequence, and each is worth understanding.

---

### Step 1 — Library Installation (first launch only, ~2–5 minutes)

Before the shell opens, Akasha checks for two optional runtime libraries and installs them automatically if they are not already present:

| Library | Purpose | Installed via |
|---|---|---|
| **TFLite / TensorFlow** | Neural engine — enables semantic vector similarity and advanced associative inference | `pip install tflite-runtime` (lightweight) or `tensorflow-cpu` as fallback |
| **SpaCy** | NLP engine — word decomposition, morphological analysis, language detection | `pip install spacy` |

You will see output like:

```
[+] Akasha online.
[ML]  Installing Neural Engine (TFLite)... done.
[NLP] Installing Natural Language Processing (SpaCy)... done.
```

This only runs once. On every subsequent launch, the libraries are already present and the step is skipped entirely.

**What if installation fails?**

Neither library is required for Akasha to run. If installation fails — due to network restrictions, hardware incompatibility, or platform limitations — Akasha continues without them, with reduced capabilities:

| Available | Capability |
|---|---|
| TFLite + SpaCy | Full semantic inference: cosine similarity, vector-based associative search, word decomposition |
| SpaCy only | Word decomposition and morphological analysis; no neural vector similarity |
| Neither | Text-level search and graph traversal only; all core commands still work |

This is **graceful contraction**: the system calibrates itself to what the hardware and environment can support, then expands as more becomes available. It will never refuse to start because an optional library is missing.

The same principle governs the seeds format: a single dormant file that contains everything needed, activating each capability as conditions allow. Compact when conditions are harsh. Full when conditions allow.

---

### Step 2 — The Genesis Rite (first launch only)

Once libraries are ready, Akasha asks you to create the administrator account.

```
[ Genesis Rite ]
  No consciousness has been established.
  You are the first. Speak your true name.
  Akasha Name (this installation): MyAkasha
  Your name (admin client ID):     admin
  Passphrase:                      ••••••••
  Confirm passphrase:              ••••••••
```

| Field | Meaning |
|---|---|
| **Akasha Name** | The name of this installation — appears in the shell prompt |
| **Your name** | Your administrator user ID |
| **Passphrase** | Login password (stored locally, never transmitted) |

After completion, the shell opens:

```
[ MyAkasha online. Welcome, admin. ]
akasha/user $
```

This only happens once. From the second launch onward, Akasha boots directly to the shell.

---

### Step 3 — Ontology Loading (background, progressive)

The shell is now open and Akasha is fully usable. But something continues in the background: the built-in **ontology** is being loaded.

The ontology is Akasha's shared vocabulary — a pre-built knowledge structure covering common words, geographic places, historical periods, emotional dimensions, and conceptual categories. This is what allows Akasha to associate your observations with existing knowledge without you having to define everything from scratch.

Loading feeds through a low-priority background queue, so your own writes and reads always take precedence. You will see an occasional progress note:

```
akasha/user $ [loading ontology... 34%]
```

Associative richness grows as loading progresses. You do not need to wait — everything in this guide works at any stage. By the time you reach the concept model examples, loading will likely be complete.

---

## Your First Atom

Akasha is easiest to understand by using it.

At the shell prompt, write your first Atom with the `w` command:

```
akasha/user $ w "My first kiss tasted sweet and sour."
→ 3a9fc2...
```

Akasha returns a short hash — the **key** — that uniquely identifies this Atom. The key is computed from the content itself: write the same text again and you get the same key. This is called **content-addressing**.

For now, you do not need to work with the key directly. Akasha provides a more convenient way to refer to Atoms: **aliases**.

### Assigning an Alias

Give your Atom a human-readable name with the `al` command:

```
akasha/user $ al $it "first kiss"
```

`$it` is a shortcut that always refers to the Atom you most recently touched. You will use it constantly.

Now you can refer to your Atom by its name:

```
akasha/user $ r "first kiss"
```

Akasha recalls the phrase. But alongside the content, you will see something else:

```
Content: My first kiss tasted sweet and sour.
  ~sys:refers_to  →  @sweet   "Sweet taste; a pleasurable gustatory sensation."
  ~sys:refers_to  →  @sour    "Sour taste; the sharp or acidic flavour."
  ~sys:refers_to  →  @kiss    "The act of pressing one's lips against..."
```

Akasha's Weaver automatically detected *sweet*, *sour*, and *kiss* as vocabulary already present in the built-in ontology, and created semantic bridges to them — without you having to declare any schema or category in advance.

This is the first sign of the semantic landscape at work.

---

## A Shared Foundation: Built-in Knowledge

Your phrase is now part of Akasha's memory. But Akasha already had memory before you arrived.

Try reading something you have never written:

```
akasha/user $ r apple
```

You will see a definition from the built-in ontology and its connections:

```
Content: A round fruit with red or green skin. Used fresh, baked, or juiced.
  [calc:associated_with]  →  dna:taste:sweet   "Sweet taste; a pleasurable gustatory sensation."
  [calc:associated_with]  →  dna:color:red     "Red."
  [calc:associated_with]  →  dna:texture:crisp "Crisp texture; firm and brittle."
  [rec:sweetness]         →  0.85
  [rec:acidity]           →  0.25
  [rec:color]             →  red
```

Notice that *sweet* appears here too — the same vocabulary atom your phrase connected to moments ago. Your personal memory and the built-in ontology share the same semantic space.

This is how shared knowledge works in Akasha: the built-in ontology creates a common vocabulary, and your own atoms enter that space through the connections they naturally form with existing words and concepts.

---

## Walking the Semantic Landscape: `dive`

The `r` command recalls an Atom directly. The `dive` command does something more: it focuses on an Atom and shows you the full neighbourhood around it — nearby concepts, emotional associations, historical connections.

```
akasha/user $ dive Rome
```

You might see:

```
Focus: Rome  (geo:capital:rome)
  → Italy    [sys:capital_of]
```

From Rome you step to Italy. From Italy the graph opens wider — southern Europe, the G7, the European Union:

```
akasha/user $ dive Italy
akasha/user $ dive France
akasha/user $ dive Germany
```

Each dive brings a new neighbourhood into focus. The graph becomes a landscape you can walk.

**Aliases are case-insensitive.** `Apple`, `apple`, and `APPLE` all refer to the same Atom.

---

## Reading the Colon Notation

You have already seen expressions like `sys:part_of`, `history:rival_of`, and `set:ingred:fruit`. The colon (`:`）is Akasha's universal **namespace separator** — it appears in three distinct roles, and knowing which role you are looking at will prevent a great deal of confusion.

### Role 1 — Atom keys

Atom keys are the unique identifiers stored in the graph. They follow the pattern `namespace:local_name`:

```
fruit:fig          ← the fig atom, in the "fruit" namespace
concept:aristotle  ← the Aristotle concept atom
place:rome         ← the Rome place atom
word:sweet         ← a proto-word atom in the word namespace
```

The namespace groups related atoms together. You can browse a namespace with `onto.dump ns=fruit:` or traverse it with `tree ns:fruit depth=2`.

Most of the time you do not need to type the full key: if an atom has an alias (`fig`, `rome`, `aristotle`), you can use the alias everywhere instead. The two are interchangeable.

### Role 2 — Set names

Sets also use colon-separated paths, but they are a different kind of object — collections of atoms, not atoms themselves:

```
set:ingred:fruit           ← the "fruit ingredients" named collection
set:ingred:autumn          ← a seasonal sub-collection
set:rec:fruit              ← auto-created by rec.new type=fruit
leaf:en                    ← English vocabulary leaf set (built-in)
```

You can always tell a set from an atom key: sets appear in `s.ls`, `s.add`, `in_set=` arguments, and `lens src=`. An atom key appears as a target of `r`, `dive`, `ln`, `rec.set key=`, and similar commands.

### Role 3 — Relation labels (rel)

The third use of the colon is in **relation labels** — the typed connection between a source atom and a destination atom. These appear as the third argument of `ln`, in `[square brackets]` in `dive` output, and in the `follow=` parameter of `lens` and `tree`.

```
sys:is_a           ← structural: classification ("a fig is_a fruit")
sys:part_of        ← structural: composition ("Rome is part_of Italy")
sense:taste        ← sensory quality
sense:smell        ← sensory quality
emo:evokes         ← emotional association
calc:associated_with ← loose thematic link (computed / inferred)
history:rival_of   ← domain-specific, freely invented
rec:sweetness      ← record attribute link (added by rec.set)
```

The prefix before the colon indicates the **vocabulary domain** the relation belongs to. The built-in domains (`sys:`, `emo:`, `sense:`, `log:`, `calc:`) are defined in the ontology. You can also invent your own — any string with or without a colon works as a relation label.

### At a glance

| Where you see it | Example | It is |
|---|---|---|
| `r`, `dive`, `tree`, target of `ln` | `fruit:fig` | An atom key |
| `s.ls`, `s.add`, `in_set=`, `lens src=` | `set:ingred:fruit` | A set name |
| Third arg of `ln`, `[square brackets]`, `follow=` | `sys:is_a` | A relation label |

All three use the same colon syntax. The command context tells you which kind you are dealing with.

### A note on dot vs space notation

Most multi-part commands in Akasha can be written with either a dot or a space between the command and subcommand — `rec.new` and `rec new` are identical. This documentation uses dot notation throughout, as it is unambiguous and easier to scan.

One exception: the `svc` service manager uses space notation only (`svc ls`, `svc start`, `svc stop`). `svc.ls` will not work — write it with a space.

---

## Connecting Ideas: Links

The ontology contains many pre-built connections. But you can add your own.

Links are directed semantic relationships between Atoms. The command is `ln`:

```
ln <source> <destination> <relation>
```

Apple, for example, can be connected in many ways:

```
akasha/user $ ln apple "sweet and sour" sense:taste
akasha/user $ ln apple red              color:typical
akasha/user $ ln apple yellow           color:typical
akasha/user $ ln apple green            color:typical
```

You can also link to atoms you write on the spot:

```
akasha/user $ w "Apple Inc., founded in 1976 by Steve Jobs"
akasha/user $ al $it apple.inc
akasha/user $ ln apple apple.inc calc:associated_with
```

Now `dive apple` shows all three dimensions of *apple* at once: the fruit, its sensory profile, and the technology company.

### Common Relation Types

Akasha has a built-in vocabulary of relation types. A few of the most useful:

| Relation | Meaning |
|---|---|
| `sys:is_a` | Classification — "a rose is_a flower" |
| `sys:part_of` | Whole and part — "Rome is part_of Italy" |
| `sys:associated_with` | Loose thematic connection |
| `sys:causes` | Causal relation |
| `sense:taste`, `sense:smell`, `sense:texture` | Sensory qualities |
| `emo:evokes` | Emotional resonance |
| `@supports`, `@contradicts` | Argumentative relations |

You are also free to invent your own. `ln apple harvest season:autumn` works perfectly — Akasha does not require relation types to be pre-registered.

---

## Why Shared Knowledge Matters

You might ask: why does Akasha come with a built-in ontology at all? Why not start from a blank slate?

The answer is in how memory actually works.

Human memory functions because it is *enormous*. A child learns the word *apple* not by being told a definition, but by hearing it thousands of times in different contexts — near *red*, *round*, *sweet*, *tree*, *autumn*, *teacher*. Meaning emerges from the density of accumulated associations.

A note-taking tool with fifty notes has fifty isolated fragments. Akasha with its built-in ontology already has tens of thousands of connected concepts — a rich substrate into which your own observations, field notes, and ideas can immediately find their place.

When you wrote "My first kiss tasted sweet and sour," Akasha did not need you to explain what *sweet* and *sour* mean. It already knew. Your phrase immediately found neighbours.

This is the difference between a knowledge system and a filing system.

---

## Sets: Meaning Through Grouping

Alongside typed links, Akasha uses another organizing principle: **sets**.

A set is a named collection of Atoms. Unlike a tag, a set is an operational object: you can query its members, combine it with other sets, and project it into concept models for analysis.

Look at an existing set from the built-in ontology:

```
akasha/user $ s.ls set:ingred:fruit
```

You might see:

```
Members of set:ingred:fruit  (5)
  apple    ingred:fruit:apple
  banana   ingred:fruit:banana
  orange   ingred:fruit:orange
  lemon    ingred:fruit:lemon
  grape    ingred:fruit:grape
```

`ingred:fruit` as a path carries no meaning by itself. But this collection — this *set of things that are fruits* — makes the concept visible.

Meaning does not live in a word. It lives in the network of relationships and groupings that surround it.

Add a new member:

```
akasha/user $ s.add set:ingred:fruit "passion fruit"
akasha/user $ s.ls set:ingred:fruit
```

*Passion fruit* is now part of the concept. No schema change. No migration. The concept simply became richer.

---

## The Concept as Emergent Structure

We have now seen two organizing mechanisms:

- **Links** — typed relationships between Atoms (apple → sweet, Rome → Italy, emo:evokes → bittersweet)
- **Sets** — named groupings of Atoms (fruits, Mediterranean cities, philosophy quotes)

These two mechanisms, working together, produce something that neither produces alone: **concepts**.

A concept in Akasha is not stored. It is *not a record in a table*.

A concept is the stable pattern that emerges from the density of relationships and groupings around an Atom. *Fruits* is a concept because we know which atoms belong to the set, which sensory qualities they link to, which cultures cultivate them, which historical periods first traded them.

Remove the links and sets, and *fruits* reverts to a word. Restore them, and the concept re-emerges. The information was always in the relationships.

Human beings think this way. We understand *love* not from a dictionary entry, but from thousands of associated experiences, emotions, contrasts, and stories. Akasha is designed to mirror this.

---

## Exploring the Structure: `tree`

The `tree` command renders the link graph as a navigable visual tree — useful for seeing at a glance how an Atom is connected to its neighbourhood.

```
akasha/user $ tree set:ingred:fruit
```

```
set:ingred:fruit
├─ apple        [calc:associated_with]→ dna:taste:sweet, dna:color:red, dna:texture:crisp
├─ banana       [calc:associated_with]→ dna:taste:sweet, dna:color:yellow
├─ orange       [calc:associated_with]→ dna:color:orange
├─ lemon        [calc:associated_with]→ dna:taste:sour, dna:color:yellow
└─ grape
```

Try it with a place:

```
akasha/user $ tree Spain
```

Or with a concept:

```
akasha/user $ tree France depth=3
```

The `depth` parameter controls how many hops outward the tree expands (1–5). The default is 2.

You can also filter by relation type:

```
akasha/user $ tree set:ingred:fruit follow=sys:is_a
```

This shows only the classification hierarchy — stripping out sensory, emotional, and cultural links to reveal the taxonomic skeleton.

---

## Finding Related Atoms: Meaning-Layer Search

`dive` and `tree` walk the links you (or the ontology) have **explicitly drawn**. But Akasha
also builds a *meaning layer* underneath: every text Atom gets a semantic fingerprint, learned
from the words it contains and from how it sits in the graph. That lets you ask questions the
explicit links can't answer — *"what else is like this?"* — even when no link exists yet.

There are three kinds of "related", and Akasha gives you a separate command for each.

### `sim` — atoms that *mean* the same thing

`sim <atom>` finds Atoms whose **meaning** is closest to the one you name. It is anchored on the
Atom's own content — you are not typing a search phrase, you are saying *"find more like THIS."*

```
akasha/user $ sim Rome
```

You might get Athens, Carthage, and Constantinople — ancient capitals — even if you never linked
them. The anchor Atom itself is always excluded from its own results. Add `limit=` to widen or
narrow the list (`sim Rome limit=20`).

> **Free-text variant.** If you want to search by a phrase instead of an existing Atom, use
> `search query="ancient mediterranean city"`. Same ranking, different starting point.

### `node.sim` — atoms *connected* the same way

`node.sim <atom>` finds Atoms that occupy the **same structural position** in the graph —
"wired in the same way" — regardless of what they mean.

```
akasha/user $ node.sim Rome
```

`sim` and `node.sim` deliberately disagree. Two capitals can *mean* similar things (`sim`) while
being wired very differently (`node.sim`), and two unrelated Atoms can share a structural role.
Reach for `sim` when you care about topic, `node.sim` when you care about role.

### `view` — the meaning of one Atom, on its own

`view <atom>` (also spelled `cosmos <atom>`) shows the **consciousness view** of a single Atom:
its signposts (direct links), its resonance (semantically-near Atoms two hops out), and its
position and aura colour in the cosmos field — without diving or changing your current focus.

```
akasha/user $ view Rome
```

It is the read-only "tell me about this one" companion to `dive`'s "take me there".

### `emotion.find` — atoms that *feel* an emotion

Emotions are first-class Atoms in the ontology (`emo:awe`, `emo:fear`, `emo:joy`, …).
`emotion.find` runs the lookup in reverse — *which Atoms feel this?*

```
akasha/user $ emotion.find emo=awe
```

The mirror command, `emotion.profile <atom>`, gives you the emotional **vector** of a single
Atom — which emotions it leans toward, and how strongly.

### `dream` — sleeping on it

The commands above rank what is *already* near. `dream` does the opposite: it hunts the
**affinity gap** — Atoms that are **near in meaning but far in the explicit graph**. These are
the connections you tend to notice only after sleeping on a problem, so `dream` behaves that way
on purpose: it runs as a background job, and you check back for the result.

```
akasha/user $ dream Icarus
☾ dream [Icarus]  incubating…
  Come back with the same `dream id=` to see the staged bridges.
```

Do something else, then ask again:

```
akasha/user $ dream Icarus
✦ dream [Icarus]  status=ready  2 bridge(s)
     1. [lilienthal]  pioneer of flight        0.612
     2. [ambition]    the drive to exceed      0.481
```

Each candidate is a **staged, tentative** bridge — `dream` never draws a real link on its own.
**You** decide:

- Type the number (or `dream.confirm dst=lilienthal`) to promote a bridge into a real link.
- `dream.forget all=yes` to discard the rest.

This human-in-the-loop step is deliberate: the point of a dream is whether the proposed
connection **resonates with your own recall** — so the confirmation is yours to give, never
the machine's. (These same instruments power the Dream panel in the Cosmos web viewport.)

### Growing the graph: `gap.scan`

Once you have written a fair amount, one command tells you **where your knowledge is thin**:

```
akasha/user $ gap.scan
```

`gap.scan` surfaces *important-but-under-linked* Atoms — concepts that many things point at, but
which you have barely connected to anything themselves. That mismatch is a map of what to enrich
next. It is the first step of Akasha's **self-expanding loop**: scan for gaps → fill them (write
links, `fetch` from the web, or let an LLM propose them) → the graph gets richer → scan again.

> **Under the hood.** The semantic search above rests on a *learned model* that Akasha trains from
> your own graph — it improves as you write. That training runs automatically at startup; an admin
> can also refresh the structural half by hand with `node.learn`. You never *have* to run it, but
> it is why `sim` and `node.sim` get sharper the more you use Akasha.

---

## Concept Models: Organizing for a Purpose

Akasha's memory is free-form by design. You can write and link anything, in any order, without declaring schemas or tables in advance.

But sometimes you want to *organize* that free-form memory for a specific purpose — the way a researcher reaches for index cards, a librarian for a catalogue, an analyst for a spreadsheet.

In Akasha, these organizing tools are called **Concept Models**.

A Concept Model is a projection operator: it looks at a set of Atoms, extracts whatever attributes are relevant to its purpose, and presents the result as a structured view — a table, a chart, a histogram.

The same Atoms can be viewed through multiple Concept Models simultaneously, without duplicating any data.

### Scanning a Set with `lens`

The simplest way to project any set into a structured view is `lens`.

`lens` scans a source — a set, a table, an ontology subtree — profiles the attributes it finds, and proposes matching Concept Models. The attributes do not need to be declared in advance; `lens` discovers them from the links already present on each Atom.

The built-in ontology includes sensory and flavor attributes for fruits. Let us scan the `ingred:fruit` set and see what `lens` finds:

```
akasha/user $ lens src=set:ingred:fruit
```

```
◎ lens scan  set:ingred:fruit  5 node(s)  flat_set

  Attributes:
  ██████████  100%  rec:acidity              float   0.95
  ██████████  100%  rec:color                text    red
  ██████████  100%  rec:sweetness            float   0.85

  Candidates:
       1.  rec              ████████ 0.82
       2.  quadrant         ██████░░ 0.75  x=rec:acidity y=rec:sweetness
```

`lens` found sweetness, acidity, and color attributes already present in the ontology — loaded in the background during startup. No data entry required.

Now project the scan result into a record set with a single command:

```
akasha/user $ lens.flatten into=fruit_view
```

This creates a clean set of record atoms — one per fruit — carrying the discovered attributes. View the result as a formatted table:

```
akasha/user $ rec.table in_set=set:fruit_view
```

```
┌─────────┬───────────┬──────────┬────────┐
│ content │ sweetness │ acidity  │ color  │
├─────────┼───────────┼──────────┼────────┤
│ Apple   │ 0.85      │ 0.25     │ red    │
│ Banana  │ 0.90      │ 0.08     │ yellow │
│ Orange  │ 0.68      │ 0.52     │ orange │
│ Lemon   │ 0.05      │ 0.95     │ yellow │
│ Grape   │ 0.78      │ 0.38     │ green  │
└─────────┴───────────┴──────────┴────────┘
```

The original ontology atoms are untouched. `lens.flatten` created a new independent record set from what was already there.

This is Concept Model projection: any set of Atoms — from your own notes, from the shared ontology, from a search result — can be cast into a structured view with two commands.

### Visualizing: the 4-Quadrant Scatter Plot

Now project the same record set onto a visual map with the **Quadrant model**:

```
akasha/user $ quadrant.plot in_set=set:fruit_view \
    x=acidity y=sweetness \
    q1="tangy sweet" q2="mellow sweet" \
    q3="bland"       q4="sharp"
```

```
 sweetness
    1 │ Banana                    │ Apple  Grape
      │                           │
  0.5 │                           │ Orange
      │                           │
    0 │ ──────────────────────────┼──────────── acidity
      │                           │ Lemon
      └───────────────────────────┘
          mellow sweet       tangy sweet / sharp
```

Banana sits high in the *mellow sweet* quadrant; lemon sits alone in the *sharp* corner; apple and grape share the tangy-sweet region.

No schema was declared. No data was typed in. The same two-command pattern — `lens` then `lens.flatten` — works on any set in Akasha: your own notes, a search result, an imported CSV, an ontology subtree.

### The Web Portal and Cosmos

Akasha is designed to work anywhere — on a tablet, a smartphone, a rented server terminal, or a machine with no display at all. The vast majority of its capabilities are available through the CLI prompt you have been using throughout this guide.

For those who want a richer graphical interface, Akasha also provides a web portal. Any device with a browser on the same network can connect.

**In the seeds distribution, the web server starts automatically** alongside the shell. You do not need to do anything to launch it. To confirm it is running, use `svc ls` at the Akasha prompt:

```
akasha/user $ svc ls

  Services
  ─────────────────────────────────────────
  http_portal   running   http://127.0.0.1:8000
```

If the portal shows as stopped for any reason, start it with:

```
akasha/user $ svc start http_portal
```

Then open in any browser on the same machine:

```
http://localhost:8000/
```

Once the portal page appears, click **Cosmos**.

Cosmos is a 3D graph explorer. It takes the same `dive` function you used from the CLI — expanding the neighbourhood of an Atom, following links outward — and expresses it as a spaceship cockpit: concepts float as nodes in three-dimensional space, links become visible connections, and navigating the semantic landscape becomes a spatial experience.

The portal is a single-page application built with HTML and JavaScript. If you have those skills, you can build your own interface on the same JSON-RPC API — a single HTML file is all it takes to create a custom view of your Akasha data. The Blue Cookbook (Chapter 0) walks through building one from scratch.

### Other Concept Models

The Record and Quadrant models are two of many. Akasha includes:

| Domain | Models |
|---|---|
| Data / Analysis | `rec.*`, `table.*`, `lens.*`, `quadrant.*` |
| Research / Field | `note.*`, `fieldnote.*`, `survey.*`, `agg.*` |
| Narrative / World | `cast.*`, `world.*`, `map.*` |
| Semantic / Ontology | `thesaurus.*`, `curation.*` |

A specialist's field notebook, a librarian's catalogue card, an accountant's ledger — all can be expressed as Concept Models. New models can be added as plugins without modifying the kernel.

---

## Viewing the Current State

To see the overall state of your Akasha instance:

```
akasha/user $ cog
```

This shows loaded ontologies, atom counts, active scopes, and queue status.

To explore what namespaces are loaded:

```
akasha/user $ onto.dump namespaces
```

To see atoms in a specific namespace:

```
akasha/user $ onto.dump atoms ns=ingred:fruit:
```

As ontology loading progresses, these counts grow. Eventually the full shared vocabulary settles into place and the count stabilizes.

---

## What Akasha Is For

Akasha can be used as a personal knowledge graph, a research database, a collaborative semantic workspace, or a long-lived memory substrate for LLM-assisted workflows.

It can handle isolated notes. It can also handle the messy, overlapping, emotionally-resonant complexity of real human inquiry — because it was built around the same principles that govern human memory: links, groupings, and the emergence of meaning from density.

If you want to use it simply as a graph database, that works. But that is a means, not the destination.

Akasha was built as a research substrate for the study of **concepts themselves** — how they form, how they relate, how they evolve when new knowledge enters the graph. The built-in shared knowledge, the emotional and sensory links, the Concept Models — all of these serve that larger purpose.

Akasha is, in the most precise sense, a **concept-oriented operating system**: an external cognitive substrate for handling concepts and Concept Models with the same freedom and fluency that an operating system gives you over files and processes.

---

## Where to Go Next

### Cookbook

The Cookbook is the primary learning resource. It is self-contained: each chapter explains everything needed, inline, without sending you to other documents.

Three tracks are available, by focus rather than skill level:

| Track | Audience | Focus |
|---|---|---|
| [**Red**](docs/cookbook/red/) | Non-programmers | Everything achievable with CLI commands alone |
| [**Blue**](docs/cookbook/blue/) | Programmers | Building web interfaces and extending Akasha in Python |
| [**Green**](docs/cookbook/green/) | Ontology builders | `.ak` batch files, namespace design, LLM-assisted ontology enrichment |

Chapters are aligned by theme across all three tracks. Start with Red 0 regardless of your track — it covers the same CLI operations as this guide, more thoroughly.

| Chapter | Theme |
|---|---|
| 0 — Basic Operations | Atoms, links, sets, aliases, navigation |
| 1 — Concept Models | Records, tables, scatter plots, lens scanning |
| 2 — Maps and Time | Geographic and temporal dimensions *(forthcoming)* |

### Quick Reference

[`quick-reference.md`](quick-reference.md) — the complete command reference for the Akasha CLI: every command, every argument, in one place.

---

## Common Pitfalls

**`$it` points to the wrong atom**
Navigation commands (`r`, `dive`, `tree`, `explore`) also update `$it`. If you want to keep a reference across several commands, assign an alias immediately after writing.

**"Nothing found" on `r` or `dive`**
Ontology loading may still be in progress. Try again after a minute, or check `cog` for the load percentage.

**Aliases are case-insensitive, but sets are not**
`apple` and `Apple` refer to the same Atom. `set:Fruit` and `set:fruit` are different sets.

**Browser apps show "Connection refused"**
The web server may not be running. Check with `svc ls` at the Akasha prompt and start it if needed:

```
akasha/user $ svc ls
akasha/user $ svc start http_portal
```

Then open `http://localhost:8000/`.

---

## Reference

| Resource | Contents |
|---|---|
| [`quick-reference.md`](quick-reference.md) | Complete CLI command reference |
| [`docs/cookbook/red/`](docs/cookbook/red/) | Cookbook — CLI track (non-programmers) |
| [`docs/cookbook/blue/`](docs/cookbook/blue/) | Cookbook — web/Python track |
| [`docs/cookbook/green/`](docs/cookbook/green/) | Cookbook — ontology track |
| [`docs/concept-model/concept-model-spec.md`](docs/concept-model/concept-model-spec.md) | Concept Model API |
| [`docs/ontology/ontology-spec.md`](docs/ontology/ontology-spec.md) | Built-in ontology reference |
| [`docs/developer/api-spec.md`](docs/developer/api-spec.md) | JSON-RPC API reference |
| [`docs/for-llm/akasha-spec-compact.md`](docs/for-llm/akasha-spec-compact.md) | Compact reference for LLM context |

---

**© 2026 Akasha Protocol Project**
