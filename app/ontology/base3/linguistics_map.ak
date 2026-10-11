# Akasha ontology — linguistics: a broad general-education-level map.
# Levels of analysis + branch fields + founders + an Akasha text-engine bridge,
# over the existing (flat) ling:* atoms. ling (top) already exists — only linked.
# General-education breadth; research depth is reserved for level-C packs. Base pack.

ln ling knowledge:branch:humanities knowledge:in_branch
ln ling knowledge:branch:social_science thesaurus:related
ln ling knowledge:cognitive_science thesaurus:related

# ══ levels of analysis (structural core) ══
def "ling:field:structural" "The structural core of linguistics — the levels of analysis from sound to meaning (理論言語学の中核)."
ln ling:field:structural ling sys:part_of
def "ling:field:phonetics" "音声学 — the physical sounds of speech: how they are produced, transmitted and heard."
ln ling:field:phonetics ling:field:structural sys:part_of
ln ling:phonetics ling:field:phonetics sys:part_of
def "ling:field:phonology" "音韻論 — the sound SYSTEM of a language: which contrasts carry meaning."
ln ling:field:phonology ling:field:structural sys:part_of
ln ling:phonology ling:field:phonology sys:part_of
ln ling:phoneme ling:field:phonology sys:part_of
ln ling:field:phonetics ling:field:phonology ling:feeds_into
def "ling:field:morphology" "形態論 — the internal structure of words, built from morphemes."
ln ling:field:morphology ling:field:structural sys:part_of
ln ling:morphology ling:field:morphology sys:part_of
ln ling:morpheme ling:field:morphology sys:part_of
ln ling:root_word ling:field:morphology sys:part_of
ln ling:word ling:field:morphology sys:part_of
ln ling:field:phonology ling:field:morphology ling:feeds_into
def "ling:field:syntax" "統語論 — how words combine into phrases and sentences."
ln ling:field:syntax ling:field:structural sys:part_of
ln ling:syntax ling:field:syntax sys:part_of
ln ling:sentence ling:field:syntax sys:part_of
ln ling:grammar ling:field:syntax sys:part_of
ln ling:recursion ling:field:syntax sys:part_of
ln ling:universal_grammar ling:field:syntax sys:part_of
ln ling:structure ling:field:syntax sys:part_of
ln ling:field:morphology ling:field:syntax ling:feeds_into
def "ling:field:semantics" "意味論 — literal meaning: of words, and of how they combine."
ln ling:field:semantics ling:field:structural sys:part_of
ln ling:semantics ling:field:semantics sys:part_of
ln ling:meaning ling:field:semantics sys:part_of
ln ling:lexicon ling:field:semantics sys:part_of
ln ling:reference ling:field:semantics sys:part_of
ln ling:polysemy ling:field:semantics sys:part_of
ln ling:metaphor ling:field:semantics sys:part_of
ln ling:symbolic_meaning ling:field:semantics sys:part_of
ln ling:signified ling:field:semantics sys:part_of
ln ling:signifier ling:field:semantics sys:part_of
ln ling:sign ling:field:semantics sys:part_of
ln ling:field:syntax ling:field:semantics ling:feeds_into
def "ling:field:pragmatics" "語用論 — meaning in use: how context and intent shape what is meant."
ln ling:field:pragmatics ling:field:structural sys:part_of
ln ling:pragmatics ling:field:pragmatics sys:part_of
ln ling:deixis ling:field:pragmatics sys:part_of
ln ling:speech_act ling:field:pragmatics sys:part_of
ln ling:implication ling:field:pragmatics sys:part_of
ln ling:context ling:field:pragmatics sys:part_of
ln ling:utterance ling:field:pragmatics sys:part_of
ln ling:reference ling:field:pragmatics sys:part_of
ln ling:field:semantics ling:field:pragmatics ling:feeds_into
def "ling:field:discourse" "談話分析 — language above the sentence: conversation, narrative and text."
ln ling:field:discourse ling:field:structural sys:part_of
ln ling:narrative_discourse ling:field:discourse sys:part_of
ln ling:dialogue ling:field:discourse sys:part_of
ln ling:rhetoric ling:field:discourse sys:part_of
ln ling:register ling:field:discourse sys:part_of
ln ling:code ling:field:discourse sys:part_of
ln ling:field:pragmatics ling:field:discourse ling:feeds_into

# ══ branch / interface fields ══
def "ling:field:historical" "歴史言語学 — how languages change over time and how they are related."
ln ling:field:historical ling sys:part_of
ln ling:historical_linguistics ling:field:historical sys:part_of
ln ling:language_change ling:field:historical sys:part_of
ln ling:language_family ling:field:historical sys:part_of
ln ling:etymology ling:field:historical sys:part_of
ln ling:field:historical crosscut:evolution thesaurus:related
def "ling:field:sociolinguistics" "社会言語学 — language in society: dialect, register, variation, bilingualism."
ln ling:field:sociolinguistics ling sys:part_of
ln ling:sociolinguistics ling:field:sociolinguistics sys:part_of
ln ling:dialect ling:field:sociolinguistics sys:part_of
ln ling:register ling:field:sociolinguistics sys:part_of
ln ling:bilingualism ling:field:sociolinguistics sys:part_of
ln ling:field:sociolinguistics socio:culture thesaurus:related
def "ling:field:psycholinguistics" "心理言語学 — how language is produced, understood and acquired in the mind."
ln ling:field:psycholinguistics ling sys:part_of
ln ling:psycholinguistics ling:field:psycholinguistics sys:part_of
ln ling:field:psycholinguistics psy:field:cognitive thesaurus:related
ln ling:field:psycholinguistics knowledge:cognitive_science thesaurus:related
def "ling:field:neurolinguistics" "神経言語学 — how the brain represents and processes language."
ln ling:field:neurolinguistics ling sys:part_of
ln ling:field:neurolinguistics neuro:cognitive_neuroscience thesaurus:related
ln ling:field:neurolinguistics neuro:cerebral_cortex thesaurus:related
def "ling:field:computational" "計算言語学 — modelling and processing language by computer (NLP)."
ln ling:field:computational ling sys:part_of
ln ling:computational_linguistics ling:field:computational sys:part_of
ln ling:field:computational cs thesaurus:related
ln ling:field:computational ai:embedding thesaurus:related
ln ling:field:computational crosscut:information thesaurus:related
def "ling:field:applied" "応用言語学 — language teaching, translation, lexicography and policy."
ln ling:field:applied ling sys:part_of
ln ling:field:applied edupsy:learning_theory thesaurus:related
ln ling:field:applied lib:indexing thesaurus:related
def "ling:field:typology" "言語類型論 — comparing the structures of the world's languages."
ln ling:field:typology ling sys:part_of
ln ling:field:typology ling:language_family thesaurus:related
def "ling:field:semiotics" "記号論 — signs and meaning in general, of which language is one system."
ln ling:field:semiotics ling sys:part_of
ln ling:sign ling:field:semiotics sys:part_of
ln ling:signifier ling:field:semiotics sys:part_of
ln ling:signified ling:field:semiotics sys:part_of
ln ling:symbolic_meaning ling:field:semiotics sys:part_of
ln ling:field:semiotics crosscut:information thesaurus:related
def "ling:field:pragmatics_field" "語用・談話研究 — the study of language in context and interaction."
ln ling:field:pragmatics_field ling sys:part_of
ln ling:speech_act ling:field:pragmatics_field sys:part_of
ln ling:dialogue ling:field:pragmatics_field sys:part_of
ln ling:field:pragmatics_field ling:field:pragmatics thesaurus:related

# ══ general-education-level concepts (new) ══
def "ling:concept:allophone" "One of the several actual sounds that realise a single phoneme without changing meaning."
ln ling:concept:allophone ling:field:phonology sys:part_of
ln ling:concept:allophone ling:phoneme thesaurus:related
def "ling:concept:prosody" "The rhythm, stress and intonation of speech, which carry meaning of their own."
ln ling:concept:prosody ling:field:phonology sys:part_of
def "ling:concept:inflection" "A change in a word's form to mark grammar (tense, number, case) without making a new word."
ln ling:concept:inflection ling:field:morphology sys:part_of
ln ling:concept:inflection ling:morpheme thesaurus:related
def "ling:concept:derivation" "Making a new word from another by adding an affix (happy → happiness)."
ln ling:concept:derivation ling:field:morphology sys:part_of
ln ling:concept:derivation ling:morpheme thesaurus:related
def "ling:concept:part_of_speech" "The grammatical class of a word: noun, verb, adjective and so on."
ln ling:concept:part_of_speech ling:field:syntax sys:part_of
ln ling:concept:part_of_speech ling:word thesaurus:related
def "ling:concept:lexeme" "An abstract vocabulary unit — the family of forms 'run, runs, ran, running' share."
ln ling:concept:lexeme ling:field:morphology sys:part_of
ln ling:concept:lexeme ling:lexicon thesaurus:related
def "ling:concept:tense_aspect_mood" "How language marks time, the flow of an event, and the speaker's stance (real, wished, commanded)."
ln ling:concept:tense_aspect_mood ling:field:morphology sys:part_of
ln ling:concept:tense_aspect_mood ling:grammar thesaurus:related
def "ling:concept:grammatical_case" "The marking of a noun's role in a sentence (subject, object, possessor)."
ln ling:concept:grammatical_case ling:field:syntax sys:part_of
def "ling:concept:agreement" "When one word's form must match another's (the verb agreeing with its subject)."
ln ling:concept:agreement ling:field:syntax sys:part_of
def "ling:concept:phrase_clause" "The units between word and sentence: the phrase, and the clause with its own verb."
ln ling:concept:phrase_clause ling:field:syntax sys:part_of
ln ling:concept:phrase_clause ling:sentence thesaurus:related
def "ling:concept:ambiguity" "When a form has more than one possible meaning or structure."
ln ling:concept:ambiguity ling:field:semantics sys:part_of
ln ling:concept:ambiguity ling:polysemy thesaurus:related
def "ling:concept:connotation_denotation" "A word's plain reference (denotation) versus its felt associations (connotation)."
ln ling:concept:connotation_denotation ling:field:semantics sys:part_of
ln ling:concept:connotation_denotation ling:meaning thesaurus:related
def "ling:concept:grammaticalization" "How ordinary words erode over time into grammatical markers."
ln ling:concept:grammaticalization ling:field:historical sys:part_of
ln ling:concept:grammaticalization ling:language_change thesaurus:related
def "ling:concept:sound_change" "The regular, law-like shifts in pronunciation over time (e.g. Grimm's law)."
ln ling:concept:sound_change ling:field:historical sys:part_of
ln ling:concept:sound_change ling:phonology thesaurus:related
def "ling:concept:language_acquisition" "How children acquire a first language, and how we learn later ones."
ln ling:concept:language_acquisition ling:field:psycholinguistics sys:part_of
ln ling:concept:language_acquisition devpsy:language_acquisition thesaurus:related
def "ling:concept:linguistic_relativity" "The idea that the language one speaks shapes how one thinks (Sapir-Whorf)."
ln ling:concept:linguistic_relativity ling:field:sociolinguistics sys:part_of
ln ling:concept:linguistic_relativity socio:culture thesaurus:related
def "ling:concept:pidgin_creole" "A makeshift contact language (pidgin) and the full native language it can become (creole)."
ln ling:concept:pidgin_creole ling:field:sociolinguistics sys:part_of
ln ling:concept:pidgin_creole ling:dialect thesaurus:related
def "ling:concept:linguistic_typology_classes" "Types by word-building: isolating, agglutinative, fusional, polysynthetic."
ln ling:concept:linguistic_typology_classes ling:field:typology sys:part_of
def "ling:concept:writing_system" "How languages are written: logographic, syllabic, alphabetic and mixed."
ln ling:concept:writing_system ling:field:applied sys:part_of
ln ling:concept:writing_system epig:inscription thesaurus:related
ln ling:concept:writing_system ms:script thesaurus:related
def "ling:concept:langue_parole" "Saussure's split: the shared language system (langue) versus individual speech (parole)."
ln ling:concept:langue_parole ling:field:semiotics sys:part_of
ln ling:concept:langue_parole ling:sign thesaurus:related
def "ling:concept:competence_performance" "Chomsky's split: tacit knowledge of a language versus its actual use."
ln ling:concept:competence_performance ling:field:psycholinguistics sys:part_of
ln ling:concept:competence_performance ling:universal_grammar thesaurus:related
def "ling:concept:corpus" "A large, structured body of real texts, the evidence base of modern linguistics."
ln ling:concept:corpus ling:field:computational sys:part_of
ln ling:concept:corpus ai:embedding thesaurus:related
def "ling:concept:tokenization" "Splitting text into words or sub-word units — the first step of language processing."
ln ling:concept:tokenization ling:field:computational sys:part_of
ln ling:concept:tokenization ling:word thesaurus:related
def "ling:concept:parsing" "Analysing a sentence into its grammatical structure automatically."
ln ling:concept:parsing ling:field:computational sys:part_of
ln ling:concept:parsing ling:syntax thesaurus:related

# ══ founders (person:*) ══
def "person:panini" "Ancient Indian grammarian (c.5th-4th c. BCE) whose formal grammar of Sanskrit is the first great linguistic analysis."
ln person:panini person:figure thesaurus:related
ln person:panini person:field:linguistics_scholarship person:worked_in
ln person:panini hist:period:classical_antiquity person:active_in
ln person:panini ling:morphology thesaurus:related
ln person:panini ling:grammar thesaurus:related
def "person:jacob_grimm" "Philologist who, with the comparative method, formulated the sound law (Grimm's law) of the Germanic consonant shift."
ln person:jacob_grimm person:figure thesaurus:related
ln person:jacob_grimm person:field:linguistics_scholarship person:worked_in
ln person:jacob_grimm hist:period:industrial_revolution person:active_in
ln person:jacob_grimm ling:concept:sound_change thesaurus:related
ln person:jacob_grimm ling:historical_linguistics thesaurus:related
def "person:ferdinand_de_saussure" "Founder of structural linguistics; the arbitrary sign, langue vs parole, and language as a system of differences."
ln person:ferdinand_de_saussure person:figure thesaurus:related
ln person:ferdinand_de_saussure person:field:linguistics_scholarship person:worked_in
ln person:ferdinand_de_saussure hist:period:modern_era person:active_in
ln person:ferdinand_de_saussure ling:sign thesaurus:related
ln person:ferdinand_de_saussure ling:concept:langue_parole thesaurus:related
ln person:ferdinand_de_saussure ling:field:semiotics thesaurus:related
def "person:roman_jakobson" "Structuralist who mapped the functions of language and advanced phonology and poetics."
ln person:roman_jakobson person:figure thesaurus:related
ln person:roman_jakobson person:field:linguistics_scholarship person:worked_in
ln person:roman_jakobson hist:period:modern_era person:active_in
ln person:roman_jakobson ling:phonology thesaurus:related
ln person:roman_jakobson ling:field:discourse thesaurus:related
def "person:edward_sapir" "Anthropological linguist central to the idea that language and culture shape thought."
ln person:edward_sapir person:figure thesaurus:related
ln person:edward_sapir person:field:linguistics_scholarship person:worked_in
ln person:edward_sapir hist:period:modern_era person:active_in
ln person:edward_sapir ling:concept:linguistic_relativity thesaurus:related
def "person:noam_chomsky" "Founder of generative grammar; universal grammar and the competence/performance distinction transformed the field."
ln person:noam_chomsky person:figure thesaurus:related
ln person:noam_chomsky person:field:linguistics_scholarship person:worked_in
ln person:noam_chomsky hist:period:modern_era person:active_in
ln person:noam_chomsky ling:universal_grammar thesaurus:related
ln person:noam_chomsky ling:concept:competence_performance thesaurus:related
ln person:noam_chomsky ling:syntax thesaurus:related

# ══ the Akasha bridge — linguistics ↔ Akasha's text engine ══
def "ling:concept:distributional_semantics" "Meaning learned from the company a word keeps (Firth): words used in similar contexts have similar meanings — the principle behind word embeddings, and behind Akasha's own learned semantic layer."
ln ling:concept:distributional_semantics ling:field:semantics sys:part_of
ln ling:concept:distributional_semantics ling:field:computational thesaurus:related
ln ling:concept:distributional_semantics ai:embedding thesaurus:related
ln ling:concept:distributional_semantics crosscut:information thesaurus:related
def "ling:concept:lexical_decomposition" "Breaking an utterance into its smallest meaning-bearing units — the linguistic counterpart of Akasha's Weaver, which decomposes text into proto-words and component sets."
ln ling:concept:lexical_decomposition ling:field:morphology sys:part_of
ln ling:concept:lexical_decomposition ling:morpheme thesaurus:related
ln ling:concept:lexical_decomposition ai:akasha_pattern thesaurus:related
ln ling:field:computational ai:akasha_pattern thesaurus:related
