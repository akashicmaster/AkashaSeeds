# AKASHA — Foundational Design Context

*Integrated full text: the 2 October 2026 canonical document with A34 and A35 (11 October 2026) appended.*

> Provenance note. The body through A33 is reconstructed from the maintainer's supplied PDF of the 2 October 2026 canonical document; its wording is the maintainer's, and where this reconstruction's formatting differs from that source, the source governs. A34 and A35 are the newly authored additions (the readable account is White Paper Chapter 18). This file is a single full assembly for embedding; reconcile the body's formatting against the canonical source before it becomes canon.

---

Akasha — Foundational Design Context

Status: Living architectural context / Quelle reference

Purpose: Preserve the foundational design intent of Akasha independently of any single implementation phase, so that future

design discussions can distinguish original architectural principles from implementation discoveries and engineering

history.

Revised 26 September 2026: Part II gains A24 (observation, evaluation and intervention), A25 (workbench

templates, Model Observatory, Model Trainer), A26 (ID sets and one gate), A27 (operation profiles), A28 (status)

and A29 (reserved concept models).

Revised 27 September 2026: Part II gains A30 (reusable workbench templates: the runtime as a platform primitive,

template definitions as application resources, the instance as a pinned branch, general concept models and their

promotion path, and the rule that a citation is an input). A25 and A29 gain pointers to it.

Revised 2 October 2026: Part II gains A31 (participants and source-mappable operands: participation as a binding,

the typed result, the bidirectional mapping, the reserved model effect) and A32 (status and the next release). A29's

reserved set gains effect and studio. A33 (kernel, drivers and plugins: the invariant compiled kernel between

applications above and environment-specific drivers below).

0. How to Read This Document

Akasha has accumulated many implementations, experiments, names, and subsystems. Some of them appeared recently; the

underlying ideas often did not.

A central rule for reading the project history is:

Do not mistake implementation chronology for conceptual chronology.

Many of Akasha's foundational ideas predate the current codebase by roughly thirty years, originating in the author's work and

thinking as a knowledge engineer around Lisp, Prolog, semantic networks, knowledge representation, and concept modeling.

The 2026 implementation history is therefore not primarily a story of repeatedly changing the fundamental design. It is a story

of finding practical implementation boundaries for ideas that had remained dormant until contemporary hardware, software,

LLMs, networking, and deployment environments made them feasible.

A useful summary is:

The concepts were old. The implementation had to catch up.

This distinction is essential when interpreting Silica, Seeds, Society, Telemetry, Workflow, World, Workbench, DTN, semantic

caching, or LLM integration.

1. Foundational Thesis

Akasha is a local-first Concept Operating System and semantic substrate.

Its purpose is not merely to store data, documents, triples, or ontology statements. It is intended to provide a computational

environment in which:

concepts can exist as first-class structures,

multiple interpretations can coexist,

humans and machines can inhabit the same semantic world,

observations can enter that world dynamically,

actions and workflows can change it,

knowledge and executable process can travel together,

execution can continue under degraded or disconnected conditions,

and the same semantic boundaries can inform computation from local memory operations to distributed placement.

Akasha should therefore not be reduced to:

a graph database,

an ontology engine,

a vector database,

an LLM memory layer,

an agent framework,

a workflow engine,

an IoT platform,

or a distributed database.

It can support aspects of all of these because they are projections of a deeper substrate.

2. The Primitive Substrate: Atom, Link, Set

The fundamental substrate is intentionally small:

Atom

Link

Set

Everything above this level should be understood as a semantic construction over these primitives.

2.1 Atom

An Atom is the fundamental addressable/persistent unit.

An Atom may participate in representing:

a concept,

a note,

a quotation,

a source fragment,

an observation,

a person,

an event,

a sensor endpoint,

an actuator endpoint,

a workflow state,

a role,

a world-state element,

or another semantic object.

The kernel does not require a different storage species for each domain.

The same primitive can therefore participate in both apparently "static" knowledge and dynamic processes.

This is deliberate.

2.2 Link

Links connect Atoms and make topology meaningful.

Meaning is not assumed to reside only in the payload of an Atom. It also emerges from relationships, context, participation,

and projection.

The same Atom can therefore mean differently when reached through different structures.

2.3 Set

Set is one of the most important primitives in Akasha.

A Set is not necessarily:

a class,

a strict taxonomy,

a database table,

a folder,

or a mutually exclusive category.

Sets may overlap.

A Set may represent:

a domain,

an interpretation,

a hypothesis,

a semantic neighborhood,

a professional rule-space,

a permission boundary,

an execution boundary,

a distribution unit,

a memory-residency unit,

a placement unit,

or a temporary working context.

This allows multiple interpretations to coexist without forcing them into one canonical ontology.

For example, an apple can simultaneously participate in:

a biological Set,

a food Set,

a Biblical-symbolic Set,

a literary Set,

a commercial/technology Set.

Akasha does not need to decide which is the one true hierarchy.

3. Scope and Set: One Internal Geometry

At the API and explanatory level, Akasha may distinguish Scope and Set because they communicate different intentions.

Internally, however, the important design insight is:

Scope and Set share the same Atom-Set geometry.

A Scope is therefore not merely a conventional ACL wrapper around otherwise globally visible objects.

It can be understood as a projection of a semantic Set into a client's accessible world.

This produces a different security intuition from conventional systems.

Traditional access:

object exists

    ↓

ACL check

    ↓

allow / deny

Akasha projection:

client scope

    ↓

semantic projection

    ↓

object is present in this world

or

object is not projected at all

A private semantic region can therefore behave like a black hole from the perspective of an unrelated client: it is not merely

visible-but-denied; it is absent from that client's projected world.

Directional references are possible. A private Set may refer to public knowledge without requiring public knowledge to refer

back into the private Set.

This is important for:

private annotation of public sources,

personal extensions of public knowledge,

research isolation,

organizational boundaries,

and secure semantic composition.

4. Concept: Deduction and Function

Akasha was not designed merely to store definitions of concepts.

A Concept must be approachable from more than one direction.

One important distinction is between:

Deductive / definitional view

Concept Model

     ↓

defined semantic structure

     ↓

Atoms / Links / Sets

This supports deliberate modeling: a human can state what a concept is intended to mean and how it should be structured.

Functional / observational / inductive view

Atoms / observations / relations

          ↓

co-occurrence and use

          ↓

candidate structures

          ↓

possible Sets / concepts

This allows concepts to be discovered through how they participate in the world rather than only through prior definition.

Neither side replaces the other.

Akasha is intended to support movement between:

definition ↔ observation

deduction ↔ induction

model ↔ use

A candidate Set discovered inductively does not automatically become canonical truth. It can coexist with other hypotheses

until humans or agents refine, name, compare, or reject it.

This is one reason Akasha should not converge automatically toward a single universal ontology.

5. dive: Exploration Without Destroying Ambiguity

The dive concept follows directly from overlapping Sets.

Graph traversal often assumes that useful exploration means:

following explicit edges,

selecting a hierarchy,

finding shortest paths,

or choosing a canonical neighborhood.

Akasha's semantic exploration must not destroy the looseness of meaning merely to make navigation convenient.

For a concept such as apple, exploration may encounter overlapping neighborhoods without first forcing the user to choose

one ontology.

Apple

 ├─ Biology

 ├─ Food

 ├─ Religion

 ├─ Literature

 ├─ Technology

 └─ other interpretations

dive is therefore better understood as movement through a sea of meanings than as ordinary tree navigation.

6. From Loose Meaning to Strict Domains

Akasha does not treat ambiguity and rigor as separate architectures.

A strict professional domain is a special case of Set interpretation in which constraints become strong.

For example:

loose semantic world

        ↓

overlapping concepts

        ↓

Sets

        ↓

constrained Sets

        ↓

professional domain

Accounting, audit, compliance, engineering rules, or other professional systems can therefore be expressed without replacing

the underlying semantic model.

Strictness is added through:

constraints,

rules,

authority,

roles,

validation,

evidence requirements,

and permitted operations.

This supports an important architectural principle:

A human begins in an ambiguous world and learns rules. Akasha should be able to do the same without

changing substrates.

7. Norms, Audit, Authority, and Roles

Because Sets can carry constraints and interpretation, normative systems can also be represented semantically.

A normative Set may express:

what is permitted,

what is forbidden,

what is required,

exceptions,

professional standards,

ethical rules,

audit criteria,

or domain-specific authority.

An auditor is not fundamentally a special executable type.

An auditor can be modeled as an Agent connected to:

an audit role,

an authority/permission Set,

relevant knowledge Sets,

evidence,

and operations.

The same architecture can apply whether the Agent is:

human,

LLM,

programmatic,

robotic,

or another machine participant.

Authority and interpretive truth must not be conflated.

A moderator may control process without becoming epistemic ground truth.

8. Multi-Client Is Foundational

Akasha was designed as a multi-client semantic environment.

Possible clients include:

CLI users,

browser interfaces,

mobile applications,

human participants,

LLMs,

sensors,

actuators,

robotic controllers,

automated programs.

A client participates through semantic session/scope mechanisms rather than receiving a fundamentally different ontology

depending on its species.

This becomes especially important for LLMs.

9. LLMs as First-Class Clients, Not Magical Exceptions

LLM participation was not intended to create a separate "AI world."

The fundamental design is:

An LLM is one client and may become one Agent in the same world as other participants.

It should not be privileged simply because it is an LLM.

Nor should it be treated merely as:

a chat window,

a tool-calling controller,

an omniscient narrator,

or a free-running autonomous process.

The Station experiment explored an intermediate and more useful model.

LLMs played roles such as:

news caster,

commentator / tsukkomi role.

The goal was not unrestricted conversation and not rigid script playback.

The goal was to test how an LLM could participate as a member of a Society, with role, context, turn structure, and social

relation influencing behavior.

This experiment forms a practical foundation for LLM participation in the newer World / Society / Workbench architecture.

Station itself is expected to be absorbed into or unified with Workbench rather than remain a separate conceptual island.

10. Telemetry: The Semantic World Is Dynamic

Atom was designed from the beginning with the intention that the semantic substrate could map to a dynamic physical world.

In particular, sensor and actuator integration was not an afterthought.

The telemetry experiment tested this design directly:

physical world

      ↓

telemetry

      ↓

observation

      ↓

Atom mapping

      ↓

semantic world

This demonstrates a crucial difference from a purely static ontology or conventional graph database.

An ontology can define concepts such as:

temperature,

sensor,

position,

pressure,

device.

Akasha is intended to let actual observations enter the same semantic world over time.

Thus the World is not merely described.

It changes.

The reverse direction matters equally:

Akasha semantic state

       ↓

Workflow / decision

       ↓

Actuator mapping

       ↓

physical world

Sensor and actuator mapping therefore make the semantic world bidirectional.

11. World: A Place Where Meaning, State, Agents, and Time Meet

The World model existed conceptually before its recent implementation work.

The current reconstruction is not a newly invented direction. It is the point at which implementation has finally caught up with

the original design sufficiently to make the World practical.

A World can contain or coordinate:

Concepts,

Sources,

Agents,

Roles,

Societies,

Workbenches,

Workflows,

observations,

state changes,

Chronons,

Projections.

The transition now occurring in Akasha can be summarized as:

Earlier implementation focus:

"How can a semantic substrate be made real and robust?"

Current focus:

"Now that the substrate exists, what semantic worlds can live on it?"

12. Source and Source Viewer

A semantic system must distinguish source material from interpretation.

Source infrastructure exists to preserve this boundary.

A Source may represent acquired material such as:

papers,

documents,

observations,

external data,

frozen acquisition frames,

other evidence.

The Source Viewer exposes source material and provenance without silently converting interpretation into source fact.

Conceptually:

Source

  ↓

Source Viewer

  ↓

observation / selection / reference

  ↓

Workbench

  ↓

interpretation

This is especially important for research.

A shared Source does not imply a shared Reading.

Multiple Agents can encounter the same Source and form independent interpretations.

13. Labo

Concept Labo is the research-oriented environment built on the semantic substrate.

Its purpose is not to impose one interpretation.

It provides a bounded research namespace in which Sources, Concepts, interpretations, comparisons, and histories can

coexist.

Important principles include:

interpretation is plural,

provenance matters,

history should not be silently overwritten,

views should reference rather than unnecessarily copy,

research state and public presentation should remain distinguishable.

Labo is one important bridge between the foundational substrate and real intellectual work.

14. Workbench: Where an Agent Actually Works

Workbench is central to the new practical World model.

A useful definition is:

A Workbench is the place where an Agent works within a particular world, time, role, and set of tools.

Workbench is not a domain application.

The same conceptual machinery should support very different activities, for example:

machine learning over a plant world,

an academic seminar,

field research,

LLM collaboration,

audit,

accounting,

engineering.

The domain emerges from composition of semantic primitives and projections, not from a new backend for every use case.

A Workbench may coordinate:

Source access,

available operations,

role-specific controls,

current Workflow,

current Chronon,

Society membership,

private and shared semantic spaces,

public Projection.

15. Workflow Is Part of Memory

Workflow is another foundational idea that predates the current implementation.

In conventional architectures, knowledge and workflow are often separated:

knowledge database

      ↓ reference

workflow engine

      ↓

execution

Akasha takes a different approach.

The Workflow itself lives on the Atom network.

Atom network

 ├─ concepts

 ├─ world state

 ├─ workflow structure

 └─ execution state

Therefore:

a Workflow can be remembered,

execution state can be remembered,

execution can be resumed,

state can be rolled back,

revisions can be preserved,

execution can be transported,

an Agent can potentially construct or modify a Workflow.

This is another demonstration that Akasha's memory is dynamic.

Memory does not only remember what is known.

It can remember how to act and where an action currently is.

A useful formulation is:

Programming can become a form of remembering how to act.

16. Rollback, Revision, and Temporal Continuity

Because Workflow and state participate in the same semantic substrate, rollback is not merely a database recovery trick.

It is part of semantic temporal continuity.

The system should be able to preserve:

previous interpretations,

previous workflow states,

earlier readings,

intermediate execution states,

revisions,

failures and recoveries.

This matters for both machines and humans.

In a research seminar, a revised interpretation should not erase the student's earlier reading.

In an automated process, a corrected workflow should not require pretending the earlier execution never happened.

History itself is knowledge.

17. Chronon

Chronon provides a temporal/process dimension to the World.

It can be used to distinguish:

phases,

moments,

revisions,

visibility changes,

workflow transitions,

historical states.

Chronon becomes especially powerful when combined with Projection and Role.

Chronon × Projection × Role

          ↓

what this Agent can see and do now

This avoids hard-coding every activity as a separate application mode.

18. Society

Society represents structured coexistence among Agents.

It is deliberately broader than "multi-agent chat."

A Society may contain:

humans,

LLMs,

automated programs,

observers,

moderators,

participants,

other Agents.

Society supplies social structure without requiring either:

unrestricted autonomous behavior,

or rigid scripted behavior.

Roles, relationships, Workflow, Workbench, and current World state shape what participation means.

A future Organization can impose stricter rules where Society represents looser social coordination.

19. Projection

Projection determines what part or interpretation of the semantic world is exposed.

Projection is used for more than visualization.

It can participate in:

access,

research isolation,

phase-specific visibility,

public/private boundaries,

role-specific interfaces,

presentation,

external publication.

This supports an important separation:

Workbench

   │

   ├─ private research activity

   ├─ participant views

   ├─ Public Projection

   └─ Broadcaster / reporting Agent

Public Projection and broadcasting are not the same operation.

Research can remain closed while selected results are projected publicly.

20. Radu Seminar as a Human Workbench Use Case

A planned public seminar with Radu provides a concrete human research use case.

The initial research material includes two Di Paolo papers. Radu is first reading and annotating them naturally, without being

forced into an Akasha-specific annotation schema.

This is intentional.

The researcher's actual intellectual practice should inform the Workbench projection; the researcher should not be forced to

adapt to a premature UI ontology.

A likely seminar flow is:

shared Source

    ↓

independent reading

    ↓

private annotation

    ↓

submit

    ↓

comparison opens

    ↓

seminar discussion

    ↓

revision

    ↓

preserve old + revised readings

    ↓

optional public projection

Radu's reading is not Ground Truth.

It is an instructor/moderator reading among other readings.

Moderator authority governs process; it does not define interpretive truth.

This use case is expected to follow the PLANTS validation of the new World / Workbench architecture.

21. PLANTS as the First Practical World/Workbench Validation

PLANTS is the first practical implementation centered on the reconstructed World model and Workbench architecture.

Its importance is not merely that it concerns plants or machine learning.

It tests whether a machine can perform substantial work inside the same semantic World architecture intended for other

Agents.

If PLANTS succeeds and the Radu seminar follows on the same substrate, Akasha will have demonstrated two very different

activities without building two unrelated application backends:

PLANTS

machine works in a semantic world

Radu seminar

humans work in a semantic world

The difference is largely in:

Sources,

Agents,

Roles,

Workflows,

Projections,

and tools.

The substrate remains the same.

22. Harmonia: Execution Above Storage

Akasha deliberately avoids making database-specific concurrency behavior the conceptual center of execution.

Harmonia coordinates work above the storage engine.

This permits the system to reason in Akasha-native units rather than forcing the architecture to inherit SQL locking or another

backend's execution model.

Jobs can be reasoned about through semantic read/write Sets.

If two operations are semantically disjoint, their Set relationships can inform parallel execution.

This opens a path toward:

deterministic orchestration,

backend independence,

semantic parallelization,

distributed execution,

resumable jobs,

and workload placement.

23. Silica: The Native Semantic Instruction Boundary

Silica should not be understood merely as a reaction against SQLite.

SQLite is a strong and valuable implementation.

Silica exists because Akasha has long carried another design idea: knowledge operations should eventually be expressible at a

boundary analogous to a native CPU instruction set.

This idea dates back to experience with Lisp and Prolog, when machines such as Symbolics demonstrated specialized

computing but at prohibitive cost.

Modern fabless hardware development, FPGA/RISC-V ecosystems, and lower chip-design barriers make the idea less

fantastical than it once was.

The immediate goal is not to fabricate a chip.

The architectural goal is to establish a software boundary that could plausibly correspond to native semantic instructions later.

Akasha semantic operation

        ↓

--------------------------------

Silica / backend instruction boundary

--------------------------------

        ↓

current software implementation

possible future:

native semantic hardware

An Akasha memory operation that might require multiple database transactions or commits can therefore become one Akasha-

native command.

The important question is not merely performance.

It is:

What is one meaningful memory instruction for Akasha?

The SQLite and Silica implementations intentionally share the same upper interface boundary so that the memory engine can

be replaced without rewriting the semantic layers above it.

24. Micro Semantics and Macro Distribution

A key architectural consequence of the native instruction boundary is that the same semantic judgment can scale upward.

At the micro level:

semantic operation

    ↓

native command

    ↓

memory / WAL / execution

At the macro level:

semantic Set / working context

    ↓

residency / placement

    ↓

cache / node / distribution

The unifying principle is:

The semantic boundary that determines what belongs together in a small operation can also help determine

what belongs together in memory or across machines.

This idea is central to the semantic macro-cache.

A conventional cache primarily remembers addresses or recently accessed blocks.

A semantic macro-cache can reason about what the system is currently working on and keep semantically relevant regions

resident.

Thus micro-level semantic operations and macro-level distribution are not unrelated optimizations. They are two scales of the

same design idea.

25. Semantic Macro-Cache

The semantic macro-cache asks:

Can memory residency follow semantic attention?

This includes not only what a human reader is viewing, but also what the system is actively working on.

Sets can therefore become natural units for:

warming,

paging,

placement,

distribution,

synchronization,

and eviction.

For example, entering a Europe-related research context may make geography, countries, capitals, and relevant history

semantically hot while unrelated biology Sets become cold.

The goal is not merely faster lookup.

It is alignment between:

meaning

  ↓

attention

  ↓

memory residency

  ↓

execution placement

26. Knowledge Portability

Because concepts, Sets, Workflow, and execution state all belong to the semantic substrate, Akasha's notion of portability is

stronger than "copy the database."

A portable unit may include:

relevant knowledge,

interpretation,

rules,

Workflow,

execution state,

permissions/scopes,

and required semantic context.

Conceptually:

Node A

 ├─ knowledge Sets

 ├─ Workflow

 └─ state

       │

       │ transport

       ▼

Node B

 ├─ knowledge Sets

 ├─ Workflow

 └─ state

       ↓

    continue

This is foundational to distributed and constrained operation.

27. DTN: Delay Is Not Failure

Akasha's distributed model is compatible with Delay/Disruption Tolerant Networking thinking.

The system should not assume:

permanent connectivity,

low latency,

a continuously reachable central server,

or unlimited local resources.

If a node possesses the relevant semantic Sets and Workflow, it may continue useful work while disconnected.

Results can synchronize later.

Thus:

Network delay should not imply loss of semantic work.

This is particularly important for:

field systems,

IoT networks,

mobile devices,

remote environments,

intermittent links,

autonomous machines.

28. IoT and Semantic Distribution

In an IoT environment, every device does not need the entire Akasha world.

A device can receive the semantic region and Workflow relevant to its role.

                 Akasha World

                      │

             semantic placement

          ┌───────────┼───────────┐

          ↓           ↓           ↓

       Sensor A    Edge Node B   Actuator C

        Set α        Set β         Set γ

       Workflow     Workflow      Workflow

This connects:

Sets,

Scope,

semantic macro-cache,

Workflow,

DTN,

telemetry,

sensor/actuator mapping,

and degraded execution.

Knowledge distribution is therefore semantic rather than merely block- or table-oriented.

29. Self-Programming Agents

Because Workflow itself is represented on the Atom network, an Agent can in principle reason about and modify executable

process semantically.

A possible loop is:

observe

   ↓

reason

   ↓

construct / modify Workflow

   ↓

execute

   ↓

observe result

   ↓

revise or rollback

This is different from defining self-programming only as "an LLM writes source code and executes it."

An Agent may instead acquire a new way of acting by constructing a new remembered Workflow.

Because Workflow history and rollback can be preserved, the substrate also provides a basis for controlled self-modification.

This is a foundation, not a claim that unrestricted self-programming has already been solved.

30. Seeds: Deployment as Germination

The name Seeds is architectural, not decorative.

A Seed is intended to behave analogically like a dormant biological seed:

Seed

  ↓

arrives in an environment

  ↓

observes available conditions

  ↓

adapts

  ↓

germinates

  ↓

Akasha instance

The important question is not:

"What does this environment lack?"

but:

"What can Akasha do in this environment?"

A rich environment may permit a large deployment.

A constrained environment may permit only a smaller form.

The semantic identity and continuity should survive capability reduction.

31. Retreat / Degradation Strategy

Akasha's ability to run in local or constrained environments is not explained by local-first alone.

A deeper requirement is that knowledge and work must be able to travel to places where:

compute is limited,

services are missing,

connectivity is intermittent,

process models differ,

or only a subset of capabilities is available.

The system therefore needs a retreat/degradation strategy.

Conceptually:

full environment

      ↓ unavailable

reduced runtime

      ↓

fewer capabilities

      ↓

local execution

      ↓

delayed communication

      ↓

semantic continuity remains

A concise principle is:

Capabilities may retreat; semantic continuity should not.

This is why lightweight/local deployment, DTN, portable Workflow, Set placement, and Seeds belong to the same design

family.

32. Akasha Itself as a Seed

There is also a historical analogy.

The foundational design spent roughly thirty years dormant.

The environment changed:

hardware became cheaper,

general compute became abundant,

LLMs appeared as unusually capable semantic clients,

chip design became more accessible,

fabless development became normal,

open ISAs and FPGA prototyping lowered experimentation barriers,

local/mobile devices became powerful,

distributed systems became commonplace.

The old design encountered a new environment and became implementable.

In that sense:

Akasha itself was a seed.

This is not merely literary branding. It mirrors the project's actual relationship between dormant architecture and

environmental opportunity.

33. The Four Long-Lived Design Axes

The foundational design can be summarized through four interdependent axes.

33.1 Concept

Meaning should exist independently of implementation-specific representations.

Concepts should be able to be:

defined,

observed,

compared,

reinterpreted,

connected,

projected,

and revised.

33.2 World

Humans, machines, sensors, actuators, observations, roles, and state should be able to inhabit one semantic world without

requiring separate ontological universes.

33.3 Semantic Machine

Knowledge operations should have Akasha-native computational boundaries.

Those boundaries should remain meaningful from:

memory operation,

to cache,

to parallelization,

to distributed placement,

and potentially to hardware instruction.

33.4 Workflow

Knowledge and executable process should share the same memory substrate.

Work should therefore be:

remembered,

resumed,

rolled back,

transported,

delayed,

distributed,

and potentially rewritten by Agents.

These four axes are not independent features. Together they describe the intended computational environment.

34. A Unified View

A compact conceptual map is:

                       WORLD

                         │

          ┌──────────────┼──────────────┐

          │              │              │

       Sources         Agents       Telemetry

          │              │              │

          ↓              ↓              ↓

       Concept        Society       Observation

          │              │              │

          └────────── Workbench ─────────┘

                         │

                      Workflow

                         │

                      Chronon

                         │

                    Atom / Link / Set

                         │

                 semantic operations

                         │

                  Harmonia / engine

                         │

              SQLite  ↔  Silica

                         │

          semantic instruction boundary

                         │

                 possible hardware

Meanwhile, across the same structure:

Set / Scope

    ↓

Projection

    ↓

memory residency

    ↓

placement

    ↓

distribution

    ↓

DTN / constrained execution

This is why Akasha should not be described as a stack of unrelated features.

The same semantic primitives recur at multiple scales.

35. Current Development Phase

The foundational substrate is now substantially implemented.

Important completed or strongly established areas include:

Atom/Link/Set substrate,

Concept mechanisms,

deductive and functional/observational views,

multi-client service,

Scope/session architecture,

persistence,

Harmonia execution,

SQLite-backed operation,

Silica native-engine experimentation,

robustness and load testing on VPS,

LLM participation experiments through Society/Station,

telemetry-to-Atom mapping,

Source/Source Viewer,

Labo,

World model reconstruction.

The current transition is:

BUILD THE SUBSTRATE

        ↓

THE SUBSTRATE SURVIVES REALITY

        ↓

USE THE CONCEPTS

        ↓

BUILD AND INHABIT SEMANTIC WORLDS

The immediate practical focus is therefore:

Workbench,

Workflow,

Society,

World,

role/projection design,

and real use cases.

PLANTS is the first major practical validation of this phase.

The Radu seminar is expected to be the next human research use case.

36. Post-AI Perspective

Akasha should not be framed primarily as a response to the current AI-agent market.

Its central questions predate LLMs:

What is a concept?

How does meaning persist?

How do concepts relate?

How does a world change?

How do Agents participate in it?

How do observation and action connect?

How can knowledge and action travel?

What should a machine remember?

What is one meaningful computational operation on knowledge?

The appearance of LLMs is important because a new kind of semantic client suddenly exists.

But the architecture does not begin from:

LLM

 ↓

tools

 ↓

memory

 ↓

agent

It can instead approach AI after examining:

life,

environment,

cognition,

autonomy,

embodiment,

self/non-self,

memory,

society,

culture,

action.

This is one reason research around enactivism, autopoiesis, Buddhist philosophy, Yoga, mindfulness, Varela, Di Paolo, Evan

Thompson, and later American cognitive traditions is relevant to Akasha.

The intention is not to force these traditions into Akasha's existing vocabulary.

It is to let them challenge and reinterpret what concepts such as:

Agent,

World,

autonomy,

memory,

self,

action,

and cognition

actually mean.

A useful methodological principle is:

Temporarily move AI out of the center, travel through older and broader theories of life and cognition, then

return and ask what AI looks like from there.

This is a possible post-AI research direction, not a predetermined conclusion.

37. Design-History Guardrails

Future collaborators, including LLMs, should preserve the following distinctions.

Do not say:

"Telemetry made Akasha dynamic."

Prefer: "Telemetry experimentally demonstrated the dynamic sensor/world mapping already intended by the Atom design."

Do not say:

"LLMs caused Akasha to invent an Agent model."

Prefer: "LLMs provided a new first-class client with which the pre-existing human/machine participation model could finally

be exercised in a powerful form."

Do not say:

"Silica was invented because SQLite was bad."

Prefer: "SQLite remains a strong implementation; Silica realizes the older goal of an Akasha-native semantic instruction

boundary and allows direct control of memory operations."

Do not say:

"World/Workbench is Akasha's new direction."

Prefer: "The recent World/Workbench work is implementation catching up with a long-standing design direction."

Do not say:

"Workflow is an application feature."

Prefer: "Workflow is part of the semantic memory model: process, execution state, rollback, portability, and delayed

continuation are knowledge concerns."

Do not say:

"Seeds exists mainly because Akasha is local-first."

Prefer: "Local-first is important, but Seeds and degradation behavior also express the deeper requirement that semantic

knowledge and executable work can germinate under heterogeneous and constrained environments."

Do not say:

"Semantic macro-cache is merely a performance optimization."

Prefer: "It tests whether semantic attention can determine memory residency and, by extension, placement and distribution."

Do not say:

"Akasha is an LLM agent framework."

Prefer: "An LLM is one possible client/Agent within a broader semantic world."

38. Medium / Development Story Interpretation

The Medium development-side stories should be read as an implementation diary.

They record:

rediscovering old architectural questions,

testing them against modern software,

finding practical boundaries,

encountering failures,

simplifying implementation,

and watching the implementation converge toward the original conceptual design.

The narrative is therefore not:

Akasha idea A

 ↓

idea A failed

 ↓

invent idea B

 ↓

invent idea C

It is closer to:

long-lived conceptual design

        ↓

modern implementation attempt

        ↓

engineering obstacle

        ↓

implementation discovery

        ↓

another part of the old design becomes practical

This is the correct context for stories about:

concept-first design,

maps and projections,

reality becoming the beta tester,

cache becoming semantic,

reading SQLite,

Silica,

World,

Society,

Telemetry,

Workflow,

PLANTS,

and future Workbench use cases.

A concise formulation is:

The implementation kept discovering consequences of the original design.

39. Why the Historical Origin Matters

The thirty-year history is not included merely for nostalgia.

It explains why several current Akasha decisions differ from fashionable defaults.

Akasha did not begin by asking:

how to add memory to an LLM,

how to build an autonomous agent,

how to wrap a graph database,

how to create an AI SaaS platform.

It began from older knowledge-engineering questions about:

meaning,

concept representation,

semantic relation,

machine participation,

dynamic worlds,

executable knowledge,

and knowledge-native computation.

Modern technology has made those questions newly implementable.

This history is therefore part of the architecture.

40. Working Principle for Future Design

When a new requirement appears, do not immediately create a new application-specific subsystem.

First ask whether it can be expressed through existing primitives:

Atom / Link / Set

        ↓

Concept / Scope / Projection

        ↓

Agent / Role

        ↓

World / Society / Workbench

        ↓

Chronon / Workflow

        ↓

Harmonia

        ↓

storage / execution boundary

Examples:

a seminar should primarily be a Workbench/Workflow/Projection composition,

an auditor should primarily be an Agent + role + authority/knowledge Sets,

an IoT device should primarily be a client with relevant semantic Sets and sensor/actuator mappings,

an LLM should primarily be a client/Agent in a Society,

a professional domain should primarily be constrained semantic Sets,

a distributed job should primarily carry semantic context + Workflow + state.

Only introduce a new foundational primitive when the existing model genuinely cannot express the requirement without

distortion.

41. Short Canonical Summary

Akasha is a local-first Concept Operating System built on Atom, Link, and overlapping Set primitives.

Concepts can be approached through both deliberate definition and observed/functional structure. Scope shares the same Set-

like geometry, allowing semantic projection and strong isolation. Humans, LLMs, programs, sensors, and actuators can

participate as clients in the same World.

The system is dynamic by design. Telemetry can map observations into Atoms; Workflows themselves live on the Atom

network and can execute, resume, revise, roll back, travel, and potentially be rewritten by Agents. This makes knowledge

portable not only as facts but as executable semantic process.

Harmonia coordinates work above storage. Silica explores an Akasha-native semantic instruction boundary that may one day

map naturally toward specialized hardware. The same semantic boundaries that matter at the micro level also inform macro-

level cache residency, placement, parallelization, and distribution.

Seeds expresses the deployment philosophy: knowledge can remain dormant, encounter an environment, adapt to available

capabilities, and germinate. Degradation is therefore not merely an offline feature; it supports semantic continuity across

local, constrained, IoT, and DTN environments.

The foundational concepts are not recent reactions to LLMs. They originate in knowledge-engineering ideas held for roughly

thirty years. The current implementation history is the story of those concepts finding practical form.

The substrate is now strong enough that the project is entering its next phase:

not primarily building the semantic foundation, but using it to create real semantic worlds in which humans

and machines can observe, reason, work, communicate, revise, and act.

42. Canonical One-Line Orientation

Akasha preserves meaning across memory, execution, agents, worlds, and machines by keeping the semantic

unit visible from Atom to distribution.

Part II — Specification Additions, September 2026

Sections 1–42 are the foundational context and are kept verbatim. This part records what was specified, and in most cases

implemented and verified on the public server, between 1 and 20 September 2026 (A18–A23 added 19–20 September). Each

section names the foundational section it extends. Where a design is decided but not yet built, the section says so. Nothing

here introduces a new primitive: every addition is Atom, Link, Set membership, a macro over Set operations, or an operating

rule.

A1. Source → Datasets → Registry (extends 12, 21)

Pools and samples. A Source is imported as a pool: a Set of items with provenance, each item a content-addressed atom. A

dataset is a frozen sample of a pool — a Set with a role — stratified where labels exist, named by the digest of its member list,

immutable once sealed.

Three roles. A learning bench binds three datasets, each from any source:

target       what we want to recognize better        labels sealed

training     large, related, labeled                  labels used

evaluation   labeled, never seen by the model         labels used once

The held-out frame inside training is the selection frame; the evaluation set is the report frame. A sweep selects by the first

and reports on the second. Overlaps are measured at bind time by identity and by content digest. An evaluation item present in

training refuses the training. A target item present in training is removed from training by default: the target judges learning; it

does not participate in it. This default is a bench policy and is recorded on the bind.

Labels are an answer key. A target's labels exist as atoms but no observer reads them. They are consulted only by

comparison macros after the fact, and counts derived from them are public while the key itself is not (§A9).

Per-item trace. Every item exposes two lists, written at mint and never computed by a viewer:

observations[] — machine readings of the item (family, observer, model version, run, bench, branch, mode,

purpose), each a member of its coordinate Sets (§17 additions in A3);

interpretations[] — readings an Agent has bridged to the item, carrying the same coordinates plus the version of

the observer that produced the bridged reading.

An observation is not an interpretation; a viewer shows both and computes neither.

Registry (decided, not built — P1-R). A finished model version may be registered as a production model, by an Agent or by

an explicit bench policy (auto_register under policy is allowed). Registration copies identity, figures at registration and

full provenance into an immutable record, publishes the weights as an immutable generation, and moves one current pointer

by compare-and-swap. There is one registry per world, world-wide. Other benches observe with prod:<name> or pin prod:

<name>@<version>. The source bench may retrain or retire; a registered version never moves.

A2. Sweeps: Conditions, Lineage, Leaderboard, Versions (extends 14, 15,

21)

Template. A parameterized workflow is a file config/<bench>/templates/<name>.ak whose header #!params

a,b=default,… declares its bindings; steps reference them as $a. Templates ship with the seed.

A condition is a branch. wf.branch from=<template> params=k=v,… loads the template with its bindings and creates a

branch whose name is its lineage:

<parent>@p<fork position>/<template>@<cond8>

cond8 = first eight hex digits of the digest of the sorted bindings

Re-branching with identical bindings returns the existing branch (already=true). Every binding is a Set the branch marker

joins — set:wb:<b>:cond:<key>:<value> — so "every branch trained with this head on that split" is an intersection,

never a query. The lineage name is the one identity; a slug of it may be carried alongside as a key but is never the name.

A sweep is a named condition space with a budget.

sweep.def          grid → condition atoms (cartesian, bounded by max); 0 branches

sweep.materialise  up to n conditions → branches (wf.branch from=)

sweep.status       conds · branches · pending · done · failed · retired

sweep.leaderboard  the ranked projection (see below)

The grid expansion and the per-condition branch loop live in one concept (sweep.*), because the script language has no

loops; the shipped macros forward to it so that macro.ls / macro.run remain the operator surface. done is derived — the

branch has an evaluation in the sweep's evaluations Set — never written. A grid change adds conditions and retires the ones

no longer valid: status=retired, never deletion; a condition that already has a branch keeps its execution state and is

marked retired_grid instead. The grid's head values are validated against the learner kinds that actually train; a condition

whose head cannot train is refused at definition, and bench.train refuses an unknown head rather than degrading silently.

The engine that produced a model is always recorded on the model and on every evaluation row.

Admission. The society's policy lists sweeps; a branch whose marker names an admitted sweep may be run (society.run …

workflow=<lineage>) even though it is not a static workflows entry. The driver's selection of branches, the quarantine of a

branch after two failures, and the drift re-run of finished branches under a small daily budget are decided and not yet built

(P0-b); the quarantine counts members of the deviation Set of §A3, not a private counter.

Evaluations are a Set; ranking is a read. bench.evaluate writes one metrics atom per (model, frame) and joins it to

set:wb:<b>:evaluations, to the sweep's …:sweep:<name>:evaluations, and to every cond: Set of its branch; the atom

carries branch (lineage), cond8, model version, corpus digest, frame, n, the figures, engine, the bench coordinate, and the

artifact epoch. lens.rank set= key= [within=] [group=] sorts and groups; the default group is the frame, so figures

from different test sets are never ranked together; a request spanning frames is flagged, not merged.

The leaderboard is derived state. wb:<b>:leaderboard:<sweep> is the stored result of lens.rank over the sweep's

evaluations, each row joined with its condition's bindings and its engine, with select_by and report frames in the header

and a leak flag (constant false until selection and report frames differ). It carries built_at_epoch and an artifact identity;

a rebuild that changes nothing is a no-op; every prior generation stays in …:leaderboard:<sweep>:history. It is rebuilt in

the same write path that files an evaluation, and verified or repaired at boot by the hydrate registry (§A8). No operator

command produces it; the manual re-mint exists only as a participant write.

Versioned weights. bench.train publishes weights as an immutable, content-named generation (publish_generation)

and moves the model's pointer by compare-and-swap; on disk head_<run>_<sha8>.json is never overwritten, and

head_<run>.json mirrors the current generation for one seed so older readers do not break. vlab:learned:<oid> resolves

to the current version; @<sha8> pins one. keep_versions prunes files only and stamps weights_present=false on the

atom; nothing about a version is forgotten.

Cost (observed, not yet optimized). One condition re-embeds its training pool and its target pool with the same embedder

that earlier runs already applied to the same items: about forty minutes on the public server, all of it embedding. Embedding-

level reuse keyed on (item, observer model version) inside the vision observer is specified as its own slice; until it lands, a

sweep's cost is the embedder's, not the learner's.

A3. One Recorder: Execution, Trace, Deviation (extends 15, 16, 17)

One recorder. Whether a plan step runs inline or as a background job, the same recorder annotates the plan entry (status, a

result summary), mints the bench coordinate, writes the executes (execution) or rehearses (thought) link from that

coordinate to the plan position, and — when the branch belongs to a sweep — moves its condition to done or failed. A job

path that ran the plan without recording it was the defect the public server showed on 14 September; the rule is that execution

which leaves no trace on the plan did not, for the world, happen.

A refusal is a result, not a failure — and it is visible. A write refused by a grant returns status=refused with its reason

and logs one line ([<concept>] <op> refused bench=… caller=… reason=…). A background job whose step was

refused ends FAILED with that reason; it never ends DONE having written nothing.

Trace as causal structure. The links written at mint — executes, rehearses, forked_from, sync, superseded_by,

interpreted, evidenced_by (§A6) — are the causal structure. "Why this path" is a walk over incoming links from an

execution coordinate back through fork, dispatch and decision atoms; it is a macro, and it reads only what was written.

Deviation atoms (decided, with P0-b). When actual diverges from plan, the recorder mints wb:<b>:deviation:<exec8>:

<pos> with {kind, branch, pos, planned, actual, coordinate} and joins it to set:wb:<b>:deviations,

…:deviation:kind:<kind>, …:deviation:branch:<lineage>; it links deviates_from → the plan entry and

observed_in → the execution coordinate. Kinds: step_failed, rewound (by the driver — a mechanical reset, not a

thought), budget_chunked, result_drift (same bindings, different artifact identity), param_override,

admission_refused. A recurring deviation is then lens.rank … group=kind; the quarantine rule is "two members of

…:deviation:kind:step_failed for one branch". Plan, actual and observed remain three things; the difference between

the first two is an object of its own.

A4. The Epistemic Position (extends 3, 17, 19, 25)

The stamp. At each execution coordinate the recorder stamps what the acting session could see: role, a digest of its scopes,

the identity of the active horizon plan (the semantic macro-cache plan's artifact identity), a digest of its active Sets, and its

read budget. Every value exists at that moment; the stamp copies identifiers, not content. Two executions that differ only in

the horizon identity are a legitimate comparison.

Four distinctions, four Sets.

AVAILABLE    membership in the durable universe at that epoch   (an as-of read, §A5; never materialized)

VISIBLE      set:exec:<id>:visible    horizon plan ∩ the session's scopes at that epoch

CONSIDERED   set:exec:<id>:considered atoms the read core actually served to the execution

ACTED-UPON   the links the act atom itself wrote

CONSIDERED is the only new ledger and the only cost. Decision: it is kept in full only on benches whose purpose is

thought (the Thought Lab); elsewhere it is sampled, one execution in n, in the manner of the IPC sampler; its in-memory

copy is evicted with the telemetry tier. A missed decision is then visible − considered (shown, not read) or available −

visible (hidden by the horizon), computed by the comparison lens over two Sets.

Retrieval is an epistemic policy. What the macro-cache plan brings into the horizon shapes what an Agent can think with.

The plan is therefore an artifact with an identity, recorded on every execution, and a legitimate axis of a thought experiment

(§A6).

A5. Replay: As-Of Reads, Boundaries, Fidelity, Side Effects (extends 16,

17, 25)

As-of reads (decided — S1-c). Set membership and atom meta may be read as of a universe epoch (as_of=<epoch>), served

from the write-ahead sequence and the immutable generations. Content needs no as-of read (it is immutable); the horizon is

never read as-of.

A chronon is a replay boundary. replay.from chronon=<c> vary=k=v is a macro: resolve the coordinate's executes

link to its plan position, branch from the template at that position with the original bindings overridden by vary. The result is

a sweep condition whose lineage names the chronon it forked from; nothing new is named.

Three layers replay separately. State: as-of reads. Epistemic: the stamp of §A4, with the horizon plan re-hydrated from its

stored generation. Execution: the step results the recorder stored, served back instead of re-running the operator.

Fidelity is declared. A replay branch binds replay_fidelity ∈ {semantic, decision, action, bit}; the recorder

checks it at each step — bit: artifact identity equal; action: same operator and parameters; decision: same judged act;

semantic: the comparison lens reports no change under the declared frame — and writes fidelity_met as one more

evaluation row, so it ranks with the rest.

Side effects are isolated. A capability may be marked effectful (sending, publishing, physical action). In a replay, an

effectful step runs in thought mode: the stored result is served, the coordinate is minted with rehearses, and nothing reaches

the world. The mark is an attribute of the capability (§A7), not of a step.

A6. The Thought Lab, Acts and Claims (extends 13, 18, 20)

Acts are two coordinates. An act by an Agent is recorded as act_declared (what the Agent said it was doing) and

act_judged (what an observer or the bench judged it to be). Both are Set memberships on the bench clock; neither

overwrites the other. The Radu seminar runs on the thought kind from its first session, so every reading, comparison and

revision is an act with both coordinates.

A thought experiment is a sweep. The Thought Lab uses the sweep machinery of §A2 unchanged: a template binds model,

role, task, partner, skills (a capability Set, §A7) and activation (a horizon plan or admission policy), and every

binding is a cond: Set. What is compared is a configuration, never an Agent's isolated "intelligence".

Claims attach to evidence. A statement an Agent makes about work — "tested", "verified", "improved" — is a claim atom in

set:wb:<b>:claims with one link evidenced_by → an execution coordinate, an observation or an evaluation row. Its

status is derived at read time, never written: attached when a link resolves, unattached when none does, contradicted

when the evidence's own status (failed, retired, superseded) negates it. There is no false. Decision: a guest may read

counts per status; the text of a claim stays inside the admitted circle (§A9).

Distillation (later — P0-c). Once deviations (§A3) and replay (§A5) exist, comparing a successful and a failed branch after

their fork is a comparison lens over two execution Sets, and what is distilled is either a template parameter proposal, a

guardrail (a deviation kind the driver refuses to repeat) or a macro. It waits for several executions per condition.

A7. Capabilities: Identity, Qualification, Offer and Grant (extends 7, 9,

18, 29)

Identity. An operator's identity is the build fingerprint of the seed that ships it. A capability is <name>@<fingerprint>. A

comparison across seeds is honest by construction.

Qualification. A capability is qualified on the running build — by an evaluation on the bench that uses it — before it is

offered; a promoted capability is world-scoped, so every society in the world sees the same promotion.

Offer is not grant. What an Agent in a role can discover is the members of set:cap:offered:<society>:<role> — read

by cap.ls role= context=, guest-readable when the bench is public. What it may execute is the grant check as it stands

(operator:* capabilities, responsible:* roles on the society). "Can execute" and "may execute" are two Sets; a thought

experiment varies the first and never touches the second.

Effectful. A capability that reaches outside the world — send, publish, physical action — carries the attribute effectful;

replay (§A5) rehearses it, never executes it.

A8. Memory Semantics: Hydrate, Validity, Dependency, Value (extends

10, 16, 25, 31)

The hydrate registry. Every accelerator is registered with its name, canonical inputs, regenerator, layer version, boot policy

(verify or rebuild), and whether it is droppable. At boot, after relations are ready, the policy runs and logs one line per

accelerator — [hydrate] <name> boot=<policy> recorded epoch=<e> assigned=<n> — and stamps the run epoch;

assigned=0 on a verify means the accelerator equals its regeneration. hydrate.verify runs weekly. Regenerators

enumerate from canonical atoms, never from an index that only new writes join; an index is itself an accelerator the

regenerator backfills. In production the registry holds the observation layer, the chronon Sets, the macro-cache plan, the

retention collections, the boot index and the leaderboards.

Artifact identity = universe epoch + scope + coordinate + input Sets + transform/projection + access context. Stored

comparisons and boards carry built_at_epoch and are marked stale by comparison with their inputs' epochs, never silently

trusted.

Effectivity. "Valid when, under which condition, for whom" is an intersection: a chronon coordinate's range Set ∩ the cond:

Sets ∩ the role's visible Set — effective.at, a macro. No valid_from field exists.

Validity and expiry. An atom that expires joins set:valid:until:<clock>:<position>; the retention sweep moves

expired members out of the horizon and never out of the store. Historical observations join no such Set.

Dependency and contradiction. depends_on and contradicts are links. A beliefs accelerator (verify at boot) stamps

status=retired reason=source_retired on dependents of a retired or superseded source — the same word the sweep

uses, so every viewer already knows it.

Memory value. beacon_strength is an accelerator, regenerable from four Sets: revisits (admits by day), decision influence

(membership in considered Sets of executions whose evaluation ended ok), outcome, and freshness (chronon distance). It is

a residency signal for the macro-cache plan next to demand; the plan remains the horizon, the strength remains derived and

droppable. Decision: every new accelerator runs verify-only for its first week in production before it may influence anything.

Forgetting. To forget is to leave the horizon. Nothing leaves the universe except by a retention rule that names it.

A9. Identity, Groups, and the Public Circle (extends 7, 8, 19)

Rules the public server taught between 13 and 15 September 2026, now part of the design:

Privilege is a role, not a name. A session is privileged when its scopes say so (scope:sys:admin,

role:librarian), never because its identifier equals a literal. Internal boot dispatch may carry a bare identifier; a

person never does.

Membership is written by provisioning. A society's group created at provisioning contains the world's admin

identities; an admin who is not a member of a group cannot open it, and that is correct — so the provisioning writes the

membership rather than the gate being widened.

Unknown is refused. Adding a member to a group that does not exist is refused; only creation creates.

Identities stay in the circle. Group member identifiers are readable by members; a guest reads counts. The same rule

governs claims (§A6) and answer keys (§A1): counts leave the circle, identities and texts do not.

Derived state needs no command. A leaderboard, an index, a coordinate layer — anything regenerable — is produced

by the write that changes its inputs and verified at boot. If a document ever asks an operator to type a command to

produce derived state, the document is wrong.

A grid change retires; it never deletes. History stays legible; what is no longer valid is marked, skipped, and counted.

Re-index from the truth. When a new build changes what an accelerator indexes, the boot repairs the index from the

canonical atoms; a new build re-applies idempotent definitions (sweeps, policies) exactly as the driver re-arms itself on

a new build.

A10. Status of the Additions (15 September 2026)

Implemented and verified on the public server:

  A1  pools, frozen samples with roles, per-item trace (observations / interpretations)

  A2  templates, lineage branches, cond Sets, sweep.def/materialise/status, retire,

      evaluations Set, lens.rank, derived leaderboard, versioned weights

  A3  one recorder (inline + job), refusal logging, job FAILED on refusal

  A8  hydrate registry with boot verify/rebuild, artifact epoch, leaderboard as accelerator

  A9  all rules

Decided, not yet built:

  A1  registry (P1-R), evaluation set and selection/report frames (P1-D)

  A2  driver picking, quarantine, drift re-runs (P0-b); embedding reuse (S2-k)

  A3  deviation atoms (with P0-b)

  A4  the stamp and the four Sets (P2)

  A5  as-of reads (S1-c); replay, fidelity, effectful (P2, P3)

  A6  claims (with P0-b); the Thought Lab templates (P2)

  A7  cap.ls and offered Sets (P3)

  A8  effectivity macro, validity Sets (next order); beliefs and beacon_strength (after one hydrate week)

Taken in 17 September 2026 (the Cognitive Workbench Extension proposal), decided, not yet built — track C:

  A11 observation bundles and their coordinates (vision layer is the first instance, in production)

  A12 alignment frames as hydrate artifacts (observe.diff / lens.compare / lens.rank are the first, in

production)

  A13 Nebula candidate Sets and links (the nebula explorer itself is in production)

  A14 role binding as five Sets; driver axes; frame-generating budget; the abductive template

  A15 proposals, moderator decisions, scoped grants, the causal walk

  A16 the C0–C6 pack and vector evaluation

Note (17 September): since the 15th, B1 (driver picking, deviations, claims), B2 (embedding reuse) and R7 are in production;

S2-m3, B1-a, S2-k2, B1-b are in production as of 51b7a847b5; wave 2 (A8 macro + validity Sets, A7 offered Sets, A5 as-of

reads) is ordered.

A11. Observation Bundles: Non-Linguistic Observation Coordinates

(extends 12, A1)

Scope. Everything an observer produces — a probability distribution, a feature vector, an embedding, a prediction error, a

spike train, a cluster assignment, a slot, an anomaly score, a time-series state, a label — is an Observation. It requires no

language. The vision layer of §A1 is the first instance; this section is the general rule.

Unit. The stored unit is the Observation Bundle: what one observer formed in one pass over one input range. A bundle is one

atom carrying its coordinates; its high-dimensional body, when there is one, is a content-addressed artifact in the artifact store,

referenced by identity. Raw tensors never become atoms.

Coordinates written at mint (all Set memberships):

source · input range              set:vlab:src:<item>:obs, set:src:<pool>:range:<r>

observer family · identity · version   set:vlab:family:<f>, :observer:<o>, :model:<sha8>

layer                             set:obs:layer:

<signal|residual|feature|bundle|proto_object|proto_concept|concept|interpretation|language>

modality · readout                set:obs:modality:<m>, set:obs:readout:<r>

run · bench · branch · mode · purpose   as §A1 / D2-M

chronon · window                  the bench coordinate; set:obs:window:<clock>:<from>..<to>

granularity frame                 set:obs:frame:<name>          (§A12; the frame the bundle was read in)

transform · projection            set:obs:transform:<t>         (identity when none)

representation type               set:obs:repr:<distribution|vector|sequence|assignment|score|label>

uncertainty                       meta {confidence, error, degraded}

artifact identity · input Sets    meta {artifact_id, inputs[]}

status                            set:obs:status:<observed|absence|degraded|mock|refused>

The layer table is a frame, not an ontology: the same output may sit at a different layer in another frame, and says so by

joining another frame Set. An absence (an observer looked and produced nothing) is a bundle with status=absence, never a

missing row.

A12. Precomputed Alignment Frames (extends 19, 25, A8)

Comparing heterogeneous observers is paid for before any reasoner looks: temporal and spatial alignment, granularity

conversion, distribution comparison, neighbourhood and topology, clustering, prediction–observation delta, cross-observer

agreement and disagreement, missingness, before–after, cross-modality crosswalks. Each result is a derived artifact whose

identity is universe epoch + scope + coordinate + input Sets + transform + projection + access context (§A8), stored through

the artifact store and registered in the hydrate registry (droppable=true, on_boot=verify): regenerable from the canonical

observations, never the truth. The comparison macros in production (observe.diff, lens.compare, lens.rank) are the

first alignment frames.

Seven rules, none negotiable:

1. An alignment never overwrites an observation.

2. An aligned representation is a Projection, not a source fact.

3. Several alignment frames coexist; none is "the" frame.

4. No ranking crosses frames implicitly (lens.rank refuses; the board groups by frame).

5. The transform and its lossiness are recorded on the artifact.

6. Staleness is shown (stale from epoch comparison), never hidden.

7. A value filled by inference is marked imputed and is not an observation.

A13. Nebula: Externalised Proto-Concepts (extends 4, 13, A6)

Not new. nebula exists: the inductive explorer that surveys the universe for regions that grew the same relation schema and

proposes them; a human confirms and names (nebula.confirm), rejects, or forgets. This section widens its candidates and

fixes its representation; nothing is renamed.

Candidates join set:nebula:<kind> Sets at the moment they are formed, by any Agent, observer or alignment macro:

weak_association · unnamed_cluster · anomaly · competing_boundary

· provisional_relation · contradiction · retained_hypothesis

· minority_interpretation · alternate_frame · candidate_concept_model

Each candidate is an atom with the link vocabulary: observed_in, derived_from, interpreted, supports,

contradicts, depends_on, predicts, explains, forked_from, superseded_by, evidenced_by (the same links §A3

and §A6 use).

Rules. No candidate is merged or promoted by a score. Promotion to a Concept (or to a Concept Model) is an act with both

coordinates (act_declared / act_judged, §A6) or a declared bench policy, and is recorded as nebula.confirm. After

promotion the candidate and its formation history stay in the Nebula (superseded_by → the concept). A candidate that no

current evaluation frame can measure is retained, never deleted for that reason. Guests read counts per kind; candidates' texts

follow the circle rule of §A9.

A14. Cognitive Society and the Thought Lab Driver (extends 18, 20, A6,

A7)

Participants need no speech. Human, LLM, classifier, embedding observer, sequence model, anomaly detector, learned

head, sensor, actuator controller, workflow, another Akasha — each is an Agent. There is no message passing between them;

every observation, proposal, evaluation and interpretation passes through the shared semantic world.

A Role is a product of Sets, never a persona prompt:

Role = responsibility            set:role:<society>:<role>:responsible   (the responsible:* links)

     × visible Projection        set:cap:visible:<society>:<role>         (§A7)

     × offered Capabilities      set:cap:offered:<society>:<role>         (§A7)

     × granted Capabilities      the grant check                          (§A7)

     × output contract           set:role:<society>:<role>:contract       (what its acts must carry: e.g. an

observer's act must carry a bundle, never an interpretation)

     × evaluation frame          set:role:<society>:<role>:frame          (which frames judge it)

Named roles ship as configuration: observer, anomaly_finder, hypothesis_generator, counterexample_seeker,

evidence_challenger, frame_proposer, conservator, synthesizer, moderator. A role whose only difference from

another is prompt text is not a role; the evals assert that two roles differ in at least one of the five Sets.

The driver's axes are template bindings (§A6), each a cond: Set: model, role, task, partner, skills, activation,

observer_composition, observation_frame, granularity, alignment_transform, nebula_visibility,

replay_origin, budget, autonomy_mode, evaluator_composition.

Two searches, two budgets. Within-frame search varies conditions inside declared concepts, variables and frames — the

sweep, driver, board and replay as they stand. Frame-generating search starts from an anomaly (a Nebula candidate) and

proposes a new grouping, relation, concept candidate, granularity, comparison frame, evaluation vector, or intervention; its

output is itself a Nebula candidate or a new sweep definition, and it draws on its own budget key

(budget.frame_generating), so that the cheaper search never starves it. The two are never mixed in one branch.

The abductive loop is a workflow template (config/<bench>/templates/abduce.ak): unexplained observation →

competing hypotheses and frames (Nebula candidates) → predicted discriminating observations → replay / counterfactual /

new observation → evaluation under several frames → retain / revise / fork / retire → optional promotion. A hypothesis

without a positive result is retained unattached (§A6); nothing is deleted because the current frames cannot measure it.

A15. Containment: The Human Moderator Boundary (extends 7, 18, A5,

A7, A9)

Principle (original to the design, restated). Cognitive autonomy inside the Workbench; operational authority at the

boundary with the world stays with a human moderator. A Thought Lab runs unattended — branching, rewinding, sweeping,

comparing, re-running — and no one approves its thoughts. Approval is required exactly where thought would become an

irreversible act.

Protocol.

1. A capability that reaches outside the world carries effectful (§A7).

2. In thought mode an effectful step is never executed: the stored result or a declared simulation is served and the

coordinate is minted with rehearses (§A5).

3. A Society may create a proposal: a claim (§A6) whose about is one capability call — {world,

capability@fingerprint, params, expected_effect, risk_frame} — and whose evidenced_by points at

the branch that rehearsed it. It joins set:wb:<b>:proposals.

4. The moderator records one act per proposal — approve, refuse, request_revision — with both coordinates; the

act links decides → the proposal.

5. An approval writes a grant record in IAM: {capability, target, scope, expires_at (a chronon

coordinate), uses_left}, minimal by construction: one target, single use unless stated, and an expiry the

moderator names explicitly as a chronon coordinate (until=cronon:…:c<n>). There is no default expiry; an approval

without until= is refused. (Decision, 17 September.) The existing grant check reads it; nothing else changes in

authorisation.

6. Execution happens only after sync to the world, is recorded with executes, and consumes the grant.

7. The result returns as an Observation (§A11) into the Workbench — the cycle's last link.

8. No Agent can widen its own role or grant; offer, discovery and execution stay three Sets (§A7). A proposal whose grant

expired reads expired, never executes, and stays.

Causal walk. From any effectful execution coordinate the links lead back: executes → the plan entry → decides ← the

moderator's act → the proposal → evidenced_by → the rehearsing branch → its lineage and chronons. The walk is a macro

over existing links.

Authority is not truth. An approved hypothesis is not thereby true; a refused one not thereby false. The moderator's decision

is a procedural act with its own coordinates and nothing more.

A16. Experiment Pack C0–C6 and Vector Evaluation (extends 21, A2, A4)

Conditions are one sweep definition (config/<bench>/sweeps/ cognition.json) over the same task and Sources:

C0  one LLM, plain context, no Nebula

C1  several LLMs, no roles

C2  several LLMs, roles

C3  roles + shared observations

C4  roles + observations + Nebula

C5  heterogeneous LLMs + non-linguistic observers + Nebula

C6  C5 + a human buddy

Same-model instances and heterogeneous models are separate conditions; a role difference must be a Set difference (§A14),

so that the pack cannot degenerate into prompt theatre.

Evaluation is a vector. An evaluation row carries, per declared frame, the axes it can measure: task performance, explanatory

coverage, hypothesis diversity, anomaly discovery, contradiction discovery, evidence attachment rate, calibration, recovery

from a false lead, counterfactual reach, predictive discriminability, transfer across Sources, novelty relative to the ontology

and the history, survival across alternate frames, retained minority interpretations, human cognitive expansion, and cost

(compute, tokens, wall-clock). The board ranks on one declared key at a time and groups by frame; no composite score is ever

computed by the system. Novelty is read only together with coverage, testability, coherence and evidence.

Human cognitive expansion (C6) is measured from the Sets that already exist: hypotheses the human could consider

(visible, considered, §A4), relations and counterexamples first seen, decision changes and their evidenced_by, the

Projections reached that the human did not reach alone, and the uncertainty retained after the decision. The human's final

judgment is an act with both coordinates, not ground truth.

Exit criteria (the proposal's twelve, kept): observers compared without language; observation, derived artifact and

interpretation never confused; frames never overwrite; identical inputs regenerate identical artifact identities; the Nebula holds

competing candidates without forced merge; role differences are observable as Set differences; an unattended Thought Lab

completes branch, rewind, sweep and evaluation; no effectful capability reaches outside from thought mode; every effectful

execution walks back to a moderator decision and a grant; results return as observations; C0–C6 reproduce on one Source,

task and frame set; evaluation keeps several axes.

A17. One Gate for Every Model: Shared LLM Routing and Allocation

(extends 9, 18, 24, A7, A14)

Why. An LLM in a Society is one Agent among many (§9, §A14). In production the Agents that use one share a single

external contract — today one free tier, hosted in the EU; next a local model; later others — and the archives run as a

demonstration on no budget. The gate that every call already passes through (llm_provider.generate: one function, no

per-program keys or endpoints, a hard daily/monthly floor, rate spacing, persisted accounting) is the right place; what is

missing is allocation: who may spend how much of a bounded day, decided before an execution starts rather than discovered

halfway through it. This section adds that layer as an option of Society routing. It adds no thread, no scheduler, no second

queue, no parallelism, and no per-program wiring.

Provider as capability. A model is offered to a role as a capability llm:<provider>:<model>@<fingerprint8> in

set:cap:offered:<society>:<role> (§A7). "Which model" is therefore a role binding and a Thought Lab axis (model,

§A14), not a property of the Society. A Society may hold several LLM participants (one per role or several per role); a single

contract may be shared by every Society in the world. Both are the same mechanism: the capability names the provider, the

gate owns the contract.

Routing option. A society's policy declares llm.route:

shared     every call goes through the world gate's pool for that provider (default)

dedicated  the society carries its own provider record (a second contract / key), still through the gate

local      the provider is a local model (`ollama` today); pool capacity = the host's declared budget

Provider order for the launch: mistral (shared free tier) → ollama (local) → others. Switching is configuration; the

semantic layers never learn a provider's name beyond the capability atom.

The pool. Per provider, per bench day, one bounded pool: {capacity_calls, capacity_tokens_est, reserved,

spent, by[program]}. Capacity is the self-imposed cap already in force (below the provider's published figures;

overridable by environment). The day boundary is the refill; there is no scheduler. The pool is a readable record, not an

opaque counter: one aggregate atom per provider per day (llm:pool:<provider>:<bench day>), joined to the day Set the

retention sweep already iterates, so it is bounded and compacts with the telemetry tier (decision 1).

Allotment is declared where the schedule is declared. Every program that already declares its cadence (a station

programme's per_day, a sweep's budget, a society's autorun policy) gains two values there: llm_calls_per_run (the

estimate) and weight. The programme table's "today / daily budget" cell is the public face of these numbers; no new

configuration surface.

Admission reserves per execution. At the single job admission point (submit_job), before a run starts: reserve

llm_calls_per_run from the pool. Admitted → the run proceeds prepaid and cannot run out mid-way. Refused → the run

does not start, the refusal is logged with its reason, and the programme earns a carry-over credit that places it first at the next

admission (a once-a-day programme survives beside a continuous one). At the end of a run, unused reservation returns to the

pool and the actual spend is written to the job's cost ledger (the fields exist; they finally carry values). Priority ordering gains a

cost axis in the existing priority projection: interactive work before batch, an over-allotted requester after everyone else;

callers unchanged. The hard floor stays as the last line of defence; a reservation defect can never exceed the provider cap.

Estimates. A programme reserves its declared estimate; the ledger's measured mean corrects the declaration over time

(decision 3: declare, then correct from measurement). Allocation is priority + carry-over first; weights are added only when a

programme actually starves (decision 2).

Containment link. A call to an external provider is not effectful — it changes nothing in the world — so it is allowed in

thought mode; publishing its output is (§A15). The gate therefore never asks the moderator; the publish step does.

Observability. The pool atom is readable by the circle (counts only to guests: calls, spent, refused); every refusal is a

deviation of kind admission_refused (§A3) on the programme's branch; the station's Health line gains llm(pool=

<provider> spent=<n>/<cap> reserved=<n> refused_today=<n>).

Order of implementation (decision 4: this before more programmes): stage 1 pool + reserve/settle at admission; stage 2

carry-over + cost axis; stage 3 ledger-driven estimates. Each stage is safe to stop at; every stage keeps the floor.

A18. Workbench-to-World: Commitments, Trials, Residuals (extends A3,

A5, A6, A12, A15, A16)

Why. §A15 ends with "the result returns as an Observation into the Workbench — the cycle's last link" and stops there. This

section specifies that link and everything between a board and the world: how a hypothesis that ranks first becomes a bounded

act, how the act is watched, and how what comes back changes the next experiment. Nothing here is a new primitive: every

artifact is a claim, a Set membership, a derived artifact, a grant record or a macro that already exists or is already decided.

Taken in 19 September 2026 from the maintainer's proposal "Workbench-to-World Feedback Loop".

Principle. A hypothesis that ranks first has been compared, not confirmed. Acting on it is a provisional operational

commitment: a rational decision to act under stated coordinates — the Sources and observations used, the competitors

compared, the roles and scopes, the projection and horizon, the chronon and epoch, the frames and weights, the intended

environment — and never a claim that it is true. Operational validity and ontological claim are two things; Akasha records the

first and never converts it into the second. Unresolved questions are kept as questions: stable places where observations,

interpretations and refutations accumulate.

The commitment is a claim. set:wb:<b>:commitments holds claim atoms (§A6) whose about is one evaluation row plus

a decision frame, and whose evidenced_by points at that row. Everything else is a Set membership on the commitment:

application scope, risk class, reversibility, level (set:commit:<key>:<value>), and expiry as set:valid:until:

<chronon> with no default. Score, confidence and uncertainty are read from the row, never copied. Status is derived: active

(link resolves, unexpired), expired, superseded (a later commitment on the same hypothesis), withdrawn (an act).

Competitors are the other rows of the same sweep and frame; they are never retired by a commitment.

Levels are grant scopes. L0 replay / counterfactual and L1 shadow need no grant (thought or read-only); L2 advisory is a

proposal that names a human executor and no capability; L3 sandbox is a grant whose target is a sandbox world or group; L4

canary is a grant with uses_left, one target, until=; L5 bounded automation is a declared bench policy with budget, stop

and compensation; L6 policy promotion is a registry-style record (§A1: immutable, CAS pointer). Promotion to the next level

is a new claim evidenced_by the previous level's evaluation rows — never the same trial's own report. L4 and above always

carry a moderator act (§A15). Admission is a policy, not a formula: thresholds are Sets (set:policy:admit:<key>:

<value>), the driver may propose at L ≤ 3 under such a policy, hypothesis_gap is a read (rank 1 versus rank 2 within the

frame), and the six options — adopt, trial small, shadow, fetch more Sources, choose the experiment that discriminates

competitors, defer — are acts with both coordinates.

The proposal is §A15.3, with its about extended by maximum_effect, idempotency_key, observation_window,

abort_condition, compensation. Approval, grant, sync, executes and consumption are §A15.4–6 unchanged.

The outcome contract is sealed before the trial. A derived artifact (§A8) with identity and built_at_epoch — content-

addressed, so it cannot be rewritten after the fact — carrying baseline, expected metrics and ranges, the observation sources,

the deadline, the attribution window, known confounders, and unknown_allowed=true. Expected observations are declared

as bundle coordinates (§A11: observer, frame, window), so an expected reading that never arrives is a bundle with

status=absence, never a missing row. The commitment links contracts → the contract (the one new link kind).

Pending observation without a scheduler. A sealed contract joins set:valid:until:<clock>:<deadline>; the retention

sweep that already iterates validity Sets at the day boundary finds contracts whose window closed and submits the evaluation

job. unobserved is then derived: window closed, returns Set empty.

What returns is canonical; the residual is derived. The observation that comes back from the world is the atom — a bundle

with provenance=external, observed_in → the execution coordinate. The residual — expected versus observed,

direction, confidence, attribution — is an alignment frame of the kind §A12 already lists (prediction–observation delta),

derived_from the contract and the observation, regenerable, stale when its inputs move, never the truth. A residual no

current hypothesis explains also mints a Nebula candidate (§A13: anomaly, retained_hypothesis). Deviation (§A3, plan

versus actual) and residual (expected versus observed) are two objects and are never merged. Outcome statuses are

vocabulary: set:trial:outcome:<s> with confirmed_within_scope · partially_supported ·

operationally_useful_unexplained · contradicted · inconclusive · unobserved · confounded ·

unexpected; the third of these is a first-class result and is never hidden. A success is also asked for its residual: a coarse

success judgement loses the microscopic difference.

Two evaluations, two frames. A trial is evaluated under an operational frame (quality, time, cost, stability, effect on users,

safety, reproducibility) and an epistemic frame (where the prediction held, where it failed, whether a competitor explains the

same result, whether the frame itself was biased, what was unobservable, which new variables or boundaries appeared,

whether re-experiment is worth it). Both are frames of the vector evaluation (§A16); no rank crosses them (§A12 rule 4). A

business success does not confirm the causal hypothesis; a business failure that returned a high-value residual is an epistemic

success. A decision frame that ranks a vector by declared weights is allowed only as a declared, identified artifact with the

weights recorded on it, ranking within one evaluation frame; the board never computes a composite by default.

Roles. Harmonia decomposes a trial into budgeted jobs, watches stop conditions, inserts the gate before an effectful step,

starts the evaluation job when the window closes, runs rollback or compensation on failure, and keeps the commitment

pending until something returns; it decides no truth. The Society separates proposer, moderator, executor, observer and

reviewer as roles (five Sets, §A14) and may require by policy that one Agent does not hold them all; execution permission and

epistemic support are two things.

Causal structure. hypothesis → evaluation → commitment → proposal → moderator decision → execution → external

observation → operational evaluation → epistemic evaluation → revision, each a coordinate with the stamp of §A4, walked

by the macro of §A15 extended by contracts, observed_in, derived_from, predicts.

Distillation (§A6, P0-c) reads recurring residuals: a template parameter proposal, a guardrail (a deviation kind the driver

refuses to repeat) or a macro — proposed, never applied.

First scope. Internal, reversible, observable choices: the horizon plan (two macro-cache plans, L1 shadow by visible −

considered, then L4 canary on one bench), then the driver's pick policy. Deletion, publishing outside, sending, payment and

physical control are out of the first loop.

Command surface (macros over claim, proposal, workflow, observation): commit.propose bench= branch= frame=

scope= risk= expiry=, commit.inspect id=, commit.approve id= role= level= budget=, commit.refuse id=

reason=, trial.plan commitment= outcome_contract=, trial.run id=, trial.abort id= reason=,

trial.observe id= source=, trial.evaluate id= operational_frame= epistemic_frame=, trial.feedback

id= branch=true.

Invariants. Thought and execution are never confused; an external effect needs a proposal first; high-risk or irreversible

effects need a human moderator regardless of score; predictions are sealed before the trial; execution, refusal, stop and

unobservability are all recorded; hypothesis, score vector, decision frame and scope are stored together; operational success is

never converted into truth; competitors and past evaluations are never deleted; deviation and residual are separate objects; an

execution from which nothing returned is not a completed loop.

First completion. For one bounded task, one lineage answers: which Sources and observations produced the hypothesis; in

which condition space it was compared; why it became a candidate; who permitted which effect at which scope; what was

done; what returned; what the difference from the prediction was; how the difference changed the next hypothesis or

workflow — and the loop replays from the same chronon under another condition.

A19. Review Mode: A Falsification Rubric as a Thought Lab Frame

(extends A4, A6, A13, A14, A16; anticipates A18)

Why. A hypothesis that ranks first in a sweep has been compared; it has not been examined. Examination is a different act: not

"which configuration scores best" but "what would make this hypothesis wrong, and has anyone looked". The Thought Lab

already has the roles for this (counterexample_seeker, evidence_challenger, frame_proposer, conservator, §A14)

and the places to put what they find (claims with evidenced_by, §A6; Nebula candidates, §A13). What is missing is a shared

list of questions every examination asks, so that two reviews of two hypotheses are comparable and a review that skipped a

question is visible as such. This section adds that list as vocabulary, and the examination as a template and a frame. No new

primitive.

The rubric is vocabulary. Ten questions, one atom each in a review namespace (nsdef:review), defined once in the

lexicon:

review:q:definition        Are the terms defined? (each term of the hypothesis resolves to an atom; an

unresolved term is the finding)

review:q:counterexample    Is there a counterexample, in the Sources or in the history?

review:q:alternative       Is there an alternative explanation of the same evidence?

review:q:unobservable      Does it rest on an assumption no observer can read?

review:q:other_model       Would a different model / observer produce the same result?

review:q:weakener          Which observation would weaken it?

review:q:rejection         Under which condition is it rejected?

review:q:gain              After a counterexample, did the revision gain predictive power?

review:q:parameters        Or did it only add a free parameter?

review:q:transfer          Does it hold under another Source, role, or Projection?

A question the code compares against is an id, never a string. The list is extended by adding an atom, never by editing the

code.

A verdict is a Set membership with evidence. A review of a hypothesis H (a claim, a commitment of §A18, a Nebula

candidate, or a leaderboard row) writes, per question, one act with both coordinates (act_declared / act_judged, §A6)

whose result joins exactly one of

set:review:<q>:passes          the question was asked and answered in H's favour

set:review:<q>:fails           answered against H — the finding is the evidence

set:review:<q>:unobservable    the question cannot be answered with the Sources and observers at hand (a bundle

with status=absence, §A11)

set:review:<q>:not_asked       the review did not reach this question (budget, refusal)

and links evidenced_by → what the answer rests on: an observation, an evaluation row, a Source item, a replay branch, a

Nebula candidate. A fails on alternative mints the alternative as a Nebula candidate (retained_hypothesis or

minority_interpretation); a fails on counterexample links contradicts. There is no false (§A6): a review never

deletes or demotes H; it attaches what was found.

The review is a template, run by roles. config/<bench>/ templates/review.ak binds hypothesis, reviewers (a role

Set, §A14 — at least two of counterexample_seeker, evidence_challenger, frame_proposer, conservator; a human

may hold any), sources, budget; each question is one plan step executed through the one recorder (§A3), so

cronon.executions lists ten coordinates per review and a review cut short shows not_asked for the rest, never silence. A

review runs with purpose=thought; it publishes nothing. Two reviews of one hypothesis are two branches (wf.branch), and

their disagreement is a comparison lens over their verdict Sets, not a merge.

The rubric is an evaluation frame, not a score. The ten verdicts form one declared frame (frame=review) on the vector

evaluation of §A16; the board may rank on one question at a time within that frame (lens.rank

key=review:q:counterexample), and never sums the ten. "Passed review" is not a word the system uses; a viewer shows

ten cells, each passes / fails / unobservable / not_asked, and the reader draws the line.

Where it binds. Three questions feed the Workbench-to-World loop (§A18) directly: weakener and rejection are the stop

conditions and expected observations an Outcome Contract must name — a commitment whose hypothesis has not_asked or

unobservable on either cannot be proposed above L1; transfer is the sweep across cond: Sets the abductive template

already runs (§A14). gain and parameters are read again at the epistemic evaluation after a trial, on the revised hypothesis.

definition is the project's own thesis applied to itself: a hypothesis whose terms do not resolve in the lexicon is not yet a

hypothesis, it is a phrase.

Guests. Counts per question and verdict are public; the findings' texts follow the circle rule (§A9).

Evals. review_workbench_eval: a review of a fixture hypothesis produces ten coordinates; a budget cut leaves not_asked

members; a fails on alternative produces a Nebula candidate with evidenced_by; lens.rank refuses to sum the frame;

a commitment over a hypothesis with weakener=not_asked is refused at commit.propose level>=L2 with the question id

as the reason.

Source. The idea of a fixed list of examination questions, applied to every hypothesis alike, was prompted by senka L8's

Layer-8 Cognitive Architecture / SCOPE × COS work (https://github.com/senka-l8/Layer8-Cognitive-Architecture) and the

author's public posts on it. The ten questions as written above are the maintainer's formulation for Akasha; this section

borrows none of that model's terms or structure (A1–D4, layers, Sephirot) and makes no claim about it — per its Citation &

Usage Policy v1, which asks for URL and author credit and forbids borrowing terminology into a different model. Readers of

that work should go to the source.

Staging. With D1 of track D (the manual loop): vocabulary (nsdef:review, the ten atoms, the four verdict Set families) first,

then the template and the review.run hypothesis= reviewers= macro; GUI: ten cells on a hypothesis row, one order

after the reads are live.

A20. One Workbench, One Driver: Workloads, Duty, Effect (extends 14,

15, 18, A2, A3, A15, A17)

Why. A research sweep, a broadcast programme and an operational business process were being run by two different

arrangements of bench, society and workflow, and a driver that knew one of them. Each fix became a branch on a name.

Ruled 20 September 2026: there is no "research mode" and no "operations mode". One unit carries the difference as a

declaration.

Four words, fixed. A Bench is where coordinates, observations and artifacts live; its kind names observer families and

nothing else. A Society is who may act: roles, grants, moderator. A Workload is the unit the driver runs: one workflow

(template + params) on one bench, acted by one society, declaring trigger, duty, effect, appetite, budget, and pins

(§A22). A Programme is a workload with duty=continuous and effect=publish; a room shows it. Every field of the

declaration is a Set membership (set:wl:duty:<d>, set:wl:effect:<e>, set:wl:trigger:<t>, set:wl:bench:<b>,

set:wl:society:<s>), so "every continuous workload that publishes" is an intersection. The key <bench>/<slug> (§A17's

programme key) is the workload's identity in the pool ledger, the guide, the Health line and the room.

What the driver reads. Five things: trigger (boot, cadence, pick), duty, effect (thought · execute · publish), appetite

(§A17), budget. It never reads a bench kind, a society's or a group's name, or the existence of a programme file. An eval

greps the driver, admission, society.run and the recorder for the forbidden comparisons.

Duty is the only behavioural switch. wb:duty:best_effort (default, research): a gate that stops the run writes skipped=

<reason>; repeated failure takes it off the schedule until someone looks; nothing is owed at boot; a run that produced nothing

is a run that produced nothing. wb:duty:continuous (programmes, business processes): any stop joins the workload to a

state Set with a reason id — never silent; the breaker never unschedules; one run is owed at boot (skipped=fresh only if the

last run is younger than the cadence); a run that produced nothing reads standing_by · no_text and the previous airing is

rebroadcast until the next trigger. States are vocabulary — wl:state:warming_up · on_air · rebroadcast ·

standing_by with reasons fresh · llm_pool · provider_429 · provider_capacity · provider_absent ·

no_text … — one membership at a time, the previous one ended on the bench clock. A rebroadcast is a state, never a new

airing: no model call, no reservation, no observation, no atom.

Provisioning gives every workload its workflow. At boot, from the declaration, idempotent, re-applied on a new build: the

bench exists; the society exists with the admin identities, roles as five Sets and a moderator; the workflow exists on the

declared bench (wf.new from the template file — never a bench named after the society, never an assumed main); the

workload atom with its memberships, armed if its trigger says so; registered in the guide if effect=publish; one line

[bench] provisioned workload=… society=… workflow=… trigger=… duty=… effect=…. A declaration without a

template is a provisioning error at boot, not a workload "left alone". Provisioning is the one place that acts as admin.

The station under these rules. One group studio_ai; one society per programme studio_ai/<slug>; one bench

wb:studio_ai; one workflow per programme; the news programme is the same shape — its turn logic becomes ops in a

template, its own timer goes, the driver owns the cadence. The guide lists workloads with effect=publish only. "Airings

today" is one number: members of the workload's observations Set ∩ the day Set, read by the guide, the Health line and the

pool ledger alike.

The test. Adding an operational workload — a payroll run — is a template, one declaration with duty=continuous, a

society with a moderator, and a grant with until= for the effectful step. If it needs a branch anywhere, the branch is the

defect. A generic conformance eval (workload_conformance_eval <declaration>) runs the same checklist for every

workload: fresh store → boot → provisioned line → one run → coordinates → observations → state Set → guide row →

second boot unchanged → a gate refusal writes a reason → an effectful step rehearsed in thought → no literal state in code.

A21. The Heart and the Application Layer (extends 1, 6, 24, 29, A9, A20)

Why. By 20 September 2026 the kernel held 18,310 lines: the schedulers of every function, the provisioning, the station

daemon, the bench driver, the ontology pack loader, and 169 RPC handlers behind a chain of 128 comparisons; it reached into

the Concept Models from inside its methods forty-three times. A new Concept Model, ontology, bench or room could not be

written without opening it. Ruled: two layers, one direction.

The heart is kernel.py and the core modules — sessions, IAM, RPC dispatch, IPC, boot order, Health, the hydrate registry,

retention, WAL / Silica, the supervisor — and the Application API. It is generic: it knows no Concept Model, Source, bench,

room or programme by name. It may be compiled and shipped as a binary; only its own order edits it.

The application layer is ontology/ (packs and .ak), concepts/ (Concept Models in Python and their projections),

source/ (pools, packs, bootstraps, fetch, precompute), workbench/ (the driver: workloads, schedules, provisioning,

admission, states, the LLM gate), config/ (declarations and templates, per package), archives/ (rooms and viewers) and

test/. It is written in Python, .ak, JSON and HTML only. A new Concept Model, a new ontology, a new bench, a new

programme, a new room needs nothing from the heart — and the ontology, archives and GUI implementers never open it.

Rules. (1) The heart exposes one surface, the Application API — atoms, sets, recorder, ops.register,

schedule.register, provision.register, hydrate.register, session (read-only), llm.generate, log — and

nothing else of it is importable; application packages import the API; the heart imports no application package by name, it

discovers them through manifests. (2) Every application package has a MANIFEST.json: what it contributes (ops, schedules,

provisioners, hydrate accelerators, declarations, code paths, data paths, evals) and what it depends on; an implementation is

found by one rule — manifest entry → module:function — and exists in exactly one place. (3) Dependencies form a DAG,

heart ← ontology ← source ← concepts ← workbench ← archives, enforced by an eval; no rightward import, no

function-level import. (4) Deployment is manifest-driven: the seed loader reads the aggregated manifest for what is code

(managed, pruned when stale) and what is data (protected); no path name is compared in code. (5) Boot is a declared phase

sequence — heart, manifests, ontology (→ gate ontology.loaded), source, concepts, provision, hydrate, schedules (each

armed after its declared gate), serve — with one log line per phase and package, phase gates as Set memberships on the boot

epoch, new_build hooks run once per fingerprint, a failed hook degrading its package and never stopping the heart, and no

environment read inside a hook. (6) No if on a name — a bench kind, a society, a package, a path, a programme —

anywhere: behaviour is declared and read. (7) Authority in one place: provisioning runs as admin from one module.

Ownership (maintainer's decision, 20 September). Two roles own the two layers and never share a file. The platform

(backend) owns the heart, the Application API, the engines — ontology loader, Source engine, Workbench driver (schedules,

autorun, provisioning, admission, states, the LLM gate) — Harmonia, the portal boundary, the launcher and seed loader, and

the base classes and mechanism concepts (base, _universal, registry, store, hydrate, cap, claim, chronon, cronon,

lens, workflow, workbench, sweep, society, cast, agent, operator, proj). The development user (frontend) owns

Concept Model definitions (concepts/<model>.py through the API — a bench kind is a Concept Model), ontology

definitions (packs, lexicon, REGISTRY), GUI definitions (archives/), the placement and operation of benches, workflows

and societies (workload declarations, templates, Source declarations, macros), the authoring tree models/, their own evals,

and the shipping of seeds (crystallizer, SEED_MANIFEST.json, Release assets). Every manifest carries owner: platform |

user; user code depends on platform code through the API and base classes, never the reverse; a seed's diff is partitioned by

owner in its delivery note and ownership_eval fails a file whose owner does not match the role that produced it. Where a

user need meets a platform gap, the user writes a one-line order ("needs platform: …"), not a patch; the platform ships no

declaration, template, pack or room. The conformance eval is the contract between the two: a failing declaration is the user's

defect, a failing provisioning line, admission, state write or read shape is the platform's.

Enforcement. wiring_eval (the import graph against the DAG), manifest_eval (every op, schedule, provisioner and

accelerator is one resolving manifest entry; orphans fail), kernel_ratchet_eval (the kernel only shrinks until ≤ 5,000 lines

and holds no domain definitions), authority_eval, deploy_eval, boot_phase_eval, ownership_eval. A layout change

ships alone, changes no behaviour, and is proven by the whole eval suite passing unchanged and by byte-identical guest reads.

A22. Concept Model Lifecycle: Versioned Hypotheses, Experiment

Contracts, Field Evaluation, the Local Repository (extends 6, 7, A1, A2,

A6, A14, A16, A18, A20, A21)

Why. §A18 says what a trial risks and what returns; §A20 says what the driver runs; neither says what the thing is that a

sweep varies, a commitment risks, a residual is about and a repository versions. Taken in 20 September 2026 from the

maintainer's proposal "Human-Guided Concept Model Lifecycle": the Concept Model as an executable hypothesis with an

identity, designed by a human and a language model together, and never generated or tuned by the system in this stage.

A Concept Model is an executable hypothesis. M = ⟨S, B, A, O, θ, P, E⟩: a Source scope, an assumed boundary,

assumed properties and relations, an operand set, parameters, projections, evaluation frames. It declares no final ontology; it

says "read this Source scope by this boundary and these properties, apply these operands, and under these conditions this

behaviour should be observed". It is also an instrument: defining it decides what becomes observable, what becomes a

difference and what is ignored — so its evaluation asks what its boundary made visible and what fell outside, which operands

moved the result, and what was available, visible, considered and acted upon (§A4). A Concept Model is code in the

application layer (§A21) plus a declaration atom cm:<id>@<digest> whose parts are Sets: boundary, properties, relations,

operands, parameter schema, expected behaviour, known limitations, unresolved questions, authoring participants, Source

evidence.

Operand ≠ capability ≠ grant ≠ workflow ≠ effect. An operand is a declaration atom operand:<name>@<digest> — input

scope, parameters, declared operation, expected observation, output contract, deterministic-or-observer, effectful, known

limitations — meaningful inside a Concept Model. A capability is what the running build can execute (§A7); a grant is what a

role may execute; a workflow binds operands to order and state; an effect is what happened in the world. At commitment

(§A18) an operand binds → a capability <name>@<fp8>; effectful stays the capability's mark.

Sources and ontology per experiment. Training, target and evaluation Sets, digests and overlap refusal are §A1 unchanged.

An ontology used by an experiment is a pack generation — content-addressed, published like weights (§A2) — and is a

binding of the branch; changing it creates a new condition, never an overwrite. The ontology distinguishes observed

properties, interpretations, sealed labels, assumed relations, and derived or accelerated memberships.

The experiment contract is the branch. Every element the proposal's contract names — concept_model@digest,

ontology@digest, operand:<name>@digest, pool identity, dataset digests, parameter bindings, observer versions, horizon

plan artifact, role, scope, selection and report frames, budget, chronon — is a cond: Set on the branch marker (§A2). An

evaluation row joins those Sets at mint, so a result without its contract cannot exist. The parameterized question is the

template's parameter space; the driver's axes (§A14) gain boundary, property, relation, operand_composition,

operand_order, ontology_version, source_scope.

Execution. One recorder (§A3) stamps the pins on every coordinate; effectful operands rehearse in thought (§A5); replay

separates state, epistemic and execution layers with declared fidelity. Evaluation is the vector of §A16 under three declared

frames — static_fit (precision, recall, ranking, similarity, relation consistency), dynamic_validity (stability under small

parameter change, Source exclusion, operand reordering, chronon, observer, role and horizon change, transfer to another

Source or domain) and operational_usefulness (§A18's operational frame) — never ranked across frames, never reduced

to one number; candidates with different strengths are retained (§A13), never converged early.

Projection for a human. Version history, branch comparison, score vector as radar or parallel coordinates, boundary

membership difference, operand contribution, Source and ontology coverage, failure and residual browser, lab versus field,

lineage and causal trace — each a derived artifact (§A8, §A12) over Sets, links, scores and artifact identities already recorded,

computing nothing else. Revision is a new version or branch (forked_from, supersedes), never an overwrite: add or

remove an operand, change its order, widen a boundary, revise a relation or the ontology, re-select Sources, add a frame,

change the question. Evidence- assisted revision, not automatic tuning.

Two axes, kept apart. Epistemic maturity — set:cm:maturity:<m> with unexamined · exploratory ·

partially_supported · reproduced_within_scope · bounded · contested ·

operationally_useful_unexplained — is joined by an act with both coordinates and evidenced_by (§A6), optionally

proposed by the review template (§A19), never moved by a score. Operational admission is §A18's level

(thought_only=L0/1, shadow=L1, advisory=L2, sandbox=L3, bounded_use=L4/5, active_workflow=L6). A high

score with irreversible high risk is not admitted; a partly examined model that is low-risk, reversible and observable may be

admitted small. A workload (§A20) that uses a model pins it: pins {concept_model, ontology, operands, datasets,

projection} on the declaration, stamped on every coordinate, refused by the conformance eval when a pin resolves to

current instead of a digest; a new version is a new binding, and past executions are never re-read under a new version.

Field evaluation. Operational use is an experiment under conditions the Thought Lab cannot reproduce (real users, external

systems, time, imperfect observation, changing Sources, cost, organisations). Its results are a frame of their own

(frame=field beside frame=lab), evaluated operationally and epistemically (§A18), and return to authoring as proposals —

boundary, property, relation, operand, parameter, ontology, Source selection, guardrail, new question — as Nebula candidates

and revision material, never applied automatically.

The local-first repository is the registry pattern. What the proposal asks for — immutable snapshot, parent lineage, branch,

tag, log, file-level compare, publish, version pinning — exists as atoms, Sets, links and generations (§A1 registry, §A2

versioned weights, §A8 artifact identity); a second version store beside them would be a second truth. The authoring tree is

real and stays: a local directory models/<id>/{refs,versions/<digest>/…} (never concepts/, which is the Python

package) that a human and a model edit; cm.repo.snapshot reads it and mints the version — files as content-addressed

atoms, a manifest atom, cm:<id>@<digest>, forked_from → parents; cm.repo.publish moves the pointer by CAS;

branch and tag are Sets with pointers; log is the lineage walk; compare is a lens; pin is @<digest>. The manifest's fields

(parents, digests, participants, reason, compatibility) are the version atom's meta; its status is the two Sets above. Not in this

stage: atom-level semantic diff, automatic merge, three-way merge, conflict resolution, automatic upgrade, a Git wire

protocol, copying Source data into the tree (Sources are referenced by identity and digest). Merging is done by people:

compare versions, take what is needed into a new working directory, snapshot with several parents; a model's explanation of a

difference is an interpretation attached to the versions, not the canonical diff.

Command surface (macros): cm.repo.init · status · snapshot · branch · switch · tag · log · compare ·

publish.

Scale and degradation. Identity — model version, ontology version, operand fingerprints, Source Set identities, experiment

lineage, evaluation history — is independent of scale, deployment form and provider (§A8). Without an external model the

versions, ontology, Sets, deterministic operands, cached observations, workflow state and evaluation history remain local and

the loop still runs. Large concept and action models enter as authoring assistants, hypothesis generators, operands, observers,

critics, evaluators, parameter searchers, workflow planners, local or external capabilities — never as a replacement for the

record, the grant, the effect boundary, the stop or the rollback, which stay Akasha's.

Invariants. A Concept Model is never a truth claim; model version, ontology version and operand fingerprints are recorded

separately; a score without its Sources, datasets, parameters and frames is not stored; observation and interpretation are never

confused; overlaps are checked; the vector is never overwritten by a rank; candidates are never converged early; revision is a

new version; thought and execution are never confused; an effectful operand rehearses in the Thought Lab; maturity and

admission are separate; operational success is not ontological truth; lab and field are separate frames; field execution pins its

versions; a run from which nothing returned is not a completed loop; automatic generation or tuning is not assumed; the GUI

is not the only door; the loop runs without network, external model or central server.

First completion. For one Concept Model, one lineage answers twelve questions: which question and evidence the human

and the model designed from; which boundary, properties, relations and operands; which versions were snapshotted; which

Sets were cut from which pool; which questions became conditions; what each branch rehearsed or executed; which frames

gave which vectors; which projection a human read and what they revised; which version went to operations at which risk and

scope; what returned and what the difference was; how it connected to the next model, ontology, operand or question; and

whether the experiment or the decision replays from the same version and chronon. The first lineage is the plants vision model

and the Plant Geek programme: the programme's classifier is the model at a pinned version, its airings are field observations,

its residuals return to the bench.

Stages. P0 — the human-guided local loop (directory format, snapshot and manifest, branch / tag / log / compare / publish,

the contract as branch, version binding to sweeps, operand fingerprints, dataset binding, score vector, manual projection,

human-guided revision, bounded field use, field evaluation recorded) — is the first line of completion and part of the release

gate. P1 — the human-facing Workbench (editors, selectors, grid editor, branch comparison, score visualisation, residual

browser, lab / field comparison, version history, binding and rollback UI). P2 — scale (split execution over large Source Sets,

distributed Harmonia, S3- compatible immutable artifacts, macro-cache integration, package transfer, DTN execution, multi-

node evaluation). A Research Track — draft generation by a model, operand proposals, active parameter search, ontology

candidates, semantic diff, assisted merge, revision proposals from field residuals, guardrail distillation, admission support,

cross-world exchange, controlled self-revision, selective integration of concept, action and world models — stays explicit and

does not gate P0–P2.

A23. Status of the Additions (20 September 2026)

Implemented and verified on the public server (since A10):

  A3  deviation atoms; A6 claims; A2 driver picking, quarantine; S2-k embedding reuse

  A8  effective.at, validity Sets, retention phase; A5 as-of reads (guest-correct)

  A7  cap.ls, offered Sets, effectful attribute, stale_build flag

  A17 stage 1 (pool, reserve, settle), stage 2 (carry-over) live; 429 body kept; R8 persistence

  A20 vocabulary (wb:duty, wl/station states and reasons) and the guide serving state + reason;

      studio provisioning code shipped; log rotation (R9)

  research and station ports on the Workbench (`[port] lab=…`)

Ruled 19–20 September, in progress:

  A21 the heart / application-layer split — one layout seed, no behaviour change (backend order 09-20)

  A20 workloads, duty, one driver — seed A after the layout seed

  A19 review mode; A18 the loop; A22 the lifecycle — track D after the ports (release gate 09-20)

Decisions recorded by the librarian on the maintainer's instruction that implementers must not stall

(reversible by the maintainer): A18 — no system composite, decision frames as declared artifacts;

admission as policy and acts, L4+ moderated; residual as alignment frame; first trial the horizon

plan, then the pick policy; C5 pulled forward as D0.  A22 — repository = registry pattern; authoring

tree `models/`; yaml hypothesis atom with fingerprinted operands; maturity by act; P0 lineage

plants → plant_geek.

Release gate (20 September): nothing ships before the loop — L → A → B → C → D0 → D1 → D2 → G → R.

A24. Observation, Evaluation and Intervention: Trajectories on Chronons

(extends 15, 16, 17, A3, A5, A11, A16, A18, A20)

Why. The Learning Workbench (§A16, PLANTS) already runs bind → observe → feature → train → evaluate → observe

again → diff on a bench, and §A18 returns the consequences of an act as observations. Both treat a changing system — a

classifier, a programme, a model — by occasional scores. This section generalises what PLANTS demonstrated into a

platform primitive: an observation is a point on a Chronon, repeated observation is a trajectory, and the observation itself is

part of the world and therefore has provenance. Taken in 23 September 2026 from the maintainer's proposal "Observation,

Evaluation and Intervention Framework — Chronon-Based Observatory for Adaptive Systems". Nothing here is a new

primitive: every artifact is an atom, a link, a Set membership, a Concept Model or a derived artifact that already exists.

Principle. A changing system should not be evaluated only by occasional scores; it should be observed as a trajectory. And:

observation is never assumed neutral. Akasha does not need to know how a system thinks internally to observe how its

semantic world develops; it needs repeatable coordinates, a clock, and honest records of what was done to the system in order

to observe it.

The observation. An Observation is a relation between a target, a coordinate, a condition, an observer and a Chronon:

Observation { target, chronon, coordinate, observer, mode, condition,

              stimulus, state_before, response, state_after,

              metric, result, provenance }

It is recorded through the one recorder (§A3) on the bench's coordinate, immutable, with the gate's admission stamped in it

(§A26). The coordinate is semantic and belongs to the Concept Model: for a language model causality, temporality,

source grounding, counterfactual, uncertainty; for a vision model object identity, viewpoint, occlusion; for

a robot position, goal, affordance, recovery. The framework knows none of these words; the Concept Model does

(§A21).

Three modes. mode is one of three, and the mode is part of what the target experienced:

O0 — passive. The system's own processing is watched from the side; no stimulus is added. Hidden states, logits,

entropy, attention and gradient statistics, weight deltas, natural inputs and outputs, sensor telemetry. Capture cheaply

in-process; analyse heavily out-of-process.

O1 — probe. A stimulus is given to measure a property: direct question, paraphrase, inverse relation, novel instance,

counterfactual, distractor, source conflict, temporal shift. The coordinate is held fixed; the stimulus varies.

O2 — intervention. The conditions themselves are changed — context, role, source visibility, history, memory,

environment, tools, state, goal, budget — and the causal difference measured.

Observation has provenance. O1 and O2 change the target's experience by definition; O0 can change timing, memory and

execution through its hooks. So every observation records its observer, mode, method, sampling policy, and whether training,

memory and gradients were writable and which execution branch it ran on. Three trajectories are kept apart and comparable:

the model trajectory (what the system did), the observation trajectory (what was done to watch it), the intervention trajectory

(what was done to change it). "Changed by learning" and "changed by being observed" are then two questions with two

answers.

Chronon as the coordinate of change. The Chronon (§15, §A5) is generalised from the society's turn to the common time-

and-state coordinate of any changing system. The same semantic coordinates are observed at C100, C101, C102 …; from

them the platform derives state → delta → trajectory → regime → change point. The epistemic position (§A4) — role,

scope, active Sets, horizon, read budget — is recorded beside each observation, so the record says not only what was seen but

from where.

Delta, trajectory, regime. Δ(C100, C101) is a first-class derived observation; its vocabulary (improved, degraded, stable,

emerged, disappeared, fragmented, recovered) is the Concept Model's. A trajectory is Chronon × coordinate × metric —

a development curve, never one number. A regime (stable phases, transition points, from change-point detection or any other

method) is a derived artifact materialised into the Active Semantic Horizon (§25), regenerable from the observations and

never canonical.

Semantic tomography. The framework does not assume the internal dynamics of a neural model can be read. It observes

repeatedly from many directions and estimates a latent system model, and it names that estimate as an estimate. Two

resolutions can be raised: Chronon density (temporal) and the number of concepts, relations, probes and metrics (semantic).

The epistemic boundary is kept: "we inferred a latent structure from reproducible signals", never "we read the representation".

Observers are plugins. observer.behavior, .logits, .hidden_state, .gradient, .weight_delta, .sensor, .sae,

.human — an interface, not a hierarchy. Sparse autoencoders and every later interpretability technique are one

implementation each, added without a heart change. Cost is tiered: cheap and broad observation → anomaly → expensive and

precise observation.

Open and closed targets. An open-weight model admits O0 + O1 + O2 and optional internal observers; a closed model

admits O1 + O2 only. Closed models are still observed longitudinally — consistency, context sensitivity, counterfactual

stability, source conflict, output distribution — and a provider's silent update ("same name, different behaviour") becomes a

detected change point rather than a rumour.

Observation profiles. An Observation Profile is a Concept-Model artifact that bundles targets, coordinates, observers, mode,

sampling cadence, metrics, thresholds and comparison policy (profile.world_model, .temporal, .causal,

.source_grounding, .uncertainty, .spatial, .affordance, .recovery). The bench template stays the same; the

profile changes what is observed and how it is judged. Under §A27 an operation profile may name an observation profile as

its observe block.

Replay and controlled branching. From one Chronon, replay (§A5) branches the observation conditions — continue

untouched, probe family A, probe family B, intervention C — so the observer effect is itself a subject of study. Effectful

capabilities are rehearsed (§A18): compared without acting on the world.

Statistics are projections. PCA, clustering, correlation, factor analysis, change-point detection, state-space fits, trajectory

classification are never canonical semantics. Observations, Chronons and metrics are the durable truth; analyses are

projections or derived artifacts that can be recomputed by another method from the same observations.

Canonical vs derived. Durable: raw observations, chronons, observer provenance, conditions, branch lineage, metrics,

interventions, outcomes. Derived and regenerable: the current trajectory, regime classification, anomaly list, leaderboard,

statistical projections, visualisation caches, the current semantic profile. Artifact identity follows the existing discipline (§A8,

§A12): universe epoch, scope, chronon/coordinate, input Sets, transform, access context.

Authority stays explicit. Observation → diagnosis → proposal is one chain; authorisation → execution is another. The

observer may diagnose. The trainer may propose. Authority remains explicit. An intervention on a target, and any training

change, passes the one gate (§A26) as run or provision under the actor's assignment, and the human containment boundary

of §A15 is unchanged.

Beyond language models. The same structure — target system → observation point → mode → metric → chronon →

trajectory → intervention → outcome — carries transformers, recurrent and state-space models, vision and multimodal

models, VLA and robotics policies, RL agents, predictive controllers, simulations and sensor-driven adaptive systems. What

differs is the Concept Model and the target adapter; nothing else.

What the heart provides, and only that. Record an observation, stamp a chronon, compare coordinates, derive a delta,

persist a trajectory, branch a replay, dispatch an observer, dispatch an intervention. Meaning-free, fast, and fit to be compiled

(§A21). What to observe, what counts as failure, what constitutes improvement, what should trigger an intervention are the

Concept Model's, the ontology's, the template's.

A25. Workbench Templates: the Catalogue, Model Observatory, Model

Trainer (extends A16, A20, A21, A22, A24)

Why. Most uses of a Workbench are a template. The benches built during the archives experiments — the plants learning

bench, the research notebook, the broadcast studio, the visual-curation and survey benches, the telemetry feeds — differ in

Source, Agent, Role, Workflow, Observation, Chronon, Set and Projection configuration, not in kind. This section names the

catalogue and adds the two templates §A24 calls for. A template is a directory of data (an operation profile it assumes,

workflow files, a declaration skeleton, a page skeleton); an application of web-application scale is a Concept Model + a

template + a GUI, and touches no platform code.

The catalogue.

template

from

profile (§A27)

the loop it carries

learning

the PLANTS

private_lab

dataset → features → train → evaluate → promote, with sweeps

bench

research

the research

private_lab /

sources, hypotheses, evidence, proofs, notes

notebook

seminar

broadcast

the studio

broadcast

turn / react / wrap on a source Set, roles, a room

curation

the visual-curation

private_lab

image corpus → curation layers

bench

survey

the mobility bench seminar

coded survey → deliberation record

feed

telemetry

telemetry_feed

pull → record → map

observatory new (§A24)

private_lab /

bind target → observation profile → observe → chronon → compare → delta

seminar

→ trajectory → regime/anomaly → project

trainer

new (§A24)

private_lab

observe → diagnose → propose → approve → train/adapt → observe again

→ compare

Model Observatory. The developer configures a Concept Model, an ontology, an Observation Profile and a Target Adapter;

nothing model-specific lives in the template. Its outputs are trajectories and regimes for the target's semantic coordinates; its

page is the development curve, not a score.

Model Trainer. Kept separate from the observatory because it acts. Observation and intervention are distinct workflow steps,

both recorded; the proposal step produces a claim (§A6), the approval is a person's act under the gate, the training change is

an effectful capability with the §A15 boundary. For a public open-weight model the strategy is: fix the model, take its

semantic phenotype with the observatory, form a training hypothesis, apply a targeted post-training, observe again — weak-

but-coherent → targeted SFT, unstable distinctions → contrastive training, context or location failure → state-aware

curriculum, composition failure → relational training, regression or interference → replay/rehearsal, miscalibration →

calibration. "Prepare a dataset, run it, read a benchmark" becomes observe → diagnose → design → train → observe again.

World-model observation. For language and world-model research the coordinates are kept apart — world representation,

localisation, goal representation, relation consistency, action selection — so a failure is named (wrong world structure / wrong

current position / wrong goal relation / representation interference / wrong action selection) and the question is never "does a

world model exist" but "which structure formed, when, in what order, how stably".

PLANTS as the precedent. The learning bench is not an example of the observatory; it is its first implementation, built

before the abstraction was named. The abstraction is what PLANTS already did, generalised: observe → learn → observe

again.

Minimal implementation for the next release. The observation schema, the three modes, the Observation Profile, the

observer plugin interface, a metric registry, chronon stamping, delta comparison, the trajectory representation, basic

regime/change detection, replay integration, and the two templates at v1. Not in scope: SAE, mechanistic interpretability,

automatic curriculum generation — each a later plugin.

§A30 generalises this catalogue: the eight templates here are the base templates of the template runtime, and domain

templates compose them.

A26. ID Sets and One Gate (extends 7, 9, A7, A9, A15, A21)

Decision, 22 September 2026. Every permission and every operating condition is decided in one function from data. The

shape is IAM's: a role, groups, permissions on a scope — a bundle is an ID set; an ID set is assigned to an identity by one line

of one file; an agent that connects through a client inherits the client's ID set.

The table (eight rows, eight actions — read · say · run · record · annotate · publish · provision ·

admin): admin (everything, everywhere), librarian (read · run · record · annotate · publish · provision, everywhere; never

say, never admin), programme (read · run · say · annotate · publish, its own workload), researcher (read · run · say ·

record · annotate · provision, its bench), resident (everything but admin, its own cell), member (read · say, its groups),

guest (read, what is public), telemetry (read · run · record, feeds). A new kind of participant is a new row.

The gate. gate(identity, action, target, cast) → ok | reason: (1) the identity's ID set (absent → guest); (2)
action ∈ may; (3) target ∈ on; (4) the facts the action needs — run needs the target ∈ declared ∩ armed ∩ source_ready ∩

headroom, say needs the cast to be a declared role or the speaker itself, publish and a guest's read need public. Each fact is

a Set with one writer. The first missing term is the reason; there is no other reason vocabulary.

One mechanism. The gate is session management: a session's scopes are scopes_for(identity); group membership,

society roles (chairman, scribe, broadcaster, admission) and consent are assignment lines and fact Sets; lineage writes are the

action annotate. No code compares a scope, a role or a flag outside the gate; the store enforces the list the gate produced and

decides nothing. Every admitted effect carries admitted: {identity, action, target, idset} in its observation —

the provenance is the audit trail.

Why. Scattered checks are the hole: each is a second gate nobody listed, and two gates disagree. One table can be read by a

person, enumerated by one eval and changed in one place.

A27. Operation Profiles (extends A20, A25, A26)

Decision, 22 September 2026. Every operating condition of a workload is a field with one owner of its default — the

operation profile — and one place it is read — the merged declaration. A declaration names its profile and overrides what it

must; a profile may lock fields; the merge carries _source per field so a person can see where every condition came from.

The first five: private_lab, open_meeting, broadcast, seminar, telemetry_feed. A profile answers who is admitted as

what (assignment lines), who may see (consent Sets), how it runs (duty, trigger, budget, retry, breaker), what it produces

(effect), what it needs (facts), which governance casts exist, what it outputs and keeps. Six readers of one record; adding a

profile is adding a file. An observe block names an Observation Profile (§A24) for observatory and trainer templates.

The developer's surface. One declaration, one template of turn-shaped lines, one page with two derived reads

(workload.status, feed.read); id.check and profile.check explain any standing-by programme in a minute. Nothing

else.

A28. Status of the Additions (26 September 2026)

Implemented and verified on the public server (since A23):

  A20 workloads on one bench, one driver reading five fields; duty/effect; the ontology.loaded gate

  A21 the heart / application-layer split (layout seed); package manifests with owners

  A26 stage 1 (the gate module, the ID-set table, the assignment file) and stage 2 (sessions and the

      dispatcher on the gate; the eight actions; job.submit as run; the four entrances; the

      cell's own identity files; the consent migration); the resident row

  status belongs to the application: workload.status and society.feed.read as derived reads; the

      programme-guide register and the station vocabulary removed from platform modules

  the driver runs as the workload's declared client; the effect clock; reservations released

      per process; one next-attempt function for driver and status

Decided and in progress:

  platform boundary clean-up (the application names left in the heart, portals, engines and

      system concept models; the application's private calls) — the precondition of A29

  the ontology engine: content-keyed sentinels, per-pack canon plan, ontology.loaded /

      ontology.normalized, memory-bounded reconcile

  A26 stages 3-4 (society row and consent in the table, the driver asking the gate, admitted on

      every effect, annotate)

Decided, held until the boundary clean-up is accepted (A29 sequence):

  A29 reserved concept models (packaging, reserved prefixes and namespaces)

  A27 operation profiles (loader, lock, _source, CLI)

  A24/A25 observation, metric, trajectory; observer and metric registries; replay branching;

      the template catalogue; Model Observatory v1 and Model Trainer v1, PLANTS as the first

  A18/A19/A1/A12/A14 through the reserved model `frame`; A15/A18/A22 acts through `act`;

      A22 through `cm`

A29. Reserved Concept Models (extends 1, 6, A21, A22, A26; decided 23

September 2026)

Why. A Concept Model is an executable hypothesis the application defines after the fact and revises freely (A22). If the

platform depends on one to provide a service, revising it can break the platform; if the application can write a model the

worldview rests on, the worldview bends to one application's convenience. Both are closed by one line: a small set of concept

models is reserved — packaged inside the platform, fixed in meaning, mechanism only — and everything else is the

application's.

Criteria. A concept is reserved if it is part of the world-model foundation the design fixes (atom, link, set; concept and the

concept lattice; operand, operator, agent; chronon, cronon, scenario; the epistemic position; source and observation; society,

agent, role; workbench and workflow; claim, capability, validity, derived artifacts; the word model and its relation core), or if

a platform service (gate, sessions, recorder, driver, provisioning, source engine, ontology loader, dispatcher) needs it.

Otherwise it is application, whoever wrote it. A reserved model contains no application word; its prefix and namespaces are

refused to an application module or pack; its atoms are written only through its own ops, under the gate; it is extended only at

declared plug points.

The set. Existing: base, registry, _universal, store, cache, hydrate, textview, concept, chronon, cronon,

scenario, claim, cap (identity half), agent, cast (role half), society (space half), world (container half), source, labo,

lens, lexbridge, the explore / semantic / horizon / cross / csl / macro ops, whiteboard, log, associate, dream, nebula,

the ingestion half of the I/O pipe, the platform half of the concept schedules, the recording half of pulse, workbench,

workflow, sweep. Ontology: lexicon, base1-base3, scenario; the upper ontology Product, Component, Method,

Producer; the cosmos coordinates. New (for the unimplemented sections): frame (A1 selection and report frames, A12

alignment frames, A14 frame budget, A18 decision frames and residuals, A19 review rubric), act (A15 moderator decisions,

A18 admission, A22 maturity changes), observation, metric, trajectory (A11, A16, A24), cm (A22), effect (A31: the

intent → issued → acknowledged → outcome chain of an egress), and studio (A32: the authoring substrate under the

development GUI, whose pages are the application's).

Growth. The reserved set is expected to grow as the worldview does. Promotion is a procedure: the case (which part of the

worldview it fixes, or which service needs it); a section in this document first; a move with no behaviour change, its prefix

and namespaces reserved and its application parts split off; a seal by eval (mechanism only, reachable only through its ops).

Visible candidates: fact, analysis, rec / table. The maturity path that leads a general concept model to a promotion case

(general → candidate → validated → reserved proposal → system-reserved) is §A30's.

Precondition. The packaging begins only when the current platform-application infiltration is cleared: no platform file names

an application module, prefix or method except through a generated table; no application module calls a private member of a

platform class; no application prefix equals a platform prefix.

A30. Reusable Workbench Templates: the Runtime and the Packages

(extends A2, A20, A21, A22, A25, A26, A27, A29; decided 27 September

2026)

Why. The substrate runs; the next barrier is that a researcher, an archivist, a digital-humanities practitioner or an office cannot

start work without designing the Source intake, the separation of Source and reading, the Concept Models, the ontology, the

roles, the workflow, the observations, the projections, the effect boundary and the replay contract themselves. A template is a

versioned, verifiable starting point for that work — not a worldview. Its user plants a Seed, chooses a template, connects

Sources, and a workbench is provisioned whose every binding can be inspected, replayed and revised.

The decision. The template mechanism is a platform primitive; template definitions are application resources. The platform

interprets, validates, instantiates, records and replays templates; the application writes them. No primitive is added: a template

is a composition of atoms, links, Sets, Concept Models, projections, chronons, workflows, manifests, content-addressed

generations and the one gate.

Two kinds. A Workflow Template is the parameterised .ak of A2 — steps, branches, operands, order. A Workbench Template

is an application package (kind: "template" in the one manifest aggregate of A21) that binds one or more workflow

templates with Concept Models, ontology packs, Source contracts, mappings, operation profiles (A27), observation profiles

(A24), society and roles, projections, page skeletons, evals and migration notes. The eight templates of A25 are the base

templates; a domain template composes them and overrides only fields its profiles leave unlocked.

Layers and owners.

layer

owner

changed by the application

heart / kernel

platform

never

system-reserved CMs (A29) platform

never

template runtime

platform

never

general CMs

application yes; a published version is a new generation

template packages

application yes; a published version is a new generation

template instances

the world

a local override is a new branch

derived views and caches

horizon

regenerated

The runtime understands manifests, dependencies, bindings, the gate, the recorder, versions and projection contracts —

nothing else. It compares no path and no domain word. Its own facts and reasons live in the reserved namespace tpl:.

The manifest. id; version (content digest); owner; title, purpose; requires (platform API, reserved CMs, general CMs

by generation, other packages); provides; source_contracts; ontology (pack generations — the digest of the content

keys the ontology loader's sentinels compute for the pack's files); workflows; one operation_profile per workload;

observation_profile; parameters and defaults; locked_fields; effect_boundary; retention; compatibility

({platform_api: <major>, reserved: {<cm>: <generation>}}); samples ({ref, digest, license,

attribution} — no sample without a licence); migration; evals. A template injects no code: executable steps name

operations, operands, provisioners and schedules registered in application manifests, and every one passes the gate. A

capability the template needs and the platform lacks is a needs platform: line, never a private call.

The runtime. Catalogue listing and search; manifest and dependency-DAG validation; reserved prefix and namespace

protection; generation resolution; Source-contract checks; parameter binding; a dry-run plan, deterministic and shown before

anything is written; provisioning of the workbench, society, roles and workflows (as the installer, under the gate's

provision); profile merge (A27); projection and page registration; the instance contract; idempotence on the second boot;

fork, snapshot, publish, compare; replay and rollback; compatibility and manual migration support. A template may propose

role assignments; it cannot grant itself admin, a grant or publish.

The instance is a branch. An instance records, as Sets its results join: template id, generation and parent; the reserved-CM

and general-CM generations; ontology pack generations; operand fingerprints; workflow template generations; the operation

profile and the source of each override; the observation profile; Source identity, pool, digest and snapshot condition; mapping

generations; workbench, world, society; roles, scopes, consent and ID sets; projections and the horizon plan; parameter

bindings; budget, retention and effect boundary; the creation chronon and universe epoch; author, installer, reviewer. A result

without this contract cannot exist (A22). A new template version never upgrades an instance: compare, read the migration

note, rehearse on a new branch, compare observations and projections, and a person decides; the new binding is a new

instance or a new branch.

Instance state is facts and derivations. Facts, written by the runtime with reason and chronon: planned, provisioned,

source_bound (per contract), conformance_passed, suspended, superseded, archived (the last three are acts). Derived

and never stored: source_pending, ready (provisioned ∩ every contract bound ∩ conformance passed), active (a run in

flight), degraded (ready with a declared capability absent).

Source, structure, meaning, state. A canonical data model is, here, a Source contract, a mapping and an exchange

projection; a mapping is a reversible translation contract that keeps the Source's names, structure, gaps, uncertainty,

conditions, approver and validity period. An ontology is domain vocabulary bound to general CMs; it never rewrites a Source,

and a change is a new generation to which earlier observations stay pinned. A knowledge graph is a projection of the universe,

not a canonical store. Source binding mints a Source identity, records original format, acquisition time, digest and access

condition, checks the contract, offers mapping candidates, records the adopted mapping as a projection, and shows Source and

mapping side by side; a person or a permitted agent adopts. In archival work: the image is the Source; OCR is an observation

or derived artifact; a transcription is an interpretation; an edition is a projection; the reason for a reading is a claim with

evidence; exhibition text is a public projection.

A citation is an input. An observation may name a Source atom only if that atom's text was in the input of the operation that

produced it. The platform's model call records the digests of the atoms it composed into its input (the op passes them as

sources=, not as text it spliced), and the recorder refuses a source outside that record. (Learned 26 September 2026, when a

programme recorded a source its model never received.)

General CMs. Application hypotheses (A22), freely defined, forked and revised; drafts editable, published generations

immutable; versioned apart from Sources, ontology and operands; competing models coexist; templates depend on them by

generation and meet them through mappings and projections, never by merging them into one model. A general CM takes no

reserved prefix and writes no gate fact: a publish decision becomes the publish fact only through an act under the gate. The

initial catalogue to be proven as general CMs: Source–Claim–Evidence, Entity–Identity, Event–Actor–Context, Collection–

Item, Version–Derivation, Observation–Hypothesis (on the reserved observation), Narrative–Perspective, Decision–

Authority (on the reserved act), Rule–Exception, Task (task.*), Metric–Definition (on the reserved metric), Rights–

Access–Consent, State–Transition, Spatial–Temporal. Reusable ontology patterns: hierarchical and faceted classification,

authority record, event-centric, claim–evidence, provenance–derivation, temporal validity, multi-perspective overlay, state

machine, rule–exception, part–whole, crosswalk; every pattern keeps observed property, interpretation, sealed label, assumed

relation and derived membership apart.

Maturity and promotion. general → candidate (reused by several templates or domains) → validated (field observations,

failures and compatibility accumulated) → reserved proposal (the written case of A29) → system-reserved (sealed at a

release). Each move is an act with evidence; usage counts may nominate a candidate, never promote it. Promotion certifies an

operational invariant proven across domains; it is not a judgement of truth. The procedure is A29's, preceded by splitting the

application part off as a general CM and recording conforms_to / supersedes between the old and the reserved model.

Supply chain. Trusted in the first release = carried by the Seed (its fingerprint covers the template digests). Any other

template is checked for owner and digest, dependencies, registered operations only, no reserved namespace, effectful

capabilities, external endpoints, default publicity, retention, provider requirements and eval results, and deploys only in

thought or sandbox mode. Trust levels are Sets written by a provision act of the admin or librarian ID set. Signatures

come later.

The five-minute condition. A reference template reaches its first useful view within five minutes of a fresh Seed only if the

runtime loads the ontology packs the template requires first and lets the rest grow in the background, and only once an

unchanged redeploy opens ontology.loaded in under five minutes (the ontology-engine work). A template that requires the

whole ontology does not claim five minutes.

Evals. manifest completeness and references; the dependency DAG; ownership; reserved namespaces; Source contracts; a

deterministic dry-run; provisioning from a fresh store; idempotence on the second boot; every action through the gate; no

effect in thought mode; replay at the same generation and chronon; degradation without a model or network; no derived view

treated as canonical (including a citation is an input); no upgrade overwriting an instance. A reference template must show

that it was added with no platform code change, builds from a fresh Seed, keeps Source and interpretation apart, pins every

binding by digest, replays a completed workflow, keeps failures and interruptions as observations, reuses its state on the

second boot, does its basic work without a model, and executes no effectful step without a moderator.

Reference templates. First: Archival Accession & Provenance (the first demonstration: accession, rights, a researcher

projection and a public one, a corrected identification with both states kept, replay of an earlier chronon, a fork with a local

field). Then Literature & Evidence Review and Decision & Meeting Record, which reuse benches already running. Source

Transcription & Scholarly Edition and Internal Knowledge Consolidation follow once the first three have shown that the

general CMs are shared. Model Observatory and Model Trainer remain the A25 release target. The first crosswalk is Dublin

Core; RiC-O is the next candidate.

Not goals. Templating every kind of work; automatic ontology generation adopted as canonical; automatic promotion;

automatic or three-way merge and semantic diff; automatic instance upgrade; templates that bring code or permissions; a

knowledge graph as a new canonical store; fully automatic operation by a model as the default; one business vocabulary for a

whole organisation.

Status. Decided 27 September 2026 and held with A29: it starts after the boundary clean-up is accepted and after the gate

(stages 3–4), act, profiles and observation are in place. The one piece taken now is the pack generation digest, part of the

ontology-engine work.

A31. Participants and Source-Mappable Operands (extends 7, 12, A1, A5,

A7, A11, A15, A17, A18, A24, A26, A29, A30; decided 2 October 2026)

Why. "Which clients can connect" is the wrong question. Two classes are needed, and a Workbench and a Society meet them

differently: - participating subjects — humans, model-backed Agents, programs, workflows, devices and other Akasha

instances that observe, interpret, predict, judge, transform or act through the substrate; - resources mapped as Sources and

Operands — documents, datasets, telemetry streams, remote-sensing products, model weights, indexes, observations,

candidate Sets and artifacts that Workflows and Operators act on.

The difference is semantic, not technical. An HTTP endpoint is not a participant by being reachable, and a stream is not an

Agent by being live. Participation is a binding Akasha makes, not a property of a model, endpoint, file or device. A model

file is a Source artifact or an Operand under evaluation. An inference server is an external service. A registered model-backed

entity with a role, a scope, an offer and a record-keeping obligation is a participating Agent. A sensor reading is an

Observation Operand. A gateway that selects, signs or reacts to readings may be a participant. A Sentinel scene is a Source

asset, a change-detection service may be a participant, and its change mask is a derived observation.

position

meaning

participating subject

identity; takes part under role, scope, offer, gate and evidence obligation

position

Source

Operand

meaning

an identified origin or bounded collection through which material enters a Workbench

a semantic or computational object that is selected, compared, scored, transformed or interpreted

Operator / capability a declared operation on an Operand (§A7)

artifact / projection

a derived, regenerable or presentational result (§A8)

The participant binding (in reserved agent, the identity half): - participant_id: stable, independent of the endpoint; -

implementation_fingerprint: weights or version, build, or firmware; for a hosted model, the model and version the

response reports; - participant_kind: generative, decision, retrieval, perception, prediction, symbolic, workflow, human,

device or federation; - deployment: in-process, subprocess, localhost, LAN, self-hosted remote, managed or brokered; -

transport: native, MCP stdio, HTTP, OpenAI-compatible, provider-native, job, or stream; - modalities_in /

modalities_out; - state_model; - offered capabilities (§A7); - effect_class; - the evidence and uncertainty contracts; -

cost_budget; - latency_class; - privacy_class (what material it may receive); - health / fallback; - evaluation facts.

Model family and provider are attributes, not types.

Three rules keep the binding from becoming a second authority: 1. A grant is the gate's answer. It is not a field of the

binding. What a participant may do is gate(participant, action, target) over its assignment line and the grant facts

that acts write (§A26). 2. effect_class maps onto the eight actions: thought-only → none; read → read; propose → say /

annotate; write → record; publish → publish; send or physical action → run of an effectful capability. For an

effectful capability, gate step 4 adds granted (an act: a moderator, or a declared automatic policy, §A15) and

interlock_clear (written by the interlock's owner). No action is added. 3. Sending material out is an egress. Material

given to a participant crosses with it, so the gate checks the material's privacy class against the participant's deployment:

local-only never leaves the node; self-hosted stays on the operator's machines; approved external may go to a

named managed or hosted participant; public may go anywhere.

Further rules: - The pool covers every metered participant. §A17's allocation and the headroom fact apply to any

participant with a cost_budget. - No fallback is silent. A substitute is another participant, used by a declared rule and

recorded on the run. A changed fingerprint behind the same endpoint is a change point (§A25). - In-process participants are

bounded, deterministic and light, because a CPU-bound thread in the writer convoys its I/O (measured 240× on 28 September

2026). The default is a subprocess or a service.

Binding state: - facts, with reason and chronon: discovered, bound, active, paused, qualified, suspended, retired; -

derived, never stored: degraded (a declared capability failing its health check) and disconnected (the last health

observation older than its declared interval).

The typed result. Whatever a participant returns enters the record as one of the recorder's shapes: - a claim (§A6); - an

observation (§A24), of which a score or a probability is one with a typed result; - an artifact (§A8, regenerable and never

canonical); - a witness (evidence linked by evidenced_by); - an error (recorded, never dropped).

Each carries: - admitted (§A26); - the participant's fingerprint; - the digests of its inputs (§A30: a citation is an input; for a

ranking, the candidate pool is an input); - an epistemic kind — observed, predicted, simulated or interpreted.

A prediction is never an observation: it states its horizon, conditions, uncertainty and model, and a simulation states that it

executed nothing real. Embeddings, indexes and rankings are projections. Two close vectors are a candidate, never a fact.

Deterministic participants (validators, solvers, compilers, statistical programs) return witnesses, counterexamples, traces,

bounds or exit codes. A language model may formulate their inputs and interpret their outputs, but it does not replace them

where a deterministic check exists.

The Source / Operand mapping (in reserved source, beside §A30's Source-contract envelope): - source_id, operand_id,

source_locator; - content_fingerprint (hash, ETag, product ID or dataset version); - source_role; -

mapping_direction — ingress, egress or duplex; - the binding facts above; - the observation coordinate: event or

acquisition time, reception time, location or footprint, sensor and reference frame (§A11); - the revision policy; - licence and

access; - derived_from, and caused_by (an observation that may result from an issued command).

The rest are application data: - schema, Concept Model and quality contract; - allowed_operators; - for egress,

effect_target, command_schema, delivery_semantics and the interlock declaration; - retention and export.

External telemetry and remote-sensing sources first produce source-specific observation Sets. Calibration, alignment and

interpretation are later workflow stages, and a claim ("flooding is likely") links to the observations and the Concept Model

that read them. A revised upstream record (a corrected earthquake magnitude, a reprocessed product) is a new observation and

never overwrites the earlier one.

The two directions, and the reserved model effect. - Ingress observes and may propose; it changes nothing outside. -

Egress is always effectful and needs the grant facts above. - Duplex closes the loop: state → sensor → observation →

interpretation and decision → Action Operand → authorised actuator → changed state → new observation.

The new reserved model effect holds the chain as four records, none of which overwrites another: - intent — the Action

Operand, semantic and inspectable before execution; - issued — the command the binding translated it into, with its delivery

semantics; - acknowledged — the endpoint's answer: accepted, rejected, queued, executed or unknown; - outcome — an

observation linked by caused_by.

An issued command is not evidence that the intended effect occurred, and an acknowledgement is not the outcome. Replay

serves the stored records or rehearses (§A5); it never re-issues. The station's X channel is the first egress mapping in

production and the reference: the account is the target, delivery is at most once per turn, the API's response is the

acknowledgement, the visible thread is the outcome, and replay never reposts.

Telemetry. The native recorder is the semantic authority for Akasha's execution. OpenTelemetry traces, metrics and logs are

correlated with it through trace_id, span_id, workflow, agent, participant fingerprint and chronon. Evidence selected for a

claim is promoted into durable records before the operational stream expires (the retention hook, §A8). Dashboards are

projections.

Deployment forms, all behind the same binding: - in-process (bounded); - subprocess / stdio (the default for tools and local

models); - localhost model server (llama.cpp, Ollama, LM Studio, MLX); - LAN or GPU worker (vLLM, SGLang, LocalAI);

- self-hosted remote; - managed dedicated endpoint; - serverless hosted inference; - router or broker, under policy only; -

federated Akasha, which exchanges claims and evidence, not completions.

The first transport is OpenAI-compatible, under the pool. Provider-native adapters remain possible for multimodal, caching,

batch or tool semantics.

Ownership. - Platform: - the binding and registry mechanism; - the typed envelope; - the reserved parts of agent, source

and effect; - the gate facts; - the transports its own services need (the OpenAI-compatible model transport, subprocess/stdio,

HTTP fetch with a provenance record); - OpenTelemetry correlation; - federation identity, when it comes. - Application: -

which participants exist and in which roles; - domain source adapters (OpenAQ, Sensor.Community, OpenSky, USGS,

NOAA, Copernicus, NASA Earthdata, Landsat, JAXA, local sensors and stations); - validators, solvers, rerankers, classifiers

and forecasters as declared capabilities; - actuator bindings and command schemas.

Protocol-generic adapters that are not platform services (STAC, MQTT) start as application packages through declared

extension points (implements:) and may be promoted by §A30's path. Named products are examples, not dependencies. A

product's claims about calibration are provisional until they are reproduced on the bench.

Order.

priority

P0

P1

contents

OpenAI-compatible text/chat/embedding transport; subprocess/stdio adapter; the typed result envelope; the participant binding;

append-only evidence recording; the bidirectional mapping envelope

embedding and reranking as two capabilities; a typed-decision adapter; a deterministic validator or solver wrapper; a passive

ingress adapter (USGS GeoJSON as the reference); OpenTelemetry correlation; effectful egress with grants, interlocks,

acknowledgement and rehearsal (the X channel as the reference); a remote Akasha participant

P2

vision, audio and OCR participants; forecast and anomaly participants; a Thought Lab simulator participant; LAN/GPU

discovery; brokered fallback under policy; a STAC catalogue adapter; public sensor adapters; one duplex closed-loop

demonstration

The next release takes P0, P1 except the remote Akasha participant, and P2's closed loop in rehearsal (§A32).

The starter composition, the release demonstration: - a local language model that reads and drafts; - a hosted model reached

only by escalation; - an embedding capability and a reranker or typed-decision participant; - a solver or validator; - an

observer and a telemetry observer; - an ingress source; - an actuator participant in rehearsal; - an outcome observer; - a human

moderator who holds the grants.

Collective capability comes from the configuration, not from one model.

A32. Status of the Additions, and the Next Release (2 October 2026)

Implemented and verified on the public server (since A28):

  the platform boundary clean-up, platform half: the platform names no application module, prefix,

      method, site or dataset (allow-list 0); no application reach into platform privates; the CLI

      table generated; extension points by `implements:`; the run record the platform's own

  the ontology engine: content-keyed sentinels, per-pack canon, ontology.loaded / ontology.normalized,

      memory-bounded reconcile; an unchanged redeploy opens ontology.loaded in under two minutes

      after the store's replay; a pack load holds only the workloads it touches

  memory: the store's open trims the replay's transient buffers (steady 3.5-3.9 GB)

  the workload record: the stood-by reason carried verbatim; last.ok means the declared effect

      happened; the spent-without-effect guard; pool refusals transient, headroom re-stated

  grounding: a station turn is generated from its item or not at all; continuous broadcast with a

      declared exhaustion rule

Phase 0 still open (the precondition of the campaign):

  application: bench kinds under their own prefixes; the CLI declared on its ops; the world split

  both: an item identity is never reused for another text; the reconcile keeps what the files define

Decided, to be implemented in one campaign (release-procedure-2026-10-02):

  A29 reserved concept models, with `effect` (A31) added to the set

  A26 stages 3-4; A27 operation profiles; acts

  A24/A25 observation, metric, trajectory; Model Observatory and Model Trainer v1

  A30 the template runtime and the reference templates

  A31 participants and source-mappable operands: P0, P1 (without the remote Akasha participant),

      the closed loop in rehearsal

  A1/A12/A14/A18/A19 through `frame`; A22 through `cm`

The next release is this campaign's release gate.

Both series (owner, 2 October 2026). The Workbench GUI — the template catalogue, the dry-run plan, Source binding and

the Source Viewer, instance pages, the status and check views, and the moderator's approval view — ships on the seeds series

as well as the thesaurus series. A seeds build is therefore a no-code environment: whoever plants it can make an application

from a template at once. The seeds series carries its own demonstration data, applications and documents, small and openly

licensed, that work offline and without a model. The thesaurus series' Sources and programmes are not carried over as they

are.

Two doors, one cell. The seeds portal has two entrances that are two projections of the same cell, through the same ops and

the same gate: - /studio/, the no-code development GUI; - /apps/, the app runtime.

The studio stands on the system-reserved concept model studio: the authoring session, the draft, the sandbox binding and the

recorded step log. Every action it offers is an op with a cli entry, called through the same gate as the CLI line. The

development GUI on top of it is the application's, and its appearance may change with the application. It has no op, argument

or state of its own beyond presentation. It is a projection of the CLI, not a second interface.

The bundled demo apps are made in the studio. Their packages hold only what the studio writes, and what it records for each

app is a CLI script that rebuilds it on a fresh cell.

The code path stays open. A Concept Model written as an application module, with pages wired to it in JavaScript through the

same RPC, appears in /apps/ beside the studio-made apps. Neither path has a private door.

On the thesaurus series, /studio/ is a login route separate from the public archives. It admits only identities the admin has

assigned to a studio sandbox, and nothing built there leaves the sandbox except by a publish act.

Why the boundary is held (owner, 2 October 2026). Akasha is open source, but the platform can serve as a foundation only

if its implementation is defended at the boundary. Its position is that of a Unix kernel: - applications reach it through a stable

surface — the ops, the Application API, the public base-class names, the declared extension points and hooks, and data files; -

they never reach it through its internals.

The same line is where the platform will one day be compiled (Cython): what lies behind it may change its implementation

language without any application noticing.

On the other side of the line the application is free: - the look and feel, the development screens included; - templates, general

Concept Models, pages and demo content are the application developer's to change without asking.

Removing every infiltration in both directions in September 2026 was this principle applied. The reserved concept models

stand behind the line. Everything that presents them stands in front of it.

A33. Kernel, Drivers and Plugins (extends 8, A21, A29, A31, A32; owner, 2

October 2026)

Three layers, as in Unix.

layer

what it is

who may change it

compiled

applications

look and feel, the development GUI, templates, general Concept

the application developer,

no

Models, pages, demo content

freely

the kernel

the heart (sessions, identity, the gate, dispatch, the recorder, boot order,

the platform, by release only

yes — the

Harmonia's scheduling semantics, health), the reserved concept models,

future Cython

the Application API, the driver interface

drivers and

everything that binds the kernel to a particular environment: memory

the porter who brings

plugins

and storage substrates, input/output, the execution and host substrate,

Akasha to a target

runtimes

environment, freely

unit

no

The kernel is invariant. However Akasha scales, the compiled part is the same. The same kernel runs on a small IoT node

(one bank on flash, a serial line, no model) and on a distributed cloud deployment (object storage, managed databases,

distributed workers, hosted models). Size, cost, latency and placement are decided by drivers. Meaning, permission and

record are decided by the kernel.

Two stable surfaces. - Upward: the Application API (ops, public base-class names, extension points, hooks, data).

Applications reach the kernel only through it. - Downward: the driver interface (a driver development kit). Drivers and

plugins import only it.

The kernel imports no driver or plugin by name. Drivers are registered by manifest (implements:), exactly as applications

are. The kernel contains nothing specific to an environment — no cloud SDK, no device protocol, no assumption of a local

filesystem, a process model or a network — except what reaches it through the driver interface.

Driver classes. 1. Memory and storage substrate: - the durable semantic store (put_immutable, read, read_range,

publish_generation, resolve_generation, cas_pointer, leases); - the artifact store; - the indexes.

Implementations: the local Silica banks and their write-ahead log, SQLite, S3-compatible object stores, distributed stores,

hardware-accelerated or in-chip memory, mappings onto cloud services. 2. Input and output: - model transports (OpenAI-

compatible, provider-native, local servers); - process and stdio; - HTTP; - streams (MQTT, serial, GPIO, BLE); - source

adapters (ingress, §A31); - actuator bindings (egress, §A31); - federation and delay-tolerant transports. 3. Execution and

host: - where jobs run (threads, processes, LAN or GPU workers, serverless functions); - how the host keeps the cell alive

(launcher, supervisor, watchdog). 4. Plugins: runtimes the kernel calls through hooks — NLP, ML runtimes (TFLite, ONNX),

embedders, solvers.

The driver contract — the storage rule of Chapter 8, generalised: - Declaration. A driver declares its capabilities: for

storage, compare-and-swap, versioning, range read, consistent listing, server time, leases; for input/output, direction, delivery

semantics, acknowledgement, ordering; for execution, isolation and the durability of job state. - Requirement. A deployment

tier declares what it requires. - Comparison. The two are compared once at boot, in one line. A driver that cannot meet a

requirement refuses the tier. It never degrades silently. - Conformance. Each driver interface has a conformance suite. A

driver is admitted when it passes, as a Unix is held to its standard. - Semantics. A driver may change cost, latency, capacity

and placement. It never changes meaning, permission or record: content identity, generations, the gate, the recorder, the effect

chain and replay behave identically over every admissible driver.

Roles. - The platform maintains the kernel, the driver interface, the conformance suites and the reference drivers (the local

Silica store, the OpenAI-compatible model transport, the process transport, HTTP fetch, the current host supervision).

Reference drivers stay outside the compiled kernel like any other driver. - A porter adds drivers and plugins for a target

environment without touching the kernel. - The application chooses, by declaration, which bindings its workloads use.

§A31's transports, source adapters and actuator bindings are drivers in this sense.

Today's code against this line. - lib/akasha/backends/ is storage drivers. - plugins/ (the NLP hook) is a plugin. - The

launcher, the supervisor and cron-heal are host drivers. - The model gateway's provider call is a model transport.

A classification of every platform module — kernel, driver interface, reference driver or plugin — is the first contract of the

campaign that follows (C11).

---

## A34. Workbench and World Reasoning: Plural Projections, Modes, and Validation (extends 11, 14, 19, 25, A4, A6, A18, A19, A29, A31, A32)

**Why.** §11 gives a World where meaning, state, agents and time meet; §19 makes
Projection more than visualization; A18 carries a first-ranked hypothesis out to the
world as a bounded commitment. This section states the step those leave implicit: that
a Workbench does not reason over one knowledge space but **selects, crosses and
compares several World Projections**, and that the projection is not only a constraint
on reasoning but a **subject** of it. The move it records is one sentence: Akasha
advances from a base that stores settled memory to a base that projects the world as
several observation geometries, makes each geometry's freshness, scope, authority,
evidence and compression loss explicit, and keeps hypotheses, refutations, failures and
residuals as first-class results. Nothing here is a new primitive; every artifact is a
Source, an Observation, a claim (A6), a Set membership, a grant record or a Concept
Model that already exists or is already decided.

**Three things kept apart.** The section never conflates:

- a **World Projection** — a shareable world representation whose Source, time, scope,
  transform and loss are recorded;
- an **Agent Reasoning Space** — the internal state an agent forms transiently to
  reason (never identified with a projection);
- a **Workbench State** — the execution context that binds Source, projections, roles,
  grants, workflow, chronon and tools (§14, A20).

**A34.1 A world is plural.** "World Model" here never means one large model. A World
Model is the set of World Projections constructed from the durable semantic universe
for a given purpose, together with their generation, validation and update history.
§19's Projection is generalized: a projection is an *observation geometry* — it defines
what can be observed, compared and verified, not how something is displayed. Typical
geometries (extensible as Concept Models, not a fixed enumeration): physical/spatial,
temporal, organizational, authority/permission, financial/resource, provenance/
evidence, sensor/telemetry, external-system state, policy/regulation, operational
state, social/stakeholder. One Workbench may bind several at once and cross only the
parts it needs.

**A34.2 The Projection Contract.** A projection is a machine-readable Artifact, not an
implicit view. Its contract carries at least: `projection_id`/`generation`, `world_id`,
`purpose`/`scope`, `source_set` with digests, `axis_set`, `transform`,
`observation_time`, `built_at`, `freshness_policy`, `authority_profile`,
`evidence_profile` (provenance, confidence, coverage), `loss_profile`, `access`/
`privacy`, and `status` (draft/active/stale/superseded/invalidated). The contract
guarantees that the inputs and transform can be named, the projection re-built from the
same inputs and version, the observable and the unobservable both described, comparable
projections identified, the distinctions lost to compression shown, and staleness and
regeneration evaluated. The contract is expressed in Atom/Link/Set and introduced as an
ordinary Concept Model; once stable, promotion to a Reserved Concept Model is weighed
under A29's procedure — not before.

**A34.3 Binding, and reproducibility.** At Workbench creation or before a run, the
projections used are **bound explicitly** by digest (a Binding Manifest: bound
projections and digests, required/optional, use = constraint/evidence/context/
comparison/target, allowed reasoning modes, freshness and coverage requirements,
conflict policy, allowed axes and cross-frames, role/grant visibility, fallback). A new
generation of a projection does not silently replace a running run; replacement is an
explicit **rebind**, recorded as a separate run or a resume. A run is thus pinned to the
exact projection digests it reasoned over — the epistemic position of A4, made concrete
for projections.

**A34.4 Compression loss as a first-class fact.** Every projection discards something:
a daily rollup loses sub-day order; aggregation to an organizational unit loses
individual variation; embedding weakens the boundary of negation and condition;
ontology classification hides the unclassified; a permission model confuses practice
with formal rule. The `loss_profile` carries these, and the interface shows not only
what is visible but **what this projection cannot distinguish**.

**A34.5 Three reasoning modes.** The Workbench standardizes three, each mapped to the
authority A18 already defines:

- **Mode A — reason under the world.** Treat the bound projections as constraints and
  plan, explain or choose within them. (A18 L0–L1 by default.)
- **Mode B — reason without selected constraints.** Build a counterfactual with a
  constraint deliberately suspended. The suspended constraint is **not deleted** — it
  is recorded as `suspended_constraint` and carries no authority over reality. (A18 L0
  counterfactual; it cannot by itself cross the effect boundary.)
- **Mode C — reason about the world.** Take a projection's own gaps, staleness,
  misclassification, missing axes or contradictions as the subject. The result is a
  projection-update proposal or a World Change Proposal (A18 L2+), never a direct
  change.

**A34.6 State-space and model-space search.** State-space search explores states, plans
and solutions within one projection; **model-space search** changes the projection,
axes, transform, classification or method of observation itself. Agent evaluation has
leaned on the first; this section makes the second an explicit Workbench capability.
Its output is always a Candidate — it never auto-replaces an active projection. Axis
operations (add/exclude/redefine, cross, regrain, change unit/time window, overlay
authority/provenance/confidence, extract the residual outside a classification) produce
a new generation or a Candidate Projection, never an overwrite.

**A34.7 Three levels of validation.** Each result passes, as far as it can:

- **V1 Local consistency** — no internal contradiction (type, schema, rule, proof,
  critic, unit test);
- **V2 Global satisfiability** — can it hold simultaneously with other projections,
  policies and resources (cross-projection validation, constraint solving,
  simulation);
- **V3 World correspondence** — does it match the observable world (telemetry, human
  witness, external API, canary, outcome observation).

Passing V1 is not passing V3. A result without V3 is shown as an **unverified
hypothesis**, never as truth; *not observed* is never rendered as *passed*. A failing
plan or claim is classified — reasoning error, insufficient evidence, projection
incomplete/stale/mismatch, missing axis/relation, unsatisfied world constraint,
authority/grant violation, external execution failure, outcome divergence — so "the
agent is weak" never hides a defect in the observation design or the world
representation.

**A34.8 Blindness diagnosis.** A Blindness Finding is a distinct Artifact from an error.
Candidate conditions: several agents repeat the same failure on the same input; critics
disagree on conclusion but share the same Source; results swing sharply when the
projection changes; residuals concentrate on one axis; prediction error correlates with
freshness or coverage; an outcome contains a state the projection cannot represent. A
Blindness Finding may *propose* an added Source, an added axis, a new projection or a
changed observation contract; it never adopts one automatically. These feed A19's
falsification review.

**A34.9 Cross-projection work.** Crossing projections is not a join. A Cross-Projection
Frame records the input projection digests, the join/alignment keys, the temporal
alignment rule, unit/taxonomy normalization, missing-value semantics, conflict policy,
output axes, introduced assumptions and the loss profile. Representative crosses: time ×
authority, cost × organizational boundary, geography × logistics, provenance ×
confidence, policy × observed behavior, physical location × permission.

**A34.10 Participants, Sources, Operands (consistency with A31).** A31's distinction
holds unchanged: a Participant is a reasoning subject (human, LLM, non-linguistic model,
agent, workflow, another Akasha, external service, sensor, robot); a Source is read as
observation/evidence; an Operand is read from or acted on, mapped dynamically. One
entity may hold several roles by context but is separated on the record — a sensor is a
Participant and a Source provider; an actuator is a Participant and an Action Operand
target. The standard bidirectional chain is state → sensor → observation →
interpretation/decision → action operand → authorized actuator → changed state → new
observation, and an Action keeps intent / issued / acknowledged / outcome as separate
records (A31). V3 is evaluated chiefly on the outcome observation.

**A34.11 Authority and the cognitive seam.** Counterfactual freedom inside a Workbench
— removing constraints, denying an institution, taking an extreme interest role,
proposing the destructive — never means authority to change reality. Every world change
runs the A18 path: Proposal → Evaluation → Human/Authority/Moderation → Grant → Sync →
Execute → Observation. An agent may generate a Candidate Projection but cannot replace
an active one; promotion requires Source-lineage completeness, a diff from the prior
generation, a loss profile, validation results, an authority policy, rollback, and a
human or a defined Promotion Gate. Because a smoothly-presented conclusion makes a human
lose the boundary of who reasoned, the interface keeps the necessary friction: fact,
inference, hypothesis, proposal and decision are shown apart; AI-generated and
human-confirmed are distinguished; a strong claim cannot be promoted without its
grounds; an override records its reason and its responsible subject.

**A34.12 Standard result types.** A31's typed result is reused with world-reasoning
roles: Claim, Observation, Artifact, Witness, Error, Residual, Proposal. A critic's
judgement is itself a Claim — it records model id, rationale, referenced Source/Gate/
Projection and timestamp, and is treated as a competing claim, never the final
authority.

**A34.13 Operations and templates.** Per the standing rule (A21, A29), conceptual
operations are offered as CLI/Operations and the GUI is their projection; a new command
is not made a kernel primitive, and a compound operation is a Script, Workflow or
Template Macro. The minimal operation candidates — `projection.register` / `.build` /
`.bind` / `.rebind` / `.inspect` / `.cross` / `.diff` / `.validate` / `.blindness`,
`world.reason`, `world.propose`, `axis.propose` — all pass the one Operation Door (A17,
A20) and record run, actor, role, grant, Source digests, projection digests, chronon and
result digest. A `world_reasoning` Workflow template frames the cycle: Frame → Bind →
Preflight → Branch (Mode A/B/C, roles, hypotheses) → Run (under token/cost/time budget)
→ Challenge → Validate → Diagnose → Compare → Propose → Gate → Observe. Structural
diversity — stakeholder role, incentive, scope and horizon, evidence threshold, stance,
removed assumptions, permitted tools and Source visibility, alternative projection
bindings — is a first-class setting, not persona acting; which difference produced which
result is recorded. Long deliberations run on a daily token/cost/API/wall-clock budget,
are recorded as chronons (§17), and replay fast for review or Showtime — and **replay is
not execution: an Action Operand in replay is effect-free**.

**A34.14 The research track, and its boundary.** Promoted only after evaluation in an
explicitly-marked Experiment World (never dropped into the canonical universe): an
embedded Situated Inference Field over the durable memory (graph propagation, constraint
solver, symbolic/statistical hybrid, small or sparse interpretable networks, sensorimotor
predictors — judged on local cost, traceability, incremental update, uncertainty,
projection sensitivity, counterfactual usefulness and embodiment, not on prose); adapters
(LoRA, steering, prompt policy, tool profile) as **versioned Observer/Participant
components** with their own provenance, assigned per run, with implicit continuous
learning forbidden; internal-state observation as a Source, not a self-authority, its
confounders recorded; distributed Source federation by locator, digest, license and
provenance receipt without central collection; and blockchain limited to digest anchors,
signatures, timestamps and consent/revocation receipts — never a truth layer for meaning.

**A34.15 Architecture decisions fixed by this section.**

1. **A world is plural** — a World Model is a set of provenance-linked World
   Projections, not one model.
2. **A projection is an observation geometry** — a contract for what can be observed,
   compared and verified, not a display format.
3. **A Workbench supports state-space and model-space search** — searching axes,
   projections and methods of observation is a formal Workbench operation, not only
   searching solutions.
4. **Validation has three levels** — local consistency, global satisfiability, world
   correspondence are never conflated.
5. **Counterfactual freedom stops at the effect boundary** — thought is maximally free;
   a real change goes only through the existing Proposal/Grant/Gate/Observation path.

**A34.16 Acceptance invariants.** A World Projection never becomes active without Source
lineage. An agent result never changes a projection or the World implicitly. A projection
update makes a new generation and keeps the old. A Workbench run is pinned to projection
digests. V1 is never shown as V2 or V3; *not observed* is never shown as *passed*. A
cross-projection records its alignment rule and loss. A Mode-B result has no real-execution
authority. Replay fires no Action Operand. A critic/validator judgement is a
provenance-linked Claim, not the final authority. No agent or projection widens a grant.
A GUI action has the same meaning as the CLI/Operation/Gate beneath it.

**Non-goals (initial implementation).** Build one complete World Model; give an agent
automatic authority to update the World; make a critic the final arbiter of truth; make
a blockchain the truth layer; make an embedding or a knowledge graph the single index;
bring an embedded inference engine into the current release gate; make GUI-specific state
canonical data; replace human approval with a vague "human in the loop".

**Sequencing (no dates; timing is internal).** The near-term, foundational layer stays
small enough not to expand the current release gate: projection metadata on existing
artifacts (Source digest, observation time, scope, freshness), Workbench projection
bindings, result `validation_level` and epistemic kind, a read-only freshness/coverage
display, and the Projection Contract and Binding Manifest as Concept Model drafts, with a
`world_reasoning` template expressed only as far as the existing Template Runtime allows,
and a read-only Studio Projection Inspector. The fuller reasoning layer (the three modes,
cross-projection, V2/V3, blindness, heterogeneous roles), the thin-client surface (Field
Notes, local-first delayed sync, multi-device continuity, Showtime replay) and the
visualization surfaces follow in a later cycle; the research track (A34.14) is later
still. Each step is evaluated under A19 before any Reserved Concept Model promotion
(A29).

## A35. Status of the Additions (11 October 2026)

A34 is the only addition since A33. It is additive and subordinate to the 2 October
canonical text (A31, A32, A33) and introduces no new primitive. Reference priority is
unchanged: the White Paper (3rd rev.) and this document govern; the Design Memo of 10
October and the Workbench↔World Model note of 11 October are below them; the Additive
Specification is below those. The near-term foundational layer of A34 attaches to the
A32 release gate without expanding it; everything heavier is explicitly later.
