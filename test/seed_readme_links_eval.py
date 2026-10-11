#!/usr/bin/env python3
"""
Every document the shipped README links to is in the seed.

seeds 13: `README.md` links `THE_AKASHA_WHITE_PAPER.md` and `AKASHA_FOUNDATIONAL_DESIGN_CONTEXT.md`,
but the crystallizer ships only the root files `reproductor/engine.py` `CORE_FILES` names, and those
two were not among them — so both links were dead in every extracted seed, and a reflection of the
extracted tree onto a public `main` would have deleted them. A series can add `docs/` subfolders,
never a root file, so only the platform's list can carry them.

  L1 (tree)      every relative link in README.md resolves to a file or directory here — on a
                 DEPLOYED (extracted) tree this is the user's own check
  L2 (generator) every ROOT file README.md links to is in CORE_FILES — a root document added to
                 the README cannot fall out of the seed again
  L3 (payload)   in the LATEST cut (the committed payloads whose `BUILD` date is the newest — older
                 payloads in the tree are history, not the release), README.md is there and each of
                 its relative links resolves inside that payload

Run:  python test/seed_readme_links_eval.py     (exit 0 = all pass)
"""
import base64
import glob
import io
import os
import re
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

_fails = []
_LINK = re.compile(r"\]\(([^)\s]+)\)")


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def relative_links(text):
    out = []
    for target in _LINK.findall(text):
        target = target.split("#", 1)[0]
        if not target or re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I) or target.startswith("/"):
            continue                                  # a URL, a mail link, an in-page anchor
        out.append(target)
    return sorted(set(out))


def main():
    print("=" * 78)
    print("Every document the shipped README links to is in the seed")
    print("=" * 78)
    readme = open("README.md", encoding="utf-8").read()
    links = relative_links(readme)
    roots = [l for l in links if "/" not in l.rstrip("/")]
    check("README.md has relative links, root files among them (the check is not vacuous)",
          bool(links) and bool(roots), "%d links, %d root files" % (len(links), len(roots)))

    # L1
    dead = [l for l in links if not os.path.exists(l)]
    check("L1 every relative README link resolves in this tree", not dead, str(dead))

    # L2
    if not os.path.isdir("reproductor"):
        print("  ----  crystallizer absent (deployed tree) — L2/L3 are generator-side")
    else:
        from reproductor.engine import CORE_FILES
        missing = [r for r in roots if r not in CORE_FILES]
        check("L2 every root file README.md links to is in CORE_FILES", not missing, str(missing))

        # L3
        cut = {}
        for sp in sorted(glob.glob("akasha_seeds_*.py")):
            with open(sp, encoding="utf-8") as fh:
                head = fh.read(4096)
            bm = re.search(r"'commit_date': '([^']+)'", head)
            if bm:
                cut[sp] = bm.group(1)
        newest = max(cut.values()) if cut else None
        seeds = sorted(sp for sp, d in cut.items() if d == newest)
        if not seeds:
            print("  ----  no committed seed payload here — L3 is generator-side")
        else:
            print("  ----  the latest cut (%s): %s" % (newest, ", ".join(seeds)))
        for sp in seeds:
            src = open(sp, encoding="utf-8").read()
            m = re.search(r'PAYLOAD = """(.*?)"""', src, re.S)
            if not m:
                check("L3 %s: a payload" % sp, False, "no PAYLOAD block")
                continue
            zf = zipfile.ZipFile(io.BytesIO(base64.b64decode("".join(m.group(1).split()))))
            names = set(zf.namelist())
            if "README.md" not in names:
                check("L3 %s ships README.md" % sp, False)
                continue
            p_links = relative_links(zf.read("README.md").decode("utf-8", "replace"))
            p_dead = [l for l in p_links
                      if l.rstrip("/") not in names and not any(n.startswith(l.rstrip("/") + "/")
                                                                for n in names)]
            check("L3 %s: every README link resolves inside the payload" % sp, not p_dead,
                  str(p_dead))

    print()
    if _fails:
        print(f"RESULT: FAIL — {len(_fails)} check(s): {_fails}")
        return 1
    print("RESULT: PASS — every document the shipped README links to is in the tree and in every "
          "seed payload; a root document the README names is in the crystallizer's list.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
