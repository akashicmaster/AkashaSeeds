# Akasha ontology — namespace: ats
# atoms: 37

def "ats.automotive" "Automotive autonomous driving systems including ADAS and full self-driving."
set.add name="ontology.autonomous_transportation_systems" id="ats.automotive"

def "ats.communication" "Vehicle-to-everything (V2X) and train-to-ground communication."
set.add name="ontology.autonomous_transportation_systems" id="ats.communication"

def "ats.infrastructure" "Infrastructure supporting autonomous mobility."
set.add name="ontology.autonomous_transportation_systems" id="ats.infrastructure"

def "ats.perception" "Perception and environment understanding."
set.add name="ontology.autonomous_transportation_systems" id="ats.perception"

def "ats.planning" "Planning, prediction, and decision-making."
set.add name="ontology.autonomous_transportation_systems" id="ats.planning"

def "ats.railway" "Railway automation including ATO, ATC, CBTC, and driverless train systems."
set.add name="ontology.autonomous_transportation_systems" id="ats.railway"

def "ats.safety" "Functional safety, redundancy, and fail-operational design."
set.add name="ontology.autonomous_transportation_systems" id="ats.safety"

def "ats.sensing" "Sensors for autonomous vehicles and trains."
set.add name="ontology.autonomous_transportation_systems" id="ats.sensing"

def "ats:adas" "Advanced Driver Assistance Systems (L1–L2)."
ln ats:adas ats.automotive sys:is_a
set.add name="ontology.autonomous_transportation_systems" id="ats:adas"

def "ats:atc" "Automatic Train Control."
ln ats:atc ats.railway sys:is_a
set.add name="ontology.autonomous_transportation_systems" id="ats:atc"

def "ats:ato" "Automatic Train Operation (Grades of Automation)."
ln ats:ato ats.railway sys:is_a
set.add name="ontology.autonomous_transportation_systems" id="ats:ato"

def "ats:autonomous_driving" "Autonomous driving (L3–L5)."
ln ats:autonomous_driving ats.automotive sys:is_a
set.add name="ontology.autonomous_transportation_systems" id="ats:autonomous_driving"

def "ats:camera" "Camera sensing for perception."
ln ats:camera ats.sensing sys:is_a
set.add name="ontology.autonomous_transportation_systems" id="ats:camera"

def "ats:cbtc" "Communication-Based Train Control."
ln ats:cbtc ats.railway sys:is_a
ln ats:cbtc ats:rail_signaling @requires
set.add name="ontology.autonomous_transportation_systems" id="ats:cbtc"

def "ats:decision_making" "Decision-making and behavior planning."
ln ats:decision_making ats.planning sys:is_a
set.add name="ontology.autonomous_transportation_systems" id="ats:decision_making"

def "ats:en50126" "EN 50126/50128/50129 railway safety standards."
ln ats:en50126 ats.safety sys:is_a
ln ats:en50126 ats:atc @applies_to
set.add name="ontology.autonomous_transportation_systems" id="ats:en50126"

def "ats:hd_map" "High-definition maps for autonomous driving."
ln ats:hd_map ats.automotive sys:is_a
set.add name="ontology.autonomous_transportation_systems" id="ats:hd_map"

def "ats:hd_map_infrastructure" "HD map infrastructure for autonomous driving."
ln ats:hd_map_infrastructure ats.infrastructure sys:is_a
set.add name="ontology.autonomous_transportation_systems" id="ats:hd_map_infrastructure"

def "ats:imu" "Inertial Measurement Unit."
ln ats:imu ats.sensing sys:is_a
set.add name="ontology.autonomous_transportation_systems" id="ats:imu"

def "ats:interlocking" "Railway interlocking systems."
ln ats:interlocking ats.railway sys:is_a
set.add name="ontology.autonomous_transportation_systems" id="ats:interlocking"

def "ats:iso26262" "ISO 26262 functional safety for road vehicles."
ln ats:iso26262 ats.safety sys:is_a
ln ats:iso26262 ats:vehicle_ecu @applies_to
set.add name="ontology.autonomous_transportation_systems" id="ats:iso26262"

def "ats:lidar" "LiDAR sensing for 3D environment detection."
ln ats:lidar ats.sensing sys:is_a
ln ats:lidar ats:object_detection @informs
set.add name="ontology.autonomous_transportation_systems" id="ats:lidar"

def "ats:localization" "Localization using sensor fusion."
ln ats:localization ats.perception sys:is_a
ln ats:localization ats:trajectory_planning @supports
set.add name="ontology.autonomous_transportation_systems" id="ats:localization"

def "ats:object_detection" "Object detection and classification."
ln ats:object_detection ats.perception sys:is_a
set.add name="ontology.autonomous_transportation_systems" id="ats:object_detection"

def "ats:object_tracking" "Object tracking."
ln ats:object_tracking ats.perception sys:is_a
set.add name="ontology.autonomous_transportation_systems" id="ats:object_tracking"

def "ats:path_planning" "Path planning for autonomous vehicles and trains."
ln ats:path_planning ats.planning sys:is_a
set.add name="ontology.autonomous_transportation_systems" id="ats:path_planning"

def "ats:prediction" "Prediction of surrounding agents."
ln ats:prediction ats.planning sys:is_a
set.add name="ontology.autonomous_transportation_systems" id="ats:prediction"

def "ats:radar" "Radar sensing for velocity and distance."
ln ats:radar ats.sensing sys:is_a
set.add name="ontology.autonomous_transportation_systems" id="ats:radar"

def "ats:rail_signaling" "Railway signaling infrastructure."
ln ats:rail_signaling ats.infrastructure sys:is_a
set.add name="ontology.autonomous_transportation_systems" id="ats:rail_signaling"

def "ats:redundancy" "Redundancy and fail-operational design."
ln ats:redundancy ats.safety sys:is_a
set.add name="ontology.autonomous_transportation_systems" id="ats:redundancy"

def "ats:scene_understanding" "Scene understanding and semantic segmentation."
ln ats:scene_understanding ats.perception sys:is_a
set.add name="ontology.autonomous_transportation_systems" id="ats:scene_understanding"

def "ats:smart_road" "Smart road infrastructure with sensors and connectivity."
ln ats:smart_road ats.infrastructure sys:is_a
set.add name="ontology.autonomous_transportation_systems" id="ats:smart_road"

def "ats:train_to_ground" "Train-to-ground communication."
ln ats:train_to_ground ats.communication sys:is_a
set.add name="ontology.autonomous_transportation_systems" id="ats:train_to_ground"

def "ats:trajectory_planning" "Trajectory generation and optimization."
ln ats:trajectory_planning ats.planning sys:is_a
set.add name="ontology.autonomous_transportation_systems" id="ats:trajectory_planning"

def "ats:v2i" "Vehicle-to-infrastructure communication."
ln ats:v2i ats.communication sys:is_a
ln ats:v2i ats:decision_making @influences
set.add name="ontology.autonomous_transportation_systems" id="ats:v2i"

def "ats:v2v" "Vehicle-to-vehicle communication."
ln ats:v2v ats.communication sys:is_a
set.add name="ontology.autonomous_transportation_systems" id="ats:v2v"

def "ats:vehicle_ecu" "Vehicle ECUs for autonomous driving computation."
ln ats:vehicle_ecu ats.automotive sys:is_a
set.add name="ontology.autonomous_transportation_systems" id="ats:vehicle_ecu"
