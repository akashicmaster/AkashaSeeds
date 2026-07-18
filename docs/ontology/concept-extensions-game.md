# AKASHA Concept Model Extension Specifications — Entertainment

**Scope:** Harmonia domain concept models (`lib/akasha/concepts/`) and AKASHA session layer (`lib/akasha/session/`)  
**Audience:** Game designers, developers, and interactive narrative authors working in the Harmonia project  
**Related:** [`docs/ontology/concept-extensions-story.md`](concept-extensions-story.md) — Cast and World narrative models  
**Related:** [`docs/concept-model/concept-model-spec.md`](../concept-model/concept-model-spec.md) — core plugin authoring guide

---

## Table of Contents

1. [Overview](#1-overview)
2. [Soma — Mech Frame Model](#2-soma--mech-frame-model)
   - [2.1 Design Rationale](#21-design-rationale)
   - [2.2 Cortex Topology](#22-cortex-topology)
   - [2.3 Kernel Methods](#23-kernel-methods)
   - [2.4 CLI Shorthand Reference](#24-cli-shorthand-reference)
   - [2.5 Slot System](#25-slot-system)
   - [2.6 Workflow Example](#26-workflow-example)
3. [Engram — Psyche Model](#3-engram--psyche-model)
   - [3.1 Design Rationale](#31-design-rationale)
   - [3.2 Cortex Topology](#32-cortex-topology)
   - [3.3 Kernel Methods](#33-kernel-methods)
   - [3.4 CLI Shorthand Reference](#34-cli-shorthand-reference)
   - [3.5 Bond System](#35-bond-system)
   - [3.6 Metaphor System](#36-metaphor-system)
   - [3.7 Workflow Example](#37-workflow-example)
4. [Operator — Tactician Model](#4-operator--tactician-model)
   - [4.1 Design Rationale](#41-design-rationale)
   - [4.2 Cortex Topology](#42-cortex-topology)
   - [4.3 Kernel Methods](#43-kernel-methods)
   - [4.4 CLI Shorthand Reference](#44-cli-shorthand-reference)
   - [4.5 Clash Modes](#45-clash-modes)
   - [4.6 Workflow Example](#46-workflow-example)
5. [Eidolon — Spatial Model](#5-eidolon--spatial-model)
   - [5.1 Design Rationale](#51-design-rationale)
   - [5.2 Cortex Topology](#52-cortex-topology)
   - [5.3 Kernel Methods](#53-kernel-methods)
   - [5.4 CLI Shorthand Reference](#54-cli-shorthand-reference)
   - [5.5 Single-Presence Invariant](#55-single-presence-invariant)
   - [5.6 Workflow Example](#56-workflow-example)
6. [Integration Patterns](#6-integration-patterns)
   - [6.1 Psyche Transplant](#61-psyche-transplant)
   - [6.2 Lost Experience After Frame Destruction](#62-lost-experience-after-frame-destruction)
   - [6.3 World × Soma × Engram](#63-world--soma--engram)
7. [SessionSpace](#7-sessionspace)
   - [7.1 Design Rationale](#71-design-rationale)
   - [7.2 Ownership vs Location](#72-ownership-vs-location)
   - [7.3 Cortex Topology](#73-cortex-topology)
   - [7.4 Kernel Methods](#74-kernel-methods)
   - [7.5 Focus Mechanism](#75-focus-mechanism)
   - [7.6 Workflow Examples](#76-workflow-examples)
   - [7.7 Stage Integration](#77-stage-integration)

---

## 1. Overview

This document covers the Entertainment tier of the AKASHA concept model ecosystem:
the Harmonia game models (Soma, Engram, Operator, Eidolon) and the AKASHA SessionSpace
layer that underpins all multi-instance interaction.

Harmonia is a suite of concept models for a game world in which **mech frames (Soma) and psyches (Engram) co-exist as separate entities**.

This separation is a foundational design principle:

```
Soma (mech frame)  ─── equippable parts, physical state, repair records
Engram (psyche)    ─── utterances/memories, resonance links to other psyches

Mounted independently in SessionSpace:
    instance.mount model=soma   slot=unit
    instance.mount model=engram slot=pilot
```

A psyche is not bound to a frame. Even if a frame is destroyed the psyche survives. Conversely, a psyche can be transplanted to a different frame. This separation underpins gameplay mechanics such as "psyche transplant" and "lost experience after frame destruction."

**SessionSpace** (`lib/akasha/session/space.py`) is the session instance layer (Layer 3)
that sits between the kernel and all concept model plugins. It manages client-owned virtual
spaces of mounted instances and the focus routing that allows multiple concept models to
operate simultaneously within a single session. It is documented here because its primary
interactive use cases arise in game and multi-participant entertainment contexts.

**File layout:** `lib/akasha/concepts/` — Harmonia domain package; `lib/akasha/session/` — AKASHA session layer.

---

## 2. Soma — Mech Frame Model

**File:** `lib/akasha/concepts/soma.py`  
**Prefix:** `soma`  
**CLI prefix:** `som.*`

### 2.1 Design Rationale

Soma represents a physical mech frame. A frame is a collection of slots; the parts equipped to those slots constitute the frame's capabilities. Part atoms are any Cortex atoms defined externally — they can be WorldConcept object atoms or atoms written with a simple `w` command.

**Slot constraints are set-managed** — Part atoms are immutable, so slot occupancy cannot be tracked by mutating metadata after equipping. Instead, per-slot sets (`set:soma:{id}:slot:{slot_name}`) count occupancy.

### 2.2 Cortex Topology

```
SomaRoot  (concept="soma", role="root")
  │
  ├─ har:equipped:{slot} ──▶  PartAtom    (any external atom)
  └─ sys:state_change    ──▶  RepairAtom  {soma_id, timestamp}
```

**Set layout:**

| Set | Contents |
|-----|----------|
| `set:soma:index` | All Soma root atoms (global) |
| `set:soma:{id}` | All atoms belonging to this frame |
| `set:soma:{id}:equipment` | Equipped part atoms |
| `set:soma:{id}:slot:head` | Head slot (capacity 1) |
| `set:soma:{id}:slot:arm_r` | Right arm slot (capacity 1) |
| `set:soma:{id}:slot:arm_l` | Left arm slot (capacity 1) |
| `set:soma:{id}:slot:core` | Core slot (capacity 1) |
| `set:soma:{id}:slot:booster` | Booster slot (capacity 2) |
| `set:soma:{id}:slot:weapon` | Weapon slot (capacity 3) |
| `set:concept:{id}` | Concept-word atoms (empty for now) |

### 2.3 Kernel Methods

| Method | IAM | Description |
|--------|-----|-------------|
| `soma.new` | write | Construct a new mech frame |
| `soma.equip` | write | Equip a part into a slot |
| `soma.status` | read | Return frame status and equipment list |
| `soma.repair` | write | Record a repair event |

**`soma.new` parameters:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | string | — | Frame name (required) |
| `max_capacity` | int | `100` | Equipment capacity ceiling (reserved for future budget enforcement) |

**`soma.equip` parameters:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `part_id` | string | — | ID of the part atom to equip (required) |
| `slot` | string | — | Slot name (`head`/`arm_r`/`arm_l`/`core`/`booster`/`weapon`) (required) |
| `cost` | int | `0` | Capacity consumed by this part (stored as link weight) |

**`soma.repair` parameters:**

None. The repair event is recorded automatically in Cortex.

### 2.4 CLI Shorthand Reference

| CLI | Full method | Key args |
|-----|-------------|----------|
| `som.new` | `soma.new` | `name`, `max_capacity?` |
| `som.equip` | `soma.equip` | `part_id`, `slot`, `cost?` |
| `som.status` | `soma.status` | — |
| `som.repair` | `soma.repair` | — |

### 2.5 Slot System

| Slot | Capacity | Description |
|------|----------|-------------|
| `head` | 1 | Head sensors / visual system |
| `arm_r` | 1 | Right arm (manipulation / shooting) |
| `arm_l` | 1 | Left arm (shield / support) |
| `core` | 1 | Power reactor / control system |
| `booster` | 2 | Propulsion units |
| `weapon` | 3 | Armaments |

Calling `soma.equip` on a full slot raises a `RuntimeError`. Unequipping a part (`soma.unequip`) to free a slot is planned for Phase 2.

### 2.6 Workflow Example

```
akasha/user $ som.new name="Unit-01"
{"status": "constructed", "soma_id": "a1b2...ef01", "name": "Unit-01"}

akasha/user $ w "Positron Rifle"         → part_id = c3d4...ab02
akasha/user $ som.equip part_id=c3d4...ab02 slot=weapon
{"status": "equipped", "slot": "weapon"}

akasha/user $ w "AT Field Generator"     → part_id = e5f6...cd03
akasha/user $ som.equip part_id=e5f6...cd03 slot=core
{"status": "equipped", "slot": "core"}

akasha/user $ som.status
{
  "soma_id": "a1b2...ef01",
  "name": "Unit-01",
  "status": "active",
  "equipment": ["c3d4...ab02", "e5f6...cd03"],
  "slots": {
    "weapon": {"parts": ["c3d4...ab02"], "capacity": 3},
    "core":   {"parts": ["e5f6...cd03"], "capacity": 1},
    ...
  }
}

akasha/user $ som.repair
{"status": "repaired", "record_id": "f7a8...de04"}
```

---

## 3. Engram — Psyche Model

**File:** `lib/akasha/concepts/engram.py`  
**Prefix:** `engram`  
**CLI prefix:** `eng.*`

### 3.1 Design Rationale

Engram represents the psyche itself. It exists independently of any frame, accumulating its own utterances/memories and resonance links to other psyches.

**Separation of psyche and frame** — Engram does not reference Soma. Which Soma the psyche is riding is managed by the SessionSpace focus and instance layer. This allows "psyche transplant" to happen naturally outside the kernel.

**Resonance** — `engram.bond` creates a resonance link (`har:resonance`) between two psyches. Strength is stored as `resonance_boost` (0.0–1.0) in the link weight `w`. Because of the event-sourced append-only design, repeated calls for the same pair do not overwrite the existing link; instead a new Bond atom is appended and the timeline tracks the latest value.

**Metaphor** — `engram.metaphor` writes a publicly scoped (`view:public`) metaphor message to Cortex for ARG use. Attaching it to a location atom enables location-based narrative discovery.

### 3.2 Cortex Topology

```
EngramRoot  (concept="engram", role="root")
  │
  ├─ har:said      ──▶  MemoryAtom    {mood, text}
  ├─ har:has_bond  ──▶  BondAtom      {resonance_boost, from, to}
  ├─ har:resonance ──▶  EngramRoot    (another psyche's root atom, w=resonance_boost)
  └─ sys:speaks    ──▶  MetaphorAtom  {is_metaphor: true, scopes: [view:public]}
                            └─ sys:located_in ──▶ LocationAtom
```

**Set layout:**

| Set | Contents |
|-----|----------|
| `set:engram:index` | All Engram root atoms (global) |
| `set:engram:{id}` | All atoms belonging to this psyche |
| `set:engram:{id}:memories` | Utterance / memory atoms |
| `set:engram:{id}:bonds` | Resonance bond atoms |
| `set:concept:{id}` | Concept-word atoms (empty for now) |

### 3.3 Kernel Methods

| Method | IAM | Description |
|--------|-----|-------------|
| `engram.new` | write | Create a new psyche |
| `engram.talk` | write | Record an utterance or memory |
| `engram.bond` | write | Record a resonance bond to another psyche |
| `engram.metaphor` | write | Place a public ARG metaphor message at a location |

**`engram.new` parameters:**

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Psyche name (required) |

**`engram.talk` parameters:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `text` | string | — | Utterance / memory text (required) |
| `mood` | string | `"neutral"` | Emotional state label |

**`engram.bond` parameters:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `target_engram_id` | string | — | Root ID of the target Engram (required) |
| `resonance_boost` | float | `1.0` | Resonance strength 0.0–1.0 (stored as link weight `w`) |

**`engram.metaphor` parameters:**

| Field | Type | Description |
|-------|------|-------------|
| `target_user_context` | string | Context hint to be implied (required) |
| `location_id` | string | Location atom ID where the message is placed (required) |

### 3.4 CLI Shorthand Reference

| CLI | Full method | Key args |
|-----|-------------|----------|
| `eng.new` | `engram.new` | `name` |
| `eng.talk` | `engram.talk` | `text`, `mood?` |
| `eng.bond` | `engram.bond` | `target_engram_id`, `resonance_boost?` |
| `eng.metaphor` | `engram.metaphor` | `target_user_context`, `location_id` |

### 3.5 Bond System

`engram.bond` **appends** resonance links; it never overwrites.

```
EngramRoot_A ──har:resonance (w=0.3)──▶ EngramRoot_B
EngramRoot_A ──har:has_bond──▶  BondAtom {resonance_boost: 0.3, from: A, to: B}
```

To read the current resonance strength, inspect the latest Bond atom in `set:engram:{id}:bonds`. When strength changes, a new Bond atom is appended and the timeline tracks the latest value.

### 3.6 Metaphor System

`engram.metaphor` writes an **ARG mystery message** from the psyche into Cortex.

- Scope `view:public` — discoverable by players outside the current session
- `sys:located_in` link attaches the message to a location atom — design intent is that exploring a place reveals the message
- `sys:speaks` link connects the psyche root — allows tracking which psyche emitted the message

```
# A psyche leaves a cryptic message at a ruin
eng.metaphor target_user_context="meaning of sync ratio" location_id=<ruins_id>
{"status": "metaphor_cast", "msg_id": "k1l2...mn09"}
# → "(A soliloquy hinting at 'meaning of sync ratio', unclear to whom it is addressed)"
#   stored with view:public scope
```

### 3.7 Workflow Example

```
akasha/user $ eng.new name="Pilot-Rei"
{"status": "created", "engram_id": "b2c3...fg05", "name": "Pilot-Rei"}

akasha/user $ eng.talk text="First sync. I feel nothing." mood="dissociative"
{"status": "recorded", "memory_id": "d4e5...hi06", "mood": "dissociative"}

akasha/user $ eng.new name="Pilot-Asuka"
{"engram_id": "f6g7...jk07", ...}

akasha/user $ instance.focus slot=rei   # switch focus back to Rei

akasha/user $ eng.bond target_engram_id=f6g7...jk07 resonance_boost=0.3
{"status": "bonded", "bond_id": "h8i9...lm08", "added_weight": 0.3}

akasha/user $ wd.place name="Area-3 Ruins" place_type="ruin" category="battlefield"
{"place_id": "j0k1...op10", ...}

akasha/user $ eng.metaphor target_user_context="memory of angel contact" location_id=j0k1...op10
{"status": "metaphor_cast", "msg_id": "l2m3...qr11"}
```

---

## 4. Operator — Tactician Model

**File:** `lib/akasha/concepts/operator.py`  
**Prefix:** `operator`  
**CLI prefix:** `op.*`

### 4.1 Design Rationale

Operator is a **stateless** concept model. It carries no `concept_id`, no `INDEX_SET`, and is never registered in the session focus. Instead it executes a combat resolution (Clash) against a Soma atom passed as an argument and writes the result as an event atom in Cortex.

**Savepoint principle applied** — Even in simulation mode, the result is persisted as an event atom in Cortex. Nothing is ever erased. The distinction between live combat and simulation is identified by the `event_type` metadata on the event atom.

**Phase 1 mock evaluation** — The current `_evaluate_tactics` simply returns `tactics_jcl.get("complexity_score", 60)`. Phase 2 will expand to Load/Complexity/Resonance vector scoring.

### 4.2 Cortex Topology

Operator has no root atom of its own. Only the following event atoms are written:

```
AttackerSomaRoot ──sys:simulated──────────▶  SimulationEvent  {event_type: "simulation", success: bool}
AttackerSomaRoot ──sys:involved_in────────▶  CombatEvent      {event_type: "combat_result", success: bool}
AttackerSomaRoot ──sys:state_change:damaged▶ CombatEvent      (on failure only)
```

### 4.3 Kernel Methods

| Method | IAM | Description |
|--------|-----|-------------|
| `operator.clash` | write | Run a combat resolution and record the result as an event |

**`operator.clash` parameters:**

| Field | Type | Description |
|-------|------|-------------|
| `attacker_soma_id` | string | Attacker Soma root ID (required) |
| `defender_id` | string | Target atom ID of the defender (required) |
| `tactics_jcl` | dict | Tactic definition JCL (may include `complexity_score`) |
| `mode` | string | `"simulation"` or `"real"` |

### 4.4 CLI Shorthand Reference

| CLI | Full method | Key args |
|-----|-------------|----------|
| `op.clash` | `operator.clash` | `attacker_soma_id`, `defender_id`, `tactics_jcl`, `mode` |

### 4.5 Clash Modes

| Mode | Damage | Cortex writes | Use case |
|------|--------|---------------|----------|
| `simulation` | None | SimulationEvent atom + `sys:simulated` link | Training / dojo |
| `real` | Yes (on failure: `sys:state_change:damaged` link) | CombatEvent atom + `sys:involved_in` link | Live combat |

Results are persisted as event atoms in both modes (Savepoint principle).

### 4.6 Workflow Example

```
# Define a tactic JCL
tactics = {"name": "Positron Strike", "complexity_score": 75}

# Verify in simulation first
akasha/user $ op.clash attacker_soma_id=<unit01_id> defender_id=<angel_id> \
                       tactics_jcl=tactics mode=simulation
{
  "tactics_used": "Positron Strike",
  "power": 75,
  "success": true,
  "mode": "simulation",
  "note": "Simulation complete. Event logged. No damage taken.",
  "simulation_id": "m3n4...st12"
}

# Deploy for real
akasha/user $ op.clash attacker_soma_id=<unit01_id> defender_id=<angel_id> \
                       tactics_jcl=tactics mode=real
{
  "tactics_used": "Positron Strike",
  "power": 75,
  "success": true,
  "mode": "real",
  "event_id": "n4o5...uv13"
}
```

---

## 5. Eidolon — Spatial Model

**File:** `lib/akasha/concepts/eidolon.py`  
**Prefix:** `eidolon`  
**CLI prefix:** `eid.*`

### 5.1 Design Rationale

Eidolon is Harmonia's dedicated spatial model. It lives in its own namespace, independent of WorldConcept (the general-purpose world model), and carries Harmonia-specific semantics (psyche containers, metaphor triggers, movement constraints). It can optionally be connected to WorldConcept via portals.

Hierarchical topology (`sys:contains` / `sys:located_in`) expresses nested spatial structures, and actor movement is kept consistent by the **Single-Presence Invariant**.

### 5.2 Cortex Topology

```
EidolonRoot  (concept="eidolon", role="root", location_type=...)
  │
  ├─ sys:contains  ──▶  ChildEidolonRoot  (child location)
  └─ (reverse)
      ChildEidolonRoot ──sys:located_in──▶ EidolonRoot

ActorAtom ──sys:located_in──▶ EidolonRoot  (actor's current location)
```

**Set layout:**

| Set | Contents |
|-----|----------|
| `set:eidolon:index` | All Eidolon root atoms (global) |
| `set:eidolon:{id}` | All atoms belonging to this location |
| `set:eidolon:{id}:sub_locations` | Contained child locations |
| `set:eidolon:{id}:occupants` | Actors currently in this location |
| `set:concept:{id}` | Concept-word atoms (empty for now) |

### 5.3 Kernel Methods

| Method | IAM | Description |
|--------|-----|-------------|
| `eidolon.new` | write | Manifest a new spatial location |
| `eidolon.open` | write | Activate an existing location |
| `eidolon.ls` | read | List all locations |
| `eidolon.link` | write | Connect a child location hierarchically |
| `eidolon.move` | write | Move an actor into this location |
| `eidolon.map` | read | Return the topology map of this location |
| `eidolon.rm` | write | Soft-delete the location root |

**`eidolon.new` parameters:**

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Location name (required) |
| `location_type` | string | Type (`world` / `city` / `facility` / `room` / etc.) (required) |

**`eidolon.link` parameters:**

| Field | Type | Description |
|-------|------|-------------|
| `child_location_id` | string | Eidolon root ID of the location to nest (required) |

**`eidolon.move` parameters:**

| Field | Type | Description |
|-------|------|-------------|
| `actor_id` | string | Actor atom ID to move (e.g. a Soma root) (required) |

### 5.4 CLI Shorthand Reference

| CLI | Full method | Key args |
|-----|-------------|----------|
| `eid.new` | `eidolon.new` | `name`, `location_type` |
| `eid.open` | `eidolon.open` | `eidolon_id` |
| `eid.ls` | `eidolon.ls` | — |
| `eid.link` | `eidolon.link` | `child_location_id` |
| `eid.move` | `eidolon.move` | `actor_id` |
| `eid.map` | `eidolon.map` | — |
| `eid.rm` | `eidolon.rm` | — |

### 5.5 Single-Presence Invariant

`eidolon.move` guarantees that an actor **cannot be in more than one location simultaneously**.

Before adding the actor to the new location, all existing `sys:located_in` links are removed and the actor is removed from every previous occupant set:

```
# Before: Unit-01 is in EidolonA
Unit-01 ──sys:located_in──▶ EidolonA
set:eidolon:{A}:occupants = [Unit-01]

# eid.move actor_id=<unit01_id> called on EidolonB
# → removes old link and old set entry
# → adds new link

# After: Unit-01 is in EidolonB only
Unit-01 ──sys:located_in──▶ EidolonB
set:eidolon:{B}:occupants = [Unit-01]
```

### 5.6 Workflow Example

```
# Build the world
akasha/user $ eid.new name="City-3" location_type="city"
{"status": "manifested", "concept_id": "a1b2...ef01", "name": "City-3", "location_type": "city"}

akasha/user $ eid.new name="NERV HQ" location_type="facility"
{"concept_id": "b2c3...fg02", ...}

# Hierarchy: City-3 contains NERV HQ
akasha/user $ eid.open eidolon_id=a1b2...ef01
akasha/user $ eid.link child_location_id=b2c3...fg02
{"status": "linked", "parent": "a1b2...ef01", "child": "b2c3...fg02"}

# Place Unit-01 inside NERV HQ
akasha/user $ eid.open eidolon_id=b2c3...fg02
akasha/user $ eid.move actor_id=<unit01_soma_id>
{"status": "moved", "actor": "...", "destination": "b2c3...fg02"}

# Check topology
akasha/user $ eid.map
{
  "name": "NERV HQ",
  "location_type": "facility",
  "sub_locations": [],
  "occupants": ["<unit01_soma_id>"]
}

# Move Unit-01 to City-3 surface — auto-exits NERV HQ
akasha/user $ eid.open eidolon_id=a1b2...ef01
akasha/user $ eid.move actor_id=<unit01_soma_id>
{"status": "moved", "actor": "...", "destination": "a1b2...ef01"}
# → Unit-01 removed from NERV HQ occupants automatically
```

---

## 6. Integration Patterns

### 6.1 Psyche Transplant

Because Soma and Engram can be mounted independently, transplanting a psyche into a different frame is a pure SessionSpace operation.

```
# Initial state: Rei is piloting Unit-01
instance.mount model=soma   slot=unit   id=<unit01_id>
instance.mount model=engram slot=pilot  id=<rei_id>

# Transplant: put Asuka into the same frame
instance.unmount slot=pilot
instance.mount model=engram slot=pilot id=<asuka_id>

# soma.* still points to the same unit
# engram.* now points to Asuka
```

Rei's Engram remains in Cortex — `instance.unmount` only removes the slot binding; no atoms are deleted.

### 6.2 Lost Experience After Frame Destruction

Even if a frame is destroyed and its Soma removed, the Engram is fully preserved.

```
# Frame destroyed
soma.rm   # → SomaRoot is soft-deleted (subordinate atoms retained in v1)

# The psyche lives on
eng.talk text="I lost the frame. But I'm still here." mood="disoriented"

# Transplant into a new frame
som.new name="Unit-02-Alpha"
instance.unmount slot=unit
instance.mount model=soma slot=unit id=<new_soma_id>

# Resonance bonds carry over — the bond to another psyche is etched in the Engram
```

### 6.3 World × Soma × Engram

Combining WorldConcept places, events, and laws with Soma and Engram enables narrative-driven game state management.

```
# Mount three models in the session
instance.mount model=world  slot=stage  name="City-3"
instance.mount model=soma   slot=unit   name="Unit-01"
instance.mount model=engram slot=pilot  name="Pilot-Rei"

# Record a world event
wd.event description="Angel appears in Area 3" intensity=0.9

# Human judgment: record the psychological impact in the Engram
eng.talk text="It came again." mood="resigned"

# Update the frame's state
som.repair

# Associate everything with an episode via a collection
wd.col label="Episode-01"
wd.put collect_id=<col_id> member_id=<event_id>
wd.put collect_id=<col_id> member_id=<soma_id>
wd.put collect_id=<col_id> member_id=<engram_id>
```

Through the collection atom, all events, frames, and psyches related to a specific episode can be cross-referenced in a single query.

---

*→ Back to [concept-model-spec.md](../concept-model/concept-model-spec.md) · [README](../../README.md)*

---

## 7. SessionSpace

**Source:** `lib/akasha/session/space.py`  
**Session context keys:** `active_space_root`, `space_focus`  
**Cortex atoms owned:** SpaceRoot atom + SlotAtom per mounted instance


### 7.1 Design Rationale

SessionSpace (`lib/akasha/session/space.py`) is **Layer 3** of the architecture — the session instance layer that sits between the kernel and the concept model plugins.

```
Layer 1  Kernel (Cortex · IAM · Sets)
Layer 2  Concept Model Plugins  (stateless dispatchers, mutual isolation)
Layer 3  SessionSpace           (client-owned virtual space of instances)
```

A client's semantic session is a **virtual space**: a Cortex atom that is the root of a set of concept model instances. Any concept model can be mounted into a space — CastConcept, FieldNoteConcept, SynthesisConcept, and future models all use the same `instance.mount` interface. There are no per-model wrapper classes (BotConcept has been removed).

### 7.2 Ownership vs Location

Ownership and physical location are two independent axes:

| Axis | Representation | Meaning |
|------|---------------|---------|
| **Location** | Set membership in `set:space:{id}:slots` | Where the instance lives |
| **Ownership** | Link type from SpaceRoot to SlotAtom | Who controls it |

Link types:

| Link | Meaning |
|------|---------|
| `space:owns` | This space created the instance and controls its lifecycle |
| `space:contains` | This space references an instance owned elsewhere |

A SlotAtom can be a member of multiple spaces simultaneously. Example: a CastConcept instance owned by session A can be borrowed into a StageEncounter space via `instance.join` — it then appears in both `set:space:A:slots` and `set:space:stage:slots`, with different link types expressing the different relationships.

This corresponds directly to the intuition: **your wallet (owned) and a friend's wallet (borrowed) can both be in your bag (the space), but the ownership relation differs**.

### 7.3 Cortex Topology

```
SpaceRoot  (concept="space", role="root", client_id=...)
  │
  ├─ space:owns     ──▶  SlotAtom  {slot, model, concept_id}
  │                          └─ space:instance ──▶  ConceptRoot
  │
  └─ space:contains ──▶  SlotAtom  {slot, model, concept_id}
                             └─ space:instance ──▶  ConceptRoot (owned elsewhere)
```

**Set layout:**

| Set | Contents |
|-----|----------|
| `set:space:index` | All space root atoms (global) |
| `set:space:{id}` | All atoms in this space (root + slots) |
| `set:space:{id}:slots` | Slot atoms only |

**Slot atom metadata:**

| Field | Value |
|-------|-------|
| `type` | `"space_slot"` |
| `concept` | `"space"` |
| `slot` | slot name string (e.g. `"bot"`, `"diary"`) |
| `model` | concept model prefix (e.g. `"cast"`, `"fieldnote"`) |
| `concept_id` | Cortex key of the mounted instance's root atom |

### 7.4 Kernel Methods

| Method | IAM action | Description |
|--------|-----------|-------------|
| `instance.mount` | `write` | Mount a concept model instance (space:owns) |
| `instance.join` | `write` | Borrow an external instance (space:contains) |
| `instance.focus` | `write` | Route a model class's commands to a slot |
| `instance.blur` | `write` | Clear routing focus for a model class |
| `instance.ls` | `read` | List all instances in this space |
| `instance.unmount` | `write` | Remove a slot (instance is not deleted) |

**`instance.mount` parameters:**

| Field | Type | Description |
|-------|------|-------------|
| `model` | string | Concept model prefix (e.g. `"cast"`) |
| `slot` | string | Name for this instance in the space (e.g. `"bot"`) |
| `id` | string | Existing concept_id to mount (omit to create new) |
| `name` | string | Name passed to `op_new` when creating (optional) |

**`instance.join` parameters:**

| Field | Type | Description |
|-------|------|-------------|
| `concept_id` | string | Root atom of the instance to borrow |
| `slot` | string | Name for this slot in the space |
| `model` | string | Model prefix (auto-detected from atom meta if omitted) |

### 7.5 Focus Mechanism

Focus determines which mounted instance handles a model class's commands. It is stored in two places:

1. **`space_focus` session context key** — `dict: model_prefix → slot_name` (routing table)
2. **Each model's own context key** — set as a side effect of `instance.focus`

When `instance.focus slot="bot"` is called:
1. SpaceConcept reads the slot's `model` and `concept_id`.
2. Updates `space_focus["cast"] = "bot"`.
3. Calls `session.set_context("active_cast_root", concept_id)`.

CastConcept continues to read `active_cast_root` from session context, unchanged. SpaceConcept is the authority that sets it — concept models require no modification.

The convention that enables this: every concept model plugin exposes `CONTEXT_KEY_ACTIVE` as a class attribute (defined in `BaseConcept` as `None`; overridden per model). SpaceConcept reads this attribute to know which key to set.

`instance.blur model="cast"` clears both `space_focus["cast"]` and `active_cast_root`.

Auto-focus: when `instance.mount` creates or mounts the first instance of a model class in this space, it automatically focuses it. Subsequent mounts of the same model class do not change focus.

### 7.6 Workflow Examples

**Personal bot (wallet in your own bag):**

```
instance.mount  model=cast  slot=bot  name="aria"
# → SpaceRoot --space:owns--> SlotAtom{slot=bot, model=cast, concept_id=X}
# → auto-focused: active_cast_root = X
# → cast.* commands now target "aria"

cast.identity.set  text="Calm analytical researcher"
cast.trait.set     curiosity=0.9  empathy=0.7
cast.mask.add      presentation="warm and approachable"  audience=public

instance.blur   model=cast       # step out of cast focus
instance.focus  slot=bot         # step back in
instance.unmount slot=bot        # release slot (cast data preserved in Cortex)
```

**Mounting an existing cast:**

```
cast.ls                                       # find existing cast_id
instance.mount  model=cast  slot=bot  id=<cast_id>
```

**Two model classes in one space:**

```
instance.mount  model=cast        slot=bot     name="aria"
instance.mount  model=fieldnote   slot=diary   name="2026 Field Notes"
instance.ls
# → instances: [
#     {slot:"bot",   model:"cast",      focused:true},
#     {slot:"diary", model:"fieldnote", focused:true},
#   ]
# cast.* → bot,  fn.* → diary — independent routing per model class
```

### 7.7 Stage Integration

When multi-client interaction features are implemented, a `StageConcept` (`lib/akasha/session/stage.py`) will manage shared spaces where participants' casts interact.

`instance.join` is the hook for borrowing:

```
# Stage space borrows session A's cast
instance.join  concept_id=<cast_A_id>  slot=participant_0

# Set membership result:
#   set:space:A:slots      → SlotAtom_A     (space:owns)
#   set:space:stage:slots  → SlotAtom_stage (space:contains)
# Both SlotAtoms point to the same ConceptRoot — different ownership, same location data.
```

IAM scopes continue to protect private data: the stage space sees only `audience="public"` mask atoms. Wounds, secrets, policies, and internal rules remain in the owning session's private scope and are never surfaced through `space:contains` references.

---

*New concept model extensions should be added as numbered sections in this document.*

---
