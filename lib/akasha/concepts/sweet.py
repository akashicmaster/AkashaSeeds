"""
Sweet Concept Model — a DICTIONARY over confectionery / お菓子 (製菓): desserts, cakes, cookies,
pastries, chocolate, pudding, ice cream, candy, tarts … (the `sweets_bread_c` pack, Wikidata).

Same shape as small plates: the sweets live in the SHARED `dish:` namespace (already meals in the
canonical layer), singled out by the `sweet:all` umbrella set — each item `sys:is_a` one or more
sub-types (`dish:cake` / `dish:cookie` / … `sys:is_a dish:sweet`), with a per-type membership set
(`sweet:<type>`), a P495 country (`dish:from:<country>`), a P2012 cuisine and P186 ingredient
links. One of the DishFamilyConcept families (dishfamily.py — the shared mechanism).

  sweet.search   name/keyword lookup across the sweets
  sweet.ls       browse by axis — type (cake/cookie/pastry/chocolate/…), country, cuisine
  sweet.get      a sweet's profile — its type(s), cuisines, ingredients

Distribution is thesaurus/enterprise only (sweets_bread_c is autoload=false, a C-tier food pack).
"""
import logging

from lib.akasha.concepts.dishfamily import DishFamilyConcept
from lib.akasha.concepts.dictionary import DictionaryConcept

logger = logging.getLogger("Harmonia.Concept.Sweet")


class SweetConcept(DishFamilyConcept):
    """Dictionary over confectionery / お菓子 — browse by type (cake / cookie / pastry / …),
    country of origin, and cuisine."""

    CONCEPT_PREFIX = "sweet"
    CONCEPT_LABEL  = ("confectionery dictionary (お菓子 / 製菓) — cakes / cookies / pastries / "
                      "chocolate / puddings / candy by type, country and cuisine")
    NOUN   = "sweet"
    ID_KEY = "sweet_id"
    AXES   = ()

    UMBRELLA   = "dish:sweet"
    ENTITY_SET = "sweet:all"
    ENTITY_EXCLUDE = frozenset({"dish:sweet"})
    AXIS_SPEC = {
        "style":   ("sweet:{v}",     DictionaryConcept.SET_AXIS),
        "country": ("dish:from:{v}", DictionaryConcept.SET_AXIS),
        "cuisine": ("cuisine:{v}",   "thesaurus:related"),
    }

    CONCEPT_METHODS = {
        "search": {"op": "op_search", "action": "read", "cli": "sweet.search", "args": ["q"],
                   "desc": "Search sweets by name/keyword: sweet search <q> [limit=]"},
        "ls":     {"op": "op_ls", "action": "read", "cli": "sweet.ls", "args": [],
                   "desc": ("Browse sweets by axis: sweet ls "
                            "[type=cake|cookie|pastry|chocolate|pudding|ice_cream|candy|tart|…] "
                            "[country=france] [cuisine=french]")},
        "get":    {"op": "op_get", "action": "read", "cli": "sweet.get", "args": ["id"],
                   "desc": ("Sweet profile — type(s), cuisines, ingredients: "
                            "sweet get id=dish:<slug>")},
    }
