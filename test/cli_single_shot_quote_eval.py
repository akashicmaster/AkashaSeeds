#!/usr/bin/env python3
"""
cli_single_shot_quote_eval.py — a single-shot CLI argument value with spaces survives the shlex re-parse.

`python akasha.py <cmd …>` captures argv via nargs=REMAINDER (the shell's already-split tokens), then
run_single_shot re-parses the joined STRING with shlex (router.build_rpc_request → shlex.split). A bare
" ".join then re-splits any value containing spaces — e.g. `fixture_policy="no synthetic artworks; …"`
collapsed to just "no". The fix is to shlex.quote each token before joining, so the round-trip is
lossless (CLI-first convention: single-shot must behave like the interactive CLI). This pins it.

Run:  python test/cli_single_shot_quote_eval.py     (exit 0 = pass)
"""
import os
import shlex
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def main():
    from api.router import CommandRouter

    fails = []

    def check(name, ok, detail=""):
        print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
        if not ok:
            fails.append(name)

    # The shell hands these already-split tokens (quotes removed) to argv/REMAINDER:
    argv = ["source.lab.declare", "lab=visual_curation", "klass=CORPUS",
            "pool=source:pool:cma:visual_curation:v1",
            "fixture_policy=no synthetic artworks; CC0 open-access records only"]

    def data_of(line):
        return ((CommandRouter.build_rpc_request(line, "tok").get("params") or {}).get("data") or {})

    # The bug: a bare join truncates the spaced value.
    old = data_of(" ".join(argv))
    check("reproduces the bug: bare join truncates the spaced value to 'no'",
          old.get("fixture_policy") == "no", repr(old.get("fixture_policy")))

    # The fix: shlex.quote each token → the value round-trips intact.
    new = data_of(" ".join(shlex.quote(t) for t in argv))
    check("fix: shlex.quote per token preserves the full spaced value",
          new.get("fixture_policy") == "no synthetic artworks; CC0 open-access records only",
          repr(new.get("fixture_policy")))
    # the other args are unaffected
    check("fix: the other key=value args are intact",
          new.get("lab") == "visual_curation" and new.get("klass") == "CORPUS"
          and new.get("pool") == "source:pool:cma:visual_curation:v1", str(new))

    # akasha.py's single-shot sites actually apply the quote-join.
    src = open(os.path.join(ROOT, "akasha.py"), encoding="utf-8").read()
    check("akasha.py single-shot joins with shlex.quote (both run_single_shot sites)",
          src.count("_shlex.quote(t) for t in args.cmd") >= 2 and '" ".join(args.cmd)' not in src,
          "quote-joins=%d, bare-join present=%s"
          % (src.count("_shlex.quote(t) for t in args.cmd"), '" ".join(args.cmd)' in src))

    print()
    if fails:
        print(f"FAIL — {len(fails)} check(s) failed: {fails}")
        sys.exit(1)
    print("ALL PASS — a single-shot CLI argument value with spaces survives the shlex re-parse "
          "(shlex.quote per token); single-shot behaves like the interactive CLI.")


if __name__ == "__main__":
    main()
