# Akasha Public Roadmap

Akasha is a **local-first semantic knowledge-graph substrate** — a *cognitive substrate*
that humans, LLMs, sensors, and future hardware all use through a single, unified
interface.

This roadmap is a public plan. Each item is tied to a GitHub issue and presented in
priority order across three horizons — **Now / Next / Later** — anchored to release
series (seeds / thesaurus / enterprise) rather than dates.

> Legend: 🎯 headline feature · 🔌 integration · 🧠 intelligence layer · 🌐 distribution & scale · 🏭 physical world

---

## Now — next release (seeds12 / thesaurus08)

- 🎯🧠 **[#52](https://github.com/henrigrohmann/akashictree/issues/52) nebula — discovering the cores of concept models**
  A third explorer that surveys the accumulated concept atoms and systematically hunts
  for "cores that could grow into concept models" — dense star-systems of meaning. Where
  `assoc` fills local gaps and `dream` makes serendipitous associations, nebula performs
  global, structural **inductive schema formation**: vector neighbourhoods plus semantic
  scoring let categories like *fruit* or *recipe* emerge *after the fact*.
- 🔌 **[#30](https://github.com/henrigrohmann/akashictree/issues/30) MCP server wiring** — LLM clients use Akasha directly (read first, then scoped write).
- 🧩 **[#50](https://github.com/henrigrohmann/akashictree/issues/50) Drop-in concept models** — a concept model you install is usable from the CLI immediately.
- ✅ **[#53](https://github.com/henrigrohmann/akashictree/issues/53) sim / search semantic-ranking verification** (high tier) — re-confirm the lexicon-definition-layer exclusion on production embeddings.

## Next — a few releases out

- 🌐 **[#26](https://github.com/henrigrohmann/akashictree/issues/26) Thesaurus knowledge-exchange ecosystem** — knowledge sharing between Akasha instances.
- 🔀 **[#24](https://github.com/henrigrohmann/akashictree/issues/24) / [#46](https://github.com/henrigrohmann/akashictree/issues/46) Workflows & complex I/O chains as jobs** — declarative multi-stage pipes: Contexa → concept model → Jataka.
- 🪐 **[#48](https://github.com/henrigrohmann/akashictree/issues/48) / [#49](https://github.com/henrigrohmann/akashictree/issues/49) Making cosmos real** — feed the meaning layer's results (real coordinates, embeddings) into the 3D GUI, and add flight instruments.
- 🧠 **[#45](https://github.com/henrigrohmann/akashictree/issues/45) / [#34](https://github.com/henrigrohmann/akashictree/issues/34) / [#31](https://github.com/henrigrohmann/akashictree/issues/31) LLM collaboration (avatar-mediated)** — natural-language I/O loop, delegate agents, lower always-on connection cost.
- ☁️ **[#27](https://github.com/henrigrohmann/akashictree/issues/27) Cloud offload for the knowledge graph** — on-demand retrieval (iCloud-style), for personal and group graphs alike.
- 🖼️ **[#40](https://github.com/henrigrohmann/akashictree/issues/40) / [#42](https://github.com/henrigrohmann/akashictree/issues/42) Meaning-layer extensions** — expanded image profiling; a second track for emotion analysis.

## Later — mid- to long-term vision

- 🌐 **[#29](https://github.com/henrigrohmann/akashictree/issues/29) DTN (disruption-tolerant asynchronous handoff)** — agents collaborate without being online simultaneously.
- 🏭 **[#33](https://github.com/henrigrohmann/akashictree/issues/33) / [#17](https://github.com/henrigrohmann/akashictree/issues/17) / [#28](https://github.com/henrigrohmann/akashictree/issues/28) Sensor / actuator mapping** — from virtual simulation to automated factory and warehouse operation.
- 🏢 **[#47](https://github.com/henrigrohmann/akashictree/issues/47) Multi-provider (enterprise)** — one server, multiple tenants.
- 🔐 **[#23](https://github.com/henrigrohmann/akashictree/issues/23) Public-key client authentication** — asymmetric auth beyond passphrases.
- 🔬 **Hardware path (FPGA)** — the AkashaBackend instruction set implemented on-chip (Raspberry Pi HAT → ASIC).

---

## The spine of the design (why this order)

At its core Akasha holds a **dual epistemology: induction (accumulation) and deduction
(definition), supported simultaneously**.

- The bridge between concept atoms (induction) and concept models (deduction) is
  **already complete** — concept models operate on real concept atoms.
- Relations and namespaces are **first-class citizens** with definitions, made readable
  (done).
- Next, **nebula** closes the generative direction from induction to deduction —
  completing the self-expanding-ontology loop.

The three release series (seeds / thesaurus / enterprise) share **one codebase**; they
differ only in bundled content and configuration. The license is MIT.

*This roadmap is updated as work progresses. See the individual issues for details and
discussion.*
