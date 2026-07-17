# Akasha ontology — meat flesh colour (赤身/白身肉) + aging (熟成). Base pack.
# Reuse the flesh_type white/red axis for meat, and add an aging axis with the
# methods and the meats/cuts commonly subjected to them.

# ── flesh colour (赤身/白身) ──
ln ingred:meat:beef flesh_type:red bio:flesh_type
ln ingred:meat:lamb flesh_type:red bio:flesh_type
ln ingred:meat:venison flesh_type:red bio:flesh_type
ln ingred:meat:pork flesh_type:red bio:flesh_type
ln ingred:meat:duck flesh_type:red bio:flesh_type
ln ingred:meat:ribeye flesh_type:red bio:flesh_type
ln ingred:meat:sirloin flesh_type:red bio:flesh_type
ln ingred:meat:brisket flesh_type:red bio:flesh_type
ln ingred:meat:chuck flesh_type:red bio:flesh_type
ln ingred:meat:flank flesh_type:red bio:flesh_type
ln ingred:meat:shank flesh_type:red bio:flesh_type
ln ingred:meat:tenderloin flesh_type:red bio:flesh_type
ln ingred:meat:pork_belly flesh_type:red bio:flesh_type
ln ingred:meat:pork_loin flesh_type:red bio:flesh_type
ln ingred:meat:pork_shoulder flesh_type:red bio:flesh_type
ln ingred:meat:bacon flesh_type:red bio:flesh_type
ln ingred:meat:ham flesh_type:red bio:flesh_type
ln ingred:meat:thigh_meat flesh_type:red bio:flesh_type
ln ingred:meat:heart flesh_type:red bio:flesh_type
ln ingred:meat:liver flesh_type:red bio:flesh_type
ln ingred:meat:chicken flesh_type:white bio:flesh_type
ln ingred:meat:breast_meat flesh_type:white bio:flesh_type
ln ingred:meat:poultry_wing flesh_type:white bio:flesh_type
ln ingred:meat:tripe flesh_type:white bio:flesh_type

def "aging:dry_aged" "Dry aging — open cold aging that concentrates flavour and tenderises."
def "aging:wet_aged" "Wet aging — vacuum-sealed aging in its own juices."
def "aging:hung" "Hanging / game aging (venison, wildfowl)."

# ── aging (熟成) ──
ln ingred:meat:beef aging:dry_aged culinary:aging
ln ingred:meat:ribeye aging:dry_aged culinary:aging
ln ingred:meat:sirloin aging:dry_aged culinary:aging
ln ingred:meat:tenderloin aging:dry_aged culinary:aging
ln ingred:meat:lamb aging:dry_aged culinary:aging
ln ingred:meat:beef aging:wet_aged culinary:aging
ln ingred:meat:pork aging:wet_aged culinary:aging
ln ingred:meat:brisket aging:wet_aged culinary:aging
ln ingred:meat:chuck aging:wet_aged culinary:aging
ln ingred:meat:venison aging:hung culinary:aging
ln ingred:meat:duck aging:hung culinary:aging
ln ingred:ferment:prosciutto aging:dry_aged culinary:aging
ln ingred:ferment:salami aging:dry_aged culinary:aging
