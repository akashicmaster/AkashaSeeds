# Akasha ontology — religious dietary laws (definition, computed views).
# dietflag:* group the foods a rule turns on (mostly derived from existing
# axes); dietlaw:* forbid dietflag:*/allergen:* atoms. The permissible list is
# COMPUTED (scripts/dietlaw_permits.py), not stored per food. NOTE: for halal
# & kosher, permissible-species MEAT still requires certified slaughter
# (dhabihah / shechita) — species permission is necessary, not sufficient.
# Descriptive cultural knowledge. Base pack.

def "dietflag:pork" "Pork and pork products."
ln ingred:meat:pork dietflag:pork bio:dietflag
ln ingred:meat:bacon dietflag:pork bio:dietflag
ln ingred:meat:ham dietflag:pork bio:dietflag
ln ingred:meat:pork_belly dietflag:pork bio:dietflag
ln ingred:meat:pork_loin dietflag:pork bio:dietflag
ln ingred:meat:pork_shoulder dietflag:pork bio:dietflag
ln ingred:condiment:lard dietflag:pork bio:dietflag
def "dietflag:beef" "Beef / cattle products."
ln ingred:meat:beef dietflag:beef bio:dietflag
ln ingred:meat:ribeye dietflag:beef bio:dietflag
ln ingred:meat:sirloin dietflag:beef bio:dietflag
ln ingred:meat:brisket dietflag:beef bio:dietflag
ln ingred:meat:chuck dietflag:beef bio:dietflag
ln ingred:meat:flank dietflag:beef bio:dietflag
ln ingred:meat:shank dietflag:beef bio:dietflag
ln ingred:meat:tenderloin dietflag:beef bio:dietflag
ln ingred:meat:bone_marrow dietflag:beef bio:dietflag
ln ingred:meat:tripe dietflag:beef bio:dietflag
def "dietflag:alcohol" "Alcohol / intoxicants."
ln ingred:condiment:mirin dietflag:alcohol bio:dietflag
def "dietflag:animal_flesh" "Any animal flesh (meat, poultry, fish, shellfish)."
ln ingred:meat:bacon dietflag:animal_flesh bio:dietflag
ln ingred:meat:beef dietflag:animal_flesh bio:dietflag
ln ingred:meat:bone_marrow dietflag:animal_flesh bio:dietflag
ln ingred:meat:breast_meat dietflag:animal_flesh bio:dietflag
ln ingred:meat:brisket dietflag:animal_flesh bio:dietflag
ln ingred:meat:chicken dietflag:animal_flesh bio:dietflag
ln ingred:meat:chuck dietflag:animal_flesh bio:dietflag
ln ingred:meat:duck dietflag:animal_flesh bio:dietflag
ln ingred:meat:flank dietflag:animal_flesh bio:dietflag
ln ingred:meat:ham dietflag:animal_flesh bio:dietflag
ln ingred:meat:heart dietflag:animal_flesh bio:dietflag
ln ingred:meat:lamb dietflag:animal_flesh bio:dietflag
ln ingred:meat:liver dietflag:animal_flesh bio:dietflag
ln ingred:meat:pork dietflag:animal_flesh bio:dietflag
ln ingred:meat:pork_belly dietflag:animal_flesh bio:dietflag
ln ingred:meat:pork_loin dietflag:animal_flesh bio:dietflag
ln ingred:meat:pork_shoulder dietflag:animal_flesh bio:dietflag
ln ingred:meat:poultry_wing dietflag:animal_flesh bio:dietflag
ln ingred:meat:ribeye dietflag:animal_flesh bio:dietflag
ln ingred:meat:shank dietflag:animal_flesh bio:dietflag
ln ingred:meat:sirloin dietflag:animal_flesh bio:dietflag
ln ingred:meat:tenderloin dietflag:animal_flesh bio:dietflag
ln ingred:meat:thigh_meat dietflag:animal_flesh bio:dietflag
ln ingred:meat:tripe dietflag:animal_flesh bio:dietflag
ln ingred:meat:venison dietflag:animal_flesh bio:dietflag
ln ingred:seafood:anchovy dietflag:animal_flesh bio:dietflag
ln ingred:seafood:arctic_char dietflag:animal_flesh bio:dietflag
ln ingred:seafood:barramundi dietflag:animal_flesh bio:dietflag
ln ingred:seafood:bonito dietflag:animal_flesh bio:dietflag
ln ingred:seafood:bottarga dietflag:animal_flesh bio:dietflag
ln ingred:seafood:bream dietflag:animal_flesh bio:dietflag
ln ingred:seafood:carp dietflag:animal_flesh bio:dietflag
ln ingred:seafood:catfish dietflag:animal_flesh bio:dietflag
ln ingred:seafood:caviar dietflag:animal_flesh bio:dietflag
ln ingred:seafood:chikuwa dietflag:animal_flesh bio:dietflag
ln ingred:seafood:clam dietflag:animal_flesh bio:dietflag
ln ingred:seafood:cod dietflag:animal_flesh bio:dietflag
ln ingred:seafood:crab dietflag:animal_flesh bio:dietflag
ln ingred:seafood:eel dietflag:animal_flesh bio:dietflag
ln ingred:seafood:fillet dietflag:animal_flesh bio:dietflag
ln ingred:seafood:fish_ball dietflag:animal_flesh bio:dietflag
ln ingred:seafood:fish_liver dietflag:animal_flesh bio:dietflag
ln ingred:seafood:flounder dietflag:animal_flesh bio:dietflag
ln ingred:seafood:flying_fish dietflag:animal_flesh bio:dietflag
ln ingred:seafood:grouper dietflag:animal_flesh bio:dietflag
ln ingred:seafood:haddock dietflag:animal_flesh bio:dietflag
ln ingred:seafood:hake dietflag:animal_flesh bio:dietflag
ln ingred:seafood:halibut dietflag:animal_flesh bio:dietflag
ln ingred:seafood:herring dietflag:animal_flesh bio:dietflag
ln ingred:seafood:ikura dietflag:animal_flesh bio:dietflag
ln ingred:seafood:imitation_crab dietflag:animal_flesh bio:dietflag
ln ingred:seafood:kamaboko dietflag:animal_flesh bio:dietflag
ln ingred:seafood:langoustine dietflag:animal_flesh bio:dietflag
ln ingred:seafood:lobster dietflag:animal_flesh bio:dietflag
ln ingred:seafood:mackerel dietflag:animal_flesh bio:dietflag
ln ingred:seafood:mahi_mahi dietflag:animal_flesh bio:dietflag
ln ingred:seafood:mentaiko dietflag:animal_flesh bio:dietflag
ln ingred:seafood:milt dietflag:animal_flesh bio:dietflag
ln ingred:seafood:monkfish dietflag:animal_flesh bio:dietflag
ln ingred:seafood:mullet dietflag:animal_flesh bio:dietflag
ln ingred:seafood:mussel dietflag:animal_flesh bio:dietflag
ln ingred:seafood:octopus dietflag:animal_flesh bio:dietflag
ln ingred:seafood:oyster dietflag:animal_flesh bio:dietflag
ln ingred:seafood:perch dietflag:animal_flesh bio:dietflag
ln ingred:seafood:pike dietflag:animal_flesh bio:dietflag
ln ingred:seafood:pollock dietflag:animal_flesh bio:dietflag
ln ingred:seafood:pomfret dietflag:animal_flesh bio:dietflag
ln ingred:seafood:roe dietflag:animal_flesh bio:dietflag
ln ingred:seafood:salmon dietflag:animal_flesh bio:dietflag
ln ingred:seafood:sardine dietflag:animal_flesh bio:dietflag
ln ingred:seafood:scallop dietflag:animal_flesh bio:dietflag
ln ingred:seafood:sea_bass dietflag:animal_flesh bio:dietflag
ln ingred:seafood:sea_urchin dietflag:animal_flesh bio:dietflag
ln ingred:seafood:shrimp dietflag:animal_flesh bio:dietflag
ln ingred:seafood:snapper dietflag:animal_flesh bio:dietflag
ln ingred:seafood:sole dietflag:animal_flesh bio:dietflag
ln ingred:seafood:squid dietflag:animal_flesh bio:dietflag
ln ingred:seafood:sturgeon dietflag:animal_flesh bio:dietflag
ln ingred:seafood:surimi dietflag:animal_flesh bio:dietflag
ln ingred:seafood:swordfish dietflag:animal_flesh bio:dietflag
ln ingred:seafood:tilapia dietflag:animal_flesh bio:dietflag
ln ingred:seafood:tobiko dietflag:animal_flesh bio:dietflag
ln ingred:seafood:trout dietflag:animal_flesh bio:dietflag
ln ingred:seafood:tuna dietflag:animal_flesh bio:dietflag
ln ingred:seafood:turbot dietflag:animal_flesh bio:dietflag
ln ingred:seafood:walleye dietflag:animal_flesh bio:dietflag
ln ingred:seafood:yellowtail dietflag:animal_flesh bio:dietflag
def "dietflag:five_pungent" "The five pungent roots (五葷: garlic, onion, leek, scallion, chives)."
ln ingred:veg:garlic dietflag:five_pungent bio:dietflag
ln ingred:veg:onion dietflag:five_pungent bio:dietflag
ln ingred:veg:leek dietflag:five_pungent bio:dietflag
ln ingred:veg:scallion dietflag:five_pungent bio:dietflag
ln ingred:herb:chives dietflag:five_pungent bio:dietflag
def "dietflag:honey" "Honey."
ln ingred:condiment:honey dietflag:honey bio:dietflag
def "dietflag:root_veg" "Root/bulb/tuber vegetables (uprooting harms the plant)."
ln ingred:veg:beet dietflag:root_veg bio:dietflag
ln ingred:veg:carrot dietflag:root_veg bio:dietflag
ln ingred:veg:cassava dietflag:root_veg bio:dietflag
ln ingred:veg:daikon dietflag:root_veg bio:dietflag
ln ingred:veg:fennel dietflag:root_veg bio:dietflag
ln ingred:veg:garlic dietflag:root_veg bio:dietflag
ln ingred:veg:jicama dietflag:root_veg bio:dietflag
ln ingred:veg:leek dietflag:root_veg bio:dietflag
ln ingred:veg:lotus_root dietflag:root_veg bio:dietflag
ln ingred:veg:onion dietflag:root_veg bio:dietflag
ln ingred:veg:parsnip dietflag:root_veg bio:dietflag
ln ingred:veg:potato dietflag:root_veg bio:dietflag
ln ingred:veg:radish dietflag:root_veg bio:dietflag
ln ingred:veg:scallion dietflag:root_veg bio:dietflag
ln ingred:veg:shallot dietflag:root_veg bio:dietflag
ln ingred:veg:sweet_potato dietflag:root_veg bio:dietflag
ln ingred:veg:taro dietflag:root_veg bio:dietflag
ln ingred:veg:turnip dietflag:root_veg bio:dietflag
def "dietflag:shellfish" "Shellfish (crustaceans & molluscs)."
ln ingred:seafood:clam dietflag:shellfish bio:dietflag
ln ingred:seafood:crab dietflag:shellfish bio:dietflag
ln ingred:seafood:langoustine dietflag:shellfish bio:dietflag
ln ingred:seafood:lobster dietflag:shellfish bio:dietflag
ln ingred:seafood:mussel dietflag:shellfish bio:dietflag
ln ingred:seafood:octopus dietflag:shellfish bio:dietflag
ln ingred:seafood:oyster dietflag:shellfish bio:dietflag
ln ingred:seafood:scallop dietflag:shellfish bio:dietflag
ln ingred:seafood:shrimp dietflag:shellfish bio:dietflag
ln ingred:seafood:squid dietflag:shellfish bio:dietflag
def "dietflag:non_kosher_fish" "Fish lacking fins & true scales."
ln ingred:seafood:eel dietflag:non_kosher_fish bio:dietflag
ln ingred:seafood:catfish dietflag:non_kosher_fish bio:dietflag
ln ingred:seafood:monkfish dietflag:non_kosher_fish bio:dietflag
ln ingred:seafood:sturgeon dietflag:non_kosher_fish bio:dietflag
ln ingred:seafood:swordfish dietflag:non_kosher_fish bio:dietflag

# ── dietary laws & what they forbid ──
def "dietlaw" "Religious / observance-based dietary laws."
def "dietlaw:halal" "Islamic dietary law (ハラール)."
ln dietlaw:halal dietlaw thesaurus:related
ln dietlaw:halal dietflag:pork dietlaw:forbids
ln dietlaw:halal dietflag:alcohol dietlaw:forbids
def "dietlaw:kosher" "Jewish dietary law (カシュルート)."
ln dietlaw:kosher dietlaw thesaurus:related
ln dietlaw:kosher dietflag:pork dietlaw:forbids
ln dietlaw:kosher dietflag:shellfish dietlaw:forbids
ln dietlaw:kosher dietflag:non_kosher_fish dietlaw:forbids
def "dietlaw:hindu" "Common Hindu practice — no beef."
ln dietlaw:hindu dietlaw thesaurus:related
ln dietlaw:hindu dietflag:beef dietlaw:forbids
def "dietlaw:vegetarian" "Lacto-ovo vegetarian — no animal flesh."
ln dietlaw:vegetarian dietlaw thesaurus:related
ln dietlaw:vegetarian dietflag:animal_flesh dietlaw:forbids
def "dietlaw:vegan" "Vegan — no animal products."
ln dietlaw:vegan dietlaw thesaurus:related
ln dietlaw:vegan dietflag:animal_flesh dietlaw:forbids
ln dietlaw:vegan dietflag:honey dietlaw:forbids
ln dietlaw:vegan allergen:egg dietlaw:forbids
ln dietlaw:vegan allergen:milk dietlaw:forbids
def "dietlaw:jain" "Jain — no flesh, no root vegetables, no honey."
ln dietlaw:jain dietlaw thesaurus:related
ln dietlaw:jain dietflag:animal_flesh dietlaw:forbids
ln dietlaw:jain dietflag:root_veg dietlaw:forbids
ln dietlaw:jain dietflag:honey dietlaw:forbids
ln dietlaw:jain dietflag:five_pungent dietlaw:forbids
def "dietlaw:buddhist_veg" "Buddhist vegetarian (some traditions) — no flesh, no five pungent."
ln dietlaw:buddhist_veg dietlaw thesaurus:related
ln dietlaw:buddhist_veg dietflag:animal_flesh dietlaw:forbids
ln dietlaw:buddhist_veg dietflag:five_pungent dietlaw:forbids
