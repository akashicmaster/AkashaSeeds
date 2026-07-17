# Akasha ontology — food frontier: space food, future food, food security.
# Bridging the food domain (ingred:/diet:/nutrisci:) with the space, tech and
# humanitarian edges. Base pack.

def "spacefood" "Food engineered for spaceflight and off-world living."
def "spacefood:space_food" "Food formulated, processed and packaged for spaceflight (宇宙食)."
ln spacefood:space_food spacefood thesaurus:related
ln spacefood:space_food astro:solar_system thesaurus:related
ln spacefood:space_food technique:food_drying thesaurus:related
def "spacefood:freeze_dried_food" "Food dehydrated by sublimation for light, stable, rehydratable rations."
ln spacefood:freeze_dried_food spacefood thesaurus:related
ln spacefood:freeze_dried_food technique:food_drying thesaurus:related
ln spacefood:freeze_dried_food technique:snap_freezing thesaurus:related
def "spacefood:rehydratable_food" "Dried food restored with water in orbit."
ln spacefood:rehydratable_food spacefood thesaurus:related
def "spacefood:thermostabilized_food" "Heat-processed shelf-stable food (retort pouches) for missions."
ln spacefood:thermostabilized_food spacefood thesaurus:related
def "spacefood:microgravity_eating" "Eating without gravity — crumbs, fluids and aromas all behave differently."
ln spacefood:microgravity_eating spacefood thesaurus:related
def "spacefood:bioregenerative_life_support" "A closed system where plants/algae recycle air, water and food for a crew."
ln spacefood:bioregenerative_life_support spacefood thesaurus:related
ln spacefood:bioregenerative_life_support foodsustain:circular_food_economy thesaurus:related
def "spacefood:space_agriculture" "Growing crops in orbit or on other worlds (宇宙農業)."
ln spacefood:space_agriculture spacefood thesaurus:related
ln spacefood:space_agriculture astro:planet thesaurus:related
ln spacefood:space_agriculture futureag:hydroponics thesaurus:related
def "spacefood:space_hydroponics" "Soilless cultivation adapted to microgravity."
ln spacefood:space_hydroponics spacefood thesaurus:related
def "spacefood:mars_food" "Food strategy for long-duration Mars missions and settlement."
ln spacefood:mars_food spacefood thesaurus:related
ln spacefood:mars_food astro:planet thesaurus:related
def "spacefood:spirulina" "A protein-rich cyanobacterium proposed for space and sustainable diets."
ln spacefood:spirulina spacefood thesaurus:related
ln spacefood:spirulina futurefood:algae_food thesaurus:related
ln spacefood:spirulina nutrisci:functional_food thesaurus:related
# ── future food / alternative protein (未来の食卓) ──
def "futurefood" "Novel foods and proteins reshaping the future table."
def "futurefood:alternative_protein" "Protein from non-conventional sources — plants, cells, insects, microbes."
ln futurefood:alternative_protein futurefood thesaurus:related
def "futurefood:cultured_meat" "Meat grown from animal cells without slaughter (培養肉)."
ln futurefood:cultured_meat futurefood thesaurus:related
ln futurefood:cultured_meat occupation:rancher thesaurus:related
ln futurefood:cultured_meat foodsci:food_microbiology thesaurus:related
def "futurefood:cellular_agriculture" "Producing animal products from cell cultures rather than animals."
ln futurefood:cellular_agriculture futurefood thesaurus:related
def "futurefood:plant_based_meat" "Plant-protein products engineered to mimic meat."
ln futurefood:plant_based_meat futurefood thesaurus:related
ln futurefood:plant_based_meat diet:plant_based thesaurus:related
ln futurefood:plant_based_meat diet:vegan thesaurus:related
def "futurefood:insect_food" "Edible insects as protein — entomophagy (昆虫食)."
ln futurefood:insect_food futurefood thesaurus:related
ln futurefood:insect_food foodstud:food_taboo thesaurus:related
def "futurefood:mycoprotein" "Fungal protein grown by fermentation (e.g. Quorn)."
ln futurefood:mycoprotein futurefood thesaurus:related
ln futurefood:mycoprotein foodsci:fermentation_science thesaurus:related
def "futurefood:algae_food" "Microalgae and seaweed as scalable food (藻類食)."
ln futurefood:algae_food futurefood thesaurus:related
ln futurefood:algae_food spacefood:spirulina thesaurus:related
def "futurefood:precision_fermentation" "Engineering microbes to brew specific proteins (e.g. dairy proteins without cows)."
ln futurefood:precision_fermentation futurefood thesaurus:related
ln futurefood:precision_fermentation foodsci:fermentation_science thesaurus:related
ln futurefood:precision_fermentation nutrisci:functional_food thesaurus:related
def "futurefood:3d_printed_food" "Layer-by-layer fabrication of food from pastes and inks."
ln futurefood:3d_printed_food futurefood thesaurus:related
def "futurefood:meal_replacement" "Nutritionally complete engineered meals in liquid or bar form."
ln futurefood:meal_replacement futurefood thesaurus:related
ln futurefood:meal_replacement nutrisci:personalized_nutrition thesaurus:related
def "futurefood:novel_food" "A food without significant prior consumption history, needing safety approval."
ln futurefood:novel_food futurefood thesaurus:related
ln futurefood:novel_food foodsafe:haccp thesaurus:related
def "futurefood:food_tech" "Technology-driven innovation across the food system."
ln futurefood:food_tech futurefood thesaurus:related
# ── food security & crisis (食糧危機) ──
def "foodsec" "Food security — reliable access to sufficient, safe, nutritious food."
def "foodsec:food_security" "When all people at all times have access to enough safe, nutritious food (食料安全保障)."
ln foodsec:food_security foodsec thesaurus:related
def "foodsec:food_insecurity" "Uncertain or inadequate access to food."
ln foodsec:food_insecurity foodsec thesaurus:related
def "foodsec:famine" "An extreme, widespread scarcity of food causing death (飢饉)."
ln foodsec:famine foodsec thesaurus:related
def "foodsec:hunger" "Chronic insufficiency of food energy."
ln foodsec:hunger foodsec thesaurus:related
def "foodsec:malnutrition" "Deficiency, excess or imbalance of nutrients — under- and over-nutrition."
ln foodsec:malnutrition foodsec thesaurus:related
ln foodsec:malnutrition nutrisci:bioavailability thesaurus:related
def "foodsec:food_desert" "An area with poor access to affordable fresh food."
ln foodsec:food_desert foodsec thesaurus:related
ln foodsec:food_desert place:supermarket thesaurus:related
def "foodsec:food_sovereignty" "A people's right to define their own food and agriculture systems."
ln foodsec:food_sovereignty foodsec thesaurus:related
def "foodsec:food_aid" "Provision of food to populations in need."
ln foodsec:food_aid foodsec thesaurus:related
ln foodsec:food_aid gov:function:welfare thesaurus:related
ln foodsec:food_aid gov:benefit:public_assistance thesaurus:related
def "foodsec:food_bank" "A charity distributing donated food to those in need."
ln foodsec:food_bank foodsec thesaurus:related
ln foodsec:food_bank gov:benefit:public_assistance thesaurus:related
ln foodsec:food_bank group:neighborhood_association thesaurus:related
def "foodsec:price_volatility" "Sharp swings in food prices threatening access."
ln foodsec:price_volatility foodsec thesaurus:related
def "foodsec:supply_chain_disruption" "Breaks in the chain from farm to table (war, pandemic, climate)."
ln foodsec:supply_chain_disruption foodsec thesaurus:related
ln foodsec:supply_chain_disruption asc:blockchain_trace thesaurus:related
def "foodsec:crop_failure" "Loss of a harvest to drought, flood, pest or disease."
ln foodsec:crop_failure foodsec thesaurus:related
ln foodsec:crop_failure futureag:drought_resistant_crop thesaurus:related
def "foodsec:post_harvest_loss" "Food lost between harvest and consumption in storage and transport."
ln foodsec:post_harvest_loss foodsec thesaurus:related
ln foodsec:post_harvest_loss foodsustain:food_waste thesaurus:related
def "foodsec:global_food_system" "The interconnected worldwide web of food production, trade and consumption."
ln foodsec:global_food_system foodsec thesaurus:related
ln foodsec:global_food_system admin:country thesaurus:related
