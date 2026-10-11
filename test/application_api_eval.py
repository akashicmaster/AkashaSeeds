#!/usr/bin/env python3
"""
The Application API release (the purge order, §1 — P1).

An application imports only `lib.akasha.api.<topic>`. This eval holds the release:

  1. the generated sections of `docs/platform/SPEC.md` are what the name table says (`--check`), and
     the spec's title carries `lib.akasha.api.spec.NAME`;
  2. every name resolves, has a contract, and is public (no `_` name is exported);
  3. a topic module imports nothing until a name is used (lazy — no import cycle can form, and an
     application pays for what it uses);
  4. COVERAGE: every name an application module imports TODAY from a platform module that is not the
     API has a replacement — the identical object under an API name, or a Concept Model reachable by
     its declared prefix (`concepts.model`), or an entry of the documented no-API list. (This is what
     makes the application's A1 a mechanical change.) The count of such import sites is printed: it
     is what `wiring_eval` closes at P4;
  5. `concepts.model(session, prefix)` returns a working model instance on a real cell;
  6. the reserved concept names, the declaration roots and the owned fields are published.

Run:  python test/application_api_eval.py     (exit 0 = all pass)
"""
import ast
import glob
import hashlib
import importlib
import inspect
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []

NO_API_MODULES = ("lib.akasha.canon", "lib.akasha.concepts._radu_gate")
# names whose replacement is a REDESIGN, not the same object: (module, name) → the API name
REDESIGNED = {
    ("lib.akasha.kernel", "KernelDispatcher"): "client.embedded",
    ("api.gateway", "AkashaGateway"): "client.embedded",
    ("api.gateway", "gateway"): "client.embedded",
    ("lib.akasha.jcl.validator", "_BLOCKED_METHODS"): "jobs.is_blocked",
    ("lib.akasha.jcl.validator", "_BLOCKED_PREFIXES"): "jobs.is_blocked",
}


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _mod_path(mod):
    base = mod.replace(".", "/")
    for c in (base + ".py", base + "/__init__.py"):
        if os.path.exists(c):
            return c
    return None


def application_imports():
    """[(file, line, module, name)] — names an application module the platform loads imports from a PLATFORM-owned module
    outside `lib/akasha/api/` (`import m as x; x.name` counted by attribute)."""
    from lib.akasha import kernel as K
    from lib.akasha.api import manifest as M
    agg = K._heart_aggregate()

    def owner(p):
        try:
            return M.owner_of(agg, p)
        except Exception:
            return "?"

    def platform_mod(mod):
        p = _mod_path(mod)
        return bool(p) and owner(p) == "platform" and not p.startswith("lib/akasha/api/")
    out = []
    # the application's MODULES the platform loads: its Concept Models and its pages (its scripts,
    # seeds and evals are tools that may boot a kernel like any operator script)
    from lib.akasha.api import reserved as _R
    files = [os.path.relpath(f, ROOT) for k in ("concepts", "pages")
             for f in glob.glob(os.path.join(_R.root(k), "**", "*.py"), recursive=True)
             if "__pycache__" not in f]
    for f in sorted(files):
        if owner(f) != "user":
            continue
        try:
            tree = ast.parse(open(f, encoding="utf-8").read())
        except Exception:
            continue
        aliases = {}
        for n in ast.walk(tree):
            if isinstance(n, ast.ImportFrom) and n.module and n.level == 0:
                for a in n.names:
                    sub = n.module + "." + a.name
                    if _mod_path(sub):
                        if platform_mod(sub):
                            aliases[a.asname or a.name] = sub
                    elif platform_mod(n.module):
                        out.append((f, n.lineno, n.module, a.name))
            elif isinstance(n, ast.Import):
                for a in n.names:
                    if platform_mod(a.name):
                        aliases[a.asname or a.name] = a.name
        for n in ast.walk(tree):
            if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id in aliases:
                out.append((f, n.lineno, aliases[n.value.id], n.attr))
    return out


def main():
    print("=" * 78)
    print("The Application API release (P1)")
    print("=" * 78)
    from lib.akasha.api.exports import EXPORTS, resolve

    print("\n  ── 1. the published list ──")
    r = subprocess.run([sys.executable, "scripts/gen_application_api.py", "--check"], cwd=ROOT,
                       capture_output=True, text=True, timeout=300)
    check("docs/platform/SPEC.md's generated sections are up to date with the name table",
          r.returncode == 0, (r.stdout + r.stderr).strip()[-160:])
    from lib.akasha.api import spec as _spec
    _head = open(os.path.join(ROOT, "docs", "platform", "SPEC.md"), encoding="utf-8").readline()
    check("the specification names its version (%s) and the changelog has its entry" % _spec.NAME,
          _spec.NAME in _head and ("## " + _spec.NAME) in open(
              os.path.join(ROOT, "docs", "platform", "CHANGELOG.md"), encoding="utf-8").read(), _head.strip())

    print("\n  ── 2. every name resolves, has a contract, is public ──")
    bad, nocontract, private = [], [], []
    for topic, names in EXPORTS.items():
        for n, (tgt, contract) in names.items():
            try:
                resolve(topic, n)
            except Exception as exc:
                bad.append("%s.%s: %s" % (topic, n, exc))
            if len(str(contract or "").strip()) < 12:
                nocontract.append("%s.%s" % (topic, n))
            if n.startswith("_"):
                private.append("%s.%s" % (topic, n))
    total = sum(len(v) for v in EXPORTS.values())
    check("all %d names in %d topics resolve" % (total, len(EXPORTS)), not bad, str(bad[:4]))
    check("every name carries a contract", not nocontract, str(nocontract[:6]))
    check("no private (`_`) name is exported", not private, str(private))

    print("\n  ── 3. lazy ──")
    probe = subprocess.run(
        [sys.executable, "-c",
         "import sys; sys.path.insert(0, %r)\n"
         "import lib.akasha.api.process, lib.akasha.api.vision, lib.akasha.api.jobs\n"
         "print('LOADED', [m for m in ('lib.akasha.memtrace', 'lib.akasha.source.vision', "
         "'lib.akasha.jcl.job') if m in sys.modules])" % ROOT],
        cwd=ROOT, capture_output=True, text=True, timeout=120)
    loaded = next((ln for ln in probe.stdout.splitlines() if ln.startswith("LOADED")), "?")
    check("importing a topic module imports none of the modules behind it", loaded == "LOADED []",
          loaded or probe.stderr[-160:])

    print("\n  ── 4. coverage: today's application imports all have an API ──")
    ident = {}
    for topic, names in EXPORTS.items():
        for n in names:
            try:
                ident[id(resolve(topic, n))] = "%s.%s" % (topic, n)
            except Exception:
                pass
    sites = application_imports()
    uncovered = []
    via = {"api": 0, "model": 0, "no_api": 0, "redesign": 0}
    for f, line, mod, name in sites:
        if (mod, name) in REDESIGNED:
            via["redesign"] += 1
            continue
        if mod in NO_API_MODULES or "%s.%s" % (mod, name) in NO_API_MODULES:
            via["no_api"] += 1                     # `from lib.akasha import canon` too (deleted, §3)
            continue
        try:
            obj = getattr(importlib.import_module(mod), name)
        except Exception:
            uncovered.append("%s:%d %s.%s (does not resolve)" % (f, line, mod, name))
            continue
        if id(obj) in ident:
            via["api"] += 1
        elif inspect.isclass(obj) and getattr(obj, "CONCEPT_PREFIX", None):
            via["model"] += 1
        else:
            uncovered.append("%s:%d %s.%s" % (f, line, mod, name))
    print("        %d application uses of non-API platform names in %d files: %d → an API name, "
          "%d → concepts.model(prefix), %d → a redesigned API name, %d → no API by design"
          % (len(sites), len({s[0] for s in sites}), via["api"], via["model"], via["redesign"],
             via["no_api"]))
    check("every one has a replacement in the API", not uncovered,
          "%d: %s" % (len(uncovered), uncovered[:5]))

    print("\n  ── 5. concepts.model on a cell ──")
    from lib.akasha.kernel import KernelDispatcher
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="apiev_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin", "data": {"user_name": "admin",
                           "passphrase": hashlib.sha256(b"pw").hexdigest()}}, "id": "g"}, "local")
    from lib.akasha.api import concepts as C
    m = C.model(k.manager.get_session("admin"), "source")
    check("concepts.model(session, 'source') is the source engine's model, bound to the session",
          m is not None and getattr(m, "CONCEPT_PREFIX", "") == "source" and callable(getattr(m, "op_status", None)))
    check("…and an undeclared prefix gives None", C.model(k.manager.get_session("admin"), "no-such") is None)
    from lib.akasha.api import client as CL, jobs as J
    gw = CL.embedded(tempfile.mkdtemp(prefix="apiev_emb_"), "seeds", load_ontology=False)
    pr = gw.dispatch({"jsonrpc": "2.0", "method": "sys.ping", "params": {}, "id": "p"})
    check("client.embedded(…, load_ontology=False) is a working in-process cell (no class patched)",
          "error" not in pr and type(gw.kernel_client).__name__ == "EmbeddedCellNoPacks"
          and KernelDispatcher._boot_load_ontology is not type(gw.kernel_client)._boot_load_ontology,
          str(pr)[:100])
    check("jobs.is_blocked answers the JCL blocklist (job.submit is blocked, w is not)",
          J.is_blocked("job.submit") and not J.is_blocked("w"))

    print("\n  ── 6. reserved names, declaration roots, owned fields ──")
    from lib.akasha.api import declarations as D, fields as F
    check("RESERVED_CONCEPTS names the source engine's pool and item concepts",
          C.RESERVED_CONCEPTS.get("source_pool") == "source" and C.RESERVED_CONCEPTS.get("source_item") == "source")
    from lib.akasha.api import reserved as _R
    check("every declaration root resolves under the application root (and nowhere else)",
          all(D.root(k_, "b").startswith(_R.app_root() + os.sep) for k_ in D.ROOTS),
          str({k_: D.root(k_) for k_ in D.ROOTS if "%s" not in D.ROOTS[k_]}))
    check("the owned fields are listed", any(x["field"] == "status" for x in F.owned()), str(F.owned()))
    print()
    if _fails:
        print("FAILED (%d): %s" % (len(_fails), "; ".join(_fails)))
        sys.exit(1)
    print("RESULT: PASS — the Application API is published (SPEC.md §3 generated from one name "
          "table), every name resolves with a contract, the topic modules are lazy, and every name the "
          "application imports from the platform today has its replacement.")
    sys.exit(0)


if __name__ == "__main__":
    main()
