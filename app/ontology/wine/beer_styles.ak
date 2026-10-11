# Craft beer — styles and the drinker's vocabulary (A-tier).

def "beer:beer" "Beer — fermented from malted grain and hops (ビール)."
ln beer:beer beverage:fermented thesaurus:related

def "beer:ale" "Ale — warm, top-fermented beer; fruity and expressive (エール)."
def "beer:lager" "Lager — cold, bottom-fermented beer; clean and crisp (ラガー)."
ln beer:ale beer:beer thesaurus:related
ln beer:lager beer:beer thesaurus:related

def "beer:ipa" "India Pale Ale — hop-forward, bitter and aromatic."
ln beer:ipa beer:ale beer:style
def "beer:pale_ale" "Balanced hoppy ale, the craft gateway."
ln beer:pale_ale beer:ale beer:style
def "beer:hazy_ipa" "New-England IPA — soft, juicy, low-bitterness."
ln beer:hazy_ipa beer:ale beer:style
def "beer:stout" "Dark, roasty ale of coffee and chocolate notes."
ln beer:stout beer:ale beer:style
def "beer:porter" "Dark ale, lighter and sweeter than stout."
ln beer:porter beer:ale beer:style
def "beer:wheat_beer" "Cloudy wheat ale — banana/clove (hefeweizen, witbier)."
ln beer:wheat_beer beer:ale beer:style
def "beer:saison" "Dry, spicy Belgian farmhouse ale."
ln beer:saison beer:ale beer:style
def "beer:sour_beer" "Tart ale soured by wild yeast/bacteria (lambic, gose)."
ln beer:sour_beer beer:ale beer:style
def "beer:barleywine" "Strong, rich, ageworthy ale."
ln beer:barleywine beer:ale beer:style
def "beer:brown_ale" "Malty, nutty, sessionable ale."
ln beer:brown_ale beer:ale beer:style
def "beer:pilsner" "Pale, crisp, hop-snappy lager."
ln beer:pilsner beer:lager beer:style
def "beer:bock" "Strong malty lager."
ln beer:bock beer:lager beer:style
def "beer:amber_lager" "Toasty, balanced lager."
ln beer:amber_lager beer:lager beer:style

def "beer:hops" "The flower giving beer bitterness and aroma (ホップ)."
ln beer:hops beer:beer thesaurus:related
def "beer:malt" "Kilned grain giving body, colour and sweetness (麦芽)."
ln beer:malt beer:beer thesaurus:related
ln beer:malt foodsci:fermentation_science thesaurus:related
def "beer:abv" "Alcohol by volume — a beer's strength."
ln beer:abv beer:beer thesaurus:related
def "beer:ibu" "International Bitterness Units — measured hop bitterness."
ln beer:ibu beer:beer thesaurus:related
def "beer:dry_hopping" "Adding hops late/cold for aroma without bitterness."
ln beer:dry_hopping beer:beer thesaurus:related
def "beer:craft_brewery" "A small independent brewer prizing flavour over scale (クラフトビール)."
ln beer:craft_brewery beer:beer thesaurus:related
def "beer:session_beer" "A low-strength beer made for drinking several."
ln beer:session_beer beer:beer thesaurus:related
