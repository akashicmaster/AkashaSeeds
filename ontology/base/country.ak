# Akasha ontology — namespace: country
# atoms: 11

def "country:has_capital" "A CountryConcept state has a designated capital city entry."
ln country:has_capital ont.country sys:part_of
set.add name="ontology.earth" id="country:has_capital"

def "country:has_dispute" "A state has an active or historical territorial or diplomatic dispute entry."
ln country:has_dispute ont.country sys:part_of

def "country:has_economy" "A state has an economic indicator entry (GDP, trade, currency, etc.)."
ln country:has_economy ont.country sys:part_of
set.add name="ontology.earth" id="country:has_economy"

def "country:has_government" "A state has a government structure entry (type, leadership, institutions)."
ln country:has_government ont.country sys:part_of

def "country:has_law" "A state has a legal instrument or legislative record entry."
ln country:has_law ont.country sys:part_of

def "country:has_name" "A CountryConcept state has a formal name record (may include historical or unofficial names)."
ln country:has_name ont.country sys:part_of

def "country:has_population" "A state has a population census or estimate entry."
ln country:has_population ont.country sys:part_of

def "country:has_sovereignty" "A state has a sovereignty claim or recognition record."
ln country:has_sovereignty ont.country sys:part_of

def "country:has_territory" "A CountryConcept state has a spatial territory entry (may reference a GeoConcept place via geo_id)."
ln country:has_territory ont.country sys:part_of
ln country:has_territory geo:is_in thesaurus:related
set.add name="ontology.earth" id="country:has_territory"

def "country:uses_correspondence" "Bridge: a CountryConcept entity references a CorrespondenceConcept alignment for cross-system identity resolution."

def "country:uses_geo" "Bridge: a CountryConcept territory references a GeoConcept spatial place as its physical grounding. Enables cross-model spatial queries."
ln country:uses_geo ont.country sys:part_of
ln country:uses_geo geo:has_place thesaurus:related
set.add name="ontology.earth" id="country:uses_geo"
