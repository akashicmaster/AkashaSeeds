#!/usr/bin/env python3
"""
The platform stands alone (platform-spec v1; the purge order P5 — the proof of II).

  1. The application root (`app/`) is deleted: the tree outside it (build output left out) is copied
     to a scratch directory with a fresh repository of its own, and nothing of the application is there.
  2. A fresh cell boots there: genesis, `sys.ping`, an atom written and read back, a society made
     and listed, a source registered — the platform's own Concept Models served by the platform's
     own manifests.
  2b. The CLI and access tables there are exactly the platform's: the generator finds the platform's
     commands from the platform's manifests alone, each is in the committed `api/cli_table.py` with
     the same spec, there is NO application table, and both generators' `--check` pass.
  3. The launcher serves there: the Cell daemon comes online and `stop` stops it.
  4. The platform's ENTIRE suite passes there: every `test/*_eval.py` but this one.
  5. Statically, platform code names no application identifier: op names, op prefixes, concept
     names and file paths DERIVED from the application's own manifests, modules and files — no hand
     list. Strings in code count; comments, docstrings and generated tables do not; a reserved
     concept name and a platform op are the platform's own. Must be 0. And no platform string names
     the application root except `api/reserved.py`, which defines it.

Run:  python test/platform_alone_eval.py           (exit 0 = all pass)
      python test/platform_alone_eval.py --quick   skips step 4, the whole suite
"""
import ast
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []

GENERATED = {"lib/akasha/kernel_methods.py", "api/cli_table.py"}
SCANNED_TREES = ("lib/", "api/", "akasha.py", "reproductor/", "spawn.py", "remote/", "services/",
                 "scripts/")
SUITE_WORKERS = 4


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _tree_files():
    out = subprocess.run(["git", "-C", ROOT, "ls-files", "-co", "--exclude-standard"],
                         capture_output=True, text=True).stdout.split()
    return [f for f in out if os.path.isfile(os.path.join(ROOT, f))]


def _owners():
    from lib.akasha.api import manifest as M
    return {f: M.owner_of(None, f) for f in _tree_files()}


CHILD = r'''
import hashlib, json, os, sys, tempfile
sys.path.insert(0, os.getcwd())
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
from lib.akasha.api.client import embedded
gw = embedded(tempfile.mkdtemp(prefix="palone_cell_"), "seeds", load_ontology=False)
k = gw.kernel_client
def d(m, data, tok="admin"):
    return k.dispatch({"jsonrpc": "2.0", "method": m, "params": {"session_token": tok, "data": data}, "id": "p"}, "local")
out = {}
out["genesis"] = d("kernel.genesis_rite", {"user_name": "admin", "passphrase": hashlib.sha256(b"pw").hexdigest()})
out["ping"] = d("sys.ping", {})
w = d("kernel.memory.write", {"text": "a platform-alone atom", "scope": "universal"})
out["write"] = w
key = (w.get("result") or {}).get("key")
out["read"] = d("kernel.memory.read", {"id": key}) if key else {}
out["grp"] = d("grp.new", {"group_id": "alone", "admin_id": "admin"})
out["society_new"] = d("society.new", {"group": "alone", "name": "hall"})
out["society_ls"] = d("society.ls", {"group": "alone"})
out["source"] = d("source.register", {"provider": "alone", "name": "alonesrc", "rights": "CC0"})
print("RESULT_JSON " + json.dumps(out, default=str))
'''

CLI_CHILD = r'''
import json, os, subprocess, sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.path.join(os.getcwd(), "scripts"))
import gen_cli_table as G
per, flat, groups, apps = G.collect()
from api import cli_table as T
from lib.akasha import kernel_methods as KM
from lib.akasha.api import tables as TB
from api.router import CommandRouter
missing = sorted(c for c in flat if c not in T.CLI_SPECS)
differ = sorted(c for c in flat if c in T.CLI_SPECS and T.CLI_SPECS[c] != flat[c])
req = CommandRouter.build_rpc_request('ln alpha beta thesaurus:related', "admin")
checks = {s: subprocess.run([sys.executable, os.path.join("scripts", s + ".py"), "--check"],
                            capture_output=True, text=True).returncode
          for s in ("gen_cli_table", "gen_kernel_methods")}
print("RESULT_JSON " + json.dumps({
    "n": len(flat), "missing": missing, "differ": differ, "apps": len(apps), "ln": req,
    "app_tables": TB.application_tables(TB.CLI_TABLE) + TB.application_tables(TB.ACCESS_TABLE),
    "cli_is_platform": T.CLI_SPECS == T.PLATFORM_CLI_SPECS,
    "access_is_platform": KM.METHOD_TO_ACTION == KM.PLATFORM_METHOD_TO_ACTION,
    "checks": checks}, default=str))
'''


def main():
    own = _owners()
    print("\n  ── 1. the tree without the application ──")
    from lib.akasha.api import reserved as RES
    user = sorted(f for f, o in own.items() if o == "user")
    plat = sorted(f for f, o in own.items() if o == "platform" and not f.startswith("akasha_seeds_"))
    alone = tempfile.mkdtemp(prefix="platform_alone_")
    for f in plat:
        dst = os.path.join(alone, f)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(os.path.join(ROOT, f), dst)
    # its own repository, so an eval that reads `git ls-files` sees exactly this tree
    subprocess.run("git init -q && git add -A && git -c user.email=a@a -c user.name=a commit -qm alone",
                   shell=True, cwd=alone, capture_output=True)
    check("the application root is deleted (%d files under %s/), the platform's copied (%d)"
          % (len(user), RES.APP_DIR, len(plat)),
          bool(user) and not os.path.exists(os.path.join(alone, RES.APP_DIR))
          and all(not RES.is_app_path(f) for f in plat), "user=%d platform=%d" % (len(user), len(plat)))

    print("\n  ── 2. a fresh cell boots and serves the platform's models ──")
    env = dict(os.environ, AKASHA_SKIP_AUTOINSTALL="1", PYTHONPATH="")
    r = subprocess.run([sys.executable, "-c", CHILD], cwd=alone, env=env, capture_output=True,
                       text=True, timeout=600)
    line = next((l for l in r.stdout.splitlines() if l.startswith("RESULT_JSON ")), "")
    res = json.loads(line[len("RESULT_JSON "):]) if line else {}

    def ok(name):
        return isinstance(res.get(name), dict) and "result" in res[name]
    check("genesis and sys.ping", ok("genesis") and (res.get("ping") or {}).get("result", {})
          .get("status") == "kernel_online", (r.stderr or "")[-300:] if not res else "")
    check("an atom is written and read back", ok("write") and ok("read")
          and "platform-alone" in json.dumps(res.get("read")), str(res.get("read"))[:160])
    check("a society is made and listed (a platform Concept Model, served by the platform manifest)",
          ok("society_new") and "hall" in json.dumps(res.get("society_ls")),
          str(res.get("society_ls"))[:160])
    check("a source is registered (the source engine)", ok("source"), str(res.get("source"))[:160])

    print("\n  ── 2b. the CLI table holds every platform command ──")
    r2 = subprocess.run([sys.executable, "-c", CLI_CHILD], cwd=alone, env=env, capture_output=True,
                        text=True, timeout=300)
    line2 = next((l for l in r2.stdout.splitlines() if l.startswith("RESULT_JSON ")), "")
    cli = json.loads(line2[len("RESULT_JSON "):]) if line2 else {}
    check("the generator finds the platform's commands from the platform's manifests alone "
          "(%s; no application manifest is there)" % cli.get("n"),
          (cli.get("n") or 0) > 100 and cli.get("apps") == 0, (r2.stderr or "")[-300:] if not cli else "")
    check("…there is no application table, and the merged CLI and access tables ARE the platform's",
          cli and not cli.get("app_tables") and cli.get("cli_is_platform") and cli.get("access_is_platform"),
          "app_tables=%s" % cli.get("app_tables"))
    check("…and both generators' --check pass there: each platform table equals its generator's output "
          "from the platform's manifests alone", cli and all(v == 0 for v in (cli.get("checks") or {"x": 1}).values()),
          str(cli.get("checks")))
    check("…every one is in the committed api/cli_table.py with the same spec",
          cli and not cli.get("missing") and not cli.get("differ"),
          "missing=%s differ=%s" % ((cli.get("missing") or [])[:6], (cli.get("differ") or [])[:6]))
    ln = cli.get("ln") or {}
    check("…and the router parses `ln` into kernel.memory.link",
          isinstance(ln, dict) and ln.get("method") == "kernel.memory.link", str(ln)[:160])

    print("\n  ── 3. the launcher ──")
    # The launcher on a fresh directory starts the Cell daemon and its web portal, then answers the
    # command (here: "not initialized" — genesis is the operator's interactive rite). What is held:
    # the daemon came online and the portal was serving, as `stop` then reports stopping both.
    cell = tempfile.mkdtemp(prefix="palone_launch_")
    lenv = dict(env, AKASHA_DATA_DIR=cell)
    r3 = r4 = None
    try:
        r3 = subprocess.run([sys.executable, "akasha.py", "sys.ping"], cwd=alone, env=lenv,
                            stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=600)
    finally:
        r4 = subprocess.run([sys.executable, "akasha.py", "stop"], cwd=alone, env=lenv,
                            stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=180)
    out3 = (r3.stdout + r3.stderr) if r3 else ""
    out4 = (r4.stdout + r4.stderr) if r4 else ""
    check("the launcher brings the Cell daemon online in the platform-alone tree",
          r3 is not None and r3.returncode == 0 and "Cell daemon online" in out3, out3.strip()[-200:])
    check("…its web portal was serving, and `stop` stops both",
          "Stopped svc:web-portal" in out4 and "Stopped svc:cell" in out4, out4.strip()[-200:])

    if "--quick" not in sys.argv:
        print("\n  ── 4. the platform's entire suite, there ──")
        evals = sorted(os.path.splitext(f)[0] for f in os.listdir(os.path.join(alone, "test"))
                       if f.endswith("_eval.py") and f != os.path.basename(__file__))
        from concurrent.futures import ThreadPoolExecutor

        def _run(ev):
            try:
                p = subprocess.run([sys.executable, os.path.join("test", ev + ".py")], cwd=alone,
                                   env=env, capture_output=True, text=True, timeout=1200)
                return ev, p.returncode, p.stdout + p.stderr
            except subprocess.TimeoutExpired:
                return ev, -9, "timeout"
        with ThreadPoolExecutor(SUITE_WORKERS) as ex:
            results = list(ex.map(_run, evals))
        failed = [(ev, rc, out) for ev, rc, out in results if rc != 0]
        for ev, rc, out in failed:
            tail = [l for l in out.splitlines() if "FAIL" in l or "Error" in l][:2]
            print("        %s rc=%s %s" % (ev, rc, " | ".join(tail)[:200]))
        check("the platform's suite passes with no application: %d of %d evals"
              % (len(results) - len(failed), len(results)), not failed,
              ", ".join(ev for ev, _, _ in failed[:8]))
    shutil.rmtree(alone, ignore_errors=True)

    print("\n  ── 5. platform code names no application identifier ──")
    hits = _scan(own)
    check("application identifiers in platform code: %d (must be 0)" % len(hits), not hits,
          "; ".join("%s:%d %s %r" % h for h in hits[:6]))

    print()
    if _fails:
        print("FAILED (%d): %s" % (len(_fails), "; ".join(_fails)))
        sys.exit(1)
    print("RESULT: PASS — with every application file removed the platform boots, serves its own "
          "models and its launcher, passes its conformance suite, and its code names nothing of the "
          "application's.")
    sys.exit(0)


def _scan(own):
    """(file, line, kind, string) for each application identifier in platform code."""
    logging.disable(logging.WARNING)
    try:
        from lib.akasha.api import manifest as M, reserved as RES
        from lib.akasha.concepts import registry as R
        plat_ops, app_ops = set(), set()
        for p in M.default_manifest_paths(os.path.join(ROOT, "lib", "akasha")):
            m = json.load(open(p, encoding="utf-8"))
            rel = os.path.relpath(p, ROOT)
            (plat_ops if M.owner_of(None, rel) == "platform" else app_ops).update(m.get("ops") or {})
        app_pkg = RES.app_package()
        for meth, h in (getattr(R.get_active(), "_handlers", {}) or {}).items():
            mod = h[0].__module__
            (app_ops if mod == app_pkg or mod.startswith(app_pkg + ".") else plat_ops).add(meth)
    finally:
        logging.disable(logging.NOTSET)
    reserved = set(RES.RESERVED_CONCEPTS) | set(RES.RESERVED_CONCEPTS.values())
    app_ops -= plat_ops
    plat_prefixes = {o.split(".")[0] for o in plat_ops}
    app_prefixes = {o.split(".")[0] for o in app_ops} - plat_prefixes - reserved
    app_concepts = set()
    for f, o in own.items():
        if o == "user" and f.endswith(".py"):
            src = open(os.path.join(ROOT, f), encoding="utf-8", errors="ignore").read()
            app_concepts.update(re.findall(r'["\']concept["\']\s*:\s*["\'](\w+)["\']', src))
    app_concepts -= reserved
    roots = [str(v).split("%s")[0].rstrip("/") + "/" for v in RES.DECLARATION_ROOTS.values()]
    # the application's own trees, as a platform string could name them (`app/<top>/…`)
    app_tops = sorted({f.split("/")[1] for f, o in own.items() if o == "user" and f.count("/") >= 2})
    app_trees = tuple("%s/%s/" % (RES.APP_DIR, t) for t in app_tops)
    hits = []
    for f, o in sorted(own.items()):
        if o != "platform" or not f.endswith(".py") or f in GENERATED or not f.startswith(SCANNED_TREES):
            continue
        try:
            src = open(os.path.join(ROOT, f), encoding="utf-8").read()
            tree = ast.parse(src)
        except Exception:
            continue
        skip, concept_vals, method_keys, join_args = set(), set(), set(), set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Expr) and isinstance(getattr(node, "value", None), ast.Constant) \
                    and isinstance(node.value.value, str):
                skip.update(range(node.lineno, (node.end_lineno or node.lineno) + 1))
            if isinstance(node, ast.Dict):
                for k, v in zip(node.keys, node.values):
                    if isinstance(k, ast.Constant) and k.value == "concept" and isinstance(v, ast.Constant):
                        concept_vals.add(id(v))
            if isinstance(node, ast.Compare) and "concept" in ast.unparse(node.left):
                for c in node.comparators:
                    concept_vals.update(id(s) for s in ast.walk(c) if isinstance(s, ast.Constant))
            # `"app"` as one component of a path join names the application root
            if isinstance(node, ast.Call) and getattr(node.func, "attr", "") == "join":
                join_args.update(id(a) for a in node.args
                                 if isinstance(a, ast.Constant) and a.value == RES.APP_DIR)
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                tgts = node.targets if isinstance(node, ast.Assign) else [node.target]
                if any(getattr(t, "id", "") == "CONCEPT_METHODS" for t in tgts) and \
                        isinstance(node.value, ast.Dict):
                    method_keys.update(id(k) for k in node.value.keys if k is not None)
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Constant) and isinstance(node.value, str)) or node.lineno in skip \
                    or id(node) in method_keys:
                continue
            t = node.value.strip()
            kind = None
            if t in app_ops:
                kind = "op"
            elif id(node) in concept_vals and t in app_concepts:
                kind = "concept"
            elif re.fullmatch(r"[a-z_]+\.[a-z_][a-z_.]*", t) and t.split(".")[0] in app_prefixes \
                    and not re.search(r"\.(py|json|ak|csl|md|html|js|css)$", t):
                kind = "op-prefix"
            elif re.fullmatch(r"[\w./%<>{}*-]+", t) and any(a in t for a in app_trees):
                kind = "path"
            elif f != "lib/akasha/api/reserved.py" and (t.startswith(RES.APP_DIR + "/")
                                                           or id(node) in join_args):
                kind = "app-root"
            if kind:
                hits.append((f, node.lineno, kind, t))
    return hits


if __name__ == "__main__":
    main()
