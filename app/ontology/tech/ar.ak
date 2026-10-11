# Akasha ontology — namespace: ar
# atoms: 36

def "ar.autonomous_tractor" "Autonomous tractors and machinery."
set.add name="ontology.agri_robotics" id="ar.autonomous_tractor"

def "ar.field_robots" "Field robots for outdoor agriculture."
set.add name="ontology.agri_robotics" id="ar.field_robots"

def "ar.harvesting" "Harvesting robots and manipulators."
set.add name="ontology.agri_robotics" id="ar.harvesting"

def "ar.integration" "Integration with farm systems and automation."
set.add name="ontology.agri_robotics" id="ar.integration"

def "ar.mobility" "Mobility systems for agricultural terrain."
set.add name="ontology.agri_robotics" id="ar.mobility"

def "ar.perception" "Perception and sensing for agricultural robots."
set.add name="ontology.agri_robotics" id="ar.perception"

def "ar.planning" "Task planning and scheduling."
set.add name="ontology.agri_robotics" id="ar.planning"

def "ar.swarm" "Swarm-based agricultural robotics."
set.add name="ontology.agri_robotics" id="ar.swarm"

def "ar.weeding" "Weeding and crop-care robots."
set.add name="ontology.agri_robotics" id="ar.weeding"

def "ar:autonomous_drive" "Autonomous driving for tractors."
ln ar:autonomous_drive ar.autonomous_tractor sys:is_a
ln ar:autonomous_drive ar:route_planning @supports
set.add name="ontology.agri_robotics" id="ar:autonomous_drive"

def "ar:camera_vision" "Camera-based perception."
ln ar:camera_vision ar.perception sys:is_a
set.add name="ontology.agri_robotics" id="ar:camera_vision"

def "ar:fruit_picker" "Fruit-picking robots."
ln ar:fruit_picker ar.harvesting sys:is_a
set.add name="ontology.agri_robotics" id="ar:fruit_picker"

def "ar:greenhouse_link" "Integration with greenhouse control."
ln ar:greenhouse_link ar.integration sys:is_a
set.add name="ontology.agri_robotics" id="ar:greenhouse_link"

def "ar:irrigation_link" "Integration with irrigation automation."
ln ar:irrigation_link ar.integration sys:is_a
set.add name="ontology.agri_robotics" id="ar:irrigation_link"

def "ar:laser_weeding" "Laser-based weed removal."
ln ar:laser_weeding ar.weeding sys:is_a
ln ar:laser_weeding ar:swarm_weeding @enables
set.add name="ontology.agri_robotics" id="ar:laser_weeding"

def "ar:legged_robot" "Legged robots for uneven fields."
ln ar:legged_robot ar.mobility sys:is_a
set.add name="ontology.agri_robotics" id="ar:legged_robot"

def "ar:lidar" "LiDAR for mapping and navigation."
ln ar:lidar ar.perception sys:is_a
set.add name="ontology.agri_robotics" id="ar:lidar"

def "ar:mechanical_weeder" "Mechanical weeding robots."
ln ar:mechanical_weeder ar.weeding sys:is_a
set.add name="ontology.agri_robotics" id="ar:mechanical_weeder"

def "ar:ml_planning" "Machine learning for planning."
ln ar:ml_planning ar.planning sys:is_a
set.add name="ontology.agri_robotics" id="ar:ml_planning"

def "ar:multispectral" "Multispectral crop analysis."
ln ar:multispectral ar.perception sys:is_a
ln ar:multispectral ar:precision_harvest @informs
set.add name="ontology.agri_robotics" id="ar:multispectral"

def "ar:plowing_robot" "Automated plowing systems."
ln ar:plowing_robot ar.autonomous_tractor sys:is_a
set.add name="ontology.agri_robotics" id="ar:plowing_robot"

def "ar:precision_harvest" "Precision harvesting systems."
ln ar:precision_harvest ar.harvesting sys:is_a
set.add name="ontology.agri_robotics" id="ar:precision_harvest"

def "ar:route_planning" "Route planning for field tasks."
ln ar:route_planning ar.planning sys:is_a
set.add name="ontology.agri_robotics" id="ar:route_planning"

def "ar:row_following_robot" "Row-following field robots."
ln ar:row_following_robot ar.field_robots sys:is_a
set.add name="ontology.agri_robotics" id="ar:row_following_robot"

def "ar:scouting_robot" "Robots for scouting and crop monitoring."
ln ar:scouting_robot ar.field_robots sys:is_a
ln ar:scouting_robot ar:ml_planning @feeds
set.add name="ontology.agri_robotics" id="ar:scouting_robot"

def "ar:smart_implement" "Smart implements and attachments."
ln ar:smart_implement ar.autonomous_tractor sys:is_a
set.add name="ontology.agri_robotics" id="ar:smart_implement"

def "ar:spraying_robot" "Ground-based spraying robots."
ln ar:spraying_robot ar.field_robots sys:is_a
set.add name="ontology.agri_robotics" id="ar:spraying_robot"

def "ar:supply_chain_link" "Integration with supply chain systems."
ln ar:supply_chain_link ar.integration sys:is_a
set.add name="ontology.agri_robotics" id="ar:supply_chain_link"

def "ar:swarm_harvest" "Cooperative harvesting."
ln ar:swarm_harvest ar.swarm sys:is_a
set.add name="ontology.agri_robotics" id="ar:swarm_harvest"

def "ar:swarm_scouting" "Swarm scouting and mapping."
ln ar:swarm_scouting ar.swarm sys:is_a
set.add name="ontology.agri_robotics" id="ar:swarm_scouting"

def "ar:swarm_weeding" "Swarm-based weeding robots."
ln ar:swarm_weeding ar.swarm sys:is_a
set.add name="ontology.agri_robotics" id="ar:swarm_weeding"

def "ar:task_allocation" "Task allocation among robots."
ln ar:task_allocation ar.planning sys:is_a
ln ar:task_allocation ar:swarm_harvest @allocates
set.add name="ontology.agri_robotics" id="ar:task_allocation"

def "ar:tracked_robot" "Tracked robots for rough terrain."
ln ar:tracked_robot ar.mobility sys:is_a
set.add name="ontology.agri_robotics" id="ar:tracked_robot"

def "ar:vegetable_harvester" "Vegetable harvesting robots."
ln ar:vegetable_harvester ar.harvesting sys:is_a
set.add name="ontology.agri_robotics" id="ar:vegetable_harvester"

def "ar:vision_weeding" "Vision-based selective weeding."
ln ar:vision_weeding ar.weeding sys:is_a
set.add name="ontology.agri_robotics" id="ar:vision_weeding"

def "ar:wheeled_robot" "Wheeled agricultural robots."
ln ar:wheeled_robot ar.mobility sys:is_a
set.add name="ontology.agri_robotics" id="ar:wheeled_robot"
