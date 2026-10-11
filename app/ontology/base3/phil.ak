# Akasha ontology — namespace: phil
# atoms: 63

def "phil:abduction" "Inference toward the most plausible explanation."
ln phil:abduction philosophy.logic sys:is_a
ln phil:abduction mystery @supports
set.add name="ontology.philosophy" id="phil:abduction"

def "phil:actuality" "State of realized existence or fulfilled potential."
ln phil:actuality philosophy.metaphysics sys:is_a
ln phil:actuality phil:potentiality @fulfills
ln phil:actuality phil:being @realizes
set.add name="ontology.philosophy" id="phil:actuality"

def "phil:ambiguity" "Condition of having multiple possible meanings."
ln phil:ambiguity philosophy.language sys:is_a
ln phil:ambiguity phil:meaning @complicates
ln phil:ambiguity phil:interpretation @requires
set.add name="ontology.philosophy" id="phil:ambiguity"

def "phil:antithesis" "Opposing proposition challenging a thesis."
ln phil:antithesis philosophy.dialectics sys:is_a
ln phil:antithesis phil:thesis @contradicts
set.add name="ontology.philosophy" id="phil:antithesis"

def "phil:authority" "Legitimate power or recognized right to govern."
ln phil:authority philosophy.politics sys:is_a
ln phil:authority civ:policy @enables
set.add name="ontology.philosophy" id="phil:authority"

def "phil:becoming" "Process of change and transformation through time."
ln phil:becoming philosophy.metaphysics sys:is_a
ln phil:becoming phil:being @contrasts_with
set.add name="ontology.philosophy" id="phil:becoming"

def "phil:being" "Existence considered in its most fundamental sense."
ln phil:being philosophy.metaphysics sys:is_a
set.add name="ontology.philosophy" id="phil:being"

def "phil:belief" "Acceptance that a proposition is true or meaningful."
ln phil:belief philosophy.epistemology sys:is_a
ln phil:belief believe @related_to
set.add name="ontology.philosophy" id="phil:belief"

def "phil:causality" "The relation between causes and effects."
ln phil:causality philosophy.metaphysics sys:is_a
ln phil:causality cause @related_to
ln phil:causality effect @related_to
ln phil:causality phil:determinism @supports
set.add name="ontology.philosophy" id="phil:causality"

def "phil:conclusion" "Statement derived from premises through inference."
ln phil:conclusion philosophy.logic sys:is_a
set.add name="ontology.philosophy" id="phil:conclusion"

def "phil:consciousness" "Awareness of experience, self, or existence."
ln phil:consciousness philosophy.mind sys:is_a
set.add name="ontology.philosophy" id="phil:consciousness"

def "phil:consistency" "Absence of contradiction within a system or argument."
ln phil:consistency philosophy.logic sys:is_a
ln phil:consistency phil:contradiction @contrasts_with
set.add name="ontology.philosophy" id="phil:consistency"

def "phil:context" "Surrounding conditions that shape meaning and understanding."
ln phil:context philosophy.hermeneutics sys:is_a
ln phil:context phil:interpretation @influences
set.add name="ontology.philosophy" id="phil:context"

def "phil:contingency" "Condition of depending on circumstances rather than necessity."
ln phil:contingency philosophy.logic sys:is_a
ln phil:contingency phil:necessity @contrasts_with
ln phil:contingency phil:fate @contrasts_with
set.add name="ontology.philosophy" id="phil:contingency"

def "phil:contradiction" "Mutual incompatibility between propositions."
ln phil:contradiction philosophy.logic sys:is_a
ln phil:contradiction order @threatens
set.add name="ontology.philosophy" id="phil:contradiction"

def "phil:deduction" "Reasoning from general principles toward necessary conclusions."
ln phil:deduction philosophy.logic sys:is_a
ln phil:deduction phil:necessity @supports
set.add name="ontology.philosophy" id="phil:deduction"

def "phil:desire" "Motivational attraction toward an object or outcome."
ln phil:desire philosophy.ethics sys:is_a
ln phil:desire phil:freedom @motivates
ln phil:desire nar:quest @motivates
set.add name="ontology.philosophy" id="phil:desire"

def "phil:determinism" "The doctrine that events are fixed by prior causes."
ln phil:determinism philosophy.metaphysics sys:is_a
set.add name="ontology.philosophy" id="phil:determinism"

def "phil:difference" "Distinction or non-identity between entities or concepts."
ln phil:difference philosophy.metaphysics sys:is_a
ln phil:difference phil:identity @contrasts_with
set.add name="ontology.philosophy" id="phil:difference"

def "phil:discourse" "Structured field of language, concepts, and communicative practice."
ln phil:discourse philosophy.hermeneutics sys:is_a
ln phil:discourse civ:comment @related_to
set.add name="ontology.philosophy" id="phil:discourse"

def "phil:doubt" "Suspension of certainty or confidence."
ln phil:doubt philosophy.epistemology sys:is_a
ln phil:doubt doubt sys:same_as
set.add name="ontology.philosophy" id="phil:doubt"

def "phil:emergence" "Appearance of higher-order structure from interacting components."
ln phil:emergence philosophy.metaphysics sys:is_a
ln phil:emergence complex @related_to
ln phil:emergence complexity @related_to
set.add name="ontology.philosophy" id="phil:emergence"

def "phil:essence" "Intrinsic nature that makes a thing what it is."
ln phil:essence philosophy.metaphysics sys:is_a
set.add name="ontology.philosophy" id="phil:essence"

def "phil:evidence" "Grounds supporting belief or justification."
ln phil:evidence philosophy.epistemology sys:is_a
set.add name="ontology.philosophy" id="phil:evidence"

def "phil:fallacy" "Pattern of reasoning that appears valid but contains an error."
ln phil:fallacy philosophy.logic sys:is_a
ln phil:fallacy phil:validity @threatens
set.add name="ontology.philosophy" id="phil:fallacy"

def "phil:fate" "The idea that events are pre-determined or destined."
ln phil:fate philosophy.metaphysics sys:is_a
ln phil:fate phil:determinism @related_to
ln phil:fate nar:tragedy @associated_with
set.add name="ontology.philosophy" id="phil:fate"

def "phil:freedom" "Capacity for self-directed action."
ln phil:freedom philosophy.ethics sys:is_a
set.add name="ontology.philosophy" id="phil:freedom"

def "phil:identity" "The continuity of a thing as itself through change."
ln phil:identity philosophy.metaphysics sys:is_a
ln phil:identity phil:selfhood @related_to
ln phil:identity nar:rebirth @related_to
set.add name="ontology.philosophy" id="phil:identity"

def "phil:induction" "Reasoning from observations toward generalized patterns."
ln phil:induction philosophy.logic sys:is_a
ln phil:induction phil:possibility @supports
set.add name="ontology.philosophy" id="phil:induction"

def "phil:inference" "Process of deriving conclusions from premises."
ln phil:inference philosophy.logic sys:is_a
ln phil:inference phil:premise @depends_on
ln phil:inference phil:conclusion @produces
set.add name="ontology.philosophy" id="phil:inference"

def "phil:intentionality" "Directedness of consciousness toward objects, meanings, or states."
ln phil:intentionality philosophy.mind sys:is_a
ln phil:intentionality phil:consciousness @depends_on
ln phil:intentionality phil:meaning @directs_toward
set.add name="ontology.philosophy" id="phil:intentionality"

def "phil:interpretation" "Act of constructing meaning from a text, symbol, or event."
ln phil:interpretation philosophy.hermeneutics sys:is_a
ln phil:interpretation phil:meaning @constructs
ln phil:interpretation phil:symbol @decodes
set.add name="ontology.philosophy" id="phil:interpretation"

def "phil:justice" "Fairness and rightful order."
ln phil:justice philosophy.ethics sys:is_a
ln phil:justice civ:fairness @related_to
set.add name="ontology.philosophy" id="phil:justice"

def "phil:knowledge" "Justified understanding or awareness."
ln phil:knowledge philosophy.epistemology sys:is_a
set.add name="ontology.philosophy" id="phil:knowledge"

def "phil:legitimacy" "Justified rightfulness of rule or order."
ln phil:legitimacy philosophy.politics sys:is_a
ln phil:legitimacy civ:trust @depends_on
set.add name="ontology.philosophy" id="phil:legitimacy"

def "phil:liberty" "Freedom from coercive constraint."
ln phil:liberty philosophy.politics sys:is_a
set.add name="ontology.philosophy" id="phil:liberty"

def "phil:meaning" "Semantic or conceptual content communicated by signs or language."
ln phil:meaning philosophy.language sys:is_a
ln phil:meaning phil:symbol @depends_on
set.add name="ontology.philosophy" id="phil:meaning"

def "phil:memory" "Retention and recall of experience."
ln phil:memory philosophy.mind sys:is_a
ln phil:memory phil:identity @supports
set.add name="ontology.philosophy" id="phil:memory"

def "phil:narrative" "Meaningful sequence organizing events, identities, or explanations."
ln phil:narrative philosophy.hermeneutics sys:is_a
ln phil:narrative ont.narrative @related_to
ln phil:narrative plot:tragedy @can_contain
set.add name="ontology.philosophy" id="phil:narrative"

def "phil:necessity" "Condition of being unavoidable or logically required."
ln phil:necessity philosophy.logic sys:is_a
ln phil:necessity phil:possibility @contrasts_with
set.add name="ontology.philosophy" id="phil:necessity"

def "phil:object" "Entity toward which consciousness or thought is directed."
ln phil:object philosophy.mind sys:is_a
ln phil:object phil:subject @contrasts_with
set.add name="ontology.philosophy" id="phil:object"

def "phil:ontology" "The philosophical study of what exists."
ln phil:ontology philosophy.metaphysics sys:is_a
ln phil:ontology sys:schema @contrasts_with
set.add name="ontology.philosophy" id="phil:ontology"

def "phil:paradox" "Statement or structure that produces self-conflicting implications."
ln phil:paradox philosophy.logic sys:is_a
ln phil:paradox phil:contradiction @related_to
ln phil:paradox phil:truth @threatens
set.add name="ontology.philosophy" id="phil:paradox"

def "phil:perception" "Interpretation of sensory experience."
ln phil:perception philosophy.mind sys:is_a
set.add name="ontology.philosophy" id="phil:perception"

def "phil:phenomenon" "Thing as experienced or perceived in consciousness."
ln phil:phenomenon philosophy.mind sys:is_a
ln phil:phenomenon phil:interpretation @requires
set.add name="ontology.philosophy" id="phil:phenomenon"

def "phil:possibility" "Condition of being able to exist, occur, or become actual."
ln phil:possibility philosophy.logic sys:is_a
set.add name="ontology.philosophy" id="phil:possibility"

def "phil:potentiality" "Capacity to become or develop into a future state."
ln phil:potentiality philosophy.metaphysics sys:is_a
set.add name="ontology.philosophy" id="phil:potentiality"

def "phil:premise" "Statement assumed as the basis of an argument."
ln phil:premise philosophy.logic sys:is_a
set.add name="ontology.philosophy" id="phil:premise"

def "phil:reason" "Logical inference and rational thought."
ln phil:reason philosophy.epistemology sys:is_a
ln phil:reason sys:abstraction @supports
set.add name="ontology.philosophy" id="phil:reason"

def "phil:reference" "Relation between language and what it points to."
ln phil:reference philosophy.language sys:is_a
ln phil:reference phil:truth @supports
set.add name="ontology.philosophy" id="phil:reference"

def "phil:responsibility" "Accountability for actions and consequences."
ln phil:responsibility philosophy.ethics sys:is_a
ln phil:responsibility phil:freedom @depends_on
set.add name="ontology.philosophy" id="phil:responsibility"

def "phil:selfhood" "The condition of being a self."
ln phil:selfhood philosophy.mind sys:is_a
set.add name="ontology.philosophy" id="phil:selfhood"

def "phil:skepticism" "Philosophical position emphasizing doubt and critical inquiry."
ln phil:skepticism philosophy.epistemology sys:is_a
ln phil:skepticism phil:doubt @supports
ln phil:skepticism phil:knowledge @questions
set.add name="ontology.philosophy" id="phil:skepticism"

def "phil:subject" "Experiencing or perceiving self."
ln phil:subject philosophy.mind sys:is_a
set.add name="ontology.philosophy" id="phil:subject"

def "phil:symbol" "Sign representing something beyond itself."
ln phil:symbol philosophy.language sys:is_a
set.add name="ontology.philosophy" id="phil:symbol"

def "phil:symbolism" "Layered meaning expressed through symbolic representation."
ln phil:symbolism philosophy.hermeneutics sys:is_a
ln phil:symbolism phil:symbol @depends_on
ln phil:symbolism fnty:mana_ether @interprets
set.add name="ontology.philosophy" id="phil:symbolism"

def "phil:synthesis" "Higher-order reconciliation of contradiction."
ln phil:synthesis philosophy.dialectics sys:is_a
ln phil:synthesis phil:thesis @integrates
ln phil:synthesis phil:antithesis @integrates
ln phil:synthesis phil:contradiction @resolves
set.add name="ontology.philosophy" id="phil:synthesis"

def "phil:temporality" "Structure of time as experienced or conceptualized."
ln phil:temporality philosophy.metaphysics sys:is_a
ln phil:temporality past @related_to
ln phil:temporality future @related_to
ln phil:temporality phil:memory @shapes
set.add name="ontology.philosophy" id="phil:temporality"

def "phil:text" "Structured expression interpreted by readers or observers."
ln phil:text philosophy.hermeneutics sys:is_a
set.add name="ontology.philosophy" id="phil:text"

def "phil:thesis" "Initial proposition or conceptual position."
ln phil:thesis philosophy.dialectics sys:is_a
set.add name="ontology.philosophy" id="phil:thesis"

def "phil:truth" "Condition of correspondence with reality or coherence within a system."
ln phil:truth philosophy.epistemology sys:is_a
ln phil:truth truth sys:same_as
ln phil:truth phil:meaning @depends_on
ln phil:truth phil:belief @contrasts_with
set.add name="ontology.philosophy" id="phil:truth"

def "phil:validity" "Property of an argument whose conclusion follows logically from its premises."
ln phil:validity philosophy.logic sys:is_a
set.add name="ontology.philosophy" id="phil:validity"

def "phil:virtue" "Moral excellence expressed in character and action."
ln phil:virtue philosophy.ethics sys:is_a
set.add name="ontology.philosophy" id="phil:virtue"
