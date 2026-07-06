"""
CSL Compiler.

Transforms a validated Script AST into a list of CompiledCall objects.
Each CompiledCall maps directly to a single JSON-RPC method invocation.

Variable references ($var, $var.field) become {"__ref__": "$name"} dicts
that the runtime resolves once actual return values are available.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .ast import (
    Assignment, BoolLiteral, Command, CommentNode, DictLiteral, FieldAccess,
    ListLiteral, NullLiteral, NumberLiteral, Param, Script, StringLiteral,
    Variable,
)


# ---------------------------------------------------------------------------
# CompiledCall
# ---------------------------------------------------------------------------

@dataclass
class CompiledCall:
    method: str
    params: Dict[str, Any]
    assigns_to: Optional[str]   # variable name if this is an Assignment
    source_line: int
    comment: Optional[str]


# ---------------------------------------------------------------------------
# Compiler
# ---------------------------------------------------------------------------

class _Compiler:
    def compile(self, script: Script) -> List[CompiledCall]:
        calls: List[CompiledCall] = []
        for stmt in script.statements:
            if isinstance(stmt, CommentNode):
                continue
            if isinstance(stmt, Assignment):
                call = self._compile_command(stmt.command, assigns_to=stmt.variable)
                calls.append(call)
            elif isinstance(stmt, Command):
                call = self._compile_command(stmt, assigns_to=None)
                calls.append(call)
        return calls

    def _compile_command(
        self, cmd: Command, assigns_to: Optional[str]
    ) -> CompiledCall:
        params: Dict[str, Any] = {}
        for param in cmd.params:
            params[param.key] = self._resolve_value(param.value)
        return CompiledCall(
            method=cmd.method,
            params=params,
            assigns_to=assigns_to,
            source_line=cmd.pos.line,
            comment=cmd.comment,
        )

    def _resolve_value(self, value: Any) -> Any:
        """Convert an AST value node into a Python primitive or __ref__ dict."""
        if isinstance(value, StringLiteral):
            return value.value
        if isinstance(value, NumberLiteral):
            return value.value
        if isinstance(value, BoolLiteral):
            return value.value
        if isinstance(value, NullLiteral):
            return None
        if isinstance(value, Variable):
            return {"__ref__": f"${value.name}"}
        if isinstance(value, FieldAccess):
            return {"__ref__": f"${value.variable}.{value.field}"}
        if isinstance(value, ListLiteral):
            return [self._resolve_value(item) for item in value.items]
        if isinstance(value, DictLiteral):
            return {k: self._resolve_value(v) for k, v in value.entries.items()}
        raise TypeError(f"CSL compiler: unexpected AST node type {type(value).__name__}")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compile_script(script: Script) -> List[CompiledCall]:
    """
    Compile a Script AST into a list of CompiledCall objects.

    The compiler does not perform validation — run validate() first if you
    want to catch semantic errors before compilation.
    """
    compiler = _Compiler()
    return compiler.compile(script)
