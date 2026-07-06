# Akasha ontology — namespace: iot
# atoms: 42

def "iot.discovery" "Device discovery, pairing, and service discovery."
set.add name="ontology.iot_protocols" id="iot.discovery"

def "iot.domain_stacks" "Domain-specific IoT stacks (home, industrial, LPWAN)."
set.add name="ontology.iot_protocols" id="iot.domain_stacks"

def "iot.link_layer" "Link-layer and MAC protocols for IoT."
set.add name="ontology.iot_protocols" id="iot.link_layer"

def "iot.messaging" "Application messaging and data exchange protocols."
set.add name="ontology.iot_protocols" id="iot.messaging"

def "iot.network_layer" "Network-layer protocols and routing for IoT."
set.add name="ontology.iot_protocols" id="iot.network_layer"

def "iot.security" "Security, encryption, and authentication for IoT."
set.add name="ontology.iot_protocols" id="iot.security"

def "iot.transport_layer" "Transport and session protocols for IoT."
set.add name="ontology.iot_protocols" id="iot.transport_layer"

def "iot:6lowpan" "6LoWPAN adaptation of IPv6 over low-power networks."
ln iot:6lowpan iot.network_layer sys:is_a
ln iot:6lowpan iot:zigbee @runs_over
set.add name="ontology.iot_protocols" id="iot:6lowpan"

def "iot:amqp" "AMQP messaging for IoT backends."
ln iot:amqp iot.messaging sys:is_a
set.add name="ontology.iot_protocols" id="iot:amqp"

def "iot:ble" "Bluetooth Low Energy."
ln iot:ble iot.link_layer sys:is_a
set.add name="ontology.iot_protocols" id="iot:ble"

def "iot:cert_based_auth" "Certificate-based authentication."
ln iot:cert_based_auth iot.security sys:is_a
set.add name="ontology.iot_protocols" id="iot:cert_based_auth"

def "iot:coap" "CoAP (Constrained Application Protocol) over UDP."
ln iot:coap iot.transport_layer sys:is_a
ln iot:coap iot:udp @runs_over
set.add name="ontology.iot_protocols" id="iot:coap"

def "iot:dtls" "DTLS for secure datagram transport."
ln iot:dtls iot.transport_layer sys:is_a
ln iot:dtls iot:coap @secures
set.add name="ontology.iot_protocols" id="iot:dtls"

def "iot:home_stack" "Home automation IoT stacks."
ln iot:home_stack iot.domain_stacks sys:is_a
set.add name="ontology.iot_protocols" id="iot:home_stack"

def "iot:http_rest" "HTTP/REST APIs for IoT devices."
ln iot:http_rest iot.messaging sys:is_a
set.add name="ontology.iot_protocols" id="iot:http_rest"

def "iot:industrial_stack" "Industrial IoT (IIoT) stacks."
ln iot:industrial_stack iot.domain_stacks sys:is_a
set.add name="ontology.iot_protocols" id="iot:industrial_stack"

def "iot:ipv6" "IPv6 addressing for IoT devices."
ln iot:ipv6 iot.network_layer sys:is_a
set.add name="ontology.iot_protocols" id="iot:ipv6"

def "iot:lora" "LoRa physical layer for LPWAN."
ln iot:lora iot.link_layer sys:is_a
set.add name="ontology.iot_protocols" id="iot:lora"

def "iot:lorawan" "LoRaWAN network protocol for LPWAN."
ln iot:lorawan iot.network_layer sys:is_a
ln iot:lorawan iot:lora @runs_over
set.add name="ontology.iot_protocols" id="iot:lorawan"

def "iot:lpwan_stack" "LPWAN-based IoT stacks."
ln iot:lpwan_stack iot.domain_stacks sys:is_a
set.add name="ontology.iot_protocols" id="iot:lpwan_stack"

def "iot:lte_m" "LTE-M cellular IoT."
ln iot:lte_m iot:lpwan_stack sys:is_a
set.add name="ontology.iot_protocols" id="iot:lte_m"

def "iot:matter" "Matter interoperability standard for smart home."
ln iot:matter iot:home_stack sys:is_a
ln iot:matter iot:home_stack @unifies
set.add name="ontology.iot_protocols" id="iot:matter"

def "iot:mdns" "mDNS for local service discovery."
ln iot:mdns iot.discovery sys:is_a
set.add name="ontology.iot_protocols" id="iot:mdns"

def "iot:modbus_tcp" "Modbus/TCP for industrial devices."
ln iot:modbus_tcp iot:industrial_stack sys:is_a
set.add name="ontology.iot_protocols" id="iot:modbus_tcp"

def "iot:mqtt" "MQTT publish/subscribe messaging protocol."
ln iot:mqtt iot.messaging sys:is_a
ln iot:mqtt iot:tcp @runs_over
set.add name="ontology.iot_protocols" id="iot:mqtt"

def "iot:mqtt_sn" "MQTT-SN for sensor networks."
ln iot:mqtt_sn iot.messaging sys:is_a
set.add name="ontology.iot_protocols" id="iot:mqtt_sn"

def "iot:nb_iot" "NB-IoT cellular IoT."
ln iot:nb_iot iot:lpwan_stack sys:is_a
set.add name="ontology.iot_protocols" id="iot:nb_iot"

def "iot:opc_ua" "OPC UA for industrial communication."
ln iot:opc_ua iot:industrial_stack sys:is_a
ln iot:opc_ua iot:industrial_stack @core_protocol
set.add name="ontology.iot_protocols" id="iot:opc_ua"

def "iot:pairing" "Device pairing and onboarding procedures."
ln iot:pairing iot.discovery sys:is_a
set.add name="ontology.iot_protocols" id="iot:pairing"

def "iot:profinet" "PROFINET industrial Ethernet."
ln iot:profinet iot:industrial_stack sys:is_a
set.add name="ontology.iot_protocols" id="iot:profinet"

def "iot:psk" "Pre-shared key authentication."
ln iot:psk iot.security sys:is_a
set.add name="ontology.iot_protocols" id="iot:psk"

def "iot:rpl" "RPL routing protocol for low-power and lossy networks."
ln iot:rpl iot.network_layer sys:is_a
ln iot:rpl iot:thread @used_by
set.add name="ontology.iot_protocols" id="iot:rpl"

def "iot:secure_boot" "Secure boot and firmware integrity."
ln iot:secure_boot iot.security sys:is_a
set.add name="ontology.iot_protocols" id="iot:secure_boot"

def "iot:sigfox" "Sigfox LPWAN network."
ln iot:sigfox iot:lpwan_stack sys:is_a
set.add name="ontology.iot_protocols" id="iot:sigfox"

def "iot:ssdp" "SSDP/UPnP discovery."
ln iot:ssdp iot.discovery sys:is_a
set.add name="ontology.iot_protocols" id="iot:ssdp"

def "iot:tcp" "TCP transport for reliable IoT communication."
ln iot:tcp iot.transport_layer sys:is_a
set.add name="ontology.iot_protocols" id="iot:tcp"

def "iot:thread" "Thread mesh networking for home IoT."
ln iot:thread iot:home_stack sys:is_a
set.add name="ontology.iot_protocols" id="iot:thread"

def "iot:tls" "TLS for secure IoT communication."
ln iot:tls iot.security sys:is_a
ln iot:tls iot:mqtt @secures
set.add name="ontology.iot_protocols" id="iot:tls"

def "iot:udp" "UDP transport for lightweight IoT communication."
ln iot:udp iot.transport_layer sys:is_a
set.add name="ontology.iot_protocols" id="iot:udp"

def "iot:wifi" "Wi-Fi for high-throughput IoT devices."
ln iot:wifi iot.link_layer sys:is_a
set.add name="ontology.iot_protocols" id="iot:wifi"

def "iot:zigbee" "Zigbee low-power mesh networking."
ln iot:zigbee iot.link_layer sys:is_a
set.add name="ontology.iot_protocols" id="iot:zigbee"

def "iot:zwave" "Z-Wave low-power home automation network."
ln iot:zwave iot.link_layer sys:is_a
set.add name="ontology.iot_protocols" id="iot:zwave"
