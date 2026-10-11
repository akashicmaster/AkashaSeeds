# Akasha ontology — Level-C frames.
# The A/B/C tier policy: A = light, all editions; B = broad-but-shallow general-education (the maps
# built across this work, Thesaurus); C = pinpoint, exhaustive research depth (master's/
# PhD), a FUTURE opt-in pack per domain. This file only DEFINES each C frame's scope and
# anchors it to the domain's B-tier spine — it loads NO C content. Building a C pack means
# filling in its frame. nutrition:c is flagged first-to-implement. Base pack (frames only).

def "c" "レベルC — the research-depth (master's/PhD) layer of the ontology. Each c:* frame defines the deep-dive scope for one domain; the content is a future opt-in pack, not loaded here."
ln c knowledge thesaurus:related
ln c crosscut:scale thesaurus:related
def "c:priority:first" "The C frame slated to be implemented first."
ln c:priority:first c sys:part_of

# ══ per-domain C frames (scope defined; content not loaded) ══
def "c:nutrition" "栄養・食のC — concrete recipe/menu deep-dive (per-dish composition, technique parameters, regional variants), food history (culinary_history), and food folklore/ethnology (foodways) refined to research depth. FIRST to implement."
ln c:nutrition c sys:part_of
ln c:nutrition nutrisci c:deepens
ln c:nutrition foodsci c:deepens
ln c:nutrition foodstud c:deepens
ln c:nutrition foodstud:culinary_history c:deepens
ln c:nutrition foodstud:food_folklore c:deepens
def "c:medicine" "医学のC — full nosology (ICD/MeSH), pharmacology at molecular depth, clinical guidelines by specialty, and the primary-literature evidence base."
ln c:medicine c sys:part_of
ln c:medicine med:medicine c:deepens
def "c:biology" "生物学のC — the NCBI-scale taxonomy of species, molecular pathways, and the genomics literature."
ln c:biology c sys:part_of
ln c:biology bio:biology c:deepens
def "c:archaeology" "考古学のC — the Pleiades-scale gazetteer of sites, excavation reports, typologies and absolute-dating series."
ln c:archaeology c sys:part_of
ln c:archaeology archaeo c:deepens
def "c:literature" "文学のC — full public-domain text corpora (Gutenberg-scale), critical editions, and the scholarship on each work."
ln c:literature c sys:part_of
ln c:literature lit:movement c:deepens
ln c:literature epic:epic c:deepens
def "c:history" "歴史学のC — the primary-source record: charters, chronicles, archives, and the historiographical debates."
ln c:history c sys:part_of
ln c:history hist:period c:deepens
ln c:history auxhist c:deepens
def "c:physics" "物理学のC — the mathematical formalism (Lagrangian/field theory), derivations, and the experimental frontier."
ln c:physics c sys:part_of
ln c:physics phys:physics c:deepens
def "c:chemistry" "化学のC — reaction mechanisms, spectroscopic databases, and the synthesis literature."
ln c:chemistry c sys:part_of
ln c:chemistry chem:chemistry c:deepens
def "c:earth_science" "地球科学のC — regional geology, the stratigraphic record, and quantitative climate modelling."
ln c:earth_science c sys:part_of
ln c:earth_science earthsci:earth_science c:deepens
def "c:astronomy" "天文学のC — survey catalogues (stars, galaxies, exoplanets) and the astrophysics literature."
ln c:astronomy c sys:part_of
ln c:astronomy astro:astronomy c:deepens
def "c:mathematics" "数学のC — formal proofs, the research areas, and the theorem-dependency structure."
ln c:mathematics c sys:part_of
ln c:mathematics math c:deepens
def "c:computer_science" "情報科学のC — algorithms with complexity proofs, systems internals, and the ML/AI research frontier."
ln c:computer_science c sys:part_of
ln c:computer_science cs c:deepens
def "c:engineering" "工学のC — design codes and standards, quantitative analysis, and per-branch handbooks."
ln c:engineering c sys:part_of
ln c:engineering eng:engineering c:deepens
def "c:economics" "経済学のC — formal models, econometric methods, and the empirical/theoretical literature."
ln c:economics c sys:part_of
ln c:economics econ c:deepens
def "c:sociology" "社会学のC — social theory in depth, quantitative and qualitative methods, and empirical studies."
ln c:sociology c sys:part_of
ln c:sociology socio c:deepens
def "c:political_science" "政治学のC — formal theory, comparative datasets, and the IR/political-economy literature."
ln c:political_science c sys:part_of
ln c:political_science polisci:political_science c:deepens
def "c:law" "法学のC — statutes, case law, doctrine and comparative-law scholarship."
ln c:law c sys:part_of
ln c:law law:law c:deepens
ln c:law law:branch:constitutional_law c:deepens
def "c:management" "経営学のC — strategy frameworks, quantitative finance, and the management-science literature."
ln c:management c sys:part_of
ln c:management mgmt:management c:deepens
def "c:psychology" "心理学のC — measurement (psychometrics), experimental paradigms, and the empirical literature by subfield."
ln c:psychology c sys:part_of
ln c:psychology psy c:deepens
def "c:linguistics" "言語学のC — formal grammars, typological databases, corpora and computational models."
ln c:linguistics c sys:part_of
ln c:linguistics ling c:deepens
def "c:semiotics" "記号論のC — the primary theorists in depth and applied sign-analysis across media."
ln c:semiotics c sys:part_of
ln c:semiotics semio:semiotics c:deepens
def "c:anthropology" "人類学のC — ethnographic monographs, kinship formalisms, and theory in depth."
ln c:anthropology c sys:part_of
ln c:anthropology anthro:anthropology c:deepens
def "c:folklore" "民俗学のC — the ATU/motif indices in full, regional traditions, and fieldwork archives."
ln c:folklore c sys:part_of
ln c:folklore folk:folklore c:deepens
def "c:paleography" "古文書学のC — script catalogues, manuscript descriptions, diplomatic editions and dating."
ln c:paleography c sys:part_of
ln c:paleography paleo:paleography c:deepens
def "c:philosophy" "哲学のC — the primary texts, the argument structure, and the commentary tradition."
ln c:philosophy c sys:part_of
ln c:philosophy phil:philosophy c:deepens
def "c:religion" "宗教学のC — scriptures, sects and doctrine, sacred sites and the comparative literature."
ln c:religion c sys:part_of
ln c:religion religion:religion c:deepens
def "c:art" "芸術学のC — the catalogue of works and artists, techniques, and art-historical scholarship."
ln c:art c sys:part_of
ln c:art art:movement c:deepens
def "c:music" "音楽学のC — scores and theory, the repertoire, and musicological analysis."
ln c:music c sys:part_of
ln c:music music:period c:deepens
def "c:digital_humanities" "デジタル人文学のC — method implementations, tool pipelines, and reproducible analyses over the corpora."
ln c:digital_humanities c sys:part_of
ln c:digital_humanities dh c:deepens
def "c:world_geography" "世界地理のC — every country and city in depth, classical polities and geographic objects, and the route networks (the world/geo C backlog)."
ln c:world_geography c sys:part_of
ln c:world_geography hist:period c:deepens
ln c:world_geography admin:city c:deepens

# nutrition:c is the first C frame to be implemented
ln c:nutrition c:priority:first thesaurus:related
