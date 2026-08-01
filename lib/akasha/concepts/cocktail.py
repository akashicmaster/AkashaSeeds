"""
Cocktail Concept Model — a reference cocktail library, browsable by axis, with a recipe `get`.

Cocktails exist as attribute-rich `cocktail:*` atoms from TWO packs that share the namespace with
DIFFERENT relations, and CocktailConcept unifies both so all ~450 are browsable together:
  • ontology/wine/cocktails*.ak (A-tier): base=cocktail:base→spirit/liqueur/beverage,
    method=cocktail:mixed, plus taste / strength / garnish links.
  • ontology/drinks_c/cocktails.ak (C-tier, TheCocktailDB, 442 drinks): ingredients=cocktail:uses
    →ing:*, method=cocktail:method, category=sys:is_a→cocktail:category:*, strength in prose.
Several axes therefore accept multiple relations/namespaces (union). Cocktail is a DICTIONARY
(read the live graph) whose `get` reads like a recipe card. It reuses DictionaryConcept's search /
ls mechanism and adds a cocktail-specific `get` that collects the multi-valued recipe groups
(base/ingredient list, garnish, taste, occasion):

  cocktail.search   name/keyword lookup across the cocktails
  cocktail.ls       browse by axis — base spirit, taste, strength, method, glass
  cocktail.get      the recipe card — base(s), method, glass, garnish, taste, strength, occasion

Unlike wine/cheese there are no pairing edges in the data, so cocktail has no `pairs` operator;
its stance is reference-recipe discovery (browse → recipe). If per-user cocktail authoring is
wanted later, that is a separate FormulaConcept-based `cocktail.new`, not this reference view.

Note: `cocktail:alcoholic` / `cocktail:non_alcoholic` / `cocktail:cocktail` are 2-segment
*vocab* atoms (strength values, a hub), not cocktails — excluded via ENTITY_EXCLUDE. The `base`
axis resolves over the spirit: / liqueur: / beverage: namespaces, so `ls base=vermouth` (liqueur)
and `ls base=orange_juice` (beverage) work as well as `ls base=gin` (spirit).
"""
import logging
from typing import Any, Dict, List

from lib.akasha.concepts.dictionary import DictionaryConcept

logger = logging.getLogger("Harmonia.Concept.Cocktail")


class CocktailConcept(DictionaryConcept):
    """Reference cocktail dictionary — browse by base/taste/strength/method/glass; recipe get."""

    CONCEPT_PREFIX = "cocktail"
    CONCEPT_LABEL  = ("cocktail dictionary — reference recipes browsable by base / taste / "
                      "strength / method / glass")
    NOUN   = "cocktail"
    ID_KEY = "cocktail_id"
    AXES   = ()

    NS             = "cocktail"
    ENTITY_KINDS   = ()
    ENTITY_EXCLUDE = frozenset({"cocktail:alcoholic", "cocktail:non_alcoholic",
                                "cocktail:cocktail"})
    # Two cocktail datasets share this namespace with DIFFERENT relations, so several axes
    # accept multiple templates AND multiple relations (union):
    #   • wine pack (A-tier):  base=cocktail:base→spirit/liqueur/beverage, method=cocktail:mixed,
    #                          taste/strength/garnish links
    #   • drinks_c (TheCocktailDB): ingredients=cocktail:uses→ing:*, method=cocktail:method,
    #                          category=sys:is_a→cocktail:category:*, strength in prose (no link)
    AXIS_SPEC = {
        "base":     (["spirit:{v}", "liqueur:{v}", "beverage:{v}", "ing:{v}"],
                     ["cocktail:base", "cocktail:uses"]),
        "taste":    ("taste:{v}",           "cocktail:tastes"),
        "strength": ("cocktail:{v}",        "cocktail:strength"),   # alcoholic / non_alcoholic
        "method":   ("cocktail:method:{v}", ["cocktail:mixed", "cocktail:method"]),
        "glass":    ("glassware:{v}",       "cocktail:served_in"),
        "category": ("cocktail:category:{v}", "sys:is_a"),          # drinks_c (TheCocktailDB)
    }

    # Recipe-card groups collected by `get` (rel(s) -> field), and whether the field is a list.
    _GROUPS = (
        ("base",     ["cocktail:base", "cocktail:uses"], True),     # spirits (wine) + ings (drinks_c)
        ("taste",    "cocktail:tastes",                  True),
        ("garnish",  "cocktail:garnished_with",          True),
        ("occasion", "occasion:served_at",               True),
        ("method",   ["cocktail:mixed", "cocktail:method"], False),
        ("glass",    "cocktail:served_in",               False),
        ("strength", "cocktail:strength",                False),
        ("category", "sys:is_a",                         False),    # drinks_c category
    )

    CONCEPT_METHODS = {
        "search": {"op": "op_search", "action": "read", "cli": "cocktail.search", "args": ["q"],
                   "desc": "Search cocktails by name/keyword: cocktail search <q> [limit=]"},
        "ls":     {"op": "op_ls", "action": "read", "cli": "cocktail.ls", "args": [],
                   "desc": ("Browse cocktails by axis: cocktail ls [base=gin] [taste=sour] "
                            "[strength=alcoholic] [method=shaken] [glass=coupe] "
                            "[category=cocktail]")},
        "get":    {"op": "op_get", "action": "read", "cli": "cocktail.get", "args": ["id"],
                   "desc": ("Cocktail recipe card — base(s), method, glass, garnish, taste: "
                            "cocktail get id=cocktail:margarita")},
    }

    def op_search(self, q: str = "", name: str = "", limit: Any = "",
                  offset: Any = 0, cursor: Any = "") -> Dict[str, Any]:
        """[cocktail.search] Find cocktails whose name or note contains every query token.
        READ-level; paginated (default 20, max 100)."""
        return self._dict_search(q or name, limit, offset, cursor)

    def op_ls(self, base: str = "", taste: str = "", strength: str = "",
              method: str = "", glass: str = "", category: str = "", limit: Any = "",
              offset: Any = 0, cursor: Any = "") -> Dict[str, Any]:
        """[cocktail.ls] Browse cocktails by axis — `base` (gin/vodka/rum/vermouth/an ingredient),
        `taste` (sour/sweet/bitter/refreshing/…), `strength` (alcoholic|non_alcoholic), `method`
        (built/shaken/stirred/muddled/blended), `glass`, `category` (TheCocktailDB class); axes
        intersect. READ-level; paginated (default 20, max 100)."""
        return self._dict_ls({"base": base, "taste": taste, "strength": strength,
                              "method": method, "glass": glass, "category": category},
                             limit, offset, cursor)

    def op_get(self, id: str = "", name: str = "") -> Dict[str, Any]:
        """[cocktail.get] A cocktail's recipe card — its base spirit(s), mixing method, glass,
        garnish, taste, strength, and serving occasions, read from the structured links.
        READ-level."""
        ref = (id or name).strip()
        key = self._resolve(ref)
        if not key:
            raise ValueError("cocktail.get: no such cocktail.")
        alias = self._alias_of(key, ref)
        card = {"type": "cocktail:recipe", "id": alias,
                "name": alias.split(":")[-1].replace("_", " "),
                "note": (self.cortex.get_chunk(key) or "").strip()}
        card.update(self._link_groups(key, self._GROUPS))
        return card
