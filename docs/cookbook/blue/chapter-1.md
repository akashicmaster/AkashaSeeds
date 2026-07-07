# Blue Book — Chapter 1: Writing and Extending Concept Models

> **Before this chapter:** read Red Book, Chapter 1 for the CLI-level concept model operations.
> This chapter shows how those operations are implemented and extended in Python.

---

## 1-1 What a Concept Model Is

Akasha is built around a strict separation between three roles:

| Role | What it is | Example |
|---|---|---|
| **Operand** | Data — carries no behaviour | Atom, Link, Set |
| **Operator** | Operation — defined independently of data | `op_new`, `op_ls`, `op_top` |
| **Agent** | Subject — applies Operators to Operands | human at the CLI, LLM, sensor, script |

A **concept model** is a collection of named Operators. It is nothing more than that.
When you type `rec.new content="fig"` at the CLI, the router looks up the `rec` prefix,
finds the class registered there, instantiates it with the current session, and calls
the `op_new` method on it. The Atom that gets written is the Operand.
The method that wrote it is the Operator.
You — or the LLM calling the API — are the Agent.

Operators do not live inside data objects. Atoms are immutable, content-addressed records
with no methods attached. If you need a new Operator, you add a new method to a concept
model class. The Atom does not change.

### The prefix is a namespace

The CLI prefix (`rec.`, `rating.`, `table.`) is purely a namespace that groups related
commands. A prefix called `rating` does not mean there is a separate "rating store" —
it means all commands under `rating.` are implemented by the same Python class.
The graph data itself is ordinary Atoms and Links; the concept model imposes no hidden
structure of its own.

### Schema is discovered, not declared

Consider the Mediterranean fruit dataset: fig, grape, date, lemon, orange, olive.
When fruit records are stored as `rec` atoms, attributes like `sweetness` and `acidity`
are stored as `rec:sweetness` and `rec:acidity` links pointing to value Atoms.
There is no column definition anywhere. When `rec.table` renders a table, it reads
whichever `rec:*` links are present on each Atom and assembles the columns on the spot.

This is the pattern you follow when writing your own concept model: let the graph links
be the schema. Discover them at operation time. Never declare them up front.

---

## 1-2 The Anatomy of a Concept Model

Every concept model is a Python class that extends `BaseConcept`.

### BaseConcept

```python
from lib.akasha.concepts.base import BaseConcept
```

`BaseConcept.__init__` receives a `session` object and wires up two key attributes:

| Attribute | What it provides |
|---|---|
| `self.session` | The `AkashaSession` — client identity, active scopes, session context |
| `self.cortex` | The `AkashaEngine` — graph read/write operations |

`BaseConcept` also exposes the `allowed_scopes` property, which returns
`self.session.active_scopes`. Use this whenever you call `check_access`.

### CONCEPT_PREFIX

```python
CONCEPT_PREFIX = "rating"
```

This string is the CLI namespace. Every method in `CONCEPT_METHODS` will be
accessible as `rating.<suffix>` in the CLI and via the JSON-RPC API.
Choose a short, lowercase, collision-free name.

### CONCEPT_METHODS

```python
CONCEPT_METHODS = {
    "add": {
        "op":     "op_add",
        "action": "write",
        "args":   ["key", "score", "note"],
        "desc":   "Add a score to an atom: rating.add key=<key> score=<0-1> [note=<text>]",
    },
    "ls": {
        "op":     "op_ls",
        "action": "read",
        "args":   ["in_set"],
        "desc":   "List all rated atoms: rating.ls [in_set=<set>]",
    },
}
```

Each entry maps a command suffix to a spec dict:

| Key | Required | Meaning |
|---|---|---|
| `"op"` | yes | Name of the method to call on the class |
| `"action"` | no | `"read"` or `"write"` — used by the IAM layer for access checks |
| `"args"` | no | Accepted parameter names — used for CLI tab-completion and routing |
| `"desc"` | no | One-line description shown in `help` output |

### op_* methods

Every Operator method follows the same convention:

```python
def op_add(self, key: str, score: float, note: str = "") -> dict:
    ...
```

- The method name must match the `"op"` value in `CONCEPT_METHODS`.
- Parameters correspond to the CLI arguments the user passes.
  The registry filters `data` to only the kwargs your method actually accepts.
- Return a plain `dict`, or a `TextViewConcept` descriptor for formatted output.

### TextViewConcept return types

When an `op_*` method wants the CLI to render structured output, it returns
a dict produced by one of the `TextViewConcept` factory methods.

```python
from lib.akasha.concepts.textview import TextViewConcept
```

There are three you will use most often:

**Table** — rows of records with named columns:
```python
TextViewConcept.table(
    title   = "Fruits",
    columns = ["name", "sweetness", "acidity"],
    rows    = [
        {"name": "fig",    "sweetness": "0.88", "acidity": "0.18"},
        {"name": "grape",  "sweetness": "0.82", "acidity": "0.35"},
    ],
)
```

**List** — flat list of labelled items:
```python
TextViewConcept.list_(
    title = "Sweet fruits",
    items = [
        TextViewConcept.item("fig",   meta="sweetness 0.88"),
        TextViewConcept.item("date",  meta="sweetness 0.95"),
        TextViewConcept.item("grape", meta="sweetness 0.82"),
    ],
)
```

**Keyval** — a single record shown as key-value pairs:
```python
TextViewConcept.keyval(
    title = "Fig",
    pairs = [("sweetness", "0.88"), ("acidity", "0.18")],
)
```

The `_view` field in the returned dict tells the CLI renderer which layout to use.
You never set it manually — the factory methods handle it.

---

## 1-3 Writing Your First Concept Model

This section walks through a complete concept model from scratch.

The goal: a `rating` model that lets any Agent attach a numeric quality score (0–1)
to any existing Atom, and retrieve ranked results.

```
rating.add key=<atom>  score=<0-1>  [note=<text>]
rating.ls  [in_set=<set>]
rating.top [in_set=<set>]  [limit=5]
```

### How it stores data

`rating.add` adds two links to the target Atom:

- `rating:score` → value Atom containing the score as a decimal string
- `rating:note`  → value Atom containing the annotation text (optional)

It also adds the target Atom's key to a global index set `set:rating:all`,
which is how `rating.ls` and `rating.top` discover what has been rated.

When `in_set` is given, the operation takes the intersection of `set:rating:all`
with the named set, so you can limit results to, say, `set:fruits:mediterranean`.

### The complete class

Save this file as `lib/akasha/concepts/rating.py`.
No other file needs to be edited — auto-discovery registers it on the next startup.

```python
"""
RatingConcept — score atoms on a 0–1 scale.

Operand  : target Atom (whatever you are rating), value Atoms (score, note text)
Operator : rating.add / rating.ls / rating.top
Agent    : any AkashaSession client — human, LLM, sensor, script
"""

import logging
import time
from typing import Any, Dict, List, Optional

from lib.akasha.concepts.base import BaseConcept
from lib.akasha.concepts.textview import TextViewConcept

logger = logging.getLogger("Harmonia.Rating")

_RATING_SET = "set:rating:all"


class RatingConcept(BaseConcept):
    """Score atoms on a 0–1 scale and retrieve ranked results."""

    CONCEPT_PREFIX = "rating"
    CONCEPT_LABEL  = "Score and rank atoms on a 0–1 scale"

    CONCEPT_METHODS = {
        "add": {
            "op":     "op_add",
            "action": "write",
            "args":   ["key", "score", "note"],
            "desc":   "Add or update a score: rating.add key=<key> score=<0-1> [note=<text>]",
        },
        "ls": {
            "op":     "op_ls",
            "action": "read",
            "args":   ["in_set"],
            "desc":   "List rated atoms with scores: rating.ls [in_set=<set>]",
        },
        "top": {
            "op":     "op_top",
            "action": "read",
            "args":   ["in_set", "limit"],
            "desc":   "Top-N atoms by score: rating.top [in_set=<set>] [limit=5]",
        },
    }

    # ── helpers ───────────────────────────────────────────────────────────────

    def _author_scopes(self):
        """Return (client_id, scopes) for write operations."""
        aid = getattr(self.session, "client_id", "system")
        return aid, [f"owner:user_{aid}", f"view:user_{aid}"]

    def _get_score(self, key: str) -> Optional[float]:
        """Return the rating:score value for this key, or None if unrated."""
        for dst, rel in self.cortex.get_adjacent_links(key):
            if rel == "rating:score":
                raw = self.cortex.get_chunk(dst) or ""
                try:
                    return float(raw)
                except (ValueError, TypeError):
                    return None
        return None

    def _get_note(self, key: str) -> str:
        """Return the rating:note text for this key, or an empty string."""
        for dst, rel in self.cortex.get_adjacent_links(key):
            if rel == "rating:note":
                return self.cortex.get_chunk(dst) or ""
        return ""

    def _resolve_keys(self, in_set: str) -> List[str]:
        """Return rated keys, optionally intersected with in_set."""
        rated = set(self.cortex.get_collection_members(_RATING_SET))
        if in_set:
            name = in_set if in_set.startswith("set:") else f"set:{in_set}"
            pool = set(self.cortex.get_collection_members(name))
            return list(rated & pool)
        return list(rated)

    # ── operators ─────────────────────────────────────────────────────────────

    def op_add(
        self,
        key: str,
        score: float,
        note: str = "",
    ) -> Dict[str, Any]:
        """[rating.add] Add or update a score on an atom."""
        if not key:
            raise ValueError("key is required.")
        score_f = float(score)
        if not 0.0 <= score_f <= 1.0:
            raise ValueError("score must be between 0.0 and 1.0.")

        author, scopes = self._author_scopes()

        # Remove any existing rating links before writing the new values.
        # This implements "last write wins" update semantics.
        for dst, rel in self.cortex.get_adjacent_links(key):
            if rel == "rating:score":
                self.cortex.remove_link(key, dst, "rating:score")
            elif rel == "rating:note" and note:
                self.cortex.remove_link(key, dst, "rating:note")

        score_key = self.cortex.put_chunk(
            content=str(score_f),
            meta={"type": "rating_value", "created_at": time.time()},
            author=author,
            scopes=scopes,
        )
        self.cortex.put_link(key, score_key, "rating:score", author=author)

        if note:
            note_key = self.cortex.put_chunk(
                content=note,
                meta={"type": "rating_note", "created_at": time.time()},
                author=author,
                scopes=scopes,
            )
            self.cortex.put_link(key, note_key, "rating:note", author=author)

        # Register the rated atom to the global index set.
        self.cortex.add_to_set(_RATING_SET, key)

        label = (self.cortex.get_chunk(key) or key)[:60]
        return {
            "status": "rated",
            "key":    key,
            "score":  score_f,
            "note":   note or None,
            "label":  label,
        }

    def op_ls(self, in_set: str = "") -> Dict[str, Any]:
        """[rating.ls] List all rated atoms with their scores."""
        scopes = self.allowed_scopes
        keys   = self._resolve_keys(in_set)

        rows = []
        for k in keys:
            if not self.cortex.check_access(k, self.allowed_scopes):
                continue
            s = self._get_score(k)
            if s is None:
                continue
            label = (self.cortex.get_chunk(k) or k)[:50]
            rows.append({
                "atom":  label,
                "score": f"{s:.2f}",
                "note":  self._get_note(k),
            })

        title = "Rated atoms" + (f"  ·  {in_set}" if in_set else "")
        return TextViewConcept.table(
            title   = title,
            columns = ["atom", "score", "note"],
            rows    = rows,
        )

    def op_top(self, in_set: str = "", limit: int = 5) -> Dict[str, Any]:
        """[rating.top] Show top-N atoms by score, highest first."""
        scopes = self.allowed_scopes
        keys   = self._resolve_keys(in_set)

        scored = []
        for k in keys:
            if not self.cortex.check_access(k, self.allowed_scopes):
                continue
            s = self._get_score(k)
            if s is not None:
                scored.append((k, s))

        scored.sort(key=lambda x: x[1], reverse=True)
        top = scored[: int(limit)]

        rows = []
        for rank, (k, s) in enumerate(top, start=1):
            label = (self.cortex.get_chunk(k) or k)[:50]
            rows.append({
                "rank":  str(rank),
                "atom":  label,
                "score": f"{s:.2f}",
                "note":  self._get_note(k),
            })

        title = f"Top {limit} by rating" + (f"  ·  {in_set}" if in_set else "")
        return TextViewConcept.table(
            title   = title,
            columns = ["rank", "atom", "score", "note"],
            rows    = rows,
        )
```

### File placement and auto-discovery

Place the file at:

```
lib/akasha/concepts/rating.py
```

The concept registry scans every `.py` file in that directory at startup.
Any class that defines both `CONCEPT_PREFIX` and `CONCEPT_METHODS` is registered
automatically. There is no central registry file to edit.

The scanner skips files whose names begin with `_` (underscores), so `__init__.py`,
`_helpers.py`, and similar support files are never treated as concept models.

After adding `rating.py` and restarting the server, the commands are immediately live:

```
rating.add key=<key> score=0.88 note="intensely sweet, almost honeyed"
rating.ls
rating.top limit=3
```

### CLI walkthrough with the fruit dataset

Assume the six Mediterranean fruits are already stored as `rec` atoms:

```
rec.new content="fig"    sweetness=0.88 acidity=0.18
rec.new content="grape"  sweetness=0.82 acidity=0.35
rec.new content="date"   sweetness=0.95 acidity=0.05
rec.new content="lemon"  sweetness=0.08 acidity=0.95
rec.new content="orange" sweetness=0.72 acidity=0.52
rec.new content="olive"  sweetness=0.10 acidity=0.22
```

Rate them for use in a cheese-pairing guide:

```
rating.add key=<fig-key>    score=0.88 note="excellent with aged pecorino"
rating.add key=<grape-key>  score=0.75 note="good with fresh chèvre"
rating.add key=<date-key>   score=0.92 note="outstanding with gorgonzola"
rating.add key=<lemon-key>  score=0.40 note="best as a garnish only"
rating.add key=<orange-key> score=0.70 note="works well with manchego"
rating.add key=<olive-key>  score=0.85 note="natural partner for feta"
```

Retrieve the full list:

```
rating.ls

Rated atoms
┌──────────────────────────────────────────┬───────┬────────────────────────────────────┐
│ atom                                     │ score │ note                               │
├──────────────────────────────────────────┼───────┼────────────────────────────────────┤
│ fig                                      │ 0.88  │ excellent with aged pecorino        │
│ date                                     │ 0.92  │ outstanding with gorgonzola         │
│ olive                                    │ 0.85  │ natural partner for feta            │
│ grape                                    │ 0.75  │ good with fresh chèvre              │
│ orange                                   │ 0.70  │ works well with manchego            │
│ lemon                                    │ 0.40  │ best as a garnish only              │
└──────────────────────────────────────────┴───────┴────────────────────────────────────┘
```

Top three:

```
rating.top limit=3

Top 3 by rating
┌──────┬────────┬───────┬──────────────────────────────────┐
│ rank │ atom   │ score │ note                             │
├──────┼────────┼───────┼──────────────────────────────────┤
│ 1    │ date   │ 0.92  │ outstanding with gorgonzola      │
│ 2    │ fig    │ 0.88  │ excellent with aged pecorino     │
│ 3    │ olive  │ 0.85  │ natural partner for feta         │
└──────┴────────┴───────┴──────────────────────────────────┘
```

---

## 1-4 Using cortex Methods

`self.cortex` is an `AkashaEngine` instance.
It is the only API surface you should use inside an `op_*` method.
Never access the SQLite backend directly.

The methods you will reach for most often are:

### Writing atoms

```python
key = self.cortex.put_chunk(
    content = "0.88",
    meta    = {"type": "rating_value", "created_at": time.time()},
    author  = author_id,
    scopes  = ["owner:user_alice", "view:user_alice"],
)
```

`put_chunk` is content-addressed: if an Atom with identical content already exists,
the same key is returned and no duplicate is created.
The `meta` dict is stored alongside the content but does not affect the key.
`scopes` controls who can read the Atom.

### Writing links

```python
self.cortex.put_link(
    src    = fruit_key,
    dst    = score_key,
    rel    = "rating:score",
    author = author_id,
)
```

`put_link` stores a directed, typed edge from `src` to `dst`.
The `rel` string is the relation label; by convention, concept model relations
are namespaced with the model prefix (`rating:score`, `rec:sweetness`, etc.).
The optional `w` parameter (default `1.0`) is a link weight.

### Removing links

```python
self.cortex.remove_link(src, dst, rel)
```

Use this when you need to replace an attribute: remove the old link,
then call `put_link` with the new destination.
This is the pattern `RatingConcept.op_add` uses to implement update semantics.

### Reading atom content

```python
content = self.cortex.get_chunk(key)   # returns str or None
meta    = self.cortex.get_meta(key)    # returns dict or {}
```

`get_chunk` returns the raw text stored in the Atom.
`get_meta` returns the metadata dict that was passed at write time.

### Reading links

```python
links = self.cortex.get_adjacent_links(key)
# returns [[dst_key, rel_label], ...]

for dst, rel in links:
    if rel == "rating:score":
        score = float(self.cortex.get_chunk(dst))
```

An optional second argument filters by relation:

```python
score_links = self.cortex.get_adjacent_links(key, "rating:score")
```

### Resolving aliases

```python
key = self.cortex.resolve_alias("fig")
# returns the key for the atom aliased as "fig", or None
```

Aliases let users pass a readable name (`fig`) instead of a hash key.
Always call `resolve_alias` first when your method accepts a key-or-alias argument.

### Working with sets

```python
# Add a key to a named set
self.cortex.add_to_set("set:fruits:mediterranean", key)

# List all keys in a set
keys = self.cortex.get_collection_members("set:fruits:mediterranean")
# returns a list of key strings
```

Set names are arbitrary strings. By convention, user-defined sets begin with
`set:` to distinguish them from system-generated collections.

### Checking access

```python
if self.cortex.check_access(key, self.allowed_scopes):
    # safe to read
```

Always check access before returning Atom content in a read operation.
`self.allowed_scopes` is a property on `BaseConcept` that reads
`self.session.active_scopes`.

---

## 1-5 Returning Display Views

`TextViewConcept` provides factory methods that produce structured output dicts.
The CLI renderer inspects the `_view` field in the returned dict to choose
the appropriate layout. You never set `_view` yourself.

Import it at the top of your concept model file:

```python
from lib.akasha.concepts.textview import TextViewConcept
```

### Table view — `TextViewConcept.table`

Use when results are naturally rows with named columns.
Most `ls` and `top` commands should return a table.

```python
return TextViewConcept.table(
    title   = "Mediterranean fruits",
    columns = ["fruit", "sweetness", "acidity"],
    rows    = [
        {"fruit": "date",   "sweetness": "0.95", "acidity": "0.05"},
        {"fruit": "fig",    "sweetness": "0.88", "acidity": "0.18"},
        {"fruit": "grape",  "sweetness": "0.82", "acidity": "0.35"},
        {"fruit": "orange", "sweetness": "0.72", "acidity": "0.52"},
        {"fruit": "olive",  "sweetness": "0.10", "acidity": "0.22"},
        {"fruit": "lemon",  "sweetness": "0.08", "acidity": "0.95"},
    ],
)
```

Each entry in `rows` is a plain dict. Keys are column names;
values are strings (convert numbers before passing). Columns are displayed
in the order given by the `columns` list.

### List view — `TextViewConcept.list_`

Use for a flat list of items where a full table would be excessive.
Good for `ls` commands that return names without rich attribute data.

```python
sweet = ["date", "fig", "grape"]

return TextViewConcept.list_(
    title = "Fruits with sweetness > 0.75",
    items = [
        TextViewConcept.item(label=name, meta=f"sweetness {sw}")
        for name, sw in [("date", "0.95"), ("fig", "0.88"), ("grape", "0.82")]
    ],
)
```

`TextViewConcept.item` is a helper that builds the `{"label", "meta", "detail"}`
dict expected by the list renderer. All fields after `label` are optional.

```python
TextViewConcept.item(label="olive", meta="sweetness 0.10", detail="low sugar, high fat")
```

### Keyval view — `TextViewConcept.keyval`

Use for a single record displayed as a key-value breakdown.
Good for `view` and `get` commands that show the detail of one atom.

```python
return TextViewConcept.keyval(
    title = "Fig — profile",
    pairs = [
        ("sweetness", "0.88"),
        ("acidity",   "0.18"),
        ("note",      "excellent with aged pecorino"),
        ("score",     "0.88"),
    ],
)
```

`pairs` is a list of `(key, value)` tuples. You can also pass
`{"key": k, "val": v}` dicts if that is more convenient in your context.

### Choosing the right view

| Situation | Use |
|---|---|
| Multiple records, multiple attributes | `table` |
| List of names or short labels | `list_` |
| Single record in full detail | `keyval` |
| Numeric series or frequency distribution | `chart` (see `rec.hist`) |

---

## 1-6 Adding Commands to Existing Models

### The direct edit approach

If you want to add `rec.rank` and you have write access to the codebase,
open `lib/akasha/concepts/rec.py` and:

1. Add a `"rank"` entry to `CONCEPT_METHODS`.
2. Add an `op_rank` method to the class.

```python
# Inside RecConcept.CONCEPT_METHODS, add:
"rank": {
    "op":     "op_rank",
    "action": "read",
    "args":   ["attr", "in_set", "limit"],
    "desc":   "Sort records by a numeric attribute: rec.rank attr=<a> in_set=<set> [limit=10]",
},
```

```python
def op_rank(
    self,
    attr:   str,
    in_set: str = "",
    limit:  int = 10,
) -> Dict[str, Any]:
    """[rec.rank] Sort records by a numeric attribute, highest first."""
    if not attr:
        raise ValueError("attr is required.")

    keys   = self._resolve_keys(in_set, type="")
    values = self._collect_float_attr(attr, keys)

    # Pair each key with its attribute value, then sort descending.
    scored = []
    for k in keys:
        s = None
        for dst, rel in self.cortex.get_adjacent_links(k):
            if rel == f"rec:{attr}":
                raw = self.cortex.get_chunk(dst) or ""
                try:
                    s = float(raw.replace(",", "").replace("_", ""))
                except (ValueError, TypeError):
                    pass
                break
        if s is not None:
            scored.append((k, s))

    scored.sort(key=lambda x: x[1], reverse=True)
    top = scored[: int(limit)]

    rows = []
    for rank, (k, s) in enumerate(top, start=1):
        label = (self.cortex.get_chunk(k) or k)[:50]
        rows.append({"rank": str(rank), "atom": label, attr: f"{s:.4g}"})

    title = f"Ranked by {attr}" + (f"  ·  {in_set}" if in_set else "")
    return TextViewConcept.table(
        title   = title,
        columns = ["rank", "atom", attr],
        rows    = rows,
    )
```

After the restart, `rec.rank` is available in the CLI:

```
rec.rank attr=sweetness in_set=set:fruits:mediterranean limit=6

Ranked by sweetness  ·  set:fruits:mediterranean
┌──────┬────────┬───────────┐
│ rank │ atom   │ sweetness │
├──────┼────────┼───────────┤
│ 1    │ date   │ 0.95      │
│ 2    │ fig    │ 0.88      │
│ 3    │ grape  │ 0.82      │
│ 4    │ orange │ 0.72      │
│ 5    │ olive  │ 0.1       │
│ 6    │ lemon  │ 0.08      │
└──────┴────────┴───────────┘
```

### The subclass extension approach

When you want to add a command to a model without modifying its source file —
for instance, when working in a fork or adding project-specific extensions —
drop a new file into `lib/akasha/concepts/` with a subclass that declares
**only the new commands** in its own `CONCEPT_METHODS`.
The registry will register those commands alongside the parent class's commands
because both share the same `CONCEPT_PREFIX`.

```python
# lib/akasha/concepts/rec_rank.py

from lib.akasha.concepts.rec import RecConcept
from lib.akasha.concepts.textview import TextViewConcept


class RecRankExtension(RecConcept):
    """Adds rec.rank without modifying RecConcept."""

    CONCEPT_PREFIX  = "rec"
    CONCEPT_METHODS = {
        "rank": {
            "op":     "op_rank",
            "action": "read",
            "args":   ["attr", "in_set", "limit"],
            "desc":   "Sort records by a numeric attribute: rec.rank attr=<a> in_set=<set> [limit=10]",
        },
    }

    def op_rank(self, attr: str, in_set: str = "", limit: int = 10) -> dict:
        # self._resolve_keys and self._collect_float_attr are inherited from RecConcept.
        keys = self._resolve_keys(in_set, type="")
        scored = []
        for k in keys:
            for dst, rel in self.cortex.get_adjacent_links(k):
                if rel == f"rec:{attr}":
                    raw = self.cortex.get_chunk(dst) or ""
                    try:
                        scored.append((k, float(raw.replace(",", "").replace("_", ""))))
                    except (ValueError, TypeError):
                        pass
                    break

        scored.sort(key=lambda x: x[1], reverse=True)
        rows = [
            {"rank": str(i + 1), "atom": (self.cortex.get_chunk(k) or k)[:50], attr: f"{s:.4g}"}
            for i, (k, s) in enumerate(scored[: int(limit)])
        ]
        return TextViewConcept.table(
            title   = f"Ranked by {attr}" + (f"  ·  {in_set}" if in_set else ""),
            columns = ["rank", "atom", attr],
            rows    = rows,
        )
```

Subclassing is the right choice when you want to share logic with the parent class
(inherited helpers like `_resolve_keys`, `_collect_float_attr`) without duplicating it.
The new command appears in `help` output as soon as the server restarts.

---

## Next Steps / References

**Continue in the Blue Book:**
- Chapter 2 covers concept model testing: how to write unit tests for `op_*` methods
  using an in-memory `AkashaSession`, without needing a running server.
- Chapter 3 covers session context: how to store and retrieve cross-call state
  with `self.session.set_context` / `self.session.get_context`.

**Specification references:**
- `lib/akasha/concepts/base.py` — `BaseConcept`, staging, span annotations
- `lib/akasha/concepts/textview.py` — all `TextViewConcept` factory methods and signatures
- `lib/akasha/concepts/registry.py` — `ConceptRegistry.discover` and `ConceptRegistry.dispatch`
- `lib/akasha/concepts/rec.py` — production example: schema-free record model
- `lib/akasha/composite.py` — `AkashaEngine` cortex methods in full detail
- `docs/for-llm/` — LLM-oriented reference for concept model construction
