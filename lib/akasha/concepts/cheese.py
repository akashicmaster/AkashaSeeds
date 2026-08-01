"""
Cheese Concept Model — a DICTIONARY over the ontology's cheese entities, from the pairing side.

Cheese mirrors wine: the entities already exist as `cheese:*` atoms (ontology/wine/, loaded
universal in the thesaurus tier), each with a note, a milk type, an origin country, a texture
family, and the curated wine pairings (the same `pairing:*` edges wine uses, seen from the
cheese side). CheeseConcept reads that live graph via DictionaryConcept's shared mechanism and
exposes four clear READ operators:

  cheese.search   name/keyword lookup across the cheese entities
  cheese.ls       browse by axis — milk (cheese:made_from → cheese:milk:*), texture
                  (sys:part_of → cheese:type:*), country (cheese:origin_country → geo:country:*)
  cheese.get      a cheese's profile — note, milk, texture, country, and its wine pairings
  cheese.pairs    the standpoint the app wants — what WINE to serve with a cheese

The stance is the inverse of wine's: `cheese.pairs` defaults to `target=wine`, following the
wine↔cheese pairing edges from the cheese side (incoming). Distribution is thesaurus-only
(ontology/wine/ is autoload=false); CheeseConcept itself is series-independent.
"""
import logging
from typing import Any, Dict

from lib.akasha.concepts.dictionary import DictionaryConcept

logger = logging.getLogger("Harmonia.Concept.Cheese")


class CheeseConcept(DictionaryConcept):
    """Dictionary over `cheese:*` — browse by milk/texture/country, and pair to wine.

    ⚠️ Cheese/wine data lives in the `wine` ontology pack, which is tier-B (opt-in on the
    seeds tier). If cheese.ls/search/pairs come back empty, enable it once with
    `onto.pack.enable wine` (thesaurus/server tiers autoload it via load_all)."""

    CONCEPT_PREFIX = "cheese"
    CONCEPT_LABEL  = ("cheese dictionary — world cheeses, multi-axis browse "
                      "(milk / texture / country) + wine pairing")
    NOUN   = "cheese"
    ID_KEY = "cheese_id"
    AXES   = ()

    NS           = "cheese"
    ENTITY_KINDS = ()                          # cheeses are flat `cheese:<slug>`
    AXIS_SPEC    = {
        "milk":    ("cheese:milk:{v}", "cheese:made_from"),
        "texture": ("cheese:type:{v}", "sys:part_of"),   # ns is cheese:type:*, the axis is texture
        "country": ("geo:country:{v}", "cheese:origin_country"),
    }
    PAIR_RELS    = ("pairing:regional_pairing", "pairing:accord",
                    "pairing:sweetness_with_saltiness", "pairing:contraste")
    PAIR_TARGET  = "wine"        # the standpoint: what wine to serve with a cheese

    CONCEPT_METHODS = {
        "search": {"op": "op_search", "action": "read", "cli": "cheese.search", "args": ["q"],
                   "desc": "Search cheeses by name/keyword: cheese search <q> [limit=]"},
        "ls":     {"op": "op_ls", "action": "read", "cli": "cheese.ls", "args": [],
                   "desc": ("Browse cheeses by axis: cheese ls [milk=sheep] [texture=blue] "
                            "[country=france]")},
        "get":    {"op": "op_get", "action": "read", "cli": "cheese.get", "args": ["id"],
                   "desc": ("Cheese profile — note, milk, texture, country, wine pairings: "
                            "cheese get id=cheese:roquefort")},
        "pairs":  {"op": "op_pairs", "action": "read", "cli": "cheese.pairs", "args": ["id"],
                   "desc": ("What wine to serve with a cheese: "
                            "cheese pairs id=cheese:roquefort")},
    }

    def op_search(self, q: str = "", name: str = "", limit: Any = "",
                  offset: Any = 0, cursor: Any = "") -> Dict[str, Any]:
        """[cheese.search] Find cheeses whose name or note contains every query token.
        READ-level; paginated (default 20, max 100)."""
        return self._dict_search(q or name, limit, offset, cursor)

    def op_ls(self, milk: str = "", texture: str = "", country: str = "",
              limit: Any = "", offset: Any = 0, cursor: Any = "") -> Dict[str, Any]:
        """[cheese.ls] Browse cheeses by axis — `milk` (cow/goat/sheep/mixed/buffalo),
        `texture` (hard/blue/fresh/soft_ripened/washed_rind/…), `country`; axes intersect,
        read straight from the graph. READ-level; paginated (default 20, max 100)."""
        return self._dict_ls({"milk": milk, "texture": texture, "country": country},
                             limit, offset, cursor)

    def op_get(self, id: str = "", name: str = "") -> Dict[str, Any]:
        """[cheese.get] A cheese's full profile — note, milk, texture, country, and the wines
        it pairs with. READ-level."""
        return self._dict_get(id or name)

    def op_pairs(self, id: str = "", name: str = "", target: str = "") -> Dict[str, Any]:
        """[cheese.pairs] The standpoint the app wants — what WINE to serve with a cheese,
        following the curated `pairing:*` edges from the cheese side. Defaults to `target=wine`;
        pass another namespace to widen. Ranked by pairing strength. READ-level."""
        return self._dict_pairs(id or name, target)
