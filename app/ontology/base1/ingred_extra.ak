# Akasha ontology — a couple of common foods missing from the ingredient set.
def "ingred:fruit:avocado" "A rich, buttery fruit high in monounsaturated fat."
al ingred:fruit:avocado avocado
ln ingred:fruit:avocado fruit_type:tropical bio:fruit_type
ln ingred:fruit:avocado fat_source:plant bio:fat_source
ln ingred:fruit:avocado plantpart:fruit_veg bio:plant_part

def "ingred:legume:tofu" "Soybean curd; a mild, protein-rich soy product."
al ingred:legume:tofu tofu
ln ingred:legume:tofu ingred:legume:soybean @derived_from
ln ingred:legume:tofu legume_type:oilseed bio:legume_type
ln ingred:legume:tofu dna:taste:umami calc:associated_with
