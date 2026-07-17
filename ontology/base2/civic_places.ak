# Akasha ontology — public institutions, community, daily-life transport.
# Physical community places grouped by civic function, tied to the roles and
# relations that happen there. civ:* is deliberation vocabulary; place:* is the
# physical institution. Base pack.

def "place" "A public / community institution or place."
def "place_type" "Civic function of a place."
def "place_type:health" "health & medical"
ln place_type:health place_type thesaurus:related
def "place_type:education" "education & learning"
ln place_type:education place_type thesaurus:related
def "place_type:civic" "government & civic"
ln place_type:civic place_type thesaurus:related
def "place_type:recreation" "recreation & leisure"
ln place_type:recreation place_type thesaurus:related
def "place_type:safety" "public safety"
ln place_type:safety place_type thesaurus:related
def "place_type:care" "care & welfare"
ln place_type:care place_type thesaurus:related
def "place_type:transport" "transport"
ln place_type:transport place_type thesaurus:related

def "place:hospital" "Hospital — health & medical institution."
ln place:hospital place_type:health civic:function
ln doctor place:hospital civic:role_at
ln nurse place:hospital civic:role_at
ln patient place:hospital civic:role_at
def "place:clinic" "Clinic — health & medical institution."
ln place:clinic place_type:health civic:function
ln doctor place:clinic civic:role_at
ln patient place:clinic civic:role_at
def "place:pharmacy" "Pharmacy — health & medical institution."
ln place:pharmacy place_type:health civic:function
ln pharmacist place:pharmacy civic:role_at
def "place:school" "School — education & learning institution."
ln place:school place_type:education civic:function
ln teacher place:school civic:role_at
ln student place:school civic:role_at
ln classmate place:school civic:role_at
def "place:kindergarten" "Kindergarten — education & learning institution."
ln place:kindergarten place_type:education civic:function
ln teacher place:kindergarten civic:role_at
ln child place:kindergarten civic:role_at
def "place:daycare" "Daycare — care & welfare institution."
ln place:daycare place_type:care civic:function
ln caregiver place:daycare civic:role_at
ln child place:daycare civic:role_at
def "place:library" "Library — education & learning institution."
ln place:library place_type:education civic:function
ln librarian place:library civic:role_at
def "place:city_hall" "City hall — government & civic institution."
ln place:city_hall place_type:civic civic:function
ln mayor place:city_hall civic:role_at
ln clerk place:city_hall civic:role_at
ln resident place:city_hall civic:role_at
def "place:post_office" "Post office — government & civic institution."
ln place:post_office place_type:civic civic:function
ln clerk place:post_office civic:role_at
def "place:government_office" "Government office — government & civic institution."
ln place:government_office place_type:civic civic:function
ln official place:government_office civic:role_at
ln clerk place:government_office civic:role_at
def "place:police_station" "Police station — public safety institution."
ln place:police_station place_type:safety civic:function
ln officer place:police_station civic:role_at
def "place:fire_station" "Fire station — public safety institution."
ln place:fire_station place_type:safety civic:function
ln firefighter place:fire_station civic:role_at
def "place:park" "Park — recreation & leisure institution."
ln place:park place_type:recreation civic:function
ln neighbor place:park civic:role_at
ln child place:park civic:role_at
def "place:playground" "Playground — recreation & leisure institution."
ln place:playground place_type:recreation civic:function
ln child place:playground civic:role_at
def "place:community_center" "Community center — recreation & leisure institution."
ln place:community_center place_type:recreation civic:function
ln neighbor place:community_center civic:role_at
ln resident place:community_center civic:role_at
def "place:nursing_home" "Nursing home — care & welfare institution."
ln place:nursing_home place_type:care civic:function
ln caregiver place:nursing_home civic:role_at
ln nurse place:nursing_home civic:role_at
def "place:station" "Station — transport institution."
ln place:station place_type:transport civic:function
def "place:bus_stop" "Bus stop — transport institution."
ln place:bus_stop place_type:transport civic:function

# ── community / local society ──
def "concept:community" "A body of people sharing a place and social ties."
def "concept:neighborhood" "The local area around one's home and its residents."
def "concept:local_society" "地域社会 — the web of households, institutions and ties in a locality."
ln concept:neighborhood concept:community thesaurus:related
ln concept:local_society concept:community thesaurus:related
ln civ:resident concept:neighborhood social:member_of
ln social:neighbor_of concept:neighborhood thesaurus:related
ln concept:local_society place concept:includes

# ── daily-life transport ──
def "transport" "A means of daily travel."
def "transport:school_bus" "School bus — carries children to and from school."
def "transport:bicycle" "Bicycle — personal human-powered local transport."
def "transport:public_bus" "Public bus — shared local transit."
def "transport:on_foot" "Walking — travel on foot."
ln transport:school_bus transport thesaurus:related
ln transport:bicycle transport thesaurus:related
ln transport:public_bus transport thesaurus:related
ln transport:on_foot transport thesaurus:related
ln transport:school_bus place:school civic:serves
ln transport:public_bus place:bus_stop civic:serves
al transport:bicycle bicycle
al transport:school_bus school_bus
