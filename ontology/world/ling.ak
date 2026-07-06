# Akasha ontology — namespace: ling
# atoms: 31

def "ling.discourse" "Extended communication across sentences, speakers, and contexts."
ln ling.discourse ont.linguistics sys:part_of
set.add name="ontology.linguistics" id="ling.discourse"

def "ling.morphology" "Internal structure and formation of words."
ln ling.morphology ont.linguistics sys:part_of
set.add name="ontology.linguistics" id="ling.morphology"

def "ling.pragmatics" "Contextual and situational meaning in communication."
ln ling.pragmatics ont.linguistics sys:part_of
set.add name="ontology.linguistics" id="ling.pragmatics"

def "ling.semantics" "Meaning and conceptual interpretation in language."
ln ling.semantics ont.linguistics sys:part_of
set.add name="ontology.linguistics" id="ling.semantics"

def "ling.semiotics" "Signs, symbols, and representational systems."
ln ling.semiotics ont.linguistics sys:part_of
set.add name="ontology.linguistics" id="ling.semiotics"

def "ling.syntax" "Structural organization of language."
ln ling.syntax ont.linguistics sys:part_of
set.add name="ontology.linguistics" id="ling.syntax"

def "ling:code" "Shared symbolic system enabling communication."
ln ling:code ling.semiotics sys:is_a
set.add name="ontology.linguistics" id="ling:code"

def "ling:context" "Situational framework shaping interpretation."
ln ling:context ling.pragmatics sys:is_a
ln ling:context phil:context sys:same_as
ln ling:context phil:interpretation @shapes
set.add name="ontology.linguistics" id="ling:context"

def "ling:deixis" "Meaning dependent on speaker, place, or time context."
ln ling:deixis ling.pragmatics sys:is_a
ln ling:deixis present @depends_on
ln ling:deixis memory @depends_on
set.add name="ontology.linguistics" id="ling:deixis"

def "ling:dialogue" "Interactive exchange between speakers."
ln ling:dialogue ling.discourse sys:is_a
ln ling:dialogue civ:public_hearing @supports
set.add name="ontology.linguistics" id="ling:dialogue"

def "ling:grammar" "Rules governing linguistic structure and composition."
ln ling:grammar ling.syntax sys:is_a
ln ling:grammar order @supports
set.add name="ontology.linguistics" id="ling:grammar"

def "ling:implication" "Meaning indirectly suggested rather than explicitly stated."
ln ling:implication ling.pragmatics sys:is_a
set.add name="ontology.linguistics" id="ling:implication"

def "ling:meaning" "Conceptual content conveyed through language."
ln ling:meaning ling.semantics sys:is_a
ln ling:meaning phil:meaning sys:same_as
set.add name="ontology.linguistics" id="ling:meaning"

def "ling:metaphor" "Understanding one conceptual domain through another."
ln ling:metaphor ling.semantics sys:is_a
ln ling:metaphor nar:magic_transfer @related_to
set.add name="ontology.linguistics" id="ling:metaphor"

def "ling:morpheme" "Smallest grammatical or semantic unit in language."
ln ling:morpheme ling.morphology sys:is_a
set.add name="ontology.linguistics" id="ling:morpheme"

def "ling:narrative_discourse" "Language organizing events into meaningful sequence."
ln ling:narrative_discourse ling.discourse sys:is_a
ln ling:narrative_discourse ont.narrative @related_to
ln ling:narrative_discourse phil:narrative @extends
set.add name="ontology.linguistics" id="ling:narrative_discourse"

def "ling:polysemy" "Condition where one word possesses multiple related meanings."
ln ling:polysemy ling.semantics sys:is_a
ln ling:polysemy phil:ambiguity @related_to
ln ling:polysemy phil:ambiguity @extends
set.add name="ontology.linguistics" id="ling:polysemy"

def "ling:recursion" "Self-embedding structure enabling infinite generative language."
ln ling:recursion ling.syntax sys:is_a
ln ling:recursion quote:deutsch_recurse @referenced_by
set.add name="ontology.linguistics" id="ling:recursion"

def "ling:reference" "Relation between language and entities in the world."
ln ling:reference ling.semantics sys:is_a
ln ling:reference phil:reference sys:same_as
set.add name="ontology.linguistics" id="ling:reference"

def "ling:register" "Variation in language according to social context or purpose."
ln ling:register ling.discourse sys:is_a
ln ling:register biz:segment @adjusts_for
set.add name="ontology.linguistics" id="ling:register"

def "ling:rhetoric" "Strategic use of language to persuade or influence."
ln ling:rhetoric ling.discourse sys:is_a
ln ling:rhetoric biz:value_proposition @supports
set.add name="ontology.linguistics" id="ling:rhetoric"

def "ling:root_word" "Core morpheme carrying primary semantic meaning."
ln ling:root_word ling.morphology sys:is_a
set.add name="ontology.linguistics" id="ling:root_word"

def "ling:sentence" "Structured linguistic unit expressing a complete thought."
ln ling:sentence ling.syntax sys:is_a
set.add name="ontology.linguistics" id="ling:sentence"

def "ling:sign" "Entity representing meaning beyond itself."
ln ling:sign ling.semiotics sys:is_a
ln ling:sign phil:symbol @related_to
set.add name="ontology.linguistics" id="ling:sign"

def "ling:signified" "Concept represented by a signifier."
ln ling:signified ling.semiotics sys:is_a
ln ling:signified ling:meaning @contains
set.add name="ontology.linguistics" id="ling:signified"

def "ling:signifier" "Material form of a sign such as sound or written mark."
ln ling:signifier ling.semiotics sys:is_a
set.add name="ontology.linguistics" id="ling:signifier"

def "ling:speech_act" "Utterance performing an action such as promising or commanding."
ln ling:speech_act ling.pragmatics sys:is_a
ln ling:speech_act ling:utterance @depends_on
ln ling:speech_act civ:briefing @can_manifest_as
set.add name="ontology.linguistics" id="ling:speech_act"

def "ling:structure" "Arrangement and relationship of linguistic elements."
ln ling:structure ling.syntax sys:is_a
set.add name="ontology.linguistics" id="ling:structure"

def "ling:symbolic_meaning" "Meaning carried through symbolic association."
ln ling:symbolic_meaning ling.semantics sys:is_a
ln ling:symbolic_meaning phil:symbolism @related_to
set.add name="ontology.linguistics" id="ling:symbolic_meaning"

def "ling:utterance" "Concrete act of speaking or expression in context."
ln ling:utterance ling.pragmatics sys:is_a
set.add name="ontology.linguistics" id="ling:utterance"

def "ling:word" "Minimal meaningful linguistic unit."
ln ling:word ling.morphology sys:is_a
set.add name="ontology.linguistics" id="ling:word"
