# Akasha ontology — FAO major crops that were missing (fruits, vegetables,
# pulses, sugar crops, cocoa/coffee). Concepts + links to existing axes only
# (lean). Base pack.

def "ingred:fruit:plantain" "Plantain — a starchy cooking banana; a staple across the tropics."
al ingred:fruit:plantain plantain
ln ingred:fruit:plantain fruit_type:tropical bio:fruit_type
ln ingred:fruit:plantain plantpart:fruit_veg bio:plant_part

def "ingred:fruit:date" "Date — the very sweet fruit of the date palm; staple in arid regions."
al ingred:fruit:date date
ln ingred:fruit:date fruit_type:tropical bio:fruit_type
ln ingred:fruit:date dna:taste:sweet calc:associated_with

def "ingred:fruit:kiwi" "Kiwifruit — a fuzzy green berry, sweet-tart."
al ingred:fruit:kiwi kiwi
al ingred:fruit:kiwi kiwifruit
ln ingred:fruit:kiwi fruit_type:berry bio:fruit_type
ln ingred:fruit:kiwi dna:taste:sour calc:associated_with
ln ingred:fruit:kiwi dna:color:green calc:associated_with

def "ingred:fruit:guava" "Guava — a fragrant tropical fruit."
al ingred:fruit:guava guava
ln ingred:fruit:guava fruit_type:tropical bio:fruit_type
ln ingred:fruit:guava dna:taste:sweet calc:associated_with

def "ingred:fruit:persimmon" "Persimmon — a sweet autumn fruit (kaki)."
al ingred:fruit:persimmon persimmon
al ingred:fruit:persimmon kaki
ln ingred:fruit:persimmon fruit_type:berry bio:fruit_type
ln ingred:fruit:persimmon dna:taste:sweet calc:associated_with

def "ingred:fruit:olive" "Olive — the drupe pressed for olive oil; cured as a condiment."
al ingred:fruit:olive olive
ln ingred:fruit:olive fruit_type:stone bio:fruit_type
ln ingred:fruit:olive fat_source:plant bio:fat_source
ln ingred:fruit:olive dna:taste:bitter calc:associated_with

def "ingred:fruit:lychee" "Lychee — a fragrant, sweet subtropical fruit."
al ingred:fruit:lychee lychee
al ingred:fruit:lychee litchi
ln ingred:fruit:lychee fruit_type:tropical bio:fruit_type
ln ingred:fruit:lychee dna:taste:sweet calc:associated_with
ln ingred:fruit:lychee cuisine:chinese thesaurus:related

def "ingred:fruit:jackfruit" "Jackfruit — a large tropical fruit, sweet ripe or savoury unripe."
al ingred:fruit:jackfruit jackfruit
ln ingred:fruit:jackfruit fruit_type:tropical bio:fruit_type
ln ingred:fruit:jackfruit dna:taste:sweet calc:associated_with

def "ingred:fruit:passion_fruit" "Passion fruit — an intensely aromatic, tart tropical fruit."
al ingred:fruit:passion_fruit passion_fruit
ln ingred:fruit:passion_fruit fruit_type:tropical bio:fruit_type
ln ingred:fruit:passion_fruit dna:taste:sour calc:associated_with

def "ingred:veg:yam" "Yam — a starchy tropical tuber; a staple in West Africa."
al ingred:veg:yam yam
ln ingred:veg:yam plantpart:tuber bio:plant_part

def "ingred:veg:bok_choy" "Bok choy — a mild Chinese leafy brassica."
al ingred:veg:bok_choy bok_choy
al ingred:veg:bok_choy pak_choi
ln ingred:veg:bok_choy plantpart:leaf bio:plant_part
ln ingred:veg:bok_choy cuisine:chinese thesaurus:related

def "ingred:veg:butternut_squash" "Butternut squash — a sweet winter squash."
al ingred:veg:butternut_squash butternut_squash
al ingred:veg:butternut_squash butternut
ln ingred:veg:butternut_squash plantpart:fruit_veg bio:plant_part
ln ingred:veg:butternut_squash dna:taste:sweet calc:associated_with

def "ingred:veg:green_bean" "Green bean — the immature pod of the common bean."
al ingred:veg:green_bean green_bean
al ingred:veg:green_bean string_bean
ln ingred:veg:green_bean plantpart:fruit_veg bio:plant_part

def "ingred:legume:pea" "Pea — a sweet green pulse (garden pea)."
al ingred:legume:pea pea
ln ingred:legume:pea legume_type:pulse bio:legume_type
ln ingred:legume:pea dna:taste:sweet calc:associated_with

def "ingred:legume:fava_bean" "Fava (broad) bean — a large flat pulse."
al ingred:legume:fava_bean fava_bean
al ingred:legume:fava_bean broad_bean
ln ingred:legume:fava_bean legume_type:pulse bio:legume_type

def "ingred:legume:cowpea" "Cowpea — a drought-tolerant pulse (black-eyed pea)."
al ingred:legume:cowpea cowpea
al ingred:legume:cowpea black_eyed_pea
ln ingred:legume:cowpea legume_type:pulse bio:legume_type

def "ingred:legume:pigeon_pea" "Pigeon pea — a tropical pulse (toor dal)."
al ingred:legume:pigeon_pea pigeon_pea
al ingred:legume:pigeon_pea toor_dal
ln ingred:legume:pigeon_pea legume_type:pulse bio:legume_type
ln ingred:legume:pigeon_pea cuisine:indian thesaurus:related

def "ingred:grain:sugarcane" "Sugarcane — a giant grass; the main source of sugar."
al ingred:grain:sugarcane sugarcane
ln ingred:grain:sugarcane grain_type:cereal bio:grain_type
ln ingred:grain:sugarcane dna:taste:sweet calc:associated_with

def "ingred:veg:sugar_beet" "Sugar beet — a root crop refined into sugar."
al ingred:veg:sugar_beet sugar_beet
ln ingred:veg:sugar_beet plantpart:root bio:plant_part
ln ingred:veg:sugar_beet dna:taste:sweet calc:associated_with

def "ingred:seed:cocoa" "Cocoa — the fermented, roasted seed of the cacao tree; base of chocolate."
al ingred:seed:cocoa cocoa
al ingred:seed:cocoa cacao
ln ingred:seed:cocoa nut_type:seed bio:nut_type
ln ingred:seed:cocoa fat_source:plant bio:fat_source
ln ingred:seed:cocoa dna:taste:bitter calc:associated_with

def "ingred:seed:coffee" "Coffee — the roasted seed (bean) of the coffee cherry."
al ingred:seed:coffee coffee
al ingred:seed:coffee coffee_bean
ln ingred:seed:coffee nut_type:seed bio:nut_type
ln ingred:seed:coffee dna:taste:bitter calc:associated_with

# sugar is refined from sugarcane / sugar beet
ln ingred:condiment:sugar ingred:grain:sugarcane @derived_from
ln ingred:condiment:sugar ingred:veg:sugar_beet @derived_from

