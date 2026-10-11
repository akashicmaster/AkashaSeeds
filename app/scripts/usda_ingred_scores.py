"""
usda_ingred_scores.py — derive ingredient sweetness from USDA sugars

The rec:sweetness flavour scores only existed for 5 hand-authored fruits, so the
ingredient→taste bridge reached almost nothing. This estimates sweetness for the
culinary ingredient concepts (ingred:*) from USDA FoodData Central: it matches
each ingredient to the USDA foods that share its head word and takes the median
Total Sugars (nutrient 269) per 100g, mapped to a 0–1 sweetness.

Total *sugars* (not total carbohydrate) is used on purpose — starch-heavy foods
(bread, potato) are carb-rich but not sweet. Ingredients that already carry a
hand-authored rec:sweetness are left untouched.

Output: ontology/base/ingred_scores_usda.ak   (provenance: inferred from USDA)
Then re-run app/scripts/ingred_taste_bridge.py to extend the taste links.

Usage:
    python app/scripts/usda_ingred_scores.py --food-json <sr_legacy_or_foundation>.json
    python app/scripts/usda_ingred_scores.py --food-json <..>.json --dry-run
"""
import argparse, glob, json, os, re, statistics, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, "ontology", "base", "ingred_scores_usda.ak")
SUGAR_NUTRIENT = "269"          # USDA "Total Sugars", g/100g
SWEET_DIVISOR  = 15.0           # sugar g / 15, capped at 1.0 (≈ fruits ≥ 0.6, veg < 0.4)


def singular(w):
    w = w.lower()
    if len(w) > 4 and w.endswith("ies"): return w[:-3] + "y"
    if len(w) > 4 and w.endswith("oes"): return w[:-2]
    if len(w) > 3 and w.endswith("s") and not w.endswith("ss"): return w[:-1]
    return w


def toke(s):
    s = unicodedata.normalize("NFD", s or "").encode("ascii", "ignore").decode().lower()
    return [t for t in re.split(r"[^a-z0-9]+", s) if t]


def load_ingredients():
    """ingred atom -> set of candidate head tokens (from term + aliases); and the
    set of atoms that already have a hand-authored rec:sweetness."""
    cand, scored = {}, set()
    for fp in glob.glob(os.path.join(ROOT, "ontology", "**", "*.ak"), recursive=True):
        if os.path.abspath(fp) == os.path.abspath(OUT):
            continue                     # ignore our own output so re-runs regenerate
        txt = open(fp, errors="ignore").read()
        for a in re.findall(r'^def\s+"(ingred:[^"]+)"', txt, re.M):
            toks = toke(a.split(":")[-1])
            if toks:
                cand.setdefault(a, set()).add(singular(toks[-1]))
                cand[a].add(singular(toks[0]))
        for a, al in re.findall(r'^al\s+(ingred:\S+)\s+(\S+)', txt, re.M):
            t = toke(al)
            if t and a in cand:
                cand[a].add(singular(t[-1]))
        for a in re.findall(r'^ln\s+(ingred:\S+)\s+score:[0-9.]+\s+rec:sweetness', txt, re.M):
            scored.add(a)
    return cand, scored


def food_sugar_by_head(food_json):
    """head token (singular of the food's first word) -> list of sugar values."""
    d = json.load(open(food_json, encoding="utf-8"))
    foods = d.get("SRLegacyFoods") or d.get("FoundationFoods") or d.get("foods") or []
    by = {}
    for f in foods:
        desc = f.get("description") or ""
        segs = desc.split(",")
        # index under the first segment's word(s) AND the first word of the 2nd
        # segment — so "Nuts, chestnuts, …" is reachable as both nut and chestnut.
        heads = set()
        s0 = toke(segs[0])
        if s0:
            heads.add(singular(s0[-1] if len(s0) == 1 else s0[0]))
        if len(segs) > 1:
            s1 = toke(segs[1])
            if s1:
                heads.add(singular(s1[0]))
        if not heads:
            continue
        sugar = None
        for fn in f.get("foodNutrients", []):
            n = fn.get("nutrient", {})
            if str(n.get("number")) == SUGAR_NUTRIENT:
                sugar = fn.get("amount"); break
        if sugar is not None:
            for h in heads:
                by.setdefault(h, []).append(float(sugar))
    return by, len(foods)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--food-json", required=True)
    ap.add_argument("--divisor", type=float, default=SWEET_DIVISOR)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cand, scored = load_ingredients()
    by_head, nfoods = food_sugar_by_head(args.food_json)
    print(f"ingredients: {len(cand)} ({len(scored)} already scored) | USDA foods: {nfoods} | sugar heads: {len(by_head)}")

    # Savoury categories are not sweet ingredients; cap them so a spurious
    # single sugar match (e.g. a glazed-meat food sharing a head word) can't
    # wrongly cross the taste-bridge threshold.
    SAVOURY  = {"meat", "seafood", "poultry", "pork", "beef", "game_meat", "processed_meat", "fish"}
    # Seasonings are aromatic, not sugar-sweet; keep them below the taste threshold
    # so a stray sugary-product match (e.g. cinnamon rolls) can't cross it.
    AROMATIC = {"spice", "herb", "additive"}
    rows = []          # (ingred, sweetness, n_matches, sugar)
    for atom, heads in sorted(cand.items()):
        if atom in scored:
            continue
        vals = []
        for h in heads:
            vals += by_head.get(h, [])
        if not vals:
            continue
        sugar = statistics.median(vals)
        sweet = round(min(1.0, sugar / args.divisor), 2)
        cat = atom.split(":")[1] if atom.count(":") >= 2 else ""
        if cat in SAVOURY:
            sweet = min(sweet, 0.3)
        elif cat in AROMATIC:
            sweet = min(sweet, 0.5)
        rows.append((atom, sweet, len(vals), round(sugar, 1)))

    rows.sort(key=lambda r: -r[1])
    print(f"scored {len(rows)} new ingredients. Top / bottom samples:")
    for r in rows[:8] + rows[-4:]:
        print(f"  {r[0]:30s} sweetness={r[1]}  (sugar {r[3]}g, n={r[2]})")

    if args.dry_run:
        print("(dry run — no file written)")
        return

    L = ["# Akasha ontology — ingredient sweetness (inferred from USDA sugars)",
         "# Generated by app/scripts/usda_ingred_scores.py from USDA Total Sugars (269).",
         "# sweetness = min(1, median_sugar_g/100g / %g). Provenance: inferred." % args.divisor,
         "# Ingredients with a hand-authored rec:sweetness are not overwritten.",
         "# Re-run app/scripts/ingred_taste_bridge.py afterwards to extend taste links.",
         ""]
    for atom, sweet, _, _ in rows:
        L.append(f"ln {atom} score:{sweet} rec:sweetness")
    open(OUT, "w").write("\n".join(L) + "\n")
    print(f"→ {OUT}")


if __name__ == "__main__":
    main()
