# Cocktails — the non-alcoholic side (mocktails) + the alcoholic/non split.
# Non-alcoholic cocktails are built like their alcoholic cousins, from juices,
# sodas and syrups. Base for the serving-occasion axis. A-tier.

def "cocktail:alcoholic" "A cocktail containing spirits/liqueurs/wine (アルコールカクテル)."
def "cocktail:non_alcoholic" "A cocktail with no alcohol — a mocktail (ノンアルコールカクテル/モクテル)."
ln cocktail:alcoholic cocktail:cocktail thesaurus:related
ln cocktail:non_alcoholic cocktail:cocktail thesaurus:related
ln cocktail:non_alcoholic beverage:mocktail thesaurus:related

# ── existing cocktails are alcoholic ──
ln cocktail:martini cocktail:alcoholic cocktail:strength
ln cocktail:negroni cocktail:alcoholic cocktail:strength
ln cocktail:old_fashioned cocktail:alcoholic cocktail:strength
ln cocktail:margarita cocktail:alcoholic cocktail:strength
ln cocktail:mojito cocktail:alcoholic cocktail:strength
ln cocktail:manhattan cocktail:alcoholic cocktail:strength
ln cocktail:daiquiri cocktail:alcoholic cocktail:strength
ln cocktail:cosmopolitan cocktail:alcoholic cocktail:strength
ln cocktail:gin_and_tonic cocktail:alcoholic cocktail:strength
ln cocktail:whiskey_sour cocktail:alcoholic cocktail:strength
ln cocktail:bloody_mary cocktail:alcoholic cocktail:strength
ln cocktail:pina_colada cocktail:alcoholic cocktail:strength
ln cocktail:moscow_mule cocktail:alcoholic cocktail:strength
ln cocktail:aperol_spritz cocktail:alcoholic cocktail:strength
ln cocktail:mimosa cocktail:alcoholic cocktail:strength
ln cocktail:mai_tai cocktail:alcoholic cocktail:strength

# ── mocktails (non-alcoholic) ──
def "cocktail:virgin_mojito" "Virgin Mojito — a mocktail."
ln cocktail:virgin_mojito cocktail:non_alcoholic cocktail:strength
ln cocktail:virgin_mojito cocktail:method:muddled cocktail:mixed
ln cocktail:virgin_mojito beverage:soda_water cocktail:base
ln cocktail:virgin_mojito garnish:mint_sprig cocktail:garnished_with
ln cocktail:virgin_mojito glassware:highball_glass cocktail:served_in
ln cocktail:virgin_mojito taste:refreshing cocktail:tastes
def "cocktail:virgin_pina_colada" "Virgin Pina Colada — a mocktail."
ln cocktail:virgin_pina_colada cocktail:non_alcoholic cocktail:strength
ln cocktail:virgin_pina_colada cocktail:method:blended cocktail:mixed
ln cocktail:virgin_pina_colada beverage:orange_juice cocktail:base
ln cocktail:virgin_pina_colada garnish:pineapple_wedge cocktail:garnished_with
ln cocktail:virgin_pina_colada glassware:hurricane_glass cocktail:served_in
ln cocktail:virgin_pina_colada taste:tropical cocktail:tastes
def "cocktail:shirley_temple" "Shirley Temple — a mocktail."
ln cocktail:shirley_temple cocktail:non_alcoholic cocktail:strength
ln cocktail:shirley_temple cocktail:method:built cocktail:mixed
ln cocktail:shirley_temple beverage:ginger_ale cocktail:base
ln cocktail:shirley_temple garnish:cocktail_cherry cocktail:garnished_with
ln cocktail:shirley_temple glassware:highball_glass cocktail:served_in
ln cocktail:shirley_temple taste:sweet cocktail:tastes
def "cocktail:virgin_mary" "Virgin Mary — a mocktail."
ln cocktail:virgin_mary cocktail:non_alcoholic cocktail:strength
ln cocktail:virgin_mary cocktail:method:built cocktail:mixed
ln cocktail:virgin_mary beverage:tomato_juice cocktail:base
ln cocktail:virgin_mary garnish:celery_stalk cocktail:garnished_with
ln cocktail:virgin_mary glassware:highball_glass cocktail:served_in
ln cocktail:virgin_mary taste:spirit_forward cocktail:tastes
def "cocktail:arnold_palmer" "Arnold Palmer — a mocktail."
ln cocktail:arnold_palmer cocktail:non_alcoholic cocktail:strength
ln cocktail:arnold_palmer cocktail:method:built cocktail:mixed
ln cocktail:arnold_palmer beverage:black_tea cocktail:base
ln cocktail:arnold_palmer beverage:lemonade cocktail:base
ln cocktail:arnold_palmer garnish:lemon_wheel cocktail:garnished_with
ln cocktail:arnold_palmer glassware:collins_glass cocktail:served_in
ln cocktail:arnold_palmer taste:refreshing cocktail:tastes
def "cocktail:cucumber_cooler" "Cucumber Cooler — a mocktail."
ln cocktail:cucumber_cooler cocktail:non_alcoholic cocktail:strength
ln cocktail:cucumber_cooler cocktail:method:built cocktail:mixed
ln cocktail:cucumber_cooler beverage:soda_water cocktail:base
ln cocktail:cucumber_cooler garnish:cucumber_slice cocktail:garnished_with
ln cocktail:cucumber_cooler glassware:highball_glass cocktail:served_in
ln cocktail:cucumber_cooler taste:refreshing cocktail:tastes
def "cocktail:fruit_punch" "Fruit Punch — a mocktail."
ln cocktail:fruit_punch cocktail:non_alcoholic cocktail:strength
ln cocktail:fruit_punch cocktail:method:built cocktail:mixed
ln cocktail:fruit_punch beverage:orange_juice cocktail:base
ln cocktail:fruit_punch beverage:apple_juice cocktail:base
ln cocktail:fruit_punch garnish:orange_slice cocktail:garnished_with
ln cocktail:fruit_punch glassware:hurricane_glass cocktail:served_in
ln cocktail:fruit_punch taste:sweet cocktail:tastes
def "cocktail:ginger_fizz" "Ginger Fizz — a mocktail."
ln cocktail:ginger_fizz cocktail:non_alcoholic cocktail:strength
ln cocktail:ginger_fizz cocktail:method:built cocktail:mixed
ln cocktail:ginger_fizz beverage:ginger_ale cocktail:base
ln cocktail:ginger_fizz beverage:sparkling_water cocktail:base
ln cocktail:ginger_fizz garnish:lime_wedge cocktail:garnished_with
ln cocktail:ginger_fizz glassware:highball_glass cocktail:served_in
ln cocktail:ginger_fizz taste:refreshing cocktail:tastes
def "cocktail:berry_lemonade" "Berry Lemonade — a mocktail."
ln cocktail:berry_lemonade cocktail:non_alcoholic cocktail:strength
ln cocktail:berry_lemonade cocktail:method:built cocktail:mixed
ln cocktail:berry_lemonade beverage:lemonade cocktail:base
ln cocktail:berry_lemonade garnish:cocktail_cherry cocktail:garnished_with
ln cocktail:berry_lemonade glassware:collins_glass cocktail:served_in
ln cocktail:berry_lemonade taste:sour cocktail:tastes
def "cocktail:sparkling_grape" "Sparkling Grape — a mocktail."
ln cocktail:sparkling_grape cocktail:non_alcoholic cocktail:strength
ln cocktail:sparkling_grape cocktail:method:built cocktail:mixed
ln cocktail:sparkling_grape beverage:apple_juice cocktail:base
ln cocktail:sparkling_grape beverage:sparkling_water cocktail:base
ln cocktail:sparkling_grape garnish:cocktail_cherry cocktail:garnished_with
ln cocktail:sparkling_grape glassware:flute cocktail:served_in
ln cocktail:sparkling_grape taste:sweet cocktail:tastes
