# Cacao & chocolate — the drink and the food, from bean to bar (A-tier).
# Mesoamerican origin; bridged to foodstud:columbian_exchange, foodsci:
# fermentation, cuisine:mexican, and the beverage/ingredient layers.

def "cacao:cacao" "Theobroma cacao — the bean behind chocolate and cocoa (カカオ)."
ln cacao:cacao cuisine:mexican thesaurus:related
ln cacao:cacao foodstud:columbian_exchange thesaurus:related

def "cacao:cacao_bean" "The seed of the cacao pod, fermented and dried."
ln cacao:cacao_bean cacao:cacao thesaurus:related
def "cacao:cacao_fermentation" "Fermenting the beans in their pulp — where chocolate flavour is born."
ln cacao:cacao_fermentation cacao:cacao thesaurus:related
ln cacao:cacao_fermentation foodsci:fermentation_science thesaurus:related
def "cacao:cocoa" "Ground, defatted cacao — the base of cocoa powder and drinks (ココア)."
ln cacao:cocoa cacao:cacao thesaurus:related
def "cacao:cocoa_butter" "The fat of the cacao bean, giving chocolate its melt."
ln cacao:cocoa_butter cacao:cacao thesaurus:related
def "cacao:cacao_nibs" "Crushed roasted cacao beans."
ln cacao:cacao_nibs cacao:cacao thesaurus:related
def "cacao:conching" "Long kneading that smooths chocolate's texture."
ln cacao:conching cacao:cacao thesaurus:related
def "cacao:couverture" "High-cocoa-butter chocolate for coating and tempering."
ln cacao:couverture cacao:cacao thesaurus:related
ln cacao:couverture verb:cook:temper thesaurus:related
def "cacao:cacao_percentage" "The share of cacao solids — higher = more intense, less sweet."
ln cacao:cacao_percentage cacao:cacao thesaurus:related
def "cacao:single_origin_chocolate" "Chocolate from one region's beans, terroir-expressive."
ln cacao:single_origin_chocolate cacao:cacao thesaurus:related
ln cacao:single_origin_chocolate foodstud:terroir thesaurus:related
# ── chocolate as food ──
def "chocolate:dark_chocolate" "High-cacao, low-sugar chocolate (ダークチョコ)."
ln chocolate:dark_chocolate cacao:cacao chocolate:made_from
def "chocolate:milk_chocolate" "Chocolate with added milk — sweeter, milder."
ln chocolate:milk_chocolate cacao:cacao chocolate:made_from
def "chocolate:white_chocolate" "Cocoa butter, sugar and milk, no cocoa solids."
ln chocolate:white_chocolate cacao:cacao chocolate:made_from
def "chocolate:cocoa_powder" "Dried defatted cacao for baking and drinks."
ln chocolate:cocoa_powder cacao:cacao chocolate:made_from
def "chocolate:ganache" "Chocolate-and-cream emulsion for truffles and fillings."
ln chocolate:ganache cacao:cacao chocolate:made_from
def "chocolate:praline" "Nut-and-chocolate confection."
ln chocolate:praline cacao:cacao chocolate:made_from
def "chocolate:chocolate_bar" "A moulded bar of chocolate."
ln chocolate:chocolate_bar cacao:cacao chocolate:made_from
ln chocolate:dark_chocolate dish:chocolate_cake thesaurus:related
ln chocolate:ganache verb:cook:emulsify thesaurus:related

# ── cacao beverages ──
def "beverage:hot_cocoa" "Sweet cocoa-and-milk drink ( = hot_chocolate)."
ln beverage:hot_cocoa cacao:cacao beverage:made_from
ln beverage:hot_cocoa beverage:cat:dairy_drink beverage:kind
def "beverage:mocha" "Espresso with chocolate and steamed milk (カフェモカ)."
ln beverage:mocha cacao:cacao beverage:made_from
ln beverage:mocha beverage:cat:dairy_drink beverage:kind
def "beverage:drinking_chocolate" "Rich melted-chocolate drink."
ln beverage:drinking_chocolate cacao:cacao beverage:made_from
ln beverage:drinking_chocolate beverage:cat:dairy_drink beverage:kind
def "beverage:xocolatl" "The ancient Aztec bitter-spiced cacao drink (ショコラトル)."
ln beverage:xocolatl cacao:cacao beverage:made_from
ln beverage:xocolatl beverage:cat:dairy_drink beverage:kind
ln beverage:mocha coffee:coffee thesaurus:related
ln beverage:xocolatl cuisine:mexican thesaurus:related
ln beverage:xocolatl foodstud:food_symbolism thesaurus:related
