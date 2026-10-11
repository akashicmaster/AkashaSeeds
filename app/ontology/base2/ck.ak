# Akasha ontology — namespace: ck
# atoms: 37

def "ck.automation" "Automation and robotics."
set.add name="ontology.central_kitchen" id="ck.automation"

def "ck.cooking" "Cooking and thermal processing."
set.add name="ontology.central_kitchen" id="ck.cooking"

def "ck.integration" "Integration with supply chain and retail."
set.add name="ontology.central_kitchen" id="ck.integration"

def "ck.logistics" "Logistics and distribution integration."
set.add name="ontology.central_kitchen" id="ck.logistics"

def "ck.packaging" "Packaging and sealing."
set.add name="ontology.central_kitchen" id="ck.packaging"

def "ck.portioning" "Portioning and meal assembly."
set.add name="ontology.central_kitchen" id="ck.portioning"

def "ck.preparation" "Ingredient preparation and preprocessing."
set.add name="ontology.central_kitchen" id="ck.preparation"

def "ck.quality_control" "Quality control and inspection."
set.add name="ontology.central_kitchen" id="ck.quality_control"

def "ck.safety" "Food safety and hygiene management."
set.add name="ontology.central_kitchen" id="ck.safety"

def "ck:agri_link" "Integration with agricultural supply chains."
ln ck:agri_link ck.integration sys:is_a
set.add name="ontology.central_kitchen" id="ck:agri_link"

def "ck:allergen_control" "Allergen management."
ln ck:allergen_control ck.safety sys:is_a
set.add name="ontology.central_kitchen" id="ck:allergen_control"

def "ck:auto_portioning" "Automated portioning."
ln ck:auto_portioning ck.portioning sys:is_a
set.add name="ontology.central_kitchen" id="ck:auto_portioning"

def "ck:cold_chain_link" "Cold chain integration."
ln ck:cold_chain_link ck.logistics sys:is_a
set.add name="ontology.central_kitchen" id="ck:cold_chain_link"

def "ck:conveyor_systems" "Conveyor and material handling."
ln ck:conveyor_systems ck.automation sys:is_a
set.add name="ontology.central_kitchen" id="ck:conveyor_systems"

def "ck:cutting" "Cutting, slicing, chopping."
ln ck:cutting ck.preparation sys:is_a
set.add name="ontology.central_kitchen" id="ck:cutting"

def "ck:food_processing_link" "Integration with food processing."
ln ck:food_processing_link ck.integration sys:is_a
set.add name="ontology.central_kitchen" id="ck:food_processing_link"

def "ck:frying" "Frying and sautéing."
ln ck:frying ck.cooking sys:is_a
set.add name="ontology.central_kitchen" id="ck:frying"

def "ck:haccp" "HACCP compliance."
ln ck:haccp ck.safety sys:is_a
ln ck:haccp ck:sanitation @requires
set.add name="ontology.central_kitchen" id="ck:haccp"

def "ck:inspection" "Visual and automated inspection."
ln ck:inspection ck.quality_control sys:is_a
set.add name="ontology.central_kitchen" id="ck:inspection"

def "ck:labeling" "Labeling and identification."
ln ck:labeling ck.portioning sys:is_a
set.add name="ontology.central_kitchen" id="ck:labeling"

def "ck:last_mile" "Last-mile delivery integration."
ln ck:last_mile ck.logistics sys:is_a
set.add name="ontology.central_kitchen" id="ck:last_mile"

def "ck:machine_vision" "Machine vision for processing."
ln ck:machine_vision ck.automation sys:is_a
set.add name="ontology.central_kitchen" id="ck:machine_vision"

def "ck:map_pack" "Modified Atmosphere Packaging (MAP)."
ln ck:map_pack ck.packaging sys:is_a
set.add name="ontology.central_kitchen" id="ck:map_pack"

def "ck:meal_assembly" "Meal assembly lines."
ln ck:meal_assembly ck.portioning sys:is_a
set.add name="ontology.central_kitchen" id="ck:meal_assembly"

def "ck:oven_cooking" "Oven and baking processes."
ln ck:oven_cooking ck.cooking sys:is_a
set.add name="ontology.central_kitchen" id="ck:oven_cooking"

def "ck:retail_link" "Integration with retail and restaurants."
ln ck:retail_link ck.integration sys:is_a
set.add name="ontology.central_kitchen" id="ck:retail_link"

def "ck:robotic_picking" "Robotic picking and sorting."
ln ck:robotic_picking ck.automation sys:is_a
ln ck:robotic_picking ck:sorting @accelerates
set.add name="ontology.central_kitchen" id="ck:robotic_picking"

def "ck:route_planning" "Route planning for meal distribution."
ln ck:route_planning ck.logistics sys:is_a
ln ck:route_planning ck:last_mile @optimizes
set.add name="ontology.central_kitchen" id="ck:route_planning"

def "ck:sanitation" "Sanitation and hygiene."
ln ck:sanitation ck.safety sys:is_a
set.add name="ontology.central_kitchen" id="ck:sanitation"

def "ck:sealing" "Sealing and wrapping."
ln ck:sealing ck.packaging sys:is_a
set.add name="ontology.central_kitchen" id="ck:sealing"

def "ck:sensor_qc" "Sensor-based QC (NIR, hyperspectral)."
ln ck:sensor_qc ck.quality_control sys:is_a
ln ck:sensor_qc ck:inspection @enhances
set.add name="ontology.central_kitchen" id="ck:sensor_qc"

def "ck:sorting" "Sorting and grading ingredients."
ln ck:sorting ck.preparation sys:is_a
set.add name="ontology.central_kitchen" id="ck:sorting"

def "ck:sous_vide" "Sous-vide and controlled thermal cooking."
ln ck:sous_vide ck.cooking sys:is_a
set.add name="ontology.central_kitchen" id="ck:sous_vide"

def "ck:steaming" "Steaming and boiling."
ln ck:steaming ck.cooking sys:is_a
set.add name="ontology.central_kitchen" id="ck:steaming"

def "ck:taste_panel" "Taste and sensory evaluation."
ln ck:taste_panel ck.quality_control sys:is_a
set.add name="ontology.central_kitchen" id="ck:taste_panel"

def "ck:vacuum_pack" "Vacuum packaging."
ln ck:vacuum_pack ck.packaging sys:is_a
ln ck:vacuum_pack ck:cold_chain_link @supports
set.add name="ontology.central_kitchen" id="ck:vacuum_pack"

def "ck:washing" "Washing and cleaning of ingredients."
ln ck:washing ck.preparation sys:is_a
set.add name="ontology.central_kitchen" id="ck:washing"
