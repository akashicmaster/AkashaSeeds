# Akasha ontology — geopolitical organisations and memberships
# Design note: atoms have no intrinsic meaning; membership (set inclusion) and
# directed links (geo:member_of) together constitute the concept.
# From any country atom follow geo:member_of to reach all its organisations.
# From any org atom query the corresponding set to list all member states.
# atoms: 18

# ── Relation ───────────────────────────────────────────────────────────────────

def "geo:member_of" "A state holds formal membership in a geopolitical, economic or security organisation."
ln geo:member_of ont.geo sys:part_of

# ── United Nations ─────────────────────────────────────────────────────────────

def "geo:org:UN" "United Nations — intergovernmental organisation founded 1945; 193 member states."
set.add name="set:geo:un" id="geo:country:ARG"
set.add name="set:geo:un" id="geo:country:AUS"
set.add name="set:geo:un" id="geo:country:BRA"
set.add name="set:geo:un" id="geo:country:CAN"
set.add name="set:geo:un" id="geo:country:CHN"
set.add name="set:geo:un" id="geo:country:DEU"
set.add name="set:geo:un" id="geo:country:FRA"
set.add name="set:geo:un" id="geo:country:GBR"
set.add name="set:geo:un" id="geo:country:IND"
set.add name="set:geo:un" id="geo:country:IDN"
set.add name="set:geo:un" id="geo:country:ITA"
set.add name="set:geo:un" id="geo:country:JPN"
set.add name="set:geo:un" id="geo:country:KOR"
set.add name="set:geo:un" id="geo:country:MEX"
set.add name="set:geo:un" id="geo:country:RUS"
set.add name="set:geo:un" id="geo:country:SAU"
set.add name="set:geo:un" id="geo:country:ZAF"
set.add name="set:geo:un" id="geo:country:TUR"
set.add name="set:geo:un" id="geo:country:USA"
set.add name="set:geo:un" id="geo:country:EGY"
set.add name="set:geo:un" id="geo:country:NGA"
set.add name="set:geo:un" id="geo:country:ETH"
set.add name="set:geo:un" id="geo:country:IRN"
set.add name="set:geo:un" id="geo:country:PAK"
set.add name="set:geo:un" id="geo:country:THA"
set.add name="set:geo:un" id="geo:country:VNM"
set.add name="set:geo:un" id="geo:country:PHL"
set.add name="set:geo:un" id="geo:country:ESP"
set.add name="set:geo:un" id="geo:country:POL"
set.add name="set:geo:un" id="geo:country:NLD"
set.add name="set:geo:un" id="geo:country:UKR"
set.add name="set:geo:un" id="geo:country:COL"
set.add name="set:geo:un" id="geo:country:CHL"
set.add name="set:geo:un" id="geo:country:NZL"
set.add name="set:geo:un" id="geo:country:ARE"
set.add name="set:geo:un" id="geo:country:SGP"
set.add name="set:geo:un" id="geo:country:SWE"
set.add name="set:geo:un" id="geo:country:NOR"
set.add name="set:geo:un" id="geo:country:CHE"
set.add name="set:geo:un" id="geo:country:ISR"
set.add name="set:geo:un" id="geo:country:KEN"
set.add name="set:geo:un" id="geo:country:MAR"
set.add name="set:geo:un" id="geo:country:PER"
ln geo:country:ARG geo:org:UN geo:member_of
ln geo:country:AUS geo:org:UN geo:member_of
ln geo:country:BRA geo:org:UN geo:member_of
ln geo:country:CAN geo:org:UN geo:member_of
ln geo:country:CHN geo:org:UN geo:member_of
ln geo:country:DEU geo:org:UN geo:member_of
ln geo:country:FRA geo:org:UN geo:member_of
ln geo:country:GBR geo:org:UN geo:member_of
ln geo:country:IND geo:org:UN geo:member_of
ln geo:country:IDN geo:org:UN geo:member_of
ln geo:country:ITA geo:org:UN geo:member_of
ln geo:country:JPN geo:org:UN geo:member_of
ln geo:country:KOR geo:org:UN geo:member_of
ln geo:country:MEX geo:org:UN geo:member_of
ln geo:country:RUS geo:org:UN geo:member_of
ln geo:country:SAU geo:org:UN geo:member_of
ln geo:country:ZAF geo:org:UN geo:member_of
ln geo:country:TUR geo:org:UN geo:member_of
ln geo:country:USA geo:org:UN geo:member_of
ln geo:country:EGY geo:org:UN geo:member_of
ln geo:country:NGA geo:org:UN geo:member_of
ln geo:country:ETH geo:org:UN geo:member_of
ln geo:country:IRN geo:org:UN geo:member_of
ln geo:country:PAK geo:org:UN geo:member_of
ln geo:country:THA geo:org:UN geo:member_of
ln geo:country:VNM geo:org:UN geo:member_of
ln geo:country:PHL geo:org:UN geo:member_of
ln geo:country:ESP geo:org:UN geo:member_of
ln geo:country:POL geo:org:UN geo:member_of
ln geo:country:NLD geo:org:UN geo:member_of
ln geo:country:UKR geo:org:UN geo:member_of
ln geo:country:COL geo:org:UN geo:member_of
ln geo:country:CHL geo:org:UN geo:member_of
ln geo:country:NZL geo:org:UN geo:member_of
ln geo:country:ARE geo:org:UN geo:member_of
ln geo:country:SGP geo:org:UN geo:member_of
ln geo:country:SWE geo:org:UN geo:member_of
ln geo:country:NOR geo:org:UN geo:member_of
ln geo:country:CHE geo:org:UN geo:member_of
ln geo:country:ISR geo:org:UN geo:member_of
ln geo:country:KEN geo:org:UN geo:member_of
ln geo:country:MAR geo:org:UN geo:member_of
ln geo:country:PER geo:org:UN geo:member_of

# ── UN Security Council — Permanent 5 ─────────────────────────────────────────

def "geo:org:UN_P5" "UN Security Council permanent members — veto-holding powers."
set.add name="set:geo:un:p5" id="geo:country:CHN"
set.add name="set:geo:un:p5" id="geo:country:FRA"
set.add name="set:geo:un:p5" id="geo:country:RUS"
set.add name="set:geo:un:p5" id="geo:country:GBR"
set.add name="set:geo:un:p5" id="geo:country:USA"
ln geo:country:CHN geo:org:UN_P5 geo:member_of
ln geo:country:FRA geo:org:UN_P5 geo:member_of
ln geo:country:RUS geo:org:UN_P5 geo:member_of
ln geo:country:GBR geo:org:UN_P5 geo:member_of
ln geo:country:USA geo:org:UN_P5 geo:member_of

# ── G7 ────────────────────────────────────────────────────────────────────────

def "geo:org:G7" "G7 — Group of Seven leading industrialised democracies."
set.add name="set:geo:g7" id="geo:country:CAN"
set.add name="set:geo:g7" id="geo:country:FRA"
set.add name="set:geo:g7" id="geo:country:DEU"
set.add name="set:geo:g7" id="geo:country:ITA"
set.add name="set:geo:g7" id="geo:country:JPN"
set.add name="set:geo:g7" id="geo:country:GBR"
set.add name="set:geo:g7" id="geo:country:USA"
ln geo:country:CAN geo:org:G7 geo:member_of
ln geo:country:FRA geo:org:G7 geo:member_of
ln geo:country:DEU geo:org:G7 geo:member_of
ln geo:country:ITA geo:org:G7 geo:member_of
ln geo:country:JPN geo:org:G7 geo:member_of
ln geo:country:GBR geo:org:G7 geo:member_of
ln geo:country:USA geo:org:G7 geo:member_of

# ── G20 ───────────────────────────────────────────────────────────────────────

def "geo:org:G20" "G20 — Group of Twenty: major economies representing around 85% of world GDP."
set.add name="set:geo:g20" id="geo:country:ARG"
set.add name="set:geo:g20" id="geo:country:AUS"
set.add name="set:geo:g20" id="geo:country:BRA"
set.add name="set:geo:g20" id="geo:country:CAN"
set.add name="set:geo:g20" id="geo:country:CHN"
set.add name="set:geo:g20" id="geo:country:DEU"
set.add name="set:geo:g20" id="geo:country:FRA"
set.add name="set:geo:g20" id="geo:country:GBR"
set.add name="set:geo:g20" id="geo:country:IND"
set.add name="set:geo:g20" id="geo:country:IDN"
set.add name="set:geo:g20" id="geo:country:ITA"
set.add name="set:geo:g20" id="geo:country:JPN"
set.add name="set:geo:g20" id="geo:country:KOR"
set.add name="set:geo:g20" id="geo:country:MEX"
set.add name="set:geo:g20" id="geo:country:RUS"
set.add name="set:geo:g20" id="geo:country:SAU"
set.add name="set:geo:g20" id="geo:country:ZAF"
set.add name="set:geo:g20" id="geo:country:TUR"
set.add name="set:geo:g20" id="geo:country:USA"
ln geo:country:ARG geo:org:G20 geo:member_of
ln geo:country:AUS geo:org:G20 geo:member_of
ln geo:country:BRA geo:org:G20 geo:member_of
ln geo:country:CAN geo:org:G20 geo:member_of
ln geo:country:CHN geo:org:G20 geo:member_of
ln geo:country:DEU geo:org:G20 geo:member_of
ln geo:country:FRA geo:org:G20 geo:member_of
ln geo:country:GBR geo:org:G20 geo:member_of
ln geo:country:IND geo:org:G20 geo:member_of
ln geo:country:IDN geo:org:G20 geo:member_of
ln geo:country:ITA geo:org:G20 geo:member_of
ln geo:country:JPN geo:org:G20 geo:member_of
ln geo:country:KOR geo:org:G20 geo:member_of
ln geo:country:MEX geo:org:G20 geo:member_of
ln geo:country:RUS geo:org:G20 geo:member_of
ln geo:country:SAU geo:org:G20 geo:member_of
ln geo:country:ZAF geo:org:G20 geo:member_of
ln geo:country:TUR geo:org:G20 geo:member_of
ln geo:country:USA geo:org:G20 geo:member_of

# ── NATO ──────────────────────────────────────────────────────────────────────

def "geo:org:NATO" "NATO — North Atlantic Treaty Organization; collective defence alliance."
set.add name="set:geo:nato" id="geo:country:CAN"
set.add name="set:geo:nato" id="geo:country:USA"
set.add name="set:geo:nato" id="geo:country:GBR"
set.add name="set:geo:nato" id="geo:country:FRA"
set.add name="set:geo:nato" id="geo:country:DEU"
set.add name="set:geo:nato" id="geo:country:ITA"
set.add name="set:geo:nato" id="geo:country:NLD"
set.add name="set:geo:nato" id="geo:country:ESP"
set.add name="set:geo:nato" id="geo:country:POL"
set.add name="set:geo:nato" id="geo:country:NOR"
set.add name="set:geo:nato" id="geo:country:TUR"
set.add name="set:geo:nato" id="geo:country:SWE"
ln geo:country:CAN geo:org:NATO geo:member_of
ln geo:country:USA geo:org:NATO geo:member_of
ln geo:country:GBR geo:org:NATO geo:member_of
ln geo:country:FRA geo:org:NATO geo:member_of
ln geo:country:DEU geo:org:NATO geo:member_of
ln geo:country:ITA geo:org:NATO geo:member_of
ln geo:country:NLD geo:org:NATO geo:member_of
ln geo:country:ESP geo:org:NATO geo:member_of
ln geo:country:POL geo:org:NATO geo:member_of
ln geo:country:NOR geo:org:NATO geo:member_of
ln geo:country:TUR geo:org:NATO geo:member_of
ln geo:country:SWE geo:org:NATO geo:member_of

# ── European Union ────────────────────────────────────────────────────────────

def "geo:org:EU" "European Union — political and economic union of 27 member states."
set.add name="set:geo:eu" id="geo:country:DEU"
set.add name="set:geo:eu" id="geo:country:FRA"
set.add name="set:geo:eu" id="geo:country:ITA"
set.add name="set:geo:eu" id="geo:country:NLD"
set.add name="set:geo:eu" id="geo:country:ESP"
set.add name="set:geo:eu" id="geo:country:POL"
set.add name="set:geo:eu" id="geo:country:SWE"
ln geo:country:DEU geo:org:EU geo:member_of
ln geo:country:FRA geo:org:EU geo:member_of
ln geo:country:ITA geo:org:EU geo:member_of
ln geo:country:NLD geo:org:EU geo:member_of
ln geo:country:ESP geo:org:EU geo:member_of
ln geo:country:POL geo:org:EU geo:member_of
ln geo:country:SWE geo:org:EU geo:member_of

# ── ASEAN ─────────────────────────────────────────────────────────────────────

def "geo:org:ASEAN" "ASEAN — Association of Southeast Asian Nations; 10-member regional bloc."
set.add name="set:geo:asean" id="geo:country:IDN"
set.add name="set:geo:asean" id="geo:country:THA"
set.add name="set:geo:asean" id="geo:country:VNM"
set.add name="set:geo:asean" id="geo:country:PHL"
set.add name="set:geo:asean" id="geo:country:SGP"
ln geo:country:IDN geo:org:ASEAN geo:member_of
ln geo:country:THA geo:org:ASEAN geo:member_of
ln geo:country:VNM geo:org:ASEAN geo:member_of
ln geo:country:PHL geo:org:ASEAN geo:member_of
ln geo:country:SGP geo:org:ASEAN geo:member_of

# ── Arab League ───────────────────────────────────────────────────────────────

def "geo:org:ARAB_LEAGUE" "Arab League — League of Arab States; 22 member states sharing Arabic language and culture."
set.add name="set:geo:arab_league" id="geo:country:EGY"
set.add name="set:geo:arab_league" id="geo:country:SAU"
set.add name="set:geo:arab_league" id="geo:country:ARE"
set.add name="set:geo:arab_league" id="geo:country:MAR"
ln geo:country:EGY geo:org:ARAB_LEAGUE geo:member_of
ln geo:country:SAU geo:org:ARAB_LEAGUE geo:member_of
ln geo:country:ARE geo:org:ARAB_LEAGUE geo:member_of
ln geo:country:MAR geo:org:ARAB_LEAGUE geo:member_of

# ── African Union ─────────────────────────────────────────────────────────────

def "geo:org:AFRICAN_UNION" "African Union — continental body of 55 member states of Africa."
set.add name="set:geo:african_union" id="geo:country:NGA"
set.add name="set:geo:african_union" id="geo:country:EGY"
set.add name="set:geo:african_union" id="geo:country:ETH"
set.add name="set:geo:african_union" id="geo:country:ZAF"
set.add name="set:geo:african_union" id="geo:country:KEN"
set.add name="set:geo:african_union" id="geo:country:MAR"
ln geo:country:NGA geo:org:AFRICAN_UNION geo:member_of
ln geo:country:EGY geo:org:AFRICAN_UNION geo:member_of
ln geo:country:ETH geo:org:AFRICAN_UNION geo:member_of
ln geo:country:ZAF geo:org:AFRICAN_UNION geo:member_of
ln geo:country:KEN geo:org:AFRICAN_UNION geo:member_of
ln geo:country:MAR geo:org:AFRICAN_UNION geo:member_of

# ── Commonwealth of Nations ───────────────────────────────────────────────────

def "geo:org:COMMONWEALTH" "Commonwealth of Nations — 56 member states, mostly former territories of the British Empire."
set.add name="set:geo:commonwealth" id="geo:country:AUS"
set.add name="set:geo:commonwealth" id="geo:country:CAN"
set.add name="set:geo:commonwealth" id="geo:country:GBR"
set.add name="set:geo:commonwealth" id="geo:country:IND"
set.add name="set:geo:commonwealth" id="geo:country:NGA"
set.add name="set:geo:commonwealth" id="geo:country:NZL"
set.add name="set:geo:commonwealth" id="geo:country:ZAF"
set.add name="set:geo:commonwealth" id="geo:country:PAK"
set.add name="set:geo:commonwealth" id="geo:country:SGP"
set.add name="set:geo:commonwealth" id="geo:country:KEN"
ln geo:country:AUS geo:org:COMMONWEALTH geo:member_of
ln geo:country:CAN geo:org:COMMONWEALTH geo:member_of
ln geo:country:GBR geo:org:COMMONWEALTH geo:member_of
ln geo:country:IND geo:org:COMMONWEALTH geo:member_of
ln geo:country:NGA geo:org:COMMONWEALTH geo:member_of
ln geo:country:NZL geo:org:COMMONWEALTH geo:member_of
ln geo:country:ZAF geo:org:COMMONWEALTH geo:member_of
ln geo:country:PAK geo:org:COMMONWEALTH geo:member_of
ln geo:country:SGP geo:org:COMMONWEALTH geo:member_of
ln geo:country:KEN geo:org:COMMONWEALTH geo:member_of

# ── BRICS ─────────────────────────────────────────────────────────────────────

def "geo:org:BRICS" "BRICS — major emerging economies; expanded 2024 to include Egypt, Ethiopia, Iran and UAE."
set.add name="set:geo:brics" id="geo:country:BRA"
set.add name="set:geo:brics" id="geo:country:RUS"
set.add name="set:geo:brics" id="geo:country:IND"
set.add name="set:geo:brics" id="geo:country:CHN"
set.add name="set:geo:brics" id="geo:country:ZAF"
set.add name="set:geo:brics" id="geo:country:EGY"
set.add name="set:geo:brics" id="geo:country:ETH"
set.add name="set:geo:brics" id="geo:country:IRN"
set.add name="set:geo:brics" id="geo:country:ARE"
ln geo:country:BRA geo:org:BRICS geo:member_of
ln geo:country:RUS geo:org:BRICS geo:member_of
ln geo:country:IND geo:org:BRICS geo:member_of
ln geo:country:CHN geo:org:BRICS geo:member_of
ln geo:country:ZAF geo:org:BRICS geo:member_of
ln geo:country:EGY geo:org:BRICS geo:member_of
ln geo:country:ETH geo:org:BRICS geo:member_of
ln geo:country:IRN geo:org:BRICS geo:member_of
ln geo:country:ARE geo:org:BRICS geo:member_of

# ── OPEC ──────────────────────────────────────────────────────────────────────

def "geo:org:OPEC" "OPEC — Organization of the Petroleum Exporting Countries; coordinates petroleum policies."
set.add name="set:geo:opec" id="geo:country:SAU"
set.add name="set:geo:opec" id="geo:country:IRN"
set.add name="set:geo:opec" id="geo:country:ARE"
set.add name="set:geo:opec" id="geo:country:NGA"
ln geo:country:SAU geo:org:OPEC geo:member_of
ln geo:country:IRN geo:org:OPEC geo:member_of
ln geo:country:ARE geo:org:OPEC geo:member_of
ln geo:country:NGA geo:org:OPEC geo:member_of

# ── SCO ───────────────────────────────────────────────────────────────────────

def "geo:org:SCO" "Shanghai Cooperation Organisation — Eurasian political, economic and security alliance."
set.add name="set:geo:sco" id="geo:country:CHN"
set.add name="set:geo:sco" id="geo:country:RUS"
set.add name="set:geo:sco" id="geo:country:IND"
set.add name="set:geo:sco" id="geo:country:PAK"
set.add name="set:geo:sco" id="geo:country:IRN"
ln geo:country:CHN geo:org:SCO geo:member_of
ln geo:country:RUS geo:org:SCO geo:member_of
ln geo:country:IND geo:org:SCO geo:member_of
ln geo:country:PAK geo:org:SCO geo:member_of
ln geo:country:IRN geo:org:SCO geo:member_of

# ── OECD ──────────────────────────────────────────────────────────────────────

def "geo:org:OECD" "OECD — Organisation for Economic Co-operation and Development; 38 high-income market economies."
set.add name="set:geo:oecd" id="geo:country:AUS"
set.add name="set:geo:oecd" id="geo:country:CAN"
set.add name="set:geo:oecd" id="geo:country:CHL"
set.add name="set:geo:oecd" id="geo:country:COL"
set.add name="set:geo:oecd" id="geo:country:DEU"
set.add name="set:geo:oecd" id="geo:country:ESP"
set.add name="set:geo:oecd" id="geo:country:FRA"
set.add name="set:geo:oecd" id="geo:country:GBR"
set.add name="set:geo:oecd" id="geo:country:ISR"
set.add name="set:geo:oecd" id="geo:country:ITA"
set.add name="set:geo:oecd" id="geo:country:JPN"
set.add name="set:geo:oecd" id="geo:country:KOR"
set.add name="set:geo:oecd" id="geo:country:MEX"
set.add name="set:geo:oecd" id="geo:country:NLD"
set.add name="set:geo:oecd" id="geo:country:NOR"
set.add name="set:geo:oecd" id="geo:country:NZL"
set.add name="set:geo:oecd" id="geo:country:POL"
set.add name="set:geo:oecd" id="geo:country:SWE"
set.add name="set:geo:oecd" id="geo:country:CHE"
set.add name="set:geo:oecd" id="geo:country:TUR"
set.add name="set:geo:oecd" id="geo:country:USA"
ln geo:country:AUS geo:org:OECD geo:member_of
ln geo:country:CAN geo:org:OECD geo:member_of
ln geo:country:CHL geo:org:OECD geo:member_of
ln geo:country:COL geo:org:OECD geo:member_of
ln geo:country:DEU geo:org:OECD geo:member_of
ln geo:country:ESP geo:org:OECD geo:member_of
ln geo:country:FRA geo:org:OECD geo:member_of
ln geo:country:GBR geo:org:OECD geo:member_of
ln geo:country:ISR geo:org:OECD geo:member_of
ln geo:country:ITA geo:org:OECD geo:member_of
ln geo:country:JPN geo:org:OECD geo:member_of
ln geo:country:KOR geo:org:OECD geo:member_of
ln geo:country:MEX geo:org:OECD geo:member_of
ln geo:country:NLD geo:org:OECD geo:member_of
ln geo:country:NOR geo:org:OECD geo:member_of
ln geo:country:NZL geo:org:OECD geo:member_of
ln geo:country:POL geo:org:OECD geo:member_of
ln geo:country:SWE geo:org:OECD geo:member_of
ln geo:country:CHE geo:org:OECD geo:member_of
ln geo:country:TUR geo:org:OECD geo:member_of
ln geo:country:USA geo:org:OECD geo:member_of

# ── CPTPP ─────────────────────────────────────────────────────────────────────

def "geo:org:CPTPP" "CPTPP — Comprehensive and Progressive Agreement for Trans-Pacific Partnership."
set.add name="set:geo:cptpp" id="geo:country:AUS"
set.add name="set:geo:cptpp" id="geo:country:CAN"
set.add name="set:geo:cptpp" id="geo:country:CHL"
set.add name="set:geo:cptpp" id="geo:country:GBR"
set.add name="set:geo:cptpp" id="geo:country:JPN"
set.add name="set:geo:cptpp" id="geo:country:MEX"
set.add name="set:geo:cptpp" id="geo:country:NZL"
set.add name="set:geo:cptpp" id="geo:country:PER"
set.add name="set:geo:cptpp" id="geo:country:SGP"
set.add name="set:geo:cptpp" id="geo:country:VNM"
ln geo:country:AUS geo:org:CPTPP geo:member_of
ln geo:country:CAN geo:org:CPTPP geo:member_of
ln geo:country:CHL geo:org:CPTPP geo:member_of
ln geo:country:GBR geo:org:CPTPP geo:member_of
ln geo:country:JPN geo:org:CPTPP geo:member_of
ln geo:country:MEX geo:org:CPTPP geo:member_of
ln geo:country:NZL geo:org:CPTPP geo:member_of
ln geo:country:PER geo:org:CPTPP geo:member_of
ln geo:country:SGP geo:org:CPTPP geo:member_of
ln geo:country:VNM geo:org:CPTPP geo:member_of

# ── Quad ──────────────────────────────────────────────────────────────────────

def "geo:org:QUAD" "Quad — Quadrilateral Security Dialogue; strategic security forum in the Indo-Pacific."
set.add name="set:geo:quad" id="geo:country:USA"
set.add name="set:geo:quad" id="geo:country:JPN"
set.add name="set:geo:quad" id="geo:country:IND"
set.add name="set:geo:quad" id="geo:country:AUS"
ln geo:country:USA geo:org:QUAD geo:member_of
ln geo:country:JPN geo:org:QUAD geo:member_of
ln geo:country:IND geo:org:QUAD geo:member_of
ln geo:country:AUS geo:org:QUAD geo:member_of

# ── Five Eyes ─────────────────────────────────────────────────────────────────

def "geo:org:FIVE_EYES" "Five Eyes — intelligence alliance sharing signals intelligence."
set.add name="set:geo:five_eyes" id="geo:country:USA"
set.add name="set:geo:five_eyes" id="geo:country:GBR"
set.add name="set:geo:five_eyes" id="geo:country:CAN"
set.add name="set:geo:five_eyes" id="geo:country:AUS"
set.add name="set:geo:five_eyes" id="geo:country:NZL"
ln geo:country:USA geo:org:FIVE_EYES geo:member_of
ln geo:country:GBR geo:org:FIVE_EYES geo:member_of
ln geo:country:CAN geo:org:FIVE_EYES geo:member_of
ln geo:country:AUS geo:org:FIVE_EYES geo:member_of
ln geo:country:NZL geo:org:FIVE_EYES geo:member_of
