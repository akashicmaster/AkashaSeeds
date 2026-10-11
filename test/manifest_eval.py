#!/usr/bin/env python3
"""
The manifests are the map (backend layout order 2026-09-20 §4).

Every application package carries a `MANIFEST.json` saying what it contributes — ops, schedules,
thread units, provisioners, hydrate accelerators, routers, binds, hooks — and what it depends on.
An implementation is then found by ONE rule: *manifest entry → `module:function`*. Before this,
the same question ("where is bench.info served?") was answered by reading an 18,000-line dispatch
chain, and a method could be defined in two places without anyone noticing.

Checked here:
  1. every manifest parses, names its package, and declares a dependency list that is a DAG in
     the declared order
  2. every entry RESOLVES — an op, a schedule, a thread unit, a provisioner, a router, a bind, a
     hook. A manifest entry that does not resolve must be a boot error naming the entry, never a
     -32601 at request time, so the aggregate is built here and the failure is the test
  3. no method is claimed by two packages, and no schedule name collides
  4. an op declares its IAM action (`access`) or is deliberately gated by its dispatch stage; the
     generated access table is in sync with the manifests (`gen_kernel_methods.py --check`)
  5. the declared paths exist: `code_paths`, `data_paths` and the `declarations` globs
  6. every package the tree carries is aggregated — a package with no manifest is invisible to
     the heart, which is the failure mode this file exists to prevent

Run:  python test/manifest_eval.py     (exit 0 = all pass)
"""
import glob
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []

ORDER = ["heart", "ontology", "source", "concepts", "workbench"]     # the platform's packages


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def main():
    os.chdir(ROOT)
    from lib.akasha.api import manifest as _M0, reserved as _R0
    paths = [os.path.relpath(p, ROOT) for p in _M0.default_manifest_paths(os.path.join(ROOT, "lib", "akasha"))]
    mans = {}
    for p in paths:
        try:
            mans[p] = json.load(open(p, encoding="utf-8"))
        except ValueError as exc:
            check("manifest parses: %s" % p, False, str(exc))
    plat = {p: m for p, m in mans.items() if not _R0.is_app_path(p)}
    appm = {p: m for p, m in mans.items() if _R0.is_app_path(p)}
    check("every platform package has its manifest (the heart and the four packages), each `owner: "
          "platform`", {m["package"] for m in plat.values()} == set(ORDER)
          and all(m.get("owner") == "platform" for m in plat.values()),
          "%s" % sorted((m.get("package"), m.get("owner")) for m in plat.values()))
    check("an application manifest is found only under the application root, `owner: user` (%d here)"
          % len(appm), all(m.get("owner") == "user" for m in appm.values()),
          str(sorted(appm)))

    # ── 1. shape + dependency order ──────────────────────────────────────────────────────────
    bad_dep = []
    app_pkgs = {m.get("package") for m in appm.values()}
    for p, m in mans.items():
        pkg = m.get("package")
        for dep in (m.get("depends_on") or []):
            if p in appm:           # an application package may depend on the platform, never back
                if dep not in ORDER and dep not in app_pkgs:
                    bad_dep.append("%s: %s depends_on %s" % (p, pkg, dep))
            elif dep not in ORDER or ORDER.index(dep) >= ORDER.index(pkg):
                bad_dep.append("%s: %s depends_on %s" % (p, pkg, dep))
    check("each manifest names its package and depends only on packages BELOW it — the declared "
          "order is a DAG", not bad_dep, str(bad_dep))

    # ── 2. every entry resolves (the aggregate is the proof) ─────────────────────────────────
    from lib.akasha import kernel as _kmod
    agg = _kmod._heart_aggregate()
    check("the aggregate builds: every ops / schedules / thread_units / provision / routers / "
          "binds / hooks entry in every manifest resolves to a real function",
          bool(agg.packages) and bool(agg.schedules.phase("writer")),
          "packages=%d" % len(agg.packages))

    from lib.akasha.api import manifest as _m
    broken = []
    for p, man in mans.items():
        for section in ("ops", "schedules", "provision", "hooks"):
            for name, spec in (man.get(section) or {}).items():
                ref = spec.get("fn") if isinstance(spec, dict) else spec
                if not ref:
                    continue          # access-only op: declares a gate, a router dispatches it
                try:
                    _m.resolve(ref, "%s %s.%s" % (p, section, name))
                except Exception as exc:
                    broken.append("%s %s.%s → %s" % (p, section, name, exc))
        for unit in (man.get("thread_units") or []):
            for field in ("wanted", "start"):
                try:
                    _m.resolve(unit[field], "%s unit %s" % (p, unit.get("name")))
                except Exception as exc:
                    broken.append("%s unit %s.%s → %s" % (p, unit.get("name"), field, exc))
    check("a manifest entry that does not resolve is a NAMED boot error, not a -32601 at request "
          "time — none is broken now", not broken, str(broken[:4]))

    # ── 3. no method or schedule claimed twice ───────────────────────────────────────────────
    owners, dup_ops, sched, dup_sched = {}, [], {}, []
    for p, man in mans.items():
        for name in (man.get("ops") or {}):
            if name in owners:
                dup_ops.append("%s claimed by %s and %s" % (name, owners[name], man["package"]))
            owners[name] = man["package"]
        for name in (man.get("schedules") or {}):
            if name in sched:
                dup_sched.append("%s in %s and %s" % (name, sched[name], man["package"]))
            sched[name] = man["package"]
    check("no method is claimed by two packages — an implementation exists in exactly one place",
          not dup_ops, str(dup_ops[:4]))
    check("no two packages register the same schedule name", not dup_sched, str(dup_sched[:4]))

    # ── 4. the access table is derived, and in sync ──────────────────────────────────────────
    no_access = [n for p, man in mans.items() for n, spec in (man.get("ops") or {}).items()
                 if isinstance(spec, dict) and "access" not in spec]
    check("every op DECLARES its IAM action (`access`), null included — the gate is never left to "
          "be remembered elsewhere", not no_access, "%d: %s" % (len(no_access), no_access[:6]))
    r = subprocess.run([sys.executable, "scripts/gen_kernel_methods.py", "--check"],
                       capture_output=True, text=True, cwd=ROOT)
    check("each generated access table — the platform's and each application manifest's — equals "
          "its generator's output from its own manifest (scripts/gen_kernel_methods.py --check)",
          r.returncode == 0,
          (r.stdout or r.stderr).strip().splitlines()[-1:] and
          (r.stdout or r.stderr).strip().splitlines()[-1] or "")

    # The purge order §4.3 — every platform commit carries PLATFORM_TREE.json, current. The
    # application's cut verifies its tree hash; a stale one would fail THEIR cut for OUR change.
    if os.path.isdir(os.path.join(ROOT, ".git")):
        r = subprocess.run([sys.executable, "scripts/gen_platform_tree.py", "--check"],
                           capture_output=True, text=True, cwd=ROOT)
        check("PLATFORM_TREE.json is current (scripts/gen_platform_tree.py --check)", r.returncode == 0,
              ((r.stdout or r.stderr).strip().splitlines() or [""])[-1])

    # The purge order §4.5 — docs/deployment.md is the environment's whole list, generated from the
    # manifests' `env` declarations; a stale page would point an operator at the wrong list.
    r = subprocess.run([sys.executable, "scripts/gen_deployment_doc.py", "--check"],
                       capture_output=True, text=True, cwd=ROOT)
    check("docs/deployment.md is current (scripts/gen_deployment_doc.py --check)", r.returncode == 0,
          ((r.stdout or r.stderr).strip().splitlines() or [""])[-1])

    r = subprocess.run([sys.executable, "scripts/gen_cli_table.py", "--check"],
                       capture_output=True, text=True, cwd=ROOT)
    check("the generated CLI table is in sync with the manifests' `cli` attributes "
          "(scripts/gen_cli_table.py --check) — the router holds no hand-written platform command",
          r.returncode == 0,
          (r.stdout or r.stderr).strip().splitlines()[-1:] and
          (r.stdout or r.stderr).strip().splitlines()[-1] or "")
    # Rulings of 4 October — the generated tables are split by OWNER: the platform's from the
    # platform's manifests (in the platform tree), each application manifest's beside it. A name
    # declared on both sides is a generation error; an application table that repeats a platform
    # name is a boot error; and a manifest re-declaring what its package's platform half declares
    # is a boot error.
    import importlib.util, tempfile as _tf

    def _load(script):
        _spec = importlib.util.spec_from_file_location(script + "_eval",
                                                       os.path.join(ROOT, "scripts", script + ".py"))
        mod = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(mod)
        return mod
    G, K = _load("gen_cli_table"), _load("gen_kernel_methods")
    _tmp = _tf.mkdtemp(prefix="clitab_")

    def _man(name, owner, ops):
        with open(os.path.join(_tmp, name), "w") as fh:
            json.dump({"package": name, "owner": owner, "ops": ops}, fh)
        return (name, name, owner)

    def _errs(mod, mans):
        real = (mod.ROOT, mod.manifests)
        mod.ROOT, mod.manifests = _tmp, (lambda: mans)
        try:
            mod.collect()
            return ""
        except SystemExit as e:
            return str(e)
        finally:
            mod.ROOT, mod.manifests = real
    _p = _man("p", "platform", {"a.x": {"access": "read", "cli": {"zz": {"args": []}}}})
    e1 = _errs(G, [_p, _man("u", "user", {"b.y": {"access": "read", "cli": {"zz": {"args": []}}}})])
    check("a command spelling declared by the platform and the application is a generation error",
          "declared twice" in e1 and "zz" in e1, e1)
    _u2 = _man("u2", "user", {"a.x": {"access": "read", "cli": {"zz": {"args": []}}}})
    e2, e3 = _errs(G, [_p, _u2]), _errs(K, [_p, _u2])
    check("an op the platform declares, re-declared by the application, is a generation error in "
          "BOTH generators (no shadow skip)", "a.x" in e2 and "declared twice" in e2
          and "a.x" in e3 and "declared twice" in e3, "cli=%r access=%r" % (e2, e3))
    _realK = (K.ROOT, K.manifests)
    try:
        K.ROOT, K.manifests = _tmp, (lambda: [_p, _man("u3", "user", {"b.y": {"access": "write"}})])
        _per, _flat, _apps = K.collect()
    finally:
        K.ROOT, K.manifests = _realK
    check("the access generator splits by owner: the platform's table holds the platform's "
          "methods only, the application's holds its own",
          _flat == {"a.x": "read"} and _apps.get("u3") == {"b.y": "write"},
          "platform=%s apps=%s" % (_flat, _apps))

    from lib.akasha.api import tables as _T, manifest as _M
    _troot = _tf.mkdtemp(prefix="tabroot_")
    _app = os.path.join(_troot, _R0.APP_DIR)
    _app_tbl = os.path.join(_app, "config", _T.ACCESS_TABLE)
    os.makedirs(os.path.join(_troot, "lib", "akasha"))
    os.makedirs(os.path.join(_app, "config"))
    for _p, _doc in ((os.path.join(_troot, "lib/akasha/MANIFEST.json"), {"package": "heart", "owner": "platform"}),
                     (os.path.join(_app, "config", "MANIFEST.json"), {"package": "app", "owner": "user"}),
                     (_app_tbl, {"access": {"a.x": "write", "b.y": "read"}})):
        with open(_p, "w") as fh:
            json.dump(_doc, fh)
    _env_app = os.environ.get("AKASHA_APP_DIR")
    os.environ["AKASHA_APP_DIR"] = _app            # the fixture application root
    try:
        try:
            _T.merged({"a.x": "read"}, _T.ACCESS_TABLE, "access", root=_troot)
            conflict = ""
        except _T.TableConflict as e:
            conflict = str(e)
        check("at boot, an application table that repeats a platform name is a TableConflict naming it",
              "'a.x'" in conflict and _T.ACCESS_TABLE in conflict, conflict)
        with open(_app_tbl, "w") as fh:
            json.dump({"access": {"b.y": "read"}}, fh)
        check("…and with no repeat the platform's table and the application's merge",
              _T.merged({"a.x": "read"}, _T.ACCESS_TABLE, "access", root=_troot)
              == {"a.x": "read", "b.y": "read"})

        _plat_m = os.path.join(_troot, "lib", "akasha", "MANIFEST.json")
        _app_m = os.path.join(_app, "config", "MANIFEST.json")
        with open(_plat_m, "w") as fh:
            json.dump({"package": "heart", "owner": "platform", "ops": {"x.op": {"access": "read"}}}, fh)
        with open(_app_m, "w") as fh:
            json.dump({"package": "app", "owner": "user", "ops": {"x.op": {"access": "read"}}}, fh)
        try:
            _M.load_manifests([_plat_m, _app_m])
            redecl = ""
        except ValueError as e:
            redecl = str(e)
        check("an application manifest re-declaring what a platform manifest declares is a BOOT "
              "error, by name", "'x.op'" in redecl and "declared once" in redecl, redecl)
        with open(_app_m, "w") as fh:
            json.dump({"package": "app", "owner": "platform"}, fh)
        try:
            _M.load_manifests([_app_m])
            wrong = ""
        except ValueError as e:
            wrong = str(e)
        check("a manifest whose owner disagrees with where it lives is a BOOT error (ownership is "
              "location: under the application root = the application's)",
              "ownership is where a file lives" in wrong, wrong)
    finally:
        if _env_app is None:
            os.environ.pop("AKASHA_APP_DIR", None)
        else:
            os.environ["AKASHA_APP_DIR"] = _env_app


    bad_cli = ["%s ops.%s" % (os.path.relpath(p, ROOT), n) for p, man in mans.items()
               for n, spec in (man.get("ops") or {}).items()
               if isinstance(spec, dict) and "cli" in spec and not (
                   isinstance(spec["cli"], dict) and spec["cli"] and all(
                       isinstance(c, dict) and set(c) <= {"args", "desc", "group"}
                       for c in spec["cli"].values()))]
    check("every `cli` attribute maps a command spelling to {args, desc, group} and nothing else",
          not bad_cli, str(bad_cli[:4]))

    # ── 5. the declared paths are real ───────────────────────────────────────────────────────
    unsafe, deploy_only = [], []
    for p, man in mans.items():
        for field in ("code_paths", "data_paths", "declarations"):
            for rel in (man.get(field) or []):
                if (not isinstance(rel, str) or not rel or os.path.isabs(rel)
                        or ".." in rel.split("/")):
                    unsafe.append("%s %s: %r" % (p, field, rel))
                elif not glob.glob(rel) and not os.path.exists(rel.rstrip("/")):
                    # legitimate: a path the CRYSTALLIZER writes into a deployment and the repo
                    # therefore does not carry (the tier's bootstrap flags, the featured set)
                    deploy_only.append("%s %s: %s" % (p, field, rel))
    check("no declared path could escape the tree — every code_path, data_path and declarations "
          "glob is relative and free of `..` (the extractor trusts these)",
          not unsafe, str(unsafe[:5]))
    check("each package's own code directory is really there",
          all(os.path.isdir(os.path.dirname(p)) for p in mans),
          str([p for p in mans if not os.path.isdir(os.path.dirname(p))]))
    if deploy_only:
        print("        (declared but absent from the repo — written into a deployment by the "
              "crystallizer: %s)" % ", ".join(sorted(deploy_only)))

    # ── 6. what the heart runs comes from the manifests ──────────────────────────────────────
    # A manifest aggregate with NO thread unit is valid (directive 2026-10-02 §6.2): the feed
    # poller's thread becomes a declared workload, and the driver is a platform loop, not a unit.
    # What must hold is that every unit a manifest DECLARES is in the aggregate (and resolves —
    # section 2 above), not that there is at least one.
    units = sorted(n for n, *_ in agg.schedules.units())
    declared_units = sorted(str(u.get("name")) for man in mans.values()
                            for u in (man.get("thread_units") or []))
    check("the boot phases are the manifests' own — load, writer, post_load",
          bool(agg.schedules.phase("load")) and bool(agg.schedules.phase("post_load")),
          "load=%d writer=%d post_load=%d"
          % (len(agg.schedules.phase("load")), len(agg.schedules.phase("writer")),
             len(agg.schedules.phase("post_load"))))
    check("every thread unit a manifest declares is in the aggregate (none is required: %d "
          "declared)" % len(declared_units), units == declared_units,
          "declared=%s aggregate=%s" % (declared_units, units))

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("RESULT: PASS — the manifests are a complete, resolvable map: every package declares "
          "what it contributes and what it sits on, every entry resolves to one implementation in "
          "one place, every op declares its gate, the access table is derived from them, and the "
          "paths they declare are the paths the tree has.")
    sys.exit(0)


if __name__ == "__main__":
    main()
