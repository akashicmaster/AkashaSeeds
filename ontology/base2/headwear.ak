# Akasha ontology — headwear (帽子): group + types.
# hat/cap/beanie/sunhat existed but 帽子 was not a group and lacked types.
# Group them and tie by season / sun / rain. Base pack.

def "concept:headwear" "帽子 — hats and caps worn on the head."
# ── new hat types ──
def "clothing:beret" "Beret."
ln clothing:beret clothing_zone:head clothing:zone
ln clothing:beret formality:smart_casual clothing:formality
ln clothing:beret home:closet home:located_in
ln clothing:beret verb:act:wear verb:acts_on
ln clothing:beret obj:durable obj_durability
ln clothing:beret concept:headwear thesaurus:related
def "clothing:fedora" "Fedora."
ln clothing:fedora clothing_zone:head clothing:zone
ln clothing:fedora formality:smart_casual clothing:formality
ln clothing:fedora home:closet home:located_in
ln clothing:fedora verb:act:wear verb:acts_on
ln clothing:fedora obj:durable obj_durability
ln clothing:fedora concept:headwear thesaurus:related
def "clothing:straw_hat" "Straw hat (麦わら帽子)."
ln clothing:straw_hat clothing_zone:head clothing:zone
ln clothing:straw_hat formality:casual clothing:formality
ln clothing:straw_hat home:closet home:located_in
ln clothing:straw_hat verb:act:wear verb:acts_on
ln clothing:straw_hat obj:durable obj_durability
ln clothing:straw_hat concept:headwear thesaurus:related
ln clothing:straw_hat season:summer in_season
ln clothing:straw_hat concept:sun_protection thesaurus:related
def "clothing:panama_hat" "Panama hat."
ln clothing:panama_hat clothing_zone:head clothing:zone
ln clothing:panama_hat formality:smart_casual clothing:formality
ln clothing:panama_hat home:closet home:located_in
ln clothing:panama_hat verb:act:wear verb:acts_on
ln clothing:panama_hat obj:durable obj_durability
ln clothing:panama_hat concept:headwear thesaurus:related
ln clothing:panama_hat season:summer in_season
ln clothing:panama_hat concept:sun_protection thesaurus:related
def "clothing:bucket_hat" "Bucket hat."
ln clothing:bucket_hat clothing_zone:head clothing:zone
ln clothing:bucket_hat formality:casual clothing:formality
ln clothing:bucket_hat home:closet home:located_in
ln clothing:bucket_hat verb:act:wear verb:acts_on
ln clothing:bucket_hat obj:durable obj_durability
ln clothing:bucket_hat concept:headwear thesaurus:related
def "clothing:knit_cap" "Knit cap (ニット帽)."
ln clothing:knit_cap clothing_zone:head clothing:zone
ln clothing:knit_cap formality:casual clothing:formality
ln clothing:knit_cap home:closet home:located_in
ln clothing:knit_cap verb:act:wear verb:acts_on
ln clothing:knit_cap obj:durable obj_durability
ln clothing:knit_cap concept:headwear thesaurus:related
ln clothing:knit_cap season:winter in_season
def "clothing:visor" "Visor."
ln clothing:visor clothing_zone:head clothing:zone
ln clothing:visor formality:sportswear clothing:formality
ln clothing:visor home:closet home:located_in
ln clothing:visor verb:act:wear verb:acts_on
ln clothing:visor obj:durable obj_durability
ln clothing:visor concept:headwear thesaurus:related
ln clothing:visor season:summer in_season
ln clothing:visor concept:sun_protection thesaurus:related
def "clothing:helmet" "Helmet."
ln clothing:helmet clothing_zone:head clothing:zone
ln clothing:helmet formality:sportswear clothing:formality
ln clothing:helmet home:closet home:located_in
ln clothing:helmet verb:act:wear verb:acts_on
ln clothing:helmet obj:durable obj_durability
ln clothing:helmet concept:headwear thesaurus:related
def "clothing:hood" "Hood."
ln clothing:hood clothing_zone:head clothing:zone
ln clothing:hood formality:casual clothing:formality
ln clothing:hood home:closet home:located_in
ln clothing:hood verb:act:wear verb:acts_on
ln clothing:hood obj:durable obj_durability
ln clothing:hood concept:headwear thesaurus:related
def "clothing:winter_hat" "Winter hat (防寒帽)."
ln clothing:winter_hat clothing_zone:head clothing:zone
ln clothing:winter_hat formality:casual clothing:formality
ln clothing:winter_hat home:closet home:located_in
ln clothing:winter_hat verb:act:wear verb:acts_on
ln clothing:winter_hat obj:durable obj_durability
ln clothing:winter_hat concept:headwear thesaurus:related
ln clothing:winter_hat season:winter in_season
def "clothing:rain_hat" "Rain hat (レインハット)."
ln clothing:rain_hat clothing_zone:head clothing:zone
ln clothing:rain_hat formality:casual clothing:formality
ln clothing:rain_hat home:closet home:located_in
ln clothing:rain_hat verb:act:wear verb:acts_on
ln clothing:rain_hat obj:durable obj_durability
ln clothing:rain_hat concept:headwear thesaurus:related
ln clothing:rain_hat concept:rain_gear thesaurus:related
ln clothing:rain_hat weather:precipitation home:used_for

# ── existing head items joined to the group ──
ln clothing:hat concept:headwear thesaurus:related
ln clothing:cap concept:headwear thesaurus:related
ln clothing:beanie concept:headwear thesaurus:related
ln clothing:sunhat concept:headwear thesaurus:related
