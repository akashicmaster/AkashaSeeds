"""
cuisine_profile.py — show what's characteristic of a cuisine / dish / recipe.

Propagates the cuisine signature (region · flavour base + components · staple ·
hallmark technique) and, for a recipe, which signature ingredients it actually
uses (the concrete こだわり), flagging the shared 通底 (onion/garlic…) vs the
distinctive 違い.

Usage:
    python app/scripts/cuisine_profile.py --cuisine japanese
    python app/scripts/cuisine_profile.py --recipe teriyaki_chicken
    python app/scripts/cuisine_profile.py --dish paella
"""
import argparse, glob, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def scan():
    d = dict(region={}, sig={}, staple={}, comp={}, r_cui={}, r_ing={}, common=set())
    for fp in glob.glob(os.path.join(ROOT, "ontology", "**", "*.ak"), recursive=True):
        t = open(fp, errors="ignore").read()
        for c, r in re.findall(r'^ln cuisine:(\S+) region:(\S+) culinary:region', t, re.M):
            d["region"].setdefault(c, set()).add(r)
        for c, s in re.findall(r'^ln cuisine:(\S+) (\S+) cuisine:signature', t, re.M):
            d["sig"].setdefault(c, set()).add(s)
        for c, i in re.findall(r'^ln cuisine:(\S+) (ingred:\S+) cuisine:staple', t, re.M):
            d["staple"].setdefault(c, set()).add(i)
        for b, i in re.findall(r'^ln (flavor_base:\S+) (ingred:\S+) culinary:component', t, re.M):
            d["comp"].setdefault(b, set()).add(i)
        for r, c in re.findall(r'^ln (recipe:\S+|dish:\S+) cuisine:(\S+) ', t, re.M):
            d["r_cui"].setdefault(r, set()).add(c)
        for r, i in re.findall(r'^ln (recipe:\S+|dish:\S+) (ingred:\S+) ', t, re.M):
            d["r_ing"].setdefault(r, set()).add(i)
        for i in re.findall(r'^ln (ingred:\S+) culinary:common_thread culinary:common', t, re.M):
            d["common"].add(i)
    return d

def profile(cui, d, recipe_ings=None):
    print(f"cuisine:{cui}")
    print("  region:", ", ".join(sorted(d['region'].get(cui, []))) or "—")
    sigs = d['sig'].get(cui, set())
    bases = [s for s in sigs if s.startswith('flavor_base:')]
    techs = [s for s in sigs if s.startswith('technique:')]
    print("  staple:", ", ".join(x.split(':')[-1] for x in d['staple'].get(cui, [])) or "—")
    print("  signature technique:", ", ".join(x.split(':')[-1] for x in techs) or "—")
    for b in bases:
        comps = d['comp'].get(b, set())
        print(f"  flavour base {b.split(':')[-1]}:", ", ".join(x.split(':')[-1] for x in sorted(comps)))
        if recipe_ings is not None:
            used = comps & recipe_ings
            common = {x for x in used if x in d['common']}
            distinct = used - common
            print("     → in this dish — 違い(distinctive):",
                  ", ".join(x.split(':')[-1] for x in sorted(distinct)) or "(none)")
            print("       通底(shared):", ", ".join(x.split(':')[-1] for x in sorted(common)) or "(none)")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cuisine"); ap.add_argument("--recipe"); ap.add_argument("--dish")
    a = ap.parse_args()
    d = scan()
    if a.cuisine:
        profile(a.cuisine, d)
    else:
        key = f"recipe:{a.recipe}" if a.recipe else f"dish:{a.dish}"
        cuis = d['r_cui'].get(key, set())
        ings = d['r_ing'].get(key, set())
        print(f"{key} — cuisine: {', '.join(sorted(cuis)) or '—'}, {len(ings)} ingredients")
        for c in sorted(cuis):
            profile(c, d, recipe_ings=ings)
if __name__ == "__main__":
    main()
