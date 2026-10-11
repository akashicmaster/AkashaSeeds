# Akasha ontology — namespace: idea
# atoms: 28

def "idea:affinity_diagram" "KJ method: grouping ideas into themes to reveal structure."
ln idea:affinity_diagram ideation.methods sys:is_a
ln idea:affinity_diagram idea:insight_extraction @enables
set.add name="ontology.ideation" id="idea:affinity_diagram"

def "idea:brainstorming" "Free-form group ideation technique encouraging quantity over quality."
ln idea:brainstorming ideation.methods sys:is_a
ln idea:brainstorming idea:divergent_thinking @supports
set.add name="ontology.ideation" id="idea:brainstorming"

def "idea:brainwriting" "Silent idea generation technique where participants write ideas individually."
ln idea:brainwriting ideation.methods sys:is_a
ln idea:brainwriting idea:convergent_thinking @supports
set.add name="ontology.ideation" id="idea:brainwriting"

def "idea:concept_test" "Evaluating an idea with users or stakeholders."
ln idea:concept_test ideation.process sys:is_a
set.add name="ontology.ideation" id="idea:concept_test"

def "idea:consensus_building" "Techniques for aligning stakeholders around shared decisions."
ln idea:consensus_building ideation.collaboration sys:is_a
set.add name="ontology.ideation" id="idea:consensus_building"

def "idea:convergent_thinking" "Narrowing options to select the most promising ideas."
ln idea:convergent_thinking ideation.process sys:is_a
set.add name="ontology.ideation" id="idea:convergent_thinking"

def "idea:divergent_thinking" "Expanding the solution space through broad exploration."
ln idea:divergent_thinking ideation.process sys:is_a
set.add name="ontology.ideation" id="idea:divergent_thinking"

def "idea:dot_voting" "Group voting technique for selecting ideas."
ln idea:dot_voting ideation.evaluation sys:is_a
set.add name="ontology.ideation" id="idea:dot_voting"

def "idea:facilitation" "Guiding group processes to maximize creativity and clarity."
ln idea:facilitation ideation.collaboration sys:is_a
ln idea:facilitation ideation.process @supports
set.add name="ontology.ideation" id="idea:facilitation"

def "idea:five_whys" "Root cause analysis by repeatedly asking 'Why?'."
ln idea:five_whys ideation.frameworks sys:is_a
set.add name="ontology.ideation" id="idea:five_whys"

def "idea:impact_effort" "Matrix evaluating ideas by impact and implementation effort."
ln idea:impact_effort ideation.evaluation sys:is_a
ln idea:impact_effort idea:convergent_thinking @supports
set.add name="ontology.ideation" id="idea:impact_effort"

def "idea:insight_extraction" "Identifying underlying truths or patterns that guide ideation."
ln idea:insight_extraction ideation.process sys:is_a
set.add name="ontology.ideation" id="idea:insight_extraction"

def "idea:journey_map" "Mapping user experience across stages to identify insights."
ln idea:journey_map ideation.frameworks sys:is_a
set.add name="ontology.ideation" id="idea:journey_map"

def "idea:kano_model" "Model classifying features by customer satisfaction impact."
ln idea:kano_model ideation.evaluation sys:is_a
set.add name="ontology.ideation" id="idea:kano_model"

def "idea:lateral_thinking" "Technique for generating ideas by breaking logical patterns."
ln idea:lateral_thinking ideation.methods sys:is_a
set.add name="ontology.ideation" id="idea:lateral_thinking"

def "idea:logic_tree" "Tree structure for breaking down problems into components."
ln idea:logic_tree ideation.frameworks sys:is_a
set.add name="ontology.ideation" id="idea:logic_tree"

def "idea:mece" "Mutually Exclusive, Collectively Exhaustive — structuring principle for clarity."
ln idea:mece ideation.frameworks sys:is_a
set.add name="ontology.ideation" id="idea:mece"

def "idea:mind_map" "Visual technique for exploring ideas through branching associations."
ln idea:mind_map ideation.methods sys:is_a
ln idea:mind_map idea:logic_tree @related_to
set.add name="ontology.ideation" id="idea:mind_map"

def "idea:moscow" "Must / Should / Could / Won't prioritization method."
ln idea:moscow ideation.evaluation sys:is_a
set.add name="ontology.ideation" id="idea:moscow"

def "idea:problem_framing" "Defining the core problem and reframing it to reveal opportunities."
ln idea:problem_framing ideation.process sys:is_a
set.add name="ontology.ideation" id="idea:problem_framing"

def "idea:prototype" "Early, simplified representation of an idea used for testing."
ln idea:prototype ideation.process sys:is_a
ln idea:prototype idea:concept_test @precedes
set.add name="ontology.ideation" id="idea:prototype"

def "idea:random_word" "Idea generation using random stimuli to provoke new associations."
ln idea:random_word ideation.methods sys:is_a
set.add name="ontology.ideation" id="idea:random_word"

def "idea:reverse_brainstorm" "Technique for generating ideas by inverting the problem."
ln idea:reverse_brainstorm ideation.methods sys:is_a
set.add name="ontology.ideation" id="idea:reverse_brainstorm"

def "idea:rice" "Reach, Impact, Confidence, Effort scoring model."
ln idea:rice ideation.evaluation sys:is_a
set.add name="ontology.ideation" id="idea:rice"

def "idea:scamper" "SCAMPER creativity method: Substitute, Combine, Adapt, Modify, Put to other uses, Eliminate, Reverse."
ln idea:scamper ideation.methods sys:is_a
set.add name="ontology.ideation" id="idea:scamper"

def "idea:storyboard" "Visual sequence describing how an idea works in context."
ln idea:storyboard ideation.process sys:is_a
set.add name="ontology.ideation" id="idea:storyboard"

def "idea:swot" "Strengths, Weaknesses, Opportunities, Threats analysis."
ln idea:swot ideation.frameworks sys:is_a
set.add name="ontology.ideation" id="idea:swot"

def "idea:workshop" "Structured collaborative session for ideation or planning."
ln idea:workshop ideation.collaboration sys:is_a
ln idea:workshop ideation.methods @enables
set.add name="ontology.ideation" id="idea:workshop"
