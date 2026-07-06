# Akasha ontology — namespace: sus
# atoms: 34

def "sus.circular_economy" "Circular economy and resource loops."
set.add name="ontology.urban_sustainability" id="sus.circular_economy"

def "sus.climate_action" "Climate mitigation and adaptation."
set.add name="ontology.urban_sustainability" id="sus.climate_action"

def "sus.economic" "Economic sustainability and green economy."
set.add name="ontology.urban_sustainability" id="sus.economic"

def "sus.environmental" "Environmental sustainability."
set.add name="ontology.urban_sustainability" id="sus.environmental"

def "sus.governance" "Sustainability governance and policy."
set.add name="ontology.urban_sustainability" id="sus.governance"

def "sus.green_infrastructure" "Green and blue urban infrastructure."
set.add name="ontology.urban_sustainability" id="sus.green_infrastructure"

def "sus.resilience" "Urban resilience and risk reduction."
set.add name="ontology.urban_sustainability" id="sus.resilience"

def "sus.social" "Social sustainability and well-being."
set.add name="ontology.urban_sustainability" id="sus.social"

def "sus:adaptation" "Climate adaptation strategies."
ln sus:adaptation sus.climate_action sys:is_a
ln sus:adaptation sus:disaster_resilience @strengthens
set.add name="ontology.urban_sustainability" id="sus:adaptation"

def "sus:air_quality" "Air quality management."
ln sus:air_quality sus.environmental sys:is_a
set.add name="ontology.urban_sustainability" id="sus:air_quality"

def "sus:bio_cycle" "Biological nutrient cycles."
ln sus:bio_cycle sus.circular_economy sys:is_a
set.add name="ontology.urban_sustainability" id="sus:bio_cycle"

def "sus:biodiversity" "Urban biodiversity and ecosystems."
ln sus:biodiversity sus.environmental sys:is_a
set.add name="ontology.urban_sustainability" id="sus:biodiversity"

def "sus:blue_infrastructure" "Water-based infrastructure (rivers, wetlands)."
ln sus:blue_infrastructure sus.green_infrastructure sys:is_a
set.add name="ontology.urban_sustainability" id="sus:blue_infrastructure"

def "sus:carbon_management" "Carbon management and sequestration."
ln sus:carbon_management sus.climate_action sys:is_a
set.add name="ontology.urban_sustainability" id="sus:carbon_management"

def "sus:community_engagement" "Community engagement and participation."
ln sus:community_engagement sus.social sys:is_a
set.add name="ontology.urban_sustainability" id="sus:community_engagement"

def "sus:continuity" "Continuity of urban functions."
ln sus:continuity sus.resilience sys:is_a
set.add name="ontology.urban_sustainability" id="sus:continuity"

def "sus:disaster_resilience" "Disaster resilience and risk reduction."
ln sus:disaster_resilience sus.resilience sys:is_a
set.add name="ontology.urban_sustainability" id="sus:disaster_resilience"

def "sus:education" "Education and capacity building."
ln sus:education sus.social sys:is_a
set.add name="ontology.urban_sustainability" id="sus:education"

def "sus:equity" "Equity and social inclusion."
ln sus:equity sus.social sys:is_a
set.add name="ontology.urban_sustainability" id="sus:equity"

def "sus:green_economy" "Green economy and sustainable industries."
ln sus:green_economy sus.economic sys:is_a
set.add name="ontology.urban_sustainability" id="sus:green_economy"

def "sus:green_jobs" "Green jobs and workforce transition."
ln sus:green_jobs sus.economic sys:is_a
set.add name="ontology.urban_sustainability" id="sus:green_jobs"

def "sus:green_roofs" "Green roofs and walls."
ln sus:green_roofs sus.green_infrastructure sys:is_a
set.add name="ontology.urban_sustainability" id="sus:green_roofs"

def "sus:mitigation" "Climate mitigation (GHG reduction)."
ln sus:mitigation sus.climate_action sys:is_a
ln sus:mitigation sus:carbon_management @reduces
set.add name="ontology.urban_sustainability" id="sus:mitigation"

def "sus:policy" "Urban sustainability policy."
ln sus:policy sus.governance sys:is_a
set.add name="ontology.urban_sustainability" id="sus:policy"

def "sus:public_health" "Public health and well-being."
ln sus:public_health sus.social sys:is_a
set.add name="ontology.urban_sustainability" id="sus:public_health"

def "sus:recycling" "Recycling systems."
ln sus:recycling sus.circular_economy sys:is_a
ln sus:recycling sus:resource_efficiency @supports
set.add name="ontology.urban_sustainability" id="sus:recycling"

def "sus:redundancy" "Redundancy and backup systems."
ln sus:redundancy sus.resilience sys:is_a
set.add name="ontology.urban_sustainability" id="sus:redundancy"

def "sus:resource_efficiency" "Resource efficiency and productivity."
ln sus:resource_efficiency sus.economic sys:is_a
set.add name="ontology.urban_sustainability" id="sus:resource_efficiency"

def "sus:reuse" "Reuse and upcycling."
ln sus:reuse sus.circular_economy sys:is_a
set.add name="ontology.urban_sustainability" id="sus:reuse"

def "sus:soil_health" "Soil health and contamination control."
ln sus:soil_health sus.environmental sys:is_a
set.add name="ontology.urban_sustainability" id="sus:soil_health"

def "sus:standards" "Sustainability standards and certifications."
ln sus:standards sus.governance sys:is_a
set.add name="ontology.urban_sustainability" id="sus:standards"

def "sus:urban_parks" "Urban parks and green spaces."
ln sus:urban_parks sus.green_infrastructure sys:is_a
ln sus:urban_parks sus:biodiversity @enhances
set.add name="ontology.urban_sustainability" id="sus:urban_parks"

def "sus:urban_planning" "Sustainable urban planning."
ln sus:urban_planning sus.governance sys:is_a
ln sus:urban_planning sus.green_infrastructure @integrates_with
set.add name="ontology.urban_sustainability" id="sus:urban_planning"

def "sus:water_quality" "Water quality and watershed protection."
ln sus:water_quality sus.environmental sys:is_a
set.add name="ontology.urban_sustainability" id="sus:water_quality"
