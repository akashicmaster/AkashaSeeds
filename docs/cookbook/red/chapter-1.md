# Red Book — Chapter 1: Concept Models

By the end of this chapter you will be able to store structured data in Akasha — fruits,
cheeses, quotes, or any collection of items with attributes — and query, visualise, and compare
them entirely from the CLI, without writing a single line of code.

> **How to read this chapter**
> This chapter is self-contained. All commands, concepts, and behaviours needed to follow the
> examples are explained within the text. No other documentation needs to be open.
> For deeper specification details, a reference list is provided at the very end.

---

## 1-1 What Is a Concept Model?

In everyday speech, a "model" usually means a fixed template: define the columns first, then
pour data into them. Akasha's concept models are different. A concept model in Akasha is a
**projection operator** — a lens that makes existing atoms visible in a particular shape.

The atoms themselves do not belong to any model. The same atom can be projected through any
number of models at the same time.

**A concrete example.** Suppose you have an atom whose content is `"orange"`. Through the
lens of a fruit model it becomes a fruit with sweetness and acidity scores. Through the lens of a
colour model it could become an entry in a palette, with hue and saturation. Through the lens of
a dietary model it might appear as a vitamin C source with a daily allowance percentage. The atom
`"orange"` never changes. What changes is the angle from which you look at it.

This is not a theoretical distinction — it has a practical consequence you will notice immediately:
if you later decide you want to add an attribute to an atom that already exists in Akasha
(perhaps an ontology concept, perhaps an atom you wrote months ago), you can do so without
touching the atom itself. You simply attach new structured attributes to it from outside.

### What This Means for You

- There is no "schema declaration" step before you can start entering data.
- You never have to choose between a graph atom and a table record — an atom can be both.
- Structured attributes are added incrementally and non-destructively: adding a `sweetness`
  score to an atom does not change its content or break any existing links.

The concept model is the *set of conventions* for how you attach and query those attributes.
In this chapter the model you will use most is the **`rec` (record) model** and the
**`table` model**.

---

## 1-2 The Three Roles: Operand, Operator, Agent

Akasha separates every action into three strictly independent roles.

| Role | What it is | Example |
|---|---|---|
| **Operand** | Data — carries no behaviour of its own | Atom `"fig"` with a `sweetness` attribute |
| **Operator** | Operation — defined independently of any particular piece of data | `rec.new`, `rec.sum`, `quadrant.plot` |
| **Agent** | The subject who applies an operator to an operand | You, typing at the CLI |

This separation is not just philosophical; it shapes how you think about the commands.
`rec.new` does not belong to any atom — it is an operator you apply whenever you choose.
The atom `"fig"` has no built-in method called `get_sweetness` — its `sweetness` attribute is
retrieved by an operator (`rec.get`) that you invoke separately.

Why does this matter? Because it means operators evolve independently of data. A new visualisation
command (`rec.heatmap`, for instance) can be added to Akasha without touching any existing atoms.
All your previous data becomes immediately compatible with the new operator, without a migration
step.

### Three Routes to a Rec Atom

Before entering the detailed commands, it helps to know that there are three ways to make an atom
visible through the record model.

| Route | What it does | When to use it |
|---|---|---|
| **Route A** — `rec.new` | Creates a new atom specifically as a record, with type and attributes set in a single step | Starting fresh, collecting new data |
| **Route B** — `rec.set` + `rec.idx` | Takes an atom that already exists in Akasha and attaches record attributes to it | Enriching an ontology atom, adding structure to an atom you wrote earlier |
| **Route C** — `lens.flatten` | Scans an entire set of atoms (from any source) and converts the result into a rec.set | Importing table data, snapshot-ing a graph traversal, converting a `tbl:` table into a rec.set |

All three routes produce rec atoms that behave identically for all subsequent operators. You can
freely mix atoms from all three routes in the same index set and query them together.

---

## 1-3 Route A — Creating Records with `rec.new`

### Your First Record

`rec.new` creates a new atom and attaches structured attributes to it in a single command.

```
rec.new type=fruit content="fig" sweetness=0.88 acidity=0.18
```

Breaking this down:

- `type=fruit` — the concept type. This is a human-readable label; Akasha automatically
  creates a set called `set:rec:fruit` and adds the new atom to it. You do not need to create
  the set manually.
- `content="fig"` — the text content of the atom. This is what you will see when the atom
  is displayed, and it is what the `content` column shows in tables and visualisations.
- `sweetness=0.88` and `acidity=0.18` — these are **inline attributes**. Any key=value pairs
  you write beyond `type` and `content` are stored immediately as structured attributes on
  the new atom.

### The Full Fruit Dataset

Enter these seven records one at a time:

```
rec.new type=fruit content="fig"          sweetness=0.88 acidity=0.18
rec.new type=fruit content="grape"        sweetness=0.82 acidity=0.35
rec.new type=fruit content="date"         sweetness=0.95 acidity=0.05
rec.new type=fruit content="pomegranate"  sweetness=0.65 acidity=0.55
rec.new type=fruit content="olive"        sweetness=0.10 acidity=0.22
rec.new type=fruit content="lemon"        sweetness=0.08 acidity=0.95
rec.new type=fruit content="orange"       sweetness=0.72 acidity=0.52
```

After running all seven commands, `set:rec:fruit` will contain seven atoms.

### Auto-Indexing: How `type=` Works

When you write `type=fruit`, Akasha does the following automatically:

1. Computes the content hash of the text `"fig"` — this is the atom's key.
2. Attaches the type label to the atom's metadata (`rec_type = "fruit"`).
3. Creates an `instance_of` link from the atom to the `fruit` concept atom (if `fruit` exists in
   your ontology; otherwise the link points to the raw text).
4. Adds the atom's key to the set `set:rec:fruit`.

You never see steps 2–4 happen because they are performed invisibly as part of `rec.new`. But
they are the foundation for every query you will run later: `rec.ls type=fruit` works because
every `rec.new type=fruit` call has already registered the atom in that set.

### Idempotency: Running the Same Command Twice Is Safe

Akasha uses **content addressing**: the key of an atom is derived from its text content. If you
run:

```
rec.new type=fruit content="fig" sweetness=0.88 acidity=0.18
```

twice, the following happens:

- The first run creates the atom and attaches the attributes.
- The second run resolves to the *same* atom (same content, same key), and **upserts** the
  attributes — existing links are refreshed but not duplicated, and the set membership is
  already present, so it is not added twice.

The end state is identical whether you ran the command once or ten times. You cannot accidentally
create duplicate entries by re-entering a command.

### Adding More Attributes Later

Inline attributes in `rec.new` are convenient when you have all the data ready. But you can also
add attributes later using `rec.set` (covered in Section 1-4). For `rec.new`, any key=value
pair that is not `type` or `content` is treated as an inline attribute. There is no fixed list of
permitted attribute names — you invent the names yourself.

---

## 1-4 Route B — Enriching Existing Atoms with `rec.set` and `rec.idx`

### What Route B Is For

Not everything you want to analyse with rec operators starts as a `rec.new` command. You may
have atoms written earlier with `w`, atoms imported from Wikipedia, or atoms that already exist
in the Akasha ontology as named concepts. Route B lets you attach structured attributes to any
of these atoms without disturbing them.

### `rec.set` — Adding or Replacing an Attribute

```
rec.set key=<atom_key_or_alias> attr=<attribute_name> val=<value>
```

Suppose the atom `concept:olive` already exists in the Akasha ontology. You want to track its
sweetness and acidity for analysis alongside your `rec.new` fruit atoms.

```
rec.set key=concept:olive   attr=sweetness val=0.10
rec.set key=concept:olive   attr=acidity   val=0.22
```

These two commands add a `rec:sweetness` link and a `rec:acidity` link to the existing atom.
The atom's content (`"The olive is a species..."` or whatever its ontology text is) is **not
touched**. Its existing links to other ontology atoms are **not affected**. Its meaning in the
knowledge graph is **not changed**. Only two new attribute links are added.

This is a fundamental design rule: `rec.set` always adds or replaces a single attribute link.
It never modifies an atom's content or removes its existing connections.

### `rec.idx` — Adding an Atom to Index Sets

After attaching attributes, you need to tell Akasha which sets this atom belongs to:

```
rec.idx key=<atom_key_or_alias> sets=<set_name>[,<set_name>,...]
```

To include `concept:olive` in the fruit query results:

```
rec.idx key=concept:olive sets=rec:fruit
```

Now `concept:olive` is a member of `set:rec:fruit` and will appear in `rec.ls type=fruit` and
`rec.table type=fruit` alongside the atoms you created with `rec.new`.

You can add an atom to multiple sets in a single `rec.idx` call:

```
rec.idx key=concept:olive sets=rec:fruit,mediterranean_ingredients,low_sugar
```

The bare names `rec:fruit`, `mediterranean_ingredients`, and `low_sugar` are automatically
expanded to `set:rec:fruit`, `set:mediterranean_ingredients`, and `set:low_sugar`. The `set:`
prefix is optional — Akasha adds it if it is missing.

### The Cheese Dataset Using `rec.new`

For the cheese examples in this chapter, use `rec.new` rather than Route B:

```
rec.new type=cheese content="Brie"      origin="France"      texture="soft"      aged=4
rec.new type=cheese content="Gruyère"   origin="Switzerland" texture="hard"      aged=12
rec.new type=cheese content="Feta"      origin="Greece"      texture="crumbly"   aged=3
rec.new type=cheese content="Manchego"  origin="Spain"       texture="firm"      aged=6
rec.new type=cheese content="Halloumi"  origin="Cyprus"      texture="semi-hard" aged=0
rec.new type=cheese content="Pecorino"  origin="Italy"       texture="hard"      aged=18
```

The `aged` attribute stores the number of months of ageing. `Halloumi` is a fresh cheese sold
immediately after making, so its value is `0`.

---

## 1-5 Querying Records

### `rec.get` — Retrieve a Single Record with All Its Attributes

```
rec.get key=<atom_key_or_alias>
```

After you have entered the fruit records, retrieve one to confirm it was stored correctly:

```
rec.get key=fig
```

If `fig` is an alias for the atom, this works directly. If you do not have the alias, use the
atom's hash key (the short string shown after `rec.new` returns).

Typical output:

```
key:       a3f7c2...
content:   fig
type:      fruit
sweetness: 0.88
acidity:   0.18
```

The `type` field reflects the `rec_type` from the atom's metadata. The remaining fields are
the `rec:` attribute links. Attributes are returned in the order they were added.

### `rec.ls` — List Records by Type or Set

`rec.ls` lists the atoms registered under a type or in a specific set. It shows a short preview
of each atom's content, not the full attribute list.

**List by type:**

```
rec.ls type=fruit
```

This reads `set:rec:fruit` and returns all its members. The output is a numbered list of content
previews:

```
7 records  (type: fruit)
  1.  fig
  2.  grape
  3.  date
  4.  pomegranate
  5.  olive
  6.  lemon
  7.  orange
```

**List by set:**

```
rec.ls in_set=mediterranean_ingredients
```

This reads whatever you have added to `set:mediterranean_ingredients`. The `set:` prefix is
optional — `in_set=mediterranean_ingredients` and `in_set=set:mediterranean_ingredients` are
equivalent.

**Combined filter:**

```
rec.ls type=fruit in_set=low_sugar
```

When both `type=` and `in_set=` are given, the result is the **intersection** — only atoms that
are members of both `set:rec:fruit` and `set:low_sugar`.

### `rec.sum` — Sum a Numeric Attribute Across Records

```
rec.sum attr=<attribute_name> type=<type>
rec.sum attr=<attribute_name> in_set=<set>
```

To compute the total sweetness across all fruits:

```
rec.sum attr=sweetness type=fruit
```

Output:

```
attr:    sweetness
sum:     4.20
count:   7
skipped: 0
type:    fruit
```

`count` is the number of atoms that had a numeric value for `sweetness`. `skipped` counts atoms
whose `sweetness` value was present but could not be parsed as a number. Atoms with no
`sweetness` attribute are silently excluded from both counts.

To compute the total ageing months across cheeses:

```
rec.sum attr=aged type=cheese
```

```
attr:    aged
sum:     43
count:   6
skipped: 0
type:    cheese
```

43 months is the combined ageing across all six cheeses. A single `rec.sum` call covers the
entire set in one step.

### `rec.table` — Display Records as a Formatted Table

```
rec.table type=<type>
rec.table in_set=<set>
```

`rec.table` reads all the atoms in the set, collects all the attribute names found across them
(called **column discovery**), and renders the result as an aligned table.

**There is no schema declaration step.** Akasha scans the actual `rec:` links present in the
atoms and derives the column list automatically. If some atoms have a `sweetness` attribute and
others do not, the table still renders correctly — missing values show as empty cells.

```
rec.table type=fruit
```

Typical output:

```
  set:rec:fruit
  ─────────────────────────────────────────────────────
  content       sweetness   acidity
  ─────────────────────────────────────────────────────
  fig           0.88        0.18
  grape         0.82        0.35
  date          0.95        0.05
  pomegranate   0.65        0.55
  olive         0.10        0.22
  lemon         0.08        0.95
  orange        0.72        0.52
  ─────────────────────────────────────────────────────
  7 rows
```

Numeric columns are right-aligned automatically. Text columns are left-aligned. Column widths
are derived from the data.

To add a row limit:

```
rec.table type=fruit limit=3
```

---

## 1-6 Visualising Records

### `rec.hist` — Histogram of a Numeric Attribute

A histogram divides the range of a numeric attribute into bins and shows how many atoms fall
into each bin. It renders as a horizontal bar chart in the terminal.

```
rec.hist attr=<attribute_name> type=<type> [bins=10]
```

To visualise the distribution of ageing months across the cheese collection:

```
rec.hist attr=aged type=cheese
```

The range runs from 0 (Halloumi) to 18 (Pecorino). With the default of 10 bins, each bin
spans approximately 1.8 months. Because the six cheeses are spread across the full range,
most bins will have one entry and some will be empty.

To use fewer bins and see a coarser picture:

```
rec.hist attr=aged type=cheese bins=4
```

With 4 bins the distribution becomes: fresh (0–4 months), young (4–9), aged (9–13), old (13–18).
This shows at a glance that the collection skews toward extremes — very fresh and very long-aged.

For the fruit dataset:

```
rec.hist attr=sweetness type=fruit
```

The range runs from 0.08 (lemon) to 0.95 (date). You will see that most fruits cluster at the
high end, with lemon and olive as outliers at the low end.

### `rec.heatmap` — Two-Dimensional Distribution

`rec.heatmap` bins two numeric attributes simultaneously and shows intensity as a filled grid in
the terminal. Cells with more atoms are darker; empty cells are blank.

```
rec.heatmap x=<attr> y=<attr> type=<type> [x_bins=8] [y_bins=6]
```

To see how acidity and sweetness co-vary across the fruit dataset:

```
rec.heatmap x=acidity y=sweetness type=fruit
```

The X axis (horizontal) shows acidity from low to high. The Y axis (vertical) shows sweetness
from high (top) to low (bottom). The pattern that emerges: most fruits cluster in the upper-left
(low acidity, high sweetness — fig, grape, date), one outlier sits in the lower-right (high
acidity, low sweetness — lemon), and orange and pomegranate occupy the middle-right.

You can also plot a third attribute as the intensity of each cell, instead of frequency count:

```
rec.heatmap x=acidity y=sweetness type=fruit value=sweetness x_bins=4 y_bins=4
```

Here the cell colour represents the average `sweetness` value in that bin rather than the count
of atoms. This adds a third dimension of information to the same two-axis grid.

---

## 1-7 The Table Model

The `rec.*` model is schema-free: you invent attribute names as you go, and different atoms in
the same set can have different sets of attributes. The **`table` model** (accessible via the
`table.*` commands) is the opposite: you declare columns up front, and rows must conform to
those columns. This makes tables suitable when you need CSV round-trip compatibility, strict
column ordering, or a predictable structure for sharing with others.

Every row in a `table` is also a rec-compatible atom. This means `rec.get` and `rec.set` work
on table rows transparently. You can create a table for structured entry, then use `rec.sum` or
`rec.table` to query it, or use `lens` to convert its rows into a rec.set for further analysis.

### `table.new` — Create a Table

```
table.new name=<name> cols="<col1>:<type>,<col2>:<type>,..."
```

Column types available: `text` (default), `int`, `float`, `bool`, `date`.

Create a table for the philosopher quotes dataset:

```
table.new name=quotes cols="author:text,origin:text,quote_text:text,century:int"
```

This creates a table atom with the alias `tbl:quotes`. Four columns are declared:
`author`, `origin`, `quote_text`, and `century`.

Column declarations are stored in the atom's metadata and used by `table.view` for column
ordering. They are **not enforced at write time** — values are always stored as text
atoms internally, regardless of the declared type. The type annotation is used for display
formatting (numeric types right-align) and CSV export ordering.

### `table.col.add` — Add a Column After Creation

If you need to add a column to an existing table:

```
table.col.add table=quotes name=era type=text
```

This adds an `era` column to the `quotes` table. Existing rows will have an empty value for
this column until you update them with `rec.set`.

### `table.row.add` — Insert a Row

```
table.row.add table=<name> col1=val1 col2=val2 ...
```

Insert the five philosopher quotes:

```
table.row.add table=quotes \
    author="Aristotle" \
    origin="Greece" \
    century=-4 \
    quote_text="We are what we repeatedly do. Excellence, then, is not an act, but a habit."

table.row.add table=quotes \
    author="Marcus Aurelius" \
    origin="Rome" \
    century=2 \
    quote_text="You have power over your mind, not outside events. Realize this, and you will find strength."

table.row.add table=quotes \
    author="Rumi" \
    origin="Persia" \
    century=13 \
    quote_text="Out beyond ideas of wrongdoing and rightdoing, there is a field. I'll meet you there."

table.row.add table=quotes \
    author="Ibn Battuta" \
    origin="Morocco" \
    century=14 \
    quote_text="Traveling — it leaves you speechless, then turns you into a storyteller."

table.row.add table=quotes \
    author="Heraclitus" \
    origin="Greece" \
    century=-5 \
    quote_text="No man ever steps in the same river twice, for it's not the same river and he's not the same man."
```

(The backslash `\` breaks a long command across multiple lines for readability. If your
terminal does not support line continuation, type each row on a single line.)

Each `table.row.add` call creates a new atom and links it to the table via a `tbl:row` link.
The row atom is also added to the set `tbl:quotes:rows` automatically.

### `table.view` — Display the Table

```
table.view quotes
```

or equivalently:

```
table.view table=quotes
```

Output:

```
  tbl:quotes
  ─────────────────────────────────────────────────────────────────────────────────
  author           origin    century  quote_text
  ─────────────────────────────────────────────────────────────────────────────────
  Aristotle        Greece      -4     We are what we repeatedly do. Excellence...
  Marcus Aurelius  Rome         2     You have power over your mind, not outside...
  Rumi             Persia      13     Out beyond ideas of wrongdoing and rightdoin...
  Ibn Battuta      Morocco     14     Traveling — it leaves you speechless, then...
  Heraclitus       Greece      -5     No man ever steps in the same river twice...
  ─────────────────────────────────────────────────────────────────────────────────
  5 rows
```

Columns appear in declaration order. The `century` column is right-aligned because it was
declared as `int`. Long text is truncated to fit the terminal width. To see a specific row in
full, use `table.row.get`.

### `table.export` — Export as CSV

```
table.export table=quotes
```

This prints the table contents as RFC 4180 CSV with a header row:

```
author,origin,century,quote_text
Aristotle,Greece,-4,"We are what we repeatedly do. Excellence, then, is not an act, but a habit."
Marcus Aurelius,Rome,2,"You have power over your mind, not outside events. Realize this, and you will find strength."
...
```

Columns appear in declaration order. Values containing commas or quotation marks are properly
quoted.

### `table.ls` — List All Tables

```
table.ls
```

Returns a list of all table atoms available in the current session, along with their row counts
and creation timestamps.

---

## 1-8 Scanning with `lens`

The `lens` family of commands bridges two worlds: the unstructured graph on one side, and the
structured rec/table models on the other. A lens scans any named source, profiles what it finds,
and offers you options for what to do with the result.

### Scanning a Set with `lens src=`

```
lens src=<source>
```

Point `lens` at any source. The source can be a rec.set, a table, a named set, or an atom key.

```
lens src=set:rec:fruit
```

`lens` scans all the atoms in `set:rec:fruit`, collects the attribute names it finds across all
of them (`sweetness`, `acidity`, `content`), measures how consistently each attribute is present
(its **coverage**), and infers the probable data type of each attribute (text, float, int, etc.).

The output shows a profile summary and a list of numbered **candidates** — concept model
projections that could accept this data. For a rec.set with numeric attributes, you will typically
see the `table` model listed as a candidate (which would create a structured table from the data)
and possibly `quadrant` (for a scatter plot).

Scanning a structured table:

```
lens src=tbl:quotes
```

This scans the rows of the `quotes` table via its `ExportableMixin` — `lens` recognises that
`tbl:quotes` refers to a table atom and reads its rows directly, rather than reading the table
atom's own links.

### Tree Scanning with `follow=` and `depth=`

```
lens src=<atom_key_or_alias> follow=<relation_type> depth=<N>
```

Instead of scanning a flat set, this form performs a **breadth-first traversal** starting from
a single atom and following a particular link type outward.

Suppose you have an ontology atom for `concept:cheese` with `sys:is_a` links pointing toward
specific cheese atoms. You can scan the entire subtree:

```
lens src=concept:cheese follow=sys:is_a depth=2
```

This starts at `concept:cheese`, follows all outgoing `sys:is_a` links to depth 2, and collects
all the atoms encountered. If Halloumi, Feta, and Brie each have `sys:is_a → concept:cheese`,
they will all be collected.

The `depth` parameter controls how many steps outward from the root atom the traversal goes.
`depth=1` collects only direct neighbours. `depth=3` goes three hops out. The default is 2.

### `lens.flatten` — Route C to a Rec Set

After running any `lens` scan, you can persist the scanned atoms as new rec atoms in a named set.

```
lens.flatten into=<set_name>
```

This is Route C: it takes every atom collected by the most recent `lens` scan, creates a new
rec atom for each one (carrying the same attributes), and adds all of them to `set:<set_name>`.

**The original atoms are never modified.** `lens.flatten` creates new atoms linked back to the
originals via a `ctx:source` link. The new atoms are full citizens of the rec model — they
appear in `rec.ls`, `rec.table`, `rec.hist`, and so on.

**Example workflow:** Scan a table, flatten into a rec.set, then use rec analysis tools.

```
lens src=tbl:quotes
lens.flatten into=quotes_rec
rec.table in_set=quotes_rec
rec.ls in_set=quotes_rec
```

Or scan an ontology subtree and flatten it for analysis:

```
lens src=concept:cheese follow=sys:is_a depth=1
lens.flatten into=cheese_scan
rec.table in_set=cheese_scan
```

### `lens.cast` — Project into a Concept Model

`lens.cast` is an alternative to `lens.flatten`. Instead of creating raw rec atoms, it projects
the scanned data directly into a specific concept model — for example, creating a structured
`table` with automatically detected columns.

```
lens.cast signpost=1 into=<name>
```

After `lens src=set:rec:fruit`, if the `table` model appears as candidate 1 in the output,
then:

```
lens.cast signpost=1 into=fruit_table
```

This creates a new `table` atom named `fruit_table` with columns auto-derived from the rec
attributes found during the scan (`sweetness`, `acidity`), and populates it with one row per
fruit atom. Column types are inferred automatically.

You can also specify a model directly by name:

```
lens.cast model=table into=fruit_table
```

Column and axis discovery is entirely automatic at cast time — no schema declaration is needed
before running `lens.cast`.

---

## 1-9 Visual Analysis and Set Operations

### `quadrant.plot` — Four-Quadrant Scatter Plot

`quadrant.plot` takes any rec.set and projects two of its numeric attributes onto a
four-quadrant ASCII scatter plot drawn in the terminal. No browser is required.

```
quadrant.plot in_set=<set> x=<attr> y=<attr> [q1=...] [q2=...] [q3=...] [q4=...] [x_mid=<float>] [y_mid=<float>]
```

Plot the fruits by acidity (X axis) and sweetness (Y axis):

```
quadrant.plot in_set=set:rec:fruit x=acidity y=sweetness \
    q1="tart-sweet" q2="mild-sweet" q3="mild-lean" q4="tart-lean"
```

The four corners are labelled as you specify:
- `q1` — top-right (high X, high Y): pomegranate and orange
- `q2` — top-left (low X, high Y): fig, grape, date
- `q3` — bottom-left (low X, low Y): olive
- `q4` — bottom-right (high X, low Y): lemon

The plot's dividing lines are placed at the **data midpoint** by default. With the fruit dataset,
the acidity midpoint is around 0.52 and the sweetness midpoint is around 0.52. This means the
lines fall near the data's natural centre.

To fix the midpoint at a specific value — useful when you want a stable baseline across sessions:

```
quadrant.plot in_set=set:rec:fruit x=acidity y=sweetness \
    x_mid=0.50 y_mid=0.50 \
    q1="tart-sweet" q2="mild-sweet" q3="mild-lean" q4="tart-lean"
```

With midpoints fixed at 0.50, olive (acidity=0.22, sweetness=0.10) sits in the lower-left
(mild-lean), and lemon (acidity=0.95, sweetness=0.08) sits in the lower-right (tart-lean).

When multiple fruits fall on the same grid row, the plot substitutes numbers for dots and
appends a legend below. This is normal with small datasets — the 48-column grid resolves
fine positional differences.

**Parameter reference:**

| Parameter | Required | Default | Description |
|---|---|---|---|
| `in_set=` | yes | — | The rec.set to read (the `set:` prefix is optional) |
| `x=` | yes | — | Attribute name for the horizontal axis |
| `y=` | yes | — | Attribute name for the vertical axis |
| `label=` | no | `content` | Attribute to use as point label |
| `x_mid=` | no | data midpoint | Horizontal dividing line |
| `y_mid=` | no | data midpoint | Vertical dividing line |
| `x_label=` | no | value of `x` | Display name shown on the axis |
| `y_label=` | no | value of `y` | Display name shown on the axis |
| `q1=` | no | — | Label for top-right quadrant |
| `q2=` | no | — | Label for top-left quadrant |
| `q3=` | no | — | Label for bottom-left quadrant |
| `q4=` | no | — | Label for bottom-right quadrant |

Atoms whose `x` or `y` attribute is absent or non-numeric are silently skipped. All other atoms
in the set are plotted.

### `tree` — Link-Traversal Tree

```
tree <alias|key|set:name|ns:prefix> [depth=2] [follow=<rel>] [format=rich|ascii]
```

`tree` walks outgoing links from a starting point and renders the result as a tree. It is
distinct from `lens`'s tree scan: `tree` is for visual exploration of the graph structure;
`lens` is for collecting atoms into a set for further analysis.

To see all atoms in the fruit rec.set and their immediate links:

```
tree set:rec:fruit depth=1
```

This shows each of the seven fruit atoms as a top-level node, with one level of their outgoing
links as children. You will see the `instance_of` link (pointing to the `fruit` concept atom),
the `rec:sweetness` link (pointing to the value atom `"0.88"`, etc.), and the `rec:acidity`
link.

To follow a specific link type from a single root atom:

```
tree concept:cheese follow=sys:is_a depth=2 format=ascii
```

This produces a plain-text tree (no colour, no Unicode box-drawing) starting at `concept:cheese`
and following only `sys:is_a` links outward to depth 2. Useful if you want to copy the output
into a document or a message.

**Target types:**

| Target form | What is shown |
|---|---|
| `alias` or `hash_key` | That single atom's outgoing link tree |
| `set:name` | Each set member as a top-level node, with sub-trees |
| `ns:prefix` | All atoms in a namespace as top-level nodes |

`depth` runs from 1 to 5 (capped). Output is limited to 20 children per node and 150 total
nodes to keep the display manageable.

### `cross` — Weighted Set Intersection

`cross` finds atoms that appear in more than one named rec.set and ranks them by how many sets
they appear in.

```
cross <concept1> <concept2> [<concept3> ...]
```

The arguments to `cross` are concept names or set paths. To find atoms that appear in both
`set:rec:fruit` and a set called `set:mediterranean_ingredients`:

```
cross set:rec:fruit set:mediterranean_ingredients
```

The output lists every atom that belongs to at least one of the named sets, ordered by a
**weight** score: atoms present in all named sets receive weight 1.0; atoms present in only
some sets receive a proportionally lower weight. This lets you see true intersection (weight
1.0) and partial overlap at a glance.

For a concrete scenario: if you have added the olive to both `set:rec:fruit` (via `rec.new` or
`rec.idx`) and `set:mediterranean_ingredients` (via `s.add` or `rec.idx`), it will appear in
the results with weight 1.0 — appearing in both. Lemon, present only in `set:rec:fruit`, will
appear with weight 0.5.

**How to compare the fruit and cheese datasets directly:**

```
cross set:rec:fruit set:rec:cheese
```

In the example datasets used throughout this chapter, no atoms are shared between the two sets,
so the result will be empty. But if you were to add an atom like `"fig and cheese pairing"` to
both sets with `rec.idx`, it would appear with weight 1.0.

`cross` is most useful when you have built several overlapping sets — perhaps one set per
traveller, or one set per century, or one set per origin country — and want to find the atoms
that appear in all or most of them.

---

## Next Steps

This chapter covered the full rec/table/lens/quadrant workflow from a non-programmer
perspective. The next chapters in the Red Book continue without requiring any of the earlier
chapters as prerequisites — each chapter is self-contained.

**Red Book Chapter 2** covers notes and longer-form text: writing multi-section documents,
linking them into the knowledge graph, and reading them back.

**Red Book Chapter 3** covers the survey and dialogue models: structured question-and-answer
data, batch imports, and comparison across respondents.

---

## References

The following documents provide specification-level detail for the topics in this chapter.
They are listed for reference only — nothing in them is required to complete the examples above.

| Document | Contents |
|---|---|
| `docs/users/cli-quick-reference.md` | Complete command reference for `rec.*`, `table.*`, `lens.*`, `quadrant.*`, and `tree` |
| `docs/cookbook/quadrant-scatter.md` | Detailed walkthrough of `quadrant.plot` with additional scatter plot examples |
| `lib/akasha/concepts/rec.py` | Source implementation of RecConcept and all `rec.*` operators |
| `lib/akasha/concepts/table.py` | Source implementation of TableConcept and all `table.*` operators |
| `lib/akasha/concepts/lens.py` | Source implementation of LensConcept, SourceScanner, and `lens.*` operators |
| `lib/akasha/concepts/quadrant.py` | Source implementation of QuadrantConcept and `quadrant.plot` |
| `docs/concept-model/concept-model-spec.md` | Full specification of the concept model architecture (BaseConcept, dispatch, IAM) |
