# historical_wars.ak
# Landmark wars and conflicts — antiquity through Cold War
# Sources: Cambridge History of Warfare, SIPRI, Keegan — Public domain terminology
#

# ── Namespace anchors ─────────────────────────────────────────────────────────

def "war:era:ancient" "Wars of antiquity, before 500 CE — root for ancient conflict atoms."
def "war:era:medieval" "Medieval conflicts, 500–1500 CE — root for medieval conflict atoms."
def "war:era:early_modern" "Early modern wars, 1500–1800 — root for early modern conflict atoms."
def "war:era:modern" "19th- and early 20th-century wars — root for modern conflict atoms."
def "war:era:world_wars" "World War I and World War II — root for the two world war atoms."
def "war:era:cold_war" "Cold War and proxy conflicts, 1945–1991 — root for cold war conflict atoms."

set.add name="ontology.historical_wars" id="war:era:ancient"
set.add name="ontology.historical_wars" id="war:era:medieval"
set.add name="ontology.historical_wars" id="war:era:early_modern"
set.add name="ontology.historical_wars" id="war:era:modern"
set.add name="ontology.historical_wars" id="war:era:world_wars"
set.add name="ontology.historical_wars" id="war:era:cold_war"

# ── Ancient conflicts ─────────────────────────────────────────────────────────

def "war:conflict:persian_wars" "Greco-Persian Wars (499–449 BCE); Athenian-led Greeks repelled Achaemenid invasion; Marathon (490), Thermopylae/Salamis (480), Plataea (479); Greek independence secured."
ln war:conflict:persian_wars war:era:ancient sys:part_of
set.add name="ontology.historical_wars" id="war:conflict:persian_wars"

def "war:conflict:peloponnesian_war" "Peloponnesian War (431–404 BCE); Athens vs Sparta; Thucydides' account; Athens' plague and Sicilian Expedition disaster; Sparta ultimately victorious."
ln war:conflict:peloponnesian_war war:era:ancient sys:part_of
ln war:conflict:peloponnesian_war war:conflict:persian_wars war:preceded_by
set.add name="ontology.historical_wars" id="war:conflict:peloponnesian_war"

def "war:conflict:alexander_conquests" "Macedonian Conquests (336–323 BCE); Alexander III defeats Persia, Egypt, Central Asia, India; Granicus to Hydaspes; largest empire to that date."
ln war:conflict:alexander_conquests war:era:ancient sys:part_of
set.add name="ontology.historical_wars" id="war:conflict:alexander_conquests"

def "war:conflict:punic_wars" "Punic Wars (264–146 BCE); Rome vs Carthage; 3 wars; Hannibal's Italy invasion (Cannae 216 BCE); Rome destroys Carthage 146 BCE; established Roman Mediterranean dominance."
ln war:conflict:punic_wars war:era:ancient sys:part_of
set.add name="ontology.historical_wars" id="war:conflict:punic_wars"

def "war:conflict:roman_civil_wars" "Roman Civil Wars (133–31 BCE); Marius/Sulla, Caesar/Pompey, Antony/Octavian; collapse of the Republic into the Principate; culminated at Actium (31 BCE)."
ln war:conflict:roman_civil_wars war:era:ancient sys:part_of
ln war:conflict:roman_civil_wars war:conflict:punic_wars war:preceded_by
set.add name="ontology.historical_wars" id="war:conflict:roman_civil_wars"

def "war:conflict:jewish_roman_wars" "Jewish-Roman Wars (66–135 CE); First revolt (66–73): destruction of the Jerusalem Temple 70 CE; Bar Kokhba revolt (132–135): Jewish diaspora cemented."
ln war:conflict:jewish_roman_wars war:era:ancient sys:part_of
set.add name="ontology.historical_wars" id="war:conflict:jewish_roman_wars"

def "war:conflict:gothic_wars" "Gothic Wars and fall of Western Rome (376–476 CE); Adrianople (378); Visigoths sack Rome (410); Odoacer deposes Romulus Augustulus (476)."
ln war:conflict:gothic_wars war:era:ancient sys:part_of
set.add name="ontology.historical_wars" id="war:conflict:gothic_wars"

def "war:conflict:byzantine_sassanid_war" "Byzantine-Sassanid War (602–628 CE); last great ancient war; both powers exhausted each other, enabling the Arab conquest; Heraclius ultimately victorious."
ln war:conflict:byzantine_sassanid_war war:era:ancient sys:part_of
ln war:conflict:byzantine_sassanid_war war:conflict:arab_conquests war:led_to
set.add name="ontology.historical_wars" id="war:conflict:byzantine_sassanid_war"

def "war:conflict:arab_conquests" "Arab-Islamic Conquests (632–750 CE); Rashidun and Umayyad caliphates conquer Persia, Levant, Egypt, North Africa, Spain; Yarmouk (636), Qadisiyya (636)."
ln war:conflict:arab_conquests war:era:ancient sys:part_of
set.add name="ontology.historical_wars" id="war:conflict:arab_conquests"

# ── Medieval conflicts ────────────────────────────────────────────────────────

def "war:conflict:viking_raids" "Viking Age (793–1066 CE); raids on Britain (Lindisfarne 793), France, Mediterranean; Danelaw; Normandy; Dublin; eventual settlement and Christianisation."
ln war:conflict:viking_raids war:era:medieval sys:part_of
set.add name="ontology.historical_wars" id="war:conflict:viking_raids"

def "war:conflict:norman_conquest" "Norman Conquest of England (1066); William I defeats Harold at Hastings; feudal reorganisation of England; Domesday Book; lasting French language influence."
ln war:conflict:norman_conquest war:era:medieval sys:part_of
ln war:conflict:norman_conquest war:conflict:viking_raids war:preceded_by
set.add name="ontology.historical_wars" id="war:conflict:norman_conquest"

def "war:conflict:crusades" "Crusades (1095–1291); 9+ campaigns; Pope Urban II; First Crusade took Jerusalem (1099); Saladin retook it (1187); Christian states ended with fall of Acre (1291)."
ln war:conflict:crusades war:era:medieval sys:part_of
set.add name="ontology.historical_wars" id="war:conflict:crusades"

def "war:conflict:mongol_conquests" "Mongol Conquests (1206–1368); Genghis Khan and successors; Eurasia from Korea to Poland; largest contiguous land empire; 40M+ deaths estimated; Pax Mongolica after."
ln war:conflict:mongol_conquests war:era:medieval sys:part_of
set.add name="ontology.historical_wars" id="war:conflict:mongol_conquests"

def "war:conflict:hundred_years_war" "Hundred Years War (1337–1453); England vs France over throne; Crécy, Agincourt (English victories); Joan of Arc turns tide; French expelled except Calais."
ln war:conflict:hundred_years_war war:era:medieval sys:part_of
set.add name="ontology.historical_wars" id="war:conflict:hundred_years_war"

def "war:conflict:reconquista" "Reconquista (722–1492); Christian kingdoms recover Iberia from Umayyads and Moors; Covadonga to fall of Granada; ended the year Columbus sailed."
ln war:conflict:reconquista war:era:medieval sys:part_of
ln war:conflict:reconquista war:conflict:arab_conquests war:preceded_by
set.add name="ontology.historical_wars" id="war:conflict:reconquista"

def "war:conflict:wars_of_roses" "Wars of the Roses (1455–1487); Lancaster vs York for the English throne; ended with Tudor victory (Henry VII); dramatised by Shakespeare."
ln war:conflict:wars_of_roses war:era:medieval sys:part_of
set.add name="ontology.historical_wars" id="war:conflict:wars_of_roses"

def "war:conflict:ottoman_conquest_byzantium" "Ottoman Conquest of Constantinople (1453); Mehmed II; 1,000-year Byzantine Empire ended; gunpowder artillery decisive; Eastern Orthodox diaspora into Europe."
ln war:conflict:ottoman_conquest_byzantium war:era:medieval sys:part_of
set.add name="ontology.historical_wars" id="war:conflict:ottoman_conquest_byzantium"

def "war:conflict:timur_conquests" "Timur's Conquests (1370–1405); Timurid expansion from Samarkand; Delhi, Baghdad, Damascus sacked; Battle of Ankara (1402) captured Ottoman sultan Bayezid I."
ln war:conflict:timur_conquests war:era:medieval sys:part_of
set.add name="ontology.historical_wars" id="war:conflict:timur_conquests"

# ── Early modern conflicts ────────────────────────────────────────────────────

def "war:conflict:italian_wars" "Italian Wars (1494–1559); France, Spain, Papacy, Venice compete for Italy; introduced gunpowder-age tactics; Habsburg-Valois rivalry; Treaty of Cateau-Cambrésis."
ln war:conflict:italian_wars war:era:early_modern sys:part_of
set.add name="ontology.historical_wars" id="war:conflict:italian_wars"

def "war:conflict:thirty_years_war" "Thirty Years War (1618–1648); Holy Roman Empire; religious → political conflict; Bohemian, Danish, Swedish, French phases; Peace of Westphalia; 30% Central European population lost."
ln war:conflict:thirty_years_war war:era:early_modern sys:part_of
set.add name="ontology.historical_wars" id="war:conflict:thirty_years_war"

def "war:conflict:english_civil_war" "English Civil War (1642–1651); Parliament vs Crown; Oliver Cromwell; Charles I executed 1649; Interregnum; Restoration 1660; constitutional monarchy foundation."
ln war:conflict:english_civil_war war:era:early_modern sys:part_of
set.add name="ontology.historical_wars" id="war:conflict:english_civil_war"

def "war:conflict:war_spanish_succession" "War of Spanish Succession (1701–1714); Louis XIV vs Grand Alliance; Blenheim (Marlborough 1704); Treaty of Utrecht; balance-of-power principle established."
ln war:conflict:war_spanish_succession war:era:early_modern sys:part_of
set.add name="ontology.historical_wars" id="war:conflict:war_spanish_succession"

def "war:conflict:seven_years_war" "Seven Years War (1756–1763); first global conflict across 5 continents; Britain vs France/Austria; British Empire consolidated; Quebec, Bengal, Senegal captured."
ln war:conflict:seven_years_war war:era:early_modern sys:part_of
set.add name="ontology.historical_wars" id="war:conflict:seven_years_war"

def "war:conflict:american_revolutionary_war" "American Revolutionary War (1775–1783); 13 Colonies vs Britain; French alliance crucial; Saratoga, Yorktown; Treaty of Paris; first successful anti-colonial independence."
ln war:conflict:american_revolutionary_war war:era:early_modern sys:part_of
ln war:conflict:american_revolutionary_war war:conflict:seven_years_war war:preceded_by
set.add name="ontology.historical_wars" id="war:conflict:american_revolutionary_war"

# ── Modern conflicts ──────────────────────────────────────────────────────────

def "war:conflict:french_revolutionary_wars" "French Revolutionary Wars (1792–1802); France vs European coalitions; levée en masse; spread revolutionary ideals across Europe; Napoleon emerged."
ln war:conflict:french_revolutionary_wars war:era:modern sys:part_of
ln war:conflict:french_revolutionary_wars war:conflict:american_revolutionary_war war:influenced_by
set.add name="ontology.historical_wars" id="war:conflict:french_revolutionary_wars"

def "war:conflict:napoleonic_wars" "Napoleonic Wars (1803–1815); Napoleon vs shifting coalitions; Austerlitz, Trafalgar, Leipzig, Waterloo; Continental System; reshaping of Europe; Congress of Vienna."
ln war:conflict:napoleonic_wars war:era:modern sys:part_of
ln war:conflict:napoleonic_wars war:conflict:french_revolutionary_wars war:preceded_by
set.add name="ontology.historical_wars" id="war:conflict:napoleonic_wars"

def "war:conflict:american_civil_war" "American Civil War (1861–1865); Union vs Confederate States; slavery abolition; Gettysburg, Sherman's March; 620,000+ dead; industrial total war paradigm."
ln war:conflict:american_civil_war war:era:modern sys:part_of
set.add name="ontology.historical_wars" id="war:conflict:american_civil_war"

def "war:conflict:franco_prussian_war" "Franco-Prussian War (1870–1871); Prussian victory; German unification; Sedan surrender of Napoleon III; Paris Commune; Alsace-Lorraine annexation."
ln war:conflict:franco_prussian_war war:era:modern sys:part_of
ln war:conflict:franco_prussian_war war:conflict:world_war_i war:led_to
set.add name="ontology.historical_wars" id="war:conflict:franco_prussian_war"

def "war:conflict:russo_japanese_war" "Russo-Japanese War (1904–1905); Japan defeats Russia; Tsushima naval battle; first Asian power defeats European great power in modern era; Portsmouth Treaty."
ln war:conflict:russo_japanese_war war:era:modern sys:part_of
set.add name="ontology.historical_wars" id="war:conflict:russo_japanese_war"

def "war:conflict:balkan_wars" "Balkan Wars (1912–1913); First: Balkan League vs Ottoman; Second: Balkan states fight each other; Ottoman Europe largely lost; directly set stage for WWI."
ln war:conflict:balkan_wars war:era:modern sys:part_of
ln war:conflict:balkan_wars war:conflict:world_war_i war:led_to
set.add name="ontology.historical_wars" id="war:conflict:balkan_wars"

# ── World Wars ────────────────────────────────────────────────────────────────

def "war:conflict:world_war_i" "World War I (1914–1918); Allied Powers vs Central Powers; trench warfare; Verdun, Somme; poison gas; 20M dead; Russian Revolution; Armistice 11/11/1918; Treaty of Versailles."
ln war:conflict:world_war_i war:era:world_wars sys:part_of
ln war:conflict:world_war_i war:conflict:world_war_ii war:led_to
set.add name="ontology.historical_wars" id="war:conflict:world_war_i"

def "war:conflict:russian_civil_war" "Russian Civil War (1917–1922); Bolsheviks vs White Army and foreign intervention; Red Terror; 5–12M dead (combat + famine/disease); Soviet Union established."
ln war:conflict:russian_civil_war war:era:world_wars sys:part_of
ln war:conflict:russian_civil_war war:conflict:world_war_i war:preceded_by
set.add name="ontology.historical_wars" id="war:conflict:russian_civil_war"

def "war:conflict:world_war_ii" "World War II (1939–1945); Axis vs Allies; Blitzkrieg, Battle of Britain, Stalingrad, D-Day, Pacific War; Holocaust; nuclear weapons used; 70–85M dead; UN founded."
ln war:conflict:world_war_ii war:era:world_wars sys:part_of
set.add name="ontology.historical_wars" id="war:conflict:world_war_ii"

def "war:conflict:chinese_civil_war" "Chinese Civil War (1927–1949); CCP vs KMT; Long March; Japanese invasion interlude; CCP victory; PRC founded 1949; ROC retreats to Taiwan."
ln war:conflict:chinese_civil_war war:era:world_wars sys:part_of
ln war:conflict:chinese_civil_war war:conflict:world_war_ii war:influenced_by
set.add name="ontology.historical_wars" id="war:conflict:chinese_civil_war"

# ── Cold War conflicts ────────────────────────────────────────────────────────

def "war:conflict:korean_war" "Korean War (1950–1953); North Korea + China vs South Korea + UN forces; 38th parallel; armistice but no peace treaty; 3M+ dead; ongoing technical state of war."
ln war:conflict:korean_war war:era:cold_war sys:part_of
ln war:conflict:korean_war war:conflict:world_war_ii war:preceded_by
set.add name="ontology.historical_wars" id="war:conflict:korean_war"

def "war:conflict:algerian_war" "Algerian War of Independence (1954–1962); FLN vs France; torture, urban bombing; 1M+ dead; French withdrawal; de Gaulle's Fifth Republic triggered."
ln war:conflict:algerian_war war:era:cold_war sys:part_of
set.add name="ontology.historical_wars" id="war:conflict:algerian_war"

def "war:conflict:vietnam_war" "Vietnam War (1955–1975); North Vietnam + Viet Cong vs South Vietnam + USA; guerrilla warfare; 3M+ dead; US withdrawal 1973; North Vietnam victory 1975."
ln war:conflict:vietnam_war war:era:cold_war sys:part_of
ln war:conflict:vietnam_war war:conflict:korean_war war:preceded_by
set.add name="ontology.historical_wars" id="war:conflict:vietnam_war"

def "war:conflict:arab_israeli_wars" "Arab-Israeli Wars (1948, 1956, 1967, 1973); Israeli independence (1948); Six-Day War (1967): Sinai, West Bank, Golan captured; Yom Kippur War (1973): near-defeat then recovery."
ln war:conflict:arab_israeli_wars war:era:cold_war sys:part_of
set.add name="ontology.historical_wars" id="war:conflict:arab_israeli_wars"

def "war:conflict:soviet_afghan_war" "Soviet-Afghan War (1979–1989); USSR vs CIA-backed Mujahideen; the Soviet Union's Vietnam; 1–2M Afghan dead; Soviet withdrawal; contributed to USSR collapse."
ln war:conflict:soviet_afghan_war war:era:cold_war sys:part_of
set.add name="ontology.historical_wars" id="war:conflict:soviet_afghan_war"

def "war:conflict:falklands_war" "Falklands War (1982); Argentina vs UK; rapid conventional war; British task force victory; Argentine defeat; Thatcher political consolidation; sovereignty unresolved."
ln war:conflict:falklands_war war:era:cold_war sys:part_of
set.add name="ontology.historical_wars" id="war:conflict:falklands_war"

def "war:conflict:iran_iraq_war" "Iran-Iraq War (1980–1988); Saddam's Iraq vs Khomeini's Iran; chemical weapons used at Halabja; 500K–1M dead; stalemate; ended by UN Resolution 598."
ln war:conflict:iran_iraq_war war:era:cold_war sys:part_of
set.add name="ontology.historical_wars" id="war:conflict:iran_iraq_war"

# ── Causal chains across eras ──────────────────────────────────────────────────

ln war:conflict:napoleonic_wars war:conflict:franco_prussian_war war:led_to
ln war:conflict:russian_civil_war war:conflict:world_war_ii war:influenced_by
ln war:conflict:world_war_ii war:conflict:korean_war war:led_to
ln war:conflict:world_war_ii war:conflict:arab_israeli_wars war:led_to
ln war:conflict:soviet_afghan_war war:conflict:algerian_war war:influenced_by
