"""
CSL Recursive Descent Parser.

Consumes a flat list of Token objects (from the tokenizer) and produces a
Script AST.  The grammar is line-oriented, with Python-style indentation for
block syntax.

Grammar (simplified):
    script        := statement* EOF
    statement     := comment | assignment | block_command | command
    assignment    := VARIABLE EQUALS command_line
    block_command := IDENTIFIER COLON NEWLINE INDENT block_params DEDENT
    block_params  := (IDENTIFIER EQUALS value NEWLINE)+
    command       := IDENTIFIER params? (COMMENT)?
    params        := param+
    param         := IDENTIFIER EQUALS value
    value         := STRING | NUMBER | BOOL | NULL | VARFIELD | VARIABLE
                   | list | inline_dict | IDENTIFIER
    list          := LBRACKET (value (COMMA value)*)? RBRACKET
    inline_dict   := LBRACE (IDENTIFIER EQUALS value
                              (COMMA IDENTIFIER EQUALS value)*)? RBRACE
"""
from __future__ import annotations

from typing import Any, List, Optional

from .tokenizer import TT, Token
from .ast import (
    Assignment, BoolLiteral, Command, CommentNode, DictLiteral, FieldAccess,
    ListLiteral, NullLiteral, NumberLiteral, Param, Pos, Script, StringLiteral,
    Variable,
)


class CSLParseError(Exception):
    """Raised on parse failures.  Carries line/col information."""

    def __init__(self, message: str, line: int = 0, col: int = 0) -> None:
        super().__init__(message)
        self.line = line
        self.col = col

    def __str__(self) -> str:
        return f"[line {self.line}, col {self.col}] {self.args[0]}"


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

class _Parser:
    def __init__(self, tokens: List[Token]) -> None:
        self._tokens = tokens
        self._pos = 0

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _cur(self) -> Token:
        return self._tokens[self._pos]

    def _peek(self, offset: int = 0) -> Token:
        idx = self._pos + offset
        if idx >= len(self._tokens):
            return self._tokens[-1]  # EOF
        return self._tokens[idx]

    def _advance(self) -> Token:
        tok = self._tokens[self._pos]
        if self._pos < len(self._tokens) - 1:
            self._pos += 1
        return tok

    def _check(self, tt: TT) -> bool:
        return self._cur().type == tt

    def _match(self, *types: TT) -> Optional[Token]:
        if self._cur().type in types:
            return self._advance()
        return None

    def _expect(self, tt: TT, msg: str = "") -> Token:
        if self._cur().type != tt:
            tok = self._cur()
            raise CSLParseError(
                msg or f"Expected {tt.name}, got {tok.type.name} ({tok.value!r})",
                tok.line, tok.col,
            )
        return self._advance()

    def _skip_newlines(self) -> None:
        while self._check(TT.NEWLINE):
            self._advance()

    def _pos_from(self, tok: Token) -> Pos:
        return Pos(tok.line, tok.col)

    # ── Top-level ─────────────────────────────────────────────────────────

    def parse(self) -> Script:
        statements = []
        self._skip_newlines()
        while not self._check(TT.EOF):
            stmt = self._statement()
            if stmt is not None:
                statements.append(stmt)
            self._skip_newlines()
        return Script(statements=statements)

    # ── Statement ─────────────────────────────────────────────────────────

    def _statement(self):
        tok = self._cur()

        # blank / stray NEWLINE
        if tok.type == TT.NEWLINE:
            self._advance()
            return None

        # COMMENT-only line
        if tok.type == TT.COMMENT:
            node = CommentNode(text=tok.value, pos=self._pos_from(tok))
            self._advance()
            self._match(TT.NEWLINE)
            return node

        # assignment: $var = command ...
        if tok.type == TT.VARIABLE:
            return self._assignment()

        # command or block_command
        if tok.type == TT.IDENTIFIER:
            return self._command_or_block()

        # Skip unknown tokens (INDENT/DEDENT at top level, etc.)
        self._advance()
        return None

    # ── Assignment: $var = IDENTIFIER params  OR  $var = IDENTIFIER:\n block ──

    def _assignment(self):
        var_tok = self._expect(TT.VARIABLE)
        self._expect(TT.EQUALS, f"Expected '=' after ${var_tok.value}")
        # Detect block assignment: $var = method:\n INDENT ...
        if self._cur().type == TT.IDENTIFIER and self._peek(1).type == TT.COLON:
            after_colon = self._peek(2)
            if after_colon.type in (TT.NEWLINE, TT.COMMENT, TT.EOF):
                cmd = self._block_command()
                return Assignment(
                    variable=var_tok.value,
                    command=cmd,
                    pos=self._pos_from(var_tok),
                )
        cmd = self._command_line(allow_comment=True)
        return Assignment(
            variable=var_tok.value,
            command=cmd,
            pos=self._pos_from(var_tok),
        )

    # ── Command or block command ──────────────────────────────────────────

    def _command_or_block(self):
        id_tok = self._cur()
        # Peek ahead: if after the IDENTIFIER comes COLON then NEWLINE → block
        # We need to look past any intermediate tokens on the same line
        # Simple rule: if next non-WS token is COLON and then NEWLINE → block
        lookahead = self._peek(1)
        if lookahead.type == TT.COLON:
            # Could be block syntax. Check that after the COLON comes a NEWLINE
            after_colon = self._peek(2)
            if after_colon.type in (TT.NEWLINE, TT.COMMENT, TT.EOF):
                return self._block_command()
        return self._command_line(allow_comment=True)

    # ── Block command: METHOD: \n INDENT key=val ... DEDENT ───────────────

    def _block_command(self):
        id_tok = self._expect(TT.IDENTIFIER)
        colon_tok = self._expect(TT.COLON)
        # optional trailing comment before newline
        comment_text: Optional[str] = None
        if self._check(TT.COMMENT):
            comment_text = self._advance().value
        self._expect(TT.NEWLINE, "Expected NEWLINE after block header ':'")
        self._expect(TT.INDENT, "Expected indented block after ':'")

        params: List[Param] = []
        while not self._check(TT.DEDENT) and not self._check(TT.EOF):
            if self._check(TT.NEWLINE):
                self._advance()
                continue
            if self._check(TT.COMMENT):
                self._advance()
                self._match(TT.NEWLINE)
                continue
            if self._check(TT.IDENTIFIER):
                p = self._param()
                if p is not None:
                    params.append(p)
            else:
                self._advance()  # skip unexpected
            self._match(TT.NEWLINE)

        self._match(TT.DEDENT)

        return Command(
            method=id_tok.value,
            params=params,
            comment=comment_text,
            pos=self._pos_from(id_tok),
        )

    # ── Command line: IDENTIFIER param* [COMMENT] NEWLINE ─────────────────

    def _command_line(self, allow_comment: bool = False):
        id_tok = self._expect(TT.IDENTIFIER)
        params: List[Param] = []
        comment_text: Optional[str] = None

        while not self._check(TT.NEWLINE) and not self._check(TT.EOF):
            if self._check(TT.COMMENT):
                comment_text = self._advance().value
                break
            p = self._param()
            if p is not None:
                params.append(p)
            else:
                break

        self._match(TT.NEWLINE)

        # Colon-free indented block continuation:
        #   method\n
        #       key = val   ← INDENT with no preceding ':'
        # This mirrors the colon-based block_command but without requiring the
        # explicit ':' separator, so user-authored CSL files can omit it.
        if self._check(TT.INDENT):
            self._advance()
            while not self._check(TT.DEDENT) and not self._check(TT.EOF):
                if self._check(TT.NEWLINE):
                    self._advance()
                    continue
                if self._check(TT.COMMENT):
                    self._advance()
                    self._match(TT.NEWLINE)
                    continue
                if self._check(TT.IDENTIFIER):
                    p = self._param()
                    if p is not None:
                        params.append(p)
                else:
                    self._advance()
                self._match(TT.NEWLINE)
            self._match(TT.DEDENT)

        return Command(
            method=id_tok.value,
            params=params,
            comment=comment_text,
            pos=self._pos_from(id_tok),
        )

    # ── Param: key=value ──────────────────────────────────────────────────

    def _param(self) -> Optional[Param]:
        if not self._check(TT.IDENTIFIER):
            return None
        # Check the token after is EQUALS
        if self._peek(1).type != TT.EQUALS:
            return None
        key_tok = self._advance()  # consume IDENTIFIER
        self._advance()            # consume EQUALS
        val = self._value()
        return Param(key=key_tok.value, value=val, pos=self._pos_from(key_tok))

    # ── Value ─────────────────────────────────────────────────────────────

    def _value(self) -> Any:
        tok = self._cur()

        if tok.type == TT.STRING:
            self._advance()
            return StringLiteral(value=tok.value, pos=self._pos_from(tok))

        if tok.type == TT.NUMBER:
            self._advance()
            return NumberLiteral(value=tok.value, pos=self._pos_from(tok))

        if tok.type == TT.BOOL:
            self._advance()
            return BoolLiteral(value=tok.value, pos=self._pos_from(tok))

        if tok.type == TT.NULL:
            self._advance()
            return NullLiteral(pos=self._pos_from(tok))

        if tok.type == TT.VARFIELD:
            self._advance()
            # value is "$var.field"
            raw = tok.value[1:]  # strip leading $
            var, field = raw.split(".", 1)
            return FieldAccess(variable=var, field=field, pos=self._pos_from(tok))

        if tok.type == TT.VARIABLE:
            self._advance()
            return Variable(name=tok.value, pos=self._pos_from(tok))

        if tok.type == TT.LBRACKET:
            return self._list_literal()

        if tok.type == TT.LBRACE:
            return self._dict_literal()

        if tok.type == TT.IDENTIFIER:
            # Bare identifier on the right side → treat as string literal
            self._advance()
            return StringLiteral(value=tok.value, pos=self._pos_from(tok))

        # Fallback: return None literal for unknown
        raise CSLParseError(
            f"Unexpected token in value position: {tok.type.name} ({tok.value!r})",
            tok.line, tok.col,
        )

    # ── List literal: [val, val, ...] ─────────────────────────────────────

    def _list_literal(self) -> ListLiteral:
        open_tok = self._expect(TT.LBRACKET)
        items = []
        while not self._check(TT.RBRACKET) and not self._check(TT.EOF):
            if self._check(TT.COMMA):
                self._advance()
                continue
            if self._check(TT.NEWLINE):
                self._advance()
                continue
            items.append(self._value())
        self._expect(TT.RBRACKET, "Expected ']' to close list")
        return ListLiteral(items=items, pos=self._pos_from(open_tok))

    # ── Inline dict: {key=val, key=val} ──────────────────────────────────

    def _dict_literal(self) -> DictLiteral:
        open_tok = self._expect(TT.LBRACE)
        entries = {}
        while not self._check(TT.RBRACE) and not self._check(TT.EOF):
            if self._check(TT.COMMA):
                self._advance()
                continue
            if self._check(TT.NEWLINE):
                self._advance()
                continue
            if not self._check(TT.IDENTIFIER):
                tok = self._cur()
                raise CSLParseError(
                    f"Expected key=value inside dict, got {tok.type.name} ({tok.value!r})",
                    tok.line, tok.col,
                )
            if self._peek(1).type != TT.EQUALS:
                tok = self._cur()
                raise CSLParseError(
                    f"Expected '=' after dict key '{tok.value}'",
                    tok.line, tok.col,
                )
            key_tok = self._advance()
            self._advance()  # consume EQUALS
            val = self._value()
            entries[key_tok.value] = val
        self._expect(TT.RBRACE, "Expected '}' to close dict")
        return DictLiteral(entries=entries, pos=self._pos_from(open_tok))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse(tokens: List[Token]) -> Script:
    """
    Parse a list of tokens into a Script AST.

    Raises CSLParseError on syntax errors.
    """
    parser = _Parser(tokens)
    return parser.parse()
