# Akasha ontology (world pack) — physical geography, tied to geo:.
# Mountains, ranges, seas, oceans, rivers, lakes, deserts and plains — each
# linked to the country/countries and continent it belongs to (geo:in_country /
# geo:spans). Fills a gap: geo: had only political units. A-tier.

def "geo:mountain" "A notable mountain peak (山)."
def "geo:mountain:everest" "Earth's highest peak, 8,849 m, in the Himalayas."
ln geo:mountain:everest geo:mountain thesaurus:related
ln geo:mountain:everest geo:country:NPL geo:in_country
ln geo:mountain:everest geo:country:CHN geo:in_country
def "geo:mountain:k2" "The second-highest and deadliest great peak."
ln geo:mountain:k2 geo:mountain thesaurus:related
ln geo:mountain:k2 geo:country:PAK geo:in_country
ln geo:mountain:k2 geo:country:CHN geo:in_country
def "geo:mountain:kilimanjaro" "Africa's highest, a snow-capped equatorial volcano."
ln geo:mountain:kilimanjaro geo:mountain thesaurus:related
ln geo:mountain:kilimanjaro geo:country:TZA geo:in_country
def "geo:mountain:mont_blanc" "The highest Alpine peak."
ln geo:mountain:mont_blanc geo:mountain thesaurus:related
ln geo:mountain:mont_blanc geo:country:FRA geo:in_country
ln geo:mountain:mont_blanc geo:country:ITA geo:in_country
def "geo:mountain:matterhorn" "The iconic pyramidal Alpine peak."
ln geo:mountain:matterhorn geo:mountain thesaurus:related
ln geo:mountain:matterhorn geo:country:CHE geo:in_country
ln geo:mountain:matterhorn geo:country:ITA geo:in_country
def "geo:mountain:denali" "North America's highest, in Alaska."
ln geo:mountain:denali geo:mountain thesaurus:related
ln geo:mountain:denali geo:country:USA geo:in_country
def "geo:mountain:aconcagua" "The highest peak outside Asia, in the Andes."
ln geo:mountain:aconcagua geo:mountain thesaurus:related
ln geo:mountain:aconcagua geo:country:ARG geo:in_country
def "geo:mountain:fuji" "Japan's sacred symmetrical volcano."
ln geo:mountain:fuji geo:mountain thesaurus:related
ln geo:mountain:fuji geo:country:JPN geo:in_country
def "geo:mountain:mount_elbrus" "Europe's highest, in the Caucasus."
ln geo:mountain:mount_elbrus geo:mountain thesaurus:related
ln geo:mountain:mount_elbrus geo:country:RUS geo:in_country

def "geo:range" "A mountain range (山脈)."
def "geo:range:himalayas" "The roof of the world, holding Earth's highest peaks."
ln geo:range:himalayas geo:range thesaurus:related
ln geo:range:himalayas geo:country:NPL geo:in_country
ln geo:range:himalayas geo:country:IND geo:in_country
ln geo:range:himalayas geo:country:CHN geo:in_country
ln geo:range:himalayas geo:country:BTN geo:in_country
ln geo:range:himalayas geo:country:PAK geo:in_country
def "geo:range:alps" "The great range of central Europe."
ln geo:range:alps geo:range thesaurus:related
ln geo:range:alps geo:country:FRA geo:in_country
ln geo:range:alps geo:country:CHE geo:in_country
ln geo:range:alps geo:country:ITA geo:in_country
ln geo:range:alps geo:country:AUT geo:in_country
ln geo:range:alps geo:country:DEU geo:in_country
def "geo:range:andes" "The world's longest continental range, spine of South America."
ln geo:range:andes geo:range thesaurus:related
ln geo:range:andes geo:country:CHL geo:in_country
ln geo:range:andes geo:country:ARG geo:in_country
ln geo:range:andes geo:country:PER geo:in_country
ln geo:range:andes geo:country:BOL geo:in_country
ln geo:range:andes geo:country:ECU geo:in_country
ln geo:range:andes geo:country:COL geo:in_country
def "geo:range:rocky_mountains" "The rugged spine of western North America."
ln geo:range:rocky_mountains geo:range thesaurus:related
ln geo:range:rocky_mountains geo:country:USA geo:in_country
ln geo:range:rocky_mountains geo:country:CAN geo:in_country
def "geo:range:ural_mountains" "The traditional Europe-Asia divide."
ln geo:range:ural_mountains geo:range thesaurus:related
ln geo:range:ural_mountains geo:country:RUS geo:in_country
def "geo:range:caucasus" "The range between the Black and Caspian seas."
ln geo:range:caucasus geo:range thesaurus:related
ln geo:range:caucasus geo:country:RUS geo:in_country
ln geo:range:caucasus geo:country:GEO geo:in_country
ln geo:range:caucasus geo:country:AZE geo:in_country
def "geo:range:atlas_mountains" "The range of northwest Africa."
ln geo:range:atlas_mountains geo:range thesaurus:related
ln geo:range:atlas_mountains geo:country:MAR geo:in_country
ln geo:range:atlas_mountains geo:country:DZA geo:in_country

def "geo:sea" "A sea — a large body of salt water (海)."
def "geo:sea:mediterranean" "The cradle-of-civilizations sea between three continents."
ln geo:sea:mediterranean geo:sea thesaurus:related
ln geo:sea:mediterranean geo:country:ITA geo:in_country
ln geo:sea:mediterranean geo:country:GRC geo:in_country
ln geo:sea:mediterranean geo:country:ESP geo:in_country
ln geo:sea:mediterranean geo:country:EGY geo:in_country
ln geo:sea:mediterranean geo:country:TUR geo:in_country
def "geo:sea:black_sea" "The inland sea north of Anatolia."
ln geo:sea:black_sea geo:sea thesaurus:related
ln geo:sea:black_sea geo:country:TUR geo:in_country
ln geo:sea:black_sea geo:country:RUS geo:in_country
ln geo:sea:black_sea geo:country:UKR geo:in_country
def "geo:sea:red_sea" "The narrow sea between Africa and Arabia."
ln geo:sea:red_sea geo:sea thesaurus:related
ln geo:sea:red_sea geo:country:EGY geo:in_country
ln geo:sea:red_sea geo:country:SAU geo:in_country
def "geo:sea:caribbean_sea" "The tropical sea of the West Indies."
ln geo:sea:caribbean_sea geo:sea thesaurus:related
ln geo:sea:caribbean_sea geo:country:CUB geo:in_country
ln geo:sea:caribbean_sea geo:country:JAM geo:in_country
def "geo:sea:arabian_sea" "The northwest Indian Ocean sea."
ln geo:sea:arabian_sea geo:sea thesaurus:related
ln geo:sea:arabian_sea geo:country:IND geo:in_country
ln geo:sea:arabian_sea geo:country:OMN geo:in_country
ln geo:sea:arabian_sea geo:country:PAK geo:in_country
def "geo:sea:south_china_sea" "The strategic, contested Southeast-Asian sea."
ln geo:sea:south_china_sea geo:sea thesaurus:related
ln geo:sea:south_china_sea geo:country:CHN geo:in_country
ln geo:sea:south_china_sea geo:country:VNM geo:in_country
ln geo:sea:south_china_sea geo:country:PHL geo:in_country
def "geo:sea:baltic_sea" "The brackish northern-European sea."
ln geo:sea:baltic_sea geo:sea thesaurus:related
ln geo:sea:baltic_sea geo:country:SWE geo:in_country
ln geo:sea:baltic_sea geo:country:FIN geo:in_country
ln geo:sea:baltic_sea geo:country:DEU geo:in_country
ln geo:sea:baltic_sea geo:country:POL geo:in_country
def "geo:sea:aegean_sea" "The island-studded sea of the ancient Greeks."
ln geo:sea:aegean_sea geo:sea thesaurus:related
ln geo:sea:aegean_sea geo:country:GRC geo:in_country
ln geo:sea:aegean_sea geo:country:TUR geo:in_country

def "geo:ocean" "One of Earth's five oceans (大洋)."
def "geo:ocean:pacific" "The largest and deepest ocean."
ln geo:ocean:pacific geo:ocean thesaurus:related
def "geo:ocean:atlantic" "The ocean between the Americas and Europe/Africa."
ln geo:ocean:atlantic geo:ocean thesaurus:related
def "geo:ocean:indian_ocean" "The ocean south of Asia."
ln geo:ocean:indian_ocean geo:ocean thesaurus:related
def "geo:ocean:arctic_ocean" "The ice-covered northern ocean."
ln geo:ocean:arctic_ocean geo:ocean thesaurus:related
def "geo:ocean:southern_ocean" "The ocean encircling Antarctica."
ln geo:ocean:southern_ocean geo:ocean thesaurus:related

def "geo:river" "A major river (川)."
def "geo:river:nile" "The world's longest river, lifeblood of Egypt."
ln geo:river:nile geo:river thesaurus:related
ln geo:river:nile geo:country:EGY geo:in_country
ln geo:river:nile geo:country:SDN geo:in_country
ln geo:river:nile geo:country:UGA geo:in_country
def "geo:river:amazon" "The largest river by discharge, through the rainforest."
ln geo:river:amazon geo:river thesaurus:related
ln geo:river:amazon geo:country:BRA geo:in_country
ln geo:river:amazon geo:country:PER geo:in_country
ln geo:river:amazon geo:country:COL geo:in_country
def "geo:river:yangtze" "Asia's longest river, artery of China."
ln geo:river:yangtze geo:river thesaurus:related
ln geo:river:yangtze geo:country:CHN geo:in_country
def "geo:river:mississippi" "The great river of the American heartland."
ln geo:river:mississippi geo:river thesaurus:related
ln geo:river:mississippi geo:country:USA geo:in_country
def "geo:river:ganges" "The sacred river of the Indian plains."
ln geo:river:ganges geo:river thesaurus:related
ln geo:river:ganges geo:country:IND geo:in_country
ln geo:river:ganges geo:country:BGD geo:in_country
def "geo:river:danube" "Europe's second-longest, crossing ten countries."
ln geo:river:danube geo:river thesaurus:related
ln geo:river:danube geo:country:DEU geo:in_country
ln geo:river:danube geo:country:AUT geo:in_country
ln geo:river:danube geo:country:HUN geo:in_country
ln geo:river:danube geo:country:ROU geo:in_country
def "geo:river:rhine" "The commercial artery of western Europe."
ln geo:river:rhine geo:river thesaurus:related
ln geo:river:rhine geo:country:CHE geo:in_country
ln geo:river:rhine geo:country:DEU geo:in_country
ln geo:river:rhine geo:country:NLD geo:in_country
def "geo:river:volga" "Europe's longest river, mother of Russia."
ln geo:river:volga geo:river thesaurus:related
ln geo:river:volga geo:country:RUS geo:in_country
def "geo:river:mekong" "The great river of mainland Southeast Asia."
ln geo:river:mekong geo:river thesaurus:related
ln geo:river:mekong geo:country:CHN geo:in_country
ln geo:river:mekong geo:country:THA geo:in_country
ln geo:river:mekong geo:country:KHM geo:in_country
ln geo:river:mekong geo:country:VNM geo:in_country
ln geo:river:mekong geo:country:LAO geo:in_country
def "geo:river:congo_river" "The deepest river, draining the Congo basin."
ln geo:river:congo_river geo:river thesaurus:related
ln geo:river:congo_river geo:country:COD geo:in_country

def "geo:lake" "A major lake (湖)."
def "geo:lake:lake_superior" "The largest freshwater lake by area."
ln geo:lake:lake_superior geo:lake thesaurus:related
ln geo:lake:lake_superior geo:country:USA geo:in_country
ln geo:lake:lake_superior geo:country:CAN geo:in_country
def "geo:lake:lake_victoria" "Africa's largest lake, a Nile source."
ln geo:lake:lake_victoria geo:lake thesaurus:related
ln geo:lake:lake_victoria geo:country:TZA geo:in_country
ln geo:lake:lake_victoria geo:country:UGA geo:in_country
ln geo:lake:lake_victoria geo:country:KEN geo:in_country
def "geo:lake:lake_baikal" "The world's deepest and oldest lake."
ln geo:lake:lake_baikal geo:lake thesaurus:related
ln geo:lake:lake_baikal geo:country:RUS geo:in_country
def "geo:lake:caspian_sea" "The largest inland body of water (a salt lake)."
ln geo:lake:caspian_sea geo:lake thesaurus:related
ln geo:lake:caspian_sea geo:country:RUS geo:in_country
ln geo:lake:caspian_sea geo:country:IRN geo:in_country
ln geo:lake:caspian_sea geo:country:KAZ geo:in_country
def "geo:lake:lake_tanganyika" "The world's second-deepest lake."
ln geo:lake:lake_tanganyika geo:lake thesaurus:related
ln geo:lake:lake_tanganyika geo:country:TZA geo:in_country
ln geo:lake:lake_tanganyika geo:country:COD geo:in_country

def "geo:desert" "A desert (砂漠)."
def "geo:desert:sahara" "The world's largest hot desert, across North Africa."
ln geo:desert:sahara geo:desert thesaurus:related
ln geo:desert:sahara geo:country:DZA geo:in_country
ln geo:desert:sahara geo:country:LBY geo:in_country
ln geo:desert:sahara geo:country:EGY geo:in_country
ln geo:desert:sahara geo:country:MLI geo:in_country
def "geo:desert:arabian_desert" "The vast desert of the Arabian Peninsula."
ln geo:desert:arabian_desert geo:desert thesaurus:related
ln geo:desert:arabian_desert geo:country:SAU geo:in_country
def "geo:desert:gobi" "The cold desert of East Asia."
ln geo:desert:gobi geo:desert thesaurus:related
ln geo:desert:gobi geo:country:MNG geo:in_country
ln geo:desert:gobi geo:country:CHN geo:in_country
def "geo:desert:kalahari" "The semi-arid savanna-desert of southern Africa."
ln geo:desert:kalahari geo:desert thesaurus:related
ln geo:desert:kalahari geo:country:BWA geo:in_country
ln geo:desert:kalahari geo:country:NAM geo:in_country
def "geo:desert:atacama" "The driest non-polar desert, in the Andes' rain shadow."
ln geo:desert:atacama geo:desert thesaurus:related
ln geo:desert:atacama geo:country:CHL geo:in_country

def "geo:plain" "A great plain, steppe or lowland (平野/草原)."
def "geo:plain:great_plains" "The vast grassland heartland of North America."
ln geo:plain:great_plains geo:plain thesaurus:related
ln geo:plain:great_plains geo:country:USA geo:in_country
ln geo:plain:great_plains geo:country:CAN geo:in_country
def "geo:plain:pampas" "The fertile lowland grassland of Argentina."
ln geo:plain:pampas geo:plain thesaurus:related
ln geo:plain:pampas geo:country:ARG geo:in_country
def "geo:plain:eurasian_steppe" "The grass corridor that carried nomads across Eurasia."
ln geo:plain:eurasian_steppe geo:plain thesaurus:related
ln geo:plain:eurasian_steppe geo:country:RUS geo:in_country
ln geo:plain:eurasian_steppe geo:country:KAZ geo:in_country
ln geo:plain:eurasian_steppe geo:country:MNG geo:in_country
def "geo:plain:north_european_plain" "The broad lowland from France to Russia."
ln geo:plain:north_european_plain geo:plain thesaurus:related
ln geo:plain:north_european_plain geo:country:DEU geo:in_country
ln geo:plain:north_european_plain geo:country:POL geo:in_country
ln geo:plain:north_european_plain geo:country:RUS geo:in_country
def "geo:plain:indo_gangetic_plain" "The fertile, densely-peopled plain of the Ganges and Indus."
ln geo:plain:indo_gangetic_plain geo:plain thesaurus:related
ln geo:plain:indo_gangetic_plain geo:country:IND geo:in_country
ln geo:plain:indo_gangetic_plain geo:country:PAK geo:in_country
ln geo:plain:indo_gangetic_plain geo:country:BGD geo:in_country

