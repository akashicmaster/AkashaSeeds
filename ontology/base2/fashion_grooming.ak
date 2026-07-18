# Akasha ontology — personal: fashion, cosmetics, accessories, grooming.
# Clothing by body zone × formality × season; cosmetics by type; bags/wallets;
# and thegetting-ready activities (dressing/makeup/grooming) that going out requires.
# Built on home:closet, season:*, verb:act:wear. Base pack.

def "clothing" "A garment."
def "clothing_zone" "Body region a garment covers."
def "clothing_zone:head" "head"
def "clothing_zone:upper" "upper body"
def "clothing_zone:lower" "lower body"
def "clothing_zone:whole" "whole body"
def "clothing_zone:inner" "underclothes"
def "clothing_zone:feet" "feet"
def "clothing_zone:hands" "hands"
def "formality" "How formal an item of dress is."
def "formality:casual" "casual dress."
def "formality:smart_casual" "smart casual dress."
def "formality:business" "business dress."
def "formality:formal" "formal dress."
def "formality:sportswear" "sportswear dress."
def "formality:loungewear" "loungewear dress."

# ── clothing ──
def "clothing:t_shirt" "T shirt."
ln clothing:t_shirt clothing_zone:upper clothing:zone
ln clothing:t_shirt formality:casual clothing:formality
ln clothing:t_shirt home:closet home:located_in
ln clothing:t_shirt verb:act:wear verb:acts_on
ln clothing:t_shirt obj:durable obj_durability
def "clothing:dress_shirt" "Dress shirt."
ln clothing:dress_shirt clothing_zone:upper clothing:zone
ln clothing:dress_shirt formality:business clothing:formality
ln clothing:dress_shirt home:closet home:located_in
ln clothing:dress_shirt verb:act:wear verb:acts_on
ln clothing:dress_shirt obj:durable obj_durability
def "clothing:blouse" "Blouse."
ln clothing:blouse clothing_zone:upper clothing:zone
ln clothing:blouse formality:smart_casual clothing:formality
ln clothing:blouse home:closet home:located_in
ln clothing:blouse verb:act:wear verb:acts_on
ln clothing:blouse obj:durable obj_durability
def "clothing:sweater" "Sweater."
ln clothing:sweater clothing_zone:upper clothing:zone
ln clothing:sweater formality:casual clothing:formality
ln clothing:sweater home:closet home:located_in
ln clothing:sweater verb:act:wear verb:acts_on
ln clothing:sweater obj:durable obj_durability
ln clothing:sweater season:winter in_season
def "clothing:hoodie" "Hoodie."
ln clothing:hoodie clothing_zone:upper clothing:zone
ln clothing:hoodie formality:sportswear clothing:formality
ln clothing:hoodie home:closet home:located_in
ln clothing:hoodie verb:act:wear verb:acts_on
ln clothing:hoodie obj:durable obj_durability
def "clothing:tank_top" "Tank top."
ln clothing:tank_top clothing_zone:upper clothing:zone
ln clothing:tank_top formality:casual clothing:formality
ln clothing:tank_top home:closet home:located_in
ln clothing:tank_top verb:act:wear verb:acts_on
ln clothing:tank_top obj:durable obj_durability
ln clothing:tank_top season:summer in_season
def "clothing:polo_shirt" "Polo shirt."
ln clothing:polo_shirt clothing_zone:upper clothing:zone
ln clothing:polo_shirt formality:smart_casual clothing:formality
ln clothing:polo_shirt home:closet home:located_in
ln clothing:polo_shirt verb:act:wear verb:acts_on
ln clothing:polo_shirt obj:durable obj_durability
def "clothing:cardigan" "Cardigan."
ln clothing:cardigan clothing_zone:upper clothing:zone
ln clothing:cardigan formality:casual clothing:formality
ln clothing:cardigan home:closet home:located_in
ln clothing:cardigan verb:act:wear verb:acts_on
ln clothing:cardigan obj:durable obj_durability
def "clothing:jeans" "Jeans."
ln clothing:jeans clothing_zone:lower clothing:zone
ln clothing:jeans formality:casual clothing:formality
ln clothing:jeans home:closet home:located_in
ln clothing:jeans verb:act:wear verb:acts_on
ln clothing:jeans obj:durable obj_durability
def "clothing:trousers" "Trousers."
ln clothing:trousers clothing_zone:lower clothing:zone
ln clothing:trousers formality:business clothing:formality
ln clothing:trousers home:closet home:located_in
ln clothing:trousers verb:act:wear verb:acts_on
ln clothing:trousers obj:durable obj_durability
def "clothing:skirt" "Skirt."
ln clothing:skirt clothing_zone:lower clothing:zone
ln clothing:skirt formality:smart_casual clothing:formality
ln clothing:skirt home:closet home:located_in
ln clothing:skirt verb:act:wear verb:acts_on
ln clothing:skirt obj:durable obj_durability
def "clothing:shorts" "Shorts."
ln clothing:shorts clothing_zone:lower clothing:zone
ln clothing:shorts formality:casual clothing:formality
ln clothing:shorts home:closet home:located_in
ln clothing:shorts verb:act:wear verb:acts_on
ln clothing:shorts obj:durable obj_durability
ln clothing:shorts season:summer in_season
def "clothing:leggings" "Leggings."
ln clothing:leggings clothing_zone:lower clothing:zone
ln clothing:leggings formality:sportswear clothing:formality
ln clothing:leggings home:closet home:located_in
ln clothing:leggings verb:act:wear verb:acts_on
ln clothing:leggings obj:durable obj_durability
def "clothing:coat" "Coat."
ln clothing:coat clothing_zone:whole clothing:zone
ln clothing:coat formality:formal clothing:formality
ln clothing:coat home:closet home:located_in
ln clothing:coat verb:act:wear verb:acts_on
ln clothing:coat obj:durable obj_durability
ln clothing:coat season:winter in_season
def "clothing:jacket" "Jacket."
ln clothing:jacket clothing_zone:upper clothing:zone
ln clothing:jacket formality:smart_casual clothing:formality
ln clothing:jacket home:closet home:located_in
ln clothing:jacket verb:act:wear verb:acts_on
ln clothing:jacket obj:durable obj_durability
def "clothing:blazer" "Blazer."
ln clothing:blazer clothing_zone:upper clothing:zone
ln clothing:blazer formality:business clothing:formality
ln clothing:blazer home:closet home:located_in
ln clothing:blazer verb:act:wear verb:acts_on
ln clothing:blazer obj:durable obj_durability
def "clothing:raincoat" "Raincoat."
ln clothing:raincoat clothing_zone:whole clothing:zone
ln clothing:raincoat formality:casual clothing:formality
ln clothing:raincoat home:closet home:located_in
ln clothing:raincoat verb:act:wear verb:acts_on
ln clothing:raincoat obj:durable obj_durability
def "clothing:down_jacket" "Down jacket."
ln clothing:down_jacket clothing_zone:whole clothing:zone
ln clothing:down_jacket formality:casual clothing:formality
ln clothing:down_jacket home:closet home:located_in
ln clothing:down_jacket verb:act:wear verb:acts_on
ln clothing:down_jacket obj:durable obj_durability
ln clothing:down_jacket season:winter in_season
def "clothing:windbreaker" "Windbreaker."
ln clothing:windbreaker clothing_zone:upper clothing:zone
ln clothing:windbreaker formality:sportswear clothing:formality
ln clothing:windbreaker home:closet home:located_in
ln clothing:windbreaker verb:act:wear verb:acts_on
ln clothing:windbreaker obj:durable obj_durability
def "clothing:dress" "Dress."
ln clothing:dress clothing_zone:whole clothing:zone
ln clothing:dress formality:formal clothing:formality
ln clothing:dress home:closet home:located_in
ln clothing:dress verb:act:wear verb:acts_on
ln clothing:dress obj:durable obj_durability
def "clothing:suit" "Suit."
ln clothing:suit clothing_zone:whole clothing:zone
ln clothing:suit formality:business clothing:formality
ln clothing:suit home:closet home:located_in
ln clothing:suit verb:act:wear verb:acts_on
ln clothing:suit obj:durable obj_durability
def "clothing:gown" "Gown."
ln clothing:gown clothing_zone:whole clothing:zone
ln clothing:gown formality:formal clothing:formality
ln clothing:gown home:closet home:located_in
ln clothing:gown verb:act:wear verb:acts_on
ln clothing:gown obj:durable obj_durability
def "clothing:kimono" "Kimono."
ln clothing:kimono clothing_zone:whole clothing:zone
ln clothing:kimono formality:formal clothing:formality
ln clothing:kimono home:closet home:located_in
ln clothing:kimono verb:act:wear verb:acts_on
ln clothing:kimono obj:durable obj_durability
def "clothing:uniform" "Uniform."
ln clothing:uniform clothing_zone:whole clothing:zone
ln clothing:uniform formality:business clothing:formality
ln clothing:uniform home:closet home:located_in
ln clothing:uniform verb:act:wear verb:acts_on
ln clothing:uniform obj:durable obj_durability
def "clothing:jumpsuit" "Jumpsuit."
ln clothing:jumpsuit clothing_zone:whole clothing:zone
ln clothing:jumpsuit formality:casual clothing:formality
ln clothing:jumpsuit home:closet home:located_in
ln clothing:jumpsuit verb:act:wear verb:acts_on
ln clothing:jumpsuit obj:durable obj_durability
def "clothing:underwear" "Underwear."
ln clothing:underwear clothing_zone:inner clothing:zone
ln clothing:underwear formality:loungewear clothing:formality
ln clothing:underwear home:closet home:located_in
ln clothing:underwear verb:act:wear verb:acts_on
ln clothing:underwear obj:durable obj_durability
def "clothing:bra" "Bra."
ln clothing:bra clothing_zone:inner clothing:zone
ln clothing:bra formality:loungewear clothing:formality
ln clothing:bra home:closet home:located_in
ln clothing:bra verb:act:wear verb:acts_on
ln clothing:bra obj:durable obj_durability
def "clothing:socks" "Socks."
ln clothing:socks clothing_zone:inner clothing:zone
ln clothing:socks formality:casual clothing:formality
ln clothing:socks home:closet home:located_in
ln clothing:socks verb:act:wear verb:acts_on
ln clothing:socks obj:durable obj_durability
def "clothing:undershirt" "Undershirt."
ln clothing:undershirt clothing_zone:inner clothing:zone
ln clothing:undershirt formality:loungewear clothing:formality
ln clothing:undershirt home:closet home:located_in
ln clothing:undershirt verb:act:wear verb:acts_on
ln clothing:undershirt obj:durable obj_durability
def "clothing:tights" "Tights."
ln clothing:tights clothing_zone:inner clothing:zone
ln clothing:tights formality:smart_casual clothing:formality
ln clothing:tights home:closet home:located_in
ln clothing:tights verb:act:wear verb:acts_on
ln clothing:tights obj:durable obj_durability
ln clothing:tights season:winter in_season
def "clothing:stockings" "Stockings."
ln clothing:stockings clothing_zone:inner clothing:zone
ln clothing:stockings formality:formal clothing:formality
ln clothing:stockings home:closet home:located_in
ln clothing:stockings verb:act:wear verb:acts_on
ln clothing:stockings obj:durable obj_durability
def "clothing:pajamas" "Pajamas."
ln clothing:pajamas clothing_zone:whole clothing:zone
ln clothing:pajamas formality:loungewear clothing:formality
ln clothing:pajamas home:closet home:located_in
ln clothing:pajamas verb:act:wear verb:acts_on
ln clothing:pajamas obj:durable obj_durability
def "clothing:bathrobe" "Bathrobe."
ln clothing:bathrobe clothing_zone:whole clothing:zone
ln clothing:bathrobe formality:loungewear clothing:formality
ln clothing:bathrobe home:closet home:located_in
ln clothing:bathrobe verb:act:wear verb:acts_on
ln clothing:bathrobe obj:durable obj_durability
def "clothing:shoes" "Shoes."
ln clothing:shoes clothing_zone:feet clothing:zone
ln clothing:shoes formality:smart_casual clothing:formality
ln clothing:shoes home:closet home:located_in
ln clothing:shoes verb:act:wear verb:acts_on
ln clothing:shoes obj:durable obj_durability
def "clothing:sneakers" "Sneakers."
ln clothing:sneakers clothing_zone:feet clothing:zone
ln clothing:sneakers formality:sportswear clothing:formality
ln clothing:sneakers home:closet home:located_in
ln clothing:sneakers verb:act:wear verb:acts_on
ln clothing:sneakers obj:durable obj_durability
def "clothing:boots" "Boots."
ln clothing:boots clothing_zone:feet clothing:zone
ln clothing:boots formality:casual clothing:formality
ln clothing:boots home:closet home:located_in
ln clothing:boots verb:act:wear verb:acts_on
ln clothing:boots obj:durable obj_durability
ln clothing:boots season:winter in_season
def "clothing:sandals" "Sandals."
ln clothing:sandals clothing_zone:feet clothing:zone
ln clothing:sandals formality:casual clothing:formality
ln clothing:sandals home:closet home:located_in
ln clothing:sandals verb:act:wear verb:acts_on
ln clothing:sandals obj:durable obj_durability
ln clothing:sandals season:summer in_season
def "clothing:heels" "Heels."
ln clothing:heels clothing_zone:feet clothing:zone
ln clothing:heels formality:formal clothing:formality
ln clothing:heels home:closet home:located_in
ln clothing:heels verb:act:wear verb:acts_on
ln clothing:heels obj:durable obj_durability
def "clothing:loafers" "Loafers."
ln clothing:loafers clothing_zone:feet clothing:zone
ln clothing:loafers formality:smart_casual clothing:formality
ln clothing:loafers home:closet home:located_in
ln clothing:loafers verb:act:wear verb:acts_on
ln clothing:loafers obj:durable obj_durability
def "clothing:slippers" "Slippers."
ln clothing:slippers clothing_zone:feet clothing:zone
ln clothing:slippers formality:loungewear clothing:formality
ln clothing:slippers home:closet home:located_in
ln clothing:slippers verb:act:wear verb:acts_on
ln clothing:slippers obj:durable obj_durability
def "clothing:hat" "Hat."
ln clothing:hat clothing_zone:head clothing:zone
ln clothing:hat formality:casual clothing:formality
ln clothing:hat home:closet home:located_in
ln clothing:hat verb:act:wear verb:acts_on
ln clothing:hat obj:durable obj_durability
def "clothing:cap" "Cap."
ln clothing:cap clothing_zone:head clothing:zone
ln clothing:cap formality:casual clothing:formality
ln clothing:cap home:closet home:located_in
ln clothing:cap verb:act:wear verb:acts_on
ln clothing:cap obj:durable obj_durability
def "clothing:beanie" "Beanie."
ln clothing:beanie clothing_zone:head clothing:zone
ln clothing:beanie formality:casual clothing:formality
ln clothing:beanie home:closet home:located_in
ln clothing:beanie verb:act:wear verb:acts_on
ln clothing:beanie obj:durable obj_durability
ln clothing:beanie season:winter in_season
def "clothing:sunhat" "Sunhat."
ln clothing:sunhat clothing_zone:head clothing:zone
ln clothing:sunhat formality:casual clothing:formality
ln clothing:sunhat home:closet home:located_in
ln clothing:sunhat verb:act:wear verb:acts_on
ln clothing:sunhat obj:durable obj_durability
ln clothing:sunhat season:summer in_season
def "clothing:scarf" "Scarf."
ln clothing:scarf clothing_zone:upper clothing:zone
ln clothing:scarf formality:casual clothing:formality
ln clothing:scarf home:closet home:located_in
ln clothing:scarf verb:act:wear verb:acts_on
ln clothing:scarf obj:durable obj_durability
ln clothing:scarf season:winter in_season
def "clothing:gloves" "Gloves."
ln clothing:gloves clothing_zone:hands clothing:zone
ln clothing:gloves formality:casual clothing:formality
ln clothing:gloves home:closet home:located_in
ln clothing:gloves verb:act:wear verb:acts_on
ln clothing:gloves obj:durable obj_durability
ln clothing:gloves season:winter in_season

def "cosmetic" "A makeup or skincare product."
def "cosmetic_type:base" "complexion base"
def "cosmetic_type:eye" "eye makeup"
def "cosmetic_type:lip" "lip makeup"
def "cosmetic_type:cheek" "cheek makeup"
def "cosmetic_type:nail" "nail"
def "cosmetic_type:skincare" "skincare"
def "cosmetic_type:tool" "makeup tool"
# ── cosmetics → makeup ──
def "cosmetic:foundation" "Foundation."
ln cosmetic:foundation cosmetic_type:base thesaurus:related
ln cosmetic:foundation activity:makeup home:used_for
ln cosmetic:foundation furniture:dressing_table home:located_in
ln cosmetic:foundation obj:consumable obj_durability
ln cosmetic:foundation concept:daily_necessities civic:supplies
def "cosmetic:concealer" "Concealer."
ln cosmetic:concealer cosmetic_type:base thesaurus:related
ln cosmetic:concealer activity:makeup home:used_for
ln cosmetic:concealer furniture:dressing_table home:located_in
ln cosmetic:concealer obj:consumable obj_durability
ln cosmetic:concealer concept:daily_necessities civic:supplies
def "cosmetic:face_powder" "Face powder."
ln cosmetic:face_powder cosmetic_type:base thesaurus:related
ln cosmetic:face_powder activity:makeup home:used_for
ln cosmetic:face_powder furniture:dressing_table home:located_in
ln cosmetic:face_powder obj:consumable obj_durability
ln cosmetic:face_powder concept:daily_necessities civic:supplies
def "cosmetic:bb_cream" "Bb cream."
ln cosmetic:bb_cream cosmetic_type:base thesaurus:related
ln cosmetic:bb_cream activity:makeup home:used_for
ln cosmetic:bb_cream furniture:dressing_table home:located_in
ln cosmetic:bb_cream obj:consumable obj_durability
ln cosmetic:bb_cream concept:daily_necessities civic:supplies
def "cosmetic:mascara" "Mascara."
ln cosmetic:mascara cosmetic_type:eye thesaurus:related
ln cosmetic:mascara activity:makeup home:used_for
ln cosmetic:mascara furniture:dressing_table home:located_in
ln cosmetic:mascara obj:consumable obj_durability
ln cosmetic:mascara concept:daily_necessities civic:supplies
def "cosmetic:eyeliner" "Eyeliner."
ln cosmetic:eyeliner cosmetic_type:eye thesaurus:related
ln cosmetic:eyeliner activity:makeup home:used_for
ln cosmetic:eyeliner furniture:dressing_table home:located_in
ln cosmetic:eyeliner obj:consumable obj_durability
ln cosmetic:eyeliner concept:daily_necessities civic:supplies
def "cosmetic:eyeshadow" "Eyeshadow."
ln cosmetic:eyeshadow cosmetic_type:eye thesaurus:related
ln cosmetic:eyeshadow activity:makeup home:used_for
ln cosmetic:eyeshadow furniture:dressing_table home:located_in
ln cosmetic:eyeshadow obj:consumable obj_durability
ln cosmetic:eyeshadow concept:daily_necessities civic:supplies
def "cosmetic:eyebrow_pencil" "Eyebrow pencil."
ln cosmetic:eyebrow_pencil cosmetic_type:eye thesaurus:related
ln cosmetic:eyebrow_pencil activity:makeup home:used_for
ln cosmetic:eyebrow_pencil furniture:dressing_table home:located_in
ln cosmetic:eyebrow_pencil obj:consumable obj_durability
ln cosmetic:eyebrow_pencil concept:daily_necessities civic:supplies
def "cosmetic:lipstick" "Lipstick."
ln cosmetic:lipstick cosmetic_type:lip thesaurus:related
ln cosmetic:lipstick activity:makeup home:used_for
ln cosmetic:lipstick furniture:dressing_table home:located_in
ln cosmetic:lipstick obj:consumable obj_durability
ln cosmetic:lipstick concept:daily_necessities civic:supplies
def "cosmetic:lip_gloss" "Lip gloss."
ln cosmetic:lip_gloss cosmetic_type:lip thesaurus:related
ln cosmetic:lip_gloss activity:makeup home:used_for
ln cosmetic:lip_gloss furniture:dressing_table home:located_in
ln cosmetic:lip_gloss obj:consumable obj_durability
ln cosmetic:lip_gloss concept:daily_necessities civic:supplies
def "cosmetic:lip_balm" "Lip balm."
ln cosmetic:lip_balm cosmetic_type:lip thesaurus:related
ln cosmetic:lip_balm activity:makeup home:used_for
ln cosmetic:lip_balm furniture:dressing_table home:located_in
ln cosmetic:lip_balm obj:consumable obj_durability
ln cosmetic:lip_balm concept:daily_necessities civic:supplies
def "cosmetic:blush" "Blush."
ln cosmetic:blush cosmetic_type:cheek thesaurus:related
ln cosmetic:blush activity:makeup home:used_for
ln cosmetic:blush furniture:dressing_table home:located_in
ln cosmetic:blush obj:consumable obj_durability
ln cosmetic:blush concept:daily_necessities civic:supplies
def "cosmetic:bronzer" "Bronzer."
ln cosmetic:bronzer cosmetic_type:cheek thesaurus:related
ln cosmetic:bronzer activity:makeup home:used_for
ln cosmetic:bronzer furniture:dressing_table home:located_in
ln cosmetic:bronzer obj:consumable obj_durability
ln cosmetic:bronzer concept:daily_necessities civic:supplies
def "cosmetic:highlighter" "Highlighter."
ln cosmetic:highlighter cosmetic_type:cheek thesaurus:related
ln cosmetic:highlighter activity:makeup home:used_for
ln cosmetic:highlighter furniture:dressing_table home:located_in
ln cosmetic:highlighter obj:consumable obj_durability
ln cosmetic:highlighter concept:daily_necessities civic:supplies
def "cosmetic:nail_polish" "Nail polish."
ln cosmetic:nail_polish cosmetic_type:nail thesaurus:related
ln cosmetic:nail_polish activity:makeup home:used_for
ln cosmetic:nail_polish furniture:dressing_table home:located_in
ln cosmetic:nail_polish obj:consumable obj_durability
ln cosmetic:nail_polish concept:daily_necessities civic:supplies
def "cosmetic:moisturizer" "Moisturizer."
ln cosmetic:moisturizer cosmetic_type:skincare thesaurus:related
ln cosmetic:moisturizer activity:makeup home:used_for
ln cosmetic:moisturizer furniture:dressing_table home:located_in
ln cosmetic:moisturizer obj:consumable obj_durability
ln cosmetic:moisturizer concept:daily_necessities civic:supplies
def "cosmetic:cleanser" "Cleanser."
ln cosmetic:cleanser cosmetic_type:skincare thesaurus:related
ln cosmetic:cleanser activity:makeup home:used_for
ln cosmetic:cleanser furniture:dressing_table home:located_in
ln cosmetic:cleanser obj:consumable obj_durability
ln cosmetic:cleanser concept:daily_necessities civic:supplies
def "cosmetic:toner" "Toner."
ln cosmetic:toner cosmetic_type:skincare thesaurus:related
ln cosmetic:toner activity:makeup home:used_for
ln cosmetic:toner furniture:dressing_table home:located_in
ln cosmetic:toner obj:consumable obj_durability
ln cosmetic:toner concept:daily_necessities civic:supplies
def "cosmetic:sunscreen" "Sunscreen."
ln cosmetic:sunscreen cosmetic_type:skincare thesaurus:related
ln cosmetic:sunscreen activity:makeup home:used_for
ln cosmetic:sunscreen furniture:dressing_table home:located_in
ln cosmetic:sunscreen obj:consumable obj_durability
ln cosmetic:sunscreen concept:daily_necessities civic:supplies
def "cosmetic:serum" "Serum."
ln cosmetic:serum cosmetic_type:skincare thesaurus:related
ln cosmetic:serum activity:makeup home:used_for
ln cosmetic:serum furniture:dressing_table home:located_in
ln cosmetic:serum obj:consumable obj_durability
ln cosmetic:serum concept:daily_necessities civic:supplies
def "cosmetic:face_lotion" "Face lotion."
ln cosmetic:face_lotion cosmetic_type:skincare thesaurus:related
ln cosmetic:face_lotion activity:makeup home:used_for
ln cosmetic:face_lotion furniture:dressing_table home:located_in
ln cosmetic:face_lotion obj:consumable obj_durability
ln cosmetic:face_lotion concept:daily_necessities civic:supplies
def "cosmetic:makeup_brush" "Makeup brush."
ln cosmetic:makeup_brush cosmetic_type:tool thesaurus:related
ln cosmetic:makeup_brush activity:makeup home:used_for
ln cosmetic:makeup_brush furniture:dressing_table home:located_in
ln cosmetic:makeup_brush obj:durable obj_durability
def "cosmetic:makeup_sponge" "Makeup sponge."
ln cosmetic:makeup_sponge cosmetic_type:tool thesaurus:related
ln cosmetic:makeup_sponge activity:makeup home:used_for
ln cosmetic:makeup_sponge furniture:dressing_table home:located_in
ln cosmetic:makeup_sponge obj:consumable obj_durability
ln cosmetic:makeup_sponge concept:daily_necessities civic:supplies
def "cosmetic:tweezers" "Tweezers."
ln cosmetic:tweezers cosmetic_type:tool thesaurus:related
ln cosmetic:tweezers activity:makeup home:used_for
ln cosmetic:tweezers furniture:dressing_table home:located_in
ln cosmetic:tweezers obj:durable obj_durability
def "cosmetic:eyelash_curler" "Eyelash curler."
ln cosmetic:eyelash_curler cosmetic_type:tool thesaurus:related
ln cosmetic:eyelash_curler activity:makeup home:used_for
ln cosmetic:eyelash_curler furniture:dressing_table home:located_in
ln cosmetic:eyelash_curler obj:durable obj_durability

def "accessory" "A carried or worn accessory."
def "accessory_type:bag" "bag/luggage"
def "accessory_type:wallet" "money-carrier"
def "accessory_type:jewelry" "jewellery"
def "accessory_type:other" "other accessory"
# ── accessories ──
def "accessory:handbag" "Handbag."
ln accessory:handbag accessory_type:bag thesaurus:related
ln accessory:handbag home:closet home:located_in
ln accessory:handbag verb:act:wear verb:acts_on
ln accessory:handbag obj:durable obj_durability
def "accessory:backpack" "Backpack."
ln accessory:backpack accessory_type:bag thesaurus:related
ln accessory:backpack home:closet home:located_in
ln accessory:backpack verb:act:wear verb:acts_on
ln accessory:backpack obj:durable obj_durability
def "accessory:tote_bag" "Tote bag."
ln accessory:tote_bag accessory_type:bag thesaurus:related
ln accessory:tote_bag home:closet home:located_in
ln accessory:tote_bag verb:act:wear verb:acts_on
ln accessory:tote_bag obj:durable obj_durability
def "accessory:shoulder_bag" "Shoulder bag."
ln accessory:shoulder_bag accessory_type:bag thesaurus:related
ln accessory:shoulder_bag home:closet home:located_in
ln accessory:shoulder_bag verb:act:wear verb:acts_on
ln accessory:shoulder_bag obj:durable obj_durability
def "accessory:clutch" "Clutch."
ln accessory:clutch accessory_type:bag thesaurus:related
ln accessory:clutch home:closet home:located_in
ln accessory:clutch verb:act:wear verb:acts_on
ln accessory:clutch obj:durable obj_durability
def "accessory:suitcase" "Suitcase."
ln accessory:suitcase accessory_type:bag thesaurus:related
ln accessory:suitcase home:closet home:located_in
ln accessory:suitcase verb:act:wear verb:acts_on
ln accessory:suitcase obj:durable obj_durability
def "accessory:pouch" "Pouch."
ln accessory:pouch accessory_type:bag thesaurus:related
ln accessory:pouch home:closet home:located_in
ln accessory:pouch verb:act:wear verb:acts_on
ln accessory:pouch obj:durable obj_durability
def "accessory:wallet" "Wallet."
ln accessory:wallet accessory_type:wallet thesaurus:related
ln accessory:wallet home:closet home:located_in
ln accessory:wallet verb:act:wear verb:acts_on
ln accessory:wallet obj:durable obj_durability
def "accessory:purse" "Purse."
ln accessory:purse accessory_type:wallet thesaurus:related
ln accessory:purse home:closet home:located_in
ln accessory:purse verb:act:wear verb:acts_on
ln accessory:purse obj:durable obj_durability
def "accessory:coin_purse" "Coin purse."
ln accessory:coin_purse accessory_type:wallet thesaurus:related
ln accessory:coin_purse home:closet home:located_in
ln accessory:coin_purse verb:act:wear verb:acts_on
ln accessory:coin_purse obj:durable obj_durability
def "accessory:card_holder" "Card holder."
ln accessory:card_holder accessory_type:wallet thesaurus:related
ln accessory:card_holder home:closet home:located_in
ln accessory:card_holder verb:act:wear verb:acts_on
ln accessory:card_holder obj:durable obj_durability
def "accessory:necklace" "Necklace."
ln accessory:necklace accessory_type:jewelry thesaurus:related
ln accessory:necklace home:closet home:located_in
ln accessory:necklace verb:act:wear verb:acts_on
ln accessory:necklace obj:durable obj_durability
def "accessory:ring" "Ring."
ln accessory:ring accessory_type:jewelry thesaurus:related
ln accessory:ring home:closet home:located_in
ln accessory:ring verb:act:wear verb:acts_on
ln accessory:ring obj:durable obj_durability
def "accessory:earrings" "Earrings."
ln accessory:earrings accessory_type:jewelry thesaurus:related
ln accessory:earrings home:closet home:located_in
ln accessory:earrings verb:act:wear verb:acts_on
ln accessory:earrings obj:durable obj_durability
def "accessory:bracelet" "Bracelet."
ln accessory:bracelet accessory_type:jewelry thesaurus:related
ln accessory:bracelet home:closet home:located_in
ln accessory:bracelet verb:act:wear verb:acts_on
ln accessory:bracelet obj:durable obj_durability
def "accessory:watch" "Watch."
ln accessory:watch accessory_type:jewelry thesaurus:related
ln accessory:watch home:closet home:located_in
ln accessory:watch verb:act:wear verb:acts_on
ln accessory:watch obj:durable obj_durability
def "accessory:belt" "Belt."
ln accessory:belt accessory_type:other thesaurus:related
ln accessory:belt home:closet home:located_in
ln accessory:belt verb:act:wear verb:acts_on
ln accessory:belt obj:durable obj_durability
def "accessory:umbrella" "Umbrella."
ln accessory:umbrella accessory_type:other thesaurus:related
ln accessory:umbrella home:closet home:located_in
ln accessory:umbrella verb:act:wear verb:acts_on
ln accessory:umbrella obj:durable obj_durability
def "accessory:sunglasses" "Sunglasses."
ln accessory:sunglasses accessory_type:other thesaurus:related
ln accessory:sunglasses home:closet home:located_in
ln accessory:sunglasses verb:act:wear verb:acts_on
ln accessory:sunglasses obj:durable obj_durability

# ── grooming / going-out activities ──
def "activity:dressing" "着替え — getting dressed."
def "activity:makeup" "化粧 — applying makeup."
def "activity:grooming" "身だしなみ — grooming (hair, shaving, tidying)."
def "activity:going_out" "外出 — going out, which calls for dressing and grooming."
ln activity:dressing home concept:related
ln activity:grooming home concept:related
ln activity:going_out activity:dressing concept:requires
ln activity:going_out activity:makeup concept:requires
ln activity:going_out activity:grooming concept:requires
ln clothing activity:dressing thesaurus:related
ln activity:grooming home:bathroom civic:role_at
