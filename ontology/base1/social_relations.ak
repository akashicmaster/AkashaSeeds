# Akasha ontology — social relations beyond kin (neighbours, peers, care).
# Extends kin.ak's social: relations. Symmetric relations self-link sys:synonym;
# directional ones get sys:antonym inverses. Roles carry affect, like kin.ak.
# Base pack.

def "social:neighbor_of" "Living near another household — proximity without kinship."
ln social:neighbor_of social:neighbor_of sys:synonym   # symmetric
ln social:neighbor_of emo:trust calc:associated_with
ln social:neighbor_of emo:anticipation calc:associated_with
def "social:classmate_of" "Sharing a class or school year with another."
ln social:classmate_of social:classmate_of sys:synonym   # symmetric
ln social:classmate_of emo:joy calc:associated_with
ln social:classmate_of emo:trust calc:associated_with
ln social:classmate_of concept:friendship thesaurus:related
def "social:colleague_of" "Sharing a workplace or profession with another."
ln social:colleague_of social:colleague_of sys:synonym   # symmetric
ln social:colleague_of emo:trust calc:associated_with
ln social:colleague_of emo:respect calc:associated_with
def "social:childhood_friend_of" "A friend since childhood — 幼馴染; bond formed before memory."
ln social:childhood_friend_of social:childhood_friend_of sys:synonym   # symmetric
ln social:childhood_friend_of emo:nostalgia calc:associated_with
ln social:childhood_friend_of emo:trust calc:associated_with
ln social:childhood_friend_of emo:adoration calc:associated_with
ln social:childhood_friend_of concept:friendship thesaurus:related
def "social:acquaintance_of" "Known to each other, but not close."
ln social:acquaintance_of social:acquaintance_of sys:synonym   # symmetric
ln social:acquaintance_of emo:interest calc:associated_with
def "social:mentor_of" "Guiding another's growth by experience."
ln social:mentor_of social:mentee_of sys:antonym
ln social:mentor_of emo:admiration calc:associated_with
ln social:mentor_of emo:satisfaction calc:associated_with
def "social:mentee_of" "Being guided by a more experienced person."
ln social:mentee_of social:mentor_of sys:antonym
ln social:mentee_of emo:anticipation calc:associated_with
ln social:mentee_of emo:admiration calc:associated_with
def "social:caregiver_of" "Providing daily care (elder/child/patient care)."
ln social:caregiver_of social:care_recipient_of sys:antonym
ln social:caregiver_of emo:empathetic_pain calc:associated_with
ln social:caregiver_of emo:adoration calc:associated_with
def "social:care_recipient_of" "Receiving daily care from another."
ln social:care_recipient_of social:caregiver_of sys:antonym
ln social:care_recipient_of emo:trust calc:associated_with
ln social:care_recipient_of emo:anxiety calc:associated_with
def "social:doctor_of" "The clinical care relation from physician to patient."
ln social:doctor_of social:patient_of sys:antonym
ln social:doctor_of emo:responsibility calc:associated_with
ln social:doctor_of emo:empathetic_pain calc:associated_with
def "social:patient_of" "Being under a physician's care."
ln social:patient_of social:doctor_of sys:antonym
ln social:patient_of emo:trust calc:associated_with
ln social:patient_of emo:anxiety calc:associated_with
# ── role words → social relations ──
ln neighbor social:neighbor_of thesaurus:related
ln classmate social:classmate_of thesaurus:related
ln colleague social:colleague_of thesaurus:related
ln mentor social:mentor_of thesaurus:related
ln doctor social:doctor_of thesaurus:related
ln physician social:doctor_of thesaurus:related
ln patient social:patient_of thesaurus:related
ln nurse social:caregiver_of thesaurus:related
ln caregiver social:caregiver_of thesaurus:related
