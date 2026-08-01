"""
Drink Concept Model — the DICTIONARY over the whole beverage (drink) product layer.

`drink` is the beverage PRODUCT umbrella in the canonical Product·Component·Method·Producer upper
ontology (lib/akasha/canon.py). The drink categories roll up into it — `cocktail sys:is_a drink`,
`wine sys:is_a drink`, `spirit sys:is_a drink` — and every one of their product entries joins
`drink:all`, the COMPLETE beverage dictionary (the superset). This is the drink-side analogue of
`meal`, and the surface the "飲料も一まとまり" principle asks for: one cohesive list of every drink,
over which its components and producer are visible as present-or-missing.

  drink.search   name/keyword lookup across every drink (cocktail / wine / spirit)
  drink.ls       browse by axis — category (cocktail/wine/spirit) and `recipe=yes` (the
                 with-method subset — cocktails carry an inline mixing method)
  drink.get      a drink's profile — its category, components (made_from), producer (made_by),
                 and whether it carries a method

The dual role is explicit: a spirit appears here as a PRODUCT (drunk neat), and the SAME atom is a
cocktail COMPONENT (a `sys:made_from` target) — `cocktail.get`/`drink.get` surfaces it as a part.
`cocktail.*` / `wine.*` / `spirit.*` remain the per-category surfaces; `drink.*` is the union.
Producers (distilleries, breweries) are NOT drinks and never appear here — they are the far side
of `made_by`.
"""
import logging
from typing import Any, Dict, List

from lib.akasha.concepts.dictionary import DictionaryConcept
from lib.akasha import canon

logger = logging.getLogger("Harmonia.Concept.Drink")


class DrinkConcept(DictionaryConcept):
    """Dictionary over the complete beverage product layer — the superset, with components and
    producer visible as present-or-missing properties."""

    CONCEPT_PREFIX = "drink"
    CONCEPT_LABEL  = ("drink dictionary — every beverage (the product superset): cocktails, wines "
                      "and spirits by category, with components and producer")
    NOUN   = "drink"
    ID_KEY = "drink_id"
    AXES   = ()

    NS         = ("cocktail", "wine", "whiskey", "rum", "tequila")   # namespaces drinks live in
    ENTITY_SET = "drink:all"          # the canonical superset (built automatically by normalizer)
    AXIS_SPEC = {
        # category value → its sub-domain superset (cocktail→cocktail:all, spirit→spirit:all, …)
        "category":   ("{v}:all",            DictionaryConcept.SET_AXIS),
        "has_recipe": ("drink:with_recipe",  DictionaryConcept.SET_AXIS),
    }

    # namespace → drink category (whiskey/rum/tequila all read as "spirit").
    _CATEGORY = {"cocktail": "cocktail", "wine": "wine",
                 "whiskey": "spirit", "rum": "spirit", "tequila": "spirit"}

    CONCEPT_METHODS = {
        "search": {"op": "op_search", "action": "read", "cli": "drink.search", "args": ["q"],
                   "desc": "Search drinks by name/keyword: drink search <q> [limit=]"},
        "ls":     {"op": "op_ls", "action": "read", "cli": "drink.ls", "args": [],
                   "desc": ("Browse drinks by axis: drink ls [category=cocktail|wine|spirit] "
                            "[recipe=yes] — recipe=yes limits to drinks that carry a method")},
        "get":    {"op": "op_get", "action": "read", "cli": "drink.get", "args": ["id"],
                   "desc": ("Drink profile — category, components, producer, method flag: "
                            "drink get id=cocktail:<slug>")},
    }

    def _category(self, alias: str) -> str:
        return self._CATEGORY.get(alias.split(":", 1)[0], "drink")

    def _adjacent(self, key: str, rel: str) -> List[str]:
        out = set()
        for dst, r in (self.cortex.get_adjacent_links(key) or []):
            if r == rel and self._visible(dst):
                nm = self._name(dst) or ""
                out.add(nm.split(":", 1)[1] if ":" in nm else nm)
        return sorted(out)

    def _profile(self, key: str, alias: str) -> Dict[str, Any]:
        """Adds the drink `category` (cocktail / wine / spirit) to the base profile."""
        prof = super()._profile(key, alias)
        prof["category"] = self._category(alias)
        return prof

    def op_search(self, q: str = "", name: str = "", limit: Any = "",
                  offset: Any = 0, cursor: Any = "") -> Dict[str, Any]:
        """[drink.search] Find drinks whose name or description contains every query token, across
        the complete beverage dictionary. READ-level; paginated (default 20, max 100)."""
        return self._dict_search(q or name, limit, offset, cursor)

    def op_ls(self, category: str = "", recipe: str = "", limit: Any = "",
              offset: Any = 0, cursor: Any = "") -> Dict[str, Any]:
        """[drink.ls] Browse drinks by axis — `category` (cocktail / wine / spirit) and
        `recipe=yes` (limit to the subset that carries a method). Axes intersect. READ-level;
        paginated (default 20, max 100)."""
        filt = {"category": category}
        if str(recipe).strip().lower() in ("yes", "true", "1", "y"):
            filt["has_recipe"] = "with_recipe"
        return self._dict_ls(filt, limit, offset, cursor)

    def op_get(self, id: str = "", name: str = "") -> Dict[str, Any]:
        """[drink.get] A drink's profile — its category, the components it is made from, the
        producer that makes it (where recorded), and whether it carries a method. This is the
        whole-drink view; each field may be present or missing. READ-level."""
        ref = (id or name).strip()
        key = self._resolve(ref)
        if not key:
            raise ValueError("drink.get: no such drink.")
        alias = self._alias_of(key, ref)
        prof = self._profile(key, alias)
        prof["type"] = "drink:profile"
        made_from = self._adjacent(key, canon.MADE_FROM)
        made_by = self._adjacent(key, canon.MADE_BY)
        prof["made_from"] = made_from
        prof["made_by"] = made_by
        wr = set(self.cortex.get_collection_members("drink:with_recipe") or [])
        prof["has_recipe"] = key in wr
        prof["has_components"] = bool(made_from)
        return prof
