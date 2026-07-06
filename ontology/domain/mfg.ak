# Akasha ontology — namespace: mfg
# atoms: 31

def "mfg:bom" "Bill of Materials — list of components and quantities."
ln mfg:bom manufacturing.engineering sys:is_a
set.add name="ontology.manufacturing" id="mfg:bom"

def "mfg:bottleneck" "The slowest step limiting overall throughput."
ln mfg:bottleneck manufacturing.process sys:is_a
ln mfg:bottleneck mfg:throughput @limits
set.add name="ontology.manufacturing" id="mfg:bottleneck"

def "mfg:capacity_planning" "Ensuring production resources can meet demand."
ln mfg:capacity_planning manufacturing.planning sys:is_a
ln mfg:capacity_planning mfg:load_leveling @supports
set.add name="ontology.manufacturing" id="mfg:capacity_planning"

def "mfg:control_chart" "Graphical tool for monitoring process variation."
ln mfg:control_chart manufacturing.quality sys:is_a
set.add name="ontology.manufacturing" id="mfg:control_chart"

def "mfg:cycle_time" "Time required to complete one unit of work."
ln mfg:cycle_time manufacturing.process sys:is_a
set.add name="ontology.manufacturing" id="mfg:cycle_time"

def "mfg:defect_rate" "Percentage of units that fail to meet quality standards."
ln mfg:defect_rate manufacturing.quality sys:is_a
set.add name="ontology.manufacturing" id="mfg:defect_rate"

def "mfg:dfa" "Design for Assembly — designing products for efficient assembly."
ln mfg:dfa manufacturing.engineering sys:is_a
set.add name="ontology.manufacturing" id="mfg:dfa"

def "mfg:dfm" "Design for Manufacturing — designing products for ease of production."
ln mfg:dfm manufacturing.engineering sys:is_a
ln mfg:dfm mfg:bom @influences
set.add name="ontology.manufacturing" id="mfg:dfm"

def "mfg:downtime_analysis" "Analyzing equipment downtime to improve availability."
ln mfg:downtime_analysis manufacturing.maintenance sys:is_a
set.add name="ontology.manufacturing" id="mfg:downtime_analysis"

def "mfg:eoq" "Economic Order Quantity — optimal order size minimizing cost."
ln mfg:eoq manufacturing.inventory sys:is_a
set.add name="ontology.manufacturing" id="mfg:eoq"

def "mfg:lead_time" "Time between ordering and receiving materials."
ln mfg:lead_time manufacturing.inventory sys:is_a
set.add name="ontology.manufacturing" id="mfg:lead_time"

def "mfg:load_leveling" "Balancing workload across time and resources."
ln mfg:load_leveling manufacturing.planning sys:is_a
set.add name="ontology.manufacturing" id="mfg:load_leveling"

def "mfg:mps" "Master Production Schedule — plan for what to produce and when."
ln mfg:mps manufacturing.planning sys:is_a
set.add name="ontology.manufacturing" id="mfg:mps"

def "mfg:mrp" "Material Requirements Planning — calculating needed materials and timing."
ln mfg:mrp manufacturing.planning sys:is_a
ln mfg:mrp mfg:procurement @depends_on
set.add name="ontology.manufacturing" id="mfg:mrp"

def "mfg:oee" "Overall Equipment Effectiveness — measure of equipment productivity."
ln mfg:oee manufacturing.maintenance sys:is_a
ln mfg:oee mfg:downtime_analysis @related_to
set.add name="ontology.manufacturing" id="mfg:oee"

def "mfg:predictive_maintenance" "Using data to predict and prevent equipment failures."
ln mfg:predictive_maintenance manufacturing.maintenance sys:is_a
set.add name="ontology.manufacturing" id="mfg:predictive_maintenance"

def "mfg:preventive_maintenance" "Scheduled maintenance to prevent failures."
ln mfg:preventive_maintenance manufacturing.maintenance sys:is_a
set.add name="ontology.manufacturing" id="mfg:preventive_maintenance"

def "mfg:process_flow" "Sequence of steps through which materials move in production."
ln mfg:process_flow manufacturing.process sys:is_a
set.add name="ontology.manufacturing" id="mfg:process_flow"

def "mfg:procurement" "Acquiring materials and components from suppliers."
ln mfg:procurement manufacturing.inventory sys:is_a
set.add name="ontology.manufacturing" id="mfg:procurement"

def "mfg:production_scheduling" "Assigning tasks to time slots and resources."
ln mfg:production_scheduling manufacturing.planning sys:is_a
set.add name="ontology.manufacturing" id="mfg:production_scheduling"

def "mfg:qa" "Quality Assurance — ensuring processes produce quality outputs."
ln mfg:qa manufacturing.quality sys:is_a
set.add name="ontology.manufacturing" id="mfg:qa"

def "mfg:qc" "Quality Control — inspecting outputs to ensure standards."
ln mfg:qc manufacturing.quality sys:is_a
set.add name="ontology.manufacturing" id="mfg:qc"

def "mfg:root_cause_analysis" "Identifying underlying causes of defects or failures."
ln mfg:root_cause_analysis manufacturing.quality sys:is_a
ln mfg:root_cause_analysis mfg:defect_rate @reduces
set.add name="ontology.manufacturing" id="mfg:root_cause_analysis"

def "mfg:safety_stock" "Extra inventory held to prevent stockouts."
ln mfg:safety_stock manufacturing.inventory sys:is_a
set.add name="ontology.manufacturing" id="mfg:safety_stock"

def "mfg:spc" "Statistical Process Control — monitoring processes using statistics."
ln mfg:spc manufacturing.quality sys:is_a
ln mfg:spc mfg:control_chart @supports
set.add name="ontology.manufacturing" id="mfg:spc"

def "mfg:standard_work" "Documented best method for performing a task."
ln mfg:standard_work manufacturing.engineering sys:is_a
set.add name="ontology.manufacturing" id="mfg:standard_work"

def "mfg:supplier_management" "Managing supplier relationships and performance."
ln mfg:supplier_management manufacturing.inventory sys:is_a
set.add name="ontology.manufacturing" id="mfg:supplier_management"

def "mfg:takt_time" "Rate at which products must be completed to meet demand."
ln mfg:takt_time manufacturing.process sys:is_a
ln mfg:takt_time mfg:production_scheduling @supports
set.add name="ontology.manufacturing" id="mfg:takt_time"

def "mfg:throughput" "Amount of output produced per unit time."
ln mfg:throughput manufacturing.process sys:is_a
set.add name="ontology.manufacturing" id="mfg:throughput"

def "mfg:tooling" "Tools, dies, and fixtures required for production."
ln mfg:tooling manufacturing.engineering sys:is_a
set.add name="ontology.manufacturing" id="mfg:tooling"

def "mfg:tpm" "Total Productive Maintenance — maximizing equipment effectiveness."
ln mfg:tpm manufacturing.maintenance sys:is_a
set.add name="ontology.manufacturing" id="mfg:tpm"
