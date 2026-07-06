# Akasha ontology — namespace: sr
# atoms: 33

def "sr.applications" "Applications of swarm robotics."
set.add name="ontology.swarm_robotics" id="sr.applications"

def "sr.collective_behavior" "Collective behaviors emerging from interactions."
set.add name="ontology.swarm_robotics" id="sr.collective_behavior"

def "sr.communication" "Communication and information sharing."
set.add name="ontology.swarm_robotics" id="sr.communication"

def "sr.distributed_control" "Distributed control and coordination."
set.add name="ontology.swarm_robotics" id="sr.distributed_control"

def "sr.formation" "Formation control for robot groups."
set.add name="ontology.swarm_robotics" id="sr.formation"

def "sr.local_rules" "Local interaction rules for robots."
set.add name="ontology.swarm_robotics" id="sr.local_rules"

def "sr.platforms" "Robot platforms used in swarms."
set.add name="ontology.swarm_robotics" id="sr.platforms"

def "sr.task_allocation" "Distributed task allocation and scheduling."
set.add name="ontology.swarm_robotics" id="sr.task_allocation"

def "sr:alignment" "Alignment with neighbors."
ln sr:alignment sr.local_rules sys:is_a
ln sr:alignment sr:flocking @enables
set.add name="ontology.swarm_robotics" id="sr:alignment"

def "sr:auction_based" "Auction-based task allocation."
ln sr:auction_based sr.task_allocation sys:is_a
ln sr:auction_based sr:swarm_delivery @allocates
set.add name="ontology.swarm_robotics" id="sr:auction_based"

def "sr:behavior_based" "Behavior-based formation control."
ln sr:behavior_based sr.formation sys:is_a
set.add name="ontology.swarm_robotics" id="sr:behavior_based"

def "sr:ble_comm" "BLE communication for micro swarms."
ln sr:ble_comm sr.communication sys:is_a
set.add name="ontology.swarm_robotics" id="sr:ble_comm"

def "sr:cohesion" "Cohesion toward group center."
ln sr:cohesion sr.local_rules sys:is_a
set.add name="ontology.swarm_robotics" id="sr:cohesion"

def "sr:decentralized_control" "Decentralized control without central authority."
ln sr:decentralized_control sr.distributed_control sys:is_a
set.add name="ontology.swarm_robotics" id="sr:decentralized_control"

def "sr:drone_swarm" "Aerial drone swarms."
ln sr:drone_swarm sr.platforms sys:is_a
set.add name="ontology.swarm_robotics" id="sr:drone_swarm"

def "sr:event_triggered" "Event-triggered control."
ln sr:event_triggered sr.distributed_control sys:is_a
set.add name="ontology.swarm_robotics" id="sr:event_triggered"

def "sr:exploration" "Collective exploration."
ln sr:exploration sr.collective_behavior sys:is_a
set.add name="ontology.swarm_robotics" id="sr:exploration"

def "sr:flocking" "Flocking behavior."
ln sr:flocking sr.collective_behavior sys:is_a
set.add name="ontology.swarm_robotics" id="sr:flocking"

def "sr:ground_robot_swarm" "Ground robot swarms."
ln sr:ground_robot_swarm sr.platforms sys:is_a
set.add name="ontology.swarm_robotics" id="sr:ground_robot_swarm"

def "sr:infrastructure_inspection" "Infrastructure inspection."
ln sr:infrastructure_inspection sr.applications sys:is_a
set.add name="ontology.swarm_robotics" id="sr:infrastructure_inspection"

def "sr:leader_follower" "Leader–follower formation."
ln sr:leader_follower sr.formation sys:is_a
set.add name="ontology.swarm_robotics" id="sr:leader_follower"

def "sr:mapping" "Large-area mapping."
ln sr:mapping sr.applications sys:is_a
set.add name="ontology.swarm_robotics" id="sr:mapping"

def "sr:market_based" "Market-based coordination."
ln sr:market_based sr.task_allocation sys:is_a
set.add name="ontology.swarm_robotics" id="sr:market_based"

def "sr:mesh_network" "Mesh networking for robot swarms."
ln sr:mesh_network sr.communication sys:is_a
ln sr:mesh_network sr:drone_swarm @supports
set.add name="ontology.swarm_robotics" id="sr:mesh_network"

def "sr:micro_swarm" "Microscale swarm robots."
ln sr:micro_swarm sr.platforms sys:is_a
ln sr:micro_swarm sr:exploration @participates_in
set.add name="ontology.swarm_robotics" id="sr:micro_swarm"

def "sr:role_assignment" "Role assignment in robot groups."
ln sr:role_assignment sr.task_allocation sys:is_a
set.add name="ontology.swarm_robotics" id="sr:role_assignment"

def "sr:search_rescue" "Search and rescue operations."
ln sr:search_rescue sr.applications sys:is_a
set.add name="ontology.swarm_robotics" id="sr:search_rescue"

def "sr:separation" "Collision avoidance."
ln sr:separation sr.local_rules sys:is_a
set.add name="ontology.swarm_robotics" id="sr:separation"

def "sr:stigmergy" "Stigmergy-based coordination."
ln sr:stigmergy sr.distributed_control sys:is_a
ln sr:stigmergy sr:mapping @influences
set.add name="ontology.swarm_robotics" id="sr:stigmergy"

def "sr:swarm_delivery" "Swarm-based delivery."
ln sr:swarm_delivery sr.applications sys:is_a
set.add name="ontology.swarm_robotics" id="sr:swarm_delivery"

def "sr:swarming" "Swarming and aggregation."
ln sr:swarming sr.collective_behavior sys:is_a
set.add name="ontology.swarm_robotics" id="sr:swarming"

def "sr:uwb_comm" "UWB for localization and communication."
ln sr:uwb_comm sr.communication sys:is_a
set.add name="ontology.swarm_robotics" id="sr:uwb_comm"

def "sr:virtual_structure" "Virtual structure method."
ln sr:virtual_structure sr.formation sys:is_a
set.add name="ontology.swarm_robotics" id="sr:virtual_structure"
