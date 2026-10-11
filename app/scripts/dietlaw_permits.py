"""
dietlaw_permits.py — religious dietary-law permissible view (computed).

Lists the ingredient concepts permissible under a dietary law as the food
universe minus the foods carrying any forbidden dietflag/allergen. Nothing is
stored per food; the complement is computed. --write materialises a set.

NOTE: for halal & kosher, permissible-species MEAT still requires certified
slaughter (dhabihah / shechita) — this view answers species permissibility only.

Usage:
    python app/scripts/dietlaw_permits.py --list
    python app/scripts/dietlaw_permits.py --law halal
    python app/scripts/dietlaw_permits.py --law vegan --write ontology/base
"""
import argparse, glob, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def scan():
    ing=set(); member={}; forbids={}
    for fp in glob.glob(os.path.join(ROOT,"ontology","**","*.ak"),recursive=True):
        t=open(fp,errors="ignore").read()
        for a in re.findall(r'^def "(ingred:[a-z_]+:[a-z_]+)"',t,re.M): ing.add(a)
        for a,grp in re.findall(r'^ln (ingred:\S+) ((?:dietflag|allergen):\S+) bio:\w+',t,re.M):
            member.setdefault(grp,set()).add(a)
        for law,tgt in re.findall(r'^ln dietlaw:(\S+) (\S+) dietlaw:forbids',t,re.M):
            forbids.setdefault(law,set()).add(tgt)
        for d,tgt in re.findall(r'^ln diet:(\S+) (\S+) diet:excludes',t,re.M):
            forbids.setdefault(d,set()).add(tgt)
    return ing, member, forbids

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--law"); ap.add_argument("--view"); ap.add_argument("--list",action="store_true"); ap.add_argument("--write")
    a=ap.parse_args()
    ing,member,forbids=scan()
    a.law = a.law or a.view
    if a.list or not a.law:
        print("laws:", ", ".join(sorted(forbids))); return
    tgts=forbids.get(a.law,set())
    bad=set().union(*[member.get(t,set()) for t in tgts]) if tgts else set()
    ok=sorted(ing-bad)
    print(f"{a.law} — forbids {sorted(tgts)}")
    print(f"  {len(ok)} permissible / {len(bad)} forbidden (of {len(ing)})")
    if a.write:
        L=[f"# Materialised permissible set for dietlaw:{a.law} (computed).",
           f'def "set:permit:{a.law}" "Foods permissible under {a.law}."']
        L+=[f'set.add name="permit:{a.law}" id="{x}"' for x in ok]
        p=os.path.join(a.write,f"dietlaw_{a.law}.ak"); open(p,"w").write("\n".join(L)+"\n"); print("  wrote",p)
    else:
        print("  forbidden e.g.:", ", ".join(x.split(":")[-1] for x in sorted(bad)[:20]))
if __name__=="__main__": main()
