#!/usr/bin/env python3
"""
Pairing-sets eval — prove the Akashic Kitchen "Pairing" room's browse sets populate
CROSS-PACK at runtime.

Why this exists: the frontend reported the Pairing room as empty and hypothesised a
missing derivation (that pairing:wines / pairing:cheeses needed link→set auto-derivation
across packs). This eval disproves that: the sets are statically authored in
ontology/kitchen_index/pairing_sets.ak and their members (cheese:* / wine:* atoms) live
in the wine pack. The only thing that must hold is that a set.add in one pack resolves an
alias defined in ANOTHER pack — which the boot loader's global-relations phase guarantees
(all al before any set.add). We reproduce that ordering here against the real backend and
assert both sets fill with resolvable members.

If this passes but the live site shows an empty Pairing room, the cause is a runtime
partial/crashed-mid-load (the same family as empty recipe-content chunks), NOT the
ontology — recover with `onto.reload confirm="RELOAD"`.

    python test/pairing_sets_eval.py
"""
import os
import sys
import glob
import shlex
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
os.environ["AKASHA_SKIP_AUTOINSTALL"] = "1"

from lib.akasha.composite import NucleusEngine

EXPECT = {"pairing:cheeses": 9, "pairing:wines": 15}   # lower bounds (>=), see note below


def _load(ne, path, phase):
    n = 0
    for raw in open(path, encoding="utf-8"):
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        try:
            toks = shlex.split(s)
        except ValueError:
            continue
        if not toks:
            continue
        cmd = toks[0]
        if phase == "atoms" and cmd == "def" and len(toks) >= 3:
            ne.set_alias(ne.put_atom(toks[2], {}, author="test"), toks[1]); n += 1
        elif phase == "atoms" and cmd == "al" and len(toks) >= 3:
            ne.set_alias(ne.resolve_alias(toks[1]) or toks[1], toks[2]); n += 1
        elif phase == "rel" and cmd == "set.add":
            kw = dict(t.split("=", 1) for t in toks[1:] if "=" in t)
            name = kw.get("name", "").strip('"'); idv = kw.get("id", "").strip('"')
            ne.add_to_set(name, ne.resolve_alias(idv) or idv); n += 1
    return n


def main():
    # The pairing sets live in the tier-C `kitchen_index` pack, which the public seeds
    # tier does NOT bundle (onto: ["*"] = A+B only). SKIP rather than crash where it's
    # stripped — the thesaurus/server tiers (which ship kitchen_index) still exercise it.
    pairing_ak = "ontology/kitchen_index/pairing_sets.ak"
    wine_aks = sorted(glob.glob("ontology/wine/*.ak"))
    if not os.path.exists(pairing_ak) or not wine_aks:
        missing = "kitchen_index" if not os.path.exists(pairing_ak) else "wine"
        print(f"  SKIP  the '{missing}' pack is not bundled in this build "
              "(kitchen_index is tier-C, excluded from the seeds tier) — pairing-set derivation skipped")
        sys.exit(0)

    tmp = tempfile.mkdtemp()
    ne = NucleusEngine(os.path.join(tmp, "pairing_eval.db"))

    # Phase 1 — atoms + aliases from the wine pack (defines cheese:* / wine:*).
    for f in wine_aks:
        _load(ne, f, "atoms")
    # Phase 2 — the cross-pack set.add (kitchen_index → wine atoms), as the
    # global-relations phase runs it after every pack's aliases exist.
    _load(ne, pairing_ak, "rel")

    ok = True
    for name, floor in EXPECT.items():
        mem = ne.list_set(name) or []
        keys = [m if isinstance(m, str) else (m.get("key") or m.get("id")) for m in mem]
        resolved = sum(1 for k in keys if ne.get_aliases_by_key(k))
        good = len(mem) >= floor and resolved == len(mem) and len(mem) > 0
        ok = ok and good
        print(f"  {name:16}: {len(mem)} members, {resolved} alias-resolvable "
              f"(expect >= {floor}) — {'PASS' if good else 'FAIL'}")

    print("RESULT:", "PASS — pairing sets populate cross-pack" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
