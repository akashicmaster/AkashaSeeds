# Green Book, Chapter 1: Enriching Ontology Atoms with Structured Attributes

> **Before this chapter:** Read Red Book, Chapter 1 for the concept model CLI
> operations, and Green Book, Chapter 0 for .ak file creation.
> This chapter shows how to combine ontology structure with concept model views.

By the end of this chapter you will be able to take atoms that already exist in
the ontology — loaded from a .ak file — and annotate them with numeric
attributes so that the concept model views (`rec.table`, `quadrant.plot`,
`rec.hist`) become fully operational. You will not write a single line of Python.
All operations are CLI commands or .ak files.

---

## 1-1 Ontology and Concept Models as Two Layers

Every atom in Akasha can participate simultaneously in two independent layers.

**Layer 1 — Ontology: what things are and how they relate**

When you write a .ak file and load it, you are building structural knowledge.
The `def` command creates atoms. The `ln` command declares typed relationships
between them. The `al` command gives human-readable names. Together, these
establish meaning in the graph — `fruit:fig` is a type of `fruit`, it grows in
`geo:mediterranean` climates, it evokes `emo:nostalgia`, and it relates to
`concept:honey` through `thesaurus:related`. This is the ontology layer.

**Layer 2 — Concept models: how to measure and compare things**

The `rec.*` family of commands treats atoms as data points. `rec.set` attaches
a named numeric attribute — `sweetness`, `acidity`, `saltiness` — to any atom
by key. `rec.idx` registers that atom in a named analysis set. Once enrolled,
`rec.table`, `quadrant.plot`, and `rec.hist` can operate on the set.

**The crucial point: the two layers are completely independent.**

Adding a `sweetness` attribute to `fruit:fig` does not modify its structural
meaning. The `sys:is_a` link to `fruit` is untouched. The `emo:evokes` link to
`emo:joy` is untouched. `rec.set` only adds a `rec:` namespace link — a
numeric annotation hanging off the atom — and that link is invisible to the
ontology traversal commands (`explore`, `tree`, `lens`).

Conversely, the ontology layer does not know or care about rec attributes.
Loading a new .ak file that redefines `fruit:fig` would update the description
atom, but the `sweetness=0.88` attribute attached by `rec.set` would survive
unchanged.

This independence is a deliberate application of Akasha's Operand / Operator /
Agent design. Atoms are the operands — passive data, no embedded behaviour.
The ontology commands (`def`, `ln`) and the concept model commands (`rec.set`,
`rec.idx`) are separate operator families, each evolving independently. You,
the ontology builder, are the agent that decides when and how to apply them.

**Two routes to concept model views**

| Route | Starting point | Use when |
|---|---|---|
| **A** | `rec.new` creates fresh atoms | You are building data purely for analysis — no structural meaning needed |
| **B** | Ontology atoms already exist; annotate with `rec.set` | Atoms carry structural meaning you want to preserve alongside numeric analysis |

Red Book, Chapter 1 covered Route A in full. This chapter covers Route B.

---

## 1-2 Route B in Depth: Annotating Ontology Atoms

Assume you have already loaded `fruit.ak` (as created in Green Book, Chapter 0).
The following seven atoms now exist in the graph:

```
fruit:fig          fruit:grape     fruit:date
fruit:pomegranate  fruit:olive     fruit:lemon
fruit:orange
```

They carry ontology links — `sys:is_a`, `geo:origin`, emotional associations —
but they have no numeric attributes yet. `rec.table` on any set containing them
would produce an empty column list.

### Step 1 — Attach sweetness and acidity attributes

Use `rec.set` for each atom. The `key` parameter is the atom's canonical
identifier (the same key used in `def` and `ln` in the .ak file):

```
rec.set key=fruit:fig         attr=sweetness val=0.88
rec.set key=fruit:fig         attr=acidity   val=0.18

rec.set key=fruit:grape       attr=sweetness val=0.82
rec.set key=fruit:grape       attr=acidity   val=0.35

rec.set key=fruit:date        attr=sweetness val=0.95
rec.set key=fruit:date        attr=acidity   val=0.05

rec.set key=fruit:pomegranate attr=sweetness val=0.65
rec.set key=fruit:pomegranate attr=acidity   val=0.55

rec.set key=fruit:olive       attr=sweetness val=0.10
rec.set key=fruit:olive       attr=acidity   val=0.22

rec.set key=fruit:lemon       attr=sweetness val=0.08
rec.set key=fruit:lemon       attr=acidity   val=0.95

rec.set key=fruit:orange      attr=sweetness val=0.72
rec.set key=fruit:orange      attr=acidity   val=0.52
```

`rec.set` is idempotent within a session. Running the same command twice
replaces the attribute value — it does not create a duplicate. If you correct a
score, simply re-run `rec.set` with the new value.

### Step 2 — Enrol each atom in an analysis set

`rec.idx` registers an atom in a named set so that the view commands know
which atoms to include:

```
rec.idx key=fruit:fig         sets=rec:fruit_analysis
rec.idx key=fruit:grape       sets=rec:fruit_analysis
rec.idx key=fruit:date        sets=rec:fruit_analysis
rec.idx key=fruit:pomegranate sets=rec:fruit_analysis
rec.idx key=fruit:olive       sets=rec:fruit_analysis
rec.idx key=fruit:lemon       sets=rec:fruit_analysis
rec.idx key=fruit:orange      sets=rec:fruit_analysis
```

The `sets=` parameter accepts a plain name. The `set:` prefix is added
automatically if omitted, but including it explicitly is equally valid:
`sets=set:rec:fruit_analysis`.

### Step 3 — Verify with rec.table

```
rec.table in_set=rec:fruit_analysis
```

Output:

```
  set:rec:fruit_analysis  (7 items)

  atom                sweetness   acidity
  ────────────────────────────────────────
  fruit:fig              0.88      0.18
  fruit:grape            0.82      0.35
  fruit:date             0.95      0.05
  fruit:pomegranate      0.65      0.55
  fruit:olive            0.10      0.22
  fruit:lemon            0.08      0.95
  fruit:orange           0.72      0.52
```

All seven atoms are present with both attributes populated. If any row shows
`—` in an attribute column, that atom was not reached by `rec.set`. Re-run the
corresponding command and the table will update.

### Step 4 — Plot the scatter chart

```
quadrant.plot in_set=rec:fruit_analysis x=acidity y=sweetness \
    q1="tangy sweet" q2="mellow sweet" q3="bland" q4="tart"
```

Output:

```
  set:rec:fruit_analysis  ·  acidity × sweetness
         mellow sweet              tangy sweet

  sweetness ↑
   1.00 ┤                          ┆
        ┤      ●                   ┆                   date
        ┤  ●        ●              ┆                   fig, grape
        ┤                          ┆       ●            orange
   0.65 ┤                          ┆   ●               pomegranate
        ┼╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┼╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌
        ┤                          ┆
        ┤                          ┆
        ┤  ●                       ┆                   olive
        ┤                          ┆                ●  lemon
   0.00 ┤                          ┆
        bland                      ┆tart
        └──────────────────────────────────────────────
         0.05                    0.50                0.95
         acidity →
```

The chart reveals the structure of the dataset immediately. Date, fig, and grape
cluster in the mellow-sweet corner — low acidity, high sweetness. Lemon sits
alone in the tart extreme. Olive occupies the bland region, reflecting its
primarily savoury, non-sweet profile. Orange and pomegranate share the
tangy-sweet quadrant, both offering a balance of sweetness and acid bite.

The dividing lines are placed automatically at the midpoint of the data range
(acidity midpoint ≈ 0.50; sweetness midpoint ≈ 0.52). To fix the midpoint at
a canonical 0.50/0.50 for consistent cross-session comparison, add `x_mid=0.5
y_mid=0.5` to the command.

**The original ontology atoms are unchanged.** Run `dive fruit:fig` after
this step and you will see exactly the same structural links as before — no
`sweetness` or `acidity` entries appear there. The rec attributes live in the
`rec:` namespace, separate from the ontology traversal layer.

---

## 1-3 Using set.add to Group Atoms for Analysis

In Route B above, you annotated atoms and enrolled them in an analysis set
entirely through CLI commands. There is an alternative that keeps the grouping
decision inside the .ak file itself.

### Declaring the analysis group in .ak

In your `fruit.ak` file, add `set.add` lines beneath the atom definitions:

```
def "fruit:fig"          "Fig — Ficus carica; sweet, seedy Mediterranean fruit"
def "fruit:grape"        "Grape — Vitis vinifera; fresh or dried (raisin)"
def "fruit:date"         "Date — Phoenix dactylifera; intensely sweet stone fruit"
def "fruit:pomegranate"  "Pomegranate — Punica granatum; jewel-seeded acidic fruit"
def "fruit:olive"        "Olive — Olea europaea; bitter stone fruit; cured or pressed"
def "fruit:lemon"        "Lemon — Citrus limon; high-acid citrus"
def "fruit:orange"       "Orange — Citrus sinensis; sweet-acid citrus"

ln fruit:fig         fruit        sys:is_a
ln fruit:grape       fruit        sys:is_a
ln fruit:date        fruit        sys:is_a
ln fruit:pomegranate fruit        sys:is_a
ln fruit:olive       fruit        sys:is_a
ln fruit:lemon       fruit        sys:is_a
ln fruit:orange      fruit        sys:is_a

set.add name="set:fruit:mediterranean" id="fruit:fig"
set.add name="set:fruit:mediterranean" id="fruit:grape"
set.add name="set:fruit:mediterranean" id="fruit:date"
set.add name="set:fruit:mediterranean" id="fruit:pomegranate"
set.add name="set:fruit:mediterranean" id="fruit:olive"
set.add name="set:fruit:mediterranean" id="fruit:lemon"
set.add name="set:fruit:mediterranean" id="fruit:orange"
```

After `run fruit.ak`, the set `set:fruit:mediterranean` is
populated automatically.

### Scanning the set before annotation

```
lens src=set:fruit:mediterranean
```

This lists every atom in the set along with its description and any links
already attached. Use this to confirm all seven fruits are present and their
structural definitions look correct before adding numeric attributes.

### Annotating from the set

Once you have verified the set contents, the annotation workflow is the same as
in 1-2 above — `rec.set` followed by `rec.idx`. The only advantage of
declaring the group in .ak is that the membership decision is version-controlled
in your ontology file. When you reload the .ak after a session restart, the
set re-populates automatically (atom loading is idempotent). You then re-run
your attribute commands to restore the rec layer.

**When to use this pattern:** Use `set.add` in .ak when you are organising a
permanent analytical grouping (e.g. "all fruits cultivated in the
Mediterranean") and want that grouping to survive across sessions without
manual re-entry. Keep the `rec.set` annotations in a separate shell script (see
section 1-7) that you run after loading the .ak.

---

## 1-4 LLM-Assisted Attribute Generation

Manually scoring seven fruits is straightforward. Scoring a hundred concept
atoms by hand is tedious and error-prone. The LLM-assisted workflow transfers
the scoring labour to a language model whose training data already includes
culinary, cultural, or scientific knowledge about your domain.

### Step 1 — Export the atom list

```
onto.dump atoms ns=fruit:
```

Output:

```
fruit:date          "Date — Phoenix dactylifera; intensely sweet stone fruit"
fruit:fig           "Fig — Ficus carica; sweet, seedy Mediterranean fruit"
fruit:grape         "Grape — Vitis vinifera; fresh or dried (raisin)"
fruit:lemon         "Lemon — Citrus limon; high-acid citrus"
fruit:olive         "Olive — Olea europaea; bitter stone fruit; cured or pressed"
fruit:orange        "Orange — Citrus sinensis; sweet-acid citrus"
fruit:pomegranate   "Pomegranate — Punica granatum; jewel-seeded acidic fruit"
```

Copy this output to your clipboard.

### Step 2 — Compose a prompt for the LLM

Open Claude, ChatGPT, or any capable language model. Paste the following prompt,
replacing the atom list with the output from Step 1:

---

```
I am building a knowledge graph in Akasha. Below are Mediterranean fruit atoms
with their descriptions.

fruit:date          "Date — Phoenix dactylifera; intensely sweet stone fruit"
fruit:fig           "Fig — Ficus carica; sweet, seedy Mediterranean fruit"
fruit:grape         "Grape — Vitis vinifera; fresh or dried (raisin)"
fruit:lemon         "Lemon — Citrus limon; high-acid citrus"
fruit:olive         "Olive — Olea europaea; bitter stone fruit; cured or pressed"
fruit:orange        "Orange — Citrus sinensis; sweet-acid citrus"
fruit:pomegranate   "Pomegranate — Punica granatum; jewel-seeded acidic fruit"

For each fruit, assign a sweetness score (0.0 = not sweet at all, 1.0 = maximum
sweetness) and an acidity score (0.0 = not acidic at all, 1.0 = maximum acidity)
based on standard culinary knowledge of the fresh, raw fruit.

Return the results as Akasha CLI commands in this exact format, with no
additional text:

rec.set key=<atom_key> attr=sweetness val=<value>
rec.set key=<atom_key> attr=acidity   val=<value>
rec.idx key=<atom_key> sets=rec:fruit_analysis
```

---

### Step 3 — Receive and review the LLM output

A well-prompted LLM will return something close to:

```
rec.set key=fruit:date         attr=sweetness val=0.95
rec.set key=fruit:date         attr=acidity   val=0.05
rec.idx key=fruit:date         sets=rec:fruit_analysis

rec.set key=fruit:fig          attr=sweetness val=0.88
rec.set key=fruit:fig          attr=acidity   val=0.18
rec.idx key=fruit:fig          sets=rec:fruit_analysis

rec.set key=fruit:grape        attr=sweetness val=0.82
rec.set key=fruit:grape        attr=acidity   val=0.35
rec.idx key=fruit:grape        sets=rec:fruit_analysis

rec.set key=fruit:lemon        attr=sweetness val=0.08
rec.set key=fruit:lemon        attr=acidity   val=0.95
rec.idx key=fruit:lemon        sets=rec:fruit_analysis

rec.set key=fruit:olive        attr=sweetness val=0.10
rec.set key=fruit:olive        attr=acidity   val=0.22
rec.idx key=fruit:olive        sets=rec:fruit_analysis

rec.set key=fruit:orange       attr=sweetness val=0.72
rec.set key=fruit:orange       attr=acidity   val=0.52
rec.idx key=fruit:orange       sets=rec:fruit_analysis

rec.set key=fruit:pomegranate  attr=sweetness val=0.65
rec.set key=fruit:pomegranate  attr=acidity   val=0.55
rec.idx key=fruit:pomegranate  sets=rec:fruit_analysis
```

Before pasting into the CLI, read through the values. Ask yourself: does a
date scoring 0.95 sweetness and 0.05 acidity feel right? Does 0.10 sweetness
for olive make sense (raw olives are bitter, not sweet — yes, this is correct)?
LLMs can make overconfident mistakes on less-familiar domains, so a brief
sanity read matters.

### Step 4 — Paste into the CLI

Copy the entire block of commands and paste it into the Akasha CLI. Commands
are processed line by line. After the last line, run:

```
rec.table in_set=rec:fruit_analysis
```

to confirm all seven atoms are present with both attributes populated.

### Why this workflow scales

An LLM's training data contains decades of culinary literature, nutritional
databases, flavour-science papers, and recipe collections. For well-established
domains — Mediterranean foods, world cheeses, classical music, historical
events — LLM scoring is surprisingly consistent with expert consensus. The
scores it produces are not as precise as a laboratory measurement, but they are
sufficient for semantic placement and comparative analysis.

Akasha provides the persistence layer the LLM lacks: once the scores are
written, they survive session resets, can be queried, and become the foundation
for views the LLM cannot generate on its own. The workflow is a direct
expression of the Akasha + LLM complementarity described in the architectural
overview — the LLM contributes knowledge; Akasha contributes permanence and
structure.

---

## 1-5 Cheese Analysis: Multiple Attributes

Fruits work well for a two-attribute scatter plot. Cheeses offer a richer
example: they carry both categorical attributes (country, texture category) and
multiple numeric ones (aging months, saltiness, creaminess). This section walks
through the full workflow.

### Defining cheeses in .ak

Create `cheese.ak`:

```
# Texture categories
def "cheese:soft"        "Soft-ripened cheese — rind-matured, creamy interior"
def "cheese:hard"        "Hard cheese — low moisture, extended aging, dense"
def "cheese:crumbly"     "Crumbly cheese — high-acid, moisture expelled"
def "cheese:firm"        "Firm cheese — moderate aging, sliceable body"
def "cheese:semi_hard"   "Semi-hard cheese — between firm and hard"

# Countries of origin
def "geo:france"         "France"
def "geo:switzerland"    "Switzerland"
def "geo:greece"         "Greece"
def "geo:spain"          "Spain"
def "geo:cyprus"         "Cyprus"
def "geo:italy"          "Italy"

# Individual cheeses
def "cheese:brie"        "Brie de Meaux — French soft-ripened cow's milk cheese"
def "cheese:gruyere"     "Gruyère — Swiss mountain hard cheese, aged in cellars"
def "cheese:feta"        "Feta PDO — Greek brined crumbly sheep/goat cheese"
def "cheese:manchego"    "Manchego PDO — Spanish firm aged sheep's milk cheese"
def "cheese:halloumi"    "Halloumi PDO — Cypriot semi-hard grilling cheese"
def "cheese:pecorino"    "Pecorino Romano PDO — Italian hard aged sheep's milk"

# Classification: texture
ln cheese:brie      cheese:soft      sys:is_a
ln cheese:gruyere   cheese:hard      sys:is_a
ln cheese:feta      cheese:crumbly   sys:is_a
ln cheese:manchego  cheese:firm      sys:is_a
ln cheese:halloumi  cheese:semi_hard sys:is_a
ln cheese:pecorino  cheese:hard      sys:is_a

# Classification: origin
ln cheese:brie      geo:france       geo:origin
ln cheese:gruyere   geo:switzerland  geo:origin
ln cheese:feta      geo:greece       geo:origin
ln cheese:manchego  geo:spain        geo:origin
ln cheese:halloumi  geo:cyprus       geo:origin
ln cheese:pecorino  geo:italy        geo:origin

# Analysis set
set.add name="set:cheese:european" id="cheese:brie"
set.add name="set:cheese:european" id="cheese:gruyere"
set.add name="set:cheese:european" id="cheese:feta"
set.add name="set:cheese:european" id="cheese:manchego"
set.add name="set:cheese:european" id="cheese:halloumi"
set.add name="set:cheese:european" id="cheese:pecorino"
```

Load it:

```
run cheese.ak
```

### Annotating with numeric attributes

```
# Brie: France, soft, 4 months aging
rec.set key=cheese:brie     attr=aging_months  val=4
rec.set key=cheese:brie     attr=saltiness     val=0.25
rec.set key=cheese:brie     attr=creaminess    val=0.90
rec.idx key=cheese:brie     sets=rec:cheese_analysis

# Gruyère: Switzerland, hard, 12 months aging
rec.set key=cheese:gruyere  attr=aging_months  val=12
rec.set key=cheese:gruyere  attr=saltiness     val=0.55
rec.set key=cheese:gruyere  attr=creaminess    val=0.55
rec.idx key=cheese:gruyere  sets=rec:cheese_analysis

# Feta: Greece, crumbly, 3 months aging
rec.set key=cheese:feta     attr=aging_months  val=3
rec.set key=cheese:feta     attr=saltiness     val=0.85
rec.set key=cheese:feta     attr=creaminess    val=0.35
rec.idx key=cheese:feta     sets=rec:cheese_analysis

# Manchego: Spain, firm, 6 months aging
rec.set key=cheese:manchego attr=aging_months  val=6
rec.set key=cheese:manchego attr=saltiness     val=0.60
rec.set key=cheese:manchego attr=creaminess    val=0.45
rec.idx key=cheese:manchego sets=rec:cheese_analysis

# Halloumi: Cyprus, semi-hard, fresh (0 months)
rec.set key=cheese:halloumi attr=aging_months  val=0
rec.set key=cheese:halloumi attr=saltiness     val=0.70
rec.set key=cheese:halloumi attr=creaminess    val=0.30
rec.idx key=cheese:halloumi sets=rec:cheese_analysis

# Pecorino: Italy, hard, 18 months aging
rec.set key=cheese:pecorino attr=aging_months  val=18
rec.set key=cheese:pecorino attr=saltiness     val=0.80
rec.set key=cheese:pecorino attr=creaminess    val=0.40
rec.idx key=cheese:pecorino sets=rec:cheese_analysis
```

### rec.table — verify all attributes

```
rec.table in_set=rec:cheese_analysis
```

Output:

```
  set:rec:cheese_analysis  (6 items)

  atom               aging_months  saltiness  creaminess
  ───────────────────────────────────────────────────────
  cheese:brie               4        0.25       0.90
  cheese:gruyere           12        0.55       0.55
  cheese:feta               3        0.85       0.35
  cheese:manchego           6        0.60       0.45
  cheese:halloumi           0        0.70       0.30
  cheese:pecorino          18        0.80       0.40
```

### quadrant.plot — saltiness vs. creaminess

```
quadrant.plot in_set=rec:cheese_analysis x=saltiness y=creaminess \
    q1="salty & creamy" q2="mild & creamy" q3="mild & dry" q4="salty & dry"
```

Output:

```
  set:rec:cheese_analysis  ·  saltiness × creaminess
          mild & creamy               salty & creamy

  creaminess ↑
   1.00 ┤                          ┆
        ┤                          ┆
        ┤  ●                       ┆                   brie
        ┤                          ┆
   0.60 ┼╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┼╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌
        ┤                          ┆  ●                gruyère
        ┤                          ┆       ●           manchego
        ┤                          ┆         ●    ●    pecorino, feta
        ┤                          ┆     ●             halloumi
   0.00 ┤                          ┆
        mild & dry                 ┆salty & dry
        └──────────────────────────────────────────────
         0.25                    0.55                0.85
         saltiness →
```

The structural insight from the chart: Brie stands alone in the mild-and-creamy
corner. All other cheeses land in the salty-and-dry quadrant, with Gruyère
closest to centre. This reflects a genuine pattern in aged Mediterranean and
Alpine cheeses — brine-curing and extended aging both reduce moisture and
concentrate salt, pulling cheeses toward the lower-right.

### rec.hist — aging distribution

```
rec.hist in_set=rec:cheese_analysis attr=aging_months
```

Output:

```
  set:rec:cheese_analysis  ·  aging_months

   0  ┤ ████                        Halloumi
   3  ┤ ████                        Feta
   4  ┤ ████                        Brie
   6  ┤ ████                        Manchego
  12  ┤ ████████████████            Gruyère
  18  ┤ ████████████████████████    Pecorino
```

The histogram shows clearly that the dataset splits into two clusters: fresh-to-
short-aged cheeses (0–6 months) and long-aged cheeses (12–18 months). A dataset
with more entries would reveal whether this gap is structural or an artifact of
the small sample.

### tree — verifying ontology links

After adding rec attributes, verify that the structural layer is intact:

```
tree cheese:brie
```

Output:

```
  cheese:brie
  ├── [sys:is_a]    → cheese:soft
  └── [geo:origin]  → geo:france
```

The `tree` command shows only ontology links. The `aging_months`, `saltiness`,
and `creaminess` attributes do not appear here — they live in the rec layer and
are accessed through `rec.table` or `quadrant.plot`, not through graph
traversal. This separation is correct and expected.

---

## 1-6 Ontology Quality Workflow

After LLM-assisted attribute generation — or after annotating manually — run a
structured quality pass before treating the dataset as reliable.

### Stage 1 — Tabular outlier check

```
rec.table in_set=rec:fruit_analysis
```

Scan for extreme values that look implausible. A sweetness score of `0.00` for
a date is almost certainly wrong — dates are among the sweetest fruits known.
A score of `1.00` for lemon acidity is plausible (lemon juice pH is close to
2.0), but worth confirming.

Look for:
- Values at exactly 0.00 or 1.00 (often a default or clamp, not a real score)
- Missing values shown as `—` (the atom was not reached by `rec.set`)
- Values that contradict each other (e.g. olive scoring 0.80 sweetness while
  scoring 0.05 acidity — both numbers might be wrong if they originated from
  a confused LLM response about a different olive species)

### Stage 2 — Visual sanity check

```
quadrant.plot in_set=rec:fruit_analysis x=acidity y=sweetness \
    q1="tangy sweet" q2="mellow sweet" q3="bland" q4="tart"
```

Look at where each fruit lands. Ask:
- Does it feel intuitively right?
- Is any quadrant unexpectedly empty or unexpectedly crowded?
- Does any point appear isolated in a position that contradicts common knowledge?

If lemon scores both high acidity and high sweetness (top-right), something
went wrong. Lemon should be in the bottom-right (high acidity, low sweetness).

### Stage 3 — Structural link check

```
dive fruit:olive
```

Verify that the structural links — `sys:is_a`, `geo:origin`, emotional
associations — are correct independently of the rec attributes. A badly defined
ontology atom produces misleading views regardless of how carefully the numeric
scores are set.

### Stage 4 — Correcting values

`rec.set` replaces the existing attribute value when re-run with the same key
and attr:

```
rec.set key=fruit:olive attr=sweetness val=0.10
```

If you realise olive was incorrectly scored at `0.45`, re-running with `0.10`
corrects it immediately. No delete step is required. Run `rec.table` again to
confirm.

### Incremental enrichment strategy

Do not try to add all attributes in a single pass. A reliable workflow:

1. Add two core attributes (e.g. `sweetness`, `acidity`). Verify with
   `rec.table` and `quadrant.plot`.
2. Confirm the structural distribution makes sense.
3. Add a third attribute (e.g. `colour_depth` or `water_content`). Verify.
4. Continue adding attributes one at a time, checking the table after each
   addition.

Starting with two attributes keeps the plot readable and the verification
obvious. Each additional attribute is evaluated against an already-trusted base.

---

## 1-7 Exporting the Enriched Ontology

### What persists and what does not

The structural ontology written by `run fruit.ak` is durable
immediately — atoms and links are written to SQLite through the WriteQueue and
survive a session restart. Reloading the same .ak file after restart is safe
and idempotent.

The rec attributes written by `rec.set` and `rec.idx` are equally durable —
they are stored in the same SQLite database. They are not lost when the session
ends. What they lack is a source file you can version-control and
re-run from scratch.

If the database is lost or rebuilt, only your .ak file survives. The `rec.set`
commands exist only in your terminal history unless you take an explicit step to
preserve them.

### Best practice — keep a companion attributes script

Alongside `fruit.ak`, maintain a `fruit_attributes.sh` file:

```bash
#!/usr/bin/env bash
# fruit_attributes.sh
# Run after: akasha.py run fruit.ak

akasha.py rec.set key=fruit:fig         attr=sweetness val=0.88
akasha.py rec.set key=fruit:fig         attr=acidity   val=0.18
akasha.py rec.idx key=fruit:fig         sets=rec:fruit_analysis

akasha.py rec.set key=fruit:grape       attr=sweetness val=0.82
akasha.py rec.set key=fruit:grape       attr=acidity   val=0.35
akasha.py rec.idx key=fruit:grape       sets=rec:fruit_analysis

akasha.py rec.set key=fruit:date        attr=sweetness val=0.95
akasha.py rec.set key=fruit:date        attr=acidity   val=0.05
akasha.py rec.idx key=fruit:date        sets=rec:fruit_analysis

akasha.py rec.set key=fruit:pomegranate attr=sweetness val=0.65
akasha.py rec.set key=fruit:pomegranate attr=acidity   val=0.55
akasha.py rec.idx key=fruit:pomegranate sets=rec:fruit_analysis

akasha.py rec.set key=fruit:olive       attr=sweetness val=0.10
akasha.py rec.set key=fruit:olive       attr=acidity   val=0.22
akasha.py rec.idx key=fruit:olive       sets=rec:fruit_analysis

akasha.py rec.set key=fruit:lemon       attr=sweetness val=0.08
akasha.py rec.set key=fruit:lemon       attr=acidity   val=0.95
akasha.py rec.idx key=fruit:lemon       sets=rec:fruit_analysis

akasha.py rec.set key=fruit:orange      attr=sweetness val=0.72
akasha.py rec.set key=fruit:orange      attr=acidity   val=0.52
akasha.py rec.idx key=fruit:orange      sets=rec:fruit_analysis
```

This script is the single source of truth for the rec layer. When you correct
a score, update the script. When you add a new attribute, add lines to the
script. Because `rec.set` is idempotent, the script is safe to re-run on a
database that already has the attributes — it will update values in place
without creating duplicates.

### Commenting scores into the .ak file

For small datasets, embedding the attribute values as comments directly in the
.ak file is also a valid approach:

```
def "fruit:fig"  "Fig — Ficus carica; sweet, seedy Mediterranean fruit"
#   sweetness=0.88  acidity=0.18
ln fruit:fig  fruit  sys:is_a
```

The comments are ignored by the loader and do not enter the graph. They serve
as human-readable documentation of the scoring decisions and make it easy to
reconstruct the attribute script from the .ak file alone.

### When to use onto.dump

If you are starting from an existing database and want to reconstruct the
attribute script from what is already stored:

```
onto.dump atoms ns=fruit:
```

This gives you the atom list. You then run `rec.table in_set=rec:fruit_analysis`
to retrieve the current attribute values, and combine the two outputs to
reconstruct the script. This is useful when the script was lost but the
database survived.

---

## Next Steps

**Green Book, Chapter 2** extends this workflow to multi-namespace ontologies:
cheeses and fruits on the same quadrant plot, linking across domains with
`calc:contrasts_with` and `thesaurus:related`, and using `lens.flatten` to
compose cross-namespace analysis sets without modifying either source ontology.

**Red Book, Chapter 2** covers advanced concept model operations: `rec.filter`
for conditional sub-sets, `rec.rank` for sorted listings, and `rec.sum` for
aggregate statistics across large collections.

---

## Reference Summary

| Command | Purpose |
|---|---|
| `rec.set key=<k> attr=<a> val=<v>` | Attach a numeric attribute to an atom; replaces existing value |
| `rec.idx key=<k> sets=<s>` | Enrol an atom in an analysis set |
| `rec.table in_set=<s>` | Display all atoms in a set with their attributes as a table |
| `quadrant.plot in_set=<s> x=<a> y=<b>` | Scatter plot of two numeric attributes |
| `rec.hist in_set=<s> attr=<a>` | Distribution chart for one numeric attribute |
| `tree <key>` | Show ontology links for an atom (rec attributes not shown) |
| `dive <key>` | Expand an atom's neighbourhood (links, related words) |
| `lens src=<set>` | List all atoms in a set with descriptions and links |
| `run <file>` | Load a .ak file into the graph (submits a JCL job) |
| `onto.dump atoms ns=<ns>` | Export all atoms in a namespace |
| `set.add name=<s> id=<key>` | Add an atom to a named set (used in .ak files) |
