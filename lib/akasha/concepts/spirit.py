"""
Spirit Concept Model — a DICTIONARY over distilled spirits (drinks_c, Wikidata).

The drinks_c pack imports spirits from Wikidata into per-type namespaces that all share the same
shape — an entity, a `<type>:<type>` hub, an origin-country membership set, and a sparse producer
link:

  whiskey:<form>:<slug>  --sys:is_a--> whiskey:whiskey ; set whiskey:from:<country> ; whiskey:made_by
  rum:<form>:<slug>      (…rum…)                       ; set rum:from:<country>
  tequila:<form>:<slug>  (…tequila…)                   ; set tequila:from:<country>

where <form> is `distillery` (the maker) or `brand` (the labelled spirit).

Because the three namespaces differ ONLY in name, folding them into one `spirit` dictionary with
a `type` axis is the right call — three separate concepts would just triplicate identical
operators. SpiritConcept spans all three namespaces (DictionaryConcept's multi-namespace mode):

  spirit.search   name/keyword lookup across whiskey + rum + tequila
  spirit.ls       browse by axis — type (whiskey|rum|tequila) and country (a membership set)
  spirit.get      a spirit's profile — its type, origin description, and producer(s)

Distribution is thesaurus/enterprise only (drinks_c is autoload=false, tier C). The `spirit:*`
namespace in the wine pack (gin/vodka/… as cocktail bases) is a separate, tiny classification and
is intentionally NOT folded in here — cocktail.base already resolves those.
"""
import logging
from typing import Any, Dict

from lib.akasha.concepts.dictionary import DictionaryConcept

logger = logging.getLogger("Harmonia.Concept.Spirit")


class SpiritConcept(DictionaryConcept):
    """Unified dictionary over whiskey / rum / tequila — browse by type and origin country."""

    CONCEPT_PREFIX = "spirit"
    CONCEPT_LABEL  = "spirit dictionary — whiskey / rum / tequila by type and origin country"
    NOUN   = "spirit"
    ID_KEY = "spirit_id"
    AXES   = ()

    NS             = ("whiskey", "rum", "tequila")       # the three sibling namespaces
    ENTITY_KINDS   = ()
    ENTITY_DEPTH   = 2                                   # entities are <type>:<form>:<slug>
    ENTITY_EXCLUDE = frozenset({"whiskey:whiskey", "rum:rum", "tequila:tequila"})
    KIND_FIELD     = "spirit_type"                       # the namespace names the spirit type
    AXIS_SPEC = {
        "country": (["whiskey:from:{v}", "rum:from:{v}", "tequila:from:{v}"],
                    DictionaryConcept.SET_AXIS),
    }
    _GROUPS = (
        ("producer", ["whiskey:made_by", "rum:made_by", "tequila:made_by"], True),
    )

    CONCEPT_METHODS = {
        "search": {"op": "op_search", "action": "read", "cli": "spirit.search", "args": ["q"],
                   "desc": "Search spirits by name/keyword: spirit search <q> [limit=]"},
        "ls":     {"op": "op_ls", "action": "read", "cli": "spirit.ls", "args": [],
                   "desc": ("Browse spirits by axis: spirit ls [type=whiskey|rum|tequila] "
                            "[country=scotland]")},
        "get":    {"op": "op_get", "action": "read", "cli": "spirit.get", "args": ["id"],
                   "desc": ("Spirit profile — type, origin, producer(s): "
                            "spirit get id=whiskey:<slug>")},
    }

    def _profile(self, key: str, alias: str) -> Dict[str, Any]:
        """Adds `form` (distillery | brand — the 2nd segment) to the base profile, alongside the
        `spirit_type` (the namespace) the multi-namespace base already fills in."""
        prof = super()._profile(key, alias)
        if alias.count(":") >= 2:
            prof["form"] = alias.split(":")[1]
        return prof

    def op_search(self, q: str = "", name: str = "", limit: Any = "",
                  offset: Any = 0, cursor: Any = "") -> Dict[str, Any]:
        """[spirit.search] Find spirits whose name or description contains every query token,
        across whiskey / rum / tequila. READ-level; paginated (default 20, max 100)."""
        return self._dict_search(q or name, limit, offset, cursor)

    def op_ls(self, type: str = "", country: str = "", limit: Any = "",
              offset: Any = 0, cursor: Any = "") -> Dict[str, Any]:
        """[spirit.ls] Browse spirits by axis — `type` (whiskey/rum/tequila) and/or `country`
        (a membership set); axes intersect. READ-level; paginated (default 20, max 100)."""
        return self._dict_ls({"kind": type, "country": country}, limit, offset, cursor)

    def op_get(self, id: str = "", name: str = "") -> Dict[str, Any]:
        """[spirit.get] A spirit's profile — its type (namespace), origin description, and its
        producer(s) where recorded. READ-level."""
        ref = (id or name).strip()
        key = self._resolve(ref)
        if not key:
            raise ValueError("spirit.get: no such spirit.")
        prof = self._profile(key, self._alias_of(key, ref))
        prof["type"] = "spirit:profile"
        prof.update(self._link_groups(key, self._GROUPS))
        return prof
