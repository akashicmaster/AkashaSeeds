# Akasha ontology — archaeology: the subdiscipline spine.
# archaeo:* atoms exist (cultures, dating methods, field concepts) but had no branch
# spine. This adds archaeo:branch:* and cross-links the existing atoms + paleography/epigraphy.
# archaeo (top) already exists — only linked. general-education breadth; research depth to level-C.

ln archaeo knowledge:branch:humanities knowledge:in_branch
ln archaeo auxhist thesaurus:related
ln archaeo anthro:field:archaeological thesaurus:related
ln archaeo hist:period:modern_era thesaurus:related

# ══ branches of archaeology ══
def "archaeo:branch:prehistoric" "先史考古学 — the human past before written records, from the Palaeolithic to the first states."
ln archaeo:branch:prehistoric archaeo sys:part_of
ln archaeo:culture:clovis archaeo:branch:prehistoric sys:part_of
ln archaeo:culture:natufian archaeo:branch:prehistoric sys:part_of
ln archaeo:culture:jomon_culture archaeo:branch:prehistoric sys:part_of
ln archaeo:culture:yangshao archaeo:branch:prehistoric sys:part_of
ln archaeo:culture:cucuteni_trypillia archaeo:branch:prehistoric sys:part_of
ln archaeo:culture:harappan archaeo:branch:prehistoric sys:part_of
ln archaeo:branch:prehistoric hist:period:classical_antiquity thesaurus:related
def "archaeo:branch:protohistoric_classical" "原史・古典考古学 — the Bronze and Iron Age civilisations and the Greek and Roman world."
ln archaeo:branch:protohistoric_classical archaeo sys:part_of
ln archaeo:culture:minoan archaeo:branch:protohistoric_classical sys:part_of
ln archaeo:culture:la_tene archaeo:branch:protohistoric_classical sys:part_of
ln archaeo:culture:olmec archaeo:branch:protohistoric_classical sys:part_of
ln archaeo:branch:protohistoric_classical epig:inscription thesaurus:related
def "archaeo:branch:near_eastern" "オリエント考古学 — the ancient Near East: Mesopotamia, the Levant, Anatolia and Persia."
ln archaeo:branch:near_eastern archaeo sys:part_of
ln archaeo:branch:near_eastern epig:cuneiform thesaurus:related
def "archaeo:branch:egyptology" "エジプト学 — the archaeology and philology of ancient Egypt."
ln archaeo:branch:egyptology archaeo sys:part_of
ln archaeo:branch:egyptology epig:hieroglyph thesaurus:related
def "archaeo:branch:historical_archaeology" "歴史考古学 — the material past of literate, historically-documented societies."
ln archaeo:branch:historical_archaeology archaeo sys:part_of
ln archaeo:branch:historical_archaeology paleo:diplomatics thesaurus:related
ln archaeo:branch:historical_archaeology hist:period:modern_era thesaurus:related
def "archaeo:branch:industrial_archaeology" "産業考古学 — the physical remains of the industrial age."
ln archaeo:branch:industrial_archaeology archaeo sys:part_of
ln archaeo:branch:industrial_archaeology hist:period:industrial_revolution thesaurus:related
ln archaeo:branch:industrial_archaeology matsci thesaurus:related
def "archaeo:branch:underwater_archaeology" "水中考古学 — shipwrecks and submerged sites."
ln archaeo:branch:underwater_archaeology archaeo sys:part_of
ln archaeo:branch:underwater_archaeology earthsci:branch:oceanography thesaurus:related
def "archaeo:branch:bioarchaeology" "生物考古学 — human remains: diet, disease, ancestry and lifeways from bones."
ln archaeo:branch:bioarchaeology archaeo sys:part_of
ln archaeo:branch:bioarchaeology bio:branch:evolution thesaurus:related
ln archaeo:branch:bioarchaeology med:basic:pathology thesaurus:related
def "archaeo:branch:environmental_archaeology" "環境考古学 — reconstructing past climates, landscapes, plants and animals."
ln archaeo:branch:environmental_archaeology archaeo sys:part_of
ln archaeo:branch:environmental_archaeology ecol thesaurus:related
ln archaeo:branch:environmental_archaeology earthsci:branch:paleontology thesaurus:related
def "archaeo:branch:archaeological_science" "考古科学 — the laboratory methods: dating, materials analysis and remote sensing."
ln archaeo:branch:archaeological_science archaeo sys:part_of
ln archaeo:dating:absolute_dating archaeo:branch:archaeological_science sys:part_of
ln archaeo:dating:relative_dating archaeo:branch:archaeological_science sys:part_of
ln archaeo:dating:radiocarbon_dating_m archaeo:branch:archaeological_science sys:part_of
ln archaeo:dating:dendrochronology_m archaeo:branch:archaeological_science sys:part_of
ln archaeo:dating:potassium_argon archaeo:branch:archaeological_science sys:part_of
ln archaeo:dating:obsidian_hydration archaeo:branch:archaeological_science sys:part_of
ln archaeo:dating:thermoluminescence archaeo:branch:archaeological_science sys:part_of
ln archaeo:dating:uranium_series archaeo:branch:archaeological_science sys:part_of
ln archaeo:dating:varve_dating archaeo:branch:archaeological_science sys:part_of
ln archaeo:branch:archaeological_science chem:branch:analytical_chemistry thesaurus:related
ln archaeo:branch:archaeological_science dh:family:spatial thesaurus:related

# ══ field method (existing archaeo: concepts) ══
def "archaeo:method" "発掘・記録の方法 — how archaeology recovers and records material evidence."
ln archaeo:method archaeo sys:part_of
ln archaeo:archaeological_site archaeo:method sys:part_of
ln archaeo:artifact archaeo:method sys:part_of
ln archaeo:context archaeo:method sys:part_of
ln archaeo:cultural_layer archaeo:method sys:part_of
ln archaeo:culture archaeo:method sys:part_of
ln archaeo:dating archaeo:method sys:part_of
ln archaeo:method paleo:paleography thesaurus:related
ln archaeo:method dh:family:digitization_3d thesaurus:related
ln archaeo:culture anthro:concept:material_culture thesaurus:related
