# Akasha ontology — human relationships (the interpersonal web beyond kin).
# Extends kin.ak's social: relations and classifies ALL person-to-person
# relations by kind (kinship/peer/romantic/professional/hierarchical/care/
# adversarial/civic) × polarity (positive/neutral/negative). Base pack.

def "rel_kind:kinship" "kinship relationship."
def "rel_kind:peer" "peer relationship."
def "rel_kind:romantic" "romantic relationship."
def "rel_kind:professional" "professional relationship."
def "rel_kind:hierarchical" "hierarchical relationship."
def "rel_kind:care" "care relationship."
def "rel_kind:adversarial" "adversarial relationship."
def "rel_kind:civic" "civic relationship."
def "rel_polarity:positive" "positive affect."
def "rel_polarity:neutral" "neutral affect."
def "rel_polarity:negative" "negative affect."

def "social:lover_of" "Romantic lovers."
ln social:lover_of social:lover_of sys:synonym   # symmetric
ln social:lover_of emo:romance calc:associated_with
ln social:lover_of emo:adoration calc:associated_with
def "social:fiance_of" "Engaged to marry."
ln social:fiance_of social:fiance_of sys:synonym   # symmetric
ln social:fiance_of emo:romance calc:associated_with
ln social:fiance_of emo:anticipation calc:associated_with
def "social:ex_of" "A former partner."
ln social:ex_of social:ex_of sys:synonym   # symmetric
ln social:ex_of emo:nostalgia calc:associated_with
def "social:rival_of" "Competing against another."
ln social:rival_of social:rival_of sys:synonym   # symmetric
ln social:rival_of emo:anticipation calc:associated_with
def "social:enemy_of" "In hostility with another."
ln social:enemy_of social:enemy_of sys:synonym   # symmetric
ln social:enemy_of emo:anger calc:associated_with
def "social:ally_of" "Bound in common cause."
ln social:ally_of social:ally_of sys:synonym   # symmetric
ln social:ally_of emo:trust calc:associated_with
def "social:roommate_of" "Sharing a dwelling."
ln social:roommate_of social:roommate_of sys:synonym   # symmetric
ln social:roommate_of emo:trust calc:associated_with
def "social:stranger_of" "Unknown to each other."
ln social:stranger_of social:stranger_of sys:synonym   # symmetric
def "social:employer_of" "Hiring another's labour."
ln social:employer_of social:employee_of sys:antonym
ln social:employer_of emo:responsibility calc:associated_with
def "social:employee_of" "Working for an employer."
ln social:employee_of social:employer_of sys:antonym
ln social:employee_of emo:anticipation calc:associated_with
ln social:employee_of emo:anxiety calc:associated_with
def "social:boss_of" "Holding authority at work over another."
ln social:boss_of social:subordinate_of sys:antonym
ln social:boss_of emo:responsibility calc:associated_with
def "social:subordinate_of" "Reporting to a boss."
ln social:subordinate_of social:boss_of sys:antonym
ln social:subordinate_of emo:anxiety calc:associated_with
ln social:subordinate_of emo:admiration calc:associated_with
def "social:senior_of" "先輩 — the senior in a seniority relation."
ln social:senior_of social:junior_of sys:antonym
ln social:senior_of emo:responsibility calc:associated_with
ln social:senior_of emo:admiration calc:associated_with
def "social:junior_of" "後輩 — the junior in a seniority relation."
ln social:junior_of social:senior_of sys:antonym
ln social:junior_of emo:admiration calc:associated_with
ln social:junior_of emo:anticipation calc:associated_with
def "social:landlord_of" "Renting property to another."
ln social:landlord_of social:tenant_of sys:antonym
ln social:landlord_of emo:responsibility calc:associated_with
def "social:tenant_of" "Renting a dwelling from a landlord."
ln social:tenant_of social:landlord_of sys:antonym
ln social:tenant_of emo:trust calc:associated_with
ln social:tenant_of emo:anxiety calc:associated_with

# ── classify every relation by kind × polarity ──
ln kin:parent_of rel_kind:kinship social:rel_kind
ln kin:parent_of rel_polarity:positive social:rel_polarity
ln kin:child_of rel_kind:kinship social:rel_kind
ln kin:child_of rel_polarity:positive social:rel_polarity
ln kin:sibling_of rel_kind:kinship social:rel_kind
ln kin:sibling_of rel_polarity:positive social:rel_polarity
ln kin:ancestor_of rel_kind:kinship social:rel_kind
ln kin:ancestor_of rel_polarity:neutral social:rel_polarity
ln kin:descendant_of rel_kind:kinship social:rel_kind
ln kin:descendant_of rel_polarity:neutral social:rel_polarity
ln kin:partner_of rel_kind:romantic social:rel_kind
ln kin:partner_of rel_polarity:positive social:rel_polarity
ln kin:grandparent_of rel_kind:kinship social:rel_kind
ln kin:grandparent_of rel_polarity:positive social:rel_polarity
ln kin:grandchild_of rel_kind:kinship social:rel_kind
ln kin:grandchild_of rel_polarity:positive social:rel_polarity
ln kin:auncle_of rel_kind:kinship social:rel_kind
ln kin:auncle_of rel_polarity:positive social:rel_polarity
ln kin:nibling_of rel_kind:kinship social:rel_kind
ln kin:nibling_of rel_polarity:positive social:rel_polarity
ln kin:cousin_of rel_kind:kinship social:rel_kind
ln kin:cousin_of rel_polarity:neutral social:rel_polarity
ln social:friend_of rel_kind:peer social:rel_kind
ln social:friend_of rel_polarity:positive social:rel_polarity
ln social:childhood_friend_of rel_kind:peer social:rel_kind
ln social:childhood_friend_of rel_polarity:positive social:rel_polarity
ln social:classmate_of rel_kind:peer social:rel_kind
ln social:classmate_of rel_polarity:neutral social:rel_polarity
ln social:colleague_of rel_kind:professional social:rel_kind
ln social:colleague_of rel_polarity:neutral social:rel_polarity
ln social:neighbor_of rel_kind:peer social:rel_kind
ln social:neighbor_of rel_polarity:neutral social:rel_polarity
ln social:acquaintance_of rel_kind:peer social:rel_kind
ln social:acquaintance_of rel_polarity:neutral social:rel_polarity
ln social:mentor_of rel_kind:hierarchical social:rel_kind
ln social:mentor_of rel_polarity:positive social:rel_polarity
ln social:mentee_of rel_kind:hierarchical social:rel_kind
ln social:mentee_of rel_polarity:positive social:rel_polarity
ln social:caregiver_of rel_kind:care social:rel_kind
ln social:caregiver_of rel_polarity:positive social:rel_polarity
ln social:care_recipient_of rel_kind:care social:rel_kind
ln social:care_recipient_of rel_polarity:positive social:rel_polarity
ln social:doctor_of rel_kind:care social:rel_kind
ln social:doctor_of rel_polarity:neutral social:rel_polarity
ln social:patient_of rel_kind:care social:rel_kind
ln social:patient_of rel_polarity:neutral social:rel_polarity
ln social:teacher_of rel_kind:hierarchical social:rel_kind
ln social:teacher_of rel_polarity:positive social:rel_polarity
ln social:student_of rel_kind:hierarchical social:rel_kind
ln social:student_of rel_polarity:positive social:rel_polarity
ln social:leader_of rel_kind:hierarchical social:rel_kind
ln social:leader_of rel_polarity:neutral social:rel_polarity
ln social:member_of rel_kind:civic social:rel_kind
ln social:member_of rel_polarity:neutral social:rel_polarity
ln social:lover_of rel_kind:romantic social:rel_kind
ln social:lover_of rel_polarity:positive social:rel_polarity
ln social:fiance_of rel_kind:romantic social:rel_kind
ln social:fiance_of rel_polarity:positive social:rel_polarity
ln social:ex_of rel_kind:romantic social:rel_kind
ln social:ex_of rel_polarity:neutral social:rel_polarity
ln social:rival_of rel_kind:adversarial social:rel_kind
ln social:rival_of rel_polarity:negative social:rel_polarity
ln social:enemy_of rel_kind:adversarial social:rel_kind
ln social:enemy_of rel_polarity:negative social:rel_polarity
ln social:ally_of rel_kind:adversarial social:rel_kind
ln social:ally_of rel_polarity:positive social:rel_polarity
ln social:roommate_of rel_kind:peer social:rel_kind
ln social:roommate_of rel_polarity:neutral social:rel_polarity
ln social:stranger_of rel_kind:peer social:rel_kind
ln social:stranger_of rel_polarity:neutral social:rel_polarity
ln social:employer_of rel_kind:professional social:rel_kind
ln social:employer_of rel_polarity:neutral social:rel_polarity
ln social:employee_of rel_kind:professional social:rel_kind
ln social:employee_of rel_polarity:neutral social:rel_polarity
ln social:boss_of rel_kind:hierarchical social:rel_kind
ln social:boss_of rel_polarity:neutral social:rel_polarity
ln social:subordinate_of rel_kind:hierarchical social:rel_kind
ln social:subordinate_of rel_polarity:neutral social:rel_polarity
ln social:senior_of rel_kind:hierarchical social:rel_kind
ln social:senior_of rel_polarity:neutral social:rel_polarity
ln social:junior_of rel_kind:hierarchical social:rel_kind
ln social:junior_of rel_polarity:neutral social:rel_polarity
ln social:landlord_of rel_kind:professional social:rel_kind
ln social:landlord_of rel_polarity:neutral social:rel_polarity
ln social:tenant_of rel_kind:professional social:rel_kind
ln social:tenant_of rel_polarity:neutral social:rel_polarity
