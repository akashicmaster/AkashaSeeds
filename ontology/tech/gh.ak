# Akasha ontology — namespace: gh
# atoms: 47

def "gh.automation" "Control, scheduling, and automation logic."
set.add name="ontology.smart_greenhouse" id="gh.automation"

def "gh.climate_control" "Climate control (temperature, humidity, CO2, ventilation)."
set.add name="ontology.smart_greenhouse" id="gh.climate_control"

def "gh.energy" "Energy supply, storage, and efficiency."
set.add name="ontology.smart_greenhouse" id="gh.energy"

def "gh.integration" "Integration with farm, grid, and external systems."
set.add name="ontology.smart_greenhouse" id="gh.integration"

def "gh.irrigation" "Irrigation and fertigation systems."
set.add name="ontology.smart_greenhouse" id="gh.irrigation"

def "gh.lighting" "Artificial lighting and light management."
set.add name="ontology.smart_greenhouse" id="gh.lighting"

def "gh.optimization" "Data-driven optimization and prediction."
set.add name="ontology.smart_greenhouse" id="gh.optimization"

def "gh.sensing" "Sensors and monitoring systems."
set.add name="ontology.smart_greenhouse" id="gh.sensing"

def "gh.structure" "Greenhouse structure and physical configuration."
set.add name="ontology.smart_greenhouse" id="gh.structure"

def "gh:agri_automation_link" "Link to broader agricultural automation."
ln gh:agri_automation_link gh.integration sys:is_a
set.add name="ontology.smart_greenhouse" id="gh:agri_automation_link"

def "gh:anomaly_detection" "Anomaly detection and alerts."
ln gh:anomaly_detection gh.optimization sys:is_a
set.add name="ontology.smart_greenhouse" id="gh:anomaly_detection"

def "gh:co2_control" "CO2 injection and control."
ln gh:co2_control gh.climate_control sys:is_a
set.add name="ontology.smart_greenhouse" id="gh:co2_control"

def "gh:co2_sensor" "CO2 concentration sensors."
ln gh:co2_sensor gh.sensing sys:is_a
ln gh:co2_sensor gh:co2_control @informs
set.add name="ontology.smart_greenhouse" id="gh:co2_sensor"

def "gh:control_loops" "Feedback control loops (PID, rule-based)."
ln gh:control_loops gh.automation sys:is_a
set.add name="ontology.smart_greenhouse" id="gh:control_loops"

def "gh:cooling" "Cooling systems (pads, chillers)."
ln gh:cooling gh.climate_control sys:is_a
set.add name="ontology.smart_greenhouse" id="gh:cooling"

def "gh:cover_material" "Cover materials (glass, film, polycarbonate)."
ln gh:cover_material gh.structure sys:is_a
set.add name="ontology.smart_greenhouse" id="gh:cover_material"

def "gh:dimming_control" "Dimming and scheduling control."
ln gh:dimming_control gh.lighting sys:is_a
set.add name="ontology.smart_greenhouse" id="gh:dimming_control"

def "gh:drip_irrigation" "Drip irrigation systems."
ln gh:drip_irrigation gh.irrigation sys:is_a
set.add name="ontology.smart_greenhouse" id="gh:drip_irrigation"

def "gh:ebb_flow" "Ebb-and-flow irrigation tables."
ln gh:ebb_flow gh.irrigation sys:is_a
set.add name="ontology.smart_greenhouse" id="gh:ebb_flow"

def "gh:energy_efficiency" "Energy efficiency measures."
ln gh:energy_efficiency gh.energy sys:is_a
set.add name="ontology.smart_greenhouse" id="gh:energy_efficiency"

def "gh:energy_storage" "Energy storage (batteries, thermal)."
ln gh:energy_storage gh.energy sys:is_a
set.add name="ontology.smart_greenhouse" id="gh:energy_storage"

def "gh:farm_management_link" "Integration with farm management systems."
ln gh:farm_management_link gh.integration sys:is_a
set.add name="ontology.smart_greenhouse" id="gh:farm_management_link"

def "gh:fertigation" "Fertigation (nutrient dosing) systems."
ln gh:fertigation gh.irrigation sys:is_a
set.add name="ontology.smart_greenhouse" id="gh:fertigation"

def "gh:frame" "Structural frame (steel, aluminum, etc.)."
ln gh:frame gh.structure sys:is_a
set.add name="ontology.smart_greenhouse" id="gh:frame"

def "gh:grid_connection" "Grid connection and metering."
ln gh:grid_connection gh.energy sys:is_a
set.add name="ontology.smart_greenhouse" id="gh:grid_connection"

def "gh:growth_model" "Crop growth models."
ln gh:growth_model gh.optimization sys:is_a
set.add name="ontology.smart_greenhouse" id="gh:growth_model"

def "gh:heating" "Heating systems (boilers, heaters)."
ln gh:heating gh.climate_control sys:is_a
set.add name="ontology.smart_greenhouse" id="gh:heating"

def "gh:hps_lighting" "HPS and other legacy lighting."
ln gh:hps_lighting gh.lighting sys:is_a
set.add name="ontology.smart_greenhouse" id="gh:hps_lighting"

def "gh:humidification" "Humidification/dehumidification systems."
ln gh:humidification gh.climate_control sys:is_a
set.add name="ontology.smart_greenhouse" id="gh:humidification"

def "gh:humidity_sensor" "Humidity sensors."
ln gh:humidity_sensor gh.sensing sys:is_a
ln gh:humidity_sensor gh:misting @informs
set.add name="ontology.smart_greenhouse" id="gh:humidity_sensor"

def "gh:led_lighting" "LED grow lighting."
ln gh:led_lighting gh.lighting sys:is_a
set.add name="ontology.smart_greenhouse" id="gh:led_lighting"

def "gh:light_sensor" "PAR/illuminance sensors."
ln gh:light_sensor gh.sensing sys:is_a
ln gh:light_sensor gh:dimming_control @informs
set.add name="ontology.smart_greenhouse" id="gh:light_sensor"

def "gh:misting" "Misting and fogging systems."
ln gh:misting gh.irrigation sys:is_a
set.add name="ontology.smart_greenhouse" id="gh:misting"

def "gh:ml_optimization" "ML-based climate and resource optimization."
ln gh:ml_optimization gh.optimization sys:is_a
ln gh:ml_optimization gh.climate_control @optimizes
set.add name="ontology.smart_greenhouse" id="gh:ml_optimization"

def "gh:pv_system" "PV/solar generation for greenhouse."
ln gh:pv_system gh.energy sys:is_a
ln gh:pv_system gh:energy_efficiency @supports
set.add name="ontology.smart_greenhouse" id="gh:pv_system"

def "gh:remote_access" "Remote monitoring and control (HMI, apps)."
ln gh:remote_access gh.automation sys:is_a
ln gh:remote_access gh:anomaly_detection @monitors
set.add name="ontology.smart_greenhouse" id="gh:remote_access"

def "gh:scada_link" "Integration with SCADA/industrial control."
ln gh:scada_link gh.integration sys:is_a
set.add name="ontology.smart_greenhouse" id="gh:scada_link"

def "gh:scheduling" "Time-based and event-based scheduling."
ln gh:scheduling gh.automation sys:is_a
set.add name="ontology.smart_greenhouse" id="gh:scheduling"

def "gh:shading_system" "Shading curtains and screens."
ln gh:shading_system gh.lighting sys:is_a
set.add name="ontology.smart_greenhouse" id="gh:shading_system"

def "gh:smart_valve" "Smart valves and flow control."
ln gh:smart_valve gh.irrigation sys:is_a
set.add name="ontology.smart_greenhouse" id="gh:smart_valve"

def "gh:soil_moisture_sensor" "Soil/substrate moisture sensors."
ln gh:soil_moisture_sensor gh.sensing sys:is_a
ln gh:soil_moisture_sensor gh:drip_irrigation @informs
set.add name="ontology.smart_greenhouse" id="gh:soil_moisture_sensor"

def "gh:temperature_sensor" "Air/soil temperature sensors."
ln gh:temperature_sensor gh.sensing sys:is_a
ln gh:temperature_sensor gh:heating @informs
set.add name="ontology.smart_greenhouse" id="gh:temperature_sensor"

def "gh:ventilation" "Ventilation (fans, vents, louvers)."
ln gh:ventilation gh.climate_control sys:is_a
set.add name="ontology.smart_greenhouse" id="gh:ventilation"

def "gh:water_system_link" "Integration with water supply systems."
ln gh:water_system_link gh.integration sys:is_a
set.add name="ontology.smart_greenhouse" id="gh:water_system_link"

def "gh:yield_prediction" "Yield prediction and forecasting."
ln gh:yield_prediction gh.optimization sys:is_a
ln gh:yield_prediction gh:farm_management_link @feeds
set.add name="ontology.smart_greenhouse" id="gh:yield_prediction"

def "gh:zone_control" "Zone-based control strategies."
ln gh:zone_control gh.automation sys:is_a
set.add name="ontology.smart_greenhouse" id="gh:zone_control"

def "gh:zone_layout" "Zoning and compartment layout."
ln gh:zone_layout gh.structure sys:is_a
ln gh:zone_layout gh:zone_control @constrains
set.add name="ontology.smart_greenhouse" id="gh:zone_layout"
