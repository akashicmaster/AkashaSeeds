# Akasha ontology — namespace: sg
# atoms: 34

def "sg.communication" "Communication networks for smart grid."
set.add name="ontology.smart_grid" id="sg.communication"

def "sg.cybersecurity" "Cybersecurity for smart grid systems."
set.add name="ontology.smart_grid" id="sg.cybersecurity"

def "sg.demand_response" "Demand response and load flexibility."
set.add name="ontology.smart_grid" id="sg.demand_response"

def "sg.distributed_energy" "Distributed energy resources and integration."
set.add name="ontology.smart_grid" id="sg.distributed_energy"

def "sg.forecasting" "Forecasting and optimization."
set.add name="ontology.smart_grid" id="sg.forecasting"

def "sg.grid_control" "Grid control, automation, and stability management."
set.add name="ontology.smart_grid" id="sg.grid_control"

def "sg.market" "Energy markets and trading integration."
set.add name="ontology.smart_grid" id="sg.market"

def "sg.metering" "Advanced metering and measurement systems."
set.add name="ontology.smart_grid" id="sg.metering"

def "sg:ami" "Advanced Metering Infrastructure."
ln sg:ami sg.metering sys:is_a
set.add name="ontology.smart_grid" id="sg:ami"

def "sg:authentication" "Authentication and access control."
ln sg:authentication sg.cybersecurity sys:is_a
set.add name="ontology.smart_grid" id="sg:authentication"

def "sg:cellular_5g" "5G cellular communication for grid."
ln sg:cellular_5g sg.communication sys:is_a
ln sg:cellular_5g sg:scada @connects
set.add name="ontology.smart_grid" id="sg:cellular_5g"

def "sg:dr_event" "Demand response event control."
ln sg:dr_event sg.demand_response sys:is_a
set.add name="ontology.smart_grid" id="sg:dr_event"

def "sg:dynamic_pricing" "Dynamic pricing for demand flexibility."
ln sg:dynamic_pricing sg.demand_response sys:is_a
set.add name="ontology.smart_grid" id="sg:dynamic_pricing"

def "sg:energy_trading" "Energy trading platforms."
ln sg:energy_trading sg.market sys:is_a
set.add name="ontology.smart_grid" id="sg:energy_trading"

def "sg:ev_integration" "Electric vehicle grid integration (V2G)."
ln sg:ev_integration sg.distributed_energy sys:is_a
set.add name="ontology.smart_grid" id="sg:ev_integration"

def "sg:feeder_automation" "Feeder automation and fault isolation."
ln sg:feeder_automation sg.grid_control sys:is_a
set.add name="ontology.smart_grid" id="sg:feeder_automation"

def "sg:fiber_network" "Fiber-optic communication for grid."
ln sg:fiber_network sg.communication sys:is_a
set.add name="ontology.smart_grid" id="sg:fiber_network"

def "sg:intrusion_detection" "Intrusion detection for grid networks."
ln sg:intrusion_detection sg.cybersecurity sys:is_a
set.add name="ontology.smart_grid" id="sg:intrusion_detection"

def "sg:load_control" "Automated load control systems."
ln sg:load_control sg.demand_response sys:is_a
set.add name="ontology.smart_grid" id="sg:load_control"

def "sg:load_forecasting" "Load forecasting."
ln sg:load_forecasting sg.forecasting sys:is_a
ln sg:load_forecasting sg:dynamic_pricing @influences
set.add name="ontology.smart_grid" id="sg:load_forecasting"

def "sg:meter_data_management" "Meter data management systems."
ln sg:meter_data_management sg.metering sys:is_a
set.add name="ontology.smart_grid" id="sg:meter_data_management"

def "sg:microgrid" "Local microgrids with autonomous control."
ln sg:microgrid sg.distributed_energy sys:is_a
ln sg:microgrid sg:optimization @optimized_by
set.add name="ontology.smart_grid" id="sg:microgrid"

def "sg:optimization" "Grid optimization algorithms."
ln sg:optimization sg.forecasting sys:is_a
set.add name="ontology.smart_grid" id="sg:optimization"

def "sg:powerline_comm" "Power Line Communication (PLC)."
ln sg:powerline_comm sg.communication sys:is_a
set.add name="ontology.smart_grid" id="sg:powerline_comm"

def "sg:renewable_forecasting" "Renewable generation forecasting."
ln sg:renewable_forecasting sg.forecasting sys:is_a
set.add name="ontology.smart_grid" id="sg:renewable_forecasting"

def "sg:retail_market" "Retail electricity markets."
ln sg:retail_market sg.market sys:is_a
set.add name="ontology.smart_grid" id="sg:retail_market"

def "sg:rtu" "Remote Terminal Units."
ln sg:rtu sg.grid_control sys:is_a
set.add name="ontology.smart_grid" id="sg:rtu"

def "sg:scada" "SCADA systems for grid monitoring."
ln sg:scada sg.grid_control sys:is_a
set.add name="ontology.smart_grid" id="sg:scada"

def "sg:smart_inverter" "Smart inverters for DER control."
ln sg:smart_inverter sg.grid_control sys:is_a
set.add name="ontology.smart_grid" id="sg:smart_inverter"

def "sg:smart_meter" "Smart meters for real-time measurement."
ln sg:smart_meter sg.metering sys:is_a
ln sg:smart_meter sg:dr_event @informs
set.add name="ontology.smart_grid" id="sg:smart_meter"

def "sg:solar_pv" "Distributed solar PV systems."
ln sg:solar_pv sg.distributed_energy sys:is_a
ln sg:solar_pv sg:smart_inverter @controlled_by
set.add name="ontology.smart_grid" id="sg:solar_pv"

def "sg:system_hardening" "System hardening for grid devices."
ln sg:system_hardening sg.cybersecurity sys:is_a
set.add name="ontology.smart_grid" id="sg:system_hardening"

def "sg:wholesale_market" "Wholesale electricity markets."
ln sg:wholesale_market sg.market sys:is_a
set.add name="ontology.smart_grid" id="sg:wholesale_market"

def "sg:wind_turbine" "Small-scale wind turbines."
ln sg:wind_turbine sg.distributed_energy sys:is_a
set.add name="ontology.smart_grid" id="sg:wind_turbine"
