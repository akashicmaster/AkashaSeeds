#!/usr/bin/env python3
"""
Static lexicon-coverage verifier — the regression guard for the rel-definition spec.

Sibling to verify_set_memberships.py / verify_link_targets.py, but purely static (no DB):
it reads the `.ak` tree and asserts the spec's "no bare rels/namespaces" invariant —

  every relation used on an edge, and every namespace an atom/edge introduces, has a
  `reldef:<rel>` / `nsdef:<ns>` definition somewhere in the ontology.

Scope: by default it checks the packs that AUTOLOAD (REGISTRY.json `autoload: true`) plus
the always-loaded `lexicon` pack — the set a default (seeds) boot actually loads, so the
check matches what a user sees. `--all` widens it to every pack (the load_all / thesaurus
surface). A namespace is covered if any prefix of it is defined (the reader's progressive
`nsdef` fallback: `dna:taste:sweet` is covered by `nsdef:dna:taste` or `nsdef:dna`).

Usage:
    python test/verify_lexicon.py          # autoloaded packs (+ lexicon)
    python test/verify_lexicon.py --all     # every pack (thesaurus surface)

Exit non-zero if any used relation or namespace lacks a definition.
"""
import glob
import json
import os
import shlex
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ONT = os.path.join(ROOT, "ontology")


def _packs(all_packs):
    reg = json.load(open(os.path.join(ONT, "REGISTRY.json"), encoding="utf-8"))
    if all_packs:
        return {p["name"] for p in reg["packages"]}
    return {p["name"] for p in reg["packages"] if p.get("autoload")} | {"lexicon"}


def _top_ns(tok):
    if ":" in tok and tok[0] not in "{'\"":
        return tok.split(":")[0]
    return None


def scan(packs):
    """Return (used_rels, used_ns, defined_rels, defined_ns) restricted to `packs`."""
    used_rels, used_ns = set(), set()
    defined_rels, defined_ns = set(), set()
    for fp in glob.glob(os.path.join(ONT, "**", "*.ak"), recursive=True):
        pack = os.path.relpath(fp, ONT).split(os.sep)[0]
        if pack not in packs:
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


def _ns_covered(ns, defined_ns):
    """A namespace is covered if any prefix of it is defined (reader fallback)."""
    parts = ns.split(":")
    return any(":".join(parts[:i]) in defined_ns for i in range(len(parts), 0, -1))


def main(argv):
    all_packs = "--all" in argv[1:]
    packs = _packs(all_packs)
    used_rels, used_ns, def_rels, def_ns = scan(packs)

    # `rel:salient` is the profile-declaration relation itself and is defined by the
    # engine, not the ontology; it never needs a reldef of its own.
    used_rels.discard("rel:salient")

    missing_rels = sorted(r for r in used_rels if r not in def_rels)
    missing_ns = sorted(n for n in used_ns if not _ns_covered(n, def_ns))

    scope = "ALL packs" if all_packs else "autoloaded packs (+ lexicon)"
    print(f"\n  lexicon coverage — {scope}")
    print(f"  relations used: {len(used_rels):4d}  defined: {len(def_rels):4d}  "
          f"missing: {len(missing_rels)}")
    print(f"  namespaces used: {len(used_ns):4d}  defined: {len(def_ns):4d}  "
          f"missing: {len(missing_ns)}")

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

    if missing_rels or missing_ns:
        print("\nRESULT: FAIL — regenerate with scripts/gen_lexicon.py "
              "(or add the definition).")
        return 1
    print("\nRESULT: PASS — every used relation and namespace is defined.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
