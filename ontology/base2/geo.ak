# Akasha ontology — namespace: geo
# atoms: 74

def "geo.ref.airport.us" "Namespace anchor for US airport reference atoms (geo:airport:{IATA}). 221 airports from plotly/datasets airport traffic 2011."
ln geo.ref.airport.us ont.geo_ref sys:part_of
ln geo.ref.airport.us ont.geo thesaurus:related
set.add name="ontology.earth" id="geo.ref.airport.us"

def "geo.ref.city.us" "Namespace anchor for US city reference atoms (geo:city:us:{slug}). 2739 cities from plotly/datasets US cities 2014."
ln geo.ref.city.us ont.geo_ref sys:part_of
ln geo.ref.city.us ont.geo thesaurus:related
set.add name="ontology.earth" id="geo.ref.city.us"

def "geo.ref.country" "Namespace anchor for world country reference atoms (geo:country:{ISO3}). 221 countries loaded from plotly/datasets world GDP 2014."
ln geo.ref.country ont.geo_ref sys:part_of
ln geo.ref.country ont.country thesaurus:related
set.add name="ontology.earth" id="geo.ref.country"

def "geo:adjacent_to" "Two places share a boundary or are immediately beside each other."
ln geo:adjacent_to ont.geo sys:part_of
ln geo:adjacent_to geo:near thesaurus:hyponym

def "geo:class:carbonate_mineral" "Minerals containing the carbonate ion (CO3²⁻)."

def "geo:class:halide_mineral" "Minerals with a dominant halide anion (F⁻, Cl⁻, Br⁻, I⁻)."

def "geo:class:oxide_mineral" "Minerals in which the oxide anion (O²⁻) is bonded to one or more metal cations."

def "geo:class:silicate_mineral" "Rock-forming minerals made up of silicate groups, constituting the largest and most important class of minerals."

def "geo:class:sulfide_mineral" "Minerals containing sulfur in its lowest oxidation number as the major anion."

def "geo:concept:clarke_number" "The relative abundance of chemical elements in the Earth's crust."

def "geo:concept:elemental_abundance" "The measure of how common an element is in a given environment."

def "geo:concept:native_element" "Elements that occur in nature in uncombined form with a distinct mineral structure."
ln geo:concept:native_element chem:element:gold sys:associated_with
ln geo:concept:native_element chem:element:copper sys:associated_with
ln geo:concept:native_element chem:element:sulfur sys:associated_with
ln geo:concept:native_element chem:element:carbon sys:associated_with

def "geo:contains" "A place physically contains another (e.g. a region contains a settlement)."
ln geo:contains ont.geo sys:part_of
ln geo:contains geo:is_in thesaurus:antonym

def "geo:continent:africa" "Africa — second-largest continent by area and population; 54 recognised sovereign states."
ln geo:continent:africa ont.earth.enrichment sys:part_of
set.add name="ontology.earth.enrichment" id="geo:continent:africa"

def "geo:continent:antarctica" "Antarctica — southernmost continent; governed by the Antarctic Treaty System; no permanent population."
ln geo:continent:antarctica ont.earth.enrichment sys:part_of
set.add name="ontology.earth.enrichment" id="geo:continent:antarctica"

def "geo:continent:asia" "Asia — largest continent by area and population; home to more than 60% of the world's people."
ln geo:continent:asia ont.earth.enrichment sys:part_of
set.add name="ontology.earth.enrichment" id="geo:continent:asia"

def "geo:continent:europe" "Europe — western peninsula of Eurasia; bounded by the Atlantic, Arctic, and Mediterranean."
ln geo:continent:europe ont.earth.enrichment sys:part_of
set.add name="ontology.earth.enrichment" id="geo:continent:europe"

def "geo:continent:north_america" "North America — continent comprising Canada, the United States, Mexico, Central America, and the Caribbean."
ln geo:continent:north_america ont.earth.enrichment sys:part_of
set.add name="ontology.earth.enrichment" id="geo:continent:north_america"

def "geo:continent:oceania" "Oceania — Australia, New Zealand, and the Pacific island nations of Melanesia, Micronesia, and Polynesia."
ln geo:continent:oceania ont.earth.enrichment sys:part_of
set.add name="ontology.earth.enrichment" id="geo:continent:oceania"

def "geo:continent:south_america" "South America — continent comprising twelve sovereign countries south of the Panama isthmus."
ln geo:continent:south_america ont.earth.enrichment sys:part_of
set.add name="ontology.earth.enrichment" id="geo:continent:south_america"

def "geo:from_dataset" "An entity atom was derived from or belongs to a specific source dataset atom."
ln geo:from_dataset ont.geo sys:part_of
set.add name="ontology.earth" id="geo:from_dataset"

def "geo:gdp_tier:high" "High economy — GDP above $500 billion. G7 and major emerging economies."
ln geo:gdp_tier:high ont.earth.enrichment sys:part_of
set.add name="ontology.earth.enrichment" id="geo:gdp_tier:high"

def "geo:gdp_tier:low" "Low economy — GDP below $5 billion."
ln geo:gdp_tier:low ont.earth.enrichment sys:part_of
set.add name="ontology.earth.enrichment" id="geo:gdp_tier:low"

def "geo:gdp_tier:lower_middle" "Lower-middle economy — GDP $5–50 billion."
ln geo:gdp_tier:lower_middle ont.earth.enrichment sys:part_of
ln geo:gdp_tier:lower_middle geo:gdp_tier:upper_middle thesaurus:hyponym
set.add name="ontology.earth.enrichment" id="geo:gdp_tier:lower_middle"

def "geo:gdp_tier:upper_middle" "Upper-middle economy — GDP $50–500 billion."
ln geo:gdp_tier:upper_middle ont.earth.enrichment sys:part_of
ln geo:gdp_tier:upper_middle geo:gdp_tier:high thesaurus:hyponym
set.add name="ontology.earth.enrichment" id="geo:gdp_tier:upper_middle"

def "geo:has_connection" "A place is explicitly connected to another place via a typed spatial relationship (adjacent, overlaps, route, visible_from, etc.)."
ln geo:has_connection ont.geo sys:part_of

def "geo:has_coordinate" "A geo instance has a coordinate entry (lat/lon, UTM, etc.) in the given coordinate system."
ln geo:has_coordinate ont.geo sys:part_of
set.add name="ontology.earth" id="geo:has_coordinate"

def "geo:has_event" "A place has a dated spatial event (discovery, destruction, rename, boundary change, etc.)."
ln geo:has_event ont.geo sys:part_of
set.add name="ontology.earth" id="geo:has_event"

def "geo:has_feature" "A place has a notable physical or political feature (natural, built, archaeological, political, infrastructure, symbolic)."
ln geo:has_feature ont.geo sys:part_of
set.add name="ontology.earth" id="geo:has_feature"

def "geo:has_layer" "A geo instance has an abstract overlay layer (thematic, temporal, or analytical)."
ln geo:has_layer ont.geo sys:part_of

def "geo:has_observation" "A place has an associated field or remote observation record."
ln geo:has_observation ont.geo sys:part_of
set.add name="ontology.earth" id="geo:has_observation"

def "geo:has_place" "A GeoConcept root contains a named place entity (site, region, landmark, world_place, etc.)."
ln geo:has_place ont.geo sys:part_of
set.add name="ontology.earth" id="geo:has_place"

def "geo:has_state" "A place has a recorded state (current or historical condition snapshot)."
ln geo:has_state ont.geo sys:part_of

def "geo:is_in" "Spatial containment or jurisdictional membership. city geo:is_in country; airport geo:is_in city. Directional: contained → container."
ln geo:is_in ont.geo sys:part_of
ln geo:is_in geo:contains thesaurus:antonym
set.add name="ontology.earth" id="geo:is_in"

def "geo:layer:atmosphere" "A layer of gas or layers of gases that envelop a planet, held in place by the gravity of the planetary body."
ln geo:layer:atmosphere chem:compound:dinitrogen @rich_in
ln geo:layer:atmosphere chem:element:oxygen @rich_in
ln geo:layer:atmosphere chem:compound:carbon_dioxide @contains

def "geo:layer:crust" "The outermost solid shell of a rocky planet, dwarf planet, or natural satellite."
ln geo:layer:crust geo:concept:clarke_number @measured_by
ln geo:layer:crust chem:element:oxygen @rich_in
ln geo:layer:crust chem:element:silicon @rich_in
ln geo:layer:crust chem:element:aluminum @rich_in
ln geo:layer:crust chem:element:iron @rich_in
ln geo:layer:crust chem:compound:silica @abundant_in

def "geo:layer:hydrosphere" "The combined mass of water found on, under, and above the surface of a planet."
ln geo:layer:hydrosphere chem:compound:water @composed_of

def "geo:layer:inner_core" "The innermost geologic layer of planet Earth, primarily a solid ball with a radius of about 1,220 km."
ln geo:layer:inner_core chem:element:iron @rich_in
ln geo:layer:inner_core chem:element:nickel @rich_in
ln geo:layer:inner_core phys:state:solid sys:is_a

def "geo:layer:mantle" "A layer inside a planetary body bounded below by a core and above by a crust; largely made of silicate rock."
ln geo:layer:mantle geo:class:silicate_mineral @rich_in
ln geo:layer:mantle chem:element:magnesium @rich_in
ln geo:layer:mantle chem:element:silicon @rich_in

def "geo:layer:outer_core" "A fluid layer composed of mostly iron and nickel that lies above Earth's solid inner core and below its mantle."
ln geo:layer:outer_core chem:element:iron @rich_in
ln geo:layer:outer_core chem:element:nickel @rich_in
ln geo:layer:outer_core phys:state:liquid sys:is_a

def "geo:mineral:calcite" "A carbonate mineral and the most stable polymorph of calcium carbonate (CaCO₃)."
ln geo:mineral:calcite geo:class:carbonate_mineral sys:is_a
ln geo:mineral:calcite chem:element:calcium @composed_of
ln geo:mineral:calcite chem:element:carbon @composed_of

def "geo:mineral:corundum" "A crystalline form of aluminum oxide typically containing traces of iron, titanium, vanadium and chromium."
ln geo:mineral:corundum geo:class:oxide_mineral sys:is_a
ln geo:mineral:corundum chem:element:aluminum @composed_of
ln geo:mineral:corundum chem:element:chromium @doped_with
ln geo:mineral:corundum phys:optics:d_d_transition @exhibits

def "geo:mineral:diamond" "A solid form of the element carbon with its atoms arranged in a crystal structure called diamond cubic."
ln geo:mineral:diamond chem:element:carbon @composed_of
ln geo:mineral:diamond geo:mineral:graphite @polymorph_of
ln geo:mineral:diamond mat:prop:hardness @exhibits_maximum

def "geo:mineral:feldspar" "A group of rock-forming tectosilicate minerals that make up about 41% of the Earth's continental crust by weight."
ln geo:mineral:feldspar geo:class:silicate_mineral sys:is_a

def "geo:mineral:graphite" "A crystalline form of the element carbon with its atoms arranged in a hexagonal structure."
ln geo:mineral:graphite chem:element:carbon @composed_of
ln geo:mineral:graphite mat:prop:hardness @exhibits_minimum
ln geo:mineral:graphite dna:color:black calc:associated_with

def "geo:mineral:halite" "Commonly known as rock salt, a type of salt that is the mineral form of sodium chloride (NaCl)."
ln geo:mineral:halite geo:class:halide_mineral sys:is_a
ln geo:mineral:halite chem:element:sodium @composed_of
ln geo:mineral:halite chem:element:chlorine @composed_of

def "geo:mineral:pyrite" "An iron sulfide mineral with a pale brass-yellow hue, also known as fool's gold."
ln geo:mineral:pyrite geo:class:sulfide_mineral sys:is_a
ln geo:mineral:pyrite chem:element:iron @composed_of
ln geo:mineral:pyrite chem:element:sulfur @composed_of
ln geo:mineral:pyrite dna:color:yellow calc:associated_with

def "geo:mineral:quartz" "A hard, crystalline mineral composed of silica (silicon dioxide)."
ln geo:mineral:quartz geo:class:silicate_mineral sys:is_a
ln geo:mineral:quartz chem:element:silicon @composed_of
ln geo:mineral:quartz chem:element:oxygen @composed_of

def "geo:near" "Two places are in proximity within a contextually meaningful distance."
ln geo:near ont.geo sys:part_of
ln geo:near geo:adjacent_to thesaurus:hypernym

def "geo:prop:cleavage" "The tendency of a crystalline material to split along definite crystallographic structural planes."

def "geo:prop:luster" "The way light interacts with the surface of a crystal, rock, or mineral."

def "geo:prop:streak" "The color of the powder produced when a mineral is dragged across an un-weathered surface."

def "geo:region:australia_new_zealand" "UN M.49: Australia and New Zealand."
ln geo:region:australia_new_zealand geo:continent:oceania sys:part_of
set.add name="ontology.earth.enrichment" id="geo:region:australia_new_zealand"

def "geo:region:caribbean" "UN M.49: Caribbean — Antigua and Barbuda, Bahamas, Barbados, Cuba, Dominica, Dominican Republic, Grenada, Haiti, Jamaica, Saint Kitts and Nevis, Saint Lucia, Saint Vincent, Trinidad and Tobago."
ln geo:region:caribbean geo:continent:north_america sys:part_of
set.add name="ontology.earth.enrichment" id="geo:region:caribbean"

def "geo:region:central_america" "UN M.49: Central America — Belize, Costa Rica, El Salvador, Guatemala, Honduras, Nicaragua, Panama."
ln geo:region:central_america geo:continent:north_america sys:part_of
set.add name="ontology.earth.enrichment" id="geo:region:central_america"

def "geo:region:central_asia" "UN M.49: Central Asia — Kazakhstan, Kyrgyzstan, Tajikistan, Turkmenistan, Uzbekistan."
ln geo:region:central_asia geo:continent:asia sys:part_of
set.add name="ontology.earth.enrichment" id="geo:region:central_asia"

def "geo:region:eastern_africa" "UN M.49: Eastern Africa — Burundi, Comoros, Djibouti, Eritrea, Ethiopia, Kenya, Madagascar, Malawi, Mauritius, Mozambique, Rwanda, Somalia, South Sudan, Tanzania, Uganda."
ln geo:region:eastern_africa geo:continent:africa sys:part_of
set.add name="ontology.earth.enrichment" id="geo:region:eastern_africa"

def "geo:region:eastern_asia" "UN M.49: Eastern Asia — China, Japan, South Korea, North Korea, Mongolia."
ln geo:region:eastern_asia geo:continent:asia sys:part_of
set.add name="ontology.earth.enrichment" id="geo:region:eastern_asia"

def "geo:region:eastern_europe" "UN M.49: Eastern Europe — Belarus, Bulgaria, Czech Republic, Hungary, Moldova, Poland, Romania, Russia, Slovakia, Ukraine."
ln geo:region:eastern_europe geo:continent:europe sys:part_of
set.add name="ontology.earth.enrichment" id="geo:region:eastern_europe"

def "geo:region:melanesia" "UN M.49: Melanesia — Fiji, Papua New Guinea, Solomon Islands, Vanuatu."
ln geo:region:melanesia geo:continent:oceania sys:part_of
set.add name="ontology.earth.enrichment" id="geo:region:melanesia"

def "geo:region:micronesia" "UN M.49: Micronesia — Federated States of Micronesia, Kiribati, Marshall Islands, Nauru, Palau."
ln geo:region:micronesia geo:continent:oceania sys:part_of
set.add name="ontology.earth.enrichment" id="geo:region:micronesia"

def "geo:region:middle_africa" "UN M.49: Middle/Central Africa — Angola, Cameroon, Central African Republic, Chad, Congo, DR Congo, Equatorial Guinea, Gabon, São Tomé and Príncipe."
ln geo:region:middle_africa geo:continent:africa sys:part_of
set.add name="ontology.earth.enrichment" id="geo:region:middle_africa"

def "geo:region:northern_africa" "UN M.49: Northern Africa — Algeria, Egypt, Libya, Morocco, Sudan, Tunisia."
ln geo:region:northern_africa geo:continent:africa sys:part_of
set.add name="ontology.earth.enrichment" id="geo:region:northern_africa"

def "geo:region:northern_america" "UN M.49: Northern America — Canada, Mexico, United States."
ln geo:region:northern_america geo:continent:north_america sys:part_of
set.add name="ontology.earth.enrichment" id="geo:region:northern_america"

def "geo:region:northern_europe" "UN M.49: Northern Europe — Denmark, Estonia, Finland, Iceland, Ireland, Latvia, Lithuania, Norway, Sweden, United Kingdom."
ln geo:region:northern_europe geo:continent:europe sys:part_of
set.add name="ontology.earth.enrichment" id="geo:region:northern_europe"

def "geo:region:polynesia" "UN M.49: Polynesia — Samoa, Tonga, Tuvalu."
ln geo:region:polynesia geo:continent:oceania sys:part_of
set.add name="ontology.earth.enrichment" id="geo:region:polynesia"

def "geo:region:south_america" "UN M.49: South America — Argentina, Bolivia, Brazil, Chile, Colombia, Ecuador, Guyana, Paraguay, Peru, Suriname, Uruguay, Venezuela."
ln geo:region:south_america geo:continent:south_america sys:part_of
set.add name="ontology.earth.enrichment" id="geo:region:south_america"

def "geo:region:southeastern_asia" "UN M.49: South-eastern Asia — Brunei, Cambodia, Timor-Leste, Indonesia, Laos, Malaysia, Myanmar, Philippines, Singapore, Thailand, Vietnam."
ln geo:region:southeastern_asia geo:continent:asia sys:part_of
set.add name="ontology.earth.enrichment" id="geo:region:southeastern_asia"

def "geo:region:southern_africa" "UN M.49: Southern Africa — Botswana, Eswatini, Lesotho, Namibia, South Africa, Zimbabwe, Zambia."
ln geo:region:southern_africa geo:continent:africa sys:part_of
set.add name="ontology.earth.enrichment" id="geo:region:southern_africa"

def "geo:region:southern_asia" "UN M.49: Southern Asia — Afghanistan, Bangladesh, Bhutan, India, Iran, Maldives, Nepal, Pakistan, Sri Lanka."
ln geo:region:southern_asia geo:continent:asia sys:part_of
set.add name="ontology.earth.enrichment" id="geo:region:southern_asia"

def "geo:region:southern_europe" "UN M.49: Southern Europe — Albania, Andorra, Bosnia, Croatia, Greece, Holy See, Italy, Malta, Montenegro, Portugal, San Marino, Serbia, Slovenia, Spain, North Macedonia."
ln geo:region:southern_europe geo:continent:europe sys:part_of
set.add name="ontology.earth.enrichment" id="geo:region:southern_europe"

def "geo:region:western_africa" "UN M.49: Western Africa — Benin, Burkina Faso, Cabo Verde, Côte d'Ivoire, Gambia, Ghana, Guinea, Guinea-Bissau, Liberia, Mali, Mauritania, Niger, Nigeria, Senegal, Sierra Leone, Togo."
ln geo:region:western_africa geo:continent:africa sys:part_of
set.add name="ontology.earth.enrichment" id="geo:region:western_africa"

def "geo:region:western_asia" "UN M.49: Western Asia — Armenia, Azerbaijan, Bahrain, Cyprus, Georgia, Iraq, Israel, Jordan, Kuwait, Lebanon, Oman, Palestine, Qatar, Saudi Arabia, Syria, Turkey, UAE, Yemen."
ln geo:region:western_asia geo:continent:asia sys:part_of
set.add name="ontology.earth.enrichment" id="geo:region:western_asia"

def "geo:region:western_europe" "UN M.49: Western Europe — Austria, Belgium, France, Germany, Liechtenstein, Luxembourg, Monaco, Netherlands, Switzerland."
ln geo:region:western_europe geo:continent:europe sys:part_of
set.add name="ontology.earth.enrichment" id="geo:region:western_europe"
