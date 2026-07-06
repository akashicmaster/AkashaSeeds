# Akasha ontology — namespace: comp
# atoms: 34

def "comp.analog" "Analog computing using continuous physical quantities."
ln comp.analog ont.computation_paradigms sys:part_of
set.add name="ontology.computation_paradigms" id="comp.analog"

def "comp.biological" "Biological and molecular computing including DNA and cellular computing."
ln comp.biological ont.computation_paradigms sys:part_of
set.add name="ontology.computation_paradigms" id="comp.biological"

def "comp.neuromorphic" "Neuromorphic computing inspired by biological neural systems."
ln comp.neuromorphic ont.computation_paradigms sys:part_of
set.add name="ontology.computation_paradigms" id="comp.neuromorphic"

def "comp.non_von_neumann" "Non-von Neumann architectures including in-memory and dataflow computing."
ln comp.non_von_neumann ont.computation_paradigms sys:part_of
set.add name="ontology.computation_paradigms" id="comp.non_von_neumann"

def "comp.photonic" "Photonic and optical computing using light as computation medium."
ln comp.photonic ont.computation_paradigms sys:part_of
set.add name="ontology.computation_paradigms" id="comp.photonic"

def "comp.physical" "Physical and mechanical computing including stick/rod-based and fluidic systems."
ln comp.physical ont.computation_paradigms sys:part_of
set.add name="ontology.computation_paradigms" id="comp.physical"

def "comp.quantum" "Quantum computing paradigms including gate-based, annealing, and photonic quantum systems."
ln comp.quantum ont.computation_paradigms sys:part_of
set.add name="ontology.computation_paradigms" id="comp.quantum"

def "comp:analog_differential_solver" "Analog computers solving differential equations via physical circuits."
ln comp:analog_differential_solver comp.analog sys:is_a
set.add name="ontology.computation_paradigms" id="comp:analog_differential_solver"

def "comp:analog_neuromorphic" "Analog neuromorphic circuits implementing neural dynamics."
ln comp:analog_neuromorphic comp.neuromorphic sys:is_a
set.add name="ontology.computation_paradigms" id="comp:analog_neuromorphic"

def "comp:cellular_computing" "Computing using living cells as information processing units."
ln comp:cellular_computing comp.biological sys:is_a
set.add name="ontology.computation_paradigms" id="comp:cellular_computing"

def "comp:dataflow_machine" "Dataflow machines where computation is driven by data availability."
ln comp:dataflow_machine comp.non_von_neumann sys:is_a
set.add name="ontology.computation_paradigms" id="comp:dataflow_machine"

def "comp:dna_computing" "DNA-based computing using molecular reactions."
ln comp:dna_computing comp.biological sys:is_a
set.add name="ontology.computation_paradigms" id="comp:dna_computing"

def "comp:event_driven_neuromorphic" "Event-driven neuromorphic architectures."
ln comp:event_driven_neuromorphic comp.neuromorphic sys:is_a
set.add name="ontology.computation_paradigms" id="comp:event_driven_neuromorphic"

def "comp:fluidic_computing" "Fluidic computing using flows and pressure as information carriers."
ln comp:fluidic_computing comp.physical sys:is_a
set.add name="ontology.computation_paradigms" id="comp:fluidic_computing"

def "comp:graph_processor" "Graph processors optimized for graph-structured workloads."
ln comp:graph_processor comp.non_von_neumann sys:is_a
set.add name="ontology.computation_paradigms" id="comp:graph_processor"

def "comp:in_memory_computing" "In-memory computing where memory elements perform computation."
ln comp:in_memory_computing comp.non_von_neumann sys:is_a
set.add name="ontology.computation_paradigms" id="comp:in_memory_computing"

def "comp:ion_trap_quantum" "Ion trap quantum computing."
ln comp:ion_trap_quantum comp.quantum sys:is_a
set.add name="ontology.computation_paradigms" id="comp:ion_trap_quantum"

def "comp:ising_machine" "Ising machines implementing optimization via physical spin systems."
ln comp:ising_machine comp.physical sys:is_a
ln comp:ising_machine comp:quantum_annealing @physically_implements
set.add name="ontology.computation_paradigms" id="comp:ising_machine"

def "comp:mechanical_computing" "Mechanical computing using gears, levers, and physical linkages."
ln comp:mechanical_computing comp.physical sys:is_a
set.add name="ontology.computation_paradigms" id="comp:mechanical_computing"

def "comp:memristor_computing" "Memristor-based analog computing and in-memory operations."
ln comp:memristor_computing comp.analog sys:is_a
ln comp:memristor_computing comp:in_memory_computing @enables
set.add name="ontology.computation_paradigms" id="comp:memristor_computing"

def "comp:optical_analog" "Optical analog computing using interference and diffraction."
ln comp:optical_analog comp.analog sys:is_a
set.add name="ontology.computation_paradigms" id="comp:optical_analog"

def "comp:optical_neural_network" "Neural networks implemented with optical components."
ln comp:optical_neural_network comp.photonic sys:is_a
set.add name="ontology.computation_paradigms" id="comp:optical_neural_network"

def "comp:optical_spiking" "Spiking computation using optical pulses."
ln comp:optical_spiking comp.photonic sys:is_a
set.add name="ontology.computation_paradigms" id="comp:optical_spiking"

def "comp:particle_based" "Particle-based computing using collective dynamics."
ln comp:particle_based comp.physical sys:is_a
set.add name="ontology.computation_paradigms" id="comp:particle_based"

def "comp:photonic_quantum" "Photonic quantum computing using optical qubits."
ln comp:photonic_quantum comp.quantum sys:is_a
set.add name="ontology.computation_paradigms" id="comp:photonic_quantum"

def "comp:processing_in_memory" "Processing-in-memory architectures tightly coupling compute and memory."
ln comp:processing_in_memory comp.non_von_neumann sys:is_a
set.add name="ontology.computation_paradigms" id="comp:processing_in_memory"

def "comp:quantum_annealing" "Quantum annealing for optimization problems."
ln comp:quantum_annealing comp.quantum sys:is_a
set.add name="ontology.computation_paradigms" id="comp:quantum_annealing"

def "comp:quantum_gate_model" "Gate-based quantum computing using qubits and quantum circuits."
ln comp:quantum_gate_model comp.quantum sys:is_a
set.add name="ontology.computation_paradigms" id="comp:quantum_gate_model"

def "comp:reconfigurable_fpga" "Reconfigurable computing using FPGAs."
ln comp:reconfigurable_fpga comp.non_von_neumann sys:is_a
ln comp:reconfigurable_fpga comp:dataflow_machine @can_implement
set.add name="ontology.computation_paradigms" id="comp:reconfigurable_fpga"

def "comp:rna_circuits" "RNA-based logic and regulatory circuits."
ln comp:rna_circuits comp.biological sys:is_a
set.add name="ontology.computation_paradigms" id="comp:rna_circuits"

def "comp:silicon_photonics" "Silicon photonics for high-speed optical interconnects and computing."
ln comp:silicon_photonics comp.photonic sys:is_a
ln comp:silicon_photonics comp:optical_neural_network @supports
set.add name="ontology.computation_paradigms" id="comp:silicon_photonics"

def "comp:spiking_neural" "Spiking neural network-based neuromorphic computing."
ln comp:spiking_neural comp.neuromorphic sys:is_a
ln comp:spiking_neural comp:optical_spiking @analogous_to
set.add name="ontology.computation_paradigms" id="comp:spiking_neural"

def "comp:synthetic_bio_logic" "Synthetic biology constructs implementing logic gates."
ln comp:synthetic_bio_logic comp.biological sys:is_a
set.add name="ontology.computation_paradigms" id="comp:synthetic_bio_logic"

def "comp:topological_quantum" "Topological quantum computing using anyons."
ln comp:topological_quantum comp.quantum sys:is_a
set.add name="ontology.computation_paradigms" id="comp:topological_quantum"
