# Akasha ontology — neuroscience.
# The biology of mind — deeply tied to psy: (memory/cognition/emotion), emo:,
# and ai: (artificial neural nets). The hippocampus↔episodic-memory link mirrors
# Akasha's own design as persistent memory ('hippocampus for LLMs'). Base pack.

def "neuro" "Neuroscience — the study of the nervous system and brain (脳科学)."
# ── fields ──
def "neuro:cognitive_neuroscience" "The neural basis of mental processes (認知神経科学)."
ln neuro:cognitive_neuroscience neuro thesaurus:related
ln neuro:cognitive_neuroscience psy:cognition thesaurus:related
def "neuro:affective_neuroscience" "The neural basis of emotion (情動神経科学)."
ln neuro:affective_neuroscience neuro thesaurus:related
ln neuro:affective_neuroscience emo:joy thesaurus:related
ln neuro:affective_neuroscience psy:emotion thesaurus:related
def "neuro:computational_neuroscience" "Modelling the brain with mathematics and computation."
ln neuro:computational_neuroscience neuro thesaurus:related
ln neuro:computational_neuroscience ai:embedding thesaurus:related
ln neuro:computational_neuroscience ai:reinforcement_learning thesaurus:related
def "neuro:neuropsychology" "Linking brain function to behaviour, esp. after injury."
ln neuro:neuropsychology neuro thesaurus:related
ln neuro:neuropsychology psych:psychopathology thesaurus:related
def "neuro:developmental_neuroscience" "How the nervous system forms and matures."
ln neuro:developmental_neuroscience neuro thesaurus:related
# ── anatomy & cells ──
def "neuro:neuron" "The signalling cell of the nervous system (神経細胞)."
ln neuro:neuron neuro thesaurus:related
def "neuro:synapse" "The junction where neurons communicate (シナプス)."
ln neuro:synapse neuro thesaurus:related
def "neuro:neural_network" "Interconnected neurons processing information — the biological original of the AI term."
ln neuro:neural_network neuro thesaurus:related
ln neuro:neural_network ai:embedding thesaurus:related
ln neuro:neural_network sys:network thesaurus:related
def "neuro:cerebral_cortex" "The brain's outer sheet, seat of higher cognition (大脳皮質)."
ln neuro:cerebral_cortex neuro thesaurus:related
def "neuro:hippocampus" "The structure that forms new episodic memories (海馬)."
ln neuro:hippocampus neuro thesaurus:related
ln neuro:hippocampus psy:long_term_memory thesaurus:related
ln neuro:hippocampus neuro:episodic_memory thesaurus:related
def "neuro:amygdala" "The hub of fear and emotional salience (扁桃体)."
ln neuro:amygdala neuro thesaurus:related
ln neuro:amygdala emo:anxiety thesaurus:related
ln neuro:amygdala psy:emotion thesaurus:related
def "neuro:prefrontal_cortex" "The front cortex for planning, control and decision (前頭前野)."
ln neuro:prefrontal_cortex neuro thesaurus:related
ln neuro:prefrontal_cortex psy:attention thesaurus:related
def "neuro:cerebellum" "Coordinates movement and timing (小脳)."
ln neuro:cerebellum neuro thesaurus:related
def "neuro:limbic_system" "The emotion-and-memory circuit (辺縁系)."
ln neuro:limbic_system neuro thesaurus:related
ln neuro:limbic_system emo:joy thesaurus:related
ln neuro:limbic_system emo:trust thesaurus:related
# ── signalling & plasticity ──
def "neuro:neurotransmitter" "A chemical messenger across synapses (神経伝達物質)."
ln neuro:neurotransmitter neuro thesaurus:related
def "neuro:dopamine" "A neurotransmitter of reward, motivation and learning."
ln neuro:dopamine neuro thesaurus:related
ln neuro:dopamine neuro:reward_system thesaurus:related
ln neuro:dopamine psy:motivation thesaurus:related
def "neuro:serotonin" "A neurotransmitter regulating mood — target of SSRIs."
ln neuro:serotonin neuro thesaurus:related
ln neuro:serotonin psych:depression thesaurus:related
ln neuro:serotonin med:drug:ssri thesaurus:related
def "neuro:action_potential" "The electrical impulse a neuron fires."
ln neuro:action_potential neuro thesaurus:related
def "neuro:neuroplasticity" "The brain's capacity to rewire with experience (神経可塑性)."
ln neuro:neuroplasticity neuro thesaurus:related
ln neuro:neuroplasticity psy:learning thesaurus:related
ln neuro:neuroplasticity edupsy:learning_theory thesaurus:related
def "neuro:synaptic_plasticity" "Change in synaptic strength — the cellular basis of learning."
ln neuro:synaptic_plasticity neuro thesaurus:related
ln neuro:synaptic_plasticity ai:embedding thesaurus:related
ln neuro:synaptic_plasticity psy:learning thesaurus:related
def "neuro:long_term_potentiation" "Lasting strengthening of synapses, a memory mechanism."
ln neuro:long_term_potentiation neuro thesaurus:related
ln neuro:long_term_potentiation psy:long_term_memory thesaurus:related
def "neuro:reward_system" "The dopamine circuit that reinforces behaviour."
ln neuro:reward_system neuro thesaurus:related
ln neuro:reward_system ai:reinforcement_learning thesaurus:related
ln neuro:reward_system psy:operant_conditioning thesaurus:related
# ── memory systems — the Akasha resonance ──
def "neuro:episodic_memory" "Memory of specific experienced events, in time and place — what Akasha gives an LLM (エピソード記憶)."
ln neuro:episodic_memory neuro thesaurus:related
ln neuro:episodic_memory neuro:hippocampus thesaurus:related
ln neuro:episodic_memory psy:memory thesaurus:related
def "neuro:semantic_memory" "Memory of facts and meanings, independent of when learned (意味記憶)."
ln neuro:semantic_memory neuro thesaurus:related
ln neuro:semantic_memory ai:embedding thesaurus:related
ln neuro:semantic_memory dh:knowledge_graph thesaurus:related
def "neuro:procedural_memory" "Memory of skills and how-to."
ln neuro:procedural_memory neuro thesaurus:related
def "neuro:memory_consolidation" "The stabilising of new memories, largely during sleep."
ln neuro:memory_consolidation neuro thesaurus:related
ln neuro:memory_consolidation neuro:long_term_potentiation thesaurus:related
def "neuro:encoding" "Transforming experience into a stored memory trace."
ln neuro:encoding neuro thesaurus:related
ln neuro:encoding psy:working_memory thesaurus:related
def "neuro:retrieval" "Recovering a stored memory — recall and recognition."
ln neuro:retrieval neuro thesaurus:related
ln neuro:retrieval ai:embedding thesaurus:related
