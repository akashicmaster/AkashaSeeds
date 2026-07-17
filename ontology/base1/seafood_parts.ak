# Akasha ontology — seafood parts & products (roe/milt/liver, fillet, surimi)
# Adds gonad/organ parts and cut/paste product forms to the seafood category,
# extends the cut_type axis (fillet/roe/milt), and links sources/derivations.
# Base pack.

def "cut_type:fillet" "Fillet — a boneless cut/slice of fish (切り身)."
def "cut_type:roe" "Roe — fish eggs / ovary (卵巣・魚卵)."
def "cut_type:milt" "Milt — soft roe / testes of male fish (精巣・白子)."

def "ingred:seafood:roe" "Fish roe — the egg mass (ovary) of fish; briny and rich."
al ingred:seafood:roe roe
ln ingred:seafood:roe cut_type:roe culinary:cut_type
ln ingred:seafood:roe dna:taste:salty calc:associated_with
ln ingred:seafood:roe dna:taste:umami calc:associated_with

def "ingred:seafood:milt" "Soft roe — the milt (testes) of male fish, e.g. shirako; creamy."
al ingred:seafood:milt milt
al ingred:seafood:milt shirako
ln ingred:seafood:milt cut_type:milt culinary:cut_type
ln ingred:seafood:milt dna:taste:umami calc:associated_with

def "ingred:seafood:fish_liver" "Fish liver, e.g. monkfish (ankimo) or cod liver; rich and creamy."
al ingred:seafood:fish_liver fish_liver
al ingred:seafood:fish_liver ankimo
ln ingred:seafood:fish_liver cut_type:offal culinary:cut_type
ln ingred:seafood:fish_liver dna:taste:umami calc:associated_with
ln ingred:seafood:fish_liver dna:taste:bitter calc:associated_with

def "ingred:seafood:ikura" "Salmon roe — large, glossy orange pearls."
al ingred:seafood:ikura ikura
ln ingred:seafood:ikura cut_type:roe culinary:cut_type
ln ingred:seafood:ikura ingred:seafood:salmon sys:part_of
ln ingred:seafood:ikura dna:taste:salty calc:associated_with
ln ingred:seafood:ikura dna:taste:umami calc:associated_with
ln ingred:seafood:ikura dna:color:orange calc:associated_with

def "ingred:seafood:tobiko" "Flying-fish roe — tiny, crunchy pearls."
al ingred:seafood:tobiko tobiko
ln ingred:seafood:tobiko cut_type:roe culinary:cut_type
ln ingred:seafood:tobiko dna:taste:salty calc:associated_with

def "ingred:seafood:mentaiko" "Spicy marinated pollock roe."
al ingred:seafood:mentaiko mentaiko
ln ingred:seafood:mentaiko cut_type:roe culinary:cut_type
ln ingred:seafood:mentaiko dna:taste:salty calc:associated_with

def "ingred:seafood:bottarga" "Cured, pressed grey-mullet or tuna roe."
al ingred:seafood:bottarga bottarga
ln ingred:seafood:bottarga cut_type:roe culinary:cut_type
ln ingred:seafood:bottarga dna:taste:salty calc:associated_with
ln ingred:seafood:bottarga dna:taste:umami calc:associated_with

def "ingred:seafood:fillet" "A boneless fillet or cut piece of fish (切り身)."
al ingred:seafood:fillet fillet
ln ingred:seafood:fillet cut_type:fillet culinary:cut_type

def "ingred:seafood:surimi" "Washed, minced fish paste — the base of fish cakes (すり身)."
al ingred:seafood:surimi surimi
ln ingred:seafood:surimi cut_type:processed culinary:cut_type
ln ingred:seafood:surimi dna:taste:umami calc:associated_with

def "ingred:seafood:kamaboko" "Steamed cured surimi fish cake."
al ingred:seafood:kamaboko kamaboko
ln ingred:seafood:kamaboko cut_type:processed culinary:cut_type
ln ingred:seafood:kamaboko ingred:seafood:surimi @derived_from
ln ingred:seafood:kamaboko dna:taste:umami calc:associated_with

def "ingred:seafood:chikuwa" "Grilled tube-shaped surimi."
al ingred:seafood:chikuwa chikuwa
ln ingred:seafood:chikuwa cut_type:processed culinary:cut_type
ln ingred:seafood:chikuwa ingred:seafood:surimi @derived_from
ln ingred:seafood:chikuwa dna:taste:umami calc:associated_with

def "ingred:seafood:fish_ball" "Bouncy boiled fish-paste balls."
al ingred:seafood:fish_ball fish_ball
ln ingred:seafood:fish_ball cut_type:processed culinary:cut_type
ln ingred:seafood:fish_ball ingred:seafood:surimi @derived_from
ln ingred:seafood:fish_ball dna:taste:umami calc:associated_with

def "ingred:seafood:imitation_crab" "Surimi shaped and coloured to mimic crab (kanikama)."
al ingred:seafood:imitation_crab imitation_crab
al ingred:seafood:imitation_crab kanikama
ln ingred:seafood:imitation_crab cut_type:processed culinary:cut_type
ln ingred:seafood:imitation_crab ingred:seafood:surimi @derived_from
ln ingred:seafood:imitation_crab dna:taste:umami calc:associated_with

ln ingred:seafood:mentaiko dna:pungency:hot calc:associated_with
ln ingred:seafood:caviar cut_type:roe culinary:cut_type
ln ingred:seafood:sea_urchin cut_type:roe culinary:cut_type   # uni = gonad
