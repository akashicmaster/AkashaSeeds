#!/usr/bin/env python3
# Digital-humanities CAPSTONE — broad cross-linking:
#   app/ontology/base3/dh_capstone.ak
# The DH methods already exist richly (dh:* 37, textanal:* 25, bib:/cite:) but hang
# unconnected to (a) the humanities discipline spines built across this work and
# (b) their mathematical / information-science foundations. This capstone wires BOTH
# directions so the whole ontology becomes analysable:
#   method  --dh:grounded_in-->  math:/cs:/ai:/crosscut:   (the formal foundation)
#   method  --dh:serves------->  the humanities domain it studies
# and adds the latest infosci/math lenses (vector semantics, network science, language
# models, dimensionality reduction) — noting where they ARE Akasha's own machinery.
# dh (top) already exists — only linked.

import os

def esc(s):
    return s.replace('"', "'")

L = [
 "# Akasha ontology — digital humanities CAPSTONE.",
 "# Broad cross-link: wires the existing dh:/textanal: methods to BOTH their math/infosci",
 "# foundations (dh:grounded_in) AND the humanities domains they serve (dh:serves),",
 "# so the whole built ontology becomes analysable. Adds the latest computational",
 "# lenses and closes the loop on Akasha as a DH platform. general-education breadth; research",
 "# depth reserved for level-C packs. Base pack.",
 "",
 "ln dh knowledge:branch:interdisciplinary knowledge:in_branch",
 "ln dh knowledge:branch:humanities thesaurus:related",
 "ln dh cs thesaurus:related",
 "ln dh math thesaurus:related",
]

# ── method families: group the existing dh:/textanal: methods ─────────────────
# (family_slug, gloss, [member atoms], [grounded_in], [serves])
FAMILIES = [
 ("text_analysis",
  "テキスト分析 — reading text at scale by computer: counting, comparing, modelling and mining words.",
  ["dh:text_mining","dh:distant_reading","dh:close_reading","dh:topic_modeling","dh:sentiment_analysis",
   "dh:named_entity_recognition","dh:stylometry","dh:concordance","dh:corpus_linguistics","dh:text_encoding",
   "dh:transcription","dh:scholarly_digital_edition","dh:critical_apparatus",
   "textanal:tf_idf","textanal:cosine_similarity","textanal:burrows_delta","textanal:topic_modeling",
   "textanal:word_embedding","textanal:named_entity_recognition","textanal:stylometry","textanal:ngram",
   "textanal:collocation","textanal:keyness","textanal:type_token_ratio","textanal:concordance","textanal:kwic"],
  ["math:statistics","cs:information_theory","ai:embedding","ling:field:computational"],
  ["lit:movement","textcrit:textual_criticism","ling","person:figure"]),
 ("network_analysis",
  "ネットワーク分析 — treating people, texts and ideas as nodes and links, and measuring the structure.",
  ["dh:social_network_analysis","dh:graph_analysis","dh:network_visualization","dh:centrality",
   "dh:community_detection","dh:bridges","dh:knowledge_graph"],
  ["math:graph_theory","crosscut:network","cs:data_structure"],
  ["person:figure","socio:social_network","cite:citation_network","collab:coauthorship_network","myth:monomyth"]),
 ("spatial",
  "空間人文学 — putting culture on the map: GIS, deep mapping and the geography of the humanities.",
  ["dh:gis","dh:geospatial_humanities","dh:deep_mapping"],
  ["math:geometry","crosscut:scale"],
  ["archaeo","hist:period","admin:city","landmark:landmark"]),
 ("quantitative",
  "計量人文学 — counting culture: quantitative history and cultural analytics.",
  ["dh:quantitative_history","dh:cultural_analytics","dh:temporal_analysis"],
  ["math:statistics","math:probability"],
  ["hist:period","socio","econ:field:econometrics"]),
 ("visualization",
  "可視化 — showing patterns the eye can read: charts, timelines and network graphs.",
  ["dh:data_visualization","dh:timeline"],
  ["math:statistics","crosscut:information"],
  ["hist:period","art:movement"]),
 ("semantic_web",
  "セマンティック・ウェブ — meaning made machine-readable: linked open data, ontologies and knowledge graphs.",
  ["dh:semantic_web","dh:linked_open_data","dh:sparql","dh:ontology_engineering","dh:knowledge_graph"],
  ["cs:data_structure","math:set","crosscut:information"],
  ["ling:field:semantics","semio:semiotics"]),
 ("digitization_3d",
  "デジタル化・三次元復元 — bringing objects and sites into the digital record.",
  ["dh:3d_modeling","dh:photogrammetry","dh:virtual_reconstruction"],
  ["math:geometry","crosscut:scale"],
  ["archaeo","paleo:paleography","anthro:concept:material_culture"]),
]
L += ["", "# ══ method families (grounded in math/infosci, serving the humanities) ══",
      'def "dh:family" "The families of digital-humanities method, each grounded in a formal foundation and serving a humanistic question."',
      "ln dh:family dh sys:part_of"]
for slug, gloss, members, grounded, serves in FAMILIES:
    fid = f"dh:family:{slug}"
    L.append(f'def "{fid}" "{esc(gloss)}"')
    L.append(f"ln {fid} dh:family sys:part_of")
    for m in members:
        L.append(f"ln {m} {fid} sys:part_of")
    for g in grounded:
        L.append(f"ln {fid} {g} dh:grounded_in")
    for s in serves:
        L.append(f"ln {fid} {s} dh:serves")

# ── the latest infosci / math lenses (new) ───────────────────────────────────
# (slug, gloss, [grounded_in], [serves/related], akasha_note)
LENSES = [
 ("vector_semantics",
  "ベクトル意味論 — representing words and texts as points in a space, so that nearness means similarity of meaning (word/document embeddings).",
  ["math:linear_algebra","ai:embedding","cs:information_theory"],
  ["ling:concept:distributional_semantics","textanal:word_embedding","dh:family:text_analysis"], True),
 ("network_science",
  "ネットワーク科学 — the mathematics of connected systems: centrality, community, small-world and scale-free structure.",
  ["math:graph_theory","crosscut:network","crosscut:emergence"],
  ["dh:family:network_analysis","socio:social_network"], True),
 ("dimensionality_reduction",
  "次元削減 — compressing high-dimensional data to its few strongest patterns (PCA, SVD, PPMI, UMAP).",
  ["math:linear_algebra","math:statistics"],
  ["dh:family:text_analysis","dh:cultural_analytics"], True),
 ("statistical_inference",
  "統計的推論 — reasoning from a sample to a claim, with the uncertainty made explicit.",
  ["math:statistics","math:probability"],
  ["dh:family:quantitative","knowledge:method:empirical"], False),
 ("language_models",
  "言語モデル — systems that model the probability of text and now generate and interpret it (LLMs), the newest tool of computational text study.",
  ["ai:llm","ai:multi_llm_orchestration","math:probability"],
  ["ling:field:computational","dh:family:text_analysis"], True),
 ("vector_search",
  "ベクトル検索 — retrieving by meaning rather than keyword, by nearest-neighbour search over embeddings.",
  ["ai:vector_database","ai:embedding","math:linear_algebra"],
  ["dh:knowledge_graph","dh:family:semantic_web"], True),
]
L += ["", "# ══ the latest information-science / mathematical lenses ══",
      'def "dh:lens" "The formal, computational lenses through which digital humanities analyses culture (最新の情報科学・数学的視点)."',
      "ln dh:lens dh sys:part_of"]
for slug, gloss, grounded, related, akasha in LENSES:
    lid = f"dh:lens:{slug}"
    L.append(f'def "{lid}" "{esc(gloss)}"')
    L.append(f"ln {lid} dh:lens sys:part_of")
    for g in grounded:
        L.append(f"ln {lid} {g} dh:grounded_in")
    for r in related:
        L.append(f"ln {lid} {r} thesaurus:related")
    if akasha:
        L.append(f"ln {lid} ai:akasha_pattern thesaurus:related")

# ── broad cross-links: DH ↔ every humanities spine built across this work ─────
# each domain spine becomes a corpus/network DH can analyse
SPINES = [
 ("lit:movement", "literature"),
 ("art:movement", "art history"),
 ("music:period", "music history"),
 ("phil:philosophy", "philosophy"),
 ("religion:religion", "religion"),
 ("hist:period", "history"),
 ("anthro:anthropology", "anthropology"),
 ("folk:folklore", "folklore"),
 ("ling", "linguistics"),
 ("semio:semiotics", "semiotics"),
 ("paleo:paleography", "paleography"),
 ("epic:epic", "the epics"),
]
L += ["", "# ══ broad cross-links — every humanities spine is now an analysable corpus ══"]
for node, _label in SPINES:
    L.append(f"ln dh {node} dh:can_analyse")

# ── the Akasha capstone: Akasha IS a DH platform ─────────────────────────────
L += ["", "# ══ capstone — Akasha as a working DH platform ══",
 'def "dh:concept:akasha_as_platform" "Akasha is itself a digital-humanities platform: content-addressed atoms and typed links ARE a knowledge graph and linked-open-data; its learned semantic layer (PPMI+SVD over the graph) IS vector semantics and dimensionality reduction; graph traversal and dream-staging ARE network analysis and distant reading. The methods DH reaches for are the engine\'s own operations."',
 "ln dh:concept:akasha_as_platform dh sys:part_of",
 "ln dh:concept:akasha_as_platform ai:akasha_pattern thesaurus:related",
 "ln dh:concept:akasha_as_platform dh:knowledge_graph thesaurus:related",
 "ln dh:concept:akasha_as_platform dh:distant_reading thesaurus:related",
 "ln dh:concept:akasha_as_platform dh:lens:vector_semantics thesaurus:related",
 "ln dh:concept:akasha_as_platform dh:lens:network_science thesaurus:related",
 "ln dh:concept:akasha_as_platform ling:concept:distributional_semantics thesaurus:related",
 "ln dh:concept:akasha_as_platform semio:concept:atom_as_sign thesaurus:related",
 "ln dh:concept:akasha_as_platform crosscut:information thesaurus:related",
 'def "dh:concept:analysable_ontology" "Because every domain built across this work is a spine of linked atoms, the ontology itself is a corpus: the same centrality, community-detection and distant-reading methods that DH applies to archives apply, unchanged, to Akasha\'s own knowledge — the graph analyses itself."',
 "ln dh:concept:analysable_ontology dh sys:part_of",
 "ln dh:concept:analysable_ontology knowledge thesaurus:related",
 "ln dh:concept:analysable_ontology dh:family:network_analysis thesaurus:related",
 "ln dh:concept:analysable_ontology crosscut:emergence thesaurus:related",
]

path = "app/ontology/base3/dh_capstone.ak"
os.makedirs(os.path.dirname(path), exist_ok=True)
with open(path, "w", encoding="utf-8") as f:
    f.write("\n".join(L) + "\n")
nd = sum(1 for l in L if l.startswith("def "))
nl = sum(1 for l in L if l.startswith("ln "))
print(f"{path}: def={nd} ln={nl} ({len(L)} lines)")
