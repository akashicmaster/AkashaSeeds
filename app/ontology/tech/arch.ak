# Akasha ontology — namespace: arch
# atoms: 8

def "arch:ally" "A companion who supports the hero."
ln arch:ally narrative.archetype sys:is_a
set.add name="ontology.narrative" id="arch:ally"

def "arch:herald" "The one who announces the call to change."
ln arch:herald narrative.archetype sys:is_a
ln arch:herald journey:call_to_adventure @related_to
set.add name="ontology.narrative" id="arch:herald"

def "arch:hero" "The protagonist who grows through the journey."
ln arch:hero narrative.archetype sys:is_a
ln arch:hero narrative.journey @related_to
ln arch:hero arch:shadow @contrasts_with
ln arch:hero word:en:hero @related_to
ln arch:hero word:en:protagonist @related_to
set.add name="ontology.narrative" id="arch:hero"

def "arch:mentor" "The guide who aids and equips the hero."
ln arch:mentor narrative.archetype sys:is_a
ln arch:mentor journey:meeting_the_mentor @related_to
ln arch:mentor fnty:soul_contractor @related_to
set.add name="ontology.narrative" id="arch:mentor"

def "arch:shadow" "The antagonistic force embodying what is opposed."
ln arch:shadow narrative.archetype sys:is_a
ln arch:shadow journey:ordeal @related_to
ln arch:shadow word:en:antagonist @related_to
ln arch:shadow word:en:villain @related_to
ln arch:shadow fnty:destined_rival @related_to
set.add name="ontology.narrative" id="arch:shadow"

def "arch:shapeshifter" "A figure of shifting loyalty or identity."
ln arch:shapeshifter narrative.archetype sys:is_a
set.add name="ontology.narrative" id="arch:shapeshifter"

def "arch:threshold_guardian" "A figure who tests the hero at a boundary."
ln arch:threshold_guardian narrative.archetype sys:is_a
ln arch:threshold_guardian journey:crossing_the_threshold @related_to
set.add name="ontology.narrative" id="arch:threshold_guardian"

def "arch:trickster" "A disruptive figure who upsets the order."
ln arch:trickster narrative.archetype sys:is_a
set.add name="ontology.narrative" id="arch:trickster"
