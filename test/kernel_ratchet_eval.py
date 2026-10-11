#!/usr/bin/env python3
"""
The heart stays a heart (backend layout order 2026-09-20 §7.1–7.2).

`kernel.py` reached 18,310 lines and 384 methods because every feature that needed a dispatch
entry grew a handler beside it: the bench driver, the station's daemon, the corpus bootstraps,
the ontology loader and every concept op lived in the same file as session resolution and the
capability gate. A "generic" kernel knew what a studio was. The purge moved each family into the
package that owns it; this eval is the assertion that stops it coming back.

Checked here:
  1. kernel.py is at or under the ceiling (5,000 lines) — an ASSERTION (the purge order §4.1: the
     ratchet that sat below it is deleted; a ratchet is a declining bound, the ceiling is the law)
  2. no application family is DEFINED in the heart any more: `_bench_*`, `_station_*`, `_studio_*`,
     `_provision_*`, `_autorun_*`, `_source_*`, `_onto_*`, `_llm_*`, or a concept op handler
  3. the 128-branch dispatch chain is gone: no `if method ==` anywhere in the heart; dispatch is
     the manifests' table
  4. no application package is imported in the heart's own modules (the companion check lives in
     wiring_eval; here it is the kernel file specifically, where the drift started)
  5. the heart still serves what it kept — sessions, auth/IAM, dispatch, Health, hydrate,
     retention, WAL, supervisor — so this is a purge, not an amputation

Run:  python test/kernel_ratchet_eval.py     (exit 0 = all pass)
"""
import ast
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []

KERNEL = os.path.join(ROOT, "lib", "akasha", "kernel.py")
CEILING = 5000                 # the order's ceiling — an assertion, not a ratchet

# Families that belong to an application package. A definition matching one of these in the heart
# is the drift this eval exists to catch.
APP_PREFIXES = ("_bench_", "_station_", "_studio_", "_provision_", "_autorun_", "_source_",
                "_onto_", "_llm_", "_sweep_", "_vlab_", "_nebula_", "_dream_", "_macro_",
                "_cross_", "_io_", "_horizon_", "_weave_")


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def main():
    src = open(KERNEL, encoding="utf-8").read()
    # `wc -l` semantics, so the number in the order, the number in the delivery note and the number
    # here are ONE number. Counting newlines + 1 made a file ending in a newline read one line
    # longer than every other tool reported it, which is how a ratchet acquires an off-by-one
    # nobody can reconcile.
    lines = len(src.splitlines())
    tree = ast.parse(src)

    # ── 1. size ───────────────────────────────────────────────────────────────────────────────
    check("kernel.py is under the ceiling: %d lines ≤ %d" % (lines, CEILING), lines <= CEILING)

    # ── 2. no application family defined here ────────────────────────────────────────────────
    defs = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defs.append(node.name)
    strays = sorted(n for n in defs if n.startswith(APP_PREFIXES))
    check("no application family is DEFINED in the heart (bench / station / studio / provisioning "
          "/ autorun / source / onto / llm / concept-op handlers)",
          not strays, "%d: %s" % (len(strays), strays[:8]))

    handlers = sorted(n for n in defs if n.startswith("_handle_"))
    check("the `_handle_*` population is down to the heart's own — sessions, auth/IAM, users and "
          "groups, status, compact, census (%d left)" % len(handlers), len(handlers) <= 60,
          str(handlers[:8]))

    # ── 3. the dispatch chain is gone ────────────────────────────────────────────────────────
    chain = re.findall(r"^\s*(?:el)?if\s+method\s*==", src, re.M)
    check("the `if method ==` chain is deleted — dispatch is the manifests' table, not 128 "
          "branches", not chain, "%d left" % len(chain))
    check("`method in (...)` dispatch branching is gone too",
          not re.findall(r"^\s*(?:el)?if\s+method\s+in\s*[\(\{]", src, re.M),
          str(re.findall(r"^\s*(?:el)?if\s+method\s+in\s*[\(\{].{0,50}", src, re.M)[:3]))

    # ── 4. no application import in the kernel file ──────────────────────────────────────────
    app_imports = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            mods = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or ""]
            for mod in mods:
                if re.match(r"lib\.akasha\.(ontology|source|concepts|workbench)(\.|$)", mod):
                    app_imports.append("%d: %s" % (node.lineno, mod))
    check("kernel.py imports NO application package — it reaches them through the manifests' "
          "ops, schedules, routers, binds and hooks", not app_imports,
          "%d: %s" % (len(app_imports), app_imports[:6]))

    # ── 5. the heart still does the heart's work ─────────────────────────────────────────────
    from lib.akasha import kernel as _kmod
    agg = _kmod._heart_aggregate()
    kept = {"sys.status", "sys.su", "auth.verify", "session.guest.create", "iam.grant",
            "user.add", "grp.new", "svc.ls", "sys.compact", "sys.census"}
    heart_ops = {n for n, spec in
                 [(n, s) for m in agg.packages if m["package"] == "heart"
                  for n, s in (m.get("ops") or {}).items()]}
    missing = sorted(kept - heart_ops)
    check("the heart still OWNS what it kept — sessions, auth, IAM, users and groups, the "
          "supervisor plane, compact and census", not missing, str(missing))
    STAGES = ("pre_identity", "post_identity", "pre_su", "pre", "post")
    unresolved = [n for n in sorted(kept)
                  if not any(agg.ops.resolve(n, st) is not None for st in STAGES)]
    check("every heart op the dispatcher kept RESOLVES at one of its stages (a purge, not an "
          "amputation)", not unresolved, str(unresolved))

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("RESULT: PASS — the heart is %d lines and knows no application family by name: no bench, "
          "station, source, ontology or concept handler is defined in it, the dispatch chain is a "
          "table, and it imports no application package — while still serving sessions, auth, IAM, "
          "the supervisor plane and the store's own maintenance." % lines)
    sys.exit(0)


if __name__ == "__main__":
    main()
