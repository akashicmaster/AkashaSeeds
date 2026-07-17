# Akasha CSL — Specification v0.1

**Concept Specific Language**  
**Status:** Phase 1 implemented — `lib/akasha/csl/`

---

## Table of Contents

1. [Philosophy](#1-philosophy)
2. [Architecture](#2-architecture)
3. [Execution Model](#3-execution-model)
4. [Language Reference](#4-language-reference)
   - [4.1 Statements](#41-statements)
   - [4.2 Variables](#42-variables)
   - [4.3 Key-Value Parameters](#43-key-value-parameters)
   - [4.4 Values](#44-values)
   - [4.5 Block Syntax](#45-block-syntax)
   - [4.6 Lists](#46-lists)
   - [4.7 Inline Dictionaries](#47-inline-dictionaries)
   - [4.8 Comments](#48-comments)
   - [4.9 Multi-line Strings](#49-multi-line-strings)
5. [Command Namespace](#5-command-namespace)
6. [Validation Model](#6-validation-model)
7. [Compilation and Runtime](#7-compilation-and-runtime)
8. [Kernel API](#8-kernel-api)
9. [Runtime Module Architecture](#9-runtime-module-architecture)
10. [LLM Integration Guide](#10-llm-integration-guide)
11. [Error Reference](#11-error-reference)
12. [Ontology Drafting (future)](#12-ontology-drafting-future)
13. [Multi-locale Roadmap](#13-multi-locale-roadmap)
14. [Examples](#14-examples)

---

## 1. Philosophy

### 1.1 What CSL Is

CSL (Concept Specific Language) is a lightweight semantic coordination language for Akasha.

CSL is designed to be:

- **Human-readable** — a researcher who has never used a terminal can read and verify a CSL script
- **LLM-readable** — the grammar is compact enough to fit in a system prompt
- **Structurally explicit** — every operation is unambiguous before execution
- **Parser-friendly** — one-pass, deterministic, no lookahead beyond a single line
- **Ontology-oriented** — vocabulary is driven by the live Concept Model registry
- **Execution-safe** — validation happens before any mutation occurs

CSL is NOT:

- A general-purpose programming language
- A natural-language parser
- A replacement for the Akasha CLI
- A hidden tool invocation format

### 1.2 Position in the Stack

CSL exists between natural language and executable graph operations:

```
Natural language (human notes, research memos)
       │
       │  LLM with CSL grammar spec in system prompt
       ▼
  [ CSL script ]          ← human review happens here
       │
       │  CSL runtime (tokenize → parse → validate → compile → execute)
       ▼
  Akasha JSON-RPC calls
       │
       ▼
  Cortex (knowledge graph)
```

The **review gate** at the CSL layer is intentional. The human checks what the LLM understood before anything is written to the graph. `csl.dry` and `csl.explain` exist specifically to support this review.

### 1.3 Core Principle

CSL is a **semantic stabilization layer**.

Natural language remains flexible. CSL fixes:

- actor / subject
- target / object
- temporal scope (`as_of`)
- confidence level
- evidence references
- relation type
- perspective (`de_facto`, `de_jure`, ...)
- epistemic framing

before execution.

---

## 2. Architecture

```
lib/akasha/csl/
├── tokenizer.py   Converts CSL source text → flat Token list
├── parser.py      Recursive descent parser: Token list → Script AST
├── ast.py         AST node dataclass definitions
├── validator.py   Semantic checks: Script AST → List[ValidationError]
├── compiler.py    AST → List[CompiledCall]  (no side effects)
├── runtime.py     Executes CompiledCall list, manages variable store
└── repl.py        Interactive interpreter (csl> prompt)
```

The pipeline is strictly one-directional and each stage is independently testable:

```python
tokens  = tokenize(source)
script  = parse(tokens)
errors  = validate(script)          # list may be empty
calls   = compile_script(script)    # pure, no I/O
results = CslRuntime(session).run(calls)
```

---

## 3. Execution Model

### 3.1 Interactive Interpreter

```bash
akasha csl
```

```
csl> $src = fact.source.add kind=newspaper title="PM Speech" credibility=0.9
csl> fact.claim speaker="PM" content="Carbon neutrality by 2050"
csl> intel.assess:
...     requirement_id = $req.requirement_id
...     assessment_type = situation
...     judgment = "Situation assessed as stable"
...     confidence = 0.8
...
csl> exit
```

- Each line (or block) executes immediately after the `csl>` prompt.
- Lines ending with `:` enter block-continuation mode (`...` prompt) until a blank line.
- Results are printed as JSON.
- Variable assignments print `-> $name = <method result>`.

### 3.2 Batch Script Mode

Submit a script via the kernel API:

```json
{"method": "csl.run", "params": {"script": "..."}}
```

- Tokenizes, parses, validates, compiles, then executes sequentially.
- Validation hard errors (level `"error"`) block execution entirely; warnings do not.
- At runtime, individual call failures are **non-fatal**: the error is recorded in the
  `ExecutionResult` and execution continues with the next call.
- All results (including per-call errors) are returned in the `results` array.

### 3.3 Validation Only

```bash
akasha csl check script.csl
```

Performs token, grammar, and semantic validation. No execution. Outputs structured errors (see §11).

### 3.4 Dry Run

```bash
akasha csl dry-run script.csl
```

Outputs the compiled operations as JSON without executing them:

```json
[
  {
    "method": "fact.source.add",
    "params": {"kind": "newspaper", "title": "PM Speech", "credibility": 0.9},
    "assigns_to": "src",
    "source_line": 1
  }
]
```

This is the primary **LLM review** format: paste the output to an LLM for explanation before running.

### 3.5 Explain

```bash
akasha csl explain script.csl
```

Produces a human-readable English summary of each operation:

```
Line 1: $src = fact.source.add(kind='newspaper', title='PM Speech', credibility=0.9)
Line 2: fact.claim(speaker='PM', content='Carbon neutrality by 2050')
```

---

## 4. Language Reference

### 4.1 Statements

A CSL script is a sequence of statements, one per line (or one block per colon-terminated line).

Three statement forms:

| Form | Syntax | Effect |
|------|--------|--------|
| Command | `method key=val ...` | Execute and discard result |
| Assignment | `$var = method key=val ...` | Execute and store result in `$var` |
| Comment | `# text` or `// text` | No effect; preserved in AST metadata |

Blank lines are ignored. Indented lines are only valid inside a block (see §4.5).

### 4.2 Variables

Variables begin with `$`.

```
$src
$claim
$country
$req
```

**Assignment** — captures the JSON return value of a command:

```
$src = fact.source.add kind=newspaper title="PM Speech"
```

**Field access** — reads a field from a captured result:

```
fact.add fact_type=event content="Event" source_id=$src.source_id
```

Field access syntax is `$variable.field`. Only one level of nesting is supported in Phase 1.

**Variable scope** — variables are scoped to the script execution session. In the REPL, variables persist across lines within the same session.

**Undefined variable** — referencing a variable before it is assigned is a validation error (see §11).

### 4.3 Key-Value Parameters

Parameters use explicit key=value assignment:

```
kind=newspaper
title="PM Speech"
credibility=0.9
```

- Keys are bare identifiers (`[A-Za-z_][A-Za-z0-9_]*`).
- Values can be any type listed in §4.4.
- Whitespace around `=` is optional.
- Parameter order is not significant.

### 4.4 Values

| Type | Example | Notes |
|------|---------|-------|
| String | `"PM Speech"` | Double-quoted; supports `\"`, `\n`, `\t`, `\\` |
| Multi-line string | `"""..."""` | See §4.9 |
| Integer | `42`, `-7` | |
| Float | `0.9`, `3.14` | |
| Boolean | `true` / `false` | Also accepts `True` / `False` |
| Null | `null` / `none` | Also accepts `None` |
| Variable | `$src` | Resolved at runtime |
| Field access | `$src.source_id` | Single field depth |
| List | `[$id1, $id2]` | See §4.6 |
| Inline dict | `{source_id=$s.source_id, weight=2}` | See §4.7 |
| Bare identifier | `de_facto`, `newspaper` | Coerced to string at parse time |

**Bare identifiers** on the right-hand side of `=` are treated as string literals. This allows:

```
perspective=de_facto          # → "de_facto"
kind=official_doc             # → "official_doc"
assessment_type=situation     # → "situation"
```

### 4.5 Block Syntax

A command may use an indented block instead of inline parameters. The method name is followed by `:`, a newline, and an indented section of `key = value` pairs:

```
intel.assess.add:
    requirement_id = $req.requirement_id
    assessment_type = situation
    judgment = "The situation is assessed as stable."
    confidence = 0.8
    method = human
```

This is equivalent to:

```
intel.assess.add requirement_id=$req.requirement_id assessment_type=situation judgment="The situation is assessed as stable." confidence=0.8 method=human
```

Block syntax is preferred for commands with many parameters or long string values.

**Rules:**
- The header line must end with `:`.
- The block is delimited by indentation (Python-style INDENT/DEDENT).
- Each block line must be a `key = value` pair.
- Comments (`# ...`) are allowed inside blocks.
- Blank lines inside a block end the block in the REPL but are silently ignored in file mode.

Assignment with block syntax:

```
$assessment = intel.assess:
    requirement_id  = $req.requirement_id
    assessment_type = risk
    judgment        = "Elevated risk detected."
    confidence      = 0.7
```

### 4.6 Lists

```
evidence=[$src1.source_id, $src2.source_id, "fixed-id-string"]
```

- Delimited by `[` and `]`.
- Items are comma-separated.
- Any value type (§4.4) is valid as a list item.
- Trailing commas are accepted.
- Multi-line lists are supported (newlines inside `[...]` are ignored by the parser).

Multi-line list example:

```
cur.fold:
    view_id = $view.view_id
    competing_input_ids = [
        $input_a.input_id,
        $input_b.input_id,
        $input_c.input_id
    ]
    unresolved = true
```

### 4.7 Inline Dictionaries

```
inputs=[
    {source_id=$s1.source_id, weight=2},
    {source_id=$s2.source_id, weight=1}
]
```

- Delimited by `{` and `}`.
- Entries are `key=value` pairs, separated by commas.
- Keys are bare identifiers.
- Values can be any type (§4.4).
- Dictionaries may appear as list items.

### 4.8 Comments

Two comment styles are supported:

```
# This is a comment
// This is also a comment
```

Comments run to the end of the line. They may appear:
- On a line by themselves
- At the end of a command line (after all parameters)
- Inside block bodies

Comments are preserved in the AST (`Command.comment` field) for use by `csl.explain`.

### 4.9 Multi-line Strings

Triple-quoted strings span multiple lines:

```
cur.conclude:
    view_id = $view.view_id
    statement = """
        Under international law as of 1939, France retained de jure
        sovereignty over Alsace-Lorraine. German administration was
        de facto but not recognised by the Allied powers.
    """
    confidence = 0.9
```

**Implementation note:** Multi-line strings are pre-processed by the tokenizer before line-by-line scanning. The `"""..."""` block is replaced with a single-line placeholder, then substituted back when the `STRING` token is created. This means multi-line strings work correctly in both inline and block positions.

---

## 5. Command Namespace

CSL commands map directly to Akasha method names. Two naming conventions are accepted:

| Convention | Example | Source |
|------------|---------|--------|
| Full method name | `fact.source.add` | ConceptRegistry (`CONCEPT_PREFIX + "." + method_suffix`) |
| Router alias | `ft.src.add` | `api/router.py` `COMMAND_SPECS` keys |

Both resolve to the same kernel method. The validator accepts either form.

**Namespace discovery** — the validator loads the live ConceptRegistry at startup and also reads `COMMAND_SPECS` from `api/router.py`. Any registered concept or router alias is considered valid. This means new concept plugins are automatically available in CSL without any parser changes.

**Built-in kernel methods** — a hardcoded set of non-concept methods is always valid:

```
w / r / rm / ln / def / exp
al / al.ls / al.find
look / out
s.add / s.rm / s.ls / s.clear / s.op
n.new / n.add / n.sec / n.read / n.rm ...
log.new / log.cp / log.ann ...
wb.new / wb.pin / wb.show ...
intel.* / cur.* / ft.* / agg.* / synth.* / pres.*
csl.run / csl.check / csl.dry / csl.explain
```

(See `lib/akasha/csl/validator.py:_KNOWN_KERNEL_METHODS` for the complete set.)

---

## 6. Validation Model

Validation runs after parsing, before compilation. It never modifies the AST.

### 6.1 Checks Performed

| Check | Level | Description |
|-------|-------|-------------|
| Unknown method | error | Method not in ConceptRegistry, router, or kernel set |
| Variable used before assignment | error | `$var` referenced before `$var = ...` appears |
| Numeric range | warning | `confidence`, `credibility`, `weight`, `feasibility`, `expected_value` outside [0, 1] |
| Typo suggestion | error (with hint) | Unknown method/param matched by `difflib.get_close_matches` |

### 6.2 `ValidationError` Structure

```python
@dataclass
class ValidationError:
    line: int
    col: int
    error: str
    parameter: str = ""    # parameter name if relevant
    suggestion: str = ""   # close-match suggestion
    level: str = "error"   # "error" | "warning"
```

### 6.3 Validation Output (JSON)

`csl.check` returns:

```json
{
  "valid": false,
  "errors": [
    {
      "line": 14,
      "col": 8,
      "error": "Unknown method 'curation.view'",
      "parameter": "",
      "suggestion": "Did you mean: curation.view.run?",
      "level": "error"
    },
    {
      "line": 21,
      "col": 12,
      "error": "Parameter 'confidence' value 1.5 is outside [0, 1]",
      "parameter": "confidence",
      "suggestion": "",
      "level": "warning"
    }
  ]
}
```

### 6.4 Severity Semantics

- **error** — blocks `csl.run` execution. `csl.check` reports all errors. `csl.dry` and `csl.explain` also block on errors.
- **warning** — does not block execution. Reported in `csl.check` output. Intended for LLM repair loops.

**Numeric range parameters** (validated for [0, 1] range):
`confidence`, `credibility`, `weight`, `feasibility`, `expected_value`

---

## 7. Compilation and Runtime

### 7.1 `CompiledCall`

The compiler produces a list of `CompiledCall` objects:

```python
@dataclass
class CompiledCall:
    method: str              # e.g. "fact.source.add"
    params: Dict[str, Any]   # resolved primitives or __ref__ dicts
    assigns_to: Optional[str] # variable name if this is an Assignment
    source_line: int
    comment: Optional[str]
```

### 7.2 Variable References in Compiled Output

Variable references are **not resolved** by the compiler. They are stored as placeholder dicts for the runtime to resolve:

| AST node | Compiled value |
|----------|----------------|
| `Variable("src")` | `{"__ref__": "$src"}` |
| `FieldAccess("src", "source_id")` | `{"__ref__": "$src.source_id"}` |

This keeps the compiler pure (no I/O, no session state) and makes `csl.dry` output inspectable.

### 7.3 Runtime Variable Store

`CslRuntime` maintains a `_vars: Dict[str, Any]` store. When a call with `assigns_to` succeeds, the result is stored:

```python
self._vars["src"] = result   # stores the full JSON result dict
```

Field access `$src.source_id` resolves as:

```python
stored = self._vars.get("src", {})
return stored.get("source_id") if isinstance(stored, dict) else None
```

### 7.4 Dispatch Order

The runtime dispatches each `CompiledCall` in order:

1. **ConceptRegistry** — tries `_concept_registry.dispatch(method, session, params, rid)` first.
2. **Session dispatch** — if the session object has a `dispatch()` method, tries it.
3. **Error** — raises `RuntimeError` if neither handles the method.

Results from a successful dispatch are either `{"result": ...}` (success) or `{"error": ...}` (application error). Both are captured in `ExecutionResult`.

### 7.5 `ExecutionResult`

```python
@dataclass
class ExecutionResult:
    method: str
    params: Dict[str, Any]
    result: Any              # None if no result or error
    error: Optional[str]     # error message if failed
    assigns_to: Optional[str]
    source_line: int
```

---

## 8. Kernel API

Four endpoints are registered in the kernel:

| Method | IAM | Description |
|--------|-----|-------------|
| `csl.run` | write | Parse, validate, compile, and execute a CSL script |
| `csl.check` | read | Validate CSL without executing |
| `csl.dry` | read | Compile to operations list (no execution) |
| `csl.explain` | read | Human-readable summary of operations |

### 8.1 Request Format

All four methods accept:

```json
{
  "method": "csl.run",
  "params": {
    "script": "# CSL source text here\n$src = fact.source.add ..."
  }
}
```

Parameter key is `"script"` (or `"source"` as alias).

### 8.2 `csl.run` Response

```json
{
  "results": [
    {
      "method": "fact.source.add",
      "result": {"status": "created", "source_id": "abc123..."},
      "error": null,
      "assigns_to": "src"
    }
  ]
}
```

### 8.3 `csl.dry` Response

```json
{
  "operations": [
    {
      "method": "fact.source.add",
      "params": {"kind": "newspaper", "title": "PM Speech", "credibility": 0.9},
      "assigns_to": "src",
      "source_line": 2
    }
  ]
}
```

### 8.4 `csl.explain` Response

```json
{
  "explanation": "Line 2: $src = fact.source.add(kind='newspaper', title='PM Speech', credibility=0.9)\nLine 3: fact.claim(speaker='PM', content='Carbon neutrality by 2050')"
}
```

### 8.5 Router Aliases

```
csl.run     → method: csl.run
csl.check   → method: csl.check
csl.dry     → method: csl.dry
csl.explain → method: csl.explain
```

---

## 9. Runtime Module Architecture

```
tokenize(source: str) -> List[Token]
    │
    │  Token types: VARFIELD, VARIABLE, STRING, NUMBER, BOOL, NULL,
    │               IDENTIFIER, EQUALS, LBRACKET, RBRACKET, LBRACE,
    │               RBRACE, COMMA, COLON, NEWLINE, INDENT, DEDENT,
    │               COMMENT, EOF
    │
    ▼
parse(tokens: List[Token]) -> Script
    │
    │  AST nodes: Script, Command, Assignment, CommentNode,
    │             Param, StringLiteral, NumberLiteral, BoolLiteral,
    │             NullLiteral, Variable, FieldAccess, ListLiteral,
    │             DictLiteral
    │
    ▼
validate(script: Script) -> List[ValidationError]
    │
    │  Checks: method existence, variable-before-use,
    │          numeric range, typo suggestion
    │
    ▼
compile_script(script: Script) -> List[CompiledCall]
    │
    │  CompiledCall: {method, params, assigns_to, source_line, comment}
    │  Variable refs become {"__ref__": "$name"} or {"__ref__": "$name.field"}
    │
    ▼
CslRuntime(session).run(calls) -> List[ExecutionResult]
    │
    │  Resolves __ref__ from _vars store.
    │  Dispatches via ConceptRegistry → session.dispatch → error.
    │  Stores assigns_to results in _vars.
    │
    ▼
List[ExecutionResult]
    {method, params, result, error, assigns_to, source_line}
```

### 9.1 Token Detail

The tokenizer handles multi-line strings (`"""..."""`) via pre-processing:

1. Scan source for `"""..."""` blocks.
2. Replace each with a single-line placeholder: `"__MLSTR_N__"`.
3. Store original content in a `placeholder_map`.
4. Tokenize line-by-line.
5. When a `STRING` token matches a placeholder key, substitute the original content.

**VARFIELD vs VARIABLE disambiguation:**

The inline regex matches `VARFIELD` (`$var.field`) before `VARIABLE` (`$var`). This ensures `$src.source_id` is captured as a single token rather than `$src` followed by `.source_id`.

**IDENTIFIER with dots:**

Method names like `fact.source.add` are matched as a single `IDENTIFIER` token by the pattern `[A-Za-z_][A-Za-z0-9_.]*`. This avoids ambiguity between method dots and field-access dots (which only appear after `$`).

**Indentation tracking:**

- An `indent_stack` (starting at `[0]`) tracks open indent levels.
- When a non-blank, non-comment line has greater indentation than `indent_stack[-1]`, an `INDENT` token is emitted and the new level is pushed.
- When indentation decreases, `DEDENT` tokens are emitted until the stack matches.
- Blank lines and comment-only lines do not trigger INDENT/DEDENT.

---

## 10. LLM Integration Guide

### 10.1 System Prompt Template

To instruct an LLM to generate CSL, include the following in the system prompt:

```
You are outputting Akasha CSL (Concept Specific Language).
CSL is an intermediate language that compiles to Akasha kernel method calls.
One CSL statement = one kernel call. Output is deterministically parseable.

RULES:
- Methods use dot notation: fact.source.add, cur.premise, intel.req
- Parameters use key=value: title="text" credibility=0.8
- Variables capture results: $src = fact.source.add ...
- Field access: $src.source_id
- Lists: evidence=[$src.source_id, $src2.source_id]
- Dicts: inputs=[{ref_id=$s.source_id, weight=2}]
- Comments: # explain what this step does
- Block syntax for long params:
    method.name:
        key = value
        key = value

AVAILABLE METHODS (examples):
fact.source.add   kind= title= credibility=
fact.add          fact_type= content= source_id=
fact.claim        speaker= content= source_id=
cur.new           title=
cur.premise       label= as_of= perspective= conflict_policy=
cur.input         ref_id= role= premise_id= confidence=
cur.view          premise_id= label=
cur.conclude      view_id= statement= conclusion_type= confidence=
intel.new         title=
intel.req         question= requirement_type= priority=
intel.scan        requirement_id= target_id= scan_type= signal=
intel.assess      requirement_id= assessment_type= judgment= confidence=
intel.recommend   requirement_id= statement= recommended_option_id=
[... add more as needed from the active concept registry ...]

VALIDATE BEFORE SUBMITTING: confidence/credibility/weight must be in [0, 1].
```

### 10.2 Human–LLM Collaboration Workflow

```
1. Human provides: raw notes, data, research memo
2. LLM generates: CSL script (using grammar above)
3. Human reviews: csl.dry to see operations list
                  csl.explain for plain-English summary
                  csl.check for validation errors
4. Human approves or edits the CSL script
5. Human runs: csl.run to execute
```

The `csl.dry` output (§8.3) is the recommended format for the human review step because it shows exactly what will be written to the graph, with no surprises.

### 10.3 LLM Repair Loop

Validation errors (§11) are structured to feed back into an LLM:

```
1. csl.check returns errors
2. Paste error JSON into LLM prompt:
   "The following CSL script produced these errors. Please fix it:
    [script]
    [errors JSON]"
3. LLM produces corrected CSL
4. Repeat from step 1 until clean
```

The `suggestion` field in `ValidationError` provides a close-match hint (e.g., `"Did you mean: curation.view.run?"`) that the LLM can use without needing to know the full method list.

---

## 11. Error Reference

### 11.1 Parse Errors (`CSLParseError`)

Raised by the parser. Stops the pipeline before validation.

| Message | Cause |
|---------|-------|
| `Expected '=' after $var` | Assignment missing `=` |
| `Expected NEWLINE after block header ':'` | Block header not at end of line |
| `Expected indented block after ':'` | No indented content after block header |
| `Expected ']' to close list` | Unclosed `[` |
| `Expected '}' to close dict` | Unclosed `{` |
| `Unexpected token in value position` | Token appears where a value is expected |

### 11.2 Validation Errors

| Error | Level | Trigger |
|-------|-------|---------|
| `Unknown method 'X'` | error | Method not in ConceptRegistry, router, or kernel set |
| `Did you mean: Y?` | error (with suggestion) | `difflib.get_close_matches` found a close match |
| `Variable '$X' used before assignment` | error | `$var` appears before `$var = ...` |
| `Parameter 'X' value Y is outside [0, 1]` | warning | Numeric range params out of range |

### 11.3 Runtime Errors

Returned in `ExecutionResult.error`.

| Error | Cause |
|-------|-------|
| `No handler for method 'X'` | Method not handled by ConceptRegistry or session |
| `Variable '$X' not found` | Variable referenced at runtime that has no stored result |
| `Field 'Y' not found in $X result` | Field access on a result that doesn't have that key |
| Application errors | Propagated from concept model (e.g., `"fact id is required"`) |

---

## 12. Ontology Drafting (future)

The `ontology` block keyword is reserved for a future phase:

```
ontology CountryControl:
    entity Territory
    entity Polity
    relation controlled_by:
        from Territory
        to Polity
        temporal true
        evidence required
```

Phase 1 tokenizes and parses this but does not compile or execute it. Ontology blocks are intended for:

- Schema design
- Graph planning
- LLM-guided ontology structuring
- Future compilation into Concept Model scaffolds

---

## 13. Multi-locale Roadmap

CSL's AST is language-independent. The surface syntax (verbs, keywords) is the only locale-specific layer.

### 13.1 Phase 1 (current): English only

All keywords, verbs, and error messages are English. Method names use the existing Akasha namespace (which is already English). The grammar spec for LLM prompting is English.

### 13.2 Planned locale order

| Phase | Locale | Notes |
|-------|--------|-------|
| 1 (current) | English | Canonical grammar. All future locales normalize to English AST. |
| 2 | German | `erstelle`, `füge hinzu`, `bewerte`, ... |
| 3 | Spanish | `crear`, `agregar`, `evaluar`, ... |
| 4 | French | `créer`, `ajouter`, `évaluer`, ... |
| 5 | Japanese | `作成する`, `追加する`, `評価する`, ... |

### 13.3 Locale Architecture

Each locale is a YAML file `lib/akasha/csl/locales/{lang}.yaml`:

```yaml
# lib/akasha/csl/locales/ja.yaml
verbs:
  作成する: create
  作る: create
  追加する: add
  登録する: add
  開く: open
  実行する: run
  評価する: assess
  推定する: estimate
  推奨する: recommend
  決定する: decide

nouns:
  ファクト集: fact-collection
  情報源: source
  事実: fact
  前提: premise
  見解: view
  キュレーション: curation
  インテリジェンス: intelligence
  要件: requirement
  差異: gap

# Method mappings (locale alias → canonical method)
methods:
  ソース追加: fact.source.add
  事実追加: fact.add
  主張記録: fact.claim
```

The locale normalizer runs before the tokenizer. It replaces locale tokens with canonical English tokens, then hands off to the standard pipeline. The AST and all downstream stages are locale-agnostic.

### 13.4 LLM Grammar Spec per Locale

Each locale ships a `spec_{lang}.md` (e.g., `spec_ja.md`) with the grammar spec translated for LLM prompting. The canonical `spec_en.md` (this document, §10.1) serves as the template.

---

## 14. Examples

### 14.1 Fact collection from research notes

```csl
# Research: PM's Carbon Neutrality Speech, June 2023
# Source: Official transcript

$src = fact.source.add:
    kind = official_doc
    title = "PM Carbon Neutrality Speech — June 2023"
    url = "https://example.gov/speech/2023-06"
    credibility = 0.95

# Core policy commitment
$f1 = fact.add:
    fact_type = event
    content = "PM commits to carbon neutrality by 2050"
    source_id = $src.source_id

# Specific claim by the speaker
$c1 = fact.claim:
    speaker = "Prime Minister"
    content = "We will reduce emissions by 45% by 2030, on a path to net zero by 2050."
    source_id = $src.source_id

# Corroboration gap
fact.absent:
    description = "No independent verification of the 45% figure baseline year"
    source_id = $src.source_id

# Quality check
ft.diagnose
```

### 14.2 Curation — territorial dispute

```csl
# Curation: Alsace-Lorraine sovereignty 1871–1945
cur.new title="Alsace-Lorraine sovereignty analysis"

# Inputs (pointing to existing atoms — never copies)
$i_fr = cur.input ref_id=<fr_sovereignty_id> role=sovereignty
$i_de = cur.input ref_id=<de_admin_id>       role=administration
$i_vt = cur.input ref_id=<versailles_id>     role=fact

# Premises
$p_jure  = cur.premise label="de_jure_1939"  as_of="1939-09-01" perspective=de_jure  conflict_policy=perspective_preferred
$p_facto = cur.premise label="de_facto_1942" as_of="1942-01-01" perspective=de_facto conflict_policy=most_recent

# Views
$v_jure  = cur.view premise_id=$p_jure.premise_id  label="Alsace: de jure 1939"
$v_facto = cur.view premise_id=$p_facto.premise_id label="Alsace: de facto 1942"

# Fold inside the de facto view
cur.fold:
    view_id = $v_facto.view_id
    resolution_scope = {entity=alsace, relation=controlled_by, time=1942, perspective=de_facto}
    competing_input_ids = [$i_fr.input_id, $i_de.input_id]
    winner_id = $i_de.input_id
    rationale = {policy=most_recent, note="German administration atom more recent"}

# Conclusions
cur.conclude view_id=$v_facto.view_id statement="As of 1942, Alsace was under German de facto administration." conclusion_type=state confidence=0.85
cur.conclude view_id=$v_jure.view_id  statement="France retained de jure sovereignty under international law." conclusion_type=state confidence=0.90

cur.diagnose
```

### 14.3 Intelligence cycle

```csl
# Intelligence workspace
intel.new title="Kaliningrad strategic assessment 2024"

$req = intel.req:
    question = "What is the current de facto vs de jure status of Kaliningrad and primary risk vectors?"
    requirement_type = strategic
    priority = high

# Scan existing evidence
intel.scan requirement_id=$req.requirement_id target_id=<ru_sovereignty_fact_id> scan_type=fact signal="Russian sovereignty confirmed 1991 Königsberg Treaty"
intel.scan requirement_id=$req.requirement_id target_id=<cur_view_id> scan_type=curation_view signal="De facto / de jure gap identified in 1939–1945 period"

# Record gaps
$gap = intel.gap:
    requirement_id = $req.requirement_id
    description = "No post-2022 sovereignty evaluation on record"
    gap_type = outdated
    severity = high

# Tasking
intel.task requirement_id=$req.requirement_id gap_id=$gap.gap_id description="Update from 2022–2024 sources" tasking_type=collect priority=high

# Assessment (after tasking fulfilled)
$assess = intel.assess:
    requirement_id = $req.requirement_id
    assessment_type = situation
    judgment = "Russia retains uncontested de facto control; de jure internationally recognised."
    basis = [<updated_sovereignty_id>, <cur_conclusion_id>]
    confidence = 0.85

# Estimate
intel.estimate:
    requirement_id = $req.requirement_id
    estimate_type = probability
    statement = "Probability of military contingency within 24 months: 15–25%"
    basis = [$assess.assessment_id]
    probability = 0.20
    range_low = 0.15
    range_high = 0.25
    confidence = 0.55

# Recommend
$rec = intel.recommend:
    requirement_id = $req.requirement_id
    statement = "Issue interim assessment with uncertainty bounds; commission field monitoring."
    confidence = 0.75
    status = reviewed

# Record decision
intel.decision recommendation_id=$rec.recommendation_id decision_status=accepted decided_by="Research Director" reason="Approved for publication."

# Full cycle view
intel.cycle requirement_id=$req.requirement_id
```

---

*CSL v0.1 — Phase 1 implementation: `lib/akasha/csl/`*  
*Spec maintained alongside implementation. Update this document when the runtime changes.*
