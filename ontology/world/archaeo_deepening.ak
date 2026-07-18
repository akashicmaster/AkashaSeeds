# Akasha ontology (world pack) — archaeology deepened: dating & the written record.
# Dating methods (relative & absolute) and the great inscribed/manuscript finds
# that bridge archaeo: to epig: (inscriptions) and ms: (manuscripts). A-tier.

def "archaeo:dating" "A method of establishing archaeological age (年代測定)."
def "archaeo:dating:relative_dating" "Ordering finds earlier/later without exact dates (stratigraphy, seriation, typology)."
ln archaeo:dating:relative_dating archaeo:dating thesaurus:related
def "archaeo:dating:absolute_dating" "Assigning a calendar age (radiocarbon, dendrochronology, K-Ar)."
ln archaeo:dating:absolute_dating archaeo:dating thesaurus:related
def "archaeo:dating:radiocarbon_dating_m" "Dating organic remains by carbon-14 decay, back ~50,000 years."
ln archaeo:dating:radiocarbon_dating_m archaeo:dating thesaurus:related
def "archaeo:dating:dendrochronology_m" "Dating by matching tree-ring patterns, to the exact year."
ln archaeo:dating:dendrochronology_m archaeo:dating thesaurus:related
def "archaeo:dating:potassium_argon" "Dating volcanic rock (and early hominin sites) over millions of years."
ln archaeo:dating:potassium_argon archaeo:dating thesaurus:related
def "archaeo:dating:thermoluminescence" "Dating fired clay and burnt stone by trapped-electron light."
ln archaeo:dating:thermoluminescence archaeo:dating thesaurus:related
def "archaeo:dating:obsidian_hydration" "Dating obsidian tools by their water-absorption rind."
ln archaeo:dating:obsidian_hydration archaeo:dating thesaurus:related
def "archaeo:dating:uranium_series" "Dating cave formations and coral by uranium decay."
ln archaeo:dating:uranium_series archaeo:dating thesaurus:related
def "archaeo:dating:varve_dating" "Counting annual glacial-lake sediment layers."
ln archaeo:dating:varve_dating archaeo:dating thesaurus:related
ln archaeo:dating:relative_dating archaeo:stratigraphy_arch thesaurus:related
ln archaeo:dating:relative_dating archaeo:seriation thesaurus:related
ln archaeo:dating:absolute_dating archaeo:radiocarbon_dating thesaurus:related

# ── landmark inscribed & manuscript finds ──
def "archaeo:find" "A famous inscribed or written archaeological find."
def "archaeo:find:rosetta_stone" "The trilingual stele (Egyptian hieroglyphic/demotic + Greek) that unlocked hieroglyphs."
ln archaeo:find:rosetta_stone archaeo:find thesaurus:related
ln archaeo:find:rosetta_stone geo:country:EGY archaeo:located_in
ln archaeo:find:rosetta_stone epig:inscription thesaurus:related
ln archaeo:find:rosetta_stone epig:hieroglyph thesaurus:related
def "archaeo:find:behistun_inscription" "Darius's trilingual cliff inscription that unlocked cuneiform."
ln archaeo:find:behistun_inscription archaeo:find thesaurus:related
ln archaeo:find:behistun_inscription geo:country:IRN archaeo:located_in
ln archaeo:find:behistun_inscription epig:inscription thesaurus:related
ln archaeo:find:behistun_inscription epig:cuneiform thesaurus:related
def "archaeo:find:oracle_bones" "Shang-dynasty divination bones bearing the earliest Chinese writing."
ln archaeo:find:oracle_bones archaeo:find thesaurus:related
ln archaeo:find:oracle_bones geo:country:CHN archaeo:located_in
ln archaeo:find:oracle_bones epig:inscription thesaurus:related
ln archaeo:find:oracle_bones hist:period:china:shang thesaurus:related
def "archaeo:find:code_of_hammurabi_stele" "The diorite stele carved with Babylon's law code."
ln archaeo:find:code_of_hammurabi_stele archaeo:find thesaurus:related
ln archaeo:find:code_of_hammurabi_stele geo:country:IRQ archaeo:located_in
ln archaeo:find:code_of_hammurabi_stele epig:inscription thesaurus:related
ln archaeo:find:code_of_hammurabi_stele law:code:hammurabi thesaurus:related
def "archaeo:find:dead_sea_scrolls" "The ancient Jewish manuscripts found in Qumran caves."
ln archaeo:find:dead_sea_scrolls archaeo:find thesaurus:related
ln archaeo:find:dead_sea_scrolls geo:country:ISR archaeo:located_in
ln archaeo:find:dead_sea_scrolls ms:scroll thesaurus:related
ln archaeo:find:dead_sea_scrolls papyr:papyrus thesaurus:related
def "archaeo:find:nag_hammadi" "The buried codices of Gnostic gospels."
ln archaeo:find:nag_hammadi archaeo:find thesaurus:related
ln archaeo:find:nag_hammadi geo:country:EGY archaeo:located_in
ln archaeo:find:nag_hammadi ms:codex thesaurus:related
def "archaeo:find:cuneiform_tablets" "Clay tablets — contracts, epics and archives of Mesopotamia."
ln archaeo:find:cuneiform_tablets archaeo:find thesaurus:related
ln archaeo:find:cuneiform_tablets geo:country:IRQ archaeo:located_in
ln archaeo:find:cuneiform_tablets epig:cuneiform thesaurus:related
ln archaeo:find:cuneiform_tablets epic:epic_of_gilgamesh thesaurus:related
def "archaeo:find:rongorongo" "The undeciphered glyph tablets of Rapa Nui."
ln archaeo:find:rongorongo archaeo:find thesaurus:related
ln archaeo:find:rongorongo geo:country:CHL archaeo:located_in
ln archaeo:find:rongorongo archaeo:site:moai_rapa_nui thesaurus:related
