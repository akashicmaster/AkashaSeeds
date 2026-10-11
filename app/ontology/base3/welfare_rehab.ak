# Akasha ontology — social welfare, rehabilitation, special education, disability.
# Deepens the care/welfare side, bridged to gov:welfare/benefit, socio:inequality,
# care:/nursing:/med:, occupation:social_worker/therapist, pedagogy: and devpsy:.
# Base pack.

def "socwork" "Social welfare & social work — organised support for wellbeing and against hardship (社会福祉)."
ln socwork gov:function:welfare thesaurus:related
ln socwork occupation:social_worker thesaurus:related

def "socwork:social_welfare" "Society's systems for meeting basic needs and reducing hardship (社会福祉)."
ln socwork:social_welfare socwork thesaurus:related
def "socwork:social_work" "The profession helping people cope with life challenges (ソーシャルワーク)."
ln socwork:social_work socwork thesaurus:related
def "socwork:welfare_state" "A state taking responsibility for citizens' welfare (福祉国家)."
ln socwork:welfare_state socwork thesaurus:related
ln socwork:welfare_state gov:benefit:social_security thesaurus:related
ln socwork:welfare_state admin:country thesaurus:related
def "socwork:social_services" "Public services supporting vulnerable people."
ln socwork:social_services socwork thesaurus:related
def "socwork:case_work" "Working with an individual/family to assess and meet needs."
ln socwork:case_work socwork thesaurus:related
ln socwork:case_work care:care_manager thesaurus:related
def "socwork:child_welfare" "Protecting and supporting children (児童福祉)."
ln socwork:child_welfare socwork thesaurus:related
ln socwork:child_welfare kin:child_of thesaurus:related
ln socwork:child_welfare gov:benefit:child_allowance thesaurus:related
def "socwork:elderly_welfare" "Support for older people (高齢者福祉)."
ln socwork:elderly_welfare socwork thesaurus:related
ln socwork:elderly_welfare care:long_term_care thesaurus:related
ln socwork:elderly_welfare gov:benefit:pension thesaurus:related
def "socwork:disability_welfare" "Support for people with disabilities (障害者福祉)."
ln socwork:disability_welfare socwork thesaurus:related
ln socwork:disability_welfare gov:benefit:disability_benefit thesaurus:related
ln socwork:disability_welfare special:disability thesaurus:related
def "socwork:poverty" "Lack of the resources for a decent life (貧困)."
ln socwork:poverty socwork thesaurus:related
ln socwork:poverty socio:inequality thesaurus:related
ln socwork:poverty gov:benefit:public_assistance thesaurus:related
def "socwork:social_exclusion" "Being shut out of normal social participation."
ln socwork:social_exclusion socwork thesaurus:related
ln socwork:social_exclusion socio:inequality thesaurus:related
ln socwork:social_exclusion socio:deviance thesaurus:related
def "socwork:safety_net" "The programmes catching those who fall into hardship (セーフティネット)."
ln socwork:safety_net socwork thesaurus:related
ln socwork:safety_net insur:social_insurance thesaurus:related
ln socwork:safety_net gov:benefit:unemployment_benefit thesaurus:related
def "socwork:empowerment" "Building people's capacity to control their own lives."
ln socwork:empowerment socwork thesaurus:related
def "socwork:advocacy" "Speaking and acting for others' rights and needs."
ln socwork:advocacy socwork thesaurus:related
# ── rehabilitation ──
def "rehab" "Rehabilitation — restoring function and participation after illness or injury (リハビリ)."
ln rehab med:medicine thesaurus:related
ln rehab occupation:therapist thesaurus:related

def "rehab:physical_therapy" "Restoring movement and strength (理学療法/PT)."
ln rehab:physical_therapy rehab thesaurus:related
ln rehab:physical_therapy care:frailty thesaurus:related
ln rehab:physical_therapy med:basic:anatomy thesaurus:related
def "rehab:occupational_therapy" "Regaining daily-living and work skills (作業療法/OT)."
ln rehab:occupational_therapy rehab thesaurus:related
ln rehab:occupational_therapy care:activities_of_daily_living thesaurus:related
def "rehab:speech_therapy" "Treating speech, language and swallowing (言語療法/ST)."
ln rehab:speech_therapy rehab thesaurus:related
ln rehab:speech_therapy devpsy:language_acquisition thesaurus:related
ln rehab:speech_therapy psych:developmental_psychology thesaurus:related
def "rehab:rehabilitation_medicine" "The medical specialty of functional recovery (リハビリ医学)."
ln rehab:rehabilitation_medicine rehab thesaurus:related
def "rehab:assistive_technology" "Devices that support function — wheelchairs, hearing aids, AAC (福祉用具)."
ln rehab:assistive_technology rehab thesaurus:related
ln rehab:assistive_technology special:accessibility thesaurus:related
ln rehab:assistive_technology special:universal_design thesaurus:related
def "rehab:prosthetics" "Artificial limbs restoring lost function."
ln rehab:prosthetics rehab thesaurus:related
def "rehab:mobility_training" "Relearning safe movement and transfers."
ln rehab:mobility_training rehab thesaurus:related
def "rehab:functional_recovery" "Regaining the ability to perform daily activities."
ln rehab:functional_recovery rehab thesaurus:related
ln rehab:functional_recovery neuro:neuroplasticity thesaurus:related
def "rehab:adl_training" "Practising activities of daily living toward independence."
ln rehab:adl_training rehab thesaurus:related
ln rehab:adl_training care:activities_of_daily_living thesaurus:related
ln rehab:adl_training nursing:patient_care thesaurus:related
# ── special education & disability ──
def "special" "Special needs education & disability support (特別支援教育・障害)."
ln special pedagogy:special_education thesaurus:related
ln special school:school_counselor thesaurus:related

def "special:disability" "A long-term impairment interacting with barriers to limit participation (障害)."
ln special:disability special thesaurus:related
def "special:developmental_disability" "A disability arising in the developmental period (発達障害)."
ln special:developmental_disability special thesaurus:related
ln special:developmental_disability devpsy:developmental_milestone thesaurus:related
ln special:developmental_disability devpsy:theory_of_mind thesaurus:related
def "special:learning_disability" "Specific difficulty in learning despite ability (学習障害/LD)."
ln special:learning_disability special thesaurus:related
ln special:learning_disability edupsy:learning_theory thesaurus:related
ln special:learning_disability special:individualized_education_program thesaurus:related
def "special:intellectual_disability" "Significant limits in intellectual and adaptive functioning (知的障害)."
ln special:intellectual_disability special thesaurus:related
def "special:autism_spectrum" "A spectrum of differences in social communication and behaviour (自閉スペクトラム症)."
ln special:autism_spectrum special thesaurus:related
ln special:autism_spectrum devpsy:theory_of_mind thesaurus:related
ln special:autism_spectrum counsel:family_therapy thesaurus:related
def "special:adhd" "Attention-deficit/hyperactivity — inattention and impulsivity (ADHD)."
ln special:adhd special thesaurus:related
ln special:adhd psy:attention thesaurus:related
ln special:adhd psych:clinical_psychology thesaurus:related
def "special:sensory_impairment" "Impairment of hearing or vision."
ln special:sensory_impairment special thesaurus:related
def "special:individualized_education_program" "A tailored plan for a learner's special needs (個別支援計画/IEP)."
ln special:individualized_education_program special thesaurus:related
def "special:inclusion" "Educating and including learners of all abilities together (インクルージョン)."
ln special:inclusion special thesaurus:related
ln special:inclusion socio:inequality thesaurus:related
ln special:inclusion pedagogy:inclusive_education thesaurus:related
def "special:accessibility" "Designing so people with disabilities can participate (アクセシビリティ)."
ln special:accessibility special thesaurus:related
ln special:accessibility civ:accessibility thesaurus:related
ln special:accessibility rehab:assistive_technology thesaurus:related
def "special:reasonable_accommodation" "Adjustments enabling equal participation (合理的配慮)."
ln special:reasonable_accommodation special thesaurus:related
ln special:reasonable_accommodation special:accessibility thesaurus:related
def "special:universal_design" "Designing for the widest range of people from the start."
ln special:universal_design special thesaurus:related
def "special:early_intervention" "Support in the early years to aid development."
ln special:early_intervention special thesaurus:related
ln special:early_intervention devpsy:critical_period thesaurus:related
ln special:early_intervention devpsy:early_childhood thesaurus:related
def "special:social_model_disability" "The view that disability arises from societal barriers, not just impairment."
ln special:social_model_disability special thesaurus:related
ln special:social_model_disability socio:social_constructionism thesaurus:related
ln special:social_model_disability socwork:disability_welfare thesaurus:related
