# Akasha ontology — allergen free-from view (definition, not materialised).
# free_from:X --allergen:excludes--> allergen:Y defines the view; the member
# list is COMPUTED (scripts/allergen_free_from.py) as the food set minus the
# foods carrying the excluded allergen(s) — not stored as ~4k complement links.
# Also completes fish-derived seafood products for allergen:fish. Base pack.

# ── fish-derived products → allergen:fish ──
ln ingred:seafood:surimi allergen:fish bio:allergen
ln ingred:seafood:kamaboko allergen:fish bio:allergen
ln ingred:seafood:chikuwa allergen:fish bio:allergen
ln ingred:seafood:fish_ball allergen:fish bio:allergen
ln ingred:seafood:imitation_crab allergen:fish bio:allergen
ln ingred:seafood:katsuobushi allergen:fish bio:allergen
ln ingred:seafood:fish_liver allergen:fish bio:allergen
ln ingred:seafood:roe allergen:fish bio:allergen
ln ingred:seafood:ikura allergen:fish bio:allergen
ln ingred:seafood:tobiko allergen:fish bio:allergen
ln ingred:seafood:mentaiko allergen:fish bio:allergen
ln ingred:seafood:bottarga allergen:fish bio:allergen

def "free_from" "Free-from views: foods free of a given allergen (computed complement)."
def "free_from:gluten" "Foods free of gluten (wheat_gluten)."
ln free_from:gluten free_from thesaurus:related
ln free_from:gluten allergen:wheat_gluten allergen:excludes
def "free_from:dairy" "Foods free of dairy (milk)."
ln free_from:dairy free_from thesaurus:related
ln free_from:dairy allergen:milk allergen:excludes
def "free_from:egg" "Foods free of egg (egg)."
ln free_from:egg free_from thesaurus:related
ln free_from:egg allergen:egg allergen:excludes
def "free_from:soy" "Foods free of soy (soy)."
ln free_from:soy free_from thesaurus:related
ln free_from:soy allergen:soy allergen:excludes
def "free_from:fish" "Foods free of fish (fish)."
ln free_from:fish free_from thesaurus:related
ln free_from:fish allergen:fish allergen:excludes
def "free_from:peanut" "Foods free of peanut (peanut)."
ln free_from:peanut free_from thesaurus:related
ln free_from:peanut allergen:peanut allergen:excludes
def "free_from:tree_nut" "Foods free of tree_nut (tree_nut)."
ln free_from:tree_nut free_from thesaurus:related
ln free_from:tree_nut allergen:tree_nut allergen:excludes
def "free_from:nut" "Foods free of nut (tree_nut/peanut)."
ln free_from:nut free_from thesaurus:related
ln free_from:nut allergen:tree_nut allergen:excludes
ln free_from:nut allergen:peanut allergen:excludes
def "free_from:shellfish" "Foods free of shellfish (crustacean/mollusc)."
ln free_from:shellfish free_from thesaurus:related
ln free_from:shellfish allergen:crustacean allergen:excludes
ln free_from:shellfish allergen:mollusc allergen:excludes
def "free_from:sesame" "Foods free of sesame (sesame)."
ln free_from:sesame free_from thesaurus:related
ln free_from:sesame allergen:sesame allergen:excludes
def "free_from:celery" "Foods free of celery (celery)."
ln free_from:celery free_from thesaurus:related
ln free_from:celery allergen:celery allergen:excludes
def "free_from:mustard" "Foods free of mustard (mustard)."
ln free_from:mustard free_from thesaurus:related
ln free_from:mustard allergen:mustard allergen:excludes
