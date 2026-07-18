# Akasha ontology (world pack) — historical polities & their modern heirs.
# Ties ancient civilizations/empires to the modern country on their land
# (hist:territory_now → geo:country:*), their cultural heir (cuisine:/myth:),
# and their ethnic/linguistic descent — the geographic, cultural AND ethnic
# threads the request asks for. A-tier.

def "hist:polity" "A historical state, empire or civilization (歴史上の国家/文明)."
def "hist:era:ancient" "The the earliest literate states."
def "hist:era:classical" "The the Greco-Roman/Persian classical age."
def "hist:era:postclassical" "The the medieval/pre-Columbian era."
def "hist:era:early_modern" "The the gunpowder empires."

# ── polities → territory (geo), cultural heir, ethnic descent ──
def "hist:ancient_egypt" "The Nile civilization of pharaohs and pyramids."
ln hist:ancient_egypt hist:polity thesaurus:related
ln hist:ancient_egypt hist:era:ancient hist:era_of
ln hist:ancient_egypt geo:country:EGY hist:territory_now
ln hist:ancient_egypt cuisine:ancient_egyptian hist:cultural_heir
# ethnic: Copts and modern Egyptians on the same Nile.
def "hist:sumer" "The first cities of southern Mesopotamia."
ln hist:sumer hist:polity thesaurus:related
ln hist:sumer hist:era:ancient hist:era_of
ln hist:sumer geo:country:IRQ hist:territory_now
# ethnic: absorbed into later Mesopotamian peoples.
def "hist:babylonia" "The empire of Hammurabi and Nebuchadnezzar."
ln hist:babylonia hist:polity thesaurus:related
ln hist:babylonia hist:era:ancient hist:era_of
ln hist:babylonia geo:country:IRQ hist:territory_now
ln hist:babylonia myth:babylonian_enuma_elish hist:cultural_heir
# ethnic: modern Iraqis on the Tigris-Euphrates.
def "hist:assyria" "The militarized Mesopotamian empire."
ln hist:assyria hist:polity thesaurus:related
ln hist:assyria hist:era:ancient hist:era_of
ln hist:assyria geo:country:IRQ hist:territory_now
# ethnic: Assyrian Christians preserve the name and tongue.
def "hist:achaemenid_persia" "Cyrus and Darius's vast Persian empire."
ln hist:achaemenid_persia hist:polity thesaurus:related
ln hist:achaemenid_persia hist:era:classical hist:era_of
ln hist:achaemenid_persia geo:country:IRN hist:territory_now
ln hist:achaemenid_persia cuisine:persian hist:cultural_heir
# ethnic: modern Iranians, heirs to Persian language and culture.
def "hist:ancient_greece" "The city-states of Athens, Sparta and the Hellenic world."
ln hist:ancient_greece hist:polity thesaurus:related
ln hist:ancient_greece hist:era:classical hist:era_of
ln hist:ancient_greece geo:country:GRC hist:territory_now
# ethnic: modern Greeks, continuous language and Orthodoxy.
def "hist:roman_empire" "The Mediterranean empire centred on Rome."
ln hist:roman_empire hist:polity thesaurus:related
ln hist:roman_empire hist:era:classical hist:era_of
ln hist:roman_empire geo:country:ITA hist:territory_now
# ethnic: Italians at the core; Latin seeded the Romance peoples.
def "hist:byzantine_empire" "The Greek-speaking Christian eastern Roman empire."
ln hist:byzantine_empire hist:polity thesaurus:related
ln hist:byzantine_empire hist:era:postclassical hist:era_of
ln hist:byzantine_empire geo:country:TUR hist:territory_now
# ethnic: Greeks and Orthodox Christendom; Constantinople is Istanbul.
def "hist:carthage" "The Phoenician maritime power of North Africa."
ln hist:carthage hist:polity thesaurus:related
ln hist:carthage hist:era:classical hist:era_of
ln hist:carthage geo:country:TUN hist:territory_now
# ethnic: absorbed by Rome; on modern Tunisian soil.
def "hist:phoenicia" "The seafaring, alphabet-spreading Levantine cities."
ln hist:phoenicia hist:polity thesaurus:related
ln hist:phoenicia hist:era:ancient hist:era_of
ln hist:phoenicia geo:country:LBN hist:territory_now
# ethnic: Lebanese trace descent to the Phoenicians.
def "hist:hittite_empire" "The Bronze-Age Anatolian power."
ln hist:hittite_empire hist:polity thesaurus:related
ln hist:hittite_empire hist:era:ancient hist:era_of
ln hist:hittite_empire geo:country:TUR hist:territory_now
# ethnic: vanished; on modern Turkish land.
def "hist:maya_civilization" "The Mesoamerican civilization of glyphs and pyramids."
ln hist:maya_civilization hist:polity thesaurus:related
ln hist:maya_civilization hist:era:postclassical hist:era_of
ln hist:maya_civilization geo:country:MEX hist:territory_now
ln hist:maya_civilization geo:country:GTM hist:territory_now
ln hist:maya_civilization myth:maya_hero_twins hist:cultural_heir
# ethnic: millions of Maya still speak Mayan languages.
def "hist:aztec_empire" "The Nahua empire of Tenochtitlan."
ln hist:aztec_empire hist:polity thesaurus:related
ln hist:aztec_empire hist:era:postclassical hist:era_of
ln hist:aztec_empire geo:country:MEX hist:territory_now
ln hist:aztec_empire cuisine:aztec hist:cultural_heir
ln hist:aztec_empire myth:aztec_five_suns hist:cultural_heir
# ethnic: Nahua peoples of central Mexico.
def "hist:inca_empire" "The Andean empire of Tawantinsuyu."
ln hist:inca_empire hist:polity thesaurus:related
ln hist:inca_empire hist:era:postclassical hist:era_of
ln hist:inca_empire geo:country:PER hist:territory_now
ln hist:inca_empire cuisine:inca hist:cultural_heir
# ethnic: Quechua and Aymara peoples of the Andes.
def "hist:ottoman_empire" "The Turkish empire straddling three continents."
ln hist:ottoman_empire hist:polity thesaurus:related
ln hist:ottoman_empire hist:era:early_modern hist:era_of
ln hist:ottoman_empire geo:country:TUR hist:territory_now
ln hist:ottoman_empire cuisine:ottoman hist:cultural_heir
# ethnic: modern Turks; its cuisine spans the Balkans-Levant.
def "hist:mongol_empire" "The largest contiguous land empire, of Genghis Khan."
ln hist:mongol_empire hist:polity thesaurus:related
ln hist:mongol_empire hist:era:postclassical hist:era_of
ln hist:mongol_empire geo:country:MNG hist:territory_now
# ethnic: Mongols; its reach shaped Eurasia.
def "hist:han_china" "The classical Chinese empire that named the Han people."
ln hist:han_china hist:polity thesaurus:related
ln hist:han_china hist:era:ancient hist:era_of
ln hist:han_china geo:country:CHN hist:territory_now
ln hist:han_china cuisine:chinese hist:cultural_heir
# ethnic: the Han Chinese majority.
def "hist:indus_valley" "The Bronze-Age Harappan civilization."
ln hist:indus_valley hist:polity thesaurus:related
ln hist:indus_valley hist:era:ancient hist:era_of
ln hist:indus_valley geo:country:PAK hist:territory_now
ln hist:indus_valley geo:country:IND hist:territory_now
# ethnic: absorbed into South Asian peoples.
def "hist:gaul" "The Celtic land Rome conquered."
ln hist:gaul hist:polity thesaurus:related
ln hist:gaul hist:era:classical hist:era_of
ln hist:gaul geo:country:FRA hist:territory_now
# ethnic: the French, on Gaulish soil.
def "hist:aksum" "The trading empire of the Ethiopian highlands."
ln hist:aksum hist:polity thesaurus:related
ln hist:aksum hist:era:classical hist:era_of
ln hist:aksum geo:country:ETH hist:territory_now
ln hist:aksum cuisine:ethiopian hist:cultural_heir
# ethnic: Ethiopians, heirs to Aksum and Ge'ez.

# ── city continuity ──
def "hist:city" "A city seen across time — its historical and modern identities."
def "hist:city:constantinople" "Byzantium → Constantinople → Istanbul: the city of two empires."
ln hist:city:constantinople hist:city thesaurus:related
ln hist:city:constantinople geo:country:TUR hist:city_in
ln hist:city:constantinople hist:byzantine_empire hist:capital_of
def "hist:city:tenochtitlan" "The Aztec island capital, now buried under Mexico City."
ln hist:city:tenochtitlan hist:city thesaurus:related
ln hist:city:tenochtitlan geo:country:MEX hist:city_in
ln hist:city:tenochtitlan hist:aztec_empire hist:capital_of
def "hist:city:memphis_egypt" "Egypt's ancient capital near modern Cairo."
ln hist:city:memphis_egypt hist:city thesaurus:related
ln hist:city:memphis_egypt geo:country:EGY hist:city_in
ln hist:city:memphis_egypt hist:ancient_egypt hist:capital_of
def "hist:city:babylon_city" "The great city near modern Hillah, south of Baghdad."
ln hist:city:babylon_city hist:city thesaurus:related
ln hist:city:babylon_city geo:country:IRQ hist:city_in
ln hist:city:babylon_city hist:babylonia hist:capital_of
def "hist:city:persepolis" "The Achaemenid ceremonial capital near Shiraz."
ln hist:city:persepolis hist:city thesaurus:related
ln hist:city:persepolis geo:country:IRN hist:city_in
ln hist:city:persepolis hist:achaemenid_persia hist:capital_of
def "hist:city:carthage_city" "The Punic capital, now a suburb of Tunis."
ln hist:city:carthage_city hist:city thesaurus:related
ln hist:city:carthage_city geo:country:TUN hist:city_in
ln hist:city:carthage_city hist:carthage hist:capital_of
def "hist:city:cusco" "The Inca capital — still a living Andean city."
ln hist:city:cusco hist:city thesaurus:related
ln hist:city:cusco geo:country:PER hist:city_in
ln hist:city:cusco hist:inca_empire hist:capital_of
def "hist:city:changan" "Tang-dynasty capital, now Xi'an."
ln hist:city:changan hist:city thesaurus:related
ln hist:city:changan geo:country:CHN hist:city_in
ln hist:city:changan hist:han_china hist:capital_of
def "hist:city:rome_city" "The Eternal City — continuous from empire to capital."
ln hist:city:rome_city hist:city thesaurus:related
ln hist:city:rome_city geo:country:ITA hist:city_in
ln hist:city:rome_city hist:roman_empire hist:capital_of
def "hist:city:athens_city" "Continuous from the classical polis to Greece's capital."
ln hist:city:athens_city hist:city thesaurus:related
ln hist:city:athens_city geo:country:GRC hist:city_in
ln hist:city:athens_city hist:ancient_greece hist:capital_of
