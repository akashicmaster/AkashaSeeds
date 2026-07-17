# Akasha ontology — toys, craft/art, more appliances, structure.
# Adds children's toys, art & sewing supplies, communication/comfort
# appliances, and building structure — tied to hobby activities. Base pack.

# ── new space & structure ──
def "home:childrens_room" "Childrens room (子供部屋) — private room."
ln home:childrens_room home_type:room thesaurus:related
ln home:childrens_room home_zone:private home:zone

def "home_type:structure" "A structural surface of a room (ceiling/wall/floor)."
def "home:ceiling" "Ceiling (天井) — structure."
ln home:ceiling home_type:structure thesaurus:related
def "home:wall" "Wall — structure."
ln home:wall home_type:structure thesaurus:related
def "home:floor" "Floor — structure."
ln home:floor home_type:structure thesaurus:related

# ── hobby & domestic activities ──
def "activity:art" "絵を描く — drawing & painting."
ln activity:art home concept:related
def "activity:sewing" "裁縫 — sewing & needlework."
ln activity:sewing home concept:related
def "activity:play" "子供の遊び — children's play."
ln activity:play home concept:related
def "activity:exercise" "運動 — exercise & fitness."
ln activity:exercise home concept:related

# ── appliances (電話・ドアホン・ミシン・加湿/除湿) ──
def "appliance:telephone" "Telephone (電話)."
ln appliance:telephone appliance thesaurus:related
ln appliance:telephone home:hallway home:located_in
ln appliance:telephone obj:durable obj_durability
def "appliance:doorphone" "Doorphone (ドアホン)."
ln appliance:doorphone appliance thesaurus:related
ln appliance:doorphone home:entrance home:located_in
ln appliance:doorphone obj:durable obj_durability
def "appliance:sewing_machine" "Sewing machine (ミシン)."
ln appliance:sewing_machine appliance thesaurus:related
ln appliance:sewing_machine home:study home:located_in
ln appliance:sewing_machine obj:durable obj_durability
ln appliance:sewing_machine activity:sewing home:used_for
def "appliance:humidifier" "Humidifier (加湿器)."
ln appliance:humidifier appliance thesaurus:related
ln appliance:humidifier home:living_room home:located_in
ln appliance:humidifier obj:durable obj_durability
def "appliance:dehumidifier" "Dehumidifier (除湿機)."
ln appliance:dehumidifier appliance thesaurus:related
ln appliance:dehumidifier home:living_room home:located_in
ln appliance:dehumidifier obj:durable obj_durability
def "appliance:air_purifier" "Air purifier."
ln appliance:air_purifier appliance thesaurus:related
ln appliance:air_purifier home:living_room home:located_in
ln appliance:air_purifier obj:durable obj_durability
ln appliance:doorphone home:doorbell thesaurus:related

def "toy" "A children's plaything."
def "toy_type:building" "construction toys"
def "toy_type:pretend" "role-play toys"
def "toy_type:plush" "soft toys"
def "toy_type:game" "games & puzzles"
def "toy_type:active" "active/outdoor toys"
def "toy_type:creative" "creative toys"
# ── toys (おもちゃ) → play ──
def "toy:building_blocks" "Building blocks."
ln toy:building_blocks toy_type:building thesaurus:related
ln toy:building_blocks home:childrens_room home:located_in
ln toy:building_blocks activity:play home:used_for
ln toy:building_blocks obj:durable obj_durability
def "toy:toy_bricks" "Toy bricks."
ln toy:toy_bricks toy_type:building thesaurus:related
ln toy:toy_bricks home:childrens_room home:located_in
ln toy:toy_bricks activity:play home:used_for
ln toy:toy_bricks obj:durable obj_durability
def "toy:doll" "Doll."
ln toy:doll toy_type:pretend thesaurus:related
ln toy:doll home:childrens_room home:located_in
ln toy:doll activity:play home:used_for
ln toy:doll obj:durable obj_durability
def "toy:toy_car" "Toy car."
ln toy:toy_car toy_type:pretend thesaurus:related
ln toy:toy_car home:childrens_room home:located_in
ln toy:toy_car activity:play home:used_for
ln toy:toy_car obj:durable obj_durability
def "toy:toy_kitchen" "Toy kitchen."
ln toy:toy_kitchen toy_type:pretend thesaurus:related
ln toy:toy_kitchen home:childrens_room home:located_in
ln toy:toy_kitchen activity:play home:used_for
ln toy:toy_kitchen obj:durable obj_durability
def "toy:stuffed_animal" "Stuffed animal."
ln toy:stuffed_animal toy_type:plush thesaurus:related
ln toy:stuffed_animal home:childrens_room home:located_in
ln toy:stuffed_animal activity:play home:used_for
ln toy:stuffed_animal obj:durable obj_durability
def "toy:teddy_bear" "Teddy bear."
ln toy:teddy_bear toy_type:plush thesaurus:related
ln toy:teddy_bear home:childrens_room home:located_in
ln toy:teddy_bear activity:play home:used_for
ln toy:teddy_bear obj:durable obj_durability
def "toy:puzzle" "Puzzle."
ln toy:puzzle toy_type:game thesaurus:related
ln toy:puzzle home:childrens_room home:located_in
ln toy:puzzle activity:play home:used_for
ln toy:puzzle obj:durable obj_durability
def "toy:board_game" "Board game."
ln toy:board_game toy_type:game thesaurus:related
ln toy:board_game home:childrens_room home:located_in
ln toy:board_game activity:play home:used_for
ln toy:board_game obj:durable obj_durability
def "toy:ball" "Ball."
ln toy:ball toy_type:active thesaurus:related
ln toy:ball home:childrens_room home:located_in
ln toy:ball activity:play home:used_for
ln toy:ball obj:durable obj_durability
def "toy:tricycle" "Tricycle."
ln toy:tricycle toy_type:active thesaurus:related
ln toy:tricycle home:childrens_room home:located_in
ln toy:tricycle activity:play home:used_for
ln toy:tricycle obj:durable obj_durability
def "toy:building_set" "Building set."
ln toy:building_set toy_type:building thesaurus:related
ln toy:building_set home:childrens_room home:located_in
ln toy:building_set activity:play home:used_for
ln toy:building_set obj:durable obj_durability
def "toy:action_figure" "Action figure."
ln toy:action_figure toy_type:pretend thesaurus:related
ln toy:action_figure home:childrens_room home:located_in
ln toy:action_figure activity:play home:used_for
ln toy:action_figure obj:durable obj_durability
def "toy:train_set" "Train set."
ln toy:train_set toy_type:pretend thesaurus:related
ln toy:train_set home:childrens_room home:located_in
ln toy:train_set activity:play home:used_for
ln toy:train_set obj:durable obj_durability
def "toy:rattle" "Rattle."
ln toy:rattle toy_type:plush thesaurus:related
ln toy:rattle home:childrens_room home:located_in
ln toy:rattle activity:play home:used_for
ln toy:rattle obj:durable obj_durability
def "toy:toy_blocks_creative" "Toy blocks creative."
ln toy:toy_blocks_creative toy_type:creative thesaurus:related
ln toy:toy_blocks_creative home:childrens_room home:located_in
ln toy:toy_blocks_creative activity:play home:used_for
ln toy:toy_blocks_creative obj:durable obj_durability

def "craft" "An art or handicraft supply."
# ── craft & art (画材・裁縫) ──
def "craft:crayon" "Crayon (クレヨン)."
ln craft:crayon craft thesaurus:related
ln craft:crayon activity:art home:used_for
ln craft:crayon home:study home:located_in
ln craft:crayon obj:consumable obj_durability
def "craft:paint" "Paint."
ln craft:paint craft thesaurus:related
ln craft:paint activity:art home:used_for
ln craft:paint home:study home:located_in
ln craft:paint obj:consumable obj_durability
def "craft:canvas" "Canvas."
ln craft:canvas craft thesaurus:related
ln craft:canvas activity:art home:used_for
ln craft:canvas home:study home:located_in
ln craft:canvas obj:durable obj_durability
def "craft:paintbrush" "Paintbrush."
ln craft:paintbrush craft thesaurus:related
ln craft:paintbrush activity:art home:used_for
ln craft:paintbrush home:study home:located_in
ln craft:paintbrush obj:durable obj_durability
def "craft:sketchbook" "Sketchbook."
ln craft:sketchbook craft thesaurus:related
ln craft:sketchbook activity:art home:used_for
ln craft:sketchbook home:study home:located_in
ln craft:sketchbook obj:consumable obj_durability
def "craft:palette" "Palette."
ln craft:palette craft thesaurus:related
ln craft:palette activity:art home:used_for
ln craft:palette home:study home:located_in
ln craft:palette obj:durable obj_durability
def "craft:sewing_box" "Sewing box (裁縫箱)."
ln craft:sewing_box craft thesaurus:related
ln craft:sewing_box activity:sewing home:used_for
ln craft:sewing_box home:study home:located_in
ln craft:sewing_box obj:durable obj_durability
def "craft:needle" "Needle."
ln craft:needle craft thesaurus:related
ln craft:needle activity:sewing home:used_for
ln craft:needle home:study home:located_in
ln craft:needle obj:durable obj_durability
def "craft:thread" "Thread."
ln craft:thread craft thesaurus:related
ln craft:thread activity:sewing home:used_for
ln craft:thread home:study home:located_in
ln craft:thread obj:consumable obj_durability
def "craft:yarn" "Yarn."
ln craft:yarn craft thesaurus:related
ln craft:yarn activity:sewing home:used_for
ln craft:yarn home:study home:located_in
ln craft:yarn obj:consumable obj_durability
def "craft:fabric" "Fabric."
ln craft:fabric craft thesaurus:related
ln craft:fabric activity:sewing home:used_for
ln craft:fabric home:study home:located_in
ln craft:fabric obj:consumable obj_durability
def "craft:knitting_needles" "Knitting needles."
ln craft:knitting_needles craft thesaurus:related
ln craft:knitting_needles activity:sewing home:used_for
ln craft:knitting_needles home:study home:located_in
ln craft:knitting_needles obj:durable obj_durability
def "craft:pins" "Pins."
ln craft:pins craft thesaurus:related
ln craft:pins activity:sewing home:used_for
ln craft:pins home:study home:located_in
ln craft:pins obj:consumable obj_durability

# ── misc household items ──
def "furniture:step_stool" "Step stool (踏み台)."
ln furniture:step_stool home:kitchen home:located_in
ln furniture:step_stool obj:durable obj_durability
def "tool:clothes_hanger" "Clothes hanger (ハンガー)."
ln tool:clothes_hanger home:closet home:located_in
ln tool:clothes_hanger obj:durable obj_durability
def "tool:yoga_mat" "Yoga mat (ヨガマット)."
ln tool:yoga_mat home:living_room home:located_in
ln tool:yoga_mat obj:durable obj_durability
ln tool:yoga_mat activity:exercise home:used_for
