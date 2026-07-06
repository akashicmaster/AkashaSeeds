# Akasha ontology — namespace: mas
# atoms: 29

def "mas.agent" "Agent models and properties."
set.add name="ontology.multi_agent_systems" id="mas.agent"

def "mas.applications" "Applications of multi-agent systems."
set.add name="ontology.multi_agent_systems" id="mas.applications"

def "mas.communication" "Communication protocols and information sharing."
set.add name="ontology.multi_agent_systems" id="mas.communication"

def "mas.coordination" "Coordination and cooperation strategies."
set.add name="ontology.multi_agent_systems" id="mas.coordination"

def "mas.decision" "Distributed decision-making."
set.add name="ontology.multi_agent_systems" id="mas.decision"

def "mas.interaction" "Interaction mechanisms among agents."
set.add name="ontology.multi_agent_systems" id="mas.interaction"

def "mas.learning" "Learning in multi-agent environments."
set.add name="ontology.multi_agent_systems" id="mas.learning"

def "mas:agent_comm_language" "Agent communication languages (FIPA ACL, KQML)."
ln mas:agent_comm_language mas.communication sys:is_a
set.add name="ontology.multi_agent_systems" id="mas:agent_comm_language"

def "mas:auction_mechanism" "Auction-based allocation and decision."
ln mas:auction_mechanism mas.decision sys:is_a
set.add name="ontology.multi_agent_systems" id="mas:auction_mechanism"

def "mas:blackboard" "Blackboard architecture for shared agent information."
ln mas:blackboard mas.communication sys:is_a
ln mas:blackboard mas:coalition_formation @supports
set.add name="ontology.multi_agent_systems" id="mas:blackboard"

def "mas:coalition_formation" "Coalition formation among agents."
ln mas:coalition_formation mas.coordination sys:is_a
set.add name="ontology.multi_agent_systems" id="mas:coalition_formation"

def "mas:competition" "Competitive interactions."
ln mas:competition mas.interaction sys:is_a
set.add name="ontology.multi_agent_systems" id="mas:competition"

def "mas:contract_net" "Contract net protocol for task allocation."
ln mas:contract_net mas.coordination sys:is_a
ln mas:contract_net mas:multi_robot_coordination @allocates
set.add name="ontology.multi_agent_systems" id="mas:contract_net"

def "mas:cooperation" "Cooperative interactions."
ln mas:cooperation mas.interaction sys:is_a
set.add name="ontology.multi_agent_systems" id="mas:cooperation"

def "mas:deliberative_agent" "Deliberative agents with planning."
ln mas:deliberative_agent mas.agent sys:is_a
set.add name="ontology.multi_agent_systems" id="mas:deliberative_agent"

def "mas:federated_learning" "Federated learning distributed across agents."
ln mas:federated_learning mas.learning sys:is_a
set.add name="ontology.multi_agent_systems" id="mas:federated_learning"

def "mas:game_theory" "Game-theoretic decision-making."
ln mas:game_theory mas.decision sys:is_a
ln mas:game_theory mas:competition @models
set.add name="ontology.multi_agent_systems" id="mas:game_theory"

def "mas:healthcare_mas" "MAS in healthcare and clinical decision support."
ln mas:healthcare_mas mas.applications sys:is_a
set.add name="ontology.multi_agent_systems" id="mas:healthcare_mas"

def "mas:hybrid_agent" "Hybrid reactive-deliberative agents."
ln mas:hybrid_agent mas.agent sys:is_a
set.add name="ontology.multi_agent_systems" id="mas:hybrid_agent"

def "mas:imitation_learning" "Imitation learning and behavior cloning in MAS."
ln mas:imitation_learning mas.learning sys:is_a
set.add name="ontology.multi_agent_systems" id="mas:imitation_learning"

def "mas:message_passing" "Peer-to-peer message passing between agents."
ln mas:message_passing mas.communication sys:is_a
set.add name="ontology.multi_agent_systems" id="mas:message_passing"

def "mas:mixed_motive" "Mixed-motive interactions (coopetitive)."
ln mas:mixed_motive mas.interaction sys:is_a
set.add name="ontology.multi_agent_systems" id="mas:mixed_motive"

def "mas:multi_agent_rl" "Multi-agent reinforcement learning."
ln mas:multi_agent_rl mas.learning sys:is_a
ln mas:multi_agent_rl mas:cooperation @optimizes
set.add name="ontology.multi_agent_systems" id="mas:multi_agent_rl"

def "mas:multi_robot_coordination" "Multi-robot coordination using MAS."
ln mas:multi_robot_coordination mas.applications sys:is_a
set.add name="ontology.multi_agent_systems" id="mas:multi_robot_coordination"

def "mas:negotiation" "Negotiation and bargaining among agents."
ln mas:negotiation mas.coordination sys:is_a
ln mas:negotiation mas:auction_mechanism @uses
set.add name="ontology.multi_agent_systems" id="mas:negotiation"

def "mas:reactive_agent" "Reactive agents with stimulus-response behavior."
ln mas:reactive_agent mas.agent sys:is_a
set.add name="ontology.multi_agent_systems" id="mas:reactive_agent"

def "mas:smart_grid_mas" "MAS for smart grid management and trading."
ln mas:smart_grid_mas mas.applications sys:is_a
set.add name="ontology.multi_agent_systems" id="mas:smart_grid_mas"

def "mas:supply_chain_mas" "MAS for supply chain optimization."
ln mas:supply_chain_mas mas.applications sys:is_a
set.add name="ontology.multi_agent_systems" id="mas:supply_chain_mas"

def "mas:voting_mechanism" "Voting-based collective decisions."
ln mas:voting_mechanism mas.decision sys:is_a
set.add name="ontology.multi_agent_systems" id="mas:voting_mechanism"
