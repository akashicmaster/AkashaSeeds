# Akasha ontology (world pack) — historical periods, the timeline itself.
# base3/hist.ak holds the THEORY of history (periodization, memory, chronicle);
# this adds the actual PERIODS as first-class, ordered atoms (chrono:before),
# richly described and tied to hist:polities, archaeo:, epic: and person:era:.

def "hist:period" "A named span of history with shared character (時代)."
# ── the periods, in order (chrono:before) ──
def "hist:period:paleolithic" "The Old Stone Age — from the first stone tools (~3.3 Mya) to the end of the Ice Age; hunter-gatherers, fire, cave art and the peopling of the earth."
ln hist:period:paleolithic hist:period thesaurus:related
ln hist:period:paleolithic archaeo:prehistory thesaurus:related
def "hist:period:mesolithic" "The Middle Stone Age — post-glacial foragers with microliths, as forests spread and the first settlements appear."
ln hist:period:mesolithic hist:period thesaurus:related
ln hist:period:paleolithic hist:period:mesolithic chrono:before
ln hist:period:mesolithic archaeo:prehistory thesaurus:related
def "hist:period:neolithic" "The New Stone Age — farming, herding, pottery and permanent villages: the Neolithic Revolution that made civilization possible."
ln hist:period:neolithic hist:period thesaurus:related
ln hist:period:mesolithic hist:period:neolithic chrono:before
ln hist:period:neolithic agron:agronomy thesaurus:related
ln hist:period:neolithic archaeo:prehistory thesaurus:related
def "hist:period:bronze_age" "The age of bronze metallurgy, writing, cities and the first states — Sumer, Egypt, the Indus, Minoan and Shang."
ln hist:period:bronze_age hist:period thesaurus:related
ln hist:period:neolithic hist:period:bronze_age chrono:before
ln hist:period:bronze_age hist:sumer thesaurus:related
ln hist:period:bronze_age hist:ancient_egypt thesaurus:related
ln hist:period:bronze_age hist:indus_valley thesaurus:related
ln hist:period:bronze_age matsci:alloy thesaurus:related
def "hist:period:iron_age" "The spread of iron tools and weapons, larger empires and alphabets — Assyria, the Hebrew kingdoms, early Greece and China's Zhou."
ln hist:period:iron_age hist:period thesaurus:related
ln hist:period:bronze_age hist:period:iron_age chrono:before
ln hist:period:iron_age hist:assyria thesaurus:related
ln hist:period:iron_age matsci:metal thesaurus:related
def "hist:period:classical_antiquity" "The Greco-Roman classical world — the polis, Athenian democracy and philosophy, the Roman Republic and Empire, and their Persian and Indian contemporaries."
ln hist:period:classical_antiquity hist:period thesaurus:related
ln hist:period:iron_age hist:period:classical_antiquity chrono:before
ln hist:period:classical_antiquity hist:ancient_greece thesaurus:related
ln hist:period:classical_antiquity hist:roman_empire thesaurus:related
ln hist:period:classical_antiquity epic:iliad thesaurus:related
ln hist:period:classical_antiquity phil:field:ethics thesaurus:related
def "hist:period:late_antiquity" "The transformation of the Roman world (~3rd–7th c.) — Christianity's rise, barbarian settlement, and the birth of Byzantium and Islam."
ln hist:period:late_antiquity hist:period thesaurus:related
ln hist:period:classical_antiquity hist:period:late_antiquity chrono:before
ln hist:period:late_antiquity hist:byzantine_empire thesaurus:related
def "hist:period:early_middle_ages" "The 'early medieval' centuries after Rome's western fall — Charlemagne, the Vikings, and the Islamic Golden Age."
ln hist:period:early_middle_ages hist:period thesaurus:related
ln hist:period:late_antiquity hist:period:early_middle_ages chrono:before
ln hist:period:early_middle_ages hist:roman_empire thesaurus:related
def "hist:period:high_middle_ages" "The medieval peak (~1000–1300) — cathedrals, universities, the Crusades, feudalism and rising towns."
ln hist:period:high_middle_ages hist:period thesaurus:related
ln hist:period:early_middle_ages hist:period:high_middle_ages chrono:before
ln hist:period:high_middle_ages law:law thesaurus:related
def "hist:period:late_middle_ages" "Crisis and change (~1300–1500) — the Black Death, the Hundred Years' War, and the seeds of the Renaissance."
ln hist:period:late_middle_ages hist:period thesaurus:related
ln hist:period:high_middle_ages hist:period:late_middle_ages chrono:before
def "hist:period:renaissance" "The 'rebirth' of classical learning and art (~14th–16th c.), humanism, and the flowering of Italy — Leonardo, Michelangelo, printing."
ln hist:period:renaissance hist:period thesaurus:related
ln hist:period:late_middle_ages hist:period:renaissance chrono:before
ln hist:period:renaissance hist:renaissance thesaurus:related
ln hist:period:renaissance artsci:art_history thesaurus:related
def "hist:period:age_of_exploration" "The era of oceanic voyages (~15th–17th c.) linking the continents — and the Columbian Exchange that remade the world's food and peoples."
ln hist:period:age_of_exploration hist:period thesaurus:related
ln hist:period:renaissance hist:period:age_of_exploration chrono:before
ln hist:period:age_of_exploration foodstud:columbian_exchange thesaurus:related
ln hist:period:age_of_exploration cartog:portolan_chart thesaurus:related
ln hist:period:age_of_exploration geog:cartography thesaurus:related
def "hist:period:reformation_era" "The Protestant Reformation and Counter-Reformation (16th c.) that split Western Christendom and reshaped Europe's politics."
ln hist:period:reformation_era hist:period thesaurus:related
ln hist:period:age_of_exploration hist:period:reformation_era chrono:before
ln hist:period:reformation_era socio:social_institution thesaurus:related
def "hist:period:scientific_revolution" "The 16th–17th-century transformation of natural knowledge — Copernicus, Galileo, Newton — birthing modern science."
ln hist:period:scientific_revolution hist:period thesaurus:related
ln hist:period:reformation_era hist:period:scientific_revolution chrono:before
ln hist:period:scientific_revolution research:research thesaurus:related
ln hist:period:scientific_revolution astrophys:cosmology thesaurus:related
def "hist:period:enlightenment" "The 'Age of Reason' (18th c.) — reason, rights, tolerance and progress; the intellectual ground of modern politics."
ln hist:period:enlightenment hist:period thesaurus:related
ln hist:period:scientific_revolution hist:period:enlightenment chrono:before
ln hist:period:enlightenment hist:enlightenment thesaurus:related
ln hist:period:enlightenment phil:field:political_philosophy thesaurus:related
ln hist:period:enlightenment law:concept:social_contract thesaurus:related
def "hist:period:industrial_revolution" "The mechanization of production (~1760–1840) — steam, factories, railways and the birth of the modern economy and working class."
ln hist:period:industrial_revolution hist:period thesaurus:related
ln hist:period:enlightenment hist:period:industrial_revolution chrono:before
ln hist:period:industrial_revolution econ:economic_growth thesaurus:related
ln hist:period:industrial_revolution socio:social_class thesaurus:related
ln hist:period:industrial_revolution mecheng:thermodynamics thesaurus:related
def "hist:period:modern_era" "The long 19th century — nation-states, empire and colonialism, mass politics and rapid technological change."
ln hist:period:modern_era hist:period thesaurus:related
ln hist:period:industrial_revolution hist:period:modern_era chrono:before
ln hist:period:modern_era admin:nation thesaurus:related
ln hist:period:modern_era socio:modernization thesaurus:related
def "hist:period:world_wars_era" "The age of total war (1914–1945) — two world wars, revolutions, genocide, and the collapse of empires."
ln hist:period:world_wars_era hist:period thesaurus:related
ln hist:period:modern_era hist:period:world_wars_era chrono:before
ln hist:period:world_wars_era war:war thesaurus:related
def "hist:period:cold_war" "The bipolar standoff (1947–1991) of the US and USSR — nuclear deterrence, proxy wars, decolonization and the space race."
ln hist:period:cold_war hist:period thesaurus:related
ln hist:period:world_wars_era hist:period:cold_war chrono:before
ln hist:period:cold_war admin:country thesaurus:related
def "hist:period:information_age" "The contemporary digital era — computing, the internet, globalization and the networked society."
ln hist:period:information_age hist:period thesaurus:related
ln hist:period:cold_war hist:period:information_age chrono:before
ln hist:period:information_age cs:cs thesaurus:related
ln hist:period:information_age dh:knowledge_graph thesaurus:related
ln hist:period:information_age socio:globalization thesaurus:related
