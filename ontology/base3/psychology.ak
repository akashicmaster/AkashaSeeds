# Akasha ontology — psychology (心理学), the general discipline.
# The broad science of mind and behaviour, cross-linked to its clinical branch
# (psych:/counsel:), the affect layer (emo:), machine learning (ai:), and
# education (edupsy:). Base pack.

def "psy" "Psychology — the science of mind and behaviour (心理学)."
# ── branches ──
def "psy:cognitive_psychology" "The study of mental processes — perception, memory, thought (認知心理学)."
ln psy:cognitive_psychology psy thesaurus:related
def "psy:developmental_psychology" "How mind and behaviour change across the lifespan (発達心理学)."
ln psy:developmental_psychology psy thesaurus:related
ln psy:developmental_psychology kin:child_of thesaurus:related
ln psy:developmental_psychology school:student thesaurus:related
ln psy:developmental_psychology psych thesaurus:related
def "psy:social_psychology" "How others shape our thoughts, feelings and behaviour (社会心理学)."
ln psy:social_psychology psy thesaurus:related
ln psy:social_psychology socio:social_interaction thesaurus:related
ln psy:social_psychology socio:in_group thesaurus:related
def "psy:behavioral_psychology" "The study of learned behaviour and conditioning (行動心理学)."
ln psy:behavioral_psychology psy thesaurus:related
ln psy:behavioral_psychology ai:reinforcement_learning thesaurus:related
def "psy:personality_psychology" "The study of stable individual differences (性格心理学)."
ln psy:personality_psychology psy thesaurus:related
def "psy:biopsychology" "The biological bases of behaviour (生理心理学)."
ln psy:biopsychology psy thesaurus:related
# ── core concepts ──
def "psy:memory" "The encoding, storage and retrieval of information (記憶)."
ln psy:memory psy thesaurus:related
ln psy:memory ai:embedding thesaurus:related
def "psy:working_memory" "The small store holding information in active use."
ln psy:working_memory psy thesaurus:related
def "psy:long_term_memory" "The durable store of knowledge and experience."
ln psy:long_term_memory psy thesaurus:related
ln psy:long_term_memory ai:embedding thesaurus:related
def "psy:attention" "The selective focusing of mental resources (注意)."
ln psy:attention psy thesaurus:related
def "psy:perception" "Organising and interpreting sensory input (知覚)."
ln psy:perception psy thesaurus:related
ln psy:perception sensory:flavor_perception thesaurus:related
def "psy:cognition" "The mental processes of knowing (認知)."
ln psy:cognition psy thesaurus:related
def "psy:learning" "A lasting change in behaviour or knowledge from experience (学習)."
ln psy:learning psy thesaurus:related
ln psy:learning ai:supervised_learning thesaurus:related
ln psy:learning edupsy:learning_theory thesaurus:related
def "psy:intelligence" "The capacity to learn, reason and solve problems (知能)."
ln psy:intelligence psy thesaurus:related
def "psy:emotion" "A patterned affective response of feeling, body and expression (情動)."
ln psy:emotion psy thesaurus:related
ln psy:emotion emo:joy thesaurus:related
ln psy:emotion emo:trust thesaurus:related
ln psy:emotion emo:anxiety thesaurus:related
def "psy:motivation" "What energises and directs behaviour (動機づけ)."
ln psy:motivation psy thesaurus:related
ln psy:motivation org:intrinsic_motivation thesaurus:related
ln psy:motivation org:extrinsic_motivation thesaurus:related
def "psy:conditioning" "Learning associations between stimuli and responses."
ln psy:conditioning psy thesaurus:related
def "psy:classical_conditioning" "Pavlovian learning of stimulus associations."
ln psy:classical_conditioning psy thesaurus:related
def "psy:operant_conditioning" "Skinner's learning by reinforcement and punishment."
ln psy:operant_conditioning psy thesaurus:related
ln psy:operant_conditioning ai:reinforcement_learning thesaurus:related
def "psy:cognitive_bias" "Systematic deviations from rational judgement."
ln psy:cognitive_bias psy thesaurus:related
def "psy:consciousness" "Subjective awareness of self and world (意識)."
ln psy:consciousness psy thesaurus:related
ln psy:consciousness phil:identity thesaurus:related
# ── theorists & theories ──
def "psy:piaget_stages" "Piaget's stages of cognitive development in children."
ln psy:piaget_stages psy thesaurus:related
ln psy:piaget_stages psy:developmental_psychology thesaurus:related
ln psy:piaget_stages kin:child_of thesaurus:related
def "psy:vygotsky_sociocultural" "Vygotsky's view that learning is social and mediated by culture."
ln psy:vygotsky_sociocultural psy thesaurus:related
ln psy:vygotsky_sociocultural edupsy:zone_of_proximal_development thesaurus:related
ln psy:vygotsky_sociocultural socio:socialization thesaurus:related
def "psy:skinner_operant" "Skinner's account of behaviour shaped by consequences."
ln psy:skinner_operant psy thesaurus:related
ln psy:skinner_operant psy:operant_conditioning thesaurus:related
def "psy:maslow_hierarchy" "Maslow's hierarchy from physiological needs to self-actualisation."
ln psy:maslow_hierarchy psy thesaurus:related
ln psy:maslow_hierarchy org:intrinsic_motivation thesaurus:related
def "psy:bandura_social_learning" "Bandura's theory of learning by observation and modelling."
ln psy:bandura_social_learning psy thesaurus:related
ln psy:bandura_social_learning edupsy:self_efficacy thesaurus:related
def "psy:big_five" "The five-factor model of personality (OCEAN)."
ln psy:big_five psy thesaurus:related
ln psych psy thesaurus:related
