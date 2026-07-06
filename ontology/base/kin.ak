# Akasha ontology — namespace: kin / social
# Kinship and social relation atoms.
# These are RELATION CONCEPTS, not instances — they define the types of bonds
# that can exist between people, institutions and groups.
# Linked to emotions to show that relationships carry affective weight.
# atoms: 11

def "kin:parent_of" "The relation of being parent to another person — origin, care and authority."
ln kin:parent_of kin:child_of sys:antonym
ln kin:parent_of emo:adoration calc:associated_with
ln kin:parent_of emo:satisfaction calc:associated_with
ln kin:parent_of emo:anxiety calc:associated_with

def "kin:child_of" "The relation of being born to or raised by a parent — origin of identity."
ln kin:child_of kin:parent_of sys:antonym
ln kin:child_of emo:trust calc:associated_with
ln kin:child_of emo:nostalgia calc:associated_with
ln kin:child_of emo:adoration calc:associated_with

def "kin:sibling_of" "The relation of sharing at least one parent with another person."
ln kin:sibling_of emo:trust calc:associated_with
ln kin:sibling_of emo:joy calc:associated_with
ln kin:sibling_of emo:empathetic_pain calc:associated_with

def "kin:ancestor_of" "The relation of being a forebear through generational lineage."
ln kin:ancestor_of kin:descendant_of sys:antonym
ln kin:ancestor_of emo:nostalgia calc:associated_with
ln kin:ancestor_of emo:awe calc:associated_with

def "kin:descendant_of" "The relation of tracing lineage back to an ancestor."
ln kin:descendant_of kin:ancestor_of sys:antonym
ln kin:descendant_of emo:nostalgia calc:associated_with

def "kin:partner_of" "The relation of committed romantic or life partnership."
ln kin:partner_of concept:love thesaurus:related
ln kin:partner_of emo:trust calc:associated_with
ln kin:partner_of emo:romance calc:associated_with

def "social:member_of" "The relation of holding membership in a group, institution or community."
ln social:member_of emo:trust calc:associated_with
ln social:member_of emo:satisfaction calc:associated_with
ln social:member_of emo:anticipation calc:associated_with

def "social:student_of" "The relation of learning under the guidance of a teacher or institution."
ln social:student_of emo:interest calc:associated_with
ln social:student_of emo:anticipation calc:associated_with
ln social:student_of emo:anxiety calc:associated_with
ln social:student_of emo:admiration calc:associated_with

def "social:teacher_of" "The relation of guiding or instructing a student."
ln social:teacher_of social:student_of sys:antonym
ln social:teacher_of emo:satisfaction calc:associated_with
ln social:teacher_of emo:admiration calc:associated_with

def "social:friend_of" "The relation of mutual affection and trust between people."
ln social:friend_of emo:joy calc:associated_with
ln social:friend_of emo:trust calc:associated_with
ln social:friend_of emo:empathetic_pain calc:associated_with
ln social:friend_of concept:friendship thesaurus:related

def "social:leader_of" "The relation of holding authority or responsibility over a group."
ln social:leader_of emo:admiration calc:associated_with
ln social:leader_of emo:awe calc:associated_with
ln social:leader_of emo:anxiety calc:associated_with
ln social:leader_of social:member_of thesaurus:related
