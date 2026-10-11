#!/usr/bin/env python3
"""
Group 4 — every point the platform ASKS for is filled, by exactly one op.

Group 4 moved every place the platform named an application onto something the application declares
on its own manifest entries. While the application's half was outstanding, `test/_application_owed.py`
filled those declarations for evals and this eval counted what was still owed (46 at 2026-09-26 AM).
The application's order declared all of them (46 → 0), so the stub is deleted, as its header said it
would be, and this eval holds the result instead of counting a debt:

  1. every extension point platform code asks for — the second argument of `implementer(…)`, the
     argument of `declared_implementer(…)`, every `"pipeline.<role>"` a pipeline endpoint dispatches —
     is implemented by EXACTLY ONE op (none = the feature is empty on a cell; two = which one answers
     depends on manifest order). The points are READ FROM THE PLATFORM'S CODE, not listed here, so a
     new point is covered the day it is asked for;
  2. every declared implementer is an op a Concept Model or a manifest actually serves;
  3. the attributes the platform reads are present: at least one `dive_bearing` op, the `letters`
     and `glossary` reference roles, a pulse surface, the MCP concept tool, and each package-level
     `effectful_families` a capability names.

Run:  python test/application_owed_eval.py     (exit 0 = all pass)
"""
import ast
import glob
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _platform_py(agg):
    from lib.akasha.api import manifest as M
    out = []
    for f in sorted(glob.glob(os.path.join(ROOT, "lib", "**", "*.py"), recursive=True)
                    + glob.glob(os.path.join(ROOT, "api", "**", "*.py"), recursive=True)
                    + [os.path.join(ROOT, "akasha.py")]):
        rel = os.path.relpath(f, ROOT)
        if "__pycache__" in rel:
            continue
        try:
            if M.owner_of(agg, rel) == "platform":
                out.append(f)
        except Exception:
            continue
    return out


def asked_points(agg):
    """{point: [site, …]} for every point platform code asks for."""
    pts = {}
    for f in _platform_py(agg):
        try:
            tree = ast.parse(open(f, encoding="utf-8").read())
        except SyntaxError:
            continue
        rel = os.path.relpath(f, ROOT)
        for n in ast.walk(tree):
            if isinstance(n, ast.Call):
                name = getattr(n.func, "attr", getattr(n.func, "id", ""))
                arg = None
                if name == "implementer" and len(n.args) >= 2:
                    arg = n.args[1]
                elif name == "declared_implementer" and n.args:
                    arg = n.args[0]
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    pts.setdefault(arg.value, []).append("%s:%d" % (rel, n.lineno))
            if isinstance(n, ast.Constant) and isinstance(n.value, str) \
                    and n.value.startswith("pipeline.") and n.value.count(".") >= 2 \
                    and " " not in n.value:
                pts.setdefault(n.value, []).append("%s:%d" % (rel, n.lineno))
    return pts


def main():
    print("=" * 78)
    print("Group 4 — every point the platform asks for is filled, by exactly one op")
    print("=" * 78)
    from lib.akasha.api import manifest as M
    agg = M.load_manifests(M.default_manifest_paths(os.path.join(ROOT, "lib", "akasha")))
    attrs = M.declared_op_attrs()
    from lib.akasha.concepts import registry as R
    reg = R.build_active()

    implementers = {}
    for m, a in attrs.items():
        val = a.get("implements")
        for p in (val if isinstance(val, (list, tuple)) else [val]):
            if p:
                implementers.setdefault(str(p), []).append(m)

    asked = asked_points(agg)
    check("platform code asks for extension points (%d found)" % len(asked), len(asked) >= 5,
          ", ".join(sorted(asked)))
    empty = sorted(p for p in asked if not implementers.get(p))
    check("…and every one is implemented — none is empty on a cell", not empty,
          "; ".join("%s (asked at %s)" % (p, asked[p][0]) for p in empty))
    twice = {p: implementers[p] for p in asked if len(implementers.get(p) or []) > 1}
    check("…by exactly ONE op — two would make the answer depend on manifest order", not twice,
          str(twice))
    served = set(reg._handlers) | set(agg.op_package)
    ghosts = sorted({m for ms in implementers.values() for m in ms if m not in served})
    check("every declared implementer is an op something serves", not ghosts, str(ghosts))

    dive = sorted(m for m, a in attrs.items() if a.get("dive_bearing"))
    check("the dive-bearing set is not empty (dive admission guards %d op(s))" % len(dive),
          len(dive) >= 4, ", ".join(dive))
    roles = {(a.get("projection") or {}).get("reference", {}).get("role")
             for a in attrs.values() if isinstance(a.get("projection"), dict)
             and isinstance((a.get("projection") or {}).get("reference"), dict)}
    check("the portal's two reference roles are declared (letters, glossary)",
          {"letters", "glossary"} <= roles, str(sorted(r for r in roles if r)))
    check("at least one pulse surface is declared", bool(M.declared_projection("pulse")),
          "%d" % len(M.declared_projection("pulse")))
    mcp = [m for m, v in M.declared_projection("mcp").items() if isinstance(v, dict) and v.get("name")]
    check("the MCP concept tool is declared by its op", bool(mcp), str(mcp))
    check("the application declares its world-leaving capability family",
          "station" in M.declared_effectful_families(), str(sorted(M.declared_effectful_families())))
    check("the eval-only stub is gone (`test/_application_owed.py`)",
          not os.path.exists(os.path.join(ROOT, "test", "_application_owed.py")))

    print()
    if _fails:
        print("FAILED (%d): %s" % (len(_fails), "; ".join(_fails)))
        sys.exit(1)
    print("RESULT: PASS — every extension point the platform asks for is implemented by exactly one "
          "real op, and the attributes the platform reads are declared by their owners.")
    sys.exit(0)


if __name__ == "__main__":
    main()
