# Akasha ontology — resource science (資源学).
# Natural resources, their extraction, reserves and management — bridged to
# geo:mineral, energy:, matsci:, foodsustain:, regulation: and gov:. Base pack.

def "resource" "A natural resource and its study (資源)."
# ── resource types ──
def "resource:natural_resource" "A material or energy source from nature used by society (天然資源)."
ln resource:natural_resource resource thesaurus:related
def "resource:renewable_resource" "A resource that replenishes on a human timescale (再生可能資源)."
ln resource:renewable_resource resource thesaurus:related
ln resource:renewable_resource energy:solar thesaurus:related
ln resource:renewable_resource energy:wind thesaurus:related
def "resource:nonrenewable_resource" "A resource depleted faster than it forms (枯渇性資源)."
ln resource:nonrenewable_resource resource thesaurus:related
ln resource:nonrenewable_resource energy:fossil thesaurus:related
def "resource:mineral_resource" "Economically useful minerals and metals (鉱物資源)."
ln resource:mineral_resource resource thesaurus:related
ln resource:mineral_resource geo:mineral:quartz thesaurus:related
ln resource:mineral_resource matsci:metal thesaurus:related
def "resource:energy_resource" "Sources of usable energy (fossil, nuclear, renewable) (エネルギー資源)."
ln resource:energy_resource resource thesaurus:related
ln resource:energy_resource energy:hydro thesaurus:related
ln resource:energy_resource energy:nuclear thesaurus:related
def "resource:water_resource" "Freshwater available for use (水資源)."
ln resource:water_resource resource thesaurus:related
ln resource:water_resource foodsustain:water_footprint thesaurus:related
ln resource:water_resource infra:water_supply thesaurus:related
def "resource:biological_resource" "Living resources — forests, fisheries, biodiversity (生物資源)."
ln resource:biological_resource resource thesaurus:related
ln resource:biological_resource regulation:fishing_ban thesaurus:related
ln resource:biological_resource futureag:aquaculture thesaurus:related
# ── extraction & processing ──
def "resource:mining" "Extracting minerals from the earth (採掘)."
ln resource:mining resource thesaurus:related
def "resource:ore" "Rock from which a metal is profitably extracted (鉱石)."
ln resource:ore resource thesaurus:related
ln resource:ore geo:mineral:pyrite thesaurus:related
ln resource:ore matsci:metal thesaurus:related
def "resource:reserves" "The known, economically recoverable quantity of a resource (埋蔵量)."
ln resource:reserves resource thesaurus:related
def "resource:deposit" "A natural concentration of a resource."
ln resource:deposit resource thesaurus:related
def "resource:prospecting" "Searching for exploitable resource deposits (探鉱)."
ln resource:prospecting resource thesaurus:related
def "resource:refining" "Purifying a raw resource into usable form (精錬)."
ln resource:refining resource thesaurus:related
ln resource:refining resource:energy_resource thesaurus:related
ln resource:refining chemeng:distillation thesaurus:related
def "resource:smelting" "Extracting metal from ore by heat (製錬)."
ln resource:smelting resource thesaurus:related
ln resource:smelting matsci:alloy thesaurus:related
ln resource:smelting chemeng:reactor thesaurus:related
def "resource:extraction" "Removing a resource from its natural setting."
ln resource:extraction resource thesaurus:related
# ── criticality, management & circularity ──
def "resource:rare_earth" "Rare-earth elements vital to magnets, batteries and electronics (希土類)."
ln resource:rare_earth resource thesaurus:related
ln resource:rare_earth electron:semiconductor thesaurus:related
ln resource:rare_earth eleceng:motor thesaurus:related
def "resource:critical_minerals" "Minerals essential to the economy yet supply-risky (重要鉱物)."
ln resource:critical_minerals resource thesaurus:related
ln resource:critical_minerals matsci:semiconductor thesaurus:related
def "resource:strategic_resource" "A resource of national-security importance."
ln resource:strategic_resource resource thesaurus:related
def "resource:resource_depletion" "The using-up of a finite resource (資源枯渇)."
ln resource:resource_depletion resource thesaurus:related
ln resource:resource_depletion resource:nonrenewable_resource thesaurus:related
ln resource:resource_depletion econ:scarcity thesaurus:related
def "resource:resource_security" "Securing reliable access to needed resources."
ln resource:resource_security resource thesaurus:related
def "resource:resource_management" "Governing extraction and use for the long term (資源管理)."
ln resource:resource_management resource thesaurus:related
ln resource:resource_management regulation:closed_season thesaurus:related
ln resource:resource_management gov:function:public_works thesaurus:related
def "resource:sustainable_resource_use" "Using resources within their capacity to renew."
ln resource:sustainable_resource_use resource thesaurus:related
ln resource:sustainable_resource_use foodsustain:food_sustainability thesaurus:related
def "resource:circular_economy" "Keeping materials in use through reuse and recycling (循環経済)."
ln resource:circular_economy resource thesaurus:related
ln resource:circular_economy foodsustain:circular_food_economy thesaurus:related
ln resource:circular_economy sus:recycling thesaurus:related
def "resource:recycling" "Recovering materials from waste for reuse (リサイクル)."
ln resource:recycling resource thesaurus:related
ln resource:recycling gov:sanitation:recycling thesaurus:related
ln resource:recycling foodsustain:food_waste thesaurus:related
def "resource:urban_mining" "Recovering metals from discarded products and e-waste (都市鉱山)."
ln resource:urban_mining resource thesaurus:related
ln resource:urban_mining electron:integrated_circuit thesaurus:related
ln resource:urban_mining sus:recycling thesaurus:related
def "resource:resource_geopolitics" "How resource control shapes power between states."
ln resource:resource_geopolitics resource thesaurus:related
ln resource:resource_geopolitics admin:country thesaurus:related
ln resource:resource_geopolitics fx:reserve_currency thesaurus:related
ln resource:resource_geopolitics foodstud:spice_trade thesaurus:related
