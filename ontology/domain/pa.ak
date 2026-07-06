# Akasha ontology — namespace: pa
# atoms: 34

def "pa.data_analytics" "Data analytics and modeling."
set.add name="ontology.precision_agriculture" id="pa.data_analytics"

def "pa.decision_support" "Decision support and recommendations."
set.add name="ontology.precision_agriculture" id="pa.decision_support"

def "pa.integration" "Integration with farm management and supply chains."
set.add name="ontology.precision_agriculture" id="pa.integration"

def "pa.mapping" "Spatial mapping and geospatial layers."
set.add name="ontology.precision_agriculture" id="pa.mapping"

def "pa.robotics_drones" "Robotics and drones in precision agriculture."
set.add name="ontology.precision_agriculture" id="pa.robotics_drones"

def "pa.sensing" "Sensors and data acquisition."
set.add name="ontology.precision_agriculture" id="pa.sensing"

def "pa.sustainability" "Sustainability and resource efficiency."
set.add name="ontology.precision_agriculture" id="pa.sustainability"

def "pa.variable_rate" "Variable-rate application of inputs."
set.add name="ontology.precision_agriculture" id="pa.variable_rate"

def "pa:agri_automation_link" "Integration with agricultural automation and control."
ln pa:agri_automation_link pa.integration sys:is_a
set.add name="ontology.precision_agriculture" id="pa:agri_automation_link"

def "pa:alerts" "Alerts and notifications for anomalies and events."
ln pa:alerts pa.decision_support sys:is_a
set.add name="ontology.precision_agriculture" id="pa:alerts"

def "pa:crop_sensing" "Crop health, biomass, and stress sensing."
ln pa:crop_sensing pa.sensing sys:is_a
set.add name="ontology.precision_agriculture" id="pa:crop_sensing"

def "pa:decision_dashboard" "Decision dashboards and visualization."
ln pa:decision_dashboard pa.decision_support sys:is_a
set.add name="ontology.precision_agriculture" id="pa:decision_dashboard"

def "pa:drone_mapping" "Drone-based mapping and imaging."
ln pa:drone_mapping pa.robotics_drones sys:is_a
ln pa:drone_mapping pa:yield_mapping @supports
set.add name="ontology.precision_agriculture" id="pa:drone_mapping"

def "pa:drone_spraying" "Drone-based spraying and application."
ln pa:drone_spraying pa.robotics_drones sys:is_a
set.add name="ontology.precision_agriculture" id="pa:drone_spraying"

def "pa:elevation_map" "Elevation and terrain maps."
ln pa:elevation_map pa.mapping sys:is_a
set.add name="ontology.precision_agriculture" id="pa:elevation_map"

def "pa:environment_sensing" "Weather, microclimate, and environmental sensing."
ln pa:environment_sensing pa.sensing sys:is_a
set.add name="ontology.precision_agriculture" id="pa:environment_sensing"

def "pa:environmental_impact" "Environmental impact assessment."
ln pa:environmental_impact pa.sustainability sys:is_a
set.add name="ontology.precision_agriculture" id="pa:environmental_impact"

def "pa:farm_management_link" "Integration with farm management systems."
ln pa:farm_management_link pa.integration sys:is_a
ln pa:farm_management_link pa:decision_dashboard @hosts
set.add name="ontology.precision_agriculture" id="pa:farm_management_link"

def "pa:field_robot_link" "Link to field robots for precision tasks."
ln pa:field_robot_link pa.robotics_drones sys:is_a
set.add name="ontology.precision_agriculture" id="pa:field_robot_link"

def "pa:management_zones" "Management zone maps."
ln pa:management_zones pa.mapping sys:is_a
set.add name="ontology.precision_agriculture" id="pa:management_zones"

def "pa:ml_models" "Machine learning models for prediction and classification."
ln pa:ml_models pa.data_analytics sys:is_a
ln pa:ml_models pa:variable_rate_fertilizer @optimizes
set.add name="ontology.precision_agriculture" id="pa:ml_models"

def "pa:nutrient_efficiency" "Nutrient use efficiency."
ln pa:nutrient_efficiency pa.sustainability sys:is_a
set.add name="ontology.precision_agriculture" id="pa:nutrient_efficiency"

def "pa:recommendation_engine" "Recommendation engines for field operations."
ln pa:recommendation_engine pa.decision_support sys:is_a
set.add name="ontology.precision_agriculture" id="pa:recommendation_engine"

def "pa:simulation_models" "Simulation models for crop and resource dynamics."
ln pa:simulation_models pa.data_analytics sys:is_a
set.add name="ontology.precision_agriculture" id="pa:simulation_models"

def "pa:soil_mapping" "Soil property maps."
ln pa:soil_mapping pa.mapping sys:is_a
set.add name="ontology.precision_agriculture" id="pa:soil_mapping"

def "pa:soil_sensing" "Soil moisture, nutrients, salinity, and pH sensing."
ln pa:soil_sensing pa.sensing sys:is_a
ln pa:soil_sensing pa:soil_mapping @feeds
set.add name="ontology.precision_agriculture" id="pa:soil_sensing"

def "pa:statistical_analysis" "Statistical analysis of field data."
ln pa:statistical_analysis pa.data_analytics sys:is_a
set.add name="ontology.precision_agriculture" id="pa:statistical_analysis"

def "pa:supply_chain_link" "Integration with agricultural supply chains."
ln pa:supply_chain_link pa.integration sys:is_a
set.add name="ontology.precision_agriculture" id="pa:supply_chain_link"

def "pa:variable_rate_chemicals" "Variable-rate pesticide and herbicide application."
ln pa:variable_rate_chemicals pa.variable_rate sys:is_a
set.add name="ontology.precision_agriculture" id="pa:variable_rate_chemicals"

def "pa:variable_rate_fertilizer" "Variable-rate fertilizer application."
ln pa:variable_rate_fertilizer pa.variable_rate sys:is_a
set.add name="ontology.precision_agriculture" id="pa:variable_rate_fertilizer"

def "pa:variable_rate_irrigation" "Variable-rate irrigation."
ln pa:variable_rate_irrigation pa.variable_rate sys:is_a
set.add name="ontology.precision_agriculture" id="pa:variable_rate_irrigation"

def "pa:variable_rate_seeding" "Variable-rate seeding and planting."
ln pa:variable_rate_seeding pa.variable_rate sys:is_a
set.add name="ontology.precision_agriculture" id="pa:variable_rate_seeding"

def "pa:water_efficiency" "Water use efficiency."
ln pa:water_efficiency pa.sustainability sys:is_a
ln pa:water_efficiency pa:variable_rate_irrigation @guides
set.add name="ontology.precision_agriculture" id="pa:water_efficiency"

def "pa:yield_mapping" "Yield maps from harvest data."
ln pa:yield_mapping pa.mapping sys:is_a
ln pa:yield_mapping pa:management_zones @informs
set.add name="ontology.precision_agriculture" id="pa:yield_mapping"
