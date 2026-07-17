# Akasha ontology — seasonality frame (region-relative).
# KEY: an ingredient carries its harvest SEASON (climate-relative), not a month.
# The hemisphere×season→month cross is defined ONCE here (seasonmap:north/south),
# so the SAME season maps to opposite months in N vs S. Tropical = year_round.
# Query with scripts/seasonal.py. Base pack.

def "season:spring" "Season: spring."
def "season:summer" "Season: summer."
def "season:autumn" "Season: autumn."
def "season:winter" "Season: winter."
def "season:year_round" "Season: year_round."
def "hemisphere:north" "Northern hemisphere."
def "hemisphere:south" "Southern hemisphere."
def "climate:tropical" "Tropical zone — minimal seasonality (year-round)."
def "climate:temperate" "Temperate zone."
def "climate:cold" "Cold / boreal zone."
def "month:january" "January."
def "month:february" "February."
def "month:march" "March."
def "month:april" "April."
def "month:may" "May."
def "month:june" "June."
def "month:july" "July."
def "month:august" "August."
def "month:september" "September."
def "month:october" "October."
def "month:november" "November."
def "month:december" "December."

# ── hemisphere × season → month (defined once) ──
ln season:spring month:march seasonmap:north
ln season:spring month:april seasonmap:north
ln season:spring month:may seasonmap:north
ln season:summer month:june seasonmap:north
ln season:summer month:july seasonmap:north
ln season:summer month:august seasonmap:north
ln season:autumn month:september seasonmap:north
ln season:autumn month:october seasonmap:north
ln season:autumn month:november seasonmap:north
ln season:winter month:december seasonmap:north
ln season:winter month:january seasonmap:north
ln season:winter month:february seasonmap:north
ln season:spring month:september seasonmap:south
ln season:spring month:october seasonmap:south
ln season:spring month:november seasonmap:south
ln season:summer month:december seasonmap:south
ln season:summer month:january seasonmap:south
ln season:summer month:february seasonmap:south
ln season:autumn month:march seasonmap:south
ln season:autumn month:april seasonmap:south
ln season:autumn month:may seasonmap:south
ln season:winter month:june seasonmap:south
ln season:winter month:july seasonmap:south
ln season:winter month:august seasonmap:south
ln season:year_round month:january seasonmap:north
ln season:year_round month:january seasonmap:south
ln season:year_round month:february seasonmap:north
ln season:year_round month:february seasonmap:south
ln season:year_round month:march seasonmap:north
ln season:year_round month:march seasonmap:south
ln season:year_round month:april seasonmap:north
ln season:year_round month:april seasonmap:south
ln season:year_round month:may seasonmap:north
ln season:year_round month:may seasonmap:south
ln season:year_round month:june seasonmap:north
ln season:year_round month:june seasonmap:south
ln season:year_round month:july seasonmap:north
ln season:year_round month:july seasonmap:south
ln season:year_round month:august seasonmap:north
ln season:year_round month:august seasonmap:south
ln season:year_round month:september seasonmap:north
ln season:year_round month:september seasonmap:south
ln season:year_round month:october seasonmap:north
ln season:year_round month:october seasonmap:south
ln season:year_round month:november seasonmap:north
ln season:year_round month:november seasonmap:south
ln season:year_round month:december seasonmap:north
ln season:year_round month:december seasonmap:south
