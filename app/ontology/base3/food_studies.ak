# Akasha ontology — food studies & sensory science.
# The humanities of food — folklore, ethnology, anthropology, history — and the
# science of tasting. Heavy bridging to cuisine:/dish:/event:/oral:/dh:/region:
# and to the tasting: vocabulary. Base pack.

def "foodstud" "Food studies — the cultural, historical and social study of food."
def "foodstud:food_folklore" "Traditional food beliefs, customs and lore passed through communities (食民俗)."
ln foodstud:food_folklore foodstud thesaurus:related
def "foodstud:food_ethnology" "The comparative study of foodways across cultures."
ln foodstud:food_ethnology foodstud thesaurus:related
def "foodstud:food_anthropology" "How food constitutes society, identity and exchange."
ln foodstud:food_anthropology foodstud thesaurus:related
def "foodstud:culinary_history" "The historical study of ingredients, dishes and eating."
ln foodstud:culinary_history foodstud thesaurus:related
ln foodstud:culinary_history dh:distant_reading thesaurus:related
def "foodstud:gastronomy_studies" "The scholarly study of food and dining as culture."
ln foodstud:gastronomy_studies foodstud thesaurus:related
def "foodstud:foodways" "The whole web of a group's food practices — sourcing, cooking, eating, meaning."
ln foodstud:foodways foodstud thesaurus:related
ln foodstud:foodways cuisine:japanese thesaurus:related
ln foodstud:foodways region:east_asia thesaurus:related
def "foodstud:commensality" "Eating together as a bond of family and community."
ln foodstud:commensality foodstud thesaurus:related
ln foodstud:commensality social:friend_of thesaurus:related
def "foodstud:food_taboo" "A culturally forbidden food (pork, beef, insects, depending on culture)."
ln foodstud:food_taboo foodstud thesaurus:related
ln foodstud:food_taboo diet:vegetarian thesaurus:related
ln foodstud:food_taboo diet:vegan thesaurus:related
def "foodstud:ritual_food" "Food prescribed for ceremony and rite (osechi, communion bread)."
ln foodstud:ritual_food foodstud thesaurus:related
ln foodstud:ritual_food event:local_festival thesaurus:related
def "foodstud:festival_food" "Special dishes tied to a festival or season (お節, Christmas pudding)."
ln foodstud:festival_food foodstud thesaurus:related
ln foodstud:festival_food event:local_festival thesaurus:related
ln foodstud:festival_food event:christmas thesaurus:related
def "foodstud:culinary_heritage" "A community's inherited food tradition, sometimes safeguarded."
ln foodstud:culinary_heritage foodstud thesaurus:related
def "foodstud:intangible_cultural_heritage" "UNESCO-recognised living traditions — washoku, the French gastronomic meal, kimjang."
ln foodstud:intangible_cultural_heritage foodstud thesaurus:related
ln foodstud:intangible_cultural_heritage cuisine:japanese thesaurus:related
ln foodstud:intangible_cultural_heritage cuisine:french thesaurus:related
def "foodstud:food_symbolism" "Meanings foods carry — luck, purity, fertility, mourning."
ln foodstud:food_symbolism foodstud thesaurus:related
ln foodstud:food_symbolism oral:motif thesaurus:related
def "foodstud:comfort_food" "Food eaten for emotional solace, freighted with memory."
ln foodstud:comfort_food foodstud thesaurus:related
ln foodstud:comfort_food emo:nostalgia thesaurus:related
def "foodstud:food_memory" "The powerful tie between taste, smell and remembrance (cf. Proust's madeleine)."
ln foodstud:food_memory foodstud thesaurus:related
ln foodstud:food_memory emo:nostalgia thesaurus:related
def "foodstud:recipe_transmission" "How recipes pass down — orally, in manuscript, in print."
ln foodstud:recipe_transmission foodstud thesaurus:related
ln foodstud:recipe_transmission oral:oral_tradition thesaurus:related
ln foodstud:recipe_transmission oral:transmission thesaurus:related
ln foodstud:recipe_transmission dh:transcription thesaurus:related
def "foodstud:cookbook_history" "The history of the cookbook as a cultural document."
ln foodstud:cookbook_history foodstud thesaurus:related
ln foodstud:cookbook_history dh:close_reading thesaurus:related
ln foodstud:cookbook_history lib:cataloging thesaurus:related
def "foodstud:columbian_exchange" "The post-1492 transfer of foods (tomato, chilli, potato, maize) that remade world cuisines."
ln foodstud:columbian_exchange foodstud thesaurus:related
ln foodstud:columbian_exchange cuisine:mexican thesaurus:related
ln foodstud:columbian_exchange region:mesoamerica thesaurus:related
def "foodstud:spice_trade" "The long-distance trade that drove exploration and shaped cuisines."
ln foodstud:spice_trade foodstud thesaurus:related
def "foodstud:terroir" "The taste of place — soil, climate and tradition expressed in a food (テロワール)."
ln foodstud:terroir foodstud thesaurus:related
ln foodstud:terroir tasting:terroir thesaurus:related
ln foodstud:terroir cuisine:italian thesaurus:related
def "foodstud:culinary_identity" "Food as a marker of national, regional or ethnic identity."
ln foodstud:culinary_identity foodstud thesaurus:related
ln foodstud:culinary_identity culinary:signature thesaurus:related
def "foodstud:hospitality" "The social obligation and art of feeding a guest."
ln foodstud:hospitality foodstud thesaurus:related
# ── sensory science ──
def "sensory" "Sensory science — the perception and evaluation of food."
def "sensory:sensory_evaluation" "Systematic measurement of food perception by human panels (官能評価)."
ln sensory:sensory_evaluation sensory thesaurus:related
ln sensory:sensory_evaluation tasting:terroir thesaurus:related
ln sensory:sensory_evaluation research thesaurus:related
def "sensory:sensory_panel" "A trained group scoring a food's sensory attributes."
ln sensory:sensory_panel sensory thesaurus:related
def "sensory:hedonic_scale" "A liking scale (e.g. 9-point) measuring preference."
ln sensory:hedonic_scale sensory thesaurus:related
def "sensory:descriptive_analysis" "Panellists profiling intensity of defined attributes."
ln sensory:descriptive_analysis sensory thesaurus:related
def "sensory:detection_threshold" "The lowest concentration at which a stimulus is sensed."
ln sensory:detection_threshold sensory thesaurus:related
def "sensory:gustation" "The sense of taste — sweet, sour, salty, bitter, umami."
ln sensory:gustation sensory thesaurus:related
ln sensory:gustation tasting:viscosity thesaurus:related
def "sensory:olfaction" "The sense of smell; retronasal olfaction dominates flavour."
ln sensory:olfaction sensory thesaurus:related
ln sensory:olfaction tasting:primary_aroma thesaurus:related
def "sensory:umami" "The savoury fifth taste of glutamate and nucleotides (旨味)."
ln sensory:umami sensory thesaurus:related
ln sensory:umami cuisine:japanese thesaurus:related
ln sensory:umami foodsci:koji thesaurus:related
def "sensory:kokumi" "A mouthfulness/heartiness sensation enhancing other tastes (こく味)."
ln sensory:kokumi sensory thesaurus:related
ln sensory:kokumi sensory:umami thesaurus:related
def "sensory:flavor_perception" "The brain's fusion of taste, aroma, texture and trigeminal input."
ln sensory:flavor_perception sensory thesaurus:related
ln sensory:flavor_perception emo:joy thesaurus:related
def "sensory:trigeminal_sensation" "Chemesthesis — pungency, cooling, tingling (chilli heat, mint)."
ln sensory:trigeminal_sensation sensory thesaurus:related
def "sensory:aroma_compound" "A volatile molecule contributing to smell and flavour."
ln sensory:aroma_compound sensory thesaurus:related
ln sensory:aroma_compound tasting:secondary_aroma thesaurus:related
def "sensory:food_pairing_hypothesis" "The idea that foods sharing key aroma compounds pair well."
ln sensory:food_pairing_hypothesis sensory thesaurus:related
ln sensory:food_pairing_hypothesis dh:network thesaurus:related
