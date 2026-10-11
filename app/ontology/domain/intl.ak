# Akasha ontology — namespace: intl
# atoms: 27

def "intl.customs" "Customs clearance, duties, tariffs, and border procedures."
ln intl.customs ont.international_logistics sys:part_of
set.add name="ontology.international_logistics" id="intl.customs"

def "intl.documentation" "International shipping documents, certificates, and legal paperwork."
ln intl.documentation ont.international_logistics sys:part_of
set.add name="ontology.international_logistics" id="intl.documentation"

def "intl.risk" "Risks in international logistics including geopolitical, regulatory, and transit risks."
ln intl.risk ont.international_logistics sys:part_of
set.add name="ontology.international_logistics" id="intl.risk"

def "intl.shipping" "Global shipping modes, carriers, and international transport networks."
ln intl.shipping ont.international_logistics sys:part_of
set.add name="ontology.international_logistics" id="intl.shipping"

def "intl.trade_compliance" "Trade regulations, export controls, sanctions, and compliance."
ln intl.trade_compliance ont.international_logistics sys:part_of
set.add name="ontology.international_logistics" id="intl.trade_compliance"

def "intl:air_freight" "International transportation of goods by aircraft."
ln intl:air_freight intl.shipping sys:is_a
set.add name="ontology.international_logistics" id="intl:air_freight"

def "intl:bill_of_lading" "Legal document issued by a carrier acknowledging receipt of cargo."
ln intl:bill_of_lading intl.documentation sys:is_a
set.add name="ontology.international_logistics" id="intl:bill_of_lading"

def "intl:certificate_of_origin" "Document certifying the country where goods were produced."
ln intl:certificate_of_origin intl.documentation sys:is_a
set.add name="ontology.international_logistics" id="intl:certificate_of_origin"

def "intl:commercial_invoice" "Document detailing the transaction between exporter and importer."
ln intl:commercial_invoice intl.documentation sys:is_a
set.add name="ontology.international_logistics" id="intl:commercial_invoice"

def "intl:container_shipping" "Transporting goods in standardized containers."
ln intl:container_shipping intl.shipping sys:is_a
ln intl:container_shipping intl:sea_freight @supports
set.add name="ontology.international_logistics" id="intl:container_shipping"

def "intl:country_of_origin" "Country where a product was manufactured or produced."
ln intl:country_of_origin intl.trade_compliance sys:is_a
set.add name="ontology.international_logistics" id="intl:country_of_origin"

def "intl:customs_broker" "Licensed professional who facilitates customs clearance."
ln intl:customs_broker intl.customs sys:is_a
ln intl:customs_broker intl:customs_clearance @supports
set.add name="ontology.international_logistics" id="intl:customs_broker"

def "intl:customs_clearance" "Process of obtaining approval for goods to enter or leave a country."
ln intl:customs_clearance intl.customs sys:is_a
set.add name="ontology.international_logistics" id="intl:customs_clearance"

def "intl:duties" "Taxes imposed on imported or exported goods."
ln intl:duties intl.customs sys:is_a
set.add name="ontology.international_logistics" id="intl:duties"

def "intl:export_control" "Regulations governing the export of sensitive goods or technologies."
ln intl:export_control intl.trade_compliance sys:is_a
set.add name="ontology.international_logistics" id="intl:export_control"

def "intl:free_trade_agreement" "Agreement reducing trade barriers between countries."
ln intl:free_trade_agreement intl.trade_compliance sys:is_a
ln intl:free_trade_agreement word:en:tariff @reduces
set.add name="ontology.international_logistics" id="intl:free_trade_agreement"

def "intl:geopolitical_risk" "Risks arising from political instability or conflict."
ln intl:geopolitical_risk intl.risk sys:is_a
ln intl:geopolitical_risk intl:sanctions @related_to
set.add name="ontology.international_logistics" id="intl:geopolitical_risk"

def "intl:global_carrier" "International shipping company responsible for transporting goods."
ln intl:global_carrier intl.shipping sys:is_a
set.add name="ontology.international_logistics" id="intl:global_carrier"

def "intl:hs_code" "Harmonized System code used to classify traded goods."
ln intl:hs_code intl.customs sys:is_a
ln intl:hs_code intl:duties @determines
set.add name="ontology.international_logistics" id="intl:hs_code"

def "intl:insurance_certificate" "Document proving insurance coverage for international shipments."
ln intl:insurance_certificate intl.documentation sys:is_a
ln intl:insurance_certificate intl.risk @mitigates
set.add name="ontology.international_logistics" id="intl:insurance_certificate"

def "intl:maritime_piracy" "Security risks affecting sea freight routes."
ln intl:maritime_piracy intl.risk sys:is_a
set.add name="ontology.international_logistics" id="intl:maritime_piracy"

def "intl:multimodal_transport" "Using multiple modes of transport under a single contract."
ln intl:multimodal_transport intl.shipping sys:is_a
ln intl:multimodal_transport intl:global_carrier @related_to
set.add name="ontology.international_logistics" id="intl:multimodal_transport"

def "intl:packing_list" "Document listing the contents of a shipment."
ln intl:packing_list intl.documentation sys:is_a
set.add name="ontology.international_logistics" id="intl:packing_list"

def "intl:regulatory_risk" "Risks due to changes in trade laws or regulations."
ln intl:regulatory_risk intl.risk sys:is_a
set.add name="ontology.international_logistics" id="intl:regulatory_risk"

def "intl:sanctions" "Restrictions imposed on trade with specific countries or entities."
ln intl:sanctions intl.trade_compliance sys:is_a
set.add name="ontology.international_logistics" id="intl:sanctions"

def "intl:sea_freight" "International transportation of goods by ocean vessels."
ln intl:sea_freight intl.shipping sys:is_a
set.add name="ontology.international_logistics" id="intl:sea_freight"

def "intl:transit_delay" "Delays caused by congestion, weather, or operational issues."
ln intl:transit_delay intl.risk sys:is_a
set.add name="ontology.international_logistics" id="intl:transit_delay"
