"""
CSL Tokenizer.

Converts CSL source text into a flat list of Token objects, tracking
indentation via INDENT/DEDENT tokens (Python-style).

Multi-line strings (\"\"\"...\"\"\") are pre-processed before line-by-line
scanning so they appear as a single STRING token.
"""
from __future__ import annotations

import re
from collections import namedtuple
from enum import Enum, auto
from typing import Dict, List


class TT(Enum):
    """Token types."""
    VARFIELD   = auto()   # $var.field
    VARIABLE   = auto()   # $var
    STRING     = auto()   # "..." or """..."""
    NUMBER     = auto()   # integer or float
    BOOL       = auto()   # true/false/True/False
    NULL       = auto()   # null/none/None
    IDENTIFIER = auto()   # method names / bare values (may contain dots)
    EQUALS     = auto()   # =
    LBRACKET   = auto()   # [
    RBRACKET   = auto()   # ]
    LBRACE     = auto()   # {
    RBRACE     = auto()   # }
    COMMA      = auto()   # ,
    COLON      = auto()   # :
    NEWLINE    = auto()
    INDENT     = auto()
    DEDENT     = auto()
    COMMENT    = auto()   # # ... or // ...
    EOF        = auto()


Token = namedtuple("Token", ["type", "value", "line", "col"])


# ── Inline regex (applied after stripping leading whitespace) ─────────────────

_INLINE = re.compile(
    r'(?P<STRING>"(?:[^"\\]|\\.)*")'
    r'|(?P<COMMENT>#.*|//.*)'
    r'|(?P<VARFIELD>\$[A-Za-z_]\w*\.[A-Za-z_]\w*)'
    r'|(?P<VARIABLE>\$[A-Za-z_]\w*)'
    r'|(?P<NUMBER>-?\d+(?:\.\d+)?)'
    r'|(?P<BOOL>\b(?:true|false|True|False)\b)'
    r'|(?P<NULL>\b(?:null|none|None)\b)'
    r'|(?P<IDENTIFIER>[A-Za-z_][A-Za-z0-9_.]*)'
    r'|(?P<EQUALS>=)'
    r'|(?P<LBRACKET>\[)'
    r'|(?P<RBRACKET>\])'
    r'|(?P<LBRACE>\{)'
    r'|(?P<RBRACE>\})'
    r'|(?P<COMMA>,)'
    r'|(?P<COLON>:)'
    r'|(?P<WS>[ \t]+)'
)

# Map regex group name → TT enum
_GROUP_TO_TT: Dict[str, TT] = {
    "STRING":     TT.STRING,
    "COMMENT":    TT.COMMENT,
    "VARFIELD":   TT.VARFIELD,
    "VARIABLE":   TT.VARIABLE,
    "NUMBER":     TT.NUMBER,
    "BOOL":       TT.BOOL,
    "NULL":       TT.NULL,
    "IDENTIFIER": TT.IDENTIFIER,
    "EQUALS":     TT.EQUALS,
    "LBRACKET":   TT.LBRACKET,
    "RBRACKET":   TT.RBRACKET,
    "LBRACE":     TT.LBRACE,
    "RBRACE":     TT.RBRACE,
    "COMMA":      TT.COMMA,
    "COLON":      TT.COLON,
}


def _preprocess_multiline(source: str) -> tuple[str, Dict[str, str]]:
    """
    Replace all triple-quoted strings with single-line placeholders.
    Returns (processed_source, placeholder_map).
    """
    placeholder_map: Dict[str, str] = {}
    idx = 0
    counter = 0
    result: List[str] = []

    while idx < len(source):
        if source[idx:idx+3] == '"""':
            end = source.find('"""', idx + 3)
            if end == -1:
                # Unclosed triple quote — treat the rest as the string
                content = source[idx+3:]
                idx = len(source)
            else:
                content = source[idx+3:end]
                idx = end + 3
            placeholder = f'"__MLSTR_{counter}__"'
            placeholder_map[f"__MLSTR_{counter}__"] = content
            counter += 1
            result.append(placeholder)
        else:
            result.append(source[idx])
            idx += 1

    return "".join(result), placeholder_map


def tokenize(source: str) -> List[Token]:
    """
    Tokenize CSL source text. Returns a list of Token objects ending with EOF.
    """
    # Pre-process multi-line strings
    processed, mlstr_map = _preprocess_multiline(source)

    tokens: List[Token] = []
    indent_stack: List[int] = [0]

    lines = processed.split("\n")

    for line_no, raw_line in enumerate(lines, start=1):
        # Determine indentation
        stripped = raw_line.lstrip(" \t")
        indent = len(raw_line) - len(stripped)
        line_content = stripped.rstrip()

        # Skip blank lines and comment-only lines for INDENT/DEDENT purposes
        is_blank = not line_content
        is_comment_only = line_content.startswith("#") or line_content.startswith("//")

        if is_blank or is_comment_only:
            if is_comment_only:
                # Emit a COMMENT token for comment-only lines
                comment_text = line_content[2:].strip() if line_content.startswith("//") else line_content[1:].strip()
                tokens.append(Token(TT.COMMENT, comment_text, line_no, 1))
                tokens.append(Token(TT.NEWLINE, "\n", line_no, len(raw_line)))
            continue

        # Emit INDENT/DEDENT based on indentation change
        current_indent = indent_stack[-1]
        if indent > current_indent:
            indent_stack.append(indent)
            tokens.append(Token(TT.INDENT, indent, line_no, 1))
        elif indent < current_indent:
            while indent_stack[-1] > indent:
                indent_stack.pop()
                tokens.append(Token(TT.DEDENT, indent_stack[-1], line_no, 1))

        # Scan the content of the line
        col_offset = indent  # track column position within the original line
        pos = 0
        while pos < len(line_content):
            m = _INLINE.match(line_content, pos)
            if not m:
                # Skip unknown character
                pos += 1
                continue

            group = m.lastgroup
            value = m.group()
            col = col_offset + m.start() + 1  # 1-based column

            if group == "WS":
                pos = m.end()
                continue

            if group == "COMMENT":
                # Comment token — extract text (strip leading # or //)
                comment_text = value
                if comment_text.startswith("//"):
                    comment_text = comment_text[2:].strip()
                elif comment_text.startswith("#"):
                    comment_text = comment_text[1:].strip()
                tokens.append(Token(TT.COMMENT, comment_text, line_no, col))
                break  # rest of line is comment

            tt = _GROUP_TO_TT.get(group)
            if tt is None:
                pos = m.end()
                continue

            # Convert STRING: possibly substitute multi-line placeholder
            if tt == TT.STRING:
                inner = value[1:-1]  # strip surrounding quotes
                # Unescape standard escape sequences
                inner = inner.replace('\\"', '"').replace("\\n", "\n").replace("\\t", "\t").replace("\\\\", "\\")
                # Check for placeholder substitution
                actual = mlstr_map.get(inner, inner)
                tokens.append(Token(TT.STRING, actual, line_no, col))

            elif tt == TT.NUMBER:
                num_val: object
                if "." in value:
                    num_val = float(value)
                else:
                    num_val = int(value)
                tokens.append(Token(TT.NUMBER, num_val, line_no, col))

            elif tt == TT.BOOL:
                tokens.append(Token(TT.BOOL, value.lower() == "true", line_no, col))

            elif tt == TT.NULL:
                tokens.append(Token(TT.NULL, None, line_no, col))

            elif tt == TT.VARFIELD:
                # $var.field — emit as VARFIELD token; value is the raw "$var.field" text
                tokens.append(Token(TT.VARFIELD, value, line_no, col))

            elif tt == TT.VARIABLE:
                # $var — strip leading $
                tokens.append(Token(TT.VARIABLE, value[1:], line_no, col))

            else:
                tokens.append(Token(tt, value, line_no, col))

            pos = m.end()

        # Emit NEWLINE at end of content line
        tokens.append(Token(TT.NEWLINE, "\n", line_no, len(raw_line) + 1))

    # Close any remaining open indents
    while len(indent_stack) > 1:
        indent_stack.pop()
        tokens.append(Token(TT.DEDENT, indent_stack[-1], len(lines) + 1, 1))

    tokens.append(Token(TT.EOF, None, len(lines) + 1, 1))
    return tokens
