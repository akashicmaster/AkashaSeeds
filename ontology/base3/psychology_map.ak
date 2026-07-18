# Akasha ontology — psychology: a broad general-education-level map.
# Subfields + schools + founders + broadened core concepts, with the scattered
# psy:/cog:/devpsy:/edupsy:/counsel:/psych:/neuro:/emo: atoms cross-linked under it.
# General-education breadth; research depth is reserved for level-C packs. Base pack.

# psy (top) and person:figure already exist — do not re-define.
def "person:field:psychology" "Psychology — the field of those who study mind and behaviour."
ln person:field:psychology person:figure thesaurus:related
ln person:field:psychology psy thesaurus:related
ln psy knowledge:branch:social_science knowledge:in_branch
ln psy knowledge:cognitive_science thesaurus:related

# ══ subfields (psy:field:*) ══
def "psy:field:cognitive" "認知心理学 — mental processes: perception, attention, memory, thought, language."
ln psy:field:cognitive psy sys:part_of
ln psy:cognition psy:field:cognitive sys:part_of
ln psy:cognitive_psychology psy:field:cognitive sys:part_of
ln psy:attention psy:field:cognitive sys:part_of
ln psy:perception psy:field:cognitive sys:part_of
ln psy:memory psy:field:cognitive sys:part_of
ln psy:working_memory psy:field:cognitive sys:part_of
ln psy:long_term_memory psy:field:cognitive sys:part_of
ln psy:learning psy:field:cognitive sys:part_of
ln psy:cognitive_bias psy:field:cognitive sys:part_of
ln psy:consciousness psy:field:cognitive sys:part_of
ln psy:intelligence psy:field:cognitive sys:part_of
ln psy:field:cognitive cog:pattern_recognition thesaurus:related
ln psy:field:cognitive neuro:cognitive_neuroscience thesaurus:related
ln psy:field:cognitive knowledge:cognitive_science thesaurus:related
def "psy:field:developmental" "発達心理学 — how mind and behaviour change across the lifespan."
ln psy:field:developmental psy sys:part_of
ln psy:developmental_psychology psy:field:developmental sys:part_of
ln psy:piaget_stages psy:field:developmental sys:part_of
ln psy:vygotsky_sociocultural psy:field:developmental sys:part_of
ln psy:field:developmental devpsy:attachment thesaurus:related
ln psy:field:developmental devpsy:erikson_stages thesaurus:related
def "psy:field:social" "社会心理学 — how people think about, influence and relate to one another."
ln psy:field:social psy sys:part_of
ln psy:social_psychology psy:field:social sys:part_of
ln psy:bandura_social_learning psy:field:social sys:part_of
ln psy:field:social cog:cognitive_dissonance thesaurus:related
ln psy:field:social socio:social_interaction thesaurus:related
def "psy:field:personality" "人格心理学 — the enduring patterns that make each person distinctive."
ln psy:field:personality psy sys:part_of
ln psy:personality_psychology psy:field:personality sys:part_of
ln psy:big_five psy:field:personality sys:part_of
ln psy:maslow_hierarchy psy:field:personality sys:part_of
def "psy:field:biological" "生物心理学 — the biological bases of behaviour: brain, neurons, hormones, genes."
ln psy:field:biological psy sys:part_of
ln psy:biopsychology psy:field:biological sys:part_of
ln psy:field:biological neuro:neuron thesaurus:related
ln psy:field:biological neuro:neurotransmitter thesaurus:related
ln psy:field:biological neuro:limbic_system thesaurus:related
ln psy:field:biological bio:branch:physiology thesaurus:related
def "psy:field:clinical" "臨床心理学 — assessing and treating mental disorders and distress."
ln psy:field:clinical psy sys:part_of
ln psych:clinical_psychology psy:field:clinical sys:part_of
ln psych:psychopathology psy:field:clinical sys:part_of
ln psych:mental_health psy:field:clinical sys:part_of
ln psych:diagnosis_dsm psy:field:clinical sys:part_of
ln psych:psychological_assessment psy:field:clinical sys:part_of
ln psy:field:clinical counsel:psychotherapy thesaurus:related
ln psy:field:clinical med:medicine thesaurus:related
def "psy:field:counseling" "カウンセリング心理学 — helping people cope, adjust and grow through dialogue."
ln psy:field:counseling psy sys:part_of
ln counsel:counseling psy:field:counseling sys:part_of
ln counsel:psychotherapy psy:field:counseling sys:part_of
ln counsel:therapeutic_alliance psy:field:counseling sys:part_of
ln counsel:active_listening psy:field:counseling sys:part_of
ln counsel:empathy psy:field:counseling sys:part_of
ln psy:field:counseling psych:mental_health thesaurus:related
def "psy:field:educational" "教育心理学 — how people learn and how teaching can help."
ln psy:field:educational psy sys:part_of
ln edupsy:learning_theory psy:field:educational sys:part_of
ln edupsy:constructivism psy:field:educational sys:part_of
ln edupsy:metacognition psy:field:educational sys:part_of
ln edupsy:growth_mindset psy:field:educational sys:part_of
ln edupsy:self_efficacy psy:field:educational sys:part_of
ln edupsy:zone_of_proximal_development psy:field:educational sys:part_of
ln psy:field:educational psy:learning thesaurus:related
def "psy:field:abnormal" "異常心理学 — the nature, causes and classification of psychological disorders."
ln psy:field:abnormal psy sys:part_of
ln psych:psychopathology psy:field:abnormal sys:part_of
ln psych:anxiety_disorder psy:field:abnormal sys:part_of
ln psych:depression psy:field:abnormal sys:part_of
ln psych:ptsd psy:field:abnormal sys:part_of
ln psy:field:abnormal psych:diagnosis_dsm thesaurus:related
def "psy:field:health" "健康心理学 — how mind, behaviour and body interact in health and illness."
ln psy:field:health psy sys:part_of
ln psy:field:health counsel:mindfulness thesaurus:related
ln psy:field:health med:medicine thesaurus:related
ln psy:field:health bio:branch:physiology thesaurus:related
def "psy:field:industrial_organizational" "産業・組織心理学 — behaviour at work: motivation, teams, leadership, selection."
ln psy:field:industrial_organizational psy sys:part_of
ln psy:motivation psy:field:industrial_organizational sys:part_of
ln psy:field:industrial_organizational org:engagement thesaurus:related
ln psy:field:industrial_organizational mgmt:field:organizational_behavior thesaurus:related
def "psy:field:positive" "ポジティブ心理学 — wellbeing, strengths, flourishing and what makes life good."
ln psy:field:positive psy sys:part_of
ln psy:field:positive emo:joy thesaurus:related
ln psy:field:positive emo:satisfaction thesaurus:related
ln psy:field:positive edupsy:growth_mindset thesaurus:related
def "psy:field:cross_cultural" "文化心理学 — how culture shapes mind and behaviour."
ln psy:field:cross_cultural psy sys:part_of
ln psy:field:cross_cultural socio:culture thesaurus:related
ln psy:field:cross_cultural psy:social_psychology thesaurus:related
def "psy:field:comparative" "比較心理学 — behaviour across animal species, and what it reveals about mind."
ln psy:field:comparative psy sys:part_of
ln psy:conditioning psy:field:comparative sys:part_of
ln psy:field:comparative bio:branch:zoology thesaurus:related
ln psy:field:comparative crosscut:evolution thesaurus:related
def "psy:field:forensic" "犯罪・司法心理学 — psychology applied to law, crime and the courts."
ln psy:field:forensic psy sys:part_of
ln psy:field:forensic law:branch:criminal_law thesaurus:related
ln psy:field:forensic socio:deviance thesaurus:related
def "psy:field:neuropsychology" "神経心理学 — how brain structure and damage relate to mind and behaviour."
ln psy:field:neuropsychology psy sys:part_of
ln psy:field:neuropsychology neuro:neuropsychology thesaurus:related
ln psy:field:neuropsychology neuro:prefrontal_cortex thesaurus:related
ln psy:field:neuropsychology neuro:hippocampus thesaurus:related
def "psy:field:affective" "感情心理学 — the psychology of emotion, mood and feeling."
ln psy:field:affective psy sys:part_of
ln psy:emotion psy:field:affective sys:part_of
ln psy:field:affective emo:anger thesaurus:related
ln psy:field:affective emo:fear thesaurus:related
ln psy:field:affective emo:joy thesaurus:related
ln psy:field:affective neuro:affective_neuroscience thesaurus:related
def "psy:field:experimental_methods" "実験心理学・心理測定 — how psychology is studied: experiment, measurement, statistics."
ln psy:field:experimental_methods psy sys:part_of
ln psych:psychometrics psy:field:experimental_methods sys:part_of
ln psych:psychological_assessment psy:field:experimental_methods sys:part_of
ln psy:field:experimental_methods knowledge:method:experimental thesaurus:related
ln psy:field:experimental_methods math:statistics thesaurus:related

# ══ schools / perspectives (psy:school:*) ══
def "psy:school:structuralism" "構造主義 — analysing consciousness into its elementary sensations (Wundt, Titchener)."
ln psy:school:structuralism psy sys:part_of
def "psy:school:functionalism" "機能主義 — what mind is FOR: how mental processes help us adapt (James)."
ln psy:school:functionalism psy sys:part_of
ln psy:school:structuralism psy:school:functionalism chrono:before
def "psy:school:psychoanalysis" "精神分析 — the unconscious, drives and childhood as shapers of mind (Freud)."
ln psy:school:psychoanalysis psy sys:part_of
ln psy:school:psychoanalysis counsel:psychoanalysis thesaurus:related
ln psy:school:psychoanalysis counsel:transference thesaurus:related
ln psy:school:psychoanalysis cog:ego thesaurus:related
ln psy:school:psychoanalysis cog:projection thesaurus:related
ln psy:school:psychoanalysis cog:denial thesaurus:related
ln psy:school:functionalism psy:school:psychoanalysis chrono:before
def "psy:school:gestalt" "ゲシュタルト心理学 — the whole is other than the sum of its parts; perceptual organisation."
ln psy:school:gestalt psy sys:part_of
ln psy:school:gestalt psy:perception thesaurus:related
ln psy:school:psychoanalysis psy:school:gestalt chrono:before
def "psy:school:behaviorism" "行動主義 — psychology as the science of observable behaviour, learned by conditioning (Watson, Skinner)."
ln psy:school:behaviorism psy sys:part_of
ln psy:school:behaviorism psy:behavioral_psychology thesaurus:related
ln psy:school:behaviorism psy:classical_conditioning thesaurus:related
ln psy:school:behaviorism psy:operant_conditioning thesaurus:related
ln psy:school:behaviorism psy:conditioning thesaurus:related
ln psy:school:behaviorism edupsy:behaviorism thesaurus:related
ln psy:school:gestalt psy:school:behaviorism chrono:before
def "psy:school:humanistic" "人間性心理学 — free will, growth and self-actualisation (Maslow, Rogers)."
ln psy:school:humanistic psy sys:part_of
ln psy:school:humanistic psy:maslow_hierarchy thesaurus:related
ln psy:school:humanistic counsel:person_centered_therapy thesaurus:related
ln psy:school:humanistic counsel:unconditional_positive_regard thesaurus:related
ln psy:school:behaviorism psy:school:humanistic chrono:before
def "psy:school:cognitive" "認知主義 — the mind as an information processor; the 'cognitive revolution'."
ln psy:school:cognitive psy sys:part_of
ln psy:school:cognitive psy:cognitive_psychology thesaurus:related
ln psy:school:cognitive edupsy:cognitivism thesaurus:related
ln psy:school:humanistic psy:school:cognitive chrono:before
def "psy:school:sociocultural" "社会文化的アプローチ — mind as shaped by culture and social interaction (Vygotsky)."
ln psy:school:sociocultural psy sys:part_of
ln psy:school:sociocultural psy:vygotsky_sociocultural thesaurus:related
ln psy:school:sociocultural edupsy:social_constructivism thesaurus:related
ln psy:school:cognitive psy:school:sociocultural chrono:before
def "psy:school:biological" "生物学的アプローチ — behaviour explained through brain, genes and evolution."
ln psy:school:biological psy sys:part_of
ln psy:school:biological psy:biopsychology thesaurus:related
ln psy:school:sociocultural psy:school:biological chrono:before
def "psy:school:evolutionary" "進化心理学 — mind as a set of adaptations shaped by natural selection."
ln psy:school:evolutionary psy sys:part_of
ln psy:school:biological psy:school:evolutionary chrono:before

# ══ founders (person:*) ══
def "person:wilhelm_wundt" "Founder of psychology as an experimental science; opened the first psychology lab (1879)."
ln person:wilhelm_wundt person:figure thesaurus:related
ln person:wilhelm_wundt person:field:psychology person:worked_in
ln person:wilhelm_wundt psy:school:structuralism person:belongs_to_school
ln person:wilhelm_wundt hist:period:modern_era person:active_in
def "person:william_james" "American pioneer of functionalism; wrote 'The Principles of Psychology'."
ln person:william_james person:figure thesaurus:related
ln person:william_james person:field:psychology person:worked_in
ln person:william_james psy:school:functionalism person:belongs_to_school
ln person:william_james hist:period:modern_era person:active_in
ln person:william_james psy:consciousness thesaurus:related
ln person:william_james psy:emotion thesaurus:related
def "person:sigmund_freud" "Founder of psychoanalysis; theorised the unconscious, drives and defence."
ln person:sigmund_freud person:figure thesaurus:related
ln person:sigmund_freud person:field:psychology person:worked_in
ln person:sigmund_freud psy:school:psychoanalysis person:belongs_to_school
ln person:sigmund_freud hist:period:modern_era person:active_in
ln person:sigmund_freud counsel:psychoanalysis thesaurus:related
def "person:carl_jung" "Founder of analytical psychology; archetypes and the collective unconscious."
ln person:carl_jung person:figure thesaurus:related
ln person:carl_jung person:field:psychology person:worked_in
ln person:carl_jung psy:school:psychoanalysis person:belongs_to_school
ln person:carl_jung hist:period:modern_era person:active_in
def "person:alfred_adler" "Founder of individual psychology; the inferiority complex and striving."
ln person:alfred_adler person:figure thesaurus:related
ln person:alfred_adler person:field:psychology person:worked_in
ln person:alfred_adler psy:school:psychoanalysis person:belongs_to_school
ln person:alfred_adler hist:period:modern_era person:active_in
def "person:john_watson" "Founder of behaviorism; psychology as the prediction and control of behaviour."
ln person:john_watson person:figure thesaurus:related
ln person:john_watson person:field:psychology person:worked_in
ln person:john_watson psy:school:behaviorism person:belongs_to_school
ln person:john_watson hist:period:modern_era person:active_in
ln person:john_watson psy:behavioral_psychology thesaurus:related
def "person:ivan_pavlov" "Discovered classical conditioning through his experiments on dogs."
ln person:ivan_pavlov person:figure thesaurus:related
ln person:ivan_pavlov person:field:psychology person:worked_in
ln person:ivan_pavlov psy:school:behaviorism person:belongs_to_school
ln person:ivan_pavlov hist:period:modern_era person:active_in
ln person:ivan_pavlov psy:classical_conditioning thesaurus:related
def "person:b_f_skinner" "Developed operant conditioning and reinforcement; radical behaviorism."
ln person:b_f_skinner person:figure thesaurus:related
ln person:b_f_skinner person:field:psychology person:worked_in
ln person:b_f_skinner psy:school:behaviorism person:belongs_to_school
ln person:b_f_skinner hist:period:modern_era person:active_in
ln person:b_f_skinner psy:operant_conditioning thesaurus:related
ln person:b_f_skinner psy:skinner_operant thesaurus:related
def "person:abraham_maslow" "Humanistic psychologist; the hierarchy of needs and self-actualisation."
ln person:abraham_maslow person:figure thesaurus:related
ln person:abraham_maslow person:field:psychology person:worked_in
ln person:abraham_maslow psy:school:humanistic person:belongs_to_school
ln person:abraham_maslow hist:period:modern_era person:active_in
ln person:abraham_maslow psy:maslow_hierarchy thesaurus:related
def "person:carl_rogers" "Founder of person-centred therapy; unconditional positive regard."
ln person:carl_rogers person:figure thesaurus:related
ln person:carl_rogers person:field:psychology person:worked_in
ln person:carl_rogers psy:school:humanistic person:belongs_to_school
ln person:carl_rogers hist:period:modern_era person:active_in
ln person:carl_rogers counsel:person_centered_therapy thesaurus:related
ln person:carl_rogers counsel:unconditional_positive_regard thesaurus:related
def "person:jean_piaget" "Mapped the stages of children's cognitive development."
ln person:jean_piaget person:figure thesaurus:related
ln person:jean_piaget person:field:psychology person:worked_in
ln person:jean_piaget psy:school:cognitive person:belongs_to_school
ln person:jean_piaget hist:period:modern_era person:active_in
ln person:jean_piaget psy:piaget_stages thesaurus:related
ln person:jean_piaget devpsy:sensorimotor_stage thesaurus:related
def "person:lev_vygotsky" "Theorised the social and cultural bases of learning; the zone of proximal development."
ln person:lev_vygotsky person:figure thesaurus:related
ln person:lev_vygotsky person:field:psychology person:worked_in
ln person:lev_vygotsky psy:school:sociocultural person:belongs_to_school
ln person:lev_vygotsky hist:period:modern_era person:active_in
ln person:lev_vygotsky psy:vygotsky_sociocultural thesaurus:related
ln person:lev_vygotsky edupsy:zone_of_proximal_development thesaurus:related
def "person:albert_bandura" "Social learning theory; observational learning and self-efficacy."
ln person:albert_bandura person:figure thesaurus:related
ln person:albert_bandura person:field:psychology person:worked_in
ln person:albert_bandura psy:school:cognitive person:belongs_to_school
ln person:albert_bandura hist:period:modern_era person:active_in
ln person:albert_bandura psy:bandura_social_learning thesaurus:related
ln person:albert_bandura edupsy:self_efficacy thesaurus:related
def "person:erik_erikson" "Theorised eight psychosocial stages across the whole lifespan."
ln person:erik_erikson person:figure thesaurus:related
ln person:erik_erikson person:field:psychology person:worked_in
ln person:erik_erikson psy:school:psychoanalysis person:belongs_to_school
ln person:erik_erikson hist:period:modern_era person:active_in
ln person:erik_erikson devpsy:erikson_stages thesaurus:related
def "person:john_bowlby" "Founder of attachment theory: the child's bond with the caregiver."
ln person:john_bowlby person:figure thesaurus:related
ln person:john_bowlby person:field:psychology person:worked_in
ln person:john_bowlby psy:school:psychoanalysis person:belongs_to_school
ln person:john_bowlby hist:period:modern_era person:active_in
ln person:john_bowlby devpsy:attachment thesaurus:related
ln person:john_bowlby devpsy:secure_attachment thesaurus:related
def "person:mary_ainsworth" "Devised the 'Strange Situation'; classified patterns of infant attachment."
ln person:mary_ainsworth person:figure thesaurus:related
ln person:mary_ainsworth person:field:psychology person:worked_in
ln person:mary_ainsworth psy:school:psychoanalysis person:belongs_to_school
ln person:mary_ainsworth hist:period:modern_era person:active_in
ln person:mary_ainsworth devpsy:secure_attachment thesaurus:related
ln person:mary_ainsworth devpsy:insecure_attachment thesaurus:related
def "person:daniel_kahneman" "Showed how heuristics and biases shape judgement; founded behavioural economics."
ln person:daniel_kahneman person:figure thesaurus:related
ln person:daniel_kahneman person:field:psychology person:worked_in
ln person:daniel_kahneman psy:school:cognitive person:belongs_to_school
ln person:daniel_kahneman hist:period:modern_era person:active_in
ln person:daniel_kahneman psy:cognitive_bias thesaurus:related
ln person:daniel_kahneman cog:anchoring thesaurus:related
ln person:daniel_kahneman econ:field:behavioral_economics thesaurus:related
def "person:stanley_milgram" "His obedience experiments revealed how ordinary people follow authority."
ln person:stanley_milgram person:figure thesaurus:related
ln person:stanley_milgram person:field:psychology person:worked_in
ln person:stanley_milgram psy:school:cognitive person:belongs_to_school
ln person:stanley_milgram hist:period:modern_era person:active_in
ln person:stanley_milgram socio:authority thesaurus:related
def "person:paul_ekman" "Mapped the basic, universally-recognised facial expressions of emotion."
ln person:paul_ekman person:figure thesaurus:related
ln person:paul_ekman person:field:psychology person:worked_in
ln person:paul_ekman psy:school:biological person:belongs_to_school
ln person:paul_ekman hist:period:modern_era person:active_in
ln person:paul_ekman psy:emotion thesaurus:related
ln person:paul_ekman emo:anger thesaurus:related

# ══ broadened core concepts (psy:topic:* / psy:concept:*) ══
def "psy:topic:learning" "学習 — relatively lasting change in behaviour from experience."
ln psy:topic:learning psy:field:cognitive sys:part_of
def "psy:concept:reinforcement" "Any consequence that makes a behaviour more likely to recur."
ln psy:concept:reinforcement psy:topic:learning sys:part_of
def "psy:concept:punishment" "Any consequence that makes a behaviour less likely to recur."
ln psy:concept:punishment psy:topic:learning sys:part_of
def "psy:concept:extinction" "The fading of a conditioned response when it is no longer reinforced."
ln psy:concept:extinction psy:topic:learning sys:part_of
def "psy:concept:shaping" "Building a complex behaviour by reinforcing successive approximations."
ln psy:concept:shaping psy:topic:learning sys:part_of
def "psy:concept:observational_learning" "Learning by watching and imitating others (modelling)."
ln psy:concept:observational_learning psy:topic:learning sys:part_of
def "psy:concept:habituation" "A decreasing response to a repeated, harmless stimulus."
ln psy:concept:habituation psy:topic:learning sys:part_of
def "psy:topic:memory" "記憶 — encoding, storing and retrieving information."
ln psy:topic:memory psy:field:cognitive sys:part_of
def "psy:concept:sensory_memory" "The very brief, high-capacity trace of raw sensation."
ln psy:concept:sensory_memory psy:topic:memory sys:part_of
def "psy:concept:encoding" "Transforming information into a form that can be stored."
ln psy:concept:encoding psy:topic:memory sys:part_of
def "psy:concept:retrieval" "Bringing stored information back into awareness."
ln psy:concept:retrieval psy:topic:memory sys:part_of
def "psy:concept:forgetting_curve" "The rapid, then slowing, loss of memory over time (Ebbinghaus)."
ln psy:concept:forgetting_curve psy:topic:memory sys:part_of
def "psy:concept:schema" "An organised mental framework that guides how we interpret and remember."
ln psy:concept:schema psy:topic:memory sys:part_of
def "psy:concept:false_memory" "A recollection that feels real but did not happen as remembered."
ln psy:concept:false_memory psy:topic:memory sys:part_of
def "psy:topic:motivation_emotion" "動機づけと情動 — what drives behaviour and how feeling arises."
ln psy:topic:motivation_emotion psy:field:affective sys:part_of
def "psy:concept:intrinsic_motivation" "Doing something for its own inherent reward."
ln psy:concept:intrinsic_motivation psy:topic:motivation_emotion sys:part_of
def "psy:concept:extrinsic_motivation" "Doing something for an external reward or to avoid punishment."
ln psy:concept:extrinsic_motivation psy:topic:motivation_emotion sys:part_of
def "psy:concept:drive_theory" "Behaviour as driven to reduce the tension of unmet needs."
ln psy:concept:drive_theory psy:topic:motivation_emotion sys:part_of
def "psy:concept:arousal" "The body's state of physiological activation."
ln psy:concept:arousal psy:topic:motivation_emotion sys:part_of
def "psy:concept:james_lange_theory" "Emotion as our perception of bodily changes ('we are afraid because we tremble')."
ln psy:concept:james_lange_theory psy:topic:motivation_emotion sys:part_of
def "psy:concept:cannon_bard_theory" "Bodily arousal and the felt emotion arise at the same time."
ln psy:concept:cannon_bard_theory psy:topic:motivation_emotion sys:part_of
def "psy:concept:two_factor_theory" "Emotion = physiological arousal + a cognitive label for it (Schachter-Singer)."
ln psy:concept:two_factor_theory psy:topic:motivation_emotion sys:part_of
def "psy:topic:personality" "人格 — the enduring structure of an individual's psychology."
ln psy:topic:personality psy:field:personality sys:part_of
def "psy:concept:trait_theory" "Personality described as standing on a few stable dimensions."
ln psy:concept:trait_theory psy:topic:personality sys:part_of
def "psy:concept:id_ego_superego" "Freud's three-part model of the psyche: drive, reality, conscience."
ln psy:concept:id_ego_superego psy:topic:personality sys:part_of
def "psy:concept:defense_mechanism" "Unconscious strategies that protect the self from anxiety."
ln psy:concept:defense_mechanism psy:topic:personality sys:part_of
def "psy:concept:locus_of_control" "Whether one feels outcomes are due to oneself or to outside forces."
ln psy:concept:locus_of_control psy:topic:personality sys:part_of
def "psy:concept:self_concept" "The organised set of beliefs one holds about oneself."
ln psy:concept:self_concept psy:topic:personality sys:part_of
def "psy:topic:social" "社会的行動 — thought and behaviour in the presence of others."
ln psy:topic:social psy:field:social sys:part_of
def "psy:concept:conformity" "Adjusting one's behaviour to match a group (Asch)."
ln psy:concept:conformity psy:topic:social sys:part_of
def "psy:concept:obedience" "Complying with the commands of an authority (Milgram)."
ln psy:concept:obedience psy:topic:social sys:part_of
def "psy:concept:attribution" "How we explain the causes of behaviour, our own and others'."
ln psy:concept:attribution psy:topic:social sys:part_of
def "psy:concept:prejudice" "A pre-formed, usually negative attitude toward a group."
ln psy:concept:prejudice psy:topic:social sys:part_of
def "psy:concept:bystander_effect" "The more onlookers, the less likely any one helps."
ln psy:concept:bystander_effect psy:topic:social sys:part_of
def "psy:concept:groupthink" "The suppression of dissent for the sake of group harmony."
ln psy:concept:groupthink psy:topic:social sys:part_of
def "psy:concept:attitude" "A learned evaluation of a person, object or idea."
ln psy:concept:attitude psy:topic:social sys:part_of
def "psy:topic:stress_coping" "ストレスと対処 — the demand on the organism and how it responds."
ln psy:topic:stress_coping psy:field:health sys:part_of
def "psy:concept:stress" "The response to demands that tax or exceed one's resources."
ln psy:concept:stress psy:topic:stress_coping sys:part_of
def "psy:concept:coping" "The effort to manage stress, problem- or emotion-focused."
ln psy:concept:coping psy:topic:stress_coping sys:part_of
def "psy:concept:general_adaptation_syndrome" "Selye's alarm-resistance-exhaustion stages of the stress response."
ln psy:concept:general_adaptation_syndrome psy:topic:stress_coping sys:part_of
def "psy:concept:resilience" "The capacity to adapt well in the face of adversity."
ln psy:concept:resilience psy:topic:stress_coping sys:part_of
def "psy:concept:burnout" "Exhaustion, cynicism and reduced efficacy from chronic stress."
ln psy:concept:burnout psy:topic:stress_coping sys:part_of
def "psy:topic:disorder" "精神障害 — clinically significant disturbance of mind and behaviour."
ln psy:topic:disorder psy:field:abnormal sys:part_of
def "psy:concept:anxiety_disorders" "Disorders marked by excessive fear and worry."
ln psy:concept:anxiety_disorders psy:topic:disorder sys:part_of
def "psy:concept:mood_disorders" "Disorders of emotional state, such as depression and bipolar disorder."
ln psy:concept:mood_disorders psy:topic:disorder sys:part_of
def "psy:concept:schizophrenia" "A severe disorder of thought and perception, with psychosis."
ln psy:concept:schizophrenia psy:topic:disorder sys:part_of
def "psy:concept:ocd" "Obsessive-compulsive disorder: intrusive thoughts and ritual acts."
ln psy:concept:ocd psy:topic:disorder sys:part_of
def "psy:concept:personality_disorders" "Enduring, inflexible patterns of inner experience and behaviour."
ln psy:concept:personality_disorders psy:topic:disorder sys:part_of
def "psy:concept:neurodevelopmental" "Disorders arising in development, such as autism and ADHD."
ln psy:concept:neurodevelopmental psy:topic:disorder sys:part_of
def "psy:concept:eating_disorders" "Disorders of eating behaviour and body image."
ln psy:concept:eating_disorders psy:topic:disorder sys:part_of
def "psy:topic:therapy" "心理療法 — the treatment of psychological problems."
ln psy:topic:therapy psy:field:clinical sys:part_of
def "psy:concept:cognitive_behavioral_therapy" "Changing unhelpful thoughts and behaviours; the best-evidenced talking therapy."
ln psy:concept:cognitive_behavioral_therapy psy:topic:therapy sys:part_of
def "psy:concept:psychodynamic_therapy" "Exploring unconscious conflict and early relationships."
ln psy:concept:psychodynamic_therapy psy:topic:therapy sys:part_of
def "psy:concept:humanistic_therapy" "A warm, accepting relationship to support growth (Rogers)."
ln psy:concept:humanistic_therapy psy:topic:therapy sys:part_of
def "psy:concept:behavioral_therapy" "Using conditioning to change maladaptive behaviour."
ln psy:concept:behavioral_therapy psy:topic:therapy sys:part_of
def "psy:concept:biomedical_therapy" "Treating disorder with medication or other biological means."
ln psy:concept:biomedical_therapy psy:topic:therapy sys:part_of
def "psy:concept:group_family_therapy" "Working with people together, in groups or as families."
ln psy:concept:group_family_therapy psy:topic:therapy sys:part_of
def "psy:topic:method" "研究法 — how psychology gathers and tests its knowledge."
ln psy:topic:method psy:field:experimental_methods sys:part_of
def "psy:concept:experiment" "Manipulating a variable to test its causal effect."
ln psy:concept:experiment psy:topic:method sys:part_of
def "psy:concept:correlational_study" "Measuring how two variables move together (not causation)."
ln psy:concept:correlational_study psy:topic:method sys:part_of
def "psy:concept:case_study" "The deep study of a single person or case."
ln psy:concept:case_study psy:topic:method sys:part_of
def "psy:concept:naturalistic_observation" "Watching behaviour unfold in its natural setting."
ln psy:concept:naturalistic_observation psy:topic:method sys:part_of
def "psy:concept:reliability" "The consistency of a measure across occasions."
ln psy:concept:reliability psy:topic:method sys:part_of
def "psy:concept:validity" "Whether a measure captures what it claims to."
ln psy:concept:validity psy:topic:method sys:part_of

# ── cross bridges to existing atoms ──
ln psy:concept:observational_learning psy:bandura_social_learning thesaurus:related
ln psy:concept:cognitive_behavioral_therapy counsel:cognitive_behavioral_therapy thesaurus:related
ln psy:concept:humanistic_therapy counsel:person_centered_therapy thesaurus:related
ln psy:concept:psychodynamic_therapy counsel:psychoanalysis thesaurus:related
ln psy:concept:group_family_therapy counsel:group_therapy thesaurus:related
ln psy:concept:defense_mechanism cog:projection thesaurus:related
ln psy:concept:anxiety_disorders psych:anxiety_disorder thesaurus:related
ln psy:concept:mood_disorders psych:depression thesaurus:related
ln psy:concept:conformity socio:norm thesaurus:related
ln psy:concept:obedience socio:authority thesaurus:related
ln psy:concept:burnout org:burnout thesaurus:related
ln psy:concept:stress counsel:mindfulness thesaurus:related
ln psy:concept:schema edupsy:cognitive_load thesaurus:related
ln psy:concept:intrinsic_motivation org:intrinsic_motivation thesaurus:related
