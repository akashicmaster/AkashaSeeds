# war_concepts.ak
# Military theory, types of warfare, strategic concepts, and laws of war
# Sources: Clausewitz, Sun Tzu, Jomini, Geneva Conventions — Public domain terminology
#

# ── Namespace anchors ─────────────────────────────────────────────────────────

def "war:concept" "Root namespace for military and conflict concepts."
def "war:type" "Types and forms of warfare — classificatory root."
def "war:tactic" "Battlefield tactics and formations — classificatory root."
def "war:theory" "Military theorists and strategic schools — classificatory root."
def "war:law" "Laws of war, humanitarian norms, and international legal frameworks."

# ── Types of warfare ──────────────────────────────────────────────────────────

def "war:type:total_war" "Mobilisation of entire society and economy; no distinction between combatants and civilians; WWI/WWII paradigm; theorised by Ludendorff and Clausewitz."
ln war:type:total_war war:type sys:part_of
set.add name="ontology.war_concepts" id="war:type:total_war"

def "war:type:limited_war" "Conflict with restricted objectives and means; contrast to total war; Korea, Gulf War; avoids civilian mobilisation and full economic commitment."
ln war:type:limited_war war:type sys:part_of
set.add name="ontology.war_concepts" id="war:type:limited_war"

def "war:type:guerrilla_warfare" "Irregular combatants use hit-and-run, ambush, and sabotage; avoids pitched battle; Mao, Lawrence of Arabia; Spanish origin of term (1808 Peninsular War)."
ln war:type:guerrilla_warfare war:type sys:part_of
set.add name="ontology.war_concepts" id="war:type:guerrilla_warfare"

def "war:type:attrition_warfare" "Strategy of gradually wearing down enemy resources and manpower until collapse; WWI Western Front; Verdun; costly to attacker and defender alike."
ln war:type:attrition_warfare war:type sys:part_of
set.add name="ontology.war_concepts" id="war:type:attrition_warfare"

def "war:type:maneuver_warfare" "Rapid movement to strike enemy weakness, disrupt cohesion, collapse will rather than destroy force; Auftragstaktik; blitzkrieg; Boyd's OODA loop."
ln war:type:maneuver_warfare war:type sys:part_of
set.add name="ontology.war_concepts" id="war:type:maneuver_warfare"

def "war:type:siege_warfare" "Surrounding and starving out fortified positions; trebuchet, mining, sapping; dominant from antiquity through the gunpowder era."
ln war:type:siege_warfare war:type sys:part_of
set.add name="ontology.war_concepts" id="war:type:siege_warfare"

def "war:type:naval_warfare" "Combat at sea; trireme ramming (antiquity) → line of battle (Age of Sail) → submarine and carrier warfare (20th century)."
ln war:type:naval_warfare war:type sys:part_of
set.add name="ontology.war_concepts" id="war:type:naval_warfare"

def "war:type:amphibious_warfare" "Joint sea-land assault requiring combined arms and logistical mastery; Gallipoli (1915), Normandy (1944), Inchon (1950)."
ln war:type:amphibious_warfare war:type sys:part_of
set.add name="ontology.war_concepts" id="war:type:amphibious_warfare"

def "war:type:air_power" "Strategic bombing, close air support, air superiority; Douhet's theory (1921); WWII strategic bombing campaigns; CAS doctrine in modern warfare."
ln war:type:air_power war:type sys:part_of
set.add name="ontology.war_concepts" id="war:type:air_power"

def "war:type:asymmetric_warfare" "Weaker party uses unconventional means against conventionally superior foe; IED, suicide bombing, lawfare; avoids direct confrontation."
ln war:type:asymmetric_warfare war:type sys:part_of
set.add name="ontology.war_concepts" id="war:type:asymmetric_warfare"

def "war:type:proxy_war" "Third parties fight on behalf of larger powers; Cold War pattern; Korea, Vietnam, Angola, Syria; deniability for sponsoring states."
ln war:type:proxy_war war:type sys:part_of
set.add name="ontology.war_concepts" id="war:type:proxy_war"

def "war:type:hybrid_warfare" "Simultaneous use of conventional, irregular, cyber, information, and economic means; Gerasimov doctrine; Russia-Ukraine 2014 as archetype."
ln war:type:hybrid_warfare war:type sys:part_of
set.add name="ontology.war_concepts" id="war:type:hybrid_warfare"

def "war:type:counterinsurgency" "COIN: strategies to defeat insurgency by winning population, cutting off insurgents; Galula, Petraeus FM 3-24; hearts-and-minds doctrine."
ln war:type:counterinsurgency war:type sys:part_of
set.add name="ontology.war_concepts" id="war:type:counterinsurgency"

def "war:type:economic_warfare" "Blockade, sanctions, resource denial, trade war as instruments of conflict; Continental System (Napoleon); WWII Pacific blockade of Japan."
ln war:type:economic_warfare war:type sys:part_of
set.add name="ontology.war_concepts" id="war:type:economic_warfare"

def "war:type:information_warfare" "Propaganda, deception, psychological operations, electronic warfare, cyber operations; reflexive control theory; PSYOP."
ln war:type:information_warfare war:type sys:part_of
set.add name="ontology.war_concepts" id="war:type:information_warfare"

def "war:type:cyber_warfare" "Attacks on digital infrastructure; Stuxnet (2010); offensive cyber operations against power grids, communications, and military systems."
ln war:type:cyber_warfare war:type sys:part_of
ln war:type:cyber_warfare war:type:information_warfare war:part_of
set.add name="ontology.war_concepts" id="war:type:cyber_warfare"

def "war:type:civil_war" "Armed conflict within a state between organised factions; American Civil War, Spanish Civil War, Syrian Civil War; often ideological in character."
ln war:type:civil_war war:type sys:part_of
set.add name="ontology.war_concepts" id="war:type:civil_war"

def "war:type:colonial_war" "War of conquest or suppression of colonies; pacification campaigns; counterinsurgency against independence movements; 19th-20th century."
ln war:type:colonial_war war:type sys:part_of
set.add name="ontology.war_concepts" id="war:type:colonial_war"

def "war:type:revolutionary_war" "Armed struggle to overthrow existing government or social order; French Revolution, Russian, Chinese, Cuban revolutions."
ln war:type:revolutionary_war war:type sys:part_of
set.add name="ontology.war_concepts" id="war:type:revolutionary_war"

# ── Tactical concepts ─────────────────────────────────────────────────────────

def "war:tactic:phalanx" "Greek/Macedonian heavy infantry formation; 8+ ranks of hoplites with overlapping shields and sarissas; decisive at Marathon (490 BCE) and Gaugamela (331 BCE)."
ln war:tactic:phalanx war:tactic sys:part_of
set.add name="ontology.war_concepts" id="war:tactic:phalanx"

def "war:tactic:maniple" "Roman flexible tactical subunit; manipular legion replaced phalanx; 3-line system (hastati, principes, triarii); adaptable to broken terrain."
ln war:tactic:maniple war:tactic sys:part_of
set.add name="ontology.war_concepts" id="war:tactic:maniple"

def "war:tactic:testudo" "Roman tortoise formation; interlocked shields overhead and to sides; protection against missiles during siege approach and assault."
ln war:tactic:testudo war:tactic sys:part_of
set.add name="ontology.war_concepts" id="war:tactic:testudo"

def "war:tactic:envelopment" "Double envelopment encircling enemy force; Cannae model (216 BCE); Hannibal encircled Roman army; Schlieffen Plan; Khalkhin Gol (1939)."
ln war:tactic:envelopment war:tactic sys:part_of
set.add name="ontology.war_concepts" id="war:tactic:envelopment"

def "war:tactic:defense_in_depth" "Multiple defensive lines force attacker to exhaust reserves before reaching core; elastic defence; Soviet deep battle theory; Kursk (1943)."
ln war:tactic:defense_in_depth war:tactic sys:part_of
set.add name="ontology.war_concepts" id="war:tactic:defense_in_depth"

def "war:tactic:feigned_retreat" "False withdrawal to draw enemy out of formation, then turn and attack; employed by Mongols, Parthians, and Normans at Hastings (1066)."
ln war:tactic:feigned_retreat war:tactic sys:part_of
set.add name="ontology.war_concepts" id="war:tactic:feigned_retreat"

def "war:tactic:combined_arms" "Coordinated use of infantry, cavalry/armour, artillery, and air; modern doctrine; Wehrmacht WWII; all-arms battle."
ln war:tactic:combined_arms war:tactic sys:part_of
set.add name="ontology.war_concepts" id="war:tactic:combined_arms"

def "war:tactic:blitzkrieg" "German lightning war; tank-led breakthrough, rapid exploitation, encirclement; Poland 1939, France 1940; operational rather than purely tactical concept."
ln war:tactic:blitzkrieg war:tactic sys:part_of
ln war:tactic:blitzkrieg war:tactic:combined_arms war:part_of
set.add name="ontology.war_concepts" id="war:tactic:blitzkrieg"

def "war:tactic:infiltration_tactics" "Stormtrooper tactics; small units bypass strongpoints and attack rear areas; WWI German Hutier tactics (1917); subsequently adopted widely."
ln war:tactic:infiltration_tactics war:tactic sys:part_of
set.add name="ontology.war_concepts" id="war:tactic:infiltration_tactics"

def "war:tactic:naval_line_of_battle" "Warships in line abreast exchanging broadsides; Age of Sail standard tactic; Trafalgar (1805); superseded by ironclads and torpedo weapons."
ln war:tactic:naval_line_of_battle war:tactic sys:part_of
set.add name="ontology.war_concepts" id="war:tactic:naval_line_of_battle"

def "war:tactic:siege_escalade" "Assault on fortification walls using scaling ladders, towers, or battering rams; dangerous frontal assault; alternative to starvation siege."
ln war:tactic:siege_escalade war:tactic sys:part_of
ln war:tactic:siege_escalade war:type:siege_warfare war:part_of
set.add name="ontology.war_concepts" id="war:tactic:siege_escalade"

# ── Military theorists ────────────────────────────────────────────────────────

def "war:theory:sun_tzu" "Art of War (c.500 BCE); deception, intelligence, adaptability; supreme excellence is to subdue the enemy without fighting; still taught in staff colleges worldwide."
ln war:theory:sun_tzu war:theory sys:part_of
set.add name="ontology.war_concepts" id="war:theory:sun_tzu"

def "war:theory:thucydides" "History of the Peloponnesian War; power politics; Melian Dialogue; Thucydides trap (rising vs established power); foundational text of political realism."
ln war:theory:thucydides war:theory sys:part_of
set.add name="ontology.war_concepts" id="war:theory:thucydides"

def "war:theory:vegetius" "Epitoma Rei Militaris (c.390 CE); Roman military manual; \"si vis pacem, para bellum\" (if you want peace, prepare for war); transmitted Roman doctrine to medieval Europe."
ln war:theory:vegetius war:theory sys:part_of
set.add name="ontology.war_concepts" id="war:theory:vegetius"

def "war:theory:clausewitz" "On War (Vom Kriege, 1832); war as continuation of politics by other means; fog of war; friction; centre of gravity; trinity of people, army, and government."
ln war:theory:clausewitz war:theory sys:part_of
set.add name="ontology.war_concepts" id="war:theory:clausewitz"

def "war:theory:jomini" "Summary of the Art of War (1838); geometric principles; interior lines; decisive point; dominated 19th-century American and European military thinking."
ln war:theory:jomini war:theory sys:part_of
set.add name="ontology.war_concepts" id="war:theory:jomini"

def "war:theory:mahan" "The Influence of Sea Power upon History (1890); naval supremacy as key to national power; influenced US, German, and Japanese naval expansion."
ln war:theory:mahan war:theory sys:part_of
set.add name="ontology.war_concepts" id="war:theory:mahan"

def "war:theory:douhet" "The Command of the Air (1921); strategic bombing can win wars independently by breaking civilian morale; influenced RAF Bomber Command and USAAF doctrine."
ln war:theory:douhet war:theory sys:part_of
set.add name="ontology.war_concepts" id="war:theory:douhet"

def "war:theory:mao_military" "People's War theory; three-stage guerrilla war (organisation → guerrilla → mobile/conventional); political power grows out of the barrel of a gun."
ln war:theory:mao_military war:theory sys:part_of
set.add name="ontology.war_concepts" id="war:theory:mao_military"

def "war:theory:galula" "Counterinsurgency Warfare (1964); win population's support first; population is the prize not the terrain; influenced FM 3-24; drawn from Algeria experience."
ln war:theory:galula war:theory sys:part_of
set.add name="ontology.war_concepts" id="war:theory:galula"

def "war:theory:boyd" "OODA Loop (Observe-Orient-Decide-Act); faster decision cycle defeats slower opponent; chaos theory applied to combat; derived from F-86 vs MiG-15 analysis."
ln war:theory:boyd war:theory sys:part_of
set.add name="ontology.war_concepts" id="war:theory:boyd"

# ── Laws of war ───────────────────────────────────────────────────────────────

def "war:law:ius_ad_bellum" "Law governing resort to force; just war criteria: just cause, right authority, last resort, proportionality; codified in UN Charter Articles 2(4) and 51."
ln war:law:ius_ad_bellum war:law sys:part_of
set.add name="ontology.war_concepts" id="war:law:ius_ad_bellum"

def "war:law:ius_in_bello" "Law governing conduct in war; independent of whether the war itself is just; principles: distinction, proportionality, military necessity; IHL foundation."
ln war:law:ius_in_bello war:law sys:part_of
set.add name="ontology.war_concepts" id="war:law:ius_in_bello"

def "war:law:just_war_theory" "Augustine, Aquinas, Grotius, Vitoria; criteria for a just war (ius ad bellum + ius in bello); still influential in international law and military ethics."
ln war:law:just_war_theory war:law sys:part_of
ln war:law:just_war_theory war:law:ius_ad_bellum war:part_of
ln war:law:just_war_theory war:law:ius_in_bello war:part_of
set.add name="ontology.war_concepts" id="war:law:just_war_theory"

def "war:law:geneva_conventions" "1864 (Red Cross), 1906, 1929, 1949 (four conventions); protection of wounded, POWs, and civilians; Additional Protocols 1977; backbone of IHL."
ln war:law:geneva_conventions war:law sys:part_of
ln war:law:geneva_conventions war:law:ius_in_bello war:part_of
set.add name="ontology.war_concepts" id="war:law:geneva_conventions"

def "war:law:hague_conventions" "1899 and 1907 Hague Conventions; rules on land and naval warfare, weapons prohibition; dum-dum bullets banned; Martens clause; anticipated poison gas."
ln war:law:hague_conventions war:law sys:part_of
ln war:law:hague_conventions war:law:ius_in_bello war:part_of
set.add name="ontology.war_concepts" id="war:law:hague_conventions"

def "war:law:law_of_occupation" "Rules governing military occupation of enemy territory; Hague Regulations 1907 and Geneva Convention IV 1949; occupier's duties to civilian population."
ln war:law:law_of_occupation war:law sys:part_of
set.add name="ontology.war_concepts" id="war:law:law_of_occupation"

def "war:law:war_crimes" "Violations of laws and customs of war; grave breaches of Geneva Conventions; ICC jurisdiction; Nuremberg and Tokyo tribunals established the concept in law."
ln war:law:war_crimes war:law sys:part_of
set.add name="ontology.war_concepts" id="war:law:war_crimes"

def "war:law:genocide_convention" "1948 Genocide Convention; acts with intent to destroy national, ethnic, racial, or religious group in whole or part; Cambodia, Rwanda, Srebrenica cases."
ln war:law:genocide_convention war:law sys:part_of
set.add name="ontology.war_concepts" id="war:law:genocide_convention"

def "war:law:r2p" "Responsibility to Protect (R2P); 2005 World Summit Outcome; states must protect civilians; international community may intervene if state fails; invoked in Libya 2011."
ln war:law:r2p war:law sys:part_of
set.add name="ontology.war_concepts" id="war:law:r2p"

def "war:law:scorched_earth" "Destroying resources to deny them to the enemy; Sherman's March (1864); Soviet WWII retreat; prohibited under IHL when targeting civilian necessities."
ln war:law:scorched_earth war:law sys:part_of
set.add name="ontology.war_concepts" id="war:law:scorched_earth"

def "war:law:martial_law" "Military authority replaces civilian governance in emergency; suspension of normal legal processes; habeas corpus; contested legality under IHL."
ln war:law:martial_law war:law sys:part_of
set.add name="ontology.war_concepts" id="war:law:martial_law"

# ── Cross-type relations ───────────────────────────────────────────────────────

ln war:type:counterinsurgency war:theory:galula war:influenced_by
ln war:type:maneuver_warfare war:theory:boyd war:influenced_by
ln war:type:total_war war:theory:clausewitz war:influenced_by
ln war:type:guerrilla_warfare war:theory:mao_military war:influenced_by
ln war:type:air_power war:theory:douhet war:influenced_by
ln war:type:hybrid_warfare war:type:information_warfare war:part_of
ln war:tactic:blitzkrieg war:type:maneuver_warfare war:part_of
ln war:law:ius_in_bello war:law:ius_ad_bellum war:part_of

# ── Anchor set entries ─────────────────────────────────────────────────────────

set.add name="ontology.war_concepts" id="war:concept"
set.add name="ontology.war_concepts" id="war:type"
set.add name="ontology.war_concepts" id="war:tactic"
set.add name="ontology.war_concepts" id="war:theory"
set.add name="ontology.war_concepts" id="war:law"
