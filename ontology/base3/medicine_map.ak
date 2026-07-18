# Akasha ontology — medicine: the general-education-level map.
# The content already exists richly (med:basic/clinical/specialty/evidence/drug/
# pharma/condition/system) but had no spine tying it to med:medicine. This adds the
# divisions and cross-links the existing atoms. med:medicine already exists — only linked.
# General-education breadth; research depth reserved for level-C. Base pack.

ln med:medicine knowledge:branch:applied_science knowledge:in_branch
ln med:medicine bio:biology thesaurus:related
ln med:medicine knowledge:cognitive_science thesaurus:related

# ══ divisions of medicine ══
def "med:division:basic_science" "基礎医学 — the sciences underlying medicine: how the body is built and works, and how disease arises."
ln med:division:basic_science med:medicine sys:part_of
ln med:basic:anatomy med:division:basic_science sys:part_of
ln med:basic:physiology med:division:basic_science sys:part_of
ln med:basic:pathology med:division:basic_science sys:part_of
ln med:basic:pharmacology med:division:basic_science sys:part_of
ln med:basic:immunology med:division:basic_science sys:part_of
ln med:basic:epidemiology med:division:basic_science sys:part_of
ln med:basic:preventive_medicine med:division:basic_science sys:part_of
ln med:basic:public_health med:division:basic_science sys:part_of
ln med:division:basic_science bio:branch:physiology thesaurus:related
ln med:division:basic_science bio:branch:biochemistry thesaurus:related
def "med:division:clinical_practice" "臨床医学 — the work of caring for patients: history, examination, diagnosis and treatment."
ln med:division:clinical_practice med:medicine sys:part_of
ln med:clinical:history_taking med:division:clinical_practice sys:part_of
ln med:clinical:physical_examination med:division:clinical_practice sys:part_of
ln med:clinical:vital_signs med:division:clinical_practice sys:part_of
ln med:clinical:diagnosis med:division:clinical_practice sys:part_of
ln med:clinical:differential_diagnosis med:division:clinical_practice sys:part_of
ln med:clinical:clinical_reasoning med:division:clinical_practice sys:part_of
ln med:clinical:treatment med:division:clinical_practice sys:part_of
ln med:clinical:prognosis med:division:clinical_practice sys:part_of
ln med:clinical:prescription med:division:clinical_practice sys:part_of
ln med:clinical:referral med:division:clinical_practice sys:part_of
ln med:clinical:informed_consent med:division:clinical_practice sys:part_of
def "med:division:specialties" "診療科 — the branches of clinical medicine by body system, age or method."
ln med:division:specialties med:medicine sys:part_of
ln med:specialty:internal_medicine med:division:specialties sys:part_of
ln med:specialty:surgery med:division:specialties sys:part_of
ln med:specialty:pediatrics med:division:specialties sys:part_of
ln med:specialty:obstetrics_gynecology med:division:specialties sys:part_of
ln med:specialty:psychiatry med:division:specialties sys:part_of
ln med:specialty:neurology med:division:specialties sys:part_of
ln med:specialty:cardiology med:division:specialties sys:part_of
ln med:specialty:oncology med:division:specialties sys:part_of
ln med:specialty:radiology med:division:specialties sys:part_of
ln med:specialty:pathology med:division:specialties sys:part_of
ln med:specialty:anesthesiology med:division:specialties sys:part_of
ln med:specialty:emergency_medicine med:division:specialties sys:part_of
ln med:specialty:family_medicine med:division:specialties sys:part_of
ln med:specialty:geriatrics med:division:specialties sys:part_of
ln med:specialty:public_health_medicine med:division:specialties sys:part_of
def "med:division:therapeutics" "治療学・薬理 — how disease is treated, above all with drugs."
ln med:division:therapeutics med:medicine sys:part_of
ln med:drug:aspirin med:division:therapeutics sys:part_of
ln med:drug:nsaid med:division:therapeutics sys:part_of
ln med:drug:statin med:division:therapeutics sys:part_of
ln med:drug:beta_blocker med:division:therapeutics sys:part_of
ln med:drug:ssri med:division:therapeutics sys:part_of
ln med:drug:l_dopa med:division:therapeutics sys:part_of
ln med:pharma:pharmacodynamics med:division:therapeutics sys:part_of
ln med:pharma:pharmacokinetics med:division:therapeutics sys:part_of
ln med:pharma:agonist med:division:therapeutics sys:part_of
ln med:pharma:antagonist med:division:therapeutics sys:part_of
ln med:division:therapeutics chem:branch:biochemistry thesaurus:related
def "med:division:evidence" "根拠に基づく医療 (EBM) — grounding practice in the best current research."
ln med:division:evidence med:medicine sys:part_of
ln med:evidence:evidence_based_medicine med:division:evidence sys:part_of
ln med:evidence:randomized_controlled_trial med:division:evidence sys:part_of
ln med:evidence:systematic_review med:division:evidence sys:part_of
ln med:evidence:meta_analysis med:division:evidence sys:part_of
ln med:evidence:cohort_study med:division:evidence sys:part_of
ln med:evidence:clinical_guideline med:division:evidence sys:part_of
ln med:evidence:biostatistics med:division:evidence sys:part_of
ln med:evidence:placebo med:division:evidence sys:part_of
ln med:division:evidence math:statistics thesaurus:related
ln med:division:evidence dh:lens:statistical_inference thesaurus:related
def "med:division:disease" "疾病学 — the diseases medicine confronts."
ln med:division:disease med:medicine sys:part_of
ln med:condition:diabetes med:division:disease sys:part_of
ln med:condition:atherosclerosis med:division:disease sys:part_of
ln med:condition:osteoporosis med:division:disease sys:part_of
ln med:condition:anemia med:division:disease sys:part_of
ln med:condition:scurvy med:division:disease sys:part_of
ln med:condition:kwashiorkor med:division:disease sys:part_of
ln med:condition:protein_deficiency med:division:disease sys:part_of
ln med:condition:night_blindness med:division:disease sys:part_of
ln med:condition:famine med:division:disease sys:part_of
ln med:division:disease nutrisci thesaurus:related
def "med:division:traditions" "医学の諸伝統 — the world's systems of medicine, Western and other."
ln med:division:traditions med:medicine sys:part_of
ln med:system:western_medicine med:division:traditions sys:part_of
ln med:system:tcm med:division:traditions sys:part_of
ln med:system:kampo med:division:traditions sys:part_of
ln med:system:ayurveda med:division:traditions sys:part_of
ln med:system:medical_astrology med:division:traditions sys:part_of
ln med:concept:hippocratic_oath med:division:traditions sys:part_of
ln med:concept:dosha med:division:traditions sys:part_of
ln med:concept:qi_blood_fluid med:division:traditions sys:part_of
ln med:division:traditions tcm:action:clear_heat thesaurus:related
ln med:division:traditions anthro:concept:magic_religion thesaurus:related
def "med:division:allied_health" "看護・ケア・生体医工 — the professions and technologies allied to medicine."
ln med:division:allied_health med:medicine sys:part_of
ln med:division:allied_health nursing:holistic_care thesaurus:related
ln med:division:allied_health care:care_plan thesaurus:related
ln med:division:allied_health bme:artificial_organ thesaurus:related
ln med:division:allied_health eng:branch:biomedical thesaurus:related
ln med:specialty:psychiatry psy:field:clinical thesaurus:related
ln med:specialty:neurology neuro thesaurus:related
ln med:basic:anatomy bio:branch:physiology thesaurus:related
ln med:basic:epidemiology dh:family:quantitative thesaurus:related

# ══ founders (new) ══
def "person:hippocrates" "Greek physician (c.460-370 BCE) held as the father of Western medicine; the ethic of the Hippocratic Oath bears his name."
ln person:hippocrates person:figure thesaurus:related
ln person:hippocrates person:field:medicine person:worked_in
ln person:hippocrates med:medicine person:worked_in
ln person:hippocrates med:concept:hippocratic_oath thesaurus:related
ln person:hippocrates hist:period:classical_antiquity person:active_in
def "person:florence_nightingale" "English reformer (1820-1910), founder of modern nursing and a pioneer of medical statistics and hospital sanitation."
ln person:florence_nightingale person:figure thesaurus:related
ln person:florence_nightingale person:field:medicine person:worked_in
ln person:florence_nightingale med:division:allied_health thesaurus:related
ln person:florence_nightingale med:evidence:biostatistics thesaurus:related
ln person:florence_nightingale hist:period:industrial_revolution person:active_in
