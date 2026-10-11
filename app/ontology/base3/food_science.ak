# Akasha ontology — food science, safety (HACCP) & precision cooking.
# The scientific study of food, bridging the everyday food domain (ingred:/
# technique:/dish:) with chemistry, microbiology and research method. Base pack.

def "foodsci" "Food science — the physics, chemistry and biology of food."
def "foodsci:maillard_reaction" "The heat-driven browning of amino acids and sugars that builds savoury, roasted flavour (メイラード反応)."
ln foodsci:maillard_reaction foodsci thesaurus:related
ln foodsci:maillard_reaction technique:searing thesaurus:related
ln foodsci:maillard_reaction technique:roasting thesaurus:related
ln foodsci:maillard_reaction cook_class:cook thesaurus:related
ln foodsci:maillard_reaction verb:cook:sear thesaurus:related
def "foodsci:caramelization" "The thermal breakdown of sugars into brown, bittersweet flavour compounds."
ln foodsci:caramelization foodsci thesaurus:related
ln foodsci:caramelization verb:cook:caramelize thesaurus:related
ln foodsci:caramelization technique:baking thesaurus:related
def "foodsci:enzymatic_browning" "Discolouration when cut produce meets air (polyphenol oxidase), e.g. sliced apple."
ln foodsci:enzymatic_browning foodsci thesaurus:related
ln foodsci:enzymatic_browning foodsafe:food_hygiene thesaurus:related
def "foodsci:denaturation" "The unfolding of protein structure by heat, acid or agitation — the basis of cooking eggs and meat."
ln foodsci:denaturation foodsci thesaurus:related
def "foodsci:protein_coagulation" "Denatured proteins bonding into a solid network (a set custard, cooked white)."
ln foodsci:protein_coagulation foodsci thesaurus:related
def "foodsci:gelatinization" "Starch granules swelling and thickening in hot water (sauce, rice)."
ln foodsci:gelatinization foodsci thesaurus:related
ln foodsci:gelatinization cook_class:cook thesaurus:related
def "foodsci:starch_retrogradation" "Cooled starch recrystallising — staling of bread, firming of rice."
ln foodsci:starch_retrogradation foodsci thesaurus:related
def "foodsci:emulsification" "Dispersing one liquid in another with an emulsifier (mayonnaise, hollandaise)."
ln foodsci:emulsification foodsci thesaurus:related
ln foodsci:emulsification verb:cook:emulsify thesaurus:related
def "foodsci:colloid" "A stable dispersion (foam, gel, emulsion) underlying much food texture."
ln foodsci:colloid foodsci thesaurus:related
def "foodsci:syneresis" "Weeping of liquid from a gel (whey from yoghurt)."
ln foodsci:syneresis foodsci thesaurus:related
def "foodsci:glass_transition" "The temperature where amorphous foods turn from glassy to rubbery — crispness and staling."
ln foodsci:glass_transition foodsci thesaurus:related
def "foodsci:water_activity" "Free-water availability (aw) governing microbial growth and shelf life."
ln foodsci:water_activity foodsci thesaurus:related
def "foodsci:lipid_oxidation" "Rancidity — the oxidation of fats producing off-flavours."
ln foodsci:lipid_oxidation foodsci thesaurus:related
def "foodsci:hydrocolloid" "A gelling/thickening agent (agar, pectin, xanthan) central to modern texture work."
ln foodsci:hydrocolloid foodsci thesaurus:related
ln foodsci:hydrocolloid foodsci:colloid thesaurus:related
def "foodsci:food_rheology" "The science of flow and deformation — viscosity, elasticity, texture."
ln foodsci:food_rheology foodsci thesaurus:related
ln foodsci:food_rheology research thesaurus:related
def "foodsci:mouthfeel" "The tactile sensation of food in the mouth."
ln foodsci:mouthfeel foodsci thesaurus:related
ln foodsci:mouthfeel tasting:viscosity thesaurus:related
# ── molecular gastronomy ──
def "foodsci:molecular_gastronomy" "The scientific study of cooking transformations, and its avant-garde cuisine (分子ガストロノミー)."
ln foodsci:molecular_gastronomy foodsci thesaurus:related
ln foodsci:molecular_gastronomy technique thesaurus:related
ln foodsci:molecular_gastronomy research thesaurus:related
def "foodsci:spherification" "Encasing a flavoured liquid in a thin gel membrane (alginate + calcium)."
ln foodsci:spherification foodsci thesaurus:related
ln foodsci:spherification foodsci:hydrocolloid thesaurus:related
def "foodsci:gelification" "Setting liquids into gels with hydrocolloids for novel textures."
ln foodsci:gelification foodsci thesaurus:related
def "foodsci:culinary_foam" "An airy foam (espuma) stabilised by lecithin or protein."
ln foodsci:culinary_foam foodsci thesaurus:related
ln foodsci:culinary_foam foodsci:colloid thesaurus:related
def "foodsci:transglutaminase" "'Meat glue' enzyme that bonds proteins into new forms."
ln foodsci:transglutaminase foodsci thesaurus:related
def "foodsci:liquid_nitrogen_cooking" "Flash-freezing for instant ices and shattering textures."
ln foodsci:liquid_nitrogen_cooking foodsci thesaurus:related
# ── food microbiology ──
def "foodsci:food_microbiology" "The study of microbes in food — spoilage, safety and fermentation."
ln foodsci:food_microbiology foodsci thesaurus:related
def "foodsci:fermentation_science" "The controlled microbial transformation of food (味噌, cheese, bread, kimchi)."
ln foodsci:fermentation_science foodsci thesaurus:related
ln foodsci:fermentation_science technique:fermentation thesaurus:related
ln foodsci:fermentation_science fp:fermentation thesaurus:related
def "foodsci:starter_culture" "A defined microbial inoculum starting a fermentation."
ln foodsci:starter_culture foodsci thesaurus:related
def "foodsci:lactic_acid_bacteria" "The souring, preserving microbes of yoghurt, kimchi and sauerkraut."
ln foodsci:lactic_acid_bacteria foodsci thesaurus:related
ln foodsci:lactic_acid_bacteria nutrisci:probiotic thesaurus:related
def "foodsci:koji" "Aspergillus oryzae, the mould behind sake, miso and soy sauce (麹)."
ln foodsci:koji foodsci thesaurus:related
ln foodsci:koji cuisine:japanese thesaurus:related
def "foodsci:spoilage" "Undesirable microbial or chemical deterioration of food."
ln foodsci:spoilage foodsci thesaurus:related
# ── food safety — HACCP unifies the scattered defs ──
def "foodsafe" "Food safety — preventing hazards from farm to fork."
def "foodsafe:haccp" "Hazard Analysis and Critical Control Points — the preventive system of identifying and controlling food hazards."
ln foodsafe:haccp foodsafe thesaurus:related
ln foodsafe:haccp fp:haccp thesaurus:related
ln foodsafe:haccp ck:haccp thesaurus:related
ln foodsafe:haccp cc:haccp thesaurus:related
ln foodsafe:haccp research thesaurus:related
def "foodsafe:critical_control_point" "A step where control is essential to prevent a hazard (a CCP)."
ln foodsafe:critical_control_point foodsafe thesaurus:related
def "foodsafe:hazard_analysis" "Identifying biological, chemical and physical hazards in a process."
ln foodsafe:hazard_analysis foodsafe thesaurus:related
def "foodsafe:food_hygiene" "Practices keeping food safe to eat (衛生)."
ln foodsafe:food_hygiene foodsafe thesaurus:related
def "foodsafe:cold_chain" "Unbroken refrigeration from production to consumption."
ln foodsafe:cold_chain foodsafe thesaurus:related
def "foodsafe:temperature_danger_zone" "~5–60°C, where pathogens multiply fastest."
ln foodsafe:temperature_danger_zone foodsafe thesaurus:related
ln foodsafe:temperature_danger_zone technique_param:heat_level:low thesaurus:related
def "foodsafe:pasteurization" "Mild heat killing pathogens while preserving quality (低温殺菌)."
ln foodsafe:pasteurization foodsafe thesaurus:related
ln foodsafe:pasteurization fp:pasteurization thesaurus:related
ln foodsafe:pasteurization foodprecis:low_temperature_cooking thesaurus:related
def "foodsafe:cross_contamination" "Transfer of pathogens between foods, hands or surfaces."
ln foodsafe:cross_contamination foodsafe thesaurus:related
def "foodsafe:foodborne_illness" "Illness from contaminated food (食中毒)."
ln foodsafe:foodborne_illness foodsafe thesaurus:related
ln foodsafe:foodborne_illness foodsci:food_microbiology thesaurus:related
def "foodsafe:pathogen" "A disease-causing microbe (Salmonella, Listeria, E. coli, norovirus)."
ln foodsafe:pathogen foodsafe thesaurus:related
ln foodsafe:pathogen foodsci:food_microbiology thesaurus:related
def "foodsafe:shelf_life" "The period a food stays safe and acceptable."
ln foodsafe:shelf_life foodsafe thesaurus:related
def "foodsafe:traceability" "The ability to track food through the supply chain."
ln foodsafe:traceability foodsafe thesaurus:related
def "foodsafe:allergen_control" "Managing allergen cross-contact in production."
ln foodsafe:allergen_control foodsafe thesaurus:related
ln foodsafe:allergen_control constraint:treenut thesaurus:related
def "foodsafe:iso22000" "An international food-safety management standard."
ln foodsafe:iso22000 foodsafe thesaurus:related
# ── precision & low-temperature cooking ──
def "foodprecis" "Precision cooking — controlling time and temperature exactly."
def "foodprecis:low_temperature_cooking" "Cooking at gentle, precisely held temperatures for even doneness and tenderness (低温調理)."
ln foodprecis:low_temperature_cooking foodprecis thesaurus:related
ln foodprecis:low_temperature_cooking technique:sous_vide thesaurus:related
ln foodprecis:low_temperature_cooking technique_param:heat_level:low thesaurus:related
ln foodprecis:low_temperature_cooking technique_param:pace:slow thesaurus:related
def "foodprecis:sous_vide_science" "Vacuum-sealed cooking in a temperature-controlled water bath; doneness is set by temperature, safety by time."
ln foodprecis:sous_vide_science foodprecis thesaurus:related
ln foodprecis:sous_vide_science technique:sous_vide thesaurus:related
ln foodprecis:sous_vide_science ck:sous_vide thesaurus:related
ln foodprecis:sous_vide_science foodsci:denaturation thesaurus:related
def "foodprecis:time_temperature" "The pairing of holding temperature and time that determines both doneness and pasteurization."
ln foodprecis:time_temperature foodprecis thesaurus:related
ln foodprecis:time_temperature foodsafe:pasteurization thesaurus:related
def "foodprecis:collagen_conversion" "Slow heat turning tough collagen into gelatine — the tenderising of braises and sous-vide."
ln foodprecis:collagen_conversion foodprecis thesaurus:related
ln foodprecis:collagen_conversion technique:braising thesaurus:related
ln foodprecis:collagen_conversion foodsci:denaturation thesaurus:related
def "foodprecis:protein_doneness" "Each protein sets at a characteristic temperature — the logic of precise cooking."
ln foodprecis:protein_doneness foodprecis thesaurus:related
ln foodprecis:protein_doneness foodsci:protein_coagulation thesaurus:related
def "foodprecis:thermal_immersion" "Heating via a circulated water bath (immersion circulator)."
ln foodprecis:thermal_immersion foodprecis thesaurus:related
