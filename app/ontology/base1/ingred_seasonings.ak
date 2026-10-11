# Akasha ontology — seasonings: herbs, spices, condiments (expanded)
# New concepts with flavour (taste/smell/colour) links + classification axes
# herb_type (soft/woody) / spice_part / condiment_type. Base pack.

def "herb_type:soft" "Soft (tender-leaf) herbs, used mostly fresh."
def "herb_type:woody" "Woody (hardy) herbs that stand up to cooking."
def "spice_part:seed" "Seed spices."
def "spice_part:bark" "Bark spices."
def "spice_part:rhizome" "Rhizome/root spices."
def "spice_part:flower_bud" "Flower or bud spices."
def "spice_part:fruit" "Dried-fruit/berry spices."
def "spice_part:aril" "Aril/nut spices."
def "spice_part:resin" "Resin/gum spices."
def "spice_part:processed" "Ground/processed spice powders."
def "condiment_type:sauce" "Sauces."
def "condiment_type:oil" "Culinary oils."
def "condiment_type:sweetener" "Sweeteners."
def "condiment_type:seasoning" "Dry seasonings."
def "condiment_type:vinegar" "Vinegars."
def "condiment_type:paste" "Pastes."
def "condiment_type:dairy_fat" "Dairy fats."

# ── new herbs ──
def "ingred:herb:parsley" "A bright, grassy soft herb used fresh as garnish and in sauces."
al ingred:herb:parsley parsley
ln ingred:herb:parsley dna:smell:fragrant calc:associated_with
def "ingred:herb:sage" "A woody herb with a savoury, slightly bitter, camphorous flavour."
al ingred:herb:sage sage
ln ingred:herb:sage dna:smell:fragrant calc:associated_with
ln ingred:herb:sage dna:taste:bitter calc:associated_with
def "ingred:herb:chives" "A delicate allium herb with a mild oniony bite."
al ingred:herb:chives chives
ln ingred:herb:chives dna:smell:pungent calc:associated_with
ln ingred:herb:chives dna:taste:umami calc:associated_with
def "ingred:herb:tarragon" "A soft herb with a delicate anise-like aroma."
al ingred:herb:tarragon tarragon
ln ingred:herb:tarragon dna:smell:fragrant calc:associated_with
def "ingred:herb:marjoram" "A sweet, mild woody herb related to oregano."
al ingred:herb:marjoram marjoram
ln ingred:herb:marjoram dna:smell:fragrant calc:associated_with
def "ingred:herb:bay_leaf" "An aromatic woody leaf used to perfume slow-cooked dishes."
al ingred:herb:bay_leaf bay_leaf
ln ingred:herb:bay_leaf dna:smell:fragrant calc:associated_with
def "ingred:herb:chervil" "A delicate soft herb with a faint anise-parsley flavour."
al ingred:herb:chervil chervil
ln ingred:herb:chervil dna:smell:fragrant calc:associated_with
def "ingred:herb:savory" "A peppery woody herb used with beans and meats."
al ingred:herb:savory savory
ln ingred:herb:savory dna:smell:fragrant calc:associated_with
def "ingred:herb:sorrel" "A soft leafy herb with a sharp, lemony, sour taste."
al ingred:herb:sorrel sorrel
ln ingred:herb:sorrel dna:taste:sour calc:associated_with
def "ingred:herb:shiso" "A fragrant Japanese soft herb with minty-basil notes."
al ingred:herb:shiso shiso
ln ingred:herb:shiso dna:smell:fragrant calc:associated_with

# ── new spices ──
def "ingred:spice:paprika" "Ground dried sweet red peppers; mild, earthy, colouring."
al ingred:spice:paprika paprika
ln ingred:spice:paprika dna:color:red calc:associated_with
def "ingred:spice:cayenne" "Ground hot red chilli; sharp, pungent heat."
al ingred:spice:cayenne cayenne
ln ingred:spice:cayenne dna:taste:hot calc:associated_with
ln ingred:spice:cayenne dna:color:red calc:associated_with
def "ingred:spice:chili_powder" "A blend of ground chillies and spices; warm, hot, earthy."
al ingred:spice:chili_powder chili_powder
ln ingred:spice:chili_powder dna:taste:hot calc:associated_with
ln ingred:spice:chili_powder dna:color:red calc:associated_with
def "ingred:spice:ginger" "A pungent, warming rhizome; fresh or dried."
al ingred:spice:ginger ginger
ln ingred:spice:ginger dna:taste:hot calc:associated_with
ln ingred:spice:ginger dna:smell:fragrant calc:associated_with
def "ingred:spice:galangal" "An aromatic rhizome, sharper and more citrusy than ginger."
al ingred:spice:galangal galangal
ln ingred:spice:galangal dna:taste:hot calc:associated_with
ln ingred:spice:galangal dna:smell:fragrant calc:associated_with
def "ingred:spice:allspice" "A dried berry tasting of clove, cinnamon and nutmeg."
al ingred:spice:allspice allspice
ln ingred:spice:allspice dna:smell:fragrant calc:associated_with
def "ingred:spice:fennel_seed" "Sweet, anise-scented seeds."
al ingred:spice:fennel_seed fennel_seed
ln ingred:spice:fennel_seed dna:taste:sweet calc:associated_with
ln ingred:spice:fennel_seed dna:smell:fragrant calc:associated_with
def "ingred:spice:caraway" "Earthy, faintly bitter aromatic seeds."
al ingred:spice:caraway caraway
ln ingred:spice:caraway dna:smell:fragrant calc:associated_with
ln ingred:spice:caraway dna:taste:bitter calc:associated_with
def "ingred:spice:sumac" "Tangy, deep-red ground berries with a lemony tartness."
al ingred:spice:sumac sumac
ln ingred:spice:sumac dna:taste:sour calc:associated_with
ln ingred:spice:sumac dna:color:red calc:associated_with
def "ingred:spice:mace" "The lacy aril around nutmeg; warm and delicate."
al ingred:spice:mace mace
ln ingred:spice:mace dna:smell:fragrant calc:associated_with
def "ingred:spice:white_pepper" "Milder, earthier peppercorns with the husk removed."
al ingred:spice:white_pepper white_pepper
ln ingred:spice:white_pepper dna:taste:hot calc:associated_with
ln ingred:spice:white_pepper dna:smell:pungent calc:associated_with
def "ingred:spice:sichuan_pepper" "Citrusy husks that create a tingling, numbing sensation."
al ingred:spice:sichuan_pepper sichuan_pepper
ln ingred:spice:sichuan_pepper dna:smell:fragrant calc:associated_with
ln ingred:spice:sichuan_pepper dna:taste:hot calc:associated_with
def "ingred:spice:juniper" "Piney, resinous berries used in game and gin."
al ingred:spice:juniper juniper
ln ingred:spice:juniper dna:smell:fragrant calc:associated_with
ln ingred:spice:juniper dna:taste:bitter calc:associated_with
def "ingred:spice:anise_seed" "Sweet, liquorice-scented seeds."
al ingred:spice:anise_seed anise_seed
ln ingred:spice:anise_seed dna:taste:sweet calc:associated_with
ln ingred:spice:anise_seed dna:smell:fragrant calc:associated_with
def "ingred:spice:poppy_seed" "Tiny nutty seeds used in baking and fillings."
al ingred:spice:poppy_seed poppy_seed
ln ingred:spice:poppy_seed dna:smell:fragrant calc:associated_with
def "ingred:spice:long_pepper" "A hotter, sweeter, more complex relative of black pepper."
al ingred:spice:long_pepper long_pepper
ln ingred:spice:long_pepper dna:taste:hot calc:associated_with
ln ingred:spice:long_pepper dna:smell:pungent calc:associated_with
def "ingred:spice:garlic_powder" "Dried ground garlic; savoury and pungent."
al ingred:spice:garlic_powder garlic_powder
ln ingred:spice:garlic_powder dna:smell:pungent calc:associated_with
ln ingred:spice:garlic_powder dna:taste:umami calc:associated_with
def "ingred:spice:onion_powder" "Dried ground onion; sweet-savoury."
al ingred:spice:onion_powder onion_powder
ln ingred:spice:onion_powder dna:smell:pungent calc:associated_with

# ── new condiments ──
def "ingred:condiment:oyster_sauce" "A thick, savoury-sweet sauce of oyster extract."
al ingred:condiment:oyster_sauce oyster_sauce
ln ingred:condiment:oyster_sauce dna:taste:umami calc:associated_with
ln ingred:condiment:oyster_sauce dna:taste:salty calc:associated_with
def "ingred:condiment:hoisin_sauce" "A sweet, salty, umami Chinese soybean sauce."
al ingred:condiment:hoisin_sauce hoisin_sauce
ln ingred:condiment:hoisin_sauce dna:taste:sweet calc:associated_with
ln ingred:condiment:hoisin_sauce dna:taste:umami calc:associated_with
def "ingred:condiment:sriracha" "A hot, tangy, garlicky chilli sauce."
al ingred:condiment:sriracha sriracha
ln ingred:condiment:sriracha dna:taste:hot calc:associated_with
ln ingred:condiment:sriracha dna:taste:sour calc:associated_with
def "ingred:condiment:hot_sauce" "A pungent condiment of chillies and vinegar."
al ingred:condiment:hot_sauce hot_sauce
ln ingred:condiment:hot_sauce dna:taste:hot calc:associated_with
ln ingred:condiment:hot_sauce dna:taste:sour calc:associated_with
def "ingred:condiment:tabasco" "A sharp, vinegary fermented chilli sauce."
al ingred:condiment:tabasco tabasco
ln ingred:condiment:tabasco dna:taste:hot calc:associated_with
ln ingred:condiment:tabasco dna:taste:sour calc:associated_with
def "ingred:condiment:tahini" "A paste of ground sesame; nutty and faintly bitter."
al ingred:condiment:tahini tahini
ln ingred:condiment:tahini dna:taste:bitter calc:associated_with
def "ingred:condiment:ponzu" "A citrus-soy sauce; tart and savoury."
al ingred:condiment:ponzu ponzu
ln ingred:condiment:ponzu dna:taste:sour calc:associated_with
ln ingred:condiment:ponzu dna:taste:umami calc:associated_with
def "ingred:condiment:teriyaki_sauce" "A glossy sweet-salty Japanese glaze."
al ingred:condiment:teriyaki_sauce teriyaki_sauce
ln ingred:condiment:teriyaki_sauce dna:taste:sweet calc:associated_with
ln ingred:condiment:teriyaki_sauce dna:taste:umami calc:associated_with
def "ingred:condiment:bbq_sauce" "A sweet, smoky, tangy sauce for grilled meats."
al ingred:condiment:bbq_sauce bbq_sauce
ln ingred:condiment:bbq_sauce dna:taste:sweet calc:associated_with
ln ingred:condiment:bbq_sauce dna:taste:umami calc:associated_with
def "ingred:condiment:chili_oil" "Oil infused with dried chillies; hot and aromatic."
al ingred:condiment:chili_oil chili_oil
ln ingred:condiment:chili_oil dna:taste:hot calc:associated_with
def "ingred:condiment:tomato_paste" "Concentrated tomato; deeply umami and lightly sweet."
al ingred:condiment:tomato_paste tomato_paste
ln ingred:condiment:tomato_paste dna:taste:umami calc:associated_with
ln ingred:condiment:tomato_paste dna:taste:sweet calc:associated_with
def "ingred:condiment:harissa" "A North African hot chilli-spice paste."
al ingred:condiment:harissa harissa
ln ingred:condiment:harissa dna:taste:hot calc:associated_with
def "ingred:condiment:pesto" "A herb, nut, cheese and oil sauce."
al ingred:condiment:pesto pesto
ln ingred:condiment:pesto dna:smell:fragrant calc:associated_with
def "ingred:condiment:salsa" "A fresh sauce of tomato, chilli and lime."
al ingred:condiment:salsa salsa
ln ingred:condiment:salsa dna:taste:sour calc:associated_with
ln ingred:condiment:salsa dna:taste:hot calc:associated_with
def "ingred:condiment:horseradish" "A pungent root condiment with sinus-clearing heat."
al ingred:condiment:horseradish horseradish
ln ingred:condiment:horseradish dna:taste:hot calc:associated_with
ln ingred:condiment:horseradish dna:smell:pungent calc:associated_with
def "ingred:condiment:wasabi" "A pungent green Japanese condiment; sharp nasal heat."
al ingred:condiment:wasabi wasabi
ln ingred:condiment:wasabi dna:taste:hot calc:associated_with
ln ingred:condiment:wasabi dna:smell:pungent calc:associated_with
def "ingred:condiment:balsamic_vinegar" "A dark, syrupy, sweet-sour aged vinegar."
al ingred:condiment:balsamic_vinegar balsamic_vinegar
ln ingred:condiment:balsamic_vinegar dna:taste:sour calc:associated_with
ln ingred:condiment:balsamic_vinegar dna:taste:sweet calc:associated_with
def "ingred:condiment:rice_vinegar" "A mild, mellow vinegar from fermented rice."
al ingred:condiment:rice_vinegar rice_vinegar
ln ingred:condiment:rice_vinegar dna:taste:sour calc:associated_with
def "ingred:condiment:ghee" "Clarified butter; rich and nutty."
al ingred:condiment:ghee ghee
def "ingred:condiment:sour_cream" "A tangy cultured cream."
al ingred:condiment:sour_cream sour_cream
ln ingred:condiment:sour_cream dna:taste:sour calc:associated_with

# ── herb → herb_type ──
ln ingred:herb:basil herb_type:soft bio:herb_type
ln ingred:herb:chervil herb_type:soft bio:herb_type
ln ingred:herb:chives herb_type:soft bio:herb_type
ln ingred:herb:cilantro herb_type:soft bio:herb_type
ln ingred:herb:curry_leaf herb_type:soft bio:herb_type
ln ingred:herb:dill herb_type:soft bio:herb_type
ln ingred:herb:kaffir_lime_leaf herb_type:soft bio:herb_type
ln ingred:herb:lemongrass herb_type:soft bio:herb_type
ln ingred:herb:mint herb_type:soft bio:herb_type
ln ingred:herb:parsley herb_type:soft bio:herb_type
ln ingred:herb:shiso herb_type:soft bio:herb_type
ln ingred:herb:sorrel herb_type:soft bio:herb_type
ln ingred:herb:tarragon herb_type:soft bio:herb_type
ln ingred:herb:bay_leaf herb_type:woody bio:herb_type
ln ingred:herb:marjoram herb_type:woody bio:herb_type
ln ingred:herb:oregano herb_type:woody bio:herb_type
ln ingred:herb:rosemary herb_type:woody bio:herb_type
ln ingred:herb:sage herb_type:woody bio:herb_type
ln ingred:herb:savory herb_type:woody bio:herb_type
ln ingred:herb:thyme herb_type:woody bio:herb_type

# ── spice → spice_part ──
ln ingred:spice:ajwain spice_part:seed bio:plant_part
ln ingred:spice:anise_seed spice_part:seed bio:plant_part
ln ingred:spice:caraway spice_part:seed bio:plant_part
ln ingred:spice:cardamom spice_part:seed bio:plant_part
ln ingred:spice:coriander_seed spice_part:seed bio:plant_part
ln ingred:spice:cumin spice_part:seed bio:plant_part
ln ingred:spice:fennel_seed spice_part:seed bio:plant_part
ln ingred:spice:fenugreek spice_part:seed bio:plant_part
ln ingred:spice:mustard_seed spice_part:seed bio:plant_part
ln ingred:spice:nigella_seed spice_part:seed bio:plant_part
ln ingred:spice:poppy_seed spice_part:seed bio:plant_part
ln ingred:spice:cinnamon spice_part:bark bio:plant_part
ln ingred:spice:galangal spice_part:rhizome bio:plant_part
ln ingred:spice:ginger spice_part:rhizome bio:plant_part
ln ingred:spice:turmeric spice_part:rhizome bio:plant_part
ln ingred:spice:clove spice_part:flower_bud bio:plant_part
ln ingred:spice:saffron spice_part:flower_bud bio:plant_part
ln ingred:spice:allspice spice_part:fruit bio:plant_part
ln ingred:spice:amchur spice_part:fruit bio:plant_part
ln ingred:spice:black_cardamom spice_part:fruit bio:plant_part
ln ingred:spice:black_pepper spice_part:fruit bio:plant_part
ln ingred:spice:cayenne spice_part:fruit bio:plant_part
ln ingred:spice:chili_powder spice_part:fruit bio:plant_part
ln ingred:spice:juniper spice_part:fruit bio:plant_part
ln ingred:spice:long_pepper spice_part:fruit bio:plant_part
ln ingred:spice:paprika spice_part:fruit bio:plant_part
ln ingred:spice:sichuan_pepper spice_part:fruit bio:plant_part
ln ingred:spice:star_anise spice_part:fruit bio:plant_part
ln ingred:spice:sumac spice_part:fruit bio:plant_part
ln ingred:spice:vanilla spice_part:fruit bio:plant_part
ln ingred:spice:white_pepper spice_part:fruit bio:plant_part
ln ingred:spice:mace spice_part:aril bio:plant_part
ln ingred:spice:nutmeg spice_part:aril bio:plant_part
ln ingred:spice:asafoetida spice_part:resin bio:plant_part
ln ingred:spice:garlic_powder spice_part:processed bio:plant_part
ln ingred:spice:onion_powder spice_part:processed bio:plant_part

# ── condiment → condiment_type ──
ln ingred:condiment:bbq_sauce condiment_type:sauce culinary:condiment_type
ln ingred:condiment:fish_sauce condiment_type:sauce culinary:condiment_type
ln ingred:condiment:gochujang condiment_type:sauce culinary:condiment_type
ln ingred:condiment:harissa condiment_type:sauce culinary:condiment_type
ln ingred:condiment:hoisin_sauce condiment_type:sauce culinary:condiment_type
ln ingred:condiment:hot_sauce condiment_type:sauce culinary:condiment_type
ln ingred:condiment:ketchup condiment_type:sauce culinary:condiment_type
ln ingred:condiment:mayonnaise condiment_type:sauce culinary:condiment_type
ln ingred:condiment:mustard condiment_type:sauce culinary:condiment_type
ln ingred:condiment:oyster_sauce condiment_type:sauce culinary:condiment_type
ln ingred:condiment:pesto condiment_type:sauce culinary:condiment_type
ln ingred:condiment:ponzu condiment_type:sauce culinary:condiment_type
ln ingred:condiment:salsa condiment_type:sauce culinary:condiment_type
ln ingred:condiment:soy_sauce condiment_type:sauce culinary:condiment_type
ln ingred:condiment:sriracha condiment_type:sauce culinary:condiment_type
ln ingred:condiment:tabasco condiment_type:sauce culinary:condiment_type
ln ingred:condiment:teriyaki_sauce condiment_type:sauce culinary:condiment_type
ln ingred:condiment:worcestershire_sauce condiment_type:sauce culinary:condiment_type
ln ingred:condiment:chili_oil condiment_type:oil culinary:condiment_type
ln ingred:condiment:olive_oil condiment_type:oil culinary:condiment_type
ln ingred:condiment:sesame_oil condiment_type:oil culinary:condiment_type
ln ingred:condiment:honey condiment_type:sweetener culinary:condiment_type
ln ingred:condiment:maple_syrup condiment_type:sweetener culinary:condiment_type
ln ingred:condiment:mirin condiment_type:sweetener culinary:condiment_type
ln ingred:condiment:sugar condiment_type:sweetener culinary:condiment_type
ln ingred:condiment:salt condiment_type:seasoning culinary:condiment_type
ln ingred:condiment:balsamic_vinegar condiment_type:vinegar culinary:condiment_type
ln ingred:condiment:rice_vinegar condiment_type:vinegar culinary:condiment_type
ln ingred:condiment:vinegar condiment_type:vinegar culinary:condiment_type
ln ingred:condiment:horseradish condiment_type:paste culinary:condiment_type
ln ingred:condiment:miso condiment_type:paste culinary:condiment_type
ln ingred:condiment:tahini condiment_type:paste culinary:condiment_type
ln ingred:condiment:tomato_paste condiment_type:paste culinary:condiment_type
ln ingred:condiment:wasabi condiment_type:paste culinary:condiment_type
ln ingred:condiment:butter condiment_type:dairy_fat culinary:condiment_type
ln ingred:condiment:ghee condiment_type:dairy_fat culinary:condiment_type
ln ingred:condiment:sour_cream condiment_type:dairy_fat culinary:condiment_type

