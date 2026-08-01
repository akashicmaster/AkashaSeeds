# Akasha Roadmap

*Where this is going — and why it matters.*

---

## Where We Are Today

Akasha started as a local-first semantic graph running on a single SQLite file.
It grew incrementally — often written on an iPad mini, between trains and quiet evenings —
into something that manages knowledge across multiple users, languages, namespaces,
and access scopes, with a full concept-model ecosystem on top.

The core is stable and the engineering foundation is solid. The write path and orchestration
layer were rebuilt from the ground up for the open-source release, and on that base the outward-
facing layers — a native storage engine, inductive discovery, an external-LLM interface, and a
shared dialogue space — have now shipped:

- **Security model hardened** — signed, expiring session tokens (`gbk:` / `akt:`, HMAC-SHA256);
  server-set transport trust (`NETWORK` / `LOCAL` / `INTERNAL`); PBKDF2 + per-user-salt
  passphrases; fail-closed scope enforcement on every read; `iam.manage` capability gating;
  internal-only system identities. (`security-audit-report.md`, `security-fix-proposal.md`)
- **Harmonia orchestration, slices 1–4** — the WriteQueue is a priority queue served by a
  single worker (priority changes *order*, never parallelism); the JCL worker schedules at
  step granularity with PERT `depends_on`, bounded transient-only retry, and soft timeouts;
  a **single-route write guard** forces every memory write through one orchestrated path;
  cross-DB bundles commit forward with a boot-time orphan scan.
  (`docs/for-llm/orchestration-architecture.md`)
- **Minimal workflow reception** — a workflow is stored *as an executable atom* (CSL body,
  `wf:` alias) and run as one bounded JCL job. The static content-addressed graph is
  beginning to be re-read as a dynamic execution model. (`docs/for-llm/workflow-reception.md`)
- **Meaning layer — self-owned, degradation-first** — semantic embeddings in three tiers
  (feature-hashing floor → learned PPMI+SVD mid tier → optional sentence-transformer), a
  boot auto-learn that bakes vectors onto atoms, the self-expanding-ontology loop
  (`gap.scan` → `gap.fetch` → weave → `semantic.learn`), structural node embeddings, image
  classification via the **LiteRT** backend ladder (`image.profile`), and the link-based
  emotion axis (`emotion.profile`). Zero heavy dependencies; degrades cleanly.
  (`docs/for-llm/semantic-layer.md`)
- **One data I/O route** — a single disk-I/O layer (`fileio.py`) and one **pipe interface**
  (`pipeline.py`: `Source` | `Sink` | `run_pipeline`) replace the former scattered import/
  export paths. Files (CSV/JSON/MD/TXT), in-memory uploads, the `table` model (both ways),
  sets, client-receive, and lens projection into a concept model are all the *same*
  interface — the Unix pipe of the data plane. Contexa input (`contexa.ingest`) and Jataka
  output (`jataka.present`) ride it live. (`docs/for-llm/io-pipeline.md`)
- **Silica — a self-owned native storage engine** — a hardware-mappable *pseudo-ISA* memory
  store (banked hash keyspace, custom WAL, transactions/rollback, checkpoint, read cache).
  `SilicaBackend` implements the `AkashaBackend` instruction set and is a **drop-in equal of
  the SQLite backend** (parity verified). This is the SQLite → own-ISA migration path — and
  the concrete foundation under the hardware arc below. SQLite stays the default; Silica is
  the verified alternative. (`docs/for-llm/silica-store-pseudo-isa-spec.md`)
- **nebula — inductive schema formation** — a third explorer that surveys accumulated concept
  atoms for dense clusters sharing a relation schema (an emerging concept model) and proposes
  it for a human to plant. Unlike `assoc` (local gap-fill) or `dream` (incidental affinity),
  nebula is global and inductive — it *closes the induction → deduction loop*, so categories
  like fruit or recipe can crystallize after the fact. (`docs/for-llm/nebula-spec.md`)
- **MCP service — external LLMs as first-class clients** — a Model Context Protocol server
  implemented in **pure stdlib (no `mcp-python-sdk`)**, so it installs on the seeds/edge tier.
  Two transports ship together: **local stdio** (`akasha.py --mcp`, `TRUST_LOCAL`, attaches to
  the daemon for shared memory) and **remote HTTP** (`/mcp`, `TRUST_NETWORK`: anonymous →
  guest read-only, `Bearer akt:` → scoped write). The kernel is the capability gate. 15 tools,
  including `akasha_command` (run any CLI command). (`docs/for-llm/mcp-spec.md`)
- **society — a virtual dialogue space (avatar-mediated, LLM-agnostic)** — a first-class chat
  space on a group: it holds a roster of avatars (`cast`s), owns the timeline, and defines turn
  ordering. *cast = persona; society = space.* Multiple named channels per group, flat + reply
  threading, crossing with the `world` model, pseudonymous-by-default participation. A society
  is not just a chat room but a **coworking space** — the anchors for governance (`kind=cowork`,
  a responsible `society.decider`) are in place, with deliberation/voting/decision and society-
  scoped workflow reserved on the same substrate. (`docs/for-llm/society-space-spec.md`)
- **LLM connection experiment kit** — two use cases over MCP: **UC1** human ↔ LLM natural-
  language chat through a society, and **UC2** *LLM-as-operator* (a human's request → the LLM
  runs CLI-equivalent operations over MCP and reports back). Ollama drivers included, with a
  `--mock` mode that verifies the plumbing without a model. (`docs/for-llm/llm-connection-experiment.md`)

The base is durable and the outward-facing layers are live. What follows is the near-term work,
then the longer arc.

---

## Now — validate the LLM collaboration, and harden for beta

The substrate is shipped; the immediate work is to *use* it and polish for release.

- **Run and tune the local-LLM (Ollama) connection experiment.** Drive UC1 and UC2 on real
  hardware and tune tool selection, context budget, and English response quality. The strategy
  is deliberate: **bootstrap on a low-accuracy local model now** so the substrate — tools,
  provenance guardrails, confirm-staging, the society/workflow seams — matures. When more
  capable (paid) LLMs connect over the *same* MCP surface later, they inherit a proven
  substrate and extract far more performance with no redesign.
- **Beta pre-ship polish.** Cookbook (basic ops, CSL syntax, adding ontology), documentation
  consistency, a smoke test of every RPC method, and the archives portal's display/links.

---

## Next — a few releases out

- **Curation → Presentation → Export — one meaning graph, many tellings** (a headline
  differentiator). The pipeline is already **Semantic Graph → Interpretation → Presentation →
  Export**: `curation.project` / `pres.export` render a curated path through the Consciousness
  interpretation layer (`generate_view`) into a **Scroll** or **Kamishibai** artifact today. The
  evolution: (1) **project the same graph into multiple interpretations** — different lenses,
  emphases, and emotional tones over the identical atoms; (2) **more presentation targets** —
  Scroll / Kamishibai (shipped) + **Markdown** + **LLM narration** + future forms; (3) the key
  idea — **the form is chosen by a concept model, not by UI**. Switching from a data table to a
  scroll to a narrated story is a *lens / presentation-model* swap on the same pipe, not a
  bespoke screen. **LLM narration** plugs in here (degradation-first): `jataka.present … as=narrative`
  already emits a deterministic structural template with no model; an injected narrator (over MCP,
  the same substrate as the content ops) lifts it to generated prose — the meaning stays in the
  graph, the LLM supplies only the telling. This is the strongest "same substrate, many faces"
  story to show off. (`docs/for-llm/curation-presentation-scroll-spec.md`, `io-pipeline.md`)
- **LLM-assisted content operations** (all on the provenance guardrail + confirm-staging): long-
  atom summarization (`sys:summary_of`, `provenance=inferred`); short title / auto-alias
  generation **staged as suggestions and human/decider-confirmed** (aliases are a definition-
  completeness surface — never written canonically by an LLM directly); condition-driven
  autonomous bot avatars; and a "secretary" avatar that grounds command recall via a command-
  catalogue read tool instead of hallucinating syntax.
- **Society-scoped governance / workflow** — deliberation, voting, and decision by the
  responsible cast, turning a society into the *unit of workflow control* (proposals = steps,
  the decider gates transitions). The bridge to governance-driven multi-agent collaboration.
- **Multi-LLM pipeline + async handoff** (#29) —
  one agent explores, another generates CSL; `pending_links` gives disruption tolerance (DTN),
  so agents collaborate without being online at the same moment. Remove the human relay.
- **Knowledge-exchange ecosystem** (#26) —
  Akasha / thesaurus instances safely exchange curations, ontology, and links; content-
  addressing unifies identical knowledge. Portable, signed, provenance-preserving exchange units.
- **Cloud offload / on-demand retrieval** (#27) —
  an iCloud-style "what isn't local is fetched on demand" tier at the atom/cortex level, for a
  personal cortex and a shared group graph alike. SQLite stays ground truth; the cloud is a
  volatile eviction tier. (*Exchange* and *retrieval* are orthogonal axes.)
- **Silica native-engine tuning** (robustness is proven green; this is speed/indexing only) —
  group-commit fsync amortisation, O(1) `status` counters, auto-checkpoint, and secondary
  link/collection indexes to replace the remaining O(n) scans. Drop-in behind the unchanged
  `AkashaBackend` contract; not required for the reference release. Backlog + code anchors:
  `docs/for-llm/silica-store-pseudo-isa-spec.md` (Performance & indexing backlog).
- **Meaning-layer extensions** — vision (detection, caption/OCR, gap-driven image fetch;
  #40), an external-NLP sentiment
  second track (#42), and multi-locale
  NLP (mixed-script text).

---

## The Longer Arc

The near-term steps serve one line: collapse the human relay, let knowledge move between
instances and agents, and let the same graph reach from the cloud down to a sensor — and,
eventually, into silicon.

### Collapsing the human relay (MCP + self-expanding graph)

Today the loop is: *human explains ontology → LLM writes CSL → human runs it → human reviews →
repeat.* The human is the relay and every session starts blank. The MCP service collapses it:
an LLM scans the existing ontology directly (`akasha_explore` / `akasha_gap_scan`), fills precise
structural holes, and checks its proposals against what already exists. The human stops
explaining the graph before each session and instead sets goals and evaluates outcomes:

```
Richer graph → better LLM contributions → richer graph → ...
```

### Multi-LLM collaboration without a shared protocol

Group sessions — and now the **society** dialogue space on top of them — let multiple clients
(human or LLM) share one graph space, with scope-controlled access, attributed writes, and
preserved temporal order. Two LLMs from different providers collaborate because their **common
language is Akasha's concept model, not the transport protocol**. `pending_links` adds disruption
tolerance: one agent explores, another generates CSL, a third validates — none needing to be
online at the same moment.

> A low-cost, local-first, semantically grounded multi-agent environment that doesn't require
> proprietary orchestration infrastructure or cloud accounts.

### Akasha as the hippocampus for AI

LLMs are extraordinary pattern-recognition engines with no episodic memory. Every conversation
starts blank; long-term experience disappears at context reset. Anchored to an Akasha session, an
LLM gains persistence (experiences as atoms and typed links), recall by graph traversal,
preserved temporal structure, and scope-isolated memory that can be selectively shared through
group sessions. The result is a complete cognitive loop:

```
Neocortex (LLM)         — pattern recognition, language generation
Hippocampus (Akasha)    — episodic fixation and recall
Sensorimotor (hardware) — interaction with the physical world
```

### One substrate across every scale

`AkashaBackend` defines ~50 primitive operations — a minimal instruction set for semantic
memory — with no reference to files, tables, or SQL. It describes *what the substrate must do*,
not *how*. Different scales swap the implementation; the upper layers (composite, session, IAM,
concept models) run unchanged:

| Scale | Backend | Status |
|---|---|---|
| Local / edge | SQLite | ✅ Working (default) |
| Native ISA store | **Silica** — banked pseudo-ISA, custom WAL/txn | ✅ Drop-in parity with SQLite; the own-ISA migration path |
| Cloud / distributed | Object store + event-driven growth (S3 + Lambda affinity) | 🔲 Offload seams exist (#27); full backend designed |
| Embedded / IoT | Hardware register mapping | 🔲 Seams ready; first PoC planned (#28) |
| Silicon | Custom chip implementing the ISA | 🔮 Long-term — now standing on the Silica pseudo-ISA |

**IoT.** Override `get_chunk_raw` for a live sensor read and `put_chunk_raw` for an actuator
command; scopes become device-authorization capabilities. The semantic graph becomes the control
plane *and* the memory of what the system reported and when. A Raspberry Pi with a sensor array
becomes a semantic edge node — the same graph and upper layers move from seeded-value simulation
to real control by swapping only the backend.

**Silicon.** The fabless era means you no longer need a fab to design a chip, and RISC-V showed a
clean open ISA is a legitimate basis for real hardware. `AkashaBackend` *is* an instruction set
architecture for semantic-memory operations — and **Silica is that ISA already realized in a
banked, WAL-backed store**, one step from a register map. Implemented in dedicated silicon
pipelines (on-chip graph traversal, scope filtering, alias resolution), its performance profile
would be entirely different — a natural fit for robotics control planes, embedded sensor
networks, and low-latency edge inference. Not next year; not structurally impossible either. The
architecture was built to support it.

---

## How to Contribute

The GitHub issues are the live worklist. Good places to push:

**Near-term (LLM + multi-agent):**
- Run the local-LLM connection experiment and report findings (UC1 chat, UC2 operator)
- Test multi-LLM group/society sessions and DTN handoff (#29)
- Prototype the reserved society governance/workflow (deliberation → vote → decide)

**Medium-term (edge + cloud + IoT):**
- Implement a cloud offload / retrieval tier (#27) and deploy targets (#25)
- Build the sensor-node IoT binding, simulation-first (#28, #17)
- Extend the declarative workflow DAG (#24)

**Long-term (silicon):**
- Map the Silica pseudo-ISA onto an FPGA register interface
- Benchmark hardware-accelerated graph traversal vs. the SQLite baseline

**Concept-model work (always open):**
- Extend the thesaurus ontology with new namespaces and domains
- Write semantic extensions for your field of expertise
- Connect Akasha to external knowledge sources via import pipelines

---

The architecture is ready.
The instruction set is defined — and now realized as a native engine.
The concept-model ecosystem is live, and external intelligence can plug into it.

What remains is the work of connecting it to the world.

*One contribution at a time.*

---

**→ Start with the concepts:** the architecture-vision overview — the full technical picture
**→ Start building:** [`quick-start.md`](quick-start.md) — running Akasha in 20 minutes
