# Akasha ontology — community events and participatory groups.
# Events (holidays/festivals/markets) and groups (scouts/sports/civic) where a
# community gathers — tied to concept:community, the place, and season where
# fixed. group: is community groups (org:* is management theory). Base pack.

def "event_type:holiday" "a calendar holiday"
def "event_type:festival" "a communal celebration"
def "event_type:market_event" "a communal buying/selling event"

def "event:christmas" "A midwinter gift-giving holiday."
ln event:christmas event_type:holiday thesaurus:related
ln event:christmas concept:community thesaurus:related
ln event:christmas season:winter in_season
def "event:new_year" "The turn of the year."
ln event:new_year event_type:holiday thesaurus:related
ln event:new_year concept:community thesaurus:related
ln event:new_year season:winter in_season
def "event:halloween" "Autumn costume-and-sweets holiday."
ln event:halloween event_type:holiday thesaurus:related
ln event:halloween concept:community thesaurus:related
ln event:halloween concept:neighborhood civic:held_at
ln event:halloween season:autumn in_season
def "event:easter" "Spring holiday."
ln event:easter event_type:holiday thesaurus:related
ln event:easter concept:community thesaurus:related
ln event:easter season:spring in_season
def "event:local_festival" "お祭り/matsuri — a locality's own seasonal festival, rooted in place."
ln event:local_festival event_type:festival thesaurus:related
ln event:local_festival concept:community thesaurus:related
ln event:local_festival concept:neighborhood civic:held_at
def "event:fair" "A community fair with stalls, rides and produce."
ln event:fair event_type:festival thesaurus:related
ln event:fair concept:community thesaurus:related
ln event:fair place:park civic:held_at
def "event:carnival_event" "A street carnival / parade."
ln event:carnival_event event_type:festival thesaurus:related
ln event:carnival_event concept:community thesaurus:related
ln event:carnival_event concept:neighborhood civic:held_at
def "event:bazaar" "A charity/community sale of donated goods."
ln event:bazaar event_type:market_event thesaurus:related
ln event:bazaar concept:community thesaurus:related
ln event:bazaar place:community_center civic:held_at
ln event:bazaar place:school civic:held_at
def "event:flea_market" "A market of second-hand and handmade goods."
ln event:flea_market event_type:market_event thesaurus:related
ln event:flea_market concept:community thesaurus:related
ln event:flea_market place:park civic:held_at
ln event:flea_market place:community_center civic:held_at

# ── participatory community groups ──
def "group_type:youth" "youth organisation"
def "group_type:sports" "amateur/community sport"
def "group_type:civic" "neighbourhood civic group"
def "group_type:hobby" "hobby/interest group"

def "group:scouts" "Scouting movement for youth — outdoors, service, badges."
ln group:scouts group_type:youth thesaurus:related
ln group:scouts concept:community thesaurus:related
ln group:scouts social:member_of thesaurus:related
ln group:scouts place:community_center civic:held_at
def "group:boy_scouts" "Boy Scouts."
ln group:boy_scouts group_type:youth thesaurus:related
ln group:boy_scouts concept:community thesaurus:related
ln group:boy_scouts social:member_of thesaurus:related
def "group:girl_scouts" "Girl Scouts."
ln group:girl_scouts group_type:youth thesaurus:related
ln group:girl_scouts concept:community thesaurus:related
ln group:girl_scouts social:member_of thesaurus:related
def "group:sports_club" "A local club for amateur sport open to all."
ln group:sports_club group_type:sports thesaurus:related
ln group:sports_club concept:community thesaurus:related
ln group:sports_club social:member_of thesaurus:related
ln group:sports_club place:park civic:held_at
def "group:little_league" "Youth community baseball/soccer league."
ln group:little_league group_type:sports thesaurus:related
ln group:little_league concept:community thesaurus:related
ln group:little_league social:member_of thesaurus:related
ln group:little_league place:park civic:held_at
def "group:community_sports" "みんなが参加する — participatory amateur sport for all ages."
ln group:community_sports group_type:sports thesaurus:related
ln group:community_sports concept:community thesaurus:related
ln group:community_sports social:member_of thesaurus:related
ln group:community_sports place:park civic:held_at
ln group:community_sports place:school civic:held_at
def "group:neighborhood_association" "町内会/自治会 — residents' association running local affairs."
ln group:neighborhood_association group_type:civic thesaurus:related
ln group:neighborhood_association concept:community thesaurus:related
ln group:neighborhood_association social:member_of thesaurus:related
ln group:neighborhood_association place:community_center civic:held_at
def "group:pta" "Parent-Teacher Association."
ln group:pta group_type:civic thesaurus:related
ln group:pta concept:community thesaurus:related
ln group:pta social:member_of thesaurus:related
ln group:pta place:school civic:held_at
ln group:boy_scouts group:scouts thesaurus:related
ln group:girl_scouts group:scouts thesaurus:related
