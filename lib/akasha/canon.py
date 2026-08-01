"""
Canonical upper ontology — Product · Component · Method · Producer (THE LAW).

See docs/for-llm/product-component-ontology.md. Every "made thing" domain in Akasha is organised
on ONE universal shape so local per-pack rules never accumulate:

  • a PRODUCT (成果物) is the deliverable — `meal` (food), and the beverages under `drink`
        (cocktail, wine, spirit). Every product entry `sys:is_a <domain>`; `set <domain>:all` is
        the COMPLETE dictionary (the SUPERSET). A product may roll up into a super-product
        (cocktail/wine/spirit `sys:is_a drink`; members also join `drink:all`).
  • a COMPONENT (構成要素) is what products are made from — `ingredient` (`ingred:*`, `food:*`),
        and, for a cocktail, its spirits / liqueurs / mixers. product `sys:made_from` component.
  • a METHOD (製法) is how a product is made — `recipe` (its own atom, bound `sys:method_of`
        a meal). A cocktail instead carries its mixing method INLINE, so cocktails are simply
        marked as method-carrying (`drink:with_recipe`) rather than owning a separate atom.
  • a PRODUCER (生産者) is who makes a product — distilleries, breweries. product `sys:made_by`
        producer. A producer is NOT a drink (a distillery is not drunk); keeping it a distinct
        role is what stops producers polluting `drink:all`.

The direction is fixed: the product dictionary is the SUPERSET; the method layer is a SUBSET of
it (recipe ⊆ meal:all; if a recipe's product entry is missing it is MINTED first), never the
reverse. The DUAL ROLE is explicit and allowed: a spirit is a drink PRODUCT (drunk neat) AND a
cocktail COMPONENT (a `made_from` target) — an atom can hold more than one role.

This module is DATA — `lib/akasha/ontology_normalize.py` derives the canonical links/sets from it
at every ingestion. Adding a domain is ONE entry here + the super-concept defs in
ontology/base1/canon_upper.ak; no concept/loader code changes.
"""

# ── universal relations (namespaced → stored verbatim by the loader) ─────────────
IS_A      = "sys:is_a"
MADE_FROM = "sys:made_from"     # product → component
METHOD_OF = "sys:method_of"     # method  → product
MADE_BY   = "sys:made_by"       # product → producer

# ── universal role super-concepts ────────────────────────────────────────────────
ROLE_PRODUCT   = "role:product"
ROLE_COMPONENT = "role:component"
ROLE_METHOD    = "role:method"
ROLE_PRODUCER  = "role:producer"

# ── the domain registry (the whole law, as data) ─────────────────────────────────
# Per domain super-concept:
#   role        one of the ROLE_* above.
#   member_ns   tuple of (alias-prefix, colon-depth) pairs — the entity atoms of this domain
#               (a prefix may be deep, e.g. ("whiskey:brand", 2), to select only the products
#               and leave the producers / other kinds out).
#   all_set     this domain's own superset collection.
#   parent      (optional) a super-product this domain rolls up into (sys:is_a) …
#   rollup_set  (optional) … and whose superset its members also join (e.g. drink:all).
#   method_marker (optional) a set every member joins because it carries an INLINE method
#               (cocktails → drink:with_recipe).
#   method_of / product_ns / subset_set  (METHOD domains only) the product domain a method binds
#               to, the namespace to mint the product into, and the "has-method" subset set.
DOMAINS = {
    # ── food ──
    "meal":       {"role": ROLE_PRODUCT,   "member_ns": (("dish", 1),),   "all_set": "meal:all"},
    # `ingredient` is the UNIVERSAL component super-concept — food ingredients (`ingred:*`) AND the
    # drink components a cocktail is made from: cocktail ingredients (`ing:*`), liqueurs
    # (`liqueur:*`), mixers (`beverage:*`) and base spirits (`spirit:*`). All carry role:component.
    "ingredient": {"role": ROLE_COMPONENT,
                   "member_ns": (("ingred", 2), ("ing", 1), ("liqueur", 1),
                                 ("beverage", 1), ("spirit", 1)),
                   "all_set": "ingredient:all"},
    "recipe":     {"role": ROLE_METHOD,    "member_ns": (("recipe", 1),), "all_set": "recipe:all",
                   "method_of": "meal", "product_ns": "dish", "subset_set": "meal:with_recipe"},
    # ── drink (an umbrella product; its categories roll up into it) ──
    "drink":      {"role": ROLE_PRODUCT,   "member_ns": (), "all_set": "drink:all"},
    "cocktail":   {"role": ROLE_PRODUCT,   "member_ns": (("cocktail", 1),), "all_set": "cocktail:all",
                   "parent": "drink", "rollup_set": "drink:all",
                   "method_marker": "drink:with_recipe"},   # a cocktail carries its mixing method
    "wine":       {"role": ROLE_PRODUCT,   "member_ns": (("wine:varietal", 2),), "all_set": "wine:all",
                   "parent": "drink", "rollup_set": "drink:all"},
    "spirit":     {"role": ROLE_PRODUCT,
                   "member_ns": (("whiskey:brand", 2), ("rum:brand", 2), ("tequila:brand", 2)),
                   "all_set": "spirit:all", "parent": "drink", "rollup_set": "drink:all"},
    # ── producers (NOT drinks) ──
    "producer":   {"role": ROLE_PRODUCER,
                   "member_ns": (("brewery", 1), ("whiskey:distillery", 2),
                                 ("rum:distillery", 2), ("tequila:distillery", 2)),
                   "all_set": "producer:all"},
}

# Aliases (at a domain's member depth) that are the domain HUB, not an entity — excluded.
HUB_EXCLUDE = frozenset({"brewery:brewery"})

# Namespaces whose atoms are components (valid `sys:made_from` targets) — informational.
COMPONENT_NS = ("ingred", "food", "ing", "liqueur", "beverage", "spirit")

# Namespaces whose outgoing material links canonicalize to `sys:made_from`.
PRODUCT_NS = ("dish", "cocktail", "recipe")

# Per-pack material relations → the canonical `sys:made_from`. A value lists the target
# namespaces that qualify ("*" = any). `thesaurus:related` is generic, so it only counts as
# "made from" when it points at a component; the cocktail rels are already material by intent.
MATERIAL_RELS = {
    "thesaurus:related": ("ingred", "food"),
    "cocktail:base":     ("*",),
    "cocktail:uses":     ("*",),
}

# Per-pack producer relations → the canonical `sys:made_by` (product → producer).
PRODUCER_RELS = {
    "whiskey:made_by": ("*",),
    "rum:made_by":     ("*",),
    "tequila:made_by": ("*",),
}
