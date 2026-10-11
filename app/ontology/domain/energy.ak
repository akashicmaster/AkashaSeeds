# Akasha ontology — namespace: energy
# atoms: 30

def "energy.conversion" "Energy conversion technologies."
set.add name="ontology.energy_systems" id="energy.conversion"

def "energy.decarbonization" "Decarbonization, policy, and energy markets."
set.add name="ontology.energy_systems" id="energy.decarbonization"

def "energy.demand" "Energy consumption and demand sectors."
set.add name="ontology.energy_systems" id="energy.demand"

def "energy.generation" "Energy generation including renewable and conventional sources."
set.add name="ontology.energy_systems" id="energy.generation"

def "energy.grid" "Transmission and distribution networks."
set.add name="ontology.energy_systems" id="energy.grid"

def "energy.management" "Energy management systems and smart grid control."
set.add name="ontology.energy_systems" id="energy.management"

def "energy.storage" "Energy storage systems."
set.add name="ontology.energy_systems" id="energy.storage"

def "energy:battery_storage" "Battery energy storage systems."
ln energy:battery_storage energy.storage sys:is_a
set.add name="ontology.energy_systems" id="energy:battery_storage"

def "energy:carbon_management" "Carbon management and emissions reduction."
ln energy:carbon_management energy.decarbonization sys:is_a
set.add name="ontology.energy_systems" id="energy:carbon_management"

def "energy:chp" "Combined Heat and Power (CHP)."
ln energy:chp energy.conversion sys:is_a
set.add name="ontology.energy_systems" id="energy:chp"

def "energy:demand_response" "Demand response systems."
ln energy:demand_response energy.management sys:is_a
set.add name="ontology.energy_systems" id="energy:demand_response"

def "energy:distribution" "Distribution networks."
ln energy:distribution energy.grid sys:is_a
set.add name="ontology.energy_systems" id="energy:distribution"

def "energy:ems" "Energy Management Systems (EMS)."
ln energy:ems energy.management sys:is_a
set.add name="ontology.energy_systems" id="energy:ems"

def "energy:forecasting" "Energy forecasting and optimization."
ln energy:forecasting energy.management sys:is_a
set.add name="ontology.energy_systems" id="energy:forecasting"

def "energy:fossil" "Fossil fuel-based generation."
ln energy:fossil energy.generation sys:is_a
set.add name="ontology.energy_systems" id="energy:fossil"

def "energy:hydro" "Hydropower generation."
ln energy:hydro energy.generation sys:is_a
set.add name="ontology.energy_systems" id="energy:hydro"

def "energy:hydrogen" "Hydrogen production and conversion."
ln energy:hydrogen energy.conversion sys:is_a
ln energy:hydrogen energy:power_to_x @supports
set.add name="ontology.energy_systems" id="energy:hydrogen"

def "energy:industrial" "Industrial energy consumption."
ln energy:industrial energy.demand sys:is_a
set.add name="ontology.energy_systems" id="energy:industrial"

def "energy:market" "Energy markets and trading."
ln energy:market energy.decarbonization sys:is_a
set.add name="ontology.energy_systems" id="energy:market"

def "energy:microgrid" "Local microgrids."
ln energy:microgrid energy.grid sys:is_a
ln energy:microgrid energy:ems @controlled_by
ln energy:microgrid off:disaster_autonomy @enables
set.add name="ontology.energy_systems" id="energy:microgrid"

def "energy:nuclear" "Nuclear power generation."
ln energy:nuclear energy.generation sys:is_a
set.add name="ontology.energy_systems" id="energy:nuclear"

def "energy:policy" "Energy policy and regulation."
ln energy:policy energy.decarbonization sys:is_a
set.add name="ontology.energy_systems" id="energy:policy"

def "energy:power_to_x" "Power-to-X conversion technologies."
ln energy:power_to_x energy.conversion sys:is_a
set.add name="ontology.energy_systems" id="energy:power_to_x"

def "energy:pumped_hydro" "Pumped hydro storage."
ln energy:pumped_hydro energy.storage sys:is_a
set.add name="ontology.energy_systems" id="energy:pumped_hydro"

def "energy:residential" "Residential energy consumption."
ln energy:residential energy.demand sys:is_a
set.add name="ontology.energy_systems" id="energy:residential"

def "energy:solar" "Solar photovoltaic and thermal generation."
ln energy:solar energy.generation sys:is_a
ln energy:solar energy:battery_storage @charges
set.add name="ontology.energy_systems" id="energy:solar"

def "energy:thermal_storage" "Thermal energy storage."
ln energy:thermal_storage energy.storage sys:is_a
set.add name="ontology.energy_systems" id="energy:thermal_storage"

def "energy:transmission" "High-voltage transmission networks."
ln energy:transmission energy.grid sys:is_a
set.add name="ontology.energy_systems" id="energy:transmission"

def "energy:transport" "Transport sector energy use (EV, rail, logistics)."
ln energy:transport energy.demand sys:is_a
set.add name="ontology.energy_systems" id="energy:transport"

def "energy:wind" "Wind power generation."
ln energy:wind energy.generation sys:is_a
ln energy:wind energy:forecasting @influences
set.add name="ontology.energy_systems" id="energy:wind"
