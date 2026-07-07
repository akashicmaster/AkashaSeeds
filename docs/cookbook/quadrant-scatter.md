# Four-Quadrant Scatter Plot — `quadrant.plot`

This chapter shows the complete procedure for taking data created with `rec.*` and rendering it as a four-quadrant scatter plot in the terminal using `quadrant.plot`.

---

## Overview

`quadrant.plot` reads rec Atoms belonging to any Set and draws an ASCII scatter plot with two numeric attributes as the X and Y axes.

```
quadrant.plot in_set=<set-name> x=<attribute-name> y=<attribute-name>
```

- Coordinates are calculated automatically (midpoint derived from the data minimum and maximum)
- Each point is labeled (default label is the Atom's `content`)
- The dividing lines and corner labels for the four quadrants can be specified

No external libraries required. No browser required. Runs in the terminal alone.

---

## Step 1 — Register Data with `rec.new`

We use fruit as an example. Each fruit is assigned `acidity` and `sweetness` scores between 0 and 1.

```
rec.new type=fruit content="Mango"      acidity=0.20 sweetness=0.90
rec.new type=fruit content="Grape"      acidity=0.35 sweetness=0.82
rec.new type=fruit content="Strawberry" acidity=0.68 sweetness=0.74
rec.new type=fruit content="Pineapple"  acidity=0.72 sweetness=0.65
rec.new type=fruit content="Cantaloupe" acidity=0.22 sweetness=0.38
rec.new type=fruit content="Grapefruit" acidity=0.80 sweetness=0.28
rec.new type=fruit content="Lemon"      acidity=0.95 sweetness=0.10
```

Running `rec.new type=fruit` automatically registers each Atom in `set:rec:fruit`.

### Verification

```
rec.ls type=fruit
```

If 7 items are returned, you are ready to proceed.

---

## Step 2 — Plot the Scatter Chart

```
quadrant.plot in_set=set:rec:fruit x=acidity y=sweetness
```

Output (for a terminal width of approximately 80 characters):

```
  set:rec:fruit  ·  acidity × sweetness
        sweet & mild           ┆sweet & tart

  sweetness ↑
   1.00 ┤                       ┆
        ┤     ●                 ┆                          Mango
        ┤            ●          ┆                          Grape
        ┤                       ┆     ●                    Strawberry
        ┤                       ┆       ●                  Pineapple
        ┤                       ┆
   0.50 ┼╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┼╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌
        ┤      ●                ┆                          Cantaloupe
        ┤                       ┆           ●              Grapefruit
        ┤                       ┆
        ┤                       ┆                  ●       Lemon
   0.00 ┤                       ┆
        bland                  ┆sour
        └────────────────────────────────────────────────
         0.11                  0.57                 1.04
         acidity →
```

The axis midpoint (`0.57`) is calculated automatically from the data minimum and maximum.

---

## Step 3 — Name the Quadrants

The four corner labels can be specified as arguments.

| Argument | Position |
|------|------|
| `q1` | Top-right (high X, high Y) |
| `q2` | Top-left (low X, high Y) |
| `q3` | Bottom-left (low X, low Y) |
| `q4` | Bottom-right (high X, low Y) |

```
quadrant.plot in_set=set:rec:fruit x=acidity y=sweetness \
    q1="sweet & tart" q2="sweet & mild" q3="bland" q4="sour"
```

Corner labels are displayed faintly above and below the dividing lines (see the output example above).

---

## Step 4 — Specify the Midpoint Manually

If you want a fixed midpoint instead of the statistically derived midpoint from the data, use `x_mid` / `y_mid`.

Example: splitting into four quadrants with `0.5` as the baseline for both acidity and sweetness:

```
quadrant.plot in_set=set:rec:fruit x=acidity y=sweetness \
    x_mid=0.5 y_mid=0.5 \
    q1="sweet & tart" q2="sweet & mild" q3="bland" q4="sour"
```

Fixing the midpoint keeps the axes from shifting when additional data is entered.
Use this when you have a defined reference value, such as in portfolio analysis or scoring evaluations.

---

## Step 5 — Change the Axis Labels

The axis labels displayed can be overridden with `x_label` / `y_label`.
The attribute name is used as the default, but you can assign any custom display name.

```
quadrant.plot in_set=set:rec:fruit x=acidity y=sweetness \
    x_label="Acidity" y_label="Sweetness"
```

---

## Legend Display When Labels Overlap

When multiple Atoms fall on the same grid row, points are displayed as numbers (`1`–`9`) instead of `●`, and a legend is shown below the plot.

```
  sweetness ↑
   0.90 ┤  1 3  ┆ 2        ← multiple points on the same row
  ...

  1.  Mango
  2.  Strawberry
  3.  Grape
```

When data points are dense, adjust `x_mid` / `y_mid` to spread them out, or target a more focused subset.

---

## Attribute Names

The names passed to `x=` / `y=` must exactly match the attribute names used in `rec.new`.

```
rec.new type=fruit content="Mango" acidity=0.20 sweetness=0.90
                                   ↑                ↑
quadrant.plot ... x=acidity y=sweetness
                    ↑           ↑  ← same names
```

Atoms whose attribute values are not numeric are automatically skipped.

---

## Parameter Reference

| Argument | Required | Description |
|------|------|------|
| `in_set` | ✓ | Set name (`set:` prefix may be omitted) |
| `x` | ✓ | Name of the numeric attribute to use as the X axis |
| `y` | ✓ | Name of the numeric attribute to use as the Y axis |
| `label` | — | Attribute name to use for labels (default: `content`) |
| `x_mid` | — | X axis dividing position (default: data midpoint) |
| `y_mid` | — | Y axis dividing position (default: data midpoint) |
| `x_label` | — | X axis display name (default: value of `x`) |
| `y_label` | — | Y axis display name (default: value of `y`) |
| `q1` | — | Top-right corner label |
| `q2` | — | Top-left corner label |
| `q3` | — | Bottom-left corner label |
| `q4` | — | Bottom-right corner label |

---

## Applying to Existing Atoms (Without `rec.new`)

The target is not limited to Atoms created with `rec.new`.
Atoms written with `w`, or Atoms loaded from an ontology, can also have numeric attributes added after the fact with `rec.set` + `rec.idx`, and then passed to `quadrant.plot`.

```
# Example: adding scores to concept Atoms already in the ontology
rec.set key=concept:icarus   attr=hubris_score val=0.9
rec.set key=concept:icarus   attr=mythos_depth val=0.7
rec.idx key=concept:icarus   sets=rec:myth_analysis

rec.set key=concept:daedalus attr=hubris_score val=0.4
rec.set key=concept:daedalus attr=mythos_depth val=0.85
rec.idx key=concept:daedalus sets=rec:myth_analysis

quadrant.plot in_set=set:rec:myth_analysis x=hubris_score y=mythos_depth \
    q1="dangerous glory" q2="quiet craft" q3="forgotten" q4="prudent skill"
```

The content and ontological meaning of the original Atoms (such as `concept:icarus`) remain unchanged.
`rec.set` only adds a link `rec:hubris_score → "0.9"`.

You can also use `lens` to scan any set of Atoms, convert them to rec Atoms with `lens.flatten`,
and pass the result to `quadrant.plot`.

```
# Scan ontology subtree → rec snapshot → scatter plot
lens src=concept:mythology follow=sys:part_of depth=3
lens.flatten into=myth_snapshot
# ← add numeric attributes individually with rec.set, then quadrant.plot
```

---

## References

- `rec.new` / `rec.set` / `rec.idx` / `rec.table` → Quick Reference §Record Model
- Applying to existing Atoms, cast routes → Quick Reference §Concept Model Casting
- `table.view` → tabular display of table-type data
- `lens.*` → Quick Reference §Lens
- `TextViewConcept` → `lib/akasha/concepts/textview.py`
- `QuadrantConcept` → `lib/akasha/concepts/quadrant.py`
- Scatter plot renderer → `api/shell/renderer.py` `_render_tv_scatter()`
