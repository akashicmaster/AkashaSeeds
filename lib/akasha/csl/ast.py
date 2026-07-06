"""
CSL Abstract Syntax Tree node definitions.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union


@dataclass
class Pos:
    line: int
    col: int = 0


# ── Value nodes ───────────────────────────────────────────────────────────────

@dataclass
class StringLiteral:
    value: str
    pos: Pos


@dataclass
class NumberLiteral:
    value: Union[int, float]
    pos: Pos


@dataclass
class BoolLiteral:
    value: bool
    pos: Pos


@dataclass
class NullLiteral:
    pos: Pos


@dataclass
class Variable:
    """$var reference."""
    name: str
    pos: Pos


@dataclass
class FieldAccess:
    """$var.field reference."""
    variable: str
    field: str
    pos: Pos


@dataclass
class ListLiteral:
    items: List[Any]
    pos: Pos


@dataclass
class DictLiteral:
    """Inline dict: {key=val, key=val}."""
    entries: Dict[str, Any]
    pos: Pos


# ── Statement nodes ───────────────────────────────────────────────────────────

@dataclass
class Param:
    key: str
    value: Any
    pos: Pos


@dataclass
class Command:
    method: str
    params: List[Param]
    comment: Optional[str]
    pos: Pos


@dataclass
class Assignment:
    """$var = command ..."""
    variable: str
    command: Command
    pos: Pos


@dataclass
class CommentNode:
    text: str
    pos: Pos


# ── Top-level ─────────────────────────────────────────────────────────────────

@dataclass
class Script:
    statements: List[Union[Assignment, Command, CommentNode]]
    source: str = ""
