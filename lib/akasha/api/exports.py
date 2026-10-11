"""
THE APPLICATION API'S NAME TABLE — what an application may import, by topic, with its contract.

The order of 3 October (the purge, §1): an application developer writes an archives-equivalent web
application without touching one line of platform code, and imports nothing of the platform but
`lib.akasha.api`. Each topic module (`lib.akasha.api.<topic>`) answers its names from THIS table,
lazily (PEP 562), so the API imports no heart module until a name is used and no import cycle can
form. `docs/platform/SPEC.md` §3 is generated from it (`scripts/gen_application_api.py`, `--check` in
`test/application_api_eval.py`).

An entry is `name: (target, contract)`. `target` is `"<module>:<attribute>"`, or `"=<topic>:<fn>"`
for a name the API itself defines (a public face over an internal). The contract is the promise:
the name keeps its meaning across releases, and a change to it is an API change, noted as one.

What has NO entry has no API. Internals and private state (a leading underscore) are not exported;
the application redesigns around them. Two module families were imported by the application and
deliberately get none:
  - `lib.akasha.canon` — deleted (§3): the Product·Component·Method law is the application's own
    data (`canon.json`), and the relation names are ordinary vocabulary it declares itself.
  - `lib.akasha.concepts._radu_gate` — deleted (§2): it named one account. A bench that is not for
    the public lives in its group (`bench_public: false`), which the scope gate keeps to its members.
"""
from typing import Dict, Tuple

EXPORTS: Dict[str, Dict[str, Tuple[str, str]]] = {
    # ── Concept Models: the bases an application model subclasses, and models reached by prefix ──
    "concepts": {
        "BaseConcept": ("lib.akasha.concepts.base:BaseConcept",
                        "The base every Concept Model subclasses: CONCEPT_PREFIX / CONCEPT_METHODS, "
                        "op_* methods, the session's stores. A model is found by its prefix."),
        "ImportableMixin": ("lib.akasha.concepts.mixins.importable:ImportableMixin",
                            "The Importable contract: a model implementing import_records(records, "
                            "into=, mapping=) is a drop-in target of io.ingest."),
        "ExportableMixin": ("lib.akasha.concepts.mixins.exportable:ExportableMixin",
                            "The lens export adapter: a model that appears as a SOURCE in a lens "
                            "pipeline (the mirror of ImportableMixin)."),
        "ProvenanceMixin": ("lib.akasha.concepts.mixins.provenance:ProvenanceMixin",
                            "Provenance and source-credibility helpers: the latest event-sourced source "
                            "evaluation, effective credibility and independence."),
        "TemporalMixin": ("lib.akasha.concepts.mixins.temporal:TemporalMixin",
                          "Temporal linked-list helpers: time normalisation and an event-sourced, "
                          "insert-sorted temporal list."),
        "VisibilityMixin": ("lib.akasha.concepts.mixins.visibility:VisibilityMixin",
                            "Visibility helpers: hidden / revealed / archived / tombstoned checks by "
                            "transition link."),
        "UniversalConcept": ("lib.akasha.concepts._universal:UniversalConcept",
                             "BaseConcept whose writes go to the shared nucleus (guest-readable), or a "
                             "group engine for space=group:<gid>."),
        "UNIVERSAL": ("lib.akasha.concepts._universal:UNIVERSAL",
                      "The universal scope token a UniversalConcept writes with."),
        "slug": ("lib.akasha.concepts._universal:slug",
                 "A string → the id slug every model uses in aliases (lower, [a-z0-9_])."),
        "WorkbenchConcept": ("lib.akasha.concepts.workbench:WorkbenchConcept",
                             "The bench base: a bench kind subclasses it and declares its kind; the "
                             "bench store, cycles and runs are the base's."),
        "model": ("=concepts:model",
                  "model(session, prefix) → an instance of the Concept Model that declares `prefix` "
                  "(None if none does). The way to use another model without importing it."),
        "model_class": ("=concepts:model_class",
                        "model_class(prefix) → the class declaring `prefix` (None if none) — for a "
                        "static helper or a declared constant."),
        "active_kernel": ("lib.akasha.concepts.workflow:active_kernel",
                          "The running kernel, for a model that must dispatch an op (never import "
                          "the kernel)."),
        "WorldAxis": ("lib.akasha.concepts.world_axis:WorldAxis",
                      "The world axis: commons alias, the clock, env / sync sets, env events."),
        "CHRONON_DEFAULT_SPACE": ("lib.akasha.concepts.chronon:DEFAULT_SPACE",
                                  "The chronon network's default space name."),
        "PERFECTIVE": ("lib.akasha.concepts.chronon:PERFECTIVE",
                       "A sealed chronon's aspect (the past)."),
        "PROSPECTIVE": ("lib.akasha.concepts.chronon:PROSPECTIVE",
                        "A scenario chronon's aspect (the future)."),
        "RESERVED_CONCEPTS": ("=reserved:RESERVED_CONCEPTS",
                              "The concept names the platform's engines reserve — the ONLY concept "
                              "names platform code tests. An application never mints them."),
    },
    # ── the source engine's facts an application reads ──
    "source": {
        "frozen_pools": ("lib.akasha.source.bootstrap:frozen_pools",
                         "frozen_pools(kernel) → the pools in `set:source:pool:frozen`."),
        "source_declarations": ("lib.akasha.source.bootstrap:source_declarations",
                                "source_declarations(kernel=None) → the corpus declarations under the "
                                "declaration root `source`."),
        "FROZEN_POOLS_SET": ("lib.akasha.source.bootstrap:POOL_FROZEN",
                             "The Set the source engine keeps of every frozen, non-empty pool."),
        "ITEM_STATUS": ("lib.akasha.concepts.source:ITEM_STATUS",
                        "The item status vocabulary the door `source.item.status` accepts."),
    },
    # ── engine-owned fields (§1.4) ──
    "fields": {
        "owned": ("lib.akasha.owned_fields:declared",
                  "owned() → every engine-owned meta field: [{owner, field, scope}]. The store "
                  "refuses any other writer of one."),
        "OwnedFieldRefused": ("lib.akasha.owned_fields:OwnedFieldRefused",
                              "Raised (a PermissionError) by a write that changes a field another "
                              "engine owns; the message names the field and its owner."),
    },
    # ── declaration roots (§1.3) ──
    "declarations": {
        "ROOTS": ("=reserved:DECLARATION_ROOTS",
                  "The roots the platform reads declarations from — workloads, profiles, templates, "
                  "packs, pages, source. It reads no file because of an application's name for it."),
        "root": ("=reserved:root",
                 "root(kind) → the absolute directory of a declaration root (KeyError if unknown)."),
    },
    # ── batch jobs (JCL) ──
    "jobs": {
        "Job": ("lib.akasha.jcl.job:JCLJob", "A batch job: ordered steps, a class, an owner."),
        "Step": ("lib.akasha.jcl.job:JCLStep", "One step of a job: method + params."),
        "Worker": ("lib.akasha.jcl.worker:JCLWorker", "The job worker (to read a job's state)."),
        "DONE": ("lib.akasha.jcl.job:DONE", "A job state."),
        "FAILED": ("lib.akasha.jcl.job:FAILED", "A job state."),
        "CANCELLED": ("lib.akasha.jcl.job:CANCELLED", "A job state."),
        "CLASS_BATCH_ATOM": ("lib.akasha.jcl.job:CLASS_BATCH_ATOM", "A job class (atom writes)."),
        "CLASS_LINK": ("lib.akasha.jcl.job:CLASS_LINK", "A job class (link writes)."),
        "CLASS_MAINTENANCE": ("lib.akasha.jcl.job:CLASS_MAINTENANCE", "A job class (maintenance)."),
        "budget_exhausted": ("lib.akasha.jcl.workspace_context:budget_exhausted",
                             "budget_exhausted() → True when the running workspace's wall-clock "
                             "share is spent; a long block yields at that point."),
        "is_blocked": ("=jobs:is_blocked",
                       "is_blocked(method) → True if a batch step may not call `method` (the JCL "
                       "blocklist), so a model can refuse it before submitting."),
    },
    # ── process / memory / lifecycle ──
    "process": {
        "rss_mb": ("lib.akasha.memtrace:_rss_mb", "rss_mb() → this process's RSS in MB, or None."),
        "gc_trim": ("lib.akasha.memtrace:gc_trim",
                    "gc_trim() → gc.collect + malloc_trim: return freed heap after a big transient."),
        "native_load": ("lib.akasha.memtrace:native_load",
                        "native_load(name, min_delta_mb=1) — a context manager that logs `[NativeLoad] "
                        "what=… Δrss=…` around a native allocation expected > 100 MB (R6)."),
        "is_shutting_down": ("lib.akasha.lifecycle:is_shutting_down",
                             "is_shutting_down() → True once graceful shutdown began; a loop returns."),
        "list_units": ("lib.harmonia.supervisor:list_units",
                       "list_units(base_dir) → the supervisor's units (id, kind, pid, state)."),
        "active_store": ("lib.akasha.storage:active_store",
                         "active_store() → the cell's store facts (backend, durable, paths)."),
        "load_secrets": ("lib.akasha.secrets:load_into_env",
                         "load_secrets(base_dir) → read the cell's secrets file into the environment; returns "
                         "how many were set."),
        "artifact_id": ("lib.akasha.artifact_epoch:artifact_id",
                        "artifact_id(universe_epoch, scope, coordinate, inputs, transform, projection='', "
                        "access_context='') → the stable id of a derived artefact."),
        "is_stale": ("lib.akasha.artifact_epoch:is_stale",
                     "is_stale(built_at_epoch, inputs_epoch) → True if a derived artefact predates its "
                     "inputs' epoch."),
    },
    # ── vision (image → labels / features) ──
    "vision": {
        "VisionEngine": ("lib.akasha.source.vision:VisionEngine",
                         "Image → classification labels / features via the LiteRT backend ladder."),
        "MODEL_FILE": ("lib.akasha.source.vision:_MODEL_FILE",
                       "The bundled classifier's file name (for a readiness probe)."),
        "resolve_backend": ("lib.akasha.source.vision:_resolve_backend",
                            "resolve_backend(allow_install=True) → the usable LiteRT backend, or "
                            "None; allow_install=False never installs (observe time)."),
    },
    # ── LLM providers ──
    "llm": {
        "DEFAULT_MODELS": ("lib.akasha.workbench.llm_provider:DEFAULT_MODELS",
                           "Provider → its default model id."),
        "active": ("lib.akasha.workbench.llm_provider:active",
                   "active(kernel=None) → the provider in use."),
        "available": ("lib.akasha.workbench.llm_provider:available",
                      "available(provider) → True if the provider's credentials are present."),
        "generate": ("lib.akasha.workbench.llm_provider:generate",
                     "generate(provider, model, system, user, timeout=60.0) → the provider's text."),
        "quota": ("lib.akasha.workbench.llm_provider:quota",
                  "quota(provider) → its remaining day budget."),
        "backoff_seconds": ("lib.akasha.workbench.llm_provider:backoff_seconds",
                            "backoff_seconds(provider) → the provider's retry delay after a refusal."),
    },
    # ── declared workloads (read side) ──
    "workloads": {
        "declarations": ("lib.akasha.workbench.workload:declarations",
                         "declarations(kernel) → the workload declarations under the root "
                         "`workloads`, as read by the platform."),
        "key": ("lib.akasha.workbench.workload:key", "key(decl) → the workload's key."),
        "problems": ("lib.akasha.workbench.workload:problems",
                     "problems(decl) → the field names a declaration gets wrong ([] = valid)."),
        "duty": ("lib.akasha.workbench.workload:duty", "duty(decl) → its declared duty id."),
        "bench_slug": ("lib.akasha.workbench.workload:bench_slug", "bench_slug(decl) → its bench."),
        "branch_of": ("lib.akasha.workbench.workload:branch_of",
                      "branch_of(decl) → its workflow branch."),
        "society_of": ("lib.akasha.workbench.workload:society_of",
                       "society_of(decl) → (gid, name) of its society."),
        "plan": ("lib.akasha.workbench.workload_provision:plan",
                 "plan(decl) → the provisioning plan as [(op, label, params)] (nothing written)."),
        "provision": ("lib.akasha.workbench.workload_provision:provision",
                      "provision(dispatch, decl, note=None, kernel_session=None) → reconcile one "
                      "declaration through `dispatch` (the installer's); returns its report."),
        "template_path": ("lib.akasha.workbench.workload_provision:template_path",
                          "template_path(decl) → the template file under the root `templates`."),
    },
    # ── graph helpers ──
    "graph": {
        "GraphQueryEngine": ("lib.akasha.graph.query:GraphQueryEngine",
                             "GraphQueryEngine(cortex, visible_fn=None, meta_fn=None, content_fn=None) — a "
                             "bounded query over a graph (paths, neighbourhoods)."),
        "discover_atoms": ("lib.akasha.discovery:discover_atoms",
                           "discover_atoms(ctx, nucleus, group_engines, scopes, *, ns, set_filt, "
                           "atom_type, pat, limit=50) → atoms matching, scope-filtered."),
        "paginate": ("lib.akasha.pagination:paginate",
                     "paginate(items, limit=None, cursor=None, *, default=20, max_limit=None) → "
                     "(window, page) — the one cursor shape."),
        "KnowledgeCapsule": ("lib.akasha.capsule:KnowledgeCapsule",
                             "KnowledgeCapsule(session) — a self-contained bundle of atoms + links for "
                             "export/import."),
    },
    # ── learned heads (small trainable models over embeddings) ──
    "learned": {
        "KINDS": ("lib.akasha.concepts.learned_head:KINDS", "The head kinds."),
        "fit": ("lib.akasha.concepts.learned_head:fit", "fit(X, y, kind='logreg', seed=0) → a trained head."),
        "predict": ("lib.akasha.concepts.learned_head:predict", "predict(head, vec) → (label, probability)."),
        "predict_batch": ("lib.akasha.concepts.learned_head:predict_batch",
                          "predict_batch(head, X) → labels."),
        "metrics": ("lib.akasha.concepts.learned_head:metrics",
                    "metrics(y_true, y_pred, classes) → the evaluation metrics."),
        "save": ("lib.akasha.concepts.learned_head:save", "save(head, path) → (path, bytes) — persist."),
        "load": ("lib.akasha.concepts.learned_head:load", "load(path) → a head, or None."),
    },
    # ── files (the allow-listed disk layer) ──
    "files": {
        "FileIO": ("lib.harmonia.fileio:FileIO",
                   "The single disk-I/O layer: read/parse, serialise/write CSV/JSON/MD/TXT under "
                   "the allow-listed roots."),
    },
    # ── a client of a running cell (scripts, importers, labs) ──
    "client": {
        "connect": ("api.portals.cell_ipc:SocketGateway",
                    "connect(base_dir, timeout=…) → a gateway to the running cell over its local "
                    "socket; `.dispatch(payload)` → the JSON-RPC response."),
        "ping": ("api.portals.cell_ipc:ping", "ping(base_dir) → True if a cell answers."),
        "embedded": ("=client:embedded",
                     "embedded(base_dir, series='seeds', load_ontology=True) → a gateway over an "
                     "in-process cell, for an offline script or an eval (never beside a running "
                     "writer); `.kernel_client` is the in-process dispatcher."),
        "Environment": ("api.env_detector:Symbiosis",
                        "Symbiosis — the host environment probe (platform, NLP, optional packages)."),
    },
}


def target_of(topic: str, name: str) -> Tuple[str, str]:
    """(module, attribute) a name resolves to. `=<topic>:<fn>` is the API's own definition."""
    tgt = EXPORTS[topic][name][0]
    if tgt.startswith("="):
        mod, attr = tgt[1:].split(":", 1)
        return "lib.akasha.api." + mod, attr
    mod, attr = tgt.split(":", 1)
    return mod, attr


def resolve(topic: str, name: str):
    """The object a name stands for (imports its owner module on first use)."""
    import importlib
    mod, attr = target_of(topic, name)
    return getattr(importlib.import_module(mod), attr)


def bind(module_name: str, topic: str):
    """(__getattr__, __dir__) for a topic module — PEP 562 lazy names."""
    import sys

    def __getattr__(name):
        if name in EXPORTS[topic]:
            obj = resolve(topic, name)
            setattr(sys.modules[module_name], name, obj)
            return obj
        raise AttributeError("lib.akasha.api.%s has no name %r — it is not part of the Application "
                             "API (see docs/platform/SPEC.md §3)" % (topic, name))

    def __dir__():
        return sorted(set(EXPORTS[topic]) | set(vars(sys.modules[module_name])))
    return __getattr__, __dir__
