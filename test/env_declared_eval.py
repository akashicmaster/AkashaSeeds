#!/usr/bin/env python3
"""
The environment carries deployment facts only, every one declared (the purge order, 3 October §4.5).

Every AKASHA_* variable the platform reads is declared in the heart's manifest (`env`: kind, default,
means); a package declares its own in its manifest. docs/deployment.md is generated from them. The
launcher refuses a set AKASHA_* variable no manifest declares, by name, with exit 3.

  1. every AKASHA_* name in a platform module's code (string literals — comments are not readers)
     is declared, and every name the heart declares is read by a platform module (no dead row);
  2. every declared row has a known kind and says what it means;
  3. `env_undeclared`: a declared name passes, a family member passes, a deleted switch is named;
  4. the real launcher: an undeclared exported variable → exit 3 + `[env] refused name=<it>`; the
     same name in `env/deployment.env` → the same; only declared names → no refusal; `stop` with an
     undeclared name still runs (a cell can always be halted);
  5. docs/deployment.md is current.

Run:  python test/env_declared_eval.py     (exit 0 = all pass)
"""
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import tokenize

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"
_fails = []

KINDS = {"path", "network", "secret", "identity", "series", "capacity", "process"}
RUNTIME = ("lib/", "api/", "services/", "reproductor/", "remote/", "akasha.py", "spawn.py")
# a name followed by `.<ext>` is a FILE (`AKASHA_FOUNDATIONAL_DESIGN_CONTEXT.md`, a root document the
# crystallizer ships), not an environment variable
_NAME = re.compile(r"(?<![A-Za-z0-9_])AKASHA_[A-Z0-9_]+\b(?!\.(?:md|txt|json|py|ak|html|csv)\b)")


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _platform_files():
    from lib.akasha.api import manifest as M
    agg = M.load_manifests(M.default_manifest_paths(os.path.join(ROOT, "lib", "akasha")))
    out = subprocess.run(["git", "-C", ROOT, "ls-files", "-co", "--exclude-standard"],
                         capture_output=True, text=True).stdout.split()
    return [f for f in out if f.endswith(".py") and f.startswith(RUNTIME)
            and not os.path.basename(f).startswith("akasha_seeds_")
            and os.path.isfile(os.path.join(ROOT, f)) and M.owner_of(agg, f) == "platform"]


def _code_names(path):
    """AKASHA_* names in the file's string literals. A trailing `_` is a fragment a format builds a
    family name from (`"AKASHA_LLM_%s_%s"`), returned as such."""
    names = set()
    try:
        with open(os.path.join(ROOT, path), "rb") as fh:
            toks = list(tokenize.tokenize(io.BytesIO(fh.read()).readline))
    except (tokenize.TokenError, SyntaxError, OSError):
        return names
    for t in toks:
        if t.type == tokenize.STRING:
            names.update(_NAME.findall(t.string))
    return names


def main():
    from lib.akasha.api import manifest as M
    heart = json.load(open(os.path.join(ROOT, "lib", "akasha", "MANIFEST.json")))["env"]
    decl = M.declared_env()

    print("\n  ── 1. every name the platform reads is declared; every declared name is read ──")
    read_by = {}
    for f in _platform_files():
        for n in _code_names(f):
            read_by.setdefault(n, set()).add(f)
    whole = sorted(n for n in read_by if not n.endswith("_"))
    frags = sorted(n for n in read_by if n.endswith("_"))
    und = M.env_undeclared(whole, decl)
    check("0 undeclared AKASHA_* names in platform code (%d read)" % len(whole), not und,
          "; ".join("%s ← %s" % (n, sorted(read_by[n])[0]) for n in und[:8]))
    bad_frag = [f for f in frags if not any(k.startswith(f) for k in decl)]
    check("every name fragment builds a declared family", not bad_frag, str(bad_frag))
    dead = []
    for n in heart:
        if "*" in n:
            pre = n.split("*")[0]
            if not any(r.startswith(pre) for r in read_by):
                dead.append(n)
        elif n not in read_by and not any(n.startswith(f) for f in frags):
            dead.append(n)              # (a fragment a format completes — `"AKASHA_LLM_%s" % var`)
    check("0 heart-declared names no platform code reads (%d declared)" % len(heart), not dead,
          str(dead[:8]))

    print("\n  ── 2. every row is a fact with a meaning ──")
    badk = [n for n, r in decl.items() if r.get("kind") not in KINDS]
    check("every declared kind is one of %s" % sorted(KINDS), not badk, str(badk[:8]))
    nomean = [n for n, r in decl.items() if not str(r.get("means") or "").strip()]
    check("every declared row says what it means", not nomean, str(nomean[:8]))

    print("\n  ── 3. the matcher ──")
    got = M.env_undeclared(["AKASHA_SECRET", "AKASHA_LLM_MISTRAL_CALLS_PER_DAY",
                            "AKASHA_NO_SEMCACHE", "PATH", "AKASHA_SUPERVISOR_STRICT"], decl)
    check("declared and family names pass; deleted switches are named; non-AKASHA ignored",
          got == ["AKASHA_NO_SEMCACHE", "AKASHA_SUPERVISOR_STRICT"], str(got))

    print("\n  ── 4. the launcher refuses by name ──")
    base_env = {k: v for k, v in os.environ.items() if not k.startswith("AKASHA_")}
    base_env.update({"AKASHA_SKIP_AUTOINSTALL": "1", "PYTHONPATH": ""})

    def launch(args, extra=None, dep=None):
        tmp = tempfile.mkdtemp(prefix="akasha_envdecl_")
        root = os.path.join(tmp, "root")
        os.makedirs(os.path.join(root, "env"))
        for f in ("akasha.py",):
            os.symlink(os.path.join(ROOT, f), os.path.join(root, f))
        for d in ("lib", "api", "services", "reproductor", "remote", "ontology", "config", "archives",
                  "scripts", "docs"):
            if os.path.isdir(os.path.join(ROOT, d)):
                os.symlink(os.path.join(ROOT, d), os.path.join(root, d))
        if dep:
            with open(os.path.join(root, "env", "deployment.env"), "w") as fh:
                fh.write(dep)
        env = dict(base_env, AKASHA_DATA_DIR=os.path.join(tmp, "data"))
        env.update(extra or {})
        r = subprocess.run([sys.executable, os.path.join(root, "akasha.py")] + args, env=env,
                           capture_output=True, text=True, timeout=120, cwd=root)
        return r.returncode, (r.stderr or "") + (r.stdout or "")

    rc, out = launch(["--help"], {"AKASHA_NO_SEMCACHE": "1"})
    check("an undeclared exported variable → exit 3 + `[env] refused name=AKASHA_NO_SEMCACHE`",
          rc == 3 and "[env] refused name=AKASHA_NO_SEMCACHE" in out, "rc=%s %s" % (rc, out[-160:]))
    rc, out = launch(["--help"], dep="AKASHA_SERIES=seeds14\nAKASHA_FEED_POLLX=1\n")
    check("the same in env/deployment.env → exit 3 + refused name=AKASHA_FEED_POLLX",
          rc == 3 and "refused name=AKASHA_FEED_POLLX" in out and "AKASHA_SERIES" not in
          out.split("refused name=")[-1][:20], "rc=%s %s" % (rc, out[-160:]))
    rc, out = launch(["--help"], {"AKASHA_LOG_LEVEL": "INFO", "AKASHA_LLM_MISTRAL_CALLS_PER_DAY": "9"},
                     dep="AKASHA_SERIES=seeds14\n")
    check("only declared names (one a family member) → no refusal, the launcher proceeds",
          rc != 3 and "refused name=" not in out, "rc=%s %s" % (rc, out[-160:]))
    rc, out = launch(["stop"], {"AKASHA_NO_SEMCACHE": "1"})
    check("`stop` with an undeclared name still runs (a cell can always be halted)",
          rc != 3 and "refused name=" not in out, "rc=%s %s" % (rc, out[-160:]))

    print("\n  ── 5. the published list ──")
    r = subprocess.run([sys.executable, "scripts/gen_deployment_doc.py", "--check"],
                       capture_output=True, text=True, cwd=ROOT)
    check("docs/deployment.md is current", r.returncode == 0,
          ((r.stdout or r.stderr).strip().splitlines() or [""])[-1])
    try:
        page = open(os.path.join(ROOT, "docs", "deployment.md"), encoding="utf-8").read()
    except OSError:
        page = ""
    # the page lists the PLATFORM's variables; an application's are declared in its own manifest
    from lib.akasha.api import manifest as _M, reserved as _R
    plat_env = {}
    for _p in _M.default_manifest_paths(os.path.join(ROOT, "lib", "akasha")):
        if not _R.is_app_path(_p):
            plat_env.update(json.load(open(_p, encoding="utf-8")).get("env") or {})
    missing = [n for n in plat_env if "`%s`" % n not in page]
    check("every variable a platform manifest declares is on the page (%d)" % len(plat_env),
          bool(plat_env) and not missing, str(missing[:6]))

    print()
    if _fails:
        print("RESULT: FAIL — %d check(s): %s" % (len(_fails), "; ".join(_fails)))
        return 1
    print("RESULT: PASS — every AKASHA_* variable is a declared deployment fact, published in "
          "docs/deployment.md, and the launcher refuses any other by name.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
