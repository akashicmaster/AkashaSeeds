# Akasha ontology — namespace: med
# atoms: 27

def "med:concept:dosha" "In Ayurvedic medicine, one of three functional energies in nature (Vata, Pitta, and Kapha) that determine one's constitution and health."
ln med:concept:dosha med:system:ayurveda @central_concept_of

def "med:concept:hippocratic_oath" "An oath of ethics historically taken by physicians, establishing the principles of medical confidentiality and non-maleficence."
ln med:concept:hippocratic_oath med:system:western_medicine @foundational_ethics_for

def "med:concept:qi_blood_fluid" "The fundamental substances in TCM/Kampo that maintain life activities: Qi (energy), Blood (nutrients), and Fluid (body fluids)."
ln med:concept:qi_blood_fluid med:system:tcm @central_concept_of
ln med:concept:qi_blood_fluid med:system:kampo @central_concept_of

def "med:condition:anemia" "A decrease in the total amount of red blood cells or hemoglobin in the blood, often caused by iron or vitamin B12 deficiency."

def "med:condition:atherosclerosis" "A disease in which the inside of an artery narrows due to the build-up of plaque, which contains cholesterol and triglycerides."

def "med:condition:diabetes" "A group of metabolic disorders characterized by a high blood sugar level over a prolonged period."

def "med:condition:famine" "A widespread scarcity of food, caused by factors like crop failure or war, which was heavily mitigated in Eurasia by the introduction of the potato."

def "med:condition:kwashiorkor" "A severe form of malnutrition caused by a lack of protein in the diet."
ln med:condition:kwashiorkor med:condition:protein_deficiency sys:is_a

def "med:condition:night_blindness" "A condition making it difficult or impossible to see in relatively low light, often caused by vitamin A deficiency."

def "med:condition:osteoporosis" "A systemic skeletal disorder characterized by low bone mass and micro-architectural deterioration of bone tissue, often related to calcium and vitamin D."

def "med:condition:protein_deficiency" "A nutritional deficiency resulting from inadequate protein intake, leading to muscle wasting and immunodeficiency."

def "med:condition:scurvy" "A disease resulting from a lack of vitamin C, characterized by weakness, anemia, gum disease, and skin problems."

def "med:drug:aspirin" "A medication used to reduce pain, fever, or inflammation (a type of NSAID)."
ln med:drug:aspirin med:drug:nsaid sys:is_a
ln med:drug:aspirin bio:mechanism:competitive_inhibition @utilizes

def "med:drug:beta_blocker" "A class of medications predominantly used to manage abnormal heart rhythms and protect the heart from a second heart attack."
ln med:drug:beta_blocker med:pharma:antagonist sys:is_a
ln med:drug:beta_blocker bio:hormone:adrenaline @blocks_effect_of

def "med:drug:l_dopa" "A precursor to the neurotransmitters dopamine, norepinephrine, and epinephrine, used in the clinical treatment of Parkinson's disease."
ln med:drug:l_dopa bio:neurotransmitter:dopamine @precursor_of

def "med:drug:nsaid" "Nonsteroidal anti-inflammatory drugs, widely used to relieve pain, reduce inflammation, and bring down a high temperature."
ln med:drug:nsaid chem:protein:enzyme @inhibits

def "med:drug:ssri" "Selective serotonin reuptake inhibitors, a class of drugs typically used as antidepressants."
ln med:drug:ssri bio:receptor:transporter @inhibits
ln med:drug:ssri bio:neurotransmitter:serotonin @increases_availability_of

def "med:drug:statin" "A class of lipid-lowering medications that reduce illness and mortality in those who are at high risk of cardiovascular disease."
ln med:drug:statin chem:protein:enzyme @inhibits
ln med:drug:statin chem:lipid:cholesterol @reduces_synthesis_of

def "med:pharma:agonist" "A chemical that binds to a receptor and activates the receptor to produce a biological response."
ln med:pharma:agonist bio:receptor:receptor @activates

def "med:pharma:antagonist" "A type of receptor ligand or drug that blocks or dampens a biological response by binding to and blocking a receptor."
ln med:pharma:antagonist bio:receptor:receptor @blocks

def "med:pharma:pharmacodynamics" "The study of the biochemical and physiologic effects of drugs and their mechanisms of action (what the drug does to the body)."

def "med:pharma:pharmacokinetics" "The branch of pharmacology dedicated to determining the fate of substances administered to a living organism (ADME: Absorption, Distribution, Metabolism, Excretion)."
ln med:pharma:pharmacokinetics bio:metabolism:absorption @includes
ln med:pharma:pharmacokinetics bio:metabolism:metabolism @includes

def "med:system:ayurveda" "An alternative medicine system with historical roots in the Indian subcontinent, focusing on balancing the body's life energies."
ln med:system:ayurveda bio:metabolism:metabolism @regulates_holistically

def "med:system:kampo" "The Japanese study and adaptation of Traditional Chinese medicine, characterized by strict formulas and an emphasis on physical constitution (Sho)."
ln med:system:kampo bio:metabolism:metabolism @regulates_holistically

def "med:system:medical_astrology" "An ancient medical system that associates various parts of the body, diseases, and drugs as under the influence of the sun, moon, and planets."
ln med:system:medical_astrology mystic:concept:astrology @utilizes
ln med:system:medical_astrology sci:history:humorism @integrates_with
ln med:system:medical_astrology mystic:concept:zodiac @maps_to_body_parts

def "med:system:tcm" "A broad range of medicine practices sharing common concepts developed in China, based on a tradition of more than 2,000 years."
ln med:system:tcm med:system:kampo @adapted_into

def "med:system:western_medicine" "A system in which medical doctors and other healthcare professionals treat symptoms and diseases using drugs, radiation, or surgery."
ln med:system:western_medicine med:pharma:pharmacodynamics @utilizes
ln med:system:western_medicine med:system:kampo @contrasts_with_in_approach
ln med:system:western_medicine med:system:ayurveda @contrasts_with_in_approach
