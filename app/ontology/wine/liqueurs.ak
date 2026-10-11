# Liqueurs & aperitifs — sweetened, flavoured spirits (A-tier).

def "liqueur:liqueur" "A sweetened, flavoured spirit (リキュール)."
ln liqueur:liqueur beverage:fortified thesaurus:related

def "liqueur:type:herbal" "Herb/spice-based (Chartreuse, amaro). liqueur."
def "liqueur:type:fruit" "Fruit-based (limoncello, triple sec). liqueur."
def "liqueur:type:cream" "Cream-based (Baileys). liqueur."
def "liqueur:type:coffee" "Coffee-based (Kahlúa). liqueur."
def "liqueur:type:bitter" "Bitter aperitif/digestif (Campari, Aperol, amaro). liqueur."
def "liqueur:amaretto" "Amaretto."
ln liqueur:amaretto liqueur:liqueur liqueur:is
ln liqueur:amaretto liqueur:type:fruit liqueur:kind
def "liqueur:cointreau" "Cointreau."
ln liqueur:cointreau liqueur:liqueur liqueur:is
ln liqueur:cointreau liqueur:type:fruit liqueur:kind
def "liqueur:triple_sec" "Triple Sec."
ln liqueur:triple_sec liqueur:liqueur liqueur:is
ln liqueur:triple_sec liqueur:type:fruit liqueur:kind
def "liqueur:limoncello" "Limoncello."
ln liqueur:limoncello liqueur:liqueur liqueur:is
ln liqueur:limoncello liqueur:type:fruit liqueur:kind
def "liqueur:grand_marnier" "Grand Marnier."
ln liqueur:grand_marnier liqueur:liqueur liqueur:is
ln liqueur:grand_marnier liqueur:type:fruit liqueur:kind
def "liqueur:chartreuse" "Chartreuse."
ln liqueur:chartreuse liqueur:liqueur liqueur:is
ln liqueur:chartreuse liqueur:type:herbal liqueur:kind
def "liqueur:benedictine" "Benedictine."
ln liqueur:benedictine liqueur:liqueur liqueur:is
ln liqueur:benedictine liqueur:type:herbal liqueur:kind
def "liqueur:sambuca" "Sambuca."
ln liqueur:sambuca liqueur:liqueur liqueur:is
ln liqueur:sambuca liqueur:type:herbal liqueur:kind
def "liqueur:campari" "Campari."
ln liqueur:campari liqueur:liqueur liqueur:is
ln liqueur:campari liqueur:type:bitter liqueur:kind
def "liqueur:aperol" "Aperol."
ln liqueur:aperol liqueur:liqueur liqueur:is
ln liqueur:aperol liqueur:type:bitter liqueur:kind
def "liqueur:amaro" "Amaro."
ln liqueur:amaro liqueur:liqueur liqueur:is
ln liqueur:amaro liqueur:type:bitter liqueur:kind
def "liqueur:vermouth" "Vermouth."
ln liqueur:vermouth liqueur:liqueur liqueur:is
ln liqueur:vermouth liqueur:type:bitter liqueur:kind
def "liqueur:baileys" "Baileys."
ln liqueur:baileys liqueur:liqueur liqueur:is
ln liqueur:baileys liqueur:type:cream liqueur:kind
def "liqueur:kahlua" "Kahlua."
ln liqueur:kahlua liqueur:liqueur liqueur:is
ln liqueur:kahlua liqueur:type:coffee liqueur:kind

def "liqueur:aperitif" "A drink before the meal to whet the appetite (食前酒)."
def "liqueur:digestif" "A drink after the meal to aid digestion (食後酒)."
ln liqueur:campari liqueur:aperitif thesaurus:related
ln liqueur:aperol liqueur:aperitif thesaurus:related
ln liqueur:amaro liqueur:digestif thesaurus:related
ln liqueur:aperitif beverage:alcohol thesaurus:related
