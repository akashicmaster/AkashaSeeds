# Akasha ontology — namespace: rtos
# atoms: 29

def "rtos.architecture" "Architectural models of RTOS including microkernel and event-driven designs."
ln rtos.architecture ont.rtos_embedded_os sys:part_of
set.add name="ontology.rtos_embedded_os" id="rtos.architecture"

def "rtos.automotive" "Automotive operating systems including AUTOSAR and automotive Linux."
ln rtos.automotive ont.rtos_embedded_os sys:part_of
set.add name="ontology.rtos_embedded_os" id="rtos.automotive"

def "rtos.core" "Real-time operating systems for embedded and industrial systems."
ln rtos.core ont.rtos_embedded_os sys:part_of
set.add name="ontology.rtos_embedded_os" id="rtos.core"

def "rtos.embedded_linux" "Embedded Linux distributions and build systems."
ln rtos.embedded_linux ont.rtos_embedded_os sys:part_of
set.add name="ontology.rtos_embedded_os" id="rtos.embedded_linux"

def "rtos.iot" "IoT-focused operating systems for constrained devices."
ln rtos.iot ont.rtos_embedded_os sys:part_of
set.add name="ontology.rtos_embedded_os" id="rtos.iot"

def "rtos.network_os" "Network device operating systems including router and switch OS."
ln rtos.network_os ont.rtos_embedded_os sys:part_of
set.add name="ontology.rtos_embedded_os" id="rtos.network_os"

def "rtos.safety" "Safety standards and certifications for embedded systems."
ln rtos.safety ont.rtos_embedded_os sys:part_of
set.add name="ontology.rtos_embedded_os" id="rtos.safety"

def "rtos:agl" "Automotive Grade Linux for vehicle infotainment."
ln rtos:agl rtos.embedded_linux sys:is_a
ln rtos:agl rtos:autosar_adaptive @coexists_with
set.add name="ontology.rtos_embedded_os" id="rtos:agl"

def "rtos:autosar" "AUTOSAR Classic Platform for safety-critical automotive ECUs."
ln rtos:autosar rtos.automotive sys:is_a
ln rtos:autosar rtos:iso26262 @requires
set.add name="ontology.rtos_embedded_os" id="rtos:autosar"

def "rtos:autosar_adaptive" "AUTOSAR Adaptive Platform for high-performance automotive computing."
ln rtos:autosar_adaptive rtos.automotive sys:is_a
set.add name="ontology.rtos_embedded_os" id="rtos:autosar_adaptive"

def "rtos:buildroot" "Buildroot embedded Linux build system."
ln rtos:buildroot rtos.embedded_linux sys:is_a
set.add name="ontology.rtos_embedded_os" id="rtos:buildroot"

def "rtos:cisco_ios" "Cisco IOS network operating system."
ln rtos:cisco_ios rtos.network_os sys:is_a
set.add name="ontology.rtos_embedded_os" id="rtos:cisco_ios"

def "rtos:contiki" "Contiki OS for low-power IoT networks."
ln rtos:contiki rtos.iot sys:is_a
set.add name="ontology.rtos_embedded_os" id="rtos:contiki"

def "rtos:do178c" "DO-178C safety standard for avionics software."
ln rtos:do178c rtos.safety sys:is_a
set.add name="ontology.rtos_embedded_os" id="rtos:do178c"

def "rtos:event_driven" "Event-driven RTOS architecture for deterministic scheduling."
ln rtos:event_driven rtos.architecture sys:is_a
set.add name="ontology.rtos_embedded_os" id="rtos:event_driven"

def "rtos:freertos" "FreeRTOS lightweight RTOS for microcontrollers."
ln rtos:freertos rtos.core sys:is_a
ln rtos:freertos rtos:mbed_os @used_with
set.add name="ontology.rtos_embedded_os" id="rtos:freertos"

def "rtos:iec61508" "IEC 61508 functional safety standard for industrial systems."
ln rtos:iec61508 rtos.safety sys:is_a
set.add name="ontology.rtos_embedded_os" id="rtos:iec61508"

def "rtos:iso26262" "ISO 26262 functional safety standard for automotive systems."
ln rtos:iso26262 rtos.safety sys:is_a
set.add name="ontology.rtos_embedded_os" id="rtos:iso26262"

def "rtos:junos" "Juniper Junos OS."
ln rtos:junos rtos.network_os sys:is_a
set.add name="ontology.rtos_embedded_os" id="rtos:junos"

def "rtos:mbed_os" "ARM Mbed OS for IoT devices."
ln rtos:mbed_os rtos.iot sys:is_a
set.add name="ontology.rtos_embedded_os" id="rtos:mbed_os"

def "rtos:microkernel" "Microkernel architecture used in QNX and similar RTOS."
ln rtos:microkernel rtos.architecture sys:is_a
ln rtos:microkernel rtos:qnx @implements
set.add name="ontology.rtos_embedded_os" id="rtos:microkernel"

def "rtos:monolithic_kernel" "Monolithic kernel architecture used in Linux-based embedded systems."
ln rtos:monolithic_kernel rtos.architecture sys:is_a
ln rtos:monolithic_kernel rtos:yocto @used_by
set.add name="ontology.rtos_embedded_os" id="rtos:monolithic_kernel"

def "rtos:nx_os" "Cisco NX-OS for data center switches."
ln rtos:nx_os rtos.network_os sys:is_a
set.add name="ontology.rtos_embedded_os" id="rtos:nx_os"

def "rtos:qnx" "QNX microkernel RTOS widely used in automotive and industrial systems."
ln rtos:qnx rtos.core sys:is_a
set.add name="ontology.rtos_embedded_os" id="rtos:qnx"

def "rtos:qnx_automotive" "QNX-based automotive OS."
ln rtos:qnx_automotive rtos.automotive sys:is_a
set.add name="ontology.rtos_embedded_os" id="rtos:qnx_automotive"

def "rtos:riot_os" "RIOT OS for constrained IoT devices."
ln rtos:riot_os rtos.iot sys:is_a
set.add name="ontology.rtos_embedded_os" id="rtos:riot_os"

def "rtos:vxworks" "VxWorks commercial RTOS for aerospace and industrial control."
ln rtos:vxworks rtos.core sys:is_a
set.add name="ontology.rtos_embedded_os" id="rtos:vxworks"

def "rtos:yocto" "Yocto Project for building custom embedded Linux distributions."
ln rtos:yocto rtos.embedded_linux sys:is_a
set.add name="ontology.rtos_embedded_os" id="rtos:yocto"

def "rtos:zephyr" "Zephyr RTOS for IoT and embedded systems."
ln rtos:zephyr rtos.core sys:is_a
set.add name="ontology.rtos_embedded_os" id="rtos:zephyr"
