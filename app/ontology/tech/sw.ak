# Akasha ontology — namespace: sw
# atoms: 32

def "sw.collective_behavior" "Collective behaviors emerging from local rules."
set.add name="ontology.swarm_control" id="sw.collective_behavior"

def "sw.consensus" "Consensus algorithms and agreement protocols."
set.add name="ontology.swarm_control" id="sw.consensus"

def "sw.cybernetics" "Cybernetic regulation and feedback."
set.add name="ontology.swarm_control" id="sw.cybernetics"

def "sw.distributed_control" "Distributed and decentralized control."
set.add name="ontology.swarm_control" id="sw.distributed_control"

def "sw.formation" "Formation control and coordinated movement."
set.add name="ontology.swarm_control" id="sw.formation"

def "sw.local_rules" "Local interaction rules for agents."
set.add name="ontology.swarm_control" id="sw.local_rules"

def "sw.micro_nano_swarm" "Micro/nano-scale swarm robotics."
set.add name="ontology.swarm_control" id="sw.micro_nano_swarm"

def "sw.multi_agent" "Multi-agent systems and coordination."
set.add name="ontology.swarm_control" id="sw.multi_agent"

def "sw:adaptive_control" "Adaptive swarm control."
ln sw:adaptive_control sw.cybernetics sys:is_a
set.add name="ontology.swarm_control" id="sw:adaptive_control"

def "sw:alignment" "Alignment with neighbors."
ln sw:alignment sw.local_rules sys:is_a
ln sw:alignment sw:flocking @enables
set.add name="ontology.swarm_control" id="sw:alignment"

def "sw:average_consensus" "Average consensus algorithms."
ln sw:average_consensus sw.consensus sys:is_a
set.add name="ontology.swarm_control" id="sw:average_consensus"

def "sw:behavior_based" "Behavior-based formation control."
ln sw:behavior_based sw.formation sys:is_a
set.add name="ontology.swarm_control" id="sw:behavior_based"

def "sw:bio_swarm" "Bio-hybrid micro/nano swarms."
ln sw:bio_swarm sw.micro_nano_swarm sys:is_a
set.add name="ontology.swarm_control" id="sw:bio_swarm"

def "sw:cohesion" "Cohesion toward group center."
ln sw:cohesion sw.local_rules sys:is_a
set.add name="ontology.swarm_control" id="sw:cohesion"

def "sw:cooperative_control" "Cooperative control strategies."
ln sw:cooperative_control sw.multi_agent sys:is_a
set.add name="ontology.swarm_control" id="sw:cooperative_control"

def "sw:decentralized_control" "Decentralized control without central authority."
ln sw:decentralized_control sw.distributed_control sys:is_a
set.add name="ontology.swarm_control" id="sw:decentralized_control"

def "sw:emergent_behavior" "Emergent behavior modeling."
ln sw:emergent_behavior sw.cybernetics sys:is_a
set.add name="ontology.swarm_control" id="sw:emergent_behavior"

def "sw:event_triggered" "Event-triggered distributed control."
ln sw:event_triggered sw.distributed_control sys:is_a
set.add name="ontology.swarm_control" id="sw:event_triggered"

def "sw:feedback" "Feedback loops in swarm systems."
ln sw:feedback sw.cybernetics sys:is_a
set.add name="ontology.swarm_control" id="sw:feedback"

def "sw:flocking" "Flocking behavior (Boids model)."
ln sw:flocking sw.collective_behavior sys:is_a
set.add name="ontology.swarm_control" id="sw:flocking"

def "sw:foraging" "Collective foraging and exploration."
ln sw:foraging sw.collective_behavior sys:is_a
set.add name="ontology.swarm_control" id="sw:foraging"

def "sw:leader_follower" "Leader–follower formation control."
ln sw:leader_follower sw.formation sys:is_a
ln sw:leader_follower sw:synchronization @influences
set.add name="ontology.swarm_control" id="sw:leader_follower"

def "sw:micro_swarm_robot" "Microscale swarm robots."
ln sw:micro_swarm_robot sw.micro_nano_swarm sys:is_a
ln sw:micro_swarm_robot sw:swarming @participates_in
set.add name="ontology.swarm_control" id="sw:micro_swarm_robot"

def "sw:multi_agent_path" "Multi-agent path planning."
ln sw:multi_agent_path sw.multi_agent sys:is_a
set.add name="ontology.swarm_control" id="sw:multi_agent_path"

def "sw:nano_swarm_robot" "Nanoscale swarm robots."
ln sw:nano_swarm_robot sw.micro_nano_swarm sys:is_a
set.add name="ontology.swarm_control" id="sw:nano_swarm_robot"

def "sw:separation" "Collision avoidance and separation."
ln sw:separation sw.local_rules sys:is_a
set.add name="ontology.swarm_control" id="sw:separation"

def "sw:stigmergy" "Stigmergy-based coordination."
ln sw:stigmergy sw.distributed_control sys:is_a
ln sw:stigmergy sw:foraging @supports
set.add name="ontology.swarm_control" id="sw:stigmergy"

def "sw:swarming" "Swarming and aggregation."
ln sw:swarming sw.collective_behavior sys:is_a
set.add name="ontology.swarm_control" id="sw:swarming"

def "sw:synchronization" "Synchronization of agents."
ln sw:synchronization sw.consensus sys:is_a
set.add name="ontology.swarm_control" id="sw:synchronization"

def "sw:task_allocation" "Distributed task allocation."
ln sw:task_allocation sw.multi_agent sys:is_a
set.add name="ontology.swarm_control" id="sw:task_allocation"

def "sw:virtual_structure" "Virtual structure method."
ln sw:virtual_structure sw.formation sys:is_a
set.add name="ontology.swarm_control" id="sw:virtual_structure"

def "sw:voting" "Distributed voting and agreement."
ln sw:voting sw.consensus sys:is_a
set.add name="ontology.swarm_control" id="sw:voting"
