# Akasha ontology — namespace: tool
# atoms: 103

def "tool:dining:butter_knife" "Dull-edged knife used for spreading butter or jams."
ln tool:dining:butter_knife verb:cook:spread sys:refers_to

def "tool:dining:carafe" "Glass container without handles used for serving wine or water."

def "tool:dining:centerpiece" "Decorative object placed in the center of a dining table."
ln tool:dining:centerpiece verb:cook:decor sys:refers_to

def "tool:dining:charger_plate" "Large decorative base plate used during formal multi-course meals."

def "tool:dining:chopsticks" "Pair of slender sticks for gripping food, traditional in East Asia."

def "tool:dining:coaster" "Small mat placed under a glass to protect the table surface."

def "tool:dining:dining_knife" "Table knife for cutting prepared food at the table."
ln tool:dining:dining_knife verb:cook:cut sys:refers_to

def "tool:dining:finger_bowl" "Small bowl of water, often with lemon or petals, for rinsing fingers at the table."
ln tool:dining:finger_bowl verb:cook:wash sys:refers_to
ln tool:dining:finger_bowl water calc:associated_with
ln tool:dining:finger_bowl dna:smell:fragrant calc:associated_with

def "tool:dining:fork" "Utensil with tines for piercing, holding, and lifting food."

def "tool:dining:gravy_boat" "Elongated, boat-shaped pitcher used for serving sauces or gravy."
ln tool:dining:gravy_boat verb:cook:drizzle sys:refers_to

def "tool:dining:napkin" "Piece of cloth or paper used at meals for wiping the mouth and fingers."
ln tool:dining:napkin dna:texture:soft calc:associated_with

def "tool:dining:pepper_mill" "Grinder for crushing whole peppercorns directly onto food."
ln tool:dining:pepper_mill verb:cook:grind sys:refers_to
ln tool:dining:pepper_mill dna:smell:pungent calc:associated_with

def "tool:dining:pitcher" "Large container with a spout and handle for pouring liquids."

def "tool:dining:placemat" "Individual table mat for a single person's place setting."

def "tool:dining:plate" "Standard flat dish for serving or eating food."
ln tool:dining:plate verb:cook:plate sys:refers_to

def "tool:dining:platter" "Large flat dish used for serving food to multiple people."
ln tool:dining:platter verb:cook:plate sys:refers_to

def "tool:dining:salt_shaker" "Dispenser with perforated top for adding salt to food at the table."
ln tool:dining:salt_shaker verb:cook:season sys:refers_to
ln tool:dining:salt_shaker dna:taste:salty calc:associated_with

def "tool:dining:saucer" "Small shallow dish meant to hold a teacup or coffee cup."

def "tool:dining:soup_bowl" "Deep dish designed for serving soups, stews, or liquid-heavy foods."
ln tool:dining:soup_bowl verb:cook:plate sys:refers_to

def "tool:dining:soup_spoon" "Wide or deep-bowled spoon specifically for eating soup."

def "tool:dining:spoon" "Utensil with a shallow bowl for consuming liquids or soft foods."

def "tool:dining:tablecloth" "Cloth used to cover and protect the dining table."
ln tool:dining:tablecloth dna:texture:soft calc:associated_with

def "tool:dining:teacup" "Cup with a handle used for hot tea or coffee."

def "tool:dining:water_glass" "Standard tumbler or goblet for serving water."

def "tool:dining:wine_glass" "Stemmed glass designed to enhance the aroma and temperature of wine."
ln tool:dining:wine_glass dna:texture:smooth calc:associated_with

def "tool:large:blast_chiller" "Rapid thermal reduction unit for food safety and quality."
ln tool:large:blast_chiller process:cook_chill sys:part_of
ln tool:large:blast_chiller prop:power:high_voltage sys:is_a

def "tool:large:combi_oven" "Steam-injection thermal multi-function unit."
ln tool:large:combi_oven verb:cook:steam sys:refers_to
ln tool:large:combi_oven verb:cook:bake sys:refers_to
ln tool:large:combi_oven verb:cook:roast sys:refers_to
ln tool:large:combi_oven verb:cook:poach sys:refers_to
ln tool:large:combi_oven verb:cook:simmer sys:refers_to
ln tool:large:combi_oven process:cook_chill sys:part_of
ln tool:large:combi_oven tool:large:blast_chiller @pairs_with
ln tool:large:combi_oven prop:power:high_voltage sys:is_a
ln tool:large:combi_oven prop:power:gas sys:is_a

def "tool:large:deep_fryer" "Large-capacity fat-heating tank for immersion frying."
ln tool:large:deep_fryer verb:cook:deep_fry sys:refers_to
ln tool:large:deep_fryer prop:power:high_voltage sys:is_a

def "tool:large:freezer" "Standard frozen storage unit; holds below 0C."
ln tool:large:freezer cook:temp:ice_cold calc:associated_with

def "tool:large:hood" "Industrial smoke and heat extraction unit mounted above cooking line."
ln tool:large:hood verb:cook:smoke sys:refers_to

def "tool:large:oven" "Standard thermal baking and roasting unit."
ln tool:large:oven verb:cook:bake sys:refers_to
ln tool:large:oven verb:cook:roast sys:refers_to
ln tool:large:oven prop:power:gas sys:is_a

def "tool:large:range" "Combined stove and oven unit."

def "tool:large:refrigerator" "Standard cold storage unit; holds 0C - 5C."
ln tool:large:refrigerator cook:temp:chilled calc:associated_with

def "tool:large:salamander" "Overhead direct-broiling unit for finishing and glazing."
ln tool:large:salamander verb:cook:broil sys:refers_to
ln tool:large:salamander verb:cook:glaze sys:refers_to

def "tool:large:steam_kettle" "Jacketed steam-boiling vessel for high-volume liquid cooking."
ln tool:large:steam_kettle verb:cook:steam sys:refers_to
ln tool:large:steam_kettle verb:cook:boil sys:refers_to

def "tool:large:stove" "Top-mounted heating device for open-flame or electric cooking."
ln tool:large:stove verb:cook:boil sys:refers_to
ln tool:large:stove verb:cook:saute sys:refers_to
ln tool:large:stove prop:power:gas sys:is_a

def "tool:large:tilt_skillet" "Large tilting pan for braising, stewing, and shallow frying."
ln tool:large:tilt_skillet verb:cook:braise sys:refers_to
ln tool:large:tilt_skillet verb:cook:stew sys:refers_to
ln tool:large:tilt_skillet prop:power:gas sys:is_a

def "tool:large:vacuum_machine" "Commercial chamber vacuum sealer for preservation and sous-vide prep."
ln tool:large:vacuum_machine tool:large:combi_oven @pairs_with

def "tool:large:walk_in_cooler" "Room-scale cold storage for bulk ingredient holding."

def "tool:service:atomizer" "Small spray bottle for misting aromatic spirits or tinctures over a drink."
ln tool:service:atomizer dna:smell:fragrant @promotes

def "tool:service:bar_spoon" "Long-handled spoon for reaching the bottom of tall mixing glasses."
ln tool:service:bar_spoon process:mixology:stir @enables
ln tool:service:bar_spoon process:mixology:layer @enables

def "tool:service:boston_shaker" "Two-piece cocktail shaker: a large tin and a smaller tin or mixing glass."
ln tool:service:boston_shaker tool:service:shaker sys:is_a
ln tool:service:boston_shaker process:mixology:shake @enables
ln tool:service:boston_shaker dna:texture:crisp calc:associated_with

def "tool:service:citrus_squeezer" "Handheld press for extracting fresh juice from lemons and limes directly into a glass."

def "tool:service:cobbler_shaker" "Three-piece cocktail shaker with built-in strainer and cap."
ln tool:service:cobbler_shaker tool:service:shaker sys:is_a
ln tool:service:cobbler_shaker process:mixology:shake @enables

def "tool:service:coravin" "Wine preservation system extracting wine through the cork using argon gas, leaving the seal intact."
ln tool:service:coravin prop:service:oxidative @prevents

def "tool:service:corkscrew" "Lever or screw mechanism for pulling corks; specific class of wine opener."
ln tool:service:corkscrew tool:service:wine_opener sys:is_a

def "tool:service:decanter" "Vessel used for decanting wine to aerate and separate sediment."
ln tool:service:decanter verb:cook:aerate sys:refers_to
ln tool:service:decanter prop:service:oxidative @promotes

def "tool:service:fine_strainer" "Conical fine-mesh sieve used for double straining to remove ice shards and pulp."
ln tool:service:fine_strainer process:mixology:double_strain @enables

def "tool:service:foil_cutter" "Small rotary or blade tool for cleanly removing the foil capsule from a wine bottle."

def "tool:service:hawthorne_strainer" "Spring-loaded tool for straining cocktails while holding back ice."

def "tool:service:ice_bucket" "Insulated vessel for keeping drinks chilled at the table."

def "tool:service:ice_pick" "Pointed tool for breaking or hand-carving clear ice blocks."

def "tool:service:jigger" "Precision measuring cup for spirits and mixers."

def "tool:service:julep_strainer" "Perforated bowl-shaped strainer used with a mixing glass to hold back ice while pouring."
ln tool:service:julep_strainer process:mixology:stir @complements

def "tool:service:mixing_glass" "Heavy-walled vessel for stirring cocktails."

def "tool:service:muddler" "Tool for crushing fruits, herbs, or spices in a glass to release juices."
ln tool:service:muddler verb:cook:crush sys:refers_to
ln tool:service:muddler verb:cook:infuse sys:refers_to
ln tool:service:muddler dna:smell:fragrant calc:associated_with
ln tool:service:muddler verb:cook:press sys:refers_to
ln tool:service:muddler process:mixology:infusion @promotes

def "tool:service:shaker" "Vessel for vigorously mixing and chilling cocktails with ice."
ln tool:service:shaker dna:texture:crisp calc:associated_with

def "tool:service:speed_pourer" "Spout attached to a liquor bottle for fast and accurate free pouring."

def "tool:service:tastevin" "Traditional shallow silver cup used by sommeliers for evaluating wine color and aroma."
ln tool:service:tastevin verb:cook:taste sys:refers_to

def "tool:service:wine_opener" "Lever or screw device for removing corks from bottles."

def "tool:service:wine_stopper" "Device to seal open wine bottles to prevent oxidation."
ln tool:service:wine_stopper prop:service:oxidative @prevents

def "tool:small:bain_marie" "Traditional water bath setup for gentle, indirect heating."
ln tool:small:bain_marie verb:cook:melt sys:refers_to
ln tool:small:bain_marie verb:cook:poach sys:refers_to

def "tool:small:bench_scraper" "Flat blade for manipulating dough, dividing, and cleaning surfaces."
ln tool:small:bench_scraper verb:cook:portion sys:refers_to
ln tool:small:bench_scraper verb:cook:cut sys:refers_to

def "tool:small:blender" "High-speed liquid and solid pulverizer."
ln tool:small:blender verb:cook:puree sys:refers_to
ln tool:small:blender verb:cook:blend sys:refers_to

def "tool:small:cast_iron_skillet" "Heavy heat-retaining pan for searing and baking."
ln tool:small:cast_iron_skillet verb:cook:sear sys:refers_to

def "tool:small:chinois" "Conical sieve with an extremely fine mesh for smooth purees and soups."
ln tool:small:chinois verb:cook:strain sys:refers_to
ln tool:small:chinois verb:cook:clarify sys:refers_to
ln tool:small:chinois dna:texture:smooth calc:associated_with

def "tool:small:copper_bowl" "Traditional unlined copper bowl used to chemically stabilize egg white foams."
ln tool:small:copper_bowl verb:cook:whip sys:refers_to
ln tool:small:copper_bowl verb:cook:aerate sys:refers_to
ln tool:small:copper_bowl dna:texture:soft calc:associated_with

def "tool:small:culinary_siphon" "Pressurized canister (using N2O or CO2) for creating foams, espumas, and rapid infusions."
ln tool:small:culinary_siphon verb:cook:aerate sys:refers_to
ln tool:small:culinary_siphon verb:cook:infuse sys:refers_to
ln tool:small:culinary_siphon dna:texture:soft calc:associated_with

def "tool:small:cutting_board" "Surface for safely cutting ingredients."
ln tool:small:cutting_board prop:cook:manual sys:is_a
ln tool:small:cutting_board haccp:cross_contamination @can_cause

def "tool:small:digital_scale" "High-precision measurement device for mass, crucial for modern baking and hydrocolloids."
ln tool:small:digital_scale verb:cook:weigh sys:refers_to
ln tool:small:digital_scale unit:base:gram sys:refers_to

def "tool:small:dutch_oven" "Heavy cast-iron pot with a tight-fitting lid for slow cooking and braising."
ln tool:small:dutch_oven verb:cook:braise sys:refers_to
ln tool:small:dutch_oven verb:cook:stew sys:refers_to
ln tool:small:dutch_oven verb:cook:bake sys:refers_to

def "tool:small:food_processor" "Motorized tool for rapid chopping, slicing, and mixing."
ln tool:small:food_processor verb:cook:chop sys:refers_to

def "tool:small:grater" "Tool with sharp perforations for shredding food."
ln tool:small:grater verb:cook:grate sys:refers_to
ln tool:small:grater prop:cook:manual sys:is_a

def "tool:small:hand_grinder" "Manual crank-operated machine for mincing meat."
ln tool:small:hand_grinder prop:cook:manual sys:is_a
ln tool:small:hand_grinder verb:cook:mince sys:refers_to

def "tool:small:knife" "Standard blade for cutting, slicing, and chopping."
ln tool:small:knife verb:cook:cut sys:refers_to
ln tool:small:knife verb:cook:slice sys:refers_to
ln tool:small:knife verb:cook:chop sys:refers_to
ln tool:small:knife verb:cook:mince sys:refers_to
ln tool:small:knife verb:cook:dice sys:refers_to
ln tool:small:knife prop:cook:manual sys:is_a

def "tool:small:ladle" "Deep spoon for serving liquids and soups."
ln tool:small:ladle prop:cook:manual sys:is_a

def "tool:small:marble_slab" "Cold stone surface used for tempering chocolate and working pastry dough."
ln tool:small:marble_slab dna:touch:cool calc:associated_with
ln tool:small:marble_slab verb:cook:cool sys:refers_to

def "tool:small:mezzaluna" "Curved blade with two handles for rocking chop."
ln tool:small:mezzaluna verb:cook:mince sys:refers_to
ln tool:small:mezzaluna verb:cook:chop sys:refers_to

def "tool:small:micro_puree_machine" "High-speed precision shaver for creating ultra-smooth textures from deep-frozen bases (e.g., Pacojet)."
ln tool:small:micro_puree_machine verb:cook:puree sys:refers_to
ln tool:small:micro_puree_machine dna:texture:smooth calc:associated_with
ln tool:small:micro_puree_machine verb:cook:freeze calc:associated_with

def "tool:small:mixing_bowl" "Hemispherical container for preparing ingredients."
ln tool:small:mixing_bowl prop:cook:manual sys:is_a

def "tool:small:mortar_and_pestle" "Traditional heavy bowl and club for crushing and grinding."
ln tool:small:mortar_and_pestle prop:cook:manual sys:is_a
ln tool:small:mortar_and_pestle verb:cook:crush sys:refers_to
ln tool:small:mortar_and_pestle verb:cook:grind sys:refers_to
ln tool:small:mortar_and_pestle verb:cook:pound sys:refers_to

def "tool:small:pan" "Shallow container for frying and sautéing."
ln tool:small:pan verb:cook:saute sys:refers_to
ln tool:small:pan verb:cook:fry sys:refers_to

def "tool:small:pastry_blender" "Hand tool with metal strips for cutting solid fat into flour."
ln tool:small:pastry_blender prop:cook:manual sys:is_a
ln tool:small:pastry_blender verb:cook:incorporate sys:refers_to
ln tool:small:pastry_blender verb:cook:cut sys:refers_to

def "tool:small:pastry_brush" "Tool for applying glazes, egg washes, or marinades."
ln tool:small:pastry_brush verb:cook:glaze sys:refers_to
ln tool:small:pastry_brush verb:cook:baste sys:refers_to

def "tool:small:peeler" "Handheld tool for removing the outer skin of produce."
ln tool:small:peeler verb:cook:peel sys:refers_to
ln tool:small:peeler prop:cook:manual sys:is_a

def "tool:small:piping_bag" "Cone-shaped bag for extruding semi-solid foods and decoration."
ln tool:small:piping_bag verb:cook:garnish sys:refers_to
ln tool:small:piping_bag verb:cook:decor sys:refers_to

def "tool:small:pot" "Deep container for boiling, simmering, and stewing."
ln tool:small:pot verb:cook:boil sys:refers_to
ln tool:small:pot verb:cook:simmer sys:refers_to
ln tool:small:pot verb:cook:stew sys:refers_to

def "tool:small:probe_thermometer" "Instant-read digital tool for checking internal food temperature."
ln tool:small:probe_thermometer verb:cook:measure sys:refers_to
ln tool:small:probe_thermometer unit:base:celsius sys:refers_to
ln tool:small:probe_thermometer haccp:monitoring @enables

def "tool:small:rolling_pin" "Cylindrical tool for flattening dough."
ln tool:small:rolling_pin prop:cook:manual sys:is_a
ln tool:small:rolling_pin verb:cook:roll sys:refers_to
ln tool:small:rolling_pin verb:cook:press sys:refers_to

def "tool:small:saucepan" "Small deep pan with a long handle for sauces."

def "tool:small:smoking_gun" "Handheld device for injecting cold smoke into enclosed containers."
ln tool:small:smoking_gun verb:cook:smoke sys:refers_to
ln tool:small:smoking_gun dna:smell:pungent calc:associated_with

def "tool:small:sous_vide_circulator" "Precision immersion heater for maintaining exact water bath temperatures."
ln tool:small:sous_vide_circulator verb:cook:poach sys:refers_to

def "tool:small:spatula" "Flexible flat utensil for scraping or flipping."
ln tool:small:spatula prop:cook:manual sys:is_a

def "tool:small:spice_grinder" "Small motorized mill for pulverizing dry spices."
ln tool:small:spice_grinder verb:cook:grind sys:refers_to

def "tool:small:stand_mixer" "Heavy-duty motorized mixer for doughs, batters, and whipping."
ln tool:small:stand_mixer verb:cook:knead sys:refers_to
ln tool:small:stand_mixer verb:cook:whip sys:refers_to

def "tool:small:strainer" "Fine mesh wire bowl for filtering liquids."
ln tool:small:strainer verb:cook:strain sys:refers_to
ln tool:small:strainer verb:cook:sift sys:refers_to
ln tool:small:strainer prop:cook:manual sys:is_a

def "tool:small:tamis" "Drum sieve for aerating flour or passing purees smoothly."
ln tool:small:tamis verb:cook:sift sys:refers_to
ln tool:small:tamis verb:cook:puree sys:refers_to
ln tool:small:tamis dna:texture:smooth calc:associated_with

def "tool:small:tart_pan" "Shallow pan with fluted edges and often a removable bottom."
ln tool:small:tart_pan verb:cook:bake sys:refers_to

def "tool:small:tongs" "Gripping tool for handling hot or delicate food."
ln tool:small:tongs prop:cook:manual sys:is_a

def "tool:small:vacuum_sealer" "Device for removing oxygen from packaging to preserve food or cook sous-vide."
ln tool:small:vacuum_sealer verb:cook:store sys:refers_to
ln tool:small:vacuum_sealer verb:cook:marinate sys:refers_to
ln tool:small:vacuum_sealer prop:cook:anaerobic sys:is_a
ln tool:small:vacuum_sealer haccp:biological_hazard @can_prevent

def "tool:small:whisk" "Wire loop utensil for beating and incorporating air."
ln tool:small:whisk verb:cook:whisk sys:refers_to
ln tool:small:whisk verb:cook:emulsify sys:refers_to
ln tool:small:whisk verb:cook:aerate sys:refers_to
ln tool:small:whisk prop:cook:manual sys:is_a

def "tool:small:wok" "Round-bottomed pan for high-heat stir-frying."
ln tool:small:wok verb:cook:stir_fry sys:refers_to

def "tool:small:wooden_spoon" "Traditional utensil for stirring, preventing metallic taste and scratching."
ln tool:small:wooden_spoon verb:cook:stir sys:refers_to
ln tool:small:wooden_spoon verb:cook:fold sys:refers_to
