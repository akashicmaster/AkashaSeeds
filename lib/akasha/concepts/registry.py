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


def _filter_params(op: Callable, data: Dict[str, Any]) -> Dict[str, Any]:
    """Return only the kwargs accepted by op's signature."""
    try:
        sig = inspect.signature(op)
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
            Maps method suffix → op name string, or spec dict with keys:
              op:     str               op method name on the class
              coerce: Callable | None   maps raw data dict → kwargs

    Discovery: call discover(concepts_dir) once at startup.  Any Python file
    in that directory whose top-level class defines both CONCEPT_PREFIX and
    CONCEPT_METHODS is registered automatically.
    """

    def __init__(self) -> None:
        self._handlers:         Dict[str, Tuple[type, str, Optional[Callable]]] = {}
        # Auto-derived tables — populated when CONCEPT_METHODS specs include
        # "action", "args", and "desc" keys.
        self._method_actions:   Dict[str, str]  = {}   # method → IAM action
        self._command_specs:    Dict[str, dict] = {}   # CLI cmd → {method, args, desc}
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

        for suffix, spec in cls.CONCEPT_METHODS.items():
            full = f"{prefix}.{suffix}"
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

            self._handlers[full] = (cls, op_name, coerce)
            logger.debug("ConceptRegistry: %s → %s.%s", full, cls.__name__, op_name)

            # Populate auto-derived tables when spec is fully annotated
            if action:
                self._method_actions[full] = action
            if desc:
                cmd = cli_key if cli_key else full
                self._command_specs[cmd] = {"method": full, "args": args, "desc": desc}

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
                if (obj.__module__ == mod_path
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

    def get_concept_labels(self) -> Dict[str, str]:
        """Return auto-derived prefix→label mapping (from CONCEPT_LABEL)."""
        return dict(self._concept_labels)

    def get_concept_prefixes(self) -> Dict[str, str]:
        """Return auto-derived 'prefix.'→'prefix' mapping for all registered models."""
        return dict(self._concept_prefixes)

    def get_class(self, prefix: str) -> Optional[type]:
        """Return the plugin class for a given CONCEPT_PREFIX, or None."""
        for cls, _op, _coerce in self._handlers.values():
            if cls.CONCEPT_PREFIX == prefix:
                return cls
        return None

    # ── Dispatch ──────────────────────────────────────────────────────────────

    def can_handle(self, method: str) -> bool:
        return method in self._handlers

    def dispatch(self, method: str, session: Any, data: Dict[str, Any], rid: Any) -> dict:
        """Instantiate concept class, call op method, return JSON-RPC response dict."""
        cls, op_name, coerce = self._handlers[method]
        concept = cls(session)
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
