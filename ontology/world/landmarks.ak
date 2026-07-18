# Akasha ontology (world pack) — landmarks & natural wonders.
# Famous places to visit, tied to their country. A-tier.

def "landmark:landmark" "A famous place worth visiting (名所/ランドマーク)."
def "landmark:type:monument" "A a built monument or icon."
def "landmark:type:natural_wonder" "A a wonder of nature."
def "landmark:type:religious_site" "A a sacred/religious site."
def "landmark:type:modern_icon" "A a modern architectural icon."

# ── landmarks → country & type ──
def "landmark:eiffel_tower" "Paris's iron lattice tower."
ln landmark:eiffel_tower landmark:landmark thesaurus:related
ln landmark:eiffel_tower landmark:type:modern_icon landmark:is
ln landmark:eiffel_tower geo:country:FRA landmark:in_country
def "landmark:statue_of_liberty" "New York's copper colossus of freedom."
ln landmark:statue_of_liberty landmark:landmark thesaurus:related
ln landmark:statue_of_liberty landmark:type:monument landmark:is
ln landmark:statue_of_liberty geo:country:USA landmark:in_country
def "landmark:big_ben" "London's great clock tower."
ln landmark:big_ben landmark:landmark thesaurus:related
ln landmark:big_ben landmark:type:monument landmark:is
ln landmark:big_ben geo:country:GBR landmark:in_country
def "landmark:sydney_opera_house" "The sail-roofed harbour opera house."
ln landmark:sydney_opera_house landmark:landmark thesaurus:related
ln landmark:sydney_opera_house landmark:type:modern_icon landmark:is
ln landmark:sydney_opera_house geo:country:AUS landmark:in_country
def "landmark:burj_khalifa" "Dubai's 828-m tallest building."
ln landmark:burj_khalifa landmark:landmark thesaurus:related
ln landmark:burj_khalifa landmark:type:modern_icon landmark:is
ln landmark:burj_khalifa geo:country:ARE landmark:in_country
def "landmark:christ_the_redeemer" "Rio's mountaintop Art-Deco Christ."
ln landmark:christ_the_redeemer landmark:landmark thesaurus:related
ln landmark:christ_the_redeemer landmark:type:religious_site landmark:is
ln landmark:christ_the_redeemer geo:country:BRA landmark:in_country
def "landmark:golden_gate_bridge" "San Francisco's red suspension bridge."
ln landmark:golden_gate_bridge landmark:landmark thesaurus:related
ln landmark:golden_gate_bridge landmark:type:modern_icon landmark:is
ln landmark:golden_gate_bridge geo:country:USA landmark:in_country
def "landmark:tokyo_tower" "Tokyo's red-and-white broadcasting tower."
ln landmark:tokyo_tower landmark:landmark thesaurus:related
ln landmark:tokyo_tower landmark:type:modern_icon landmark:is
ln landmark:tokyo_tower geo:country:JPN landmark:in_country
def "landmark:leaning_tower_of_pisa" "The famously tilting bell tower."
ln landmark:leaning_tower_of_pisa landmark:landmark thesaurus:related
ln landmark:leaning_tower_of_pisa landmark:type:monument landmark:is
ln landmark:leaning_tower_of_pisa geo:country:ITA landmark:in_country
def "landmark:brandenburg_gate" "Berlin's neoclassical triumphal gate."
ln landmark:brandenburg_gate landmark:landmark thesaurus:related
ln landmark:brandenburg_gate landmark:type:monument landmark:is
ln landmark:brandenburg_gate geo:country:DEU landmark:in_country
def "landmark:sagrada_familia" "Gaudí's still-unfinished Barcelona basilica."
ln landmark:sagrada_familia landmark:landmark thesaurus:related
ln landmark:sagrada_familia landmark:type:religious_site landmark:is
ln landmark:sagrada_familia geo:country:ESP landmark:in_country
def "landmark:niagara_falls" "The great falls on the US-Canada border."
ln landmark:niagara_falls landmark:landmark thesaurus:related
ln landmark:niagara_falls landmark:type:natural_wonder landmark:is
ln landmark:niagara_falls geo:country:USA landmark:in_country
def "landmark:mount_everest" "Earth's highest peak, 8,849 m."
ln landmark:mount_everest landmark:landmark thesaurus:related
ln landmark:mount_everest landmark:type:natural_wonder landmark:is
ln landmark:mount_everest geo:country:NPL landmark:in_country
def "landmark:victoria_falls" "'The smoke that thunders' of the Zambezi."
ln landmark:victoria_falls landmark:landmark thesaurus:related
ln landmark:victoria_falls landmark:type:natural_wonder landmark:is
ln landmark:victoria_falls geo:country:ZWE landmark:in_country
def "landmark:santorini" "The white-and-blue caldera island."
ln landmark:santorini landmark:landmark thesaurus:related
ln landmark:santorini landmark:type:natural_wonder landmark:is
ln landmark:santorini geo:country:GRC landmark:in_country
def "landmark:northern_lights" "The auroral light of the polar sky."
ln landmark:northern_lights landmark:landmark thesaurus:related
ln landmark:northern_lights landmark:type:natural_wonder landmark:is
ln landmark:northern_lights geo:country:ISL landmark:in_country
def "landmark:amazon_rainforest" "The planet's largest rainforest."
ln landmark:amazon_rainforest landmark:landmark thesaurus:related
ln landmark:amazon_rainforest landmark:type:natural_wonder landmark:is
ln landmark:amazon_rainforest geo:country:BRA landmark:in_country
