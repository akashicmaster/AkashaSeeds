# Akasha ontology — linguistics (言語学).
# lang: held only language codes; this adds the DISCIPLINE. Bridged to textanal:/
# dh:/oral:/ms:/devpsy:/cs:/math:logic. Base pack.

def "ling" "Linguistics — the scientific study of language (言語学)."
ln ling person:field:linguistics_scholarship thesaurus:related
# ── levels of language ──
def "ling:phonetics" "The physical sounds of speech — production and perception (音声学)."
ln ling:phonetics ling thesaurus:related
ln ling:phonetics oral:field_recording thesaurus:related
def "ling:phonology" "The sound system and patterns of a language (音韻論)."
ln ling:phonology ling thesaurus:related
def "ling:morphology" "The structure of words from morphemes (形態論)."
ln ling:morphology ling thesaurus:related
ln ling:morphology textanal:lemmatization thesaurus:related
ln ling:morphology textanal:morphological_analysis thesaurus:related
def "ling:syntax" "The rules combining words into sentences (統語論)."
ln ling:syntax ling thesaurus:related
ln ling:syntax textanal:dependency_parsing thesaurus:related
ln ling:syntax cs:automaton thesaurus:related
ln ling:syntax math:logic thesaurus:related
def "ling:semantics" "The study of linguistic meaning (意味論)."
ln ling:semantics ling thesaurus:related
ln ling:semantics ai:embedding thesaurus:related
ln ling:semantics dh:knowledge_graph thesaurus:related
def "ling:pragmatics" "Meaning in context and use (語用論)."
ln ling:pragmatics ling thesaurus:related
def "ling:phoneme" "The smallest sound unit distinguishing meaning (音素)."
ln ling:phoneme ling thesaurus:related
def "ling:morpheme" "The smallest meaningful unit (形態素)."
ln ling:morpheme ling thesaurus:related
def "ling:grammar" "The system of rules governing a language (文法)."
ln ling:grammar ling thesaurus:related
def "ling:lexicon" "The vocabulary of a language (語彙)."
ln ling:lexicon ling thesaurus:related
ln ling:lexicon textanal:corpus thesaurus:related
ln ling:lexicon lib:authority_control thesaurus:related
# ── subfields & concepts ──
def "ling:sociolinguistics" "How language varies with society and identity (社会言語学)."
ln ling:sociolinguistics ling thesaurus:related
ln ling:sociolinguistics socio:identity thesaurus:related
ln ling:sociolinguistics socio:social_group thesaurus:related
def "ling:psycholinguistics" "The mental processing of language (心理言語学)."
ln ling:psycholinguistics ling thesaurus:related
ln ling:psycholinguistics devpsy:language_acquisition thesaurus:related
ln ling:psycholinguistics neuro:cerebral_cortex thesaurus:related
def "ling:historical_linguistics" "How languages change and relate over time (歴史言語学)."
ln ling:historical_linguistics ling thesaurus:related
ln ling:historical_linguistics ling:etymology thesaurus:related
ln ling:historical_linguistics oral:oral_tradition thesaurus:related
def "ling:computational_linguistics" "Modelling language by computation (計算言語学)."
ln ling:computational_linguistics ling thesaurus:related
ln ling:computational_linguistics dh:corpus_linguistics thesaurus:related
ln ling:computational_linguistics textanal:corpus thesaurus:related
ln ling:computational_linguistics ai:embedding thesaurus:related
def "ling:language_family" "A group of languages descended from a common ancestor (語族)."
ln ling:language_family ling thesaurus:related
ln ling:language_family dh:network thesaurus:related
ln ling:language_family life:phylogeny thesaurus:related
def "ling:language_change" "The evolution of a language over time."
ln ling:language_change ling thesaurus:related
def "ling:dialect" "A regional or social variety of a language (方言)."
ln ling:dialect ling thesaurus:related
def "ling:etymology" "The origin and history of words (語源)."
ln ling:etymology ling thesaurus:related
ln ling:etymology ling:historical_linguistics thesaurus:related
ln ling:etymology ling:lexicon thesaurus:related
def "ling:universal_grammar" "Chomsky's proposed innate basis of language."
ln ling:universal_grammar ling thesaurus:related
def "ling:sign" "Saussure's unit of signifier and signified — the heart of semiotics (記号)."
ln ling:sign ling thesaurus:related
ln ling:sign dh:semantic_web thesaurus:related
ln ling:sign ling:semantics thesaurus:related
def "ling:bilingualism" "The use of two languages by a speaker or community."
ln ling:bilingualism ling thesaurus:related
