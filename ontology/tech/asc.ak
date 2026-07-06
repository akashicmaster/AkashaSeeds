# Akasha ontology — namespace: asc
# atoms: 40

def "asc.distribution" "Wholesale and distribution centers."
set.add name="ontology.agri_supply_chain" id="asc.distribution"

def "asc.harvest" "Harvesting and field collection."
set.add name="ontology.agri_supply_chain" id="asc.harvest"

def "asc.logistics" "Transport and logistics networks."
set.add name="ontology.agri_supply_chain" id="asc.logistics"

def "asc.post_harvest" "Post-harvest handling and quality control."
set.add name="ontology.agri_supply_chain" id="asc.post_harvest"

def "asc.processing" "Food processing and transformation."
set.add name="ontology.agri_supply_chain" id="asc.processing"

def "asc.production" "Crop production and cultivation."
set.add name="ontology.agri_supply_chain" id="asc.production"

def "asc.retail" "Retail, markets, and consumer delivery."
set.add name="ontology.agri_supply_chain" id="asc.retail"

def "asc.storage" "Storage, cold chain, and preservation."
set.add name="ontology.agri_supply_chain" id="asc.storage"

def "asc.sustainability" "Sustainability and waste reduction."
set.add name="ontology.agri_supply_chain" id="asc.sustainability"

def "asc.traceability" "Traceability, certification, and data flows."
set.add name="ontology.agri_supply_chain" id="asc.traceability"

def "asc:automation_link" "Integration with agricultural automation."
ln asc:automation_link asc.production sys:is_a
ln asc:automation_link asc:crop_planning @optimizes
set.add name="ontology.agri_supply_chain" id="asc:automation_link"

def "asc:barcode_qr" "Barcode/QR-based tracking."
ln asc:barcode_qr asc.traceability sys:is_a
set.add name="ontology.agri_supply_chain" id="asc:barcode_qr"

def "asc:blockchain_trace" "Blockchain-based traceability."
ln asc:blockchain_trace asc.traceability sys:is_a
ln asc:blockchain_trace asc:market_distribution @verifies
set.add name="ontology.agri_supply_chain" id="asc:blockchain_trace"

def "asc:carbon_footprint" "Carbon footprint tracking."
ln asc:carbon_footprint asc.sustainability sys:is_a
set.add name="ontology.agri_supply_chain" id="asc:carbon_footprint"

def "asc:certification" "Certification and compliance."
ln asc:certification asc.traceability sys:is_a
set.add name="ontology.agri_supply_chain" id="asc:certification"

def "asc:circular_agri" "Circular agriculture and reuse."
ln asc:circular_agri asc.sustainability sys:is_a
set.add name="ontology.agri_supply_chain" id="asc:circular_agri"

def "asc:cold_chain" "Cold chain storage."
ln asc:cold_chain asc.storage sys:is_a
ln asc:cold_chain asc:food_safety @enables
set.add name="ontology.agri_supply_chain" id="asc:cold_chain"

def "asc:crop_planning" "Crop planning and rotation."
ln asc:crop_planning asc.production sys:is_a
set.add name="ontology.agri_supply_chain" id="asc:crop_planning"

def "asc:distribution_center" "Distribution centers."
ln asc:distribution_center asc.distribution sys:is_a
set.add name="ontology.agri_supply_chain" id="asc:distribution_center"

def "asc:drone_collection" "Drone-assisted collection."
ln asc:drone_collection asc.harvest sys:is_a
set.add name="ontology.agri_supply_chain" id="asc:drone_collection"

def "asc:drone_logistics" "Drone-based logistics."
ln asc:drone_logistics asc.logistics sys:is_a
ln asc:drone_logistics asc:last_mile @supports
set.add name="ontology.agri_supply_chain" id="asc:drone_logistics"

def "asc:food_safety" "Food safety and compliance."
ln asc:food_safety asc.processing sys:is_a
set.add name="ontology.agri_supply_chain" id="asc:food_safety"

def "asc:ground_transport" "Ground transport logistics."
ln asc:ground_transport asc.logistics sys:is_a
set.add name="ontology.agri_supply_chain" id="asc:ground_transport"

def "asc:last_mile" "Last-mile delivery."
ln asc:last_mile asc.retail sys:is_a
set.add name="ontology.agri_supply_chain" id="asc:last_mile"

def "asc:logistics_coordination" "Logistics coordination and routing."
ln asc:logistics_coordination asc.logistics sys:is_a
set.add name="ontology.agri_supply_chain" id="asc:logistics_coordination"

def "asc:manual_harvest" "Manual harvesting."
ln asc:manual_harvest asc.harvest sys:is_a
set.add name="ontology.agri_supply_chain" id="asc:manual_harvest"

def "asc:market_distribution" "Market and regional distribution."
ln asc:market_distribution asc.distribution sys:is_a
set.add name="ontology.agri_supply_chain" id="asc:market_distribution"

def "asc:online_retail" "Online retail and e-commerce."
ln asc:online_retail asc.retail sys:is_a
set.add name="ontology.agri_supply_chain" id="asc:online_retail"

def "asc:preservation" "Preservation and shelf-life extension."
ln asc:preservation asc.storage sys:is_a
set.add name="ontology.agri_supply_chain" id="asc:preservation"

def "asc:primary_processing" "Primary processing (cutting, milling)."
ln asc:primary_processing asc.processing sys:is_a
set.add name="ontology.agri_supply_chain" id="asc:primary_processing"

def "asc:quality_control" "Quality control and inspection."
ln asc:quality_control asc.post_harvest sys:is_a
set.add name="ontology.agri_supply_chain" id="asc:quality_control"

def "asc:robotic_harvest" "Robotic harvesting."
ln asc:robotic_harvest asc.harvest sys:is_a
ln asc:robotic_harvest asc:sorting @feeds
set.add name="ontology.agri_supply_chain" id="asc:robotic_harvest"

def "asc:secondary_processing" "Secondary processing (packaging, cooking)."
ln asc:secondary_processing asc.processing sys:is_a
set.add name="ontology.agri_supply_chain" id="asc:secondary_processing"

def "asc:silo_storage" "Silo and bulk storage."
ln asc:silo_storage asc.storage sys:is_a
set.add name="ontology.agri_supply_chain" id="asc:silo_storage"

def "asc:soil_management" "Soil and nutrient management."
ln asc:soil_management asc.production sys:is_a
set.add name="ontology.agri_supply_chain" id="asc:soil_management"

def "asc:sorting" "Sorting and grading."
ln asc:sorting asc.post_harvest sys:is_a
set.add name="ontology.agri_supply_chain" id="asc:sorting"

def "asc:storefront" "Retail stores and supermarkets."
ln asc:storefront asc.retail sys:is_a
set.add name="ontology.agri_supply_chain" id="asc:storefront"

def "asc:washing" "Washing and cleaning."
ln asc:washing asc.post_harvest sys:is_a
set.add name="ontology.agri_supply_chain" id="asc:washing"

def "asc:waste_reduction" "Food waste reduction."
ln asc:waste_reduction asc.sustainability sys:is_a
set.add name="ontology.agri_supply_chain" id="asc:waste_reduction"

def "asc:wholesale" "Wholesale distribution."
ln asc:wholesale asc.distribution sys:is_a
set.add name="ontology.agri_supply_chain" id="asc:wholesale"
