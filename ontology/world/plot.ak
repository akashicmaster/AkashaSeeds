# Akasha ontology — namespace: plot
# atoms: 7

def "plot:comedy" "Confusion and tangle resolved into harmony and union."
ln plot:comedy narrative.basic_plot sys:is_a
ln plot:comedy plot:tragedy @contrasts_with
ln plot:comedy word:en:comedy @related_to
set.add name="ontology.narrative" id="plot:comedy"

def "plot:overcoming_the_monster" "The hero confronts and defeats a great threat."
ln plot:overcoming_the_monster narrative.basic_plot sys:is_a
ln plot:overcoming_the_monster arch:shadow @related_to
ln plot:overcoming_the_monster emo:fear @reads_as
set.add name="ontology.narrative" id="plot:overcoming_the_monster"

def "plot:rags_to_riches" "An ordinary figure rises, loses all, and rises again wiser."
ln plot:rags_to_riches narrative.basic_plot sys:is_a
set.add name="ontology.narrative" id="plot:rags_to_riches"

def "plot:rebirth" "A figure falls under a dark spell and is redeemed."
ln plot:rebirth narrative.basic_plot sys:is_a
ln plot:rebirth emo:awe @reads_as
ln plot:rebirth fnty:yamiodochi @related_to
set.add name="ontology.narrative" id="plot:rebirth"

def "plot:the_quest" "A hero journeys toward a distant goal against trials."
ln plot:the_quest narrative.basic_plot sys:is_a
ln plot:the_quest narrative.journey @related_to
ln plot:the_quest fnty:isekai_reincarnation @related_to
set.add name="ontology.narrative" id="plot:the_quest"

def "plot:tragedy" "A flaw drives a protagonist to downfall."
ln plot:tragedy narrative.basic_plot sys:is_a
ln plot:tragedy emo:despair @reads_as
ln plot:tragedy word:en:tragedy @related_to
set.add name="ontology.narrative" id="plot:tragedy"

def "plot:voyage_and_return" "A hero enters a strange world and comes home changed."
ln plot:voyage_and_return narrative.basic_plot sys:is_a
set.add name="ontology.narrative" id="plot:voyage_and_return"
