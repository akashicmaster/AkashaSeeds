# Akasha ontology — technique consolidation + heat-source axis.
# Near-synonymous techniques across cuisines are tied to a canonical node
# (technique:variant_of), and the more meaningful distinction — the heat
# source (charcoal/wood/gas…) — is made its own axis. Base pack.

def "technique:griddling" "Griddling — cooking on a flat hot metal/stone surface."
def "technique:clay_oven" "Clay-oven baking — radiant heat in a tandoor-type clay oven."
def "technique:hot_pot" "Hot pot — communal simmering of items in a shared pot of broth."

# ── consolidate near-synonyms to a canonical node ──
ln technique:yakimono technique:grilling technique:variant_of
ln technique:shioyaki technique:grilling technique:variant_of
ln technique:mangal technique:grilling technique:variant_of
ln technique:sis_kebab technique:grilling technique:variant_of
ln technique:bulgogi_grill technique:grilling technique:variant_of
ln technique:parrilla_venezolana technique:grilling technique:variant_of
ln technique:koz technique:grilling technique:variant_of
ln technique:a_la_plancha technique:griddling technique:variant_of
ln technique:comal technique:griddling technique:variant_of
ln technique:sac_griddle technique:griddling technique:variant_of
ln technique:tandir technique:clay_oven technique:variant_of
ln technique:tandoor technique:clay_oven technique:variant_of
ln technique:agemono technique:deep_frying technique:variant_of
ln technique:karaage technique:deep_frying technique:variant_of
ln technique:mushimono technique:steaming technique:variant_of
ln technique:nabemono technique:hot_pot technique:variant_of
ln technique:nimono technique:simmering technique:variant_of
# barbacoa & hangi are earth-oven (pit-steaming), NOT dry pit-barbecue —
# see technique_earth_oven.ak.
ln technique:low_and_slow technique:smoking technique:variant_of
ln technique:dhungar technique:smoking technique:variant_of

def "heat_source:charcoal" "炭 — charcoal."
def "heat_source:wood" "薪 — wood fire."
def "heat_source:gas" "gas flame."
def "heat_source:electric" "electric element."
def "heat_source:ember" "熾火 — glowing embers / hot stones."
def "heat_source:pit" "underground pit."
def "heat_source:infrared" "infrared/salamander."
def "heat_source:induction" "induction."

# ── heat source — the meaningful axis for fire cooking ──
ln technique:grilling heat_source:charcoal technique:heat_source
ln technique:grilling heat_source:wood technique:heat_source
ln technique:grilling heat_source:gas technique:heat_source
ln technique:mangal heat_source:charcoal technique:heat_source
ln technique:sis_kebab heat_source:charcoal technique:heat_source
ln technique:bulgogi_grill heat_source:charcoal technique:heat_source
ln technique:bulgogi_grill heat_source:gas technique:heat_source
ln technique:koz heat_source:ember technique:heat_source
ln technique:koz heat_source:charcoal technique:heat_source
ln technique:yakimono heat_source:charcoal technique:heat_source
ln technique:yakimono heat_source:gas technique:heat_source
ln technique:shioyaki heat_source:charcoal technique:heat_source
ln technique:shioyaki heat_source:gas technique:heat_source
ln technique:tandir heat_source:wood technique:heat_source
ln technique:tandir heat_source:charcoal technique:heat_source
ln technique:tandoor heat_source:charcoal technique:heat_source
ln technique:tandoor heat_source:wood technique:heat_source
ln technique:clay_oven heat_source:wood technique:heat_source
ln technique:clay_oven heat_source:charcoal technique:heat_source
ln technique:low_and_slow heat_source:wood technique:heat_source
ln technique:comal heat_source:gas technique:heat_source
ln technique:comal heat_source:wood technique:heat_source
ln technique:griddling heat_source:gas technique:heat_source
ln technique:griddling heat_source:electric technique:heat_source
ln technique:a_la_plancha heat_source:gas technique:heat_source
ln technique:a_la_plancha heat_source:electric technique:heat_source
ln technique:barbacoa heat_source:pit technique:heat_source
ln technique:barbacoa heat_source:wood technique:heat_source
ln technique:hangi heat_source:pit technique:heat_source
ln technique:hangi heat_source:ember technique:heat_source
ln technique:pit_barbecue heat_source:pit technique:heat_source
ln technique:pit_barbecue heat_source:wood technique:heat_source
