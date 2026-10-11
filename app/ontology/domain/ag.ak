# Akasha ontology — namespace: ag
# atoms: 32

def "ag.drones" "Aerial drones for agriculture."
set.add name="ontology.agricultural_automation" id="ag.drones"

def "ag.environment_control" "Greenhouse and climate control."
set.add name="ontology.agricultural_automation" id="ag.environment_control"

def "ag.irrigation" "Irrigation and water management automation."
set.add name="ontology.agricultural_automation" id="ag.irrigation"

def "ag.operations" "Farm operations and workflow automation."
set.add name="ontology.agricultural_automation" id="ag.operations"

def "ag.planning" "Crop planning, prediction, and optimization."
set.add name="ontology.agricultural_automation" id="ag.planning"

def "ag.robotics" "Agricultural robots and autonomous machinery."
set.add name="ontology.agricultural_automation" id="ag.robotics"

def "ag.sensing" "Sensors and monitoring systems."
set.add name="ontology.agricultural_automation" id="ag.sensing"

def "ag.supply_chain" "Integration with food supply chains."
set.add name="ontology.agricultural_automation" id="ag.supply_chain"

def "ag:autonomous_tractor" "Autonomous tractors and machinery."
ln ag:autonomous_tractor ag.robotics sys:is_a
ln ag:autonomous_tractor ag:workflow_automation @participates_in
set.add name="ontology.agricultural_automation" id="ag:autonomous_tractor"

def "ag:co2_control" "CO2 concentration control."
ln ag:co2_control ag.environment_control sys:is_a
set.add name="ontology.agricultural_automation" id="ag:co2_control"

def "ag:crop_health" "Crop health and growth monitoring."
ln ag:crop_health ag.sensing sys:is_a
set.add name="ontology.agricultural_automation" id="ag:crop_health"

def "ag:drip_irrigation" "Automated drip irrigation."
ln ag:drip_irrigation ag.irrigation sys:is_a
set.add name="ontology.agricultural_automation" id="ag:drip_irrigation"

def "ag:drone_mapping" "Aerial mapping and crop analysis."
ln ag:drone_mapping ag.drones sys:is_a
ln ag:drone_mapping ag:yield_prediction @supports
set.add name="ontology.agricultural_automation" id="ag:drone_mapping"

def "ag:drone_monitoring" "Large-area crop monitoring."
ln ag:drone_monitoring ag.drones sys:is_a
set.add name="ontology.agricultural_automation" id="ag:drone_monitoring"

def "ag:drone_spraying" "Drone spraying and fertilization."
ln ag:drone_spraying ag.drones sys:is_a
ln ag:drone_spraying ag:water_optimization @related_to
set.add name="ontology.agricultural_automation" id="ag:drone_spraying"

def "ag:greenhouse_control" "Greenhouse climate control."
ln ag:greenhouse_control ag.environment_control sys:is_a
set.add name="ontology.agricultural_automation" id="ag:greenhouse_control"

def "ag:grow_lighting" "Grow lighting automation."
ln ag:grow_lighting ag.environment_control sys:is_a
set.add name="ontology.agricultural_automation" id="ag:grow_lighting"

def "ag:harvesting_robot" "Harvesting robots."
ln ag:harvesting_robot ag.robotics sys:is_a
set.add name="ontology.agricultural_automation" id="ag:harvesting_robot"

def "ag:inventory_management" "Seed, fertilizer, and supply inventory."
ln ag:inventory_management ag.operations sys:is_a
set.add name="ontology.agricultural_automation" id="ag:inventory_management"

def "ag:market_link" "Market and distribution integration."
ln ag:market_link ag.supply_chain sys:is_a
set.add name="ontology.agricultural_automation" id="ag:market_link"

def "ag:ml_optimization" "Machine learning for crop optimization."
ln ag:ml_optimization ag.planning sys:is_a
ln ag:ml_optimization ag:greenhouse_control @optimizes
set.add name="ontology.agricultural_automation" id="ag:ml_optimization"

def "ag:post_harvest" "Post-harvest processing."
ln ag:post_harvest ag.supply_chain sys:is_a
set.add name="ontology.agricultural_automation" id="ag:post_harvest"

def "ag:smart_valve" "Smart irrigation valves."
ln ag:smart_valve ag.irrigation sys:is_a
set.add name="ontology.agricultural_automation" id="ag:smart_valve"

def "ag:soil_sensor" "Soil moisture, nutrients, and pH sensors."
ln ag:soil_sensor ag.sensing sys:is_a
ln ag:soil_sensor ag:drip_irrigation @informs
set.add name="ontology.agricultural_automation" id="ag:soil_sensor"

def "ag:task_scheduling" "Task scheduling and resource allocation."
ln ag:task_scheduling ag.planning sys:is_a
set.add name="ontology.agricultural_automation" id="ag:task_scheduling"

def "ag:traceability" "Traceability and logging."
ln ag:traceability ag.operations sys:is_a
set.add name="ontology.agricultural_automation" id="ag:traceability"

def "ag:transport" "Transport and cold-chain integration."
ln ag:transport ag.supply_chain sys:is_a
set.add name="ontology.agricultural_automation" id="ag:transport"

def "ag:water_optimization" "Water usage optimization."
ln ag:water_optimization ag.irrigation sys:is_a
set.add name="ontology.agricultural_automation" id="ag:water_optimization"

def "ag:weather_station" "Local weather monitoring."
ln ag:weather_station ag.sensing sys:is_a
set.add name="ontology.agricultural_automation" id="ag:weather_station"

def "ag:weeding_robot" "Weeding and crop-care robots."
ln ag:weeding_robot ag.robotics sys:is_a
set.add name="ontology.agricultural_automation" id="ag:weeding_robot"

def "ag:workflow_automation" "Farm workflow automation."
ln ag:workflow_automation ag.operations sys:is_a
set.add name="ontology.agricultural_automation" id="ag:workflow_automation"

def "ag:yield_prediction" "Yield prediction and forecasting."
ln ag:yield_prediction ag.planning sys:is_a
set.add name="ontology.agricultural_automation" id="ag:yield_prediction"
