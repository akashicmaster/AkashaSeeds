# Chapter 0: Basic Operations

By the end of this chapter, you will be able to use all the core commands of the Akasha CLI.
Read this chapter following on from the Quick Start.

> **How to read the Cookbook**
> The entire Cookbook, including this chapter, is self-contained.
> While working through the examples, you will not need to consult other documentation.
> For advanced usage and specification details,
> a reference list is provided at the end of each chapter. No reference links appear inline.

---

## What Is an Atom?

The smallest unit of memory in Akasha is called an **Atom**.

An Atom is plain text. Whether it is a single word, a sentence, or multiple paragraphs, the structure is the same. When you write an Atom, a **hash key** (e.g. `3a9fc2…`) is computed from the content and used to identify it. If the content is identical, writing it again produces the same key (idempotency).

```
w "Nile"                              # a single word is an Atom too
w "The Nile is the longest river in Africa"   # so is a sentence — the structure is the same
```

At this stage, an Atom is **just a symbol**. It carries no meaning for Akasha yet. Symbols acquire meaning only when they form relationships with other Atoms through the **links and Sets** described below.

**`$it`** is a shortcut that refers to the Atom you wrote most recently.

---

## 0-1 Write, Read, Delete

### Write

```
w "Nile"
w "The Nile is the longest river in Africa"
```

For multi-line content, wrap with `"""`:

```
w """
  Ancient Rome began as a city-state around 753 BCE
  and grew into an empire. At its height, its territory
  spanned the entire Mediterranean world.
"""
```

### Read

```
r $it           # read the most recent Atom
r 3a9fc2        # read by the first few characters of the hash key
r nile          # read by alias (explained below)
```

### Delete

```
rm $it
```

Writing the same content again restores it (because the hash is the same).

---

## 0-2 Assigning Aliases

You can assign a human-readable name in place of the hash key.

```
w "Nile"
al $it nile                      # assign the name "nile"
r nile                           # from here on, refer to it by this name
```

Multi-word names can be written as-is:

```
al $it "nile river"
r "nile river"
```

### Alias Multiplicity and Uniqueness

**A single Atom can have multiple aliases.**

```
w "Nile"
al $it nile
al $it "nile river"
al $it nil                       # abbreviated forms can be added too
r nile                           # any of the names can be used to reference it
r "nile river"
r nil
```

There is a constraint in the other direction: **each alias can only be bound to one Atom.** If `nile` is already assigned to another Atom, attempting to assign the same name to a different Atom later will not redirect the alias. Instead, the later Atom receives an implicit `specializes` link pointing to `nile`, and the name is not moved (first-wins policy).

```
al atom_A nile            # nile → atom_A is fixed
al atom_B nile            # later: nile does not move; a specializes link is created from atom_B → atom_A
```

To deliberately reassign an existing alias, delete it first with `al.rm`, then re-register it:

```
al.rm nile
al atom_B nile
```

### Managing Aliases

```
al.ls                            # list all named Atoms
al.find nile%                    # find names starting with "nile" (% is a wildcard)
al.find %river%                  # find names containing "river"
al.rm nile                       # remove the alias (the Atom itself remains)
```

---

## 0-3 Creating Links

### Links Create Meaning

An Atom on its own is a chunk of data. Meaning is created by links.

Immediately after writing it, the Atom "Nile" is just a 5-character string. Linking it to river with `sys:is_a` tells us that the Nile is a type of river. Linking it to coordinates with `geo:at` lets it be treated as a place on a map. Linking it with `emo:awe` adds the emotional context that this Atom evokes a sense of awe.

In this way, the accumulation of links transforms an Atom into something meaningful.

### Command Syntax

```
ln <source> <destination> <relation type>
```

```
w "Nile"
al $it nile
w "River"
al $it river

ln nile river sys:is_a          # nile is a type of river
```

### Link Uniqueness and Multiplicity

**Multiple links with different relation types can coexist between the same pair of Atoms.**

```
ln nile africa "flows through"     # ← (nile, africa, "flows through")
ln nile africa sys:associated_with # ← (nile, africa, sys:associated_with)
ln nile africa emo:evokes          # ← (nile, africa, emo:evokes)
```

All three are stored as independent links. There is no conflict.

The uniqueness constraint operates at the level of the **(source, destination, relation type)** triple. Writing the same triple again is an upsert — the link itself does not change; only its weight and authorship metadata are updated.

```
ln nile africa "flows through"     # first time: new registration
ln nile africa "flows through"     # second time: no duplicate; only metadata is updated
```

Relation types (rel) fall into two categories: those pre-defined by Akasha, and those you define freely yourself. The main ones are described below.

---

### sys: — System Relation Types (Core Vocabulary Defined in the DNA)

These are the most fundamental relation types, defined in Akasha's DNA (`lib/akasha/dna.py`). Use them when building the skeleton of the graph.

---

#### `sys:is_a` — Classification (Class Hierarchy)

Expresses that something is a member of a broader category. The dictionary equivalent is "a kind of".

```
ln nile    river    sys:is_a    # nile is a type of river
ln oak     tree     sys:is_a    # oak is a type of tree
ln tokyo   city     sys:is_a    # tokyo is a type of city
ln python  language sys:is_a    # Python is a type of language
ln sonnet  poem     sys:is_a    # a sonnet is a type of poem
```

Chaining `sys:is_a` links builds a classification hierarchy (taxonomy):

```
ln river       body_of_water  sys:is_a
ln lake        body_of_water  sys:is_a
ln ocean       body_of_water  sys:is_a
```

This enables queries such as "enumerate everything that belongs to body_of_water".

---

#### `sys:part_of` — Whole and Part

Expresses that something is a constituent of something larger. The relationship of "contained in" or "forms part of".

```
ln cairo      egypt        sys:part_of   # cairo is part of egypt
ln amazon     south_america sys:part_of  # the Amazon is part of South America
ln neuron     brain        sys:part_of   # a neuron is a component of the brain
ln chapter_1  book         sys:part_of   # chapter 1 is part of the book
ln wheel      bicycle      sys:part_of   # a wheel is a part of a bicycle
```

Difference from `sys:is_a`:

| | sys:is_a | sys:part_of |
|---|---|---|
| Question | "What kind of thing is it?" | "What is it part of?" |
| Example | tokyo → city (Tokyo is a type of city) | tokyo → japan (Tokyo is part of Japan) |
| Operation | Cross-category aggregation | Whole-part reconstruction |

---

#### `sys:causes` / `sys:requires` — Causation and Dependency

`sys:causes` expresses a cause-and-effect relationship.

```
ln drought    famine     sys:causes    # drought causes famine
ln exercise   fatigue    sys:causes    # exercise causes fatigue
ln interest   debt       sys:causes    # interest causes debt to grow
```

`sys:requires` expresses a dependency or prerequisite relationship.

```
ln fire       oxygen     sys:requires  # fire requires oxygen
ln flight     engine     sys:requires  # flight requires an engine
ln democracy  education  sys:requires  # democracy requires education
```

---

#### `sys:associated_with` — Loose Association

Use this when things are related but do not have a clear causal or classification relationship. It explicitly records the "somehow connected" intuition.

```
ln nile       ancient_egypt  sys:associated_with
ln summer     beach          sys:associated_with
ln jazz       new_orleans    sys:associated_with
ln sherlock   pipe           sys:associated_with
```

---

### emo: and sense: — Emotional and Sensory Relations

Akasha's emotional and sensory vocabulary is defined in three places.

**DNA (`lib/akasha/dna.py`) — Primary and Compound Emotions**

These are the foundational vocabulary loaded into `scope:sys:universal` at startup.

Primary emotions (8 dimensions based on the Plutchik model):

| Atom | Meaning |
|------|------|
| `emo:joy` | Joy, elation, expansion |
| `emo:sadness` | Sadness, contraction, memory |
| `emo:fear` | Fear, avoidance, survival instinct |
| `emo:anger` | Anger, friction, boundary defense |
| `emo:trust` | Trust, acceptance, opening vulnerability |
| `emo:disgust` | Disgust, rejection, boundary protection |
| `emo:surprise` | Surprise, attention reset |
| `emo:anticipation` | Anticipation, forward-looking readiness |

Compound emotions (combinations of primary emotions):

| Atom | Composition | Meaning |
|------|------|------|
| `emo:awe` | fear + surprise + joy | Awe, being overwhelmed before something vast |
| `emo:nostalgia` | joy + sadness | Sweet longing for the past |
| `emo:love` | joy + trust | Deep attachment, bond |
| `emo:curiosity` | anticipation + surprise | Drive to explore the unknown |
| `emo:despair` | sadness + fear | Complete loss of hope |
| `emo:contempt` | anger + disgust | Contempt, looking down on |

**`ontology/base/emo.ak` — Extended Emotion Vocabulary**

Fine-grained emotional states not present in the DNA are added here. Examples: `emo:anxiety`, `emo:calmness`, `emo:aesthetic` (aesthetic appreciation), `emo:craving`, `emo:entrancement`.

**`ontology/base/sense.ak` and `ontology/base/dna.ak` — Sensory Experience**

Atoms representing the five senses and sensory experiences are defined here.

`sense:` namespace (sensory conditions):

| Atom | Meaning |
|------|------|
| `sense:warmth` | Warmth, the heat associated with comfort and reassurance |
| `sense:cold` | Cold, clarity, tension |
| `sense:brightness` | Brightness of light, revelation, openness |
| `sense:smell_rain` | Petrichor, the scent of earth after rain |
| `sense:smell_earth` | Scent of soil, return to roots |
| `sense:taste_sweet` | Sweetness, pleasure, comfort |
| `sense:taste_bitter` | Bitterness, depth, acquired taste |

`dna:` namespace (colour, sound, scent, texture):

| Example | Meaning |
|----|------|
| `dna:color:azure`, `dna:color:red`, etc. | Colour perception |
| `dna:smell:fragrant`, `dna:smell:pungent`, etc. | Olfactory |
| `dna:sound:loud`, `dna:sound:rhythmic`, etc. | Auditory |
| `dna:taste:sweet`, `dna:taste:umami`, etc. | Gustatory |
| `dna:texture:crisp`, `dna:texture:hard`, etc. | Tactile |

**Patterns for linking emotions and sensory experience**

```
# emo:evokes — the Atom evokes this emotion
ln nile        emo:awe        emo:evokes
ln war_photo   emo:sadness    emo:evokes
ln reunion     emo:nostalgia  emo:evokes
ln discovery   emo:curiosity  emo:evokes

# calc:associated_with — sensory association
ln nile        sense:brightness  calc:associated_with
ln coffee      sense:smell_food  calc:associated_with
ln winter      dna:color:white   calc:associated_with
ln jazz        dna:sound:rhythmic calc:associated_with
```

Browsing the emotion and sensory lists:

```
exp ns=emo                   # list the emo: namespace
exp ns=sense                 # list the sense: namespace
exp ns=dna                   # list the dna: namespace (colour, sound, scent, texture)
al.find emo:%                # all aliases starting with "emo:"
```

---

### log: — Logical Relations

The `log:` namespace expresses logical relations between propositions.

```
ln fire_exists  oxygen_present  log:implies  # if fire exists, oxygen is present (implication)
ln hot          cold            log:not      # hot is not cold (negation)
```

Logical relations are used in the graph's inference layer (advanced usage). For everyday recording work, `sys:` and `emo:` cover the vast majority of cases.

---

### @ rel — Domain-Specific Relations Used by the Ontology

Domain-specific relation types are defined in the `.ak` files in `ontology/base/`. They are written with the `@` prefix.

```
ln vitamins    immunity     @supports      # vitamins support immunity
ln antibiotics bacteria     @prevents      # antibiotics prevent bacterial growth
ln salt        flavor       @enhances      # salt enhances flavour
ln thesis      antithesis   @contrasts_with
```

Frequently used @ rel values:

| rel | Meaning |
|-----|------|
| `@related_to` | There is a relationship (when classification is difficult) |
| `@associated_with` | Associative relationship |
| `@contrasts_with` | Contrast, opposition |
| `@supports` | Support, reinforcement |
| `@prevents` | Prevention, blocking |
| `@enables` | Enables, promotes |
| `@requires` | Prerequisite condition |
| `@produces` | Result, product |
| `@influences` | Has influence on |
| `@precedes` | Precedes (temporally or logically) |

---

### Freedom in rel and Recommended Vocabulary

**Akasha does not enforce any particular rel.** Any string can be used as a rel:

```
ln nile    egypt    "flows through"
ln caesar  rome     "ruled"
ln icarus  sun      "flew too close to"
```

This is intentional design. Akasha does not impose a meaning network — you decide the logic, perspective, and vocabulary with which you describe the world.

---

**That said, Akasha provides a pre-built vocabulary based on logic, emotion, and relational structure.**

Using this vocabulary is recommended for three reasons:

**① The graph becomes traversable**
Free-form rel values are readable, but if `"flows through"`, `"flow through"`, and `"passes through"` all exist separately, they will not match when you search or aggregate later. Built-in rel values function as consistent keys.

**② Meaning is defined**
The direction of `sys:causes` is fixed, and the meaning of `ref:before` is shared by all users. Mislinks are easier to audit, and LLMs or other clients can read the same vocabulary and understand it.

**③ Vocabulary for emotion, logic, and space-time is included**
Terms such as `emo:awe`, `ref:before`, `sys:part_of`, and `set_op:intersection` are provided from the start — vocabulary that describes not just the content of memories but their meaning structure.

**Guidance:**
- Use built-in rel values (`sys:` / `emo:` / `ref:` / `log:` / `set_op:` / `@`) whenever they cover the intended meaning.
- If you use custom vocabulary, keep notation consistent within the project.
- When recording external text (e.g. fetched from Wikipedia), free-form rel values are fine.

---

### Complete rel Reference

| Source | Namespace | Contents |
|--------|-----------|------|
| `lib/akasha/dna.py` | `sys:` | Basic topology: is_a / part_of / causes / requires / associated_with, etc. |
| `lib/akasha/dna.py` | `log:` | and / or / not / implies / iff (fuzzy logic) |
| `lib/akasha/dna.py` | `emo:` | Primary and compound emotions (DNA-defined) |
| `lib/akasha/dna.py` | `geo:` / `chrono:` | Spatiotemporal coordinate links |
| `lib/akasha/dna.py` | `set_op:` | union / intersection / difference / complement / membership / subset |
| `lib/akasha/ref_primitives.py` | `ref:` | Demonstratives, referents, logical connectives, quantifiers, ordering relations |
| `ontology/base/emo.ak` | `emo:` | Extended emotions (anxiety / calmness / aesthetic, etc.) |
| `ontology/base/sense.ak` | `sense:` | Sensory experience (warmth / brightness / smell_rain, etc.) |
| `ontology/base/dna.ak` | `dna:` | Colour, sound, scent, texture |
| Each `.ak` file in `ontology/base/` | `@` | Domain-specific relations (supports / prevents / enables, etc.) |

```
exp ns=ref          # ref: namespace — demonstratives, quantifiers, logical connectives
exp ns=emo          # emo: namespace — emotions
exp ns=sense        # sense: namespace — sensory experience
s.ls leaf:set_op    # set_op: atoms — set-theoretic operations
s.ls leaf:ref       # ref: atoms — the full set of reference primitives
al.find ref:%       # all aliases starting with "ref:"
```

---

### Managing Links

```
ln.ls nile                            # list all links connected to nile
ln.rm nile river sys:is_a             # remove the link (the Atom itself remains)
```

---

## 0-4 Working with Sets

A **Set** groups Atoms into a named collection. It is equivalent to a tag, folder, or category, but a single Atom can belong to multiple Sets simultaneously.

```
s.add <set name> <atom name or key>
```

`s.add` is **idempotent**. Adding the same Atom to the same Set multiple times creates no duplicates. There is no restriction on adding the same Atom to different Sets.

### Sets Create Meaning

Where a link expresses a relationship between two points, a Set expresses a bundle of Atoms that share the same property.

For example, if you only add `sys:is_a → river` links to "nile", "amazon", and "yangtze", the only way to query "enumerate all the world's major rivers" is to traverse backwards from river. By adding them to a Set called `rivers`, `s.ls rivers` retrieves them in one step.

Either links or Sets alone is incomplete. You end up with a graph you can traverse but not classify, or one you can classify but not traverse.

### Three Types of Sets

---

**① User-created Sets**

Create these freely for your own purposes and perspectives. There are no naming rules, but using the `category:subcategory` pattern makes them easier to distinguish from system Sets.

```
s.add rivers nile
s.add rivers amazon
s.add rivers yangtze

s.add topic:ancient_world nile
s.add topic:ancient_world rome
s.add topic:ancient_world alexandria

s.add research:2024 nile_wiki
s.add research:2024 caesar_wiki
```

---

**② Sets with defined roles (conventional patterns)**

These Sets are referenced by fixed names somewhere in the code. Knowing them helps you read the output of `s.ls`.

| Set name pattern | What it contains | Who creates it |
|----------------|-----------|-----------|
| `dialogue:{session_id}` | Statement Atoms from a dialogue Session | Contexa (dialogue engine) |
| `survey:{id}:q:{qid}` | Answer Atoms from a survey | Contexa (batch processing) |
| `fetch:{session_id}:refs` | Atoms retrieved by fetch | The fetch command |

---

**③ Sets automatically created by the system (implicit creation)**

Created automatically by Weaver (the word decomposition engine) or the ontology loader. They can be inspected with the `exp` command.

| Set name pattern | What it contains |
|----------------|-----------|
| `set:word:{lemma}` | All Atoms that mention this word (in its base form) |
| `components:{atom_key}` | The component words of that Atom (as decomposed by Weaver) |
| `leaf:{namespace}` | Atoms belonging to a namespace such as `emo:`, `geo:`, etc. |
| `lang:{lang_code}` | Atoms classified by language |

For example, immediately after writing `w "The Nile flows through Africa"`, running `s.ls set:word:nile` will show that Atom as a member.

---

### Basic Operations

```
s.ls rivers                      # list the members of the Set
s.rm rivers amazon               # remove from the Set (the Atom itself is not deleted)
s.clear rivers                   # empty the Set (Atoms are not deleted)
```

### Set Operations

```
s.op union  result_set  source_a  source_b   # union (belongs to either)
s.op isect  result_set  source_a  source_b   # intersection (belongs to both)
s.op diff   result_set  source_a  source_b   # difference (in source_a but not in source_b)
```

For example, to extract Atoms that belong to the ancient world and are also rivers:

```
s.op isect ancient_rivers topic:ancient_world rivers
s.ls ancient_rivers
```

---

## Atoms Become Concepts

Let us pause and clarify the relationship between Atoms, links, and Sets.

### What Is a Concept?

Akasha has no special data type called "concept". **A concept is an Atom that has acquired a position within the graph.**

As an Atom accumulates positional information — what category it belongs to, what it relates to, what emotions it evokes, which Sets it is in — its meaning grows richer.

The boundary is gradual. With no links and no Sets, an Atom is just a symbol. Each addition of a link or Set adds another layer of meaning.

### How Nile Becomes a Concept

```
w "Nile"
                        → just a 5-character symbol

al $it nile
                        → a named symbol (still no meaning)

ln nile river  sys:is_a
ln nile africa sys:associated_with
                        → we now know that Nile is a river and is related to Africa

s.add rivers nile
s.add topic:ancient_world nile
                        → classified in the "rivers" category, placed in the ancient world context

ln nile emo:awe emo:evokes
                        → the emotional tone that Nile evokes is recorded

fetch "Nile River"
al $it nile_wiki
ln nile nile_wiki "described in"
                        → the Wikipedia entry is linked, creating a reference to detailed content
```

The final state of nile can be understood through graph traversal as: "a river flowing through Africa, belonging to the ancient world, evoking awe, with a detailed Wikipedia entry". This is an **Atom as concept** in Akasha.

### def Is Syntactic Sugar for w + al

When creating the starting point for a concept, `w` and `al` are always used as a pair:

```
w "A natural watercourse of fresh water."
al $it river
```

The `def` command combines these two steps into one line:

```
def "river" "A natural watercourse of fresh water."
```

`def` writes an Atom and assigns a name to it at the same time. That is all it does. Meaning is given afterwards through `ln` and `s.add`.

The `def` command is explained in detail in Chapter 1. For now, think of it as "a shortcut that writes `w` and `al` in one line".

---

## 0-5 Exploration and Navigation

Commands for browsing and navigating the Atoms you have written.

```
hist                             # display recently written Atoms, newest first
ls                               # same (abbreviated form)
ls 20                            # specify a count
```

### dive — Expanding the Meaning Space

```
dive nile                        # expand the area around "nile" (links, related words)
```

While in dive mode, you can navigate by entering a number alone:

```
dive nile
> 2                              # navigate to the Atom at signpost 2
> out                            # return to the level above
```

### tree — Link-Traversal Tree

`tree` walks outgoing links from a starting point and renders the result as a tree.

```
tree <alias|key|set:name|ns:prefix> [depth=2] [follow=<rel>] [format=rich|ascii]
```

**Target types** — auto-detected from the first argument:

| Target form | What it shows |
|---|---|
| `<alias>` or `<key>` | Atom's outgoing link tree (BFS link traversal) |
| `set:<name>` | Set members as top-level nodes, each with their link sub-trees |
| `ns:<prefix>` | All Atoms in a namespace as top-level nodes |

**Optional parameters:**

| Parameter | Default | Description |
|---|---|---|
| `depth=` | `2` | Traversal depth (1–5 cap) |
| `follow=` | *(all)* | Only follow links of this relation type (e.g. `follow=sys:part_of`) |
| `format=` | `rich` | `rich` uses colour and Unicode box-drawing; `ascii` uses plain line-drawing |

Examples:

```
tree nile depth=3
tree set:rivers depth=2
tree ns:emo depth=1 follow=sys:is_a format=ascii
```

A depth-1 tree shows only direct links. Depth-3 shows three levels of connected Atoms. Output is capped at 20 children and 150 total nodes to keep the display readable.

### Browsing the Ontology

Akasha comes with concept namespaces such as `emo:`, `geo:`, and `calc:` built in from the start.

```
exp ns=emo                       # list Atoms in the emotion namespace
exp ns=geo                       # the geography namespace
al.find emo:%                    # all aliases starting with "emo:"
```

---

## 0-6 Importing from External Sources

Fetches articles from Wikipedia or a URL and stores them as Atoms. After retrieval, word decomposition (Weaver) runs automatically.

```
fetch "Nile River"               # search for and retrieve "Nile River" from Wikipedia
fetch "https://..."              # retrieve directly from a URL
```

Immediately after retrieval, the result is accessible via `$it`, so you can continue with aliasing and linking:

```
fetch "Nile River"
al $it nile_wiki
ln nile nile_wiki "described in"
```

---

## 0-7 Checking Status

```
status                           # session, memory, and JCL queue status
ping                             # check kernel responsiveness
```

---

## $ Reference Notation Summary

| Notation | Meaning |
|------|------|
| `$it` | The Atom you wrote most recently |
| `$0` | Your most recent Atom (history entry 0) |
| `$1` `$2` … | History entries 1, 2, … |
| `$0:5` | History entries 0 through 5 (range) |
| `$who` `$where` `$when` | Typed context variables (set with `ref set`) |
| `nile` | An alias |
| `3a9fc2` | A hash key (a few leading characters are sufficient) |

---

## Next Steps

This chapter covered writing Atoms, assigning names to them, and giving them meaning through links and Sets.

Chapter 1 introduces **Concept Models**. It explains how to define commonly used structures — people, documents, surveys, and more — with the `def` command, and how to build reusable models by combining `ln` and `s.add`.

You can check the list of available models at any time:

```
help concepts
```

---

*Next chapter: Chapter 1 — Introduction to Concept Models*
