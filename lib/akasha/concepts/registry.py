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
    """IAM action from a verb convention: read for a curated non-mutating verb set,
    else write (fail-safe). The op's method name and the CLI suffix are both consulted."""
    for base in (suffix, op_name[3:] if op_name.startswith("op_") else op_name):
        head = base.replace(".", "_").split("_", 1)[0].lower()
        if head in _READ_VERBS:
            return "read"
    return "write"


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
        self._command_specs:    Dict[str, dict] = {}   # CLI cmd → {method, args, desc}
        self._command_groups:   Dict[str, str]  = {}   # CLI cmd → concept group (prefix)
        self._concept_labels:   Dict[str, str]  = {}   # prefix → label string
        self._concept_prefixes: Dict[str, str]  = {}   # "prefix." → "prefix"

    # ── Registration ──────────────────────────────────────────────────────────

    def register(self, cls: type) -> None:
        """Register a concept class by its CONCEPT_PREFIX and CONCEPT_METHODS."""
        if not all(hasattr(cls, a) for a in _REQUIRED_ATTRS):
            raise TypeError(f"{cls.__name__} missing CONCEPT_PREFIX or CONCEPT_METHODS")
        prefix = cls.CONCEPT_PREFIX

        # Collect concept-level metadata
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

    def _register_methods(self, cls: type, cmd_prefix: str,
                          namespace: Optional[str]) -> None:
        """Register every CONCEPT_METHODS entry under cmd_prefix, deriving any UN-annotated
        cli/args/desc/action field from the op itself (issue #50, zero-boilerplate). When
        `namespace` is set, it is bound into the handler so dispatch instantiates the concept
        with it (the namespace-aliased surface)."""
        for suffix, spec in cls.CONCEPT_METHODS.items():
            full = f"{cmd_prefix}.{suffix}"
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

    def get_class(self, prefix: str) -> Optional[type]:
        """Return the plugin class for a given CONCEPT_PREFIX, or None."""
        for entry in self._handlers.values():
            if entry[0].CONCEPT_PREFIX == prefix:
                return entry[0]
        return None

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
            result = op(**params)
            return _ok(rid, result)
        except RuntimeError as exc:
            return _err(rid, -32002, str(exc))
        except (TypeError, ValueError) as exc:
            return _err(rid, -32602, str(exc))
        except NotImplementedError as exc:
            return _err(rid, -32601, str(exc))
        except Exception as exc:
            logger.exception("ConceptRegistry: unhandled error in %s", method)
            return _err(rid, -32603, str(exc))

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
