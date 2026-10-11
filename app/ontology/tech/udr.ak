# Akasha ontology — namespace: udr
# atoms: 35

def "udr.community" "Community preparedness and governance."
set.add name="ontology.urban_disaster_resilience" id="udr.community"

def "udr.emergency_response" "Emergency response and crisis management."
set.add name="ontology.urban_disaster_resilience" id="udr.emergency_response"

def "udr.evacuation" "Evacuation planning and shelters."
set.add name="ontology.urban_disaster_resilience" id="udr.evacuation"

def "udr.hazards" "Natural and human-made hazards."
set.add name="ontology.urban_disaster_resilience" id="udr.hazards"

def "udr.infrastructure_resilience" "Infrastructure resilience and protection."
set.add name="ontology.urban_disaster_resilience" id="udr.infrastructure_resilience"

def "udr.monitoring" "Monitoring, sensing, and early warning."
set.add name="ontology.urban_disaster_resilience" id="udr.monitoring"

def "udr.recovery" "Recovery, reconstruction, and continuity."
set.add name="ontology.urban_disaster_resilience" id="udr.recovery"

def "udr:alert_system" "Public alert and warning systems."
ln udr:alert_system udr.monitoring sys:is_a
ln udr:alert_system udr.evacuation @triggers
set.add name="ontology.urban_disaster_resilience" id="udr:alert_system"

def "udr:business_continuity" "Business continuity planning."
ln udr:business_continuity udr.recovery sys:is_a
set.add name="ontology.urban_disaster_resilience" id="udr:business_continuity"

def "udr:debris_management" "Debris removal and management."
ln udr:debris_management udr.recovery sys:is_a
set.add name="ontology.urban_disaster_resilience" id="udr:debris_management"

def "udr:disaster_education" "Disaster education and training."
ln udr:disaster_education udr.community sys:is_a
set.add name="ontology.urban_disaster_resilience" id="udr:disaster_education"

def "udr:earthquake" "Earthquakes and seismic hazards."
ln udr:earthquake udr.hazards sys:is_a
set.add name="ontology.urban_disaster_resilience" id="udr:earthquake"

def "udr:emergency_dispatch" "Emergency dispatch and coordination."
ln udr:emergency_dispatch udr.emergency_response sys:is_a
set.add name="ontology.urban_disaster_resilience" id="udr:emergency_dispatch"

def "udr:evacuation_routes" "Evacuation routes and planning."
ln udr:evacuation_routes udr.evacuation sys:is_a
set.add name="ontology.urban_disaster_resilience" id="udr:evacuation_routes"

def "udr:evacuation_traffic" "Traffic management during evacuation."
ln udr:evacuation_traffic udr.evacuation sys:is_a
set.add name="ontology.urban_disaster_resilience" id="udr:evacuation_traffic"

def "udr:fire_department" "Fire department response."
ln udr:fire_department udr.emergency_response sys:is_a
set.add name="ontology.urban_disaster_resilience" id="udr:fire_department"

def "udr:flood" "Flooding and storm surges."
ln udr:flood udr.hazards sys:is_a
set.add name="ontology.urban_disaster_resilience" id="udr:flood"

def "udr:flood_defense" "Flood defense structures."
ln udr:flood_defense udr.infrastructure_resilience sys:is_a
set.add name="ontology.urban_disaster_resilience" id="udr:flood_defense"

def "udr:landslide" "Landslides and slope failures."
ln udr:landslide udr.hazards sys:is_a
set.add name="ontology.urban_disaster_resilience" id="udr:landslide"

def "udr:lifeline_infrastructure" "Critical lifeline infrastructure (power, water, comms)."
ln udr:lifeline_infrastructure udr.infrastructure_resilience sys:is_a
ln udr:lifeline_infrastructure udr:business_continuity @required_for
set.add name="ontology.urban_disaster_resilience" id="udr:lifeline_infrastructure"

def "udr:local_governance" "Local governance for disaster management."
ln udr:local_governance udr.community sys:is_a
set.add name="ontology.urban_disaster_resilience" id="udr:local_governance"

def "udr:medical_response" "Emergency medical response."
ln udr:medical_response udr.emergency_response sys:is_a
set.add name="ontology.urban_disaster_resilience" id="udr:medical_response"

def "udr:rainfall_monitoring" "Rainfall and hydrological monitoring."
ln udr:rainfall_monitoring udr.monitoring sys:is_a
set.add name="ontology.urban_disaster_resilience" id="udr:rainfall_monitoring"

def "udr:reconstruction" "Reconstruction of damaged infrastructure."
ln udr:reconstruction udr.recovery sys:is_a
set.add name="ontology.urban_disaster_resilience" id="udr:reconstruction"

def "udr:redundancy" "Redundant systems for resilience."
ln udr:redundancy udr.infrastructure_resilience sys:is_a
set.add name="ontology.urban_disaster_resilience" id="udr:redundancy"

def "udr:river_level" "River level monitoring."
ln udr:river_level udr.monitoring sys:is_a
ln udr:river_level udr:flood_defense @supports
set.add name="ontology.urban_disaster_resilience" id="udr:river_level"

def "udr:search_and_rescue" "Search and rescue operations."
ln udr:search_and_rescue udr.emergency_response sys:is_a
set.add name="ontology.urban_disaster_resilience" id="udr:search_and_rescue"

def "udr:seismic_monitoring" "Seismic monitoring networks."
ln udr:seismic_monitoring udr.monitoring sys:is_a
ln udr:seismic_monitoring udr:seismic_retrofit @informs
set.add name="ontology.urban_disaster_resilience" id="udr:seismic_monitoring"

def "udr:seismic_retrofit" "Seismic retrofitting of buildings."
ln udr:seismic_retrofit udr.infrastructure_resilience sys:is_a
set.add name="ontology.urban_disaster_resilience" id="udr:seismic_retrofit"

def "udr:sensors" "Sensors for hazard monitoring."
ln udr:sensors udr.monitoring sys:is_a
set.add name="ontology.urban_disaster_resilience" id="udr:sensors"

def "udr:shelters" "Emergency shelters."
ln udr:shelters udr.evacuation sys:is_a
set.add name="ontology.urban_disaster_resilience" id="udr:shelters"

def "udr:tsunami" "Tsunami hazards."
ln udr:tsunami udr.hazards sys:is_a
set.add name="ontology.urban_disaster_resilience" id="udr:tsunami"

def "udr:typhoon" "Typhoons and extreme weather."
ln udr:typhoon udr.hazards sys:is_a
set.add name="ontology.urban_disaster_resilience" id="udr:typhoon"

def "udr:urban_fire" "Urban fires."
ln udr:urban_fire udr.hazards sys:is_a
set.add name="ontology.urban_disaster_resilience" id="udr:urban_fire"

def "udr:volunteer_networks" "Community volunteer networks."
ln udr:volunteer_networks udr.community sys:is_a
set.add name="ontology.urban_disaster_resilience" id="udr:volunteer_networks"
