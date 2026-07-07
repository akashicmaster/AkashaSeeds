# Akasha Roadmap

*Where this is going — and why it matters.*

---

## Where We Are Today

Akasha started as a local-first semantic graph running on a single SQLite file.
It grew incrementally — often written on an iPad mini, between trains and quiet evenings —
into something that manages knowledge across multiple users, languages, namespaces,
and access scopes, with a full concept-model ecosystem on top.

The core is stable and the engineering foundation is solid. Recently the write path and
orchestration layer were rebuilt from the ground up for the open-source release:

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

The base is now durable enough to build the outward-facing vision on. What follows is the
plan for the next quarter, then the longer arc.

---

## This Quarter's Goals

Six tracked goals, each grounded in existing code seams and filed as an issue. The GitHub
repo is used less as a private worktree than as a **live broadcast** — each goal is a unit
of work to build in the open, showing a static atom graph being redefined as a running model.

### Server quality — run anywhere ([#25](https://github.com/henrigrohmann/akashictree/issues/25))
Prove the "runs anywhere" promise on real deployments. The three series (seeds / thesaurus /
enterprise) share one codebase; `akasha.py` already carries the launch modes (stdlib httpd,
uvicorn/FastAPI, CGI, stdio). Validate **AWS-friendly** (S3 immutable objects + Lambda
event-driven growth + SQLite edge cache — *not* DynamoDB hot queries), **GCP-friendly**
(Cloud Run / GCS), and **shared/rental hosting** (CGI path, stdlib-only core, graceful
degrade without FastAPI). Ship a smoke runbook per target and verify the crash-stop
("last write only") guarantee holds on containerised / networked filesystems.

### Knowledge-exchange ecosystem ([#26](https://github.com/henrigrohmann/akashictree/issues/26))
Let multiple Akasha / thesaurus instances **safely exchange** curations, ontology, and
semantic links. Because atoms are content-addressed, identical knowledge unifies naturally.
Seams: `sync.push` / `sync.pull`, `GroupEngine`, and the thesaurus concept models. Work:
portable exchange units (`.ak` export + provenance + signature), scoped peer push/pull
(fail-closed), provenance-preserving merge (first-wins + `specializes`), and a discovery
catalogue of who holds which namespace.

### Cloud offload / on-demand retrieval — personal *and* group ([#27](https://github.com/henrigrohmann/akashictree/issues/27))
An iCloud-style "what isn't local is fetched on demand" layer — **at the core (atom/cortex)
level, not thesaurus-specific**. It applies to a personal cortex (single-user seeds) and to
a shared group graph alike. Cold atoms are evicted to an object store keyed by sha256 and
transparently retrieved on read. Seams: `evict_chunk`, `register_fault_handler`,
`rw.fetch_remote_memory`, and the IDLE maintenance-job path ([#12](https://github.com/henrigrohmann/akashictree/issues/12)).
SQLite stays the sole ground truth; the cloud is a volatile eviction tier, never the
source of truth. This is *retrieval*; [#26](https://github.com/henrigrohmann/akashictree/issues/26)
is *exchange* — orthogonal axes.

### IoT: Lego Mindstorms control loop ([#28](https://github.com/henrigrohmann/akashictree/issues/28))
First end-to-end physical validation of sensor/actuator atom binding
([#17](https://github.com/henrigrohmann/akashictree/issues/17)) on accessible hardware.
Override `get_chunk_raw` / `put_chunk_raw` for a `MindstormsBackend`, declare the causal
model in `.ak` with `ref:if` / `ref:therefore`, and demonstrate the core claim: the same
graph and the same upper layers move from **seeded-value simulation to real control by
swapping only the backend** — no change above the instruction-set boundary.

### DTN: async handoff test ([#29](https://github.com/henrigrohmann/akashictree/issues/29))
End-to-end test of delay/disruption-tolerant handoff via `pending_links`
(`enqueue_pending_link` / `_weave_pending_links`): agents and peers collaborate **without
being online simultaneously**. Verify order-independence and idempotency, survival across
disconnect/reconnect under crash-stop (the pending queue is SQLite-durable), scope-gated
weave (fail-closed), and a two-agent pipeline collaborating across an offline gap.

### MCP integration — Phase 2 ([#30](https://github.com/henrigrohmann/akashictree/issues/30))
Wire the `api/portals/mcp.py` stub to live transport via `mcp-python-sdk` so any compatible
LLM client can call Akasha directly. Expose `thesaurus.view.atom` (lookup), `thesaurus.search`
(semantic), and namespace scan (gap detection). The MCP portal receives at `TRUST_NETWORK`
(server-set, not client-supplied); reads stay scope-filtered and fail-closed. Read-only
first, then scoped write — collapsing the human-relay loop below.

**Supporting open issues this quarter feeds into:**
[#12](https://github.com/henrigrohmann/akashictree/issues/12) IDLE maintenance jobs ·
[#14](https://github.com/henrigrohmann/akashictree/issues/14) external-library candidates ·
[#15](https://github.com/henrigrohmann/akashictree/issues/15) local-LLM candidates ·
[#17](https://github.com/henrigrohmann/akashictree/issues/17) sensor/actuator binding ·
[#18](https://github.com/henrigrohmann/akashictree/issues/18) low-code for server/enterprise ·
[#22](https://github.com/henrigrohmann/akashictree/issues/22) safe parallel dispatch ·
[#23](https://github.com/henrigrohmann/akashictree/issues/23) public-key auth ·
[#24](https://github.com/henrigrohmann/akashictree/issues/24) full declarative workflow DAG.

---

## The Arc Behind the Quarter

The six goals are steps along one line: collapse the human relay, let knowledge move
between instances and agents, and let the same graph reach from the cloud down to a
sensor. The sections below are the longer view those steps serve.

### Collapsing the human relay (MCP + self-expanding graph)

Today the loop is: *human explains ontology → LLM writes CSL → human runs it → human
reviews → repeat.* The human is the relay and every session starts blank.

MCP ([#30](https://github.com/henrigrohmann/akashictree/issues/30)) collapses that. Once an
LLM can scan the existing ontology directly, it identifies gaps, generates CSL that fills
precise structural holes, and checks its own proposals against what already exists. The
human stops explaining the graph before each session and instead sets goals and evaluates
outcomes. The feedback loop becomes self-reinforcing:

```
Richer graph → better LLM contributions → richer graph → ...
```

### Multi-LLM collaboration without a shared protocol

Group sessions already let multiple clients — human or LLM — share one graph space, with
scope-controlled access, attributed writes, and preserved temporal order. Two LLMs from
different providers can collaborate because their **common language is Akasha's concept
model, not the transport protocol**. `pending_links` ([#29](https://github.com/henrigrohmann/akashictree/issues/29))
adds disruption tolerance: one agent explores, another generates CSL, a third validates —
none needing to be online at the same moment.

> A low-cost, local-first, semantically grounded multi-agent environment that doesn't
> require proprietary orchestration infrastructure or cloud accounts.

### Akasha as the hippocampus for AI

LLMs are extraordinary pattern-recognition engines with no episodic memory. Every
conversation starts blank; long-term experience disappears at context reset. Anchored to an
Akasha session, an LLM gains persistence (experiences written as atoms and typed links),
recall by graph traversal, preserved temporal structure, and scope-isolated memory that can
be selectively shared through group sessions. The result is a complete cognitive loop:

```
Neocortex (LLM)         — pattern recognition, language generation
Hippocampus (Akasha)    — episodic fixation and recall
Sensorimotor (hardware) — interaction with the physical world
```

### One substrate across every scale

`AkashaBackend` defines ~50 primitive operations — a minimal instruction set for semantic
memory — with no reference to files, tables, or SQL. It describes *what the substrate must
do*, not *how*. Different scales swap the implementation; the upper layers (composite,
session, IAM, concept models) run unchanged:

| Scale | Backend | Status |
|---|---|---|
| Local / edge | SQLite | ✅ Working |
| Cloud / distributed | Object store + event-driven growth (S3 + Lambda affinity) | 🔲 Offload seams exist ([#27](https://github.com/henrigrohmann/akashictree/issues/27)); full backend designed |
| Embedded / IoT | Hardware register mapping | 🔲 Seams ready; first PoC this quarter ([#28](https://github.com/henrigrohmann/akashictree/issues/28)) |
| Silicon | Custom chip implementing the ISA | 🔮 Long-term possibility |

**IoT.** Override `get_chunk_raw` for a live sensor read and `put_chunk_raw` for an actuator
command; scopes become device-authorization capabilities. The semantic graph becomes the
control plane *and* the memory of what the system reported and when. A Raspberry Pi with a
sensor array becomes a semantic edge node — the Lego Mindstorms experiment
([#28](https://github.com/henrigrohmann/akashictree/issues/28)) is the first step onto that
path.

**Silicon.** The fabless era means you no longer need a fab to design a chip, and RISC-V
showed a clean open ISA is a legitimate basis for real hardware. `AkashaBackend` *is* an
instruction set architecture for semantic-memory operations. Implemented in dedicated
silicon pipelines — on-chip graph traversal, scope filtering, alias resolution — its
performance profile would be entirely different, a natural fit for robotics control planes,
embedded sensor networks, and low-latency edge inference. Not next year; not structurally
impossible either. The architecture was built to support it.

---

## How to Contribute

The GitHub issues above are the live worklist. Good places to push:

**Near-term (MCP + multi-agent):**
- Wire the MCP server for the thesaurus layer ([#30](https://github.com/henrigrohmann/akashictree/issues/30))
- Test multi-LLM group-session and DTN handoff workflows ([#29](https://github.com/henrigrohmann/akashictree/issues/29))
- Write a connector guide for LLM-to-Akasha sessions

**Medium-term (edge + cloud + IoT):**
- Implement a cloud offload / retrieval tier ([#27](https://github.com/henrigrohmann/akashictree/issues/27)) and deploy targets ([#25](https://github.com/henrigrohmann/akashictree/issues/25))
- Build the sensor-node IoT binding, simulation-first ([#28](https://github.com/henrigrohmann/akashictree/issues/28), [#17](https://github.com/henrigrohmann/akashictree/issues/17))
- Extend the declarative workflow DAG ([#24](https://github.com/henrigrohmann/akashictree/issues/24))

**Long-term (silicon):**
- Prototype the 50-primitive Akasha ISA on an FPGA
- Benchmark hardware-accelerated graph traversal vs. the SQLite baseline

**Concept-model work (always open):**
- Extend the thesaurus ontology with new namespaces and domains
- Write semantic extensions for your field of expertise
- Connect Akasha to external knowledge sources via import pipelines

---

The architecture is ready.
The instruction set is defined.
The concept-model ecosystem is live.

What remains is the work of connecting it to the world.

*One contribution at a time.*

---

**→ Start with the codebase:** [`CLAUDE.md`](CLAUDE.md) — session context for LLM collaborators
**→ Start with the concepts:** [`docs/for-llm/architecture-vision.md`](docs/for-llm/architecture-vision.md) — the full technical picture
**→ Start building:** [`quick-start.md`](quick-start.md) — running Akasha in 20 minutes
