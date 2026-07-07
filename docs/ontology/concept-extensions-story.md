# AKASHA Concept Model Extension Specifications — Story

This document covers the Story concept models: tools for narrative and
character-world modeling.

**Cast** models a character as a cognitive topology — not a flat list of attributes,
but a layered graph of tensions that generates behaviour from the inside out.
It is designed for fiction writing, game design, and any domain where character
motivation, internal contradiction, and narrative arc matter more than surface
statistics.

**World** models the spatial and temporal environment a character inhabits: places,
objects, portals, connections, laws, and the event-sourced history of how the world
changes. It is the outer-environment counterpart to Cast's inner-state model.

Together, Cast and World form the two-sided foundation for fiction world-building:
an agent layer (what characters believe, fear, desire, and do) and a world layer
(where they live, what rules govern that place, and what events alter its state).

All concept models are registered automatically via the **Concept Model Plugin Registry**
(`lib/akasha/concepts/registry.py`). See `docs/concept-model-spec.md §7` for the plugin
authoring guide.

---

## Table of Contents

1. [Cast](#1-cast)
   - [1.1 Design Rationale](#11-design-rationale)
   - [1.2 Cortex Topology](#12-cortex-topology)
   - [1.3 Atom Layer Reference](#13-atom-layer-reference)
   - [1.4 Kernel Methods](#14-kernel-methods)
   - [1.5 CLI Shorthand Reference](#15-cli-shorthand-reference)
   - [1.6 Workflow Example](#16-workflow-example)
   - [1.7 Cross-Concept Application Patterns](#17-cross-concept-application-patterns)
2. [World](#2-world)
   - [2.1 Design Rationale](#21-design-rationale)
   - [2.2 Cortex Topology](#22-cortex-topology)
   - [2.3 Kernel Methods](#23-kernel-methods)
   - [2.4 CLI Shorthand Reference](#24-cli-shorthand-reference)
   - [2.5 Key Design Decisions](#25-key-design-decisions)
   - [2.6 Workflow Example](#26-workflow-example)
   - [2.7 Session Instance Layer Integration](#27-session-instance-layer-integration)

---

## 1. Cast

**Source:** `lib/akasha/concepts/cast.py`  
**Context key:** `active_cast_root`  
**Global index:** `set:cast:index`

### 1.1 Design Rationale

> *A Cast is not a list of attributes. A Cast is a graph of tensions.*

Most character representation systems — RPG sheets, narrative databases, game entity configs — store a character as a flat record of values: strength 12, charisma 8, backstory "grew up in poverty." These attributes are true, but they are inert. They describe the character's surface without explaining the character's *behaviour*.

CastConcept models a character as a **cognitive topology**: a set of layered graph structures that generate behaviour from the inside out. The driving insight is that behaviour emerges from tension — between what a character believes and what they fear, between what they desire and what they allow themselves to want, between the mask they wear and the wound underneath.

The layers are:

| Layer | Subsets | Role |
|---|---|---|
| **Foundation** | identity, appearance, ability, skills, possessions, social_positions | Static attributes — who the character *is* |
| **Behaviour-generating** | emotions, wounds, policies, rules, traits, thresholds, states | Dynamic tensions — what drives the character |
| **Surface** | masks, secrets, outputs | Visible behaviour — what others see |
| **Meta** | contradictions, shadows | Second-order tensions — internal conflicts |
| **Bond** | bonds, bond_updates | Relational tensions — how the character connects to others |
| **Destiny** | fates, callings, roles, myths, arcs | Narrative shape — where the character is going |

The two analysis operators — `cast.diagnose` and `cast.react` — read across all layers to compute emergent behaviour. `diagnose` returns a static pressure score and arc-readiness flags. `react` simulates a real-time response to an external event: it computes event force, checks the reaction threshold, filters perception through the trait vector, and returns the character's output with arc delta suggestions.

CastConcept is designed to be compatible with a future `HumanConcept` for real-person actor analysis, and with game engine event loops via the `cast.react` operator.

### 1.2 Cortex Topology

```
root (cast root atom)
 │
 ├──[sys:top]──► atom₁ ──[sys:next]──► atom₂ ──[sys:next]──► …
 │ └──[sys:bottom]──────────────────────────────────────────►┘
 │
 ├──[cast:has_identity]──► identity atom
 ├──[cast:has_emotion]──► emotion atom
 │     └──[cast:fears]──► (same emotion atom, if verb=fear)
 ├──[cast:has_wound]──► wound atom
 │     └──[cast:haunted_by]──► source event atom (external)
 ├──[cast:has_contradiction]──► contradiction atom
 ├──[cast:has_mask]──► mask atom
 │     └──[cast:presents_as]──► (same mask atom)
 ├──[cast:has_bond]──► bond atom
 │     └──[cast:refers_to]──► target cast root atom
 └──[cast:has_arc]──► arc atom
       └──[cast:resolves_into]──► root (if transformed_state set)
```

**Set namespaces:**

| Set | Contents |
|---|---|
| `set:cast:{root_id}` | All content atoms for this cast |
| `set:cast:{root_id}:{subset}` | Atoms for each layer (e.g. `emotions`, `wounds`, `bonds`) |
| `set:concept:{root_id}` | Concept-word vocabulary atoms |
| `set:cast:index` | All cast root atoms (global, for `cast.ls`) |

**Subsets:** `identity`, `appearance`, `ability`, `adornments`, `skills`, `possessions`, `social_positions`, `emotions`, `wounds`, `policies`, `rules`, `traits`, `thresholds`, `states`, `masks`, `secrets`, `outputs`, `contradictions`, `shadows`, `bonds`, `bond_updates`, `fates`, `callings`, `roles`, `myths`, `arcs`

### 1.3 Atom Layer Reference

**Root atom** (`cast.new`)

| Field | Type | Notes |
|---|---|---|
| `type` | `"concept"` | Required for `op_open` validation |
| `concept` | `"cast"` | Required for `op_open` validation |
| `role` | `"root"` | |
| `name` | str | Display name |
| `identity` | str | Short identity string (optional; full identity via `cast.identity.set`) |
| `created_at` | float | Unix timestamp |

**Trait atom** (`cast.trait.set`) — drives all behaviour simulation

| Field | Type | Range | Notes |
|---|---|---|---|
| `energy` | float | 0–1 | Introvert (0) ↔ Extrovert (1) |
| `process` | float | 0–1 | Intuitive (0) ↔ Logical (1) |
| `response` | float | 0–1 | Impulsive (0) ↔ Cautious (1) |
| `trust` | float | 0–1 | Suspicious (0) ↔ Trusting (1) |
| `flexibility` | float | 0–1 | Rigid (0) ↔ Adaptive (1) |

**Threshold atom** (auto-generated by `cast.trait.set`)

| Field | Notes |
|---|---|
| `reaction` | Capped at 0.9; event force ≥ threshold → direct reaction bypassing perception filter |
| `accumulation_decay` | = `flexibility`; controls how fast accumulated stress dissipates |
| `trust_gate` | = `trust`; used by `cast.react` perception filter |

**Emotion atom** (`cast.emotion.add`)

| Field | Notes |
|---|---|
| `verb` | e.g. `"fear"`, `"love"`, `"desire"` |
| `object` | target of the emotion (stored in meta as `"object"`) |
| `label` | `"{verb}({object})"` |
| `intensity` | 0–1 |

**Wound atom** (`cast.wound.add`)

| Field | Notes |
|---|---|
| `event` | Description of the wounding event |
| `event_id` | Optional atom ID of a source event (e.g. FieldNote observation) |
| `depth` | 0–1; contributes to `diagnose.pressure_score` (× 0.7) |
| `distortion` | Cognitive distortion produced by this wound |

**Bond atom** (`cast.bond.add`)

| Field | Notes |
|---|---|
| `target_id` | Root atom ID of the target cast |
| `types` | List: `"love"`, `"rivalry"`, `"envy"`, `"friendship"`, `"dependency"`, etc. |
| `trust` | 0–1; ≥ 0.7 generates a `cast:trust` link |
| `power` | Signed float; positive = this cast holds power over target |
| `affect` | Signed float; positive = warm affect |
| `dependency` | Non-empty string generates `cast:dependency` link |

**Arc atom** (`cast.arc.add`)

| Field | Notes |
|---|---|
| `arc_type` | `"growth"` / `"fall"` / `"flat"` / `"corruption"` / `"healing"` |
| `initial_state` | Character state at arc start |
| `conflict_state` | State at peak tension |
| `transformed_state` | State at arc resolution (optional; generates `cast:resolves_into` link) |

### 1.4 Kernel Methods

| Method | Op | Action | Key Parameters |
|---|---|---|---|
| `cast.new` | `op_new` | write | `name`, `identity?` |
| `cast.open` | `op_open` | read | `cast_id` (also accepts `id`, `entity_id`) |
| `cast.ls` | `op_list_all` | read | — |
| `cast.map` | `op_map` | read | — |
| `cast.clone` | `op_clone` | write | `name` |
| `cast.rm` | `op_delete` | drop | — |
| `cast.identity.set` | `op_set_identity` | write | `text`, `source_id?`, `evidence?` |
| `cast.appear.set` | `op_set_appearance` | write | `vector` (dict), `note?` |
| `cast.ability.set` | `op_set_ability` | write | `vector` (dict), `note?` |
| `cast.adorn.add` | `op_add_adornment` | write | `item`, `signal?`, `intent?` |
| `cast.skill.add` | `op_add_skill` | write | `name`, `level?` (0–1) |
| `cast.possess.add` | `op_add_possession` | write | `item`, `attachment?`, `emotion?`, `story_flag?` |
| `cast.pos.set` | `op_set_social_position` | write | `position` (dict) |
| `cast.emotion.add` | `op_add_emotion` | write | `verb`, `obj`, `intensity?` |
| `cast.wound.add` | `op_add_wound` | write | `event`, `emotion?`, `depth?`, `distortion?`, `event_id?` |
| `cast.policy.add` | `op_add_policy` | write | `logic`, `emotional_root?`, `pleasure_score?`, `depth?` |
| `cast.rule.add` | `op_add_rule` | write | `text`, `strength?` |
| `cast.trait.set` | `op_set_trait` | write | `trait` (dict) *or* `key`+`value` (partial update) |
| `cast.state.set` | `op_set_state` | write | `state` (dict) |
| `cast.mask.add` | `op_add_mask` | write | `presentation`, `hides?`, `audience?` |
| `cast.secret.add` | `op_add_secret` | write | `content`, `protection?`, `shared_with?`, `revealed_by?` |
| `cast.output.add` | `op_add_output` | write | `modality`, `content`, `valence?`, `leakage?` |
| `cast.conflict.add` | `op_add_contradiction` | write | `a`, `b`, `tension?`, `result?` |
| `cast.shadow.add` | `op_add_shadow` | write | `kind` (suppressed/projected/disowned), `content`, `trigger?`, `source_wound_id?` |
| `cast.bond.add` | `op_add_bond` | write | `target_id`, `types?`, `trust?`, `power?`, `affect?`, `dependency?` |
| `cast.bond.update` | `op_update_bond` | write | `bond_id`, `delta` (dict), `event_id?` |
| `cast.fate.set` | `op_set_fate` | write | `event`, `certainty?`, `awareness?` |
| `cast.calling.set` | `op_set_calling` | write | `mission`, `discovered?`, `alignment?` |
| `cast.role.set` | `op_set_role` | write | `role`, `perspective?`, `source_ontology?` |
| `cast.myth.set` | `op_set_myth` | write | `archetype`, `symbol?`, `resonance?` |
| `cast.arc.add` | `op_add_arc` | write | `arc_type`, `initial_state`, `conflict_state`, `transformed_state?` |
| `cast.react` | `op_react` | read | `event` (dict) *or* `event_id` |
| `cast.diagnose` | `op_diagnose` | read | — |

#### `cast.clone` — deep copy semantics

`cast.clone name="<new_name>"` copies the full cast graph (all 25 subsets) to a new, independently addressable cast root. Because AKASHA uses content-addressed atoms, content atoms are **shared** between source and clone — no data is duplicated at the storage level. Only the new root atom and its outgoing links (root→atom via `SUBSET_TO_RELATION`, plus `sys:top` / `sys:bottom` timeline anchors) are freshly created.

Session focus is restored to the source cast after the operation, so the user's current cast context is not disrupted. The most common use case is snapshotting the active cast before destructive edits:

```
cast.clone  name="aria_v1_backup"
```

**Known v1 limitation:** back-links from atoms to the original root (e.g. `cast:hides` from a mask atom back to the root) continue pointing to the source root. Forward links and set membership are correct.

### 1.5 CLI Shorthand Reference

```
cast.new    name="<name>" [identity="<text>"]
cast.open   cast_id=<id>
cast.ls
cast.clone  name="<new_name>"
cast.rm

cast.identity.set  text="<text>"
cast.trait.set     trait={"response": 0.7, "trust": 0.3}
cast.emotion.add   verb="fear"  obj="<target>"  intensity=0.8
cast.wound.add     event="<desc>"  depth=0.7  distortion="<text>"
cast.policy.add    logic="<text>"  depth=0.6
cast.conflict.add  a="<belief>"  b="<counter>"  tension=0.8
cast.shadow.add    kind="suppressed"  content="<text>"
cast.bond.add      target_id=<id>  types=["love","rivalry"]  trust=0.2

cast.diagnose
cast.react   event={"intensity": 0.8, "frequency": 2, "accumulation": 0.3}
cast.map
```

### 1.6 Workflow Example

Modeling a fictional character with internal contradictions:

```
# 1. Create the cast
cast.new name="Kenji Mori" identity="Middle manager, master of masks"

# 2. Foundation layers
cast.trait.set trait={"response": 0.75, "trust": 0.25, "process": 0.65}
cast.appear.set vector={"height": 0.6, "presence": 0.8, "age": 0.55}
cast.skill.add name="Negotiation" level=0.85
cast.skill.add name="Emotional control" level=0.9

# 3. Behaviour-generating layers
cast.emotion.add verb="fear"   obj="Powerlessness"   intensity=0.85
cast.emotion.add verb="desire" obj="Validation"      intensity=0.75
cast.wound.add event="A childhood of constant rejection by his father" depth=0.8 \
               distortion="Showing emotion is weakness"
cast.policy.add logic="Control everything. Lose control and collapse" depth=0.75
cast.rule.add text="Never express gratitude" strength=0.9

# 4. Surface layers
cast.mask.add presentation="The calm, rational manager" \
             hides="Emotional fear and need for validation"
cast.secret.add content="Secretly envious of subordinates' success" protection=0.9

# 5. Contradictions and shadows
cast.conflict.add a="I am superior to everyone" b="I am not recognized" tension=0.85
cast.shadow.add kind="projected" content="Weakness and dependency" \
               source_wound_id=<wound_id>

# 6. Bonds
cast.bond.add target_id=<colleague_id> types=["rivalry","envy"] \
              trust=0.15 power=0.3 affect=-0.4

# 7. Destiny
cast.calling.set mission="Build genuine connections" discovered=false alignment=0.1
cast.arc.add arc_type="growth" \
             initial_state="The manager who rules through a mask" \
             conflict_state="Loses control, becomes isolated" \
             transformed_state="Accepts vulnerability, learns to trust"

# 8. Diagnose internal tensions
cast.diagnose
# → pressure_score: 3.12, arc_ready: true, calling_unresolved: true

# 9. Simulate reaction to an event
cast.react event={"intensity": 0.7, "frequency": 3, "accumulation": 0.4}
# → threshold_exceeded: false, perceived_event: "Perceived as a logical threat",
#    policy_activated: ["Control everything. Lose control and collapse"],
#    mask_engaged: true
```

### 1.7 Cross-Concept Application Patterns

CastConcept operates independently but connects to the broader AKASHA ecosystem at three points.

---

#### Pattern A: FieldNote (see `concept-extensions-fieldwork.md` §1) → Cast (character observation pipeline)

Qualitative observations about a real or fictional person recorded via FieldNote can be elevated into Cast atoms, preserving the original observation atom as the evidentiary source.

```
[FieldNote (see concept-extensions-fieldwork.md §1)]  ──► [Cast (§1)]
    │                      │
    └─ Observation atom     └─ wound.event_id = observation_id
       "Childhood record"       └─ bond.history = [observation_id]
```

**Workflow:**

1. Record observations via `fn.obs`: `fn.obs text="The relationship with his father was domineering" tag="family"`
2. Open the cast: `cast.open cast_id=<id>`
3. Reference the observation in a wound: `cast.wound.add event="..." event_id=<obs_id>`
4. Reference observation events in bond history: `cast.bond.add ... history=[<obs_id>]`

The `_require_access` guard ensures only accessible observation atoms can be linked. The link `cast:wounded_by` from the wound atom to the source observation creates a traceable evidence chain.

---

#### Pattern B: Cast (§1) → Synthesis (character interpretation pipeline)

Cast analysis results — diagnose outputs and reaction traces — can be elevated as Synthesis sources. This is the key pattern for turning character data into argued interpretations.

```
[Cast (§1)]  ──► [Synthesis (see concept-model-intelligence.md §3)]
    │                  │
    └─ diagnose()       └─ synth.source.add ref_id=<cast_root_id>
    └─ cast root atom   └─ synth.code.add (from contradiction atoms)
                        └─ synth.claim.add "This character is..."
```

**Workflow:**

1. Build the cast fully (traits, wounds, contradictions, arcs).
2. Run `cast.diagnose` to identify high-tension contradictions and arc-readiness.
3. Create a Synthesis: `synth.new title="Kenji Mori — Character Analysis"`
4. Add the cast root as a source: `synth.source.add ref_id=<cast_root_id>`
5. Elevate each high-tension contradiction atom as a Synthesis code:
   `synth.code.add text="Contradiction between need for control and need for validation" ref_id=<contradiction_id>`
6. Build themes and claims from codes via the standard Synthesis pipeline (see `concept-model-intelligence.md` §3).

---

#### Pattern C: Cast (§1) → Presentation (character sheet output)

A CastConcept root can be rendered as a character sheet, relationship map, or narrative brief through PresentationConcept. The presentation holds only the arrangement; all data lives in the Cast graph.

```
[Cast (§1)]  ──► [Presentation (see concept-model-intelligence.md §4)]
    │                   │
    └─ cast root atom    └─ pres.new context_universes=["cast"]
    └─ emotion atoms     └─ Frame "Emotion Map"
    └─ bond atoms             └─ Region "bonds" → pres.node.add ref_id=<bond_id>
    └─ arc atom          └─ Frame "Character Arc"
                              └─ Region "arc" → pres.node.add ref_id=<arc_id>
```

**Workflow:**

1. Call `pres.new title="Kenji Mori — Character Brief" context_universes=["cast"]`.
2. Create a frame per character layer (e.g. "Psychological Profile", "Relationship Map", "Arc").
3. Add regions within each frame; place Cast atom IDs as nodes via `pres.node.add ref_id=<atom_id>`.
4. The renderer fetches atom content on demand — the presentation is always live against the Cast graph.

This pattern is especially useful in game design: the game engine calls `cast.react` to compute runtime behaviour, while the presentation provides a human-readable overview of the character for designers and writers.

---

---

## 2. World

**File:** `lib/akasha/concepts/world.py`  
**Prefix:** `world`  
**CLI prefix:** `wd.*`  
**Version:** 1.0.1

> "A World is a space in which paths can exist."

A topology model for fictional and conceptual worlds. Phase 1 records world state manually — no automatic simulation. Event atoms record change pressure; `place.state` and `law.change` record human-authored consequences.

### 2.1 Design Rationale

WorldConcept is the spatial counterpart to CastConcept. Where Cast models an agent's inner state, World models the outer environment the agent inhabits.

```
Layer 1  Kernel (Cortex · IAM · Sets)
Layer 2  WorldConcept — topology, laws, events, history
              ↕  world:located_at / world:event_at
         CastConcept  — identity, traits, policies, bonds
```

**Phase 1 principle — manual state recording:**  
The author records what changed as a consequence of events. No automatic state propagation happens. The workflow is:

```
world.event "The king died" intensity=0.8         → event_id
world.place.state <castle_id> "succession_crisis" event_id=<event_id>
world.law.change  <law_id>    "destabilized"       event_id=<event_id>
```

**History subset design:**  
`history` intentionally overlaps `events`, `place_states`, and `law_states`. All three are added to `set:world:{id}:history` by their respective operators. This lets `world.diagnose` query a unified change timeline without cross-joining three sets.

### 2.2 Cortex Topology

```
WorldRoot  (concept="world", role="root")
  │
  ├─ sys:contains   ──▶  PlaceAtom    {name, place_type, layers}
  │   │
  │   ├─ sys:contains ──▶  ObjectAtom  {name, attributes}
  │   ├─ sys:contains ──▶  PropAtom    {item, suggests[], minimal}
  │   └─ world:has_portal ──▶  PortalAtom {direction, suggests, connects_to}
  │
  ├─ world:has_connection ──▶  ConnectionAtom {from, to, connection_type, direction}
  ├─ world:has_collection ──▶  CollectionAtom {label, collection_type}
  ├─ world:has_law        ──▶  LawAtom        {law_type, threshold, state}
  │
  ├─ world:has_event       ──▶  EventAtom      {description, force, intensity}
  ├─ world:has_place_state ──▶  PlaceStateAtom {place_id, state, event_id}
  ├─ world:has_law_state   ──▶  LawStateAtom   {law_id, new_state, event_id}
  └─ world:has_history     ──▶  (events + place_states + law_states)
```

**Set layout:**

| Set | Contents |
|-----|----------|
| `set:world:index` | All world root atoms |
| `set:world:{id}` | All content atoms in this world |
| `set:world:{id}:places` | Place atoms |
| `set:world:{id}:objects` | Object atoms |
| `set:world:{id}:props` | Prop atoms |
| `set:world:{id}:suggesters` | Props + Portals (dual membership) |
| `set:world:{id}:connections` | Connection atoms |
| `set:world:{id}:portals` | Portal atoms |
| `set:world:{id}:collections` | Collection atoms |
| `set:world:{id}:laws` | Law atoms |
| `set:world:{id}:place_states` | Place state change records |
| `set:world:{id}:law_states` | Law state change records |
| `set:world:{id}:events` | Event atoms |
| `set:world:{id}:history` | Events + place_states + law_states (unified) |
| `set:world:{id}:hidden` | Hidden layer atoms |
| `set:concept:{id}` | Concept-word atoms for this world |

### 2.3 Kernel Methods

| Method | IAM | Description |
|--------|-----|-------------|
| `world.new` | write | Create a new world |
| `world.open` | read | Open an existing world |
| `world.ls` | read | List all worlds |
| `world.map` | read | Full topology snapshot |
| `world.rm` | drop | Delete world root (shallow — subordinates not removed) |
| `world.place.add` | write | Add a place |
| `world.place.state` | write | Record a place state change (event-sourced) |
| `world.object.add` | write | Add an object to a place |
| `world.prop.add` | write | Add a prop / suggester to a place |
| `world.collect.add` | write | Create a collection |
| `world.collect.put` | write | Add any accessible atom to a collection |
| `world.connect` | write | Connect two places (structural, not temporal) |
| `world.portal.add` | write | Add a portal to a place |
| `world.law.add` | write | Add a law |
| `world.law.change` | write | Record a law state change (event-sourced) |
| `world.hidden.add` | write | Add a hidden layer element |
| `world.event` | write | Record a world event |
| `world.diagnose` | read | Diagnose tensions in the world |

### 2.4 CLI Shorthand Reference

| CLI | Full method | Key args |
|-----|-------------|----------|
| `wd.new` | `world.new` | `title`, `description`, `time_type` |
| `wd.open` | `world.open` | `world_id` |
| `wd.ls` | `world.ls` | — |
| `wd.map` | `world.map` | — |
| `wd.rm` | `world.rm` | — |
| `wd.place` | `world.place.add` | `name`, `place_type`, `category` |
| `wd.state` | `world.place.state` | `place_id`, `state`, `event_id?` |
| `wd.obj` | `world.object.add` | `place_id`, `name` |
| `wd.prop` | `world.prop.add` | `place_id`, `item`, `suggests?` |
| `wd.col` | `world.collect.add` | `label`, `collection_type` |
| `wd.put` | `world.collect.put` | `collect_id`, `member_id` |
| `wd.link` | `world.connect` | `from_id`, `to_id`, `connection_type` |
| `wd.portal` | `world.portal.add` | `place_id`, `direction` |
| `wd.law` | `world.law.add` | `law_type`, `content` |
| `wd.amend` | `world.law.change` | `law_id`, `new_state`, `event_id?` |
| `wd.hide` | `world.hidden.add` | `hint`, `confidence?` |
| `wd.event` | `world.event` | `description`, `intensity` |
| `wd.dx` | `world.diagnose` | `limit?` |

### 2.5 Key Design Decisions

**`suggests` as plain metadata (not concept_word atoms):**  
Prop and Portal `suggests` values are stored as plain strings in atom metadata. Registering them as concept_words would create alias collisions with vocabulary shared by other concept models (e.g., `concept:word:village` would conflict if FieldNote also defines a "village" concept). The `sys:derived_from` link pattern is used only for structural roles (place, object, law, event) that are specific to WorldConcept.

**Connections and Collections are structural (timeline=False):**  
`world.connect` and `world.collect.add` do not append to the temporal timeline. They express topology (the graph of the world), not events in the world's history. All other atom types are temporal by default.

**Cross-concept collection membership:**  
`world.collect.put` accepts any accessible atom as a `member_id`, including atoms from CastConcept or other concept models. Access is checked via IAM scopes at the time of the call. Cross-session sharing requires explicit scope grants at atom creation time.

**Law state change is event-sourced:**  
`world.law.change` does not mutate the original law atom. It appends a `law_state` atom, preserving the full history of law changes for audit and rollback.

**Law types and thresholds:**

| Type | Default threshold | Meaning |
|------|------------------|---------|
| `physical` | 0.99 | Near-unbreakable (gravity, thermodynamics) |
| `narrative` | 0.90 | Strong story logic (cause → consequence) |
| `social` | 0.70 | Social norms and institutions |
| `special` | 0.50 | Magic systems, special rules |
| `belief` | 0.30 | Shared beliefs, easily shifted |

**Hidden Layer:**  
Hidden atoms are intentionally not Places. They represent undetermined zones hinted at but not yet materialised in the fiction. When discovered (via Cast Policy or story event), the author creates a real Place via `world.place.add` and links it to the hidden atom.

### 2.6 Workflow Example

```
akasha/user $ wd.new title="Aratana Sekai" description="Post-collapse world"
{"status": "created", "world_id": "a1b2...ef01", "title": "Aratana Sekai"}

akasha/user $ wd.place name="废都 Fenix" place_type="ruin" category="city"
{"status": "place_added", "place_id": "c3d4...ab02", "name": "废都 Fenix"}

akasha/user $ wd.law law_type="social" content="Water is currency"
{"status": "law_added", "law_id": "e5f6...cd03", "law_type": "social", "threshold": 0.7}

akasha/user $ wd.event description="Dam collapsed" intensity=0.9 place_id=c3d4...ab02
{
  "status": "event_recorded",
  "event_id": "f7a8...de04",
  "force": 0.95,
  "manual_next_steps": [
    "world.place.state <place_id> <state> event_id=<event_id>",
    "world.law.change  <law_id>   <new_state> event_id=<event_id>"
  ]
}

akasha/user $ wd.state place_id=c3d4...ab02 state="flooded" event_id=f7a8...de04
{"status": "place_state_set", "place_id": "c3d4...ab02", "state": "flooded"}

akasha/user $ wd.amend law_id=e5f6...cd03 new_state="destabilized" event_id=f7a8...de04
{"status": "law_changed", "law_id": "e5f6...cd03", "new_state": "destabilized"}

akasha/user $ wd.dx
{
  "counts": {"places": 1, "laws": 1, "events": 1, ...},
  "diagnosis": {
    "high_force_events": [{"id": "f7a8...de04", "meta": {"force": 0.95}}],
    "unstable_laws":     [{"id": "...", "meta": {"new_state": "destabilized"}}],
    ...
  }
}
```

### 2.7 Session Instance Layer Integration

WorldConcept fully supports `instance.mount`:

```
akasha/user $ instance.mount model=world slot=fiction name="Aratana Sekai"
# → world.* commands route to "Aratana Sekai"
# → active_world_root set in session context

akasha/user $ instance.mount model=world slot=stage name="Arena"
# → second world mounted; fiction still focused (auto-focus only on first)

akasha/user $ instance.focus slot=stage
# → world.* commands now route to "Arena"
```

`CONTEXT_KEY_ACTIVE = "active_world_root"` is exposed as both a module constant and a class attribute, enabling SpaceConcept's focus mechanism without any modification to WorldConcept itself.

---
