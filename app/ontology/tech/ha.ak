# Akasha ontology — namespace: ha
# atoms: 34

def "ha.assistive" "Assistive technologies and comfort systems."
set.add name="ontology.home_automation" id="ha.assistive"

def "ha.automation" "Automation logic, routines, and AI control."
set.add name="ontology.home_automation" id="ha.automation"

def "ha.communication" "IoT protocols and device communication."
set.add name="ontology.home_automation" id="ha.communication"

def "ha.devices" "Sensors and actuators in smart homes."
set.add name="ontology.home_automation" id="ha.devices"

def "ha.energy" "Home energy management and integration."
set.add name="ontology.home_automation" id="ha.energy"

def "ha.hvac" "Heating, ventilation, and air conditioning automation."
set.add name="ontology.home_automation" id="ha.hvac"

def "ha.lighting" "Lighting control and automation."
set.add name="ontology.home_automation" id="ha.lighting"

def "ha.security" "Home security and access control."
set.add name="ontology.home_automation" id="ha.security"

def "ha:ai_automation" "AI-driven automation and prediction."
ln ha:ai_automation ha.automation sys:is_a
ln ha:ai_automation ha:lighting_schedule @optimizes
set.add name="ontology.home_automation" id="ha:ai_automation"

def "ha:air_quality" "Air quality monitoring and control."
ln ha:air_quality ha.hvac sys:is_a
ln ha:air_quality ha:health_monitoring @supports
set.add name="ontology.home_automation" id="ha:air_quality"

def "ha:alarm_system" "Alarm and intrusion detection."
ln ha:alarm_system ha.security sys:is_a
set.add name="ontology.home_automation" id="ha:alarm_system"

def "ha:color_lighting" "Color-changing smart lighting."
ln ha:color_lighting ha.lighting sys:is_a
set.add name="ontology.home_automation" id="ha:color_lighting"

def "ha:contact_sensor" "Door/window contact sensors."
ln ha:contact_sensor ha.devices sys:is_a
set.add name="ontology.home_automation" id="ha:contact_sensor"

def "ha:dimming" "Dimming and brightness control."
ln ha:dimming ha.lighting sys:is_a
set.add name="ontology.home_automation" id="ha:dimming"

def "ha:elderly_support" "Elderly support and monitoring."
ln ha:elderly_support ha.assistive sys:is_a
set.add name="ontology.home_automation" id="ha:elderly_support"

def "ha:health_monitoring" "Health and wellness monitoring."
ln ha:health_monitoring ha.assistive sys:is_a
set.add name="ontology.home_automation" id="ha:health_monitoring"

def "ha:home_ems" "Home energy management systems."
ln ha:home_ems ha.energy sys:is_a
set.add name="ontology.home_automation" id="ha:home_ems"

def "ha:lighting_schedule" "Lighting schedules and routines."
ln ha:lighting_schedule ha.lighting sys:is_a
set.add name="ontology.home_automation" id="ha:lighting_schedule"

def "ha:matter" "Matter interoperability standard."
ln ha:matter ha.communication sys:is_a
set.add name="ontology.home_automation" id="ha:matter"

def "ha:motion_sensor" "Motion and occupancy sensors."
ln ha:motion_sensor ha.devices sys:is_a
set.add name="ontology.home_automation" id="ha:motion_sensor"

def "ha:rule_engine" "Rule-based automation engine."
ln ha:rule_engine ha.automation sys:is_a
set.add name="ontology.home_automation" id="ha:rule_engine"

def "ha:scene_control" "Scene-based multi-device control."
ln ha:scene_control ha.automation sys:is_a
set.add name="ontology.home_automation" id="ha:scene_control"

def "ha:security_camera" "Security cameras."
ln ha:security_camera ha.security sys:is_a
set.add name="ontology.home_automation" id="ha:security_camera"

def "ha:smart_lock" "Smart locks and access control."
ln ha:smart_lock ha.security sys:is_a
ln ha:smart_lock ha:security_camera @integrates_with
set.add name="ontology.home_automation" id="ha:smart_lock"

def "ha:smart_switch" "Smart switches and relays."
ln ha:smart_switch ha.devices sys:is_a
set.add name="ontology.home_automation" id="ha:smart_switch"

def "ha:smart_thermostat" "Smart thermostats."
ln ha:smart_thermostat ha.hvac sys:is_a
set.add name="ontology.home_automation" id="ha:smart_thermostat"

def "ha:solar_integration" "Solar PV integration for homes."
ln ha:solar_integration ha.energy sys:is_a
ln ha:solar_integration ha:home_ems @feeds
set.add name="ontology.home_automation" id="ha:solar_integration"

def "ha:temperature_sensor" "Temperature sensors."
ln ha:temperature_sensor ha.devices sys:is_a
ln ha:temperature_sensor ha:smart_thermostat @informs
set.add name="ontology.home_automation" id="ha:temperature_sensor"

def "ha:v2h" "Vehicle-to-home energy integration."
ln ha:v2h ha.energy sys:is_a
set.add name="ontology.home_automation" id="ha:v2h"

def "ha:ventilation_control" "Automated ventilation systems."
ln ha:ventilation_control ha.hvac sys:is_a
set.add name="ontology.home_automation" id="ha:ventilation_control"

def "ha:voice_assistant" "Voice assistants for home control."
ln ha:voice_assistant ha.assistive sys:is_a
set.add name="ontology.home_automation" id="ha:voice_assistant"

def "ha:wifi" "Wi-Fi based smart devices."
ln ha:wifi ha.communication sys:is_a
set.add name="ontology.home_automation" id="ha:wifi"

def "ha:zigbee" "Zigbee protocol."
ln ha:zigbee ha.communication sys:is_a
set.add name="ontology.home_automation" id="ha:zigbee"

def "ha:zwave" "Z-Wave protocol."
ln ha:zwave ha.communication sys:is_a
set.add name="ontology.home_automation" id="ha:zwave"
