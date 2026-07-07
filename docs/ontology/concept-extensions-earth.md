# Akasha Earth — Geoscientific & Social-Scientific Knowledge Extensions

**Version:** 1.3.0
**Supersedes:** `concept-extensions-geo.md` v1.2.0
**Status:** Active

---

## Preamble

The Earth can be approached from two distinct scientific traditions — and a complete knowledge system requires both.

**Geoscientific** — the physical world: terrain, coordinates, place, cartographic depiction, spatial measurement, coordinate systems, and material geography as it exists independent of human interpretation. A river is a feature with elevation, flow direction, and width. A coastline is a geometry. A city is a point with latitude and longitude.

**Social-scientific** — the human world layered on top of the physical: populations, polities, borders, laws, economies, cultural identities, sovereignty claims, and the individual actors who inhabit, contest, and reshape the land. The same river becomes a border, a trade route, a sacred site, and a zone of contested jurisdiction. The same coastline becomes an exclusive economic zone, a landing site, a contested fishing ground.

Both traditions are required for a complete picture, and neither is neutral. A map does not merely depict geography — it makes political claims, encodes imperial ambitions, and erases certain communities while privileging others. A border is not merely a line on a map — it is a legal instrument, a historical scar, and an ongoing negotiation between states, peoples, and realities.

**Akasha Earth** brings these two traditions together under a single semantic framework:

| Concept | Domain | Core question |
|:--------|:-------|:--------------|
| **GeoConcept** | Physical geography | Where does this place exist, and how has it changed? |
| **MapConcept** | Cartographic depiction | How was this place drawn, labeled, and interpreted? |
| **CorrespondenceConcept** | Cross-system alignment | What is the evidence that these two representations refer to the same thing? |
| **HumanConcept** | Individual actors | Who is this person, what do we know about them, and from what sources? |
| **CountryConcept** | Polities & sovereignty | What is this state, what does it claim, and how has it governed? |

All five models are designed to interoperate through the graph. A MapConcept grounding connects a cartographic feature to a GeoConcept place. A CountryConcept territory links to a GeoConcept region. A HumanConcept record links to a CountryConcept as a bond target. CorrespondenceConcept provides the cross-system alignment layer for all of them.

---

## Shared Design Layer: VisibilityMixin

**File:** `lib/akasha/concepts/mixins/visibility.py`

Several Earth-family concept models share the same visibility semantics: hidden
places, revealed entities, archived records, and soft-deleted or tombstoned
atoms. Rather than each model re-implementing its own rules, Akasha Earth uses
a shared `VisibilityMixin` that sits above IAM access control and adds a
consistent semantic layer.

| State | Meaning |
|:------|:--------|
| **hidden** | The atom exists but should not appear in ordinary traversal |
| **revealed** | A hidden atom has become visible through an event or evidence |
| **archived** | The atom is retained but is no longer current |
| **tombstoned** | The atom is treated as removed from normal semantic views |

Visibility is determined by both metadata flags **and** transition links.
A place may retain `hidden=true` forever in its immutable atom metadata, but
become visible the moment it receives a `sys:revealed_by` outgoing link — for
example, when a `geo.reveal` transition is recorded.

```
TargetAtom ──sys:revealed_by───▶ RevealTransition
TargetAtom ──sys:hidden_by─────▶ HideTransition
TargetAtom ──sys:archived_by───▶ ArchiveTransition
TargetAtom ──sys:tombstoned_by─▶ TombstoneTransition
```

This keeps the original atom immutable while allowing the world-view to evolve
over time — consistent with Akasha's event-sourced design throughout.

The mixin exposes:

- `_base_access_visible(atom_id)` — pure IAM check (`cortex.check_access`)
- `_is_hidden / _is_revealed / _is_archived / _is_tombstoned(atom_id)` — each
  checks both the atom's metadata flag **and** the corresponding `sys:*` link
- `_visible_semantic(atom_id, include_hidden, include_archived, include_tombstoned)` — the full composite check
- `_visibility_state(atom_id)` — returns a full audit dict for introspection

**Current adoption:** GeoConcept inherits `VisibilityMixin` and uses it for all
spatial visibility decisions, including BFS traversal in `geo.nearby` and
`geo.path`. The same layer is intended for MapConcept, HumanConcept,
CountryConcept, and EarthConcept so that semantic visibility remains consistent
across the whole Earth extension family.

---

## Table of Contents

- [Shared Design Layer: VisibilityMixin](#shared-design-layer-visibilitymixin)

> **Part I — Physical Geography**

- [1. GeoConcept](#1-geoconcept)
  - [1.1 Design Rationale](#11-design-rationale)
  - [1.2 Cortex Topology](#12-cortex-topology)
  - [1.3 Kernel Methods](#13-kernel-methods)
  - [1.4 CLI Shorthand Reference](#14-cli-shorthand-reference)
  - [1.5 Spatial Query Operations](#15-spatial-query-operations)
  - [1.6 Temporal Index](#16-temporal-index)
  - [1.7 Workflow Examples](#17-workflow-examples)
- [2. MapConcept](#2-mapconcept)
  - [2.1 Design Rationale](#21-design-rationale)
  - [2.2 Cortex Topology](#22-cortex-topology)
  - [2.3 Kernel Methods](#23-kernel-methods)
  - [2.4 CLI Shorthand Reference](#24-cli-shorthand-reference)
  - [2.5 Workflow Examples](#25-workflow-examples)

> **Part II — Cross-System Alignment**

- [3. CorrespondenceConcept](#3-correspondenceconcept)
  - [3.1 Design Rationale](#31-design-rationale)
  - [3.2 Cortex Topology](#32-cortex-topology)
  - [3.3 Kernel Methods](#33-kernel-methods)
  - [3.4 CLI Shorthand Reference](#34-cli-shorthand-reference)
  - [3.5 Confidence Model](#35-confidence-model)
  - [3.6 Workflow Examples](#36-workflow-examples)

> **Part III — Human Society**

- [4. HumanConcept](#4-humanconcept)
  - [4.1 Design Rationale](#41-design-rationale)
  - [4.2 Cortex Topology](#42-cortex-topology)
  - [4.3 Kernel Methods](#43-kernel-methods)
  - [4.4 CLI Shorthand Reference](#44-cli-shorthand-reference)
  - [4.5 Observable / FactConcept Integration](#45-observable--factconcept-integration)
  - [4.6 Workflow Example](#46-workflow-example)
- [5. CountryConcept](#5-countryconcept) *(documentation in progress)*
  - [5.1 Design Rationale](#51-design-rationale)
  - [5.2 Cortex Topology](#52-cortex-topology)
  - [5.3 Kernel Methods](#53-kernel-methods)
  - [5.4 CLI Shorthand Reference](#54-cli-shorthand-reference)
  - [5.5 Workflow Examples](#55-workflow-examples)

---

---

> **Part I — Physical Geography**
>
> *Geoscientific modeling: spatial reality, cartographic depiction, and the material world.*

---

## 1. GeoConcept

**File:** `lib/akasha/concepts/geo.py`
**Concept prefix:** `geo`
**Context key:** `active_geo_root`
**Index set:** `set:geo:index`

### 1.1 Design Rationale

GeoConcept models grounded spatial knowledge as an event-sourced graph. It is
designed for use cases where geography is contested, layered, or revealed
over time — historical research, ARG world-building, archaeological analysis,
and intelligence workflows.

**Core principles:**

- **Immutability first** — coordinates, places, and features are never modified
  in place. Changes are recorded as `transition` atoms appended to the graph.
- **Evidence attachment** — every spatial atom accepts a `source_id` link
  (`geo:evidenced_by`) connecting it to a FactConcept, FieldNote, or other
  source atom.
- **Multiple realities** — `geo.clone` creates alternate-representation places
  (disputed geography, historical layers, fictional projections) without
  overwriting the canonical version.
- **Hidden discovery** — places can be created with `hidden=true` and later
  revealed via `geo.reveal`, producing an auditable `transition` record. The
  original atom is never mutated; visibility is resolved through the shared
  `VisibilityMixin`, using both concept-specific links such as `geo:revealed_by`
  and common semantic links such as `sys:revealed_by`.
- **Coordinate-system agnosticism** — supports WGS84, UTM, local grid, pixel,
  relative, and symbolic systems in the same root.
- **Snapshot-anchored cloning** — `geo.clone snapshot_id=<id>` records which
  temporal snapshot a clone is based on, enabling "build a WorldModel from 1940
  terrain" workflows.
- **Soft delete** — `geo.rm` removes the root from the index only; all child
  atoms are retained in Cortex and remain accessible to users with direct atom
  IDs. No `drop_chunk` is called.

#### Pipeline overview

```
geo.new title="Battle of X" coordinate_system=wgs84
    │
    ├── geo.coord.add   → CoordinateAtom  ──geo:has_coordinate──▶ GeoRoot
    ├── geo.place.add   → PlaceAtom       ──geo:has_place──────▶ GeoRoot
    │       └── geo.feature.add → FeatureAtom ──geo:has_feature──▶ PlaceAtom
    ├── geo.observe.add → ObservationAtom ──geo:has_observation──▶ GeoRoot
    ├── geo.event.add   → EventAtom       ──geo:has_event──────▶ GeoRoot
    │       └── geo.place.state → PlaceStateAtom ──geo:has_state──▶ PlaceAtom
    ├── geo.connect     → ConnectionAtom  (topology edges between places)
    ├── geo.affine.add  → AffineAtom      (coordinate-system transform record)
    ├── geo.clone       → ClonePlaceAtom  ──geo:clone_of──▶ OriginalPlace
    ├── geo.transition.add → TransitionAtom ──geo:changed_by◀── TargetAtom
    ├── geo.reveal      → TransitionAtom (type=revealed)
    └── geo.diagnose    → diagnostic report (no write)
```

---

### 1.2 Cortex Topology

#### 1.2.1 Root atom

| Field              | Value                         |
|--------------------|-------------------------------|
| `type`             | `"concept"`                   |
| `concept`          | `"geo"`                       |
| `role`             | `"root"`                      |
| `title`            | User-supplied title           |
| `description`      | Optional description          |
| `coordinate_system`| One of `COORDINATE_SYSTEMS`   |

The root is added to `set:geo:index` (global) and `set:geo:{root_id}` (content).

#### 1.2.2 Subset sets

| Subset         | Set key                          | Relation from root       |
|----------------|----------------------------------|--------------------------|
| `coordinates`  | `set:geo:{id}:coordinates`       | `geo:has_coordinate`     |
| `places`       | `set:geo:{id}:places`            | `geo:has_place`          |
| `features`     | `set:geo:{id}:features`          | `geo:has_feature`        |
| `observations` | `set:geo:{id}:observations`      | `geo:has_observation`    |
| `events`       | `set:geo:{id}:events`            | `geo:has_event`          |
| `layers`       | `set:geo:{id}:layers`            | `geo:has_layer`          |
| `snapshots`    | `set:geo:{id}:snapshots`         | `geo:has_snapshot`       |
| `states`       | `set:geo:{id}:states`            | `geo:has_state`          |
| `connections`  | `set:geo:{id}:connections`       | `geo:has_connection`     |
| `affines`      | `set:geo:{id}:affines`           | `geo:has_affine`         |
| `clones`       | `set:geo:{id}:clones`            | `geo:has_clone`          |
| `transitions`  | `set:geo:{id}:transitions`       | `geo:has_transition`     |

#### 1.2.3 Key link patterns

```
# Place hierarchy
ParentPlace ──sys:contains──▶ ChildPlace
ChildPlace  ──sys:part_of───▶ ParentPlace

# Place ↔ Coordinate
Place ──geo:located_at──▶ Coordinate

# Feature attachment
Place ──geo:has_feature──▶ Feature

# Observation
Observation ──geo:observes──────▶ Target
Target      ──geo:observed_by──▶ Observation

# Event causality
Event ──geo:occurred_at──▶ Place
PlaceState ──geo:caused_by──▶ Event
Place ──geo:has_state──▶ PlaceState

# Connection topology
Place_A ──geo:{connection_type}──▶ Place_B   (direct edge)
ConnectionAtom ──geo:from──▶ Place_A
ConnectionAtom ──geo:to──▶ Place_B

# Clone
Original ──geo:cloned_as──▶ Clone
Clone    ──geo:clone_of───▶ Original

# Transition / reveal (concept-specific links)
Target ──geo:changed_by──▶ TransitionAtom
Target ──geo:revealed_by──▶ TransitionAtom  (type=revealed)
Target ──geo:hidden_by───▶ TransitionAtom   (type=hidden)
Target ──geo:moved_by────▶ TransitionAtom   (type=moved)

# Shared semantic visibility (VisibilityMixin)
Target ──sys:revealed_by───▶ TransitionAtom
Target ──sys:hidden_by─────▶ TransitionAtom
Target ──sys:archived_by───▶ TransitionAtom
Target ──sys:tombstoned_by─▶ TransitionAtom

# Evidence
Any atom ──geo:evidenced_by──▶ SourceAtom

# Temporal linked list (rooted at GeoRoot, managed by TemporalMixin)
GeoRoot ──sys:time_top────▶ OldestTemporalAtom
GeoRoot ──sys:time_bottom─▶ NewestTemporalAtom
TemporalAtom ──sys:time_next────▶ LaterAtom
TemporalAtom ──sys:time_previous─▶ EarlierAtom
```

Temporal types indexed: `geo_event`, `geo_transition`, `geo_place_state`,
`geo_observation`, `geo_snapshot`.

#### 1.2.4 Controlled vocabularies

**COORDINATE_SYSTEMS** — `wgs84`, `local_grid`, `utm`, `pixel`, `relative`,
`symbolic`, `other`

**PLACE_TYPES** — `site`, `region`, `building`, `room`, `road`, `boundary`,
`landmark`, `zone`, `world_place`, `other`

**FEATURE_TYPES** — `natural`, `built`, `archaeological`, `political`,
`ecological`, `infrastructure`, `symbolic`, `hidden`, `other`

**OBSERVATION_METHODS** — `human`, `sensor`, `survey`, `satellite`, `map`,
`fieldnote`, `llm`, `other`

**CONNECTION_TYPES** — `adjacent_to`, `contains`, `overlaps`, `near`, `route`,
`boundary`, `visible_from`, `accessible_from`, `symbolically_linked`, `other`

**TRANSITION_TYPES** — `created`, `destroyed`, `moved`, `renamed`, `merged`,
`split`, `revealed`, `hidden`, `state_changed`, `other`

---

### 1.3 Kernel Methods

#### `geo.new`
Create a new Geo root.

| Parameter           | Type   | Required | Default  |
|---------------------|--------|----------|----------|
| `title`             | str    | yes      | —        |
| `description`       | str    | no       | `""`     |
| `coordinate_system` | str    | no       | `wgs84`  |

Returns: `{ geo_id, concept_id, title, coordinate_system }`

#### `geo.open`
Open an existing Geo root and set it as the session focus.

| Parameter | Type | Required |
|-----------|------|----------|
| `geo_id`  | str  | yes      |

#### `geo.ls`
List all accessible Geo roots (sorted newest-first).

#### `geo.map`
Show structure of the active Geo root — all 12 subset member lists.

#### `geo.rm`
Soft-delete the active Geo root. Removes the root from `set:geo:index` only;
all child atoms are retained in Cortex and remain accessible to users who hold
direct atom IDs. No `drop_chunk` is called.

---

#### `geo.coord.add`
Add a coordinate atom.

| Parameter    | Type  | Default  | Notes                          |
|--------------|-------|----------|--------------------------------|
| `label`      | str   | `""`     | Human label for this point     |
| `system`     | str   | `wgs84`  | Coordinate system              |
| `lat`        | float | `null`   | Latitude (WGS84)               |
| `lon`        | float | `null`   | Longitude (WGS84)              |
| `alt`        | float | `null`   | Altitude (metres)              |
| `x/y/z`      | float | `null`   | Alternate axes                 |
| `precision`  | str   | `""`     | e.g. `"±10m"`                  |
| `source_id`  | str   | `""`     | Evidence atom                  |
| `confidence` | float | `0.8`    | Clamped to [0, 1]              |
| `note`       | str   | `""`     | Free-text content              |

Returns: `{ coordinate_id }`

---

#### `geo.place.add`
Add a named place.

| Parameter        | Type  | Default | Notes                       |
|------------------|-------|---------|-----------------------------|
| `name`           | str   | —       | Required                    |
| `place_type`     | str   | `site`  | From PLACE_TYPES            |
| `coordinate_id`  | str   | `""`    | Attach a coordinate atom    |
| `parent_place_id`| str   | `""`    | Creates containment links   |
| `description`    | str   | `""`    |                             |
| `source_id`      | str   | `""`    |                             |
| `confidence`     | float | `0.8`   |                             |
| `hidden`         | bool  | `false` | Hidden until revealed       |

Returns: `{ place_id, name }`

---

#### `geo.place.state`
Record a state change on a place (manual, event-sourced).

| Parameter     | Type  | Default | Notes                            |
|---------------|-------|---------|----------------------------------|
| `place_id`    | str   | —       | Required                         |
| `state`       | str   | —       | e.g. `"under_siege"`             |
| `event_id`    | str   | `""`    | Causal event atom                |
| `occurred_at` | str   | `""`    | ISO timestamp; used for temporal index |
| `intensity`   | float | `0.5`   |                                  |
| `note`        | str   | `""`    |                                  |

Returns: `{ state_id, place_id, state }`

---

#### `geo.feature.add`
Add a feature to a place.

| Parameter      | Type  | Default | Notes                |
|----------------|-------|---------|----------------------|
| `place_id`     | str   | —       | Required             |
| `name`         | str   | —       | Required             |
| `feature_type` | str   | `other` | From FEATURE_TYPES   |
| `description`  | str   | `""`    |                      |
| `source_id`    | str   | `""`    |                      |
| `confidence`   | float | `0.7`   |                      |
| `properties`   | dict  | `{}`    | Arbitrary key-values |

Returns: `{ feature_id, place_id }`

---

#### `geo.observe.add`
Record an observation of any spatial atom.

| Parameter     | Type  | Default  | Notes                          |
|---------------|-------|----------|--------------------------------|
| `target_id`   | str   | —        | Required — the observed atom   |
| `text`        | str   | —        | Required                       |
| `method`      | str   | `human`  | From OBSERVATION_METHODS       |
| `observer`    | str   | `""`     | Observer name/id               |
| `observed_at` | str   | `""`     | ISO timestamp or description   |
| `source_id`   | str   | `""`     |                                |
| `confidence`  | float | `0.7`    |                                |
| `data`        | dict  | `{}`     | Structured observation data    |

Returns: `{ observation_id }`

---

#### `geo.event.add`
Record a spatial event (battle, flood, discovery, etc.).

| Parameter    | Type       | Default  | Notes                        |
|--------------|------------|----------|------------------------------|
| `description`| str        | —        | Required                     |
| `place_id`   | str        | `""`     | Where it occurred            |
| `event_time` | str        | `""`     | ISO timestamp or description |
| `intensity`  | float      | `0.5`    |                              |
| `event_type` | str        | `event`  | Free-form type tag           |
| `source_id`  | str        | `""`     |                              |
| `affects`    | list[str]  | `[]`     | Atom IDs affected            |
| `confidence` | float      | `0.7`    |                              |

Returns: `{ event_id }`

---

#### `geo.layer.add`
Create a named layer grouping spatial atoms.

| Parameter     | Type      | Default | Notes              |
|---------------|-----------|---------|--------------------|
| `label`       | str       | —       | Required           |
| `layer_type`  | str       | `data`  | Free-form type tag |
| `members`     | list[str] | `[]`    | Member atom IDs    |
| `description` | str       | `""`    |                    |
| `source_id`   | str       | `""`    |                    |

Returns: `{ layer_id, label }`

---

#### `geo.snapshot.add`
Capture a named snapshot of the current spatial state.

| Parameter    | Type      | Default | Notes                      |
|--------------|-----------|---------|----------------------------|
| `label`      | str       | —       | Required                   |
| `captured_at`| str       | `""`    | Timestamp or description   |
| `members`    | list[str] | `[]`    | Atom IDs in the snapshot   |
| `note`       | str       | `""`    |                            |
| `source_id`  | str       | `""`    |                            |

Returns: `{ snapshot_id, label }`

---

#### `geo.connect`
Connect two spatial atoms with a typed relationship.

| Parameter         | Type      | Default       | Notes                          |
|-------------------|-----------|---------------|--------------------------------|
| `src_id`          | str       | —             | Required                       |
| `dst_id`          | str       | —             | Required                       |
| `connection_type` | str       | `adjacent_to` | From CONNECTION_TYPES          |
| `direction`       | str       | `directed`    | `directed` or `mutual`         |
| `distance`        | float     | `null`        | Optional distance value        |
| `weight`          | float     | `1.0`         | Graph traversal weight         |
| `evidence`        | list[str] | `[]`          | Evidence atom IDs              |
| `note`            | str       | `""`          |                                |

**`direction` semantics:**
- `directed` — one ConnectionAtom, one graph edge `src → dst`
- `mutual` — one ConnectionAtom (with `direction=mutual` recorded in meta), two
  graph edges: `src → dst` and `dst → src`. A single atom models the
  relationship; the bidirectional edges make both nodes reachable from either
  side in `geo.nearby` / `geo.path`.

Returns: `{ connection_id, src_id, dst_id, connection_type }`

---

#### `geo.affine.add`
Record an affine transform between two coordinate systems.

| Parameter       | Type             | Default | Notes                             |
|-----------------|------------------|---------|-----------------------------------|
| `label`         | str              | —       | Required                          |
| `source_system` | str              | —       | Required                          |
| `target_system` | str              | —       | Required                          |
| `matrix`        | list[list[float]]| —       | Required — transform matrix       |
| `offset`        | list[float]      | `[]`    | Translation offset                |
| `source_id`     | str              | `""`    |                                   |
| `confidence`    | float            | `0.8`   |                                   |
| `note`          | str              | `""`    |                                   |

This records the transform rule as an inspectable atom. It does not
automatically re-project existing coordinate atoms.

Returns: `{ affine_id, label, source_system, target_system }`

---

#### `geo.clone`
Clone a place as an alternate representation.

| Parameter             | Type | Default       | Notes                              |
|-----------------------|------|---------------|------------------------------------|
| `place_id`            | str  | —             | Required — the original            |
| `name`                | str  | `""`          | Name for the clone                 |
| `clone_type`          | str  | `alternate`   | e.g. `disputed`, `historical`, `fictional` |
| `reason`              | str  | `""`          |                                    |
| `source_id`           | str  | `""`          |                                    |
| `preserve_coordinates`| bool | `true`        | Copy coordinate link from original |
| `hidden`              | bool | `false`       |                                    |
| `snapshot_id`         | str  | `""`          | Snapshot this clone is based on    |

When `snapshot_id` is provided, the clone records a `geo:cloned_from_snapshot`
link to the snapshot atom. This enables "build a WorldModel from 1940 terrain"
workflows: create a snapshot of the historical geo state, then clone from it.

Returns: `{ original_place_id, clone_place_id, name, clone_type, snapshot_id }`

---

#### `geo.transition.add`
Record an explicit spatial transition (event-sourced, immutable).

| Parameter         | Type      | Default | Notes                          |
|-------------------|-----------|---------|--------------------------------|
| `target_id`       | str       | —       | Required                       |
| `transition_type` | str       | —       | Required, from TRANSITION_TYPES|
| `description`     | str       | —       | Required                       |
| `event_id`        | str       | `""`    | Causal event atom              |
| `from_state`      | str       | `""`    | State before transition        |
| `to_state`        | str       | `""`    | State after transition         |
| `occurred_at`     | str       | `""`    | Timestamp or description       |
| `evidence`        | list[str] | `[]`    |                                |
| `confidence`      | float     | `0.7`   |                                |

Returns: `{ transition_id, target_id, transition_type }`

---

#### `geo.nearby`
Walk geo:* links from a place to find connected neighbors.

| Parameter        | Type      | Default  | Notes                               |
|------------------|-----------|----------|-------------------------------------|
| `place_id`       | str       | —        | Required                            |
| `rels`           | list[str] | see below| Relation types to traverse          |
| `include_hidden` | bool      | `false`  |                                     |
| `depth`          | int       | `1`      | BFS depth limit                     |

Default relations: `geo:adjacent_to`, `geo:near`, `geo:route`,
`geo:accessible_from`, `geo:visible_from`, `geo:contains`, `sys:part_of`,
`geo:overlaps`.

`geo:contains` is a parent → child link; `sys:part_of` is the child → parent
reverse created automatically by `geo.place.add parent_place_id=...`. Including
both in the default set means traversal works in both directions without
requiring an explicit incoming-link walk.

**Hidden / revealed behavior:** A place with `hidden=true` in its meta is
excluded unless `include_hidden=true` **or** the place has a `geo:revealed_by`
outgoing link (created by `geo.reveal`). Because the original atom is immutable,
the `hidden` flag is never cleared — revealed status is determined solely by the
presence of a transition atom.

Returns: `{ place_id, nearby: [{ id, depth, via, content, meta }], count }`

---

#### `geo.path`
Find a BFS path between two spatial atoms.

| Parameter        | Type      | Default  | Notes                          |
|------------------|-----------|----------|--------------------------------|
| `src_id`         | str       | —        | Required                       |
| `dst_id`         | str       | —        | Required                       |
| `rels`           | list[str] | see below| Relation types to traverse     |
| `max_depth`      | int       | `6`      |                                |
| `include_hidden` | bool      | `false`  |                                |

Default relations: `geo:adjacent_to`, `geo:near`, `geo:route`,
`geo:accessible_from`, `geo:contains`, `sys:part_of`.

Applies the same hidden/revealed logic as `geo.nearby`: a place is treated as
visible if it has a `geo:revealed_by` link, regardless of its `hidden` flag.

Returns: `{ found, path: [atom_id,...], relations: [rel,...], length }`

---

#### `geo.reveal`
Reveal a hidden place by appending a `revealed` transition.

| Parameter     | Type  | Default | Notes                              |
|---------------|-------|---------|------------------------------------|
| `place_id`    | str   | —       | Required                           |
| `revealed_by` | str   | `""`    | Evidence/event atom that triggered reveal |
| `note`        | str   | `""`    |                                    |
| `confidence`  | float | `0.8`   |                                    |

The original place atom is not mutated. The revealed state is queryable
through the place's `geo:changed_by` / `geo:revealed_by` transition atoms.

Returns: `{ status, place_id, transition_id }`

---

#### `geo.diagnose`
Diagnose spatial consistency and modeling gaps in the active Geo root.

Returns a structured report:

```json
{
  "geo_root_id": "...",
  "counts": {
    "places": 12,
    "coordinates": 8,
    "connections": 15,
    "affines": 1,
    "clones": 2,
    "transitions": 4
  },
  "diagnosis": {
    "places_without_coordinates": [...],
    "hidden_places": [...],
    "orphan_connections": [...],
    "clone_without_original": [...],
    "low_confidence_places": [...],
    "has_affine_systems": true,
    "has_transition_history": true
  }
}
```

Each list is capped at the 10 most recent items.
`low_confidence_places` flags places with `confidence < 0.4`.
`orphan_connections` flags connections whose `src_id` or `dst_id` is not
found in the visible places set.
`hidden_places` lists places with `hidden=true` that have **not** yet been
revealed (no `geo:revealed_by` link). Revealed places are excluded from this
list even though their `hidden` flag remains `true` in the immutable atom.

---

#### `geo.analyze` *(future)*

Reserved for coordinate transform execution:

```
geo.analyze type="transform" affine_id=<id> coordinate_id=<id>
```

Applies a recorded affine transform atom to a coordinate atom, producing a
new coordinate atom in the target system. Not yet implemented.

---

#### `geo.history` / `geo.timeview`
Walk the temporal index from the oldest entry to the newest.

| Parameter       | Type      | Default | Notes                                   |
|-----------------|-----------|---------|-----------------------------------------|
| `limit`         | int       | `100`   | Maximum entries to return               |
| `include_hidden`| bool      | `false` |                                         |
| `atom_types`    | list[str] | all     | Filter to specific TEMPORAL_TYPES       |

`timeview` is an alias for `history`.

Returns: `{ geo_id, history: [{ id, content, type, occurred_at, time_sort, meta }], count }`

---

#### `geo.time.rebuild`
Rebuild the temporal linked list from all temporal subset atoms. Run once
after importing historical data that predates the index.

Returns: `{ status, geo_id, count }`

---

### 1.4 CLI Shorthand Reference

| Alias              | Method              | Key args                          |
|--------------------|---------------------|-----------------------------------|
| `geo.new`          | `geo.new`           | `title`, `coordinate_system`      |
| `geo.open`         | `geo.open`          | `geo_id`                          |
| `geo.ls`           | `geo.ls`            | —                                 |
| `geo.map`          | `geo.map`           | —                                 |
| `geo.rm`           | `geo.rm`            | —                                 |
| `geo.coord`        | `geo.coord.add`     | `label`, `system`, `lat`, `lon`   |
| `geo.place`        | `geo.place.add`     | `name`, `place_type`              |
| `geo.pstate`       | `geo.place.state`   | `place_id`, `state`               |
| `geo.feat`         | `geo.feature.add`   | `place_id`, `name`, `feature_type`|
| `geo.obs`          | `geo.observe.add`   | `target_id`, `text`, `method`     |
| `geo.event`        | `geo.event.add`     | `description`, `place_id`         |
| `geo.layer`        | `geo.layer.add`     | `label`, `layer_type`             |
| `geo.snap`         | `geo.snapshot.add`  | `label`, `captured_at`            |
| `geo.connect`      | `geo.connect`       | `src_id`, `dst_id`, `connection_type` |
| `geo.affine`       | `geo.affine.add`    | `label`, `source_system`, `target_system`, `matrix` |
| `geo.clone`        | `geo.clone`         | `place_id`, `clone_type`          |
| `geo.trans`        | `geo.transition.add`| `target_id`, `transition_type`, `description` |
| `geo.nearby`       | `geo.nearby`        | `place_id`, `depth`               |
| `geo.path`         | `geo.path`          | `src_id`, `dst_id`                |
| `geo.reveal`       | `geo.reveal`        | `place_id`, `revealed_by`         |
| `geo.diagnose`     | `geo.diagnose`      | —                                 |
| `geo.history`      | `geo.history`       | `limit`, `atom_types`             |
| `geo.timeview`     | `geo.history`       | `limit`, `atom_types`             |
| `geo.time.rebuild` | `geo.time.rebuild`  | —                                 |

---

### 1.5 Spatial Query Operations

#### 1.5.1 Neighborhood traversal (`geo.nearby`)

`geo.nearby` performs a BFS over outgoing links from a starting place.
The `depth` parameter controls how many hops to walk. Hidden places are
excluded unless `include_hidden=true`.

**Hierarchy traversal:** `geo:contains` (parent → child) and `sys:part_of`
(child → parent) are both in the default relation set. `sys:part_of` is created
automatically by `geo.place.add parent_place_id=...` as the explicit reverse of
`sys:contains`, so both up and down traversal work without incoming-link scans.

**Note:** For relationship types that do not have a pre-created reverse link
(e.g. custom `geo:*` relations added via `geo.connect directed`), an
`include_incoming=true` flag could be added to also walk `get_incoming_links`.
The current default set covers the common containment case.

```
geo.nearby <castle_id> depth=2
# → returns all places within 2 connection hops
```

The result includes the traversal `via` relation for each neighbor, which
lets you distinguish route-reachable from line-of-sight reachable places.

#### 1.5.2 Path finding (`geo.path`)

`geo.path` finds the shortest connection path between two atoms using BFS.
It respects IAM visibility and skips hidden places unless opted in.

```
geo.path <gate_id> <throne_room_id> max_depth=5
# → { found: true, path: [gate, courtyard, hall, throne_room], relations: [...] }
```

If no path exists within `max_depth`, returns `{ found: false }`.

#### 1.5.3 Reveal / hidden pattern

Create a place as hidden, then reveal it when appropriate evidence arrives:

```
# Create hidden
geo.place name="Secret passage" hidden=true
# → place_id = P1

# Later: reveal
geo.reveal P1 revealed_by=<evidence_atom_id> note="Discovered in survey 1847"
# → creates TransitionAtom (type=revealed) linked to P1
# → P1 original atom is unchanged; the revealed state is in the transition
```

To query whether a place has been revealed, look for `geo:revealed_by` or the
shared `sys:revealed_by` outgoing link from the place atom. The shared link is
used by `VisibilityMixin`, allowing the same visibility semantics to be reused
by other Earth-family concept models.

---

### 1.6 Temporal Index

#### 1.6.1 Design

GeoConcept maintains a singly-linked temporal index rooted at the GeoRoot atom.
The index covers five atom types: `geo_event`, `geo_transition`,
`geo_place_state`, `geo_observation`, `geo_snapshot`.

```
GeoRoot ──sys:time_top────▶ [2020-01-01 event]
                                    │ sys:time_next
                                    ▼
                            [2021-06-15 observation]
                                    │ sys:time_next
                                    ▼
                            [2024-03-15 event]
                                    │ sys:time_next
                                    ▼
                            [9999 (no date) snapshot]
GeoRoot ──sys:time_bottom─▶ [9999 (no date) snapshot]
```

> The temporal index is managed by `TemporalMixin` (`lib/akasha/concepts/mixins/temporal.py`)
> and uses the `sys:time_*` link prefix so the same index structure can be shared
> across all concept models.

Each temporal atom stores two fields in meta:
- `occurred_at` — raw value supplied by the caller (ISO date, description, etc.)
- `time_sort` — normalised sort key (`YYYY-MM-DDTHH:MM:SS`; undated atoms get
  `9999-12-31T23:59:59` and sort last)

#### 1.6.2 Insertion sort

`_append_to_time_index` walks the linked list from the head and inserts the new
atom before the first node whose `time_sort` is greater. This is O(n) per
insert; for most Geo roots (hundreds of events) this is acceptable.

#### 1.6.3 Rebuild

If data was imported without timestamps, or if atoms were created before the
temporal index was deployed, run `geo.time.rebuild` once. It:
1. Collects all temporal atoms from the five subsets
2. Reads `occurred_at` / `event_time` / `observed_at` / `captured_at` from meta
3. Clears existing `sys:time_top`, `sys:time_bottom`, `sys:time_next`, and `sys:time_previous` links
4. Re-inserts all atoms in sorted order

#### 1.6.4 Filtering

`geo.history` accepts `atom_types` to restrict the view:

```
# Only events and place states
geo.history atom_types=["geo_event","geo_place_state"]

# Only snapshots
geo.history atom_types=["geo_snapshot"]
```

---

### 1.7 Workflow Examples

#### 1.7.1 Archaeological site mapping

```
# Create the geo root
geo.new title="Acropolis Excavation 2024" coordinate_system=wgs84

# Add datum coordinate
geo.coord label="site datum" lat=37.9715 lon=23.7267 precision="±2m" confidence=0.95

# Add places
geo.place name="Parthenon" place_type=building coordinate_id=<coord_id>
geo.place name="Erechtheion" place_type=building
geo.place name="South Slope" place_type=region

# Feature on a place
geo.feat <parthenon_id> name="East Frieze" feature_type=archaeological

# Connect places
geo.connect <parthenon_id> <erechtheion_id> connection_type=adjacent_to direction=mutual

# Record an observation
geo.obs <parthenon_id> text="Column drum displacement observed" method=human observer="Dr. Smith"

# Record an event
geo.event description="Partial column collapse" place_id=<parthenon_id> event_time="2024-03-15"

# Record the resulting state change
geo.pstate <parthenon_id> state="structural_review" event_id=<event_id> occurred_at="2024-03-15"

# Snapshot the current state
geo.snap label="2024-Q1" captured_at="2024-03-31" members=[<parthenon_id>, <erechtheion_id>]

# Diagnose
geo.diagnose
```

#### 1.7.2 Disputed geography (alternate-reality clone)

```
geo.new title="Contested Border Region"

# Canonical place
geo.place name="Riverside Town" place_type=region coordinate_id=<coord_id>

# Alternate claim
geo.clone <town_id> name="Riverside Town (eastern claim)" clone_type=disputed \
    reason="Administrative boundary dispute 1923"

# Record the clone has a different coordinate interpretation
geo.coord label="eastern claim origin" lat=48.1 lon=17.2 confidence=0.6
geo.transition.add <clone_id> transition_type=moved \
    description="Boundary reassignment 1923" from_state="pre-1923" to_state="post-1923"
```

#### 1.7.3 ARG / narrative hidden place reveal

```
# Session 1: world-building
geo.new title="Undercity"
geo.place name="Hidden Market" hidden=true
geo.place name="Main Tunnel" place_type=road

# Session 4: player finds a map
geo.obs <main_tunnel_id> text="Player finds a hidden door" method=human
geo.reveal <hidden_market_id> revealed_by=<observation_id> note="Players found the hidden market"

# Players can now reach the market
geo.connect <main_tunnel_id> <hidden_market_id> connection_type=accessible_from
geo.nearby <main_tunnel_id>
# → now includes hidden_market_id
```

#### 1.7.4 Multi-system coordinate mapping

```
# Two coordinate systems exist
geo.new title="Factory Floor" coordinate_system=local_grid

geo.coord label="machine A" system=local_grid x=10.5 y=3.2
geo.coord label="machine A" system=pixel x=1050 y=320

# Register the affine transform between them
geo.affine label="grid_to_pixel" source_system=local_grid target_system=pixel \
    matrix=[[100,0],[0,100]] offset=[0,0]
```

---

---

## 2. MapConcept

**File:** `lib/akasha/concepts/map.py`
**Concept prefix:** `map`
**Context key:** `active_map_root`
**Index set:** `set:map:index`

### 2.1 Design Rationale

MapConcept models cartographic depiction: how geography was drawn, named,
projected, omitted, revised, and interpreted in a specific map or map
tradition.

- **GeoConcept** records spatial reality — what exists.
- **MapConcept** records representation — how someone depicted it.
- **CorrespondenceConcept** records cross-system mapping claims.

MapConcept is designed for historical cartography, administrative boundary
research, archaeology, field survey digitization, intelligence map analysis,
fictional map studies, and country/territory modeling.

A map is not treated as neutral geography. It is a source object with maker,
purpose, bias, projection, scale, edition history, labels, geometry, and
grounding claims.

**Core principles:**

- Map editions are source-like atoms with provenance and credibility.
- Features are things depicted on a map, not things that exist in the world.
- Geometries are how features are drawn (point, polygon, line, …).
- Labels are textual representations attached to features or geometries.
- Groundings connect map-local depictions to external atoms (Geo, Human, Fact,
  CorrespondenceConcept atoms) using `corr:*` links for interoperability.
- Revisions are event-sourced through transition atoms; source atoms are never
  mutated.
- Evaluation is event-sourced; confidence is read-time, not backfilled.
- Temporal ordering is maintained through shared `sys:time_top`, `sys:time_next`,
  and related links managed by `TemporalMixin` — identical in structure to the
  GeoConcept temporal index.

#### Pipeline overview

```
map.new title="Meiji Administrative Map Collection"
    │
    ├── map.edition  title="Dajokan Map 1871"  credibility=0.9
    │       │
    │       ├── map.feature  name="Musashi Province"  feature_type=admin_boundary
    │       │       │
    │       │       ├── map.geom    geometry_type=polygon  coordinates=<data>
    │       │       ├── map.label   text="Musashi Province"  language=ja
    │       │       └── map.ground  dst_id=<geo_place>  relation=overlaps
    │       │
    │       └── map.projection  target_system=wgs84  method=georeference
    │
    ├── map.eval    target_id=<feature>  confidence=0.65
    ├── map.trans   target_id=<edition>  transition_type=superseded  occurred_at=1878
    │
    ├── map.history                  (temporal linked-list walk)
    ├── map.diagnose                 (quality report)
    └── map.trace   target_id=<id>   (evidence/eval chain)
```

---

### 2.2 Cortex Topology

#### 2.2.1 Root atom

```
MapRoot  (concept="map", role="root")
```

#### 2.2.2 Link structure

```
MapRoot ──map:has_edition    ──▶ EditionAtom
MapRoot ──map:has_feature    ──▶ FeatureAtom
MapRoot ──map:has_geometry   ──▶ GeometryAtom
MapRoot ──map:has_label      ──▶ LabelAtom
MapRoot ──map:has_projection ──▶ ProjectionAtom
MapRoot ──map:has_grounding  ──▶ GroundingAtom
MapRoot ──map:has_snapshot   ──▶ SnapshotAtom
MapRoot ──map:has_transition ──▶ TransitionAtom
MapRoot ──map:has_eval       ──▶ EvalAtom

EditionAtom ──map:depicts_feature ──▶ FeatureAtom
FeatureAtom ──map:has_geometry    ──▶ GeometryAtom
LabelAtom   ──map:labels          ──▶ FeatureAtom / GeometryAtom
EditionAtom ──map:uses_label      ──▶ LabelAtom
EditionAtom ──map:projected_by    ──▶ ProjectionAtom

GroundingAtom ──corr:from         ──▶ Map-local atom
GroundingAtom ──corr:to           ──▶ External atom (Geo, Human, Fact, …)
Map-local     ──corr:{relation}   ──▶ External atom

TargetAtom ──map:changed_by       ──▶ TransitionAtom
TargetAtom ──map:{type}_by        ──▶ TransitionAtom  (e.g. map:superseded_by)
TargetAtom ──map:evaluated_by     ──▶ EvalAtom

MapRoot ──sys:time_top    ──▶ oldest temporal atom
MapRoot ──sys:time_bottom ──▶ newest temporal atom
Atom    ──sys:time_next   ──▶ next newer atom
Atom    ──sys:time_previous──▶ next older atom
```

Temporal atoms: `map_edition`, `map_snapshot`, `map_transition`, `map_eval`.

#### 2.2.3 Set layout

| Set | Contents |
|:----|:---------|
| `set:map:index` | All Map root atoms |
| `set:map:{id}` | All atoms in this Map collection |
| `set:map:{id}:editions` | Map edition/source atoms |
| `set:map:{id}:features` | Depicted feature atoms |
| `set:map:{id}:geometries` | Geometry atoms |
| `set:map:{id}:labels` | Label atoms |
| `set:map:{id}:projections` | Projection/georeference atoms |
| `set:map:{id}:groundings` | Grounding/correspondence atoms |
| `set:map:{id}:snapshots` | Temporal snapshots |
| `set:map:{id}:transitions` | Revision/transition atoms |
| `set:map:{id}:evals` | Event-sourced evaluations |
| `set:concept:{id}` | Concept-word atoms only |

#### 2.2.4 Controlled vocabularies

| Vocabulary | Values |
|:-----------|:-------|
| `coordinate_system` | `local_grid`, `pixel`, `wgs84`, `utm`, `relative`, `symbolic`, `other` |
| `feature_type` | `border`, `road`, `admin_boundary`, `coastline`, `settlement`, `landmark`, `annotation`, `route`, `terrain`, `symbolic`, `other` |
| `geometry_type` | `point`, `line`, `polygon`, `multipoint`, `multiline`, `multipolygon`, `raster`, `symbolic`, `other` |
| `status` | `active`, `disputed`, `retracted`, `superseded`, `unverified` |
| `transition_type` | `created`, `superseded`, `revised`, `annotated`, `translated`, `derived`, `suppressed`, `redacted`, `restored`, `renamed`, `other` |
| `source_kind` | `map`, `atlas`, `archive`, `official_doc`, `survey`, `fieldnote`, `academic_paper`, `news_article`, `other` |
| `projection_method` | `manual`, `affine`, `georeference`, `control_points`, `rubber_sheet`, `llm`, `other` |

---

### 2.3 Kernel Methods

| Method | IAM | Description |
|:-------|:----|:------------|
| `map.new` | write | Create a new Map collection root |
| `map.open` | write | Activate an existing Map collection |
| `map.ls` | read | List accessible Map collections |
| `map.map` / `map.show` | read | Show structure of active Map collection |
| `map.rm` | write | Soft-delete active Map collection from index |
| `map.edition.add` | write | Add a map edition/source with provenance metadata |
| `map.feature.add` | write | Add a depicted cartographic feature |
| `map.geometry.add` | write | Add geometry for a feature |
| `map.label.add` | write | Add label text (with language, script, romanization) |
| `map.projection.add` | write | Add projection/georeference metadata |
| `map.ground` | write | Ground a map atom to an external atom via `corr:*` links |
| `map.snapshot.add` | write | Capture a temporal snapshot of map state |
| `map.transition.add` | write | Record a map revision or cartographic state change |
| `map.history` | read | Read temporal linked-list history |
| `map.timeview` | read | Alias for `map.history` |
| `map.time.rebuild` | write | Rebuild temporal index (for bulk import) |
| `map.eval` | write | Append event-sourced evaluation of any map atom |
| `map.diagnose` | read | Diagnose completeness and conflicts |
| `map.trace` | read | Trace one atom's evidence, evaluation, and transition history |

#### 2.3.1 `map.edition.add` parameters

| Parameter | Type | Default | Description |
|:----------|:-----|:--------|:------------|
| `title` | str | required | Edition title |
| `maker` | str | `""` | Map maker / cartographer |
| `publisher` | str | `""` | Publisher or issuing body |
| `created_at` | str | `""` | Creation date (ISO or partial) — becomes temporal sort key |
| `projection` | str | `""` | Named projection (Mercator, etc.) |
| `scale` | str | `""` | Map scale |
| `coordinate_system` | str | `symbolic` | One of controlled vocabulary |
| `purpose` | str | `""` | Stated purpose of the map |
| `purpose_tags` | list | `[]` | Free-text purpose tags |
| `quelle_level` | int | 2 | Source quality level 1–5 |
| `independence` | float | 0.5 | Source independence 0–1 |
| `credibility` | float | 0.5 | Overall source credibility 0–1 |
| `bias` | str | `unknown` | Bias assessment |
| `bias_tags` | list | `[]` | Free-text bias tags |
| `motivation` | str | `""` | Motivation behind the map |
| `source_kind` | str | `map` | One of controlled vocabulary |
| `status` | str | `active` | One of status types |
| `note` | str | `""` | Atom content override |

#### 2.3.2 `map.ground` parameters

| Parameter | Type | Default | Description |
|:----------|:-----|:--------|:------------|
| `src_id` | str | required | Map-local atom (feature, geometry, label, …) |
| `dst_id` | str | required | External atom (Geo place, Human, Fact, …) |
| `relation` | str | `grounds` | Relation name — becomes `corr:{relation}` link |
| `source_id` | str | `""` | Evidentiary source atom |
| `confidence` | float | 0.7 | Grounding confidence 0–1 |
| `status` | str | `active` | One of status types |
| `context` | str | `""` | Contextual note on scope |
| `note` | str | `""` | Atom content override |

`op_ground` emits three link types:
- `corr:from` (grounding atom → src)
- `corr:to` (grounding atom → dst)
- `corr:{relation}` (src → dst directly)

This makes groundings directly consumable by CorrespondenceConcept traversal.

---

### 2.4 CLI Shorthand Reference

| CLI | Full method |
|:----|:------------|
| `map.new` | `map.new` |
| `map.open` | `map.open` |
| `map.ls` | `map.ls` |
| `map.show` | `map.show` |
| `map.rm` | `map.rm` |
| `map.ed` / `map.edition` | `map.edition.add` |
| `map.feat` | `map.feature.add` |
| `map.geom` | `map.geometry.add` |
| `map.label` | `map.label.add` |
| `map.proj` | `map.projection.add` |
| `map.ground` | `map.ground` |
| `map.snap` | `map.snapshot.add` |
| `map.trans` | `map.transition.add` |
| `map.history` / `map.timeview` | `map.history` |
| `map.time.rebuild` | `map.time.rebuild` |
| `map.eval` | `map.eval` |
| `map.diagnose` | `map.diagnose` |
| `map.trace` | `map.trace` |
| `mp.new` / `mp.open` / … | Same as above, short prefix |

---

### 2.5 Workflow Examples

#### 2.5.1 Historical administrative map

```
# Create collection
map.new title="Meiji Administrative Map Collection"

# Add a source edition
map.edition title="Dajokan Administrative Map 1871" \
    maker="Dajokan" source_kind="official_doc" credibility=0.9 \
    coordinate_system="symbolic" created_at="1871-07-14"
# → edition_id = E1

# Add a depicted feature
map.feat edition_id=E1 name="Musashi Province" \
    feature_type="admin_boundary" confidence=0.85
# → feature_id = F1

# Add geometry
map.geom feature_id=F1 geometry_type="polygon" \
    coordinates=[[139.4,35.4],[139.8,35.4],[139.8,35.9],[139.4,35.9]] \
    coordinate_system="wgs84"

# Add label
map.label edition_id=E1 target_id=F1 \
    text="Musashi Province" language="ja" script="kanji"

# Ground to a GeoConcept place
map.ground src_id=F1 dst_id=<geo_place_id> \
    relation="overlaps" confidence=0.8

# Record that this edition was superseded
map.trans target_id=E1 transition_type="superseded" \
    description="Superseded by Meiji 11 prefecture reorganization" \
    occurred_at="1878-07-22"

# Evaluate a feature with updated confidence
map.eval target_id=F1 confidence=0.65 \
    note="Boundary approximate; source map lacks precise projection."

# Diagnose the collection
map.diagnose

# Trace a feature's evidence chain
map.trace target_id=F1
```

#### 2.5.2 Fictional map with georeferencing

```
# Fictional map of a game world
map.new title="Harmonia Continent Map v2"

map.edition title="Game World Map Rev2" maker="Studio A" \
    coordinate_system="pixel" credibility=0.95 source_kind="map"
# → E2

map.feat edition_id=E2 name="Iron Wastes" feature_type="terrain"
# → F2

map.geom feature_id=F2 geometry_type="polygon" \
    coordinates=[[1200,400],[1600,400],[1600,900],[1200,900]] \
    coordinate_system="pixel"

# Add georeference projection to align pixel coords to local grid
map.proj edition_id=E2 target_system="local_grid" \
    method="affine" matrix=[[0.01,0],[0,0.01]] offset=[0,0] \
    confidence=0.9

# Ground to a Geo place in the game world GeoConcept
map.ground src_id=F2 dst_id=<geo_iron_wastes> relation="depicts"

map.history
map.diagnose
```

#### 2.5.3 Rebuilding temporal index after bulk import

```
# After importing 200 editions from an archive in arbitrary order
map.time.rebuild
# → rebuilds sys:time_top/bottom/next/previous chain sorted by time_sort

map.history limit=20
# → most recent 20 temporal events, earliest first
```

---

---

> **Part II — Cross-System Alignment**
>
> *Evidenced, scoped, confidence-weighted correspondence between representations.*

---

## 3. CorrespondenceConcept

**File:** `lib/akasha/concepts/correspondence.py`
**Concept prefix:** `corr`
**Context key:** `active_corr_root`
**Index set:** `set:corr:index`

### 3.1 Design Rationale

CorrespondenceConcept models the claim that two things in different systems
correspond — without asserting they are identical. It is designed for use
cases where mappings are contested, time-scoped, inferred, or carry
non-trivial provenance:

- Historical border → modern administrative unit
- Country-level entity → geographic region in a GeoConcept root
- Fictional place → real-world location (ARG or fiction-to-reality mapping)
- Cross-language concept equivalences
- Ontology alignment between two knowledge bases

**Core principle:** A correspondence is a scoped, evidenced, directional
or mutual mapping *claim*. Confidence is a first-class value, computed
from source credibility and (for inferred links) from extraction and
inference algorithm quality.

#### Pipeline overview

```
corr.new title="Japan administrative mapping"
    │
    ├── corr.sys  label="Historical provinces" system_type="historical"
    ├── corr.sys  label="Modern prefectures"   system_type="administrative"
    │
    ├── corr.src  kind="official_doc" title="Meiji reform decree" credibility=0.9
    │
    ├── corr.link src_id=<province> dst_id=<prefecture>
    │             relation=replaces source_id=<src> confidence=0.85
    │
    ├── corr.infer src_id=<A> dst_id=<B> relation=overlaps inputs=[...]
    │             (confidence = extraction × inference × weighted_source_credibility)
    │
    ├── corr.proj  link_id=<link> target_system_id=<game_world_system>
    │
    ├── corr.eval  link_id=<link> confidence=0.6 status=disputed
    ├── corr.dispute target_id=<link> reason="..." severity=high
    │
    ├── corr.trace  link_id=<link>   (full provenance view)
    └── corr.diagnose                (quality report)
```

---

### 3.2 Cortex Topology

#### 3.2.1 Root atom

| Field         | Value                     |
|---------------|---------------------------|
| `type`        | `"concept"`               |
| `concept`     | `"corr"`                  |
| `role`        | `"root"`                  |
| `title`       | User-supplied title       |
| `description` | Optional                  |

The root is added to `set:corr:index` (global) and `set:corr:{root_id}` (content).

#### 3.2.2 Subset sets

| Subset        | Set key                           | Relation from root      |
|---------------|-----------------------------------|-------------------------|
| `systems`     | `set:corr:{id}:systems`           | `corr:has_system`       |
| `links`       | `set:corr:{id}:links`             | `corr:has_link`         |
| `projections` | `set:corr:{id}:projections`       | `corr:has_projection`   |
| `sources`     | `set:corr:{id}:sources`           | `corr:has_source`       |
| `source_evals`| `set:corr:{id}:source_evals`      | `corr:has_source_eval`  |
| `evals`       | `set:corr:{id}:evals`             | `corr:has_eval`         |
| `disputes`    | `set:corr:{id}:disputes`          | `corr:has_dispute`      |

#### 3.2.3 Key link patterns

```
# System registration
CorrRoot ──corr:has_system──▶ SystemAtom
SystemAtom ──corr:refers_to──▶ ExternalRefAtom (optional)

# Direct link
CorrRoot ──corr:has_link──▶ LinkAtom
LinkAtom ──corr:from──────▶ SrcAtom
LinkAtom ──corr:to────────▶ DstAtom
LinkAtom ──corr:evidenced_by──▶ SourceAtom
SrcAtom  ──corr:{relation}──▶ DstAtom    (direct graph edge)
DstAtom  ──corr:{relation}──▶ SrcAtom    (only if direction=mutual)

# Inferred link (same topology as direct; provenance in meta)
LinkAtom ──corr:evidenced_by──▶ SourceAtom_1
LinkAtom ──corr:evidenced_by──▶ SourceAtom_2  ...

# System attribution
LinkAtom ──corr:src_system──▶ SystemAtom
LinkAtom ──corr:dst_system──▶ SystemAtom

# Projection
ProjectionAtom ──corr:projects_from──▶ LinkAtom
ProjectionAtom ──corr:projects_into──▶ TargetSystemAtom

# Evaluation (event-sourced, immutable)
LinkAtom   ──corr:evaluated_by──▶ EvalAtom
SourceAtom ──corr:evaluated_by──▶ SourceEvalAtom

# Dispute
TargetAtom ──corr:disputed_by──▶ DisputeAtom
```

#### 3.2.4 Controlled vocabularies

**RELATION_TYPES** — `equals`, `overlaps`, `contains`, `part_of`,
`adjacent_to`, `replaces`, `derived_from`, `claims`, `governs`,
`administers`, `symbolically_matches`, `other`

**STATUS_TYPES** — `active`, `disputed`, `retracted`, `superseded`,
`unverified`

**SOURCE_KINDS** — `map`, `official_doc`, `treaty`, `archive`,
`fieldnote`, `fact`, `geo`, `country`, `academic_paper`, `news_article`,
`other`

**ALGO_METHODS** — `human`, `llm`, `rule_based`, `statistical`,
`pattern_matching`, `hybrid`

---

### 3.3 Kernel Methods

#### `corr.new`
Create a new Correspondence root.

| Parameter     | Type | Required |
|---------------|------|----------|
| `title`       | str  | yes      |
| `description` | str  | no       |

Returns: `{ corr_id, concept_id, title }`

#### `corr.open`
Open an existing root and set it as the session focus.

| Parameter | Type | Required |
|-----------|------|----------|
| `corr_id` | str  | yes      |

#### `corr.ls`
List all accessible Correspondence roots (newest-first).

#### `corr.map`
Show structure of the active root — all 7 subset member lists.

#### `corr.rm`
Soft-delete the active root (removes from index; atoms retained).

---

#### `corr.system.add`
Register a coordinate or conceptual system.

| Parameter     | Type | Default    | Notes                          |
|---------------|------|------------|--------------------------------|
| `label`       | str  | —          | Required                       |
| `system_type` | str  | `generic`  | Free-form type tag             |
| `ref_id`      | str  | `""`       | External atom this system wraps|
| `ref_universe`| str  | `""`       | Namespace of the external system|
| `description` | str  | `""`       |                                |

Returns: `{ system_id, label, system_type }`

---

#### `corr.source.add`
Register an evidence source.

| Parameter      | Type  | Default | Notes                  |
|----------------|-------|---------|------------------------|
| `ref_id`       | str   | `""`    | Link to external atom  |
| `kind`         | str   | `other` | From SOURCE_KINDS      |
| `title`        | str   | `""`    |                        |
| `url`          | str   | `""`    |                        |
| `author`       | str   | `""`    |                        |
| `publisher`    | str   | `""`    |                        |
| `published`    | str   | `""`    |                        |
| `retrieved`    | str   | `""`    |                        |
| `credibility`  | float | `0.5`   | Clamped to [0, 1]      |
| `independence` | float | `0.5`   | Source independence    |
| `note`         | str   | `""`    |                        |

Returns: `{ source_id, kind, credibility }`

---

#### `corr.source.eval`
Event-sourced credibility update for a source atom.

| Parameter      | Type  | Default | Notes              |
|----------------|-------|---------|--------------------|
| `source_id`    | str   | —       | Required           |
| `credibility`  | float | —       | New value if set   |
| `independence` | float | —       | New value if set   |
| `note`         | str   | `""`    |                    |

The original source atom is not mutated. The latest eval drives
`_effective_source_credibility` which is used in confidence calculations.

Returns: `{ eval_id, source_id, updates }`

---

#### `corr.link.add`
Add a direct evidenced correspondence link.

| Parameter      | Type  | Default    | Notes                            |
|----------------|-------|------------|----------------------------------|
| `src_id`       | str   | —          | Required                         |
| `dst_id`       | str   | —          | Required                         |
| `relation`     | str   | —          | Required; from RELATION_TYPES    |
| `source_id`    | str   | —          | Required evidence source         |
| `src_system_id`| str   | `""`       | System the src_id belongs to     |
| `dst_system_id`| str   | `""`       | System the dst_id belongs to     |
| `direction`    | str   | `directed` | `directed` or `mutual`           |
| `confidence`   | float | `0.7`      | Raw confidence before credibility|
| `status`       | str   | `active`   | From STATUS_TYPES                |
| `valid_from`   | str   | `""`       | Temporal scope start             |
| `valid_to`     | str   | `""`       | Temporal scope end               |
| `context`      | str   | `""`       | Scope context label              |
| `perspective`  | str   | `""`       | Whose perspective                |
| `note`         | str   | `""`       |                                  |

**Confidence formula (direct):**
```
final_confidence = raw_confidence × source_credibility_effective
```

Returns: `{ link_id, relation, confidence }`

---

#### `corr.link.infer`
Add an inferred correspondence link with full provenance.

| Parameter              | Type        | Default   | Notes                          |
|------------------------|-------------|-----------|--------------------------------|
| `src_id`               | str         | —         | Required                       |
| `dst_id`               | str         | —         | Required                       |
| `relation`             | str         | —         | Required; from RELATION_TYPES  |
| `inputs`               | list[dict]  | —         | Required; `[{source_id, weight}]`|
| `src_system_id`        | str         | `""`      |                                |
| `dst_system_id`        | str         | `""`      |                                |
| `direction`            | str         | `directed`|                                |
| `extraction_method`    | str         | `human`   | From ALGO_METHODS              |
| `extraction_confidence`| float       | `0.8`     |                                |
| `extraction_model`     | str         | `""`      | Model name/version if LLM      |
| `extraction_llm_trust` | float       | `1.0`     | Trust multiplier for LLM output|
| `inference_method`     | str         | `human`   | From ALGO_METHODS              |
| `inference_confidence` | float       | `0.8`     |                                |
| `inference_model`      | str         | `""`      |                                |
| `inference_llm_trust`  | float       | `1.0`     |                                |
| `steps`                | list[dict]  | `[]`      | Reasoning chain steps          |
| `status`               | str         | `active`  |                                |
| `valid_from/to`        | str         | `""`      | Temporal scope                 |
| `note`                 | str         | `""`      |                                |

**Confidence formula (inferred):**
```
eff_extraction = extraction_confidence × extraction_llm_trust
eff_inference  = inference_confidence  × inference_llm_trust
source_weighted = Σ(source_i.credibility_effective × weight_i) / Σ(weight_i)
final_confidence = eff_extraction × eff_inference × source_weighted
```

Full provenance is stored in the link atom's `meta.provenance` field and is
retrievable via `corr.trace`.

Returns: `{ link_id, relation, confidence, source_weighted_credibility }`

---

#### `corr.project.add`
Project a link into another system with an optional confidence modifier.

| Parameter            | Type  | Default | Notes                          |
|----------------------|-------|---------|--------------------------------|
| `link_id`            | str   | —       | Required — a corr_link atom    |
| `target_system_id`   | str   | —       | Required                       |
| `projected_relation` | str   | `""`    | Override relation type         |
| `confidence_modifier`| float | `1.0`   | Multiplied onto base confidence|
| `source_id`          | str   | `""`    | Evidence for the projection    |
| `note`               | str   | `""`    |                                |

```
projected_confidence = link.confidence × confidence_modifier
```

Returns: `{ projection_id, source_link_id, target_system_id, confidence }`

---

#### `corr.eval.add`
Event-sourced evaluation of a correspondence link.

| Parameter    | Type  | Default | Notes             |
|--------------|-------|---------|-------------------|
| `link_id`    | str   | —       | Required          |
| `confidence` | float | —       | New value if set  |
| `status`     | str   | `""`    | From STATUS_TYPES |
| `note`       | str   | `""`    |                   |

Original link atom is not mutated. Produces an immutable eval record.

Returns: `{ evaluation_id, target_id, updates }`

---

#### `corr.dispute.add`
Record a dispute against any correspondence atom.

| Parameter   | Type | Default  | Notes                              |
|-------------|------|----------|------------------------------------|
| `target_id` | str  | —        | Required                           |
| `reason`    | str  | —        | Required                           |
| `severity`  | str  | `medium` | `low`, `medium`, `high`, `critical`|
| `source_id` | str  | `""`     | Evidence for the dispute           |
| `note`      | str  | `""`     |                                    |

Returns: `{ dispute_id, target_id, severity }`

---

#### `corr.trace`
Full provenance trace for a correspondence link.

| Parameter | Type | Required |
|-----------|------|----------|
| `link_id` | str  | yes      |

Returns origin-sensitive breakdown:
- **direct:** source atom summary + `{ raw_confidence, source_credibility, formula }`
- **inferred:** full `provenance` dict + per-input source summaries + `credibility_breakdown`
- Both include any associated `disputes`

---

#### `corr.diagnose`
Quality report for the active Correspondence root.

| Parameter | Type | Default |
|-----------|------|---------|
| `limit`   | int  | `10`    |

Returns:
```json
{
  "corr_root_id": "...",
  "counts": { "links": 24, "disputes": 3, "projections": 5 },
  "diagnosis": {
    "low_confidence_links": [...],
    "disputed_links": [...],
    "expired_links": [...],
    "inferred_links": [...],
    "projections_without_target": [...]
  }
}
```

`expired_links` = links with a non-empty `scope.valid_to` (temporally bounded).
`low_confidence_links` = links with `confidence < 0.4`.

---

### 3.4 CLI Shorthand Reference

| Alias          | Method              | Key args                                  |
|----------------|---------------------|-------------------------------------------|
| `corr.new`     | `corr.new`          | `title`, `description`                    |
| `corr.open`    | `corr.open`         | `corr_id`                                 |
| `corr.ls`      | `corr.ls`           | —                                         |
| `corr.map`     | `corr.map`          | —                                         |
| `corr.rm`      | `corr.rm`           | —                                         |
| `corr.sys`     | `corr.system.add`   | `label`, `system_type`, `ref_id`          |
| `corr.src`     | `corr.source.add`   | `kind`, `title`, `credibility`            |
| `corr.src.eval`| `corr.source.eval`  | `source_id`, `credibility`, `independence`|
| `corr.link`    | `corr.link.add`     | `src_id`, `dst_id`, `relation`, `source_id`|
| `corr.infer`   | `corr.link.infer`   | `src_id`, `dst_id`, `relation`, `inputs`  |
| `corr.proj`    | `corr.project.add`  | `link_id`, `target_system_id`             |
| `corr.eval`    | `corr.eval.add`     | `link_id`, `confidence`, `status`         |
| `corr.dispute` | `corr.dispute.add`  | `target_id`, `reason`, `severity`         |
| `corr.trace`   | `corr.trace`        | `link_id`                                 |
| `corr.diagnose`| `corr.diagnose`     | —                                         |

---

### 3.5 Confidence Model

#### 3.5.1 Source credibility (event-sourced)

Each source has a `credibility` field in its meta (set at creation,
default `0.5`). `corr.source.eval` appends an immutable eval atom;
the latest eval drives `_effective_source_credibility`. The source atom
itself is never mutated.

#### 3.5.2 Direct link confidence

```
final_confidence = raw_confidence × source_credibility_effective
```

`raw_confidence` is the user-supplied value (default `0.7`).
Both are stored in the link meta; `corr.trace` shows the breakdown.

#### 3.5.3 Inferred link confidence

```
eff_extraction = extraction_confidence × extraction_llm_trust
eff_inference  = inference_confidence  × inference_llm_trust
source_weighted = Σ( cred_i × weight_i ) / Σ( weight_i )
final_confidence = eff_extraction × eff_inference × source_weighted
```

`llm_trust` parameters let you discount LLM-generated extraction or
inference steps. Setting `extraction_llm_trust=0.7` for a GPT-4 extraction
says "I trust this extraction at 70% of face value."

All intermediate values are stored in `meta.provenance` and exposed by
`corr.trace`.

#### 3.5.4 Projection confidence

```
projected_confidence = parent_link.confidence × confidence_modifier
```

Projections inherit the parent link's already-discounted confidence and
can apply an additional modifier (e.g. `0.8` for "this projection into
the game world loses some fidelity").

---

### 3.6 Workflow Examples

#### 3.6.1 Historical province → modern prefecture mapping

```
corr.new title="Meiji administrative reform mapping"

# Register the two systems
corr.sys label="Edo-period provinces" system_type="historical"
corr.sys label="Meiji prefectures"    system_type="administrative"

# Add a primary source
corr.src kind="official_doc" title="Dajokan decree 1871" credibility=0.95
# → source_id = S1

# Direct correspondence: Musashi → Tokyo/Kanagawa/Saitama (overlaps)
corr.link src_id=<musashi> dst_id=<tokyo>
          relation=contains source_id=S1
          src_system_id=<edo_sys> dst_system_id=<meiji_sys>
          confidence=0.9 valid_from="1871-07-14"

# Disputed boundary
corr.link src_id=<kai> dst_id=<yamanashi>
          relation=replaces source_id=S1 confidence=0.7
corr.dispute target_id=<link_id> reason="Northern border contested in 1878" severity=medium
```

#### 3.6.2 Inferred correspondence with LLM extraction

```
corr.new title="ARG fiction-to-reality layer"

corr.src kind="archive" title="In-game document scan" credibility=0.6
# → S1
corr.src kind="geo"     title="OSM region data"        credibility=0.9
# → S2

# LLM extracted the candidate pair; human verified the inference
corr.infer src_id=<fiction_city> dst_id=<real_district>
           relation=symbolically_matches
           inputs=[{"source_id": "S1", "weight": 1.0},
                   {"source_id": "S2", "weight": 2.0}]
           extraction_method=llm extraction_model="gpt-4o"
           extraction_confidence=0.75 extraction_llm_trust=0.8
           inference_method=human   inference_confidence=0.9
           note="Player council determined match in session 7"

# Check the confidence breakdown
corr.trace <link_id>
# confidence = (0.75×0.8) × (0.9×1.0) × weighted_source_cred
```

#### 3.6.3 Cross-system projection into a game world

```
# Existing real-world link
corr.link src_id=<japan_region> dst_id=<historical_province>
          relation=contains source_id=<src>
# → link_id = L1

# Project into the game world system
corr.sys label="Game world regions" system_type="fictional" ref_universe="harmonia"
corr.proj link_id=L1 target_system_id=<game_sys>
          confidence_modifier=0.7
          note="Game world uses compressed geography"

# Now diagnose the whole correspondence
corr.diagnose
```

#### 3.6.4 Source credibility update workflow

```
# Initial assessment
corr.src kind="news_article" title="Reuters 2023" credibility=0.7
# → S1

# New information: source later retracted one claim
corr.src.eval source_id=S1 credibility=0.45
              note="Partial retraction issued 2024-01"

# All links that use S1 now automatically get lower effective confidence
# when _effective_source_credibility is called (read-time, not backfilled)
corr.trace <link_using_S1>
# → source_credibility now shows 0.45 (from eval), not 0.7
```

---

---

> **Part III — Human Society**
>
> *Social-scientific modeling: individual actors, polities, sovereignty, and law.*

---

## 4. HumanConcept

**File:** `lib/akasha/concepts/human.py`
**Concept prefix:** `human`
**Context key:** `active_human_root`
**CLI prefix:** `hum.*`
**Index set:** `set:human:index`

### 4.1 Design Rationale

HumanConcept is a concept model for **evidence-based recording of real or
source-grounded human actors**. It is designed for journalism, field research,
policy analysis, intelligence work, and fiction-to-reality bridging.

**Core principle: every attribute must be grounded.** Unlike CastConcept
(fictional characters), Human enforces that assessments, estimates, and bonds
must reference at least one Source atom or evidence atom. Ungrounded claims are
flagged by `human.diagnose`.

**Downstream of FactConcept** — The recommended pipeline is:

```
FieldNote / web source → FactConcept (Source + Fact)
                               ↓
                        HumanConcept (name, life events, assessments, bonds)
                               ↓
                     SynthesisConcept / PresentationConcept
```

`human.observable` reads incoming `fact:involves_human` links
(FactAtom → HumanRoot) and outgoing `fact:evidenced_by` links
(HumanRoot → FactAtom) from FactConcept atoms, so Facts about this person are
automatically surfaced without manual linking.

**Entity resolution** — `human.merge.link` flags two Human records as possibly
the same person. `human.merge.confirm` elevates the link to `human:same_as`.
Disputes against any specific atom are recorded with `human.dispute`.

**Fictional projection** — `human.fictionalize` links a Human record to a
CastConcept atom, recording what was transformed and what was preserved. This
supports traceability from fiction back to real-world sources.

---

### 4.2 Cortex Topology

```
HumanRoot  (concept="human", role="root")
  │
  ├─ human:has_name              ──▶  NameAtom            {name, name_type, language, confidence}
  ├─ human:has_life_event        ──▶  LifeEventAtom       {event_type, value, confidence}
  ├─ human:has_status            ──▶  StatusAtom          {status, confidence}
  ├─ human:has_pseudonym         ──▶  PseudonymAtom       {pseudonym, context, confidence}
  ├─ human:has_assessment        ──▶  AssessmentAtom      {assessment_type, content, confidence}
  ├─ human:has_estimate          ──▶  EstimateAtom        {estimate_type, value, basis, confidence}
  ├─ human:has_merge_link        ──▶  MergeLinkAtom       {other_human_id, confirmed}
  ├─ human:has_alias             ──▶  AliasAtom           {alias, target_id, confidence}
  ├─ human:has_dispute           ──▶  DisputeAtom         {target_id, reason, severity}
  ├─ human:has_fictional_projection ▶ FictionalProjAtom  {cast_id, transformation, preserve}
  ├─ human:has_bond              ──▶  BondAtom            {target_id, relation, strength, direction}
  └─ human:has_bond_update       ──▶  BondUpdateAtom     {bond_id, delta, event_id}

ContentAtom ──human:evidenced_by──▶ SourceAtom / FactAtom
HumanRoot   ──human:identified_from─▶ SourceAtom
HumanRoot   ──human:possibly_same_as▶ OtherHumanRoot   (unconfirmed merge)
HumanRoot   ──human:same_as─────────▶ OtherHumanRoot   (confirmed merge)
HumanRoot   ──human:fictionalized_as▶ CastRoot
```

**Set layout:**

| Set | Contents |
|-----|----------|
| `set:human:index` | All Human root atoms (global) |
| `set:human:{id}` | All atoms in this Human record |
| `set:human:{id}:names` | Name atoms |
| `set:human:{id}:life_events` | Life event atoms (birth, death, career, …) |
| `set:human:{id}:statuses` | Status atoms (alive/deceased/unknown/…) |
| `set:human:{id}:pseudonyms` | Pseudonym atoms |
| `set:human:{id}:assessments` | Evidence-backed assessment atoms |
| `set:human:{id}:estimates` | Estimated attribute atoms |
| `set:human:{id}:merge_links` | Merge link and confirmation atoms |
| `set:human:{id}:aliases` | Contextual alias atoms |
| `set:human:{id}:disputes` | Dispute atoms |
| `set:human:{id}:fictional` | Fictional projection atoms |
| `set:human:{id}:bonds` | Relationship bond atoms |
| `set:human:{id}:bond_updates` | Bond state update atoms |
| `set:concept:{id}` | Concept-word atoms |

---

### 4.3 Kernel Methods

| Method | IAM | Description |
|--------|-----|-------------|
| `human.new` | write | Create a new Human record |
| `human.open` | write | Activate an existing Human record |
| `human.ls` | read | List all Human records |
| `human.map` | read | Return full atom map of the active Human |
| `human.rm` | write | Soft-delete the active Human record |
| `human.name.add` | write | Add a name (primary, legal, informal, …) |
| `human.birth.set` | write | Record birth date and/or place |
| `human.death.set` | write | Record death date and/or place |
| `human.status.set` | write | Set status (alive/deceased/unknown/…) |
| `human.pseudo.add` | write | Add a pseudonym or alternate name |
| `human.assess` | write | Add an evidence-backed assessment |
| `human.estimate` | write | Add an estimated attribute |
| `human.merge.link` | write | Flag two records as possibly the same person |
| `human.merge.confirm` | write | Confirm a merge (elevates to `human:same_as`) |
| `human.alias` | write | Add a contextual alias |
| `human.dispute` | write | Record a dispute against a Human atom |
| `human.fictionalize` | write | Link Human to a fictional Cast projection |
| `human.bond.add` | write | Record a relationship bond |
| `human.bond.update` | write | Record a change to an existing bond |
| `human.observable` | read | Show Facts externally linked to this Human |
| `human.timeline` | read | Chronological event timeline |
| `human.profile` | read | Full structured profile |
| `human.diagnose` | read | Diagnose evidence completeness |
| `human.trace` | read | Trace evidence chain for a Human atom |

**`human.new` parameters:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | string | — | Primary name (required) |
| `description` | string | `""` | Free-text description |
| `source_id` | string | `""` | Source atom where this person was identified |
| `evidence` | list | `[]` | Additional evidence atom IDs |

**`human.assess` parameters:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `assessment_type` | string | — | `trait`/`policy`/`habit`/`risk`/`capacity`/`role`/`motivation`/`reputation` (required) |
| `content` | string | — | Assessment text (required) |
| `source_id` | string | `""` | Source atom (required unless `evidence` is provided) |
| `evidence` | list | `[]` | Evidence atom IDs |
| `confidence` | float | `0.6` | Confidence 0.0–1.0 |
| `method` | string | `"human"` | Assessment method |

**`human.bond.add` parameters:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `target_id` | string | — | Target entity atom ID (required) |
| `target_type` | string | `"human"` | `human`/`organization`/`community`/`geo`/`cast`/`world_place` |
| `relation` | string | `"associated_with"` | Relation label (becomes `human:{relation}` link) |
| `direction` | string | `"directed"` | `directed` or `mutual` |
| `strength` | float | `0.5` | Bond strength 0.0–1.0 |
| `evidence` | list | `[]` | Evidence atoms (required if `history` is empty) |
| `history` | list | `[]` | Historical event atoms driving this bond |

---

### 4.4 CLI Shorthand Reference

| CLI | Full method | Key args |
|-----|-------------|----------|
| `hum.new` | `human.new` | `name`, `description?` |
| `hum.open` | `human.open` | `human_id` |
| `hum.ls` | `human.ls` | — |
| `hum.map` | `human.map` | — |
| `hum.rm` | `human.rm` | — |
| `hum.name` | `human.name.add` | `name`, `name_type?` |
| `hum.birth` | `human.birth.set` | `date?`, `place?` |
| `hum.death` | `human.death.set` | `date?`, `place?` |
| `hum.status` | `human.status.set` | `status` |
| `hum.pseudo` | `human.pseudo.add` | `pseudonym`, `context?` |
| `hum.assess` | `human.assess` | `assessment_type`, `content`, `source_id` |
| `hum.est` | `human.estimate` | `estimate_type`, `value`, `basis` |
| `hum.merge.link` | `human.merge.link` | `other_human_id`, `reason?` |
| `hum.merge.ok` | `human.merge.confirm` | `merge_link_id` |
| `hum.alias` | `human.alias` | `alias` |
| `hum.dispute` | `human.dispute` | `target_id`, `reason` |
| `hum.fict` | `human.fictionalize` | `cast_id?`, `transformation?` |
| `hum.bond` | `human.bond.add` | `target_id`, `relation?`, `strength?` |
| `hum.bond.up` | `human.bond.update` | `bond_id`, `delta`, `event_id?` |
| `hum.obs` | `human.observable` | — |
| `hum.timeline` | `human.timeline` | — |
| `hum.profile` | `human.profile` | — |
| `hum.diagnose` | `human.diagnose` | — |
| `hum.trace` | `human.trace` | `target_id?` |

---

### 4.5 Observable / FactConcept Integration

`human.observable` surfaces Facts that are externally linked to this Human
without requiring manual wiring. It works by scanning:

- **Incoming `fact:involves_human`** — FactAtom → HumanRoot links created by `ft.ent.link`
- **Outgoing `fact:evidenced_by`** — HumanRoot → FactAtom links
- **Outgoing `human:*` / `fact:*` links** — Other outbound links to entity or fact atoms

This means the pipeline `ft.add → ft.ent.link` automatically populates
`hum.obs` for the referenced Human.

```
# A Fact recorded via FactConcept:
ft.ent.link fact_id=<fact_id> entity_id=<human_root_id> entity_type=human role=subject

# Now visible under the Human:
hum.obs
→ {"observable": [{"id": "<fact_id>", "content": "...", "meta": {...}}], "count": 1}
```

`human.timeline` merges internal life events with observable facts, ordered
chronologically.

---

### 4.6 Workflow Example

```
# Create a Human record from a news source
akasha/user $ ft.new title="Official Speech Coverage"
akasha/user $ ft.src.add url="https://example.gov/speech" kind="official_doc" credibility=0.9
{"source_id": "src_a1b2..."}

akasha/user $ hum.new name="Minister Tanaka" source_id=src_a1b2...
{"status": "created", "human_id": "hum_c3d4...", "name": "Minister Tanaka"}

# Add names and life data
akasha/user $ hum.name name="Tanaka Hiroshi" name_type="legal" language="ja" source_id=src_a1b2...
{"status": "name_added", "name_id": "nm_e5f6..."}

akasha/user $ hum.birth date="1962-03-15" source_id=src_a1b2... confidence=0.9
{"status": "birth_set", "life_event_id": "le_g7h8..."}

akasha/user $ hum.status status="active" source_id=src_a1b2...
{"status": "status_set", "value": "active"}

# Add evidence-backed assessment
akasha/user $ hum.assess assessment_type=policy \
    content="Pro-nuclear energy stance evident in 2024 Diet speech" \
    source_id=src_a1b2... confidence=0.85
{"status": "assessment_added", "assessment_id": "as_i9j0..."}

# Link a Fact to this Human via FactConcept
akasha/user $ ft.add fact_type=claim \
    content="We will achieve carbon neutrality by 2050" \
    source_id=src_a1b2...
{"fact_id": "fc_k1l2..."}

akasha/user $ ft.ent.link fact_id=fc_k1l2... entity_id=hum_c3d4... entity_type=human role=speaker
{"status": "entity_linked"}

# Observable Facts now appear automatically
akasha/user $ hum.obs
{"observable": [{"id": "fc_k1l2...", "content": "We will achieve...", ...}], "count": 1}

# Record a relationship bond
akasha/user $ hum.new name="Deputy Minister Suzuki" source_id=src_a1b2...
{"human_id": "hum_m3n4..."}

akasha/user $ hum.open human_id=hum_c3d4...
akasha/user $ hum.bond target_id=hum_m3n4... relation=works_with strength=0.8 \
    evidence=[src_a1b2...]
{"status": "bond_added", "bond_id": "bn_o5p6..."}

# Full profile and diagnosis
akasha/user $ hum.profile
{
  "name": "Minister Tanaka",
  "life_events": [...],
  "status": {"meta": {"status": "active"}, ...},
  "assessments": [...],
  "bonds": [...]
}

akasha/user $ hum.diagnose
{
  "counts": {"observable": 1, "assessments": 1, "bonds": 1, ...},
  "diagnosis": {
    "unevidenced_bonds": [],
    "has_observable_facts": true,
    ...
  }
}
```

---

---

## 5. CountryConcept

**File:** `lib/akasha/concepts/country.py`
**Concept prefix:** `country`
**Context key:** `active_country_root`
**Index set:** `set:country:index`

> *Full documentation in progress (Phase 5). The implementation is complete;
> this chapter will be expanded with full parameter tables, workflow examples,
> and cross-model integration patterns.*

### 5.1 Design Rationale

CountryConcept models polities and sovereign entities as event-sourced,
evidence-grounded graph structures. It is designed for political geography,
international relations research, historical state analysis, geopolitical
intelligence work, and fiction involving realistic statecraft.

A country is not modeled as a static record but as a layered accumulation of:
- **Names** — official, historical, native, abbreviated forms
- **Territories** — sovereign, claimed, disputed, administered, overseas
- **Capitals** — primary and historical seats of government
- **Governments** — constitutional forms, ruling parties, regime types
- **Populations** — demographic snapshots and migration events
- **Economies** — GDP, currency, trade, sanctions, debt
- **Sovereignty** — recognized, disputed, de facto, de jure status
- **Claims** — territorial, maritime, border, historical
- **Administrations** — which entities govern which territories
- **Laws** — constitutions, statutes, treaties, and their lifecycle
- **Events** — founding, independence, annexation, regime change, collapse
- **Correspondences** — links to GeoConcept, MapConcept, HumanConcept, FactConcept

**Core principles:**
- **Immutability** — all updates are new atoms; original atoms are never mutated.
- **Evidence grounding** — claims, boundaries, and assessments link to source atoms.
- **Contested reality** — sovereignty types and claim types model the contested
  nature of statehood without forcing a canonical answer.
- **Temporal depth** — the event log and law lifecycle support full historical
  reconstruction from founding to present.

### 5.2 Cortex Topology

**Subsets (15):** `names`, `territories`, `capitals`, `governments`,
`populations`, `economies`, `sovereignties`, `claims`, `administrations`,
`laws`, `law_changes`, `events`, `evals`, `disputes`, `corr_links`

**Key link patterns:**
```
CountryRoot ──country:has_name        ──▶ NameAtom
CountryRoot ──country:has_territory   ──▶ TerritoryAtom
CountryRoot ──country:has_capital     ──▶ CapitalAtom
CountryRoot ──country:has_government  ──▶ GovernmentAtom
CountryRoot ──country:has_sovereignty ──▶ SovereigntyAtom
CountryRoot ──country:has_claim       ──▶ ClaimAtom
ClaimAtom   ──country:claims          ──▶ TargetAtom (geo, country, …)
CountryRoot ──country:claims          ──▶ TargetAtom (direct fast-path)
CountryRoot ──country:has_law         ──▶ LawAtom
LawAtom     ──country:has_law_change  ──▶ LawChangeAtom
CountryRoot ──country:has_event       ──▶ EventAtom
CountryRoot ──country:has_correspondence ──▶ CorrLinkAtom
```

**Controlled vocabularies:**

| Vocabulary | Key values |
|:-----------|:-----------|
| `country_type` | `state`, `polity`, `empire`, `kingdom`, `republic`, `federation`, `colony`, `autonomous_region`, `disputed_state`, `historical_state`, `other` |
| `name_type` | `official`, `short`, `legal`, `historical`, `native`, `exonym`, `abbreviation`, `former`, `other` |
| `territory_type` | `sovereign`, `claimed`, `administered`, `occupied`, `historical`, `disputed`, `overseas`, `core`, `other` |
| `government_type` | `monarchy`, `republic`, `federal_republic`, `constitutional_monarchy`, `dictatorship`, `military`, `theocracy`, `colony`, `protectorate`, `transitional`, `unknown`, `other` |
| `sovereignty_type` | `recognized`, `partially_recognized`, `disputed`, `occupied`, `dependent`, `protectorate`, `colony`, `de_facto`, `de_jure`, `historical`, `unknown`, `other` |
| `claim_type` | `territorial`, `sovereignty`, `maritime`, `border`, `administrative`, `historical`, `symbolic`, `other` |
| `law_type` | `constitution`, `statute`, `decree`, `treaty`, `customary`, `emergency`, `administrative`, `international`, `other` |
| `event_type` | `founding`, `independence`, `annexation`, `cession`, `war`, `civil_war`, `revolution`, `coup`, `treaty`, `election`, `regime_change`, `collapse`, `recognition`, `border_change`, `law_change`, `capital_change`, `population_change`, `economic_event`, `other` |

### 5.3 Kernel Methods

| Method | IAM | Description |
|--------|-----|-------------|
| `country.new` | write | Create a new Country record |
| `country.open` | write | Activate an existing Country record |
| `country.ls` | read | List all Country records |
| `country.map` | read | Show full atom map of active Country |
| `country.rm` | write | Soft-delete active Country record |
| `country.name.add` | write | Add a name variant |
| `country.territory.add` | write | Add a territory record |
| `country.capital.set` | write | Set capital city |
| `country.gov.set` | write | Set government type/structure |
| `country.pop.set` | write | Record a population snapshot |
| `country.econ.add` | write | Add an economic data atom |
| `country.sovereignty.set` | write | Record sovereignty status |
| `country.claim.add` | write | Add a territorial or sovereignty claim |
| `country.admin.add` | write | Add an administration relationship |
| `country.law.add` | write | Add a law or legal instrument |
| `country.law.change` | write | Record a law lifecycle change |
| `country.event.add` | write | Add a historical event |
| `country.corr.link` | write | Link to a CorrespondenceConcept atom |
| `country.profile` | read | Full structured profile |
| `country.timeline` | read | Chronological event/law/sovereignty timeline |
| `country.observable` | read | Facts and observations linked to this Country |
| `country.diagnose` | read | Diagnose completeness and evidence gaps |
| `country.trace` | read | Trace evidence chain for a Country atom |

### 5.4 CLI Shorthand Reference

| CLI | Full method |
|:----|:------------|
| `country.new` | `country.new` |
| `country.open` | `country.open` |
| `country.ls` | `country.ls` |
| `country.map` | `country.map` |
| `country.rm` | `country.rm` |
| `country.name.add` | `country.name.add` |
| `country.territory.add` | `country.territory.add` |
| `country.capital.set` | `country.capital.set` |
| `country.gov.set` | `country.gov.set` |
| `country.pop.set` | `country.pop.set` |
| `country.econ.add` | `country.econ.add` |
| `country.sovereignty.set` | `country.sovereignty.set` |
| `country.claim.add` | `country.claim.add` |
| `country.admin.add` | `country.admin.add` |
| `country.law.add` | `country.law.add` |
| `country.law.change` | `country.law.change` |
| `country.event.add` | `country.event.add` |
| `country.corr.link` | `country.corr.link` |
| `country.profile` | `country.profile` |
| `country.timeline` | `country.timeline` |
| `country.observable` | `country.observable` |
| `country.diagnose` | `country.diagnose` |
| `country.trace` | `country.trace` |

### 5.5 Workflow Examples

*(Full workflow examples will be added in Phase 5.)*

---

*→ Back to [ontology-spec.md](ontology-spec.md) · [concept-model-spec.md](../concept-model/concept-model-spec.md) · [README](../README.md)*
