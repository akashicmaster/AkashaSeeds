# Akasha ontology — clinical psychology & counseling (臨床心理・カウンセリング).
# Bridged to occupation:therapist/school_counselor, social:mentor_of, place:clinic,
# emo:* (the affect layer) and med:. Base pack.

def "psych" "Clinical psychology — assessment and treatment of mental disorder (臨床心理学)."
ln psych occupation:therapist thesaurus:related
ln psych med:specialty:psychiatry thesaurus:related

def "psych:mental_health" "A state of psychological well-being (メンタルヘルス)."
ln psych:mental_health psych thesaurus:related
ln psych:mental_health work:work_stress thesaurus:related
ln psych:mental_health emo:trust thesaurus:related
def "psych:psychopathology" "The study of mental disorders (精神病理学)."
ln psych:psychopathology psych thesaurus:related
def "psych:psychological_assessment" "Evaluating a person's psychological functioning."
ln psych:psychological_assessment psych thesaurus:related
def "psych:psychometrics" "The measurement of psychological traits and abilities."
ln psych:psychometrics psych thesaurus:related
ln psych:psychometrics research:method:quantitative thesaurus:related
def "psych:depression" "A mood disorder of persistent low mood and loss of interest (うつ)."
ln psych:depression psych thesaurus:related
ln psych:depression emo:anxiety thesaurus:related
ln psych:depression med:drug:ssri thesaurus:related
def "psych:anxiety_disorder" "Disorders of excessive fear and worry (不安障害)."
ln psych:anxiety_disorder psych thesaurus:related
ln psych:anxiety_disorder emo:anxiety thesaurus:related
def "psych:ptsd" "Post-traumatic stress disorder after overwhelming events."
ln psych:ptsd psych thesaurus:related
ln psych:ptsd emo:anxiety thesaurus:related
def "psych:diagnosis_dsm" "Diagnosis by standardized manuals (DSM/ICD)."
ln psych:diagnosis_dsm psych thesaurus:related
def "psych:clinical_psychology" "The applied field treating psychological distress."
ln psych:clinical_psychology psych thesaurus:related
def "psych:developmental_psychology" "How mind and behaviour change across the lifespan."
ln psych:developmental_psychology psych thesaurus:related
ln psych:developmental_psychology kin:child_of thesaurus:related
ln psych:developmental_psychology school:student thesaurus:related
# ── counseling & psychotherapy (カウンセリング・心理療法) ──
def "counsel" "Counseling — a helping relationship supporting change and coping (カウンセリング)."
ln counsel psych thesaurus:related
ln counsel social:mentor_of thesaurus:related
ln counsel school:school_counselor thesaurus:related

def "counsel:counseling" "A professional helping conversation for personal difficulties (カウンセリング)."
ln counsel:counseling counsel thesaurus:related
def "counsel:psychotherapy" "Treatment of mental distress by psychological means (心理療法)."
ln counsel:psychotherapy counsel thesaurus:related
def "counsel:therapeutic_alliance" "The trusting bond between therapist and client, key to outcome."
ln counsel:therapeutic_alliance counsel thesaurus:related
def "counsel:cognitive_behavioral_therapy" "Changing unhelpful thoughts and behaviours (認知行動療法/CBT)."
ln counsel:cognitive_behavioral_therapy counsel thesaurus:related
ln counsel:cognitive_behavioral_therapy psych:depression thesaurus:related
ln counsel:cognitive_behavioral_therapy psych:anxiety_disorder thesaurus:related
def "counsel:psychoanalysis" "Freud's therapy exploring the unconscious."
ln counsel:psychoanalysis counsel thesaurus:related
ln counsel:psychoanalysis phil:identity thesaurus:related
def "counsel:person_centered_therapy" "Rogers's approach led by the client, built on acceptance."
ln counsel:person_centered_therapy counsel thesaurus:related
ln counsel:person_centered_therapy emo:trust thesaurus:related
def "counsel:active_listening" "Attentive, reflecting listening that shows understanding (傾聴)."
ln counsel:active_listening counsel thesaurus:related
ln counsel:active_listening social:mentor_of thesaurus:related
def "counsel:empathy" "Understanding and sharing another's feelings — the counselor's core skill."
ln counsel:empathy counsel thesaurus:related
ln counsel:empathy emo:empathetic_pain thesaurus:related
ln counsel:empathy social:friend_of thesaurus:related
def "counsel:unconditional_positive_regard" "Rogers's non-judgemental acceptance of the client."
ln counsel:unconditional_positive_regard counsel thesaurus:related
def "counsel:transference" "The client's redirection of feelings onto the therapist."
ln counsel:transference counsel thesaurus:related
def "counsel:group_therapy" "Therapy conducted with a group of clients."
ln counsel:group_therapy counsel thesaurus:related
def "counsel:family_therapy" "Therapy treating the family system, not just the individual."
ln counsel:family_therapy counsel thesaurus:related
ln counsel:family_therapy kin:parent_of thesaurus:related
ln counsel:family_therapy socio:primary_group thesaurus:related
def "counsel:crisis_intervention" "Immediate support in acute psychological crisis."
ln counsel:crisis_intervention counsel thesaurus:related
ln counsel:crisis_intervention gov:emergency_call thesaurus:related
def "counsel:motivational_interviewing" "A collaborative method strengthening motivation to change."
ln counsel:motivational_interviewing counsel thesaurus:related
def "counsel:mindfulness" "Non-judgemental present-moment awareness used therapeutically (マインドフルネス)."
ln counsel:mindfulness counsel thesaurus:related
ln counsel:mindfulness work:work_life_balance thesaurus:related
def "counsel:confidentiality" "The client's right to privacy of what is disclosed."
ln counsel:confidentiality counsel thesaurus:related
ln counsel:confidentiality socio:role thesaurus:related
def "counsel:counselor" "The professional who provides counseling."
ln counsel:counselor counsel thesaurus:related
ln counsel:counselor occupation:therapist thesaurus:related
ln counsel:counselor school:school_counselor thesaurus:related
def "counsel:client" "The person receiving counseling."
ln counsel:client counsel thesaurus:related
