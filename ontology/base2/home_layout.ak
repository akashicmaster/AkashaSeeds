# Akasha ontology — 間取り (madori): floor plan / room layout.
# Arranges the home:* rooms into a dwelling — by zone, adjacency, and which
# rooms each dwelling type contains. Built on home_spaces.ak. Base pack.

def "home:layout" "間取り — the arrangement of rooms in a dwelling."
def "home:adjacent_to" "Spatial adjacency between two rooms (symmetric)."
def "home:has_room" "A dwelling type contains this room."

def "home_zone:wet" "water-using rooms"
def "home_zone:private" "private rooms"
def "home_zone:public" "shared living rooms"
def "home_zone:service" "circulation & utility"
def "home_zone:outdoor" "outdoor spaces"

# ── room → zone ──
ln home:kitchen home_zone:wet home:zone
ln home:bathroom home_zone:wet home:zone
ln home:toilet home_zone:wet home:zone
ln home:laundry_room home_zone:wet home:zone
ln home:bedroom home_zone:private home:zone
ln home:study home_zone:private home:zone
ln home:living_room home_zone:public home:zone
ln home:dining_room home_zone:public home:zone
ln home:entrance home_zone:service home:zone
ln home:hallway home_zone:service home:zone
ln home:storeroom home_zone:service home:zone
ln home:closet home_zone:service home:zone
ln home:garage home_zone:service home:zone
ln home:garden home_zone:outdoor home:zone
ln home:yard home_zone:outdoor home:zone
ln home:driveway home_zone:outdoor home:zone
ln home:balcony home_zone:outdoor home:zone
ln home:porch home_zone:outdoor home:zone

# ── room adjacency (symmetric) ──
ln home:entrance home:hallway home:adjacent_to
ln home:hallway home:entrance home:adjacent_to
ln home:hallway home:living_room home:adjacent_to
ln home:living_room home:hallway home:adjacent_to
ln home:hallway home:bedroom home:adjacent_to
ln home:bedroom home:hallway home:adjacent_to
ln home:hallway home:study home:adjacent_to
ln home:study home:hallway home:adjacent_to
ln home:hallway home:bathroom home:adjacent_to
ln home:bathroom home:hallway home:adjacent_to
ln home:living_room home:dining_room home:adjacent_to
ln home:dining_room home:living_room home:adjacent_to
ln home:dining_room home:kitchen home:adjacent_to
ln home:kitchen home:dining_room home:adjacent_to
ln home:kitchen home:laundry_room home:adjacent_to
ln home:laundry_room home:kitchen home:adjacent_to
ln home:bathroom home:toilet home:adjacent_to
ln home:toilet home:bathroom home:adjacent_to
ln home:bathroom home:laundry_room home:adjacent_to
ln home:laundry_room home:bathroom home:adjacent_to
ln home:living_room home:balcony home:adjacent_to
ln home:balcony home:living_room home:adjacent_to
ln home:entrance home:driveway home:adjacent_to
ln home:driveway home:entrance home:adjacent_to
ln home:garage home:driveway home:adjacent_to
ln home:driveway home:garage home:adjacent_to
ln home:bedroom home:closet home:adjacent_to
ln home:closet home:bedroom home:adjacent_to

# ── dwelling types → rooms (間取りの型) ──
def "home:dwelling:studio" "1R/1K — a single room with kitchenette."
ln home:dwelling:studio home:layout thesaurus:related
ln home:dwelling:studio home:entrance home:has_room
ln home:dwelling:studio home:kitchen home:has_room
ln home:dwelling:studio home:bathroom home:has_room
ln home:dwelling:studio home:toilet home:has_room
def "home:dwelling:one_ldk" "1LDK — one bedroom plus a living-dining-kitchen."
ln home:dwelling:one_ldk home:layout thesaurus:related
ln home:dwelling:one_ldk home:entrance home:has_room
ln home:dwelling:one_ldk home:kitchen home:has_room
ln home:dwelling:one_ldk home:living_room home:has_room
ln home:dwelling:one_ldk home:dining_room home:has_room
ln home:dwelling:one_ldk home:bedroom home:has_room
ln home:dwelling:one_ldk home:bathroom home:has_room
ln home:dwelling:one_ldk home:toilet home:has_room
def "home:dwelling:two_ldk" "2LDK — two bedrooms plus LDK."
ln home:dwelling:two_ldk home:layout thesaurus:related
ln home:dwelling:two_ldk home:entrance home:has_room
ln home:dwelling:two_ldk home:kitchen home:has_room
ln home:dwelling:two_ldk home:living_room home:has_room
ln home:dwelling:two_ldk home:dining_room home:has_room
ln home:dwelling:two_ldk home:bedroom home:has_room
ln home:dwelling:two_ldk home:bathroom home:has_room
ln home:dwelling:two_ldk home:toilet home:has_room
ln home:dwelling:two_ldk home:balcony home:has_room
def "home:dwelling:apartment_unit" "A flat in an apartment building."
ln home:dwelling:apartment_unit home:layout thesaurus:related
ln home:dwelling:apartment_unit home:entrance home:has_room
ln home:dwelling:apartment_unit home:kitchen home:has_room
ln home:dwelling:apartment_unit home:living_room home:has_room
ln home:dwelling:apartment_unit home:bedroom home:has_room
ln home:dwelling:apartment_unit home:bathroom home:has_room
ln home:dwelling:apartment_unit home:toilet home:has_room
ln home:dwelling:apartment_unit home:balcony home:has_room
def "home:dwelling:detached_house" "A stand-alone house with yard."
ln home:dwelling:detached_house home:layout thesaurus:related
ln home:dwelling:detached_house home:entrance home:has_room
ln home:dwelling:detached_house home:hallway home:has_room
ln home:dwelling:detached_house home:kitchen home:has_room
ln home:dwelling:detached_house home:dining_room home:has_room
ln home:dwelling:detached_house home:living_room home:has_room
ln home:dwelling:detached_house home:bedroom home:has_room
ln home:dwelling:detached_house home:study home:has_room
ln home:dwelling:detached_house home:bathroom home:has_room
ln home:dwelling:detached_house home:toilet home:has_room
ln home:dwelling:detached_house home:storeroom home:has_room
ln home:dwelling:detached_house home:garage home:has_room
ln home:dwelling:detached_house home:garden home:has_room
