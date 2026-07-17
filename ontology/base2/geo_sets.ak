# Akasha ontology — geographic properties and sets
# Extends the base 43 countries with:
#   - geo:borders relation + bilateral land-border links
#   - set:geo:landlocked / set:geo:island_nations
#   - set:geo:northern_hemisphere / set:geo:southern_hemisphere
#   - set:geo:tropical / set:geo:temperate / set:geo:polar
# atoms: 8

# ── Relation: land border ──────────────────────────────────────────────────────

def "geo:borders" "Two sovereign states share a land border (add both directions)."
ln geo:borders geo:adjacent_to thesaurus:hyponym
ln geo:borders ont.geo sys:part_of

# ── Land borders — bilateral pairs within the 43-country base set ──────────────
# Americas
ln geo:country:ARG geo:country:BRA geo:borders
ln geo:country:BRA geo:country:ARG geo:borders
ln geo:country:ARG geo:country:CHL geo:borders
ln geo:country:CHL geo:country:ARG geo:borders
ln geo:country:BRA geo:country:COL geo:borders
ln geo:country:COL geo:country:BRA geo:borders
ln geo:country:BRA geo:country:PER geo:borders
ln geo:country:PER geo:country:BRA geo:borders
ln geo:country:CAN geo:country:USA geo:borders
ln geo:country:USA geo:country:CAN geo:borders
ln geo:country:MEX geo:country:USA geo:borders
ln geo:country:USA geo:country:MEX geo:borders
ln geo:country:COL geo:country:PER geo:borders
ln geo:country:PER geo:country:COL geo:borders
ln geo:country:CHL geo:country:PER geo:borders
ln geo:country:PER geo:country:CHL geo:borders
# Europe
ln geo:country:DEU geo:country:FRA geo:borders
ln geo:country:FRA geo:country:DEU geo:borders
ln geo:country:DEU geo:country:NLD geo:borders
ln geo:country:NLD geo:country:DEU geo:borders
ln geo:country:DEU geo:country:POL geo:borders
ln geo:country:POL geo:country:DEU geo:borders
ln geo:country:DEU geo:country:CHE geo:borders
ln geo:country:CHE geo:country:DEU geo:borders
ln geo:country:FRA geo:country:ESP geo:borders
ln geo:country:ESP geo:country:FRA geo:borders
ln geo:country:FRA geo:country:CHE geo:borders
ln geo:country:CHE geo:country:FRA geo:borders
ln geo:country:FRA geo:country:ITA geo:borders
ln geo:country:ITA geo:country:FRA geo:borders
ln geo:country:CHE geo:country:ITA geo:borders
ln geo:country:ITA geo:country:CHE geo:borders
ln geo:country:POL geo:country:RUS geo:borders
ln geo:country:RUS geo:country:POL geo:borders
ln geo:country:POL geo:country:UKR geo:borders
ln geo:country:UKR geo:country:POL geo:borders
ln geo:country:RUS geo:country:UKR geo:borders
ln geo:country:UKR geo:country:RUS geo:borders
ln geo:country:SWE geo:country:NOR geo:borders
ln geo:country:NOR geo:country:SWE geo:borders
ln geo:country:NOR geo:country:RUS geo:borders
ln geo:country:RUS geo:country:NOR geo:borders
# Europe ↔ Africa (Spain–Morocco via Ceuta/Melilla enclaves)
ln geo:country:ESP geo:country:MAR geo:borders
ln geo:country:MAR geo:country:ESP geo:borders
# Asia
ln geo:country:CHN geo:country:RUS geo:borders
ln geo:country:RUS geo:country:CHN geo:borders
ln geo:country:CHN geo:country:IND geo:borders
ln geo:country:IND geo:country:CHN geo:borders
ln geo:country:CHN geo:country:PAK geo:borders
ln geo:country:PAK geo:country:CHN geo:borders
ln geo:country:CHN geo:country:VNM geo:borders
ln geo:country:VNM geo:country:CHN geo:borders
ln geo:country:IND geo:country:PAK geo:borders
ln geo:country:PAK geo:country:IND geo:borders
ln geo:country:IRN geo:country:PAK geo:borders
ln geo:country:PAK geo:country:IRN geo:borders
ln geo:country:IRN geo:country:TUR geo:borders
ln geo:country:TUR geo:country:IRN geo:borders
# Middle East
ln geo:country:ARE geo:country:SAU geo:borders
ln geo:country:SAU geo:country:ARE geo:borders
ln geo:country:ISR geo:country:EGY geo:borders
ln geo:country:EGY geo:country:ISR geo:borders
# Africa
ln geo:country:KEN geo:country:ETH geo:borders
ln geo:country:ETH geo:country:KEN geo:borders

# ── Concept: landlocked ────────────────────────────────────────────────────────

def "geo:concept:landlocked" "Country with no coastline, entirely enclosed by land or inland seas."
set.add name="set:geo:landlocked" id="geo:country:CHE"
set.add name="set:geo:landlocked" id="geo:country:ETH"

# ── Concept: island nations ────────────────────────────────────────────────────

def "geo:concept:island_nation" "Country consisting entirely or predominantly of islands with no land border to another state."
set.add name="set:geo:island_nations" id="geo:country:AUS"
set.add name="set:geo:island_nations" id="geo:country:GBR"
set.add name="set:geo:island_nations" id="geo:country:IDN"
set.add name="set:geo:island_nations" id="geo:country:JPN"
set.add name="set:geo:island_nations" id="geo:country:NZL"
set.add name="set:geo:island_nations" id="geo:country:PHL"
set.add name="set:geo:island_nations" id="geo:country:SGP"

# ── Concept: hemispheres ───────────────────────────────────────────────────────

def "geo:concept:northern_hemisphere" "Country located predominantly north of the equator."
def "geo:concept:southern_hemisphere" "Country located predominantly south of the equator."

# Northern hemisphere (by majority land area and population centre)
set.add name="set:geo:northern_hemisphere" id="geo:country:CAN"
set.add name="set:geo:northern_hemisphere" id="geo:country:CHN"
set.add name="set:geo:northern_hemisphere" id="geo:country:DEU"
set.add name="set:geo:northern_hemisphere" id="geo:country:EGY"
set.add name="set:geo:northern_hemisphere" id="geo:country:ESP"
set.add name="set:geo:northern_hemisphere" id="geo:country:ETH"
set.add name="set:geo:northern_hemisphere" id="geo:country:FRA"
set.add name="set:geo:northern_hemisphere" id="geo:country:GBR"
set.add name="set:geo:northern_hemisphere" id="geo:country:IND"
set.add name="set:geo:northern_hemisphere" id="geo:country:IRN"
set.add name="set:geo:northern_hemisphere" id="geo:country:ISR"
set.add name="set:geo:northern_hemisphere" id="geo:country:ITA"
set.add name="set:geo:northern_hemisphere" id="geo:country:JPN"
set.add name="set:geo:northern_hemisphere" id="geo:country:KEN"
set.add name="set:geo:northern_hemisphere" id="geo:country:KOR"
set.add name="set:geo:northern_hemisphere" id="geo:country:MAR"
set.add name="set:geo:northern_hemisphere" id="geo:country:MEX"
set.add name="set:geo:northern_hemisphere" id="geo:country:NGA"
set.add name="set:geo:northern_hemisphere" id="geo:country:NLD"
set.add name="set:geo:northern_hemisphere" id="geo:country:NOR"
set.add name="set:geo:northern_hemisphere" id="geo:country:PAK"
set.add name="set:geo:northern_hemisphere" id="geo:country:PHL"
set.add name="set:geo:northern_hemisphere" id="geo:country:POL"
set.add name="set:geo:northern_hemisphere" id="geo:country:RUS"
set.add name="set:geo:northern_hemisphere" id="geo:country:SAU"
set.add name="set:geo:northern_hemisphere" id="geo:country:SGP"
set.add name="set:geo:northern_hemisphere" id="geo:country:SWE"
set.add name="set:geo:northern_hemisphere" id="geo:country:THA"
set.add name="set:geo:northern_hemisphere" id="geo:country:TUR"
set.add name="set:geo:northern_hemisphere" id="geo:country:UKR"
set.add name="set:geo:northern_hemisphere" id="geo:country:USA"
set.add name="set:geo:northern_hemisphere" id="geo:country:VNM"
set.add name="set:geo:northern_hemisphere" id="geo:country:CHE"
set.add name="set:geo:northern_hemisphere" id="geo:country:ARE"
set.add name="set:geo:northern_hemisphere" id="geo:country:COL"
# Straddle equator — in both sets
set.add name="set:geo:northern_hemisphere" id="geo:country:BRA"
set.add name="set:geo:northern_hemisphere" id="geo:country:IDN"

# Southern hemisphere
set.add name="set:geo:southern_hemisphere" id="geo:country:ARG"
set.add name="set:geo:southern_hemisphere" id="geo:country:AUS"
set.add name="set:geo:southern_hemisphere" id="geo:country:BRA"
set.add name="set:geo:southern_hemisphere" id="geo:country:CHL"
set.add name="set:geo:southern_hemisphere" id="geo:country:IDN"
set.add name="set:geo:southern_hemisphere" id="geo:country:NZL"
set.add name="set:geo:southern_hemisphere" id="geo:country:PER"
set.add name="set:geo:southern_hemisphere" id="geo:country:ZAF"

# ── Concept: climate zones ─────────────────────────────────────────────────────

def "geo:concept:tropical_zone" "Country with a predominantly tropical climate — warm year-round, near the equator."
def "geo:concept:temperate_zone" "Country with a predominantly temperate climate — four distinct seasons, mid-latitudes."
def "geo:concept:polar_zone" "Country with a predominantly boreal or polar climate — long cold winters, high latitudes."

# Tropical zone (primarily equatorial / tropical savannah / tropical monsoon)
set.add name="set:geo:tropical" id="geo:country:BRA"
set.add name="set:geo:tropical" id="geo:country:COL"
set.add name="set:geo:tropical" id="geo:country:ETH"
set.add name="set:geo:tropical" id="geo:country:IDN"
set.add name="set:geo:tropical" id="geo:country:KEN"
set.add name="set:geo:tropical" id="geo:country:NGA"
set.add name="set:geo:tropical" id="geo:country:PHL"
set.add name="set:geo:tropical" id="geo:country:SGP"
set.add name="set:geo:tropical" id="geo:country:THA"
set.add name="set:geo:tropical" id="geo:country:VNM"

# Temperate zone (Mediterranean, oceanic, continental, subtropical arid)
set.add name="set:geo:temperate" id="geo:country:ARG"
set.add name="set:geo:temperate" id="geo:country:ARE"
set.add name="set:geo:temperate" id="geo:country:AUS"
set.add name="set:geo:temperate" id="geo:country:CHE"
set.add name="set:geo:temperate" id="geo:country:CHL"
set.add name="set:geo:temperate" id="geo:country:CHN"
set.add name="set:geo:temperate" id="geo:country:DEU"
set.add name="set:geo:temperate" id="geo:country:EGY"
set.add name="set:geo:temperate" id="geo:country:ESP"
set.add name="set:geo:temperate" id="geo:country:FRA"
set.add name="set:geo:temperate" id="geo:country:GBR"
set.add name="set:geo:temperate" id="geo:country:IND"
set.add name="set:geo:temperate" id="geo:country:IRN"
set.add name="set:geo:temperate" id="geo:country:ISR"
set.add name="set:geo:temperate" id="geo:country:ITA"
set.add name="set:geo:temperate" id="geo:country:JPN"
set.add name="set:geo:temperate" id="geo:country:KOR"
set.add name="set:geo:temperate" id="geo:country:MAR"
set.add name="set:geo:temperate" id="geo:country:MEX"
set.add name="set:geo:temperate" id="geo:country:NLD"
set.add name="set:geo:temperate" id="geo:country:NZL"
set.add name="set:geo:temperate" id="geo:country:PAK"
set.add name="set:geo:temperate" id="geo:country:PER"
set.add name="set:geo:temperate" id="geo:country:POL"
set.add name="set:geo:temperate" id="geo:country:SAU"
set.add name="set:geo:temperate" id="geo:country:SWE"
set.add name="set:geo:temperate" id="geo:country:TUR"
set.add name="set:geo:temperate" id="geo:country:UKR"
set.add name="set:geo:temperate" id="geo:country:USA"
set.add name="set:geo:temperate" id="geo:country:ZAF"

# Polar/boreal zone (subarctic and Arctic climates dominant)
set.add name="set:geo:polar" id="geo:country:CAN"
set.add name="set:geo:polar" id="geo:country:NOR"
set.add name="set:geo:polar" id="geo:country:RUS"
