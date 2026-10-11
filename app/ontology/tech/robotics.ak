# Akasha ontology — namespace: robotics
# atoms: 28

def "robotics.control" "Control of robotic systems including feedback, impedance, and hybrid control."
ln robotics.control ont.robotics_integration sys:part_of
set.add name="ontology.robotics_integration" id="robotics.control"

def "robotics.dynamics" "Robot dynamics, rigid-body modeling, and force interactions."
ln robotics.dynamics ont.robotics_integration sys:part_of
set.add name="ontology.robotics_integration" id="robotics.dynamics"

def "robotics.mechanics" "Robot mechanisms, kinematics, and structural design."
ln robotics.mechanics ont.robotics_integration sys:part_of
set.add name="ontology.robotics_integration" id="robotics.mechanics"

def "robotics.perception" "Robot perception including sensors, SLAM, and computer vision."
ln robotics.perception ont.robotics_integration sys:part_of
set.add name="ontology.robotics_integration" id="robotics.perception"

def "robotics.planning" "Motion planning, trajectory optimization, and decision-making."
ln robotics.planning ont.robotics_integration sys:part_of
set.add name="ontology.robotics_integration" id="robotics.planning"

def "robotics.software" "Robotics software frameworks including ROS, middleware, and RTOS integration."
ln robotics.software ont.robotics_integration sys:part_of
set.add name="ontology.robotics_integration" id="robotics.software"

def "robotics.system_integration" "System-level integration including safety, multi-robot coordination, and human-robot interaction."
ln robotics.system_integration ont.robotics_integration sys:part_of
set.add name="ontology.robotics_integration" id="robotics.system_integration"

def "robotics:contact_dynamics" "Contact and force interaction modeling."
ln robotics:contact_dynamics robotics.dynamics sys:is_a
ln robotics:contact_dynamics robotics:hybrid_position_force @required_for
set.add name="ontology.robotics_integration" id="robotics:contact_dynamics"

def "robotics:forward_kinematics" "Forward kinematics mapping joint space to task space."
ln robotics:forward_kinematics robotics.mechanics sys:is_a
set.add name="ontology.robotics_integration" id="robotics:forward_kinematics"

def "robotics:hri" "Human-robot interaction."
ln robotics:hri robotics.system_integration sys:is_a
set.add name="ontology.robotics_integration" id="robotics:hri"

def "robotics:hybrid_position_force" "Hybrid position/force control."
ln robotics:hybrid_position_force robotics.control sys:is_a
set.add name="ontology.robotics_integration" id="robotics:hybrid_position_force"

def "robotics:impedance_control" "Impedance and admittance control for compliant interaction."
ln robotics:impedance_control robotics.dynamics sys:is_a
ln robotics:impedance_control robotics:hri @supports
set.add name="ontology.robotics_integration" id="robotics:impedance_control"

def "robotics:inverse_kinematics" "Inverse kinematics solving joint configurations for desired poses."
ln robotics:inverse_kinematics robotics.mechanics sys:is_a
ln robotics:inverse_kinematics robotics:trajectory_optimization @used_by
set.add name="ontology.robotics_integration" id="robotics:inverse_kinematics"

def "robotics:joint_space_control" "Joint-space control for manipulators."
ln robotics:joint_space_control robotics.control sys:is_a
set.add name="ontology.robotics_integration" id="robotics:joint_space_control"

def "robotics:lidar" "LiDAR sensing for mapping and localization."
ln robotics:lidar robotics.perception sys:is_a
set.add name="ontology.robotics_integration" id="robotics:lidar"

def "robotics:mechanism_design" "Robot mechanism and linkage design."
ln robotics:mechanism_design robotics.mechanics sys:is_a
set.add name="ontology.robotics_integration" id="robotics:mechanism_design"

def "robotics:multi_robot" "Multi-robot coordination and swarm robotics."
ln robotics:multi_robot robotics.system_integration sys:is_a
set.add name="ontology.robotics_integration" id="robotics:multi_robot"

def "robotics:path_planning" "Path planning for mobile and manipulator robots."
ln robotics:path_planning robotics.planning sys:is_a
set.add name="ontology.robotics_integration" id="robotics:path_planning"

def "robotics:reinforcement_learning_control" "Reinforcement learning for robot decision-making."
ln robotics:reinforcement_learning_control robotics.planning sys:is_a
set.add name="ontology.robotics_integration" id="robotics:reinforcement_learning_control"

def "robotics:rigid_body_dynamics" "Rigid-body dynamics for robotic manipulators and mobile robots."
ln robotics:rigid_body_dynamics robotics.dynamics sys:is_a
set.add name="ontology.robotics_integration" id="robotics:rigid_body_dynamics"

def "robotics:ros1" "ROS1 middleware."
ln robotics:ros1 robotics.software sys:is_a
set.add name="ontology.robotics_integration" id="robotics:ros1"

def "robotics:ros2" "ROS2 middleware with DDS and real-time support."
ln robotics:ros2 robotics.software sys:is_a
ln robotics:ros2 robotics:rtos_integration @integrates_with
set.add name="ontology.robotics_integration" id="robotics:ros2"

def "robotics:rtos_integration" "RTOS integration for real-time robotics."
ln robotics:rtos_integration robotics.software sys:is_a
set.add name="ontology.robotics_integration" id="robotics:rtos_integration"

def "robotics:safety" "Robot safety including ISO 10218 and collaborative robot standards."
ln robotics:safety robotics.system_integration sys:is_a
set.add name="ontology.robotics_integration" id="robotics:safety"

def "robotics:slam" "SLAM for simultaneous localization and mapping."
ln robotics:slam robotics.perception sys:is_a
ln robotics:slam robotics:path_planning @informs
set.add name="ontology.robotics_integration" id="robotics:slam"

def "robotics:task_space_control" "Task-space control for end-effector behavior."
ln robotics:task_space_control robotics.control sys:is_a
set.add name="ontology.robotics_integration" id="robotics:task_space_control"

def "robotics:trajectory_optimization" "Trajectory optimization using numerical methods."
ln robotics:trajectory_optimization robotics.planning sys:is_a
set.add name="ontology.robotics_integration" id="robotics:trajectory_optimization"

def "robotics:vision" "Computer vision for robotics."
ln robotics:vision robotics.perception sys:is_a
set.add name="ontology.robotics_integration" id="robotics:vision"
