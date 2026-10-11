# Akasha ontology — namespace: wr
# atoms: 30

def "wr.circular_economy" "Circular economy and resource loops."
set.add name="ontology.waste_recycling" id="wr.circular_economy"

def "wr.collection" "Waste collection and logistics."
set.add name="ontology.waste_recycling" id="wr.collection"

def "wr.disposal" "Final disposal systems."
set.add name="ontology.waste_recycling" id="wr.disposal"

def "wr.monitoring" "Monitoring, IoT, and smart waste systems."
set.add name="ontology.waste_recycling" id="wr.monitoring"

def "wr.recycling" "Recycling and resource recovery."
set.add name="ontology.waste_recycling" id="wr.recycling"

def "wr.sorting" "Waste sorting and classification."
set.add name="ontology.waste_recycling" id="wr.sorting"

def "wr.treatment" "Waste treatment and processing."
set.add name="ontology.waste_recycling" id="wr.treatment"

def "wr:ai_sorting" "AI-based waste classification."
ln wr:ai_sorting wr.sorting sys:is_a
set.add name="ontology.waste_recycling" id="wr:ai_sorting"

def "wr:anaerobic_digestion" "Anaerobic digestion for biogas."
ln wr:anaerobic_digestion wr.treatment sys:is_a
ln wr:anaerobic_digestion wr:biogas @produces
set.add name="ontology.waste_recycling" id="wr:anaerobic_digestion"

def "wr:ash_disposal" "Ash disposal from incineration."
ln wr:ash_disposal wr.disposal sys:is_a
set.add name="ontology.waste_recycling" id="wr:ash_disposal"

def "wr:automated_sorting" "Automated sorting using sensors and robotics."
ln wr:automated_sorting wr.sorting sys:is_a
ln wr:automated_sorting wr:material_recovery @feeds
set.add name="ontology.waste_recycling" id="wr:automated_sorting"

def "wr:biogas" "Biogas production from organic waste."
ln wr:biogas wr.circular_economy sys:is_a
set.add name="ontology.waste_recycling" id="wr:biogas"

def "wr:collection_routing" "Routing optimization for waste collection."
ln wr:collection_routing wr.collection sys:is_a
set.add name="ontology.waste_recycling" id="wr:collection_routing"

def "wr:collection_truck" "Garbage collection trucks."
ln wr:collection_truck wr.collection sys:is_a
set.add name="ontology.waste_recycling" id="wr:collection_truck"

def "wr:composting" "Organic waste composting."
ln wr:composting wr.treatment sys:is_a
ln wr:composting wr:biogas @supports
set.add name="ontology.waste_recycling" id="wr:composting"

def "wr:e_waste" "Electronic waste recycling."
ln wr:e_waste wr.recycling sys:is_a
ln wr:e_waste wr:hazardous_waste @requires
set.add name="ontology.waste_recycling" id="wr:e_waste"

def "wr:fill_level" "Fill-level monitoring for bins."
ln wr:fill_level wr.monitoring sys:is_a
set.add name="ontology.waste_recycling" id="wr:fill_level"

def "wr:glass_recycling" "Glass recycling."
ln wr:glass_recycling wr.recycling sys:is_a
set.add name="ontology.waste_recycling" id="wr:glass_recycling"

def "wr:hazardous_waste" "Hazardous waste disposal."
ln wr:hazardous_waste wr.disposal sys:is_a
set.add name="ontology.waste_recycling" id="wr:hazardous_waste"

def "wr:incineration" "Incineration and thermal treatment."
ln wr:incineration wr.treatment sys:is_a
set.add name="ontology.waste_recycling" id="wr:incineration"

def "wr:iot_sensors" "IoT sensors for waste monitoring."
ln wr:iot_sensors wr.monitoring sys:is_a
set.add name="ontology.waste_recycling" id="wr:iot_sensors"

def "wr:landfill" "Landfill disposal."
ln wr:landfill wr.disposal sys:is_a
set.add name="ontology.waste_recycling" id="wr:landfill"

def "wr:manual_sorting" "Manual sorting of waste."
ln wr:manual_sorting wr.sorting sys:is_a
set.add name="ontology.waste_recycling" id="wr:manual_sorting"

def "wr:material_recovery" "Material recovery facilities (MRF)."
ln wr:material_recovery wr.circular_economy sys:is_a
set.add name="ontology.waste_recycling" id="wr:material_recovery"

def "wr:metal_recycling" "Metal recycling."
ln wr:metal_recycling wr.recycling sys:is_a
set.add name="ontology.waste_recycling" id="wr:metal_recycling"

def "wr:paper_recycling" "Paper recycling."
ln wr:paper_recycling wr.recycling sys:is_a
set.add name="ontology.waste_recycling" id="wr:paper_recycling"

def "wr:plastic_recycling" "Plastic recycling processes."
ln wr:plastic_recycling wr.recycling sys:is_a
set.add name="ontology.waste_recycling" id="wr:plastic_recycling"

def "wr:reuse" "Reuse and upcycling."
ln wr:reuse wr.circular_economy sys:is_a
set.add name="ontology.waste_recycling" id="wr:reuse"

def "wr:scada" "SCADA systems for waste facilities."
ln wr:scada wr.monitoring sys:is_a
set.add name="ontology.waste_recycling" id="wr:scada"

def "wr:waste_bins" "Waste bins and container systems."
ln wr:waste_bins wr.collection sys:is_a
ln wr:waste_bins wr:fill_level @monitored_by
set.add name="ontology.waste_recycling" id="wr:waste_bins"
