# Writing a drop-in concept model

Drop a Python file into `lib/akasha/concepts/` and its operators are **immediately usable
and discoverable from the CLI** — no router edit, no kernel handler, no GUI. This page is
the whole story: the minimal file, what you get for free, and how to override a default.

> This is the concrete expression of Akasha's **Operand / Operator / Agent** methodology:
> a concept model is a registry of Operators; the CLI is the Agent's entry point. The seam
> between them is *derived from the model itself* — nothing is declared twice.

---

## The minimal file

```python
# lib/akasha/concepts/foo.py

class Foo:
    CONCEPT_PREFIX  = "foo"                     # command namespace
    CONCEPT_METHODS = {                         # suffix → op method name (BARE form)
        "note":  "op_note",
        "tally": "op_tally",
        "show":  "op_show",
    }

    def __init__(self, session):
        self.session = session                  # the Agent's session (cortex, scopes, IAM)

    def op_note(self, content, tag="misc"):
        """Record a note. The first required param is the free-text body."""
        ...

    def op_tally(self, a, b):
        """Add two numbers a and b."""
        ...

    def op_show(self, target="all"):
        """List stored notes for a target (read-only)."""
        ...
```

That is the **entire** integration. Two class attributes (`CONCEPT_PREFIX`,
`CONCEPT_METHODS`) opt the class into auto-discovery; the `op_*` methods are the Operators.

---

## What you get for free

The instant the file is present, every op is reachable **four equivalent ways** and fully
help-listed, with everything derived from the op itself:

| Surface | Derived from | Example |
|---|---|---|
| **CLI command** (canonical) | `CONCEPT_PREFIX` + suffix | `foo.note hello world` |
| **CLI command** (one-shot) | same | `foo note hello world` |
| **Subcommand mode** | same | `[foo]` → `note hello world` |
| **Positional args** | the `op_*` signature | `foo.tally 3 4` → `a=3, b=4` |
| **`help -c foo`** | the op's **docstring** | `note — Record a note. …` |
| **IAM action** (read/write) | a **verb convention** | `note`,`tally` → write; `show` → read |

### Positional args — the rule

The **required** parameters of the op (those without a default) become the positional CLI
args, in signature order. Parameters **with a default** stay optional and are reachable as
`key=value`. The **last** positional arg absorbs all remaining tokens, so free text works:

```
foo.note hello there friend        → content="hello there friend"   (tag defaults to "misc")
foo.note the body tag=urgent       → content="the body", tag="urgent"
foo.tally 3 4                       → a="3", b="4"
```

### Help — from the docstring

`help -c foo` lists the operators; each blurb is the first line of the op's docstring. Give
every op a one-line docstring and its help writes itself.

### IAM action — the convention (and why it fails safe)

Each op is gated by an IAM action so the kernel can route it (an op with *no* action is
rejected `-32601 Method not found` at the capability gate — it never reaches dispatch). The
action is derived:

- a curated set of **read verbs** (`ls`, `list`, `get`, `show`, `view`, `find`, `search`,
  `read`, `explore`, `roots`, `tree`, `children`, `stat`, `info`, `near`, `sim`, `profile`,
  … — operations that never mutate) → **`read`**
- **anything else → `write`** (fail-safe: an unknown verb requires the higher capability, so
  a write can never be mislabelled as a guest-readable read).

Guests have READ only, so a derived-`read` op is guest-reachable and a derived-`write` op is
not — exactly the intent.

---

## Overriding a default

Derivation only fills a **missing** field — an explicit annotation always wins. Switch a
bare entry to the dict form and set just the keys you want to pin:

```python
CONCEPT_METHODS = {
    # 'scan' reads like a read verb but this op mutates — force write, and pin the rest.
    "scan": {"op": "op_scan", "action": "write",
             "args": ["query"], "desc": "Rebuild the index for a query", "cli": "foo.scan"},
    # everything else stays bare and derived:
    "ls":   "op_list",
}
```

| Key | Meaning | Omit to derive from |
|---|---|---|
| `op` | op method name (**required** in dict form) | — |
| `action` | IAM action: `read` / `write` / `drop` | the verb convention |
| `args` | positional CLI arg names | the op's required parameters |
| `desc` | help text | the op's docstring |
| `cli` | explicit CLI alias (the command key) | the dotted `prefix.suffix` |
| `coerce` | `lambda data: kwargs` for custom param mapping | signature filtering |

**Annotate `action` explicitly whenever the read/write split is load-bearing** — e.g. a
projection/analysis op that reads but whose verb the convention would guess as write, or a
destructive op that should require the DELETE capability (`"action": "drop"`). The convention
is a convenience for the common verbs, not a security boundary.

---

## What is *not* derivable (still write real code)

- The **op bodies** — the actual Operators. Derivation wires the surface, not the behaviour.
- **Custom param mapping** (`coerce`) when the CLI/JSON keys differ from the op's parameter
  names, or when an op takes an open `**kwargs` set.
- A model that must appear under a **short abbreviation** distinct from its prefix still sets
  `cli` per op (back-compat abbreviations like `th.reference` are pinned this way).

---

## Verifying your model from the REPL

The CLI is the fast path for authoring and debugging — no front-end required:

```
akasha> foo note hello world          # dispatch it
akasha> help -c foo                    # confirm help + args are derived as expected
akasha> [foo]                          # enter subcommand mode
[foo]> tally 3 4
```

If an op returns `-32601 Method not found`, the class was not discovered (check both
`CONCEPT_PREFIX` and `CONCEPT_METHODS` are present, and the file is not `_`-prefixed).

---

## Namespace-aliased surfaces (advanced)

A model can expose the **same ops under a second command prefix** bound to a constructor
namespace — useful when one topology needs an isolated variant (e.g. the Note Loom app's
`loom.note.*` is the note ops with an isolated active-document cursor). Declare
`CONCEPT_NAMESPACES = {command_prefix: constructor_namespace}` and give the model's
`__init__` a `namespace` kwarg:

```python
class NoteConcept(BaseConcept):
    CONCEPT_PREFIX = "note"
    CONCEPT_NAMESPACES = {"loom.note": "loom"}     # loom.note.* = note ops, namespace="loom"
    CONCEPT_METHODS = { ... }

    def __init__(self, session, concept_id=None, namespace=None):
        super().__init__(session, concept_id, namespace=namespace)
```

The registry then registers `loom.note.<suffix>` for every op, instantiating
`NoteConcept(session, namespace="loom")`. No parallel handler block, no bespoke wiring — a
namespaced surface is just another entry in the one drop-in path.

## Reference (advanced)

- Registry + derivation: `lib/akasha/concepts/registry.py` (`register`,
  `_derive_action` / `_derive_positional_args` / `_derive_desc`).
- Router folding: `api/router.py` (`augment_from_registry`, `concept_namespaces`).
- Capability gate: `lib/akasha/kernel.py` (the `_METHOD_TO_ACTION` lookup) merges the
  registry's derived actions at boot (hand-written entries win).
- End-to-end eval: `test/dropin_concept_eval.py`.
- The fuller contributor spec (lifecycle, rendering, pipeline hooks):
  `docs/concept-model/concept-model-spec.md`.
