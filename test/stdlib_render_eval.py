#!/usr/bin/env python3
"""
Stdlib-only console render eval — the console renders every view with no third-party package.

The core is Python stdlib only (requirements.txt: "Core: None"). `rich` is optional: the console
uses it for trees and tables when present and draws them in plain lines when not. A clean install
without it used to crash on `tree <set>` (`ModuleNotFoundError: No module named 'rich'`) and on
every table view.

Here `rich` is made unimportable (whether or not it is installed), and:

  R1 `tree` on a set, through the console router and the kernel, renders and names its members.
  R2 a table view (the shape `rec.table` / `tbl.ls` return) renders, numbers right-aligned.
  R3 a tree view that asks for the default `format="rich"` renders in lines.
  R4 scatter / list / keyval views render.
  R5 nothing imported `rich` while rendering.

Run:  python test/stdlib_render_eval.py
"""
import contextlib
import hashlib
import io
import os
import re
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"


class _NoRich:
    """Meta-path finder that makes `rich` unimportable for this process."""
    def find_spec(self, name, path=None, target=None):
        if name == "rich" or name.startswith("rich."):
            raise ImportError(f"No module named '{name}' (blocked by the eval)")
        return None


sys.meta_path.insert(0, _NoRich())
for _m in [m for m in sys.modules if m == "rich" or m.startswith("rich.")]:
    del sys.modules[_m]

_results = []


def record(name, ok, detail=""):
    _results.append((name, ok, detail))
    print(f"  {'OK  ' if ok else '!! FAIL'}  {name:28} {detail}")


def _rendered(resp):
    from api.shell import renderer
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            renderer.render(resp)
        return re.sub(r"\x1b\[[0-9;]*m", "", buf.getvalue()), None
    except Exception as e:                      # the defect: ModuleNotFoundError
        return buf.getvalue(), repr(e)


def main():
    print("\n  stdlib-only render eval — trees and tables without `rich`\n")
    from lib.akasha.kernel import KernelDispatcher
    from api.router import CommandRouter
    KernelDispatcher._boot_load_ontology = lambda self: None
    k = KernelDispatcher(series="seeds", base_dir=tempfile.mkdtemp(prefix="akasha_norich_"))
    k.dispatch({"jsonrpc": "2.0", "method": "kernel.genesis_rite",
                "params": {"session_token": "admin",
                           "data": {"user_name": "admin",
                                    "passphrase": hashlib.sha256(b"pw").hexdigest()}},
                "id": "g"}, "local")

    def cli(line):
        return k.dispatch(CommandRouter.build_rpc_request(line, "admin"), "local")

    for name, text in (("fruit:apple", "A round fruit with red or green skin."),
                       ("fruit:lemon", "A yellow citrus fruit, very sour.")):
        cli(f'def "{name}" "{text}"')
        cli(f"s.add set:norich:fruit {name}")
    cli("ln fruit:apple fruit:lemon thesaurus:related")

    # R1 — tree through the router and the kernel.
    resp = cli("tree set:norich:fruit")
    out, err = _rendered(resp)
    record("R1 tree <set>", err is None and "fruit:apple" in out and "fruit:lemon" in out,
           err or f"{out.count(chr(10))} lines, both members drawn")

    # R2 — a table view.
    table = {"result": {"_view": "table", "title": "set:norich:fruit",
                        "columns": ["content", "sweetness", "acidity", "color"],
                        "rows": [{"content": "fruit:apple", "sweetness": "0.85",
                                  "acidity": "0.25", "color": "red"},
                                 {"content": "fruit:lemon", "sweetness": "0.1",
                                  "acidity": "0.95", "color": "yellow"}]}}
    out, err = _rendered(table)
    line = next((l for l in out.splitlines() if "fruit:lemon" in l), "")
    record("R2 table view", err is None and "sweetness" in out and line.endswith("yellow")
           and " 0.1 " in line,
           err or f"row: {line.strip()!r}")

    # R3 — a tree view with the default format.
    tv = {"result": {"_view": "tree", "title": "t", "root": "root", "format": "rich",
                     "children": [{"label": "a", "sublabel": "[sys:is_a]",
                                   "children": [{"label": "b"}]}]}}
    out, err = _rendered(tv)
    record("R3 tree view format=rich", err is None and "└─ a" in out and "b" in out,
           err or "drawn in lines")

    # R4 — the other views.
    others = [
        {"_view": "scatter", "title": "s", "x": "acidity", "y": "sweetness",
         "points": [{"label": "apple", "x": 0.25, "y": 0.85},
                    {"label": "lemon", "x": 0.95, "y": 0.1}]},
        {"_view": "list", "title": "l", "items": [{"label": "one", "meta": "m"}]},
        {"_view": "keyval", "title": "k", "pairs": [["a", "1"]]},
    ]
    errs = [(v["_view"], _rendered({"result": v})[1]) for v in others]
    errs = [e for e in errs if e[1]]
    record("R4 scatter/list/keyval", not errs, str(errs) if errs else "rendered")

    record("R5 rich never imported", not any(m == "rich" or m.startswith("rich.")
                                             for m in sys.modules), "")

    print()
    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"  {passed}/{total} phases passed" + (f", {total - passed} FAILED" if passed < total else ""))
    if passed < total:
        print("\nRESULT: FAIL — a console view needs a package the core does not declare.")
        return 1
    print("\nRESULT: PASS — with `rich` unimportable every console view renders, trees and tables "
          "in plain lines.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
