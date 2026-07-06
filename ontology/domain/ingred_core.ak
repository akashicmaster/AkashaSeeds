# Akasha ontology — namespace: ingred
# atoms: 226

def "ingred:additive:agar_agar" "A jelly-like substance obtained from red algae, used as a vegetarian gelatin substitute."
ln ingred:additive:agar_agar sci:cook:coagulation @promotes

def "ingred:additive:calcium_chloride" "A calcium salt used in conjunction with sodium alginate to trigger gelation."
ln ingred:additive:calcium_chloride sci:cook:spherification @requires

def "ingred:additive:lecithin" "A fat essential in cells, widely used as a natural emulsifier and to create culinary foams."
ln ingred:additive:lecithin sci:cook:emulsification @promotes

def "ingred:additive:sodium_alginate" "An extract of brown seaweed used as a gelling agent, critical for spherification."
ln ingred:additive:sodium_alginate sci:cook:spherification @requires

def "ingred:additive:xanthan_gum" "A polysaccharide used universally as a food additive to thicken and stabilize emulsions."
ln ingred:additive:xanthan_gum dna:texture:viscous @promotes

def "ingred:blend:chaat_masala" "A funky, tart, and salty Indian spice blend used as a finishing garnish, heavily featuring amchur and black salt."
ln ingred:blend:chaat_masala dna:taste:sour calc:associated_with
ln ingred:blend:chaat_masala ingred:spice:amchur @contains

def "ingred:blend:curry_powder" "A British-invented spice blend designed to mimic the flavors of Indian cooking."

def "ingred:blend:five_spice" "A Chinese blend encompassing all five tastes, typically containing star anise, cloves, cinnamon, fennel, and pepper."
ln ingred:blend:five_spice cuisine:chinese calc:associated_with

def "ingred:blend:garam_masala" "A warming, aromatic Indian spice blend, typically added near the end of cooking."
ln ingred:blend:garam_masala ingred:spice:cardamom @contains
ln ingred:blend:garam_masala ingred:spice:cinnamon @contains
ln ingred:blend:garam_masala ingred:spice:clove @contains
ln ingred:blend:garam_masala cuisine:indian calc:associated_with

def "ingred:blend:panch_phoran" "A Bengali five-spice blend consisting of whole cumin, mustard, fenugreek, nigella, and fennel seeds."
ln ingred:blend:panch_phoran ingred:spice:cumin @contains
ln ingred:blend:panch_phoran ingred:spice:mustard_seed @contains
ln ingred:blend:panch_phoran ingred:spice:fenugreek @contains
ln ingred:blend:panch_phoran ingred:spice:nigella_seed @contains
ln ingred:blend:panch_phoran cuisine:indian calc:associated_with

def "ingred:blend:ras_el_hanout" "A complex, aromatic North African spice mix often containing dozens of spices."

def "ingred:blend:zaatar" "A Middle Eastern blend of thyme, oregano, sumac, and toasted sesame seeds."
ln ingred:blend:zaatar cuisine:levantine calc:associated_with

def "ingred:condiment:butter" "A dairy product made from the fat and protein components of churned cream."
ln ingred:condiment:butter chem:fatty_acid:saturated_fatty_acid @rich_in
ln ingred:condiment:butter chem:odor:diacetyl @contains

def "ingred:condiment:fish_sauce" "A liquid condiment made from fish or krill that have been coated in salt and fermented."
ln ingred:condiment:fish_sauce dna:taste:umami calc:associated_with
ln ingred:condiment:fish_sauce dna:smell:pungent calc:associated_with

def "ingred:condiment:gochujang" "A savory, sweet, and spicy fermented condiment made from chili powder, glutinous rice, and soybeans."

def "ingred:condiment:honey" "A sweet, viscous food substance made by bees."
ln ingred:condiment:honey dna:taste:sweet calc:associated_with
ln ingred:condiment:honey dna:texture:viscous calc:associated_with

def "ingred:condiment:ketchup" "A sweet and tangy sauce, typically made from tomatoes, sugar, and vinegar."

def "ingred:condiment:maple_syrup" "A syrup usually made from the xylem sap of sugar maple trees."

def "ingred:condiment:mayonnaise" "A thick, cold, and creamy emulsion of oil, egg yolk, and acid."
ln ingred:condiment:mayonnaise dna:texture:viscous calc:associated_with
ln ingred:condiment:mayonnaise sci:cook:emulsion sys:is_a

def "ingred:condiment:mirin" "A type of rice wine similar to sake, but with a lower alcohol content and higher sugar content."
ln ingred:condiment:mirin dna:taste:sweet calc:associated_with

def "ingred:condiment:miso" "A traditional Japanese seasoning produced by fermenting soybeans with salt and koji."
ln ingred:condiment:miso dna:taste:umami calc:associated_with

def "ingred:condiment:mustard" "A condiment made from the seeds of a mustard plant mixed with water, vinegar, or other liquids."
ln ingred:condiment:mustard dna:taste:sour calc:associated_with
ln ingred:condiment:mustard dna:smell:pungent calc:associated_with

def "ingred:condiment:olive_oil" "A liquid fat obtained from olives, central to Mediterranean cuisine."
ln ingred:condiment:olive_oil chem:fatty_acid:oleic_acid @rich_in

def "ingred:condiment:salt" "A mineral composed primarily of sodium chloride, the most fundamental flavor enhancer."
ln ingred:condiment:salt dna:taste:salty calc:associated_with

def "ingred:condiment:sesame_oil" "An edible vegetable oil derived from sesame seeds, highly aromatic when toasted."
ln ingred:condiment:sesame_oil dna:smell:fragrant calc:associated_with

def "ingred:condiment:soy_sauce" "A liquid condiment of Chinese origin, traditionally made from a fermented paste of soybeans."
ln ingred:condiment:soy_sauce dna:taste:salty calc:associated_with
ln ingred:condiment:soy_sauce dna:taste:umami calc:associated_with

def "ingred:condiment:sugar" "A sweet crystalline substance obtained from various plants."
ln ingred:condiment:sugar dna:taste:sweet calc:associated_with
ln ingred:condiment:sugar sci:cook:caramelization @undergoes

def "ingred:condiment:vinegar" "An aqueous solution of acetic acid and trace chemicals, typically produced by fermentation."
ln ingred:condiment:vinegar dna:taste:sour calc:associated_with

def "ingred:condiment:worcestershire_sauce" "A fermented liquid condiment of English origin, savory and slightly sweet."

def "ingred:dry_good:bulgur" "A cereal food made from the cracked parboiled groats of several different wheat species."

def "ingred:dry_good:couscous" "A Maghrebi dish of small steamed granules of rolled durum wheat semolina."
ln ingred:dry_good:couscous ingred:flour:wheat_flour @derived_from

def "ingred:dry_good:noodle" "A type of food made from unleavened dough which is rolled flat and cut into long strips or strings."
ln ingred:dry_good:noodle verb:cook:boil @requires

def "ingred:dry_good:pasta" "A staple food of Italian cuisine made from unleavened dough of durum wheat flour mixed with water or eggs."
ln ingred:dry_good:pasta ingred:flour:wheat_flour @derived_from
ln ingred:dry_good:pasta verb:cook:boil @requires

def "ingred:ferment:cheese" "A dairy product derived from milk, produced in wide ranges of flavors, textures, and forms by coagulation of the milk protein casein."
ln ingred:ferment:cheese dna:taste:umami calc:associated_with
ln ingred:ferment:cheese dna:smell:musty calc:associated_with

def "ingred:ferment:doenjang" "A thick, brown, fermented soybean paste from Korea, earthy and deeply savory."
ln ingred:ferment:doenjang dna:taste:umami calc:associated_with

def "ingred:ferment:hakarl" "A national dish of Iceland consisting of fermented and dried Greenland shark."
ln ingred:ferment:hakarl dna:smell:acrid calc:associated_with
ln ingred:ferment:hakarl cuisine:nordic calc:associated_with

def "ingred:ferment:katsuobushi" "Dried, fermented, and smoked skipjack tuna, essential for Japanese dashi."
ln ingred:ferment:katsuobushi dna:taste:umami calc:associated_with
ln ingred:ferment:katsuobushi cuisine:washoku calc:associated_with

def "ingred:ferment:kefir" "A fermented milk drink similar to a thin yogurt, made from kefir grains."

def "ingred:ferment:kimchi" "A traditional Korean side dish of salted and fermented vegetables, such as napa cabbage and Korean radish."
ln ingred:ferment:kimchi dna:taste:sour calc:associated_with
ln ingred:ferment:kimchi dna:taste:hot calc:associated_with

def "ingred:ferment:kombucha" "A fermented, lightly effervescent, sweetened black or green tea drink."

def "ingred:ferment:kvass" "A traditional fermented beverage from Eastern Europe made from rye bread."

def "ingred:ferment:natto" "A traditional Japanese food made from fermented soybeans, known for its powerful smell and sticky texture."
ln ingred:ferment:natto dna:texture:slimy calc:associated_with
ln ingred:ferment:natto dna:smell:musty calc:associated_with
ln ingred:ferment:natto cuisine:washoku calc:associated_with

def "ingred:ferment:pickled_cucumber" "A cucumber that has been pickled in a brine, vinegar, or other solution and left to ferment."

def "ingred:ferment:prosciutto" "An Italian dry-cured ham that is usually thinly sliced and served uncooked."
ln ingred:ferment:prosciutto dna:taste:salty calc:associated_with
ln ingred:ferment:prosciutto dna:taste:umami calc:associated_with
ln ingred:ferment:prosciutto cuisine:italian calc:associated_with

def "ingred:ferment:salami" "A type of cured sausage consisting of fermented and air-dried meat, typically pork."
ln ingred:ferment:salami cuisine:italian calc:associated_with

def "ingred:ferment:sauerkraut" "Finely cut raw cabbage that has been fermented by various lactic acid bacteria, staple in German cuisine."
ln ingred:ferment:sauerkraut dna:taste:sour calc:associated_with
ln ingred:ferment:sauerkraut cuisine:french calc:associated_with

def "ingred:ferment:smetana" "A type of sour cream from Central and Eastern Europe, rich and slightly tart."

def "ingred:ferment:stinky_tofu" "A Chinese form of fermented tofu with a strong odor, often sold as a street snack."
ln ingred:ferment:stinky_tofu dna:smell:rotten calc:associated_with

def "ingred:ferment:surstromming" "Lightly salted fermented Baltic herring from Sweden, infamous for its overwhelmingly strong odor."
ln ingred:ferment:surstromming dna:smell:rotten calc:associated_with
ln ingred:ferment:surstromming cuisine:nordic calc:associated_with

def "ingred:ferment:tempeh" "A traditional Indonesian soy product made from fermented soybeans formed into a block."
ln ingred:ferment:tempeh cuisine:nyonya calc:associated_with

def "ingred:ferment:umeboshi" "Pickled and fermented ume fruits common in Japan, extremely sour and salty."
ln ingred:ferment:umeboshi dna:taste:sour calc:associated_with
ln ingred:ferment:umeboshi dna:taste:salty calc:associated_with
ln ingred:ferment:umeboshi cuisine:washoku calc:associated_with

def "ingred:ferment:yogurt" "A food produced by bacterial fermentation of milk, known for its tart flavor and smooth texture."
ln ingred:ferment:yogurt dna:taste:sour calc:associated_with

def "ingred:ferment:zhacai" "A pickled mustard plant stem from Chongqing, China, spicy, sour, and salty."

def "ingred:flour:buckwheat_flour" "Flour milled from buckwheat, used for Japanese soba noodles and French galettes."
ln ingred:flour:buckwheat_flour ingred:grain:buckwheat @derived_from

def "ingred:flour:chickpea_flour" "A pulse flour made from ground chickpeas, crucial in Indian (Besan) and Mediterranean cooking."
ln ingred:flour:chickpea_flour ingred:legume:chickpea @derived_from

def "ingred:flour:cornmeal" "A meal (coarse flour) ground from dried corn, used for polenta and cornbread."
ln ingred:flour:cornmeal ingred:grain:corn @derived_from

def "ingred:flour:cornstarch" "The starch derived from the corn grain, used primarily as a thickening agent."
ln ingred:flour:cornstarch ingred:grain:corn @derived_from
ln ingred:flour:cornstarch sci:cook:gelatinization @undergoes
ln ingred:flour:cornstarch dna:texture:viscous @promotes

def "ingred:flour:rice_flour" "A form of flour made from finely milled rice, completely gluten-free."
ln ingred:flour:rice_flour ingred:grain:rice @derived_from

def "ingred:flour:wheat_flour" "A powder made from the grinding of wheat, containing gluten proteins."
ln ingred:flour:wheat_flour ingred:grain:wheat @derived_from

def "ingred:fruit:apple" "A round fruit with red or green skin. Used fresh, baked, or juiced."
ln ingred:fruit:apple dna:taste:sweet calc:associated_with
ln ingred:fruit:apple dna:color:red calc:associated_with
ln ingred:fruit:apple dna:texture:crisp calc:associated_with
ln ingred:fruit:apple verb:cook:core sys:refers_to

def "ingred:fruit:apricot" "A small, golden-orange stone fruit with a velvety skin."

def "ingred:fruit:banana" "A long curved fruit with a yellow skin and soft, sweet flesh."
ln ingred:fruit:banana chem:odor:isoamyl_acetate @contains
ln ingred:fruit:banana dna:taste:sweet calc:associated_with
ln ingred:fruit:banana dna:color:yellow calc:associated_with
ln ingred:fruit:banana dna:texture:soft calc:associated_with

def "ingred:fruit:blackberry" "A dark, aggregate fruit with a sweet-tart flavor."

def "ingred:fruit:blueberry" "A small, round, dark blue fruit."
ln ingred:fruit:blueberry dna:color:blue calc:associated_with

def "ingred:fruit:cherry" "A small, round stone fruit, typically red or dark purple."
ln ingred:fruit:cherry verb:cook:pit sys:refers_to

def "ingred:fruit:coconut" "A large tropical seed with a hard shell, providing water, milk, and meat."

def "ingred:fruit:fig" "A soft, sweet fruit full of small seeds, growing on a ficus tree."
ln ingred:fruit:fig dna:texture:soft calc:associated_with

def "ingred:fruit:grape" "A small, juicy berry growing in clusters on vines."

def "ingred:fruit:grapefruit" "A large, tart, and slightly bitter citrus fruit."
ln ingred:fruit:grapefruit dna:taste:bitter calc:associated_with

def "ingred:fruit:lemon" "A yellow citrus fruit known for its acidic juice and aromatic rind."
ln ingred:fruit:lemon chem:odor:limonene @contains
ln ingred:fruit:lemon dna:taste:sour calc:associated_with
ln ingred:fruit:lemon dna:smell:fragrant calc:associated_with
ln ingred:fruit:lemon dna:color:yellow calc:associated_with
ln ingred:fruit:lemon verb:cook:zest sys:refers_to
ln ingred:fruit:lemon verb:cook:press sys:refers_to

def "ingred:fruit:lime" "A green citrus fruit with a sharp, acidic flavor."
ln ingred:fruit:lime dna:taste:sour calc:associated_with
ln ingred:fruit:lime verb:cook:press sys:refers_to

def "ingred:fruit:mango" "A fleshy tropical stone fruit with a sweet, resinous flavor."
ln ingred:fruit:mango dna:taste:sweet calc:associated_with
ln ingred:fruit:mango dna:smell:fragrant calc:associated_with

def "ingred:fruit:melon" "A large, sweet, fleshy fruit derived from trailing vines."

def "ingred:fruit:orange" "A round citrus fruit with sweet and tart juice."
ln ingred:fruit:orange chem:odor:limonene @contains
ln ingred:fruit:orange verb:cook:zest sys:refers_to

def "ingred:fruit:papaya" "A tropical fruit with orange flesh and black, peppery seeds."

def "ingred:fruit:peach" "A soft, sweet fruit with fuzzy skin and a large pit."
ln ingred:fruit:peach dna:taste:sweet calc:associated_with
ln ingred:fruit:peach dna:texture:soft calc:associated_with
ln ingred:fruit:peach verb:cook:pit sys:refers_to

def "ingred:fruit:pear" "A sweet, mild fruit with a fibrous center."
ln ingred:fruit:pear verb:cook:core sys:refers_to

def "ingred:fruit:pineapple" "A large tropical fruit with a spiky exterior and sweet-tart flesh."

def "ingred:fruit:plum" "A smooth-skinned stone fruit that can be sweet or tart."

def "ingred:fruit:pomegranate" "A tough-skinned fruit filled with sweet-tart, ruby-red seeds (arils)."

def "ingred:fruit:raspberry" "A delicate, aggregate fruit, usually red and tart."

def "ingred:fruit:strawberry" "A red, juicy, conical fruit with seeds on the outside."
ln ingred:fruit:strawberry dna:taste:sweet calc:associated_with
ln ingred:fruit:strawberry dna:color:red calc:associated_with
ln ingred:fruit:strawberry verb:cook:hull sys:refers_to

def "ingred:fruit:watermelon" "A large melon with a green rind and watery, sweet red flesh."
ln ingred:fruit:watermelon dna:texture:crisp calc:associated_with

def "ingred:fruit:yuzu" "An East Asian citrus fruit with a highly aromatic rind."
ln ingred:fruit:yuzu dna:taste:sour calc:associated_with
ln ingred:fruit:yuzu dna:smell:fragrant calc:associated_with
ln ingred:fruit:yuzu verb:cook:zest sys:refers_to

def "ingred:grain:amaranth" "A highly nutritious pseudocereal, cultivated by the Aztecs and Incas."

def "ingred:grain:barley" "A highly adaptable cereal grain used in soups, breads, and for malting/brewing."

def "ingred:grain:buckwheat" "A plant cultivated for its grain-like seeds and as a cover crop, gluten-free despite its name."

def "ingred:grain:corn" "A large grain plant domesticated by indigenous peoples in the Americas (maize)."
ln ingred:grain:corn sci:cook:gelatinization @undergoes

def "ingred:grain:millet" "A group of highly variable small-seeded grasses, widely grown as cereal crops or grains."

def "ingred:grain:oats" "A cereal grain prized for its nutritional value and cholesterol-lowering properties."

def "ingred:grain:quinoa" "A flowering plant in the amaranth family, grown primarily for its edible seeds."

def "ingred:grain:rice" "A cereal grain, the most widely consumed staple food for a large part of the world's human population."
ln ingred:grain:rice sci:cook:gelatinization @undergoes
ln ingred:grain:rice verb:cook:steam sys:refers_to
ln ingred:grain:rice verb:cook:boil sys:refers_to
ln ingred:grain:rice dna:texture:soft calc:associated_with

def "ingred:grain:rye" "A grass grown extensively as a grain, used for distinctive, dense breads and whiskey."

def "ingred:grain:sorghum" "A cultivated grass grown for grain, heavily used in Africa and Asia."

def "ingred:grain:wheat" "A cereal grain grown worldwide, foundational for baking and bread-making."

def "ingred:herb:basil" "A sweet, fragrant herb central to Italian cuisine."
ln ingred:herb:basil dna:color:green calc:associated_with

def "ingred:herb:cilantro" "The fresh leaves of the coriander plant, widely used in Mexican and Asian cuisines."
ln ingred:herb:cilantro dna:color:green calc:associated_with

def "ingred:herb:curry_leaf" "Highly aromatic fresh leaves essential to South Indian cooking."

def "ingred:herb:dill" "A feathery herb with a grassy, anise-like flavor, often paired with seafood."

def "ingred:herb:kaffir_lime_leaf" "Intensely fragrant citrus leaves used heavily in Thai cuisine."

def "ingred:herb:lemongrass" "A fibrous stalk with a strong citrus flavor, essential in Southeast Asian cuisines."

def "ingred:herb:mint" "A refreshing, cooling herb used globally in both sweet and savory dishes."
ln ingred:herb:mint chem:odor:menthol @contains

def "ingred:herb:oregano" "A robust, slightly bitter herb, essential in Mediterranean and Mexican dishes."

def "ingred:herb:rosemary" "A pine-scented, woody herb often paired with roasted meats."

def "ingred:herb:thyme" "A delicate, earthy herb fundamental to European cooking."

def "ingred:legume:adzuki_bean" "A small red bean widely grown in East Asia, typically sweetened for desserts."
ln ingred:legume:adzuki_bean dna:taste:sweet calc:associated_with

def "ingred:legume:black_bean" "A small, shiny black legume heavily used in Latin American cuisine."

def "ingred:legume:chickpea" "A versatile, high-protein legume, central to Middle Eastern and Indian cuisines (Garbanzo)."
ln ingred:legume:chickpea verb:cook:soak @requires
ln ingred:legume:chickpea verb:cook:boil sys:refers_to

def "ingred:legume:kidney_bean" "A variety of common bean shaped like a kidney, popular in chili and red beans & rice."
ln ingred:legume:kidney_bean verb:cook:soak @requires

def "ingred:legume:lentil" "An edible legume shaped like a lens, known for its quick cooking time compared to other beans."
ln ingred:legume:lentil verb:cook:simmer sys:refers_to

def "ingred:legume:mung_bean" "A small green bean used both whole and sprouted in Asian cuisines."

def "ingred:legume:peanut" "A legume crop grown mainly for its edible seeds, developing underground rather than on vines."
ln ingred:legume:peanut dna:smell:fragrant calc:associated_with

def "ingred:legume:soybean" "A species of legume native to East Asia, vital for fermentation and protein substitutes."
ln ingred:legume:soybean verb:cook:soak @requires

def "ingred:meat:bacon" "Salt-cured pork, typically from the belly, often smoked."
ln ingred:meat:bacon ingred:meat:pork_belly @derived_from
ln ingred:meat:bacon dna:taste:salty calc:associated_with
ln ingred:meat:bacon dna:smell:pungent calc:associated_with
ln ingred:meat:bacon verb:cook:render sys:refers_to
ln ingred:meat:bacon verb:cook:fry sys:refers_to

def "ingred:meat:beef" "Culinary name for meat from cattle."
ln ingred:meat:beef chem:pigment:heme @contains
ln ingred:meat:beef dna:taste:umami calc:associated_with
ln ingred:meat:beef sci:cook:maillard_reaction @promotes
ln ingred:meat:beef sci:cook:protein_denaturation @undergoes

def "ingred:meat:bone_marrow" "The rich, fatty, and flavorful tissue found inside large animal bones."
ln ingred:meat:bone_marrow dna:texture:viscous calc:associated_with
ln ingred:meat:bone_marrow dna:texture:soft calc:associated_with

def "ingred:meat:breast_meat" "The lean, white meat from the chest of a bird."
ln ingred:meat:breast_meat ingred:meat:chicken sys:part_of
ln ingred:meat:breast_meat ingred:meat:duck sys:part_of
ln ingred:meat:breast_meat verb:cook:saute sys:refers_to

def "ingred:meat:brisket" "A tough, fibrous cut from the breast or lower chest, requiring slow cooking."
ln ingred:meat:brisket ingred:meat:beef sys:part_of
ln ingred:meat:brisket dna:texture:fibrous calc:associated_with
ln ingred:meat:brisket verb:cook:braise sys:refers_to
ln ingred:meat:brisket verb:cook:smoke sys:refers_to

def "ingred:meat:chicken" "The most common type of poultry in the world."
ln ingred:meat:chicken dna:taste:umami calc:associated_with
ln ingred:meat:chicken sci:cook:protein_denaturation @undergoes

def "ingred:meat:chuck" "A heavily exercised shoulder cut, rich in collagen, ideal for braising."
ln ingred:meat:chuck ingred:meat:beef sys:part_of
ln ingred:meat:chuck dna:texture:fibrous calc:associated_with
ln ingred:meat:chuck verb:cook:braise sys:refers_to

def "ingred:meat:duck" "A waterfowl with rich, dark meat and a thick layer of fat."

def "ingred:meat:flank" "A lean, flat cut of beef from the abdominal muscles."
ln ingred:meat:flank ingred:meat:beef sys:part_of
ln ingred:meat:flank verb:cook:broil sys:refers_to

def "ingred:meat:ham" "Pork from a leg cut that has been preserved by wet or dry curing, with or without smoking."
ln ingred:meat:ham ingred:meat:pork @derived_from

def "ingred:meat:heart" "A dense, muscular organ meat with a firm texture."

def "ingred:meat:lamb" "Meat from a young domestic sheep."

def "ingred:meat:liver" "A nutrient-dense, rich-tasting organ meat."

def "ingred:meat:pork" "Culinary name for meat from domestic pigs."
ln ingred:meat:pork dna:taste:umami calc:associated_with

def "ingred:meat:pork_belly" "A fatty, boneless cut of meat from the belly of a pig."
ln ingred:meat:pork_belly ingred:meat:pork sys:part_of
ln ingred:meat:pork_belly verb:cook:roast sys:refers_to

def "ingred:meat:pork_loin" "A lean, tender cut from the back of the pig."
ln ingred:meat:pork_loin ingred:meat:pork sys:part_of

def "ingred:meat:pork_shoulder" "A well-marbled cut from the upper shoulder, great for slow roasting or pulling."
ln ingred:meat:pork_shoulder ingred:meat:pork sys:part_of

def "ingred:meat:poultry_wing" "The wing of a bird, known for a high ratio of skin and bone to meat."
ln ingred:meat:poultry_wing ingred:meat:chicken sys:part_of

def "ingred:meat:ribeye" "A highly marbled, flavorful beef cut from the rib section."
ln ingred:meat:ribeye ingred:meat:beef sys:part_of
ln ingred:meat:ribeye verb:cook:grill sys:refers_to

def "ingred:meat:shank" "The leg portion of a steer, extremely tough and full of connective tissue."
ln ingred:meat:shank ingred:meat:beef sys:part_of
ln ingred:meat:shank dna:texture:fibrous calc:associated_with
ln ingred:meat:shank verb:cook:braise sys:refers_to

def "ingred:meat:sirloin" "A flavorful cut of beef from the lower back."
ln ingred:meat:sirloin ingred:meat:beef sys:part_of

def "ingred:meat:tenderloin" "The most tender cut of beef, located beneath the ribs."
ln ingred:meat:tenderloin ingred:meat:beef sys:part_of
ln ingred:meat:tenderloin dna:texture:soft calc:associated_with
ln ingred:meat:tenderloin verb:cook:sear sys:refers_to

def "ingred:meat:thigh_meat" "The dark, fatty, and flavorful meat from the upper leg of a bird."
ln ingred:meat:thigh_meat ingred:meat:chicken sys:part_of
ln ingred:meat:thigh_meat ingred:meat:duck sys:part_of

def "ingred:meat:tripe" "The edible muscle wall of the stomach of ruminant farm animals."
ln ingred:meat:tripe verb:cook:boil sys:refers_to

def "ingred:meat:venison" "Meat from a deer; lean game meat."

def "ingred:seafood:caviar" "Salt-cured roe of the sturgeon, a luxury delicacy."
ln ingred:seafood:caviar dna:taste:salty calc:associated_with
ln ingred:seafood:caviar dna:color:black calc:associated_with

def "ingred:seafood:clam" "A burrowing bivalve mollusk, popular in soups and pasta."
ln ingred:seafood:clam verb:cook:steam sys:refers_to

def "ingred:seafood:cod" "A mild-flavored, flaky white fish."
ln ingred:seafood:cod verb:cook:poach sys:refers_to
ln ingred:seafood:cod sci:cook:protein_denaturation @undergoes

def "ingred:seafood:crab" "A crustacean with a hard exoskeleton and sweet, tender meat."
ln ingred:seafood:crab dna:taste:sweet calc:associated_with

def "ingred:seafood:eel" "A snake-like fish with rich, fatty meat, typically grilled and glazed."

def "ingred:seafood:flounder" "A flatfish with a delicate, sweet flavor, often pan-fried."
ln ingred:seafood:flounder verb:cook:fry sys:refers_to

def "ingred:seafood:halibut" "A large flatfish with dense, firm white meat."

def "ingred:seafood:kombu" "Edible kelp used extensively to produce dashi (soup stock)."
ln ingred:seafood:kombu dna:taste:umami calc:associated_with
ln ingred:seafood:kombu dna:texture:viscous calc:associated_with
ln ingred:seafood:kombu dna:color:green calc:associated_with

def "ingred:seafood:langoustine" "A slender crustacean resembling a small lobster, valued for its delicate tail meat."

def "ingred:seafood:lobster" "A large marine crustacean highly prized for its rich, sweet meat."

def "ingred:seafood:mackerel" "A strongly flavored, oily pelagic fish."
ln ingred:seafood:mackerel verb:cook:cure sys:refers_to

def "ingred:seafood:mussel" "A bivalve mollusk, typically cooked in wine and broth."
ln ingred:seafood:mussel verb:cook:steam sys:refers_to

def "ingred:seafood:octopus" "A cephalopod with eight arms, requiring tenderization before cooking."
ln ingred:seafood:octopus dna:texture:fibrous calc:associated_with
ln ingred:seafood:octopus verb:cook:braise sys:refers_to

def "ingred:seafood:oyster" "A bivalve mollusk, often eaten raw, known for its briny flavor."
ln ingred:seafood:oyster dna:taste:salty calc:associated_with
ln ingred:seafood:oyster dna:taste:umami calc:associated_with

def "ingred:seafood:salmon" "An anadromous fish known for its rich, oily, pink-to-orange flesh."
ln ingred:seafood:salmon dna:color:orange calc:associated_with
ln ingred:seafood:salmon verb:cook:smoke sys:refers_to
ln ingred:seafood:salmon verb:cook:cure sys:refers_to

def "ingred:seafood:sardine" "A small, oily forage fish, often canned, salted, or grilled."

def "ingred:seafood:scallop" "A bivalve with a large, sweet adductor muscle."
ln ingred:seafood:scallop dna:taste:sweet calc:associated_with

def "ingred:seafood:sea_bass" "A highly prized white fish with a delicate, buttery texture."
ln ingred:seafood:sea_bass verb:cook:steam sys:refers_to

def "ingred:seafood:sea_urchin" "The edible gonads of echinoderms, offering a creamy, oceanic taste."
ln ingred:seafood:sea_urchin dna:taste:umami calc:associated_with
ln ingred:seafood:sea_urchin dna:taste:sweet calc:associated_with
ln ingred:seafood:sea_urchin dna:texture:soft calc:associated_with
ln ingred:seafood:sea_urchin dna:color:yellow calc:associated_with

def "ingred:seafood:shrimp" "A widely consumed decapod crustacean with a sweet, delicate flavor."
ln ingred:seafood:shrimp verb:cook:fry sys:refers_to
ln ingred:seafood:shrimp verb:cook:boil sys:refers_to
ln ingred:seafood:shrimp sci:cook:coagulation @undergoes

def "ingred:seafood:snapper" "A firm, sweet white fish, often roasted or steamed whole."
ln ingred:seafood:snapper verb:cook:roast sys:refers_to

def "ingred:seafood:squid" "A cephalopod with a tubular body, turning opaque and firm when cooked."
ln ingred:seafood:squid dna:texture:smooth calc:associated_with
ln ingred:seafood:squid verb:cook:grill sys:refers_to

def "ingred:seafood:tuna" "A large, fast-swimming pelagic fish with dense, dark red meat."
ln ingred:seafood:tuna dna:taste:umami calc:associated_with
ln ingred:seafood:tuna dna:color:red calc:associated_with
ln ingred:seafood:tuna sci:cook:protein_denaturation @undergoes

def "ingred:spice:ajwain" "Seeds with a strong, thyme-like flavor, often used in Indian breads and lentil dishes (Carom seeds)."

def "ingred:spice:amchur" "Dried green mango powder, used to add a tart, fruity acidity to dishes without adding moisture."
ln ingred:spice:amchur dna:taste:sour calc:associated_with

def "ingred:spice:asafoetida" "A dried resin with a pungent smell that transforms into an allium-like savoriness when fried (Hing)."
ln ingred:spice:asafoetida dna:smell:pungent calc:associated_with
ln ingred:spice:asafoetida cuisine:indian calc:associated_with
ln ingred:spice:asafoetida verb:cook:fry @requires

def "ingred:spice:black_cardamom" "A larger, darker pod dried over an open fire, imparting a strong smoky flavor (Badi Elaichi)."
ln ingred:spice:black_cardamom dna:smell:musty calc:associated_with

def "ingred:spice:black_pepper" "The dried, unripe fruit of the piperaceae family, the most ubiquitous spice."

def "ingred:spice:cardamom" "The 'Queen of Spices', a green pod offering sweet, floral, and eucalyptus notes (Elaichi)."
ln ingred:spice:cardamom dna:smell:fragrant calc:associated_with

def "ingred:spice:cinnamon" "The inner bark of a tropical tree, offering sweet and warm notes."
ln ingred:spice:cinnamon chem:odor:cinnamaldehyde @contains
ln ingred:spice:cinnamon dna:taste:sweet calc:associated_with

def "ingred:spice:clove" "The aromatic flower buds of a tree, highly pungent and warm."
ln ingred:spice:clove dna:smell:pungent calc:associated_with

def "ingred:spice:coriander_seed" "The dried seeds of the cilantro plant, offering a warm, citrusy, and woody flavor (Dhania)."
ln ingred:spice:coriander_seed verb:cook:toast @requires

def "ingred:spice:cumin" "Seeds with an earthy, warm, and slightly nutty flavor, a pillar of Indian curries (Jeera)."
ln ingred:spice:cumin verb:cook:fry @requires

def "ingred:spice:fenugreek" "Bitter, maple-scented seeds and leaves (Kasuri Methi) crucial for complex Indian gravies."
ln ingred:spice:fenugreek dna:taste:bitter calc:associated_with

def "ingred:spice:mustard_seed" "Small seeds (black/brown) popped in hot oil to release a nutty, pungent flavor (Rai)."
ln ingred:spice:mustard_seed verb:cook:fry @requires

def "ingred:spice:nigella_seed" "Small black seeds with an onion-like, peppery flavor, common in naan and Bengali cooking (Kalonji)."

def "ingred:spice:nutmeg" "The seed of the myristica tree, sweet and slightly spicy."

def "ingred:spice:saffron" "The crimson stigmas of a crocus flower, the world's most expensive spice, imparting a golden color."
ln ingred:spice:saffron dna:color:orange calc:associated_with

def "ingred:spice:star_anise" "A star-shaped spice with a strong licorice flavor, vital to Chinese cuisine."

def "ingred:spice:turmeric" "A bright yellow rhizome powder providing earthiness, bitterness, and vibrant color (Haldi)."
ln ingred:spice:turmeric chem:pigment:curcumin @contains
ln ingred:spice:turmeric dna:taste:bitter calc:associated_with
ln ingred:spice:turmeric dna:color:yellow calc:associated_with

def "ingred:spice:vanilla" "The cured seed pod of an orchid, the foundational flavor of Western baking."
ln ingred:spice:vanilla chem:odor:vanillin @contains
ln ingred:spice:vanilla dna:smell:fragrant calc:associated_with

def "ingred:veg:artichoke" "The edible bud of a large thistle plant."

def "ingred:veg:asparagus" "A spring vegetable celebrated for its tender young shoots."

def "ingred:veg:bamboo_shoot" "The tender emerging sprout of the bamboo plant."
ln ingred:veg:bamboo_shoot dna:texture:fibrous calc:associated_with

def "ingred:veg:beet" "A deep red, earthy, and sweet root vegetable."
ln ingred:veg:beet dna:color:red calc:associated_with

def "ingred:veg:bell_pepper" "A sweet, non-spicy capsicum fruit."

def "ingred:veg:bitter_melon" "A tropical vine fruit noted for its intensely bitter flavor. Also known as goya."
ln ingred:veg:bitter_melon dna:taste:bitter calc:associated_with

def "ingred:veg:broccoli" "A green plant whose large flowering head, stalk, and small associated leaves are eaten as a vegetable."
ln ingred:veg:broccoli dna:color:green calc:associated_with

def "ingred:veg:brussels_sprout" "Small leafy green buds resembling miniature cabbages."

def "ingred:veg:cabbage" "A leafy green, red, or white biennial plant grown as an annual vegetable crop."

def "ingred:veg:carrot" "A sweet, crisp, orange root vegetable."
ln ingred:veg:carrot chem:pigment:carotene @contains
ln ingred:veg:carrot dna:taste:sweet calc:associated_with
ln ingred:veg:carrot dna:color:orange calc:associated_with
ln ingred:veg:carrot verb:cook:peel sys:refers_to

def "ingred:veg:cassava" "A starchy tuberous root from the tropics, used to make tapioca. Also known as yuca."

def "ingred:veg:cauliflower" "A tightly packed white head of undeveloped flower buds."

def "ingred:veg:celery" "A marshland plant cultivated for its crisp, fibrous stalks."
ln ingred:veg:celery dna:texture:crisp calc:associated_with

def "ingred:veg:chayote" "A pale green, pear-shaped squash popular in Latin American cuisine."

def "ingred:veg:chili_pepper" "A spicy capsicum fruit containing capsaicin."
ln ingred:veg:chili_pepper dna:taste:hot calc:associated_with

def "ingred:veg:cucumber" "A long, crisp, high-water-content gourd eaten fresh."

def "ingred:veg:daikon" "A long, white winter radish fundamental to East Asian cuisine."

def "ingred:veg:eggplant" "A spongy, absorbent nightshade fruit, also known as aubergine."
ln ingred:veg:eggplant dna:color:violet calc:associated_with
ln ingred:veg:eggplant verb:cook:roast sys:refers_to

def "ingred:veg:fennel" "A highly aromatic and flavorful herb with culinary uses; the bulb is eaten as a vegetable."

def "ingred:veg:garlic" "A strongly flavored bulb used universally as a base aromatic."
ln ingred:veg:garlic chem:odor:allicin @contains
ln ingred:veg:garlic dna:smell:pungent calc:associated_with
ln ingred:veg:garlic verb:cook:mince sys:refers_to

def "ingred:veg:jicama" "A crisp, sweet, edible tuber native to Mexico."
ln ingred:veg:jicama dna:texture:crisp calc:associated_with

def "ingred:veg:kale" "A hardy cabbage with green or purple leaves, which do not form a central head."
ln ingred:veg:kale dna:taste:bitter calc:associated_with

def "ingred:veg:kohlrabi" "A stout, round cultivar of cabbage with a texture similar to broccoli stem."

def "ingred:veg:leek" "A mild, sweet allium with flat, overlapping leaves."

def "ingred:veg:lettuce" "A leafy plant often grown for salads, coming in many crisp varieties."

def "ingred:veg:lotus_root" "The crisp, hole-filled underwater stem of the lotus plant."
ln ingred:veg:lotus_root dna:texture:crisp calc:associated_with

def "ingred:veg:mushroom" "The fleshy, spore-bearing fruiting body of a fungus, typically the button variety."

def "ingred:veg:nopales" "The edible pads of the prickly pear cactus, common in Mexican cuisine."

def "ingred:veg:okra" "A green seed pod known for its mucilaginous (slimy) texture when cooked."
ln ingred:veg:okra dna:texture:slimy calc:associated_with

def "ingred:veg:onion" "A bulb vegetable with papery skin, foundational to global cuisines."
ln ingred:veg:onion dna:smell:pungent calc:associated_with
ln ingred:veg:onion sci:cook:maillard_reaction @promotes
ln ingred:veg:onion sci:cook:caramelization @promotes

def "ingred:veg:parsnip" "A pale root vegetable, similar to a carrot but sweeter and earthier."

def "ingred:veg:potato" "A starchy tuber, foundational to global diets and highly versatile."
ln ingred:veg:potato sci:cook:gelatinization @promotes
ln ingred:veg:potato sci:cook:enzymatic_browning @promotes
ln ingred:veg:potato verb:cook:mash sys:refers_to
ln ingred:veg:potato verb:cook:boil sys:refers_to

def "ingred:veg:pumpkin" "A large winter squash with thick, sweet orange flesh."
ln ingred:veg:pumpkin dna:color:orange calc:associated_with

def "ingred:veg:radicchio" "A bitter-tasting leafy chicory with dark red leaves."
ln ingred:veg:radicchio dna:taste:bitter calc:associated_with

def "ingred:veg:radish" "A crisp, peppery root vegetable, often eaten raw."

def "ingred:veg:scallion" "Also known as green onion, used mostly as a garnish or mild aromatic."

def "ingred:veg:shallot" "A small bulb with a mild, sweet, and garlicky flavor."

def "ingred:veg:shiitake" "An edible mushroom native to East Asia, prized for its deep umami flavor."
ln ingred:veg:shiitake dna:taste:umami calc:associated_with

def "ingred:veg:spinach" "A leafy green vegetable known for its dark color and iron content."

def "ingred:veg:sweet_potato" "A sweet, starchy root vegetable, often orange or purple-fleshed."
ln ingred:veg:sweet_potato dna:taste:sweet calc:associated_with

def "ingred:veg:taro" "A tropical root vegetable with starchy, slightly nutty, often purplish flesh."
ln ingred:veg:taro dna:texture:viscous calc:associated_with

def "ingred:veg:tomatillo" "A small, green, tart fruit covered in a papery husk, essential for salsa verde."
ln ingred:veg:tomatillo verb:cook:puree sys:refers_to

def "ingred:veg:tomato" "A red, juicy culinary vegetable, biologically a berry."
ln ingred:veg:tomato chem:pigment:lycopene @contains
ln ingred:veg:tomato dna:taste:umami calc:associated_with
ln ingred:veg:tomato dna:color:red calc:associated_with

def "ingred:veg:truffle" "A highly aromatic subterranean fungus, considered a culinary delicacy."

def "ingred:veg:turnip" "A white-fleshed root vegetable with a slight mustard-like bite."

def "ingred:veg:water_spinach" "A semi-aquatic tropical plant grown as a leaf vegetable (kangkong)."

def "ingred:veg:zucchini" "A summer squash with dark green skin and tender flesh."
