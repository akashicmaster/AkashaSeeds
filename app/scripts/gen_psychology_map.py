#!/usr/bin/env python3
# Generate a broad general-education-level psychology map:
#   app/ontology/base3/psychology_map.ak
# Comprehensive: gives psychology its spine of subfields and
# schools, first-classes the founding psychologists as person:*, and broadens the
# general-education-level concept coverage (learning, memory, motivation/emotion, personality,
# social, stress/health, disorders, therapies, research methods) — cross-linking the
# scattered atoms already present (psy:*, cog:*, devpsy:*, edupsy:*, counsel:*,
# psych:*, neuro:*, emo:*) under it. Wired into knowledge:branch:social_science.
#
# `psy` (top) already exists — NOT re-def'd; existing atoms are only linked.

import os

def esc(s):
    return s.replace('"', "'")

L = [
 "# Akasha ontology — psychology: a broad general-education-level map.",
 "# Subfields + schools + founders + broadened core concepts, with the scattered",
 "# psy:/cog:/devpsy:/edupsy:/counsel:/psych:/neuro:/emo: atoms cross-linked under it.",
 "# General-education breadth; research depth is reserved for level-C packs. Base pack.",
 "",
 "# psy (top) and person:figure already exist — do not re-define.",
 'def "person:field:psychology" "Psychology — the field of those who study mind and behaviour."',
 "ln person:field:psychology person:figure thesaurus:related",
 "ln person:field:psychology psy thesaurus:related",
 "ln psy knowledge:branch:social_science knowledge:in_branch",
 "ln psy knowledge:cognitive_science thesaurus:related",
]

# ── Part A: subfields (psy:field:*) with existing atoms cross-linked ────────────────
FIELDS = [
 ("cognitive", "認知心理学 — mental processes: perception, attention, memory, thought, language.",
   ["psy:cognition","psy:cognitive_psychology","psy:attention","psy:perception","psy:memory","psy:working_memory","psy:long_term_memory","psy:learning","psy:cognitive_bias","psy:consciousness","psy:intelligence"], ["cog:pattern_recognition","neuro:cognitive_neuroscience","knowledge:cognitive_science"]),
 ("developmental", "発達心理学 — how mind and behaviour change across the lifespan.",
   ["psy:developmental_psychology","psy:piaget_stages","psy:vygotsky_sociocultural"], ["devpsy:attachment","devpsy:erikson_stages"]),
 ("social", "社会心理学 — how people think about, influence and relate to one another.",
   ["psy:social_psychology","psy:bandura_social_learning"], ["cog:cognitive_dissonance","socio:social_interaction"]),
 ("personality", "人格心理学 — the enduring patterns that make each person distinctive.",
   ["psy:personality_psychology","psy:big_five","psy:maslow_hierarchy"], []),
 ("biological", "生物心理学 — the biological bases of behaviour: brain, neurons, hormones, genes.",
   ["psy:biopsychology"], ["neuro:neuron","neuro:neurotransmitter","neuro:limbic_system","bio:branch:physiology"]),
 ("clinical", "臨床心理学 — assessing and treating mental disorders and distress.",
   ["psych:clinical_psychology","psych:psychopathology","psych:mental_health","psych:diagnosis_dsm","psych:psychological_assessment"], ["counsel:psychotherapy","med:medicine"]),
 ("counseling", "カウンセリング心理学 — helping people cope, adjust and grow through dialogue.",
   ["counsel:counseling","counsel:psychotherapy","counsel:therapeutic_alliance","counsel:active_listening","counsel:empathy"], ["psych:mental_health"]),
 ("educational", "教育心理学 — how people learn and how teaching can help.",
   ["edupsy:learning_theory","edupsy:constructivism","edupsy:metacognition","edupsy:growth_mindset","edupsy:self_efficacy","edupsy:zone_of_proximal_development"], ["psy:learning"]),
 ("abnormal", "異常心理学 — the nature, causes and classification of psychological disorders.",
   ["psych:psychopathology","psych:anxiety_disorder","psych:depression","psych:ptsd"], ["psych:diagnosis_dsm"]),
 ("health", "健康心理学 — how mind, behaviour and body interact in health and illness.",
   [], ["counsel:mindfulness","med:medicine","bio:branch:physiology"]),
 ("industrial_organizational", "産業・組織心理学 — behaviour at work: motivation, teams, leadership, selection.",
   ["psy:motivation"], ["org:engagement","mgmt:field:organizational_behavior"]),
 ("positive", "ポジティブ心理学 — wellbeing, strengths, flourishing and what makes life good.",
   [], ["emo:joy","emo:satisfaction","edupsy:growth_mindset"]),
 ("cross_cultural", "文化心理学 — how culture shapes mind and behaviour.",
   [], ["socio:culture","psy:social_psychology"]),
 ("comparative", "比較心理学 — behaviour across animal species, and what it reveals about mind.",
   ["psy:conditioning"], ["bio:branch:zoology","crosscut:evolution"]),
 ("forensic", "犯罪・司法心理学 — psychology applied to law, crime and the courts.",
   [], ["law:branch:criminal_law","socio:deviance"]),
 ("neuropsychology", "神経心理学 — how brain structure and damage relate to mind and behaviour.",
   [], ["neuro:neuropsychology","neuro:prefrontal_cortex","neuro:hippocampus"]),
 ("affective", "感情心理学 — the psychology of emotion, mood and feeling.",
   ["psy:emotion"], ["emo:anger","emo:fear","emo:joy","neuro:affective_neuroscience"]),
 ("experimental_methods", "実験心理学・心理測定 — how psychology is studied: experiment, measurement, statistics.",
   ["psych:psychometrics","psych:psychological_assessment"], ["knowledge:method:experimental","math:statistics"]),
]
L += ["", "# ══ subfields (psy:field:*) ══"]
for slug, gloss, kids, bridges in FIELDS:
    fid = f"psy:field:{slug}"
    L.append(f'def "{fid}" "{esc(gloss)}"')
    L.append(f"ln {fid} psy sys:part_of")
    for k in kids:
        L.append(f"ln {k} {fid} sys:part_of")
    for b in bridges:
        L.append(f"ln {fid} {b} thesaurus:related")

# ── Part B: schools / perspectives (psy:school:*) with a rough historical chain ─
SCHOOLS = [
 ("structuralism", "構造主義 — analysing consciousness into its elementary sensations (Wundt, Titchener).", [], None),
 ("functionalism", "機能主義 — what mind is FOR: how mental processes help us adapt (James).", [], "structuralism"),
 ("psychoanalysis", "精神分析 — the unconscious, drives and childhood as shapers of mind (Freud).", ["counsel:psychoanalysis","counsel:transference","cog:ego","cog:projection","cog:denial"], "functionalism"),
 ("gestalt", "ゲシュタルト心理学 — the whole is other than the sum of its parts; perceptual organisation.", ["psy:perception"], "psychoanalysis"),
 ("behaviorism", "行動主義 — psychology as the science of observable behaviour, learned by conditioning (Watson, Skinner).", ["psy:behavioral_psychology","psy:classical_conditioning","psy:operant_conditioning","psy:conditioning","edupsy:behaviorism"], "gestalt"),
 ("humanistic", "人間性心理学 — free will, growth and self-actualisation (Maslow, Rogers).", ["psy:maslow_hierarchy","counsel:person_centered_therapy","counsel:unconditional_positive_regard"], "behaviorism"),
 ("cognitive", "認知主義 — the mind as an information processor; the 'cognitive revolution'.", ["psy:cognitive_psychology","edupsy:cognitivism"], "humanistic"),
 ("sociocultural", "社会文化的アプローチ — mind as shaped by culture and social interaction (Vygotsky).", ["psy:vygotsky_sociocultural","edupsy:social_constructivism"], "cognitive"),
 ("biological", "生物学的アプローチ — behaviour explained through brain, genes and evolution.", ["psy:biopsychology"], "sociocultural"),
 ("evolutionary", "進化心理学 — mind as a set of adaptations shaped by natural selection.", [], "biological"),
]
L += ["", "# ══ schools / perspectives (psy:school:*) ══"]
prev = None
for slug, gloss, kids, after in SCHOOLS:
    sid = f"psy:school:{slug}"
    L.append(f'def "{sid}" "{esc(gloss)}"')
    L.append(f"ln {sid} psy sys:part_of")
    for k in kids:
        L.append(f"ln {sid} {k} thesaurus:related")
    if after:
        L.append(f"ln psy:school:{after} {sid} chrono:before")

# ── Part C: founders (person:*) ──────────────────────────────────────────────
# (slug, gloss, school, [concept bridges])
PEOPLE = [
 ("wilhelm_wundt", "Founder of psychology as an experimental science; opened the first psychology lab (1879).", "structuralism", []),
 ("william_james", "American pioneer of functionalism; wrote 'The Principles of Psychology'.", "functionalism", ["psy:consciousness","psy:emotion"]),
 ("sigmund_freud", "Founder of psychoanalysis; theorised the unconscious, drives and defence.", "psychoanalysis", ["counsel:psychoanalysis"]),
 ("carl_jung", "Founder of analytical psychology; archetypes and the collective unconscious.", "psychoanalysis", []),
 ("alfred_adler", "Founder of individual psychology; the inferiority complex and striving.", "psychoanalysis", []),
 ("john_watson", "Founder of behaviorism; psychology as the prediction and control of behaviour.", "behaviorism", ["psy:behavioral_psychology"]),
 ("ivan_pavlov", "Discovered classical conditioning through his experiments on dogs.", "behaviorism", ["psy:classical_conditioning"]),
 ("b_f_skinner", "Developed operant conditioning and reinforcement; radical behaviorism.", "behaviorism", ["psy:operant_conditioning","psy:skinner_operant"]),
 ("abraham_maslow", "Humanistic psychologist; the hierarchy of needs and self-actualisation.", "humanistic", ["psy:maslow_hierarchy"]),
 ("carl_rogers", "Founder of person-centred therapy; unconditional positive regard.", "humanistic", ["counsel:person_centered_therapy","counsel:unconditional_positive_regard"]),
 ("jean_piaget", "Mapped the stages of children's cognitive development.", "cognitive", ["psy:piaget_stages","devpsy:sensorimotor_stage"]),
 ("lev_vygotsky", "Theorised the social and cultural bases of learning; the zone of proximal development.", "sociocultural", ["psy:vygotsky_sociocultural","edupsy:zone_of_proximal_development"]),
 ("albert_bandura", "Social learning theory; observational learning and self-efficacy.", "cognitive", ["psy:bandura_social_learning","edupsy:self_efficacy"]),
 ("erik_erikson", "Theorised eight psychosocial stages across the whole lifespan.", "psychoanalysis", ["devpsy:erikson_stages"]),
 ("john_bowlby", "Founder of attachment theory: the child's bond with the caregiver.", "psychoanalysis", ["devpsy:attachment","devpsy:secure_attachment"]),
 ("mary_ainsworth", "Devised the 'Strange Situation'; classified patterns of infant attachment.", "psychoanalysis", ["devpsy:secure_attachment","devpsy:insecure_attachment"]),
 ("daniel_kahneman", "Showed how heuristics and biases shape judgement; founded behavioural economics.", "cognitive", ["psy:cognitive_bias","cog:anchoring","econ:field:behavioral_economics"]),
 ("stanley_milgram", "His obedience experiments revealed how ordinary people follow authority.", "cognitive", ["socio:authority"]),
 ("paul_ekman", "Mapped the basic, universally-recognised facial expressions of emotion.", "biological", ["psy:emotion","emo:anger"]),
]
L += ["", "# ══ founders (person:*) ══"]
for slug, gloss, school, bridges in PEOPLE:
    pid = f"person:{slug}"
    L.append(f'def "{pid}" "{esc(gloss)}"')
    L.append(f"ln {pid} person:figure thesaurus:related")
    L.append(f"ln {pid} person:field:psychology person:worked_in")
    L.append(f"ln {pid} psy:school:{school} person:belongs_to_school")
    L.append(f"ln {pid} hist:period:modern_era person:active_in")
    for b in bridges:
        L.append(f"ln {pid} {b} thesaurus:related")

# ── Part D: broadened general-education-level concepts filling the gaps ────────────────────
# grouped topic hubs (psy:topic:*) with concise concept atoms under them
TOPICS = [
 ("learning", "学習 — relatively lasting change in behaviour from experience.", "psy:field:cognitive", [
   ("reinforcement", "Any consequence that makes a behaviour more likely to recur."),
   ("punishment", "Any consequence that makes a behaviour less likely to recur."),
   ("extinction", "The fading of a conditioned response when it is no longer reinforced."),
   ("shaping", "Building a complex behaviour by reinforcing successive approximations."),
   ("observational_learning", "Learning by watching and imitating others (modelling)."),
   ("habituation", "A decreasing response to a repeated, harmless stimulus."),
 ]),
 ("memory", "記憶 — encoding, storing and retrieving information.", "psy:field:cognitive", [
   ("sensory_memory", "The very brief, high-capacity trace of raw sensation."),
   ("encoding", "Transforming information into a form that can be stored."),
   ("retrieval", "Bringing stored information back into awareness."),
   ("forgetting_curve", "The rapid, then slowing, loss of memory over time (Ebbinghaus)."),
   ("schema", "An organised mental framework that guides how we interpret and remember."),
   ("false_memory", "A recollection that feels real but did not happen as remembered."),
 ]),
 ("motivation_emotion", "動機づけと情動 — what drives behaviour and how feeling arises.", "psy:field:affective", [
   ("intrinsic_motivation", "Doing something for its own inherent reward."),
   ("extrinsic_motivation", "Doing something for an external reward or to avoid punishment."),
   ("drive_theory", "Behaviour as driven to reduce the tension of unmet needs."),
   ("arousal", "The body's state of physiological activation."),
   ("james_lange_theory", "Emotion as our perception of bodily changes ('we are afraid because we tremble')."),
   ("cannon_bard_theory", "Bodily arousal and the felt emotion arise at the same time."),
   ("two_factor_theory", "Emotion = physiological arousal + a cognitive label for it (Schachter-Singer)."),
 ]),
 ("personality", "人格 — the enduring structure of an individual's psychology.", "psy:field:personality", [
   ("trait_theory", "Personality described as standing on a few stable dimensions."),
   ("id_ego_superego", "Freud's three-part model of the psyche: drive, reality, conscience."),
   ("defense_mechanism", "Unconscious strategies that protect the self from anxiety."),
   ("locus_of_control", "Whether one feels outcomes are due to oneself or to outside forces."),
   ("self_concept", "The organised set of beliefs one holds about oneself."),
 ]),
 ("social", "社会的行動 — thought and behaviour in the presence of others.", "psy:field:social", [
   ("conformity", "Adjusting one's behaviour to match a group (Asch)."),
   ("obedience", "Complying with the commands of an authority (Milgram)."),
   ("attribution", "How we explain the causes of behaviour, our own and others'."),
   ("prejudice", "A pre-formed, usually negative attitude toward a group."),
   ("bystander_effect", "The more onlookers, the less likely any one helps."),
   ("groupthink", "The suppression of dissent for the sake of group harmony."),
   ("attitude", "A learned evaluation of a person, object or idea."),
 ]),
 ("stress_coping", "ストレスと対処 — the demand on the organism and how it responds.", "psy:field:health", [
   ("stress", "The response to demands that tax or exceed one's resources."),
   ("coping", "The effort to manage stress, problem- or emotion-focused."),
   ("general_adaptation_syndrome", "Selye's alarm-resistance-exhaustion stages of the stress response."),
   ("resilience", "The capacity to adapt well in the face of adversity."),
   ("burnout", "Exhaustion, cynicism and reduced efficacy from chronic stress."),
 ]),
 ("disorder", "精神障害 — clinically significant disturbance of mind and behaviour.", "psy:field:abnormal", [
   ("anxiety_disorders", "Disorders marked by excessive fear and worry."),
   ("mood_disorders", "Disorders of emotional state, such as depression and bipolar disorder."),
   ("schizophrenia", "A severe disorder of thought and perception, with psychosis."),
   ("ocd", "Obsessive-compulsive disorder: intrusive thoughts and ritual acts."),
   ("personality_disorders", "Enduring, inflexible patterns of inner experience and behaviour."),
   ("neurodevelopmental", "Disorders arising in development, such as autism and ADHD."),
   ("eating_disorders", "Disorders of eating behaviour and body image."),
 ]),
 ("therapy", "心理療法 — the treatment of psychological problems.", "psy:field:clinical", [
   ("cognitive_behavioral_therapy", "Changing unhelpful thoughts and behaviours; the best-evidenced talking therapy."),
   ("psychodynamic_therapy", "Exploring unconscious conflict and early relationships."),
   ("humanistic_therapy", "A warm, accepting relationship to support growth (Rogers)."),
   ("behavioral_therapy", "Using conditioning to change maladaptive behaviour."),
   ("biomedical_therapy", "Treating disorder with medication or other biological means."),
   ("group_family_therapy", "Working with people together, in groups or as families."),
 ]),
 ("method", "研究法 — how psychology gathers and tests its knowledge.", "psy:field:experimental_methods", [
   ("experiment", "Manipulating a variable to test its causal effect."),
   ("correlational_study", "Measuring how two variables move together (not causation)."),
   ("case_study", "The deep study of a single person or case."),
   ("naturalistic_observation", "Watching behaviour unfold in its natural setting."),
   ("reliability", "The consistency of a measure across occasions."),
   ("validity", "Whether a measure captures what it claims to."),
 ]),
]
L += ["", "# ══ broadened core concepts (psy:topic:* / psy:concept:*) ══"]
for tslug, tgloss, field_id, concepts in TOPICS:
    thub = f"psy:topic:{tslug}"
    L.append(f'def "{thub}" "{esc(tgloss)}"')
    L.append(f"ln {thub} {field_id} sys:part_of")
    for cslug, cgloss in concepts:
        cid = f"psy:concept:{cslug}"
        L.append(f'def "{cid}" "{esc(cgloss)}"')
        L.append(f"ln {cid} {thub} sys:part_of")

# a few cross bridges from the new concepts to existing atoms
L += ["", "# ── cross bridges to existing atoms ──",
 "ln psy:concept:observational_learning psy:bandura_social_learning thesaurus:related",
 "ln psy:concept:cognitive_behavioral_therapy counsel:cognitive_behavioral_therapy thesaurus:related",
 "ln psy:concept:humanistic_therapy counsel:person_centered_therapy thesaurus:related",
 "ln psy:concept:psychodynamic_therapy counsel:psychoanalysis thesaurus:related",
 "ln psy:concept:group_family_therapy counsel:group_therapy thesaurus:related",
 "ln psy:concept:defense_mechanism cog:projection thesaurus:related",
 "ln psy:concept:anxiety_disorders psych:anxiety_disorder thesaurus:related",
 "ln psy:concept:mood_disorders psych:depression thesaurus:related",
 "ln psy:concept:conformity socio:norm thesaurus:related",
 "ln psy:concept:obedience socio:authority thesaurus:related",
 "ln psy:concept:burnout org:burnout thesaurus:related",
 "ln psy:concept:stress counsel:mindfulness thesaurus:related",
 "ln psy:concept:schema edupsy:cognitive_load thesaurus:related",
 "ln psy:concept:intrinsic_motivation org:intrinsic_motivation thesaurus:related",
]

path = "app/ontology/base3/psychology_map.ak"
os.makedirs(os.path.dirname(path), exist_ok=True)
with open(path, "w", encoding="utf-8") as f:
    f.write("\n".join(L) + "\n")
ndef = sum(1 for l in L if l.startswith("def "))
nln = sum(1 for l in L if l.startswith("ln "))
print(f"{path}: def={ndef} ln={nln} ({len(L)} lines)")
