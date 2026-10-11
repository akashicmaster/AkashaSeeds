# Akasha ontology — namespace: spaceproto
# atoms: 32

def "spaceproto.ccsds" "CCSDS protocol family for space agencies."
ln spaceproto.ccsds ont.space_comm_protocols sys:part_of
set.add name="ontology.space_comm_protocols" id="spaceproto.ccsds"

def "spaceproto.dtn" "Delay/Disruption Tolerant Networking and bundle protocols."
ln spaceproto.dtn ont.space_comm_protocols sys:part_of
set.add name="ontology.space_comm_protocols" id="spaceproto.dtn"

def "spaceproto.file_transfer" "File transfer protocols for space links."
ln spaceproto.file_transfer ont.space_comm_protocols sys:part_of
set.add name="ontology.space_comm_protocols" id="spaceproto.file_transfer"

def "spaceproto.link_layer" "Space link layer protocols for telemetry and telecommand."
ln spaceproto.link_layer ont.space_comm_protocols sys:part_of
set.add name="ontology.space_comm_protocols" id="spaceproto.link_layer"

def "spaceproto.management" "Network and mission management protocols for space systems."
ln spaceproto.management ont.space_comm_protocols sys:part_of
set.add name="ontology.space_comm_protocols" id="spaceproto.management"

def "spaceproto.time_sync" "Time synchronization and time distribution in space networks."
ln spaceproto.time_sync ont.space_comm_protocols sys:part_of
set.add name="ontology.space_comm_protocols" id="spaceproto.time_sync"

def "spaceproto.tm_tc" "Telemetry and telecommand protocols."
ln spaceproto.tm_tc ont.space_comm_protocols sys:part_of
set.add name="ontology.space_comm_protocols" id="spaceproto.tm_tc"

def "spaceproto:bp_convergence_layer" "Convergence layer adapters for underlying transports."
ln spaceproto:bp_convergence_layer spaceproto.dtn sys:is_a
set.add name="ontology.space_comm_protocols" id="spaceproto:bp_convergence_layer"

def "spaceproto:bp_security" "Bundle Protocol Security (BPSec)."
ln spaceproto:bp_security spaceproto.dtn sys:is_a
ln spaceproto:bp_security spaceproto:bundle_protocol_v7 @secures
set.add name="ontology.space_comm_protocols" id="spaceproto:bp_security"

def "spaceproto:bundle_protocol" "Bundle Protocol for DTN store-and-forward networking."
ln spaceproto:bundle_protocol spaceproto.dtn sys:is_a
ln spaceproto:bundle_protocol word:en:interplanetary_internet @enables
set.add name="ontology.space_comm_protocols" id="spaceproto:bundle_protocol"

def "spaceproto:bundle_protocol_v7" "Bundle Protocol Version 7."
ln spaceproto:bundle_protocol_v7 spaceproto.dtn sys:is_a
set.add name="ontology.space_comm_protocols" id="spaceproto:bundle_protocol_v7"

def "spaceproto:ccsds_aos" "Advanced Orbiting Systems space link protocol."
ln spaceproto:ccsds_aos spaceproto.ccsds sys:is_a
ln spaceproto:ccsds_aos spaceproto:space_link_aos @implements
set.add name="ontology.space_comm_protocols" id="spaceproto:ccsds_aos"

def "spaceproto:ccsds_cfds" "CCSDS File Delivery Protocol (CFDP)."
ln spaceproto:ccsds_cfds spaceproto.ccsds sys:is_a
set.add name="ontology.space_comm_protocols" id="spaceproto:ccsds_cfds"

def "spaceproto:ccsds_space_link" "CCSDS space link protocols for telemetry and telecommand."
ln spaceproto:ccsds_space_link spaceproto.ccsds sys:is_a
set.add name="ontology.space_comm_protocols" id="spaceproto:ccsds_space_link"

def "spaceproto:ccsds_tc" "CCSDS Telecommand Transfer Frame protocol."
ln spaceproto:ccsds_tc spaceproto.ccsds sys:is_a
ln spaceproto:ccsds_tc spaceproto:space_link_tc @implements
set.add name="ontology.space_comm_protocols" id="spaceproto:ccsds_tc"

def "spaceproto:ccsds_tm" "CCSDS Telemetry Transfer Frame protocol."
ln spaceproto:ccsds_tm spaceproto.ccsds sys:is_a
ln spaceproto:ccsds_tm spaceproto:space_link_tm @implements
set.add name="ontology.space_comm_protocols" id="spaceproto:ccsds_tm"

def "spaceproto:cfdp" "CCSDS File Delivery Protocol for reliable file transfer over space links."
ln spaceproto:cfdp spaceproto.file_transfer sys:is_a
ln spaceproto:cfdp spaceproto:bundle_protocol @can_run_over
set.add name="ontology.space_comm_protocols" id="spaceproto:cfdp"

def "spaceproto:cfdp_class1" "CFDP Class 1 — unacknowledged file delivery."
ln spaceproto:cfdp_class1 spaceproto.file_transfer sys:is_a
set.add name="ontology.space_comm_protocols" id="spaceproto:cfdp_class1"

def "spaceproto:cfdp_class2" "CFDP Class 2 — acknowledged file delivery."
ln spaceproto:cfdp_class2 spaceproto.file_transfer sys:is_a
set.add name="ontology.space_comm_protocols" id="spaceproto:cfdp_class2"

def "spaceproto:mission_management" "High-level mission management protocols and procedures."
ln spaceproto:mission_management spaceproto.management sys:is_a
set.add name="ontology.space_comm_protocols" id="spaceproto:mission_management"

def "spaceproto:monitor_control" "Protocols for monitoring and controlling space assets."
ln spaceproto:monitor_control spaceproto.management sys:is_a
ln spaceproto:monitor_control spaceproto:tc_packet @uses
set.add name="ontology.space_comm_protocols" id="spaceproto:monitor_control"

def "spaceproto:space_link_aos" "Space link layer for AOS frames."
ln spaceproto:space_link_aos spaceproto.link_layer sys:is_a
set.add name="ontology.space_comm_protocols" id="spaceproto:space_link_aos"

def "spaceproto:space_link_tc" "Space link layer for telecommand transfer."
ln spaceproto:space_link_tc spaceproto.link_layer sys:is_a
set.add name="ontology.space_comm_protocols" id="spaceproto:space_link_tc"

def "spaceproto:space_link_tm" "Space link layer for telemetry transfer."
ln spaceproto:space_link_tm spaceproto.link_layer sys:is_a
set.add name="ontology.space_comm_protocols" id="spaceproto:space_link_tm"

def "spaceproto:space_mib" "Management information base for space systems."
ln spaceproto:space_mib spaceproto.management sys:is_a
set.add name="ontology.space_comm_protocols" id="spaceproto:space_mib"

def "spaceproto:tc_frame" "Telecommand transfer frame carrying commands."
ln spaceproto:tc_frame spaceproto.tm_tc sys:is_a
set.add name="ontology.space_comm_protocols" id="spaceproto:tc_frame"

def "spaceproto:tc_packet" "Telecommand packet encapsulating control instructions."
ln spaceproto:tc_packet spaceproto.tm_tc sys:is_a
set.add name="ontology.space_comm_protocols" id="spaceproto:tc_packet"

def "spaceproto:time_code" "CCSDS time code formats for spacecraft time representation."
ln spaceproto:time_code spaceproto.time_sync sys:is_a
set.add name="ontology.space_comm_protocols" id="spaceproto:time_code"

def "spaceproto:time_correlation" "Correlation between spacecraft time and ground time."
ln spaceproto:time_correlation spaceproto.time_sync sys:is_a
set.add name="ontology.space_comm_protocols" id="spaceproto:time_correlation"

def "spaceproto:time_distribution" "Distribution of time information across space links."
ln spaceproto:time_distribution spaceproto.time_sync sys:is_a
ln spaceproto:time_distribution spaceproto:tm_frame @carried_by
set.add name="ontology.space_comm_protocols" id="spaceproto:time_distribution"

def "spaceproto:tm_frame" "Telemetry transfer frame carrying spacecraft data."
ln spaceproto:tm_frame spaceproto.tm_tc sys:is_a
set.add name="ontology.space_comm_protocols" id="spaceproto:tm_frame"

def "spaceproto:tm_packet" "Telemetry packet encapsulating measurement data."
ln spaceproto:tm_packet spaceproto.tm_tc sys:is_a
set.add name="ontology.space_comm_protocols" id="spaceproto:tm_packet"
