# Akasha ontology — mechanical, electrical & electronic engineering (機械・電気・電子工学).
# The core design disciplines, bridged to phys:/mat:/mfg:/robotics:/energy:/iot:.
# Base pack.

def "mecheng" "Mechanical engineering — the design of machines, mechanisms and thermal systems (機械工学)."
# ── mechanical: fields & concepts ──
def "mecheng:statics" "Forces on bodies at rest (静力学)."
ln mecheng:statics mecheng thesaurus:related
def "mecheng:dynamics" "Motion and its causes (動力学)."
ln mecheng:dynamics mecheng thesaurus:related
def "mecheng:kinematics" "The geometry of motion, without forces (運動学)."
ln mecheng:kinematics mecheng thesaurus:related
def "mecheng:mechanics_of_materials" "Stress, strain and deformation in solids (材料力学)."
ln mecheng:mechanics_of_materials mecheng thesaurus:related
ln mecheng:mechanics_of_materials mecheng:stress thesaurus:related
def "mecheng:thermodynamics" "Energy, heat and work and their conversion (熱力学)."
ln mecheng:thermodynamics mecheng thesaurus:related
ln mecheng:thermodynamics energy:thermal_storage thesaurus:related
def "mecheng:fluid_mechanics" "The behaviour of liquids and gases (流体力学)."
ln mecheng:fluid_mechanics mecheng thesaurus:related
def "mecheng:heat_transfer" "Conduction, convection and radiation of heat (伝熱)."
ln mecheng:heat_transfer mecheng thesaurus:related
def "mecheng:machine_design" "Designing components to carry loads reliably (機械設計)."
ln mecheng:machine_design mecheng thesaurus:related
ln mecheng:machine_design mfg:dfm thesaurus:related
def "mecheng:mechatronics" "The fusion of mechanics, electronics and control (メカトロニクス)."
ln mecheng:mechatronics mecheng thesaurus:related
ln mecheng:mechatronics eleceng:motor thesaurus:related
def "mecheng:stress" "Internal force per unit area in a material (応力)."
ln mecheng:stress mecheng thesaurus:related
def "mecheng:torque" "A rotational force (トルク)."
ln mecheng:torque mecheng thesaurus:related
def "mecheng:fatigue" "Failure from repeated loading below the static limit (疲労)."
ln mecheng:fatigue mecheng thesaurus:related
ln mecheng:fatigue mecheng:stress thesaurus:related
def "mecheng:tolerance" "The allowed variation in a dimension (公差)."
ln mecheng:tolerance mecheng thesaurus:related
# ── mechanical: elements & manufacturing ──
def "mecheng:gear" "A toothed wheel transmitting torque and changing speed (歯車)."
ln mecheng:gear mecheng thesaurus:related
def "mecheng:bearing" "A component reducing friction between moving parts (軸受)."
ln mecheng:bearing mecheng thesaurus:related
def "mecheng:shaft" "A rotating element transmitting power (軸)."
ln mecheng:shaft mecheng thesaurus:related
def "mecheng:actuator" "A component that produces motion from energy (アクチュエータ)."
ln mecheng:actuator mecheng thesaurus:related
ln mecheng:actuator electron:actuator thesaurus:related
def "mecheng:machining" "Shaping material by cutting (切削加工)."
ln mecheng:machining mecheng thesaurus:related
ln mecheng:machining mfg:cycle_time thesaurus:related
def "mecheng:casting" "Forming by pouring molten material into a mould (鋳造)."
ln mecheng:casting mecheng thesaurus:related
def "mecheng:welding" "Joining materials by fusion (溶接)."
ln mecheng:welding mecheng thesaurus:related
def "mecheng:additive_manufacturing" "Building parts layer by layer — 3D printing (積層造形)."
ln mecheng:additive_manufacturing mecheng thesaurus:related
ln mecheng:additive_manufacturing mfg:dfm thesaurus:related
ln mecheng:additive_manufacturing futurefood:3d_printed_food thesaurus:related
def "mecheng:cnc" "Computer numerical control of machine tools."
ln mecheng:cnc mecheng thesaurus:related
def "mecheng:cad" "Computer-aided design of parts and assemblies (CAD)."
ln mecheng:cad mecheng thesaurus:related
ln mecheng:cad dh:3d_modeling thesaurus:related
# ── electrical engineering (電気工学) ──
def "eleceng" "Electrical engineering — the study of electricity, power and electromagnetism (電気工学)."
def "eleceng:circuit" "A closed path for electric current (回路)."
ln eleceng:circuit eleceng thesaurus:related
def "eleceng:voltage" "The electric potential difference driving current (電圧)."
ln eleceng:voltage eleceng thesaurus:related
def "eleceng:current" "The flow of electric charge (電流)."
ln eleceng:current eleceng thesaurus:related
def "eleceng:resistance" "Opposition to current flow (抵抗)."
ln eleceng:resistance eleceng thesaurus:related
def "eleceng:ohms_law" "V = I × R — the basic circuit relation (オームの法則)."
ln eleceng:ohms_law eleceng thesaurus:related
def "eleceng:electromagnetism" "The unified theory of electric and magnetic phenomena (電磁気学)."
ln eleceng:electromagnetism eleceng thesaurus:related
ln eleceng:electromagnetism eleceng:circuit thesaurus:related
def "eleceng:inductance" "A circuit's opposition to changing current."
ln eleceng:inductance eleceng thesaurus:related
def "eleceng:capacitance" "The ability to store charge."
ln eleceng:capacitance eleceng thesaurus:related
def "eleceng:transformer" "A device changing AC voltage by induction (変圧器)."
ln eleceng:transformer eleceng thesaurus:related
def "eleceng:motor" "A machine converting electrical energy to motion (電動機)."
ln eleceng:motor eleceng thesaurus:related
ln eleceng:motor eleceng:generator thesaurus:related
ln eleceng:motor mecheng:actuator thesaurus:related
def "eleceng:generator" "A machine converting motion to electricity (発電機)."
ln eleceng:generator eleceng thesaurus:related
ln eleceng:generator energy:hydro thesaurus:related
ln eleceng:generator energy:wind thesaurus:related
def "eleceng:power_system" "The network generating and delivering electric power."
ln eleceng:power_system eleceng thesaurus:related
ln eleceng:power_system energy:transmission thesaurus:related
ln eleceng:power_system energy:distribution thesaurus:related
ln eleceng:power_system infra:electricity_supply thesaurus:related
def "eleceng:control_system" "A system regulating behaviour toward a set point (制御系)."
ln eleceng:control_system eleceng thesaurus:related
ln eleceng:control_system electron:microcontroller thesaurus:related
# ── electronics (電子工学) ──
def "electron" "Electronics — circuits using semiconductors to process signals (電子工学)."
def "electron:semiconductor" "A material whose conductivity can be controlled — the basis of chips (半導体)."
ln electron:semiconductor electron thesaurus:related
def "electron:transistor" "A semiconductor switch/amplifier, the atom of digital logic (トランジスタ)."
ln electron:transistor electron thesaurus:related
ln electron:transistor electron:semiconductor thesaurus:related
def "electron:diode" "A one-way valve for current."
ln electron:diode electron thesaurus:related
def "electron:integrated_circuit" "Many components fabricated on one chip (集積回路/IC)."
ln electron:integrated_circuit electron thesaurus:related
def "electron:microchip" "A miniaturised integrated circuit."
ln electron:microchip electron thesaurus:related
def "electron:resistor" "A component providing resistance."
ln electron:resistor electron thesaurus:related
def "electron:capacitor" "A component storing charge."
ln electron:capacitor electron thesaurus:related
def "electron:printed_circuit_board" "The board wiring components together (基板/PCB)."
ln electron:printed_circuit_board electron thesaurus:related
def "electron:analog" "Continuous-signal electronics."
ln electron:analog electron thesaurus:related
def "electron:digital" "Discrete-signal (binary) electronics."
ln electron:digital electron thesaurus:related
def "electron:logic_gate" "A basic digital building block (AND/OR/NOT)."
ln electron:logic_gate electron thesaurus:related
ln electron:logic_gate electron:digital thesaurus:related
def "electron:microcontroller" "A small computer on a chip for embedded control (マイコン)."
ln electron:microcontroller electron thesaurus:related
ln electron:microcontroller iot:coap thesaurus:related
ln electron:microcontroller electron:embedded_system thesaurus:related
def "electron:microprocessor" "The processing core of a computer (CPU)."
ln electron:microprocessor electron thesaurus:related
ln electron:microprocessor electron:integrated_circuit thesaurus:related
def "electron:sensor" "A device converting a physical quantity to a signal (センサ)."
ln electron:sensor electron thesaurus:related
ln electron:sensor iot:coap thesaurus:related
def "electron:actuator" "A device converting a signal to physical action (アクチュエータ)."
ln electron:actuator electron thesaurus:related
def "electron:signal_processing" "Analysing and transforming signals (信号処理)."
ln electron:signal_processing electron thesaurus:related
ln electron:signal_processing neuro:action_potential thesaurus:related
def "electron:embedded_system" "A computer built into a device for dedicated control."
ln electron:embedded_system electron thesaurus:related
ln electron:embedded_system iot:coap thesaurus:related
