#!/usr/bin/env python3
"""
Static lexicon-coverage verifier — the regression guard for the rel-definition spec.

Sibling to verify_set_memberships.py / verify_link_targets.py, but purely static (no DB):
it reads the `.ak` tree and asserts the spec's "no bare rels/namespaces" invariant —

  every relation used on an edge, and every namespace an atom/edge introduces, has a
  `reldef:<rel>` / `nsdef:<ns>` definition somewhere in the ontology.

Scope: both pack roots (the platform's `ontology/` and the application's packs root). By default
it checks the packs that AUTOLOAD (each REGISTRY.json's `autoload: true`, the lexicon packs among them) — the set a default (seeds) boot actually loads, so the
check matches what a user sees. `--all` widens it to every pack (the load_all / thesaurus
surface). A namespace is covered if any prefix of it is defined (the reader's progressive
`nsdef` fallback: `dna:taste:sweet` is covered by `nsdef:dna:taste` or `nsdef:dna`).

Usage:
    python test/verify_lexicon.py          # autoloaded packs
    python test/verify_lexicon.py --all     # every pack (thesaurus surface)

Exit non-zero if any used relation or namespace lacks a definition.
"""
import glob
import json
import os
import re
import shlex
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from lib.akasha.api import reserved as _reserved  # noqa: E402

# Both pack roots: the platform's `ontology/` and, when present, the application's packs root.
ONTS = [os.path.join(ROOT, "ontology")] + ([_reserved.root("packs")]
                                           if os.path.isdir(_reserved.root("packs")) else [])

# ── code-vocabulary coverage ─────────────────────────────────────────────────────────────────────
# "A value the code COMPARES AGAINST is vocabulary": defined once as an atom in a namespace, and
# the code uses the id, never a free string. This pass reads that direction — every id of one of
# these families that appears as a string literal in the code must have a `def` in the `.ak` tree,
# so a new state/reason cannot reach a surface before it is defined. Add a family here when the
# code starts comparing against one. (Display words — "on air", "standing by" — are the defined
# atoms' full spellings and belong to the display layer, not here.)
CODE_VOCAB = ("wl:state:", "wl:reason:")
CODE_ROOTS = ("lib", "api", "scripts")


def _packs(all_packs):
    """{(root, pack)} in scope: every registered pack with --all, else the autoload ones."""
    out = set()
    for ont in ONTS:
        reg = json.load(open(os.path.join(ont, "REGISTRY.json"), encoding="utf-8"))
        out |= {(ont, p["name"]) for p in reg["packages"] if all_packs or p.get("autoload")}
    return out


def _top_ns(tok):
    if ":" in tok and tok[0] not in "{'\"":
        return tok.split(":")[0]
    return None


def scan(packs, defined_ids=None):
    """Return (used_rels, used_ns, defined_rels, defined_ns) restricted to `packs`.

    `defined_ids`, when a set is passed in, collects every `def`ined atom id seen — the
    code-vocabulary pass checks the code's ids against it.
    """
    used_rels, used_ns = set(), set()
    defined_rels, defined_ns = set(), set()
    for ont, fp in [(o, f) for o in ONTS
                    for f in glob.glob(os.path.join(o, "**", "*.ak"), recursive=True)]:
        pack = os.path.relpath(fp, ont).split(os.sep)[0]
        if (ont, pack) not in packs:
            continue
        for raw in open(fp, encoding="utf-8", errors="replace"):
            s = raw.strip()
            if not s or s.startswith("#"):
                continue
            parts = s.split()
            cmd = parts[0]
            if cmd == "ln" and len(parts) >= 4:
                used_rels.add(parts[3])
                for t in (parts[1], parts[2], parts[3]):
                    n = _top_ns(t)
                    if n:
                        used_ns.add(n)
            elif cmd == "def" and len(parts) >= 2:
                try:
                    did = shlex.split(s)[1]
                except ValueError:
                    continue
                if defined_ids is not None:
                    defined_ids.add(did)
                if did.startswith("reldef:"):
                    defined_rels.add(did[len("reldef:"):])
                elif did.startswith("nsdef:"):
                    defined_ns.add(did[len("nsdef:"):])
                n = _top_ns(did)
                if n and not did.startswith(("reldef:", "nsdef:")):
                    used_ns.add(n)
            elif cmd == "al" and len(parts) >= 3:
                n = _top_ns(parts[1])
                if n:
                    used_ns.add(n)
    return used_rels, used_ns, defined_rels, defined_ns


def scan_code():
    """Return {id: [file:line, …]} for every CODE_VOCAB id spelled in the code."""
    pat = re.compile("(" + "|".join(re.escape(p) for p in CODE_VOCAB) + r")[A-Za-z0-9_:]+")
    found = {}
    for root in CODE_ROOTS:
        for fp in glob.glob(os.path.join(ROOT, root, "**", "*.py"), recursive=True):
            for n, raw in enumerate(open(fp, encoding="utf-8", errors="replace"), 1):
                for m in pat.finditer(raw):
                    found.setdefault(m.group(0), []).append(
                        f"{os.path.relpath(fp, ROOT)}:{n}")
    return found


def _ns_covered(ns, defined_ns):
    """A namespace is covered if any prefix of it is defined (reader fallback)."""
    parts = ns.split(":")
    return any(":".join(parts[:i]) in defined_ns for i in range(len(parts), 0, -1))


def main(argv):
    all_packs = "--all" in argv[1:]
    packs = _packs(all_packs)
    def_ids = set()
    used_rels, used_ns, def_rels, def_ns = scan(packs, def_ids)

    # `rel:salient` is the profile-declaration relation itself and is defined by the
    # engine, not the ontology; it never needs a reldef of its own.
    used_rels.discard("rel:salient")

    missing_rels = sorted(r for r in used_rels if r not in def_rels)
    missing_ns = sorted(n for n in used_ns if not _ns_covered(n, def_ns))

    code_ids = scan_code()
    missing_code = sorted(i for i in code_ids if i not in def_ids)

    scope = "ALL packs" if all_packs else "autoloaded packs"
    print(f"\n  lexicon coverage — {scope}")
    print(f"  relations used: {len(used_rels):4d}  defined: {len(def_rels):4d}  "
          f"missing: {len(missing_rels)}")
    print(f"  namespaces used: {len(used_ns):4d}  defined: {len(def_ns):4d}  "
          f"missing: {len(missing_ns)}")
    print(f"  code vocabulary: {len(code_ids):4d}  "
          f"({', '.join(CODE_VOCAB)})  missing: {len(missing_code)}")

    if missing_rels:
        print(f"\n  FAIL — {len(missing_rels)} relation(s) used but not defined "
              f"(reldef:<rel> missing):")
        for r in missing_rels[:30]:
            print(f"    {r}")
        if len(missing_rels) > 30:
            print(f"    …+{len(missing_rels) - 30} more")
    if missing_ns:
        print(f"\n  FAIL — {len(missing_ns)} namespace(s) used but not defined "
              f"(nsdef:<ns> missing, no prefix covers them):")
        for n in missing_ns[:30]:
            print(f"    {n}")
        if len(missing_ns) > 30:
            print(f"    …+{len(missing_ns) - 30} more")

    if missing_code:
        print(f"\n  FAIL — {len(missing_code)} vocabulary id(s) spelled in the code but not "
              f"defined in the ontology (a value the code compares against is vocabulary):")
        for i in missing_code[:30]:
            print(f"    {i}   ← {code_ids[i][0]}")
        if len(missing_code) > 30:
            print(f"    …+{len(missing_code) - 30} more")

    if missing_rels or missing_ns or missing_code:
        print("\nRESULT: FAIL — regenerate with scripts/gen_lexicon.py "
              "(or add the definition).")
        return 1
    print("\nRESULT: PASS — every used relation and namespace is defined, and every "
          "vocabulary id the code compares against exists as an atom.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
