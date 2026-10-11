#!/usr/bin/env python3
"""
The owner map (platform-spec v1 §1): ownership is where a file lives.

Everything under the application root (`app/`) is the application's; everything else is the
platform's. `api.manifest.owner_of` is that one rule — there is no list (`platform_modules`,
`_OWNED_TREES` and `MANIFEST.platform.json` are gone).

Checked here:
  1. every manifest declares `owner`; the platform's five live outside the application root and say
     `platform`, the application's live under it and say `user`; no manifest carries
     `platform_modules`, and no `MANIFEST.platform.json` exists
  2. `owner_of` is the one rule, on fixture paths — including a relocated application root
  3. every tracked file resolves to exactly one owner
  4. the application does not reach into the platform's private members, declare a platform
     prefix, or get named by platform code (method or prefix) — scans over whatever application
     modules exist, so they hold vacuously with none
  5. the CLI table holds no hand-written or owed entries, and an op family lists under one group
  6. the registry's sharing rules, on classes the eval builds

Run:  python test/ownership_eval.py     (exit 0 = all pass)
"""
import ast
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []



# RATCHET — application → platform-private reaches. Measured 2026-09-26 at 46 (33 on a platform
# class instance, 13 through a platform base an application class inherits). A change may LOWER
# this line, never raise it; the audit of 2026-09-23 closes when it reads 0. The frontend's report
# that started it named three in `bench_station.py`; the scan found forty-six in six files.
PRIVATE_REACH_BOUND = 0       # CLOSED: 46 (09-26 AM) → 37 → 0 when the application switched to the public names

# (c) RATCHET — application Concept Models declaring a prefix the PLATFORM owns (a platform class's
# CONCEPT_PREFIX, or the first segment of an op a platform package's manifest declares). Measured
# 2026-09-26 at 5: `bench` ×3 (research, station, learning — the platform's `WorkbenchConcept` owns
# it from 4.17) and `feed` / `analysis` (the source package's `feed.poll`, `analysis.*` ops, which
# 4.11 moves). The registry REFUSES such a class the prefix; the application takes its own (its
# order) and this reaches 0.
PREFIX_COLLISION_BOUND = 0      # CLOSED: 5 → 3 (4.11 moved feed/analysis) → 0 (10-02 §2a: station.*, learning.*, research.*)

# (a) RATCHET — string constants in PLATFORM code that name an APPLICATION method (a method only a
# user-owned Concept Model registers). First measured over lib/ + scripts/ at 116; widened to api/,
# services/ and the launcher — where the portals and the CLI table live — it read 413, 325 of them
# the hand-written CLI table (4.6). Group 4 drives it to 0 (kernel dive list, genesis, render,
# portals, policy, the CSL validator's copy of the note ops — done; the CLI table, schedules,
# hydrate and the source engine — below).
APP_METHOD_NAMING_BOUND = 0       # CLOSED: 413 → 88 (4.6 CLI table) → 49 (lab drivers) → 43 (4.13) → 21 (4.11) → 17 (points) → 0 (pipeline points)

# (d) RATCHET — the APPLICATION's CLI entries the platform held for it, as data, in
# `api/cli_application_owed.json` (group 4, 4.6). The platform's own commands are GENERATED from
# the manifests' `cli` attributes; the application now declares its own the same way. CLOSED at 0
# (10-02 §2b): 277 commands + 20 short prefixes + 18 help labels = 315 → 0, the file deleted, and
# the router's reader of it removed — a file that reappears is read by nothing and fails below.
CLI_OWED_BOUND = 0

# (e) RATCHET — APPLICATION prefixes two application classes declare with no DECLARED primary
# (`CONCEPT_PRIMARY = True` on the one `get_class(prefix)` should answer with). Measured 10-02 at 1:
# `research` — `ResearchNotebook` (research.py) and `BenchResearchConcept` (bench_research.py, the
# research bench after §2a). Until one declares, the owner is the last to register (filename order),
# which a new file can change. CLOSED at 0 (10-03 item 2): `ResearchNotebook` declares itself primary —
# live `[registry] shared prefix=research … owner=ResearchNotebook declared=yes collisions=0`.
SHARED_PREFIX_UNDECLARED_BOUND = 0


# ── the scan (pure AST — nothing it reads is imported) ───────────────────────────────────────────
# A REACH is a call, in a USER-owned file, of an underscore method that a PLATFORM-owned class
# defines, on an object that is not `self`/`cls`/`super()`. The receiver's class is resolved
# statically, and only when it can be proved:
#
#     X(...)._m()                      X constructed right there
#     v = X(...); v._m()               a local bound to a constructor
#     self.a = X(...); self.a._m()     an attribute bound to a constructor
#     self.p._m() / self.f()._m()      a property / method whose body returns an X
#     v = self.f(); v._m()             a local bound to such an accessor
#     X._m()                           the class itself
#
# Two kinds, reported apart because they are fixed differently:
#   platform   the receiver IS a platform class instance            → a PUBLIC read/op there
#   inherited  the receiver is an application object whose          → the same public door; the
#              platform ancestor defines the private                   private came down a base
#
# What it cannot see — receivers built dynamically, passed in as arguments, fetched from a
# registry — makes the count a LOWER bound. It never counts a user class's own override.


def _src_files(root):
    """The platform's code and the application's MODULES the platform loads (its Concept Models
    and its pages)."""
    from lib.akasha.api import reserved as _R
    pats = ["lib/**/*.py", "scripts/**/*.py"] + [os.path.join(os.path.relpath(_R.root(k), root), "**", "*.py")
                                                 for k in ("concepts", "pages")]
    return sorted(f for p in pats for f in glob.glob(os.path.join(root, p), recursive=True)
                  if "__pycache__" not in f)


def _private_reach(root, owner_of_fn):
    own = {}
    for f in _src_files(root):
        rel = os.path.relpath(f, root)
        try:
            own[rel] = owner_of_fn(rel)
        except ValueError:
            pass
    trees = {}
    for rel in own:
        try:
            src = open(os.path.join(root, rel), encoding="utf-8").read()
            trees[rel] = (src, ast.parse(src))
        except Exception:
            pass
    # every class: (owner, own underscore methods, base names)
    classes = {}
    for rel, (_s, t) in trees.items():
        for c in (n for n in ast.walk(t) if isinstance(n, ast.ClassDef)):
            pm = {m.name for m in c.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))
                  and m.name.startswith("_") and not m.name.startswith("__")}
            # an underscore ALIAS of a public method (`_mk = mk`, 4.16) is still the private
            # spelling: an application calling it has not switched yet, and must still count
            pm |= {t.id for m in c.body if isinstance(m, ast.Assign) and isinstance(m.value, ast.Name)
                   for t in m.targets if isinstance(t, ast.Name) and t.id.startswith("_")
                   and not t.id.startswith("__")}
            bases = [b.id if isinstance(b, ast.Name) else getattr(b, "attr", "") for b in c.bases]
            classes.setdefault(c.name, (own[rel], pm, bases))

    def platform_privs(cn, seen=()):
        """Underscore methods a PLATFORM class in cn's ancestry defines and no USER class on the
        way overrides — what calling it on a cn instance actually reaches."""
        if cn not in classes or cn in seen:
            return set(), set()
        owner, pm, bases = classes[cn]
        got, masked = set(), set(pm) if owner == "user" else set()
        if owner == "platform":
            got |= pm
        for b in bases:
            g, m = platform_privs(b, seen + (cn,))
            got |= g
            masked |= m
        return got - masked, masked

    def ctor(node):
        if isinstance(node, ast.Call):
            fn = node.func
            nm = fn.id if isinstance(fn, ast.Name) else (fn.attr if isinstance(fn, ast.Attribute) else "")
            if nm in classes:
                return nm
        return ""

    hits = []
    for rel, (src, t) in trees.items():
        if own.get(rel) != "user":
            continue
        selfattr, accessor = {}, {}
        for fd in (n for n in ast.walk(t) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))):
            loc = {}
            for n in ast.walk(fd):
                if isinstance(n, ast.Assign) and ctor(n.value):
                    for tg in n.targets:
                        if isinstance(tg, ast.Name):
                            loc[tg.id] = ctor(n.value)
            for n in ast.walk(fd):
                if isinstance(n, ast.Return) and n.value is not None:
                    cn = ctor(n.value) or (loc.get(n.value.id) if isinstance(n.value, ast.Name) else "")
                    if cn:
                        accessor[fd.name] = (cn, any(isinstance(d, ast.Name) and d.id == "property"
                                                     for d in fd.decorator_list))
        for n in ast.walk(t):
            if isinstance(n, ast.Assign) and ctor(n.value):
                for tg in n.targets:
                    if isinstance(tg, ast.Attribute) and isinstance(tg.value, ast.Name) \
                            and tg.value.id == "self":
                        selfattr[tg.attr] = ctor(n.value)

        def via_self(v):
            if isinstance(v, ast.Attribute) and isinstance(v.value, ast.Name) and v.value.id == "self":
                if v.attr in accessor and accessor[v.attr][1]:
                    return accessor[v.attr][0]
                return selfattr.get(v.attr, "")
            if isinstance(v, ast.Call) and isinstance(v.func, ast.Attribute) \
                    and isinstance(v.func.value, ast.Name) and v.func.value.id == "self" \
                    and v.func.attr in accessor:
                return accessor[v.func.attr][0]
            return ""

        for fn in (n for n in ast.walk(t) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))):
            local = {}
            for n in ast.walk(fn):
                if isinstance(n, ast.Assign) and (ctor(n.value) or via_self(n.value)):
                    for tg in n.targets:
                        if isinstance(tg, ast.Name):
                            local[tg.id] = ctor(n.value) or via_self(n.value)
            for n in ast.walk(fn):
                if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)):
                    continue
                a, v = n.func, n.func.value
                if isinstance(v, ast.Name) and v.id in ("self", "cls"):
                    continue
                cn = (ctor(v) or via_self(v)
                      or (local.get(v.id, "") if isinstance(v, ast.Name) else "")
                      or (v.id if isinstance(v, ast.Name) and v.id in classes else ""))
                if not cn:
                    continue
                reach, _m = platform_privs(cn)
                if a.attr in reach:
                    kind = "platform" if classes[cn][0] == "platform" else "inherited"
                    hits.append((rel, n.lineno, cn, a.attr, kind))
    return sorted(set(hits))



def _prefix_collisions(root, owner_of_fn):
    """(prefix, module, class, platform-owner) for every USER Concept Model whose CONCEPT_PREFIX a
    platform class or a platform package's manifest op also claims. Pure AST + JSON."""
    import json as _json
    plat_prefix = {}
    for rel in ("lib/akasha/MANIFEST.json", "lib/akasha/ontology/MANIFEST.json",
                "lib/akasha/source/MANIFEST.json", "lib/akasha/workbench/MANIFEST.json"):
        try:
            m = _json.load(open(os.path.join(root, rel), encoding="utf-8"))
        except Exception:
            continue
        if m.get("owner") == "platform":
            for op in (m.get("ops") or {}):
                if "." in op:
                    plat_prefix.setdefault(op.split(".", 1)[0], "manifest:%s" % m.get("package"))
    user_decl = []
    for f in sorted(glob.glob(os.path.join(root, "lib", "akasha", "concepts", "*.py"))):
        rel = os.path.relpath(f, root)
        try:
            own = owner_of_fn(rel)
            t = ast.parse(open(f, encoding="utf-8").read())
        except Exception:
            continue
        for c in (n for n in t.body if isinstance(n, ast.ClassDef)):
            for st in c.body:
                if (isinstance(st, ast.Assign) and any(getattr(x, "id", "") == "CONCEPT_PREFIX"
                                                       for x in st.targets)
                        and isinstance(st.value, ast.Constant)):
                    if own == "platform":
                        plat_prefix["%s" % st.value.value] = "class:%s" % c.name
                    else:
                        user_decl.append((st.value.value, os.path.basename(rel)[:-3], c.name))
    return sorted((p, mod, cn, plat_prefix[p]) for p, mod, cn in user_decl if p in plat_prefix)


def _platform_naming_app_methods(root, reg, owner_of_fn):
    """(file, line, method) — a string constant in PLATFORM code equal to a method only an
    APPLICATION class registers. Generated tables (a `GENERATED` header) are exempt by construction."""
    from lib.akasha.concepts.registry import is_platform_class
    app_only = {m for m, v in reg._handlers.items() if not is_platform_class(v[0])}
    out = []
    extra = [os.path.join(root, "akasha.py")] + sorted(
        f for p in ("api/**/*.py", "services/**/*.py")
        for f in glob.glob(os.path.join(root, p), recursive=True) if "__pycache__" not in f)
    for f in _src_files(root) + extra:
        rel = os.path.relpath(f, root)
        if not rel.endswith(".py") or rel.startswith(("test/", "scripts/user/")):
            continue
        try:
            if owner_of_fn(rel) != "platform":
                continue
            src = open(f, encoding="utf-8").read()
        except Exception:
            continue
        if "GENERATED" in src[:600]:
            continue
        try:
            t = ast.parse(src)
        except SyntaxError:
            continue
        for n in ast.walk(t):
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value in app_only:
                out.append((rel, n.lineno, n.value))
    return sorted(out)


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def main():
    os.chdir(ROOT)
    from lib.akasha.api import manifest as M, reserved as RES
    from lib.akasha import kernel as _kmod
    from lib.akasha.api.manifest import owner_of
    paths = [os.path.relpath(p, ROOT) for p in M.default_manifest_paths(os.path.join(ROOT, "lib", "akasha"))]
    mans = {p: json.load(open(p, encoding="utf-8")) for p in paths}

    # ── 1. the manifests ─────────────────────────────────────────────────────────────────────
    missing = [p for p, m in mans.items() if m.get("owner") not in ("platform", "user")]
    check("every manifest declares `owner: platform | user`", not missing, str(missing))
    plat = {m["package"]: m.get("owner") for p, m in mans.items() if not RES.is_app_path(p)}
    check("the platform's five manifests (heart, ontology, source, concepts, workbench) live outside "
          "the application root and say `platform`",
          set(plat) == {"heart", "ontology", "source", "concepts", "workbench"}
          and set(plat.values()) == {"platform"}, str(plat))
    appm = {p: m.get("owner") for p, m in mans.items() if RES.is_app_path(p)}
    check("every application manifest lives under the application root and says `user` (%d)" % len(appm),
          set(appm.values()) <= {"user"}, str(appm))
    check("no manifest carries `platform_modules`, and no MANIFEST.platform.json exists",
          not any("platform_modules" in m for m in mans.values())
          and not glob.glob(os.path.join(ROOT, "**", "MANIFEST.platform.json"), recursive=True))
    msrc = open(os.path.join(ROOT, "lib", "akasha", "api", "manifest.py"), encoding="utf-8").read()
    check("the owner map is no list: `_OWNED_TREES` and `platform_modules` are not in manifest.py",
          "_OWNED_TREES" not in msrc and "platform_modules" not in msrc)

    # ── 2. one rule, on fixture paths ────────────────────────────────────────────────────────
    A = RES.app_root()
    for path, want in ((A + "/concepts/model.py", "user"), (A + "/config/MANIFEST.json", "user"),
                       (A, "user"), (A + "x/y.py", "platform"), ("lib/akasha/kernel.py", "platform"),
                       ("lib/akasha/concepts/base.py", "platform"), ("scripts/gen_lexicon.py", "platform"),
                       ("ontology/lexicon/PACK.json", "platform"), ("config/identity/idsets.json", "platform"),
                       ("test/ownership_eval.py", "platform")):
        check("owner_of(%s) = %s" % (os.path.relpath(path, ROOT), want), owner_of(None, path) == want,
              owner_of(None, path))
    import tempfile
    _alt = tempfile.mkdtemp(prefix="relocated_app_")
    _prev = os.environ.get("AKASHA_APP_DIR")
    os.environ["AKASHA_APP_DIR"] = _alt
    try:
        check("a relocated application root (AKASHA_APP_DIR) is the application's, wherever it is",
              owner_of(None, os.path.join(_alt, "concepts", "m.py")) == "user"
              and owner_of(None, os.path.join(ROOT, RES.APP_DIR, "concepts", "m.py")) == "platform")
    finally:
        if _prev is None:
            os.environ.pop("AKASHA_APP_DIR", None)
        else:
            os.environ["AKASHA_APP_DIR"] = _prev

    # ── 3. every tracked file resolves to exactly one owner ──────────────────────────────────
    import subprocess as _sp
    files = _sp.run(["git", "ls-files"], capture_output=True, text=True, cwd=ROOT).stdout.split()
    owners = {f: owner_of(None, f) for f in files}
    check("every tracked file resolves to exactly one owner (%d application, %d platform)"
          % (sum(1 for v in owners.values() if v == "user"), sum(1 for v in owners.values() if v == "platform")),
          set(owners.values()) <= {"user", "platform"} and all(
              (v == "user") == RES.is_app_path(f) for f, v in owners.items()))
    agg = _kmod._heart_aggregate()

    # ── 6. RATCHET: the application does not reach into the platform's private members ───────
    rows = _private_reach(ROOT, lambda p: owner_of(agg, p))
    n_pf = sum(1 for r in rows if r[4] == "platform")
    by_file = {}
    for r in rows:
        by_file[r[0]] = by_file.get(r[0], 0) + 1
    for r in rows:
        print("        reach  %s:%d  %s.%s  [%s]" % r)
    check("RATCHET — %d application → platform-private reaches (%d on a platform instance, %d "
          "inherited; bound %d; may go down, never up; the audit closes at 0)"
          % (len(rows), n_pf, len(rows) - n_pf, PRIVATE_REACH_BOUND),
          len(rows) <= PRIVATE_REACH_BOUND,
          "over by %d — %s" % (len(rows) - PRIVATE_REACH_BOUND, by_file)
          if len(rows) > PRIVATE_REACH_BOUND else str(by_file))

    # ── 7. (c) an application prefix never equals a platform prefix — and the registry refuses it ─
    coll = _prefix_collisions(ROOT, lambda p: owner_of(agg, p))
    for c in coll:
        print("        prefix  %s  %s (%s) — platform owner: %s" % c)
    check("RATCHET (c) — %d application Concept Model(s) declare a PLATFORM prefix (bound %d; may "
          "go down, never up; closes at 0)" % (len(coll), PREFIX_COLLISION_BOUND),
          len(coll) <= PREFIX_COLLISION_BOUND, str(coll))
    from lib.akasha.concepts.registry import build_active, is_platform_class
    _reg = build_active()
    _cls_owned = {c[0] for c in coll if c[3].startswith("class:")}
    check("…and the registry REFUSES each one a prefix a platform class owns: `get_class(prefix)` "
          "answers with the platform class, never an application one",
          all(_reg.get_class(p) is not None and is_platform_class(_reg.get_class(p))
              for p in _cls_owned), {p: getattr(_reg.get_class(p), "__name__", None) for p in _cls_owned})
    _ref = {(r["prefix"], r["module"]) for r in _reg.refusals()}
    check("…and says so: every class-owned collision is on the registry's refusal list",
          all((c[0], c[1]) in _ref for c in coll if c[3].startswith("class:")), sorted(_ref))
    _plat_methods = {"%s.%s" % (pfx, sfx) for pfx, own in _reg._prefix_owner.items()
                     if is_platform_class(own) for sfx in (own.CONCEPT_METHODS or {})}
    _stolen = sorted(m for m in _plat_methods
                     if m in _reg._handlers and not is_platform_class(_reg._handlers[m][0]))
    check("…and every method a platform class declares is served by a platform class (%d), never "
          "by an application class that spread it into its own table" % len(_plat_methods),
          not _stolen, str(_stolen))

    # ── 8. (a) platform code does not name an application method ─────────────────────────────
    named = _platform_naming_app_methods(ROOT, _reg, lambda p: owner_of(agg, p))
    for n in named:
        print("        names  %s:%d  %s" % n)
    check("RATCHET (a) — %d place(s) in platform code name an application method (bound %d; "
          "closes at 0 — a generated table is exempt by construction)"
          % (len(named), APP_METHOD_NAMING_BOUND), len(named) <= APP_METHOD_NAMING_BOUND)

    # ── 8b. (a) …nor reaches an application Concept Model by its PREFIX ───────────────────────
    _app_prefixes = {pfx for pfx, own in _reg._prefix_owner.items() if not is_platform_class(own)}
    _by_prefix = []
    for f in _src_files(ROOT) + [os.path.join(ROOT, "akasha.py")] + sorted(
            glob.glob(os.path.join(ROOT, "api", "**", "*.py"), recursive=True)):
        rel = os.path.relpath(f, ROOT)
        if not rel.endswith(".py") or rel.startswith(("test/", "scripts/user/")) or "__pycache__" in rel:
            continue
        try:
            if owner_of(agg, rel) != "platform":
                continue
            t = ast.parse(open(f, encoding="utf-8").read())
        except Exception:
            continue
        for n in ast.walk(t):
            if isinstance(n, ast.Call) and getattr(n.func, "attr", getattr(n.func, "id", "")) == "concept_class" \
                    and len(n.args) >= 2 and isinstance(n.args[1], ast.Constant) \
                    and n.args[1].value in _app_prefixes:
                _by_prefix.append("%s:%d %s" % (rel, n.lineno, n.args[1].value))
    check("(a) no platform file reaches an APPLICATION Concept Model by prefix "
          "(`concept_class(…, \"<app prefix>\")`) — the platform's needs are platform "
          "containers or declared points (4.14)", not _by_prefix, str(_by_prefix))

    # ── 9. (d) the CLI: generated for the platform, owed for the application ─────────────────
    import importlib
    _ct = importlib.import_module("api.cli_table")
    _owed_path = os.path.join(ROOT, "api", "cli_application_owed.json")
    check("(d) closed: `api/cli_application_owed.json` does not exist", not os.path.isfile(_owed_path))
    _readers = [f for f in ("api/router.py", "api/cli_table.py", "scripts/gen_cli_table.py")
                if "cli_application_owed.json" in open(os.path.join(ROOT, f), encoding="utf-8").read()
                and "_load_owed" in open(os.path.join(ROOT, f), encoding="utf-8").read()]
    check("…and nothing reads it: the router's owed loader is gone (a file that reappears is inert)",
          not _readers and "_OWED" not in open(os.path.join(ROOT, "api", "router.py"),
                                               encoding="utf-8").read(), str(_readers))
    owed = json.load(open(_owed_path, encoding="utf-8")) if os.path.isfile(_owed_path) else {}
    o_cmds = owed.get("commands") or {}
    n_owed = len(o_cmds) + len(owed.get("prefixes") or {}) + len(owed.get("labels") or {})
    router_src = open(os.path.join(ROOT, "api", "router.py"), encoding="utf-8").read()
    _rt = ast.parse(router_src)
    _literal_tables = [n.targets[0].id for n in ast.walk(_rt)
                       if isinstance(n, ast.Assign) and len(n.targets) == 1
                       and isinstance(n.targets[0], ast.Name)
                       and n.targets[0].id in ("COMMAND_SPECS", "CONCEPT_PREFIXES", "CONCEPT_LABELS")
                       and isinstance(n.value, ast.Dict) and any(k is not None for k in n.value.keys)]
    _ann = [n.target.id for n in ast.walk(_rt)
            if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name)
            and n.target.id in ("COMMAND_SPECS", "CONCEPT_PREFIXES", "CONCEPT_LABELS")
            and isinstance(n.value, ast.Dict) and any(k is not None for k in n.value.keys)]
    check("the router holds NO hand-written command, prefix or label table — its tables are the "
          "generated one plus the owed data", not (_literal_tables + _ann), str(_literal_tables + _ann))
    # An owed entry is DEAD once the platform or the application declares the same spelling.
    _declared_cli = {}
    for _p, _m in mans.items():
        for _meth, _spec in (_m.get("ops") or {}).items():
            for _cmd in ((_spec.get("cli") or {}) if isinstance(_spec, dict) else {}):
                _declared_cli[_cmd] = _meth
    dead = sorted(c for c in o_cmds if c in _ct.CLI_SPECS or c in _declared_cli)
    check("no owed command is also DECLARED (a `cli` on some op) — a declared one is deleted from "
          "the owed file in the same commit", not dead, str(dead[:8]))
    plat_owed = sorted(c for c, sp in o_cmds.items()
                       if (sp.get("method") or c) in _reg._handlers
                       and is_platform_class(_reg._handlers[sp.get("method") or c][0]))
    check("every owed command reaches an APPLICATION method — a platform command is never owed, it "
          "is declared", not plat_owed, str(plat_owed[:8]))
    # One help group per op family (10-02 frontend item 2): with the short prefixes gone, a command
    # whose `cli` names no `group` lists under its method's own prefix — `pr.export` (pres.export)
    # sat under `pres` while its eight siblings sat under `presentation`.
    import collections as _co
    from api.router import CommandRouter as _R
    _fam = _co.defaultdict(lambda: _co.defaultdict(list))
    for _c, _sp in _R.COMMAND_SPECS.items():
        _fam[str(_sp.get("method") or _c).split(".", 1)[0]][_R._get_concept_group(_c)].append(_c)
    _split = {p: {g: v[:3] for g, v in d.items()} for p, d in _fam.items() if len(d) > 1}
    check("every op family lists under ONE help group (a `cli` that names no `group` beside "
          "siblings that do is split off under its method prefix)", not _split, str(_split)[:300])
    check("RATCHET (d) — %d application CLI entr(y/ies) the platform still holds as data (%d "
          "commands, %d prefixes, %d labels; bound %d; closes at 0)"
          % (n_owed, len(o_cmds), len(owed.get("prefixes") or {}), len(owed.get("labels") or {}),
             CLI_OWED_BOUND), n_owed <= CLI_OWED_BOUND)

    # ── 10. (e) an application prefix two application classes share ───────────────────────────
    shared = _reg.shared_prefixes()
    for sp in shared:
        print("        shared  %s  %s owner=%s declared=%s" % (sp["prefix"], ",".join(sp["classes"]),
                                                            sp["owner"], sp["declared"]))
    check("no application method is shadowed by another application class sharing its prefix "
          "(the registry keeps the first and refuses the second, by name)",
          not _reg.shadow_refusals, str(_reg.shadow_refusals[:4]))
    _undecl = [sp["prefix"] for sp in shared if not sp["declared"]]
    check("RATCHET (e) — %d shared application prefix(es) with no declared primary (bound %d; "
          "closes at 0)" % (len(_undecl), SHARED_PREFIX_UNDECLARED_BOUND),
          len(_undecl) <= SHARED_PREFIX_UNDECLARED_BOUND, str(_undecl))

    # (f) 10-02 frontend item 4 — §2a gave the bench kinds their own prefixes (station.*, learning.*,
    # research.*). No PLATFORM file may still name one of their methods under the old `bench.`
    # spelling, in code OR in a comment: the names are DERIVED — every method a bench KIND (an
    # application subclass of the class that owns `bench`) defines and `bench.` does not route.
    _moved = set()
    _bench = _reg.get_class("bench")
    for _cls in {c for _p, (c, *_r) in _reg._handlers.items()}:
        if is_platform_class(_cls) or _bench is None or not issubclass(_cls, _bench):
            continue
        for _sfx in (getattr(_cls, "CONCEPT_METHODS", {}) or {}):
            if not _reg.can_handle("bench." + _sfx):
                _moved.add("bench." + _sfx)
    _stale = []
    _tok = re.compile(r"(?<![\w:./-])bench\.[a-z_]+(?:\.[a-z_]+)*")
    for _base in ("lib/akasha", "api", "scripts", "akasha.py"):
        _ap = os.path.join(ROOT, _base)
        _files = [_ap] if _ap.endswith(".py") else [os.path.join(d, f) for d, _, fs in os.walk(_ap)
                                                     for f in fs if f.endswith(".py")]
        for _f in _files:
            _rel = os.path.relpath(_f, ROOT)
            if "__pycache__" in _rel or owner_of(agg, _rel) != "platform":
                continue
            for _n, _line in enumerate(open(_f, encoding="utf-8"), 1):
                for _t in _tok.findall(_line):
                    if _t in _moved:
                        _stale.append("%s:%d %s" % (_rel, _n, _t))
    check("no platform file names a bench-kind method by its pre-§2a `bench.` spelling (%d derived "
          "names: `bench.air.ls`, `bench.publish`, `bench.train`, …)" % len(_moved),
          not _stale, str(_stale[:6]))

    # …and the rules themselves, on a registry of the eval's own (application-module classes)
    from lib.akasha.concepts.registry import ConceptRegistry as _CR

    def _app(name, methods, primary=False):
        ns = {"CONCEPT_PREFIX": "zz_shared", "CONCEPT_METHODS": {m: "op_x" for m in methods},
              "op_x": lambda self: None,
              "__module__": RES.app_package() + ".concepts.zz_" + name.lower()}
        if primary:
            ns["CONCEPT_PRIMARY"] = True
        return type(name, (), ns)
    A, B = _app("Alpha", ["a", "both"]), _app("Beta", ["b", "both"])
    r = _CR(); r.register(A); r.register(B)
    check("a method two application classes define stays with the FIRST; the second is refused it",
          r._handlers["zz_shared.both"][0] is A and r._handlers["zz_shared.b"][0] is B
          and [m for m, *_ in r.shadow_refusals] == ["zz_shared.both"], str(r.shadow_refusals))
    P, Q = _app("Prim", ["p"], primary=True), _app("Later", ["q"])
    r2 = _CR(); r2.register(P); r2.register(Q)
    r3 = _CR(); r3.register(Q); r3.register(P)
    check("the class that DECLARES `CONCEPT_PRIMARY` owns the prefix whatever the order",
          r2.get_class("zz_shared") is P and r3.get_class("zz_shared") is P
          and r2.shared_prefixes()[0]["declared"] is True)
    r4 = _CR(); r4.register(A); r4.register(Q)
    check("…with no declaration the owner is the last to register, reported `declared: False`",
          r4.get_class("zz_shared") is Q and r4.shared_prefixes()[0]["declared"] is False)

    print()
    if _fails:
        print(f"FAILED ({len(_fails)}): " + "; ".join(_fails)); sys.exit(1)
    print("RESULT: PASS — ownership is location: one rule, no list. Every manifest and every file "
          "resolves to one owner, and the application neither reaches into the platform nor is named "
          "by it.")
    sys.exit(0)


if __name__ == "__main__":
    main()
