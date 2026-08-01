"""
Small-plate Concept Model — a DICTIONARY over the cross-cultural small-plate / finger-food dishes
(drinks_c-sibling `smallplates_c` pack, Wikidata).

The small-plate dishes live in the SHARED `dish:` namespace (already meals in the canonical
layer), singled out by the `smallplate:all` umbrella set — each item `sys:is_a` one or more
cultural families (`dish:tapa` / `dish:pincho` / … `sys:is_a dish:smallplate`), with a per-type
membership set (`smallplate:<type>`), a P495 country (`dish:from:<country>`), a P2012 cuisine and
P186 ingredient links. This is one of the DishFamilyConcept families (see dishfamily.py — the
shared mechanism); the surface below is small-plate's own.

  smallplate.search   name/keyword lookup across the small-plate dishes
  smallplate.ls       browse by axis — type (tapa/pincho/meze/…), country, cuisine
  smallplate.get      a dish's profile — its cultural type(s), cuisines, ingredients

Distribution is thesaurus/enterprise only (smallplates_c is autoload=false, a drinks_c-sibling
C-tier food pack). There are no pairing edges on small plates, so there is no pairs operator.
"""
import logging

from lib.akasha.concepts.dishfamily import DishFamilyConcept
from lib.akasha.concepts.dictionary import DictionaryConcept

logger = logging.getLogger("Harmonia.Concept.Smallplate")


class SmallplateConcept(DishFamilyConcept):
    """Dictionary over the small-plate / finger-food dishes — browse by cultural type, country of
    origin, and cuisine."""

    CONCEPT_PREFIX = "smallplate"
    CONCEPT_LABEL  = ("small-plate dictionary — tapas / pinchos / antipasti / meze / canapés / "
                      "finger food by cultural type, country and cuisine")
    NOUN   = "small plate"
    ID_KEY = "smallplate_id"
    AXES   = ()

    UMBRELLA   = "dish:smallplate"
    ENTITY_SET = "smallplate:all"
    ENTITY_EXCLUDE = frozenset({"dish:smallplate"})
    # `type` (the cultural family) and `country` are membership SETS; `cuisine` is a typed link.
    # The `type` axis is keyed `style` internally — `type` is the result-envelope key, so it can't
    # be an axis name; the ls parameter stays `type`.
    AXIS_SPEC = {
        "style":   ("smallplate:{v}", DictionaryConcept.SET_AXIS),
        "country": ("dish:from:{v}",  DictionaryConcept.SET_AXIS),
        "cuisine": ("cuisine:{v}",    "thesaurus:related"),
    }

    CONCEPT_METHODS = {
        "search": {"op": "op_search", "action": "read", "cli": "smallplate.search", "args": ["q"],
                   "desc": "Search small-plate dishes by name/keyword: smallplate search <q> [limit=]"},
        "ls":     {"op": "op_ls", "action": "read", "cli": "smallplate.ls", "args": [],
                   "desc": ("Browse small plates by axis: smallplate ls "
                            "[type=tapa|pincho|antipasto|meze|finger_food|canape|…] "
                            "[country=spain] [cuisine=italian]")},
        "get":    {"op": "op_get", "action": "read", "cli": "smallplate.get", "args": ["id"],
                   "desc": ("Small-plate profile — cultural type(s), cuisines, ingredients: "
                            "smallplate get id=dish:<slug>")},
    }
