# Akasha ontology — clinical medicine & medical science (医学).
# The academic/clinical discipline, on the small existing med:* (systems/
# conditions/drugs). Bridged to occupation:doctor, place:hospital, social:
# doctor_of, research: and bio:. Base pack.

def "med:medicine" "Medicine — the science and practice of diagnosing, treating and preventing disease (医学)."
ln med:medicine occupation:doctor thesaurus:related
ln med:medicine place:hospital thesaurus:related
ln med:medicine med:system:western_medicine thesaurus:related

# ── specialties (診療科) ──
def "med:specialty:internal_medicine" "Non-surgical care of adult disease (内科)."
ln med:specialty:internal_medicine med:medicine thesaurus:related
def "med:specialty:surgery" "Operative treatment of disease (外科)."
ln med:specialty:surgery med:medicine thesaurus:related
def "med:specialty:pediatrics" "Medicine of children (小児科)."
ln med:specialty:pediatrics med:medicine thesaurus:related
def "med:specialty:psychiatry" "Medicine of mental disorder (精神科)."
ln med:specialty:psychiatry med:medicine thesaurus:related
ln med:specialty:psychiatry psych:clinical_psychology thesaurus:related
ln med:specialty:psychiatry med:drug:ssri thesaurus:related
def "med:specialty:cardiology" "The heart and circulation (循環器科)."
ln med:specialty:cardiology med:medicine thesaurus:related
def "med:specialty:oncology" "Cancer medicine (腫瘍内科)."
ln med:specialty:oncology med:medicine thesaurus:related
ln med:specialty:oncology med:pharma:pharmacodynamics thesaurus:related
def "med:specialty:neurology" "The nervous system (神経内科)."
ln med:specialty:neurology med:medicine thesaurus:related
def "med:specialty:obstetrics_gynecology" "Pregnancy and women's health (産婦人科)."
ln med:specialty:obstetrics_gynecology med:medicine thesaurus:related
def "med:specialty:geriatrics" "Medicine of old age (老年医学)."
ln med:specialty:geriatrics med:medicine thesaurus:related
ln med:specialty:geriatrics care:gerontology thesaurus:related
ln med:specialty:geriatrics place:nursing_home thesaurus:related
def "med:specialty:emergency_medicine" "Acute and urgent care (救急医学)."
ln med:specialty:emergency_medicine med:medicine thesaurus:related
ln med:specialty:emergency_medicine place:emergency_room thesaurus:related
ln med:specialty:emergency_medicine gov:service:ambulance_service thesaurus:related
def "med:specialty:radiology" "Imaging-based diagnosis (放射線科)."
ln med:specialty:radiology med:medicine thesaurus:related
def "med:specialty:pathology" "Diagnosis from tissue and lab (病理学)."
ln med:specialty:pathology med:medicine thesaurus:related
def "med:specialty:family_medicine" "Continuing whole-person primary care (総合診療)."
ln med:specialty:family_medicine med:medicine thesaurus:related
def "med:specialty:anesthesiology" "Anaesthesia and perioperative care (麻酔科)."
ln med:specialty:anesthesiology med:medicine thesaurus:related
def "med:specialty:public_health_medicine" "Health of populations (公衆衛生医学)."
ln med:specialty:public_health_medicine med:medicine thesaurus:related
ln med:specialty:public_health_medicine gov:function:public_health thesaurus:related
# ── clinical process (臨床) ──
def "med:clinical:history_taking" "Eliciting the patient's story of illness (問診)."
ln med:clinical:history_taking med:medicine thesaurus:related
def "med:clinical:physical_examination" "Systematic bodily examination (診察)."
ln med:clinical:physical_examination med:medicine thesaurus:related
def "med:clinical:diagnosis" "Identifying the disease from signs, symptoms and tests (診断)."
ln med:clinical:diagnosis med:medicine thesaurus:related
ln med:clinical:diagnosis social:doctor_of thesaurus:related
ln med:clinical:diagnosis research:hypothesis thesaurus:related
def "med:clinical:differential_diagnosis" "The ranked list of possible causes to distinguish."
ln med:clinical:differential_diagnosis med:medicine thesaurus:related
def "med:clinical:prognosis" "The predicted course and outcome (予後)."
ln med:clinical:prognosis med:medicine thesaurus:related
def "med:clinical:treatment" "The intervention to cure or manage disease (治療)."
ln med:clinical:treatment med:medicine thesaurus:related
ln med:clinical:treatment social:patient_of thesaurus:related
def "med:clinical:prescription" "A written order for medication (処方)."
ln med:clinical:prescription med:medicine thesaurus:related
ln med:clinical:prescription med:drug:aspirin thesaurus:related
ln med:clinical:prescription med:pharma:pharmacokinetics thesaurus:related
def "med:clinical:clinical_reasoning" "The thinking that moves from findings to diagnosis and plan."
ln med:clinical:clinical_reasoning med:medicine thesaurus:related
def "med:clinical:vital_signs" "Pulse, blood pressure, temperature, respiration, oxygen (バイタル)."
ln med:clinical:vital_signs med:medicine thesaurus:related
ln med:clinical:vital_signs nursing:nursing_assessment thesaurus:related
def "med:clinical:referral" "Sending a patient to another service or specialist (紹介)."
ln med:clinical:referral med:medicine thesaurus:related
def "med:clinical:informed_consent" "Voluntary agreement to treatment after understanding it (インフォームドコンセント)."
ln med:clinical:informed_consent med:medicine thesaurus:related
ln med:clinical:informed_consent law:concept:legal_personhood thesaurus:related
# ── evidence-based medicine (EBM) ──
def "med:evidence:evidence_based_medicine" "Using the best current research evidence in clinical decisions (EBM)."
ln med:evidence:evidence_based_medicine med:medicine thesaurus:related
def "med:evidence:randomized_controlled_trial" "The gold-standard experiment comparing treatment to control (RCT)."
ln med:evidence:randomized_controlled_trial med:medicine thesaurus:related
ln med:evidence:randomized_controlled_trial research:experiment thesaurus:related
ln med:evidence:randomized_controlled_trial research:control_group thesaurus:related
ln med:evidence:randomized_controlled_trial nutrisci:nutritional_epidemiology thesaurus:related
def "med:evidence:systematic_review" "A rigorous synthesis of all studies on a question."
ln med:evidence:systematic_review med:medicine thesaurus:related
ln med:evidence:systematic_review research:literature_review thesaurus:related
ln med:evidence:systematic_review pub:review_article thesaurus:related
def "med:evidence:meta_analysis" "Statistically combining many studies' results."
ln med:evidence:meta_analysis med:medicine thesaurus:related
ln med:evidence:meta_analysis bib:science_mapping thesaurus:related
def "med:evidence:clinical_guideline" "Evidence-based recommendations for care."
ln med:evidence:clinical_guideline med:medicine thesaurus:related
def "med:evidence:placebo" "An inert treatment used as a control."
ln med:evidence:placebo med:medicine thesaurus:related
def "med:evidence:biostatistics" "Statistics applied to medicine and biology."
ln med:evidence:biostatistics med:medicine thesaurus:related
ln med:evidence:biostatistics research:method:quantitative thesaurus:related
def "med:evidence:cohort_study" "Following groups over time to link exposure and outcome."
ln med:evidence:cohort_study med:medicine thesaurus:related
ln med:evidence:cohort_study nutrisci:nutritional_epidemiology thesaurus:related
# ── basic sciences & public health ──
def "med:basic:anatomy" "The structure of the body (解剖学)."
ln med:basic:anatomy med:medicine thesaurus:related
ln med:basic:anatomy med:medicine thesaurus:related
def "med:basic:physiology" "How the body functions (生理学)."
ln med:basic:physiology med:medicine thesaurus:related
def "med:basic:pathology" "The mechanisms and effects of disease (病理学)."
ln med:basic:pathology med:medicine thesaurus:related
def "med:basic:pharmacology" "How drugs act on the body (薬理学)."
ln med:basic:pharmacology med:medicine thesaurus:related
ln med:basic:pharmacology med:pharma:pharmacodynamics thesaurus:related
ln med:basic:pharmacology med:drug:statin thesaurus:related
def "med:basic:immunology" "The immune system and defence (免疫学)."
ln med:basic:immunology med:medicine thesaurus:related
def "med:basic:epidemiology" "Patterns and causes of disease in populations (疫学)."
ln med:basic:epidemiology med:medicine thesaurus:related
ln med:basic:epidemiology nutrisci:nutritional_epidemiology thesaurus:related
ln med:basic:epidemiology gov:function:public_health thesaurus:related
def "med:basic:public_health" "Protecting and improving population health (公衆衛生)."
ln med:basic:public_health med:medicine thesaurus:related
ln med:basic:public_health gov:function:public_health thesaurus:related
def "med:basic:preventive_medicine" "Preventing disease before it starts (予防医学)."
ln med:basic:preventive_medicine med:medicine thesaurus:related
ln med:basic:preventive_medicine nutrisci:functional_food thesaurus:related
