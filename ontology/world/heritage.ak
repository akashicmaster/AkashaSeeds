# Akasha ontology (world pack) — UNESCO World Heritage & the fact of place.
# Sites tied to their country (geo:country:*) and category; intangible heritage
# bridges the food/culture layer. A-tier.

def "heritage:world_heritage" "A UNESCO World Heritage site — of outstanding universal value (世界遺産)."
def "heritage:category:cultural" "Heritage of cultural significance (monuments, cities, works)."
def "heritage:category:natural" "Heritage of natural significance (landscapes, ecosystems)."
def "heritage:category:mixed" "Heritage of both cultural and natural value."
def "heritage:category:intangible" "Heritage living traditions (rituals, crafts, cuisine)."
ln heritage:category:intangible foodstud:intangible_cultural_heritage thesaurus:related

# ── sites → country & category ──
def "heritage:great_wall" "The 20,000-km defensive wall of imperial China."
ln heritage:great_wall heritage:world_heritage thesaurus:related
ln heritage:great_wall heritage:category:cultural heritage:is
ln heritage:great_wall geo:country:CHN heritage:in_country
def "heritage:forbidden_city" "Beijing's Ming-Qing imperial palace."
ln heritage:forbidden_city heritage:world_heritage thesaurus:related
ln heritage:forbidden_city heritage:category:cultural heritage:is
ln heritage:forbidden_city geo:country:CHN heritage:in_country
def "heritage:taj_mahal" "Agra's white-marble mausoleum of love."
ln heritage:taj_mahal heritage:world_heritage thesaurus:related
ln heritage:taj_mahal heritage:category:cultural heritage:is
ln heritage:taj_mahal geo:country:IND heritage:in_country
def "heritage:machu_picchu" "The Inca citadel high in the Andes."
ln heritage:machu_picchu heritage:world_heritage thesaurus:related
ln heritage:machu_picchu heritage:category:mixed heritage:is
ln heritage:machu_picchu geo:country:PER heritage:in_country
def "heritage:angkor_wat" "The vast Khmer temple complex of Cambodia."
ln heritage:angkor_wat heritage:world_heritage thesaurus:related
ln heritage:angkor_wat heritage:category:cultural heritage:is
ln heritage:angkor_wat geo:country:KHM heritage:in_country
def "heritage:colosseum" "Rome's great amphitheatre."
ln heritage:colosseum heritage:world_heritage thesaurus:related
ln heritage:colosseum heritage:category:cultural heritage:is
ln heritage:colosseum geo:country:ITA heritage:in_country
def "heritage:pompeii" "The Roman city frozen by Vesuvius."
ln heritage:pompeii heritage:world_heritage thesaurus:related
ln heritage:pompeii heritage:category:cultural heritage:is
ln heritage:pompeii geo:country:ITA heritage:in_country
def "heritage:acropolis" "Athens' Parthenon-crowned citadel."
ln heritage:acropolis heritage:world_heritage thesaurus:related
ln heritage:acropolis heritage:category:cultural heritage:is
ln heritage:acropolis geo:country:GRC heritage:in_country
def "heritage:pyramids_of_giza" "The last standing ancient wonder."
ln heritage:pyramids_of_giza heritage:world_heritage thesaurus:related
ln heritage:pyramids_of_giza heritage:category:cultural heritage:is
ln heritage:pyramids_of_giza geo:country:EGY heritage:in_country
def "heritage:petra" "The rose-red rock-cut city of the Nabataeans."
ln heritage:petra heritage:world_heritage thesaurus:related
ln heritage:petra heritage:category:cultural heritage:is
ln heritage:petra geo:country:JOR heritage:in_country
def "heritage:chichen_itza" "The Maya-Toltec city and El Castillo pyramid."
ln heritage:chichen_itza heritage:world_heritage thesaurus:related
ln heritage:chichen_itza heritage:category:cultural heritage:is
ln heritage:chichen_itza geo:country:MEX heritage:in_country
def "heritage:historic_kyoto" "Kyoto's temples, shrines and gardens."
ln heritage:historic_kyoto heritage:world_heritage thesaurus:related
ln heritage:historic_kyoto heritage:category:cultural heritage:is
ln heritage:historic_kyoto geo:country:JPN heritage:in_country
def "heritage:himeji_castle" "Japan's finest surviving feudal castle."
ln heritage:himeji_castle heritage:world_heritage thesaurus:related
ln heritage:himeji_castle heritage:category:cultural heritage:is
ln heritage:himeji_castle geo:country:JPN heritage:in_country
def "heritage:alhambra" "Granada's Moorish palace-fortress."
ln heritage:alhambra heritage:world_heritage thesaurus:related
ln heritage:alhambra heritage:category:cultural heritage:is
ln heritage:alhambra geo:country:ESP heritage:in_country
def "heritage:stonehenge" "The prehistoric standing-stone circle."
ln heritage:stonehenge heritage:world_heritage thesaurus:related
ln heritage:stonehenge heritage:category:cultural heritage:is
ln heritage:stonehenge geo:country:GBR heritage:in_country
def "heritage:mont_saint_michel" "The tidal-island abbey of Normandy."
ln heritage:mont_saint_michel heritage:world_heritage thesaurus:related
ln heritage:mont_saint_michel heritage:category:cultural heritage:is
ln heritage:mont_saint_michel geo:country:FRA heritage:in_country
def "heritage:palace_of_versailles" "The Sun King's monumental palace."
ln heritage:palace_of_versailles heritage:world_heritage thesaurus:related
ln heritage:palace_of_versailles heritage:category:cultural heritage:is
ln heritage:palace_of_versailles geo:country:FRA heritage:in_country
def "heritage:borobudur" "The world's largest Buddhist temple."
ln heritage:borobudur heritage:world_heritage thesaurus:related
ln heritage:borobudur heritage:category:cultural heritage:is
ln heritage:borobudur geo:country:IDN heritage:in_country
def "heritage:hagia_sophia" "Istanbul's Byzantine-Ottoman masterpiece."
ln heritage:hagia_sophia heritage:world_heritage thesaurus:related
ln heritage:hagia_sophia heritage:category:cultural heritage:is
ln heritage:hagia_sophia geo:country:TUR heritage:in_country
def "heritage:cappadocia" "Fairy-chimney landscapes and cave churches."
ln heritage:cappadocia heritage:world_heritage thesaurus:related
ln heritage:cappadocia heritage:category:mixed heritage:is
ln heritage:cappadocia geo:country:TUR heritage:in_country
def "heritage:grand_canyon" "The mile-deep gorge of the Colorado River."
ln heritage:grand_canyon heritage:world_heritage thesaurus:related
ln heritage:grand_canyon heritage:category:natural heritage:is
ln heritage:grand_canyon geo:country:USA heritage:in_country
def "heritage:yellowstone" "The first national park — geysers and wildlife."
ln heritage:yellowstone heritage:world_heritage thesaurus:related
ln heritage:yellowstone heritage:category:natural heritage:is
ln heritage:yellowstone geo:country:USA heritage:in_country
def "heritage:great_barrier_reef" "The world's largest coral reef system."
ln heritage:great_barrier_reef heritage:world_heritage thesaurus:related
ln heritage:great_barrier_reef heritage:category:natural heritage:is
ln heritage:great_barrier_reef geo:country:AUS heritage:in_country
def "heritage:uluru" "The sacred sandstone monolith of the outback."
ln heritage:uluru heritage:world_heritage thesaurus:related
ln heritage:uluru heritage:category:mixed heritage:is
ln heritage:uluru geo:country:AUS heritage:in_country
def "heritage:galapagos" "Darwin's islands of endemic life."
ln heritage:galapagos heritage:world_heritage thesaurus:related
ln heritage:galapagos heritage:category:natural heritage:is
ln heritage:galapagos geo:country:ECU heritage:in_country
def "heritage:serengeti" "The great-migration savanna of East Africa."
ln heritage:serengeti heritage:world_heritage thesaurus:related
ln heritage:serengeti heritage:category:natural heritage:is
ln heritage:serengeti geo:country:TZA heritage:in_country
def "heritage:iguazu_falls" "The thundering falls on the Argentina-Brazil border."
ln heritage:iguazu_falls heritage:world_heritage thesaurus:related
ln heritage:iguazu_falls heritage:category:natural heritage:is
ln heritage:iguazu_falls geo:country:ARG heritage:in_country
def "heritage:ha_long_bay" "Emerald waters and limestone karsts."
ln heritage:ha_long_bay heritage:world_heritage thesaurus:related
ln heritage:ha_long_bay heritage:category:natural heritage:is
ln heritage:ha_long_bay geo:country:VNM heritage:in_country
def "heritage:plitvice_lakes" "Terraced turquoise lakes and waterfalls."
ln heritage:plitvice_lakes heritage:world_heritage thesaurus:related
ln heritage:plitvice_lakes heritage:category:natural heritage:is
ln heritage:plitvice_lakes geo:country:HRV heritage:in_country
def "heritage:mount_fuji" "Japan's sacred, iconic volcano."
ln heritage:mount_fuji heritage:world_heritage thesaurus:related
ln heritage:mount_fuji heritage:category:cultural heritage:is
ln heritage:mount_fuji geo:country:JPN heritage:in_country
