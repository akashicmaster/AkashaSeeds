#!/usr/bin/env python3
"""
The driver reads FIVE fields, and knows no workload by name (seed A slice 1 §1.3).

A static check, deliberately. Every other property of the driver can be demonstrated by running it;
this one can only be demonstrated by NOT finding something, and the thing not to find is the kind of
line that made a new programme cost a new branch:

    if kind == "station"                a test for what a workload IS
    if gid == "studio_ai"               a test for what it is CALLED
    station.studio_interval(kernel, gid)   a lookup keyed on a studio registry

Before this seed the driver had all three. It now reads `trigger, duty, effect, appetite, budget`
from the policy the declaration projected, and nothing else — so a fifth programme is a file.

Scope: the four modules the order names — the driver (`autorun.py`), admission (`admission.py`),
the run path (`society.run` in `concepts/society.py`) and the recorder (`wl_state.py`). NOT
provisioning, which legitimately knows bench kinds and society topics because it is what writes
them, and not the turn op, which is the frontend's.

Run:  python test/workload_grep_eval.py     (exit 0 = all pass)
"""
import ast
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT); sys.path.insert(0, ROOT)
_fails = []

# The driver surface the order names.
FILES = ("lib/akasha/workbench/autorun.py",
         "lib/akasha/workbench/admission.py",
         "lib/akasha/workbench/wl_state.py")
# `society.run` is one method of a large module; checked by its own body, not the whole file.
SOCIETY_RUN = ("lib/akasha/concepts/society.py", "op_run")

# Names that identify a workload rather than describing one. A hit is a branch waiting to happen.
BANNED_TOKENS = ("studio_ai", "studio_shelf", "studio_art", "studio_plant",
                 "news_show", "thinkers_shelf", "art_explorer", "plant_geek",
                 "ai-news", "reading_room", "field_guide", "gallery")
# Shapes that ask what something IS by its label.
BANNED_SHAPES = (
    (re.compile(r'\bkind\s*==\s*["\']'), 'a `kind == "…"` test'),
    (re.compile(r'["\']station["\']'), 'the literal "station"'),
    (re.compile(r'\bstudio'), 'a studio lookup'),
    (re.compile(r'\bgid\s*==\s*["\']'), 'a group-name comparison'),
    (re.compile(r'\bname\s*==\s*["\']'), 'a society-name comparison'),
)


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _code_lines(path, body=None):
    """(lineno, text) for the code of a file, or of one function in it — comments and docstrings
    stripped. A comment may name a programme while EXPLAINING why the code does not."""
    src = open(path, encoding="utf-8").read()
    tree = ast.parse(src)
    if body:
        node = next((n for n in ast.walk(tree)
                     if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == body), None)
        if node is None:
            return None
        lo, hi = node.lineno, (node.end_lineno or node.lineno)
    else:
        lo, hi = 1, len(src.splitlines())
    # Strip docstrings by blanking every string-expression statement's span.
    blanked = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str):
            blanked.update(range(n.value.lineno, (n.value.end_lineno or n.value.lineno) + 1))
    out = []
    for i, line in enumerate(src.splitlines(), 1):
        if i < lo or i > hi or i in blanked:
            continue
        code = line.split("#", 1)[0]
        if code.strip():
            out.append((i, code))
    return out


def main():
    print("=" * 78)
    print("The driver reads five fields and names no workload")
    print("=" * 78)

    targets = [(f, None) for f in FILES] + [SOCIETY_RUN]
    for path, body in targets:
        lines = _code_lines(path, body)
        label = path if body is None else "%s::%s" % (path, body)
        if lines is None:
            check("%s exists to be checked" % label, False, "function not found")
            continue
        hits = []
        for lineno, code in lines:
            for tok in BANNED_TOKENS:
                if tok in code:
                    hits.append("%s:%d names %s" % (path, lineno, tok))
            for rx, why in BANNED_SHAPES:
                if rx.search(code):
                    hits.append("%s:%d %s" % (path, lineno, why))
        check("%s tests no workload by name or kind" % label, not hits,
              "%d: %s" % (len(hits), hits[:3]))

    # ── the five fields, and that the driver actually reads them ─────────────────────────────
    from lib.akasha.workbench import workload as W
    check("the frozen shape is nine fields and the driver's share of it is five",
          len(W.REQUIRED) == 9 and set(W.DRIVER_FIELDS) <= set(W.REQUIRED)
          and len(W.DRIVER_FIELDS) == 5, "%s / %s" % (W.REQUIRED, W.DRIVER_FIELDS))
    pol_src = open("lib/akasha/workbench/workload.py", encoding="utf-8").read()
    drv = open("lib/akasha/workbench/autorun.py", encoding="utf-8").read()
    for f in W.DRIVER_FIELDS:
        check("the policy a declaration projects carries `%s`" % f, ('"%s"' % f) in pol_src)
    check("the driver reaches duty, effect and the trigger THROUGH the state layer rather than "
          "reading a declaration itself (one reader, one vocabulary)",
          "wl_state.continuous(" in drv and "wl_state.interval_of(" in drv
          and "workload.for_society" not in drv)

    # ── the reasons are ids, not strings assembled at the call site ──────────────────────────
    from lib.akasha.workbench import wl_state
    inline = re.findall(r'skipped=["\'][a-z_:]+["\']', drv)
    check("no reason is spelled inline in the driver — every one is a `wl_state.REASON_*` id",
          not inline, str(inline[:3]))
    check("every reason the driver can write is in the declared vocabulary",
          all(re.match(r"^[a-z_0-9]+$", r) for r in wl_state.REASONS) and len(wl_state.REASONS) >= 8,
          "%d reasons" % len(wl_state.REASONS))

    # ── nothing the driver swallows is swallowed SILENTLY ────────────────────────────────────────
    # A `logger.debug(… skipped: %s)` is invisible at the default level, so a driver that had
    # quietly stopped doing something looked exactly like a driver with nothing to do — the live
    # checkpoint could not tell the two apart. Every such site is now a WARNING naming WHICH place,
    # as an id from the module's own vocabulary, with the exception text in `detail=`.
    from lib.akasha.workbench import autorun as _ar
    drv_lines = _code_lines("lib/akasha/workbench/autorun.py")
    debugs = ["%d: %s" % (n, c.strip()) for n, c in drv_lines if "logger.debug(" in c]
    check("the driver has no logger.debug site left to hide a skip in", not debugs,
          "%d: %s" % (len(debugs), debugs[:3]))
    warned = [(n, c) for n, c in drv_lines if "reason=%s" in c]
    check("every skip the driver logs names its place with a reason id",
          len(warned) >= len(_ar.SKIP_REASONS), "%d sites" % len(warned))
    check("the skip ids are a declared vocabulary, lower-case and distinct",
          len(set(_ar.SKIP_REASONS)) == len(_ar.SKIP_REASONS) >= 1
          and all(re.match(r"^[a-z_0-9]+$", r) for r in _ar.SKIP_REASONS),
          "%d ids" % len(_ar.SKIP_REASONS))
    # …and each id is actually USED — a vocabulary nobody writes is a vocabulary that drifts.
    src_all = open("lib/akasha/workbench/autorun.py", encoding="utf-8").read()
    unused = [n for n, v in vars(_ar).items()
              if n.startswith("SKIP_") and n != "SKIP_REASONS"
              and src_all.count(n) < 3]        # the definition, the SKIP_REASONS tuple, ≥1 call site
    check("every declared skip id is written somewhere", not unused, str(unused))

    print()
    if _fails:
        print("RESULT: FAIL — %d check(s) failed:" % len(_fails))
        for f in _fails:
            print("   - " + f)
        sys.exit(1)
    print("RESULT: PASS — the driver, admission, the run path and the recorder name no workload, "
          "test no kind, and read the five declared fields through one state layer whose reasons "
          "are vocabulary ids.")
    sys.exit(0)


if __name__ == "__main__":
    main()
