# Akasha ontology — namespace: iotc
# atoms: 25

def "iotc.architecture" "IoT network architecture including gateways, edge computing, and mesh networks."
ln iotc.architecture ont.iot_connectivity sys:part_of
set.add name="ontology.iot_connectivity" id="iotc.architecture"

def "iotc.lpwan" "Low-power wide-area networks including LoRaWAN, Sigfox, NB-IoT, and LTE-M."
ln iotc.lpwan ont.iot_connectivity sys:part_of
set.add name="ontology.iot_connectivity" id="iotc.lpwan"

def "iotc.operations" "IoT operations including device management, OTA updates, and telemetry."
ln iotc.operations ont.iot_connectivity sys:part_of
set.add name="ontology.iot_connectivity" id="iotc.operations"

def "iotc.protocol" "IoT communication protocols including MQTT, CoAP, and LwM2M."
ln iotc.protocol ont.iot_connectivity sys:part_of
set.add name="ontology.iot_connectivity" id="iotc.protocol"

def "iotc.security" "IoT security including device identity, encryption, and secure boot."
ln iotc.security ont.iot_connectivity sys:part_of
set.add name="ontology.iot_connectivity" id="iotc.security"

def "iotc.short_range" "Short-range IoT connectivity including BLE, Zigbee, Z-Wave, and UWB."
ln iotc.short_range ont.iot_connectivity sys:part_of
set.add name="ontology.iot_connectivity" id="iotc.short_range"

def "iotc:coap" "REST-like protocol for constrained devices."
ln iotc:coap iotc.protocol sys:is_a
set.add name="ontology.iot_connectivity" id="iotc:coap"

def "iotc:device_identity" "Unique identity for IoT devices."
ln iotc:device_identity iotc.security sys:is_a
set.add name="ontology.iot_connectivity" id="iotc:device_identity"

def "iotc:device_management" "Lifecycle management of IoT devices."
ln iotc:device_management iotc.operations sys:is_a
set.add name="ontology.iot_connectivity" id="iotc:device_management"

def "iotc:dtls" "Datagram TLS for secure IoT communication."
ln iotc:dtls iotc.security sys:is_a
set.add name="ontology.iot_connectivity" id="iotc:dtls"

def "iotc:edge" "Edge computing for IoT data processing."
ln iotc:edge iotc.architecture sys:is_a
set.add name="ontology.iot_connectivity" id="iotc:edge"

def "iotc:gateway" "Device bridging IoT devices and cloud services."
ln iotc:gateway iotc.architecture sys:is_a
set.add name="ontology.iot_connectivity" id="iotc:gateway"

def "iotc:lorawan" "LoRaWAN — long-range, low-power IoT network."
ln iotc:lorawan iotc.lpwan sys:is_a
ln iotc:lorawan iotc:gateway @requires
set.add name="ontology.iot_connectivity" id="iotc:lorawan"

def "iotc:lte_m" "LTE-M — cellular IoT technology with mobility support."
ln iotc:lte_m iotc.lpwan sys:is_a
set.add name="ontology.iot_connectivity" id="iotc:lte_m"

def "iotc:lwm2m" "Device management protocol for IoT."
ln iotc:lwm2m iotc.protocol sys:is_a
set.add name="ontology.iot_connectivity" id="iotc:lwm2m"

def "iotc:mesh" "Mesh networking for distributed IoT communication."
ln iotc:mesh iotc.architecture sys:is_a
set.add name="ontology.iot_connectivity" id="iotc:mesh"

def "iotc:mqtt" "Lightweight publish/subscribe protocol for IoT."
ln iotc:mqtt iotc.protocol sys:is_a
ln iotc:mqtt iotc:gateway @supports
set.add name="ontology.iot_connectivity" id="iotc:mqtt"

def "iotc:nb_iot" "Narrowband IoT — cellular LPWAN technology."
ln iotc:nb_iot iotc.lpwan sys:is_a
set.add name="ontology.iot_connectivity" id="iotc:nb_iot"

def "iotc:ota_update" "Over-the-air firmware updates."
ln iotc:ota_update iotc.operations sys:is_a
ln iotc:ota_update iotc:lwm2m @uses
set.add name="ontology.iot_connectivity" id="iotc:ota_update"

def "iotc:secure_boot" "Ensures trusted firmware at startup."
ln iotc:secure_boot iotc.security sys:is_a
ln iotc:secure_boot iotc:device_identity @protects
set.add name="ontology.iot_connectivity" id="iotc:secure_boot"

def "iotc:sigfox" "Ultra-narrowband IoT communication network."
ln iotc:sigfox iotc.lpwan sys:is_a
set.add name="ontology.iot_connectivity" id="iotc:sigfox"

def "iotc:telemetry" "Device telemetry and metrics reporting."
ln iotc:telemetry iotc.operations sys:is_a
set.add name="ontology.iot_connectivity" id="iotc:telemetry"

def "iotc:uwb" "Ultra-wideband for precise location and short-range communication."
ln iotc:uwb iotc.short_range sys:is_a
set.add name="ontology.iot_connectivity" id="iotc:uwb"

def "iotc:zigbee" "Low-power mesh networking protocol for IoT."
ln iotc:zigbee iotc.short_range sys:is_a
ln iotc:zigbee iotc:mesh @supports
set.add name="ontology.iot_connectivity" id="iotc:zigbee"

def "iotc:zwave" "Short-range IoT protocol for smart home devices."
ln iotc:zwave iotc.short_range sys:is_a
set.add name="ontology.iot_connectivity" id="iotc:zwave"
