# Akasha ontology — room contents: appliances (家電), toiletries, fixtures.
# The tools and machines inside each room. Tagged by location (home:located_in)
# and durability; appliances link to the activity/verb they serve. Base pack.

def "appliance" "A household electrical appliance (家電)."
# ── appliances (家電) ──
def "appliance:refrigerator" "Refrigerator."
ln appliance:refrigerator appliance thesaurus:related
ln appliance:refrigerator home:kitchen home:located_in
ln appliance:refrigerator obj:durable obj_durability
def "appliance:washing_machine" "Washing machine."
ln appliance:washing_machine appliance thesaurus:related
ln appliance:washing_machine home:laundry_room home:located_in
ln appliance:washing_machine obj:durable obj_durability
ln appliance:washing_machine verb:act:wash home:used_for
def "appliance:microwave" "Microwave."
ln appliance:microwave appliance thesaurus:related
ln appliance:microwave home:kitchen home:located_in
ln appliance:microwave obj:durable obj_durability
def "appliance:oven" "Oven."
ln appliance:oven appliance thesaurus:related
ln appliance:oven home:kitchen home:located_in
ln appliance:oven obj:durable obj_durability
def "appliance:stove" "Stove."
ln appliance:stove appliance thesaurus:related
ln appliance:stove home:kitchen home:located_in
ln appliance:stove obj:durable obj_durability
def "appliance:range_hood" "Range hood."
ln appliance:range_hood appliance thesaurus:related
ln appliance:range_hood home:kitchen home:located_in
ln appliance:range_hood obj:durable obj_durability
def "appliance:rice_cooker" "Rice cooker."
ln appliance:rice_cooker appliance thesaurus:related
ln appliance:rice_cooker home:kitchen home:located_in
ln appliance:rice_cooker obj:durable obj_durability
def "appliance:toaster" "Toaster."
ln appliance:toaster appliance thesaurus:related
ln appliance:toaster home:kitchen home:located_in
ln appliance:toaster obj:durable obj_durability
def "appliance:electric_kettle" "Electric kettle."
ln appliance:electric_kettle appliance thesaurus:related
ln appliance:electric_kettle home:kitchen home:located_in
ln appliance:electric_kettle obj:durable obj_durability
def "appliance:dishwasher" "Dishwasher."
ln appliance:dishwasher appliance thesaurus:related
ln appliance:dishwasher home:kitchen home:located_in
ln appliance:dishwasher obj:durable obj_durability
ln appliance:dishwasher verb:act:wash home:used_for
def "appliance:television" "Television."
ln appliance:television appliance thesaurus:related
ln appliance:television home:living_room home:located_in
ln appliance:television obj:durable obj_durability
ln appliance:television verb:act:watch home:used_for
def "appliance:air_conditioner" "Air conditioner."
ln appliance:air_conditioner appliance thesaurus:related
ln appliance:air_conditioner home:living_room home:located_in
ln appliance:air_conditioner obj:durable obj_durability
def "appliance:vacuum_cleaner" "Vacuum cleaner."
ln appliance:vacuum_cleaner appliance thesaurus:related
ln appliance:vacuum_cleaner home:storeroom home:located_in
ln appliance:vacuum_cleaner obj:durable obj_durability
ln appliance:vacuum_cleaner activity:cleaning home:used_for
def "appliance:clothes_dryer" "Clothes dryer."
ln appliance:clothes_dryer appliance thesaurus:related
ln appliance:clothes_dryer home:laundry_room home:located_in
ln appliance:clothes_dryer obj:durable obj_durability
def "appliance:water_heater" "Water heater."
ln appliance:water_heater appliance thesaurus:related
ln appliance:water_heater home:bathroom home:located_in
ln appliance:water_heater obj:durable obj_durability
def "appliance:electric_fan" "Electric fan."
ln appliance:electric_fan appliance thesaurus:related
ln appliance:electric_fan home:living_room home:located_in
ln appliance:electric_fan obj:durable obj_durability
def "appliance:heater" "Heater."
ln appliance:heater appliance thesaurus:related
ln appliance:heater home:living_room home:located_in
ln appliance:heater obj:durable obj_durability
def "appliance:hairdryer" "Hairdryer."
ln appliance:hairdryer appliance thesaurus:related
ln appliance:hairdryer home:bathroom home:located_in
ln appliance:hairdryer obj:durable obj_durability
def "appliance:iron" "Iron."
ln appliance:iron appliance thesaurus:related
ln appliance:iron home:laundry_room home:located_in
ln appliance:iron obj:durable obj_durability
def "appliance:ceiling_light" "Ceiling light."
ln appliance:ceiling_light appliance thesaurus:related
ln appliance:ceiling_light home:living_room home:located_in
ln appliance:ceiling_light obj:durable obj_durability

# ── toiletries (洗面・浴室の道具) ──
def "toiletry:toothbrush" "Toothbrush."
ln toiletry:toothbrush home:bathroom home:located_in
ln toiletry:toothbrush obj:durable obj_durability
def "toiletry:toothpaste" "Toothpaste."
ln toiletry:toothpaste home:bathroom home:located_in
ln toiletry:toothpaste obj:consumable obj_durability
ln toiletry:toothpaste concept:daily_necessities civic:supplies
def "toiletry:mirror" "Mirror."
ln toiletry:mirror home:bathroom home:located_in
ln toiletry:mirror obj:durable obj_durability
def "toiletry:comb" "Comb."
ln toiletry:comb home:bathroom home:located_in
ln toiletry:comb obj:durable obj_durability
def "toiletry:razor" "Razor."
ln toiletry:razor home:bathroom home:located_in
ln toiletry:razor obj:durable obj_durability
def "toiletry:shampoo" "Shampoo."
ln toiletry:shampoo home:bathroom home:located_in
ln toiletry:shampoo obj:consumable obj_durability
ln toiletry:shampoo concept:daily_necessities civic:supplies
def "toiletry:conditioner" "Conditioner."
ln toiletry:conditioner home:bathroom home:located_in
ln toiletry:conditioner obj:consumable obj_durability
ln toiletry:conditioner concept:daily_necessities civic:supplies
def "toiletry:floss" "Floss."
ln toiletry:floss home:bathroom home:located_in
ln toiletry:floss obj:consumable obj_durability
ln toiletry:floss concept:daily_necessities civic:supplies
def "toiletry:hairbrush" "Hairbrush."
ln toiletry:hairbrush home:bathroom home:located_in
ln toiletry:hairbrush obj:durable obj_durability
def "toiletry:tooth_cup" "Tooth cup."
ln toiletry:tooth_cup home:bathroom home:located_in
ln toiletry:tooth_cup obj:durable obj_durability
def "toiletry:cotton_swab" "Cotton swab."
ln toiletry:cotton_swab home:bathroom home:located_in
ln toiletry:cotton_swab obj:consumable obj_durability
ln toiletry:cotton_swab concept:daily_necessities civic:supplies

# ── room fixtures (什器・水回り) ──
def "home:bathtub" "Bathtub — fixture."
ln home:bathtub home_type:fixture thesaurus:related
ln home:bathtub home:bathroom home:located_in
def "home:shower" "Shower — fixture."
ln home:shower home_type:fixture thesaurus:related
ln home:shower home:bathroom home:located_in
def "home:washbasin" "Washbasin — fixture."
ln home:washbasin home_type:fixture thesaurus:related
ln home:washbasin home:bathroom home:located_in
def "home:toilet_bowl" "Toilet bowl — fixture."
ln home:toilet_bowl home_type:fixture thesaurus:related
ln home:toilet_bowl home:toilet home:located_in
def "home:kitchen_sink" "Kitchen sink — fixture."
ln home:kitchen_sink home_type:fixture thesaurus:related
ln home:kitchen_sink home:kitchen home:located_in
def "home:countertop" "Countertop — fixture."
ln home:countertop home_type:fixture thesaurus:related
ln home:countertop home:kitchen home:located_in
def "home:cupboard" "Cupboard — fixture."
ln home:cupboard home_type:fixture thesaurus:related
ln home:cupboard home:kitchen home:located_in
def "home:wardrobe_closet" "Wardrobe closet — fixture."
ln home:wardrobe_closet home_type:fixture thesaurus:related
ln home:wardrobe_closet home:bedroom home:located_in
