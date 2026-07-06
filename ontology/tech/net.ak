# Akasha ontology — namespace: net
# atoms: 27

def "net:bgp" "Border Gateway Protocol — routing between autonomous systems."
ln net:bgp networking.routing sys:is_a
ln net:bgp net:mpls @related_to
set.add name="ontology.networking" id="net:bgp"

def "net:cellular" "Mobile communication networks including 4G, 5G, and beyond."
ln net:cellular networking.wireless sys:is_a
set.add name="ontology.networking" id="net:cellular"

def "net:copper_ethernet" "Ethernet communication over copper cables."
ln net:copper_ethernet networking.physical sys:is_a
set.add name="ontology.networking" id="net:copper_ethernet"

def "net:encryption" "Techniques for securing data through cryptography."
ln net:encryption networking.security sys:is_a
set.add name="ontology.networking" id="net:encryption"

def "net:fiber_optics" "Transmission using light through optical fibers."
ln net:fiber_optics networking.physical sys:is_a
set.add name="ontology.networking" id="net:fiber_optics"

def "net:firewall" "Device or software controlling network traffic based on rules."
ln net:firewall networking.security sys:is_a
set.add name="ontology.networking" id="net:firewall"

def "net:ids_ips" "Intrusion detection and prevention systems."
ln net:ids_ips networking.security sys:is_a
set.add name="ontology.networking" id="net:ids_ips"

def "net:iot_network" "Low-power wireless networks for IoT devices."
ln net:iot_network networking.wireless sys:is_a
set.add name="ontology.networking" id="net:iot_network"

def "net:ip_addressing" "Assignment of IP addresses to devices."
ln net:ip_addressing networking.fundamentals sys:is_a
set.add name="ontology.networking" id="net:ip_addressing"

def "net:modulation" "Encoding information onto carrier signals."
ln net:modulation networking.physical sys:is_a
set.add name="ontology.networking" id="net:modulation"

def "net:mpls" "Multiprotocol Label Switching — label-based forwarding."
ln net:mpls networking.routing sys:is_a
set.add name="ontology.networking" id="net:mpls"

def "net:netflow" "Flow-level traffic analysis for monitoring and capacity planning."
ln net:netflow networking.operations sys:is_a
set.add name="ontology.networking" id="net:netflow"

def "net:osi_model" "Seven-layer model describing network communication."
ln net:osi_model networking.fundamentals sys:is_a
ln net:osi_model net:tcp_ip @supports
set.add name="ontology.networking" id="net:osi_model"

def "net:ospf" "Open Shortest Path First — link-state routing protocol."
ln net:ospf networking.routing sys:is_a
set.add name="ontology.networking" id="net:ospf"

def "net:overlay_network" "Virtual networks built on top of physical networks."
ln net:overlay_network networking.cloud sys:is_a
set.add name="ontology.networking" id="net:overlay_network"

def "net:qos" "Quality of Service — prioritizing network traffic."
ln net:qos networking.operations sys:is_a
ln net:qos word:en:latency @influences
set.add name="ontology.networking" id="net:qos"

def "net:satellite" "Communication via satellites in orbit."
ln net:satellite networking.wireless sys:is_a
set.add name="ontology.networking" id="net:satellite"

def "net:sd_wan" "Software-defined WAN for dynamic routing across WAN links."
ln net:sd_wan networking.routing sys:is_a
set.add name="ontology.networking" id="net:sd_wan"

def "net:sdn" "Software-defined networking separating control and data planes."
ln net:sdn networking.cloud sys:is_a
ln net:sdn net:overlay_network @enables
set.add name="ontology.networking" id="net:sdn"

def "net:service_mesh" "Infrastructure layer for service-to-service communication."
ln net:service_mesh networking.cloud sys:is_a
set.add name="ontology.networking" id="net:service_mesh"

def "net:snmp" "Simple Network Management Protocol for monitoring devices."
ln net:snmp networking.operations sys:is_a
ln net:snmp net:troubleshooting @supports
set.add name="ontology.networking" id="net:snmp"

def "net:switching" "Forwarding frames within a local network."
ln net:switching networking.fundamentals sys:is_a
set.add name="ontology.networking" id="net:switching"

def "net:tcp_ip" "Core protocol suite of the internet."
ln net:tcp_ip networking.fundamentals sys:is_a
set.add name="ontology.networking" id="net:tcp_ip"

def "net:troubleshooting" "Diagnosing and resolving network issues."
ln net:troubleshooting networking.operations sys:is_a
set.add name="ontology.networking" id="net:troubleshooting"

def "net:vpc" "Virtual Private Cloud — isolated virtual network in cloud environments."
ln net:vpc networking.cloud sys:is_a
set.add name="ontology.networking" id="net:vpc"

def "net:vpn" "Encrypted tunnel for secure remote communication."
ln net:vpn networking.security sys:is_a
ln net:vpn net:encryption @depends_on
set.add name="ontology.networking" id="net:vpn"

def "net:wifi" "Wireless LAN communication based on IEEE 802.11."
ln net:wifi networking.wireless sys:is_a
ln net:wifi net:iot_network @supports
set.add name="ontology.networking" id="net:wifi"
