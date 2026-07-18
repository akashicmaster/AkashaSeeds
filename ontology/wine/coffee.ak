# Coffee — species, origins, roast and brewing (A-tier).

def "coffee:coffee" "Brewed from roasted, ground coffee beans (コーヒー)."
ln coffee:coffee beverage:cat:coffee thesaurus:related

def "coffee:arabica" "The finer, sweeter, lower-caffeine coffee species (アラビカ)."
def "coffee:robusta" "Hardier, more bitter, higher-caffeine species (ロブスタ)."
ln coffee:arabica coffee:coffee thesaurus:related
ln coffee:robusta coffee:coffee thesaurus:related

# ── origins ──
def "coffee:ethiopian_coffee" "Coffee's birthplace — floral, fruity, tea-like (Yirgacheffe/Sidamo)."
ln coffee:ethiopian_coffee coffee:coffee coffee:origin
def "coffee:colombian_coffee" "Balanced, nutty, caramel — a benchmark origin."
ln coffee:colombian_coffee coffee:coffee coffee:origin
def "coffee:brazilian_coffee" "Chocolatey, low-acid, the espresso backbone."
ln coffee:brazilian_coffee coffee:coffee coffee:origin
def "coffee:kenyan_coffee" "Bright, blackcurrant, wine-like acidity."
ln coffee:kenyan_coffee coffee:coffee coffee:origin
def "coffee:jamaica_blue_mountain" "Mild, smooth, prized and costly."
ln coffee:jamaica_blue_mountain coffee:coffee coffee:origin
def "coffee:yemen_mocha" "Ancient port origin — winey, chocolatey (the 'mocha')."
ln coffee:yemen_mocha coffee:coffee coffee:origin
def "coffee:guatemalan_coffee" "Cocoa, spice, full body."
ln coffee:guatemalan_coffee coffee:coffee coffee:origin
def "coffee:vietnamese_coffee" "Robusta powerhouse — bold, served with condensed milk."
ln coffee:vietnamese_coffee coffee:coffee coffee:origin
ln coffee:ethiopian_coffee foodstud:spice_trade thesaurus:related
ln coffee:yemen_mocha foodstud:spice_trade thesaurus:related

# ── roast & brewing ──
def "coffee:light_roast" "Bright, acidic, origin-expressive roast."
ln coffee:light_roast coffee:coffee thesaurus:related
def "coffee:medium_roast" "Balanced roast, sweetness and body."
ln coffee:medium_roast coffee:coffee thesaurus:related
def "coffee:dark_roast" "Bold, roasty, bitter-sweet roast."
ln coffee:dark_roast coffee:coffee thesaurus:related
def "coffee:espresso_brew" "High-pressure concentrated extraction."
ln coffee:espresso_brew coffee:coffee thesaurus:related
def "coffee:pour_over" "Hand-poured filter method — clean, bright (V60/Kalita)."
ln coffee:pour_over coffee:coffee thesaurus:related
def "coffee:french_press" "Full-immersion plunger method — full-bodied."
ln coffee:french_press coffee:coffee thesaurus:related
def "coffee:aeropress" "Pressure-plunger immersion — versatile."
ln coffee:aeropress coffee:coffee thesaurus:related
def "coffee:moka_pot" "Stovetop pressure brewer — strong, Italian."
ln coffee:moka_pot coffee:coffee thesaurus:related
ln coffee:moka_pot cuisine:italian thesaurus:related
def "coffee:cold_brew_coffee" "Cold slow steeping — smooth, low-acid."
ln coffee:cold_brew_coffee coffee:coffee thesaurus:related
def "coffee:turkish_coffee" "Very fine grounds simmered unfiltered (トルココーヒー)."
ln coffee:turkish_coffee coffee:coffee thesaurus:related
ln coffee:turkish_coffee cuisine:turkish thesaurus:related
def "coffee:single_origin" "Coffee from one origin, not blended."
ln coffee:single_origin coffee:coffee thesaurus:related
def "coffee:third_wave" "Coffee treated as an artisanal, origin-focused craft."
ln coffee:third_wave coffee:coffee thesaurus:related
