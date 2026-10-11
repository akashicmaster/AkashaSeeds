# Akasha ontology — namespace: mcom
# atoms: 34

def "mcom:5g_nr" "5G New Radio."
ln mcom:5g_nr mobile.radio sys:is_a
ln mcom:5g_nr mcom:sa @supports
set.add name="ontology.mobile_communications" id="mcom:5g_nr"

def "mcom:5gc" "5G Core with service-based architecture."
ln mcom:5gc mobile.core sys:is_a
set.add name="ontology.mobile_communications" id="mcom:5gc"

def "mcom:amf" "Access and Mobility Management Function."
ln mcom:amf mobile.core sys:is_a
set.add name="ontology.mobile_communications" id="mcom:amf"

def "mcom:beamforming" "Directional signal transmission."
ln mcom:beamforming mobile.radio sys:is_a
ln mcom:beamforming mcom:massive_mimo @supports
set.add name="ontology.mobile_communications" id="mcom:beamforming"

def "mcom:cqi" "Channel Quality Indicator."
ln mcom:cqi mobile.operations sys:is_a
set.add name="ontology.mobile_communications" id="mcom:cqi"

def "mcom:cran" "Centralized RAN."
ln mcom:cran mobile.architecture sys:is_a
set.add name="ontology.mobile_communications" id="mcom:cran"

def "mcom:dss" "Dynamic Spectrum Sharing."
ln mcom:dss mobile.spectrum sys:is_a
ln mcom:dss mcom:sub6 @supports
set.add name="ontology.mobile_communications" id="mcom:dss"

def "mcom:embb" "Enhanced Mobile Broadband."
ln mcom:embb mobile.services sys:is_a
set.add name="ontology.mobile_communications" id="mcom:embb"

def "mcom:epc" "Evolved Packet Core for LTE."
ln mcom:epc mobile.core sys:is_a
set.add name="ontology.mobile_communications" id="mcom:epc"

def "mcom:handover" "Cell-to-cell mobility procedure."
ln mcom:handover mobile.operations sys:is_a
ln mcom:handover mcom:rsrp @related_to
set.add name="ontology.mobile_communications" id="mcom:handover"

def "mcom:lte_m" "LTE-M IoT communication."
ln mcom:lte_m mobile.services sys:is_a
set.add name="ontology.mobile_communications" id="mcom:lte_m"

def "mcom:lte_ran" "LTE radio access network."
ln mcom:lte_ran mobile.radio sys:is_a
set.add name="ontology.mobile_communications" id="mcom:lte_ran"

def "mcom:massive_mimo" "Large-scale MIMO for 5G."
ln mcom:massive_mimo mobile.radio sys:is_a
set.add name="ontology.mobile_communications" id="mcom:massive_mimo"

def "mcom:mimo" "Multiple-input multiple-output antenna technology."
ln mcom:mimo mobile.radio sys:is_a
set.add name="ontology.mobile_communications" id="mcom:mimo"

def "mcom:mmtc" "Massive Machine-Type Communication."
ln mcom:mmtc mobile.services sys:is_a
set.add name="ontology.mobile_communications" id="mcom:mmtc"

def "mcom:mmwave" "Millimeter wave spectrum."
ln mcom:mmwave mobile.spectrum sys:is_a
set.add name="ontology.mobile_communications" id="mcom:mmwave"

def "mcom:nas" "Non-Access Stratum signaling."
ln mcom:nas mobile.protocol sys:is_a
set.add name="ontology.mobile_communications" id="mcom:nas"

def "mcom:nb_iot" "Narrowband IoT."
ln mcom:nb_iot mobile.services sys:is_a
set.add name="ontology.mobile_communications" id="mcom:nb_iot"

def "mcom:nsa" "Non-Standalone 5G architecture."
ln mcom:nsa mobile.architecture sys:is_a
set.add name="ontology.mobile_communications" id="mcom:nsa"

def "mcom:oran" "Open RAN architecture."
ln mcom:oran mobile.architecture sys:is_a
set.add name="ontology.mobile_communications" id="mcom:oran"

def "mcom:pdcp" "Packet Data Convergence Protocol."
ln mcom:pdcp mobile.protocol sys:is_a
set.add name="ontology.mobile_communications" id="mcom:pdcp"

def "mcom:rlc" "Radio Link Control."
ln mcom:rlc mobile.protocol sys:is_a
set.add name="ontology.mobile_communications" id="mcom:rlc"

def "mcom:rrc" "Radio Resource Control protocol."
ln mcom:rrc mobile.protocol sys:is_a
set.add name="ontology.mobile_communications" id="mcom:rrc"

def "mcom:rsrp" "Reference Signal Received Power."
ln mcom:rsrp mobile.operations sys:is_a
set.add name="ontology.mobile_communications" id="mcom:rsrp"

def "mcom:sa" "Standalone 5G architecture."
ln mcom:sa mobile.architecture sys:is_a
set.add name="ontology.mobile_communications" id="mcom:sa"

def "mcom:sinr" "Signal-to-Interference-plus-Noise Ratio."
ln mcom:sinr mobile.operations sys:is_a
set.add name="ontology.mobile_communications" id="mcom:sinr"

def "mcom:slicing" "Network slicing for dedicated virtual networks."
ln mcom:slicing mobile.architecture sys:is_a
ln mcom:slicing mcom:urllc @enables
set.add name="ontology.mobile_communications" id="mcom:slicing"

def "mcom:smf" "Session Management Function."
ln mcom:smf mobile.core sys:is_a
set.add name="ontology.mobile_communications" id="mcom:smf"

def "mcom:son" "Self-Organizing Network."
ln mcom:son mobile.operations sys:is_a
set.add name="ontology.mobile_communications" id="mcom:son"

def "mcom:sub6" "Sub-6 GHz spectrum for 5G."
ln mcom:sub6 mobile.spectrum sys:is_a
set.add name="ontology.mobile_communications" id="mcom:sub6"

def "mcom:upf" "User Plane Function."
ln mcom:upf mobile.core sys:is_a
set.add name="ontology.mobile_communications" id="mcom:upf"

def "mcom:urllc" "Ultra-Reliable Low-Latency Communication."
ln mcom:urllc mobile.services sys:is_a
set.add name="ontology.mobile_communications" id="mcom:urllc"

def "mcom:volte" "Voice over LTE."
ln mcom:volte mobile.protocol sys:is_a
ln mcom:volte mcom:epc @depends_on
set.add name="ontology.mobile_communications" id="mcom:volte"

def "mcom:vonr" "Voice over 5G NR."
ln mcom:vonr mobile.protocol sys:is_a
ln mcom:vonr mcom:5gc @depends_on
set.add name="ontology.mobile_communications" id="mcom:vonr"
