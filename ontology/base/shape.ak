# Akasha ontology — namespace: shape
# atoms: 6

def "shape:boy_meets_girl" "Something wonderful is found, lost, then regained."
ln shape:boy_meets_girl narrative.shape sys:is_a
ln shape:boy_meets_girl plot:comedy @related_to
set.add name="ontology.narrative" id="shape:boy_meets_girl"

def "shape:cinderella" "A rise, a sudden fall, then a lasting rise."
ln shape:cinderella narrative.shape sys:is_a
ln shape:cinderella plot:rags_to_riches @related_to
set.add name="ontology.narrative" id="shape:cinderella"

def "shape:creation_story" "Incremental gains, step by step upward."
ln shape:creation_story narrative.shape sys:is_a
set.add name="ontology.narrative" id="shape:creation_story"

def "shape:from_bad_to_worse" "A steady decline from an already low start."
ln shape:from_bad_to_worse narrative.shape sys:is_a
ln shape:from_bad_to_worse plot:tragedy @related_to
set.add name="ontology.narrative" id="shape:from_bad_to_worse"

def "shape:man_in_hole" "Fortune drops into trouble, then climbs out higher than before."
ln shape:man_in_hole narrative.shape sys:is_a
ln shape:man_in_hole plot:voyage_and_return @related_to
set.add name="ontology.narrative" id="shape:man_in_hole"

def "shape:which_way_is_up" "Fortune stays ambiguous; the curve resists reading."
ln shape:which_way_is_up narrative.shape sys:is_a
set.add name="ontology.narrative" id="shape:which_way_is_up"
