# Akasha ontology — culinary red/white MEAT (mammal vs poultry) + white-meat
# vegetarian view. This red/white distinction (dietary) differs from flesh_type
# (flesh colour): white meat = poultry regardless of light/dark meat. Base pack.

def "dietflag:red_meat" "Red meat — mammalian (beef, pork, lamb, game) and its cuts/offal."
ln ingred:meat:bacon dietflag:red_meat bio:dietflag
ln ingred:meat:beef dietflag:red_meat bio:dietflag
ln ingred:meat:bone_marrow dietflag:red_meat bio:dietflag
ln ingred:meat:brisket dietflag:red_meat bio:dietflag
ln ingred:meat:chuck dietflag:red_meat bio:dietflag
ln ingred:meat:flank dietflag:red_meat bio:dietflag
ln ingred:meat:ham dietflag:red_meat bio:dietflag
ln ingred:meat:heart dietflag:red_meat bio:dietflag
ln ingred:meat:lamb dietflag:red_meat bio:dietflag
ln ingred:meat:liver dietflag:red_meat bio:dietflag
ln ingred:meat:pork dietflag:red_meat bio:dietflag
ln ingred:meat:pork_belly dietflag:red_meat bio:dietflag
ln ingred:meat:pork_loin dietflag:red_meat bio:dietflag
ln ingred:meat:pork_shoulder dietflag:red_meat bio:dietflag
ln ingred:meat:ribeye dietflag:red_meat bio:dietflag
ln ingred:meat:shank dietflag:red_meat bio:dietflag
ln ingred:meat:sirloin dietflag:red_meat bio:dietflag
ln ingred:meat:tenderloin dietflag:red_meat bio:dietflag
ln ingred:meat:tripe dietflag:red_meat bio:dietflag
ln ingred:meat:venison dietflag:red_meat bio:dietflag
def "dietflag:white_meat" "White meat — poultry (chicken, duck) and its cuts."
ln ingred:meat:breast_meat dietflag:white_meat bio:dietflag
ln ingred:meat:chicken dietflag:white_meat bio:dietflag
ln ingred:meat:duck dietflag:white_meat bio:dietflag
ln ingred:meat:poultry_wing dietflag:white_meat bio:dietflag
ln ingred:meat:thigh_meat dietflag:white_meat bio:dietflag
def "dietflag:seafood" "All seafood (fish & shellfish)."
ln ingred:seafood:anchovy dietflag:seafood bio:dietflag
ln ingred:seafood:arctic_char dietflag:seafood bio:dietflag
ln ingred:seafood:barramundi dietflag:seafood bio:dietflag
ln ingred:seafood:bonito dietflag:seafood bio:dietflag
ln ingred:seafood:bottarga dietflag:seafood bio:dietflag
ln ingred:seafood:bream dietflag:seafood bio:dietflag
ln ingred:seafood:carp dietflag:seafood bio:dietflag
ln ingred:seafood:catfish dietflag:seafood bio:dietflag
ln ingred:seafood:caviar dietflag:seafood bio:dietflag
ln ingred:seafood:chikuwa dietflag:seafood bio:dietflag
ln ingred:seafood:clam dietflag:seafood bio:dietflag
ln ingred:seafood:cod dietflag:seafood bio:dietflag
ln ingred:seafood:crab dietflag:seafood bio:dietflag
ln ingred:seafood:eel dietflag:seafood bio:dietflag
ln ingred:seafood:fillet dietflag:seafood bio:dietflag
ln ingred:seafood:fish_ball dietflag:seafood bio:dietflag
ln ingred:seafood:fish_liver dietflag:seafood bio:dietflag
ln ingred:seafood:flounder dietflag:seafood bio:dietflag
ln ingred:seafood:flying_fish dietflag:seafood bio:dietflag
ln ingred:seafood:grouper dietflag:seafood bio:dietflag
ln ingred:seafood:haddock dietflag:seafood bio:dietflag
ln ingred:seafood:hake dietflag:seafood bio:dietflag
ln ingred:seafood:halibut dietflag:seafood bio:dietflag
ln ingred:seafood:herring dietflag:seafood bio:dietflag
ln ingred:seafood:ikura dietflag:seafood bio:dietflag
ln ingred:seafood:imitation_crab dietflag:seafood bio:dietflag
ln ingred:seafood:kamaboko dietflag:seafood bio:dietflag
ln ingred:seafood:langoustine dietflag:seafood bio:dietflag
ln ingred:seafood:lobster dietflag:seafood bio:dietflag
ln ingred:seafood:mackerel dietflag:seafood bio:dietflag
ln ingred:seafood:mahi_mahi dietflag:seafood bio:dietflag
ln ingred:seafood:mentaiko dietflag:seafood bio:dietflag
ln ingred:seafood:milt dietflag:seafood bio:dietflag
ln ingred:seafood:monkfish dietflag:seafood bio:dietflag
ln ingred:seafood:mullet dietflag:seafood bio:dietflag
ln ingred:seafood:mussel dietflag:seafood bio:dietflag
ln ingred:seafood:octopus dietflag:seafood bio:dietflag
ln ingred:seafood:oyster dietflag:seafood bio:dietflag
ln ingred:seafood:perch dietflag:seafood bio:dietflag
ln ingred:seafood:pike dietflag:seafood bio:dietflag
ln ingred:seafood:pollock dietflag:seafood bio:dietflag
ln ingred:seafood:pomfret dietflag:seafood bio:dietflag
ln ingred:seafood:roe dietflag:seafood bio:dietflag
ln ingred:seafood:salmon dietflag:seafood bio:dietflag
ln ingred:seafood:sardine dietflag:seafood bio:dietflag
ln ingred:seafood:scallop dietflag:seafood bio:dietflag
ln ingred:seafood:sea_bass dietflag:seafood bio:dietflag
ln ingred:seafood:sea_urchin dietflag:seafood bio:dietflag
ln ingred:seafood:shrimp dietflag:seafood bio:dietflag
ln ingred:seafood:snapper dietflag:seafood bio:dietflag
ln ingred:seafood:sole dietflag:seafood bio:dietflag
ln ingred:seafood:squid dietflag:seafood bio:dietflag
ln ingred:seafood:sturgeon dietflag:seafood bio:dietflag
ln ingred:seafood:surimi dietflag:seafood bio:dietflag
ln ingred:seafood:swordfish dietflag:seafood bio:dietflag
ln ingred:seafood:tilapia dietflag:seafood bio:dietflag
ln ingred:seafood:tobiko dietflag:seafood bio:dietflag
ln ingred:seafood:trout dietflag:seafood bio:dietflag
ln ingred:seafood:tuna dietflag:seafood bio:dietflag
ln ingred:seafood:turbot dietflag:seafood bio:dietflag
ln ingred:seafood:walleye dietflag:seafood bio:dietflag
ln ingred:seafood:yellowtail dietflag:seafood bio:dietflag

def "diet:pollotarian" "White-meat vegetarian (pollotarian) — poultry allowed; no red meat, no seafood."
ln diet:pollotarian dietary_pattern thesaurus:related
ln diet:pollotarian dietflag:red_meat diet:excludes
ln diet:pollotarian dietflag:seafood diet:excludes

def "diet:pollo_pescatarian" "Pollo-pescatarian — poultry and seafood allowed; only red (mammalian) meat excluded."
ln diet:pollo_pescatarian dietary_pattern thesaurus:related
ln diet:pollo_pescatarian dietflag:red_meat diet:excludes
