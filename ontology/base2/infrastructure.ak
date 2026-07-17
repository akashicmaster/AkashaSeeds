# Akasha ontology — social infrastructure (生活インフラ) + broadcasting.
# The technical layers exist (energy:/net:/ce:) but the everyday utility
# SERVICE to the household was missing and disconnected. infra:* utilities
# link three ways: to the home connection/appliance, to admin/gov provision,
# and to the technical layer that backs them. Plus broadcast:* (TV/radio/
# community). Base pack.

def "concept:utility" "A lifeline utility service delivered to households."
# ── utilities (ライフライン) → home / meter / tech / gov ──
def "infra:water_supply" "Water supply (上水道) — lifeline utility."
ln infra:water_supply concept:utility thesaurus:related
ln infra:water_supply home:faucet infra:delivered_via
ln infra:water_supply infra:water_meter infra:metered_by
ln infra:water_supply ce:hydrology infra:backed_by
ln infra:water_supply ce:water_quality infra:backed_by
ln infra:water_supply gov:function:public_works gov:provided_by
def "infra:sewerage" "Sewerage (下水道) — lifeline utility."
ln infra:sewerage concept:utility thesaurus:related
ln infra:sewerage drain infra:delivered_via
ln infra:sewerage ce:waste_management infra:backed_by
ln infra:sewerage gov:function:public_works gov:provided_by
def "infra:gas_supply" "Gas supply (都市ガス) — lifeline utility."
ln infra:gas_supply concept:utility thesaurus:related
ln infra:gas_supply gas_line infra:delivered_via
ln infra:gas_supply infra:gas_meter infra:metered_by
ln infra:gas_supply admin:country gov:regulated_by
def "infra:electricity_supply" "Electricity supply (電気) — lifeline utility."
ln infra:electricity_supply concept:utility thesaurus:related
ln infra:electricity_supply outlet infra:delivered_via
ln infra:electricity_supply infra:electricity_meter infra:metered_by
ln infra:electricity_supply energy:transmission infra:backed_by
ln infra:electricity_supply energy:distribution infra:backed_by
ln infra:electricity_supply admin:country gov:regulated_by
def "infra:telecom" "Telecom (電話/通信) — lifeline utility."
ln infra:telecom concept:utility thesaurus:related
ln infra:telecom home:telephone infra:delivered_via
ln infra:telecom net:cellular infra:backed_by
ln infra:telecom net:copper_ethernet infra:backed_by
ln infra:telecom admin:country gov:regulated_by
def "infra:internet" "Internet (インターネット) — lifeline utility."
ln infra:internet concept:utility thesaurus:related
ln infra:internet router infra:delivered_via
ln infra:internet net:fiber_optics infra:backed_by
ln infra:internet net:cellular infra:backed_by
ln infra:internet admin:country gov:regulated_by

# ── home connection points & meters ──
def "infra:outlet" "Outlet (コンセント)."
ln infra:outlet concept:utility thesaurus:related
ln infra:outlet home:living_room home:located_in
ln infra:outlet obj:durable obj_durability
def "infra:water_meter" "Water meter (水道メーター)."
ln infra:water_meter concept:utility thesaurus:related
ln infra:water_meter home:garden home:located_in
ln infra:water_meter obj:durable obj_durability
def "infra:gas_meter" "Gas meter (ガスメーター)."
ln infra:gas_meter concept:utility thesaurus:related
ln infra:gas_meter home:garden home:located_in
ln infra:gas_meter obj:durable obj_durability
def "infra:electricity_meter" "Electricity meter (電力量計)."
ln infra:electricity_meter concept:utility thesaurus:related
ln infra:electricity_meter home:garden home:located_in
ln infra:electricity_meter obj:durable obj_durability
def "infra:gas_line" "Gas line (ガス管)."
ln infra:gas_line concept:utility thesaurus:related
ln infra:gas_line home:kitchen home:located_in
ln infra:gas_line obj:durable obj_durability
def "infra:water_pipe" "Water pipe (水道管)."
ln infra:water_pipe concept:utility thesaurus:related
ln infra:water_pipe home:kitchen home:located_in
ln infra:water_pipe obj:durable obj_durability
def "infra:drain" "Drain (排水管)."
ln infra:drain concept:utility thesaurus:related
ln infra:drain home:bathroom home:located_in
ln infra:drain obj:durable obj_durability
def "infra:router" "Router (ルーター)."
ln infra:router concept:utility thesaurus:related
ln infra:router home:living_room home:located_in
ln infra:router obj:durable obj_durability
def "infra:antenna" "Antenna (アンテナ)."
ln infra:antenna concept:utility thesaurus:related
ln infra:antenna obj:durable obj_durability

# ── appliances powered/fed by utilities ──
ln appliance:refrigerator infra:electricity_supply infra:powered_by
ln appliance:television infra:electricity_supply infra:powered_by
ln appliance:washing_machine infra:electricity_supply infra:powered_by
ln appliance:washing_machine infra:water_supply infra:powered_by
ln appliance:stove infra:gas_supply infra:powered_by
ln appliance:water_heater infra:gas_supply infra:powered_by
ln home:kitchen_sink infra:water_supply infra:powered_by
ln home:faucet infra:water_supply infra:delivered_via
ln appliance:air_conditioner infra:electricity_supply infra:powered_by

# ── broadcasting (放送) ──
def "broadcast" "Transmission of audio/video to the public."
def "broadcast_type:television" "TV broadcasting"
def "broadcast_type:radio" "radio broadcasting"
def "broadcast_type:community" "local community broadcasting"
def "broadcast_type:cable" "cable distribution"
def "broadcast_type:satellite" "satellite broadcasting"
def "broadcast_type:emergency" "emergency/disaster broadcasting"
def "appliance:radio" "Radio (ラジオ)."
ln appliance:radio appliance thesaurus:related
ln appliance:radio home:living_room home:located_in
ln appliance:radio obj:durable obj_durability
ln appliance:radio infra:electricity_supply infra:powered_by

def "broadcast:public_broadcaster" "Public broadcaster (公共放送)."
ln broadcast:public_broadcaster broadcast_type:television broadcast:mode
ln broadcast:public_broadcaster broadcast_type:radio broadcast:mode
ln broadcast:public_broadcaster appliance:television broadcast:received_by
ln broadcast:public_broadcaster appliance:radio broadcast:received_by
def "broadcast:commercial_broadcaster" "Commercial broadcaster (民間放送)."
ln broadcast:commercial_broadcaster broadcast_type:television broadcast:mode
ln broadcast:commercial_broadcaster broadcast_type:radio broadcast:mode
ln broadcast:commercial_broadcaster appliance:television broadcast:received_by
ln broadcast:commercial_broadcaster appliance:radio broadcast:received_by
def "broadcast:community_radio" "Community radio (コミュニティFM)."
ln broadcast:community_radio broadcast_type:radio broadcast:mode
ln broadcast:community_radio broadcast_type:community broadcast:mode
ln broadcast:community_radio appliance:radio broadcast:received_by
def "broadcast:cable_tv" "Cable tv (ケーブルテレビ)."
ln broadcast:cable_tv broadcast_type:television broadcast:mode
ln broadcast:cable_tv broadcast_type:cable broadcast:mode
ln broadcast:cable_tv appliance:television broadcast:received_by
def "broadcast:satellite_tv" "Satellite tv."
ln broadcast:satellite_tv broadcast_type:television broadcast:mode
ln broadcast:satellite_tv broadcast_type:satellite broadcast:mode
ln broadcast:satellite_tv appliance:television broadcast:received_by
def "broadcast:emergency_broadcast" "Emergency broadcast (緊急放送)."
ln broadcast:emergency_broadcast broadcast_type:emergency broadcast:mode
ln broadcast:emergency_broadcast broadcast_type:radio broadcast:mode
ln broadcast:emergency_broadcast appliance:radio broadcast:received_by
ln broadcast:emergency_broadcast appliance:television broadcast:received_by
# community radio is local — tie to the community layer
ln broadcast:community_radio concept:community thesaurus:related
ln broadcast:community_radio concept:neighborhood thesaurus:related
ln broadcast:community_radio admin:municipality thesaurus:related
ln broadcast:emergency_broadcast gov:function:emergency_management gov:delivers
ln broadcast:emergency_broadcast gov:emergency_call thesaurus:related
ln broadcast concept:utility thesaurus:related
