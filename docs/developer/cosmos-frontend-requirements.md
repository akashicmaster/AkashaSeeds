# Cosmos — front-end requirements (after the meaning-layer build-out)

**Audience:** the front-end context that owns `services/static/cosmos/index.html`.
**Scope of this doc:** what the backend now provides, what the GUI must change to stop being
"decorative-only", and which existing backend methods to wire as new cockpit instruments.
Backend positioning work is **already shipped** (see *Backend anchors*); no backend change is
required to consume it — only to add the deeper instruments (all of which call methods that
already exist).

Cosmos is the **projection of the `cockpit` concept model** (`lib/akasha/concepts/cockpit.py`):
focus (`cockpit.lock`), axis/scope lens (`cockpit.tune`), beacons + wake (`cockpit.beacon` /
`cockpit.wake`). New GUI controls should map to cockpit / kernel methods, not invent state.

---

## 1. What the backend now provides (real — use it)

`dive.look` (via `/api/cosmos/sync`) returns `cosmos.nodes[]` where **each node now carries**:

| Field | Meaning | Was |
|---|---|---|
| `x`, `y`, `z` | **Real semantic position** — near in space ⇒ near in meaning. When a learned model exists it projects onto that model's **principal (SVD) axes** (a fitted, topic-clustered layout, server-side); otherwise a distance-preserving random-projection seed of the self-owned embedding. Deterministic & stable. | *absent* (layout was pure ForceGraph physics — spatially meaningless) |
| `val` | **Degree-based size** — bigger = more connected (hub vs leaf). | constant 10/12/20 |
| `color` | Emotion/sense **aura** from the atom's `emo:`/`sense:` links (already real). | (unchanged) |
| `group`, `alias`, `name` | type / label (unchanged). | |

Also real and already usable: **axis filter** (`structure` / `emotion` / `context` genuinely
filter relations), **resonance** (cosine-weighted 2-hop), **jobs** (`job.ls`).

## 2. Required GUI changes (make the viewport honest)

1. **Seed positions from `x`/`y`/`z`.** Feed them to ForceGraph3D as initial coordinates
   (or pin with `fx/fy/fz` for a fixed semantic layout, or use as a seed then let a light
   physics pass relax link overlaps). Today the GUI ignores them and lets physics scatter
   nodes — that is the single biggest "cosmetic-only" element: the "cosmos" carried no spatial meaning.
2. **Size nodes by `val`** instead of the constant fallback.
3. Colors already come from `n.color` — keep.

These three are additive: nodes without the fields (older payloads) still render.

## 3. New operational elements (surface the enriched meaning layer)

The meaning layer is built but **cosmos exposes almost none of it** (only `assoc`/`dream`/
`fetch`). Wire these **existing** backend methods as cockpit instruments:

| Instrument | Backend method (exists) | Renders as |
|---|---|---|
| **Semantic neighbours** ("atoms like THIS") | `sim` / `semantic.search {id}` | overlay nodes + dashed links from focus |
| **Structural neighbours** ("connected the same way") | `node.sim {id}` | overlay nodes (distinct link style) |
| **Dream bridges** (the affinity gap) | `dream {id}` *(async: submit → `status:"dreaming"` + `job_id`, poll → `status:"ready"` + candidates)* | **ghost links** (staged `tent:`); click ✓ → `dream.confirm {src,dst}`, ✗ → `dream.forget {src,dst}` |
| **Missing links** (1-hop, high-confidence) | `assoc {id}` / `gap.scan` | candidate links with an "add" affordance |
| **Emotion find / profile** | `emotion.find {emo}` / `emotion.profile {id}` | highlight matching nodes; show focal emotion vector in Telemetry |
| **Report / export** | `jataka.present (survey=\|set=\|focus=) as=table\|scatter\|narrative` | a "Report" panel — table, scatter (uses the SAME real position), or narrative prose |
| **Intake** | `contexa.ingest` / `contexa.fetch` | an "Intake" panel (upload responses / fetch web → graph) |

**Dream is the flagship instrument.** It is now an async "sleep-on-it" job: the pilot warps to
an atom, hits *Dream*, gets a "dreaming…" indicator (poll the `job_id`), and on return sees
**ghost bridges** — near-in-meaning / far-in-graph candidates — to **confirm or dismiss by
hand**. Human approval is mandatory by design (no auto-linking). This is the cockpit's most
distinctive control and maps directly onto the viewport.

## 4. Still fake / backend follow-up (do NOT present as real yet)

- **`time` axis does not filter** — the chrono layer isn't wired into `associate`; today it is
  passed as metadata only. **`story` axis** needs `polti:`/`story:` ontology to have any data.
  Until wired, either hide these options or badge them "experimental".
- **Crisp topic *clustering* layout — handled server-side; the GUI needs no algorithm.**
  When a learned distributional model exists (the boot auto-learn builds one), `x/y/z` is now
  projected onto the model's **principal (SVD-ordered) axes** — a fitted, topic-clustered
  layout computed entirely on the server. The GUI still just reads `x/y/z`. Without a learned
  model (e.g. a tiny fresh Cell) it degrades to the distance-preserving random-projection seed.
  So a client-side UMAP/t-SNE is **not** required; do not add layout algorithms to the GUI.

## 5. Backend anchors (for reference / follow-up)

- `lib/akasha/consciousness.py` — `CosmosMapper.position` (learned-principal fitted layout →
  `_principal_3d`, else floor `_project_3d`), `calculate_nd` (now real: `[x,y,z,T,layer,color]`).
- `lib/akasha/kernel.py` — `_format_associate_cosmos` (attaches `x/y/z` + degree `val`),
  `_handle_dive_look`.
- `lib/akasha/concepts/cockpit.py` — the projected model.
- Meaning-layer methods already available: `semantic.search`/`sim`, `node.sim`/`node.learn`,
  `dream`/`dream.confirm`/`dream.forget`, `emotion.find`/`emotion.profile`, `gap.scan`,
  `jataka.present`, `contexa.ingest`/`contexa.fetch`.
- `test/cosmos_eval.py` — proves position clusters by topic, graph carries geometry, scatter spreads.
