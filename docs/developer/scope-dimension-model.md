# AKASHA Scope Dimension Model

**Version:** 1.0  
**Last updated:** 2026-05-27  
**Audience:** Contributors, kernel developers, LLM co-developers

---

## Table of Contents

1. [Overview](#1-overview)
2. [The Four Scope Dimensions](#2-the-four-scope-dimensions)
3. [Storage Architecture](#3-storage-architecture)
4. [Node Character — Three Factors](#4-node-character--three-factors)
5. [Write Pattern — Fast Path + Index Path](#5-write-pattern--fast-path--index-path)
6. [Namespace Reference](#6-namespace-reference)
7. [Security Rules](#7-security-rules)
8. [Private Instance → Universal Concept Pattern](#8-private-instance--universal-concept-pattern)
9. [Session Context Namespace — Service Isolation](#9-session-context-namespace--service-isolation)
10. [Multi-Store Architecture — Nucleus, Cell, Group](#10-multi-store-architecture--nucleus-cell-group)

---

## 1. Overview

Every atom in AKASHA carries **scope tags** — string labels encoded as
`namespace:value` (e.g., `owner:user_alice`, `lang:en`, `leaf:love`).
These tags serve fundamentally different purposes depending on which
*dimension* they belong to.

Mixing dimensions causes two classes of bugs:

| Bug class | Example |
|---|---|
| **Security hole** | Locale preference `lang:ja` mistakenly evaluated as an access-control scope, making an atom visible to Japanese-locale users who otherwise lack permission. |
| **Computational explosion** | Access-control check iterates over all atoms instead of using a pre-built index, causing O(N) per query. |

The model therefore defines strict rules about where each dimension is stored,
when it is evaluated, and which dimensions may never appear in the same SQL query.

---

## 2. The Four Scope Dimensions

### Dim-1 — Access Control

> **Question answered:** *Can this session see this atom?*

Evaluated as the final security filter on every read and traversal. Stored in
the dedicated `chunk_access` table (not `collections`). Never stored with
computational dimension data.

| Prefix | Example | Meaning |
|---|---|---|
| `scope:sys:*` | `scope:sys:universal` | System-managed visibility scope |
| `owner:` | `owner:user_alice` | Private ownership — only the owner (and ADMIN) can see this atom |
| `view:` | `view:user_alice` | Explicit read grant — added separately from ownership |
| `view:public` | — | Any session can read, including unauthenticated GUEST |
| `view:group_G` | `view:group_research` | All members of group G can read |
| `scope:group_G` | `scope:group_research` | Group-scoped knowledge namespace |
| `view:admin_override` | — | ADMIN can read pending/capsule atoms |

**Implementation:** `AkashaCore.chunk_access` table → `check_chunk_access_any()`.  
**Never passed to:** `collections` table queries, set-theory operations, locale ordering.

---

### Dim-2 — Capability Flags

> **Question answered:** *Is this session allowed to perform this action?*

Checked by `IdentityManager.authorize()` only. Never stored in the database as
scope membership — these are session-level assertions.

| Value | Meaning |
|---|---|
| `role:librarian` | Can write to `scope:sys:universal`; bypasses access check for reads |
| `role:admin` | Can perform destructive infrastructure operations |
| `iam.manage` | ADMIN-only user-management capability — gates `user.add` / `user.ls` / `user.mod` / `user.passwd` / `user.rm` |
| `write:group_G` | Can write to a group's shared knowledge |
| `manage:group_G` | Can add/remove group members |

**Implementation:** evaluated in `identity.py:authorize()` only.  
**Never passed to:** SQL queries, `chunk_access`, `collections`.

---

### Dim-3 — Locale Preference

> **Question answered:** *In which language(s) does this session prefer results?*

A display-ordering preference only. Used to rank and filter results after
access-control resolution. Stored in `session.locale` (in-memory + session
context meta), never in the collections or chunk_access tables.

| Prefix | Example | Meaning |
|---|---|
| `lang:` | `lang:en`, `lang:ja` | ISO 639-1 language preference |

**Implementation:** `LocaleContext.get_priority_list()` → passed to
`AkashaEngine.list_leaf(locale_codes=...)` and
`AkashaCore.get_collection_members_locale_ordered()`.  
**Never used as:** an access-control filter, a SQL permission predicate.  
**Shell command:** `locale set <primary> [<l1,l2,...>]`

---

### Calc-Dim — Computational Dimensions

> **Question answered:** *To which semantic dimensions / categories does this atom belong?*

These tags encode *what an atom is*, not *who can see it*. They enable
multi-dimensional set-theory queries: cross-concept intersection, locale-ordered
search, namespace grouping.

Stored in the `collections` table. **Must** be registered at write time
(or shortly after via the async queue) to keep query complexity O(1).

| Prefix | Example | Meaning |
|---|---|
| `leaf:` | `leaf:love` | Unqualified name — links all namespaces for a concept (`word:en:love` and `emo:love` both → `leaf:love`) |
| `ns:` | `ns:word`, `ns:word:en` | Namespace grouping for alias paths |
| `lang:` | `lang:en` | Language tag derived from ISO 639-1 code in alias namespace |
| User sets | `set:my_list` | User-defined membership set |

> Note: `lang:` appears in both Dim-3 (session preference) and Calc-Dim
> (atom collection membership). The session holds a *list of preferred codes*;
> the atom is tagged with its actual language code. These are different
> structures that happen to share the `lang:` prefix.

---

## 3. Storage Architecture

```
┌─────────────────────────────────────────────────────────┐
│  chunks  (key, content, meta, author, status, ...)       │
│  The physical atom store. No scope data here.            │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  chunk_access  (key, scope)          Dim-1 ONLY          │
│                                                          │
│  scope:sys:universal → key_A                             │
│  owner:user_alice    → key_B                             │
│  view:user_alice     → key_B                             │
│                                                          │
│  Indexed on both key and scope.                          │
│  Used exclusively for access-control EXISTS subqueries.  │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  collections  (name, key)           Calc-Dim ONLY        │
│                                                          │
│  leaf:love    → key_A   (word:en:love)                   │
│  leaf:love    → key_C   (emo:love)                       │
│  ns:word      → key_A                                    │
│  ns:word:en   → key_A                                    │
│  lang:en      → key_A                                    │
│  ns:emo       → key_C                                    │
│  set:my_list  → key_A                                    │
│                                                          │
│  Never contains scope:/owner:/view: prefixes.            │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  aliases  (alias, key)                                   │
│                                                          │
│  word:en:love → key_A   (full namespace alias)           │
│  love         → key_A   (plain alias — registered fast)  │
│                                                          │
│  The ':' namespace encodes dimension info. Expanding     │
│  it into collections is deferred to the index path.      │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  pending_derivations  (id, key, alias, queued_at)        │
│                                                          │
│  Queue for async collection derivation.                  │
│  Drained by JCL worker on job completion,                │
│  and by _migrate_tables at startup (catch-all).          │
└─────────────────────────────────────────────────────────┘
```

---

## 4. Node Character — Three Factors

Every atom's semantic identity is determined by three factors, in increasing
order of richness and computational cost:

### Factor 1 — Namespace Prefix (`:` left side)

The prefix in an atom's alias encodes the dimension it belongs to.

```
word:en:love    prefix=word  → vocabulary namespace
                segment=en   → ISO 639-1 code → Calc-Dim lang:en
                leaf=love    → Calc-Dim leaf:love

emo:love        prefix=emo   → emotion namespace
                leaf=love    → Calc-Dim leaf:love

owner:user_x    prefix=owner → Dim-1 access control (stored in chunk_access)
```

At write time the prefix alone is sufficient to determine the correct storage
table (Dim-1 → `chunk_access`; Calc-Dim → `collections`).

### Factor 2 — Collection Membership (most efficient)

O(1) SQL index lookup. Answers questions like:
- "Is this atom in the English vocabulary namespace?" → `SELECT 1 FROM collections WHERE name='ns:word:en' AND key=?`
- "Find all atoms named 'love' across all namespaces" → `SELECT key FROM collections WHERE name='leaf:love'`
- "Show me English atoms first, then Japanese" → `get_collection_members_locale_ordered(..., ['en', 'ja'])`

**Rule:** Register atoms in ALL appropriate collections at write time (or
immediately after via the async queue). Redundancy is acceptable; missing
entries cause silent query failures that are hard to debug.

### Factor 3 — Property Links (richest, most expensive)

Graph traversal via `sys:associated_with`, `sys:is_a`, `sys:part_of`, etc.
Used for deep semantic queries: "what concepts are related to this one?"

This layer is populated asynchronously by Harmonia (NLP mapping, Weaver,
Tensor engine). Never use it as the primary access-control gate.

---

## 5. Write Pattern — Fast Path + Index Path

All alias registrations follow a two-phase pipeline:

```
FAST PATH (synchronous, always):
  set_alias('word:en:love', key)
    │
    ├─ aliases: 'word:en:love' → key      (full alias)
    ├─ aliases: 'love'         → key      (plain alias — r love works NOW)
    └─ pending_derivations: enqueue(key, 'word:en:love')

INDEX PATH (async, Harmonia / JCL):
  JCL job completion  ─OR─  _migrate_tables at startup
    │
    └─ drain_derivation_queue()
         └─ _derive_alias_collections('word:en:love', key)
              ├─ collections: leaf:love   → key
              ├─ collections: ns:word     → key
              ├─ collections: ns:word:en  → key
              └─ collections: lang:en     → key
```

**Why two phases?**  
The write path must not be blocked by index-building work. The atom and its
alias are committed immediately; the full collection membership — needed for
multi-dimensional set queries — is built in the background. On session restart,
`_migrate_tables` acts as a catch-all drain for any queued work.

**`r love` availability:**
- Immediately after write: works (plain alias `love` registered synchronously).
- Full cross-namespace collection query (`list_leaf`, `set.ls`): works after
  the next JCL drain or startup.

---

## 6. Namespace Reference

Complete classification of all scope prefixes used in the system.

| Prefix | Dimension | Table | Evaluated by | Example |
|---|---|---|---|---|
| `scope:sys:universal` | Dim-1 | `chunk_access` | `check_chunk_access_any` | All users can read |
| `scope:sys:dna` | Dim-1 | `chunk_access` | `check_chunk_access_any` | ADMIN-only raw DNA |
| `scope:group_G` | Dim-1 | `chunk_access` | `check_chunk_access_any` | Group namespace |
| `owner:` | Dim-1 | `chunk_access` | `check_chunk_access_any` | Private ownership |
| `view:` | Dim-1 | `chunk_access` | `check_chunk_access_any` | Read grant |
| `role:librarian` | Dim-2 | session only | `authorize()` | Capability bypass |
| `role:admin` | Dim-2 | session only | `authorize()` | Destructive ops |
| `iam.manage` | Dim-2 | session only | `authorize()` | ADMIN-only user management (`user.add/ls/mod/passwd/rm`) |
| `write:group_G` | Dim-2 | session only | `authorize()` | Group write right |
| `manage:group_G` | Dim-2 | session only | `authorize()` | Group admin right |
| `lang:XX` (session) | Dim-3 | session locale | `list_leaf(locale_codes=...)` | Preferred language |
| `leaf:` | Calc-Dim | `collections` | set-theory queries | Cross-NS concept name |
| `ns:` | Calc-Dim | `collections` | set-theory queries | Namespace grouping |
| `lang:XX` (atom) | Calc-Dim | `collections` | locale ordering | Atom's language |
| `set:` (user) | Calc-Dim | `collections` | set-theory queries | User-defined set |
| `emo:` *(future)* | Calc-Dim | `collections` | set-theory queries | Emotion category |
| `type:` *(future)* | Calc-Dim | `collections` | set-theory queries | Semantic type |

---

## 7. Security Rules

These rules are invariants. Violating them introduces either security holes or
computational explosions.

1. **Dim-1 never enters `collections`.** Access scopes (`scope:`, `owner:`, `view:`) are stored exclusively in `chunk_access`. The migration in `_migrate_tables` promotes any legacy entries automatically.

2. **Dim-2 never enters SQL.** Capability flags (`role:`, `write:`, `manage:`) are session-level assertions evaluated by `authorize()`. They are never passed as SQL parameters.

3. **Dim-3 never enters access-control SQL.** `lang:` locale preferences are passed to `list_leaf(locale_codes=...)` for display ordering only, never to `chunk_access` or `check_chunk_access_any`.

4. **Capability bypasses are checked before dimension filtering.** `check_access` evaluates the librarian/system capability bypass (`role:librarian`) before calling any SQL. A bypassed check never reaches the SQL path.

5. **Calc-Dim must be eagerly registered.** Collection membership drives all multi-dimensional queries. An atom not in the right collections is effectively invisible to those queries. Use the async queue (`pending_derivations`) rather than skipping registration.

6. **Private atoms are never promoted by traversal.** When a private atom
   links to a universal concept, the reverse link (universal → private) is
   blocked by `check_access`. See §8.

---

## 8. Private Instance → Universal Concept Pattern

A common situation: NLP extraction creates a private copy of a concept
(e.g., `word:en:love` extracted from a private journal entry) that should
link to the universal concept `emo:love` without exposing the private atom.

```
Private atom (owner:user_alice)
  │
  └─ sys:instance_of ──▶  Universal concept (scope:sys:universal)
                                    │
                         check_access blocks reverse traversal
```

Rules:
- The link is **one-directional**: private → universal only.
- The universal concept remains universally readable.
- `get_incoming_links` on the universal concept will surface the private atom's
  key, but `check_access` will filter it out before it reaches the caller.
- The private atom's `leaf:love` collection membership is only visible to
  sessions that hold `owner:user_alice` or `view:user_alice`.

This preserves privacy while allowing the universal graph to remain coherent.

---

## 9. Session Context Namespace — Service Isolation

### 9.1 What Is Session Context?

Session context is a per-user key–value dictionary maintained by the kernel session object.
It tracks the *currently active* instance of each concept model — for example,
`active_note_root` holds the ID of the note the user is currently editing.
Session context is **not** stored in the graph; it lives in memory for the duration of
the session.

This is orthogonal to the four scope dimensions: scope dimensions govern *who can see
what data*, while session context governs *which instance is currently in focus* for a
given service.

### 9.2 The Collision Risk

All concept models store their active instance under a module-level constant:

```python
CONTEXT_KEY_ACTIVE = "active_note_root"   # NoteConcept
CONTEXT_KEY_ACTIVE = "active_fieldnote_root"   # FieldNoteConcept
```

This is safe as long as each concept class is used by **exactly one UI service**.
The problem arises when the same concept class is reused across multiple services.
Example: the Note app and Loom both use `NoteConcept`. Without isolation, whichever
service called `note.new` last overwrites `active_note_root`, causing the other service
to silently load the wrong document on the next request.

### 9.3 The `namespace` Parameter

`BaseConcept.__init__` accepts an optional `namespace: str`. When provided, all session
context keys are automatically prefixed:

| `namespace` | Effective context key |
|---|---|
| `None` (default) | `active_note_root` |
| `"loom"` | `loom:active_note_root` |
| `"fieldnote"` | `fieldnote:active_note_root` |

The concept class itself does not change. The kernel handler passes the appropriate
namespace at instantiation:

```python
# Note app — no namespace (backward-compatible)
concept = NoteConcept(session)

# Loom — isolated context
concept = NoteConcept(session, namespace="loom")
```

### 9.4 RPC Naming Convention

To let the kernel dispatch to the right namespace, services that share a concept model
use a prefixed RPC method name:

```
note.new      →  Note app   (namespace=None)
loom.note.new →  Loom       (namespace="loom")
```

The client calls the prefixed method; the kernel resolves the namespace from the prefix.
The concept class implementation is shared — only the context key differs.

### 9.5 Rules

| Rule | Why |
|---|---|
| Every `get_context` / `set_context` call goes through `self._ctx_key()` | Prevents raw key collision |
| Each UI service that reuses a concept class gets a unique namespace string | Guarantees session-level isolation |
| `namespace=None` preserves the bare key | Backward-compatible with existing services |
| New RPC prefixes follow `{service}.{concept}.{op}` | Kernel can dispatch to the right namespace without inspecting the request body |
| A concept class that is only ever used by one service does not need a namespace | Unnecessary complexity |

---

## 10. Multi-Store Architecture — Nucleus, Cell, Group

AKASHA uses **three tiers of SQLite databases** to separate universal shared knowledge from private user data and group collaboration spaces. Each tier has a distinct write path, a distinct scope tag, and a distinct runtime object.

### 10.1 The Three Stores

```
data/
  central/
    nucleus.db          ← Nucleus — shared by all cells
  cells/
    {client_id}/
      l_cortex.db       ← Per-user local cell
  groups/
    {group_id}/
      g_space.db        ← Per-group collaboration space
```

| Store | DB path | Runtime class | Scope tag | Who writes |
|---|---|---|---|---|
| **Nucleus** | `data/central/nucleus.db` | `NucleusEngine` | `scope:sys:universal` | LIBRARIAN, ADMIN (via `scope=universal`); auto-generated proto-words |
| **Local cell** | `data/cells/{id}/l_cortex.db` | `AkashaEngine` | `owner:user_{id}`, `view:user_{id}` | Any authenticated user (private writes) |
| **Group space** | `data/groups/{gid}/g_space.db` | `GroupEngine` | `scope:group_{gid}` | Donation API (`dont.send`); group librarians |

### 10.2 The Two Write Modes

**Private write** (default): atom goes to the caller's local cell DB only.
```
kernel.memory.write  text="My private thought"
→ AkashaEngine (l_cortex.db)  scope: [owner:user_alice, view:user_alice]
```

**Universal write** (`scope=universal`, requires LIBRARIAN/ADMIN): atom goes to the nucleus DB **only** — it is never duplicated into the caller's local cell.
```
kernel.memory.write  text="The word 'philosophy' ..."  scope=universal  alias=word:en:philosophy
→ NucleusEngine (nucleus.db)  scope: [scope:sys:universal]
```

This prevents data duplication: a librarian's cell does not accumulate copies of the shared ontology.

### 10.3 Proto-Words and the Nucleus

When any qualified alias such as `word:en:philosophy` is registered, `_ensure_protoword()` creates a **bare proto-word atom** for the unqualified term `philosophy`. This acts as a universal structural anchor that all namespace variants (word:en:philosophy, emo:philosophy, …) can link to.

**Key design decisions:**
- The proto-word key is `sha256("philosophy")` — deterministic, content-addressed.
- The proto-word is stored **in the nucleus only** (never in the local cell), tagged `scope:sys:universal`.
- If the nucleus is not available, the proto-word falls back to the local cell (degraded mode).
- The same sha256 key means any cell that independently creates the proto-word will land on the exact same key — no merge conflicts across cells.

### 10.4 The Read Fallback Chain

Every read operation that needs to resolve an alias or fetch atom content follows a three-level fallback:

```
1. Local cell (l_cortex.db)
      │ not found?
      ▼
2. Nucleus (nucleus.db)
      │ not found?
      ▼
3. Group engines (g_space.db for each group the caller belongs to)
```

This chain is implemented identically in two places:

- `lib/akasha/resolver.py:ContextResolver.resolve()` — alias resolution for `$`-references and bare names
- `lib/akasha/consciousness.py:ConsciousnessEngine.generate_view()` — content and alias lookup for `dive.look`

The IAM scope filter (`allowed_scopes`) is applied at each level: a nucleus atom is only returned if `scope:sys:universal` is in the caller's scopes, and a group atom is only returned if the corresponding `scope:group_{gid}` is present.

### 10.5 Session Initialization

At session creation (`AkashaSession.__init__`), the kernel:

1. Opens the caller's local cell DB as `session.local_cortex` (`AkashaEngine`).
2. Attaches the nucleus as `session.nucleus` (`NucleusEngine`) — shared single instance across all sessions.
3. Calls `iam.get_client_groups(client_id)` and opens a `GroupEngine` for each group → `session.group_engines: Dict[str, GroupEngine]`.
4. Passes `nucleus` and `group_engines` to `ConsciousnessEngine` so `generate_view()` has access to all three stores.

```python
session.local_cortex  → AkashaEngine("data/cells/alice/l_cortex.db")
session.nucleus       → NucleusEngine("data/central/nucleus.db")
session.group_engines → {
    "history_lab": GroupEngine("history_lab", "data"),
    "dig2026":     GroupEngine("dig2026", "data"),
}
```

### 10.6 Group Donation vs. Open Share

Atoms reach a group space via the **Delegation & Donation Sets** API (`dont.*`). Two modes are available:

| Mode | Implementation | Effect on original | Collaboration safety |
|---|---|---|---|
| **Copy** (default) | Atom copied to group DB | Unchanged | Group can edit copy independently; original safe |
| **Open** | Original atom's `chunk_access` extended | Scope widened | No copy; group sees same atom; edits affect original |

Copy mode is the recommended default for group sharing because it allows group members to collaboratively modify or extend the copy without risking the original author's data. Re-integration of group work back into the origin is a future design problem.
