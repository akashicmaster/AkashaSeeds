# Akasha ontology — namespace: supply_chain
# atoms: 6

def "supply_chain.inventory" "Inventory types, safety stock, warehouse management."
ln supply_chain.inventory ont.supply_chain sys:part_of
set.add name="ontology.supply_chain" id="supply_chain.inventory"

def "supply_chain.logistics" "Transportation, distribution, routing, and delivery."
ln supply_chain.logistics ont.supply_chain sys:part_of
set.add name="ontology.supply_chain" id="supply_chain.logistics"

def "supply_chain.operations" "Order management, fulfillment, throughput, and SCOR."
ln supply_chain.operations ont.supply_chain sys:part_of
set.add name="ontology.supply_chain" id="supply_chain.operations"

def "supply_chain.planning" "Demand planning, forecasting, S&OP, and replenishment."
ln supply_chain.planning ont.supply_chain sys:part_of
set.add name="ontology.supply_chain" id="supply_chain.planning"

def "supply_chain.procurement" "Sourcing, purchasing, supplier management, and contracts."
ln supply_chain.procurement ont.supply_chain sys:part_of
set.add name="ontology.supply_chain" id="supply_chain.procurement"

def "supply_chain.risk" "Supply chain risk, disruption, resilience, and redundancy."
ln supply_chain.risk ont.supply_chain sys:part_of
set.add name="ontology.supply_chain" id="supply_chain.risk"
