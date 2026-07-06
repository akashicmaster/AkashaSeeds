# Akasha ontology — namespace: ce
# atoms: 32

def "ce.construction" "Construction engineering and project management."
set.add name="ontology.civil_engineering" id="ce.construction"

def "ce.environmental" "Environmental engineering and pollution control."
set.add name="ontology.civil_engineering" id="ce.environmental"

def "ce.geotechnical" "Geotechnical engineering and soil mechanics."
set.add name="ontology.civil_engineering" id="ce.geotechnical"

def "ce.structures" "Civil structures such as bridges and dams."
set.add name="ontology.civil_engineering" id="ce.structures"

def "ce.surveying" "Surveying, geomatics, and mapping."
set.add name="ontology.civil_engineering" id="ce.surveying"

def "ce.transportation" "Transportation engineering and roadway systems."
set.add name="ontology.civil_engineering" id="ce.transportation"

def "ce.urban_systems" "Integration with urban infrastructure and planning."
set.add name="ontology.civil_engineering" id="ce.urban_systems"

def "ce.water_resources" "Water resources and hydraulic engineering."
set.add name="ontology.civil_engineering" id="ce.water_resources"

def "ce:air_quality" "Air quality engineering."
ln ce:air_quality ce.environmental sys:is_a
set.add name="ontology.civil_engineering" id="ce:air_quality"

def "ce:bridge_engineering" "Bridge design and analysis."
ln ce:bridge_engineering ce.structures sys:is_a
ln ce:bridge_engineering ce:traffic_engineering @supports
set.add name="ontology.civil_engineering" id="ce:bridge_engineering"

def "ce:coastal_engineering" "Coastal engineering and erosion control."
ln ce:coastal_engineering ce.water_resources sys:is_a
set.add name="ontology.civil_engineering" id="ce:coastal_engineering"

def "ce:construction_methods" "Construction methods and equipment."
ln ce:construction_methods ce.construction sys:is_a
set.add name="ontology.civil_engineering" id="ce:construction_methods"

def "ce:construction_safety" "Construction safety engineering."
ln ce:construction_safety ce.construction sys:is_a
set.add name="ontology.civil_engineering" id="ce:construction_safety"

def "ce:dam_engineering" "Dam and reservoir structures."
ln ce:dam_engineering ce.structures sys:is_a
set.add name="ontology.civil_engineering" id="ce:dam_engineering"

def "ce:foundation_design" "Foundation design (shallow, deep)."
ln ce:foundation_design ce.geotechnical sys:is_a
set.add name="ontology.civil_engineering" id="ce:foundation_design"

def "ce:gis" "Geographic Information Systems."
ln ce:gis ce.surveying sys:is_a
ln ce:gis ce:urban_planning @enables
set.add name="ontology.civil_engineering" id="ce:gis"

def "ce:gps_survey" "GPS and GNSS surveying."
ln ce:gps_survey ce.surveying sys:is_a
set.add name="ontology.civil_engineering" id="ce:gps_survey"

def "ce:hydrology" "Hydrology and watershed modeling."
ln ce:hydrology ce.water_resources sys:is_a
set.add name="ontology.civil_engineering" id="ce:hydrology"

def "ce:infrastructure_networks" "Integration with water, power, and transport networks."
ln ce:infrastructure_networks ce.urban_systems sys:is_a
set.add name="ontology.civil_engineering" id="ce:infrastructure_networks"

def "ce:lidar_mapping" "LiDAR mapping and 3D scanning."
ln ce:lidar_mapping ce.surveying sys:is_a
set.add name="ontology.civil_engineering" id="ce:lidar_mapping"

def "ce:project_management" "Construction project management."
ln ce:project_management ce.construction sys:is_a
ln ce:project_management ce:construction_methods @coordinates
set.add name="ontology.civil_engineering" id="ce:project_management"

def "ce:railway_engineering" "Railway engineering."
ln ce:railway_engineering ce.transportation sys:is_a
set.add name="ontology.civil_engineering" id="ce:railway_engineering"

def "ce:resilience" "Infrastructure resilience and disaster mitigation."
ln ce:resilience ce.urban_systems sys:is_a
set.add name="ontology.civil_engineering" id="ce:resilience"

def "ce:river_engineering" "River engineering and flood control."
ln ce:river_engineering ce.water_resources sys:is_a
ln ce:river_engineering ce:hydrology @influences
set.add name="ontology.civil_engineering" id="ce:river_engineering"

def "ce:roadway_design" "Roadway geometric design."
ln ce:roadway_design ce.transportation sys:is_a
set.add name="ontology.civil_engineering" id="ce:roadway_design"

def "ce:slope_stability" "Slope stability and landslide analysis."
ln ce:slope_stability ce.geotechnical sys:is_a
ln ce:slope_stability ce:resilience @informs
set.add name="ontology.civil_engineering" id="ce:slope_stability"

def "ce:soil_mechanics" "Soil mechanics and foundation behavior."
ln ce:soil_mechanics ce.geotechnical sys:is_a
set.add name="ontology.civil_engineering" id="ce:soil_mechanics"

def "ce:traffic_engineering" "Traffic engineering and operations."
ln ce:traffic_engineering ce.transportation sys:is_a
set.add name="ontology.civil_engineering" id="ce:traffic_engineering"

def "ce:tunnel_engineering" "Tunnel and underground structures."
ln ce:tunnel_engineering ce.structures sys:is_a
set.add name="ontology.civil_engineering" id="ce:tunnel_engineering"

def "ce:urban_planning" "Urban planning and land use."
ln ce:urban_planning ce.urban_systems sys:is_a
set.add name="ontology.civil_engineering" id="ce:urban_planning"

def "ce:waste_management" "Solid waste and recycling systems."
ln ce:waste_management ce.environmental sys:is_a
set.add name="ontology.civil_engineering" id="ce:waste_management"

def "ce:water_quality" "Water quality and treatment."
ln ce:water_quality ce.environmental sys:is_a
set.add name="ontology.civil_engineering" id="ce:water_quality"
