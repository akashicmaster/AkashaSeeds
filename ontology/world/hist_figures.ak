# Akasha ontology (world pack) — historical figures, made first-class.
# person: held only era/field classification axes; add actual people, tied to
# their era (person:era:), field (person:field:), period (hist:period:), polity/
# country, and their words (quote:) where present. A-tier.

def "person:figure" "A notable historical person (歴史上の人物)."
def "person:hammurabi" "Babylon's king (r.~1792 BCE) whose law code is history's most famous."
ln person:hammurabi person:figure thesaurus:related
ln person:hammurabi person:era:ancient person:lived_in
ln person:hammurabi person:field:law person:worked_in
ln person:hammurabi hist:period:bronze_age person:active_in
ln person:hammurabi hist:babylonia thesaurus:related
ln person:hammurabi law:code:hammurabi thesaurus:related
def "person:cyrus_the_great" "Founder of the Achaemenid Persian empire, remembered for tolerance."
ln person:cyrus_the_great person:figure thesaurus:related
ln person:cyrus_the_great person:era:ancient person:lived_in
ln person:cyrus_the_great person:field:politics_statecraft person:worked_in
ln person:cyrus_the_great hist:period:classical_antiquity person:active_in
ln person:cyrus_the_great hist:achaemenid_persia thesaurus:related
ln person:cyrus_the_great ethnicity:persians thesaurus:related
def "person:confucius" "China's great teacher of ethics, ritual and good government."
ln person:confucius person:figure thesaurus:related
ln person:confucius person:era:ancient person:lived_in
ln person:confucius person:field:philosophy person:worked_in
ln person:confucius hist:period:iron_age person:active_in
ln person:confucius hist:han_china thesaurus:related
ln person:confucius quote:confucius_slowly thesaurus:related
def "person:buddha" "Siddhartha Gautama, whose awakening founded Buddhism."
ln person:buddha person:figure thesaurus:related
ln person:buddha person:era:ancient person:lived_in
ln person:buddha person:field:religion person:worked_in
ln person:buddha hist:period:iron_age person:active_in
ln person:buddha ethnicity:indo_aryans thesaurus:related
ln person:buddha quote:dhammapada_thought thesaurus:related
def "person:socrates" "The Athenian philosopher who questioned everything and drank the hemlock."
ln person:socrates person:figure thesaurus:related
ln person:socrates person:era:ancient person:lived_in
ln person:socrates person:field:philosophy person:worked_in
ln person:socrates hist:period:classical_antiquity person:active_in
ln person:socrates hist:ancient_greece thesaurus:related
ln person:socrates quote:socrates_examined thesaurus:related
def "person:alexander_the_great" "The Macedonian king who conquered from Greece to India by age 32."
ln person:alexander_the_great person:figure thesaurus:related
ln person:alexander_the_great person:era:ancient person:lived_in
ln person:alexander_the_great person:field:military person:worked_in
ln person:alexander_the_great hist:period:classical_antiquity person:active_in
ln person:alexander_the_great hist:ancient_greece thesaurus:related
ln person:alexander_the_great epic:iliad thesaurus:related
def "person:ashoka" "The Mauryan emperor who, sickened by war, spread Buddhism and dharma."
ln person:ashoka person:figure thesaurus:related
ln person:ashoka person:era:ancient person:lived_in
ln person:ashoka person:field:politics_statecraft person:worked_in
ln person:ashoka hist:period:classical_antiquity person:active_in
ln person:ashoka ethnicity:indo_aryans thesaurus:related
def "person:qin_shi_huang" "China's first emperor, unifier and builder of the Great Wall."
ln person:qin_shi_huang person:figure thesaurus:related
ln person:qin_shi_huang person:era:ancient person:lived_in
ln person:qin_shi_huang person:field:politics_statecraft person:worked_in
ln person:qin_shi_huang hist:period:classical_antiquity person:active_in
ln person:qin_shi_huang hist:han_china thesaurus:related
ln person:qin_shi_huang archaeo:site:terracotta_army thesaurus:related
def "person:julius_caesar" "The general and dictator whose crossing of the Rubicon ended the Roman Republic."
ln person:julius_caesar person:figure thesaurus:related
ln person:julius_caesar person:era:ancient person:lived_in
ln person:julius_caesar person:field:military person:worked_in
ln person:julius_caesar hist:period:classical_antiquity person:active_in
ln person:julius_caesar hist:roman_empire thesaurus:related
def "person:cleopatra" "The last pharaoh of Egypt, ally and lover of Caesar and Antony."
ln person:cleopatra person:figure thesaurus:related
ln person:cleopatra person:era:ancient person:lived_in
ln person:cleopatra person:field:politics_statecraft person:worked_in
ln person:cleopatra hist:period:classical_antiquity person:active_in
ln person:cleopatra hist:ancient_egypt thesaurus:related
def "person:charlemagne" "King of the Franks crowned Emperor in 800, reviver of Western learning."
ln person:charlemagne person:figure thesaurus:related
ln person:charlemagne person:era:medieval person:lived_in
ln person:charlemagne person:field:military person:worked_in
ln person:charlemagne hist:period:early_middle_ages person:active_in
ln person:charlemagne ethnicity:french thesaurus:related
def "person:genghis_khan" "Founder of the Mongol Empire, the largest contiguous land empire."
ln person:genghis_khan person:figure thesaurus:related
ln person:genghis_khan person:era:medieval person:lived_in
ln person:genghis_khan person:field:military person:worked_in
ln person:genghis_khan hist:period:high_middle_ages person:active_in
ln person:genghis_khan hist:mongol_empire thesaurus:related
ln person:genghis_khan ethnicity:mongols thesaurus:related
def "person:ibn_battuta" "The Moroccan traveller whose journeys spanned the medieval Islamic world."
ln person:ibn_battuta person:figure thesaurus:related
ln person:ibn_battuta person:era:medieval person:lived_in
ln person:ibn_battuta person:field:exploration_navigation person:worked_in
ln person:ibn_battuta hist:period:late_middle_ages person:active_in
ln person:ibn_battuta ethnicity:arabs thesaurus:related
def "person:leonardo_da_vinci" "The Renaissance polymath of the Mona Lisa, anatomy and flying machines."
ln person:leonardo_da_vinci person:figure thesaurus:related
ln person:leonardo_da_vinci person:era:renaissance person:lived_in
ln person:leonardo_da_vinci person:field:visual_arts person:worked_in
ln person:leonardo_da_vinci hist:period:renaissance person:active_in
ln person:leonardo_da_vinci hist:renaissance thesaurus:related
ln person:leonardo_da_vinci ethnicity:italians thesaurus:related
def "person:michelangelo" "Sculptor of David and painter of the Sistine ceiling."
ln person:michelangelo person:figure thesaurus:related
ln person:michelangelo person:era:renaissance person:lived_in
ln person:michelangelo person:field:visual_arts person:worked_in
ln person:michelangelo hist:period:renaissance person:active_in
ln person:michelangelo hist:renaissance thesaurus:related
ln person:michelangelo ethnicity:italians thesaurus:related
def "person:columbus" "The navigator whose 1492 crossing linked the hemispheres."
ln person:columbus person:figure thesaurus:related
ln person:columbus person:era:renaissance person:lived_in
ln person:columbus person:field:exploration_navigation person:worked_in
ln person:columbus hist:period:age_of_exploration person:active_in
ln person:columbus hist:event:columbian_voyages thesaurus:related
def "person:zheng_he" "The Ming admiral whose treasure fleets reached Africa decades before Columbus."
ln person:zheng_he person:figure thesaurus:related
ln person:zheng_he person:era:renaissance person:lived_in
ln person:zheng_he person:field:exploration_navigation person:worked_in
ln person:zheng_he hist:period:age_of_exploration person:active_in
ln person:zheng_he hist:han_china thesaurus:related
def "person:martin_luther" "The monk whose 95 Theses launched the Protestant Reformation."
ln person:martin_luther person:figure thesaurus:related
ln person:martin_luther person:era:early_modern person:lived_in
ln person:martin_luther person:field:religion person:worked_in
ln person:martin_luther hist:period:reformation_era person:active_in
ln person:martin_luther hist:event:protestant_reformation thesaurus:related
def "person:galileo" "The father of observational astronomy, tried for defending Copernicus."
ln person:galileo person:figure thesaurus:related
ln person:galileo person:era:early_modern person:lived_in
ln person:galileo person:field:science person:worked_in
ln person:galileo hist:period:scientific_revolution person:active_in
ln person:galileo astrophys:cosmology thesaurus:related
def "person:newton" "The physicist of gravity, motion and calculus — the Principia."
ln person:newton person:figure thesaurus:related
ln person:newton person:era:early_modern person:lived_in
ln person:newton person:field:science person:worked_in
ln person:newton hist:period:scientific_revolution person:active_in
ln person:newton math:calculus thesaurus:related
ln person:newton astrophys:gravity thesaurus:related
def "person:napoleon" "The general and emperor whose wars and Code reshaped Europe."
ln person:napoleon person:figure thesaurus:related
ln person:napoleon person:era:early_modern person:lived_in
ln person:napoleon person:field:military person:worked_in
ln person:napoleon hist:period:modern_era person:active_in
ln person:napoleon hist:event:napoleonic_wars thesaurus:related
def "person:lincoln" "The US president who preserved the Union and ended slavery."
ln person:lincoln person:figure thesaurus:related
ln person:lincoln person:era:industrial_era person:lived_in
ln person:lincoln person:field:politics_statecraft person:worked_in
ln person:lincoln hist:period:modern_era person:active_in
ln person:lincoln quote:lincoln_gettysburg thesaurus:related
ln person:lincoln hist:event:abolition_of_slavery thesaurus:related
def "person:darwin" "The naturalist whose theory of evolution by natural selection remade biology."
ln person:darwin person:figure thesaurus:related
ln person:darwin person:era:industrial_era person:lived_in
ln person:darwin person:field:science person:worked_in
ln person:darwin hist:period:modern_era person:active_in
ln person:darwin life:evolution thesaurus:related
ln person:darwin life:natural_selection thesaurus:related
def "person:gandhi" "The leader of India's nonviolent independence struggle."
ln person:gandhi person:figure thesaurus:related
ln person:gandhi person:era:industrial_era person:lived_in
ln person:gandhi person:field:politics_statecraft person:worked_in
ln person:gandhi hist:period:world_wars_era person:active_in
ln person:gandhi ethnicity:indo_aryans thesaurus:related
ln person:gandhi socio:social_movement thesaurus:related
def "person:murasaki_shikibu" "The Heian lady-in-waiting who wrote the Tale of Genji."
ln person:murasaki_shikibu person:figure thesaurus:related
ln person:murasaki_shikibu person:era:medieval person:lived_in
ln person:murasaki_shikibu person:field:literature person:worked_in
ln person:murasaki_shikibu hist:period:high_middle_ages person:active_in
ln person:murasaki_shikibu epic:tale_of_genji thesaurus:related
ln person:murasaki_shikibu ethnicity:japanese_people thesaurus:related
def "person:ferdowsi" "The poet whose Shahnameh saved the Persian language and its myths."
ln person:ferdowsi person:figure thesaurus:related
ln person:ferdowsi person:era:medieval person:lived_in
ln person:ferdowsi person:field:literature person:worked_in
ln person:ferdowsi hist:period:high_middle_ages person:active_in
ln person:ferdowsi epic:shahnameh thesaurus:related
ln person:ferdowsi ethnicity:persians thesaurus:related
