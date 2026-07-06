# Akasha ontology — namespace: mecha
# atoms: 30

def "mecha.actuators" "Actuators for motion, force, and energy conversion."
ln mecha.actuators ont.mechatronics sys:part_of
set.add name="ontology.mechatronics" id="mecha.actuators"

def "mecha.control" "Control theory including feedback, PID, state-space, and optimal control."
ln mecha.control ont.mechatronics sys:part_of
set.add name="ontology.mechatronics" id="mecha.control"

def "mecha.electronics" "Electronics including circuits, power systems, and signal conditioning."
ln mecha.electronics ont.mechatronics sys:part_of
set.add name="ontology.mechatronics" id="mecha.electronics"

def "mecha.embedded" "Embedded software, firmware, and RTOS for mechatronic systems."
ln mecha.embedded ont.mechatronics sys:part_of
set.add name="ontology.mechatronics" id="mecha.embedded"

def "mecha.mechanical" "Mechanical structures, mechanisms, kinematics, and dynamics."
ln mecha.mechanical ont.mechatronics sys:part_of
set.add name="ontology.mechatronics" id="mecha.mechanical"

def "mecha.robotics" "Robotics integration combining mechanics, electronics, control, and software."
ln mecha.robotics ont.mechatronics sys:part_of
set.add name="ontology.mechatronics" id="mecha.robotics"

def "mecha.sensors" "Sensors for measurement and perception."
ln mecha.sensors ont.mechatronics sys:part_of
set.add name="ontology.mechatronics" id="mecha.sensors"

def "mecha:analog_circuits" "Analog circuits for signal conditioning."
ln mecha:analog_circuits mecha.electronics sys:is_a
set.add name="ontology.mechatronics" id="mecha:analog_circuits"

def "mecha:digital_circuits" "Digital logic and microcontroller interfaces."
ln mecha:digital_circuits mecha.electronics sys:is_a
set.add name="ontology.mechatronics" id="mecha:digital_circuits"

def "mecha:embedded_comm" "Embedded communication protocols (CAN, SPI, I2C)."
ln mecha:embedded_comm mecha.embedded sys:is_a
set.add name="ontology.mechatronics" id="mecha:embedded_comm"

def "mecha:encoder" "Rotary and linear encoders for position measurement."
ln mecha:encoder mecha.sensors sys:is_a
set.add name="ontology.mechatronics" id="mecha:encoder"

def "mecha:firmware" "Firmware for embedded control systems."
ln mecha:firmware mecha.embedded sys:is_a
set.add name="ontology.mechatronics" id="mecha:firmware"

def "mecha:force_sensor" "Force and torque sensors."
ln mecha:force_sensor mecha.sensors sys:is_a
set.add name="ontology.mechatronics" id="mecha:force_sensor"

def "mecha:frame_structure" "Structural frames and mechanical chassis."
ln mecha:frame_structure mecha.mechanical sys:is_a
set.add name="ontology.mechatronics" id="mecha:frame_structure"

def "mecha:gear_system" "Gear trains and transmission systems."
ln mecha:gear_system mecha.mechanical sys:is_a
ln mecha:gear_system mecha:robot_dynamics @affects
set.add name="ontology.mechatronics" id="mecha:gear_system"

def "mecha:hydraulic_actuator" "Hydraulic actuators for high-force applications."
ln mecha:hydraulic_actuator mecha.actuators sys:is_a
set.add name="ontology.mechatronics" id="mecha:hydraulic_actuator"

def "mecha:imu" "Inertial Measurement Unit (accelerometer + gyroscope)."
ln mecha:imu mecha.sensors sys:is_a
ln mecha:imu mecha:pid_control @used_by
set.add name="ontology.mechatronics" id="mecha:imu"

def "mecha:linkage" "Mechanical linkages and kinematic chains."
ln mecha:linkage mecha.mechanical sys:is_a
set.add name="ontology.mechatronics" id="mecha:linkage"

def "mecha:motor" "Electric motors including DC, BLDC, and servo motors."
ln mecha:motor mecha.actuators sys:is_a
ln mecha:motor mecha:pid_control @controlled_by
set.add name="ontology.mechatronics" id="mecha:motor"

def "mecha:optimal_control" "Optimal control including LQR and MPC."
ln mecha:optimal_control mecha.control sys:is_a
set.add name="ontology.mechatronics" id="mecha:optimal_control"

def "mecha:path_planning" "Path and motion planning algorithms."
ln mecha:path_planning mecha.robotics sys:is_a
set.add name="ontology.mechatronics" id="mecha:path_planning"

def "mecha:pid_control" "PID control for feedback regulation."
ln mecha:pid_control mecha.control sys:is_a
set.add name="ontology.mechatronics" id="mecha:pid_control"

def "mecha:piezo_actuator" "Piezoelectric actuators for precision motion."
ln mecha:piezo_actuator mecha.actuators sys:is_a
set.add name="ontology.mechatronics" id="mecha:piezo_actuator"

def "mecha:pneumatic_actuator" "Pneumatic actuators using compressed air."
ln mecha:pneumatic_actuator mecha.actuators sys:is_a
set.add name="ontology.mechatronics" id="mecha:pneumatic_actuator"

def "mecha:power_electronics" "Power electronics for motor control and energy conversion."
ln mecha:power_electronics mecha.electronics sys:is_a
set.add name="ontology.mechatronics" id="mecha:power_electronics"

def "mecha:robot_dynamics" "Robot dynamics and force modeling."
ln mecha:robot_dynamics mecha.robotics sys:is_a
set.add name="ontology.mechatronics" id="mecha:robot_dynamics"

def "mecha:robot_kinematics" "Robot kinematics including forward and inverse models."
ln mecha:robot_kinematics mecha.robotics sys:is_a
set.add name="ontology.mechatronics" id="mecha:robot_kinematics"

def "mecha:rtos" "Real-time operating systems for mechatronics."
ln mecha:rtos mecha.embedded sys:is_a
ln mecha:rtos mecha.control @supports
set.add name="ontology.mechatronics" id="mecha:rtos"

def "mecha:state_space" "State-space control models."
ln mecha:state_space mecha.control sys:is_a
set.add name="ontology.mechatronics" id="mecha:state_space"

def "mecha:vision_sensor" "Camera and vision-based sensors."
ln mecha:vision_sensor mecha.sensors sys:is_a
ln mecha:vision_sensor mecha:path_planning @informs
set.add name="ontology.mechatronics" id="mecha:vision_sensor"
