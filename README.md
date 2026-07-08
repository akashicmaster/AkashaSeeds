# Your notes shouldn't be dead files.

### AKASHA thinks while you dream.

Akasha is a local-first, concept-oriented operating system.

It was created from a simple observation:

Human beings rarely think in files.

We think in meaningful chunks.

A remembered sentence.

A quotation.

A place on a map.

A field observation.

A fragment of a story.

A scientific hypothesis.

An idea.

Most software systems are built around files and records.

Akasha is built around chunks.

No cloud.

No mandatory external dependencies.

Runs locally — even on an iPad in the middle of an archaeological dig site.

---

## 🌱 Files, Records, and Chunks

Most software organizes information around documents or records.

| System | Primary Unit |
| :--- | :--- |
| Word Processor | Document |
| Spreadsheet | Row / Cell |
| Database | Record |
| Wiki | Page |
| Note Apps | Note |
| **Akasha** | **Chunk** |

Traditional systems ask:

*How should this information be stored?*

Akasha asks:

*What is the meaningful thing here?*

That meaningful thing becomes an Atom.

---

## 🎯 What Is an Atom?

An atom is not necessarily a word.

An atom is a chunk of meaning.

More precisely:

An atom is a place where attention can land.

An atom might be:

- a sentence
- a quotation
- a paragraph
- a coordinate
- a field observation
- a legal principle
- a poem fragment
- a historical event
- a scientific claim

Anything that can be held in attention as a meaningful unit.

Humans think in chunks.

Akasha stores chunks as atoms.

---

## 📇 Think of It as a Card

If you are familiar with Zettelkasten, index cards, or Kyoto University Cards — an atom can be thought of as a digital knowledge card.

A document may contain hundreds of ideas.

Akasha allows those ideas to be separated into individual chunks, connected to other chunks, and explored independently.

But Akasha goes one step further.

The goal is not the cards themselves.

The goal is the semantic space that emerges between them.

| System | Primary Focus |
| :--- | :--- |
| Obsidian | Linking documents |
| Zettelkasten | Linking cards |
| **Akasha** | **Exploring semantic space** |

Obsidian links notes.

Zettelkasten links cards.

Akasha explores the semantic landscape that emerges between them.

---

## 🌊 A Sea of Meaning

Imagine three different sources.

A note you wrote yesterday.

A Wikipedia article.

A paragraph from a book.

Each contains a fragment related to the same idea.

Traditional systems keep those fragments inside their original documents.

Akasha extracts them as chunks.

Those chunks can then be linked together.

A quotation may support an observation.

A place may connect to an event.

An event may influence a concept.

As these relationships accumulate, a semantic landscape begins to emerge.

This landscape is what Akasha calls a Concept Space.

---

## 🌌 Concepts Are Not Stored

This is one of the most important ideas in Akasha.

Concepts are not stored separately from chunks.

Concepts emerge from relationships between chunks.

A concept is not a file.

A concept is not a database record.

A concept is not a page.

A concept is a stable pattern that appears inside the graph.

Meaning comes first.

Concepts emerge later.

---

## 🤿 Knowledge Should Be Navigable

Akasha is easiest to understand by using it.

```
w "My first kiss tasted sweet and sour."
al $it "first kiss"

dive Rome
```

You are no longer opening a document.

You are entering a semantic landscape.

A chunk becomes an anchor.

From there you can explore, connect, interpret, and extend.

Knowledge becomes navigable.

---

## 🧠 A Built-In Semantic Foundation

Akasha comes with a built-in ontology — a pre-built vocabulary covering common words, geographic places, historical periods, emotional dimensions, and conceptual categories.

When you write `w "My first kiss tasted sweet and sour."`, Akasha does not need you to explain what *sweet* and *sour* mean. It already knows. Your phrase immediately finds neighbours:

```
Content: My first kiss tasted sweet and sour.
Nearby: bittersweet memories [emo:evokes]
        sweet [sense:taste]
        sour  [sense:taste]
```

A note-taking tool with fifty notes has fifty isolated fragments. Akasha with its built-in ontology already has tens of thousands of connected concepts — a rich substrate into which your own observations find their place the moment you write them.

This is the difference between a knowledge system and a filing system.

---

## 📄 Documents Are Sources, Not Containers

Many knowledge systems treat documents as the primary unit of knowledge.

Akasha does not.

Documents are treated as sources rather than containers.

A note. A PDF. A book. A web page. A Wikipedia article.

All can be linked into Akasha.

Meaningful chunks can be extracted, named, connected, and reused.

A sentence from one source may connect to:

- a quotation from another source
- a coordinate on a map
- a historical event
- a scientific observation
- a legal principle

The resulting graph is not a graph of documents.

It is a graph of meaning.

---

## 🧩 A Living Concept Model Ecosystem

Akasha provides reusable semantic lenses called Concept Models.

Each model is a collection of named operators that can be applied to any atom or atom set.
The same atom can be viewed simultaneously through multiple models — as an ontology node,
a data record, and a point on a scatter plot — without any duplication of data.

All Concept Models are auto-discovered through a plugin registry. Adding a new model requires no kernel modifications.

**Data / Analysis**

| Model | Prefix | Purpose |
| :--- | :--- | :--- |
| **Record** | `rec.*` | Schema-free structured records — atoms with typed attribute links, aggregation, histograms, heatmaps |
| **Table** | `table.*` | Formal tabular data — named columns, typed rows, CSV import/export |
| **Lens** | `lens.*` | Source scanner — profiles any atom set or table, casts to any concept model view |
| **Quadrant** | `quadrant.*` | 4-quadrant scatter — visual positioning on a 2-axis plane, rendered as an ASCII grid |

**Research / Field**

| Model | Prefix | Purpose |
| :--- | :--- | :--- |
| **Note** | `note.*` | Hierarchical structured notes with granular span annotations |
| **FieldNote** | `fieldnote.*` | Field observation journals for qualitative data capture |
| **Survey** | `survey.*` | Structured questionnaires with typed responses and respondents |
| **Aggregation** | `agg.*` | Statistical summaries, group comparisons, and correlations |
| **Synthesis** | `synth.*` | Qualitative coding, theme development, and interpretive claims |
| **Fact** | `fact.*` | Discrete factual claims with sourcing and confidence tracking |

**Narrative / World**

| Model | Prefix | Purpose |
| :--- | :--- | :--- |
| **Cast** | `cast.*` | Persona and character modeling — identity, traits, wounds, bonds, masks |
| **World** | `world.*` | Topology of fictional or conceptual worlds — places, laws, events, history |
| **Map** | `map.*` | Cartographic depiction — editions, features, labels, geometry, projection |

**Semantic / Ontology**

| Model | Prefix | Purpose |
| :--- | :--- | :--- |
| **Thesaurus** | `thesaurus.*` | Ontology navigation and semantic link management |
| **Curation** | `curation.*` | Curated collections with editorial workflow |

Multiple Concept Models can coexist inside the same semantic session.

One graph. One memory substrate. Many perspectives.

→ Full ontology reference: [`docs/ontology/`](docs/ontology/)

---

## 📊 Structured Analysis from the CLI

You do not need to write code to perform real analytical work in Akasha.

The built-in ontology already contains sensory and flavor attributes for fruits — sweetness, acidity, color — loaded in the background during startup. You can project any set directly into a structured view using `lens`:

```
# Scan the built-in fruits set — attributes are already in the ontology
akasha/user $ lens src=set:fruits
```

```
Scanned 24 atoms from set:fruits
  — sweetness (numeric, 21/24 atoms)
  — acidity   (numeric, 19/24 atoms)
  — color     (text, 24/24 atoms)

Candidate models:
  [0] rec      — schema-free record table   (coverage: 88%)
  [1] quadrant — 4-quadrant scatter plot    (sweetness × acidity, coverage: 79%)
```

No data entry required. `lens` discovers the attributes already present on each atom.

Project the scan into a record set with one command:

```
akasha/user $ lens.flatten into=fruit_view
```

Display as a formatted table:

```
akasha/user $ rec.table in_set=set:fruit_view
```

```
┌─────────────┬───────────┬──────────┬────────┐
│ content     │ sweetness │ acidity  │ color  │
├─────────────┼───────────┼──────────┼────────┤
│ Fig         │ 0.88      │ 0.18     │ purple │
│ Grape       │ 0.82      │ 0.35     │ green  │
│ Date        │ 0.95      │ 0.05     │ brown  │
│ Pomegranate │ 0.65      │ 0.55     │ red    │
│ Olive       │ 0.10      │ 0.22     │ green  │
│ Lemon       │ 0.08      │ 0.95     │ yellow │
│ Orange      │ 0.72      │ 0.52     │ orange │
└─────────────┴───────────┴──────────┴────────┘
```

Now project the same atoms onto a 4-quadrant map — no browser required:

```
akasha/user $ quadrant.plot in_set=set:fruit_view \
    x=acidity y=sweetness \
    q1="tangy sweet" q2="mellow sweet" \
    q3="bland"       q4="sharp"
```

```
 sweetness
    1 │ Date                      │ Fig  Grape
      │                           │
  0.5 │ Pomegranate               │ Orange
      │                           │
    0 │ Olive ────────────────────┼──────────── acidity
      │                           │ Lemon
      └───────────────────────────┘
          bland          tangy sweet / sharp
```

The same two-command pattern — `lens` then `lens.flatten` — works on any set: your own notes, a search result, an imported CSV, an ontology subtree.

You can also annotate atoms that already exist in the graph without touching their structure:

```
# Add record attributes to existing ontology atoms
rec.set key=concept:aristotle  attr=influence_score val=0.95
rec.set key=concept:heraclitus attr=influence_score val=0.88
rec.idx key=concept:aristotle  sets=rec:philosophers
rec.idx key=concept:heraclitus sets=rec:philosophers

rec.table in_set=set:rec:philosophers
```

The original ontology atoms are untouched. Only `rec:` attribute links were added.

The `tree` command renders any atom, set, or namespace as a navigable graph tree:

```
tree fruit:fig depth=3
tree set:rec:fruit depth=2 format=ascii
tree ns:concept depth=2 follow=sys:is_a
```

All outputs — tables, trees, scatter plots, histograms, heatmaps — flow through a single display protocol so they render consistently across the terminal, web portal, and API.

---

## 🌐 The Web Portal and Cosmos

For those who want a richer graphical interface, Akasha provides a web portal that serves any device with a browser on the same network.

In the seeds distribution, the web server starts automatically alongside the shell. Check its status with:

```
akasha/user $ svc ls

  Services
  ─────────────────────────────────────────
  http_portal   running   http://127.0.0.1:8000
```

Then open in any browser:

```
http://localhost:8000/
```

Once the portal page appears, click **Cosmos**.

Cosmos is a 3D graph explorer. It takes the same `dive` function you use from the CLI — expanding the neighbourhood of an Atom, following links outward — and expresses it as a spaceship cockpit: concepts float as nodes in three-dimensional space, links become visible connections, and navigating the semantic landscape becomes a spatial experience.

The portal is a single-page application built with HTML and JavaScript. If you have those skills, you can build your own interface on the same JSON-RPC API. The [Blue Cookbook](docs/cookbook/blue/) walks through building one from scratch.

---

## ⚖️ Operand · Operator · Agent

Every action in Akasha is governed by a single organizing principle.

**Operand** — data. Carries no behaviour. An Atom is content-addressed text. It has no methods.

**Operator** — operation. Defined independently of the data it transforms. A `rec.table` operator reads attribute links from any atom set and renders a table. It does not care how the atoms were created.

**Agent** — subject. Applies operators to operands. An Agent may be a human typing in a terminal, an LLM, a sensor, or an automated script. The operator does not know or care which.

This separation is deliberately different from object-oriented design, where behaviour is embedded inside data objects. When behaviour needs to change in OO, the object changes — or requires inheritance, wrapping, or design patterns to work around the coupling.

Akasha does not do this.

Adding a new operator is a new class file. Atoms remain immutable. Agents can apply any operator they are authorized for. The inheritance maze never forms.

This is the methodology that governs every layer of Akasha — from the graph primitives up through Concept Models, session access control, and LLM integration.

---

## 🧠 Concepts First. Code Second.

Akasha is built around a simple principle:

> Define what things mean first.  
> The code comes later.

Traditional software development begins with implementation details:

- tables
- schemas
- APIs
- state containers
- infrastructure

Akasha begins with Concept Models.

A Concept Model describes how a domain behaves:

- a research project
- a historical archive
- a field journal
- a fictional world
- a survey universe
- an organization
- an ecosystem
- a manufacturing process

Once the conceptual topology becomes clear, operators emerge naturally.

This approach is called **Concepts-Oriented Design (COD)**.

| Traditional Approach | Akasha Approach |
| :--- | :--- |
| Design tables first | Design concepts first |
| Write APIs manually | Derive operators from topology |
| State scattered through code | State lives in the graph |
| ORM migration cycles | Evolving semantic structures |
| Implementation drives meaning | Meaning drives implementation |
| Human adapts to software | Software adapts to human thought |

The result is surprisingly practical.

Researchers, writers, analysts, engineers, and domain experts remain the primary designers.

LLMs assist implementation rather than replacing expertise.

---

## 📐 Turning Concepts Into Code

Akasha was designed around a fundamental belief:

> Your knowledge, concepts, and experience matter more than the software.  
> You are the architect.  
> The LLM is not.

The role of the LLM is to help materialize conceptual structures into executable operators, semantic workflows, visualizations, and applications.

The workflow becomes:

1. Define concepts
2. Define relationships
3. Define conceptual topology
4. Define operator semantics
5. Let the LLM help synthesize implementation

In other words:

> The LLM should generate code from concepts —  
> not generate concepts from code.

This single inversion changes the relationship between experts and software.

→ **[Turning Concepts Into Code](TURNING_CONCEPTS_INTO_CODE.md)** — a practical guide to designing knowledge systems with Akasha and an LLM.

---

## 🤝 Beyond "Vibe Coding"

Modern AI-assisted development often produces software that appears intelligent but collapses under real-world complexity.

The problem is rarely code quality.

The problem is conceptual instability.

Akasha attempts to solve this by introducing structure before implementation.

Concepts become explicit.

Relationships become explicit.

Assumptions become explicit.

Only then does code appear.

This allows human expertise and machine generation to collaborate without losing coherence.

---

## 🌐 Semantic Memory for Humans and Machines

Akasha can be used as a personal knowledge system.

It can also become a shared semantic substrate for teams, organizations, software agents, and physical systems.

The same conceptual graph can connect:

- humans
- LLMs
- documents
- databases
- sensors
- robots
- external services

through a common conceptual layer.

This is important because reality is not made of APIs.

Reality is made of things, events, constraints, goals, and consequences.

A concept layer provides a stable interface between reasoning and action.

---

## 🚗 Concepts Before Actions

A long-term goal of Akasha is to make concepts directly actionable.

A concept may eventually connect to:

- observations
- sensors
- simulations
- workflows
- actuators

through Concept Models.

This creates an important separation of concerns.

An LLM can imagine.

A Concept Model can evaluate.

Physical systems can enforce constraints.

This mirrors how humans operate.

We imagine freely.

Reality provides feedback.

Strategy emerges from the interaction between the two.

Akasha is designed to support that loop.

---

## ⚙️ The Engineering Foundation

Under the philosophical language lies a very practical system.

Akasha currently includes:

- content-addressed atoms
- typed semantic links (`sys:`, `emo:`, `sense:`, `log:`, `calc:`, `rec:`, and free-form)
- associative memory and set-based indexing
- BFS link-traversal with `tree` — renders any atom, set, or namespace as a navigable tree
- schema-free record model (`rec.*`) — atomic data with aggregation, histogram, heatmap
- formal table model (`table.*`) — columns, rows, CSV import/export
- lens scanner (`lens.*`) — profiles any source, projects to any concept model
- 4-quadrant scatter plot (`quadrant.*`) — ASCII grid, no browser required
- TextViewConcept display protocol — consistent rendering across all output types
- session-scoped semantic state and IAM scopes
- WriteQueue — all writes serialised, lock-free, crash-stop safe
- local SQLite persistence with WAL journal mode
- plugin auto-discovery — new concept models require no kernel changes
- JSON-RPC 2.0 API (`/rpc`)
- local-first deployment — runs on a laptop, a Raspberry Pi, or an iPad
- graceful contraction — runs without TFLite or SpaCy if unavailable; capabilities scale to hardware
- LLM integration through MCP (in progress)

No ORM.

No schema migrations.

No heavyweight infrastructure.

State lives in the graph, not in code.

→ Architecture deep-dive: [`docs/concept-model/concept-model-spec.md`](docs/concept-model/concept-model-spec.md)

---

## 🌿 Small Core, Large Worlds

Akasha was originally developed under severe practical constraints.

Trains.

Cafés.

Family restaurants.

An iPad mini.

Intermittent connectivity.

Limited hardware.

No infrastructure budget.

These limitations became design principles.

The result is a system that can scale conceptually while remaining operationally lightweight.

The architecture was never cloud-first.

It was survival-first.

That turned out to matter.

---

## 🫘 Cryptobiosis: The Resurrection of the Seed

Akasha can exist as a dormant single-file seed.

When executed, the seed reconstructs a complete semantic environment — kernel, browser applications, built-in ontology, and startup loader — all from a single Python script.

```bash
# Download akasha_seeds_seeds.zip from the latest release Assets:
# https://github.com/akashicmaster/AkashaSeeds/releases
# Unzip it, place akasha_seeds_seeds.py in an empty folder, then:
python3 akasha_seeds_seeds.py   # unpacks and launches immediately
```

On the first launch, Akasha automatically installs two optional runtime libraries:

| Library | Purpose |
| :--- | :--- |
| **TFLite** | Neural engine — semantic vector similarity, advanced associative inference |
| **SpaCy** | NLP engine — word decomposition, morphological analysis, language detection |

If either is unavailable, Akasha continues without it. **Graceful contraction**: the system calibrates to what the hardware can support, then expands as more becomes available. It will never refuse to start because an optional library is missing.

Knowledge systems should not require enterprise infrastructure.

Researchers, writers, students, and independent thinkers deserve tools that can survive anywhere.

---

## 🔭 Example Use Cases

- Digital Humanities
- Archaeology
- Ecology
- Qualitative Research
- Fiction Writing
- Organizational Memory
- Conceptual Design
- Ontology Engineering
- Human–LLM Collaboration
- Air-Gapped Knowledge Systems
- Experimental Cognitive Systems

---

## 💡 The Central Idea

Akasha is built on a very simple belief:

> Human beings already know how to think.  
> Software should help structure thought, not replace it.

The expert remains the source of meaning.

The graph preserves it.

The Concept Models organize it.

The LLM helps materialize it.

Akasha is, in the most precise sense, a **concept-oriented operating system** — an external cognitive substrate for handling concepts and Concept Models with the same freedom and fluency that an operating system gives you over files and processes.

---

## Final Thought

Akasha is not trying to become another productivity application.

Nor is it trying to become another AI platform.

It is an experiment in treating concepts as computational objects.

A place where:

- concepts come before code
- meaning comes before infrastructure
- knowledge remains alive
- human expertise remains central
- AI becomes a collaborator rather than a replacement

If successful, Akasha may help create systems that feel less like databases and more like living cognitive environments.

One concept.

One atom.

One connection at a time.

---

## 📚 Documentation

### Cookbook

The Cookbook is the practical complement to the Quick Start. It is organized into three tracks by audience — not by skill level, but by focus. All three tracks cover the same themes chapter by chapter.

| Track | Audience | Focus |
| :--- | :--- | :--- |
| [**Red**](docs/cookbook/red/) | Non-programmers | Everything achievable with CLI commands alone — no coding required |
| [**Blue**](docs/cookbook/blue/) | Programmers | Building web interfaces and extending Akasha in Python |
| [**Green**](docs/cookbook/green/) | Ontology builders | Creating `.ak` batch files, managing namespaces, LLM-assisted ontology enrichment |

| Chapter | Theme |
| :--- | :--- |
| 0 — Basic Operations | Atoms, links, sets, aliases, navigation |
| 1 — Concept Models | Structured data, records, tables, scatter plots, lens scanning |
| 2 — Maps and Time | Geographical and temporal dimensions *(forthcoming)* |

Start with Red 0 regardless of track. Blue and Green chapters reference their Red counterpart for CLI context before extending it.

### Reference

| Document | Audience | Contents |
| :--- | :--- | :--- |
| [**Quick Start**](quick-start.md) | New users | Installation, first session, core commands |
| [**Quick Reference**](quick-reference.md) | All CLI users | Complete command quick reference |
| [**Turning Concepts Into Code**](TURNING_CONCEPTS_INTO_CODE.md) | Everyone | Designing semantic systems with Akasha and an LLM |
| [**Roadmap**](roadmap.md) | Contributors | Vision, near-term goals, multi-agent future, long-term possibilities |
| [`docs/users/user-manual.md`](docs/users/user-manual.md) | General users | CLI workflows and Session Instance Layer |
| [`docs/users/csl-manual.md`](docs/users/csl-manual.md) | CSL users | Full CSL command reference |
| [`docs/users/admin-manual.md`](docs/users/admin-manual.md) | Administrators | User management, scopes, server setup |
| [`docs/ontology/ontology-spec.md`](docs/ontology/ontology-spec.md) | Ontology designers | Built-in ontology and Concept Model extensions |
| [`docs/concept-model/concept-model-spec.md`](docs/concept-model/concept-model-spec.md) | Plugin developers | BaseConcept API and implementation guide |
| [`docs/developer/api-spec.md`](docs/developer/api-spec.md) | App developers | Full RPC API reference |
| [`docs/for-llm/akasha-spec-compact.md`](docs/for-llm/akasha-spec-compact.md) | LLMs | Compact single-file Akasha reference for LLM context |

---

## 🚀 Ready to Begin?

**[→ quick-start.md](quick-start.md)**

From installation to a working concept graph in minutes.

**© 2026 Akasha Protocol Project**
