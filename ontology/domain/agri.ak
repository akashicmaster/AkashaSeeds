# Akasha ontology — namespace: agri
# atoms: 5

def "agri:concept:population_growth" "The increase in the number of individuals in a population, significantly boosted globally by calorie-dense New World crops."
ln agri:concept:population_growth sci:history:industrial_revolution @enables_labor_force_for

def "agri:crop:chili_pepper" "The fruit of plants from the genus Capsicum, used widely as a spice and heavily adopted in Asian and European cuisines after the Columbian Exchange."

def "agri:crop:maize" "Also known as corn, a cereal grain first domesticated by indigenous peoples in southern Mexico, highly efficient in converting sunlight into food."
ln agri:crop:maize chem:carbo:carbohydrate @rich_in
ln agri:crop:maize nutri:diet:calorie @provides_efficiently
ln agri:crop:maize agri:concept:population_growth @drives

def "agri:crop:potato" "A root vegetable native to the Americas, a starchy tuber of the plant Solanum tuberosum, highly resilient to cold and poor soils."
ln agri:crop:potato chem:carbo:carbohydrate @rich_in
ln agri:crop:potato nutri:diet:calorie @provides_efficiently
ln agri:crop:potato nutri:micronutrient:vitamin_c @contains
ln agri:crop:potato med:condition:famine @prevents
ln agri:crop:potato agri:concept:population_growth @drives

def "agri:crop:sweet_potato" "A plant with large, starchy, sweet-tasting tuberous roots, highly adaptable to tropical and warm temperate regions."
ln agri:crop:sweet_potato med:condition:famine @prevents
