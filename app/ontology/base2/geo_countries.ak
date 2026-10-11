# Akasha ontology — namespace: geo:country
# World country atoms — base set (44 countries: G20 + regional reps + Mongolia).
# Full 221-country set: world/geo_countries_core.ak
# Each country has a lowercase ISO-3 alias (e.g. fra → geo:country:FRA)
# so capitals are reachable via: s r fra → sys:has_capital → geo:capital:paris
# atoms: 44

def "geo:country:ARG" "Argentina"
al geo:country:ARG arg
al geo:country:ARG argentina
set.add name="set:geo:countries" id="geo:country:ARG"
set.add name="set:geo:index" id="geo:country:ARG"
ln geo:country:ARG geo:region:south_america thesaurus:hypernym
def "geo:country:AUS" "Australia"
al geo:country:AUS aus
al geo:country:AUS australia
set.add name="set:geo:countries" id="geo:country:AUS"
set.add name="set:geo:index" id="geo:country:AUS"
ln geo:country:AUS geo:region:australia_new_zealand thesaurus:hypernym
def "geo:country:BRA" "Brazil"
al geo:country:BRA bra
al geo:country:BRA brazil
set.add name="set:geo:countries" id="geo:country:BRA"
set.add name="set:geo:index" id="geo:country:BRA"
ln geo:country:BRA geo:region:south_america thesaurus:hypernym
def "geo:country:CAN" "Canada"
al geo:country:CAN can
al geo:country:CAN canada
set.add name="set:geo:countries" id="geo:country:CAN"
set.add name="set:geo:index" id="geo:country:CAN"
ln geo:country:CAN geo:region:northern_america thesaurus:hypernym
def "geo:country:CHN" "China"
al geo:country:CHN chn
al geo:country:CHN china
set.add name="set:geo:countries" id="geo:country:CHN"
set.add name="set:geo:index" id="geo:country:CHN"
ln geo:country:CHN geo:region:eastern_asia thesaurus:hypernym
def "geo:country:DEU" "Germany"
al geo:country:DEU deu
al geo:country:DEU germany
al geo:country:DEU deutschland
set.add name="set:geo:countries" id="geo:country:DEU"
set.add name="set:geo:index" id="geo:country:DEU"
ln geo:country:DEU geo:region:western_europe thesaurus:hypernym
def "geo:country:FRA" "France"
al geo:country:FRA fra
al geo:country:FRA france
set.add name="set:geo:countries" id="geo:country:FRA"
set.add name="set:geo:index" id="geo:country:FRA"
ln geo:country:FRA geo:region:western_europe thesaurus:hypernym
def "geo:country:GBR" "United Kingdom"
al geo:country:GBR gbr
al geo:country:GBR uk
al geo:country:GBR britain
set.add name="set:geo:countries" id="geo:country:GBR"
set.add name="set:geo:index" id="geo:country:GBR"
ln geo:country:GBR geo:region:northern_europe thesaurus:hypernym
def "geo:country:IND" "India"
al geo:country:IND ind
al geo:country:IND india
set.add name="set:geo:countries" id="geo:country:IND"
set.add name="set:geo:index" id="geo:country:IND"
ln geo:country:IND geo:region:southern_asia thesaurus:hypernym
def "geo:country:IDN" "Indonesia"
al geo:country:IDN idn
al geo:country:IDN indonesia
set.add name="set:geo:countries" id="geo:country:IDN"
set.add name="set:geo:index" id="geo:country:IDN"
ln geo:country:IDN geo:region:southeastern_asia thesaurus:hypernym
def "geo:country:ITA" "Italy"
al geo:country:ITA ita
al geo:country:ITA italy
set.add name="set:geo:countries" id="geo:country:ITA"
set.add name="set:geo:index" id="geo:country:ITA"
ln geo:country:ITA geo:region:southern_europe thesaurus:hypernym
def "geo:country:JPN" "Japan"
al geo:country:JPN jpn
al geo:country:JPN japan
set.add name="set:geo:countries" id="geo:country:JPN"
set.add name="set:geo:index" id="geo:country:JPN"
ln geo:country:JPN geo:region:eastern_asia thesaurus:hypernym
def "geo:country:KOR" "Korea, South"
al geo:country:KOR kor
al geo:country:KOR south_korea
set.add name="set:geo:countries" id="geo:country:KOR"
set.add name="set:geo:index" id="geo:country:KOR"
ln geo:country:KOR geo:region:eastern_asia thesaurus:hypernym
def "geo:country:MEX" "Mexico"
al geo:country:MEX mex
al geo:country:MEX mexico
set.add name="set:geo:countries" id="geo:country:MEX"
set.add name="set:geo:index" id="geo:country:MEX"
ln geo:country:MEX geo:region:central_america thesaurus:hypernym
def "geo:country:RUS" "Russia"
al geo:country:RUS rus
al geo:country:RUS russia
set.add name="set:geo:countries" id="geo:country:RUS"
set.add name="set:geo:index" id="geo:country:RUS"
ln geo:country:RUS geo:region:eastern_europe thesaurus:hypernym
def "geo:country:SAU" "Saudi Arabia"
al geo:country:SAU sau
al geo:country:SAU saudi_arabia
set.add name="set:geo:countries" id="geo:country:SAU"
set.add name="set:geo:index" id="geo:country:SAU"
ln geo:country:SAU geo:region:western_asia thesaurus:hypernym
def "geo:country:ZAF" "South Africa"
al geo:country:ZAF zaf
al geo:country:ZAF south_africa
set.add name="set:geo:countries" id="geo:country:ZAF"
set.add name="set:geo:index" id="geo:country:ZAF"
ln geo:country:ZAF geo:region:southern_africa thesaurus:hypernym
def "geo:country:TUR" "Turkey"
al geo:country:TUR tur
al geo:country:TUR turkey
set.add name="set:geo:countries" id="geo:country:TUR"
set.add name="set:geo:index" id="geo:country:TUR"
ln geo:country:TUR geo:region:western_asia thesaurus:hypernym
def "geo:country:USA" "United States"
al geo:country:USA usa
al geo:country:USA us
al geo:country:USA america
set.add name="set:geo:countries" id="geo:country:USA"
set.add name="set:geo:index" id="geo:country:USA"
ln geo:country:USA geo:region:northern_america thesaurus:hypernym
def "geo:country:EGY" "Egypt"
al geo:country:EGY egy
al geo:country:EGY egypt
set.add name="set:geo:countries" id="geo:country:EGY"
set.add name="set:geo:index" id="geo:country:EGY"
ln geo:country:EGY geo:region:northern_africa thesaurus:hypernym
def "geo:country:NGA" "Nigeria"
al geo:country:NGA nga
al geo:country:NGA nigeria
set.add name="set:geo:countries" id="geo:country:NGA"
set.add name="set:geo:index" id="geo:country:NGA"
ln geo:country:NGA geo:region:western_africa thesaurus:hypernym
def "geo:country:ETH" "Ethiopia"
al geo:country:ETH eth
al geo:country:ETH ethiopia
set.add name="set:geo:countries" id="geo:country:ETH"
set.add name="set:geo:index" id="geo:country:ETH"
ln geo:country:ETH geo:region:eastern_africa thesaurus:hypernym
def "geo:country:IRN" "Iran"
al geo:country:IRN irn
al geo:country:IRN iran
set.add name="set:geo:countries" id="geo:country:IRN"
set.add name="set:geo:index" id="geo:country:IRN"
ln geo:country:IRN geo:region:southern_asia thesaurus:hypernym
def "geo:country:PAK" "Pakistan"
al geo:country:PAK pak
al geo:country:PAK pakistan
set.add name="set:geo:countries" id="geo:country:PAK"
set.add name="set:geo:index" id="geo:country:PAK"
ln geo:country:PAK geo:region:southern_asia thesaurus:hypernym
def "geo:country:THA" "Thailand"
al geo:country:THA tha
al geo:country:THA thailand
set.add name="set:geo:countries" id="geo:country:THA"
set.add name="set:geo:index" id="geo:country:THA"
ln geo:country:THA geo:region:southeastern_asia thesaurus:hypernym
def "geo:country:VNM" "Vietnam"
al geo:country:VNM vnm
al geo:country:VNM vietnam
set.add name="set:geo:countries" id="geo:country:VNM"
set.add name="set:geo:index" id="geo:country:VNM"
ln geo:country:VNM geo:region:southeastern_asia thesaurus:hypernym
def "geo:country:PHL" "Philippines"
al geo:country:PHL phl
al geo:country:PHL philippines
set.add name="set:geo:countries" id="geo:country:PHL"
set.add name="set:geo:index" id="geo:country:PHL"
ln geo:country:PHL geo:region:southeastern_asia thesaurus:hypernym
def "geo:country:ESP" "Spain"
al geo:country:ESP esp
al geo:country:ESP spain
set.add name="set:geo:countries" id="geo:country:ESP"
set.add name="set:geo:index" id="geo:country:ESP"
ln geo:country:ESP geo:region:southern_europe thesaurus:hypernym
def "geo:country:POL" "Poland"
al geo:country:POL pol
al geo:country:POL poland
set.add name="set:geo:countries" id="geo:country:POL"
set.add name="set:geo:index" id="geo:country:POL"
ln geo:country:POL geo:region:eastern_europe thesaurus:hypernym
def "geo:country:NLD" "Netherlands"
al geo:country:NLD nld
al geo:country:NLD netherlands
set.add name="set:geo:countries" id="geo:country:NLD"
set.add name="set:geo:index" id="geo:country:NLD"
ln geo:country:NLD geo:region:western_europe thesaurus:hypernym
def "geo:country:UKR" "Ukraine"
al geo:country:UKR ukr
al geo:country:UKR ukraine
set.add name="set:geo:countries" id="geo:country:UKR"
set.add name="set:geo:index" id="geo:country:UKR"
ln geo:country:UKR geo:region:eastern_europe thesaurus:hypernym
def "geo:country:COL" "Colombia"
al geo:country:COL col
al geo:country:COL colombia
set.add name="set:geo:countries" id="geo:country:COL"
set.add name="set:geo:index" id="geo:country:COL"
ln geo:country:COL geo:region:south_america thesaurus:hypernym
def "geo:country:CHL" "Chile"
al geo:country:CHL chl
al geo:country:CHL chile
set.add name="set:geo:countries" id="geo:country:CHL"
set.add name="set:geo:index" id="geo:country:CHL"
ln geo:country:CHL geo:region:south_america thesaurus:hypernym
def "geo:country:NZL" "New Zealand"
al geo:country:NZL nzl
al geo:country:NZL new_zealand
set.add name="set:geo:countries" id="geo:country:NZL"
set.add name="set:geo:index" id="geo:country:NZL"
ln geo:country:NZL geo:region:australia_new_zealand thesaurus:hypernym
def "geo:country:ARE" "United Arab Emirates"
al geo:country:ARE are
al geo:country:ARE uae
set.add name="set:geo:countries" id="geo:country:ARE"
set.add name="set:geo:index" id="geo:country:ARE"
ln geo:country:ARE geo:region:western_asia thesaurus:hypernym
def "geo:country:SGP" "Singapore"
al geo:country:SGP sgp
al geo:country:SGP singapore
set.add name="set:geo:countries" id="geo:country:SGP"
set.add name="set:geo:index" id="geo:country:SGP"
ln geo:country:SGP geo:region:southeastern_asia thesaurus:hypernym
def "geo:country:SWE" "Sweden"
al geo:country:SWE swe
al geo:country:SWE sweden
set.add name="set:geo:countries" id="geo:country:SWE"
set.add name="set:geo:index" id="geo:country:SWE"
ln geo:country:SWE geo:region:northern_europe thesaurus:hypernym
def "geo:country:NOR" "Norway"
al geo:country:NOR nor
al geo:country:NOR norway
set.add name="set:geo:countries" id="geo:country:NOR"
set.add name="set:geo:index" id="geo:country:NOR"
ln geo:country:NOR geo:region:northern_europe thesaurus:hypernym
def "geo:country:CHE" "Switzerland"
al geo:country:CHE che
al geo:country:CHE switzerland
set.add name="set:geo:countries" id="geo:country:CHE"
set.add name="set:geo:index" id="geo:country:CHE"
ln geo:country:CHE geo:region:western_europe thesaurus:hypernym
def "geo:country:ISR" "Israel"
al geo:country:ISR isr
al geo:country:ISR israel
set.add name="set:geo:countries" id="geo:country:ISR"
set.add name="set:geo:index" id="geo:country:ISR"
ln geo:country:ISR geo:region:western_asia thesaurus:hypernym
def "geo:country:KEN" "Kenya"
al geo:country:KEN ken
al geo:country:KEN kenya
set.add name="set:geo:countries" id="geo:country:KEN"
set.add name="set:geo:index" id="geo:country:KEN"
ln geo:country:KEN geo:region:eastern_africa thesaurus:hypernym
def "geo:country:MAR" "Morocco"
al geo:country:MAR mar
al geo:country:MAR morocco
set.add name="set:geo:countries" id="geo:country:MAR"
set.add name="set:geo:index" id="geo:country:MAR"
ln geo:country:MAR geo:region:northern_africa thesaurus:hypernym
def "geo:country:PER" "Peru"
al geo:country:PER per
al geo:country:PER peru
set.add name="set:geo:countries" id="geo:country:PER"
set.add name="set:geo:index" id="geo:country:PER"
ln geo:country:PER geo:region:south_america thesaurus:hypernym
def "geo:country:MNG" "Mongolia"
al geo:country:MNG mng
al geo:country:MNG mongolia
set.add name="set:geo:countries" id="geo:country:MNG"
set.add name="set:geo:index" id="geo:country:MNG"
ln geo:country:MNG geo:region:eastern_asia thesaurus:hypernym
def "geo:country:BEL" "Belgium"
al geo:country:BEL bel
al geo:country:BEL belgium
set.add name="set:geo:countries" id="geo:country:BEL"
set.add name="set:geo:index" id="geo:country:BEL"
ln geo:country:BEL geo:region:western_europe thesaurus:hypernym
def "geo:country:BGD" "Bangladesh"
al geo:country:BGD bgd
al geo:country:BGD bangladesh
set.add name="set:geo:countries" id="geo:country:BGD"
set.add name="set:geo:index" id="geo:country:BGD"
ln geo:country:BGD geo:region:southern_asia thesaurus:hypernym
def "geo:country:IRQ" "Iraq"
al geo:country:IRQ irq
al geo:country:IRQ iraq
set.add name="set:geo:countries" id="geo:country:IRQ"
set.add name="set:geo:index" id="geo:country:IRQ"
ln geo:country:IRQ geo:region:western_asia thesaurus:hypernym
def "geo:country:MYS" "Malaysia"
al geo:country:MYS mys
al geo:country:MYS malaysia
set.add name="set:geo:countries" id="geo:country:MYS"
set.add name="set:geo:index" id="geo:country:MYS"
ln geo:country:MYS geo:region:southeastern_asia thesaurus:hypernym
