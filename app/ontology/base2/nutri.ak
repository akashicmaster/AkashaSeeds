# Akasha ontology — namespace: nutri
# atoms: 19

def "nutri:concept:bcaa" "Branched-chain amino acids, essential for muscle protein synthesis and recovery."
ln nutri:concept:bcaa nutri:role:muscle_synthesis @promotes

def "nutri:concept:conditionally_essential_amino_acid" "An amino acid that is normally nonessential but becomes essential under certain clinical conditions (e.g., stress, illness)."

def "nutri:concept:dietary_mineral" "A chemical element required as an essential nutrient by organisms to perform functions necessary for life."
ln nutri:concept:dietary_mineral nutri:concept:micronutrient sys:is_a

def "nutri:concept:essential_amino_acid" "An amino acid that cannot be synthesized de novo by the organism and thus must be supplied in its diet."
ln nutri:concept:essential_amino_acid med:condition:protein_deficiency @prevents

def "nutri:concept:macronutrient" "Nutrients that provide calories or energy and are required in large amounts to maintain body functions."
ln nutri:concept:macronutrient nutri:diet:calorie @provides

def "nutri:concept:micronutrient" "A chemical element or substance required in trace amounts for the normal growth and development of living organisms."
ln nutri:concept:micronutrient bio:metabolism:metabolism @supports

def "nutri:concept:nonessential_amino_acid" "An amino acid that can be synthesized by the human body and is not strictly required in the diet."

def "nutri:concept:nutrition" "The biochemical and physiological process by which an organism uses food to support its life."

def "nutri:concept:vitamin" "An organic molecule that is an essential micronutrient which an organism needs in small quantities for the proper functioning of its metabolism."
ln nutri:concept:vitamin nutri:concept:micronutrient sys:is_a

def "nutri:diet:basal_metabolic_rate" "The rate of energy expenditure per unit time by endothermic animals at rest."
ln nutri:diet:basal_metabolic_rate nutri:diet:calorie @consumes

def "nutri:diet:calorie" "A unit of energy, often used to express the nutritional value of foods."

def "nutri:diet:dietary_fiber" "The portion of plant-derived food that cannot be completely broken down by human digestive enzymes."
ln nutri:diet:dietary_fiber bio:metabolism:digestion @resists
ln nutri:diet:dietary_fiber nutri:diet:glycemic_index @lowers

def "nutri:diet:glycemic_index" "A number from 0 to 100 assigned to a food, representing the relative rise in the blood glucose level."
ln nutri:diet:glycemic_index chem:carbo:glucose @measures_impact_of

def "nutri:micronutrient:vitamin_a" "A group of unsaturated nutritional organic compounds that includes retinol, retinal, and several provitamin A carotenoids, vital for vision and immunity."
ln nutri:micronutrient:vitamin_a nutri:concept:vitamin sys:is_a
ln nutri:micronutrient:vitamin_a med:condition:night_blindness @prevents

def "nutri:micronutrient:vitamin_b12" "A water-soluble vitamin involved in the metabolism of every cell of the human body, a cofactor in DNA synthesis."
ln nutri:micronutrient:vitamin_b12 nutri:concept:vitamin sys:is_a
ln nutri:micronutrient:vitamin_b12 bio:role:coenzyme sys:is_a
ln nutri:micronutrient:vitamin_b12 med:condition:anemia @prevents

def "nutri:micronutrient:vitamin_c" "Ascorbic acid, a water-soluble vitamin involved in tissue repair, collagen formation, and the enzymatic production of certain neurotransmitters."
ln nutri:micronutrient:vitamin_c nutri:concept:vitamin sys:is_a
ln nutri:micronutrient:vitamin_c bio:role:antioxidant sys:is_a
ln nutri:micronutrient:vitamin_c chem:protein:collagen @essential_for
ln nutri:micronutrient:vitamin_c med:condition:scurvy @prevents

def "nutri:micronutrient:vitamin_d" "A group of fat-soluble secosteroids responsible for increasing intestinal absorption of calcium, magnesium, and phosphate."
ln nutri:micronutrient:vitamin_d nutri:concept:vitamin sys:is_a
ln nutri:micronutrient:vitamin_d chem:element:calcium @regulates_absorption

def "nutri:role:muscle_synthesis" "The biological process of building new muscle tissue."

def "nutri:role:neurotransmitter_precursor" "A substance from which a neurotransmitter is formed."
