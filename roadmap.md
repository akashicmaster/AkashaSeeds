# Akasha Roadmap

*Where this is going — and why it matters.*

This roadmap states directions, not dates. It is grouped by how settled each
direction is: what the substrate already does, what is being built on it now, what
follows, and what is still research. Anything marked research is evaluated in an
experiment world before it is allowed near the canonical one.

---

## Where we are today

Akasha is a local-first, concept-oriented semantic operating system. Knowledge is
stored as content-addressed **atoms** linked by typed relations and grouped into
**sets**; typed **Concept Models** project those atoms into structured views. The
design keeps three things strictly apart — the immutable **operand** (an atom), the
**operator** (a Concept Model), and the **agent** (a human, an LLM, or a script) —
and that separation is what the rest of the system is built to protect.

Two commitments run underneath. Memory has two layers: a **durable semantic universe**
that is the only source of truth, and an **active horizon** — indexes, caches,
projections, materialized sets — that is an accelerator, disposable, and regenerable
from the universe. And time is not a clock service: a **chronon** is a set, and reading
history is intersection.

What is shipped and verified:

- **The substrate** — atoms, links, sets, Source, World, Observation, Society,
  Workbench, Workflow, Chronon — running offline on modest hardware, and on a public
  server.
- **The learning workbench** — the first complete observe → learn → observe-again
  cycle, with its numbers.
- **The seeds distribution** — the whole system as a single self-extracting file that
  germinates into a running instance, with user knowledge protected across updates.
- **The platform / application boundary.** The platform is now a **pure substrate**:
  it imports, names and depends on nothing of any application, and it boots, serves and
  passes its own tests with every application removed. An application reaches the
  platform only through a published **specification** and a stable API; it builds its
  concept models, packs, pages and declarations without touching one line of platform
  code. This boundary is the foundation everything below rests on — a flagship feature
  should not sit on a base that still leaks across its own layers.

The first **regular release** of the seeds series stands on that boundary: the layer
separation is normalized, the architecture does not wobble, and the substrate carries
no conspicuous defect.

---

## Now — a no-code workbench, and the first world-reasoning foundations

**Build an application without code.** The Workbench gains a no-code authoring GUI
(Studio): from a seeds install, a developer composes concept models, declarations and
pages and wires them into a running application, without editing platform code. The
code path stays open — a developer may still author a Concept Model and wire it in
JavaScript — but it is no longer the only way in. The look and feel of that GUI belongs
to the application; the authoring substrate underneath is reserved to the platform, and
every GUI action maps to a command the CLI already has.

**The world is plural — the first foundations.** A world is not one model but many
**projections** of the durable universe, each built for a purpose, time and scope.
The early, foundational pieces land first, kept small so they do not expand the
release they ride in:

- every projection carries its **source lineage, observation time, freshness and
  scope**, and a run is pinned to the exact projection it reasoned over, so a result is
  reproducible;
- a result records **what kind of claim it is** — observation, hypothesis, verified —
  and an unverified result is shown as a hypothesis, never as truth;
- a **projection contract** and a **binding manifest** are introduced as ordinary
  concept models (not new kernel primitives), so what a projection can and cannot
  observe is explicit and machine-readable;
- the Studio gains a **read-only projection inspector** — what is bound, how fresh,
  how much is covered, what was lost in compression.

**Instance email, on the protocol model.** Mail is added the way other protocols
already are — a platform transport, like the web portal, off by default on a seeds
install but present in the code. An instance administrator can grant a client an
address on the instance's own domain, as a client-management function continuous with
session management; inbound mail resolves to that client. The transport faces the
public internet, so it is safe by construction: no open relay, size and rate caps,
sender checks recorded with each message, and the port stays closed unless a
deployment declares it.

---

## Next — reasoning with, without, and about the world

The reasoning layer the projection foundations make possible:

- **Three modes.** *Reason under the world* — plan and choose within the current
  projections as constraints. *Reason without selected constraints* — build a
  counterfactual with a constraint deliberately suspended, recorded as suspended, with
  no authority to touch reality. *Reason about the world* — treat a projection's own
  gaps, staleness, missing axes and contradictions as the subject, producing a
  projection-update or world-change proposal, never a direct change.
- **Three levels of validation.** Local consistency, global satisfiability across
  projections and policies, and correspondence to the observable world — kept distinct,
  so passing the first is never shown as passing the third, and *not observed* is never
  shown as *passed*.
- **Cross-projection work** — aligning different observation geometries on explicit
  keys, time, units and evidence, and recording what was assumed and what was lost.
- **Blindness diagnosis** — when several agents fail the same way, or results swing
  with the projection, the system proposes a missing axis or a new projection instead
  of only retrying the agent.
- **Structural diversity and replay** — heterogeneous agent roles, and long
  deliberations run on a daily budget and recorded as chronons, replayable fast for
  review (replay fires no real effect).

**Counterfactual freedom stops at the effect boundary.** Inside the workbench, removing
constraints and proposing the radical is allowed; the only path to a real change runs
proposal → evaluation → human / authority / moderation → grant → execution →
observation.

---

## Later — the thin client, and seeing the work

- **Field Notes — a thin client.** A pared-down, local-first app: capture, ask,
  connect, inspect the source, mark uncertain, approve or reject a proposal, sync.
  Knowledge continues across a person's devices; light work is local-first and heavy
  work is deferred to a VPS or archive — all through the same operations and the same
  provenance. The experience to aim at is an intelligent iCloud, not a new silo.
- **Seeing the work.** Visualization surfaces built on the projection layer: a
  cross-projection canvas that edits alignment and conflict rules (and saves the result
  as data, not as canvas state), and a validation matrix that shows each claim's three
  levels — where *not observed* never shares a color with *passed*.
- **The cognitive seam.** The more smoothly a result is presented, the easier it is to
  lose the boundary of who reasoned. The interface keeps the necessary friction: fact,
  inference, hypothesis, proposal and decision are told apart; AI-generated and
  human-confirmed are distinguished; a strong claim cannot be promoted without its
  grounds.

---

## Research track

Evaluated in an explicitly-marked experiment world, promoted only after it survives
review — never dropped straight into the canonical universe.

- **An embedded situated inference engine** — not a small LLM clone, but a lightweight
  reasoning layer over the durable memory, judged on local cost, traceability,
  incremental update, uncertainty and counterfactual usefulness rather than on prose.
- **Adapters as observers** — LoRA, steering, tool and prompt policies treated as
  versioned participant components with their own provenance, assigned per run, with no
  implicit continuous learning.
- **Internal-state observation** — introspection and activation analysis as a *source*,
  not a self-authority, with its confounders recorded.
- **Distributed source** — referencing other Akasha repositories by locator, digest,
  license and provenance receipt, without central collection; meaning and authority
  stay on the Akasha side.
- **Limited anchoring** — blockchain used only for digest anchors, signatures,
  timestamps and consent receipts, never as a truth layer for meaning.

---

## Engineering, under all of it

- **Keep the boundary pure.** Every release proves the platform still boots, serves and
  passes its suite with every application removed, and that no application name appears
  in platform code.
- **Then the inside.** With the boundary between the layers settled, the next depth is
  the dependency graph *inside* the kernel — import direction, internal layering,
  cycles — cleaned on the same principle. This follows the no-code GUI, not before it.
- **A fresh cell on each format change.** The design keeps the history of its mistakes;
  during development a format change is a clean start, not a migration, and old data is
  archived, never silently misread.

---

## Principles that do not change

1. **Source precedes interpretation.** Every projection, inference and critique traces
   back to a source or an observation.
2. **Atoms, links and sets are the whole persistent substrate.** New capabilities are
   concept models over them, not new kernel primitives.
3. **The durable universe is the only truth; the horizon is disposable.**
4. **A world is plural.** It is a set of provenance-linked projections, not one model.
5. **A projection is an observation geometry** — a contract for what can be observed,
   compared and verified, not a way of displaying.
6. **Counterfactual freedom stops at the effect boundary.** Thought is free; changing
   reality goes through proposal, grant, gate and observation.
7. **The platform is a pure substrate.** It carries no reverse dependency on any
   application; an application consumes it through a specification and never edits it.

---

## How to contribute

Akasha is MIT-licensed and built in public. The substrate, the seeds distribution and
the documentation are open; the design documents — the White Paper and the Foundational
Design Context — are the place to understand why the system is shaped the way it is
before proposing a change. The most useful contributions right now are concept models
and ontology packs authored against the published specification, and honest reports
from running a seed as a real user would.
