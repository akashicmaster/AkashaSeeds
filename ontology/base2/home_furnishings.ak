# Akasha ontology — home furnishings: fittings, decor, info surfaces.
# Doors/screens (fixtures), freestanding furniture, soft & wall decor, and
# information surfaces (calendar/message board). Tagged by room, durability,
# and decor_type. Built on home_spaces / room_contents. Base pack.

# ── door / screen fixtures (建具) ──
def "home:door" "Door — fixture."
ln home:door home_type:fixture thesaurus:related
ln home:door home:hallway home:located_in
def "home:sliding_door" "Sliding door (襖/障子) — fixture."
ln home:sliding_door home_type:fixture thesaurus:related
ln home:sliding_door home:hallway home:located_in
def "home:skylight" "Skylight — fixture."
ln home:skylight home_type:fixture thesaurus:related
ln home:skylight home:hallway home:located_in

# ── furniture (鏡台・玄関まわり) ──
def "furniture:dressing_table" "Dressing table (鏡台)."
ln furniture:dressing_table home:bedroom home:located_in
ln furniture:dressing_table obj:durable obj_durability
def "furniture:coat_rack" "Coat rack."
ln furniture:coat_rack home:entrance home:located_in
ln furniture:coat_rack obj:durable obj_durability
def "furniture:shoe_rack" "Shoe rack (下駄箱)."
ln furniture:shoe_rack home:entrance home:located_in
ln furniture:shoe_rack obj:durable obj_durability
def "furniture:umbrella_stand" "Umbrella stand."
ln furniture:umbrella_stand home:entrance home:located_in
ln furniture:umbrella_stand obj:durable obj_durability
def "furniture:sideboard" "Sideboard."
ln furniture:sideboard home:dining_room home:located_in
ln furniture:sideboard obj:durable obj_durability
def "furniture:hat_stand" "Hat stand."
ln furniture:hat_stand home:entrance home:located_in
ln furniture:hat_stand obj:durable obj_durability

def "decor" "A decorative or informational furnishing."
def "decor_type:covering" "window covering"
def "decor_type:floor" "floor covering"
def "decor_type:wall_decor" "wall-mounted decor"
def "decor_type:ornament" "ornamental object"
def "decor_type:info" "information surface"

# ── decor & info surfaces ──
def "decor:curtain" "Curtain (カーテン)."
ln decor:curtain decor_type:covering thesaurus:related
ln decor:curtain home:living_room home:located_in
ln decor:curtain obj:durable obj_durability
def "decor:blinds" "Blinds."
ln decor:blinds decor_type:covering thesaurus:related
ln decor:blinds home:living_room home:located_in
ln decor:blinds obj:durable obj_durability
def "decor:paper_screen" "Paper screen."
ln decor:paper_screen decor_type:covering thesaurus:related
ln decor:paper_screen home:living_room home:located_in
ln decor:paper_screen obj:durable obj_durability
def "decor:rug" "Rug."
ln decor:rug decor_type:floor thesaurus:related
ln decor:rug home:living_room home:located_in
ln decor:rug obj:durable obj_durability
def "decor:carpet" "Carpet."
ln decor:carpet decor_type:floor thesaurus:related
ln decor:carpet home:living_room home:located_in
ln decor:carpet obj:durable obj_durability
def "decor:doormat" "Doormat."
ln decor:doormat decor_type:floor thesaurus:related
ln decor:doormat home:entrance home:located_in
ln decor:doormat obj:durable obj_durability
def "decor:picture_frame" "Picture frame (額縁)."
ln decor:picture_frame decor_type:wall_decor thesaurus:related
ln decor:picture_frame home:living_room home:located_in
ln decor:picture_frame obj:durable obj_durability
def "decor:painting" "Painting."
ln decor:painting decor_type:wall_decor thesaurus:related
ln decor:painting home:living_room home:located_in
ln decor:painting obj:durable obj_durability
def "decor:poster" "Poster."
ln decor:poster decor_type:wall_decor thesaurus:related
ln decor:poster home:bedroom home:located_in
ln decor:poster obj:durable obj_durability
def "decor:wall_clock" "Wall clock."
ln decor:wall_clock decor_type:wall_decor thesaurus:related
ln decor:wall_clock home:living_room home:located_in
ln decor:wall_clock obj:durable obj_durability
def "decor:tapestry" "Tapestry."
ln decor:tapestry decor_type:wall_decor thesaurus:related
ln decor:tapestry home:living_room home:located_in
ln decor:tapestry obj:durable obj_durability
def "decor:vase" "Vase (花瓶)."
ln decor:vase decor_type:ornament thesaurus:related
ln decor:vase home:living_room home:located_in
ln decor:vase obj:durable obj_durability
def "decor:ornament" "Ornament."
ln decor:ornament decor_type:ornament thesaurus:related
ln decor:ornament home:living_room home:located_in
ln decor:ornament obj:durable obj_durability
def "decor:houseplant" "Houseplant."
ln decor:houseplant decor_type:ornament thesaurus:related
ln decor:houseplant home:living_room home:located_in
ln decor:houseplant obj:durable obj_durability
def "decor:candle" "Candle."
ln decor:candle decor_type:ornament thesaurus:related
ln decor:candle home:living_room home:located_in
ln decor:candle obj:consumable obj_durability
def "decor:calendar" "Calendar (カレンダー)."
ln decor:calendar decor_type:info thesaurus:related
ln decor:calendar home:kitchen home:located_in
ln decor:calendar obj:consumable obj_durability
def "decor:message_board" "Message board (伝言板)."
ln decor:message_board decor_type:info thesaurus:related
ln decor:message_board home:kitchen home:located_in
ln decor:message_board obj:durable obj_durability
def "decor:bulletin_board" "Bulletin board."
ln decor:bulletin_board decor_type:info thesaurus:related
ln decor:bulletin_board home:entrance home:located_in
ln decor:bulletin_board obj:durable obj_durability
def "decor:whiteboard" "Whiteboard."
ln decor:whiteboard decor_type:info thesaurus:related
ln decor:whiteboard home:study home:located_in
ln decor:whiteboard obj:durable obj_durability
def "decor:memo_pad" "Memo pad."
ln decor:memo_pad decor_type:info thesaurus:related
ln decor:memo_pad home:kitchen home:located_in
ln decor:memo_pad obj:consumable obj_durability
