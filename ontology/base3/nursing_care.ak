# Akasha ontology — nursing science & long-term care.
# Bridged to occupation:nurse/caregiver, place:hospital/nursing_home, social:
# caregiver_of/care_recipient_of, gov:welfare and med:. Base pack.

def "nursing" "Nursing — the science and practice of caring for the sick and well (看護学)."
ln nursing occupation:nurse thesaurus:related
ln nursing social:caregiver_of thesaurus:related
ln nursing place:hospital thesaurus:related

# ── nursing process ──
def "nursing:nursing_assessment" "Gathering the patient's health data (アセスメント)."
ln nursing:nursing_assessment nursing thesaurus:related
ln nursing:nursing_assessment nursing:nursing_diagnosis chrono:before
def "nursing:nursing_diagnosis" "The nurse's judgement of the patient's responses to health problems."
ln nursing:nursing_diagnosis nursing thesaurus:related
ln nursing:nursing_diagnosis nursing:care_planning chrono:before
def "nursing:care_planning" "Setting goals and nursing interventions (看護計画)."
ln nursing:care_planning nursing thesaurus:related
ln nursing:care_planning nursing:implementation chrono:before
def "nursing:implementation" "Carrying out the planned care."
ln nursing:implementation nursing thesaurus:related
ln nursing:implementation nursing:evaluation chrono:before
def "nursing:evaluation" "Judging whether goals were met, and revising."
ln nursing:evaluation nursing thesaurus:related
# ── nursing practice & theory ──
def "nursing:patient_care" "Direct care of the patient's needs (患者ケア)."
ln nursing:patient_care nursing thesaurus:related
def "nursing:holistic_care" "Caring for body, mind and social context together."
ln nursing:holistic_care nursing thesaurus:related
ln nursing:holistic_care care:long_term_care thesaurus:related
def "nursing:evidence_based_nursing" "Nursing guided by research evidence."
ln nursing:evidence_based_nursing nursing thesaurus:related
ln nursing:evidence_based_nursing med:evidence:evidence_based_medicine thesaurus:related
def "nursing:medication_administration" "Safely giving prescribed drugs (与薬)."
ln nursing:medication_administration nursing thesaurus:related
ln nursing:medication_administration med:clinical:prescription thesaurus:related
def "nursing:wound_care" "Management of wounds and dressings."
ln nursing:wound_care nursing thesaurus:related
def "nursing:patient_advocacy" "Acting to protect the patient's rights and interests."
ln nursing:patient_advocacy nursing thesaurus:related
ln nursing:patient_advocacy social:patient_of thesaurus:related
def "nursing:nursing_ethics" "The ethics of the nurse–patient relationship."
ln nursing:nursing_ethics nursing thesaurus:related
def "nursing:triage" "Prioritising patients by urgency (トリアージ)."
ln nursing:triage nursing thesaurus:related
ln nursing:triage place:emergency_room thesaurus:related
ln nursing:triage gov:service:ambulance_service thesaurus:related
def "nursing:nightingale" "Florence Nightingale — founder of modern nursing and of hospital reform."
ln nursing:nightingale nursing thesaurus:related
def "nursing:self_care_deficit_theory" "Orem's theory: nursing meets the self-care a patient cannot (セルフケア理論)."
ln nursing:self_care_deficit_theory nursing thesaurus:related
def "nursing:theory_of_caring" "Watson's theory placing caring at the heart of nursing."
ln nursing:theory_of_caring nursing thesaurus:related
# ── long-term care & gerontology ──
def "care" "Long-term care — sustained support for daily living (介護)."
ln care occupation:caregiver thesaurus:related
ln care place:nursing_home thesaurus:related
ln care social:caregiver_of thesaurus:related
ln care social:care_recipient_of thesaurus:related

def "care:long_term_care" "Ongoing help with living for the frail, disabled or chronically ill (長期介護)."
ln care:long_term_care care thesaurus:related
def "care:gerontology" "The scientific study of ageing (老年学)."
ln care:gerontology care thesaurus:related
ln care:gerontology med:specialty:geriatrics thesaurus:related
def "care:geriatric_care" "Health and social care of older people."
ln care:geriatric_care care thesaurus:related
def "care:activities_of_daily_living" "Basic self-care tasks — eating, bathing, dressing, toileting (ADL/日常生活動作)."
ln care:activities_of_daily_living care thesaurus:related
ln care:activities_of_daily_living nursing:patient_care thesaurus:related
ln care:activities_of_daily_living supply:towel thesaurus:related
def "care:instrumental_adl" "Complex daily tasks — cooking, shopping, managing money (IADL)."
ln care:instrumental_adl care thesaurus:related
def "care:care_manager" "One who assesses needs and coordinates a care plan (ケアマネジャー)."
ln care:care_manager care thesaurus:related
ln care:care_manager occupation:social_worker thesaurus:related
ln care:care_manager care:care_plan thesaurus:related
def "care:care_plan" "An individualised plan of long-term care services (ケアプラン)."
ln care:care_plan care thesaurus:related
def "care:home_care" "Care delivered in the person's own home (在宅介護)."
ln care:home_care care thesaurus:related
ln care:home_care home:dwelling:detached_house thesaurus:related
def "care:day_care_service" "Daytime care and activity outside the home (デイサービス)."
ln care:day_care_service care thesaurus:related
ln care:day_care_service place:nursing_home thesaurus:related
ln care:day_care_service gov:function:welfare thesaurus:related
def "care:respite_care" "Temporary care giving family carers a break."
ln care:respite_care care thesaurus:related
def "care:palliative_care" "Care relieving suffering in serious illness (緩和ケア)."
ln care:palliative_care care thesaurus:related
ln care:palliative_care med:specialty:geriatrics thesaurus:related
def "care:hospice" "Care for the dying, focused on comfort and dignity (ホスピス)."
ln care:hospice care thesaurus:related
def "care:end_of_life_care" "Care in the final phase of life (終末期ケア)."
ln care:end_of_life_care care thesaurus:related
def "care:dementia_care" "Care tailored to people living with dementia (認知症ケア)."
ln care:dementia_care care thesaurus:related
ln care:dementia_care psych:mental_health thesaurus:related
def "care:long_term_care_insurance" "Public insurance funding long-term care (介護保険)."
ln care:long_term_care_insurance care thesaurus:related
ln care:long_term_care_insurance insur:social_insurance thesaurus:related
ln care:long_term_care_insurance gov:benefit:pension thesaurus:related
def "care:assisted_living" "Housing with support for daily living."
ln care:assisted_living care thesaurus:related
def "care:family_caregiving" "Unpaid care given by relatives (家族介護)."
ln care:family_caregiving care thesaurus:related
ln care:family_caregiving kin:child_of thesaurus:related
ln care:family_caregiving social:caregiver_of thesaurus:related
def "care:frailty" "Reduced reserve and resilience in old age."
ln care:frailty care thesaurus:related
