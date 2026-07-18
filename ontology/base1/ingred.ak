# Akasha ontology — namespace: ingred
# Everyday ingredients — basic set (35 items).
# Full 226-item set: domain/ingred_core.ak
# atoms: 35

def "ingred:veg:onion" "A bulb vegetable with papery skin, foundational to global cuisines."
ln ingred:veg:onion dna:smell:pungent calc:associated_with
ln ingred:veg:onion sci:cook:maillard_reaction @promotes
ln ingred:veg:onion sci:cook:caramelization @promotes

def "ingred:veg:garlic" "A strongly flavored bulb used universally as a base aromatic."
ln ingred:veg:garlic chem:odor:allicin @contains
ln ingred:veg:garlic dna:smell:pungent calc:associated_with
ln ingred:veg:garlic verb:cook:mince sys:refers_to

def "ingred:veg:potato" "A starchy tuber, foundational to global diets and highly versatile."
ln ingred:veg:potato sci:cook:gelatinization @promotes
ln ingred:veg:potato sci:cook:enzymatic_browning @promotes
ln ingred:veg:potato verb:cook:mash sys:refers_to
ln ingred:veg:potato verb:cook:boil sys:refers_to

def "ingred:veg:tomato" "A red, juicy culinary vegetable, biologically a berry."
ln ingred:veg:tomato chem:pigment:lycopene @contains
ln ingred:veg:tomato dna:taste:umami calc:associated_with
ln ingred:veg:tomato dna:color:red calc:associated_with

def "ingred:veg:carrot" "A sweet, crisp, orange root vegetable."
ln ingred:veg:carrot chem:pigment:carotene @contains
ln ingred:veg:carrot dna:taste:sweet calc:associated_with
ln ingred:veg:carrot dna:color:orange calc:associated_with
ln ingred:veg:carrot verb:cook:peel sys:refers_to

def "ingred:veg:cabbage" "A leafy green, red, or white biennial plant grown as an annual vegetable crop."

def "ingred:veg:spinach" "A leafy green vegetable known for its dark color and iron content."

def "ingred:veg:mushroom" "The fleshy, spore-bearing fruiting body of a fungus, typically the button variety."

def "ingred:veg:chili_pepper" "A spicy capsicum fruit containing capsaicin."
ln ingred:veg:chili_pepper dna:taste:hot calc:associated_with

def "ingred:veg:bell_pepper" "A sweet, non-spicy capsicum fruit."

def "ingred:fruit:apple" "A round fruit with red or green skin. Used fresh, baked, or juiced."
ln ingred:fruit:apple dna:taste:sweet calc:associated_with
ln ingred:fruit:apple dna:color:red calc:associated_with
ln ingred:fruit:apple dna:texture:crisp calc:associated_with
ln ingred:fruit:apple verb:cook:core sys:refers_to

def "ingred:fruit:banana" "A long curved fruit with a yellow skin and soft, sweet flesh."
ln ingred:fruit:banana chem:odor:isoamyl_acetate @contains
ln ingred:fruit:banana dna:taste:sweet calc:associated_with
ln ingred:fruit:banana dna:color:yellow calc:associated_with
ln ingred:fruit:banana dna:texture:soft calc:associated_with

def "ingred:fruit:orange" "A round citrus fruit with sweet and tart juice."
ln ingred:fruit:orange chem:odor:limonene @contains
ln ingred:fruit:orange verb:cook:zest sys:refers_to
ln ingred:fruit:orange dna:color:orange calc:associated_with
ln ingred:fruit:orange dna:taste:sweet calc:associated_with
ln ingred:fruit:orange dna:taste:sour calc:associated_with

def "ingred:fruit:lemon" "A yellow citrus fruit known for its acidic juice and aromatic rind."
ln ingred:fruit:lemon chem:odor:limonene @contains
ln ingred:fruit:lemon dna:taste:sour calc:associated_with
ln ingred:fruit:lemon dna:smell:fragrant calc:associated_with
ln ingred:fruit:lemon dna:color:yellow calc:associated_with
ln ingred:fruit:lemon verb:cook:zest sys:refers_to
ln ingred:fruit:lemon verb:cook:press sys:refers_to

def "ingred:fruit:grape" "A small, juicy berry growing in clusters on vines."

def "ingred:grain:rice" "A cereal grain, the most widely consumed staple food for a large part of the world's human population."
ln ingred:grain:rice sci:cook:gelatinization @undergoes
ln ingred:grain:rice verb:cook:steam sys:refers_to
ln ingred:grain:rice verb:cook:boil sys:refers_to
ln ingred:grain:rice dna:texture:soft calc:associated_with

def "ingred:grain:wheat" "A cereal grain grown worldwide, foundational for baking and bread-making."

def "ingred:grain:oats" "A cereal grain prized for its nutritional value and cholesterol-lowering properties."

def "ingred:legume:chickpea" "A versatile, high-protein legume, central to Middle Eastern and Indian cuisines (Garbanzo)."
ln ingred:legume:chickpea verb:cook:soak @requires
ln ingred:legume:chickpea verb:cook:boil sys:refers_to

def "ingred:legume:lentil" "An edible legume shaped like a lens, known for its quick cooking time compared to other beans."
ln ingred:legume:lentil verb:cook:simmer sys:refers_to

def "ingred:meat:chicken" "The most common type of poultry in the world."
ln ingred:meat:chicken dna:taste:umami calc:associated_with
ln ingred:meat:chicken sci:cook:protein_denaturation @undergoes

def "ingred:meat:beef" "Culinary name for meat from cattle."
ln ingred:meat:beef chem:pigment:heme @contains
ln ingred:meat:beef dna:taste:umami calc:associated_with
ln ingred:meat:beef sci:cook:maillard_reaction @promotes
ln ingred:meat:beef sci:cook:protein_denaturation @undergoes

def "ingred:meat:pork" "Culinary name for meat from domestic pigs."
ln ingred:meat:pork dna:taste:umami calc:associated_with

def "ingred:seafood:salmon" "An anadromous fish known for its rich, oily, pink-to-orange flesh."
ln ingred:seafood:salmon dna:color:orange calc:associated_with
ln ingred:seafood:salmon verb:cook:smoke sys:refers_to
ln ingred:seafood:salmon verb:cook:cure sys:refers_to

def "ingred:seafood:tuna" "A large, fast-swimming pelagic fish with dense, dark red meat."
ln ingred:seafood:tuna dna:taste:umami calc:associated_with
ln ingred:seafood:tuna dna:color:red calc:associated_with
ln ingred:seafood:tuna sci:cook:protein_denaturation @undergoes

def "ingred:condiment:salt" "A mineral composed primarily of sodium chloride, the most fundamental flavor enhancer."
ln ingred:condiment:salt dna:taste:salty calc:associated_with

def "ingred:condiment:sugar" "A sweet crystalline substance obtained from various plants."
ln ingred:condiment:sugar dna:taste:sweet calc:associated_with
ln ingred:condiment:sugar sci:cook:caramelization @undergoes

def "ingred:condiment:olive_oil" "A liquid fat obtained from olives, central to Mediterranean cuisine."
ln ingred:condiment:olive_oil chem:fatty_acid:oleic_acid @rich_in

def "ingred:condiment:butter" "A dairy product made from the fat and protein components of churned cream."
ln ingred:condiment:butter chem:fatty_acid:saturated_fatty_acid @rich_in
ln ingred:condiment:butter chem:odor:diacetyl @contains

def "ingred:condiment:soy_sauce" "A liquid condiment of Chinese origin, traditionally made from a fermented paste of soybeans."
ln ingred:condiment:soy_sauce dna:taste:salty calc:associated_with
ln ingred:condiment:soy_sauce dna:taste:umami calc:associated_with

def "ingred:spice:black_pepper" "The dried, unripe fruit of the piperaceae family, the most ubiquitous spice."

def "ingred:spice:cinnamon" "The inner bark of a tropical tree, offering sweet and warm notes."
ln ingred:spice:cinnamon chem:odor:cinnamaldehyde @contains
ln ingred:spice:cinnamon dna:taste:sweet calc:associated_with

def "ingred:spice:cumin" "Seeds with an earthy, warm, and slightly nutty flavor, a pillar of Indian curries (Jeera)."
ln ingred:spice:cumin verb:cook:fry @requires

def "ingred:herb:basil" "A sweet, fragrant herb central to Italian cuisine."
ln ingred:herb:basil dna:color:green calc:associated_with

def "ingred:herb:mint" "A refreshing, cooling herb used globally in both sweet and savory dishes."
ln ingred:herb:mint chem:odor:menthol @contains
