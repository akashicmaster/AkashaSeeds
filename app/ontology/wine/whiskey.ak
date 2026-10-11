# Whisky/whiskey — types, regions and the taster's vocabulary (A-tier).

def "whiskey:whiskey" "Whisky — spirit distilled from fermented grain mash and cask-aged (ウイスキー)."
ln whiskey:whiskey beverage:distilled thesaurus:related
ln whiskey:whiskey chemeng:distillation thesaurus:related

def "whiskey:scotch" "Scotch whisky — malted barley, aged ≥3y in Scotland."
ln whiskey:scotch whiskey:whiskey whiskey:type
def "whiskey:single_malt" "From one distillery's malted barley — prized and expressive."
ln whiskey:single_malt whiskey:whiskey whiskey:type
def "whiskey:blended_whisky" "A blend of malt and grain whiskies."
ln whiskey:blended_whisky whiskey:whiskey whiskey:type
def "whiskey:bourbon" "American whiskey ≥51% corn, new charred-oak casks — sweet, vanilla."
ln whiskey:bourbon whiskey:whiskey whiskey:type
def "whiskey:rye_whiskey" "≥51% rye — spicy, dry."
ln whiskey:rye_whiskey whiskey:whiskey whiskey:type
def "whiskey:irish_whiskey" "Typically triple-distilled — smooth, light."
ln whiskey:irish_whiskey whiskey:whiskey whiskey:type
def "whiskey:japanese_whisky" "Scotch-inspired, refined and balanced (ジャパニーズウイスキー)."
ln whiskey:japanese_whisky whiskey:whiskey whiskey:type
def "whiskey:tennessee_whiskey" "Bourbon-like, charcoal-mellowed."
ln whiskey:tennessee_whiskey whiskey:whiskey whiskey:type

def "whiskey:peat" "Smoked malt giving Islay whisky its medicinal, smoky character (ピート)."
ln whiskey:peat whiskey:whiskey thesaurus:related
ln whiskey:peat whiskey:islay thesaurus:related
def "whiskey:cask_aging" "Maturation in oak barrels — where colour and much flavour form."
ln whiskey:cask_aging whiskey:whiskey thesaurus:related
def "whiskey:single_cask" "Bottled from one barrel, unblended."
ln whiskey:single_cask whiskey:whiskey thesaurus:related
def "whiskey:cask_strength" "Bottled undiluted, at barrel proof."
ln whiskey:cask_strength whiskey:whiskey thesaurus:related
def "whiskey:angels_share" "The whisky lost to evaporation during aging (エンジェルズシェア)."
ln whiskey:angels_share whiskey:whiskey thesaurus:related
def "whiskey:speyside" "Scotland's densest whisky region — elegant, fruity."
ln whiskey:speyside whiskey:whiskey thesaurus:related
ln whiskey:speyside whiskey:scotch thesaurus:related
def "whiskey:islay" "Scottish island of intensely peaty, maritime whiskies."
ln whiskey:islay whiskey:whiskey thesaurus:related
ln whiskey:islay whiskey:scotch thesaurus:related
