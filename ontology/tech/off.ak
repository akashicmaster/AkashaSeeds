# Akasha ontology — namespace: off
# atoms: 31

def "off.communication" "Communication systems for off-grid environments."
set.add name="ontology.offgrid_systems" id="off.communication"

def "off.community" "Off-grid communities, governance, and social systems."
set.add name="ontology.offgrid_systems" id="off.community"

def "off.control" "Control, automation, and cybernetic regulation."
set.add name="ontology.offgrid_systems" id="off.control"

def "off.energy" "Off-grid energy generation and storage."
set.add name="ontology.offgrid_systems" id="off.energy"

def "off.infrastructure" "Physical and built infrastructure for off-grid living."
set.add name="ontology.offgrid_systems" id="off.infrastructure"

def "off.resilience" "Resilience, disaster autonomy, and redundancy."
set.add name="ontology.offgrid_systems" id="off.resilience"

def "off.water" "Water sourcing, purification, and recycling."
set.add name="ontology.offgrid_systems" id="off.water"

def "off:battery_storage" "Battery storage for autonomous operation."
ln off:battery_storage off.energy sys:is_a
set.add name="ontology.offgrid_systems" id="off:battery_storage"

def "off:compost_toilet" "Composting toilets and sanitation."
ln off:compost_toilet off.infrastructure sys:is_a
set.add name="ontology.offgrid_systems" id="off:compost_toilet"

def "off:cybernetic_control" "Cybernetic regulation of autonomous systems."
ln off:cybernetic_control off.control sys:is_a
ln off:cybernetic_control off:predictive_control @enhances
set.add name="ontology.offgrid_systems" id="off:cybernetic_control"

def "off:desalination" "Small-scale desalination."
ln off:desalination off.water sys:is_a
set.add name="ontology.offgrid_systems" id="off:desalination"

def "off:disaster_autonomy" "Disaster-resilient off-grid operation."
ln off:disaster_autonomy off.resilience sys:is_a
set.add name="ontology.offgrid_systems" id="off:disaster_autonomy"

def "off:eco_housing" "Eco-housing and autonomous dwellings."
ln off:eco_housing off.infrastructure sys:is_a
set.add name="ontology.offgrid_systems" id="off:eco_housing"

def "off:greywater_recycling" "Greywater recycling."
ln off:greywater_recycling off.water sys:is_a
set.add name="ontology.offgrid_systems" id="off:greywater_recycling"

def "off:local_economy" "Local circular economy."
ln off:local_economy off.community sys:is_a
set.add name="ontology.offgrid_systems" id="off:local_economy"

def "off:local_ems" "Local energy management systems."
ln off:local_ems off.control sys:is_a
set.add name="ontology.offgrid_systems" id="off:local_ems"

def "off:local_governance" "Local governance for off-grid living."
ln off:local_governance off.community sys:is_a
set.add name="ontology.offgrid_systems" id="off:local_governance"

def "off:mesh_network" "Local mesh networks."
ln off:mesh_network off.communication sys:is_a
ln off:mesh_network off:local_ems @supports
ln off:mesh_network udr:emergency_dispatch @connects
set.add name="ontology.offgrid_systems" id="off:mesh_network"

def "off:micro_community" "Small-scale autonomous communities."
ln off:micro_community off.community sys:is_a
set.add name="ontology.offgrid_systems" id="off:micro_community"

def "off:micro_hydro" "Micro-hydro generation."
ln off:micro_hydro off.energy sys:is_a
set.add name="ontology.offgrid_systems" id="off:micro_hydro"

def "off:predictive_control" "Predictive control for resource optimization."
ln off:predictive_control off.control sys:is_a
set.add name="ontology.offgrid_systems" id="off:predictive_control"

def "off:radio_comm" "Radio communication for emergencies."
ln off:radio_comm off.communication sys:is_a
set.add name="ontology.offgrid_systems" id="off:radio_comm"

def "off:rainwater" "Rainwater harvesting."
ln off:rainwater off.water sys:is_a
ln off:rainwater off:water_purification @feeds
set.add name="ontology.offgrid_systems" id="off:rainwater"

def "off:redundancy" "Redundant systems for autonomy."
ln off:redundancy off.resilience sys:is_a
set.add name="ontology.offgrid_systems" id="off:redundancy"

def "off:resource_storage" "Food, water, and energy storage."
ln off:resource_storage off.resilience sys:is_a
set.add name="ontology.offgrid_systems" id="off:resource_storage"

def "off:satellite_internet" "Satellite internet for remote connectivity."
ln off:satellite_internet off.communication sys:is_a
set.add name="ontology.offgrid_systems" id="off:satellite_internet"

def "off:solar" "Solar PV for off-grid power."
ln off:solar off.energy sys:is_a
ln off:solar off:battery_storage @charges
set.add name="ontology.offgrid_systems" id="off:solar"

def "off:thermal_insulation" "Thermal insulation for energy efficiency."
ln off:thermal_insulation off.infrastructure sys:is_a
set.add name="ontology.offgrid_systems" id="off:thermal_insulation"

def "off:v2h" "Vehicle-to-home energy systems."
ln off:v2h off.energy sys:is_a
set.add name="ontology.offgrid_systems" id="off:v2h"

def "off:water_purification" "Water purification systems."
ln off:water_purification off.water sys:is_a
set.add name="ontology.offgrid_systems" id="off:water_purification"

def "off:wind" "Small-scale wind turbines."
ln off:wind off.energy sys:is_a
set.add name="ontology.offgrid_systems" id="off:wind"
