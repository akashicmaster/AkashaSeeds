"""
Concept Model Plugin Registry.

Auto-discovers and dispatches concept model classes that opt in via
CONCEPT_PREFIX and CONCEPT_METHODS class attributes.

Concept model commands are intentionally hidden from the main help system.
Contributors and third parties can add new concept models by dropping a
Python file into lib/akasha/concepts/ — no changes to kernel.py required.
"""

import os
import importlib
import inspect
import logging
from typing import Any, Callable, Dict, Optional, Tuple

logger = logging.getLogger("Akasha.ConceptRegistry")

_PLATFORM_CACHE: Dict[str, Any] = {}


def _platform_facts() -> Dict[str, Any]:
    """{prefixes: the first segment of every op a PLATFORM package's manifest declares}. Read from
    the manifests — data — once per process, so the registry names no prefix of its own."""
    if _PLATFORM_CACHE:
        return _PLATFORM_CACHE
    import json as _json
    lib_akasha = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    prefixes = set()
    for rel in ("MANIFEST.json", "ontology/MANIFEST.json", "source/MANIFEST.json",
                "concepts/MANIFEST.json", "workbench/MANIFEST.json"):
        try:
            m = _json.load(open(os.path.join(lib_akasha, rel), encoding="utf-8"))
        except Exception:
            continue
        if m.get("owner") != "platform":
            continue
        for op in (m.get("ops") or {}):
            if "." in op:
                prefixes.add(op.split(".", 1)[0])
    _PLATFORM_CACHE.update({"prefixes": prefixes})
    return _PLATFORM_CACHE


def is_platform_class(cls: type) -> bool:
    """A concept class is the APPLICATION's when its module is under the application root's package
    (`app.concepts.…`), and the platform's otherwise — the one ownership rule, applied to modules."""
    from lib.akasha.api import reserved as _reserved
    mod = getattr(cls, "__module__", "") or ""
    return not (mod == _reserved.app_package() or mod.startswith(_reserved.app_package() + "."))

_REQUIRED_ATTRS = ("CONCEPT_PREFIX", "CONCEPT_METHODS")

# Module-level active registry — set by kernel.py after discovery.
# router.py reads this lazily so it never imports from lib.akasha.kernel.
_active_registry: "Optional[ConceptRegistry]" = None


def set_active(registry: "ConceptRegistry") -> None:
    """Set the process-wide active registry (called once from kernel.py)."""
    global _active_registry
    _active_registry = registry


def get_active() -> "Optional[ConceptRegistry]":
    """Return the active registry, or None if not yet initialised."""
    return _active_registry


def build_active() -> "ConceptRegistry":
    """Build the process-wide registry ONCE and activate it: discover the concept models under
    lib/akasha/concepts/ (Layer 2) and the instance layer under lib/akasha/session/ (Layer 3), then
    inject it into SpaceConcept / lens so they resolve model plugins without circular imports.
    Declared by concepts/MANIFEST.json `routers` — the heart reaches it through the API (backend layout
    order 2026-09-20); this is the discovery block that used to sit at the top of kernel.py, verbatim.
    Commands in both layers are intentionally hidden from the main help system — see
    docs/concept-model-spec.md."""
    global _active_registry
    if _active_registry is not None:
        return _active_registry
    reg = ConceptRegistry()
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))          # lib/akasha/
    reg.discover(os.path.join(here, "concepts"), module_prefix="lib.akasha.concepts")
    reg.discover(os.path.join(here, "session"), module_prefix="lib.akasha.session")
    # the APPLICATION's Concept Models, discovered from the application root only (P5)
    from lib.akasha.api import reserved as _reserved
    _app_concepts = _reserved.root("concepts")
    if os.path.isdir(_app_concepts):
        reg.discover(_app_concepts, module_prefix=_reserved.app_package() + ".concepts")
    for _sp in reg.shared_prefixes():
        # one line per application prefix two classes declare: who, who owns it, and whether the
        # owner was DECLARED (`CONCEPT_PRIMARY = True`) or is just the last to register
        logger.info("[registry] shared prefix=%s classes=%s owner=%s declared=%s collisions=%d",
                    _sp["prefix"], ",".join(_sp["classes"]), _sp["owner"],
                    "yes" if _sp["declared"] else "no (last to register)", _sp["collisions"])
    # imported here, after discovery, to keep the original import ORDER (space/lens are discovered
    # concept modules themselves; injecting before discovery would change it)
    from lib.akasha.session import space as _space_mod
    _space_mod.set_registry(reg)
    import lib.akasha.concepts.lens as _lens_mod
    _lens_mod.set_registry(reg)
    set_active(reg)
    return reg


def _ok(rid: Any, result: Any) -> dict:
    return {"jsonrpc": "2.0", "result": result, "id": rid}


def _err(rid: Any, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "error": {"code": code, "message": message}, "id": rid}


# ── Zero-boilerplate derivation (issue #50) ─────────────────────────────────────
# A concept op is fully drop-in even when its CONCEPT_METHODS entry carries NO
# cli/args/desc/action annotation: the CLI surface (positional args, help text) and the
# IAM action are DERIVED from the op itself — parameter signature, docstring, and a verb
# convention. An explicit annotation always wins; derivation only fills a missing field.

# Read verbs — curated to operations that never mutate the graph. Anything not matched
# here defaults to "write" (fail-safe: an unknown op requires the higher capability, so a
# write can never be mislabelled as a guest-readable read). Authors override with "action".
_READ_VERBS = frozenset({
    "ls", "list", "get", "show", "view", "find", "search", "read", "reference",
    "explore", "concept", "sum", "stat", "status", "roots", "tree", "children",
    "info", "dump", "scan", "peek", "look", "out", "near", "sim", "profile",
    "summary", "count", "describe", "detail", "inspect", "render", "present",
})


def _derive_action(suffix: str, op_name: str) -> str:
    """The gate ACTION from a verb convention: `read` for a curated non-mutating verb set,
    else `record` (fail-safe).

    The eight actions are the whole vocabulary (one-gate order 2026-09-22 §2b), and a derived
    op is no exception: emitting the old `write` token here produced `unknown_action` at the
    gate, which is a REFUSAL — fail-closed, but for the wrong reason and with a term that names
    nothing an operator can act on. An op that needs a different action than these two declares
    it in its manifest `access`, where it can be read."""
    for base in (suffix, op_name[3:] if op_name.startswith("op_") else op_name):
        head = base.replace(".", "_").split("_", 1)[0].lower()
        if head in _READ_VERBS:
            return "read"
    return "record"


def _derive_positional_args(op: Callable) -> list:
    """Ordered names of the op's REQUIRED (no-default) parameters — the natural
    positional CLI args. Parameters WITH a default stay optional (reachable as key=value,
    passed through by the router). *args/**kwargs are skipped. Mirrors, for a bare entry,
    what an author would hand-write as `args`."""
    try:
        sig = inspect.signature(op)
    except (TypeError, ValueError):
        return []
    out = []
    for name, p in sig.parameters.items():
        if name == "self":
            continue
        if p.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            continue
        if p.default is inspect.Parameter.empty:
            out.append(name)
    return out


def _derive_desc(op: Callable) -> str:
    """One-line help from the op's docstring (first paragraph, whitespace-collapsed).
    Empty when the op has no docstring — the author is nudged to add one, but the command
    is still registered (help simply shows no blurb)."""
    doc = inspect.getdoc(op) or ""
    if not doc:
        return ""
    para = doc.strip().split("\n\n", 1)[0]
    return " ".join(para.split())[:200]


def _filter_params(op: Callable, data: Dict[str, Any]) -> Dict[str, Any]:
    """Return only the kwargs accepted by op's signature.

    If the op declares **kwargs (a VAR_KEYWORD parameter), pass every param
    through — the op sorts them itself (e.g. recipe.food collecting an open set of
    USDA nutrient fields). `data` has already been stripped of framework keys
    (session_token / client_id) upstream, so nothing sensitive leaks into **kwargs.
    """
    try:
        sig = inspect.signature(op)
        if any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()):
            return dict(data)
        valid = set(sig.parameters) - {"self"}
        return {k: v for k, v in data.items() if k in valid}
    except (TypeError, ValueError):
        return dict(data)


class ConceptRegistry:
    """
    Registry for auto-discovered concept model classes.

    Each eligible class must define:
        CONCEPT_PREFIX:  str
            Command prefix, e.g. "fieldnote"
        CONCEPT_METHODS: Dict[str, str | dict]
            Maps method suffix → op name string (bare), or a spec dict with keys:
              op:     str               op method name on the class (required)
              coerce: Callable | None   maps raw data dict → kwargs
              action: str               IAM action ("read"/"write"/"drop") — optional;
                                        derived from a verb convention when omitted
              args:   list[str]         positional CLI arg names — optional; derived
                                        from the op's required parameters when omitted
              desc:   str               help text — optional; derived from the op's
                                        docstring when omitted
              cli:    str               explicit CLI alias — optional; the dotted full
                                        method name (prefix.suffix) is used otherwise

            The bare form `"suffix": "op_name"` is fully drop-in: the CLI command,
            positional args, help text, and IAM action are all derived from the op
            itself (issue #50). Annotate only to override a derived default.

    Discovery: call discover(concepts_dir) once at startup.  Any Python file
    in that directory whose top-level class defines both CONCEPT_PREFIX and
    CONCEPT_METHODS is registered automatically.
    """

    def __init__(self) -> None:
        self._handlers:         Dict[str, Tuple[type, str, Optional[Callable]]] = {}
        # Auto-derived tables — populated for EVERY discovered op. An annotated spec
        # supplies action/args/desc/cli directly; a bare spec has them derived from the
        # op's signature, docstring, and a verb convention (issue #50, zero-boilerplate).
        self._method_actions:   Dict[str, str]  = {}   # method → IAM action
        # method → the PARAM that names the gate's target, for the concepts that declare one.
        # `kernel.dispatch` asks `gate(identity, <action>)` and cannot do better: it knows the
        # method, not what the call is about. Step 3 ("on this target") needs the thing, and the
        # thing is in the params. A concept states which param holds it — `CONCEPT_TARGET_ARG` —
        # and this is where that declaration is read, ONCE, for every op it covers.
        self._method_targets:   Dict[str, str]  = {}   # method → param name holding the target
        self._method_target_attrs: Dict[str, dict] = {}  # method → {target, target_kind, target_required}
        self._command_specs:    Dict[str, dict] = {}   # CLI cmd → {method, args, desc}
        self._command_groups:   Dict[str, str]  = {}   # CLI cmd → concept group (prefix)
        self._concept_labels:   Dict[str, str]  = {}   # prefix → label string
        self._concept_prefixes: Dict[str, str]  = {}   # "prefix." → "prefix"
        # 4.17 — who OWNS each prefix (the class `get_class(prefix)` answers with), and the
        # application classes that were REFUSED a platform prefix: (prefix, class, module, n own
        # methods still routed by their full name). `ownership_eval` (c) counts the latter.
        self._prefix_owner:     Dict[str, type] = {}
        self._prefix_claims:    Dict[str, list] = {}   # prefix → every class that declared it
        self.refused_prefixes:  list = []
        # 10-02 — an APPLICATION prefix two application classes declare (`research`: the notebook
        # and the research bench). Neither may shadow the other's method (`shadow_refusals`), and
        # the owner `get_class(prefix)` answers with is the one that DECLARES `CONCEPT_PRIMARY =
        # True`; with no declaration it is the last to register (filename order) — the behaviour
        # before 10-02, kept until the application declares, and counted by ownership_eval (e).
        self.shadow_refusals:   list = []   # (method, kept class, refused class)

    # ── Registration ──────────────────────────────────────────────────────────

    def register(self, cls: type) -> None:
        """Register a concept class by its CONCEPT_PREFIX and CONCEPT_METHODS."""
        if not all(hasattr(cls, a) for a in _REQUIRED_ATTRS):
            raise TypeError(f"{cls.__name__} missing CONCEPT_PREFIX or CONCEPT_METHODS")
        prefix = cls.CONCEPT_PREFIX
        platform = is_platform_class(cls)
        owner = self._prefix_owner.get(prefix)
        self._prefix_claims.setdefault(prefix, []).append(cls)
        # A prefix is the PLATFORM's when a platform class declares it. (A platform package's
        # manifest ops also name prefixes — `feed.poll`, `analysis.precompute`; those collisions
        # are counted by ownership_eval (c) and resolved by 4.11, which moves the ops.)
        platform_prefix = owner is not None and is_platform_class(owner)
        if not platform and platform_prefix:
            # 4.17 — THE REGISTRY REFUSES A PLATFORM PREFIX TO AN APPLICATION MODULE. The class does
            # not own the prefix (`get_class` never answers with it) and may not register a method
            # the platform defines; the methods only it defines still route by their full name —
            # refusing those would take a running application down — and the line below says how
            # many it owes a prefix of its own.
            self._refuse(cls, prefix)
        elif (not platform and owner is not None and owner is not cls
              and getattr(owner, "__dict__", {}).get("CONCEPT_PRIMARY")
              and not cls.__dict__.get("CONCEPT_PRIMARY")):
            pass                       # a shared application prefix: the declared primary keeps it
        else:
            if platform:
                # the platform arrived after application claimants: it takes the prefix back from
                # EVERY one of them (discovery is by filename, so `bench_*` precede `workbench`)
                for _c in self._prefix_claims.get(prefix, []):
                    if _c is not cls and not is_platform_class(_c):
                        self._refuse(_c, prefix)
            self._prefix_owner[prefix] = cls
            label = getattr(cls, "CONCEPT_LABEL", "")
            if label:
                self._concept_labels[prefix] = label
            self._concept_prefixes[f"{prefix}."] = prefix

        # Register the canonical command surface (no bound namespace) …
        self._register_methods(cls, prefix, namespace=None)

        # … then any namespace-aliased surfaces. A model may expose the SAME ops under a
        # SECOND command prefix bound to a constructor namespace (CONCEPT_NAMESPACES maps
        # command-prefix → constructor namespace). NoteConcept uses this to expose
        # `loom.note.*` = the note ops instantiated with namespace="loom" (an isolated
        # active-note cursor). This is the ONE drop-in path for what used to be a parallel
        # hand-wired kernel handler block — a namespaced surface needs no bespoke wiring.
        for alias_prefix, ns in getattr(cls, "CONCEPT_NAMESPACES", {}).items():
            self._concept_prefixes[f"{alias_prefix}."] = alias_prefix
            if label:
                self._concept_labels[alias_prefix] = label
            self._register_methods(cls, alias_prefix, namespace=ns)

    def _refuse(self, cls: type, prefix: str) -> None:
        if any(p == prefix and c is cls for p, c in self.refused_prefixes):
            return
        self.refused_prefixes.append((prefix, cls))
        logger.warning("[registry] refused prefix=%s to application class=%s module=%s — the "
                       "platform owns it; the platform's methods are its own, and this class's own "
                       "methods route by their full name until it declares its own prefix "
                       "(group 4, 4.17)", prefix, cls.__name__,
                       (getattr(cls, "__module__", "") or "").rsplit(".", 1)[-1])

    def refusals(self) -> list:
        """The application classes refused a platform prefix, each with the methods it still owes a
        prefix of its own (its methods the prefix's owner does not define)."""
        out = []
        for prefix, cls in self.refused_prefixes:
            owner = self._prefix_owner.get(prefix)
            base = set((getattr(owner, "CONCEPT_METHODS", {}) or {})) if owner is not None else set()
            own = sorted(sfx for sfx in (getattr(cls, "CONCEPT_METHODS", {}) or {}) if sfx not in base)
            out.append({"prefix": prefix, "class": cls.__name__,
                        "module": (getattr(cls, "__module__", "") or "").rsplit(".", 1)[-1],
                        "owner": getattr(owner, "__name__", None), "owed_methods": own})
        return out

    def _register_methods(self, cls: type, cmd_prefix: str,
                          namespace: Optional[str]) -> None:
        """Register every CONCEPT_METHODS entry under cmd_prefix, deriving any UN-annotated
        cli/args/desc/action field from the op itself (issue #50, zero-boilerplate). When
        `namespace` is set, it is bound into the handler so dispatch instantiates the concept
        with it (the namespace-aliased surface)."""
        _app = not is_platform_class(cls)
        for suffix, spec in cls.CONCEPT_METHODS.items():
            full = f"{cmd_prefix}.{suffix}"
            _prev = self._handlers.get(full)
            if _app and _prev is not None and is_platform_class(_prev[0]):
                continue                 # 4.17 — an application never shadows a platform method
            if (_app and _prev is not None and _prev[0] is not cls
                    and not is_platform_class(_prev[0])):
                # 10-02 — two application classes sharing a prefix: the first to register a method
                # keeps it; the later one is refused it, by name, instead of silently replacing it.
                self.shadow_refusals.append((full, _prev[0].__name__, cls.__name__))
                logger.warning("[registry] shared prefix=%s method=%s kept=%s refused=%s — two "
                               "application classes define it; give one a prefix of its own",
                               cmd_prefix, full, _prev[0].__name__, cls.__name__)
                continue
            if isinstance(spec, str):
                op_name = spec
                coerce  = None
                action  = None
                args    = []
                desc    = ""
                cli_key = None
            else:
                op_name = spec["op"]
                coerce  = spec.get("coerce")
                action  = spec.get("action")     # "read" | "write" | "drop" | …
                args    = spec.get("args", [])   # positional CLI arg names
                desc    = spec.get("desc", "")   # help text
                cli_key = spec.get("cli")        # optional CLI alias (e.g. "lens" for lens.scan)
            # A cli alias belongs to the canonical surface only; a namespaced surface always
            # uses its dotted full name so `loom.note.new` stays distinct from `n.new`.
            if namespace is not None:
                cli_key = None

            self._handlers[full] = (cls, op_name, coerce, namespace)
            logger.debug("ConceptRegistry: %s → %s.%s (ns=%s)", full, cls.__name__,
                         op_name, namespace)

            # An explicit annotation always wins (only a missing field is derived).
            op_func = getattr(cls, op_name, None)
            if callable(op_func):
                if not args:
                    args = _derive_positional_args(op_func)
                if not desc:
                    desc = _derive_desc(op_func)
            if not action:
                action = _derive_action(suffix, op_name)

            # Every discoverable op gets an IAM action (else the kernel 404s it at the
            # capability gate before it can ever reach registry dispatch) …
            self._method_actions[full] = action
            # … and, where the concept DECLARES which param names the thing it acts on, the
            # second half of the gate's question. Reads are left out on purpose: `sweep.status`
            # and `bench.info` are guest-readable by design, and step 4 already governs what a
            # guest may see. The declaration is per CLASS, not per op, because "what a bench op
            # is about" is a property of the family — no branch anywhere names a method.
            # An op MAY override the family default with its own `target`, and `"target": ""`
            # opts out — which is what an op that CREATES its target needs: asking the gate
            # about a bench `bench.new` is about to mint is the resolution-vs-decision mistake
            # (the op is what makes the thing the question is about), and it refuses every
            # first act. The opt-out is written beside the op, as a declaration, so it can be
            # read and counted; it is never inferred from the method's name here.
            _tgt = spec.get("target") if isinstance(spec, dict) and "target" in spec \
                else getattr(cls, "CONCEPT_TARGET_ARG", "")
            _tgt = str(_tgt or "")
            if _tgt and action != "read":
                self._method_targets[full] = _tgt
                # §6.4 — how the value becomes a place (`target_kind`), and whether a call without
                # it is refused (`target_required`). Data on the spec, read here once.
                if isinstance(spec, dict) and (spec.get("target_kind") or spec.get("target_required")):
                    self._method_target_attrs[full] = {"target": _tgt,
                                                       "target_kind": spec.get("target_kind") or "",
                                                       "target_required": spec.get("target_required") is True}
            # … and a CLI command spec, so it is reachable (canonical / one-shot /
            # subcommand mode) and help-listed. The command key is the explicit `cli`
            # alias when given, else the DOTTED full method name — never a bare word, so
            # a model can never silently reclaim a removed top-level alias.
            cmd = cli_key if cli_key else full
            self._command_specs[cmd] = {"method": full, "args": args, "desc": desc}
            # Record the command's concept group so help can group a CLI alias
            # (e.g. "reference") that does not start with the "prefix." — the
            # router's prefix-startswith grouping cannot infer that on its own.
            self._command_groups[cmd] = cmd_prefix

    def discover(self, concepts_dir: str,
                 module_prefix: str = "lib.akasha.concepts") -> int:
        """
        Scan concepts_dir and register all eligible concept classes.
        module_prefix is used to build the importlib path for each file.
        Returns the count of classes registered.
        """
        count = 0
        try:
            filenames = sorted(os.listdir(concepts_dir))
        except OSError as exc:
            logger.error("ConceptRegistry: cannot scan %s: %s", concepts_dir, exc)
            return 0

        for fname in filenames:
            if not fname.endswith(".py") or fname.startswith("_"):
                continue
            module_name = fname[:-3]
            mod_path = f"{module_prefix}.{module_name}"
            try:
                mod = importlib.import_module(mod_path)
            except ImportError as exc:
                logger.warning("ConceptRegistry: could not import %s: %s", mod_path, exc)
                continue
            for _, obj in inspect.getmembers(mod, inspect.isclass):
                # A concept model must DECLARE its own CONCEPT_PREFIX — an abstract base
                # subclass that merely INHERITS a prefix (e.g. DictionaryConcept /
                # DishFamilyConcept inheriting "formula" from FormulaConcept) is NOT a
                # distinct model and must not register, else it silently shadows the real
                # `formula.*` handlers by scan order. CONCEPT_METHODS may still be inherited.
                if (obj.__module__ == mod_path
                        and "CONCEPT_PREFIX" in obj.__dict__
                        and all(hasattr(obj, a) for a in _REQUIRED_ATTRS)):
                    try:
                        self.register(obj)
                        count += 1
                        logger.info(
                            "ConceptRegistry: registered %s (prefix=%s)",
                            obj.__name__, obj.CONCEPT_PREFIX,
                        )
                    except Exception as exc:
                        logger.warning(
                            "ConceptRegistry: failed to register %s: %s",
                            obj.__name__, exc,
                        )
        return count

    # ── Auto-derived table accessors ──────────────────────────────────────────

    def get_method_actions(self) -> Dict[str, str]:
        """Return auto-derived method→IAM-action mapping (from annotated specs)."""
        return dict(self._method_actions)

    def get_command_specs(self) -> Dict[str, dict]:
        """Return auto-derived CLI command specs (from annotated specs)."""
        return dict(self._command_specs)

    def get_command_groups(self) -> Dict[str, str]:
        """Return auto-derived CLI-command → concept-group mapping (handles CLI aliases
        that do not start with the 'prefix.', e.g. 'reference' → 'thesaurus')."""
        return dict(self._command_groups)

    def get_concept_labels(self) -> Dict[str, str]:
        """Return auto-derived prefix→label mapping (from CONCEPT_LABEL)."""
        return dict(self._concept_labels)

    def get_concept_prefixes(self) -> Dict[str, str]:
        """Return auto-derived 'prefix.'→'prefix' mapping for all registered models."""
        return dict(self._concept_prefixes)

    def shared_prefixes(self) -> list:
        """Application prefixes more than one application class declares: who declares it, who owns
        it (the class `get_class` answers with), and whether that owner was DECLARED primary."""
        out = []
        for prefix, claims in sorted(self._prefix_claims.items()):
            apps = [c for c in claims if not is_platform_class(c)]
            owner = self._prefix_owner.get(prefix)
            if len(apps) < 2 or owner is None or is_platform_class(owner):
                continue
            out.append({"prefix": prefix,
                        "classes": ["%s(%s)" % (c.__name__, (c.__module__ or "").rsplit(".", 1)[-1])
                                    for c in apps],
                        "owner": owner.__name__,
                        "declared": bool(owner.__dict__.get("CONCEPT_PRIMARY")),
                        "collisions": sum(1 for m, *_ in self.shadow_refusals
                                          if m.startswith(prefix + "."))})
        return out

    def get_class(self, prefix: str) -> Optional[type]:
        """Return the class that OWNS `prefix`, or None. With two classes declaring one prefix this
        used to answer with whichever handler came first in iteration order; the owner is now
        explicit, and a platform prefix is only ever owned by the platform (4.17)."""
        return self._prefix_owner.get(prefix)

    # ── Dispatch ──────────────────────────────────────────────────────────────

    def can_handle(self, method: str) -> bool:
        return method in self._handlers

    def dispatch(self, method: str, session: Any, data: Dict[str, Any], rid: Any) -> dict:
        """Instantiate concept class, call op method, return JSON-RPC response dict."""
        cls, op_name, coerce, namespace = self._handlers[method]
        concept = cls(session, namespace=namespace) if namespace else cls(session)
        op = getattr(concept, op_name, None)
        if op is None:
            return _err(rid, -32601, f"Method '{method}' is not implemented")
        try:
            params = coerce(data) if coerce else _filter_params(op, data)
            self._gate_target(method, concept, session, data, params)
            result = op(**params)
            return _ok(rid, result)
        except PermissionError as exc:
            # F3 — a concept op that refuses the caller (e.g. a guest reading member-only data) maps to
            # the standard permission code, so the client tells "not allowed" apart from "not built".
            return _err(rid, -32001, str(exc))
        except RuntimeError as exc:
            return _err(rid, -32002, str(exc))
        except (TypeError, ValueError) as exc:
            return _err(rid, -32602, str(exc))
        except NotImplementedError as exc:
            return _err(rid, -32601, str(exc))
        except Exception as exc:
            logger.exception("ConceptRegistry: unhandled error in %s", method)
            return _err(rid, -32603, str(exc))

    def _gate_target(self, method: str, concept: Any, session: Any,
                     data: Dict[str, Any], params: Dict[str, Any]) -> None:
        """THE SECOND HALF OF THE GATE'S QUESTION — the same function, asked with the target.

        `kernel.dispatch` asks `gate(identity, <action>)`, and its own comment states why that is
        only half: "the boundary asks the ACTION; the op asks again with its target." The boundary
        cannot do better — it knows the method name, not what the call is about. Step 3 ("target ∈
        idset.on") needs the thing, and the thing is a param.

        WHAT WENT WRONG WITHOUT IT. A closed bench refuses a stranger by SCOPE — she cannot
        resolve `scope:wb:<name>`, so the op fails before any permission question — and that is
        why the family looked covered. A PUBLIC bench lives in the nucleus and every identity can
        read it, so its writes are refused by the table or by nothing. With no target in the
        question there is no table answer to give: `record` on one's own cell and `record` on
        someone else's public bench are the same question, and the eighth row (`resident`, which
        every self-registered account holds) answers yes to it.

        The concept declares the param; nothing here knows a method, a bench or a family by name.
        A declared param that is absent or empty asks nothing — an op called without its target
        has a shape problem, which is the op's own error to raise, not a refusal to invent."""
        arg = self._method_targets.get(method)
        if not arg:
            return
        from lib.akasha.api import gate as _gate
        who = getattr(session, "client_id", "") or ""
        action = self._method_actions.get(method, "")
        tattrs = self._method_target_attrs.get(method)
        if tattrs:
            # a declared KIND (or a required target): the platform's resolver, the same one a
            # manifest op's declared target uses (`api.targets`) — so a bench is spelled one way
            from lib.akasha.api import targets as _targets
            from lib.akasha.concepts.workflow import active_kernel as _ak
            merged = dict(data or {})
            merged.update(params or {})
            ok, why, target = _targets.check(_ak(), who, action, tattrs, merged, session)
            if ok:
                return
            _gate.refuse_log(who, action, target, why)
            raise PermissionError("%s: %s %s on %s" % (who, why, action, target))
        raw = params.get(arg, data.get(arg))
        raw = "" if raw is None else str(raw).strip()
        if not raw:
            return
        target = concept.gate_target(raw) if hasattr(concept, "gate_target") else raw
        ok, why = _gate.gate(who, action, target)
        if ok:
            return
        _gate.refuse_log(who, action, target, why)
        raise PermissionError("%s: %s %s on %s" % (who, why, action, target))

    def dispatch_if_handled(
        self,
        method: str,
        session: Any,
        data: Dict[str, Any],
        rid: Any,
    ) -> Optional[dict]:
        """Return dispatch result if the method is registered, else None."""
        if method not in self._handlers:
            return None
        return self.dispatch(method, session, data, rid)
