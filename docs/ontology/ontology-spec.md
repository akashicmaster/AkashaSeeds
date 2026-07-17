# Akasha Ontology Specification

**Version 1.1**

---

## Table of Contents

0. [Epistemological Foundations](#0-epistemological-foundations)
1. [What Is Ontology in Akasha?](#1-what-is-ontology-in-akasha)
2. [Three-Layer Architecture](#2-three-layer-architecture)
3. [Layer 1 — DNA: The Innate Core](#3-layer-1--dna-the-innate-core)
   - [3.1 System & Topology Relations](#31-system--topology-relations)
   - [3.2 Fuzzy Formal Logic](#32-fuzzy-formal-logic)
   - [3.3 Spatiotemporal Axes](#33-spatiotemporal-axes)
   - [3.4 Emotion Dimensions](#34-emotion-dimensions)
   - [3.5 Epistemological Frames](#35-epistemological-frames)
4. [Layer 2 — Acquired Ontology: Startup Files](#4-layer-2--acquired-ontology-startup-files)
   - [4.1 Shell Script Files (.ak)](#41-shell-script-files-ak)
   - [4.2 CSL Script Files (.csl)](#42-csl-script-files-csl)
   - [4.3 Loading Behaviour](#43-loading-behaviour)
   - [4.4 Manual Reload](#44-manual-reload)
5. [Layer 3 — Runtime Ontology: Building via CLI and CSL](#5-layer-3--runtime-ontology-building-via-cli-and-csl)
   - [5.1 The Basic Pattern](#51-the-basic-pattern)
   - [5.2 Writing Structured Ontologies with CSL](#52-writing-structured-ontologies-with-csl)
   - [5.3 Saving Reusable Ontology Scripts](#53-saving-reusable-ontology-scripts)
6. [Concept Model Plugins](#6-concept-model-plugins)
   - [6.1 What Concept Models Do](#61-what-concept-models-do)
   - [6.2 Auto-Discovery](#62-auto-discovery)
   - [6.3 The Knowledge Work Suite](#63-the-knowledge-work-suite)
   - [6.4 The World-Building Suite (Harmonia)](#64-the-world-building-suite-harmonia)
7. [Current Ontology Contents](#7-current-ontology-contents)
   - [7.1 Directory Structure](#71-directory-structure)
   - [7.2 Common Layer](#72-common-layer)
   - [7.3 Seed Layer](#73-seed-layer)
8. [Writing Ontology Files](#8-writing-ontology-files)
   - [8.1 .ak File Format](#81-ak-file-format)
   - [8.2 .csl File Format](#82-csl-file-format)
   - [8.3 Naming Conventions](#83-naming-conventions)
9. [Further Reading](#9-further-reading)

---

## 0. Epistemological Foundations

> *"In the beginning was the Word."*

Akasha's knowledge model rests on one foundational epistemological claim:

**A word does not carry meaning. A word simply IS. Meaning is the product of relationships.**

### 0.1 The Proto-Word Principle

When a bare alias — a word with no namespace qualifier — is registered in Akasha, it makes one and only one claim: *this word exists*. No definition, no category, no part of speech is required. The act of registration is itself the statement: "this word is present and available to be given meaning."

This atom is called a **proto-word** (祖語). It is the lexical anchor for everything that will later be said about the word. At birth it holds only its own spelling. Its character accumulates through:

- **Links** — semantic edges connecting the proto-word to other atoms (`specializes`, `sys:is_a`, `sys:causes`, `sys:antonym`, …)
- **Set memberships** — collection assignments that situate the word within categories, domains, or dimensions
- **Qualified atoms** — atoms registered under namespaced aliases (e.g., `verb:cook:dry`, `word:en:dry`) that each declare themselves a specialization of the proto-word

A proto-word with no links is not "meaningless" — it is *potential meaning*, waiting for relationships to arrive. This is the true form of late-binding.

### 0.2 Late-Binding as the Natural Growth of Knowledge

In classical ontology design, a term must be completely defined before it can be used. In Akasha that is neither required nor expected. The normal lifecycle of a concept is:

```
1. Declaration    — a bare alias is registered; the proto-word is born
2. Qualification  — domain-specific atoms link back to it via 'specializes'
3. Characterization — relations, antonyms, and set memberships accumulate
4. Maturity       — the word's meaning is fully legible from the graph
```

This lifecycle can take seconds (if defined all at once in a CSL script) or months (if built up through usage and curation). The system imposes no deadline and requires no complete definition upfront.

### 0.3 Noun-First / Operand-First

Among qualified specializations, nouns are the natural anchor. A word like *plate* exists as a thing before it exists as an action. A word like *dry* exists as a quality before it exists as a process.

This mirrors the **operand-first principle**: *what a thing is* precedes *what is done to it or with it*. When Akasha loads a culinary ontology that defines `plate` as a verb ("to plate a dish"), the proto-word `plate` already exists as a noun. The culinary usage becomes a `specializes` link — an enrichment of the graph, not a replacement of an existing meaning.

The bare alias always names the most abstract presence of the word. Operational and pragmatic senses fan out as qualified atoms, each with their own content and relationships, all traceable back to the shared proto-word root.

### 0.4 Practical Consequence: No Alias Collisions

Because the proto-word owns the bare alias from first registration (first-wins), and qualified atoms never compete for bare aliases, there are no alias collisions in normal ontology loading.

Two ontology files that both define `"dry"` — one from core vocabulary, one from a culinary domain — produce a richer graph, not a conflict:

```
[dry]  ← proto-word (bare alias; first registrant)
   ↑ specializes
[verb:cook:dry]      ← culinary technique (remove moisture by heat)
   ↑ specializes
[word:en:dry]        ← English lexical entry
   ↑ specializes
[word:en:dry:adj]    ← adjectival use
```

Searching for `dry` resolves to the proto-word. Following its incoming `specializes` links reveals the full web of meanings the community has built around the word. An LLM navigating the graph can start at any alias and reach the proto-word by following `specializes` edges upward, or discover all specializations by traversing downward.

### 0.5 What This Means for Ontology Authors

When writing `.ak` or `.csl` ontology files, two layers of rules apply: **system behavior** (what the kernel guarantees automatically) and **authoring rules** (what you must write explicitly to produce a clean, navigable graph).

#### System behavior (automatic)

- **Bare word registrations are proto-word declarations.** Registering `dry` creates the lexical anchor; no definition is required.
- **Qualified registrations guarantee the proto-word.** Defining `verb:cook:dry` causes the system to ensure a proto-word `dry` exists and creates a `specializes` link automatically. The proto-word is created on demand if no earlier file claimed it.
- **Load order is deterministic and collision-free.** First-wins on bare aliases; later qualified atoms automatically `specialize` the first registrant. Load order is an efficiency concern, not a correctness requirement — proto-word late-binding means forward references resolve regardless of file order.

#### Authoring rules (explicit — the Three Laws)

These rules govern how to write ontology files. The system enforces topology automatically; these rules enforce authoring intent.

**Law 1 — Every namespace atom must produce a proto-word.**

This is now **automatically satisfied** by `def "namespace:name" "description"` in `.ak` files and `define name="namespace:name" description="..."` in `.csl` files. When a namespaced alias is registered, `set_alias()` calls `_ensure_protoword()` which creates the bare word atom and a `specializes` link (with `status="inferred"`) automatically. You never write bare alias lines in `.ak` files.

```
# LEGACY — still works but deprecated
w "Electric field: a physical field surrounding charged particles."
al $it "phys:em:electric_field"
al $it "electric_field"

# CORRECT — canonical .ak form; proto-word 'electric_field' auto-created
def "phys:em:electric_field" "A physical field surrounding electrically charged particles."
```

**Law 2 — `ln` / `link.create` uses proto-words (bare aliases) on both sides.**

```
# CORRECT — relationship between concepts, expressed at proto-word level
ln electric_field electric_charge @generates

# WRONG — relationship buried in namespace handles; invisible to other domains
ln phys:em:electric_field phys:charge:electric_charge @generates
```

Hub-membership links (`sys:is_a` to a category hub, `sys:part_of` to a root) may use namespace keys because they are structural bookkeeping, not semantic assertions.

**Law 3 — General noun before domain specialization.**

Define the proto-word (general concept) first. Domain-specific entries link back to it. This is auto-satisfied when `def "ns:name"` fires `_ensure_protoword()` — the proto-word is guaranteed to exist when the namespace atom is created. See `docs/for-llm/akasha-ontology-guide.md` for full examples.

---

## 1. What Is Ontology in Akasha?

In Akasha, **ontology** means the shared vocabulary of concepts, relations, and definitions that gives the knowledge graph its meaning.

Without ontology, the graph is a collection of isolated atoms connected by anonymous links. With ontology, those atoms become instances of known concepts, those links carry semantic weight, and every user (human or AI) can interpret the graph the same way.

Concretely, ontology in Akasha consists of three things:

1. **Relation labels** — names for link types, such as `sys:is_a`, `emo:joy`, or `geo:at`. Without agreed-upon labels, `A → B` means nothing; `A [sys:causes] B` means *A causes B*.
2. **Concept hubs** — named anchor atoms that other atoms link to. A hub called `Atlantis` lets every note about Atlantis point to the same node.
3. **Structured models** — concept plugins that interpret graph patterns and enforce domain-specific rules (see §6).

---

## 2. Three-Layer Architecture

Akasha's ontology is built up in three layers, each adding more structure:

```
┌─────────────────────────────────────────────────────┐
│  Layer 3 — Runtime                                  │
│  Built by users and AI via CLI commands and CSL     │
│  scripts. Persists in the graph. User-owned.        │
├─────────────────────────────────────────────────────┤
│  Layer 2 — Acquired                                 │
│  .ak and .csl files in ontology/. Loaded once at   │
│  first startup. Scope: sys:universal (shared).      │
├─────────────────────────────────────────────────────┤
│  Layer 1 — DNA                                      │
│  Hard-coded in lib/akasha/dna.py. Loaded by the    │
│  kernel at boot, before any session exists.         │
│  Cannot be modified without changing source code.   │
└─────────────────────────────────────────────────────┘
```

Each layer builds on the one below. DNA provides the absolute foundation; acquired files extend it with domain vocabulary; runtime operations extend it further for specific research or creative projects.

---

## 3. Layer 1 — DNA: The Innate Core

**Source:** `lib/akasha/dna.py`  
**Loaded:** At kernel boot, into `scope:sys:universal`  
**Mutable:** No — requires source code change

The DNA sequence is the state of Akasha's conceptual memory immediately after birth. It defines the most fundamental building blocks: how to express logic, how to describe space and time, and how to name emotions.

Every relation label defined in DNA is available as a link type from the first moment a session exists.

### 3.1 System & Topology Relations

| Relation | Meaning |
|----------|---------|
| `sys:is_a` | Class/subclass hierarchy (Dog is_a Animal) |
| `sys:part_of` | Meronymic component relation (Engine part_of Car) |
| `sys:associated_with` | Broad associative semantic link (default link type) |
| `calc:associated_with` | Loose conceptual association used in vocabulary files (e.g. `c_vocab_core*.ak`). Distinct from `sys:associated_with` — the `calc:` prefix marks it as a derived/calculated relation rather than a structural primitive. |
| `sys:mapped_to` | Forward topological mapping / transformation |
| `sys:mapped_from` | Inverse topological mapping / transformation |
| `sys:requires` | Dependency relation (Fire requires Oxygen) |
| `sys:causes` | Causality relation (Rain causes Wetness) |

### 3.2 Fuzzy Formal Logic

Akasha uses **fuzzy logic** rather than binary true/false, because real knowledge is rarely certain. Link weights encode degrees of confidence.

| Relation | Meaning |
|----------|---------|
| `log:not` | Fuzzy negation — probability of mutual exclusivity |
| `log:and` | Logical conjunction — degree of necessity for both |
| `log:or` | Logical disjunction — degree of sufficiency for either |
| `log:implies` | Fuzzy implication — confidence that P implies Q |
| `log:iff` | Fuzzy equivalence — probability that two concepts are semantically identical |

### 3.3 Spatiotemporal Axes

| Relation | Meaning |
|----------|---------|
| `geo:at` | Spatial link — pins an atom to coordinates [lat, lng] |
| `geo:ref` | Affine reference — calibrates historical vs modern maps |
| `chrono:period` | Temporal link — pins an atom to a historical era |
| `nar:perspective` | Narrative filter — defines the POV for a cognitive layer |

### 3.4 Emotion Dimensions

Emotion is a first-class dimension in Akasha. The DNA defines an 8-dimensional primary space (based on Plutchik/Keltner) and a set of compound emotions that emerge from combinations.

**Primary emotions (8 axes):**

| Relation | Meaning |
|----------|---------|
| `emo:joy` | Happiness, expansion, presence |
| `emo:sadness` | Melancholy, contraction, memory |
| `emo:fear` | Caution, avoidance, survival focus |
| `emo:anger` | Hostility, friction, boundary defence |
| `emo:trust` | Acceptance, openness, vulnerability |
| `emo:disgust` | Rejection, aversion, boundary protection |
| `emo:surprise` | Unexpectedness, interruption, attention reset |
| `emo:anticipation` | Forward-looking, expectation, readiness |

**Compound emotions (emergent):**

| Relation | Composition | Meaning |
|----------|-------------|---------|
| `emo:awe` | Fear + Surprise + Joy | Reverential wonder at something vast |
| `emo:nostalgia` | Joy + Sadness | Sentimental longing for the past |
| `emo:love` | Joy + Trust | Deep affection and attachment |
| `emo:guilt` | Fear + Sadness + Disgust(self) | Remorse for past actions |
| `emo:curiosity` | Anticipation + Surprise | Desire to explore the unknown |
| `emo:despair` | Sadness + Fear, no Anticipation | Complete loss of hope |
| `emo:contempt` | Anger + Disgust | Treating someone as beneath consideration |

### 3.5 Epistemological Frames

The DNA includes placeholder definitions for alternative philosophical lenses. These are designed to allow the system to analyse the same graph from different theoretical viewpoints in the future.

| Relation | Frame |
|----------|-------|
| `frame:dialectics:thesis` | The initial proposition |
| `frame:dialectics:antithesis` | The negation or contradiction |
| `frame:dialectics:synthesis` | The resolution combining both |
| `frame:systems:feedback_loop` | Circular causality |

---

## 4. Layer 2 — Acquired Ontology: Startup Files

**Source:** `ontology/` directory — package layout governed by `ontology/REGISTRY.json` v2  
**Loaded:** The `base1`, `base2`, `base3` packs (autoload=true in REGISTRY.json) load automatically on first startup, in order — base1 first so quick-start works at once, base2/base3 streaming in behind it. All other packages (art, film, tech, world, vocab, …) have autoload=false and are not loaded automatically.  
**Scope:** `sys:universal` (visible to all users)  
**Mutable:** Yes — add files to the appropriate package directory and they load on next first-boot (or after `onto.reload`)

The acquired ontology extends the DNA with richer vocabulary and concept hubs. It is designed to be the "shared common knowledge" that all users inherit without having to build it themselves.

> **REGISTRY.json v2 package layout:** Loading is **not** a recursive directory walk of `ontology/`. `ontology/REGISTRY.json` lists every package (name + autoload flag). At startup, only packages with `"autoload": true` (currently only `base`) are loaded into the graph. Other packages are loaded on demand or by setting their `"autoload"` flag to `true` and running `onto.reload`. The `ontology/thesaurus/` directory is loaded by the same boot sequence alongside the REGISTRY packages.

### 4.1 Shell Script Files (.ak)

`.ak` files are lists of shell commands, one per line. Each command is parsed by the shell and submitted to the kernel as a batch job.

**Canonical format (June 2026 and later):**

```
# example: ontology/common/emotions.ak
# def "namespace:name" "description" — proto-word auto-created, no al $it needed
def "emo:admiration" "Respect and warm approval."
def "emo:joy" "A feeling of great pleasure and happiness."

ln joy love sys:causes        ← bare aliases (proto-words), not namespace aliases
```

`def "ns:name" "description"` creates the atom with `meta.canonical=True`, registers the namespace alias, and auto-creates the proto-word (bare alias) via `_ensure_protoword`. A `specializes` link is automatically created from the namespace atom to its proto-word, with `status="inferred"`.

Legacy format (`w "text" + al $it "ns:name" + al $it "bare"`) still parses correctly but is deprecated in ontology files.

`.ak` files are best suited for flat vocabulary lists and concept definition sequences.

### 4.2 CSL Script Files (.csl)

`.csl` files contain CSL commands and are executed via `csl.run` at startup. They are suited for more expressive ontology definitions — particularly when using concept model methods (`fact.new`, `curation.new`, etc.) or when block syntax makes a definition clearer.

```
# example: ontology/common/setup.csl

# Define a fact collection for world geography
$geo_facts = fact.new:
    title       = "World Geography"
    description = "Core geographic facts shared across all domains"

fact.add:
    fact_type = relation
    content   = "The equator divides Earth into northern and southern hemispheres."
    source_id = $geo_facts.fact_root_id
```

### 4.3 Loading Behaviour

All file types are loaded **once per fresh install**. Four sentinel aliases track what has been loaded:

| Sentinel alias | Tracks |
|----------------|--------|
| `ont:ak:atoms:loaded` | Phase 1 of `.ak` loading complete (all atoms written, before link phase) |
| `ont:ak:loaded` | Full `.ak` load complete (atoms + links) |
| `ont:csl:loaded` | All `.csl` ontology scripts loaded |
| `ont:curation:loaded` | All `curations/*.csl` files auto-loaded |

On subsequent logins, sentinels are detected and loading is skipped. Use `onto.reload` or `onto.reset` (§4.4) to re-trigger loading.

**Startup output (first login, illustrative — actual files are in package directories):**
```
  [ont] Loading acquired ontology…
        ontology/base1/emo.ak         (74 steps)
        ontology/base1/word_core_01.ak (142 steps)
        …
  [ont] Ready — N steps across M files.
  [ont] Loading CSL ontology scripts…
        ontology/thesaurus/a_thesaurus_core.csl  (13 ops)
  [ont] CSL ready — 13 ops across 1 files.
```

**File ordering:** files within each directory are loaded in alphabetical order. Use filename prefixes (`a_`, `b_`, `c_`) to control execution order when one file depends on another.

### 4.4 Manual Reload / Reset

Two commands allow re-loading ontology after modification. Both require **LIBRARIAN** role or above.

**`onto.reload`** — Soft reset. Removes all four boot sentinels and re-triggers the full boot sequence in a background thread. Existing atoms are idempotent (content-addressed: same content = same key = no change). New or modified files will be picked up.

```
akasha/user $ onto.reload
{
  "status": "reload_triggered",
  "sentinels_cleared": ["ont:ak:atoms:loaded", "ont:ak:loaded", "ont:csl:loaded", "ont:curation:loaded"],
  "message": "Ontology reload started in background."
}
```

**`onto.reset confirm="RESET"`** — ⚠️ **DANGEROUS ZONE** ⚠️. Hard nuclear clear. Deletes ALL atoms, links, aliases, and namespace counts from nucleus except the 35 DNA primal atoms. Then re-triggers the full boot sequence. **This cannot be undone.** Use when you want a completely clean reload of the ontology from scratch.

```
akasha/user $ onto.reset confirm="RESET"
{
  "status": "reset_complete",
  "dna_atoms_preserved": 35,
  "message": "Nucleus cleared. DNA atoms restored. Ontology reload started."
}
```

Without `confirm="RESET"`, the command returns an error message describing what will be deleted.

> Note: **Thesaurus data** (stored in nucleus with `scope:sys:universal`) is cleared by `onto.reset` along with all other ontology data. The thesaurus is fully rebuilt on reload from `ontology/thesaurus/a_thesaurus_core.csl` and any curations that auto-load from `curations/`.

---

## 5. Layer 3 — Runtime Ontology: Building via CLI and CSL

Any user can extend the ontology at runtime by writing atoms, setting aliases, and creating links. These additions are user-owned (not in `scope:sys:universal` by default) and persist across sessions.

### 5.1 The Basic Pattern

```
# From the shell — define a concept hub and connect it
def "Quantum Entanglement"
ln "Quantum Entanglement" "Quantum Mechanics" sys:part_of
ln "Quantum Entanglement" "Non-locality" sys:causes

# From the CSL interpreter
csl> define name="Quantum Entanglement"
csl> link.create src="Quantum Entanglement" dst="Quantum Mechanics" rel="sys:part_of"
```

### 5.2 Writing Structured Ontologies with CSL

For larger ontology additions, CSL's block syntax and variable chaining make definitions readable and auditable:

```
# Define a cluster of related concepts
$qm   = define name="Quantum Mechanics"      description="Branch of physics describing phenomena at atomic scales." scope="universal"
$ent  = define name="Quantum Entanglement"   description="Correlation between quantum particles regardless of distance." scope="universal"
$sup  = define name="Superposition"          description="A quantum system existing in multiple states simultaneously." scope="universal"
$meas = define name="Measurement Problem"    description="The puzzle of how observation collapses a quantum superposition." scope="universal"

link.create:
    src = $ent.key
    dst = $qm.key
    rel = "sys:part_of"

link.create:
    src = $sup.key
    dst = $qm.key
    rel = "sys:part_of"

link.create:
    src = $meas.key
    dst = $sup.key
    rel = "sys:causes"
```

Before running, validate and preview:

```
akasha/user $ csl.check script="..."   # check for errors
akasha/user $ csl.dry   script="..."   # preview operations
akasha/user $ csl.run   script="..."   # execute
```

### 5.3 Saving Reusable Ontology Scripts

Ontology scripts that you use repeatedly can be saved to the graph and re-run by name:

```
akasha/user $ csl.save name="quantum_basics" script="..."
akasha/user $ csl.exec quantum_basics
```

Or stored as a `.csl` file in `ontology/` for automatic loading on fresh installs.

---

## 6. Concept Model Plugins

### 6.1 What Concept Models Do

Raw atoms and links are a flexible but low-level representation. **Concept model plugins** add a higher-level vocabulary on top: instead of manually writing atoms and drawing links to represent a "Fact with a source", you call `fact.new` and the plugin handles the internal graph structure for you.

Concept models provide:
- **Structured creation** — `fact.new`, `curation.new`, `intelligence.new`, etc.
- **Enforced relationships** — a Fact knows it belongs to a collection; a Curation knows its Premises
- **Domain-specific queries** — `fact.trace`, `intelligence.cycle`, `human.timeline`
- **Validation** — `fact.diagnose`, `curation.diagnose`, `intelligence.diagnose`

The same knowledge can be expressed as raw atoms OR as concept model instances. Concept models are the preferred approach whenever a domain has structure that would otherwise need to be manually reconstructed from raw links.

### 6.2 Auto-Discovery

Concept model plugins are discovered automatically at kernel boot. Any Python file in `lib/akasha/concepts/` or `lib/harmonia/` that defines a class with `CONCEPT_PREFIX` and `CONCEPT_METHODS` attributes is registered without any changes to `kernel.py`.

```
lib/akasha/concepts/
    fact.py        → registers fact.*, ft.* commands
    curation.py    → registers curation.*, cur.* commands
    intelligence.py→ registers intelligence.*, intel.* commands
    ...
```

This means adding a new concept domain to Akasha is a matter of dropping a single Python file into the `concepts/` directory.

### 6.3 The Knowledge Work Suite

These plugins are designed for research, analysis, and evidence-based knowledge building:

| Plugin | Prefix | Purpose |
|--------|--------|---------|
| **Note** | `note` | Hierarchical document structure (chapters, sections, paragraphs) |
| **Fact** | `fact` | Recording events, states, claims, and inferences with source tracking |
| **Curation** | `curation` | Premise-bound conflict resolution and auditable view construction |
| **Intelligence** | `intelligence` | Full decision-cycle orchestration (requirements → assessments → recommendations) |
| **Aggregation** | `agg` | Quantitative measurement and statistical partitioning |
| **Synthesis** | `synth` | Qualitative coding, thematic grouping, and interpretive mapping |
| **Presentation** | `pres` | Assembling knowledge into audience-ready deliverable structures |
| **Human** | `human` | Evidence-grounded actor modelling with provenance and dispute tracking |
| **Country** | `country` | Geopolitical entities, sovereignty events, and territorial claims |
| **Correspondence** | `corr` | Cross-system relational mapping and semantic correspondence |
| **Map** | `map` | Cartographic knowledge: editions, features, projections, and temporal state |
| **Geo** | `geo` | Grounded spatial coordinates, places, and field observations |
| **FieldNote** | `fieldnote` | Qualitative field observation and structured note-taking |
| **Survey** | `survey` | Survey design, respondent management, and quantitative data collection |
| **Log** | `log` | Chronological exploration logging with checkpoints and annotations |
| **Whiteboard** | `wb` | Scratch-space concept pinning and focus switching |
| **Cockpit** | `cockpit` | Operational dashboard with focal locking and dimensional tuning |
| **Thesaurus** | `thesaurus` | Cross-graph semantic enrichment, ShelfScore computation, and curator exhibition sequences |

The pipeline from raw observation to actionable decision follows this chain:

```
  Fact ──► Aggregation ──► Synthesis ──► Curation ──► Intelligence ──► Presentation
 (collect)  (quantify)    (code/theme)  (reconcile)   (assess/decide)   (communicate)
```

Each stage consumes the output of the previous one. A Curation workspace can take Fact collections as inputs; an Intelligence workspace can draw on Curation views as its evidence base.

### 6.4 The World-Building Suite (Harmonia)

The Harmonia domain provides concept models for interactive narrative and game environments:

| Plugin | Prefix | Purpose |
|--------|--------|---------|
| **Soma** | `soma` | Physical mech frame — part slots, equipment, damage state |
| **Engram** | `engram` | Psyche / memory carrier — utterances, bonds, metaphor messages |
| **Eidolon** | `eidolon` | Spatial topology — hierarchical locations, actor placement |
| **Operator** | `operator` | Stateless tactician — combat simulation, tactic execution |

Harmonia also includes infrastructure plugins used transparently by the engine:

| Plugin | Purpose |
|--------|---------|
| `NLP (nlp.py)` | Multi-locale natural-language processing (SpaCy, with graceful fallback) |
| `TFLite Engine` | Semantic embedding and similarity scoring (TensorFlow Lite or NumPy fallback) |
| `Weaver` | Network materialisation — assigns ownership and visibility scopes to all atoms |
| `Transport` | Data movement — CSV ↔ memory, crash-proof staging |
| `Sensor` | Background daemons — clocks, file watchers |

---

## 7. Current Ontology Contents

### 7.1 Directory Structure

```
ontology/
├── REGISTRY.json            ← v2 package registry (name + autoload flag per package)
├── base/                    autoload=true — core vocabulary (~9 700 atoms)
│   ├── PACK.json
│   ├── emo.ak
│   ├── word_core_01.ak … word_core_04.ak
│   ├── phil.ak, sci.ak, geo.ak, … (54 .ak files total)
│   └── …
├── tech/                    autoload=false — technology & computing namespaces
│   ├── PACK.json
│   ├── ai.ak, sys.ak, prog.ak, data.ak, … (60+ files)
│   └── …
├── world/                   autoload=false — humanities, mythology, narrative
│   ├── PACK.json
│   ├── myth.ak, tale.ak, polti.ak, … (20+ files)
│   └── …
├── vocab/                   autoload=false — extended word vocabulary
│   ├── PACK.json
│   └── word_ext_01.ak … word_ext_10.ak
├── art/, film/, biology/, geology/, law/, … (domain packs, all autoload=false)
└── thesaurus/               loaded by boot sequence alongside REGISTRY packages
    └── a_thesaurus_core.csl

curations/                   ← auto-loaded after ont:csl:loaded sentinel
└── sky_dreamers.csl         curator exhibition scripts (Thesaurus concept model)
```

Package loading is driven by `ontology/REGISTRY.json` v2, not by a recursive directory walk. Only packages with `"autoload": true` are loaded at startup — currently only `base`. To activate another package, set its `"autoload"` to `true` in REGISTRY.json and run `onto.reload`.

**`curations/`** is at the project root (outside `ontology/`). After the `ont:csl:loaded` sentinel is set, the boot sequence automatically loads all `.csl` files from `curations/`. This triggers on every boot where the `ont:curation:loaded` sentinel is absent — i.e., on first install and after `onto.reload` / `onto.reset`.

### 7.2 Base Package (`ontology/base1–3/` (the base packs))

The `base1`/`base2`/`base3` packs load automatically at startup (progressively, in order). Together they hold the core vocabulary, everyday life-world, and specialist/knowledge canopy — roughly 16k atoms across ~186 `.ak` files (base1 ≈ words, feelings and the everyday table; base2 ≈ the life-world; base3 ≈ the sciences and the knowledge map). Representative files:

**`emo.ak`** — Extended emotion vocabulary  
Defines compound emotion concepts with `emo:*` aliases, extending the 8 primary emotions hard-coded in DNA: `emo:admiration`, `emo:adoration`, `emo:aesthetic`, `emo:amusement`, `emo:anxiety`, `emo:awkwardness`, and more.

Links between emotion atoms establish the compositional relationships (e.g., `emo:awe` links to `emo:fear`, `emo:surprise`, and `emo:joy`).

**`word_core_01.ak` – `word_core_04.ak`** — Core vocabulary  
Defines fundamental abstract concepts with namespace aliases (`word:en:*`). Covers life, death, love, time, space, truth, justice, freedom, power, knowledge, and other foundational concepts.

**`phil.ak`, `sci.ak`, `geo.ak`, `hist.ak`, `lang.ak`, …** — Domain vocabulary  
Core concept hubs for philosophy, science, geography, history, linguistics, and other foundational domains. See the REGISTRY.json companion document or `onto.dump namespaces` for the full namespace list.

### 7.3 Optional Packages

Optional packages must be activated by setting `"autoload": true` in `ontology/REGISTRY.json` and running `onto.reload` (or enabled one-time via the appropriate load command).

| Package | Content |
|---|---|
| `tech` | Technology and computing namespaces (AI, programming, data, networking, cloud, IoT, OS, robotics, …) — 60+ `.ak` files |
| `world` | Humanities, mythology, narrative (myth, tale, polti, journey, narrative, writing, …) — 20+ `.ak` files |
| `vocab` | Extended word vocabulary (`word_ext_01.ak` – `word_ext_10.ak`) |
| `art`, `film` | Art movements, film movements, stage forms |
| `biology`, `geology`, `medicine`, `nutrition`, `music`, `law`, `literature` | Domain-specific content |
| `domain`, `archaeology`, `people`, `resources`, `space`, `war`, `weather`, `wine` | Specialised domains |

### 7.4 Sky Dreamers Ontology (`ontology/base2/sky.ak`)

**`sky.ak`** — Sky Dreamers: human figures and events in flight history  
Namespace: `sky:` with sub-namespaces `sky:myth:`, `sky:pioneer:`, `sky:event:`, `sky:enigma:`, `sky:artifact:`.

Root hub: `ont.sky_dreamers`. Defines 11 atoms tracing the human dream of flight from myth to the modern era:

| Atom | Category |
|---|---|
| `sky:myth:icarus`, `sky:myth:daedalus` | Greek myth |
| `sky:enigma:nazca_lines` | Ancient enigma |
| `sky:pioneer:da_vinci`, `sky:artifact:ornithopter` | Renaissance |
| `sky:event:montgolfier_first_flight` | First ascent, 1783 |
| `sky:pioneer:lilienthal` | Glider pioneer, 1896 |
| `sky:event:wright_first_flight` | First powered flight, 1903 |
| `sky:event:lindbergh_transatlantic` | Solo Atlantic crossing, 1927 |
| `sky:enigma:earhart_disappearance`, `sky:enigma:saint_exupery_disappearance` | Those who never returned |

Emotion links use `calc:has_emotion` to `emo:awe`, `emo:fear`, `emo:sadness`, `emo:anticipation`. Temporal chain expressed via `@precedes` / `@precedes_conceptually`. Bridges to existing aviation atoms via `sys:same_as` (Wright ↔ `sci:history:wright_brothers_flight`).

### 7.5 Curations Directory (`curations/`)

Curator exhibition scripts that use the Thesaurus concept model. These files are **automatically queued by the kernel** after the `ont:csl:loaded` sentinel is set on startup. They do not need to be run manually — the boot sequence loads them automatically (and re-loads them after `onto.reload` / `onto.reset` when the `ont:curation:loaded` sentinel is absent).

**`sky_dreamers.csl`** — People Who Dreamed of the Sky — A Genealogy of Falls and Flights (Sky Dreamers Vol. 1)  
A 10-waypoint curation exhibition covering the genealogy of flight from Icarus to Saint-Exupéry. Includes semantic enrichment (affective links, near-synonym clusters, namespace bridges) and curator interpretations in Japanese. See file header for run instructions and `thesaurus.view.curation` for the UI projection.

---

## 8. Writing Ontology Files

### 8.1 .ak File Format

An `.ak` file is a plain-text list of shell commands, one per line. Blank lines and lines beginning with `#` are ignored.

```
# ==============================================================================
# Akasha Ontology: [Topic]
# ⚠️ このontologyはLLMに指示して作られました。人間の専門家による厳密なチェックは
# 行なっていませんので、利用の際はご注意ください。
# (This ontology was created with LLM instructions and has not been rigorously
# reviewed by human domain experts. Please use with caution.)
# ==============================================================================

# --- Section name ---
# def "namespace:name" "Description." — canonical form
# Proto-word (bare alias) is auto-created by the kernel. No al $it line needed.
def "namespace:concept_name" "Clear description of the concept."

# Concept hub with no namespace (bare hub for proper nouns, archetypes, etc.)
def "Concept Name"

# ln uses bare aliases (proto-words) on both sides
ln concept_a concept_b sys:is_a
```

**Key rules for .ak files:**
- `def "namespace:name" "description"` creates a canonical hub atom, registers the alias, and auto-creates the proto-word. This is the standard form for concept definitions.
- `def "Name"` (no namespace, no description) creates a bare hub atom — useful for proper nouns, archetypes, etc.
- `ln bare_alias_a bare_alias_b relation` creates a link; aliases are resolved at load time
- `w "text"` + `al $it "alias"` is the legacy form — still valid but deprecated for definitions
- All aliases in `def/w/al` steps become permanent, `scope:sys:universal` (auto-injected)

### 8.2 .csl File Format

A `.csl` file contains CSL commands and can use the full CSL feature set including variables, block syntax, and concept model methods.

```csl
# ==============================================================================
# Akasha Ontology: [Topic] — CSL format
# ==============================================================================

# Create a fact collection as an ontological anchor
$col = fact.new:
    title       = "Topic: Domain Name"
    description = "Brief description of what this collection covers."

# Add foundational facts
fact.add:
    fact_type = relation
    content   = "Statement of foundational relation or fact."
    source_id = $col.fact_root_id

# Define and link concept hubs
$concept_a = define name="Concept A"
$concept_b = define name="Concept B"

link.create:
    src = $concept_a.key
    dst = $concept_b.key
    rel  = "sys:causes"
```

**When to use .csl instead of .ak:**
- The ontology uses concept model methods (`fact.new`, `curation.new`, etc.)
- Block syntax makes definitions clearer than single-line commands
- The script needs variables to chain one result into the next

### 8.3 Naming Conventions

Aliases follow a **dot-separated namespace** convention:

| Pattern | Used for | Examples |
|---------|----------|---------|
| `sys:*` | Core relations (DNA) | `sys:is_a`, `sys:causes` |
| `log:*` | Logic relations (DNA) | `log:implies`, `log:and` |
| `geo:*` | Spatial relations | `geo:at`, `geo:ref` |
| `chrono:*` | Temporal relations | `chrono:period` |
| `emo:*` | Emotion dimensions | `emo:joy`, `emo:admiration` |
| `nar:*` | Narrative structure | `nar:perspective` |
| `polti:NN` | Polti dramatic situations | `polti:01` through `polti:36` |
| `word:en:*` | English vocabulary | `word:en:love`, `word:en:death` |
| `frame:*` | Epistemological frames | `frame:dialectics:thesis` |
| `ont:*` | Ontology system internals | `ont:csl:loaded` |

User-defined concept hubs typically use plain names (`Atlantis`, `Quantum Mechanics`) without a namespace prefix, as they are proper names rather than relation types.

### 8.4 Late Binding and Ontology Verification

**Proto-word late binding (both `.ak` and `.csl`).**  
Both `ln` in `.ak` files and `link.create` in `.csl` files use the same late-binding mechanism. When a link target alias is not yet registered, the kernel extracts the bare segment of the alias and uses (or creates on demand) the corresponding proto-word. The link is stored with a valid atom key immediately. When the target namespace atom is later defined, it receives a `specializes` link to the proto-word, making the full path traversable. There are no dangling or pending states in normal ontology loading.

**Strict placeholder mode (opt-in: `=` prefix).**  
When two namespace atoms are intentionally distinct senses of the same proto-word and a link must target the specific sense rather than the shared proto-word, prefix the alias with `=`:

```
ln src =nar:tragedy @exemplifies           # .ak — strict dst
link.create src="..." dst="=nar:tragedy" rel="..."  # .csl — strict dst
```

The alias string is stored as a placeholder for that specific future atom. No proto-word fallback is applied. Use `onto.dump links` to confirm that strict-mode dst values have resolved to 64-char hex hashes once the target atom is registered.

**Resolution behaviour:**

| Context | Situation | Behaviour |
|---------|-----------|-----------|
| `.ak` or `.csl` | Target alias not yet registered (default) | Bare segment extracted; proto-word created if absent; link stored with valid key |
| `.ak` or `.csl` | Target alias already registered | Resolves at link-creation time; link stored with target's key |
| `.ak` or `.csl` | `=` prefix on alias (opt-in strict mode) | Alias string stored as exact placeholder; no proto-word fallback |

**Post-load verification with `onto.dump` and `onto.report`:**

After all ontology files have loaded, run these commands to audit the graph:

```
onto.report                          # alias collision log (unresolved entries only, by default)
onto.dump atoms ns=phil:             # all atoms in a namespace
onto.dump links rel=sys:is_a        # all is_a links
onto.dump aliases pattern=phil:%    # all phil: aliases
onto.dump sets collection=ontology.philosophy  # collection membership
onto.dump namespaces                 # atom count per namespace prefix
```

Under the proto-word design, alias collisions do not occur during normal loads — `onto.report` will typically show no unresolved entries. Use it primarily to detect unexpected bare-alias conflicts introduced by manual edits.

**LLM-assisted cross-checking:**

Because `onto.dump` can extract subgraphs by namespace, relation type, or collection, an LLM session can be used to verify ontology integrity after a batch of new files is added:

1. Run `onto.dump mode=atoms ns=phil:` and ask an LLM to confirm every term has at least one `sys:is_a` link to a hub.
2. Run `onto.dump mode=links rel=sys:antonym` and ask an LLM to verify the pairs are symmetric and semantically correct.
3. Run `onto.report` and ask an LLM to identify which overwrites (if any) represent genuine conflicts vs. intentional updates.

This workflow lets a collaborating LLM serve as an auditor without needing file-system access — the dump output is self-contained.

---

## 9. Further Reading

| Document | What it covers |
|----------|----------------|
| [`docs/users/user-manual.md`](../users/user-manual.md) | Shell command reference — how to write, link, alias, explore |
| [`docs/users/csl-manual.md`](../users/csl-manual.md) | CSL language — interactive interpreter and script mode |
| [`docs/concept-model/concept-model-spec.md`](../concept-model/concept-model-spec.md) | How to write a new concept model plugin |
| [`docs/concept-model/concept-model-intelligence.md`](../concept-model/concept-model-intelligence.md) | The Fact→Intelligence pipeline in detail |
| [`docs/ontology/concept-extensions-earth.md`](concept-extensions-earth.md) | Geo and Earth-science concept extensions |
| [`docs/concept-extensions-story.md`](concept-extensions-story.md) | Story and character concept extensions |
| [`docs/scope-dimension-model.md`](scope-dimension-model.md) | How multi-dimensional scoping works |

---

*For implementation details of the ontology loading mechanism: `api/portals/stdio.py` → `_autoload_ontology()`, `_autoload_ontology_csl()`*  
*For the DNA source: `lib/akasha/dna.py` → `get_primal_sequence()`*  
*For concept model registration: `lib/akasha/concepts/registry.py` → `ConceptRegistry.discover()`*
