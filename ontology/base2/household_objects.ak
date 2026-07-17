# Akasha ontology — household objects: furniture, stationery, supplies, tools.
# Each tagged by location (home:*), durability (consumable/durable) and, for
# tools, the activity it serves. Consumables feed concept:daily_necessities.
# DIY/yard activities and the home center (ホームセンター) tie it together. Base pack.

def "obj_durability" "Whether an object is used up (consumable) or lasts (durable)."
def "obj:consumable" "consumable good."
ln obj:consumable obj_durability thesaurus:related
def "obj:durable" "durable good."
ln obj:durable obj_durability thesaurus:related

# ── furniture (durable) ──
def "furniture:sofa" "Sofa."
ln furniture:sofa home:living_room home:located_in
ln furniture:sofa obj:durable obj_durability
def "furniture:couch" "Couch."
ln furniture:couch home:living_room home:located_in
ln furniture:couch obj:durable obj_durability
def "furniture:bed" "Bed."
ln furniture:bed home:bedroom home:located_in
ln furniture:bed obj:durable obj_durability
def "furniture:dining_table" "Dining table."
ln furniture:dining_table home:dining_room home:located_in
ln furniture:dining_table obj:durable obj_durability
def "furniture:chair" "Chair."
ln furniture:chair home:dining_room home:located_in
ln furniture:chair obj:durable obj_durability
def "furniture:desk" "Desk."
ln furniture:desk home:study home:located_in
ln furniture:desk obj:durable obj_durability
def "furniture:bookshelf" "Bookshelf."
ln furniture:bookshelf home:study home:located_in
ln furniture:bookshelf obj:durable obj_durability
def "furniture:wardrobe" "Wardrobe."
ln furniture:wardrobe home:bedroom home:located_in
ln furniture:wardrobe obj:durable obj_durability
def "furniture:cabinet" "Cabinet."
ln furniture:cabinet home:kitchen home:located_in
ln furniture:cabinet obj:durable obj_durability
def "furniture:chest_of_drawers" "Chest of drawers."
ln furniture:chest_of_drawers home:bedroom home:located_in
ln furniture:chest_of_drawers obj:durable obj_durability
def "furniture:dresser" "Dresser."
ln furniture:dresser home:bedroom home:located_in
ln furniture:dresser obj:durable obj_durability
def "furniture:coffee_table" "Coffee table."
ln furniture:coffee_table home:living_room home:located_in
ln furniture:coffee_table obj:durable obj_durability

# ── stationery (文房具) ──
def "stationery:pen" "Pen."
ln stationery:pen home:study home:located_in
ln stationery:pen obj:durable obj_durability
def "stationery:pencil" "Pencil."
ln stationery:pencil home:study home:located_in
ln stationery:pencil obj:durable obj_durability
def "stationery:notebook" "Notebook."
ln stationery:notebook home:study home:located_in
ln stationery:notebook obj:durable obj_durability
def "stationery:paper" "Paper."
ln stationery:paper home:study home:located_in
ln stationery:paper obj:durable obj_durability
def "stationery:eraser" "Eraser."
ln stationery:eraser home:study home:located_in
ln stationery:eraser obj:durable obj_durability
def "stationery:scissors" "Scissors."
ln stationery:scissors home:study home:located_in
ln stationery:scissors obj:durable obj_durability
def "stationery:stapler" "Stapler."
ln stationery:stapler home:study home:located_in
ln stationery:stapler obj:durable obj_durability
def "stationery:tape" "Tape."
ln stationery:tape home:study home:located_in
ln stationery:tape obj:durable obj_durability
def "stationery:glue" "Glue."
ln stationery:glue home:study home:located_in
ln stationery:glue obj:durable obj_durability
def "stationery:ruler" "Ruler."
ln stationery:ruler home:study home:located_in
ln stationery:ruler obj:durable obj_durability
def "stationery:marker" "Marker."
ln stationery:marker home:study home:located_in
ln stationery:marker obj:durable obj_durability
def "stationery:envelope" "Envelope."
ln stationery:envelope home:study home:located_in
ln stationery:envelope obj:durable obj_durability
def "stationery:clip" "Clip."
ln stationery:clip home:study home:located_in
ln stationery:clip obj:durable obj_durability

# ── supplies / consumables (備品・消耗品) → daily necessities ──
def "supply:toilet_paper" "Toilet paper (トイレットペーパー)."
ln supply:toilet_paper home:toilet home:located_in
ln supply:toilet_paper obj:consumable obj_durability
ln supply:toilet_paper concept:daily_necessities civic:supplies
def "supply:towel" "Towel (タオル)."
ln supply:towel home:bathroom home:located_in
ln supply:towel obj:consumable obj_durability
ln supply:towel concept:daily_necessities civic:supplies
def "supply:dishcloth" "Dishcloth (布巾)."
ln supply:dishcloth home:kitchen home:located_in
ln supply:dishcloth obj:consumable obj_durability
ln supply:dishcloth concept:daily_necessities civic:supplies
def "supply:cleaning_rag" "Cleaning rag (雑巾)."
ln supply:cleaning_rag home:storeroom home:located_in
ln supply:cleaning_rag obj:consumable obj_durability
ln supply:cleaning_rag concept:daily_necessities civic:supplies
def "supply:tissue" "Tissue."
ln supply:tissue home:living_room home:located_in
ln supply:tissue obj:consumable obj_durability
ln supply:tissue concept:daily_necessities civic:supplies
def "supply:paper_towel" "Paper towel."
ln supply:paper_towel home:kitchen home:located_in
ln supply:paper_towel obj:consumable obj_durability
ln supply:paper_towel concept:daily_necessities civic:supplies
def "supply:soap" "Soap."
ln supply:soap home:bathroom home:located_in
ln supply:soap obj:consumable obj_durability
ln supply:soap concept:daily_necessities civic:supplies
def "supply:detergent" "Detergent."
ln supply:detergent home:laundry_room home:located_in
ln supply:detergent obj:consumable obj_durability
ln supply:detergent concept:daily_necessities civic:supplies
def "supply:dish_soap" "Dish soap."
ln supply:dish_soap home:kitchen home:located_in
ln supply:dish_soap obj:consumable obj_durability
ln supply:dish_soap concept:daily_necessities civic:supplies
def "supply:sponge" "Sponge."
ln supply:sponge home:kitchen home:located_in
ln supply:sponge obj:consumable obj_durability
ln supply:sponge concept:daily_necessities civic:supplies
def "supply:trash_bag" "Trash bag."
ln supply:trash_bag home:kitchen home:located_in
ln supply:trash_bag obj:consumable obj_durability
ln supply:trash_bag concept:daily_necessities civic:supplies
def "supply:light_bulb" "Light bulb."
ln supply:light_bulb home:storeroom home:located_in
ln supply:light_bulb obj:consumable obj_durability
ln supply:light_bulb concept:daily_necessities civic:supplies
def "supply:battery" "Battery."
ln supply:battery home:storeroom home:located_in
ln supply:battery obj:consumable obj_durability
ln supply:battery concept:daily_necessities civic:supplies

# ── tools & yard equipment → activity ──
def "tool:lawn_mower" "Lawn mower."
ln tool:lawn_mower home:garden home:located_in
ln tool:lawn_mower obj:durable obj_durability
ln tool:lawn_mower activity:lawn_mowing home:used_for
def "tool:garden_hose" "Garden hose."
ln tool:garden_hose home:garden home:located_in
ln tool:garden_hose obj:durable obj_durability
ln tool:garden_hose activity:gardening home:used_for
def "tool:rake" "Rake."
ln tool:rake home:garden home:located_in
ln tool:rake obj:durable obj_durability
ln tool:rake activity:gardening home:used_for
def "tool:shovel" "Shovel."
ln tool:shovel home:garden home:located_in
ln tool:shovel obj:durable obj_durability
ln tool:shovel activity:gardening home:used_for
def "tool:watering_can" "Watering can."
ln tool:watering_can home:garden home:located_in
ln tool:watering_can obj:durable obj_durability
ln tool:watering_can activity:gardening home:used_for
def "tool:broom" "Broom."
ln tool:broom home:storeroom home:located_in
ln tool:broom obj:durable obj_durability
ln tool:broom activity:cleaning home:used_for
def "tool:bucket" "Bucket."
ln tool:bucket home:storeroom home:located_in
ln tool:bucket obj:durable obj_durability
ln tool:bucket activity:cleaning home:used_for
def "tool:mop" "Mop."
ln tool:mop home:storeroom home:located_in
ln tool:mop obj:durable obj_durability
ln tool:mop activity:cleaning home:used_for
def "tool:ladder" "Ladder."
ln tool:ladder home:garage home:located_in
ln tool:ladder obj:durable obj_durability
ln tool:ladder activity:diy home:used_for
def "tool:toolbox" "Toolbox."
ln tool:toolbox home:garage home:located_in
ln tool:toolbox obj:durable obj_durability
ln tool:toolbox activity:diy home:used_for
def "tool:hammer" "Hammer."
ln tool:hammer home:garage home:located_in
ln tool:hammer obj:durable obj_durability
ln tool:hammer activity:diy home:used_for
def "tool:screwdriver" "Screwdriver."
ln tool:screwdriver home:garage home:located_in
ln tool:screwdriver obj:durable obj_durability
ln tool:screwdriver activity:diy home:used_for
def "tool:drill" "Drill."
ln tool:drill home:garage home:located_in
ln tool:drill obj:durable obj_durability
ln tool:drill activity:diy home:used_for
def "tool:wrench" "Wrench."
ln tool:wrench home:garage home:located_in
ln tool:wrench obj:durable obj_durability
ln tool:wrench activity:diy home:used_for
def "tool:car_wash_sponge" "Car wash sponge."
ln tool:car_wash_sponge home:garage home:located_in
ln tool:car_wash_sponge obj:durable obj_durability
ln tool:car_wash_sponge activity:car_washing home:used_for

# ── domestic & DIY activities ──
def "activity:diy" "日曜大工 — do-it-yourself home carpentry and repair."
ln activity:diy home concept:related
def "activity:car_washing" "洗車 — washing the car."
ln activity:car_washing home concept:related
def "activity:gardening" "庭仕事 — tending the garden."
ln activity:gardening home concept:related
def "activity:lawn_mowing" "芝刈り — mowing the lawn."
ln activity:lawn_mowing home concept:related
def "activity:cleaning" "Household cleaning."
ln activity:cleaning home concept:related

# ── home center (ホームセンター) ──
def "place:home_center" "Home center (ホームセンター) — DIY, garden and household goods store."
def "place:hardware_store" "Hardware store — tools, fixings and building supplies."
ln place:home_center place_type:commerce civic:function
ln place:hardware_store place_type:commerce civic:function
ln place:home_center activity:diy civic:supplies
ln place:home_center activity:gardening civic:supplies
ln place:home_center concept:daily_necessities civic:supplies
