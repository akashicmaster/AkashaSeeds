# Akasha ontology — grain & legume classification. Base pack.

def "grain_type:cereal" "True cereal grass grain."
def "grain_type:pseudocereal" "Non-grass seed used as grain."
def "legume_type:pulse" "Pulse — dried edible legume seed."
def "legume_type:oilseed" "Oil-rich legume seed."

ln ingred:grain:wheat grain_type:cereal bio:grain_type
ln ingred:grain:rice grain_type:cereal bio:grain_type
ln ingred:grain:corn grain_type:cereal bio:grain_type
ln ingred:grain:barley grain_type:cereal bio:grain_type
ln ingred:grain:oats grain_type:cereal bio:grain_type
ln ingred:grain:rye grain_type:cereal bio:grain_type
ln ingred:grain:millet grain_type:cereal bio:grain_type
ln ingred:grain:sorghum grain_type:cereal bio:grain_type
ln ingred:grain:quinoa grain_type:pseudocereal bio:grain_type
ln ingred:grain:amaranth grain_type:pseudocereal bio:grain_type
ln ingred:grain:buckwheat grain_type:pseudocereal bio:grain_type
ln ingred:legume:adzuki_bean legume_type:pulse bio:legume_type
ln ingred:legume:black_bean legume_type:pulse bio:legume_type
ln ingred:legume:chickpea legume_type:pulse bio:legume_type
ln ingred:legume:kidney_bean legume_type:pulse bio:legume_type
ln ingred:legume:lentil legume_type:pulse bio:legume_type
ln ingred:legume:mung_bean legume_type:pulse bio:legume_type
ln ingred:legume:peanut legume_type:oilseed bio:legume_type
ln ingred:legume:soybean legume_type:oilseed bio:legume_type
