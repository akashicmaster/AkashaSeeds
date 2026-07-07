# AKASHA Concept Model Specification (Intelligence)

This document covers the Intelligence tier of the AKASHA concept model ecosystem.
The Intelligence tier spans the full data-to-insight pipeline:

1. **Collection** — structured ingestion of raw facts with traceable provenance (Fact)
2. **Aggregation** — quantitative partitioning, statistical measurement, and cross-group analysis (Aggregation)
3. **Interpretation** — qualitative coding, thematic grouping, and evidence-backed claims (Synthesis)
4. **Reconciliation** — premise-bound conflict resolution and auditable view construction (Curation)
5. **Decision Support** — requirement-centric orchestration of the full reasoning cycle (Intelligence)
6. **Presentation** — structured assembly into a communicable, audience-ready deliverable (Presentation)

The six models form a composable pipeline. Aggregation and Synthesis draw on the same source
corpus and produce complementary outputs — numerical patterns and argued interpretations.
Curation reconciles conflicting evidence under stated premises, producing auditable views and
conclusions. Intelligence orchestrates the full reasoning cycle from requirements through
assessments, estimates, and recommendations to recorded decisions. Presentation assembles all
upstream outputs into a coherent, audience-ready deliverable. Fact anchors the entire pipeline
to credibility-scored, event-sourced source material.

All concept models are registered automatically via the **Concept Model Plugin Registry**
(`lib/akasha/concepts/registry.py`). See `docs/concept-model-spec.md §7` for the plugin
authoring guide.

---

## Table of Contents

1. [Fact](#1-fact)
   - [1.1 Design Rationale](#11-design-rationale)
   - [1.2 Cortex Topology](#12-cortex-topology)
   - [1.3 Kernel Methods](#13-kernel-methods)
   - [1.4 CLI Shorthand Reference](#14-cli-shorthand-reference)
   - [1.5 Credibility Model](#15-credibility-model)
   - [1.6 Workflow Example](#16-workflow-example)
2. [Aggregation](#2-aggregation)
   - [2.1 Design Rationale](#21-design-rationale)
   - [2.2 Cortex Topology](#22-cortex-topology)
   - [2.3 Atom Metadata Reference](#23-atom-metadata-reference)
   - [2.4 Kernel Methods](#24-kernel-methods)
   - [2.5 CLI Shorthand Reference](#25-cli-shorthand-reference)
   - [2.6 Workflow Example](#26-workflow-example)
   - [2.7 Known Constraints](#27-known-constraints)
   - [2.8 Broader Applications](#28-broader-applications)
3. [Synthesis](#3-synthesis)
   - [3.1 Design Rationale](#31-design-rationale)
   - [3.2 Cortex Topology](#32-cortex-topology)
   - [3.3 Atom Metadata Reference](#33-atom-metadata-reference)
   - [3.4 Kernel Methods](#34-kernel-methods)
   - [3.5 CLI Shorthand Reference](#35-cli-shorthand-reference)
   - [3.6 Workflow Example](#36-workflow-example)
   - [3.7 Cross-Concept Application Patterns](#37-cross-concept-application-patterns)
4. [Curation](#4-curation)
   - [4.1 Design Rationale](#41-design-rationale)
   - [4.2 Cortex Topology](#42-cortex-topology)
   - [4.3 Atom Metadata Reference](#43-atom-metadata-reference)
   - [4.4 Kernel Methods](#44-kernel-methods)
   - [4.5 CLI Shorthand Reference](#45-cli-shorthand-reference)
   - [4.6 Conflict Policies](#46-conflict-policies)
   - [4.7 Workflow Example](#47-workflow-example)
   - [4.8 Cross-Concept Integration](#48-cross-concept-integration)
5. [Intelligence](#5-intelligence)
   - [5.1 Design Rationale](#51-design-rationale)
   - [5.2 Cortex Topology](#52-cortex-topology)
   - [5.3 Atom Metadata Reference](#53-atom-metadata-reference)
   - [5.4 Kernel Methods](#54-kernel-methods)
   - [5.5 CLI Shorthand Reference](#55-cli-shorthand-reference)
   - [5.6 Workflow Example](#56-workflow-example)
   - [5.7 Cross-Concept Integration](#57-cross-concept-integration)
6. [Presentation](#6-presentation)
   - [6.1 Design Rationale](#61-design-rationale)
   - [6.2 Cortex Topology](#62-cortex-topology)
   - [6.3 Atom Metadata Reference](#63-atom-metadata-reference)
   - [6.4 Kernel Methods](#64-kernel-methods)
   - [6.5 CLI Shorthand Reference](#65-cli-shorthand-reference)
   - [6.6 Workflow Example](#66-workflow-example)
   - [6.7 Cross-Concept Application Patterns](#67-cross-concept-application-patterns)

---

## 1. Fact

**Source:** `lib/akasha/concepts/fact.py`  
**Context key:** `active_fact_root`  
**CLI prefix:** `ft.*`

### 1.1 Design Rationale

Fact is a concept model for **recording, classifying, and tracing facts** extracted from sources. It is designed for use cases where the quality and provenance of evidence must be strictly managed — journalism, policy research, and intelligence analysis.

**Direct Fact** is a fact verified by a single Source alone. Credibility is derived directly from the Source's evaluated value.

**Inferred Fact** is a fact derived from multiple Sources through curation. Credibility is calculated as:

```
credibility = extraction_confidence
            × inference_confidence
            × Σ(source_i.credibility_effective × weight_i / total_weight)
```

When an LLM is used, each algorithm's confidence is adjusted as `task_confidence × llm_trust`.

**Source Eval** is event-sourced. Each call to `fact.source.eval` appends an eval atom to the `source_evals` subset. The Source atom is immutable. `_effective_source_credibility()` always reads the latest evaluated value.

**FactSet** is a purpose-driven grouping of facts. The same Fact can belong to multiple FactSets simultaneously (not a fixed hierarchy).

### 1.2 Cortex Topology

```
FactRoot  (concept="fact", role="root")
  │
  ├─ fact:has_source      ──▶  SourceAtom       {quelle_level, credibility, independence, ...}
  ├─ fact:has_source_eval ──▶  SourceEvalAtom   {source_id, updates, previous}
  ├─ fact:has_fact        ──▶  DirectFactAtom   {origin: "direct",   fact_type, credibility}
  ├─ fact:has_fact        ──▶  InferredFactAtom {origin: "inferred", provenance, credibility}
  ├─ fact:has_fact_set    ──▶  FactSetAtom      {label, criteria}
  ├─ fact:has_entity      ──▶  EntityLinkAtom   {fact_id, entity_id, entity_type, role}
  └─ fact:has_provenance  ──▶  ProvenanceAtom   {fact_id, provenance}

DirectFactAtom   ──fact:derived_from_source──▶ SourceAtom
InferredFactAtom ──fact:derived_from_source──▶ SourceAtom  (multiple)
InferredFactAtom ──fact:has_provenance──▶      ProvenanceAtom
```

**Set layout:**

| Set | Contents |
|-----|----------|
| `set:fact:index` | All Fact root atoms (global) |
| `set:fact:{id}` | All atoms in this Fact collection |
| `set:fact:{id}:sources` | Source atoms |
| `set:fact:{id}:source_evals` | Source eval atoms (separate from sources) |
| `set:fact:{id}:facts` | Direct / Inferred Fact atoms |
| `set:fact:{id}:fact_sets` | FactSet atoms |
| `set:fact:{id}:entities` | Entity link atoms |
| `set:fact:{id}:provenances` | Provenance atoms |

### 1.3 Kernel Methods

| Method | IAM | Description |
|--------|-----|-------------|
| `fact.new` | write | Create a new Fact collection |
| `fact.open` | write | Activate an existing Fact collection |
| `fact.ls` | read | List all Fact collections |
| `fact.map` | read | Return the structure map of the active Fact collection |
| `fact.rm` | write | Soft-delete the active Fact collection |
| `fact.source.add` | write | Add a Source (evidentiary anchor) |
| `fact.source.eval` | write | Record an updated credibility evaluation for a Source |
| `fact.add` | write | Add a Direct Fact |
| `fact.claim` | write | Record a Claim Fact |
| `fact.absent` | write | Record an Absence Fact (Intelligence Gap) |
| `fact.infer` | write | Add an Inferred Fact |
| `fact.set.new` | write | Create a FactSet |
| `fact.set.add` | write | Add a Fact to a FactSet |
| `fact.entity.link` | write | Link a Fact to an Entity |
| `fact.diagnose` | read | Diagnose quality and completeness of the collection |
| `fact.trace` | read | Trace the evidence chain of a Fact |

**`fact.source.add` key parameters:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `url` | string | `""` | Source URL |
| `kind` | string | `"news_article"` | Kind (`news_article` / `official_doc` / `testimony` / `sensor` / `social_media` / `academic_paper` / `legal_doc` / `financial_report` / `other`) |
| `quelle_level` | int | `2` | Source tier (1=primary, 2=secondary, 3+=tertiary) |
| `independence` | float | `0.5` | Independence 0.0–1.0 |
| `credibility` | float | `0.5` | Initial credibility 0.0–1.0 |

**`fact.add` key parameters:**

| Field | Type | Description |
|-------|------|-------------|
| `fact_type` | string | `event` / `state` / `claim` / `relation` / `absence` |
| `content` | string | Fact statement (required) |
| `source_id` | string | Backing Source ID (required) |
| `status` | string | `active` / `disputed` / `retracted` / `superseded` / `unverified` |

**`fact.infer` key parameters:**

| Field | Type | Description |
|-------|------|-------------|
| `fact_type` | string | `event` / `state` / `claim` / `relation` / `absence` |
| `content` | string | Inferred fact statement (required) |
| `inputs` | list | `[{source_id, weight, role}, ...]` (required) |
| `extraction_method` | string | `human` / `llm` / `rule_based` / `statistical` / `pattern_matching` / `hybrid` |
| `extraction_confidence` | float | 0.0–1.0 |
| `inference_method` | string | same as above |
| `inference_confidence` | float | 0.0–1.0 |

### 1.4 CLI Shorthand Reference

| CLI | Full method | Key args |
|-----|-------------|----------|
| `ft.new` | `fact.new` | `title`, `description?` |
| `ft.open` | `fact.open` | `fact_root_id` |
| `ft.ls` | `fact.ls` | — |
| `ft.map` | `fact.map` | — |
| `ft.rm` | `fact.rm` | — |
| `ft.src.add` | `fact.source.add` | `url`, `kind`, `title`, `credibility?` |
| `ft.src.eval` | `fact.source.eval` | `source_id`, `credibility?` |
| `ft.add` | `fact.add` | `fact_type`, `content`, `source_id` |
| `ft.claim` | `fact.claim` | `speaker`, `content`, `source_id` |
| `ft.absent` | `fact.absent` | `description`, `source_id` |
| `ft.infer` | `fact.infer` | `fact_type`, `content`, `inputs` |
| `ft.set.new` | `fact.set.new` | `label` |
| `ft.set.add` | `fact.set.add` | `factset_id`, `fact_id` |
| `ft.ent.link` | `fact.entity.link` | `fact_id`, `entity_id`, `entity_type` |
| `ft.diagnose` | `fact.diagnose` | — |
| `ft.trace` | `fact.trace` | `fact_id` |

### 1.5 Credibility Model

**Direct Fact credibility:**

```
credibility = _effective_source_credibility(source_id)
```

Each call to `fact.source.eval` appends an eval atom to the `source_evals` subset (the Source atom is immutable). `_effective_source_credibility()` reads `updates.credibility` from the latest eval atom.

**Inferred Fact credibility (Fix 2: weight-normalised):**

```
credibility = extraction_conf × inference_conf × source_weighted

source_weighted = Σ(source_i.credibility_effective × weight_i / total_weight)
```

When using LLM: `algo_conf = task_confidence × llm_trust` (clamped to 0.0–1.0)

### 1.6 Workflow Example

```
# Create a Fact collection
akasha/user $ ft.new title="Prime Minister Speech Analysis"
{"status": "created", "concept_id": "a1b2...ef01", "title": "Prime Minister Speech Analysis"}

# Register sources
akasha/user $ ft.src.add url="https://example.gov/speech" kind="official_doc" title="PM Speech 2024" quelle_level=1 credibility=0.9
{"status": "source_added", "source_id": "b2c3...fg02", "credibility": 0.9}

akasha/user $ ft.src.add url="https://news.example.com/analysis" kind="news_article" credibility=0.6
{"source_id": "c3d4...hi03", "credibility": 0.6}

# Add a Direct Fact
akasha/user $ ft.add fact_type=event content="PM announced new climate policy on Jan 15" source_id=b2c3...fg02 event_time="2024-01-15"
{"status": "fact_added", "fact_id": "d4e5...jk04", "credibility": 0.9}

# Record a Claim (records what was said, not whether it is true)
akasha/user $ ft.claim speaker="PM Tanaka" content="We will achieve carbon neutrality by 2050" source_id=b2c3...fg02
{"status": "claim_added", "fact_id": "e5f6...lm05", "credibility": 0.9}

# Record an Absence Fact (Intelligence Gap)
akasha/user $ ft.absent description="No implementation timeline provided in the speech" source_id=b2c3...fg02
{"status": "absence_added", "fact_id": "f6g7...no06", "gap_type": "no_statement"}

# Update Source credibility (Source atom is immutable; an eval atom is appended)
akasha/user $ ft.src.eval source_id=c3d4...hi03 credibility=0.75
{"status": "source_evaluated", "eval_id": "g7h8...pq07"}

# Inferred Fact (derived from two Sources)
akasha/user $ ft.infer fact_type=state \
    content="Government is committed but lacks concrete implementation plan" \
    inputs=[{source_id:b2c3...fg02,weight:2,role:primary},{source_id:c3d4...hi03,weight:1,role:secondary}] \
    extraction_method=human extraction_confidence=0.85 \
    inference_method=human inference_confidence=0.8
{
  "status": "inferred_fact_added",
  "fact_id": "h8i9...rs08",
  "credibility": 0.612,        # 0.85 × 0.80 × (0.9×0.667 + 0.75×0.333)
  "source_weighted_credibility": 0.85
}

# Quality diagnosis
akasha/user $ ft.diagnose
{"counts": {"facts": 4, "sources": 2, ...}, "diagnosis": {"absence_facts": [...], ...}}

# Trace the evidence chain
akasha/user $ ft.trace fact_id=h8i9...rs08
{
  "fact_type": "state",
  "origin": "inferred",
  "credibility": 0.612,
  "credibility_breakdown": {
    "extraction_confidence": 0.85,
    "inference_confidence": 0.8,
    "source_weighted_credibility": 0.85,
    "formula": "extraction_conf × inference_conf × Σ(source_i.credibility × weight_i / total_weight)"
  }
}
```

*→ Back to [concept-model-spec.md](concept-model-spec.md) · [README](../README.md)*

---

## 2. Aggregation

**Source:** `lib/akasha/concepts/aggregation.py`  
**Context key:** `active_aggregation_root`  
**Global index:** `set:agg:index`

### 2.1 Design Rationale

Aggregation was designed alongside Survey as a statistical analysis layer that
sits above a survey's raw response data. However, the **5-layer model
(Unit → Group → Measure → Analysis → Hierarchy) is domain-agnostic** — the only
structural coupling to Survey is the `source_id` field in the root meta and the
`sys:for_source` / `sys:has_aggregation` links established at creation. Units are
ordinary Cortex atom keys; `agg.unit.add` does not enforce what kind of atom is
on the other end.

| Layer | Atom type | Purpose |
|-------|-----------|---------|
| **Unit** | Reference to any accessible Cortex atom | Selects the input data for this analysis — survey responses, observations, notes, or any atoms |
| **Group** | `agg_group` | Labels a named partition of units (e.g. demographic segment, thematic cluster, time window) |
| **Measure** | `agg_measure` | Attaches a key/value statistic to a group (e.g. mean, count, percentage, frequency) |
| **Analysis** | `agg_analysis` | Records a directed relation between two groups with a numeric score (e.g. correlation, chi-square, growth rate) |
| **Hierarchy** | `agg_hierarchy` | Nests groups under a labelled parent for multi-level structure (taxonomy, org chart, topic tree) |

A single survey — or any source corpus — can have multiple aggregation roots: one
per analysis run, per reporting period, or per research question. Each root is
independent and references source atoms by Cortex key without copying data.

See §2.8 for concrete applications of the model outside the Survey context.

### 2.2 Cortex Topology

```
AggregationRoot  (concept="aggregation", role="root")
  │
  ├── sys:for_source      ──▶  Survey Root  (present when source_id was supplied)
  │
  ├── agg:unit            ──▶  Any Cortex atom  [repeated per unit]
  │
  ├── agg:group           ──▶  Group atom
  │                               └── agg:member ──▶  Any Cortex atom  [per member]
  │
  │   (Group atom)
  │       └── agg:measure ──▶  Measure atom   [per statistic]
  │
  │   (Group A) ──agg:analysis_out──▶  Analysis atom ◀──agg:analysis_in── (Group B)
  │
  └── agg:hierarchy       ──▶  Hierarchy node
                                  └── agg:child ──▶  Group atom  [repeated per child]
```

Inverse link when the aggregation root was created against a survey:

```
Survey Root  ──sys:has_aggregation──▶  AggregationRoot
```

**Set layout:**

| Set | Contents |
|-----|----------|
| `set:agg:index` | Global index — all aggregation root IDs |
| `set:agg:{id}` | All content atoms for this aggregation |
| `set:agg:{id}:units` | Unit atom keys (references to survey response atoms) |
| `set:agg:{id}:groups` | Group atoms |
| `set:agg:{id}:measures` | Measure atoms |
| `set:agg:{id}:analysis` | Analysis relation atoms |
| `set:agg:{id}:hierarchy` | Hierarchy node atoms |
| `set:concept:{id}` | Concept catalog (concept-word "aggregation" only) |

### 2.3 Atom Metadata Reference

**Aggregation root** (`op_new`):

| Field | Value |
|-------|-------|
| `type` | `"concept"` |
| `concept` | `"aggregation"` |
| `role` | `"root"` |
| `source_id` | Cortex key of the source corpus root atom |
| `created_at` | float |

**Group** (`op_add_group`):

| Field | Value |
|-------|-------|
| `type` | `"agg_group"` |
| `label` | string |
| `created_at` | float |

**Measure** (`op_add_measure`):

| Field | Value |
|-------|-------|
| `type` | `"agg_measure"` |
| `group_id` | Cortex key of the parent group atom |
| `key` | statistic name (e.g. `"mean"`, `"count"`) |
| `value` | any JSON-serialisable value |
| `created_at` | float |

**Analysis** (`op_add_analysis`):

| Field | Value |
|-------|-------|
| `type` | `"agg_analysis"` |
| `src` | Cortex key of the source group |
| `dst` | Cortex key of the destination group |
| `relation` | string (e.g. `"correlation"`, `"chi_square"`) |
| `score` | float |
| `created_at` | float |

**Hierarchy node** (`op_add_hierarchy`):

| Field | Value |
|-------|-------|
| `type` | `"agg_hierarchy"` |
| `label` | string |
| `created_at` | float |

### 2.4 Kernel Methods

#### `agg.new`

Create an AggregationRoot linked to an existing survey. Becomes the session's
active aggregation.

**Params (`data`):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source_id` | string | Yes | Cortex key of the source corpus root atom |

**Response:**

```json
{"result": {"status": "created", "aggregation_id": "...", "source_id": "..."}}
```

---

#### `agg.open`

Mount an existing aggregation as the session's active aggregation.

**Params:** `agg_id` (required)

**Response:** `{"status": "opened", "aggregation_id": "...", "source_id": "..."}`

**Errors:** `-32002` if atom is not an aggregation root; `-32602` if `agg_id` missing.

---

#### `agg.ls`

List all aggregation roots accessible to the current user, newest first.

**Params:** *(none)*

**Response:**

```json
{
  "result": {
    "aggregations": [
      {"aggregation_id": "...", "source_id": "...", "created_at": 0.0}
    ],
    "count": 1
  }
}
```

---

#### `agg.unit.add`

Index an existing survey response atom as an aggregation unit. Does not copy
the atom — only adds the key to `set:agg:{id}:units` and creates an `agg:unit` link.

**Params:** `unit_id` (required — Cortex key of any accessible Cortex atom)

**Response:** `{"status": "unit_added", "unit": "<unit_id>"}`

**Errors:** `-32002` if no active aggregation or if `unit_id` is not accessible.

---

#### `agg.group.add`

Create a labelled group and optionally assign initial member unit IDs.

**Params (`data`):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `label` | string | Yes | Group name |
| `members` | list[string] | No | Response atom keys to link as `agg:member` |

**Response:** `{"status": "group_added", "group_id": "..."}`

---

#### `agg.measure.add`

Attach a key/value statistic to a group atom.

**Params (`data`):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `group_id` | string | Yes | Cortex key of the target group |
| `key` | string | Yes | Statistic name (e.g. `"mean"`, `"count"`, `"pct"`) |
| `value` | any | Yes | Statistic value |

**Response:** `{"status": "measure_added", "measure_id": "..."}`

---

#### `agg.analysis.add`

Record a directed relation between two groups with a numeric score. Creates an
analysis atom and links it with `agg:analysis_out` (from `src_group`) and
`agg:analysis_in` (from `dst_group`).

**Params (`data`):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `src_group` | string | Yes | Source group atom key |
| `dst_group` | string | Yes | Destination group atom key |
| `relation` | string | Yes | Relation type (e.g. `"correlation"`, `"chi_square"`) |
| `score` | float | Yes | Numeric result |

**Response:** `{"status": "analysis_added", "analysis_id": "..."}`

---

#### `agg.hier.add`

Create a hierarchy node that groups existing group atoms under a named parent.

**Params (`data`):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `label` | string | Yes | Hierarchy node name |
| `children` | list[string] | Yes | Group atom keys to attach as `agg:child` |

**Response:** `{"status": "hierarchy_added", "node_id": "..."}`

---

#### `agg.list`

Return the structural inventory of the active aggregation (lists of atom keys
by category).

**Params:** *(none)*

**Response:**

```json
{
  "result": {
    "aggregation_id": "...",
    "units":     ["..."],
    "groups":    ["..."],
    "measures":  ["..."],
    "analysis":  ["..."],
    "hierarchy": ["..."]
  }
}
```

---

#### `agg.rm`

Delete the active aggregation root and clear the session context. Does **not**
delete the survey or the response atoms indexed as units.

**Params:** *(none)*

**Response:** `{"status": "deleted", "aggregation_id": "..."}`

---

### 2.5 CLI Shorthand Reference

> CLI aliases for `agg.*` are **not yet registered** in `api/router.py`.
> The methods are fully callable via JSON-RPC directly. The table below shows
> the recommended alias names for a future `api/router.py` addition.

| Recommended alias | Method | Arguments |
|-------------------|--------|-----------|
| `agg.new <source_id>` | `agg.new` | `source_id` |
| `agg.open <agg_id>` | `agg.open` | `agg_id` |
| `agg.ls` | `agg.ls` | — |
| `agg.unit <unit_id>` | `agg.unit.add` | `unit_id` |
| `agg.grp <label> [members…]` | `agg.group.add` | `label` (absorbs remaining as member list) |
| `agg.mea <group_id> <key> <value>` | `agg.measure.add` | `group_id`, `key`, `value` |
| `agg.rel <src> <dst> <relation> <score>` | `agg.analysis.add` | `src_group`, `dst_group`, `relation`, `score` |
| `agg.hier <label> <child…>` | `agg.hier.add` | `label` (absorbs remaining as child list) |
| `agg.list` | `agg.list` | — |
| `agg.rm` | `agg.rm` | — |

### 2.6 Workflow Example

```python
# Assume a survey already exists with responses
survey_id   = "abc123..."
response_id = "def456..."   # from survey.ans

# Create an aggregation for the survey
agg = rpc("agg.new", {"source_id": survey_id}, token=token)
agg_id = agg["result"]["aggregation_id"]

# Index response atoms as units
rpc("agg.unit.add", {"unit_id": response_id}, token=token)

# Create two demographic groups
g1 = rpc("agg.group.add", {"label": "age_18_34", "members": [response_id]}, token=token)
g1_id = g1["result"]["group_id"]

g2 = rpc("agg.group.add", {"label": "age_35_plus"}, token=token)
g2_id = g2["result"]["group_id"]

# Attach statistics to each group
rpc("agg.measure.add", {"group_id": g1_id, "key": "mean_score", "value": 7.4}, token=token)
rpc("agg.measure.add", {"group_id": g1_id, "key": "count",      "value": 42},  token=token)

rpc("agg.measure.add", {"group_id": g2_id, "key": "mean_score", "value": 6.1}, token=token)
rpc("agg.measure.add", {"group_id": g2_id, "key": "count",      "value": 38},  token=token)

# Record an analysis relation between the two groups
rpc("agg.analysis.add", {
    "src_group": g1_id,
    "dst_group": g2_id,
    "relation":  "mean_diff",
    "score":     1.3,
}, token=token)

# Build a hierarchy above both groups
rpc("agg.hier.add", {"label": "all_respondents", "children": [g1_id, g2_id]}, token=token)

# Inspect the structure
inventory = rpc("agg.list", {}, token=token)
# → {"aggregation_id": ..., "units": [...], "groups": [...], "measures": [...], ...}

# Resume in another session
rpc("agg.open", {"agg_id": agg_id}, token=token)

# List all aggregations
all_aggs = rpc("agg.ls", {}, token=token)

# Delete (does not affect the parent survey or its responses)
rpc("agg.rm", {}, token=token)
```

### 2.7 Known Constraints

#### Concept-word alias sharing

`AggregationConcept` registers a single concept-word atom for the root type
(`"aggregation"`) via the global alias `concept:word:aggregation`. Sub-atom
types (`agg_group`, `agg_measure`, `agg_analysis`, `agg_hierarchy`) are **not**
registered as concept words — they live only in the agg-scope sets and are not
visible in the concept catalog.

The global alias namespace (`concept:word:{word}`) is shared across all concept
models in the system. The alias is created on the first write and re-used by
subsequent calls (`resolve_alias` → idempotent). If two concept models register
the same word (e.g. both claim `"aggregation"`), whichever is registered first
wins; the second call silently re-uses the existing atom, which carries the first
model's `concept_model` metadata field.

To avoid collisions, keep concept-word names specific to the model's domain.
The word `"aggregation"` is sufficiently specific; generic words like `"unit"` or
`"group"` should be avoided as standalone concept words in future models.

#### Units are references, not copies

`agg.unit.add` indexes an existing atom by adding its key to `set:agg:{id}:units`
and creating an `agg:unit` link. It does **not** copy the atom — the original
atom in its source concept model (Survey, FieldNote, or any other) is unchanged.
Deleting the aggregation root (`agg.rm`) does not delete any referenced atoms.

---

### 2.8 Broader Applications

The 5-layer model (Unit → Group → Measure → Analysis → Hierarchy) maps onto a
general pattern that recurs across many domains:

> *Select a corpus of atoms → partition them into named groups → attach statistics
> to each partition → record relations between partitions → organise the whole
> into a navigable structure.*

The model is not bound to Survey. Any accessible Cortex atom — survey response,
FieldNote observation, Note paragraph, raw memory atom — can serve as a unit.
The sections below outline concrete application patterns.

#### Cross-concept corpus analysis

Units can be drawn from multiple concept models in the same aggregation.
For example, combining FieldNote observations and Survey responses in a single
aggregation root allows a unified statistical view of both quantitative survey
data and qualitative field records collected during the same research period.

```python
# Mix FieldNote observations and Survey responses as units
rpc("agg.unit.add", {"unit_id": survey_response_id}, token=token)
rpc("agg.unit.add", {"unit_id": fieldnote_obs_id},   token=token)

# Partition by source concept model
rpc("agg.group.add", {"label": "survey_responses",   "members": [...]}, token=token)
rpc("agg.group.add", {"label": "field_observations", "members": [...]}, token=token)
```

#### Longitudinal / temporal analysis

Groups can represent time windows rather than demographic or thematic segments.
Units (atoms created across different sessions or dates) are partitioned by
`created_at` into weekly, monthly, or seasonal groups. Measures then record
activity counts or keyword frequencies per period. Analysis atoms record
growth rates or seasonal correlation scores between adjacent periods.

```python
rpc("agg.group.add", {"label": "2026-Q1", "members": q1_atom_ids}, token=token)
rpc("agg.group.add", {"label": "2026-Q2", "members": q2_atom_ids}, token=token)

rpc("agg.measure.add",  {"group_id": q1_id, "key": "count",      "value": 38}, token=token)
rpc("agg.measure.add",  {"group_id": q2_id, "key": "count",      "value": 55}, token=token)
rpc("agg.analysis.add", {
    "src_group": q1_id, "dst_group": q2_id,
    "relation": "growth_rate", "score": 0.447,
}, token=token)
```

#### Taxonomy and classification without statistical data

The Group and Hierarchy layers alone are sufficient to build a flat or
multi-level domain taxonomy. Units and Measures are optional; an aggregation
that contains only groups and hierarchy nodes acts as a pure classification
structure — an org chart, a genre taxonomy, a tag hierarchy — stored directly
in the graph without any statistical content.

```python
# Leaf groups (no members required)
g_mammal  = rpc("agg.group.add", {"label": "Mammalia"},  token=token)["result"]["group_id"]
g_reptile = rpc("agg.group.add", {"label": "Reptilia"},  token=token)["result"]["group_id"]
g_avian   = rpc("agg.group.add", {"label": "Aves"},      token=token)["result"]["group_id"]

# Root hierarchy node
rpc("agg.hier.add", {
    "label":    "Vertebrata",
    "children": [g_mammal, g_reptile, g_avian],
}, token=token)
```

#### Multi-level reporting (Hierarchy as a report schema)

When a survey or corpus produces many groups (e.g. one per question, one per
geographic unit), Hierarchy nodes act as the report schema: top-level nodes
correspond to report sections, intermediate nodes to subsections, and leaf
groups to individual statistical tables. The hierarchy graph can be traversed
at render time to produce a structured report without additional indexing.

#### Analysis as a labelled graph over groups

The Analysis layer is effectively a labelled, weighted directed graph where
nodes are Group atoms and edges carry a `relation` type and a numeric `score`.
This structure is suitable for storing pre-computed similarity matrices,
dependency graphs between thematic clusters, or any pairwise relation that
would otherwise require a separate adjacency table.

#### Design guidance for non-Survey applications

When using Aggregation outside the Survey context:

- **`source_id` in `agg.new`** is recorded in the root meta and used for the
  `sys:for_source` back-link, but it is just a documentation field. Pass the
  key of the primary source corpus root (a FieldNote ID, a Note ID, or a
  synthetic anchor atom) to preserve traceability, or pass a placeholder if
  the units come from multiple sources.
- **All 5 layers are optional.** An aggregation is valid with only a root and
  however many layers are relevant. A taxonomy needs only Groups + Hierarchy;
  a simple frequency table needs only Units + Groups + Measures.
- **Aggregation roots are cheap.** Creating one per analysis run or per
  reporting snapshot is the intended pattern — do not try to mutate a single
  root to represent multiple analytical states.

#### Qualitative counterpart: Synthesis (§3)

Aggregation answers *how many, how much, and which groups differ*. The
adjacent `SynthesisConcept` (§3) answers *what it means and what can be
claimed*. Both models draw on the same raw source atoms and produce
complementary outputs that Presentation (§4) can assemble into a single
coherent narrative. In practice the two analysis layers run in parallel:
Aggregation partitions and measures the corpus quantitatively while Synthesis
codes and interprets the same material qualitatively.

---

## 3. Synthesis

**Source:** `lib/akasha/concepts/synthesis.py`  
**Context key:** `active_synthesis_root`  
**Prefix:** `synth`  
**Index set:** `set:synth:index`

---

### 3.1 Design Rationale

`SynthesisConcept` models the qualitative reasoning process that sits between raw
source material and a finished argument. It provides structured containers for the
mental operations that researchers actually perform: labelling passages (Code),
grouping labels into themes (Theme), forming interpretive statements (Interpretation),
and finally asserting defensible claims (Claim).

The model is inspired by Grounded Theory and qualitative content analysis workflows,
but is deliberately abstract — it does not prescribe a specific methodology. The same
six-layer stack (Source → Code → Theme → Interpretation → Claim → Thread) can serve
inductive coding, thematic analysis, discourse analysis, or informal argument mapping.

A key design property is that **Sources are references, not copies**. A `synth.source.add`
call indexes any accessible Cortex atom in the synthesis without duplicating it, so the
original FieldNote observation, Survey response, or external document atom remains the
sole authoritative version. Synthesis only records the *meaning attributed to* that
source.

**Thread** is an optional layer that sequences any mix of atoms (codes, interpretations,
claims) into a named reasoning chain — useful for tracking how a line of argument
developed over time, or for ordering the narrative arc of a presentation.

Within the broader analysis pipeline, Synthesis occupies the **qualitative layer** —
the counterpart to Aggregation's (§2) quantitative role. Aggregation asks *how many,
how much, and which groups differ*; Synthesis asks *what does it mean, why does it
matter, and what can we claim*. Both models draw on the same raw source atoms, and
their outputs converge in Presentation (§4), where statistical measures and
evidence-backed arguments are assembled into a coherent narrative.

---

### 3.2 Cortex Topology

```
SynthesisRoot  (concept="synthesis", role="root")
│
├─[synth:source]──► Source atom   (original, uncopied — from any universe)
│                       │
│                       └─[synth:refers_to]──► source_ref (optional commentary wrapper)
│
├─[synth:code]──► Code            (label applied to source material)
│                   └─[synth:applies_to]──► Source atom
│
├─[synth:theme]──► Theme          (grouping of codes)
│                    └─[synth:contains]──► Code
│
├─[synth:interp]──► Interpretation
│                      ├─[synth:interprets]──► Theme
│                      └─[synth:supported_by]──► evidence atom
│
├─[synth:claim]──► Claim
│                    ├─[synth:argues]──► Interpretation
│                    └─[synth:evidence]──► evidence atom
│
└─[synth:thread]──► Thread
                      ├─[sys:top]──► first step atom
                      ├─[sys:bottom]──► last step atom
                      └─[synth:step]──► (any step atom, flat index)
```

Namespace:

| Set | Contents |
|-----|----------|
| `set:synth:{id}` | All atoms belonging to this synthesis |
| `set:synth:{id}:sources` | Source reference atoms |
| `set:synth:{id}:codes` | Code atoms |
| `set:synth:{id}:themes` | Theme atoms |
| `set:synth:{id}:interpretations` | Interpretation atoms |
| `set:synth:{id}:claims` | Claim atoms |
| `set:synth:{id}:threads` | Thread atoms |
| `set:concept:{id}` | Concept catalog entry |
| `set:synth:index` | Global index of all synthesis roots |

---

### 3.3 Atom Metadata Reference

#### SynthesisRoot

| Field | Type | Description |
|-------|------|-------------|
| `type` | `"concept"` | Standard concept root marker |
| `concept` | `"synthesis"` | Used by `op_open` for validation |
| `role` | `"root"` | Topology role tag |
| `title` | string | Human-readable synthesis title |
| `source_universes` | list[str] | Allowed `ref_universe` values; empty = unrestricted |
| `created_at` | float | Unix timestamp |

#### Code

| Field | Type | Description |
|-------|------|-------------|
| `type` | `"synth_code"` | |
| `label` | string | The code text |
| `confidence` | float? | Optional analyst confidence (0–1) |
| `created_at` | float | |

#### Theme

| Field | Type | Description |
|-------|------|-------------|
| `type` | `"synth_theme"` | |
| `title` | string | Theme label |
| `created_at` | float | |

#### Interpretation

| Field | Type | Description |
|-------|------|-------------|
| `type` | `"synth_interpretation"` | |
| `stance` | string | Epistemic stance (`"hypothesis"`, `"finding"`, `"assertion"`, …) |
| `confidence` | float? | Optional confidence |
| `created_at` | float | |

#### Claim

| Field | Type | Description |
|-------|------|-------------|
| `type` | `"synth_claim"` | |
| `status` | string | Lifecycle state (`"draft"`, `"reviewed"`, `"published"`) |
| `confidence` | float? | Optional confidence |
| `created_at` | float | |

#### Thread

| Field | Type | Description |
|-------|------|-------------|
| `type` | `"synth_thread"` | |
| `title` | string | Thread name |
| `created_at` | float | |

Thread steps are linked via `sys:top` / `sys:bottom` (head/tail pointers on the thread atom)
and `sys:next` / `sys:previous` (doubly-linked list between step atoms).

---

### 3.4 Kernel Methods

#### `synth.new`

Create a SynthesisRoot.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `title` | string | yes | Synthesis title |
| `source_universes` | list[str] | no | Whitelist of allowed `ref_universe` values; empty = unrestricted |

**Returns:**

```json
{
  "status": "created",
  "synthesis_id": "<synth_id>",
  "title": "<title>",
  "source_universes": []
}
```

---

#### `synth.open`

Mount an existing synthesis as the session's active synthesis.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `synth_id` | string | yes | Synthesis root atom key (also accepted as `synthesis_id`) |

**Returns:**

```json
{
  "status": "opened",
  "synthesis_id": "<synth_id>",
  "title": "<title>",
  "source_universes": []
}
```

---

#### `synth.ls`

List all synthesis roots accessible to this session.

**Parameters:** none

**Returns:**

```json
{
  "syntheses": [
    {
      "synthesis_id": "<id>",
      "title": "<title>",
      "source_universes": [],
      "created_at": 1700000000.0
    }
  ],
  "count": 1
}
```

---

#### `synth.source.add`

Index an existing Cortex atom as a source for this synthesis.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `ref_id` | string | yes | Key of the source atom to index |
| `ref_universe` | string | no | Namespace of the source atom (validated against `source_universes` if set) |
| `note` | string | no | Analyst commentary; creates a lightweight `synth_source_ref` wrapper atom |

The original atom is indexed directly — no copy is made.

**Returns:**

```json
{
  "status": "source_added",
  "source_id": "<ref_id>",
  "source_ref_id": "<wrapper_id or null>",
  "ref_universe": "<universe>"
}
```

---

#### `synth.code.add`

Create a qualitative code, optionally applied to a source atom.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `label` | string | yes | Code text |
| `source_id` | string | no | Source atom the code applies to |
| `confidence` | float | no | Analyst confidence (0–1) |

**Returns:**

```json
{ "status": "code_added", "code_id": "<id>", "label": "<label>", "source_id": "<id or null>" }
```

---

#### `synth.theme.add`

Create a theme grouping one or more codes.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `title` | string | yes | Theme label |
| `codes` | list[str] | no | Code atom keys to include |

**Returns:**

```json
{ "status": "theme_added", "theme_id": "<id>", "title": "<title>", "codes": [] }
```

---

#### `synth.interp.add`

Record an interpretation grounded in a theme and/or evidence atoms.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `text` | string | yes | Interpretation text |
| `theme_id` | string | no | Theme atom this interpretation is about |
| `support` | list[str] | no | Evidence atom keys |
| `stance` | string | no | Epistemic stance (default `"hypothesis"`) |
| `confidence` | float | no | Analyst confidence |

**Returns:**

```json
{
  "status": "interpretation_added",
  "interpretation_id": "<id>",
  "theme_id": "<id or null>",
  "support": []
}
```

---

#### `synth.claim.add`

Assert a claim backed by interpretations and/or direct evidence.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `text` | string | yes | Claim text |
| `interpretations` | list[str] | no | Interpretation atom keys |
| `evidence` | list[str] | no | Direct evidence atom keys |
| `status` | string | no | Lifecycle state (default `"draft"`) |
| `confidence` | float | no | Analyst confidence |

**Returns:**

```json
{
  "status": "claim_added",
  "claim_id": "<id>",
  "interpretations": [],
  "evidence": []
}
```

---

#### `synth.thread.new`

Create a named reasoning thread.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `title` | string | yes | Thread title |

**Returns:**

```json
{ "status": "thread_created", "thread_id": "<id>", "title": "<title>" }
```

---

#### `synth.thread.add`

Append an existing atom as the next step in a reasoning thread. Any atom
(code, interpretation, claim, source reference) can be a thread step.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `thread_id` | string | yes | Thread atom key |
| `node_id` | string | yes | Atom to append as next step |

**Returns:**

```json
{ "status": "thread_step_added", "thread_id": "<id>", "node_id": "<id>" }
```

---

#### `synth.map`

Return the full structural inventory of the active synthesis (all subset IDs).

**Parameters:** none

**Returns:**

```json
{
  "synthesis_id": "<id>",
  "sources":         ["<id>", ...],
  "codes":           ["<id>", ...],
  "themes":          ["<id>", ...],
  "interpretations": ["<id>", ...],
  "claims":          ["<id>", ...],
  "threads":         ["<id>", ...]
}
```

---

#### `synth.trace`

Walk the evidence chain backwards from a specific claim, returning all
linked interpretations, themes, codes, and source atoms.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `claim_id` | string | yes | Claim atom key to trace |

**Returns:**

```json
{
  "claim":           { "id": "<id>", "content": "...", "meta": {} },
  "interpretations": [ ... ],
  "themes":          [ ... ],
  "codes":           [ ... ],
  "sources":         [ ... ],
  "evidence":        [ ... ]
}
```

Each entry is a `{ id, content, meta }` summary. Duplicates are removed.

---

#### `synth.rm`

Delete the active synthesis root and clear session context. Sub-atoms remain
in the Cortex as orphaned atoms unless dropped separately.

**Parameters:** none

**Returns:**

```json
{ "status": "deleted", "synthesis_id": "<id>" }
```

---

### 3.5 CLI Shorthand Reference

| CLI Command | Kernel Method | Description |
|-------------|---------------|-------------|
| `synth.new <title>` | `synth.new` | Create a synthesis |
| `synth.open <synth_id>` | `synth.open` | Mount an existing synthesis |
| `synth.ls` | `synth.ls` | List all syntheses |
| `synth.source.add <ref_id> [ref_universe=<u>] [note=<text>]` | `synth.source.add` | Index a source atom |
| `synth.code.add <label> [source_id=<id>]` | `synth.code.add` | Add a code |
| `synth.theme.add <title> [codes=[<id>,...]]` | `synth.theme.add` | Add a theme |
| `synth.interp.add <text> [theme_id=<id>] [stance=<s>]` | `synth.interp.add` | Add an interpretation |
| `synth.claim.add <text> [interpretations=[<id>,...]]` | `synth.claim.add` | Add a claim |
| `synth.thread.new <title>` | `synth.thread.new` | Create a reasoning thread |
| `synth.thread.add <thread_id> <node_id>` | `synth.thread.add` | Append a step to a thread |
| `synth.map` | `synth.map` | Show full structural inventory |
| `synth.trace <claim_id>` | `synth.trace` | Trace evidence chain from a claim |
| `synth.rm` | `synth.rm` | Delete active synthesis |

---

### 3.6 Workflow Example

Below is a condensed qualitative analysis workflow covering sources through to a
traceable claim.

```json
// 1. Create a synthesis workspace
{ "method": "synth.new", "params": {
    "title": "Workplace Burnout Study",
    "source_universes": ["fieldnote", "survey"]
}}
// → { "synthesis_id": "<S>" }

// 2. Index source atoms (fieldnote observations, survey responses)
{ "method": "synth.source.add", "params": {
    "ref_id": "<fn_observation_id>",
    "ref_universe": "fieldnote",
    "note": "Participant described feeling 'invisible' to management"
}}
// → { "source_id": "<fn_observation_id>", "source_ref_id": "<SR1>" }

{ "method": "synth.source.add", "params": {
    "ref_id": "<sv_response_id>",
    "ref_universe": "survey"
}}
// → { "source_id": "<sv_response_id>", "source_ref_id": null }

// 3. Code the sources
{ "method": "synth.code.add", "params": {
    "label": "Lack of recognition", "source_id": "<fn_observation_id>"
}}
// → { "code_id": "<C1>" }

{ "method": "synth.code.add", "params": {
    "label": "Workload overload", "source_id": "<sv_response_id>", "confidence": 0.85
}}
// → { "code_id": "<C2>" }

// 4. Group codes into a theme
{ "method": "synth.theme.add", "params": {
    "title": "Systemic neglect", "codes": ["<C1>", "<C2>"]
}}
// → { "theme_id": "<T1>" }

// 5. Interpret the theme
{ "method": "synth.interp.add", "params": {
    "text": "Participants experience burnout as a product of organisational inattention, not individual failure",
    "theme_id": "<T1>",
    "stance": "finding",
    "confidence": 0.78
}}
// → { "interpretation_id": "<I1>" }

// 6. Assert a claim
{ "method": "synth.claim.add", "params": {
    "text": "Structural change, not individual resilience training, is the appropriate intervention",
    "interpretations": ["<I1>"],
    "status": "draft"
}}
// → { "claim_id": "<CL1>" }

// 7. Trace the evidence chain
{ "method": "synth.trace", "params": { "claim_id": "<CL1>" }}
// → full chain: claim → interpretation → theme → codes → source atoms

// 8. Build a reasoning thread
{ "method": "synth.thread.new", "params": { "title": "Main argument arc" }}
// → { "thread_id": "<TH1>" }

{ "method": "synth.thread.add", "params": { "thread_id": "<TH1>", "node_id": "<T1>" }}
{ "method": "synth.thread.add", "params": { "thread_id": "<TH1>", "node_id": "<I1>" }}
{ "method": "synth.thread.add", "params": { "thread_id": "<TH1>", "node_id": "<CL1>" }}
```

---

### 3.7 Cross-Concept Application Patterns

Synthesis sits between two other analytical models and one output model:

- **Upstream: FieldNote and Survey** (see `concept-extensions-fieldwork.md`) — supply raw observation and
  response atoms as source material.
- **Parallel: Aggregation (§2)** — the quantitative counterpart. Aggregation
  measures *how many* and *how much*; Synthesis interprets *what it means* and
  *what can be claimed*. Crucially, Aggregation measure atoms can themselves be
  indexed as Synthesis sources, making the two models composable rather than
  alternative.
- **Downstream: Presentation (§4)** — the output layer. Synthesis claims and
  threads map naturally to slide frames and narrative arcs.

---

#### Pattern A: FieldNote → Synthesis (qualitative grounded argument)

The canonical qualitative use case: field observations are coded, grouped into
themes, interpreted, and crystallised into defensible claims.

```
[FieldNote (see concept-extensions-fieldwork.md §1)]
    │
    ├─ Observations  ──synth.source.add──►  [Synthesis (§3)]
    └─ Span annotations                          │
                                                 ├─ Codes (labels on passages)
                                                 ├─ Themes (grouped codes)
                                                 ├─ Interpretations
                                                 └─ Claims  ──► Presentation (§4)
```

**Workflow:**

1. Record field observations with `fn.new` + `fn.add`.
2. Create a Synthesis with `synth.new`, setting `source_universes: ["fieldnote"]`.
3. Index significant observations via `synth.source.add`; add `note` commentary
   to explain why each was selected.
4. Apply codes iteratively with `synth.code.add source_id=<obs_id>`.
5. Group related codes into themes with `synth.theme.add codes=[...]`.
6. Write interpretations with `synth.interp.add theme_id=<t>`.
7. Assert claims with `synth.claim.add interpretations=[...]`.
8. Run `synth.trace <claim_id>` to verify the full evidence chain.

---

#### Pattern B: Aggregation (§2) → Synthesis (quantitative findings as interpretive sources)

Aggregation measure atoms are just Cortex atoms — they can be indexed as Synthesis
sources. This enables qualitative interpretation of statistical patterns, creating
a genuine mixed-methods analysis within a single Synthesis workspace.

```
[Survey (see concept-extensions-fieldwork.md §2)]  ──► [Aggregation (§2)]
    │                      │
    └─ Responses           ├─ Groups (demographic segments)
                           ├─ Measures (rates, means, counts)  ──synth.source.add──►
                           └─ Analysis (correlations)                               │
                                                                          [Synthesis (§3)]
[FieldNote (see concept-extensions-fieldwork.md §1)]  ──synth.source.add──────────────────────────────────►       │
    └─ Observations                                                            ├─ Codes on patterns
                                                                               │  ("unexpectedly low
                                                                               │   engagement rate")
                                                                               ├─ Themes bridging
                                                                               │  quant + qual
                                                                               └─ Claims grounded
                                                                                  in both
```

**Workflow:**

1. Run the Survey → Aggregation pipeline (§2.6) to produce groups and measures.
2. Create a Synthesis with `source_universes: ["agg", "fieldnote"]`.
3. Index key Aggregation measure atoms:
   `synth.source.add ref_id=<measure_id> ref_universe="agg" note="<why this number matters>"`.
4. Also index relevant FieldNote observations as sources.
5. Apply codes to both types of sources in the same coding frame.
6. Build themes that group quantitative patterns and qualitative evidence together.
7. Write interpretations and claims that explicitly cite both kinds of evidence:
   `synth.claim.add evidence=[<measure_id>, <obs_id>]`.

This is the model's most distinctive capability: Aggregation answers the *what*
(a measure of 12% engagement), and Synthesis provides the *why* (the interpretive
argument about what that number means in context).

---

#### Pattern C: Synthesis → Presentation (§4) (argument elevation)

Synthesis Threads provide the narrative arc; finished claims become presentation
frames. The Thread's `sys:top → sys:next → sys:bottom` chain defines the slide
order.

```
[Synthesis (§3)]
    ├─ Thread "Main arc"
    │    ├─ sys:top ──► Theme atom
    │    ├─ sys:next──► Interpretation atom
    │    └─ sys:bottom──► Claim atom
    │
    └─ Claims  ─────────────────────────────────────────────────►  [Presentation (§4)]
                                                                          │
                                                                          ├─ Deck "Evidence"
                                                                          │    └─ Frames per theme
                                                                          └─ Deck "Conclusions"
                                                                               └─ Frames per claim
```

**Workflow:**

1. Create a Presentation with `context_universes: ["synth", "fieldnote", "agg"]`.
2. For each Synthesis Theme, add a Frame in the Evidence deck
   (`ref_universe="synth"`, `ref_id=<theme_id>`).
3. For each Synthesis Claim (status `"reviewed"` or `"published"`), add a Frame
   in the Conclusions deck (`ref_universe="synth"`, `ref_id=<claim_id>`).
4. Use `pres.node.add` with `role="highlight"` to surface the key source atoms
   (FieldNote observations, Aggregation measures) directly inside each frame.
5. Use `synth.trace` before finalising to verify that every claim frame has a
   complete, accessible evidence chain.

---

#### General Guidance

- **The synthesis workspace is a live reasoning environment; the presentation is
  the output.** Commit claims to Presentation only when they reach status
  `"reviewed"` or `"published"`.
- **`source_universes` enforces source discipline.** Setting it to `["fieldnote"]`
  or `["agg", "fieldnote"]` prevents accidental indexing of unrelated atoms.
- **Threads are optional but valuable.** They preserve how an argument developed
  over time — information that flat graph structures usually lose.
- **`synth.trace` is the audit tool.** Run it on every claim before publication
  to verify the full chain Source → Code → Theme → Interpretation → Claim.
- **Aggregation and Synthesis are complementary, not alternative.** Use both when
  your research combines quantitative measurement with qualitative interpretation.

---

## 4. Curation

**Source:** `lib/akasha/concepts/curation.py`  
**Context key:** `active_curation_root`  
**CLI prefix:** `cur.*`  
**Index set:** `set:curation:index`

---

### 4.1 Design Rationale

`CurationConcept` is a **premise-bound reconciliation engine**. It is not a truth engine.

The central design principle: **inputs remain intact**. When conflicting evidence atoms exist — two facts asserting different controlling powers over a territory, multiple country claims assigning different sovereignty, assessments built on incompatible sources — Curation does not delete or overwrite any of them. Instead, it creates a **View** under a stated **Premise** and folds conflicts only inside that View.

**Unresolved conflicts are first-class outputs**, not failures. A View containing unresolved folds is a valid, auditable output that carries more epistemic honesty than a silently overwritten record.

**When to use Curation:**
- Reconciling conflicting Facts, Claims, Correspondences, or Country records
- Building premise-conditioned summaries ("as of 1940", "from a de facto perspective")
- Making the history of editorial decisions auditable and reversible
- Passing structured, scoped Conclusions to Synthesis (§3) or Intelligence (§5)

**What Curation does not do:**
- Does not modify or delete source atoms
- Does not declare global truth across the knowledge base
- Does not enforce a single world-view

### 4.2 Cortex Topology

```
CurationRoot  (concept="curation", role="root")
  │
  ├─ curation:has_premise     ──▶  PremiseAtom     {label, as_of, perspective, conflict_policy, policy_steps}
  ├─ curation:has_input       ──▶  InputAtom        {ref_id, input_role, confidence, premise_id}
  ├─ curation:has_view        ──▶  ViewAtom         {premise_id, input_ids, status, derived_from_view_id, created_under}
  ├─ curation:has_fold        ──▶  FoldAtom         {view_id, resolution_scope, competing_input_ids, winner_id, unresolved}
  ├─ curation:has_conclusion  ──▶  ConclusionAtom   {view_id, statement, subject, predicate, object, confidence}
  └─ curation:has_dispute     ──▶  DisputeAtom      {target_id, reason, severity}

InputAtom      ──curation:refers_to──────────▶  (any external atom: Fact, Country, Correspondence …)
InputAtom      ──curation:under_premise──────▶  PremiseAtom
ViewAtom       ──curation:uses_premise───────▶  PremiseAtom
ViewAtom       ──curation:uses_input─────────▶  InputAtom            (multiple)
ViewAtom       ──curation:derived_from_view──▶  ViewAtom             (historiography chain)
FoldAtom       ──curation:in_view───────────▶  ViewAtom
FoldAtom       ──curation:compares──────────▶  InputAtom            (multiple)
FoldAtom       ──curation:selects───────────▶  InputAtom            (winner)
FoldAtom       ──curation:drops─────────────▶  InputAtom            (multiple, suppressed under this premise)
ConclusionAtom ──curation:concluded_in──────▶  ViewAtom
ConclusionAtom ──curation:supported_by──────▶  InputAtom            (multiple)
(target)       ──curation:disputed_by───────▶  DisputeAtom
DisputeAtom    ──curation:evidenced_by──────▶  SourceAtom
```

**Set layout:**

| Set | Contents |
|-----|----------|
| `set:curation:index` | All CurationRoot atoms (global) |
| `set:curation:{id}` | All atoms in this workspace |
| `set:curation:{id}:premises` | Premise atoms |
| `set:curation:{id}:inputs` | Input pointer atoms |
| `set:curation:{id}:views` | View atoms |
| `set:curation:{id}:folds` | Fold audit atoms |
| `set:curation:{id}:conclusions` | Conclusion atoms |
| `set:curation:{id}:disputes` | Dispute atoms |

### 4.3 Atom Metadata Reference

**PremiseAtom** (`type: curation_premise`)

| Field | Type | Description |
|-------|------|-------------|
| `label` | str | Human-readable name for this premise |
| `as_of` | str | Temporal scope, e.g. `"1940-06-01"` |
| `perspective` | str | Epistemic stance, e.g. `"de_facto"`, `"de_jure"` |
| `source_policy` | str | Which inputs to consider (`"all_accessible"`, etc.) |
| `conflict_policy` | str | How conflicts are folded (see §4.6) |
| `policy_steps` | list | Composable pipeline steps for `"composite"` policy |
| `mode` | str | `"normal"` (default) |
| `scope` | dict | Optional spatial or domain scope |

**InputAtom** (`type: curation_input`)

| Field | Type | Description |
|-------|------|-------------|
| `ref_id` | str | ID of the referenced external atom |
| `input_role` | str | `fact`, `correspondence`, `country_event`, `country_claim`, `sovereignty`, `administration`, `law`, `source`, `assessment`, `other` |
| `source_model` | str | Concept model of the referenced atom |
| `premise_id` | str \| null | If set, this input is scoped to a specific Premise |
| `weight` | float | Relative weight within conflict resolution (default 1.0) |
| `confidence` | float [0–1] | Inherited from referenced atom or set explicitly |
| `status` | str | `"candidate"` (default) |

**ViewAtom** (`type: curation_view`)

| Field | Type | Description |
|-------|------|-------------|
| `label` | str | Descriptive name for this view |
| `premise_id` | str | The Premise under which this View was built |
| `input_ids` | list[str] | All InputAtoms considered in this View |
| `status` | str | `draft`, `active`, `superseded`, `disputed`, `archived` |
| `derived_from_view_id` | str \| null | Parent View for historiography chains |
| `created_under` | dict | Snapshot of `as_of`, `perspective`, `conflict_policy`, `policy_steps`, `mode` |

**FoldAtom** (`type: curation_fold`)

| Field | Type | Description |
|-------|------|-------------|
| `view_id` | str | The View this fold belongs to |
| `resolution_scope` | dict | The specific conflict being resolved (entity, relation, time, perspective) |
| `competing_input_ids` | list[str] | All inputs that were in conflict |
| `winner_id` | str \| null | The input selected as the fold result |
| `dropped_ids` | list[str] | Inputs suppressed under this premise |
| `unresolved` | bool | True if the conflict was not resolved |
| `rationale` | dict | Structured explanation of the fold decision |

**ConclusionAtom** (`type: curation_conclusion`)

| Field | Type | Description |
|-------|------|-------------|
| `view_id` | str | The View this conclusion lives in |
| `conclusion_type` | str | `state`, `event`, `relation`, `assessment`, `estimate`, `recommendation_basis`, `unresolved`, `other` |
| `statement` | str | Natural-language conclusion |
| `subject` / `predicate` / `object` | str | Optional S/P/O triple for downstream processing |
| `scope` | dict | Temporal or spatial scope of the conclusion |
| `supported_by` | list[str] | Input atoms that support this conclusion |
| `confidence` | float [0–1] | Analyst confidence in the conclusion |
| `status` | str | `"provisional"` (default) |

### 4.4 Kernel Methods

| Method | IAM | Description |
|--------|-----|-------------|
| `curation.new` | write | Create a new Curation workspace |
| `curation.open` | read | Activate an existing workspace |
| `curation.ls` | read | List all Curation workspaces |
| `curation.map` | read | Return the structure map |
| `curation.rm` | drop | Soft-delete (preserves atoms for audit) |
| `curation.premise.add` | write | Add a Premise |
| `curation.input.add` | write | Register an evidence-bearing atom as input |
| `curation.view.run` | write | Create a View under a Premise |
| `curation.fold.add` | write | Record a conflict fold (winner, dropped, or unresolved) |
| `curation.conclusion.add` | write | Add a structured conclusion inside a View |
| `curation.dispute.add` | write | Flag a dispute against a View, Fold, or Conclusion |
| `curation.trace` | read | Trace a View / Fold / Conclusion to its inputs |
| `curation.diagnose` | read | Surface unresolved folds, low-confidence conclusions, coverage gaps |

**`curation.premise.add` key parameters:**

| Parameter | Required | Description |
|-----------|----------|-------------|
| `label` | ✓ | Human-readable premise name |
| `as_of` | — | Temporal cut-off date or period |
| `perspective` | — | `de_facto`, `de_jure`, `claimed`, etc. |
| `conflict_policy` | — | How to fold conflicts (see §4.6) |
| `policy_steps` | — | Step list for `"composite"` policy |

**`curation.input.add` key parameters:**

| Parameter | Required | Description |
|-----------|----------|-------------|
| `ref_id` | ✓ | Atom ID of the evidence source |
| `role` | — | One of the `INPUT_ROLES` values |
| `premise_id` | — | Scope this input to a specific Premise |
| `confidence` | — | Override; defaults to source atom's credibility |

**`curation.fold.add` key parameters:**

| Parameter | Required | Description |
|-----------|----------|-------------|
| `view_id` | ✓ | View this fold belongs to |
| `resolution_scope` | ✓ | Dict describing the conflict (entity, relation, time, perspective) |
| `competing_input_ids` | ✓ | List of conflicting input atom IDs |
| `winner_id` | — | Selected input; omit for `unresolved` folds |
| `dropped_ids` | — | Inputs suppressed under this premise |
| `unresolved` | — | Set `true` when conflict cannot be decided |
| `rationale` | — | Structured explanation dict |

### 4.5 CLI Shorthand Reference

| Alias | Method | Key args |
|-------|--------|----------|
| `cur.new` | `curation.new` | `title` |
| `cur.open` | `curation.open` | `curation_id` |
| `cur.ls` | `curation.ls` | — |
| `cur.map` | `curation.map` | — |
| `cur.rm` | `curation.rm` | — |
| `cur.premise` | `curation.premise.add` | `label`, `as_of`, `perspective`, `conflict_policy` |
| `cur.input` | `curation.input.add` | `ref_id`, `role`, `premise_id`, `confidence` |
| `cur.view` | `curation.view.run` | `premise_id`, `label`, `input_ids` |
| `cur.fold` | `curation.fold.add` | `view_id`, `resolution_scope`, `competing_input_ids` |
| `cur.conclude` | `curation.conclusion.add` | `view_id`, `statement`, `conclusion_type` |
| `cur.dispute` | `curation.dispute.add` | `target_id`, `reason`, `severity` |
| `cur.trace` | `curation.trace` | `target_id` |
| `cur.diagnose` | `curation.diagnose` | — |

### 4.6 Conflict Policies

The `conflict_policy` field on a Premise determines how competing inputs are folded inside a View.

| Policy | Behaviour |
|--------|-----------|
| `highest_credibility` | The input with the highest effective credibility score wins |
| `most_recent` | The most recently dated input wins |
| `perspective_preferred` | The input whose perspective matches the Premise perspective wins |
| `source_policy` | Folding follows the source's own declared policy |
| `leave_unresolved` | Conflict is recorded as-is; a `FoldAtom` with `unresolved: true` is created |
| `manual` | The analyst explicitly sets `winner_id` when calling `curation.fold.add` |
| `composite` | Policy is executed as an ordered `policy_steps` pipeline |

**`composite` policy steps** allow fine-grained control:

```json
[
  {"op": "filter",   "field": "confidence", "gte": 0.5},
  {"op": "prefer",   "field": "perspective", "value": "de_facto"},
  {"op": "prefer",   "field": "time",        "order": "newest"},
  {"op": "fallback", "action": "leave_unresolved"}
]
```

Steps are evaluated in order; the first step that produces a single winner terminates the pipeline.

### 4.7 Workflow Example

Territory sovereignty — building two premise-conditioned views from conflicting country records.

```python
# 1. Create a Curation workspace
cur.new title="Alsace-Lorraine sovereignty 1871–1945"

# 2. Register inputs (pointing to existing Country / Fact atoms — not copied)
cur.input ref_id=<fr_sovereignty_id>   role=sovereignty   note="French de jure sovereignty pre-1871"
cur.input ref_id=<de_sovereignty_id>   role=sovereignty   note="German de facto control 1871–1918"
cur.input ref_id=<versailles_fact_id>  role=fact          note="Treaty of Versailles 1919 return clause"
cur.input ref_id=<fr_claim_1939_id>    role=country_claim note="French de jure claim 1939"
cur.input ref_id=<de_admin_1940_id>    role=administration note="German administration re-established 1940"

# 3. Add premises
cur.premise label="de_jure_1939"  as_of="1939-09-01" perspective="de_jure"  conflict_policy="perspective_preferred"
cur.premise label="de_facto_1942" as_of="1942-01-01" perspective="de_facto" conflict_policy="most_recent"

# 4. Run a View under each Premise — inputs are automatically gathered
cur.view premise_id=<de_jure_id>   label="Alsace: de jure 1939"
cur.view premise_id=<de_facto_id>  label="Alsace: de facto 1942"

# 5. Record folds for the de facto 1942 view
cur.fold view_id=<de_facto_view_id> \
  resolution_scope='{"entity":"alsace","relation":"controlled_by","time":"1942","perspective":"de_facto"}' \
  competing_input_ids=[<fr_claim_1939_id>,<de_admin_1940_id>] \
  winner_id=<de_admin_1940_id> \
  rationale='{"policy":"most_recent","note":"German administration atom is more recent"}'

# 6. Add conclusions
cur.conclude view_id=<de_facto_view_id> \
  statement="As of 1942, Alsace was under German de facto administration." \
  conclusion_type=state subject="Alsace" predicate="controlled_by" obj="Germany" \
  confidence=0.85

cur.conclude view_id=<de_jure_view_id> \
  statement="Under international law as of 1939, France retained de jure sovereignty over Alsace." \
  conclusion_type=state subject="Alsace" predicate="sovereign_of" obj="France" \
  confidence=0.90

# 7. Diagnose the workspace
cur.diagnose
# → counts all atoms, flags any unresolved_folds, low-confidence conclusions

# 8. Trace a fold for audit
cur.trace target_id=<fold_id>
# → competing inputs, winner, dropped, rationale
```

### 4.8 Cross-Concept Integration

Curation is the **connective tissue** between raw evidence collection and downstream reasoning:

```
[Fact §1]          ──cur.input role=fact──────────────────▶
[Country]          ──cur.input role=sovereignty/claim──────▶
[Correspondence]   ──cur.input role=correspondence─────────▶  [Curation §4]
[Human]            ──cur.input role=assessment──────────────▶      │
                                                                    ├─ View (de_jure)
                                                                    │    └─ Conclusion ──synth.source.add──▶ [Synthesis §3]
                                                                    │
                                                                    ├─ View (de_facto)
                                                                    │    └─ Conclusion ──intel.assess.add──▶ [Intelligence §5]
                                                                    │
                                                                    └─ Unresolved Fold ──pres.node.add────▶ [Presentation §6]
```

- **Fact → Curation**: Curation references Fact atoms as inputs via `ref_id` without copying them.
- **Country / Correspondence → Curation**: sovereignty, claim, admin, and law atoms all fit the `INPUT_ROLES` vocabulary.
- **Curation → Synthesis (§3)**: Conclusion atoms are registered as Synthesis sources via `synth.source.add ref_universe="curation"`. The evidence chain is preserved: Synthesis Codes cite the Conclusion, which traces back through the Fold to the original inputs.
- **Curation → Intelligence (§5)**: Assessment atoms cite Curation View IDs in their `basis` list, making the assessment auditable to the original inputs and the premise under which they were reconciled.
- **Curation → Presentation (§6)**: Both resolved Conclusions and unresolved Folds can be surfaced as Presentation Nodes. This lets audiences see where the analysis is solid and where open questions remain.

---

## 5. Intelligence

**Source:** `lib/akasha/concepts/intelligence.py`  
**Context key:** `active_intelligence_root`  
**CLI prefix:** `intel.*`  
**Index set:** `set:intelligence:index`

---

### 5.1 Design Rationale

`IntelligenceConcept` is a **decision-cycle orchestration layer**. It does not replace Fact, Curation, Synthesis, or Presentation — it coordinates them.

The cycle follows a requirement-centric pipeline:

```
Requirement → Scan → Gap → Tasking → Assessment → Estimate → Option → Recommendation → Decision
```

**Core design principles:**

- **Requirement-centric**: every work product carries a `requirement_id`, enabling `intelligence.cycle` to reconstruct the complete picture for any question
- **Auditable decision trail**: Recommendation and Decision are separate, event-sourced atoms — what analysts recommended and what decision-makers did are never conflated
- **Tasking is instructional, not operational**: `intel.task` creates an instruction atom; it does not directly write to Survey, Fact, or FieldNote
- **Knowledge gaps are first-class outputs**: Gap atoms are as analytically significant as positive findings — they drive Taskings and bound the credibility of Assessments
- **Intelligence is not a truth engine**: conclusions are always conditional on the quality and completeness of the underlying Fact, Curation, and Synthesis work

### 5.2 Cortex Topology

```
IntelligenceRoot  (concept="intelligence", role="root")
  │
  ├─ intel:has_requirement   ──▶  RequirementAtom   {question, requirement_type, priority, status}
  ├─ intel:has_scan          ──▶  ScanAtom           {requirement_id, target_id, scan_type, signal, confidence}
  ├─ intel:has_gap           ──▶  GapAtom            {requirement_id, description, gap_type, severity, status}
  ├─ intel:has_tasking       ──▶  TaskingAtom        {requirement_id, gap_id, tasking_type, priority, status}
  ├─ intel:has_assessment    ──▶  AssessmentAtom     {requirement_id, assessment_type, judgment, basis, confidence}
  ├─ intel:has_estimate      ──▶  EstimateAtom       {requirement_id, estimate_type, statement, probability, range}
  ├─ intel:has_option        ──▶  OptionAtom         {requirement_id, title, option_type, benefits, risks, feasibility}
  ├─ intel:has_recommendation──▶  RecommendationAtom {requirement_id, statement, recommended_option_id, status, decision_status}
  ├─ intel:has_decision      ──▶  DecisionAtom       {recommendation_id, decision_status, decided_by, decided_at}
  └─ intel:has_dispute       ──▶  DisputeAtom        {target_id, reason, severity}

(work products) ──intel:answers_requirement──▶  RequirementAtom
RequirementAtom ──intel:has_work_product────▶  (all work products, bidirectional)

ScanAtom          ──intel:scans──────────▶  (any external Cortex atom)
TaskingAtom       ──intel:addresses_gap──▶  GapAtom
AssessmentAtom    ──intel:based_on───────▶  (Curation Conclusion, Fact, Synthesis Claim, Scan)
EstimateAtom      ──intel:based_on───────▶  (same)
OptionAtom        ──intel:based_on───────▶  (Assessment, Estimate atoms)
RecommendationAtom──intel:recommends_option─▶  OptionAtom
RecommendationAtom──intel:grounded_in────▶  (Assessment, Estimate atoms)
RecommendationAtom──intel:decided_by─────▶  DecisionAtom
DecisionAtom      ──intel:answers_requirement──▶  RequirementAtom
(target)          ──intel:disputed_by────▶  DisputeAtom
```

**Set layout:**

| Set | Contents |
|-----|----------|
| `set:intelligence:index` | All IntelligenceRoot atoms (global) |
| `set:intelligence:{id}` | All atoms in this workspace |
| `set:intelligence:{id}:requirements` | Requirement atoms |
| `set:intelligence:{id}:scans` | Scan atoms |
| `set:intelligence:{id}:gaps` | Gap atoms |
| `set:intelligence:{id}:taskings` | Tasking atoms |
| `set:intelligence:{id}:assessments` | Assessment atoms |
| `set:intelligence:{id}:estimates` | Estimate atoms |
| `set:intelligence:{id}:options` | Option atoms |
| `set:intelligence:{id}:recommendations` | Recommendation atoms |
| `set:intelligence:{id}:decisions` | Decision atoms |
| `set:intelligence:{id}:disputes` | Dispute atoms |

### 5.3 Atom Metadata Reference

**RequirementAtom** (`type: intel_requirement`)

| Field | Type | Description |
|-------|------|-------------|
| `question` | str | The intelligence question being answered |
| `requirement_type` | str | `research`, `policy`, `fieldwork`, `osint`, `historical`, `strategic`, `operational`, `creative`, `other` |
| `priority` | str | `low`, `medium`, `high`, `critical` |
| `owner` | str | Responsible analyst or team |
| `due` | str | Deadline or time-horizon |
| `scope` | dict | Optional spatial, temporal, or domain scope |
| `success_criteria` | list[str] | What "done" looks like for this requirement |
| `status` | str | `"open"` (default) |

**ScanAtom** (`type: intel_scan`)

| Field | Type | Description |
|-------|------|-------------|
| `requirement_id` | str | Owning Requirement |
| `target_id` | str | The Cortex atom being scanned |
| `scan_type` | str | `fact`, `curation_view`, `synthesis`, `aggregation`, `country`, `geo`, `map`, `human`, `source`, `other` |
| `signal` | str | What the scan found (raw observation) |
| `summary` | str | Analyst summary of the signal |
| `confidence` | float [0–1] | Confidence in the signal |
| `source_model` | str | Concept model of the target atom |

**GapAtom** (`type: intel_gap`)

| Field | Type | Description |
|-------|------|-------------|
| `requirement_id` | str | Owning Requirement |
| `description` | str | What knowledge is missing |
| `gap_type` | str | `missing_source`, `low_confidence`, `contradiction`, `outdated`, `unresolved`, `insufficient_coverage`, `missing_fieldwork`, `missing_analysis`, `other` |
| `related_ids` | list[str] | Atoms that are insufficient or conflicting |
| `severity` | str | `low`, `medium`, `high`, `critical` |
| `status` | str | `"open"` (default) |

**TaskingAtom** (`type: intel_tasking`)

| Field | Type | Description |
|-------|------|-------------|
| `requirement_id` | str | Owning Requirement |
| `gap_id` | str \| null | The Gap this tasking addresses |
| `description` | str | Instruction text |
| `tasking_type` | str | `collect`, `verify`, `interview`, `survey`, `field_observe`, `analyze`, `curate`, `synthesize`, `present`, `other` |
| `target_model` | str | Suggested destination concept (e.g. `"fact"`, `"survey"`) |
| `target_hint` | str | Suggested target detail |
| `priority` | str | `low`, `medium`, `high`, `critical` |
| `assigned_to` | str | Person or team |
| `status` | str | `"open"` (default) |

**AssessmentAtom** (`type: intel_assessment`)

| Field | Type | Description |
|-------|------|-------------|
| `requirement_id` | str | Owning Requirement |
| `assessment_type` | str | `situation`, `risk`, `opportunity`, `capability`, `intent`, `reliability`, `control`, `trend`, `other` |
| `judgment` | str | The analyst's evaluative statement |
| `basis` | list[str] | Curation Conclusions, Fact atoms, Synthesis Claims that ground this judgment |
| `confidence` | float [0–1] | Confidence in the judgment |
| `method` | str | `"human"` (default), `"llm_assisted"`, etc. |
| `caveats` | list[str] | Limitations or conditions on the judgment |

**RecommendationAtom** (`type: intel_recommendation`)

| Field | Type | Description |
|-------|------|-------------|
| `requirement_id` | str | Owning Requirement |
| `statement` | str | The recommendation text |
| `recommended_option_id` | str \| null | The preferred Option |
| `basis` | list[str] | Assessment / Estimate atoms grounding the recommendation |
| `confidence` | float [0–1] | Analyst confidence |
| `status` | str | `draft`, `reviewed`, `issued` |
| `decision_status` | str | `accepted`, `rejected`, `deferred`, `superseded`, `unknown` |
| `rationale` | str | Narrative explanation |
| `caveats` | list[str] | Conditions or limitations |

**DecisionAtom** (`type: intel_decision`)

| Field | Type | Description |
|-------|------|-------------|
| `recommendation_id` | str | The Recommendation being decided upon |
| `decision_status` | str | `accepted`, `rejected`, `deferred`, `superseded`, `unknown` |
| `decided_by` | str | Decision-maker identity |
| `decided_at` | str | Timestamp or date |
| `reason` | str | Rationale for the decision |

### 5.4 Kernel Methods

| Method | IAM | Description |
|--------|-----|-------------|
| `intelligence.new` | write | Create a new Intelligence workspace |
| `intelligence.open` | read | Activate an existing workspace |
| `intelligence.ls` | read | List all Intelligence workspaces |
| `intelligence.map` | read | Return the structure map |
| `intelligence.rm` | drop | Soft-delete (preserves atoms for audit) |
| `intelligence.req.add` | write | Add a Requirement (the central question) |
| `intelligence.scan.add` | write | Record a signal from an existing atom |
| `intelligence.gap.add` | write | Record a knowledge gap |
| `intelligence.task.add` | write | Issue a Tasking instruction |
| `intelligence.assess.add` | write | Add an Assessment (judgment) |
| `intelligence.estimate.add` | write | Add an Estimate (probability, scenario, range) |
| `intelligence.option.add` | write | Add a decision Option |
| `intelligence.recommend.add` | write | Issue a Recommendation |
| `intelligence.decision.add` | write | Record a Decision against a Recommendation |
| `intelligence.dispute.add` | write | Flag a dispute against any Intelligence atom |
| `intelligence.cycle` | read | Return full cycle view for a Requirement |
| `intelligence.trace` | read | Trace an atom to its requirement and basis chain |
| `intelligence.diagnose` | read | Surface open gaps, orphaned work products, undecided recommendations |

**`intelligence.req.add` key parameters:**

| Parameter | Required | Description |
|-----------|----------|-------------|
| `question` | ✓ | The intelligence question |
| `requirement_type` | — | Category (`research`, `policy`, `fieldwork`, etc.) |
| `priority` | — | `low` / `medium` / `high` / `critical` |
| `success_criteria` | — | List of strings defining completion |

**`intelligence.assess.add` key parameters:**

| Parameter | Required | Description |
|-----------|----------|-------------|
| `requirement_id` | ✓ | The Requirement being answered |
| `assessment_type` | ✓ | One of the `ASSESSMENT_TYPES` values |
| `judgment` | ✓ | The evaluative statement |
| `basis` | — | List of Curation Conclusion / Fact / Synthesis Claim IDs |
| `confidence` | — | [0–1], default 0.5 |
| `caveats` | — | List of limitation strings |

### 5.5 CLI Shorthand Reference

| Alias | Method | Key args |
|-------|--------|----------|
| `intel.new` | `intelligence.new` | `title` |
| `intel.open` | `intelligence.open` | `intelligence_id` |
| `intel.ls` | `intelligence.ls` | — |
| `intel.map` | `intelligence.map` | — |
| `intel.rm` | `intelligence.rm` | — |
| `intel.req` | `intelligence.req.add` | `question`, `requirement_type`, `priority` |
| `intel.scan` | `intelligence.scan.add` | `requirement_id`, `target_id`, `scan_type` |
| `intel.gap` | `intelligence.gap.add` | `requirement_id`, `description`, `gap_type` |
| `intel.task` | `intelligence.task.add` | `requirement_id`, `description`, `tasking_type`, `gap_id` |
| `intel.assess` | `intelligence.assess.add` | `requirement_id`, `assessment_type`, `judgment`, `basis` |
| `intel.estimate` | `intelligence.estimate.add` | `requirement_id`, `estimate_type`, `statement` |
| `intel.option` | `intelligence.option.add` | `requirement_id`, `title`, `option_type` |
| `intel.recommend` | `intelligence.recommend.add` | `requirement_id`, `statement`, `recommended_option_id` |
| `intel.decision` | `intelligence.decision.add` | `recommendation_id`, `decision_status`, `decided_by` |
| `intel.dispute` | `intelligence.dispute.add` | `target_id`, `reason`, `severity` |
| `intel.cycle` | `intelligence.cycle` | `requirement_id` |
| `intel.trace` | `intelligence.trace` | `target_id` |
| `intel.diagnose` | `intelligence.diagnose` | — |

### 5.6 Workflow Example

A strategic intelligence cycle for a research organisation evaluating a territorial dispute.

```python
# 1. Create workspace
intel.new title="Kaliningrad status assessment 2024"

# 2. Define the central requirement
intel.req question="What is the current de facto vs de jure status of Kaliningrad,
            and what are the primary vectors of strategic risk?"  \
  requirement_type=strategic priority=high \
  success_criteria=["de_facto_control_confirmed","de_jure_status_mapped","risk_vectors_ranked"]

# 3. Scan existing evidence (pointing to Fact / Curation / Country atoms)
intel.scan requirement_id=<req_id> target_id=<ru_sovereignty_fact_id> \
  scan_type=fact signal="Russian sovereignty atom confirmed 1991 Königsberg Treaty"

intel.scan requirement_id=<req_id> target_id=<kaliningrad_curation_view_id> \
  scan_type=curation_view signal="De facto / de jure gap identified in 1939–1945 period"

# 4. Record gaps
intel.gap requirement_id=<req_id> \
  description="No post-2022 sovereignty evaluation on record" \
  gap_type=outdated severity=high

intel.gap requirement_id=<req_id> \
  description="Lithuanian transit restriction impact not quantified" \
  gap_type=missing_analysis severity=medium

# 5. Issue taskings to fill gaps
intel.task requirement_id=<req_id> gap_id=<outdated_gap_id> \
  description="Update sovereignty and control atoms from 2022–2024 sources" \
  tasking_type=collect target_model=fact priority=high

intel.task requirement_id=<req_id> gap_id=<transit_gap_id> \
  description="Run Aggregation on Lithuanian transit data 2022–2024" \
  tasking_type=analyze target_model=aggregation priority=medium

# --- (after taskings are fulfilled externally) ---

# 6. Assess
intel.assess requirement_id=<req_id> assessment_type=situation \
  judgment="Russia retains uncontested de facto control; de jure status is internationally recognised." \
  basis=[<updated_sovereignty_id>,<kaliningrad_cur_conclusion_id>] \
  confidence=0.85

intel.assess requirement_id=<req_id> assessment_type=risk \
  judgment="Transit restriction creates logistical vulnerability under Article 5 scenarios." \
  basis=[<agg_transit_measure_id>,<nato_law_fact_id>] \
  confidence=0.70 \
  caveats=["Assessment based on open-source only","Escalation dynamics not modelled"]

# 7. Estimate
intel.estimate requirement_id=<req_id> estimate_type=probability \
  statement="Probability of military contingency within 24 months: 15–25%" \
  basis=[<risk_assessment_id>] \
  probability=0.20 range_low=0.15 range_high=0.25 \
  horizon="2026-06" confidence=0.55

# 8. Define options
intel.option requirement_id=<req_id> title="Expand field monitoring" \
  option_type=field_action \
  benefits=["Closes transit gap","Improves estimate confidence"] \
  risks=["Resource intensive"] \
  feasibility=0.7 expected_value=0.8

intel.option requirement_id=<req_id> title="Issue interim assessment with caveats" \
  option_type=presentation_action \
  benefits=["Timely","Transparent about uncertainty"] \
  risks=["May be cited without caveats"] \
  feasibility=0.95 expected_value=0.65

# 9. Recommend
intel.recommend requirement_id=<req_id> \
  statement="Issue interim assessment with explicit uncertainty bounds.
             Commission field monitoring to close transit gap within 90 days." \
  recommended_option_id=<interim_option_id> \
  basis=[<situation_assessment_id>,<risk_assessment_id>,<probability_estimate_id>] \
  confidence=0.75 status=reviewed

# 10. Record the decision
intel.decision recommendation_id=<rec_id> decision_status=accepted \
  decided_by="Research Director" decided_at="2024-06-15" \
  reason="Interim assessment approved; field monitoring commissioned."

# 11. View the full cycle
intel.cycle requirement_id=<req_id>
# → requirement, scans, gaps, taskings, assessments, estimates, options, recommendations, decisions

# 12. Diagnose
intel.diagnose
# → open_gaps, open_taskings, low_confidence_assessments,
#   recommendations_without_decision, requirements_without_assessment
```

### 5.7 Cross-Concept Integration

Intelligence is the **final reasoning layer** before Presentation. It draws on every upstream concept model:

```
[Fact §1]              ──intel.scan────────────────────────────────────────────▶
[Aggregation §2]       ──intel.scan  scan_type=aggregation──────────────────────▶
[Synthesis §3]         ──intel.scan  scan_type=synthesis───────────────────────▶  [Intelligence §5]
[Curation §4]          ──intel.assess.add basis=[<view_id>]─────────────────────▶      │
[Country / Human / Geo]──intel.scan  scan_type=country/human/geo─────────────────▶      │
                                                                                         │
                                  ┌──────────────────────────────────────────────────────┘
                                  │
                                  ├─ Recommendations ──pres.frame.add ref_universe=intelligence──▶ [Presentation §6]
                                  ├─ Assessments     ──pres.node.add───────────────────────────▶
                                  └─ Open Gaps       ──pres.node.add role=caveat────────────────▶
```

- **Fact → Intelligence**: Scan atoms point directly to Fact atoms. Assessments cite high-credibility Fact atoms in their `basis`.
- **Curation → Intelligence (primary link)**: The `basis` field of `AssessmentAtom` should normally contain Curation Conclusion atom IDs. This ensures the assessment is traceable through the fold record back to the raw inputs.
- **Synthesis → Intelligence**: Synthesis Claims and Interpretations can appear in `basis`, linking the interpretive argument to the assessment judgment.
- **Aggregation → Intelligence**: Scan + Assessment can reference Aggregation Measure atoms directly, grounding quantitative signals in the intelligence judgment.
- **Intelligence → Presentation (§6)**: Issued Recommendations and their supporting Assessment / Estimate atoms are surfaced via `pres.frame.add`. Open Gaps can be added as caveat nodes to show the audience where uncertainty remains.
- **Cycle view as narrative**: `intel.cycle requirement_id=<id>` returns the full Requirement-to-Decision chain, providing the narrative backbone for a Presentation deck.

---

## 6. Presentation

**Source:** `lib/akasha/concepts/presentation.py`  
**Context key:** `active_presentation_root`  
**Prefix:** `pres`  
**Index set:** `set:pres:index`

---

### 6.1 Design Rationale

`PresentationConcept` models the abstract structure of a presentation — a slide
deck, a research talk, a poster, or any hierarchical content assembly — without
coupling to a specific rendering format or authoring tool.

The central insight is that the *content* of a presentation always lives
elsewhere in the Cortex (as FieldNote observations, Survey responses, Aggregation
measures, Note atoms, etc.) and the presentation model only describes *how those
atoms are arranged*. A **Node** in the presentation is a reference pointer that
says "take this atom from universe X and show it here." This keeps the source of
truth in the originating concept model and lets the same content appear in
multiple presentations without duplication.

The four-layer stack (Deck → Frame → Region → Node) maps cleanly onto typical
slide software metaphors, but the model is agnostic: a "Frame" could equally
represent a poster panel, a report section, or a dashboard tile.

In a research pipeline, Presentation is the **convergence point** where the two
analysis layers meet. Aggregation (§2) supplies the quantitative results —
measures, group comparisons, and statistical correlations. Synthesis (§3) supplies
the qualitative argument — themes, interpretations, and evidence-backed claims.
A frame can reference an Aggregation measure and a Synthesis claim with equal
facility through the same `ref_universe` / `ref_id` pointer mechanism, making it
straightforward to build slides that show both the number and the meaning on the
same canvas.

---

### 6.2 Cortex Topology

```
PresentationRoot   (concept="presentation", role="root")
│
├─[pres:deck]──► Deck        — ordered section grouping frames
│                  │
│                  └─[pres:frame]──► Frame   — individual slide / page
│                                       │
│                                       ├─[pres:region]──► Region  — layout zone
│                                       │                      │
│                                       │                      └─[pres:node]──► Node
│                                       │
│                                       └─[pres:node]──► Node   (frame-level nodes)
│
└─[pres:frame]──► Frame  (frames may also attach directly to the root)
```

Namespace:

| Set | Contents |
|-----|----------|
| `set:pres:{id}` | All atoms belonging to this presentation |
| `set:pres:{id}:decks` | Deck atoms |
| `set:pres:{id}:frames` | Frame atoms |
| `set:pres:{id}:regions` | Region atoms |
| `set:pres:{id}:nodes` | Node atoms |
| `set:concept:{id}` | Concept catalog entry (concept-word registration) |
| `set:pres:index` | Global index of all presentation roots |

---

### 6.3 Atom Metadata Reference

#### PresentationRoot

| Field | Type | Description |
|-------|------|-------------|
| `type` | `"concept"` | Standard concept root marker |
| `concept` | `"presentation"` | Used by `op_open` for validation |
| `role` | `"root"` | Topology role tag |
| `title` | string | Human-readable presentation title |
| `context_universes` | list[str] | Allowed `ref_universe` values for frames/nodes; empty = unrestricted |
| `created_at` | float | Unix timestamp |

#### Deck

| Field | Type | Description |
|-------|------|-------------|
| `type` | `"pres_deck"` | |
| `title` | string | Section title |
| `order` | float | Sort key within the presentation |
| `created_at` | float | |

#### Frame

| Field | Type | Description |
|-------|------|-------------|
| `type` | `"pres_frame"` | |
| `title` | string | Slide/page title |
| `order` | float | Sort key within its parent |
| `ref_universe` | string? | Optional source namespace for the primary reference |
| `ref_id` | string? | Optional atom key in `ref_universe` |
| `created_at` | float | |

#### Region

| Field | Type | Description |
|-------|------|-------------|
| `type` | `"pres_region"` | |
| `label` | string | Layout zone label (e.g. `"title"`, `"body"`, `"footnote"`) |
| `order` | float | Sort key within its frame |
| `created_at` | float | |

#### Node

| Field | Type | Description |
|-------|------|-------------|
| `type` | `"pres_node"` | |
| `ref_universe` | string | Source namespace (e.g. `"fieldnote"`, `"survey"`, `"agg"`) |
| `ref_id` | string | Atom key to display |
| `role` | string | Content role (`"item"`, `"title"`, `"caption"`, `"highlight"`, …) |
| `style` | string? | Optional renderer hint |
| `created_at` | float | |

---

### 6.4 Kernel Methods

#### `pres.new`

Create a new PresentationRoot.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `title` | string | yes | Presentation title |
| `context_universes` | list[str] | no | Whitelist of allowed `ref_universe` values; empty = unrestricted |

**Returns:**

```json
{
  "status": "created",
  "presentation_id": "<pres_id>",
  "title": "<title>",
  "context_universes": []
}
```

Sets `active_presentation_root` in session context.

---

#### `pres.open`

Mount an existing presentation as the active presentation.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `pres_id` | string | yes | Presentation root atom key (also accepted as `presentation_id`) |

**Returns:**

```json
{
  "status": "opened",
  "presentation_id": "<pres_id>",
  "title": "<title>",
  "context_universes": []
}
```

---

#### `pres.ls`

List all presentation roots accessible to this session.

**Parameters:** none

**Returns:**

```json
{
  "presentations": [
    {
      "presentation_id": "<id>",
      "title": "<title>",
      "context_universes": [],
      "created_at": 1700000000.0
    }
  ],
  "count": 1
}
```

---

#### `pres.deck.add`

Add an ordered deck (section) to the active presentation.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `title` | string | yes | Deck title |
| `order` | float | no | Sort key (default `0.0`) |

**Returns:**

```json
{ "status": "deck_added", "deck_id": "<deck_id>" }
```

---

#### `pres.frame.add`

Add a frame (slide or page) to a deck, or directly to the presentation root.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `title` | string | yes | Frame title |
| `deck_id` | string | no | Parent deck; if omitted, frame attaches to root |
| `order` | float | no | Sort key (default `0.0`) |
| `ref_universe` | string | no | Namespace of the primary atom reference |
| `ref_id` | string | no | Atom key in `ref_universe` |

If `context_universes` is set on the root and `ref_universe` is provided, the
value must appear in the whitelist or the call raises an error.

**Returns:**

```json
{ "status": "frame_added", "frame_id": "<frame_id>" }
```

---

#### `pres.region.add`

Add a layout region within a frame.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `frame_id` | string | yes | Parent frame atom key |
| `label` | string | yes | Region label (`"title"`, `"body"`, `"footer"`, etc.) |
| `order` | float | no | Sort key within the frame (default `0.0`) |

**Returns:**

```json
{ "status": "region_added", "region_id": "<region_id>" }
```

---

#### `pres.node.add`

Attach a content reference node to a region or frame.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `parent_id` | string | yes | Region or frame atom key |
| `ref_universe` | string | yes | Source namespace (e.g. `"fieldnote"`, `"agg"`, `"survey"`) |
| `ref_id` | string | yes | Atom key to display |
| `role` | string | no | Content role (default `"item"`) |
| `style` | string | no | Renderer hint (default `null`) |

**Returns:**

```json
{ "status": "node_added", "node_id": "<node_id>" }
```

---

#### `pres.list`

Return the structural inventory of the active presentation.

**Parameters:** none

**Returns:**

```json
{
  "presentation_id": "<id>",
  "decks":   ["<deck_id>", ...],
  "frames":  ["<frame_id>", ...],
  "regions": ["<region_id>", ...],
  "nodes":   ["<node_id>", ...]
}
```

---

#### `pres.rm`

Delete the active presentation root and clear session context. Sub-atoms
(decks, frames, regions, nodes) remain in the Cortex as orphaned atoms unless
dropped separately.

**Parameters:** none

**Returns:**

```json
{ "status": "deleted", "presentation_id": "<id>" }
```

---

### 6.5 CLI Shorthand Reference

| CLI Command | Kernel Method | Description |
|-------------|---------------|-------------|
| `pres.new <title>` | `pres.new` | Create a presentation |
| `pres.open <pres_id>` | `pres.open` | Mount an existing presentation |
| `pres.ls` | `pres.ls` | List all presentations |
| `pres.deck.add <title>` | `pres.deck.add` | Add a deck |
| `pres.frame.add <title> [deck_id=<id>]` | `pres.frame.add` | Add a frame |
| `pres.region.add <frame_id> <label>` | `pres.region.add` | Add a layout region |
| `pres.node.add <parent_id> <ref_universe> <ref_id>` | `pres.node.add` | Add a content node |
| `pres.list` | `pres.list` | Show structural inventory |
| `pres.rm` | `pres.rm` | Delete active presentation |

---

### 6.6 Workflow Example

Below is a minimal workflow that creates a two-deck presentation with one frame
each and a few nodes pointing to atoms from other concept models.

```json
// 1. Create a presentation
{ "method": "pres.new", "params": {
    "title": "Q3 Research Summary",
    "context_universes": ["fieldnote", "agg", "survey"]
}}
// → { "status": "created", "presentation_id": "<P>" }

// 2. Add two decks
{ "method": "pres.deck.add", "params": { "title": "Introduction",  "order": 1.0 }}
// → { "deck_id": "<D1>" }
{ "method": "pres.deck.add", "params": { "title": "Results",       "order": 2.0 }}
// → { "deck_id": "<D2>" }

// 3. Add frames
{ "method": "pres.frame.add", "params": {
    "title": "Study Background", "deck_id": "<D1>", "order": 1.0
}}
// → { "frame_id": "<F1>" }

{ "method": "pres.frame.add", "params": {
    "title": "Key Findings", "deck_id": "<D2>", "order": 1.0,
    "ref_universe": "agg", "ref_id": "<agg_measure_id>"
}}
// → { "frame_id": "<F2>" }

// 4. Add a body region to F1
{ "method": "pres.region.add", "params": {
    "frame_id": "<F1>", "label": "body", "order": 1.0
}}
// → { "region_id": "<R1>" }

// 5. Attach content nodes
{ "method": "pres.node.add", "params": {
    "parent_id": "<R1>",
    "ref_universe": "fieldnote",
    "ref_id": "<fn_observation_id>",
    "role": "item"
}}
{ "method": "pres.node.add", "params": {
    "parent_id": "<F2>",
    "ref_universe": "agg",
    "ref_id": "<agg_measure_id>",
    "role": "highlight"
}}

// 6. Inspect the structure
{ "method": "pres.list" }
// → { "presentation_id": "<P>", "decks": [...], "frames": [...], ... }
```

---

### 6.7 Cross-Concept Application Patterns

Presentation is the **output layer** of the analysis pipeline. It does not
perform analysis itself — it assembles the results of upstream models into a
structured, communicable form. The three patterns below reflect the three main
upstream configurations, from simplest to most complete.

---

#### Pattern A: Aggregation (§2) → Presentation (quantitative results deck)

The pure quantitative path: statistical analysis of survey data is assembled
into a results presentation. No qualitative interpretation is required.

```
[Survey (see concept-extensions-fieldwork.md §2)]  ──► [Aggregation (§2)]  ──pres.new()──►  [Presentation (§4)]
    │                      │                                      │
    ├─ Questions            ├─ Units (responses)                  ├─ Deck "Methodology"
    ├─ Options              ├─ Groups (demographics)              ├─ Deck "Results"
    └─ Responses            ├─ Measures (rates, means)            │    └─ Frames per measure
                            └─ Analysis (correlations)            └─ Deck "Conclusions"
```

**Workflow:**

1. Build and run the Survey → Aggregation pipeline (§2.6).
2. Call `pres.new` with `context_universes: ["agg", "survey"]`.
3. Create decks for Methodology, Results, and Conclusions.
4. For each key Aggregation measure, call `pres.frame.add` with
   `ref_universe="agg"` and `ref_id=<measure_id>`.
5. Add `pres.node.add` nodes pointing at the survey question atoms
   (`ref_universe="survey"`) for the Methods section.

Presentation only holds the *arrangement*. Re-running the Aggregation and
updating a measure atom automatically refreshes any presentation that
references it.

---

#### Pattern B: Synthesis (§3) → Presentation (qualitative argument deck)

The pure qualitative path: coded observations and interpreted themes are
assembled into a research argument presentation.

```
[FieldNote (see concept-extensions-fieldwork.md §1)]  ──► [Synthesis (§3)]  ──pres.new()──►  [Presentation (§4)]
    │                        │                                    │
    └─ Observations          ├─ Codes                             ├─ Deck "Evidence"
                             ├─ Themes                            │    └─ Frames per theme
                             ├─ Interpretations                   └─ Deck "Argument"
                             └─ Claims                                 └─ Frames per claim
```

**Workflow:**

1. Run the FieldNote → Synthesis pipeline (§3.7 Pattern A).
2. Call `pres.new` with `context_universes: ["synth", "fieldnote"]`.
3. Create an Evidence deck with one frame per Synthesis Theme
   (`ref_universe="synth"`, `ref_id=<theme_id>`).
4. Create an Argument deck with one frame per Synthesis Claim that has
   reached status `"reviewed"` or `"published"`.
5. Use `pres.node.add role="highlight"` inside evidence frames to surface
   the key FieldNote observation atoms directly on the slide.
6. Run `synth.trace` on each claim before finalising to confirm the
   evidence chain is complete.

---

#### Pattern C: Aggregation (§2) + Synthesis (§3) → Presentation (complete pipeline)

The most powerful combination: quantitative measures and qualitative claims
converge in a single presentation. This pattern produces research output where
each significant number is paired with an interpreted argument, and each
argument is grounded in traceable evidence.

```
[Survey (see concept-extensions-fieldwork.md §2)]  ──► [Aggregation (§2)]  ──synth.source.add──► [Synthesis (§3)]
    │                      │                                        │
    │                      └─ Measures ──────────────────────────►  ├─ Codes + Themes
    │                                                                └─ Claims
[FieldNote (see concept-extensions-fieldwork.md §1)]  ──synth.source.add──────────────────────────────────► ↑
    └─ Observations

         [Aggregation (§2)]  ─── pres.frame.add(ref_universe="agg") ──►┐
                                                                         ├──► [Presentation (§4)]
         [Synthesis (§3)]   ─── pres.frame.add(ref_universe="synth") ──►┘
```

**Workflow:**

1. Run Survey → Aggregation (§2.6) to produce groups, measures, and analysis.
2. Run FieldNote → Synthesis (§3.7 Pattern A or B) to produce codes, themes,
   and claims — including Aggregation measure atoms as Synthesis sources where
   useful.
3. Call `pres.new` with `context_universes: ["agg", "synth", "survey", "fieldnote"]`.
4. Create decks by narrative function:
   - **"Background"**: frames pointing at FieldNote observations and Survey
     design atoms.
   - **"Findings"**: alternating frames — one Aggregation measure, then one
     Synthesis theme that interprets it.
   - **"Conclusions"**: frames pointing at Synthesis claims
     (`ref_universe="synth"`, `ref_id=<claim_id>`).
5. Use `pres.region.add` to create `"stat"` and `"interpretation"` zones
   within each Findings frame, placing an Aggregation node and a Synthesis
   node side by side.
6. Verify every Conclusions frame with `synth.trace` before finalising.

This pattern delivers the full research lifecycle in a single presentation:
raw evidence → statistical pattern → interpretive claim → argued conclusion.

---

#### General Guidance

- **`context_universes` is a soft contract.** Set it to the namespaces you
  actually intend to reference (e.g. `["agg", "synth"]`) to prevent
  accidental cross-contamination from other concept models.
- **Frames can reference root atoms.** Passing a Synthesis root or Aggregation
  root as `ref_id` lets a renderer expand the whole analysis on one slide —
  useful for summary or abstract slides.
- **Nodes are cheap; reuse freely.** The same atom — an Aggregation measure,
  a Synthesis claim, a FieldNote observation — can appear in multiple frames
  across multiple presentations with no duplication in the Cortex.
- **Presentations are disposable output.** Deleting a presentation with
  `pres.rm` removes only the arrangement structure. All upstream analysis
  atoms (Aggregation, Synthesis, FieldNote) remain intact.
- **Rebuild freely.** Because Presentation is pure arrangement, it is safe and
  cheap to discard a draft presentation and rebuild it once the upstream
  analysis has been revised.

---

---
