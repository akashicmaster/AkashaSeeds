# Akasha ontology — namespace: auto
# atoms: 33

def "auto.control_layer" "Control layer including classical, optimal, robust, and nonlinear control."
ln auto.control_layer ont.automation sys:part_of
set.add name="ontology.automation" id="auto.control_layer"

def "auto.cybernetic_layer" "Cybernetic integration including feedback, adaptation, and self-organization."
ln auto.cybernetic_layer ont.automation sys:part_of
set.add name="ontology.automation" id="auto.cybernetic_layer"

def "auto.information_layer" "Information and communication layer including PLC, SCADA, DCS, and fieldbus."
ln auto.information_layer ont.automation sys:part_of
set.add name="ontology.automation" id="auto.information_layer"

def "auto.intelligence_layer" "Intelligent automation including AI, optimization, and digital twins."
ln auto.intelligence_layer ont.automation sys:part_of
set.add name="ontology.automation" id="auto.intelligence_layer"

def "auto.orchestration_layer" "Factory and enterprise orchestration including MES, APS, WMS, and ERP."
ln auto.orchestration_layer ont.automation sys:part_of
set.add name="ontology.automation" id="auto.orchestration_layer"

def "auto.physical_layer" "Physical automation layer including mechanics, electronics, sensors, and actuators."
ln auto.physical_layer ont.automation sys:part_of
set.add name="ontology.automation" id="auto.physical_layer"

def "auto.robotics_layer" "Robotics and motion automation including industrial robots and mobile robots."
ln auto.robotics_layer ont.automation sys:part_of
set.add name="ontology.automation" id="auto.robotics_layer"

def "auto:actuators" "Actuators for motion and force."
ln auto:actuators auto.physical_layer sys:is_a
set.add name="ontology.automation" id="auto:actuators"

def "auto:adaptive_systems" "Adaptive automation systems."
ln auto:adaptive_systems auto.cybernetic_layer sys:is_a
set.add name="ontology.automation" id="auto:adaptive_systems"

def "auto:anomaly_detection" "Anomaly detection in automated systems."
ln auto:anomaly_detection auto.intelligence_layer sys:is_a
set.add name="ontology.automation" id="auto:anomaly_detection"

def "auto:aps" "Advanced Planning and Scheduling."
ln auto:aps auto.orchestration_layer sys:is_a
set.add name="ontology.automation" id="auto:aps"

def "auto:dcs" "Distributed Control Systems."
ln auto:dcs auto.information_layer sys:is_a
set.add name="ontology.automation" id="auto:dcs"

def "auto:digital_twin" "Digital twins for simulation and prediction."
ln auto:digital_twin auto.intelligence_layer sys:is_a
ln auto:digital_twin auto:mes_system @supports
set.add name="ontology.automation" id="auto:digital_twin"

def "auto:electronics" "Electronics and power systems."
ln auto:electronics auto.physical_layer sys:is_a
set.add name="ontology.automation" id="auto:electronics"

def "auto:erp" "Enterprise Resource Planning."
ln auto:erp auto.orchestration_layer sys:is_a
set.add name="ontology.automation" id="auto:erp"

def "auto:feedback" "Feedback loops in automation systems."
ln auto:feedback auto.cybernetic_layer sys:is_a
set.add name="ontology.automation" id="auto:feedback"

def "auto:fieldbus" "Industrial communication protocols."
ln auto:fieldbus auto.information_layer sys:is_a
set.add name="ontology.automation" id="auto:fieldbus"

def "auto:industrial_robotics" "Industrial robots for manufacturing automation."
ln auto:industrial_robotics auto.robotics_layer sys:is_a
ln auto:industrial_robotics auto:plc_system @controlled_by
set.add name="ontology.automation" id="auto:industrial_robotics"

def "auto:machine_learning" "Machine learning for automation."
ln auto:machine_learning auto.intelligence_layer sys:is_a
set.add name="ontology.automation" id="auto:machine_learning"

def "auto:mechanics" "Mechanical systems for automation."
ln auto:mechanics auto.physical_layer sys:is_a
set.add name="ontology.automation" id="auto:mechanics"

def "auto:mes_system" "Manufacturing Execution System."
ln auto:mes_system auto.orchestration_layer sys:is_a
set.add name="ontology.automation" id="auto:mes_system"

def "auto:mobile_robotics" "Autonomous mobile robots (AMR/AGV)."
ln auto:mobile_robotics auto.robotics_layer sys:is_a
set.add name="ontology.automation" id="auto:mobile_robotics"

def "auto:mpc" "Model Predictive Control."
ln auto:mpc auto.control_layer sys:is_a
ln auto:mpc auto:optimization @uses
set.add name="ontology.automation" id="auto:mpc"

def "auto:optimization" "Optimization for scheduling and control."
ln auto:optimization auto.intelligence_layer sys:is_a
set.add name="ontology.automation" id="auto:optimization"

def "auto:pid" "PID control for automation systems."
ln auto:pid auto.control_layer sys:is_a
set.add name="ontology.automation" id="auto:pid"

def "auto:plc_system" "PLC-based automation control."
ln auto:plc_system auto.information_layer sys:is_a
set.add name="ontology.automation" id="auto:plc_system"

def "auto:robot_cell" "Robot cell integration."
ln auto:robot_cell auto.robotics_layer sys:is_a
set.add name="ontology.automation" id="auto:robot_cell"

def "auto:robust_control" "Robust control for uncertain systems."
ln auto:robust_control auto.control_layer sys:is_a
set.add name="ontology.automation" id="auto:robust_control"

def "auto:scada" "SCADA systems for supervisory control."
ln auto:scada auto.information_layer sys:is_a
set.add name="ontology.automation" id="auto:scada"

def "auto:self_organization" "Self-organizing automation."
ln auto:self_organization auto.cybernetic_layer sys:is_a
ln auto:self_organization auto:mobile_robotics @influences
set.add name="ontology.automation" id="auto:self_organization"

def "auto:sensors" "Sensors for measurement and detection."
ln auto:sensors auto.physical_layer sys:is_a
ln auto:sensors auto:pid @informs
set.add name="ontology.automation" id="auto:sensors"

def "auto:state_space" "State-space control."
ln auto:state_space auto.control_layer sys:is_a
set.add name="ontology.automation" id="auto:state_space"

def "auto:wms" "Warehouse Management System."
ln auto:wms auto.orchestration_layer sys:is_a
set.add name="ontology.automation" id="auto:wms"
