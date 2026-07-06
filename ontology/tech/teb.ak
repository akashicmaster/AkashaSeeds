# Akasha ontology — namespace: teb
# atoms: 24

def "teb.congestion_control" "Congestion control and mitigation strategies."
set.add name="ontology.traffic_engineering_bridge" id="teb.congestion_control"

def "teb.demand_management" "Transportation demand management (TDM)."
set.add name="ontology.traffic_engineering_bridge" id="teb.demand_management"

def "teb.road_design" "Roadway and intersection geometric design."
set.add name="ontology.traffic_engineering_bridge" id="teb.road_design"

def "teb.signal_control" "Traffic signal control and coordination."
set.add name="ontology.traffic_engineering_bridge" id="teb.signal_control"

def "teb.traffic_flow" "Traffic flow theory and modeling."
set.add name="ontology.traffic_engineering_bridge" id="teb.traffic_flow"

def "teb.transport_engineering" "Transportation engineering as an integrated discipline."
set.add name="ontology.traffic_engineering_bridge" id="teb.transport_engineering"

def "teb:actuated_signal" "Actuated signal control."
ln teb:actuated_signal teb.signal_control sys:is_a
set.add name="ontology.traffic_engineering_bridge" id="teb:actuated_signal"

def "teb:cell_transmission_model" "Cell Transmission Model (CTM)."
ln teb:cell_transmission_model teb.traffic_flow sys:is_a
set.add name="ontology.traffic_engineering_bridge" id="teb:cell_transmission_model"

def "teb:congestion_pricing" "Congestion pricing and tolling."
ln teb:congestion_pricing teb.demand_management sys:is_a
ln teb:congestion_pricing teb:variable_speed @influences
set.add name="ontology.traffic_engineering_bridge" id="teb:congestion_pricing"

def "teb:coordinated_signal" "Coordinated signal control (green waves)."
ln teb:coordinated_signal teb.signal_control sys:is_a
ln teb:coordinated_signal teb:geometric_design @integrates_with
set.add name="ontology.traffic_engineering_bridge" id="teb:coordinated_signal"

def "teb:fixed_time_signal" "Fixed-time signal control."
ln teb:fixed_time_signal teb.signal_control sys:is_a
set.add name="ontology.traffic_engineering_bridge" id="teb:fixed_time_signal"

def "teb:freeway_design" "Freeway and interchange design."
ln teb:freeway_design teb.road_design sys:is_a
set.add name="ontology.traffic_engineering_bridge" id="teb:freeway_design"

def "teb:fundamental_diagram" "Fundamental diagram of traffic flow."
ln teb:fundamental_diagram teb.traffic_flow sys:is_a
ln teb:fundamental_diagram teb:ramp_metering @informs
set.add name="ontology.traffic_engineering_bridge" id="teb:fundamental_diagram"

def "teb:geometric_design" "Geometric design of roads and intersections."
ln teb:geometric_design teb.road_design sys:is_a
set.add name="ontology.traffic_engineering_bridge" id="teb:geometric_design"

def "teb:lane_control" "Lane control and dynamic lane assignment."
ln teb:lane_control teb.congestion_control sys:is_a
set.add name="ontology.traffic_engineering_bridge" id="teb:lane_control"

def "teb:microscopic_model" "Microscopic car-following models."
ln teb:microscopic_model teb.traffic_flow sys:is_a
ln teb:microscopic_model teb:actuated_signal @supports
set.add name="ontology.traffic_engineering_bridge" id="teb:microscopic_model"

def "teb:public_transport_shift" "Modal shift to public transport."
ln teb:public_transport_shift teb.demand_management sys:is_a
set.add name="ontology.traffic_engineering_bridge" id="teb:public_transport_shift"

def "teb:ramp_metering" "Ramp metering for freeway congestion control."
ln teb:ramp_metering teb.congestion_control sys:is_a
set.add name="ontology.traffic_engineering_bridge" id="teb:ramp_metering"

def "teb:road_safety" "Road safety engineering."
ln teb:road_safety teb.transport_engineering sys:is_a
set.add name="ontology.traffic_engineering_bridge" id="teb:road_safety"

def "teb:roundabout" "Roundabout design."
ln teb:roundabout teb.road_design sys:is_a
set.add name="ontology.traffic_engineering_bridge" id="teb:roundabout"

def "teb:telework" "Telework and trip reduction strategies."
ln teb:telework teb.demand_management sys:is_a
set.add name="ontology.traffic_engineering_bridge" id="teb:telework"

def "teb:traffic_operations" "Traffic operations and control."
ln teb:traffic_operations teb.transport_engineering sys:is_a
set.add name="ontology.traffic_engineering_bridge" id="teb:traffic_operations"

def "teb:transport_planning" "Transportation planning."
ln teb:transport_planning teb.transport_engineering sys:is_a
ln teb:transport_planning teb.demand_management @requires
set.add name="ontology.traffic_engineering_bridge" id="teb:transport_planning"

def "teb:variable_speed" "Variable speed limits."
ln teb:variable_speed teb.congestion_control sys:is_a
set.add name="ontology.traffic_engineering_bridge" id="teb:variable_speed"
