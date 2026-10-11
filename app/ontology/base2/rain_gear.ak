# Akasha ontology — rain gear & sun protection.
# raincoat/umbrella existed but 'rain gear' was not a group and lacked rain boots,
# poncho, folding umbrella, parasol. Group them, and tie to weather and season.
# weather: is meteorological vocabulary; weather:precipitation is the rain hook.
# Base pack.

def "concept:rain_gear" "雨具 — gear that keeps rain off (umbrella, raincoat, rain boots…)."
def "concept:sun_protection" "日除け — gear against strong sun (parasol, sun hat, sunglasses)."
def "concept:rainy_season" "梅雨/rainy season — a prolonged wet spell."
ln concept:rain_gear weather:precipitation thesaurus:related
ln concept:rainy_season weather:precipitation thesaurus:related
ln concept:rain_gear concept:rainy_season thesaurus:related

# ── rain clothing ──
def "clothing:rain_boots" "Rain boots (長靴)."
ln clothing:rain_boots clothing_zone:feet clothing:zone
ln clothing:rain_boots formality:casual clothing:formality
ln clothing:rain_boots home:closet home:located_in
ln clothing:rain_boots verb:act:wear verb:acts_on
ln clothing:rain_boots obj:durable obj_durability
ln clothing:rain_boots concept:rain_gear thesaurus:related
ln clothing:rain_boots weather:precipitation home:used_for
def "clothing:poncho" "Poncho."
ln clothing:poncho clothing_zone:whole clothing:zone
ln clothing:poncho formality:casual clothing:formality
ln clothing:poncho home:closet home:located_in
ln clothing:poncho verb:act:wear verb:acts_on
ln clothing:poncho obj:durable obj_durability
ln clothing:poncho concept:rain_gear thesaurus:related
ln clothing:poncho weather:precipitation home:used_for
def "clothing:rain_pants" "Rain pants."
ln clothing:rain_pants clothing_zone:lower clothing:zone
ln clothing:rain_pants formality:sportswear clothing:formality
ln clothing:rain_pants home:closet home:located_in
ln clothing:rain_pants verb:act:wear verb:acts_on
ln clothing:rain_pants obj:durable obj_durability
ln clothing:rain_pants concept:rain_gear thesaurus:related
ln clothing:rain_pants weather:precipitation home:used_for
def "clothing:waterproof_jacket" "Waterproof jacket."
ln clothing:waterproof_jacket clothing_zone:upper clothing:zone
ln clothing:waterproof_jacket formality:sportswear clothing:formality
ln clothing:waterproof_jacket home:closet home:located_in
ln clothing:waterproof_jacket verb:act:wear verb:acts_on
ln clothing:waterproof_jacket obj:durable obj_durability
ln clothing:waterproof_jacket concept:rain_gear thesaurus:related
ln clothing:waterproof_jacket weather:precipitation home:used_for

# ── rain accessories ──
def "accessory:folding_umbrella" "Folding umbrella (折り畳み傘)."
ln accessory:folding_umbrella accessory_type:other thesaurus:related
ln accessory:folding_umbrella home:closet home:located_in
ln accessory:folding_umbrella concept:rain_gear thesaurus:related
ln accessory:folding_umbrella weather:precipitation home:used_for
ln accessory:folding_umbrella obj:durable obj_durability

# ── sun protection ──
def "accessory:parasol" "Parasol (日傘)."
ln accessory:parasol accessory_type:other thesaurus:related
ln accessory:parasol home:closet home:located_in
ln accessory:parasol concept:sun_protection thesaurus:related
ln accessory:parasol season:summer in_season
ln accessory:parasol obj:durable obj_durability
ln clothing:sunhat concept:sun_protection thesaurus:related
ln accessory:sunglasses concept:sun_protection thesaurus:related

# ── existing items joined to the groups ──
ln clothing:raincoat concept:rain_gear thesaurus:related
ln clothing:raincoat weather:precipitation home:used_for
ln accessory:umbrella concept:rain_gear thesaurus:related
ln accessory:umbrella weather:precipitation home:used_for
ln clothing:boots concept:rain_gear thesaurus:related
# rain gear is what going out in the wet calls for
ln activity:going_out concept:rain_gear thesaurus:related
