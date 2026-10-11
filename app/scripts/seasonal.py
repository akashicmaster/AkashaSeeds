"""
seasonal.py — region-relative "what's in season" view (computed).

An ingredient carries its harvest SEASON (climate-relative); the hemisphere ×
season → month cross lives once in seasonality.ak. This resolves, for a given
hemisphere and month, which seasons map to that month, then lists the
ingredients in those seasons (year_round always included).

Usage:
    python app/scripts/seasonal.py --hemisphere north --month october
    python app/scripts/seasonal.py --hemisphere south --month october
    python app/scripts/seasonal.py --season autumn        # season → ingredients
"""
import argparse, glob, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def scan():
    in_season = {}      # season -> {ingredients}
    seasonmap = {}      # (hemi, month) -> {seasons}
    for fp in glob.glob(os.path.join(ROOT, "ontology", "**", "*.ak"), recursive=True):
        t = open(fp, errors="ignore").read()
        for ing, s in re.findall(r'^ln (ingred:\S+) season:(\S+) in_season', t, re.M):
            in_season.setdefault(s, set()).add(ing)
        for s, m, h in re.findall(r'^ln season:(\S+) month:(\S+) seasonmap:(\S+)', t, re.M):
            seasonmap.setdefault((h, m), set()).add(s)
    return in_season, seasonmap

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hemisphere", choices=["north", "south"])
    ap.add_argument("--month"); ap.add_argument("--season")
    a = ap.parse_args()
    in_season, seasonmap = scan()
    if a.season:
        seasons = {a.season}
        label = f"season:{a.season}"
    else:
        if not (a.hemisphere and a.month):
            print("give --season, or --hemisphere and --month"); return
        seasons = seasonmap.get((a.hemisphere, a.month.lower()), set())
        label = f"{a.hemisphere} / {a.month} → seasons {sorted(seasons)}"
    foods = sorted(set().union(*[in_season.get(s, set()) for s in seasons]) if seasons else set())
    print(label)
    print(f"  {len(foods)} in season:", ", ".join(x.split(':')[-1] for x in foods))
if __name__ == "__main__":
    main()
