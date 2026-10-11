# Akasha ontology — namespace: map
# atoms: 6

def "map:has_edition" "A MapConcept root has a cartographic edition entry (a specific version of a map document)."
ln map:has_edition ont.map sys:part_of
set.add name="ontology.earth" id="map:has_edition"

def "map:has_feature" "A map has a drawn cartographic feature (polygon, line, point, symbol)."
ln map:has_feature ont.map sys:part_of
set.add name="ontology.earth" id="map:has_feature"

def "map:has_geometry" "A map feature has associated geometric data (GeoJSON, WKT, or native coordinate list)."
ln map:has_geometry ont.map sys:part_of

def "map:has_grounding" "A map feature has a grounding link to a real-world entity (GeoConcept place, CountryConcept territory, etc.)."
ln map:has_grounding ont.map sys:part_of
ln map:has_grounding geo:has_place thesaurus:related
set.add name="ontology.earth" id="map:has_grounding"

def "map:has_label" "A map feature has a text label entry with position and style."
ln map:has_label ont.map sys:part_of

def "map:has_projection" "A map edition uses a named cartographic projection (e.g. Mercator, Robinson, WGS84)."
ln map:has_projection ont.map sys:part_of
