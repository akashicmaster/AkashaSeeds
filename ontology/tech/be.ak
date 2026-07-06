# Akasha ontology — namespace: be
# atoms: 36

def "be.building_physics" "Building physics and performance."
set.add name="ontology.building_engineering" id="be.building_physics"

def "be.construction" "Construction engineering and methods."
set.add name="ontology.building_engineering" id="be.construction"

def "be.materials" "Building materials and material science."
set.add name="ontology.building_engineering" id="be.materials"

def "be.mep" "Mechanical, Electrical, and Plumbing systems."
set.add name="ontology.building_engineering" id="be.mep"

def "be.safety" "Building safety and codes."
set.add name="ontology.building_engineering" id="be.safety"

def "be.structural" "Structural engineering for buildings."
set.add name="ontology.building_engineering" id="be.structural"

def "be.sustainability" "Sustainable building design."
set.add name="ontology.building_engineering" id="be.sustainability"

def "be.urban_integration" "Integration with urban systems and infrastructure."
set.add name="ontology.building_engineering" id="be.urban_integration"

def "be:acoustics" "Building acoustics."
ln be:acoustics be.building_physics sys:is_a
set.add name="ontology.building_engineering" id="be:acoustics"

def "be:airflow" "Airflow and ventilation physics."
ln be:airflow be.building_physics sys:is_a
set.add name="ontology.building_engineering" id="be:airflow"

def "be:building_codes" "Building codes and regulations."
ln be:building_codes be.safety sys:is_a
set.add name="ontology.building_engineering" id="be:building_codes"

def "be:concrete" "Concrete materials and mix design."
ln be:concrete be.materials sys:is_a
set.add name="ontology.building_engineering" id="be:concrete"

def "be:construction_methods" "Construction methods and sequencing."
ln be:construction_methods be.construction sys:is_a
set.add name="ontology.building_engineering" id="be:construction_methods"

def "be:daylighting" "Daylighting and visual comfort."
ln be:daylighting be.building_physics sys:is_a
set.add name="ontology.building_engineering" id="be:daylighting"

def "be:egress_design" "Egress and evacuation design."
ln be:egress_design be.safety sys:is_a
set.add name="ontology.building_engineering" id="be:egress_design"

def "be:electrical_system" "Electrical systems and power distribution."
ln be:electrical_system be.mep sys:is_a
set.add name="ontology.building_engineering" id="be:electrical_system"

def "be:energy_efficiency" "Energy-efficient building design."
ln be:energy_efficiency be.sustainability sys:is_a
ln be:energy_efficiency be:electrical_system @reduces_load
set.add name="ontology.building_engineering" id="be:energy_efficiency"

def "be:fire_code" "Fire safety codes."
ln be:fire_code be.safety sys:is_a
set.add name="ontology.building_engineering" id="be:fire_code"

def "be:fire_protection" "Fire protection systems."
ln be:fire_protection be.mep sys:is_a
set.add name="ontology.building_engineering" id="be:fire_protection"

def "be:green_certification" "Green building certifications (LEED, BREEAM)."
ln be:green_certification be.sustainability sys:is_a
set.add name="ontology.building_engineering" id="be:green_certification"

def "be:green_materials" "Low-carbon and sustainable materials."
ln be:green_materials be.sustainability sys:is_a
set.add name="ontology.building_engineering" id="be:green_materials"

def "be:hvac" "Heating, ventilation, and air conditioning."
ln be:hvac be.mep sys:is_a
ln be:hvac be:thermal_performance @influences
set.add name="ontology.building_engineering" id="be:hvac"

def "be:infrastructure_connection" "Connection to urban infrastructure (water, power, comms)."
ln be:infrastructure_connection be.urban_integration sys:is_a
set.add name="ontology.building_engineering" id="be:infrastructure_connection"

def "be:insulation" "Thermal and acoustic insulation materials."
ln be:insulation be.materials sys:is_a
set.add name="ontology.building_engineering" id="be:insulation"

def "be:mobility_access" "Access to transportation systems."
ln be:mobility_access be.urban_integration sys:is_a
set.add name="ontology.building_engineering" id="be:mobility_access"

def "be:plumbing" "Plumbing and water systems."
ln be:plumbing be.mep sys:is_a
set.add name="ontology.building_engineering" id="be:plumbing"

def "be:prefabrication" "Prefabrication and modular construction."
ln be:prefabrication be.construction sys:is_a
ln be:prefabrication be:green_materials @supports
set.add name="ontology.building_engineering" id="be:prefabrication"

def "be:reinforced_concrete" "Reinforced concrete structures."
ln be:reinforced_concrete be.structural sys:is_a
set.add name="ontology.building_engineering" id="be:reinforced_concrete"

def "be:seismic_design" "Seismic design and earthquake engineering."
ln be:seismic_design be.structural sys:is_a
ln be:seismic_design be:building_codes @informs
set.add name="ontology.building_engineering" id="be:seismic_design"

def "be:site_management" "Construction site management."
ln be:site_management be.construction sys:is_a
set.add name="ontology.building_engineering" id="be:site_management"

def "be:steel" "Steel materials."
ln be:steel be.materials sys:is_a
set.add name="ontology.building_engineering" id="be:steel"

def "be:steel_structure" "Steel structures."
ln be:steel_structure be.structural sys:is_a
set.add name="ontology.building_engineering" id="be:steel_structure"

def "be:thermal_performance" "Thermal performance and heat transfer."
ln be:thermal_performance be.building_physics sys:is_a
set.add name="ontology.building_engineering" id="be:thermal_performance"

def "be:timber_structure" "Timber structures."
ln be:timber_structure be.structural sys:is_a
set.add name="ontology.building_engineering" id="be:timber_structure"

def "be:urban_context" "Urban context and zoning."
ln be:urban_context be.urban_integration sys:is_a
ln be:urban_context be:mobility_access @integrates_with
set.add name="ontology.building_engineering" id="be:urban_context"

def "be:wood" "Wood materials."
ln be:wood be.materials sys:is_a
set.add name="ontology.building_engineering" id="be:wood"
