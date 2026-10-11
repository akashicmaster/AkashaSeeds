# Canonical upper ontology — Product · Component · Method (成果物・構成要素・製法). THE LAW.
# See docs/for-llm/product-component-ontology.md and lib/akasha/canon.py. Loaded in base1
# (tier A → present in every series). These are the only hand-authored canonical atoms; every
# per-entry sys:is_a / sys:made_from / sys:method_of link and every :all / :with_recipe set is
# derived automatically at ontology ingestion by lib/akasha/ontology_normalize.py — never by hand.

# ── universal role super-concepts ──
def "role:product" "product (成果物) — a made deliverable. A domain's complete product dictionary (its :all set) is the SUPERSET; carrying a method or known parts is never a membership condition."
def "role:component" "component (構成要素) — a part that products are made from (via sys:made_from)."
def "role:method" "method (製法) — how a product is made. A method is always bound to a product (sys:method_of); methods are a SUBSET of the product dictionary, never the reverse."
def "role:producer" "producer (生産者) — who makes a product (via sys:made_by). A producer is not itself a product (a distillery is not drunk), so it never enters a product dictionary."

# ── universal relation definitions (Definition Completeness) ──
def "reldef:sys:made_from" "made from — product to component. A product is made from a component; one directed edge, traversable both ways. Replaces the per-pack material rels (thesaurus:related to an ingredient, cocktail:base, cocktail:uses)."
def "reldef:sys:method_of" "method of — method to product. A recipe is the method of a meal. Guarantees recipe is a subset of the meal dictionary: if the product entry is missing it is minted first."
def "reldef:sys:made_by" "made by — product to producer. A drink is made by a distillery / brewery / winery. Replaces the per-pack producer rels (whiskey:made_by, rum:made_by, tequila:made_by)."

# ── namespace definitions ──
def "nsdef:meal" "meal — the food product namespace (dish:*); the complete dish dictionary (set meal:all)."
def "nsdef:recipe" "recipe — the food method namespace (recipe:*); the subset of meals that carry a method (set meal:with_recipe)."
def "nsdef:ingredient" "ingredient — the universal component namespace: food ingredients (ingred:*) and the drink components a cocktail is made from (ing:*, liqueur:*, beverage:*, spirit:* base spirits). All carry role:component."
def "nsdef:producer" "producer — the drinks-producer namespace: distilleries (whiskey/rum/tequila:distillery:*) and breweries (brewery:*); the far side of made_by (set producer:all)."
def "nsdef:drink" "drink — the beverage product umbrella (set drink:all); cocktail / wine / spirit roll up into it."
def "nsdef:cocktail" "cocktail — the drink product namespace (cocktail:*); the complete cocktail dictionary (set cocktail:all). Cocktails carry an inline mixing method (set drink:with_recipe)."

# ── domain super-concepts + their role ──
def "meal" "Meal — the food product super-concept. Every dish is-a meal; set meal:all is the complete dictionary (the superset). Meals that also carry a method are in meal:with_recipe; meals with known parts have sys:made_from edges. Either may be absent without affecting membership."
def "ingredient" "Ingredient — the food component super-concept. Every ingred:* is-a ingredient; products are made from ingredients."
def "recipe" "Recipe — the food method super-concept. Every recipe is-a recipe and is the method_of a meal (its product)."
def "drink" "Drink — the beverage product super-concept. Cocktails, wines and spirits are-a drink; set drink:all is the complete beverage dictionary. Drinks with an inline method are in drink:with_recipe; a drink is made_from its components and made_by its producer."
def "cocktail" "Cocktail — a drink product category. Every cocktail is-a cocktail (and is-a drink); set cocktail:all is the dictionary. A cocktail is made_from its spirits / liqueurs / mixers and carries its mixing method inline."
def "wine" "Wine — a drink product category. Every wine varietal is-a wine (and is-a drink)."
def "spirit" "Spirit — a drink product category. Every bottled spirit is-a spirit (and is-a drink); a spirit is also a cocktail COMPONENT (a made_from target) — the product/component dual role — and is made_by a distillery."
def "producer" "Producer — the drinks-producer super-concept. Distilleries and breweries are-a producer; a producer makes drinks (the incoming made_by) but is not itself a drink."
ln meal role:product sys:is_a
ln ingredient role:component sys:is_a
ln recipe role:method sys:is_a
ln drink role:product sys:is_a
ln producer role:producer sys:is_a
ln cocktail drink sys:is_a
ln wine drink sys:is_a
ln spirit drink sys:is_a
