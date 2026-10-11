"""
allergen_free_from.py — the allergen free-from view (computed).

Lists the ingredient concepts free of a given allergen (or free_from view) as
the food universe minus the foods that carry the excluded allergen(s) — so the
complement is never stored, only computed. Optionally materialises a
set:free_from:<view> .ak.

Usage:
    python app/scripts/allergen_free_from.py --list                 # available views
    python app/scripts/allergen_free_from.py --free-from gluten     # gluten-free foods
    python app/scripts/allergen_free_from.py --allergen fish        # fish-free foods
    python app/scripts/allergen_free_from.py --free-from nut --write ontology/base
"""
import argparse, glob, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def scan():
    ing = set(); alg = {}; views = {}
    for fp in glob.glob(os.path.join(ROOT, "ontology", "**", "*.ak"), recursive=True):
        t = open(fp, errors="ignore").read()
        for a in re.findall(r'^def "(ingred:[a-z_]+:[a-z_]+)"', t, re.M): ing.add(a)
        for a, al in re.findall(r'^ln (ingred:\S+) allergen:(\S+) bio:allergen', t, re.M):
            alg.setdefault(al, set()).add(a)
        for v, al in re.findall(r'^ln free_from:(\S+) allergen:(\S+) allergen:excludes', t, re.M):
            views.setdefault(v, set()).add(al)
    return ing, alg, views

def free_of(allergens, ing, alg):
    bad = set().union(*[alg.get(a, set()) for a in allergens]) if allergens else set()
    return sorted(ing - bad), sorted(bad)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--free-from"); ap.add_argument("--allergen")
    ap.add_argument("--list", action="store_true"); ap.add_argument("--write")
    a = ap.parse_args()
    ing, alg, views = scan()
    if a.list or not (a.free_from or a.allergen):
        print("allergens:", ", ".join(sorted(alg)))
        print("free_from views:", ", ".join(sorted(views)))
        return
    if a.free_from:
        excl = views.get(a.free_from, {a.free_from}); name = a.free_from
    else:
        excl = {a.allergen}; name = a.allergen
    free, bad = free_of(excl, ing, alg)
    print(f"free_from:{name} — excludes {sorted(excl)}")
    print(f"  {len(free)} free / {len(bad)} excluded (of {len(ing)})")
    if a.write:
        L = [f"# Materialised free-from set for {name} (computed complement).",
             f'def "set:free_from:{name}" "Foods free of {name}."']
        L += [f'set.add name="free_from:{name}" id="{x}"' for x in free]
        p = os.path.join(a.write, f"free_from_{name}.ak")
        open(p, "w").write("\n".join(L) + "\n"); print("  wrote", p)
    else:
        print("  excluded:", ", ".join(x.split(":")[-1] for x in bad))
if __name__ == "__main__":
    main()
