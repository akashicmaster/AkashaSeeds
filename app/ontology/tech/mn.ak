# Akasha ontology — namespace: mn
# atoms: 36

def "mn.actuators" "Micro/nano actuators and motion systems."
set.add name="ontology.micro_nano_machines" id="mn.actuators"

def "mn.bio" "Biomedical micro/nano machines."
set.add name="ontology.micro_nano_machines" id="mn.bio"

def "mn.control" "Control, feedback, and cybernetic regulation."
set.add name="ontology.micro_nano_machines" id="mn.control"

def "mn.fabrication" "Micro/nano fabrication and lithography."
set.add name="ontology.micro_nano_machines" id="mn.fabrication"

def "mn.integration" "Integration with macro systems and IoT."
set.add name="ontology.micro_nano_machines" id="mn.integration"

def "mn.materials" "Materials for micro/nano machines."
set.add name="ontology.micro_nano_machines" id="mn.materials"

def "mn.mems" "Micro-Electro-Mechanical Systems (MEMS)."
set.add name="ontology.micro_nano_machines" id="mn.mems"

def "mn.nems" "Nano-Electro-Mechanical Systems (NEMS)."
set.add name="ontology.micro_nano_machines" id="mn.nems"

def "mn.sensing" "Micro/nano sensors and detection systems."
set.add name="ontology.micro_nano_machines" id="mn.sensing"

def "mn:ai_control" "AI-driven control and prediction."
ln mn:ai_control mn.control sys:is_a
ln mn:ai_control mn:thermal_actuator @optimizes
ln mn:ai_control sw:adaptive_control @enhances
set.add name="ontology.micro_nano_machines" id="mn:ai_control"

def "mn:bio_sensor" "Biosensors and chemical sensors."
ln mn:bio_sensor mn.sensing sys:is_a
ln mn:bio_sensor mn:drug_delivery @informs
set.add name="ontology.micro_nano_machines" id="mn:bio_sensor"

def "mn:bio_system_integration" "Integration with biological systems."
ln mn:bio_system_integration mn.integration sys:is_a
set.add name="ontology.micro_nano_machines" id="mn:bio_system_integration"

def "mn:cell_manipulation" "Cell manipulation microtools."
ln mn:cell_manipulation mn.bio sys:is_a
set.add name="ontology.micro_nano_machines" id="mn:cell_manipulation"

def "mn:deposition" "Thin-film deposition (CVD, PVD, ALD)."
ln mn:deposition mn.fabrication sys:is_a
set.add name="ontology.micro_nano_machines" id="mn:deposition"

def "mn:diagnostic_nanodevice" "Diagnostic nanodevices."
ln mn:diagnostic_nanodevice mn.bio sys:is_a
set.add name="ontology.micro_nano_machines" id="mn:diagnostic_nanodevice"

def "mn:drug_delivery" "Targeted drug delivery nanomachines."
ln mn:drug_delivery mn.bio sys:is_a
set.add name="ontology.micro_nano_machines" id="mn:drug_delivery"

def "mn:electrostatic_actuator" "Electrostatic actuators."
ln mn:electrostatic_actuator mn.actuators sys:is_a
set.add name="ontology.micro_nano_machines" id="mn:electrostatic_actuator"

def "mn:etching" "Etching processes (dry/wet)."
ln mn:etching mn.fabrication sys:is_a
set.add name="ontology.micro_nano_machines" id="mn:etching"

def "mn:feedback_control" "Feedback control for micro/nano systems."
ln mn:feedback_control mn.control sys:is_a
set.add name="ontology.micro_nano_machines" id="mn:feedback_control"

def "mn:graphene" "Graphene and 2D materials."
ln mn:graphene mn.materials sys:is_a
ln mn:graphene mn:nano_resonator @enables
set.add name="ontology.micro_nano_machines" id="mn:graphene"

def "mn:iot_integration" "Integration with IoT and sensor networks."
ln mn:iot_integration mn.integration sys:is_a
ln mn:iot_integration mn:mems_sensor @connects
set.add name="ontology.micro_nano_machines" id="mn:iot_integration"

def "mn:lithography" "Lithography (optical, e-beam, nanoimprint)."
ln mn:lithography mn.fabrication sys:is_a
set.add name="ontology.micro_nano_machines" id="mn:lithography"

def "mn:macro_system_integration" "Integration with macro-scale robotics and devices."
ln mn:macro_system_integration mn.integration sys:is_a
set.add name="ontology.micro_nano_machines" id="mn:macro_system_integration"

def "mn:mass_sensor" "Mass-sensitive resonant sensors."
ln mn:mass_sensor mn.sensing sys:is_a
set.add name="ontology.micro_nano_machines" id="mn:mass_sensor"

def "mn:mems_mirror" "MEMS optical mirrors."
ln mn:mems_mirror mn.mems sys:is_a
set.add name="ontology.micro_nano_machines" id="mn:mems_mirror"

def "mn:mems_sensor" "MEMS sensors (accelerometers, gyros, pressure)."
ln mn:mems_sensor mn.mems sys:is_a
set.add name="ontology.micro_nano_machines" id="mn:mems_sensor"

def "mn:mems_switch" "MEMS RF switches."
ln mn:mems_switch mn.mems sys:is_a
set.add name="ontology.micro_nano_machines" id="mn:mems_switch"

def "mn:nano_resonator" "Nano mechanical resonators."
ln mn:nano_resonator mn.nems sys:is_a
set.add name="ontology.micro_nano_machines" id="mn:nano_resonator"

def "mn:nanorobot" "Nanoscale robotic systems."
ln mn:nanorobot mn.nems sys:is_a
ln mn:nanorobot mn:swarm_control @controlled_by
set.add name="ontology.micro_nano_machines" id="mn:nanorobot"

def "mn:nanowire_device" "Nanowire-based devices."
ln mn:nanowire_device mn.nems sys:is_a
set.add name="ontology.micro_nano_machines" id="mn:nanowire_device"

def "mn:optical_sensor" "Optical micro/nano sensors."
ln mn:optical_sensor mn.sensing sys:is_a
set.add name="ontology.micro_nano_machines" id="mn:optical_sensor"

def "mn:piezo_actuator" "Piezoelectric actuators."
ln mn:piezo_actuator mn.actuators sys:is_a
set.add name="ontology.micro_nano_machines" id="mn:piezo_actuator"

def "mn:polymer" "Functional polymers for micro/nano devices."
ln mn:polymer mn.materials sys:is_a
set.add name="ontology.micro_nano_machines" id="mn:polymer"

def "mn:silicon" "Silicon and SOI materials."
ln mn:silicon mn.materials sys:is_a
set.add name="ontology.micro_nano_machines" id="mn:silicon"

def "mn:swarm_control" "Swarm control of nanorobots."
ln mn:swarm_control mn.control sys:is_a
set.add name="ontology.micro_nano_machines" id="mn:swarm_control"

def "mn:thermal_actuator" "Thermal microactuators."
ln mn:thermal_actuator mn.actuators sys:is_a
set.add name="ontology.micro_nano_machines" id="mn:thermal_actuator"
