"""Manifest aggregation — how the heart discovers the application layer without naming it.

Every package (and the heart itself) has a `MANIFEST.json`:

    {"package": "workbench", "version": 1, "depends_on": ["concepts", "source", "ontology"],
     "ops":       {"bench.info": {"fn": "lib.akasha.workbench.bench:op_info", "stage": "post", "access": "read"}},
     "schedules": {"bench_autorun": {"fn": "lib.akasha.workbench.autorun:start", "phase": "writer", "order": 120}},
     "thread_units": [{"name": "svc:feed-poll", "wanted": "…:wanted", "thread_attr": "_feed_poll_thread", "start": "…:start"}],
     "provision": {"benches": {"fn": "lib.akasha.workbench.provision:apply", "order": 10}},
     "hydrate":   {"leaderboard": "lib.akasha.workbench.autorun:leaderboard_hydrate_all", "cronon": null},
     "routers":   {"concept_registry": "lib.akasha.concepts.registry:build_active"},
     "hooks":     {"studio_appetite": "lib.akasha.workbench.station:studio_appetite"},
     "declarations": "config/workbench/workloads/*.json",
     "code_paths": ["lib/akasha/workbench/"], "data_paths": ["data/"],
     "evals": ["test/workbench_*_eval.py"]}

An entry is `"<dotted.module>:<qualname>"`; `qualname` may be `Class.method` (resolved to the
plain function). A name that does not resolve is a boot error naming the entry. `load_manifests`
returns the aggregate: the ops table, the schedule registry, the provision registry, the package
records in dependency order, and the union of code/data paths (what deployment protects/prunes).

`routers` — a package's dynamic dispatchers (the Concept Model registry): each entry is a factory
`fn() → router` built once at aggregation; the heart consults every router in `_route` through the
router protocol only (`dispatch_if_handled(method, session, data, rid)`, `get_method_actions()`,
`get_class(prefix)`) and never names the package. A factory that raises is logged and skipped (the
kernel used to log `ConceptRegistry init failed` and carry on — same contract).
An op entry with an `access` but no `fn` is an ACCESS-ONLY declaration: the package states the
method's IAM action while a router dispatches it. `kernel_methods.py` (the access table the CSL
validator reads without a kernel) is GENERATED from these plus the routers —
`python scripts/gen_kernel_methods.py`.

`owner` — `platform` (the mechanism: nobody but its own order edits it) or `user` (the
application). Ownership itself is ONE rule (the purge order, P5): a file under the application root
(`app/`, `api.reserved.app_root()`) is the application's, every other file is the platform's. The
manifest's `owner` must agree with where it lives.

`binds` — functions the heart calls once with itself at boot, so a package that needs a kernel
handle (a concept that submits its own jobs) receives it without the heart importing the package.

`hooks` — named upward calls (`name → fn(kernel, …)`) a LOWER layer may invoke through
`kernel.api.hooks` when a higher package owns the answer (e.g. a concept asking the workbench for a
studio's declared appetite). A hook nobody declares is simply absent.
"""
import importlib
import logging
import json
import os
from typing import Any, Dict, List, Tuple

from .ops import OpsTable
from .provision import ProvisionRegistry
from .schedule import ScheduleRegistry

MANIFEST_NAME = "MANIFEST.json"

# The keys of an op entry the aggregate itself consumes. Every OTHER key is an attribute the op
# declares about itself and lands in `Aggregate.op_attrs` — read by whoever asks, never by name.
OP_CORE_KEYS = ("fn", "stage", "access")


class Aggregate:
    __slots__ = ("ops", "schedules", "provision", "packages", "code_paths", "data_paths",
                 "hydrate", "hydrate_fns", "sources", "routers", "method_actions", "hooks",
                 "binds", "owners", "op_attrs", "op_package", "hook_lists")

    def __init__(self):
        self.ops = OpsTable()
        self.schedules = ScheduleRegistry()
        self.provision = ProvisionRegistry()
        self.packages: List[Dict[str, Any]] = []
        self.code_paths: List[str] = []
        self.data_paths: List[str] = []
        self.hydrate: List[str] = []              # every accelerator a package declares (names)
        self.hydrate_fns: Dict[str, Any] = {}     # name → regenerator fn(kernel) for those a package owns
        self.sources: List[str] = []
        self.routers: List[Any] = []              # dynamic dispatchers (router protocol), in package order
        self.method_actions: Dict[str, str] = {}  # method → IAM action contributed by the routers
        self.hooks: Dict[str, Any] = {}           # named upward calls: name → fn(kernel, …)
        self.binds: List[Any] = []                # fn(kernel) each package wants called once at boot
        self.owners: Dict[str, str] = {}          # package → "platform" | "user" (§1.7)
                                                           # inside an otherwise user-owned package
        # method → the ATTRIBUTES its op entry declares beyond fn/stage/access (`dive_bearing`,
        # `projection`, `block_branch`, `cli`, …). Access-only entries count: a method a router
        # dispatches is described here by the package that owns it, so the heart can ask "which
        # ops are dive-bearing?" without a list of names of its own (group 4, 4.2/4.7/4.12).
        self.op_attrs: Dict[str, Dict[str, Any]] = {}
        self.op_package: Dict[str, str] = {}      # method → the package whose manifest declares it
        # name → EVERY package's registration of that hook, in package order. `hooks[name]` keeps
        # the last one (a single answer); a question every package may contribute to — "which
        # retention collection does this atom belong to?" — asks them all (`api.hooks_all`).
        self.hook_lists: Dict[str, List[Any]] = {}


class LateBound:
    """A manifest entry called through its module ATTRIBUTE, resolved on every call.

    A hook replaced a function-level `from lib.akasha.workbench import llm_pool` inside the
    caller, and that import re-read the attribute each time — so a module that rebinds one of its
    own functions (the LLM gate's provider entry point, a test double) stayed in effect. Binding
    the function object once at boot would quietly break that late binding, so the hook keeps it."""

    __slots__ = ("ref", "source", "_mod", "_parts")

    def __init__(self, ref: str, source: str = ""):
        self.ref, self.source = ref, source
        mod, _, qual = ref.partition(":")
        self._mod, self._parts = mod, qual.split(".")

    @property
    def __name__(self):
        return self._parts[-1]

    def target(self):
        obj = importlib.import_module(self._mod)
        for part in self._parts:
            obj = getattr(obj, part)
        return getattr(obj, "__func__", obj)

    def __call__(self, *a, **kw):
        return self.target()(*a, **kw)

    def __repr__(self):
        return "<hook %s>" % self.ref


def resolve(ref: str, source: str = ""):
    """`lib.akasha.x.y:Name` or `lib.akasha.x.y:Class.method` → the function object."""
    if ":" not in ref:
        raise ValueError(f"manifest entry {ref!r} ({source}) is not 'module:qualname'")
    mod_name, qual = ref.split(":", 1)
    try:
        mod = importlib.import_module(mod_name)
    except Exception as exc:
        raise ValueError(f"manifest entry {ref!r} ({source}): module import failed: {exc}") from exc
    obj = mod
    for part in qual.split("."):
        try:
            obj = getattr(obj, part)
        except AttributeError:
            raise ValueError(f"manifest entry {ref!r} ({source}) does not resolve ({part!r} missing)")
    if not callable(obj):
        raise ValueError(f"manifest entry {ref!r} ({source}) is not callable")
    return obj


def read_manifest(path: str) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        m = json.load(f)
    if not isinstance(m, dict) or not m.get("package"):
        raise ValueError(f"{path}: not a manifest (no 'package')")
    m["_path"] = path
    return m


def _order_packages(manifests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Dependency order (a package after everything it depends on); a cycle is an error."""
    by_name = {m["package"]: m for m in manifests}
    out: List[Dict[str, Any]] = []
    state: Dict[str, int] = {}

    def visit(name: str, chain: Tuple[str, ...]):
        if state.get(name) == 2:
            return
        if state.get(name) == 1:
            raise ValueError("manifest dependency cycle: " + " -> ".join(chain + (name,)))
        m = by_name.get(name)
        if m is None:
            return                       # a dependency that ships no manifest (e.g. the heart)
        state[name] = 1
        for dep in m.get("depends_on", []) or []:
            visit(dep, chain + (name,))
        state[name] = 2
        out.append(m)

    for m in manifests:
        visit(m["package"], ())
    return out


def load_manifests(paths: List[str]) -> Aggregate:
    """Aggregate the manifests at `paths` (the heart's first, then the packages)."""
    agg = Aggregate()
    manifests = [read_manifest(p) for p in paths]
    # What a PLATFORM manifest declares, an application manifest may not declare again: a name
    # declared on both sides is a BOOT ERROR, by name (the purge order, rulings of 4 October).
    plat_decl: Dict[Tuple[str, str], str] = {}
    for m in manifests:
        if m.get("owner") == "platform":
            for section in ("ops", "schedules", "hooks", "routers"):
                for n in (m.get(section) or {}):
                    plat_decl.setdefault((section, n), m["package"])
            for b in (m.get("binds") or []):
                plat_decl.setdefault(("binds", b), m["package"])
    for m in _order_packages(manifests):
        src = m["_path"]
        agg.packages.append(m)
        agg.sources.append(src)
        _check = m.get("owner") != "platform"

        def _shadow(section, name, _check=_check, _src=src):
            if _check and (section, name) in plat_decl:
                raise ValueError("%s declares %s %r, which the platform manifest of package %r "
                                 "already declares — a name is declared once"
                                 % (os.path.relpath(_src, _root_dir()) if os.path.isabs(_src) else _src,
                                    section, name, plat_decl[(section, name)]))
            return False
        for name, spec in (m.get("ops") or {}).items():
            if _shadow("ops", name):
                continue
            spec = {"fn": spec} if isinstance(spec, str) else dict(spec)
            if spec.get("access"):
                agg.method_actions[name] = spec["access"]
            _attrs = {k: v for k, v in spec.items() if k not in OP_CORE_KEYS}
            if _attrs:
                agg.op_attrs.setdefault(name, {}).update(_attrs)
            agg.op_package.setdefault(name, m["package"])
            if not spec.get("fn"):
                # An ACCESS-ONLY entry: the package declares this method's IAM action but a router
                # (or another layer) dispatches it. It contributes to the access table and nothing else.
                continue
            agg.ops.register(name, resolve(spec["fn"], f"{src} ops.{name}"),
                             stage=spec.get("stage", "post"), access=spec.get("access"),
                             source=f"{m['package']}:{spec['fn']}")
        for name, spec in (m.get("schedules") or {}).items():
            if _shadow("schedules", name):
                continue
            spec = {"fn": spec} if isinstance(spec, str) else dict(spec)
            agg.schedules.register(name, resolve(spec["fn"], f"{src} schedules.{name}"),
                                   phase=spec.get("phase", "writer"), order=int(spec.get("order", 100)),
                                   source=f"{m['package']}:{spec['fn']}",
                                   when=spec.get("when", "every_boot"), package=m["package"],
                                   after=spec.get("after", ""),
                                   provides=spec.get("provides", ""))
        for unit in (m.get("thread_units") or []):
            agg.schedules.register_unit(unit["name"], resolve(unit["wanted"], f"{src} unit {unit['name']}"),
                                        unit["thread_attr"],
                                        resolve(unit["start"], f"{src} unit {unit['name']}"),
                                        order=int(unit.get("order", 100)))
        for name, spec in (m.get("provision") or {}).items():
            spec = {"fn": spec} if isinstance(spec, str) else dict(spec)
            agg.provision.register(name, resolve(spec["fn"], f"{src} provision.{name}"),
                                   order=int(spec.get("order", 100)), source=f"{m['package']}:{spec['fn']}")
        hyd = m.get("hydrate") or []
        for name in (hyd if isinstance(hyd, list) else list(hyd.keys())):
            agg.hydrate.append(name)
            fn = None if isinstance(hyd, list) else hyd[name]
            if fn:
                agg.hydrate_fns[name] = resolve(fn, f"{src} hydrate.{name}")
        for name, spec in (m.get("routers") or {}).items():
            if _shadow("routers", name):
                continue
            fn = spec["fn"] if isinstance(spec, dict) else spec
            factory = resolve(fn, f"{src} routers.{name}")
            try:
                router = factory()
            except Exception as exc:                       # noqa: BLE001 — a boot error, logged, not fatal
                logging.getLogger("Akasha.Kernel").error("%s router %s init failed: %s", m["package"], name, exc)
                continue
            if router is None:
                continue
            agg.routers.append(router)
            for meth, action in (router.get_method_actions() or {}).items():
                agg.method_actions.setdefault(meth, action)   # a manifest `access` already set wins
        owner = m.get("owner")
        if owner not in ("platform", "user"):
            raise ValueError("manifest %s must declare owner: platform | user (got %r)" % (src, owner))
        from . import reserved as _reserved
        if (owner == "user") != _reserved.is_app_path(src):
            raise ValueError("manifest %s declares owner %r but lives %s the application root — "
                             "ownership is where a file lives" % (src, owner,
                                                                  "under" if owner == "platform" else "outside"))
        agg.owners[m["package"]] = owner
        for spec in (m.get("binds") or []):
            if _shadow("binds", spec):
                continue
            agg.binds.append(resolve(spec, f"{src} binds"))
        for name, spec in (m.get("hooks") or {}).items():
            if _shadow("hooks", name):
                continue
            fn = spec["fn"] if isinstance(spec, dict) else spec
            resolve(fn, f"{src} hooks.{name}")          # fail LOUDLY at boot if it does not exist
            agg.hooks[name] = LateBound(fn, f"{src} hooks.{name}")
            agg.hook_lists.setdefault(name, []).append(agg.hooks[name])
        agg.code_paths.extend(m.get("code_paths") or [])
        agg.data_paths.extend(m.get("data_paths") or [])
    from . import set_routers as _set_routers
    _set_routers(agg.routers)          # reachable without a kernel (the CSL validator, the CLI)
    return agg


def owner_of(agg, path: str) -> str:
    """Who owns a file: "user" (the application) when it lives under the application root, else
    "platform". One rule, no list (the purge order, P5). `agg` is accepted for the call shape and
    not consulted."""
    from . import reserved as _reserved
    return "user" if _reserved.is_app_path(path) else "platform"


def default_manifest_paths(lib_akasha_dir: str) -> List[str]:
    """The platform's manifests (the heart's and each platform package's under lib/akasha/), then the
    application's, discovered from the application root only: its manifest (`config/MANIFEST.json`)
    and its pages' (`archives/MANIFEST.json`)."""
    from . import reserved as _reserved
    paths = []
    heart = os.path.join(lib_akasha_dir, MANIFEST_NAME)
    if os.path.exists(heart):
        paths.append(heart)
    for pkg in ("ontology", "source", "concepts", "workbench"):
        p = os.path.join(lib_akasha_dir, pkg, MANIFEST_NAME)
        if os.path.exists(p):
            paths.append(p)
    for p in (_reserved.root("manifest"), os.path.join(_reserved.root("pages"), MANIFEST_NAME)):
        if os.path.exists(p):
            paths.append(p)
    return paths


# ── the declarations, read as DATA (no import) — for processes that do not boot a kernel ─────────
#
# A portal (the ASGI front, the MCP server, the launcher) needs to know what the manifests DECLARE —
# which ops are a reference projection, which read is a pulse surface, which URL prefixes a package
# serves — without importing the application to find out. These read the manifest JSON only, once,
# and never resolve a `fn`. The kernel's aggregate carries the same attributes (`op_attrs`); the two
# are one source because both come from the same files.
_DECLARED: Dict[str, Any] = {}


def _root_dir() -> str:
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def _declared() -> Dict[str, Any]:
    if _DECLARED:
        return _DECLARED
    lib_akasha = os.path.join(_root_dir(), "lib", "akasha")
    attrs: Dict[str, Dict[str, Any]] = {}
    static: Dict[str, str] = {}
    restricted: Dict[str, List[str]] = {}
    effectful: set = set()
    env: Dict[str, Dict[str, Any]] = {}
    for path in default_manifest_paths(lib_akasha):
        try:
            m = read_manifest(path)
        except Exception:
            continue
        for name, spec in (m.get("ops") or {}).items():
            if isinstance(spec, dict):
                a = {k: v for k, v in spec.items() if k not in OP_CORE_KEYS}
                if a:
                    attrs.setdefault(name, {}).update(a)
        base = os.path.dirname(path)
        for mount, rel in (m.get("static") or {}).items():
            if isinstance(mount, str) and mount.startswith("/") and isinstance(rel, str):
                static[mount] = os.path.join(base, rel)
        for fam in (m.get("effectful_families") or []):
            if isinstance(fam, str) and fam and not fam.startswith("_"):
                effectful.add(fam)
        for prefix, clients in (m.get("restricted") or {}).items():
            if isinstance(prefix, str) and prefix.startswith("/") and isinstance(clients, list):
                restricted.setdefault(prefix, [])
                restricted[prefix] += [str(c) for c in clients if str(c) not in restricted[prefix]]
        for name, spec in (m.get("env") or {}).items():
            if isinstance(name, str) and name.startswith(ENV_PREFIX):
                row = dict(spec) if isinstance(spec, dict) else {"means": str(spec)}
                row["package"] = m.get("package")
                env.setdefault(name, row)
    _DECLARED.update({"op_attrs": attrs, "static": static, "effectful_families": effectful,
                      "restricted": restricted, "env": env})
    return _DECLARED


# The environment (the purge order §4.5). Every AKASHA_* variable a process reads is DECLARED — the
# heart's manifest for the platform's, a package's manifest for its own — and is a deployment fact,
# never a behaviour switch. A name with `*` declares a family (one provider's budget). The launcher
# refuses a set AKASHA_* variable no manifest declares, by name.
ENV_PREFIX = "AKASHA_"


def declared_env() -> Dict[str, Dict[str, Any]]:
    """name → {kind, default, means, package} for every variable a manifest declares."""
    return {k: dict(v) for k, v in _declared()["env"].items()}


def env_undeclared(names, declared: Dict[str, Any] = None) -> List[str]:
    """The AKASHA_* names in `names` that no manifest declares (a `*` entry matches a family)."""
    import fnmatch
    decl = declared_env() if declared is None else declared
    fams = [k for k in decl if "*" in k]
    out = []
    for n in names:
        if not str(n).startswith(ENV_PREFIX) or n in decl:
            continue
        if any(fnmatch.fnmatchcase(n, f) for f in fams):
            continue
        out.append(n)
    return sorted(out)


def declared_restricted() -> Dict[str, List[str]]:
    """URL prefix → the client ids that may read it, for every `restricted` map a manifest declares.
    The portal serves such a prefix only to a token of one of those clients (or an admin); nothing
    declared → nothing restricted. The platform names no client and no path of its own here."""
    return {k: list(v) for k, v in _declared()["restricted"].items()}


def declared_op_attrs() -> Dict[str, Dict[str, Any]]:
    """method → the attributes its manifest entry declares (the JSON, no import)."""
    return _declared()["op_attrs"]


def declared_projection(kind: str) -> Dict[str, Any]:
    """method → its `projection[kind]` value, for every op whose manifest entry declares one —
    `reference` (a public letter-page read a portal may cache), `pulse` (a single-concept read the
    pulse tap records, valued by its surface name), `mcp` (the tool an MCP client sees)."""
    out = {}
    for m, a in declared_op_attrs().items():
        proj = a.get("projection")
        if isinstance(proj, dict) and proj.get(kind):
            out[m] = proj[kind]
    return out


def declared_implementer(point: str) -> str:
    """The method whose manifest entry declares it IMPLEMENTS `point` (the JSON, no import) — the
    kernel-less twin of `api.implementer`, for a portal or a module with no kernel in hand."""
    for m, a in sorted(declared_op_attrs().items()):
        val = a.get("implements")
        pts = val if isinstance(val, (list, tuple)) else [val]
        if str(point) in [str(p) for p in pts if p]:
            return m
    return ""


def declared_reference(role: str) -> str:
    """The reference read that plays `role` — `letters` (the A–Z page) or `glossary` (the
    salience-ordered concept list) — as its op declares it in `projection.reference.role`, or ""
    when none does. The portal and the semcache seeding ask this; neither names the op."""
    for m, spec in sorted(declared_projection("reference").items()):
        if isinstance(spec, dict) and spec.get("role") == role:
            return m
    return ""


def declared_effectful_families() -> set:
    """Capability families a package declares WORLD-LEAVING (`effectful_families` in its manifest),
    unioned with the prefix of every op whose entry declares `"effectful": true`. A capability name
    is `<family>:<verb>` and need not be an op name, so a family is declared, not inferred."""
    fams = set(_declared()["effectful_families"])
    for m, a in declared_op_attrs().items():
        if a.get("effectful") and "." in m:
            fams.add(m.split(".", 1)[0])
    return fams


def declared_static() -> Dict[str, str]:
    """URL mount → absolute directory, for every `static` map a manifest declares. A mount whose
    directory is not on this cell is the caller's to skip (with a line)."""
    return dict(_declared()["static"])
