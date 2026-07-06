# Akasha ontology — namespace: satcom
# atoms: 36

def "satcom.network" "Satellite network architecture including bent-pipe, regenerative payload, and ISL."
ln satcom.network ont.satellite_communications sys:part_of
set.add name="ontology.satellite_communications" id="satcom.network"

def "satcom.operations" "Satellite operations including TT&C, NOC, and handover."
ln satcom.operations ont.satellite_communications sys:part_of
set.add name="ontology.satellite_communications" id="satcom.operations"

def "satcom.orbit" "Satellite orbit types including GEO, MEO, LEO, and HEO."
ln satcom.orbit ont.satellite_communications sys:part_of
set.add name="ontology.satellite_communications" id="satcom.orbit"

def "satcom.protocol" "Satellite communication protocols including DVB-S2, ACM, and RCS2."
ln satcom.protocol ont.satellite_communications sys:part_of
set.add name="ontology.satellite_communications" id="satcom.protocol"

def "satcom.radio" "RF technologies including uplink/downlink, frequency bands, and link budget."
ln satcom.radio ont.satellite_communications sys:part_of
set.add name="ontology.satellite_communications" id="satcom.radio"

def "satcom.security" "Satellite security including anti-jamming, encryption, and spoofing protection."
ln satcom.security ont.satellite_communications sys:part_of
set.add name="ontology.satellite_communications" id="satcom.security"

def "satcom.services" "Satellite services including broadband, IoT, broadcast, and backhaul."
ln satcom.services ont.satellite_communications sys:part_of
set.add name="ontology.satellite_communications" id="satcom.services"

def "satcom:acm" "Adaptive coding and modulation."
ln satcom:acm satcom.protocol sys:is_a
ln satcom:acm satcom:dvb_s2x @enhances
set.add name="ontology.satellite_communications" id="satcom:acm"

def "satcom:anti_jamming" "Techniques to prevent jamming."
ln satcom:anti_jamming satcom.security sys:is_a
ln satcom:anti_jamming satcom.radio @protects
set.add name="ontology.satellite_communications" id="satcom:anti_jamming"

def "satcom:aviation" "In-flight satellite connectivity."
ln satcom:aviation satcom.services sys:is_a
set.add name="ontology.satellite_communications" id="satcom:aviation"

def "satcom:backhaul" "Mobile network backhaul via satellite."
ln satcom:backhaul satcom.services sys:is_a
set.add name="ontology.satellite_communications" id="satcom:backhaul"

def "satcom:bent_pipe" "Transparent payload relaying signals."
ln satcom:bent_pipe satcom.network sys:is_a
set.add name="ontology.satellite_communications" id="satcom:bent_pipe"

def "satcom:broadband" "Satellite broadband internet."
ln satcom:broadband satcom.services sys:is_a
set.add name="ontology.satellite_communications" id="satcom:broadband"

def "satcom:doppler" "Frequency shift due to satellite motion."
ln satcom:doppler satcom.radio sys:is_a
set.add name="ontology.satellite_communications" id="satcom:doppler"

def "satcom:dvb_rcs2" "Return channel via satellite."
ln satcom:dvb_rcs2 satcom.protocol sys:is_a
set.add name="ontology.satellite_communications" id="satcom:dvb_rcs2"

def "satcom:dvb_s2" "DVB-S2 satellite broadcast standard."
ln satcom:dvb_s2 satcom.protocol sys:is_a
set.add name="ontology.satellite_communications" id="satcom:dvb_s2"

def "satcom:dvb_s2x" "Enhanced DVB-S2X standard."
ln satcom:dvb_s2x satcom.protocol sys:is_a
set.add name="ontology.satellite_communications" id="satcom:dvb_s2x"

def "satcom:encryption" "Encryption for satellite links."
ln satcom:encryption satcom.security sys:is_a
set.add name="ontology.satellite_communications" id="satcom:encryption"

def "satcom:gateway" "Ground station connecting satellite to terrestrial networks."
ln satcom:gateway satcom.network sys:is_a
ln satcom:gateway satcom:backhaul @supports
set.add name="ontology.satellite_communications" id="satcom:gateway"

def "satcom:geo" "Geostationary Earth Orbit."
ln satcom:geo satcom.orbit sys:is_a
set.add name="ontology.satellite_communications" id="satcom:geo"

def "satcom:gnss_spoofing_protection" "Protection against GNSS spoofing."
ln satcom:gnss_spoofing_protection satcom.security sys:is_a
set.add name="ontology.satellite_communications" id="satcom:gnss_spoofing_protection"

def "satcom:handover" "Handover between LEO satellites."
ln satcom:handover satcom.operations sys:is_a
set.add name="ontology.satellite_communications" id="satcom:handover"

def "satcom:heo" "Highly Elliptical Orbit."
ln satcom:heo satcom.orbit sys:is_a
set.add name="ontology.satellite_communications" id="satcom:heo"

def "satcom:inclined" "Inclined orbit for regional coverage."
ln satcom:inclined satcom.orbit sys:is_a
set.add name="ontology.satellite_communications" id="satcom:inclined"

def "satcom:iot_satellite" "IoT connectivity via satellite."
ln satcom:iot_satellite satcom.services sys:is_a
set.add name="ontology.satellite_communications" id="satcom:iot_satellite"

def "satcom:isl" "Inter-satellite link."
ln satcom:isl satcom.network sys:is_a
ln satcom:isl word:en:constellation @supports
set.add name="ontology.satellite_communications" id="satcom:isl"

def "satcom:ka_band" "Ka-band satellite frequency."
ln satcom:ka_band satcom.radio sys:is_a
set.add name="ontology.satellite_communications" id="satcom:ka_band"

def "satcom:ku_band" "Ku-band satellite frequency."
ln satcom:ku_band satcom.radio sys:is_a
set.add name="ontology.satellite_communications" id="satcom:ku_band"

def "satcom:leo" "Low Earth Orbit."
ln satcom:leo satcom.orbit sys:is_a
ln satcom:leo satcom:handover @requires
set.add name="ontology.satellite_communications" id="satcom:leo"

def "satcom:link_budget" "Calculation of received signal strength."
ln satcom:link_budget satcom.radio sys:is_a
set.add name="ontology.satellite_communications" id="satcom:link_budget"

def "satcom:maritime" "Maritime satellite connectivity."
ln satcom:maritime satcom.services sys:is_a
set.add name="ontology.satellite_communications" id="satcom:maritime"

def "satcom:meo" "Medium Earth Orbit."
ln satcom:meo satcom.orbit sys:is_a
set.add name="ontology.satellite_communications" id="satcom:meo"

def "satcom:noc" "Network operations center for satellite systems."
ln satcom:noc satcom.operations sys:is_a
set.add name="ontology.satellite_communications" id="satcom:noc"

def "satcom:regenerative" "Payload performing onboard processing."
ln satcom:regenerative satcom.network sys:is_a
set.add name="ontology.satellite_communications" id="satcom:regenerative"

def "satcom:s_band" "S-band satellite frequency."
ln satcom:s_band satcom.radio sys:is_a
set.add name="ontology.satellite_communications" id="satcom:s_band"

def "satcom:ttc" "Telemetry, Tracking, and Command."
ln satcom:ttc satcom.operations sys:is_a
set.add name="ontology.satellite_communications" id="satcom:ttc"
