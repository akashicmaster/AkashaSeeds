# pantry.ak — canonical vocab for the recipe concept model.
#
# Cooking methods and dietary constraints/allergens the recipe model resolves
# against by alias (method:<slug> / constraint:<slug>). Recipes reference these;
# giving them described atoms here (rather than letting recipe.add auto-stub
# them) makes the vocab real ontology. Recipes are authored in
# curations/recipe_demo.csl. Duplicate-safe: atoms are content-addressed and the
# aliases are first-wins, so reloading is idempotent.

# ── Cooking methods (recipe:by / recipe:step_by resolve to these) ─────────────
def "method:simmer" "Cook gently in liquid just below boiling — tenderises and melds flavour."
al method:simmer simmer
def "method:boil"   "Cook in rapidly bubbling liquid at ~100C."
al method:boil boil
def "method:fry"    "Cook in hot fat over direct heat; browns and crisps."
al method:fry fry
def "method:steam"  "Cook over boiling-water vapour — gentle, retains nutrients and shape."
al method:steam steam
def "method:bake"   "Cook with dry radiant oven heat."
al method:bake bake
def "method:grill"  "Cook over or under fierce direct heat; chars and caramelises."
al method:grill grill
def "method:raw"    "Served uncooked — dressing/curing only."
al method:raw raw

# ── Dietary constraints / allergens (recipe:constraint resolves to these) ─────
# Hard filters: recipe.suggest avoid=<slug> subtracts any recipe carrying these.
def "constraint:peanut"    "Peanut — a major allergen; strict avoidance for peanut allergy."
al constraint:peanut peanut
def "constraint:treenut"   "Tree nuts (almond, walnut, cashew…) — major allergen."
al constraint:treenut treenut
def "constraint:gluten"    "Gluten (wheat/barley/rye) — avoid for coeliac / gluten intolerance."
al constraint:gluten gluten
def "constraint:dairy"     "Dairy / lactose — avoid for lactose intolerance or dairy allergy."
al constraint:dairy dairy
def "constraint:shellfish" "Shellfish (shrimp, crab…) — major allergen."
al constraint:shellfish shellfish
def "constraint:egg"       "Egg — common allergen."
al constraint:egg egg
def "constraint:pork"      "Pork — dietary/religious avoidance (halal, kosher)."
al constraint:pork pork_taboo
def "constraint:alcohol"   "Alcohol — dietary/religious/health avoidance."
al constraint:alcohol alcohol
