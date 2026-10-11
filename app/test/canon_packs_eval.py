#!/usr/bin/env python3
"""
THE PACKS CARRY THEIR OWN CANONICAL SHAPE — generated at build time, and the law holds structurally (purge A4).

The Product · Component · Method · Producer law used to be derived by the platform at every ontology ingestion. It is now
the application's: the law is data (`app/ontology/kitchen_index/canon.json`), `app/scripts/gen_canonical.py` applies it to
the authored packs, and each pack carries the result as `canonical.ak`. Held here:

  1. every `canonical.ak` is FRESH — regenerating writes nothing (the build gate: `gen_canonical.py --check`)
  2. the generator is DETERMINISTIC and each file says it is generated
  3. THE LAW, asserted structurally over the packs' own statements (the A0 count baseline was withdrawn as a gate,
     4 October): every product entry is `sys:is_a <domain>` and in `<domain>:all`; every recipe is `sys:method_of` a
     product that is in `meal:all` AND `meal:with_recipe`; every product → component material link has its
     `sys:made_from`; every product → producer link has its `sys:made_by`; every endpoint a canonical statement names is
     defined by some pack (nothing a loader would refuse)
  4. the law has no member the platform has to name: `canon.json` carries the domains, and the kitchen's vocabulary
  5. no pack's authored `.ak` adds to a canonical SET by hand (`meal:all`, `drink:all`, `meal:with_recipe`, … — a hand-written
     one would be a second author); other domains (ayurveda, …) use the universal `sys:made_from` freely, and the
     hand-authored upper atoms in `canon_upper.ak` are the only exception (definitions and the domain→role links)

The live check — load every pack on a fresh cell, zero loader refusals, the canonical sets equal the baseline — is
`canon_packs_load_eval.py` (long: it loads the whole ontology).

Run:  python app/test/canon_packs_eval.py     (exit 0 = all pass)
"""
import glob
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
_fails = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   ({detail})" if detail else ""))
    if not ok:
        _fails.append(name)


def _parse(path):
    import shlex
    for raw in open(path, encoding="utf-8", errors="ignore"):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        try:
            parts = shlex.split(line)
        except ValueError:
            parts = line.split()
        if parts:
            yield parts


def check_law():
    """The Product · Component · Method · Producer law, read independently of the generator from the packs' statements."""
    ont = os.path.join(ROOT, "app", "ontology")
    law = {"domains": {}, "hub": set(), "pns": [], "mat": {}, "prod": {}}
    for f in glob.glob(os.path.join(ont, "*", "canon.json")):
        doc = json.load(open(f, encoding="utf-8"))
        law["domains"].update(doc.get("domains") or {})
        law["hub"].update(doc.get("hub_exclude") or [])
        law["pns"] += [n for n in (doc.get("product_ns") or []) if isinstance(n, str) and not n.startswith("_")]
        for key, out in (("material_rels", law["mat"]), ("producer_rels", law["prod"])):
            for rel, spec in (doc.get(key) or {}).items():
                if not rel.startswith("_") and isinstance(spec, dict):
                    out[rel] = spec.get("targets") or ["*"]
    defined, authored, canon_links, canon_sets = set(), [], set(), set()
    for f in sorted(glob.glob(os.path.join(ont, "*", "*.ak"))):
        is_canon = os.path.basename(f) == "canonical.ak"
        for p in _parse(f):
            c = p[0].lower()
            if c == "def" and len(p) >= 2:
                defined.add(p[1])
            elif c == "al" and len(p) >= 3:
                defined.add(p[2])
            elif c == "ln" and len(p) >= 4:
                (canon_links.add((p[1], p[2], p[3])) if is_canon else authored.append((p[1], p[2], p[3])))
                if is_canon:
                    canon_links.add((p[1], p[2], p[3]))
            elif c == "set.add" and is_canon:
                kv = dict(x.split("=", 1) for x in p[1:] if "=" in x)
                canon_sets.add((kv.get("name"), kv.get("id")))
    alias_all = defined | {a for (a, _d, _r) in authored} | {d for (_a, d, _r) in authored}

    def members(cfg):
        out = set()
        for prefix, depth in cfg.get("member_ns", ()):
            out |= {a for a in defined if a.startswith(prefix + ":") and a.count(":") == depth and a not in law["hub"]}
        return out

    bad = []
    prod_all = {}
    for dom, cfg in law["domains"].items():
        for a in members(cfg):
            if (a, dom, "sys:is_a") not in canon_links:
                bad.append("%s not sys:is_a %s" % (a, dom))
            for sname in (cfg.get("all_set"), cfg.get("rollup_set"), cfg.get("method_marker")):
                if sname and (sname, a) not in canon_sets:
                    bad.append("%s not in %s" % (a, sname))
        if cfg.get("role") == "role:product":
            prod_all[dom] = members(cfg)
    check("every product / component / method / producer entry is sys:is_a its domain and in its sets",
          not bad, "%d: %s" % (len(bad), bad[:3]))

    meal_all = {a for (n, a) in canon_sets if n == "meal:all"}
    with_recipe = {a for (n, a) in canon_sets if n == "meal:with_recipe"}
    rbad = []
    for dom, cfg in law["domains"].items():
        if cfg.get("role") != "role:method":
            continue
        for m in members(cfg):
            tgt = [d for (s_, d, r) in canon_links if s_ == m and r == "sys:method_of"]
            if len(tgt) != 1:
                rbad.append("%s method_of=%s" % (m, tgt))
            elif tgt[0] not in meal_all or tgt[0] not in with_recipe:
                rbad.append("%s -> %s not in meal:all + meal:with_recipe" % (m, tgt[0]))
    check("every recipe is sys:method_of ONE product, and that product is in meal:all and meal:with_recipe (recipe ⊆ meal)",
          not rbad, "%d: %s" % (len(rbad), rbad[:3]))

    mbad = []
    for (s_, d, r) in authored:
        tg = law["mat"].get(r)
        if tg and any(s_.startswith(ns + ":") for ns in law["pns"]) and ("*" in tg or any(d.startswith(t + ":") for t in tg)):
            if (s_, d, "sys:made_from") not in canon_links:
                mbad.append("%s -> %s" % (s_, d))
        ptg = law["prod"].get(r)
        if ptg and ("*" in ptg or any(d.startswith(t + ":") for t in ptg)):
            if (s_, d, "sys:made_by") not in canon_links:
                mbad.append("made_by %s -> %s" % (s_, d))
    check("every product → component link carries sys:made_from, every product → producer link sys:made_by",
          not mbad, "%d: %s" % (len(mbad), mbad[:3]))

    dangling = sorted({x for (a, d, _r) in canon_links for x in (a, d)
                       if x not in alias_all and x not in law["domains"] and not x.startswith("role:")})
    check("every endpoint a canonical statement names is defined by a pack (nothing a loader would refuse)",
          not dangling, "%d: %s" % (len(dangling), dangling[:4]))


def main():
    gen = os.path.join(ROOT, "app", "scripts", "gen_canonical.py")
    r = subprocess.run([sys.executable, gen, "--check"], capture_output=True, text=True)
    check("every canonical.ak is fresh (`gen_canonical.py --check` writes nothing)", r.returncode == 0,
          (r.stdout or r.stderr).strip()[-160:])
    files = sorted(glob.glob(os.path.join(ROOT, "app", "ontology", "*", "canonical.ak")))
    check("the packs carry their canonical shape (canonical.ak in %d packs)" % len(files), len(files) >= 5)
    check("each canonical.ak says it is GENERATED and is not to be edited",
          all(open(f, encoding="utf-8").read().startswith("# GENERATED by app/scripts/gen_canonical.py") for f in files))

    check_law()

    law = json.load(open(os.path.join(ROOT, "app", "ontology", "kitchen_index", "canon.json"), encoding="utf-8"))
    check("canon.json carries the law as data: the domains, the hub exclusions and the kitchen's translation rows",
          {"domains", "hub_exclude", "product_ns", "material_rels", "producer_rels"} <= set(law)
          and {"meal", "recipe", "ingredient", "drink", "cocktail", "wine", "spirit", "producer"} <= set(law["domains"]))

    canon_rel = re.compile(r"name=\"(?:meal|ingredient|recipe|drink|cocktail|wine|spirit|producer):all\"|name=\"(?:meal|drink):with_recipe\"")
    by_hand = []
    for f in sorted(glob.glob(os.path.join(ROOT, "app", "ontology", "*", "*.ak"))):
        if os.path.basename(f) in ("canonical.ak", "canon_upper.ak"):
            continue
        for n, line in enumerate(open(f, encoding="utf-8", errors="ignore"), 1):
            if not line.lstrip().startswith("#") and canon_rel.search(line) and not line.startswith(("def ", "al ")):
                by_hand.append("%s:%d" % (os.path.relpath(f, ROOT), n))
                break
    check("no pack authors a canonical statement by hand (one author: the generator)", not by_hand, str(by_hand[:4]))
    print()
    if _fails:
        print("RESULT: FAIL (%d): %s\n" % (len(_fails), "; ".join(_fails)))
        return 1
    print("RESULT: PASS — the packs carry their canonical shape, generated from canon.json at build time, fresh, "
          "deterministic, hand-authored nowhere, and the law holds structurally.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
