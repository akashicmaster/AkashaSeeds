# Akasha Concept Model — Contributor & LLM Specification

> **Audience**: Contributors, LLM co-developers  
> **Purpose**: Everything you need to build a new Concept Model for `lib/akasha/concepts/`  
> **Version**: 1.3 — Akasha kernel series `seeds`

---

## 1. What Is a Concept Model?

A **Concept Model** is a higher-order graph constructor that lives on top of the raw Cortex.
The Cortex knows only atoms (chunks) and links — it has no understanding of "a document" or
"a task list" or "a research thread". Concept Models give semantic shape to those raw nodes.

The dispatch chain is:

```
Shell command  ──►  kernel dispatch()  ──►  ConceptModel.dispatch(op, params)
                                                    │
                                          op_*(self, **params)
                                                    │
                                         cortex.put_chunk / put_link / …
```

Every concept model must:

1. Inherit from `BaseConcept`.
2. Expose all behaviour exclusively through `op_*` methods.
3. Write to the Cortex only via `self.cortex.*` or `self.create_structured_chunk()`.
4. Never touch the filesystem, the shell, or the network directly.
5. Call `self._require_concept()` at the top of every `op_*` method that requires an
   initialized instance (i.e. all operators except `op_new`).

---

## 2. BaseConcept API Contract

**File**: `lib/akasha/concepts/base.py`

### 2.1 Constructor

```python
BaseConcept(session, concept_id: Optional[str] = None, namespace: Optional[str] = None)
```

| Attribute | Source | Description |
|-----------|--------|-------------|
| `self.session` | arg | The kernel `Session` object. Carries `client_id`, `active_scopes`, and a context dict. |
| `self.cortex` | `session.cortex` or `session.local_cortex` | `AkashaEngine` instance. All Cortex I/O goes here. |
| `self.concept_id` | arg | Stable string ID for this concept instance (a chunk hash or an alias). `None` until `op_new` sets it. |
| `self.set_name` | derived | `f"set:concept:{self.concept_id}"` — the general concept catalog set. `None` if `concept_id` not yet set. |
| `self.namespace` | arg | Optional string (e.g. `"loom"`). When set, all session context keys are prefixed with `"{namespace}:"`. See §2.3. |

Staging state (see §2.7):

```python
self.staged_changes: Dict[str, Dict]   # key → {content, meta, action_type}
self.staged_links:   List[Tuple]        # (src, dst, rel, w)
self.undo_stack:     List[Dict]
self.redo_stack:     List[Dict]
```

### 2.2 Dispatch Convention

```python
def dispatch(self, operator: str, params: Dict[str, Any]) -> Any
```

`"foo.bar"` → calls `self.op_foo_bar(**params)`.

- The kernel calls this. Never call `dispatch` from inside a concept.
- All `op_*` methods must accept their parameters as **keyword arguments**.
- If an operator is not implemented, `dispatch` raises `NotImplementedError`.

### 2.3 Session Accessors

```python
@property
def allowed_scopes(self) -> List[str]
```

Returns `session.active_scopes` — the IAM scope list computed for the authenticated client.
Pass this whenever a Cortex method takes a `scopes` or `requester_scopes` argument.

Reading and writing session context (for stateful concepts) — always use `_ctx_key()`:

```python
ctx_val = getattr(self.session, "get_context", lambda k: None)(self._ctx_key("some_key"))
if hasattr(self.session, "set_context"):
    self.session.set_context(self._ctx_key("some_key"), value)
```

`_ctx_key(key)` returns `"{namespace}:{key}"` when a namespace is active, or bare `key` when not.
Never pass raw string literals to `get_context` / `set_context` — always route through `_ctx_key`.

### 2.4 Concept Guard — `_require_concept`

```python
def _require_concept(self)
```

Raises `RuntimeError` if `self.concept_id` is `None`. Call at the top of every `op_*`
method that requires the concept to be initialized. This is defined in `BaseConcept` — do
not redefine it in subclasses.

```python
def op_add(self, text: str) -> Dict[str, Any]:
    self._require_concept()   # ← required in every op_* except op_new
    ...
```

### 2.5 Node Registration

```python
def register_concept_node(self, key: str, subset_suffix: Optional[str] = None)
```

Adds `key` to:
- `self.set_name` (`set:concept:{concept_id}`) — the general concept catalog for this instance
- `f"{self.set_name}:{subset_suffix}"` (if suffix provided)

This is the canonical way to populate the **concept catalog set**, which `serialize_concept`
uses for export and which deletion sweeps scan. Note: this registers the concept-word atoms,
not the content atoms (see §3.3 for the distinction).

### 2.6 Primitive Write — `create_structured_chunk`

```python
def create_structured_chunk(
    self,
    content: str,
    role: str,
    author_id: str,
    scopes: List[str],
    parent_set_id: Optional[str] = None
) -> Dict[str, Any]
```

Returns `{"chunk_id": str, "chunk_set": f"set:chunk:{chunk_id}"}`.

Internally:
1. Calls `cortex.put_chunk(content, meta, author, scopes)` — immediate write.
2. Registers the new node to `self.set_name` via `register_concept_node`.
3. Also registers to `parent_set_id` if given.
4. Creates `set:chunk:{chunk_id}` — a private inner-element bucket for this atom.

This is the **preferred** entry point for materializing content atoms; it handles all
standard housekeeping automatically.

> **Note for NoteConcept subclasses**: `create_structured_chunk` calls
> `register_concept_node` which adds the content atom to `set:concept:*`. In the dual-
> namespace design (§3.3), content atoms should not be in `set:concept:*`. Use
> `_register_to_package` with `concept_word` for structural nodes, and call
> `create_structured_chunk` only for raw content chunks where the dual-namespace rule
> does not apply (the `parent_set_id` correctly routes them to `set:note:*`).

### 2.7 Span Annotations

```python
def annotate_span(
    self,
    parent_chunk_key: str,
    start_char: int,
    end_char: int,
    annotation_text: str,
    role: str = "annotation",
    target_concept_id: Optional[str] = None
) -> str   # returns annotation atom key

def get_span_annotations(self, parent_chunk_key: str) -> List[Dict[str, Any]]
```

Span annotations map to character offsets within a parent atom.
Links created: `sys:has_annotation_span`, `sys:included`, optionally `sys:associated_with`.
`get_span_annotations` returns results sorted by `start` offset.

### 2.8 Transactional Staging

In-memory undo/redo before a final bulk commit. Use for interactive multi-step editing.

| Method | Effect |
|--------|--------|
| `stage_change(key, content, meta, action_type)` | Queue a node mutation |
| `stage_link(src, dst, rel, w)` | Queue a link creation |
| `undo()` | Pop undo stack, revert staged state |
| `redo()` | Re-apply last undone action |
| `commit_staged()` | Flush all staged changes to Cortex; handles hash-remapping |

`commit_staged` returns `{"status", "nodes_written", "links_woven", "mutations"}`.

> **Boundary warning**: Staging is per-concept in-process state. It is **not** a Harmonia
> workspace transaction. If a concept is used inside a JCL job and the job rolls back,
> staged commits that already reached the Cortex will **not** be reversed. Stage only
> within a single JCL step, or call `commit_staged` before the Harmonia rollback boundary.

### 2.9 Serialization

```python
def serialize_concept(self) -> Dict[str, Any]
def hydrate_concept(self, schema_data: Dict[str, Any]) -> str
def export_concept(self, format_type: str, **kwargs) -> Any
def import_concept(self, raw_data: Any, format_type: str, **kwargs) -> str
```

`serialize_concept` produces the canonical transfer schema:

```json
{
  "specification": "akasha_concept_schema_v1.0",
  "concept_type": "MyConceptClass",
  "concept_id": "...",
  "atoms": { "<key>": { "content": "...", "meta": {...} } },
  "links": [ { "src": "...", "dst": "...", "rel": "...", "w": 1.0 } ]
}
```

Export/import for `"json"` format is built-in. Other formats (`"markdown"`, `"pdf"`) require
a plugin registered at `self.cortex._plugins["transform.export.<format>"]`.

---

## 3. NoteConcept — Reference Implementation

**File**: `lib/akasha/concepts/note.py`

NoteConcept is the canonical reference for a **stateful, structured concept** with dual-
namespace set management and a sequential timeline topology.

### 3.1 Auto-Mount Pattern

```python
def __init__(self, session, concept_id=None):
    super().__init__(session, concept_id)
    if not self.concept_id:
        active_root = getattr(self.session, "get_context", lambda k: None)("active_note_root")
        if active_root:
            self.concept_id = active_root
            self.set_name = f"set:concept:{self.concept_id}"
```

If the kernel doesn't supply a `concept_id`, NoteConcept reads the session context key
`"active_note_root"`. This allows commands like `n.add` to work without explicitly
referencing the note — the session remembers which note is open.

**Pattern**: Use session context for "active resource" tracking. `op_new` sets it;
every subsequent operator reads it via `_require_concept` + auto-mount.

### 3.2 Dual Set Namespace

NoteConcept uses two orthogonal set namespaces that serve different purposes.
The **same physical atom must never appear in both**.

| Namespace | Contents | Purpose |
|-----------|----------|---------|
| `set:note:{root_id}` | Content atoms — the actual sections, paragraphs, and chunks of this note | Note-model scope: reading, traversal, sequential output |
| `set:concept:{root_id}` | Concept-word atoms — general vocabulary terms like `"section"`, `"paragraph"`, `"document"` | General concept catalog: serialization, cross-model vocabulary |

Note-scope set helpers:

```python
def _get_set_name(self, suffix: str = "") -> str:
    return f"set:note:{self.concept_id}:{suffix}" if suffix else f"set:note:{self.concept_id}"
```

Sub-sets created at initialization:
- `set:note:{root_id}` — master content membership
- `set:note:{root_id}:sections`
- `set:note:{root_id}:paragraphs`
- `set:section:{sec_id}`, `set:paragraph:{para_id}` — per-node inner buckets

### 3.3 Concept-Word Atoms and One-Directional Derivation

General concept-word atoms represent structural roles (e.g. `"section"`, `"paragraph"`) as
standalone vocabulary atoms, independent of any particular note document.

```
content_atom("Introduction", role=section)
        │
        │  sys:derived_from          (one-directional)
        ▼
concept_word_atom("section", type=concept_word)
        │
    aliased: concept:word:section
    registered: set:concept:{root_id}
```

The note model's usage of "section" derives from the general concept, but may differ in
meaning or scope. The reverse link is **intentionally absent** — the general concept does
not reference back into any specific note.

**Implementation**:

```python
_CONCEPT_WORD_ALIAS_PREFIX = "concept:word:"

def _get_or_create_concept_word(self, word: str) -> str:
    alias = f"{_CONCEPT_WORD_ALIAS_PREFIX}{word}"
    existing = self.cortex.resolve_alias(alias)
    if existing:
        return existing
    # Create a new general concept-word atom in the user's private scope
    key = self.cortex.put_chunk(
        content=word,
        meta={"type": "concept_word", "word": word, "concept_model": "note", ...},
        author=author_id, scopes=scopes
    )
    self.cortex.set_alias(key, alias)
    return key

def _register_to_package(self, key: str, subset_suffix=None, concept_word=None):
    # 1. Content atom → note-scope only
    self.cortex.add_to_set(self._get_set_name(), key)
    if subset_suffix:
        self.cortex.add_to_set(self._get_set_name(subset_suffix), key)
    # 2. Concept-word atom → concept catalog (separate atom, one-directional link)
    if concept_word:
        cw_key = self._get_or_create_concept_word(concept_word)
        self.register_concept_node(cw_key)         # → set:concept:{root_id}
        self.cortex.put_link(key, cw_key, "sys:derived_from", author=author_id)
```

`concept_word` values passed by each operator:

| Operator | `concept_word` |
|----------|---------------|
| `op_new` | `"document"` |
| `op_section` | role value (e.g. `"section"`, `"chapter"`, `"appendix"`) |
| `op_paragraph` | `"paragraph"` |
| `op_add_chunk` | _(none — content chunks use `create_structured_chunk` directly)_ |

### 3.4 Dual Topology — Timeline and Hierarchy

NoteConcept maintains two orthogonal structures simultaneously:

```
HORIZONTAL (timeline)
    root ──sys:top──► node_A ──sys:next──► node_B ──sys:next──► node_C
    root ──sys:bottom────────────────────────────────────────────► node_C
    (each node also carries sys:previous pointing back)

VERTICAL (hierarchy)
    root ──sys:contains──► chapter_1 ──sys:contains──► section_1_1
    section_1_1 ──sys:part_of──► chapter_1
```

The horizontal timeline enables flat sequential reading (`op_get_sequential_text`).
The vertical hierarchy enables TOC traversal (`op_toc`).

`_append_to_timeline` manages the `sys:bottom` floating pointer using the Cortex
abstraction layer — **no raw SQL**:

```python
def _append_to_timeline(self, node_id: str, author_id: str):
    tail_links = self.cortex.get_adjacent_links(self.concept_id, "sys:bottom")
    if not tail_links:
        self.cortex.put_link(self.concept_id, node_id, "sys:top", author=author_id)
    else:
        last_node_id = tail_links[0][0]
        self.cortex.put_link(last_node_id, node_id, "sys:next", author=author_id)
        self.cortex.put_link(node_id, last_node_id, "sys:previous", author=author_id)
        self.cortex.remove_link(self.concept_id, last_node_id, "sys:bottom")
    self.cortex.put_link(self.concept_id, node_id, "sys:bottom", author=author_id)
```

### 3.5 Operator Inventory

| Shell command | Kernel method | `op_*` method | Parameters |
|---------------|---------------|---------------|------------|
| `n.new` | `note.new` | `op_new` | `title: str`, `author?: str`, `isbn?: str` |
| `n.add` | `note.add` | `op_add_chunk` | `text: str`, `role?: str` |
| `n.sec` / `n.chap` | `note.section` | `op_section` | `title: str`, `role?: str` |
| `n.para` | `note.paragraph` | `op_paragraph` | `category?: str` |
| `n.toc` | `note.toc` | `op_toc` | _(none)_ |
| `n.read` | `note.read` | `op_get_sequential_text` | _(none)_ |
| `n.rm` | `note.rm` | `op_delete` | _(none)_ |

---

## 4. Building a New Concept Model — Step-by-Step

### 4.1 Canonical Template

The template below reflects all patterns established across the bundled concept
models. Copy it verbatim and search-replace `mything` / `MyThing` / `mt`.

```python
"""
MyThing Concept Model.

Brief description of what this concept models and its topology.

Namespace contract (two-namespace rule):
  - Content atoms  → set:mything:{concept_id}  AND  set:mything:{concept_id}:{subset}
  - Concept-word atom → set:concept:{concept_id}  (concept catalog scope)
"""

import time
import logging
from typing import List, Dict, Any, Optional

from lib.akasha.concepts.base import BaseConcept

logger = logging.getLogger("Harmonia.Concept.MyThing")

# Session context key — must be unique across all concept models
CONTEXT_KEY_ACTIVE = "active_mything_root"
# Global index set — all root IDs across all sessions
INDEX_SET = "set:mything:index"
_CONCEPT_WORD_ALIAS_PREFIX = "concept:word:"


class MyThingConcept(BaseConcept):
    """One-line description of what this concept represents."""

    # ── Plugin registry contract ───────────────────────────────────────────────
    CONCEPT_PREFIX = "mt"
    CONCEPT_METHODS = {
        "new":  {"op": "op_new"},
        # coerce normalises both "mything_id" (API return) and "mt_id" (shorthand)
        "open": {"op": "op_open",
                 "coerce": lambda d: {
                     "mything_id": d.get("mything_id") or d.get("mt_id", ""),
                 }},
        "ls":   {"op": "op_list_all"},   # list ALL instances (scans INDEX_SET)
        "add":  {"op": "op_add"},
        "list": {"op": "op_list"},       # list structure of the ACTIVE instance
        "rm":   {"op": "op_delete"},
    }

    # ── Constructor ───────────────────────────────────────────────────────────

    def __init__(self, session: Any, concept_id: Optional[str] = None, namespace: Optional[str] = None):
        super().__init__(session, concept_id, namespace=namespace)
        # Auto-mount: if kernel didn't pass a concept_id, recover from session context
        if not self.concept_id:
            stored = getattr(self.session, "get_context", lambda k: None)(self._ctx_key(CONTEXT_KEY_ACTIVE))
            if stored:
                self.concept_id = stored
                self.set_name = f"set:concept:{self.concept_id}"

    # ── Private helpers ───────────────────────────────────────────────────────

    def _mt_set(self, suffix: Optional[str] = None) -> str:
        base = f"set:mything:{self.concept_id}"
        return f"{base}:{suffix}" if suffix else base

    def _author_and_scopes(self):
        author_id = getattr(self.session, "client_id", "system")
        scopes = [f"owner:user_{author_id}", f"view:user_{author_id}"]
        return author_id, scopes

    def _get_or_create_concept_word(self, word: str) -> str:
        alias = f"{_CONCEPT_WORD_ALIAS_PREFIX}{word}"
        existing = self.cortex.resolve_alias(alias)
        if existing:
            return existing
        author_id, scopes = self._author_and_scopes()
        key = self.cortex.put_chunk(
            content=word,
            meta={"type": "concept_word", "word": word,
                  "concept_model": "mything", "created_at": time.time()},
            author=author_id, scopes=scopes,
        )
        self.cortex.set_alias(key, alias)
        return key

    def _register(self, key: str, subset_suffix: Optional[str] = None,
                  concept_word: Optional[str] = None) -> None:
        """Dual-namespace: content atom → mything-scope; concept-word → catalog."""
        author_id, _ = self._author_and_scopes()
        self.cortex.add_to_set(self._mt_set(), key)          # main content set
        if subset_suffix:
            self.cortex.add_to_set(self._mt_set(subset_suffix), key)
        if concept_word:
            cw_key = self._get_or_create_concept_word(concept_word)
            self.register_concept_node(cw_key)               # concept catalog set
            self.cortex.put_link(key, cw_key, "sys:derived_from", author=author_id)

    def _require_access(self, atom_id: str, label: str = "Atom") -> None:
        """Access guard: raises RuntimeError if atom_id is not readable by this session."""
        if not self.cortex.check_access(atom_id, self.allowed_scopes):
            raise RuntimeError(f"{label} not accessible: {atom_id[:12]}")

    def _visible_members(self, suffix: str) -> List[str]:
        """Return accessible members of a subset, filtered by IAM."""
        return [
            k for k in self.cortex.get_collection_members(self._mt_set(suffix))
            if self.cortex.check_access(k, self.allowed_scopes)
        ]

    # ── Operators ─────────────────────────────────────────────────────────────

    def op_new(self, title: str) -> Dict[str, Any]:
        """[mt.new] Create a new MyThing root."""
        # op_new is the only operator that does NOT call _require_concept
        author_id, scopes = self._author_and_scopes()

        root_id = self.cortex.put_chunk(
            content=f"[ MyThing: {title} ]",
            meta={
                "type":       "concept",    # always "concept" on roots
                "concept":    "mything",    # validated in op_open — use this field
                "role":       "root",
                "title":      title,
                "created_at": time.time(),
            },
            author=author_id, scopes=scopes,
        )

        self.concept_id = root_id
        self.set_name   = f"set:concept:{self.concept_id}"

        # ORDERING RULE: create ALL sets before any call that writes to them.
        self.cortex.create_set(self.set_name)               # concept catalog set
        self.cortex.create_set(self._mt_set())              # main content set
        self.cortex.create_set(self._mt_set("items"))       # per-subset sets
        self.cortex.create_set(INDEX_SET)                   # global index (idempotent)
        self.cortex.add_to_set(INDEX_SET, root_id)

        # Register AFTER sets exist (no concept_word — root lives in content set only)
        self._register(root_id)

        if hasattr(self.session, "set_context"):
            self.session.set_context(self._ctx_key(CONTEXT_KEY_ACTIVE), root_id)

        logger.info("[MyThingConcept] Created '%s' (%s)", title, root_id[:8])
        return {"status": "created", "mything_id": root_id, "title": title}

    def op_open(self, mything_id: str) -> Dict[str, Any]:
        """[mt.open] Mount an existing MyThing as the session's active instance."""
        # Validate using "concept" field, NOT "type" (all roots have type="concept")
        meta = self.cortex.get_meta(mything_id)
        if not meta or meta.get("concept") != "mything":
            raise RuntimeError(f"Atom '{mything_id[:12]}' is not a mything root.")
        self.concept_id = mything_id
        self.set_name   = f"set:concept:{self.concept_id}"
        if hasattr(self.session, "set_context"):
            self.session.set_context(self._ctx_key(CONTEXT_KEY_ACTIVE), mything_id)
        return {"status": "opened", "mything_id": mything_id, "title": meta.get("title", "")}

    def op_list_all(self) -> Dict[str, Any]:
        """[mt.ls] List all MyThing roots accessible to this session."""
        members = self.cortex.get_collection_members(INDEX_SET)
        items = []
        for key in members:
            if not self.cortex.check_access(key, self.allowed_scopes):
                continue
            meta = self.cortex.get_meta(key) or {}
            if meta.get("concept") != "mything":
                continue
            items.append({"mything_id": key, "title": meta.get("title", ""),
                          "created_at": meta.get("created_at", 0)})
        items.sort(key=lambda x: x.get("created_at", 0), reverse=True)
        return {"mythings": items, "count": len(items)}

    def op_add(self, text: str) -> Dict[str, Any]:
        """[mt.add] Add a content item to the active MyThing."""
        self._require_concept()
        author_id, scopes = self._author_and_scopes()

        item_id = self.cortex.put_chunk(
            content=text,
            meta={"type": "mt_item", "created_at": time.time()},
            author=author_id, scopes=scopes,
        )
        # Sub-atom goes into BOTH main set and sub-set (never sub-set only)
        self._register(item_id, subset_suffix="items", concept_word="item")
        self.cortex.put_link(self.concept_id, item_id, "mt:item", author=author_id)

        return {"status": "added", "item_id": item_id}

    def op_list(self) -> Dict[str, Any]:
        """[mt.list] Return structural inventory of the active MyThing."""
        self._require_concept()
        return {
            "mything_id": self.concept_id,
            "items":      self._visible_members("items"),
        }

    def op_delete(self) -> Dict[str, Any]:
        """[mt.rm] Delete the active MyThing root and clear session context."""
        self._require_concept()
        target = self.concept_id
        self.cortex.drop_chunk(target, requester_scopes=self.allowed_scopes)
        if hasattr(self.session, "set_context"):
            self.session.set_context(CONTEXT_KEY_ACTIVE, None)
        return {"status": "deleted", "mything_id": target}
```

Key differences from a naive implementation, all enforced by the patterns above:

- **`CONCEPT_PREFIX` + `CONCEPT_METHODS`** at class level — required for auto-discovery.
- **`__init__` auto-mount** — always override to restore session context.
- **`coerce` on `open`** — normalise the param name to match what the API returns.
- **`ls` → `op_list_all`** scans `INDEX_SET`; **`list`** → `op_list` returns the current instance's structure. Both are mandatory.
- **Set creation order in `op_new`** — ALL sets created before ANY `_register` or `register_concept_node` call.
- **`INDEX_SET`** created with `create_set` (idempotent) before `add_to_set`.
- **`_register`** adds to BOTH main set AND sub-set.
- **`_require_access`** called on every input atom ID supplied by the caller.
- **`_visible_members`** filters by IAM — never return raw `get_collection_members` output.
- **Root meta uses `"concept": "mything"`** — `op_open` validates on this field.
- **Sub-atom `type` uses `"{prefix}_{role}"` naming** (e.g. `"mt_item"`).
- **`op_delete` clears session context** (sets to `None`).

See §4.3 for the full bug catalogue that motivated these patterns.

### 4.2 Pre-Submit Checklist

Use this before opening a PR or handing a concept model off for review.

**Structure**
- [ ] Inherits `BaseConcept`; no methods copied from it.
- [ ] `CONCEPT_PREFIX` (str) and `CONCEPT_METHODS` (dict) defined at class level.
- [ ] `__init__` overrides and restores `CONTEXT_KEY_ACTIVE` from session.
- [ ] All public behaviour exposed as `op_*` methods accepting keyword arguments only.

**`op_new`**
- [ ] Root meta has `"type": "concept"`, `"concept": "<name>"`, `"role": "root"`.
- [ ] `self.cortex.create_set(self.set_name)` called BEFORE any `_register` call.
- [ ] `INDEX_SET` created with `create_set` (idempotent) before `add_to_set`.
- [ ] All content sets (`_mt_set()`, `_mt_set("items")`, …) created before any writes.
- [ ] `_register` or `register_concept_node` called ONLY AFTER all sets exist.
- [ ] Session context written via `session.set_context(CONTEXT_KEY_ACTIVE, root_id)`.
- [ ] Return dict includes all key fields (`title`, etc.) that `op_open` would return.

**`op_open`**
- [ ] Validates with `meta.get("concept") != "<name>"`, not `meta.get("type")`.
- [ ] `get_meta` return guarded against `None`: `meta = ... or {}`.
- [ ] `coerce` lambda in `CONCEPT_METHODS["open"]` normalises both the short ID key
     (e.g. `mt_id`) and the full API return key (e.g. `mything_id`).
- [ ] Writes `CONTEXT_KEY_ACTIVE` to session on success.

**`op_list_all` (mapped to `ls`)**
- [ ] Scans `INDEX_SET`, not `self.set_name`.
- [ ] Filters each member with `check_access` before including in results.
- [ ] Skips members whose `meta.get("concept")` doesn't match.

**Sub-atom operators (`op_add_*`)**
- [ ] Every input atom ID from the caller guarded with `_require_access(id, label)`.
- [ ] Sub-atom added to BOTH main set (`_mt_set()`) AND sub-set (`_mt_set("items")`).
- [ ] Sub-atom `type` uses `"{prefix}_{role}"` convention (e.g. `"mt_item"`).

**`op_list` / `op_map`**
- [ ] Uses `_visible_members(suffix)` (with `check_access` filter), never raw
     `get_collection_members`.

**`op_delete` (mapped to `rm`)**
- [ ] Calls `drop_chunk` with `requester_scopes=self.allowed_scopes`.
- [ ] Sets `CONTEXT_KEY_ACTIVE` to `None` in session.

**General**
- [ ] Every `op_*` except `op_new` calls `self._require_concept()` as first statement.
- [ ] All `put_chunk` calls pass `scopes` derived from `session.client_id`.
- [ ] `CONTEXT_KEY_ACTIVE` and `INDEX_SET` defined as module-level constants.
- [ ] No filesystem, network, or shell access.
- [ ] No import of `kernel.py` or `router.py`.
- [ ] IAM routing added to `_METHOD_TO_ACTION` in `kernel.py` (§7.2).

---

### 4.3 Common Implementation Bugs

The following bugs have been encountered in real concept model implementations.
Each entry gives the symptom, the root cause, and the fix.

---

#### B1 — Set creation ordering crash

**Symptom:** `op_new` raises a Cortex error about a missing set, or concept-word
atoms are registered into a non-existent set.

**Root cause:** `self.cortex.create_set(self.set_name)` was called AFTER
`_register_to_package` or `register_concept_node` — which write to `self.set_name`.

**Fix:** Create ALL sets (`self.set_name`, `INDEX_SET`, all content sets) before any
call that writes to them.

```python
# ✗ WRONG — set_name not yet created when _register runs
self._register(root_id)
self.cortex.create_set(self.set_name)

# ✓ CORRECT — all sets created first
self.cortex.create_set(self.set_name)
self.cortex.create_set(self._mt_set())
self.cortex.create_set(INDEX_SET)
self._register(root_id)   # safe now
```

---

#### B2 — Sub-atom not in main content set

**Symptom:** `op_list` / `op_map` returns empty results even after adding items.
The sub-set (`set:mt:{id}:items`) has members but `set:mt:{id}` is empty.

**Root cause:** `_register` only added the atom to the sub-set, skipping the main
content set.

**Fix:** Always add to BOTH main set and sub-set.

```python
# ✗ WRONG — main set never updated
self.cortex.add_to_set(self._mt_set("items"), item_id)

# ✓ CORRECT
self.cortex.add_to_set(self._mt_set(),         item_id)   # main set
self.cortex.add_to_set(self._mt_set("items"),  item_id)   # sub-set
```

---

#### B3 — `op_open` validates on `type` instead of `concept`

**Symptom:** `op_open` raises "is not a mything root" for valid roots, OR passes
silently for the wrong atom type.

**Root cause:** All concept roots have `"type": "concept"`. The discriminating field
is `"concept"`.

**Fix:**

```python
# ✗ WRONG — all roots have type "concept"; this never catches wrong roots
if meta.get("type") != "mything_root":
    raise RuntimeError(...)

# ✓ CORRECT
if not meta or meta.get("concept") != "mything":
    raise RuntimeError(...)
```

---

#### B4 — `op_open` `coerce` missing

**Symptom:** `mt.open` fails with a parameter error when called with the ID key
returned by `mt.new` (e.g. `{"mything_id": "..."}` fails because `op_open` expects
`{"mt_id": "..."}`).

**Root cause:** `op_new` returns `"mything_id"` but `op_open` takes `mt_id` as its
parameter, and no `coerce` lambda normalises the name.

**Fix:** Add a `coerce` lambda in `CONCEPT_METHODS["open"]`:

```python
"open": {"op": "op_open",
         "coerce": lambda d: {
             "mything_id": d.get("mything_id") or d.get("mt_id", ""),
         }},
```

---

#### B5 — Missing access guard on input atoms

**Symptom:** A caller can pass any atom ID and have it silently added to the
concept, bypassing IAM — a security and data-integrity issue.

**Root cause:** `op_add_*` methods do not call `_require_access` on the IDs
supplied by the caller.

**Fix:** Call `_require_access(atom_id, "label")` on every user-supplied atom ID
before using it.

```python
def op_add_item(self, ref_id: str) -> Dict[str, Any]:
    self._require_concept()
    self._require_access(ref_id, "Item atom")   # ← required
    ...
```

---

#### B6 — `get_meta` return not guarded against `None`

**Symptom:** `AttributeError: 'NoneType' object has no attribute 'get'` when
accessing metadata on a root or any atom that may not exist.

**Root cause:** `self.cortex.get_meta(key)` returns `None` if the atom is not found.

**Fix:**

```python
# ✗ WRONG
root_meta = self.cortex.get_meta(self.concept_id)
allowed = root_meta.get("context_universes", [])   # crashes if None

# ✓ CORRECT
root_meta = self.cortex.get_meta(self.concept_id) or {}
allowed = root_meta.get("context_universes", [])
```

---

#### B7 — `_members` returns inaccessible atoms

**Symptom:** `op_list` / `op_map` leaks atom IDs that the current session is not
authorised to see.

**Root cause:** Raw `get_collection_members` output returned directly, without
`check_access` filtering.

**Fix:**

```python
# ✗ WRONG
return list(self.cortex.get_collection_members(self._mt_set("items")))

# ✓ CORRECT
return [
    k for k in self.cortex.get_collection_members(self._mt_set("items"))
    if self.cortex.check_access(k, self.allowed_scopes)
]
```

---

#### B8 — Root meta missing `concept` field

**Symptom:** `op_open` validation always fails (or passes incorrectly); concept catalog
queries return unexpected atoms.

**Root cause:** Root atom created without `"concept": "<name>"` in meta — relying
only on `"type": "concept_root"` or a custom type string.

**Fix:** Root `put_chunk` meta must always contain:

```python
meta={
    "type":    "concept",    # always literal "concept"
    "concept": "mything",   # the discriminating field
    "role":    "root",
    ...
}
```

---

#### B9 — Missing `__init__` auto-mount

**Symptom:** A second call in the same session (e.g. `mt.add`) fails with "No active
concept" even though `mt.new` was called moments before.

**Root cause:** The subclass does not override `__init__`, so `BaseConcept.__init__`
never reads `CONTEXT_KEY_ACTIVE` from the session — the session context written by
`op_new` is never recovered.

**Fix:** Always override `__init__`:

```python
def __init__(self, session, concept_id=None):
    super().__init__(session, concept_id)
    if not self.concept_id:
        stored = getattr(self.session, "get_context", lambda k: None)(CONTEXT_KEY_ACTIVE)
        if stored:
            self.concept_id = stored
            self.set_name = f"set:concept:{self.concept_id}"
```

---

#### B10 — Missing `ls` or `rm`

**Symptom:** Users cannot discover existing instances or delete them; the concept
is inconsistent with other models in the shell.

**Root cause:** `op_list_all` and/or `op_delete` not implemented.

**Fix:** Always implement both, mapped as `"ls"` and `"rm"` in `CONCEPT_METHODS`.

---

#### B11 — Inconsistent sub-atom type naming

**Symptom:** Filtering by `meta.get("type")` in client code is unreliable; types
from different concept models collide (e.g. two models both use `"node"`).

**Root cause:** Sub-atom `type` field uses a generic name instead of a namespaced one.

**Fix:** Always prefix the type with the concept prefix:
`"mt_item"`, `"pres_frame"`, `"agg_measure"`, `"synth_code"`, etc.

---

## 5. Set Namespace Design

### 5.1 The Two-Namespace Rule

Every concept model uses two categories of sets, each holding a different kind of atom:

| Category | Default naming | Populated by | Purpose |
|----------|---------------|--------------|---------|
| **Content set** | `set:<concept>:{root_id}` | `_register_to_package`, `create_structured_chunk` with `parent_set_id` | Stores the actual content atoms (text, structure) of this concept instance |
| **Concept catalog** | `set:concept:{root_id}` (`self.set_name`) | `register_concept_node` | Stores general concept-word atoms; used by `serialize_concept` |

**Rule**: A physical atom belongs to exactly one category. The same atom is never in both.

**Root atom corollary**: The concept root atom belongs to the content set only. Never pass `concept_word=` when calling `_register(root_id)` — the root is not a concept-word node.

### 5.2 Concept-Word Atoms

Concept-word atoms are stable, reusable vocabulary atoms. They represent structural or
semantic roles as general concepts, independent of any specific instance. Properties:

- Content: the role word itself (e.g. `"section"`)
- Meta: `{"type": "concept_word", "word": "section", "concept_model": "note"}`
- Alias: `concept:word:section` — stable lookup key across sessions
- Scope: user's private scope (can be promoted to collective by LIBRARIAN)
- Lifetime: shared; one atom per word, not one per note instance

### 5.3 Derivation Links (`sys:derived_from`)

Every content atom that has a concept-word counterpart carries a `sys:derived_from` link:

```
content_atom  ──sys:derived_from──►  concept_word_atom
```

This is **one-directional**. The concept word does not reference back into specific instances
because the general concept may be used differently across models and documents.

---

## 6. Cortex Methods Used by Concepts

These are the `AkashaEngine` methods a concept model may call:

| Method | Signature | Notes |
|--------|-----------|-------|
| `put_chunk` | `(content, meta, author, scopes) → key` | Primary atom write. Returns a content-addressed hash key. |
| `get_chunk` | `(key) → str` | Read atom content. |
| `get_meta` | `(key) → dict` | Read atom metadata. |
| `drop_chunk` | `(key, requester_scopes) → None` | Physical deletion. Always pass `requester_scopes=self.allowed_scopes`. |
| `put_link` | `(src, dst, rel, w?, author?) → None` | Create a directed link. |
| `remove_link` | `(src, dst, rel) → None` | Remove a specific directed link. Use this — never raw SQL. |
| `get_adjacent_links` | `(key, rel?) → List[(dst, rel)]` | Outgoing links, optionally filtered by rel. |
| `get_incoming_links` | `(key, rel?) → List[(src, rel)]` | Incoming links, optionally filtered by rel. |
| `create_set` | `(set_name) → None` | Initialize a set bag. |
| `add_to_set` | `(set_name, key) → None` | Add a member to a set. |
| `remove_from_set` | `(set_name, key) → None` | Remove a member from a set. |
| `get_collection_members` | `(set_name) → List[str]` | List all members of a set. |
| `check_access` | `(key, scopes) → bool` | IAM access check for a single atom. |
| `set_alias` | `(key, alias) → None` | Assign a human-readable alias to an atom. |
| `resolve_alias` | `(alias) → Optional[str]` | Look up a key by alias. |

### Session Methods Used

| Method | Signature | Notes |
|--------|-----------|-------|
| `session.client_id` | `str` property | The authenticated client identifier. |
| `session.active_scopes` | `List[str]` property | IAM scope list. Same as `self.allowed_scopes`. |
| `session.get_context(key)` | `(str) → Any` | Read a transient session value. |
| `session.set_context(key, val)` | `(str, Any) → None` | Write a transient session value. |

---

## 7. Kernel Integration

### 7.1 Registering a New Concept — Plugin Registry

**No changes to `kernel.py` are required.**

Drop your Python file into `lib/akasha/concepts/`. The Concept Model Plugin Registry
(`lib/akasha/concepts/registry.py`) auto-discovers all eligible classes at kernel startup.

A class is eligible if it defines both `CONCEPT_PREFIX` and `CONCEPT_METHODS`:

```python
class MyThingConcept(BaseConcept):
    CONCEPT_PREFIX = "mything"
    CONCEPT_METHODS = {
        # suffix → op method name, or spec dict with "op" and optional "coerce"
        "new": {"op": "op_new"},
        "add": {"op": "op_add"},
        "ls":  {"op": "op_list"},
        "rm":  {"op": "op_delete"},
        # Example with coerce — use when JSON param names differ from op arg names:
        "open": {
            "op":     "op_open",
            "coerce": lambda d: {"mything_id": d.get("id") or d.get("mything_id", "")},
        },
    }
```

At startup, `ConceptRegistry.discover(concepts_dir)` scans the directory, imports each
`*.py` file that is not a dunder file, and registers every top-level class that has both
`CONCEPT_PREFIX` and `CONCEPT_METHODS`. The full method name dispatched in JSON-RPC is
`"{CONCEPT_PREFIX}.{suffix}"`.

**Exception mapping inside the registry:**

| Python exception | JSON-RPC code | Typical cause |
|---|---|---|
| `RuntimeError` | `-32002` | No active concept (`_require_concept`), not found, precondition |
| `TypeError`, `ValueError` | `-32602` | Invalid or missing parameter |
| `NotImplementedError` | `-32601` | Op method exists in CONCEPT_METHODS but not on class |
| Any other | `-32603` | Internal error |

**Concept model commands are intentionally hidden from the main `help` output.**
Document each model's API in `docs/concept-model-spec.md` (this file).

### 7.2 IAM Routing

Add each method to `_METHOD_TO_ACTION` in `kernel.py` so IAM enforces read/write/drop
permissions on concept model commands:

```python
"mything.new":    "write",
"mything.add":    "write",
"mything.ls":     "read",
"mything.rm":     "drop",
```

### 7.3 Shell Command Aliases

Add short aliases to `api/router.py`:

```python
"mt.new": "mything.new",
"mt.add": "mything.add",
"mt.ls":  "mything.ls",
"mt.rm":  "mything.rm",
```

### 7.4 Session Instance Layer Integration

The Session Instance Layer (Layer 3, `lib/akasha/session/space.py`) lets a client mount
concept models as named instances inside a virtual space. Concept models do not need to
know about SpaceConcept — they only need to follow two conventions, and SpaceConcept
handles the rest.

#### 7.4.1 Two Binding Modes

A concept model reaches the session in one of two ways:

| Mode | Used by | How binding is set |
|------|---------|--------------------|
| **Direct** | Simple single-instance models (NoteConcept, etc.) | `op_new` / `op_open` call `session.set_context` themselves |
| **Space-managed** | Multi-instance models (CastConcept, etc.) | `instance.mount` / `instance.focus` call `session.set_context` via SpaceConcept |

A model can support both simultaneously: `op_new` sets context for standalone use;
SpaceConcept overwrites it on `instance.focus`.

#### 7.4.2 The `CONTEXT_KEY_ACTIVE` Convention

Any concept model that can be managed by SpaceConcept must expose its active-instance
context key as a class attribute named `CONTEXT_KEY_ACTIVE`.

```python
# 1. Module-level constant — readable by anyone importing this module
CONTEXT_KEY_ACTIVE = "active_mything_root"

class MyThingConcept(BaseConcept):
    CONCEPT_PREFIX = "mything"

    # 2. Class attribute — readable by SpaceConcept via cls.CONTEXT_KEY_ACTIVE
    CONTEXT_KEY_ACTIVE = CONTEXT_KEY_ACTIVE
```

`BaseConcept` defines this as `None` by default. If a model leaves it `None`, SpaceConcept
cannot set focus for it; `instance.focus` on that slot raises an error.

When `instance.focus slot="bot"` is called:

1. SpaceConcept reads the slot's `model` and `concept_id`.
2. Resolves the plugin class via `registry.get_class(model)`.
3. Reads `cls.CONTEXT_KEY_ACTIVE` to get the key name.
4. Calls `session.set_context(key, concept_id)`.

The concept model itself is never called — only the session context key is updated.

#### 7.4.3 `op_new` Must Return `concept_id`

When `instance.mount model=mything slot=X name="..."` is called **without** an `id`
parameter, SpaceConcept creates a new instance by dispatching `mything.new`. It then
reads the returned dict's `"concept_id"` key to know the new root atom's ID.

```python
def op_new(self, title: str, ...) -> Dict[str, Any]:
    ...
    return {
        "status":     "created",
        "concept_id": root_id,   # required — SpaceConcept reads this key
        "mything_id": root_id,   # optional alias for CLI output
        "title":      title,
    }
```

Missing `concept_id` in the return dict causes `instance.mount` to raise a `RuntimeError`.

#### 7.4.4 Session Context in `op_new` / `op_open`

Every model that maintains an active instance should set session context directly in
`op_new` and `op_open`. This supports standalone use (without `instance.mount`):

```python
def op_new(self, title: str) -> Dict[str, Any]:
    ...
    if hasattr(self.session, "set_context"):
        self.session.set_context(CONTEXT_KEY_ACTIVE, root_id)
    return {"status": "created", "concept_id": root_id, ...}
```

When `instance.mount` later calls `_apply_focus`, it overwrites the same key with the
same value — this is a safe no-op. The `hasattr` guard keeps the model testable with
stub session objects.

#### 7.4.5 Multi-Instance Model Lifecycle

For a model that supports multiple simultaneous instances (like CastConcept):

```
instance.mount model=mything slot=A name="alpha"
  → op_new() called → sets active_mything_root = A_id  (auto-focus, first slot)

instance.mount model=mything slot=B name="beta"
  → op_new() called → sets active_mything_root = B_id  (op_new sets it directly)
  → SpaceConcept does NOT auto-focus (slot A already focused) → restores A_id

# result: active_mything_root = A_id  (slot A still focused)

instance.focus slot=B
  → SpaceConcept sets active_mything_root = B_id

instance.blur model=mything
  → SpaceConcept sets active_mything_root = None

instance.unmount slot=A
  → SlotAtom removed from space; underlying concept root preserved in Cortex
```

The concept model's `op_*` methods read `CONTEXT_KEY_ACTIVE` from session context at
invocation time — they do not cache it. Switching focus between slots is therefore
instantaneous with no state to clean up inside the model.

#### 7.4.6 Summary: What a Concept Model Author Must Do

| Requirement | Where | What |
|-------------|-------|------|
| Module constant | top of file | `CONTEXT_KEY_ACTIVE = "active_{model}_root"` |
| Class attribute | class body | `CONTEXT_KEY_ACTIVE = CONTEXT_KEY_ACTIVE` |
| `op_new` return | `op_new` | include `"concept_id": root_id` |
| Session context | `op_new`, `op_open` | `session.set_context(CONTEXT_KEY_ACTIVE, id)` |
| Session context | `op_delete` / `op_close` | `session.set_context(CONTEXT_KEY_ACTIVE, None)` |

No changes to `space.py`, `kernel.py`, or the registry are required for a new model to
be mountable via `instance.mount`.

---

## 8. Design Principles

**Operand-First**: The dispatch operator (`"note.add"`) names the concept before the verb.
The concept is the first-class object; the verb is a method on it.

**Cortex as the only storage**: Concepts never write to files, databases, or networks
directly. All persistence goes through `self.cortex`. This keeps concepts testable in
isolation with a mock Cortex.

**Session for context, Cortex for memory**: Transient state (which note is open, which
container is active) lives in session context. Permanent knowledge lives in Cortex atoms.

**Scope propagation**: Concept methods always derive `author_id` from `session.client_id`
and build `scopes` as `["owner:user_{id}", "view:user_{id}"]`. Every atom written by a
concept is owned by the authenticated client.

**Content set vs concept catalog**: Content atoms live in the concept's own namespace
(`set:note:*`, `set:mything:*`). General vocabulary lives in `set:concept:*`. The same
atom is never in both. Use `sys:derived_from` links to connect instances to vocabulary.

**`_require_concept` everywhere**: Every `op_*` except `op_new` must call
`self._require_concept()` as its first statement. Returning error dicts silently is wrong
— raise explicitly so the kernel can surface a clear error to the client.

**No cross-concept direct calls**: Concepts do not instantiate or call each other. Cross-
concept relationships are expressed as Cortex links:
`cortex.put_link(a_id, b_id, "sys:associated_with")`.

---

## 9. Reserved Link Relations

| Relation | Direction | Meaning |
|----------|-----------|---------|
| `sys:top` | root → first_node | Timeline start pointer |
| `sys:bottom` | root → last_node | Timeline end floating pointer (updated via `remove_link` + `put_link`) |
| `sys:next` | node → next_node | Forward sequential link |
| `sys:previous` | node → prev_node | Backward sequential link |
| `sys:contains` | parent → child | Vertical hierarchy: parent owns child |
| `sys:part_of` | child → parent | Vertical hierarchy: child belongs to parent |
| `sys:derived_from` | content_atom → concept_word_atom | Instance derives from general concept (one-directional) |
| `sys:has_annotation_span` | chunk → annotation | Character-level sub-atom |
| `sys:included` | chunk → annotation | Containment (span alias) |
| `sys:associated_with` | any → any | Loose semantic association |

Custom relations for a concept must use a concept-namespaced form:

```
{prefix}:{relation}     # e.g. agg:unit, synth:code, pres:frame, mt:item
```

Never use bare relation names or re-use another concept's prefix. The bundled
models establish these namespaces:

| Concept | Relations used |
|---------|---------------|
| Aggregation (`agg`) | `agg:unit`, `agg:group`, `agg:member`, `agg:measure`, `agg:analysis_out`, `agg:analysis_in`, `agg:hierarchy`, `agg:child` |
| Synthesis (`synth`) | `synth:source`, `synth:refers_to`, `synth:code`, `synth:applies_to`, `synth:theme`, `synth:contains`, `synth:interp`, `synth:interprets`, `synth:supported_by`, `synth:claim`, `synth:argues`, `synth:evidence`, `synth:thread`, `synth:step` |
| Presentation (`pres`) | `pres:deck`, `pres:frame`, `pres:region`, `pres:node` |

Avoid reusing `sys:top/bottom/next/previous` unless your concept implements a sequential
timeline. Using them for other purposes breaks `op_get_sequential_text` and TOC traversal
if the two concepts share atoms.

---

## 10. Bundled Concept Model API Reference

The following concept models ship with AkashicTree and are registered automatically
via the Plugin Registry. Their commands are hidden from the main `help` output.

---

### 10.1 Cockpit

**Source:** `lib/akasha/concepts/cockpit.py`  
**Session context key:** `active_cockpit_root`

A stateful navigational vessel for the Semantic Cosmos. Maintains a **transient instrument
panel** (focal point, axis, scope) in the session, and materialises observations as
**beacons** — permanent atoms with embedded telemetry — only when explicitly commanded.
The chronological sequence of beacons is the **wake**.

Topology:
- Root atom (`concept: "cockpit"`, `role: "root"`) anchors the vessel.
- Beacon atoms linked via `sys:contains` and sequenced by `sys:top → sys:next → sys:bottom`.
- Transient state lives in session context only; never written between beacon drops.

| Method | Required params | Description |
|---|---|---|
| `cockpit.new` | `name` (str) | Commission a new cockpit deck |
| `cockpit.ls` | — | List all cockpits owned by this user |
| `cockpit.open` | `cockpit_id` (str) | Mount an existing cockpit as active |
| `cockpit.lock` | `target` (str) | Set the focal point (session only) |
| `cockpit.tune` | `axis`? (str), `scope`? (int) | Adjust dimensional lens filters |
| `cockpit.beacon` | `note` (str) | Drop a beacon at current focal point |
| `cockpit.wake` | — | Read the chronological beacon trail |
| `cockpit.status` | — | Read instrument panel state |
| `cockpit.rm` | — | Decommission the active cockpit |

**CLI aliases:** `cp.new`, `cp.ls`, `cp.open`, `cp.lock`, `cp.tune`, `cp.beacon`, `cp.wake`, `cp.status`, `cp.rm`

---

### 10.2 FieldNote

**Source:** `lib/akasha/concepts/fieldnote.py`  
**Session context key:** `active_fieldnote_root`

A flat, context-tagged field observation record. Unlike the Note concept (hierarchical
document), FieldNote is deliberately flat — all observations append to a single chronological
timeline. Context metadata (project, region, season) lives on the root atom.

| Method | Required params | Description |
|---|---|---|
| `fieldnote.new` | `title` (str) | Create a new FieldNote record |
| `fieldnote.ls` | — | List all accessible FieldNote records |
| `fieldnote.open` | `fieldnote_id` (str) | Mount an existing record as active |
| `fieldnote.add` | `text` (str) | Append an observation |
| `fieldnote.read` | — | Read all observations in order |
| `fieldnote.rm` | — | Delete the active FieldNote root |

Optional params for `fieldnote.new`: `project`, `region`, `season` (all strings).

**Response shapes:**
- `fieldnote.read` → `{"observations": [...], "count": N}`
- Each observation: `{"id", "content", "role", "created_at"}`

---

### 10.3 Survey

**Source:** `lib/akasha/concepts/survey.py`  
**Session context key:** `active_survey_root`

A pure-structural data-collection universe. Maintains five typed atom populations — root,
questions, options, respondents, responses — each cross-linked by `sys:contains` /
`sys:part_of` and registered into two namespaces (dual-namespace rule).

**Namespace contract:**

| Namespace | Set | Contents |
|---|---|---|
| Survey-scope | `set:survey:{id}`, `set:survey:{id}:{subset}` | All content atoms |
| Concept catalog | `set:concept:{id}` | Concept-word atoms only — NOT the root atom |

Each content atom links to its concept-word via `sys:derived_from`.

| Method | Required params | Description |
|---|---|---|
| `survey.new` | `title` (str) | Create a new survey root |
| `survey.open` | `survey_id` (str) | Mount an existing survey |
| `survey.ls` | — | List all accessible surveys |
| `survey.q.add` | `text` (str) | Add a question to active survey |
| `survey.opt.add` | `question_id`, `label` (str) | Add an option to a question |
| `survey.res.add` | `respondent_id` (str) | Register a respondent |
| `survey.ans` | `question_id`, `respondent_atom`, `answer` | Record a tri-linked response |
| `survey.list` | — | Structural inventory of active survey |
| `survey.rm` | — | Delete the active survey root |

Optional params: `survey.new` accepts `description`; `survey.q.add` accepts `qtype` and `order`; `survey.opt.add` accepts `value`; `survey.res.add` accepts `attributes` dict.

---

### 10.4 Aggregation

**Source:** `lib/akasha/concepts/aggregation.py`  
**Session context key:** `active_aggregation_root`  
**Prefix:** `agg` · **Index set:** `set:agg:index`

Builds statistical analysis structures over any set of Cortex atoms. The five-layer
model (Unit → Group → Measure → Analysis → Hierarchy) maps raw atom collections to
labelled partitions, attaches statistics to each partition, records directed relations
between partitions, and organises everything into a navigable hierarchy. Source atoms
are indexed as *references* — never copied.

| Method | Required params | Optional params | Description |
|--------|-----------------|-----------------|-------------|
| `agg.new` | `source_id` | — | Create aggregation root linked to a corpus atom |
| `agg.open` | `agg_id` / `aggregation_id` | — | Mount an existing aggregation |
| `agg.ls` | — | — | List all accessible aggregations |
| `agg.unit.add` | `unit_id` | — | Index an atom as an analysis unit |
| `agg.group.add` | `label` | `members` (list) | Create a labelled group of units |
| `agg.measure.add` | `group_id`, `key`, `value` | — | Attach a statistic to a group |
| `agg.analysis.add` | `src_group`, `dst_group`, `relation`, `score` | — | Record a directed relation between groups |
| `agg.hier.add` | `label` | `children` (list) | Create a hierarchy node |
| `agg.list` | — | — | Structural inventory of active aggregation |
| `agg.rm` | — | — | Delete the active aggregation root |

**CLI aliases:** `agg.new`, `agg.open`, `agg.ls`, `agg.unit.add`, `agg.group.add`, `agg.measure.add`, `agg.analysis.add`, `agg.hier.add`, `agg.list`, `agg.rm`

See `docs/concept-extensions.md §3` for design rationale, topology, and cross-concept patterns.

---

### 10.5 Synthesis

**Source:** `lib/akasha/concepts/synthesis.py`  
**Session context key:** `active_synthesis_root`  
**Prefix:** `synth` · **Index set:** `set:synth:index`

Models the qualitative reasoning process between raw source material and a finished
argument. The six layers — Source (reference), Code, Theme, Interpretation, Claim,
Thread — correspond to the mental operations of qualitative analysis (Grounded Theory,
thematic analysis, discourse analysis). Source atoms are indexed as references; the
analysis builds interpretive meaning on top without duplicating the originals.

`synth.trace` walks the evidence chain backwards from any claim to its source atoms,
producing a full audit trail.

| Method | Required params | Optional params | Description |
|--------|-----------------|-----------------|-------------|
| `synth.new` | `title` | `source_universes` (list) | Create synthesis root |
| `synth.open` | `synth_id` / `synthesis_id` | — | Mount an existing synthesis |
| `synth.ls` | — | — | List all accessible syntheses |
| `synth.source.add` | `ref_id` | `ref_universe`, `note` | Index a source atom (with optional commentary) |
| `synth.code.add` | `label` | `source_id`, `confidence` | Create a qualitative code |
| `synth.theme.add` | `title` | `codes` (list) | Create a theme grouping codes |
| `synth.interp.add` | `text` | `theme_id`, `support` (list), `stance`, `confidence` | Record an interpretation |
| `synth.claim.add` | `text` | `interpretations` (list), `evidence` (list), `status`, `confidence` | Assert a claim |
| `synth.thread.new` | `title` | — | Create a named reasoning thread |
| `synth.thread.add` | `thread_id`, `node_id` | — | Append an atom as next step in a thread |
| `synth.map` | — | — | Structural inventory of active synthesis |
| `synth.trace` | `claim_id` | — | Walk evidence chain from claim to sources |
| `synth.rm` | — | — | Delete the active synthesis root |

**CLI aliases:** as above (no short-form prefix defined by default).

See `docs/concept-extensions.md §4` for design rationale, topology, and cross-concept patterns including the Aggregation → Synthesis mixed-methods pattern.

---

### 10.6 Presentation

**Source:** `lib/akasha/concepts/presentation.py`  
**Session context key:** `active_presentation_root`  
**Prefix:** `pres` · **Index set:** `set:pres:index`

Models the abstract structure of a presentation (slide deck, research talk, poster,
report) without coupling to any rendering format. Content always lives in upstream
models (FieldNote, Survey, Aggregation, Synthesis); the Presentation only holds
*arrangement* — which atoms appear where, in what order, and with what role.

The four-layer stack (Deck → Frame → Region → Node) maps to slide software metaphors
but is format-agnostic. A Node is a `(ref_universe, ref_id)` pointer to a Cortex atom
from any concept model.

| Method | Required params | Optional params | Description |
|--------|-----------------|-----------------|-------------|
| `pres.new` | `title` | `context_universes` (list) | Create presentation root |
| `pres.open` | `pres_id` / `presentation_id` | — | Mount an existing presentation |
| `pres.ls` | — | — | List all accessible presentations |
| `pres.deck.add` | `title` | `order` | Add a section deck |
| `pres.frame.add` | `title` | `deck_id`, `order`, `ref_universe`, `ref_id` | Add a slide/page |
| `pres.region.add` | `frame_id`, `label` | `order` | Add a layout zone within a frame |
| `pres.node.add` | `parent_id`, `ref_universe`, `ref_id` | `role`, `style` | Attach a content reference |
| `pres.list` | — | — | Structural inventory of active presentation |
| `pres.rm` | — | — | Delete the active presentation root |

**CLI aliases:** as above (no short-form prefix defined by default).

See `docs/concept-extensions.md §5` for design rationale, topology, and cross-concept patterns including the Aggregation + Synthesis → Presentation full pipeline.

---

### 10.7 Thesaurus

**Source:** `lib/akasha/concepts/thesaurus.py`  
**Prefix:** `thesaurus` · **Index sets:** `set:thesaurus:index`, `set:thesaurus:curations`, `set:thesaurus:series`

Semantic enrichment model that attaches typed relation links to any atom in the graph and computes a per-atom **ShelfScore** — a weighted quality index reflecting how richly an atom is semantically connected. The model also manages **CurationCollections** (curator-authored linear exhibition sequences) and **ExhibitionSeries** (themed groups of collections with archive and current-page routing).

Unlike other concept models, Thesaurus has no single-root lifecycle. It operates across the entire graph: any atom can be enriched by adding thesaurus links to it, and ShelfScore can be queried for any atom at any time.

**Relation types** (registered in `ontology/thesaurus/a_thesaurus_core.csl`):

| Relation | Role |
|---|---|
| `thesaurus:synonym` | ShelfScore: synonym_coverage |
| `thesaurus:near_synonym` | ShelfScore: synonym_coverage |
| `thesaurus:antonym` | ShelfScore: antonym_presence |
| `thesaurus:hypernym` | ShelfScore: chain_balance |
| `thesaurus:hyponym` | ShelfScore: chain_balance |
| `thesaurus:example_usage` | ShelfScore: example_density |
| `thesaurus:affective` | ShelfScore: affective_score (emotion + sensory unified) |
| `thesaurus:namespace_bridge` | ShelfScore: namespace_bridges |
| `thesaurus:external_ref` | ShelfScore: external_refs (Wikipedia, Britannica, etc.) |
| `thesaurus:interprets` | CuratedAtom → original (one-way shadow) |
| `thesaurus:in_curation` | CuratedAtom → CurationCollection |
| `thesaurus:seq_next` | Linear sequence within a collection |
| `thesaurus:in_series` | CurationCollection → ExhibitionSeries (many-to-many) |

**ShelfScore components** (each clamped \[0, 1\]):

| Component | Formula | Weight |
|---|---|---|
| `link_total` | thesaurus link count / 8 | 0.05 |
| `synonym_coverage` | (synonym + near_synonym) / 3 | 0.20 |
| `antonym_presence` | min(antonym count, 1) | 0.05 |
| `chain_balance` | hypernym + hyponym presence, balanced | 0.05 |
| `example_density` | example_usage count / 2 | 0.20 |
| `affective_score` | affective link count / 3 | 0.20 |
| `namespace_bridges` | namespace_bridge count / 2 | 0.15 |
| `external_refs` | external reference count / 4 | 0.10 |

**Index maintenance:** `thesaurus.shelf.link` automatically registers both endpoint atoms into `set:thesaurus:index`. Atoms added via `thesaurus.curation.atom` register the original atom in `set:thesaurus:index`. `thesaurus.shelf.list` only enumerates atoms in this set.

**Namespace contract:**

| Set | Contents |
|---|---|
| `set:thesaurus:index` | All atoms that carry at least one `thesaurus:*` link |
| `set:thesaurus:curations` | CurationCollection root atoms + CuratedAtoms |
| `set:thesaurus:series` | ExhibitionSeries root atoms |

**CurationCollection topology:**

```
CurationCollection ──thesaurus:seq_next──► CuratedAtom₁
                                                │
                                          thesaurus:seq_next
                                                ▼
                                          CuratedAtom₂
                                                │
                                          thesaurus:interprets
                                                ▼
                                          original atom  (never modified)
```

Each CuratedAtom also carries a `thesaurus:in_curation` link back to its collection. The sequence is strictly linear — no branching. Exiting the sequence means departing to a free dive; the sequence itself does not model divergence.

**ExhibitionSeries topology:**

```
ExhibitionSeries  ←─thesaurus:in_series──  CurationCollection₁
                  ←─thesaurus:in_series──  CurationCollection₂
                  meta: {exhibitions: [col1_key, col2_key]}
                         ↑ ordered: last = current, earlier = archive
```

A CurationCollection can belong to **multiple** ExhibitionSeries (many-to-many via `thesaurus:in_series` links). Each series independently maintains its own ordered `exhibitions` list in its atom meta. Calling `thesaurus.series.add` is idempotent for each (series, collection) pair.

**URL permanence:** `_url_slug(alias)` strips the namespace prefix from an alias to derive a stable URL identifier:
- `series:dreams-genealogy` → `dreams-genealogy` → `/series/dreams-genealogy`
- `curations:sky-dreamers-vol1` → `sky-dreamers-vol1` → `/exhibition/sky-dreamers-vol1`
- bare word alias `love` (proto-word) → `/word/love`

Every atom with an alias automatically has a permanent URL slug — no additional data is needed.

| Method | Required params | Optional params | Description |
|---|---|---|---|
| `thesaurus.shelf.score` | `atom_id` or `name` | — | Compute full ShelfScore breakdown for one atom |
| `thesaurus.shelf.list` | — | `limit` (default 20), `min_score` (default 0.0) | List indexed atoms ranked by ShelfScore |
| `thesaurus.shelf.link` | `atom_id`/`name`, `target_id`/`target_name`, `rel` | `weight` (default 1.0) | Add a typed `thesaurus:*` link; indexes both atoms |
| `thesaurus.shelf.link_ext` | `name` (or `atom_id`), `url`, `label` | — | Attach an external reference URL; creates `thesaurus:ExternalRef` atom (upsert on source+label); counts toward `external_refs` ShelfScore component |
| `thesaurus.curation.new` | `title` | `concept`, `alias` | Create a CurationCollection atom |
| `thesaurus.curation.ls` | — | — | List all CurationCollections |
| `thesaurus.curation.atom` | `collection_id`, (`original_id` or `original_name`), `interpretation` | `position` | Add a CuratedAtom to a collection |
| `thesaurus.series.new` | `title` | `slug`, `alias` | Create an ExhibitionSeries; idempotent if alias already exists |
| `thesaurus.series.ls` | — | — | List all ExhibitionSeries |
| `thesaurus.series.add` | (`series_id` or `alias`), (`collection` or `collection_id`) | — | Add a CurationCollection to a series as the new current exhibition; idempotent per (series, collection) pair |
| `thesaurus.view.atom` | `atom_id` or `name` | — | Full UI projection: ShelfScore breakdown, semantic links grouped by type, external refs panel, curation waypoints for this atom |
| `thesaurus.view.curation` | `collection_id` or `alias` | — | Full UI projection for a CurationCollection: ordered waypoints with original atom data, external refs, ShelfScore, and `url_slug` |
| `thesaurus.view.series` | `series_id` or `alias` | — | Full UI projection for an ExhibitionSeries: `current` (latest) and `archive` (reverse-chronological) with `url_slug` per entry |

**Response shapes:**

`thesaurus.shelf.score` returns:
```json
{
  "atom_id": "...",
  "shelf_score": 0.4250,
  "components": {
    "link_total": 0.375, "synonym_coverage": 0.667, "antonym_presence": 1.0,
    "chain_balance": 0.28, "example_density": 0.5, "affective_score": 0.333,
    "namespace_bridges": 0.5, "external_refs": 0.75
  },
  "link_counts": {
    "synonym": 1, "near_synonym": 1, "antonym": 1, "hypernym": 1, "hyponym": 0,
    "example_usage": 1, "affective": 1, "namespace_bridge": 1, "external_ref": 3
  }
}
```

`thesaurus.shelf.list` returns `{"atoms": [...], "total_indexed": N}` where each entry includes `atom_id`, `shelf_score`, `components`, `link_counts`, `content`, and `name`.

`thesaurus.view.atom` returns a `thesaurus:AtomView` projection:
```json
{
  "type": "thesaurus:AtomView",
  "atom": { "key": "...", "name": "sky:myth:icarus", "description": "Son of Daedalus..." },
  "shelf_score": { "shelf_score": 0.52, "components": {...}, "link_counts": {...} },
  "semantic_links": {
    "synonyms": [], "near_synonyms": [{"key":"...","name":"sky:pioneer:lilienthal","description":"..."}],
    "antonyms": [{"key":"...","name":"sky:myth:daedalus","description":"..."}],
    "hypernyms": [], "hyponyms": [], "example_usage": [],
    "affective": [{"key":"...","name":"emo:awe","description":"..."},{"key":"...","name":"emo:fear","description":"..."}],
    "namespace_bridges": [{"key":"...","name":"tech:aviation:glider","description":"..."}]
  },
  "external_refs": [
    {"label": "Wikipedia", "url": "https://en.wikipedia.org/wiki/Icarus"},
    {"label": "Britannica", "url": "https://www.britannica.com/topic/Icarus-Greek-mythology"},
    {"label": "Perseus",    "url": "https://www.perseus.tufts.edu/..."}
  ],
  "curations": [
    {
      "curated_id": "...", "collection_id": "...",
      "collection_title": "Those Who Yearned for the Sky — A Genealogy of Falls and Flights",
      "interpretation": "Icarus is not a myth of failure...", "position": 1
    }
  ]
}
```

`thesaurus.view.curation` returns a `thesaurus:CurationView` projection:
```json
{
  "type": "thesaurus:CurationView",
  "collection": {
    "id": "...", "alias": "curations:sky-dreamers-vol1",
    "url_slug": "sky-dreamers-vol1",
    "title": "Those Who Yearned for the Sky — A Genealogy of Falls and Flights",
    "concept": "flight_dream", "curator": "user1", "waypoint_count": 10
  },
  "waypoints": [
    {
      "position": 1, "curated_id": "...",
      "interpretation": "Icarus is not a myth of failure...",
      "original": {
        "key": "...", "name": "sky:myth:icarus", "description": "Son of Daedalus...",
        "shelf_score": 0.52,
        "external_refs": [{"label": "Wikipedia", "url": "..."}]
      }
    }
  ]
}
```

`thesaurus.view.series` returns a `thesaurus:SeriesView` projection:
```json
{
  "type": "thesaurus:SeriesView",
  "series": {
    "id": "...", "alias": "series:dreams-genealogy",
    "url_slug": "dreams-genealogy",
    "title": "Genealogy of the Dreamers",
    "curator": "user1", "created_at": 1.7e9, "exhibition_count": 2
  },
  "current": {
    "id": "...", "alias": "curations:sky-dreamers-vol2",
    "url_slug": "sky-dreamers-vol2",
    "title": "...", "waypoint_count": 8, "position": 2
  },
  "archive": [
    {
      "id": "...", "alias": "curations:sky-dreamers-vol1",
      "url_slug": "sky-dreamers-vol1",
      "title": "Those Who Yearned for the Sky — A Genealogy of Falls and Flights",
      "waypoint_count": 10, "position": 1
    }
  ]
}
```

`archive` entries are in reverse chronological order (most recently archived first). An empty series returns `"current": null, "archive": []`.

**External ref atom structure:** `thesaurus.shelf.link_ext` creates (or upserts) an atom with alias `thesaurus:ext:{source-slug}:{label-slug}` (e.g. `thesaurus:ext:sky-myth-icarus:wikipedia`), content = URL, meta = `{"type": "thesaurus:ExternalRef", "label": label, "url": url}`. The source atom is linked to this atom via `thesaurus:external_ref`. Duplicate calls with the same source+label pair are idempotent (the existing ref atom is reused).

**URL slug derivation:** `_url_slug(alias)` strips the namespace prefix: `curations:sky-dreamers-vol1` → `sky-dreamers-vol1`. All view projections include `url_slug` for every alias-bearing entity (series, collections, proto-words). Proto-word (bare-word) aliases have no prefix, so they map directly: `love` → `love` → `/word/love`.

---

## 11. Root Lifecycle Guarantees *(stub — not yet specified)*

> **Status:** Design pending. The questions below will become significant once concept
> count and data volume grow. The current implementation makes no guarantees beyond
> what is listed under "Current behaviour".

### 11.1 Current Behaviour (v1.4)

`op_delete` in each concept model calls `cortex.drop_chunk(root_id)` and removes
`root_id` from `INDEX_SET`. Nothing else is guaranteed:

- Subordinate atoms (traits, masks, items, …) are **not** deleted.
- Concept sets (`set:concept:{id}`, `set:<model>:{id}`, sub-sets) are **not** removed.
- Aliases assigned to the root are **not** invalidated.
- `space:owns` / `space:contains` links in any SessionSpace are **not** cleaned up.

This is safe while data volume is small ("seeds phase"). The items below are the open
design questions.

### 11.2 Open Questions

**Drop policy**

| Policy | Meaning |
|--------|---------|
| `shallow` | Delete root only; subordinate atoms and sets enter GC queue |
| `cascade` | Recursively delete all atoms reachable via `sys:contains` from root |
| `tombstone` | Rewrite root meta to `{"deleted": true}`; links preserved for audit |

Default policy for each concept model, and whether callers can override, TBD.

**Index and set cleanup**

- Is `INDEX_SET` removal automatic (triggered by `drop_chunk`) or the concept's responsibility?
- When does an empty concept set get reclaimed? Reference-counted, sweep-based, or manual?
- Who owns set GC — Cortex, kernel, or individual concept models?

**Alias invalidation**

- When `drop_chunk(root_id)` is called, are aliases pointing to `root_id` automatically removed?
- Or do they persist as dangling aliases until explicit cleanup?

**Orphan policy**

After a `shallow` drop, subordinate atoms have no reachable parent. Options:

1. **Silent orphan** — atoms remain; only a sweep finds them.
2. **Warn on read** — Cortex flags atoms whose root is gone.
3. **GC sweep** — a maintenance job collects unreferenced atoms periodically.

**SessionSpace cleanup**

When a concept root is deleted, any `SlotAtom` in a SessionSpace that holds its
`concept_id` becomes stale. Whether `instance.unmount` is called automatically or the
slot silently holds a dead reference is TBD.

**Cascading across concept boundaries**

If a CastConcept root is cascade-deleted, should linked SynthesisConcept nodes that
reference it via `sys:associated_with` also be dropped, or only unlinked?

---

## 12. Service Namespace Isolation

### 12.1 The Problem

Session context is **user-scoped**, not service-scoped. Two UI services that use the same
concept class (e.g. the Note app and the Loom writing atelier both use `NoteConcept`) share
the same session context dictionary. Without isolation, whichever service called `op_new`
last overwrites `active_note_root`, causing the other service to load a wrong document.

### 12.2 The Solution — `namespace` Parameter

`BaseConcept.__init__` accepts an optional `namespace: str`. When provided:

- `self._ns = f"{namespace}:"`
- `self._ctx_key(key)` returns `f"{namespace}:{key}"` instead of bare `key`

All context reads and writes in `op_new`, `op_open`, `op_delete`, and `__init__` must
route through `self._ctx_key()`. Services that share the same concept class but need
independent state simply use different namespaces.

### 12.3 How to Apply

**Concept class** (`__init__`, every `set_context` / `get_context` call):

```python
def __init__(self, session, concept_id=None, namespace=None):
    super().__init__(session, concept_id, namespace=namespace)
    if not self.concept_id:
        stored = getattr(self.session, "get_context", lambda k: None)(
            self._ctx_key(CONTEXT_KEY_ACTIVE)
        )
        ...

# In op_new / op_open / op_delete:
self.session.set_context(self._ctx_key(CONTEXT_KEY_ACTIVE), root_id)
```

**Kernel handler** — instantiate with the service's namespace:

```python
# Standard Note app — no namespace (backward-compatible)
concept = NoteConcept(session)

# Loom writing atelier — isolated under "loom:"
concept = NoteConcept(session, namespace="loom")
```

**RPC naming convention** — prefix the RPC method with the service name so the kernel
knows which namespace to use without ambiguity:

```
note.new / note.read / …       → no namespace  (Note app)
loom.note.new / loom.note.read → namespace="loom"  (Loom)
```

### 12.4 Design Rules

| Rule | Rationale |
|------|-----------|
| Every `get_context` / `set_context` call goes through `self._ctx_key()` | Prevents raw key bleed |
| Each UI service that uses a shared concept model gets a unique namespace string | Guarantees session-level isolation |
| Namespace strings are short lowercase identifiers (`"loom"`, `"fieldnote"`) | Readable in session dumps |
| `namespace=None` (default) preserves the bare key — backward-compatible | Existing services need no change |
| New RPCs for a namespaced service follow `{service}.{concept}.{op}` | Kernel can dispatch to the right namespace without inspecting request body |

### 12.5 Which Concept Models Are Affected

A concept model needs namespace support only when the **same concept class is (or could be)
used by more than one UI service**. If a concept class has exactly one service, its module-
level `CONTEXT_KEY_ACTIVE` is already unique and no namespace is required.

| Concept Class | Context Key | Namespace Needed? |
|---------------|-------------|-------------------|
| `NoteConcept` | `active_note_root` | Yes — Note app + Loom both use it |
| `FieldNoteConcept` | `active_fieldnote_root` | Applied (future-proofing) |
| All others | `active_*_root` (unique per class) | Only if a second service appears |

## 13. Change Log

| Version | Changes |
|---------|---------|
| 1.0 | Initial specification |
| 1.1 | Added `_require_concept` to BaseConcept (§2.4). Added `cortex.remove_link` (§6). Documented dual-namespace design and `sys:derived_from` derivation pattern (§3.2, §3.3, §5). Updated `_append_to_timeline` to use `cortex.remove_link`. Fixed `op_delete` to pass `requester_scopes`. Added staging × Harmonia boundary warning (§2.8). Added §5 set namespace design as a standalone section. Updated template (§4.1) to reflect all current patterns. Added `sys:derived_from` to reserved relations table (§9). |
| 1.2 | Replaced manual kernel handler pattern (§7.1) with Plugin Registry auto-discovery. `CONCEPT_PREFIX` + `CONCEPT_METHODS` opt-in — no `kernel.py` changes needed for new models. Added §10 API reference for bundled concept models (Cockpit, FieldNote, Survey). |
| 1.3 | Rewrote §4.1 template to reflect all patterns from Aggregation, Synthesis, Presentation implementations: `CONCEPT_METHODS` with `coerce`, `INDEX_SET`, `_require_access`, `_visible_members`, correct set creation order. Expanded §4.2 checklist. Added §4.3 Common Implementation Bugs (B1–B11). Added concept-namespace relation convention to §9 with full table for agg/synth/pres relations. Added §10.4–10.6 API reference entries for Aggregation, Synthesis, Presentation. |
| 1.4 | Fixed Two-Namespace Rule violation in template: `_register(root_id)` — no `concept_word` on root atom (§4.1, §4.3 B1, §5.1). Added root atom corollary to §5.1. Added §7.4 Session Instance Layer Integration: two binding modes, `CONTEXT_KEY_ACTIVE` convention, `concept_id` return requirement, multi-instance lifecycle. Added §11 Root Lifecycle Guarantees stub: current behaviour, open questions on drop policy, GC, alias invalidation, orphan policy, SessionSpace cleanup. |
| 1.5 | Added `namespace` parameter to `BaseConcept.__init__` and `_ctx_key()` helper (§2.1, §2.3). Updated template `__init__`, `op_new`, `op_open` to use `_ctx_key()` (§4.1). Added §12 Service Namespace Isolation: problem statement, solution, design rules, affected models table. |
| 1.6 | Added §10.7 Thesaurus: cross-graph semantic enrichment model with ShelfScore, typed relation registry, and CurationCollection management. Unlike other models, Thesaurus has no single root — it operates across the entire graph. Relation types registered in `ontology/thesaurus/a_thesaurus_core.csl`. |
| 1.7 | Thesaurus §10.7 extended: `thesaurus:external_ref` relation type added; `thesaurus.shelf.link_ext` operator attaches external URLs (Wikipedia, Britannica, etc.) to atoms; `external_refs` ShelfScore component (w=0.10) counts external refs / 4. `thesaurus.view.atom` and `thesaurus.view.curation` operators added for complete UI projection. ShelfScore weights rebalanced: `link_total` 0.10→0.05, `chain_balance` 0.10→0.05, `external_refs` new 0.10. Shell renderer extended to handle `thesaurus:AtomView` and `thesaurus:CurationView` result types. |
| 1.8 | Thesaurus §10.7 extended with ExhibitionSeries: `thesaurus:in_series` relation added (many-to-many: a CurationCollection can belong to multiple series). `thesaurus.series.new`, `thesaurus.series.ls`, `thesaurus.series.add`, `thesaurus.view.series` operators added. `set:thesaurus:series` index set. `url_slug` field added to all view projections (series, curation, collection). URL permanence convention documented: `/series/{slug}`, `/exhibition/{slug}`, `/word/{alias}`. Shell renderer extended with `_render_thesaurus_series_view` for `thesaurus:SeriesView` result type. |
