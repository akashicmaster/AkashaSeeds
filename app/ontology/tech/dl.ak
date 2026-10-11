# Akasha ontology — namespace: dl
# atoms: 32

def "dl.fleet" "Drone fleet and asset management."
set.add name="ontology.drone_logistics" id="dl.fleet"

def "dl.hubs" "Drone hubs, vertiports, and depots."
set.add name="ontology.drone_logistics" id="dl.hubs"

def "dl.operations" "Operational workflows and mission execution."
set.add name="ontology.drone_logistics" id="dl.operations"

def "dl.payload" "Payload types and handling."
set.add name="ontology.drone_logistics" id="dl.payload"

def "dl.regulation" "Regulations, compliance, and safety for drone logistics."
set.add name="ontology.drone_logistics" id="dl.regulation"

def "dl.routing" "Routing, path planning, and optimization."
set.add name="ontology.drone_logistics" id="dl.routing"

def "dl.swarm_delivery" "Swarm-based delivery and coordination."
set.add name="ontology.drone_logistics" id="dl.swarm_delivery"

def "dl.urban_integration" "Integration with urban logistics and infrastructure."
set.add name="ontology.drone_logistics" id="dl.urban_integration"

def "dl:air_corridor" "Designated aerial corridors and lanes."
ln dl:air_corridor dl.routing sys:is_a
set.add name="ontology.drone_logistics" id="dl:air_corridor"

def "dl:airspace_rules" "Airspace rules for drone logistics."
ln dl:airspace_rules dl.regulation sys:is_a
set.add name="ontology.drone_logistics" id="dl:airspace_rules"

def "dl:batch_delivery" "Batch delivery using multiple drones."
ln dl:batch_delivery dl.swarm_delivery sys:is_a
set.add name="ontology.drone_logistics" id="dl:batch_delivery"

def "dl:cooperative_swarm" "Cooperative swarm delivery strategies."
ln dl:cooperative_swarm dl.swarm_delivery sys:is_a
set.add name="ontology.drone_logistics" id="dl:cooperative_swarm"

def "dl:dispatch" "Dispatching of delivery missions."
ln dl:dispatch dl.operations sys:is_a
ln dl:dispatch dl:last_mile @supports
set.add name="ontology.drone_logistics" id="dl:dispatch"

def "dl:dynamic_task_allocation" "Dynamic task allocation among drones."
ln dl:dynamic_task_allocation dl.swarm_delivery sys:is_a
ln dl:dynamic_task_allocation dl:cooperative_swarm @enables
set.add name="ontology.drone_logistics" id="dl:dynamic_task_allocation"

def "dl:fleet_assignment" "Assignment of drones to missions."
ln dl:fleet_assignment dl.fleet sys:is_a
set.add name="ontology.drone_logistics" id="dl:fleet_assignment"

def "dl:fleet_inventory" "Inventory of drones and capabilities."
ln dl:fleet_inventory dl.fleet sys:is_a
set.add name="ontology.drone_logistics" id="dl:fleet_inventory"

def "dl:fleet_maintenance" "Maintenance scheduling and health monitoring."
ln dl:fleet_maintenance dl.fleet sys:is_a
set.add name="ontology.drone_logistics" id="dl:fleet_maintenance"

def "dl:incident_management" "Incident and exception handling."
ln dl:incident_management dl.operations sys:is_a
set.add name="ontology.drone_logistics" id="dl:incident_management"

def "dl:last_mile" "Last-mile delivery integration."
ln dl:last_mile dl.urban_integration sys:is_a
set.add name="ontology.drone_logistics" id="dl:last_mile"

def "dl:medical_payload" "Medical supplies and emergency payloads."
ln dl:medical_payload dl.payload sys:is_a
set.add name="ontology.drone_logistics" id="dl:medical_payload"

def "dl:micro_hub" "Micro hubs for local distribution."
ln dl:micro_hub dl.hubs sys:is_a
set.add name="ontology.drone_logistics" id="dl:micro_hub"

def "dl:parcel_payload" "Standard parcel payloads."
ln dl:parcel_payload dl.payload sys:is_a
set.add name="ontology.drone_logistics" id="dl:parcel_payload"

def "dl:privacy" "Privacy and data protection in drone operations."
ln dl:privacy dl.regulation sys:is_a
set.add name="ontology.drone_logistics" id="dl:privacy"

def "dl:route_optimization" "Optimization of routes for cost and time."
ln dl:route_optimization dl.routing sys:is_a
set.add name="ontology.drone_logistics" id="dl:route_optimization"

def "dl:route_planning" "Route planning for drone delivery."
ln dl:route_planning dl.routing sys:is_a
ln dl:route_planning dl:route_optimization @integrates_with
set.add name="ontology.drone_logistics" id="dl:route_planning"

def "dl:safety_requirements" "Safety requirements and risk management."
ln dl:safety_requirements dl.regulation sys:is_a
set.add name="ontology.drone_logistics" id="dl:safety_requirements"

def "dl:special_payload" "Oversized, fragile, or special-condition payloads."
ln dl:special_payload dl.payload sys:is_a
set.add name="ontology.drone_logistics" id="dl:special_payload"

def "dl:tracking" "Real-time tracking of drones and payloads."
ln dl:tracking dl.operations sys:is_a
ln dl:tracking dl:incident_management @informs
set.add name="ontology.drone_logistics" id="dl:tracking"

def "dl:traffic_coordination" "Coordination with ground traffic and airspace."
ln dl:traffic_coordination dl.urban_integration sys:is_a
set.add name="ontology.drone_logistics" id="dl:traffic_coordination"

def "dl:urban_logistics_network" "Urban logistics network integrating drones and ground transport."
ln dl:urban_logistics_network dl.urban_integration sys:is_a
set.add name="ontology.drone_logistics" id="dl:urban_logistics_network"

def "dl:vertiport" "Vertiports for takeoff/landing and charging."
ln dl:vertiport dl.hubs sys:is_a
ln dl:vertiport dl:airspace_rules @constrained_by
set.add name="ontology.drone_logistics" id="dl:vertiport"

def "dl:warehouse_integration" "Integration with warehouses and fulfillment centers."
ln dl:warehouse_integration dl.hubs sys:is_a
set.add name="ontology.drone_logistics" id="dl:warehouse_integration"
