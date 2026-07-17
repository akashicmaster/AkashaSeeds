# Akasha ontology — nutrition science (新栄養学).
# From classical nutrients to the new frontiers — nutrigenomics, the microbiome,
# functional foods, chrononutrition — bridging nutrient:/diet:/tcm: with research
# method and food science. Base pack.

def "nutrisci" "Nutrition science — how food affects the body, classical to frontier."
def "nutrisci:bioavailability" "The fraction of a nutrient actually absorbed and usable — e.g. iron from meat vs plants."
ln nutrisci:bioavailability nutrisci thesaurus:related
def "nutrisci:glycemic_index" "How fast a food raises blood glucose relative to a reference (GI/血糖指数)."
ln nutrisci:glycemic_index nutrisci thesaurus:related
ln nutrisci:glycemic_index diet:low_gi thesaurus:related
def "nutrisci:glycemic_load" "Glycemic index adjusted for portion carbohydrate — a truer blood-sugar measure."
ln nutrisci:glycemic_load nutrisci thesaurus:related
ln nutrisci:glycemic_load diet:low_gi thesaurus:related
def "nutrisci:nutrigenomics" "How nutrients regulate gene expression (栄養ゲノミクス)."
ln nutrisci:nutrigenomics nutrisci thesaurus:related
def "nutrisci:nutrigenetics" "How genetic variation shapes individual response to diet."
ln nutrisci:nutrigenetics nutrisci thesaurus:related
def "nutrisci:personalized_nutrition" "Tailoring diet to a person's genes, microbiome and metabolism (個別化栄養)."
ln nutrisci:personalized_nutrition nutrisci thesaurus:related
ln nutrisci:personalized_nutrition nutrisci:nutrigenomics thesaurus:related
def "nutrisci:microbiome" "The community of gut microbes that ferment fibre and shape health (腸内細菌叢)."
ln nutrisci:microbiome nutrisci thesaurus:related
ln nutrisci:microbiome foodsci:fermentation_science thesaurus:related
ln nutrisci:microbiome foodsci:lactic_acid_bacteria thesaurus:related
def "nutrisci:prebiotic" "A fibre that feeds beneficial gut microbes."
ln nutrisci:prebiotic nutrisci thesaurus:related
ln nutrisci:prebiotic nutrisci:dietary_fiber thesaurus:related
def "nutrisci:probiotic" "Live beneficial microbes delivered in food (yoghurt, kimchi)."
ln nutrisci:probiotic nutrisci thesaurus:related
ln nutrisci:probiotic foodsci:lactic_acid_bacteria thesaurus:related
def "nutrisci:postbiotic" "Beneficial compounds produced by gut microbes (e.g. short-chain fatty acids)."
ln nutrisci:postbiotic nutrisci thesaurus:related
def "nutrisci:functional_food" "A food with health benefits beyond basic nutrition (機能性食品)."
ln nutrisci:functional_food nutrisci thesaurus:related
def "nutrisci:nutraceutical" "A food-derived product with medicinal effect."
ln nutrisci:nutraceutical nutrisci thesaurus:related
def "nutrisci:bioactive_compound" "A non-nutrient food compound with a biological effect."
ln nutrisci:bioactive_compound nutrisci thesaurus:related
ln nutrisci:bioactive_compound nutrisci:phytochemical thesaurus:related
def "nutrisci:phytochemical" "A plant compound (polyphenol, carotenoid, glucosinolate) with health activity."
ln nutrisci:phytochemical nutrisci thesaurus:related
ln nutrisci:phytochemical diet:plant_based thesaurus:related
def "nutrisci:polyphenol" "Antioxidant plant compounds abundant in tea, cocoa, berries."
ln nutrisci:polyphenol nutrisci thesaurus:related
def "nutrisci:antioxidant" "A compound that neutralises reactive oxygen, slowing oxidative damage."
ln nutrisci:antioxidant nutrisci thesaurus:related
ln nutrisci:antioxidant diet:anti_inflammatory thesaurus:related
def "nutrisci:dietary_fiber" "Indigestible carbohydrate feeding the microbiome and aiding satiety (食物繊維)."
ln nutrisci:dietary_fiber nutrisci thesaurus:related
ln nutrisci:dietary_fiber diet:plant_based thesaurus:related
def "nutrisci:chrononutrition" "How the timing of eating interacts with the body clock (時間栄養学)."
ln nutrisci:chrononutrition nutrisci thesaurus:related
def "nutrisci:intermittent_fasting" "Eating patterns cycling fasting and feeding windows."
ln nutrisci:intermittent_fasting nutrisci thesaurus:related
def "nutrisci:nutritional_epidemiology" "Studying diet–disease links in populations."
ln nutrisci:nutritional_epidemiology nutrisci thesaurus:related
ln nutrisci:nutritional_epidemiology research:method:quantitative thesaurus:related
ln nutrisci:nutritional_epidemiology research:findings thesaurus:related
def "nutrisci:biomarker" "A measurable indicator of nutritional status or intake."
ln nutrisci:biomarker nutrisci thesaurus:related
def "nutrisci:food_as_medicine" "The use of diet to prevent and manage disease (医食同源)."
ln nutrisci:food_as_medicine nutrisci thesaurus:related
ln nutrisci:food_as_medicine diet:anti_inflammatory thesaurus:related
def "nutrisci:satiety" "The feeling of fullness that ends eating."
ln nutrisci:satiety nutrisci thesaurus:related
def "nutrisci:metabolomics" "Profiling the small-molecule metabolites that reflect diet and metabolism."
ln nutrisci:metabolomics nutrisci thesaurus:related
# ── food-as-medicine bridges (医食同源) ──
ln nutrisci:food_as_medicine diet:mediterranean thesaurus:related
