# Akasha ontology — archaeology & geography (考古学・地理学).
# archaeology/ was empty; geography as a discipline was thin (geo: is mostly
# places). Bridged to mus:/digarch:/epig:/earthsci:/oral:/cartog:/geo:/admin:/
# region:/dh:. Base pack.

def "archaeo" "Archaeology — the study of the human past through material remains (考古学)."
def "archaeo:excavation" "The careful digging and recording of a site (発掘)."
ln archaeo:excavation archaeo thesaurus:related
def "archaeo:archaeological_site" "A place with physical traces of past human activity (遺跡)."
ln archaeo:archaeological_site archaeo thesaurus:related
def "archaeo:artifact" "A portable object made or used by people (遺物)."
ln archaeo:artifact archaeo thesaurus:related
ln archaeo:artifact mus:artifact thesaurus:related
ln archaeo:artifact mus:accession thesaurus:related
def "archaeo:feature" "A non-portable trace — a hearth, posthole, wall (遺構)."
ln archaeo:feature archaeo thesaurus:related
def "archaeo:stratigraphy_arch" "Reading a site's layers to order events in time (層位)."
ln archaeo:stratigraphy_arch archaeo thesaurus:related
ln archaeo:stratigraphy_arch earthsci:stratigraphy thesaurus:related
def "archaeo:context" "The precise find-spot and associations of an object, its meaning-bearer."
ln archaeo:context archaeo thesaurus:related
ln archaeo:context mus:provenance thesaurus:related
ln archaeo:context lib:cataloging thesaurus:related
def "archaeo:potsherd" "A fragment of pottery, archaeology's most abundant find (土器片)."
ln archaeo:potsherd archaeo thesaurus:related
def "archaeo:material_culture" "The objects through which a society is studied."
ln archaeo:material_culture archaeo thesaurus:related
ln archaeo:material_culture foodstud:foodways thesaurus:related
ln archaeo:material_culture oral:oral_tradition thesaurus:related
def "archaeo:radiocarbon_dating" "Dating organic remains by carbon-14 decay (放射性炭素年代測定)."
ln archaeo:radiocarbon_dating archaeo thesaurus:related
ln archaeo:radiocarbon_dating earthsci:geology thesaurus:related
def "archaeo:dendrochronology" "Dating by tree-ring patterns (年輪年代学)."
ln archaeo:dendrochronology archaeo thesaurus:related
ln archaeo:dendrochronology archaeo:radiocarbon_dating thesaurus:related
def "archaeo:typology" "Classifying artifacts by form to order and compare them (型式学)."
ln archaeo:typology archaeo thesaurus:related
ln archaeo:typology lib:classification thesaurus:related
def "archaeo:seriation" "Ordering assemblages by changing style frequencies."
ln archaeo:seriation archaeo thesaurus:related
def "archaeo:field_survey" "Systematic surface search for sites (分布調査)."
ln archaeo:field_survey archaeo thesaurus:related
ln archaeo:field_survey dh:gis thesaurus:related
ln archaeo:field_survey geog:remote_sensing thesaurus:related
def "archaeo:prehistory" "The human past before written records (先史)."
ln archaeo:prehistory archaeo thesaurus:related
ln archaeo:prehistory oral:oral_tradition thesaurus:related
ln archaeo:prehistory epig:cuneiform thesaurus:related
def "archaeo:ethnoarchaeology" "Studying living peoples to interpret material remains."
ln archaeo:ethnoarchaeology archaeo thesaurus:related
ln archaeo:ethnoarchaeology socio:ethnography thesaurus:related
ln archaeo:ethnoarchaeology foodstud:food_ethnology thesaurus:related
def "archaeo:cultural_layer" "An occupation deposit accumulated by human activity (文化層)."
ln archaeo:cultural_layer archaeo thesaurus:related
# ── geography as a discipline (地理学) ──
def "geog" "Geography — the study of places, space and human–environment relations (地理学)."
def "geog:physical_geography" "The study of natural landscapes and processes (自然地理学)."
ln geog:physical_geography geog thesaurus:related
def "geog:human_geography" "The study of people, culture and economy in space (人文地理学)."
ln geog:human_geography geog thesaurus:related
def "geog:cartography" "The art and science of map-making (地図学)."
ln geog:cartography geog thesaurus:related
ln geog:cartography cartog:portolan_chart thesaurus:related
ln geog:cartography dh:gis thesaurus:related
def "geog:gis" "Geographic information systems for spatial data (GIS)."
ln geog:gis geog thesaurus:related
ln geog:gis dh:gis thesaurus:related
ln geog:gis ce:gis thesaurus:related
def "geog:remote_sensing" "Observing the earth from satellites and aircraft (リモートセンシング)."
ln geog:remote_sensing geog thesaurus:related
ln geog:remote_sensing ce:lidar_mapping thesaurus:related
ln geog:remote_sensing astro:planet thesaurus:related
ln geog:remote_sensing electron:sensor thesaurus:related
def "geog:spatial_analysis" "Analysing patterns and relations across space."
ln geog:spatial_analysis geog thesaurus:related
ln geog:spatial_analysis dh:geospatial_humanities thesaurus:related
ln geog:spatial_analysis math:statistics thesaurus:related
def "geog:geomorphology" "Landforms and the processes that shape them (地形学)."
ln geog:geomorphology geog thesaurus:related
ln geog:geomorphology earthsci:geomorphology thesaurus:related
ln geog:geomorphology earthsci:erosion thesaurus:related
def "geog:biogeography" "The distribution of life across space and time (生物地理学)."
ln geog:biogeography geog thesaurus:related
ln geog:biogeography ecol:biome thesaurus:related
ln geog:biogeography life:speciation thesaurus:related
def "geog:demography" "The statistical study of populations (人口学)."
ln geog:demography geog thesaurus:related
ln geog:demography socio:society thesaurus:related
ln geog:demography math:statistics thesaurus:related
ln geog:demography gov:function:civil_registry thesaurus:related
def "geog:urban_geography" "The study of cities and urban space (都市地理学)."
ln geog:urban_geography geog thesaurus:related
ln geog:urban_geography admin:city thesaurus:related
ln geog:urban_geography socio:urbanization thesaurus:related
def "geog:economic_geography" "The spatial patterns of economic activity (経済地理学)."
ln geog:economic_geography geog thesaurus:related
ln geog:economic_geography econ:trade thesaurus:related
ln geog:economic_geography resource:resource_geopolitics thesaurus:related
def "geog:cultural_geography" "How culture shapes and is shaped by place (文化地理学)."
ln geog:cultural_geography geog thesaurus:related
ln geog:cultural_geography foodstud:culinary_identity thesaurus:related
ln geog:cultural_geography region:mediterranean thesaurus:related
def "geog:geopolitics" "How geography shapes power between states (地政学)."
ln geog:geopolitics geog thesaurus:related
ln geog:geopolitics admin:country thesaurus:related
ln geog:geopolitics resource:resource_geopolitics thesaurus:related
ln geog:geopolitics fx:reserve_currency thesaurus:related
def "geog:place" "A location invested with human meaning (場所)."
ln geog:place geog thesaurus:related
def "geog:region" "An area unified by shared features (地域)."
ln geog:region geog thesaurus:related
ln geog:region region:east_asia thesaurus:related
ln geog:region admin:region thesaurus:related
