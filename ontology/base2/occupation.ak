# Akasha ontology — occupations (職業) and work rank (地位).
# Most adults work: an occupation taxonomy by sector, mapped to workplace
# (place:*), to the person:field:* it belongs to, and bridged to the social
# role relations. Plus a work-rank ladder (地位). Base pack.

def "occupation" "A trade or profession."
def "occupation_sector:healthcare" "health & medicine"
def "occupation_sector:education" "teaching"
def "occupation_sector:tech_engineering" "engineering & IT"
def "occupation_sector:business_finance" "business & finance"
def "occupation_sector:legal" "law"
def "occupation_sector:public_civil" "government & public service"
def "occupation_sector:safety_emergency" "safety & emergency"
def "occupation_sector:trades_construction" "skilled trades & building"
def "occupation_sector:agriculture" "farming & primary"
def "occupation_sector:food_service" "food & drink service"
def "occupation_sector:retail_service" "retail & personal service"
def "occupation_sector:transport" "transport"
def "occupation_sector:arts_media" "arts & media"
def "occupation_sector:science_research" "science & research"
def "occupation_sector:religion_other" "religion & other"

# ── occupations → sector / workplace / field / social-role bridge ──
def "occupation:doctor" "Doctor."
ln occupation:doctor occupation_sector:healthcare occupation:sector
ln occupation:doctor doctor thesaurus:related
ln occupation:doctor place:hospital occupation:works_at
ln occupation:doctor person:field:medicine occupation:field
def "occupation:nurse" "Nurse."
ln occupation:nurse occupation_sector:healthcare occupation:sector
ln occupation:nurse nurse thesaurus:related
ln occupation:nurse place:hospital occupation:works_at
ln occupation:nurse person:field:medicine occupation:field
def "occupation:surgeon" "Surgeon."
ln occupation:surgeon occupation_sector:healthcare occupation:sector
ln occupation:surgeon surgeon thesaurus:related
ln occupation:surgeon place:hospital occupation:works_at
ln occupation:surgeon person:field:medicine occupation:field
def "occupation:dentist" "Dentist."
ln occupation:dentist occupation_sector:healthcare occupation:sector
ln occupation:dentist dentist thesaurus:related
ln occupation:dentist place:clinic occupation:works_at
ln occupation:dentist person:field:medicine occupation:field
def "occupation:pharmacist" "Pharmacist."
ln occupation:pharmacist occupation_sector:healthcare occupation:sector
ln occupation:pharmacist pharmacist thesaurus:related
ln occupation:pharmacist place:pharmacy occupation:works_at
ln occupation:pharmacist person:field:medicine occupation:field
def "occupation:veterinarian" "Veterinarian."
ln occupation:veterinarian occupation_sector:healthcare occupation:sector
ln occupation:veterinarian veterinarian thesaurus:related
ln occupation:veterinarian place:clinic occupation:works_at
ln occupation:veterinarian person:field:medicine occupation:field
def "occupation:therapist" "Therapist."
ln occupation:therapist occupation_sector:healthcare occupation:sector
ln occupation:therapist therapist thesaurus:related
ln occupation:therapist person:field:medicine occupation:field
def "occupation:caregiver" "Caregiver."
ln occupation:caregiver occupation_sector:healthcare occupation:sector
ln occupation:caregiver caregiver thesaurus:related
ln occupation:caregiver place:nursing_home occupation:works_at
def "occupation:teacher" "Teacher."
ln occupation:teacher occupation_sector:education occupation:sector
ln occupation:teacher teacher thesaurus:related
ln occupation:teacher place:school occupation:works_at
def "occupation:professor" "Professor."
ln occupation:professor occupation_sector:education occupation:sector
ln occupation:professor professor thesaurus:related
ln occupation:professor place:school occupation:works_at
def "occupation:principal" "Principal."
ln occupation:principal occupation_sector:education occupation:sector
ln occupation:principal principal thesaurus:related
ln occupation:principal place:school occupation:works_at
def "occupation:tutor" "Tutor."
ln occupation:tutor occupation_sector:education occupation:sector
ln occupation:tutor tutor thesaurus:related
def "occupation:librarian" "Librarian."
ln occupation:librarian occupation_sector:education occupation:sector
ln occupation:librarian librarian thesaurus:related
ln occupation:librarian place:library occupation:works_at
def "occupation:engineer" "Engineer."
ln occupation:engineer occupation_sector:tech_engineering occupation:sector
ln occupation:engineer engineer thesaurus:related
ln occupation:engineer person:field:engineering_invention occupation:field
def "occupation:programmer" "Programmer."
ln occupation:programmer occupation_sector:tech_engineering occupation:sector
ln occupation:programmer programmer thesaurus:related
ln occupation:programmer person:field:engineering_invention occupation:field
def "occupation:architect" "Architect."
ln occupation:architect occupation_sector:tech_engineering occupation:sector
ln occupation:architect architect thesaurus:related
ln occupation:architect person:field:architecture occupation:field
def "occupation:technician" "Technician."
ln occupation:technician occupation_sector:tech_engineering occupation:sector
ln occupation:technician technician thesaurus:related
ln occupation:technician place:repair_shop occupation:works_at
def "occupation:manager" "Manager."
ln occupation:manager occupation_sector:business_finance occupation:sector
ln occupation:manager manager thesaurus:related
def "occupation:accountant" "Accountant."
ln occupation:accountant occupation_sector:business_finance occupation:sector
ln occupation:accountant accountant thesaurus:related
ln occupation:accountant person:field:economics occupation:field
def "occupation:banker" "Banker."
ln occupation:banker occupation_sector:business_finance occupation:sector
ln occupation:banker banker thesaurus:related
ln occupation:banker place:bank occupation:works_at
ln occupation:banker person:field:economics occupation:field
def "occupation:teller" "Teller."
ln occupation:teller occupation_sector:business_finance occupation:sector
ln occupation:teller teller thesaurus:related
ln occupation:teller place:bank occupation:works_at
def "occupation:salesperson" "Salesperson."
ln occupation:salesperson occupation_sector:business_finance occupation:sector
ln occupation:salesperson salesperson thesaurus:related
def "occupation:clerk" "Clerk."
ln occupation:clerk occupation_sector:business_finance occupation:sector
ln occupation:clerk clerk thesaurus:related
ln occupation:clerk place:government_office occupation:works_at
def "occupation:secretary" "Secretary."
ln occupation:secretary occupation_sector:business_finance occupation:sector
ln occupation:secretary secretary thesaurus:related
def "occupation:entrepreneur" "Entrepreneur."
ln occupation:entrepreneur occupation_sector:business_finance occupation:sector
ln occupation:entrepreneur entrepreneur thesaurus:related
def "occupation:consultant" "Consultant."
ln occupation:consultant occupation_sector:business_finance occupation:sector
ln occupation:consultant consultant thesaurus:related
def "occupation:lawyer" "Lawyer."
ln occupation:lawyer occupation_sector:legal occupation:sector
ln occupation:lawyer lawyer thesaurus:related
ln occupation:lawyer person:field:law occupation:field
def "occupation:judge" "Judge."
ln occupation:judge occupation_sector:legal occupation:sector
ln occupation:judge judge thesaurus:related
ln occupation:judge person:field:law occupation:field
def "occupation:notary" "Notary."
ln occupation:notary occupation_sector:legal occupation:sector
ln occupation:notary notary thesaurus:related
ln occupation:notary person:field:law occupation:field
def "occupation:mayor" "Mayor."
ln occupation:mayor occupation_sector:public_civil occupation:sector
ln occupation:mayor mayor thesaurus:related
ln occupation:mayor place:city_hall occupation:works_at
ln occupation:mayor person:field:politics_statecraft occupation:field
def "occupation:official" "Official."
ln occupation:official occupation_sector:public_civil occupation:sector
ln occupation:official official thesaurus:related
ln occupation:official place:government_office occupation:works_at
ln occupation:official person:field:politics_statecraft occupation:field
def "occupation:diplomat" "Diplomat."
ln occupation:diplomat occupation_sector:public_civil occupation:sector
ln occupation:diplomat diplomat thesaurus:related
ln occupation:diplomat person:field:politics_statecraft occupation:field
def "occupation:civil_servant" "Civil servant."
ln occupation:civil_servant occupation_sector:public_civil occupation:sector
ln occupation:civil_servant civil_servant thesaurus:related
ln occupation:civil_servant place:city_hall occupation:works_at
def "occupation:politician" "Politician."
ln occupation:politician occupation_sector:public_civil occupation:sector
ln occupation:politician politician thesaurus:related
ln occupation:politician person:field:politics_statecraft occupation:field
def "occupation:police_officer" "Police officer."
ln occupation:police_officer occupation_sector:safety_emergency occupation:sector
ln occupation:police_officer police_officer thesaurus:related
ln occupation:police_officer place:police_station occupation:works_at
def "occupation:firefighter" "Firefighter."
ln occupation:firefighter occupation_sector:safety_emergency occupation:sector
ln occupation:firefighter firefighter thesaurus:related
ln occupation:firefighter place:fire_station occupation:works_at
def "occupation:soldier" "Soldier."
ln occupation:soldier occupation_sector:safety_emergency occupation:sector
ln occupation:soldier soldier thesaurus:related
ln occupation:soldier person:field:military occupation:field
def "occupation:security_guard" "Security guard."
ln occupation:security_guard occupation_sector:safety_emergency occupation:sector
ln occupation:security_guard security_guard thesaurus:related
def "occupation:carpenter" "Carpenter."
ln occupation:carpenter occupation_sector:trades_construction occupation:sector
ln occupation:carpenter carpenter thesaurus:related
def "occupation:plumber" "Plumber."
ln occupation:plumber occupation_sector:trades_construction occupation:sector
ln occupation:plumber plumber thesaurus:related
def "occupation:electrician" "Electrician."
ln occupation:electrician occupation_sector:trades_construction occupation:sector
ln occupation:electrician electrician thesaurus:related
def "occupation:welder" "Welder."
ln occupation:welder occupation_sector:trades_construction occupation:sector
ln occupation:welder welder thesaurus:related
def "occupation:mason" "Mason."
ln occupation:mason occupation_sector:trades_construction occupation:sector
ln occupation:mason mason thesaurus:related
def "occupation:mechanic" "Mechanic."
ln occupation:mechanic occupation_sector:trades_construction occupation:sector
ln occupation:mechanic mechanic thesaurus:related
ln occupation:mechanic place:repair_shop occupation:works_at
def "occupation:construction_worker" "Construction worker."
ln occupation:construction_worker occupation_sector:trades_construction occupation:sector
ln occupation:construction_worker construction_worker thesaurus:related
def "occupation:farmer" "Farmer."
ln occupation:farmer occupation_sector:agriculture occupation:sector
ln occupation:farmer farmer thesaurus:related
def "occupation:fisherman" "Fisherman."
ln occupation:fisherman occupation_sector:agriculture occupation:sector
ln occupation:fisherman fisherman thesaurus:related
def "occupation:rancher" "Rancher."
ln occupation:rancher occupation_sector:agriculture occupation:sector
ln occupation:rancher rancher thesaurus:related
def "occupation:gardener" "Gardener."
ln occupation:gardener occupation_sector:agriculture occupation:sector
ln occupation:gardener gardener thesaurus:related
ln occupation:gardener place:park occupation:works_at
def "occupation:chef" "Chef."
ln occupation:chef occupation_sector:food_service occupation:sector
ln occupation:chef chef thesaurus:related
ln occupation:chef place:restaurant occupation:works_at
def "occupation:cook" "Cook."
ln occupation:cook occupation_sector:food_service occupation:sector
ln occupation:cook cook thesaurus:related
ln occupation:cook place:diner occupation:works_at
def "occupation:waiter" "Waiter."
ln occupation:waiter occupation_sector:food_service occupation:sector
ln occupation:waiter waiter thesaurus:related
ln occupation:waiter place:restaurant occupation:works_at
def "occupation:baker" "Baker."
ln occupation:baker occupation_sector:food_service occupation:sector
ln occupation:baker baker thesaurus:related
ln occupation:baker place:bakery occupation:works_at
def "occupation:butcher" "Butcher."
ln occupation:butcher occupation_sector:food_service occupation:sector
ln occupation:butcher butcher thesaurus:related
ln occupation:butcher place:butcher_shop occupation:works_at
def "occupation:barista" "Barista."
ln occupation:barista occupation_sector:food_service occupation:sector
ln occupation:barista barista thesaurus:related
ln occupation:barista place:cafe occupation:works_at
def "occupation:bartender" "Bartender."
ln occupation:bartender occupation_sector:food_service occupation:sector
ln occupation:bartender bartender thesaurus:related
ln occupation:bartender place:bar occupation:works_at
def "occupation:cashier" "Cashier."
ln occupation:cashier occupation_sector:retail_service occupation:sector
ln occupation:cashier cashier thesaurus:related
ln occupation:cashier place:supermarket occupation:works_at
def "occupation:shopkeeper" "Shopkeeper."
ln occupation:shopkeeper occupation_sector:retail_service occupation:sector
ln occupation:shopkeeper shopkeeper thesaurus:related
ln occupation:shopkeeper place:general_store occupation:works_at
def "occupation:hairdresser" "Hairdresser."
ln occupation:hairdresser occupation_sector:retail_service occupation:sector
ln occupation:hairdresser hairdresser thesaurus:related
ln occupation:hairdresser place:hair_salon occupation:works_at
def "occupation:barber" "Barber."
ln occupation:barber occupation_sector:retail_service occupation:sector
ln occupation:barber barber thesaurus:related
ln occupation:barber place:barber occupation:works_at
def "occupation:tailor" "Tailor."
ln occupation:tailor occupation_sector:retail_service occupation:sector
ln occupation:tailor tailor thesaurus:related
def "occupation:cleaner" "Cleaner."
ln occupation:cleaner occupation_sector:retail_service occupation:sector
ln occupation:cleaner cleaner thesaurus:related
ln occupation:cleaner place:dry_cleaner occupation:works_at
def "occupation:driver" "Driver."
ln occupation:driver occupation_sector:transport occupation:sector
ln occupation:driver driver thesaurus:related
def "occupation:pilot" "Pilot."
ln occupation:pilot occupation_sector:transport occupation:sector
ln occupation:pilot pilot thesaurus:related
def "occupation:sailor" "Sailor."
ln occupation:sailor occupation_sector:transport occupation:sector
ln occupation:sailor sailor thesaurus:related
ln occupation:sailor person:field:exploration_navigation occupation:field
def "occupation:conductor" "Conductor."
ln occupation:conductor occupation_sector:transport occupation:sector
ln occupation:conductor conductor thesaurus:related
ln occupation:conductor place:station occupation:works_at
def "occupation:artist" "Artist."
ln occupation:artist occupation_sector:arts_media occupation:sector
ln occupation:artist artist thesaurus:related
ln occupation:artist person:field:visual_arts occupation:field
def "occupation:writer" "Writer."
ln occupation:writer occupation_sector:arts_media occupation:sector
ln occupation:writer writer thesaurus:related
ln occupation:writer person:field:literature occupation:field
def "occupation:journalist" "Journalist."
ln occupation:journalist occupation_sector:arts_media occupation:sector
ln occupation:journalist journalist thesaurus:related
ln occupation:journalist person:field:literature occupation:field
def "occupation:musician" "Musician."
ln occupation:musician occupation_sector:arts_media occupation:sector
ln occupation:musician musician thesaurus:related
ln occupation:musician person:field:music occupation:field
def "occupation:actor" "Actor."
ln occupation:actor occupation_sector:arts_media occupation:sector
ln occupation:actor actor thesaurus:related
ln occupation:actor person:field:theater_performing_arts occupation:field
def "occupation:designer" "Designer."
ln occupation:designer occupation_sector:arts_media occupation:sector
ln occupation:designer designer thesaurus:related
ln occupation:designer person:field:visual_arts occupation:field
def "occupation:photographer" "Photographer."
ln occupation:photographer occupation_sector:arts_media occupation:sector
ln occupation:photographer photographer thesaurus:related
ln occupation:photographer person:field:visual_arts occupation:field
def "occupation:scientist" "Scientist."
ln occupation:scientist occupation_sector:science_research occupation:sector
ln occupation:scientist scientist thesaurus:related
ln occupation:scientist person:field:science occupation:field
def "occupation:researcher" "Researcher."
ln occupation:researcher occupation_sector:science_research occupation:sector
ln occupation:researcher researcher thesaurus:related
ln occupation:researcher person:field:science occupation:field
def "occupation:mathematician" "Mathematician."
ln occupation:mathematician occupation_sector:science_research occupation:sector
ln occupation:mathematician mathematician thesaurus:related
ln occupation:mathematician person:field:mathematics occupation:field
def "occupation:priest" "Priest."
ln occupation:priest occupation_sector:religion_other occupation:sector
ln occupation:priest priest thesaurus:related
ln occupation:priest person:field:religion occupation:field
def "occupation:athlete" "Athlete."
ln occupation:athlete occupation_sector:religion_other occupation:sector
ln occupation:athlete athlete thesaurus:related
def "occupation:model" "Model."
ln occupation:model occupation_sector:religion_other occupation:sector
ln occupation:model model thesaurus:related

def "status" "地位 — position or standing, esp. rank at work."
def "status:outranks" "Holds a higher position than."
# ── work-rank ladder (高→低) ──
def "status:owner" "Owner — work rank."
ln status:owner status thesaurus:related
ln status:owner status:executive status:outranks
def "status:executive" "Executive — work rank."
ln status:executive status thesaurus:related
ln status:executive status:director status:outranks
def "status:director" "Director — work rank."
ln status:director status thesaurus:related
ln status:director status:manager status:outranks
def "status:manager" "Manager — work rank."
ln status:manager status thesaurus:related
ln status:manager status:supervisor status:outranks
def "status:supervisor" "Supervisor — work rank."
ln status:supervisor status thesaurus:related
ln status:supervisor status:senior_staff status:outranks
def "status:senior_staff" "Senior staff — work rank."
ln status:senior_staff status thesaurus:related
ln status:senior_staff status:staff status:outranks
def "status:staff" "Staff — work rank."
ln status:staff status thesaurus:related
ln status:staff status:trainee status:outranks
def "status:trainee" "Trainee — work rank."
ln status:trainee status thesaurus:related
# rank ties into the social hierarchy relations
ln status:outranks social:boss_of thesaurus:related
ln status:outranks social:senior_of thesaurus:related
ln occupation status thesaurus:related
