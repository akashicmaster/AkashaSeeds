# Akasha ontology — oils & fats: new sources + fat classification. Base pack.

def "fat_source:plant" "Plant-derived fat/oil."
def "fat_source:animal" "Animal-derived fat."

def "ingred:condiment:vegetable_oil" "A neutral blended plant cooking oil."
al ingred:condiment:vegetable_oil vegetable_oil
ln ingred:condiment:vegetable_oil condiment_type:oil culinary:condiment_type
ln ingred:condiment:vegetable_oil fat_source:plant bio:fat_source
def "ingred:condiment:canola_oil" "A light, neutral rapeseed oil."
al ingred:condiment:canola_oil canola_oil
ln ingred:condiment:canola_oil condiment_type:oil culinary:condiment_type
ln ingred:condiment:canola_oil fat_source:plant bio:fat_source
def "ingred:condiment:coconut_oil" "A tropical oil solid at room temperature."
al ingred:condiment:coconut_oil coconut_oil
ln ingred:condiment:coconut_oil condiment_type:oil culinary:condiment_type
ln ingred:condiment:coconut_oil fat_source:plant bio:fat_source
def "ingred:condiment:peanut_oil" "A nutty, high-smoke-point groundnut oil."
al ingred:condiment:peanut_oil peanut_oil
ln ingred:condiment:peanut_oil condiment_type:oil culinary:condiment_type
ln ingred:condiment:peanut_oil fat_source:plant bio:fat_source
def "ingred:condiment:sunflower_oil" "A light, neutral seed oil."
al ingred:condiment:sunflower_oil sunflower_oil
ln ingred:condiment:sunflower_oil condiment_type:oil culinary:condiment_type
ln ingred:condiment:sunflower_oil fat_source:plant bio:fat_source
def "ingred:condiment:avocado_oil" "A rich, high-smoke-point fruit oil."
al ingred:condiment:avocado_oil avocado_oil
ln ingred:condiment:avocado_oil condiment_type:oil culinary:condiment_type
ln ingred:condiment:avocado_oil fat_source:plant bio:fat_source
def "ingred:condiment:grapeseed_oil" "A clean, light oil pressed from grape seeds."
al ingred:condiment:grapeseed_oil grapeseed_oil
ln ingred:condiment:grapeseed_oil condiment_type:oil culinary:condiment_type
ln ingred:condiment:grapeseed_oil fat_source:plant bio:fat_source
def "ingred:condiment:lard" "Rendered pork fat."
al ingred:condiment:lard lard
ln ingred:condiment:lard condiment_type:dairy_fat culinary:condiment_type
ln ingred:condiment:lard fat_source:animal bio:fat_source
def "ingred:condiment:tallow" "Rendered beef or mutton fat."
al ingred:condiment:tallow tallow
ln ingred:condiment:tallow condiment_type:dairy_fat culinary:condiment_type
ln ingred:condiment:tallow fat_source:animal bio:fat_source
def "ingred:condiment:coconut_milk" "Rich pressed liquid of coconut flesh."
al ingred:condiment:coconut_milk coconut_milk
ln ingred:condiment:coconut_milk condiment_type:paste culinary:condiment_type
ln ingred:condiment:coconut_milk fat_source:plant bio:fat_source
ln ingred:condiment:olive_oil fat_source:plant bio:fat_source
ln ingred:condiment:sesame_oil fat_source:plant bio:fat_source
ln ingred:condiment:chili_oil fat_source:plant bio:fat_source
ln ingred:condiment:butter fat_source:animal bio:fat_source
ln ingred:condiment:ghee fat_source:animal bio:fat_source
