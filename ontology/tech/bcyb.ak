# Akasha ontology — namespace: bcyb
# atoms: 34

def "bcyb.brain_machine_interface" "Brain–machine and neuroprosthetic interfaces."
ln bcyb.brain_machine_interface ont.biological_cybernetics sys:part_of
set.add name="ontology.biological_cybernetics" id="bcyb.brain_machine_interface"

def "bcyb.homeostasis_adaptation" "Homeostasis, adaptation, and plasticity."
ln bcyb.homeostasis_adaptation ont.biological_cybernetics sys:part_of
set.add name="ontology.biological_cybernetics" id="bcyb.homeostasis_adaptation"

def "bcyb.modeling_methods" "Modeling and analysis methods in biological cybernetics."
ln bcyb.modeling_methods ont.biological_cybernetics sys:part_of
set.add name="ontology.biological_cybernetics" id="bcyb.modeling_methods"

def "bcyb.motor_control" "Motor control and coordination of movement."
ln bcyb.motor_control ont.biological_cybernetics sys:part_of
set.add name="ontology.biological_cybernetics" id="bcyb.motor_control"

def "bcyb.neural_control" "Neural control systems in the brain and spinal cord."
ln bcyb.neural_control ont.biological_cybernetics sys:part_of
set.add name="ontology.biological_cybernetics" id="bcyb.neural_control"

def "bcyb.physiological_regulation" "Physiological regulation of internal variables."
ln bcyb.physiological_regulation ont.biological_cybernetics sys:part_of
set.add name="ontology.biological_cybernetics" id="bcyb.physiological_regulation"

def "bcyb.sensory_systems" "Sensory systems and perception loops."
ln bcyb.sensory_systems ont.biological_cybernetics sys:part_of
set.add name="ontology.biological_cybernetics" id="bcyb.sensory_systems"

def "bcyb:allostasis" "Allostasis as predictive regulation under changing conditions."
ln bcyb:allostasis bcyb.homeostasis_adaptation sys:is_a
set.add name="ontology.biological_cybernetics" id="bcyb:allostasis"

def "bcyb:auditory_system" "Auditory sensory system."
ln bcyb:auditory_system bcyb.sensory_systems sys:is_a
set.add name="ontology.biological_cybernetics" id="bcyb:auditory_system"

def "bcyb:cardiovascular_regulation" "Regulation of blood pressure and heart rate."
ln bcyb:cardiovascular_regulation bcyb.physiological_regulation sys:is_a
set.add name="ontology.biological_cybernetics" id="bcyb:cardiovascular_regulation"

def "bcyb:central_pattern_generator" "Central pattern generators producing rhythmic activity."
ln bcyb:central_pattern_generator bcyb.neural_control sys:is_a
set.add name="ontology.biological_cybernetics" id="bcyb:central_pattern_generator"

def "bcyb:computational_neuroscience" "Computational models of neural systems."
ln bcyb:computational_neuroscience bcyb.modeling_methods sys:is_a
set.add name="ontology.biological_cybernetics" id="bcyb:computational_neuroscience"

def "bcyb:control_loop_model" "Control loop models of biological regulation."
ln bcyb:control_loop_model bcyb.modeling_methods sys:is_a
ln bcyb:control_loop_model bcyb.physiological_regulation @describes
set.add name="ontology.biological_cybernetics" id="bcyb:control_loop_model"

def "bcyb:cortical_motor_control" "Cortical control of voluntary movement."
ln bcyb:cortical_motor_control bcyb.motor_control sys:is_a
set.add name="ontology.biological_cybernetics" id="bcyb:cortical_motor_control"

def "bcyb:endocrine_regulation" "Hormonal regulation via endocrine system."
ln bcyb:endocrine_regulation bcyb.physiological_regulation sys:is_a
set.add name="ontology.biological_cybernetics" id="bcyb:endocrine_regulation"

def "bcyb:feedback_gain" "Feedback gain in biological control loops."
ln bcyb:feedback_gain bcyb.homeostasis_adaptation sys:is_a
set.add name="ontology.biological_cybernetics" id="bcyb:feedback_gain"

def "bcyb:invasive_bmi" "Invasive brain–machine interfaces using implanted electrodes."
ln bcyb:invasive_bmi bcyb.brain_machine_interface sys:is_a
set.add name="ontology.biological_cybernetics" id="bcyb:invasive_bmi"

def "bcyb:inverse_model" "Internal inverse models mapping desired outcomes to motor commands."
ln bcyb:inverse_model bcyb.motor_control sys:is_a
set.add name="ontology.biological_cybernetics" id="bcyb:inverse_model"

def "bcyb:motor_unit" "Motor unit linking motor neuron to muscle fibers."
ln bcyb:motor_unit bcyb.motor_control sys:is_a
set.add name="ontology.biological_cybernetics" id="bcyb:motor_unit"

def "bcyb:neural_network" "Biological neural networks and circuits."
ln bcyb:neural_network bcyb.neural_control sys:is_a
set.add name="ontology.biological_cybernetics" id="bcyb:neural_network"

def "bcyb:neural_plasticity" "Neural plasticity adjusting synaptic strengths."
ln bcyb:neural_plasticity bcyb.homeostasis_adaptation sys:is_a
ln bcyb:neural_plasticity bcyb:computational_neuroscience @modeled_by
set.add name="ontology.biological_cybernetics" id="bcyb:neural_plasticity"

def "bcyb:neuron" "Neuron as basic information processing unit."
ln bcyb:neuron bcyb.neural_control sys:is_a
set.add name="ontology.biological_cybernetics" id="bcyb:neuron"

def "bcyb:neuroprosthetic_control" "Neuroprosthetic devices controlled by neural activity."
ln bcyb:neuroprosthetic_control bcyb.brain_machine_interface sys:is_a
ln bcyb:neuroprosthetic_control bcyb.motor_control @replaces
set.add name="ontology.biological_cybernetics" id="bcyb:neuroprosthetic_control"

def "bcyb:noninvasive_bmi" "Non-invasive BMIs using EEG or other surface signals."
ln bcyb:noninvasive_bmi bcyb.brain_machine_interface sys:is_a
set.add name="ontology.biological_cybernetics" id="bcyb:noninvasive_bmi"

def "bcyb:reflex_loop" "Reflex loop as simple feedback circuit."
ln bcyb:reflex_loop bcyb.neural_control sys:is_a
ln bcyb:reflex_loop bcyb:motor_unit @connects
set.add name="ontology.biological_cybernetics" id="bcyb:reflex_loop"

def "bcyb:respiratory_control" "Control of breathing and gas exchange."
ln bcyb:respiratory_control bcyb.physiological_regulation sys:is_a
set.add name="ontology.biological_cybernetics" id="bcyb:respiratory_control"

def "bcyb:set_point" "Set point representing desired value of regulated variable."
ln bcyb:set_point bcyb.homeostasis_adaptation sys:is_a
set.add name="ontology.biological_cybernetics" id="bcyb:set_point"

def "bcyb:somatosensory_system" "Somatosensory system including touch and proprioception."
ln bcyb:somatosensory_system bcyb.sensory_systems sys:is_a
ln bcyb:somatosensory_system bcyb.motor_control @informs
set.add name="ontology.biological_cybernetics" id="bcyb:somatosensory_system"

def "bcyb:spinal_circuits" "Spinal circuits for basic motor patterns and reflexes."
ln bcyb:spinal_circuits bcyb.motor_control sys:is_a
set.add name="ontology.biological_cybernetics" id="bcyb:spinal_circuits"

def "bcyb:state_space_model" "State-space models of neural and physiological systems."
ln bcyb:state_space_model bcyb.modeling_methods sys:is_a
ln bcyb:state_space_model bcyb.neural_control @applied_to
set.add name="ontology.biological_cybernetics" id="bcyb:state_space_model"

def "bcyb:system_identification" "System identification from physiological data."
ln bcyb:system_identification bcyb.modeling_methods sys:is_a
set.add name="ontology.biological_cybernetics" id="bcyb:system_identification"

def "bcyb:thermoregulation" "Regulation of body temperature."
ln bcyb:thermoregulation bcyb.physiological_regulation sys:is_a
set.add name="ontology.biological_cybernetics" id="bcyb:thermoregulation"

def "bcyb:vestibular_system" "Vestibular system for balance and orientation."
ln bcyb:vestibular_system bcyb.sensory_systems sys:is_a
ln bcyb:vestibular_system bcyb.motor_control @stabilizes
set.add name="ontology.biological_cybernetics" id="bcyb:vestibular_system"

def "bcyb:visual_system" "Visual sensory system and processing pathways."
ln bcyb:visual_system bcyb.sensory_systems sys:is_a
set.add name="ontology.biological_cybernetics" id="bcyb:visual_system"
