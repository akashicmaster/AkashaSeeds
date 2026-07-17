# Akasha ontology — fish species + flesh_type (白身/赤身) + source (天然/養殖)
# Add missing food-fish species (incl. roe/liver source species), and two
# axes: flesh_type white/red for finfish, source wild/farmed for seafood.
# Base pack.

def "flesh_type:white" "White fish (白身) — lean, mild, pale flesh."
def "flesh_type:red" "Red/oily fish (赤身・青魚) — darker, richer, fattier flesh."
def "source:wild" "Wild-caught (天然)."
def "source:farmed" "Farmed / aquaculture (養殖)."

# ── new species ──
def "ingred:seafood:pollock" "A lean white cod-family fish; source of mentaiko and surimi."
al ingred:seafood:pollock pollock
ln ingred:seafood:pollock habitat:marine bio:habitat
ln ingred:seafood:pollock cut_type:whole culinary:cut_type
ln ingred:seafood:pollock dna:taste:umami calc:associated_with
def "ingred:seafood:flying_fish" "A marine fish whose roe (tobiko) is prized."
al ingred:seafood:flying_fish flying_fish
ln ingred:seafood:flying_fish habitat:marine bio:habitat
ln ingred:seafood:flying_fish cut_type:whole culinary:cut_type
ln ingred:seafood:flying_fish dna:taste:umami calc:associated_with
def "ingred:seafood:mullet" "Grey mullet; its roe is cured as bottarga."
al ingred:seafood:mullet mullet
ln ingred:seafood:mullet habitat:marine bio:habitat
ln ingred:seafood:mullet cut_type:whole culinary:cut_type
ln ingred:seafood:mullet dna:taste:umami calc:associated_with
def "ingred:seafood:monkfish" "A firm white fish; its liver (ankimo) is a delicacy."
al ingred:seafood:monkfish monkfish
ln ingred:seafood:monkfish habitat:marine bio:habitat
ln ingred:seafood:monkfish cut_type:whole culinary:cut_type
ln ingred:seafood:monkfish dna:taste:umami calc:associated_with
def "ingred:seafood:herring" "A small, oily, silvery schooling fish."
al ingred:seafood:herring herring
ln ingred:seafood:herring habitat:marine bio:habitat
ln ingred:seafood:herring cut_type:whole culinary:cut_type
ln ingred:seafood:herring dna:taste:umami calc:associated_with
def "ingred:seafood:anchovy" "A tiny, intensely savoury oily fish, often cured."
al ingred:seafood:anchovy anchovy
ln ingred:seafood:anchovy habitat:marine bio:habitat
ln ingred:seafood:anchovy cut_type:whole culinary:cut_type
ln ingred:seafood:anchovy dna:taste:umami calc:associated_with
ln ingred:seafood:anchovy dna:taste:salty calc:associated_with
def "ingred:seafood:swordfish" "A large meaty billfish with dense steaks."
al ingred:seafood:swordfish swordfish
ln ingred:seafood:swordfish habitat:marine bio:habitat
ln ingred:seafood:swordfish cut_type:whole culinary:cut_type
ln ingred:seafood:swordfish dna:taste:umami calc:associated_with
def "ingred:seafood:sole" "A delicate flatfish with fine white flesh."
al ingred:seafood:sole sole
ln ingred:seafood:sole habitat:marine bio:habitat
ln ingred:seafood:sole cut_type:whole culinary:cut_type
ln ingred:seafood:sole dna:taste:umami calc:associated_with
def "ingred:seafood:turbot" "A prized flatfish with firm white flesh."
al ingred:seafood:turbot turbot
ln ingred:seafood:turbot habitat:marine bio:habitat
ln ingred:seafood:turbot cut_type:whole culinary:cut_type
ln ingred:seafood:turbot dna:taste:umami calc:associated_with
def "ingred:seafood:hake" "A soft-fleshed white cod relative."
al ingred:seafood:hake hake
ln ingred:seafood:hake habitat:marine bio:habitat
ln ingred:seafood:hake cut_type:whole culinary:cut_type
ln ingred:seafood:hake dna:taste:umami calc:associated_with
def "ingred:seafood:haddock" "A mild white cod-family fish."
al ingred:seafood:haddock haddock
ln ingred:seafood:haddock habitat:marine bio:habitat
ln ingred:seafood:haddock cut_type:whole culinary:cut_type
ln ingred:seafood:haddock dna:taste:umami calc:associated_with
def "ingred:seafood:yellowtail" "Hamachi; a rich, buttery fish, often farmed."
al ingred:seafood:yellowtail yellowtail
ln ingred:seafood:yellowtail habitat:marine bio:habitat
ln ingred:seafood:yellowtail cut_type:whole culinary:cut_type
ln ingred:seafood:yellowtail dna:taste:umami calc:associated_with
def "ingred:seafood:bonito" "A small tuna relative, dried as katsuobushi."
al ingred:seafood:bonito bonito
ln ingred:seafood:bonito habitat:marine bio:habitat
ln ingred:seafood:bonito cut_type:whole culinary:cut_type
ln ingred:seafood:bonito dna:taste:umami calc:associated_with
def "ingred:seafood:mahi_mahi" "A firm, mild tropical fish (dorado)."
al ingred:seafood:mahi_mahi mahi_mahi
ln ingred:seafood:mahi_mahi habitat:marine bio:habitat
ln ingred:seafood:mahi_mahi cut_type:whole culinary:cut_type
ln ingred:seafood:mahi_mahi dna:taste:umami calc:associated_with
def "ingred:seafood:grouper" "A large firm white reef fish."
al ingred:seafood:grouper grouper
ln ingred:seafood:grouper habitat:marine bio:habitat
ln ingred:seafood:grouper cut_type:whole culinary:cut_type
ln ingred:seafood:grouper dna:taste:umami calc:associated_with
def "ingred:seafood:pomfret" "A flat silvery fish with tender white flesh."
al ingred:seafood:pomfret pomfret
ln ingred:seafood:pomfret habitat:marine bio:habitat
ln ingred:seafood:pomfret cut_type:whole culinary:cut_type
ln ingred:seafood:pomfret dna:taste:umami calc:associated_with
def "ingred:seafood:barramundi" "An Asian sea bass, widely farmed; buttery white flesh."
al ingred:seafood:barramundi barramundi
ln ingred:seafood:barramundi habitat:catadromous bio:habitat
ln ingred:seafood:barramundi cut_type:whole culinary:cut_type
ln ingred:seafood:barramundi dna:taste:umami calc:associated_with

# ── flesh_type (白身/赤身) ──
ln ingred:seafood:barramundi flesh_type:white bio:flesh_type
ln ingred:seafood:bream flesh_type:white bio:flesh_type
ln ingred:seafood:carp flesh_type:white bio:flesh_type
ln ingred:seafood:catfish flesh_type:white bio:flesh_type
ln ingred:seafood:cod flesh_type:white bio:flesh_type
ln ingred:seafood:flounder flesh_type:white bio:flesh_type
ln ingred:seafood:flying_fish flesh_type:white bio:flesh_type
ln ingred:seafood:grouper flesh_type:white bio:flesh_type
ln ingred:seafood:haddock flesh_type:white bio:flesh_type
ln ingred:seafood:hake flesh_type:white bio:flesh_type
ln ingred:seafood:halibut flesh_type:white bio:flesh_type
ln ingred:seafood:mahi_mahi flesh_type:white bio:flesh_type
ln ingred:seafood:monkfish flesh_type:white bio:flesh_type
ln ingred:seafood:mullet flesh_type:white bio:flesh_type
ln ingred:seafood:perch flesh_type:white bio:flesh_type
ln ingred:seafood:pike flesh_type:white bio:flesh_type
ln ingred:seafood:pollock flesh_type:white bio:flesh_type
ln ingred:seafood:pomfret flesh_type:white bio:flesh_type
ln ingred:seafood:sea_bass flesh_type:white bio:flesh_type
ln ingred:seafood:snapper flesh_type:white bio:flesh_type
ln ingred:seafood:sole flesh_type:white bio:flesh_type
ln ingred:seafood:sturgeon flesh_type:white bio:flesh_type
ln ingred:seafood:tilapia flesh_type:white bio:flesh_type
ln ingred:seafood:turbot flesh_type:white bio:flesh_type
ln ingred:seafood:walleye flesh_type:white bio:flesh_type
ln ingred:seafood:anchovy flesh_type:red bio:flesh_type
ln ingred:seafood:arctic_char flesh_type:red bio:flesh_type
ln ingred:seafood:bonito flesh_type:red bio:flesh_type
ln ingred:seafood:herring flesh_type:red bio:flesh_type
ln ingred:seafood:mackerel flesh_type:red bio:flesh_type
ln ingred:seafood:salmon flesh_type:red bio:flesh_type
ln ingred:seafood:sardine flesh_type:red bio:flesh_type
ln ingred:seafood:swordfish flesh_type:red bio:flesh_type
ln ingred:seafood:trout flesh_type:red bio:flesh_type
ln ingred:seafood:tuna flesh_type:red bio:flesh_type
ln ingred:seafood:yellowtail flesh_type:red bio:flesh_type

# ── source (天然/養殖) ──
ln ingred:seafood:anchovy source:wild bio:source
ln ingred:seafood:bonito source:wild bio:source
ln ingred:seafood:cod source:wild bio:source
ln ingred:seafood:crab source:wild bio:source
ln ingred:seafood:flounder source:wild bio:source
ln ingred:seafood:flying_fish source:wild bio:source
ln ingred:seafood:grouper source:wild bio:source
ln ingred:seafood:haddock source:wild bio:source
ln ingred:seafood:hake source:wild bio:source
ln ingred:seafood:halibut source:wild bio:source
ln ingred:seafood:herring source:wild bio:source
ln ingred:seafood:langoustine source:wild bio:source
ln ingred:seafood:lobster source:wild bio:source
ln ingred:seafood:mackerel source:wild bio:source
ln ingred:seafood:mahi_mahi source:wild bio:source
ln ingred:seafood:monkfish source:wild bio:source
ln ingred:seafood:mullet source:wild bio:source
ln ingred:seafood:octopus source:wild bio:source
ln ingred:seafood:perch source:wild bio:source
ln ingred:seafood:pike source:wild bio:source
ln ingred:seafood:pollock source:wild bio:source
ln ingred:seafood:pomfret source:wild bio:source
ln ingred:seafood:sardine source:wild bio:source
ln ingred:seafood:sea_urchin source:wild bio:source
ln ingred:seafood:snapper source:wild bio:source
ln ingred:seafood:sole source:wild bio:source
ln ingred:seafood:squid source:wild bio:source
ln ingred:seafood:swordfish source:wild bio:source
ln ingred:seafood:tuna source:wild bio:source
ln ingred:seafood:turbot source:wild bio:source
ln ingred:seafood:walleye source:wild bio:source
ln ingred:seafood:arctic_char source:farmed bio:source
ln ingred:seafood:barramundi source:farmed bio:source
ln ingred:seafood:carp source:farmed bio:source
ln ingred:seafood:catfish source:farmed bio:source
ln ingred:seafood:tilapia source:farmed bio:source
ln ingred:seafood:bream source:wild bio:source
ln ingred:seafood:bream source:farmed bio:source
ln ingred:seafood:clam source:wild bio:source
ln ingred:seafood:clam source:farmed bio:source
ln ingred:seafood:eel source:wild bio:source
ln ingred:seafood:eel source:farmed bio:source
ln ingred:seafood:kombu source:wild bio:source
ln ingred:seafood:kombu source:farmed bio:source
ln ingred:seafood:mussel source:wild bio:source
ln ingred:seafood:mussel source:farmed bio:source
ln ingred:seafood:oyster source:wild bio:source
ln ingred:seafood:oyster source:farmed bio:source
ln ingred:seafood:salmon source:wild bio:source
ln ingred:seafood:salmon source:farmed bio:source
ln ingred:seafood:scallop source:wild bio:source
ln ingred:seafood:scallop source:farmed bio:source
ln ingred:seafood:sea_bass source:wild bio:source
ln ingred:seafood:sea_bass source:farmed bio:source
ln ingred:seafood:shrimp source:wild bio:source
ln ingred:seafood:shrimp source:farmed bio:source
ln ingred:seafood:sturgeon source:wild bio:source
ln ingred:seafood:sturgeon source:farmed bio:source
ln ingred:seafood:trout source:wild bio:source
ln ingred:seafood:trout source:farmed bio:source
ln ingred:seafood:yellowtail source:wild bio:source
ln ingred:seafood:yellowtail source:farmed bio:source

# ── roe/liver → source species ──
ln ingred:seafood:mentaiko ingred:seafood:pollock sys:part_of
ln ingred:seafood:tobiko ingred:seafood:flying_fish sys:part_of
ln ingred:seafood:bottarga ingred:seafood:mullet sys:part_of
ln ingred:seafood:fish_liver ingred:seafood:monkfish sys:part_of
ln ingred:seafood:fish_liver ingred:seafood:cod sys:part_of
ln ingred:seafood:katsuobushi ingred:seafood:bonito @derived_from
