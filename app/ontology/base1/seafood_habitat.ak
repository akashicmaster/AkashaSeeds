# Akasha ontology — seafood habitat axis + freshwater/anadromous fish
# 1) habitat concepts (marine/freshwater/anadromous/catadromous) and a
#    bio:habitat link on every seafood ingredient (sea vs river distinction).
# 2) new freshwater & anadromous fish concepts with habitat + taste links.

def "habitat:marine" "Marine (saltwater) habitat — seas and oceans."
def "habitat:freshwater" "Freshwater habitat — rivers, lakes, ponds, and streams."
def "habitat:anadromous" "Anadromous: hatched in freshwater, matures at sea (e.g. salmon, sturgeon)."
def "habitat:catadromous" "Catadromous: hatched at sea, matures in freshwater (e.g. eel)."

# ── existing seafood → habitat ──
ln ingred:seafood:clam habitat:marine bio:habitat
ln ingred:seafood:cod habitat:marine bio:habitat
ln ingred:seafood:crab habitat:marine bio:habitat
ln ingred:seafood:flounder habitat:marine bio:habitat
ln ingred:seafood:halibut habitat:marine bio:habitat
ln ingred:seafood:kombu habitat:marine bio:habitat
ln ingred:seafood:langoustine habitat:marine bio:habitat
ln ingred:seafood:lobster habitat:marine bio:habitat
ln ingred:seafood:mackerel habitat:marine bio:habitat
ln ingred:seafood:mussel habitat:marine bio:habitat
ln ingred:seafood:octopus habitat:marine bio:habitat
ln ingred:seafood:oyster habitat:marine bio:habitat
ln ingred:seafood:sardine habitat:marine bio:habitat
ln ingred:seafood:scallop habitat:marine bio:habitat
ln ingred:seafood:sea_bass habitat:marine bio:habitat
ln ingred:seafood:sea_urchin habitat:marine bio:habitat
ln ingred:seafood:shrimp habitat:marine bio:habitat
ln ingred:seafood:snapper habitat:marine bio:habitat
ln ingred:seafood:squid habitat:marine bio:habitat
ln ingred:seafood:tuna habitat:marine bio:habitat
ln ingred:seafood:salmon habitat:anadromous bio:habitat
ln ingred:seafood:caviar habitat:anadromous bio:habitat
ln ingred:seafood:eel habitat:catadromous bio:habitat

# ── new freshwater / anadromous fish ──
def "ingred:seafood:trout" "A freshwater game fish with delicate, flaky, pink-tinged flesh."
al ingred:seafood:trout trout
ln ingred:seafood:trout habitat:freshwater bio:habitat
ln ingred:seafood:trout dna:taste:umami calc:associated_with
ln ingred:seafood:trout dna:taste:sweet calc:associated_with

def "ingred:seafood:carp" "A hardy freshwater fish with rich, earthy, slightly muddy flesh."
al ingred:seafood:carp carp
ln ingred:seafood:carp habitat:freshwater bio:habitat
ln ingred:seafood:carp dna:taste:umami calc:associated_with

def "ingred:seafood:catfish" "A freshwater bottom-feeder with firm, mild, slightly sweet flesh."
al ingred:seafood:catfish catfish
ln ingred:seafood:catfish habitat:freshwater bio:habitat
ln ingred:seafood:catfish dna:taste:umami calc:associated_with

def "ingred:seafood:tilapia" "A mild, lean, white-fleshed freshwater fish farmed worldwide."
al ingred:seafood:tilapia tilapia
ln ingred:seafood:tilapia habitat:freshwater bio:habitat
ln ingred:seafood:tilapia dna:taste:umami calc:associated_with

def "ingred:seafood:perch" "A freshwater fish with firm, white, delicate flesh."
al ingred:seafood:perch perch
ln ingred:seafood:perch habitat:freshwater bio:habitat
ln ingred:seafood:perch dna:taste:umami calc:associated_with

def "ingred:seafood:pike" "A predatory freshwater fish with lean, firm white flesh."
al ingred:seafood:pike pike
ln ingred:seafood:pike habitat:freshwater bio:habitat
ln ingred:seafood:pike dna:taste:umami calc:associated_with

def "ingred:seafood:walleye" "A prized freshwater fish with sweet, flaky white flesh."
al ingred:seafood:walleye walleye
ln ingred:seafood:walleye habitat:freshwater bio:habitat
ln ingred:seafood:walleye dna:taste:umami calc:associated_with
ln ingred:seafood:walleye dna:taste:sweet calc:associated_with

def "ingred:seafood:bream" "A freshwater fish with soft, mild white flesh."
al ingred:seafood:bream bream
ln ingred:seafood:bream habitat:freshwater bio:habitat
ln ingred:seafood:bream dna:taste:umami calc:associated_with

def "ingred:seafood:sturgeon" "A large anadromous fish with firm flesh; the source of caviar."
al ingred:seafood:sturgeon sturgeon
ln ingred:seafood:sturgeon habitat:anadromous bio:habitat
ln ingred:seafood:sturgeon dna:taste:umami calc:associated_with

def "ingred:seafood:arctic_char" "An anadromous salmonid with rich, sweet, salmon-like flesh."
al ingred:seafood:arctic_char arctic_char
ln ingred:seafood:arctic_char habitat:anadromous bio:habitat
ln ingred:seafood:arctic_char dna:taste:umami calc:associated_with
ln ingred:seafood:arctic_char dna:taste:sweet calc:associated_with

