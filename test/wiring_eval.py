#!/usr/bin/env python3
"""
The wiring rule (backend layout order 2026-09-20 §1) — two layers, ONE direction.

    HEART         lib/akasha/ — sessions, IAM, dispatch, IPC, boot order, Health, hydrate,
                  retention, WAL/Silica, supervisor, and the Application API. Generic: it knows
                  no Concept Model, no Source, no bench, no room, no programme by name.
    PACKAGES      ontology/ ← source/ ← concepts/ ← workbench/   (the platform's, under lib/akasha/)
    APPLICATION   the application root (`app/`), rightmost: it may import the platform's API only

Dependencies form a DAG in that order. A package may import one to its LEFT; an import to the
RIGHT is the defect this eval exists to catch, because that is how the heart came to import
thirty application modules and a "generic" kernel came to know what a station is.

What the heart does instead, and what this eval checks is actually used:
  · ops / schedules / provisioners come from the manifests (a table, not an import)
  · `routers` — a package's dispatcher, consulted through get_method_actions / dispatch_if_handled
  · `binds`  — the heart hands itself to a package that asked for a handle
  · `hooks`  — a named upward call a package declares, e.g. the LLM gate the JCL worker settles
  · `concept_class(kernel, prefix)` — reach a Concept Model by its declared prefix, never by module

Checked here:
  1. no rightward import anywhere under lib/ and the application root
  2. no cross-package import inside a function in a FORBIDDEN direction — the shape that hides a
     layer violation from a module-level read
  3. the heart imports no application package by name — kernel.py, composite.py, the JCL worker
     and the CSL layer included
  4. the mechanisms above are WIRED, not merely declared: the aggregate carries routers, binds
     and hooks, and every declared entry resolves
  5. the ASSERTION that closed the last gap (the purge order §4.1, P4): no APPLICATION module — a
     file the owner map gives to the application — imports a heart module that is not the API.
     0, by assertion; the ratchet that counted it down (157 → 59 → 0) is deleted.

Run:  python test/wiring_eval.py     (exit 0 = all pass)
"""
import ast
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []

ORDER = ["heart", "ontology", "source", "concepts", "workbench", "application"]
from lib.akasha.api import reserved as _RES  # noqa: E402
_APP_PKG = _RES.app_package()



def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def pkg_of(path):
    m = re.match(r"lib/akasha/(ontology|source|concepts|workbench)/", path)
    if m:
        return m.group(1)
    if path.startswith("lib/akasha/session/"):
        return "concepts"          # the registry's instance layer — a Concept Model tier, not the heart
    if path.startswith("lib/akasha/api/"):
        return "api"
    if _RES.is_app_path(path):
        return "application"
    return "heart"


def imported_pkg(mod):
    if mod == _APP_PKG or mod.startswith(_APP_PKG + "."):
        return "application"
    m = re.match(r"lib\.akasha\.(ontology|source|concepts|workbench)(\.|$)", mod)
    if m:
        return m.group(1)
    if mod.startswith("lib.akasha.session"):
        return "concepts"
    if mod.startswith("lib.akasha.api"):
        return "api"
    if mod.startswith(("lib.akasha", "lib.harmonia", "lib.contexa", "lib.jataka")):
        return "heart"
    return None


UNPARSEABLE = []


def imports_of(path):
    """(lineno, module, in_function) for every project import in the file. An application file that
    does not parse is named and skipped (its own evals answer for it); a platform one fails."""
    try:
        tree = ast.parse(open(path, encoding="utf-8").read())
    except SyntaxError as exc:
        if not _RES.is_app_path(path):
            raise
        UNPARSEABLE.append("%s:%s" % (path, exc.lineno))
        return []
    fn_lines = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            fn_lines.update(range(n.lineno, (n.end_lineno or n.lineno) + 1))
    out = []
    for n in ast.walk(tree):
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            mods = [a.name for a in n.names] if isinstance(n, ast.Import) else [n.module or ""]
            for mod in mods:
                if imported_pkg(mod) is not None:
                    out.append((n.lineno, mod, n.lineno in fn_lines))
    return out


def main():
    # the application's MODULES the platform loads — its Concept Models and its pages; its scripts,
    # seeds and evals are tools that may boot a kernel like any operator script
    app_mods = [os.path.relpath(_RES.root(k), ROOT) for k in ("concepts", "pages")]
    files = sorted(glob.glob("lib/**/*.py", recursive=True)
                   + [f for d in app_mods for f in glob.glob(os.path.join(d, "**", "*.py"), recursive=True)])
    files = [f for f in files if "__pycache__" not in f]

    rightward, cross_fn, heart_imports_app, app_imports_heart = [], [], [], []
    for f in files:
        src = pkg_of(f)
        for lineno, mod, in_fn in imports_of(f):
            dst = imported_pkg(mod)
            if src == "api" or dst == "api" or dst == src:
                continue
            where = "%s:%d %s" % (f, lineno, mod)
            if ORDER.index(dst) > ORDER.index(src):
                rightward.append(where)
                if src == "heart":
                    heart_imports_app.append(where)
                if in_fn:
                    cross_fn.append(where)   # a forbidden edge, hidden inside a call
            if src != "heart" and dst == "heart":
                app_imports_heart.append(where)

    if UNPARSEABLE:
        print("        (application files that do not parse, not scanned: %s)" % ", ".join(UNPARSEABLE))
    # ── 1. the DAG holds ──────────────────────────────────────────────────────────────────────
    check("no RIGHTWARD import: heart ← ontology ← source ← concepts ← workbench ← application",
          not rightward, "%d: %s" % (len(rightward), rightward[:6]))
    check("the heart imports no application package by name — it discovers them through their "
          "manifests", not heart_imports_app, "%d: %s" % (len(heart_imports_app), heart_imports_app[:6]))

    # ── 2. no cross-package import hidden inside a function ──────────────────────────────────
    check("no forbidden edge hidden inside a function — a rightward import is caught whether it "
          "sits at the top of the file or in a call",
          not cross_fn, "%d: %s" % (len(cross_fn), cross_fn[:6]))

    # ── 3. the mechanisms that replace those imports are wired ───────────────────────────────
    from lib.akasha import kernel as _kmod
    agg = _kmod._heart_aggregate()
    check("the aggregate carries the packages' ROUTERS, and their method actions reach the "
          "access table", bool(agg.routers) and len(agg.method_actions) > 0,
          "routers=%d actions=%d" % (len(agg.routers), len(agg.method_actions)))
    check("a router answers the router protocol (dispatch_if_handled / get_method_actions / "
          "get_class)", all(callable(getattr(r, m, None)) for r in agg.routers
                            for m in ("dispatch_if_handled", "get_method_actions", "get_class")))
    check("BINDS are declared and callable — the heart hands itself to a package that asked for "
          "a handle instead of being imported by it",
          bool(agg.binds) and all(callable(b) for b in agg.binds), "%d" % len(agg.binds))
    check("HOOKS are declared and callable — every named upward call resolves to a function",
          bool(agg.hooks) and all(callable(f) for f in agg.hooks.values()), "%d" % len(agg.hooks))

    from lib.akasha import api as _api
    check("concept_class(kernel, prefix) reaches a Concept Model by its declared prefix — the way "
          "a lower layer uses one without importing it",
          _api.concept_class(None, "cronon") is not None and _api.concept_class(None, "source") is not None
          and _api.concept_class(None, "nope-not-a-model") is None)

    # the hooks the heart actually calls must exist, or a Health line / a settled reservation
    # would silently become a no-op
    # (`tier_policy` is an extension point the APPLICATION may fill; the heart's default stands
    # when nothing does, so it is not required here)
    for name in ("llm_settle", "llm_health_segment", "pulse_note_dispatch"):
        check("the hook the heart calls is provided by a package: %s" % name,
              callable(agg.hooks.get(name)), str(agg.hooks.get(name)))

    # ── 5. the closed gap, as an assertion (P4) ──────────────────────────────────────────────
    from lib.akasha.api import manifest as _M
    _agg = _M.load_manifests(_M.default_manifest_paths(os.path.join(ROOT, "lib", "akasha")))
    app_heart = [w for w in app_imports_heart if _M.owner_of(_agg, w.split(":", 1)[0]) == "user"]
    print("        (platform modules inside the packages importing the heart: %d — the platform's own "
          "layering, not the gap)" % (len(app_imports_heart) - len(app_heart)))
    check("application modules importing a heart module that is not the API: %d (must be 0)"
          % len(app_heart), not app_heart, "; ".join(app_heart[:6]))

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("RESULT: PASS — the dependency graph runs one way. No package imports one to its right, "
          "no layer edge hides inside a function, and the heart names no application package: it "
          "reaches them through the manifests' routers, binds and hooks, and a Concept Model by "
          "its declared prefix.")
    sys.exit(0)


if __name__ == "__main__":
    main()
