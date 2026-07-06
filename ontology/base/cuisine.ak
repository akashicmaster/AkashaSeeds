# Akasha ontology — namespace: cuisine
# atoms: 37

def "cuisine:bistro" "Casual, robust, and comforting French home-style or tavern cooking."
ln cuisine:bistro cuisine:french sys:part_of

def "cuisine:cajun" "Rustic, spicy cuisine of the Acadians in Louisiana, emphasizing local swamp and bayou ingredients."
ln cuisine:cajun dna:taste:hot calc:associated_with

def "cuisine:cantonese" "Subtle and fresh cooking from Guangdong, famous for dim sum and roasting."
ln cuisine:cantonese cuisine:chinese sys:part_of

def "cuisine:chifa" "Peruvian-Chinese fusion cuisine, adapting Cantonese elements to Andean and Amazonian ingredients."
ln cuisine:chifa cuisine:peruvian @fuses_with
ln cuisine:chifa cuisine:cantonese @fuses_with

def "cuisine:chinese" "The overarching culinary traditions of China."

def "cuisine:creole" "Sophisticated, cosmopolitan cuisine of New Orleans, blending French, Spanish, African, and Native influences."
ln cuisine:creole cuisine:french @fuses_with

def "cuisine:french" "The overarching culinary traditions of France, foundational to Western gastronomy."

def "cuisine:haute_cuisine" "High-level French gastronomy, characterized by meticulous preparation and presentation."
ln cuisine:haute_cuisine cuisine:french sys:part_of

def "cuisine:huaiyang" "Eastern Chinese cuisine known for precise knife skills, slightly sweet flavors, and braising."
ln cuisine:huaiyang cuisine:chinese sys:part_of

def "cuisine:iberian" "Cooking traditions of Spain and Portugal, marked by cured meats, seafood, paprika, and tapas culture."

def "cuisine:indian" "Diverse culinary traditions of the Indian subcontinent, unified by complex spice usage."

def "cuisine:italian" "The overarching culinary traditions of Italy, deeply regional and ingredient-focused."

def "cuisine:kaiseki" "Traditional multi-course Japanese dinner, highly refined and seasonal."
ln cuisine:kaiseki cuisine:washoku sys:part_of

def "cuisine:kyodo_ryori" "Japanese local/regional specialties reflecting unique geography and history."

def "cuisine:levantine" "Eastern Mediterranean cuisine covering Lebanon, Syria, and Israel; rich in mezze, olive oil, and legumes."

def "cuisine:maghrebi" "North African cooking (Morocco, Algeria, Tunisia) famous for tagines, couscous, and ras el hanout."

def "cuisine:mexican" "Overarching culinary tradition of Mexico, rich in corn, beans, and chilies."

def "cuisine:mughlai" "North Indian cuisine influenced by the Mughal Empire, featuring rich, creamy, and heavily spiced curries."
ln cuisine:mughlai cuisine:indian sys:part_of

def "cuisine:neapolitan" "Cuisine of Naples, famous for pizza, simple tomato sauces, and coastal seafood."
ln cuisine:neapolitan cuisine:italian sys:part_of

def "cuisine:nikkei" "Peruvian-Japanese fusion cuisine, combining Peruvian ingredients with Japanese techniques."
ln cuisine:nikkei cuisine:peruvian @fuses_with
ln cuisine:nikkei cuisine:washoku @fuses_with

def "cuisine:nordic" "New Nordic Cuisine, a movement emphasizing purity, simplicity, seasonal foraging, and local Scandinavian environments."

def "cuisine:nouvelle_cuisine" "Modern French style emphasizing lighter, more delicate dishes and plated presentation."
ln cuisine:nouvelle_cuisine cuisine:french sys:part_of

def "cuisine:nyonya" "Also known as Peranakan cuisine; a hybrid of Chinese ingredients with Malay/Indonesian spices and techniques."
ln cuisine:nyonya cuisine:chinese @fuses_with

def "cuisine:oaxacan" "Regional Mexican cuisine famous for complex moles and artisanal mezcal."
ln cuisine:oaxacan cuisine:mexican sys:part_of

def "cuisine:okinawan" "Regional cuisine of Okinawa, heavy in pork, seaweed, and bitter melon."

def "cuisine:peruvian" "Culinary tradition of Peru, known for massive biodiversity and multicultural influences."

def "cuisine:provencal" "Regional cooking of Provence, relying heavily on olive oil, garlic, tomatoes, and herbs."
ln cuisine:provencal cuisine:french sys:part_of

def "cuisine:shandong" "Northern Chinese coastal cuisine, known for light aromas, seafood, and soups."
ln cuisine:shandong cuisine:chinese sys:part_of

def "cuisine:shojin" "Japanese Buddhist vegetarian cuisine, focusing on vegetables, tofu, and mindful preparation."
ln cuisine:shojin cuisine:washoku sys:part_of
ln cuisine:shojin dna:taste:umami calc:associated_with

def "cuisine:sichuan" "Bold, pungent, and spicy cooking from Sichuan province, famous for mala flavor."
ln cuisine:sichuan cuisine:chinese sys:part_of
ln cuisine:sichuan dna:taste:hot calc:associated_with
ln cuisine:sichuan dna:smell:pungent calc:associated_with

def "cuisine:sicilian" "Cuisine of Sicily, featuring Mediterranean cross-cultural influences, citrus, and sweet-sour flavors."
ln cuisine:sicilian cuisine:italian sys:part_of
ln cuisine:sicilian dna:taste:sour calc:associated_with
ln cuisine:sicilian dna:taste:sweet calc:associated_with

def "cuisine:soul_food" "Traditional African American cuisine originating in the Southern US, emphasizing comfort and rich flavors."

def "cuisine:thai" "Aromatic and intensely flavored cuisine balancing sweet, sour, spicy, and salty profiles."
ln cuisine:thai dna:taste:hot calc:associated_with
ln cuisine:thai dna:taste:sour calc:associated_with
ln cuisine:thai dna:taste:sweet calc:associated_with
ln cuisine:thai dna:taste:salty calc:associated_with

def "cuisine:tuscan" "Rustic cooking from Tuscany, characterized by beans, bread, grilled meats, and olive oil."
ln cuisine:tuscan cuisine:italian sys:part_of

def "cuisine:vietnamese" "Fresh and vibrant cuisine characterized by herbs, clear broths, and fish sauce."

def "cuisine:washoku" "Traditional Japanese cuisine, emphasizing seasonal ingredients and balance."
ln cuisine:washoku dna:taste:umami calc:associated_with

def "cuisine:yoshoku" "Western-influenced cooking style in Japan, featuring dishes like omurice and croquettes."
ln cuisine:yoshoku cuisine:washoku @fuses_with
ln cuisine:yoshoku cuisine:french @fuses_with
