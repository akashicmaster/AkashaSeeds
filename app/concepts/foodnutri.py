"""
Shared USDA/FDC food-nutrition parsing — one canonical parser for every food-facing concept.

Food atoms (`food:*`, the USDA FoodData Central catalogue in the nutrition pack) store their
nutrition as a descriptive content string, e.g.

    "Cheese, parmesan, grated — per 100g: 421 kcal, Protein 29.6g, Fat 28.0g, …"

`parse_nutrition` turns that into a `{basis_g, kcal, protein_g, …}` dict. It lives here, not in
any one concept, because both recipe (the ingredient picker / rollup) and ingredient (the
dictionary's nutrition view over the same `food:*` entries) need it — one parser, one behaviour.
"""
import re
from typing import Dict, Optional

# Descriptive nutrient label (as written in the USDA content string) → canonical key.
NUTR_LABEL_KEY = {
    "energy": "kcal", "kcal": "kcal", "calories": "kcal",
    "protein": "protein_g",
    "fat": "fat_g", "total fat": "fat_g",
    "carbohydrate": "carb_g", "carbohydrates": "carb_g", "carbs": "carb_g", "carb": "carb_g",
    "fiber": "fiber_g", "fibre": "fiber_g",
    "sugar": "sugar_g", "sugars": "sugar_g",
    "sodium": "sodium_mg", "calcium": "calcium_mg", "vitamin c": "vitc_mg",
}
_PER_BASIS_RE  = re.compile(r"per\s+(\d+(?:\.\d+)?)\s*g\b", re.I)
_KCAL_RE       = re.compile(r"(\d+(?:\.\d+)?)\s*k?cal\b", re.I)
_NUTR_FIELD_RE = re.compile(r"([A-Za-z][A-Za-z ]*?)\s+(\d+(?:\.\d+)?)\s*(mg|g)\b", re.I)


def parse_nutrition(content: str) -> Optional[Dict[str, float]]:
    """Parse a USDA-style content string into a nutrition dict, or None. Only fires on the
    `per <N>g:` basis marker so a food's descriptive name is never read as data."""
    if not content:
        return None
    mb = _PER_BASIS_RE.search(content)
    if not mb:
        return None
    seg = content[mb.end():]
    nut: Dict[str, float] = {}
    mk = _KCAL_RE.search(seg)
    if mk:
        nut["kcal"] = float(mk.group(1))
    for m in _NUTR_FIELD_RE.finditer(seg):
        label = m.group(1).strip().lower()
        key = NUTR_LABEL_KEY.get(label) or (
            NUTR_LABEL_KEY.get(label.split()[-1]) if label.split() else None)
        if key:
            nut[key] = float(m.group(2))
    if not nut:
        return None
    nut["basis_g"] = float(mb.group(1))
    return nut
