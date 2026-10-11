# The Akasha White Paper

*Concept-Oriented Computing and the Semantic Substrate.*  
*Integrated full text, 11 October 2026 — third edition body plus the new Chapter 18.*

> Provenance note. The body through Chapter 17 (and the Epilogue, Reading the History, Foreword and Acknowledgements) is reconstructed from the maintainer's supplied PDF of the third edition (revised 2 October 2026); its formatting should be reconciled against the canonical source, which governs. The revision-log line and the table-of-contents entry for Chapter 18 have been inserted into that body. Chapter 18, The World Is Plural, is the newly authored addition (11 October 2026); it is the readable account of Foundational Design Context A34, and where the two differ, the Design Context governs.

---

The Akasha White Paper

Concept-Oriented Computing and the Semantic Substrate

Why Akasha was designed this way — the conceptual foundation behind everything in this repository.

Third edition, September 2026. This paper is the readable account of the design. The canonical architectural reference is

Akasha — Foundational Design Context; where the two differ, that document governs.

What changed since the second edition: the Workbench, Workflow, and Chronon chapters now describe what was

implemented and verified on a public server in September 2026 — chronons as Sets, observation coordinates, macros over Set

operations — rather than only the intent; a chapter on the learning workbench reports the first complete observe → learn →

observe-again cycle with its numbers; the substrate chapter separates the durable semantic universe from the active semantic

horizon and states the storage abstraction that follows from it; and a short chapter records the operating rules a public world

taught us. Designs that are decided but not yet implemented are marked as such.

Revised 15 September 2026: the learning workbench chapter now reports the sweep engine as it runs on the server —

parameterized templates, branches named by lineage, conditions as Sets, a leaderboard that is derived state — and what its

first condition taught; the Source section states how a source becomes datasets with roles and how an item's readings are

traced; Chapter 10 adds the execution recorder, deviations, the epistemic position and replay; Chapter 12 adds claims,

capabilities as offered and granted, and the Thought Lab; Chapter 8 adds as-of reads and what keeps a memory active;

Chapter 16 adds the rules of the second week. The corresponding normative text is Part II of the Foundational Design

Context.

Revised 17 September 2026: Chapter 10 adds observation before language and the Nebula; Chapter 12 adds the cognitive

Society and containment — the Cognitive Workbench Extension taken into Part II as §A11–§A16.

Revised 20 September 2026: Chapter 10 adds one Workbench with many duties and the separation of the heart from the

application layer; Chapter 12 adds the examination of a hypothesis; two chapters are new — Chapter 13, Designing a Concept

(the Concept Model as an executable hypothesis and its lifecycle), and Chapter 14, Returning the Consequences (the

Workbench-to-World feedback loop); Seeds and the public-world rules move to Chapters 15 and 16. The normative text is

Part II §A18–§A22; the release gate of 20 September makes the closed loop the condition of shipping.

Revised 26 September 2026: a new Chapter 15, Observing a Changing System, places observation, evaluation and

intervention on the chronon — trajectories rather than scores, the three modes of observation, tomography rather than direct

reading, and the Model Observatory and Model Trainer templates; Chapter 13 closes with the grammar Akasha keeps fixed

(the reserved concept models); Chapter 17 (formerly 16) adds one gate for every permission. Former Chapters 15 and 16 are

now 16 and 17.

Revised 27 September 2026: Chapter 16 adds how a Seed becomes a working bench through a template — the mechanism the

platform keeps, the definitions the application writes, and the instance as a pinned branch; Chapter 13 adds general concept

models and what promoting one into the grammar means; Chapter 17 adds that a citation is an input. The normative text is

Part II §A30.

Revised 2 October 2026: Chapter 12 adds that taking part in a Society is a binding Akasha makes — participants on one side,

Sources and Operands on the other; Chapter 14 adds the two directions of a mapping and what an effect is. The normative text

is Part II §A31; §A32 states what the next release contains.

Revised 11 October 2026: a new Chapter 18, The World Is Plural, gives the readable account of reasoning with, without, and about the world — world representations as several projections rather than one model, the projection as a contract for what can be observed, three levels of checking kept apart, and the rule that a thought experiment's freedom stops where reality begins. The normative text is Foundational Design Context A34; nothing earlier changes.

Abstract

This paper introduces Concept-Oriented Computing, a computational paradigm in which concepts, rather than files,

documents, or database records, become the primary unit of computation.

It presents the architectural principles underlying Akasha, a local-first Concept Operating System and semantic substrate

designed for humans, Large Language Models (LLMs), programs, sensors, and actuators as participants in one semantic

world.

The substrate is deliberately small: Atom, Link, and overlapping Set. Everything above it — Concept Models, Scope,

Projection, Agents and roles, World, Society, Workbench, Workflow, Chronon — is a semantic construction over those three

primitives. The same primitives recur at every scale: they decide what a single memory operation touches, what stays resident

in memory, what travels to another machine, and what can keep working while a network is down.

Unlike conventional software, where implementation determines meaning, Concept-Oriented Computing begins by defining

conceptual structures and lets implementations follow. Workflow and execution state live on the same substrate as knowledge,

so the system remembers not only what is known but how to act and where an action currently stands.

The foundational ideas are not a reaction to today's AI. They originate in knowledge-engineering questions held for roughly

thirty years; contemporary hardware, networks, and LLMs made them implementable. LLMs matter here as a new kind of

first-class client, not as the center of the architecture.

The resulting architecture proposes a durable semantic substrate in which concepts, workflows, browser portals, research

environments, machine learning benches, and future physical participants coexist within a shared conceptual world — and in

which that world can germinate, degrade gracefully, and continue under constrained conditions.

Two further commitments run through this edition. Time is not a clock service: a chronon is a Set, and reading history is

intersection. And memory has two layers: a durable semantic universe that is the only source of truth, and an active semantic

horizon — indexes, caches, projections, materialized Sets — that is an accelerator, disposable, and regenerable from the

universe. Everything the system has learned about surviving in public follows from keeping those two layers apart.

Contents

1. Foreword

2. Chapter 1 — Why Concepts?

3. Chapter 2 — Concept-Oriented Computing

4. Chapter 3 — Atom, Link, Set

5. Chapter 4 — Scope and Projection

6. Chapter 5 — Semantic Pipelines

7. Chapter 6 — Concept Models

8. Chapter 7 — Operand · Operator · Agent

9. Chapter 8 — The Semantic Substrate

10. Chapter 9 — A World That Changes

11. Chapter 10 — World, Workbench, Workflow, Chronon

12. Chapter 11 — The Learning Workbench

13. Chapter 12 — Society

14. Chapter 13 — Designing a Concept

15. Chapter 14 — Returning the Consequences

16. Chapter 15 — Observing a Changing System

17. Chapter 16 — Seeds, Retreat, and Continuity

18. Chapter 17 — Keeping a Public World Honest

19. Chapter 18 — The World Is Plural

20. Epilogue — Toward a Concept-Oriented Future

21. Reading the History

Foreword

Akasha did not begin as an attempt to build another knowledge management system.

Nor another graph database.

Nor another AI framework.

It began with a much simpler question.

Why does software become obsolete faster than knowledge?

During the development of Akasha, one observation became increasingly difficult to ignore.

Concepts often survive for centuries.

Software rarely survives for decades.

The architecture presented in this paper is an attempt to reconcile those different timescales.

The question itself is older than the code.

Most of what follows was first thought through roughly thirty years ago, in the practice of a knowledge engineer working with

Lisp, Prolog, semantic networks, and concept modeling.

The ideas stayed dormant because the machines, the networks, and the deployment environments of that time could not carry

them.

They can now.

The 2026 implementation is therefore not a story of repeatedly changing a design.

It is a story of an old design finally finding its practical boundaries.

The concepts were old. The implementation had to catch up.

Everything that follows emerges from that single question, and from that single distinction.

Chapter 1 — Why Concepts?

For more than half a century, computing has searched for better ways to represent human thought.

Files made information persistent.

Objects made software modular.

Documents made writing collaborative.

Databases made records searchable.

Pipelines made computation composable.

Each abstraction solved an important problem.

Yet none of them describes how human beings actually think.

People rarely think in files.

They remember places.

Recipes.

Faces.

Stories.

Questions.

Ideas.

Concepts.

Modern smartphones quietly revealed this change.

When people tap Share, they are no longer manipulating files.

They are choosing actions for meaningful objects.

The underlying implementation has become secondary to the intention.

Akasha begins where that transition ends.

It treats concepts—not files, documents, or database records—as the primary computational object.

Everything else follows from that decision.

Chapter 2 — Concept-Oriented Computing

Meaning Before Implementation

For decades, software engineering has primarily been concerned with implementation.

Programming languages evolved.

Databases evolved.

Operating systems evolved.

Networks evolved.

Each generation introduced new abstractions that made implementation more manageable.

Yet one assumption remained remarkably stable:

The implementation defines the system.

Tables define databases.

Objects define applications.

Documents define collaboration.

Files define operating systems.

The meaning of information is expected to emerge later.

Akasha reverses this order.

Meaning comes first.

Implementation follows.

A concept is not merely a label attached to data.

It is the stable pattern that persists even as implementations change.

A recipe remains the same recipe whether it is written on paper, stored in a database, or rendered in a browser.

A historical event remains the same event whether represented as text, coordinates, timelines, or relationships.

A scientific observation remains the same observation whether visualized as a table, a graph, or a report.

The implementation changes.

The concept does not.

Akasha therefore treats concepts as the primary computational object.

Everything else becomes an interpretation.

The same semantic space can simultaneously appear as:

a note

a table

a map

a recipe

a browser application

an ontology

an MCP tool

a workflow

a research bench

No duplication is required.

Different representations emerge from the same conceptual substrate.

This principle extends beyond visualization.

Concept Models define how concepts may be interpreted.

Operators define how they may be transformed.

Agents decide when those transformations occur.

The graph itself remains independent of all three.

This separation allows knowledge to outlive software.

Applications become temporary views over concepts rather than permanent containers of information.

Concept-Oriented Computing therefore asks a different question from conventional software engineering.

Traditional software asks:

How should this system be implemented?

Akasha asks:

What concepts already exist, and how should they relate to one another?

Only after those relationships become clear does implementation begin.

This inversion changes the relationship between humans and software.

Domain experts no longer describe requirements for programmers to translate.

They describe concepts.

LLMs no longer invent system structure.

They help materialize existing conceptual structures into executable operators, interfaces, and workflows.

Implementation becomes collaborative.

Meaning remains human.

Concept-Oriented Computing is therefore not a replacement for existing paradigms.

Object-oriented programming remains useful.

Relational databases remain useful.

Functional programming remains useful.

They become implementation technologies rather than conceptual foundations.

Concepts occupy the highest level of abstraction.

Everything else supports them.

Figure 2.1 — From the World to the Screen

The whole architecture can be drawn as a single vertical descent:

                     Reality

                        │   observed and named

                        ▼

                    Concepts            what a thing IS

                        │   interpreted by

                        ▼

                 Concept Models         how it may be read

   ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄  the meaning line  ┄┄┄

                        │   acted on by

                        ▼

                    Operators           how it may change

                        │   rendered by

                        ▼

                 Presentations          CLI · browser · MCP

                        │   assembled into

                        ▼

                  Applications          temporary combinations

Everything above the meaning line is defined by humans and is meant to be stable — it outlives any particular piece of

software.

Everything below the line is implementation. It can be regenerated, replaced, or thrown away — increasingly with the help of

LLMs — without touching what the knowledge means.

This is where Concept-Oriented Computing departs most clearly from the paradigms it grew up alongside.

Figure 2.2 — Where Meaning Lives

Object-oriented design and MVC also draw layered pictures. But read their stacks carefully and the arrow of definition points

the other way:

      OBJECT-ORIENTED  /  MVC                        AKASHA

      ───────────────────────                        ──────

           Interface · View                          Reality

                  ▲                                     │

        Application · Controller                    Concepts

                  ▲                                     │

            Classes · Model                       Concept Models

                  ▲                                     │

            Database schema                         Operators

                                                        │

         meaning lives at the                     Presentations

         BOTTOM — whatever the                          │

         schema permits you to say                 Applications

                                                meaning lives at the

                                                TOP — the software below

                                                is a replaceable view

In an object-oriented system, a class binds data and behavior into one implementation unit; what a "recipe" is becomes

whatever the class hierarchy allows it to be.

In MVC, the Model is already an implementation artifact — a schema, a set of objects. The View and Controller organize the

application around it, but the meaning of the data is trapped inside that application. When the application is rewritten,

meaning has to be migrated out of the wreckage.

In Akasha the dependency is inverted. Concepts are defined before — and independently of — every class, schema, and view.

Applications depend on concepts; concepts never depend on applications. Deleting every application below the meaning line

loses nothing but pixels.

From this perspective, Akasha is not primarily a database, a note-taking application, or an AI framework.

It is an attempt to build a semantic execution substrate where concepts remain stable while implementations continue to

evolve.

The history of computing has repeatedly found better abstractions.

Files.

Objects.

Documents.

Pipelines.

Akasha proposes that concepts may become the next stable abstraction.

Chapter 3 — Atom, Link, Set

The Primitive Substrate

Every large idea in Akasha rests on three small ones.

Atom

Link

Set

Everything above this level is a semantic construction over these primitives.

There is no fourth primitive waiting in reserve for a hard case.

When a new requirement appears, the first question is always whether these three can express it.

Atom

An Atom is the fundamental addressable, persistent unit.

An Atom may take part in representing:

a concept

a note

a quotation

a fragment of a source

an observation

a person

an event

a sensor endpoint

an actuator endpoint

a step of a workflow

a role

an element of the state of a world

The kernel does not require a different storage species for each of these.

The same primitive serves what looks like static knowledge and what looks like a running process.

This is deliberate.

It is the reason a workflow can be remembered the way a fact is remembered, and the reason a sensor reading can sit beside a

definition.

Link

Links connect Atoms and make topology meaningful.

Meaning is not assumed to live only in the payload of an Atom.

It also emerges from relationships, from context, from participation, from the path by which something was reached.

The same Atom can mean differently when reached through different structures.

An apple reached through a recipe is an ingredient.

The same apple reached through a botany reference is a species.

Nothing was copied.

Only the path changed.

Set

Set is the most consequential of the three.

A Set is not necessarily:

a class

a strict taxonomy

a database table

a folder

a mutually exclusive category

Sets may overlap.

A Set may represent a domain, an interpretation, a hypothesis, a semantic neighborhood, a professional rule-space, a

permission boundary, an execution boundary, a unit of distribution, a unit of memory residency, or a temporary working

context.

Because Sets overlap, multiple interpretations coexist without being forced into one canonical ontology.

Figure 3.1 — One Atom, Many Sets

                          ● apple

                          │

        ┌─────────┬───────┼───────┬──────────┐

        │         │       │       │          │

     biology    food   scripture literature technology

       Set       Set      Set      Set        Set

The apple belongs to all five.

Akasha does not decide which one is the true hierarchy.

It does not need to.

Every later mechanism in this paper — Concept Models, Scope, Projection, the semantic macro-cache, distribution across

machines — is a way of asking "which Sets matter right now?"

The answer changes.

The Atom does not.

Chapter 4 — Scope and Projection

The Absent Object

At the level of the API and of explanation, Akasha distinguishes Scope from Set because they communicate different

intentions.

A Set groups meaning.

A Scope grants a client a world.

Internally the important insight is simpler:

Scope and Set share the same Atom–Set geometry.

A Scope is not an access-control list wrapped around objects that are otherwise globally visible.

It is a projection of a semantic Set into a client's accessible world.

This produces a security intuition unlike the conventional one.

Figure 4.1 — Denied versus Absent

      CONVENTIONAL                          AKASHA

      object exists                       client scope

           │                                   │

           ▼                                   ▼

       ACL check                      semantic projection

           │                                   │

      allow / deny                object is present in this world

                                             or

                                  object is not projected at all

A private semantic region behaves, from the point of view of an unrelated client, like a black hole.

It is not visible-but-denied.

It is absent from that client's projected world.

References can be directional.

A private Set may refer to public knowledge without public knowledge referring back into the private Set.

This is what makes the following ordinary rather than exceptional:

private annotation of a public source

personal extension of shared knowledge

research that stays isolated until it is ready

organizational boundaries inside one substrate

secure composition of semantic regions

Projection is the general form of the same idea.

Projection decides what part — or which interpretation — of the semantic world is exposed, and to whom.

It is used for far more than visualization:

access

research isolation

visibility that changes by phase

public and private boundaries

role-specific interfaces

presentation

publication

Public projection and broadcasting are not the same operation.

Research can remain closed while selected results are projected publicly.

The rest of this paper will keep returning to Projection, because it is the mechanism by which one substrate can hold many

worlds without any of them leaking into the others.

Chapter 5 — Semantic Pipelines

From Unix Pipes to Shared Meaning

One of the most influential ideas in computing is surprisingly small.

The Unix pipe.

A single character:

|

It connected independent programs without requiring them to understand one another.

Each program performed one task well.

The output of one became the input of the next.

Data flowed.

Responsibilities remained separate.

This idea shaped generations of software.

As graphical interfaces replaced command lines, the pipe became less visible.

Applications became larger.

Files became central.

Users were expected to move documents between programs rather than compose small tools together.

The underlying operating systems still used pipelines internally, but ordinary users rarely encountered them directly.

For a time, the pipeline seemed to disappear.

It did not.

It simply changed form.

Modern smartphones quietly reintroduced the same idea.

Millions of people now use semantic pipelines every day.

They simply call them Share.

When someone taps the Share button, they are not thinking about files or storage.

They are choosing the next interpretation.

A photograph may become:

a message

a calendar event

a note

a map location

an AI prompt

The object itself remains the same.

Only its meaning within the next context changes.

The user is no longer manipulating files.

The user is navigating intentions.

Akasha extends this principle one step further.

Instead of sharing documents between applications, it shares concepts between operators.

An observation can become:

a research note

a structured record

a map feature

a recipe ingredient

a timeline event

a browser visualization

an MCP tool response

a training example

No conversion is required.

The underlying concept remains unchanged.

Different operators simply interpret it differently.

Figure 5.1 — The Evolution of the Pipeline

     1970s · Unix          2000s · Smartphone           Akasha

     ────────────          ──────────────────           ──────

       Program                    Photo                 Concept

          │                         │                      │

          ▼                         ▼                      ▼

       Program                    Share                 Operator

          │                         │                      │

          ▼                         ▼                      ▼

       Program                 Application            Concept Model

                                                           │

                                                           ▼

                                                      Presentation

    bytes flow             a meaningful object       meaning flows —

    between programs       chooses its next act      every stage leaves

                                                     the concept intact

Each generation kept the composability and moved the unit up one level: from bytes, to meaningful objects, to concepts

themselves.

This changes the role of applications.

Applications are no longer permanent containers of information.

They become temporary windows into a shared semantic substrate.

A browser portal.

A command-line tool.

An LLM.

A visualization.

A workflow engine.

Each becomes another operator acting upon the same conceptual world.

Because the substrate is shared, entirely different interfaces can coexist naturally.

The command

dive France

the browser portal,

an MCP request,

or a future augmented reality interface

may all traverse exactly the same semantic graph.

Only the presentation changes.

The knowledge does not.

Figure 5.2 — One Concept, Many Interpretations

                        Semantic Graph

                              ●

                           "apple"

                              │

          ┌───────────┬───────┴─────┬───────────┐

          ▼           ▼             ▼           ▼

       Recipe     Nutrition     Geography    Ontology        concept models

          │           │             │           │            (interpretations)

          ▼           ▼             ▼           ▼

       Browser      Table          Map       LLM · MCP       presentations

The apple is stored once.

No copy is ever made for the recipe, the table, or the map.

Four interpretations, four surfaces — one atom.

This principle also changes software development.

Traditionally, every new application introduces another storage model.

Another database.

Another synchronization problem.

Another migration strategy.

Akasha instead treats storage as an implementation detail.

The semantic graph becomes the stable layer.

Applications become replaceable.

Interfaces evolve.

Concepts remain.

The same principle scales beyond a single computer.

A person.

An LLM.

A scheduled workflow.

A remote service.

Another Akasha instance.

Each may participate in the same semantic pipeline.

The differences between them become differences in latency, trust, authority, and capability—not differences in architecture.

Whether a result arrives immediately, tomorrow, or after crossing a disconnected network, it remains another contribution to

the same conceptual process.

From this perspective, distributed computing is no longer a separate discipline.

It is semantic computation operating across different scales of time and distance.

This is why Akasha places so much emphasis on queues, jobs, and durable semantic state.

Pipelines should not disappear when a process exits.

They should survive interruptions.

Continue after failures.

Resume on another machine.

Or even continue through another participant.

A semantic pipeline is not merely a stream of bytes.

It is a stream of evolving meaning.

The Unix pipe connected programs.

The Share button connected applications.

Akasha proposes the next step:

Semantic Pipelines connect concepts.

Chapter 6 — Concept Models

The Grammar of Meaning

Concepts alone are not enough.

Knowing that something is a recipe, a historical event, or a legal principle does not yet tell us how it behaves.

Every domain has its own internal grammar.

Recipes have ingredients.

Maps have coordinates.

Organizations have roles.

Stories have characters.

Scientific observations have evidence.

Each domain carries expectations about what relationships are meaningful and what operations should be possible.

Traditional software usually expresses these rules by creating new applications.

Akasha does something different.

It introduces Concept Models.

A Concept Model is not a database schema.

Nor is it a class hierarchy.

It is a semantic interpretation of a region of the graph.

It answers a simple question:

If this concept belongs to this domain, what operations become meaningful?

The graph itself remains unchanged.

Only its interpretation changes.

The same concept may participate in many Concept Models simultaneously.

Consider a single atom representing an apple.

Within different models it may appear as:

an ingredient

a nutritional record

a botanical species

a market product

a symbol in mythology

a geographical export

a point on a flavor map

Each interpretation reveals something different.

None requires copying the underlying data.

Two Directions to a Concept

A Concept Model is the deductive, definitional way to reach a concept.

A human states what a concept is meant to mean and how it should be structured, and the model projects Atoms, Links, and

Sets accordingly.

There is a second direction, and Akasha was designed for both.

Figure 6.1 — Definition and Observation

      DEDUCTIVE · DEFINITIONAL             FUNCTIONAL · OBSERVATIONAL

         Concept Model                     Atoms · observations · relations

              │                                        │

              ▼                                        ▼

     defined semantic structure               co-occurrence and use

              │                                        │

              ▼                                        ▼

       Atoms / Links / Sets                     candidate structures

                                                       │

                                                       ▼

                                             possible Sets / concepts

In the second direction, concepts are discovered through how they participate in the world, not only through prior definition.

Neither direction replaces the other.

Akasha is meant to move freely between them:

definition  ↔  observation

deduction   ↔  induction

model       ↔  use

A Set discovered inductively does not automatically become canonical truth.

It coexists with other hypotheses until humans or agents refine, name, compare, or reject it.

This is one reason Akasha should never converge automatically toward a single universal ontology.

dive

Overlapping Sets have a direct consequence for exploration.

Graph traversal usually assumes that useful exploration means following explicit edges, picking a hierarchy, finding shortest

paths, or choosing a canonical neighborhood.

Akasha's exploration must not destroy the looseness of meaning merely to make navigation convenient.

dive apple

For a concept such as apple, dive encounters overlapping neighborhoods without first forcing the user to choose one

ontology.

Apple

 ├─ Biology

 ├─ Food

 ├─ Religion

 ├─ Literature

 ├─ Technology

 └─ other interpretations

dive is better understood as movement through a sea of meanings than as ordinary tree navigation.

From Loose Meaning to Strict Domains

Akasha does not keep ambiguity and rigor in separate architectures.

A strict professional domain is a special case of Set interpretation in which the constraints have become strong.

loose semantic world

        ↓

overlapping concepts

        ↓

Sets

        ↓

constrained Sets

        ↓

professional domain

Accounting, audit, compliance, engineering rules, or clinical protocols can be expressed without replacing the underlying

semantic model.

Strictness is added through constraints, rules, authority, roles, validation, evidence requirements, and permitted operations.

A human begins in an ambiguous world and learns rules. Akasha should be able to do the same without

changing substrates.

Norms, Authority, Roles

Because Sets can carry constraints and interpretation, normative systems are also semantic.

A normative Set may express what is permitted, what is forbidden, what is required, exceptions, professional standards, audit

criteria, or domain-specific authority.

An auditor is not a special executable type.

An auditor is an Agent connected to an audit role, an authority Set, the relevant knowledge Sets, evidence, and a set of

permitted operations.

The same architecture applies whether that Agent is human, an LLM, a program, or a machine.

One distinction must be kept intact throughout:

Authority and interpretive truth are not the same thing.

A moderator may govern a process without becoming its epistemic ground truth.

That sentence will matter again when we reach Society.

This separation fundamentally changes software architecture.

Instead of building separate applications for each domain,

Akasha builds reusable semantic grammars.

Applications become combinations of Concept Models rather than isolated systems.

The browser portal,

the command-line interface,

an MCP client,

or a future augmented reality interface

all operate on the same concepts.

They simply activate different Concept Models.

Concept Models therefore become reusable building blocks.

A Recipe model can be applied to:

a personal notebook

a restaurant archive

a historical cookbook

a culinary research project

an educational website

The implementation remains the same.

Only the concepts change.

This dramatically lowers the cost of creating new software.

Adding a new domain no longer requires building another application.

It requires describing another conceptual grammar.

Once that grammar exists,

operators,

browser views,

CLI commands,

LLM tools,

and workflows

can emerge from the same model.

This is why Akasha places Concept Models above applications.

Applications come and go.

Interfaces evolve.

Technologies become obsolete.

Conceptual grammars tend to survive much longer.

Human civilization still reasons with concepts developed thousands of years ago.

Software should be designed with similar longevity in mind.

Concept Models therefore occupy the space between concepts and implementations.

They are not merely plugins.

They are semantic contracts.

They define how meaning becomes action.

Figure 6.2 — The Concept Stack

                Reality                    ─┐

                   │                        │   the foundation —

                   ▼                        │   given, not designed

                Concepts                   ─┘

                   │

                   ▼

             Concept Models                ──  the stable layer:

                   │                           semantic contracts

                   ▼

               Operators                   ─┐

                   │                        │   the working layer —

                   ▼                        │   regenerated freely,

             Presentations                  │   increasingly with LLMs

                   │                        │

                   ▼                        │

             Applications                  ─┘

Applications become the outermost layer.

Concept Models become the stable layer.

Concepts remain the foundation.

The further a layer sits from the foundation, the more freely it may be replaced.

Figure 6.3 — One Graph, Many Worlds

                      Semantic Graph

                            │

        ┌───────────────────┼───────────────────┐

        ▼                   ▼                   ▼

     Recipe             Geography           Philosophy        concept models

        │                   │                   │

        ▼                   ▼                   ▼

     Kitchen            World Map          Concept World      worlds (portals)

        │                   │                   │

        └───────────────────┼───────────────────┘

                            ▼

                 Browser · CLI · MCP                          any surface,

                                                              any world

The graph never changes.

Only the conceptual interpretation changes.

Any surface can open any world: the Kitchen in a browser, the World Map from the command line, a Concept World through

an MCP client. The pairing is a choice, not an architecture.

The Browser Is No Longer the Application

This principle led to one unexpected consequence during the development of Akasha.

The browser portals—such as Akashic Kitchen—are not applications in the traditional sense.

They contain almost no domain logic.

Their primary role is presentation.

The conceptual behavior already exists inside the Concept Models.

The browser simply renders the current interpretation of the semantic space.

This separation allows designers and domain experts to create entirely new portals without changing the underlying execution

engine.

The implementation remains stable.

The worlds continue to grow.

Chapter 7 — Operand · Operator · Agent

Separating Meaning from Action

Every generation of software engineering has tried to separate concerns.

Functions separated algorithms from machine code.

Modules separated programs into manageable units.

Objects combined data with behavior.

Services separated systems across networks.

Each step improved software by reducing unnecessary coupling.

Yet one coupling remained largely unquestioned.

The coupling between meaning and behavior.

In object-oriented systems, an object usually owns both.

A customer knows how to update itself.

A document knows how to save itself.

A map knows how to render itself.

Behavior becomes attached to the thing.

This approach has been enormously successful.

But it also means that every new interpretation tends to require changes to the object itself—or another layer of abstraction

around it.

As systems grow, inheritance hierarchies expand.

Interfaces multiply.

Patterns accumulate.

The software becomes increasingly organized around implementation rather than meaning.

Akasha begins from a different observation.

Concepts do not perform actions.

People do.

So do programs.

So do LLMs.

So do sensors.

Concepts simply exist.

This leads to a strict separation between three roles.

Operand

An Operand is the thing being understood.

In Akasha, this is an Atom—or a semantic structure built from atoms.

Operands are intentionally passive.

They do not know how they should be displayed.

They do not know how they should be analyzed.

They do not know who is using them.

They simply preserve meaning.

Operator

An Operator defines an action.

Render a table.

Search for similar concepts.

Project onto a map.

Generate a browser view.

Summarize with an LLM.

Extract a feature vector from an image.

Each operator performs one semantic transformation.

Operators remain independent of the concepts they process.

The same operator can work across many Concept Models.

The same Concept Model can support many operators.

Agent

An Agent decides when an operator should act.

An Agent may be:

a human user

an LLM

a scheduled workflow

a browser portal

a robot

a sensor

another Akasha instance

The Operator does not know which Agent invoked it.

The Operand does not know either.

Each layer remains independent.

This separation creates an unusual property.

Adding a new interpretation rarely requires changing existing concepts.

Adding a new interface rarely requires changing existing operators.

Adding a new type of participant rarely requires changing either.

Each evolves independently.

The result is not simply loose coupling.

It is semantic independence.

Meaning no longer depends on implementation.

Implementation no longer depends on presentation.

Presentation no longer depends on the identity of the participant.

Figure 7.1 — Responsibility Flow

         Agent               decides WHEN — holds intention

           │

           │  invokes

           ▼

        Operator             defines the ACTION

           │

           │  interprets through

           ▼

     Concept Model           defines what is MEANINGFUL

           │

           │  reads · writes

           ▼

        Operand              preserves MEANING — passive

Notice what is missing.

There are no arrows pointing upward.

Concepts never request actions.

Operators never decide intentions.

Agents never alter meaning directly.

Responsibilities flow in one direction.

Multi-Client Is Foundational

Akasha was designed from the beginning as a multi-client semantic environment.

CLI users, browsers, mobile applications, LLMs, sensors, actuators, robotic controllers, and automated programs are all

clients.

A client participates through session and scope mechanisms.

It does not receive a different ontology because of its species.

This becomes especially important for one kind of client.

The LLM Is One Client, Not an Exception

LLM participation was never intended to create a separate "AI world."

An LLM is one client and may become one Agent in the same world as other participants.

It is not privileged because it is an LLM.

It is also not reduced to a chat window, a tool-calling controller, an omniscient narrator, or a free-running autonomous

process.

The Station experiment explored the space between those extremes: LLMs took roles — a news caster, a commentator —

inside a Society, with role, context, turn structure, and social relation shaping what they said.

The point was not unrestricted conversation and not scripted playback.

The point was to test how an LLM behaves as a member.

That experiment is the practical foundation for LLM participation in the World, Society, and Workbench architecture

described later, and Station itself is expected to be absorbed into Workbench rather than remain a separate island.

A Society of Agents

Once Agents become independent, another consequence appears.

Humans and LLMs cease to be fundamentally different architectural elements.

Both become Agents.

One may contribute intuition.

Another may contribute speed.

A third may contribute perception through sensors.

A fourth may contribute deterministic computation.

Each participates in the same semantic process.

Differences become questions of capability, authority, latency, and trust—not architecture.

This principle eventually led to the design of Society.

Society is not primarily a chat system.

It is a coordination model for multiple Agents acting upon a common semantic substrate.

Humans,

LLMs,

scheduled jobs,

external services,

and future physical systems

all become participants in the same conceptual process.

Beyond Object-Oriented Programming

Akasha is not intended to replace object-oriented programming.

Object-oriented programming remains an excellent implementation technology.

Akasha simply places it lower in the conceptual stack.

Objects implement behavior.

Concepts define meaning.

Operators connect the two.

This inversion allows conceptual structures to remain stable even as implementation technologies evolve.

Figure 7.2 — Two Ways of Thinking

        TRADITIONAL                           AKASHA

          Object                               Agent           who acts

       ┌─────────────┐                           │

       │    Data     │                           ▼

       │  Behavior   │                        Operator         what can be done

       └─────────────┘                           │

                                                 ▼

      one unit owns both:                   Concept Model      what is meaningful

      the thing knows how                        │

      to act on itself                           ▼

                                              Concept          what a thing is

   "What methods should                 "What operations become

    this object have?"                   meaningful for this concept?"

The question changes from

"What methods should this object have?"

to

"What operations become meaningful for this concept?"

That single change reshapes the entire architecture.

Chapter 8 — The Semantic Substrate

A Memory That Outlives Programs

Every software system depends on a substrate.

Operating systems provide files.

Databases provide records.

Message brokers provide queues.

Workflow engines provide jobs.

Each abstraction solves a particular problem.

Yet they are usually treated as separate systems.

Applications become responsible for connecting them.

Akasha begins from a different assumption.

Knowledge itself should be the substrate.

Not merely the data.

Not merely the storage.

The semantic relationships between concepts should become the persistent foundation upon which every other service

operates.

This foundation is called the Semantic Substrate.

It is neither a database nor an application framework.

It is a living semantic environment.

Atoms,

links,

sets,

sessions,

jobs,

and operators

all exist within the same conceptual space.

They are different aspects of one substrate rather than independent technologies.

This has an important consequence.

Processes become temporary.

Concepts remain.

A browser may close.

A command-line session may terminate.

An LLM conversation may end.

A server may crash.

The semantic world continues to exist.

Applications become visitors.

The substrate remains.

Traditional software usually asks applications to preserve state.

Akasha asks the substrate to preserve meaning.

The distinction matters.

State belongs to implementations.

Meaning belongs to concepts.

When meaning survives independently,

new implementations become possible without reconstructing knowledge from scratch.

The Semantic Substrate therefore stores much more than content.

It stores continuity.

A concept remembers its relationships.

A session remembers its context.

A job remembers its progress.

An ontology remembers its evolution.

The substrate becomes an external memory for both humans and machines.

This persistence changes how computation itself is viewed.

Instead of treating execution as a sequence of transient function calls,

Akasha treats execution as the gradual transformation of a persistent semantic world.

Every completed operation leaves the substrate richer than before.

Knowledge accumulates rather than disappearing with the process that created it.

Durable Meaning

Durability is usually discussed in terms of storage.

Akasha extends the idea to meaning itself.

Consider a long-running ontology import.

A conventional program may fail halfway through and restart from the beginning.

Akasha records semantic progress.

The import resumes from the last meaningful point rather than repeating completed work.

The same principle applies to graph weaving,

semantic indexing,

projection,

curation,

feature extraction over a corpus of images,

and browser generation.

Meaning becomes resumable.

This principle eventually led to a surprisingly simple observation.

A queue is also knowledge.

A workflow is also knowledge.

An unfinished task is also knowledge.

Rather than treating these as temporary runtime objects,

Akasha represents them inside the same semantic substrate.

Jobs become concepts.

Queues become concepts.

Execution history becomes part of the graph.

This allows computation to survive interruptions naturally.

A disconnected laptop.

A terminated SSH session.

A restarted server.

A suspended mobile device.

None fundamentally changes the conceptual process.

The next participant simply continues.

Harmonia: Execution Above Storage

Akasha deliberately refuses to let a database's concurrency behavior become the conceptual center of execution.

Harmonia coordinates work above the storage engine.

It reasons in Akasha-native units — jobs, steps, workspaces — rather than inheriting SQL locking or another backend's

execution model.

Jobs can be reasoned about through their semantic read and write Sets.

If two operations are semantically disjoint, their Set relationships can tell the scheduler that they may run in parallel.

This is the path toward deterministic orchestration, backend independence, semantic parallelization, resumable jobs, and

eventually placement of work across machines.

One Substrate, Many Engines

The Semantic Substrate deliberately remains independent of its storage engine.

SQLite provides one implementation.

Silica provides another.

Future engines may provide others.

The substrate does not change.

Only the persistence mechanism does.

The two implementations share the same upper interface on purpose, so the memory engine can be replaced without rewriting

the semantic layers above it.

Silica: A Native Semantic Instruction Boundary

Silica is not a reaction against SQLite.

SQLite is a strong implementation and remains the recommended default.

Silica exists because Akasha has long carried another design idea:

Knowledge operations should eventually be expressible at a boundary analogous to a native CPU instruction

set.

The idea dates back to Lisp and Prolog, and to machines such as Symbolics that demonstrated specialized computing at

prohibitive cost.

Fabless hardware development, open instruction sets, and FPGA prototyping make the idea less fantastical than it was.

The immediate goal is not to fabricate a chip.

The goal is a software boundary that could plausibly correspond to native semantic instructions later.

Figure 8.1 — The Instruction Boundary

        Akasha semantic operation

                  │

   ────────────────────────────────────────

     Silica / backend instruction boundary

   ────────────────────────────────────────

                  │

        current software implementation

        possible future:

        native semantic hardware

An Akasha memory operation that would take several database transactions can become one Akasha-native command.

The important question is not only performance.

It is:

What is one meaningful memory instruction for Akasha?

Micro Semantics, Macro Distribution

The instruction boundary has a consequence that reaches far beyond one machine.

The same semantic judgment scales upward.

   MICRO                                   MACRO

   semantic operation                      semantic Set / working context

         │                                          │

         ▼                                          ▼

   native command                          residency / placement

         │                                          │

         ▼                                          ▼

   memory / WAL / execution                cache / node / distribution

The semantic boundary that decides what belongs together in one small operation can also decide what

belongs together in memory, or across machines.

Micro-level operations and macro-level distribution are not unrelated optimizations.

They are two scales of one design idea.

The Semantic Macro-Cache

The semantic macro-cache asks one question:

Can memory residency follow semantic attention?

A conventional cache remembers addresses or recently accessed blocks.

A semantic macro-cache reasons about what the system is working on — what a human reader is viewing, what a workflow is

currently touching — and keeps semantically relevant regions resident.

Sets become natural units for warming, paging, placement, distribution, synchronization, and eviction.

Entering a European research context makes geography, countries, capitals, and the relevant history hot, while unrelated

biology Sets go cold.

The goal is not merely faster lookup.

It is alignment:

meaning

  ↓

attention

  ↓

memory residency

  ↓

execution placement

This is not a performance trick bolted on afterwards.

It is what happens when the Set — the primitive from Chapter 3 — is taken seriously as a unit of computation.

Two Layers of Memory

Running a semantic world on a public server for several weeks made one distinction unavoidable.

Not everything the system keeps is knowledge.

Some of it is knowledge: atoms, links, Set membership, chronons, observations, the commit history that ordered them, the

namespaces and scopes that bound them.

Some of it is machinery for reaching knowledge quickly: the in-memory index rebuilt at boot, the semantic macro-cache, a

materialized intersection, a projection, a compiled traversal structure, a browser snapshot, a leaderboard.

The first kind is the durable semantic universe.

The second kind is the active semantic horizon.

   Durable Semantic Universe

   ─────────────────────────

   atoms · links · definitions

   chronons · observations

   canonical Set membership

   WAL · commit history

   namespaces · scopes

   durable semantic artifacts

             │

             │  materialize · hydrate

             ▼

   Active Semantic Horizon

   ───────────────────────

   active Sets · intersection results

   projections · transform results

   semantic macro-cache · beacons

   session working space · LLM-visible context

             │

             │  discardable

             ▼

   RAM · local SSD · process state

The rule that separates them is one sentence:

A materialized semantic horizon is an accelerator, never the source of semantic truth.

An accelerator may be lost, corrupt, or stale. The system must then fall back to the universe — to the last good generation

plus the visible tail of the commit history, or to a full regeneration — and continue. Nothing in the horizon may be the only

place a fact lives.

This is not a storage policy. It is what makes the horizon disposable: the condition under which memory residency can follow

attention (the macro-cache), under which a device can carry a region of the world and drop it (Chapter 16), and under which a

second machine can hydrate the same world from the same universe.

The consequence for engineering is a discipline rather than a component.

Every structure the system keeps is classified as canonical or accelerator. Every accelerator names the canonical inputs it

derives from, the operation that regenerates it, its cost bound, and the test that proves regeneration gives back the same thing.

Regeneration is idempotent and keyed on the accelerator's own version, never on a coincidental field. The four "backfills" that

appeared during 2026 — for retention collections, for observation coordinates, for chronon Sets, for the compaction calendar

— are instances of one operation that finally has a name: hydrate.

The discipline also fixes cache identity. A derived artifact is not identified by its inputs alone. Its identity includes the epoch of

the universe it was computed against — the commit sequence, or the chronon coordinate of the bench that produced it —

together with scope, transform, projection, and the access context of the reader:

artifact identity =

   universe epoch

 + scope

 + chronon / coordinate

 + input Sets

 + transform · projection

 + access context

A reader compares the artifact's epoch with the epoch of its inputs. A stale artifact is served as "last generation plus visible

tail" and rebuilt, or rebuilt inline under a budget. It is never silently trusted.

Chronon therefore enters memory consistency. A bench artifact keyed by its bench coordinate answers "as of which

execution" for free; a world artifact keyed by the world chronon does the same for synchronization. No new mechanism is

needed — the coordinate Sets of Chapter 10 are the epoch.

The registry that names every accelerator now runs on the server. At boot, after the relations are ready, each entry either

verifies itself against its regeneration or rebuilds, and writes one line saying which, with the epoch it recorded and how many

memberships it had to assign. A verify that assigns nothing is the proof that the accelerator equals its regeneration; a verify

that assigns one is a repair, and the repair is logged, not hidden. The observation layer, the chronon Sets, the macro-cache

plan, the retention collections, the boot index and the sweep leaderboards are its entries. One rule was learned the hard way: a

regenerator enumerates from the canonical atoms, never from an index that only new writes join — the index is itself an

accelerator, and the regenerator backfills it as it goes.

Reading As Of

The universe keeps its history in order. That order can be read.

A Set membership or an atom's meta can be read as of a universe epoch — as it stood at that commit — from the write-ahead

sequence and the immutable generations. Content needs no such read, because content never changes; the horizon gets no

such read, because the horizon is not the truth. This is the one primitive that replay (Chapter 10) needs and the first item of the

storage track. (Decided.)

What Stays Active

The horizon is not a smaller copy of the universe. It is dense: what is currently valid, useful, and influential, not what is

complete. Three semantics keep it so, and each is a Set or a link, not a field.

Validity. An atom that expires — a price, a device state — joins a Set naming the coordinate until which it is valid; the

retention sweep moves expired members out of the horizon and never out of the store. A historical observation joins no such

Set; it does not expire. "Valid when, under which condition, for whom" is an intersection of a chronon range, the condition

Sets and a role's visible Set — a macro, effective.at.

Dependency and contradiction. depends_on and contradicts are links. When a source is retired or superseded, an

accelerator stamps its dependents retired with the reason, using the same word the sweep uses for a condition its grid no

longer covers, so that every viewer already knows what it means.

Value. Access frequency is what the macro-cache plan uses today, and it is not enough. The strength of a beacon is regenerable

from four Sets: how often an atom was revisited, how often it was among the atoms an execution considered when that

execution ended well, the outcome of those executions, and how far away its chronon is. It becomes one residency signal next

to demand. Like every accelerator before it, it runs verify-only for its first week in production before it may move anything.

(Decided.)

To forget, in this vocabulary, is to leave the horizon. Nothing leaves the universe except by a retention rule that names it.

Generations, Pointers, Leases

Large artifacts of the horizon — model weights, a compiled index, a semcache plan — are not updated in place.

They are published as immutable generations, named by content hash, and made current by updating one small pointer with

compare-and-swap:

write immutable generation

        ↓

verify hash

        ↓

publish pointer (compare-and-swap)

Two processes may compute the same generation; the older one cannot overwrite the newer. A superseded generation stays

readable until a retention rule, not a scan, retires it. A registered production model (Chapter 11) is exactly this: an immutable

version and a current pointer.

Ownership of the single writer follows the same pattern. Today it is a run-dir unit, a boot lock, and a watchdog that reaps

orphans. Beneath the abstraction it becomes a lease — acquired, renewed, released — whose epoch is fenced into the write-

ahead log, so that a writer whose lease has lapsed cannot commit.

Storage Is Negotiated

"S3-compatible" is a description of an API, not of behavior.

A backend that answers put and get may still lack conditional writes, versioning, consistent listing, or a trustworthy clock —

and a system that assumes them will corrupt itself quietly. Akasha therefore does not ask a backend what it is. It asks what it

can do.

   Akasha semantic layer

           │

   SemanticArtifactStore     macro-cache · materialized Set · projection

           │                 · index generation · model weights · beacon

   DurableSemanticStore      put_immutable · read · read_range

           │                 · publish_generation · resolve_generation

           │                 · cas_pointer · acquire / renew / release lease

   backend                   local filesystem · S3 / MinIO · distributed

Each backend declares a capability set — compare-and-swap, versioning, range read, consistent list, server time, leases. Each

deployment tier declares what it requires. At boot the two are compared, once, in one log line; a backend that cannot do what

the tier needs is admitted as a read replica or refused, never accepted on faith. The semantic layers above never learn the

backend's name.

This is the second lesson the public server taught. The first was "keep the universe and the horizon apart"; the second is "let

the horizon's storage be replaced without the universe noticing."

Figure 8.2 — The Semantic Substrate

      Human       Browser        LLM        Workflow      Sensor · Actuator

        │            │            │             │                │

        └────────────┴─────┬──────┴─────────────┴────────────────┘

                           ▼

   ═══════════════════════════════════════════════════════════════

                    S E M A N T I C   S U B S T R A T E

           atoms · links · sets · concept models · scopes

           sessions · jobs · workflows · chronons · ontology

   ═══════════════════════════════════════════════════════════════

                           │

             ┌─────────────┴─────────────┐

             ▼                           ▼

   DURABLE SEMANTIC UNIVERSE     ACTIVE SEMANTIC HORIZON

   the only source of truth      accelerators — disposable,

   WAL · canonical Sets          regenerable, epoch-keyed

             │                           │

             ▼                           ▼

                       Harmonia

                           │

                           ▼

              SQLite   ·   Silica   ·   future engines

                           │

           DurableSemanticStore  (capabilities negotiated)

                           │

        local files · object storage · distributed backends

                           │

              semantic instruction boundary

Every participant touches the same semantic world.

Only the interface changes.

Below the substrate, the storage engine and the storage backend are interchangeable; above it, every participant is a peer.

From Memory to Continuity

Traditional software often distinguishes between data and execution.

Akasha deliberately blurs that boundary.

Execution is itself remembered.

Not as logs alone,

but as semantic structures that may be resumed,

reinterpreted,

or continued by another participant.

This is why queues,

sessions,

and jobs belong inside the substrate rather than outside it.

The substrate remembers not only what is known,

but what is still becoming.

Figure 8.3 — Knowledge Outlives Processes

    time ────────────────────────────────────────────────────▶

    Process A      ●────×

    SSH session           ●────────×

    LLM session                  ●──────×

    Browser                                ●─────────×

    Future robot                                        ●─────···

                   │      │      │      │        │      │

                   ▼      ▼      ▼      ▼        ▼      ▼

   ═══════════════════════════════════════════════════════════════

            S E M A N T I C   S U B S T R A T E

                     (never interrupted)

   ═══════════════════════════════════════════════════════════════

Each participant is born and dies on its own schedule.

The band beneath them never breaks.

Processes come and go.

The semantic world persists.

Chapter 9 — A World That Changes

Telemetry, Observation, Action

An ontology can define temperature, sensor, position, pressure, device.

A static ontology stops there.

Akasha was designed from the beginning so that the semantic substrate could map onto a dynamic physical world.

Sensor and actuator integration was not an afterthought.

It was one of the reasons the Atom was made general enough to hold an observation beside a definition.

The telemetry experiment tested this directly.

Figure 9.1 — Observation Enters the World

    physical world

          ↓

      telemetry

          ↓

     observation

          ↓

     Atom mapping

          ↓

    semantic world

Actual readings enter the same semantic world as the concepts that describe them, over time.

The World is not merely described.

It changes.

The reverse direction matters equally.

Figure 9.2 — Decision Leaves the World

   Akasha semantic state

           ↓

   Workflow / decision

           ↓

    Actuator mapping

           ↓

     physical world

Sensor and actuator mapping make the semantic world bidirectional.

A workflow that lives on the substrate can act on the world outside it, and the result of that action returns as a new

observation.

A guardrail for reading the history:

Telemetry did not make Akasha dynamic.

Telemetry experimentally demonstrated the dynamic sensor–world mapping that the Atom was designed for.

The same is true of PLANTS, the first machine-learning bench on the new World architecture, in which a machine observes a

corpus of images, extracts features, trains, evaluates, and proposes — all as observations and records in one semantic world.

The world in Akasha is a place where meaning, state, agents, and time meet.

The next chapter gives that place its structure.

Chapter 10 — World, Workbench, Workflow, Chronon

Where Work Actually Happens

A World is a place where meaning, state, agents, and time meet.

It can contain or coordinate concepts, sources, agents, roles, societies, workbenches, workflows, observations, state changes,

chronons, and projections.

The World existed in the design long before its recent implementation.

What changed in 2026 is that the substrate became strong enough to carry it.

Earlier focus:

"How can a semantic substrate be made real and robust?"

Current focus:

"Now that the substrate exists, what semantic worlds can live on it?"

Source Before Interpretation

A semantic system must keep source material apart from interpretation.

A Source may be a paper, a document, an observation, external data, a frozen acquisition frame, a set of photo references, or

any other evidence.

The Source Viewer exposes source material and its provenance without silently turning interpretation into source fact.

Source

  ↓

Source Viewer

  ↓

observation / selection / reference

  ↓

Workbench

  ↓

interpretation

A shared Source does not imply a shared Reading.

Several Agents can encounter the same Source and form independent interpretations.

This is the whole point of a research environment.

On the learning benches the boundary is kept in a specific shape. A source is imported as a pool — a Set of content-addressed

items with provenance. A dataset is a frozen sample of a pool: a Set with a role, stratified where labels exist, named by the

digest of its members, immutable once sealed. A bench binds three of them — a target to recognize better, a training set to

learn from, an evaluation set the model never sees — and the overlaps are measured at bind time by identity and by content

digest. A target item that turns up in training is removed from training by default: the target judges learning, it does not take

part in it. The target's labels exist as atoms, but no observer reads them; they are an answer key, consulted only by comparison

macros afterwards.

Every item then carries two lists, written when the readings are minted and never computed by a viewer: its observations —

what machines read of it, each with family, observer, model version, run, bench, branch, mode and purpose — and its

interpretations — readings an Agent has bridged to it, with the same coordinates and the version of the observer that produced

the bridged reading. An observation is not an interpretation. The Source Viewer shows both, and where a coordinate is

missing it says so.

Labo

Concept Labo is the research-oriented environment built on the substrate.

It provides a bounded research namespace in which Sources, Concepts, interpretations, comparisons, and histories coexist.

Its principles are few:

interpretation is plural

provenance matters

history is not silently overwritten

views reference rather than copy

research state and public presentation stay distinguishable

Labo is the bridge between the substrate and real intellectual work.

Workbench

A Workbench is the place where an Agent works within a particular world, time, role, and set of tools.

A Workbench is not a domain application.

The same machinery supports machine learning over a plant corpus, an academic seminar, field research, LLM collaboration,

audit, accounting, or engineering.

The domain emerges from the composition of semantic primitives and projections, not from a new backend for every use

case.

A Workbench coordinates:

source access

the operations available

role-specific controls

the current Workflow

the current Chronon

Society membership

private and shared semantic spaces

public Projection

Everything an Agent does at a bench passes through one door, is recorded as one observation on the bench's stream, and is

checked against the roles the Agent holds in the Society connected to that bench.

That door is now real. In the 2026 implementation every bench operation — binding a dataset, extracting features, training,

evaluating, promoting, observing — is one call through one method, which writes the observation before the long work starts

(status running) and finalizes it after. A process that dies mid-operation leaves a visible running observation on the bench's

clock instead of nothing. What a bench did is never reconstructed from logs; it is read from its own stream.

Workflow Is Part of Memory

Conventional architectures separate knowledge from process:

knowledge database

      ↓ reference

workflow engine

      ↓

execution

Akasha does not.

The Workflow itself lives on the Atom network.

Atom network

 ├─ concepts

 ├─ world state

 ├─ workflow structure

 └─ execution state

Therefore a Workflow can be remembered; its execution state can be remembered; execution can be resumed; state can be

rolled back; revisions can be preserved; execution can be transported; and an Agent can, in principle, construct or modify a

Workflow.

Memory does not only remember what is known.

It remembers how to act, and where an action currently is.

Programming can become a form of remembering how to act.

Rollback and Revision

Because Workflow and state share the substrate with knowledge, rollback is not a database recovery trick.

It is part of semantic temporal continuity.

The system preserves previous interpretations, previous workflow states, earlier readings, intermediate execution states,

revisions, failures, and recoveries.

In a seminar, a revised interpretation must not erase a student's earlier reading.

In an automated process, a corrected workflow must not pretend the earlier execution never happened.

History itself is knowledge.

Chronon

Chronon gives the World its temporal and process dimension.

It distinguishes phases, moments, revisions, visibility changes, workflow transitions, and historical states.

It becomes powerful in combination:

Chronon × Projection × Role

          ↓

what this Agent can see and do now

This is how one Workbench can be a closed reading room today and a public exhibition next month without becoming two

applications.

Chronons Are Sets

The second edition described what a chronon distinguishes. The third can say what a chronon is.

A chronon is a Set. A coordinate on a clock is a Set whose members are the records that happened at that coordinate. Reading

history is intersection. There is no clock service, no timeline table, and no special "axis" type — because a special type would

have to be taught to every operator, whereas a Set is already understood by all of them.

Three clocks exist, and they are deliberately different:

   world clock        cronon:world:<w>:c<n>

                      one coordinate per change of the world's state

   workbench clock    cronon:wb:<bench>:c<n>

                      one coordinate per observation at the bench —

                      every execution and every thought experiment

   workflow clock     cronon:wf:<bench>:<branch>:p<n>

                      one coordinate per plan position, per branch —

                      rewindable, branchable, never synchronized

A workflow's clock is a plan. It can be rewound, advanced, and branched freely, because it records what an Agent intends, not

what happened. When a plan step is executed on real material, the execution is delegated to the workbench: the bench mints a

coordinate, and a link executes points from that bench coordinate to the plan position. Executing the same step three times

yields three bench coordinates pointing at one plan position, with nothing in the plan changed.

When a plan step is only rehearsed — a thought experiment — the bench still records it, marked thought, and the link is

rehearses. Thought and execution are distinguishable by membership, and a reader who wants "only what really happened"

takes the complement of the thought Set. A mechanical reset by the system's own driver, made in order to re-run a script, is

part of the execution it precedes; it is not a thought, and it is not recorded as one.

Synchronization exists only between the world clock and a workbench clock — when a bench dispatches something to the

world, when an automatic run completes, when the world is asked to synchronize with a bench. A workflow clock is never

synchronized with anything; that is what makes it safe to rewind.

The daily PLANTS run on the public server mints twenty-six bench coordinates for one seven-block execution and zero

thought coordinates. The line that says so is in the log, once per run.

Observation Coordinates

An observation made by a machine — a classifier's reading of a photograph, an embedding, a learned head's prediction — is

an atom like any other. What makes it findable is that it is a member of every Set a reader might slice by, written at the

moment it is minted:

   set:vlab:src:<item>:obs            everything ever observed about this item

   set:vlab:run:<run>:observations     one observation run

   set:vlab:family:<sense|learned|mock>

   set:vlab:observer:<name>:observations

   set:vlab:model:<sha8>:observations  one model version

   set:wb:<bench>:observations         what one bench read

   set:wb:<bench>:branch:<w>:observations

   set:vlab:mode:thought

   set:vlab:purpose:<bench|precompute|manual>

"The learned readings of this item" is src:<item>:obs ∩ family:learned. "What the plant bench read about it" is ∩

wb:plants_vision:observations. "Before and after" is the item intersected with two runs. None of these is a query; each

is one Set read.

The rule generalizes: a coordinate is a Set the record joins at mint. Bench, branch, model version, purpose, mode, dataset

role, condition binding — every attribute that a reader may want to slice by is written as membership, not searched for later.

The Source Viewer reads these memberships and computes nothing; a missing coordinate is shown as unclassified, never

guessed.

Macros, Not Handlers

If chronons and coordinates are Sets, then most "operators" a reader wants are compositions of Set operations.

Comparing the readings of one run against another; listing the executions of a plan; the timeline of a clock; the

synchronizations between a world and a bench — none of these needs a handler in the kernel. Each is a small script over

lens, s.ls, and within=, saved with parameters and run by name:

macro.run name=observe.diff bench=plants-vision before=o0 after=o1 truth=species_symbol

macro.run name=executions   bench=plants-vision branch=plants_t6

macro.run name=timeline     clock=world:default from=1

macro.run name=sync.between world=default bench=plants-vision

The rule — coarser operators are macros, never direct handlers — keeps the kernel's vocabulary small and keeps every

coarse operator honest: it can only say what the Sets say. A macro that stores its result stores it as an aggregate atom linked to

the Sets it compared, keyed by epoch, so the Source Viewer can show a comparison without re-running it, and so the

comparison can be shown as it stood at any later coordinate.

One Recorder, and the Deviation

A plan step can run inline, as the Agent watches, or as a background job. For a week in September the two paths left different

traces: the inline path annotated the plan entry, minted the bench coordinate and wrote the executes link; the job path ran the

operators and recorded nothing on the plan. A branch had trained a model, evaluated it and promoted an observer, and the plan

said every step was still pending.

The rule that came out of it is simple. Execution that leaves no trace on the plan did not, for the world, happen. One

recorder serves both paths: it annotates the entry with its status and a summary of the result, mints the coordinate, writes

executes or rehearses, and — when the branch belongs to a sweep — moves its condition to done or failed. A write that a

grant refuses is a result too, with its reason, logged once; a background job whose step was refused ends failed, never "done,

nothing written".

With plan and execution both recorded, their difference becomes an object. When actual diverges from plan — a step fails, the

driver rewinds to re-run a script, a step exhausts its budget and continues in chunks, a re-run with identical bindings yields a

different artifact, a parameter is overridden, an admission is refused — the recorder mints a deviation: one atom naming the

kind, the branch, the position, what was planned and what happened, joined to the bench's deviation Set and to a Set per kind

and per branch, linked to the plan entry it deviates from and to the execution it was observed in. Plan, actual and observed

stay three things; the difference between the first two is now something a reader can rank, count on a timeline, and compare

across weeks. What repeats is the operating model the plan did not describe. The quarantine of a failing branch is no longer a

private counter in the driver; it is two members of one Set. (Decided; it lands with the driver's branch selection.)

The Epistemic Position

A world remembers what was true. It should also remember what an Agent could see when it acted — because most wrong

decisions are not wrong reasoning over the right facts, but reasoning over the facts that happened to be in view.

At each execution coordinate the recorder therefore stamps the acting session's position: its role, a digest of its scopes, the

identity of its active horizon plan (the macro-cache plan of Chapter 8, which already has one), a digest of its active Sets, and

its read budget. Every value exists at that moment; the stamp copies identifiers, not content. Two executions that differ only in

the horizon they were given are a legitimate comparison — and, in the Thought Lab, a legitimate experiment.

Four things are then kept apart, as four Sets. What was available: membership in the durable universe at that epoch, read as-

of, never materialized. What was visible: the horizon plan intersected with the session's scopes. What was considered: the

atoms the read core actually served to that execution. What was acted upon: the links the act itself wrote. A missed decision is

the difference of two of them — shown but not read, or hidden by the horizon — computed by the same comparison lens as

everything else. The considered ledger is the one that costs something; it is kept in full only on thought benches, sampled

elsewhere, and evicted from memory with the telemetry. (Decided.)

Retrieval, seen this way, is an epistemic policy before it is a performance policy. What the macro-cache brings into the

horizon is what the Agent can think with. The plan is an artifact with an identity for that reason, and it is written on every

execution.

Replay

If a chronon is a Set, a chronon is also a place to stand. Three things make it possible to go back to one and act again under

different conditions.

The first is a read as of an epoch: Set membership and atom meta served as they stood at a universe epoch, from the commit

sequence and the immutable generations. Content needs no such read — it never changed; the horizon gets no such read — it

is not the truth. (Decided; the first item of the storage track.)

The second is that a replay is a branch. replay.from chronon=… vary=… resolves the coordinate's executes link to its

plan position and branches from the template there, with the original bindings and the variation. The branch's lineage names

the chronon it forked from. Nothing new is named, and the replay ranks on the leaderboard with every other condition.

The third is that replay has layers, and they are declared. State replays through as-of reads. The epistemic position replays

through the stamp, with the horizon plan re-hydrated from its stored generation. Execution replays through the results the

recorder stored, served back instead of re-running an operator. A replay branch declares what it means by "the same" —

semantic, decision, action, or bit-level — and the recorder checks it at each step and writes the result as one more evaluation

row. A capability that reaches outside the world — sending, publishing, a physical action — is marked effectful, and a replay

rehearses it: the stored result is served, the coordinate is minted as a thought, and nothing leaves. Counterfactuals can then be

run in a world that keeps its promises.

Observation Before Language

Most systems that put a language model at their centre also put language at the bottom: documents, prompts, responses,

fragments retrieved into a context. Whatever happened before a sentence was formed — a repetition nobody has named, an

observation that fits no category, a weak similarity, two observers disagreeing, a candidate rejected before it was said — is

lost by the time the sentence exists. When such a system fails to make a conceptual leap, one cannot tell whether the model

could not, or whether it was given nothing to leap from.

Akasha's observation layer does not require language. A probability distribution, an embedding, a prediction error, a spike

train, a cluster, a slot, an anomaly score, a time-series state — each is an observation bundle: what one observer formed in one

pass, stored as one atom with its coordinates and, when it has a body, a content-addressed artifact. The coordinates are the

ones the vision layer already writes — source, observer, version, run, bench, branch, mode, purpose, chronon — and a few

more: the layer the bundle sits at (signal, residual, feature, bundle, proto-object, proto-concept, concept, interpretation,

language — a frame, not an ontology), the modality, the transform, the representation type, and a status that includes absence:

an observer that looked and found nothing writes that down.

Comparison between unlike observers is paid for before any reasoner arrives. Alignment in time and space, conversion

between granularities, distribution comparison, neighbourhoods, agreement and disagreement between observers, deltas

between prediction and observation — each is a derived artifact with an epoch and an identity, registered in the hydrate

registry and regenerable from the observations. The rules are the ones the substrate already imposes: an alignment never

overwrites an observation; an aligned representation is a projection, not a source fact; several frames coexist; nothing ranks

across frames; the transform and its loss are recorded; staleness is shown; a value filled by inference is marked and is not an

observation. Making things comparable must not become making them one.

The Nebula

Between an observation and a concept there is a region the system has always had a name for. nebula is Akasha's third

explorer — after assoc, which fills a local gap, and dream, which proposes a pair — the one that surveys the whole universe

for regions that have grown the same relation schema and proposes them as a concept in the making. The machine proposes; a

person confirms and names.

What widens now is what may enter it. A weak association. An unnamed cluster. An anomaly no frame explains. Two

boundaries that compete for the same items. A provisional relation. A contradiction left standing. A hypothesis with no

positive result yet. A minority reading. An alternate frame. A candidate Concept Model. Each joins a Nebula Set by kind, at

the moment it is formed, by whoever forms it — an Agent, an observer, an alignment macro — and carries the links the rest of

the world uses: observed in, derived from, supports, contradicts, depends on, predicts, explains, forked from, superseded by,

evidenced by.

Nothing in the Nebula is merged by a score. Promotion to a concept is an act, declared and judged, or a policy a bench

declared in advance; after promotion the candidate and its formation history remain, linked to what it became. A candidate

that no current frame can measure is kept, not deleted for being unmeasurable. The Nebula is where a concept's history is

legible before the concept exists — which is the only time that history can still be recorded.

Two Activities, One Substrate

Two very different activities are being built on this architecture.

Figure 10.1 — Machine Work and Human Work

    PLANTS                                    Radu seminar

    a machine works                           humans work

    in a semantic world                       in a semantic world

    sources:  photo references, checklist     sources:  two papers

    agents:   observers, learners, a driver   agents:   moderator, students, an observer

    workflow: bind → extract → train →        workflow: read → annotate → submit →

              evaluate → promote                        compare → discuss → revise

    output:   a learned observer, and two     output:   preserved readings, old and revised

              readings of every target item

The difference is in Sources, Agents, Roles, Workflows, Projections, and tools.

The substrate is the same.

The machine's half has run to completion, daily, on a public server, since September 2026; the next chapter reports it. The

seminar is the next human use case. If both succeed, Akasha will have shown two unrelated kinds of work without two

unrelated backends.

One Workbench, Many Duties

For two weeks the same Workbench ran a learning bench and a broadcast station, and the two were run by two arrangements:

a society with a bench of its own name and a workflow called main on one side, a station with its own daemon, its own timer

and its own counters on the other. The driver knew the first. When a new programme was declared in the second shape and

the driver tried to run it in the first, it found a bench that did not exist and a workflow that was never written, and stood by.

Each repair had been a branch on a name — is this a station, is this society the news — and the branches were becoming the

design.

The ruling is that there is no research mode and no operations mode. The unit the driver runs is a workload: one workflow on

one bench, acted by one society, declaring five things — when it triggers, what duty it owes, what effect it has, what appetite

it brings to the model gate, and what budget stops it. A research sweep, a reading programme and a payroll run are three

workloads that differ only in what they declare; a programme is nothing more than a workload with a continuous duty and a

publishing effect. Every declared value is a Set the workload joins, so "every continuous workload that publishes" is an

intersection and never a scan of configuration files.

Duty is the one behavioural switch. A best-effort workload — the default, and right for research — stops when a gate stops it,

comes off the schedule after repeated failure until someone looks, and owes nothing at boot; a run that produced nothing is a

run that produced nothing. A continuous workload — a programme, a business process — must never go silent: any stop

writes a state and a reason, the breaker never unschedules it, one run is owed at boot, and a run that produced nothing leaves

the previous airing on the air until the next trigger. The states are vocabulary, one membership at a time, and a rebroadcast is a

state and never a new airing — no model call, no reservation, no atom. The driver reads the five declarations and nothing else:

not a bench's kind, not a society's name, not whether a programme file exists. An evaluation greps it for the forbidden

comparisons.

Provisioning gives every workload its workflow, on the bench the declaration names, at boot, idempotently; a declaration

without a template is a boot error, not a programme "left alone". The test of the design is a workload it was not written for:

adding a payroll run is a template, one declaration, a society with a moderator and a grant with an expiry for the effectful step.

If it needs a branch anywhere, the branch is the defect. A generic conformance evaluation runs the same checklist for every

workload — provisioned, run once, coordinates, observations, state, guide row, second boot unchanged, refusal with a reason,

effectful step rehearsed in thought — so a new function ships with a declaration, a template and one evaluation, not a bespoke

test and a week of fixes. (Ruled 20 September 2026; Part II §A20.)

The Heart and the Application Layer

A design that separates operand, operator and agent should also separate the generic from the particular in its own code, and

for two weeks it did not. The kernel had grown to eighteen thousand lines: the timers of every function, the provisioning, the

station's daemon, the bench driver, the ontology loader, and a hundred and sixty-nine request handlers behind a chain of a

hundred and twenty-eight comparisons, reaching into the Concept Models from inside its own methods. A new Concept

Model, a new ontology, a new bench or a new room could not be written without opening it.

The rule is two layers and one direction. The heart — sessions, identity, dispatch, inter-process pooling, boot order, health, the

hydrate registry, retention, the write-ahead store, the supervisor — is generic and knows no Concept Model, Source, bench,

room or programme by name. It may be compiled and shipped as a binary, and only its own order edits it. The application

layer — the ontology packs, the Concept Models, Source management, the Workbench driver, the declarations and templates,

the rooms, the evaluations — is written in Python, the script language, JSON and HTML, and needs nothing from the heart. A

person who defines a concept, an ontology, a bench or a page never opens the kernel; that is what makes it possible to give

those layers to different hands.

The heart exposes one surface, the Application API — atoms, Sets, the recorder, registration of operations, schedules,

provisioners and accelerators, a read-only view of the session, the model gate, the log — and nothing else of it can be

imported. It imports no application package by name; it discovers them through their manifests. Every application package

carries a manifest that says what it contributes and what it depends on, and an implementation is found by one rule: manifest

entry, module, function, and only there. Dependencies form a directed acyclic graph the evaluations enforce. Deployment

reads the aggregated manifest for what is code and what is data, and compares no path name; boot is a declared sequence of

phases — heart, manifests, ontology, source, concepts, provisioning, hydrate, schedules, serve — each hook registered by a

manifest, each phase gated by a Set membership so that a sweep does not pick while a pack is loading, each line in the log. No

code branches on a name.

Two roles own the two layers, and they never share a file. The platform — the backend — owns the heart, the API, the

engines, the base classes and the mechanisms; the development user — the frontend — owns the definitions of concepts,

ontologies and pages, the placement and operation of benches, workflows and societies, the authoring tree, and the shipping

of seeds. Every package manifest names its owner; user code depends on platform code through the API and never the

reverse; a seed's changes are partitioned by owner in its delivery note and an evaluation fails a file whose owner does not

match the hand that wrote it. When a user need meets a platform gap, the user writes a one-line order, not a patch. The

conformance evaluation is the contract between them: a failing declaration is the user's defect, a failing provisioning line or

read shape is the platform's. The platform is a product; the development user builds on it without opening it.

The reason is the one that made operating systems possible. A kernel can serve as a foundation for programs written by

strangers only if what it does is reached through a stable surface and its insides are reached by nothing. Akasha's platform sits

in that position. Its code is open to read, but an application touches it only through operations, the published interface, the

public names of its base classes, declared extension points and data. That line is also where the platform will one day be

compiled into another language without any application noticing. On the near side of the line, the application has full

freedom, and is meant to: how everything looks, the screens on which applications are built, the templates and the concept

models of each domain all belong to whoever builds on the platform, and changing them never requires opening it.

Below the line there is a second freedom, also as in Unix: drivers. Whatever binds the kernel to a particular world — where

memory is kept (local banks, a database, object storage, a distributed store, memory built into a chip), how input and output

travel (a model service, a process, a serial line, a message bus, a satellite archive, an actuator), where jobs run and how the

host keeps them alive — is a driver or a plugin, written against a stable driver interface by whoever ports Akasha to that

world. Each driver states what it can do; each deployment states what it needs; the two are compared once at boot, and a

driver that cannot meet a need refuses rather than pretending. A driver may make Akasha smaller or larger, slower or faster,

cheaper or dearer. It may never change what anything means, who may do it, or what is recorded. That is why the compiled

kernel can be the same on a sensor node and across a cloud: everything that differs between the two lives below it, and

everything that differs between applications lives above it.

A layout change ships alone and changes no behaviour; it is proven by the whole evaluation suite passing unchanged and by

byte-identical reads from a guest. The kernel only shrinks until it is under five thousand lines, and stays there by an evaluation

that fails when it grows. (Ruled 20 September 2026; Part II §A21; the layout seed is the first step of the release sequence.)

Self-Programming, Carefully

Because Workflow is represented on the Atom network, an Agent can reason about executable process semantically.

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

revise or roll back

This is not "an LLM writes source code and runs it."

An Agent acquires a new way of acting by constructing a new remembered Workflow — with history and rollback intact.

The substrate provides a basis for controlled self-modification.

It is a foundation, not a claim that unrestricted self-programming is solved.

Chapter 11 — The Learning Workbench

Observe, Learn, Observe Again

PLANTS is the first workbench on which the whole World architecture has been exercised end to end by a machine, without

an operator, on a public server.

It is deliberately small. Twenty plant species. One thousand photo references, frozen as one pool. A generic image embedding

that runs on a small CPU. A linear classifier. The point was never the botany. The point was to find out whether a bench, a

workflow, a society's driver, the source layer, the chronons, and the Source Viewer could carry a complete learning cycle —

and to find every place where they could not.

The Shape of the Cycle

A learning cycle on a workbench has a fixed shape, and the shape is the template every later learning bench follows:

   T1  bind      the datasets, by role

   T2  observe   the TARGET with a learning-free observer        →  o0

   T3  feature   extract embeddings from the TRAINING set        →  f1

   T4  train     a head on f1, with a held-out frame inside it

   T5  evaluate  the head on the held-out frame; promote it as an observer

   T6  observe   the same TARGET with the learned observer        →  o1

   T7  diff      o0 against o1, per item and in sum   (a macro, not code)

Two ideas carry the design.

The target and the training set are different datasets — frozen, stratified samples of the pool, disjoint by construction, each a

Set with a role. The target's labels exist, but no observer ever reads them; they are an answer key, consulted only by the diff at

the end.

And the two observations of the target are two coordinates of the same items. Before: what a general-purpose classifier

trained on ImageNet says a plant photograph is. After: what the head trained on this bench says. The difference per item is an

intersection; the difference in sum is one aggregate atom, stored and linked to both runs.

What Stage One Proved

On 10 September 2026 the seven blocks ran to status=ok on the public server, and have run every day since, unattended:

   target       400 items, 20 species        (a stratified sample)

   training     600 items                    (the complement)

   o0           litert · ImageNet labels     e.g. "stupa 0.082", "buckeye 0.199"

   f1           mobilenet · 1,024-d embeddings

   train        sklearn logistic regression  · 20 classes

                held-out frame (120 items)    accuracy 0.2167 · macro-F1 0.1595

   o1           plants_head_f1 · species labels

   diff         items=400  changed=399  agree_before=0  agree_after=93

Read the last line honestly. Agreement before learning is zero: ImageNet has no plant species, so it cannot agree with a

species key. Agreement after learning is 93 of 400, or 0.2325, on a target the training never saw — consistent with the 0.2167

measured on the held-out frame. The two numbers agreeing is the result. It says there was no leak between training and target,

and that what the bench measured is what a reader can see.

The accuracy itself is low, and should be: thirty images per species, a linear head on a generic embedding, no tuning. It is a

plumbing figure. It will be the first thing the platform described below changes.

The second run, the next day, re-observed nothing. Every block is idempotent on its inputs — the same pool, the same

observer, the same model version yield the same observation atom, and the run records that it reused it. A daily rerun of an

unchanged bench costs thirty seconds and adds no observations. When the model changes, the old readings stay and the new

ones join a new model coordinate.

And the Source Viewer shows it. A target item's page lists a learning-free reading and a learned reading, each with its run,

bench, branch, model version, and chronon position; a training item says it has no learned reading, by design. The reader can

follow the change without trusting a summary.

From a Bench to a Platform

Stage one made the next step definable. Between 13 and 15 September most of it was built and run on the same server: a

platform on which learning runs under varied conditions, and on which a finished model becomes something other benches

can use. What follows is what runs; the two pieces that are still only decided are marked.

Three sources, three roles. A learning bench binds a target (what we want to recognize better), a training set (large, related,

labeled), and an evaluation set (labeled, never seen by the model), each from any source, each a Set with a role. The held-out

frame inside training becomes the selection frame; the evaluation set becomes the report frame — a sweep chooses by the

first and reports on the second, so the unseen set is never the thing being optimized. Overlaps are measured by identity and by

content digest at bind time; an evaluation item that leaks into training refuses the training; a target item that appears in training

is, by default, removed from training — the target is for judging learning, not for learning. (The evaluation set and the two

frames are decided, not yet bound on the server; today selection and report are the same held-out frame, and the board says

so.)

A condition is a branch. A parameterized template — a file of plan lines with a #!params header — is bound to one set of

values and becomes a workflow branch whose name carries its lineage: the parent branch, the plan position it forked from, the

template, and an eight-digit digest of its bindings:

   main@p0/learn_observe@46440ec6        head=ridge · split=0.8 · seed=2

Branching twice with the same bindings returns the same branch. Every binding is a Set the branch joins, so "all branches

trained with this head on that split" is an intersection.

A sweep is a named condition space with a budget. sweep.def expands a grid into condition atoms, bounded by a

maximum, and creates no branch; sweep.materialise turns up to n of them into branches; sweep.status reads the fan —

conditions, branches, pending, done, failed, retired. Done is never written: a condition is done when its branch has an

evaluation in the sweep's evaluations Set. A grid change adds conditions and retires the ones that are no longer valid; it deletes

nothing, and a condition that already ran keeps its history. The sweep is declared in the bench's configuration and defined at

provisioning, on every new build, without an operator; a branch of an admitted sweep may run even though it is not a static

workflow of the society. The driver's own selection of the next branch within a budget, the quarantine of a branch after two

failures, and the drift re-run of finished branches are decided and not yet built; today an Agent chooses.

A leaderboard is derived state. Evaluations are a Set; ranking is a read over it, grouped by the frame they were measured on,

so that numbers from different test sets are never compared. The board is the stored result of that read, each row joined with

its condition's bindings and the engine that produced its model, carrying the epoch it was built at and an artifact identity; a

rebuild that changes nothing is a no-op, and every earlier generation stays in a history Set. It is rebuilt by the same write that

files an evaluation, and verified — or repaired — at boot by the hydrate registry. No command produces it. On the night the

registry first ran with it, the server's board was missing; the boot line read assigned=1, and it was there.

Versioned weights. Training publishes weights as an immutable generation named by content and moves the model's pointer

by compare-and-swap. A version can be pinned; a retrain adds a version and loses nothing. A registered production model —

an immutable copy of identity, figures and provenance behind a current pointer, observed by other benches as prod:<name>

— is the same mechanism one step up, and is decided, not yet built.

What the first condition taught. The first materialized condition asked for a ridge head. The bench trained it, evaluated it

(accuracy 0.3667 on the held-out frame, against 0.2167 for stage one's logistic regression), promoted it, observed the target

with it, and ranked it — and the evaluation row said engine=numpy_centroid. There is no ridge learner; the head had fallen

back, honestly labeled, to a centroid classifier, and a centroid on this embedding beats the linear head. Two rules followed. A

sweep's grid is validated against the learner kinds that exist, at definition; a training step refuses an unknown head rather than

degrading quietly; and the engine is a column of the board, always. And the comparison itself — a mock beating the learner

— was kept, because it is an observation.

The condition also took forty minutes, all of it embedding: the same six hundred training photographs and four hundred target

photographs, with the same embedder that earlier runs had already applied to them. Reuse of an embedding across conditions,

keyed on the item and the observer's version, is specified as its own slice; until it lands, a sweep costs what its embedder

costs, not what its learner costs.

Every one of these is Set membership, a macro, or a template. The handlers the platform added to the kernel are few: the grid

expansion and the per-condition branch loop (the script language has no loops), writing a Set at mint, admitting a sweep in the

society's policy, ranking, publishing a generation, the condition's status move. The rest is composition.

Figure 11.1 — One Cycle, Two Coordinates

        target items                       training items

        (labels sealed)                    (labels used)

             │                                  │

             │  T2 observe                      │  T3 feature

             ▼                                  ▼

       ┌─────────────┐                     embeddings f1

       │   run o0    │  learning-free            │

       └─────────────┘                          │  T4 train

             │                                  ▼

             │                            learned head ── T5 evaluate on

             │                                  │           the held-out frame

             │  T6 observe with the head        │

             ▼                                  │

       ┌─────────────┐  ◀───────────────────────┘

       │   run o1    │  learned

       └─────────────┘

             │

             │  T7  o0 ∩ item  vs  o1 ∩ item      (a macro over Sets)

             ▼

        per-item change · one aggregate atom · visible in the Source Viewer

Chapter 12 — Society

A Society of Agents

Traditional software is usually designed around a single actor.

One user.

One application.

One process.

Even distributed systems often preserve this assumption.

Multiple computers cooperate,

but each still executes a predefined role.

Akasha begins with a different premise.

Knowledge rarely belongs to one participant.

Ideas emerge through interaction.

A historian consults archives.

An engineer evaluates measurements.

An editor reviews a manuscript.

An LLM proposes alternatives.

A sensor contributes observations.

Each sees the world differently.

Each contributes something unique.

Concept-Oriented Computing therefore treats participants themselves as semantic entities.

Every participant becomes an Agent.

Not because they are identical,

but because they interact through the same semantic substrate.

An Agent may be:

a human

an LLM

a scheduled workflow

another Akasha instance

an external service

a sensor

a robot

Their internal implementations differ enormously.

Their conceptual role does not.

Each observes,

interprets,

or transforms the same semantic world.

This changes the purpose of communication.

Traditional systems exchange messages.

Akasha exchanges meaning.

The semantic graph becomes the common language.

Participants no longer need identical implementations.

They only need to understand the concepts they share.

Structure Without Command

Society represents structured coexistence among Agents.

It is deliberately broader than multi-agent chat.

A Society supplies roles — moderator, participant, observer, audience, broadcaster — and relationships, without requiring

either unrestricted autonomous behavior or rigid scripted behavior.

Roles, relationships, the current Workflow, the Workbench, and the state of the World together shape what participation

means.

A moderator can run a Society by hand, or the Society can be placed in an automatic mode in which the moderator's role is

driven by the system under a declared policy — which workflows, on what trigger, within what budget, and what happens on

failure.

Every automatic act still needs a keeper of the record: an observer that writes down what was done.

A future Organization can impose stricter rules where Society represents looser coordination.

Identity Without Centrality

Society deliberately avoids placing any participant at the architectural center.

Humans are not privileged because they are human.

LLMs are not privileged because they are intelligent.

Services are not privileged because they are automated.

Authority comes from the semantic context,

not from the implementation.

A participant may receive permission to observe,

to propose,

to modify,

or to approve.

These capabilities belong to the semantic world itself,

rather than to a particular technology.

Authority Is Not Truth

The moderator of a seminar governs its process.

Who reads next.

When comparison opens.

When a revision is recorded.

The moderator's reading is nevertheless one reading among others.

It is not ground truth.

Akasha keeps these apart on purpose: procedural authority is a role in a Society; interpretive truth is never assigned by role.

This is the same distinction Chapter 6 drew for auditors and norms, now applied to people.

This makes Society fundamentally different from traditional multi-agent systems.

Most multi-agent systems define interactions between software agents.

Akasha defines interactions between participants.

Some happen to be software.

Some happen to be human.

Some may eventually become physical systems.

Architecture does not distinguish between them.

Trust does.

Authority does.

Capability does.

Claims and Evidence

Participants say things about their work. "Tested." "Verified." "The model improved." In most systems such statements are

either believed or ignored; in a semantic world they can be attached.

A claim is an atom. It joins the bench's claims Set and carries one link, evidenced_by, to an execution coordinate, an

observation, or an evaluation row. Its status is never written; it is read: attached when the link resolves, unattached when there

is none, contradicted when the evidence's own status — failed, retired, superseded — negates it. There is no false. A claim

without evidence is not a lie; it is an interpretation nobody has yet attached to the world, and it is shown as such.

This is the distinction between declared and judged acts, applied to statements. An act by an Agent is recorded twice — as

what the Agent declared it was doing, and as what an observer or the bench judged it to be — on two coordinates of the same

clock, neither overwriting the other. The seminar runs on this footing from its first session, so that a reading, a comparison and

a revision are each an act with both coordinates. Guests may read how many claims stand attached, unattached or

contradicted; the text of a claim stays inside the circle that made it. (Decided.)

Offered and Granted

"Can execute" and "may execute" are two different facts, and a system that keeps one Set for both cannot run an experiment

about either.

What an Agent in a role can discover is a Set: the capabilities offered to that role in that society, readable as such. What it may

do is the grant check, unchanged. A thought experiment varies the first — which skills are on the table — and never touches

the second. A capability's identity is the build fingerprint of the seed that ships it, so a comparison across seeds is honest by

construction; a capability is qualified on the running build before it is offered, and a promotion is world-scoped, so every

society in the world sees the same one. A capability that reaches outside the world — sends, publishes, moves something — is

marked effectful, and a replay rehearses it rather than executing it. (Decided; the offered Sets are the next capability piece.)

The Thought Lab

Given claims, declared and judged acts, and the epistemic position of Chapter 10, an experiment about thinking needs no new

machinery. It is a sweep.

A thought template binds a model, a role, a task, a partner, a skills Set and an activation — which horizon plan, which

admission policy — and each binding is a Set the branch joins. What is compared is a configuration, never an Agent's isolated

intelligence: the same model with a different partner, the same role with a narrower horizon, the same task with one capability

withheld. The evaluation rows rank on the same board as any other sweep, grouped by the frame they were judged on; a

replay from a chronon under a varied binding is one more condition. The seminar's readings are the first material. (Decided;

the templates are the next Thought Lab piece.)

Examining a Hypothesis

A hypothesis that ranks first in a sweep has been compared; it has not been examined. Examination is a different act — not

which configuration scores best, but what would make this hypothesis wrong and whether anyone looked. The Thought Lab

already has the roles for it, the counterexample seeker, the evidence challenger, the frame proposer, the conservator, and the

places to put what they find: claims with evidence and Nebula candidates. What it lacked was a shared list of questions every

examination asks, so that two reviews of two hypotheses are comparable and a review that skipped a question is visible as

such.

The list is ten questions, and they are vocabulary — one atom each, defined once: are the terms defined, so that each resolves

to an atom; is there a counterexample in the Sources or the history; is there an alternative explanation of the same evidence;

does it rest on an assumption no observer can read; would a different model or observer produce the same result; which

observation would weaken it; under which condition is it rejected; after a counterexample, did the revision gain predictive

power; or did it only add a free parameter; and does it hold under another Source, role or projection. A review of a hypothesis

writes, per question, one act with both coordinates whose result joins exactly one of four Sets — passes, fails, unobservable,

not asked — and links to what the answer rests on. A failure on the alternative question mints the alternative as a Nebula

candidate; a failure on the counterexample links a contradiction. There is no false: a review never deletes or demotes a

hypothesis, it attaches what was found.

The review is a template run by roles in thought mode; each question is a plan step through the one recorder, so a review cut

short by its budget shows not asked for the rest, never silence. The ten verdicts form one evaluation frame; the board may

rank on one question at a time and never sums them. "Passed review" is not a phrase the system uses: a viewer shows ten cells

and the reader draws the line. Three of the questions feed the loop of Chapter 14 directly — the weakening observation and

the rejection condition are what an outcome contract must name before a trial, and a hypothesis that has not been asked them

cannot be committed above a shadow; the transfer question is the sweep across conditions the abductive template already

runs. The first question is the project's own thesis applied to itself: a hypothesis whose terms do not resolve in the lexicon is

not yet a hypothesis, it is a phrase.

The idea of a fixed list of examination questions applied to every hypothesis alike was prompted by senka L8's Layer-8

Cognitive Architecture / SCOPE × COS work and the author's public posts on it; the ten questions here are this project's own

formulation, and nothing of that model's terms or structure is borrowed. (Ruled 20 September 2026; Part II §A19.)

A Cognitive Society

A participant in a Society need not speak. A classifier, an embedding observer, a sequence model, an anomaly detector, a

learned head, a sensor, an actuator's controller, a workflow, another Akasha — each is an Agent, because each observes, acts,

and leaves coordinates. There is no message passing between them. Everything a participant observes, proposes, judges or

interprets goes through the shared world, where every other participant can read it under its own projection.

A role, in such a Society, cannot be a persona prompt. It is a product of five Sets: what the role is responsible for, what it can

see, what it is offered, what it is granted, and the contract its acts must honour — an observer's act must carry a bundle and

never an interpretation; a synthesizer may propose a synthesis and never canonise it; a conservator keeps minority readings

and failed branches alive; a moderator governs process and the boundary with the world and decides no truth. Two roles that

differ only in wording are one role, and the evaluations say so.

Because the roles, the observers, the frames and the Nebula are all bindings, an experiment about thinking is a sweep over

configurations — one language model alone; several without roles; several with roles; roles with shared observations; with the

Nebula; unlike models with non-linguistic observers; all of that with a human buddy — on one Source, one task, one set of

frames. Two kinds of search are kept apart and budgeted apart. Within a frame, the driver varies conditions as it already does.

Across frames, a search starts from an anomaly and proposes a new grouping, relation, granularity, comparison, or evaluation

axis; what it produces is a Nebula candidate or a new sweep, never a quiet change to the axis everything else is ranked on.

The loop that makes a conceptual leap testable is a template: an unexplained observation, competing explanations, the

observations that would tell them apart, a replay or a new observation, evaluation under several frames, and then retain,

revise, fork, or retire. What is measured is a vector — coverage, diversity, anomalies found, contradictions found, evidence

attached, calibration, recovery from a false lead, reach of counterfactuals, transfer, novelty read together with testability,

minority readings retained, what a human could consider that they could not before, and cost. The board ranks on one

declared key at a time. There is no composite score. (Decided; track C in the plan.)

One Gate for Every Model

A language model in a Society is one participant among many. In production, the participants that use one share a single

external contract — at launch one free tier, hosted in Europe; next a local model on the host; later others — and a public

world that runs as a demonstration has no budget to spend. Two things follow, and the design already had the shape for both.

The first is that a model is a capability, not a property of a Society. It is offered to a role as llm:<provider>:

<model>@<fingerprint> in that role's offered Set, so a Society may hold several models in several roles, and every Society

in the world may share one contract: the capability names the provider, the gate owns the contract. Which model a role gets is

a binding, and therefore a Thought Lab axis, not a deployment fact.

The second is allocation. Every call already passes one gate — one function, no per-program keys, a hard daily and monthly

floor, rate spacing, accounting that survives restarts — but the floor only prevents overspend; it does not decide who spends.

Left alone, programs take the day's calls first come first served, and a run can reach the cap halfway through: a reading

programme in which the reader reads, the listener asks, and the commentator never answers. The remedy is the rule the

substrate uses for everything bounded: the population is the budget, and you pay at admission, never per event. A day's calls

are a bounded pool per provider; an execution reserves its estimate when it is admitted, runs prepaid, and settles what it did

not use at the end; a run the pool cannot hold does not start, says why, and earns the right to go first tomorrow. Priority gains a

cost axis. The pool is a readable atom per provider per day, compacted with the telemetry, so the day's spending is a fact

anyone in the circle can read. Nothing is added that the substrate does not already have: no thread, no scheduler, no second

queue. A call to a provider changes nothing in the world and is allowed in thought mode; publishing what it produced is the

effectful act, and that is where containment applies.

Containment

The Workbench in thought mode is a laboratory, and the design has always treated it as one. Inside, autonomy is cognitive and

complete: a Society of unlike Agents may branch, rewind, sweep, compare and re-run without a person present, and no one

approves a thought. Authority lives at one place only — where a thought would become an irreversible act in the world.

The protocol is short. A capability that reaches outside carries the mark effectful. In thought mode such a step is never

executed; its stored result or a declared simulation is served and the coordinate is minted as a rehearsal. A Society may write a

proposal: a claim whose subject is one capability call, with the world it targets, the parameters, the expected effect, the risk

frame, and, as evidence, the branch that rehearsed it. A human moderator records one act per proposal — approve, refuse, ask

for revision — with both coordinates. An approval is a written grant: one target, one use unless stated otherwise, and an

expiry the moderator names as a chronon coordinate — there is no default, and an approval without one is refused; the same

check that governs every write reads it. Execution happens only after synchronisation to the world, is recorded as such, and

consumes the grant. Its result returns as an observation, and the cycle closes. No Agent can widen its own role or its own

grant; offer, discovery and execution remain three Sets.

The biological laboratory is the exact analogy: a containment area, cultures that grow unattended, a notebook that records

everything, quarantine for what fails, an airlock, a safety officer who signs the release, and monitoring of what comes back.

From any effectful execution the links walk back to the plan, the moderator's act, the proposal, the rehearsing branch and its

chronons; the walk is a macro over links the world already writes. And the moderator's approval makes nothing true, just as a

refusal makes nothing false — it is a procedural act with coordinates, as the seminar chapter said of every authority. (Decided;

track C.)

Conversations Become Knowledge

Most conversations disappear.

Chat windows close.

Messages scroll away.

Context is forgotten.

Society treats conversations differently.

A conversation is not merely communication.

It is a process of constructing concepts.

Ideas become atoms.

Relationships become links.

Questions become jobs.

Decisions become history.

The semantic substrate remembers not only what was concluded,

but how those conclusions emerged.

Coordination Instead of Control

Because every participant acts independently,

Society is not built around command.

It is built around coordination.

An Agent proposes.

Another evaluates.

A third contributes evidence.

A fourth performs computation.

Consensus emerges through semantic interaction rather than centralized control.

This principle naturally extends beyond real-time collaboration.

Some participants respond immediately.

Others may respond hours later.

Others may disappear entirely.

The semantic process continues.

Latency changes.

Architecture does not.

Figure 12.1 — A Society of Agents

       Human            LLM            Workflow

         ↕               ↕                ↕

   ═══════════════════════════════════════════════════

           S E M A N T I C   W O R L D

              (the concept substrate)

   ═══════════════════════════════════════════════════

         ↕               ↕                ↕

       Sensor      Another Akasha       Robot

Participants never communicate directly.

They contribute through the semantic substrate.

Notice that no arrow connects one participant to another. Every proposal, every evaluation, every observation passes through

shared meaning — which is why participants with wholly different implementations can cooperate at all.

Society Beyond AI

The recent rise of LLMs has made multi-agent systems fashionable.

Akasha's Society is not a response to that trend.

Its roots are older.

It emerged from a simpler question:

How can many independent participants contribute to the same conceptual world without sharing the same implementation?

LLMs happen to fit naturally into that answer.

So do people.

So do workflows.

Future technologies may fit equally well.

Society therefore outlives today's AI.

It describes a computational relationship,

not a particular generation of intelligent systems.

Taking Part Is a Binding

A Society admits more than people and language models. A program that checks a constraint, a classifier that answers yes or

no with a probability, a reranker, a forecaster, a scheduled workflow, a sensor gateway, a robot, another Akasha — each can

contribute, and each contributes something different: a witness, a score, a forecast, a reading, an act. What they have in

common is not their technology but the terms on which they take part: an identity, a role, a scope, what they are offered, what

they are permitted, and what they must leave behind as evidence.

So the question is never which clients can connect. A reachable endpoint is not a participant, and a live stream is not an agent.

Participation is a binding Akasha makes. The same model weights are a Source when they are archived, an Operand when

they are evaluated, an external service when they are served, and a participant only when an identity is bound to them with a

role and an obligation to record. The same sensor reading is an observation; the gateway that chose to send it may be a

participant. Model family and provider are attributes of a participant, not kinds of it.

Three rules keep the binding honest. What a participant may do is not written on the participant: it is what the one gate

answers, from the assignment line and the grants that acts have written. A participant that is handed material outside the

machine it runs on has received that material, so the material's privacy decides which participants may see it, and what is

marked local never leaves the node. And no substitution is silent: when one participant stands in for another, or a provider

changes the model behind an endpoint, a different fingerprint is recorded, and the change is a point on the trajectory, not an

invisible continuity.

Whatever a participant returns enters the record in the same few shapes — a claim, an observation, a score, an artifact, a

witness, an error — stamped with who produced it under which line, which inputs it was given, and whether it was observed,

predicted, simulated or interpreted. A forecast is not an observation of the future. A ranking of candidates is not evidence

about any of them. Two close vectors are a suggestion, not a fact. Where a deterministic check exists — a solver, a validator, a

test — a language model may phrase its question and read its answer, but the answer is the check's. (Decided October 2026,

§A31.)

Toward Collective Intelligence

When concepts become shared,

memory becomes shared.

When memory becomes shared,

reasoning becomes cumulative.

Each participant extends the semantic world,

making it richer for the next.

Knowledge ceases to belong to individuals.

It becomes part of a continuously evolving conceptual environment.

Society is therefore not the final application built upon the Semantic Substrate.

It is the natural consequence of making meaning persistent.

Figure 12.2 — Knowledge Accumulates

    time ──────────────────────────────────────────────────▶

      Human            LLM             Workflow         Future

    observation      analysis          curation       participant

         │               │                 │                │

         ▼               ▼                 ▼                ▼

      ▓▓▓▓          ▓▓▓▓▓▓▓▓▓       ▓▓▓▓▓▓▓▓▓▓▓▓▓▓   ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓

   ═══════════════════════════════════════════════════════════════════

          the semantic world — every contribution is added to

          everything that came before; the band only widens

Each participant inherits the accumulated work of every previous participant.

No one begins from an empty world.

Chapter 13 — Designing a Concept

Chapter 6 said that a Concept Model is a typed projection of atoms — a Note, a Survey, a World, a Map. What it did not say is

where a Concept Model comes from, how it is known to be any good, and what happens when the world disagrees with it.

This chapter, taken into the design in September 2026, answers that a Concept Model is an executable hypothesis: something

a human and a language model design together, that the Workbench tests, that operations use provisionally, and that the world

corrects.

A Concept Model Is an Executable Hypothesis

A Concept Model is a seven-part statement: a Source scope, an assumed boundary of the concept, the properties and relations

it assumes, a set of operands, the parameters that may vary, the projections that show it, and the frames that judge it. It

declares no final ontology of the world. It says: read this Source scope by this boundary and these properties, apply these

operands, and under these conditions this behaviour should be observed. That is an operational claim, and it can be wrong in

specific ways — which is what makes it a hypothesis rather than a schema.

It is also an instrument. Defining a concept decides what becomes observable, what counts as a difference, and what is

ignored. So evaluating a Concept Model asks not only whether it landed on its target but what its boundary made visible and

what fell outside, which operands moved the result, and — in the terms of Chapter 10 — what was available, visible,

considered and acted upon when it was applied. Two models with the same score can be looking at different worlds.

An operand is not a method; it is an operation with an expected observation, declared inside the model. Set intersection, a

graph walk, a distance, a clustering, a statistical test, a tensor operation, a rule check, a reading by a language model, a

critique by several — any of these may be an operand, and what matters is not how it is implemented but that its expected

behaviour is recorded as part of the hypothesis and can be found wanting. An operand is not a capability, which is what the

running build can execute; not a grant, which is what a role may execute; not a workflow, which binds operands to order and

state; and not an effect, which is what actually happened. The distinctions are the ones Chapter 7 drew between operand,

operator and agent, carried one level up.

Authoring, Together

The design of a Concept Model is, for now, a collaboration between a person and a language model, and the design refuses to

make it anything else. The person brings the meaning of the question, the purpose, an intuition about where the boundary lies,

the value in practice, the risk and the responsibility, and the decision to adopt or hold. The model brings language for

candidate boundaries and properties, competing definitions, the known theories and libraries, candidate operands,

counterexamples and edge cases, candidate Sources and ontologies, and explanations of what the experiments showed.

Akasha brings the record: versions, Source scopes, branches, executions, evaluations, provenance, chronons, and what came

back from the field, all in one semantic space and all replayable. Automatic generation of concepts, automatic tuning,

automatic promotion by score, automatic revision from field results — these are research questions the design names and

declines to require. Their absence is not a defect; the deliverable is a Workbench on which a person and a model design, and

the system tests, applies and records.

The loop is short to state and long to run: a question and a purpose; a hypothesis designed together; operands filled with

known computation, model readings and Set operations; Sources, datasets and an ontology chosen together; an experiment in

the Thought Lab; a projection a human can read; a revision designed together; and around again. Sources become datasets

with three roles, as Chapter 10 described — training, a target whose labels stay sealed, an evaluation the model never sees —

identified by digest and refused when they overlap. The ontology an experiment uses is a version of its own, published like

weights and bound to the branch; changing it makes a new condition, never an overwrite. It distinguishes what was observed

directly, what an observer or model interpreted, what was sealed as a label, what the model assumes as a relation, and what is

derived.

The Contract Is the Branch

Everything that defines an experiment — the model version, the ontology version, the operand fingerprints, the pool, the three

dataset digests, the parameter bindings, the observer versions, the horizon plan, the role and scope, the frames, the budget, the

chronon — is a binding, and every binding is a Set the branch joins. So the experiment contract is not a record beside the

results; it is the branch, and a result without its contract cannot exist, because the evaluation row joins the branch's Sets when

it is written. A question in the Thought Lab is not a sentence but a choice of what to vary: widen the boundary and see what

atoms leak in; change a relation's weight and see whether the landing holds; reorder the operands and see whether the result is

preserved; remove part of the Source, change the chronon, change the observer, move to another domain. The sweep

machinery of Chapter 11 runs it unchanged.

Evaluation is a vector, judged under three frames that are never ranked across: static fit — how well the model landed on its

target now; dynamic validity — how it deforms or collapses when the conditions move; and operational usefulness —

whether a bounded piece of work is better for it. Candidates with different strengths — precise but brittle, coarse but stable

across Sources, weakly explanatory but cheap, useless in operations but rich in unexplained residuals — are kept, and never

converged early into a winner. A human reads a projection of all this — version history, branch comparison, the vector as a

radar, the difference in boundary membership, which operand contributed, where the failures and residuals are, lab beside

field, the lineage — and designs the next version. A revision never overwrites: it is a new version with its parent recorded, and

the old executions are never re-read under it.

Two Axes, Kept Apart

How well a model is understood and how far it may be used are two different questions, and the design keeps two answers.

Epistemic maturity — unexamined, exploratory, partially supported, reproduced within scope, bounded, contested,

operationally useful but unexplained — is a Set a model joins by an act with evidence, perhaps proposed by the review of

Chapter 12, and never by a score. Operational admission — thought only, shadow, advisory, sandbox, bounded use, an active

workflow — is the level of Chapter 14. A high score with an irreversible, high-risk effect is not admitted; a partly examined

model that is low-risk, reversible and observable may be admitted small. A workload that uses a model pins its version, its

ontology, its operands, its datasets and its projection, and the record refuses a pin that says "current". When a better version

exists, a new binding is made; nothing that ran is reinterpreted.

Operational use is not graduation. It is an experiment under conditions the laboratory cannot reproduce — real users, external

systems, time, imperfect observation, changing Sources, cost, organisations — and its results are a frame of their own, beside

the laboratory's and never mixed into it. What returns is a proposal — to a boundary, a property, an operand, a parameter, the

ontology, the Source selection, a guardrail, a new question — that becomes material for the next design session, and is never

applied by itself.

A Repository Without a Second Truth

Concept Models and ontologies need version control, and the design has had it all along under another name: content-

addressed generations, pointers moved by compare-and-swap, lineage as links, immutable artifacts. A version is a snapshot of

an authoring directory — the files a person and a model edit — minted as atoms with a manifest, with its parents linked;

branches and tags are Sets with pointers; the log is a walk; compare is a lens; publish moves the pointer; a pin names a digest.

What is deliberately absent at this stage is semantic difference at the atom level, automatic merge, three-way merge, conflict

resolution, automatic upgrade, and a Git wire protocol. Merging is done by people: compare two versions, take what is needed

into a new working directory, snapshot it with two parents. A model may explain the difference between two versions; the

explanation is an interpretation attached to them, not the canonical diff. Source data is never copied into the tree; it is

referenced by identity and digest.

None of this depends on scale, deployment or provider. The identity of a model version, an ontology version, an operand, a

dataset, a lineage and an evaluation is the same on one offline device, on a personal server, on object storage, across nodes,

over a delay-tolerant link, or between federated worlds. Without an external model, the versions, the ontology, the Sets, the

deterministic operands, the cached observations, the workflow state and the evaluation history remain, and the loop still runs.

Large concept models and large action models, as they arrive, enter this loop as authoring assistants, hypothesis generators,

operands, observers, critics, evaluators, parameter searchers or planners — never as a replacement for the record, the grant,

the effect boundary, the stop or the rollback, which remain Akasha's.

The first completion is one lineage that answers twelve questions from its reads alone — from the question a person and a

model started with, through the versions, the datasets, the conditions, the rehearsals, the vectors, the projection a human read

and what they changed, the version that went to operations and at what risk, what came back and how it differed, to how the

difference reached the next model — and replays. The first such lineage is the plants vision model of Chapter 11 and the plant

programme of the station that uses it: the programme's classifier is the model at a pinned version, its airings are field

observations, and its residuals return to the bench. (Taken into Part II as §A22, 20 September 2026; stage P0 is part of the

release gate.)

The Grammar Stays Fixed

The application designs its concepts freely, and revises them as hypotheses. It does so on top of a small set of concepts

Akasha itself keeps fixed: the atom, the link and the set; the concept lattice; time as chronons; the epistemic position; the

source and the observation; the society, its agents and roles; the workbench and its workflow; the claim, the capability, the

derived artifact; the word model and its relations. These are the grammar of the world, not its vocabulary. They are reserved

— packaged inside the platform, written only through their own operations, closed to redefinition — so that no application's

convenience can bend what every other application stands on. The set is small on purpose, and it is allowed to grow: a

concept earns its place in the grammar by a written case, a section in the design context, and a move that changes nothing it

already did.

General Models, and What Promotion Means

Between the grammar and a single application's concepts lies a middle layer: models that many kinds of work turn out to

share. A claim with its evidence and counter-evidence; an entity with its names, aliases and the uncertainty of its

identification; an event with its actors, place and time; a collection and its items; a version and what it was derived from; a

rule and its exceptions; a decision, its authority and its dissent; rights, licences and consent. Archives need them, research

needs them, an office needs them. They are still the application's — general concept models, hypotheses like any other, forked

and revised, kept side by side when they compete, never merged into one great model. Templates depend on them by version

and meet them through mappings.

Some of them may one day enter the grammar. The path is slow on purpose: a model is reused across templates and domains,

it accumulates field observations and failures, someone writes the case for why the platform needs it, the design context gains

a section, the domain-specific part is split off, and only the mechanism moves, at a release. Each step is an act with its

evidence; a count of how often a model was used may nominate it, and never promote it. Promotion does not declare a

concept true. It says that an operational invariant has held in enough different places that the platform can promise it — a

statement about what works, not about what is.

Chapter 14 — Returning the Consequences

Chapter 12 ended the story of containment with a sentence: the result of an approved act returns as an observation, and the

cycle closes. This chapter is that sentence made into a mechanism. It was taken into the design on 19 September 2026 and it

changes nothing that came before; it fills the space between a leaderboard and the world.

Acting Without Believing

A hypothesis that ranks first has been compared, not confirmed. When the Workbench acts on it, the act is a provisional

operational commitment — a decision that acting on this hypothesis is, under stated coordinates, the more rational course. The

coordinates are the whole point: which Sources and observations were used, which competitors were compared, which roles

and scopes, which projection and horizon, which chronon and epoch, which frames and weights, which environment the act is

meant for. Newtonian mechanics is good engineering under stated limits and is not a complete account of the world; a

language model treated as an Agent inside a bounded workflow can be effective without that proving anything about its

experience. Akasha uses what works operationally and records where it applies and where it breaks. The questions it cannot

answer — what a concept is, what consciousness is — it keeps open, as stable places where observations, interpretations and

refutations accumulate.

So the commitment is a claim, in the sense of Chapter 12: its subject is one evaluation row and a declared decision frame, its

evidence is that row, and everything else about it — scope, risk class, reversibility, level, expiry as a chronon coordinate with

no default — is a Set it joins. Its status is derived, never written: active, expired, superseded by a later commitment on the

same hypothesis, withdrawn by an act. Its competitors are the other rows of the same sweep, and a commitment retires none

of them; if the chosen hypothesis breaks in the world, the branch that lost by a little is still there to resume from.

Levels of Exposure

A hypothesis does not go from the Thought Lab to full use in one step, and the steps are grant scopes rather than a new

authority. Replay and counterfactual touch nothing; a shadow evaluation only watches the work as it is done today; advisory

proposes to a person who acts; a sandbox trial runs inside an isolated world under a grant scoped to it; a canary runs on a

limited target for a limited time under a grant with a number of uses and an expiry; bounded automation runs under a declared

policy with a budget, a stop and a compensation; policy promotion is a registry record, immutable, with a pointer. Promotion

from one level to the next is a new claim whose evidence is the previous level's evaluations, never the trial's own report of

itself. From the canary upward, a human moderator records the decision regardless of score. Admission is a policy and a set of

acts, not a formula: thresholds are Sets, the driver may propose at the lower levels under such a policy, the gap between the

first and second hypothesis is a read, and the options — adopt, try small, shadow, fetch more Sources, run the experiment that

tells the competitors apart, defer — are acts with both coordinates. A high score with a close competitor is a reason for a

small, informative trial, not a large deployment: the value of information is part of the decision.

The Contract Before the Trial

Before anything is done, the trial states what would be seen. The outcome contract names a baseline, expected metrics and

their ranges, the sources that will observe, a deadline, an attribution window, the confounders already known, and —

explicitly — that an unknown outcome is allowed. It is sealed by construction: a content-addressed artifact with its epoch,

which cannot be rewritten after the fact. Its expected observations are declared as observation coordinates, so an expected

reading that never arrives is recorded as an absence, never as a missing row. The trial itself runs as any workload does:

budgeted jobs, the gate before the effectful step, the one recorder, and — because the contract joins a validity Set with its

deadline — the evaluation starts when the retention sweep, on its ordinary rounds, finds the window closed. No scheduler is

added; a trial from which nothing has returned is simply pending, and if nothing returns by the deadline it is unobserved,

which is a result.

What Comes Back

What comes back from the world is an observation — the canonical atom, marked as external, linked to the execution it

observes. The residual — the difference between what the contract expected and what was observed, with its direction,

confidence and attribution — is derived from the two, as an alignment frame of the kind Chapter 10 described: regenerable,

stale when its inputs move, never the truth. A residual no current hypothesis explains also becomes a Nebula candidate,

because that is exactly what the Nebula is for. Deviation and residual are different objects and stay different: a deviation is

plan against actual, a residual is expectation against outcome.

The outcomes a trial may have are vocabulary, and one of them matters more than the rest: confirmed within scope, partially

supported, contradicted, inconclusive, unobserved, confounded, unexpected — and operationally useful but unexplained.

Engineering has always lived with things that work and are not understood; the design refuses to hide that state, because

hiding it is how an approximation becomes a belief. A success is also asked for its residual: a coarse judgement of success

loses the microscopic difference that would have been the next question.

Two evaluations follow, under two frames that are never ranked across. The operational frame asks whether the work was

better for it — quality, time, cost, stability, effect on users, safety, reproducibility. The epistemic frame asks what was learned

— where the prediction held and failed, whether a competitor explains the same result, whether the frame itself was biased,

what could not be observed, which new variables or boundaries appeared, whether it is worth running again. A business

success does not confirm the causal hypothesis; a business failure that returned a rich residual is an epistemic success. Scores

stay vectors; a ranking that combines them by declared weights is allowed only as a declared, identified artifact with the

weights on it, and never as the default of the board.

Roles, and the Walk Back

Harmonia decomposes the trial, watches the stops, inserts the gate, starts the evaluation, runs the rollback, and holds the

commitment pending; it decides no truth. The Society keeps proposer, moderator, executor, observer and reviewer as roles

that a policy may forbid one Agent to hold together; permission to execute and epistemic support are two things. From any

effectful execution the links lead back — to the plan, the moderator's act, the proposal, the rehearsing branch, the

commitment, the evaluation, the hypothesis, the Sources — and forward to what returned, the residual, the revision. Each

coordinate carries the epistemic stamp, so "why this decision" and "would a different horizon have changed it" are

comparisons, not reconstructions. What recurring residuals teach — a template parameter, a guardrail the driver refuses to

repeat, a macro — is distilled as a proposal, never applied by itself.

The first loop is deliberately small and internal: which macro-cache plan the horizon uses, watched as a shadow through what

was visible and what was considered, then tried as a canary on one bench; then the driver's own pick policy. Deletion,

publishing outside, sending, payment and physical control are not in the first loop. The completion criterion is not autonomy.

It is that for one bounded task a single lineage answers where the hypothesis came from, how it was compared, why it was

chosen, who permitted what, what was done, what returned, how it differed from the prediction, and how that difference

changed the next hypothesis — and that the loop replays from the same chronon under another condition.

Believe none absolutely. Preserve the alternatives. Act on the best-supported hypothesis in proportion to confidence

and risk. Return the consequences as new observations.

(Taken into Part II as §A18, 19 September 2026; stages P0–P1 are part of the release gate.)

Two Directions, and What an Effect Is

Material crosses the boundary of the world in two directions. Inward, a sensor, a feed, an archive or a catalogue turns external

state into observations: they may inform, and they may propose, but they change nothing outside. Outward, an intention

becomes an act on something that is not Akasha — a message sent, a post published, a switch thrown, a robot moved. The two

share identities, coordinates and provenance, but not authority. An inward mapping needs permission to read; an outward one

is always an effect, and needs a grant that an act has written, an interlock that is clear, and a moderator or a policy declared in

advance.

An effect is not one record but four, and none of them overwrites another: the intention — an action stated as an operand,

inspectable before anything happens; the command the binding translated it into, with how it is delivered; the

acknowledgement the far side returned; and the outcome — a later observation, linked to the command that may have caused

it. A command is not evidence that its effect occurred, and an acknowledgement is not an outcome. The public station learned

this in its own channel: the request to post a thread was issued, the service answered that the account's credits were exhausted,

and nothing appeared — three different facts, which the design keeps as three records. A replay never issues a command

again; it serves what was recorded, or rehearses.

When the two directions close on each other — observation, decision, action, the changed state observed again — the

Workbench becomes an instrument that can act. The design keeps the loop inspectable at every link and puts the person at the

one place where thought would become an irreversible act. (Decided October 2026, §A31.)

Chapter 15 — Observing a Changing System

A Trajectory, Not a Score

Everything Akasha keeps is a record of something changing: a kitchen's vocabulary, a classifier trained on a bench, a

programme that airs at noon, a language model behind a provider's endpoint. We are used to evaluating such things by a

number taken now and then — a benchmark score, an accuracy, a rating. A number taken now and then tells you where a

system stood at the moment you looked, and nothing about how it got there or where it is going.

Akasha treats a changing system the way it treats everything else: as a sequence of observations on a clock. The clock is the

chronon that already orders a society's turns. An observation is a point: this target, this coordinate, this condition, this

observer, this chronon, this result. Repeat the observation at the next chronon and you have a delta. Repeat it for a season and

you have a trajectory — a development curve for each coordinate, from which stable phases and transitions can be read. A

changing system should not be evaluated only by occasional scores; it should be observed as a trajectory.

The coordinates are semantic, and they belong to the concept model, not to the platform. For a language model they might be

causality, temporality, grounding in sources, counterfactual stability, calibrated uncertainty. For a vision model, object identity

under viewpoint and occlusion. For a robot, position, goal, affordance, recovery. The platform knows none of these words. It

knows how to record a point, stamp a chronon, compare two points, derive a delta, keep a trajectory, branch a replay. That is

all it should know, and it is why the same machinery serves a bakery's recipes and a transformer's hidden states.

Three Ways of Looking

There are three ways to observe a system, and they are not the same act.

The first is to watch it work — passive observation. Nothing is added; the system's own inputs and outputs, its internal

statistics if they are reachable, its sensors, are recorded from the side.

The second is to probe it: to give it a stimulus chosen to measure one property. A paraphrase, an inverse relation, a novel

instance, a counterfactual, a distractor, a conflict between sources, a shift in time. The property is held fixed; the stimulus

varies.

The third is to intervene: to change the conditions themselves — the context, the role, what sources are visible, what it

remembers, what tools it has, what it is trying to do — and to measure the causal difference.

Akasha names these O0, O1 and O2, and it records which one was used, every time. The reason is the next section.

Observation Is Part of the World

A probe changes the system's experience: it has now seen the question. An intervention changes its world. Even passive

observation, through the hooks it installs and the samples it takes, can change timing and memory. So Akasha never assumes

that an observation was neutral. Each one records its observer, its mode, its method, its sampling policy, and whether the

target's training, memory and gradients were writable at the time. Three trajectories are kept apart: what the system did, what

was done to watch it, what was done to change it. Later, when the curve moves, one can ask two questions that are usually

confused — did it change because it learned, or because it was observed — and get two answers.

Tomography, Not X-Ray

Nobody can read a neural model's internal world directly, and Akasha does not pretend to. It does what a tomographer does: it

observes from many directions, repeatedly, and estimates the latent structure that would explain what it saw. Two resolutions

can be raised. More chronons give finer time; more concepts, relations, probes and metrics give finer meaning. What comes

out is an estimate, and it is recorded as an estimate. The line between "we inferred this structure from reproducible signals"

and "we read the representation" is an epistemic boundary, and the record keeps it.

Observers are plugins behind an interface — behaviour, logits, hidden states, gradients, weight deltas, sensors, a sparse

autoencoder, a human — and none is the centre of the design. A closed model behind an endpoint admits probing and

intervention but not passive internal observation; it can still be watched longitudinally, and a provider's silent update, which

used to be a rumour ("it feels different this week"), becomes a detected change point on a curve.

The Observatory and the Trainer

Two workbench templates carry this. The Model Observatory binds a target, takes an observation profile, observes, records,

compares, derives deltas, keeps trajectories, flags regimes and anomalies, and projects the result. A developer configures a

concept model, an ontology, an observation profile and an adapter for the target; nothing model-specific goes into the

template.

The Model Trainer is kept separate because it acts. It observes, diagnoses, proposes an intervention — and then stops.

Approval is a person's act; the training change is an effectful capability under the same authority every other act on the world

has. The observer may diagnose. The trainer may propose. Authority remains explicit. For a public open-weight model this

turns "prepare a dataset, run it, read a benchmark" into "take the model's semantic phenotype, form a hypothesis, apply a

targeted post-training, observe again".

None of this is new to Akasha. The plants bench described earlier in this book already did it — bind, observe, extract features,

train, evaluate, observe again, compare — before the pattern had a name. The observatory is that pattern, generalised to any

system that changes.

Chapter 16 — Seeds, Retreat, and Continuity

Carrying Worlds

Software is usually distributed as applications.

A version is released.

Users install it.

Data is migrated.

Configuration is preserved.

Eventually another version replaces the previous one.

The application changes.

The user adapts.

Akasha begins from a different perspective.

The application is not the important artifact.

The conceptual world is.

The software exists only to reveal it.

This distinction led to the idea of Seeds.

A Seed is not simply an installer.

It is a dormant semantic world.

When executed, it reconstructs everything required for that world to exist again.

The execution engine.

The browser portals.

The ontology.

The Concept Models.

The semantic pipeline.

The workbenches and their workflows.

The surrounding environment.

The Seed contains the potential for an entire conceptual ecosystem.

This resembles biological seeds more than software packages.

A seed does not contain a tree.

It contains the instructions required for a tree to grow again.

Likewise, an Akasha Seed contains the conditions required for a semantic world to reappear.

The world is reconstructed rather than merely copied.

Germination

The name is architectural, not decorative.

Figure 13.1 — A Seed Meets an Environment

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

The question a Seed asks is not "what does this environment lack?"

It is:

"What can Akasha do in this environment?"

A rich environment permits a large deployment.

A constrained environment permits a smaller form.

Semantic identity and continuity survive the reduction.

A Seed decides, at the time it is generated, what it will do when it is planted: which data it carries, which benches it

provisions, which workflows run on their own once the data they need is in place. A planted Seed needs no one standing

beside it.

A Seed is also the oldest instance of the pattern Chapter 8 named: an immutable generation. Running a new Seed over an

existing installation replaces the code, the ontology packages, the portals, and the configuration, and touches nothing in the

durable universe — the store, the user's ontology, the bench artifacts, the registered models survive every update. On the

public server this has happened dozens of times in one month; the world was never rebuilt, and each run of the daily workflow

after an update reused every observation it had already made. Static archives and published generations may move to object

storage; the Seed still carries what a world needs to wake.

From a Seed to a Workbench

A Seed that wakes is not yet a place to work. Before a researcher, an archivist or an office can begin, someone has to decide

what is taken in as Source and how Source is kept apart from its readings, which concept models read it, which ontology is

assumed, who takes part in which role, what runs, what is observed, what a person is shown, where an effect must stop for

approval, and how the state before a revision will be reproduced. That design burden is what keeps a working substrate from

becoming working practice.

A template carries that design as a starting point. It is not a worldview and not a wizard: it is a versioned package —

workflows, concept models, ontology packs, Source contracts, roles, operating profiles, observation profiles, projections, page

skeletons, evaluations — that a person chooses, connects to their own Sources and inspects before anything is built. The

division is the one that runs through the whole system: the mechanism that reads, validates, builds, records and replays

templates belongs to the platform and cannot be changed by an application; the templates themselves belong to the application

and can be written, forked and revised by anyone. The mechanism knows no domain word. A template brings no code and

cannot grant itself a permission; every step it names is an operation already registered, and every one passes the one gate.

What a template builds is a branch, not a copy. It records every version it used — of the template, of each concept model, of

each ontology pack, of the workflows and operands — and every Source by identity and digest, every parameter, role and

boundary, and the chronon it was created on. A result produced without that contract cannot exist. When a template is revised,

nothing already built is upgraded: the difference is read, a migration is rehearsed on a new branch, the observations are

compared, and a person decides. When a Source is connected it is not turned into meaning on arrival: it is given an identity

and a digest, checked against the contract, offered mappings, and shown beside them; a person adopts a reading. In an archive

the image is the Source, the OCR an observation, the transcription an interpretation, the edition a projection, the reason for a

reading a claim with its evidence, the exhibition text a public projection — and a template provides that distinction from its

first minute.

The target is modest to state and hard to keep: plant a Seed, choose a template, name a Source, and within minutes have a

workbench whose every part can be inspected, that runs without a cloud account or an external model, and that resumes the

same state after a reboot. The small seed, not only the large one, carries this: the next release puts the Workbench and its

templates into the seeds series itself, with a few small, openly licensed examples of its own, so that whoever plants it can

build an application without writing code. It opens with two doors on the same world — one to build, one to use — and its

examples were themselves built through the first door. The door's appearance belongs to the application and may change;

what it stands on is fixed in the grammar and hides nothing: every step taken through it is a command line the console

accepts, and what it records for an application is a script that builds the application again. Code remains a door too: a concept

model written by hand, wired to a page in a few lines of JavaScript, stands in the same place and passes the same gate.

(Decided September 2026, §A30; not yet implemented.)

Retreat

Running in local or constrained environments is not explained by local-first alone.

The deeper requirement is that knowledge and work must be able to travel to places where compute is limited, services are

missing, connectivity is intermittent, or only a subset of capabilities exists.

So the system needs a retreat strategy.

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

Capabilities may retreat; semantic continuity should not.

This is why lightweight deployment, delay-tolerant networking, portable Workflow, Set placement, and Seeds belong to one

design family.

Portability

Because concepts, Sets, Workflow, and execution state all belong to the substrate, portability in Akasha is stronger than "copy

the database."

A portable unit may carry the relevant knowledge, its interpretation, rules, the Workflow, its execution state, permissions and

scopes, and the semantic context it needs.

Figure 13.2 — Work Travels

   Node A                                Node B

    ├─ knowledge Sets                     ├─ knowledge Sets

    ├─ Workflow          ── transport ──▶ ├─ Workflow

    └─ state                              └─ state

                                               ↓

                                            continue

The work does not restart on the other side.

It continues.

Delay Is Not Failure

Akasha's distributed model is compatible with delay- and disruption-tolerant networking.

The system does not assume permanent connectivity, low latency, a continuously reachable center, or unlimited local

resources.

If a node holds the relevant Sets and the Workflow, it keeps doing useful work while disconnected, and synchronizes later.

Network delay should not imply loss of semantic work.

Field systems, mobile devices, remote sites, intermittent links, autonomous machines.

Every Device Does Not Need the Whole World

In an IoT environment, a device receives the semantic region and the Workflow relevant to its role.

Figure 13.3 — Semantic Placement

                     Akasha World

                          │

                 semantic placement

              ┌───────────┼───────────┐

              ↓           ↓           ↓

           Sensor A    Edge Node B   Actuator C

            Set α        Set β         Set γ

           Workflow     Workflow      Workflow

Sets, Scope, the macro-cache, Workflow, delay tolerance, telemetry, and degraded execution are one mechanism seen from

different distances.

Knowledge distribution is semantic, not block- or table-oriented.

The World Comes First

Because concepts remain independent of implementation,

upgrading Akasha becomes fundamentally different from upgrading conventional software.

The objective is not to replace the user's system.

The objective is to preserve the user's world.

Concepts,

ontologies,

browser portals,

and Concept Models

remain where they belong.

Only the execution engine changes.

This principle allows updates to become remarkably simple.

New Concept Models may be added without modifying the kernel.

Browser portals may evolve independently of storage.

Ontology packages may be expanded without restructuring existing knowledge.

Future storage engines may replace previous ones.

The semantic world remains continuous throughout.

Incremental Growth

Knowledge rarely appears all at once.

Neither should ontology.

Akasha therefore treats ontology as a continuously growing ecosystem.

Additional concept packages may be introduced at any time.

Existing concepts become richer.

Relationships become denser.

New worlds emerge without replacing previous ones.

The graph grows organically.

This same principle applies to browser portals.

A new portal is not a new application.

It is another interpretation of the same conceptual substrate.

Akashic Kitchen,

future philosophy portals,

historical atlases,

scientific explorers,

or educational environments

all coexist naturally because they describe different views of one semantic world.

Continuity Instead of Migration

Traditional systems often require migration.

Schemas evolve.

Tables change.

Applications adapt.

Compatibility becomes an ongoing engineering effort.

Akasha approaches continuity differently.

Concepts remain stable.

Relationships remain stable.

Meaning remains stable.

Implementation evolves around them.

Migration becomes the exception rather than the rule.

This does not eliminate change.

It changes where change occurs.

Instead of rewriting conceptual structures,

Akasha replaces or extends interpretations.

The semantic world continues uninterrupted.

Figure 13.4 — Growing a Semantic World

        Ontology          Concept          Browser

        packages           models          portals         branches —

             ╲               │               ╱             added season by

              ╲              │              ╱              season, never

               └─────────────┼─────────────┘               rebuilt

                             │

                      Semantic World                       the trunk —

                             ▲                             one, continuous

                             │

                             │  grows out of

                             │

                           Seed                            a dormant world —

                                                           run once, it wakes

The world grows.

It is not rebuilt.

This is the one figure in this paper whose arrows point upward — because a seed does not descend into a world. A world rises

out of a seed.

Akasha Itself Was a Seed

There is a historical analogy.

The foundational design spent roughly thirty years dormant.

The environment changed: hardware became cheap, general compute abundant, LLMs appeared as unusually capable

semantic clients, chip design became accessible, local and mobile devices became powerful, distributed systems became

ordinary.

The old design encountered a new environment and became implementable.

Akasha itself was a seed.

This is not literary branding.

It mirrors the project's actual relationship between a dormant architecture and an environmental opportunity.

Beyond Software Distribution

Seen from this perspective,

a Seed is not primarily a software package.

It is a vehicle for transporting semantic worlds.

A complete conceptual environment can be preserved,

shared,

reconstructed,

extended,

or continued elsewhere.

The world travels.

The concepts survive.

The implementation follows.

Figure 13.5 — From Software to Worlds

        TRADITIONAL                          AKASHA

        Application                      Semantic World

             │                                 │

             ▼                                 ▼   condensed into

        Installation                         Seed

             │                                 │

             ▼                                 ▼   grows again as

           User                       Another Semantic World

                                               │

                                               ▼   … which can itself

                                              ···      be reseeded

     software is copied              the world itself travels —

     to every machine                preserved, shared, continued

The objective is no longer to copy software.

The objective is to preserve continuity.

Chapter 17 — Keeping a Public World Honest

What the Server Taught

A semantic world that runs in public, unattended, on modest hardware, teaches rules that no design document anticipates. This

chapter records the ones that held, in the order the server taught them. They are operating principles, and they are short.

The killer writes the record. A process cannot log its own sudden death. So every path that ends another process — a

supervisor replacing a portal, a launcher stopping a writer, a watchdog reviving a wedged daemon — writes one line naming

what it did, to whom, and why, before it acts. A process that leaves on its own writes one line saying why. When a writer

disappeared without a trace in September 2026, the trace was reconstructed from three logs and a kernel journal; the rule

exists so that it never has to be reconstructed again.

A daemon's life is its own. The single writer's main thread once waited on the child process it had spawned for its portal;

when the supervisor replaced that portal, the writer quietly exited. A long-lived process blocks on its own shutdown signal and

nothing else.

Accelerators sweep victims, not the store. A nightly task that decides what to retire must iterate the collection of candidates

written at write time — never the store, never bodies to decide a derived fact. The two nights this rule was broken, memory

rose by six hundred megabytes and requests queued for two minutes. The night it was kept, the same task took nothing.

A warning must mean something. A warning that fires every minute in a healthy system hides the one that matters.

Saturation is warned once, when it is sustained and material, and closed with a line when it drains. Every long operation has a

time budget and says when it was cut.

Busy is not wedged. A process that misses a health probe while burning CPU is working. Replacing it is the failure, not the

cure.

Coordinates are written, not computed. The Source Viewer, the CLI, and any future Agent read the same Set memberships.

The browser never groups, ranks, or infers; when a value is missing it says so.

Public is the default; labels are not. Everything published under the archives is readable by a guest, read-only, and the

exclusions are enforced on the server, not in the page. Counts derived from an answer key are public; the answer key is not.

Stage exits are criteria, not feelings. A stage of a workbench is finished when a written list of observable facts holds on the

public server, with no operator command — not when it seems to work.

The observation cycle is the method. A build is delivered as a Seed; it is expanded and its evaluations run in a sandbox; it is

planted on the server; the server's logs are read against the build; every defect is reported with a root cause and a location; the

order for the next build is written before the next build. The librarian who keeps that cycle changes no code. Two weeks of it

turned a bench that ran once into one that runs every day.

The second week added five.

A refusal is a result, and it is visible. A write a grant refuses returns its reason, logs one line, and fails the job that carried it.

The day a job ended "done" having written nothing, an hour went to finding out that the admin was not named admin.

Privilege is a role; membership is written. A session is privileged because its scopes say so, never because its identifier

equals a literal. A society's group is created with the world's admins in it; the gate is not widened to let them in later.

Derived state needs no command. A leaderboard, an index, a coordinate layer — anything regenerable — is produced by the

write that changes its inputs and verified at boot. A document that asks an operator to type a command to produce derived

state is wrong, and was.

A grid change retires; it never deletes. What is no longer valid is marked, skipped, and counted. What already ran keeps its

history.

Re-index from the truth. When a new build changes what an accelerator indexes, the boot repairs the index from the

canonical atoms and re-applies every idempotent definition — a sweep, a policy — exactly as the driver re-arms itself on a

new build. An index that only new writes join is a lie about the old ones.

None of these rules is about machine learning, or about plants. They are what it costs to let a semantic world live in public —

and they are the reason the universe and the horizon must be kept apart.

One gate. A system that sells provenance cannot afford more than one place where permission is decided. Every check that

lives somewhere else — "is this caller the owner of the avatar", "does this role carry the librarian scope", "may this job be

enqueued" — is a second gate that nobody listed and that will, one day, disagree with the first. Akasha keeps one table,

readable on a page: a handful of roles, each with its groups, what it may do, and where. An identity is assigned a row by one

line of one file. Every act — read, say, run, record, annotate, publish, provision, admin — passes one function that reads the

table, the line, and a few facts with one writer each, and answers yes or the name of what was missing. The answer is stamped

into the record the act produced. That stamp is the provenance: not "this atom exists", but "this atom was made by this

identity, under this line, for this reason, and here is the line". A permission model you can read is a permission model you can

audit; one you cannot read is a hole, however carefully each of its pieces was written.

A citation is an input. For several days in September 2026 the news programme on the public server named, in its record, an

item from its notebook as the source of each segment — and the model had never been given the item. Its prompts had lost the

place where the item was inserted when the programme moved into its declaration, so the model was told it was handed a

story and invented one, while the record said which real story it was. The record was well-formed, and wrong. The rule that

follows is mechanical: an observation may name a source only if that source's text was part of the input that produced it, and

the platform, which composes the model's input, records which sources it composed and refuses any other. A provenance a

program asserts is a claim; a provenance the system recorded while doing the work is a fact.

Epilogue — Toward a Concept-Oriented Future

Throughout the history of computing, progress has often come from discovering better abstractions.

Files allowed information to survive.

Programming languages separated algorithms from hardware.

Operating systems separated applications from machines.

Objects separated behavior into reusable structures.

Networks separated computation across distance.

Pipelines separated programs into composable processes.

Each abstraction made software more capable by reducing unnecessary complexity.

Akasha does not reject these ideas.

It builds upon them.

Its proposal is simply that another stable abstraction now becomes possible.

The concept itself.

A concept survives changes in language.

It survives changes in software.

It survives changes in storage.

It survives changes in interface.

Concepts persist while implementations evolve around them.

If software wishes to become a long-term partner in human thought,

its architecture should begin where human thought begins.

With concepts.

Four Axes

The whole design can be held in four interdependent axes.

Concept. Meaning exists independently of any implementation-specific representation. Concepts can be defined, observed,

compared, reinterpreted, connected, projected, and revised.

World. Humans, machines, sensors, actuators, observations, roles, and state inhabit one semantic world without separate

ontological universes.

Semantic Machine. Knowledge operations have Akasha-native computational boundaries, meaningful from a memory

operation to a cache, to parallelization, to distributed placement, and potentially to a hardware instruction.

Workflow. Knowledge and executable process share one memory substrate, so work is remembered, resumed, rolled back,

transported, delayed, distributed, and potentially rewritten by Agents.

They are not four features.

They describe one computational environment.

Figure E.1 — The Unified View

                       WORLD

                         │

          ┌──────────────┼──────────────┐

          │              │              │

       Sources         Agents       Telemetry

          │              │              │

          ▼              ▼              ▼

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

     durable universe  ·  active horizon (accelerators)

                         │

        DurableSemanticStore · negotiated backends

                         │

          semantic instruction boundary

                         │

                 possible hardware

   and, across the same structure:

   Set / Scope → Projection → memory residency → placement

            → distribution → delay-tolerant, constrained execution

   Set as coordinate → chronon → epoch → cache identity

Akasha is not a stack of unrelated features.

The same semantic primitives recur at every scale.

The Age of Implementation

This is particularly relevant in the age of artificial intelligence.

Large language models have dramatically reduced the cost of implementation.

Generating code,

interfaces,

documentation,

and workflows

is becoming increasingly accessible.

As implementation becomes easier,

conceptual design becomes more valuable.

The limiting factor shifts.

Not how quickly software can be written,

but whether it represents the right concepts.

Concept-Oriented Computing therefore does not compete with AI.

It complements it.

Human expertise remains responsible for defining meaning.

Concept Models organize that meaning.

LLMs help transform it into software.

The relationship becomes collaborative rather than competitive.

Implementation accelerates.

Concepts remain human.

A Post-AI Perspective

Akasha should not be framed primarily as a response to the AI-agent market.

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

LLMs matter because a new kind of semantic client suddenly exists.

But the architecture does not begin from LLM → tools → memory → agent.

It approaches AI after looking at life, environment, cognition, autonomy, embodiment, self and non-self, memory, society,

culture, and action — which is why enactivism, autopoiesis, and the older contemplative traditions are relevant to a research

program on Akasha.

Temporarily move AI out of the center, travel through older and broader theories of life and cognition, then

return and ask what AI looks like from there.

A possible direction, not a conclusion.

The same principle extends beyond software development.

Researchers,

teachers,

engineers,

historians,

artists,

designers,

and domain experts

already possess rich conceptual worlds.

Most software asks them to translate those worlds into technical structures.

Akasha attempts the opposite.

Software should learn the conceptual world of its users.

Not the other way around.

This philosophy naturally extends beyond today's computers.

Future participants may include robots,

scientific instruments,

distributed sensor networks,

autonomous laboratories,

or technologies that do not yet exist.

Their implementations will differ.

The semantic substrate need not.

Concepts provide continuity across changing technologies.

For this reason,

Akasha should not be understood merely as another application,

another database,

or another AI framework.

It is an experiment in building a durable conceptual foundation beneath them.

Applications may disappear.

Interfaces may evolve.

Programming languages may change.

Storage engines may be replaced.

Concepts remain.

The goal is therefore not to predict the future of computing.

The future will almost certainly surprise us.

Instead,

the goal is to build an architecture capable of surviving it.

One in which meaning remains stable,

while implementations continue to evolve.

Perhaps this is ultimately the role of software.

Not to replace human thought.

Not even to imitate it.

But to become a place where thought itself may continue to grow.

The substrate has been built.

It has survived reality — load, crashes, restarts, disconnected iPads, a public server.

The phase that follows is not building the foundation.

It is using it:

BUILD THE SUBSTRATE

        ↓

THE SUBSTRATE SURVIVES REALITY

        ↓

USE THE CONCEPTS

        ↓

BUILD AND INHABIT SEMANTIC WORLDS

A machine has read four hundred plant photographs twice inside one such world — once before it learned and once after —

and a reader can follow the change item by item.

A seminar of people will read inside another.

The expedition is only beginning.

Reading the History

Akasha has accumulated many implementations, experiments, names, and subsystems.

Some appeared recently.

The ideas beneath them usually did not.

Do not mistake implementation chronology for conceptual chronology.

A few guardrails for anyone — human or LLM — who reads the repository, the development diary, or this paper:

Telemetry did not make Akasha dynamic; it demonstrated a dynamic mapping the Atom was designed for.

LLMs did not cause Akasha to invent an Agent model; they were a new first-class client for a participation model that

already existed.

Silica was not invented because SQLite was bad; SQLite remains a strong implementation, and Silica realizes the older

goal of a native semantic instruction boundary.

World and Workbench are not a new direction; they are implementation catching up with a long-standing one.

Workflow is not an application feature; it is part of the memory model.

Seeds do not exist mainly because Akasha is local-first; they express the requirement that knowledge and work

germinate in heterogeneous, constrained environments.

The semantic macro-cache is not merely a performance optimization; it tests whether attention can govern memory

residency and, by extension, placement.

Akasha is not an LLM agent framework; an LLM is one client in a broader semantic world.

Chronons are Sets, not a clock service; there is no "axis" type, and reading time is intersection.

The layers in the Source Viewer are read from coordinates written at mint; the browser computes none of them.

The durable universe / active horizon split was not adopted from another system's API; the pattern was recognized in

Akasha's own incidents and then named, with HydraDB's design as a useful comparison.

The condition-sweep platform, the three-source bench, and the model registry (Chapter 11) are designs decided in

September 2026 whose implementation follows; the completed cycle they build on is real.

When a new requirement appears, do not immediately create a new subsystem.

First ask whether Atom, Link, and Set — through Concept, Scope, Projection, Agent, Role, World, Society, Workbench,

Chronon, and Workflow — can already express it.

Introduce a new primitive only when the existing model genuinely cannot say it without distortion.

The full statement of these principles, with the reasoning behind each, is Akasha — Foundational Design Context.

Acknowledgements

Akasha was developed as an independent open-source project under practical constraints that shaped its philosophy as much

as its implementation.

Much of its architecture emerged through long conversations with Large Language Models—not as autonomous designers,

but as tireless collaborators.

They questioned assumptions.

Proposed alternatives.

Reviewed designs.

Generated prototypes.

Searched for inconsistencies.

And, perhaps most importantly, allowed ideas to evolve through dialogue.

The concepts presented in this paper remain human decisions.

The journey toward them, however, became a genuinely collaborative one.

The ideas presented here were shaped by many conversations—

with books,

with history,

with colleagues,

with open-source communities,

and, in recent years,

with Large Language Models.

Like every participant in an Akasha Society,

each contributed a different perspective.

The responsibility for the concepts remains entirely the author's.

The gratitude is shared.

---

## Chapter 18 — The World Is Plural

There is a temptation, once a system can hold a great deal of knowledge, to speak of
*the* world model — one representation, kept current, that everything reads from. Akasha
does not work that way, and this chapter says why, and what it does instead.

A world, in Akasha, is not one model. It is many **projections** of the one durable
memory, each built for a purpose, a time and a scope. The financial view of a city
program and its logistics view are not two opinions about one truth; they are two
observation geometries, each showing what it is shaped to show and silent about the
rest. A projection, in this sense, is not a way of displaying the world. It is a
contract for *what can be observed in it, what can be compared, and what can be
checked*. That is the first idea of this chapter: a world model is plural, and a
projection is an observation geometry.

Because a projection is built from the durable universe by a transform, it can always
say where it came from. Each one carries its Sources and their digests, the time it
observes, the time it was built, how fresh it is allowed to be, what authority and
evidence stand behind it, and — this is the part usually left out — **what it threw
away**. Every projection discards something. A daily summary loses the order of minutes.
An average over a department loses the person. An embedding blurs the line a negation
draws. A permission model mistakes the way things are actually done for the rule on
paper. Akasha treats those losses as information, not as the small print of a chart: the
interface shows not only what a projection makes visible but what it *cannot
distinguish*.

A Workbench, then, does not reason over "the knowledge." It **binds** the particular
projections it will use, by their exact version, before it starts — so that when it
produces a result, you can return to precisely the world it was reasoning in and get the
same answer. A newer version of a projection does not quietly slide under a running
piece of work; swapping it is a deliberate act, recorded as such. This is the same
discipline the rest of Akasha keeps about memory: a result is only as trustworthy as the
coordinates it names, and here the projection is one of those coordinates.

With the projections bound, the Workbench can reason in three postures, and it is worth
keeping them apart because people usually run them together and then argue past each
other. It can reason **under** the world — plan and choose within the projections as
they stand, which is ordinary operation. It can reason **without** a chosen constraint —
suspend a rule on purpose and follow the counterfactual, to test a premise or imagine a
different order; the suspended rule is not deleted but set aside, marked, and given no
power over anything real. And it can reason **about** the world — take the projection's
own blind spots, staleness, missing axes and contradictions as the thing to be reasoned
about, and come back not with an answer inside the world but with a *proposal to change
how the world is represented*. The first searches for a better solution; the last
searches for a better way of seeing. Akasha makes both first-class, and keeps the output
of the second always a candidate — a new way of seeing is proposed, compared against the
old on the same problem, and never allowed to overwrite it on its own.

A result then has to be checked, and here Akasha refuses a common shortcut: it keeps
three different questions apart. Is the result internally consistent? Could it hold at
the same time as everything else — the other projections, the policies, the resources?
And does it correspond to what can actually be observed in the world? These are not
degrees of the same check; they are different checks, and passing the first says nothing
about the third. A result that has only passed the first is shown as an unverified
hypothesis, never as a fact, and "not yet observed" is never painted the same color as
"confirmed." When something fails, the failure is named — was it the reasoning, the
evidence, a projection that was incomplete or stale or simply the wrong one, a missing
axis, a constraint the world would not allow, a permission that was not held, or an
action that failed when it reached the world? — so that "the agent was not good enough"
can never quietly stand in for "we were looking through the wrong lens." When several
attempts fail the same way, that pattern is itself a finding: it can propose a missing
axis or a new projection, rather than only trying the agent again.

All of this freedom — suspending rules, taking an extreme position, proposing the
disruptive — lives entirely inside the Workbench, and it buys no authority over reality.
This is the line the chapter ends on, because it is the one that matters most. A thought
experiment may go as far as it likes; a change to the actual world goes only one way,
through the path Akasha already has: a proposal, an evaluation, a human or an authority
or a moderator at the gate, a grant, the act, and the observation that comes back. An
agent can draw a new map; it cannot make the territory follow it. And because a fluent,
confident answer makes it easy to forget whose reasoning it was, the interface keeps a
deliberate friction: fact and inference and hypothesis and proposal and decision are
shown as different things, what a machine produced is marked apart from what a person
confirmed, and a strong claim cannot be promoted without its grounds. The point of a
plural world is not to multiply opinions. It is to make the act of looking honest — to
say, every time, through which lens we looked, what that lens could not show, and how far
what we concluded has actually been checked against the world.
