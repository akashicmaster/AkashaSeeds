# Green Book — Chapter 0: Building Knowledge in Bulk with .ak Files

> **Before this chapter:** read Red Book, Chapter 0 for the CLI commands.
> This chapter covers creating knowledge in bulk using .ak batch files.

By the end of this chapter you will be able to write a complete `.ak` file,
load it into Akasha, and verify that every atom, link, and alias was created correctly.

> **How to read the Green Book**
> Each chapter is self-contained. All concepts needed to work through the examples
> are explained within the chapter. For specification details, a reference list
> appears at the end. No reference links appear inline.

---

## 0-1 Why .ak Files?

The CLI's interactive commands — `w`, `def`, `ln`, `al`, `s.add` — are the right tool
for exploration: writing a note, linking two ideas, following a trail of associations.
But suppose you want to load a hundred related concepts at once, or hand a structured
vocabulary to a colleague, or version-control a growing ontology. Interactive commands
become awkward quickly.

The `.ak` format was designed exactly for this situation. It is a plain text file that
Akasha's batch loader can execute in one shot. Everything you would type at the prompt —
definitions, links, aliases, set memberships — is written out once, stored in a file,
and submitted with a single command.

**Three properties make `.ak` files especially useful:**

**Reproducible.** Running the same `.ak` file twice produces exactly the same result
as running it once. All four commands are idempotent — defining an atom that already
exists silently unifies rather than duplicating; creating a link that already exists
is a no-op. This means you can re-run a file freely when you add new items to it.

**Version-controllable.** A `.ak` file is plain text. It diffs cleanly, can be
committed to git, and can be reviewed line by line before loading.

**LLM-generatable.** The vocabulary is deliberately minimal: four commands with
straightforward syntax. A language model asked to produce a `.ak` file from a
description or source text has very little to learn and very little to get wrong.
This is how Akasha's ontology was built, and how most large ontology additions
will continue to be made.

---

## 0-2 The Four Commands

A `.ak` file contains only four commands. Comments (lines beginning with `#`) are
ignored. Blank lines are allowed anywhere.

---

### `def` — Define an Atom

```
def "namespace:key" "Human-readable description text"
```

`def` writes an Atom and registers its first alias in one step.
The first argument becomes both the atom's identifier and its primary alias.
The second argument is the atom's content — the text that will be stored and indexed.

```
def "fruit:fig" "The fig (Ficus carica), one of the earliest cultivated fruits in the
Mediterranean basin. Grown in the Levant and North Africa for at least 11,000 years."

def "concept:flux" "The philosophical idea that all things are in constant change and motion."

def "person:heraclitus" "Greek philosopher, c. 535–475 BCE. Known for the doctrine of
flux and the unity of opposites. Associated with the river metaphor: you cannot step
into the same river twice."
```

`def` is idempotent. If the exact content already exists in Akasha, no new atom is
created — the existing atom is silently reused. This is content-addressing at work:
two identical texts produce the same hash, so the system recognises them as one atom.

---

### `ln` — Create a Typed Link

```
ln src_key dst_key rel_label
```

`ln` creates a directed link from one atom to another with a relation type.
The source and destination are written as keys (the first argument of their `def` line).
The relation type can be any string.

```
# Using built-in system relation types
ln fruit:fig fruit:genus sys:is_a
ln fruit:fig place:levant @originates_in

# Using emotional relation types already in the base ontology
ln fruit:fig emo:nostalgia emo:evokes
ln fruit:pomegranate emo:awe emo:evokes

# Linking philosophers to their core concepts
ln person:heraclitus concept:flux sys:associated_with
ln person:heraclitus concept:flux @articulated
```

The most commonly used relation types in ontology work are:

| Relation | Meaning |
|---|---|
| `sys:is_a` | Classification — "is a type of" |
| `sys:part_of` | Composition — "is a component of" |
| `sys:associated_with` | Loose association — "is somehow connected to" |
| `sys:causes` | Causation — "leads to" |
| `@originates_in` | Geographic or cultural origin |
| `@articulated` | "This person stated or developed this idea" |
| `emo:evokes` | "This atom is associated with this emotional tone" |

Akasha does not enforce any particular relation label. Any string you write becomes
a valid relation type, available for traversal and filtering. The built-in `sys:` and
`emo:` prefixes carry defined semantics; your own labels (like `originates_in` or
`aged_for`) are equally valid and simply name a relationship you have chosen to record.

`ln` is idempotent. Creating the same link twice does not create a duplicate.

---

### `al` — Register an Alias

```
al atom_key alias_name
```

`al` gives a shorter or more convenient name to an atom that was already defined.
The atom's primary alias was created by `def`; `al` adds secondary aliases.

```
al fruit:fig fig
al fruit:grape grape
al person:heraclitus heraclitus
al person:aristotle aristotle
```

After the file loads, any of these names can be used at the CLI (`r fig`, `dive heraclitus`).

Alias assignment follows a first-wins policy. If `fig` is already assigned to a different
atom (perhaps one written in a previous session), the second attempt does not reassign
the alias — instead, a `specializes` link is created from the new atom toward the
existing one, and the name is not moved. This protects established names from being
silently redirected. To deliberately reassign an alias, remove it first at the CLI:
`al.rm fig`, then re-register it.

A single atom may carry any number of aliases. Registering `fig`, `figs`, and
`ficus_carica` against the same atom is valid.

---

### `set.add` — Add an Atom to a Named Set

```
set.add name="set:name:here" id="atom:key:here"
```

`set.add` places an atom into a named collection. Sets are the primary way to
group atoms for later query, export, or batch processing.

```
set.add name="set:fruits:mediterranean" id="fruit:fig"
set.add name="set:fruits:mediterranean" id="fruit:grape"
set.add name="set:fruits:mediterranean" id="fruit:pomegranate"
```

After loading, `s.ls set:fruits:mediterranean` at the CLI will return all three atoms.
You can run `rec.table in_set=set:fruits:mediterranean` to display them as a formatted table.

Set membership is idempotent — adding the same atom to the same set twice creates
no duplicate entry.

---

### `#` — Comment

Any line beginning with `#` is ignored by the loader. Use comments to label
sections of a file, record authorship or dates, or note why a particular link
was made.

```
# Mediterranean fruits — Green Book Chapter 0 example
# Last updated: 2026-07-04
# All place: atoms in this file are self-contained; do not depend on geo.ak
```

---

## 0-3 Your First .ak File: Mediterranean Fruits

The file below defines seven ancient Mediterranean fruits — fig, grape, date, pomegranate,
olive, lemon, and orange. It is complete and self-contained: every atom referenced inside
the file is defined within the file. Atoms from the base ontology (such as `emo:nostalgia`,
`emo:awe`) are referenced without being redefined, because they are loaded automatically
at startup.

Save this file as `mediterranean_fruits.ak` in your working directory.

```
# mediterranean_fruits.ak
# Seven ancient Mediterranean fruits: atoms, links, aliases, set membership
# Self-contained: all place: and fruit: atoms are defined here.
# Depends on: emo: atoms from base ontology (loaded at startup)

# ── Classification hub ────────────────────────────────────────────────────────

def "fruit:genus" "The genus-level category for fruits: the edible, seed-bearing
products of flowering plants. Used as the is_a hub for all fruit atoms in this file."

al fruit:genus fruit_category

# ── Place atoms (self-contained — do not rely on geo.ak) ─────────────────────

def "place:mediterranean_basin" "The lands surrounding the Mediterranean Sea. A cradle
of agriculture, trade, and civilisation. Shared climate: hot dry summers, mild wet winters."

def "place:levant" "The eastern Mediterranean coastlands — modern Israel, Palestine,
Lebanon, and Syria. Among the earliest sites of settled agriculture, c. 10,000 BCE."

def "place:middle_east" "The broader region spanning the Fertile Crescent, the Arabian
Peninsula, and the Persian plateau. Home to some of the world's oldest cultivation traditions."

def "place:persia" "The Iranian plateau and surrounding regions. Historical centre of
the Persian Empire. Key origin zone for pomegranates, pistachios, and citrus."

def "place:north_africa" "The African coast of the Mediterranean, including Egypt,
Libya, Tunisia, Algeria, and Morocco. Major olive and date cultivation zone."

def "place:southeast_asia" "The tropical and subtropical regions of Asia east of India.
Origin zone for citrus fruits before their westward spread to the Mediterranean."

al place:mediterranean_basin mediterranean_basin
al place:levant levant
al place:middle_east middle_east
al place:persia persia
al place:north_africa north_africa

# ── Fruit atoms ───────────────────────────────────────────────────────────────

def "fruit:fig" "The fig (Ficus carica), one of the earliest cultivated fruits in the
world. Native to the Levant and western Asia. Sweet, honeyed interior with edible skin.
Dried figs were a staple food of ancient Mediterranean civilisations. Mentioned in the
Epic of Gilgamesh and the Bible."

def "fruit:grape" "The grape (Vitis vinifera), cultivated for at least 8,000 years
in the South Caucasus and Near East. Foundation of winemaking across Mediterranean
cultures. Sacred to Dionysus in Greek religion and to Bacchus in Roman religion.
Eaten fresh, dried as raisins, or fermented."

def "fruit:date" "The date (Phoenix dactylifera), fruit of the date palm. Native to
the Persian Gulf and North Africa. One of the most calorie-dense natural fruits.
A dietary staple of desert communities for millennia. The date palm is a symbol of
life in arid regions."

def "fruit:pomegranate" "The pomegranate (Punica granatum), native to Persia and the
Himalayan foothills. Deep red, many-seeded fruit with a leathery rind. Symbol of
fertility and the underworld in Greek mythology (Persephone's fruit). Widely used in
Persian and Levantine cuisine."

def "fruit:olive" "The olive (Olea europaea), defining fruit of Mediterranean civilisation.
Cultivated for at least 7,000 years. Produces olive oil — the primary cooking fat,
lamp fuel, and cosmetic of the ancient world. Sacred to Athena in Greek mythology."

def "fruit:lemon" "The lemon (Citrus limon), a hybrid of the citron and the bitter orange.
Originated in South Asia, reached the Mediterranean via Persia and North Africa around
the 10th century CE. Prized for its bright acidity in both cooking and medicine."

def "fruit:orange" "The sweet orange (Citrus sinensis), originating in South and East Asia.
Reached the Mediterranean through trade routes in the 15th century CE. The sweet orange
was a luxury fruit in early modern Europe. Now the most widely cultivated citrus."

# ── Aliases ───────────────────────────────────────────────────────────────────

al fruit:fig fig
al fruit:grape grape
al fruit:date date
al fruit:pomegranate pomegranate
al fruit:olive olive
al fruit:lemon lemon
al fruit:orange orange

# ── Classification links ──────────────────────────────────────────────────────

ln fruit:fig        fruit:genus  sys:is_a
ln fruit:grape      fruit:genus  sys:is_a
ln fruit:date       fruit:genus  sys:is_a
ln fruit:pomegranate fruit:genus sys:is_a
ln fruit:olive      fruit:genus  sys:is_a
ln fruit:lemon      fruit:genus  sys:is_a
ln fruit:orange     fruit:genus  sys:is_a

# ── Geographic origin links ───────────────────────────────────────────────────

ln fruit:fig        place:levant             @originates_in
ln fruit:grape      place:levant             @originates_in
ln fruit:date       place:middle_east        @originates_in
ln fruit:date       place:north_africa       sys:associated_with
ln fruit:pomegranate place:persia            @originates_in
ln fruit:pomegranate place:levant            sys:associated_with
ln fruit:olive      place:mediterranean_basin @originates_in
ln fruit:lemon      place:southeast_asia     @originates_in
ln fruit:orange     place:southeast_asia     @originates_in

# ── Emotional and cultural associations ───────────────────────────────────────
# emo: atoms are defined in the base ontology and do not need def here.

ln fruit:fig        emo:nostalgia  emo:evokes
ln fruit:grape      emo:joy        emo:evokes
ln fruit:pomegranate emo:awe       emo:evokes
ln fruit:olive      emo:trust      emo:evokes
ln fruit:date       emo:anticipation emo:evokes

# ── Set membership ────────────────────────────────────────────────────────────

set.add name="set:fruits:mediterranean" id="fruit:fig"
set.add name="set:fruits:mediterranean" id="fruit:grape"
set.add name="set:fruits:mediterranean" id="fruit:date"
set.add name="set:fruits:mediterranean" id="fruit:pomegranate"
set.add name="set:fruits:mediterranean" id="fruit:olive"
set.add name="set:fruits:mediterranean" id="fruit:lemon"
set.add name="set:fruits:mediterranean" id="fruit:orange"

set.add name="set:fruits:ancient" id="fruit:fig"
set.add name="set:fruits:ancient" id="fruit:grape"
set.add name="set:fruits:ancient" id="fruit:date"
set.add name="set:fruits:ancient" id="fruit:pomegranate"
set.add name="set:fruits:ancient" id="fruit:olive"
```

Notice that `fruit:lemon` and `fruit:orange` are in `set:fruits:mediterranean` but not
`set:fruits:ancient` — they reached the Mediterranean much later and the distinction is
worth preserving in the graph. This is the kind of decision you make at authoring time;
the file records your judgment, not just the data.

---

## 0-4 Loading and Verifying

### Loading the File

Submit the file to the batch loader with:

```
run mediterranean_fruits.ak
```

If the file is not in your current directory, use the full path:

```
run /home/user/research/mediterranean_fruits.ak
```

The loader queues all lines as a background JCL job. You will see a confirmation that
the job was submitted. Because loading runs in the background, the CLI remains
responsive while the file is processed.

For a file of this size (about 60 lines), loading completes within a few seconds.
Large ontology files with thousands of atoms may take a minute or two — this is
normal. The WriteQueue ensures correctness; it processes one write at a time in order.

### Verifying Atoms Were Created

List atoms in the `fruit:` namespace:

```
onto.dump atoms ns=fruit: limit=20
```

You should see all seven fruit atoms plus `fruit:genus`. The output will show each
atom's key and the beginning of its description text.

Check which namespaces are now registered:

```
onto.dump namespaces
```

This lists every namespace present in the nucleus with its atom count. You should see
`fruit:` and `place:` appear with their respective counts.

### Reading Atoms by Alias

```
r fig
```

This returns the full text of the `fruit:fig` atom. If you see "alias not found", the
file may not have finished loading yet. Wait a moment and try again.

### Exploring Relationships

Dive into the fig atom's meaning space:

```
dive fig
```

The dive view shows the atom's text, its outgoing links (signposts), nearby atoms in
the graph, and its emotional position. You should see links to `fruit:genus`, `place:levant`,
and `emo:nostalgia` among the signposts.

Traverse the link tree to depth 2:

```
tree fig depth=2
```

This shows fig's direct links (depth 1) and the links from each of those atoms (depth 2).
At depth 2 you will see the Mediterranean basin's links, the Levant's links, and so on.

To see the entire set of Mediterranean fruits in a tree view:

```
tree set:fruits:mediterranean depth=1
```

This renders each member of the set as a top-level node, with its direct links beneath.
Depth 1 is a good starting point; depth 2 for a large set can produce a very long output.

---

## 0-5 Namespace Design

### What a Namespace Is

In Akasha, a namespace is the prefix before the colon in an atom's key. `fruit:fig` is
in the `fruit:` namespace. `place:levant` is in the `place:` namespace. `emo:nostalgia`
is in the `emo:` namespace.

Namespaces are a naming convention, not a schema enforcement mechanism. Akasha does not
prevent you from putting any key in any namespace. The colon is simply a character — but
because the CLI, `onto.dump`, and the export commands all treat it as a separator, the
convention is worth following consistently.

### Common Namespace Patterns

These patterns are used throughout the Akasha base ontology and are safe to follow
in your own files:

| Namespace | Contents |
|---|---|
| `concept:` | Abstract ideas, philosophical concepts |
| `fruit:`, `cheese:`, `dish:` | Domain-specific categories you define |
| `person:` | Named individuals (historical, fictional) |
| `place:` | Geographic locations, regions, cities |
| `era:` | Historical time periods |
| `emo:` | Emotional tones (base ontology — do not redefine) |
| `sys:` | Reserved for Akasha system relations — do not use for atoms |

### Why Namespaces Matter

**Avoiding key collisions.** The key `olive` could mean the fruit, the colour, the
name, or a town. Using `fruit:olive` is unambiguous. If someone later adds a
`color:olive` atom, there is no conflict.

**Grouping for export and inspection.** `onto.dump atoms ns=fruit:` returns only
fruit atoms. Without namespaces you would need to query by set membership instead —
more setup, less convenient.

**Graph traversal boundaries.** The `tree ns:fruit` command shows all atoms in the
`fruit:` namespace as top-level nodes. This makes namespace-organised graphs easy
to browse.

### Practical Tips

Keep keys lowercase and use underscores for multi-word concepts:

```
# Good
def "place:ancient_rome" "..."
def "era:bronze_age" "..."
def "concept:golden_mean" "Aristotle's doctrine of virtue as the midpoint between excess and deficiency."

# Avoid
def "place:Ancient Rome" "..."        # spaces in keys cause parsing ambiguity
def "Era:BronzeAge" "..."             # mixed case is harder to remember and search
```

Prefer width over depth. A three-level key like `cheese:europe:france:brie` is
technically valid but unwieldy. If you need to group French cheeses, use a set
(`set.add name="set:cheeses:france" id="cheese:brie"`) rather than embedding
geography into the key.

If you are defining a subdomain with many atoms, one file per namespace keeps files
manageable: `cheese_europe.ak`, `cheese_middle_east.ak`, rather than one enormous file.

### A Philosophers Example

Philosophers and their concepts illustrate namespace design well. The person occupies
the `person:` namespace; the concept occupies `concept:` or `phil:` (either works).
The link between them uses a relation that captures the relationship accurately.

```
# philosophers.ak — brief excerpt illustrating namespace conventions

def "person:aristotle"  "Greek philosopher, 384–322 BCE. Student of Plato, tutor of
Alexander the Great. Founder of logic, biology as a discipline, and the concept of
the golden mean. Wrote the Nicomachean Ethics, Politics, and Poetics."

def "person:plato"      "Greek philosopher, c. 428–348 BCE. Student of Socrates,
teacher of Aristotle. Developed the theory of Forms: that abstract universals are
more real than physical particulars."

def "person:heraclitus" "Greek philosopher, c. 535–475 BCE. Proposed that all things
are in constant flux and that opposites are unified. 'You cannot step into the same
river twice.' Associated with fire as the primary element."

def "person:epicurus"   "Greek philosopher, 341–270 BCE. Founder of Epicureanism.
Taught that the highest good is ataraxia (tranquility) achieved through simple
pleasures, friendship, and philosophical contemplation."

def "concept:golden_mean" "Aristotle's doctrine that virtue lies at the midpoint
between excess and deficiency. Courage is the mean between cowardice and recklessness."

def "concept:flux"      "Heraclitus's doctrine that all things are in constant change.
Reality is a dynamic process, not a fixed state. The river metaphor: constant flow,
yet the river persists."

def "concept:the_forms"  "Plato's theory that abstract universals (the Form of Beauty,
Justice, the Good) are the true reality, of which physical objects are imperfect copies."

def "concept:ataraxia"  "Epicurean term for tranquility of mind — freedom from mental
disturbance and anxiety. The highest human good in Epicurean philosophy."

al person:aristotle  aristotle
al person:plato      plato
al person:heraclitus heraclitus
al person:epicurus   epicurus

al concept:golden_mean golden_mean
al concept:flux        flux
al concept:the_forms   the_forms
al concept:ataraxia    ataraxia

ln person:aristotle  concept:golden_mean  @articulated
ln person:heraclitus concept:flux         @articulated
ln person:plato      concept:the_forms    @articulated
ln person:epicurus   concept:ataraxia     @articulated

ln person:plato      person:aristotle     @taught
ln person:aristotle  person:plato         @studied_under

ln concept:flux      emo:awe     emo:evokes
ln concept:the_forms emo:curiosity emo:evokes
ln concept:ataraxia  emo:trust   emo:evokes

set.add name="set:persons:greek_philosophers"  id="person:aristotle"
set.add name="set:persons:greek_philosophers"  id="person:plato"
set.add name="set:persons:greek_philosophers"  id="person:heraclitus"
set.add name="set:persons:greek_philosophers"  id="person:epicurus"

set.add name="set:concepts:ancient_philosophy" id="concept:golden_mean"
set.add name="set:concepts:ancient_philosophy" id="concept:flux"
set.add name="set:concepts:ancient_philosophy" id="concept:the_forms"
set.add name="set:concepts:ancient_philosophy" id="concept:ataraxia"
```

---

## 0-6 A Richer .ak File: Cheeses with Attributes

The cheese example introduces a situation you will encounter often: you want to record
structured attributes (aging period, texture, milk source) alongside the narrative
description. This is where `.ak` and the `rec.*` CLI commands work together.

### What .ak Can Express Directly

The `.ak` format records atoms, links, and set membership. Links are the way `.ak`
expresses attributes: you create atoms for the attribute values and link to them.

```
# cheese_mediterranean.ak
# Six European cheeses with Mediterranean and Near-Eastern connections.

# ── Classification and texture hubs ──────────────────────────────────────────

def "cheese:genus"       "The genus-level category for cheeses: curdled and aged milk
products. Used as the is_a hub for all cheese atoms in this file."

def "cheese:type:soft"   "Soft-textured cheese. High moisture content. Typically young,
mild, and eaten soon after production. Examples: Brie, fresh chèvre, ricotta."

def "cheese:type:semi_hard" "Semi-hard textured cheese. Moderate moisture, firm but
supple paste. Often aged 1–6 months. Examples: Halloumi, Manchego (young), Gruyère (young)."

def "cheese:type:hard"   "Hard-textured cheese. Low moisture, firm paste, aged at least
6 months. Develops complex, concentrated flavour. Examples: aged Manchego, Pecorino."

def "cheese:type:brined" "Cheese aged and stored in brine (saltwater). Distinctive salty
flavour, white colour, crumbly to creamy texture. Examples: Feta, Halloumi."

def "cheese:milk:sheep"  "Cheese made from sheep's milk. Richer in fat and protein than
cow's milk. Characteristic flavour: lanolin, nuttiness, slight sweetness."

def "cheese:milk:cow"    "Cheese made from cow's milk. Most common milk type. Mild
flavour base; ranges from fresh and lactic to rich and complex when aged."

def "cheese:milk:mixed"  "Cheese made from a blend of milks (cow + sheep, or cow + goat).
Complexity from multiple milk flavours."

# ── Place atoms (minimal set for this file) ──────────────────────────────────

def "place:france"       "The French Republic. Major world cheese-producing nation;
home to more than 400 distinct cheese styles, many with PDO protection."

def "place:switzerland"  "The Swiss Confederation. Alpine cheese traditions dating
to the Middle Ages. Home of Gruyère, Emmental, Appenzeller, and Raclette."

def "place:greece"       "The Hellenic Republic. Mediterranean cheese traditions
going back to antiquity. Feta is the most widely exported Greek cheese."

def "place:spain"        "The Kingdom of Spain. Diverse regional cheese traditions.
Manchego from La Mancha is the flagship Spanish cheese internationally."

def "place:cyprus"       "The Republic of Cyprus. Eastern Mediterranean island with
a distinct cheese culture. Halloumi — the grilling cheese — is its most famous export."

def "place:italy"        "The Italian Republic. Home to a vast canon of regional
cheeses, including Parmigiano-Reggiano, Pecorino, Gorgonzola, and Mozzarella."

al place:france     france
al place:switzerland switzerland
al place:greece     greece
al place:spain      spain
al place:cyprus     cyprus
al place:italy      italy

# ── Cheese atoms ─────────────────────────────────────────────────────────────

def "cheese:brie"        "Brie is a soft-ripened cow's milk cheese from the Île-de-France
region of France. Bloomy white rind, supple ivory paste, flavour of mushroom and butter.
Historically called the 'King of Cheeses.' Typically aged 4–8 weeks."

def "cheese:gruyere"     "Gruyère (AOP) is a hard cow's milk cheese from the canton of
Fribourg, Switzerland. Produced since at least the 12th century. Pale yellow paste,
small eyes, flavour of fruit and hazelnut that deepens with age. Aged 5–18 months."

def "cheese:feta"        "Feta (PDO) is a brined white cheese from Greece, made from
sheep's milk or a sheep-and-goat blend (at most 30% goat). Firm yet crumbly, tangy
and salty. One of the oldest cheeses in the world. PDO status since 2002."

def "cheese:manchego"    "Manchego (DOP) is a hard sheep's milk cheese from La Mancha,
Spain. Herringbone rind pattern impressed by the traditional esparto grass mould.
Ivory paste, small holes, buttery and nutty flavour. Aged 60 days to 2 years."

def "cheese:halloumi"    "Halloumi is a semi-hard brined cheese from Cyprus, made from
sheep's and goat's milk (sometimes with cow's milk). Very high melting point — it can
be grilled or fried without losing shape. Distinctive squeaky texture when fresh."

def "cheese:pecorino"    "Pecorino is any Italian cheese made from sheep's milk (pecora
= sheep). The most famous variety, Pecorino Romano (DOP), is hard and sharp, used
grated in Roman pasta dishes (cacio e pepe, amatriciana). The Tuscan variant is milder."

# ── Aliases ───────────────────────────────────────────────────────────────────

al cheese:brie     brie
al cheese:gruyere  gruyere
al cheese:feta     feta
al cheese:manchego manchego
al cheese:halloumi halloumi
al cheese:pecorino pecorino

# ── Classification links ──────────────────────────────────────────────────────

ln cheese:brie     cheese:genus sys:is_a
ln cheese:gruyere  cheese:genus sys:is_a
ln cheese:feta     cheese:genus sys:is_a
ln cheese:manchego cheese:genus sys:is_a
ln cheese:halloumi cheese:genus sys:is_a
ln cheese:pecorino cheese:genus sys:is_a

# ── Texture links ─────────────────────────────────────────────────────────────

ln cheese:brie     cheese:type:soft      sys:is_a
ln cheese:gruyere  cheese:type:hard      sys:is_a
ln cheese:feta     cheese:type:brined    sys:is_a
ln cheese:manchego cheese:type:hard      sys:is_a
ln cheese:halloumi cheese:type:brined    sys:is_a
ln cheese:halloumi cheese:type:semi_hard sys:associated_with
ln cheese:pecorino cheese:type:hard      sys:is_a

# ── Milk source links ─────────────────────────────────────────────────────────

ln cheese:brie     cheese:milk:cow   @made_from
ln cheese:gruyere  cheese:milk:cow   @made_from
ln cheese:feta     cheese:milk:sheep @made_from
ln cheese:manchego cheese:milk:sheep @made_from
ln cheese:halloumi cheese:milk:mixed @made_from
ln cheese:pecorino cheese:milk:sheep @made_from

# ── Geographic origin ─────────────────────────────────────────────────────────

ln cheese:brie     place:france      @originates_in
ln cheese:gruyere  place:switzerland @originates_in
ln cheese:feta     place:greece      @originates_in
ln cheese:manchego place:spain       @originates_in
ln cheese:halloumi place:cyprus      @originates_in
ln cheese:pecorino place:italy       @originates_in

# ── Emotional associations ────────────────────────────────────────────────────

ln cheese:brie     emo:joy        emo:evokes
ln cheese:gruyere  emo:trust      emo:evokes
ln cheese:feta     emo:nostalgia  emo:evokes
ln cheese:manchego emo:anticipation emo:evokes
ln cheese:halloumi emo:surprise   emo:evokes
ln cheese:pecorino emo:trust      emo:evokes

# ── Set membership ────────────────────────────────────────────────────────────

set.add name="set:cheeses:european"        id="cheese:brie"
set.add name="set:cheeses:european"        id="cheese:gruyere"
set.add name="set:cheeses:european"        id="cheese:feta"
set.add name="set:cheeses:european"        id="cheese:manchego"
set.add name="set:cheeses:european"        id="cheese:halloumi"
set.add name="set:cheeses:european"        id="cheese:pecorino"

set.add name="set:cheeses:sheep_milk"      id="cheese:feta"
set.add name="set:cheeses:sheep_milk"      id="cheese:manchego"
set.add name="set:cheeses:sheep_milk"      id="cheese:pecorino"

set.add name="set:cheeses:mediterranean"   id="cheese:feta"
set.add name="set:cheeses:mediterranean"   id="cheese:halloumi"
set.add name="set:cheeses:mediterranean"   id="cheese:manchego"
set.add name="set:cheeses:mediterranean"   id="cheese:pecorino"
```

### What .ak Cannot Express: Numeric Attributes

The `.ak` format has no syntax for storing a number directly on an atom.
Aging in months, fat content, moisture percentage — these are numeric facts and they
belong in the `rec.*` layer, not in the link graph.

After loading the file above, add aging times interactively at the CLI:

```
rec.set key=cheese:brie     attr=aging_months_min val=1
rec.set key=cheese:brie     attr=aging_months_max val=2
rec.set key=cheese:gruyere  attr=aging_months_min val=5
rec.set key=cheese:gruyere  attr=aging_months_max val=18
rec.set key=cheese:feta     attr=aging_months_min val=2
rec.set key=cheese:manchego attr=aging_months_min val=2
rec.set key=cheese:manchego attr=aging_months_max val=24
rec.set key=cheese:halloumi attr=aging_months_min val=0
rec.set key=cheese:pecorino attr=aging_months_min val=5

# Enroll all six into the rec index so rec.table can display them
rec.idx key=cheese:brie     sets=set:rec:cheese
rec.idx key=cheese:gruyere  sets=set:rec:cheese
rec.idx key=cheese:feta     sets=set:rec:cheese
rec.idx key=cheese:manchego sets=set:rec:cheese
rec.idx key=cheese:halloumi sets=set:rec:cheese
rec.idx key=cheese:pecorino sets=set:rec:cheese
```

Then display the table:

```
rec.table in_set=set:rec:cheese
```

The `.ak` file establishes the graph structure — what these atoms are, where they
come from, how they relate. The `rec.*` commands add the numeric layer on top.
Both layers live in the same Akasha nucleus and are traversable together.

---

## 0-7 Maintenance: Add, Update, Check

### Adding New Items

Open the `.ak` file and add a new block:

```
def "fruit:quince" "The quince (Cydonia oblonga), native to Southwest Asia and the
Caucasus. Hard, astringent when raw; transforms into a fragrant golden preserve when
cooked. Widespread in Mediterranean cuisine: membrillo in Spain, quince jam in Greece."

al fruit:quince quince

ln fruit:quince fruit:genus            sys:is_a
ln fruit:quince place:middle_east      @originates_in
ln fruit:quince emo:nostalgia          emo:evokes

set.add name="set:fruits:mediterranean" id="fruit:quince"
set.add name="set:fruits:ancient"       id="fruit:quince"
```

Then run the file again:

```
run mediterranean_fruits.ak
```

Because all commands are idempotent, re-running the full file is safe. The seven
original atoms are silently unified (no duplicate created); only `fruit:quince` and
its links are new additions.

### Checking What Is Loaded

Inspect the current state of the `fruit:` namespace:

```
onto.dump atoms ns=fruit:
```

Check link structure for a specific atom:

```
onto.dump links rel=sys:is_a
```

This lists every `sys:is_a` link in the nucleus — useful for confirming that all your
classification links landed correctly.

Spot-check an individual atom and its relationships:

```
r quince
dive quince
tree quince depth=2
```

### Removing Items

The `.ak` format does not have a delete command. Deletion is done at the CLI:

```
rm quince                       # remove the atom (requires no dangling links)
al.rm quince                    # remove just the alias without deleting the atom
```

If the atom has links pointing to or from it, you may need to remove those first:

```
ln.ls quince                    # list all links involving quince
ln.rm quince fruit:genus sys:is_a    # remove a specific link
```

After deleting an atom, re-running the `.ak` file will recreate it, because `def` is
idempotent in the direction of creation, not deletion. If you want an atom permanently
absent, remove its `def` block from the file before re-running.

---

## Next Steps

This chapter covered the complete `.ak` format: the four commands, namespace conventions,
a full Mediterranean fruits file, the cheese attributes pattern, and day-to-day
maintenance. At this point you can build a structured vocabulary from scratch and load
it reliably.

The next Green Book chapters build on this foundation:

- **Chapter 1** — Linking ontology files together; referencing atoms from the base
  ontology (place:, era:, emo:) instead of redefining them in every file.
- **Chapter 2** — Generating `.ak` files with an LLM; reviewing and curating the output.
- **Chapter 3** — Exporting a namespace with `onto.export` and distributing `.ak` files
  to other Akasha instances.

---

## Reference

The following specification documents provide authoritative detail on topics introduced
in this chapter. Consult them when you need precise behaviour descriptions; they are
not required reading to complete the examples above.

| Topic | Document |
|---|---|
| Complete `.ak` command vocabulary | `docs/ontology/ontology-spec.md` |
| Namespace conventions and reserved prefixes | `docs/ontology/ontology-spec.md` |
| `onto.dump` modes and parameters | `docs/for-llm/akasha-spec-compact.md` |
| `rec.*` structured record model | `docs/users/cli-quick-reference.md` |
| WriteQueue and idempotency guarantees | `docs/for-llm/architecture-vision.md` |
| Alias collision behaviour (first-wins) | `docs/users/user-manual.md` |
