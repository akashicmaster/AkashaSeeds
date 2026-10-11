# Akasha ontology — napa (Chinese) cabbage, a major East-Asian leaf vegetable.
def "ingred:veg:napa_cabbage" "Napa / Chinese cabbage — a mild, crisp leafy brassica; the base of kimchi and many pickles. One of the most widely grown vegetables across East Asia."
al ingred:veg:napa_cabbage napa_cabbage
al ingred:veg:napa_cabbage napa
al ingred:veg:napa_cabbage hakusai
al ingred:veg:napa_cabbage wombok
ln ingred:veg:napa_cabbage plantpart:leaf bio:plant_part
ln ingred:veg:napa_cabbage dna:taste:sweet calc:associated_with
ln ingred:veg:napa_cabbage cuisine:chinese thesaurus:related
ln ingred:veg:napa_cabbage cuisine:korean thesaurus:related
# kimchi is made from napa cabbage
ln ingred:ferment:kimchi ingred:veg:napa_cabbage @derived_from
# curated sets
set.add name="culinary:pickling" id="ingred:veg:napa_cabbage"
