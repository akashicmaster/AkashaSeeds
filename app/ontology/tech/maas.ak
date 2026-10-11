# Akasha ontology — namespace: maas
# atoms: 29

def "maas.autonomous_mobility" "Integration of autonomous vehicles and fleets into MaaS."
set.add name="ontology.maas" id="maas.autonomous_mobility"

def "maas.data_interoperability" "Data standards and interoperability frameworks."
set.add name="ontology.maas" id="maas.data_interoperability"

def "maas.modal_integration" "Integration of multiple mobility modes."
set.add name="ontology.maas" id="maas.modal_integration"

def "maas.payment" "Payment, ticketing, and fare integration."
set.add name="ontology.maas" id="maas.payment"

def "maas.platform" "MaaS platforms and orchestration layers."
set.add name="ontology.maas" id="maas.platform"

def "maas.routing" "Routing, optimization, and trip planning."
set.add name="ontology.maas" id="maas.routing"

def "maas.urban_mobility" "Urban mobility systems and public transport integration."
set.add name="ontology.maas" id="maas.urban_mobility"

def "maas:autonomous_fleet" "Autonomous vehicle fleets integrated into MaaS."
ln maas:autonomous_fleet maas.autonomous_mobility sys:is_a
ln maas:autonomous_fleet maas:predictive_routing @influences
set.add name="ontology.maas" id="maas:autonomous_fleet"

def "maas:autonomous_rail" "Driverless rail integrated into MaaS."
ln maas:autonomous_rail maas.autonomous_mobility sys:is_a
set.add name="ontology.maas" id="maas:autonomous_rail"

def "maas:autonomous_shuttle" "Autonomous shuttles for first/last-mile mobility."
ln maas:autonomous_shuttle maas.autonomous_mobility sys:is_a
set.add name="ontology.maas" id="maas:autonomous_shuttle"

def "maas:billing" "Billing and settlement between providers."
ln maas:billing maas.payment sys:is_a
set.add name="ontology.maas" id="maas:billing"

def "maas:car_sharing" "Car sharing services."
ln maas:car_sharing maas.modal_integration sys:is_a
set.add name="ontology.maas" id="maas:car_sharing"

def "maas:consumer_app" "User-facing MaaS application."
ln maas:consumer_app maas.platform sys:is_a
set.add name="ontology.maas" id="maas:consumer_app"

def "maas:fare_integration" "Unified fare integration across modes."
ln maas:fare_integration maas.payment sys:is_a
ln maas:fare_integration maas:service_provider @requires
set.add name="ontology.maas" id="maas:fare_integration"

def "maas:gtfs" "GTFS for static transit data."
ln maas:gtfs maas.data_interoperability sys:is_a
set.add name="ontology.maas" id="maas:gtfs"

def "maas:gtfs_realtime" "GTFS-RT for real-time transit data."
ln maas:gtfs_realtime maas.data_interoperability sys:is_a
ln maas:gtfs_realtime maas:real_time_routing @informs
set.add name="ontology.maas" id="maas:gtfs_realtime"

def "maas:micromobility" "Micromobility (bike, scooter, e-bike)."
ln maas:micromobility maas.modal_integration sys:is_a
set.add name="ontology.maas" id="maas:micromobility"

def "maas:multimodal_routing" "Multimodal routing across transport modes."
ln maas:multimodal_routing maas.routing sys:is_a
ln maas:multimodal_routing maas:consumer_app @used_by
set.add name="ontology.maas" id="maas:multimodal_routing"

def "maas:orchestration_platform" "MaaS orchestration platform integrating modes, data, and services."
ln maas:orchestration_platform maas.platform sys:is_a
set.add name="ontology.maas" id="maas:orchestration_platform"

def "maas:predictive_routing" "Predictive routing using demand and traffic forecasts."
ln maas:predictive_routing maas.routing sys:is_a
set.add name="ontology.maas" id="maas:predictive_routing"

def "maas:public_transport" "Public transport integration (bus, rail, metro)."
ln maas:public_transport maas.modal_integration sys:is_a
set.add name="ontology.maas" id="maas:public_transport"

def "maas:public_transport_ops" "Public transport operations integration."
ln maas:public_transport_ops maas.urban_mobility sys:is_a
set.add name="ontology.maas" id="maas:public_transport_ops"

def "maas:real_time_routing" "Real-time routing using live data."
ln maas:real_time_routing maas.routing sys:is_a
set.add name="ontology.maas" id="maas:real_time_routing"

def "maas:ride_hailing" "Ride-hailing and on-demand mobility."
ln maas:ride_hailing maas.modal_integration sys:is_a
set.add name="ontology.maas" id="maas:ride_hailing"

def "maas:service_provider" "Mobility service providers participating in MaaS."
ln maas:service_provider maas.platform sys:is_a
set.add name="ontology.maas" id="maas:service_provider"

def "maas:smart_parking" "Smart parking systems."
ln maas:smart_parking maas.urban_mobility sys:is_a
set.add name="ontology.maas" id="maas:smart_parking"

def "maas:ticketing" "Digital ticketing and passes."
ln maas:ticketing maas.payment sys:is_a
set.add name="ontology.maas" id="maas:ticketing"

def "maas:traffic_management" "Urban traffic management systems."
ln maas:traffic_management maas.urban_mobility sys:is_a
ln maas:traffic_management maas:real_time_routing @supports
set.add name="ontology.maas" id="maas:traffic_management"

def "maas:transport_data_exchange" "Transport data exchange standards."
ln maas:transport_data_exchange maas.data_interoperability sys:is_a
set.add name="ontology.maas" id="maas:transport_data_exchange"
