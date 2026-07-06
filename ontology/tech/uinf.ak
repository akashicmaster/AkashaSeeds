# Akasha ontology — namespace: uinf
# atoms: 37

def "uinf.buildings" "Buildings, facilities, and built environment."
set.add name="ontology.urban_infrastructure" id="uinf.buildings"

def "uinf.communication" "Communication networks and digital connectivity."
set.add name="ontology.urban_infrastructure" id="uinf.communication"

def "uinf.digital_infrastructure" "Digital infrastructure including IoT, cloud, and data platforms."
set.add name="ontology.urban_infrastructure" id="uinf.digital_infrastructure"

def "uinf.energy" "Energy generation, distribution, and management."
set.add name="ontology.urban_infrastructure" id="uinf.energy"

def "uinf.public_safety" "Public safety, disaster prevention, and emergency response."
set.add name="ontology.urban_infrastructure" id="uinf.public_safety"

def "uinf.transportation" "Urban transportation infrastructure."
set.add name="ontology.urban_infrastructure" id="uinf.transportation"

def "uinf.urban_operations" "Urban operations, governance, and smart city orchestration."
set.add name="ontology.urban_infrastructure" id="uinf.urban_operations"

def "uinf.water" "Water supply, sewage, and stormwater systems."
set.add name="ontology.urban_infrastructure" id="uinf.water"

def "uinf:bike_infrastructure" "Bike lanes and micromobility paths."
ln uinf:bike_infrastructure uinf.transportation sys:is_a
set.add name="ontology.urban_infrastructure" id="uinf:bike_infrastructure"

def "uinf:bus_infrastructure" "Bus lanes, stops, and depots."
ln uinf:bus_infrastructure uinf.transportation sys:is_a
set.add name="ontology.urban_infrastructure" id="uinf:bus_infrastructure"

def "uinf:cellular_network" "Cellular networks including 5G."
ln uinf:cellular_network uinf.communication sys:is_a
set.add name="ontology.urban_infrastructure" id="uinf:cellular_network"

def "uinf:cloud_platform" "Cloud platforms for urban data."
ln uinf:cloud_platform uinf.digital_infrastructure sys:is_a
set.add name="ontology.urban_infrastructure" id="uinf:cloud_platform"

def "uinf:commercial_buildings" "Commercial and office buildings."
ln uinf:commercial_buildings uinf.buildings sys:is_a
set.add name="ontology.urban_infrastructure" id="uinf:commercial_buildings"

def "uinf:digital_twin" "Urban digital twin systems."
ln uinf:digital_twin uinf.digital_infrastructure sys:is_a
ln uinf:digital_twin uinf:traffic_management @supports
set.add name="ontology.urban_infrastructure" id="uinf:digital_twin"

def "uinf:disaster_monitoring" "Disaster monitoring sensors and networks."
ln uinf:disaster_monitoring uinf.public_safety sys:is_a
set.add name="ontology.urban_infrastructure" id="uinf:disaster_monitoring"

def "uinf:earthquake_resilience" "Earthquake resilience and monitoring."
ln uinf:earthquake_resilience uinf.public_safety sys:is_a
set.add name="ontology.urban_infrastructure" id="uinf:earthquake_resilience"

def "uinf:edge_computing" "Edge computing nodes."
ln uinf:edge_computing uinf.digital_infrastructure sys:is_a
set.add name="ontology.urban_infrastructure" id="uinf:edge_computing"

def "uinf:energy_storage" "Energy storage systems."
ln uinf:energy_storage uinf.energy sys:is_a
set.add name="ontology.urban_infrastructure" id="uinf:energy_storage"

def "uinf:ev_charging" "EV charging infrastructure."
ln uinf:ev_charging energy:transport @expands
ln uinf:ev_charging uinf.energy sys:is_a
ln uinf:ev_charging uinf.energy @expands
set.add name="ontology.urban_infrastructure" id="uinf:ev_charging"

def "uinf:fiber_network" "Fiber-optic communication networks."
ln uinf:fiber_network uinf.communication sys:is_a
ln uinf:fiber_network uinf:cloud_platform @connects
set.add name="ontology.urban_infrastructure" id="uinf:fiber_network"

def "uinf:fire_safety" "Fire safety and emergency response."
ln uinf:fire_safety uinf.public_safety sys:is_a
set.add name="ontology.urban_infrastructure" id="uinf:fire_safety"

def "uinf:flood_prevention" "Flood prevention and levee systems."
ln uinf:flood_prevention uinf.public_safety sys:is_a
set.add name="ontology.urban_infrastructure" id="uinf:flood_prevention"

def "uinf:housing" "Residential buildings."
ln uinf:housing uinf.buildings sys:is_a
set.add name="ontology.urban_infrastructure" id="uinf:housing"

def "uinf:iot_sensors" "IoT sensors for urban monitoring."
ln uinf:iot_sensors uinf.digital_infrastructure sys:is_a
set.add name="ontology.urban_infrastructure" id="uinf:iot_sensors"

def "uinf:mobility_orchestration" "Mobility orchestration including MaaS integration."
ln uinf:mobility_orchestration uinf.urban_operations sys:is_a
set.add name="ontology.urban_infrastructure" id="uinf:mobility_orchestration"

def "uinf:power_grid" "Electric power grid."
ln uinf:power_grid uinf.energy sys:is_a
set.add name="ontology.urban_infrastructure" id="uinf:power_grid"

def "uinf:public_buildings" "Public buildings such as schools and hospitals."
ln uinf:public_buildings uinf.buildings sys:is_a
set.add name="ontology.urban_infrastructure" id="uinf:public_buildings"

def "uinf:public_wifi" "Public Wi-Fi infrastructure."
ln uinf:public_wifi uinf.communication sys:is_a
set.add name="ontology.urban_infrastructure" id="uinf:public_wifi"

def "uinf:rail_network" "Rail and metro networks."
ln uinf:rail_network uinf.transportation sys:is_a
ln uinf:rail_network uinf:mobility_orchestration @integrates_with
set.add name="ontology.urban_infrastructure" id="uinf:rail_network"

def "uinf:renewable_energy" "Renewable energy generation."
ln uinf:renewable_energy uinf.energy sys:is_a
set.add name="ontology.urban_infrastructure" id="uinf:renewable_energy"

def "uinf:road_network" "Urban road networks."
ln uinf:road_network uinf.transportation sys:is_a
set.add name="ontology.urban_infrastructure" id="uinf:road_network"

def "uinf:sewage_system" "Sewage and wastewater treatment."
ln uinf:sewage_system uinf.water sys:is_a
set.add name="ontology.urban_infrastructure" id="uinf:sewage_system"

def "uinf:stormwater_management" "Stormwater and flood control."
ln uinf:stormwater_management uinf.water sys:is_a
ln uinf:stormwater_management uinf:disaster_monitoring @monitored_by
set.add name="ontology.urban_infrastructure" id="uinf:stormwater_management"

def "uinf:traffic_management" "Urban traffic management."
ln uinf:traffic_management uinf.urban_operations sys:is_a
set.add name="ontology.urban_infrastructure" id="uinf:traffic_management"

def "uinf:urban_governance" "Urban governance and administrative systems."
ln uinf:urban_governance uinf.urban_operations sys:is_a
set.add name="ontology.urban_infrastructure" id="uinf:urban_governance"

def "uinf:waste_management" "Waste collection and recycling."
ln uinf:waste_management uinf.urban_operations sys:is_a
set.add name="ontology.urban_infrastructure" id="uinf:waste_management"

def "uinf:water_supply" "Water supply systems."
ln uinf:water_supply uinf.water sys:is_a
set.add name="ontology.urban_infrastructure" id="uinf:water_supply"
