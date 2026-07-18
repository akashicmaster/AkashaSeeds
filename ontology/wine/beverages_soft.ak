# Non-alcoholic beverages — the everyday drinker's map (A-tier).
# Broadens beverage: beyond alcohol. Bridged to tasting:/cuisine:/foodsci:.

def "beverage:soft" "Non-alcoholic drinks (ソフトドリンク)."
ln beverage:soft beverage:alcohol thesaurus:related

def "beverage:cat:soft_drink" "Carbonated/sweet soft drinks."
ln beverage:cat:soft_drink beverage:soft thesaurus:related
def "beverage:cat:juice" "Pressed fruit/vegetable juice."
ln beverage:cat:juice beverage:soft thesaurus:related
def "beverage:cat:tea" "Infusions of the tea plant and herbs."
ln beverage:cat:tea beverage:soft thesaurus:related
def "beverage:cat:coffee" "Brewed from roasted coffee beans."
ln beverage:cat:coffee beverage:soft thesaurus:related
def "beverage:cat:water_drink" "Drinking water, still or sparkling."
ln beverage:cat:water_drink beverage:soft thesaurus:related
def "beverage:cat:dairy_drink" "Milk-based drinks."
ln beverage:cat:dairy_drink beverage:soft thesaurus:related
def "beverage:cat:functional_drink" "Energy/sports/health drinks."
ln beverage:cat:functional_drink beverage:soft thesaurus:related

def "beverage:cola" "Sweet caramel-coloured carbonated drink."
ln beverage:cola beverage:cat:soft_drink beverage:kind
def "beverage:lemonade" "Lemon (or lemon-lime) sweet drink."
ln beverage:lemonade beverage:cat:soft_drink beverage:kind
def "beverage:ginger_ale" "Ginger-flavoured soda."
ln beverage:ginger_ale beverage:cat:soft_drink beverage:kind
def "beverage:tonic_water" "Quinine-bittered soda, the gin partner."
ln beverage:tonic_water beverage:cat:soft_drink beverage:kind
def "beverage:soda_water" "Plain carbonated water (club soda)."
ln beverage:soda_water beverage:cat:soft_drink beverage:kind
def "beverage:orange_juice" "Pressed orange juice (オレンジジュース)."
ln beverage:orange_juice beverage:cat:juice beverage:kind
def "beverage:apple_juice" "Pressed apple juice."
ln beverage:apple_juice beverage:cat:juice beverage:kind
def "beverage:tomato_juice" "Savoury tomato juice — the Bloody Mary base."
ln beverage:tomato_juice beverage:cat:juice beverage:kind
def "beverage:smoothie" "Blended fruit (and dairy) drink."
ln beverage:smoothie beverage:cat:juice beverage:kind
def "beverage:green_tea" "Unoxidised tea — grassy, fresh (緑茶)."
ln beverage:green_tea beverage:cat:tea beverage:kind
def "beverage:black_tea" "Fully oxidised tea — malty, robust (紅茶)."
ln beverage:black_tea beverage:cat:tea beverage:kind
def "beverage:oolong_tea" "Partially oxidised tea (烏龍茶)."
ln beverage:oolong_tea beverage:cat:tea beverage:kind
def "beverage:matcha" "Stone-ground powdered green tea (抹茶)."
ln beverage:matcha beverage:cat:tea beverage:kind
def "beverage:herbal_tea" "Caffeine-free infusion of herbs/flowers."
ln beverage:herbal_tea beverage:cat:tea beverage:kind
def "beverage:chai" "Spiced milk tea (チャイ)."
ln beverage:chai beverage:cat:tea beverage:kind
def "beverage:espresso" "Concentrated pressure-brewed coffee (エスプレッソ)."
ln beverage:espresso beverage:cat:coffee beverage:kind
def "beverage:latte" "Espresso with steamed milk (カフェラテ)."
ln beverage:latte beverage:cat:coffee beverage:kind
def "beverage:cappuccino" "Espresso with equal steamed milk and foam."
ln beverage:cappuccino beverage:cat:coffee beverage:kind
def "beverage:cold_brew" "Slow cold-water-steeped coffee — smooth, low-acid."
ln beverage:cold_brew beverage:cat:coffee beverage:kind
def "beverage:drip_coffee" "Filter-brewed coffee."
ln beverage:drip_coffee beverage:cat:coffee beverage:kind
def "beverage:mineral_water" "Bottled spring/mineral water."
ln beverage:mineral_water beverage:cat:water_drink beverage:kind
def "beverage:sparkling_water" "Carbonated water (炭酸水)."
ln beverage:sparkling_water beverage:cat:water_drink beverage:kind
def "beverage:milk" "Cow's (or plant) milk (牛乳)."
ln beverage:milk beverage:cat:dairy_drink beverage:kind
def "beverage:hot_chocolate" "Warm cocoa-and-milk drink."
ln beverage:hot_chocolate beverage:cat:dairy_drink beverage:kind
def "beverage:kombucha" "Fermented, lightly effervescent sweet tea (コンブチャ)."
ln beverage:kombucha beverage:cat:functional_drink beverage:kind
def "beverage:energy_drink" "Caffeine/sugar stimulant drink."
ln beverage:energy_drink beverage:cat:functional_drink beverage:kind
def "beverage:sports_drink" "Electrolyte hydration drink."
ln beverage:sports_drink beverage:cat:functional_drink beverage:kind
def "beverage:mocktail" "An alcohol-free cocktail (モクテル)."
ln beverage:mocktail beverage:cat:soft_drink beverage:kind

# a few cross-links
ln beverage:matcha cuisine:japanese thesaurus:related
ln beverage:kombucha foodsci:fermentation_science thesaurus:related
ln beverage:green_tea foodsci:fermentation_science thesaurus:related
ln beverage:tonic_water spirit:gin thesaurus:related
ln beverage:mocktail cocktail:cocktail thesaurus:related
