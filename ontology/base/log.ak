# Akasha ontology — namespace: log
# atoms: 21

def "log:air_transport" "Transportation of goods by aircraft."
ln log:air_transport logistics.transportation sys:is_a
set.add name="ontology.logistics" id="log:air_transport"

def "log:bill_of_lading" "Legal document issued by a carrier to acknowledge receipt of cargo."
ln log:bill_of_lading logistics.freight sys:is_a
set.add name="ontology.logistics" id="log:bill_of_lading"

def "log:carrier" "Company responsible for transporting goods."
ln log:carrier logistics.transportation sys:is_a
set.add name="ontology.logistics" id="log:carrier"

def "log:cross_docking" "Direct transfer of goods from inbound to outbound transport with minimal storage."
ln log:cross_docking logistics.warehousing sys:is_a
ln log:cross_docking log:fulfillment @supports
set.add name="ontology.logistics" id="log:cross_docking"

def "log:customs" "Regulations and processes for cross-border shipments."
ln log:customs logistics.freight sys:is_a
set.add name="ontology.logistics" id="log:customs"

def "log:delivery_scheduling" "Assigning delivery times and routes."
ln log:delivery_scheduling logistics.planning sys:is_a
set.add name="ontology.logistics" id="log:delivery_scheduling"

def "log:distribution_center" "Facility for receiving, sorting, and distributing goods."
ln log:distribution_center logistics.distribution sys:is_a
set.add name="ontology.logistics" id="log:distribution_center"

def "log:freight_class" "Classification of freight based on density, handling, and liability."
ln log:freight_class logistics.freight sys:is_a
set.add name="ontology.logistics" id="log:freight_class"

def "log:fulfillment" "Processing and shipping customer orders."
ln log:fulfillment logistics.distribution sys:is_a
set.add name="ontology.logistics" id="log:fulfillment"

def "log:hub" "Central node for consolidating and redistributing shipments."
ln log:hub logistics.distribution sys:is_a
ln log:hub log:distribution_center @related_to
set.add name="ontology.logistics" id="log:hub"

def "log:incoterms" "International commercial terms defining buyer/seller responsibilities."
ln log:incoterms logistics.freight sys:is_a
ln log:incoterms log:customs @related_to
set.add name="ontology.logistics" id="log:incoterms"

def "log:last_mile" "Final step of delivering goods to the end customer."
ln log:last_mile logistics.distribution sys:is_a
ln log:last_mile word:en:delivery @supports
set.add name="ontology.logistics" id="log:last_mile"

def "log:load_planning" "Optimizing how goods are loaded into transport vehicles."
ln log:load_planning logistics.planning sys:is_a
set.add name="ontology.logistics" id="log:load_planning"

def "log:packing" "Preparing goods for shipment."
ln log:packing logistics.warehousing sys:is_a
set.add name="ontology.logistics" id="log:packing"

def "log:picking" "Selecting items from storage to fulfill orders."
ln log:picking logistics.warehousing sys:is_a
set.add name="ontology.logistics" id="log:picking"

def "log:rail_transport" "Transportation of goods by train."
ln log:rail_transport logistics.transportation sys:is_a
set.add name="ontology.logistics" id="log:rail_transport"

def "log:route_optimization" "Algorithmic optimization of delivery routes."
ln log:route_optimization logistics.planning sys:is_a
set.add name="ontology.logistics" id="log:route_optimization"

def "log:routing" "Optimizing delivery routes for efficiency."
ln log:routing logistics.transportation sys:is_a
ln log:routing log:route_optimization @supports
set.add name="ontology.logistics" id="log:routing"

def "log:sea_transport" "Transportation of goods by ship or vessel."
ln log:sea_transport logistics.transportation sys:is_a
set.add name="ontology.logistics" id="log:sea_transport"

def "log:storage" "Storing goods in a controlled environment."
ln log:storage logistics.warehousing sys:is_a
set.add name="ontology.logistics" id="log:storage"

def "log:truck_transport" "Transportation of goods by truck."
ln log:truck_transport logistics.transportation sys:is_a
ln log:truck_transport log:load_planning @supports
set.add name="ontology.logistics" id="log:truck_transport"
