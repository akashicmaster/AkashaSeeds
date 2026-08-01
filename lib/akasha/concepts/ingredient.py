"""
Ingredient Concept Model — a food/ingredient DICTIONARY over the ontology's `ingred:*` concepts.

Ingredients already exist as `ingred:<category>:<name>` concept atoms (base packs, so present in
every tier), each carrying a description plus curated dimensions — allergens (`bio:allergen →
allergen:*`) and seasonality (`in_season → season:*`) — and the category is the alias's own
second segment (fruit / vegetable / meat / seafood / nut / …). IngredientConcept reads that live
graph via DictionaryConcept and exposes three clear READ operators:

  ingredient.search   name/keyword lookup across the ingredient concepts
  ingredient.ls       browse by axis — category, allergen, season
  ingredient.get      a dictionary entry — category, description, allergens, seasons

This is a separate concept from recipe.food.search on purpose: food.search is the *recipe
ingredient picker* (name → fdc → nutrition over the `food:*` catalogue); ingredient.* is the
*dictionary* over the `ingred:*` concept layer (category / allergen / season). Two clear
surfaces, not one switched by a parameter. There are no pairing edges on ingredients, so there
is no pairs operator.
"""
import logging
from typing import Any, Dict, List, Tuple

from lib.akasha.concepts.dictionary import DictionaryConcept
from lib.akasha.concepts.formula import _paginate
from lib.akasha.concepts.foodnutri import parse_nutrition

logger = logging.getLogger("Harmonia.Concept.Ingredient")


class IngredientConcept(DictionaryConcept):
    """Dictionary over `ingred:<category>:<name>` — browse by category / allergen / season."""

    CONCEPT_PREFIX = "ingredient"
    CONCEPT_LABEL  = ("ingredient dictionary — food concepts by category, with allergens "
                      "and seasonality")
    NOUN   = "ingredient"
    ID_KEY = "ingredient_id"
    AXES   = ()

    NS           = "ingred"
    ENTITY_KINDS = ()          # categories are open-ended; enumerate all ingred:*:* by depth
    ENTITY_DEPTH = 2           # an ingredient alias is ingred:<category>:<name> (2 colons)
    KIND_FIELD   = "category"  # the 2nd segment is the food category
    # The USDA/FDA nutrition pack (`food:*`) bridges to the concept layer here:
    # `food:<usda_entry> --thesaurus:related--> ingred:<concept>` (so it is an INCOMING edge).
    FOOD_BRIDGE_REL = "thesaurus:related"
    # NB: `in_season` is authored as a bare relation, which the loader namespaces to
    # `calc:in_season` (bare rels default to calc:); `bio:allergen` is already namespaced and
    # stored verbatim. The stored forms are what we match here. `use` is a SET axis — the
    # culinary theme groupings (culinary:sushi_neta / :ceviche / :carpaccio / :bbq / :smoothie /
    # :pickling / :smoked / :baby_food) are membership sets, not links.
    AXIS_SPEC    = {
        "allergen": ("allergen:{v}", "bio:allergen"),
        "season":   ("season:{v}",   "calc:in_season"),
        "use":      ("culinary:{v}", DictionaryConcept.SET_AXIS),
    }

    # Multi-valued dimensions gathered by `get` (an ingredient may have several).
    _GROUPS = (
        ("allergens", "bio:allergen",   True),
        ("seasons",   "calc:in_season", True),
    )

    CONCEPT_METHODS = {
        "search": {"op": "op_search", "action": "read", "cli": "ingredient.search",
                   "args": ["q"],
                   "desc": "Search ingredients by name/keyword: ingredient search <q> [limit=]"},
        "ls":     {"op": "op_ls", "action": "read", "cli": "ingredient.ls", "args": [],
                   "desc": ("Browse ingredients by axis: ingredient ls [category=fruit] "
                            "[allergen=tree_nut] [season=spring] "
                            "[use=sushi_neta|ceviche|carpaccio|bbq|…]")},
        "get":    {"op": "op_get", "action": "read", "cli": "ingredient.get", "args": ["id"],
                   "desc": ("Ingredient entry — category, description, allergens, seasons: "
                            "ingredient get id=ingred:fruit:strawberry")},
        "nutrition": {"op": "op_nutrition", "action": "read", "cli": "ingredient.nutrition",
                      "args": ["id"],
                      "desc": ("USDA/FDA nutrition for an ingredient — its FoodData Central "
                               "variants + per-basis nutrition: ingredient nutrition "
                               "id=ingred:fruit:apple")},
    }

    def _bridged_foods(self, key: str) -> List[Tuple[str, str]]:
        """The USDA `food:*` nutrition entries bridged to this ingredient concept — the
        FoodData Central variants that link to it (incoming thesaurus:related). Scope-filtered,
        de-duped, sorted by alias. This is where the nutrition pack meets the dictionary."""
        out: Dict[str, str] = {}
        for src, rel in (self.cortex.get_incoming_links(key, self.FOOD_BRIDGE_REL) or []):
            if rel != self.FOOD_BRIDGE_REL or not self._visible(src):
                continue
            alias = self._name(src) or ""
            if alias.startswith("food:"):
                out.setdefault(src, alias)
        return sorted(out.items(), key=lambda kv: kv[1])

    def _food_row(self, fkey: str, falias: str) -> Dict[str, Any]:
        content = self.cortex.get_chunk(fkey) or ""
        nut = parse_nutrition(content) or {}
        per = {k: v for k, v in nut.items() if k != "basis_g"}
        head = content.split(" — ")[0].strip() if " — " in content else falias.split(":")[-1]
        return {"key": fkey, "food": falias, "name": head, "fdc": self._fdc_of(fkey),
                "basis_g": nut.get("basis_g") if nut else None, "per_basis": per}

    def _culinary_uses(self, key: str) -> List[str]:
        """The culinary theme groupings this ingredient belongs to (`sushi_neta`, `ceviche`, …).
        The themes are labelled `theme:<slug>` with a matching membership set `culinary:<slug>`;
        we resolve the theme list dynamically (so new themes appear) and test set membership."""
        cores = []
        cc = getattr(self.cortex, "core", None)
        if cc is not None:
            cores.append(cc)
        nc = getattr(getattr(self.session, "nucleus", None), "core", None)
        if nc is not None and nc is not cc:
            cores.append(nc)
        slugs = set()
        for core in cores:
            for row in (core.get_aliases_by_pattern("theme:%") or []):
                alias = row.get("alias", "")
                if alias.count(":") == 1:
                    slugs.add(alias.split(":", 1)[1])
        return sorted(s for s in slugs
                      if key in set(self.cortex.get_collection_members(f"culinary:{s}") or []))

    def _representative_nutrition(self, foods: List[Tuple[str, str]]):
        """One representative nutrition row for the get card: prefer a `raw` USDA variant (the
        base, unprepared form — the fairest single figure for an ingredient), else the first
        variant that carries parseable nutrition. None when nothing bridges/parses."""
        rows = [self._food_row(fk, fa) for fk, fa in foods]
        rows = [r for r in rows if r.get("per_basis")]
        if not rows:
            return None
        for r in rows:
            if "raw" in r["food"].lower() or "raw" in (r["name"] or "").lower():
                return r
        return rows[0]

    def op_search(self, q: str = "", name: str = "", limit: Any = "",
                  offset: Any = 0, cursor: Any = "") -> Dict[str, Any]:
        """[ingredient.search] Find ingredients whose name or description contains every query
        token. READ-level; paginated (default 20, max 100)."""
        return self._dict_search(q or name, limit, offset, cursor)

    def op_ls(self, category: str = "", allergen: str = "", season: str = "",
              use: str = "", limit: Any = "", offset: Any = 0, cursor: Any = "") -> Dict[str, Any]:
        """[ingredient.ls] Browse ingredients by axis — `category` (fruit/vegetable/meat/…),
        `allergen` (tree_nut/dairy/…), `season` (spring/summer/autumn/winter), and `use` — the
        culinary theme groupings (`sushi_neta`, `ceviche`, `carpaccio`, `bbq`, `smoothie`,
        `pickling`, `smoked`, `baby_food`); axes intersect. READ-level; paginated
        (default 20, max 100)."""
        return self._dict_ls({"kind": category, "allergen": allergen, "season": season,
                              "use": use}, limit, offset, cursor)

    def op_get(self, id: str = "", name: str = "") -> Dict[str, Any]:
        """[ingredient.get] A dictionary entry — the ingredient's category, description, its
        curated allergens, seasons, and culinary `uses` (sushi_neta / ceviche / …), the count of
        USDA nutrition variants (`nutrition_variants`, full list via ingredient.nutrition), and a
        representative `nutrition` figure (the raw variant where present). READ-level."""
        ref = (id or name).strip()
        key = self._resolve(ref)
        if not key:
            raise ValueError("ingredient.get: no such ingredient.")
        alias = self._alias_of(key, ref)
        entry = {"type": "ingred:entry", "id": alias,
                 "name": alias.split(":")[-1].replace("_", " "),
                 "category": alias.split(":")[1] if alias.count(":") >= 2 else "",
                 "note": (self.cortex.get_chunk(key) or "").strip()}
        entry.update(self._link_groups(key, self._GROUPS))
        entry["uses"] = self._culinary_uses(key)            # sushi_neta / ceviche / …
        foods = self._bridged_foods(key)
        entry["nutrition_variants"] = len(foods)           # full list via ingredient.nutrition
        rep = self._representative_nutrition(foods)         # a representative (raw) figure inline
        if rep:
            entry["nutrition"] = {"name": rep["name"], "fdc": rep["fdc"],
                                  "basis_g": rep["basis_g"], "per_basis": rep["per_basis"]}
        return entry

    def op_nutrition(self, id: str = "", name: str = "", limit: Any = "",
                     offset: Any = 0, cursor: Any = "") -> Dict[str, Any]:
        """[ingredient.nutrition] The USDA/FDA nutrition for an ingredient concept — every
        `food:*` FoodData Central variant bridged to it, each with its per-basis nutrition and
        `fdc` id (parsed from the same content the recipe rollup reads). This is the ingredient
        dictionary's nutrition view over the nutrition pack. READ-level; paginated (default 20,
        max 100)."""
        ref = (id or name).strip()
        key = self._resolve(ref)
        if not key:
            raise ValueError("ingredient.nutrition: no such ingredient.")
        rows = [self._food_row(fk, fa) for fk, fa in self._bridged_foods(key)]
        page, nxt, more = _paginate(rows, self._page_limit(limit), cursor or offset)
        return {"type": "ingred:nutrition", "id": self._alias_of(key, ref),
                "results": page, "count": len(rows), "next_cursor": nxt, "has_more": more}
