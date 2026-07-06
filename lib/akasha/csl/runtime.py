"""
CSL Runtime.

Executes a list of CompiledCall objects against the Akasha kernel / session.
Resolves variable references ({"__ref__": "$name"}) from previously stored
results and dispatches each method call through the ConceptRegistry or
directly to the session.
"""
from __future__ import annotations

import logging
import os
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .compiler import CompiledCall

logger = logging.getLogger("Akasha.CSL.Runtime")


# ---------------------------------------------------------------------------
# ExecutionResult
# ---------------------------------------------------------------------------

@dataclass
class ExecutionResult:
    method: str
    params: Dict[str, Any]
    result: Any
    error: Optional[str]
    assigns_to: Optional[str]
    source_line: int


# ---------------------------------------------------------------------------
# Registry helper (lazy, best-effort)
# ---------------------------------------------------------------------------

_REGISTRY_CACHE: Optional[Any] = None
_REGISTRY_LOCK  = __import__("threading").Lock()


def _get_registry(discover_path: Optional[str] = None):
    """
    Load and return a ConceptRegistry instance, or None if unavailable.
    Module-level singleton — built once and reused across all CslRuntime instances.
    """
    global _REGISTRY_CACHE
    if _REGISTRY_CACHE is not None:
        return _REGISTRY_CACHE
    with _REGISTRY_LOCK:
        if _REGISTRY_CACHE is not None:
            return _REGISTRY_CACHE
        try:
            _csl_dir    = os.path.dirname(__file__)
            _akasha_dir = os.path.dirname(_csl_dir)
            _lib_dir    = os.path.dirname(_akasha_dir)
            _root_dir   = os.path.dirname(_lib_dir)
            if _root_dir not in sys.path:
                sys.path.insert(0, _root_dir)

            from lib.akasha.concepts.registry import ConceptRegistry
            reg = ConceptRegistry()
            concepts_dir = discover_path or os.path.join(_akasha_dir, "concepts")
            reg.discover(concepts_dir, module_prefix="lib.akasha.concepts")
            _REGISTRY_CACHE = reg
            return reg
        except Exception as exc:
            logger.warning("CSL runtime: could not load ConceptRegistry: %s", exc)
            return None


# ---------------------------------------------------------------------------
# CslRuntime
# ---------------------------------------------------------------------------

class CslRuntime:
    """
    Execute a compiled CSL script against a session.

    Parameters
    ----------
    session : Any
        An Akasha session object (same type used by KernelDispatcher).
        May be None when running in a test/offline context — in that case
        only ConceptRegistry dispatch is attempted.
    """

    def __init__(self, session: Any, dispatcher: Any = None) -> None:
        self.session    = session
        # Optional kernel dispatcher: allows CSL to call kernel-level methods
        # (define, link.create, set.add, …) when running inside _handle_csl.
        self._dispatcher = dispatcher
        self._vars: Dict[str, Any] = {}
        self._registry = _get_registry()

    # ── Public interface ──────────────────────────────────────────────────

    def run(self, calls: List[CompiledCall]) -> List[ExecutionResult]:
        """Execute all compiled calls in order, accumulating results."""
        results: List[ExecutionResult] = []
        for call in calls:
            result = self.run_one(call)
            results.append(result)
            if result.error:
                # Non-fatal: log and continue
                logger.warning(
                    "CSL: error in %s (line %d): %s",
                    call.method, call.source_line, result.error,
                )
        return results

    def run_one(self, call: CompiledCall) -> ExecutionResult:
        """Execute a single CompiledCall and return its ExecutionResult."""
        # Resolve any __ref__ placeholders in params
        resolved_params = {
            k: self._resolve(v) for k, v in call.params.items()
        }

        try:
            raw = self._dispatch(call.method, resolved_params)
            # Store result for variable references
            if call.assigns_to:
                self._vars[call.assigns_to] = raw

            return ExecutionResult(
                method=call.method,
                params=resolved_params,
                result=raw,
                error=None,
                assigns_to=call.assigns_to,
                source_line=call.source_line,
            )
        except Exception as exc:
            return ExecutionResult(
                method=call.method,
                params=resolved_params,
                result=None,
                error=str(exc),
                assigns_to=call.assigns_to,
                source_line=call.source_line,
            )

    # ── Reference resolution ──────────────────────────────────────────────

    def _resolve(self, value: Any) -> Any:
        """Recursively resolve __ref__ placeholders from self._vars."""
        if isinstance(value, dict) and "__ref__" in value:
            ref = value["__ref__"]
            if ref.startswith("$"):
                ref = ref[1:]
            if "." in ref:
                var, field_name = ref.split(".", 1)
                stored = self._vars.get(var)
                if isinstance(stored, dict):
                    val = stored.get(field_name)
                    if val is None:
                        logger.warning(
                            "CSL: field '%s' not found in $%s (available: %s)",
                            field_name, var, list(stored.keys()),
                        )
                    return val
                logger.warning(
                    "CSL: $%s.%s — $%s is not a dict (got %s)",
                    var, field_name, var, type(stored).__name__,
                )
                return None
            return self._vars.get(ref)

        if isinstance(value, list):
            return [self._resolve(v) for v in value]

        if isinstance(value, dict):
            return {k: self._resolve(v) for k, v in value.items()}

        return value

    # ── Method dispatch ───────────────────────────────────────────────────

    def _dispatch(self, method: str, params: Dict[str, Any]) -> Any:
        """
        Dispatch a method call and return the bare result value.

        Dispatch priority:
          1. ConceptRegistry (if available and handles the method)
          2. KernelDispatcher via session (if session is a KernelDispatcher)
          3. Direct call on session object (fallback)
          4. Raise RuntimeError
        """
        # 1. Try ConceptRegistry
        if self._registry is not None and self._registry.can_handle(method):
            rid = "_csl_"
            response = self._registry.dispatch(method, self.session, params, rid)
            return self._unwrap_response(method, response)

        # 2. Try KernelDispatcher dispatch.
        # Prefer session.dispatch (session is itself a dispatcher), then fall
        # back to the optional dispatcher injected at construction time (e.g.
        # when CslRuntime is created inside _handle_csl with the kernel as
        # dispatcher so that define / link.create / set.add can reach the kernel).
        _disp = None
        if self.session is not None and hasattr(self.session, "dispatch"):
            _disp = self.session
        elif self._dispatcher is not None and hasattr(self._dispatcher, "dispatch"):
            _disp = self._dispatcher

        if _disp is not None:
            import uuid
            rid = str(uuid.uuid4())
            # _skip_history: suppress ctx.stream() inside _authenticated_dispatch.
            # History context ($0, $N) is never needed for batch CSL/JCL writes;
            # skipping the DB fetch eliminates one SELECT per command during boot load.
            payload = {
                "jsonrpc": "2.0",
                "method": method,
                "params": {
                    "data": {**params, "_skip_history": True},
                    # PersistentSession uses client_id as its identity token
                    "session_token": (
                        getattr(self.session, "token", None)
                        or getattr(self.session, "client_id", None)
                    ),
                    "client_id": getattr(self.session, "client_id", None),
                },
                "id": rid,
            }
            response = _disp.dispatch(payload)
            return self._unwrap_response(method, response)

        # 3. Try calling method directly on session (duck-typed fallback)
        if self.session is not None:
            method_parts = method.replace(".", "_")
            fn = getattr(self.session, method_parts, None)
            if fn is not None and callable(fn):
                return fn(**params)

        raise RuntimeError(
            f"No handler found for method '{method}' — "
            "ConceptRegistry does not handle it and no kernel session is available"
        )

    @staticmethod
    def _unwrap_response(method: str, response: dict) -> Any:
        """
        Extract the bare result from a JSON-RPC 2.0 response dict.
        Raises RuntimeError if the response contains an error.
        """
        if not isinstance(response, dict):
            return response

        if "error" in response:
            err = response["error"]
            if isinstance(err, dict):
                msg = err.get("message", str(err))
            else:
                msg = str(err)
            raise RuntimeError(f"{method}: {msg}")

        return response.get("result")
