# Spirits — the world's distilled drinks, by base and character (A-tier).

def "spirit:spirit" "A distilled alcoholic spirit (蒸留酒)."
ln spirit:spirit beverage:distilled thesaurus:related
ln spirit:spirit chemeng:distillation thesaurus:related

def "spirit:vodka" "Neutral, clean spirit — the blank canvas (ウォッカ)."
ln spirit:vodka spirit:spirit spirit:type
def "spirit:gin" "Neutral spirit redistilled with juniper and botanicals (ジン)."
ln spirit:gin spirit:spirit spirit:type
def "spirit:rum" "Spirit from cane juice or molasses — crisp white to rich aged (ラム)."
ln spirit:rum spirit:spirit spirit:type
def "spirit:tequila" "Mexican agave spirit from Jalisco (テキーラ)."
ln spirit:tequila spirit:spirit spirit:type
def "spirit:mezcal" "Smoky agave spirit, roasted in earth pits (メスカル)."
ln spirit:mezcal spirit:spirit spirit:type
def "spirit:brandy" "Distilled wine, cask-aged (ブランデー)."
ln spirit:brandy spirit:spirit spirit:type
def "spirit:cognac" "France's benchmark brandy, double-distilled, oak-aged."
ln spirit:cognac spirit:spirit spirit:type
def "spirit:grappa" "Italian pomace brandy — fiery, aromatic."
ln spirit:grappa spirit:spirit spirit:type
def "spirit:pisco" "Andean grape brandy (Peru/Chile), unaged."
ln spirit:pisco spirit:spirit spirit:type
def "spirit:baijiu" "China's fragrant grain spirit — the world's most-drunk (白酒)."
ln spirit:baijiu spirit:spirit spirit:type
def "spirit:soju" "Korea's light, clean spirit (焼酎/소주)."
ln spirit:soju spirit:spirit spirit:type
def "spirit:aquavit" "Nordic caraway/dill-spiced spirit."
ln spirit:aquavit spirit:spirit spirit:type

ln spirit:tequila cuisine:mexican thesaurus:related
ln spirit:baijiu cuisine:chinese thesaurus:related
ln spirit:soju cuisine:korean thesaurus:related

def "spirit:botanicals" "Aromatic plants (juniper, citrus) flavouring gin and others."
ln spirit:botanicals spirit:spirit thesaurus:related
ln spirit:botanicals spirit:gin thesaurus:related
def "spirit:proof" "A measure of alcoholic strength (2× ABV in the US)."
ln spirit:proof spirit:spirit thesaurus:related
def "spirit:neutral_spirit" "A near-flavourless high-proof spirit, the base for gin/vodka/liqueurs."
ln spirit:neutral_spirit spirit:spirit thesaurus:related
def "spirit:pot_still" "A batch still giving characterful spirit."
ln spirit:pot_still spirit:spirit thesaurus:related
ln spirit:pot_still chemeng:distillation thesaurus:related
def "spirit:column_still" "A continuous still giving clean, high-proof spirit."
ln spirit:column_still spirit:spirit thesaurus:related
ln spirit:column_still chemeng:distillation thesaurus:related
