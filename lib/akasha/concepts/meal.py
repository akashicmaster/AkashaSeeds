"""
Meal Concept Model — the DICTIONARY over the whole meal (dish) product layer.

`meal` is the food PRODUCT super-concept in the canonical Product·Component·Method upper ontology
(lib/akasha/canon.py). Every dish is `sys:is_a meal` and joins `meal:all` — the COMPLETE
dictionary, the superset. Having a recipe (a `sys:method_of` from `recipe:*`) or known ingredients
(`sys:made_from`) is a PROPERTY of an entry, never a condition for being in the dictionary — so a
meal can appear here with its method or its parts simply missing.

This is the surface the "料理は料理でひとまとまり" principle asks for: one cohesive list of every
meal, over which the recipe layer and the ingredient layer are subsets you can see the presence
or absence of. It reads the live graph via DictionaryConcept's shared-namespace mode (entities =
members of `meal:all`, built automatically by the normalizer — not a hand-maintained set):

  meal.search   name/keyword lookup across every meal
  meal.ls       browse by axis — cuisine, country, and `has_recipe` (the with-method subset)
  meal.get      a meal's profile — its ingredients (components), its recipe(s) (method), and
                whether each is present or missing

`smallplate.*` is a narrower view of the SAME product layer (the small-plate subset); `recipe.*`
is the method layer (a subset of meals); `ingredient.*` is the component layer.
"""
import logging
from typing import Any, Dict, List

from lib.akasha.concepts.dictionary import DictionaryConcept
from lib.akasha import canon

logger = logging.getLogger("Harmonia.Concept.Meal")


class MealConcept(DictionaryConcept):
    """Dictionary over the complete meal (dish) product layer — the superset, with the recipe
    and ingredient layers visible as present-or-missing properties."""

    CONCEPT_PREFIX = "meal"
    CONCEPT_LABEL  = ("meal dictionary — every dish (the product superset), with its ingredients "
                      "and recipe shown as present-or-missing")
    NOUN   = "meal"
    ID_KEY = "meal_id"
    AXES   = ()

    NS         = "dish"                 # meal entries live in the shared dish: namespace …
    ENTITY_SET = "meal:all"            # … and ARE the members of the canonical superset set
    ENTITY_EXCLUDE = frozenset({"dish:smallplate"})
    AXIS_SPEC = {
        "cuisine": ("cuisine:{v}",    "thesaurus:related"),
        "country": ("dish:from:{v}",  DictionaryConcept.SET_AXIS),
        # the with-method subset, as a browsable axis (dish:* in meal:with_recipe)
        "has_recipe": ("meal:with_recipe", DictionaryConcept.SET_AXIS),
    }

    CONCEPT_METHODS = {
        "search": {"op": "op_search", "action": "read", "cli": "meal.search", "args": ["q"],
                   "desc": "Search meals by name/keyword: meal search <q> [limit=]"},
        "ls":     {"op": "op_ls", "action": "read", "cli": "meal.ls", "args": [],
                   "desc": ("Browse meals by axis: meal ls [cuisine=spanish] [country=spain] "
                            "[recipe=yes] — recipe=yes limits to meals that carry a method")},
        "get":    {"op": "op_get", "action": "read", "cli": "meal.get", "args": ["id"],
                   "desc": ("Meal profile — ingredients, recipe(s), and whether each is present: "
                            "meal get id=dish:<slug>")},
    }

    def _components(self, key: str) -> List[str]:
        """The meal's ingredients (canonical `sys:made_from` targets), by last path segment."""
        out = set()
        for dst, rel in (self.cortex.get_adjacent_links(key) or []):
            if rel == canon.MADE_FROM and self._visible(dst):
                nm = self._name(dst) or ""
                out.add(nm.split(":", 1)[1] if ":" in nm else nm)
        return sorted(out)

    def _methods(self, key: str) -> List[str]:
        """The meal's recipe(s) — the incoming `sys:method_of` edges (the method layer)."""
        out = set()
        for src, rel in (self.cortex.get_incoming_links(key, canon.METHOD_OF) or []):
            if rel == canon.METHOD_OF and self._visible(src):
                nm = self._name(src) or ""
                out.add(nm.split(":", 1)[1] if ":" in nm else nm)
        return sorted(out)

    def op_search(self, q: str = "", name: str = "", limit: Any = "",
                  offset: Any = 0, cursor: Any = "") -> Dict[str, Any]:
        """[meal.search] Find meals whose name or description contains every query token, across
        the complete dictionary. READ-level; paginated (default 20, max 100)."""
        return self._dict_search(q or name, limit, offset, cursor)

    def op_ls(self, cuisine: str = "", country: str = "", recipe: str = "", limit: Any = "",
              offset: Any = 0, cursor: Any = "") -> Dict[str, Any]:
        """[meal.ls] Browse meals by axis — `cuisine`, `country`, and `recipe=yes` (limit to the
        subset that carries a method). Axes intersect. READ-level; paginated (default 20, max
        100)."""
        filt = {"cuisine": cuisine, "country": country}
        if str(recipe).strip().lower() in ("yes", "true", "1", "y"):
            filt["has_recipe"] = "with_recipe"     # the value component of meal:with_recipe
        return self._dict_ls(filt, limit, offset, cursor)

    def op_get(self, id: str = "", name: str = "") -> Dict[str, Any]:
        """[meal.get] A meal's profile — its ingredients (components) and recipe(s) (method),
        each shown as present or missing, plus cuisine/country. This is the whole-meal view over
        which the recipe and ingredient layers are subsets. READ-level."""
        ref = (id or name).strip()
        key = self._resolve(ref)
        if not key:
            raise ValueError("meal.get: no such meal.")
        prof = self._profile(key, self._alias_of(key, ref))    # id/key/name/note/cuisine
        prof["type"] = "meal:profile"
        ings = self._components(key)
        recs = self._methods(key)
        prof["ingredients"] = ings
        prof["recipes"] = recs
        prof["has_ingredients"] = bool(ings)
        prof["has_recipe"] = bool(recs)
        return prof
