# Akasha ontology — admin: administrative-division TYPE hierarchy.
# The missing ladder between the bottom-up community concepts (neighborhood/
# community/local_society) and the top-down geo:* instances (countries/states/
# capitals). Types carry an admin_scale ordinal and a within/contains chain;
# bottom-up concepts and geo:* instances are both bridged in. Base pack.

def "admin" "An administrative or settlement division."
def "admin:within" "This division lies inside a larger one (child→parent)."
def "admin:contains" "This division contains a smaller one (parent→child)."

# ── division types with scale ──
def "admin:household" "Household (世帯) — admin division (scale 0)."
ln admin:household admin thesaurus:related
ln admin:household admin_scale:0 admin:scale
def "admin:block" "Block (街区) — admin division (scale 1)."
ln admin:block admin thesaurus:related
ln admin:block admin_scale:1 admin:scale
def "admin:neighborhood" "Neighborhood (町内/近隣) — admin division (scale 2)."
ln admin:neighborhood admin thesaurus:related
ln admin:neighborhood admin_scale:2 admin:scale
def "admin:district" "District (地区) — admin division (scale 3)."
ln admin:district admin thesaurus:related
ln admin:district admin_scale:3 admin:scale
def "admin:ward" "Ward (区) — admin division (scale 4)."
ln admin:ward admin thesaurus:related
ln admin:ward admin_scale:4 admin:scale
def "admin:municipality" "Municipality (基礎自治体) — admin division (scale 5)."
ln admin:municipality admin thesaurus:related
ln admin:municipality admin_scale:5 admin:scale
def "admin:city" "City (市) — admin division (scale 5)."
ln admin:city admin thesaurus:related
ln admin:city admin_scale:5 admin:scale
def "admin:town" "Town (町) — admin division (scale 5)."
ln admin:town admin thesaurus:related
ln admin:town admin_scale:5 admin:scale
def "admin:village" "Village (村) — admin division (scale 5)."
ln admin:village admin thesaurus:related
ln admin:village admin_scale:5 admin:scale
def "admin:metropolis" "Metropolis (大都市) — admin division (scale 5)."
ln admin:metropolis admin thesaurus:related
ln admin:metropolis admin_scale:5 admin:scale
def "admin:county" "County (郡) — admin division (scale 6)."
ln admin:county admin thesaurus:related
ln admin:county admin_scale:6 admin:scale
def "admin:prefecture" "Prefecture (県) — admin division (scale 7)."
ln admin:prefecture admin thesaurus:related
ln admin:prefecture admin_scale:7 admin:scale
def "admin:state" "State (州) — admin division (scale 7)."
ln admin:state admin thesaurus:related
ln admin:state admin_scale:7 admin:scale
def "admin:province" "Province (省/州) — admin division (scale 7)."
ln admin:province admin thesaurus:related
ln admin:province admin_scale:7 admin:scale
def "admin:country" "Country (国) — admin division (scale 8)."
ln admin:country admin thesaurus:related
ln admin:country admin_scale:8 admin:scale
def "admin:nation" "Nation (国民国家) — admin division (scale 8)."
ln admin:nation admin thesaurus:related
ln admin:nation admin_scale:8 admin:scale
def "admin:region" "Region (地方/広域) — admin division (scale 9)."
ln admin:region admin thesaurus:related
ln admin:region admin_scale:9 admin:scale
def "admin:continent" "Continent (大陸) — admin division (scale 10)."
ln admin:continent admin thesaurus:related
ln admin:continent admin_scale:10 admin:scale
def "admin:world" "World — admin division (scale 11)."
ln admin:world admin thesaurus:related
ln admin:world admin_scale:11 admin:scale
def "admin:capital" "Capital (首都) — admin division (scale 5)."
ln admin:capital admin thesaurus:related
ln admin:capital admin_scale:5 admin:scale
def "admin_scale:0" "scale level 0."
def "admin_scale:1" "scale level 1."
def "admin_scale:2" "scale level 2."
def "admin_scale:3" "scale level 3."
def "admin_scale:4" "scale level 4."
def "admin_scale:5" "scale level 5."
def "admin_scale:6" "scale level 6."
def "admin_scale:7" "scale level 7."
def "admin_scale:8" "scale level 8."
def "admin_scale:9" "scale level 9."
def "admin_scale:10" "scale level 10."
def "admin_scale:11" "scale level 11."

# ── within / contains ladder ──
ln admin:household admin:block admin:within
ln admin:block admin:household admin:contains
ln admin:block admin:neighborhood admin:within
ln admin:neighborhood admin:block admin:contains
ln admin:neighborhood admin:district admin:within
ln admin:district admin:neighborhood admin:contains
ln admin:district admin:city admin:within
ln admin:city admin:district admin:contains
ln admin:city admin:county admin:within
ln admin:county admin:city admin:contains
ln admin:county admin:prefecture admin:within
ln admin:prefecture admin:county admin:contains
ln admin:prefecture admin:country admin:within
ln admin:country admin:prefecture admin:contains
ln admin:country admin:continent admin:within
ln admin:continent admin:country admin:contains
ln admin:continent admin:world admin:within
ln admin:world admin:continent admin:contains
ln admin:ward admin:city admin:within
ln admin:city admin:ward admin:contains
ln admin:town admin:county admin:within
ln admin:county admin:town admin:contains
ln admin:village admin:county admin:within
ln admin:county admin:village admin:contains
ln admin:metropolis admin:prefecture admin:within
ln admin:prefecture admin:metropolis admin:contains
ln admin:state admin:country admin:within
ln admin:country admin:state admin:contains
ln admin:province admin:country admin:within
ln admin:country admin:province admin:contains
ln admin:nation admin:continent admin:within
ln admin:continent admin:nation admin:contains
ln admin:region admin:continent admin:within
ln admin:continent admin:region admin:contains
ln admin:capital admin:country admin:within
ln admin:country admin:capital admin:contains

# ── municipality kinds & level equivalences ──
ln admin:city admin:municipality admin:kind_of
ln admin:town admin:municipality admin:kind_of
ln admin:village admin:municipality admin:kind_of
ln admin:metropolis admin:municipality admin:kind_of
ln admin:state admin:prefecture thesaurus:related
ln admin:province admin:prefecture thesaurus:related
ln admin:nation admin:country thesaurus:related

# ── bridge: bottom-up community ↔ admin types ──
ln concept:neighborhood admin:neighborhood thesaurus:related
ln concept:community admin:neighborhood thesaurus:related
ln concept:local_society admin:municipality thesaurus:related
ln place:city_hall admin:municipality admin:seat_of
ln civ:resident admin:municipality admin:resident_of
ln social:neighbor_of admin:neighborhood thesaurus:related
ln home:dwelling:detached_house admin:household thesaurus:related
ln occupation:mayor admin:municipality admin:governs
ln occupation:official admin:prefecture admin:governs
ln group:neighborhood_association admin:neighborhood thesaurus:related

# ── bridge: geo:* instances typed into the admin ladder ──
ln geo:capital:ulaanbaatar admin:capital geo:instance_of
ln geo:capital:edinburgh admin:capital geo:instance_of
ln geo:capital:cardiff admin:capital geo:instance_of
ln geo:capital:belfast admin:capital geo:instance_of
ln geo:capital:abu_dhabi admin:capital geo:instance_of
ln geo:capital:addis_ababa admin:capital geo:instance_of
ln geo:capital:amsterdam admin:capital geo:instance_of
ln geo:capital:ankara admin:capital geo:instance_of
ln geo:capital:bern admin:capital geo:instance_of
ln geo:capital:beijing admin:capital geo:instance_of
ln geo:capital:berlin admin:capital geo:instance_of
ln geo:capital:bogota admin:capital geo:instance_of
ln geo:capital:brasilia admin:capital geo:instance_of
ln geo:capital:buenos_aires admin:capital geo:instance_of
ln geo:capital:cairo admin:capital geo:instance_of
ln geo:capital:canberra admin:capital geo:instance_of
ln geo:capital:hanoi admin:capital geo:instance_of
ln geo:capital:islamabad admin:capital geo:instance_of
ln geo:capital:jakarta admin:capital geo:instance_of
ln geo:capital:jerusalem admin:capital geo:instance_of
ln geo:capital:kyiv admin:capital geo:instance_of
ln geo:capital:lima admin:capital geo:instance_of
ln geo:capital:london admin:capital geo:instance_of
ln geo:capital:madrid admin:capital geo:instance_of
ln geo:capital:manila admin:capital geo:instance_of
ln geo:capital:mexico_city admin:capital geo:instance_of
ln geo:capital:moscow admin:capital geo:instance_of
ln geo:capital:nairobi admin:capital geo:instance_of
ln geo:capital:new_delhi admin:capital geo:instance_of
ln geo:capital:oslo admin:capital geo:instance_of
ln geo:capital:ottawa admin:capital geo:instance_of
ln geo:capital:paris admin:capital geo:instance_of
ln geo:capital:pretoria admin:capital geo:instance_of
ln geo:capital:rabat admin:capital geo:instance_of
ln geo:capital:riyadh admin:capital geo:instance_of
ln geo:capital:rome admin:capital geo:instance_of
ln geo:capital:santiago admin:capital geo:instance_of
ln geo:capital:seoul admin:capital geo:instance_of
ln geo:capital:singapore admin:capital geo:instance_of
ln geo:capital:stockholm admin:capital geo:instance_of
ln geo:capital:tehran admin:capital geo:instance_of
ln geo:capital:tokyo admin:capital geo:instance_of
ln geo:capital:warsaw admin:capital geo:instance_of
ln geo:capital:washington_dc admin:capital geo:instance_of
ln geo:capital:wellington admin:capital geo:instance_of
ln geo:capital:abuja admin:capital geo:instance_of
ln geo:capital:bangkok admin:capital geo:instance_of
ln geo:capital:brussels admin:capital geo:instance_of
ln geo:capital:dhaka admin:capital geo:instance_of
ln geo:capital:baghdad admin:capital geo:instance_of
ln geo:capital:kuala_lumpur admin:capital geo:instance_of
ln geo:continent:africa admin:continent geo:instance_of
ln geo:continent:antarctica admin:continent geo:instance_of
ln geo:continent:asia admin:continent geo:instance_of
ln geo:continent:europe admin:continent geo:instance_of
ln geo:continent:north_america admin:continent geo:instance_of
ln geo:continent:oceania admin:continent geo:instance_of
ln geo:continent:south_america admin:continent geo:instance_of
ln geo:region:australia_new_zealand admin:region geo:instance_of
ln geo:region:caribbean admin:region geo:instance_of
ln geo:region:central_america admin:region geo:instance_of
ln geo:region:central_asia admin:region geo:instance_of
ln geo:region:eastern_africa admin:region geo:instance_of
ln geo:region:eastern_asia admin:region geo:instance_of
ln geo:region:eastern_europe admin:region geo:instance_of
ln geo:region:melanesia admin:region geo:instance_of
ln geo:region:micronesia admin:region geo:instance_of
ln geo:region:middle_africa admin:region geo:instance_of
ln geo:region:northern_africa admin:region geo:instance_of
ln geo:region:northern_america admin:region geo:instance_of
ln geo:region:northern_europe admin:region geo:instance_of
ln geo:region:polynesia admin:region geo:instance_of
ln geo:region:south_america admin:region geo:instance_of
ln geo:region:southeastern_asia admin:region geo:instance_of
ln geo:region:southern_africa admin:region geo:instance_of
ln geo:region:southern_asia admin:region geo:instance_of
ln geo:region:southern_europe admin:region geo:instance_of
ln geo:region:western_africa admin:region geo:instance_of
ln geo:region:western_asia admin:region geo:instance_of
ln geo:region:western_europe admin:region geo:instance_of

# ── geo:* underscore-format instances typed (country/state/province/nation) ──

# ── country/state/province/nation instances (uppercase ISO ids) typed ──
ln geo:country:ABW admin:country geo:instance_of
ln geo:country:AFG admin:country geo:instance_of
ln geo:country:AGO admin:country geo:instance_of
ln geo:country:AIA admin:country geo:instance_of
ln geo:country:ALB admin:country geo:instance_of
ln geo:country:AND admin:country geo:instance_of
ln geo:country:ARE admin:country geo:instance_of
ln geo:country:ARG admin:country geo:instance_of
ln geo:country:ARM admin:country geo:instance_of
ln geo:country:ASM admin:country geo:instance_of
ln geo:country:ATG admin:country geo:instance_of
ln geo:country:AUS admin:country geo:instance_of
ln geo:country:AUT admin:country geo:instance_of
ln geo:country:AZE admin:country geo:instance_of
ln geo:country:BDI admin:country geo:instance_of
ln geo:country:BEL admin:country geo:instance_of
ln geo:country:BEN admin:country geo:instance_of
ln geo:country:BFA admin:country geo:instance_of
ln geo:country:BGD admin:country geo:instance_of
ln geo:country:BGR admin:country geo:instance_of
ln geo:country:BHM admin:country geo:instance_of
ln geo:country:BHR admin:country geo:instance_of
ln geo:country:BIH admin:country geo:instance_of
ln geo:country:BLR admin:country geo:instance_of
ln geo:country:BLZ admin:country geo:instance_of
ln geo:country:BMU admin:country geo:instance_of
ln geo:country:BOL admin:country geo:instance_of
ln geo:country:BRA admin:country geo:instance_of
ln geo:country:BRB admin:country geo:instance_of
ln geo:country:BRN admin:country geo:instance_of
ln geo:country:BTN admin:country geo:instance_of
ln geo:country:BWA admin:country geo:instance_of
ln geo:country:CAF admin:country geo:instance_of
ln geo:country:CAN admin:country geo:instance_of
ln geo:country:CHE admin:country geo:instance_of
ln geo:country:CHL admin:country geo:instance_of
ln geo:country:CHN admin:country geo:instance_of
ln geo:country:CIV admin:country geo:instance_of
ln geo:country:CMR admin:country geo:instance_of
ln geo:country:COD admin:country geo:instance_of
ln geo:country:COG admin:country geo:instance_of
ln geo:country:COK admin:country geo:instance_of
ln geo:country:COL admin:country geo:instance_of
ln geo:country:COM admin:country geo:instance_of
ln geo:country:CPV admin:country geo:instance_of
ln geo:country:CRI admin:country geo:instance_of
ln geo:country:CUB admin:country geo:instance_of
ln geo:country:CUW admin:country geo:instance_of
ln geo:country:CYM admin:country geo:instance_of
ln geo:country:CYP admin:country geo:instance_of
ln geo:country:CZE admin:country geo:instance_of
ln geo:country:DEU admin:country geo:instance_of
ln geo:country:DJI admin:country geo:instance_of
ln geo:country:DMA admin:country geo:instance_of
ln geo:country:DNK admin:country geo:instance_of
ln geo:country:DOM admin:country geo:instance_of
ln geo:country:DZA admin:country geo:instance_of
ln geo:country:ECU admin:country geo:instance_of
ln geo:country:EGY admin:country geo:instance_of
ln geo:country:ERI admin:country geo:instance_of
ln geo:country:ESP admin:country geo:instance_of
ln geo:country:EST admin:country geo:instance_of
ln geo:country:ETH admin:country geo:instance_of
ln geo:country:FIN admin:country geo:instance_of
ln geo:country:FJI admin:country geo:instance_of
ln geo:country:FLK admin:country geo:instance_of
ln geo:country:FRA admin:country geo:instance_of
ln geo:country:FRO admin:country geo:instance_of
ln geo:country:FSM admin:country geo:instance_of
ln geo:country:GAB admin:country geo:instance_of
ln geo:country:GBR admin:country geo:instance_of
ln geo:country:GEO admin:country geo:instance_of
ln geo:country:GGY admin:country geo:instance_of
ln geo:country:GHA admin:country geo:instance_of
ln geo:country:GIB admin:country geo:instance_of
ln geo:country:GIN admin:country geo:instance_of
ln geo:country:GMB admin:country geo:instance_of
ln geo:country:GNB admin:country geo:instance_of
ln geo:country:GNQ admin:country geo:instance_of
ln geo:country:GRC admin:country geo:instance_of
ln geo:country:GRD admin:country geo:instance_of
ln geo:country:GRL admin:country geo:instance_of
ln geo:country:GTM admin:country geo:instance_of
ln geo:country:GUM admin:country geo:instance_of
ln geo:country:GUY admin:country geo:instance_of
ln geo:country:HKG admin:country geo:instance_of
ln geo:country:HND admin:country geo:instance_of
ln geo:country:HRV admin:country geo:instance_of
ln geo:country:HTI admin:country geo:instance_of
ln geo:country:HUN admin:country geo:instance_of
ln geo:country:IDN admin:country geo:instance_of
ln geo:country:IMN admin:country geo:instance_of
ln geo:country:IND admin:country geo:instance_of
ln geo:country:IRL admin:country geo:instance_of
ln geo:country:IRN admin:country geo:instance_of
ln geo:country:IRQ admin:country geo:instance_of
ln geo:country:ISL admin:country geo:instance_of
ln geo:country:ISR admin:country geo:instance_of
ln geo:country:ITA admin:country geo:instance_of
ln geo:country:JAM admin:country geo:instance_of
ln geo:country:JEY admin:country geo:instance_of
ln geo:country:JOR admin:country geo:instance_of
ln geo:country:JPN admin:country geo:instance_of
ln geo:country:KAZ admin:country geo:instance_of
ln geo:country:KEN admin:country geo:instance_of
ln geo:country:KGZ admin:country geo:instance_of
ln geo:country:KHM admin:country geo:instance_of
ln geo:country:KIR admin:country geo:instance_of
ln geo:country:KNA admin:country geo:instance_of
ln geo:country:KOR admin:country geo:instance_of
ln geo:country:KSV admin:country geo:instance_of
ln geo:country:KWT admin:country geo:instance_of
ln geo:country:LAO admin:country geo:instance_of
ln geo:country:LBN admin:country geo:instance_of
ln geo:country:LBR admin:country geo:instance_of
ln geo:country:LBY admin:country geo:instance_of
ln geo:country:LCA admin:country geo:instance_of
ln geo:country:LIE admin:country geo:instance_of
ln geo:country:LKA admin:country geo:instance_of
ln geo:country:LSO admin:country geo:instance_of
ln geo:country:LTU admin:country geo:instance_of
ln geo:country:LUX admin:country geo:instance_of
ln geo:country:LVA admin:country geo:instance_of
ln geo:country:MAC admin:country geo:instance_of
ln geo:country:MAF admin:country geo:instance_of
ln geo:country:MAR admin:country geo:instance_of
ln geo:country:MCO admin:country geo:instance_of
ln geo:country:MDA admin:country geo:instance_of
ln geo:country:MDG admin:country geo:instance_of
ln geo:country:MDV admin:country geo:instance_of
ln geo:country:MEX admin:country geo:instance_of
ln geo:country:MHL admin:country geo:instance_of
ln geo:country:MKD admin:country geo:instance_of
ln geo:country:MLI admin:country geo:instance_of
ln geo:country:MLT admin:country geo:instance_of
ln geo:country:MMR admin:country geo:instance_of
ln geo:country:MNE admin:country geo:instance_of
ln geo:country:MNG admin:country geo:instance_of
ln geo:country:MNP admin:country geo:instance_of
ln geo:country:MOZ admin:country geo:instance_of
ln geo:country:MRT admin:country geo:instance_of
ln geo:country:MUS admin:country geo:instance_of
ln geo:country:MWI admin:country geo:instance_of
ln geo:country:MYS admin:country geo:instance_of
ln geo:country:NAM admin:country geo:instance_of
ln geo:country:NCL admin:country geo:instance_of
ln geo:country:NER admin:country geo:instance_of
ln geo:country:NGA admin:country geo:instance_of
ln geo:country:NIC admin:country geo:instance_of
ln geo:country:NIU admin:country geo:instance_of
ln geo:country:NLD admin:country geo:instance_of
ln geo:country:NOR admin:country geo:instance_of
ln geo:country:NPL admin:country geo:instance_of
ln geo:country:NZL admin:country geo:instance_of
ln geo:country:OMN admin:country geo:instance_of
ln geo:country:PAK admin:country geo:instance_of
ln geo:country:PAN admin:country geo:instance_of
ln geo:country:PER admin:country geo:instance_of
ln geo:country:PHL admin:country geo:instance_of
ln geo:country:PLW admin:country geo:instance_of
ln geo:country:PNG admin:country geo:instance_of
ln geo:country:POL admin:country geo:instance_of
ln geo:country:PRI admin:country geo:instance_of
ln geo:country:PRK admin:country geo:instance_of
ln geo:country:PRT admin:country geo:instance_of
ln geo:country:PRY admin:country geo:instance_of
ln geo:country:PYF admin:country geo:instance_of
ln geo:country:QAT admin:country geo:instance_of
ln geo:country:ROU admin:country geo:instance_of
ln geo:country:RUS admin:country geo:instance_of
ln geo:country:RWA admin:country geo:instance_of
ln geo:country:SAU admin:country geo:instance_of
ln geo:country:SDN admin:country geo:instance_of
ln geo:country:SEN admin:country geo:instance_of
ln geo:country:SGP admin:country geo:instance_of
ln geo:country:SLB admin:country geo:instance_of
ln geo:country:SLE admin:country geo:instance_of
ln geo:country:SLV admin:country geo:instance_of
ln geo:country:SMR admin:country geo:instance_of
ln geo:country:SOM admin:country geo:instance_of
ln geo:country:SPM admin:country geo:instance_of
ln geo:country:SRB admin:country geo:instance_of
ln geo:country:SSD admin:country geo:instance_of
ln geo:country:STP admin:country geo:instance_of
ln geo:country:SUR admin:country geo:instance_of
ln geo:country:SVK admin:country geo:instance_of
ln geo:country:SVN admin:country geo:instance_of
ln geo:country:SWE admin:country geo:instance_of
ln geo:country:SWZ admin:country geo:instance_of
ln geo:country:SXM admin:country geo:instance_of
ln geo:country:SYC admin:country geo:instance_of
ln geo:country:SYR admin:country geo:instance_of
ln geo:country:TCD admin:country geo:instance_of
ln geo:country:TGO admin:country geo:instance_of
ln geo:country:THA admin:country geo:instance_of
ln geo:country:TJK admin:country geo:instance_of
ln geo:country:TKM admin:country geo:instance_of
ln geo:country:TLS admin:country geo:instance_of
ln geo:country:TON admin:country geo:instance_of
ln geo:country:TTO admin:country geo:instance_of
ln geo:country:TUN admin:country geo:instance_of
ln geo:country:TUR admin:country geo:instance_of
ln geo:country:TUV admin:country geo:instance_of
ln geo:country:TWN admin:country geo:instance_of
ln geo:country:TZA admin:country geo:instance_of
ln geo:country:UGA admin:country geo:instance_of
ln geo:country:UKR admin:country geo:instance_of
ln geo:country:URY admin:country geo:instance_of
ln geo:country:USA admin:country geo:instance_of
ln geo:country:UZB admin:country geo:instance_of
ln geo:country:VCT admin:country geo:instance_of
ln geo:country:VEN admin:country geo:instance_of
ln geo:country:VGB admin:country geo:instance_of
ln geo:country:VNM admin:country geo:instance_of
ln geo:country:VUT admin:country geo:instance_of
ln geo:country:WBG admin:country geo:instance_of
ln geo:country:WSM admin:country geo:instance_of
ln geo:country:YEM admin:country geo:instance_of
ln geo:country:ZAF admin:country geo:instance_of
ln geo:country:ZMB admin:country geo:instance_of
ln geo:country:ZWE admin:country geo:instance_of
ln geo:province:CA_AB admin:province geo:instance_of
ln geo:province:CA_BC admin:province geo:instance_of
ln geo:province:CA_MB admin:province geo:instance_of
ln geo:province:CA_NB admin:province geo:instance_of
ln geo:province:CA_NL admin:province geo:instance_of
ln geo:province:CA_NS admin:province geo:instance_of
ln geo:province:CA_ON admin:province geo:instance_of
ln geo:province:CA_PE admin:province geo:instance_of
ln geo:province:CA_QC admin:province geo:instance_of
ln geo:province:CA_SK admin:province geo:instance_of
ln geo:province:CA_NT admin:province geo:instance_of
ln geo:province:CA_NU admin:province geo:instance_of
ln geo:province:CA_YT admin:province geo:instance_of
ln geo:nation:GBR admin:nation geo:instance_of
ln geo:nation:ENG admin:nation geo:instance_of
ln geo:nation:SCT admin:nation geo:instance_of
ln geo:nation:WLS admin:nation geo:instance_of
ln geo:nation:NIR admin:nation geo:instance_of
ln geo:state:US_AL admin:state geo:instance_of
ln geo:state:US_AK admin:state geo:instance_of
ln geo:state:US_AZ admin:state geo:instance_of
ln geo:state:US_AR admin:state geo:instance_of
ln geo:state:US_CA admin:state geo:instance_of
ln geo:state:US_CO admin:state geo:instance_of
ln geo:state:US_CT admin:state geo:instance_of
ln geo:state:US_DE admin:state geo:instance_of
ln geo:state:US_FL admin:state geo:instance_of
ln geo:state:US_GA admin:state geo:instance_of
ln geo:state:US_HI admin:state geo:instance_of
ln geo:state:US_ID admin:state geo:instance_of
ln geo:state:US_IL admin:state geo:instance_of
ln geo:state:US_IN admin:state geo:instance_of
ln geo:state:US_IA admin:state geo:instance_of
ln geo:state:US_KS admin:state geo:instance_of
ln geo:state:US_KY admin:state geo:instance_of
ln geo:state:US_LA admin:state geo:instance_of
ln geo:state:US_ME admin:state geo:instance_of
ln geo:state:US_MD admin:state geo:instance_of
ln geo:state:US_MA admin:state geo:instance_of
ln geo:state:US_MI admin:state geo:instance_of
ln geo:state:US_MN admin:state geo:instance_of
ln geo:state:US_MS admin:state geo:instance_of
ln geo:state:US_MO admin:state geo:instance_of
ln geo:state:US_MT admin:state geo:instance_of
ln geo:state:US_NE admin:state geo:instance_of
ln geo:state:US_NV admin:state geo:instance_of
ln geo:state:US_NH admin:state geo:instance_of
ln geo:state:US_NJ admin:state geo:instance_of
ln geo:state:US_NM admin:state geo:instance_of
ln geo:state:US_NY admin:state geo:instance_of
ln geo:state:US_NC admin:state geo:instance_of
ln geo:state:US_ND admin:state geo:instance_of
ln geo:state:US_OH admin:state geo:instance_of
ln geo:state:US_OK admin:state geo:instance_of
ln geo:state:US_OR admin:state geo:instance_of
ln geo:state:US_PA admin:state geo:instance_of
ln geo:state:US_RI admin:state geo:instance_of
ln geo:state:US_SC admin:state geo:instance_of
ln geo:state:US_SD admin:state geo:instance_of
ln geo:state:US_TN admin:state geo:instance_of
ln geo:state:US_TX admin:state geo:instance_of
ln geo:state:US_UT admin:state geo:instance_of
ln geo:state:US_VT admin:state geo:instance_of
ln geo:state:US_VA admin:state geo:instance_of
ln geo:state:US_WA admin:state geo:instance_of
ln geo:state:US_WV admin:state geo:instance_of
ln geo:state:US_WI admin:state geo:instance_of
ln geo:state:US_WY admin:state geo:instance_of
ln geo:state:US_DC admin:state geo:instance_of
