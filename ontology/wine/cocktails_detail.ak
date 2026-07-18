# Cocktail detail — glassware and taste profile (A-tier).

def "glassware:glass" "A drinking glass chosen to suit the drink (グラス)."
def "glassware:martini_glass" "Stemmed conical glass for up cocktails."
ln glassware:martini_glass glassware:glass thesaurus:related
def "glassware:rocks_glass" "Short tumbler for spirits over ice (old-fashioned glass)."
ln glassware:rocks_glass glassware:glass thesaurus:related
def "glassware:highball_glass" "Tall glass for long mixed drinks."
ln glassware:highball_glass glassware:glass thesaurus:related
def "glassware:coupe" "Shallow stemmed glass for shaken/up drinks."
ln glassware:coupe glassware:glass thesaurus:related
def "glassware:collins_glass" "Very tall narrow glass."
ln glassware:collins_glass glassware:glass thesaurus:related
def "glassware:wine_glass" "Stemmed bowl for wine and spritzes."
ln glassware:wine_glass glassware:glass thesaurus:related
def "glassware:flute" "Tall narrow stem for sparkling drinks."
ln glassware:flute glassware:glass thesaurus:related
def "glassware:hurricane_glass" "Curvy tall glass for tropical drinks."
ln glassware:hurricane_glass glassware:glass thesaurus:related
def "glassware:copper_mug" "Chilled copper mug for the Moscow Mule."
ln glassware:copper_mug glassware:glass thesaurus:related
def "glassware:shot_glass" "Small glass for a single measure."
ln glassware:shot_glass glassware:glass thesaurus:related

def "taste:profile" "The dominant taste character of a drink."
def "taste:dry" "A low in sugar, crisp."
ln taste:dry taste:profile thesaurus:related
def "taste:sweet" "A noticeably sugary."
ln taste:sweet taste:profile thesaurus:related
def "taste:sour" "A tart, citrus-driven."
ln taste:sour taste:profile thesaurus:related
def "taste:bitter" "A bitter-forward (amaro, Campari)."
ln taste:bitter taste:profile thesaurus:related
def "taste:spirit_forward" "A strong, spirit-dominant."
ln taste:spirit_forward taste:profile thesaurus:related
def "taste:refreshing" "A light and thirst-quenching."
ln taste:refreshing taste:profile thesaurus:related
def "taste:tropical" "A fruity, exotic."
ln taste:tropical taste:profile thesaurus:related

# ── glass & taste per cocktail ──
ln cocktail:martini glassware:martini_glass cocktail:served_in
ln cocktail:martini taste:dry cocktail:tastes
ln cocktail:negroni glassware:rocks_glass cocktail:served_in
ln cocktail:negroni taste:bitter cocktail:tastes
ln cocktail:old_fashioned glassware:rocks_glass cocktail:served_in
ln cocktail:old_fashioned taste:spirit_forward cocktail:tastes
ln cocktail:margarita glassware:coupe cocktail:served_in
ln cocktail:margarita taste:sour cocktail:tastes
ln cocktail:mojito glassware:highball_glass cocktail:served_in
ln cocktail:mojito taste:refreshing cocktail:tastes
ln cocktail:manhattan glassware:coupe cocktail:served_in
ln cocktail:manhattan taste:spirit_forward cocktail:tastes
ln cocktail:daiquiri glassware:coupe cocktail:served_in
ln cocktail:daiquiri taste:sour cocktail:tastes
ln cocktail:cosmopolitan glassware:martini_glass cocktail:served_in
ln cocktail:cosmopolitan taste:sour cocktail:tastes
ln cocktail:gin_and_tonic glassware:highball_glass cocktail:served_in
ln cocktail:gin_and_tonic taste:refreshing cocktail:tastes
ln cocktail:whiskey_sour glassware:rocks_glass cocktail:served_in
ln cocktail:whiskey_sour taste:sour cocktail:tastes
ln cocktail:bloody_mary glassware:highball_glass cocktail:served_in
ln cocktail:bloody_mary taste:spirit_forward cocktail:tastes
ln cocktail:pina_colada glassware:hurricane_glass cocktail:served_in
ln cocktail:pina_colada taste:tropical cocktail:tastes
ln cocktail:moscow_mule glassware:copper_mug cocktail:served_in
ln cocktail:moscow_mule taste:refreshing cocktail:tastes
ln cocktail:aperol_spritz glassware:wine_glass cocktail:served_in
ln cocktail:aperol_spritz taste:bitter cocktail:tastes
ln cocktail:mimosa glassware:flute cocktail:served_in
ln cocktail:mimosa taste:refreshing cocktail:tastes
ln cocktail:mai_tai glassware:hurricane_glass cocktail:served_in
ln cocktail:mai_tai taste:tropical cocktail:tastes
