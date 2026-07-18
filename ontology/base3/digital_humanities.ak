# Akasha ontology — digital humanities, thick + cross-disciplinary.
# DH is bridging by nature: humanities method ↔ computation ↔ GLAM/linked data.
# Each method carries dh:bridges edges to the field(s) it connects — and many
# land squarely on Akasha's own graph/thesaurus/linked-data core. Base pack.

def "dh" "Digital humanities — computation in service of humanistic inquiry."
def "dh:bridges" "Connects a humanities method to another discipline."
def "dh_area:text" "text & language analysis"
def "dh_area:network" "network analysis"
def "dh_area:spatial" "spatial/GIS"
def "dh_area:temporal" "time & chronology"
def "dh_area:visual" "visualization & cultural analytics"
def "dh_area:edition" "digital scholarly editions"
def "dh_area:linked_data" "semantic web & linked data"
def "dh_area:multimedia" "3D & multimedia"
def "dh_area:crowdsourcing" "public participation"

# ── DH methods, each bridged to the field(s) it connects ──
def "dh:text_mining" "Text mining."
ln dh:text_mining dh_area:text dh:area
ln dh:text_mining dh thesaurus:related
ln dh:text_mining person:field:literature dh:bridges
ln dh:text_mining ai:embedding dh:bridges
ln dh:text_mining data:embedding dh:bridges
def "dh:distant_reading" "Distant reading (遠読)."
ln dh:distant_reading dh_area:text dh:area
ln dh:distant_reading dh thesaurus:related
ln dh:distant_reading person:field:literature dh:bridges
ln dh:distant_reading bib:bibliometrics dh:bridges
def "dh:close_reading" "Close reading (精読)."
ln dh:close_reading dh_area:text dh:area
ln dh:close_reading dh thesaurus:related
ln dh:close_reading person:field:literature dh:bridges
def "dh:corpus_linguistics" "Corpus linguistics (コーパス言語学)."
ln dh:corpus_linguistics dh_area:text dh:area
ln dh:corpus_linguistics dh thesaurus:related
ln dh:corpus_linguistics person:field:linguistics_scholarship dh:bridges
ln dh:corpus_linguistics lang:corpus dh:bridges
def "dh:concordance" "Concordance (コンコーダンス)."
ln dh:concordance dh_area:text dh:area
ln dh:concordance dh thesaurus:related
ln dh:concordance person:field:linguistics_scholarship dh:bridges
def "dh:topic_modeling" "Topic modeling (トピックモデル)."
ln dh:topic_modeling dh_area:text dh:area
ln dh:topic_modeling dh thesaurus:related
ln dh:topic_modeling ai:embedding dh:bridges
ln dh:topic_modeling person:field:literature dh:bridges
def "dh:stylometry" "Stylometry (文体計量)."
ln dh:stylometry dh_area:text dh:area
ln dh:stylometry dh thesaurus:related
ln dh:stylometry person:field:literature dh:bridges
ln dh:stylometry person:field:mathematics dh:bridges
def "dh:named_entity_recognition" "Named entity recognition (固有表現抽出)."
ln dh:named_entity_recognition dh_area:text dh:area
ln dh:named_entity_recognition dh thesaurus:related
ln dh:named_entity_recognition ai:embedding dh:bridges
ln dh:named_entity_recognition lang:corpus dh:bridges
def "dh:sentiment_analysis" "Sentiment analysis."
ln dh:sentiment_analysis dh_area:text dh:area
ln dh:sentiment_analysis dh thesaurus:related
ln dh:sentiment_analysis ai:embedding dh:bridges
ln dh:sentiment_analysis emo:joy dh:bridges
def "dh:text_encoding" "Text encoding (テキスト符号化)."
ln dh:text_encoding dh_area:edition dh:area
ln dh:text_encoding dh thesaurus:related
ln dh:text_encoding metastd:tei dh:bridges
ln dh:text_encoding metastd:rdf dh:bridges
def "dh:social_network_analysis" "Social network analysis (社会ネットワーク分析)."
ln dh:social_network_analysis dh_area:network dh:area
ln dh:social_network_analysis dh thesaurus:related
ln dh:social_network_analysis person:field:science dh:bridges
ln dh:social_network_analysis sys:network dh:bridges
ln dh:social_network_analysis collab:coauthorship_network dh:bridges
def "dh:network_visualization" "Network visualization."
ln dh:network_visualization dh_area:network dh:area
ln dh:network_visualization dh thesaurus:related
ln dh:network_visualization sys:network dh:bridges
ln dh:network_visualization data:embedding dh:bridges
def "dh:centrality" "Centrality."
ln dh:centrality dh_area:network dh:area
ln dh:centrality dh thesaurus:related
ln dh:centrality sys:network dh:bridges
ln dh:centrality cite:citation_network dh:bridges
def "dh:community_detection" "Community detection."
ln dh:community_detection dh_area:network dh:area
ln dh:community_detection dh thesaurus:related
ln dh:community_detection sys:network dh:bridges
ln dh:community_detection cite:citation_network dh:bridges
def "dh:graph_analysis" "Graph analysis."
ln dh:graph_analysis dh_area:network dh:area
ln dh:graph_analysis dh thesaurus:related
ln dh:graph_analysis sys:network dh:bridges
ln dh:graph_analysis cite:citation_network dh:bridges
ln dh:graph_analysis collab:coauthorship_network dh:bridges
def "dh:gis" "Gis."
ln dh:gis dh_area:spatial dh:area
ln dh:gis dh thesaurus:related
ln dh:gis ce:gis dh:bridges
ln dh:gis person:field:exploration_navigation dh:bridges
def "dh:geospatial_humanities" "Geospatial humanities (空間人文学)."
ln dh:geospatial_humanities dh_area:spatial dh:area
ln dh:geospatial_humanities dh thesaurus:related
ln dh:geospatial_humanities ce:gis dh:bridges
ln dh:geospatial_humanities person:field:exploration_navigation dh:bridges
def "dh:deep_mapping" "Deep mapping."
ln dh:deep_mapping dh_area:spatial dh:area
ln dh:deep_mapping dh thesaurus:related
ln dh:deep_mapping ce:gis dh:bridges
ln dh:deep_mapping person:field:literature dh:bridges
def "dh:temporal_analysis" "Temporal analysis."
ln dh:temporal_analysis dh_area:temporal dh:area
ln dh:temporal_analysis dh thesaurus:related
ln dh:temporal_analysis person:field:literature dh:bridges
def "dh:timeline" "Timeline."
ln dh:timeline dh_area:temporal dh:area
ln dh:timeline dh thesaurus:related
ln dh:timeline person:field:literature dh:bridges
def "dh:data_visualization" "Data visualization."
ln dh:data_visualization dh_area:visual dh:area
ln dh:data_visualization dh thesaurus:related
ln dh:data_visualization data:embedding dh:bridges
ln dh:data_visualization person:field:visual_arts dh:bridges
def "dh:cultural_analytics" "Cultural analytics (カルチュラル・アナリティクス)."
ln dh:cultural_analytics dh_area:visual dh:area
ln dh:cultural_analytics dh thesaurus:related
ln dh:cultural_analytics person:field:visual_arts dh:bridges
ln dh:cultural_analytics data:embedding dh:bridges
def "dh:quantitative_history" "Quantitative history (計量史学)."
ln dh:quantitative_history dh_area:visual dh:area
ln dh:quantitative_history dh thesaurus:related
ln dh:quantitative_history person:field:mathematics dh:bridges
ln dh:quantitative_history bib:bibliometrics dh:bridges
def "dh:scholarly_digital_edition" "Scholarly digital edition (学術的電子版)."
ln dh:scholarly_digital_edition dh_area:edition dh:area
ln dh:scholarly_digital_edition dh thesaurus:related
ln dh:scholarly_digital_edition metastd:tei dh:bridges
ln dh:scholarly_digital_edition lib:cataloging dh:bridges
def "dh:critical_apparatus" "Critical apparatus."
ln dh:critical_apparatus dh_area:edition dh:area
ln dh:critical_apparatus dh thesaurus:related
ln dh:critical_apparatus person:field:literature dh:bridges
ln dh:critical_apparatus lib:cataloging dh:bridges
def "dh:transcription" "Transcription."
ln dh:transcription dh_area:edition dh:area
ln dh:transcription dh thesaurus:related
ln dh:transcription lib:cataloging dh:bridges
ln dh:transcription digarch:digitization dh:bridges
def "dh:collation" "Collation."
ln dh:collation dh_area:edition dh:area
ln dh:collation dh thesaurus:related
ln dh:collation person:field:literature dh:bridges
def "dh:linked_open_data" "Linked open data (リンクト・オープン・データ)."
ln dh:linked_open_data dh_area:linked_data dh:area
ln dh:linked_open_data dh thesaurus:related
ln dh:linked_open_data metastd:rdf dh:bridges
ln dh:linked_open_data metastd:dublin_core dh:bridges
ln dh:linked_open_data sys:network dh:bridges
def "dh:semantic_web" "Semantic web."
ln dh:semantic_web dh_area:linked_data dh:area
ln dh:semantic_web dh thesaurus:related
ln dh:semantic_web metastd:rdf dh:bridges
ln dh:semantic_web sys:network dh:bridges
def "dh:knowledge_graph" "Knowledge graph (知識グラフ)."
ln dh:knowledge_graph dh_area:linked_data dh:area
ln dh:knowledge_graph dh thesaurus:related
ln dh:knowledge_graph sys:network dh:bridges
ln dh:knowledge_graph cite:citation_network dh:bridges
ln dh:knowledge_graph digarch:controlled_vocabulary dh:bridges
def "dh:ontology_engineering" "Ontology engineering."
ln dh:ontology_engineering dh_area:linked_data dh:area
ln dh:ontology_engineering dh thesaurus:related
ln dh:ontology_engineering metastd:cidoc_crm dh:bridges
ln dh:ontology_engineering digarch:controlled_vocabulary dh:bridges
def "dh:sparql" "Sparql."
ln dh:sparql dh_area:linked_data dh:area
ln dh:sparql dh thesaurus:related
ln dh:sparql metastd:rdf dh:bridges
def "dh:3d_modeling" "3d modeling."
ln dh:3d_modeling dh_area:multimedia dh:area
ln dh:3d_modeling dh thesaurus:related
ln dh:3d_modeling person:field:architecture dh:bridges
ln dh:3d_modeling digarch:digital_object dh:bridges
def "dh:virtual_reconstruction" "Virtual reconstruction."
ln dh:virtual_reconstruction dh_area:multimedia dh:area
ln dh:virtual_reconstruction dh thesaurus:related
ln dh:virtual_reconstruction person:field:architecture dh:bridges
ln dh:virtual_reconstruction digarch:digital_preservation dh:bridges
def "dh:photogrammetry" "Photogrammetry."
ln dh:photogrammetry dh_area:multimedia dh:area
ln dh:photogrammetry dh thesaurus:related
ln dh:photogrammetry ce:lidar_mapping dh:bridges
ln dh:photogrammetry digarch:digitization dh:bridges
def "dh:crowdsourcing" "Crowdsourcing (クラウドソーシング)."
ln dh:crowdsourcing dh_area:crowdsourcing dh:area
ln dh:crowdsourcing dh thesaurus:related
ln dh:crowdsourcing os:citizen_science dh:bridges
ln dh:crowdsourcing lib:reference_service dh:bridges

# ── DH ↔ Akasha: the linked-data methods ARE Akasha's substrate ──
ln dh:knowledge_graph dh thesaurus:related
ln dh:linked_open_data digarch:controlled_vocabulary thesaurus:related
ln dh:ontology_engineering digarch:controlled_vocabulary thesaurus:related
ln dh:semantic_web metastd:rdf thesaurus:related
