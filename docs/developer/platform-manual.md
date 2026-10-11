# Platform manual — the heart, the Application API and the manifests

Audience: anyone adding an op, a schedule, a Concept Model, a provisioner, a package or a deploy
path. This is the reference for the mechanism established by
`directive-backend-layout-2026-09-20.md` and the ownership ruling; it is kept current in the same
seed that changes the thing it describes.

**The contract with an application is `docs/platform/SPEC.md` (platform-spec v1.3.2; a release is pinned by its commit and its `PLATFORM_TREE.json` tree hash).** This manual
is the platform's own working detail; where the two differ, the specification is the contract.

---

## 1. The two parts

```text
PLATFORM     everything outside app/ — lib/akasha/ (the heart and its packages ontology/,
             source/, concepts/, workbench/), api/, services/, the platform's ontology/,
             config/, scripts/, test/, reproductor/, akasha.py
APPLICATION  app/ — concepts/, config/, ontology/, archives/, scripts/, seeds/, curations/,
             assets/, test/   (platform-spec §1–§2)
```

Inside the platform a package may import one to its LEFT (heart ← ontology ← source ← concepts ←
workbench); the application is rightmost and imports the API only. `test/wiring_eval.py` holds it.

The heart names no Concept Model, Source, bench, room or programme. Everything it runs comes from
a `MANIFEST.json`, never an import. A manifest entry that does not resolve is a **boot error
naming the entry** — never a `-32601` at request time.

**Who owns what: where a file lives.** `api.manifest.owner_of(_, path)` is one rule — under the
application root (`api.reserved.app_root()`, `app/` unless `AKASHA_APP_DIR` says otherwise) it is the
application's, anywhere else the platform's. There is no owner list. Every manifest still declares
`owner`, and a manifest whose owner disagrees with its location is a boot error. Held by
`test/ownership_eval.py`.

| manifest | owner |
|---|---|
| `lib/akasha/MANIFEST.json` (heart), `lib/akasha/{ontology,source,concepts,workbench}/MANIFEST.json` | platform |
| `app/config/MANIFEST.json`, `app/archives/MANIFEST.json` | the application |

The platform discovers the application from its root only (SPEC §2): Concept Models from
`concepts/` (`registry.build_active` imports every module there as `<package>.concepts.<stem>`), the
manifest from `config/MANIFEST.json`, packs from `ontology/` (after the platform's own `ontology/`;
`loader.ontology_roots()`), pages from `archives/`, declarations from their roots
(`api.reserved.DECLARATION_ROOTS`).

---

## 2. Application API reference — `lib/akasha/api/`

Pure Python, dependency-free: it imports no heart module, so the heart behind it may be compiled.
This is the ONLY door; an application package reaches the heart through it and nothing else.

### The application's names — `lib.akasha.api.<topic>` (the purge order, P1)

**An application imports only `lib.akasha.api`.** Every name it may use is in ONE table,
`lib/akasha/api/exports.py` (`name → ("module:attr", contract)`), grouped by topic:
`concepts`, `source`, `fields`, `declarations`, `jobs`, `process`, `vision`, `llm`, `workloads`,
`graph`, `learned`, `files`, `client`. Each topic module resolves its names LAZILY (PEP 562):
importing it imports nothing behind it, so no cycle can form. The published list,
`lib/akasha/api/APPLICATION_API.md`, is GENERATED from the table (`python
scripts/gen_application_api.py`; `--check` in `test/application_api_eval.py`) — never edit it.

- **A Concept Model is never imported.** `concepts.model(session, prefix)` returns an instance of
  the model that declares `prefix` (`model_class(prefix)` for its class). The bases a model
  subclasses (`BaseConcept`, `UniversalConcept`, `WorkbenchConcept`) are API names.
- **A private name (`_…`) is never exported.** Where a need is legitimate the API gives a public
  face (`process.rss_mb`, `vision.MODEL_FILE`, `vision.resolve_backend`, `jobs.is_blocked`);
  otherwise the application redesigns. `client.embedded(base_dir, series, load_ontology=False)`
  replaces a script's `KernelDispatcher` class patch (per cell; nothing global is patched).
- **No API by design:** `lib.akasha.canon` (deleted — the law is the application's) and
  `concepts._radu_gate` (it names one application).
- **Adding a name** is one entry in `exports.py` + regenerating the `.md`. A name that keeps its
  meaning is the contract; changing one is an API change, noted as one.

**Reserved concept names** (`api/reserved.py` `RESERVED_CONCEPTS`, `concepts.RESERVED_CONCEPTS`):
the concept names a platform engine mints, each mapped to its engine. They are the ONLY concept
names platform code may test; an application never mints one.

**Declaration roots** (`api/reserved.py` `DECLARATION_ROOTS`, `declarations.root(kind)`):
`workloads`, `templates` (per bench), `profiles`, `source`, `packs`, `pages`. The platform reads
declarations from these roots and from no file named by an application; the workload, template and
source readers read them.

**Engine-owned fields** (`lib/akasha/owned_fields.py`, `fields.owned()`). A reserved engine declares
the meta fields it alone writes — `declare(owner, field, concept=…)` or `declare(owner, field,
member_of=(prefix, suffix))` (membership, not a concept name). The source engine declares `status`
on any member of a `source:pool:…:members` Set and `by_status` on `source_pool`. Both backends check
every meta write (`put_chunk_raw`, `update_meta`, `merge_meta`, Silica's `write_atom`): a write that
CHANGES an owned field, by anyone but the owner (whose writes run inside `writing_as(owner)`), raises
`OwnedFieldRefused` naming the field, the atom and the owner. A write that leaves the field as it was
passes. `update_meta` and `merge_meta` check INSIDE the atomic write (the SQLite writer thread, the
Silica bank lock) against the record they replace — so a stale whole-meta copy that would revert an
owned field is refused, not landed; the caller's owner and the atom's memberships are read first
(`owned_fields.context`). Held by `test/owned_fields_eval.py`; the door by membership by
`test/status_door_eval.py`.

**`merge_meta(key, updates)` — the one way to change some fields of an atom's meta** (ISA, both
backends; purge order P2). The read, the merge and the write are ONE step against every other writer
of the record: SQLite runs it on its single writer thread, Silica under the record's bank lock
(`SilicaStore.update`, the TRMW instruction — a `Txn` cannot do this, its reads precede its commit's
lock). `updates` is a dict, or a callable given the current meta and returning the dict to merge (a
counter, a tally bucket). Returns the meta as written, `None` for no such atom; a merge that changes
nothing writes nothing. A read → edit → `update_meta` of the whole meta by the caller is NOT atomic:
it overwrites a concurrent writer's change to another field with its stale copy — the weave's
salience bump did exactly that to `source.item.status` one run in three on a single-store cell,
which the deleted pool-tally adoption had been recounting. The composite `set_meta` / `add_meta` /
`verify_chunk` / salience bump, the source engine's `_set_meta` (its status door, tallies and clock)
and `_universal.set_meta` all write through it. Held by `test/meta_merge_eval.py` (N threads × M
increments exact, two writers of different fields both survive, a stale copy cannot revert an owned
field — each failing with the old read-edit-write).

### `api.trust` — transport trust

A property of the **server-side transport binding**, set by the portal that received the request.
A client can never supply it.

| value | meaning |
|---|---|
| `TRUST_NETWORK` | default; untrusted remote (ASGI, web worker, CGI). A bare `client_id` is only ever an anonymous GUEST; a privileged identity must present a signed `akt:` token |
| `TRUST_LOCAL` | the operator's stdio console — the OS process boundary is the gate, so a bare `client_id` (including admin) is accepted |
| `TRUST_INTERNAL` | kernel-originated in-process dispatch (JCL worker, boot loader, self-dispatch); bare id and `system.*` identities accepted |

`TRUSTED_TRANSPORTS = {TRUST_LOCAL, TRUST_INTERNAL}`.

### `api.rpc` — the envelope

```python
ok(rid, data)                 -> {"jsonrpc": "2.0", "result": …, "id": rid}
err(rid, code, message, data) -> {"jsonrpc": "2.0", "error": {…}, "id": rid or <uuid>}
```

Key order is part of the wire shape (a client may hash or diff the raw response) and is fixed
here. The heart never raises to the caller.

### `api.ops` — the RPC dispatch table

An op is `fn(kernel, <named parameters>)`. It declares what it needs **by parameter name**, drawn
from the request vocabulary; the table binds those names from the `Req` at call time, resolved
once per op at registration. An unknown parameter name is a boot error naming the op. This is what
lets a handler move out of the kernel class with no adapter: the same signature, minus `self`,
plus one manifest line.

Request fields: `rid`, `method`, `data`, `session`, `ctx`, `scopes`, `client_id`, `history`,
`su_key`, `transport_trust`, `raw_token`, `role`. (`real_client_id` is an accepted alias for
`client_id`, which the `su` handler uses.) `*args` / `**kwargs` are not bindable.

`stage` says WHERE in the request path the op runs — declared data, never an `if` on a name:

| stage | when |
|---|---|
| `pre_identity` | before the identity is resolved (ping, status, `auth.*`, guest sessions) |
| `post_identity` | with the resolved identity, before the capability check (`whoami`) |
| `pre_su` | under the real identity, before `su` elevation is applied |
| `pre` | after su/ctx resolution, before the Concept Model registry is consulted |
| `post` | after the registry (the registry wins a name it handles) |

`OpsTable.register(name, fn, stage, access, source)`; a name registered twice is an error naming
both sources.

### `api.schedule` — the timer registry

A schedule body is `fn(kernel)`; it starts its own daemon thread or does its one-shot boot work.
The heart runs a PHASE's bodies in ascending `order`:

| phase | when |
|---|---|
| `load` | the boot load itself, in the `ont-boot-loader` thread at boot and again after genesis |
| `writer` | once per writer process, right after "Kernel online" (independent of the load) |
| `post_load` | once per process, from the load path after the admin exists |

`register(name, fn, phase, order, source, when, package)`; `meta(name)` returns `{when, package}`;
`phase(name)` lists the bodies in order; `run_phase(kernel, phase)` runs and REPORTS them (§5).
`register_unit(name, wanted, thread_attr, start, order)` declares a **thread unit**: a host-bound
thread the guard re-creates when it dies — a wanted-predicate, the kernel attribute holding the
Thread, and an idempotent starter, again as data so the guard names nothing itself.

`run_phase` never raises: a body that fails is reported `status=error` and the rest of the phase
still runs. A boot has always survived one bad schedule; hiding that was the bug.

**Named gates.** A body may declare `provides: "<gate>"` (it opens that gate when it finishes,
however it finishes) and another `after: "<gate>"` (it must not run before). Both are manifest
entries, so the pairing is data and the registry knows a gate has a producer BEFORE any phase runs
— which is what removes the race: the writer phase runs before the load thread is even started, so
a consumer with no declared producer would always win. A deferred body is reported
`status=deferred reason=<gate>` and re-run, in order, by `open_gate`. **A gate nobody declares is
open**, so a cell that never loads an ontology (an eval, a pack-less seed) is unaffected.

```python
gate_open(kernel, name)      # shut only while a DECLARED producer has yet to open it
open_gate(kernel, name)      # the producer, done: releases every deferred body, in order
mark_running(kernel, name)   # the producer, working right now
is_running(kernel, name)     # what a long-lived DAEMON asks instead of `gate_open`
```

`is_running` exists because a daemon is not part of the boot sequence: its first tick is minutes
later, by which point the producer has either finished or was never going to run. "Is a load
happening right now?" is False before one starts, False after it ends, and False forever on a cell
that has none — which is the honest answer for all three. The driver uses it to defer a pick
(`[bench.auto] pick deferred reason=onto_load`); a boot body uses `after:`.

**The defer is SCOPED (09-28).** A load in flight publishes what it touches —
`ontology.loader.in_flight(kernel)` → `{first, packs, declares}` (the cell has never finished a
pack; the packs found CHANGED so far; the per-pack answers kept for the load). On a cell's FIRST
load every workload waits (`scope=all first_load=1`) — but only until the CORE is in (v1.3, VPS
10-11): the loader loads the autoload tier first (autoload:true; on a tier without `load_all` every
pack it loads; `ontology/user/` packs last), and `_core_ready` then applies the core files'
relations — except a file with a step naming a `def`/`al` name a pack still to load declares, left
WHOLE to the global phase — and republishes `{first: False, packs: <packs still to load> +
relations:core}`, where `declares["relations:core"]` is the set of alias and Set names the held
files bind. One `[onto] core ready …` line. From then on, and on every later load, `wl_state.onto_hold` holds a
workload only when a changing pack DECLARES (`def` / `al` / `set.add name=`, via
`loader.pack_declares`, scanned once per pack per load) one of the names the workload declares it
reads — `W.ontology_names`: its `pins` values and its `requires` Sets. The rest keep their cadence.
**Declaring those names is the contract**: a template that reads an ontology name its declaration
does not name is not held for a load that rewrites it. Held by `test/onto_load_scope_eval.py`.

### `api.provision` — boot provisioning

`fn(kernel)`, run as admin in ascending `order` (a package's `depends_on` fixes the order across
packages, `order` within one). Provisioning writes what the declarations say and is idempotent; it
is the ONE place application code obtains an admin session, and it lives in
`lib/akasha/workbench/provision.py`. `test/authority_eval.py` holds that.

### `api.authority` — the one door to an elevated session (the purge order §4.1)

Outside provisioning no platform module calls `get_session("admin"|"system.*")` or enters
`system_context()`. A module that must act as the operator calls
`authority.elevated(kernel, purpose)`; `authority.PURPOSES` is the whole list of reasons, one row
each with the identity it acts as — today `ontology.load` (the boot loader writes the packs),
`driver` (the workbench driver reads and records its societies' state) and `retention.expiry`
(validity expiry). An undeclared purpose raises `UndeclaredPurpose`. One `[authority] elevated
purpose=<p> identity=<id>` line per purpose per process. A new reason is a reviewed row.

### `api.manifest` — the aggregator

`load_manifests(paths) -> Aggregate` with `ops`, `schedules`, `provision`, `packages` (in
dependency order), `code_paths`, `data_paths`, `hydrate` / `hydrate_fns`, `routers`,
`method_actions`, `hooks`, `binds`, `owners`.

- `resolve("module:qualname")` — `qualname` may be `Class.method`; a failure names the entry.
- `read_manifest(path)`, `default_manifest_paths(lib_akasha_dir)` (the heart's, the four packages',
  and `archives/MANIFEST.json` at the tree root — the GUI contributes no op, it is there for its
  paths and its OWNER).
- `owner_of(_, path)` — `user` under the application root, `platform` anywhere else (one rule).
- `LateBound` — a hook is called through its module ATTRIBUTE, re-resolved on every call. A
  function-level import re-read the attribute each time, so a module that rebinds one of its own
  functions (the LLM gate's provider entry point, a test double) stayed in effect. Binding the
  function object once at boot would quietly break that; the hook keeps it.

### `api.heart` — the process-level helpers

Memory telemetry (`_rss_mb`, `_smaps_rollup`, `_mem_available_mb`, `_with_rss_delta`), the
serialised nightly-maintenance gate (`_maint_gate_ok`, `_run_gated_maint`), thread/fd counts, the
boot flags (`_autolearn_disabled_reason`, `_boot_bootstraps_disabled`), the nucleus write context
and the job dict shape. Names keep their kernel spelling, so a moved body is unchanged; the
`[maint]` / `[Health]` lines keep the `Akasha.Kernel` logger name.

### `api.concept_class(kernel, prefix)` and `api.hook(kernel, name)`

`concept_class` is the ONE way a lower layer reaches a Concept Model: by its declared prefix,
through the router, never by importing the module. `hook` returns a named upward call a package
declared, or `None` — the caller degrades; it never imports the package.

`api.routers(kernel)` / `api.discover_routers()` give the active dispatchers for code with no
kernel in hand (the CSL validator, the thin CLI client).

**Router protocol** — what a package's dispatcher must answer:
`dispatch_if_handled(method, session, data, rid)`, `get_method_actions()`, `get_class(prefix)`.

---

## 3. Manifest field reference

```jsonc
{
  "package": "workbench",
  "version": 1,
  "owner": "platform",                       // platform | user  (required)
  "depends_on": ["concepts", "source", "ontology"],

  "ops": {
    "bench.info": {"fn": "lib.akasha.workbench.bench:op_info", "stage": "post", "access": "read"},
    "recipe.new": {"access": "write"}        // ACCESS-ONLY: a router dispatches it
  },
  "schedules": {
    "bench_autorun": {"fn": "…autorun:start", "phase": "writer", "order": 120,
                      "when": "every_boot"}, // new_build | every_boot  (required)
    "ontology_load": {"fn": "…loader:boot_load_ontology", "phase": "load", "order": 10,
                      "provides": "ontology.loaded,ontology.normalized"},  // OPENS these gates (comma list)
    "workload_provision": {"fn": "…provision:schedule_workload_provision", "phase": "writer",
                           "order": 115, "after": "ontology.loaded"}   // …and this one WAITS on it
  },
  "thread_units": [{"name": "svc:feed-poll", "wanted": "…:wanted",
                    "thread_attr": "_feed_poll_thread", "start": "…:start", "order": 100}],
  "provision": {"benches": {"fn": "…provision:apply", "order": 10}},
  "hydrate":   {"leaderboard": "…autorun:leaderboard_hydrate_all", "cronon": null},
  "routers":   {"concept_registry": "lib.akasha.concepts.registry:build_active"},
  "binds":     ["lib.akasha.concepts.workflow:set_active_kernel"],
  "hooks":     {"workload_appetite": "lib.akasha.workbench.workload:workload_appetite"},
  "declarations": "config/workbench/workloads/*.json",
  "code_paths": ["lib/akasha/workbench/", "config/workbench/"],
  "data_paths": ["data/"],
  "dirs":       ["data", "logs"],
  "evals":      ["test/workbench_*_eval.py"]
}
```

| field | meaning |
|---|---|
| `package` | the package name; used in dependency order, log lines and the owner map |
| `owner` | **required**; `platform` or `user`. A missing or unknown value is a boot error naming the manifest |
| (no `platform_modules`, no `platform_of`) | the owner lists and the platform half of a shared package are gone (P5): a package is wholly the platform's or wholly the application's, by location. A name a platform manifest declares, an application manifest may not declare again — a BOOT ERROR naming the manifest, the section and the name |
| `depends_on` | packages that must be aggregated first; a cycle is an error naming the chain |
| `ops` | method name → `{fn, stage, access}`. `fn` omitted = **access-only**: the package declares the IAM action while a router dispatches the method |
| `schedules` | name → `{fn, phase, order, when, after?, provides?}`. `when` is a LABEL on the boot line, not a gate |
| `schedules[].provides` | the named GATE this body opens when it finishes, however it finishes. Declaring one makes the gate shut from registration, before any phase runs — which is what stops a consumer winning a race against a producer whose thread has not started |
| `schedules[].after` | the named gate this body must not run before. A body whose gate is shut is reported `status=deferred reason=<gate>` and re-run, in order, the moment `open_gate` fires. **A gate nobody `provides` is open**, so an eval that patches the producer away, or a seed with no packs, runs its `after:` bodies in their normal place rather than waiting forever |
| `thread_units` | host-bound threads the guard re-creates: `{name, wanted, thread_attr, start, order}` |
| `provision` | name → `{fn, order}`; run as admin at boot, idempotent |
| `hydrate` | accelerators this package owns; a value is a regenerator `fn(kernel)`, `null` = declared but regenerated elsewhere |
| `routers` | name → a factory `fn() → router`, built once at aggregation. A factory that raises is logged and skipped |
| `binds` | `fn(kernel)` the heart calls once with itself at boot, so a package gets a kernel handle without the heart importing it |
| `hooks` | name → `fn(kernel, …)`, a named UPWARD call a lower layer may make through `kernel.api.hooks`. Late-bound. A hook nobody declares is simply absent |
| `declarations` | the glob of this package's declaration files (its workloads, macros, pack opt-ins) |
| `code_paths` | trees the SEED owns: written on extract, pruned when the payload no longer carries them |
| `data_paths` | trees the OPERATOR or the runtime owns: never overwritten, never pruned |
| `dirs` | directories `akasha.py` ensures at launch |
| `evals` | the evals that hold this package |
| `ops[].<attr>` | any key on an op entry beyond `fn` / `stage` / `access` is an OP ATTRIBUTE, aggregated into `kernel.api.op_attrs` (and readable without a kernel through `manifest.declared_op_attrs()`). See *Op attributes and extension points* below |
| `effectful_families` | capability families this package's ops take OUT of the cell (`x_broadcast`); `cap.ls` marks their capabilities `effectful`. Unioned with the prefix of every op declaring `"effectful": true` |
| `static` | URL mount → directory relative to the manifest (archives declares `{"/cosmos": "cosmos", "/word": "word", "/field": "field"}`); the launcher and the ASGI front mount it and treat the prefix as reserved. A mount whose directory is absent is skipped with a line |
| `restricted` | URL prefix → the client ids that may read it (`{"/prefix/": ["client", …]}`); `manifest.declared_restricted()` unions every package's lists. The ASGI front serves such a prefix (pages and JSON) only to a token of one of those clients or an admin — cookie `akasha_restricted` (scoped to the prefix) or `Bearer`; a JSON asset is answered 403, a page with a sign-in form (`auth.verify`). The longest declared prefix wins; nothing declared gates nothing; one `[portal] restricted prefixes=…` line at start. The platform names no account: the single-account gate it carried (a client id, its path, its cookie, its boot-created user with a baked passphrase, and `_radu_gate`'s guest refusals in `bench.ls` / `bench.info` / `cap.ls` / `claim.status`) is deleted (purge order §2). A bench not for the public lives in its group (`bench_public: false`) and the scope gate keeps it to its members. Held by `test/restricted_prefix_eval.py` |
| `env` | the environment variables this package reads: name → `{kind, default, means}` (a `*` in a name declares a family, e.g. `AKASHA_LLM_*_CALLS_PER_DAY`). `kind` ∈ path · network · secret · identity · series · capacity · process — a deployment FACT, never a behaviour switch. The heart's manifest declares the platform's 119; `manifest.declared_env()` unions every package's, and the launcher refuses a set `AKASHA_*` name none declares (§4, *The environment*). Held by `test/env_declared_eval.py` |

**The access table is GENERATED** from the manifests' `access` fields plus the routers:
`python scripts/gen_kernel_methods.py` (and `--check` in `manifest_eval`) writes
`lib/akasha/kernel_methods.py`. Never edit it by hand — put the action beside the op.

**The generated tables are split by owner (rulings of 4 October, later).** Both generators — the
access table (`gen_kernel_methods.py`) and the CLI table (`gen_cli_table.py`) — write:

| table | from | to | owner |
|---|---|---|---|
| the platform's | the platform's manifests only (everything outside the application root) | `lib/akasha/kernel_methods.py` (`PLATFORM_METHOD_TO_ACTION`), `api/cli_table.py` (`PLATFORM_CLI_SPECS` / `PLATFORM_CLI_GROUPS`) | platform — in `PLATFORM_TREE.json` |
| each application manifest's | that manifest only | beside it: `MANIFEST.access.json` (`access`), `MANIFEST.cli.json` (`specs`, `groups`) | the application, which regenerates it with the platform's generator, unmodified |

- An application op never changes a platform file, so the application's cut can verify the
  platform tree.
- At import the platform module merges the application tables through `lib.akasha.api.tables`
  (`METHOD_TO_ACTION`, `CLI_SPECS`, `CLI_GROUPS` are the union). A name in both raises
  `TableConflict`, naming the name and both files: a boot error, never one side silently winning.
- A name declared on both sides is already a GENERATION error: an op, a command spelling, or a help
  group with a different label. A help group whose label repeats the platform's word for word is
  omitted from the application table and reported as `redundant:`.
- `--check` compares every table with its generator's output from its own manifest
  (`manifest_eval`).
- In a platform-alone tree there is no application table, and both checks pass there
  (`platform_alone_eval` §2b).

Current shape:

| manifest | ops (with `fn` / access-only) | schedules | units | hydrate | routers | binds | hooks | cli commands |
|---|---|---|---|---|---|---|---|---|
| heart | 57 (55 / 2) | 10 | – | – | – | – | – | 9 |
| ontology | 17 (17 / 0) | 1 | – | – | – | – | – | 11 |
| source | – | 3 | – | – | – | – | – | – |
| concepts | 478 (156 / 322) | 13 | 1 | – | 1 | 2 | 6 | 139 |
| workbench | 14 (14 / 0) | 7 | – | 3 | – | – | 19 | 8 |
| archives | – | – | – | – | – | – | – | – |

### Op attributes and extension points (group 4)

The heart and the mechanism ask BY ATTRIBUTE — "which ops are dive-bearing?" — and never keep a
list of application method names. The attribute sits on the op's own manifest entry, so the package
that owns the op owns the answer. Read with `api.op_attr(kernel, method, attr)`, `api.ops_with(kernel,
attr)`, `api.implementer(kernel, point)`; portals with no kernel read the same JSON through
`manifest.declared_op_attrs()` / `declared_projection(kind)` / `declared_static()` /
`declared_effectful_families()`.

| attribute | who reads it | meaning |
|---|---|---|
| `"implements": "<point>"` (or a list) | `api.implementer` | this op FILLS a platform extension point. Points today: `society.air` (the programme recorder `society.air` forwards to — it raises if nothing implements it), `genesis` (the world-seeding call of the genesis rite — skipped with a line if absent), `render_concept` (the one-concept render the space probe exercises and the portal prerenders `/a/<slug>` with — no prerender if absent), `concept_tree` (the taxonomic navigator `tree … concept=yes` delegates to), `bench.bind_pool` (how provisioning grounds a declared workload's bench in each `source:pool:` it requires — called `{name: <bench slug>, pool}` as admin by `reconcile_workload_resources`, at boot and on the freeze hook, never with a `model:` or `set:` entry; `[bench] provision workload=… pools_unbound reason=no_bind_pool_declared` if absent; the `[bench] resources reconciled` line carries `bound=`). `workload.labo.new` / `workload.labo.bind` (how provisioning makes a declaration's per-pool `labo` true — called `{name, about, scope}` / `{name, pool, origin: "shadow"}`; `[bench] labo not provisioned … reason=no_implementer point=…` if absent; §6.4). `workload.labo.of` (a READ: `{pool}` → `{"labos": [{"labo": "labo:<name>", "origin": "registered"|"shadow"|""}]}` — the labs that already hold a pool; asked only for a `labo` with `when: "unbound"`, and with no implementer no shadow labo is made; 3 October decision 2). The I/O pipeline's endpoints (`lib/harmonia/pipeline.py`) dispatch their verbs as `pipeline.<role>` points — `pipeline.table.create|import|export`, `pipeline.survey.respondent|answer|open|list`, `pipeline.curation.narrate`, `pipeline.deck.new|add|open|list`, `pipeline.frame.add`, `pipeline.concept.card` — resolved by `pipeline_ops.io_dispatch`; a point nobody implements answers `-32601 no op implements pipeline.<role>`. Kernel-less code asks `manifest.declared_implementer(point)` |
| `"dive_bearing": true` | `kernel._dive_bearing` | a read that walks a neighbourhood and so passes dive admission. One `[api] dive_bearing ops=<n>` line at boot |
| `"block_branch": true` | `concepts/workflow.py` | the op takes the advancing workflow branch as block context |
| `"projection": {…}` | the ASGI front, the pulse tap, the MCP server | `reference: {role: letters\|glossary, default_limit}` — a public letter-page read the portal may cache; `pulse: "<surface>"` — a single-concept read the pulse tap records; `mcp: {name, description, inputSchema}` — the tool an MCP client sees (`mcp_tools()` appends every declared one to the heart's own) |
| `"effectful": true` | `cap.ls` | the op's family leaves the cell |
| `"hydrate": {name, layer_v, on_boot, boot_verify, inputs, assigned_key, droppable, desc}` | `concepts/hydrate.py` | this op REGENERATES an application accelerator (4.13). The `hydrate.*` registry is the platform's own table plus one entry per op declaring this; `hydrate.ls` / `run` / `verify` / the boot pass treat it like any other. The platform names no application regenerator |
| `"cli": {"<cmd>": {args, desc, group?}}` | `scripts/gen_cli_table.py` → `api/cli_table.py` (GENERATED) → `api/router.py` | the op's CLI spellings (group 4, 4.6). One op may carry several (`dive` / `look` / `d`); the method is the op itself, so a command can never name an op that does not exist, and a spelling declared twice is a generator error. `group` lists it under a help group no Concept Model class names; the package labels such a group in its manifest's `cli_groups`. `manifest_eval` runs the generator `--check` |
| `"target": "<param>"`, `"target_kind": "bench"`, `"target_required": true` | `api/ops.py` `Entry.call` (manifest ops) · `concepts/registry.py` `_gate_target` (registry ops; also accepted in a `CONCEPT_METHODS` spec) · `api/targets.py` | the PLACE the op writes to (directive 2026-10-02 §6.4). The gate is asked again with it before the op runs — the boundary asked only the action. `target_kind: bench` resolves a bench name to the spelling an assignment line uses (`wb:<slug>` public, `<gid>/wb:<slug>` in a group) through the platform's bench model. `target_required` refuses a call WITHOUT the param (`out_of_scope … (no <param>=)`) — for an op that would otherwise write to a fixed universal namespace. `run` over a place asks REACH only: the run facts (declared · armed · source_ready · headroom) belong to a workload's own run, keyed by its key, and a bench is not one. Held by `test/workload_resource_access_eval.py` §7 |

**The CLI table** (4.6). `CommandRouter.COMMAND_SPECS` is the generated `CLI_SPECS`, the
platform's and the application's commands alike, each declared on its op. The owed data file
(`api/cli_application_owed.json`, 315 entries) closed at 0 on 10-02 and was deleted; the router's
reader of it went with it, so a file that reappears is read by nothing (`ownership_eval` §9). The
router holds no hand-written table. Registry-discovered Concept Models still derive their own specs
from `CONCEPT_METHODS` at runtime (`cli` / `args` / `desc` keys) and label their group with
`CONCEPT_LABEL`. With the short prefixes gone, a command lists under the `group` its `cli` names or
else its method's own prefix — so **every spelling of one op family names the same `group`**
(`ownership_eval` §9 fails on a family split across groups; `pr.export` sat under `pres` until it
named `presentation` on 10-02). Regenerate after editing a `cli`: `python scripts/gen_cli_table.py`.

**Which manifest says which command (rulings of 4 October).** The platform's commands come from the
platform's manifests and land in `api/cli_table.py`; the application's come from its own manifest
and land beside it in `MANIFEST.cli.json` (the split above). The platform's CLI never depends on an
application declaring a platform command: with every application file removed, the table still
holds every platform command and the router still parses `ln` (`platform_alone_eval` §2b). Held by
`manifest_eval` and `platform_alone_eval`.

**Application boot jobs** (4.13). The labo register and the vision-roster line were platform
schedules that dispatched application ops by name; they moved, unchanged in behaviour, to the
application, and are declared in its own manifest (`app/config/MANIFEST.json`) — the platform
neither names nor schedules them. The semcache seeding finds its top-salient
backbone through `manifest.declared_reference("glossary")` (the read whose `projection.reference.role`
is `glossary`) and logs `[semcache.featured] top_salient skipped reason=no_glossary_declared` when
none is. A boot job polls `api.heart.shutting_down()` rather than importing the lifecycle module.

**The source engine records and announces** (4.11). The feed poller (`svc:feed-poll`, `feed.poll`,
the telemetry GC, the telemetry-day retention classifier), the `analysis.precompute` / `analysis.diag`
ops and the media / analysis precompute passes drove application Concept Models by name. They moved,
unchanged in behaviour, to `concepts/feed_poll.py`, `concepts/analysis_ops.py` and
`concepts/precompute.py`, and their manifest entries (ops, schedules, the thread unit, the hook) moved
from the source manifest to the concepts manifest. `source/` keeps pools, packs, the declared-corpus
bootstraps and the fetch. Turning the polls and precomputes into declared workloads is the
application's step.

**First-run seeds are recipes** (4.4). `lib/akasha/seeding.py` (`sys.onboarding.seed app=`)
re-creates each shipped `seeds/<app>/*.akasha` capsule through the ops a RECIPE names —
`config/seed/*.json` (application data, declared in the concepts manifest): `doc_types`, a `create`
step run once with the seed metadata, an `item` step run once per atom of the capsule's
`sys:top → sys:next` chain. Arguments are templates — `{title}`, `{text}`, `{meta.role}` (the item's
atom_meta), `{a|b|literal}` — and an empty value drops the argument. The planter dispatches through
`api.routers()` and names no Concept Model; a doc_type with no recipe logs
`[seed] skipped doc_type=… reason=no_recipe`. (It used to import the note and fieldnote models; and
`sys.onboarding.seed` imported `.seeding` relative to `concepts/`, so it failed at import on every
cell.) Held by `test/seed_recipe_eval.py`.

**The world's axis is the platform's** (4.14). The society and the workbench record on the shared
world's axis (society formed / connected / severed / moderator mode; bench created / retired; a
workflow dispatch synced). They reached it through the application's `world` Concept Model by
prefix. They now hold `concepts/world_axis.WorldAxis` — the minimal SYSTEM world container: the
world's clock, `op_tick`, `op_env_record`, `op_sync_record`, `genesis` — which writes exactly the
atoms the world model's commons ops write (`world:<w>:env:<n>`, `world:<w>:sync:<n>`, clock
`world:<w>`, the env / sync Sets and coordinate Sets), so both write one axis. The topology model
(places, laws, portals) stays the application's; its commons ops may delegate to `WorldAxis`. The
heart's own `graph.tree` view uses `api.views` (`node`, `tree`), the same `_view` shape as the
application's `TextViewConcept`. `ownership_eval` §8b fails on any platform
`concept_class(…, "<application prefix>")`.

**Multi-registrant hooks.** `api.hook(kernel, name)` returns the one registration (the last);
`api.hooks_all(kernel, name)` returns EVERY package's, in package order, for a question each may
answer. The per-minute workload roll-up counts `effects_today` (it said `aired`).

**System identities** (4.15). `api.trust.system_identity(name, role)` registers an internal
identity (reachable only over TRUST_INTERNAL / TRUST_LOCAL); the heart names only its own three
(weaver, librarian, jataka). The society module registers `system.broadcaster`,
`system.moderator` and `system.observer` as `librarian` at load.

**Anonymous role** (4.1). An unknown bare id over the network is a guest whose role comes from the
gate's `anonymous` lines (`gate.lines_for("anonymous")`), not from a series branch in `identity.py`. This holds in EVERY series and whatever role the caller asks for: the manager's old fallback (an unknown id got its `requested_role`, admin by default, outside the thesaurus tier) now applies only when the assignment file has no `anonymous` line at all. A local operator is a REGISTERED identity (genesis registers admin); `test/admin_reserve_eval.py` holds both halves.

**Data the application writes, the platform reads** (4.7, 4.9, 4.10): `archives/site.json` (what a host
calls itself — most specific first: `archives/<host>/site.json`, a `hosts` entry, then `name`; an
optional `term_set` names the JSON-LD DefinedTermSet, defaulting to the site name);
`ontology/*/canon.json` (`rules` — the pack rules the loader checks, below); `ontology/REGISTRY.json`
`reserved_dirs` (directories under `ontology/` that are not packs — none today).

**The ontology is loaded as written, or refused — never repaired** (the purge order §3,
`lib/akasha/ontology/validate.py`). There is no runtime canon pass, no `canon.py`, no
`OntologyNormalizer`: the loader writes what a pack says and nothing else. The rules a pack must keep
are the application's, declared under `"rules"` in any `ontology/<pack>/canon.json` (all files
unioned). A rule:

```json
{"id": "<what the refusal names>", "every": "<name prefix>", "depth": 1, "except": ["<name>"],
 "link": "<relation>", "to": "<target prefix>"}          // or: "in_set": "<set name>"
```

The subjects are the names a pack DEFINES (`def`) starting with `every` (with exactly `depth` `:`
separators, less `except`). Each subject needs, IN THE SAME PACK, `ln <subject> <dst> <link>` (with
`dst` starting `to`), or `set.add name=<in_set> id=<subject>`. A changed pack is checked before any of
it is written. A pack that breaks a rule is refused whole: no atom written, no sentinel (the next
boot checks again), its relations left out of the global phase, nothing reconciled. A malformed
rule is reported (`[onto] rule ignored file=… rule=… reason=…`) and not applied. An unchanged pack
(sentinel hit) is not re-checked. Held by `test/pack_validation_eval.py`.

### Adding things

- **An op** — write `fn(kernel, …)` in a package module, add one `ops` entry with its `stage` and
  `access`, regenerate the access table. For a CLI spelling, give the entry a `cli` and run
  `python scripts/gen_cli_table.py`. Nothing in the heart changes.
- **A schedule** — write `fn(kernel)`, add one `schedules` entry with `phase`, `order` and `when`.
- **A Concept Model** — a class with `CONCEPT_PREFIX` / `CONCEPT_METHODS`: the platform's under
  `lib/akasha/concepts/`, an application's under `app/concepts/` (never the other way). The
  registry router finds it. Its methods are access-only `ops` entries.
- **A package** — a directory with a `MANIFEST.json` declaring `package`, `owner` and
  `depends_on`, added to `default_manifest_paths`. Everything else follows from its declarations.
- **A new relation or namespace** — the platform's: register it in `scripts/gen_lexicon.py`
  (`CORE_RELS` / `CORE_NS`); an application's: its `app/config/lexicon.json` (SPEC §5.10). Then
  regenerate (`python scripts/gen_lexicon.py`) and confirm `python test/verify_lexicon.py --all` is PASS.

---

## 4. Deployment contract

The crystallizer unions every package manifest's `code_paths` / `data_paths` / `dirs` into the
`SEED_MANIFEST` it embeds beside the payload, refusing **at build time** any declaration that
could escape the tree (absolute, or containing `..`), naming the manifest. `safe_extract` and
`prune_stale` in the emitted self-extractor are **one loop each** over that manifest and compare
no basename. The old `PROTECTED_PATHS`, `PRUNE_KEEP`, `PRUNE_EXTS` and the `.env` basename test
are gone. `akasha.py` ensures the declared `dirs` at launch.

The rules, in full:

1. a path under a `data_path` is **never written when it exists** and **never pruned**;
2. a path a `code_path` claims is written, and pruned when the payload no longer carries it;
3. a path no `code_path` claims is left alone — an operator's own file beside the seed's survives;
4. `keep_paths` (the crystallizer's per-series exclusions) is never pruned, even inside a claimed
   tree;
5. a payload entry with `..` or an absolute path is skipped at extract time.

Consequence worth stating: the prune now touches only what a manifest claims, so an operator's
`config/tls.json` survives where it used to be deleted. That is a narrowing of a destructive
action, in the safe direction.

**The protected-path inventory** — every path the retired `PROTECTED_PATHS` list shielded, and the
manifest that now claims it. Held by name in `test/deploy_eval.py`, so the list cannot quietly
shrink.

| protected path | now declared in |
|---|---|
| `data/` (the store — **and `data/central/secrets.env` inside it**) | heart `data_paths` |
| `env/models/` | heart `data_paths` |
| `env/deployment.env` | heart `data_paths` |
| `env/secrets.env` | heart `data_paths` |
| `.env` | heart `data_paths` |
| `docs/user/` | heart `data_paths` |
| `apps/custom/` | heart `data_paths` |
| `lib/plugins/` | heart `data_paths` |
| `logs/`, `config/tls.json` | heart `data_paths` (added by this mechanism) |
| `ontology/user/` | ontology `data_paths` |
| `archives/snapshots/` | archives `data_paths` |

---


**Which declared paths the payload carries.** The crystallizer ships every declared `code_paths` /
`data_paths` entry whose top-level directory no other packing rule owns, plus `config/`
(`Cryptobiosis._generic_declared_entries`). The owned set is read from the blueprints: every
series' `core_dirs`, `extra_dirs` and bundled file lists, the `docs/`, `ontology/` and `apps/`
selections, and the manifests' runtime `dirs`. So a new tree — the first-run capsules under
`seeds/<app>/`, for instance — ships with nothing more than its declaration, and a tier rule (archives
only on service tiers, a docs selection, the tiered ontology) is never bypassed. Dot-files never ship.
A shipped file is replaced and pruned by the extractor only if its extension is in `SEED_CODE_EXTS`,
which includes `.akasha`. Held by `test/seed_declared_paths_eval.py`.
Every directory under `config/` must be claimed by a declared path — an undeclared one ships in no
seed, silently (the operation profiles did, until `config/profiles/` became a workbench `code_path` on
10-02); the same eval fails on one. Config a cell must RECEIVE updates of is a `code_path`; a
`data_path` is never written when it exists.

**The source engine's two pool facts (§6.1, §6.4).** `set:source:pool:frozen` holds every frozen,
non-empty pool's key; the source engine is its only writer — stated at freeze (before the
`source_ready_changed` hook fires) and reconciled at boot (`[source] frozen pools reconciled
set=… members=… added=… removed=…`). A pool's by-status tally is LIVE: `source.pool.create` starts
it at zero, `source.pool.add` counts the member it gains, and `_set_item_status` (the one door for
an item's status) moves one count in every pool the item belongs to. Freezing reads it and never
recounts. Nothing adopts or recounts a tally (the purge order §2 deleted `source.backfill`, the
adoption and the drift recount): a pool this engine did not create has no live tally and reads zero,
and a status written around the door is refused at the store (engine-owned fields), so there is no
drift to recount. Held by `test/workload_resource_access_eval.py` §6–§7.

**The door is public: `source.item.status pool= item= status=`** (directive 10-03 item 5). Code
outside the source engine sets a member's status through it, never by writing `status` into the
item's meta. One write moves the item's meta, its `source:status:<s>` Set (old out, new in — the
removal now goes to the store `_add_to_set` wrote, `_rm_from_set`), its source's tally and every
pool's. Gated `record` on the pool (a declared, required target: no `pool=` is refused
`out_of_scope`); WHAT IS AN ITEM is decided by MEMBERSHIP — any member of `pool=`, whatever its concept (the engine names no application concept; 10-03 §6) — and a non-member is refused `not a member of <pool>`; a member with no prior status moves its tally +1 into that bucket (`changed: true`, the vlab path); the same status twice is `changed: false` and moves nothing — a status written AROUND the door is refused at the store (engine-owned fields), so the door has nothing to repair; the old status the door moves out of is the one its write replaced (read inside `merge_meta`), so two concurrent door calls on one item move one count each; `status` is one of `ITEM_STATUS`;
idempotent (`changed: false`). Held by `test/source_item_status_eval.py`.

**The id-set table is the shipped one; the assignment file is the cell's.** `idsets.json` (what each
row may do) is the platform's vocabulary and is READ FROM `config/identity/` as is — no cell copy, no
upgrade, no `.bak` (the purge order §2). A cell's `assign.ak` (who holds what) is its own: seeded once
from the shipped file, written only by `identity.assign` and the account entrances (genesis,
`user.add`, membership, self-registration); there is no migration and no line adoption. A line may
name a NAMED TARGET (`gate.NAMED_TARGETS`: `feeds` = the source feeds) instead of a place; a named
target opens no group engine. Held by `test/workload_resource_access_eval.py` and
`test/seed_payload_eval.py` (the shipped telemetry line).

**An eval's script dependencies.** A bundled eval that loads `scripts/<name>.py` the payload does not
carry stops the cut (`_assert_eval_script_deps_bundled`). A reference is a CALL whose positional
arguments hold `"scripts"` then `"<name>.py"` — read from the AST (`_eval_script_refs`), so a tuple,
list, comment or string naming a script is not one (ownership_eval's walk tuple blocked every cut
until 10-02c); an unparseable eval falls back to the text match. Held by
`test/crystallizer_script_deps_eval.py`.

**A workload ships with what it requires** (frontend 26d). Inside that pass, a workload declaration
(`config/workbench/workloads/*.json` with `bench` + `workflow` + `society`) ships only when the same
payload CARRIES every `source:pool:` and `model:` it `requires`: a pool is carried when a bundled
`assets/<pack>/pack.json` or a bundled `config/source/<id>.json` declares it, a model when the
bundled `assets/models/model.json` names it and its file ships. A `set:` requirement never withholds
(an ontology Set can land from a pack a cell enables later). A withheld declaration takes its bench's
directory `config/workbench/<bench>/` with it when no shipped workload uses that bench, and the build
prints `[seed] workload withheld file=… reason=requires_not_carried missing=…`. So a tier's DATA rules
decide which labs it gets, and a declaration needs no tier field. Measured: `seeds14` withholds
`plants_vision.json` and `config/workbench/plants-vision/` (11 entries); `thesaurus09` withholds
nothing. `Cryptobiosis._withheld_workloads`; held by `test/workload_tier_scope_eval.py`.

### The data-format id (the purge order §4.4, `lib/akasha/data_format.py`)

A cell's store is written in ONE data format, named by `DATA_FORMAT_ID` (today
`akasha-cell-2026-10-03`). The first boot of a fresh directory stamps it into `central/DATA_FORMAT`
(fsync'd) BEFORE the store exists; the serve-only portal never stamps. Every boot reads the stamp
before anything opens or writes the directory — `akasha.py` right after it resolves the data
directory (before its boot lock, heartbeat and backend marker), and `KernelDispatcher.__init__`
before the gate binds. A directory stamped with another id, or a store with no stamp (written
before stamps existed: `found=none`), stops with ONE line and writes nothing:

```
[cell] data format found=<id|none> expected=<id> dir=<path> — this build does not read it. Move this directory aside and start fresh. To keep atoms, dump them with the old build and describe them again as a pack in ontology/user/.
```

The kernel raises `DataFormatMismatch`; the launcher prints the line on stderr and exits **3**.
There is no migration (rule 1). Change the id only with a change to what is ON DISK. Held by
`test/data_format_eval.py`.

### The environment (the purge order §4.5)

The environment carries **deployment facts only** — where the cell lives, whom it talks to, its
secrets, its name, its series, its budgets. **There is no behaviour switch in it**: every
`AKASHA_NO_*` / `AKASHA_FORCE_*` / override / opt-in variable the platform used to read was deleted
together with the code path it chose, and the default behaviour is the only behaviour. That
includes the allocation tracer (`AKASHA_ALLOC_TRACE`, ruling 4 October): tracing slows and enlarges
every allocation, so turning it on changes the running product. The always-on `[Health]`,
`[MemTop]`, `[Silica] open` and `[NativeLoad]` lines answer the memory questions; a deeper
investigation runs out of band, on a copy of the cell, with Python's own `PYTHONTRACEMALLOC`. Where a
behaviour still differs between deployments, a declared fact decides it — the series (`load_all`
tiers reconcile ontology; the seeds line learns embeddings on demand), the process's role (a
serve-only portal never writes), the presence of a key (the supervisor verifies recipes when a key
exists), a declaration's own `enabled: false` (a corpus).

- **Declared.** Every `AKASHA_*` name the platform reads is a row in the heart manifest's `env`
  (`kind`, `default`, `means`); an application package declares its own in its manifest.
  `manifest.declared_env()` reads them as data, without importing anything.
- **Published.** `docs/deployment.md` is generated from those rows —
  `python scripts/gen_deployment_doc.py` (`--check` in `manifest_eval`) — and ships in every seed.
- **Refused by name.** `akasha.py main` reads `env/deployment.env` (setdefault), then refuses every
  `AKASHA_*` variable — exported or in the file — that no manifest declares: one
  `[env] refused name=<NAME>` line per name and exit **3**, before anything reads the environment.
  `stop` is exempt, so a cell can always be halted. There is no "ignored" list: a name nobody reads
  is not declared, so it is refused.

Held by `test/env_declared_eval.py`: every name in a platform module's string literals is declared,
every declared name is read, every row has a known kind and a meaning, the real launcher refuses
(exported and file) and proceeds on declared names, and the page is current.

## 4b. The workload model — what a scheduled unit of work declares

Seed A slice 1. A workload on a workbench — a research experiment, a broadcast programme, an
operational process — is DECLARED in one file and read by one driver. `config/workbench/workloads/
<slug>.json`, nine frozen fields:

| field | what it says |
|---|---|
| `bench` | the workbench it runs on (`wb:studio_ai`) |
| `workflow` | the slug: names its template, and IS its branch on the bench |
| `society` | `<group>/<space>` — where it speaks |
| `trigger` | `{"boot": true, "then": "every:1800s" \| "daily:07:00Z"}` — when it is due. Daily is UTC |
| `duty` | `wb:duty:continuous` \| `wb:duty:best_effort` — what the driver owes it when a gate stops it |
| `effect` | `publish` \| `record` — whether its output faces the public. Whether it has a ROOM someone can open is the separate question `workload.publishes_to_room` answers, ONCE, from the declaration: a workload that publishes to an external channel (`pins.channel`) publishes and has no room |
| `appetite` | `{llm_calls_per_run, weight}` — what ONE run costs the model provider |
| `budget` | `{per_day, max_wall_s, max_steps}` — what a DAY of it may cost. `per_day` is the EFFECT allowance, not poll beats: a run spends one by producing the declared effect (an airing for `publish`, a completed run for `record`). A run that produced nothing, and a failed run, leave it unchanged — `autorun.run_charges_allowance` is the rule, charged at one site. Attempt rate is bounded by the cadence, retries and `BOOT_AIRING_TRIES`; the day's model SPEND is bounded by the LLM pool, which is the authority for spend |
| `pins` | the atoms and Sets its template steps resolve against |
| `idset` *(optional)* | the ID set provisioning assigns the workload's CLIENT, on its two own places: its space `<gid>/<space>` and its bench — `<gid>/wb:<bench slug>`, or `wb:<bench slug>` for a `bench_public` bench (what a bench op's gate target is). Absent → `programme`. Only a row whose `on` is `assigned` in `config/identity/idsets.json` — and that is not a resource row (`facts: false`) — may be named (today `programme`, `researcher`, `member`, `telemetry`), so a declaration cannot give its client `admin`, `librarian`, `resident` or `consumer` (`reason=idset`). Provisioning CONVERGES: a line the client holds on those places for another ID set is removed. A lab declares `researcher` (it `record`s on its bench) |
| `workflows` *(optional)* | the branches the workload runs, in order, each loaded from `config/workbench/<bench>/templates/<name>.ak` onto the branch of that name. Absent → one branch, the `workflow` slug. `workflow` stays the workload's NAME (the accounting key, the default client); a listed name with no template refuses the workload `reason=template` naming each missing file |
| `sweeps` *(optional)* | sweep definitions, `config/workbench/<bench>/sweeps/<name>.json`, applied at provisioning (`sweep.def`) and carried in the policy; the driver picks their branches after a static run ends ok |
| `grants` *(optional)* | cast → responsibility kinds (`operator:<family>`, `decide`) the declared casts hold on the society, beside the default `operator:air` |
| `requires` → resource lines | for each `source:pool:…` / `model:…` entry, provisioning writes `<client> consumer on <resource>` — the `consumer` row: `read` · `run`, never `record`, `facts: false` (a job over an input is not the workload's own run, so `declared`/`armed`/`source_ready`/`headroom` are not asked of the pool). CONVERGES: a line for a requirement that is gone is removed. `set:` entries add no line. The client's main ID set stays on its own two places. The target is the resource key itself (no source or model op asks the gate with a pool target yet; a gate question about a pool names its key). **`set:source:pool:frozen`** (§6.1): the client is bound to EVERY member of the source engine's frozen-pool Set, and to a pool that freezes later at its freeze (the `source_ready_changed` hook re-converges); one function does it all — `provision.reconcile_workload_resources`, run by provisioning, by the freeze hook and at boot (`reconcile_run_facts`). Held by `test/workload_resource_access_eval.py` (directive 2026-10-02 §5.2, §6.1) |
| `labo` *(optional)* | `{name: "<pattern with {pool}>", about, scope}` (§6.4). For each pool the workload requires (Set members included), provisioning ensures that labo and binds the pool, as admin (the installer's `provision`), through the `workload.labo.new` / `workload.labo.bind` points, and again on the freeze hook. `{pool}` expands to the pool's slug (`source:pool:plants_images:v1` → `plants_images_v1`); a name without `{pool}` on a workload that can require more than one pool is refused (`reason=labo`). `when`: `always` (default — every required pool) or `unbound` (a SHADOW labo — only for a pool no other lab holds, asked through `workload.labo.of`; a pool held by a registered lab is skipped with `[bench] labo shadow skipped workload=… pool=… registered=…`; registered labs win, 3 October decision 2); any other value is refused (`reason=labo`) |
| `profile` *(optional)* | names a file under the profiles root, `config/profiles/<p>.json` (ruling of 4 October). Its fields are the declaration's DEFAULTS, applied when `workload.declarations()` reads the file: a field the declaration states wins, a dict field (`space`, `budget`, `trigger`, `moderator`, …) merges key by key with the declaration's keys winning at every level, and the profile's `_` keys are not copied — so a declaration without `duty` takes the profile's. An unknown profile is a provisioning error by name: `[bench] workload profile unknown file=… profile=<p> root=config/profiles`, then `[bench] provision failed … reason=profile`. Also a Set membership `set:wl:profile:<p>` a page can group by. Held by `test/workload_profile_eval.py` |
| `bench_kind` *(optional)* | the kind the bench records (`bench.ls` / `bench.info`, and the families a registered kind records). Absent → the declared `effect` (the order-§3 default: the platform maps nothing; a declaration may state a kind) |
| `bench_public` *(optional)* | `true` → the bench lives in the NUCLEUS (guest-readable, its own place `wb:<slug>`) instead of the workload's group (`<gid>/wb:<slug>`). The client's ID-set line follows the bench; the line on the other spelling is removed. Absent → `false` |
| `space.kind` / `space.identity` *(optional)* | passed to `society.new`: `chat` \| `cowork`, `open` \| `locked` (`reason=space` otherwise) |

**A workload is the ONE author of its bench** (26d). `bench.new` is create-if-absent, so a bench that
already exists keeps its placement and kind; provisioning compares them with the declaration and
reports a difference by field id — `problem=bench_public: wb:<slug> exists as a public bench and the
declaration places it in <gid> …` / `problem=bench_kind: …`. The placement one is not cosmetic: the
client's line is on the declared place and every bench step is gated on the real one. The legacy
bench SCAFFOLD (`workloads/bench_<name>.json`, applied by `provision_apply_bench`) is still read for a
contract that is not a workload (`bench_research.json`), but the crystallizer no longer writes
`bench_plants_vision.json`: that scaffold made the lab's bench PUBLIC while its client held a line on
`plants-lab/wb:plants_vision`, and every bench step the lab ran as its client was refused
`out_of_scope`. Held by `test/workload_bench_place_eval.py`.

**The driver reads five of them** — `trigger, duty, effect, appetite, budget` — and no sixth. There
is no `kind`, no `"station"`, no studio name and no society-name comparison in `autorun.py`,
`admission.py`, `society.run` or the recorder; `test/workload_grep_eval.py` holds that statically,
because it is the one property you can only demonstrate by not finding something.

**What the platform answers about a workload — `workload.status key=<key>`** (a read;
`wl_state.handle_status`). Four fields and not one word of application vocabulary:

| field | what it is |
|---|---|
| `last` | `{at, ok, job_ok, reason, effect_count, spent, by, job_id}` — **`ok` means the DECLARED EFFECT happened** (D15, 09-27): `job_ok and run_charges_allowance(pol, effect_count)`, the one predicate the allowance, the effect clock and the spent-without-effect guard already use; `job_ok` is the job's own outcome, so a stood-by run reads `{ok: false, job_ok: true, reason: <the op's id>}` and not as on air. A declaration with no `effect_read` keeps "a successful job is the effect". The newest row of the workload's OWN run record (`wl_state.record_run`, a bounded vault ring `wl_run/<key>` of the newest 200 rows, written by the driver once per run whatever the run's fate — refused at admission, failed in its job, or succeeded). Group 4, 4.12(a): it used to be read from the APPLICATION's rows, so a run that wrote none under its own key (a refusal, a failure before the first turn, a publish keyed under its source programme) had no outcome and `last` answered with some other run. `reason` is the refusal id or the job's own error, **verbatim, and empty when there was none**. `effect_count` is read through the op the declaration names in `effect_read` (below); a declaration that names none counts a successful job as its one effect |
| | **`effect_read`** (optional declaration field, 4.12(b)) — `{op, args, rows, effect, reason, at}`: the read op that lists this workload's effect rows, the args (`{bench}`, `{key}` substituted), the key of the row list in its result, the row field that says the row is an effect, and the fields carrying its reason and time. The platform calls it with `since=<run start>` and counts; it never names the application's op in code. Provisioning validates it and projects it into the policy the driver reads |
| `gate` | `{run: "ok" \| <term>}` — the gate's answer for `run` on this key: `declared` / `armed` / `source_ready` / `headroom` / `roles`, the only reason vocabulary the platform owns. REACH (step 3) is asked of the workload's SPACE and the FACTS (step 4) of its KEY — `gate(client, run, key, place=<gid>/<space>)`. A key is not a place: a station's key happens to spell its space, a lab's (`plants-vision/plants_vision`) does not, and asking reach of the key answered `out_of_scope` for a lab that runs fine (26d) |
| | `requires` has THREE KINDS, told apart by prefix and each answered by its owner: `model:<name>` a bundled binary (nothing to wait for), `set:<name>` an ontology Set (ready when it has members — looked up by its BARE name first, the way an `.ak` writes `set.add name=`, then literally, since the platform's own fact Sets carry `set:` in their stored name; `set:` is the requirement's kind, not part of the Set's name), anything else a source pool (ready when frozen and non-empty). One predicate — `provision.requirement_ready` — serves both the fact that DECIDES and the list that NAMES the wait, so a room's reason can never contradict the gate's answer. Everything non-`model:` used to be asked of `pool_frozen`, so a `set:` requirement waited on a pool that was never a pool |
| | **All four RUN facts hold WORKLOAD KEYS**, and each has one writer: `declared` (the loader, at boot), `armed` (the driver), `source_ready` (the workbench, from the pools the declaration requires — at boot and on the source engine's `source_ready_changed` hook), `headroom` (admission, at reserve / refusal / settle, and at boot from the pool). An unstated positive fact reads as "no", so a fact with no writer makes the step permanently unpassable: two of these had none, and the status of a programme that was on air answered `source_ready` and then `headroom` |
| `next_at` | when the trigger next opens, from the declaration's cadence, measured from the last EFFECT (`wl_state.last_effect_at`, through the declared `effect_read`) |
| `next_at` | when this workload next TRIES — `next_attempt`, **the same function the driver writes into `retry_at`**. A non-zero answer is always strictly in the FUTURE: `last_run + cadence` is measured from the EFFECT clock, which a run producing nothing never advances, so once the gap exceeds one cadence that sum is a moment in the PAST, and a past `retry_at` reads as "due" on every tick (D1: 87 runs in 90 minutes for a four-hourly declaration). The window rolls forward by WHOLE cadences, keeping the declared phase |
| `spent_today` | the model calls charged to this key today, read through `llm_program_spent` + `llm_active_provider`. A hook name no manifest carries is a spelling mistake the platform cannot see at boot — it returns `None`, the caller's `except` swallows it, and the field reports a confident 0 |

**There is no `state` field, and there will not be one.** "On air", "standing by", "rebroadcast"
and the sentences around them are the APPLICATION's words, composed on the page or in its Concept
Model from `last` and `gate`. The platform records and answers; the application names (ruling
2026-09-23, `docs/handoff/backend-status-is-the-applications-2026-09-23.md`). The stamped register
that preceded this — `station:show:*`, `set:station:state:*`, `society.station`,
`set_programme_state` — is deleted: every field on it was the platform naming an application's
status, and it was a second copy of facts the observations already held, so the two could and did
disagree. **A platform module that needs to name a status is a defect**, and
`test/platform_vocabulary_eval.py` fails the build for `station:state` / `station:reason` /
`no_text` outside the LLM gateway.

**Retry policy stays the platform's**, keyed on the platform's own terms — the gate's, plus the LLM
gateway's transient outcomes (`llm_pool`, `provider_429`, `provider_capacity`, `no_text`). An empty
reason, or one the application chose, is **not** transient: it waits for the next trigger rather
than spinning under a word the platform supplied for it.

**The key is `<bench>/<slug>`** — `studio_ai/news_show`, the bench without its `wb:`. It is what
the model-provider ledger, the day's spend and the carry-over credit are accounted under, so it is
derived, never accepted from a caller: a client that could name its own key could spend another
workload's credit. `workload.workload_appetite(kernel, bench, branch)` is the hook the workflow
layer calls to derive it, keyed on the PAIR because four workloads share one bench.

**Every field is also a Set.** Provisioning writes `set:wl:bench:*`, `:workflow:*`, `:society:*`,
`:trigger:*`, `:duty:*`, `:effect:*`, `:appetite:calls:N`, `:budget:per_day:N`, `:pins:*` on the
workload atom, mechanically named and reconciled on every boot. That is what makes `bench.info`'s
`programmes` a Set intersection (`set:wl:effect:publish` ∩ `set:wl:bench:<b>`) instead of a test
for what the bench is called.

**Where the code is.** `workbench/workload.py` (the declaration: reading, validating, the five
fields, the Sets), `workbench/workload_provision.py` (the plan as data + its execution),
`workbench/wl_state.py` (the states, the reason ids, what a bench aired), and
`provision.provision_workloads` (the boot body — the one authority). `station_provision.py` is
gone.

**Adding a workload is a file.** Drop a declaration in `config/workbench/workloads/` and a template
at `config/workbench/<bench>/templates/<slug>.ak`. The next boot provisions it, arms it, gives it
its own branch and a guide row, and the driver runs it on its declared cadence. Nothing in the
platform changes.

**A declaration is a desired state; a boot reconciles to it.** Every provisioning step is an
ensure, and there is no "is it provisioned already?" predicate — that two-path version is what kept
a programme off the air for two days, because its society existed and was armed (so the boot
skipped the plan) while the workflow entries its runs needed had never been written. *Armed is not
provisioned.*

**Reconciling BOTH ways: the undeclared cannot run.** The declaration loader reconciles
`set:wl:declared` to the files on every pass, so a workload whose declaration is gone loses its key,
and the gate's step 4 refuses its run `declared`. That is the whole mechanism — the purge order §2
deleted `retire_undeclared` / `retire_undeclared_benches` and their retired rows. Nothing is disarmed
or marked: the society, its feed and its bench stand, and a declaration that comes back makes it
runnable again. Held by `test/workload_conformance_eval.py`.

**The driver's first tick waits for the declared-workload pass** (directive 2026-10-03 item 1). The
kernel creates `_workload_provision_done` before the writer phase runs; the declared-workload body
(`workload_provision`, `after: ontology.loaded`, which writes the workflow entries a run executes)
sets it in a `finally` — with declarations or without, ok or raising — and `lifecycle` sets it on
shutdown. The driver waits for it, with a 30-minute ceiling, then `[bench.auto] provisioning pass not
seen after 30min — ticking on the stored policy`. There is ONE provisioning path: the legacy
`bench_*.json` / `auto_exec.json` pass and its A51 event are deleted (the purge order §2); a workload's
capabilities come from its declaration's `grants`. Held by `test/bench_provision_order_eval.py`.

**A workload runs as its declared client.** `workload.client_of(decl)` is the one answer to "who is
this run?", and the driver dispatches `society.run` as that client — `[bench.auto] run start …
as=<client>`. Admin provisions and reads; it does not speak. The gate that had to move for this is
`job.submit`: **who may enqueue** is not the same question as **what the job may do**. A submit over
`TRUST_INTERNAL` — which only the kernel sets, never a client — is admitted; every other transport
keeps the admin/librarian gate. The owner is still pinned to the submitter, every step is still
re-authenticated as that owner, and `validate_steps` still blocklists the same families. Nothing a
job can DO changed.

**Two clocks, and they answer different questions.**

| key | means | read by |
|---|---|---|
| `last_run` | when the workload last PRODUCED ITS EFFECT | the `daily:` / `interval:` window |
| `retry_at` | when it will next TRY | `autorun_due`, and the guide row's `next_update_at` |

`last_run` is stamped in the same statement block that charges `runs_per_day`, once the outcome is
known, at ONE site. Stamped on the attempt instead — which it was — one empty boot run satisfied
today's window and bought a whole day of silence for a failure nobody had yet diagnosed.

`retry_at` **is** the schedule while it is set: it brings the next attempt forward AND holds it
back. Read only as "fire early", an armed retry said two things at once — *wait until 10:02*, and
*also run on any tick the window happens to be open* — and with the window no longer closed by an
attempt, the second is a run every sixty seconds. Every branch of a run that produced nothing leaves
one behind, so nothing is unpaced.

**A retry is for what a retry can fix.** `wl_state.TRANSIENT_REASONS` — `llm_pool`, `provider_429`,
`provider_capacity`, `no_text` — get the growing backoff. Every other reason, **including every id
the platform has never heard of**, is a grant or a precondition: no retry creates a workflow, admits
a cast or loads a corpus. Those say `[bench.auto] not retried society=… reason=<id> (waits for
provisioning)` once and wait for the next provisioning pass or boot, either of which clears
`retry_at`. A reason id is an opaque string the application chose; nothing else validates it.

---

## 4c. The declared source import — one managed unit, any corpus

Step 2. A corpus that must be loaded into a cell at boot is DECLARED in
`config/source/<id>.json` (under the application root) with an `importer` naming a callable, and the platform
runs it. **The platform knows the mechanism; it knows no dataset.**

```python
run_declared(kernel, decl, ctl=None) -> {
    "status":  "complete" | "skipped" | "no_data" | "degraded" | "failed",
    "detail":  str,        # one line, for the log and the unit's status
    "sentinel": bool,      # may the caller stop asking?
    ...                    # dataset facts: images / members / added / acquired, pool
}
```

`sentinel` is the whole of the return value's purpose. Only `complete` and an **unchanged**
`skipped` earn it; `no_data`, `degraded` and `failed` do not, so an interrupted or silently
degraded run is retried on the next boot rather than recorded as finished. A corpus the cell does
not carry returns `skipped` with `sentinel: False` — most cells ship no corpus, and a boot that
treats that as an error spends every boot reporting it.

`ctl` is the seam to the managed unit: `ctl.say(msg)` names one phase (and beats the heartbeat, and
**raises** on cap or shutdown — an importer must let that propagate), `ctl.progress()` /
`ctl.advance(n)` carry the resume cursor. Its default is a working stand-alone one, so an importer
runs from a terminal or an eval with nothing else present.

**What the platform owns** (`source/bootstrap.py`, written once rather than once per corpus): the
run-once sentinel `source_bootstrap_<id>.done` keyed on a digest of the declaration's `reset_key`
(change the key, the corpus re-imports), the progress file, the heartbeat, the hard wall-clock cap,
the relations-ready wait and the serve-first gate — and **one thread, serial, in id order**, because
four corpora do not earn four threads (R3). R4 holds: the sentinel is read before any file is
opened.

**The schedule says what it found, every boot** —
`[source.bootstrap] declarations found=N runnable=M [ids=…]`. `found=` is what the tree has,
`runnable=` what survives `"enabled": false`. This line exists because the branch was silent: a cell
that carries no corpus and a cell whose declarations were dropped in packaging both reach the same
early return, and four seeds shipped importing nothing with no log saying so. **`found=0` on a tier
that is meant to carry a corpus is a packaging defect, and this is where you see it.**

Off: `"enabled": false` in the declaration — the one switch, and it is the declaration's own (the
environment switches are deleted, the purge order §4.5). Skips carry reason ids (`decl_unreadable`, `import_failed`,
`unit_failed`). Eval `test/source_bootstrap_unit_eval.py`.

**A corpus's schema policy is data too.** `scripts/corpus_to_ak.py` — the off-line generator that
turns a dataset into an `.ak` pack — reads `config/source/corpus_policy/<name>.json` (the id field,
which fields are coded, which are free text). A per-corpus table inside a generic generator is the
tool knowing a dataset; a subdirectory, so `source_declarations()`, which globs
`config/source/*.json`, never mistakes a policy for a declaration.

---

## 5. The log lines

### Boot phases

`ScheduleRegistry.run_phase` — the ONE place a schedule runs — reports each body:

```text
[boot] phase=1:load package=ontology name=ontology_load when=new_build status=ok t=12.40s Δrss=310MB
[boot] phase=2:writer package=heart name=wal_maintenance when=every_boot status=ok t=0.00s Δrss=0MB
[boot] phase=2:writer package=workbench name=bench_autorun when=new_build status=error t=0.01s Δrss=0MB detail=RuntimeError: …
[boot] complete phase=2:writer ran=15 failed=1 t=0.42s Δrss=8MB
```

| field | meaning |
|---|---|
| `phase=<n>:<name>` | `1:load`, `2:writer`, `3:post_load` |
| `package` | the package whose manifest declared the body — "whose work is this?" without a grep |
| `name` | the schedule's declared name |
| `when` | `new_build` (its work is expected once per new build; the body is sentinel-gated **inside**) or `every_boot` (it starts a daemon, or does per-boot work). A **label**, not a gate — the registry runs every registered body exactly as before, and the body keeps its own sentinel |
| `status` | `ok` or `error`; an error carries `detail=<ExcType>: <message>` and the phase continues |
| `t`, `Δrss` | the body's wall time and RSS delta (the same reading Health takes; `?` off-Linux) |

The same report is available as DATA on `registry.log`, so a later check reads it instead of
scraping a log. `test/boot_phase_eval.py` holds the shape and that every manifest schedule
declares a valid `when`.

The phase **gates** (`after=ontology.loaded`, which would change *when* a pick runs) are not part
of this mechanism; they belong to seed A with S2-k4.

### Decision lines — a stop names itself, once, where it was decided

The rule (seed-A order §0): every decision point logs ONE line carrying ids; a skip or a refusal
always carries `reason=<id>`; the reason is a **vocabulary id**, and anything explanatory rides in
FIELDS beside it. The platform's own ids are bare (`llm_pool`, `runs_per_day`, `source_ready`); an
id in an application's namespace (`station:reason:*`) is written by that application, on its own
observation, and passed through here untranslated. A guest-visible value has exactly one logged writer.

| line | written by | says |
|---|---|---|
| `[source.bootstrap] declarations found=N runnable=M [ids=…]` | `source.bootstrap:schedule_source_bootstrap` | what the tree declares and what will run, EVERY boot including zero. `found=0` on a tier meant to carry a corpus is a packaging defect; before this line, that cell and a cell with no corpus looked identical |
| `[llm] pool provider=… day=… cap=<calls>/<tokens> from=<env\|default> spent=… reserved=…` | `llm.install_llm_pool_store` | one line per boot: the effective ceiling in force for the provider AND where it came from. `from=default` on a cell whose deploy sets `AKASHA_LLM_*_CALLS_PER_DAY` means the variable never reached this process — the number alone could not say so. `env/default` when the call and token ceilings have different sources |
| `[llm] pool released stale reservations provider=… n=<reserved>` | `llm.install_llm_pool_store` | a reservation belongs to a RUN OF A PROCESS: it is settled at its job's terminal transition, so one still open at boot was left by jobs that no longer exist, and admission would answer against a ceiling that much lower all day (a live cell booted with `reserved=65`). Released before the line above reports the pool, so that number is the pool this process actually has. The SPEND, the refusals and the per-program tallies are untouched — those record what happened. Silent when there was nothing to release |
| `[llm] pool tally EXCEEDS the meter provider=… pool_spent=… metered=… by=[…]` | `llm_pool.pool_view` | the two spend counters disagreeing, at the moment they do. A53's meter counts every call ATTEMPTED (before the request goes out; it is the ceiling); B10's `by[program].spent` counts only the calls that ANSWERED, per workload. The meter is therefore an upper bound on the pool's sum, always — and the day it is not, settle has counted spend no call produced. `settle` is idempotent per reservation ID **on the durable pool record**, not on the passed dict: a reservation re-read from the vault used to settle twice and charge `consumed` again, which is how a workload reported 240 calls on a day the provider metered 21 (D5). An inflated tally dies with its own provider-day |
| `[bench.auto] breaker tripped society=… reason=spent_without_effect runs=K calls=N` | `autorun` (the guard, `wl_state.spent_without_effect`) | a CONTINUOUS workload's last K runs each spent model calls and none produced the declared effect, so it went to manual for real — whatever its duty. A continuous workload otherwise keeps its cadence through its breaker (stopping a broadcaster is the silence the airing ruling forbids); that rule assumes a retry is free. K = 3 unless the declaration sets `on_failure.spent_without_effect`. A run that produced its effect, or spent nothing, ends the streak. The spend is read per job (`wl_state.job_spent`: the reservation's `consumed` before the settle, `api_calls` after — the worker marks DONE a moment before it settles). Re-armed by a new build or config (A35). **It depends on the run's outcome being read correctly** — see `run_outcome` below |
| | **A run's outcome is read from the rows that run wrote.** `station.air.ls` returns the aired Set's members in STORE order (hash order on a real kernel) and trims `limit` after that walk; `wl_state._air_rows` therefore asks for every row of the workload and sorts them by wall clock `at`, once, so "newest last" is a fact for every reader (`run_outcome`, `last_aired_at`, `status().last`). `run_outcome` counts the rows stamped after the run began — not `after − before` over two arbitrary 500-row slices, which counted a real airing as ZERO past 500 rows (the 09-25 incident) — and returns the newest stood-by row's OWN reason, verbatim, or empty |
| | **An application module reads a platform Concept Model through its PUBLIC members only.** `SocietyConcept.society_key(gid, space)` (the society atom, or `""` when none this session can see — never raises) and `SocietyConcept.declared_casts(gid, space)` (the roles a space declares, by id and name — what the gate's `say` step compares) are the reads a station needs; sealing a turn onto the chronon network is the public `chronon.seal` (`ChrononConcept.op_seal`), whose gate every programme client passes as its society's chairman. `ownership_eval` §6 counts every application call of a platform class's underscore method on another object (on a platform instance, or inherited through a platform base) and held it under a RATCHET — 46 at 2026-09-26 AM, 37, then **0** when the application switched to the public names; the bound is now 0. **The base class IS the application's SDK (group 4, 4.16):** `UniversalConcept`'s helpers have public names — `key`, `alias`, `mk`, `mk_replace`, `link`, `add_to_set`, `remove_from_set`, `set_meta`, `meta`, `members`, `collections_for`, `links`, `clock_alias`, `akasha_now`, `now_wall`, `cronon_coord`, `akasha_peek`, `cronon_locate` — and so do `SocietyConcept.resolve_society` / `society_id`, `ChrononConcept.mint`, `WorkflowConcept.mint_deviation` (and the op `wf.deviation`), `WorkbenchConcept.ensure_public_bench`, `VisionEngine.load_image`. The underscore spellings are class ALIASES kept ONE seed; the scan counts them, so the ratchet falls only as the application switches |
| `[registry] refused prefix=<p> to application class=<C> module=<m>` | `concepts/registry.py` | group 4, 4.17: an APPLICATION Concept Model declared a prefix a PLATFORM class owns (`WorkbenchConcept` owns `bench`). It is refused the prefix — `get_class(prefix)` answers with the platform class — and any method the platform defines; its own methods still route by their full name until it declares a prefix of its own (the application's order). `registry.refusals()` lists them with the methods owed. Before this, `bench.new/info/ls/grants/retire` were served by whichever of three application kinds registered LAST by filename |
| `[registry] shared prefix=<p> classes=<C(m)>,… owner=<C> declared=yes|no (last to register) collisions=N` (+ `[registry] shared prefix=<p> method=<m> kept=<A> refused=<B>`) | `concepts/registry.py` `build_active` | 10-02: an APPLICATION prefix two application classes declare (`research`: `ResearchNotebook` and the research bench). Neither may shadow the other's method — the first to register keeps it, the second is refused it by name. `get_class(prefix)` answers with the class that declares `CONCEPT_PRIMARY = True`; with no declaration, the last to register (filename order — a new file can change it), reported `declared=no`. `ownership_eval` (e) ratchets the undeclared ones |
| `[bench.auto] run end society=… status=refused reason=<id> breaker=N (unchanged) — next attempt at <t>` | `autorun` | a run the admission point REFUSED (D11). `wf.advance` returns the refusal as data — `{status: refused, reason: <id>, code, retry_at}`, the id carried in the JSON-RPC error's `data`, never parsed from its message — and moves no cursor (the steps did not run). A reason a clock cures (`is_transient`, e.g. `llm_pool`) leaves the breaker untouched and waits for the moment the refusing party names (`llm_pool.next_day_turn()`); any other id takes the ordinary ladder. Either way the run is recorded stood-by with its id |
| `[llm] pool day turned <d> → <d+1> — headroom re-stated for every key` | `admission.observe_day_turn` (first act of each driver tick) | headroom went false at a refusal and only a reserve, settle or boot set it true again, so a key refused once stayed locked at the gate after the pool refilled (D12). The day turn re-states it for every key, through `admission.reconcile_headroom` — admission is `set:pool:headroom`'s one writer; `provision.reconcile_headroom` is a delegate kept for the boot call |
| `[bench] provision CONFLICT society=… workloads=[…]` | `provision.provision_workloads` | two declarations name ONE society. A society carries one autorun record — one policy, one `retry_at` — so they share a schedule each tick overwrites, and both are due on every tick while both files say hours. Reported, not refused: the pair still provisions (last writer wins, as before) and the line names both keys |
| `[source] readiness reconciled ready=N waiting=N ready_keys=[…] waiting_keys=[…]` | `provision.reconcile_source_ready` | which workloads the gate will admit for `run`, and which are waiting on a pool — by NAME. A count alone cannot say which |
| `[llm] headroom reconciled provider=… room=N tight=N tight_keys=[…]` | `provision.reconcile_headroom` | the same, for the pool's half of step 4 |
| `[society] consent migrated v<N> groups=N public=N open_guest=N public_keys=[…]` | `schedules.schedule_society_consent_migrate` | **the sentinel is versioned with the migration** (`society_consent_v<N>.done`, and it records the keys too). A fixed migration is a different migration: the v1 run landed its sentinel on the live cell with the spaces still not public, and a sentinel cannot say WHICH migration ran — so the corrected one could never run there. The old file is never deleted; it is the record that v1 ran. The repeat is harmless by construction: every key stated is read out of that group's own consent Set, so a second pass over an already-migrated cell states the same facts and changes nothing. The line NAMES the spaces it made public: `public=5` is equally consistent with five other spaces, which is exactly the ambiguity that left a live cell unable to tell "the space is called something else" from "the fact was written and then lost" |
| `[bench] run stood by workload=<gid>/<space> reason=<id>` | `wl_state.note` | a run produced nothing, reported with the reason the OP gave — or `-` when it gave none. This is the whole of what the platform writes about a run's outcome; nothing is stamped anywhere |
| `[bench.auto] not retried society=… reason=<id> (waits for provisioning)` | `autorun.py` | a run produced nothing for a reason no clock fixes. Said once, at the place that decided it; the trigger then waits for the next provisioning pass or boot |
| `[llm] pool refused program=… provider=… reason=<id> need=… free=… committed=… headroom=… cap=… credited=… refused_today=…` | `llm_pool.reserve` | the POOL's arithmetic for a refusal. `reason` is `llm_pool` or `budget_tokens`; **`headroom`** is the calls other CREDITED programmes are owed, held out of this one — that is why a pool can refuse while the cap looks empty. Throttled to one per (provider, programme) per hour |
| `[llm] admission <outcome> program=… provider=… calls=… declared=… free=… cap=…` | `admission._admission_line` | **the one reservation line** — the admission point's own decision, one per scheduled run. `committed` is `cap − free` (the pool logged its own copy of this until step 2, when the second reserver was deleted). `outcome` ∈ `reserved` \| `refused` \| `unmetered`; `unmetered` is a scheduled run that reached admission asking for nothing — the case the pool never hears about, and the one that made an airing gone unmetered look, in the log, like an airing that never happened. `declared=false` means the accounting key fell back to the submitter's label instead of coming from the declaration |
| `[llm] settle program=… status=… reserved=… spent=… returned=…` | `jcl/worker._settle_llm` | the run's real spend, at its TERMINAL transition — DONE, FAILED and CANCELLED alike |
| `[llm] pool reflected provider=… day=… spent=… pool_spent=… reserved=… refused=… runs=…` | `llm.llm_pool_reflect` | the guest-readable pool atom was refreshed. A failure is `[llm] pool reflect FAILED …` at WARNING |
| `[bench] new wb:<name> kind=… world=… by=<hook>` | `workbench._ensure_public_bench` | a public bench came into existence, and which hook asked |
| `[bench] provision capabilities society=… role=… offered=N fp=… retired=N` | `workbench/provision.py` | a role's offered capabilities at this build, and how many older generations were retired |
| `[telemetry.evict] keep_days=… cutoff<… scanned=… dropped=… still_reporting=… truncated=… Δrss=…` | `feed.op_gc` | the retention sweep, including how many members it SPARED because they still report on a kept day |
| `[semantic.search] partial q=<sha8> reason=budget candidates=… t=…s (budget=…s)` | `semantic_ops` | a search cut by the TIME budget. The `cap` cut is silent by design — every large query hits it |
| `[bench.auto] skipped reason=<id> [society=…] detail=…` (also `[hydrate] skipped …`, `[cronon] skipped …`) | `autorun.py` | the driver swallowed an exception and carried on, naming WHICH place as an id from `autorun.SKIP_REASONS`. These were `logger.debug`, invisible at the default level — a driver that had quietly stopped doing something looked exactly like one with nothing to do. NOT throttled: each is an exception on a path that is supposed to work, unlike the budget's cap lines |
| `[bench] provisioned workload=<key> society=… workflow=… trigger=… duty=… effect=… entries=N armed=… problems=N` | `provision.provision_workloads` | one workload reconciled to its declaration, with the five declared fields on the line |
| `[bench] provision failed workload=<key> reason=<id>` | `provision.provision_workloads` | a declaration that could not be provisioned. `reason` is the FIELD id it is missing (`trigger`, `budget`, …) or `template` — the line tells the declaration's author which line to look at |
| `[bench.auto] pick deferred reason=onto_load workload=<key> packs=<p,…> names=<n,…>` | `autorun.bench_autorun_tick` | this workload is held for the load in flight: a changing pack declares a name it declares (`wl:reason:onto_load`). Once per window per workload. The window opens with `[bench.auto] onto_load in flight scope=touched packs=…`; a cell's first load logs `pick deferred reason=onto_load scope=all first_load=1` instead and holds everything until its core is in (`[onto] core ready`); the next tick logs `onto_load in flight scope=touched packs=…` (one line per mode, v1.3). A workload the hold released logs `[bench.auto] released society=<key> from onto_load — due now` and runs on that tick (v1.3.2). A held workload is an action, not a run: nothing is recorded and the breaker is untouched |
| `[boot] gil switch_interval=1.00ms (was 5.00ms)` | `akasha.py` `_log_gil_switch()` — the WRITER only, once it holds the boot lock (10-02 §4; at logging setup every cron-heal probe that deferred wrote it, 412 lines in two days). The interval itself is still set at process entry of every `--daemon` | the writer daemon's GIL switch interval (09-28). The write path releases the GIL tens of times per step (≈26 fsyncs per atom step on the `sync=full` nucleus, the JCL ↔ WriteQueue handoff), and at CPython's 5 ms default it waited up to that long per CPU-bound request thread each time — a 6 ms atom step took ~1.4 s beside four busy threads (283 ms at 1 ms). `AKASHA_GIL_SWITCH_MS` overrides (0.05–50). Held by `test/gil_switch_eval.py` |
| `[boot] gate open name=<gate> released=N` | `api.schedule.open_gate` | a producer finished and released the bodies that declared `after:` it. The ontology load produces TWO: **`ontology.loaded`** (atoms + global relations — opened inside the load the moment the relations are applied; provisioning waits on this one) and **`ontology.normalized`** (the reconcile — opened when the load returns; the name stays, the canon pass it once covered is deleted). Both are also opened in the load's `finally`, however it ended |
| `[onto] atoms packs=N unchanged=N refused=N changed=N jobs=N t= Δrss=` | `ontology.loader` | the atom phase. **A file's key is its CONTENT** — `loader.content_key`: sha256 of the file with blank lines and `#` comment lines removed, computed once per boot per file (cached on `(path, mtime_ns, size)` — the stat is only the lookup, never the key). A pack's sentinel is the hash of `basename:content_key` over its files, so a comment edit or a fresh extraction (every mtime new) is `unchanged`. Sentinels are content-keyed only: a sentinel under any older key (`basename:size`, a size-keyed file alias, `_canon_*`) is not read, so the first boot of this build reloads once (the purge order §3). The phase waits on the pack's **own** atom jobs reaching a terminal state; weave jobs are held and submitted after `ontology.loaded` at maintenance class, so one pack's weave never holds the next pack's gate |
| `[onto] core ready packs=N al= ln= set= held_files=N — workloads resume; N pack(s) still to load hold only the workloads that read their names t= Δrss=` | `ontology.loader._core_ready` | a FIRST load with packs beyond the autoload tier: the core is in and its safe relations applied; the driver leaves `scope=all` for the per-name hold. `held_files` = core files left whole to the global phase. Costs one streamed read of the remaining packs' `def`/`al` lines (66,039 names, 7 MB, 22 s over the repo's packs) |
| `[Kernel] Pack '<p>': phase-1 still running after Ns (cap Ns) — its atom jobs continue in the background; sentinel and weave are queued behind them` | `ontology.loader` | the loader's wait on a pack (`PACK_WAIT_FLOOR_S` 1800, `PACK_WAIT_PER_FILE_S` 60) ran out. Not a cut (v1.3): the pack goes on to `load complete … deferred=background`, and `Pack '<p>': background atoms landed — load complete` writes its sentinel after the relations phase (or `atoms still landing at the gate` — the next boot loads only its files not yet in). Replaces `phase-1 timeout — skipping link phase` |
| `[onto] relations files_read=N reparsed=N skipped=N al= ln= set= t= Δrss=` | `ontology.loader` | the global relations phase. `skipped` = the stat fast path matched AND its recorded content key has a done sentinel; `files_read` − `reparsed` = files re-hashed (new stat) whose content was unchanged — a fresh extraction reads every file and re-parses none. **`reparsed=0` is the acceptance number for an unchanged redeploy** |
| `[onto] pack refused pack=<p> rule=<id> entry=<name> at=<file>:<line> need=<what is missing> declared_in=<pack>/canon.json` | `ontology.loader` | a changed pack broke a declared rule; the FIRST offending entry in file / line order. Nothing of the pack is written. The cure is the pack's author's (§3); the platform writes nothing in its place |
| `[onto] reconcile packs=N retired=N t= Δrss=` (+ `Reconcile '<pack>': keys=N retired=N t= Δrss=` per pack) | `ontology.loader` | retirement of what a changed pack dropped. A pack's def-keys are STREAMED from its FILES (`loader.file_def_keys` → `pack_def_key_set`): each def's key is `def_key(name, description)` — the sha256 of the exact hub content `handle_define` writes — so `keys` is the number of atoms the files define, whatever the store's aliases say (D16: the keep-set used to resolve each NAME through the store and kept whatever stale key a redefined name still pointed at). `retire()` removes an alias only while it still points at the key it retires. The phase holds the key set, never the pack — 2.7 MB peak over `vocab` (19,022 defs), the largest pack |
| `[bench] resources reconciled workload=… client=… consumer=N added=N removed=N labos=N frozen_set=yes\|no` | `workbench/provision.reconcile_workload_resources` | one workload's resource lines converged (§5.2/§6.1) and its per-pool labos ensured (§6.4) — at provisioning, at a freeze, at boot |
| `[bench] labo shadow skipped workload=… pool=… registered=<labo,…>` | `workbench/provision._ensure_labos` | a `when: unbound` shadow labo was NOT made for this pool because a registered lab already holds it (3 October decision 2 — registered labs win). Not an error |
| `[Kernel] Pack '<p>' '<file>': file sentinel present but N def(s) not bound to this file's text (e.g. <name>) — reloading the file` | `ontology.loader` (changing packs only) | a file whose per-file sentinel says it ran, but one of its def names does not resolve to that def's content key (or the atom is evicted). The file's relation sentinels are cleared and it is re-run, so a cell an earlier reconcile damaged heals on the next load of the pack (D16) |
| `[env] deployment.env applied N var(s): <applied>` | `akasha.py main` | the launcher applied `env/deployment.env` (setdefault — an exported var wins, so N may be smaller than the file) |
| `[env] refused name=<NAME> — no manifest declares it …` | `akasha.py main` | an `AKASHA_*` variable (exported or in `env/deployment.env`) that no manifest declares. One line per name, then exit 3; `stop` is exempt. Unset it, or — for an application's own variable — declare it in its package manifest's `env` (§4, *The environment*). Held by `test/env_declared_eval.py` |
| `[Silica] open rss_before= after_replay= after_trim= anon= fmap= banks= records= t= store= avail_start= avail_end= swapin_pages= majflt= read_bytes=` | `backends.silica.SilicaStore._open_line` | the store's OPEN, always on (directive 09-27 §3): process RSS before the store existed, after the WAL replay rebuilt the index, and after a gc + `malloc_trim(0)`; the smaps anon / file-map split; the replayed record count. One INFO line per open of the large store (multi-bank, or ≥ 100k records — the shared nucleus); a per-guest cell logs the same fields at DEBUG, untrimmed (`after_trim=-`). `after_replay − rss_before` is what the open costs; `after_replay − after_trim` is what the allocator was holding for nothing. The last five are the WAL REPLAY span's alone (directive 10-03 item 3): the host's MemAvailable at its start and end (`/proc/meminfo`), the host's swap-in pages (`/proc/vmstat pswpin`), this process's major faults (`/proc/self/stat`) and storage bytes read (`/proc/self/io read_bytes`) during it; `-` where /proc cannot say. A slow replay with high `majflt`/`swapin_pages` and a low `avail_start` is memory pressure; high `read_bytes` with neither is a cold page cache |
| `[iam] token signing secret source=<id>` | `IdentityManager.__init__` | where this process's `gbk:`/`akt:` signing key came from — `env` \| `vault` \| `minted` \| `ephemeral`, one line per boot, never the key itself. **`env` is the only one a networked or multi-host deploy should see** (Security Model → post-launch priority #1): anything else means `AKASHA_SECRET` did not reach this process and it is signing with a key of its own |

### The others, unchanged by the layout

`[Health]` (per minute, one line, with each population's count), `[hydrate]` (per accelerator, at
boot, with `assigned=`), `[maint]`, `[NativeLoad] what=… Δrss=…MB` (any single allocation over
100 MB), `[telemetry.evict]` / `[mirror.compact]` `phase=<n> n= Δrss= t=` (the bounded sweeps),
`[scan]`, `[ipc]`, `[compact]`.

### What the operator's shell prints for a stop (10-02 §2)

The CLI renderer (`api/shell/renderer.py`) prints a result whose `status` is not ok — `standby`,
`refused`, `held`, `blocked`, … or any non-ok status carrying `reason`/`detail`/`error` — as ONE
line, `<status> · <reason> · <detail>` (`-` for an empty part), never `✓ <status>`. An op that
stands by therefore needs nothing from the shell: return `{status, reason, detail}` and the operator
sees all three. A concept list (`station.air.ls`, …) prints every field of a row as `key=value`,
`status`/`reason`/`detail`/`error` first, wrapped to the terminal width (`COLUMNS`) up to four
lines, then `+N more` — no value is cut to 20 characters. Held by `test/cli_standby_render_eval.py`.

---

## 6. The enforcement evals

Run with the suite. `authority_eval`, `gate_eval` and `kernel_ratchet_eval` are ASSERTIONS since the purge order (§4.1); the remaining ratchets may only go down. A ratchet is a
declining bound on a known gap, never a claim that the gap is safe.

| eval | holds |
|---|---|
| `test/wiring_eval.py` | one import direction; no forbidden import hidden inside a function; the heart names no application package; routers/binds/hooks wired. **Ratchet:** application modules importing a non-API heart module — schedule seed A ≤ 157, seed B ≤ 59, seed C ≤ 0 |
| `test/manifest_eval.py` | every manifest entry resolves, one owner per method, the generated access table is in sync, no declared path escapes the tree |
| `test/kernel_ratchet_eval.py` | `kernel.py` ≤ 5,000 lines — an ASSERTION (the purge order §4.1 deleted the ratchet below it; `wc -l` semantics), no application family defined in it, 0 `if method ==` |
| `test/authority_eval.py` | provisioning in one module; ASSERTION (§4.1): no platform module but the authority elevates itself — a platform module that must act as the operator asks `lib.akasha.api.authority.elevated(kernel, purpose)`, every purpose a declared row (`ontology.load`, `driver`, `retention.expiry`), an undeclared one refused (`UndeclaredPurpose`); application modules that elevate are listed |
| `test/gate_eval.py` | the id-set table enumerated; ASSERTION (§4.1): 0 permission decision terms (`role ==`, `_pub_nucleus`, `"role:librarian" in`, `in active_scopes`, …) in platform CODE (comments and docstrings are not decisions) outside the gate, the session manager and the store; application modules that still decide are listed |
| `test/deploy_eval.py` | the seed manifest is the union of the packages' declarations; fresh extract, re-extract (data byte-identical, code replaced, retired code pruned), escape refused at build and at extract; the protected-path inventory above |
| `test/application_owed_eval.py` | every extension point platform code asks for (`implementer(…)`, `declared_implementer(…)`, a dispatched `"pipeline.<role>"` — read from the code, not listed) is implemented by EXACTLY one real op; the dive-bearing set, the `letters`/`glossary` reference roles, a pulse surface, the MCP concept tool and the effectful families are declared. It counted the application's owed declarations while they were outstanding (46 → 0); the eval-only stub that filled them is deleted |
| `test/ownership_eval.py` | ownership is location (P5): every manifest declares an owner that matches where it lives; `owner_of` is one rule (fixture paths, and a relocated root); every tracked file resolves to one owner; no `platform_modules` / `MANIFEST.platform.json` / `_OWNED_TREES`. Over whatever application modules exist (vacuous with none): no reach into a platform class's private member, no platform prefix declared, no application method or prefix named by platform code; the CLI table holds no hand-written or owed entry and an op family lists under one group; the registry's sharing rules on built classes |
| `test/boot_phase_eval.py` | the boot phase report, and that every manifest schedule declares `when` |
| `test/onto_redefine_eval.py` | D16 on the REAL loader, both backends (Silica and SQLite, each in its own process): a def name moved to another file with new text binds to the new key both ways, its Set follows it, the reconcile retires the old key only and counts `keys` = the atoms the files define, after the move and after an unrelated reload; a cell the old reconcile damaged heals on the next load; `retire()` keeps a name that points elsewhere |
| `test/cli_standby_render_eval.py` | through `sys.cli_exec`: a stood-by `station.publish` renders ONE line `standby · <reason> · <detail>` (dry=yes before a turn is sealed; the consent stop once one is and consent is withdrawn); `{status: ok}` still renders `✓ ok`; a `bench.air.ls` row prints `reason` first and fits the terminal |
| `test/source_item_status_eval.py` | directive 10-03 item 5: `source.item.status` moves the item's meta, its status Set and every tally in one write (the freeze finds no drift), is idempotent, refuses bad shapes, is gated `record` on the pool (consumer refused, a record row admitted only on its own pool) and is a CLI command — both cell shapes |
| `test/application_api_eval.py` | the purge order P1: `APPLICATION_API.md` is generated from the name table; every name resolves with a contract and none is private; topic modules are lazy; every name an application imports from a non-API platform module today has a replacement (API name, `concepts.model`, a redesigned name, or the no-API list); `concepts.model` and `client.embedded` work on a cell |
| `test/platform_alone_eval.py` | the proof of II (P5): the application root is deleted (the rest copied, with a fresh repository); a fresh cell boots there (genesis, ping, an atom written and read, a society, a source); the CLI and access tables there are exactly the platform's and both generators' `--check` pass; the launcher brings daemon and portal up and `stop` stops both; the platform's ENTIRE suite (`test/*_eval.py`) passes there; and a static scan of platform code (strings in code; comments, docstrings and generated tables excluded) finds 0 application identifiers — ops, op prefixes, concept names and paths DERIVED from the application's manifests, modules and files — and no string naming the application root outside `api/reserved.py`. `--quick` skips the suite |
| `scripts/gen_platform_tree.py` / `PLATFORM_TREE.json` | §4.3: every platform-owned file under the code trees (`lib/`, `api/`, `remote/`, `reproductor/`, `config/`, `scripts/`, `docs/developer/`, `akasha.py`, `spawn.py`) and every test a PLATFORM manifest's `evals` names, with its sha256, and the tree hash. Regenerate in every platform commit; `manifest_eval` fails when it is stale. The application's cut verifies against it |
| `test/data_format_eval.py` | §4.4: a fresh directory stamped; another id or an unstamped store stops kernel and launcher (exit 3) with one line, writing nothing |
| `test/meta_merge_eval.py` | `merge_meta` is one atomic read-merge-write on both backends: N threads × M counter merges exact; two writers of different fields both survive; a stale whole-meta copy reverting an owned field is refused at the write; the composite salience bump keeps a concurrent writer's field |
| `test/owned_fields_eval.py` | engine-owned fields at the store: both backends, every meta-writing primitive, both cell shapes — a non-owner change of a pool member's `status` or a pool's `by_status` is refused with the field and owner; the owner's writes pass; `sum(by_status) == total` after random door writes |
| `test/status_door_eval.py` | the status door by membership: a no-concept, no-status member gets +1 and `changed: true`; the same status is `changed: false`; a non-member is refused `not a member of <pool>`; the door names no item concept |
| `test/env_declared_eval.py` | the purge order §4.5: every `AKASHA_*` name in a platform module's code is declared in a manifest's `env`, and every name the heart declares is read; every row has a known kind and a meaning; the real launcher refuses an undeclared name (exported, and in `env/deployment.env`) with exit 3 and `[env] refused name=`, proceeds on declared names (a family member included), and still runs `stop`; `docs/deployment.md` is current |
| `test/workload_resource_access_eval.py` | the gate rows of directive 2026-10-02 §5 and the resources of §6, on a real provisioned cell: a `telemetry` feed reaches only its own places; `consumer` lines per required pool (read · run, never record) and per member of `set:source:pool:frozen`, added at a freeze with no reboot; per-pool labos through the `workload.labo.*` points, and a `when: unbound` shadow labo only for a pool no registered lab holds (§7b); the live pool tally (no freeze recount); declared bench targets on a registry op and a manifest op (own public bench admitted and guest-readable, any other place and a missing target refused); `system.telemetry`'s reach unchanged |
| `test/concept_space_bench_eval.py` | the concept-space render's access degree is constant as the store grows 40×, zero full scans, within the cold budget — measured with `probe_reset(thread_only=True)` (Silica counts only the calling thread), so background weave threads cannot pollute the window; it proves that by rendering while another thread hammers the store (§6.3) |
| `test/onto_load_scope_eval.py` | a load in flight holds only the workloads whose declared names a changing pack declares (real driver tick, real declarations, real packs); a first load holds everything; each pack is scanned once per load; `pack_declares` reads def / al / set.add only |
| `test/gil_switch_eval.py` | the daemon sets a 1 ms GIL switch interval at entry (override read, out-of-range ignored, portal untouched), logs it, and an fsync-bound thread beside four CPU-bound threads makes ≥ 2× the progress at 1 ms as at 5 ms |
| `test/workbench_run_record_eval.py` | one run row per run, in the workload's own namespace, with its reason — refused, failed, effect keyed elsewhere — and D15: a job that succeeded with no declared effect is `{ok: false, job_ok: true}`, a stood-by run carries the op's reason verbatim, a run with its effect is `{ok: true}`; `workload.status key=<bench>/<slug>` runs through `sys.cli_exec` (09-28) |
| `test/silica_open_line_eval.py` | the store's open line on every boot (fields measured, `records` = the WAL's), none at INFO for a guest cell and no trim there; the diagnosis tracer starts at process entry on the daemon path only, sees the replay, and the kernel's marks keep it |
| `test/console_svc_admin_eval.py` | v1.1: the console's `svc` gate asks about the identity the kernel returned at login (the Genesis admin starts/restarts/stops a unit through the real console handler; a resident is refused) |
| `test/load_time_focus_eval.py` | v1.1: while a load is in flight, `dive`/`r` on a focus not found and an empty `s.ls`/`onto.dump sets` say the ontology is still loading and name `onto.status` (`loader.loading_note`); after it, the ordinary answers |
| `test/set_enumeration_eval.py` | v1.1: members a pack records in the nucleus are counted by `s.ls` (admin and resident tokens), `onto.dump sets` (`<set>` or `collection=`; `set:` retry; no name lists sets), `r` (both stores' sets) and `lens` — fixture project, the real loader (`_fixtures.pack_cell`) |
| `test/first_load_core_eval.py` | v1.3: the real loader on a fixture ontology (`load_all`): the autoload packs load first whatever their REGISTRY position; a first load releases the driver (`first=False`, the deep pack still listed) before the deep pack's atoms are queued, and `wl_state.onto_hold` then holds only a workload reading a deep name or a Set a held core file binds (`relations:core`); the core relations apply then, the file naming a deep name is left whole and bound to the deep DEFINITION by the global phase; a pack past a shortened cap completes in the background (`deferred=background`, weave queued, sentinel written); a restart is all sentinel hits |
| `test/autorun_release_eval.py` | v1.3.2: the REAL driver tick, stand-ins only at its edge (society store, hold answer, source gate, last-effect clock, `society.run`): nothing runs during a first load; the tick after the core is in runs both released workloads, the `daily:` one included though it aired an hour ago (no `fresh` skip, no wait for its slot), not the one a pack in flight holds; the tick after the load ends runs that one; then nothing more. And `derive_bench_tripped` reads past two unreadable societies |
| `test/stdlib_render_eval.py` | v1.3: with `rich` unimportable, `tree <set>` (router → kernel → renderer), a table view, a `format="rich"` tree view and the scatter / list / keyval views render; `rich` is never imported |
| `test/user_pack_eval.py` | v1.1: `ontology/user/<name>/PACK.json` is a pack (`loader.user_packages`): loads on the next boot, `autoload:false` waits for `onto.pack.enable`, no PACK.json is not a pack, a registered name wins |
| `test/workload_bench_place_eval.py` | `workload.status` asks reach on the space and facts on the key (a lab reads a fact term, then `ok`; another client is still `out_of_scope`); `bench_public` / `bench_kind` / `space.kind` / `space.identity` are read; a difference from an existing bench is reported by field id; the client's line follows the bench; the crystallizer writes no scaffold |
| `test/workload_tier_scope_eval.py` | a workload ships only on a tier whose payload carries its pools and models: the lab and its bench directory are withheld on `seeds14` naming each missing requirement, every station ships, `thesaurus09` withholds nothing, one model file or pack.json fewer is named exactly, `set:` never withholds, and the two legacy every-tier loops are gone |
| `test/seed_payload_eval.py` | every `scripts/*.py` a shipped eval names exists AND is in the payload; the manual and the delivery note ship |
| `test/station_stores_boot_eval.py` | a publishing workload's durable stores are a declared schedule; a failing store is `status=error`; every bench creation names its hook; **no function rebinds a module-level import it also calls through** |
| `test/search_budget_partial_eval.py` | both `semantic.search` truncation reasons are reachable, counted apart, and the budget cut logs its reason id |
| `test/workload_grep_eval.py` | the driver, admission, `society.run` and the recorder name no workload and test no kind; the reasons are vocabulary ids, not strings spelled at the call site |
| `test/workload_conformance_eval.py` | the whole scenario on each of the four REAL declarations: fresh store → provisioned line → the Sets → the armed policy → the cycle on its own branch → a guide row in a state → a second boot that is a no-op → a gate that writes a reason id → the derived key and appetite |
| `test/llm_settle_terminal_eval.py` | a prepaid job releases its LLM reservation at EVERY terminal transition — DONE, FAILED, both CANCELLED cascades, and the two paths that never enter the run loop; `settle` releases ONCE; the worker reaches the hook through an attribute it really has |
| `test/llm_admission_line_eval.py` | one `[llm] admission <outcome>` line per scheduled run and none for an ordinary batch job; `unmetered` is reachable, so a run that lost its appetite is distinguishable from a run that never happened |
| `test/workload_allowance_eval.py` | `runs_per_day` is charged at one guarded site for the declared effect only; a day of runs that produced nothing leaves it unchanged and does not block the run that finally does; the cap's two log lines are throttled once per society per window, per kind |
| `test/platform_vocabulary_eval.py` | **the platform names no application.** (1) no platform module imports a user concept — a Concept Model is reached by `api.concept_class`, a hook, or by dispatching its op; (2) every token hit (`station|studio|news|thesaurus|kitchen|cosmos|mobility|birdclef|cma_|bl_real|akashic|reading_room|gallery|field_guide|_legacy_sid`) is on an allow-list **in the eval, never in the code**, with its reason and the seed it is owed in — **and a STALE entry fails too**, because an exemption for something already clean is a claim that is no longer true; (3) seven files asserted clean by name. Comments and docstrings are not scanned: a file may say what it used to be |
| `test/ontology_sentinel_eval.py` | the REAL loader (`AKASHA_PROJECT_DIR` pointed at a small ontology of the eval's own) does only what a content change asks for: an unchanged restart, a comment edit and a fresh extraction submit no atom job and re-parse nothing; one def edit reloads that file only, with no canon pass; reconcile of a 4,000-def pack stays under 16 MB; every phase line carries `t=`/`Δrss=` |
| `test/pack_validation_eval.py` | a pack breaking a rule declared in `canon.json` is refused whole, by name, with the rule and its first offending entry; nothing is written in its place; fixed, it loads on the next boot; `depth` / `except` / `in_set`; a malformed rule is reported and not applied |
| `test/source_bootstrap_unit_eval.py` | the ONE managed unit that imports any declared corpus, driven through every branch on a synthetic declaration — the sentinel earned and not earned, a changed `reset_key`, the wall-clock cap, the skip switches, an unreadable declaration |
| `test/guest_secret_boot_eval.py` | the token-signing secret is resolved at boot, single-threaded, and the request path only reads it; a concurrent first touch mints once, not once per arriving thread; the source id is reported without the key |
