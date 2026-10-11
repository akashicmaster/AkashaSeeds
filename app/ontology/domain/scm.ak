# Akasha ontology — namespace: scm
# atoms: 29

def "scm:bottleneck" "The slowest step limiting supply chain throughput."
ln scm:bottleneck supply_chain.operations sys:is_a
ln scm:bottleneck scm:flow_time @limits
set.add name="ontology.supply_chain" id="scm:bottleneck"

def "scm:contract_negotiation" "Negotiating terms and agreements with suppliers."
ln scm:contract_negotiation supply_chain.procurement sys:is_a
set.add name="ontology.supply_chain" id="scm:contract_negotiation"

def "scm:demand_planning" "Process of forecasting and planning customer demand."
ln scm:demand_planning supply_chain.planning sys:is_a
set.add name="ontology.supply_chain" id="scm:demand_planning"

def "scm:disruption" "Events that interrupt supply chain flow."
ln scm:disruption supply_chain.risk sys:is_a
set.add name="ontology.supply_chain" id="scm:disruption"

def "scm:distribution_center" "Facility for receiving, storing, and distributing goods."
ln scm:distribution_center supply_chain.logistics sys:is_a
set.add name="ontology.supply_chain" id="scm:distribution_center"

def "scm:eoq" "Economic Order Quantity — optimal order size minimizing cost."
ln scm:eoq supply_chain.inventory sys:is_a
set.add name="ontology.supply_chain" id="scm:eoq"

def "scm:flow_time" "Time required for goods to move through the supply chain."
ln scm:flow_time supply_chain.operations sys:is_a
set.add name="ontology.supply_chain" id="scm:flow_time"

def "scm:freight" "Shipping goods via air, sea, rail, or truck."
ln scm:freight supply_chain.logistics sys:is_a
set.add name="ontology.supply_chain" id="scm:freight"

def "scm:fulfillment" "Picking, packing, and shipping goods to customers."
ln scm:fulfillment supply_chain.operations sys:is_a
set.add name="ontology.supply_chain" id="scm:fulfillment"

def "scm:inventory_types" "Categories of inventory such as raw materials, WIP, and finished goods."
ln scm:inventory_types supply_chain.inventory sys:is_a
set.add name="ontology.supply_chain" id="scm:inventory_types"

def "scm:last_mile_delivery" "Final step of delivering goods to the end customer."
ln scm:last_mile_delivery supply_chain.logistics sys:is_a
set.add name="ontology.supply_chain" id="scm:last_mile_delivery"

def "scm:lead_time" "Time between placing an order and receiving goods."
ln scm:lead_time supply_chain.procurement sys:is_a
set.add name="ontology.supply_chain" id="scm:lead_time"

def "scm:multi_sourcing" "Using multiple suppliers to reduce dependency risk."
ln scm:multi_sourcing supply_chain.risk sys:is_a
set.add name="ontology.supply_chain" id="scm:multi_sourcing"

def "scm:order_management" "Managing customer orders from receipt to fulfillment."
ln scm:order_management supply_chain.operations sys:is_a
set.add name="ontology.supply_chain" id="scm:order_management"

def "scm:redundancy" "Backup capacity or suppliers to reduce risk."
ln scm:redundancy supply_chain.risk sys:is_a
set.add name="ontology.supply_chain" id="scm:redundancy"

def "scm:reorder_point" "Inventory level at which replenishment is triggered."
ln scm:reorder_point supply_chain.inventory sys:is_a
set.add name="ontology.supply_chain" id="scm:reorder_point"

def "scm:replenishment" "Process of restocking inventory to meet demand."
ln scm:replenishment supply_chain.planning sys:is_a
set.add name="ontology.supply_chain" id="scm:replenishment"

def "scm:resilience" "Ability of the supply chain to recover from disruptions."
ln scm:resilience supply_chain.risk sys:is_a
ln scm:resilience scm:redundancy @supports
set.add name="ontology.supply_chain" id="scm:resilience"

def "scm:risk_management" "Identifying and mitigating supply chain risks."
ln scm:risk_management supply_chain.risk sys:is_a
set.add name="ontology.supply_chain" id="scm:risk_management"

def "scm:routing" "Optimizing delivery routes for efficiency."
ln scm:routing supply_chain.logistics sys:is_a
set.add name="ontology.supply_chain" id="scm:routing"

def "scm:safety_stock" "Extra inventory held to prevent stockouts."
ln scm:safety_stock supply_chain.inventory sys:is_a
set.add name="ontology.supply_chain" id="scm:safety_stock"

def "scm:scor_model" "Supply Chain Operations Reference model for process standardization."
ln scm:scor_model supply_chain.operations sys:is_a
ln scm:scor_model supply_chain.operations @structures
set.add name="ontology.supply_chain" id="scm:scor_model"

def "scm:sop" "Sales & Operations Planning — aligning demand, supply, and financial plans."
ln scm:sop supply_chain.planning sys:is_a
set.add name="ontology.supply_chain" id="scm:sop"

def "scm:sourcing" "Identifying and selecting suppliers for goods and services."
ln scm:sourcing supply_chain.procurement sys:is_a
ln scm:sourcing scm:supplier_management @supports
set.add name="ontology.supply_chain" id="scm:sourcing"

def "scm:supplier_management" "Managing supplier relationships, performance, and compliance."
ln scm:supplier_management supply_chain.procurement sys:is_a
set.add name="ontology.supply_chain" id="scm:supplier_management"

def "scm:supply_planning" "Ensuring supply capacity meets forecasted demand."
ln scm:supply_planning supply_chain.planning sys:is_a
set.add name="ontology.supply_chain" id="scm:supply_planning"

def "scm:third_party_logistics" "Outsourced logistics services (3PL/4PL)."
ln scm:third_party_logistics supply_chain.logistics sys:is_a
set.add name="ontology.supply_chain" id="scm:third_party_logistics"

def "scm:transportation" "Movement of goods across locations."
ln scm:transportation supply_chain.logistics sys:is_a
set.add name="ontology.supply_chain" id="scm:transportation"

def "scm:warehouse_management" "Managing storage, picking, packing, and movement of goods."
ln scm:warehouse_management supply_chain.inventory sys:is_a
ln scm:warehouse_management scm:fulfillment @supports
set.add name="ontology.supply_chain" id="scm:warehouse_management"
