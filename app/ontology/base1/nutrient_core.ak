# Akasha ontology — namespace: nutrient (core dietary nutrients)
# Hand-authored: Wikidata's nutrient class (Q181394) is too sparse/noisy to
# use as a skeleton, and the dietary nutrients are a small, stable set. These
# concepts mirror the per-100g values carried in the USDA food:* descriptions
# (energy, protein, fat, carbohydrate, fiber, calcium, sodium, vitamin C, …).
# License: MIT (editorial). atoms: category hubs + members + part_of links.

def "nutrient:energy" "Food energy, measured in kilocalories (kcal)."
set.add name="nutrient:core" id="nutrient:energy"

def "nutrient:macronutrient" "Macronutrients — energy-yielding dietary components needed in large amounts."
set.add name="nutrient:core" id="nutrient:macronutrient"

def "nutrient:protein" "Protein — amino-acid macronutrient; ~4 kcal/g."
set.add name="nutrient:core" id="nutrient:protein"
ln nutrient:protein nutrient:macronutrient sys:part_of

def "nutrient:carbohydrate" "Carbohydrate — sugars and starches; ~4 kcal/g."
set.add name="nutrient:core" id="nutrient:carbohydrate"
ln nutrient:carbohydrate nutrient:macronutrient sys:part_of

def "nutrient:fat" "Dietary fat — lipid macronutrient; ~9 kcal/g."
set.add name="nutrient:core" id="nutrient:fat"
ln nutrient:fat nutrient:macronutrient sys:part_of

def "nutrient:fiber" "Dietary fiber — indigestible plant carbohydrate."
set.add name="nutrient:core" id="nutrient:fiber"
ln nutrient:fiber nutrient:macronutrient sys:part_of

def "nutrient:sugar" "Sugars — simple carbohydrates."
set.add name="nutrient:core" id="nutrient:sugar"
ln nutrient:sugar nutrient:macronutrient sys:part_of

def "nutrient:starch" "Starch — complex plant carbohydrate."
set.add name="nutrient:core" id="nutrient:starch"
ln nutrient:starch nutrient:macronutrient sys:part_of

def "nutrient:water" "Water — essential dietary component."
set.add name="nutrient:core" id="nutrient:water"
ln nutrient:water nutrient:macronutrient sys:part_of

def "nutrient:vitamin" "Vitamins — organic micronutrients required in small amounts."
set.add name="nutrient:core" id="nutrient:vitamin"

def "nutrient:vitamin_a" "Vitamin A (retinol) — vision, immunity."
set.add name="nutrient:core" id="nutrient:vitamin_a"
ln nutrient:vitamin_a nutrient:vitamin sys:part_of

def "nutrient:vitamin_c" "Vitamin C (ascorbic acid) — antioxidant, collagen."
set.add name="nutrient:core" id="nutrient:vitamin_c"
ln nutrient:vitamin_c nutrient:vitamin sys:part_of

def "nutrient:vitamin_d" "Vitamin D — calcium absorption, bone."
set.add name="nutrient:core" id="nutrient:vitamin_d"
ln nutrient:vitamin_d nutrient:vitamin sys:part_of

def "nutrient:vitamin_e" "Vitamin E (tocopherol) — antioxidant."
set.add name="nutrient:core" id="nutrient:vitamin_e"
ln nutrient:vitamin_e nutrient:vitamin sys:part_of

def "nutrient:vitamin_k" "Vitamin K — blood clotting."
set.add name="nutrient:core" id="nutrient:vitamin_k"
ln nutrient:vitamin_k nutrient:vitamin sys:part_of

def "nutrient:thiamine" "Vitamin B1 (thiamine) — energy metabolism."
set.add name="nutrient:core" id="nutrient:thiamine"
ln nutrient:thiamine nutrient:vitamin sys:part_of

def "nutrient:riboflavin" "Vitamin B2 (riboflavin) — energy metabolism."
set.add name="nutrient:core" id="nutrient:riboflavin"
ln nutrient:riboflavin nutrient:vitamin sys:part_of

def "nutrient:niacin" "Vitamin B3 (niacin) — energy metabolism."
set.add name="nutrient:core" id="nutrient:niacin"
ln nutrient:niacin nutrient:vitamin sys:part_of

def "nutrient:pantothenic_acid" "Vitamin B5 (pantothenic acid)."
set.add name="nutrient:core" id="nutrient:pantothenic_acid"
ln nutrient:pantothenic_acid nutrient:vitamin sys:part_of

def "nutrient:vitamin_b6" "Vitamin B6 (pyridoxine) — amino-acid metabolism."
set.add name="nutrient:core" id="nutrient:vitamin_b6"
ln nutrient:vitamin_b6 nutrient:vitamin sys:part_of

def "nutrient:biotin" "Vitamin B7 (biotin)."
set.add name="nutrient:core" id="nutrient:biotin"
ln nutrient:biotin nutrient:vitamin sys:part_of

def "nutrient:folate" "Vitamin B9 (folate) — cell division."
set.add name="nutrient:core" id="nutrient:folate"
ln nutrient:folate nutrient:vitamin sys:part_of

def "nutrient:vitamin_b12" "Vitamin B12 (cobalamin) — nerves, red cells."
set.add name="nutrient:core" id="nutrient:vitamin_b12"
ln nutrient:vitamin_b12 nutrient:vitamin sys:part_of

def "nutrient:mineral" "Dietary minerals — inorganic micronutrients."
set.add name="nutrient:core" id="nutrient:mineral"

def "nutrient:calcium" "Calcium — bones, teeth, signalling."
set.add name="nutrient:core" id="nutrient:calcium"
ln nutrient:calcium nutrient:mineral sys:part_of

def "nutrient:iron" "Iron — oxygen transport (haemoglobin)."
set.add name="nutrient:core" id="nutrient:iron"
ln nutrient:iron nutrient:mineral sys:part_of

def "nutrient:magnesium" "Magnesium — enzyme cofactor."
set.add name="nutrient:core" id="nutrient:magnesium"
ln nutrient:magnesium nutrient:mineral sys:part_of

def "nutrient:phosphorus" "Phosphorus — bones, energy (ATP)."
set.add name="nutrient:core" id="nutrient:phosphorus"
ln nutrient:phosphorus nutrient:mineral sys:part_of

def "nutrient:potassium" "Potassium — fluid balance, nerves."
set.add name="nutrient:core" id="nutrient:potassium"
ln nutrient:potassium nutrient:mineral sys:part_of

def "nutrient:sodium" "Sodium — fluid balance, nerves."
set.add name="nutrient:core" id="nutrient:sodium"
ln nutrient:sodium nutrient:mineral sys:part_of

def "nutrient:zinc" "Zinc — immunity, enzymes."
set.add name="nutrient:core" id="nutrient:zinc"
ln nutrient:zinc nutrient:mineral sys:part_of

def "nutrient:copper" "Copper — enzyme cofactor."
set.add name="nutrient:core" id="nutrient:copper"
ln nutrient:copper nutrient:mineral sys:part_of

def "nutrient:manganese" "Manganese — enzyme cofactor."
set.add name="nutrient:core" id="nutrient:manganese"
ln nutrient:manganese nutrient:mineral sys:part_of

def "nutrient:selenium" "Selenium — antioxidant enzymes."
set.add name="nutrient:core" id="nutrient:selenium"
ln nutrient:selenium nutrient:mineral sys:part_of

def "nutrient:iodine" "Iodine — thyroid hormones."
set.add name="nutrient:core" id="nutrient:iodine"
ln nutrient:iodine nutrient:mineral sys:part_of

def "nutrient:chloride" "Chloride — fluid balance, stomach acid."
set.add name="nutrient:core" id="nutrient:chloride"
ln nutrient:chloride nutrient:mineral sys:part_of

