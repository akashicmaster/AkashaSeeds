# Akasha ontology — textual criticism + detailed text analysis (本文批判・テキスト分析).
# How scholars establish a text from witnesses, and the computational methods
# that read texts at scale. Bridges DH, TEI, ai:, and the manuscript sources.
# Base pack.

def "textcrit" "Textual criticism — reconstructing a text from its witnesses."
def "textcrit:textual_criticism" "The discipline of recovering an authoritative text from imperfect copies (本文批判)."
ln textcrit:textual_criticism textcrit thesaurus:related
def "textcrit:witness" "Any manuscript, print or citation attesting a text."
ln textcrit:witness textcrit thesaurus:related
ln textcrit:witness ms:codex thesaurus:related
def "textcrit:collation" "The systematic comparison of witnesses to record their differences."
ln textcrit:collation textcrit thesaurus:related
ln textcrit:collation dh:collation thesaurus:related
ln textcrit:collation ms:codex thesaurus:related
def "textcrit:variant_reading" "A point where witnesses differ (異読)."
ln textcrit:variant_reading textcrit thesaurus:related
def "textcrit:apparatus_criticus" "The footnote apparatus recording variants and their witnesses (校異)."
ln textcrit:apparatus_criticus textcrit thesaurus:related
ln textcrit:apparatus_criticus dh:critical_apparatus thesaurus:related
def "textcrit:stemmatics" "Reconstructing the family tree of witnesses from shared errors (系統学)."
ln textcrit:stemmatics textcrit thesaurus:related
ln textcrit:stemmatics sys:network thesaurus:related
def "textcrit:stemma_codicum" "The genealogical tree of the surviving copies."
ln textcrit:stemma_codicum textcrit thesaurus:related
def "textcrit:archetype" "The lost common ancestor of all surviving witnesses."
ln textcrit:archetype textcrit thesaurus:related
def "textcrit:recension" "Establishing the text of the archetype by comparing witnesses (Lachmann's method)."
ln textcrit:recension textcrit thesaurus:related
def "textcrit:conjecture" "An editor's proposed reading absent from all witnesses (推定)."
ln textcrit:conjecture textcrit thesaurus:related
def "textcrit:emendation" "Correcting a corrupt passage, by witness or by conjecture."
ln textcrit:emendation textcrit thesaurus:related
def "textcrit:lacuna" "A gap where text is missing."
ln textcrit:lacuna textcrit thesaurus:related
def "textcrit:interpolation" "Matter later inserted into the text, not original."
ln textcrit:interpolation textcrit thesaurus:related
def "textcrit:lectio_difficilior" "The 'harder reading' is likelier original — scribes simplify."
ln textcrit:lectio_difficilior textcrit thesaurus:related
def "textcrit:contamination" "Mixture of readings from more than one line, wrecking a clean stemma."
ln textcrit:contamination textcrit thesaurus:related
def "textcrit:crux" "A hopelessly corrupt passage, marked with daggers (†…†)."
ln textcrit:crux textcrit thesaurus:related
def "textcrit:haplography" "Accidental omission of one of two similar sequences."
ln textcrit:haplography textcrit thesaurus:related
def "textcrit:dittography" "Accidental repetition of a letter, word or line."
ln textcrit:dittography textcrit thesaurus:related
def "textcrit:homoeoteleuton" "Eye-skip between like endings, dropping the text between."
ln textcrit:homoeoteleuton textcrit thesaurus:related
def "textcrit:critical_edition" "An edition presenting a reconstructed text with apparatus."
ln textcrit:critical_edition textcrit thesaurus:related
ln textcrit:critical_edition dh:scholarly_digital_edition thesaurus:related
ln textcrit:critical_edition metastd:tei thesaurus:related
def "textcrit:diplomatic_edition" "An edition reproducing a single witness exactly."
ln textcrit:diplomatic_edition textcrit thesaurus:related
ln textcrit:diplomatic_edition ms:diplomatic_transcription thesaurus:related
def "textcrit:editio_princeps" "The first printed edition of a text."
ln textcrit:editio_princeps textcrit thesaurus:related
def "textcrit:sigla" "The letter-symbols standing for each witness in the apparatus."
ln textcrit:sigla textcrit thesaurus:related
def "textanal" "Computational text analysis."
def "textanal:tokenization" "Splitting text into words/tokens, the first NLP step."
ln textanal:tokenization textanal thesaurus:related
def "textanal:lemmatization" "Reducing word-forms to their dictionary lemma."
ln textanal:lemmatization textanal thesaurus:related
def "textanal:pos_tagging" "Labelling each token with its part of speech."
ln textanal:pos_tagging textanal thesaurus:related
def "textanal:dependency_parsing" "Recovering grammatical relations between words."
ln textanal:dependency_parsing textanal thesaurus:related
def "textanal:morphological_analysis" "Analysing word structure — vital for inflected/classical languages."
ln textanal:morphological_analysis textanal thesaurus:related
ln textanal:morphological_analysis person:field:linguistics_scholarship thesaurus:related
def "textanal:collocation" "Words that co-occur more than chance (statistical association)."
ln textanal:collocation textanal thesaurus:related
def "textanal:concordance" "An index of every occurrence of a word in context."
ln textanal:concordance textanal thesaurus:related
ln textanal:concordance dh:concordance thesaurus:related
def "textanal:kwic" "Keyword-in-context: the term centred with its surrounding words."
ln textanal:kwic textanal thesaurus:related
def "textanal:ngram" "A contiguous sequence of n tokens, a basic model of text."
ln textanal:ngram textanal thesaurus:related
def "textanal:type_token_ratio" "Types over tokens — a measure of lexical variety."
ln textanal:type_token_ratio textanal thesaurus:related
def "textanal:hapax_legomenon" "A word occurring only once in a corpus."
ln textanal:hapax_legomenon textanal thesaurus:related
def "textanal:keyness" "How characteristic a word is of one corpus vs a reference."
ln textanal:keyness textanal thesaurus:related
def "textanal:tf_idf" "Term frequency × inverse document frequency — classic term weighting."
ln textanal:tf_idf textanal thesaurus:related
def "textanal:word_embedding" "A dense vector placing words by distributional meaning."
ln textanal:word_embedding textanal thesaurus:related
ln textanal:word_embedding ai:embedding thesaurus:related
ln textanal:word_embedding data:embedding thesaurus:related
def "textanal:cosine_similarity" "The angle-based similarity of two vectors."
ln textanal:cosine_similarity textanal thesaurus:related
ln textanal:cosine_similarity ai:embedding thesaurus:related
def "textanal:topic_modeling" "Discovering latent themes (e.g. LDA) across a corpus."
ln textanal:topic_modeling textanal thesaurus:related
ln textanal:topic_modeling dh:topic_modeling thesaurus:related
def "textanal:stylometry" "Quantifying style, esp. for authorship attribution."
ln textanal:stylometry textanal thesaurus:related
ln textanal:stylometry dh:stylometry thesaurus:related
def "textanal:burrows_delta" "A standard distance measure for authorship attribution."
ln textanal:burrows_delta textanal thesaurus:related
ln textanal:burrows_delta dh:stylometry thesaurus:related
def "textanal:named_entity_recognition" "Tagging persons, places and dates in text."
ln textanal:named_entity_recognition textanal thesaurus:related
ln textanal:named_entity_recognition dh:named_entity_recognition thesaurus:related
def "textanal:corpus" "A structured body of text assembled for analysis (コーパス)."
ln textanal:corpus textanal thesaurus:related
ln textanal:corpus dh:corpus_linguistics thesaurus:related
ln textanal:corpus person:field:linguistics_scholarship thesaurus:related
def "textanal:treebank" "A corpus annotated with parse trees."
ln textanal:treebank textanal thesaurus:related
def "textanal:annotation" "Adding analytic labels to text; gold-standard annotation trains and tests tools."
ln textanal:annotation textanal thesaurus:related
ln textanal:annotation metastd:tei thesaurus:related
def "textanal:ocr" "Optical character recognition — machine reading of printed text."
ln textanal:ocr textanal thesaurus:related
ln textanal:ocr digarch:digitization thesaurus:related
def "textanal:htr" "Handwritten text recognition — machine reading of manuscript hands (自動翻刻)."
ln textanal:htr textanal thesaurus:related
ln textanal:htr ms:script thesaurus:related
ln textanal:htr dh:transcription thesaurus:related
def "textanal:normalization" "Regularising spelling/forms so historical variants can be compared."
ln textanal:normalization textanal thesaurus:related
