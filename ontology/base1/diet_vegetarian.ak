# Akasha ontology — secular vegetarian diet axis (dietary choice, not religion).
# Same computed-view approach: diet:<x> --diet:excludes--> dietflag/allergen.
# Permissible list computed by scripts/dietlaw_permits.py --view <x>. Base pack.

def "dietflag:meat" "Land-animal flesh (meat & poultry); fish/shellfish excluded."
ln ingred:meat:bacon dietflag:meat bio:dietflag
ln ingred:meat:beef dietflag:meat bio:dietflag
ln ingred:meat:bone_marrow dietflag:meat bio:dietflag
ln ingred:meat:breast_meat dietflag:meat bio:dietflag
ln ingred:meat:brisket dietflag:meat bio:dietflag
ln ingred:meat:chicken dietflag:meat bio:dietflag
ln ingred:meat:chuck dietflag:meat bio:dietflag
ln ingred:meat:duck dietflag:meat bio:dietflag
ln ingred:meat:flank dietflag:meat bio:dietflag
ln ingred:meat:ham dietflag:meat bio:dietflag
ln ingred:meat:heart dietflag:meat bio:dietflag
ln ingred:meat:lamb dietflag:meat bio:dietflag
ln ingred:meat:liver dietflag:meat bio:dietflag
ln ingred:meat:pork dietflag:meat bio:dietflag
ln ingred:meat:pork_belly dietflag:meat bio:dietflag
ln ingred:meat:pork_loin dietflag:meat bio:dietflag
ln ingred:meat:pork_shoulder dietflag:meat bio:dietflag
ln ingred:meat:poultry_wing dietflag:meat bio:dietflag
ln ingred:meat:ribeye dietflag:meat bio:dietflag
ln ingred:meat:shank dietflag:meat bio:dietflag
ln ingred:meat:sirloin dietflag:meat bio:dietflag
ln ingred:meat:tenderloin dietflag:meat bio:dietflag
ln ingred:meat:thigh_meat dietflag:meat bio:dietflag
ln ingred:meat:tripe dietflag:meat bio:dietflag
ln ingred:meat:venison dietflag:meat bio:dietflag

# ── vegetarian spectrum (secular) ──
def "diet:vegetarian" "Lacto-ovo vegetarian — no animal flesh; dairy & eggs allowed."
ln diet:vegetarian dietary_pattern thesaurus:related
ln diet:vegetarian dietflag:animal_flesh diet:excludes
def "diet:lacto_vegetarian" "Lacto-vegetarian — no flesh, no eggs; dairy allowed."
ln diet:lacto_vegetarian dietary_pattern thesaurus:related
ln diet:lacto_vegetarian dietflag:animal_flesh diet:excludes
ln diet:lacto_vegetarian allergen:egg diet:excludes
def "diet:ovo_vegetarian" "Ovo-vegetarian — no flesh, no dairy; eggs allowed."
ln diet:ovo_vegetarian dietary_pattern thesaurus:related
ln diet:ovo_vegetarian dietflag:animal_flesh diet:excludes
ln diet:ovo_vegetarian allergen:milk diet:excludes
def "diet:vegan" "Vegan — no animal products at all."
ln diet:vegan dietary_pattern thesaurus:related
ln diet:vegan dietflag:animal_flesh diet:excludes
ln diet:vegan dietflag:honey diet:excludes
ln diet:vegan allergen:egg diet:excludes
ln diet:vegan allergen:milk diet:excludes
def "diet:pescatarian" "Pescatarian — no land meat; fish & shellfish allowed."
ln diet:pescatarian dietary_pattern thesaurus:related
ln diet:pescatarian dietflag:meat diet:excludes
