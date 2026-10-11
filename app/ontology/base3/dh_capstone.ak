# Akasha ontology — digital humanities CAPSTONE.
# Broad cross-link: wires the existing dh:/textanal: methods to BOTH their math/infosci
# foundations (dh:grounded_in) AND the humanities domains they serve (dh:serves),
# so the whole built ontology becomes analysable. Adds the latest computational
# lenses and closes the loop on Akasha as a DH platform. general-education breadth; research
# depth reserved for level-C packs. Base pack.

ln dh knowledge:branch:interdisciplinary knowledge:in_branch
ln dh knowledge:branch:humanities thesaurus:related
ln dh cs thesaurus:related
ln dh math thesaurus:related

# ══ method families (grounded in math/infosci, serving the humanities) ══
def "dh:family" "The families of digital-humanities method, each grounded in a formal foundation and serving a humanistic question."
ln dh:family dh sys:part_of
def "dh:family:text_analysis" "テキスト分析 — reading text at scale by computer: counting, comparing, modelling and mining words."
ln dh:family:text_analysis dh:family sys:part_of
ln dh:text_mining dh:family:text_analysis sys:part_of
ln dh:distant_reading dh:family:text_analysis sys:part_of
ln dh:close_reading dh:family:text_analysis sys:part_of
ln dh:topic_modeling dh:family:text_analysis sys:part_of
ln dh:sentiment_analysis dh:family:text_analysis sys:part_of
ln dh:named_entity_recognition dh:family:text_analysis sys:part_of
ln dh:stylometry dh:family:text_analysis sys:part_of
ln dh:concordance dh:family:text_analysis sys:part_of
ln dh:corpus_linguistics dh:family:text_analysis sys:part_of
ln dh:text_encoding dh:family:text_analysis sys:part_of
ln dh:transcription dh:family:text_analysis sys:part_of
ln dh:scholarly_digital_edition dh:family:text_analysis sys:part_of
ln dh:critical_apparatus dh:family:text_analysis sys:part_of
ln textanal:tf_idf dh:family:text_analysis sys:part_of
ln textanal:cosine_similarity dh:family:text_analysis sys:part_of
ln textanal:burrows_delta dh:family:text_analysis sys:part_of
ln textanal:topic_modeling dh:family:text_analysis sys:part_of
ln textanal:word_embedding dh:family:text_analysis sys:part_of
ln textanal:named_entity_recognition dh:family:text_analysis sys:part_of
ln textanal:stylometry dh:family:text_analysis sys:part_of
ln textanal:ngram dh:family:text_analysis sys:part_of
ln textanal:collocation dh:family:text_analysis sys:part_of
ln textanal:keyness dh:family:text_analysis sys:part_of
ln textanal:type_token_ratio dh:family:text_analysis sys:part_of
ln textanal:concordance dh:family:text_analysis sys:part_of
ln textanal:kwic dh:family:text_analysis sys:part_of
ln dh:family:text_analysis math:statistics dh:grounded_in
ln dh:family:text_analysis cs:information_theory dh:grounded_in
ln dh:family:text_analysis ai:embedding dh:grounded_in
ln dh:family:text_analysis ling:field:computational dh:grounded_in
ln dh:family:text_analysis lit:movement dh:serves
ln dh:family:text_analysis textcrit:textual_criticism dh:serves
ln dh:family:text_analysis ling dh:serves
ln dh:family:text_analysis person:figure dh:serves
def "dh:family:network_analysis" "ネットワーク分析 — treating people, texts and ideas as nodes and links, and measuring the structure."
ln dh:family:network_analysis dh:family sys:part_of
ln dh:social_network_analysis dh:family:network_analysis sys:part_of
ln dh:graph_analysis dh:family:network_analysis sys:part_of
ln dh:network_visualization dh:family:network_analysis sys:part_of
ln dh:centrality dh:family:network_analysis sys:part_of
ln dh:community_detection dh:family:network_analysis sys:part_of
ln dh:bridges dh:family:network_analysis sys:part_of
ln dh:knowledge_graph dh:family:network_analysis sys:part_of
ln dh:family:network_analysis math:graph_theory dh:grounded_in
ln dh:family:network_analysis crosscut:network dh:grounded_in
ln dh:family:network_analysis cs:data_structure dh:grounded_in
ln dh:family:network_analysis person:figure dh:serves
ln dh:family:network_analysis socio:social_network dh:serves
ln dh:family:network_analysis cite:citation_network dh:serves
ln dh:family:network_analysis collab:coauthorship_network dh:serves
ln dh:family:network_analysis myth:monomyth dh:serves
def "dh:family:spatial" "空間人文学 — putting culture on the map: GIS, deep mapping and the geography of the humanities."
ln dh:family:spatial dh:family sys:part_of
ln dh:gis dh:family:spatial sys:part_of
ln dh:geospatial_humanities dh:family:spatial sys:part_of
ln dh:deep_mapping dh:family:spatial sys:part_of
ln dh:family:spatial math:geometry dh:grounded_in
ln dh:family:spatial crosscut:scale dh:grounded_in
ln dh:family:spatial archaeo dh:serves
ln dh:family:spatial hist:period dh:serves
ln dh:family:spatial admin:city dh:serves
ln dh:family:spatial landmark:landmark dh:serves
def "dh:family:quantitative" "計量人文学 — counting culture: quantitative history and cultural analytics."
ln dh:family:quantitative dh:family sys:part_of
ln dh:quantitative_history dh:family:quantitative sys:part_of
ln dh:cultural_analytics dh:family:quantitative sys:part_of
ln dh:temporal_analysis dh:family:quantitative sys:part_of
ln dh:family:quantitative math:statistics dh:grounded_in
ln dh:family:quantitative math:probability dh:grounded_in
ln dh:family:quantitative hist:period dh:serves
ln dh:family:quantitative socio dh:serves
ln dh:family:quantitative econ:field:econometrics dh:serves
def "dh:family:visualization" "可視化 — showing patterns the eye can read: charts, timelines and network graphs."
ln dh:family:visualization dh:family sys:part_of
ln dh:data_visualization dh:family:visualization sys:part_of
ln dh:timeline dh:family:visualization sys:part_of
ln dh:family:visualization math:statistics dh:grounded_in
ln dh:family:visualization crosscut:information dh:grounded_in
ln dh:family:visualization hist:period dh:serves
ln dh:family:visualization art:movement dh:serves
def "dh:family:semantic_web" "セマンティック・ウェブ — meaning made machine-readable: linked open data, ontologies and knowledge graphs."
ln dh:family:semantic_web dh:family sys:part_of
ln dh:semantic_web dh:family:semantic_web sys:part_of
ln dh:linked_open_data dh:family:semantic_web sys:part_of
ln dh:sparql dh:family:semantic_web sys:part_of
ln dh:ontology_engineering dh:family:semantic_web sys:part_of
ln dh:knowledge_graph dh:family:semantic_web sys:part_of
ln dh:family:semantic_web cs:data_structure dh:grounded_in
ln dh:family:semantic_web math:set dh:grounded_in
ln dh:family:semantic_web crosscut:information dh:grounded_in
ln dh:family:semantic_web ling:field:semantics dh:serves
ln dh:family:semantic_web semio:semiotics dh:serves
def "dh:family:digitization_3d" "デジタル化・三次元復元 — bringing objects and sites into the digital record."
ln dh:family:digitization_3d dh:family sys:part_of
ln dh:3d_modeling dh:family:digitization_3d sys:part_of
ln dh:photogrammetry dh:family:digitization_3d sys:part_of
ln dh:virtual_reconstruction dh:family:digitization_3d sys:part_of
ln dh:family:digitization_3d math:geometry dh:grounded_in
ln dh:family:digitization_3d crosscut:scale dh:grounded_in
ln dh:family:digitization_3d archaeo dh:serves
ln dh:family:digitization_3d paleo:paleography dh:serves
ln dh:family:digitization_3d anthro:concept:material_culture dh:serves

# ══ the latest information-science / mathematical lenses ══
def "dh:lens" "The formal, computational lenses through which digital humanities analyses culture (最新の情報科学・数学的視点)."
ln dh:lens dh sys:part_of
def "dh:lens:vector_semantics" "ベクトル意味論 — representing words and texts as points in a space, so that nearness means similarity of meaning (word/document embeddings)."
ln dh:lens:vector_semantics dh:lens sys:part_of
ln dh:lens:vector_semantics math:linear_algebra dh:grounded_in
ln dh:lens:vector_semantics ai:embedding dh:grounded_in
ln dh:lens:vector_semantics cs:information_theory dh:grounded_in
ln dh:lens:vector_semantics ling:concept:distributional_semantics thesaurus:related
ln dh:lens:vector_semantics textanal:word_embedding thesaurus:related
ln dh:lens:vector_semantics dh:family:text_analysis thesaurus:related
ln dh:lens:vector_semantics ai:akasha_pattern thesaurus:related
def "dh:lens:network_science" "ネットワーク科学 — the mathematics of connected systems: centrality, community, small-world and scale-free structure."
ln dh:lens:network_science dh:lens sys:part_of
ln dh:lens:network_science math:graph_theory dh:grounded_in
ln dh:lens:network_science crosscut:network dh:grounded_in
ln dh:lens:network_science crosscut:emergence dh:grounded_in
ln dh:lens:network_science dh:family:network_analysis thesaurus:related
ln dh:lens:network_science socio:social_network thesaurus:related
ln dh:lens:network_science ai:akasha_pattern thesaurus:related
def "dh:lens:dimensionality_reduction" "次元削減 — compressing high-dimensional data to its few strongest patterns (PCA, SVD, PPMI, UMAP)."
ln dh:lens:dimensionality_reduction dh:lens sys:part_of
ln dh:lens:dimensionality_reduction math:linear_algebra dh:grounded_in
ln dh:lens:dimensionality_reduction math:statistics dh:grounded_in
ln dh:lens:dimensionality_reduction dh:family:text_analysis thesaurus:related
ln dh:lens:dimensionality_reduction dh:cultural_analytics thesaurus:related
ln dh:lens:dimensionality_reduction ai:akasha_pattern thesaurus:related
def "dh:lens:statistical_inference" "統計的推論 — reasoning from a sample to a claim, with the uncertainty made explicit."
ln dh:lens:statistical_inference dh:lens sys:part_of
ln dh:lens:statistical_inference math:statistics dh:grounded_in
ln dh:lens:statistical_inference math:probability dh:grounded_in
ln dh:lens:statistical_inference dh:family:quantitative thesaurus:related
ln dh:lens:statistical_inference knowledge:method:empirical thesaurus:related
def "dh:lens:language_models" "言語モデル — systems that model the probability of text and now generate and interpret it (LLMs), the newest tool of computational text study."
ln dh:lens:language_models dh:lens sys:part_of
ln dh:lens:language_models ai:llm dh:grounded_in
ln dh:lens:language_models ai:multi_llm_orchestration dh:grounded_in
ln dh:lens:language_models math:probability dh:grounded_in
ln dh:lens:language_models ling:field:computational thesaurus:related
ln dh:lens:language_models dh:family:text_analysis thesaurus:related
ln dh:lens:language_models ai:akasha_pattern thesaurus:related
def "dh:lens:vector_search" "ベクトル検索 — retrieving by meaning rather than keyword, by nearest-neighbour search over embeddings."
ln dh:lens:vector_search dh:lens sys:part_of
ln dh:lens:vector_search ai:vector_database dh:grounded_in
ln dh:lens:vector_search ai:embedding dh:grounded_in
ln dh:lens:vector_search math:linear_algebra dh:grounded_in
ln dh:lens:vector_search dh:knowledge_graph thesaurus:related
ln dh:lens:vector_search dh:family:semantic_web thesaurus:related
ln dh:lens:vector_search ai:akasha_pattern thesaurus:related

# ══ broad cross-links — every humanities spine is now an analysable corpus ══
ln dh lit:movement dh:can_analyse
ln dh art:movement dh:can_analyse
ln dh music:period dh:can_analyse
ln dh phil:philosophy dh:can_analyse
ln dh religion:religion dh:can_analyse
ln dh hist:period dh:can_analyse
ln dh anthro:anthropology dh:can_analyse
ln dh folk:folklore dh:can_analyse
ln dh ling dh:can_analyse
ln dh semio:semiotics dh:can_analyse
ln dh paleo:paleography dh:can_analyse
ln dh epic:epic dh:can_analyse

# ══ capstone — Akasha as a working DH platform ══
def "dh:concept:akasha_as_platform" "Akasha is itself a digital-humanities platform: content-addressed atoms and typed links ARE a knowledge graph and linked-open-data; its learned semantic layer (PPMI+SVD over the graph) IS vector semantics and dimensionality reduction; graph traversal and dream-staging ARE network analysis and distant reading. The methods DH reaches for are the engine's own operations."
ln dh:concept:akasha_as_platform dh sys:part_of
ln dh:concept:akasha_as_platform ai:akasha_pattern thesaurus:related
ln dh:concept:akasha_as_platform dh:knowledge_graph thesaurus:related
ln dh:concept:akasha_as_platform dh:distant_reading thesaurus:related
ln dh:concept:akasha_as_platform dh:lens:vector_semantics thesaurus:related
ln dh:concept:akasha_as_platform dh:lens:network_science thesaurus:related
ln dh:concept:akasha_as_platform ling:concept:distributional_semantics thesaurus:related
ln dh:concept:akasha_as_platform semio:concept:atom_as_sign thesaurus:related
ln dh:concept:akasha_as_platform crosscut:information thesaurus:related
def "dh:concept:analysable_ontology" "Because every domain built across this work is a spine of linked atoms, the ontology itself is a corpus: the same centrality, community-detection and distant-reading methods that DH applies to archives apply, unchanged, to Akasha's own knowledge — the graph analyses itself."
ln dh:concept:analysable_ontology dh sys:part_of
ln dh:concept:analysable_ontology knowledge thesaurus:related
ln dh:concept:analysable_ontology dh:family:network_analysis thesaurus:related
ln dh:concept:analysable_ontology crosscut:emergence thesaurus:related
