# Concept-Oriented Design and Programming — Tutorial
## Building the Note Application Step by Step

> **Audience**: Contributors and co-developers who want to build a new Concept Model for AKASHA  
> **Example application**: `NoteConcept` — a hierarchical document engine with editing layer  
> **Prerequisite reading**: `docs/concept-model-spec.md`  
> **Version**: 1.2 — kernel series `seeds` (M1 editing layer)

---

## Part 1 — Concept-Oriented Design (COD)

Concept-Oriented Design asks one question before touching any code:

> *What is the conceptual shape of this domain, and how does it map to atoms and links?*

You are not designing a database schema or a class hierarchy. You are designing a **topology** — a graph structure that captures the domain's inherent relationships.

---

### 1.1 Domain Analysis: What Is a Note?

Start with the user's mental model, not the system's capabilities.

A *note* is a document a person writes over time. It has:

| Observation | Design consequence |
|---|---|
| A document has an identity and a title | → One **root atom** anchors the whole |
| Text is added incrementally | → Content arrives in an ordered stream |
| Chapters and sections divide the text | → A **containment hierarchy** sits alongside the stream |
| The reader reads top to bottom | → Order must be preserved exactly |
| Structural roles (chapter, section, paragraph) are general concepts used by many document types | → Those roles should exist as **vocabulary atoms** independent of any note |
| Writers revise — text changes after being written | → Edits must be non-destructive; history must survive |
| Writers rearrange — paragraphs move around | → Display order must be independent of write order |
| Writers want to undo mistakes | → Every mutation must be reversible |

Three problems must be solved simultaneously:

1. **Order**: how to traverse all content in writing order
2. **Hierarchy**: how to navigate the nested structure (ToC)
3. **Editing**: how to revise and rearrange without losing history or breaking traversal

Neither problem can be collapsed into the others.

---

### 1.2 Topology Design: Three-Layer Architecture

The solution is to maintain **three simultaneous graph structures** on the same set of atoms.

#### Horizontal Axis — the Input Timeline (immutable)

Every atom appended to the document joins a linear timeline:

```
root ──sys:top──► chunk₁ ──sys:next──► chunk₂ ──sys:next──► chunk₃
  └──sys:bottom──────────────────────────────────────────────────────►┘
```

- `sys:top` points from root to the first element (set once, never moved)
- `sys:next` / `sys:previous` form a doubly linked list between consecutive elements
- `sys:bottom` is a **floating pointer** from root to the current tail

When a new node is appended:

1. Follow `sys:bottom` from root → get `last_node`
2. Link `last_node ──sys:next──► new_node`
3. Link `new_node ──sys:previous──► last_node`
4. Remove the old `root ──sys:bottom──► last_node` link
5. Add the new `root ──sys:bottom──► new_node` link

Reading is `O(n)` via `sys:next` traversal. The `sys:bottom` pointer makes append `O(1)`.

**This layer is sacred — it is never modified after creation.**

#### Vertical Axis — the Containment Tree

Sections and paragraphs are containers. Each container holds child atoms:

```
root
 └──sys:contains──► section₁
                      └──sys:contains──► paragraph₁
                                           └──sys:contains──► chunk₁
                                           └──sys:contains──► chunk₂
 └──sys:contains──► section₂
```

Every child also carries the reverse link:

```
chunk₁ ──sys:part_of──► paragraph₁ ──sys:part_of──► section₁
```

The session tracks `active_container_id` so that `note.add` always inserts into the correct parent without the caller having to specify it.

#### Edit Layer — the Revision Surface (mutable)

The edit layer is a separate set of links that sits *over* the input timeline and can be freely rebuilt without touching `sys:*` links.

```
root ──edit:top──► anchor₂ ──edit:next──► anchor₁ ──edit:next──► anchor₃
  └──edit:bottom──────────────────────────────────────────────────────────►┘
```

- `edit:top/bottom/next/previous` mirror the `sys:*` timeline structure but are **rebuildable** — used for reordering without disturbing write history.
- When no edit-layer order exists, all traversal falls back to `sys:top/next`.
- Each anchor (original chunk atom) may point to a current **version** atom via `note:current`:

```
anchor₁ ──note:current──► version_atom₃
              (new text)
version_atom₃ ──note:revises──► version_atom₂ ──note:revises──► anchor₁
                                                      (history chain)
```

- When `note:current` is absent, the anchor itself is the current content.
- `note:revises` forms a backwards chain from newest to oldest version — history is never deleted.

All state changes are recorded in a **journal atom** pointed to by `note:edit_journal`. The journal stores a history list and a cursor:

```json
{"history": [
  {"order": null,         "active": {}},
  {"order": ["a","b","c"], "active": {"a": "version_a2"}},
  {"order": ["b","a","c"], "active": {"a": "version_a2"}}
], "cursor": 2}
```

`order: null` means "use sys: order." Undo steps the cursor back; redo steps it forward. Each edit or move pushes a new state and truncates any redo future.

---

### 1.3 Set Design: the Two-Namespace Rule

Every concept model must decide which atoms it *owns* and how they are indexed.

NoteConcept uses two distinct namespaces:

| Set pattern | Contains | Purpose |
|---|---|---|
| `set:note:{root_id}` | Content atoms for this document | Document membership, full-text scans |
| `set:note:{root_id}:sections` | Section/chapter atoms | ToC traversal |
| `set:note:{root_id}:paragraphs` | Paragraph atoms | Paragraph enumeration |
| `set:concept:{root_id}` | Concept-word atoms (vocabulary) | General concept catalog |

**The critical constraint**: the same physical atom must never appear in both `set:note:*` and `set:concept:*`.

Content atoms are document-specific instances. Concept-word atoms are general vocabulary (e.g. the atom whose content is the word `"section"`, representing the concept of "section-ness"). These are different things and must not be conflated.

The connection is expressed as a one-directional link:

```
section_atom ──sys:derived_from──► concept:word:section
```

This says: "this node is a particular instance of the general concept 'section'." The reverse link is intentionally absent because the general concept does not know, or care, how each concrete model uses it.

---

### 1.4 Vocabulary Design: Concept-Word Atoms

Concept-word atoms are **shared vocabulary resources**. They are created once per word per user, aliased for stable lookup, and reused across all note instances:

```
concept:word:document   →  "document"
concept:word:section    →  "section"
concept:word:chapter    →  "chapter"
concept:word:paragraph  →  "paragraph"
concept:word:chunk      →  "chunk"
```

An alias `concept:word:<word>` makes the atom retrievable by name without knowing its hash. If a second note uses `op_section(role="section")`, the lookup finds the existing atom and reuses it.

---

### 1.5 Design Summary (before writing code)

```
┌───────────────────────────────────────────────────────────────────┐
│ NoteConcept topology                                              │
│                                                                   │
│  INPUT LAYER (immutable after append)                             │
│  root ──[sys:top]──► chunk₁ ──[sys:next]──► chunk₂ ──...         │
│   │ └──[sys:bottom]───────────────────────────────────►┘          │
│                                                                   │
│  HIERARCHY (containment, also immutable)                          │
│   root └──[sys:contains]──► section₁                             │
│               └──[sys:contains]──► paragraph₁                    │
│                                     └──[sys:contains]──► chunk₁  │
│                                                                   │
│  EDIT LAYER (rebuildable)                                         │
│  root ──[edit:top]──► chunk₂ ──[edit:next]──► chunk₁             │
│  chunk₁ ──[note:current]──► version_atom                         │
│  version_atom ──[note:revises]──► chunk₁   (history chain)       │
│  root ──[note:edit_journal]──► journal_atom                       │
│  root ──[note:title]──► title_atom         (mutable display name) │
│                                                                   │
│  VOCABULARY                                                       │
│  chunk₁ ──[sys:derived_from]──► concept:word:chunk               │
│                                    (separate atom, vocab)         │
│                                                                   │
│  set:note:{root_id}           ← content atoms                    │
│  set:note:{root_id}:sections  ← section atoms                    │
│  set:concept:{root_id}        ← concept-word atoms (vocab)       │
└───────────────────────────────────────────────────────────────────┘
```

---

## Part 2 — Concept-Oriented Programming (COP)

With the design settled, implementation is mostly mechanical: each design decision maps to a specific API call.

---

### 2.1 File Layout

```
lib/akasha/concepts/
  base.py      ← BaseConcept (do not modify without spec review)
  note.py      ← NoteConcept  ← you are here
```

A new concept model is a single file in `lib/akasha/concepts/`. It imports `BaseConcept` and nothing else from the akasha stack.

---

### 2.2 The Skeleton

```python
from lib.akasha.concepts.base import BaseConcept
from typing import Dict, Any, Optional
import time

class NoteConcept(BaseConcept):

    def __init__(self, session, concept_id=None):
        super().__init__(session, concept_id)
        # Auto-mount from session if no explicit id was given
        if not self.concept_id:
            active_root = getattr(self.session, "get_context", lambda k: None)("active_note_root")
            if active_root:
                self.concept_id = active_root
                self.set_name = f"set:concept:{self.concept_id}"
```

Key points:

- `super().__init__` sets up `self.cortex`, `self.session`, `self.concept_id`
- Auto-mount reads the session context key `active_note_root` set by `op_new`
- This means a freshly constructed `NoteConcept(session)` with no explicit id is ready to use if a note was previously created in the same session

---

### 2.3 `op_new` — the Entry Point

Every concept model has exactly one `op_new`. It is the only operator allowed to run when `concept_id` is `None`.

```python
def op_new(self, title: str) -> Dict[str, Any]:
    author_id = getattr(self.session, 'client_id', 'system')
    scopes = [f"owner:user_{author_id}", f"view:user_{author_id}"]

    # 1. Create the root atom
    root_id = self.cortex.put_chunk(
        content=f"[ Note Book: {title} ]",
        meta={"type": "concept", "concept": "note", "role": "document",
              "title": title, "created_at": time.time()},
        author=author_id,
        scopes=scopes
    )

    # 2. Mount the concept
    self.concept_id = root_id
    self.set_name = f"set:concept:{self.concept_id}"

    # 3. Create index sets
    self.cortex.create_set(self._get_set_name())
    self.cortex.create_set(self._get_set_name("sections"))
    self.cortex.create_set(self._get_set_name("paragraphs"))

    # 4. Register root atom (content set) + vocabulary link
    self._register_to_package(root_id, concept_word="document")

    # 5. Save in session
    self.session.set_context("active_note_root", root_id)
    self.session.set_context("active_container_id", root_id)

    return {"status": "initialized", "note_id": root_id, "title": title}
```

After `op_new` runs, every subsequent operator can call `self._require_concept()` safely.

---

### 2.4 The `_require_concept()` Guard

All operators except `op_new` must start with this call:

```python
def op_section(self, title: str, role: str = "section") -> Dict[str, Any]:
    self._require_concept()   # ← raises RuntimeError if no active note
    ...
```

`_require_concept()` is defined in `BaseConcept`:

```python
def _require_concept(self):
    if not self.concept_id:
        raise RuntimeError(
            f"No active concept in {self.__class__.__name__}. Call op_new first."
        )
```

The kernel catches this and returns a `-32002` JSON-RPC error to the caller.

---

### 2.5 Implementing the Timeline

The timeline is the most critical part. Here is the complete implementation:

```python
def _append_to_timeline(self, node_id: str, author_id: str):
    tail_links = self.cortex.get_adjacent_links(self.concept_id, "sys:bottom")

    if not tail_links:
        # First node ever — no previous tail
        self.cortex.put_link(self.concept_id, node_id, "sys:top", author=author_id)
    else:
        last_node_id = tail_links[0][0]
        self.cortex.put_link(last_node_id, node_id, "sys:next",     author=author_id)
        self.cortex.put_link(node_id, last_node_id, "sys:previous", author=author_id)
        # Move the floating pointer — must go through cortex.remove_link, not raw SQL
        self.cortex.remove_link(self.concept_id, last_node_id, "sys:bottom")

    self.cortex.put_link(self.concept_id, node_id, "sys:bottom", author=author_id)
```

**Important**: use `self.cortex.remove_link()`, not `self.cortex.core.conn.execute(...)`. Direct SQL bypasses the Cortex abstraction and breaks Harmonia transaction tracking.

The `remove_link` method is defined in `AkashaEngine` (`lib/akasha/composite.py`) and delegates to `core.remove_link_raw`.

---

### 2.6 Implementing a Container Operator (`op_section`)

```python
def op_section(self, title: str, role: str = "section") -> Dict[str, Any]:
    self._require_concept()

    author_id = getattr(self.session, 'client_id', 'system')
    scopes = [f"owner:user_{author_id}", f"view:user_{author_id}"]

    # 1. Create the section atom
    sec_id = self.cortex.put_chunk(
        content=title,
        meta={"role": role, "title": title, "created_at": time.time()},
        author=author_id, scopes=scopes
    )

    # 2. Register to note-scope sets + vocabulary link
    self._register_to_package(sec_id, subset_suffix="sections", concept_word=role)

    # 3. Append to timeline (horizontal)
    self._append_to_timeline(sec_id, author_id)

    # 4. Vertical containment
    active_container = (
        getattr(self.session, "get_context", lambda k: None)("active_container_id")
        or self.concept_id
    )
    self.cortex.put_link(active_container, sec_id, "sys:contains", author=author_id)
    self.cortex.put_link(sec_id, active_container, "sys:part_of",  author=author_id)

    # 5. Shift focus to this section
    self.session.set_context("active_container_id", sec_id)

    return {"status": f"{role}_created", "section_id": sec_id, "title": title}
```

Steps 3 and 4 are always both called for every structural atom. This is what makes the dual topology work.

---

### 2.7 Implementing the Vocabulary Helper

```python
_CONCEPT_WORD_ALIAS_PREFIX = "concept:word:"

def _get_or_create_concept_word(self, word: str) -> str:
    alias = f"{_CONCEPT_WORD_ALIAS_PREFIX}{word}"
    existing = self.cortex.resolve_alias(alias)
    if existing:
        return existing

    author_id = getattr(self.session, 'client_id', 'system')
    key = self.cortex.put_chunk(
        content=word,
        meta={"type": "concept_word", "word": word, "concept_model": "note",
              "created_at": time.time()},
        author=author_id,
        scopes=[f"owner:user_{author_id}", f"view:user_{author_id}"]
    )
    self.cortex.set_alias(key, alias)
    return key
```

And the registration helper that enforces the two-namespace rule:

```python
def _register_to_package(self, key: str, subset_suffix: str = None,
                          concept_word: str = None):
    author_id = getattr(self.session, 'client_id', 'system')

    # Content atom → note-scope sets ONLY
    self.cortex.add_to_set(self._get_set_name(), key)
    if subset_suffix:
        self.cortex.add_to_set(self._get_set_name(subset_suffix), key)

    # Concept-word atom → concept catalog (separate atom, one-directional link)
    if concept_word:
        cw_key = self._get_or_create_concept_word(concept_word)
        self.register_concept_node(cw_key)  # → set:concept:{root_id}
        self.cortex.put_link(key, cw_key, "sys:derived_from", author=author_id)
```

`register_concept_node` (from `BaseConcept`) adds `cw_key` to `set:concept:{root_id}`. The content atom `key` is never added there.

---

### 2.8 Implementing a Query Operator (`op_toc`)

Query operators read from the graph and return structured data. They never write.

```python
def op_toc(self) -> Dict[str, Any]:
    self._require_concept()

    sections = self.cortex.get_set_members(self._get_set_name("sections"))
    toc = []
    for sec_id in sections:
        chunk = self.cortex.get_chunk(sec_id)
        if chunk:
            meta = chunk.get("meta", {})
            toc.append({
                "node_id": sec_id,
                "title":   meta.get("title", ""),
                "role":    meta.get("role", "section"),
            })
    return {"toc": toc}
```

---

### 2.9 Implementing the Sequential Reader (`op_get_sequential_text`)

Walking the timeline uses `sys:next` links starting from `sys:top`:

```python
def op_get_sequential_text(self) -> List[Dict[str, Any]]:
    self._require_concept()

    top_links = self.cortex.get_adjacent_links(self.concept_id, "sys:top")
    if not top_links:
        return []

    cursor = top_links[0][0]
    sequence = []
    seen     = set()

    while cursor and cursor not in seen:
        seen.add(cursor)
        chunk = self.cortex.get_chunk(cursor)
        if chunk:
            meta = chunk.get("meta", {}) or {}
            if meta.get("role") not in ("document",):
                sequence.append({
                    "id":      cursor,
                    "content": chunk.get("content", ""),
                    "role":    meta.get("role", "chunk"),
                })
        next_links = self.cortex.get_adjacent_links(cursor, "sys:next")
        cursor = next_links[0][0] if next_links else None

    return sequence
```

`op_get_sequential_text` returns a **list of chunk dicts**, not a `{"text": ..., "chunk_count": ...}` scalar. The caller (`note.read`) receives this list directly as the RPC result.

The `seen` set guards against accidental cycles (should not occur, but is cheap insurance).

The `seen` set guards against accidental cycles (should not occur, but is cheap insurance).

---

### 2.10 Registering with the Kernel — Plugin Registry

The Concept Model Plugin Registry (`lib/akasha/concepts/registry.py`) scans
`lib/akasha/concepts/` at kernel startup and auto-discovers every class that defines both
`CONCEPT_PREFIX` and `CONCEPT_METHODS`. For a **new** concept model, no import, no dispatch
block, and no handler methods are needed in `kernel.py`.

> **Important — NoteConcept is the exception, not the example.**
>
> `NoteConcept` predates the plugin registry. In the production code, `kernel.py` dispatches
> every `note.*` and `loom.note.*` call through explicit `_handle_note_*` methods — the
> same manual pattern used before auto-discovery existed. If you open `lib/akasha/kernel.py`
> you will find these entries (`if method == "note.new": return self._handle_note_new(...)`,
> and so on for every note method).
>
> The `CONCEPT_PREFIX` / `CONCEPT_METHODS` attributes below show the **target pattern for new
> concept models**. Follow this pattern when you build a new concept class; do not model your
> kernel wiring on what NoteConcept does internally.

For a new concept model, add class-level attributes:

```python
class MyConcept(BaseConcept):
    CONCEPT_PREFIX = "myprefix"
    CONCEPT_METHODS = {
        # Input layer
        "new":    {"op": "op_new"},
        "add":    {"op": "op_add_item"},
        "read":   {"op": "op_read"},
        "rm":     {"op": "op_delete"},
        # Edit layer — coerce normalises alternate param names
        "edit":   {"op": "op_edit",
                   "coerce": lambda d: {"item_id": d.get("item_id") or d.get("id",""),
                                        "text": d.get("text","")}},
        "undo":   {"op": "op_undo"},
        "redo":   {"op": "op_redo"},
    }
```

The `coerce` lambda normalises alternate parameter names so CLI callers can use either form.
Full details in `docs/concept-model-spec.md §7.1`.

**Error mapping (handled by the registry automatically):**

| Python exception | JSON-RPC code | Typical cause |
|---|---|---|
| `RuntimeError` | `-32002` | `_require_concept` failed, not found |
| `TypeError`, `ValueError` | `-32602` | Invalid or missing parameter |
| `NotImplementedError` | `-32601` | Method declared in `CONCEPT_METHODS` but not implemented |
| `PermissionError`, any other | `-32603` | Access denied or internal error (falls to catch-all) |

> **Note:** There is no explicit `PermissionError` branch in the registry dispatcher — it falls through to the final `except Exception` handler, which returns `-32603`. If you want callers to receive a distinct permission-denied code (`-32003`), wrap the permission check in the kernel handler or raise a custom exception class that your outer error handler recognises.

**What still requires a manual edit:**

- **IAM routing** — add each method to `_METHOD_TO_ACTION` in `kernel.py` so
  permission enforcement works (see §2.11 below).
- **CLI aliases** — add short aliases to `api/router.py` (see §2.12 below).

---

### 2.11 IAM Routing

Add each method to `_METHOD_TO_ACTION` in `lib/akasha/kernel.py` so the IAM layer
knows whether a call requires read, write, or drop permission:

```python
# Input layer
"note.new":       "write",
"note.add":       "write",
"note.section":   "write",
"note.paragraph": "write",
"note.toc":       "read",
"note.read":      "read",
"note.rm":        "drop",
# Edit layer (M1)
"note.list":      "read",
"note.edit":      "write",
"note.move":      "write",
"note.undo":      "write",
"note.redo":      "write",
"note.restore":   "write",
"note.rename":    "write",
```

For a new concept model using `CONCEPT_PREFIX` / `CONCEPT_METHODS`, this is the only `kernel.py` edit needed — the registry handles dispatch automatically.

---

### 2.12 Wiring the CLI Router

Add entries to `COMMAND_SPECS` in `api/router.py`:

```python
# Input layer
"n.new":  {"method": "note.new",       "args": ["title"],         "desc": "Create a new note"},
"n.add":  {"method": "note.add",       "args": ["text"],          "desc": "Append a chunk"},
"n.sec":  {"method": "note.section",   "args": ["title"],         "desc": "Add a section"},
"n.chap": {"method": "note.section",   "args": ["title", "role"], "desc": "Add a chapter"},
"n.para": {"method": "note.paragraph", "args": ["category"],      "desc": "Add a paragraph"},
"n.toc":  {"method": "note.toc",       "args": [],                "desc": "Show ToC"},
"n.read": {"method": "note.read",      "args": [],                "desc": "Read note sequentially"},
"n.rm":   {"method": "note.rm",        "args": [],                "desc": "Delete active note"},
# Edit layer (M1)
"n.list":   {"method": "note.list",    "args": [],                   "desc": "List chunks (head preview)"},
"n.edit":   {"method": "note.edit",    "args": ["chunk_id", "text"], "desc": "Edit a chunk"},
"n.move":   {"method": "note.move",    "args": ["chunk_id", "after"],"desc": "Reorder a chunk"},
"n.undo":   {"method": "note.undo",    "args": [],                   "desc": "Undo last edit"},
"n.redo":   {"method": "note.redo",    "args": [],                   "desc": "Redo"},
"n.restore":{"method": "note.restore", "args": [],                   "desc": "Restore original"},
"n.rename": {"method": "note.rename",  "args": ["title"],            "desc": "Rename the note"},
```

The `CommandRouter` handles argument parsing automatically: the last declared arg absorbs all remaining tokens, so `n.new Field Notes — Ravenna 2026` works as expected.

---

### 2.13 Implementing the Edit Layer (M1)

The editing layer adds revision, reordering, undo/redo, and rename. It lives entirely in the same `NoteConcept` class — no separate file — and introduces five groups of helpers.

#### 2.13.1 Version Resolution

An *anchor* is the original chunk atom placed in the timeline by `note.add`. An *anchor* never changes.

A *version* is a content-addressed atom holding revised text. `note:current` points from anchor to its current version:

```python
def _current(self, anchor: str) -> str:
    """Return the current version for anchor, or anchor itself if unedited."""
    l = self.cortex.get_adjacent_links(anchor, "note:current")
    return l[0][0] if l else anchor

def _set_current(self, anchor: str, version: str, author: str):
    """Atomically swap the note:current pointer on anchor."""
    for dst, _rel in self.cortex.get_adjacent_links(anchor, "note:current"):
        self.cortex.remove_link(anchor, dst, "note:current")
    if version and version != anchor:
        self.cortex.put_link(anchor, version, "note:current", author=author)
```

When reading content, always go through `_current`:

```python
ver = self._current(anchor)
text = self._content(ver)  # fetches the version's text
```

#### 2.13.2 Effective Order

Display order is the edit layer when present, otherwise the input timeline:

```python
def _effective_order(self) -> list:
    if self.cortex.get_adjacent_links(self.concept_id, "edit:top"):
        return self._walk("edit:top", "edit:next")
    return self._sys_anchors()
```

`_walk(start_rel, next_rel)` follows a linked list from `self.concept_id`:

```python
def _walk(self, start_rel: str, next_rel: str) -> list:
    out, seen = [], set()
    top = self.cortex.get_adjacent_links(self.concept_id, start_rel)
    cur = top[0][0] if top else None
    while cur and cur not in seen:
        seen.add(cur)
        out.append(cur)
        nx = self.cortex.get_adjacent_links(cur, next_rel)
        cur = nx[0][0] if nx else None
    return out
```

Rebuilding the edit order from a new anchor list:

```python
def _build_edit_order(self, order: list, author: str):
    self._clear_edit_order()          # remove all existing edit: links
    if not order:
        return                        # absence = fall back to sys: order
    self.cortex.put_link(self.concept_id, order[0], "edit:top", author=author)
    for a, b in zip(order, order[1:]):
        self.cortex.put_link(a, b, "edit:next",     author=author)
        self.cortex.put_link(b, a, "edit:previous", author=author)
    self.cortex.put_link(self.concept_id, order[-1], "edit:bottom", author=author)
```

#### 2.13.3 The Edit Journal

The journal is a JSON atom that stores the full history of states and the current cursor position:

```python
def _journal(self) -> dict:
    l = self.cortex.get_adjacent_links(self.concept_id, "note:edit_journal")
    if l:
        try:
            j = json.loads(self._content(l[0][0]))
            if "history" in j and "cursor" in j:
                return j
        except Exception:
            pass
    return {"history": [{"order": None, "active": {}}], "cursor": 0}
```

The initial state `{"order": None, "active": {}}` means "use input order, no version overrides." Every edit or move pushes a new state:

```python
def _push_state(self, j: dict, state: dict) -> dict:
    """Truncate any redo-future after cursor, then push new state."""
    j["history"] = j["history"][: j["cursor"] + 1] + [state]
    j["cursor"] += 1
    return j
```

After updating the cursor, save the journal as a **new atom** (old atom stays as implicit history):

```python
def _save_journal(self, j: dict, author: str):
    _aid, scopes = self._auth()
    old = self.cortex.get_adjacent_links(self.concept_id, "note:edit_journal")
    new = self.cortex.put_chunk(
        content=json.dumps(j, ensure_ascii=False),
        meta={"type": "note_edit_journal", "updated_at": time.time()},
        author=author, scopes=scopes,
    )
    for dst, _r in old:
        self.cortex.remove_link(self.concept_id, dst, "note:edit_journal")
    self.cortex.put_link(self.concept_id, new, "note:edit_journal", author=author)
```

#### 2.13.4 Implementing `op_edit_chunk`

`op_edit_chunk` is the core write operator of the edit layer:

```python
def op_edit_chunk(self, chunk_id: str, text: str) -> dict:
    self._require_concept()
    self._require_access(chunk_id, "Chunk")   # IAM check on specific atom
    author, scopes = self._auth()

    # 1. Resolve current version (may be the anchor itself on first edit)
    prev = self._current(chunk_id)

    # 2. Create new version atom (content-addressed — gets a new hash)
    new = self.cortex.put_chunk(
        content=text,
        meta={"role": self._meta(chunk_id).get("role", "chunk"),
              "edited_at": time.time(), "anchor": chunk_id},
        author=author, scopes=scopes,
    )

    # 3. Register the new atom in the note's content set
    self.cortex.add_to_set(self._get_set_name(), new)

    # 4. Link history: new version → previous version
    self.cortex.put_link(new, prev, "note:revises", author=author)

    # 5. Update the journal
    j = self._journal()
    cur = j["history"][j["cursor"]]
    active = dict(cur.get("active", {}))
    active[chunk_id] = new                    # anchor → new version
    self._push_state(j, {"order": cur.get("order"), "active": active})
    self._save_journal(j, author)

    # 6. Move the note:current pointer
    self._set_current(chunk_id, new, author)

    return {"status": "edited", "chunk_id": chunk_id, "version": new}
```

Key invariants:
- `chunk_id` (the anchor) **never changes** — it is the stable identity.
- `note:revises` builds a backwards chain: newest → previous → … → original.
- The journal records `{anchor: new_version}` in `active` — undo will restore to the previous state.

#### 2.13.5 Implementing `op_move_chunk`

```python
def op_move_chunk(self, chunk_id: str, after: str = None) -> dict:
    self._require_concept()
    self._require_access(chunk_id, "Chunk")
    author, _scopes = self._auth()

    # Build new order: remove chunk, reinsert at target position
    order = [a for a in self._effective_order() if a != chunk_id]
    if after and after in order:
        order.insert(order.index(after) + 1, chunk_id)
    else:
        order.insert(0, chunk_id)             # after=None → move to top

    # Save journal state (preserves active content versions)
    j = self._journal()
    cur = j["history"][j["cursor"]]
    self._push_state(j, {"order": order, "active": cur.get("active", {})})
    self._save_journal(j, author)

    # Rebuild edit links
    self._build_edit_order(order, author)
    return {"status": "moved", "chunk_id": chunk_id, "after": after, "order": order}
```

`sys:top/next` is untouched. `edit:top/next` is rebuilt to reflect the new display order.

#### 2.13.6 Implementing Undo/Redo

```python
def op_undo_edit(self) -> dict:
    self._require_concept()
    author, _ = self._auth()
    j = self._journal()
    if j["cursor"] <= 0:
        return {"status": "nothing_to_undo"}
    j["cursor"] -= 1
    self._save_journal(j, author)
    self._materialize(j["history"][j["cursor"]], author)
    return {"status": "undone", "cursor": j["cursor"]}

def op_redo_edit(self) -> dict:
    self._require_concept()
    author, _ = self._auth()
    j = self._journal()
    if j["cursor"] >= len(j["history"]) - 1:
        return {"status": "nothing_to_redo"}
    j["cursor"] += 1
    self._save_journal(j, author)
    self._materialize(j["history"][j["cursor"]], author)
    return {"status": "redone", "cursor": j["cursor"]}
```

`_materialize` applies a saved state to the live graph:

```python
def _materialize(self, state: dict, author: str):
    self._build_edit_order(state.get("order"), author)
    active = state.get("active", {}) or {}
    for anchor in self._sys_anchors():
        self._set_current(anchor, active.get(anchor), author)
```

When `active.get(anchor)` is `None` (the anchor has no version override in this state), `_set_current` removes the `note:current` link, restoring the anchor as its own content.

#### 2.13.7 The Undo/Redo Branching Rule

If a user undoes several steps and then makes a new edit, the redo future is **discarded**:

```
history:  [s0, s1, s2, s3, s4]
cursor:    ↑cursor=2

user edits → _push_state truncates history to [s0, s1, s2] then appends new state:
history:  [s0, s1, s2, s5]
cursor:    ↑cursor=3
```

s3 and s4 are gone. The version atoms they referenced still exist in the graph (content-addressed atoms are never deleted), but they are no longer reachable from the journal. This is intentional: redo after a new edit would be confusing.

#### 2.13.8 `op_restore_original`

Restore discards all edit-layer overrides in one step, but does so as a **journal entry** — so restore itself is undoable:

```python
def op_restore_original(self) -> dict:
    self._require_concept()
    author, _ = self._auth()
    j = self._journal()
    self._push_state(j, {"order": None, "active": {}})  # push "original" state
    self._save_journal(j, author)
    self._materialize({"order": None, "active": {}}, author)
    return {"status": "restored_to_original"}
```

After this call, `note.undo` steps back to the previous edited state.

#### 2.13.9 `op_rename` and `_display_title`

Root atoms are content-addressed — their hash is their identity. Renaming cannot change the hash. Instead, a pointer atom carries the display name:

```python
def op_rename(self, title: str) -> dict:
    self._require_concept()
    author, scopes = self._auth()
    new_title = self.cortex.put_chunk(
        content=title,
        meta={"type": "note_title", "updated_at": time.time()},
        author=author, scopes=scopes,
    )
    for dst, _r in self.cortex.get_adjacent_links(self.concept_id, "note:title"):
        self.cortex.remove_link(self.concept_id, dst, "note:title")
    self.cortex.put_link(self.concept_id, new_title, "note:title", author=author)
    return {"status": "renamed", "note_id": self.concept_id, "title": title}

def _display_title(self) -> str:
    l = self.cortex.get_adjacent_links(self.concept_id, "note:title")
    if l:
        return self._content(l[0][0])
    return self._meta(self.concept_id).get("title", "")
```

`note.ls` and any listing UI should call `_display_title()` rather than reading `meta["title"]` directly.

---

### 2.14 Adding a Service

The service layer is intentionally thin. A concept model is not a microservice; it is a Cortex citizen. The service's only jobs are:

1. Serve the static UI files
2. Mount the standard JSON-RPC gateway (`/api/rpc`)

```python
# services/akashic_note.py
from services.http_gateway import BaseWebService

if __name__ == "__main__":
    app = BaseWebService(port=8082, host="0.0.0.0")
    print("Note service at http://0.0.0.0:8082/note/")
    app.start()
```

The frontend calls `/api/rpc` directly with standard JSON-RPC payloads — no custom REST routes needed.

---

### 2.15 Staging and Harmonia — Boundary Warning

`BaseConcept` includes an undo/redo staging layer (`staged_changes`, `commit_staged`). This is a convenience layer for interactive editing, not a transaction system.

**Staging is NOT Harmonia**. Key differences:

| Staging | Harmonia (JCL) |
|---|---|
| In-process, per-concept-instance | Kernel-level, per-job transaction |
| `commit_staged()` writes to Cortex immediately | Rollback reverses the job's tracked per-unit workspace writes (`ws:{tx_id}`) to the local cortex; commit-forward nucleus proto-word writes are not rolled back |
| No rollback if the JCL job fails | Per-unit rollback on job failure (local-cortex writes reversed; nucleus proto-word writes are commit-forward and idempotent, deliberately not rolled back) |

If you use `commit_staged()` inside a JCL job step, and the job later fails, the staged commits **will not be rolled back** by Harmonia. Design accordingly: either avoid staging inside JCL jobs, or treat committed state as permanent.

---

## Part 3 — Pattern Reference

### Pattern: Editing a Chunk

```python
# 1. Get the current chunk list
chunks = rpc("note.list", {})["chunks"]
chunk_id = chunks[0]["id"]       # stable anchor id

# 2. Edit its content (creates a new version atom; original preserved)
rpc("note.edit", {"chunk_id": chunk_id, "text": "Revised text."})

# 3. Undo the edit
rpc("note.undo", {})

# 4. Redo it again
rpc("note.redo", {})

# 5. Move a chunk to the top
rpc("note.move", {"chunk_id": chunks[1]["id"], "after": None})

# 6. Restore original order and content in one step
rpc("note.restore", {})

# 7. Rename the note
rpc("note.rename", {"title": "Field Notes — Final"})
```

**Invariants to remember:**
- `chunk_id` (anchor) is permanent. The `version` field in `note.list` changes after each edit.
- `note.undo` after `note.restore` returns to the last edited state.
- `note.edit` when undo history exists truncates the redo future — there is no multi-branch history.

### Pattern: Adding a New Structural Role

Suppose you want to add a `"sidebar"` container (like a chapter, but parallel to the main flow):

1. **Design**: sidebar is a container in the vertical hierarchy; it also belongs in the timeline. Same dual-axis pattern as section.
2. **Implement**: copy `op_section`, rename to `op_sidebar`, pass `role="sidebar"` to `_register_to_package`.
3. **Vocabulary**: `_get_or_create_concept_word("sidebar")` creates the shared vocabulary atom automatically.
4. **CLI**: add `"n.side"` to `COMMAND_SPECS` in `router.py`.
5. **Kernel**: add `"note.sidebar": "write"` to `_METHOD_TO_ACTION` in `kernel.py` (§2.11). No handler method needed — the Plugin Registry dispatches automatically.
6. **Spec**: add entry to §10.9 in `docs/api-spec.md`.

### Pattern: Adding a Query Operator

Query operators follow this template:

```python
def op_my_query(self, **params) -> Dict[str, Any]:
    self._require_concept()
    # Read from self.cortex — never write
    # Return a dict with the results
    return {"result": ...}
```

### Pattern: The Full Write Operator Checklist

For every new write operator:

- [ ] Call `self._require_concept()` at the top
- [ ] Use `self.cortex.put_chunk()` (never `core.conn.execute` directly)
- [ ] Call `_append_to_timeline()` if the atom is part of the document flow
- [ ] Call `_register_to_package()` with appropriate `subset_suffix` and `concept_word`
- [ ] Add containment links (`sys:contains` / `sys:part_of`) if this is a container
- [ ] Update `session.set_context("active_container_id", ...)` if this shifts focus
- [ ] Return a plain dict

---

## Part 4 — Concept-Oriented UI/UX Design

### 4.1 The Central Insight

Concept-Oriented Design is not limited to modeling human thought processes or analytical data. **Any user interface can be designed as a concept model.**

Most UI design starts from the visual: wireframes, component libraries, layout grids. This is natural but carries a hidden cost — visual decisions made early become implicit constraints on UX decisions made later. The look shapes the use, often in ways that are not noticed until the design is too entrenched to change.

Concept-Oriented UI/UX design inverts this order:

> *Design the UX as pure conceptual topology first. Let the visual representation be derived from the concept model, not the other way around.*

The concept model is rendering-agnostic. A Deck → Frame → Region → Node hierarchy describes the structure of a presentation. Whether that structure is rendered as a slide viewer in a browser, a card list on a phone, or a text outline in a terminal is a separate concern — one that can be deferred, swapped, or parallelized without touching the conceptual design.

---

### 4.2 Visual-First Design vs. Concept-First Design

| Dimension | Visual-First | Concept-First |
|---|---|---|
| Starting point | Wireframe, mockup, component | Domain atoms and their relationships |
| UX derived from | "What fits this layout?" | "What operations does the user need?" |
| Early constraints | Screen dimensions, visual hierarchy, component API | None — topology is unconstrained |
| Risk | UX locked to one visual metaphor | Requires discipline to defer rendering |
| Strength | Immediately concrete, stakeholder-friendly | Rendering-agnostic, portable across surfaces |
| Consistency | Guaranteed by design system | Guaranteed by concept model invariants |
| Change cost | High (visual + logic coupled) | Low (rendering layer is a thin projection) |

Neither approach is universally superior. The key insight is that concept-first design **preserves optionality longer**: the conceptual model can be projected onto any surface, while a visual-first design is already committed to one.

---

### 4.3 Use Cases as Atoms

In concept-first UI design, the fundamental design question is:

> *What can the user do, and what is the minimum set of atoms needed to represent that action and its result?*

Each user action corresponds to an operator. Each outcome is an atom or a link. The full UX is the graph that emerges from the user's sequence of operations.

**Example: a slide editor**

User intent → Concept operator → Atom/link created

| User intent | Operator | Atom or link |
|---|---|---|
| Create a presentation | `pres.new` | Root atom with `role: document` |
| Add a slide | `pres.frame.add` | Frame atom, `sys:next` link in timeline |
| Add a content region | `pres.region.add` | Region atom, `sys:contains` link from frame |
| Place a text node | `pres.node.add` | Node atom, `sys:contains` link from region |
| Navigate to a slide | `pres.open` | Sets `active_presentation_root` in session context |

There is no button, no panel, no color picker in this model. Those are rendering details. The concept model describes *what operations exist* and *how their results are related* — not how they look.

---

### 4.4 The Rendering-Agnostic Principle

A concept model defines a **topology**. A UI surface is a **projection** of that topology onto a specific rendering medium.

```
┌──────────────────────────────────────────────────┐
│ PresentationConcept topology (platform-neutral)  │
│                                                  │
│  root ──[sys:top]──► frame₁ ──[sys:next]──► frame₂│
│    └──[sys:contains]──► frame₁                  │
│                           └──[sys:contains]──►  │
│                               region₁            │
│                                 └──[sys:contains]│
│                                     ──► node₁    │
└──────────────────────────────────────────────────┘
           │                    │                │
           ▼                    ▼                ▼
     Web slide viewer    Mobile card list   CLI outline
     (React/Canvas)      (SwiftUI)          (plain text)
```

Each rendering projection reads the same graph and translates it to its medium. Adding a new surface — say, a voice interface that reads slides aloud — requires implementing a new projection, not redesigning the concept model.

This is the architectural payoff: **the concept model is the single source of truth for UX semantics**. All surfaces are views over it.

---

### 4.5 Designing Without Visual Constraints — Guidelines

The following guidelines apply when designing a UI using a concept model.

**Guideline 1 — Start with operations, not screens.**  
List every action a user can take. Write each as a method signature. Do not ask "what does this look like?" until every operation is defined.

**Guideline 2 — Model containment, not layout.**  
`sys:contains` expresses "A holds B." It says nothing about whether B is rendered inside A visually, below A in a list, or in a modal over A. Layout is the renderer's problem.

**Guideline 3 — Model sequence with a linked list.**  
Ordered content (slides, steps, history) maps to the `sys:top / sys:next / sys:bottom` pattern. The timeline is platform-neutral. A mobile renderer walks it top-to-bottom; a slide viewer jumps via index; a CLI printer walks it sequentially.

**Guideline 4 — Model identity with root atoms.**  
Every document, every presentation, every note has one root atom. This atom is the stable identity across sessions, devices, and rendering surfaces. Pass the root ID through the system, never a session-local handle.

**Guideline 5 — Defer visual vocabulary.**  
Labels like `"card"`, `"panel"`, `"drawer"`, `"modal"` are rendering vocabulary. The concept model uses structural vocabulary: `"frame"`, `"region"`, `"node"`, `"container"`. Map rendering vocabulary to conceptual vocabulary at the projection layer, not in the concept model itself.

**Guideline 6 — Let UX flow from `op_` operators.**  
The UI affordances available to a user at any point equal the set of operators whose preconditions are currently satisfied. A disabled button corresponds to `_require_concept()` returning an error. A greyed-out menu item corresponds to insufficient IAM permission. UI state is derived from concept model state — not managed separately.

---

### 4.6 Worked Example: PresentationConcept as UI Design

`PresentationConcept` (§5 of `concept-extensions.md`) was designed with this principle in mind. Its atom hierarchy directly describes a UI:

```
Deck       (root document — the presentation as a whole)
 └── Frame (a slide — the fundamental unit of navigation)
       └── Region (a layout zone: title area, body, sidebar)
             └── Node (a content element: text, image, chart)
```

This is both a data model and a UI model. A visual designer reading this immediately understands that:

- The navigation model is Deck → Frame (slide-by-slide)
- The layout model is Frame → Region (zones within a slide)
- The content model is Region → Node (items within a zone)

A developer implementing any surface — web, mobile, print, CLI — reads the same structure and knows:

- What to render at each level
- What operations to expose at each level
- What context to maintain between operations (the `active_presentation_root` session key)

The concept model is the shared design language between UX designer and developer. It is not a deliverable for stakeholders (wireframes serve that role) — it is the **architectural specification** that ensures both designer and developer are talking about the same UX.

---

### 4.7 Integration with the Analysis Pipeline

The concept-first UI design approach integrates naturally with the analysis pipeline described in Part 1 and `concept-extensions.md`:

```
FieldNote / Survey     →  raw observations
Aggregation            →  quantitative measures
Synthesis              →  qualitative interpretation
Presentation           →  output surface (the UI)
```

`PresentationConcept` is the output end of this pipeline. A Frame can hold a Region whose Nodes display Aggregation measures, Synthesis claims, or raw FieldNote excerpts — all drawn from the same graph by atomic ID. The presentation is not a copy of the data; it is a **view over the live graph**, assembled conceptually before any rendering decision is made.

This means the same concept model underlies both the analysis workflow and the UI that displays its results. There is no translation layer between "the data" and "the display." There is only the graph and its projections.

---

## Part 5 — Loom: a Complete Concept-First UI

*File: `services/static/loom/index.html`*

Loom is a single-page writing atelier that demonstrates every principle in this document applied end-to-end: the dual-axis input topology, the M1 edit layer, and the projection layer (M2 `ProjectionConcept`), all surfaced through a thin browser client that never touches the graph directly — it only sends JSON-RPC calls.

The goal of this section is to show, concretely and line by line, how a concept model becomes a UI.

---

### 5.1 The Three-Panel Architecture

```
┌───────────────────────────────────────────────────────┐
│  Header: wordmark · title · + Chunk · Write           │
├──────────────┬──────────────────────┬─────────────────┤
│  Left panel  │     Center           │   Right panel   │
│  ─────────   │  ─────────────────   │  ─────────────  │
│  Chunk list  │   Full-text editor   │  Axes / Tags    │
│  #1 head…    │   (textarea)         │  [emotion] …    │
│  #2 head…    │                      │  ─────────────  │
│  #3 head…    │                      │  Resonance ↕    │
│  ──────────  │                      │  Associations   │
│  Undo        │                      │  · related…     │
│  Redo        │                      │  · similar…     │
│  Restore     │                      │                 │
└──────────────┴──────────────────────┴─────────────────┘
```

Each panel maps directly to one or more concept model namespaces:

| Panel | Concept model | Key methods |
|---|---|---|
| Left — chunk list | `NoteConcept` edit layer | `loom.note.list`, `loom.note.move`, `loom.note.undo`, `loom.note.redo`, `loom.note.restore` |
| Center — editor | `NoteConcept` edit layer | `loom.note.add`, `loom.note.edit` |
| Right — resonance | `ProjectionConcept` | `proj.lens`, `proj.resonate` |
| Header — title | `NoteConcept` | `loom.note.rename`, `loom.note.new` |

> **Service namespace:** Loom uses `NoteConcept` under the `"loom"` namespace (see §5.5).
> All its kernel calls are prefixed `loom.note.*` to keep its session context — the
> active document pointer — completely isolated from the standalone Note app.

There is no application-level state beyond what the graph already knows. The UI is a projection of the concept model, not a parallel data store.

---

### 5.2 The `rpc()` Helper

The entire client-server boundary is a single 12-line function:

```javascript
async function rpc(method, params = {}) {
  const res = await fetch('/api/rpc', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${TOKEN}`,
    },
    body: JSON.stringify({ jsonrpc: '2.0', id: Date.now(), method, params }),
  });
  const j = await res.json();
  if (j.error) throw new Error(j.error.message || JSON.stringify(j.error));
  return j.result;
}
```

Every UI action is a call to this function. There is no REST API, no GraphQL schema, no custom endpoint. The concept model's operator vocabulary *is* the API.

---

### 5.3 Boot: Mounting Note and Projection

When the user authenticates, `boot()` runs before the app shell appears:

```javascript
async function boot() {
  // 1. Try to resume the session's active loom note
  let hasActiveNote = false;
  try {
    await rpc('loom.note.read', {});
    hasActiveNote = true;
  } catch { /* no active loom note */ }

  // 2. Create a new note only if none is active
  if (!hasActiveNote) {
    const r = await rpc('loom.note.new', { title: 'Untitled' });
    NOTE_ID = r.note_id || r.root_id;
  }

  // 3. Mount projection (open existing, create if none, degrade gracefully)
  try {
    const pl = await rpc('proj.ls', {});
    const projs = pl?.projections || [];
    if (projs.length > 0) {
      await rpc('proj.open', { proj_id: projs[0].proj_id });
      PROJ_ID = projs[0].proj_id;
    } else throw new Error('no proj');
  } catch {
    try {
      const pr = await rpc('proj.new', { title: 'Loom Projection' });
      PROJ_ID = pr.proj_id || pr.root_id;
      for (const axis of ['emotion', 'theme', 'time', 'space'])
        await rpc('proj.axis.add', { name: axis }).catch(() => {});
    } catch { /* proj unavailable — right panel degrades gracefully */ }
  }
}
```

Three design decisions are visible here:

**Session resumption before creation.** The kernel stores `loom:active_note_root` in the
session context. If the user has a Loom document open, `loom.note.read` succeeds and no
new document is created. The client only calls `loom.note.new` when there is genuinely no
active Loom note.

**Graceful degradation.** `ProjectionConcept` is not required. If proj creation fails,
`PROJ_ID` stays empty and the right panel degrades gracefully. The core writing loop
(`loom.note.add` / `loom.note.edit` / `loom.note.list`) works without it.

**Service namespace prefix.** Every call uses `loom.note.*` rather than bare `note.*`.
This tells the kernel to instantiate `NoteConcept` under the `"loom"` namespace, so
Loom's active document pointer (`loom:active_note_root`) is completely separate from the
Note app's (`active_note_root`). See §5.5.

---

### 5.4 Left Panel: the Chunk List as a Live View

The left panel is a live rendering of `note.list`:

```javascript
async function loadChunks() {
  const r = await rpc('note.list', {});
  chunks = r.chunks || [];   // [{id, version, head, role, order}]
  renderChunkList();
}
```

`note.list` returns chunks in *display order* — the edit layer if active, otherwise the input timeline. The client never needs to know which layer is in effect. It asks for the current view and gets it.

Each chunk item shows:
- `role` — the structural type (chunk, section, chapter…)
- `head` — first 80 characters of the current version's text
- `#N` — the display position

The `id` in each item is the stable **anchor** id. Even after ten edits, the id returned by `note.list` for a given chunk never changes. This is the anchor/version distinction from §2.13.1 made visible.

#### Drag-and-Drop Reorder → `note.move`

Each chunk item carries HTML5 drag attributes:

```html
<div class="chunk-item"
     draggable="true"
     ondragstart="dragStart(event, '${c.id}')"
     ondragover="dragOver(event)"
     ondrop="dragDrop(event, '${c.id}')">
```

On drop, the client computes the target position and calls:

```javascript
async function dragDrop(e, targetId) {
  const targetIdx = chunks.findIndex(c => c.id === targetId);
  const afterId = targetIdx > 0 ? chunks[targetIdx - 1].id : null;
  await rpc('note.move', { chunk_id: dragSourceId, after: afterId });
  await loadChunks();   // refresh from the new edit layer
}
```

`note.move` rebuilds the `edit:top/next` chain server-side. The client does not touch order state — it simply refreshes after the call. The single source of truth for order lives in the graph.

#### Undo / Redo / Restore buttons

```javascript
async function doUndo() {
  const r = await rpc('note.undo', {});
  if (r.status === 'nothing_to_undo') { toast('Nothing to undo'); return; }
  await loadChunks();
}
```

The three history controls map one-to-one to operators:

| Button | Operator | Effect |
|---|---|---|
| Undo | `note.undo` | Moves journal cursor back; rematerialises previous state |
| Redo | `note.redo` | Moves journal cursor forward |
| Restore | `note.restore` | Pushes `{order:null, active:{}}` — resets to input order |

Notice that "Restore" is also a journal entry: after calling `note.restore`, the Undo button returns the user to their last edited state. The UI does not need to track this — it falls out naturally from the journal design.

---

### 5.5 Center: Auto-Save → `note.edit` → `proj.extract`

The editor is a `<textarea>` with a 1.4-second debounce:

```javascript
function onEditorInput() {
  if (savePending) clearTimeout(savePending);
  savePending = setTimeout(flushSave, 1400);
}

async function flushSave() {
  const text = document.getElementById('editor').value;
  if (text === activeChunkText) return;   // no change

  await rpc('note.edit', { chunk_id: activeChunkId, text });
  activeChunkText = text;

  // Fire-and-forget: proj.extract connects the edit to the projection layer
  if (PROJ_ID) {
    rpc('proj.extract', { version_id: activeChunkId }).catch(() => {});
  }
}
```

The save chain has three stages:

```
User types  →  [1.4s silence]  →  note.edit  →  new version atom
                                      ↓
                                proj.extract  →  tags / axes updated
                                      ↓
                              Right panel refreshes
```

**`note.edit` creates a new content-addressed version atom** and records it in the journal. The old content is never lost — it lives in the `note:revises` chain. This means every autosave is a checkpoint: the user can undo back to any previous save.

**`proj.extract` is fire-and-forget.** If it fails or is unavailable, the save still succeeds. The right panel may be stale, but the writing session is not disrupted. This is the correct boundary: writing is a `NoteConcept` responsibility; analysis is a `ProjectionConcept` responsibility. They do not block each other.

Ctrl+S / Cmd+S bypasses the debounce:

```javascript
function handleEditorKey(e) {
  if ((e.ctrlKey || e.metaKey) && e.key === 's') {
    e.preventDefault();
    clearTimeout(savePending);
    flushSave();
  }
}
```

---

### 5.6 Right Panel: Rendering the Projection Layer

The right panel reads from `ProjectionConcept` — a different concept model entirely. This is the §8 rule at work: concepts do not call each other; the UI orchestrates them.

#### Tags from `proj.lens`

```javascript
async function loadTags(chunkId) {
  if (!PROJ_ID) { /* show "proj not connected" */ return; }
  const r = await rpc('proj.lens', { atom_id: chunkId }).catch(() => null);
  // r.axes: [{axis_id, label}, …]
  el.innerHTML = r.axes.map(ax =>
    `<span class="tag-chip">${escHtml(ax.label || ax.axis_id)}</span>`
  ).join('');
}
```

`proj.lens` returns which axes from the projection are active for this atom. The result reflects whatever `proj.extract` has written into the graph since the last save. The UI renders it as tag chips — no local tag state, no duplication.

#### Associations from `proj.resonate`

```javascript
async function loadAssoc(chunkId) {
  const scope = parseInt(document.getElementById('scope-slider').value, 10);
  const r = await rpc('proj.resonate', { atom_id: chunkId, scope }).catch(() => null);
  // r.results: [{relation, head, content}, …]
}
```

The scope slider directly controls the `scope` parameter passed to `proj.resonate`. Adjusting the slider fires a debounced re-call — the UI does not try to filter or sort results locally. The concept model owns the semantics.

---

### 5.7 Title Rename: `note.rename` and the Pointer Atom Pattern

Clicking the title in the header puts it in edit mode. On confirm:

```javascript
async function commitTitleEdit() {
  const newTitle = document.getElementById('title-edit-input').value.trim();
  await rpc('note.rename', { title: newTitle });
  document.getElementById('note-title-display').textContent = newTitle;
}
```

`note.rename` creates a new `note:title` pointer atom and swaps the `root → note:title` link (§2.13.9). The root atom's hash is unchanged — it cannot change, because it is content-addressed. The pointer atom carries the mutable display name.

The UI updates the header directly from the return value, without a round-trip to `note.list`. This is safe because the title is not part of `note.list`'s output — it is a separate `note:title` link resolved by `_display_title()`.

---

### 5.8 Writing Mode: UI State from Concept Model State

The "Write" button folds both side panels:

```javascript
function toggleWritingMode() {
  writingMode = !writingMode;
  document.body.classList.toggle('writing-mode', writingMode);
}
```

CSS does the rest:

```css
body.writing-mode #left-panel,
body.writing-mode #right-panel { width: 0; opacity: 0; pointer-events: none; }
body.writing-mode #editor-area { padding: 60px 120px 40px; max-width: 680px; }
```

Writing mode is local UI state — it does not exist in the concept model. This is the correct boundary. The concept model governs what *data* exists; the rendering surface governs how it *looks*. A narrower text column and hidden panels are rendering decisions, not graph decisions.

---

### 5.9 Service Namespace Isolation

`NoteConcept` is used by both the standalone Note app and Loom. Without isolation, both
services share the same session context key (`active_note_root`), causing whichever service
ran `note.new` last to overwrite the other's active document pointer.

**The fix:** `BaseConcept` accepts a `namespace` parameter. When `namespace="loom"`, all
session context keys are prefixed: `loom:active_note_root`, `loom:active_container_id`, etc.

The kernel handler for `loom.note.new`:

```python
def _handle_loom_note_new(self, rid, data, session):
    concept = NoteConcept(session, namespace="loom")   # isolated context
    ...
```

The general rule: **any UI service that reuses an existing concept class must declare a
namespace.** The namespace string becomes a prefix on the RPC method:

```
note.new       →  Note app  (no namespace)
loom.note.new  →  Loom      (namespace="loom")
```

The concept class implementation is shared; only the session context keys differ.
See the Scope Dimension Model §9 for the full specification.

---

### 5.10 Design Principles Demonstrated by Loom

| Principle | Where it appears in Loom |
|---|---|
| **Operator vocabulary = API** | Every button calls exactly one `rpc()` with one method name |
| **Single source of truth** | Order lives in `edit:top/next`; client never caches order state |
| **Anchor stability** | `chunk_id` in the chunk list never changes across edits |
| **Non-destructive editing** | Every autosave is an undo checkpoint via `note:revises` |
| **Graceful degradation** | Right panel works independently of left panel and center |
| **§8 isolation** | Note and Proj are orchestrated by the UI, never by each other |
| **Service namespace** | Loom uses `loom.note.*` — its document pointer never collides with Note app |
| **Rendering-agnostic model** | The same operators would work identically in a CLI, mobile app, or voice interface |

---

### 5.11 What Loom Does Not Do — and Why

**Loom does not manage concept model IDs.** `NOTE_ID` and `PROJ_ID` are session variables used only to confirm that the kernel has an active note and projection. All subsequent calls use the kernel's own session context — the kernel already knows which note is active from the `note.new` / `note.open` call.

**Loom does not buffer edits in memory.** There is no local document model, no shadow copy of the full text. The `activeChunkText` variable exists only to detect whether a save is needed (avoiding a round-trip for unchanged text). All authority lives in the graph.

**Loom does not resolve the `note:title` pointer.** On refresh, it does not re-fetch the title — it relies on the value already displayed from the last `note.rename` call or the `boot()` sequence. A production implementation would call a dedicated `note.title` read operator; this is left as an exercise.

**Loom does not handle concurrent editing.** The Akasha graph is append-only and content-addressed, so concurrent writes will not corrupt data — but the last `note.edit` call wins for `note:current`. Multi-session conflict resolution would require a merge operator, which is a separate concept model concern.

---

## Appendix — Link Type Reference for NoteConcept

### Input Layer (immutable)

| Link type | Direction | Meaning |
|---|---|---|
| `sys:top` | root → first_anchor | Permanent pointer to timeline head |
| `sys:bottom` | root → last_anchor | Floating pointer to timeline tail |
| `sys:next` | anchor → next_anchor | Forward input-order traversal |
| `sys:previous` | anchor → prev_anchor | Backward input-order traversal |
| `sys:contains` | container → child | Vertical hierarchy (parent owns child) |
| `sys:part_of` | child → container | Reverse vertical link |
| `sys:derived_from` | content_atom → concept_word_atom | Instance → general concept (one-directional) |

### Edit Layer (rebuildable)

| Link type | Direction | Meaning |
|---|---|---|
| `edit:top` | root → first_anchor | Edit-order head (absent = fall back to `sys:top`) |
| `edit:bottom` | root → last_anchor | Edit-order tail |
| `edit:next` | anchor → next_anchor | Forward display-order traversal |
| `edit:previous` | anchor → prev_anchor | Backward display-order traversal |
| `note:current` | anchor → version_atom | Points anchor to its current content version |
| `note:revises` | version_atom → prev_version | History chain (newest → oldest) |
| `note:edit_journal` | root → journal_atom | JSON undo/redo state (history + cursor) |
| `note:title` | root → title_atom | Mutable display name (overrides root meta title) |

---

## Appendix — Set Namespace Reference for NoteConcept

| Set name | Members |
|---|---|
| `set:note:{root_id}` | All content atoms for this document |
| `set:note:{root_id}:sections` | Section and chapter atoms |
| `set:note:{root_id}:paragraphs` | Paragraph atoms |
| `set:concept:{root_id}` | Concept-word vocabulary atoms |
| `set:section:{sec_id}` | Content atoms belonging to a specific section |
| `set:paragraph:{para_id}` | Content atoms belonging to a specific paragraph |
