# Serving occasion — when/where a drink is served.
# Like wine's role at the table, applied across cocktails, wine, tea & coffee.
# A-tier.

def "occasion:occasion" "The scene or moment a drink/dish is served (提供シーン)."
def "occasion:aperitif" "Served before the meal, to whet the appetite (食前)."
ln occasion:aperitif occasion:occasion thesaurus:related
def "occasion:digestif" "Served after the meal, to aid digestion (食後)."
ln occasion:digestif occasion:occasion thesaurus:related
def "occasion:with_meal" "Served during the meal, paired with food (食中)."
ln occasion:with_meal occasion:occasion thesaurus:related
def "occasion:brunch" "Served the late-morning weekend meal."
ln occasion:brunch occasion:occasion thesaurus:related
def "occasion:afternoon" "Served the afternoon break (afternoon tea)."
ln occasion:afternoon occasion:occasion thesaurus:related
def "occasion:nightcap" "Served a last drink before bed (寝酒)."
ln occasion:nightcap occasion:occasion thesaurus:related
def "occasion:celebration" "Served a toast for a special occasion (乾杯)."
ln occasion:celebration occasion:occasion thesaurus:related
def "occasion:party" "Served convivial group drinking."
ln occasion:party occasion:occasion thesaurus:related
def "occasion:everyday" "Served casual, daily drinking."
ln occasion:everyday occasion:occasion thesaurus:related
def "occasion:summer_cooler" "Served a hot-weather refresher."
ln occasion:summer_cooler occasion:occasion thesaurus:related
def "occasion:winter_warmer" "Served a cold-weather warming drink."
ln occasion:winter_warmer occasion:occasion thesaurus:related
def "occasion:ceremonial" "Served a ritual/ceremonial setting."
ln occasion:ceremonial occasion:occasion thesaurus:related
def "occasion:welcome_drink" "Served offered to greet a guest (ウェルカムドリンク)."
ln occasion:welcome_drink occasion:occasion thesaurus:related

ln liqueur:aperitif occasion:aperitif thesaurus:related
ln liqueur:digestif occasion:digestif thesaurus:related

# ── cocktails → occasion ──
ln cocktail:negroni occasion:aperitif occasion:served_at
ln cocktail:aperol_spritz occasion:aperitif occasion:served_at
ln cocktail:martini occasion:aperitif occasion:served_at
ln cocktail:manhattan occasion:nightcap occasion:served_at
ln cocktail:old_fashioned occasion:nightcap occasion:served_at
ln cocktail:mimosa occasion:brunch occasion:served_at
ln cocktail:bloody_mary occasion:brunch occasion:served_at
ln cocktail:mojito occasion:summer_cooler occasion:served_at
ln cocktail:daiquiri occasion:summer_cooler occasion:served_at
ln cocktail:gin_and_tonic occasion:summer_cooler occasion:served_at
ln cocktail:moscow_mule occasion:summer_cooler occasion:served_at
ln cocktail:pina_colada occasion:party occasion:served_at
ln cocktail:mai_tai occasion:party occasion:served_at
ln cocktail:cosmopolitan occasion:party occasion:served_at
ln cocktail:margarita occasion:party occasion:served_at
ln cocktail:whiskey_sour occasion:everyday occasion:served_at
ln cocktail:shirley_temple occasion:party occasion:served_at
ln cocktail:arnold_palmer occasion:summer_cooler occasion:served_at
ln cocktail:virgin_mary occasion:brunch occasion:served_at
ln cocktail:fruit_punch occasion:party occasion:served_at
ln cocktail:sparkling_grape occasion:celebration occasion:served_at
ln cocktail:virgin_mojito occasion:summer_cooler occasion:served_at

# ── wine serving styles → occasion ──
def "wine:style:sparkling_wine" "Fizzy wine — the toast (champagne, cava, prosecco)."
ln wine:style:sparkling_wine occasion:celebration occasion:served_at
def "wine:style:dessert_wine" "Sweet wine to close a meal (Sauternes, port, ice wine)."
ln wine:style:dessert_wine occasion:digestif occasion:served_at
def "wine:style:table_wine" "Everyday still wine served with food."
ln wine:style:table_wine occasion:with_meal occasion:served_at
def "wine:style:aperitif_wine" "Light/fortified wine before the meal (dry sherry, vermouth)."
ln wine:style:aperitif_wine occasion:aperitif occasion:served_at
def "wine:style:mulled_wine" "Spiced warmed wine (グリューワイン)."
ln wine:style:mulled_wine occasion:winter_warmer occasion:served_at
ln wine:style:sparkling_wine occasion:aperitif occasion:served_at

# ── tea & coffee → occasion ──
ln tea:tea_ceremony occasion:ceremonial occasion:served_at
ln tea:matcha_tea occasion:ceremonial occasion:served_at
ln tea:barley_tea occasion:everyday occasion:served_at
ln coffee:espresso_brew occasion:digestif occasion:served_at
ln coffee:coffee occasion:everyday occasion:served_at
def "occasion:afternoon_tea" "Afternoon tea — the British ritual of tea, scones and cakes."
ln occasion:afternoon_tea occasion:afternoon thesaurus:related
ln occasion:afternoon_tea tea:black_tea thesaurus:related
