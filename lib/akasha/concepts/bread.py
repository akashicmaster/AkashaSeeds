"""
Bread Concept Model — a DICTIONARY over breads / パン (製パン): flatbreads, buns/rolls, sweet
bread / viennoiserie, sourdough, rye, quick bread … (the `sweets_bread_c` pack, Wikidata).

Same shape as small plates and sweets: the breads live in the SHARED `dish:` namespace (already
meals in the canonical layer), singled out by the `bread:all` umbrella set — each item `sys:is_a`
one or more sub-types (`dish:flatbread` / `dish:sourdough` / … `sys:is_a dish:bread`), with a
per-type membership set (`bread:<type>`), a P495 country (`dish:from:<country>`), a P2012 cuisine
and P186 ingredient links. One of the DishFamilyConcept families (dishfamily.py — the shared
mechanism).

  bread.search   name/keyword lookup across the breads
  bread.ls       browse by axis — type (flatbread/sourdough/rye/bun/…), country, cuisine
  bread.get      a bread's profile — its type(s), cuisines, ingredients

Distribution is thesaurus/enterprise only (sweets_bread_c is autoload=false, a C-tier food pack).
"""
import logging

from lib.akasha.concepts.dishfamily import DishFamilyConcept
from lib.akasha.concepts.dictionary import DictionaryConcept

logger = logging.getLogger("Harmonia.Concept.Bread")


class BreadConcept(DishFamilyConcept):
    """Dictionary over breads / パン — browse by type (flatbread / sourdough / rye / bun / …),
    country of origin, and cuisine."""

    CONCEPT_PREFIX = "bread"
    CONCEPT_LABEL  = ("bread dictionary (パン / 製パン) — flatbreads / sourdough / rye / buns / "
                      "viennoiserie / quick breads by type, country and cuisine")
    NOUN   = "bread"
    ID_KEY = "bread_id"
    AXES   = ()

    UMBRELLA   = "dish:bread"
    ENTITY_SET = "bread:all"
    ENTITY_EXCLUDE = frozenset({"dish:bread"})
    AXIS_SPEC = {
        "style":   ("bread:{v}",     DictionaryConcept.SET_AXIS),
        "country": ("dish:from:{v}", DictionaryConcept.SET_AXIS),
        "cuisine": ("cuisine:{v}",   "thesaurus:related"),
    }

    CONCEPT_METHODS = {
        "search": {"op": "op_search", "action": "read", "cli": "bread.search", "args": ["q"],
                   "desc": "Search breads by name/keyword: bread search <q> [limit=]"},
        "ls":     {"op": "op_ls", "action": "read", "cli": "bread.ls", "args": [],
                   "desc": ("Browse breads by axis: bread ls "
                            "[type=flatbread|sourdough|rye|bun|sweet_bread|quick_bread|…] "
                            "[country=india] [cuisine=indian]")},
        "get":    {"op": "op_get", "action": "read", "cli": "bread.get", "args": ["id"],
                   "desc": ("Bread profile — type(s), cuisines, ingredients: "
                            "bread get id=dish:<slug>")},
    }
