"""
Wine Concept Model — a tasting-side DICTIONARY over the ontology's wine entities.

Wine is a reference dictionary (not a formula): the varietals and regions already exist as
`wine:*` atoms (ontology/wine/, loaded universal in the thesaurus tier), each with a tasting
note, a colour, an origin region, and curated cheese pairings. WineConcept reads that live
graph directly — no per-user instances, no bake — via DictionaryConcept's shared mechanism,
exposing four clear READ operators:

  wine.search   name/keyword lookup across the varietal + region entities
  wine.ls       browse by axis — colour (sys:part_of → wine:color:*), origin
                (wine:originated_in → wine:region:*), kind (varietal|region)
  wine.get      a wine's profile — note, colour, origin, and its cheese/dish pairings
  wine.pairs    the tasting-side stance — what a wine pairs with (→ cheese / dish)

Distribution: ontology/wine/ is autoload=false, so these atoms are present in thesaurus /
enterprise (load_all) and absent from the lean seeds tier — matching the policy that new
domain ontology ships thesaurus-only. WineConcept itself is series-independent.
"""
import logging
from typing import Any, Dict

from lib.akasha.concepts.dictionary import DictionaryConcept

logger = logging.getLogger("Harmonia.Concept.Wine")


class WineConcept(DictionaryConcept):
    """Tasting-side dictionary over `wine:varietal:*` / `wine:region:*` with cheese pairing."""

    CONCEPT_PREFIX = "wine"
    CONCEPT_LABEL  = ("wine dictionary — varietals & regions, multi-axis browse "
                      "(colour / origin) + cheese pairing")
    NOUN   = "wine"
    ID_KEY = "wine_id"
    AXES   = ()

    NS           = "wine"
    ENTITY_KINDS = ("varietal", "region")
    AXIS_SPEC    = {
        "color":  ("wine:color:{v}",  "sys:part_of"),
        "region": ("wine:region:{v}", "wine:originated_in"),
    }
    PAIR_RELS    = ("pairing:regional_pairing", "pairing:accord",
                    "pairing:sweetness_with_saltiness", "pairing:contraste")
    PAIR_TARGET  = ""            # a wine pairs with cheese AND dish; no default narrowing

    CONCEPT_METHODS = {
        "search": {"op": "op_search", "action": "read", "cli": "wine.search", "args": ["q"],
                   "desc": "Search wines by name/keyword: wine search <q> [limit=]"},
        "ls":     {"op": "op_ls", "action": "read", "cli": "wine.ls", "args": [],
                   "desc": ("Browse wines by axis: wine ls [color=red] [region=piedmont] "
                            "[kind=varietal|region]")},
        "get":    {"op": "op_get", "action": "read", "cli": "wine.get", "args": ["id"],
                   "desc": ("Wine profile — note, colour, origin, cheese pairings: "
                            "wine get id=wine:varietal:nebbiolo")},
        "pairs":  {"op": "op_pairs", "action": "read", "cli": "wine.pairs", "args": ["id"],
                   "desc": ("What a wine pairs with (→ cheese / dish): "
                            "wine pairs id=wine:varietal:nebbiolo [target=cheese]")},
    }

    def op_search(self, q: str = "", name: str = "", limit: Any = "",
                  offset: Any = 0, cursor: Any = "") -> Dict[str, Any]:
        """[wine.search] Find wines whose name or tasting note contains every query token,
        across the varietal + region entities. READ-level; paginated (default 20, max 100)."""
        return self._dict_search(q or name, limit, offset, cursor)

    def op_ls(self, color: str = "", region: str = "", kind: str = "",
              limit: Any = "", offset: Any = 0, cursor: Any = "") -> Dict[str, Any]:
        """[wine.ls] Browse wines by axis — colour (`red/white/rose/orange`), origin `region`,
        and/or `kind` (varietal|region); axes intersect, read straight from the graph.
        READ-level; paginated (default 20, max 100)."""
        return self._dict_ls({"color": color, "region": region, "kind": kind},
                             limit, offset, cursor)

    def op_get(self, id: str = "", name: str = "") -> Dict[str, Any]:
        """[wine.get] A wine's full profile — tasting note, colour, origin, and its curated
        cheese/dish pairings (the tasting-side payload). READ-level."""
        return self._dict_get(id or name)

    def op_pairs(self, id: str = "", name: str = "", target: str = "") -> Dict[str, Any]:
        """[wine.pairs] The tasting-side stance — what a wine pairs with, following the curated
        `pairing:*` edges. Defaults to every paired atom (cheese + dish), grouped by namespace;
        `target=cheese` narrows it. Ranked by pairing strength. READ-level."""
        return self._dict_pairs(id or name, target)
