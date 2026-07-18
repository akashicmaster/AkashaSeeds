# Cocktails — classic mixed drinks (A-tier).
# Bridged to spirit:/liqueur:/beverage: (bases & mixers) and garnish:.

def "cocktail:cocktail" "A mixed drink of spirits, mixers and garnish (カクテル)."
ln cocktail:cocktail beverage:alcohol thesaurus:related

def "cocktail:method:shaken" "Shaken with ice (for citrus/juice drinks)."
def "cocktail:method:stirred" "Stirred with ice (for spirit-forward drinks)."
def "cocktail:method:built" "Built in the glass over ice."
def "cocktail:method:muddled" "Ingredients crushed to release flavour."
def "cocktail:method:blended" "Blended with ice."

def "cocktail:martini" "Martini."
ln cocktail:martini cocktail:cocktail thesaurus:related
ln cocktail:martini cocktail:method:stirred cocktail:mixed
ln cocktail:martini spirit:gin cocktail:base
ln cocktail:martini garnish:olive cocktail:garnished_with
def "cocktail:negroni" "Negroni."
ln cocktail:negroni cocktail:cocktail thesaurus:related
ln cocktail:negroni cocktail:method:stirred cocktail:mixed
ln cocktail:negroni spirit:gin cocktail:base
ln cocktail:negroni liqueur:campari cocktail:base
ln cocktail:negroni liqueur:vermouth cocktail:base
ln cocktail:negroni garnish:orange_peel cocktail:garnished_with
def "cocktail:old_fashioned" "Old Fashioned."
ln cocktail:old_fashioned cocktail:cocktail thesaurus:related
ln cocktail:old_fashioned cocktail:method:stirred cocktail:mixed
ln cocktail:old_fashioned whiskey:bourbon cocktail:base
ln cocktail:old_fashioned garnish:orange_peel cocktail:garnished_with
def "cocktail:margarita" "Margarita."
ln cocktail:margarita cocktail:cocktail thesaurus:related
ln cocktail:margarita cocktail:method:shaken cocktail:mixed
ln cocktail:margarita spirit:tequila cocktail:base
ln cocktail:margarita liqueur:triple_sec cocktail:base
ln cocktail:margarita garnish:salt_rim cocktail:garnished_with
def "cocktail:mojito" "Mojito."
ln cocktail:mojito cocktail:cocktail thesaurus:related
ln cocktail:mojito cocktail:method:muddled cocktail:mixed
ln cocktail:mojito spirit:rum cocktail:base
ln cocktail:mojito garnish:mint_sprig cocktail:garnished_with
def "cocktail:manhattan" "Manhattan."
ln cocktail:manhattan cocktail:cocktail thesaurus:related
ln cocktail:manhattan cocktail:method:stirred cocktail:mixed
ln cocktail:manhattan whiskey:rye_whiskey cocktail:base
ln cocktail:manhattan liqueur:vermouth cocktail:base
ln cocktail:manhattan garnish:cocktail_cherry cocktail:garnished_with
def "cocktail:daiquiri" "Daiquiri."
ln cocktail:daiquiri cocktail:cocktail thesaurus:related
ln cocktail:daiquiri cocktail:method:shaken cocktail:mixed
ln cocktail:daiquiri spirit:rum cocktail:base
ln cocktail:daiquiri garnish:lime_wedge cocktail:garnished_with
def "cocktail:cosmopolitan" "Cosmopolitan."
ln cocktail:cosmopolitan cocktail:cocktail thesaurus:related
ln cocktail:cosmopolitan cocktail:method:shaken cocktail:mixed
ln cocktail:cosmopolitan spirit:vodka cocktail:base
ln cocktail:cosmopolitan liqueur:triple_sec cocktail:base
ln cocktail:cosmopolitan garnish:orange_peel cocktail:garnished_with
def "cocktail:gin_and_tonic" "Gin And Tonic."
ln cocktail:gin_and_tonic cocktail:cocktail thesaurus:related
ln cocktail:gin_and_tonic cocktail:method:built cocktail:mixed
ln cocktail:gin_and_tonic spirit:gin cocktail:base
ln cocktail:gin_and_tonic beverage:tonic_water cocktail:base
ln cocktail:gin_and_tonic garnish:lime_wedge cocktail:garnished_with
def "cocktail:whiskey_sour" "Whiskey Sour."
ln cocktail:whiskey_sour cocktail:cocktail thesaurus:related
ln cocktail:whiskey_sour cocktail:method:shaken cocktail:mixed
ln cocktail:whiskey_sour whiskey:whiskey cocktail:base
ln cocktail:whiskey_sour garnish:cocktail_cherry cocktail:garnished_with
def "cocktail:bloody_mary" "Bloody Mary."
ln cocktail:bloody_mary cocktail:cocktail thesaurus:related
ln cocktail:bloody_mary cocktail:method:built cocktail:mixed
ln cocktail:bloody_mary spirit:vodka cocktail:base
ln cocktail:bloody_mary beverage:tomato_juice cocktail:base
ln cocktail:bloody_mary garnish:celery_stalk cocktail:garnished_with
def "cocktail:pina_colada" "Pina Colada."
ln cocktail:pina_colada cocktail:cocktail thesaurus:related
ln cocktail:pina_colada cocktail:method:blended cocktail:mixed
ln cocktail:pina_colada spirit:rum cocktail:base
ln cocktail:pina_colada garnish:pineapple_wedge cocktail:garnished_with
def "cocktail:moscow_mule" "Moscow Mule."
ln cocktail:moscow_mule cocktail:cocktail thesaurus:related
ln cocktail:moscow_mule cocktail:method:built cocktail:mixed
ln cocktail:moscow_mule spirit:vodka cocktail:base
ln cocktail:moscow_mule beverage:ginger_ale cocktail:base
ln cocktail:moscow_mule garnish:lime_wedge cocktail:garnished_with
def "cocktail:aperol_spritz" "Aperol Spritz."
ln cocktail:aperol_spritz cocktail:cocktail thesaurus:related
ln cocktail:aperol_spritz cocktail:method:built cocktail:mixed
ln cocktail:aperol_spritz liqueur:aperol cocktail:base
ln cocktail:aperol_spritz garnish:orange_slice cocktail:garnished_with
def "cocktail:mimosa" "Mimosa."
ln cocktail:mimosa cocktail:cocktail thesaurus:related
ln cocktail:mimosa cocktail:method:built cocktail:mixed
ln cocktail:mimosa beverage:orange_juice cocktail:base
ln cocktail:mimosa garnish:orange_slice cocktail:garnished_with
def "cocktail:mai_tai" "Mai Tai."
ln cocktail:mai_tai cocktail:cocktail thesaurus:related
ln cocktail:mai_tai cocktail:method:shaken cocktail:mixed
ln cocktail:mai_tai spirit:rum cocktail:base
ln cocktail:mai_tai garnish:mint_sprig cocktail:garnished_with
