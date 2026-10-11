# Akasha ontology — cuisine analysis: common thread vs signature.
# To survey world cuisines without losing each one's distinctive character, mark BOTH the
# shared substrate (common_thread) and the distinctive flavour base / staple /
# signature technique (cuisine:signature). Breaking each flavour base into its
# components makes the shared aromatics (onion/garlic) surface as common thread and the
# differentiators (fat, ferment, spice) as signature. Base pack.

def "culinary:common_thread" "通底 — elements shared across most world cuisines (the universal substrate)."
def "culinary:signature" "違い / こだわり — what distinguishes a cuisine (its flavour base, staple, hallmark technique)."
def "culinary:flavor_base" "A cuisine's aromatic/flavour foundation."

# ── common thread: universal threads ──
ln ingred:veg:onion culinary:common_thread culinary:common   # allium aromatic base, near-universal
ln ingred:veg:garlic culinary:common_thread culinary:common   # allium aromatic base, near-universal
ln culinary:common_thread technique:grilling culinary:common   # fire/grilling — universal
ln culinary:common_thread technique:fermentation culinary:common   # preservation — universal
ln ingred:condiment:salt culinary:common_thread culinary:common

# ── signature: flavour base per cuisine + components ──
def "flavor_base:mirepoix" "Mirepoix — onion, carrot, celery softened in butter."
ln flavor_base:mirepoix culinary:flavor_base thesaurus:related
ln cuisine:french flavor_base:mirepoix cuisine:signature
ln flavor_base:mirepoix ingred:veg:onion culinary:component
ln flavor_base:mirepoix ingred:veg:carrot culinary:component
ln flavor_base:mirepoix ingred:veg:celery culinary:component
ln flavor_base:mirepoix ingred:condiment:butter culinary:component
def "flavor_base:soffritto" "Soffritto — onion, carrot, celery in olive oil (+garlic, tomato)."
ln flavor_base:soffritto culinary:flavor_base thesaurus:related
ln cuisine:italian flavor_base:soffritto cuisine:signature
ln flavor_base:soffritto ingred:veg:onion culinary:component
ln flavor_base:soffritto ingred:veg:carrot culinary:component
ln flavor_base:soffritto ingred:veg:celery culinary:component
ln flavor_base:soffritto ingred:condiment:olive_oil culinary:component
ln flavor_base:soffritto ingred:veg:garlic culinary:component
ln flavor_base:soffritto ingred:veg:tomato culinary:component
def "flavor_base:ginger_garlic_scallion" "薑蔥蒜 — ginger, garlic, scallion; the Chinese aromatic base."
ln flavor_base:ginger_garlic_scallion culinary:flavor_base thesaurus:related
ln cuisine:chinese flavor_base:ginger_garlic_scallion cuisine:signature
ln flavor_base:ginger_garlic_scallion ingred:spice:ginger culinary:component
ln flavor_base:ginger_garlic_scallion ingred:veg:garlic culinary:component
ln flavor_base:ginger_garlic_scallion ingred:veg:scallion culinary:component
ln flavor_base:ginger_garlic_scallion ingred:condiment:soy_sauce culinary:component
def "flavor_base:onion_ginger_garlic" "Onion-ginger-garlic masala base with tempered spices."
ln flavor_base:onion_ginger_garlic culinary:flavor_base thesaurus:related
ln cuisine:indian flavor_base:onion_ginger_garlic cuisine:signature
ln flavor_base:onion_ginger_garlic ingred:veg:onion culinary:component
ln flavor_base:onion_ginger_garlic ingred:spice:ginger culinary:component
ln flavor_base:onion_ginger_garlic ingred:veg:garlic culinary:component
ln flavor_base:onion_ginger_garlic ingred:spice:cumin culinary:component
ln flavor_base:onion_ginger_garlic ingred:spice:mustard_seed culinary:component
ln flavor_base:onion_ginger_garlic ingred:condiment:ghee culinary:component
def "flavor_base:sofrito" "Sofrito — onion, garlic, pepper, tomato in olive oil."
ln flavor_base:sofrito culinary:flavor_base thesaurus:related
ln cuisine:spanish flavor_base:sofrito cuisine:signature
ln flavor_base:sofrito ingred:veg:onion culinary:component
ln flavor_base:sofrito ingred:veg:garlic culinary:component
ln flavor_base:sofrito ingred:veg:bell_pepper culinary:component
ln flavor_base:sofrito ingred:veg:tomato culinary:component
ln flavor_base:sofrito ingred:condiment:olive_oil culinary:component
def "flavor_base:thai_paste" "Thai curry base — lemongrass, galangal, kaffir lime, chilli."
ln flavor_base:thai_paste culinary:flavor_base thesaurus:related
ln cuisine:thai flavor_base:thai_paste cuisine:signature
ln flavor_base:thai_paste ingred:herb:lemongrass culinary:component
ln flavor_base:thai_paste ingred:spice:galangal culinary:component
ln flavor_base:thai_paste ingred:herb:kaffir_lime_leaf culinary:component
ln flavor_base:thai_paste ingred:veg:chili_pepper culinary:component
ln flavor_base:thai_paste ingred:condiment:fish_sauce culinary:component
ln flavor_base:thai_paste ingred:fruit:coconut culinary:component
def "flavor_base:dashi" "Dashi — kombu + katsuobushi umami stock, the Japanese base."
ln flavor_base:dashi culinary:flavor_base thesaurus:related
ln cuisine:japanese flavor_base:dashi cuisine:signature
ln flavor_base:dashi ingred:seafood:kombu culinary:component
ln flavor_base:dashi ingred:ferment:katsuobushi culinary:component
ln flavor_base:dashi ingred:condiment:soy_sauce culinary:component
ln flavor_base:dashi ingred:condiment:miso culinary:component
ln flavor_base:dashi ingred:condiment:mirin culinary:component
def "flavor_base:cajun_trinity" "Holy trinity — onion, celery, bell pepper."
ln flavor_base:cajun_trinity culinary:flavor_base thesaurus:related
ln cuisine:american flavor_base:cajun_trinity cuisine:signature
ln flavor_base:cajun_trinity ingred:veg:onion culinary:component
ln flavor_base:cajun_trinity ingred:veg:celery culinary:component
ln flavor_base:cajun_trinity ingred:veg:bell_pepper culinary:component
def "flavor_base:levantine_base" "Levantine base — olive oil, garlic, lemon, cumin, tahini."
ln flavor_base:levantine_base culinary:flavor_base thesaurus:related
ln cuisine:turkish flavor_base:levantine_base cuisine:signature
ln flavor_base:levantine_base ingred:condiment:olive_oil culinary:component
ln flavor_base:levantine_base ingred:veg:garlic culinary:component
ln flavor_base:levantine_base ingred:fruit:lemon culinary:component
ln flavor_base:levantine_base ingred:spice:cumin culinary:component
ln flavor_base:levantine_base ingred:condiment:tahini culinary:component
def "flavor_base:mexican_base" "Mexican base — chilli, tomato, onion, cilantro, lime, corn."
ln flavor_base:mexican_base culinary:flavor_base thesaurus:related
ln cuisine:mexican flavor_base:mexican_base cuisine:signature
ln flavor_base:mexican_base ingred:veg:chili_pepper culinary:component
ln flavor_base:mexican_base ingred:veg:tomato culinary:component
ln flavor_base:mexican_base ingred:veg:onion culinary:component
ln flavor_base:mexican_base ingred:herb:cilantro culinary:component
ln flavor_base:mexican_base ingred:fruit:lime culinary:component
ln flavor_base:mexican_base ingred:grain:corn culinary:component
def "flavor_base:korean_base" "Korean base — gochujang, garlic, sesame, scallion, ferment."
ln flavor_base:korean_base culinary:flavor_base thesaurus:related
ln cuisine:korean flavor_base:korean_base cuisine:signature
ln flavor_base:korean_base ingred:condiment:gochujang culinary:component
ln flavor_base:korean_base ingred:veg:garlic culinary:component
ln flavor_base:korean_base ingred:seed:sesame culinary:component
ln flavor_base:korean_base ingred:veg:scallion culinary:component
ln flavor_base:korean_base ingred:ferment:kimchi culinary:component
def "flavor_base:west_african_base" "West African base — tomato, onion, chilli in palm/red oil."
ln flavor_base:west_african_base culinary:flavor_base thesaurus:related
ln cuisine:nigerian flavor_base:west_african_base cuisine:signature
ln flavor_base:west_african_base ingred:veg:tomato culinary:component
ln flavor_base:west_african_base ingred:veg:onion culinary:component
ln flavor_base:west_african_base ingred:veg:chili_pepper culinary:component

# ── staple starch per cuisine (a shared need, a distinctive choice) ──
ln cuisine:chinese ingred:grain:rice cuisine:staple
ln cuisine:japanese ingred:grain:rice cuisine:staple
ln cuisine:korean ingred:grain:rice cuisine:staple
ln cuisine:thai ingred:grain:rice cuisine:staple
ln cuisine:indian ingred:grain:rice cuisine:staple
ln cuisine:french ingred:grain:wheat cuisine:staple
ln cuisine:italian ingred:grain:wheat cuisine:staple
ln cuisine:turkish ingred:grain:wheat cuisine:staple
ln cuisine:mexican ingred:grain:corn cuisine:staple
ln cuisine:ethiopian ingred:grain:teff cuisine:staple
ln cuisine:nigerian ingred:veg:cassava cuisine:staple

# ── signature technique per cuisine ──
ln cuisine:japanese technique:dashi cuisine:signature
ln cuisine:indian technique:tandoor cuisine:signature
ln cuisine:indian technique:tadka cuisine:signature
ln cuisine:chinese technique:stir_frying cuisine:signature
ln cuisine:chinese technique:velveting cuisine:signature
ln cuisine:mexican technique:nixtamalization cuisine:signature
ln cuisine:mexican technique:comal cuisine:signature
ln cuisine:korean technique:fermentation cuisine:signature
ln cuisine:turkish technique:mangal cuisine:signature
ln cuisine:french technique:braising cuisine:signature
ln cuisine:french technique:sauteing cuisine:signature
ln cuisine:ethiopian technique:dhungar cuisine:signature
