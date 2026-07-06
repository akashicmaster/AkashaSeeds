# Akasha ontology — namespace: irob
# atoms: 32

def "irob.communication" "Industrial communication including fieldbus, Ethernet-based protocols, and PLC integration."
ln irob.communication ont.industrial_robotics sys:part_of
set.add name="ontology.industrial_robotics" id="irob.communication"

def "irob.control" "Control systems for industrial robots including joint-space, task-space, and force control."
ln irob.control ont.industrial_robotics sys:part_of
set.add name="ontology.industrial_robotics" id="irob.control"

def "irob.fa_integration" "Factory automation integration including PLCs, MES, and production lines."
ln irob.fa_integration ont.industrial_robotics sys:part_of
set.add name="ontology.industrial_robotics" id="irob.fa_integration"

def "irob.mechanics" "Mechanical structures and kinematics of industrial robots."
ln irob.mechanics ont.industrial_robotics sys:part_of
set.add name="ontology.industrial_robotics" id="irob.mechanics"

def "irob.safety" "Safety standards, collaborative robot safety, and risk assessment."
ln irob.safety ont.industrial_robotics sys:part_of
set.add name="ontology.industrial_robotics" id="irob.safety"

def "irob.sensing" "Sensors used in industrial robotics including vision, force, and proximity sensing."
ln irob.sensing ont.industrial_robotics sys:part_of
set.add name="ontology.industrial_robotics" id="irob.sensing"

def "irob.types" "Types of industrial robots including articulated, SCARA, delta, and collaborative robots."
ln irob.types ont.industrial_robotics sys:part_of
set.add name="ontology.industrial_robotics" id="irob.types"

def "irob:articulated" "Articulated robots with 6 or more rotary joints."
ln irob:articulated irob.types sys:is_a
set.add name="ontology.industrial_robotics" id="irob:articulated"

def "irob:canopen" "CANopen fieldbus protocol."
ln irob:canopen irob.communication sys:is_a
set.add name="ontology.industrial_robotics" id="irob:canopen"

def "irob:cartesian" "Cartesian robots with linear axes."
ln irob:cartesian irob.types sys:is_a
set.add name="ontology.industrial_robotics" id="irob:cartesian"

def "irob:cobot" "Collaborative robots with safety-rated features."
ln irob:cobot irob.types sys:is_a
set.add name="ontology.industrial_robotics" id="irob:cobot"

def "irob:delta" "Delta robots for ultra-fast lightweight manipulation."
ln irob:delta irob.types sys:is_a
set.add name="ontology.industrial_robotics" id="irob:delta"

def "irob:dh_parameters" "Denavit-Hartenberg parameters for robot modeling."
ln irob:dh_parameters irob.mechanics sys:is_a
ln irob:dh_parameters irob:forward_kinematics @defines
set.add name="ontology.industrial_robotics" id="irob:dh_parameters"

def "irob:ethercat" "EtherCAT real-time industrial Ethernet."
ln irob:ethercat irob.communication sys:is_a
ln irob:ethercat irob:plc @used_with
set.add name="ontology.industrial_robotics" id="irob:ethercat"

def "irob:force_control" "Force and compliance control."
ln irob:force_control irob.control sys:is_a
set.add name="ontology.industrial_robotics" id="irob:force_control"

def "irob:force_sensor" "Force/torque sensors for manipulation."
ln irob:force_sensor irob.sensing sys:is_a
set.add name="ontology.industrial_robotics" id="irob:force_sensor"

def "irob:forward_kinematics" "Forward kinematics for industrial manipulators."
ln irob:forward_kinematics irob.mechanics sys:is_a
set.add name="ontology.industrial_robotics" id="irob:forward_kinematics"

def "irob:impedance_control" "Impedance control for safe interaction."
ln irob:impedance_control irob.control sys:is_a
ln irob:impedance_control irob:cobot @required_for
set.add name="ontology.industrial_robotics" id="irob:impedance_control"

def "irob:inverse_kinematics" "Inverse kinematics for industrial robots."
ln irob:inverse_kinematics irob.mechanics sys:is_a
set.add name="ontology.industrial_robotics" id="irob:inverse_kinematics"

def "irob:iso10218" "ISO 10218 industrial robot safety standard."
ln irob:iso10218 irob.safety sys:is_a
set.add name="ontology.industrial_robotics" id="irob:iso10218"

def "irob:iso_ts_15066" "ISO/TS 15066 collaborative robot safety."
ln irob:iso_ts_15066 irob.safety sys:is_a
set.add name="ontology.industrial_robotics" id="irob:iso_ts_15066"

def "irob:joint_control" "Joint-space control for industrial robots."
ln irob:joint_control irob.control sys:is_a
set.add name="ontology.industrial_robotics" id="irob:joint_control"

def "irob:mes" "Manufacturing Execution System."
ln irob:mes irob.fa_integration sys:is_a
set.add name="ontology.industrial_robotics" id="irob:mes"

def "irob:opcua" "OPC UA for industrial interoperability."
ln irob:opcua irob.communication sys:is_a
set.add name="ontology.industrial_robotics" id="irob:opcua"

def "irob:plc" "Programmable Logic Controller for automation."
ln irob:plc irob.fa_integration sys:is_a
set.add name="ontology.industrial_robotics" id="irob:plc"

def "irob:profinet" "PROFINET industrial communication."
ln irob:profinet irob.communication sys:is_a
set.add name="ontology.industrial_robotics" id="irob:profinet"

def "irob:proximity_sensor" "Proximity sensors for safety and detection."
ln irob:proximity_sensor irob.sensing sys:is_a
set.add name="ontology.industrial_robotics" id="irob:proximity_sensor"

def "irob:risk_assessment" "Risk assessment for industrial robot deployment."
ln irob:risk_assessment irob.safety sys:is_a
ln irob:risk_assessment irob:robot_cell @required_for
set.add name="ontology.industrial_robotics" id="irob:risk_assessment"

def "irob:robot_cell" "Robot cell integration with conveyors, sensors, and tooling."
ln irob:robot_cell irob.fa_integration sys:is_a
set.add name="ontology.industrial_robotics" id="irob:robot_cell"

def "irob:scara" "SCARA robots for high-speed pick-and-place."
ln irob:scara irob.types sys:is_a
set.add name="ontology.industrial_robotics" id="irob:scara"

def "irob:task_control" "Task-space control for end-effector motion."
ln irob:task_control irob.control sys:is_a
set.add name="ontology.industrial_robotics" id="irob:task_control"

def "irob:vision" "Vision systems for industrial robots."
ln irob:vision irob.sensing sys:is_a
ln irob:vision irob:task_control @informs
set.add name="ontology.industrial_robotics" id="irob:vision"
