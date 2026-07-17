# Akasha ontology — agriculture & agronomy (農学).
# ag:/agri: held only agritech; this adds the agricultural SCIENCES — soil, crop,
# animal and plant science — bridged to ag:/futureag:/foodsustain:/ingred:/
# occupation:/bio:/season:. Base pack.

def "agron" "Agronomy — the science of crop production and soil management (農学)."
ln agron occupation:farmer thesaurus:related

# ── soil science (土壌学) ──
def "agron:soil_science" "The study of soil as a natural resource (土壌学)."
ln agron:soil_science agron thesaurus:related
def "agron:soil_fertility" "The soil's capacity to supply nutrients to crops (地力)."
ln agron:soil_fertility agron thesaurus:related
ln agron:soil_fertility futureag:soil_health thesaurus:related
ln agron:soil_fertility ecol:nutrient_cycle thesaurus:related
def "agron:soil_erosion" "The loss of topsoil to wind and water (土壌侵食)."
ln agron:soil_erosion agron thesaurus:related
ln agron:soil_erosion futureag:no_till_farming thesaurus:related
def "agron:humus" "Decomposed organic matter enriching soil."
ln agron:humus agron thesaurus:related
def "agron:tillage" "Mechanical working of soil for planting (耕起)."
ln agron:tillage agron thesaurus:related
def "agron:fertilizer" "Material added to supply plant nutrients (肥料)."
ln agron:fertilizer agron thesaurus:related
ln agron:fertilizer chemeng:reactor thesaurus:related
ln agron:fertilizer futureag:regenerative_agriculture thesaurus:related
def "agron:compost" "Decomposed organic matter used as fertiliser (堆肥)."
ln agron:compost agron thesaurus:related
ln agron:compost gov:sanitation:recycling thesaurus:related
ln agron:compost foodsci:fermentation_science thesaurus:related
def "agron:nutrient_management" "Managing nutrient inputs for yield and environment."
ln agron:nutrient_management agron thesaurus:related
ln agron:nutrient_management enveng:water_pollution thesaurus:related
# ── crop science (作物学) ──
def "agron:crop_science" "The study of field-crop production (作物学)."
ln agron:crop_science agron thesaurus:related
def "agron:crop_rotation" "Alternating crops to preserve soil and break pests (輪作)."
ln agron:crop_rotation agron thesaurus:related
ln agron:crop_rotation futureag:regenerative_agriculture thesaurus:related
ln agron:crop_rotation futureag:agroecology thesaurus:related
def "agron:monoculture" "Growing a single crop over a large area."
ln agron:monoculture agron thesaurus:related
def "agron:irrigation" "Supplying water to crops (灌漑)."
ln agron:irrigation agron thesaurus:related
ln agron:irrigation ag:drip_irrigation thesaurus:related
ln agron:irrigation futureag:hydroponics thesaurus:related
ln agron:irrigation resource:water_resource thesaurus:related
def "agron:pesticide" "A chemical controlling pests (農薬)."
ln agron:pesticide agron thesaurus:related
ln agron:pesticide futureag:integrated_pest_management thesaurus:related
ln agron:pesticide enveng:soil_contamination thesaurus:related
def "agron:pollination" "Transfer of pollen enabling fruit and seed set (受粉)."
ln agron:pollination agron thesaurus:related
ln agron:pollination ecol:ecosystem_service thesaurus:related
ln agron:pollination ecol:biodiversity thesaurus:related
def "agron:plant_breeding" "Improving crops by selection and crossing (育種)."
ln agron:plant_breeding agron thesaurus:related
ln agron:plant_breeding futureag:gene_editing_crops thesaurus:related
ln agron:plant_breeding futureag:biofortification thesaurus:related
ln agron:plant_breeding life:genetics thesaurus:related
def "agron:harvest" "Gathering the mature crop (収穫)."
ln agron:harvest agron thesaurus:related
ln agron:harvest season:autumn thesaurus:related
ln agron:harvest foodsustain:seasonal_eating thesaurus:related
def "agron:horticulture" "The cultivation of fruits, vegetables and ornamentals (園芸)."
ln agron:horticulture agron thesaurus:related
ln agron:horticulture home:garden thesaurus:related
ln agron:horticulture activity:gardening thesaurus:related
# ── animal & plant science (畜産・植物) ──
def "agron:animal_science" "The science of livestock production (畜産学)."
ln agron:animal_science agron thesaurus:related
def "agron:animal_husbandry" "The care and breeding of farm animals (家畜飼育)."
ln agron:animal_husbandry agron thesaurus:related
ln agron:animal_husbandry occupation:rancher thesaurus:related
def "agron:livestock" "Farmed animals — cattle, pigs, poultry (家畜)."
ln agron:livestock agron thesaurus:related
ln agron:livestock occupation:rancher thesaurus:related
ln agron:livestock futureag:alternative_feed thesaurus:related
def "agron:grazing" "Feeding livestock on pasture."
ln agron:grazing agron thesaurus:related
ln agron:grazing futureag:regenerative_agriculture thesaurus:related
def "agron:dairy_science" "The science of milk production."
ln agron:dairy_science agron thesaurus:related
ln agron:dairy_science agron:animal_science thesaurus:related
def "agron:veterinary_science" "The medicine of animals (獣医学)."
ln agron:veterinary_science agron thesaurus:related
ln agron:veterinary_science occupation:veterinarian thesaurus:related
ln agron:veterinary_science med:medicine thesaurus:related
def "agron:photosynthesis" "How plants convert light to chemical energy — the base of the food chain (光合成)."
ln agron:photosynthesis agron thesaurus:related
ln agron:photosynthesis ecol:producer thesaurus:related
def "agron:germination" "The sprouting of a seed (発芽)."
ln agron:germination agron thesaurus:related
def "agron:cultivar" "A cultivated plant variety (品種)."
ln agron:cultivar agron thesaurus:related
ln agron:cultivar futureag:gene_editing_crops thesaurus:related
