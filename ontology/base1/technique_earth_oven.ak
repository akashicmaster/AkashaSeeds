# Akasha ontology — earth oven (pit-steaming), a distinct method split off.
# A pit lined with fire-heated stones and leaves (banana / ti / agave / maguey);
# food is wrapped, buried and STEAM-cooked — not the dry smoking of a pit
# barbecue. Widespread along the Pacific rim and into the Andes. Base pack.

def "technique:earth_oven" "Earth oven — food wrapped in leaves and steam-cooked in an earth pit over fire-heated stones. A distinct Pacific-to-Andes method."
ln technique:earth_oven technique_type:moist_heat culinary:technique_type
ln technique:earth_oven technique_type:combination culinary:technique_type
ln technique:earth_oven heat_source:ember technique:heat_source
ln technique:earth_oven heat_source:pit technique:heat_source

def "technique:curanto" "Curanto — Chilean/Chiloé earth oven over hot stones, layered with seafood, meat and potatoes under leaves."
ln technique:curanto technique:earth_oven technique:variant_of
ln technique:curanto cuisine:chilean thesaurus:related
def "technique:pachamanca" "Pachamanca — Andean earth oven; meats and tubers cooked over hot stones under earth."
ln technique:pachamanca technique:earth_oven technique:variant_of
ln technique:pachamanca cuisine:peruvian thesaurus:related
def "technique:imu" "Imu — Hawaiian underground oven (kālua), lined with ti/banana leaves."
ln technique:imu technique:earth_oven technique:variant_of
ln technique:imu cuisine:hawaiian thesaurus:related
def "technique:umu" "Umu — Polynesian (Samoan/Tongan) earth oven of hot stones."
ln technique:umu technique:earth_oven technique:variant_of
ln technique:umu cuisine:samoan thesaurus:related
def "technique:huatia" "Huatia — Andean field earth oven, especially for potatoes."
ln technique:huatia technique:earth_oven technique:variant_of
ln technique:huatia cuisine:peruvian thesaurus:related
def "technique:lovo" "Lovo — Fijian earth oven over heated stones."
ln technique:lovo technique:earth_oven technique:variant_of
ln technique:lovo cuisine:fijian thesaurus:related

# existing techniques re-tied to earth_oven
ln technique:hangi technique:earth_oven technique:variant_of
ln technique:barbacoa technique:earth_oven technique:variant_of
