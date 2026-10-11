# Akasha ontology — namespace: adc
# atoms: 30

def "adc.applications" "Applications of autonomous decentralized control."
set.add name="ontology.autonomous_decentralized_control" id="adc.applications"

def "adc.consensus" "Consensus and agreement mechanisms."
set.add name="ontology.autonomous_decentralized_control" id="adc.consensus"

def "adc.cyber_physical" "Cyber-physical integration and networks."
set.add name="ontology.autonomous_decentralized_control" id="adc.cyber_physical"

def "adc.distributed_coordination" "Distributed coordination among controllers."
set.add name="ontology.autonomous_decentralized_control" id="adc.distributed_coordination"

def "adc.fault_tolerance" "Fault tolerance and resilience."
set.add name="ontology.autonomous_decentralized_control" id="adc.fault_tolerance"

def "adc.local_control" "Local controllers and agent-level autonomy."
set.add name="ontology.autonomous_decentralized_control" id="adc.local_control"

def "adc.optimization" "Distributed optimization and resource allocation."
set.add name="ontology.autonomous_decentralized_control" id="adc.optimization"

def "adc:average_consensus" "Average consensus algorithms."
ln adc:average_consensus adc.consensus sys:is_a
ln adc:average_consensus adc:power_systems @supports
set.add name="ontology.autonomous_decentralized_control" id="adc:average_consensus"

def "adc:building_automation" "Building and home automation systems."
ln adc:building_automation adc.applications sys:is_a
set.add name="ontology.autonomous_decentralized_control" id="adc:building_automation"

def "adc:control_network" "Networks connecting distributed controllers."
ln adc:control_network adc.cyber_physical sys:is_a
set.add name="ontology.autonomous_decentralized_control" id="adc:control_network"

def "adc:distributed_optimization" "Distributed optimization algorithms."
ln adc:distributed_optimization adc.optimization sys:is_a
ln adc:distributed_optimization adc:resource_allocation @optimizes
set.add name="ontology.autonomous_decentralized_control" id="adc:distributed_optimization"

def "adc:edge_control" "Edge computing for local control."
ln adc:edge_control adc.cyber_physical sys:is_a
ln adc:edge_control adc:iot_integration @hosts
set.add name="ontology.autonomous_decentralized_control" id="adc:edge_control"

def "adc:event_triggered" "Event-triggered distributed control."
ln adc:event_triggered adc.distributed_coordination sys:is_a
ln adc:event_triggered adc:traffic_control @applied_to
set.add name="ontology.autonomous_decentralized_control" id="adc:event_triggered"

def "adc:fault_detection" "Fault detection and diagnosis."
ln adc:fault_detection adc.fault_tolerance sys:is_a
set.add name="ontology.autonomous_decentralized_control" id="adc:fault_detection"

def "adc:hierarchical_coordination" "Hierarchical but decentralized coordination."
ln adc:hierarchical_coordination adc.distributed_coordination sys:is_a
set.add name="ontology.autonomous_decentralized_control" id="adc:hierarchical_coordination"

def "adc:iot_integration" "Integration with IoT devices and sensors."
ln adc:iot_integration adc.cyber_physical sys:is_a
set.add name="ontology.autonomous_decentralized_control" id="adc:iot_integration"

def "adc:load_balancing" "Load balancing in distributed systems."
ln adc:load_balancing adc.optimization sys:is_a
set.add name="ontology.autonomous_decentralized_control" id="adc:load_balancing"

def "adc:local_model_based" "Model-based local controllers (MPC, etc.)."
ln adc:local_model_based adc.local_control sys:is_a
set.add name="ontology.autonomous_decentralized_control" id="adc:local_model_based"

def "adc:local_pid" "Local PID and feedback controllers."
ln adc:local_pid adc.local_control sys:is_a
set.add name="ontology.autonomous_decentralized_control" id="adc:local_pid"

def "adc:local_rule_based" "Rule-based local control policies."
ln adc:local_rule_based adc.local_control sys:is_a
set.add name="ontology.autonomous_decentralized_control" id="adc:local_rule_based"

def "adc:manufacturing_systems" "Decentralized manufacturing and production."
ln adc:manufacturing_systems adc.applications sys:is_a
set.add name="ontology.autonomous_decentralized_control" id="adc:manufacturing_systems"

def "adc:multi_robot_systems" "Multi-robot and swarm control systems."
ln adc:multi_robot_systems adc.applications sys:is_a
set.add name="ontology.autonomous_decentralized_control" id="adc:multi_robot_systems"

def "adc:peer_to_peer" "Peer-to-peer coordination among controllers."
ln adc:peer_to_peer adc.distributed_coordination sys:is_a
ln adc:peer_to_peer adc:multi_robot_systems @used_in
set.add name="ontology.autonomous_decentralized_control" id="adc:peer_to_peer"

def "adc:power_systems" "Power grids and smart grid control."
ln adc:power_systems adc.applications sys:is_a
set.add name="ontology.autonomous_decentralized_control" id="adc:power_systems"

def "adc:reconfiguration" "Reconfiguration after failures."
ln adc:reconfiguration adc.fault_tolerance sys:is_a
set.add name="ontology.autonomous_decentralized_control" id="adc:reconfiguration"

def "adc:redundancy" "Redundancy in controllers and communication."
ln adc:redundancy adc.fault_tolerance sys:is_a
set.add name="ontology.autonomous_decentralized_control" id="adc:redundancy"

def "adc:resource_allocation" "Resource allocation among nodes."
ln adc:resource_allocation adc.optimization sys:is_a
set.add name="ontology.autonomous_decentralized_control" id="adc:resource_allocation"

def "adc:synchronization" "Synchronization of states among nodes."
ln adc:synchronization adc.consensus sys:is_a
set.add name="ontology.autonomous_decentralized_control" id="adc:synchronization"

def "adc:traffic_control" "Traffic and transportation network control."
ln adc:traffic_control adc.applications sys:is_a
set.add name="ontology.autonomous_decentralized_control" id="adc:traffic_control"

def "adc:voting" "Voting-based decision mechanisms."
ln adc:voting adc.consensus sys:is_a
set.add name="ontology.autonomous_decentralized_control" id="adc:voting"
