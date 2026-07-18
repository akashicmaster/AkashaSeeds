# Akasha ontology — home spaces (rooms, exterior) and fixtures.
# The spatial frame that household objects live in. home_type axis: room /
# exterior / fixture. Base pack.

def "home" "A dwelling and its spaces."
def "home_type:room" "interior room"
def "home_type:exterior" "outdoor space of the property"
def "home_type:fixture" "a fixed fitting of the house/plot"

def "home:kitchen" "Kitchen — room."
ln home:kitchen home_type:room thesaurus:related
def "home:bathroom" "Bathroom — room."
ln home:bathroom home_type:room thesaurus:related
def "home:toilet" "Toilet (トイレ) — room."
ln home:toilet home_type:room thesaurus:related
def "home:living_room" "Living room — room."
ln home:living_room home_type:room thesaurus:related
def "home:bedroom" "Bedroom — room."
ln home:bedroom home_type:room thesaurus:related
def "home:dining_room" "Dining room — room."
ln home:dining_room home_type:room thesaurus:related
def "home:entrance" "Entrance (玄関) — room."
ln home:entrance home_type:room thesaurus:related
def "home:hallway" "Hallway — room."
ln home:hallway home_type:room thesaurus:related
def "home:study" "Study — room."
ln home:study home_type:room thesaurus:related
def "home:closet" "Closet — room."
ln home:closet home_type:room thesaurus:related
def "home:laundry_room" "Laundry room — room."
ln home:laundry_room home_type:room thesaurus:related
def "home:storeroom" "Storeroom — room."
ln home:storeroom home_type:room thesaurus:related
def "home:garden" "Garden (庭) — exterior."
ln home:garden home_type:exterior thesaurus:related
def "home:yard" "Yard — exterior."
ln home:yard home_type:exterior thesaurus:related
def "home:garage" "Garage (ガレージ) — exterior."
ln home:garage home_type:exterior thesaurus:related
def "home:driveway" "Driveway — exterior."
ln home:driveway home_type:exterior thesaurus:related
def "home:balcony" "Balcony — exterior."
ln home:balcony home_type:exterior thesaurus:related
def "home:porch" "Porch — exterior."
ln home:porch home_type:exterior thesaurus:related
def "home:gate" "Gate (門) — fixture."
ln home:gate home_type:fixture thesaurus:related
def "home:mailbox" "Mailbox (郵便ポスト) — fixture."
ln home:mailbox home_type:fixture thesaurus:related
def "home:fence" "Fence — fixture."
ln home:fence home_type:fixture thesaurus:related
def "home:front_door" "Front door — fixture."
ln home:front_door home_type:fixture thesaurus:related
def "home:window" "Window — fixture."
ln home:window home_type:fixture thesaurus:related
def "home:doorbell" "Doorbell — fixture."
ln home:doorbell home_type:fixture thesaurus:related
def "home:faucet" "Faucet — fixture."
ln home:faucet home_type:fixture thesaurus:related
