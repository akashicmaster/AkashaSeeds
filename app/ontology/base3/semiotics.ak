# Akasha ontology — semiotics: the study of signs and meaning-making.
# Focused general-education-level spine. The linguistic sign already exists (ling:sign/signifier/
# signified + ling:field:semiotics); this adds the general discipline — the Saussurean
# dyad, the Peircean triad, code, denotation/connotation, Barthes' myth — and bridges
# to Akasha, which is itself a sign system (a semantic space of content-addressed atoms).
# General-education breadth; research depth reserved for level-C packs. Base pack.

def "semio:semiotics" "記号論 — the study of signs, signification and meaning-making, of which language is one system (Saussure's sémiologie, Peirce's semeiotic)."
ln semio:semiotics knowledge:branch:humanities knowledge:in_branch
ln semio:semiotics ling thesaurus:related
ln semio:semiotics ling:field:semiotics thesaurus:related
ln semio:semiotics crosscut:information thesaurus:related

# ══ sign models and core concepts ══
def "semio:saussurean_dyad" "The sign as a two-sided unit: a signifier (form) bound to a signified (concept); the bond is arbitrary."
ln semio:saussurean_dyad semio:semiotics sys:part_of
ln semio:saussurean_dyad ling:signifier thesaurus:related
ln semio:saussurean_dyad ling:signified thesaurus:related
ln semio:saussurean_dyad ling:sign thesaurus:related
ln semio:saussurean_dyad person:ferdinand_de_saussure thesaurus:related
def "semio:value_by_difference" "Saussure's principle that a sign has meaning only through its difference from others — 'a system of differences with no positive terms'."
ln semio:value_by_difference semio:semiotics sys:part_of
ln semio:value_by_difference ling:sign thesaurus:related
ln semio:value_by_difference crosscut:information thesaurus:related
def "semio:peircean_triad" "Peirce's sign as three-fold: the representamen (the sign itself), its object, and the interpretant (the sense made of it)."
ln semio:peircean_triad semio:semiotics sys:part_of
def "semio:icon" "A sign that resembles what it stands for (a portrait, a map)."
ln semio:icon semio:semiotics sys:part_of
def "semio:index" "A sign physically or causally connected to what it stands for (smoke for fire, a weathervane)."
ln semio:index semio:semiotics sys:part_of
def "semio:symbol" "A sign related to its object only by convention (a word, a flag)."
ln semio:symbol semio:semiotics sys:part_of
ln semio:symbol ling:symbolic_meaning thesaurus:related
def "semio:semiosis" "The living process by which something comes to function as a sign and produce meaning."
ln semio:semiosis semio:semiotics sys:part_of
def "semio:code" "The shared system of rules that lets signs be produced and understood."
ln semio:code semio:semiotics sys:part_of
ln semio:code ling:code thesaurus:related
def "semio:denotation" "The plain, literal thing a sign points to."
ln semio:denotation semio:semiotics sys:part_of
ln semio:denotation ling:concept:connotation_denotation thesaurus:related
def "semio:connotation" "The further cultural and emotional associations a sign carries."
ln semio:connotation semio:semiotics sys:part_of
ln semio:connotation ling:concept:connotation_denotation thesaurus:related
def "semio:myth" "Barthes' second-order sign, where a whole sign becomes the signifier of an ideological meaning that seems natural."
ln semio:myth semio:semiotics sys:part_of
ln semio:myth myth:mythical_method thesaurus:related
def "semio:paradigm_syntagm" "The two axes of meaning: paradigmatic (choice among alternatives) and syntagmatic (combination in sequence)."
ln semio:paradigm_syntagm semio:semiotics sys:part_of
ln semio:paradigm_syntagm ling:field:syntax thesaurus:related
def "semio:semiotic_square" "Greimas's diagram unfolding a concept through its contrary, contradictory and complementary terms."
ln semio:semiotic_square semio:semiotics sys:part_of
ln semio:semiotic_square crosscut:symmetry thesaurus:related
def "semio:syntactics" "Morris's division: the relations of signs to one another."
ln semio:syntactics semio:semiotics sys:part_of
ln semio:syntactics ling:field:syntax thesaurus:related
def "semio:semantics_semio" "Morris's division: the relations of signs to what they denote."
ln semio:semantics_semio semio:semiotics sys:part_of
ln semio:semantics_semio ling:field:semantics thesaurus:related
def "semio:pragmatics_semio" "Morris's division: the relations of signs to their users."
ln semio:pragmatics_semio semio:semiotics sys:part_of
ln semio:pragmatics_semio ling:field:pragmatics thesaurus:related
def "semio:visual_semiotics" "The reading of images, colour and design as sign systems."
ln semio:visual_semiotics semio:semiotics sys:part_of
ln semio:visual_semiotics artsci:composition thesaurus:related
def "semio:cultural_semiotics" "Signs and meaning in culture, ritual and everyday life."
ln semio:cultural_semiotics semio:semiotics sys:part_of
ln semio:cultural_semiotics socio:culture thesaurus:related
ln semio:cultural_semiotics anthro:anthropology thesaurus:related
def "semio:biosemiotics" "Sign processes in living systems, from cells to animal signalling."
ln semio:biosemiotics semio:semiotics sys:part_of
ln semio:biosemiotics bio:biology thesaurus:related
ln semio:icon semio:peircean_triad sys:part_of
ln semio:index semio:peircean_triad sys:part_of
ln semio:symbol semio:peircean_triad sys:part_of

# ══ founders ══
def "person:charles_peirce" "American philosopher and logician; founder of pragmatism and of the triadic theory of signs."
ln person:charles_peirce person:figure thesaurus:related
ln person:charles_peirce person:field:philosophy person:worked_in
ln person:charles_peirce semio:semiotics person:worked_in
ln person:charles_peirce semio:peircean_triad thesaurus:related
def "person:roland_barthes" "French critic who read fashion, food, photographs and wrestling as sign systems, and unmasked modern 'myth'."
ln person:roland_barthes person:figure thesaurus:related
ln person:roland_barthes person:field:literature person:worked_in
ln person:roland_barthes semio:semiotics person:worked_in
ln person:roland_barthes semio:myth thesaurus:related
def "person:umberto_eco" "Italian semiotician and novelist; a general theory of signs and codes."
ln person:umberto_eco person:figure thesaurus:related
ln person:umberto_eco person:field:literature person:worked_in
ln person:umberto_eco semio:semiotics person:worked_in
ln person:umberto_eco semio:code thesaurus:related
def "person:charles_morris" "American philosopher who split semiotics into syntactics, semantics and pragmatics."
ln person:charles_morris person:figure thesaurus:related
ln person:charles_morris person:field:philosophy person:worked_in
ln person:charles_morris semio:semiotics person:worked_in
ln person:charles_morris semio:syntactics thesaurus:related
ln person:ferdinand_de_saussure semio:saussurean_dyad thesaurus:related
ln person:roman_jakobson semio:semiotics thesaurus:related

# ══ the Akasha bridge — Akasha as a sign system ══
def "semio:concept:atom_as_sign" "In Akasha every atom is a sign: a content-addressed signifier bound to a meaning, whose value — as Saussure said of the linguistic sign — comes from its DIFFERENCES from other atoms, that is, from its links. Akasha is a semiotic space made computable."
ln semio:concept:atom_as_sign semio:semiotics sys:part_of
ln semio:concept:atom_as_sign semio:value_by_difference thesaurus:related
ln semio:concept:atom_as_sign ai:akasha_pattern thesaurus:related
ln semio:concept:atom_as_sign ling:concept:distributional_semantics thesaurus:related
