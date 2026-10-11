# Tea — Camellia sinensis by oxidation & origin, brewing, AND non-tea-tree
# tisanes (herbal infusions that are not true tea). A-tier. Bridged to cuisine:/
# foodsci:fermentation & the beverage layer.

def "tea:tea" "An infusion drunk hot or cold (茶)."
ln tea:tea beverage:cat:tea thesaurus:related

def "tea:true_tea" "True tea — from the Camellia sinensis plant; type set by oxidation (茶の木由来)."
def "tea:tisane" "A herbal infusion NOT from the tea plant (ハーブティー/tisane)."
ln tea:true_tea tea:tea thesaurus:related
ln tea:tisane tea:tea thesaurus:related

# ── true teas (Camellia sinensis) ──
def "tea:white_tea" "Barely oxidised, minimally processed — delicate, sweet (白茶)."
ln tea:white_tea tea:true_tea thesaurus:related
ln tea:white_tea tea:origin:china tea:from
def "tea:green_tea" "Unoxidised, heat-fixed — grassy, fresh (緑茶)."
ln tea:green_tea tea:true_tea thesaurus:related
ln tea:green_tea tea:origin:china tea:from
ln tea:green_tea tea:origin:japan tea:from
def "tea:yellow_tea" "Lightly oxidised, mellowed — rare Chinese type (黄茶)."
ln tea:yellow_tea tea:true_tea thesaurus:related
ln tea:yellow_tea tea:origin:china tea:from
def "tea:oolong" "Partially oxidised — floral to roasted (烏龍茶)."
ln tea:oolong tea:true_tea thesaurus:related
ln tea:oolong tea:origin:china tea:from
ln tea:oolong tea:origin:taiwan tea:from
def "tea:black_tea" "Fully oxidised — malty, robust (紅茶)."
ln tea:black_tea tea:true_tea thesaurus:related
ln tea:black_tea tea:origin:india tea:from
def "tea:puerh" "Post-fermented, aged — earthy, deep (普洱茶)."
ln tea:puerh tea:true_tea thesaurus:related
ln tea:puerh tea:origin:china tea:from
def "tea:matcha_tea" "Stone-ground shade-grown green tea powder (抹茶)."
ln tea:matcha_tea tea:true_tea thesaurus:related
ln tea:matcha_tea tea:origin:japan tea:from
def "tea:sencha" "Japan's everyday steamed green tea (煎茶)."
ln tea:sencha tea:true_tea thesaurus:related
ln tea:sencha tea:origin:japan tea:from
def "tea:darjeeling" "The 'champagne of teas', muscatel — Himalayan foothills."
ln tea:darjeeling tea:true_tea thesaurus:related
ln tea:darjeeling tea:origin:india tea:from
def "tea:assam" "Bold malty black tea from NE India."
ln tea:assam tea:true_tea thesaurus:related
ln tea:assam tea:origin:india tea:from
def "tea:ceylon" "Bright citrusy black tea from Sri Lanka."
ln tea:ceylon tea:true_tea thesaurus:related
def "tea:gyokuro" "Premium shaded Japanese green — umami-rich (玉露)."
ln tea:gyokuro tea:true_tea thesaurus:related
ln tea:gyokuro tea:origin:japan tea:from
ln tea:puerh foodsci:fermentation_science thesaurus:related
ln tea:oolong foodsci:fermentation_science thesaurus:related
ln tea:matcha_tea cuisine:japanese thesaurus:related

# ── tisanes / herbal infusions (NOT Camellia sinensis) ──
def "tea:chamomile" "Calming apple-scented flower infusion (カモミール)."
ln tea:chamomile tea:tisane thesaurus:related
def "tea:peppermint" "Cooling mint infusion."
ln tea:peppermint tea:tisane thesaurus:related
def "tea:rooibos" "South African red-bush — caffeine-free, sweet, earthy (ルイボス)."
ln tea:rooibos tea:tisane thesaurus:related
def "tea:hibiscus" "Tart ruby-red flower infusion."
ln tea:hibiscus tea:tisane thesaurus:related
def "tea:ginger_tea" "Warming spiced ginger infusion."
ln tea:ginger_tea tea:tisane thesaurus:related
def "tea:lemongrass_tea" "Citrusy grass infusion."
ln tea:lemongrass_tea tea:tisane thesaurus:related
def "tea:rosehip" "Tangy vitamin-C-rich fruit infusion."
ln tea:rosehip tea:tisane thesaurus:related
def "tea:yerba_mate" "South American caffeinated holly infusion — the mate ritual (マテ茶)."
ln tea:yerba_mate tea:tisane thesaurus:related
def "tea:lavender_tea" "Floral, soothing infusion."
ln tea:lavender_tea tea:tisane thesaurus:related
def "tea:barley_tea" "Roasted-barley caffeine-free tea (麦茶)."
ln tea:barley_tea tea:tisane thesaurus:related
def "tea:honeybush" "Honey-sweet South African bush tea."
ln tea:honeybush tea:tisane thesaurus:related
ln tea:yerba_mate cuisine:argentine thesaurus:related
ln tea:barley_tea cuisine:japanese thesaurus:related

# ── brewing ──
def "tea:steeping" "Infusing tea leaves in hot water; time and temperature set the result."
ln tea:steeping tea:tea thesaurus:related
def "tea:water_temperature" "Green/white teas want cooler water (70–80°C); black/herbal near boiling."
ln tea:water_temperature tea:tea thesaurus:related
def "tea:steep_time" "Longer steeping extracts more tannin and bitterness."
ln tea:steep_time tea:tea thesaurus:related
def "tea:gongfu_brewing" "Chinese small-pot, many-short-infusions method (工夫茶)."
ln tea:gongfu_brewing tea:tea thesaurus:related
ln tea:gongfu_brewing cuisine:chinese thesaurus:related
def "tea:cold_brew_tea" "Slow cold-water steeping — smooth, low bitterness."
ln tea:cold_brew_tea tea:tea thesaurus:related
def "tea:tea_ceremony" "The ritual preparation of tea (茶道/chanoyu)."
ln tea:tea_ceremony tea:tea thesaurus:related
ln tea:tea_ceremony cuisine:japanese thesaurus:related
