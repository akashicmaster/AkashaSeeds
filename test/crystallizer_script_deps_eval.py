#!/usr/bin/env python3
"""
The crystallizer's "eval loads an unbundled script" check reads CALLS, not text.

Frontend note 2026-10-02c: every seed cut failed with

    crystallizer: bundled eval(s) dynamically import scripts/ file(s) that are NOT bundled …
    test/ownership_eval.py imports [scripts/akasha.py]

`_assert_eval_script_deps_bundled` matched the text `"scripts", "<name>.py"` anywhere, and
ownership_eval's directory walk lists `("lib/akasha", "api", "scripts", "akasha.py")` — a tuple
that loads nothing. The check now reads the AST: a reference is a CALL whose positional arguments
hold consecutive strings ending `"scripts"`, `"<name>.py"` (the form every real load takes), and it
answers the TREE path the call names — `scripts/<name>.py`, or `<app root>/scripts/<name>.py` for an
application eval's `join(ROOT, "<app root>", "scripts", "<name>.py")`.

This eval holds:
  1. the false positive is gone: ownership_eval's tuple, a list, a comment and a string name
     nothing;
  2. the real form is still caught: `os.path.join(ROOT, "scripts", "x.py")` inside any call;
  3. on a zip, the check PASSES with ownership_eval bundled and no `scripts/akasha.py`, and RAISES
     for an eval that loads a script the zip lacks (the guard keeps its teeth);
  4. over the repository's own evals, every reference found is a real load (each one sits inside a
     `join(...)` / `spec_from_file_location(...)` call line), and the evals that load a script
     are all found.

Run:  python test/crystallizer_script_deps_eval.py     (exit 0 = all pass)
"""
import glob
import io
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def main():
    print("=" * 78)
    print("The crystallizer's script-dependency check reads calls, not text")
    print("=" * 78)
    import reproductor.engine as E
    cls = next(getattr(E, n) for n in dir(E) if hasattr(getattr(E, n), "_eval_script_refs"))
    refs = cls._eval_script_refs

    print("\n  ── 1. what is NOT a load ──")
    own = open(os.path.join(ROOT, "test", "ownership_eval.py"), encoding="utf-8").read()
    check("ownership_eval (its `(\"lib/akasha\", \"api\", \"scripts\", \"akasha.py\")` walk) loads "
          "no script", refs(own) == set(), str(refs(own)))
    check("a tuple, a list, a comment and a bare string name nothing",
          refs('x = ("scripts", "a.py")\ny = ["scripts", "b.py"]\n'
               '# os.path.join("scripts", "c.py")\nz = "scripts, d.py"\n') == set())

    print("\n  ── 2. what IS a load ──")
    check("`os.path.join(ROOT, \"scripts\", \"x.py\")` is found",
          refs('import os\np = os.path.join(ROOT, "scripts", "x.py")\n') == {"scripts" + "/x.py"})
    from lib.akasha.api import reserved as RES
    check("…and the application root's form names the application's script",
          refs('import os\np = os.path.join(ROOT, "%s", "scripts", "x.py")\n' % RES.APP_DIR)
          == {RES.APP_DIR + "/scripts" + "/x.py"})
    check("…inside spec_from_file_location, and a sub-path (`user/y.py`)",
          refs('import importlib.util as u, os\n'
               's = u.spec_from_file_location("m", os.path.join(R, "scripts", "user/y.py"))\n')
          == {"scripts" + "/user/y.py"})
    check("an unparseable source falls back to the text match (never silently waved through)",
          refs('def (:\n  "scripts", "z.py"\n') == {"scripts" + "/z.py"})

    print("\n  ── 3. the check itself, on a zip ──")
    eng = cls.__new__(cls)

    def _zip(files):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            for n, src in files.items():
                z.writestr(n, src)
        buf.seek(0)
        return zipfile.ZipFile(buf)

    try:
        eng._assert_eval_script_deps_bundled(_zip({"test/ownership_eval.py": own}))
        ok, err = True, ""
    except RuntimeError as e:
        ok, err = False, str(e)[:160]
    check("ownership_eval bundled WITHOUT scripts/akasha.py → the cut proceeds (the 10-02c block)",
          ok, err)
    # (the names are built, not written: seed_payload_eval reads every quoted `scripts/<x>.py` in a
    # shipped eval as a script that eval needs bundled)
    _tool = "scripts" + "/needed_tool.py"
    loader = 'import os\nexec(open(os.path.join(ROOT, "scripts", "needed_tool.py")).read())\n'
    try:
        eng._assert_eval_script_deps_bundled(_zip({"test/x_eval.py": loader}))
        raised = ""
    except RuntimeError as e:
        raised = str(e)
    check("an eval that LOADS a script the zip lacks still stops the cut, naming both",
          "test/x_eval.py" in raised and _tool in raised, raised[:160])
    try:
        eng._assert_eval_script_deps_bundled(_zip({"test/x_eval.py": loader,
                                                   _tool: "pass\n"}))
        ok2 = True
    except RuntimeError:
        ok2 = False
    check("…and passes once that script is bundled", ok2)

    print("\n  ── 4. over the repository's own evals ──")
    found, bad = {}, []
    for p in sorted(glob.glob(os.path.join(ROOT, "test", "*.py"))):
        src = open(p, encoding="utf-8").read()
        r = refs(src)
        if r:
            found[os.path.basename(p)] = sorted(r)
        lines = src.splitlines()
        for path in r:
            name = path.rsplit("/", 1)[-1]
            hit = [ln for ln in lines if '"%s"' % name in ln or "'%s'" % name in ln]
            if not any(("join(" in ln or "spec_from_file_location(" in ln) for ln in hit):
                bad.append((os.path.basename(p), path))
    check("every reference found sits on a join(...) / spec_from_file_location(...) line",
          not bad, str(bad[:4]))
    check("the evals that load a script are found (f56_d1_fingerprint_eval → seed_check.py)",
          "scripts" + "/seed_check.py" in (found.get("f56_d1_fingerprint_eval.py") or []), str(found)[:200])
    print("        %d eval(s) load a script: %s" % (len(found), ", ".join(sorted(found))[:200]))

    print()
    if _fails:
        print("FAILED (%d): %s" % (len(_fails), "; ".join(_fails)))
        sys.exit(1)
    print("RESULT: PASS — a script reference is a call that loads it; a tuple, list, comment or "
          "string is not, and a real unbundled load still stops the cut.")
    sys.exit(0)


if __name__ == "__main__":
    main()
