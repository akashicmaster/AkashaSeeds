# Akasha ontology — nuts & seeds (new category). Base pack.
# ingred:nut:* / ingred:seed:*, with flavour, nut_type, and fat_source:plant
# (nuts/seeds are oil-rich). Note: peanut stays under legume (a groundnut).

def "nut_type:tree_nut" "Tree nut — hard-shelled fruit/seed of a tree."
def "nut_type:seed" "Culinary seed used whole or pressed for oil."

# ── nuts ──
def "ingred:nut:almond" "A sweet, versatile tree nut."
al ingred:nut:almond almond
ln ingred:nut:almond dna:taste:sweet calc:associated_with
ln ingred:nut:almond nut_type:tree_nut bio:nut_type
ln ingred:nut:almond fat_source:plant bio:fat_source
def "ingred:nut:walnut" "A rich, faintly bitter tree nut."
al ingred:nut:walnut walnut
ln ingred:nut:walnut dna:taste:bitter calc:associated_with
ln ingred:nut:walnut nut_type:tree_nut bio:nut_type
ln ingred:nut:walnut fat_source:plant bio:fat_source
def "ingred:nut:pecan" "A sweet, buttery tree nut."
al ingred:nut:pecan pecan
ln ingred:nut:pecan dna:taste:sweet calc:associated_with
ln ingred:nut:pecan nut_type:tree_nut bio:nut_type
ln ingred:nut:pecan fat_source:plant bio:fat_source
def "ingred:nut:cashew" "A creamy, mildly sweet tree nut."
al ingred:nut:cashew cashew
ln ingred:nut:cashew dna:taste:sweet calc:associated_with
ln ingred:nut:cashew nut_type:tree_nut bio:nut_type
ln ingred:nut:cashew fat_source:plant bio:fat_source
def "ingred:nut:pistachio" "A delicate green tree nut."
al ingred:nut:pistachio pistachio
ln ingred:nut:pistachio dna:taste:sweet calc:associated_with
ln ingred:nut:pistachio dna:color:green calc:associated_with
ln ingred:nut:pistachio nut_type:tree_nut bio:nut_type
ln ingred:nut:pistachio fat_source:plant bio:fat_source
def "ingred:nut:hazelnut" "An aromatic, sweet tree nut."
al ingred:nut:hazelnut hazelnut
ln ingred:nut:hazelnut dna:taste:sweet calc:associated_with
ln ingred:nut:hazelnut dna:smell:fragrant calc:associated_with
ln ingred:nut:hazelnut nut_type:tree_nut bio:nut_type
ln ingred:nut:hazelnut fat_source:plant bio:fat_source
def "ingred:nut:macadamia" "A rich, buttery tree nut."
al ingred:nut:macadamia macadamia
ln ingred:nut:macadamia nut_type:tree_nut bio:nut_type
ln ingred:nut:macadamia fat_source:plant bio:fat_source
def "ingred:nut:brazil_nut" "A large, oily tree nut."
al ingred:nut:brazil_nut brazil_nut
ln ingred:nut:brazil_nut nut_type:tree_nut bio:nut_type
ln ingred:nut:brazil_nut fat_source:plant bio:fat_source
def "ingred:nut:pine_nut" "A soft, resinous seed of pine cones."
al ingred:nut:pine_nut pine_nut
ln ingred:nut:pine_nut dna:smell:fragrant calc:associated_with
ln ingred:nut:pine_nut nut_type:tree_nut bio:nut_type
ln ingred:nut:pine_nut fat_source:plant bio:fat_source
def "ingred:nut:chestnut" "A starchy, sweet nut, roasted or boiled."
al ingred:nut:chestnut chestnut
ln ingred:nut:chestnut dna:taste:sweet calc:associated_with
ln ingred:nut:chestnut nut_type:tree_nut bio:nut_type
ln ingred:nut:chestnut fat_source:plant bio:fat_source

# ── seeds ──
def "ingred:seed:sesame" "Tiny nutty seeds; the base of tahini and oils."
al ingred:seed:sesame sesame
ln ingred:seed:sesame dna:smell:fragrant calc:associated_with
ln ingred:seed:sesame nut_type:seed bio:nut_type
ln ingred:seed:sesame fat_source:plant bio:fat_source
def "ingred:seed:sunflower_seed" "Mild, nutty seeds."
al ingred:seed:sunflower_seed sunflower_seed
ln ingred:seed:sunflower_seed nut_type:seed bio:nut_type
ln ingred:seed:sunflower_seed fat_source:plant bio:fat_source
def "ingred:seed:pumpkin_seed" "Green, nutty seeds (pepitas)."
al ingred:seed:pumpkin_seed pumpkin_seed
ln ingred:seed:pumpkin_seed dna:color:green calc:associated_with
ln ingred:seed:pumpkin_seed nut_type:seed bio:nut_type
ln ingred:seed:pumpkin_seed fat_source:plant bio:fat_source
def "ingred:seed:flax" "Nutty omega-rich seeds."
al ingred:seed:flax flax
ln ingred:seed:flax nut_type:seed bio:nut_type
ln ingred:seed:flax fat_source:plant bio:fat_source
def "ingred:seed:chia" "Tiny gelling omega-rich seeds."
al ingred:seed:chia chia
ln ingred:seed:chia nut_type:seed bio:nut_type
ln ingred:seed:chia fat_source:plant bio:fat_source
def "ingred:seed:hemp_seed" "Soft, nutty, protein-rich seeds."
al ingred:seed:hemp_seed hemp_seed
ln ingred:seed:hemp_seed nut_type:seed bio:nut_type
ln ingred:seed:hemp_seed fat_source:plant bio:fat_source

# peanut is a legume (groundnut) but used culinarily as a nut
ln ingred:legume:peanut nut_type:tree_nut thesaurus:related
ln ingred:legume:peanut fat_source:plant bio:fat_source
