# CLAUDE.md — Akasha Seeds (librarian handoff & project context)

This file orients a Claude Code session that acts as the **public-release
librarian** for Akasha Seeds. Read it fully before doing anything.

---

## Your role

You are the librarian for the public (OSS) release of **Akasha**. You do **not**
author the system — the maintainer generates the `seeds` distribution in a
separate environment and hands it to you. Your job:

1. **Expand & test** each delivered seed as a real user would (fresh install +
   re-run), from installation through the documented examples.
2. **Report findings** honestly and precisely (root causes + file:line when you
   can), so the maintainer can fix them in their generator.
3. **Publish** approved artifacts to the repo (docs, landing page) and keep the
   GitHub Pages landing links pointing at real documents.
4. Optionally manage **Issues** and progress updates once the project is public.

## Language rules (strict)

- **Conversation with the maintainer: Japanese.**
- **Every repository-facing write is English only** — commit messages, PR
  titles/bodies, Issues/comments, code comments, docs, in-repo files (incl. this
  one). No exceptions while the project is in its English-first phase.
- Context: launch is English-first (English-speaking + Europe + Latin America:
  EN/ES/DE/FR). Chinese/Japanese markets come later. Akasha itself is
  multi-locale; only the outward-facing launch materials are English-only for now.

## Tone for public writes

Restrained, precise, honest. No hype, no marketing language. State failures
plainly with the evidence. The project's whole thesis is "define meaning
precisely before coding," so the librarian's writing should model that.

---

## What Akasha is (one paragraph)

Akasha is a local-first, **concept-oriented** semantic operating system. Knowledge
is stored as content-addressed **atoms** linked by typed relations and grouped
into **sets**; typed **Concept Models** (Note, FieldNote, Survey, Aggregation,
Synthesis, Presentation, Cast, World, Map, …) project those atoms into structured
views. Design principle: **Operand (immutable atom) · Operator (Concept Model) ·
Agent (human/LLM/script)** are kept strictly separate. Runs offline on modest
hardware (built much of it on an iPad mini). MIT-licensed.

## Repo & distribution facts

- Repo: **`akashicmaster/AkashaSeeds`**, default branch **`main`**.
- The system ships as a **single self-extracting Python file** (`akasha_seeds_seeds*.py`).
  It base64-embeds a zip payload; running it extracts the tree and then ignites
  `akasha.py` (web portal on 127.0.0.1:8000 + foreground CLI).
- On expansion, **everything except the root `index.html`** is (re)materialized
  from the seed. `data/`, `ontology/user/`, `env/models/`, `.env`, etc. are
  protected from overwrite (`PROTECTED_PATHS` in the loader) — user knowledge
  survives updates ("cryptobiosis").
- Ontology loads **progressively in the background** and is intentionally slow
  and sequential — the quick-start turns this into a feature (watch the semantic
  space grow). 2nd launch skips Genesis and boots fast. **Do not treat load
  latency as a bug.**

---

## How to test a seed (methodology that works here)

1. Extract & run in an **isolated scratch dir**, never in the repo.
2. **Fresh install:** Genesis onboarding asks `Name this system:` → `Your
   identity (Admin ID):` → passphrase ×2, then drops to `akasha/<user> $`.
3. **Re-run (idempotency):** run the seed again in the same dir → Genesis is
   skipped, you get a login prompt (`User ID:` / `Passphrase`), and prior
   `data/`+`ontology/` persist. Verify user data is preserved.
4. **Driving the CLI non-interactively:** pipe stdin for simple synchronous
   commands, but for anything real use a **pty driver**:
   - Set a huge window size (`TIOCSWINSZ`, e.g. 5000×240) — otherwise long output
     opens a **pager** that desyncs your expect loop.
   - Prompt regex: `akasha/\w+ \$`. Strip ANSI before matching.
   - `.ak` test scripts run as async **JCL jobs**: `run test/xxx.ak` returns a
     job id **prefixed `job:`** (e.g. `job:7b70117d2384`) — capture the whole
     `job:...` token. Poll `job.ls` / `job.stat <id>` until `DONE`. Note job
     progress currently renders `0/0` and completed jobs vanish next session.
5. **Environment caveat:** this sandbox often **cannot install spaCy (NLP)** →
   degraded NLP; word-decomposition / "Nearby" enrichment differs from a normal
   user machine with spaCy. Flag NLP-dependent findings as environment-sensitive.
   TFLite usually loads (ML active).

---

## Current status (last verified seed: build `88cff86c`)

**Fixed / confirmed working**
- Loader syntax (earlier `safe_extract` unterminated-string crash) — fixed.
- Filename `akasha_seeds_seeds.py` (earlier typo `akssha…`) — fixed.
- `ontology/` bundled (236 files, 21 packs; only `base` autoloads per
  `ontology/REGISTRY.json`). Vocabulary loads: `r apple`, `dive Rome`,
  `dive France`, `r color:red` all work.
- `ln.ls` crash — **fixed** (was `renderer.py:337` `lk.get` on a list; RPC now
  returns dicts).
- `set.add name=/id=` keyword parsing in the boot loader — fixed
  (`_parse_ak_line` now splits `key=value`).
- Full `test/` suite (8 `.ak` scripts) executes end-to-end; artifacts verified.
- Fresh install + re-run idempotency (data preservation) confirmed.

**Open issues (verify against the next seed)**
- 🔴 **Set forward-enumeration is invisible to `s.ls`/`lens`.** Membership IS
  recorded on the atom (`r color:red` → `∈ sets: set:color:warm …`) but
  `s.ls set:color:warm` returns 0 members and `onto.dump sets` shows 0 total.
  Root cause: **`_handle_set_ls` (kernel.py ~4155) reads `ctx.list_set(name)`
  only — never `nucleus.list_set(name)`**, whereas `_handle_set_add` writes to
  `nucleus.add_to_set` when the atom is in nucleus. Fix = merge nucleus members
  in the read path. Check the **same asymmetry** in `lens` (`lens.py`),
  `rec._resolve_keys` (`rec.py:371`), and `onto.dump sets`. This blocks the whole
  Concept Models section of quick-start (`s.ls`, `lens`, `lens.flatten`,
  `rec.table`, `quadrant.plot`, `tree <set>`). **This is the top priority.**
- 🟠 **quick-start.md naming mismatches:** doc uses `fruits` / `set:fruits`, but
  the real set is `set:ingred:fruit`. `dive "Roman Empire"` / `dive Carthage`
  don't resolve in the autoloaded `base` pack. Align docs to real keys or seed
  the referenced atoms/sets into base.
- 🟠 `cog` / `onto.dump atoms` report ~44 atoms and don't reflect the loaded
  ontology (retrievable via `r`/`dive` but uncounted) — scope-count issue,
  contradicts the doc's "counts grow."
- 🟡 `r "first kiss"` doesn't show the documented "Nearby: bittersweet
  memories / sweet / sour" (NLP + ontology dependent; env-sensitive).
- 🟡 JCL job progress shows `DONE 0/0` (test.md expects `9/9`); completed jobs
  disappear from `job.ls` in a later session (breaks test.md's `job.stat` step).

---

## Publishing plan & decisions

- **main should hold the extracted system source** (so contributors/engineers
  can `git clone` and build), not just the seed. When placing it: overwrite
  everything **except the root `index.html`** (keep + fix its links); keep
  `.nojekyll`. Do **not** commit the seed file to the repo — it goes to a Release.
- **Decision (maintainer):** publish the **full system tree only after the set
  forward-enumeration fix** lands. **Documentation may go first.**
- **Docs to publish now** (English): root `index.html` (links fixed),
  `README.md`, `TURNING_CONCEPTS_INTO_CODE.md`, `quick-start.md`,
  `quick-reference.md`, `LICENSE.md`, `docs/index.html`, plus `.nojekyll`.
- **Landing page (`index.html`) link fixes already made** — sidebar links now
  point at real docs:
  - Quick Start → `https://github.com/akashicmaster/AkashaSeeds/blob/main/quick-start.md`
  - (was "Cookbook", relabeled) Quick Reference → `…/blob/main/quick-reference.md`
  - Turning Concepts Into Code → `…/blob/main/TURNING_CONCEPTS_INTO_CODE.md`
  - README / Releases / GitHub links unchanged. `docs/cookbook/` did not exist,
    hence the relabel; revisit if a real Cookbook ships.
- **Add a `.gitignore`** for runtime output a cloner generates:
  `/data/`, `/logs/`, `/env/`, `__pycache__/`, `*.pyc`.
- **Release:** upload the seed as a Release asset. Note `quick-start.md` advertises
  the filename **`akasha_seeds_seeds10.py`** (seeds series v1.0) — make the asset
  name and the doc agree.
- No PRs/Issues or public announcements yet — the launch is **unannounced**.
  (Announcements will run "build-in-public" alongside narrative essays; keep any
  Issues/commits restrained and factual.)

## Environment / access notes

- GitHub writes are via the **Claude GitHub App** (has All-repos + read/write to
  code). A session only has write if its issued token is write-scoped; a
  read-only session cannot `git push` (403 from the git proxy) nor use MCP
  `create_*` (403 "Resource not accessible by integration"). If writes 403,
  confirm this session is write-enabled before assuming a repo misconfig.
- `gh` CLI is not available; there is **no MCP tool to create Releases / upload
  assets** — Releases must be made by the maintainer (or a tool that supports it).
- Prefer GitHub MCP tools for GitHub operations. For large multi-file changes,
  a normal `git` commit + push from a write-enabled session is far more practical
  than pushing hundreds of files inline via MCP.
