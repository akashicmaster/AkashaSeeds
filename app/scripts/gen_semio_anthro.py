#!/usr/bin/env python3
# Two focused general-education-level maps:
# app/ontology/base3/semiotics.ak — semiotics
# app/ontology/base3/cultural_anthropology.ak — cultural anthropology
# Semiotics existed only as the linguistic sign (ling:sign/signifier/signified +
# ling:field:semiotics) — no Peirce triad, no Barthes. Cultural anthropology was
# absent as a namespace, though its raw materials exist scattered (ethnicity:*,
# myth:* (388), kin:*, socio:culture/ethnography). These add the discipline spines
# and cross-link the existing atoms, each with an Akasha bridge where it is truthful.

import os

def esc(s):
    return s.replace('"', "'")

def emit(lines, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    nd = sum(1 for l in lines if l.startswith("def "))
    nl = sum(1 for l in lines if l.startswith("ln "))
    print(f"{path}: def={nd} ln={nl} ({len(lines)} lines)")

# ═════════════════════════════════════════════════════════════════════════════
# SEMIOTICS
# ═════════════════════════════════════════════════════════════════════════════
S = [
 "# Akasha ontology — semiotics: the study of signs and meaning-making.",
 "# Focused general-education-level spine. The linguistic sign already exists (ling:sign/signifier/",
 "# signified + ling:field:semiotics); this adds the general discipline — the Saussurean",
 "# dyad, the Peircean triad, code, denotation/connotation, Barthes' myth — and bridges",
 "# to Akasha, which is itself a sign system (a semantic space of content-addressed atoms).",
 "# General-education breadth; research depth reserved for level-C packs. Base pack.",
 "",
 'def "semio:semiotics" "記号論 — the study of signs, signification and meaning-making, of which language is one system (Saussure\'s sémiologie, Peirce\'s semeiotic)."',
 "ln semio:semiotics knowledge:branch:humanities knowledge:in_branch",
 "ln semio:semiotics ling thesaurus:related",
 "ln semio:semiotics ling:field:semiotics thesaurus:related",
 "ln semio:semiotics crosscut:information thesaurus:related",
]
SEMIO = [
 ("saussurean_dyad", "The sign as a two-sided unit: a signifier (form) bound to a signified (concept); the bond is arbitrary.",
   ["ling:signifier","ling:signified","ling:sign","person:ferdinand_de_saussure"]),
 ("value_by_difference", "Saussure's principle that a sign has meaning only through its difference from others — 'a system of differences with no positive terms'.",
   ["ling:sign","crosscut:information"]),
 ("peircean_triad", "Peirce's sign as three-fold: the representamen (the sign itself), its object, and the interpretant (the sense made of it).",
   []),
 ("icon", "A sign that resembles what it stands for (a portrait, a map).", []),
 ("index", "A sign physically or causally connected to what it stands for (smoke for fire, a weathervane).", []),
 ("symbol", "A sign related to its object only by convention (a word, a flag).", ["ling:symbolic_meaning"]),
 ("semiosis", "The living process by which something comes to function as a sign and produce meaning.", []),
 ("code", "The shared system of rules that lets signs be produced and understood.", ["ling:code"]),
 ("denotation", "The plain, literal thing a sign points to.", ["ling:concept:connotation_denotation"]),
 ("connotation", "The further cultural and emotional associations a sign carries.", ["ling:concept:connotation_denotation"]),
 ("myth", "Barthes' second-order sign, where a whole sign becomes the signifier of an ideological meaning that seems natural.", ["myth:mythical_method"]),
 ("paradigm_syntagm", "The two axes of meaning: paradigmatic (choice among alternatives) and syntagmatic (combination in sequence).", ["ling:field:syntax"]),
 ("semiotic_square", "Greimas's diagram unfolding a concept through its contrary, contradictory and complementary terms.", ["crosscut:symmetry"]),
 ("syntactics", "Morris's division: the relations of signs to one another.", ["ling:field:syntax"]),
 ("semantics_semio", "Morris's division: the relations of signs to what they denote.", ["ling:field:semantics"]),
 ("pragmatics_semio", "Morris's division: the relations of signs to their users.", ["ling:field:pragmatics"]),
 ("visual_semiotics", "The reading of images, colour and design as sign systems.", ["artsci:composition"]),
 ("cultural_semiotics", "Signs and meaning in culture, ritual and everyday life.", ["socio:culture","anthro:anthropology"]),
 ("biosemiotics", "Sign processes in living systems, from cells to animal signalling.", ["bio:biology"]),
]
S += ["", "# ══ sign models and core concepts ══"]
for slug, gloss, bridges in SEMIO:
    cid = f"semio:{slug}"
    S.append(f'def "{cid}" "{esc(gloss)}"')
    S.append(f"ln {cid} semio:semiotics sys:part_of")
    for b in bridges:
        S.append(f"ln {cid} {b} thesaurus:related")
# Peirce's three sign types under the triad
for t in ["icon","index","symbol"]:
    S.append(f"ln semio:{t} semio:peircean_triad sys:part_of")

# founders
SEMIO_PEOPLE = [
 ("charles_peirce", "American philosopher and logician; founder of pragmatism and of the triadic theory of signs.", "philosophy", "peircean_triad"),
 ("roland_barthes", "French critic who read fashion, food, photographs and wrestling as sign systems, and unmasked modern 'myth'.", "literature", "myth"),
 ("umberto_eco", "Italian semiotician and novelist; a general theory of signs and codes.", "literature", "code"),
 ("charles_morris", "American philosopher who split semiotics into syntactics, semantics and pragmatics.", "philosophy", "syntactics"),
]
S += ["", "# ══ founders ══"]
for slug, gloss, field, concept in SEMIO_PEOPLE:
    pid = f"person:{slug}"
    S.append(f'def "{pid}" "{esc(gloss)}"')
    S.append(f"ln {pid} person:figure thesaurus:related")
    S.append(f"ln {pid} person:field:{field} person:worked_in")
    S.append(f"ln {pid} semio:semiotics person:worked_in")
    S.append(f"ln {pid} semio:{concept} thesaurus:related")
# Saussure/Jakobson already exist — relate them
S += ["ln person:ferdinand_de_saussure semio:saussurean_dyad thesaurus:related",
      "ln person:roman_jakobson semio:semiotics thesaurus:related"]

# Akasha bridge
S += ["", "# ══ the Akasha bridge — Akasha as a sign system ══",
 'def "semio:concept:atom_as_sign" "In Akasha every atom is a sign: a content-addressed signifier bound to a meaning, whose value — as Saussure said of the linguistic sign — comes from its DIFFERENCES from other atoms, that is, from its links. Akasha is a semiotic space made computable."',
 "ln semio:concept:atom_as_sign semio:semiotics sys:part_of",
 "ln semio:concept:atom_as_sign semio:value_by_difference thesaurus:related",
 "ln semio:concept:atom_as_sign ai:akasha_pattern thesaurus:related",
 "ln semio:concept:atom_as_sign ling:concept:distributional_semantics thesaurus:related",
]
emit(S, "app/ontology/base3/semiotics.ak")

# ═════════════════════════════════════════════════════════════════════════════
# CULTURAL ANTHROPOLOGY
# ═════════════════════════════════════════════════════════════════════════════
A = [
 "# Akasha ontology — cultural anthropology: the comparative study of human",
 "# cultures. The namespace was absent though the materials existed scattered —",
 "# ethnicity:* (peoples), myth:* (myths), kin:* (kinship), socio:culture/ethnography.",
 "# This adds the four-field spine, cultural anthropology's core concepts, and its",
 "# founders, cross-linking the existing atoms. general-education breadth; research depth reserved for C.",
 "",
 'def "anthro:anthropology" "文化人類学 — the holistic, comparative study of humankind: our cultures, languages, past and biology."',
 "ln anthro:anthropology knowledge:branch:humanities knowledge:in_branch",
 "ln anthro:anthropology knowledge:branch:social_science thesaurus:related",
 "ln anthro:anthropology socio thesaurus:related",
 'def "person:field:anthropology" "Anthropology — the comparative study of human cultures, societies and origins."',
 "ln person:field:anthropology person:figure thesaurus:related",
 "ln person:field:anthropology anthro:anthropology thesaurus:related",
]
# the four fields
FIELDS = [
 ("cultural", "文化人類学 — living human cultures: belief, practice, meaning.", ["socio:culture"]),
 ("linguistic", "言語人類学 — language as culture and social practice.", ["ling","ling:field:sociolinguistics"]),
 ("archaeological", "考古人類学 — the human past through material remains.", ["archaeo"]),
 ("biological", "自然人類学 — human evolution, variation and primatology.", ["life:evolution","life:common_descent","bio:branch:evolution"]),
]
A += ["", "# ══ the four fields ══"]
for slug, gloss, bridges in FIELDS:
    fid = f"anthro:field:{slug}"
    A.append(f'def "{fid}" "{esc(gloss)}"')
    A.append(f"ln {fid} anthro:anthropology sys:part_of")
    for b in bridges:
        A.append(f"ln {fid} {b} thesaurus:related")

# core concepts of cultural anthropology
CONCEPTS = [
 # (slug, gloss, [bridges])
 ("culture", "The learned, shared way of life — beliefs, practices and meanings — passed between generations.", ["socio:culture"]),
 ("cultural_relativism", "Understanding a culture on its own terms rather than judging it by one's own (Boas).", ["socio:culture"]),
 ("ethnocentrism", "Judging other cultures by the standards of one's own.", []),
 ("holism", "Seeing any custom as part of a whole way of life, not in isolation.", ["crosscut:system"]),
 ("emic_etic", "The insider's own categories (emic) versus the analyst's comparative ones (etic).", []),
 ("ethnography", "The close, first-hand description of a culture, the method at anthropology's heart.", ["socio:ethnography"]),
 ("fieldwork", "Long immersion among the people studied — living, watching, taking part.", ["socio:participant_observation"]),
 ("participant_observation", "The core technique: taking part in daily life while systematically observing it.", ["socio:participant_observation"]),
 ("thick_description", "Geertz's ideal: interpreting behaviour together with the web of meaning that makes it intelligible.", ["socio:verstehen"]),
 ("kinship", "The culturally patterned system of relatedness — descent, marriage and the terms for kin.", ["kin:line","rel_kind:kinship"]),
 ("descent", "How membership and inheritance pass down a line (patrilineal, matrilineal, bilateral).", ["kin:line:lineal"]),
 ("marriage_alliance", "Marriage as an exchange that binds groups, not only individuals.", ["kin:partner_of"]),
 ("reciprocity", "The give-and-take of gifts that creates and sustains social bonds (Mauss).", ["crosscut:network"]),
 ("gift_exchange", "The gift as a total social fact, carrying obligation to give, receive and repay.", ["crosscut:network"]),
 ("ritual", "Formal, repeated symbolic action that marks and remakes social order.", ["myth:mythical_method"]),
 ("rite_of_passage", "A ritual marking a change of status, in three stages: separation, liminality, reincorporation (van Gennep).", []),
 ("liminality", "The ambiguous 'threshold' phase of a rite, betwixt-and-between (Turner).", []),
 ("taboo", "A powerful cultural prohibition, whose breach is felt as dangerous.", []),
 ("totem", "An animal or thing that symbolises and names a social group.", ["myth:totem_animal"]),
 ("myth_anthro", "Sacred stories that model the world and society; for structuralists, a code of binary oppositions.", ["myth:monomyth","myth:mythical_method"]),
 ("magic_religion", "The systems of belief and practice addressed to unseen powers.", ["myth:mythical_method"]),
 ("shamanism", "The vocation of the specialist who mediates between the human and spirit worlds.", []),
 ("material_culture", "The made things of a people — tools, dress, dwellings — as bearers of meaning.", ["archaeo","matsci"]),
 ("structuralism_anthro", "Lévi-Strauss's method: culture as built on universal binary oppositions of the mind.", ["semio:semiotics","ling:field:structural"]),
 ("symbolic_anthropology", "Reading culture as a system of symbols and meanings (Geertz, Douglas).", ["semio:cultural_semiotics"]),
 ("functionalism_anthro", "Explaining a custom by the social need it serves (Malinowski, Radcliffe-Brown).", ["socio:functionalism"]),
]
A += ["", "# ══ core concepts of cultural anthropology ══"]
for slug, gloss, bridges in CONCEPTS:
    cid = f"anthro:concept:{slug}"
    A.append(f'def "{cid}" "{esc(gloss)}"')
    A.append(f"ln {cid} anthro:field:cultural sys:part_of")
    for b in bridges:
        A.append(f"ln {cid} {b} thesaurus:related")

# founders
ANTHRO_PEOPLE = [
 ("james_frazer", "Author of 'The Golden Bough'; a vast (armchair) comparison of myth, magic and religion.", "magic_religion"),
 ("franz_boas", "Father of American anthropology; cultural relativism and rigorous fieldwork.", "cultural_relativism"),
 ("bronislaw_malinowski", "Pioneer of intensive fieldwork and functionalism; studied the Trobriand Islanders.", "functionalism_anthro"),
 ("margaret_mead", "Studied gender, adolescence and culture; brought anthropology to a wide public.", "culture"),
 ("claude_levi_strauss", "Founder of structural anthropology; myth and kinship as systems of the mind.", "structuralism_anthro"),
 ("mary_douglas", "Analysed purity and danger — how ideas of dirt map a culture's classifications.", "taboo"),
 ("clifford_geertz", "Interpretive anthropologist; culture as text, read by 'thick description'.", "thick_description"),
]
A += ["", "# ══ founders ══"]
for slug, gloss, concept in ANTHRO_PEOPLE:
    pid = f"person:{slug}"
    A.append(f'def "{pid}" "{esc(gloss)}"')
    A.append(f"ln {pid} person:figure thesaurus:related")
    A.append(f"ln {pid} person:field:anthropology person:worked_in")
    A.append(f"ln {pid} hist:period:modern_era person:active_in")
    A.append(f"ln {pid} anthro:concept:{concept} thesaurus:related")

# bridge peoples: ethnicity:* are the subjects of ethnography
A += ["", "# ── ethnicity: the peoples studied ──",
 "ln anthro:field:cultural ethnicity:family thesaurus:related",
 "ln anthro:concept:ethnography ethnicity:family thesaurus:related",
]
emit(A, "app/ontology/base3/cultural_anthropology.ak")
