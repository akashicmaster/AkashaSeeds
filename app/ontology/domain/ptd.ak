# Akasha ontology — namespace: ptd
# atoms: 33

def "ptd.analytics" "Analytics, optimization, and demand forecasting."
set.add name="ontology.public_transport_digitalization" id="ptd.analytics"

def "ptd.fleet_management" "Fleet management and vehicle monitoring."
set.add name="ontology.public_transport_digitalization" id="ptd.fleet_management"

def "ptd.infrastructure" "Digital and physical infrastructure for public transport."
set.add name="ontology.public_transport_digitalization" id="ptd.infrastructure"

def "ptd.maas_integration" "Integration with MaaS platforms and multimodal mobility."
set.add name="ontology.public_transport_digitalization" id="ptd.maas_integration"

def "ptd.operations" "Transit operations and scheduling."
set.add name="ontology.public_transport_digitalization" id="ptd.operations"

def "ptd.passenger_information" "Passenger information systems."
set.add name="ontology.public_transport_digitalization" id="ptd.passenger_information"

def "ptd.real_time" "Real-time data, tracking, and prediction."
set.add name="ontology.public_transport_digitalization" id="ptd.real_time"

def "ptd.ticketing" "Digital ticketing and fare management."
set.add name="ontology.public_transport_digitalization" id="ptd.ticketing"

def "ptd:arrival_prediction" "Arrival time prediction."
ln ptd:arrival_prediction ptd.real_time sys:is_a
ln ptd:arrival_prediction maas:multimodal_routing @enhances
set.add name="ontology.public_transport_digitalization" id="ptd:arrival_prediction"

def "ptd:avl" "Automatic Vehicle Location (AVL)."
ln ptd:avl ptd.real_time sys:is_a
set.add name="ontology.public_transport_digitalization" id="ptd:avl"

def "ptd:demand_forecasting" "Demand forecasting for transit planning."
ln ptd:demand_forecasting ptd.analytics sys:is_a
set.add name="ontology.public_transport_digitalization" id="ptd:demand_forecasting"

def "ptd:dispatching" "Dispatching and headway management."
ln ptd:dispatching ptd.operations sys:is_a
set.add name="ontology.public_transport_digitalization" id="ptd:dispatching"

def "ptd:fare_engine" "Fare calculation and integration engine."
ln ptd:fare_engine ptd.ticketing sys:is_a
ln ptd:fare_engine ptd:fare_integration @supports
set.add name="ontology.public_transport_digitalization" id="ptd:fare_engine"

def "ptd:fare_integration" "Fare integration with MaaS providers."
ln ptd:fare_integration ptd.maas_integration sys:is_a
set.add name="ontology.public_transport_digitalization" id="ptd:fare_integration"

def "ptd:fleet_allocation" "Fleet allocation and optimization."
ln ptd:fleet_allocation ptd.fleet_management sys:is_a
set.add name="ontology.public_transport_digitalization" id="ptd:fleet_allocation"

def "ptd:gtfs_export" "Export of transit data to MaaS platforms."
ln ptd:gtfs_export ptd.maas_integration sys:is_a
set.add name="ontology.public_transport_digitalization" id="ptd:gtfs_export"

def "ptd:ic_card" "IC card systems (e.g., Suica, PASMO)."
ln ptd:ic_card ptd.ticketing sys:is_a
set.add name="ontology.public_transport_digitalization" id="ptd:ic_card"

def "ptd:iot_sensors" "IoT sensors for stations and vehicles."
ln ptd:iot_sensors ptd.infrastructure sys:is_a
set.add name="ontology.public_transport_digitalization" id="ptd:iot_sensors"

def "ptd:load_analysis" "Passenger load analysis."
ln ptd:load_analysis ptd.analytics sys:is_a
set.add name="ontology.public_transport_digitalization" id="ptd:load_analysis"

def "ptd:mobile_apps" "Mobile apps for passenger information."
ln ptd:mobile_apps ptd.passenger_information sys:is_a
set.add name="ontology.public_transport_digitalization" id="ptd:mobile_apps"

def "ptd:mobile_ticket" "Mobile ticketing and digital passes."
ln ptd:mobile_ticket ptd.ticketing sys:is_a
set.add name="ontology.public_transport_digitalization" id="ptd:mobile_ticket"

def "ptd:operations_control" "Operations control centers (OCC)."
ln ptd:operations_control ptd.operations sys:is_a
set.add name="ontology.public_transport_digitalization" id="ptd:operations_control"

def "ptd:operations_optimization" "Operations optimization."
ln ptd:operations_optimization ptd.analytics sys:is_a
set.add name="ontology.public_transport_digitalization" id="ptd:operations_optimization"

def "ptd:platform_screen_doors" "Platform screen doors and safety systems."
ln ptd:platform_screen_doors ptd.infrastructure sys:is_a
set.add name="ontology.public_transport_digitalization" id="ptd:platform_screen_doors"

def "ptd:predictive_maintenance" "Predictive maintenance for transit fleets."
ln ptd:predictive_maintenance ptd.fleet_management sys:is_a
ln ptd:predictive_maintenance ptd:vehicle_health @depends_on
set.add name="ontology.public_transport_digitalization" id="ptd:predictive_maintenance"

def "ptd:qr_ticket" "QR code ticketing."
ln ptd:qr_ticket ptd.ticketing sys:is_a
set.add name="ontology.public_transport_digitalization" id="ptd:qr_ticket"

def "ptd:realtime_api" "Real-time APIs for MaaS integration."
ln ptd:realtime_api ptd.maas_integration sys:is_a
set.add name="ontology.public_transport_digitalization" id="ptd:realtime_api"

def "ptd:realtime_feed" "Real-time transit data feeds (GTFS-RT)."
ln ptd:realtime_feed ptd.real_time sys:is_a
ln ptd:realtime_feed ptd:mobile_apps @informs
set.add name="ontology.public_transport_digitalization" id="ptd:realtime_feed"

def "ptd:scheduling" "Timetable and schedule creation."
ln ptd:scheduling ptd.operations sys:is_a
set.add name="ontology.public_transport_digitalization" id="ptd:scheduling"

def "ptd:service_alerts" "Service alerts and disruption notifications."
ln ptd:service_alerts ptd.passenger_information sys:is_a
set.add name="ontology.public_transport_digitalization" id="ptd:service_alerts"

def "ptd:signaling" "Digital signaling systems."
ln ptd:signaling ptd.infrastructure sys:is_a
ln ptd:signaling ptd:operations_control @required_for
set.add name="ontology.public_transport_digitalization" id="ptd:signaling"

def "ptd:station_display" "Station and onboard displays."
ln ptd:station_display ptd.passenger_information sys:is_a
set.add name="ontology.public_transport_digitalization" id="ptd:station_display"

def "ptd:vehicle_health" "Vehicle health monitoring."
ln ptd:vehicle_health ptd.fleet_management sys:is_a
set.add name="ontology.public_transport_digitalization" id="ptd:vehicle_health"
