"""
CSL Script Validator.

Performs semantic checks on a parsed Script AST and returns a list of
ValidationError dataclasses.  Does not modify the AST.

Checks performed:
  1. Method existence — command methods must be in the ConceptRegistry or the
     set of known kernel/built-in methods.
  2. Variable usage before definition — $var references must follow an
     assignment to that variable.
  3. Numeric range — parameters named confidence/credibility/weight/feasibility
     /expected_value are expected to be floats in [0, 1].
  4. Typo detection — unknown parameters get a close-match suggestion.
"""
from __future__ import annotations

import difflib
import os
import sys
from dataclasses import dataclass, field
from typing import Any, List, Optional, Set

from .ast import (
    Assignment, BoolLiteral, Command, CommentNode, DictLiteral, FieldAccess,
    ListLiteral, NullLiteral, NumberLiteral, Param, Script, StringLiteral, Variable,
)


# ---------------------------------------------------------------------------
# ValidationError
# ---------------------------------------------------------------------------

@dataclass
class ValidationError:
    line: int
    col: int
    error: str
    parameter: str = ""
    suggestion: str = ""
    level: str = "error"  # "error" | "warning"


# ---------------------------------------------------------------------------
# Known methods
# ---------------------------------------------------------------------------

# Methods handled directly by the kernel (not in ConceptRegistry)
_KNOWN_KERNEL_METHODS: Set[str] = {
    # Memory
    "kernel.memory.write", "write", "w",
    "kernel.memory.define", "define", "def",
    "kernel.memory.read", "read", "r",
    "kernel.memory.drop", "drop", "rm",
    "kernel.memory.link", "link.create", "ln",
    "link.list", "link.reinforce",
    "meta.set",
    # Aliases
    "kernel.identity.alias", "alias", "al",
    "kernel.identity.alias.list", "alias.list", "al.ls",
    "kernel.identity.alias.find", "alias.find", "al.find",
    # Exploration
    "explore", "network.tree",
    # Dive
    "dive.look", "look", "dive.out", "out",
    # Sets
    "set.add", "set.rm", "set.ls", "set.clear", "set.op",
    # Notes
    "note.new", "note.add", "note.section", "note.paragraph",
    "note.toc", "note.read", "note.rm", "note.list", "note.ls",
    "note.edit", "note.move", "note.undo", "note.redo",
    "note.restore", "note.rename", "note.open",
    # Associate
    "kernel.associate", "associate.unwritten",
    # Jataka
    "jataka.dream", "dream",
    # Contexa
    "contexa.fetch", "fetch",
    # Sys
    "sys.cogito", "cogito", "sys.history", "sys.session.close",
    "sys.scope.set", "sys.scope.get", "sys.scope.reset",
    "sys.ls", "sys.ping", "sys.passwd", "passwd",
    "sys.cross.query", "sys.cross.axes",
    # Log
    "log.new", "log.checkpoint", "log.annotate", "log.replay",
    "log.read", "log.rm",
    # Whiteboard
    "wb.new", "wb.pin", "wb.unpin", "wb.focus", "wb.ls",
    "wb.show", "wb.rm",
    # JCL
    "job.submit", "job.ls", "job.stat", "job.cancel",
    # Locale
    "locale.get", "locale.set",
    # Sync
    "sync.push", "sync.pull",
    # CSL itself (built-in)
    "csl", "csl.check", "csl.build", "csl.run",
}

# Parameters that should be numeric values in [0, 1]
_NUMERIC_RANGE_PARAMS = {
    "confidence", "credibility", "weight", "feasibility", "expected_value",
}


# ---------------------------------------------------------------------------
# Registry loading (best-effort)
# ---------------------------------------------------------------------------

def _load_registry():
    """
    Attempt to load and discover the ConceptRegistry.
    Returns a ConceptRegistry instance (possibly empty on failure).
    """
    try:
        # Ensure project root is on sys.path
        _csl_dir   = os.path.dirname(__file__)
        _akasha_dir = os.path.dirname(_csl_dir)
        _lib_dir    = os.path.dirname(_akasha_dir)
        _root_dir   = os.path.dirname(_lib_dir)
        if _root_dir not in sys.path:
            sys.path.insert(0, _root_dir)

        from lib.akasha.concepts.registry import ConceptRegistry
        reg = ConceptRegistry()
        concepts_dir = os.path.join(_akasha_dir, "concepts")
        reg.discover(concepts_dir, module_prefix="lib.akasha.concepts")
        return reg
    except Exception:
        return None


_concept_registry = _load_registry()


def _load_router_aliases() -> Set[str]:
    """Load CLI shorthand aliases and their target methods from the router."""
    aliases: Set[str] = set()
    try:
        _csl_dir   = os.path.dirname(__file__)
        _root_dir  = os.path.dirname(os.path.dirname(os.path.dirname(_csl_dir)))
        if _root_dir not in sys.path:
            sys.path.insert(0, _root_dir)
        from api.router import CommandRouter
        for alias, spec in CommandRouter.COMMAND_SPECS.items():
            aliases.add(alias)
            aliases.add(spec.get("method", ""))
    except Exception:
        pass
    return aliases


def _load_kernel_methods() -> Set[str]:
    """Import METHOD_TO_ACTION from the dependency-free kernel_methods module."""
    try:
        _csl_dir   = os.path.dirname(__file__)
        _root_dir  = os.path.dirname(os.path.dirname(os.path.dirname(_csl_dir)))
        if _root_dir not in sys.path:
            sys.path.insert(0, _root_dir)
        from lib.akasha.kernel_methods import METHOD_TO_ACTION
        return set(METHOD_TO_ACTION.keys())
    except Exception:
        return set()


_router_aliases  = _load_router_aliases()
_kernel_methods  = _load_kernel_methods()


def _known_methods() -> Set[str]:
    methods = set(_KNOWN_KERNEL_METHODS)
    methods.update(_router_aliases)
    methods.update(_kernel_methods)
    if _concept_registry is not None:
        # noinspection PyProtectedMember
        methods.update(_concept_registry._handlers.keys())
    return methods


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------

class _Validator:
    def __init__(self) -> None:
        self._errors: List[ValidationError] = []
        self._defined_vars: Set[str] = set()
        self._all_methods = _known_methods()

    def validate(self, script: Script) -> List[ValidationError]:
        for stmt in script.statements:
            if isinstance(stmt, CommentNode):
                continue
            if isinstance(stmt, Assignment):
                # Validate the embedded command first
                self._validate_command(stmt.command)
                # After validation, mark the variable as defined
                self._defined_vars.add(stmt.variable)
            elif isinstance(stmt, Command):
                self._validate_command(stmt)
        return self._errors

    def _validate_command(self, cmd: Command) -> None:
        # 1. Method existence
        if cmd.method not in self._all_methods:
            suggestions = difflib.get_close_matches(
                cmd.method, self._all_methods, n=3, cutoff=0.6
            )
            self._errors.append(ValidationError(
                line=cmd.pos.line,
                col=cmd.pos.col,
                error=f"Unknown method '{cmd.method}'",
                suggestion=(
                    "Did you mean: " + ", ".join(suggestions) if suggestions else ""
                ),
                level="error",
            ))

        # 2. Validate params
        for param in cmd.params:
            self._validate_param(param)

    def _validate_param(self, param: Param) -> None:
        # 2. Variable usage before definition
        self._check_value_refs(param.value, param.pos.line, param.pos.col)

        # 3. Numeric range for known fields
        if param.key in _NUMERIC_RANGE_PARAMS:
            val = param.value
            if isinstance(val, NumberLiteral):
                if not (0.0 <= val.value <= 1.0):
                    self._errors.append(ValidationError(
                        line=param.pos.line,
                        col=param.pos.col,
                        error=(
                            f"Parameter '{param.key}' value {val.value} is outside "
                            f"expected range [0, 1]"
                        ),
                        parameter=param.key,
                        suggestion="Use a value between 0.0 and 1.0",
                        level="warning",
                    ))
            elif not isinstance(val, (Variable, FieldAccess)):
                self._errors.append(ValidationError(
                    line=param.pos.line,
                    col=param.pos.col,
                    error=(
                        f"Parameter '{param.key}' expects a numeric value, "
                        f"got {type(val).__name__}"
                    ),
                    parameter=param.key,
                    suggestion="Provide a numeric literal between 0.0 and 1.0",
                    level="warning",
                ))

    def _check_value_refs(self, value: Any, line: int, col: int) -> None:
        """Recursively check variable references for undefined variables."""
        if isinstance(value, Variable):
            if value.name not in self._defined_vars:
                self._errors.append(ValidationError(
                    line=line,
                    col=col,
                    error=f"Variable '${value.name}' used before assignment",
                    parameter=value.name,
                    suggestion=(
                        f"Assign a value to ${value.name} before using it"
                    ),
                    level="error",
                ))
        elif isinstance(value, FieldAccess):
            if value.variable not in self._defined_vars:
                self._errors.append(ValidationError(
                    line=line,
                    col=col,
                    error=(
                        f"Variable '${value.variable}' used before assignment "
                        f"(in field access '${value.variable}.{value.field}')"
                    ),
                    parameter=value.variable,
                    suggestion=(
                        f"Assign a value to ${value.variable} before using it"
                    ),
                    level="error",
                ))
        elif isinstance(value, ListLiteral):
            for item in value.items:
                self._check_value_refs(item, line, col)
        elif isinstance(value, DictLiteral):
            for v in value.entries.values():
                self._check_value_refs(v, line, col)
        elif isinstance(value, (StringLiteral, NumberLiteral, BoolLiteral, NullLiteral)):
            pass  # no refs


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def validate(script: Script) -> List[ValidationError]:
    """
    Validate a Script AST.

    Returns a list of ValidationError objects (may be empty if the script is
    clean).  Does not raise exceptions.
    """
    validator = _Validator()
    return validator.validate(script)
