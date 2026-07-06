# Akasha ontology — namespace: ingred (enrichment)
# Adds emotion, sensory, colour, seasonal, and concept links to the 35
# base-pack ingredients.  Also creates category and seasonal sets.
# atoms: 0  (only links and set memberships — no new def atoms)

# ══ Category sets ══════════════════════════════════════════════════════════════

set.add name="set:ingred:vegetable" id="ingred:veg:onion"
set.add name="set:ingred:vegetable" id="ingred:veg:garlic"
set.add name="set:ingred:vegetable" id="ingred:veg:potato"
set.add name="set:ingred:vegetable" id="ingred:veg:tomato"
set.add name="set:ingred:vegetable" id="ingred:veg:carrot"
set.add name="set:ingred:vegetable" id="ingred:veg:cabbage"
set.add name="set:ingred:vegetable" id="ingred:veg:spinach"
set.add name="set:ingred:vegetable" id="ingred:veg:mushroom"
set.add name="set:ingred:vegetable" id="ingred:veg:chili_pepper"
set.add name="set:ingred:vegetable" id="ingred:veg:bell_pepper"

set.add name="set:ingred:fruit" id="ingred:fruit:apple"
set.add name="set:ingred:fruit" id="ingred:fruit:banana"
set.add name="set:ingred:fruit" id="ingred:fruit:orange"
set.add name="set:ingred:fruit" id="ingred:fruit:lemon"
set.add name="set:ingred:fruit" id="ingred:fruit:grape"

set.add name="set:ingred:grain" id="ingred:grain:rice"
set.add name="set:ingred:grain" id="ingred:grain:wheat"
set.add name="set:ingred:grain" id="ingred:grain:oats"

set.add name="set:ingred:legume" id="ingred:legume:chickpea"
set.add name="set:ingred:legume" id="ingred:legume:lentil"

set.add name="set:ingred:meat" id="ingred:meat:chicken"
set.add name="set:ingred:meat" id="ingred:meat:beef"
set.add name="set:ingred:meat" id="ingred:meat:pork"

set.add name="set:ingred:seafood" id="ingred:seafood:salmon"
set.add name="set:ingred:seafood" id="ingred:seafood:tuna"

set.add name="set:ingred:condiment" id="ingred:condiment:salt"
set.add name="set:ingred:condiment" id="ingred:condiment:sugar"
set.add name="set:ingred:condiment" id="ingred:condiment:olive_oil"
set.add name="set:ingred:condiment" id="ingred:condiment:butter"
set.add name="set:ingred:condiment" id="ingred:condiment:soy_sauce"

set.add name="set:ingred:spice" id="ingred:spice:black_pepper"
set.add name="set:ingred:spice" id="ingred:spice:cinnamon"
set.add name="set:ingred:spice" id="ingred:spice:cumin"

set.add name="set:ingred:herb" id="ingred:herb:basil"
set.add name="set:ingred:herb" id="ingred:herb:mint"

# ══ Seasonal sets ══════════════════════════════════════════════════════════════

# spring
set.add name="set:ingred:spring" id="ingred:veg:spinach"
set.add name="set:ingred:spring" id="ingred:veg:onion"
set.add name="set:ingred:spring" id="ingred:herb:mint"
set.add name="set:ingred:spring" id="ingred:veg:mushroom"

# summer
set.add name="set:ingred:summer" id="ingred:veg:tomato"
set.add name="set:ingred:summer" id="ingred:veg:chili_pepper"
set.add name="set:ingred:summer" id="ingred:veg:bell_pepper"
set.add name="set:ingred:summer" id="ingred:herb:basil"
set.add name="set:ingred:summer" id="ingred:fruit:grape"
set.add name="set:ingred:summer" id="ingred:fruit:lemon"

# autumn
set.add name="set:ingred:autumn" id="ingred:fruit:apple"
set.add name="set:ingred:autumn" id="ingred:fruit:grape"
set.add name="set:ingred:autumn" id="ingred:veg:carrot"
set.add name="set:ingred:autumn" id="ingred:veg:potato"
set.add name="set:ingred:autumn" id="ingred:veg:mushroom"
set.add name="set:ingred:autumn" id="ingred:veg:onion"
set.add name="set:ingred:autumn" id="ingred:spice:cinnamon"
set.add name="set:ingred:autumn" id="ingred:spice:cumin"
set.add name="set:ingred:autumn" id="ingred:legume:chickpea"
set.add name="set:ingred:autumn" id="ingred:legume:lentil"

# winter
set.add name="set:ingred:winter" id="ingred:veg:cabbage"
set.add name="set:ingred:winter" id="ingred:veg:potato"
set.add name="set:ingred:winter" id="ingred:grain:oats"
set.add name="set:ingred:winter" id="ingred:condiment:butter"
set.add name="set:ingred:winter" id="ingred:fruit:lemon"
set.add name="set:ingred:winter" id="ingred:fruit:orange"
set.add name="set:ingred:winter" id="ingred:spice:cinnamon"
set.add name="set:ingred:winter" id="ingred:meat:pork"

# ══ Vegetables — emotion, concept and colour enrichment ════════════════════════

# onion
ln ingred:veg:onion emo:nostalgia calc:associated_with
ln ingred:veg:onion emo:satisfaction calc:associated_with
ln ingred:veg:onion concept:food thesaurus:related
ln ingred:veg:onion concept:autumn thesaurus:related
ln ingred:veg:onion color:white thesaurus:related
ln ingred:veg:onion color:brown thesaurus:related

# garlic
ln ingred:veg:garlic emo:satisfaction calc:associated_with
ln ingred:veg:garlic emo:nostalgia calc:associated_with
ln ingred:veg:garlic concept:food thesaurus:related
ln ingred:veg:garlic color:white thesaurus:related

# potato
ln ingred:veg:potato emo:nostalgia calc:associated_with
ln ingred:veg:potato emo:satisfaction calc:associated_with
ln ingred:veg:potato emo:calmness calc:associated_with
ln ingred:veg:potato concept:food thesaurus:related
ln ingred:veg:potato concept:home thesaurus:related
ln ingred:veg:potato concept:autumn thesaurus:related
ln ingred:veg:potato color:brown thesaurus:related
ln ingred:veg:potato color:yellow thesaurus:related

# tomato
ln ingred:veg:tomato emo:joy calc:associated_with
ln ingred:veg:tomato emo:satisfaction calc:associated_with
ln ingred:veg:tomato concept:food thesaurus:related
ln ingred:veg:tomato concept:summer thesaurus:related
ln ingred:veg:tomato color:red thesaurus:related
ln ingred:veg:tomato sense:taste_sour thesaurus:related

# carrot
ln ingred:veg:carrot emo:joy calc:associated_with
ln ingred:veg:carrot emo:satisfaction calc:associated_with
ln ingred:veg:carrot concept:food thesaurus:related
ln ingred:veg:carrot concept:autumn thesaurus:related
ln ingred:veg:carrot color:orange thesaurus:related
ln ingred:veg:carrot sense:taste_sweet thesaurus:related

# cabbage
ln ingred:veg:cabbage emo:nostalgia calc:associated_with
ln ingred:veg:cabbage emo:satisfaction calc:associated_with
ln ingred:veg:cabbage concept:food thesaurus:related
ln ingred:veg:cabbage concept:winter thesaurus:related
ln ingred:veg:cabbage color:green thesaurus:related
ln ingred:veg:cabbage color:white thesaurus:related

# spinach
ln ingred:veg:spinach emo:satisfaction calc:associated_with
ln ingred:veg:spinach concept:food thesaurus:related
ln ingred:veg:spinach concept:spring thesaurus:related
ln ingred:veg:spinach concept:growth thesaurus:related
ln ingred:veg:spinach color:green thesaurus:related

# mushroom
ln ingred:veg:mushroom emo:nostalgia calc:associated_with
ln ingred:veg:mushroom emo:awe calc:associated_with
ln ingred:veg:mushroom emo:satisfaction calc:associated_with
ln ingred:veg:mushroom concept:food thesaurus:related
ln ingred:veg:mushroom concept:autumn thesaurus:related
ln ingred:veg:mushroom concept:forest thesaurus:related
ln ingred:veg:mushroom color:brown thesaurus:related
ln ingred:veg:mushroom sense:smell_earth thesaurus:related

# chili_pepper
ln ingred:veg:chili_pepper emo:excitement calc:associated_with
ln ingred:veg:chili_pepper emo:passion calc:associated_with
ln ingred:veg:chili_pepper concept:food thesaurus:related
ln ingred:veg:chili_pepper concept:summer thesaurus:related
ln ingred:veg:chili_pepper color:red thesaurus:related
ln ingred:veg:chili_pepper sense:warmth thesaurus:related

# bell_pepper
ln ingred:veg:bell_pepper emo:joy calc:associated_with
ln ingred:veg:bell_pepper concept:food thesaurus:related
ln ingred:veg:bell_pepper concept:summer thesaurus:related
ln ingred:veg:bell_pepper color:red thesaurus:related
ln ingred:veg:bell_pepper color:green thesaurus:related
ln ingred:veg:bell_pepper color:yellow thesaurus:related
ln ingred:veg:bell_pepper sense:taste_sweet thesaurus:related

# ══ Fruits — emotion, concept and colour enrichment ════════════════════════════

# apple
ln ingred:fruit:apple emo:nostalgia calc:associated_with
ln ingred:fruit:apple emo:satisfaction calc:associated_with
ln ingred:fruit:apple emo:joy calc:associated_with
ln ingred:fruit:apple concept:food thesaurus:related
ln ingred:fruit:apple concept:autumn thesaurus:related
ln ingred:fruit:apple color:red thesaurus:related
ln ingred:fruit:apple color:green thesaurus:related
ln ingred:fruit:apple sense:taste_sweet thesaurus:related
ln ingred:fruit:apple sense:taste_sour thesaurus:related

# banana
ln ingred:fruit:banana emo:joy calc:associated_with
ln ingred:fruit:banana emo:satisfaction calc:associated_with
ln ingred:fruit:banana concept:food thesaurus:related
ln ingred:fruit:banana color:yellow thesaurus:related
ln ingred:fruit:banana sense:taste_sweet thesaurus:related

# orange
ln ingred:fruit:orange emo:joy calc:associated_with
ln ingred:fruit:orange emo:excitement calc:associated_with
ln ingred:fruit:orange concept:food thesaurus:related
ln ingred:fruit:orange concept:winter thesaurus:related
ln ingred:fruit:orange color:orange thesaurus:related
ln ingred:fruit:orange sense:taste_sweet thesaurus:related
ln ingred:fruit:orange sense:taste_sour thesaurus:related

# lemon
ln ingred:fruit:lemon emo:joy calc:associated_with
ln ingred:fruit:lemon concept:food thesaurus:related
ln ingred:fruit:lemon concept:summer thesaurus:related
ln ingred:fruit:lemon color:yellow thesaurus:related
ln ingred:fruit:lemon sense:taste_sour thesaurus:related

# grape
ln ingred:fruit:grape emo:satisfaction calc:associated_with
ln ingred:fruit:grape emo:nostalgia calc:associated_with
ln ingred:fruit:grape emo:romance calc:associated_with
ln ingred:fruit:grape concept:food thesaurus:related
ln ingred:fruit:grape concept:autumn thesaurus:related
ln ingred:fruit:grape color:purple thesaurus:related
ln ingred:fruit:grape color:green thesaurus:related
ln ingred:fruit:grape sense:taste_sweet thesaurus:related
ln ingred:fruit:grape sense:taste_sour thesaurus:related

# ══ Grains — emotion, concept and seasonal enrichment ═════════════════════════

# rice
ln ingred:grain:rice emo:satisfaction calc:associated_with
ln ingred:grain:rice emo:nostalgia calc:associated_with
ln ingred:grain:rice emo:calmness calc:associated_with
ln ingred:grain:rice concept:food thesaurus:related
ln ingred:grain:rice concept:home thesaurus:related
ln ingred:grain:rice color:white thesaurus:related
set.add name="set:ingred:spring" id="ingred:grain:rice"
set.add name="set:ingred:summer" id="ingred:grain:rice"

# wheat
ln ingred:grain:wheat emo:satisfaction calc:associated_with
ln ingred:grain:wheat emo:nostalgia calc:associated_with
ln ingred:grain:wheat concept:food thesaurus:related
ln ingred:grain:wheat concept:summer thesaurus:related
ln ingred:grain:wheat color:yellow thesaurus:related
ln ingred:grain:wheat color:gold thesaurus:related
set.add name="set:ingred:summer" id="ingred:grain:wheat"
set.add name="set:ingred:autumn" id="ingred:grain:wheat"

# oats
ln ingred:grain:oats emo:satisfaction calc:associated_with
ln ingred:grain:oats emo:calmness calc:associated_with
ln ingred:grain:oats concept:food thesaurus:related
ln ingred:grain:oats concept:winter thesaurus:related
ln ingred:grain:oats color:brown thesaurus:related

# ══ Legumes — emotion and concept enrichment ══════════════════════════════════

# chickpea
ln ingred:legume:chickpea emo:satisfaction calc:associated_with
ln ingred:legume:chickpea emo:nostalgia calc:associated_with
ln ingred:legume:chickpea concept:food thesaurus:related
ln ingred:legume:chickpea color:yellow thesaurus:related

# lentil
ln ingred:legume:lentil emo:satisfaction calc:associated_with
ln ingred:legume:lentil emo:calmness calc:associated_with
ln ingred:legume:lentil emo:nostalgia calc:associated_with
ln ingred:legume:lentil concept:food thesaurus:related
ln ingred:legume:lentil concept:winter thesaurus:related
ln ingred:legume:lentil color:brown thesaurus:related

# ══ Meats — emotion and concept enrichment ════════════════════════════════════

# chicken
ln ingred:meat:chicken emo:satisfaction calc:associated_with
ln ingred:meat:chicken emo:nostalgia calc:associated_with
ln ingred:meat:chicken concept:food thesaurus:related
ln ingred:meat:chicken concept:home thesaurus:related
ln ingred:meat:chicken color:brown thesaurus:related
ln ingred:meat:chicken color:gold thesaurus:related
set.add name="set:ingred:summer" id="ingred:meat:chicken"

# beef
ln ingred:meat:beef emo:satisfaction calc:associated_with
ln ingred:meat:beef emo:craving calc:associated_with
ln ingred:meat:beef concept:food thesaurus:related
ln ingred:meat:beef color:red thesaurus:related
ln ingred:meat:beef color:brown thesaurus:related
set.add name="set:ingred:autumn" id="ingred:meat:beef"

# pork
ln ingred:meat:pork emo:satisfaction calc:associated_with
ln ingred:meat:pork emo:nostalgia calc:associated_with
ln ingred:meat:pork concept:food thesaurus:related
ln ingred:meat:pork concept:winter thesaurus:related
ln ingred:meat:pork color:pink thesaurus:related

# ══ Seafood — emotion and concept enrichment ══════════════════════════════════

# salmon
ln ingred:seafood:salmon emo:satisfaction calc:associated_with
ln ingred:seafood:salmon emo:admiration calc:associated_with
ln ingred:seafood:salmon concept:food thesaurus:related
ln ingred:seafood:salmon concept:ocean thesaurus:related
ln ingred:seafood:salmon concept:water thesaurus:related
ln ingred:seafood:salmon color:orange thesaurus:related
ln ingred:seafood:salmon color:pink thesaurus:related
set.add name="set:ingred:autumn" id="ingred:seafood:salmon"
set.add name="set:ingred:winter" id="ingred:seafood:salmon"

# tuna
ln ingred:seafood:tuna emo:satisfaction calc:associated_with
ln ingred:seafood:tuna concept:food thesaurus:related
ln ingred:seafood:tuna concept:ocean thesaurus:related
ln ingred:seafood:tuna concept:water thesaurus:related
ln ingred:seafood:tuna color:red thesaurus:related
set.add name="set:ingred:summer" id="ingred:seafood:tuna"

# ══ Condiments — emotion and sense enrichment ═════════════════════════════════

# salt
ln ingred:condiment:salt emo:satisfaction calc:associated_with
ln ingred:condiment:salt concept:food thesaurus:related
ln ingred:condiment:salt color:white thesaurus:related
ln ingred:condiment:salt sense:taste_umami thesaurus:related

# sugar
ln ingred:condiment:sugar emo:joy calc:associated_with
ln ingred:condiment:sugar emo:craving calc:associated_with
ln ingred:condiment:sugar concept:food thesaurus:related
ln ingred:condiment:sugar color:white thesaurus:related
ln ingred:condiment:sugar sense:taste_sweet thesaurus:related

# olive_oil
ln ingred:condiment:olive_oil emo:satisfaction calc:associated_with
ln ingred:condiment:olive_oil emo:nostalgia calc:associated_with
ln ingred:condiment:olive_oil concept:food thesaurus:related
ln ingred:condiment:olive_oil concept:summer thesaurus:related
ln ingred:condiment:olive_oil color:green thesaurus:related
ln ingred:condiment:olive_oil color:gold thesaurus:related
set.add name="set:ingred:summer" id="ingred:condiment:olive_oil"

# butter
ln ingred:condiment:butter emo:satisfaction calc:associated_with
ln ingred:condiment:butter emo:nostalgia calc:associated_with
ln ingred:condiment:butter emo:calmness calc:associated_with
ln ingred:condiment:butter concept:food thesaurus:related
ln ingred:condiment:butter concept:home thesaurus:related
ln ingred:condiment:butter concept:winter thesaurus:related
ln ingred:condiment:butter color:yellow thesaurus:related

# soy_sauce
ln ingred:condiment:soy_sauce emo:satisfaction calc:associated_with
ln ingred:condiment:soy_sauce emo:nostalgia calc:associated_with
ln ingred:condiment:soy_sauce concept:food thesaurus:related
ln ingred:condiment:soy_sauce color:brown thesaurus:related
ln ingred:condiment:soy_sauce sense:taste_umami thesaurus:related

# ══ Spices — emotion, sense and seasonal enrichment ══════════════════════════

# black_pepper
ln ingred:spice:black_pepper emo:satisfaction calc:associated_with
ln ingred:spice:black_pepper concept:food thesaurus:related
ln ingred:spice:black_pepper color:black thesaurus:related

# cinnamon
ln ingred:spice:cinnamon emo:nostalgia calc:associated_with
ln ingred:spice:cinnamon emo:satisfaction calc:associated_with
ln ingred:spice:cinnamon emo:calmness calc:associated_with
ln ingred:spice:cinnamon concept:food thesaurus:related
ln ingred:spice:cinnamon concept:autumn thesaurus:related
ln ingred:spice:cinnamon concept:winter thesaurus:related
ln ingred:spice:cinnamon concept:home thesaurus:related
ln ingred:spice:cinnamon color:brown thesaurus:related
ln ingred:spice:cinnamon color:orange thesaurus:related
ln ingred:spice:cinnamon sense:warmth thesaurus:related

# cumin
ln ingred:spice:cumin emo:satisfaction calc:associated_with
ln ingred:spice:cumin emo:nostalgia calc:associated_with
ln ingred:spice:cumin concept:food thesaurus:related
ln ingred:spice:cumin color:brown thesaurus:related

# ══ Herbs — emotion, sense and seasonal enrichment ════════════════════════════

# basil
ln ingred:herb:basil emo:joy calc:associated_with
ln ingred:herb:basil emo:nostalgia calc:associated_with
ln ingred:herb:basil concept:food thesaurus:related
ln ingred:herb:basil concept:summer thesaurus:related
ln ingred:herb:basil color:green thesaurus:related

# mint
ln ingred:herb:mint emo:joy calc:associated_with
ln ingred:herb:mint emo:excitement calc:associated_with
ln ingred:herb:mint concept:food thesaurus:related
ln ingred:herb:mint concept:spring thesaurus:related
ln ingred:herb:mint concept:summer thesaurus:related
ln ingred:herb:mint color:green thesaurus:related
ln ingred:herb:mint sense:cold thesaurus:related
