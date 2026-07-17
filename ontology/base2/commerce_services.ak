# Akasha ontology — commerce, food service, and daily services.
# Retail/food/service institutions extend place:* with new civic functions,
# plus service:* for mobile/delivery services (post, courier, taxi). Base pack.

def "place_type:commerce" "retail & shops"
ln place_type:commerce place_type thesaurus:related
def "place_type:food_service" "eating & drinking out"
ln place_type:food_service place_type thesaurus:related
def "place_type:service" "personal & household services"
ln place_type:service place_type thesaurus:related

def "place:supermarket" "Supermarket — commerce place."
ln place:supermarket place_type:commerce civic:function
ln cashier place:supermarket civic:role_at
ln shopper place:supermarket civic:role_at
def "place:drugstore" "Drugstore — commerce place."
ln place:drugstore place_type:commerce civic:function
ln pharmacist place:drugstore civic:role_at
ln cashier place:drugstore civic:role_at
def "place:grocery" "Grocery — commerce place."
ln place:grocery place_type:commerce civic:function
ln grocer place:grocery civic:role_at
def "place:general_store" "General store — commerce place."
ln place:general_store place_type:commerce civic:function
ln shopkeeper place:general_store civic:role_at
def "place:convenience_store" "Convenience store — commerce place."
ln place:convenience_store place_type:commerce civic:function
ln cashier place:convenience_store civic:role_at
def "place:bakery" "Bakery — commerce place."
ln place:bakery place_type:commerce civic:function
ln baker place:bakery civic:role_at
def "place:butcher_shop" "Butcher shop — commerce place."
ln place:butcher_shop place_type:commerce civic:function
ln butcher place:butcher_shop civic:role_at
def "place:greengrocer" "Greengrocer — commerce place."
ln place:greengrocer place_type:commerce civic:function
ln grocer place:greengrocer civic:role_at
def "place:market" "Market — commerce place."
ln place:market place_type:commerce civic:function
ln vendor place:market civic:role_at
def "place:restaurant" "Restaurant — food service place."
ln place:restaurant place_type:food_service civic:function
ln chef place:restaurant civic:role_at
ln waiter place:restaurant civic:role_at
ln diner_guest place:restaurant civic:role_at
def "place:diner" "Diner — food service place."
ln place:diner place_type:food_service civic:function
ln cook place:diner civic:role_at
ln waiter place:diner civic:role_at
def "place:pub" "Pub — food service place."
ln place:pub place_type:food_service civic:function
ln bartender place:pub civic:role_at
ln patron place:pub civic:role_at
def "place:cafe" "Cafe — food service place."
ln place:cafe place_type:food_service civic:function
ln barista place:cafe civic:role_at
def "place:bar" "Bar — food service place."
ln place:bar place_type:food_service civic:function
ln bartender place:bar civic:role_at
def "place:dry_cleaner" "Dry cleaner — service place."
ln place:dry_cleaner place_type:service civic:function
ln cleaner place:dry_cleaner civic:role_at
def "place:laundromat" "Laundromat — service place."
ln place:laundromat place_type:service civic:function
def "place:barber" "Barber — service place."
ln place:barber place_type:service civic:function
ln barber place:barber civic:role_at
def "place:hair_salon" "Hair salon — service place."
ln place:hair_salon place_type:service civic:function
ln hairdresser place:hair_salon civic:role_at
def "place:bank" "Bank — service place."
ln place:bank place_type:service civic:function
ln teller place:bank civic:role_at
def "place:repair_shop" "Repair shop — service place."
ln place:repair_shop place_type:service civic:function
ln mechanic place:repair_shop civic:role_at

# ── daily necessities (生活必需品) ──
def "concept:daily_necessities" "生活必需品 — everyday commodities a household needs (food, toiletries, cleaning goods)."
ln place:supermarket concept:daily_necessities civic:supplies
ln place:drugstore concept:daily_necessities civic:supplies
ln place:general_store concept:daily_necessities civic:supplies
ln place:convenience_store concept:daily_necessities civic:supplies

# ── delivery & mobile services ──
def "service" "A delivery or mobile service that comes to the household."
def "service:mail_delivery" "郵便配達 — postal delivery of letters and parcels."
def "service:courier" "運送/宅配 — parcel courier and freight delivery."
def "service:taxi" "Taxi — on-demand personal transport."
def "service:home_delivery" "Home delivery of goods (groceries, meals)."
ln service:mail_delivery service thesaurus:related
ln service:courier service thesaurus:related
ln service:taxi service thesaurus:related
ln service:home_delivery service thesaurus:related
ln service:mail_delivery place:post_office civic:operated_by
ln service:taxi transport thesaurus:related
ln mail_carrier service:mail_delivery civic:role_at
ln courier service:courier civic:role_at
ln taxi_driver service:taxi civic:role_at
