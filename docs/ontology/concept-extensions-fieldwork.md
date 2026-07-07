# AKASHA Concept Model Extension Specifications — Fieldwork

This document covers the Fieldwork concept models: structured data collection
tools designed for qualitative and quantitative observation in the field.

**FieldNote** provides a flat, chronological timeline of timestamped observations
anchored to a research context (project, region, season). It is the primary tool
for capturing raw qualitative evidence during fieldwork, experiments, or any
domain where time-tagged entries matter more than document hierarchy.

**Survey** provides a structured questionnaire graph — questions, answer options,
and respondent responses — with a tri-linked topology that allows traversal from
any of three perspectives: by survey, by question, or by respondent. It is the
primary tool for collecting structured quantitative and categorical data at scale.

Both models produce atoms that feed naturally into the Intelligence tier analysis
pipeline (see `concept-model-intelligence.md`): FieldNote observations and Survey
responses can be indexed as Aggregation units, Synthesis sources, or Presentation
nodes without copying data.

All concept models are registered automatically via the **Concept Model Plugin Registry**
(`lib/akasha/concepts/registry.py`). See `docs/concept-model-spec.md §7` for the plugin
authoring guide.

---

## Table of Contents

1. [FieldNote](#1-fieldnote)
   - [1.1 Design Rationale](#11-design-rationale)
   - [1.2 Cortex Topology](#12-cortex-topology)
   - [1.3 Root Atom Metadata](#13-root-atom-metadata)
   - [1.4 Observation Atom Metadata](#14-observation-atom-metadata)
   - [1.5 Kernel Methods](#15-kernel-methods)
   - [1.6 CLI Shorthand Reference](#16-cli-shorthand-reference)
   - [1.7 Workflow Example](#17-workflow-example)
   - [1.8 Web Application](#18-web-application)
2. [Survey](#2-survey)
   - [2.1 Design Rationale](#21-design-rationale)
   - [2.2 Cortex Topology](#22-cortex-topology)
   - [2.3 Atom Metadata Reference](#23-atom-metadata-reference)
   - [2.4 Kernel Methods](#24-kernel-methods)
   - [2.5 CLI Shorthand Reference](#25-cli-shorthand-reference)
   - [2.6 Workflow Example](#26-workflow-example)

---

## 1. FieldNote

**Source:** `lib/akasha/concepts/fieldnote.py`  
**Context key:** `active_fieldnote_root`  
**Global index:** `set:fieldnote:index`

### 1.1 Design Rationale

FieldNote models a flat, context-tagged field observation record. It is
intentionally simpler than the Note concept:

- **Note** is a hierarchical document (chapters, sections, paragraphs).
- **FieldNote** is a flat timeline of observations anchored to a research
  context — project, geographic region, and season.

Typical use: recording observations during fieldwork, experiments, or any
domain where timestamped, context-tagged entries matter more than document
structure.

### 1.2 Cortex Topology

```
Root atom  (concept="fieldnote", role="root")
  │
  ├── sys:top     ──▶  Observation 1
  │                         │
  │                    sys:next ──▶  Observation 2
  │                                       │
  │                                  sys:next ──▶  Observation N
  │
  └── sys:bottom  ──────────────────────────────▶  Observation N
```

All observation atoms are also linked from the root via `sys:contains`.
The timeline uses the same `sys:top/next/previous/bottom` pattern as Note
and Cockpit.

**Namespace contract (two-namespace rule):**

| Set | Contents |
|-----|----------|
| `set:fieldnote:index` | Global index — all root IDs across all users |
| `set:fieldnote:{concept_id}` | Content atoms for this fieldnote |
| `set:concept:{concept_id}` | Concept catalog (BaseConcept standard) |

### 1.3 Root Atom Metadata

| Field | Type | Description |
|-------|------|-------------|
| `type` | `"concept"` | Fixed |
| `concept` | `"fieldnote"` | Fixed |
| `role` | `"root"` | Fixed |
| `title` | string | Human-readable name |
| `project` | string \| null | Research project label |
| `region` | string \| null | Geographic or logical region |
| `season` | string \| null | Season, cycle, or time window label |
| `created_at` | float | Unix timestamp |

### 1.4 Observation Atom Metadata

| Field | Type | Description |
|-------|------|-------------|
| `type` | `"observation"` | Fixed |
| `role` | `"observation"` | Fixed |
| `created_at` | float | Unix timestamp |

---

### 1.5 Kernel Methods

#### `fieldnote.new`

Create a new FieldNote. Automatically becomes the session's active FieldNote.

**Params (`data`):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | Yes | FieldNote title |
| `project` | string | No | Research project |
| `region` | string | No | Geographic or logical region |
| `season` | string | No | Season or cycle label |

**Response:**

```json
{
  "result": {
    "status": "created",
    "fieldnote_id": "a1b2c3...",
    "title": "Survey Alpha",
    "project": "Mediterranean Survey",
    "region": "Calabria",
    "season": "Spring 2026"
  }
}
```

**CLI:** `fn.new <title> [project] [region] [season]`

---

#### `fieldnote.ls`

List all FieldNotes accessible to the current user, newest first.

**Params (`data`):** *(none)*

**Response:**

```json
{
  "result": {
    "fieldnotes": [
      {
        "fieldnote_id": "a1b2c3...",
        "title": "Survey Alpha",
        "project": "Mediterranean Survey",
        "region": "Calabria",
        "season": "Spring 2026",
        "created_at": 1748300000.0
      }
    ],
    "count": 1
  }
}
```

**CLI:** `fn.ls`

---

#### `fieldnote.open`

Mount an existing FieldNote as the session's active record.

**Params (`data`):**

| Field | Type | Required |
|-------|------|----------|
| `fieldnote_id` | string | Yes |

**Response:**

```json
{
  "result": {
    "status": "opened",
    "fieldnote_id": "a1b2c3...",
    "title": "Survey Alpha",
    "project": "Mediterranean Survey",
    "region": "Calabria",
    "season": "Spring 2026"
  }
}
```

**Errors:**

| Code | Condition |
|------|-----------|
| -32002 | Atom not found or is not a fieldnote root |
| -32602 | `fieldnote_id` missing |

**CLI:** `fn.open <fieldnote_id>`

---

#### `fieldnote.add`

Append an observation to the active FieldNote.

**Params (`data`):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | Yes | Observation content |

**Response:**

```json
{
  "result": {
    "status": "added",
    "observation_id": "f0a1b2...",
    "preview": "Mosaic fragment discovered at grid ref..."
  }
}
```

**Errors:** -32002 if no active FieldNote; -32602 if `text` is empty.

**CLI:** `fn.add <observation text>`

---

#### `fieldnote.read`

Read all observations in chronological order (top → bottom).

**Params (`data`):** *(none)*

**Response:**

```json
{
  "result": {
    "observations": [
      {
        "id": "f0a1b2...",
        "content": "Mosaic fragment discovered at grid ref NE-14.",
        "role": "observation",
        "created_at": 1748300100.0
      }
    ],
    "count": 1
  }
}
```

**CLI:** `fn.read`

---

#### `fieldnote.rm`

Delete the active FieldNote and clear the session context.

**Params (`data`):** *(none)*

**Response:**

```json
{"result": {"status": "deleted", "fieldnote_id": "a1b2c3..."}}
```

**Errors:** -32002 if no active FieldNote.

**CLI:** `fn.rm`

---

### 1.6 CLI Shorthand Reference

| Shorthand | Method | Arguments |
|-----------|--------|-----------|
| `fn.new <title> [project] [region] [season]` | `fieldnote.new` | `title`, `project`, `region`, `season` |
| `fn.ls` | `fieldnote.ls` | — |
| `fn.open <fieldnote_id>` | `fieldnote.open` | `fieldnote_id` |
| `fn.add <text>` | `fieldnote.add` | `text` (absorbs remaining tokens) |
| `fn.read` | `fieldnote.read` | — |
| `fn.rm` | `fieldnote.rm` | — |

The `fn.new` command passes arguments positionally. Omit trailing arguments to
leave the corresponding context fields as `null`:

```
fn.new Ravenna Survey                         # title only
fn.new Ravenna Survey "Mediterranean"         # title + project
fn.new Ravenna Survey "Mediterranean" Calabria Spring-2026
```

### 1.7 Workflow Example

```python
# Create a new record
rpc("fieldnote.new", {
    "title": "Ravenna Survey",
    "project": "Mediterranean",
    "region": "Emilia-Romagna",
    "season": "Spring 2026"
}, token=token)

# Add observations
rpc("fieldnote.add", {"text": "Apse mosaic — partial. Blue tesserae dominant."}, token=token)
rpc("fieldnote.add", {"text": "Inscriptions below apse: Latin, 6th century."}, token=token)

# Read back
result = rpc("fieldnote.read", {}, token=token)
# → {"observations": [...], "count": 2}

# List all fieldnotes
all_fn = rpc("fieldnote.ls", {}, token=token)

# Resume later
rpc("fieldnote.open", {"fieldnote_id": "a1b2c3..."}, token=token)
rpc("fieldnote.add", {"text": "Day 2: Grid NE-14 fully excavated."}, token=token)

# Delete
rpc("fieldnote.rm", {}, token=token)
```

### 1.8 Web Application

**Path:** `services/static/fieldnote/index.html`  
**Served at:** `/fieldnote/` (via `python -m services.app_server --app fieldnote`)

#### Overview

The FieldNote web application is a single-page HTML/JS app that wraps the
`fieldnote.*` kernel methods in a purpose-built observation recording UI. It
demonstrates the standard AKASHA web app pattern:

1. Pre-auth `kernel.auth.verify` → obtain `session_token`
2. All subsequent calls use `{session_token, data}` envelope
3. No server-side session state — all context lives in `sessionToken` JS variable

#### Layout

```
┌─ Header ─────────────────────────────────────────────────────┐
│  AKASHA // FIELDNOTE   [active title — context]   ◉ user    │
├─ Sidebar ──────────────┬─ Content area ────────────────────────┤
│  FieldNotes            │  Toolbar: title / project / region /  │
│  ─ item (active) ─     │          season  [New] [Read] [Delete] │
│    title               │  ─────────────────────────────────────│
│    project · region    │  Observation textarea   [Add]          │
│  ─ item ─              │  ─────────────────────────────────────│
│    …                   │  Readout (scrolling observations)      │
│                        │  ─────────────────────────────────────│
│                        │  Status bar                            │
└────────────────────────┴───────────────────────────────────────┘
```

#### Kernel Method Mapping

| UI action | Kernel method | Notes |
|-----------|---------------|-------|
| Sidebar list on load | `fieldnote.ls` | Populates list; filters by session scopes |
| "New" button | `fieldnote.new` | Sends title + optional project/region/season |
| Sidebar item click | `fieldnote.open` | Mounts fieldnote; triggers auto-read |
| "Add" / Ctrl+Enter | `fieldnote.add` | Appends observation; re-reads after write |
| "↻ Read" button | `fieldnote.read` | Returns `{observations: [...], count: N}` |
| "Delete" → confirm | `fieldnote.rm` | Two-step confirmation modal before delete |

#### Observation Rendering

Observations are rendered with role-based border colors. The `role` field
defaults to `"observation"` in the current model; additional roles
(`site`, `layer`, `find`, `source`, `media`) are reserved for future
FieldNote sub-types that record richer metadata.

| Role | Color | Intended use |
|------|-------|--------------|
| `observation` | `#00ffcc` | General timestamped note |
| `find` | `#ff9900` | Physical artifact or discovery |
| `site` | `#4488ff` | Site-level context record |
| `layer` | `#aa44ff` | Stratigraphic layer description |
| `source` | `#888888` | Bibliographic or documentary reference |
| `media` | `#666666` | Photo, drawing, or media reference |

#### Bugs Fixed During Review

The reviewed replacement code contained two errors that were corrected before
integration:

| Function | Bug | Fix applied |
|----------|-----|-------------|
| `addObservation` | Called `rpc('fieldnote.observation', ...)` — method does not exist | Changed to `rpc('fieldnote.add', ...)` |
| `refreshFieldNote` | `Array.isArray(res)` — `fieldnote.read` returns `{observations, count}`, not an array | Changed to `res.observations \|\| []` and `res.count ?? 0` |

The improved `renderObservations` (role-based colors) from the reviewed version
was adopted as-is.

---

---

## 2. Survey

**Source:** `lib/akasha/concepts/survey.py`  
**Context key:** `active_survey_root`  
**Global index:** `set:survey:index`

### 2.1 Design Rationale

Survey models a structured questionnaire — a hierarchy of questions, answer
options, and respondent responses — as a pure graph topology. Unlike Note
(hierarchical document) or FieldNote (flat chronological record), Survey is a
*multi-relational* structure: each response atom is **tri-linked** to its survey
root, its question, and its respondent simultaneously.

Typical use: building surveys, collecting and storing structured answers, and
traversing results by question, by respondent, or globally.

### 2.2 Cortex Topology

```
Survey Root
  ├── sys:contains ──▶  Question A
  │                        ├── sys:contains ──▶  Option A1
  │                        ├── sys:contains ──▶  Option A2
  │                        └── sys:contains ──▶  Response (Respondent 1 / Answer X)
  │                                                  └── sys:part_of ──▶ Survey Root
  │                                                  └── sys:part_of ──▶ Question A
  │                                                  └── sys:part_of ──▶ Respondent 1 atom
  ├── sys:contains ──▶  Respondent 1 atom
  └── sys:contains ──▶  Response (tri-linked)
```

**Set layout:**

| Set | Contents |
|-----|----------|
| `set:survey:index` | Global index — all survey root IDs |
| `set:survey:{id}` | All content atoms for this survey |
| `set:survey:{id}:questions` | Question atoms |
| `set:survey:{id}:options` | Option atoms |
| `set:survey:{id}:respondents` | Respondent atoms |
| `set:survey:{id}:responses` | Response atoms |
| `set:concept:{id}` | Concept catalog (root only, BaseConcept standard) |

**Tri-link pattern for responses:**

A response atom carries `sys:contains` / `sys:part_of` links to three parents:
survey root, the question being answered, and the respondent atom. This allows
traversal from any of the three perspectives without secondary index lookups.

### 2.3 Atom Metadata Reference

**Survey root** (`op_new`):

| Field | Value |
|-------|-------|
| `type` | `"concept"` |
| `concept` | `"survey"` |
| `role` | `"root"` |
| `title` | string |
| `description` | string |
| `created_at` | float |

**Question** (`op_add_question`):

| Field | Value |
|-------|-------|
| `type` | `"survey_question"` |
| `question_type` | `"free_text"` \| `"single_choice"` \| `"multi_choice"` \| ... |
| `order` | int \| null |

**Option** (`op_add_option`):

| Field | Value |
|-------|-------|
| `type` | `"survey_option"` |
| `label` | display string |
| `value` | string (defaults to label) |

**Respondent** (`op_add_respondent`):

| Field | Value |
|-------|-------|
| `type` | `"survey_respondent"` |
| `respondent_id` | caller-supplied identifier string |
| `attributes` | dict (arbitrary metadata) |

**Response** (`op_add_response`):

| Field | Value |
|-------|-------|
| `type` | `"survey_response"` |
| `question_id` | key of the question atom |
| `respondent_atom` | key of the respondent atom (not the `respondent_id` string) |
| `answer` | any JSON-serialisable value |
| `timestamp` | float |

### 2.4 Kernel Methods

#### `survey.new`

Create a new Survey. Becomes the session's active survey.

**Params:** `title` (required), `description` (optional)

**Response:** `{"status": "created", "survey_id": "...", "title": "..."}`

**CLI:** `sv.new <title> [description]`

---

#### `survey.open`

Mount an existing survey as the active survey.

**Params:** `survey_id` (required)

**Response:** `{"status": "opened", "survey_id": "...", "title": "...", "description": "..."}`

**Errors:** `-32002` if atom is not a survey root; `-32602` if `survey_id` missing.

**CLI:** `sv.open <survey_id>`

---

#### `survey.ls`

List all surveys accessible to the current user, newest first.

**Params:** *(none)*

**Response:**

```json
{
  "result": {
    "surveys": [
      {"survey_id": "...", "title": "...", "description": "...", "created_at": 0.0}
    ],
    "count": 1
  }
}
```

**CLI:** `sv.ls`

---

#### `survey.q.add`

Add a question to the active survey.

**Params:** `text` (required), `qtype` (optional, default `"free_text"`), `order` (optional int)

**Response:** `{"status": "question_added", "question_id": "...", "text": "..."}`

**CLI:** `sv.q <text> [qtype]`

---

#### `survey.opt.add`

Add an answer option to a question.

**Params:** `question_id` (required), `label` (required), `value` (optional, defaults to label)

**Response:** `{"status": "option_added", "option_id": "..."}`

**CLI:** `sv.opt <question_id> <label> [value]`

---

#### `survey.res.add`

Register a respondent in the active survey.

**Params:** `respondent_id` (required), `attributes` (optional dict)

**Response:** `{"status": "respondent_added", "respondent_atom": "<hex key>"}`

> Note: `respondent_atom` is the Cortex atom key. Pass this key (not `respondent_id`) to `survey.ans`.

**CLI:** `sv.who <respondent_id>`

---

#### `survey.ans`

Record a tri-linked response.

**Params:** `question_id`, `respondent_atom`, `answer` (all required)

**Response:** `{"status": "response_added", "response_id": "..."}`

**CLI:** `sv.ans <question_id> <respondent_atom> <answer>`

---

#### `survey.list`

Return the structural inventory of the active survey (lists of atom keys by category).

**Params:** *(none)*

**Response:**

```json
{
  "result": {
    "survey_id": "...",
    "questions":   ["..."],
    "options":     ["..."],
    "respondents": ["..."],
    "responses":   ["..."]
  }
}
```

**CLI:** `sv.list`

---

#### `survey.rm`

Delete the active survey and clear session context.

**Params:** *(none)*

**Response:** `{"status": "deleted", "survey_id": "..."}`

**CLI:** `sv.rm`

---

### 2.5 CLI Shorthand Reference

| Shorthand | Method | Arguments |
|-----------|--------|-----------|
| `sv.new <title> [description]` | `survey.new` | `title`, `description` |
| `sv.open <survey_id>` | `survey.open` | `survey_id` |
| `sv.ls` | `survey.ls` | — |
| `sv.q <text> [qtype]` | `survey.q.add` | `text` (absorbs remaining tokens), `qtype` |
| `sv.opt <question_id> <label> [value]` | `survey.opt.add` | `question_id`, `label`, `value` |
| `sv.who <respondent_id>` | `survey.res.add` | `respondent_id` |
| `sv.ans <question_id> <respondent_atom> <answer>` | `survey.ans` | `question_id`, `respondent_atom`, `answer` |
| `sv.list` | `survey.list` | — |
| `sv.rm` | `survey.rm` | — |

### 2.6 Workflow Example

```python
# Create a survey
sv = rpc("survey.new", {"title": "Habitat Survey 2026", "description": "Species distribution"})
survey_id = sv["survey_id"]

# Add questions
q1 = rpc("survey.q.add", {"text": "Primary habitat type?", "qtype": "single_choice"})
q1_id = q1["question_id"]

q2 = rpc("survey.q.add", {"text": "Observation notes", "qtype": "free_text"})
q2_id = q2["question_id"]

# Add options to Q1
rpc("survey.opt.add", {"question_id": q1_id, "label": "Forest"})
rpc("survey.opt.add", {"question_id": q1_id, "label": "Wetland"})
rpc("survey.opt.add", {"question_id": q1_id, "label": "Coastal"})

# Register respondents
r1 = rpc("survey.res.add", {"respondent_id": "observer_A", "attributes": {"team": "north"}})
r1_atom = r1["respondent_atom"]   # ← Cortex atom key, needed for survey.ans

r2 = rpc("survey.res.add", {"respondent_id": "observer_B"})
r2_atom = r2["respondent_atom"]

# Record responses (tri-linked: survey ↔ question ↔ respondent)
rpc("survey.ans", {"question_id": q1_id, "respondent_atom": r1_atom, "answer": "Forest"})
rpc("survey.ans", {"question_id": q2_id, "respondent_atom": r1_atom, "answer": "Dense canopy, ~30m height."})
rpc("survey.ans", {"question_id": q1_id, "respondent_atom": r2_atom, "answer": "Coastal"})

# Inspect structure
structure = rpc("survey.list", {})
# → {"survey_id": ..., "questions": [q1_id, q2_id], "respondents": [...], "responses": [...]}

# Resume in another session
rpc("survey.open", {"survey_id": survey_id})

# List all surveys
all_surveys = rpc("survey.ls", {})

# Delete
rpc("survey.rm", {})
```

---
