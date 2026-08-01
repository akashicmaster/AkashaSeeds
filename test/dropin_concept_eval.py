"""
Drop-in concept model eval (issue #50) — zero-boilerplate CLI derivation.

The promise: drop a concept model file in lib/akasha/concepts/ with a BARE
`CONCEPT_METHODS = {"suffix": "op_name"}` — no cli/args/desc/action annotations — and
it is immediately, fully usable:

  (a) the CLI command dispatches (canonical `foo.op`, one-shot `foo op`, subcommand mode),
  (b) positional args map from the op's method signature (required params, in order),
  (c) `help` text is drawn from the op's docstring,
  (d) the IAM action is derived by a verb convention (read for a curated read-verb set,
      write otherwise — fail-safe), so the kernel can route it instead of 404-ing.

This eval registers a fixture model with ONLY bare entries into a fresh ConceptRegistry
and asserts all four, then drives the three CLI forms through the real CommandRouter and
executes an op end-to-end through registry dispatch.

Run:  python test/dropin_concept_eval.py      (exit 0 = all pass)
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from lib.akasha.concepts import registry as _reg
from lib.akasha.concepts.registry import ConceptRegistry

_fails = []


def check(name, cond, detail=""):
    print(("  PASS  " if cond else "  FAIL  ") + name + (f"   ({detail})" if detail and not cond else ""))
    if not cond:
        _fails.append(name)


# ── the fixture: a model that is ALL bare entries (the zero-boilerplate case) ─────
class DropinFoo:
    """A minimal drop-in concept model — no annotations anywhere."""
    CONCEPT_PREFIX = "dropinfoo"
    CONCEPT_LABEL = "Fixture — drop-in derivation test"
    # Bare form only: suffix → op name. Nothing else declared.
    CONCEPT_METHODS = {
        "note":  "op_note",
        "tally": "op_tally",
        "show":  "op_show",
    }

    def __init__(self, session=None):
        self.session = session

    def op_note(self, content, tag="misc"):
        """Record a note. The first required param is the free-text body."""
        return {"stored": content, "tag": tag}

    def op_tally(self, a, b):
        """Add two numbers a and b."""
        return {"sum": str(a) + "+" + str(b)}

    def op_show(self, target="all"):
        """List stored notes for a target (read-only)."""
        return {"listing": target}


def build_registry():
    reg = ConceptRegistry()
    reg.register(DropinFoo)
    return reg


# ── 1. derivation from a bare entry ──────────────────────────────────────────────
def test_derivation():
    print("[1] derivation from bare CONCEPT_METHODS (no annotations)")
    reg = build_registry()

    actions = reg.get_method_actions()
    specs = reg.get_command_specs()

    # (d) IAM action by convention: 'note'/'tally' → write (not read verbs); 'show' → read.
    check("action derived: dropinfoo.note → write", actions.get("dropinfoo.note") == "write",
          actions.get("dropinfoo.note"))
    check("action derived: dropinfoo.tally → write", actions.get("dropinfoo.tally") == "write",
          actions.get("dropinfoo.tally"))
    check("action derived: dropinfoo.show → read (curated read verb)",
          actions.get("dropinfoo.show") == "read", actions.get("dropinfoo.show"))

    # (a) every bare op produced a DOTTED command spec (never a bare word).
    check("command spec emitted for bare op (dotted key)", "dropinfoo.note" in specs,
          list(specs))
    check("no bare (dotless) command key leaked",
          all("." in k for k in specs if k.startswith("dropinfoo")))

    # (b) positional args derived from the op signature: only REQUIRED params, in order.
    check("args derived from signature: note → ['content'] (tag has a default → optional)",
          specs["dropinfoo.note"]["args"] == ["content"], specs["dropinfoo.note"]["args"])
    check("args derived from signature: tally → ['a','b']",
          specs["dropinfoo.tally"]["args"] == ["a", "b"], specs["dropinfoo.tally"]["args"])
    check("args derived from signature: show → [] (target has a default)",
          specs["dropinfoo.show"]["args"] == [], specs["dropinfoo.show"]["args"])

    # (c) help text derived from the op docstring.
    check("desc derived from docstring: note",
          specs["dropinfoo.note"]["desc"].startswith("Record a note"),
          specs["dropinfoo.note"]["desc"])
    check("desc derived from docstring: tally",
          specs["dropinfoo.tally"]["desc"] == "Add two numbers a and b.",
          specs["dropinfoo.tally"]["desc"])

    # grouping: all three commands group under the model prefix.
    groups = reg.get_command_groups()
    check("commands grouped under the model prefix",
          all(groups.get(f"dropinfoo.{s}") == "dropinfoo" for s in ("note", "tally", "show")))


# ── 2. explicit annotation still wins (back-compat) ──────────────────────────────
class DropinBar:
    CONCEPT_PREFIX = "dropinbar"
    CONCEPT_METHODS = {
        # A read-looking verb ('scan') FORCED to write via annotation must stay write,
        # and an explicit args/desc/cli must override the derived ones.
        "scan": {"op": "op_scan", "action": "write", "args": ["x"], "desc": "custom", "cli": "db.scan"},
    }

    def __init__(self, session=None):
        self.session = session

    def op_scan(self, x, y=1):
        """auto-doc that must NOT win."""
        return {"x": x, "y": y}


def test_annotation_wins():
    print("[2] explicit annotation overrides every derived default")
    reg = ConceptRegistry()
    reg.register(DropinBar)
    actions = reg.get_method_actions()
    specs = reg.get_command_specs()
    check("explicit action wins (scan forced write, not derived read)",
          actions.get("dropinbar.scan") == "write")
    check("explicit cli alias used as command key", "db.scan" in specs and "dropinbar.scan" not in specs)
    check("explicit args win over signature", specs["db.scan"]["args"] == ["x"])
    check("explicit desc wins over docstring", specs["db.scan"]["desc"] == "custom")


# ── 3. the three CLI forms + positional binding through the real router ───────────
def test_cli_forms():
    print("[3] CLI forms (canonical / one-shot / subcommand) + positional binding")
    reg = build_registry()
    _reg.set_active(reg)

    # Fresh router augmentation from OUR fixture registry.
    from api.router import CommandRouter
    CommandRouter._augmented = False
    CommandRouter.augment_from_registry(reg)

    def method_of(line):
        p = CommandRouter.build_rpc_request(line, "admin")
        return (p or {}).get("method")

    def params_of(line):
        # build_rpc_request nests the op args under params["data"] (session_token sits
        # alongside). Unwrap to the actual bound op kwargs.
        p = CommandRouter.build_rpc_request(line, "admin") or {}
        inner = p.get("params", p)
        return inner.get("data", inner)

    # (a) canonical dotted form
    check("canonical: 'dropinfoo.note ...' → dropinfoo.note",
          method_of("dropinfoo.note hello world") == "dropinfoo.note")
    # (b) one-shot 'model op' form
    check("one-shot: 'dropinfoo note ...' → dropinfoo.note",
          method_of("dropinfoo note hello world") == "dropinfoo.note")
    # (c) subcommand mode: inside [dropinfoo], bare 'note ...'
    sub = CommandRouter.build_rpc_request("dropinfoo tally 3 4", "admin")
    check("subcommand mode: 'dropinfoo tally 3 4' → dropinfoo.tally",
          (sub or {}).get("method") == "dropinfoo.tally")

    # positional binding from the DERIVED args:
    # note has one positional 'content' that absorbs the remaining free text.
    p = params_of("dropinfoo.note hello there friend")
    check("positional: single free-text arg absorbs remaining tokens",
          p.get("content") == "hello there friend", p)
    # key=value overrides + the optional (defaulted) param reachable via key=value.
    p2 = params_of("dropinfoo.note the body tag=urgent")
    check("positional + key=value: content='the body', tag='urgent'",
          p2.get("content") == "the body" and p2.get("tag") == "urgent", p2)
    # tally maps two positionals a, b.
    p3 = params_of("dropinfoo.tally 3 4")
    check("positional: two-arg op binds a=3 b=4", p3.get("a") == "3" and p3.get("b") == "4", p3)

    # namespace surfaced for subcommand mode.
    ns = CommandRouter.concept_namespaces()
    check("model appears in concept_namespaces with all ops",
          set(ns.get("dropinfoo", [])) == {"note", "tally", "show"}, ns.get("dropinfoo"))


# ── 4. end-to-end execution through registry dispatch ────────────────────────────
def test_end_to_end():
    print("[4] end-to-end: a bare op executes through registry dispatch")
    reg = build_registry()
    # _filter_params must bind only the op's real params from the JSON-RPC data dict.
    resp = reg.dispatch("dropinfoo.tally", session=None,
                        data={"a": "2", "b": "5", "session_token": "x"}, rid=1)
    check("dispatch returns a result (no 404 / no crash)", "result" in resp, resp)
    check("op executed with bound params", resp.get("result", {}).get("sum") == "2+5", resp)

    resp2 = reg.dispatch("dropinfoo.note", session=None,
                         data={"content": "hi", "tag": "t"}, rid=2)
    check("op with an optional param executes", resp2.get("result", {}).get("stored") == "hi", resp2)


def main():
    test_derivation()
    test_annotation_wins()
    test_cli_forms()
    test_end_to_end()
    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails))
        sys.exit(1)
    print("ALL PASS — a bare concept model is fully drop-in: derived CLI, args, help, and IAM action.")
    sys.exit(0)


if __name__ == "__main__":
    main()
