# Akasha ontology — future agriculture & livestock + food sustainability.
# Bridging the food & farming world with agritech (ag:), supply-chain (asc:),
# seasonality, fishing regulation and diet:. Base pack.

def "futureag" "The future of farming, aquaculture and livestock."
def "futureag:vertical_farming" "Stacked indoor crop production in controlled environments (垂直農業)."
ln futureag:vertical_farming futureag thesaurus:related
ln futureag:vertical_farming occupation:farmer thesaurus:related
def "futureag:hydroponics" "Growing plants in nutrient solution without soil."
ln futureag:hydroponics futureag thesaurus:related
ln futureag:hydroponics ag:drip_irrigation thesaurus:related
ln futureag:hydroponics futureag:vertical_farming thesaurus:related
def "futureag:aeroponics" "Growing plants with roots misted in air."
ln futureag:aeroponics futureag thesaurus:related
def "futureag:aquaponics" "Coupling fish farming and hydroponics in one nutrient loop."
ln futureag:aquaponics futureag thesaurus:related
def "futureag:controlled_environment_agriculture" "Fully managed light, climate and nutrients for year-round crops."
ln futureag:controlled_environment_agriculture futureag thesaurus:related
ln futureag:controlled_environment_agriculture ag:crop_health thesaurus:related
def "futureag:precision_agriculture" "Data- and sensor-driven farming that varies inputs by the metre."
ln futureag:precision_agriculture futureag thesaurus:related
ln futureag:precision_agriculture ag:autonomous_tractor thesaurus:related
ln futureag:precision_agriculture ag:drone_monitoring thesaurus:related
ln futureag:precision_agriculture ag:crop_health thesaurus:related
ln futureag:precision_agriculture asc:barcode_qr thesaurus:related
def "futureag:urban_agriculture" "Growing food within cities — rooftops, plots, indoor farms."
ln futureag:urban_agriculture futureag thesaurus:related
ln futureag:urban_agriculture home:garden thesaurus:related
ln futureag:urban_agriculture concept:community thesaurus:related
def "futureag:gene_editing_crops" "CRISPR-edited crops for yield, nutrition or resilience."
ln futureag:gene_editing_crops futureag thesaurus:related
ln futureag:gene_editing_crops futureag:gmo thesaurus:related
def "futureag:gmo" "Genetically modified organisms in the food supply."
ln futureag:gmo futureag thesaurus:related
def "futureag:drought_resistant_crop" "Varieties bred or engineered to withstand water stress."
ln futureag:drought_resistant_crop futureag thesaurus:related
def "futureag:biofortification" "Breeding crops to be richer in vitamins and minerals."
ln futureag:biofortification futureag thesaurus:related
def "futureag:regenerative_agriculture" "Farming that rebuilds soil health and biodiversity (環境再生型農業)."
ln futureag:regenerative_agriculture futureag thesaurus:related
ln futureag:regenerative_agriculture foodsustain:soil_health thesaurus:related
def "futureag:agroecology" "Applying ecological principles to farming systems."
ln futureag:agroecology futureag thesaurus:related
ln futureag:agroecology foodsustain:biodiversity thesaurus:related
def "futureag:no_till_farming" "Avoiding ploughing to protect soil structure and carbon."
ln futureag:no_till_farming futureag thesaurus:related
def "futureag:integrated_pest_management" "Combining biological, cultural and minimal-chemical pest control."
ln futureag:integrated_pest_management futureag thesaurus:related
def "futureag:cellular_agriculture" "Producing meat, dairy or egg proteins from cell/microbe culture."
ln futureag:cellular_agriculture futureag thesaurus:related
ln futureag:cellular_agriculture futurefood:cultured_meat thesaurus:related
def "futureag:aquaculture" "Farming fish, shellfish and seaweed (養殖)."
ln futureag:aquaculture futureag thesaurus:related
ln futureag:aquaculture occupation:fisherman thesaurus:related
ln futureag:aquaculture regulation:fishing_ban thesaurus:related
def "futureag:insect_farming" "Rearing insects for food and feed at scale."
ln futureag:insect_farming futureag thesaurus:related
def "futureag:alternative_feed" "Novel animal feeds (insect meal, algae) reducing land and grain use."
ln futureag:alternative_feed futureag thesaurus:related
# ── food sustainability ──
def "foodsustain" "Sustainability of the food system — ecological, social, economic."
def "foodsustain:food_sustainability" "Meeting food needs without degrading the systems future generations depend on."
ln foodsustain:food_sustainability foodsustain thesaurus:related
def "foodsustain:sustainable_diet" "A diet low in impact and rich in health — plant-forward, diverse, seasonal."
ln foodsustain:sustainable_diet foodsustain thesaurus:related
ln foodsustain:sustainable_diet diet:mediterranean thesaurus:related
ln foodsustain:sustainable_diet diet:plant_based thesaurus:related
def "foodsustain:carbon_footprint_food" "The greenhouse-gas emissions embodied in a food."
ln foodsustain:carbon_footprint_food foodsustain thesaurus:related
ln foodsustain:carbon_footprint_food asc:carbon_footprint thesaurus:related
def "foodsustain:food_miles" "The distance food travels from farm to plate."
ln foodsustain:food_miles foodsustain thesaurus:related
ln foodsustain:food_miles asc:carbon_footprint thesaurus:related
def "foodsustain:life_cycle_assessment" "Measuring a food's impacts across its whole life cycle."
ln foodsustain:life_cycle_assessment foodsustain thesaurus:related
def "foodsustain:circular_food_economy" "Designing out waste — by-products and nutrients cycled back in."
ln foodsustain:circular_food_economy foodsustain thesaurus:related
def "foodsustain:food_waste" "Edible food discarded across the chain (食品ロス)."
ln foodsustain:food_waste foodsustain thesaurus:related
ln foodsustain:food_waste foodsec:post_harvest_loss thesaurus:related
ln foodsustain:food_waste gov:sanitation:recycling thesaurus:related
def "foodsustain:food_upcycling" "Turning by-products and surplus into new food."
ln foodsustain:food_upcycling foodsustain thesaurus:related
def "foodsustain:planetary_boundaries" "The ecological limits within which food systems must stay."
ln foodsustain:planetary_boundaries foodsustain thesaurus:related
def "foodsustain:eat_lancet" "The planetary-health reference diet balancing nutrition and sustainability."
ln foodsustain:eat_lancet foodsustain thesaurus:related
ln foodsustain:eat_lancet nutrisci:nutritional_epidemiology thesaurus:related
def "foodsustain:sustainable_seafood" "Seafood caught or farmed within stock and habitat limits."
ln foodsustain:sustainable_seafood foodsustain thesaurus:related
ln foodsustain:sustainable_seafood regulation:fishing_ban thesaurus:related
ln foodsustain:sustainable_seafood regulation:closed_season thesaurus:related
ln foodsustain:sustainable_seafood occupation:fisherman thesaurus:related
def "foodsustain:fair_trade" "Trade ensuring fair prices and conditions for producers."
ln foodsustain:fair_trade foodsustain thesaurus:related
ln foodsustain:fair_trade foodstud:spice_trade thesaurus:related
def "foodsustain:organic_farming" "Farming without synthetic pesticides or fertilisers (有機農業)."
ln foodsustain:organic_farming foodsustain thesaurus:related
ln foodsustain:organic_farming asc:certification thesaurus:related
def "foodsustain:biodiversity" "The variety of crops, breeds and ecosystems underpinning resilient food."
ln foodsustain:biodiversity foodsustain thesaurus:related
ln foodsustain:biodiversity futureag:agroecology thesaurus:related
def "foodsustain:soil_health" "The living fertility of soil, foundation of sustainable farming."
ln foodsustain:soil_health foodsustain thesaurus:related
ln foodsustain:soil_health futureag:regenerative_agriculture thesaurus:related
def "foodsustain:water_footprint" "The freshwater consumed to produce a food."
ln foodsustain:water_footprint foodsustain thesaurus:related
def "foodsustain:seasonal_eating" "Eating produce in its natural season, lowering impact (旬の食)."
ln foodsustain:seasonal_eating foodsustain thesaurus:related
ln foodsustain:seasonal_eating season:summer thesaurus:related
ln foodsustain:seasonal_eating cuisine:japanese thesaurus:related
def "foodsustain:local_food" "Food produced near where it is eaten, shortening the chain."
ln foodsustain:local_food foodsustain thesaurus:related
ln foodsustain:local_food concept:neighborhood thesaurus:related
ln foodsustain:local_food cuisine:italian thesaurus:related
# seasonal eating ties into the season / harvest / closed-season work
ln foodsustain:seasonal_eating season:autumn thesaurus:related
ln foodsustain:seasonal_eating season:winter thesaurus:related
ln foodsustain:sustainable_seafood regulation:hunting_ban thesaurus:related
