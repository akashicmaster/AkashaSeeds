# Akasha ontology — technique defining parameters (the essence, not the name).
# Merge/split techniques by their DEFINING variables — heat / fat role /
# agitation / cover / pace / medium — so 'different name, same thing'
# (grilled sardine ≡ shioyaki, both grilling) and 'same family, different
# thing' (poêlé ≠ sauté) both fall out of the graph rather than by fiat.
# e.g. sauté = fat/thin/HIGH/TOSSED/open/quick;  poêlé = fat/BASTING/LOW/
#      STATIC/COVERED/slow — clearly not the same. Base pack.

def "technique_param:heat_level:low" "low heat"
def "technique_param:heat_level:medium" "medium heat"
def "technique_param:heat_level:high" "high heat"
def "technique_param:heat_level:very_high" "very high heat"
def "technique_param:fat_role:none" "no fat medium"
def "technique_param:fat_role:thin" "thin film of fat"
def "technique_param:fat_role:basting" "fat for basting/butter-mounting"
def "technique_param:fat_role:submerged" "submerged in fat"
def "technique_param:agitation:static" "food stays still"
def "technique_param:agitation:stirred" "stirred"
def "technique_param:agitation:tossed" "tossed/flipped constantly"
def "technique_param:cover:open" "open pan/fire"
def "technique_param:cover:covered" "covered"
def "technique_param:pace:quick" "quick / à la minute"
def "technique_param:pace:slow" "slow"
def "technique_param:medium:dry" "dry radiant heat"
def "technique_param:medium:fat" "fat"
def "technique_param:medium:water" "water"
def "technique_param:medium:steam" "steam"
def "technique_param:medium:smoke" "smoke"

ln technique:grilling technique_param:medium:dry technique:param
ln technique:grilling technique_param:heat_level:high technique:param
ln technique:grilling technique_param:agitation:static technique:param
ln technique:grilling technique_param:cover:open technique:param
ln technique:grilling technique_param:pace:quick technique:param

ln technique:sauteing technique_param:medium:fat technique:param
ln technique:sauteing technique_param:fat_role:thin technique:param
ln technique:sauteing technique_param:heat_level:high technique:param
ln technique:sauteing technique_param:agitation:tossed technique:param
ln technique:sauteing technique_param:cover:open technique:param
ln technique:sauteing technique_param:pace:quick technique:param

ln technique:poele technique_param:medium:fat technique:param
ln technique:poele technique_param:fat_role:basting technique:param
ln technique:poele technique_param:heat_level:low technique:param
ln technique:poele technique_param:agitation:static technique:param
ln technique:poele technique_param:cover:covered technique:param
ln technique:poele technique_param:pace:slow technique:param

ln technique:stir_frying technique_param:medium:fat technique:param
ln technique:stir_frying technique_param:fat_role:thin technique:param
ln technique:stir_frying technique_param:heat_level:very_high technique:param
ln technique:stir_frying technique_param:agitation:tossed technique:param
ln technique:stir_frying technique_param:cover:open technique:param
ln technique:stir_frying technique_param:pace:quick technique:param

ln technique:deep_frying technique_param:medium:fat technique:param
ln technique:deep_frying technique_param:fat_role:submerged technique:param
ln technique:deep_frying technique_param:heat_level:high technique:param
ln technique:deep_frying technique_param:agitation:static technique:param
ln technique:deep_frying technique_param:cover:open technique:param
ln technique:deep_frying technique_param:pace:quick technique:param

ln technique:confiting technique_param:medium:fat technique:param
ln technique:confiting technique_param:fat_role:submerged technique:param
ln technique:confiting technique_param:heat_level:low technique:param
ln technique:confiting technique_param:agitation:static technique:param
ln technique:confiting technique_param:cover:covered technique:param
ln technique:confiting technique_param:pace:slow technique:param

ln technique:braising technique_param:medium:water technique:param
ln technique:braising technique_param:heat_level:low technique:param
ln technique:braising technique_param:agitation:static technique:param
ln technique:braising technique_param:cover:covered technique:param
ln technique:braising technique_param:pace:slow technique:param

ln technique:roasting technique_param:medium:dry technique:param
ln technique:roasting technique_param:heat_level:medium technique:param
ln technique:roasting technique_param:agitation:static technique:param
ln technique:roasting technique_param:cover:open technique:param
ln technique:roasting technique_param:pace:slow technique:param

ln technique:steaming technique_param:medium:steam technique:param
ln technique:steaming technique_param:heat_level:medium technique:param
ln technique:steaming technique_param:agitation:static technique:param
ln technique:steaming technique_param:cover:covered technique:param

ln technique:boiling technique_param:medium:water technique:param
ln technique:boiling technique_param:heat_level:high technique:param
ln technique:boiling technique_param:agitation:static technique:param
ln technique:boiling technique_param:cover:open technique:param

