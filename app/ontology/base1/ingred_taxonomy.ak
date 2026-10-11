# Akasha ontology — ingredient taxonomy axes + habitat→ecosystem bridges
# Classification hubs for seafood (habitat), meat (husbandry), fruit (type),
# and vegetables (plant part), each linked from its ingredients, plus habitat
# → resource:ecosystem bridges. Relations: bio:habitat/husbandry/plant_part/
# fruit_type. Base pack (all series).

# ── habitat → ecosystem ──
ln habitat:marine resource:ecosystem:oceans thesaurus:related
ln habitat:freshwater resource:ecosystem:freshwater thesaurus:related
ln habitat:anadromous resource:ecosystem:oceans thesaurus:related
ln habitat:anadromous resource:ecosystem:freshwater thesaurus:related
ln habitat:catadromous resource:ecosystem:oceans thesaurus:related
ln habitat:catadromous resource:ecosystem:freshwater thesaurus:related

# ── meat → husbandry ──
def "husbandry:livestock" "Livestock — domesticated mammals raised for meat (cattle, pigs, sheep, goats)."
def "husbandry:poultry" "Poultry — domesticated birds raised for meat and eggs."
def "husbandry:game" "Game — wild animals hunted for meat (venison, boar, wildfowl)."

ln ingred:meat:bacon husbandry:livestock bio:husbandry
ln ingred:meat:beef husbandry:livestock bio:husbandry
ln ingred:meat:bone_marrow husbandry:livestock bio:husbandry
ln ingred:meat:brisket husbandry:livestock bio:husbandry
ln ingred:meat:chuck husbandry:livestock bio:husbandry
ln ingred:meat:flank husbandry:livestock bio:husbandry
ln ingred:meat:ham husbandry:livestock bio:husbandry
ln ingred:meat:heart husbandry:livestock bio:husbandry
ln ingred:meat:lamb husbandry:livestock bio:husbandry
ln ingred:meat:liver husbandry:livestock bio:husbandry
ln ingred:meat:pork husbandry:livestock bio:husbandry
ln ingred:meat:pork_belly husbandry:livestock bio:husbandry
ln ingred:meat:pork_loin husbandry:livestock bio:husbandry
ln ingred:meat:pork_shoulder husbandry:livestock bio:husbandry
ln ingred:meat:ribeye husbandry:livestock bio:husbandry
ln ingred:meat:shank husbandry:livestock bio:husbandry
ln ingred:meat:sirloin husbandry:livestock bio:husbandry
ln ingred:meat:tenderloin husbandry:livestock bio:husbandry
ln ingred:meat:tripe husbandry:livestock bio:husbandry
ln ingred:meat:breast_meat husbandry:poultry bio:husbandry
ln ingred:meat:chicken husbandry:poultry bio:husbandry
ln ingred:meat:duck husbandry:poultry bio:husbandry
ln ingred:meat:poultry_wing husbandry:poultry bio:husbandry
ln ingred:meat:thigh_meat husbandry:poultry bio:husbandry
ln ingred:meat:venison husbandry:game bio:husbandry

# ── fruit → type ──
def "fruit_type:pome" "Pome fruit — apple/pear family (Rosaceae, core with seeds)."
def "fruit_type:citrus" "Citrus fruit — segmented, acidic, aromatic rind."
def "fruit_type:stone" "Stone fruit (drupe) — single hard pit."
def "fruit_type:berry" "Berry — small, soft, many-seeded fruit."
def "fruit_type:tropical" "Tropical fruit — warm-climate fruit."
def "fruit_type:melon" "Melon — large, watery, rind fruit of the gourd family."

ln ingred:fruit:apple fruit_type:pome bio:fruit_type
ln ingred:fruit:pear fruit_type:pome bio:fruit_type
ln ingred:fruit:grapefruit fruit_type:citrus bio:fruit_type
ln ingred:fruit:lemon fruit_type:citrus bio:fruit_type
ln ingred:fruit:lime fruit_type:citrus bio:fruit_type
ln ingred:fruit:orange fruit_type:citrus bio:fruit_type
ln ingred:fruit:yuzu fruit_type:citrus bio:fruit_type
ln ingred:fruit:apricot fruit_type:stone bio:fruit_type
ln ingred:fruit:cherry fruit_type:stone bio:fruit_type
ln ingred:fruit:mango fruit_type:stone bio:fruit_type
ln ingred:fruit:peach fruit_type:stone bio:fruit_type
ln ingred:fruit:plum fruit_type:stone bio:fruit_type
ln ingred:fruit:blackberry fruit_type:berry bio:fruit_type
ln ingred:fruit:blueberry fruit_type:berry bio:fruit_type
ln ingred:fruit:grape fruit_type:berry bio:fruit_type
ln ingred:fruit:raspberry fruit_type:berry bio:fruit_type
ln ingred:fruit:strawberry fruit_type:berry bio:fruit_type
ln ingred:fruit:banana fruit_type:tropical bio:fruit_type
ln ingred:fruit:coconut fruit_type:tropical bio:fruit_type
ln ingred:fruit:fig fruit_type:tropical bio:fruit_type
ln ingred:fruit:papaya fruit_type:tropical bio:fruit_type
ln ingred:fruit:pineapple fruit_type:tropical bio:fruit_type
ln ingred:fruit:pomegranate fruit_type:tropical bio:fruit_type
ln ingred:fruit:melon fruit_type:melon bio:fruit_type
ln ingred:fruit:watermelon fruit_type:melon bio:fruit_type

# ── vegetable → plant part ──
def "plantpart:root" "Root vegetable — edible root."
def "plantpart:tuber" "Tuber — starchy underground stem."
def "plantpart:bulb" "Bulb — layered underground storage (alliums, fennel)."
def "plantpart:leaf" "Leaf vegetable — edible leaves."
def "plantpart:stem" "Stem vegetable — edible stalk/shoot."
def "plantpart:flower" "Flower vegetable — edible flower head/bud."
def "plantpart:fruit_veg" "Fruit vegetable — botanically a fruit, used as a vegetable."
def "plantpart:fungus" "Fungus — edible mushrooms and truffles."

ln ingred:veg:beet plantpart:root bio:plant_part
ln ingred:veg:carrot plantpart:root bio:plant_part
ln ingred:veg:cassava plantpart:root bio:plant_part
ln ingred:veg:daikon plantpart:root bio:plant_part
ln ingred:veg:jicama plantpart:root bio:plant_part
ln ingred:veg:lotus_root plantpart:root bio:plant_part
ln ingred:veg:parsnip plantpart:root bio:plant_part
ln ingred:veg:radish plantpart:root bio:plant_part
ln ingred:veg:turnip plantpart:root bio:plant_part
ln ingred:veg:potato plantpart:tuber bio:plant_part
ln ingred:veg:sweet_potato plantpart:tuber bio:plant_part
ln ingred:veg:taro plantpart:tuber bio:plant_part
ln ingred:veg:fennel plantpart:bulb bio:plant_part
ln ingred:veg:garlic plantpart:bulb bio:plant_part
ln ingred:veg:leek plantpart:bulb bio:plant_part
ln ingred:veg:onion plantpart:bulb bio:plant_part
ln ingred:veg:scallion plantpart:bulb bio:plant_part
ln ingred:veg:shallot plantpart:bulb bio:plant_part
ln ingred:veg:brussels_sprout plantpart:leaf bio:plant_part
ln ingred:veg:cabbage plantpart:leaf bio:plant_part
ln ingred:veg:kale plantpart:leaf bio:plant_part
ln ingred:veg:lettuce plantpart:leaf bio:plant_part
ln ingred:veg:radicchio plantpart:leaf bio:plant_part
ln ingred:veg:spinach plantpart:leaf bio:plant_part
ln ingred:veg:water_spinach plantpart:leaf bio:plant_part
ln ingred:veg:asparagus plantpart:stem bio:plant_part
ln ingred:veg:bamboo_shoot plantpart:stem bio:plant_part
ln ingred:veg:celery plantpart:stem bio:plant_part
ln ingred:veg:kohlrabi plantpart:stem bio:plant_part
ln ingred:veg:artichoke plantpart:flower bio:plant_part
ln ingred:veg:broccoli plantpart:flower bio:plant_part
ln ingred:veg:cauliflower plantpart:flower bio:plant_part
ln ingred:veg:bell_pepper plantpart:fruit_veg bio:plant_part
ln ingred:veg:bitter_melon plantpart:fruit_veg bio:plant_part
ln ingred:veg:chayote plantpart:fruit_veg bio:plant_part
ln ingred:veg:chili_pepper plantpart:fruit_veg bio:plant_part
ln ingred:veg:cucumber plantpart:fruit_veg bio:plant_part
ln ingred:veg:eggplant plantpart:fruit_veg bio:plant_part
ln ingred:veg:nopales plantpart:fruit_veg bio:plant_part
ln ingred:veg:okra plantpart:fruit_veg bio:plant_part
ln ingred:veg:pumpkin plantpart:fruit_veg bio:plant_part
ln ingred:veg:tomatillo plantpart:fruit_veg bio:plant_part
ln ingred:veg:tomato plantpart:fruit_veg bio:plant_part
ln ingred:veg:zucchini plantpart:fruit_veg bio:plant_part
ln ingred:veg:mushroom plantpart:fungus bio:plant_part
ln ingred:veg:shiitake plantpart:fungus bio:plant_part
ln ingred:veg:truffle plantpart:fungus bio:plant_part

