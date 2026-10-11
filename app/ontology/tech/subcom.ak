# Akasha ontology — namespace: subcom
# atoms: 29

def "subcom.capacity" "Transmission technologies including WDM, coherent optics, and SDM."
ln subcom.capacity ont.submarine_communications sys:part_of
set.add name="ontology.submarine_communications" id="subcom.capacity"

def "subcom.infrastructure" "Physical submarine cable infrastructure including fiber, repeaters, branching units, and landing stations."
ln subcom.infrastructure ont.submarine_communications sys:part_of
set.add name="ontology.submarine_communications" id="subcom.infrastructure"

def "subcom.landing" "Cable landing stations, IX connectivity, and data center interconnection."
ln subcom.landing ont.submarine_communications sys:part_of
set.add name="ontology.submarine_communications" id="subcom.landing"

def "subcom.operations" "Cable laying, maintenance, monitoring, and repair operations."
ln subcom.operations ont.submarine_communications sys:part_of
set.add name="ontology.submarine_communications" id="subcom.operations"

def "subcom.regulation" "Regulation, treaties, EEZ, and geopolitical considerations."
ln subcom.regulation ont.submarine_communications sys:part_of
set.add name="ontology.submarine_communications" id="subcom.regulation"

def "subcom.routing" "International routing paths, BGP, redundancy, and global backbone topology."
ln subcom.routing ont.submarine_communications sys:part_of
set.add name="ontology.submarine_communications" id="subcom.routing"

def "subcom.security" "Security risks including tapping, sabotage, encryption, and physical protection."
ln subcom.security ont.submarine_communications sys:part_of
set.add name="ontology.submarine_communications" id="subcom.security"

def "subcom:bgp_international" "BGP routing for international traffic."
ln subcom:bgp_international subcom.routing sys:is_a
set.add name="ontology.submarine_communications" id="subcom:bgp_international"

def "subcom:branching_unit" "Device enabling cable branching to multiple destinations."
ln subcom:branching_unit subcom.infrastructure sys:is_a
set.add name="ontology.submarine_communications" id="subcom:branching_unit"

def "subcom:cable_cut" "Intentional or accidental cable damage."
ln subcom:cable_cut subcom.security sys:is_a
set.add name="ontology.submarine_communications" id="subcom:cable_cut"

def "subcom:cable_ship" "Ship used for laying and repairing submarine cables."
ln subcom:cable_ship subcom.operations sys:is_a
set.add name="ontology.submarine_communications" id="subcom:cable_ship"

def "subcom:cable_treaty" "International submarine cable protection treaties."
ln subcom:cable_treaty subcom.regulation sys:is_a
set.add name="ontology.submarine_communications" id="subcom:cable_treaty"

def "subcom:coherent" "Coherent optical transmission."
ln subcom:coherent subcom.capacity sys:is_a
set.add name="ontology.submarine_communications" id="subcom:coherent"

def "subcom:data_center" "Data center connected to landing stations."
ln subcom:data_center subcom.landing sys:is_a
set.add name="ontology.submarine_communications" id="subcom:data_center"

def "subcom:eez" "Exclusive Economic Zone regulations."
ln subcom:eez subcom.regulation sys:is_a
set.add name="ontology.submarine_communications" id="subcom:eez"

def "subcom:encryption" "Encryption for international traffic."
ln subcom:encryption subcom.security sys:is_a
set.add name="ontology.submarine_communications" id="subcom:encryption"

def "subcom:eurasia" "Asia–Europe submarine cable routes."
ln subcom:eurasia subcom.routing sys:is_a
set.add name="ontology.submarine_communications" id="subcom:eurasia"

def "subcom:fiber" "Optical fiber forming the core of submarine cables."
ln subcom:fiber subcom.infrastructure sys:is_a
set.add name="ontology.submarine_communications" id="subcom:fiber"

def "subcom:geopolitics" "Geopolitical risks affecting submarine cables."
ln subcom:geopolitics subcom.regulation sys:is_a
ln subcom:geopolitics subcom:cable_cut @influences
set.add name="ontology.submarine_communications" id="subcom:geopolitics"

def "subcom:ix" "Internet Exchange for international traffic exchange."
ln subcom:ix subcom.landing sys:is_a
set.add name="ontology.submarine_communications" id="subcom:ix"

def "subcom:landing_station" "Cable landing station connecting submarine cables to terrestrial networks."
ln subcom:landing_station subcom.infrastructure sys:is_a
ln subcom:landing_station subcom:ix @connects
set.add name="ontology.submarine_communications" id="subcom:landing_station"

def "subcom:otdr" "Optical Time Domain Reflectometry for fault detection."
ln subcom:otdr subcom.operations sys:is_a
ln subcom:otdr subcom:repair @supports
set.add name="ontology.submarine_communications" id="subcom:otdr"

def "subcom:repair" "Submarine cable repair operations."
ln subcom:repair subcom.operations sys:is_a
set.add name="ontology.submarine_communications" id="subcom:repair"

def "subcom:repeater" "Amplifier placed along the cable to boost optical signals."
ln subcom:repeater subcom.infrastructure sys:is_a
ln subcom:repeater subcom:coherent @supports
set.add name="ontology.submarine_communications" id="subcom:repeater"

def "subcom:sdm" "Space Division Multiplexing for submarine cables."
ln subcom:sdm subcom.capacity sys:is_a
ln subcom:sdm subcom:wdm @enhances
set.add name="ontology.submarine_communications" id="subcom:sdm"

def "subcom:tapping" "Risk of submarine cable interception."
ln subcom:tapping subcom.security sys:is_a
set.add name="ontology.submarine_communications" id="subcom:tapping"

def "subcom:transatlantic" "Trans-Atlantic submarine cable routes."
ln subcom:transatlantic subcom.routing sys:is_a
set.add name="ontology.submarine_communications" id="subcom:transatlantic"

def "subcom:transpacific" "Trans-Pacific submarine cable routes."
ln subcom:transpacific subcom.routing sys:is_a
set.add name="ontology.submarine_communications" id="subcom:transpacific"

def "subcom:wdm" "Wavelength Division Multiplexing."
ln subcom:wdm subcom.capacity sys:is_a
set.add name="ontology.submarine_communications" id="subcom:wdm"
