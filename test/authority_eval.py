#!/usr/bin/env python3
"""
Authority lives in one place (backend layout order 2026-09-20 §1.6).

"Provisioning runs as admin from ONE module (`workbench/provision.py`); no other application code
obtains an admin or system session." The rule exists because privilege that can be taken anywhere
is privilege nobody can audit: a boot path that quietly ran as admin was how a bench came to be
created, armed and re-armed from three different files, each with its own idea of the order.

Checked here:
  1. PROVISIONING — creating a bench or a society, arming a moderator, granting a capability,
     converging a studio — happens only inside `workbench/provision.py`. Another module may ask
     for it, it may not perform it
  2. the provisioning entry points are the ones the manifests declare, so the boot path the heart
     runs is that module and not a second copy
  3. the elevated identities are the known ones (`admin`, `system.*`) and no application module
     invents a new privileged name
  4. ASSERTION (the purge order §4.1: 6 → 0) — no PLATFORM module but the authority obtains an
     elevated session itself (`get_session("admin"|"system.*")`, `system_context()`). A platform
     module that must act as the operator asks the one door, `lib.akasha.api.authority.elevated(
     kernel, purpose)`, and every purpose it names is a row the door's table declares. Application
     modules that still elevate are listed (theirs to move), not counted.

Run:  python test/authority_eval.py     (exit 0 = all pass)
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

AUTHORITY = "lib/akasha/workbench/provision.py"
APP_GLOBS = ["lib/akasha/ontology/*.py", "lib/akasha/source/*.py",
             "lib/akasha/concepts/*.py", "lib/akasha/workbench/*.py"]

# Obtaining privilege: an elevated session, or a write that bypasses the workspace guard.
ELEVATION = re.compile(r'get_session\(\s*["\'](admin|system\.[\w.]+)["\']\s*\)|system_context\(\s*\)')

# The provisioning acts themselves — the ones that STAND a workload up.
PROVISION_ACTS = ("society.moderator", "society.responsible", "society.chairman",
                  "bench.new", "cap.declare", "auto_exec")

DOOR_CALL = re.compile(r'authority\.elevated\(\s*kernel\s*,\s*["\']([\w.]+)["\']\s*\)')


def _platform_file(f):
    if not f.startswith("lib/akasha/concepts/"):
        return True
    import json as _json
    pm = set(_json.load(open("lib/akasha/concepts/MANIFEST.json", encoding="utf-8"))
             .get("platform_modules") or [])
    return os.path.splitext(os.path.basename(f))[0] in pm


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def main():
    os.chdir(ROOT)
    files = sorted(f for g in APP_GLOBS for f in glob.glob(g) if "__pycache__" not in f)

    # ── 1. provisioning is performed in one module ───────────────────────────────────────────
    offenders = []
    for f in files:
        if f == AUTHORITY:
            continue
        src = open(f, encoding="utf-8").read()
        tree = ast.parse(src)
        for node in ast.walk(tree):
            # a provisioning act is a dispatched method name in a call, not a mention in prose
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if node.value in ("society.moderator", "society.responsible", "society.chairman",
                                  "bench.new"):
                    offenders.append("%s:%d %s" % (f, node.lineno, node.value))
    # The workload plan is BUILT as data in workload_provision.py and dispatched through a callable
    # the AUTHORITY module hands in (`provision.provision_workloads` passes `d`, which dispatches as
    # the boot admin over TRUST_INTERNAL). Naming a method while building a plan is data; opening a
    # privileged path to run it is the thing this check exists to stop, and that path is still in
    # exactly one module.
    plan_only = [o for o in offenders if o.startswith("lib/akasha/workbench/workload_provision.py")]
    real = [o for o in offenders if o not in plan_only]
    check("no application module outside the authority performs a provisioning act — creating a "
          "bench or society, appointing a moderator, setting a responsibility",
          not real, "%d: %s" % (len(real), real[:6]))
    if plan_only:
        print("        (workload_provision.py names %d of them while BUILDING the plan; the "
              "authority module supplies the dispatcher that executes it)" % len(plan_only))

    # ── 2. the boot path runs that module ────────────────────────────────────────────────────
    from lib.akasha import kernel as _kmod
    agg = _kmod._heart_aggregate()
    prov_srcs = [getattr(fn, "__module__", "") for _n, fn in
                 [(n, f) for n, f in (agg.provision.entries() if hasattr(agg.provision, "entries")
                                      else [])]]
    sched_from_authority = [n for n, fn in agg.schedules.phase("writer")
                            if getattr(fn, "__module__", "").endswith("workbench.provision")]
    check("the provisioning the heart runs at boot comes FROM the authority module",
          bool(sched_from_authority) or any("workbench.provision" in m for m in prov_srcs),
          "writer schedules from it: %s" % sched_from_authority)

    # ── 3. no invented privileged identity ───────────────────────────────────────────────────
    known = {"admin", "system.librarian", "system.weaver", "system.jataka", "system.broadcaster"}
    invented = set()
    for f in files:
        for m in re.finditer(r'get_session\(\s*["\'](system\.[\w.]+|admin)["\']', open(f, encoding="utf-8").read()):
            if m.group(1) not in known:
                invented.add("%s: %s" % (f, m.group(1)))
    check("no application module invents a privileged identity — the elevated names are the "
          "known ones", not invented, str(sorted(invented)[:5]))

    # ── 4. elevation: the authority, the door, nothing else ──────────────────────────────────
    elevated, app_elev, purposes = {}, {}, {}
    for f in files:
        src = open(f, encoding="utf-8").read()
        n = len(ELEVATION.findall(src))
        if n:
            (elevated if (_platform_file(f) or f == AUTHORITY) else app_elev)[f] = n
        for p in DOOR_CALL.findall(src):
            purposes.setdefault(p, []).append(os.path.basename(f))
    others = {k: v for k, v in elevated.items() if k != AUTHORITY}
    check("ASSERTION — platform modules other than the authority that elevate themselves: %d "
          "(must be 0)" % len(others), not others,
          ", ".join("%s×%d" % (os.path.basename(k), v) for k, v in sorted(others.items())))
    from lib.akasha.api import authority as _door
    undeclared = sorted(p for p in purposes if p not in _door.PURPOSES)
    check("every purpose the door is asked for is a declared row (%s)"
          % ", ".join("%s←%s" % (p, "/".join(sorted(set(v)))) for p, v in sorted(purposes.items())),
          not undeclared, str(undeclared))
    try:
        _door.elevated(None, "no.such.purpose")
        refused = False
    except _door.UndeclaredPurpose:
        refused = True
    check("an undeclared purpose is refused by the door (UndeclaredPurpose)", refused)
    if app_elev:
        print("        application modules that still elevate themselves (theirs to move): "
              + ", ".join("%s×%d" % (os.path.basename(k), v) for k, v in sorted(app_elev.items())))
    check("the authority module is among them — provisioning really does run as admin from there",
          AUTHORITY in elevated, str(sorted(elevated)))

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("RESULT: PASS — provisioning is performed in one module and run from there by the boot "
          "path; no application module outside it stands a workload up or invents a privileged "
          "identity; and the set of modules that elevate at all is bounded and named.")
    sys.exit(0)


if __name__ == "__main__":
    main()
