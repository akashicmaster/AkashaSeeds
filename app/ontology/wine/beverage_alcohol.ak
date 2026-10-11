# Akasha ontology (wine pack, A-tier) — alcoholic beverages: the drinker's map.
# Fermented → distilled → fortified/liqueur, bridged to production science
# (foodsci:fermentation_science, chemeng:distillation) and to tasting:/pairing:.

def "beverage:alcohol" "Alcoholic drinks and their appreciation (酒)."
def "beverage:fermented" "Made by fermentation alone — wine, beer, sake (醸造酒)."
def "beverage:distilled" "Fermented then distilled to raise strength — whisky, spirits (蒸留酒)."
def "beverage:fortified" "Fermented drink strengthened/flavoured with spirit — liqueur, vermouth (混成酒)."
ln beverage:fermented beverage:alcohol thesaurus:related
ln beverage:distilled beverage:alcohol thesaurus:related
ln beverage:fortified beverage:alcohol thesaurus:related
ln beverage:fermented foodsci:fermentation_science thesaurus:related
ln beverage:distilled chemeng:distillation thesaurus:related

