# Akasha ontology — evidence-based Western dietary patterns + glycemic index.
# Modern nutrition science (distinct from the traditional foodtherapy frame).

def "dietary_pattern" "Evidence-based dietary patterns studied in nutrition science."
def "diet:mediterranean" "Mediterranean diet — olive oil, fish, legumes, vegetables, whole grains; strong CVD evidence."
ln diet:mediterranean dietary_pattern thesaurus:related
def "diet:dash" "DASH — fruit, vegetables, whole grains, low-fat dairy, low sodium; lowers blood pressure."
ln diet:dash dietary_pattern thesaurus:related
def "diet:low_gi" "Low-glycaemic-index eating — slow-digesting carbohydrates; glycaemic control."
ln diet:low_gi dietary_pattern thesaurus:related
def "diet:plant_based" "Plant-based / plant-forward eating."
ln diet:plant_based dietary_pattern thesaurus:related
def "diet:keto" "Ketogenic / very-low-carbohydrate."
ln diet:keto dietary_pattern thesaurus:related
def "diet:high_fiber" "High-fibre eating."
ln diet:high_fiber dietary_pattern thesaurus:related
def "diet:low_sodium" "Low-sodium eating."
ln diet:low_sodium dietary_pattern thesaurus:related
def "gi_level:low" "Low glycaemic index (≲55)."
def "gi_level:medium" "Medium GI (56–69)."
def "gi_level:high" "High GI (≳70)."

# ── foods emphasised in each pattern ──
ln ingred:condiment:olive_oil diet:mediterranean diet:emphasized_in
ln ingred:seafood:salmon diet:mediterranean diet:emphasized_in
ln ingred:seafood:sardine diet:mediterranean diet:emphasized_in
ln ingred:seafood:mackerel diet:mediterranean diet:emphasized_in
ln ingred:seafood:anchovy diet:mediterranean diet:emphasized_in
ln ingred:seafood:tuna diet:mediterranean diet:emphasized_in
ln ingred:nut:almond diet:mediterranean diet:emphasized_in
ln ingred:nut:walnut diet:mediterranean diet:emphasized_in
ln ingred:legume:lentil diet:mediterranean diet:emphasized_in
ln ingred:legume:chickpea diet:mediterranean diet:emphasized_in
ln ingred:veg:tomato diet:mediterranean diet:emphasized_in
ln ingred:veg:eggplant diet:mediterranean diet:emphasized_in
ln ingred:veg:spinach diet:mediterranean diet:emphasized_in
ln ingred:veg:garlic diet:mediterranean diet:emphasized_in
ln ingred:ferment:yogurt diet:mediterranean diet:emphasized_in
ln ingred:grain:barley diet:mediterranean diet:emphasized_in
ln ingred:grain:oats diet:mediterranean diet:emphasized_in
ln ingred:herb:basil diet:mediterranean diet:emphasized_in
ln ingred:herb:oregano diet:mediterranean diet:emphasized_in
ln ingred:herb:rosemary diet:mediterranean diet:emphasized_in
ln ingred:legume:lentil diet:plant_based diet:emphasized_in
ln ingred:legume:chickpea diet:plant_based diet:emphasized_in
ln ingred:legume:black_bean diet:plant_based diet:emphasized_in
ln ingred:legume:kidney_bean diet:plant_based diet:emphasized_in
ln ingred:legume:mung_bean diet:plant_based diet:emphasized_in
ln ingred:veg:spinach diet:plant_based diet:emphasized_in
ln ingred:veg:kale diet:plant_based diet:emphasized_in
ln ingred:veg:broccoli diet:plant_based diet:emphasized_in
ln ingred:grain:quinoa diet:plant_based diet:emphasized_in
ln ingred:grain:oats diet:plant_based diet:emphasized_in
ln ingred:nut:almond diet:plant_based diet:emphasized_in
ln ingred:nut:walnut diet:plant_based diet:emphasized_in
ln ingred:seed:flax diet:plant_based diet:emphasized_in
ln ingred:seed:chia diet:plant_based diet:emphasized_in
ln ingred:legume:tofu diet:plant_based diet:emphasized_in
ln ingred:legume:lentil diet:low_gi diet:emphasized_in
ln ingred:legume:chickpea diet:low_gi diet:emphasized_in
ln ingred:legume:black_bean diet:low_gi diet:emphasized_in
ln ingred:legume:kidney_bean diet:low_gi diet:emphasized_in
ln ingred:legume:mung_bean diet:low_gi diet:emphasized_in
ln ingred:grain:barley diet:low_gi diet:emphasized_in
ln ingred:grain:oats diet:low_gi diet:emphasized_in
ln ingred:grain:quinoa diet:low_gi diet:emphasized_in
ln ingred:fruit:apple diet:low_gi diet:emphasized_in
ln ingred:fruit:pear diet:low_gi diet:emphasized_in
ln ingred:fruit:cherry diet:low_gi diet:emphasized_in
ln ingred:veg:broccoli diet:low_gi diet:emphasized_in
ln ingred:veg:spinach diet:low_gi diet:emphasized_in
ln ingred:veg:cucumber diet:low_gi diet:emphasized_in
ln ingred:veg:lettuce diet:low_gi diet:emphasized_in
ln ingred:nut:almond diet:low_gi diet:emphasized_in
ln ingred:nut:walnut diet:low_gi diet:emphasized_in
ln ingred:seafood:salmon diet:keto diet:emphasized_in
ln ingred:seafood:mackerel diet:keto diet:emphasized_in
ln ingred:meat:beef diet:keto diet:emphasized_in
ln ingred:meat:chicken diet:keto diet:emphasized_in
ln ingred:condiment:olive_oil diet:keto diet:emphasized_in
ln ingred:fruit:avocado diet:keto diet:emphasized_in
ln ingred:nut:almond diet:keto diet:emphasized_in
ln ingred:nut:walnut diet:keto diet:emphasized_in
ln ingred:veg:spinach diet:keto diet:emphasized_in
ln ingred:veg:cucumber diet:keto diet:emphasized_in
ln ingred:veg:lettuce diet:keto diet:emphasized_in
ln ingred:veg:eggplant diet:keto diet:emphasized_in
ln ingred:ferment:cheese diet:keto diet:emphasized_in
ln ingred:legume:lentil diet:high_fiber diet:emphasized_in
ln ingred:legume:chickpea diet:high_fiber diet:emphasized_in
ln ingred:legume:black_bean diet:high_fiber diet:emphasized_in
ln ingred:legume:kidney_bean diet:high_fiber diet:emphasized_in
ln ingred:grain:oats diet:high_fiber diet:emphasized_in
ln ingred:grain:barley diet:high_fiber diet:emphasized_in
ln ingred:grain:quinoa diet:high_fiber diet:emphasized_in
ln ingred:veg:broccoli diet:high_fiber diet:emphasized_in
ln ingred:veg:spinach diet:high_fiber diet:emphasized_in
ln ingred:seed:chia diet:high_fiber diet:emphasized_in
ln ingred:seed:flax diet:high_fiber diet:emphasized_in
ln ingred:nut:almond diet:high_fiber diet:emphasized_in
ln ingred:fruit:pear diet:high_fiber diet:emphasized_in
ln ingred:fruit:apple diet:high_fiber diet:emphasized_in
ln ingred:fruit:apple diet:dash diet:emphasized_in
ln ingred:fruit:pear diet:dash diet:emphasized_in
ln ingred:fruit:banana diet:dash diet:emphasized_in
ln ingred:veg:spinach diet:dash diet:emphasized_in
ln ingred:veg:broccoli diet:dash diet:emphasized_in
ln ingred:veg:carrot diet:dash diet:emphasized_in
ln ingred:grain:oats diet:dash diet:emphasized_in
ln ingred:grain:barley diet:dash diet:emphasized_in
ln ingred:legume:lentil diet:dash diet:emphasized_in
ln ingred:legume:chickpea diet:dash diet:emphasized_in
ln ingred:nut:almond diet:dash diet:emphasized_in
ln ingred:ferment:yogurt diet:dash diet:emphasized_in
ln ingred:condiment:sugar diet:low_gi diet:limited_in
ln ingred:condiment:sugar diet:keto diet:limited_in
ln ingred:condiment:sugar diet:dash diet:limited_in
ln ingred:condiment:honey diet:keto diet:limited_in
ln ingred:veg:potato diet:low_gi diet:limited_in
ln ingred:veg:potato diet:keto diet:limited_in
ln ingred:condiment:salt diet:low_sodium diet:limited_in
ln ingred:condiment:salt diet:dash diet:limited_in
ln ingred:condiment:soy_sauce diet:low_sodium diet:limited_in

# ── glycaemic index level ──
ln ingred:legume:lentil gi_level:low nutrition:glycemic
ln ingred:legume:chickpea gi_level:low nutrition:glycemic
ln ingred:legume:black_bean gi_level:low nutrition:glycemic
ln ingred:legume:kidney_bean gi_level:low nutrition:glycemic
ln ingred:legume:mung_bean gi_level:low nutrition:glycemic
ln ingred:legume:adzuki_bean gi_level:low nutrition:glycemic
ln ingred:legume:soybean gi_level:low nutrition:glycemic
ln ingred:grain:barley gi_level:low nutrition:glycemic
ln ingred:grain:oats gi_level:low nutrition:glycemic
ln ingred:grain:quinoa gi_level:low nutrition:glycemic
ln ingred:fruit:apple gi_level:low nutrition:glycemic
ln ingred:fruit:pear gi_level:low nutrition:glycemic
ln ingred:fruit:cherry gi_level:low nutrition:glycemic
ln ingred:fruit:grapefruit gi_level:low nutrition:glycemic
ln ingred:fruit:peach gi_level:low nutrition:glycemic
ln ingred:fruit:plum gi_level:low nutrition:glycemic
ln ingred:fruit:orange gi_level:low nutrition:glycemic
ln ingred:veg:carrot gi_level:low nutrition:glycemic
ln ingred:veg:broccoli gi_level:low nutrition:glycemic
ln ingred:veg:spinach gi_level:low nutrition:glycemic
ln ingred:veg:cucumber gi_level:low nutrition:glycemic
ln ingred:veg:lettuce gi_level:low nutrition:glycemic
ln ingred:veg:eggplant gi_level:low nutrition:glycemic
ln ingred:veg:tomato gi_level:low nutrition:glycemic
ln ingred:nut:almond gi_level:low nutrition:glycemic
ln ingred:nut:walnut gi_level:low nutrition:glycemic
ln ingred:ferment:yogurt gi_level:low nutrition:glycemic
ln ingred:grain:rice gi_level:medium nutrition:glycemic
ln ingred:veg:sweet_potato gi_level:medium nutrition:glycemic
ln ingred:grain:corn gi_level:medium nutrition:glycemic
ln ingred:fruit:banana gi_level:medium nutrition:glycemic
ln ingred:fruit:grape gi_level:medium nutrition:glycemic
ln ingred:grain:buckwheat gi_level:medium nutrition:glycemic
ln ingred:fruit:mango gi_level:medium nutrition:glycemic
ln ingred:fruit:pineapple gi_level:medium nutrition:glycemic
ln ingred:dry_good:couscous gi_level:medium nutrition:glycemic
ln ingred:veg:potato gi_level:high nutrition:glycemic
ln ingred:condiment:sugar gi_level:high nutrition:glycemic
ln ingred:condiment:honey gi_level:high nutrition:glycemic
ln ingred:fruit:watermelon gi_level:high nutrition:glycemic
ln ingred:flour:cornmeal gi_level:high nutrition:glycemic
ln ingred:flour:cornstarch gi_level:high nutrition:glycemic
ln ingred:condiment:maple_syrup gi_level:high nutrition:glycemic
