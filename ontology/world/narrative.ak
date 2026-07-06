# Akasha ontology — namespace: narrative
# atoms: 16

def "narrative.archetype" "Character archetypes recurring across stories."
ln narrative.archetype narrative.typology sys:part_of
set.add name="ontology.narrative" id="narrative.archetype"

def "narrative.basic_plot" "Booker's seven basic plots."
ln narrative.basic_plot narrative.typology sys:part_of
set.add name="ontology.narrative" id="narrative.basic_plot"

def "narrative.bolero" "Bolero arc: repetition with variation. theme -> variation -> crescendo -> resolution."
ln narrative.bolero ont.narrative sys:part_of
set.add name="ontology.narrative" id="narrative.bolero"

def "narrative.journal" "Journal arc: writing-as-noticing. observation -> echo -> insight -> consequence."
ln narrative.journal ont.narrative sys:part_of
set.add name="ontology.narrative" id="narrative.journal"

def "narrative.journey" "The hero's journey (monomyth): ordered stages of a transformative quest."
ln narrative.journey narrative.typology sys:part_of
ln narrative.journey plot:the_quest @related_to
set.add name="ontology.narrative" id="narrative.journey"

def "narrative.magic" "Magic arc: the unwritten promise. expectation -> silence -> revelation -> transfer."
ln narrative.magic ont.narrative sys:part_of
ln narrative.magic plot:rebirth @related_to
set.add name="ontology.narrative" id="narrative.magic"

def "narrative.plot" "Plot arc: the buried seed. seed -> dormant -> bloom."
ln narrative.plot ont.narrative sys:part_of
set.add name="ontology.narrative" id="narrative.plot"

def "narrative.sense" "Sensory craft: channels a passage can anchor in (for void/absence checks)."
ln narrative.sense ont.narrative sys:part_of
set.add name="ontology.narrative" id="narrative.sense"

def "narrative.shape" "Vonnegut's story shapes: the curve of a protagonist's fortune over time."
ln narrative.shape narrative.typology sys:part_of
set.add name="ontology.narrative" id="narrative.shape"

def "narrative.typology" "Story typologies: plot shapes, the hero's journey, story curves, character archetypes."
ln narrative.typology ont.narrative sys:part_of
set.add name="ontology.narrative" id="narrative.typology"
set.add name="ontology.narrative_typology" id="narrative.typology"

def "narrative.typology.conflict" "Conflict narratives: struggle between persons, groups, forces, duties, or values."
ln narrative.typology.conflict narrative.typology sys:part_of
set.add name="ontology.narrative_typology" id="narrative.typology.conflict"

def "narrative.typology.fall_rise" "Fall and rise narratives: loss, descent, recovery, restoration, or renewal."
ln narrative.typology.fall_rise narrative.typology sys:part_of
set.add name="ontology.narrative_typology" id="narrative.typology.fall_rise"

def "narrative.typology.journey" "Journey narratives: movement through space, danger, transformation, or return."
ln narrative.typology.journey narrative.typology sys:part_of
set.add name="ontology.narrative_typology" id="narrative.typology.journey"

def "narrative.typology.revelation" "Revelation narratives: hidden truth, recognition, discovery, testimony, or unveiling."
ln narrative.typology.revelation narrative.typology sys:part_of
set.add name="ontology.narrative_typology" id="narrative.typology.revelation"

def "narrative.typology.society" "Social narratives: community order, legitimacy, law, exile, rebellion, succession, and reconciliation."
ln narrative.typology.society narrative.typology sys:part_of
set.add name="ontology.narrative_typology" id="narrative.typology.society"

def "narrative.typology.transformation" "Transformation narratives: change of identity, status, knowledge, body, society, or world."
ln narrative.typology.transformation narrative.typology sys:part_of
set.add name="ontology.narrative_typology" id="narrative.typology.transformation"
