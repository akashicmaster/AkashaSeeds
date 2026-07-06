# Akasha ontology — namespace: journey
# atoms: 12

def "journey:approach" "The hero prepares for the central ordeal."
ln journey:approach narrative.journey sys:is_a
ln journey:approach journey:ordeal @then
set.add name="ontology.narrative" id="journey:approach"

def "journey:call_to_adventure" "A problem or challenge disrupts the ordinary world."
ln journey:call_to_adventure narrative.journey sys:is_a
ln journey:call_to_adventure journey:refusal_of_the_call @then
set.add name="ontology.narrative" id="journey:call_to_adventure"

def "journey:crossing_the_threshold" "The hero commits and enters the special world."
ln journey:crossing_the_threshold narrative.journey sys:is_a
ln journey:crossing_the_threshold journey:tests_allies_enemies @then
set.add name="ontology.narrative" id="journey:crossing_the_threshold"

def "journey:meeting_the_mentor" "The hero gains guidance, training, or a gift."
ln journey:meeting_the_mentor narrative.journey sys:is_a
ln journey:meeting_the_mentor journey:crossing_the_threshold @then
set.add name="ontology.narrative" id="journey:meeting_the_mentor"

def "journey:ordeal" "The hero faces the greatest fear or crisis."
ln journey:ordeal narrative.journey sys:is_a
ln journey:ordeal journey:reward @then
set.add name="ontology.narrative" id="journey:ordeal"

def "journey:ordinary_world" "The hero's normal life before the story begins."
ln journey:ordinary_world narrative.journey sys:is_a
ln journey:ordinary_world journey:call_to_adventure @then
set.add name="ontology.narrative" id="journey:ordinary_world"

def "journey:refusal_of_the_call" "The hero hesitates or refuses the call."
ln journey:refusal_of_the_call narrative.journey sys:is_a
ln journey:refusal_of_the_call journey:meeting_the_mentor @then
set.add name="ontology.narrative" id="journey:refusal_of_the_call"

def "journey:resurrection" "A final test purifies and transforms the hero."
ln journey:resurrection narrative.journey sys:is_a
ln journey:resurrection journey:return_with_the_elixir @then
set.add name="ontology.narrative" id="journey:resurrection"

def "journey:return_with_the_elixir" "The hero returns home bearing something that heals."
ln journey:return_with_the_elixir narrative.journey sys:is_a
set.add name="ontology.narrative" id="journey:return_with_the_elixir"

def "journey:reward" "The hero survives and seizes the reward."
ln journey:reward narrative.journey sys:is_a
ln journey:reward journey:the_road_back @then
set.add name="ontology.narrative" id="journey:reward"

def "journey:tests_allies_enemies" "The hero is tested and learns the new world's rules."
ln journey:tests_allies_enemies narrative.journey sys:is_a
ln journey:tests_allies_enemies journey:approach @then
set.add name="ontology.narrative" id="journey:tests_allies_enemies"

def "journey:the_road_back" "The hero begins the return, pursued by consequences."
ln journey:the_road_back narrative.journey sys:is_a
ln journey:the_road_back journey:resurrection @then
set.add name="ontology.narrative" id="journey:the_road_back"
