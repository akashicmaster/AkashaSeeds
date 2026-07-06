# Akasha ontology — namespace: cyb
# atoms: 28

def "cyb.adaptation" "Adaptation, learning, and homeostasis."
ln cyb.adaptation ont.cybernetics sys:part_of
set.add name="ontology.cybernetics" id="cyb.adaptation"

def "cyb.biological" "Biological cybernetics including neural control and physiological regulation."
ln cyb.biological ont.cybernetics sys:part_of
set.add name="ontology.cybernetics" id="cyb.biological"

def "cyb.control" "Control and feedback systems across mechanical, biological, and social domains."
ln cyb.control ont.cybernetics sys:part_of
set.add name="ontology.cybernetics" id="cyb.control"

def "cyb.information" "Communication, information theory, and signal processing."
ln cyb.information ont.cybernetics sys:part_of
set.add name="ontology.cybernetics" id="cyb.information"

def "cyb.machine" "Machine cybernetics including robotics, automation, and AI."
ln cyb.machine ont.cybernetics sys:part_of
set.add name="ontology.cybernetics" id="cyb.machine"

def "cyb.self_organization" "Self-organization and emergent behavior in complex systems."
ln cyb.self_organization ont.cybernetics sys:part_of
set.add name="ontology.cybernetics" id="cyb.self_organization"

def "cyb.social" "Social cybernetics including organizational and societal feedback systems."
ln cyb.social ont.cybernetics sys:part_of
set.add name="ontology.cybernetics" id="cyb.social"

def "cyb:adaptive_control" "Adaptive control adjusting parameters in real time."
ln cyb:adaptive_control cyb.adaptation sys:is_a
set.add name="ontology.cybernetics" id="cyb:adaptive_control"

def "cyb:ai_systems" "AI systems as cybernetic agents."
ln cyb:ai_systems cyb.machine sys:is_a
set.add name="ontology.cybernetics" id="cyb:ai_systems"

def "cyb:autonomous_systems" "Autonomous systems with closed-loop decision-making."
ln cyb:autonomous_systems cyb.machine sys:is_a
set.add name="ontology.cybernetics" id="cyb:autonomous_systems"

def "cyb:biofeedback" "Biofeedback mechanisms."
ln cyb:biofeedback cyb.biological sys:is_a
set.add name="ontology.cybernetics" id="cyb:biofeedback"

def "cyb:communication_system" "Communication channels and encoding."
ln cyb:communication_system cyb.information sys:is_a
set.add name="ontology.cybernetics" id="cyb:communication_system"

def "cyb:economic_feedback" "Feedback loops in economic systems."
ln cyb:economic_feedback cyb.social sys:is_a
set.add name="ontology.cybernetics" id="cyb:economic_feedback"

def "cyb:emergence" "Emergent behavior arising from local interactions."
ln cyb:emergence cyb.self_organization sys:is_a
set.add name="ontology.cybernetics" id="cyb:emergence"

def "cyb:entropy_minimization" "Entropy and order formation in systems."
ln cyb:entropy_minimization cyb.self_organization sys:is_a
set.add name="ontology.cybernetics" id="cyb:entropy_minimization"

def "cyb:feedback" "Feedback loops regulating system behavior."
ln cyb:feedback cyb.control sys:is_a
ln cyb:feedback cyb:homeostasis @enables
set.add name="ontology.cybernetics" id="cyb:feedback"

def "cyb:feedforward" "Feedforward control anticipating disturbances."
ln cyb:feedforward cyb.control sys:is_a
set.add name="ontology.cybernetics" id="cyb:feedforward"

def "cyb:hierarchical_control" "Hierarchical control architectures."
ln cyb:hierarchical_control cyb.control sys:is_a
set.add name="ontology.cybernetics" id="cyb:hierarchical_control"

def "cyb:homeostasis" "Homeostatic regulation."
ln cyb:homeostasis cyb.adaptation sys:is_a
set.add name="ontology.cybernetics" id="cyb:homeostasis"

def "cyb:information_theory" "Shannon information theory."
ln cyb:information_theory cyb.information sys:is_a
ln cyb:information_theory cyb:communication_system @defines
set.add name="ontology.cybernetics" id="cyb:information_theory"

def "cyb:learning" "Learning mechanisms in biological and artificial systems."
ln cyb:learning cyb.adaptation sys:is_a
set.add name="ontology.cybernetics" id="cyb:learning"

def "cyb:neural_control" "Neural control systems and brain-body coordination."
ln cyb:neural_control cyb.biological sys:is_a
ln cyb:neural_control cyb:learning @supports
set.add name="ontology.cybernetics" id="cyb:neural_control"

def "cyb:organizational_control" "Control and communication in organizations."
ln cyb:organizational_control cyb.social sys:is_a
set.add name="ontology.cybernetics" id="cyb:organizational_control"

def "cyb:physiological_regulation" "Physiological regulation systems."
ln cyb:physiological_regulation cyb.biological sys:is_a
set.add name="ontology.cybernetics" id="cyb:physiological_regulation"

def "cyb:robotics" "Robotics as applied cybernetics."
ln cyb:robotics cyb.machine sys:is_a
ln cyb:robotics cyb.control @requires
set.add name="ontology.cybernetics" id="cyb:robotics"

def "cyb:signal_processing" "Signal processing for communication and control."
ln cyb:signal_processing cyb.information sys:is_a
set.add name="ontology.cybernetics" id="cyb:signal_processing"

def "cyb:social_systems" "Social systems as cybernetic structures."
ln cyb:social_systems cyb.social sys:is_a
set.add name="ontology.cybernetics" id="cyb:social_systems"

def "cyb:swarm_dynamics" "Swarm intelligence and distributed coordination."
ln cyb:swarm_dynamics cyb.self_organization sys:is_a
ln cyb:swarm_dynamics cyb:autonomous_systems @influences
set.add name="ontology.cybernetics" id="cyb:swarm_dynamics"
