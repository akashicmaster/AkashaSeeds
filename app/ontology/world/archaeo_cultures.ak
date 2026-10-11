# Akasha ontology (world pack) — archaeological cultures & sites.
# archaeo: had only methods; add concrete cultures and famous sites, tied to
# their period (hist:period:), country (geo:), and the dating/method layer. A-tier.

def "archaeo:culture" "A prehistoric/ancient archaeological culture (考古文化)."
def "archaeo:culture:natufian" "The Levantine foragers (~12,500 BCE) who settled and stored wild grain on the eve of farming."
ln archaeo:culture:natufian archaeo:culture thesaurus:related
ln archaeo:culture:natufian hist:period:mesolithic archaeo:dated_to
def "archaeo:culture:jomon_culture" "Japan's hunter-gatherers (~14,000–300 BCE), makers of the world's oldest pottery."
ln archaeo:culture:jomon_culture archaeo:culture thesaurus:related
ln archaeo:culture:jomon_culture geo:country:JPN archaeo:located_in
ln archaeo:culture:jomon_culture hist:period:neolithic archaeo:dated_to
def "archaeo:culture:clovis" "The early Paleo-Indians (~11,000 BCE) known by their fluted spear-points."
ln archaeo:culture:clovis archaeo:culture thesaurus:related
ln archaeo:culture:clovis geo:country:USA archaeo:located_in
ln archaeo:culture:clovis hist:period:paleolithic archaeo:dated_to
def "archaeo:culture:cucuteni_trypillia" "The Neolithic culture of vast painted-pottery mega-settlements in SE Europe."
ln archaeo:culture:cucuteni_trypillia archaeo:culture thesaurus:related
ln archaeo:culture:cucuteni_trypillia geo:country:ROU archaeo:located_in
ln archaeo:culture:cucuteni_trypillia hist:period:neolithic archaeo:dated_to
def "archaeo:culture:harappan" "The Indus Valley civilization of planned brick cities and undeciphered seals."
ln archaeo:culture:harappan archaeo:culture thesaurus:related
ln archaeo:culture:harappan geo:country:PAK archaeo:located_in
ln archaeo:culture:harappan hist:period:bronze_age archaeo:dated_to
def "archaeo:culture:yangshao" "Neolithic China's millet farmers and painted pottery along the Yellow River."
ln archaeo:culture:yangshao archaeo:culture thesaurus:related
ln archaeo:culture:yangshao geo:country:CHN archaeo:located_in
ln archaeo:culture:yangshao hist:period:neolithic archaeo:dated_to
def "archaeo:culture:olmec" "Mesoamerica's 'mother culture' of colossal stone heads (~1200 BCE)."
ln archaeo:culture:olmec archaeo:culture thesaurus:related
ln archaeo:culture:olmec geo:country:MEX archaeo:located_in
ln archaeo:culture:olmec hist:period:bronze_age archaeo:dated_to
def "archaeo:culture:minoan" "Bronze-Age Crete's palace civilization of frescoes and the labyrinth myth."
ln archaeo:culture:minoan archaeo:culture thesaurus:related
ln archaeo:culture:minoan geo:country:GRC archaeo:located_in
ln archaeo:culture:minoan hist:period:bronze_age archaeo:dated_to
def "archaeo:culture:la_tene" "The later Celtic Iron-Age culture of intricate curvilinear art."
ln archaeo:culture:la_tene archaeo:culture thesaurus:related
ln archaeo:culture:la_tene geo:country:AUT archaeo:located_in
ln archaeo:culture:la_tene hist:period:iron_age archaeo:dated_to

def "archaeo:site" "A notable archaeological site (遺跡)."
def "archaeo:site:gobekli_tepe" "The world's oldest monumental temple (~9500 BCE) — built by foragers before farming."
ln archaeo:site:gobekli_tepe archaeo:site thesaurus:related
ln archaeo:site:gobekli_tepe geo:country:TUR archaeo:located_in
ln archaeo:site:gobekli_tepe hist:period:neolithic archaeo:dated_to
def "archaeo:site:catalhoyuk" "A vast Neolithic proto-city of clustered mud-brick houses entered through the roof."
ln archaeo:site:catalhoyuk archaeo:site thesaurus:related
ln archaeo:site:catalhoyuk geo:country:TUR archaeo:located_in
ln archaeo:site:catalhoyuk hist:period:neolithic archaeo:dated_to
def "archaeo:site:jericho" "One of the oldest continuously-inhabited towns, walled by ~8000 BCE."
ln archaeo:site:jericho archaeo:site thesaurus:related
ln archaeo:site:jericho geo:country:PSE archaeo:located_in
ln archaeo:site:jericho hist:period:neolithic archaeo:dated_to
def "archaeo:site:mohenjo_daro" "The great Harappan city with its grid streets and Great Bath."
ln archaeo:site:mohenjo_daro archaeo:site thesaurus:related
ln archaeo:site:mohenjo_daro geo:country:PAK archaeo:located_in
ln archaeo:site:mohenjo_daro hist:period:bronze_age archaeo:dated_to
def "archaeo:site:knossos" "The Minoan palace of Crete, labyrinthine heart of the bull-leaping culture."
ln archaeo:site:knossos archaeo:site thesaurus:related
ln archaeo:site:knossos geo:country:GRC archaeo:located_in
ln archaeo:site:knossos hist:period:bronze_age archaeo:dated_to
def "archaeo:site:lascaux" "The Paleolithic painted cave of galloping bulls and horses (~17,000 BCE)."
ln archaeo:site:lascaux archaeo:site thesaurus:related
ln archaeo:site:lascaux geo:country:FRA archaeo:located_in
ln archaeo:site:lascaux hist:period:paleolithic archaeo:dated_to
def "archaeo:site:altamira" "The cave of polychrome bison, the 'Sistine Chapel' of prehistoric art."
ln archaeo:site:altamira archaeo:site thesaurus:related
ln archaeo:site:altamira geo:country:ESP archaeo:located_in
ln archaeo:site:altamira hist:period:paleolithic archaeo:dated_to
def "archaeo:site:terracotta_army" "The 8,000-figure clay army guarding Qin Shi Huang's tomb."
ln archaeo:site:terracotta_army archaeo:site thesaurus:related
ln archaeo:site:terracotta_army geo:country:CHN archaeo:located_in
ln archaeo:site:terracotta_army hist:period:classical_antiquity archaeo:dated_to
def "archaeo:site:nazca_lines" "The vast desert geoglyphs of the Nazca, visible only from the air."
ln archaeo:site:nazca_lines archaeo:site thesaurus:related
ln archaeo:site:nazca_lines geo:country:PER archaeo:located_in
ln archaeo:site:nazca_lines hist:period:classical_antiquity archaeo:dated_to
def "archaeo:site:newgrange" "The Neolithic passage tomb lit by the winter-solstice sunrise."
ln archaeo:site:newgrange archaeo:site thesaurus:related
ln archaeo:site:newgrange geo:country:IRL archaeo:located_in
ln archaeo:site:newgrange hist:period:neolithic archaeo:dated_to
def "archaeo:site:moai_rapa_nui" "The monumental stone heads of Easter Island."
ln archaeo:site:moai_rapa_nui archaeo:site thesaurus:related
ln archaeo:site:moai_rapa_nui geo:country:CHL archaeo:located_in
ln archaeo:site:moai_rapa_nui hist:period:late_middle_ages archaeo:dated_to
ln archaeo:site:lascaux archaeo:radiocarbon_dating thesaurus:related
ln archaeo:site:gobekli_tepe archaeo:excavation thesaurus:related
