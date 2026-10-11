# Akasha ontology — namespace: corr
# atoms: 3

def "corr:evidenced_by" "A correspondence alignment is supported by a cited evidence atom (source document, measurement, expert claim)."
ln corr:evidenced_by ont.map sys:part_of

def "corr:from" "Bridge origin: the source entity in a cross-system correspondence alignment created by MapConcept.ground."
ln corr:from ont.map sys:part_of
ln corr:from geo:has_place thesaurus:related
set.add name="ontology.earth" id="corr:from"

def "corr:to" "Bridge target: the destination entity in a cross-system correspondence alignment created by MapConcept.ground."
ln corr:to ont.map sys:part_of
set.add name="ontology.earth" id="corr:to"
