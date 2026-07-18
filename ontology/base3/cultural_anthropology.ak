# Akasha ontology — cultural anthropology: the comparative study of human
# cultures. The namespace was absent though the materials existed scattered —
# ethnicity:* (peoples), myth:* (myths), kin:* (kinship), socio:culture/ethnography.
# This adds the four-field spine, cultural anthropology's core concepts, and its
# founders, cross-linking the existing atoms. general-education breadth; research depth reserved for C.

def "anthro:anthropology" "文化人類学 — the holistic, comparative study of humankind: our cultures, languages, past and biology."
ln anthro:anthropology knowledge:branch:humanities knowledge:in_branch
ln anthro:anthropology knowledge:branch:social_science thesaurus:related
ln anthro:anthropology socio thesaurus:related
def "person:field:anthropology" "Anthropology — the comparative study of human cultures, societies and origins."
ln person:field:anthropology person:figure thesaurus:related
ln person:field:anthropology anthro:anthropology thesaurus:related

# ══ the four fields ══
def "anthro:field:cultural" "文化人類学 — living human cultures: belief, practice, meaning."
ln anthro:field:cultural anthro:anthropology sys:part_of
ln anthro:field:cultural socio:culture thesaurus:related
def "anthro:field:linguistic" "言語人類学 — language as culture and social practice."
ln anthro:field:linguistic anthro:anthropology sys:part_of
ln anthro:field:linguistic ling thesaurus:related
ln anthro:field:linguistic ling:field:sociolinguistics thesaurus:related
def "anthro:field:archaeological" "考古人類学 — the human past through material remains."
ln anthro:field:archaeological anthro:anthropology sys:part_of
ln anthro:field:archaeological archaeo thesaurus:related
def "anthro:field:biological" "自然人類学 — human evolution, variation and primatology."
ln anthro:field:biological anthro:anthropology sys:part_of
ln anthro:field:biological life:evolution thesaurus:related
ln anthro:field:biological life:common_descent thesaurus:related
ln anthro:field:biological bio:branch:evolution thesaurus:related

# ══ core concepts of cultural anthropology ══
def "anthro:concept:culture" "The learned, shared way of life — beliefs, practices and meanings — passed between generations."
ln anthro:concept:culture anthro:field:cultural sys:part_of
ln anthro:concept:culture socio:culture thesaurus:related
def "anthro:concept:cultural_relativism" "Understanding a culture on its own terms rather than judging it by one's own (Boas)."
ln anthro:concept:cultural_relativism anthro:field:cultural sys:part_of
ln anthro:concept:cultural_relativism socio:culture thesaurus:related
def "anthro:concept:ethnocentrism" "Judging other cultures by the standards of one's own."
ln anthro:concept:ethnocentrism anthro:field:cultural sys:part_of
def "anthro:concept:holism" "Seeing any custom as part of a whole way of life, not in isolation."
ln anthro:concept:holism anthro:field:cultural sys:part_of
ln anthro:concept:holism crosscut:system thesaurus:related
def "anthro:concept:emic_etic" "The insider's own categories (emic) versus the analyst's comparative ones (etic)."
ln anthro:concept:emic_etic anthro:field:cultural sys:part_of
def "anthro:concept:ethnography" "The close, first-hand description of a culture, the method at anthropology's heart."
ln anthro:concept:ethnography anthro:field:cultural sys:part_of
ln anthro:concept:ethnography socio:ethnography thesaurus:related
def "anthro:concept:fieldwork" "Long immersion among the people studied — living, watching, taking part."
ln anthro:concept:fieldwork anthro:field:cultural sys:part_of
ln anthro:concept:fieldwork socio:participant_observation thesaurus:related
def "anthro:concept:participant_observation" "The core technique: taking part in daily life while systematically observing it."
ln anthro:concept:participant_observation anthro:field:cultural sys:part_of
ln anthro:concept:participant_observation socio:participant_observation thesaurus:related
def "anthro:concept:thick_description" "Geertz's ideal: interpreting behaviour together with the web of meaning that makes it intelligible."
ln anthro:concept:thick_description anthro:field:cultural sys:part_of
ln anthro:concept:thick_description socio:verstehen thesaurus:related
def "anthro:concept:kinship" "The culturally patterned system of relatedness — descent, marriage and the terms for kin."
ln anthro:concept:kinship anthro:field:cultural sys:part_of
ln anthro:concept:kinship kin:line thesaurus:related
ln anthro:concept:kinship rel_kind:kinship thesaurus:related
def "anthro:concept:descent" "How membership and inheritance pass down a line (patrilineal, matrilineal, bilateral)."
ln anthro:concept:descent anthro:field:cultural sys:part_of
ln anthro:concept:descent kin:line:lineal thesaurus:related
def "anthro:concept:marriage_alliance" "Marriage as an exchange that binds groups, not only individuals."
ln anthro:concept:marriage_alliance anthro:field:cultural sys:part_of
ln anthro:concept:marriage_alliance kin:partner_of thesaurus:related
def "anthro:concept:reciprocity" "The give-and-take of gifts that creates and sustains social bonds (Mauss)."
ln anthro:concept:reciprocity anthro:field:cultural sys:part_of
ln anthro:concept:reciprocity crosscut:network thesaurus:related
def "anthro:concept:gift_exchange" "The gift as a total social fact, carrying obligation to give, receive and repay."
ln anthro:concept:gift_exchange anthro:field:cultural sys:part_of
ln anthro:concept:gift_exchange crosscut:network thesaurus:related
def "anthro:concept:ritual" "Formal, repeated symbolic action that marks and remakes social order."
ln anthro:concept:ritual anthro:field:cultural sys:part_of
ln anthro:concept:ritual myth:mythical_method thesaurus:related
def "anthro:concept:rite_of_passage" "A ritual marking a change of status, in three stages: separation, liminality, reincorporation (van Gennep)."
ln anthro:concept:rite_of_passage anthro:field:cultural sys:part_of
def "anthro:concept:liminality" "The ambiguous 'threshold' phase of a rite, betwixt-and-between (Turner)."
ln anthro:concept:liminality anthro:field:cultural sys:part_of
def "anthro:concept:taboo" "A powerful cultural prohibition, whose breach is felt as dangerous."
ln anthro:concept:taboo anthro:field:cultural sys:part_of
def "anthro:concept:totem" "An animal or thing that symbolises and names a social group."
ln anthro:concept:totem anthro:field:cultural sys:part_of
ln anthro:concept:totem myth:totem_animal thesaurus:related
def "anthro:concept:myth_anthro" "Sacred stories that model the world and society; for structuralists, a code of binary oppositions."
ln anthro:concept:myth_anthro anthro:field:cultural sys:part_of
ln anthro:concept:myth_anthro myth:monomyth thesaurus:related
ln anthro:concept:myth_anthro myth:mythical_method thesaurus:related
def "anthro:concept:magic_religion" "The systems of belief and practice addressed to unseen powers."
ln anthro:concept:magic_religion anthro:field:cultural sys:part_of
ln anthro:concept:magic_religion myth:mythical_method thesaurus:related
def "anthro:concept:shamanism" "The vocation of the specialist who mediates between the human and spirit worlds."
ln anthro:concept:shamanism anthro:field:cultural sys:part_of
def "anthro:concept:material_culture" "The made things of a people — tools, dress, dwellings — as bearers of meaning."
ln anthro:concept:material_culture anthro:field:cultural sys:part_of
ln anthro:concept:material_culture archaeo thesaurus:related
ln anthro:concept:material_culture matsci thesaurus:related
def "anthro:concept:structuralism_anthro" "Lévi-Strauss's method: culture as built on universal binary oppositions of the mind."
ln anthro:concept:structuralism_anthro anthro:field:cultural sys:part_of
ln anthro:concept:structuralism_anthro semio:semiotics thesaurus:related
ln anthro:concept:structuralism_anthro ling:field:structural thesaurus:related
def "anthro:concept:symbolic_anthropology" "Reading culture as a system of symbols and meanings (Geertz, Douglas)."
ln anthro:concept:symbolic_anthropology anthro:field:cultural sys:part_of
ln anthro:concept:symbolic_anthropology semio:cultural_semiotics thesaurus:related
def "anthro:concept:functionalism_anthro" "Explaining a custom by the social need it serves (Malinowski, Radcliffe-Brown)."
ln anthro:concept:functionalism_anthro anthro:field:cultural sys:part_of
ln anthro:concept:functionalism_anthro socio:functionalism thesaurus:related

# ══ founders ══
def "person:james_frazer" "Author of 'The Golden Bough'; a vast (armchair) comparison of myth, magic and religion."
ln person:james_frazer person:figure thesaurus:related
ln person:james_frazer person:field:anthropology person:worked_in
ln person:james_frazer hist:period:modern_era person:active_in
ln person:james_frazer anthro:concept:magic_religion thesaurus:related
def "person:franz_boas" "Father of American anthropology; cultural relativism and rigorous fieldwork."
ln person:franz_boas person:figure thesaurus:related
ln person:franz_boas person:field:anthropology person:worked_in
ln person:franz_boas hist:period:modern_era person:active_in
ln person:franz_boas anthro:concept:cultural_relativism thesaurus:related
def "person:bronislaw_malinowski" "Pioneer of intensive fieldwork and functionalism; studied the Trobriand Islanders."
ln person:bronislaw_malinowski person:figure thesaurus:related
ln person:bronislaw_malinowski person:field:anthropology person:worked_in
ln person:bronislaw_malinowski hist:period:modern_era person:active_in
ln person:bronislaw_malinowski anthro:concept:functionalism_anthro thesaurus:related
def "person:margaret_mead" "Studied gender, adolescence and culture; brought anthropology to a wide public."
ln person:margaret_mead person:figure thesaurus:related
ln person:margaret_mead person:field:anthropology person:worked_in
ln person:margaret_mead hist:period:modern_era person:active_in
ln person:margaret_mead anthro:concept:culture thesaurus:related
def "person:claude_levi_strauss" "Founder of structural anthropology; myth and kinship as systems of the mind."
ln person:claude_levi_strauss person:figure thesaurus:related
ln person:claude_levi_strauss person:field:anthropology person:worked_in
ln person:claude_levi_strauss hist:period:modern_era person:active_in
ln person:claude_levi_strauss anthro:concept:structuralism_anthro thesaurus:related
def "person:mary_douglas" "Analysed purity and danger — how ideas of dirt map a culture's classifications."
ln person:mary_douglas person:figure thesaurus:related
ln person:mary_douglas person:field:anthropology person:worked_in
ln person:mary_douglas hist:period:modern_era person:active_in
ln person:mary_douglas anthro:concept:taboo thesaurus:related
def "person:clifford_geertz" "Interpretive anthropologist; culture as text, read by 'thick description'."
ln person:clifford_geertz person:figure thesaurus:related
ln person:clifford_geertz person:field:anthropology person:worked_in
ln person:clifford_geertz hist:period:modern_era person:active_in
ln person:clifford_geertz anthro:concept:thick_description thesaurus:related

# ── ethnicity: the peoples studied ──
ln anthro:field:cultural ethnicity:family thesaurus:related
ln anthro:concept:ethnography ethnicity:family thesaurus:related
