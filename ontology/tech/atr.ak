# Akasha ontology — namespace: atr
# atoms: 30

def "atr.intralogistics" "Intralogistics automation including AGV/AMR, conveyors, and warehouse robots."
set.add name="ontology.autonomous_transport" id="atr.intralogistics"

def "atr.logistics_automation" "Logistics automation including TMS, routing, and last-mile delivery."
set.add name="ontology.autonomous_transport" id="atr.logistics_automation"

def "atr.material_handling_equipment" "Material handling equipment including conveyors, lifters, and sorters."
set.add name="ontology.autonomous_transport" id="atr.material_handling_equipment"

def "atr.navigation" "Navigation and localization for autonomous transport systems."
set.add name="ontology.autonomous_transport" id="atr.navigation"

def "atr.safety" "Safety systems for autonomous transport and logistics."
set.add name="ontology.autonomous_transport" id="atr.safety"

def "atr.supply_chain" "Supply chain integration and orchestration."
set.add name="ontology.autonomous_transport" id="atr.supply_chain"

def "atr.warehouse_automation" "Warehouse automation including AS/RS, picking robots, and WMS integration."
set.add name="ontology.autonomous_transport" id="atr.warehouse_automation"

def "atr:agv" "Automated Guided Vehicle using fixed paths or markers."
ln atr:agv atr.intralogistics sys:is_a
set.add name="ontology.autonomous_transport" id="atr:agv"

def "atr:amr" "Autonomous Mobile Robot with SLAM-based navigation."
ln atr:amr atr.intralogistics sys:is_a
set.add name="ontology.autonomous_transport" id="atr:amr"

def "atr:asrs" "Automated Storage and Retrieval Systems."
ln atr:asrs atr.warehouse_automation sys:is_a
set.add name="ontology.autonomous_transport" id="atr:asrs"

def "atr:autonomous_forklift" "Autonomous forklift for pallet handling."
ln atr:autonomous_forklift atr.intralogistics sys:is_a
set.add name="ontology.autonomous_transport" id="atr:autonomous_forklift"

def "atr:collision_avoidance" "Collision avoidance systems."
ln atr:collision_avoidance atr.safety sys:is_a
set.add name="ontology.autonomous_transport" id="atr:collision_avoidance"

def "atr:conveyor" "Conveyor systems for continuous transport."
ln atr:conveyor atr.material_handling_equipment sys:is_a
ln atr:conveyor atr:asrs @integrates_with
set.add name="ontology.autonomous_transport" id="atr:conveyor"

def "atr:demand_forecasting" "Demand forecasting for supply chain."
ln atr:demand_forecasting atr.supply_chain sys:is_a
set.add name="ontology.autonomous_transport" id="atr:demand_forecasting"

def "atr:goods_to_person" "Goods-to-person automation systems."
ln atr:goods_to_person atr.warehouse_automation sys:is_a
ln atr:goods_to_person atr:picking_robot @cooperates_with
set.add name="ontology.autonomous_transport" id="atr:goods_to_person"

def "atr:inventory_robot" "Inventory scanning robots."
ln atr:inventory_robot atr.warehouse_automation sys:is_a
ln atr:inventory_robot atr:traceability @supports
set.add name="ontology.autonomous_transport" id="atr:inventory_robot"

def "atr:iso3691" "ISO 3691 safety standard for industrial trucks and AGVs."
ln atr:iso3691 atr.safety sys:is_a
set.add name="ontology.autonomous_transport" id="atr:iso3691"

def "atr:last_mile_robot" "Last-mile delivery robots."
ln atr:last_mile_robot atr.logistics_automation sys:is_a
set.add name="ontology.autonomous_transport" id="atr:last_mile_robot"

def "atr:lidar_nav" "LiDAR-based navigation."
ln atr:lidar_nav atr.navigation sys:is_a
set.add name="ontology.autonomous_transport" id="atr:lidar_nav"

def "atr:lifter" "Lifters and elevators for vertical transport."
ln atr:lifter atr.material_handling_equipment sys:is_a
set.add name="ontology.autonomous_transport" id="atr:lifter"

def "atr:performance_level_d" "Performance Level D safety requirements."
ln atr:performance_level_d atr.safety sys:is_a
set.add name="ontology.autonomous_transport" id="atr:performance_level_d"

def "atr:picking_robot" "Robot for automated item picking."
ln atr:picking_robot atr.intralogistics sys:is_a
set.add name="ontology.autonomous_transport" id="atr:picking_robot"

def "atr:routing_optimization" "Routing optimization for logistics."
ln atr:routing_optimization atr.logistics_automation sys:is_a
set.add name="ontology.autonomous_transport" id="atr:routing_optimization"

def "atr:rtk_gnss" "RTK-GNSS for high-precision outdoor navigation."
ln atr:rtk_gnss atr.navigation sys:is_a
set.add name="ontology.autonomous_transport" id="atr:rtk_gnss"

def "atr:scm" "Supply Chain Management systems."
ln atr:scm atr.supply_chain sys:is_a
set.add name="ontology.autonomous_transport" id="atr:scm"

def "atr:slam" "SLAM for autonomous navigation."
ln atr:slam atr.navigation sys:is_a
ln atr:slam atr:amr @enables
set.add name="ontology.autonomous_transport" id="atr:slam"

def "atr:sort_center_automation" "Automation of parcel sortation centers."
ln atr:sort_center_automation atr.logistics_automation sys:is_a
set.add name="ontology.autonomous_transport" id="atr:sort_center_automation"

def "atr:sorter" "Sorting machines for parcel and item routing."
ln atr:sorter atr.material_handling_equipment sys:is_a
set.add name="ontology.autonomous_transport" id="atr:sorter"

def "atr:traceability" "Traceability systems for goods and materials."
ln atr:traceability atr.supply_chain sys:is_a
set.add name="ontology.autonomous_transport" id="atr:traceability"

def "atr:vision_nav" "Vision-based navigation."
ln atr:vision_nav atr.navigation sys:is_a
set.add name="ontology.autonomous_transport" id="atr:vision_nav"
