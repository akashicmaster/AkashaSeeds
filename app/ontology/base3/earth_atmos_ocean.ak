# Akasha ontology — earth science, atmospheric science & oceanography.
# Complements the big geo: (mostly places) and weather: with the disciplines and
# processes. Bridged to geo:/weather:/astro:/ce:/resource:/ecol:. Base pack.

def "earthsci" "Earth science — the study of the planet's systems (地球科学)."
# ── geology & solid earth ──
def "earthsci:geology" "The study of the solid earth, its rocks and history (地質学)."
ln earthsci:geology earthsci thesaurus:related
def "earthsci:plate_tectonics" "The theory of moving lithospheric plates (プレートテクトニクス)."
ln earthsci:plate_tectonics earthsci thesaurus:related
ln earthsci:plate_tectonics geo:concept:plate_tectonics thesaurus:related
ln earthsci:plate_tectonics geo:concept:continental_drift thesaurus:related
def "earthsci:rock_cycle" "The transformation of rock among igneous, sedimentary and metamorphic (岩石循環)."
ln earthsci:rock_cycle earthsci thesaurus:related
ln earthsci:rock_cycle resource:ore thesaurus:related
def "earthsci:mineralogy" "The study of minerals (鉱物学)."
ln earthsci:mineralogy earthsci thesaurus:related
ln earthsci:mineralogy geo:mineral:quartz thesaurus:related
ln earthsci:mineralogy matsci:crystal_structure thesaurus:related
def "earthsci:stratigraphy" "The study of rock layers and their time order (層序学)."
ln earthsci:stratigraphy earthsci thesaurus:related
def "earthsci:seismology" "The study of earthquakes and seismic waves (地震学)."
ln earthsci:seismology earthsci thesaurus:related
ln earthsci:seismology ce:slope_stability thesaurus:related
ln earthsci:seismology electron:sensor thesaurus:related
def "earthsci:volcanology" "The study of volcanoes (火山学)."
ln earthsci:volcanology earthsci thesaurus:related
def "earthsci:geomorphology" "The study of landforms and the processes shaping them (地形学)."
ln earthsci:geomorphology earthsci thesaurus:related
def "earthsci:paleontology" "The study of fossils and ancient life (古生物学)."
ln earthsci:paleontology earthsci thesaurus:related
ln earthsci:paleontology life:evolution thesaurus:related
ln earthsci:paleontology life:phylogeny thesaurus:related
def "earthsci:erosion" "The wearing away of rock and soil by wind and water (侵食)."
ln earthsci:erosion earthsci thesaurus:related
ln earthsci:erosion agron:soil_erosion thesaurus:related
ln earthsci:erosion ce:river_engineering thesaurus:related
# ── atmosphere & climate ──
def "earthsci:meteorology" "The science of weather (気象学)."
ln earthsci:meteorology earthsci thesaurus:related
ln earthsci:meteorology weather:phenomenon thesaurus:related
ln earthsci:meteorology weather:system thesaurus:related
def "earthsci:atmosphere" "The gaseous envelope around the earth (大気)."
ln earthsci:atmosphere earthsci thesaurus:related
ln earthsci:atmosphere astro:planet thesaurus:related
def "earthsci:climatology" "The study of long-term climate (気候学)."
ln earthsci:climatology earthsci thesaurus:related
ln earthsci:climatology weather:climate thesaurus:related
ln earthsci:climatology enveng:climate_change thesaurus:related
def "earthsci:greenhouse_effect" "Atmospheric warming by heat-trapping gases (温室効果)."
ln earthsci:greenhouse_effect earthsci thesaurus:related
ln earthsci:greenhouse_effect enveng:greenhouse_gas thesaurus:related
ln earthsci:greenhouse_effect ecol:carbon_cycle thesaurus:related
def "earthsci:weather_forecasting" "Predicting future atmospheric states (天気予報)."
ln earthsci:weather_forecasting earthsci thesaurus:related
ln earthsci:weather_forecasting weather:precipitation thesaurus:related
ln earthsci:weather_forecasting ai:embedding thesaurus:related
ln earthsci:weather_forecasting electron:sensor thesaurus:related
def "earthsci:jet_stream" "Fast high-altitude air currents steering weather."
ln earthsci:jet_stream earthsci thesaurus:related
def "earthsci:el_nino" "A Pacific ocean–atmosphere cycle reshaping global weather."
ln earthsci:el_nino earthsci thesaurus:related
ln earthsci:el_nino earthsci:ocean_current thesaurus:related
ln earthsci:el_nino weather:climate thesaurus:related
def "earthsci:atmospheric_circulation" "The large-scale movement of air distributing heat."
ln earthsci:atmospheric_circulation earthsci thesaurus:related
# ── oceanography & hydrology ──
def "earthsci:oceanography" "The science of the oceans (海洋学)."
ln earthsci:oceanography earthsci thesaurus:related
def "earthsci:ocean_current" "Large-scale flows of seawater moving heat and nutrients (海流)."
ln earthsci:ocean_current earthsci thesaurus:related
def "earthsci:tide" "The periodic rise and fall of the sea (潮汐)."
ln earthsci:tide earthsci thesaurus:related
ln earthsci:tide astro:moon thesaurus:related
def "earthsci:salinity" "The salt content of seawater (塩分)."
ln earthsci:salinity earthsci thesaurus:related
def "earthsci:marine_ecosystem" "The living communities of the sea (海洋生態系)."
ln earthsci:marine_ecosystem earthsci thesaurus:related
ln earthsci:marine_ecosystem ecol:ecosystem thesaurus:related
ln earthsci:marine_ecosystem regulation:fishing_ban thesaurus:related
ln earthsci:marine_ecosystem futureag:aquaculture thesaurus:related
def "earthsci:coral_reef" "A biodiverse reef ecosystem built by corals (サンゴ礁)."
ln earthsci:coral_reef earthsci thesaurus:related
ln earthsci:coral_reef ecol:biodiversity thesaurus:related
ln earthsci:coral_reef enveng:climate_change thesaurus:related
def "earthsci:sea_level_rise" "The rising ocean level driven by warming (海面上昇)."
ln earthsci:sea_level_rise earthsci thesaurus:related
ln earthsci:sea_level_rise enveng:climate_change thesaurus:related
def "earthsci:hydrology" "The study of water movement through the earth system (水文学)."
ln earthsci:hydrology earthsci thesaurus:related
ln earthsci:hydrology ce:hydrology thesaurus:related
ln earthsci:hydrology infra:water_supply thesaurus:related
def "earthsci:watershed" "The land area draining to a common water body (流域)."
ln earthsci:watershed earthsci thesaurus:related
ln earthsci:watershed ce:river_engineering thesaurus:related
ln earthsci:watershed resource:water_resource thesaurus:related
def "earthsci:groundwater" "Water held underground in aquifers (地下水)."
ln earthsci:groundwater earthsci thesaurus:related
ln earthsci:groundwater resource:water_resource thesaurus:related
ln earthsci:groundwater agron:irrigation thesaurus:related
def "earthsci:aquifer" "An underground layer yielding usable water (帯水層)."
ln earthsci:aquifer earthsci thesaurus:related
ln earthsci:aquifer resource:water_resource thesaurus:related
