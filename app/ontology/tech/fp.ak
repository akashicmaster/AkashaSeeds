# Akasha ontology — namespace: fp
# atoms: 38

def "fp.automation" "Automation and robotics in processing."
set.add name="ontology.food_processing" id="fp.automation"

def "fp.energy" "Energy use and thermal processes."
set.add name="ontology.food_processing" id="fp.energy"

def "fp.integration" "Integration with supply chain and logistics."
set.add name="ontology.food_processing" id="fp.integration"

def "fp.packaging" "Food packaging systems."
set.add name="ontology.food_processing" id="fp.packaging"

def "fp.preservation" "Preservation and shelf-life extension."
set.add name="ontology.food_processing" id="fp.preservation"

def "fp.primary_processing" "Primary food processing."
set.add name="ontology.food_processing" id="fp.primary_processing"

def "fp.quality_control" "Quality control and inspection."
set.add name="ontology.food_processing" id="fp.quality_control"

def "fp.safety" "Food safety and compliance."
set.add name="ontology.food_processing" id="fp.safety"

def "fp.secondary_processing" "Secondary/industrial processing."
set.add name="ontology.food_processing" id="fp.secondary_processing"

def "fp:allergen_control" "Allergen management."
ln fp:allergen_control fp.safety sys:is_a
set.add name="ontology.food_processing" id="fp:allergen_control"

def "fp:canning" "Canning and sealing."
ln fp:canning fp.preservation sys:is_a
set.add name="ontology.food_processing" id="fp:canning"

def "fp:cleaning" "Cleaning and washing."
ln fp:cleaning fp.primary_processing sys:is_a
set.add name="ontology.food_processing" id="fp:cleaning"

def "fp:cold_chain_link" "Cold chain integration."
ln fp:cold_chain_link fp.integration sys:is_a
ln fp:cold_chain_link fp.preservation @extends
set.add name="ontology.food_processing" id="fp:cold_chain_link"

def "fp:conveyor_systems" "Conveyor and material handling."
ln fp:conveyor_systems fp.automation sys:is_a
set.add name="ontology.food_processing" id="fp:conveyor_systems"

def "fp:cooking" "Cooking, steaming, boiling."
ln fp:cooking fp.secondary_processing sys:is_a
set.add name="ontology.food_processing" id="fp:cooking"

def "fp:cooling_systems" "Cooling and chilling systems."
ln fp:cooling_systems fp.energy sys:is_a
set.add name="ontology.food_processing" id="fp:cooling_systems"

def "fp:cutting" "Cutting, slicing, trimming."
ln fp:cutting fp.primary_processing sys:is_a
set.add name="ontology.food_processing" id="fp:cutting"

def "fp:drying" "Drying and dehydration."
ln fp:drying fp.preservation sys:is_a
set.add name="ontology.food_processing" id="fp:drying"

def "fp:extrusion" "Extrusion and forming."
ln fp:extrusion fp.secondary_processing sys:is_a
set.add name="ontology.food_processing" id="fp:extrusion"

def "fp:fermentation" "Fermentation processes."
ln fp:fermentation fp.secondary_processing sys:is_a
set.add name="ontology.food_processing" id="fp:fermentation"

def "fp:freezing" "Freezing and deep-freezing."
ln fp:freezing fp.preservation sys:is_a
set.add name="ontology.food_processing" id="fp:freezing"

def "fp:haccp" "HACCP and hazard analysis."
ln fp:haccp fp.safety sys:is_a
set.add name="ontology.food_processing" id="fp:haccp"

def "fp:inspection" "Visual and automated inspection."
ln fp:inspection fp.quality_control sys:is_a
set.add name="ontology.food_processing" id="fp:inspection"

def "fp:lab_testing" "Laboratory testing."
ln fp:lab_testing fp.quality_control sys:is_a
set.add name="ontology.food_processing" id="fp:lab_testing"

def "fp:logistics_link" "Logistics and distribution integration."
ln fp:logistics_link fp.integration sys:is_a
set.add name="ontology.food_processing" id="fp:logistics_link"

def "fp:machine_vision" "Machine vision for processing."
ln fp:machine_vision fp.automation sys:is_a
ln fp:machine_vision fp:inspection @enhances
set.add name="ontology.food_processing" id="fp:machine_vision"

def "fp:map_pack" "Modified Atmosphere Packaging (MAP)."
ln fp:map_pack fp.packaging sys:is_a
set.add name="ontology.food_processing" id="fp:map_pack"

def "fp:microbial_control" "Microbial control and sanitation."
ln fp:microbial_control fp.safety sys:is_a
set.add name="ontology.food_processing" id="fp:microbial_control"

def "fp:mixing" "Mixing and blending."
ln fp:mixing fp.secondary_processing sys:is_a
set.add name="ontology.food_processing" id="fp:mixing"

def "fp:pasteurization" "Pasteurization and heat treatment."
ln fp:pasteurization fp.preservation sys:is_a
ln fp:pasteurization fp.safety @enables
set.add name="ontology.food_processing" id="fp:pasteurization"

def "fp:robotic_picking" "Robotic picking and sorting."
ln fp:robotic_picking fp.automation sys:is_a
set.add name="ontology.food_processing" id="fp:robotic_picking"

def "fp:sealing" "Sealing and wrapping."
ln fp:sealing fp.packaging sys:is_a
set.add name="ontology.food_processing" id="fp:sealing"

def "fp:sensor_qc" "Sensor-based QC (NIR, hyperspectral)."
ln fp:sensor_qc fp.quality_control sys:is_a
set.add name="ontology.food_processing" id="fp:sensor_qc"

def "fp:sorting" "Sorting and grading."
ln fp:sorting fp.primary_processing sys:is_a
ln fp:sorting fp:robotic_picking @supports
set.add name="ontology.food_processing" id="fp:sorting"

def "fp:steam_systems" "Steam systems for cooking/sterilization."
ln fp:steam_systems fp.energy sys:is_a
set.add name="ontology.food_processing" id="fp:steam_systems"

def "fp:thermal_processing" "Thermal processing and heat transfer."
ln fp:thermal_processing fp.energy sys:is_a
set.add name="ontology.food_processing" id="fp:thermal_processing"

def "fp:traceability_link" "Traceability and certification."
ln fp:traceability_link fp.integration sys:is_a
ln fp:traceability_link fp:haccp @verifies
set.add name="ontology.food_processing" id="fp:traceability_link"

def "fp:vacuum_pack" "Vacuum packaging."
ln fp:vacuum_pack fp.packaging sys:is_a
set.add name="ontology.food_processing" id="fp:vacuum_pack"
