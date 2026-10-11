# Akasha ontology (world pack) — major historical events & turning points.
# Each tied to its period (hist:period:), place (geo:), and significance, with
# rich descriptions. Bridged to hist:polities, war:, foodstud:, socio:. A-tier.

def "hist:event" "A pivotal historical event or turning point (歴史的事件)."
# ── events → period, place, significance ──
def "hist:event:neolithic_revolution" "The shift from foraging to farming (~10,000 BCE) — the deepest turning point in human history, birthing surplus, property, cities and inequality."
ln hist:event:neolithic_revolution hist:event thesaurus:related
ln hist:event:neolithic_revolution hist:period:neolithic hist:occurred_in
ln hist:event:neolithic_revolution agron:agronomy thesaurus:related
ln hist:event:neolithic_revolution socio:social_stratification thesaurus:related
def "hist:event:invention_of_writing" "The birth of writing in Sumer and Egypt (~3200 BCE) — the threshold from prehistory to history, making law, literature and administration possible."
ln hist:event:invention_of_writing hist:event thesaurus:related
ln hist:event:invention_of_writing hist:period:bronze_age hist:occurred_in
ln hist:event:invention_of_writing epig:cuneiform thesaurus:related
ln hist:event:invention_of_writing ms:script thesaurus:related
def "hist:event:fall_of_western_rome" "The deposition of the last western Roman emperor in 476 CE — the traditional end of antiquity and start of the European Middle Ages."
ln hist:event:fall_of_western_rome hist:event thesaurus:related
ln hist:event:fall_of_western_rome hist:period:late_antiquity hist:occurred_in
ln hist:event:fall_of_western_rome hist:roman_empire thesaurus:related
def "hist:event:rise_of_islam" "The 7th-century emergence of Islam and the swift Arab conquests, forging a civilization from Spain to Central Asia."
ln hist:event:rise_of_islam hist:event thesaurus:related
ln hist:event:rise_of_islam hist:period:late_antiquity hist:occurred_in
ln hist:event:rise_of_islam ethnicity:arabs thesaurus:related
ln hist:event:rise_of_islam hist:polity thesaurus:related
def "hist:event:black_death" "The plague pandemic of 1347–1351 that killed a third of Europe — reshaping labour, faith and the medieval order."
ln hist:event:black_death hist:event thesaurus:related
ln hist:event:black_death hist:period:late_middle_ages hist:occurred_in
ln hist:event:black_death life:bacteria thesaurus:related
ln hist:event:black_death foodsafe:pathogen thesaurus:related
def "hist:event:fall_of_constantinople" "The Ottoman capture of Constantinople in 1453 — the end of the Byzantine Empire and, for many, of the Middle Ages."
ln hist:event:fall_of_constantinople hist:event thesaurus:related
ln hist:event:fall_of_constantinople hist:period:late_middle_ages hist:occurred_in
ln hist:event:fall_of_constantinople hist:byzantine_empire thesaurus:related
ln hist:event:fall_of_constantinople hist:ottoman_empire thesaurus:related
ln hist:event:fall_of_constantinople hist:city:constantinople thesaurus:related
def "hist:event:columbian_voyages" "Columbus's crossing of 1492 — linking the hemispheres and launching the Columbian Exchange, conquest and the modern age."
ln hist:event:columbian_voyages hist:event thesaurus:related
ln hist:event:columbian_voyages hist:period:age_of_exploration hist:occurred_in
ln hist:event:columbian_voyages foodstud:columbian_exchange thesaurus:related
ln hist:event:columbian_voyages hist:aztec_empire thesaurus:related
ln hist:event:columbian_voyages hist:inca_empire thesaurus:related
def "hist:event:protestant_reformation" "Luther's 95 Theses (1517) and the schism that shattered Latin Christendom and remade European politics."
ln hist:event:protestant_reformation hist:event thesaurus:related
ln hist:event:protestant_reformation hist:period:reformation_era hist:occurred_in
ln hist:event:protestant_reformation socio:social_movement thesaurus:related
def "hist:event:scientific_revolution_event" "From Copernicus (1543) to Newton (1687) — the overturning of the ancient cosmos and the birth of experimental science."
ln hist:event:scientific_revolution_event hist:event thesaurus:related
ln hist:event:scientific_revolution_event hist:period:scientific_revolution hist:occurred_in
ln hist:event:scientific_revolution_event research:experiment thesaurus:related
ln hist:event:scientific_revolution_event astrophys:cosmology thesaurus:related
def "hist:event:american_revolution" "The 1776 revolt of the thirteen colonies — founding a republic on Enlightenment ideals of liberty and self-government."
ln hist:event:american_revolution hist:event thesaurus:related
ln hist:event:american_revolution hist:period:enlightenment hist:occurred_in
ln hist:event:american_revolution law:concept:social_contract thesaurus:related
ln hist:event:american_revolution geo:country:USA thesaurus:related
def "hist:event:french_revolution" "The 1789 revolution that toppled the monarchy and proclaimed liberty, equality and fraternity — the template of modern political upheaval."
ln hist:event:french_revolution hist:event thesaurus:related
ln hist:event:french_revolution hist:period:enlightenment hist:occurred_in
ln hist:event:french_revolution socio:social_movement thesaurus:related
ln hist:event:french_revolution geo:country:FRA thesaurus:related
ln hist:event:french_revolution phil:justice thesaurus:related
def "hist:event:industrial_revolution_event" "The mechanization begun in 18th-century Britain — steam, factories and railways that transformed how humanity lives and works."
ln hist:event:industrial_revolution_event hist:event thesaurus:related
ln hist:event:industrial_revolution_event hist:period:industrial_revolution hist:occurred_in
ln hist:event:industrial_revolution_event econ:economic_growth thesaurus:related
ln hist:event:industrial_revolution_event mecheng:machine_design thesaurus:related
def "hist:event:napoleonic_wars" "The wars of 1803–1815 that spread revolutionary ideals and the Napoleonic Code across Europe before Waterloo."
ln hist:event:napoleonic_wars hist:event thesaurus:related
ln hist:event:napoleonic_wars hist:period:modern_era hist:occurred_in
ln hist:event:napoleonic_wars war:war thesaurus:related
ln hist:event:napoleonic_wars law:branch:constitutional_law thesaurus:related
def "hist:event:abolition_of_slavery" "The 19th-century movements and laws ending the Atlantic slave trade and slavery — a moral turning point of the modern world."
ln hist:event:abolition_of_slavery hist:event thesaurus:related
ln hist:event:abolition_of_slavery hist:period:modern_era hist:occurred_in
ln hist:event:abolition_of_slavery socio:social_movement thesaurus:related
ln hist:event:abolition_of_slavery law:law thesaurus:related
def "hist:event:meiji_restoration" "Japan's 1868 revolution that ended the shogunate and drove headlong modernization — the model of non-Western industrialization."
ln hist:event:meiji_restoration hist:event thesaurus:related
ln hist:event:meiji_restoration hist:period:modern_era hist:occurred_in
ln hist:event:meiji_restoration geo:country:JPN thesaurus:related
ln hist:event:meiji_restoration socio:modernization thesaurus:related
def "hist:event:world_war_i" "The 1914–1918 industrial war that shattered four empires and the old order, and set the 20th century's course."
ln hist:event:world_war_i hist:event thesaurus:related
ln hist:event:world_war_i hist:period:world_wars_era hist:occurred_in
ln hist:event:world_war_i war:war thesaurus:related
def "hist:event:russian_revolution" "The 1917 Bolshevik revolution that founded the world's first communist state and split the century in two."
ln hist:event:russian_revolution hist:event thesaurus:related
ln hist:event:russian_revolution hist:period:world_wars_era hist:occurred_in
ln hist:event:russian_revolution socio:conflict_theory thesaurus:related
def "hist:event:world_war_ii" "The 1939–1945 global war — the deadliest in history, ending in the Holocaust's horror, the atomic bomb and a new world order."
ln hist:event:world_war_ii hist:event thesaurus:related
ln hist:event:world_war_ii hist:period:world_wars_era hist:occurred_in
ln hist:event:world_war_ii war:war thesaurus:related
ln hist:event:world_war_ii war:conflict thesaurus:related
def "hist:event:decolonization" "The mid-20th-century dissolution of European empires as Asia and Africa won independence — remaking the political map."
ln hist:event:decolonization hist:event thesaurus:related
ln hist:event:decolonization hist:period:cold_war hist:occurred_in
ln hist:event:decolonization admin:country thesaurus:related
ln hist:event:decolonization geog:geopolitics thesaurus:related
def "hist:event:fall_of_berlin_wall" "The 1989 fall of the Wall and the 1991 collapse of the USSR — ending the Cold War and the bipolar world."
ln hist:event:fall_of_berlin_wall hist:event thesaurus:related
ln hist:event:fall_of_berlin_wall hist:period:cold_war hist:occurred_in
ln hist:event:fall_of_berlin_wall socio:social_change thesaurus:related
def "hist:event:digital_revolution" "The late-20th-century spread of computing and the internet — the information age's founding transformation."
ln hist:event:digital_revolution hist:event thesaurus:related
ln hist:event:digital_revolution hist:period:information_age hist:occurred_in
ln hist:event:digital_revolution cs:cs thesaurus:related
ln hist:event:digital_revolution dh:knowledge_graph thesaurus:related
