# Akasha ontology — ecology & environmental science/engineering.
# Nearly absent before. Bridged to bio:/geo:/weather:/ce:/chemeng:/infra:/
# foodsustain:/resource:/law:environmental_law. Base pack.

def "ecol" "Ecology — the study of organisms and their environment (生態学)."
def "ecol:ecosystem" "A community of organisms and their physical environment as one system (生態系)."
ln ecol:ecosystem ecol thesaurus:related
ln ecol:ecosystem resource:biological_resource thesaurus:related
def "ecol:biome" "A major regional ecosystem type — forest, desert, tundra (バイオーム)."
ln ecol:biome ecol thesaurus:related
def "ecol:habitat" "The place an organism lives."
ln ecol:habitat ecol thesaurus:related
def "ecol:niche" "The role and conditions an organism occupies."
ln ecol:niche ecol thesaurus:related
def "ecol:food_chain" "A linear feeding sequence from producer to top consumer (食物連鎖)."
ln ecol:food_chain ecol thesaurus:related
def "ecol:food_web" "The interconnected feeding relations of a community (食物網)."
ln ecol:food_web ecol thesaurus:related
ln ecol:food_web dh:network thesaurus:related
ln ecol:food_web sys:network thesaurus:related
def "ecol:trophic_level" "A feeding position — producer, herbivore, carnivore, decomposer (栄養段階)."
ln ecol:trophic_level ecol thesaurus:related
def "ecol:producer" "An organism making its own food (plants, algae)."
ln ecol:producer ecol thesaurus:related
ln ecol:producer life:photosynthesis thesaurus:related
def "ecol:decomposer" "An organism breaking down dead matter."
ln ecol:decomposer ecol thesaurus:related
ln ecol:decomposer foodsci:food_microbiology thesaurus:related
def "ecol:biodiversity" "The variety of life at gene, species and ecosystem levels (生物多様性)."
ln ecol:biodiversity ecol thesaurus:related
ln ecol:biodiversity foodsustain:biodiversity thesaurus:related
ln ecol:biodiversity sus:biodiversity thesaurus:related
def "ecol:keystone_species" "A species whose removal drastically reshapes its ecosystem."
ln ecol:keystone_species ecol thesaurus:related
ln ecol:keystone_species regulation:fishing_ban thesaurus:related
def "ecol:carrying_capacity" "The maximum population an environment can sustain (環境収容力)."
ln ecol:carrying_capacity ecol thesaurus:related
def "ecol:symbiosis" "A close long-term interaction between species (共生)."
ln ecol:symbiosis ecol thesaurus:related
def "ecol:ecological_succession" "The change of a community over time toward stability (遷移)."
ln ecol:ecological_succession ecol thesaurus:related
def "ecol:nutrient_cycle" "The circulation of nutrients (carbon, nitrogen) through the ecosystem (物質循環)."
ln ecol:nutrient_cycle ecol thesaurus:related
def "ecol:carbon_cycle" "The movement of carbon through air, life, ocean and rock (炭素循環)."
ln ecol:carbon_cycle ecol thesaurus:related
ln ecol:carbon_cycle ecol:nutrient_cycle thesaurus:related
ln ecol:carbon_cycle enveng:greenhouse_gas thesaurus:related
def "ecol:ecosystem_service" "The benefits ecosystems provide people — pollination, clean water (生態系サービス)."
ln ecol:ecosystem_service ecol thesaurus:related
ln ecol:ecosystem_service foodsustain:sustainable_diet thesaurus:related
ln ecol:ecosystem_service futureag:agroecology thesaurus:related
# ── environmental science & engineering ──
def "enveng" "Environmental science & engineering — protecting and remediating the environment (環境工学)."
def "enveng:environmental_science" "The interdisciplinary study of the environment and human impact (環境科学)."
ln enveng:environmental_science enveng thesaurus:related
def "enveng:pollution" "Harmful contamination of air, water or soil (汚染)."
ln enveng:pollution enveng thesaurus:related
ln enveng:pollution econ:externality thesaurus:related
ln enveng:pollution law:branch:environmental_law thesaurus:related
def "enveng:air_pollution" "Contamination of the atmosphere by gases and particulates (大気汚染)."
ln enveng:air_pollution enveng thesaurus:related
def "enveng:water_pollution" "Contamination of water bodies (水質汚濁)."
ln enveng:water_pollution enveng thesaurus:related
def "enveng:soil_contamination" "Toxic substances in soil (土壌汚染)."
ln enveng:soil_contamination enveng thesaurus:related
def "enveng:water_treatment" "Making water safe to drink (浄水)."
ln enveng:water_treatment enveng thesaurus:related
ln enveng:water_treatment infra:water_supply thesaurus:related
ln enveng:water_treatment chemeng:absorption thesaurus:related
def "enveng:wastewater_treatment" "Cleaning sewage before release (下水処理)."
ln enveng:wastewater_treatment enveng thesaurus:related
ln enveng:wastewater_treatment infra:sewerage thesaurus:related
ln enveng:wastewater_treatment ce:water_quality thesaurus:related
ln enveng:wastewater_treatment chemeng:filtration thesaurus:related
def "enveng:waste_management" "Collecting, treating and disposing of waste (廃棄物管理)."
ln enveng:waste_management enveng thesaurus:related
ln enveng:waste_management gov:sanitation:waste_disposal thesaurus:related
ln enveng:waste_management ce:waste_management thesaurus:related
ln enveng:waste_management resource:recycling thesaurus:related
def "enveng:hazardous_waste" "Waste dangerous to health or environment (有害廃棄物)."
ln enveng:hazardous_waste enveng thesaurus:related
def "enveng:remediation" "Cleaning up contaminated sites (浄化)."
ln enveng:remediation enveng thesaurus:related
def "enveng:bioremediation" "Using microbes or plants to clean pollution (生物学的浄化)."
ln enveng:bioremediation enveng thesaurus:related
ln enveng:bioremediation foodsci:food_microbiology thesaurus:related
def "enveng:air_quality" "The cleanliness of the air we breathe."
ln enveng:air_quality enveng thesaurus:related
ln enveng:air_quality ce:air_quality thesaurus:related
ln enveng:air_quality weather:cloud thesaurus:related
def "enveng:environmental_impact_assessment" "Evaluating a project's environmental effects before approval (環境アセスメント)."
ln enveng:environmental_impact_assessment enveng thesaurus:related
ln enveng:environmental_impact_assessment civ:impact_assessment thesaurus:related
ln enveng:environmental_impact_assessment law:branch:environmental_law thesaurus:related
def "enveng:greenhouse_gas" "A gas trapping heat in the atmosphere — CO2, methane (温室効果ガス)."
ln enveng:greenhouse_gas enveng thesaurus:related
ln enveng:greenhouse_gas foodsustain:carbon_footprint_food thesaurus:related
ln enveng:greenhouse_gas ecol:carbon_cycle thesaurus:related
ln enveng:greenhouse_gas weather:climate thesaurus:related
def "enveng:climate_change" "Long-term shifts in climate driven largely by greenhouse gases (気候変動)."
ln enveng:climate_change enveng thesaurus:related
ln enveng:climate_change weather:climate thesaurus:related
ln enveng:climate_change foodsustain:food_sustainability thesaurus:related
ln enveng:climate_change econ:externality thesaurus:related
def "enveng:carbon_capture" "Capturing CO2 to curb emissions (炭素回収)."
ln enveng:carbon_capture enveng thesaurus:related
ln enveng:carbon_capture energy:carbon_management thesaurus:related
ln enveng:carbon_capture chemeng:absorption thesaurus:related
def "enveng:desalination" "Removing salt to make seawater potable (淡水化)."
ln enveng:desalination enveng thesaurus:related
ln enveng:desalination chemeng:distillation thesaurus:related
ln enveng:desalination resource:water_resource thesaurus:related
