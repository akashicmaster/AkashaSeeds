"""
Brewery Concept Model — a DICTIONARY over the Open Brewery DB catalogue (drinks_c, C-tier).

The `drinks_c` pack (thesaurus tier) imports the world's breweries from Open Brewery DB (MIT):
~11,000 `brewery:<slug>` atoms, each described with its type, city, region and country, and

  brewery:<slug> --sys:is_a--> brewery:type:<type>     (brewpub / micro / large / contract / …)
  set.add brewery:in:<country>  id=brewery:<slug>       (country as a membership set, not a link)

BreweryConcept reads that live graph via DictionaryConcept and exposes three READ operators:

  brewery.search   name/keyword lookup across the breweries
  brewery.ls       browse by axis — type (a typed link) and country (a set)
  brewery.get      a brewery's profile — its type and its description (city/region/country + site)

This is the first dictionary whose country axis is a SET rather than a typed link, so it exercises
DictionaryConcept's SET_AXIS support. Distribution is thesaurus/enterprise only (drinks_c is
autoload=false); BreweryConcept itself is series-independent.
"""
import logging
from typing import Any, Dict

from lib.akasha.concepts.dictionary import DictionaryConcept

logger = logging.getLogger("Harmonia.Concept.Brewery")


class BreweryConcept(DictionaryConcept):
    """Dictionary over `brewery:*` (Open Brewery DB) — browse by type and country."""

    CONCEPT_PREFIX = "brewery"
    CONCEPT_LABEL  = "brewery dictionary — the world's breweries by type and country (Open Brewery DB)"
    NOUN   = "brewery"
    ID_KEY = "brewery_id"
    AXES   = ()

    NS             = "brewery"
    ENTITY_KINDS   = ()
    ENTITY_EXCLUDE = frozenset({"brewery:brewery"})     # the namespace hub, not a brewery
    AXIS_SPEC = {
        # the ls= parameter is `type` (see op_ls); the axis/profile field is `brewery_type`
        # so it never collides with the result envelope's `type` key.
        "brewery_type": ("brewery:type:{v}", "sys:is_a"),
        "country":      ("brewery:in:{v}",   DictionaryConcept.SET_AXIS),
    }

    CONCEPT_METHODS = {
        "search": {"op": "op_search", "action": "read", "cli": "brewery.search", "args": ["q"],
                   "desc": "Search breweries by name/keyword: brewery search <q> [limit=]"},
        "ls":     {"op": "op_ls", "action": "read", "cli": "brewery.ls", "args": [],
                   "desc": ("Browse breweries by axis: brewery ls [type=micro] "
                            "[country=germany]")},
        "get":    {"op": "op_get", "action": "read", "cli": "brewery.get", "args": ["id"],
                   "desc": ("Brewery profile — type, description (city/region/country + site): "
                            "brewery get id=brewery:<slug>")},
    }

    def op_search(self, q: str = "", name: str = "", limit: Any = "",
                  offset: Any = 0, cursor: Any = "") -> Dict[str, Any]:
        """[brewery.search] Find breweries whose name or description contains every query token.
        READ-level; paginated (default 20, max 100)."""
        return self._dict_search(q or name, limit, offset, cursor)

    def op_ls(self, type: str = "", country: str = "", limit: Any = "",
              offset: Any = 0, cursor: Any = "") -> Dict[str, Any]:
        """[brewery.ls] Browse breweries by axis — `type` (micro/brewpub/large/contract/…, a
        typed link) and/or `country` (a membership set); axes intersect. READ-level; paginated
        (default 20, max 100)."""
        return self._dict_ls({"brewery_type": type, "country": country},
                             limit, offset, cursor)

    def op_get(self, id: str = "", name: str = "") -> Dict[str, Any]:
        """[brewery.get] A brewery's profile — its type and its description (city / region /
        country and website, as imported). READ-level."""
        return self._dict_get(id or name)
