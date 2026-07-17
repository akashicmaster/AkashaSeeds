# Akasha ontology — Ayurveda food science (rasa/virya/dosha). Descriptive; provenance: traditional.

def "ayurveda:dosha:vata" "Vata dosha (air/ether) — light, dry, mobile."
ln ayurveda:dosha:vata tradition:ayurveda thesaurus:related
def "ayurveda:dosha:pitta" "Pitta dosha (fire/water) — hot, sharp."
ln ayurveda:dosha:pitta tradition:ayurveda thesaurus:related
def "ayurveda:dosha:kapha" "Kapha dosha (earth/water) — heavy, cool, stable."
ln ayurveda:dosha:kapha tradition:ayurveda thesaurus:related
def "ayurveda:virya:heating" "Virya heating (ushna)."
ln ayurveda:virya:heating tradition:ayurveda thesaurus:related
def "ayurveda:virya:cooling" "Virya cooling (shita)."
ln ayurveda:virya:cooling tradition:ayurveda thesaurus:related
def "ayurveda:rasa:sweet" "Rasa (taste): sweet."
ln ayurveda:rasa:sweet dna:taste:sweet thesaurus:related
ln ayurveda:rasa:sweet tradition:ayurveda thesaurus:related
def "ayurveda:rasa:sour" "Rasa (taste): sour."
ln ayurveda:rasa:sour dna:taste:sour thesaurus:related
ln ayurveda:rasa:sour tradition:ayurveda thesaurus:related
def "ayurveda:rasa:salty" "Rasa (taste): salty."
ln ayurveda:rasa:salty dna:taste:salty thesaurus:related
ln ayurveda:rasa:salty tradition:ayurveda thesaurus:related
def "ayurveda:rasa:pungent" "Rasa (taste): pungent."
ln ayurveda:rasa:pungent dna:pungency:hot thesaurus:related
ln ayurveda:rasa:pungent tradition:ayurveda thesaurus:related
def "ayurveda:rasa:bitter" "Rasa (taste): bitter."
ln ayurveda:rasa:bitter dna:taste:bitter thesaurus:related
ln ayurveda:rasa:bitter tradition:ayurveda thesaurus:related
def "ayurveda:rasa:astringent" "Rasa (taste): astringent."
ln ayurveda:rasa:astringent dna:pungency:astringent thesaurus:related
ln ayurveda:rasa:astringent tradition:ayurveda thesaurus:related

# ── food → virya + dosha effect ──
ln ingred:spice:ginger ayurveda:virya:heating ayurveda:virya
ln ingred:spice:ginger ayurveda:dosha:vata ayurveda:pacifies
ln ingred:spice:ginger ayurveda:dosha:kapha ayurveda:pacifies
ln ingred:spice:ginger ayurveda:dosha:pitta ayurveda:aggravates
ln ingred:veg:garlic ayurveda:virya:heating ayurveda:virya
ln ingred:veg:garlic ayurveda:dosha:vata ayurveda:pacifies
ln ingred:veg:garlic ayurveda:dosha:kapha ayurveda:pacifies
ln ingred:veg:garlic ayurveda:dosha:pitta ayurveda:aggravates
ln ingred:veg:chili_pepper ayurveda:virya:heating ayurveda:virya
ln ingred:veg:chili_pepper ayurveda:dosha:kapha ayurveda:pacifies
ln ingred:veg:chili_pepper ayurveda:dosha:pitta ayurveda:aggravates
ln ingred:veg:chili_pepper ayurveda:dosha:vata ayurveda:aggravates
ln ingred:spice:black_pepper ayurveda:virya:heating ayurveda:virya
ln ingred:spice:black_pepper ayurveda:dosha:kapha ayurveda:pacifies
ln ingred:spice:black_pepper ayurveda:dosha:pitta ayurveda:aggravates
ln ingred:spice:cinnamon ayurveda:virya:heating ayurveda:virya
ln ingred:spice:cinnamon ayurveda:dosha:vata ayurveda:pacifies
ln ingred:spice:cinnamon ayurveda:dosha:kapha ayurveda:pacifies
ln ingred:spice:cinnamon ayurveda:dosha:pitta ayurveda:aggravates
ln ingred:veg:cucumber ayurveda:virya:cooling ayurveda:virya
ln ingred:veg:cucumber ayurveda:dosha:pitta ayurveda:pacifies
ln ingred:veg:cucumber ayurveda:dosha:vata ayurveda:aggravates
ln ingred:fruit:watermelon ayurveda:virya:cooling ayurveda:virya
ln ingred:fruit:watermelon ayurveda:dosha:pitta ayurveda:pacifies
ln ingred:fruit:watermelon ayurveda:dosha:kapha ayurveda:aggravates
ln ingred:fruit:lemon ayurveda:virya:heating ayurveda:virya
ln ingred:fruit:lemon ayurveda:dosha:vata ayurveda:pacifies
ln ingred:fruit:lemon ayurveda:dosha:pitta ayurveda:aggravates
ln ingred:condiment:ghee ayurveda:virya:cooling ayurveda:virya
ln ingred:condiment:ghee ayurveda:dosha:vata ayurveda:pacifies
ln ingred:condiment:ghee ayurveda:dosha:pitta ayurveda:pacifies
ln ingred:condiment:ghee ayurveda:dosha:kapha ayurveda:aggravates
ln ingred:condiment:honey ayurveda:virya:heating ayurveda:virya
ln ingred:condiment:honey ayurveda:dosha:kapha ayurveda:pacifies
ln ingred:grain:rice ayurveda:virya:cooling ayurveda:virya
ln ingred:grain:rice ayurveda:dosha:pitta ayurveda:pacifies
ln ingred:grain:rice ayurveda:dosha:vata ayurveda:pacifies
ln ingred:grain:rice ayurveda:dosha:kapha ayurveda:aggravates
ln ingred:ferment:yogurt ayurveda:virya:heating ayurveda:virya
ln ingred:ferment:yogurt ayurveda:dosha:vata ayurveda:pacifies
ln ingred:ferment:yogurt ayurveda:dosha:kapha ayurveda:aggravates
ln ingred:ferment:yogurt ayurveda:dosha:pitta ayurveda:aggravates
ln ingred:fruit:banana ayurveda:virya:cooling ayurveda:virya
ln ingred:fruit:banana ayurveda:dosha:vata ayurveda:pacifies
ln ingred:fruit:banana ayurveda:dosha:pitta ayurveda:pacifies
ln ingred:fruit:banana ayurveda:dosha:kapha ayurveda:aggravates
ln ingred:fruit:mango ayurveda:virya:heating ayurveda:virya
ln ingred:fruit:mango ayurveda:dosha:vata ayurveda:pacifies
ln ingred:fruit:mango ayurveda:dosha:kapha ayurveda:aggravates
ln ingred:spice:turmeric ayurveda:virya:heating ayurveda:virya
ln ingred:spice:turmeric ayurveda:dosha:kapha ayurveda:pacifies
ln ingred:spice:coriander_seed ayurveda:virya:cooling ayurveda:virya
ln ingred:spice:coriander_seed ayurveda:dosha:pitta ayurveda:pacifies
ln ingred:spice:cumin ayurveda:virya:heating ayurveda:virya
ln ingred:spice:cumin ayurveda:dosha:vata ayurveda:pacifies
ln ingred:spice:cumin ayurveda:dosha:kapha ayurveda:pacifies
ln ingred:spice:cumin ayurveda:dosha:pitta ayurveda:aggravates
ln ingred:spice:fennel_seed ayurveda:virya:cooling ayurveda:virya
ln ingred:spice:fennel_seed ayurveda:dosha:vata ayurveda:pacifies
ln ingred:spice:fennel_seed ayurveda:dosha:pitta ayurveda:pacifies
ln ingred:spice:fennel_seed ayurveda:dosha:kapha ayurveda:pacifies
ln ingred:condiment:salt ayurveda:virya:heating ayurveda:virya
ln ingred:condiment:salt ayurveda:dosha:vata ayurveda:pacifies
ln ingred:condiment:salt ayurveda:dosha:pitta ayurveda:aggravates
ln ingred:condiment:salt ayurveda:dosha:kapha ayurveda:aggravates
ln ingred:nut:almond ayurveda:virya:heating ayurveda:virya
ln ingred:nut:almond ayurveda:dosha:vata ayurveda:pacifies
ln ingred:nut:almond ayurveda:dosha:kapha ayurveda:aggravates
ln ingred:seed:sesame ayurveda:virya:heating ayurveda:virya
ln ingred:seed:sesame ayurveda:dosha:vata ayurveda:pacifies
ln ingred:seed:sesame ayurveda:dosha:pitta ayurveda:aggravates
ln ingred:seed:sesame ayurveda:dosha:kapha ayurveda:aggravates
ln ingred:fruit:coconut ayurveda:virya:cooling ayurveda:virya
ln ingred:fruit:coconut ayurveda:dosha:pitta ayurveda:pacifies
ln ingred:fruit:coconut ayurveda:dosha:vata ayurveda:pacifies
ln ingred:fruit:coconut ayurveda:dosha:kapha ayurveda:aggravates
ln ingred:veg:spinach ayurveda:virya:cooling ayurveda:virya
ln ingred:veg:spinach ayurveda:dosha:pitta ayurveda:pacifies
ln ingred:veg:spinach ayurveda:dosha:vata ayurveda:aggravates
ln ingred:legume:mung_bean ayurveda:virya:cooling ayurveda:virya
ln ingred:legume:mung_bean ayurveda:dosha:pitta ayurveda:pacifies
ln ingred:legume:mung_bean ayurveda:dosha:kapha ayurveda:pacifies
