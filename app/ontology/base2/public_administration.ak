# Akasha ontology — public administration: government functions & services.
# The service layer missing from admin_hierarchy: police/fire/ambulance,
# welfare, tax, sanitation, parks, public health. Each function is provided by
# an admin level (gov:provided_by), delivered by an agency at a place:*, staffed
# by occupation:*. Base pack.

def "gov" "A function or service of government."
# ── government functions → which admin level provides them ──
def "gov:function:public_safety" "Public safety (公安) — public function."
ln gov:function:public_safety gov thesaurus:related
ln gov:function:public_safety admin:prefecture gov:provided_by
def "gov:function:welfare" "Welfare (福祉) — public function."
ln gov:function:welfare gov thesaurus:related
ln gov:function:welfare admin:municipality gov:provided_by
def "gov:function:taxation" "Taxation (税) — public function."
ln gov:function:taxation gov thesaurus:related
ln gov:function:taxation admin:country gov:provided_by
def "gov:function:sanitation" "Sanitation (清掃/衛生) — public function."
ln gov:function:sanitation gov thesaurus:related
ln gov:function:sanitation admin:municipality gov:provided_by
def "gov:function:public_works" "Public works — public function."
ln gov:function:public_works gov thesaurus:related
ln gov:function:public_works admin:municipality gov:provided_by
def "gov:function:parks_recreation" "Parks recreation (公園緑地) — public function."
ln gov:function:parks_recreation gov thesaurus:related
ln gov:function:parks_recreation admin:municipality gov:provided_by
def "gov:function:public_health" "Public health (公衆衛生) — public function."
ln gov:function:public_health gov thesaurus:related
ln gov:function:public_health admin:prefecture gov:provided_by
def "gov:function:education" "Education — public function."
ln gov:function:education gov thesaurus:related
ln gov:function:education admin:municipality gov:provided_by
def "gov:function:civil_registry" "Civil registry (戸籍/住民登録) — public function."
ln gov:function:civil_registry gov thesaurus:related
ln gov:function:civil_registry admin:municipality gov:provided_by
def "gov:function:urban_planning" "Urban planning — public function."
ln gov:function:urban_planning gov thesaurus:related
ln gov:function:urban_planning admin:municipality gov:provided_by
def "gov:function:emergency_management" "Emergency management (防災) — public function."
ln gov:function:emergency_management gov thesaurus:related
ln gov:function:emergency_management admin:municipality gov:provided_by

# ── new public-service occupations ──
def "occupation:paramedic" "Paramedic (救急救命士)."
ln occupation:paramedic occupation_sector:safety_emergency occupation:sector
ln occupation:paramedic gov thesaurus:related
def "occupation:tax_officer" "Tax officer."
ln occupation:tax_officer occupation_sector:public_civil occupation:sector
ln occupation:tax_officer gov thesaurus:related
def "occupation:social_worker" "Social worker (ケースワーカー)."
ln occupation:social_worker occupation_sector:public_civil occupation:sector
ln occupation:social_worker gov thesaurus:related
def "occupation:sanitation_worker" "Sanitation worker."
ln occupation:sanitation_worker occupation_sector:public_civil occupation:sector
ln occupation:sanitation_worker gov thesaurus:related

# ── agencies / services → function, place, staff ──
def "gov:service:police" "Police (警察)."
ln gov:service:police gov:function:public_safety gov:delivers
ln gov:service:police place:police_station gov:based_at
ln occupation:police_officer gov:service:police gov:works_for
def "gov:service:fire_service" "Fire service (消防)."
ln gov:service:fire_service gov:function:public_safety gov:delivers
ln gov:service:fire_service place:fire_station gov:based_at
ln occupation:firefighter gov:service:fire_service gov:works_for
def "gov:service:ambulance_service" "Ambulance service (救急)."
ln gov:service:ambulance_service gov:function:emergency_management gov:delivers
ln gov:service:ambulance_service place:hospital gov:based_at
ln occupation:paramedic gov:service:ambulance_service gov:works_for
def "gov:service:welfare_office" "Welfare office (福祉事務所)."
ln gov:service:welfare_office gov:function:welfare gov:delivers
ln gov:service:welfare_office place:city_hall gov:based_at
ln occupation:social_worker gov:service:welfare_office gov:works_for
def "gov:service:tax_office" "Tax office (税務署)."
ln gov:service:tax_office gov:function:taxation gov:delivers
ln occupation:tax_officer gov:service:tax_office gov:works_for
def "gov:service:sanitation_service" "Sanitation service."
ln gov:service:sanitation_service gov:function:sanitation gov:delivers
ln occupation:sanitation_worker gov:service:sanitation_service gov:works_for
def "gov:service:parks_department" "Parks department."
ln gov:service:parks_department gov:function:parks_recreation gov:delivers
ln gov:service:parks_department place:park gov:based_at
def "gov:service:health_department" "Health department."
ln gov:service:health_department gov:function:public_health gov:delivers
ln gov:service:health_department place:hospital gov:based_at
def "gov:service:registry_office" "Registry office."
ln gov:service:registry_office gov:function:civil_registry gov:delivers
ln gov:service:registry_office place:city_hall gov:based_at
ln occupation:clerk gov:service:registry_office gov:works_for
def "gov:service:public_works_dept" "Public works dept."
ln gov:service:public_works_dept gov:function:public_works gov:delivers
def "place:tax_office" "Tax office (税務署) — civic institution."
ln place:tax_office place_type:civic civic:function
ln gov:service:tax_office place:tax_office gov:based_at

# ── emergency services ──
def "transport:ambulance" "Ambulance (救急車)."
def "transport:fire_engine" "Fire engine (消防車)."
def "transport:police_car" "Police car (パトカー)."
ln transport:ambulance transport thesaurus:related
ln transport:fire_engine transport thesaurus:related
ln transport:police_car transport thesaurus:related
ln transport:ambulance gov:service:ambulance_service gov:used_by
ln transport:fire_engine gov:service:fire_service gov:used_by
ln transport:police_car gov:service:police gov:used_by
def "place:emergency_room" "Emergency room (救急外来) — hospital emergency department."
ln place:emergency_room place_type:health civic:function
ln place:emergency_room place:hospital home:located_in
def "gov:emergency_call" "Emergency call (緊急通報(110/119)) — the emergency phone number."
ln gov:emergency_call gov:service:police gov:reaches
ln gov:emergency_call gov:service:fire_service gov:reaches
ln gov:emergency_call gov:service:ambulance_service gov:reaches

# ── welfare benefits ──
def "gov:benefit" "A welfare benefit or public assistance."
def "gov:benefit:pension" "Pension (年金) — old-age pension."
ln gov:benefit:pension gov:benefit thesaurus:related
ln gov:benefit:pension gov:function:welfare gov:delivers
def "gov:benefit:social_security" "Social security — social insurance."
ln gov:benefit:social_security gov:benefit thesaurus:related
ln gov:benefit:social_security gov:function:welfare gov:delivers
def "gov:benefit:public_assistance" "Public assistance (生活保護) — minimum-income support."
ln gov:benefit:public_assistance gov:benefit thesaurus:related
ln gov:benefit:public_assistance gov:function:welfare gov:delivers
def "gov:benefit:child_allowance" "Child allowance (児童手当) — support for families with children."
ln gov:benefit:child_allowance gov:benefit thesaurus:related
ln gov:benefit:child_allowance gov:function:welfare gov:delivers
def "gov:benefit:disability_benefit" "Disability benefit — support for disabled persons."
ln gov:benefit:disability_benefit gov:benefit thesaurus:related
ln gov:benefit:disability_benefit gov:function:welfare gov:delivers
def "gov:benefit:unemployment_benefit" "Unemployment benefit — support while jobless."
ln gov:benefit:unemployment_benefit gov:benefit thesaurus:related
ln gov:benefit:unemployment_benefit gov:function:welfare gov:delivers
ln gov:function:welfare place:nursing_home gov:based_at
ln social:caregiver_of gov:function:welfare thesaurus:related

# ── taxes ──
def "gov:tax" "A tax levied by government."
def "gov:tax:income_tax" "Income tax (所得税) — tax on income."
ln gov:tax:income_tax gov:tax thesaurus:related
ln gov:tax:income_tax gov:function:taxation gov:delivers
def "gov:tax:property_tax" "Property tax (固定資産税) — tax on property."
ln gov:tax:property_tax gov:tax thesaurus:related
ln gov:tax:property_tax gov:function:taxation gov:delivers
def "gov:tax:consumption_tax" "Consumption tax (消費税) — sales/consumption tax."
ln gov:tax:consumption_tax gov:tax thesaurus:related
ln gov:tax:consumption_tax gov:function:taxation gov:delivers
def "gov:tax:corporate_tax" "Corporate tax — tax on companies."
ln gov:tax:corporate_tax gov:tax thesaurus:related
ln gov:tax:corporate_tax gov:function:taxation gov:delivers
def "gov:tax:inheritance_tax" "Inheritance tax — tax on inheritance."
ln gov:tax:inheritance_tax gov:tax thesaurus:related
ln gov:tax:inheritance_tax gov:function:taxation gov:delivers
def "gov:tax:resident_tax" "Resident tax — local resident tax."
ln gov:tax:resident_tax gov:tax thesaurus:related
ln gov:tax:resident_tax gov:function:taxation gov:delivers
def "gov:tax_return" "A filed statement of taxable income (確定申告)."
ln gov:tax_return gov:function:taxation gov:delivers
ln civ:resident gov:tax:resident_tax gov:pays

# ── sanitation ──
def "gov:sanitation:garbage_collection" "Garbage collection (ゴミ収集) — household waste collection."
ln gov:sanitation:garbage_collection gov:function:sanitation gov:delivers
def "gov:sanitation:recycling" "Recycling — sorting & reuse of materials."
ln gov:sanitation:recycling gov:function:sanitation gov:delivers
def "gov:sanitation:waste_disposal" "Waste disposal — disposal of refuse."
ln gov:sanitation:waste_disposal gov:function:sanitation gov:delivers
def "gov:sanitation:street_cleaning" "Street cleaning — cleaning of public streets."
ln gov:sanitation:street_cleaning gov:function:sanitation gov:delivers

# ── parks & green space ──
def "green_space" "Public green / open space."
def "place:city_park" "City park — a municipal park."
ln place:city_park green_space thesaurus:related
ln place:city_park gov:function:parks_recreation gov:provided_by
def "place:botanical_garden" "Botanical garden — a curated plant garden."
ln place:botanical_garden green_space thesaurus:related
ln place:botanical_garden gov:function:parks_recreation gov:provided_by
def "place:plaza" "Plaza — a public square."
ln place:plaza green_space thesaurus:related
ln place:plaza gov:function:parks_recreation gov:provided_by
def "place:street_tree" "Street tree (街路樹) — a tree lining a street."
ln place:street_tree green_space thesaurus:related
ln place:street_tree gov:function:parks_recreation gov:provided_by
def "place:green_belt" "Green belt — protected greenery."
ln place:green_belt green_space thesaurus:related
ln place:green_belt gov:function:parks_recreation gov:provided_by
def "place:public_toilet" "Public toilet — a public lavatory."
ln place:public_toilet green_space thesaurus:related
ln place:public_toilet gov:function:parks_recreation gov:provided_by
ln place:park green_space thesaurus:related
ln place:playground green_space thesaurus:related
ln place:street_tree place_type:recreation civic:function
