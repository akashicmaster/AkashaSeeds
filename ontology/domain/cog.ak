# Akasha ontology — namespace: cog
# atoms: 29

def "cog:anchoring" "Overreliance on initial information when judging."
ln cog:anchoring cognition.bias sys:is_a
ln cog:anchoring meta:ambiguity @distorts
set.add name="ontology.cognition" id="cog:anchoring"

def "cog:attachment" "Emotionally persistent bond toward people, ideas, or identities."
ln cog:attachment cognition.emotion sys:is_a
set.add name="ontology.cognition" id="cog:attachment"

def "cog:availability_bias" "Overweighting information that is recent or vivid."
ln cog:availability_bias cognition.bias sys:is_a
ln cog:availability_bias meta:noise @amplifies
set.add name="ontology.cognition" id="cog:availability_bias"

def "cog:avoidance" "Cognitive or behavioral movement away from discomfort or threat."
ln cog:avoidance cognition.emotion sys:is_a
set.add name="ontology.cognition" id="cog:avoidance"

def "cog:cognitive_dissonance" "Mental tension caused by conflicting beliefs or actions."
ln cog:cognitive_dissonance cognition.bias sys:is_a
ln cog:cognitive_dissonance cog:denial @may_cause
set.add name="ontology.cognition" id="cog:cognitive_dissonance"

def "cog:confirmation_bias" "Tendency to favor information supporting existing beliefs."
ln cog:confirmation_bias cognition.bias sys:is_a
ln cog:confirmation_bias meta:bias sys:same_as
set.add name="ontology.cognition" id="cog:confirmation_bias"

def "cog:curiosity" "Exploratory drive toward uncertainty or novelty."
ln cog:curiosity cognition.attention sys:is_a
ln cog:curiosity emo:curiosity sys:same_as
set.add name="ontology.cognition" id="cog:curiosity"

def "cog:deliberation" "Reflective comparison of alternatives."
ln cog:deliberation cognition.decision sys:is_a
ln cog:deliberation phil:skepticism @supports
set.add name="ontology.cognition" id="cog:deliberation"

def "cog:denial" "Refusal to acknowledge threatening or dissonant information."
ln cog:denial cognition.selfhood sys:is_a
set.add name="ontology.cognition" id="cog:denial"

def "cog:desire" "Motivational pull toward wanted outcomes."
ln cog:desire cognition.emotion sys:is_a
set.add name="ontology.cognition" id="cog:desire"

def "cog:distraction" "Redirection of attention away from intended focus."
ln cog:distraction cognition.attention sys:is_a
set.add name="ontology.cognition" id="cog:distraction"

def "cog:ego" "Organizing center of identity and self-reference."
ln cog:ego cognition.selfhood sys:is_a
set.add name="ontology.cognition" id="cog:ego"

def "cog:fear_response" "Threat-oriented cognitive and physiological reaction."
ln cog:fear_response cognition.emotion sys:is_a
ln cog:fear_response emo:fear @related_to
set.add name="ontology.cognition" id="cog:fear_response"

def "cog:focus" "Sustained concentration on a target or task."
ln cog:focus cognition.attention sys:is_a
ln cog:focus cog:distraction @contrasts_with
ln cog:focus cockpit:focus @supports
set.add name="ontology.cognition" id="cog:focus"

def "cog:forgetting" "Loss or weakening of memory accessibility."
ln cog:forgetting cognition.memory sys:is_a
set.add name="ontology.cognition" id="cog:forgetting"

def "cog:framing_effect" "Decision distortion caused by presentation style."
ln cog:framing_effect cognition.bias sys:is_a
set.add name="ontology.cognition" id="cog:framing_effect"

def "cog:hypervigilance" "Persistent heightened scanning for threat or anomaly."
ln cog:hypervigilance cognition.attention sys:is_a
ln cog:hypervigilance cog:risk_assessment @intensifies
set.add name="ontology.cognition" id="cog:hypervigilance"

def "cog:interpretation" "Construction of meaning from sensory or symbolic input."
ln cog:interpretation cognition.perception sys:is_a
set.add name="ontology.cognition" id="cog:interpretation"

def "cog:intuition" "Rapid non-explicit understanding or recognition."
ln cog:intuition cognition.decision sys:is_a
ln cog:intuition phil:belief @supports
set.add name="ontology.cognition" id="cog:intuition"

def "cog:judgment" "Evaluation leading toward conclusion or action."
ln cog:judgment cognition.decision sys:is_a
ln cog:judgment phil:reason @uses
set.add name="ontology.cognition" id="cog:judgment"

def "cog:narrative_identity" "Identity constructed through remembered and interpreted life stories."
ln cog:narrative_identity cognition.selfhood sys:is_a
ln cog:narrative_identity nar:rebirth @associated_with
ln cog:narrative_identity nar:tragedy @associated_with
set.add name="ontology.cognition" id="cog:narrative_identity"

def "cog:nostalgia" "Emotionally charged reconstruction of the past."
ln cog:nostalgia cognition.memory sys:is_a
ln cog:nostalgia emo:nostalgia sys:same_as
set.add name="ontology.cognition" id="cog:nostalgia"

def "cog:pattern_recognition" "Detection of meaningful regularities or structures."
ln cog:pattern_recognition cognition.perception sys:is_a
ln cog:pattern_recognition cog:interpretation @supports
set.add name="ontology.cognition" id="cog:pattern_recognition"

def "cog:projection" "Attributing internal states or assumptions onto external reality."
ln cog:projection cognition.perception sys:is_a
ln cog:projection cognition.bias @may_cause
set.add name="ontology.cognition" id="cog:projection"

def "cog:recall" "Retrieval of stored memories or knowledge."
ln cog:recall cognition.memory sys:is_a
set.add name="ontology.cognition" id="cog:recall"

def "cog:reconstruction" "Reassembly of memory influenced by interpretation and context."
ln cog:reconstruction cognition.memory sys:is_a
ln cog:reconstruction cog:narrative_identity @supports
set.add name="ontology.cognition" id="cog:reconstruction"

def "cog:risk_assessment" "Evaluation of uncertainty, danger, or potential loss."
ln cog:risk_assessment cognition.decision sys:is_a
set.add name="ontology.cognition" id="cog:risk_assessment"

def "cog:salience" "Perceived importance or prominence of stimuli."
ln cog:salience cognition.perception sys:is_a
ln cog:salience pres:highlight @related_to
set.add name="ontology.cognition" id="cog:salience"

def "cog:self_image" "Internal representation of oneself."
ln cog:self_image cognition.selfhood sys:is_a
set.add name="ontology.cognition" id="cog:self_image"
