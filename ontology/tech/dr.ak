# Akasha ontology — namespace: dr
# atoms: 36

def "dr.airframe" "Drone airframes and mechanical structure."
set.add name="ontology.drone_technology" id="dr.airframe"

def "dr.applications" "Applications across industries."
set.add name="ontology.drone_technology" id="dr.applications"

def "dr.autonomy" "Autonomy, navigation, and control."
set.add name="ontology.drone_technology" id="dr.autonomy"

def "dr.communication" "Communication links and protocols."
set.add name="ontology.drone_technology" id="dr.communication"

def "dr.operations" "Operations, mission planning, and logistics."
set.add name="ontology.drone_technology" id="dr.operations"

def "dr.propulsion" "Propulsion systems and power."
set.add name="ontology.drone_technology" id="dr.propulsion"

def "dr.regulation" "Regulations, safety, and airspace rules."
set.add name="ontology.drone_technology" id="dr.regulation"

def "dr.sensing" "Sensors and perception systems."
set.add name="ontology.drone_technology" id="dr.sensing"

def "dr:airspace_rules" "Airspace rules and classifications."
ln dr:airspace_rules dr.regulation sys:is_a
set.add name="ontology.drone_technology" id="dr:airspace_rules"

def "dr:bvlos" "Beyond Visual Line of Sight operations."
ln dr:bvlos dr.operations sys:is_a
set.add name="ontology.drone_technology" id="dr:bvlos"

def "dr:camera" "Optical cameras."
ln dr:camera dr.sensing sys:is_a
set.add name="ontology.drone_technology" id="dr:camera"

def "dr:certification" "Pilot and system certification."
ln dr:certification dr.regulation sys:is_a
set.add name="ontology.drone_technology" id="dr:certification"

def "dr:delivery" "Drone delivery and logistics."
ln dr:delivery dr.applications sys:is_a
ln dr:delivery dr:bvlos @requires
set.add name="ontology.drone_technology" id="dr:delivery"

def "dr:disaster_response" "Disaster response and search/rescue."
ln dr:disaster_response dr.applications sys:is_a
set.add name="ontology.drone_technology" id="dr:disaster_response"

def "dr:electric_motor" "Electric propulsion."
ln dr:electric_motor dr.propulsion sys:is_a
set.add name="ontology.drone_technology" id="dr:electric_motor"

def "dr:fixed_wing" "Fixed-wing drones."
ln dr:fixed_wing dr.airframe sys:is_a
set.add name="ontology.drone_technology" id="dr:fixed_wing"

def "dr:fuel_cell" "Fuel cell propulsion."
ln dr:fuel_cell dr.propulsion sys:is_a
set.add name="ontology.drone_technology" id="dr:fuel_cell"

def "dr:gcs" "Ground Control Stations."
ln dr:gcs dr.operations sys:is_a
set.add name="ontology.drone_technology" id="dr:gcs"

def "dr:gps" "GPS/GNSS modules."
ln dr:gps dr.sensing sys:is_a
set.add name="ontology.drone_technology" id="dr:gps"

def "dr:hybrid_propulsion" "Hybrid engine systems."
ln dr:hybrid_propulsion dr.propulsion sys:is_a
set.add name="ontology.drone_technology" id="dr:hybrid_propulsion"

def "dr:imu" "Inertial measurement units."
ln dr:imu dr.sensing sys:is_a
set.add name="ontology.drone_technology" id="dr:imu"

def "dr:inspection" "Infrastructure inspection."
ln dr:inspection dr.applications sys:is_a
set.add name="ontology.drone_technology" id="dr:inspection"

def "dr:lidar" "LiDAR sensors."
ln dr:lidar dr.sensing sys:is_a
ln dr:lidar dr:inspection @informs
set.add name="ontology.drone_technology" id="dr:lidar"

def "dr:lte" "LTE/4G/5G communication."
ln dr:lte dr.communication sys:is_a
set.add name="ontology.drone_technology" id="dr:lte"

def "dr:mesh_network" "Mesh networking for drone swarms."
ln dr:mesh_network dr.communication sys:is_a
ln dr:mesh_network dr:swarm_control @enables
set.add name="ontology.drone_technology" id="dr:mesh_network"

def "dr:mission_planning" "Mission planning and flight paths."
ln dr:mission_planning dr.operations sys:is_a
set.add name="ontology.drone_technology" id="dr:mission_planning"

def "dr:multirotor" "Multirotor drones (quad, hexa, octo)."
ln dr:multirotor dr.airframe sys:is_a
set.add name="ontology.drone_technology" id="dr:multirotor"

def "dr:obstacle_avoidance" "Obstacle avoidance."
ln dr:obstacle_avoidance dr.autonomy sys:is_a
set.add name="ontology.drone_technology" id="dr:obstacle_avoidance"

def "dr:pid_control" "PID-based flight control."
ln dr:pid_control dr.autonomy sys:is_a
set.add name="ontology.drone_technology" id="dr:pid_control"

def "dr:rf_link" "RF control links."
ln dr:rf_link dr.communication sys:is_a
set.add name="ontology.drone_technology" id="dr:rf_link"

def "dr:safety" "Safety requirements and fail-safes."
ln dr:safety dr.regulation sys:is_a
set.add name="ontology.drone_technology" id="dr:safety"

def "dr:slam" "SLAM for navigation."
ln dr:slam dr.autonomy sys:is_a
ln dr:slam dr:obstacle_avoidance @supports
set.add name="ontology.drone_technology" id="dr:slam"

def "dr:surveying" "Surveying and mapping."
ln dr:surveying dr.applications sys:is_a
set.add name="ontology.drone_technology" id="dr:surveying"

def "dr:swarm_control" "Swarm coordination for drones."
ln dr:swarm_control dr.autonomy sys:is_a
ln dr:swarm_control dr:mesh_network @uses
set.add name="ontology.drone_technology" id="dr:swarm_control"

def "dr:vtol" "VTOL hybrid drones."
ln dr:vtol dr.airframe sys:is_a
set.add name="ontology.drone_technology" id="dr:vtol"

def "dr:wifi" "Wi-Fi communication."
ln dr:wifi dr.communication sys:is_a
set.add name="ontology.drone_technology" id="dr:wifi"
