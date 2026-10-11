# Akasha ontology — cooking techniques: type axis + origin cuisine + additions.
# Classify techniques by heat/method type and by culinary origin, and add
# culturally-important techniques missing from the Wikidata set (Turkish,
# Indian, Mexican, Chinese, Korean, Japanese categories, French, etc.). Base pack.

def "technique_type:dry_heat" "Dry-heat cooking (roast/grill/bake/sear — no water/fat medium)."
def "technique_type:moist_heat" "Moist-heat cooking (boil/simmer/poach/steam/blanch)."
def "technique_type:fat_cooking" "Fat-based cooking (sauté/stir-fry/deep-fry/confit)."
def "technique_type:combination" "Combination (braise/stew/pot — sear then moist)."
def "technique_type:sous_vide" "Precision low-temp / vapour (sous-vide, en papillote)."
def "technique_type:raw" "Raw / no-heat preparation (marinate/cure/slice)."
def "technique_type:preserve" "Preservation (ferment/pickle/cure/dry/smoke-preserve)."
def "technique_type:smoke" "Smoking (flavour/preserve with smoke)."

# ── new techniques ──
def "technique:tandir" "Tandır — Turkish clay pit oven for bread and meats."
ln technique:tandir technique_type:dry_heat culinary:technique_type
ln technique:tandir cuisine:turkish thesaurus:related
def "technique:mangal" "Mangal — Turkish/Levantine charcoal grill."
ln technique:mangal technique_type:dry_heat culinary:technique_type
ln technique:mangal cuisine:turkish thesaurus:related
def "technique:sis_kebab" "Şiş — skewer-grilling over coals."
ln technique:sis_kebab technique_type:dry_heat culinary:technique_type
ln technique:sis_kebab cuisine:turkish thesaurus:related
def "technique:sac_griddle" "Saç — convex iron griddle for flatbreads and sautés."
ln technique:sac_griddle technique_type:dry_heat culinary:technique_type
ln technique:sac_griddle cuisine:turkish thesaurus:related
def "technique:guvec" "Güveç — Turkish clay-pot stew."
ln technique:guvec technique_type:combination culinary:technique_type
ln technique:guvec cuisine:turkish thesaurus:related
def "technique:koz" "Köz — charring vegetables directly on embers."
ln technique:koz technique_type:dry_heat culinary:technique_type
ln technique:koz cuisine:turkish thesaurus:related
def "technique:tandoor" "Tandoor — Indian clay oven; naan and tandoori meats."
ln technique:tandoor technique_type:dry_heat culinary:technique_type
ln technique:tandoor cuisine:indian thesaurus:related
def "technique:tadka" "Tadka / tarka — blooming whole spices in hot fat, poured over a dish."
ln technique:tadka technique_type:fat_cooking culinary:technique_type
ln technique:tadka cuisine:indian thesaurus:related
def "technique:dum" "Dum — slow steaming in a sealed (dough-luted) pot."
ln technique:dum technique_type:combination culinary:technique_type
ln technique:dum cuisine:indian thesaurus:related
def "technique:bhuna" "Bhuna — sautéing and reducing spices and aromatics."
ln technique:bhuna technique_type:fat_cooking culinary:technique_type
ln technique:bhuna cuisine:indian thesaurus:related
def "technique:dhungar" "Dhungar — smoke-infusing with live charcoal and ghee."
ln technique:dhungar technique_type:smoke culinary:technique_type
ln technique:dhungar cuisine:indian thesaurus:related
def "technique:nixtamalization" "Nixtamalization — alkaline (lime) treatment of maize."
ln technique:nixtamalization technique_type:preserve culinary:technique_type
ln technique:nixtamalization cuisine:mexican thesaurus:related
def "technique:comal" "Comal — dry clay/metal griddle for tortillas and toasting."
ln technique:comal technique_type:dry_heat culinary:technique_type
ln technique:comal cuisine:mexican thesaurus:related
def "technique:barbacoa" "Barbacoa — pit-steaming wrapped meat."
ln technique:barbacoa technique_type:combination culinary:technique_type
ln technique:barbacoa cuisine:mexican thesaurus:related
def "technique:velveting" "Velveting — starch/egg coating then oil- or water-blanching."
ln technique:velveting technique_type:fat_cooking culinary:technique_type
ln technique:velveting cuisine:chinese thesaurus:related
def "technique:bao_flash_fry" "爆 bao — very-high-heat flash frying."
ln technique:bao_flash_fry technique_type:fat_cooking culinary:technique_type
ln technique:bao_flash_fry cuisine:chinese thesaurus:related
def "technique:clay_pot" "煲 — Cantonese clay-pot cooking."
ln technique:clay_pot technique_type:combination culinary:technique_type
ln technique:clay_pot cuisine:chinese thesaurus:related
def "technique:bulgogi_grill" "Bulgogi — marinated thin-slice grilling."
ln technique:bulgogi_grill technique_type:dry_heat culinary:technique_type
ln technique:bulgogi_grill cuisine:korean thesaurus:related
def "technique:jjigae" "Jjigae — Korean stew."
ln technique:jjigae technique_type:combination culinary:technique_type
ln technique:jjigae cuisine:korean thesaurus:related
def "technique:yakimono" "焼き物 — Japanese grilling/broiling category."
ln technique:yakimono technique_type:dry_heat culinary:technique_type
ln technique:yakimono cuisine:japanese thesaurus:related
def "technique:agemono" "揚げ物 — Japanese deep-frying category."
ln technique:agemono technique_type:fat_cooking culinary:technique_type
ln technique:agemono cuisine:japanese thesaurus:related
def "technique:mushimono" "蒸し物 — Japanese steaming category."
ln technique:mushimono technique_type:moist_heat culinary:technique_type
ln technique:mushimono cuisine:japanese thesaurus:related
def "technique:nabemono" "鍋物 — Japanese one-pot / hot-pot cooking."
ln technique:nabemono technique_type:combination culinary:technique_type
ln technique:nabemono cuisine:japanese thesaurus:related
def "technique:shioyaki" "塩焼き — salt-grilling of fish."
ln technique:shioyaki technique_type:dry_heat culinary:technique_type
ln technique:shioyaki cuisine:japanese thesaurus:related
def "technique:poele" "Poêlé — butter pot-roasting under cover."
ln technique:poele technique_type:fat_cooking culinary:technique_type
ln technique:poele cuisine:french thesaurus:related
def "technique:sofrito" "Sofrito / soffritto — aromatic base gently fried in fat."
ln technique:sofrito technique_type:fat_cooking culinary:technique_type
ln technique:sofrito cuisine:spanish thesaurus:related
def "technique:tagine" "Tagine — slow-braising in a conical clay pot."
ln technique:tagine technique_type:combination culinary:technique_type
ln technique:tagine cuisine:moroccan thesaurus:related
def "technique:a_la_plancha" "A la plancha — searing on a flat metal griddle."
ln technique:a_la_plancha technique_type:dry_heat culinary:technique_type
ln technique:a_la_plancha cuisine:spanish thesaurus:related
def "technique:low_and_slow" "Low-and-slow — long barbecue smoking."
ln technique:low_and_slow technique_type:smoke culinary:technique_type
ln technique:low_and_slow cuisine:american thesaurus:related
def "technique:leche_de_tigre" "Leche de tigre — citrus-chilli cure for ceviche."
ln technique:leche_de_tigre technique_type:raw culinary:technique_type
ln technique:leche_de_tigre cuisine:peruvian thesaurus:related

# ── classify existing techniques by type ──
ln technique:roasting technique_type:dry_heat culinary:technique_type
ln technique:baking technique_type:dry_heat culinary:technique_type
ln technique:grilling technique_type:dry_heat culinary:technique_type
ln technique:searing technique_type:dry_heat culinary:technique_type
ln technique:rotisserie technique_type:dry_heat culinary:technique_type
ln technique:gratinating technique_type:dry_heat culinary:technique_type
ln technique:blackening technique_type:dry_heat culinary:technique_type
ln technique:dry_roasting technique_type:dry_heat culinary:technique_type
ln technique:pit_barbecue technique_type:dry_heat culinary:technique_type
ln technique:parrilla_venezolana technique_type:dry_heat culinary:technique_type
ln technique:hangi technique_type:dry_heat culinary:technique_type
ln technique:backwood_cooking technique_type:dry_heat culinary:technique_type
ln technique:torrefacto technique_type:dry_heat culinary:technique_type
ln technique:boiling technique_type:moist_heat culinary:technique_type
ln technique:simmering technique_type:moist_heat culinary:technique_type
ln technique:poaching technique_type:moist_heat culinary:technique_type
ln technique:steaming technique_type:moist_heat culinary:technique_type
ln technique:shallow_poaching technique_type:moist_heat culinary:technique_type
ln technique:double_boiling technique_type:moist_heat culinary:technique_type
ln technique:double_steaming technique_type:moist_heat culinary:technique_type
ln technique:pressure_cooking technique_type:moist_heat culinary:technique_type
ln technique:shocking technique_type:moist_heat culinary:technique_type
ln technique:en_papillote technique_type:moist_heat culinary:technique_type
ln technique:steeping technique_type:moist_heat culinary:technique_type
ln technique:nimono technique_type:moist_heat culinary:technique_type
ln technique:jorim technique_type:moist_heat culinary:technique_type
ln technique:yamatoni technique_type:moist_heat culinary:technique_type
ln technique:ankake technique_type:moist_heat culinary:technique_type
ln technique:sauteing technique_type:fat_cooking culinary:technique_type
ln technique:stir_frying technique_type:fat_cooking culinary:technique_type
ln technique:deep_frying technique_type:fat_cooking culinary:technique_type
ln technique:confiting technique_type:fat_cooking culinary:technique_type
ln technique:karaage technique_type:fat_cooking culinary:technique_type
ln technique:gan_bian technique_type:fat_cooking culinary:technique_type
ln technique:gan_guo technique_type:fat_cooking culinary:technique_type
ln technique:phat_khing technique_type:fat_cooking culinary:technique_type
ln technique:rehogar technique_type:fat_cooking culinary:technique_type
ln technique:kinpira technique_type:fat_cooking culinary:technique_type
ln technique:meuniere_sauce technique_type:fat_cooking culinary:technique_type
ln technique:braising technique_type:combination culinary:technique_type
ln technique:stewing technique_type:combination culinary:technique_type
ln technique:red_cooking technique_type:combination culinary:technique_type
ln technique:fricassee technique_type:combination culinary:technique_type
ln technique:smothering technique_type:combination culinary:technique_type
ln technique:salmis technique_type:combination culinary:technique_type
ln technique:maggi_goreng technique_type:combination culinary:technique_type
ln technique:marinating technique_type:raw culinary:technique_type
ln technique:sashimizu technique_type:raw culinary:technique_type
ln technique:arai technique_type:raw culinary:technique_type
ln technique:zuke technique_type:raw culinary:technique_type
ln technique:maceration technique_type:raw culinary:technique_type
ln technique:kobujime technique_type:raw culinary:technique_type
ln technique:sujime technique_type:raw culinary:technique_type
ln technique:ohitashi technique_type:raw culinary:technique_type
ln technique:fermentation technique_type:preserve culinary:technique_type
ln technique:pickling technique_type:preserve culinary:technique_type
ln technique:brining technique_type:preserve culinary:technique_type
ln technique:food_drying technique_type:preserve culinary:technique_type
ln technique:charqui technique_type:preserve culinary:technique_type
ln technique:nukazuke technique_type:preserve culinary:technique_type
ln technique:mirinboshi technique_type:preserve culinary:technique_type
ln technique:salt_crust technique_type:preserve culinary:technique_type
ln technique:sugar_panning technique_type:preserve culinary:technique_type
ln technique:snap_freezing technique_type:preserve culinary:technique_type
ln technique:smoking technique_type:smoke culinary:technique_type
ln technique:sous_vide technique_type:sous_vide culinary:technique_type
ln technique:pouch_cooking technique_type:sous_vide culinary:technique_type

# ── origin cuisine for existing culture-specific techniques ──
ln technique:nimono cuisine:japanese thesaurus:related
ln technique:karaage cuisine:japanese thesaurus:related
ln technique:kinpira cuisine:japanese thesaurus:related
ln technique:ankake cuisine:japanese thesaurus:related
ln technique:nukazuke cuisine:japanese thesaurus:related
ln technique:mirinboshi cuisine:japanese thesaurus:related
ln technique:sashimizu cuisine:japanese thesaurus:related
ln technique:arai cuisine:japanese thesaurus:related
ln technique:zuke cuisine:japanese thesaurus:related
ln technique:kobujime cuisine:japanese thesaurus:related
ln technique:sujime cuisine:japanese thesaurus:related
ln technique:ohitashi cuisine:japanese thesaurus:related
ln technique:teriyaki cuisine:japanese thesaurus:related
ln technique:yamatoni cuisine:japanese thesaurus:related
ln technique:kiriyaki cuisine:japanese thesaurus:related
ln technique:mochi_pounding cuisine:japanese thesaurus:related
ln technique:gan_bian cuisine:chinese thesaurus:related
ln technique:gan_guo cuisine:chinese thesaurus:related
ln technique:red_cooking cuisine:chinese thesaurus:related
ln technique:double_steaming cuisine:chinese thesaurus:related
ln technique:jorim cuisine:korean thesaurus:related
ln technique:phat_khing cuisine:thai thesaurus:related
ln technique:philippine_asado cuisine:filipino thesaurus:related
ln technique:maggi_goreng cuisine:malaysian thesaurus:related
ln technique:fricassee cuisine:french thesaurus:related
ln technique:salmis cuisine:french thesaurus:related
ln technique:meuniere_sauce cuisine:french thesaurus:related
ln technique:confiting cuisine:french thesaurus:related
ln technique:en_papillote cuisine:french thesaurus:related
ln technique:sous_vide cuisine:french thesaurus:related
ln technique:flambe cuisine:french thesaurus:related
ln technique:rehogar cuisine:spanish thesaurus:related
ln technique:parrilla_venezolana cuisine:venezuelan thesaurus:related
ln technique:hangi cuisine:maori thesaurus:related
