# Akasha ontology — namespace: cc
# atoms: 34

def "cc.automation" "Automation and control systems."
set.add name="ontology.cold_chain" id="cc.automation"

def "cc.integration" "Integration with supply chain and logistics."
set.add name="ontology.cold_chain" id="cc.integration"

def "cc.monitoring" "Monitoring and sensing systems."
set.add name="ontology.cold_chain" id="cc.monitoring"

def "cc.packaging" "Cold-chain packaging and insulation."
set.add name="ontology.cold_chain" id="cc.packaging"

def "cc.safety" "Food safety and compliance."
set.add name="ontology.cold_chain" id="cc.safety"

def "cc.storage" "Cold storage and warehousing."
set.add name="ontology.cold_chain" id="cc.storage"

def "cc.temperature_control" "Temperature control and thermal management."
set.add name="ontology.cold_chain" id="cc.temperature_control"

def "cc.transport" "Cold transport systems."
set.add name="ontology.cold_chain" id="cc.transport"

def "cc:agri_link" "Integration with agricultural supply chains."
ln cc:agri_link cc.integration sys:is_a
set.add name="ontology.cold_chain" id="cc:agri_link"

def "cc:air_cargo" "Temperature-controlled air cargo."
ln cc:air_cargo cc.transport sys:is_a
set.add name="ontology.cold_chain" id="cc:air_cargo"

def "cc:alerting" "Alerts for temperature deviations."
ln cc:alerting cc.automation sys:is_a
set.add name="ontology.cold_chain" id="cc:alerting"

def "cc:chilling" "Chilling and refrigeration."
ln cc:chilling cc.temperature_control sys:is_a
set.add name="ontology.cold_chain" id="cc:chilling"

def "cc:cold_warehouse" "Cold warehouses and distribution centers."
ln cc:cold_warehouse cc.storage sys:is_a
ln cc:cold_warehouse cc:food_processing_link @feeds
set.add name="ontology.cold_chain" id="cc:cold_warehouse"

def "cc:control_systems" "Temperature control systems."
ln cc:control_systems cc.automation sys:is_a
set.add name="ontology.cold_chain" id="cc:control_systems"

def "cc:data_logger" "Data loggers for temperature history."
ln cc:data_logger cc.monitoring sys:is_a
set.add name="ontology.cold_chain" id="cc:data_logger"

def "cc:drone_cold_delivery" "Drone-based cold delivery."
ln cc:drone_cold_delivery cc.transport sys:is_a
ln cc:drone_cold_delivery cc:logistics_link @supports
set.add name="ontology.cold_chain" id="cc:drone_cold_delivery"

def "cc:food_processing_link" "Integration with food processing."
ln cc:food_processing_link cc.integration sys:is_a
set.add name="ontology.cold_chain" id="cc:food_processing_link"

def "cc:freezing" "Freezing and deep-freezing."
ln cc:freezing cc.temperature_control sys:is_a
set.add name="ontology.cold_chain" id="cc:freezing"

def "cc:gps_tracking" "GPS tracking for cold chain."
ln cc:gps_tracking cc.monitoring sys:is_a
set.add name="ontology.cold_chain" id="cc:gps_tracking"

def "cc:haccp" "HACCP compliance."
ln cc:haccp cc.safety sys:is_a
set.add name="ontology.cold_chain" id="cc:haccp"

def "cc:humidity_sensor" "Humidity sensors."
ln cc:humidity_sensor cc.monitoring sys:is_a
set.add name="ontology.cold_chain" id="cc:humidity_sensor"

def "cc:insulated_packaging" "Insulated packaging materials."
ln cc:insulated_packaging cc.packaging sys:is_a
set.add name="ontology.cold_chain" id="cc:insulated_packaging"

def "cc:iso22000" "ISO 22000 food safety management."
ln cc:iso22000 cc.safety sys:is_a
set.add name="ontology.cold_chain" id="cc:iso22000"

def "cc:logistics_link" "Integration with logistics networks."
ln cc:logistics_link cc.integration sys:is_a
set.add name="ontology.cold_chain" id="cc:logistics_link"

def "cc:phase_change_material" "PCM-based thermal control."
ln cc:phase_change_material cc.packaging sys:is_a
ln cc:phase_change_material cc:insulated_packaging @enhances
set.add name="ontology.cold_chain" id="cc:phase_change_material"

def "cc:predictive_maintenance" "Predictive maintenance for cold equipment."
ln cc:predictive_maintenance cc.automation sys:is_a
set.add name="ontology.cold_chain" id="cc:predictive_maintenance"

def "cc:reefer_container" "Refrigerated containers."
ln cc:reefer_container cc.storage sys:is_a
set.add name="ontology.cold_chain" id="cc:reefer_container"

def "cc:reefer_ship" "Refrigerated shipping."
ln cc:reefer_ship cc.transport sys:is_a
set.add name="ontology.cold_chain" id="cc:reefer_ship"

def "cc:reefer_truck" "Refrigerated trucks."
ln cc:reefer_truck cc.transport sys:is_a
set.add name="ontology.cold_chain" id="cc:reefer_truck"

def "cc:retail_display" "Refrigerated retail display units."
ln cc:retail_display cc.storage sys:is_a
set.add name="ontology.cold_chain" id="cc:retail_display"

def "cc:temp_sensor" "Temperature sensors."
ln cc:temp_sensor cc.monitoring sys:is_a
ln cc:temp_sensor cc:control_systems @informs
set.add name="ontology.cold_chain" id="cc:temp_sensor"

def "cc:temperature_zones" "Temperature zones (-30°C, 0–5°C, 5–15°C)."
ln cc:temperature_zones cc.temperature_control sys:is_a
set.add name="ontology.cold_chain" id="cc:temperature_zones"

def "cc:traceability" "Traceability and certification."
ln cc:traceability cc.safety sys:is_a
ln cc:traceability cc:haccp @verifies
set.add name="ontology.cold_chain" id="cc:traceability"

def "cc:vacuum_packaging" "Vacuum packaging for freshness."
ln cc:vacuum_packaging cc.packaging sys:is_a
set.add name="ontology.cold_chain" id="cc:vacuum_packaging"
